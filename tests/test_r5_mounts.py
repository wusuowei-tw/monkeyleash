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
import subprocess          # 票 133 批一 ⑤:紅燈要造真 git repo 才分得出 index / 工作樹

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
        v = gate.check_third_axis_mount(
            path=str(tmp_path / "nowhere" / "SKILL.md"))
        assert len(v) == 1, "正典檔不在,R5 卻沒回違規:%r" % v
        assert "找不到正典" in v[0], "訊息沒說出是哪一個前提沒滿足:%r" % v

    def test_a_missing_to_spec_canon_is_a_violation(self, tmp_path, monkeypatch):
        # to-spec 的路徑在函式內組,所以這裡 patch 的是 ROOT(不是 CANON_*)。
        # tmp_path 底下什麼都沒建 -> 那個檔必然不存在。
        monkeypatch.setattr(gate, "ROOT", str(tmp_path))
        v = gate.check_to_spec_override(
            path=str(tmp_path / ".agents" / "skills" / "to-spec" / "SKILL.md"))
        assert len(v) == 1, "to-spec 正典不在,R5 卻沒回違規:%r" % v
        assert "to-spec" in v[0], "訊息沒點名是哪一個檔:%r" % v

    def test_the_two_canons_stay_isolated_from_each_other(self, r5_both_repo):
        """**反控,而且是這個檔案自己的接線**:兩支的隔離必須互不影響。

        ## ⚠ 這一條被改寫過(票 133 批一 ⑥),原本釘的事實已經不成立

        **原本釘的**:`CANON_CODE_REVIEW` 是 **import 時凍結的絕對路徑常數**,
        所以 `monkeypatch.setattr(gate, "ROOT", tmp)` **不會移動它** ——
        原測試名為 `test_patching_root_does_not_move_the_code_review_canon`,
        斷言的是「改 `ROOT` 之後 `check_third_axis_mount()` 仍讀真正典 ⇒ 回 `[]`」。

        **為什麼不成立了**:批一 ⑥ 把它的權威輸入改成 index,來源變成
        `staged_text(CANON_CODE_REVIEW_REL, cwd=…)`,而 `cwd` 預設是 `ROOT`
        ⇒ **改 `ROOT` 現在就是會移動它。** 那個不對稱是被本格**刻意移除**的。

        **現在釘的**:兩支正典的隔離**仍然成立**。

        **保證它的機制是什麼 —— 本測試【不填,也不該填】。**
        原測試把「機制」寫進斷言(它斷言的是「改 `ROOT` 回 `[]`」,
        而那**只是凍結常數這個實作細節的影子**)—— 於是實作一換,
        一條反控就跟著失效,而**它要防的東西一點都沒變**。

        本測試改成直接問**那件要防的事**:
        **「弄壞其中一支,另一支會不會跟著紅?」**
        ⇒ 不論來源是凍結常數、是 `staged_text(<各自的 REL>)`、
        還是下一次又換成別的,**這條斷言的意義都一樣**。

        > **把機制寫進反控,等於讓反控在每次重構時失效一次;
        > 而失效的那一刻看起來像「測試壞了」,不像「它守的東西沒了」。**

        (⚠ 給下一個人:**這一句不是「懶得查」** ——
        票 133 批一 ⑥ 的裁決原本要求填上新機制,實作完成後確認
        本測試確實與機制無關,因此改寫成本段說明。**不要為了填而填。**)
        """
        build = r5_both_repo
        # code-review 壞、to-spec 乾淨 -> 只有前者該說話
        build(code_review=VALID_CODE_REVIEW.replace(
                  "Clean degradation is mandatory.", "(被上游版覆蓋掉了)"),
              to_spec=VALID_TO_SPEC)
        assert gate.check_third_axis_mount(), "前提不成立:壞正典沒有產生違規"
        assert gate.check_to_spec_override() == [], (
            "code-review 壞了,to-spec 那一支跟著紅 —— 兩支的隔離失效")

    def test_the_two_canons_stay_isolated_in_the_other_direction(self, r5_both_repo):
        """**成對的另一半** —— 上一條只證明 A 壞不影響 B。

        少了它,一支「`check_third_axis_mount` 永遠回違規」的實作也會讓上一條綠。
        """
        build = r5_both_repo
        # to-spec 壞、code-review 乾淨 -> 只有後者該說話
        build(code_review=VALID_CODE_REVIEW,
              to_spec=VALID_TO_SPEC.replace(
                  "LOCAL OVERRIDE (prototype snippets)", "(被覆蓋掉了)"))
        assert gate.check_to_spec_override(), "前提不成立:壞正典沒有產生違規"
        assert gate.check_third_axis_mount() == [], (
            "to-spec 壞了,code-review 那一支跟著紅 —— 兩支的隔離失效")


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
        v = gate.check_third_axis_mount(path=str(canon))
        assert len(v) == 1, "少了掛載點 %r,R5 卻沒回違規:%r" % (marker, v)
        assert marker in v[0], "訊息沒點名少了哪一個掛載點:%r" % v
        assert "skills-update.sh" in v[0], "訊息沒給修復入口:%r" % v

    def test_a_complete_canon_is_clean(self, tmp_path, monkeypatch):
        """**成對的另一半。** 少了它,一支「永遠回違規」的實作也會讓上面全綠。"""
        canon = _write(tmp_path / "SKILL.md", VALID_CODE_REVIEW)
        monkeypatch.setattr(gate, "CANON_CODE_REVIEW", str(canon))
        assert gate.check_third_axis_mount(path=str(canon)) == []

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
        v = gate.check_to_spec_override(
            path=str(root / ".agents" / "skills" / "to-spec" / "SKILL.md"))
        assert len(v) == 1, "覆寫掛載點不見了,R5 卻沒回違規:%r" % v
        assert "覆寫掛載點" in v[0], "訊息沒說出缺的是什麼:%r" % v
        assert "skills-update.sh" in v[0], "訊息沒給修復入口:%r" % v

    def test_a_complete_to_spec_is_clean(self, tmp_path, monkeypatch):
        """**成對的另一半。**"""
        root = _to_spec_root(tmp_path, VALID_TO_SPEC)
        monkeypatch.setattr(gate, "ROOT", str(root))
        assert gate.check_to_spec_override(
            path=str(root / ".agents" / "skills" / "to-spec" / "SKILL.md")) == []


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
        v = gate.check_third_axis_mount(path=str(tmp_path / "SKILL.md"))
        assert len(v) == 1, "3b 掛錯位置卻沒回違規:%r" % v
        assert "位置錯誤" in v[0], v
        assert "3b 節必須落在" in v[0], "沒點名是哪一段掛錯:%r" % v

    def test_the_prompt_before_section_4_is_misplaced(self, tmp_path, monkeypatch):
        self._canon(tmp_path, monkeypatch, CANON_PROMPT_BEFORE_SECTION_4)
        v = gate.check_third_axis_mount(path=str(tmp_path / "SKILL.md"))
        assert len(v) == 1, "prompt 掛錯位置卻沒回違規:%r" % v
        assert "Data Integrity sub-agent prompt 必須落在" in v[0], v

    def test_everything_moved_to_the_end_reports_both(self, tmp_path, monkeypatch):
        """**2026-08-17 探針的形狀**,而且兩個子判定都該中。

        只報一條的話,修的人會以為改好那一段就完了 ——
        而另一段仍然掛在錯的地方,**下一次跑會再紅一次,理由不同**。
        """
        self._canon(tmp_path, monkeypatch, CANON_ALL_MOVED_TO_THE_END)
        v = gate.check_third_axis_mount(path=str(tmp_path / "SKILL.md"))
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
        v = gate.check_third_axis_mount(path=str(tmp_path / "SKILL.md"))
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
        v = gate.check_third_axis_mount(path=str(tmp_path / "SKILL.md"))
        for field in ("sec3=", "3b=", "sec4="):
            assert field in v[0], "訊息少了偏移量欄位 %s:%r" % (field, v)

    def test_the_message_points_at_the_patch_anchors(self, tmp_path, monkeypatch):
        """票 13 判準:訊息要說出該去看哪裡。位置錯的修法在 patch 的錨點,不在正典。"""
        self._canon(tmp_path, monkeypatch, CANON_3B_AFTER_SECTION_4)
        v = gate.check_third_axis_mount(path=str(tmp_path / "SKILL.md"))
        assert "apply_patches.py" in v[0], "沒指向錨點定義的位置:%r" % v

    def test_the_correct_order_is_clean(self, tmp_path, monkeypatch):
        """**成對的另一半。** 少了它,一支「位置永遠算錯」的實作也會讓上面全綠。"""
        self._canon(tmp_path, monkeypatch, VALID_CODE_REVIEW)
        assert gate.check_third_axis_mount(path=str(tmp_path / "SKILL.md")) == []


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
        v = gate.check_to_spec_override(
            path=str(tmp_path / ".agents" / "skills" / "to-spec" / "SKILL.md"))
        assert len(v) == 1, "覆寫掛在 Implementation 之前卻沒回違規:%r" % v
        assert "覆寫位置錯誤" in v[0], v

    def test_the_override_after_the_testing_anchor_is_misplaced(
            self, tmp_path, monkeypatch):
        self._root(tmp_path, monkeypatch, TO_SPEC_OVERRIDE_AFTER_TESTING)
        v = gate.check_to_spec_override(
            path=str(tmp_path / ".agents" / "skills" / "to-spec" / "SKILL.md"))
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
        v = gate.check_to_spec_override(
            path=str(tmp_path / ".agents" / "skills" / "to-spec" / "SKILL.md"))
        assert len(v) == 1, "錨點被改名卻整條通過:%r" % v
        assert gone in v[0], "訊息沒把「錨點根本不在」講出來(應含 %s):%r" % (gone, v)

    def test_the_message_carries_the_offsets(self, tmp_path, monkeypatch):
        self._root(tmp_path, monkeypatch, TO_SPEC_OVERRIDE_AFTER_TESTING)
        v = gate.check_to_spec_override(
            path=str(tmp_path / ".agents" / "skills" / "to-spec" / "SKILL.md"))
        for field in ("impl=", "override=", "test="):
            assert field in v[0], "訊息少了偏移量欄位 %s:%r" % (field, v)

    def test_the_correct_order_is_clean(self, tmp_path, monkeypatch):
        """**成對的另一半。**"""
        self._root(tmp_path, monkeypatch, VALID_TO_SPEC)
        assert gate.check_to_spec_override(
            path=str(tmp_path / ".agents" / "skills" / "to-spec" / "SKILL.md")) == []


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
      check_friction_numbers  R9 —— 同上(**票 133 批一 ① 補**,見下)
      shadow_active       影子開著時違規會被寫進 shadow-log 而**回 0**
                          (gate.py:2422-2429)—— 不關的話這一組全部假綠

    **簽名要跟著本體走**:`staged_paths` 的替身漏一個參數,`mode_pre_commit`
    會在取清單那一步就掛掉,而本組要驗的是它**擋下之後**的行為(票 42 / test_gate.py:1852)。

    ## ⚠ R9 這一筆是補的,而它補的不只是一個遺漏

    本 docstring 第一句說「把鄰居**全部**停掉」,而 R9 **一直沒有被停** ——
    它卻一直是綠的。原因是舊版 R9 讀的是 `FRICTION_LOG` 這個**絕對路徑常數**,
    而本 fixture 只 patch 了 `gate.ROOT` ⇒ **R9 讀的是真 repo 的那份 log**,
    而那份剛好乾淨。

    > **一條「只留 R5 是活的」的 fixture,實際上讓 R9 跨出臨時 repo 去讀了真 repo。**
    > 它綠的原因不是隔離成立,是**被讀到的那份資料剛好乾淨**(`F-032` 的形狀:
    > 綠的原因不是你以為的)。

    票 133 批一 ① 把 R9 改讀 index 之後這件事才現形 —— 臨時目錄不是 git repo,
    `git show :<path>` 問不到 ⇒ R9 fail-closed ⇒ 本組紅。
    **修法是把 R9 也停掉**(它本來就該在清單裡),不是放寬 R9 的 fail-closed。

    **停掉它不減少任何涵蓋**:R9「真的被 pre-commit 呼叫」這件事由
    `tests/test_gate.py::TestFrictionNumbersAreUnique::
    test_the_rule_is_actually_invoked_at_the_authoritative_layer` 守著
    (它 patch `check_friction_numbers` 回假違規並斷言 `mode_pre_commit() == 1`)。
    **那條在,所以這裡停掉它是把兩件事分開,不是把守備拿掉。**
    """
    # ── 票 133 批一 ⑤:把臨時 root 變成**真 git repo**,兩個正典 git add 進去 ──
    #
    # **同一個根因的第二次現身,而這次繞不開。**
    # 上面那段 docstring 記的是批一 ①:臨時目錄不是 git repo,規則改讀 index
    # 之後就 fail-closed,而 ① 的修法是「把 R9 也停掉」。
    # **⑤ 停不掉 —— R5 正是這一組要驗的規則。** 停掉它,這一組就什麼都不驗了。
    #
    # ⇒ 改為讓臨時 root 真的是一個 repo。這也**更貼近真實**:
    # `mode_pre_commit()` 本來就只在 git repo 裡跑,一個沒有 index 的 root
    # 從來不是它會遇到的狀態。
    #
    # ⚠ **停用清單裡的 R9 / R6 兩筆仍然需要**:這個 repo 的 index 裡只有兩個正典,
    # 沒有 `docs/agents/friction-log.md`、也沒有 `.agents/legacy-no-redlight.txt`
    # ⇒ 那兩條照樣 fail-closed。**變成真 repo 不等於變成一個完整的 repo。**
    _git_r5(["init", "-q"], root)
    _git_r5(["config", "user.email", "t@t"], root)
    _git_r5(["config", "user.name", "t"], root)
    _git_r5(["add", "-f", "--", ".agents"], root)

    monkeypatch.setattr(gate, "ROOT", str(root))
    monkeypatch.setattr(gate, "CANON_CODE_REVIEW",
                        str(root / ".agents" / "skills" / "code-review" / "SKILL.md"))
    monkeypatch.setattr(gate, "staged_paths", lambda cwd=None, gitlinks=None: [])
    monkeypatch.setattr(gate, "check_skill_copies", lambda: [])
    monkeypatch.setattr(gate, "check_legacy_list", lambda: [])
    # 簽名跟著本體走(票 133 批一 ① 之後本體是 `(path=None, cwd=None)`)。
    monkeypatch.setattr(gate, "check_friction_numbers",
                        lambda path=None, cwd=None: [])
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


# ─────────────────────────────────────────────────────────────────────────────
# 票 133 批一 ⑤ —— R5(to-spec)的權威輸入是 **index**,不是工作樹
#
# ## 這一格的問題與答案
#
# 問:**R5 在 commit 的時點,權威輸入該是哪一個版本?**
# 答:**index**。R5 的命題是「正典 `to-spec` 的 inline snippet 覆寫掛載點還在、
#     而且落在兩個錨點之間」,而**那份正典**指的是要進歷史的那一份。
#     舊版讀工作樹 ⇒ `git add <被上游版蓋掉的>` 之後把工作樹改回來,
#     R5 綠、一份缺覆寫的正典進歷史 —— 而它會讓 skill 開始要求 AI 做 R1 一定會擋的事。
#
# ## ⚠ 本格與 ① ② ③ ④ 的三個差異
#
# **一、R5 兩層都跑,而前哨那條鏈是間接的。**
#   權威層  mode_pre_commit()            -> check_to_spec_override()
#   前哨    mode_hook() -> mount_violations_cached() -> _mount_violations_uncached()
#                                        -> check_to_spec_override()
# ⇒ 前哨那條鏈**必須明確傳參數讀工作樹**。④ 那次是 `check()` 裡兩處,
#   這次是整條鏈 —— 而它是**間接**的,所以更容易被漏掉。
#   釘它的是 ⑤c。
#
# **二、快取不在本票範圍(裁決)。**
# `.cache/mount-check.json` 屬前哨鏈,權威層不走它 ⇒ **不改**。
# ⚠ 它的鍵只有 skill 目錄的 mtime,**沒有「這是哪一個來源的結果」**,
# 而 `git add` 不改檔案 mtime。今天沒問題(權威層不走快取),
# 但**若日後有人把權威層接上快取,兩側會共用同一份判定** —— 登記在此,不處理。
#
# **三、判準是【三元組】,不是 rc,也不是訊息代號。**
# R5 的三則訊息裡**只有一則帶可變字串**:
#   `[R5] 找不到正典 …`                      -> 無可變部分
#   `[R5] 正典 to-spec 缺 inline snippet …`  -> 無可變部分
#   `[R5] … 覆寫位置錯誤:…(實際 impl=%d, override=%d, test=%d)` -> **三個字元偏移**
# 而那三個數字是 `body.find(...)` —— **`body` 就是這次讀到的那一份**
# ⇒ 它們是**這一份內容的指紋**,換來源就換值。
#
# **為什麼 ④ 那格非它不可**:兩份都違規時 rc 與訊息種類都一樣,
# 只有三元組分得出「讀的是哪一份」。
#
# ## 語料(**全部取自本檔既有的,未發明新字串**)
#
#   乾淨:            `VALID_TO_SPEC`
#   違規(帶三元組):`TO_SPEC_OVERRIDE_BEFORE_IMPL`(覆寫在檔首 -> `override=0`)
#                     `TO_SPEC_OVERRIDE_AFTER_TESTING`(Implementation 在檔首 -> `impl=0`)
#
# **兩份的三元組必然不同,而且不必算出確切數字就知道** ——
# 一份的 `override` 是 0、另一份的 `impl` 是 0,
# 而同一份不可能兩個都是 0(兩個不同字串不可能同時起於偏移 0)。
#
# ⚠ **期望值由測試自己用 `.find()` 算,不寫死數字** —— 語料改了期望值跟著改。
# 而為了不讓它退化成「拿同一個字串驗自己」,**正反兩個方向都要斷言**:
# 含 index 那份的三元組、**且不含**工作樹那份的。鑑別力來自兩份語料的差異。
#
# ⚠ **行尾一律 LF**(既有 `_write()` 就是 `newline="\n"`)。
# 工作樹走文字模式讀會把 CRLF 正規化,而 `staged_text` 走位元組解碼不會 ——
# 用 CRLF 構造兩邊差異的話,紅的是行尾不是來源。
# ─────────────────────────────────────────────────────────────────────────────

_TO_SPEC_REL = ".agents/skills/to-spec/SKILL.md"


def _offsets(body):
    """那三個偏移量,用與 `check_to_spec_override()` **同一組字串**算出來。

    ⚠ 這是「期望值與被測對象同源」的形狀,所以它**單獨不足以證明任何事**。
    鑑別力來自呼叫端**同時斷言另一份語料的三元組不出現** ——
    兩份語料不同,而 `find` 對它們給出不同答案。
    """
    return (body.find("## Implementation Decisions"),
            body.find("LOCAL OVERRIDE (prototype snippets)"),
            body.find("## Testing Decisions"))


def _offset_text(body):
    """訊息裡那一段的逐字形式,格式與 `gate.py` 的 `%` 展開相同。"""
    return "impl=%d, override=%d, test=%d" % _offsets(body)


def _git_r5(args, cwd):
    subprocess.run(["git"] + list(args), cwd=str(cwd), capture_output=True,
                   check=False)


@pytest.fixture
def r5_repo(tmp_path, monkeypatch):
    """真 git repo,`.agents/skills/to-spec/SKILL.md` 的 index 與工作樹可以不同。

    `ROOT` 指過去 —— 它同時餵 `check_to_spec_override()` 內部組出來的路徑
    與 `staged_blob` 的 `cwd` 預設值。

    回 `build(staged, worktree, add=True) -> 該檔的絕對路徑`。
    `add=False` 用於 ⑥ —— 檔案在磁碟上但**不在 index 裡**。
    """
    repo = tmp_path / "r5repo"
    repo.mkdir()
    for c in ("init -q", "config user.email t@t", "config user.name t"):
        _git_r5(c.split(), repo)
    monkeypatch.setattr(gate, "ROOT", str(repo))
    p = repo / ".agents" / "skills" / "to-spec" / "SKILL.md"

    def build(staged, worktree, add=True):
        p.parent.mkdir(parents=True, exist_ok=True)
        io.open(str(p), "w", encoding="utf-8", newline="\n").write(staged)
        if add:
            _git_r5(["add", "-f", "--", _TO_SPEC_REL], repo)
        io.open(str(p), "w", encoding="utf-8", newline="\n").write(worktree)
        return str(p)

    return build


class TestR5JudgesTheStagedToSpec:
    """2×2 真值表四格。**無參數呼叫 = 權威層那條路 = 讀 index。**"""

    def test_a_misplaced_override_in_the_index_is_reported(self, r5_repo):
        """① **本格本體**:index 的覆寫位置錯、工作樹乾淨 → 必須回 index 那份的三元組。

        舊版讀工作樹 ⇒ 回 `[]` ⇒ 一份覆寫掛錯地方的正典靜默進歷史,
        而它會讓 skill 開始要求 AI 做 R1 一定會擋的事(`gate.py` 逐字)。
        """
        r5_repo(staged=TO_SPEC_OVERRIDE_BEFORE_IMPL, worktree=VALID_TO_SPEC)
        v = gate.check_to_spec_override()
        assert v, "index 的覆寫位置錯、工作樹乾淨,R5 卻回報乾淨 —— 判的是工作樹"
        assert "覆寫位置錯誤" in v[0], v
        assert _offset_text(TO_SPEC_OVERRIDE_BEFORE_IMPL) in v[0], (
            "三元組不是 index 那份的(期望 %s):%r"
            % (_offset_text(TO_SPEC_OVERRIDE_BEFORE_IMPL), v))

    def test_a_misplaced_override_only_in_the_worktree_is_not_reported(self, r5_repo):
        """② **鑑別格**:index 乾淨、工作樹的覆寫位置錯 → 不可回違規。

        抓「乾脆兩邊都讀」那個偷懶修法 —— 它讓 ① 變綠,
        代價是每一個「skill 剛更新完還沒 add」的狀態都擋死 commit。
        """
        r5_repo(staged=VALID_TO_SPEC, worktree=TO_SPEC_OVERRIDE_AFTER_TESTING)
        v = gate.check_to_spec_override()
        assert v == [], "index 是乾淨的卻被擋 —— 判定對象跑到工作樹去了:%r" % v

    def test_an_agreeing_valid_to_spec_passes(self, r5_repo):
        """③ **反控**:兩邊一致且乾淨 → 不擋。

        少了它,「一律回違規」也能讓 ① 過,而那是把 R5 變成永遠紅 ——
        **而 R5 擋的是前哨與權威層兩層**,永遠紅等於整個 repo 動不了。
        """
        r5_repo(staged=VALID_TO_SPEC, worktree=VALID_TO_SPEC)
        assert gate.check_to_spec_override() == []

    def test_two_different_misplacements_report_the_staged_one(self, r5_repo):
        """④ **一致違規,而且兩份的偏移不同 —— 本批唯一靠三元組分勝負的一格。**

        兩份都會回「覆寫位置錯誤」⇒ **rc 一樣、訊息種類一樣**。
        分得開的只有那三個數字:
          index    `TO_SPEC_OVERRIDE_BEFORE_IMPL`   -> `override=0`
          工作樹    `TO_SPEC_OVERRIDE_AFTER_TESTING` -> `impl=0`
        同一份不可能兩個都是 0 ⇒ **兩個三元組保證不同,論據不依賴算術。**

        **正反都斷言**:含 index 那份的、**且不含**工作樹那份的。
        只斷言前者的話,一個「兩邊都讀再合併」的修法會綠。
        """
        r5_repo(staged=TO_SPEC_OVERRIDE_BEFORE_IMPL,
                worktree=TO_SPEC_OVERRIDE_AFTER_TESTING)
        v = gate.check_to_spec_override()
        assert v and "覆寫位置錯誤" in v[0], "兩份都違規卻沒回違規:%r" % v
        want = _offset_text(TO_SPEC_OVERRIDE_BEFORE_IMPL)
        unwanted = _offset_text(TO_SPEC_OVERRIDE_AFTER_TESTING)
        assert want != unwanted, (
            "兩份語料的三元組竟然相同 —— 本條的前提垮了,它證明不了任何事")
        assert want in v[0], "三元組不是 index 那份的(期望 %s):%r" % (want, v)
        assert unwanted not in v[0], (
            "訊息裡出現工作樹那份的三元組(%s)—— 兩邊都讀了:%r" % (unwanted, v))


class TestR5ExplicitPathStillReadsTheWorktree:
    """⑤ **硬限制反控**:給了 `path` 就讀工作樹,行為與修法前相同。

    少了這一批,把整支改成讀 index 也會讓 ① ② ④ 過 ——
    而那會打壞本檔既有那 8 處(它們 patch `ROOT` 後在 tmp 目錄裡跑,沒有 index),
    以及**前哨那條鏈**。
    """

    def test_a_path_makes_it_read_the_worktree(self, r5_repo):
        """⑤a:`path=…` → 工作樹那一份(位置錯 → 回那一份的三元組)。"""
        p = r5_repo(staged=VALID_TO_SPEC,
                    worktree=TO_SPEC_OVERRIDE_AFTER_TESTING)
        v = gate.check_to_spec_override(path=p)
        assert v and "覆寫位置錯誤" in v[0], (
            "給了 path 卻沒讀工作樹 —— 既有 8 處會一起壞:%r" % v)
        assert _offset_text(TO_SPEC_OVERRIDE_AFTER_TESTING) in v[0], v

    def test_a_path_does_not_peek_at_the_index(self, r5_repo):
        """⑤b:與 ⑤a 相反的一半 —— 工作樹乾淨時不得因為 index 壞而擋。

        少了它,「給了 path 就兩邊都讀」也能讓 ⑤a 綠。
        """
        p = r5_repo(staged=TO_SPEC_OVERRIDE_BEFORE_IMPL, worktree=VALID_TO_SPEC)
        assert gate.check_to_spec_override(path=p) == [], "給了 path 仍去看了 index"


def test_the_sentry_chain_still_reads_the_worktree(r5_repo):
    """⑤c **硬限制,而且是本格最容易被漏掉的那一條 —— 因為它是【間接】的。**

    前哨走的是 `mode_hook()` → `mount_violations_cached()`
    → `_mount_violations_uncached()` → `check_to_spec_override()`,
    而最後那一步目前是**裸呼叫**。預設一旦改成 index,
    **整條前哨鏈的行為會跟著變而那一行一個字都沒動**。

    本條釘住**行為不動**那一邊:前哨時點沒有 index 這回事
    —— skill 檔可能剛被 `scripts/skills-update.sh` 改過,還沒 `git add`。

    **刻意打 `_mount_violations_uncached()` 而不是 `mount_violations_cached()`**:
    後者有快取,而快取**不在本票範圍**(裁決:不改)。
    打未快取的那一支,測的才是來源選擇本身。
    """
    r5_repo(staged=TO_SPEC_OVERRIDE_BEFORE_IMPL, worktree=VALID_TO_SPEC)
    v = gate._mount_violations_uncached()
    assert not [m for m in v if "to-spec" in m], (
        "前哨鏈不再讀工作樹 —— 那一行裸呼叫被預設值連帶換掉了:%r" % v)


def test_a_to_spec_missing_from_the_index_fails_closed_with_a_reason(r5_repo):
    """⑥ **邊界:正典不在 index → fail-closed,訊息要說出前提與修法。**

    檔案在磁碟上、**不在 index 裡**(skill 剛更新完還沒 `git add` 就是這個狀態)。
    工作樹刻意放**乾淨**的那一份:退回工作樹的修法會在這裡拿到一個假綠燈。

    **不得退回工作樹** —— `staged_blob` 的 docstring 逐字:「退回去就是判錯對象,
    而且是往 fail-open 的方向錯」。

    ⚠ **訊息不得沿用「找不到正典」那一句** —— 那句話描述的是「檔案不存在」,
    而這裡檔案存在、只是不在 index 裡。**說錯前提會讓人去找一個不存在的損壞檔案**(票 13)。
    """
    r5_repo(staged=VALID_TO_SPEC, worktree=VALID_TO_SPEC, add=False)
    v = gate.check_to_spec_override()
    assert v, "正典不在 index 裡卻回報乾淨 —— fail-open"
    joined = "\n".join(v)
    assert "R5" in joined and "fail-closed" in joined, (
        "沒標明是 R5 的 fail-closed 那一支:%s" % joined)
    assert "index" in joined and "git add" in joined, (
        "訊息沒說出前提與修法:%s" % joined)
    assert "找不到正典" not in joined, (
        "把「不在 index」說成「檔案不存在」—— 人會去找一個其實還在的檔案:%s" % joined)


# ─────────────────────────────────────────────────────────────────────────────
# 票 133 批一 ⑥ —— R5(code-review)的權威輸入是 **index**,不是工作樹
#
# ## 與 ⑤ 的三個差異(⑤ 的偵察順帶看到的)
#
# **一、⑥ 讀的是【import 時凍結的模組常數】,⑤ 是【函式內用字面組】。**
#   ⑤  `p = os.path.join(ROOT, ".agents", "skills", "to-spec", "SKILL.md")`  <- 函式內
#   ⑥  `CANON_CODE_REVIEW = os.path.join(ROOT, …)`                           <- import 時
# ⇒ **⑥ 會踩到 `FRICTION_LOG_REL` / `LEGACY_LIST_REL` 那個反算陷阱,⑤ 不會。**
#   `rel(CANON_CODE_REVIEW)` 在 `ROOT` 被 patch 時會吐出 `../../..` 逃逸路徑。
#   ⇒ 需要 `CANON_CODE_REVIEW_REL`,理由與 ① ④ 同。
#
# **二、⑥ 的訊息有【兩種】可變內容,⑤ 只有一種。**
#   缺 marker  -> `[R5] 正典 code-review 缺第三軸掛載點:"<哪幾個>"`   <- 清單
#   位置錯     -> `(實際 sec3=%d, 3b=%d, sec4=%d)` 與 `(實際 sec4=%d, prompt=%d, agg=%d)`
#                                                                      <- 兩組三元組
# ⇒ **④ 那格可以用「缺的是哪一個 marker」分,比偏移量穩** ——
#   marker 是固定字串,不隨語料長度變;偏移量會。
#   兩種都用(裁決):正控與 ④ 用 marker,另一格用三元組。
#
# **三、⑤ 已經把前哨鏈那一行改成明確傳參數了** ——
#   ⑥ 只在同一行加上自己那一半,那段「行為不動 ≠ 一個字不動」的註解已涵蓋兩支。
#
# ## ⚠ 一條既有測試被改寫,不是刪除
#
# `test_patching_root_does_not_move_the_code_review_canon` 釘的是
# **本格刻意移除的那個不對稱**(見上面「差異一」)。
# 已改寫為 `test_the_two_canons_stay_isolated_from_each_other`(+ 反向那一半),
# **改問「弄壞其中一支,另一支會不會跟著紅」** —— 不依賴機制,
# 所以原本要防的東西(兩支互相污染時要有人出聲)仍然守得住。
#
# ## 語料(**全部取自本檔既有的,未發明新字串**)
#
#   乾淨:        `VALID_CODE_REVIEW`
#   缺 marker:   `VALID_CODE_REVIEW.replace(<marker>, "(被上游版覆蓋掉了)")`,
#                 marker 取自 `gate.MOUNT_MARKERS`(既有手法,同 `:188`)
#   位置錯:      `CANON_3B_AFTER_SECTION_4`、`CANON_ALL_MOVED_TO_THE_END`
#
# ⚠ **期望值由測試自己算,不寫死**(同 ⑤):marker 直接引 `gate.MOUNT_MARKERS`,
# 三元組用 `.find()` 現算。**正反都斷言** —— 含 index 那份的、且不含工作樹那份的。
# ─────────────────────────────────────────────────────────────────────────────

_CODE_REVIEW_REL = ".agents/skills/code-review/SKILL.md"

# 兩個互不相同的 marker,用來讓 index 與工作樹缺**不同**的那一個。
# 直接從 `gate.MOUNT_MARKERS` 取,不抄字串 —— 上游改了 marker,這裡跟著改。
_MK_A = gate.MOUNT_MARKERS[2]      # "Clean degradation is mandatory."
_MK_B = gate.MOUNT_MARKERS[3]      # "Exemption reconciliation (local addition)"


def _without(marker):
    """既有手法(同 `:188`):把某一個 marker 換掉。"""
    return VALID_CODE_REVIEW.replace(marker, "(被上游版覆蓋掉了)")


def _cr_offsets(body):
    """3b 那一組三元組,用與 `check_third_axis_mount()` **同一組字串**算。

    ⚠ 期望值與被測對象同源 ⇒ **單獨不足以證明任何事**;
    鑑別力來自呼叫端同時斷言**另一份語料的三元組不出現**。
    """
    return (body.find("### 3. Identify the standards sources"),
            body.find("### 3b. Identify the data-integrity sources"),
            body.find("### 4. Spawn"))


def _cr_offset_text(body):
    return "sec3=%d, 3b=%d, sec4=%d" % _cr_offsets(body)


@pytest.fixture
def r5_cr_repo(tmp_path, monkeypatch):
    """真 git repo,`code-review` 正典的 index 與工作樹可以不同。

    `to-spec` 一併放**乾淨**的一份並 `git add` —— 否則 ⑤ 那一支會在
    同一個 repo 裡 fail-closed,而本批打的是 ⑥。

    回 `build(staged, worktree, add=True) -> code-review 正典的絕對路徑`。
    """
    repo = tmp_path / "r5crrepo"
    repo.mkdir()
    for c in ("init -q", "config user.email t@t", "config user.name t"):
        _git_r5(c.split(), repo)
    monkeypatch.setattr(gate, "ROOT", str(repo))
    cr = repo / ".agents" / "skills" / "code-review" / "SKILL.md"
    ts = repo / ".agents" / "skills" / "to-spec" / "SKILL.md"
    _write(ts, VALID_TO_SPEC)
    # ⚠ **`CANON_CODE_REVIEW` 也要 patch,否則鑑別格是假綠。**
    # 它是 import 時凍結的常數,不 patch 的話「讀工作樹」那條路讀到的是
    # **真 repo 的正典**(而那份是乾淨的)⇒ ② 會綠,而綠的原因不是判定對,
    # 是被讀到的資料剛好乾淨(`F-032` 的形狀,本檔 `_wire_pre_commit` 的
    # docstring 記過同一個坑)。
    monkeypatch.setattr(gate, "CANON_CODE_REVIEW", str(cr))

    def build(staged, worktree, add=True):
        cr.parent.mkdir(parents=True, exist_ok=True)
        io.open(str(cr), "w", encoding="utf-8", newline="\n").write(staged)
        if add:
            _git_r5(["add", "-f", "--", _CODE_REVIEW_REL, ".agents/skills/to-spec"],
                    repo)
        else:
            _git_r5(["add", "-f", "--", ".agents/skills/to-spec"], repo)
        io.open(str(cr), "w", encoding="utf-8", newline="\n").write(worktree)
        return str(cr)

    return build


@pytest.fixture
def r5_both_repo(tmp_path, monkeypatch):
    """兩個正典都**進 index**的真 repo —— 給「兩支互相隔離」那兩條用。

    與 `r5_cr_repo` 分開,因為那兩條要的是**兩支都從 index 讀**的乾淨狀態,
    而不是 index/工作樹分歧。
    """
    repo = tmp_path / "r5bothrepo"
    repo.mkdir()
    for c in ("init -q", "config user.email t@t", "config user.name t"):
        _git_r5(c.split(), repo)
    monkeypatch.setattr(gate, "ROOT", str(repo))

    # 理由同 `r5_cr_repo`:不 patch 的話「讀工作樹」那條路會跑去讀真 repo 的正典。
    monkeypatch.setattr(
        gate, "CANON_CODE_REVIEW",
        str(repo / ".agents" / "skills" / "code-review" / "SKILL.md"))

    def build(code_review, to_spec):
        _write(repo / ".agents" / "skills" / "code-review" / "SKILL.md", code_review)
        _write(repo / ".agents" / "skills" / "to-spec" / "SKILL.md", to_spec)
        _git_r5(["add", "-f", "--", ".agents"], repo)
        return repo

    return build


class TestR5JudgesTheStagedCodeReview:
    """2×2 真值表四格。**無參數呼叫 = 權威層那條路 = 讀 index。**"""

    def test_a_missing_marker_in_the_index_is_named(self, r5_cr_repo):
        """① **本格本體**:index 缺一個 marker、工作樹完整 → 必須點名 index 缺的那一個。

        舊版讀工作樹 ⇒ 回 `[]` ⇒ 一份被上游版覆蓋掉第三軸的正典靜默進歷史,
        而**掛載點消失代表 patch 沒被重套**(`gate.py` 逐字)。
        """
        r5_cr_repo(staged=_without(_MK_A), worktree=VALID_CODE_REVIEW)
        v = gate.check_third_axis_mount()
        assert v, "index 缺 marker、工作樹完整,R5 卻回報乾淨 —— 判的是工作樹"
        assert _MK_A in v[0], "沒點名 index 缺的那一個(%r):%r" % (_MK_A, v)

    def test_a_missing_marker_only_in_the_worktree_is_not_named(self, r5_cr_repo):
        """② **鑑別格**:index 完整、工作樹缺 marker → 不可回違規。

        抓「乾脆兩邊都讀」那個偷懶修法 —— 它讓 ① 變綠,
        代價是每一個「skill 剛更新完還沒 add」的狀態都擋死 commit。
        """
        r5_cr_repo(staged=VALID_CODE_REVIEW, worktree=_without(_MK_B))
        v = gate.check_third_axis_mount()
        assert v == [], "index 是完整的卻被擋 —— 判定對象跑到工作樹去了:%r" % v

    def test_an_agreeing_complete_canon_passes(self, r5_cr_repo):
        """③ **反控**:兩邊一致且完整 → 不擋。

        少了它,「一律回違規」也能讓 ① 過 —— 而 R5 擋的是**兩層**,
        永遠紅等於整個 repo 動不了。
        """
        r5_cr_repo(staged=VALID_CODE_REVIEW, worktree=VALID_CODE_REVIEW)
        assert gate.check_third_axis_mount() == []

    def test_two_different_missing_markers_report_the_staged_one(self, r5_cr_repo):
        """④ **一致違規,而兩份缺的是【不同】的 marker。**

        兩份都會回「缺第三軸掛載點」⇒ **rc 一樣、訊息種類一樣**。
        分得開的是**清單裡列了哪一個**。

        **用 marker 而不是偏移量**:marker 是固定字串,不隨語料長度變 ——
        比 ⑤ 那格的三元組穩。

        **正反都斷言**:含 index 缺的那個、**且不含**工作樹缺的那個。
        只斷言前者的話,一個「兩邊都讀再合併」的修法會綠。
        """
        assert _MK_A != _MK_B, "兩個 marker 竟然相同 —— 本條的前提垮了"
        r5_cr_repo(staged=_without(_MK_A), worktree=_without(_MK_B))
        v = gate.check_third_axis_mount()
        assert v, "兩份都缺 marker 卻沒回違規:%r" % v
        assert _MK_A in v[0], "缺的不是 index 那一個(期望 %r):%r" % (_MK_A, v)
        assert _MK_B not in v[0], (
            "訊息裡出現工作樹缺的那一個(%r)—— 兩邊都讀了:%r" % (_MK_B, v))


def test_r5_reports_the_offsets_of_the_staged_canon(r5_cr_repo):
    """**第二種可變內容:偏移三元組。**

    兩份都**位置錯**,而偏移不同:
      index    `CANON_3B_AFTER_SECTION_4`
      工作樹    `CANON_ALL_MOVED_TO_THE_END`

    marker 那一軸在這裡分不出來(兩份的四個 marker 都在),
    **只有三元組分得出讀的是哪一份** —— 與 ⑤ ④ 同型。
    """
    want = _cr_offset_text(CANON_3B_AFTER_SECTION_4)
    unwanted = _cr_offset_text(CANON_ALL_MOVED_TO_THE_END)
    assert want != unwanted, (
        "兩份語料的三元組竟然相同 —— 本條的前提垮了,它證明不了任何事")
    r5_cr_repo(staged=CANON_3B_AFTER_SECTION_4,
               worktree=CANON_ALL_MOVED_TO_THE_END)
    v = gate.check_third_axis_mount()
    assert v and "位置錯誤" in v[0], "兩份都位置錯卻沒回違規:%r" % v
    assert want in v[0], "三元組不是 index 那份的(期望 %s):%r" % (want, v)
    assert unwanted not in v[0], (
        "訊息裡出現工作樹那份的三元組(%s):%r" % (unwanted, v))


class TestR5CodeReviewExplicitPathStillReadsTheWorktree:
    """⑤ **硬限制反控**:給了 `path` 就讀工作樹,行為與修法前相同。

    少了這一批,把整支改成讀 index 也會讓 ① ② ④ 過 ——
    而那會打壞本檔既有那 10 處,以及**前哨那條鏈**。
    """

    def test_a_path_makes_it_read_the_worktree(self, r5_cr_repo):
        """⑤a:`path=…` → 工作樹那一份(缺 marker → 點名那一個)。"""
        p = r5_cr_repo(staged=VALID_CODE_REVIEW, worktree=_without(_MK_B))
        v = gate.check_third_axis_mount(path=p)
        assert v and _MK_B in v[0], (
            "給了 path 卻沒讀工作樹 —— 既有 10 處會一起壞:%r" % v)

    def test_a_path_does_not_peek_at_the_index(self, r5_cr_repo):
        """⑤b:與 ⑤a 相反的一半 —— 工作樹完整時不得因為 index 壞而擋。"""
        p = r5_cr_repo(staged=_without(_MK_A), worktree=VALID_CODE_REVIEW)
        assert gate.check_third_axis_mount(path=p) == [], "給了 path 仍去看了 index"


def test_the_sentry_chain_still_reads_the_worktree_for_code_review(r5_cr_repo):
    """⑤c **前哨鏈,code-review 那一半。**

    ⑤ 已經把 `_mount_violations_uncached()` 那一行改成明確傳參數(to-spec 那半);
    本條釘的是**同一行的另一半**:`check_third_axis_mount` 也必須明確傳工作樹。

    留成裸呼叫的話,整條前哨鏈的 code-review 判定會被預設值連帶換掉
    **而那一行一個字都沒動**。

    **刻意打 `_mount_violations_uncached()`**:`mount_violations_cached()` 有快取,
    而**快取不在本票範圍**(裁決)。打未快取那一支,測的才是來源選擇本身。
    """
    r5_cr_repo(staged=_without(_MK_A), worktree=VALID_CODE_REVIEW)
    v = gate._mount_violations_uncached()
    assert not [m for m in v if "code-review" in m], (
        "前哨鏈的 code-review 那一半不再讀工作樹 —— 裸呼叫被預設值連帶換掉了:%r" % v)


def test_a_code_review_canon_missing_from_the_index_fails_closed(r5_cr_repo):
    """⑥ **邊界:正典不在 index → fail-closed,訊息要說出前提與修法。**

    檔案在磁碟上、**不在 index 裡**。工作樹刻意放**完整**的那一份:
    退回工作樹的修法會在這裡拿到一個假綠燈。

    ⚠ **訊息不得沿用「找不到正典」那一句** —— 那句話描述的是「檔案不存在」,
    而這裡檔案存在、只是不在 index 裡(同 ⑤ 的 ⑥)。
    """
    r5_cr_repo(staged=VALID_CODE_REVIEW, worktree=VALID_CODE_REVIEW, add=False)
    v = gate.check_third_axis_mount()
    assert v, "正典不在 index 裡卻回報乾淨 —— fail-open"
    joined = "\n".join(v)
    assert "R5" in joined and "fail-closed" in joined, (
        "沒標明是 R5 的 fail-closed 那一支:%s" % joined)
    assert "index" in joined and "git add" in joined, (
        "訊息沒說出前提與修法:%s" % joined)
    assert "找不到正典" not in joined, (
        "把「不在 index」說成「檔案不存在」:%s" % joined)
