# -*- coding: utf-8 -*-
"""票 114 刀三 B-2 —— 「依票號找票檔」的**跨層對帳**。

## 對的是「同一個檔」,不是「同一個物件」

`gate.ticket_untested_modules` 與 `.claude/portable/ticket_lookup.find` 是
**兩份刻意保留的實作**(票 42:權威層不得依賴 `portable/`),
所以 `a is b` 這種斷言永遠為假,不能用 —— **綁的是行為**。
與 `tests/test_gate.py::TestBothHeadingCriteriaAgree`、
`tests/test_line_ending_parity.py`、`tests/test_non_source_list_parity.py` 同型。

## ⚠ 路徑形式:比對前一律正規化成「相對 root 的 posix 路徑」

三份原本的回傳形式**不一致**(票 114 步驟 C-2 實測):

    gate.ticket_untested_modules   -> 回傳值第二格是**相對** root 的 posix 字串
    status._find_ticket_file       -> **絕對**路徑
    mcp_server._ticket_path        -> **絕對**路徑
    ticket_lookup.find(新)         -> **絕對**路徑(該模組 docstring 寫死)

**本檔一律折成相對 posix 再比。** 不折的話這條測試會因為
「一個是絕對一個是相對」而恆紅,而那種紅**不是**它要抓的東西。

## ⚠ 語料必須自證「那一格真的被走到了」

票 114 步驟 C-2 的教訓(寫在這裡,因為下一個改語料的人會踩同一個坑):
第一版語料造了一個 `<號>-a.txt` 想測 `.md` 過濾,而 `gate.TICKET_DIRS` 把
`.scratch/%s/issues` 排在 `docs/tickets/%s` 前面 —— `.scratch` 那一筆先命中,
**`docs/` 底下的 `.txt` 一次都沒有被讀到**,八格全同、對帳全綠。

**「綠的原因不是你以為的」(`F-032`)。** 所以本檔的 fixture:
只造 `docs/tickets/<feature>/`(不造 `.scratch/...`),
並且**斷言那個 `.txt` 確實排在 `.md` 之前** —— 語料自己先證明它分得出東西。
"""

import importlib.util
import io
import os
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load(name, *parts):
    """路徑載入(寫法抄 `tests/test_gate.py:336-343`)。"""
    spec = importlib.util.spec_from_file_location(name, ROOT.joinpath(*parts))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gate = _load("gate_for_ticket_parity", ".claude", "hooks", "gate.py")
lookup = _load("ticket_lookup_for_parity", ".claude", "portable", "ticket_lookup.py")

FEATURE = "f"

# (檔名, 要不要建)。**`114-a.txt` 的 sorted 位置排在 `114-c.md` 之前** ——
# 那正是分岔看得見的條件,由 `test_the_corpus_actually_separates_the_md_filter` 自證。
FILES = [
    "01-a.md",
    "10-b.md",
    "114-a.txt",
    "114-c.md",
    "114-d.md",
    "x114-e.md",
]


@pytest.fixture()
def repo(tmp_path):
    """只造 `docs/tickets/<feature>/`。

    **刻意不造 `.scratch/<feature>/issues/`** —— 造了的話它會在
    `gate.TICKET_DIRS` 裡排在前面而先命中,`docs/` 這一輪根本走不到(見模組 docstring)。
    """
    d = tmp_path / "docs" / "tickets" / FEATURE
    d.mkdir(parents=True)
    for n in FILES:
        io.open(str(d / n), "w", encoding="utf-8", newline="\n").write(
            u"**Untested by decision:** none\n")
    return tmp_path


def _dirs(root):
    """展開 `gate.TICKET_DIRS` 後**存在**的目錄(絕對路徑)。

    這一步刻意留在測試裡,不進 `ticket_lookup` —— 那支模組吃的是
    「已展開且存在的目錄清單」,來源留在各自的呼叫端(裁決,票 114)。
    """
    out = []
    for tmpl in gate.TICKET_DIRS:
        d = os.path.join(str(root), (tmpl % FEATURE).replace("/", os.sep))
        if os.path.isdir(d):
            out.append(d)
    return out


def _rel(root, path):
    """折成相對 root 的 posix 字串。`None` 原樣傳遞。"""
    if path is None:
        return None
    p = str(path)
    if os.path.isabs(p):
        p = os.path.relpath(p, str(root))
    return p.replace("\\", "/")


