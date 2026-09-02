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
import hashlib
import io
import json
import os
import posixpath
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
#   證據(消失即失去判定依據 → fail-closed)  放 .dev/
#   快取(可重建的純加速結構 → 重算)         放 .cache/,不進版控
# 目錄本身就是分類,不必靠記性維持;新增狀態檔時看它該擺哪就知道它是哪一類。
#
# ## F-036 修訂(票 31,2026-08-14)
#
# **舊文**:上面第一行原本寫「放 .dev/,**進版控**」,而 `.gitignore` 忽略
# 整個 `/.dev/` —— 三處說法不一致(本檔、`redlight.py`、`.gitignore`),
# 實測 `git ls-files .dev` = 0。**註解描述了一個不存在的機制。**
#
# **現行分軌**,判準是「可審計性 vs 流量」,而兩邊各有一條存續管道:
#   gate-exemptions.jsonl / provenance.jsonl  **進版控** —— 豁免史要可逐筆對帳
#                                             (票 24:不進版控的帳本對不了帳)
#   test-runs.jsonl                           **不進版控** —— 每跑一次測試就長,
#                                             存續歸 R5 的週級異地備份
#   pipeline.json                             不進版控 —— 執行期狀態,每台機器不同
#
# **「證據要進版控」不再是一句無條件的話。** 判準沒變(消失即失去判定依據),
# 變的是「怎麼讓它不消失」不只有版控一條路。
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
        "adr": "docs/adr/F-0013-r3-redlight-judges-the-implementation.md",
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
    # **模式旗標也要在。** 只比對 "gate.py" 的話,一支
    # `exec python .../gate.py`(沒帶 --pre-commit)會被判成已安裝 ——
    # 而它跑的是 gate.py 的預設模式,**什麼都不擋**。
    # 檔案在、名字對、內容含 "gate.py",三件事都成立而那一層仍然不存在:
    # 這是「讀起來在守、實際只守一部分」的形狀(R4 那一族),
    # 判定用的證據比它宣稱保證的東西弱一階(票 27)。
    if "--pre-commit" not in body:
        return False, ("%s 有呼叫 gate.py,但**沒帶 `--pre-commit`** —— "
                       "那跑的是預設模式,不是權威判定,什麼都不會擋。" % rel(hook))
    # **洩漏段也要在**(票 76 B5)。hook 的契約是兩段都接(.githooks/pre-commit,
    # 票 27),而本判定原本只找 "gate.py" 與 "--pre-commit" —— 判定用的證據比
    # 契約弱一階(與上面 --pre-commit 那格同族,方向相反:那次掉的是 gate 段,
    # 這格掉的是 leak_scan 段)。少了這格,裝好之後洩漏段被降級是**完全靜默**的:
    # 常駐提醒照說已安裝、活體金絲雀照綠,唯一驗它的時點是安裝當下
    # (verify_gates 的 F-062 檢查),而那個時點只有一次。
    if "leak_scan" not in body:
        return False, ("%s 有六站那段(gate.py --pre-commit),但**沒接 leak_scan** "
                       "—— 洩漏偵測層不在:含真金鑰的 commit 會直接成功"
                       "(F-062 負控實測過的方向)。兩段都接才算裝好。" % rel(hook))
    return True, "%s 已接 leak_scan + gate.py --pre-commit(兩段)" % rel(hook)


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
#
# ## 兩條設計原則(票 21 落地時寫下,不只留在票裡)
#
# **一、偵測要過度涵蓋,抽取才要誠實。**
# `WRITE_CONSTRUCT`(判斷有沒有在寫)刻意跑在**原字串**上,連引號裡的都算 ——
# 因為引號內容可能被執行(`sh -c "rm -rf x"`),而那從字串本身判斷不出來。
# 目標抽取則相反:遮掉引號內部、抽不到就說抽不到。
# **把遮蔽用到偵測上,就是把誤擋換成漏擋 —— 誤擋會被抱怨,漏擋不會有人發現。**
#
# **二、答案不在字串裡的東西,再多解析也拿不到。**
# 跳脫空白(那個空白是分隔符還是檔名的一部分)、變數的值、執行期的 cwd、
# 引號內容會不會被執行 —— 這些都不是字串的性質。
# 對它們的正確姿態是 **refuse 並明說**,不是猜一個看起來像路徑的東西:
# **擋得住而說不出來,好過擋得住而說錯**(具體而錯誤的訊息會被相信)。
# ─────────────────────────────────────────────────────────────────────────────

# 會動到檔案的指令 —— **單一來源**,偵測(正則)與抽取(集合)都從這裡長出來。
#
# 票 29 之前是兩份各自維護的名單,而 `WRITE_COMMANDS` 的註解宣稱
# 「與 WRITE_CONSTRUCT 的第一段同一份名單」—— 實測兩者的 PowerShell 交集是
# **空集合**。註解描述了一個從未存在的同步,後果是那五個 cmdlet
# 偵測得到卻抽不出目標,訊息退化成「(解析不出寫入目標)」。
# 兩份會分岔,所以現在只有一份(ADR 0003 的同一句話)。
POSIX_WRITE_COMMANDS = ("tee", "cp", "mv", "touch", "mkdir", "install",
                        "rm", "rmdir", "dd", "truncate")

# PowerShell 的動詞-名詞。**寫入與刪改是同一個家族,要一起收。**
# 票 29 之前只收了寫入那半,於是**專案內 `Remove-Item` 同時穿過 R7 與 G1**
#(G1 第二級刻意只管專案外,那是寫在 g1_guard.py 註解裡的設計)。
# 漏掉刪除的方向特別差:寫入被漏還留著檔案可以事後看,刪除被漏之後沒有東西可以看。
#
# **列舉來源是 PowerShell 的動詞表,不是「我想得到的」**(F-083):
# 想不到不等於不存在,所以往後要加的時候去查動詞表,不要憑印象。
PS_WRITE_CMDLETS = (
    # *-Content
    "Set-Content", "Add-Content", "Clear-Content", "Out-File",
    # *-Item(檔案本體的增刪搬改)
    "New-Item", "Remove-Item", "Move-Item", "Copy-Item", "Rename-Item",
    "Set-Item", "Clear-Item",
    # Export-*:把資料直接寫成檔
    "Export-Csv", "Export-Clixml", "Export-Alias",
    # 壓縮/解壓 —— **解壓也是寫**
    "Compress-Archive", "Expand-Archive",
    # 其餘寫檔者(第三類調查的產出)
    "New-FileCatalog", "Update-ScriptFileInfo", "Tee-Object",
    "Start-Transcript", "Save-Help", "Trace-Command", "Set-TraceSource",
)

WRITE_CONSTRUCT = re.compile(
    r"(?:^|[\s;&|(])(?:" + "|".join(POSIX_WRITE_COMMANDS + PS_WRITE_CMDLETS) + r")(?:\s|$)"
    r"|(?<![0-9])>>?(?!&)"          # > 與 >>,但排除 2>&1 這種 fd 重導
    r"|<<"                          # heredoc
    r"|sed\s+(?:-[a-zA-Z]*\s+)*-i", re.IGNORECASE)

# PowerShell 具名參數裡**會是路徑**的那幾個。可列舉,所以列舉。
# 其餘參數的值一律不當目標 —— `-Value hello` 的 `hello` 不是路徑,
# 把它當目標就是票 21 那個「具體而錯誤」的訊息,而人會相信它然後去找一個不存在的路徑。
#
# **參數名的歧義被動詞閘中和掉了。** `-FilePath` 在 `Tee-Object` 是輸出、
# 在 `Start-Job` 是**輸入腳本** —— 同一個名字,相反方向。
# 純參數比對會把後者誤判成寫入;而這份清單只在「動詞已經是已知寫入者」時才被查,
# 所以 `Start-Job` 根本走不到這裡。**歧義由上一層解決,不是由這一層猜。**
PS_PATH_PARAMS = {"-path", "-literalpath", "-destination", "-newname", "-target",
                  "-destinationpath", "-catalogfilepath", "-filepath", "-outfile"}

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


# 會寫檔的指令,**由上面那份單一來源長出來**,寫成集合是為了逐 token 比對 ——
# 正規表示式找得到「有沒有」,找不到「寫到哪」。
# 從同一份長出來之後,「兩邊要一致」不再是一句註解,是**構造上不可能不一致**
#(而測試 `test_the_two_lists_agree_on_powershell_verbs` 守住往後有人拆開它)。
WRITE_COMMANDS = {c.lower() for c in POSIX_WRITE_COMMANDS + PS_WRITE_CMDLETS}

# 是不是 PowerShell 那半 —— 抽取規則不同(具名參數 vs 位置運算元)。
PS_WRITE_LOWER = {c.lower() for c in PS_WRITE_CMDLETS}

# 包裝器:真正的指令在它們後面一格。少了這個,`sudo rm -rf x` 的 rm
# 不在指令位置,運算元就掃不到。
WRAPPERS = {"sudo", "env", "time", "nohup", "xargs", "command"}

# `>` / `>>` / `2>` 後面那一段就是重導向目標。`2>&1` 不算(fd 重導向,不落地)。
REDIRECT_RE = re.compile(r"(?<!\d)(?<!&)>>?\s*([^\s;&|>]+)")


# 段落切分 —— **單一來源**(票 76 A2)。許可判定與目標抽取原本各持一份:
# 許可那份少了單一 `|`,於是 `git log | tee pkg/evil.py` 整段被當 git 放行
# (管線後面那截才是真正在寫的東西,而它從來沒被看過);目標抽取那份有 `|`。
# **同一條規則兩份切段定義** —— POSIX_WRITE_COMMANDS 的註解記過同型教訓
# (票 29:兩份各自維護的名單必分岔,而註解宣稱的同步從未存在),修法相同:
# 只留一份,「兩邊要一致」從紀律變構造。
SEGMENT_SPLIT_RE = re.compile(r"&&|\|\||;|\|")


def _allowed_cmd_prefix(seg):
    """這一段是不是以許可指令開頭。**前綴後須為空白或字串尾**(票 76 A1)。

    裸的 `startswith` 沒有邊界:`gitfoo`、`github-cli`、`pipx` 都以許可詞開頭,
    整段(含重導向)因此免檢 —— F-051 邊界家族,F-117 記的三處之一。
    以 `/` 結尾的前綴(`python .claude/`)自帶邊界:斜線本身就是分隔符,
    `.claudefoo` 從構造上 startswith 不到它,所以那一類維持原樣。
    """
    for p in BASH_ALLOWED_CMDS:
        if p.endswith("/"):
            if seg.startswith(p):
                return True
        elif seg == p or (seg.startswith(p) and seg[len(p)] in " \t"):
            return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# 「切不乾淨」的字元層級訊號(票 21 E/F)
