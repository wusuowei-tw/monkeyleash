# -*- coding: utf-8 -*-
"""R8 判定的對象是「套用編輯後的整檔結果」,不是編輯片段(票 07 / F-046)。

現況的缺陷:`mode_hook` 取 `ti.get("content") or ti.get("new_string")`,
Edit 拿到的是**片段**;而 `imports_research()` 用 AST 且 fail-closed。
兩者相乘得到的判定是「**片段不是合法 Python**」⇒「**它 import 了 research**」。
函式內部每一行都是縮排的,所以「改一個函式裡的一行」在 .py 上幾乎必然觸發。

**fail-closed 只保證失敗的方向,不保證問對了問題。** 這是 F-045 的鏡像:
那則是兩個時點方向不一致,這則是同一個時點、方向對了、判定的對象錯了。

本檔的主張:
  - 片段的語法完整性與 R8 要守的東西無關 -> 不得因片段解析失敗而擋
  - **結果**含 import research -> 擋(不論片段長什麼樣)
  - **結果**解析不了 -> 擋(fail-closed 仍在,只是問對了對象)
  - 連內容都讀不到 -> 擋,而且訊息要說「讀不到」,不是「你 import 了 research」
    (誤導的訊息比沒有訊息貴 —— 它讓人去檢查一個根本沒問題的地方)
"""

import importlib.util
import io
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "gate_edit_result", ROOT / ".claude" / "hooks" / "gate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gate = _load()


EXISTING = (
    "import sqlite3\n"
    "\n"
    "from analyst_tracker import schema\n"
    "\n"
    "\n"
    "def put_backup_status(conn, name, status):\n"
    "    return _ins(conn, name, status)\n"
)


@pytest.fixture()
def repo(tmp_path, monkeypatch):
    """把 gate 的 ROOT 挪到 tmp,並在裡面放一支真的既有生產檔。

    Edit 的結果只能從磁碟上的現況算出來,所以這個 fixture 必須是真檔案,
    不能用假的字串替身 —— 替身會讓「讀不到磁碟」這條路徑永遠測不到。

    **chdir 是必要的,不是整潔**:`rel()` 走 `os.path.abspath()`,那是相對 CWD 的。
    只搬 ROOT 不搬 CWD 的話,相對路徑會被算成 `../../…`,而 `check()` 對 repo 以外的
    路徑一律放行 —— 整組測試會**全綠**,綠在「這條路徑不歸我管」上,
    一個判定都沒真的跑到。這正是 F-031 那個形狀:壞掉的訊號比沒有訊號貴。
    """
    monkeypatch.chdir(tmp_path)
    (tmp_path / "analyst_tracker").mkdir()
    io.open(tmp_path / "analyst_tracker" / "store.py", "w",
            encoding="utf-8", newline="\n").write(EXISTING)
    monkeypatch.setattr(gate, "ROOT", str(tmp_path))
    monkeypatch.setattr(gate, "load_stage", lambda: ("implement", "07"))
    return tmp_path


def _edit(old, new, **kw):
    d = {"file_path": "analyst_tracker/store.py",
         "old_string": old, "new_string": new}
    d.update(kw)
    return d


# ─────────────────────────────────────────────────────────────────────────────
# 一、解析器本身:tool_input -> 這次寫入之後檔案會有的內容
# ─────────────────────────────────────────────────────────────────────────────

