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
import datetime
import importlib.util
import io
import json
import os
import re
import subprocess
import sys

UNRECORDED = u"未記錄"
UNPROVEN = u"未證明"
NO_FUNC = u"未記錄(該 repo 的 gate 無此函式)"
DEAD_SHA = u"未記錄(sha 不在上游歷史,可能為票 84 改寫前)"

# Sync Health 比對的三個檔。**枚舉,不是 pattern** ——
# 這是一個封閉集合(閘門、守衛、守衛的測試),而
# **比對的漏是未知的,枚舉的漏是不存在的**(CLAUDE.md 的常駐檢查項)。
SYNC_WATCHED = (
    ".claude/hooks/gate.py",
    ".claude/portable/g1_guard.py",
    "tests/test_g1_guard.py",
)

_GATE_CACHE = {}


def now_iso():
    """現在。**抽成函式是為了讓它可以被換掉** ——

    否則 `test_generated_line_comes_from_the_clock` 只能斷言「長得像時間」,
    而一個從檔案讀出來的舊時間戳**也長得像時間**。
    """
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


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


def _has(gate, name):
    """那個 root 的 gate 有沒有這個東西。

    **下游裝的是舊版框架,缺函式是常態不是例外狀況。**
    少了這一問,一個 root 的舊 gate 會讓**整份** `--all` 變成一個 traceback ——
    而讀的人看到的是工具壞了,不是「那一格算不出來」。
    """
    return hasattr(gate, name)


def _p(gate, name):
    """那個 root 的 gate 宣告的某條路徑。沒有這個常數回 None。

    **每一個 `gate.X` 都要走這裡。** 直接寫 `gate.EXEMPTION_LOG` 的話,
    一個舊版 gate 會讓**整份** `--all` 變成 traceback ——
    而 `--all` 的重點正是「跨版本的 repo 一起看」,所以舊版是常態不是意外。
    """
    v = getattr(gate, name, None)
    return v if isinstance(v, str) and v else None


def _stage_of(gate):
    if not _has(gate, "load_stage"):
        return NO_FUNC, None
    try:
        s, t = gate.load_stage()
        return s, t
    except Exception:
        return UNRECORDED, None


def _feature_of(gate):
    if not _has(gate, "load_feature"):
        return None
    try:
        return gate.load_feature()
    except Exception:
        return None


def _last_where(recs, pred):
    """最後一筆符合條件的紀錄。沒有回 None。"""
    for rec in reversed(recs or []):
        if pred(rec):
            return rec
    return None


def _latest_intercept_month(gate):
    """磁碟上最新的攔截月檔。回傳 `(月份, 紀錄)`;一個都沒有回 `(None, None)`。

    **檔名形狀從產生端問出來,不是我猜的** —— 拿一個假月份餵
    `gate.intercept_path()`,再從回傳值反推前後綴。
    寫死 `intercepts-YYYY-MM.jsonl` 的話,上游哪天改了輪替命名,
    這裡會安靜地一個檔都找不到,而「找不到」與「沒有攔截」印出來一樣。
    """
    if not _has(gate, "intercept_path"):
        return None, None
    token = u"@@MONTH@@"
    try:
        probe = gate.intercept_path(token)
    except Exception:
        return None, None
    d, base = os.path.dirname(probe), os.path.basename(probe)
    if token not in base:
        return None, None
    pre, post = base.split(token, 1)
    pat = re.compile(u"^%s(\\d{4}-\\d{2})%s$" % (re.escape(pre), re.escape(post)))
    months = []
    try:
        for name in os.listdir(d):
            m = pat.match(name)
            if m:
                months.append(m.group(1))
    except Exception:
        return None, None
    if not months:
        return None, None
    latest = max(months)
    return latest, (_read_jsonl(gate.intercept_path(latest)) or [])


