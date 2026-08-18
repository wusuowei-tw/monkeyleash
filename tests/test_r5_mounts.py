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
