# -*- coding: utf-8 -*-
"""權威層端對端驗證 —— 真 hook、真 `git commit`、六格 A 輪。

    python -X utf8 scripts/e2e_authority_layer.py --official . --round A

**這支腳本只產生證據,不下判斷。** 通過與否由摘要表呈現,結案由人裁決。

## 它證明什麼、不證明什麼

**要證的是【接線】** —— `git commit` 真的啟動了正式的 pre-commit hook,
而該 hook 裡的那一格規則真的被評估過、給出預期的判定。

**不證【差異】。** 修復前後的對照(舊碼放行 / 新碼擋下)由**隔離層**的
既有測試提供(票 133 的 #10 / #11 / #13 各有舊碼新碼對照)。
本腳本**不實作 B 輪**(不把歷史版本的 gate.py 取出來跑)——
`--round B` 一律拒絕,理由:未驗收的選配功能不進這一刀。

**非零退出碼 + HEAD 不變,本身不證明是 hook 擋下的。**
所以每一個「預期拒絕」都要同時滿足 §判準 裡的多條,
其中包含 git 自己的 trace2 事件(`GIT_TRACE2_EVENT`)——
那是**不修改受測程式**就能取得的「git 啟動了這個 hook」的紀錄。
追蹤證不到的層級一律標【追蹤未證明】,**不編造訊號**。

## 隔離

- 每一個案例**一個獨立的 clone**。
  `git reset --hard` + `git clean -fd` **不會**清掉 ignored 狀態
  (`.dev/pipeline.json`、`.dev/provenance.jsonl`、`.dev/shadow.json` 全是 ignored),
  所以本腳本**不靠那兩條命令宣稱已重置** —— 直接換一個 clone。
  每個 clone 的可變控制檔由 `prepare_clone()` 逐項建立,清單見該函式。
- clone 完**立刻移除 origin** ⇒ 推不出去是構造保證,不是紀律。
- 正式 repo:**受追蹤檔案、index、HEAD 與設定不變;
  `.dev/reports/` 有預期新增**(本腳本的報告)。
  ⚠ 不宣稱「正式 repo 全程沒有任何寫入」。

## 防誤用檢查(**不是安全證明**)

所有 git 呼叫集中在 `git()`,它檢查**實際 argv 與 env**:
拒絕跳過 hook 的提交選項、拒絕在指令層覆寫 `core.hooksPath`。
**這只擋得住本腳本自己誤用那些開關**;它不證明整支腳本安全,
也不涵蓋 `sh bootstrap.sh` 那一步(那一步由它自己的三道 fail-closed 負責)。
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid

# ── 常數 ─────────────────────────────────────────────────────────────────

MARKER_NAME = ".mk-e2e-marker"
WORK_PREFIX = "mk-e2e-"
LEDGER_REL = ".dev/gate-exemptions.jsonl"
PIPELINE_REL = ".dev/pipeline.json"
PROVENANCE_REL = ".dev/provenance.jsonl"
SHADOW_REL = ".dev/shadow.json"
STAGES_REL = ".agents/pipeline-stages.yaml"
LEGACY_REL = ".agents/legacy-no-redlight.txt"
HOOK_REL = ".githooks/pre-commit"
GATE_REL = ".claude/hooks/gate.py"
LEAK_REL = ".claude/portable/leak_scan.py"

# legacy 清單裡、且確實在 go-live 樹裡的既有檔 —— 合法對照用它,
# 因為它拿得到 legacy 豁免 ⇒ R3 整條不適用,R2 照常適用。
LEGACY_MEMBER = ".claude/hooks/redlight.py"

# #13 的上游物件:用釘住的那個 commit 底下一個確實存在的路徑。
UPSTREAM_OBJECT_PATH = ".claude/portable/manifest.py"

TICKET_DIR = "docs/tickets/framework-updates"
TICKET_NUM = "900"
TICKET_REL = "%s/%s-e2e-probe.md" % (TICKET_DIR, TICKET_NUM)
UNTESTED_PREFIX = "**Untested by decision:**"

# 這些是「不算規則擋下」的樣態 —— 命中即 INCOMPLETE,見 §3.3。
NOT_A_RULE_BLOCK = (
    ("Please tell me who you are", "身分未設"),
    ("unable to auto-detect email", "身分未設"),
    ("gpg failed to sign", "簽章失敗"),
    ("無法載入 yaml 套件", "缺依賴(PyYAML)"),
    ("讀不到流程狀態", "pipeline.json 沒寫好"),
    ("站別定義不可用", "構造把站別定義寫成非法了"),
    ("[六站閘門/影子]", "影子模式開著 —— 整輪作廢"),
    ("[權威層未安裝]", "hooksPath 沒接上"),
)


# ── 防誤用:所有 git 呼叫的單一出入口 ────────────────────────────────────

class Misuse(Exception):
    """本腳本自己把 git 用錯了。**不是受測物的問題。**"""


_SKIP_HOOK_FLAGS = {"--no-verify"}

# ── `git config` 的讀取旗標與寫入旗標 ──────────────────────────────────────
#
# 早一版這裡是「`git config` 的 argv 只要提到 `core.hooksPath` 就擋」,
# **於是它把【讀】也擋掉了** —— 裁決者第 2 次跑 A 輪,第 1 案停在
# `prepare_clone()` 的正面斷言 `git config --get core.hooksPath`
# (那一行的用途正好相反:它是**確認 bootstrap 真的設好了**)。
#
# **修法必須分得出讀與寫,而且不能因此放寬對寫的阻擋。**
# 所以判準是 **fail-closed 的白名單**:
#   提到 core.hooksPath 的 `git config`,**必須帶一個明確的讀取旗標**才放行;
#   帶任何寫入旗標 -> 擋;**一個旗標都沒有 -> 也擋**。
#
# 最後那一條是刻意的:`git config core.hooksPath X` 是寫,
# 而 `git config core.hooksPath`(不給值)是讀 —— **兩者只差一個位置參數**,
# 從 argv 分辨要靠「有沒有多一個 token」,那種判準一改動就會翻向 fail-open。
# 要求明確旗標的代價是**誤擋一種沒人在用的讀法**(本腳本一律用 `--get`),
# 換到的是「新增一種寫法時不會自動獲得放行」。
#
# **兩個集合都用枚舉,不用 pattern** —— `git config` 的旗標是封閉集合,
# 而「比對的漏是未知的,枚舉的漏是不存在的」(CLAUDE.md 常駐檢查項)。
_CONFIG_READ_FLAGS = frozenset((
    "--get", "--get-all", "--get-regexp", "--get-urlmatch",
    "--get-color", "--get-colorbool", "--list", "-l"))
_CONFIG_WRITE_FLAGS = frozenset((
    "--add", "--unset", "--unset-all", "--replace-all",
    "--rename-section", "--remove-section", "--edit", "-e"))


def _assert_safe_git_argv(args):
    """檢查**實際 argv**,不是檢查原始碼字串。

    原始碼字串搜尋會命中檢查程式自己與說明文字 —— 那種自檢是假的。
    這裡問的是「這一次真的要交給 git 的參數是什麼」。

    ⚠ **這是防誤用檢查,不宣稱能證明整支腳本安全。**
       它涵蓋的只有:經過本函式的那些 git 呼叫的 argv 與 env。
    """
    toks = [str(a) for a in args]
    # 子命令 = 第一個不是全域選項的 token
    sub = None
    i = 0
    while i < len(toks):
        t = toks[i]
        if t == "-C" or t == "-c":
            i += 2
            continue
        if t.startswith("-"):
            i += 1
            continue
        sub = t
        break
    for t in toks:
        if t in _SKIP_HOOK_FLAGS:
            raise Misuse("argv 含 %s —— 跳過 hook 的提交不算驗證。" % t)
        low = t.lower().replace(" ", "")
        if "core.hookspath=" in low:
            raise Misuse("argv 想在指令層覆寫 core.hooksPath:%r" % t)
        if low.startswith("--config-env=core.hookspath"):
            raise Misuse("argv 想用 --config-env 覆寫 core.hooksPath:%r" % t)
    # `git commit -n` 的 -n 就是 --no-verify(別的子命令不是)
    if sub == "commit":
        for t in toks:
            if t == "-n":
                raise Misuse("`git commit -n` 等於 --no-verify。")
            if t.startswith("-") and not t.startswith("--") and "n" in t[1:]:
                raise Misuse("`git commit %s` 的短旗標含 n(= --no-verify)。" % t)
    # 本腳本自己永遠不設 hooksPath —— 那一步只由 `sh bootstrap.sh` 做
    if sub == "config" and any("core.hookspath" in t.lower() for t in toks):
        writes = [t for t in toks if t in _CONFIG_WRITE_FLAGS]
        reads = [t for t in toks if t in _CONFIG_READ_FLAGS]
        if writes:
            raise Misuse(
                "本腳本不得自己【寫】core.hooksPath(旗標 %s)—— "
                "那一步走 bootstrap.sh。" % ", ".join(writes))
        if not reads:
            raise Misuse(
                "提到 core.hooksPath 的 `git config` 沒有明確的讀取旗標 —— "
                "從 argv 分不出是讀還是寫,fail-closed 照擋。\n"
                "     讀法請用 %s 之一。" % " / ".join(sorted(_CONFIG_READ_FLAGS)))
        # 有讀取旗標、沒有寫入旗標 -> **放行**(這是正面斷言要用的那條路)


def _assert_safe_env(env):
    """env 不得挾帶 git 設定覆寫。"""
    for k, v in (env or {}).items():
        ku = k.upper()
        if ku.startswith("GIT_CONFIG"):
            raise Misuse("env 含 %s —— 可能覆寫 git 設定。" % k)
        if ku in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
            raise Misuse("env 含 %s —— 會改變 git 的工作對象。" % k)
        if "hookspath" in str(v).lower():
            raise Misuse("env 值提到 hooksPath:%s" % k)


def git(args, cwd=None, extra_env=None, check=False):
    """唯一的 git 出入口。回 `CompletedProcess`(bytes)。"""
    # **把 argv 併進訊息** —— 第 2 次 A 輪的報告只寫了「不得自己設定
    # core.hooksPath」,**沒有寫是哪一個子行程**,於是診斷要回頭讀原始碼才做得出來。
    # 一個說不出自己在講哪一次呼叫的擋下訊息,會讓人去檢查錯的地方(票 13)。
    try:
        _assert_safe_git_argv(args)
    except Misuse as e:
        raise Misuse("%s\n     argv : %r\n     cwd  : %r"
                     % (e, ["git"] + [str(a) for a in args], cwd))
    env = dict(os.environ)
    if extra_env:
        _assert_safe_env(extra_env)
        env.update(extra_env)
    _assert_safe_env({k: v for k, v in env.items() if k.upper().startswith("GIT_")})
    p = subprocess.run(["git"] + [str(a) for a in args], cwd=cwd,
                       capture_output=True, env=env)
    if check and p.returncode != 0:
        raise Misuse("git %s 失敗(rc=%d):%s"
                     % (" ".join(str(a) for a in args), p.returncode,
                        p.stderr.decode("utf-8", "replace")[:800]))
    return p


def gout(args, cwd=None):
    return git(args, cwd=cwd, check=True).stdout.decode("utf-8", "replace").strip()


# ── 小工具 ───────────────────────────────────────────────────────────────

def w(path, text):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def wb(path, raw):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with io.open(path, "wb") as f:
        f.write(raw)


def r(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def sha256_file(path):
    try:
        with io.open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return None


def line_count(path):
    try:
        with io.open(path, encoding="utf-8") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def tail_lines(path, skip):
    try:
        with io.open(path, encoding="utf-8") as f:
            return [ln.rstrip("\n") for ln in f][skip:]
    except Exception:
        return []


def _on_rm_error(func, path, exc):
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWRITE)
        func(path)
    else:
        raise


def path_parts(p):
    return [x for x in os.path.realpath(p).replace("\\", "/").split("/") if x]


def is_ancestor_or_same(a, b):
    """a 是不是 b 的祖先或同一個 —— **比路徑元件,不用 startswith**。

    `startswith` 會把 `C:/proj/agent-gates2` 判成 `C:/proj/agent-gates` 的子路徑。
    """
    pa, pb = path_parts(a), path_parts(b)
    if len(pa) > len(pb):
        return False
    return [x.lower() for x in pa] == [x.lower() for x in pb[:len(pa)]]


# ── 上游錨(#13 的前置)—— 不印完整路徑 ──────────────────────────────────

def read_upstream_root():
    """與 gate.py 同一套解析:恰好一行 `UPSTREAM_ROOT=<絕對路徑>`,否則 None。"""
    p = os.path.join(os.path.expanduser("~"), ".claude", "upstream-roots.txt")
    try:
        lines = io.open(p, encoding="utf-8-sig").read().splitlines()
    except Exception:
        return None
    vals = []
    for line in lines:
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("UPSTREAM_ROOT="):
            v = line.split("=", 1)[1].strip()
            if v:
                vals.append(v)
        else:
            return None
    return vals[0] if len(vals) == 1 else None


def upstream_premises(pinned_sha):
    """#13 的前置條件。**只回布林與遮蔽過的識別,不回完整路徑。**

    「看見一行 `UPSTREAM_ROOT=` 」只是格式初查;**路徑名稱結尾不是 repo 身分證明**。
    所以這裡實際去問 git:那個位置是不是 repo、那個 `commit:path` 讀不讀得到。
    """
    root = read_upstream_root()
    out = {
        "指標檔格式合法(恰好一行)": root is not None,
        "是 git repo": False,
        "commit:path 可讀": False,
        "上游位置識別(遮蔽)": None,
        "_root": root,
    }
    if not root:
        return out
    out["上游位置識別(遮蔽)"] = "sha256:%s" % hashlib.sha256(
        os.path.realpath(root).lower().encode("utf-8")).hexdigest()[:16]
    p = git(["-C", root, "rev-parse", "--git-dir"])
    out["是 git repo"] = (p.returncode == 0)
    if not out["是 git repo"]:
        return out
    q = git(["-C", root, "show", "%s:%s" % (pinned_sha, UPSTREAM_OBJECT_PATH)])
    out["commit:path 可讀"] = (q.returncode == 0)
    out["_bytes"] = q.stdout if q.returncode == 0 else None
    return out


# ── 找殼:**重用票 96 的實作,不寫第三份** ───────────────────────────────
#
# 早一版這裡是 `shutil.which("sh") or shutil.which("bash")`。
# **裁決者在普通 PowerShell 首跑,第 1 案就停在「找不到 sh/bash」** ——
# 而同一台機器的 Git for Windows 就在預設位置,agent 環境的 PATH 剛好有 `sh`。
# **那是環境等價性缺陷,不是 bootstrap.sh 的問題**,而且與票 96 同形:
# 票 96 已經為 `tests/test_bootstrap.py` 解過同一個問題(方向 3)。
#
# 所以這裡**不再自己找殼**,直接用那一份:`find_sh()` 與 `sh_env()`。
# `sh_env()` 是票 96 第二個缺口換來的 —— 走 Git for Windows 的殼時要把
# 它自己的 coreutils 前置到 PATH,否則 `bootstrap.sh` 會紅在
# `cut: command not found`,而**那種紅看起來像 bootstrap.sh 壞了**。
#
# ⚠ **已知的耦合,原地登記**:那兩支函式住在一個**測試模組**裡,
# 而這裡是維運腳本。要它們搬到共用位置是另一個決定(會動到測試的佈局),
# **本輪不做** —— 本輪的判準是「不要再寫第三份」。
# 這個 import 壞掉會**當場大聲壞掉**(ImportError),不會靜默退化。

def load_bootstrap_helpers():
    """載入票 96 的 `find_sh` / `sh_env` / `derived_candidates`。"""
    import importlib.util
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = os.path.join(repo, "tests", "test_bootstrap.py")
    spec = importlib.util.spec_from_file_location("_e2e_sh_helpers", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def sh_label(sh, hb, run=None):
    """實際用的是哪一支 —— **只印相對於 Git 安裝根的位置**,不印完整路徑。

    ⚠ `run` 要與呼叫 `find_sh()` 時用的**同一個** —— 兩邊各自推導一次的話,
    「找到的那一支」與「標籤比對的候選集」可以來自不同的 Git 安裝根,
    於是一支推導來的殼會被標成 `PATH:...`。**實測撞到過(在探針裡)。**
    """
    try:
        root, cands = hb.derived_candidates(run=run)
        if root and sh in cands:
            return "<Git 安裝根>/%s" % os.path.relpath(sh, root).replace("\\", "/")
        if sh in hb.GIT_FOR_WINDOWS:
            base = os.path.dirname(os.path.dirname(os.path.dirname(sh)))
            return "<Git 安裝根>/%s" % os.path.relpath(sh, base).replace("\\", "/")
    except Exception:
        pass
    return "PATH:%s" % os.path.basename(sh)


# ── clone 準備 ───────────────────────────────────────────────────────────
#
# **每個案例一個 clone。** 下面這份清單就是「案例可變狀態」的全部:
#   1. core.hooksPath          (bootstrap.sh 設,local config)
#   2. .dev/pipeline.json      (ignored,本函式建)
#   3. .dev/provenance.jsonl   (ignored,只有 #13 建)
#   4. .dev/shadow.json        (ignored,**一律不建,並正面斷言不存在**)
#   5. .dev/gate-exemptions.jsonl (有追蹤,clone 帶來;基準行數記下來)
#   6. .claude/skills/ 與 /skills/ (ignored,clone 不帶 ⇒ R4 不動作)
#   7. 工作樹與 index          (由各案例自己造)
# 換 clone 之後 1–7 全部回到已知狀態,不依賴 reset/clean。

def prepare_clone(official, dest, pinned_sha, log):
    git(["clone", "--no-hardlinks", official, dest], check=True)
    git(["-C", dest, "remote", "remove", "origin"], check=True)
    git(["-C", dest, "checkout", "--detach", pinned_sha], check=True)
    git(["-C", dest, "config", "user.name", "e2e-probe"], check=True)
    git(["-C", dest, "config", "user.email", "e2e-probe@example.invalid"], check=True)

    hb = load_bootstrap_helpers()
    tried = []
    sh = hb.find_sh(tried=tried)
    if not sh:
        raise Misuse(
            "找不到可用的 sh/bash —— 跑不了 bootstrap.sh(權威層接不上)。\n"
            "     **試過的每一個位置(依序)**:\n%s\n"
            "     Git 安裝根(由 `git --exec-path` 往上三層推):%s"
            % ("\n".join("       %s" % t for t in tried),
               hb.git_install_root() or "(推不出來)"))
    log["sh"] = sh_label(sh, hb)
    log["sh_tried"] = tried
    b = subprocess.run([sh, "bootstrap.sh"], cwd=dest, capture_output=True,
                       env=hb.sh_env(sh=sh))
    log["bootstrap_rc"] = b.returncode
    log["bootstrap_out"] = (b.stdout + b.stderr).decode("utf-8", "replace")
    if b.returncode != 0:
        raise Misuse("bootstrap.sh 拒絕設定 core.hooksPath:\n%s" % log["bootstrap_out"])

    w(os.path.join(dest, PIPELINE_REL),
      json.dumps({"current_stage": "implement", "feature": "framework-updates",
                  "ticket_id": None}, ensure_ascii=False, indent=2) + "\n")

    # ── 正面斷言(缺一不可)───────────────────────────────────────────
    hp = gout(["-C", dest, "config", "--get", "core.hooksPath"])
    if hp != ".githooks":
        raise Misuse("core.hooksPath 不是 .githooks,而是 %r" % hp)
    if os.path.exists(os.path.join(dest, SHADOW_REL)):
        raise Misuse("clone 裡有 %s —— 影子模式會讓整個閘門退成只記不擋。" % SHADOW_REL)
    if os.path.isdir(os.path.join(dest, ".claude", "skills")):
        raise Misuse(".claude/skills/ 竟然存在 —— R4 的前提與設計不符,停。")
    try:
        import yaml  # noqa: F401
    except Exception as e:
        raise Misuse("PyYAML 不可用(%s)—— gate.py 的站別定義讀不了。" % e)

    hook_path = os.path.join(dest, HOOK_REL)
    log["hook"] = {
        "core.hooksPath": hp,
        "解析後的 hook 路徑": os.path.relpath(hook_path, dest).replace("\\", "/"),
        "hook sha256": sha256_file(hook_path),
        "gate.py sha256": sha256_file(os.path.join(dest, GATE_REL)),
        "leak_scan.py sha256": sha256_file(os.path.join(dest, LEAK_REL)),
        "bootstrap 用的殼": log.get("sh"),
    }
    log["ledger_base_lines"] = line_count(os.path.join(dest, LEDGER_REL))
    return dest


# ── 語料構造 ─────────────────────────────────────────────────────────────

def stages_doc(clone):
    import yaml
    return yaml.safe_load(r(os.path.join(clone, STAGES_REL)))


def write_stages(clone, doc):
    import yaml
    w(os.path.join(clone, STAGES_REL),
      yaml.safe_dump(doc, allow_unicode=True, sort_keys=False))


def defs_move_write_to_review(doc):
    """把 `allows_src_write` 從 research/implement 移到 review。

    ⇒ `implement` 變成「第一個可寫站之前」的站 ⇒ 提交時點落進 `[R2/commit]`。
    **注意不是拿掉就好** —— 提交時點的 R2 走的是「前置站」那一支,
    `elif stage not in writable` 在 `at_commit` 為真時根本不會被評估。
    """
    for s in doc["stages"]:
        if s.get("id") in ("research", "implement"):
            s.pop("allows_src_write", None)
        if s.get("id") == "review":
            s["allows_src_write"] = True
    return doc


def defs_drop_research_r3_exemption(doc):
    for s in doc["stages"]:
        if s.get("id") == "research":
            s.pop("exempts_r3_in_scope", None)
    return doc


def set_stage(clone, stage, ticket_id=None):
    w(os.path.join(clone, PIPELINE_REL),
      json.dumps({"current_stage": stage, "feature": "framework-updates",
                  "ticket_id": ticket_id}, ensure_ascii=False, indent=2) + "\n")


def touch_legacy_member(clone):
    """對 legacy 成員做一個無害改動 —— R3 整條被 legacy 豁免,R2 照常適用。"""
    p = os.path.join(clone, LEGACY_MEMBER)
    with io.open(p, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n# e2e probe: harmless trailing comment\n")
    git(["-C", clone, "add", "--", LEGACY_MEMBER], check=True)


def stage_bytes(clone, rel_path, raw):
    """把位元組寫進工作樹並 `git add`(= 放進 index)。"""
    wb(os.path.join(clone, rel_path.replace("/", os.sep)), raw)
    git(["-C", clone, "add", "-f", "--", rel_path], check=True)


def set_worktree_bytes(clone, rel_path, raw):
    """**只改工作樹,不 add** —— 造出 index 與工作樹分歧。"""
    wb(os.path.join(clone, rel_path.replace("/", os.sep)), raw)


# ── 案例定義 ─────────────────────────────────────────────────────────────
#
# kind:  legal   = 合法對照(預期 commit 成功)
#        reject  = 預期拒絕
#        reverse = 反向放行(現行版本讀 index ⇒ 放行)
#        static  = 不下 commit 的靜態觀察

def build_cases(pinned_sha, up):
    C = []

    def add(**kw):
        kw.setdefault("forbid", ())
        kw.setdefault("proof", "【接線】")
        C.append(kw)

    # ── #8 R2 站別定義來源 ────────────────────────────────────────────
    def s8_legal(c):
        touch_legacy_member(c)
    add(cell="#8", cid="8-legal", kind="legal", setup=s8_legal,
        desc="站別定義原版 + legacy 成員的無害改動",
        expect="exit 0;HEAD 前進", rule=None)

    def s8_reject(c):
        doc = defs_move_write_to_review(stages_doc(c))
        write_stages(c, doc)
        git(["-C", c, "add", "--", STAGES_REL], check=True)
        git(["-C", c, "checkout", "HEAD", "--", STAGES_REL], check=False)
        # ↑ index = 改過的;工作樹 = 原版
        touch_legacy_member(c)
    add(cell="#8", cid="8-reject", kind="reject", setup=s8_reject,
        desc="index 定義 = implement 非可寫站;工作樹定義 = 原版",
        expect="exit 1;[R2/commit];含 index 來源提示",
        rule="R2", must=("[R2/commit]", "本次站別定義取自", LEGACY_MEMBER),
        forbid=("[R3]",))

    def s8_reverse(c):
        doc = defs_move_write_to_review(stages_doc(c))
        write_stages(c, doc)            # 工作樹 = 改過的,**不 add**
        touch_legacy_member(c)
    add(cell="#8", cid="8-reverse", kind="reverse", setup=s8_reverse,
        desc="index 定義 = 原版;工作樹定義 = implement 非可寫站",
        expect="exit 0(現行版本判 index)", rule=None,
        proof="【接線】+ 現行版本判 index")

    # ── #9 R3 research 範圍豁免 ───────────────────────────────────────
    def s9_legal(c):
        set_stage(c, "research")
        stage_bytes(c, "research/probe.py", b"VALUE = 1\n")
    add(cell="#9", cid="9-legal", kind="legal", setup=s9_legal,
        desc="research 站 + research/ 底下新檔(無測試)⇒ #9 豁免 R3",
        expect="exit 0;HEAD 前進", rule=None)

    def s9_reject(c):
        set_stage(c, "research")
        doc = defs_drop_research_r3_exemption(stages_doc(c))
        write_stages(c, doc)
        git(["-C", c, "add", "--", STAGES_REL], check=True)
        git(["-C", c, "checkout", "HEAD", "--", STAGES_REL], check=False)
        stage_bytes(c, "research/probe.py", b"VALUE = 1\n")
    add(cell="#9", cid="9-reject", kind="reject", setup=s9_reject,
        desc="index 定義拿掉 exempts_r3_in_scope;工作樹保留",
        expect="exit 1;[R3] 找不到對應測試;含 index 來源提示",
        rule="R3", must=("[R3]", "research/probe.py", "本次站別定義取自"))

    # ── #10 legacy 條目資格 ───────────────────────────────────────────
    def s10_legal(c):
        touch_legacy_member(c)
    add(cell="#10", cid="10-legal", kind="legal", setup=s10_legal,
        desc="legacy 清單既有成員(確在 go-live 樹裡)⇒ 豁免成立",
        expect="exit 0;HEAD 前進", rule=None)

    def s10_reject(c):
        # **只改工作樹的清單,不 add** —— R6 讀 index(乾淨),#10 讀工作樹(髒)
        p = os.path.join(c, LEGACY_REL)
        with io.open(p, "a", encoding="utf-8", newline="\n") as f:
            f.write("pkg/thing.py\n")
        stage_bytes(c, "pkg/thing.py", b"def go():\n    return 1\n")
    add(cell="#10", cid="10-reject", kind="reject", setup=s10_reject,
        desc="工作樹清單加一筆不在 go-live 樹裡的條目(不 add)",
        expect="exit 1;[R3];**不得出現 [R6]**",
        rule="R3", must=("[R3]", "pkg/thing.py"), forbid=("[R6]",))

    # ── #11 純套件標記豁免 ────────────────────────────────────────────
    def s11_legal(c):
        stage_bytes(c, "pkg/__init__.py", b"")
    add(cell="#11", cid="11-legal", kind="legal", setup=s11_legal,
        desc="index 的 __init__.py 是空的 ⇒ 純標記,豁免成立",
        expect="exit 0;HEAD 前進", rule=None)

    def s11_reject(c):
        stage_bytes(c, "pkg/__init__.py", b"def x():\n    pass\n")
        set_worktree_bytes(c, "pkg/__init__.py", b"")
    add(cell="#11", cid="11-reject", kind="reject", setup=s11_reject,
        desc="index 含 def;工作樹改成空的",
        expect="exit 1;[R3] 找不到對應測試",
        rule="R3", must=("[R3]", "pkg/__init__.py"))

    def s11_reverse(c):
        stage_bytes(c, "pkg/__init__.py", b"")
        set_worktree_bytes(c, "pkg/__init__.py", b"def x():\n    pass\n")
    add(cell="#11", cid="11-reverse", kind="reverse", setup=s11_reverse,
        desc="index 是空的;工作樹含 def",
        expect="exit 0(現行版本判 index)", rule=None,
        proof="【接線】+ 現行版本判 index")

    # ── #11② 真 hook 不可構造 —— **靜態觀察,不下 commit** ────────────
    def s11b(c):
        touch_legacy_member(c)
        set_worktree_bytes(c, "pkg/__init__.py", b"def x():\n    pass\n")
    add(cell="#11②", cid="11b-static", kind="static", setup=s11b,
        desc="未暫存的 pkg/__init__.py + 已暫存的別的檔",
        expect="`git diff --cached -z --name-only --diff-filter=ACM` 不含該檔",
        rule=None,
        proof="【真 hook 不可構造】(限定:靜態構造一個未暫存目標時,"
              "正常 staged_paths 不會選到它)")

    # ── #12 已記錄的票宣告豁免(**只有【接線】**)──────────────────────
    def _commit_ticket(c, modules):
        body = (u"# 票 %s —— e2e probe(臨時)\n\n%s %s\n"
                % (TICKET_NUM, UNTESTED_PREFIX, modules))
        w(os.path.join(c, TICKET_REL), body)
        git(["-C", c, "add", "--", TICKET_REL], check=True)
        p = git(["-C", c, "commit", "-m", "docs: e2e probe ticket"])
        if p.returncode != 0:
            raise Misuse("前置的票 commit 自己就被擋下了:\n%s"
                         % p.stderr.decode("utf-8", "replace")[:1200])

    def _ledger_record(c, declared_in):
        rec = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "file": "pkg/thing.py", "module": "thing", "ticket": TICKET_NUM,
               "stage": "implement", "declared_in": declared_in,
               "reason": "ticket-declared", "tool": "e2e-probe",
               "outcome": "granted", "blocked_by": None, "at_commit": False,
               "content_hash": None, "result_hash": None, "changes_bytes": None}
        with io.open(os.path.join(c, LEDGER_REL), "a",
                     encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def s12_legal(c):
        _commit_ticket(c, "thing")
        _ledger_record(c, TICKET_REL)
        set_stage(c, "implement", ticket_id=None)
        stage_bytes(c, "pkg/thing.py", b"def go():\n    return 1\n")
    add(cell="#12", cid="12-legal", kind="legal", setup=s12_legal,
        desc="帳本紀錄 + 票已進 HEAD 且列了該模組;ticket_id 已清空",
        expect="exit 0;HEAD 前進", rule=None,
        proof="【接線】only(見說明:正式配置下新舊路徑相同,無【差異】可驗)")

    def s12_reject_not_in_head(c):
        w(os.path.join(c, TICKET_REL),
          u"# 票 %s\n\n%s thing\n" % (TICKET_NUM, UNTESTED_PREFIX))  # 不 commit
        _ledger_record(c, TICKET_REL)
        set_stage(c, "implement", ticket_id=None)
        stage_bytes(c, "pkg/thing.py", b"def go():\n    return 1\n")
    add(cell="#12", cid="12-reject-not-in-head", kind="reject",
        setup=s12_reject_not_in_head,
        desc="帳本有紀錄,但票只在工作樹、不在 HEAD",
        expect="exit 1;[R3]", rule="R3",
        must=("[R3]", "pkg/thing.py"),
        proof="【接線】only")

    def s12_reject_wrong_module(c):
        _commit_ticket(c, "other")
        _ledger_record(c, TICKET_REL)
        set_stage(c, "implement", ticket_id=None)
        stage_bytes(c, "pkg/thing.py", b"def go():\n    return 1\n")
    add(cell="#12", cid="12-reject-wrong-module", kind="reject",
        setup=s12_reject_wrong_module,
        desc="票在 HEAD,但它宣告的是別的模組",
        expect="exit 1;[R3]", rule="R3",
        must=("[R3]", "pkg/thing.py"),
        proof="【接線】only")

    # ── #13 上游成品豁免 ──────────────────────────────────────────────
    up_raw = up.get("_bytes")

    def _provenance(c):
        rec = {"path": "pkg/thing.py", "upstream_commit": pinned_sha,
               "upstream_path": UPSTREAM_OBJECT_PATH,
               "note": "驗證者自建,非 sync.py 產物"}
        w(os.path.join(c, PROVENANCE_REL),
          json.dumps(rec, ensure_ascii=False) + "\n")

    def s13_legal(c):
        _provenance(c)
        stage_bytes(c, "pkg/thing.py", up_raw)
    add(cell="#13", cid="13-legal", kind="legal", setup=s13_legal,
        desc="index 位元組 = 上游物件 ⇒ provenance 豁免成立",
        expect="exit 0;HEAD 前進;帳本出現 upstream-provenance",
        rule=None, needs_upstream=True)

    def s13_reject(c):
        _provenance(c)
        drifted = up_raw.replace(b"\n", b"\n", 1) + b"\n# drift: one content char\n"
        stage_bytes(c, "pkg/thing.py", drifted)
        set_worktree_bytes(c, "pkg/thing.py", up_raw)
    add(cell="#13", cid="13-reject", kind="reject", setup=s13_reject,
        desc="index 漂移(改內容字元,非行尾);工作樹 = 上游物件",
        expect="exit 1;[R3];**不得出現 [R8**",
        rule="R3", must=("[R3]", "pkg/thing.py"), forbid=("[R8",),
        needs_upstream=True)

    def s13_reverse(c):
        _provenance(c)
        stage_bytes(c, "pkg/thing.py", up_raw)
        set_worktree_bytes(c, "pkg/thing.py",
                           up_raw + b"\n# drift in worktree only\n")
    add(cell="#13", cid="13-reverse", kind="reverse", setup=s13_reverse,
        desc="index = 上游物件;工作樹漂移",
        expect="exit 0(現行版本判 index)", rule=None,
        needs_upstream=True, proof="【接線】+ 現行版本判 index")

    return C


# ── 執行一個案例 ─────────────────────────────────────────────────────────

def parse_trace(trace_path):
    """從 git 的 trace2 事件裡找「git 啟動了 pre-commit hook」。

    **追蹤證不到就說證不到**,不編造訊號。
    """
    found, samples = False, []
    try:
        with io.open(trace_path, encoding="utf-8", errors="replace") as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    ev = json.loads(ln)
                except Exception:
                    continue
                if ev.get("event") != "child_start":
                    continue
                argv = ev.get("argv") or []
                blob = " ".join(str(x) for x in argv) + " " + \
                    str(ev.get("hook_name") or "") + " " + \
                    str(ev.get("child_class") or "")
                if "pre-commit" in blob:
                    found = True
                    if len(samples) < 3:
                        samples.append(blob.strip()[:300])
    except Exception as e:
        return False, ["(追蹤檔讀不到:%s)" % e]
    return found, samples


def run_case(case, official, workroot, pinned_sha, up, idx):
    res = {"cell": case["cell"], "cid": case["cid"], "kind": case["kind"],
           "desc": case["desc"], "expect": case["expect"],
           "proof": case["proof"], "actual": "", "verdict": "未完成",
           "why": "", "evidence": {}}

    if case.get("needs_upstream") and not (
            up.get("commit:path 可讀") and up.get("_bytes")):
        res["why"] = "前置條件未完成:上游錨不可用(見前置表)"
        res["actual"] = "(未執行)"
        return res

    clone = os.path.join(workroot, "case-%02d" % idx, "clone")
    log = {}
    try:
        prepare_clone(official, clone, pinned_sha, log)
        res["evidence"]["hook"] = log["hook"]
        base_lines = log["ledger_base_lines"]
        case["setup"](clone)

        staged = gout(["-C", clone, "diff", "--cached", "-z", "--name-only",
                       "--diff-filter=ACM"]).split("\0")
        staged = [x for x in staged if x.strip()]
        res["evidence"]["staged"] = staged

        # ── 靜態案例:不下 commit ─────────────────────────────────────
        if case["kind"] == "static":
            hit = "pkg/__init__.py" in staged
            res["actual"] = "staged=%s" % staged
            res["verdict"] = "通過" if (not hit and staged) else "失敗"
            res["why"] = ("未暫存的目標確實不在 staged 清單裡" if not hit
                          else "未暫存的目標竟然出現在 staged 清單裡")
            return res

        head_before = gout(["-C", clone, "rev-parse", "HEAD"])
        # 提交前再確認一次接線沒有被案例的 setup 動過
        if gout(["-C", clone, "config", "--get", "core.hooksPath"]) != ".githooks":
            raise Misuse("提交前 core.hooksPath 已不是 .githooks。")

        trace_path = os.path.join(workroot, "case-%02d" % idx, "trace2.jsonl")
        os.makedirs(os.path.dirname(trace_path), exist_ok=True)
        p = git(["-C", clone, "commit", "-m", "e2e: %s" % case["cid"]],
                extra_env={"GIT_TRACE2_EVENT": trace_path})
        rc = p.returncode
        out = (p.stdout + p.stderr).decode("utf-8", "replace")
        head_after = gout(["-C", clone, "rev-parse", "HEAD"])
        hook_seen, trace_samples = parse_trace(trace_path)

        # **重置(= 丟掉這個 clone)之前先把證據存下來**
        new_ledger = tail_lines(os.path.join(clone, LEDGER_REL), base_lines)
        res["evidence"].update({
            "rc": rc, "head_before": head_before, "head_after": head_after,
            "head 不變": head_before == head_after,
            "git trace2 看到 pre-commit hook": hook_seen,
            "trace2 樣本": trace_samples,
            "帳本新增行": new_ledger,
            "輸出": out,
        })
        res["actual"] = "rc=%d;HEAD %s;trace2 hook=%s" % (
            rc, "不變" if head_before == head_after else "前進", hook_seen)

        # ── 「不算規則擋下」的樣態,優先判 ────────────────────────────
        for needle, why in NOT_A_RULE_BLOCK:
            if needle in out:
                res["verdict"] = "未完成"
                res["why"] = "%s(命中:%s)" % (why, needle)
                return res

        if case["kind"] in ("legal", "reverse"):
            ok = (rc == 0 and head_after != head_before and hook_seen)
            res["verdict"] = "通過" if ok else "失敗"
            if not ok:
                res["why"] = ("rc=%d / HEAD %s / trace2 hook=%s —— 三者要全滿足"
                              % (rc, "不變" if head_after == head_before else "前進",
                                 hook_seen))
            elif not hook_seen:
                res["why"] = "【追蹤未證明】git 啟動 hook 這一層"
            return res

        # ── 預期拒絕 ──────────────────────────────────────────────────
        if rc == 0:
            res["verdict"] = "失敗"
            res["why"] = ("**意外提交成功** —— 新 HEAD %s;clone 保留於 %s"
                          % (head_after, os.path.realpath(clone)))
            res["keep_clone"] = True
            return res
        checks = {
            "非零退出碼": rc != 0,
            "HEAD 不變": head_after == head_before,
            "有閘門擋下訊息": "[六站閘門/pre-commit] commit 已擋下" in out,
            "git trace2 看到 hook": hook_seen,
            "暫存內容仍在 index": bool(gout(
                ["-C", clone, "diff", "--cached", "--name-only"]).strip()),
        }
        for s in case.get("must", ()):
            checks["訊息含 %r" % s] = (s in out)
        for s in case.get("forbid", ()):
            checks["訊息不含 %r" % s] = (s not in out)
        res["evidence"]["逐條判準"] = checks
        res["verdict"] = "通過" if all(checks.values()) else "失敗"
        if res["verdict"] == "失敗":
            res["why"] = "未滿足:" + "、".join(
                k for k, v in checks.items() if not v)
        return res

    except Misuse as e:
        res["verdict"] = "未完成"
        res["why"] = "前置/誤用:%s" % e
        return res
    except Exception as e:
        res["verdict"] = "未完成"
        res["why"] = "例外:%r" % (e,)
        return res


# ── 清理 ─────────────────────────────────────────────────────────────────

def cleanup(workroot, official, marker_id, keep, report):
    """三道斷言全過才刪。任一不成立 ⇒ **不刪,報路徑**。"""
    real = os.path.realpath(workroot)
    checks = {
        "① 標記檔存在且是本輪的": False,
        "② 位於系統暫存目錄底下、且 basename 以 %s 起頭" % WORK_PREFIX: False,
        "③ 與正式 repo 互不包含(比路徑元件,非 startswith)": False,
    }
    try:
        checks["① 標記檔存在且是本輪的"] = (
            r(os.path.join(real, MARKER_NAME)).strip() == marker_id)
    except Exception:
        pass
    tmp = os.path.realpath(tempfile.gettempdir())
    checks[list(checks)[1]] = (
        os.path.basename(real).startswith(WORK_PREFIX)
        and is_ancestor_or_same(tmp, real) and real != tmp)
    off = os.path.realpath(official)
    checks[list(checks)[2]] = not (is_ancestor_or_same(off, real)
                                   or is_ancestor_or_same(real, off))
    report["清理斷言"] = checks
    if keep:
        report["清理"] = "**未清理**(有案例意外提交成功)—— 路徑:%s" % real
        return
    if not all(checks.values()):
        report["清理"] = "**未清理**(斷言未全過)—— 路徑:%s" % real
        return
    try:
        shutil.rmtree(real, onerror=_on_rm_error)
        report["清理"] = "已刪除:%s(存在=%s)" % (real, os.path.exists(real))
    except Exception as e:
        report["清理"] = "**清理失敗,保留**:%s —— %r" % (real, e)


# ── 主流程 ───────────────────────────────────────────────────────────────

def self_check():
    """防誤用檢查自己的自檢。**不跑任何案例、不碰 git 以外的東西。**

    ⚠ 這證明的是「那些 argv/env 會不會被擋」,**不是整支腳本安全**。

    住在腳本裡而不是某個臨時目錄:**一個只在作者機器上跑過一次的自檢,
    下一次沒有人會跑。**
    """
    rows = []

    def case(args, expect, label):
        try:
            _assert_safe_git_argv(args)
            got = "放行"
            why = ""
        except Misuse as e:
            got = "擋下"
            why = str(e).splitlines()[0]
        rows.append((label, expect, got, "✓" if got == expect else "✗", why))

    # ── 跳過 hook ────────────────────────────────────────────────────
    case(["-C", "x", "commit", "-m", "y", "--no-verify"], "擋下", "commit --no-verify")
    case(["-C", "x", "commit", "-n", "-m", "y"], "擋下", "commit -n")
    case(["-C", "x", "commit", "-nv", "-m", "y"], "擋下", "commit -nv(短旗標束含 n)")
    case(["-C", "x", "commit", "-am", "y"], "放行", "commit -am(不含 n)")
    case(["-C", "x", "commit", "-m", "y"], "放行", "一般 commit")
    # ── 指令層覆寫 hooksPath ─────────────────────────────────────────
    case(["-c", "core.hooksPath=/tmp/evil", "-C", "x", "commit", "-m", "y"],
         "擋下", "-c core.hooksPath=")
    case(["--config-env=core.hooksPath=EVIL", "commit"], "擋下", "--config-env hooksPath")
    # ── ⭐ 讀 vs 寫(2026-09-24,A 輪第 2 次被誤擋換來的兩格)──────────
    case(["-C", "x", "config", "--get", "core.hooksPath"],
         "放行", "⭐ **讀** core.hooksPath(--get)")
    case(["-C", "x", "config", "--get-all", "core.hooksPath"],
         "放行", "⭐ 讀 core.hooksPath(--get-all)")
    case(["-C", "x", "config", "core.hooksPath", ".githooks"],
         "擋下", "⭐ **寫** core.hooksPath(位置參數)")
    case(["-C", "x", "config", "--add", "core.hooksPath", ".githooks"],
         "擋下", "⭐ 寫 core.hooksPath(--add)")
    case(["-C", "x", "config", "--unset", "core.hooksPath"],
         "擋下", "⭐ 寫 core.hooksPath(--unset)")
    case(["-C", "x", "config", "--replace-all", "core.hooksPath", "x"],
         "擋下", "⭐ 寫 core.hooksPath(--replace-all)")
    case(["-C", "x", "config", "core.hooksPath"],
         "擋下", "⭐ 無旗標(讀寫分不出)⇒ fail-closed")
    # ── 不相干的 config 不受影響 ─────────────────────────────────────
    case(["-C", "x", "config", "user.name", "e2e"], "放行", "config user.name(寫,不相干)")
    case(["-C", "x", "config", "--get", "user.email"], "放行", "config --get user.email")
    # ── 其他子命令 ───────────────────────────────────────────────────
    case(["-C", "x", "clone", "--no-hardlinks", "a", "b"], "放行", "clone")
    case(["-C", "x", "diff", "--cached", "--name-only"], "放行", "diff --cached")

    print("=" * 96)
    print("防誤用自檢 —— argv(⚠ 不宣稱整支腳本安全)")
    print("=" * 96)
    print("%-44s %-6s %-6s %-4s %s" % ("案例", "預期", "實際", "", "擋下訊息首行"))
    print("-" * 96)
    for label, expect, got, mark, why in rows:
        print("%-44s %-6s %-6s %-4s %s" % (label, expect, got, mark, why[:44]))

    env_rows = []

    def env_case(env, expect, label):
        try:
            _assert_safe_env(env)
            got = "放行"
        except Misuse:
            got = "擋下"
        env_rows.append((label, expect, got, "✓" if got == expect else "✗"))

    for k in ("GIT_CONFIG_COUNT", "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        env_case({k: "x"}, "擋下", "env %s" % k)
    env_case({"FOO": "core.hooksPath=evil"}, "擋下", "env 值提到 hooksPath")
    env_case({"GIT_TRACE2_EVENT": "t.jsonl"}, "放行", "env GIT_TRACE2_EVENT(追蹤用)")

    print()
    print("=" * 96)
    print("防誤用自檢 —— env")
    print("=" * 96)
    for label, expect, got, mark in env_rows:
        print("%-44s %-6s %-6s %s" % (label, expect, got, mark))

    path_rows = []
    for a, b, want, label in (
            (r"C:\p\agent-gates", r"C:\p\agent-gates2", False,
             "agent-gates2 不是 agent-gates 的子路徑(startswith 會判錯)"),
            (r"C:\p\agent-gates", r"C:\p\agent-gates\sub", True, "真子路徑"),
            (r"C:\p\agent-gates", r"C:\p\agent-gates", True, "同一個"),
            (r"C:\p\agent-gates\sub", r"C:\p\agent-gates", False, "反向")):
        got = is_ancestor_or_same(a, b)
        path_rows.append((label, want, got, "✓" if got == want else "✗"))

    print()
    print("=" * 96)
    print("路徑包含判定(比元件,不用 startswith)")
    print("=" * 96)
    for label, want, got, mark in path_rows:
        print("%-62s want=%-5s got=%-5s %s" % (label, want, got, mark))

    bad = ([r for r in rows if r[3] == "✗"] + [r for r in env_rows if r[3] == "✗"]
           + [r for r in path_rows if r[3] == "✗"])
    print()
    print("整體 : %s" % ("全部符合預期" if not bad else "**有 %d 格不符預期**" % len(bad)))
    return 0 if not bad else 1


def official_state(official):
    return {
        "HEAD": gout(["-C", official, "rev-parse", "HEAD"]),
        "status --porcelain": gout(["-C", official, "status", "--porcelain"]),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="權威層端對端驗證(A 輪)")
    ap.add_argument("--official", default=".", help="正式 repo 路徑")
    ap.add_argument("--round", default="A", choices=["A", "B"])
    ap.add_argument("--sha", default=None, help="要釘住的 commit(預設 = 正式 repo 的 HEAD)")
    ap.add_argument("--continue-on-failure", action="store_true",
                    help="不 fail-fast(預設 fail-fast)")
    ap.add_argument("--self-check", action="store_true",
                    help="只跑防誤用自檢,不跑任何案例")
    ap.add_argument("--smoke", action="store_true",
                    help="煙霧測試:**結果不是證據**,只用來排除腳本自身的機械問題")
    a = ap.parse_args(argv)

    if a.self_check:
        return self_check()

    if a.round == "B":
        print("[拒絕] B 輪(舊版 gate.py 對照)**本版未實作** ——")
        print("       【差異】證據由隔離層既有測試提供(票 133 #10/#11/#13);")
        print("       本項缺的是真 hook 的【接線】證據,那是 A 輪。")
        return 2

    official = os.path.realpath(a.official)
    started = datetime.datetime.now(datetime.timezone.utc)
    before = official_state(official)
    pinned = a.sha or before["HEAD"]

    print("=" * 78)
    print("權威層端對端驗證 —— A 輪(六格)")
    if a.smoke:
        print("⚠⚠ **煙霧測試 —— 本輪結果【不是證據】** ⚠⚠")
        print("     只用來排除腳本自身的機械問題(前置/誤用)。")
        print("     結案只認裁決者本人執行的那一輪。")
    print("=" * 78)
    print("正式 repo(進入):")
    print("  HEAD               : %s" % before["HEAD"])
    print("  status --porcelain : %s" % (before["status --porcelain"] or "(空)"))
    print("  釘住的 SHA         : %s" % pinned)
    print()

    up = upstream_premises(pinned)
    print("#13 上游前置(**不印完整路徑**):")
    for k in ("指標檔格式合法(恰好一行)", "是 git repo", "commit:path 可讀",
              "上游位置識別(遮蔽)"):
        print("  %-22s : %s" % (k, up.get(k)))
    print()

    # 殼的前置:**一次就印出來**,不要等到第 1 案才發現找不到
    hb = load_bootstrap_helpers()
    tried = []
    sh = hb.find_sh(tried=tried)
    print("bootstrap.sh 的殼(票 96 的 find_sh,三層:PATH → 寫死 → git --exec-path):")
    if sh:
        print("  實際用的           : %s" % sh_label(sh, hb))
        print("  工具鏈前置到 PATH  : %s"
              % (hb.sh_env(sh=sh).get("PATH", "") !=
                 os.environ.get("PATH", "")))
    else:
        print("  **找不到** —— 試過的每一個位置(依序):")
        for t in tried:
            print("       %s" % t)
        print("  Git 安裝根(由 `git --exec-path` 往上三層推):%s"
              % (hb.git_install_root() or "(推不出來)"))
    print()

    workroot = tempfile.mkdtemp(prefix=WORK_PREFIX)
    marker_id = uuid.uuid4().hex
    w(os.path.join(workroot, MARKER_NAME), marker_id + "\n")

    cases = build_cases(pinned, up)
    results, keep = [], False
    try:
        for i, c in enumerate(cases, 1):
            print("[%2d/%2d] %-24s %s" % (i, len(cases), c["cid"], c["desc"]))
            res = run_case(c, official, workroot, pinned, up, i)
            results.append(res)
            if res.get("keep_clone"):
                keep = True
            print("        -> %-6s %s" % (res["verdict"], res["why"] or res["actual"]))
            if res["verdict"] != "通過" and not a.continue_on_failure:
                print("        (預設 fail-fast:停,不跑後面的)")
                break
    finally:
        after = official_state(official)
        report = {}
        cleanup(workroot, official, marker_id, keep, report)

        print()
        print("=" * 78)
        print("摘要")
        print("=" * 78)
        hdr = ("格", "案例", "預期", "實際", "判定", "證明力")
        print("%-6s %-24s %-34s %-30s %-6s %s" % hdr)
        print("-" * 140)
        for x in results:
            print("%-6s %-24s %-34s %-30s %-6s %s"
                  % (x["cell"], x["cid"], x["expect"][:34], x["actual"][:30],
                     x["verdict"], x["proof"]))
        print()
        for k, v in report.get("清理斷言", {}).items():
            print("  清理斷言 %s : %s" % (k, v))
        print("  清理 : %s" % report.get("清理"))
        print()
        print("正式 repo(結束):")
        print("  HEAD               : %s" % after["HEAD"])
        print("  status --porcelain : %s" % (after["status --porcelain"] or "(空)"))
        print("  受追蹤檔案/index/HEAD/設定 不變 : %s"
              % (after["HEAD"] == before["HEAD"]
                 and after["status --porcelain"] == before["status --porcelain"]))
        print("  ⚠ `.dev/reports/` 有預期新增(本腳本的報告)——")
        print("     **不宣稱正式 repo 全程沒有任何寫入**。")

        stamp = started.strftime("%Y-%m-%dT%H%M%SZ")
        rp = os.path.join(official, ".dev", "reports",
                          "%s-authority-layer-e2e-roundA%s.md"
                          % (stamp, "-SMOKE-not-evidence" if a.smoke else ""))
        write_report(rp, started, before, after, pinned, up, results, report,
                     smoke=a.smoke)
        print()
        print("報告:%s" % rp)

    bad = [x for x in results if x["verdict"] != "通過"]
    return 0 if (results and not bad) else 1


def write_report(path, started, before, after, pinned, up, results, report,
                 smoke=False):
    L = []
    A = L.append
    A(u"# 權威層端對端驗證 —— A 輪(六格)%s"
      % (u" · **煙霧測試(非證據)**" if smoke else u""))
    A(u"")
    if smoke:
        A(u"> ## ⚠⚠ **本報告是煙霧測試,【不是證據】。** ⚠⚠")
        A(u">")
        A(u"> 由 **agent** 執行,目的只有一個:**排除腳本自身的機械問題**"
          u"(前置/誤用類)。")
        A(u"> **結案只認裁決者本人在普通終端機執行的那一輪** —— 協定不變。")
        A(u"> 下面每一格的「通過」都**不得**被引用為權威層的證據;"
          u"它只說「腳本跑得完」。")
        A(u"")
    A(u"**時間**:%s" % started.isoformat())
    A(u"**釘住的 SHA**:`%s`" % pinned)
    A(u"**B 輪**:未實作(【差異】由隔離層既有測試提供)")
    A(u"**執行者**:見下方〈執行安排〉")
    A(u"")
    A(u"## 正式 repo 進出")
    A(u"")
    A(u"| | 進入 | 結束 |")
    A(u"|---|---|---|")
    A(u"| `HEAD` | `%s` | `%s` |" % (before["HEAD"], after["HEAD"]))
    A(u"| `status --porcelain` | %s | %s |"
      % (before["status --porcelain"] or u"(空)",
         after["status --porcelain"] or u"(空)"))
    A(u"")
    A(u"⚠ 措辭:**受追蹤檔案、index、HEAD 與設定不變;`.dev/reports/` 有預期新增。**")
    A(u"**不宣稱正式 repo 全程沒有任何寫入。**")
    A(u"")
    A(u"## #13 上游前置(不記完整路徑)")
    A(u"")
    for k in (u"指標檔格式合法(恰好一行)", u"是 git repo", u"commit:path 可讀",
              u"上游位置識別(遮蔽)"):
        A(u"- %s:`%s`" % (k, up.get(k)))
    A(u"")
    A(u"⚠ `.dev/provenance.jsonl` 是**驗證者自建,非 `sync.py` 產物**。")
    A(u"")
    A(u"## 摘要")
    A(u"")
    A(u"| 格 | 案例 | 預期 | 實際 | 判定 | 證明力 |")
    A(u"|---|---|---|---|---|---|")
    for x in results:
        A(u"| %s | `%s` | %s | %s | **%s** | %s |"
          % (x["cell"], x["cid"], x["expect"], x["actual"], x["verdict"], x["proof"]))
    A(u"")
    A(u"## 逐案例證據")
    A(u"")
    for x in results:
        A(u"### `%s` —— %s" % (x["cid"], x["desc"]))
        A(u"")
        A(u"- **判定**:**%s**%s" % (x["verdict"], (u" —— " + x["why"]) if x["why"] else u""))
        ev = x.get("evidence", {})
        for k in (u"staged", u"rc", u"head_before", u"head_after", u"head 不變",
                  u"git trace2 看到 pre-commit hook", u"trace2 樣本", u"帳本新增行"):
            if k in ev:
                A(u"- **%s**:`%r`" % (k, ev[k]))
        if u"hook" in ev:
            A(u"- **hook 身分**:`%r`" % (ev[u"hook"],))
        if u"逐條判準" in ev:
            A(u"- **逐條判準**:")
            for k, v in ev[u"逐條判準"].items():
                A(u"  - %s:`%s`" % (k, v))
        if ev.get(u"輸出"):
            A(u"")
            A(u"```")
            A(ev[u"輸出"].rstrip()[:4000])
            A(u"```")
        A(u"")
    A(u"## 清理")
    A(u"")
    for k, v in report.get(u"清理斷言", {}).items():
        A(u"- %s:`%s`" % (k, v))
    A(u"- **結果**:%s" % report.get(u"清理"))
    A(u"")
    A(u"## 證據限制(**不編造訊號**)")
    A(u"")
    A(u"- **非零退出碼 + HEAD 不變,本身不證明是 hook 擋下的** —— "
      u"所以每個預期拒絕都要同時滿足〈逐條判準〉裡的每一條。")
    A(u"- **`git trace2` 證明的是「git 啟動了 pre-commit hook」** —— "
      u"它**不**證明 hook 內部走了哪一條規則;那一層由訊息內容與帳本新增行承擔。"
      u"追蹤沒看到就記 `False`,**不補一個替代訊號**。")
    A(u"- **#12 只有【接線】**:正式配置下 `EXEMPTION_LOG` 與舊碼自組的路徑"
      u"**逐字相同**,真 hook 在任何構造下都給一樣的答案 ⇒ **無【差異】可驗**。")
    A(u"- **#11② 限定為**:「靜態構造一個未暫存目標時,正常 `staged_paths` "
      u"不會選到它」。**不概括成真實流程永遠不可能發生 index 讀取失敗。**")
    A(u"- **#8/#9 的黑箱結果可驗證來源行為**,但**不能單靠兩個案例宣稱"
      u"「共用同一次讀取」** —— 那個構造性質由程式與既有測試支撐。")
    A(u"- 合法對照**不要求**每一案例都新增豁免帳本行或印個人清單警告 —— "
      u"正常執行可能兩者皆無。")
    A(u"")
    A(u"## 執行安排")
    A(u"")
    A(u"本輪由**裁決者本人**在普通終端機執行。")
    A(u"⚠ **repo 內找不到一份載明「REAL 層材料須來自本人或 CI」的協定文件** ——")
    A(u"`docs/agents/friction-log.md` 只有一處提到「三層驗收(UNIT / CLEAN / REAL)」,")
    A(u"`docs/tickets/framework-updates/22-machine-recovery-drill.md` 只記了一次 REAL 層通過,")
    A(u"**兩處都沒有寫來源規則**。所以這一句是**本輪的口頭裁決**,不是可引用的條文。")
    A(u"⚠ **人工按下按鈕不自動代表獨立設計或獨立驗收** —— "
      u"本腳本由 agent 設計與撰寫,執行者是人;兩者不互相背書。")
    A(u"")
    A(u"## 結案")
    A(u"")
    A(u"**票 133 與票 138 均不因本報告預先結案。**")
    A(u"票 138 的命題是「人工步驟沒有被寫下來」—— 見 `docs/agents/authority-layer-e2e.md`;")
    A(u"是否足夠由裁決者判定。")
    w(path, u"\n".join(L) + u"\n")


if __name__ == "__main__":
    sys.exit(main())
