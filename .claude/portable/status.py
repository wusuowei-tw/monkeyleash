# -*- coding: utf-8 -*-
"""`status` —— 把散在 repo 各處的證據算成一份可貼的現況。**票 99。**

## 它是什麼

一個沒看過這個 repo 的人,無法只靠貼上來的東西正確說出現況:
現況散在 `pipeline.json`、`git`、`.dev/` 三本帳、`settings.json`、票面、friction log。
要問「現在什麼狀況」只能靠人**逐個貼**,而貼的人決定貼什麼 ——
**沒貼的那一格看起來跟沒問題一樣。**

## 九條判準(2026-09-01 三方收斂),與本檔哪裡實現它們

| # | 判準 | 在本檔的樣子 |
|---|---|---|
| 1 | **projection 不存** | 全檔沒有任何寫入。每次呼叫都從現場重算 |
| 2 | **只呼叫 `gate.py`,不重述它** | `load_gate()` + 呼叫;本檔**不含**任何 R1–R9 或站別判準 |
| 3 | **每行帶來源** | `_line()` 是唯一的產行函式,`source` 是必填參數 |
| 4 | **算不出寫「未記錄」** | `UNRECORDED`;缺檔、缺欄、指令失敗一律走它 |
| 5 | **規則不做靜態 PASS** | 不重跑任何規則。印的是帳本內容與從帳本推導 |
| 6 | Enforcement Health 四行各帶來源 | `_enforcement()` |
| 7 | Sync Health 進 `--all` | **Day 3,本檔不做** |
| 8 | `--all` 跨三 repo | **Day 3,本檔不做** |
| 9 | MCP 只設計介面 | 不做 |

## 為什麼 `load_gate` 是一個具名函式而不是 `import gate`

裁 C:`gate.py` 的 `ROOT` 是從 `__file__` 往上三層推的**模組層常數**。
在 A repo 裡 import B repo 的 gate,`ROOT` 會指到 A —— **而那個錯是靜默的**
(規則還在、還被呼叫、永遠回「沒事」)。所以 per-root 各載一份。

它同時是**測試的接縫**:判準 2 說「只呼叫不重述」,而
**「有沒有真的去呼叫」從輸出看不出來** —— 一個自己偷讀 `pipeline.json`
的實作印出的字一模一樣。`tests/test_status.py::TestStageComesFromGate`
靠換掉 `load_gate` 讓輸出跟著變來證明它。**沒有這個接縫,判準 2 就只是一句話。**

## ⚠ 本檔不讀 `~/.claude/`

G1 掛在使用者層,而使用者層**不屬於任何 repo**。去讀它會讓同一份輸出
在不同機器上意義不同,而讀的人分不出來。所以 G1 那一行只說
「這是使用者層的東西,repo 內無設定」,值恆為未證明。

## ⚠ 「未證明」不是「沒裝」

`mounted:` 一律印**未證明**(裁 D)。前哨與 G1 由 harness 起,
**它們的環境不是本行程的環境** —— 本行程看不到 `$CLAUDE_PROJECT_DIR`
不代表 hook 執行時看不到。把「我這裡看不到」印成「它不在」會讓人去修一個沒壞的東西。

真正能證明它們動過的是**帳本**(`authority` 那一行):
一筆 `at_commit=true` 的豁免紀錄,是權威層在某個時點真的跑過的痕跡。
**這就是判準 5 的意思 —— 不宣告通過,只印帳本與推導。**

framework-updates/99。
"""

import argparse
import importlib.util
import io
import json
import os
import subprocess
import sys

UNRECORDED = u"未記錄"
UNPROVEN = u"未證明"

_GATE_CACHE = {}


# ─────────────────────────────────────────────────────────────────────────
# 載入與產行
# ─────────────────────────────────────────────────────────────────────────

def load_gate(root):
    """載入 `<root>/.claude/hooks/gate.py`,回傳模組。**per-root 各一份。**

    模組名帶 root 的雜湊 —— 兩個 root 同名會互相蓋掉,而蓋掉之後
    第二個 root 拿到的是第一個 root 的 `ROOT` 常數,**完全無聲**。
    """
    real = os.path.realpath(root)
    if real in _GATE_CACHE:
        return _GATE_CACHE[real]
    path = os.path.join(real, ".claude", "hooks", "gate.py")
    name = "gate_for_%s" % abs(hash(real))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _GATE_CACHE[real] = mod
    return mod


