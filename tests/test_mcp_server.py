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

    ① 工具清單恰四支      —— 守範圍;多長出第五支要紅(票 105 前為三支)
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
import json
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


EXPECTED_TOOLS = {u"status_all", u"ticket", u"friction", u"latest_report"}


def _drop_generated(blob):
    """把 `generated:` 那一行拿掉,其餘一個位元組都不動。

    **切在 `\\n` 上而不是 `splitlines()`** —— `splitlines()` 會把 `\\r` 吃掉,
    而那正是這條測試要守的東西之一(換行不得被正規化)。
    """
    keep = [ln for ln in blob.split(b"\n") if not ln.startswith(b"generated:")]
    return b"\n".join(keep)


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
# ① 工具清單恰四支
# ─────────────────────────────────────────────────────────────────────────────

class TestToolInventory:
    """裁 A:範圍鎖死在唯讀工具。**票 105 從三支擴到四支**(加 `latest_report`)。

    **用相等,不用包含。** 包含擋不住「多長出下一支」,
    而多出來的那支正是要擋的東西 —— 尤其是一支能寫的。

    ⚠ **票 105 擴充時改的是 `EXPECTED_TOOLS` 這個常數,不是把 `==` 放寬成 `<=`。**
    放寬的話這條就再也擋不住任何新增,而下面那條負控正是為了防那個放寬。
    """

    def test_exactly_four_tools(self):
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
        """**只算 `subprocess.<動詞>`,不是所有叫 `run` 的東西。**

        ⚠ 這一條原本寫成「名字是 run / check_output / call / Popen 就算」,
        而 `mcp.run(transport="stdio")` **也叫 run** —— 那條判準會把
        「啟動 server」數成第二個子程序,於是一個正確的實作永遠過不了。
        判準的對象錯了,不是防線弱。修法是綁**受詞**(`subprocess`),
        不是把 `run` 從表裡拿掉(拿掉的話 `subprocess.run` 也不算了)。
        """
        out = []
        for node in ast.walk(_server_tree()):
            if not isinstance(node, ast.Call):
                continue
            f = node.func
            if not isinstance(f, ast.Attribute):
                continue
            if not isinstance(f.value, ast.Name) or f.value.id != "subprocess":
                continue
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

    def test_stdin_and_timeout_are_pinned(self):
        """**kwargs 也要釘,不只 argv**(2026-09-03 驗收失敗)。

        ## 為什麼這一條原本不存在,而它的缺席是致命的

        紅燈②本來只釘 `argv` 前綴。而現場死掉的原因**不在 argv 裡** ——
        是缺一個 `stdin=subprocess.DEVNULL`:在 MCP stdio server 底下,
        沒有重導向 stdin 的子程序會連帶繼承 server 與客戶端之間那對管線,
        於是 `subprocess.run` **等不到結束**。

        實測(scratchpad 最小 FastMCP server,從 server 行程內部計時):
          子程序只是 `python -c "print('hi')"`,stdin 繼承 -> 卡到拆線
          客戶端逾時 20s -> 子程序記到 20.02s;逾時 40s -> 40.03s
          **是跟著拆線才回來的,不是慢** —— 沒有逾時就永遠不回來
          同一支 server 加 `stdin=DEVNULL` -> 1.03s

        ## `timeout` 是第二條,不是同一條

        缺 `stdin` 是這一次的成因;**缺 `timeout` 是它變成「永遠等」的原因**。
        修了 stdin 之後,下一個未知的阻塞仍然沒有上限。
        兩件事分開釘,因為它們各自失效。
        """
        call = self._subprocess_calls()[0]
        kw = {k.arg: k.value for k in call.keywords}

        assert "stdin" in kw, u"subprocess.run 必須明寫 stdin —— 這是死鎖的成因"
        v = kw["stdin"]
        assert (isinstance(v, ast.Attribute) and v.attr == "DEVNULL"
                and isinstance(v.value, ast.Name) and v.value.id == "subprocess"), (
            u"stdin 必須是 subprocess.DEVNULL,實際 %s" % ast.dump(v)[:100])

        assert "timeout" in kw, u"subprocess.run 必須明寫 timeout —— 否則阻塞沒有上限"
        t = kw["timeout"]
        assert isinstance(t, ast.Constant) and isinstance(t.value, int), (
            u"timeout 必須是整數字面(算得出來的上限),實際 %s" % ast.dump(t)[:100])


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
        # ⚠ `_make_root` 自己會 `io.open(..., "w")` 造那個 tmp repo,而 fixture
        # 在測試本體之前就裝好了 —— 不清的話 `no_open` 一開始就不是空的,
        # 而那個紅會**指向錯的方向**(看起來像 server 讀了檔)。
        del no_open[:]
        out = mcp_server.ticket(bad)
        assert u"未記錄" in out, u"不合法輸入 %r 應回未記錄,實際 %r" % (bad, out[:120])
        assert no_open == [], u"不合法輸入 %r 仍開了檔:%r" % (bad, no_open)

    @pytest.mark.parametrize("bad", [u"F-1; x", u"F1", u"-3", u"F-", u"; rm -rf /"])
    def test_bad_friction_returns_error_and_opens_nothing(self, bad, no_open, tmp_path):
        mcp_server.set_roots([_make_root(tmp_path)])
        del no_open[:]
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
        # ⚠ 比的是**未經正規化**的原始 bytes(換行不動)。
        # 這一條原本寫成 `direct.stdout.replace(b"\r\n", b"\n")`,
        # 也就是**預設 server 會把換行正規化** —— 而裁 B 說「一個位元組都不加工」。
        # 那樣寫的話,一個做了正規化(= 加工)的實作會**通過**這條測試,
        # 而測試的名字仍然叫「逐位元組相同」。判準與它宣稱守的東西不一致。
        #
        # ⚠ **`generated` 那一行除外**,而且只有那一行 —— 它來自時鐘,
        # 兩次跑本來就不同(`status.now_iso()`)。這與票 101 第九節的
        # 實機驗收用同一個排除法,不是為了讓測試綠而放寬的。
        # **逐行排除,不是整段 normalize**:排除一整類差異會把真正的加工一起放過去。
        assert _drop_generated(got.encode("utf-8")) == _drop_generated(direct.stdout), (
            u"status_all 的輸出與直跑 status.py 不是逐位元組相同(generated 行除外)")

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

    def test_ticket_dirs_agree_with_gate(self):
        """對帳:`mcp_server.TICKET_DIRS` 與 `gate.TICKET_DIRS` 必須相同。

        裁 3 要求 server 不 import gate,代價是**票目錄清單多一份副本**。
        **同缺陷的兩份實作必然漂開**(`F-058` 家族),所以要有東西釘住它。

        釘的方式與 `friction_heading` 那一對同型:**測試這一側 import gate 是可以的**
        —— 負控守的是 `mcp_server` 這個模組,不是這個測試檔。
        """
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "gate_for_ticketdirs", str(ROOT / ".claude" / "hooks" / "gate.py"))
        gate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gate)
        assert tuple(mcp_server.TICKET_DIRS) == tuple(gate.TICKET_DIRS), (
            u"兩份票目錄清單漂開了:mcp_server=%r gate=%r"
            % (mcp_server.TICKET_DIRS, gate.TICKET_DIRS))

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


