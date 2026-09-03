# -*- coding: utf-8 -*-
"""`.claude/portable/mcp_server.py` —— 唯讀 MCP v0(framework-updates/101)。

**本檔是票 101 的第一筆紅燈。** 寫下它的時候 `mcp_server.py` 還不存在,
所以整份**收集錯誤**(`ModuleNotFoundError`)—— 那就是紅燈本身。
先例:`tests/test_status.py` 的開頭(framework-updates/99)、
framework-updates/98 的 `8c2d555`。

## 受測介面(本檔釘住的形狀)

    mcp_server.mcp                     FastMCP 實例
    mcp_server.set_roots(list_of_str)  設定要看的 root(平常由 argparse 灌)
    mcp_server.status_all() -> str     子程序跑 status.py,**原樣**回傳 stdout
    mcp_server.ticket(n) -> str        票檔原文,或「未記錄(…)」
    mcp_server.friction(code) -> str   friction 段落原文,或「未記錄(…)」

`set_roots` 是**刻意露出來的接縫**,理由與 `status.load_gate` 同一條:
root 從 `claude_desktop_config.json` 的 args 進來(裁 6,repo 內不存路徑),
而測試不能靠一個不在版控裡的檔案。**沒有這個接縫,裁 6 就沒辦法被測。**

## 五條紅燈各守什麼

    ① 工具清單恰三支      —— 守裁 A 的範圍;多長出第四支要紅
    ② AST 無寫入 + 一處子程序 —— 守裁 3 與第六節第一層
    ③ 輸入先驗格式,不讀檔  —— 守裁 4 / 裁 F
    ④ stdout 逐位元組相同  —— 守裁 B(原樣回傳)
    ⑤ 票號邊界            —— 在 `tests/test_status.py`,因為修的是那支

## ⚠ ② 這一條證明的是什麼,先寫清楚

判準是**九個名字加一組 open mode**,不是「所有寫入方式」。
`shutil.copy` 這一族由名字表涵蓋,而**別名、getattr、exec 不涵蓋**。
所以這條綠不等於「零寫入」,等於「這些名字沒出現」——
票面第六節逐條列了限制,**不要把這條測試讀成比它強的東西**。
"""

import ast
import io
import os
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PORTABLE = ROOT / ".claude" / "portable"
SERVER_PY = PORTABLE / "mcp_server.py"
STATUS_PY = PORTABLE / "status.py"

sys.path.insert(0, str(PORTABLE))

import mcp_server  # noqa: E402


EXPECTED_TOOLS = {u"status_all", u"ticket", u"friction"}


# ─────────────────────────────────────────────────────────────────────────────
# 共用:造一個最小 repo(形狀抄 tests/test_status.py 的 _make_root)
# ─────────────────────────────────────────────────────────────────────────────

REAL_GATE = ROOT / ".claude" / "hooks" / "gate.py"
REAL_STAGES = ROOT / ".agents" / "pipeline-stages.yaml"


def _make_root(tmp_path, name=u"repo", stage=u"implement", ticket=u"101",
               feature=u"testfeat", ticket_files=None):
    """最小 repo。`ticket_files` 是 {檔名: 內文} —— 直接指定,不由票號推。"""
    import json
    import shutil

    root = tmp_path / name
    (root / ".dev").mkdir(parents=True)
    (root / ".claude" / "hooks").mkdir(parents=True)
    (root / ".agents").mkdir(parents=True)

    with io.open(str(root / ".dev" / "pipeline.json"), "w", encoding="utf-8") as f:
        json.dump({"current_stage": stage, "feature": feature,
                   "ticket_id": ticket, "updated": "2026-09-03"}, f)
    with io.open(str(root / ".claude" / "settings.json"), "w", encoding="utf-8") as f:
        json.dump({"hooks": {"PreToolUse": [{"matcher": "Write|Edit|Bash", "hooks": [
            {"type": "command",
             "command": 'python "$CLAUDE_PROJECT_DIR/.claude/hooks/gate.py"'}]}]}}, f)

    shutil.copy2(str(REAL_GATE), str(root / ".claude" / "hooks" / "gate.py"))
    shutil.copy2(str(REAL_STAGES), str(root / ".agents" / "pipeline-stages.yaml"))

    if ticket_files:
        d = root / "docs" / "tickets" / feature
        d.mkdir(parents=True)
        for fname, body in ticket_files.items():
            with io.open(str(d / fname), "w", encoding="utf-8") as f:
                f.write(body)

    return str(root)


