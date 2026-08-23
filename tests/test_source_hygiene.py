# -*- coding: utf-8 -*-
"""原始碼衛生:三條會**離開這個 repo** 的東西,各有一個機器判定。

三條的共同形狀:**壞掉的時候沒有東西會叫**。
`\\<` 那種跳脫序列今天只是 DeprecationWarning、閉區間字面讀起來完全通順、
`reason` 字串在本地看得懂 —— 三者都要有人剛好去看才會被發現,
而它們全都隨 `copy` 桶送到下游。**票 69。**

**枚舉,不比對。** 三條守的面都是封閉且可窮舉的(`.claude/` 底下的 `.py`、
追得到的檔案樹、`tests/` 底下的 `reason=` kwarg)——
封閉集合用 pattern 不是防線弱,是選錯工具:**比對的漏是未知的,枚舉的漏是不存在的。**
"""

import ast
import io
import os
import pathlib
import warnings

ROOT = pathlib.Path(__file__).resolve().parents[1]

# 本檔的 repo 相對路徑。**綁路徑不綁檔名** —— 綁檔名的話豁免的鑰匙就握在
# 要規避的人手上:任何目錄放一個同名檔就免掃。形式照 leak_scan.py 的
# 自我豁免與 gate.py 的 GATE_SELF,那兩處一開始就是路徑。
SELF_REL = "tests/test_source_hygiene.py"


def _rel(p):
    return pathlib.PurePath(p).relative_to(ROOT).as_posix()


# ─────────────────────────────────────────────────────────────────────────────
# H1 —— `.claude/` 底下的 Python 在 -W error 下要能乾淨剖析
# ─────────────────────────────────────────────────────────────────────────────
#
# 由來:`.claude/portable/g1_guard.py` 的 docstring 含 `\<` 而不是 raw string
# (量化 TSI-037,CI run #24 的 DeprecationWarning)。
# Python 3.12 起這一族由 DeprecationWarning 轉 SyntaxWarning,更晚的版本
# 規劃改成 SyntaxError —— **屆時該檔會直接 import 失敗,而它是 G1 的守衛本體。**
#
# **這一條不只守那一支。** 登記寫的是「那個檔加一個 r」,而
# 修好一個偵測器之後要回頭重掃既有資料:問的不是「以後會不會再犯」,
# 是「**現在還有幾支**」。`.claude/` 底下的 `.py` 是封閉集合,所以枚舉。

def _claude_python_files():
    out = []
    for base, dirs, names in os.walk(ROOT / ".claude"):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for n in sorted(names):
            if n.endswith(".py"):
                out.append(pathlib.Path(base) / n)
    return sorted(out)


def test_claude_python_parses_clean_with_warnings_as_errors():
    """`.claude/` 底下每一支 `.py` 都要在警告轉錯誤下剖析乾淨。

    **測的是剖析,不是 import** —— import 會有副作用(讀設定、寫檔),
    而這裡要問的是「未來的 Python 還編不編得動它」,那由 `ast.parse` 回答。
    """
    files = _claude_python_files()
    assert files, "`.claude/` 底下一支 .py 都沒枚舉到 —— 枚舉本身壞了,不是通過"

    bad = []
    for p in files:
        src = io.open(p, encoding="utf-8").read()
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            warnings.simplefilter("error", SyntaxWarning)
            try:
                ast.parse(src, filename=str(p))
            except (SyntaxError, DeprecationWarning, SyntaxWarning) as e:
                bad.append("%s:%s" % (_rel(p), e))

    assert not bad, (
        "下列檔案在警告轉錯誤下剖析不乾淨 —— 未來的 Python 版本會讓它們 "
        "import 失敗,而其中有 G1 的守衛本體:\n  " + "\n  ".join(bad))


# ─────────────────────────────────────────────────────────────────────────────
# H2 —— 活的框架面不得把規則範圍寫成閉區間
# ─────────────────────────────────────────────────────────────────────────────
#
# 寫死一個結尾編號,會讓讀的人認定它後面那一條不存在。而 R8 存在
# (`gate.py` 的 R8 分支:生產程式碼不得 import research/),它在下游擋過人。
# 規則代號的權威來源是 `gate.py` 的 `rule_codes()` —— 它從規則自己的
# 擋下訊息掃出來,加一條規則就自動涵蓋,不必有人記得改一份對照表。
#
# **黑名單,不是白名單**(ADR 0003):列出不掃的,其餘全掃,新增的檔案預設被守。
# 三次 fail-open 缺陷都源自白名單思維。