#
# **不造 tokenizer。** shlex 兩個模式都量過,兩個都不能用:
#   posix=True   E/F 切得完美,但 `rm C:\Users\fake\thing.py`
#                -> `C:Usersfakething.py`(反斜線被當跳脫,Windows 路徑毀了)
#   posix=False  Windows 路徑正確,但 E 裂成 `"pkg"` + `/"thing.py"`(比現行更糟)
#
# **posix=True 那條是「半套解析比零解析危險」的直接證據**:它產生一個
# 看起來像路徑、實際不存在的字串,然後那個字串會被拿去比對許可清單。
# 零解析至少知道自己是零。
#
# 所以改成偵測**可列舉的模糊訊號**,命中就 refuse ——
# 不解析、不猜、不報路徑。修掉的正是本票的標題病:
# `rm pkg/my\ file.py` 從「捏造一個不存在的 file.py」變成「說我切不動」。
_ESCAPED_SPACE_RE = re.compile(r"\\[ \t]")

# 訊息用的佔位項。**與「(解析不出寫入目標)」分開** —— 兩者的處置不同:
# 這一個是「引號寫法讓切分有多種讀法」,人可以改寫指令;
# 那一個是「動詞認得但運算元掃空」,通常要換工具。
AMBIGUOUS_QUOTING = "(引號或跳脫使目標無法可靠切分)"


def _quoting_is_ambiguous(seg):
    """這一段的引號/跳脫,能不能可靠地切成 token?

    兩個訊號,都是字元層級的,**不需要理解語法**:

      跳脫空白   反斜線後面接空白 -> 那個空白到底是分隔符還是檔名的一部分,
                 從字串本身答不出來
      引號殘留   剝掉成對的外層引號之後,token 裡**還有**引號 ->
                 引號不在兩端,切分就不只一種讀法

    `"pkg/thing.py"` 剝完乾淨 -> 不命中(單純引號照樣正常運作)。
    `C:\\Users\\fake\\thing.py` 沒有引號、反斜線後面接的是字母 -> 不命中。
    """
    if _ESCAPED_SPACE_RE.search(seg):
        return True
    for tok in seg.split():
        if '"' not in tok and "'" not in tok:
            continue
        core = tok
        # **先剝掉 `VAR=` 前綴。** `PATH="$PATH:/x"` 的引號在 `=` 之後,
        # 不剝的話每一條帶引號的賦值都會被判成模糊 ——
        # 連 `export PATH="…"` 這種完全無害的都擋。
        # 那是 F-031 那條路的起點:沒擋住任何實際危險,卻穩定增加繞路成本,
        # 而繞路成本累積起來規則會被關掉。(本 repo 自己跑匯出時實撞一次。)
        assign = re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", core)
        if assign:
            core = core[assign.end():]
        for q in ('"', "'"):
            if len(core) >= 2 and core[0] == q and core[-1] == q:
                core = core[1:-1]
                break
        if '"' in core or "'" in core:
            return True
    return False


def _mask_quoted(seg):
    """把**成對引號內部**的字元遮成 `\\x00`,**長度不變**。

    只用來讓 `REDIRECT_RE` 看不見引號裡的 `>` ——
    長度不變是為了讓比對到的偏移量能對回原字串取原文
    (重導向目標本身可能就在引號裡:`> "out file.txt"`)。

    **前提是引號成對且無跳脫空白**,而那是 `_quoting_is_ambiguous`
    先擋掉的 —— 走到這裡的段落必然滿足。**順序不能反**:
    先遮蔽、後 refuse 的話,遮蔽仍然是猜(票 21 的選型論證)。

    引號字元本身不遮 —— 它們是邊界,遮掉的話 token 化會走樣。
    """
    out = list(seg)
    quote = None
    for i, ch in enumerate(seg):
        if quote is None:
            if ch in ('"', "'"):
                quote = ch
        elif ch == quote:
            quote = None
        else:
            out[i] = "\x00"
    return "".join(out)


def _target_allowed(token):
    """這個寫入目標在不在許可清單裡。**路徑成分比對,不是子字串**(票 76 A3)。

    子字串的 `in` 沒有邊界:`mybuild/x` 含 `build/`、`x.dev/y` 含 `.dev/`、
    `myscratchpad_notes.py` 含 `scratchpad` —— 全部被誤判成許可(F-051 家族,
    F-117 記的三處之一)。正典形狀照 scanner.py 的兩種錨定:成分兩側補分隔符,
    讓「成分在開頭 / 中間 / 結尾」用同一個式子判,而且兩側必然是邊界。

    以 `/` 結尾的清單項(目錄)**不吃尾端補位**:`.dev/` 要求斜線真的出現在
    目標字串裡 —— 否則 `rm -rf .dev` 這種**刪目錄本體**的指令會因為補位
    變成許可,而舊行為擋它(證據目錄不是「`.dev/` 底下的流量」)。
    """
    tok = token.strip().strip('"').strip("'").replace("\\", "/")
    haystack = "/" + tok.lstrip("/")
    for t in BASH_ALLOWED_TARGETS:
        needle = "/" + t.strip("/") + "/"
        if t.endswith("/"):
            if needle in haystack:
                return True
        elif needle in haystack + "/":
            return True
    return False


def unallowed_write_targets(command):
    """這條指令會寫到哪些**沒有被許可**的位置。回空串列 = 每個目標都許可。

    要問的是「**每一個**寫入目標都被許可嗎」,不是
    「指令字串裡有沒有出現過一個許可目標」。後者是原本的寫法,
    而它讓 `2>/dev/null` 變成萬用通行證:`rm -rf x >/dev/null`、
    `tee gate.py < evil 2>/dev/null` 全部放行(票 19)。

    兩類目標:
      重導向     `>` / `>>` 後面那一段
      寫入指令   `rm` / `cp` / `mv` / `tee` / … 的路徑運算元(旗標不算)

    **解析不出來時回一個佔位項(= 擋)**:半套的解析器比零涵蓋更危險,
    所以不確定往嚴的倒(ADR 0008 的同一句話)。
    """
    bad = []
    # **先按分隔符切段再解析。** 不切的話,運算元會一路吃過 `;` 吃到下一段:
    # `rm -rf x; cd y && ls` 會把 `cd`、`y`、`ls` 全當成 rm 的目標。
    # 分隔符還可能**黏在 token 上**(`fresh9;`),所以用切的,不是比對 token。
    # 切段定義與許可判定同一份(票 76 A2,見 SEGMENT_SPLIT_RE)。
    segments = [s for s in SEGMENT_SPLIT_RE.split(command) if s.strip()]
    # **兩個變數,不是一個**(票 36)。原本只有 `saw_construct`,於是
    #   「有寫入構造」與「抽到了目標」混成同一件事 —— 而它們不是:
    #   動詞認得(construct=True)但運算元全被跳過(target=False)時,
    #   舊碼不補佔位項、回空串列,呼叫端看到空就放行 = **fail-open**。
    # 實測穿過去的:`rm -- -weird.py`(`--` 後的檔名以 `-` 開頭被當旗標)、
    # `Copy-Item .cache/x.json pkg/thing.py`(只取第一個運算元,而它剛好許可,
    # 目的地從頭到尾沒被看過)。
    saw_construct = False
    saw_target = False           # 有沒有**抽到任何目標**(不管許不許可)
    for seg in segments:
        if _quoting_is_ambiguous(seg):
            # 切不乾淨 -> **不抽運算元**(票 21 E/F)。
            # 抽了才是禍:舊碼會從 `rm pkg/my\ file.py` 生出一個
            # **指令裡根本沒有**的 `file.py`,而人會相信它。
            #
            # **但引號外的真重導向照樣要抓。** `echo "a -> b" > out.txt`
            # 的引號內有 `->`(讓這一段變模糊),而 `> out.txt` 是真的在寫檔 ——
            # 因為模糊就整段放過,等於**把誤擋換成漏擋**,而那個方向更糟:
            # 誤擋會被抱怨,漏擋不會有人發現。
            saw_construct = True
            saw_target = True            # 已經有結論,不要再落到「解析不出」那句
            for m in REDIRECT_RE.finditer(_mask_quoted(seg)):
                raw_target = seg[m.start(1):m.end(1)]
                if not _target_allowed(raw_target):
                    tgt = raw_target.strip('"').strip("'")
                    if tgt not in bad:
                        bad.append(tgt)
            if AMBIGUOUS_QUOTING not in bad:
                bad.append(AMBIGUOUS_QUOTING)
            continue
        # **重導向只在引號外算數**(票 21 標本 3)。
        # `sed 's/…/<x>/g'` 的 `>` 在引號裡,它不是 shell 重導向 ——
        # 舊碼把它當成重導向,於是生出 `/g` 這種垃圾目標。
        # 遮蔽保長度,所以比對到的偏移量可以回原字串取**原文**
        #(重導向目標本身可能就在引號裡:`> "out file.txt"`)。
        masked = _mask_quoted(seg)
        for m in REDIRECT_RE.finditer(masked):
            saw_construct = True
            saw_target = True
            raw_target = seg[m.start(1):m.end(1)]
            if not _target_allowed(raw_target):
                bad.append(raw_target.strip('"').strip("'"))

        tokens = seg.replace("\t", " ").split()
        # **只認指令位置的 token。** `rm` / `cp` / `install` 是不是寫入指令,
        # 取決於它在不在指令位置 —— `echo "install exit=$?"` 裡的 `install`
        # 是散文,`python x.py install` 裡的是參數。
        # 不分位置的話,一個字出現在引號裡就會觸發整套運算元掃描(F-078 家族)。
        i = 0
        while i < len(tokens) and (
                "=" in tokens[i] and not tokens[i].startswith("-")
                and "/" not in tokens[i].split("=", 1)[0]
                or os.path.basename(tokens[i]).lower() in WRAPPERS):
            i += 1                       # 跳過 FOO=bar 前綴與 sudo/env/time 之類
        verb = (os.path.basename(tokens[i].strip('"').strip("'")).lower()
                if i < len(tokens) else None)
        if verb in WRITE_COMMANDS:
            saw_construct = True
            i += 1
            if verb in PS_WRITE_LOWER:
                # **PowerShell:只認可列舉的位置。** 動詞後面第一個運算元,
                # 加上 `-Path` / `-Destination` / … 後面那一個。其餘一律不當目標。
                #
                # 不沿用下面那個「跳過 -Flag、其餘都是目標」的迴圈:PowerShell 的
                # 具名參數帶值,`-Value hello -Encoding utf8` 會讓 `hello`、`utf8`
                # 全變成「寫入目標」—— 那是票 21 的病(**具體而錯誤的訊息
                # 比含糊而誠實傷害更大**,因為人會相信它然後去找一個不存在的路徑)。
                # 抽不到就讓下面的佔位項接手:**擋照擋,只是不亂猜。**
                # **取所有位置運算元,不只第一個**(票 36)。
                # 只取第一個的話,`Copy-Item A B` 抽到的是**來源** ——
                # 而來源只被讀、目的地才被寫。來源剛好許可時,
                # 目的地從頭到尾沒被看過 -> bad 空 -> 放行(實測穿過去)。
                #
                # 取全部**不會**把 `-Value hello` 的 `hello` 抓進來:
                # 下面的 `-Flag` 分支已經連它的值一起跳過,
                # 走到這裡的只有裸的位置運算元。
                #
                # 代價誠實寫出來:**抽取器分不出讀/寫方向**,
                # 所以 `Copy-Item A B` 的 A 也會被點名,而 A 其實只被讀。
                # 那是過度回報(fail-closed 方向),訊息的標注歸票 21。
                while i < len(tokens):
                    tok = tokens[i]
                    if tok.lower() in PS_PATH_PARAMS and i + 1 < len(tokens):
                        nxt = tokens[i + 1]
                        if not nxt.startswith("-"):
                            saw_target = True
                            if not _target_allowed(nxt):
                                bad.append(nxt.strip('"').strip("'"))
                        i += 2
                        continue
                    if tok.startswith("-"):
                        i += 2 if (i + 1 < len(tokens)
                                   and not tokens[i + 1].startswith("-")) else 1
                        continue          # 具名參數連它的值一起跳過
                    saw_target = True
                    if not _target_allowed(tok):
                        bad.append(tok.strip('"').strip("'"))
                    i += 1
                continue
            while i < len(tokens):
                tok = tokens[i]
                if tok.startswith("-") or tok.startswith(">") or "<" in tok:
                    i += 1
                    continue
                if REDIRECT_RE.match(tok):
                    i += 1
                    continue
                saw_target = True
                if not _target_allowed(tok):
                    bad.append(tok.strip('"').strip("'"))
                i += 1

    # **三態,不是兩態**(票 36):
    #   抽到目標、有不許可的  -> bad 非空,擋並點名
    #   抽到目標、全部許可    -> bad 空且 saw_target -> **放行**
    #   一個目標都沒抽到      -> **擋**,而且說出來是解析失敗
    #
    # 舊碼的條件是 `not bad and not saw_construct`,於是第三態被吃進第二態:
    # 動詞認得(construct=True)但運算元全被跳過,回空串列 = 放行。
    # 判準是**抽到了沒有**,不是**有沒有寫入構造** —— 那是兩件事,
    # 混成一個變數就是這個洞的根(票 29 收窄抽取時沒有一起鋪底)。
    if not saw_target:
        # 看不懂就擋,而且**明說是看不懂** —— 絕不捏造一個看起來像路徑的東西。
        # 票 21 的標題病正是憑空生出路徑;擋得住而說不出來,好過擋得住而說錯。
        bad.append("(解析不出寫入目標)")
    # 去重但保留順序 —— 訊息要好讀,而重複的目標名沒有多給資訊
    seen, out = set(), []
    for b in bad:
        if b not in seen:
            seen.add(b)
            out.append(b)
    return out