# ─────────────────────────────────────────────────────────────────────────────
# ⑥ 真的起一支 stdio server,走協定叫一次(2026-09-03 驗收失敗補上)
# ─────────────────────────────────────────────────────────────────────────────
#
# 🔴 **這一條為什麼非有不可。**
#
# 2026-09-03 的驗收失敗時,全套 1232 支測試**全綠**,而 Claude Desktop 那一側
# `status_all` 完全叫不動(兩次 timed out)。兩件事不衝突 ——
# **上面每一條測試都是在 pytest 的行程裡直接呼叫那個函式**,
# 而 pytest 的 stdin 不是 MCP 管線,所以那個死鎖在測試環境裡**不會發生**。
#
# 紅燈④(逐位元組相同)是最貼近的一條,而它也是 in-process 的 ——
# 它證的是「這個函式回的字串對」,不是「這支 server 在協定上活著」。
#
# **判準:測試造的行程環境,證不出真實行程環境裡的事。**
# 這與「材料要從別的地方來」是同一句話,只是換到行程模型這一面:
# 材料(行程環境)若由測試自己造,它只能證明自洽。
# 唯一的出路是**真的走一次協定** —— 這一條就是那個出路。

_LIVE_TIMEOUT = 30          # 客戶端逾時
_LIVE_BUDGET = 15           # 斷言的上限:15s 內要回


