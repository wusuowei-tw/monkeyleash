# -*- coding: utf-8 -*-
"""票 47 —— R5 的正對照(**存在性四面 A / B / D / E**,批 1)。

## 為什麼這個檔案存在

R5 守的是:`npx skills update` 會用上游版覆蓋正典 `code-review`,
**靜默移除本地第三軸**。而在本檔之前,**R5 的判定邏輯在 pytest 裡零涵蓋** ——
`check_third_axis_mount()` / `check_to_spec_override()` 只出現三種形態
(被 `monkeypatch` 成 `lambda: []`、餵假違規測快取、只驗代號被列舉),
**沒有一種在斷言它會擋**(清冊登記五)。

> **它守的是「靜默」,而它自己也是靜默的。**

**R5 沒有壞**(2026-08-17 探針實測四種破法全擋得住)。
**本檔補的是「沒有東西證明它會擋」,不是「它擋不住」。**

## 沒有紅燈先行,而那是對的 —— 非空洞性由**成對**保證

本檔不改任何行為,所以沒有「先紅後綠」那一步。
非空洞性靠的是**每一面都成對**:

    違規輸入 -> 必須回一條違規       一支「永遠回 []」的實作在這裡紅
    乾淨輸入 -> 必須回 []            一支「永遠回違規」的實作在這裡紅

> **兩條合起來,才排除得掉「因為錯的理由而通過」(F-103)。**
> 只寫前者的話,`return ["x"]` 也全綠;只寫後者的話,`return []` 也全綠。

而**票 58 的判準**(「一個從來不會紅的綠燈是空的」)在這裡的落實方式是:
每一個類別的 docstring 都先答**「哪一個 repo 狀態確定會讓這條紅」**,
而那個狀態**由測試自己真的建出來** —— 真的寫一份檔案到磁碟,
讓真的 `check_*()` 去讀它,不替換任何判定函式。

## 兩支的路徑不對稱(要知道,否則會 patch 錯東西)

    check_third_axis_mount()   讀模組常數 CANON_CODE_REVIEW(gate.py:29,import 時算好)
    check_to_spec_override()   路徑在**函式內**組(gate.py:2253),吃的是 ROOT

所以隔離它們要 patch **不同的東西**,而且**互不影響** ——
`CANON_CODE_REVIEW` 在 import 時就從 ROOT 算完了,後來改 `ROOT` 不會移動它。

**這個不對稱是既知的,票 47 裁決「不抽常數」(那是改實作,超出純補測試)。**

## 模組層變數一律用 `monkeypatch` fixture

自動還原。**要防的是同一個行程內忘了還原、污染後續測試** ——
測試順序不保證,被污染的那一條會在別的地方紅,而**紅的位置與原因無關**。
(**不是 xdist 競態**:xdist 是多行程,模組層變數不共享。)
"""
import importlib.util
import io
import json
import os
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load_gate():
    spec = importlib.util.spec_from_file_location(
        "gate_for_r5", ROOT / ".claude" / "hooks" / "gate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# **模組層綁定是必要的,不是風格**:conftest 的 `_isolate_live_gate_state`
# 走訪測試模組的屬性去找 gate 實例(`conftest.py:72-99`),
# 在測試函式內部才載入的那份它蓋不到。
gate = _load_gate()


# ─────────────────────────────────────────────────────────────────────────────
# 最小合法語料 —— 只含判定真的會讀的錨點,不抄整份正典。
#
# **抄整份不會更真實,只會更脆**:正典每次上游更新都變,而 R5 判定讀的
# 就是下面這幾個字串與它們的先後順序。多抄的部分不參與判定,
# 卻會讓這個檔案在正典改版時無故紅 —— 那是把測試綁在無關的東西上。
# ─────────────────────────────────────────────────────────────────────────────

VALID_CODE_REVIEW = (
    "### 3. Identify the standards sources\n"
    "\n"
    "### 3b. Identify the data-integrity sources\n"
    "Clean degradation is mandatory.\n"
    "\n"
    "### 4. Spawn\n"
    "**Data Integrity sub-agent prompt**\n"
    "Exemption reconciliation (local addition)\n"
    "\n"
    "### 5. Aggregate\n"
)

VALID_TO_SPEC = (
    "## Implementation Decisions\n"
    "\n"
    "LOCAL OVERRIDE (prototype snippets)\n"
    "\n"
    "## Testing Decisions\n"
)


def _write(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    io.open(str(path), "w", encoding="utf-8", newline="\n").write(body)
    return path


def _to_spec_root(tmp_path, body):
    """造一個 ROOT,底下有 `.agents/skills/to-spec/SKILL.md`。"""
    _write(tmp_path / ".agents" / "skills" / "to-spec" / "SKILL.md", body)
    return tmp_path


# ─────────────────────────────────────────────────────────────────────────────
# 面 A / D —— 正典檔整個不見
# ─────────────────────────────────────────────────────────────────────────────

class TestR5RefusesWhenTheCanonIsGone:
    """**哪一個 repo 狀態確定會讓這條紅?**

      面 A:`.agents/skills/code-review/SKILL.md` **不存在**
      面 D:`.agents/skills/to-spec/SKILL.md` **不存在**

    這不是假想的狀態:`npx skills update` 的失敗模式之一就是把正典整個換掉,
    而換過去的版本沒有本地 patch —— **檔案在但內容不對**是面 B/E,
    **檔案根本不在**是這一面(rmtree 之後重建失敗、同步中斷、路徑改名)。

    **兩面分開,因為它們是兩支函式、兩個檔、兩則訊息。**
    合成一面的話,補一條會**看起來**蓋了兩面,而另一支仍然零涵蓋。
    """

    def test_a_missing_code_review_canon_is_a_violation(self, tmp_path, monkeypatch):
        monkeypatch.setattr(gate, "CANON_CODE_REVIEW",
                            str(tmp_path / "nowhere" / "SKILL.md"))
        v = gate.check_third_axis_mount()
        assert len(v) == 1, "正典檔不在,R5 卻沒回違規:%r" % v
        assert "找不到正典" in v[0], "訊息沒說出是哪一個前提沒滿足:%r" % v

    def test_a_missing_to_spec_canon_is_a_violation(self, tmp_path, monkeypatch):
        # to-spec 的路徑在函式內組,所以這裡 patch 的是 ROOT(不是 CANON_*)。
        # tmp_path 底下什麼都沒建 -> 那個檔必然不存在。
        monkeypatch.setattr(gate, "ROOT", str(tmp_path))
        v = gate.check_to_spec_override()
        assert len(v) == 1, "to-spec 正典不在,R5 卻沒回違規:%r" % v
        assert "to-spec" in v[0], "訊息沒點名是哪一個檔:%r" % v

    def test_patching_root_does_not_move_the_code_review_canon(self, tmp_path,
                                                               monkeypatch):
        """**反控,而且是這個檔案自己的接線**:兩支的隔離必須互不影響。

        `CANON_CODE_REVIEW` 在 import 時就從 `ROOT` 算完(`gate.py:29`),
        所以改 `ROOT` **不會**移動它。少了這一條,上面那兩條若哪天
        因為實作改成「兩支都吃 ROOT」而互相污染,不會有東西出聲。
        """
        monkeypatch.setattr(gate, "ROOT", str(tmp_path))
        assert gate.check_third_axis_mount() == [], (
            "改 ROOT 之後 code-review 那一支也跟著動了 —— 兩面的隔離失效")


# ─────────────────────────────────────────────────────────────────────────────
# 面 B —— 第三軸掛載點存在
# ─────────────────────────────────────────────────────────────────────────────

class TestR5RefusesAMissingThirdAxisMarker:
    """**哪一個 repo 狀態確定會讓這條紅?**

    正典 `code-review` 在,但 `MOUNT_MARKERS` 裡**少了任何一個** ——
    那正是 `npx skills update` 用上游版覆蓋之後的樣子:
    檔案還在、看起來正常、而第三軸不見了。

    **逐個 marker 參數化,不是只拆一個。** `verify_gates.scenario_r5` 把
    `Data Integrity` 換成中文,只打掉四個裡的**一個**
    (`### 3b. …data-integrity…` 是小寫連字號,打不到)。
    那證明「少了那一個會擋」,不證明**另外三個是承重的** ——
    一個把 `MOUNT_MARKERS` 砍到只剩一項的改動會讓那條情境照樣綠。
    """

    @pytest.mark.parametrize("marker", list(gate.MOUNT_MARKERS))
    def test_removing_any_single_marker_is_a_violation(self, tmp_path,
                                                       monkeypatch, marker):
        canon = _write(tmp_path / "SKILL.md",
                       VALID_CODE_REVIEW.replace(marker, "(被上游版覆蓋掉了)"))
        monkeypatch.setattr(gate, "CANON_CODE_REVIEW", str(canon))
        v = gate.check_third_axis_mount()
        assert len(v) == 1, "少了掛載點 %r,R5 卻沒回違規:%r" % (marker, v)
        assert marker in v[0], "訊息沒點名少了哪一個掛載點:%r" % v
        assert "skills-update.sh" in v[0], "訊息沒給修復入口:%r" % v

    def test_a_complete_canon_is_clean(self, tmp_path, monkeypatch):
        """**成對的另一半。** 少了它,一支「永遠回違規」的實作也會讓上面全綠。"""
        canon = _write(tmp_path / "SKILL.md", VALID_CODE_REVIEW)
        monkeypatch.setattr(gate, "CANON_CODE_REVIEW", str(canon))
        assert gate.check_third_axis_mount() == []

    def test_every_marker_is_load_bearing(self):
        """**元斷言**:上面那條參數化必須真的涵蓋每一個 marker。

        寫死四條的話,`MOUNT_MARKERS` 新增第五個時**不會有東西出聲** ——
        新的那一個從此沒有正對照,而測試數字看起來沒變少。
        參數化綁的是常數本身,所以這一條只是把「綁對了」講出來。
        """
        assert len(gate.MOUNT_MARKERS) >= 4, gate.MOUNT_MARKERS
        for m in gate.MOUNT_MARKERS:
            assert m in VALID_CODE_REVIEW, (
                "最小語料少了 %r —— 那條參數化對它是空轉的(乾淨基準本身就缺它,"
                "拆掉之後與拆掉之前沒有差別)" % m)


# ─────────────────────────────────────────────────────────────────────────────
# 面 E —— to-spec 的 inline snippet 覆寫存在
# ─────────────────────────────────────────────────────────────────────────────

class TestR5RefusesAMissingToSpecOverride:
    """**哪一個 repo 狀態確定會讓這條紅?**

    正典 `to-spec` 在,但少了 `LOCAL OVERRIDE (prototype snippets)`。

    **為什麼這一面要緊**(`gate.py:2249-2250` 逐字):
    上游允許把 prototype 的 snippet inline 進 spec —— **那與 R1 正面衝突**。
    覆寫被 update 蓋掉的話,**skill 會開始要求 AI 做 R1 一定會擋的事** ——
    於是使用者會撞上一個「照著指令做卻被擋」的迴圈,而兩邊都沒有錯。
    """

    def test_a_missing_override_marker_is_a_violation(self, tmp_path, monkeypatch):
        root = _to_spec_root(tmp_path, VALID_TO_SPEC.replace(
            "LOCAL OVERRIDE (prototype snippets)", "(被上游版覆蓋掉了)"))
        monkeypatch.setattr(gate, "ROOT", str(root))
        v = gate.check_to_spec_override()
        assert len(v) == 1, "覆寫掛載點不見了,R5 卻沒回違規:%r" % v
        assert "覆寫掛載點" in v[0], "訊息沒說出缺的是什麼:%r" % v
        assert "skills-update.sh" in v[0], "訊息沒給修復入口:%r" % v

    def test_a_complete_to_spec_is_clean(self, tmp_path, monkeypatch):
        """**成對的另一半。**"""
        root = _to_spec_root(tmp_path, VALID_TO_SPEC)
        monkeypatch.setattr(gate, "ROOT", str(root))
        assert gate.check_to_spec_override() == []


# ─────────────────────────────────────────────────────────────────────────────
# 出貨品的正對照 —— 用**真的**正典,不是語料
# ─────────────────────────────────────────────────────────────────────────────

class TestTheShippedCanonPassesBothChecks:
    """**這個 repo 現在的正典必須是乾淨的。**

    上面各條用最小語料驗**判定邏輯**;這兩條用**真的出貨檔**驗**這個 repo 的事實**。
    兩者都要:語料證明規則會動,出貨品證明現在沒事 ——
    而「規則會動」與「現在沒事」是兩個問題(R6 的
    `test_the_shipped_list_is_clean` 同一個形狀)。

    **它同時是本檔的活體金絲雀**:哪天有人直接跑了 `npx skills update`,
    這兩條會紅,而**紅得比 pre-commit 早** —— 跑測試的人立刻知道,
    不必等到下一次 commit。
    """

    def test_the_shipped_code_review_canon_has_its_third_axis(self):
        assert gate.check_third_axis_mount() == [], (
            "本 repo 的正典 code-review 缺第三軸掛載點 —— "
            "多半是直接跑了 npx skills update;修復:bash scripts/skills-update.sh")

    def test_the_shipped_to_spec_canon_has_its_override(self):
        assert gate.check_to_spec_override() == [], (
            "本 repo 的正典 to-spec 缺 inline snippet 覆寫掛載點 —— "
            "修復:bash scripts/skills-update.sh")


# ─────────────────────────────────────────────────────────────────────────────
# 面 C / F —— 位置(批 2)
#
# **這兩面守的失效模式與 B / E 不同,而且更難看見。**
# `gate.py:2289-2291` 逐字:
#
#     錨點插入法真正的失效模式不是「掛載點消失」,
#     而是上游改動錨點附近結構、patch 插進去但位置錯了 —— 此時字串全在、卻掛錯地方。
#
# **「字串全在」就是問題所在**:面 B / E 是字串比對,它們在這種狀態下**全綠**。
# ─────────────────────────────────────────────────────────────────────────────

# 3b 節搬到「### 4.」之後 —— 四個 marker 一個不少
CANON_3B_AFTER_SECTION_4 = (
    "### 3. Identify the standards sources\n"
    "\n"
    "### 4. Spawn\n"
    "\n"
    "### 3b. Identify the data-integrity sources\n"
    "Clean degradation is mandatory.\n"
    "**Data Integrity sub-agent prompt**\n"
    "Exemption reconciliation (local addition)\n"
    "\n"
    "### 5. Aggregate\n"
)

# prompt 搬到「### 4.」之前
CANON_PROMPT_BEFORE_SECTION_4 = (
    "### 3. Identify the standards sources\n"
    "\n"
    "### 3b. Identify the data-integrity sources\n"
    "Clean degradation is mandatory.\n"
    "**Data Integrity sub-agent prompt**\n"
    "\n"
    "### 4. Spawn\n"
    "Exemption reconciliation (local addition)\n"
    "\n"
    "### 5. Aggregate\n"
)

# **2026-08-17 探針用的那一種**:掛載點都在,但整段搬到檔尾
CANON_ALL_MOVED_TO_THE_END = (
    "### 4. Spawn\n"
    "\n"
    "### 5. Aggregate\n"
    "\n"
    "### 3. Identify the standards sources\n"
    "### 3b. Identify the data-integrity sources\n"
    "Clean degradation is mandatory.\n"
    "**Data Integrity sub-agent prompt**\n"
    "Exemption reconciliation (local addition)\n"
)

# 上游把錨點改名 —— **四個 marker 一個不少,而錨點不見了**
CANON_RENAMED_ANCHOR = VALID_CODE_REVIEW.replace("### 4. Spawn", "### 4. Launch agents")

TO_SPEC_OVERRIDE_BEFORE_IMPL = (
    "LOCAL OVERRIDE (prototype snippets)\n"
    "\n"
    "## Implementation Decisions\n"
    "\n"
    "## Testing Decisions\n"
)

TO_SPEC_OVERRIDE_AFTER_TESTING = (
    "## Implementation Decisions\n"
    "\n"
    "## Testing Decisions\n"
    "\n"
    "LOCAL OVERRIDE (prototype snippets)\n"
)

TO_SPEC_RENAMED_IMPL_ANCHOR = VALID_TO_SPEC.replace(
    "## Implementation Decisions", "## Implementation Notes")

TO_SPEC_RENAMED_TESTING_ANCHOR = VALID_TO_SPEC.replace(
    "## Testing Decisions", "## Test Plan")


class TestR5RefusesAMisplacedThirdAxis:
    """面 C —— **哪一個 repo 狀態確定會讓這條紅?**

    正典 `code-review` 在、四個 `MOUNT_MARKERS` **一個不少**,而它們**掛在錯的地方**:

      3b 節跑到「### 4.」之後
      prompt 跑到「### 4.」之前
      整段被搬到檔尾(2026-08-17 探針用的形狀)
      上游把「### 4. Spawn」改名 -> 錨點消失

    **最後一種是這一面存在的理由。** 那三個錨點
    (`### 3. …` / `### 4. Spawn` / `### 5. Aggregate`)**不在 `MOUNT_MARKERS` 裡** ——
    所以上游改名時**面 B 全綠**,而 patch 已經插到一個沒有意義的位置。
    """

    def _canon(self, tmp_path, monkeypatch, body):
        canon = _write(tmp_path / "SKILL.md", body)
        monkeypatch.setattr(gate, "CANON_CODE_REVIEW", str(canon))
        return canon

    def test_the_3b_section_after_section_4_is_misplaced(self, tmp_path, monkeypatch):
        self._canon(tmp_path, monkeypatch, CANON_3B_AFTER_SECTION_4)
        v = gate.check_third_axis_mount()
        assert len(v) == 1, "3b 掛錯位置卻沒回違規:%r" % v
        assert "位置錯誤" in v[0], v
        assert "3b 節必須落在" in v[0], "沒點名是哪一段掛錯:%r" % v

    def test_the_prompt_before_section_4_is_misplaced(self, tmp_path, monkeypatch):
        self._canon(tmp_path, monkeypatch, CANON_PROMPT_BEFORE_SECTION_4)
        v = gate.check_third_axis_mount()
        assert len(v) == 1, "prompt 掛錯位置卻沒回違規:%r" % v
        assert "Data Integrity sub-agent prompt 必須落在" in v[0], v

    def test_everything_moved_to_the_end_reports_both(self, tmp_path, monkeypatch):
        """**2026-08-17 探針的形狀**,而且兩個子判定都該中。

        只報一條的話,修的人會以為改好那一段就完了 ——
        而另一段仍然掛在錯的地方,**下一次跑會再紅一次,理由不同**。
        """
        self._canon(tmp_path, monkeypatch, CANON_ALL_MOVED_TO_THE_END)
        v = gate.check_third_axis_mount()
        assert len(v) == 1, v
        assert "3b 節必須落在" in v[0], "少報了 3b 那一段:%r" % v
        assert "Data Integrity sub-agent prompt 必須落在" in v[0], (
            "少報了 prompt 那一段:%r" % v)

    def test_a_renamed_anchor_is_caught_here_and_not_by_the_marker_check(
            self, tmp_path, monkeypatch):
        """**這一面存在的理由,寫成一條測試。**

        `### 4. Spawn` **不在 `MOUNT_MARKERS` 裡**,所以上游把它改名時:

            面 B(字串比對)  四個 marker 全在 -> **綠**
            面 C(位置)      i_sec4 == -1     -> **紅**

        少了面 C,這個狀態會**整條通過** —— 而 patch 已經插在一個
        沒有錨點可依附的位置上。
        """
        # 先證明前提:四個 marker 真的一個不少(否則這條測的是別的東西)
        for m in gate.MOUNT_MARKERS:
            assert m in CANON_RENAMED_ANCHOR, (
                "語料把 marker %r 也弄掉了 —— 那就變成在測面 B,不是面 C" % m)
        self._canon(tmp_path, monkeypatch, CANON_RENAMED_ANCHOR)
        v = gate.check_third_axis_mount()
        assert len(v) == 1, "錨點被改名卻整條通過:%r" % v
        assert "sec4=-1" in v[0], (
            "訊息沒把「錨點根本不在」講出來(sec4 應為 -1):%r" % v)

    def test_the_message_carries_the_offsets(self, tmp_path, monkeypatch):
        """**偏移量要印出來。**

        位置錯誤與掛載點消失不同:看不到數字的話,人得自己去檔案裡數 ——
        而「掛在哪裡才對」正是這條規則唯一能給的線索。
        2026-08-17 的探針就是靠這串數字認出「搬到檔尾」那一種的。
        """
        self._canon(tmp_path, monkeypatch, CANON_3B_AFTER_SECTION_4)
        v = gate.check_third_axis_mount()
        for field in ("sec3=", "3b=", "sec4="):
            assert field in v[0], "訊息少了偏移量欄位 %s:%r" % (field, v)

    def test_the_message_points_at_the_patch_anchors(self, tmp_path, monkeypatch):
        """票 13 判準:訊息要說出該去看哪裡。位置錯的修法在 patch 的錨點,不在正典。"""
        self._canon(tmp_path, monkeypatch, CANON_3B_AFTER_SECTION_4)
        v = gate.check_third_axis_mount()
        assert "apply_patches.py" in v[0], "沒指向錨點定義的位置:%r" % v

    def test_the_correct_order_is_clean(self, tmp_path, monkeypatch):
        """**成對的另一半。** 少了它,一支「位置永遠算錯」的實作也會讓上面全綠。"""
        self._canon(tmp_path, monkeypatch, VALID_CODE_REVIEW)
        assert gate.check_third_axis_mount() == []


class TestR5RefusesAMisplacedToSpecOverride:
    """面 F —— **哪一個 repo 狀態確定會讓這條紅?**

    正典 `to-spec` 在、`LOCAL OVERRIDE (prototype snippets)` **也在**,
    而它落在「## Implementation Decisions」與「## Testing Decisions」之外:

      覆寫跑到 Implementation Decisions 之前
      覆寫跑到 Testing Decisions 之後
      上游把任一個錨點改名 -> 那個錨點消失

    **與面 C 同一個形狀**:兩個錨點都**不是**面 E 檢查的字串,
    所以改名時面 E 全綠。
    """

    def _root(self, tmp_path, monkeypatch, body):
        root = _to_spec_root(tmp_path, body)
        monkeypatch.setattr(gate, "ROOT", str(root))
        return root

    def test_the_override_before_the_implementation_anchor_is_misplaced(
            self, tmp_path, monkeypatch):
        self._root(tmp_path, monkeypatch, TO_SPEC_OVERRIDE_BEFORE_IMPL)
        v = gate.check_to_spec_override()
        assert len(v) == 1, "覆寫掛在 Implementation 之前卻沒回違規:%r" % v
        assert "覆寫位置錯誤" in v[0], v

    def test_the_override_after_the_testing_anchor_is_misplaced(
            self, tmp_path, monkeypatch):
        self._root(tmp_path, monkeypatch, TO_SPEC_OVERRIDE_AFTER_TESTING)
        v = gate.check_to_spec_override()
        assert len(v) == 1, "覆寫掛在 Testing 之後卻沒回違規:%r" % v
        assert "覆寫位置錯誤" in v[0], v

    @pytest.mark.parametrize("body,gone", [
        (TO_SPEC_RENAMED_IMPL_ANCHOR, "impl=-1"),
        (TO_SPEC_RENAMED_TESTING_ANCHOR, "test=-1"),
    ])
    def test_a_renamed_anchor_is_caught_here_and_not_by_the_marker_check(
            self, tmp_path, monkeypatch, body, gone):
        """**同面 C 的理由**:兩個錨點都不在面 E 的檢查裡。

        先證明前提 —— 覆寫字串本身還在,所以面 E 綠;紅的必須是位置這一面。
        """
        assert "LOCAL OVERRIDE (prototype snippets)" in body, (
            "語料把覆寫字串也弄掉了 —— 那就變成在測面 E,不是面 F")
        self._root(tmp_path, monkeypatch, body)
        v = gate.check_to_spec_override()
        assert len(v) == 1, "錨點被改名卻整條通過:%r" % v
        assert gone in v[0], "訊息沒把「錨點根本不在」講出來(應含 %s):%r" % (gone, v)

    def test_the_message_carries_the_offsets(self, tmp_path, monkeypatch):
        self._root(tmp_path, monkeypatch, TO_SPEC_OVERRIDE_AFTER_TESTING)
        v = gate.check_to_spec_override()
        for field in ("impl=", "override=", "test="):
            assert field in v[0], "訊息少了偏移量欄位 %s:%r" % (field, v)

    def test_the_correct_order_is_clean(self, tmp_path, monkeypatch):
        """**成對的另一半。**"""
        self._root(tmp_path, monkeypatch, VALID_TO_SPEC)
        assert gate.check_to_spec_override() == []


# ─────────────────────────────────────────────────────────────────────────────
# 批 3 —— 兩層各自的「有沒有被走到」
#
# 前六面驗的是**判定對不對**(給它壞輸入,它認不認得)。
# 這一段驗的是**它有沒有被呼叫**,而那是加嚴驗收的第二題。
#
# **R5 兩層都跑**(票 47 批 0 更正的那件事):
#
#     權威層  gate.py:2419-2420  check_third_axis_mount() + check_to_spec_override()
#                                直接呼叫,**不走快取**
#     前哨    gate.py:2051       mount_violations_cached()  ← 走快取(面 G)
#
# 所以兩層各要一組,而且**都餵真的壞正典**,不是替換判定函式。
# **不用 `co_names`** —— 那證明的是「原始碼裡提到那個名字」,
# 不是「那一行真的被執行到」。
# ─────────────────────────────────────────────────────────────────────────────


def _skills_tree(tmp_path, code_review_body, to_spec_body=VALID_TO_SPEC):
    """造一個完整的 `ROOT`,底下有兩個正典。

    **兩個都要建**,因為 `mode_pre_commit()` 會呼叫兩支 —— 只建一個的話,
    另一支會因為「找不到正典」而回違規,於是斷言的 `rc == 1`
    **有一半是別的原因造成的**(F-103:因為錯的理由而通過)。
    """
    _write(tmp_path / ".agents" / "skills" / "code-review" / "SKILL.md",
           code_review_body)
    _write(tmp_path / ".agents" / "skills" / "to-spec" / "SKILL.md", to_spec_body)
    return tmp_path


def _wire_pre_commit(monkeypatch, root):
    """把 `mode_pre_commit()` 的鄰居全部停掉,只留 R5 那兩行是活的。

    停掉的每一個都有理由,而且理由不同:

      staged_paths        它要 git;而本組驗的不是 staged 檔案那條路徑
      check_skill_copies  R4 —— 讓 rc==1 只可能來自 R5
      check_legacy_list   R6 —— 同上
      shadow_active       影子開著時違規會被寫進 shadow-log 而**回 0**
                          (gate.py:2422-2429)—— 不關的話這一組全部假綠

    **簽名要跟著本體走**:`staged_paths` 的替身漏一個參數,`mode_pre_commit`
    會在取清單那一步就掛掉,而本組要驗的是它**擋下之後**的行為(票 42 / test_gate.py:1852)。
    """
    monkeypatch.setattr(gate, "ROOT", str(root))
    monkeypatch.setattr(gate, "CANON_CODE_REVIEW",
                        str(root / ".agents" / "skills" / "code-review" / "SKILL.md"))
    monkeypatch.setattr(gate, "staged_paths", lambda cwd=None, gitlinks=None: [])
    monkeypatch.setattr(gate, "check_skill_copies", lambda: [])
    monkeypatch.setattr(gate, "check_legacy_list", lambda: [])
    monkeypatch.setattr(gate, "shadow_active", lambda: False)


class TestR5IsActuallyInvokedAtTheAuthoritativeLayer:
    """④ —— **哪一個 repo 狀態確定會讓這條紅?**

    一個 repo,兩個正典都在,而 `code-review`(或 `to-spec`)少一個掛載點 ——
    **`git commit` 必須被擋下,而且訊息裡有 `[R5]`。**

    **這一組與前六面的差別**:前六面直接呼叫 `check_*()`,證明**判定對**;
    這一組走 `mode_pre_commit()`,證明**那兩行真的在權威層的通行路上**。
    規則正確但沒人呼叫,就是 F-017 的形狀 —— 而 R5 到批 3 之前
    **沒有任何測試證明它被呼叫過**(唯一沾邊的是把它 monkeypatch 掉,
    好讓別的規則的呼叫可以被斷言)。

    **兩支各一條**,因為它們是 `gate.py:2419` 與 `:2420` **兩行不同的接線** ——
    拿掉其中一行,另一條測試照樣綠。
    """

    def test_a_broken_code_review_canon_blocks_the_commit(self, tmp_path,
                                                          monkeypatch, capsys):
        root = _skills_tree(tmp_path, VALID_CODE_REVIEW.replace(
            "Clean degradation is mandatory.", "(被上游版覆蓋掉了)"))
        _wire_pre_commit(monkeypatch, root)
        rc = gate.mode_pre_commit()
        err = capsys.readouterr().err
        assert rc == 1, "正典缺掛載點,而 commit 沒有被擋下 —— R5 沒有被權威層呼叫"
        assert "[R5]" in err, "擋下了,但訊息裡沒有 [R5](擋下的是別的規則):%r" % err
        assert "Clean degradation is mandatory." in err, (
            "訊息沒點名少了哪一個掛載點 —— 被擋的人查不到要修什麼:%r" % err)

    def test_a_broken_to_spec_canon_blocks_the_commit(self, tmp_path,
                                                      monkeypatch, capsys):
        """**第二行接線,單獨釘。**

        `code-review` 保持乾淨 —— 所以 `rc == 1` 只可能來自 `check_to_spec_override()`。
        """
        root = _skills_tree(tmp_path, VALID_CODE_REVIEW,
                            to_spec_body=VALID_TO_SPEC.replace(
                                "LOCAL OVERRIDE (prototype snippets)", "(被覆蓋掉了)"))
        _wire_pre_commit(monkeypatch, root)
        rc = gate.mode_pre_commit()
        err = capsys.readouterr().err
        assert rc == 1, "to-spec 缺覆寫掛載點,而 commit 沒有被擋下"
        assert "[R5]" in err, err
        assert "覆寫掛載點" in err, "訊息沒說出缺的是什麼:%r" % err

    def test_a_clean_repo_does_not_block(self, tmp_path, monkeypatch):
        """**成對的另一半,而且這一條最要緊。**

        少了它,一支「`mode_pre_commit` 永遠回 1」的實作會讓上面兩條全綠 ——
        **F-103 實例二的形狀**(只驗結果的一半)。
        """
        root = _skills_tree(tmp_path, VALID_CODE_REVIEW)
        _wire_pre_commit(monkeypatch, root)
        assert gate.mode_pre_commit() == 0, "兩個正典都乾淨,卻擋下了 commit"

    def test_the_two_halves_are_wired_independently(self, tmp_path, monkeypatch,
                                                    capsys):
        """**兩行接線各自成立,不是「有一行就夠了」。**

        兩個正典**同時**壞掉時,兩則訊息都要出現。只出現一則的話,
        修的人會以為修好那一個就完了 —— 而另一個仍然壞著,
        **下一次 commit 會再擋一次,理由不同**。
        """
        root = _skills_tree(
            tmp_path,
            VALID_CODE_REVIEW.replace("Clean degradation is mandatory.", "(沒了)"),
            to_spec_body=VALID_TO_SPEC.replace(
                "LOCAL OVERRIDE (prototype snippets)", "(沒了)"))
        _wire_pre_commit(monkeypatch, root)
        rc = gate.mode_pre_commit()
        err = capsys.readouterr().err
        assert rc == 1, err
        assert "缺第三軸掛載點" in err, "少報了 code-review 那一半:%r" % err
        assert "覆寫掛載點" in err, "少報了 to-spec 那一半:%r" % err


class TestR5IsActuallyInvokedAtTheSentinel:
    """面 G 的真實輸入版 —— **哪一個 repo 狀態確定會讓這條紅?**

    同樣是「正典少一個掛載點」,但走的是**前哨**那條路
    (`mount_violations_cached()`,`gate.py:2051`)。

    **與既有那五條快取測試的差別**:那五條把
    `_mount_violations_uncached` / `_skills_mtime` 都換成 `lambda`,
    測的是**快取的失效邏輯**;被快取的東西是合成的。
    **它們是快取的正對照,不是 R5 的正對照。**

    這一組反過來:**兩個都不換**,餵真的壞正典、用真的檔案系統 mtime,
    驗的是「前哨這條路上,真的壞正典會不會被擋」。

    **`MOUNT_CACHE` 一定要指到 tmp** —— 不指的話這一組會寫進宿主真實的
    `.cache/mount-check.json`,而那是閘門下一次判定的輸入(票 18 的形狀:
    測試去改變閘門之後的判斷)。
    """

    def _wire(self, monkeypatch, root):
        monkeypatch.setattr(gate, "ROOT", str(root))
        monkeypatch.setattr(gate, "CANON_CODE_REVIEW",
                            str(root / ".agents" / "skills" / "code-review" / "SKILL.md"))
        monkeypatch.setattr(gate, "MOUNT_CACHE", str(root / "mount-check.json"))

    def test_a_broken_canon_makes_the_sentinel_block(self, tmp_path, monkeypatch):
        root = _skills_tree(tmp_path, VALID_CODE_REVIEW.replace(
            "Clean degradation is mandatory.", "(被上游版覆蓋掉了)"))
        self._wire(monkeypatch, root)
        assert gate.mode_hook_would_block_on_mounts() is True, (
            "正典缺掛載點,而前哨述詞說可以放行")

    def test_a_clean_canon_lets_the_sentinel_pass(self, tmp_path, monkeypatch):
        """**成對的另一半。**"""
        root = _skills_tree(tmp_path, VALID_CODE_REVIEW)
        self._wire(monkeypatch, root)
        assert gate.mode_hook_would_block_on_mounts() is False

    def test_the_cache_file_records_the_real_violation(self, tmp_path, monkeypatch):
        """快取寫下去的必須是**真的那一條違規**,不是空殼。

        寫錯的話下一次會沿用一個空的結果 —— 而**沿用空結果就是放行**。
        """
        root = _skills_tree(tmp_path, VALID_CODE_REVIEW.replace(
            "Clean degradation is mandatory.", "(沒了)"))
        self._wire(monkeypatch, root)
        gate.mount_violations_cached()
        cached = json.loads(io.open(str(root / "mount-check.json"),
                                    encoding="utf-8").read())
        assert cached["violations"], "快取檔裡沒有違規 —— 下一次會沿用一個空結果"
        assert "Clean degradation is mandatory." in cached["violations"][0], cached

    def test_fixing_the_canon_invalidates_the_cache(self, tmp_path, monkeypatch):
        """**真實的失效條件,不是合成的 mtime。**

        既有那五條用 `lambda: 1000.0` / `lambda: 2000.0` 表達「時間變了」;
        這一條**真的改檔案、真的讓 mtime 前進**,然後看快取有沒有跟上。

        `os.utime` 是必要的,不是造假:同一秒內寫兩次檔,檔案系統的
        mtime 解析度可能給出同一個值,而那會讓這條測試**隨機綠隨機紅**。
        推進的是**真實的檔案系統 mtime**(判定讀的就是它),不是替換讀取函式。
        """
        canon_dir = tmp_path / ".agents" / "skills" / "code-review"
        root = _skills_tree(tmp_path, VALID_CODE_REVIEW.replace(
            "Clean degradation is mandatory.", "(沒了)"))
        self._wire(monkeypatch, root)
        assert gate.mount_violations_cached(), "前提不成立:壞正典沒有產生違規"

        _write(canon_dir / "SKILL.md", VALID_CODE_REVIEW)
        later = os.path.getmtime(str(canon_dir / "SKILL.md")) + 10
        os.utime(str(canon_dir / "SKILL.md"), (later, later))
        os.utime(str(tmp_path / ".agents" / "skills"), (later, later))

        assert gate.mount_violations_cached() == [], (
            "正典修好了、mtime 也前進了,而快取還在回報舊的違規 —— "
            "失效條件沒有生效,使用者會看到一條已經不存在的違規")