def _line(field, value, source):
    """唯一的產行函式。**`source` 是必填參數,不是選項** —— 判準 3。

    寫成必填而不是預設值:預設值會讓「忘了給來源」變成一個合法的呼叫,
    而那一行看起來與有來源的行一模一樣。
    """
    return u"%s: %s  (source: %s)" % (field, value, source)


def _head(title):
    return u"=== %s ===" % title


# ─────────────────────────────────────────────────────────────────────────
# 讀取(全部容錯,任何失敗一律 UNRECORDED)
# ─────────────────────────────────────────────────────────────────────────

def _git(root, args):
    """跑一條 git,回傳 stdout(strip 過)或 None。**不丟例外。**"""
    try:
        out = subprocess.run(["git"] + list(args), cwd=root,
                             capture_output=True)
    except Exception:
        return None
    if out.returncode != 0:
        return None
    return out.stdout.decode("utf-8", "replace").strip()


def _read_jsonl(path):
    """逐行讀 jsonl。回傳 list of dict;**檔不存在回 None**。

    **壞掉的行跳過,不讓整份變成「未記錄」** —— 一行壞掉不代表其餘不可讀,
    而把可讀的部分丟掉等於用一個小缺陷換一個大空白(裁 F)。
    """
    if not os.path.exists(path):
        return None
    recs = []
    try:
        with io.open(path, encoding="utf-8-sig") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    rec = json.loads(raw)
                except Exception:
                    continue
                if isinstance(rec, dict):
                    recs.append(rec)
    except Exception:
        return None
    return recs


def _field(rec, key):
    """取一個欄位。缺欄或空值回 `未記錄`(裁 F)。

    欄位清單是從各帳**末行**看出來的,**全檔是否同欄未驗** ——
    舊行少一個欄位時,正確的輸出是「未記錄」,不是 `None` 也不是崩潰。
    """
    if not isinstance(rec, dict):
        return UNRECORDED
    v = rec.get(key)
    if v is None or v == "":
        return UNRECORDED
    return v


def _rel(root, path):
    try:
        return os.path.relpath(path, root).replace("\\", "/")
    except Exception:
        return path


# ─────────────────────────────────────────────────────────────────────────
# 五段
# ─────────────────────────────────────────────────────────────────────────

def _repository(root, gate):
    out = [_head(u"Repository")]
    out.append(_line(u"root", root, u"argv --root / cwd 往上找 .claude/hooks/gate.py"))

    head = _git(root, ["rev-parse", "--short", "HEAD"])
    out.append(_line(u"head", head or UNRECORDED, u"git rev-parse --short HEAD"))

    branch = _git(root, ["rev-parse", "--abbrev-ref", "HEAD"])
    out.append(_line(u"branch", branch or UNRECORDED, u"git rev-parse --abbrev-ref HEAD"))

    porcelain = _git(root, ["status", "--porcelain"])
    if porcelain is None:
        tree = UNRECORDED
    elif porcelain == "":
        tree = u"clean"
    else:
        tree = u"dirty %d" % len(porcelain.splitlines())
    out.append(_line(u"tree", tree, u"git status --porcelain"))

    counts, src = UNRECORDED, u"git rev-list --left-right --count"
    if branch:
        ref = "origin/%s...HEAD" % branch
        raw = _git(root, ["rev-list", "--left-right", "--count", ref])
        src = u"git rev-list --left-right --count %s" % ref
        if raw:
            parts = raw.split()
            if len(parts) == 2:
                counts = u"behind %s / ahead %s" % (parts[0], parts[1])
    out.append(_line(u"ahead/behind", counts, src))

    stage, ticket = gate.load_stage()
    out.append(_line(u"stage", stage, u"gate.load_stage()"))
    out.append(_line(u"ticket_id", ticket if ticket else UNRECORDED, u"gate.load_stage()"))
    out.append(_line(u"feature", gate.load_feature() or UNRECORDED, u"gate.load_feature()"))

    updated = UNRECORDED
    try:
        with io.open(gate.PIPELINE, encoding="utf-8-sig") as f:
            updated = _field(json.load(f), "updated")
    except Exception:
        updated = UNRECORDED
    out.append(_line(u"pipeline updated", updated, _rel(root, gate.PIPELINE)))
    return out