# 刪除/改名的動詞 —— 它們的出口**不是** Write / Edit(那兩個工具做不到),
# 而是 `git rm` / `git mv`(`git` 在許可清單裡,一直都過得了)。
_DELETE_VERBS = ("rm", "rmdir", "del", "erase", "unlink",
                 "remove-item", "clear-item", "clear-content")
_RENAME_VERBS = ("mv", "move-item", "rename-item", "copy-item", "cp")


def _real_exit_for(cmd):
    """這條指令真正的出口是什麼。回 None 表示 Write / Edit 就是對的。

    票 13 的活標本:訊息說「請改用 Write / Edit」,而**那兩個工具不能刪除或改名** ——
    照著做的人會得出「這件事做不到」,然後發明一條繞路
    (本票原本的結論就是這樣長出來的:留著不刪,兩個檔案並存)。
    """
    toks = [os.path.basename(t.strip('"').strip("'")).lower()
            for t in cmd.replace("\t", " ").split()]
    if any(t in _DELETE_VERBS for t in toks):
        return "git rm"
    if any(t in _RENAME_VERBS for t in toks):
        return "git mv"
    return None


_SEG_CLIP = 60


def _clip_segment(seg):
    """訊息裡的段落要可讀 —— heredoc 切出來的段落可以帶著幾十行內文。

    **只動印出來的字,不動比對的字。** 吵鬧的訊號訓練人忽略訊號(F-031),
    而一份把整份內文倒出來的擋下訊息,讀者會直接跳過 —— 那等於訊息不存在。
    """
    s = " ".join(seg.split())
    return s if len(s) <= _SEG_CLIP else s[:_SEG_CLIP] + "…"


def _may_carry_an_inline_body(cmd):
    """這條指令可能夾帶「內文」(heredoc 或引號括起來的資料)嗎。

    **純包含測試,不解析。** 回 True 只讓訊息多印一段提示,回 False 也不改變
    任何判定 —— 所以這裡刻意寧可多印:誤印的代價是幾行字,
    漏印的代價是讀者照字面推論出「整條以 `git` 開頭就安全」,而那是錯的(票 57 ⑦)。

    **這不牴觸「不寫半套解析器」。** 那條規矩約束的是**判定**
    (`bad` 怎麼算、擋不擋),而這個述詞完全不參與判定 ——
    它的輸出只進訊息。**偵測要過度涵蓋,抽取才要誠實**,而這裡兩者都不是。

    要求同時有引號與分隔字元,是為了不讓 `printf 'a' >> log.md` 這種
    根本沒有內文可切的指令也吃到那三行提示。
    """
    if "<<" in cmd:
        return True
    if not ("'" in cmd or '"' in cmd):
        return False
    return any(sep in cmd for sep in (";", "&&", "||"))


def _r7_head(bad, mixed, offenders, cmd):
    """擋下訊息的第一段 —— **說出是哪一個前提沒滿足**(票 13 判準)。

    品質標竿是票 31 的 R2 訊息:說出判準、說出實際的位置、說出該做什麼。

    **票 57 ⑦:「逐段比對」那句原本掛在 `if mixed:` 底下,而
    `mixed = any(seg_ok) and offenders` 要求「至少有一段許可」。**
    heredoc 那條路徑上一段都不許可(`python` 不在 `BASH_ALLOWED_CMDS`),
    於是那句**一個字都印不出來** —— 實測訊息只有兩行,
    而那條指令根本沒在寫檔案(F-097)。票 13 修好的是 `mixed` 分支,
    heredoc 走的是另一條:**不是回歸,是同一張票的涵蓋缺口。**

    改成 `if offenders:`,兩條路徑各自說自己的話。
    **這是訊息的發出條件,不是判定** —— `bash_write_violation()` 對同一條
    指令的擋/放結論一個字都沒變,由 `test_the_verdict_is_untouched` 釘住。
    """
    exit_hint = _real_exit_for(cmd)
    # **空字串的目標不進訊息。** 票 13 第 3 項(目標欄空括號)當時判為
    # 「closed by 票 36」——`if not saw_target` 保證 `bad` **不是空 list**。
    # 但那擋不住 `bad` 裡夾著一個**空元素**:`"、".join` 會印出
    # `(…、)` 這種結尾,讀者看到的是一個沒有名字的目標。
    # **「清單非空」與「清單裡每一項都有內容」是兩件事**,票 36 只保證了前者。
    # 這裡只過濾**印出來的**那一份,`bad` 本身一個字都不動 —— 判定不受影響。
    shown = [b for b in bad if b and b.strip()] or list(bad)
    head = "[R7] 這個 Bash 指令會寫到沒有被許可的位置(%s)。\n" % "、".join(shown)
    if offenders:
        # **落出許可清單的是某一段,不是整條。** 不說的話,人看到 `git mv` 被擋
        # 會以為 git 不在清單裡,然後去改一個沒問題的地方(F-046 的形狀)。
        head += "     **許可是逐段比對的**(`&&` / `;` / `||` 各算一段)。\n"
        if mixed:
            head += ("     這幾段不在清單裡:%s\n"
                     "     其餘各段本來就許可 —— 把它們拿掉就過得了。\n"
                     % "、".join("`%s`" % _clip_segment(s) for s in offenders))
        else:
            # **「某一段落出清單」與「一段都沒有」的修法不同**,不能講成同一句:
            # 前者拿掉那一段就過得了,後者整條要換寫法。把後者說成前者,
            # 人會去刪一個刪不掉的前綴,然後得出「這件事做不到」(票 13 的形狀)。
            head += ("     而**沒有任何一段在清單裡** —— 不是某一段的問題,"
                     "整條要換寫法。\n")
    inline = _may_carry_an_inline_body(cmd)
    if inline:
        # **切分不認引號、不認 heredoc 內文。** 不說這件事的話,
        # 讀者會把上面那句讀成「講的是 shell 的指令分隔符」,
        # 於是推論出「整條以 git 開頭就安全」—— 而實測不是(F-097 資料點 3/5/6/7)。
        head += ("     **切分不認引號,也不認 heredoc 內文**:`<<'EOF'` 到 `EOF` 之間、\n"
                 "     以及引號裡的每一個 `;` / `&&` / `||`,一樣會被切成一段。\n"
                 "     所以「整條以 `git` 開頭」不代表安全 —— 訊息或腳本內文裡的一個分號,\n"
                 "     就會切出一段不以許可前綴開頭的段落。\n"
                 "     出口:**內文用 Write 寫成檔案**,再 `git commit -F <路徑>`\n"
                 "     或 `python <路徑>` 餵進去 —— 內文完全不進指令字串,\n"
                 "     就沒有東西可以被切。\n")
    if exit_hint:
        head += ("     **Write / Edit 不能刪除或改名** —— 這條的出口是 `%s`"
                 "(`git` 在許可清單裡)。\n" % exit_hint)
    elif not inline:
        # 內文那一段**已經指名了更精確的出口**(寫成檔案再餵進去)。
        # 後面再補一句「請改用 Write / Edit」是把讀者從精確的出口拉回模糊的那個 ——
        # 票 13 的形狀:訊息的最後一句最容易被當成結論,而它比上一句弱。
        head += "     請改用 Write / Edit。\n"
    return head