def _live_call(tmp_path, root, tool, kwargs, errlog_path):
    """起一個真的 stdio server,叫一次 `tool`,回 (耗時, 文字, isError)。

    **在子行程裡跑客戶端**,不在 pytest 的事件迴圈裡 —— pytest 沒有
    `anyio`/`asyncio` 的 session fixture,而在測試裡自己 `asyncio.run()`
    會與別的 plugin 打架;更要緊的是:**客戶端與被測 server 同處一個
    行程會讓「行程環境」這個變因回到測試手上**,而那正是本節要避開的東西。
    """
    driver = tmp_path / "live_driver.py"
    with io.open(str(driver), "w", encoding="utf-8") as f:
        f.write(_LIVE_DRIVER_SRC)

    argv = [sys.executable, str(driver), str(SERVER_PY), root,
            tool, json.dumps(kwargs), str(errlog_path), str(_LIVE_TIMEOUT)]
    proc = subprocess.run(argv, capture_output=True,
                          stdin=subprocess.DEVNULL, timeout=_LIVE_TIMEOUT + 30)
    raw = proc.stdout.decode("utf-8", "replace")
    try:
        payload = json.loads(raw.split(u"---RESULT---", 1)[1])
    except Exception:
        raise AssertionError(
            u"驅動器沒有吐出結果。rc=%d\n--- stdout ---\n%s\n--- stderr ---\n%s"
            % (proc.returncode, raw[-2000:],
               proc.stderr.decode("utf-8", "replace")[-2000:]))
    return payload


_LIVE_DRIVER_SRC = u'''# -*- coding: utf-8 -*-
"""測試用的一次性 MCP 客戶端。argv:
   <server.py> <root> <tool> <kwargs-json> <errlog> <timeout>
結果以 ---RESULT--- 後接一行 JSON 印到 stdout。
"""
import asyncio, io, json, sys, time

server_py, root, tool, kwargs_json, errlog, timeout = sys.argv[1:7]
kwargs = json.loads(kwargs_json)
timeout = float(timeout)

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def go():
    params = StdioServerParameters(
        command=sys.executable,
        args=[server_py, "--root", root],
        cwd="C:\\\\" if sys.platform == "win32" else "/",
    )
    out = {"ok": False, "elapsed": None, "text": "", "isError": None, "why": ""}
    t0 = time.time()
    try:
        with io.open(errlog, "w", encoding="utf-8") as errf:
            async with stdio_client(params, errlog=errf) as (r, w):
                async with ClientSession(r, w) as session:
                    await session.initialize()
                    names = sorted(t.name for t in (await session.list_tools()).tools)
                    out["tools"] = names
                    t1 = time.time()
                    res = await asyncio.wait_for(
                        session.call_tool(tool, kwargs), timeout=timeout)
                    out["elapsed"] = time.time() - t1
                    out["text"] = "".join(getattr(c, "text", "") for c in res.content)
                    out["isError"] = bool(res.isError)
                    out["ok"] = True
    except asyncio.TimeoutError:
        out["why"] = "TimeoutError after %.1fs" % (time.time() - t0)
    except Exception as e:
        out["why"] = "%s: %s" % (type(e).__name__, str(e)[:300])
    return out


try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
result = asyncio.run(go())
sys.stdout.write("---RESULT---" + json.dumps(result, ensure_ascii=False))
'''