def _enforcement(root, gate):
    out = [_head(u"Enforcement Health")]

    # ── authority:**帳本,不是裁決**(判準 5)────────────────────────
    # 「hook 檔在不在」與「權威層真的跑過」是兩件事。前者在 clone 之後
    # 恆為假(`.git/hooks/` 不進版控),後者留得下痕跡。所以值取帳本。
    recs = _read_jsonl(gate.EXEMPTION_LOG)
    val = UNRECORDED
    if recs:
        at_commit = [r for r in recs if r.get("at_commit") is True]
        if at_commit:
            val = u"%s" % _field(at_commit[-1], "ts")
    out.append(_line(u"authority", val,
                     u"%s 最後一筆 at_commit=true" % _rel(root, gate.EXEMPTION_LOG)))

    hooks_path = _git(root, ["config", "core.hooksPath"])
    if hooks_path:
        probe = os.path.join(root, hooks_path.replace("/", os.sep), "pre-commit")
        cfg = u"core.hooksPath=%s; pre-commit 存在=%s; installed: %s" % (
            hooks_path, u"是" if os.path.exists(probe) else u"否", UNPROVEN)
    else:
        cfg = u"core.hooksPath %s; installed: %s" % (UNRECORDED, UNPROVEN)
    out.append(_line(u"authority config", cfg, u"git config core.hooksPath"))

    # ── outpost:設定解得到什麼,不代表 hook 跑的是它(裁 D)──────────
    settings = os.path.join(root, ".claude", "settings.json")
    cmd = UNRECORDED
    try:
        with io.open(settings, encoding="utf-8-sig") as f:
            doc = json.load(f)
        for grp in doc.get("hooks", {}).get("PreToolUse", []):
            for h in grp.get("hooks", []):
                if h.get("command"):
                    cmd = h["command"]
                    break
    except Exception:
        cmd = UNRECORDED
    out.append(_line(u"outpost",
                     u"%s; config resolves from %s; mounted: %s" % (cmd, root, UNPROVEN),
                     _rel(root, settings)))

    out.append(_line(u"g1",
                     u"使用者層 hook,repo 內無設定; mounted: %s" % UNPROVEN,
                     u"(無 —— 本檔不讀 ~/.claude)"))

    # ── skill mirror:直接呼叫純判定,**不走會寫 .cache 的那一支** ────
    # `mount_violations_cached()` 會寫 `.cache/mount-check.json`(gate.py:2791),
    # 而判準 1 說 projection 不存 —— 一支「看一下現況」的工具不得留下檔案。
    try:
        v = gate.skill_mirror_violations(
            os.path.join(root, ".agents", "skills"),
            [os.path.join(root, ".claude", "skills"), os.path.join(root, "skills")])
        mirror = u"違規 %d 筆" % len(v)
        if v:
            mirror += u":%s" % u" / ".join(str(x).splitlines()[0] for x in v[:3])
    except Exception as e:
        mirror = u"%s(%s)" % (UNRECORDED, e)
    out.append(_line(u"skill mirror", mirror,
                     u"gate.skill_mirror_violations(.agents/skills, [.claude/skills, skills])"))

    shadow_state = getattr(gate, "SHADOW_STATE", "")
    try:
        active = gate.shadow_active()
    except Exception:
        active = UNRECORDED
    out.append(_line(u"shadow",
                     u"active=%s; %s 存在=%s" % (
                         active, _rel(root, shadow_state),
                         u"是" if shadow_state and os.path.exists(shadow_state) else u"否"),
                     u"gate.shadow_active() / %s" % _rel(root, shadow_state)))
    return out