def bash_write_violation(command):
    """R7:這個 Bash 指令會不會寫入 repo。回 None(放行)或訊息。"""
    if not command or not command.strip():
        return None
    cmd = command.strip()

    # 逐段比對:`a && b` 的每一段都要在許可清單裡才算數,
    # 否則 `git status && rm -rf x` 會整條被許可。
    # 前綴比對帶邊界(票 76 A1)—— `gitfoo` 不是 `git`,見 _allowed_cmd_prefix。
    segments = [s.strip() for s in SEGMENT_SPLIT_RE.split(cmd) if s.strip()]
    seg_ok = [_allowed_cmd_prefix(seg) for seg in segments]
    if segments and all(seg_ok):
        return None
    # **哪幾段落出許可清單** —— 只拿來寫訊息,判定邏輯一個字都不動(票 13)。
    offenders = [seg for seg, ok in zip(segments, seg_ok) if not ok]
    mixed = any(seg_ok) and offenders

    if not WRITE_CONSTRUCT.search(cmd):
        return None

    # 「確定在 repo 外」與「不知道寫到哪」是兩件事:前者可以放行(repo 外是 G1 的事),
    # 後者必須擋。只放行前者 —— 而判準是**每一個寫入目標**都被許可,
    # 不是「指令字串裡出現過一個許可目標」(票 19,判錯對象第七例)。
    bad = unallowed_write_targets(cmd)
    if not bad:
        return None
    return (_r7_head(bad, mixed, offenders, cmd) +
            "     理由不是風格:從指令字串解析『寫到哪』解不完,而半套的解析器\n"
            "     比零涵蓋更危險 —— 零涵蓋你知道它是零。所以入口收成一個,\n"
            "     走檔案工具的話 R1–R6 全部適用。\n"
            "     例外(附理由)在 gate.py 的 BASH_ALLOWED_CMDS / BASH_ALLOWED_TARGETS。\n"
            "     指令裡出現 /dev/null **不會**讓其他寫入一起免檢。")


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


def _declares_src_write(stage_def):
    """這一筆站定義有沒有宣告 `allows_src_write`。**判準的唯一字面在這裡。**

    抽成一個字的函式看起來像多餘,而它擋的是一種特定的漂移:
    原本同一個判準在 `check()` 裡有**兩個**寫法(一個 set comprehension、
    一個 `next(...)` 的條件),改其中一個不會讓另一個出聲。
    """
    return bool(isinstance(stage_def, dict) and stage_def.get("allows_src_write"))


def writable_stage_ids(stages):
    """這份定義裡,哪些站宣告了可寫原始碼。回傳 id 的集合。"""
    return {s.get("id") for s in stages if _declares_src_write(s)}


def stage_allows_src_write(stage_id):
    """這一站可以寫原始碼嗎。回傳 bool。**票 99 裁 A。**

    為什麼要有名字:consumer(票 99 的 `status`)要問這件事,而在此之前
    判準只 inline 在 `check()` 裡。沒有名字的話,問的人只有兩條路 ——
    拿候選路徑一條一條餵 `check()`(用「擋不擋」反推「能不能寫」),
    或**自己組一份判定**。後者會長出第二份判準,而兩份必然漂開(`F-058` 家族)。

    **`status` 只呼叫,不重述。** 這一句是票 99 的判準 2,而它需要一個可呼叫的東西
    才成立 —— 少了本函式,那句話就只是一句話。

    **fail-closed**:定義檔讀不到(`load_stage_defs()` 回 err)、或站名不在定義裡,
    一律 False。`pipeline.json` 是可被手改的執行期狀態,打錯一個字就會出現
    定義檔裡沒有的站名 —— **那時的正確答案是「不准寫」,不是「查無此站所以隨便」。**
    """
    stages, _flow, err = load_stage_defs()
    if err:
        return False
    return stage_id in writable_stage_ids(stages)


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


# 票住哪裡:兩個位置都算。**做事的是「已 commit」那個條件,不是資料夾名字。**
# 實測(票 24):agent-gates 的票在進版控的 docs/tickets/,而 .scratch/ 被 gitignore;
# 三個下游 repo 反而把 .scratch/ 進版控。同一個豁免位置,上游不受審查、下游受審查。
# 綁死任一邊都會在另一邊失效,而失效的方向是「找不到宣告 = 不豁免」——
# fail-closed,但擋的是做對事的人,那種規則最後會被整條關掉(F-031)。
TICKET_DIRS = (".scratch/%s/issues", "docs/tickets/%s")

_UNTESTED_PREFIX = "**Untested by decision:**"


def declared_untested(text):
    """從票的內容取出宣告的模組名。沒有宣告回 None。

    抽出來是因為前哨與提交兩條路徑都要解析它,而**原本各有一份副本** ——
    兩份會分岔,而分岔在豁免判定裡的後果是一邊放行一邊擋(ADR 0003)。
    """
    for line in text.splitlines():
        if line.startswith(_UNTESTED_PREFIX):
            raw = line.split(":**", 1)[1]
            return {m.strip() for m in raw.replace("、", ",").split(",") if m.strip()}
    return None


def head_blob(rel_path):
    """這支檔案**在 HEAD 的內容**(bytes)。不在 HEAD 或問不到回 None。

    「在不在 HEAD」與「內容是什麼」是同一次查詢,所以只有一個入口 ——
    `head_content_hash` 與豁免宣告的判定共用它,不各自呼叫一次 git(F-080)。

    parent 問不到時**再**問 submodule(見 `submodule_head_blob`)。順序是刻意的:
    一般路徑維持單次 git 呼叫,gitlink 才多付探測的錢。
    """
    try:
        out = subprocess.run(["git", "cat-file", "blob", "HEAD:" + rel_path],
                             cwd=ROOT, capture_output=True)
    except Exception:
        return None
    if out.returncode != 0:
        # 不在 HEAD(新建未提交)、gitlink 底下、或 git 不可用 —— 只有中間那種有救
        return submodule_head_blob(rel_path)
    return out.stdout


# git tree 的 mode 是**封閉集合**,所以用枚舉不用 pattern:
# 040000 目錄 / 100644 一般檔 / 100755 可執行檔 / 120000 symlink / 160000 gitlink。
# 「比對的漏是未知的,枚舉的漏是不存在的」(CLAUDE.md 常駐檢查項、F-087)。
GITLINK_MODE = "160000"


def is_gitlink(prefix):
    """HEAD 的樹裡,這個前綴是不是一格 submodule。問不到一律 False。

    判定看 **tree 的 mode**,不讀 `.gitmodules` —— mode 是 git 自己的權威,
    而 `.gitmodules` 可能缺席、可能過期,拿它當來源就是「以錯的來源決定可見範圍」。
    """
    try:
        out = subprocess.run(["git", "ls-tree", "HEAD", "--", prefix],
                             cwd=ROOT, capture_output=True)
    except Exception:
        return False
    if out.returncode != 0:
        return False
    line = out.stdout.decode("utf-8", "replace").strip()
    return line.split(" ", 1)[0] == GITLINK_MODE if line else False


def submodule_head_blob(rel_path):
    """路徑落在 gitlink 底下時,改問**那個 submodule 自己的 HEAD**。讀不到回 None。

    parent 的樹在 gitlink 那一格存的是一個 commit id,不是子樹,所以
    `git cat-file blob HEAD:sub/foo.py` 一律 fatal。於是 `head_content_hash` 回 None,
    而 R3 的兩個合格出口(`impl_exists is False` / `impl_hash == head`)
    對 submodule 底下的**既有檔案**同時走不到 —— 永遠不合格,而唯一出口
    legacy 清單只減不增且入場券綁 parent 的樹,等於沒有出口(票 41、F-088)。

    這個缺席**完全無聲**:「gitlink 讀不到」與「新建未提交」在 `head_blob` 裡
    共用同一個回傳值 None,所以規則看起來還在,實際上對整個 submodule 失效。

    **委派的錨點是 submodule 的 HEAD,不是 parent 記錄的那個 gitlink sha。**
    紅燈紀錄的 impl_hash 取自工作樹,而工作樹跟著 submodule 的 HEAD 走;
    parent 的指標只在有人 bump 時才動,拿它當錨會讓「submodule 內已提交、
    parent 還沒 bump」這個最常見的中間狀態永遠對不上。

    **委派之後仍讀不到 -> None -> 呼叫端照舊當作不合格。** 這條路徑是「多開一條
    讀取管道」,而多開一條管道最便宜的寫法就是失敗時放行 —— 那會把一個
    「永遠擋」的缺陷換成「永遠放行」的缺陷,後者測試全綠、訊息什麼都不說。
    """
    parts = rel_path.replace("\\", "/").split("/")
    for i in range(1, len(parts)):                   # 前綴由近而遠,巢狀 submodule 取最外層
        if not is_gitlink("/".join(parts[:i])):
            continue
        sub = os.path.join(ROOT, *parts[:i])
        try:
            out = subprocess.run(["git", "-C", sub, "cat-file", "blob",
                                  "HEAD:" + "/".join(parts[i:])],
                                 cwd=ROOT, capture_output=True)
        except Exception:
            return None
        return out.stdout if out.returncode == 0 else None
    return None


def committed_declaration(rel_path):
    """票**在 HEAD 的那一版**宣告了哪些模組。票不在 HEAD 回 None。

    **讀的是已提交的內容,不是工作樹的內容。** 兩者的差別就是這條規則的全部:
    工作樹的檔案是代理人在被擋當下造得出來的,HEAD 的內容不是
    (要改它得產生一個 commit,而 commit 會出現在 diff、review 與 clone 裡)。

    只驗「路徑有沒有被 commit 過」不夠 —— 那樣可以先 commit 一張空票,
    再把宣告加在工作樹上。**條件是「這一行宣告已經在 HEAD 裡」。**
    """
    raw = head_blob(rel_path)
    if raw is None:
        return None
    return declared_untested(raw.decode("utf-8", "replace"))


def ticket_untested_modules(feature, ticket_id):
    """讀票裡「**Untested by decision:**」宣告的模組名。

    豁免不是 gate.py 自己開的後門 —— 它去讀一個**前一站產物裡已經存在的決定**。
    要新增豁免必須回頭改票,那是看得見、會被審查的動作。

    **「看得見」的定義是「已經 commit」,不是「檔案存在」**(票 24)。
    原本用 `os.path.exists()`,於是被擋住的當下建一個檔、寫一行宣告,豁免就到手 ——
    不會出現在任何 diff、任何 review、任何 clone 裡。理由與實作對不上。
    改成綁 HEAD 之後,那條路要先產生一個 commit,而那正是「會被審查」的意思。
    形狀抄 `check_legacy_list`(綁 go-live 樹),理由同一個:**無法自我服務**。

    宣告不存在、或票還沒 commit = 不豁免(fail-closed)。
    """
    if not feature or not ticket_id:
        return set(), None
    for tmpl in TICKET_DIRS:
        d = tmpl % feature
        abs_d = os.path.join(ROOT, d.replace("/", os.sep))
        if not os.path.isdir(abs_d):
            continue
        for name in sorted(os.listdir(abs_d)):
            if not name.startswith(str(ticket_id)):
                continue
            rel = "%s/%s" % (d, name)
            mods = committed_declaration(rel)
            # 票在磁碟上但不在 HEAD、或在 HEAD 但沒有宣告 —— 兩者都不豁免。
            # 仍然回傳票的路徑,訊息才說得出「看的是哪一張票」。
            return (mods or set()), rel
    return set(), None