class TestContentAfterEdit:

    def test_write_content_passes_through(self, repo):
        ti = {"file_path": "analyst_tracker/store.py", "content": "x = 1\n"}
        assert gate.content_after_edit("analyst_tracker/store.py", ti) == "x = 1\n"

    def test_an_edit_resolves_to_the_whole_file(self, repo):
        got = gate.content_after_edit(
            "analyst_tracker/store.py",
            _edit("    return _ins(conn, name, status)",
                  "    return _ins(conn, name, status, retry=0)"))
        assert got is not None
        assert got.startswith("import sqlite3\n"), got
        assert "retry=0" in got
        assert "return _ins(conn, name, status)\n" not in got

    def test_replace_all_is_honoured(self, repo):
        io.open(repo / "analyst_tracker" / "store.py", "w",
                encoding="utf-8", newline="\n").write("a = 1\na = 1\n")
        got = gate.content_after_edit("analyst_tracker/store.py",
                                      _edit("a = 1", "b = 2", replace_all=True))
        assert got == "b = 2\nb = 2\n"

    def test_a_multiedit_applies_in_order(self, repo):
        got = gate.content_after_edit("analyst_tracker/store.py", {
            "file_path": "analyst_tracker/store.py",
            "edits": [{"old_string": "import sqlite3", "new_string": "import json"},
                      {"old_string": "import json", "new_string": "import os"}]})
        assert got is not None and got.startswith("import os\n"), got

    def test_an_anchor_that_does_not_match_is_unresolvable(self, repo):
        """套不上不是 R8 該處理的情況 —— 那次編輯本來就會失敗。

        回傳 None 的語意是「算不出結果」,由呼叫端退回磁碟現況,
        **不得退回片段** —— 退回片段就是把這張票的缺陷原地保留。
        """
        assert gate.content_after_edit(
            "analyst_tracker/store.py", _edit("這一行不存在", "x")) is None

    def test_an_unreadable_file_is_unresolvable(self, repo):
        assert gate.content_after_edit(
            "analyst_tracker/nope.py", {"file_path": "analyst_tracker/nope.py",
                                        "old_string": "a", "new_string": "b"}) is None

    def test_a_crlf_file_resolves_and_keeps_its_line_endings(self, repo):
        """CRLF 檔案:anchor 取自檔案內容(真實 Edit 就是這樣來的)-> 套得上。

        行尾在本輪已經咬過兩次(R3 的 hash 比對、本檔的 fixture)。
        解析器**不得**擅自正規化:它交出去的東西要跟檔案真正會有的內容一致,
        否則規則判的是一份不存在的檔案。
        """
        p = repo / "analyst_tracker" / "store.py"
        io.open(p, "wb").write(b"import sqlite3\r\n\r\ndef f():\r\n    return 1\r\n")
        got = gate.content_after_edit(
            "analyst_tracker/store.py", _edit("    return 1\r\n", "    return 2\r\n"))
        assert got is not None, "CRLF 檔案套不上 anchor"
        assert got == "import sqlite3\r\n\r\ndef f():\r\n    return 2\r\n", repr(got)

    def test_a_cp950_file_still_resolves(self, repo):
        """編碼假設是 F-042/F-064 那條線:utf-8 解不動就整支檔案看不見。

        zh-TW Windows 上 cp950 是預設編碼,這不是假想情況。
        """
        p = repo / "analyst_tracker" / "store.py"
        io.open(p, "wb").write(
            u"# 註解\nimport research\n".encode("cp950"))
        got = gate.content_after_edit(
            "analyst_tracker/store.py", _edit("import research", "import sqlite3"))
        assert got is not None, "cp950 檔案解不動 -> 整支檔案對 R8 隱形"
        assert "import research" not in got


# ─────────────────────────────────────────────────────────────────────────────
# 二、R8 的判定對象(票 07 的驗收清單)
# ─────────────────────────────────────────────────────────────────────────────

def _hook_verdict(repo, ti):
    """走與前哨相同的路徑:tool_input -> 內容解析 -> check()。"""
    path = ti["file_path"]
    return gate.check(path, gate.content_after_edit(path, ti))