def _evidence(root, gate, ticket):
    out = [_head(u"Evidence")]

    runs = _read_jsonl(gate.RUN_LOG)
    if runs is None:
        val = UNRECORDED
    else:
        mine = [r for r in runs if ticket and r.get("ticket_id") == ticket]
        red = len([r for r in mine if r.get("result") == "red"])
        green = len([r for r in mine if r.get("result") == "green"])
        last = runs[-1] if runs else None
        tail = (u"最後一筆 %s=%s @ %s" % (_field(last, "test_file"),
                                          _field(last, "result"),
                                          _field(last, "time"))
                if last else UNRECORDED)
        val = u"本票 red %d / green %d;%s;全套結果:%s(帳本不記全套)" % (
            red, green, tail, UNRECORDED)
    out.append(_line(u"test-runs", val, _rel(root, gate.RUN_LOG)))

    month = _git(root, ["log", "-1", "--format=%cd", "--date=format:%Y-%m"])
    if not month:
        import datetime
        month = datetime.date.today().strftime("%Y-%m")
    ipath = gate.intercept_path(month)
    irecs = _read_jsonl(ipath)
    if irecs is None:
        ival = u"無當月攔截(檔不存在)"
    else:
        last = irecs[-1] if irecs else None
        ival = u"%d 筆" % len(irecs)
        if last:
            ival += u";最後一筆 %s @ %s" % (_field(last, "rule"), _field(last, "ts"))
    out.append(_line(u"intercepts", ival, _rel(root, ipath)))

    ex = _read_jsonl(gate.EXEMPTION_LOG)
    if ex is None:
        exval = UNRECORDED
    else:
        blocked = len([r for r in ex if r.get("outcome") == "blocked"])
        last = ex[-1] if ex else None
        exval = u"總 %d 筆;outcome=blocked %d 筆;最後一筆 %s" % (
            len(ex), blocked, _field(last, "ts") if last else UNRECORDED)
    out.append(_line(u"exemptions", exval, _rel(root, gate.EXEMPTION_LOG)))

    prov = getattr(gate, "PROVENANCE", "")
    pval = (u"存在" if prov and os.path.exists(prov)
            else u"%s(上游無此檔屬正常)" % UNRECORDED)
    out.append(_line(u"provenance", pval, _rel(root, prov)))
    return out


def _find_ticket_file(root, gate, feature, ticket):
    """票檔在哪。`gate.TICKET_DIRS` 兩個位置都找 —— **不重述那份清單**。"""
    if not feature or not ticket:
        return None
    for tmpl in gate.TICKET_DIRS:
        d = os.path.join(root, (tmpl % feature).replace("/", os.sep))
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if name.startswith(str(ticket)) and name.endswith(".md"):
                return os.path.join(d, name)
    return None


def _status_line_of(path):
    """票面狀態行的**原文**與行號。找不到回 (None, None)。

    `rstrip("\\r\\n")` —— 工作樹在 Windows 上是 CRLF,不去掉的話輸出會多一個
    看不見的字元,而**比對狀態行原文的人看不出那是行尾**。
    """
    try:
        with io.open(path, encoding="utf-8-sig") as f:
            for i, raw in enumerate(f, 1):
                line = raw.rstrip("\r\n")
                if line.startswith(u"**狀態**"):
                    return line, i
    except Exception:
        return None, None
    return None, None


def _ticket(root, gate, feature, ticket):
    out = [_head(u"Ticket")]
    path = _find_ticket_file(root, gate, feature, ticket)
    out.append(_line(u"ticket file", _rel(root, path) if path else UNRECORDED,
                     u"gate.TICKET_DIRS %% %s" % (feature or UNRECORDED)))

    if path:
        line, no = _status_line_of(path)
    else:
        line, no = None, None
    # 裁 B:**只印原文,不分類。** 值域實測 ≥21 種寫法、2 行跨行截斷 ——
    # 在那個值域上做分類器,產出的是一個沒有人驗得了的東西。
    out.append(_line(u"ticket status line", line if line else UNRECORDED,
                     u"%s:%s" % (_rel(root, path), no) if line else UNRECORDED))

    # **兩個位置都算,不是取第一個存在的。**
    # 取第一個的話,`.scratch/<feature>/issues` 存在但空的時候會印
    # 「有 0 / 無 0」—— 而那個輸出與「真的沒有票」長得一模一樣。
    # 實測在本 repo 就是這樣(票在 `docs/tickets/`,而 `.scratch/` 那個空目錄先被選中)。
    have, miss, dirs = 0, 0, []
    if feature:
        for tmpl in gate.TICKET_DIRS:
            cand = os.path.join(root, (tmpl % feature).replace("/", os.sep))
            if os.path.isdir(cand):
                dirs.append(cand)
    for d in dirs:
        for name in sorted(os.listdir(d)):
            if not name.endswith(".md"):
                continue
            ln, _no = _status_line_of(os.path.join(d, name))
            if ln:
                have += 1
            else:
                miss += 1
    cov = (u"有狀態行 %d 檔 / 無 %d 檔(未分類)" % (have, miss)
           if dirs else UNRECORDED)
    out.append(_line(u"status coverage", cov,
                     u" + ".join(_rel(root, d) for d in dirs) if dirs else UNRECORDED))
    return out