class TestLiveStdioServer:
    """走真的 stdio 協定叫一次。**這是唯一照得出行程層死鎖的那一條。**"""

    def _errlog(self, tmp_path, tag):
        return tmp_path / ("server_%s.stderr.log" % tag)

    def _dump(self, path):
        if not os.path.exists(str(path)):
            return u"(stderr 檔不存在)"
        body = io.open(str(path), encoding="utf-8", errors="replace").read()
        return body if body.strip() else u"(空 —— 0 bytes)"

    def test_status_all_returns_over_the_wire(self, tmp_path):
        """`status_all` 要在 15s 內經由協定回來,而且內容是真的。

        ⚠ **這一條紅的樣子是「逾時」,不是「值不對」** ——
        而逾時在報告裡讀起來像「機器慢」。它不是:同一份 `status.py`
        直跑是 1s 等級(紅燈④已經證過),差別只在**誰是父行程**。
        """
        root = _make_root(tmp_path)
        errlog = self._errlog(tmp_path, "statusall")
        r = _live_call(tmp_path, root, u"status_all", {}, errlog)

        assert r["ok"], (
            u"status_all 沒有經由協定回來:%s\n--- server stderr ---\n%s"
            % (r["why"], self._dump(errlog)))
        assert set(r.get("tools") or []) == EXPECTED_TOOLS, r.get("tools")
        assert r["elapsed"] < _LIVE_BUDGET, (
            u"status_all 走協定花了 %.2fs,超過 %ds 上限 —— 同一份 status.py "
            u"直跑是 1s 等級,差別只在誰是父行程\n--- server stderr ---\n%s"
            % (r["elapsed"], _LIVE_BUDGET, self._dump(errlog)))
        assert r["isError"] is False, r["text"][:400]
        assert r["text"].startswith(u"=== Repository ==="), (
            u"回來的不是 status 的輸出,前 200 字:%r" % r["text"][:200])

    def test_ticket_over_the_wire_is_the_negative_control(self, tmp_path):
        """**負控** —— `ticket` 走同一條線 1s 內回。

        它證的是**這條線本身是通的**:沒有這一支的話,
        上面那條逾時會有兩種讀法(「server 壞了」與「這支工具壞了」),
        而那兩種的處置完全不同。`ticket` 不開子程序,所以它一直是綠的 ——
        **綠的那一支正是把成因夾出來的那一支。**
        """
        root = _make_root(tmp_path, ticket_files={u"01-first.md": u"# 票 01\n\n內文甲\n"})
        errlog = self._errlog(tmp_path, "ticket")
        r = _live_call(tmp_path, root, u"ticket", {"n": "1"}, errlog)

        assert r["ok"], (
            u"ticket 沒有經由協定回來:%s\n--- server stderr ---\n%s"
            % (r["why"], self._dump(errlog)))
        assert r["elapsed"] < 1.0, u"ticket 走協定花了 %.2fs" % r["elapsed"]
        assert u"內文甲" in r["text"], r["text"][:200]

    def test_friction_over_the_wire_is_the_negative_control(self, tmp_path):
        """**負控之二** —— `friction` 同上,也不開子程序。"""
        root = _make_root(tmp_path)
        d = pathlib.Path(root) / "docs" / "agents"
        d.mkdir(parents=True)
        with io.open(str(d / "friction-log.md"), "w", encoding="utf-8") as f:
            f.write(_FRICTION_FIXTURE)
        errlog = self._errlog(tmp_path, "friction")
        r = _live_call(tmp_path, root, u"friction", {"code": "F-101"}, errlog)

        assert r["ok"], (
            u"friction 沒有經由協定回來:%s\n--- server stderr ---\n%s"
            % (r["why"], self._dump(errlog)))
        assert r["elapsed"] < 1.0, u"friction 走協定花了 %.2fs" % r["elapsed"]
        assert u"乙的內文" in r["text"], r["text"][:200]


