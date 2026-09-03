# -*- coding: utf-8 -*-
"""唯讀 MCP server —— 把 repo 的證據接到 Claude Desktop(framework-updates/101)。

三支工具,**就這三支**(裁 A / 紅燈①):

    status_all()      子程序跑 status.py,**原樣**回傳它的 stdout
    ticket(n)         票檔原文
    friction(code)    friction log 的那一則原文

## 為什麼 status 走子程序而不是 import(裁 3)

`status.render()` 會 `exec_module` 目標 repo 的 `gate.py`,而 `render_all` 會開 git。
**走子程序不是效能取捨,是把那兩件事關到另一個行程去** ——
這個行程從頭到尾沒有 import 過 `gate`,也沒有自己開過 git。

**這是「隔開」不是「證明」。** 票 101 第六節原本要證明「gate 模組層無副作用」,
量到 0 筆之後仍然只能寫「量到 0 筆」(黑名單非枚舉、只看名字不看 binding)。
裁 3 換了個做法:**不去證明它,把它移出去。**
移出去之後那個問題與本行程無關,而**無關比證明強** ——
證明會過期(gate.py 明天可以加一行),隔離不會。

## 為什麼沒有寫入類工具(架構級,永不做)

這支跑在 Claude Desktop 底下,而 **Desktop 那一側沒有六站閘門** ——
`gate.py` 的前哨掛在 Claude Code 的 PreToolUse。一支能寫檔的 MCP server
等於在閘門旁邊開一個它看不到的入口。

⚠ 目前守著這條的是**紅燈①(工具清單恰三支)**,它擋得住「多長出第四支」,
**擋不住「把 ticket 改成能寫」**。那一面沒有機制,明寫在票面第八節。

## root 從哪裡來(裁 6)

**只認 `--root`,repo 內不存路徑。** 三個絕對路徑住在
`claude_desktop_config.json` 的 `args` 裡,而那個檔不在版控裡。
`set_roots()` 是**刻意露出來的接縫** —— 沒有它,裁 6 就沒辦法被測。
"""

import argparse
import io
import json
import os
import re
import subprocess
import sys

from mcp.server.fastmcp import FastMCP

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from friction_heading import HEADING  # noqa: E402

# `status.py` 的絕對路徑。**argv[1] 釘的就是這個常數**(紅燈②)——
# 寫成常數而不是就地組字串,測試才驗得出它指到真的那一支。
STATUS_PY = os.path.join(_HERE, "status.py")

UNRECORDED = u"未記錄"

# 票住哪裡。**這是 `gate.py:TICKET_DIRS` 的第二份,刻意的,不是還沒清掉的重複。**
#
# 理由與 `friction_heading.py` 那一則(票 42)**方向相反但同一條**:
# 那一則說「權威層不要 import portable/」,本行說「MCP 不要 import gate」——
# 裁 3 的整個重點就是這個行程裡不能有 gate。
# 為了不讓兩份漂開(`F-058` 家族),`tests/test_mcp_server.py` 有一條對帳測試
# 釘住 `mcp_server.TICKET_DIRS == gate.TICKET_DIRS`。**測試那一側 import gate 是可以的。**
TICKET_DIRS = (".scratch/%s/issues", "docs/tickets/%s")

# 裁 4:先驗格式。**四位數上限**是因為票號是本 repo 的東西,不是使用者輸入的自由文字。
_TICKET_RE = re.compile(r"^\d{1,4}$")
# `friction_heading.HEADING` 的號碼部分同式(裁 5)。
_FRICTION_RE = re.compile(r"^[A-Za-z]+-\d+$")

# friction 段落的結束條件:**下一個 `^##`**(裁 5)。
_NEXT_HEADING = re.compile(r"^##")

_ROOTS = []


def set_roots(roots):
    """設定要看的 root。第一個視為上游(與 `status.render_all` 同一條約定)。"""
    global _ROOTS
    _ROOTS = [os.path.abspath(r) for r in roots]


def _upstream():
    """第一個 root。沒有設就回 None —— **fail-closed,不猜 cwd**。

    猜 cwd 在 Desktop 底下是災難:那個行程的工作目錄不是使用者以為的地方,
    而猜錯之後回傳的東西**看起來仍然像一份正常的答案**。
    """
    return _ROOTS[0] if _ROOTS else None


def _read(path):
    """讀一個檔的全文。讀不到回 None。**utf-8-sig** —— 工作樹可能帶 BOM。"""
    try:
        with io.open(path, encoding="utf-8-sig") as f:
            return f.read()
    except Exception:
        return None


def _feature_of(root):
    """`.dev/pipeline.json` 的 `feature`。讀不到 / 沒有回 None。

    **直接讀 json,不經過 gate** —— 這裡不需要任何判定邏輯,只要一個欄位,
    而 import gate 正是裁 3 要避開的事。
    """
    raw = _read(os.path.join(root, ".dev", "pipeline.json"))
    if raw is None:
        return None
    try:
        return json.loads(raw).get("feature")
    except Exception:
        return None


def _extra_root_args():
    """第二個以後的 root,展平成 `--root <path> --root <path> …`。"""
    out = []
    for r in _ROOTS[1:]:
        out.append("--root")
        out.append(r)
    return out


mcp = FastMCP("monkeyleash")


