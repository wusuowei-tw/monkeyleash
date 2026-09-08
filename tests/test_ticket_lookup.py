# -*- coding: utf-8 -*-
"""`.claude/portable/ticket_lookup.py` —— portable 這一側唯一一份「依票號找票檔」。

## 這支模組為什麼存在(票 114 刀三 B-2)

`status._find_ticket_file` 與 `mcp_server._ticket_path` 原本是**兩份逐字幾乎相同**
的實作(2026-09-08 實測:對八組輸入答案全同,而那是巧合不是保證)。
本票把那一份判準收成一支,兩邊改成呼叫它。

**`gate.ticket_untested_modules` 不在其中,而且刻意不共用**(票 42:
權威層 import `portable/` 會多一個失效點,而閘門起不來的樣子跟沒裝一模一樣)。
兩邊的行為一致由 `tests/test_ticket_path_parity.py` 釘住 —— 綁行為,不綁字面。

## ⚠ 這支模組的硬性約束(裁 3,見 `mcp_server.py:10-20`)

`mcp_server` 會 import 它,而那個行程**從頭到尾不得有 `gate`、不得自己開 git**:

  - **不 import `gate`、不 import `status`**
  - **不開 git、不跑子程序**
  - **不讀 `gate.TICKET_DIRS`** —— 目錄清單由**呼叫端**展開後當參數傳進來

前例是 `.claude/portable/friction_heading.py`(portable 側的共用判準模組),
載入寫法照抄:`sys.path.insert(0, <本檔目錄>)` + 裸 `import`。

**本檔的測試自己也守那些約束**(見 `TestTheModuleStaysDependencyFree`)——
少了那組,約束只活在上面這段散文裡,而**散文不是機制**。
"""

import importlib.util
import io
import os
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / ".claude" / "portable" / "ticket_lookup.py"