# ─────────────────────────────────────────────────────────────────────────────
# ⑦ 票 105:latest_report —— 回報回程
#
# **本組是真的 TDD**,不是票 102–104 那種特徵化測試:
# `latest_report` 今天不存在,所以下面每一條在刀二都必須**真的紅**,
# 而紅的樣子已經先寫在票面第四節。
# ─────────────────────────────────────────────────────────────────────────────

_REPORT_ONE = (
    u"## 第一段【給裁決者】\n"
    u"甲段內文。\n"
    u"\n"
    u"## 第二段【給裁決助手】\n"
    u"乙段內文。\n"
)

_REPORT_THREE_LEVEL = (
    u"### 第一段【給裁決者】\n"
    u"甲段內文。\n"
    u"\n"
    u"### 第二段【給裁決助手】\n"
    u"乙段內文。\n"
)

_REPORT_NO_HEADINGS = u"這份回報沒有段落標題,只有一段散文。\n"


def _with_reports(root, files):
    """在 root 底下造 `.dev/reports/` 並寫入 {檔名: 內文}。

    **不建目錄**就代表「目錄不存在」那一種空 —— 三種空要分得出來,
    所以造法也要分得出來(`files=None` vs `files={}`)。
    """
    d = os.path.join(root, ".dev", "reports")
    if files is None:
        return d
    os.makedirs(d)
    for name, body in files.items():
        with io.open(os.path.join(d, name), "w", encoding="utf-8") as f:
            f.write(body)
    return d


class TestLatestReportPart:
    """紅燈 #2:`part` 三值各回對段落。"""

    def _root(self, tmp_path, body=_REPORT_ONE):
        root = _make_root(tmp_path)
        _with_reports(root, {u"2026-09-04T120000Z-ticket-105.md": body})
        mcp_server.set_roots([root])
        return root

    def test_part_1_returns_only_the_first_section(self, tmp_path):
        self._root(tmp_path)
        out = mcp_server.latest_report(u"1")
        assert u"甲段內文" in out, out[:200]
        assert u"乙段內文" not in out, u"part=1 卻夾帶了第二段:%r" % out[:200]

    def test_part_2_returns_only_the_second_section(self, tmp_path):
        self._root(tmp_path)
        out = mcp_server.latest_report(u"2")
        assert u"乙段內文" in out, out[:200]
        assert u"甲段內文" not in out, u"part=2 卻夾帶了第一段:%r" % out[:200]

    def test_part_all_returns_both(self, tmp_path):
        self._root(tmp_path)
        out = mcp_server.latest_report(u"all")
        assert u"甲段內文" in out and u"乙段內文" in out, out[:200]

    def test_the_default_is_part_1(self, tmp_path):
        """**預設值是介面的一部分。**

        裁決寫的是「預設 1」——`latest_report()` 不給參數時要等同 `part="1"`,
        而一個預設成 `all` 的實作在三值測試裡**全部會綠**。
        """
        self._root(tmp_path)
        assert mcp_server.latest_report() == mcp_server.latest_report(u"1")