def logged_exemption_backed(rel_path, base):
    """commit 時 ticket_id 已清空(一輪做完站別會往前走),改查豁免紀錄。

    但**不採信紀錄本身** —— 回頭打開它指名的票,確認那張票真的列了這個模組。
    紀錄只是索引,票才是決定。這樣偽造一行紀錄沒有用,票對不上就擋。

    **票也必須在 HEAD 裡**(票 24)。只修前哨那一半沒有用 ——
    留著這一半就是留一條繞道:在被擋當下造一張票、再讓提交時來認它。
    豁免的兩個時點要綁同一個條件,否則鬆的那一邊定義了整條規則。
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
        mods = committed_declaration(rec.get("declared_in") or "")
        if mods and base in mods:
            return True
    return False


FRICTION_LOG = os.path.join(ROOT, "docs", "agents", "friction-log.md")

# 發號用的標題行:`## F-123 …`、`## TSI-038 …`。
# **前綴必須是字母、號碼必須緊接在 `## ` 之後** —— 這兩個條件一起,
# 把「發一個號」與「提到一個號」分開:
#   `## F-118 甲`                 -> 發號,算
#   `## 併記於 F-118(…):乙`      -> 提到,不算(號碼不在開頭)
#   `見 F-005 與 F-005 的討論`     -> 提到,不算(不是 `## ` 開頭)
# 本檔自己就有一段 `## 併記於 F-118(…)`,它刻意寫成這樣正是為了不被本條誤判。
_FRICTION_HEADING = re.compile(r"^##\s+([A-Za-z]+-\d+)(?:\s|$|[^\w-])")


def check_friction_numbers(path=None):
    """權威層規則(票 83):同一份 friction log 裡不得有兩個相同的號。

    **它已經撞過一次**(2026-08-26):兩個視窗各發了一個 `F-122`,
    兩次都經過 pre-commit、兩次都綠。抓到它靠的是有人為了發下一個號去查最大號,
    順手看到重複 —— **下一次沒有人去查最大號時,它不會被發現。**

    ## 為什麼這一條適合進權威層(判準寫死,免得被拿去論證別的)

    **零誤報**(兩個一樣的號就是撞號,沒有灰色地帶)、
    **零判斷**(不必理解那兩則寫了什麼)、**極便宜**(一次掃描 + 一個 dict)。

    對照:stale status 偵測器**不該**用同一個理由進權威層 —— 它要判
    「票面說的與實際做的一不一致」,而「實際做了什麼」本身要**推論**,
    **推論會錯,而錯在權威層等於擋住做對事的人**,那種規則最後會被整條關掉。

    > **進權威層的門檻不是「重要」,是「零誤報 + 零判斷 + 便宜」。**

    ## 範圍:只查重複

    **不查連號** —— 缺號合法(後到者改號會留下空洞,見發號規則第 4 節)。
    **不查格式**、**不查跨 repo**(下游用自己的前綴,`TSI-001` 與 `F-001`
    是不同的字串,天然不衝突)。**一條檢查一件事** ——
    混進一個會誤報的子判定,整條的可信度就跟著它走。

    **fail-closed**:讀不到一律當違規,不當作乾淨。
    """
    target = path or FRICTION_LOG
    try:
        with io.open(target, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except Exception as e:
        return ["[R9] 讀不到 friction log(%s):%s\n"
                "     讀不到一律當違規,不當作乾淨 —— 一份掃不到的清單給不出綠燈。"
                % (rel(target), e)]
    seen = {}
    dupes = {}
    for lineno, line in enumerate(lines, 1):
        m = _FRICTION_HEADING.match(line)
        if not m:
            continue
        num = m.group(1)
        if num in seen:
            dupes.setdefault(num, [seen[num]]).append(lineno)
        else:
            seen[num] = lineno
    out = []
    for num in sorted(dupes):
        at = "、".join("第 %d 行" % n for n in dupes[num])
        out.append(
            "[R9] %s 裡的 %s 發了兩次以上(%s)。\n"
            "     處置照發號規則第 4 節:**後到者改號**(以 commit 順序為準),\n"
            "     原號留痕、引用一併改指。原號不回收。\n"
            "     缺號是合法的,所以改號留下的空洞不必補。"
            % (rel(target), num, at))
    return out


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
    raw = head_blob(rel_path)            # 取 HEAD 內容只有一個入口(F-080)
    if raw is None:
        return None
    try:
        return _redlight().content_hash(raw)          # 雜湊定義只有一份(F-058)
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

    **先解 `..` 再比對**(framework-updates/82,`F-051`):`top` 取的是第一段,
    而 `docs/../pkg/thing.py` 的第一段是 `docs` —— 判成非原始碼,**R2/R3 不管它**。
    方向是 fail-open:**該管的檔案不被管**。
    判準與 `g1_guard._is_scratch()` 那一句逐字相同,而那句話寫在別的模組裡 ——
    **同一份判準寫在 A 模組的註解裡,不會讓 B 模組變安全。註解不是機制。**

    ⚠ **這一層不是唯一的一層。** 生產上唯一的呼叫點餵進來的 `r` 來自 `rel()`,
    而 `rel()` 的 `abspath` 已經把 `..` 收掉了;另一個消費端吃的是
    `git diff --cached --name-only`,git 的輸出也是正規化的。
    **所以本函式修的是契約,不是一個活著的洞** ——
    而兩層都在的意義是「哪一層失效都還有另一層」,
    那件事由 `TestBothLayersNormalizeAndNeitherIsLoadBearingAlone` 守著。
    """
    r = rel_path.replace("\\", "/")
    if r:
        r = posixpath.normpath(r)
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


PROVENANCE = os.path.join(ROOT, ".dev", "provenance.jsonl")   # 控制,不是證據

# 上游 repo 在**這台機器上**的位置。住使用者層、由人維護、gate 唯讀,
# 與 SHADOW_MAX 的安全閥同款(ADR 0012 的乙案形狀)。
#
# **不寫進 provenance.jsonl** 有兩個各自獨立的理由:
#   去識別化 —— 那是本機設定,不該跟著 commit 送進版控
#   不可自助 —— 欄位一旦可寫,指向一個自己控制的 repo 就能造出任意「上游物件」,
#               控制就不再是控制。放進 G1 保護清單之後 agent 改不動它。
UPSTREAM_ROOTS = os.path.join(os.path.expanduser("~"), ".claude",
                              "upstream-roots.txt")


def read_upstream_root():
    """讀上游指標。回傳路徑或 None。**任何問題一律 None(= 沒有豁免)。**

    格式:恰好一行 `UPSTREAM_ROOT=<絕對路徑>`;`#` 註解與空行忽略。
    多行、少行、認不得的行 -> None。與 `read_shadow_clamp()` 同一套紀律。

    用 `utf-8-sig`:PowerShell 的 `Set-Content -Encoding utf8` 寫的是帶 BOM 的
    UTF-8,BOM 黏上鍵名就解析失敗 —— 而 fail-closed 系統的故障是隱形的,
    輸入端的坑要在進門前排掉。
    """
    try:
        lines = io.open(UPSTREAM_ROOTS, encoding="utf-8-sig").read().splitlines()
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
            return None          # 不認得的行 -> 壞掉 -> fail-closed
    return vals[0] if len(vals) == 1 else None