class TestR8JudgesTheResultNotTheFragment:

    def test_an_indented_fragment_without_imports_is_not_an_r8_violation(self, repo):
        """**本票的紅燈**:縮排片段 -> IndentationError -> 現況報成 import 違規。"""
        msg = _hook_verdict(repo, _edit(
            "    return _ins(conn, name, status)",
            "    return _ins(conn, name, status, retry=0)"))
        assert not (msg and "R8" in msg), \
            "片段沒 import 任何東西卻被 R8 擋:%r" % msg

    def test_a_fragment_ending_at_a_def_anchor_is_not_an_r8_violation(self, repo):
        """片段結尾是 anchor `def foo():`(缺 body)-> SyntaxError -> 現況被擋。"""
        msg = _hook_verdict(repo, _edit(
            "def put_backup_status(conn, name, status):",
            "def put_backup_status(conn, name, status, *, retry=0):"))
        assert not (msg and "R8" in msg), \
            "anchor 片段沒 import 任何東西卻被 R8 擋:%r" % msg

    def test_a_result_that_imports_research_is_blocked(self, repo):
        """正控:片段本身乾淨,但**結果** import 了 research -> 擋。"""
        io.open(repo / "analyst_tracker" / "store.py", "w",
                encoding="utf-8", newline="\n").write("import research\n\ndef f():\n    return 1\n")
        msg = _hook_verdict(repo, _edit("    return 1", "    return 2"))
        assert msg and "R8" in msg, "結果 import research 卻放行了:%r" % msg

    def test_an_edit_that_removes_the_import_is_allowed(self, repo):
        """反控:磁碟上有 import research,這次編輯把它拿掉 -> 結果乾淨 -> 放行。

        少了這一條,「一律看磁碟現況」也會讓上面那條正控過 —— 那是另一個
        判定對象錯誤,只是錯的方向相反。
        """
        io.open(repo / "analyst_tracker" / "store.py", "w",
                encoding="utf-8", newline="\n").write("import research\n\ndef f():\n    return 1\n")
        msg = _hook_verdict(repo, _edit("import research\n", "import sqlite3\n"))
        assert not (msg and "R8" in msg), "結果已不含 import research 仍被擋:%r" % msg

    def test_a_broken_result_still_fails_closed(self, repo):
        """fail-closed 沒有被拆掉,只是問對了對象:**結果**解析不了 -> 擋。"""
        msg = _hook_verdict(repo, _edit(
            "def put_backup_status(conn, name, status):",
            "def put_backup_status(conn, name, status:"))
        assert msg and "R8" in msg, "結果是壞掉的 Python 卻放行了:%r" % msg

    def test_a_broken_result_says_so_instead_of_blaming_an_import(self, repo):
        """擋是對的,但**訊息要說對原因**。

        票 07 列的第一項代價就是這個:讀到的是 import 違規、現場是括號沒閉合,
        它讓人去檢查一個根本沒問題的地方。修好判定對象之後,
        「結果解析不了」與「結果 import 了 research」變成兩件可以分開講的事,
        沒有理由再把前者說成後者。
        """
        msg = _hook_verdict(repo, _edit(
            "def put_backup_status(conn, name, status):",
            "def put_backup_status(conn, name, status:"))
        assert "fail-closed" in msg, "語法錯誤被說成 import 違規:%r" % msg
        # 斷言的是「有沒有指控」,不是「有沒有出現 import research 這幾個字」——
        # 「無法判定它有沒有 import research/」是陳述無法判定,那句話該留著。
        assert "不得 import research/" not in msg, "仍在指控 import 違規:%r" % msg
        assert "不是合法 Python" in msg, "沒有說出真正的原因:%r" % msg

    def test_unreadable_content_says_so_instead_of_blaming_an_import(self, repo):
        """讀不到內容 -> 擋,但訊息要說「讀不到」。

        誤導的訊息比沒有訊息貴:讀到的是 import 違規、現場是括號沒閉合,
        會讓人去檢查一個根本沒問題的地方(票 07 的兩個實際代價之一)。
        """
        msg = gate.check("analyst_tracker/gone.py", None)
        assert msg and "R8" in msg, "讀不到內容卻放行:%r" % msg
        assert "fail-closed" in msg, "訊息把讀不到說成 import 違規:%r" % msg