class TestLatestReportBadPartNeverReadsAFile:
    """紅燈 #3:非法 `part` 先驗格式,**一個檔都不讀**。

    形狀抄 `TestBadInputNeverReadsAFile` —— 判準做在 `io.open` 的呼叫次數上,
    不做在回傳值上:一個先讀了再判的實作也會回錯字串,而**從回傳值上看不出來**。
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

    @pytest.mark.parametrize("bad", [u"3", u"0", u"", u"ALL", u"1;rm", u"first", u"-1"])
    def test_bad_part_returns_error_and_opens_nothing(self, bad, no_open, tmp_path):
        root = _make_root(tmp_path)
        _with_reports(root, {u"2026-09-04T120000Z-ticket-105.md": _REPORT_ONE})
        mcp_server.set_roots([root])
        # 造 tmp repo 的那些 io.open 要清掉,否則紅會指向錯的方向
        del no_open[:]
        out = mcp_server.latest_report(bad)
        assert u"未記錄" in out, u"不合法 part %r 應回未記錄,實際 %r" % (bad, out[:120])
        assert no_open == [], u"不合法 part %r 仍開了檔:%r" % (bad, no_open)


class TestLatestReportThreeKindsOfEmpty:
    """紅燈 #4:三種空**各回不同**的「未記錄(…)」。

    `F-155`:回空字串的話,「沒有目錄」「目錄是空的」「讀不到那個檔」
    在 Desktop 那一側**逐字相同**,而三者的處置完全不同 ——
    去建目錄 / 去問這輪為什麼沒寫 / 去查權限或編碼。
    """

    def test_no_reports_dir(self, tmp_path):
        root = _make_root(tmp_path)
        _with_reports(root, None)          # 刻意不建
        mcp_server.set_roots([root])
        out = mcp_server.latest_report(u"1")
        assert u"未記錄" in out, out[:200]
        assert u"reports" in out, u"沒說出是哪個目錄不存在:%r" % out[:200]

    def test_reports_dir_is_empty(self, tmp_path):
        root = _make_root(tmp_path)
        _with_reports(root, {})            # 建了但空
        mcp_server.set_roots([root])
        out = mcp_server.latest_report(u"1")
        assert u"未記錄" in out, out[:200]

    def test_the_three_empties_say_different_things(self, tmp_path):
        """**核心那一條**:三句話兩兩不同。

        少了它,三個分支各自回「未記錄」也會讓上面兩條綠 ——
        而那正是本組要擋的東西。
        """
        r1 = _make_root(tmp_path, name=u"none")
        _with_reports(r1, None)
        mcp_server.set_roots([r1])
        a = mcp_server.latest_report(u"1")

        r2 = _make_root(tmp_path, name=u"empty")
        _with_reports(r2, {})
        mcp_server.set_roots([r2])
        b = mcp_server.latest_report(u"1")

        r3 = _make_root(tmp_path, name=u"unreadable")
        d = _with_reports(r3, {u"2026-09-04T120000Z-x.md": u"x"})
        os.remove(os.path.join(d, u"2026-09-04T120000Z-x.md"))
        os.mkdir(os.path.join(d, u"2026-09-04T120000Z-x.md"))   # 同名目錄 -> 讀不到
        mcp_server.set_roots([r3])
        c = mcp_server.latest_report(u"1")

        assert a != b and b != c and a != c, (
            u"三種空回了相同的字串,分不出來:\n沒目錄=%r\n空目錄=%r\n讀不到=%r"
            % (a[:80], b[:80], c[:80]))


class TestLatestReportPicksByFilename:
    """紅燈 #5:**字典序**取最新,不看 mtime。

    裁三:mtime 的失敗是無聲的(`git checkout` / clone / 解壓縮會重設它,`F-135`)。
    所以這裡刻意讓**字典序最大的那份 mtime 最舊** ——
    兩個判準給出相反的答案,才分得出實作用的是哪一個。
    """

    def test_picks_the_lexicographically_last_even_when_its_mtime_is_oldest(
            self, tmp_path):
        root = _make_root(tmp_path)
        d = _with_reports(root, {
            u"2026-12-31T235959Z-ticket-105.md":
                u"## 第一段【給裁決者】\n新的那份。\n",
            u"2026-01-01T000000Z-ticket-105.md":
                u"## 第一段【給裁決者】\n舊的那份。\n",
        })
        # 讓字典序最大的那份 **mtime 最舊**
        old = os.path.join(d, u"2026-12-31T235959Z-ticket-105.md")
        new = os.path.join(d, u"2026-01-01T000000Z-ticket-105.md")
        os.utime(old, (1000000, 1000000))
        os.utime(new, (2000000, 2000000))

        mcp_server.set_roots([root])
        out = mcp_server.latest_report(u"1")
        assert u"新的那份" in out, (
            u"挑錯了 —— 用 mtime 會挑到「舊的那份」。實際回傳:%r" % out[:200])


class TestLatestReportTruncates:
    """紅燈 #6:`part="all"` 超過上限要截斷,**且標記帶真數字**。"""

    def test_all_is_capped_and_marked(self, tmp_path):
        body = (u"## 第一段【給裁決者】\n" + u"甲" * 30000 +
                u"\n## 第二段【給裁決助手】\n" + u"乙" * 30000 + u"\n")
        root = _make_root(tmp_path)
        _with_reports(root, {u"2026-09-04T120000Z-ticket-105.md": body})
        mcp_server.set_roots([root])

        out = mcp_server.latest_report(u"all")
        assert u"[截斷:" in out, u"超長內容沒有截斷標記:%r" % out[-200:]
        assert str(len(body)) in out, (
            u"截斷標記沒有寫出原長度 %d:%r" % (len(body), out[-200:]))
        assert u"40000" in out, u"截斷標記沒有寫出回傳長度:%r" % out[-200:]

    def test_a_short_report_is_not_marked(self, tmp_path):
        """負控:沒超過上限就不得出現截斷標記。

        少了它,一個「無條件加標記」的實作會讓上面那條綠 ——
        而那會讓每一份回報都看起來像被截斷過。
        """
        root = _make_root(tmp_path)
        _with_reports(root, {u"2026-09-04T120000Z-ticket-105.md": _REPORT_ONE})
        mcp_server.set_roots([root])
        assert u"[截斷:" not in mcp_server.latest_report(u"all")