def _load():
    spec = importlib.util.spec_from_file_location("ticket_lookup_ut", SRC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lookup = _load()


@pytest.fixture()
def dirs(tmp_path):
    """兩個票目錄,順序固定 —— 第一個裡面沒有 114,好讓第二個真的被走到。"""
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()
    for d, names in ((a, ["01-first.md", "50-x.md"]),
                     (b, ["114-a.txt", "114-c.md", "114-d.md", "x114-e.md"])):
        for n in names:
            io.open(str(d / n), "w", encoding="utf-8", newline="\n").write(u"x\n")
    return [str(a), str(b)]


class TestItFindsTheTicketFile:

    def test_a_plain_hit(self, dirs):
        assert os.path.basename(lookup.find(dirs, "01")) == "01-first.md"

    def test_it_returns_an_absolute_path(self, dirs):
        """**回絕對路徑** —— 模組 docstring 寫死的契約。

        三個呼叫端原本兩種形式(status/mcp 絕對、gate 相對),
        契約不寫死的話每個呼叫端都要猜,而猜錯不會有東西說話。
        """
        p = lookup.find(dirs, "01")
        assert os.path.isabs(p), p

    def test_it_walks_every_directory_not_just_the_first(self, dirs):
        """第一個目錄沒有 114,必須繼續找第二個。"""
        assert os.path.basename(lookup.find(dirs, "114")) == "114-c.md"

    def test_directory_order_decides_which_one_wins(self, tmp_path):
        """兩個目錄都有同一個票號時,**清單順序決定**,不是檔名排序決定。"""
        a, b = tmp_path / "a", tmp_path / "b"
        a.mkdir()
        b.mkdir()
        io.open(str(a / "114-zzz.md"), "w", encoding="utf-8").write(u"x")
        io.open(str(b / "114-aaa.md"), "w", encoding="utf-8").write(u"x")
        assert os.path.basename(lookup.find([str(a), str(b)], "114")) == "114-zzz.md"
        assert os.path.basename(lookup.find([str(b), str(a)], "114")) == "114-aaa.md"


class TestTheBoundaryAndTheExtension:

    def test_the_prefix_needs_the_dash_boundary(self, dirs):
        """**比的是 `<號>-`,不是 `<號>`**(票 101 裁 4)。

        裸前綴下 `"1"` 會命中 `10-*.md`,而**回錯一份票比回不出來糟得多**:
        回不出來的人會再查,拿到一份看起來對的票的人不會。
        """
        assert lookup.find(dirs, "1") is None
        assert lookup.find(dirs, "5") is None

    def test_a_ticket_number_in_the_middle_of_a_name_is_never_returned(self, dirs):
        """查 `114` 不得回 `x114-e.md` —— **號碼要在檔名開頭**。

        (第一版這條寫成 `find(dirs, "x114") is None`,而那是**測錯東西**:
        `x114-e.md` 對前綴 `x114-` 是合法命中,回它才對。
        邊界要問的是「查 `114` 會不會撈到 `x114-…`」,不是「查 `x114` 有沒有結果」。)
        """
        got = lookup.find(dirs, "114")
        assert os.path.basename(got) != "x114-e.md", got
        assert os.path.basename(got) == "114-c.md", got

    def test_a_name_whose_own_prefix_matches_is_still_a_legitimate_hit(self, dirs):
        """**反控**:上一條不得靠「`x114-` 永遠找不到」而成立。

        少了這一條,一個把所有非數字開頭都拒掉的實作也會讓上一條綠,
        而那是另一條規則(本模組不管票號長什麼樣,只管邊界與副檔名)。
        """
        assert os.path.basename(lookup.find(dirs, "x114")) == "x114-e.md"

    def test_a_non_md_file_with_the_right_prefix_is_skipped(self, dirs):
        """**`.md` 過濾** —— `114-a.txt` 的 sorted 位置在 `114-c.md` **之前**。

        這一條是票 114 刀三的核心:沒有過濾的話,選到的會是那個 `.txt`。
        語料自證見下一條。
        """
        assert os.path.basename(lookup.find(dirs, "114")) == "114-c.md"

    def test_the_corpus_actually_separates_the_extension(self, dirs):
        """**語料反控**:`.txt` 必須排在 `.md` 之前,否則上一條恆綠。"""
        names = sorted(os.listdir(dirs[1]))
        assert names.index("114-a.txt") < names.index("114-c.md"), names


class TestAbsentAndDegenerateInputs:

    def test_an_unknown_ticket_is_none(self, dirs):
        assert lookup.find(dirs, "999") is None

    @pytest.mark.parametrize("ticket", ["", None])
    def test_an_empty_ticket_is_none_not_a_wildcard(self, dirs, ticket):
        """空票號回 `None`,**不是**「前綴為 `-` 所以什麼都不中」那種偶然。

        寫成偶然的話,哪天前綴組法改了就會變成通配,而那是靜默的。
        """
        assert lookup.find(dirs, ticket) is None

    def test_an_empty_directory_list_is_none(self):
        assert lookup.find([], "114") is None

    def test_a_nonexistent_directory_does_not_raise(self, tmp_path):
        """契約是「已展開且**存在**的目錄清單」,但傳進不存在的也不得炸。

        呼叫端與本模組之間會有時間差(目錄可能剛被刪),
        而一個 `FileNotFoundError` 會讓整份 status 輸出消失,只為了一格算不出來
        (`status._ticket_dirs` 的 docstring 已經記過同一句)。
        """
        assert lookup.find([str(tmp_path / "nope")], "114") is None


class TestTheModuleStaysDependencyFree:
    """裁 3 的約束要有機器守著 —— **散文不是機制**。

    `mcp_server` 會 import 這支,而那個行程不得有 `gate`、不得自己開 git
    (`mcp_server.py:10-20`:「走子程序不是效能取捨,是把那兩件事關到另一個行程去」)。
    """

    FORBIDDEN = ("gate", "status", "subprocess", "git", "importlib")

    # ⚠ **第一版這裡是子字串掃描**(`"import gate" not in src`),而它紅了 ——
    # 命中的是**本模組 docstring 裡的散文**「不 import gate / status,不開 git」。
    #
    # 修法不是把樣式寫細一點。`CLAUDE.md` 的常駐檢查項逐字:
    # 「**封閉且可窮舉時,枚舉勝過比對** —— 比對的漏是未知的,枚舉的漏是不存在的。
    #  **對封閉集合用 pattern 不是防線弱,是選錯工具**」。
    # 一個模組的 import 是封閉集合,而 `ast` 把它**枚舉**出來:
    # 散文不會被算進去,`from x import y` / `import x as z` 也不會漏。

    @pytest.mark.parametrize("name", FORBIDDEN)
    def test_the_module_does_not_import_the_forbidden_ones(self, name):
        assert name not in self._imported_names(), (
            "%s 被 %s import 了 —— 裁 3 的隔離就沒了(mcp_server 會 import 這支)"
            % (name, SRC.name))

    @staticmethod
    def _imported_names():
        import ast
        tree = ast.parse(io.open(str(SRC), encoding="utf-8").read())
        mods = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods.add(node.module.split(".")[0])
        return mods

    def test_the_ast_check_would_actually_catch_a_forbidden_import(self):
        """**反控**:證明上面那組枚舉真的會咬,而不是恆綠。

        少了它,`_imported_names()` 寫錯(例如回空集合)會讓每一條都綠 ——
        而**恆真的斷言與有效的斷言在測試輸出上長得一模一樣**。
        """
        import ast
        tree = ast.parse("import subprocess\nfrom gate import x\nimport os\n")
        mods = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods.add(node.module.split(".")[0])
        assert {"subprocess", "gate"} <= mods, mods

    def test_prose_mentioning_the_forbidden_names_is_not_a_hit(self):
        """**歸因反控**:本模組的 docstring **確實**寫著「不 import gate」。

        它不該讓上面那組紅 —— 紅的話,測的是散文不是相依。
        (這正是第一版子字串掃描踩到的那一格,釘住免得有人改回去。)
        """
        src = io.open(str(SRC), encoding="utf-8").read()
        assert "import gate" in src, "docstring 那句話不見了,本條就失去對象"
        assert "gate" not in self._imported_names()

    def test_it_does_not_read_ticket_dirs_itself(self):
        """目錄清單必須由呼叫端傳進來,不得在本模組讀 `TICKET_DIRS`。"""
        src = io.open(str(SRC), encoding="utf-8").read()
        assert "TICKET_DIRS" not in src.replace("TICKET_DIRS`", ""), (
            "本模組自己讀了 TICKET_DIRS —— 那會把來源綁死,"
            "而 status 與 mcp 的來源刻意不同(前者從已載入的 gate 取,後者用自己的常數)")

    def test_only_os_is_imported(self):
        """**正控**:確認它真的只靠 `os`,而不是「剛好沒寫那幾個字」。"""
        import ast
        tree = ast.parse(io.open(str(SRC), encoding="utf-8").read())
        mods = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods.add(node.module.split(".")[0])
        assert mods <= {"os"}, "本模組 import 了 %s —— 契約是只靠 os" % sorted(mods)