def upstream_backed(rel_path):
    """這個檔案是不是「與上游那個 commit 的物件逐位元組相同」的同步成品。

    要解的問題:下游 repo 收到 sync 帶進來的實作時,R3 要求本地紅燈紀錄,
    而**紅綠燈迴圈在上游** —— 下游拿到的是成品,它從來沒有機會讓那些測試
    在實作不存在時紅過。legacy 名單只減不增,正確地不是出路(那是給機制
    上線前的既有碼,不是給新收到的成品)。

    判準:**與上游那個 commit 的物件逐位元組相同 ⇒ 紅燈責任在上游。**

    **provenance 是控制,不是證據,所以不得可自助。** 判定一律以
    `git show <commit>:<path>` 取上游物件的內容自己算雜湊,
    **不採信 provenance 檔案裡宣稱的 hash** —— 那個欄位是給人看的。
    手寫一筆 provenance 造不出一個上游沒有的 blob:偽造需要改上游,
    不是改本地檔案。這是「豁免條件必須無法自我服務」的第五次出現
    (閘門自我修改、票宣告接縫、legacy 清單、R3 的 HEAD 錨點,以及這裡)。

    雜湊前正規化行尾:`git show` 給的是物件裡的位元組(LF),
    工作樹在 autocrlf 的機器上是 CRLF,不正規化的話永遠不相等(ADR F-0013)。

    **fail-closed**:沒有紀錄、讀不動、上游問不到、內容對不上 —— 一律 False。
    """
    rec = None
    try:
        for line in io.open(PROVENANCE, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("path") == rel_path:
                rec = r          # 取最後一筆:同一個檔案可能被同步過多次
    except FileNotFoundError:
        # **「沒有這個檔」是正常狀態,不是錯誤** —— 這個 repo 從來沒同步過東西。
        # 歸進「讀不動」的話,訊息會把一個正常情況說成故障,
        # 而人會去查權限與路徑(票 26 那個「讀不到清單」的同型錯誤)。
        rec = None
    except Exception as e:
        return False, ("provenance 紀錄檔讀不動(%s):%s\n"
                       "     檔案在但解析不了 —— 那與「沒有同步歷史」是兩件事。"
                       % (rel(PROVENANCE), e))
    if not rec:
        return False, ("%s 沒有 provenance 紀錄 —— 它不是同步進來的成品,"
                       "所以紅燈責任在本地。" % rel_path)

    # **位置一律取自指標檔,不看紀錄裡的 upstream_root。**
    # 紀錄是可寫的;判定要走一個 agent 動不了的來源,否則指向一個自己控制的
    # repo 就能造出任意「上游物件」——「宣稱的 hash 不採信」是同一個原則。
    root = read_upstream_root()
    commit = rec.get("upstream_commit")
    upath = rec.get("upstream_path") or rel_path
    # **兩個分支拆開**(票 13 C):修法不同就不能共用一句話 ——
    # 前者要去修指標檔,後者要去修 sync 產出的紀錄。
    if not root:
        return False, ("上游指標檔不可用(讀不到或格式不對):%s\n"
                       "     格式是恰好一行 `UPSTREAM_ROOT=<絕對路徑>`。\n"
                       "     (該層無法再細分原因 —— 待後續)"
                       % rel(UPSTREAM_ROOTS))
    if not commit:
        return False, ("provenance 紀錄缺 `upstream_commit` 欄位 —— "
                       "沒有基準點就無從比對。這是 sync 產出的紀錄有問題,"
                       "不是指標檔的問題。")
    try:
        out = subprocess.run(["git", "-C", root, "show",
                              "%s:%s" % (commit, upath)], capture_output=True)
        if out.returncode != 0:
            return False, ("上游那個物件問不到:`%s:%s`(上游 %s)。\n"
                           "     commit 或 upstream_path 對不上上游的樹。"
                           % (commit[:12], upath, root))
        with io.open(os.path.join(ROOT, rel_path.replace("/", os.sep)), "rb") as f:
            local = f.read()
        rl = _redlight()
        if rl.content_hash(out.stdout) == rl.content_hash(local):
            return True, None
        return False, ("內容與上游物件**漂移**了(不再逐位元組相同)。\n"
                       "     豁免的判準就是「相同」—— 改過一個位元組,"
                       "紅燈責任就回到本地。")
    except Exception as e:
        return False, "比對上游物件時出錯(%s)—— 問不到答案一律不豁免。" % e


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
        # **印出實際查找的絕對路徑**(票 31 / #10)。
        # `.dev` 打成 `.dve` 時,`git status` 看不見(整個目錄被 gitignore,
        # 新目錄同樣被 ignore),而訊息只說「讀不到」——
        # 於是人對著一個**存在的、名字差一個字母**的目錄找不存在的檔案。
        # 那條路徑本身就是證據:一眼看到 `…\.dve\pipeline.json` 就知道了。
        #
        # **路徑放第二行之後,不放第一行。** 它含使用者名稱,而 `log_shadow`
        # 只把訊息的**第一行**寫進 `.dev/shadow-log.jsonl`(持久檔)——
        # 放第一行的話,每一次影子攔截都會把使用者名稱寫進檔案。
        # 人看得到,證據檔存不到。
        return ("[R2/fail-closed] %s:讀不到流程狀態(%s)。\n"
                "     不知道停在哪一站,不等於停在 idle —— 後者在提交時是放行的。\n"
                "     實際查找的位置:%s\n"
                "     （目錄名打錯時這條路徑就是證據 —— `.dev` 與 `.dve` 差一個字母,\n"
                "      而狀態目錄被 gitignore,`git status` 不會告訴你。)\n"
                "     修好 pipeline.json 再繼續。" % (r, rel(PIPELINE), PIPELINE))

    writable = writable_stage_ids(stages)

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
        first_writable = next((i for i, s in enumerate(stages) if _declares_src_write(s)), len(ids))
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
        # 同步成品:與上游該 commit 的物件逐位元組相同 -> **R3 整條**責任在上游
        # (ADR F-0014、票 20)。
        #
        # 原本只豁免紅燈半,前半的正當性寫著「同步本來就會把測試一起帶過來」——
        # **那個前提對上游自己不出貨測試的檔案為假**:`g1_verify.py`、
        # `shadow_review.py`、`verify_gates.py` 在上游 `tests/` 就沒有對應檔案,
        # 再同步幾次都一樣。而下游沒有合法解:legacy 只減不增、
        # 自己補測試與「責任在上游」相衝、手寫豁免是自助。
        #
        # 判準是責任歸屬,不是方便:
        # **下游不得對進口成品要求比上游對自己更多的紀律。**
        # 而且這個窗會自己關 —— 上游哪天補了測試,sync 就把它帶下去,
        # 下游的 R3 前半自然成立,零下游動作。
        #
        # 邊界不變:漂移一個位元組就兩半都回來;沒有證的本地碼完全照舊;
        # **不碰 R2**(票 10);**不碰 R8**(它在前面,進口成品 import research 照樣擋)。
        # **必須解包。** `upstream_backed` 回的是 `(bool, reason)`,
        # 而 `(False, "…")` 在 `if` 裡**是真的** —— 忘了解包的話,
        # 每一個同步進來的檔案都會拿到豁免,fail-closed 整條翻成 fail-open,
        # 而測試全綠、訊息什麼都不說。這是簽名改動最貴的失敗方式(票 13 C)。
        prov_ok, prov_why = upstream_backed(r)
        if prov_ok:
            note_exemption(exemptions, r, base, ticket,
                           "docs/adr/F-0014-upstream-provenance.md",
                           reason="upstream-provenance")
            return None
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


def _same_path(a, b):
    """兩個路徑指的是不是同一個地方。**正規化分隔符與大小寫再比。**

    指標檔寫的是 `UPSTREAM_ROOT=C:/projects/agent-gates`(正斜線,由人手維護),
    而 `ROOT` 在 Windows 上是反斜線。不正規化的話,錨在它**唯一該生效的 repo**
    上永遠比不中 —— 而那個失效是**靜默**的:規則還在、還被呼叫、永遠回「沒事」。
    那正是 F-042 家族(守衛的「不在」與守衛的「放行」長得一模一樣)。
    """
    try:
        return (os.path.normcase(os.path.abspath(a)) ==
                os.path.normcase(os.path.abspath(b)))
    except Exception:
        return False


def upstream_shadow_violation():
    """**上游 repo 不得處於影子狀態。** 回 `(違規訊息 or None, 說明 or None)`。

    票 89 第 1 條(來源:`docs/audits/2026-08-28-f110-inventory.md` 第 1 條)。

    ## 要防的事

    `.dev/shadow.json` 存在 -> `shadow_active()` 為真 -> 整個上游閘門
    **從「擋」退回「只記不擋」**。而它不會有任何跡象:
    **那不是錯誤狀態,那是影子模式的正常狀態。**
    票 49 第一階段(R7 攔截帳本)整個建立在「上游全程 enforce」這個前提上 ——
    這一項一旦被好心補上,那本帳從此一筆都不會再長,而它看起來仍然正常。

    `docs/machine-init.md` 第 3 項與 `docs/handover/2026-09-11.md` 那一格
    都逐字寫了「不會有東西叫」。**本函式就是那個「東西」。**

    ## 為什麼不給它一個 R 編號

    R 系列問的是「**這一次寫入 / 這一個檔案**允不允許」—— 逐檔、逐次。
    本條問的是「**這個 repo 現在的狀態下,閘門還算不算數**」,
    與 `authoritative_layer()` 那個通知同一類:**前提,不是規則**。
    硬塞一個 R 編號會讓 `rule_codes()` 多出一條逐檔規則,而它不是那種東西。

    ## 錨,以及它宣告的守備範圍

    錨是 `read_upstream_root() == ROOT`。**它擋得住「好心補上」,
    擋不住「決定要關掉」** —— `~/.claude/upstream-roots.txt` 目前沒有 G1 保護,
    改一行就能讓本條對本 repo 失效。

    **那是宣告的守備範圍,不是缺陷。** 「好心補上」的形狀是:換機器時逐項對照
    備份清單,而一個**刻意不存在**的檔案與一個**忘記複製**的檔案在清單上
    長得一模一樣,於是把它建起來 —— 那個人不會去改錨,他根本不知道有這條規則。
    已知缺口有票號(**票 89 自己**),出口是第二階段(git 背書的錨,時鐘 9/11)。

    ## 三個分支,以及為什麼中間那個不能反過來

    - **錨讀不到** -> **不擋,但出聲**。fail-closed 會擋掉每一個沒有
      `upstream-roots.txt` 的下游(那在下游是常態缺席),那是災難;
      fail-open 則是靜默失效。**印一行**把靜默拿掉,而不引入誤擋。
    - **錨讀得到但不是本 repo** -> **放行,而且不出聲**。
      `shadow.json` 存在是 ADR 0012 設計的**合法狀態**;
      一條「一律擋」的規則會在三天後擋到每一個開了影子的下游,
      **而它會讓正控全綠** —— 所以反控是硬條件,不是加分項。
    - **錨指向本 repo 且檔案在** -> **擋**。

    沒有 `shadow.json` 時**兩個方向都安靜** —— 一個每次都印的提醒
    會訓練人忽略它(F-031),而那時本來就沒有事情要說。
    """
    if not os.path.exists(SHADOW_STATE):
        return None, None

    root = read_upstream_root()
    if root is None:
        return None, (
            "[六站閘門/未生效] 這個 repo 有 %s,而讀不到上游錨 %s ——\n"
            "     「上游不得處於影子狀態」這條檢查**未生效**,本次沒有判定。\n"
            "     (不擋:錨在下游是常態缺席,擋了會擋掉每一個下游。\n"
            "      印這一行是因為靜默失效與「檢查過沒事」長得一模一樣。)\n"
            % (rel(SHADOW_STATE), rel(UPSTREAM_ROOTS)))

    if not _same_path(root, ROOT):
        return None, None

    return (
        "[六站閘門/上游影子] 上游 repo 出現 %s ——\n"
        "     整個閘門會從「擋」退回「只記不擋」,而那不是錯誤狀態,\n"
        "     是影子模式的正常狀態,所以除了這一行以外沒有東西會說。\n"
        "     票 49 的 R7 攔截帳本建立在「上游全程 enforce」上:\n"
        "     這個檔存在的每一分鐘,那本帳都不會成長,而它看起來仍然正常。\n"
        "     上游錨:%s = %s\n"
        "     這個檔在上游是**刻意不存在**的 —— 見 docs/machine-init.md 第 3 項。\n"
        % (rel(SHADOW_STATE), rel(UPSTREAM_ROOTS), root)), None


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


# ── 指令指紋(票 68)────────────────────────────────────────────────────
#
# **記指紋,不記原文。** 三個各自獨立的理由:
#   1. 指令原文含路徑,而路徑含使用者名、專案名、真實資料夾名(F-082 / F-085 那族)
#   2. `shadow-log.jsonl` **不進版控**,靠週級人工備份 ——
#      備份會被複製到別處,而複製讓洩漏面跟著擴散
#   3. 它是 G1 的保護對象 —— **一個檔案越難刪改,往裡面寫東西就越要保守**
#
# 由來:R7 202 筆裡有 72 筆判不出真陽/誤報,因為紀錄裡沒有指令。
# **本欄救不了那 72 筆**(它們的指令已經不存在),它是為下一次評估而做的。

CMD_VERB_UNKNOWN = "<其他>"

# **認得的動詞,枚舉。** 認不得就記 `CMD_VERB_UNKNOWN`,不照抄第一個 token ——
# 那個 token 本身可能就是路徑(`"C:/…/app.exe" run`),照抄等於把
# 「不記原文」讓掉一半。
#
# **這不是退回白名單。** CLAUDE.md 那條講的是**閘門**(列出不管的、其餘全擋);
# 這裡是**輸出的遮罩**,而遮罩的 fail-closed 方向是**少講** ——
# 所以 deny-by-default 才是對的方向,同 `leak-patterns.txt` 檔頭自己註明的
# 「方向與其他清單不同」。漏一個動詞的代價是少一格資訊;多印一個的代價是洩漏。
CMD_VERBS = frozenset("""
    python python3 py pip pytest node npm npx
    git gh
    cd ls cat head tail grep find wc sed awk diff sort uniq od
    echo printf touch cp mv rm mkdir chmod ln
    sh bash pwsh powershell
    curl wget tar zip unzip
    set-content out-file add-content new-item remove-item copy-item move-item
    get-content get-childitem select-string test-path
""".split())


def command_verb(command):
    """指令的第一個 token,**只在它是認得的動詞時才回傳它本身**。"""
    parts = (command or "").strip().split()
    if not parts:
        return None
    head = parts[0].strip().lower()
    return head if head in CMD_VERBS else CMD_VERB_UNKNOWN


def log_shadow(msg, at_commit, command=None):
    """把一筆『本該擋』寫進 shadow-log(證據)。append-only。

    `command` 給得出來時,額外記**指紋**(sha256 / 動詞 / 長度),**不記原文**。

    **給不出來時三個欄位一律缺席,不填 `N/A`** —— `N/A` 是一個值,
    而值會被統計、被比對、被當成「有記錄」。R1–R6 的觸發物是檔案寫入不是指令,
    **不要為了欄位齊整而編造一個指令**(票 68)。
    """
    rec = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "rule": rule_of(msg), "at_commit": at_commit,
           "verdict": "would-block",
           "message": (msg or "").splitlines()[0] if msg else ""}
    rec.update(cmd_fingerprint(command))
    try:
        _append_jsonl(SHADOW_LOG, rec)
    except Exception:
        pass
    return rec