class TestTheOldGuaranteesDoNotRegress:

    def test_a_whole_file_write_importing_research_is_still_blocked(self, repo):
        msg = _hook_verdict(repo, {"file_path": "analyst_tracker/store.py",
                                   "content": "from research import explore\n"})
        assert msg and "R8" in msg, "整檔 Write 的 R8 回歸了:%r" % msg

    def test_research_utils_is_still_not_a_research_import(self, repo):
        """F-051 的邊界不得回歸:`research_utils` 不是 `research`。"""
        msg = _hook_verdict(repo, {"file_path": "analyst_tracker/store.py",
                                   "content": "import research_utils\n"})
        assert not (msg and "R8" in msg), "research_utils 被誤判成 research:%r" % msg

    def test_research_importing_production_is_still_allowed(self, repo, monkeypatch):
        monkeypatch.setattr(gate, "load_stage", lambda: ("research", None))
        (repo / "research").mkdir()
        io.open(repo / "research" / "explore.py", "w",
                encoding="utf-8", newline="\n").write("x = 1\n")
        msg = _hook_verdict(repo, {"file_path": "research/explore.py",
                                   "content": "from analyst_tracker import data\n"})
        assert msg is None, msg


class TestTheSentinelIsActuallyWiredToIt:
    """接線也要測 —— 「只是接線,不測」兩次放過同一條要命的程式碼(F-044)。"""

    def test_mode_hook_resolves_content_instead_of_taking_the_fragment(self):
        assert "content_after_edit" in gate.mode_hook.__code__.co_names, \
            "mode_hook 沒有走內容解析,片段還是直接餵給 check()"


class TestThroughTheRealEntryPoint:
    """**本票的主紅燈**:走 PreToolUse payload 進 mode_hook,量的是使用者實際撞到的東西。

    上面那些單元測試在修好之前多半以 AttributeError 紅 —— 那種紅只證明「函式還沒寫」,
    不證明「現在的行為是錯的」。這一條用今天就存在的進入點,證明缺陷本身是紅的。
    """

    def _run(self, monkeypatch, capsys, ti):
        import json as _json
        import sys as _sys

        class _Stdin(object):
            def __init__(self, raw):
                self.buffer = self
                self._raw = raw

            def read(self):
                return self._raw

        payload = {"tool_name": "Edit", "tool_input": ti,
                   "hook_event_name": "PreToolUse"}
        monkeypatch.setattr(_sys, "stdin",
                            _Stdin(_json.dumps(payload).encode("utf-8")))
        monkeypatch.setattr(gate, "mount_violations_cached", lambda: [])
        monkeypatch.setattr(gate, "authoritative_layer", lambda: (True, ""))
        rc = gate.mode_hook()
        return rc, capsys.readouterr().err

    def test_editing_one_line_inside_a_function_is_not_an_import_violation(
            self, repo, monkeypatch, capsys):
        """六次連撞的那個形狀:函式內部改一行 -> 縮排片段 -> 被報成 import research。"""
        rc, err = self._run(monkeypatch, capsys, _edit(
            "    return _ins(conn, name, status)",
            "    return _ins(conn, name, status, retry=0)"))
        assert "R8" not in err, \
            "片段裡沒有 import 任何東西,卻被 R8 擋下:\n%s" % err
        assert rc != 2 or "R8" not in err

    def test_the_result_is_what_gets_blocked(self, repo, monkeypatch, capsys):
        """反面:結果真的 import 了 research,前哨仍要擋(rc=2)。"""
        io.open(repo / "analyst_tracker" / "store.py", "w",
                encoding="utf-8", newline="\n").write("import research\n\ndef f():\n    return 1\n")
        rc, err = self._run(monkeypatch, capsys, _edit("    return 1", "    return 2"))
        assert rc == 2 and "R8" in err, (rc, err)