def _gate_side(root, ticket):
    saved = gate.ROOT
    gate.ROOT = str(root)
    try:
        _mods, rel = gate.ticket_untested_modules(FEATURE, ticket)
        return _rel(root, rel)
    finally:
        gate.ROOT = saved


def _lookup_side(root, ticket):
    return _rel(root, lookup.find(_dirs(root), ticket))


CASES = [
    ("同票號 .txt 與 .md 並存", "114"),
    ("票號在檔名中間",           "x114"),
    ("補零票",                   "01"),
    ("不補零",                   "1"),
    ("不存在",                   "999"),
    ("空票號",                   ""),
]


class TestTheCorpusIsAbleToSeparateTheMdFilter:
    """**語料反控:先證明這組 fixture 真的走得到那一格。**

    票 114 步驟 C-2 的第一版語料造了 `.txt` 卻從未讀到它(`.scratch` 先命中),
    於是對帳全綠 —— **恆綠的斷言與有效的斷言在測試輸出上長得一模一樣。**
    """

    def test_the_txt_candidate_sorts_before_the_md_one(self, repo):
        d = repo / "docs" / "tickets" / FEATURE
        names = sorted(os.listdir(str(d)))
        assert "114-a.txt" in names and "114-c.md" in names
        assert names.index("114-a.txt") < names.index("114-c.md"), (
            "`.txt` 排在 `.md` 之後的話,沒有 .md 過濾的實作也會挑到 .md —— "
            "這組語料就分不出有沒有過濾:%s" % names)

    def test_only_one_ticket_dir_exists_so_docs_is_actually_reached(self, repo):
        """**`.scratch` 不得存在** —— 存在的話 docs 這一輪走不到(C-2 的坑)。"""
        dirs = _dirs(repo)
        assert len(dirs) == 1, "票目錄不只一個,docs 可能被前面那個蓋掉:%s" % dirs
        assert dirs[0].replace(os.sep, "/").endswith("docs/tickets/%s" % FEATURE)


class TestTheParityCheckItselfCatchesAMissingMdFilter:
    """**反控:先證明這個對帳真的會咬。**

    形狀照 `tests/test_line_ending_parity.py` 那組(引 `F-103`)。
    做法:拿一份**刻意不做 `.md` 過濾**的假實作當一端,斷言對帳**必須**抓到它。
    """

    @staticmethod
    def _no_md_filter(dirs, ticket):
        """假的一端:只比前綴,不看副檔名。"""
        if not ticket:
            return None
        prefix = str(ticket) + "-"
        for d in dirs:
            for name in sorted(os.listdir(d)):
                if name.startswith(prefix):
                    return os.path.join(d, name)
        return None

    def test_a_side_without_the_md_filter_is_caught(self, repo):
        theirs = _rel(repo, self._no_md_filter(_dirs(repo), "114"))
        mine = _lookup_side(repo, "114")
        assert theirs != mine, (
            "拿一份公認沒有 .md 過濾的實作當對照,對帳竟然沒抓到差異 —— "
            "那代表這組語料分辨不出過濾,對帳斷言是恆真的(實得兩邊都是 %r)" % mine)


class TestGateAndTheSharedLookupAgree:
    """**gate 那份與新模組對同一組輸入必須回同一個檔。**

    不一致代表有一邊在做另一邊以為它沒做的事。而這兩邊不對稱:
    **gate 那份是判定**(它讀回來的檔會被拿去發 R3 豁免),
    新模組那份只是找檔。所以範圍寬的一邊是危險的那一邊。
    """

    @pytest.mark.parametrize("label,ticket", CASES)
    def test_both_sides_return_the_same_file(self, repo, label, ticket):
        a = _gate_side(repo, ticket)
        b = _lookup_side(repo, ticket)
        assert a == b, (
            "%s(票號 %r):gate 回 %r,ticket_lookup 回 %r。\n"
            "gate 那一份是判定(發 R3 豁免),範圍不得寬於找檔那一份 —— "
            "寬了就等於讓票目錄裡任何一個 `<號>-` 開頭的檔案都能發豁免。"
            % (label, ticket, a, b))