def _latest_per_file(runs, ticket):
    """這張票底下,**每個測試檔的最新一筆**。回傳 `{檔: 紀錄}`。

    帳本是追加式,同一個檔會有很多筆。問「還有什麼是紅的」要看最新一筆,
    **不是「有沒有紅過」** —— 後者會讓每個轉綠的檔永遠留在紅名單裡,
    而一份永遠不會變空的紅名單,讀的人三天後就不看了。

    **沒有票號時回空 dict(fail-closed,票 100)。** 原本寫成
    `if ticket and rec.get(...)`,票號 falsy 時整個過濾被短路,
    於是「這張票底下」變成「全部」—— 而函式名與這段 docstring 都還宣稱前者。
    守在這裡而不是守在呼叫端:呼叫端的守衛救不了下一個呼叫者,
    而他不會知道要補,因為名字已經跟他保證篩過了。
    """
    if not ticket:
        return {}
    out = {}
    for rec in runs or []:
        if rec.get("ticket_id") != ticket:
            continue
        f = rec.get("test_file")
        if f:
            out[f] = rec
    return out


def _waterline_commits(recs):
    """provenance 的**水位線**:每個 `path` 最新一筆憑證的 commit,去重(票 100)。

    回傳 list,保留首次出現的順序(要印給人看,順序穩定才對得回去)。

    **為什麼不是末筆**:憑證是**逐檔發**的(`sync.write_provenance` 一次迴圈寫 N 筆),
    追加不覆蓋,而那四個欄位裡**沒有時間戳也沒有批次號**。
    所以 `recs[-1]` 只代表「最後一個被寫進去的 path」——
    由它推導出來的距離,是一個由單一 path 決定的數字,卻會被讀成整個下游的落後量。

    同 path 後寫的蓋前寫的,與 `_latest_per_file` 同一個「追加式帳本問最新」的形狀。
    """
    latest = {}
    for rec in recs or []:
        p = rec.get("path")
        c = rec.get("upstream_commit")
        if p and c:
            latest[p] = c
    seen, order = set(), []
    for p in latest:
        c = latest[p]
        if c not in seen:
            seen.add(c)
            order.append(c)
    return order


# ─────────────────────────────────────────────────────────────────────────
# 五段
# ─────────────────────────────────────────────────────────────────────────

def _repository(root, gate):
    out = [_head(u"Repository")]
    # 判準 1:**這份輸出是算出來的,不是存下來的。**
    # 印出算的時刻,讀的人才分得出「現況」與「某一次的快照」。
    out.append(_line(u"generated", now_iso(), u"status.now_iso()"))
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

    stage, ticket = _stage_of(gate)
    out.append(_line(u"stage", stage, u"gate.load_stage()"))
    out.append(_line(u"ticket_id", ticket if ticket else UNRECORDED, u"gate.load_stage()"))
    out.append(_line(u"feature", _feature_of(gate) or UNRECORDED, u"gate.load_feature()"))

    pipeline = _p(gate, "PIPELINE")
    updated = UNRECORDED
    if pipeline:
        try:
            with io.open(pipeline, encoding="utf-8-sig") as f:
                updated = _field(json.load(f), "updated")
        except Exception:
            updated = UNRECORDED
    out.append(_line(u"pipeline updated", updated,
                     _rel(root, pipeline) if pipeline else NO_FUNC))
    return out