# ── 攔截帳本(票 49 第一階段)──────────────────────────────────────────
#
# **`gate-exemptions.jsonl` 是豁免帳本,不是攔截帳本。** `log_exemptions()`
# 第一行是 `if not bucket: return`,而 `bucket` 是「這次判定**用到的豁免**」——
# 空的就直接返回,**而沒有動用任何豁免的單純攔截是最常見的那一種**。
# 它回答的是「哪些後門被走過」,不是「閘門今天攔了幾次、攔了什麼」。
#
# R7 更極端:enforce 分支只有 `_err`,**一筆都不寫**。上游沒有 `shadow.json`
# → 全程 enforce → **每天在產生無紀錄的攔截**。而 9/15 那份 0.0% 假陽率是拿
# 量化的影子紀錄算的,**上游的 R7 誤擋結構上不可能進入那個母體**。
#
# **不併進 `gate-exemptions.jsonl`,兩個理由都是硬的:**
#   1. **schema 不相容** —— `exemption_record()` 的鍵是豁免形狀的
#      (`file` / `module` / `declared_in` / `reason`),全部來自 `ex` 那個豁免物件。
#      一次 R7 攔截**沒有 `file`**(它的觸發物是指令),四個鍵全部填不出來。
#   2. **會弄壞 `ledger_verify` 的鏈驗證** —— 那支工具逐筆讀
#      `content_hash` → `result_hash` 串成鏈、逐段驗接續(v2 的存在理由)。
#      插進一筆沒有這兩個欄位的紀錄,鏈就斷在那裡,而那條鏈是
#      票 58 / 票 47 三次有界突變的收尾依據。
#
# > **把兩種語意塞進同一個檔,省下的是一個檔名,付出的是一支已經在用的驗證工具。**
#
# **不進版控**(裁決 2026-08-26),改列進控制檔備份清單第 10 處。三個理由:
# (a) `message` 全文含本機路徑,而開源在即 → 進版控等於天天撞 `leak_scan`,
#     那不是「記了」是「記了但推不上去」,**而它看起來像有**;
# (b) 誤擋頻率未知,大量 diff 噪音會讓人先關掉紀錄,再也量不到頻率 ——
#     **它要量的東西,正是會導致它被關掉的東西**;
# (c)「換機器會沒」該由備份解決,**不該用版控代替備份**。
# 這不是永久裁定:日後要進版控,前置是 `message` 先做路徑遮罩。

INTERCEPT_LOG = os.path.join(ROOT, ".dev", "intercepts.jsonl")   # 證據(基底檔名)
INTERCEPT_SUMMARY = os.path.join(ROOT, ".dev", "intercepts-summary.jsonl")

# 保留原始紀錄的月數:**當月 + 前一月**。
# 這是**推導出來的,不是挑的**:只留當月的話,每月 1 號手上幾乎沒有原始資料;
# 留到前一月,則任何時點都保證**至少有一個完整日曆月**可分析。
# **它是滿足「任何時點 ≥1 完整月」的最小值。**
# 特別寫出推導,是因為這條線上剛出過事 —— `F-124`:`MAX_FALSE_POSITIVE_RATE
# = 0.05` 至今查不到出處,而它靠**被引用**取得權威。
# **一個沒有推導的常數,寫下的當天就開始變成傳說。**
INTERCEPT_KEEP_MONTHS = 2

# 摘要裡收容「沒有指令」那些紀錄的鍵。
# **與紀錄層面的規矩方向相反,而那是刻意的**:紀錄層面缺席不填 `N/A`
# (值會被統計、被當成「有記錄」);摘要**是統計**,漏掉它們會讓
# `sum(by_verb) < count` 而沒有人看得出差額去了哪。
CMD_VERB_ABSENT = "<無指令>"


def cmd_fingerprint(command):
    """指令的指紋三欄(票 68)。給不出來時回**空 dict**,不是三個 `N/A`。

    抽成函式是為了讓影子側與 enforce 側**算的是同一組欄位** ——
    9/15 評估要把兩邊的樣本合起來看,而兩份各自算的欄位會各自漂移
    (`F-125` 的形狀:同一個參數在兩處各自演化,而沒有東西會說話)。
    """
    if not command or not command.strip():
        return {}
    raw = command.encode("utf-8", "replace")
    # **不加鹽**:同一條指令在不同 repo 要對得起來。它是指紋不是密碼。
    return {"cmd_sha256": hashlib.sha256(raw).hexdigest(),
            "cmd_verb": command_verb(command),
            "cmd_len": len(command)}


def intercept_path(month):
    """某個月的攔截帳本路徑:`intercepts.jsonl` → `intercepts-2026-08.jsonl`。

    **月檔名從基底常數推出來,不另外寫一個常數** —— 測試與換機器的隔離
    只要蓋住 `INTERCEPT_LOG` 就蓋住整族,不必知道輪替怎麼命名。
    """
    stem, ext = os.path.splitext(INTERCEPT_LOG)
    return "%s-%s%s" % (stem, month, ext)


def _intercept_months():
    """磁碟上現有的月檔:`{"2026-08": 路徑}`。

    摘要檔(`intercepts-summary.jsonl`)**對不上這個形狀**,所以不會被當成
    月檔再滾一次 —— 那會把長期訊號吃掉,而且無聲。
    """
    stem, ext = os.path.splitext(INTERCEPT_LOG)
    pat = re.compile(r"^%s-(\d{4}-\d{2})%s$"
                     % (re.escape(os.path.basename(stem)), re.escape(ext)))
    folder = os.path.dirname(INTERCEPT_LOG) or "."
    out = {}
    try:
        names = os.listdir(folder)
    except OSError:
        return out
    for name in names:
        m = pat.match(name)
        if m:
            out[m.group(1)] = os.path.join(folder, name)
    return out


def _kept_months(now):
    """保留期內的月份集合。

    **用月序號減,不用天數減** —— 「今天減 30 天」在 2 月與 8 月給出不同答案,
    而跨年時「月份減一」會算出第 0 月。兩個坑都在這一行裡排掉。
    """
    n = now.year * 12 + (now.month - 1)
    out = set()
    for back in range(max(1, INTERCEPT_KEEP_MONTHS)):
        y, m = divmod(n - back, 12)
        out.add("%04d-%02d" % (y, m + 1))
    return out


