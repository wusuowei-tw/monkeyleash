# -*- coding: utf-8 -*-
"""六站流程閘門 — 單一判定邏輯,兩層共用。

兩種呼叫模式(邏輯只有這一份):
  1. agent 前哨:`python gate.py`            讀 stdin 的 PreToolUse JSON,判單一檔案
     exit 0 放行 / exit 2 擋下(stderr 回饋給 AI)
  2. 權威判定:`python gate.py --pre-commit`  讀 git staged 檔案,逐一判定
     exit 0 放行 / exit 1 擋下 commit(綁得住所有人,含非 Claude 的 agent 與人工 commit)

三條硬擋:
  R1  docs/specs/** 內容含程式碼(``` 圍籬 / def / import / function)
  R2  pipeline.json 的 stage != implement 時寫入原始碼目錄
  R3  寫原始碼但對應 tests/test_<name>.py 不存在(防先寫碼再補測試)
"""

import ast
import datetime
import io
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PIPELINE = os.path.join(ROOT, ".dev", "pipeline.json")          # 狀態(被寫)
STAGES_DEF = os.path.join(ROOT, ".agents", "pipeline-stages.yaml")  # 定義(唯讀)
CANON_CODE_REVIEW = os.path.join(ROOT, ".agents", "skills", "code-review", "SKILL.md")

# 原本是 SRC_DIRS 白名單 —— 那是 fail-open:任何**新**模組都不在名單上,
# 一律放行。spec 要求「新增一個獨立模組」時整站無防護。改為黑名單:
# 除了下列非原始碼位置,其餘副檔名符合的一律視為原始碼。新模組預設被守。
# 狀態檔分類。判準是**這個檔案壞掉或消失時,正確行為是什麼**:
#   證據(消失即失去判定依據 → fail-closed)  放 .dev/,進版控
#   快取(可重建的純加速結構 → 重算)         放 .cache/,不進版控
# 目錄本身就是分類,不必靠記性維持;新增狀態檔時看它該擺哪就知道它是哪一類。
EXEMPTION_LOG = os.path.join(ROOT, ".dev", "gate-exemptions.jsonl")   # 證據
RUN_LOG = os.path.join(ROOT, ".dev", "test-runs.jsonl")               # 證據

LEGACY_LIST = os.path.join(ROOT, ".agents", "legacy-no-redlight.txt")  # 凍結定義,只減不增


def read_go_live():
    """紅燈紀錄機制上線的 commit —— 清單的入場券就是「在這個 commit 的樹裡」。
    不用日期(可改),用樹(要改寫歷史才動得了)。

    **從清單檔本身讀,不寫死在這裡。** gate.py 是要被照抄到新專案的框架檔,
    而 sha 綁死產生它的那個 repo:寫死的話照抄過去會拿一個在目標 repo
    不存在的 commit 去驗每一筆,安裝的強制驗證當場失敗。
    sha 與它定義的清單是同一件事,住在同一個檔案裡。
    """
    try:
        for line in io.open(LEGACY_LIST, encoding="utf-8"):
            if line.startswith("# go-live:"):
                return line.split(":", 1)[1].strip() or None
    except Exception:
        return None
    return None


MOUNT_CACHE = os.path.join(ROOT, ".cache", "mount-check.json")        # 快取

# 閘門自身 —— R2 豁免、R3 照常適用。名單是**具體檔案**,不是「.claude 底下的 .py」
# 這種籠統類別:後者又是白名單思維的變形。理由見 docs/adr/0004。
GATE_SELF = (".claude/hooks/gate.py",)