@mcp.tool()
def status_all() -> str:
    """把 status.py 的輸出原樣端出來。

    **一個位元組都不加工**(裁 B):不重排、不摘要、不補說明。
    `status.py` 的每一行都自帶 `(source: …)`,那是它的判準 3;
    這裡動一個字,來源欄就開始說謊而沒有東西會叫。
    """
    if not _ROOTS:
        return u"%s(沒有設定 root —— 檢查 claude_desktop_config.json 的 args)" % UNRECORDED

    # **argv 的前四格寫成字面**(裁 3 / 紅燈②):測試從 AST 讀得到
    # `[sys.executable, STATUS_PY, "--root", …]` 這個前綴。
    # 寫成 `argv = [...]` 再 `argv.extend(...)` 的話,`subprocess.run(argv)`
    # 的引數在 AST 上只是一個名字,**前綴就釘不住了** ——
    # 而釘不住的時候測試仍然會綠(它只看得到一個 Name),那正是要避免的。
    proc = subprocess.run(
        [sys.executable, STATUS_PY, "--root", _ROOTS[0], *_extra_root_args()],
        capture_output=True)

    out = proc.stdout.decode("utf-8", "replace")
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", "replace")
        # **退出碼與 stderr 都端出來,不吞。** 一個只回「失敗了」的訊息
        # 會讓讀的人以為 repo 有問題,而實際可能只是路徑打錯。
        return u"%s(status 退出碼 %d)\n--- stderr ---\n%s\n--- stdout ---\n%s" % (
            UNRECORDED, proc.returncode, err, out)
    return out


def _ticket_path(root, feature, num):
    """`<num>-` 開頭的票檔。**邊界是那個 `-`**(裁 4 前半),沒有就回 None。"""
    prefix = str(num) + u"-"
    for tmpl in TICKET_DIRS:
        rel = tmpl % feature
        d = os.path.join(root, *rel.split("/"))
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if name.startswith(prefix) and name.endswith(".md"):
                return os.path.join(d, name)
    return None


@mcp.tool()
def ticket(n: str) -> str:
    """票號 `n` 的票檔原文。找不到回「未記錄」,**不回鄰居的檔**。

    裁 4 後半:**`n` 與 `n.zfill(2)` 兩式都試**,兩式都要邊界命中。
    本 repo 的票號補零到兩位(`01`–`09`),所以呼叫者打 `1` 要能拿到票 01;
    而**補零這件事是這一層的知識** —— `status._find_ticket_file` 只答
    「這個字串有沒有邊界命中」,下游 repo 不見得補零。

    ⚠ **格式先驗,驗完才碰檔案系統。** 一個先讀了再判的實作也會回錯字串,
    而它已經把路徑餵給檔案系統了 —— 從回傳值上看不出這件事。
    """
    if not _TICKET_RE.match(n or u""):
        return u"%s(票號格式不合:%r —— 要一到四位數字)" % (UNRECORDED, n)

    root = _upstream()
    if root is None:
        return u"%s(沒有設定 root)" % UNRECORDED

    feature = _feature_of(root)
    if not feature:
        return u"%s(讀不到 .dev/pipeline.json 的 feature)" % UNRECORDED

    for form in (n, n.zfill(2)):
        path = _ticket_path(root, feature, form)
        if path is not None:
            body = _read(path)
            if body is not None:
                return body
    return u"%s(無此票:%s —— 試過 %s 與 %s 兩式)" % (
        UNRECORDED, n, n, n.zfill(2))


@mcp.tool()
def friction(code: str) -> str:
    """friction log 裡 `code` 那一則的原文(該標題到下一個 `^##` 之間)。

    裁 5:發號判準用 `friction_heading.HEADING`,**不另寫第二份、也不碰 gate 那份**。
    `## 併記於 F-118(…)` 是**提到**不是發號,那正是 `friction_heading.py` 存在的理由。
    """
    if not _FRICTION_RE.match(code or u""):
        return u"%s(friction 號格式不合:%r —— 要像 F-123)" % (UNRECORDED, code)

    root = _upstream()
    if root is None:
        return u"%s(沒有設定 root)" % UNRECORDED

    path = os.path.join(root, "docs", "agents", "friction-log.md")
    text = _read(path)
    if text is None:
        return u"%s(讀不到 docs/agents/friction-log.md)" % UNRECORDED

    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        m = HEADING.match(line)
        if m and m.group(1) == code:
            start = i
            break
    if start is None:
        return u"%s(friction log 裡沒有 %s)" % (UNRECORDED, code)

    end = len(lines)
    for j in range(start + 1, len(lines)):
        if _NEXT_HEADING.match(lines[j]):
            end = j
            break
    return u"\n".join(lines[start:end])


def main(argv=None):
    # F-062:非 ASCII 走裸 print 在 cp950 主控台會炸,而炸掉的樣子像工具壞了。
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    p = argparse.ArgumentParser(description=u"唯讀 MCP server(票 101)")
    # **只認 `--root`**(裁 6)。路徑從 claude_desktop_config.json 的 args 進來,
    # repo 內一個字都不存 —— 那個入口不存在,就沒有東西可以洩漏。
    p.add_argument("--root", action="append", default=None,
                   help=u"要看的 repo 根,可重複;第一個視為上游")
    args = p.parse_args(argv)

    if not args.root:
        sys.stderr.write(u"沒有給 --root(檢查 claude_desktop_config.json 的 args)\n")
        return 2
    set_roots(args.root)
    mcp.run(transport="stdio")
    return 0


if __name__ == "__main__":
    sys.exit(main())
