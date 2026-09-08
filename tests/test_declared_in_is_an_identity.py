# -*- coding: utf-8 -*-
"""票 116 B-8 —— 帳本的 `declared_in` 記**身分**,不記**位置**。

## 判準

> **帳本不得記錄一個在讀者的 repo 裡不保證存在的位置。**

`declared_in` 會被寫進 `.dev/gate-exemptions.jsonl`,而那份帳本**跟著 repo 走** ——
上游、兩個下游各有一份。記路徑的話,那個路徑只在**寫它的那台 repo** 上有意義。

**ADR 編號是跨 repo 穩定的身分**(`0004` 就是 `0004`);
**`docs/adr/0004-….md` 是位置**,而 `docs/adr/` 在 portable-manifest 標 `ask`
——**安裝時不帶過去**,所以下游不保證有那個檔。

**與票 114 B-2 步驟 6「引符號名不引行號」是同一條**,今天第三次:
**引身分,不引位置。**

## ⚠ 第 4 個呼叫點刻意不動,而那不是例外

`reason='ticket-declared'` 那一條記的是**票的相對路徑**,本票**一個字不改**。
理由是同一條規則的結果,不是它的例外:

> **票沒有跨 repo 穩定的身分。** 上游的票在 `docs/tickets/<feature>/`,
> 下游的票在 `.scratch/<feature>/issues/` —— **兩邊的號碼不是同一個命名空間**。
> **不存在的身分不能拿來引用**,那種情況下路徑是現有最好的識別碼。

而且那一條是**唯一真的被讀回來判定的**(`logged_exemption_backed` →
`committed_declaration` → 找 `**Untested by decision:**`)。
把它改成編號會讓 `git cat-file blob HEAD:<編號>` 找不到票 ⇒
**唯一有效的那條豁免路徑會壞掉**。由 `TestTheTicketDeclaredPathIsUntouched` 釘住。

## ⚠ 本檔守得住什麼、守不住什麼

**守得住**:呼叫點寫的是編號不是路徑,而且呼叫點的集合沒有偷偷長大。
**那是框架的性質**(只讀 `gate.py` 的 AST),在任何 repo 都成立 ⇒ 本檔標 `copy` 出貨。

**不在本檔**:「編號在 `docs/adr/` 解析得到」——
那是**這個 repo 的資料**,在下游不成立(`docs/adr/` 標 `ask` 不出貨,
兩個下游手上那份停在裝機時那一版)。它住在
`tests/test_adr_numbers_resolve_upstream.py`,**標 `skip` 不出貨**。
拆檔的理由寫在那一檔的 docstring 裡 —— 票 114 收尾那一刀踩過同一格。

**守不住**:那份 ADR 在**下游**存不存在。
**B-8 只讓帳本誠實,不讓 ADR 可達** ——
後者的到期條件寫在 `portable-manifest.txt:182-193`(票 66 落地 + `docs/adr/` 改回 `copy`),
不在本票。
"""

import ast
import importlib.util
import io
import os
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
GATE_SRC = ROOT / ".claude" / "hooks" / "gate.py"
ADR_DIR = ROOT / "docs" / "adr"