def _enforcement(root, gate):
    out = [_head(u"Enforcement Health")]

    # ── authority:**帳本,不是裁決**(判準 5)────────────────────────
    # 「hook 檔在不在」與「權威層真的跑過」是兩件事。前者在 clone 之後
    # 恆為假(`.git/hooks/` 不進版控),後者留得下痕跡。所以值取帳本。
    # **標籤是 `authority ledger` 不是 `authority`。**
    # 同一段裡有兩個 authority 來源,而它們回答的不是同一個問題:
    # 帳本答「跑過沒」,`core.hooksPath` 答「設定指向哪」。
    # 共用一個裸標籤會讓讀的人以為那是一個結論 —— 判準 5 不准印結論。
    ex_log = _p(gate, "EXEMPTION_LOG")
    recs = _read_jsonl(ex_log) if ex_log else None
    last_commit = _last_where(recs, lambda r: r.get("at_commit") is True)
    out.append(_line(u"authority ledger",
                     _field(last_commit, "ts") if last_commit else UNRECORDED,
                     u"%s 最後一筆 at_commit=true" % _rel(root, ex_log)
                     if ex_log else NO_FUNC))

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

    # 前哨的**動作**那一半 —— `at_commit=false` 的豁免紀錄是 PreToolUse 跑過的痕跡。
    # 與上一行並存不矛盾:上一行答「設定解得到什麼」,這一行答「它跑過沒」。
    # **設定解得到什麼,不代表 hook 跑的是它**(裁 D),所以兩行都要,各帶各的來源。
    last_agent = _last_where(recs, lambda r: r.get("at_commit") is False)
    out.append(_line(u"outpost ledger",
                     _field(last_agent, "ts") if last_agent else UNRECORDED,
                     u"%s 最後一筆 at_commit=false" % _rel(root, ex_log)
                     if ex_log else NO_FUNC))

    out.append(_line(u"g1",
                     u"使用者層 hook,repo 內無設定; mounted: %s" % UNPROVEN,
                     u"(無 —— 本檔不讀 ~/.claude)"))

    # ── skill mirror:直接呼叫純判定,**不走會寫 .cache 的那一支** ────
    # `mount_violations_cached()` 會寫 `.cache/mount-check.json`(gate.py:2791),
    # 而判準 1 說 projection 不存 —— 一支「看一下現況」的工具不得留下檔案。
    if not _has(gate, "skill_mirror_violations"):
        mirror = NO_FUNC
    else:
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

    shadow_state = _p(gate, "SHADOW_STATE") or ""
    if not _has(gate, "shadow_active"):
        active = NO_FUNC
    else:
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

    run_log = _p(gate, "RUN_LOG")
    runs = _read_jsonl(run_log) if run_log else None
    # **守衛與 `_derived` 同式**(票 100)。兩式並存本身就是缺陷:
    # 同一個問題在同一支檔案裡有兩種答案時,讀的人會以為那是刻意的區別。
    # 無票時**不得**印帶「本票」字樣的數字 —— 那不是缺值,是一個錯的宣稱,
    # 而帶著票面語氣的數字,讀的人會直接引用。
    if runs is None:
        val = UNRECORDED
    elif not ticket:
        val = u"%s(無當前票)" % UNRECORDED
    else:
        latest = _latest_per_file(runs, ticket)
        red = len([r for r in latest.values() if r.get("result") == "red"])
        green = len([r for r in latest.values() if r.get("result") == "green"])
        last = runs[-1] if runs else None
        tail = (u"最後一筆 %s=%s @ %s" % (_field(last, "test_file"),
                                          _field(last, "result"),
                                          _field(last, "time"))
                if last else UNRECORDED)
        val = u"本票(每檔最新一筆)red %d / green %d;%s;全套結果:%s(帳本不記全套)" % (
            red, green, tail, UNRECORDED)
    out.append(_line(u"test-runs", val,
                     _rel(root, run_log) if run_log else NO_FUNC))

    # ── intercepts 印**兩行**,不是一行 ────────────────────────────────
    # 合成一行的話,「這個月還沒有人被擋」與「這個 repo 從來沒有攔截紀錄」
    # 會印出**逐字相同**的一句話 —— 而前者是正常,後者代表前哨可能沒在跑。
    #
    # Day 2 選了「用最後一次 commit 的月份」當唯一的月,而那個選擇讓
    # Day 2 的負控空轉:移走的 8 月檔根本不在讀取路徑上(當月是 9 月)。
    # **不選月份**:當月照當月印,另外印一行「最新存在月」。
    month = datetime.date.today().strftime("%Y-%m")
    if not _has(gate, "intercept_path"):
        out.append(_line(u"intercepts (當月)", NO_FUNC, u"gate.intercept_path()"))
        out.append(_line(u"intercepts (最新存在月)", NO_FUNC, u"gate.intercept_path()"))
        cur_path = None
    else:
        cur_path = gate.intercept_path(month)
        cur = _read_jsonl(cur_path)
        out.append(_line(u"intercepts (當月)",
                         u"%d 筆" % len(cur) if cur is not None else u"檔不存在",
                         _rel(root, cur_path)))

    latest, lrecs = _latest_intercept_month(gate)
    if cur_path is None:
        pass
    elif latest is None:
        lval, lsrc = UNRECORDED, _rel(root, gate.intercept_path(u"YYYY-MM"))
        out.append(_line(u"intercepts (最新存在月)", lval, lsrc))
    else:
        last = lrecs[-1] if lrecs else None
        lval = u"%s %d 筆" % (latest, len(lrecs))
        if last:
            lval += u";末筆 %s@%s" % (_field(last, "rule"), _field(last, "ts"))
        lsrc = _rel(root, gate.intercept_path(latest))
        out.append(_line(u"intercepts (最新存在月)", lval, lsrc))

    ex_log = _p(gate, "EXEMPTION_LOG")
    ex = _read_jsonl(ex_log) if ex_log else None
    if ex is None:
        exval = UNRECORDED
    else:
        blocked = len([r for r in ex if r.get("outcome") == "blocked"])
        last = ex[-1] if ex else None
        exval = u"總 %d 筆;outcome=blocked %d 筆;最後一筆 %s" % (
            len(ex), blocked, _field(last, "ts") if last else UNRECORDED)
    out.append(_line(u"exemptions", exval,
                     _rel(root, ex_log) if ex_log else NO_FUNC))

    prov = _p(gate, "PROVENANCE")
    pval = (u"存在" if prov and os.path.exists(prov)
            else u"%s(上游無此檔屬正常)" % UNRECORDED)
    out.append(_line(u"provenance", pval,
                     _rel(root, prov) if prov else NO_FUNC))
    return out