def _summarised_months():
    """已經滾成摘要的月份。**滾動因此可以重跑而不重複計數** ——
    摘要寫成了但刪檔失敗時就會重跑。"""
    out = set()
    try:
        with io.open(INTERCEPT_SUMMARY, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if rec.get("month"):
                    out.add(rec["month"])
    except (IOError, OSError):
        pass
    return out


def _summarise_month(month, path, now):
    """一個月檔 → **每條規則一行**摘要。

    **明寫的取捨:滾動會丟掉個別紀錄的 `message` 全文與 `cmd_sha256`。**
    所以要拿來分類的月份,**必須在它被滾掉之前處理** ——
    這是一個真的損失,不是無痛壓縮。
    """
    tally = {}
    try:
        with io.open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if rec.get("kind") == "summary":
                    continue
                slot = tally.setdefault(rec.get("rule") or "?",
                                        {"count": 0, "by_verb": {}})
                slot["count"] += 1
                verb = rec.get("cmd_verb") or CMD_VERB_ABSENT
                slot["by_verb"][verb] = slot["by_verb"].get(verb, 0) + 1
    except (IOError, OSError):
        return []
    stamp = now.isoformat()
    return [{"kind": "summary", "month": month, "rule": rule,
             "count": s["count"], "by_verb": s["by_verb"], "rolled_at": stamp}
            for rule, s in sorted(tally.items())]


def roll_intercepts(now=None):
    """把超過保留期的月檔滾成摘要,**原始刪除**。回傳被滾掉的月份。

    **這是構造,不是排程或紀律** —— 在 `log_intercept()` 寫入前跑,
    所以沒有「要記得去整理」這件事。

    為什麼一定要有(核准附加條件 a,**必做不是可選**):它 append-only、
    不進版控,而 **enforce 下誤擋是常態**,所以它會一直長;而它是備份清單
    第 10 項、要**手動複製**到新機器 —— **一個越來越難複製的檔案,
    最後會被跳過。** 這是 `F-031` 的形狀換一個地方出現:F-031 是被煩到
    關掉規則,本則是被煩到跳過備份。**受害者不同,而後者不會有人發現**
    (規則被關掉時大家都知道;備份沒複製到,要到需要它的那天才知道)。

    **摘要不刪**:一行約 100 bytes、一年 12 行,不會成為複製的障礙,
    而它是「誤擋頻率隨時間怎麼變」唯一的長期訊號。
    """
    now = now or datetime.datetime.now(datetime.timezone.utc)
    keep = _kept_months(now)
    done = _summarised_months()
    rolled = []
    for month, path in sorted(_intercept_months().items()):
        if month in keep:
            continue
        if month not in done:
            for rec in _summarise_month(month, path, now):
                _append_jsonl(INTERCEPT_SUMMARY, rec)
        os.remove(path)
        rolled.append(month)
    return rolled


def log_intercept(msg, command=None, at_commit=False, now=None):
    """把一筆**真的擋下來**的攔截寫進當月帳本。append-only。

    欄位沿用票 68 已經定案的指紋三欄(`cmd_sha256` / `cmd_verb` / `cmd_len`),
    **不發明新的** —— 影子側與 enforce 側因此可以用同一組欄位對帳,
    9/15 評估時兩邊的樣本能合併看。**不記指令原文**(票 68 的裁決)。

    `message` 記**全文**(`log_shadow` 只記第一行):分類時要判「擋得對不對」,
    而**規則碼判不出來** —— 票 31:114 已經記過這一格,帳本存的是 `blocked_by`
    規則碼、不是訊息全文,於是判不出是哪一種擋。

    **失敗方向:記不下來仍然擋,但要多印一行說帳本壞了。**
    方向與 `log_exemptions` 相反、結論相同:那邊是「記不下來的豁免不算數」,
    所以 `SystemExit(2)`;這邊本來就要擋,所以**不改判定** ——
    但**不得靜默**,否則「擋了但沒記」會安靜發生,而那正是本票要消掉的東西。
    """
    now = now or datetime.datetime.now(datetime.timezone.utc)
    rec = {"ts": now.isoformat(), "rule": rule_of(msg),
           "at_commit": bool(at_commit)}
    rec.update(cmd_fingerprint(command))
    rec["message"] = msg or ""

    # 整理失敗**不得吃掉這一筆** —— 記錄比整理重要。但也不得無聲:
    # 沒被收掉的月檔會一直長,而那正是輪替要防的事。
    try:
        roll_intercepts(now=now)
    except Exception as e:
        _err("[閘門/帳本] 攔截帳本輪替失敗(%s):%s\n"
             "     這一筆仍然會記 —— 記錄比整理重要。但舊月檔沒有被收掉,\n"
             "     它會一直長,而一個越來越難複製的檔案最後會被跳過。\n"
             % (rel(INTERCEPT_LOG), e))

    path = intercept_path(now.strftime("%Y-%m"))
    try:
        _append_jsonl(path, rec)
    except Exception as e:
        _err("[閘門/帳本] 攔截無法記帳(%s):%s\n"
             "     **這次仍然擋** —— 記錄失敗不改判定,下面那條才是判定結果。\n"
             "     但這一次攔截沒有留下紀錄:R7 的誤擋率因此少一個樣本,\n"
             "     而 9/15 轉正要靠它。\n" % (rel(path), e))
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
    # **票 89:在任何規則之前。** 影子開著的那段期間,agent 的每一次寫入
    # 都已經不受 enforce 保護了 —— 等到 commit 才說已經太晚。
    up_v, up_note = upstream_shadow_violation()
    if up_note:
        _err(up_note)
    if up_v:
        _err("[六站閘門/前哨] %s" % up_v)
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
                # **只有這個呼叫點給得出 command** —— R7 是唯一以指令為觸發物的規則。
                # 其餘兩處(檔案寫入前哨、pre-commit)手上沒有指令,欄位缺席是對的。
                log_shadow(msg, at_commit=False, command=command)
                return 0
            # **記在 `_err` 之前**,而且刻意如此:記不下來要能影響輸出。
            # 放在後面的話,「擋了但沒記」與「擋了也記了」在終端機上長得一樣,
            # 而前者正是本票(49)要消掉的東西 —— 這一格是 R7 在 enforce 下
            # 唯一的紀錄,9/15 轉正的誤擋率要靠它才估得出來。
            log_intercept(msg, command=command)
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


def index_modes(cwd=None):
    """index 裡每條路徑的 mode。**判定依據是 index,不是檔案系統。**

    用 `os.path.isdir()` 判「這是不是 submodule」的話,問題就跑到磁碟上去了 ——
    而磁碟上的樣子隨時會變(目錄被搬走、submodule 沒 init、有人放了同名檔),
    **index 的 mode 才是 git 對「這一格是什麼」的答案**。

    問不到 -> `check_output` 丟例外 -> `mode_pre_commit` 當成「無法取得 staged
    檔案」擋下。fail-closed:問不到不等於「都不是 gitlink」。

    與 `.claude/portable/scanner.py` 的同名函式是**兩份實作**(兩者不共用程式碼:
    本檔隨 `.claude/hooks/` 安裝,scanner 屬 portable 掃描器骨架)。
    同缺陷的兩份實作必然漂開(F-058 家族),所以有一條測試釘住兩者對同一個 repo
    給出相同答案 —— `test_both_staged_listings_agree_on_a_gitlink`。
    """
    out = subprocess.check_output(["git", "ls-files", "--stage", "-z"],
                                  cwd=cwd or ROOT).decode("utf-8", "replace")
    modes = {}
    for rec in out.split("\0"):
        if not rec.strip():
            continue
        meta, _, path = rec.partition("\t")      # `<mode> <sha> <stage>\t<path>`
        fields = meta.split()
        if path and fields:
            modes[path] = fields[0]
    return modes


def gitlink_note(paths):
    """被跳過的 gitlink 進權威層報告。**跳過要看得見,而且要說出由誰守。**

    靜默跳過與「修好」之間差的就是這一段:讀報告的人要分得出
    「判定過、沒事」與「這一格不歸這裡判」。
    """
    return ("[六站閘門] 跳過 %d 格 gitlink(mode 160000),它們不是原始碼:\n"
            % len(paths)
            + "".join("     - %s\n" % p for p in paths)
            + "     那一格記的是一個 commit sha,**由內層 repo 自己的閘門守**。\n")


def staged_paths(cwd=None, gitlinks=None):
    """staged **檔案**清單。**用 -z(NUL 分隔),不是 --name-only + splitlines。**

    git 對非 ASCII 檔名預設回傳 C-quoted 路徑(`"docs/\\345\\217\\260….md"`),
    而下游 `replace("\\\\", "/")`(為正規化 os.path.relpath 的 Windows 反斜線而存在,
    本身正當)會把 escape 的反斜線一起換掉 —— 路徑徹底壞掉,`top` 不再是 docs,
    中文檔名的文件被判成原始碼、被 R2 誤擋。這是 F-042 那個編碼假設的第三次現身。

    不用 `core.quotePath=false`:它只關掉引號,檔名含換行或引號時仍有歧義。
    NUL 是唯一不可能出現在路徑裡的位元組 —— 結構上無歧義,不是剛好夠用。

    **gitlink(mode 160000)不是原始碼,不進判定清單**(票 42)。
    `--name-only` 對 submodule 條目回傳目錄路徑,而 `is_source_path()` 對一個
    沒有副檔名、top 又不在非原始碼清單裡的路徑回 True —— 於是一次純 bump 在
    `grill` / `spec` / `tickets` 被 R2 當成「提交原始碼」擋下(`research` 是
    範圍擋)。實測如此。**`implement` / `review` 放行是巧合,不是判定認得
    gitlink** —— 那兩站只是 R2 在提交時本來就不問的站別。

    而 R2 的擋下訊息**完全不提 gitlink**:使用者會去查站別,查不出所以然 ——
    訊息要說出是哪一個前提沒滿足,不是把人指向錯的方向(票 13)。

    修的範圍**只有「gitlink 不是原始碼」這一句**,`is_source_path` 的其他語意不動。

    `gitlinks`:呼叫端傳入的收集串列(形狀同 `check(..., exemptions=[])`),
    跳過的那幾格會 append 進去,由 `mode_pre_commit` 印進報告。
    **回傳型別不變** —— 不改成 tuple,理由見票 13 C(忘了解包會靜默翻成 fail-open)。
    """
    out = subprocess.check_output(
        ["git", "diff", "--cached", "-z", "--name-only", "--diff-filter=ACM"],
        cwd=cwd or ROOT).decode("utf-8", "replace")
    paths = [p for p in out.split("\0") if p.strip()]
    if not paths:
        return []
    modes = index_modes(cwd)
    kept = []
    for p in paths:
        if modes.get(p) == GITLINK_MODE:
            if gitlinks is not None:
                gitlinks.append(p)
            continue
        kept.append(p)
    return kept


def mode_pre_commit():
    """權威判定:掃 staged 檔案 + R4 副本一致性 + R5 第三軸掛載點。"""
    # **票 89:放在最前面,而且刻意不進 `violations`。**
    # 走一般那條路的話,影子開著時會被寫進 shadow-log 並回 0 ——
    # 而本條要偵測的**正是影子開著這件事**,於是它永遠不可能觸發。
    # 一條只在它不需要的時候才生效的檢查比沒有檢查更糟:它會被當成有守。
    up_v, up_note = upstream_shadow_violation()
    if up_note:
        _err(up_note)
    if up_v:
        _err("\n[六站閘門/pre-commit] commit 已擋下:\n\n  %s\n" % up_v)
        return 1
    gitlinks = []
    try:
        staged = staged_paths(gitlinks=gitlinks)
    except Exception as e:
        _err("[六站閘門] 無法取得 staged 檔案:%s\n" % e)
        return 1
    if gitlinks:
        _err(gitlink_note(gitlinks))
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
    violations += check_friction_numbers()
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
        # **不寫繞過方式**(票 13 B)。原本這裡是
        # 「如確定要略過:git commit --no-verify(會留下紀錄,請自行負責)」,
        # 兩個問題:
        #
        #   一、**enforcement 訊息不得提示自身的繞過方式。** 訊息要說出哪一個前提
        #       沒滿足(讓人去修),不是提供一條不必滿足前提的出口(讓人去繞)。
        #       前者把人推向修好,後者推向略過 —— 而被煩到的規則會被關掉,
        #       提示語等於幫它加速。
        #
        #   二、**「會留下紀錄」是假陳述。** `--no-verify` 在 git 裡不留任何痕跡:
        #       commit 上沒有標記、reflog 也不記。宣稱一個不存在的機制比不寫更糟 ——
        #       它讓人以為有事後對帳,於是更放心用。
        #
        # 真的需要逃生門的話,它要有**真的會留痕**的機制,而不是一句宣稱。
        _err("\n上面每一項都指出了是哪一個前提沒滿足 —— 修掉它們再提交。\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(mode_pre_commit() if "--pre-commit" in sys.argv else mode_hook())