class TestLatestReportSplitsBothHeadingLevels:
    """紅燈 #9:`##` 與 `###` **兩級都要吃**。

    裁一:`CLAUDE.md:329/:343` 寫 `###`,而實際產出的回報一直是 `##`。
    一個照 `CLAUDE.md` 寫死 `^### ` 的切分器,**對今天全部的回報一條都切不到**
    —— 而它會回「未切分」,看起來像格式壞了,實際是切分器抄錯了層級。
    """

    @pytest.mark.parametrize("body,tag", [
        (_REPORT_ONE, u"##"),
        (_REPORT_THREE_LEVEL, u"###"),
    ])
    def test_both_levels_split(self, body, tag, tmp_path):
        root = _make_root(tmp_path, name=u"r" + str(len(tag)))
        _with_reports(root, {u"2026-09-04T120000Z-ticket-105.md": body})
        mcp_server.set_roots([root])

        one = mcp_server.latest_report(u"1")
        assert u"甲段內文" in one and u"乙段內文" not in one, (
            u"%s 級標題切不出第一段:%r" % (tag, one[:200]))
        two = mcp_server.latest_report(u"2")
        assert u"乙段內文" in two and u"甲段內文" not in two, (
            u"%s 級標題切不出第二段:%r" % (tag, two[:200]))


class TestLatestReportFallsBackToWhole:
    """紅燈 #10:切不到 → 回**整份** + `[未切分:找不到段落標題]`,**不得回空**。

    回空的話,「這份回報沒有分段」與「這個 repo 沒有回報檔」
    在 Desktop 那一側**逐字相同**(`F-155`)。
    """

    def _out(self, tmp_path, part):
        root = _make_root(tmp_path, name=u"nb" + part)
        _with_reports(root, {u"2026-09-04T120000Z-ticket-105.md": _REPORT_NO_HEADINGS})
        mcp_server.set_roots([root])
        return mcp_server.latest_report(part)

    @pytest.mark.parametrize("part", [u"1", u"2"])
    def test_unsplittable_returns_the_whole_file_with_a_marker(self, part, tmp_path):
        out = self._out(tmp_path, part)
        assert u"[未切分:找不到段落標題]" in out, u"沒有標記:%r" % out[:200]
        assert u"只有一段散文" in out, u"沒有回整份:%r" % out[:200]
        assert out.strip() != u"", u"回了空字串"