def _ticket_dirs(root, gate, feature):
    """`gate.TICKET_DIRS` 展開後**存在的**那些目錄。**不重述那份清單。**

    模板不吃參數也不當掉 —— 別的 repo 的 gate 可能把它寫成固定路徑,
    而一個 `TypeError` 會讓整份輸出消失,只為了一格算不出來。
    """
    dirs = []
    for tmpl in (getattr(gate, "TICKET_DIRS", None) or ()):
        try:
            rel = tmpl % feature
        except TypeError:
            rel = tmpl
        d = os.path.join(root, rel.replace("/", os.sep))
        if os.path.isdir(d):
            dirs.append(d)
    return dirs


def _find_ticket_file(root, gate, feature, ticket):
    """票檔在哪。**所有存在的票目錄都找**,不是取第一個。

    **前綴要帶邊界**(framework-updates/101 裁 4):比的是 `<號>-`,不是 `<號>`。
    原本寫 `startswith(str(ticket))`,於是票號 `1` 會命中 `10-*.md` ——
    真實資料上這一族有九筆(`1`→票 10、`2`→票 20、…、`9`→票 90),
    因為本 repo 的票號補零到兩位,`1` 這個字串不對應任何票。
    **回錯一份票比回不出來糟得多**:回不出來的人會再查,
    拿到一份看起來對的票的人不會。

    ⚠ **補零不在這一層。** `_find_ticket_file("1")` 回 `None` 是正確行為 ——
    這裡只答「這個字串有沒有邊界命中」,補零是呼叫者對**本 repo 命名慣例**
    的知識(下游 repo 不見得補零),埋進來會在別的 repo 出錯。

    ⚠ `gate.py` 有語意相同的一份(`:1265`),**本票不修它** ——
    那一份在權威層,改它要有自己的紅燈與驗收。兩份暫時不一致,
    是知情的,不是忘了。見票 101 第八節。
    """
    if not feature or not ticket:
        return None
    prefix = str(ticket) + "-"
    for d in _ticket_dirs(root, gate, feature):
        for name in sorted(os.listdir(d)):
            if name.startswith(prefix) and name.endswith(".md"):
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
    have, miss = 0, 0
    dirs = _ticket_dirs(root, gate, feature) if feature else []
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
    # **缺函式是常態,不是例外狀況** —— 下游裝的是舊版框架。
    # 用 try/except 包住不夠:那會把「這個 root 的 gate 比較舊」與
    # 「函式在但算錯了」混成同一句話,而兩者的處置完全不同。
    if not _has(gate, "stage_allows_src_write"):
        val = NO_FUNC
    else:
        try:
            val = u"yes" if gate.stage_allows_src_write(stage) else u"no"
        except Exception as e:
            val = u"%s(%s)" % (UNRECORDED, e)
    out.append(_line(u"src write allowed in %s" % stage, val,
                     u"gate.stage_allows_src_write() <- .agents/pipeline-stages.yaml"))

    run_log = _p(gate, "RUN_LOG")
    runs = _read_jsonl(run_log) if run_log else None
    if runs is None or not ticket:
        red = green = UNRECORDED
    else:
        latest = _latest_per_file(runs, ticket)
        reds = sorted(f for f, r in latest.items() if r.get("result") == "red")
        greens = sorted(f for f, r in latest.items() if r.get("result") == "green")
        red = u" / ".join(reds) if reds else u"(無)"
        green = u" / ".join(greens) if greens else u"(無)"
    src = (u"%s 每檔最新一筆" % _rel(root, run_log)) if run_log else NO_FUNC
    out.append(_line(u"tests red under ticket %s" % (ticket or UNRECORDED), red, src))
    out.append(_line(u"tests green under ticket %s" % (ticket or UNRECORDED), green, src))

    if not _has(gate, "rule_codes"):
        rules = NO_FUNC
    else:
        try:
            rules = u" ".join(sorted(gate.rule_codes(), key=lambda c: int(c[1:])))
        except Exception:
            rules = UNRECORDED
    out.append(_line(u"rules defined", rules or u"(無)", u"gate.rule_codes()"))
    return out