# 歷史紀錄照 F-036 不改寫,所以它們合法地留著舊字面。
_H2_SKIP_DIRS = (
    ".git", "__pycache__", ".pytest_cache", ".cache", ".venv", "node_modules",
    "docs/tickets",      # 票是工作紀錄,寫下當時的字
    "docs/audits",       # 盤點報告同上
    ".scratch",          # 工作階段暫存
    ".claude/skills",    # 上游工具產生的鏡像
    "skills",
)
_H2_SKIP_FILES = (
    "docs/agents/friction-log.md",    # 摩擦紀錄照 F-036 不改寫
    "docs/agents/friction-local.md",
    SELF_REL,                          # 本檔含樣式本身
)
_H2_TEXT_EXT = (".py", ".md", ".txt", ".yaml", ".yml", ".sh", ".json", ".cfg", ".toml")

# 兩種破折號都要收:en dash 與 ASCII hyphen 在畫面上幾乎分不出來,
# 只收一種等於留一個換個字元就能繞過的洞。
_CLOSED_INTERVAL = ("R1–R7", "R1-R7")


def _live_framework_files():
    out = []
    for base, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs
                   if _rel(pathlib.Path(base) / d) not in _H2_SKIP_DIRS
                   and d not in _H2_SKIP_DIRS]
        for n in sorted(names):
            p = pathlib.Path(base) / n
            if not n.endswith(_H2_TEXT_EXT):
                continue
            if _rel(p) in _H2_SKIP_FILES:
                continue
            out.append(p)
    return sorted(out)


def test_no_closed_rule_range_on_the_live_framework_surface():
    """活的框架面不得出現寫死結尾編號的規則範圍。"""
    files = _live_framework_files()
    assert len(files) > 50, (
        "枚舉到的檔案只有 %d 個 —— 掃描範圍本身壞了,不是通過" % len(files))

    hits = []
    for p in files:
        try:
            src = io.open(p, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        for i, line in enumerate(src.splitlines(), 1):
            if any(lit in line for lit in _CLOSED_INTERVAL):
                hits.append("%s:%d:%s" % (_rel(p), i, line.strip()[:80]))

    assert not hits, (
        "下列位置把規則範圍寫成閉區間,而 R8 存在且在下游擋過人。\n"
        "改法:寫「R 系列」並指向 `gate.py` 的 `rule_codes()`,不寫死數字。\n  "
        + "\n  ".join(hits))


# ─────────────────────────────────────────────────────────────────────────────
# H3 —— `xfail` / `skip` 的 reason 不得出現裸票號
# ─────────────────────────────────────────────────────────────────────────────
#
# 由來:量化 TSI-034 實例 2。`tests/test_g1_guard.py` 標 `copy`,
# 它的 `reason` 字串會出現在**下游的 pytest 輸出**裡,而下游手上沒有那張票 ——
# 讀的人會先在自己的 repo 裡找兩張不相干的票。
#
# **範圍限 `reason=`,不是整個 `tests/`。** 這個 repo 的 `tests/` 底下有
# 一百多行裸票號寫在 docstring 與註解裡,判準對它們一樣成立,而那是一次
# 獨立的掃除。`reason` 先做的理由是**它是唯一會離開這個 repo 的那一種**:
# docstring 的讀者在這個 repo 裡,`reason` 的讀者不在。
#
# 正確寫法帶 feature(同 repo)或 repo + feature(跨 repo):
#   `framework-updates/04`、`monkeyleash framework-updates/04`
# 不寫裸的「票 04」—— 命名空間的邊界是 `.scratch/<feature>/issues/`,不是 repo。

_BARE_TICKET = __import__("re").compile(r"票\s*\d+")


def _reason_strings():
    out = []
    for p in sorted((ROOT / "tests").glob("*.py")):
        if _rel(p) == SELF_REL:
            continue
        tree = ast.parse(io.open(p, encoding="utf-8").read(), filename=str(p))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for kw in node.keywords:
                if kw.arg == "reason" and isinstance(kw.value, ast.Constant) \
                        and isinstance(kw.value.value, str):
                    out.append((_rel(p), kw.value.lineno, kw.value.value))
    return out


def test_xfail_and_skip_reasons_do_not_use_a_bare_ticket_number():
    """`reason` 字串裡的票號要帶 feature 名 —— 它會被沒有那張票的人讀到。"""
    reasons = _reason_strings()
    assert reasons, "`tests/` 底下一個 reason= 都沒枚舉到 —— 枚舉本身壞了,不是通過"

    bad = []
    for rel, lineno, text in reasons:
        for m in _BARE_TICKET.finditer(text):
            bad.append("%s:%d:%s" % (rel, lineno, m.group(0)))

    assert not bad, (
        "下列 `reason` 字串用了裸票號,而該檔會隨 `copy` 桶送到下游,\n"
        "下游的 pytest 輸出會叫人去找一張他沒有的票。\n"
        "改法:帶 feature 名(`framework-updates/04`),跨 repo 時再加 repo 名。\n  "
        + "\n  ".join(bad))