def _derived(root, gate, stage, ticket):
    out = [_head(u"Derived")]
    try:
        allowed = gate.stage_allows_src_write(stage)
        val = u"yes" if allowed else u"no"
    except Exception as e:
        val = u"%s(%s)" % (UNRECORDED, e)
    out.append(_line(u"src write allowed in %s" % stage, val,
                     u"gate.stage_allows_src_write() <- .agents/pipeline-stages.yaml"))

    runs = _read_jsonl(gate.RUN_LOG)
    if runs is None or not ticket:
        red = UNRECORDED
    else:
        files = []
        for r in runs:
            if r.get("ticket_id") == ticket and r.get("result") == "red":
                f = r.get("test_file")
                if f and f not in files:
                    files.append(f)
        red = u" / ".join(files) if files else u"(無)"
    out.append(_line(u"tests red under ticket %s" % (ticket or UNRECORDED), red,
                     _rel(root, gate.RUN_LOG)))

    try:
        rules = u" ".join(sorted(gate.rule_codes(), key=lambda c: int(c[1:])))
    except Exception:
        rules = UNRECORDED
    out.append(_line(u"rules defined", rules or UNRECORDED, u"gate.rule_codes()"))
    return out


# ─────────────────────────────────────────────────────────────────────────
# 進入點
# ─────────────────────────────────────────────────────────────────────────

def render(root):
    """算一次現況,回傳多行字串。**不寫任何檔案**(判準 1)。"""
    root = os.path.abspath(root)
    gate = load_gate(root)
    stage, ticket = gate.load_stage()
    feature = gate.load_feature()

    blocks = [
        _repository(root, gate),
        _enforcement(root, gate),
        _evidence(root, gate, ticket),
        _ticket(root, gate, feature, ticket),
        _derived(root, gate, stage, ticket),
    ]
    return u"\n\n".join(u"\n".join(b) for b in blocks) + u"\n"


def find_root(start=None):
    """從 `start` 往上找有 `.claude/hooks/gate.py` 的那個根。找不到回 None。"""
    cur = os.path.abspath(start or os.getcwd())
    while True:
        if os.path.exists(os.path.join(cur, ".claude", "hooks", "gate.py")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent


def main(argv=None):
    # F-062:非 ASCII 走裸 print 在 cp950 主控台會炸,而炸掉的樣子像工具壞了。
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    p = argparse.ArgumentParser(description=u"repo 證據的 projection(票 99 v1)")
    p.add_argument("--root", default=None,
                   help=u"要看的 repo 根;預設從 cwd 往上找 .claude/hooks/gate.py")
    # --all 是 Day 3(判準 7、8):跨 repo 要用 subprocess 逐 root 跑同一支,
    # 讓各 repo 的 gate 自己答。在單 repo 這一刀假裝支援它,會產生一個
    # 「看起來跨了 repo 而其實只讀了一個」的輸出。
    args = p.parse_args(argv)

    root = args.root or find_root()
    if not root:
        sys.stderr.write(u"找不到 repo 根(往上都沒有 .claude/hooks/gate.py)\n")
        return 2
    sys.stdout.write(render(root))
    return 0


if __name__ == "__main__":
    sys.exit(main())