# ─────────────────────────────────────────────────────────────────────────
# 進入點
# ─────────────────────────────────────────────────────────────────────────

def render(root):
    """算一次現況,回傳多行字串。**不寫任何檔案**(判準 1)。"""
    root = os.path.abspath(root)
    gate = load_gate(root)
    stage, ticket = _stage_of(gate)
    feature = _feature_of(gate)

    blocks = [
        _repository(root, gate),
        _enforcement(root, gate),
        _evidence(root, gate, ticket),
        _ticket(root, gate, feature, ticket),
        _derived(root, gate, stage, ticket),
    ]
    return u"\n\n".join(u"\n".join(b) for b in blocks) + u"\n"


def _sync_health(upstream, downstreams):
    """跨 repo 那一段(判準 7)。**對下游零寫入。**

    只用三種讀:`git`(下游的 `-C` 唯讀查詢)、`io.open`、`sync.file_hash`。
    `sync.py` 裡會寫檔的那些(`_write_bytes` / `write_provenance` /
    `regenerate_canon` / `update(apply=True)`)**一個都不叫**。

    **落後幾刀在上游算**,不在下游算 —— 距離是「上游從那一刀走了幾步」,
    而下游的 repo 裡根本沒有上游的歷史。
    """
    out = [_head(u"Sync Health")]
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import sync                                          # noqa: E402
        file_hash = sync.file_hash
    except Exception as e:
        out.append(_line(u"sync", u"%s(%s)" % (UNRECORDED, e), u"sync.file_hash"))
        return out

    out.append(_line(u"upstream", upstream, u"--root #1"))

    for i, down in enumerate(downstreams, 2):
        tag = u"[%d]" % i
        out.append(_line(u"%s downstream" % tag, down, u"--root #%d" % i))

        prov = os.path.join(down, ".dev", "provenance.jsonl")
        recs = _read_jsonl(prov)
        sha = _field(recs[-1], "upstream_commit") if recs else UNRECORDED
        out.append(_line(u"%s upstream commit" % tag, sha,
                         u"%s 末筆" % prov.replace("\\", "/")))

        # ── waterline:**加一行,不換一行**(票 100)────────────────────
        # 上面那行是一個誠實的觀測(來源欄自己寫著「末筆」),刪掉它換一個新的,
        # 會讓「本來印什麼」在事後查不到。所以水位線另起一行。
        wl = _waterline_commits(recs)
        wl_src = u"%s 每 path 最新一筆 upstream_commit 去重" % prov.replace("\\", "/")
        if not wl:
            wl_val = UNRECORDED
        elif len(wl) == 1:
            wl_val = wl[0]
        else:
            # **不挑一個。** 挑哪一個都是猜,而猜出來的距離
            # 長得跟量出來的一模一樣。N 個都印出來,讓人自己看。
            wl_val = u"%d 個不同 commit(未收齊):%s" % (
                len(wl), u" ".join(c[:12] for c in wl))
        out.append(_line(u"%s waterline" % tag, wl_val, wl_src))

        # **不做換算。** 那個 sha 可能是票 84 改寫身分之前的,
        # 而換算需要 commit-map —— 猜一個距離出來比印「未記錄」糟得多。
        #
        # **距離對 waterline 算,不對末筆算**(票 100):末筆是位置,水位線才是狀態。
        if not wl:
            behind = UNRECORDED
        elif len(wl) > 1:
            behind = u"%s(%d 個不同 commit,未收齊)" % (UNRECORDED, len(wl))
        elif _git(upstream, ["cat-file", "-e", "%s^{commit}" % wl[0]]) is None:
            behind = DEAD_SHA
        else:
            n = _git(upstream, ["rev-list", "--count", "%s..HEAD" % wl[0]])
            behind = u"%s 刀" % n if n is not None else UNRECORDED
        out.append(_line(u"%s behind" % tag, behind,
                         u"git rev-list --count <waterline sha>..HEAD @ 上游"))

        # 下游的 ahead/behind 用**現有** origin ref —— **未 fetch**。
        # 這句標註不是客套:沒 fetch 的話那個 ref 停在上次 fetch 的時點,
        # 而「ahead 0」看起來像同步,實際只是很久沒問過。
        br = _git(down, ["rev-parse", "--abbrev-ref", "HEAD"])
        cnt = _git(down, ["rev-list", "--left-right", "--count",
                          "origin/%s...HEAD" % br]) if br else None
        parts = cnt.split() if cnt else []
        out.append(_line(u"%s downstream origin" % tag,
                         (u"behind %s / ahead %s(未 fetch)" % (parts[0], parts[1])
                          if len(parts) == 2 else u"%s(未 fetch)" % UNRECORDED),
                         u"git rev-list --left-right --count origin/%s...HEAD @ 下游"
                         % (br or u"?")))

        # **兩邊都印,不只印結論。** `same` 這個字唯一能被反駁的方式
        # 就是把兩個雜湊擺出來讓人自己比。
        for rel in SYNC_WATCHED:
            up_h = file_hash(os.path.join(upstream, rel.replace("/", os.sep)))
            dn_h = file_hash(os.path.join(down, rel.replace("/", os.sep)))
            if up_h is None or dn_h is None:
                verdict = UNRECORDED
            else:
                verdict = u"same" if up_h == dn_h else u"drift"
            out.append(_line(u"%s %s" % (tag, rel),
                             u"up=%s down=%s %s" % (
                                 (up_h or UNRECORDED)[:12], (dn_h or UNRECORDED)[:12],
                                 verdict),
                             u"sync.file_hash(行尾正規化後 sha256)"))
    return out