# 規則的分時點語意差異 —— **宣告寫在規則自己的定義裡**,不在測試裡維護豁免清單
# (那會退化成裝飾)。要新增一條分歧就得動這裡並寫 ADR,是看得見的動作。
# 未宣告卻出現「權威比前哨鬆」= 缺陷,由不變式測試擋下。
RULE_DIVERGENCE = {
    "R2": {
        "adr": "docs/adr/0005-r2-time-point-semantics.md",
        "why": "寫入時問『現在這一站可以寫原始碼嗎』;提交時問『你是不是還停在前置站』。"
               "實作完成後站別本來就會往 review / idle 走,拿寫入時的問題去問提交會擋掉每一次合法提交。",
    },
    "R3": {
        "adr": "docs/adr/0013-r3-redlight-judges-the-implementation.md",
        "why": "紅燈的**票號歸屬**只在前哨問得出來 —— 提交時 ticket_id 已清空"
               "(一輪做完站別會往前走),拿寫入時的問題去問提交會擋掉每一次合法提交。"
               "實質保證不變:兩個時點都要求『紅燈發生在這次改動之前』(HEAD 雜湊那一半),"
               "提交時少的只是『屬於哪一張票』這個歸屬,不是紅燈本身。",
    },
    "R7": {
        "adr": "docs/adr/0008-r7-is-sentinel-only.md",
        "why": "R7 管的是**工具呼叫**,而 commit 只看得到 staged 檔案內容 —— "
               "『這個檔案是用 Bash 還是 Write 寫的』在提交時已經不存在了。"
               "因此 R7 只活在前哨,繞過前哨就沒有第二道。這是規則對象的性質,不是放水。",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# 三份非原始碼清單。**判準只有一句:會不會被執行,或被建置工具當成邏輯消費。**
#
# 每一項都要寫理由,而且理由要用同一句判準表述 —— 清單一長,判準就會漂移,
# 理由欄是讓漂移看得見的東西。沒有它,一年後有人往裡面加 entrypoint.sh,
# 沒有東西攔得住。
#
# 三份互斥:同一個項目不得落在兩份裡,否則行為取決於檢查順序,那是隱形的。
# ─────────────────────────────────────────────────────────────────────────────

NON_SOURCE_DIRS = {
    ".dev": "流程狀態與證據,不被執行",
    ".agents": "skill 定義與站別定義,由 agent 讀取為指令文字,不被執行",
    "skills": "同 .agents,鏡像目錄",
    "docs": "文件,不被執行",
    "tests": "測試自身,受測試執行器消費但不是產品原始碼(R3 的對象是被測物)",
    "logs": "執行輸出,不被執行",
    "assets": "靜態資產,不被執行",
    "build": "建置產出物,不是來源",
    "scripts": "維運腳本,不進產品線;變更由人直接驗證",
    ".venv": "第三方套件,不是本 repo 的來源",
    "node_modules": "第三方套件,不是本 repo 的來源",
    ".git": "版控內部資料,不被執行",
    "__pycache__": "位元碼快取,由來源產生",
    "tradingagents.egg-info": "封裝中繼資料,由來源產生",
}
# prototype 依定義是丟棄式的,不進產品線,不受站別限制(見 docs/adr/0002)
PROTOTYPE_RE = re.compile(r"^\.scratch/[^/]+/prototype/")

# 原本是 CODE_EXT 白名單(只有 9 種副檔名算原始碼)—— 與 SRC_DIRS 同一個病:
# 任何**新型態**的檔案(Dockerfile、Makefile、無副檔名腳本、還沒用過的工具的組態)
# 都不在名單上,一律放行。目錄那層已反轉(見 docs/adr/0003),這是最後一處。
#
# 反轉後:原始碼目錄底下一切皆視為原始碼,除非副檔名在下列清單內。
# 誤擋的方向可枚舉且穩定(文件、資料、鎖定檔),漏守的方向是開放的。
# 被誤擋的檔案,正確處置是把副檔名加進這裡 —— 看得見的決定,不是沉默的洞。
NON_SOURCE_EXT = {
    ".md": "文件,不被執行", ".rst": "文件,不被執行",
    ".txt": "文件,不被執行", ".adoc": "文件,不被執行",
    ".csv": "資料,不被執行", ".tsv": "資料,不被執行",
    ".json": "設定值或資料,被讀取但不含可執行邏輯",
    ".yaml": "設定值或資料,被讀取但不含可執行邏輯",
    ".yml": "設定值或資料,被讀取但不含可執行邏輯",
    ".toml": "設定值,被讀取但不含可執行邏輯",
    ".ini": "設定值,被讀取但不含可執行邏輯",
    ".cfg": "設定值,被讀取但不含可執行邏輯",
    ".xml": "資料,被讀取但不含可執行邏輯",
    ".properties": "設定值,被讀取但不含可執行邏輯",
    ".lock": "相依鎖定檔,由套件管理器產生",
    ".log": "執行輸出,不被執行",
    ".pyc": "位元碼,由來源產生", ".pyo": "位元碼,由來源產生",
    ".png": "資產,不被執行", ".jpg": "資產,不被執行",
    ".jpeg": "資產,不被執行", ".gif": "資產,不被執行",
    ".svg": "資產,不被執行", ".ico": "資產,不被執行",
    ".pdf": "資產,不被執行", ".zip": "封存,不被執行", ".gz": "封存,不被執行",
    ".xlsx": "試算表報表,資料,不被執行(儀表板產物,日常資料流)",
    ".xls": "試算表報表,資料,不被執行", ".ods": "試算表報表,資料,不被執行",
    ".parquet": "資料,不被執行", ".duckdb": "資料庫檔,不被執行",
    ".db": "資料庫檔,不被執行", ".sqlite": "資料庫檔,不被執行",
    ".example": "樣板,不被執行也不被建置消費",
    ".sample": "樣板,不被執行也不被建置消費",
    ".template": "樣板,不被執行也不被建置消費",
}

# 無副檔名、或副檔名分不出性質的具體檔名。這是第三個面向:
# 「無副檔名的檔案一律視為原始碼」會讓 Makefile 與 LICENSE 落在同一類 ——
# 前者會被建置工具消費、後者不會,單靠副檔名分不開,所以誠實開第三份。
NON_SOURCE_NAMES = {
    "LICENSE": "純文字授權書,不被執行也不被建置消費",
    "NOTICE": "純文字聲明,不被執行也不被建置消費",
    "AUTHORS": "純文字名單,不被執行也不被建置消費",
    ".gitignore": "版控忽略規則,只含路徑樣式,無可執行邏輯",
    ".dockerignore": "建置忽略規則,只含路徑樣式,無可執行邏輯",
    ".env": "環境變數值,被行程讀取但不含可執行邏輯",
}

CODE_IN_SPEC_RE = re.compile(r"```|^\s*(def|class|import|from|function|const|let)\s", re.M)


def exemption_hint(rel_path=None):
    """指出**該改的那一份**清單與該加的項目。

    三份全印出來的話,人得自己判斷該改哪一份 —— 那正好是這個訊息要省掉的認知成本。
    有副檔名就指副檔名清單,沒有就指檔名清單;判斷不出來才退回全印。
    """
    me = os.path.relpath(os.path.abspath(__file__), ROOT).replace("\\", "/")
    lines = {"NON_SOURCE_DIRS": "?", "NON_SOURCE_EXT": "?", "NON_SOURCE_NAMES": "?"}
    try:
        for i, line in enumerate(io.open(os.path.abspath(__file__), encoding="utf-8"), 1):
            for name in lines:
                if line.startswith(name) and lines[name] == "?":
                    lines[name] = i
    except Exception:
        pass

    if rel_path:
        base = os.path.basename(rel_path)
        ext = os.path.splitext(base)[1]
        if ext:
            return ("%s:%s 的 NON_SOURCE_EXT 加一筆 %r(附理由:為什麼它不會被執行"
                    "或被建置消費)" % (me, lines["NON_SOURCE_EXT"], ext))
        return ("%s:%s 的 NON_SOURCE_NAMES 加一筆 %r(附理由:為什麼它不會被執行"
                "或被建置消費)" % (me, lines["NON_SOURCE_NAMES"], base))

    return " / ".join("%s:%s 的 %s" % (me, lines[n], n) for n in lines)


def authoritative_layer(root=None):
    """權威層裝了沒。回傳 (installed, detail)。

    `.git/hooks/` 依 git 設計不進版控 —— clone 出來的副本上這一層不存在,
    而且**完全靜默**:前哨照跑、測試照綠,沒有東西會說它不在。
    F-009 的最終形式:規則存在,但整層沒被部署。

    判定看的是**內容**不是檔案存不存在:專案本來就可能有自己的 pre-commit,
    只驗檔案在不在的話,別人的 hook 佔著位子就會被判成已安裝。

    **這個偵測自己有涵蓋不到的地方,見 not_installed_notice()。**
    零接觸安裝不可能:git 刻意不讓 clone 自動執行任何東西。
    """
    r = root or ROOT
    hooks_dir = os.path.join(r, ".git", "hooks")
    try:
        p = subprocess.run(["git", "config", "--get", "core.hooksPath"],
                           cwd=r, capture_output=True)
        configured = p.stdout.decode("utf-8", "replace").strip()
        if p.returncode == 0 and configured:
            hooks_dir = configured if os.path.isabs(configured) else os.path.join(r, configured)
    except Exception:
        pass  # 讀不到就用預設位置查;查不到會判成沒裝 —— 吵鬧的方向

    hook = os.path.join(hooks_dir, "pre-commit")
    if not os.path.exists(hook):
        return False, "找不到 pre-commit(查過 %s)" % rel(hook)
    try:
        body = io.open(hook, encoding="utf-8", errors="replace").read()
    except Exception as e:
        return False, "pre-commit 讀不到(%s):%s" % (rel(hook), e)
    if "gate.py" not in body:
        return False, ("%s 存在,但它不呼叫 gate.py —— 那是別人的 hook 佔著位子,"
                       "不是本框架的權威層。" % rel(hook))
    return True, "%s 已呼叫 gate.py" % rel(hook)


def not_installed_notice(detail):
    """沒裝時要說的話 —— 含**它自己涵蓋不到什麼**。

    只說「沒裝,請裝」讀起來像裝了就全部關上了。實際上:
      前哨(隨 .claude/settings.json 走)只涵蓋 AI 路徑;
      測試(隨 tests/ 走)涵蓋所有人,但沒有機制強制它被跑(F-025)。
    兩者都碰不到「clone 下來直接手動 commit 的人」。那個缺口關不掉,明寫(docs/adr 票 05)。
    """
    return ("[權威層未安裝] %s\n"
            "     裝法:把 .git/hooks/pre-commit 指向 gate.py --pre-commit,\n"
            "     或 git config core.hooksPath <進版控的 hook 目錄>。\n"
            "     注意:本偵測只在 AI 走前哨、或有人跑測試時會出聲 ——\n"
            "     **clone 下來直接手動 commit 的人碰不到它**,那個缺口關不掉。" % detail)


def sentinel_footer():
    """前哨擋下訊息的結尾。

    原本無條件寫「權威判定在 pre-commit,繞過前哨仍會在 commit 被擋」——
    權威層不在時那是假的,而且是最糟的一種假:它讓人以為還有第二道。
    """
    installed, detail = authoritative_layer()
    if installed:
        return "(權威判定在 pre-commit,繞過前哨仍會在 commit 被擋)"
    return not_installed_notice(detail)


# ─────────────────────────────────────────────────────────────────────────────
# R7 —— Bash 寫入 repo 一律擋。**收口,不是擴涵蓋。**
#
# 不做「解析寫入目標」:heredoc 內文的路徑、sed -i、> 重導、tee、自己算路徑的腳本
# —— 解不完,而 **60% 有效的解析器比零涵蓋更危險**:零涵蓋你知道它是零,
# 60% 你會以為 Bash 被守住了。那是 R4 的形狀(讀起來在守,實際只守一部分,
# 而沒有東西告訴你是哪一部分)。
#
# 述詞只回答「有沒有在寫」,不回答「寫到哪」。判斷不出來就當作在寫。
# 所有寫入被逼回 Write/Edit,而那條路 R1–R6 已經守得住且驗過兩個環境。
#
# **殘留缺口(明寫)**:`python foo.py` 這種指令本身看不出在寫的仍然穿得過去。
# 不假裝擋得住 —— 那正是拒絕解析器的同一個理由。
# ─────────────────────────────────────────────────────────────────────────────

WRITE_CONSTRUCT = re.compile(
    r"(?:^|[\s;&|(])(?:tee|cp|mv|touch|mkdir|install|rm|rmdir|dd|truncate"
    r"|Set-Content|Add-Content|Out-File|New-Item|Clear-Content)(?:\s|$)"
    r"|(?<![0-9])>>?(?!&)"          # > 與 >>,但排除 2>&1 這種 fd 重導
    r"|<<"                          # heredoc
    r"|sed\s+(?:-[a-zA-Z]*\s+)*-i", re.IGNORECASE)

BASH_ALLOWED_CMDS = {
    "git": "版控自己的寫入(索引、工作區、.git),逼它走檔案工具沒有意義",
    "python -m pytest": "測試執行器產生 .dev/ 證據與 __pycache__,那是它的職責",
    "pytest": "同上",
    "pip": "套件管理器寫 .venv,不是本 repo 的來源",
    "python -m pip": "同上",
    "npx": "上游 skills 工具,唯一入口是 scripts/skills-update.sh",
    "bash scripts/skills-update.sh": "skills 更新的唯一入口,它自己會跑全規則驗證",
    "python .claude/": "閘門與可攜化工具自身(gate/redlight/install/verify_gates)",
}

BASH_ALLOWED_TARGETS = {
    "/dev/null": "丟棄輸出,不產生檔案",
    "/tmp/": "系統暫存,在 repo 之外",
    "scratchpad": "工作階段暫存目錄,在 repo 之外",
    ".dev/": "流程證據,由機制自己追加(append-only),不是人在編輯",
    "__pycache__": "位元碼,由直譯器產生",
    ".cache/": "快取,可重算",
    "build/": "建置產出物,不是來源",
}


def bash_write_violation(command):
    """R7:這個 Bash 指令會不會寫入 repo。回 None(放行)或訊息。"""
    if not command or not command.strip():
        return None
    cmd = command.strip()

    # 逐段比對:`a && b` 的每一段都要在許可清單裡才算數,
    # 否則 `git status && rm -rf x` 會整條被許可。
    segments = [s.strip() for s in re.split(r"&&|\|\||;", cmd) if s.strip()]
    if segments and all(
            any(seg.startswith(p) for p in BASH_ALLOWED_CMDS) for seg in segments):
        return None

    if not WRITE_CONSTRUCT.search(cmd):
        return None

    # 「確定在 repo 外」與「不知道寫到哪」是兩件事:前者可以放行(repo 外是 G1 的事),
    # 後者必須擋。只放行前者。
    for target, _why in BASH_ALLOWED_TARGETS.items():
        if target in cmd:
            return None

    return ("[R7] 這個 Bash 指令會寫入檔案,請改用 Write / Edit。\n"
            "     理由不是風格:從指令字串解析『寫到哪』解不完,而半套的解析器\n"
            "     比零涵蓋更危險 —— 零涵蓋你知道它是零。所以入口收成一個,\n"
            "     走檔案工具的話 R1–R6 全部適用。\n"
            "     例外(附理由)在 gate.py 的 BASH_ALLOWED_CMDS / BASH_ALLOWED_TARGETS。")


RESEARCH_ROOT = "research"


def _under_research(rel_path):
    """這個路徑在不在 research/ 底下。**邊界比對,不是前綴**(F-051):
    `research/x` 算,`research_utils/x` 不算。"""
    r = rel_path.replace("\\", "/")
    return r == RESEARCH_ROOT or r.startswith(RESEARCH_ROOT + "/")


def parses_as_python(content):
    """這段內容是不是合法 Python。

    `imports_research()` 對解析失敗一律回 True(fail-closed),那個方向是對的,
    但**它讓兩件事說不出差別**:「你 import 了 research」與「我看不懂這段碼」。
    擋下時把後者說成前者,會讓人去檢查一個根本沒問題的地方 ——
    誤導的訊息比沒有訊息貴,那是票 07 列的第一項代價。
    """
    try:
        ast.parse(content or "")
        return True
    except Exception:
        return False


def imports_research(content):
    """這段 Python 有沒有 import research/(頂層套件 `research`)。

    用 AST,不用字串比對 —— 字串比對分不開 `import research` 與 `import research_utils`,
    而那正是 F-051 的邊界問題。AST 給的是模組名,取頂層套件精確比對。

    **fail-closed**:解析不了(語法壞掉)一律當作**可能 import 了** ——
    「我看不懂這段碼」不能翻譯成「它沒 import research」(R8 是擋東西的規則,
    看不懂時只能更嚴)。
    """
    try:
        tree = ast.parse(content or "")
    except Exception:
        return True
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] == RESEARCH_ROOT:
                    return True
        elif isinstance(node, ast.ImportFrom):
            # from research / from research.x import ...；相對 import(module=None)不算
            if node.module and node.module.split(".")[0] == RESEARCH_ROOT:
                return True
    return False


# 解碼順序。`latin-1` 永不失敗,所以最後一關保證有東西可判。
# 要找的東西(import 敘述、code 圍籬)全是 ASCII,亂碼不影響它們的可見性。
TEXT_ENCODINGS = ("utf-8-sig", "utf-8", "cp950", "cp1252", "latin-1")


def read_text_or_none(abs_path):
    """讀成文字:**先拿位元組,再依序解碼**。

    只用 `io.open(..., encoding="utf-8")` 的話,zh-TW Windows 上以 cp950 存的 .py
    會丟 UnicodeDecodeError,而上游把它接成「跳過」或「空字串」——
    **整支檔案對規則隱形**。cp950 是那台機器的預設編碼,不是假想情況。
    F-042 / F-064 是同一個編碼假設的前幾次現身,這是同一家族。

    連位元組都拿不到(權限、路徑不存在)回傳 None —— 那是「**這個問題沒有答案**」,
    呼叫端必須 fail-closed。不得翻譯成「檔案是空的」:空檔案什麼都沒 import,
    而那正好是最鬆的答案。
    """
    try:
        with io.open(abs_path, "rb") as f:
            raw = f.read()
    except Exception:
        return None
    for enc in TEXT_ENCODINGS:
        try:
            return raw.decode(enc)
        except Exception:
            continue
    return raw.decode("latin-1", "replace")


def content_after_edit(path, tool_input):
    """這次寫入之後,檔案**會有的內容**。算不出來時回傳 None。

    規則問的是「檔案最終內容」的性質,而 Edit 的 `new_string` 是**片段**。
    片段的語法完整性跟那個問題沒有任何關係:函式內部每一行都是縮排的,
    所以「改一個函式裡的一行」在 .py 上幾乎必然 IndentationError,
    再乘上 `imports_research()` 的 fail-closed,得到的判定是
    **「片段不是合法 Python」⇒「它 import 了 research」**(票 07 / F-046)。

    **fail-closed 只保證失敗的方向,不保證問對了問題。**

    回傳 None 的語意是「算不出結果」,不是「沒事」:呼叫端退回磁碟現況,
    而磁碟也讀不到時各規則自己 fail-closed。**不得退回片段** ——
    退回片段就是把這個缺陷原地保留。

    套不上(anchor 不符或不唯一)也回 None:那次編輯本來就會失敗,
    不是規則該處理的情況。
    """
    ti = tool_input or {}
    if ti.get("content") is not None:
        return ti["content"]                      # Write:本來就是整檔內容

    edits = ti.get("edits")                       # MultiEdit
    if not isinstance(edits, list):
        if ti.get("new_string") is None:
            return None                           # 不是編輯形狀(NotebookEdit 等)
        edits = [ti]                              # Edit

    body = read_text_or_none(os.path.abspath(path))
    if body is None:
        return None
    for e in edits:
        if not isinstance(e, dict):
            return None
        old, new = e.get("old_string"), e.get("new_string")
        if old is None or new is None or old == "" or old not in body:
            return None
        body = (body.replace(old, new) if e.get("replace_all")
                else body.replace(old, new, 1))
    return body


RULE_CODE_RE = re.compile(r"\[(R\d+)(?:/[^\]]*)?\]")


def rule_codes(source_path=None):
    """本檔目前定義了哪些規則 —— 從**規則自己的擋下訊息**掃出來。

    不維護對照表:任何寫死條數或列表的驗收條件,下次加規則時不會有人記得改,
    而漏掉的那條不會有任何東西出聲。規則代號本來就寫在它自己的訊息裡,
    那是現場已有的事實,不必另外登記一份。

    `[R2/commit]` 這種帶子類的歸到 R2 —— 子類是同一條規則的不同時點,不是新規則。
    """
    path = source_path or os.path.abspath(__file__)
    try:
        with io.open(path, encoding="utf-8") as f:
            return set(RULE_CODE_RE.findall(f.read()))
    except Exception:
        return set()


def _err(msg):
    """把訊息寫進 stderr,**明確用 utf-8**。

    直接 `sys.stderr.write` 會用主控台編碼,中文擋下訊息在 cp950 終端機上
    變成亂碼 —— 一個讀不懂的擋下訊息,人會照著繞而不是照著修,
    那跟沒有訊息差不多(F-031:壞掉的訊號訓練人忽略訊號)。
    """
    try:
        sys.stderr.buffer.write(msg.encode("utf-8"))
        sys.stderr.buffer.flush()
    except Exception:
        sys.stderr.write(msg)


def rel(path):
    try:
        return os.path.relpath(os.path.abspath(path), ROOT).replace("\\", "/")
    except ValueError:
        return path.replace("\\", "/")


def load_stage_defs():
    """讀唯讀定義檔。回傳 (stages, flow, err)。

    **fail-closed**:讀不到、格式壞掉、或沒有任何站宣告 allows_src_write 時,
    回傳 err 且 stages 為空 —— 呼叫端一律不放行原始碼寫入。
    閘門壞掉時必須更嚴不能更鬆,否則比沒有閘門危險(你會以為它在守)。
    """
    rel_def = os.path.relpath(STAGES_DEF, ROOT).replace("\\", "/")
    try:
        import yaml
    except Exception as e:
        return [], "", "無法載入 yaml 套件(%s)" % e
    if not os.path.exists(STAGES_DEF):
        return [], "", "定義檔不存在:%s" % rel_def
    try:
        with io.open(STAGES_DEF, encoding="utf-8") as f:
            doc = yaml.safe_load(f)
    except Exception as e:
        return [], "", "定義檔解析失敗:%s(%s)" % (rel_def, e)
    if not isinstance(doc, dict) or not isinstance(doc.get("stages"), list) or not doc["stages"]:
        return [], "", "定義檔缺少有效的 stages 清單:%s" % rel_def
    stages = doc["stages"]
    if not all(isinstance(s, dict) and s.get("id") for s in stages):
        return [], "", "定義檔的 stages 項目缺少 id:%s" % rel_def
    if not any(s.get("allows_src_write") for s in stages):
        return [], "", "定義檔沒有任何站宣告 allows_src_write:%s" % rel_def
    flow = " -> ".join("/%s" % s["skill"] for s in stages if s.get("skill"))
    return stages, flow, None


UNREADABLE_STAGE = "__unreadable__"


def parse_hook_payload(raw):
    """把 PreToolUse 的原始位元組解成 payload。**明確 utf-8,失敗就丟例外。**

    這不是接線,是**解碼 + 解析**,所以它有測試(tests/test_gate_boundaries.py)。
    先前被歸類為「進入點分派,不測」,而那條接線裡藏著整個系統最要命的一行:
    `json.load(sys.stdin)` 用平台預設編碼解 UTF-8 payload,中文路徑當場壞掉,
    例外被 `except: return 0` 吞成放行,前哨層整輪靜默失效(F-042)。

    **判準:進入點若包含解碼、解析、格式轉換,它就不是接線。**
    接線是把 A 傳給 B;一旦中間有轉換,它就是有行為的程式碼。
    """
    return json.loads(raw.decode("utf-8"))


def load_stage():
    """讀執行期狀態。current_stage 為權威欄位。

    讀不到時回 UNREADABLE_STAGE,**不回 "idle"**。
    回 idle 的話:寫入時 idle 不可寫 → 擋下(看起來沒問題),
    但**提交時 idle 是刻意放行的**(ADR 0005),於是 pipeline.json 壞掉或被刪,
    R2 在提交時就無條件通過。「不知道停在哪一站」不等於「停在 idle」。
    """
    try:
        with io.open(PIPELINE, encoding="utf-8") as f:
            d = json.load(f)
        return d.get("current_stage", "idle"), d.get("ticket_id")
    except Exception:
        return UNREADABLE_STAGE, None


def load_feature():
    try:
        with io.open(PIPELINE, encoding="utf-8") as f:
            return json.load(f).get("feature")
    except Exception:
        return None


def ticket_untested_modules(feature, ticket_id):
    """讀票裡「**Untested by decision:**」宣告的模組名。

    豁免不是 gate.py 自己開的後門 —— 它去讀一個**前一站產物裡已經存在的決定**。
    要新增豁免必須回頭改票,那是看得見、會被審查的動作;
    在被擋住的當下加豁免會留下票的修改痕跡,對得起來。
    宣告不存在 = 不豁免(fail-closed)。
    """
    if not feature or not ticket_id:
        return set(), None
    d = os.path.join(ROOT, ".scratch", feature, "issues")
    if not os.path.isdir(d):
        return set(), None
    for name in sorted(os.listdir(d)):
        if not name.startswith(str(ticket_id)):
            continue
        p = os.path.join(d, name)
        try:
            for line in io.open(p, encoding="utf-8"):
                if line.startswith("**Untested by decision:**"):
                    raw = line.split(":**", 1)[1]
                    mods = {m.strip() for m in raw.replace("、", ",").split(",") if m.strip()}
                    return mods, ".scratch/%s/issues/%s" % (feature, name)
        except Exception:
            return set(), None
        return set(), ".scratch/%s/issues/%s" % (feature, name)
    return set(), None


def logged_exemption_backed(rel_path, base):
    """commit 時 ticket_id 已清空(一輪做完站別會往前走),改查豁免紀錄。

    但**不採信紀錄本身** —— 回頭打開它指名的票,確認那張票真的列了這個模組。
    紀錄只是索引,票才是決定。這樣偽造一行紀錄沒有用,票對不上就擋。
    """
    log = os.path.join(ROOT, ".dev", "gate-exemptions.jsonl")
    if not os.path.exists(log):
        return False
    for line in io.open(log, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        if rec.get("file") != rel_path or rec.get("module") != base:
            continue
        p = os.path.join(ROOT, (rec.get("declared_in") or "").replace("/", os.sep))
        if not os.path.exists(p):
            continue
        for l in io.open(p, encoding="utf-8"):
            if l.startswith("**Untested by decision:**"):
                mods = {m.strip() for m in
                        l.split(":**", 1)[1].replace("、", ",").split(",") if m.strip()}
                if base in mods:
                    return True
    return False


def check_legacy_list():
    """權威層規則:凍結清單裡每一筆都必須在 LEGACY_GO_LIVE 的樹裡。

    沒有這條的話,清單檔本身落在 .agents/(非原始碼)、沒有任何規則守它,
    被 R3 擋下的人只要在末尾加一行就豁免到手 —— 完全不必碰 git 歷史,
    而「無法自我服務」正是選這個設計的**唯一**理由。
    「有一條測試會抓到」不算守住:沒有機制強制那條測試被跑。

    與 R4/R5 同構,回傳違規訊息串列。**fail-closed**:清單讀不到算違規。
    """
    if not os.path.exists(LEGACY_LIST):
        return ["[R6] 找不到豁免清單 %s —— 讀不到一律當違規,不當作乾淨。" % rel(LEGACY_LIST)]
    go_live = read_go_live()
    if not go_live:
        return ["[R6] %s 沒有 go-live sha(第一行應為 `# go-live: <sha>`)。\n"
                "     讀不到基準點就無從驗證清單 —— 不是「沒基準所以都算過」。"
                % rel(LEGACY_LIST)]
    out = []
    for p in sorted(legacy_no_redlight()):
        try:
            rc = subprocess.call(["git", "cat-file", "-e", "%s:%s" % (go_live, p)],
                                 cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            return ["[R6] 無法查驗豁免清單(%s)—— 查不動一律當違規。" % e]
        if rc != 0:
            out.append("[R6] %s 不在機制上線 commit %s 的樹裡,不得列入紅燈豁免清單。\n"
                       "     清單只減不增:新檔案要走紅燈,不是往豁免名單裡加。"
                       % (p, go_live[:7]))
    return out


_REDLIGHT_MOD = []


def _redlight():
    """載入同目錄的 redlight.py。**用路徑載入,不用 `import redlight`。**

    gate.py 被測試以 spec_from_file_location 載入時,`.claude/hooks/` 不在
    sys.path 上,`import redlight` 會 ImportError —— 而那個失敗會讓
    head_content_hash 一律回 None,於是既有檔案那條路徑**永遠不合格**,
    規則看起來還在、實際上退回修改前的行為。靜默,而且測試環境與正式環境不同調。
    """
    if _REDLIGHT_MOD:
        return _REDLIGHT_MOD[0]
    import importlib.util
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "redlight.py")
    spec = importlib.util.spec_from_file_location("_redlight_for_gate", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _REDLIGHT_MOD.append(mod)
    return mod


def head_content_hash(rel_path):
    """這支檔案**在 HEAD 的內容**的雜湊。不在 HEAD 或問不到時回 None。

    錨定 HEAD 而不是磁碟現況,是因為判準必須**時點不變**:
    前哨評估時檔案還沒被寫,提交時已經被寫 —— 拿磁碟現況當錨,同一條紀錄
    在兩個時點會得到相反的答案,而權威層比前哨鬆就是缺陷(F-017 的形狀)。
    HEAD 在這兩個時點都沒動。

    回 None 一律由呼叫端當作「不合格」處理(fail-closed),不區分
    「不在 HEAD」與「git 壞掉」—— 兩者都代表這個問題沒有答案。
    """
    try:
        out = subprocess.run(["git", "cat-file", "blob", "HEAD:" + rel_path],
                             cwd=ROOT, capture_output=True)
    except Exception:
        return None
    if out.returncode != 0:
        return None                      # 不在 HEAD(新建未提交)或 git 不可用
    try:
        return _redlight().content_hash(out.stdout)   # 雜湊定義只有一份(F-058)
    except Exception:
        return None


def redlight_missing(base, also_accept=(), impl_rel=None, ticket=None):
    """R3 的另一半:這個模組的測試曾經在**這次的實作寫之前**紅過嗎?

    also_accept:除 tests/test_<base>.py 外同樣算數的測試檔位置。兩半必須接受
    同一組位置 —— 只認 tests/ 的話,pkg/foo.py 配 pkg/test_foo.py 會通過前半、
    卡死後半,而且沒有任何合法解法。

    回 None 表示有合格紀錄;回訊息表示沒有 —— 呼叫端據此擋下。

    **判定的對象是「實作」,不是「檔案」。** 原本只認 `impl_exists is False`,
    那量的是「這個**檔案**當時存不存在」。新檔案兩者重合,既有檔案永遠分岔:
    檔案還在就永遠產不出那種紀錄,於是每一支既有 .py 的紅燈先行**在機制上
    寫不出來**,唯一出口是 legacy 豁免清單 —— 也就是把 R3 從最需要它的檔案上
    整條移開。這與 F-046 是同一個形狀(fail-closed 的方向對了,判定的對象錯了)。

    合格紀錄 = 紅燈 **且** 屬於當前這張票 **且**(實作當時不存在
    **或** 紅燈是對著這支檔案在 HEAD 的內容發生的)。

      - 票號:每張票要有自己的紅燈。少了它,一筆舊紅燈只要該檔案之後沒被提交過
        就永久解鎖後續每一次修改 —— 方向會從「永遠不合格」翻成「永遠合格」。
      - HEAD 雜湊:證明紅燈發生在改動**之前**。先寫實作再補跑紅燈的話,
        那筆紀錄的 impl_hash 是改動後的內容,對不上 HEAD,擋 ——
        這是本判準唯一可能被自我服務的路徑,而它被關住了。

    `ticket` 為 None 時**不比對票號**(提交時票號已清空,見 RULE_DIVERGENCE["R3"])。
    此時 HEAD 雜湊這一半照常成立,實質保證不變,少的只是票號歸屬。

    判準仍然不比較任何時間戳。

    **全程 fail-closed**:紀錄檔不存在、讀不動、格式不對、欄位缺漏,一律當作沒有紀錄。
    讀不到就放行是 F-001 的形狀,在這裡不重演。
    """
    wanted = {"tests/test_%s.py" % base} | {p.replace("\\", "/") for p in also_accept}
    want = "tests/test_%s.py" % base
    if not os.path.exists(RUN_LOG):
        return ("找不到紅燈紀錄檔 %s —— 無法證明測試曾經紅過。\n"
                "     跑一次測試讓紀錄長出來;讀不到紀錄一律不放行。"
                % rel(RUN_LOG))

    # 只算一次:HEAD 內容與這一輪的每一筆紀錄比對,與紀錄無關。
    head = head_content_hash(impl_rel) if impl_rel else None

    saw_any = False
    saw_ticket_mismatch = False
    try:
        for line in io.open(RUN_LOG, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)          # 壞行 -> 例外 -> fail-closed
            if rec.get("test_file") not in wanted:
                continue
            saw_any = True
            if "impl_exists" not in rec:    # 欄位缺漏也算格式不對
                return ("紅燈紀錄缺 impl_exists 欄位(%s),格式不對即不放行。" % want)
            if rec.get("result") != "red":
                continue
            if ticket is not None and rec.get("ticket_id") != ticket:
                saw_ticket_mismatch = True
                continue
            if rec["impl_exists"] is False:
                return None                 # 新檔案:紅燈時實作不存在
            if head is not None and rec.get("impl_hash") == head:
                return None                 # 既有檔案:紅燈對著改動前的碼發生
    except Exception as e:
        return ("紅燈紀錄無法解析(%s):%s —— 格式不對一律不放行。" % (rel(RUN_LOG), e))

    if saw_ticket_mismatch:
        return ("%s 有紅燈紀錄,但沒有一筆屬於當前票 %s。\n"
                "     舊票的紅燈不解鎖後續修改 —— 每張票要有自己的紅燈。"
                % (want, ticket))
    if saw_any:
        return ("%s 有執行紀錄,但沒有任何一筆是「紅燈,且發生在這次改動之前」。\n"
                "     合格的形狀:實作當時不存在,或紅燈是對著這支檔案在 HEAD 的\n"
                "     內容跑出來的。先寫實作再補跑紅燈不算 —— 那是補測試,不是紅綠燈。"
                % want)
    return ("%s 沒有任何執行紀錄 —— 無法證明它曾經紅過。" % want)


def is_source_path(rel_path):
    """這個路徑是不是 R2/R3 的對象。黑名單反轉後的唯一判定點。

    抽成函式不只為了可讀:豁免清單要能斷言「裡面每一項本來都會被 R3 管」,
    而那個斷言若在測試裡自帶一份判定邏輯,測的就是它自己的副本(ADR 0003)。
    """
    r = rel_path.replace("\\", "/")
    top = r.split("/")[0] if "/" in r else ""
    return not (top in NON_SOURCE_DIRS
                or PROTOTYPE_RE.match(r)
                or r.endswith(tuple(NON_SOURCE_EXT))
                or os.path.basename(r) in NON_SOURCE_NAMES)


def legacy_no_redlight():
    """機制上線前就存在、因此無法誠實提供紅燈紀錄的既有 .py。

    豁免的只有 R3 的**後半**(紅燈紀錄);前半(對應測試檔須存在)照常適用。

    為什麼不是「檔案已存在就豁免」:那個條件 **agent 隨時可以自己製造** ——
    建一個空檔,下一次寫入就成了「既有檔案」,規則自帶開關。
    凍結清單則進不去:每一項都必須在 LEGACY_GO_LIVE 的樹裡找得到(測試守住),
    偽造需要改寫歷史。同一個原則的第三次出現(閘門自我修改、票宣告接縫、本清單)。

    **fail-closed**:清單讀不到 = 沒有任何豁免,不是全部豁免。
    """
    out = set()
    try:
        for line in io.open(LEGACY_LIST, encoding="utf-8"):
            line = line.split("#", 1)[0].strip()
            if line:
                out.add(line.replace("\\", "/"))
    except Exception:
        return set()
    return out


def is_bare_package_marker(rel_path, content):
    """__init__.py 且不含任何 def/class —— 純套件標記,沒有行為可測。

    放進去任何邏輯就不再是標記,R3 立刻恢復適用(fail-closed)。
    """
    if os.path.basename(rel_path) != "__init__.py":
        return False
    body = content
    if body is None:
        try:
            body = io.open(os.path.join(ROOT, rel_path), encoding="utf-8").read()
        except Exception:
            return False
    return not re.search(r"^\s*(def|class)\s", body or "", re.M)


def note_exemption(bucket, path, base, ticket, declared_in,
                   reason="ticket-declared"):
    """把「這次判定用到了一個豁免」收進 bucket。**不寫檔。**

    原本這裡直接寫帳本,而且寫在**判決之前** —— 於是:
      - 被後面的規則擋下的嘗試照樣記一筆(沒有人走成後門,帳上卻有一筆)
      - `check()` 有了副作用,**跑一次測試就多一筆**(測試自己會呼叫它)
    兩者相乘,19 筆 gate-self 對上零位元組變更。帳本從頭到尾沒觀測過任何寫入。

    判定與記錄因此分家:`check()` 只回答問題,強制點(mode_hook /
    mode_pre_commit)才知道「真的有人要寫」,記錄屬於那裡(票 08)。
    """
    if bucket is None:
        return
    bucket.append({"file": path, "module": base, "ticket": ticket,
                   "declared_in": declared_in, "reason": reason})


def _hash_bytes(raw):
    """與紅燈紀錄同一個雜湊定義(行尾正規化),兩邊才比得起來(F-058)。"""
    try:
        return _redlight().content_hash(raw)
    except Exception:
        return None


def exemption_record(ex, verdict, at_commit, stage, ticket, content, tool=None):
    """組出一筆帳本紀錄。

    `outcome` 把「豁免真的被用掉」與「嘗試被後面的規則擋下」分開 ——
    ADR 0004 的「某一輪十筆就是把後門當日常通道」只該算 granted。

    `changes_bytes` 回答本票的原始問題:19 筆豁免對上零位元組變更。
    **None 不是 False** —— None 是「不知道有沒有變」(提交時、或 anchor 套不上,
    算不出結果內容),False 是「確定沒變」。把前者寫成後者,對帳會看到
    一串「都沒改」而其實是「都不知道」。
    """
    before = None
    try:
        with io.open(os.path.join(ROOT, ex["file"]), "rb") as f:
            before = _hash_bytes(f.read())
    except Exception:
        before = None
    after = _hash_bytes(content.encode("utf-8")) if content is not None else None
    changed = None if (before is None or after is None) else (before != after)
    return {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "file": ex["file"], "module": ex["module"],
        "ticket": ex.get("ticket") if ex.get("ticket") is not None else ticket,
        "stage": stage,
        "declared_in": ex["declared_in"], "reason": ex["reason"],
        # gate.py 不看 tool_name(判定一律 fail-closed,不退回白名單),
        # 擋住 Read 的只有 settings.json 的 matcher。帳本要說得出來源,
        # 否則「有幾筆」又是一個解釋不了的數字。
        "tool": tool,
        "outcome": "blocked" if verdict else "granted",
        "blocked_by": rule_of(verdict) if verdict else None,
        "at_commit": bool(at_commit),
        "content_hash": before, "result_hash": after, "changes_bytes": changed,
    }


def log_exemptions(bucket, verdict, at_commit, content=None, tool=None):
    """在**強制點**把這一次判定用到的豁免寫進帳本。

    記錄失敗仍然 fail-closed:豁免的正當性建立在「它被記錄下來、可被逐筆對帳」
    上面(ADR 0004/0006)。記不下來還照給,等於給了一個沒有人看得到的豁免。
    """
    if not bucket:
        return
    stage, ticket = load_stage()
    for ex in bucket:
        rec = exemption_record(ex, verdict, at_commit, stage, ticket, content,
                               tool=tool)
        try:
            _append_jsonl(EXEMPTION_LOG, rec)
        except Exception as e:
            _err("[閘門/fail-closed] 豁免無法記帳(%s):%s\n"
                 "     記不下來的豁免不算數 —— 對帳看不到它,等於它沒發生過。\n"
                 % (rel(EXEMPTION_LOG), e))
            raise SystemExit(2)


def _append_jsonl(path, rec):
    """追加一筆 JSON Lines。抽成函式是為了讓「寫入失敗」可以被測試注入。"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def self_modification_note(rel_path):
    """閘門自我修改的豁免說明。靜默的洞比會叫的洞危險(F-011 的教訓)。"""
    if rel_path not in GATE_SELF:
        return None
    return ("[R2/自我修改豁免] %s:閘門自身,不受站別限制 —— 已記錄。\n"
            "     理由:閘門把站別卡住時,修法需要改本檔;R2 管到它就把人鎖在外面(docs/adr/0004)。\n"
            "     R3 沒有例外:寫測試不需要先解鎖任何東西。" % rel_path)


def check(path, content, at_commit=False, trace=None, exemptions=None):
    """回傳 None(放行)或違規訊息字串。content 為 None 時從磁碟讀。

    **本函式是純判定,不寫任何檔案。** 用到的豁免收進 `exemptions`(呼叫端傳入的
    串列),由強制點決定要不要記帳 —— 因為只有強制點知道「真的有人要寫」。
    原本這裡直接寫帳本,於是跑一次測試就多一筆豁免紀錄(票 08)。

    at_commit 改變 R2 的問題,不是放寬它:
      寫入時問「現在這一站可以寫原始碼嗎」—— 防的是還沒談清楚就開始寫。
      commit 時問「你是不是還停在前置站就在交原始碼」—— 實作做完後站別本來就會
      往 review / idle 走,拿寫入時的問題去問 commit 會擋掉每一次合法提交。
    """
    r = rel(path)

    # **repo 以外的路徑不歸這裡管。**
    # 六站流程規則管的是這個 repo。`rel()` 對外部檔案會產生 `../../..` 開頭的路徑,
    # 而 `is_source_path` 看到 top 是 `..`(不在非原始碼清單裡)就判成原始碼 ——
    # 於是編輯 `~/.claude/` 底下任何 .py 都被 R2 誤擋。誤擋面積大到會讓人關掉整個 hook,
    # 而關掉的涵蓋率是零(F-031)。repo 外的破壞性動作由 G1 負責,不是這條規則的職責。
    if r == ".." or r.startswith("../"):
        return None

    # R1 規格書禁止夾程式碼
    # 兩個路徑都算規格書:docs/specs/(自維護時期)與 .scratch/<feature>/spec.md
    # (官方 local-markdown issue tracker 的規定位置)。只守前者的話 R1 在官方佈局下是死規則。
    if r.startswith("docs/specs/") or re.match(r"^\.scratch/[^/]+/spec\.md$", r):
        if trace is not None:
            trace.append("R1")
        body = content
        if body is None:
            try:
                with io.open(os.path.join(ROOT, r), encoding="utf-8") as f:
                    body = f.read()
            except Exception as e:
                # 讀不到內容 = 「規格書裡有沒有程式碼」這個問題**沒被回答**,
                # 而沒被回答不等於答案是「沒有」。原本這裡 return None(放行)。
                return ("[R1/fail-closed] %s:讀不到內容(%s),無法判定規格書裡有沒有程式碼。\n"
                        "     閘門壞掉時只能更嚴,不能更鬆。" % (r, e))
        if CODE_IN_SPEC_RE.search(body or ""):
            return ("[R1] %s:規格書禁止含程式碼。spec 站只描述『要解決什麼問題』與"
                    "『怎樣算做完』,請移除 code 圍籬 / def / import / function。" % r)
        return None

    if not is_source_path(r):
        return None

    if trace is not None:
        trace.append("R2")

    stage, ticket = load_stage()
    stages, flow, defs_err = load_stage_defs()

    # 閘門自身:R2 豁免(死鎖),R3 不豁免。放行但**不靜默** —— 記帳並回報。
    gate_self = r in GATE_SELF
    if gate_self:
        note_exemption(exemptions, r, os.path.splitext(os.path.basename(r))[0],
                       ticket, "docs/adr/0004-gate-self-modification.md",
                       reason="gate-self-modification")
        _err(self_modification_note(r) + "\n")

    # R2-fc fail-closed:定義讀不到就不知道哪站可寫 —— 一律不放行
    if defs_err and not gate_self:
        return ("[R2/fail-closed] %s:站別定義不可用,原始碼寫入一律擋下。\n"
                "     原因:%s\n"
                "     閘門壞掉時只能更嚴,不能更鬆。修好定義檔後再寫。" % (r, defs_err))

    # 站別讀不到 -> 兩個時點都擋。這是唯一與時點無關的 R2 分支:
    # 「你停在哪一站」這個問題本身沒有答案時,兩種問法都答不出來。
    if stage == UNREADABLE_STAGE and not gate_self:
        return ("[R2/fail-closed] %s:讀不到流程狀態(%s)。\n"
                "     不知道停在哪一站,不等於停在 idle —— 後者在提交時是放行的。\n"
                "     修好 pipeline.json 再繼續。" % (r, rel(PIPELINE)))

    writable = {s["id"] for s in stages if s.get("allows_src_write")}

    # 路徑範圍寫入(research 站):allows_src_write 綁**路徑**不綁階段。
    # 宣告了 src_write_scope 的站,只能寫該範圍底下 —— 範圍外一律擋,不分時點。
    # agent 能自己寫 pipeline.json 宣告階段,所以把豁免爆炸半徑縮到零:
    # 不管誰宣告 research,都寫不了生產碼。
    stage_def = next((s for s in stages if s.get("id") == stage), None)
    scope = stage_def.get("src_write_scope") if stage_def else None
    if scope and not gate_self:
        sc = scope.rstrip("/")
        if not (r == sc or r.startswith(sc + "/")):
            return ("[R2/範圍] %s:current_stage='%s' 只能寫 %s 底下的原始碼。\n"
                    "     這是探索區,寫不了生產碼 —— 要進生產,把檔案**移出** %s,\n"
                    "     那是必須走六站的事件(不是第三條出口)。" % (r, stage, scope, scope))
        # 範圍內:R2 放行(research 本來就在 writable 集合裡,下面的檢查會過),落到 R3

    if gate_self:
        pass  # R2 豁免已在上面記帳並回報;R3 在下方照常適用
    elif at_commit:
        # 前置站 = 第一個可寫站之前的所有站。停在那裡卻在交原始碼,代表寫在該寫之前。
        ids = [s["id"] for s in stages]
        first_writable = next((i for i, s in enumerate(stages) if s.get("allows_src_write")), len(ids))
        pre_implement = set(ids[:first_writable]) - {"idle"}
        if stage in pre_implement:
            return ("[R2/commit] %s:current_stage='%s' 是前置站,卻要提交原始碼。\n"
                    "     代表這些碼寫在該寫之前。回頭把流程走完,或由使用者調整 current_stage。"
                    % (r, stage))
        # 這裡不可 return —— 只有 R2 的問法要換,R3 在 commit 時同樣要驗,
        # 而且權威層更該驗。早一版寫成 return None,等於把 R3 在 commit 時整個跳過。

    # R2 只有宣告 allows_src_write 的站能寫原始碼(站名定義來自 pipeline-stages.yaml)
    elif stage not in writable:
        return ("[R2] %s:目前 current_stage='%s',不可寫入原始碼"
                "(可寫入的站:%s)。\n"
                "     流程 %s\n"
                "     站名定義:.agents/pipeline-stages.yaml(唯讀)\n"
                "     跳過流程請由使用者自行修改 .dev/pipeline.json 的 current_stage\n"
                "     若這不是原始碼(誤擋):把它的目錄加進 %s;\n"
                "     **不得退回白名單** —— 三次 fail-open 缺陷都源自白名單思維(docs/adr/0003)"
                % (r, stage, "/".join(sorted(writable)) or "(無)", flow, exemption_hint(r)))

    # R3 對應測試檔須先存在
    if r.endswith(".py"):
        # trace 的語意是「這條規則的職責範圍被進入」,不是「它做出了判決」。
        # 記錄點必須在判定之前 —— 跳過判定就等於跳過記錄,偵測「規則被跳過」的
        # 機制自己會被同一個跳過略過。
        if trace is not None:
            trace.append("R3")
            trace.append("R8")

        # R8:生產程式碼(非 research/)不得 import research/。
        # 反方向放行(research 可 import 生產資料層),所以只擋生產這一側。
        # **邊界比對**:研究套件是 `research`,不是 `research_utils`(F-051,在 imports_research 裡)。
        if not _under_research(r):
            # 判定對象是**套用編輯後的整檔結果**,不是編輯片段(票 07 / F-046)。
            # content 為 None = 呼叫端算不出結果(提交時、或 anchor 套不上),
            # 退回磁碟現況;連磁碟都讀不到才是真的沒有答案。
            body = content
            if body is None:
                body = read_text_or_none(os.path.join(ROOT, r))
            if body is None:
                # 原本這裡是 `body = ""` —— 讀不到被翻譯成「檔案是空的」,
                # 而空檔案什麼都沒 import,正好是最鬆的答案:一個靜默的 fail-open。
                # 訊息要說「讀不到」,不是「你 import 了 research」:
                # 誤導的訊息比沒有訊息貴,它讓人去檢查一個根本沒問題的地方。
                return ("[R8/fail-closed] %s:讀不到內容,無法判定它有沒有 import research/。\n"
                        "     閘門壞掉時只能更嚴,不能更鬆。" % r)
            if not parses_as_python(body):
                # 擋,但說對原因。fail-closed 的方向不變,變的是它承認自己
                # 看不懂 —— 而不是把「看不懂」講成「你 import 了 research」。
                return ("[R8/fail-closed] %s:編輯後的結果不是合法 Python,"
                        "無法判定它有沒有 import research/。\n"
                        "     先把語法修好 —— 這不是 import 違規,是這一份結果本身解不開。\n"
                        "     (看不懂這段碼時閘門只能更嚴,不能更鬆。)" % r)
            if imports_research(body):
                return ("[R8] %s:生產程式碼不得 import research/。\n"
                        "     research/ 是探索區,可以被丟棄;生產碼依賴它,"
                        "研究一被殺掉生產就壞。\n"
                        "     反方向可以:research/ 底下的碼 import 生產資料層是允許的。\n"
                        "     要用到某段研究成果,把它移出 research/ 走六站,不是 import 它。"
                        % r)

        # legacy 清單:早於閘門的既有碼,豁免 R3 **整條**(兩半)。
        # 只豁免紅燈半的話,測試檔存在半照樣擋光既有碼 —— 一個 121 個檔案、
        # 0 個測試的既有 repo 裝上閘門後,每個既有檔案一被編輯就被 R3 第一半擋死,
        # 而 legacy 清單救不了(它豁免的不是那一半)。那讓清單在無測試的既有 repo
        # 幾乎是廢的(docs/adr/0006 的語意更新)。
        # 出口不變:補測試 → 從清單移除(R6 守著只減不增與刪檔排水);新檔案不受影響
        # (它不在凍結清單裡,入場券是「在上線 commit 的樹裡」,偽造不了)。
        # 放在 R8 之後:既有檔案被改成 import research 仍要被 R8 擋,legacy 不豁免那個。
        if r in legacy_no_redlight():
            return None

        base = os.path.splitext(os.path.basename(r))[0]

        # research/ 底下在 research 站豁免 R3(探索不必先寫測試)。
        # 這不放寬資料完整性(DI)軸 —— DI 在 code-review 跑,而研究碼要進生產
        # 必得走六站、過 code-review,DI 那時照樣管(docs/adr/0011)。
        if (stage_def and stage_def.get("exempts_r3_in_scope")
                and _under_research(r)):
            return None

        # 豁免:票裡已宣告「不測」的模組(接縫裁決在 spec 階段就定了)。
        # 宣告來源是前一站的產物,不是這裡硬編碼;沒宣告就不豁免。
        if is_bare_package_marker(r, content):
            return None

        untested, declared_in = ticket_untested_modules(load_feature(), ticket)
        if base in untested:
            note_exemption(exemptions, r, base, ticket, declared_in)
            return None

        # commit 時 ticket_id 已清空,改查紀錄並回頭驗票(見 logged_exemption_backed)
        if at_commit and logged_exemption_backed(r, base):
            return None

        cands = [
            os.path.join(ROOT, "tests", "test_%s.py" % base),
            os.path.join(ROOT, os.path.dirname(r), "test_%s.py" % base),
            os.path.join(ROOT, "tests", os.path.dirname(r), "test_%s.py" % base),
        ]
        # R3 的另一半:紅燈紀錄。豁免的是**列在凍結清單裡的既有檔案**,
        # 不是「檔案已存在」—— 後者 agent 自己造得出來(建個空檔就進豁免集合),
        # 等於規則自帶開關。清單的入場券是「在機制上線 commit 的樹裡」,偽造不了。
        if r not in legacy_no_redlight() and any(os.path.exists(c) for c in cands):
            # 後半接受的位置必須與前半的 cands 完全相同,否則會出現通過前半、
            # 卡死後半、且無合法解法的死路。
            why = redlight_missing(base, [os.path.relpath(c, ROOT).replace(os.sep, "/")
                                          for c in cands],
                                   impl_rel=r, ticket=ticket)
            if why:
                return ("[R3/紅燈] %s:測試檔存在,但沒有合格的紅燈紀錄。\n"
                        "     %s\n"
                        "     先跑測試確認它在實作不存在時是紅的,再回來寫功能碼。" % (r, why))

        if not any(os.path.exists(c) for c in cands):
            return ("[R3] %s:找不到對應測試(tests/test_%s.py),不可先寫功能碼。\n"
                    "     請先寫測試、執行它、確認紅燈,再回來寫功能碼。票號:%s\n"
                    "     若這不是原始碼(誤擋):把它的目錄加進 %s;\n"
                    "     **不得退回白名單**(docs/adr/0003)"
                    % (r, base, ticket or "未設定", exemption_hint(r)))
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 影子模式(rollout 工具):裝進既有 repo 時先「不擋、只寫日誌」,量測誤擋率再晉升。
#
# 安全閥 SHADOW_MAX 住在 G1 保護的 ~/.claude/shadow-clamp.txt,gate.py **唯讀** ——
# agent 改不了它(乙案,ADR 0012)。控制項不可竄改,證據(shadow-log)可(F-057)。
#
# **fail-closed 方向**:安全閥缺席 / 讀不到 / 壞掉 → 影子**不生效**、照常擋。
# 往「閘門開著」倒,不往「影子開著」倒 —— 安全閥的故障不能變成閘門的關閉。
# ─────────────────────────────────────────────────────────────────────────────

SHADOW_CLAMP = os.path.join(os.path.expanduser("~"), ".claude", "shadow-clamp.txt")
SHADOW_STATE = os.path.join(ROOT, ".dev", "shadow.json")        # 本 repo 開沒開影子
SHADOW_LOG = os.path.join(ROOT, ".dev", "shadow-log.jsonl")     # 證據(可竄改,F-057)


def _parse_iso(s):
    try:
        return datetime.date.fromisoformat(s.strip())
    except Exception:
        return None


def read_shadow_clamp():
    """讀安全閥。回傳 date 或 None。**任何問題一律回 None(影子不生效)。**

    用 `utf-8-sig`:PowerShell 的 Set-Content -Encoding utf8 寫的是帶 BOM 的 UTF-8,
    clamp 檔第一個位元組是 \\ufeff。用 utf-8 讀、哪天 BOM 黏上鍵名 → 解析失敗 →
    fail-closed → 影子永遠開不了,而所有訊息都說「照常擋,正常」——
    fail-closed 系統的故障是隱形的,輸入端的坑要在進門前排掉(使用者指出)。

    格式:恰好一行 `SHADOW_MAX=<ISO 日期>`;# 註解、空行忽略。多行或壞掉 → None。
    """
    try:
        lines = io.open(SHADOW_CLAMP, encoding="utf-8-sig").read().splitlines()
    except Exception:
        return None
    vals = []
    for line in lines:
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("SHADOW_MAX="):
            vals.append(_parse_iso(line.split("=", 1)[1]))
        else:
            return None          # 不認得的行 -> 壞掉 -> fail-closed
    if len(vals) != 1 or vals[0] is None:
        return None
    return vals[0]


def shadow_active(today=None):
    """影子現在生效嗎。回傳 bool。

    生效條件全部要成立:安全閥合法、本 repo 宣告了影子、今天 <= min(兩個到期日)。
    任一缺席 -> False -> 照常擋。
    """
    today = today or datetime.date.today()
    clamp = read_shadow_clamp()
    if clamp is None:
        return False
    try:
        st = json.load(io.open(SHADOW_STATE, encoding="utf-8"))
        until = _parse_iso(st.get("until", ""))
    except Exception:
        return False
    if until is None:
        return False
    return today <= min(clamp, until)


def rule_of(msg):
    """從擋下訊息取規則代號(R\\d+)。取不到回 '?'。"""
    m = re.search(r"\[(R\d+)", msg or "")
    return m.group(1) if m else "?"


def tag_enforce(msg):
    """正式(非影子)擋下時,在規則代號後插入 `[enforce]` 狀態標示。

    **要求:從任何一次攔截訊息就能讀出「現在是影子還是正式」,不必查檔案。**
    影子側的狀態軌跡在 shadow-log 的 `verdict=would-block`(證據落在檔案);
    正式側沒有檔案軌跡 —— 若訊息不自帶標示,兩者在終端機上長得一樣,
    「閘門到底在擋還是在放」只能靠翻 .dev/ 才知道。所以正式標示必須進訊息本身。
    只在**影子有替代分支的那些出口**套用(那些點才有影子/正式之分);
    fail-closed 與掛載點錯誤永遠擋、不受影子左右,不在此列。
    規則代號可能是 `[R2]` 或 `[R2/commit]`,標示插在該括號之後。
    """
    if not msg:
        return msg
    m = re.search(r"\[R\d+[^\]]*\]", msg)
    if m:
        return msg[:m.end()] + "[enforce]" + msg[m.end():]
    return "[enforce] " + msg


def log_shadow(msg, at_commit):
    """把一筆『本該擋』寫進 shadow-log(證據)。append-only。"""
    rec = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "rule": rule_of(msg), "at_commit": at_commit,
           "verdict": "would-block",
           "message": (msg or "").splitlines()[0] if msg else ""}
    try:
        _append_jsonl(SHADOW_LOG, rec)
    except Exception:
        pass
    return rec


def mode_hook():
    """agent 前哨:讀 PreToolUse JSON。

    **以位元組讀取,明確用 utf-8 解碼。** `json.load(sys.stdin)` 在 Windows 上
    會用主控台編碼(cp950)去解,payload 裡的中文路徑當場壞掉,json 報
    `Invalid \\escape`,而原本的 `except: return 0` 把它吞成放行 ——
    **整個前哨層因此靜默失效,一整輪沒有擋過任何東西**,而測試全綠、
    pre-commit 照常擋,沒有任何跡象。見 F-042。

    餵給規則的是 `content_after_edit()` 算出的**編輯後整檔結果**,不是
    `new_string` 那個片段(票 07 / F-046)。那一行是那張票的根因所在。
    """
    try:
        payload = parse_hook_payload(sys.stdin.buffer.read())
    except Exception as e:
        # fail-closed:讀不懂輸入不代表沒事。payload 形狀或編碼一變就靜默關閉,
        # 那是最廉價的繞法,而且沒有人會發現。
        _err("[六站閘門/fail-closed] 讀不懂 PreToolUse 輸入(%s)—— 一律擋下。\n" % e)
        return 2
    ti = payload.get("tool_input") or {}

    # R7 —— Bash/PowerShell 的寫入一律收口回檔案工具。
    # 這一格在維度 5 盤點之前是**零涵蓋**,而零涵蓋不會產生任何訊號:
    # 沒有規則被評估,就沒有規則會出錯(F-039)。
    command = ti.get("command")
    if isinstance(command, str) and command.strip():
        msg = bash_write_violation(command)
        if msg:
            if shadow_active():
                log_shadow(msg, at_commit=False)
                return 0
            # **不套 sentinel_footer()**:那句話說「繞過前哨仍會在 commit 被擋」,
            # 對 R7 是假的 —— commit 看不到工具呼叫,只看得到 staged 檔案。
            # 宣稱有第二道而實際沒有,比沒有第二道更危險(ADR 0008)。
            _err(
                "[六站閘門/前哨] %s\n"
                "(R7 只活在前哨:commit 看得到檔案內容,看不到你用什麼工具寫的。\n"
                " 繞過前哨就沒有第二道了 —— 見 docs/adr/0008)\n" % tag_enforce(msg))
            return 2
        return 0

    path = ti.get("file_path") or ti.get("notebook_path") or ""
    if not path:
        return 0
    # 片段 -> 編輯後的整檔結果。算不出來時是 None(不是空字串):
    # 各規則自己退回磁碟現況,讀不到才 fail-closed。
    content = content_after_edit(path, ti)
    mounts = mount_violations_cached()
    if mounts:
        _err("[六站閘門/前哨] skill 掛載點有問題,先修好再繼續 —— "
                         "你可能正照著被覆蓋過的指令工作:\n")
        for m in mounts:
            _err("  %s\n" % m)
        return 2

    # 豁免在**判決之後**才記帳,而且只在強制點記 —— 這裡才有「真的有人要寫」
    # 這個事件。content 一併帶進去,讓「這次寫入到底改不改得動位元組」
    # 在帳本裡看得見(票 08)。
    used = []
    msg = check(path, content, exemptions=used)
    if msg:
        if shadow_active():
            log_shadow(msg, at_commit=False)
            return 0
        log_exemptions(used, verdict=msg, at_commit=False, content=content,
                       tool=payload.get("tool_name"))
        _err("[六站閘門/前哨] %s\n%s\n" % (tag_enforce(msg), sentinel_footer()))
        return 2
    log_exemptions(used, verdict=None, at_commit=False, content=content,
                   tool=payload.get("tool_name"))

    # 沒被擋也要有機會發現權威層不在 —— 只在擋下時才講的話,
    # 一個從來沒違規的 repo 永遠學不到它只有一道防線。每 session 至多一次。
    installed, detail = authoritative_layer()
    if not installed and _should_renotice():
        _err("%s\n" % not_installed_notice(detail))
    return 0


def _should_renotice():
    """權威層未安裝的提醒節流:每 4 小時至多一次。

    每次工具呼叫都印會被當成背景噪音而被濾掉 —— 那等於沒印(F-031:
    壞掉的訊號會訓練人忽略訊號)。標記檔屬**快取**類:刪掉只是再提醒一次,
    不影響任何判定,所以放 .cache/ 不進版控。
    """
    marker = os.path.join(ROOT, ".cache", "authoritative-layer-notice")
    try:
        if os.path.exists(marker) and (time.time() - os.path.getmtime(marker)) < 4 * 3600:
            return False
        os.makedirs(os.path.dirname(marker), exist_ok=True)
        io.open(marker, "w", encoding="utf-8").write("")
    except Exception:
        return True   # 節流機制壞掉 -> 寧可多印,不要漏印
    return True


def skill_mirror_violations(canon_dir, mirror_dirs):
    """R4 —— **一條規則,依當下佈局分支**。

    不寫成兩個檢查並排:並排會讓其中一個分支在當下佈局永遠不跑,
    那正是這條規則改寫前的處境(佈局改成 symlink 後,內容比對永遠不可能觸發,
    全輪唯一一次觸發還是人工製造的負向測試)。
    單一規則每次執行都必須回答「現在是哪種佈局」,沒有假裝在守的死路徑。

      鏡像是 symlink   -> 驗完整性(斷裂、指向不存在、指向正典之外)
      鏡像是實體目錄   -> 驗內容一致
    """
    import hashlib
    if not os.path.isdir(canon_dir):
        return []
    canon_real = os.path.realpath(canon_dir)

    # 迭代來源必須是**正典與鏡像的聯集**,不能只用正典 ——
    # 只走正典的話,正典項目消失時鏡像那個斷掉的 symlink 永遠不會被走訪,
    # 而那正是「斷裂」最典型的成因。迭代來源本身就會決定涵蓋範圍(維度 4 的同一個形狀)。
    names = set(os.listdir(canon_dir))
    for mirror in mirror_dirs:
        if os.path.isdir(mirror):
            names.update(os.listdir(mirror))

    out = []
    for name in sorted(names):
        src = os.path.join(canon_dir, name, "SKILL.md")
        for mirror in mirror_dirs:
            # 鏡像整個沒建起來不是 drift,是還沒裝 —— 那由安裝流程負責,不是 R4。
            if not os.path.isdir(mirror):
                continue
            entry = os.path.join(mirror, name)
            rel_entry = rel(entry)
            if not os.path.lexists(entry):
                # **少了東西是 R4 最典型的破法**,原本卻被靜默跳過:
                # 舊碼只驗得出「內容不同」,而硬連結/symlink 佈局下內容不可能不同,
                # 兩層疊起來 R4 在實務上是空的(票 02 的機器列舉實測抓到)。
                out.append("[R4] 鏡像缺少 %s —— 正典有而鏡像沒有。\n"
                           "     重建:bash scripts/skills-update.sh" % rel_entry)
                continue

            if os.path.islink(entry):
                # 分支一:symlink 佈局 —— 內容由構造保證,要守的是連結本身
                target = os.path.realpath(entry)
                if not os.path.exists(entry):
                    out.append("[R4] symlink 斷裂:%s 指向已不存在的目標。\n"
                               "     重建:npx skills experimental_sync" % rel_entry)
                elif os.path.commonpath([target, canon_real]) != canon_real:
                    out.append("[R4] symlink 指向正典之外:%s -> %s。\n"
                               "     正典是 %s;內容一樣不代表來源正確,"
                               "上游更新不會傳播到別處的副本。" % (rel_entry, target, rel(canon_dir)))
                continue

            # 分支二:實體副本佈局 —— 兩份各自獨立,會 drift,要守的是內容
            m = os.path.join(entry, "SKILL.md")
            if not os.path.exists(src):
                out.append("[R4] 正典缺少 %s/SKILL.md,鏡像 %s 卻還留著。\n"
                           "     正典被刪而鏡像留著舊的,一樣是不一致。"
                           % (rel(os.path.join(canon_dir, name)), rel_entry))
                continue
            if not os.path.exists(m):
                out.append("[R4] 鏡像缺少 %s/SKILL.md —— 正典有而鏡像沒有。\n"
                           "     重建:bash scripts/skills-update.sh" % rel_entry)
                continue
            if (hashlib.md5(io.open(m, "rb").read()).hexdigest()
                    != hashlib.md5(io.open(src, "rb").read()).hexdigest()):
                out.append("[R4] 實體副本內容不一致:%s/SKILL.md 與正典不同。\n"
                           "     鏡像目錄應為 symlink;重建:npx skills experimental_sync"
                           % rel_entry)
    return out


def _skills_mtime():
    """正典 skill 目錄的最新修改時間。讀不到回 None —— 呼叫端據此重算,不沿用。"""
    canon = os.path.join(ROOT, ".agents", "skills")
    try:
        newest = os.path.getmtime(canon)
        for name in os.listdir(canon):
            p = os.path.join(canon, name, "SKILL.md")
            if os.path.exists(p):
                newest = max(newest, os.path.getmtime(p))
        return newest
    except Exception:
        return None


def _mount_violations_uncached():
    """實際執行掛載點檢查(R5 的兩項)。"""
    return check_third_axis_mount() + check_to_spec_override()


def mount_violations_cached():
    """以工作階段為單位的掛載點檢查。

    覆蓋只可能來自外部更新指令 —— 那是離散事件,不是編輯中途會發生的事,
    所以用 skill 目錄的修改時間當失效條件,未變動就沿用上次結果。

    **失效判斷本身出錯時一律重算**:讀不到修改時間、或修改時間比快取還舊
    (時鐘回撥、檔案被還原)都重算。快取的 fail-open 形狀就是「拿不準就用舊值」。
    """
    now = _skills_mtime()
    cached = None
    try:
        with io.open(MOUNT_CACHE, encoding="utf-8") as f:
            cached = json.load(f)
    except Exception:
        cached = None

    if (now is not None and cached
            and isinstance(cached.get("mtime"), (int, float))
            and now == cached["mtime"]):
        return list(cached.get("violations") or [])

    violations = _mount_violations_uncached()
    if now is not None:
        try:
            os.makedirs(os.path.dirname(MOUNT_CACHE), exist_ok=True)
            with io.open(MOUNT_CACHE, "w", encoding="utf-8") as f:
                json.dump({"mtime": now, "violations": violations}, f, ensure_ascii=False)
        except Exception:
            pass
    return violations


def mode_hook_would_block_on_mounts():
    """前哨是否應因掛載點問題而擋下。抽成述詞,讓它可被直接斷言 ——
    走 subprocess 抓 stderr 等於在測進入點分派,那已裁決不測。"""
    return bool(mount_violations_cached())


def check_skill_copies():
    """以本 repo 的實際路徑呼叫 R4。"""
    return skill_mirror_violations(
        os.path.join(ROOT, ".agents", "skills"),
        [os.path.join(ROOT, ".claude", "skills"), os.path.join(ROOT, "skills")])


MOUNT_MARKERS = (
    "### 3b. Identify the data-integrity sources",
    "**Data Integrity sub-agent prompt**",
    "Clean degradation is mandatory.",
    "Exemption reconciliation (local addition)",
)


def check_to_spec_override():
    """R5(P2)to-spec 的 inline snippet 覆寫。

    上游允許把 prototype 的 snippet inline 進 spec —— 那與 R1 正面衝突(見 docs/adr/0002)。
    覆寫被 update 蓋掉的話,skill 會開始要求 AI 做 R1 一定會擋的事。
    同樣只判存在與位置(布林),不判內容。
    """
    p = os.path.join(ROOT, ".agents", "skills", "to-spec", "SKILL.md")
    if not os.path.exists(p):
        return ["[R5] 找不到正典 .agents/skills/to-spec/SKILL.md"]
    body = io.open(p, encoding="utf-8").read()
    if "LOCAL OVERRIDE (prototype snippets)" not in body:
        return ["[R5] 正典 to-spec 缺 inline snippet 覆寫掛載點。\n"
                "     多半是直接跑了 `npx skills update`(會覆蓋本地 patch)。\n"
                "     修復:bash scripts/skills-update.sh(唯一允許的更新入口)"]
    i_impl = body.find("## Implementation Decisions")
    i_ovr = body.find("LOCAL OVERRIDE (prototype snippets)")
    i_test = body.find("## Testing Decisions")
    if not (i_impl != -1 and i_test != -1 and i_impl < i_ovr < i_test):
        return ["[R5] 正典 to-spec 的覆寫位置錯誤:必須落在「## Implementation Decisions」"
                "與「## Testing Decisions」之間(實際 impl=%d, override=%d, test=%d)。\n"
                "     多半是上游改了錨點附近結構,patch 插到錯的地方。"
                % (i_impl, i_ovr, i_test)]
    return []


def check_third_axis_mount():
    """R5 第三軸掛載點。

    `npx skills update` 會用上游版覆蓋正典 code-review,靜默移除本地第三軸。
    brief 目前留空、不影響行為,但掛載點消失代表 patch 沒被重套 —— 擋下,
    不讓「記得重套」這件事依賴人的記性。
    """
    if not os.path.exists(CANON_CODE_REVIEW):
        return ["[R5] 找不到正典 %s" % os.path.relpath(CANON_CODE_REVIEW, ROOT)]
    body = io.open(CANON_CODE_REVIEW, encoding="utf-8").read()
    missing = [m for m in MOUNT_MARKERS if m not in body]
    if missing:
        return ["[R5] 正典 code-review 缺第三軸掛載點:%s\n"
                "     多半是直接跑了 `npx skills update`(會覆蓋本地 patch)。\n"
                "     修復:bash scripts/skills-update.sh(唯一允許的更新入口)"
                % "、".join('"%s"' % m for m in missing)]

    # 位置判定:錨點插入法真正的失效模式不是「掛載點消失」,
    # 而是上游改動錨點附近結構、patch 插進去但位置錯了 —— 此時字串全在、卻掛錯地方。
    # 只判位置對錯(布林),不判內容好壞(那是審查不是閘門)。
    def at(marker):
        return body.find(marker)

    i_sec3, i_3b, i_sec4 = at("### 3. Identify the standards sources"), \
        at("### 3b. Identify the data-integrity sources"), at("### 4. Spawn")
    i_prompt, i_agg = at("**Data Integrity sub-agent prompt**"), at("### 5. Aggregate")

    misplaced = []
    if not (i_sec3 != -1 and i_sec4 != -1 and i_sec3 < i_3b < i_sec4):
        misplaced.append("3b 節必須落在「### 3.」與「### 4.」之間"
                         "(實際 sec3=%d, 3b=%d, sec4=%d)" % (i_sec3, i_3b, i_sec4))
    if not (i_sec4 != -1 and i_agg != -1 and i_sec4 < i_prompt < i_agg):
        misplaced.append("Data Integrity sub-agent prompt 必須落在「### 4.」與 aggregate 段之間"
                         "(實際 sec4=%d, prompt=%d, agg=%d)" % (i_sec4, i_prompt, i_agg))
    if misplaced:
        return ["[R5] 正典 code-review 第三軸掛載點位置錯誤:\n"
                + "".join("     - %s\n" % m for m in misplaced)
                + "     多半是上游改了錨點附近結構,patch 插到錯的地方。\n"
                  "     檢查 .claude/patches/apply_patches.py 的錨點是否仍成立。"]
    return []


def staged_paths(cwd=None):
    """staged 檔案清單。**用 -z(NUL 分隔),不是 --name-only + splitlines。**

    git 對非 ASCII 檔名預設回傳 C-quoted 路徑(`"docs/\\345\\217\\260….md"`),
    而下游 `replace("\\\\", "/")`(為正規化 os.path.relpath 的 Windows 反斜線而存在,
    本身正當)會把 escape 的反斜線一起換掉 —— 路徑徹底壞掉,`top` 不再是 docs,
    中文檔名的文件被判成原始碼、被 R2 誤擋。這是 F-042 那個編碼假設的第三次現身。

    不用 `core.quotePath=false`:它只關掉引號,檔名含換行或引號時仍有歧義。
    NUL 是唯一不可能出現在路徑裡的位元組 —— 結構上無歧義,不是剛好夠用。
    """
    out = subprocess.check_output(
        ["git", "diff", "--cached", "-z", "--name-only", "--diff-filter=ACM"],
        cwd=cwd or ROOT).decode("utf-8", "replace")
    return [p for p in out.split("\0") if p.strip()]


def mode_pre_commit():
    """權威判定:掃 staged 檔案 + R4 副本一致性 + R5 第三軸掛載點。"""
    try:
        staged = staged_paths()
    except Exception as e:
        _err("[六站閘門] 無法取得 staged 檔案:%s\n" % e)
        return 1
    violations = []
    for f in staged:
        used = []
        m = check(f, None, at_commit=True, exemptions=used)
        # 提交時 content 未知(檔案已經寫進去了),所以 changes_bytes 記 None ——
        # 「不知道有沒有變」不得寫成「確定沒變」。
        log_exemptions(used, verdict=m, at_commit=True, content=None,
                       tool="pre-commit")
        if m:
            violations.append(m)
    violations += check_skill_copies()
    violations += check_third_axis_mount()
    violations += check_to_spec_override()
    violations += check_legacy_list()
    if violations:
        if shadow_active():
            # 影子:不擋,逐筆寫進 shadow-log(每筆一個規則,per-rule 晉升要逐條算)。
            for v in violations:
                log_shadow(v, at_commit=True)
            _err("[六站閘門/影子] %d 項本該擋下,已寫進 %s(影子模式:不擋)。\n"
                 % (len(violations), rel(SHADOW_LOG)))
            return 0
        _err("\n[六站閘門/pre-commit] commit 已擋下,%d 項違規:\n\n" % len(violations))
        for v in violations:
            _err("  %s\n" % tag_enforce(v))
        _err("\n如確定要略過:git commit --no-verify(會留下紀錄,請自行負責)\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(mode_pre_commit() if "--pre-commit" in sys.argv else mode_hook())