# ─────────────────────────────────────────────────────────────────────────────
# ① 工具清單恰三支
# ─────────────────────────────────────────────────────────────────────────────

class TestToolInventory:
    """裁 A:範圍鎖死在三支唯讀工具。

    **用相等,不用包含。** 包含擋不住「多長出第四支」,
    而多出來的那支正是要擋的東西 —— 尤其是一支能寫的。
    """

    def test_exactly_three_tools(self):
        names = {t.name for t in mcp_server.mcp._tool_manager.list_tools()}
        assert names == EXPECTED_TOOLS, (
            u"工具清單必須恰好是 %s,實際 %s" % (sorted(EXPECTED_TOOLS), sorted(names)))

    def test_a_missing_tool_would_be_caught(self):
        """負控:少一支也要紅。

        這一條不是重複 —— 上面那條用相等,理論上少一支也會紅,
        **而「理論上」不是證據**。這裡直接示範少一支時的比較結果為假,
        免得有人把 `==` 改成 `<=` 而上面那條仍然綠。
        """
        names = {t.name for t in mcp_server.mcp._tool_manager.list_tools()}
        assert (names - {u"friction"}) != EXPECTED_TOOLS


# ─────────────────────────────────────────────────────────────────────────────
# ② AST:全檔無寫入呼叫;子程序只有一處且 argv 前綴寫死
# ─────────────────────────────────────────────────────────────────────────────

_WRITE_NAMES = frozenset([
    u"makedirs", u"mkdir", u"remove", u"unlink", u"rename", u"replace",
    u"write_text", u"write_bytes", u"copy", u"copy2", u"copyfile",
    u"copytree", u"rmtree", u"system", u"Popen",
])

_WRITE_MODE_CHARS = frozenset(u"wax+")


def _server_tree():
    return ast.parse(io.open(str(SERVER_PY), encoding="utf-8-sig").read(),
                     filename=str(SERVER_PY))