def render_all(roots):
    """多個 root 各算一份,**第一個視為上游**。判準 8。

    每個 root 走**自己的** `gate.py`(裁 C)。這裡不用 subprocess ——
    `load_gate()` 已經 per-root 各載一份模組,而模組名帶 root 的雜湊,
    所以兩個 root 的常數不會互相蓋掉。
    (subprocess 那條路留給「下游的 gate 連 import 都會炸」的情形,
     目前沒有實例,**不預先實作** —— 一個沒有實例的分支測不到,
     而測不到的分支與不存在的分支一樣不可靠。)
    """
    roots = [os.path.abspath(r) for r in roots]
    blocks = []
    for i, r in enumerate(roots, 1):
        blocks.append(u"=== [%d] %s ===" % (i, r))
        blocks.append(render(r))
    if len(roots) >= 2:
        blocks.append(u"\n".join(_sync_health(roots[0], roots[1:])) + u"\n")
    return u"\n".join(blocks)


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

    p = argparse.ArgumentParser(description=u"repo 證據的 projection(票 99)")
    # **`--root` 可重複** —— 給第二個以上就是 `--all`,第一個視為上游。
    # 沒有另設一個 `--all` 旗標:那會多出「給了 --all 卻只有一個 root」
    # 這種要處理的組合,而它沒有意義。**root 的數量自己就是那個開關。**
    p.add_argument("--root", action="append", default=None,
                   help=u"要看的 repo 根,可重複;預設從 cwd 往上找 .claude/hooks/gate.py。"
                        u"給兩個以上時第一個視為上游,並印 Sync Health")
    args = p.parse_args(argv)

    roots = args.root or ([find_root()] if find_root() else [])
    roots = [r for r in roots if r]
    if not roots:
        sys.stderr.write(u"找不到 repo 根(往上都沒有 .claude/hooks/gate.py)\n")
        return 2
    sys.stdout.write(render_all(roots) if len(roots) > 1 else render(roots[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