def _load_gate():
    spec = importlib.util.spec_from_file_location("gate_for_declared_in", GATE_SRC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gate = _load_gate()

# ── 呼叫點的形態登記表 ────────────────────────────────────────────────────────
#
# **鍵是 `reason`,不是行號** —— 行號是位置,`reason` 是那個呼叫點的身分。
# (本檔自己就在示範它要守的那條判準。)
#
# 形態只有兩種,而這個集合是**封閉**的:`note_exemption` 的呼叫點可以窮舉
# (`F-087`:封閉且可窮舉時,枚舉勝過比對)。新增第 5 個而沒有在這裡登記形態
# ⇒ `test_every_call_site_has_a_registered_form` 紅。

ADR_NUMBER = "ADR 編號"
TICKET_PATH = "票的相對路徑"

CALL_SITE_FORMS = {
    "gate-self-modification": (ADR_NUMBER, "0004"),
    "upstream-identical":     (ADR_NUMBER, "F-0016"),
    "upstream-provenance":    (ADR_NUMBER, "F-0014"),
    "ticket-declared":        (TICKET_PATH, None),
}

DEFAULT_REASON = "ticket-declared"     # note_exemption 的 reason 預設值


def _call_sites():
    """`gate.py` 裡所有 `note_exemption(...)` 呼叫。**用 ast 枚舉,不用 grep。**

    回 `[(行號, reason, declared_in 的 AST 節點)]`。

    枚舉而不是掃字串的理由:呼叫點是封閉集合,而 `ast` 把它列得完
    —— 註解裡提到 `note_exemption` 不會被算進去,跨行的呼叫也不會漏
    (`F-087`;而票 114 刀三踩過掃字串掃到自己 docstring 的坑)。
    """
    tree = ast.parse(io.open(str(GATE_SRC), encoding="utf-8").read())
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if not (isinstance(f, ast.Name) and f.id == "note_exemption"):
            continue
        if len(node.args) < 5:
            raise AssertionError(
                "note_exemption 在 gate.py:%d 的呼叫少於 5 個位置參數 —— "
                "簽名變了,本檔的第 5 個參數假設不再成立" % node.lineno)
        reason = DEFAULT_REASON
        for kw in node.keywords:
            if kw.arg == "reason":
                assert isinstance(kw.value, ast.Constant), (
                    "gate.py:%d 的 reason 不是字面常數,本檔無從枚舉" % node.lineno)
                reason = kw.value.value
        out.append((node.lineno, reason, node.args[4]))
    return out


def _literal_or_none(node):
    """字面字串回它的值;是變數(或別的表達式)回 `None`。"""
    return node.value if isinstance(node, ast.Constant) else None


class TestTheCallSitesAreEnumerable:
    """先證明枚舉本身是活的 —— 否則底下每一條都可能因為「掃到 0 個」而恆綠。"""

    def test_the_scan_finds_call_sites(self):
        sites = _call_sites()
        assert sites, "一個 note_exemption 呼叫都沒掃到 —— 底下的斷言全是空的"

    def test_the_count_matches_the_registry(self):
        """呼叫點數與登記表筆數相等。**新增第 5 個而未登記 ⇒ 紅。**"""
        sites = _call_sites()
        assert len(sites) == len(CALL_SITE_FORMS), (
            "note_exemption 有 %d 個呼叫點,而登記表有 %d 筆 —— "
            "新增了呼叫點卻沒登記它的 declared_in 形態。實際:%s"
            % (len(sites), len(CALL_SITE_FORMS),
               [(ln, rs) for ln, rs, _ in sites]))


class TestEveryCallSiteHasARegisteredForm:
    """**值域枚舉(`F-087`)**:每一個呼叫點的形態恰好落在登記的兩種之一。"""

    def test_every_reason_is_registered(self):
        for lineno, reason, _ in _call_sites():
            assert reason in CALL_SITE_FORMS, (
                "gate.py:%d 的 reason=%r 沒有登記 declared_in 的形態 —— "
                "新增呼叫點時要同時決定它記身分還是記位置" % (lineno, reason))

    def test_no_registry_entry_is_stale(self):
        """反向:登記表裡不得有已經不存在的呼叫點。"""
        live = {reason for _, reason, _ in _call_sites()}
        stale = set(CALL_SITE_FORMS) - live
        assert not stale, "登記表有已消失的呼叫點:%s" % sorted(stale)

    def test_each_call_site_matches_its_registered_form(self):
        """形態要對得上:登記 `ADR 編號` 的就得是字面編號,登記票路徑的就得是變數。"""
        bad = []
        for lineno, reason, node in _call_sites():
            form, expect = CALL_SITE_FORMS[reason]
            lit = _literal_or_none(node)
            if form == ADR_NUMBER:
                if lit != expect:
                    bad.append("gate.py:%d reason=%r 應為字面編號 %r,實得 %r"
                               % (lineno, reason, expect, lit))
            else:
                if lit is not None:
                    bad.append("gate.py:%d reason=%r 應為變數(票的相對路徑),"
                               "實得字面 %r" % (lineno, reason, lit))
        assert not bad, "\n  ".join([""] + bad)


class TestAdrDeclaredInIsAnIdentityNotALocation:
    """**紅燈甲**:三個 ADR 呼叫點寫的是**編號**,不是路徑。"""

    @staticmethod
    def _adr_literals():
        out = []
        for lineno, reason, node in _call_sites():
            if CALL_SITE_FORMS.get(reason, (None, None))[0] != ADR_NUMBER:
                continue
            out.append((lineno, reason, _literal_or_none(node)))
        return out

    def test_the_corpus_is_not_empty(self):
        """反控:掃到 0 個 ADR 呼叫點的話,底下兩條恆綠。"""
        assert self._adr_literals(), "一個 ADR 型呼叫點都沒掃到"

    def test_no_adr_declared_in_contains_a_path_separator(self):
        bad = [(ln, rs, v) for ln, rs, v in self._adr_literals()
               if v is None or "/" in v]
        assert not bad, (
            "這些 declared_in 含 `/` —— 那是**位置**不是身分,"
            "而位置只在寫它的那台 repo 上有意義:%s" % bad)

    def test_no_adr_declared_in_carries_a_file_extension(self):
        bad = [(ln, rs, v) for ln, rs, v in self._adr_literals()
               if v is None or v.endswith(".md")]
        assert not bad, (
            "這些 declared_in 以 `.md` 結尾 —— 那是檔名(位置),不是編號(身分):%s"
            % bad)


class TestTheTicketDeclaredPathIsUntouched:
    """**紅燈丙(反控)**:第 4 個呼叫點沒有被誤傷。

    ⚠ **這一條在改動前後都該綠 —— 它是釘子,不是紅燈。**
    照票 114 收尾那一刀的先例明說:
    **為儀式造一個恆綠的東西並稱之為紅燈,比沒有紅燈更糟。**

    它守的是本票**最容易做壞**的一格:把「四個都改成編號」做下去的話,
    `git cat-file blob HEAD:<編號>` 找不到票 ⇒
    `committed_declaration` 回 `None` ⇒ **唯一真的在運作的那條豁免路徑靜默失效**,
    而上面每一條都還是綠的。
    """

    def test_the_ticket_declared_site_still_passes_a_variable(self):
        sites = [(ln, rs, node) for ln, rs, node in _call_sites()
                 if rs == DEFAULT_REASON]
        assert len(sites) == 1, "ticket-declared 呼叫點不是恰好 1 個:%s" % sites
        lineno, _, node = sites[0]
        assert _literal_or_none(node) is None, (
            "gate.py:%d 的 declared_in 變成字面值了 —— 票的路徑是算出來的,"
            "寫死表示那條路徑被改成常數,而票沒有跨 repo 穩定的身分" % lineno)
        assert isinstance(node, ast.Name), (
            "gate.py:%d 的 declared_in 不是那個由 ticket_untested_modules 回傳的變數"
            % lineno)

    def test_ticket_untested_modules_still_returns_a_relative_path(
            self, tmp_path, monkeypatch):
        """行為面:那個變數拿到的仍然是**票的相對路徑**,不是編號。"""
        repo = tmp_path / "repo"
        d = repo / "docs" / "tickets" / "f"
        d.mkdir(parents=True)
        io.open(str(d / "01-x.md"), "w", encoding="utf-8", newline="\n").write(
            u"# 票\n\n**Untested by decision:** thing\n")
        monkeypatch.setattr(gate, "ROOT", str(repo))
        _mods, rel = gate.ticket_untested_modules("f", "01")
        assert rel == "docs/tickets/f/01-x.md", (
            "declared_in 不再是票的相對路徑:%r" % rel)


# ── 既有斷言的引用(不重寫)────────────────────────────────────────────────
#
# 紅燈丙的另一半 ——「`logged_exemption_backed` 對『票在 HEAD 且列了該模組』
# 仍回 True」—— **本檔不重寫**,`tests/test_gate.py` 已經有一條同義的:
#
#     tests/test_gate.py::TestUntestedByDecisionCannotBeSelfServed
#         ::test_the_commit_time_check_accepts_a_committed_ticket
#
# 它造一個真 git repo、commit 一張帶宣告的票、寫一筆指向它的帳本紀錄,
# 然後斷言 `logged_exemption_backed(...) is True`。
# **本票不改那條路徑上的任何東西,所以那條測試就是丙的行為面反控。**
# 在這裡點名是為了讓它**可搜尋** —— `F-086`:命名是為了讓它可搜尋,
# 而「同一份判準寫在別的檔案裡」不會讓這個檔變安全,所以這裡只引用不複製。