def _calls(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            yield node, (getattr(f, "id", None) or getattr(f, "attr", None))


class TestNoWriteCalls:

    def test_no_write_named_calls_anywhere_in_the_file(self):
        """**全檔**,不只模組層 —— server 的寫入會發生在工具函式裡。"""
        hits = [(n.lineno, nm) for n, nm in _calls(_server_tree())
                if nm in _WRITE_NAMES]
        assert hits == [], u"出現寫入類呼叫:%r" % (hits,)

    def test_every_open_is_read_mode(self):
        """`open` 不在名字表裡,因為讀檔要用它 —— 改看 mode 引數。

        判準:**沒有 mode 引數 = 讀**;有的話裡面不得含 `w` / `a` / `x` / `+`。
        mode 不是字面常數(變數、f-string)一律**擋** —— fail-closed:
        算不出來就當它可能是寫。
        """
        bad = []
        for node, nm in _calls(_server_tree()):
            if nm != u"open":
                continue
            mode = None
            if len(node.args) >= 2:
                mode = node.args[1]
            for kw in node.keywords:
                if kw.arg == "mode":
                    mode = kw.value
            if mode is None:
                continue                      # 無 mode = 讀,合格
            if not isinstance(mode, ast.Constant) or not isinstance(mode.value, str):
                bad.append((node.lineno, u"<mode 非字面常數,fail-closed>"))
                continue
            if set(mode.value) & _WRITE_MODE_CHARS:
                bad.append((node.lineno, mode.value))
        assert bad == [], u"open 用了寫入 mode:%r" % (bad,)


class TestSubprocessIsPinned:
    """裁 3:argv 前綴寫死,不 import `render_all`。

    **釘前綴而不只是「有沒有 subprocess」的理由**:`status.py` 的 `_git()`
    已經示範過 ——「這次傳的是唯讀指令」與「這支只跑唯讀指令」是兩句話。
    釘前綴把後者變成構造。
    """

    def _subprocess_calls(self):
        out = []
        for node, nm in _calls(_server_tree()):
            if nm in (u"run", u"check_output", u"call", u"Popen"):
                out.append(node)
        return out

    def test_exactly_one_subprocess_call(self):
        calls = self._subprocess_calls()
        assert len(calls) == 1, (
            u"子程序呼叫必須恰好一處,實際 %d 處(行:%r)"
            % (len(calls), [c.lineno for c in calls]))

    def test_argv_prefix_is_pinned(self):
        """argv[:3] 必須是 `[sys.executable, <status.py>, "--root"]`。

        第 0 格斷言是 `sys.executable` 這個**屬性存取**;
        第 1 格斷言是一個名字(模組層常數,由 `__file__` 推出來);
        第 2 格斷言是字面 `"--root"`。
        """
        call = self._subprocess_calls()[0]
        assert call.args, u"子程序呼叫沒有位置引數"
        argv = call.args[0]
        assert isinstance(argv, ast.List), u"argv 必須是 list 字面,才釘得住前綴"
        assert len(argv.elts) >= 3, u"argv 字面至少要有三格"

        a0, a1, a2 = argv.elts[0], argv.elts[1], argv.elts[2]
        assert isinstance(a0, ast.Attribute) and a0.attr == "executable", (
            u"argv[0] 必須是 sys.executable,實際 %s" % ast.dump(a0)[:80])
        assert isinstance(a1, ast.Name), (
            u"argv[1] 必須是指向 status.py 的模組層常數,實際 %s" % ast.dump(a1)[:80])
        assert isinstance(a2, ast.Constant) and a2.value == u"--root", (
            u"argv[2] 必須是字面 '--root',實際 %s" % ast.dump(a2)[:80])

    def test_status_path_constant_points_at_the_real_file(self):
        """argv[1] 那個常數要真的指到 `status.py`,不是指到別的東西。

        上一條只驗**形狀**(是個名字)。形狀對而指錯地方的話,
        argv 前綴仍然「釘住了」,而釘住的是錯的東西。
        """
        call = self._subprocess_calls()[0]
        const_name = call.args[0].elts[1].id
        val = getattr(mcp_server, const_name)
        assert os.path.abspath(str(val)) == os.path.abspath(str(STATUS_PY))


# ─────────────────────────────────────────────────────────────────────────────
# ③ 輸入先驗格式:不合法回錯,且**一個檔都不讀**
# ─────────────────────────────────────────────────────────────────────────────

class TestBadInputNeverReadsAFile:
    """裁 4 / 裁 F。

    **「回錯」不夠,要「沒讀檔」。** 一個先讀了再判的實作也會回錯字串,
    而它已經把路徑餵給檔案系統了 —— 從回傳值上**看不出**這件事,
    所以判準做在 `io.open` 的呼叫次數上,不做在回傳值上。
    """

    @pytest.fixture
    def no_open(self, monkeypatch):
        calls = []
        real = io.open

        def boom(*a, **kw):
            calls.append(a[0] if a else None)
            return real(*a, **kw)

        monkeypatch.setattr(io, "open", boom)
        return calls

    @pytest.mark.parametrize("bad", [u"abc", u"10;rm", u"", u"12345", u"-1", u"1.0"])
    def test_bad_ticket_returns_error_and_opens_nothing(self, bad, no_open, tmp_path):
        mcp_server.set_roots([_make_root(tmp_path)])
        out = mcp_server.ticket(bad)
        assert u"未記錄" in out, u"不合法輸入 %r 應回未記錄,實際 %r" % (bad, out[:120])
        assert no_open == [], u"不合法輸入 %r 仍開了檔:%r" % (bad, no_open)

    @pytest.mark.parametrize("bad", [u"F-1; x", u"F1", u"-3", u"F-", u"; rm -rf /"])
    def test_bad_friction_returns_error_and_opens_nothing(self, bad, no_open, tmp_path):
        mcp_server.set_roots([_make_root(tmp_path)])
        out = mcp_server.friction(bad)
        assert u"未記錄" in out, u"不合法輸入 %r 應回未記錄,實際 %r" % (bad, out[:120])
        assert no_open == [], u"不合法輸入 %r 仍開了檔:%r" % (bad, no_open)


# ─────────────────────────────────────────────────────────────────────────────
# ④ status_all 與直跑 status.py 逐位元組相同
# ─────────────────────────────────────────────────────────────────────────────

class TestStatusAllIsVerbatim:
    """裁 B:原樣回傳。

    **比 bytes,不比 str,也不比 strip() 之後。**
    `strip()` 一下就把「結尾那個 `\\n`」放過去了,而那正是加工。
    """

    def test_byte_for_byte(self, tmp_path):
        root = _make_root(tmp_path)
        mcp_server.set_roots([root])

        direct = subprocess.run(
            [sys.executable, str(STATUS_PY), "--root", root],
            capture_output=True)
        assert direct.returncode == 0, direct.stderr.decode("utf-8", "replace")

        got = mcp_server.status_all()
        assert got.encode("utf-8") == direct.stdout.replace(b"\r\n", b"\n"), (
            u"status_all 的輸出與直跑 status.py 不同")

    def test_unrecorded_tokens_survive(self, tmp_path):
        """「未記錄」這種字不得被 server 改寫。

        這一條不是重複 ④:逐位元組相同的兩份**可以同時都是錯的**
        (server 加工了,而測試比的是加工後 vs 加工後)。
        這裡直接對**內容**斷言,參照物換成 `status.py` 的判準 4。
        """
        root = _make_root(tmp_path)
        mcp_server.set_roots([root])
        out = mcp_server.status_all()
        assert u"未記錄" in out
        assert u"(source:" in out


# ─────────────────────────────────────────────────────────────────────────────
# ⑤ 票號:兩式都試(裁 4 後半)
# ─────────────────────────────────────────────────────────────────────────────

class TestTicketTriesBothForms:
    """裁 4 後半:`n` 與 `n.zfill(2)` **皆須邊界命中**。

    底層 `_find_ticket_file` 只答「有沒有邊界命中」(見 `tests/test_status.py`),
    補零是**呼叫者對本 repo 命名慣例的知識** —— 這一層才知道。
    """

    def test_padded_form_is_found(self, tmp_path):
        root = _make_root(tmp_path, ticket_files={
            u"01-first.md": u"# 票 01\n\n內文甲\n",
            u"10-tenth.md": u"# 票 10\n\n內文乙\n",
        })
        mcp_server.set_roots([root])
        out = mcp_server.ticket(u"1")
        assert u"內文甲" in out, u"ticket('1') 應命中 01-first.md,實際 %r" % out[:120]
        assert u"內文乙" not in out, u"ticket('1') 誤命中 10-tenth.md —— 這正是那九筆"

    def test_unpadded_form_is_found(self, tmp_path):
        root = _make_root(tmp_path, ticket_files={u"10-tenth.md": u"# 票 10\n\n內文乙\n"})
        mcp_server.set_roots([root])
        assert u"內文乙" in mcp_server.ticket(u"10")

    def test_no_such_ticket_is_unrecorded_not_a_neighbour(self, tmp_path):
        root = _make_root(tmp_path, ticket_files={u"10-tenth.md": u"# 票 10\n\n內文乙\n"})
        mcp_server.set_roots([root])
        out = mcp_server.ticket(u"1")
        assert u"未記錄" in out
        assert u"內文乙" not in out, u"無此票時回了鄰居的內文 —— 比回不出來糟"

    def test_only_the_first_root_is_searched(self, tmp_path):
        """裁 3 / 裁 6:第一個 root 視為上游,票只在上游找。

        負控的方向是「**不要**在下游找」—— 下游有同號票的話,
        回傳哪一份會變成一個看不出來的擲骰子。
        """
        up = _make_root(tmp_path, name=u"up",
                        ticket_files={u"07-up.md": u"# 票 07\n\n上游內文\n"})
        down = _make_root(tmp_path, name=u"down",
                          ticket_files={u"07-down.md": u"# 票 07\n\n下游內文\n"})
        mcp_server.set_roots([up, down])
        out = mcp_server.ticket(u"7")
        assert u"上游內文" in out
        assert u"下游內文" not in out


# ─────────────────────────────────────────────────────────────────────────────
# friction:裁 5 —— 用 friction_heading.HEADING,切到下一個 ^##
# ─────────────────────────────────────────────────────────────────────────────

_FRICTION_FIXTURE = u"""# Friction log

## F-100 第一則

甲的內文。

## 併記於 F-100(這一行是提到,不是發號)

不該被當成一則。

## F-101 第二則

乙的內文。

## F-102 第三則

丙的內文。
"""


class TestFrictionUsesTheSharedCriterion:

    def _root_with_log(self, tmp_path):
        root = _make_root(tmp_path)
        d = pathlib.Path(root) / "docs" / "agents"
        d.mkdir(parents=True)
        with io.open(str(d / "friction-log.md"), "w", encoding="utf-8") as f:
            f.write(_FRICTION_FIXTURE)
        return root

    def test_returns_the_section_up_to_the_next_heading(self, tmp_path):
        mcp_server.set_roots([self._root_with_log(tmp_path)])
        out = mcp_server.friction(u"F-101")
        assert u"乙的內文" in out
        assert u"甲的內文" not in out
        assert u"丙的內文" not in out, u"切過頭了 —— 應停在下一個 ^##"

    def test_a_mention_is_not_a_number(self, tmp_path):
        """`## 併記於 F-100(…)` 是**提到**,不是發號 —— 不得被當成一則。

        這正是 `friction_heading.py` 存在的理由(見它的 docstring)。
        """
        mcp_server.set_roots([self._root_with_log(tmp_path)])
        out = mcp_server.friction(u"F-100")
        assert u"甲的內文" in out
        assert u"不該被當成一則" not in out

    def test_missing_code_is_unrecorded(self, tmp_path):
        mcp_server.set_roots([self._root_with_log(tmp_path)])
        assert u"未記錄" in mcp_server.friction(u"F-999")


# ─────────────────────────────────────────────────────────────────────────────
# 負控(架構):server 不 import gate
# ─────────────────────────────────────────────────────────────────────────────

class TestServerDoesNotImportGate:
    """裁 3:`gate` 的模組層副作用留在子程序裡。

    **在乾淨的子直譯器裡驗,不在本行程裡驗** —— 本行程跑過別的測試,
    `sys.modules` 裡早就有 gate 模組了(`conftest` 的 `_isolate_live_gate_state`
    自己就說「**每一個**已載入的 gate 模組」)。
    在髒的行程裡斷言「沒有 gate」會**因為別人**而紅,
    那種紅燈指的方向是錯的,比不測還糟。
    """

    def test_clean_interpreter_has_no_gate_module(self):
        probe = (
            "import sys; sys.path.insert(0, %r);"
            "import mcp_server;"
            "names=[n for n in sys.modules if n=='gate' or n.startswith('gate_for_')];"
            "print(repr(names))" % str(PORTABLE)
        )
        r = subprocess.run([sys.executable, "-c", probe], capture_output=True)
        assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
        assert r.stdout.decode("utf-8").strip() == "[]", (
            u"import mcp_server 之後出現 gate 模組:%s"
            % r.stdout.decode("utf-8").strip())

    def test_source_has_no_gate_import(self):
        """靜態面也守一次 —— 上一條驗執行期,這一條驗**意圖**。

        兩者都要:延遲 import(函式體裡的 `import gate`)在乾淨探針裡不會出現,
        因為那條路徑沒被走到。
        """
        tree = _server_tree()
        bad = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    if a.name == "gate" or a.name.startswith("gate."):
                        bad.append((node.lineno, a.name))
            elif isinstance(node, ast.ImportFrom):
                if node.module and (node.module == "gate"
                                    or node.module.startswith("gate.")):
                    bad.append((node.lineno, node.module))
        assert bad == [], u"原始碼裡 import 了 gate:%r" % (bad,)
