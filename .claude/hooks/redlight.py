# -*- coding: utf-8 -*-
"""紅燈紀錄 —— 讓「這個測試曾經紅過」不再只是宣稱。

R3 的原始規格是「對應測試檔存在 **且** 有紅燈紀錄」,實作只做了前半,
而且沒有任何東西發現它掉了(F-012)。只驗檔案存在的話,一個永遠跑不起來的
測試檔也能過關 —— 上一輪就是這樣:repo 有十七個測試檔而測試執行器根本沒安裝。

**時序判準不用任何時間戳。** 要問的不是「檔案何時出現」,而是
「紅燈發生時,這個實作存不存在」—— 那件事在紅燈那一刻可以直接觀測,不必事後推斷。
檔案系統時間會被複製與觸碰打亂、會被時鐘回撥影響,版控時間對未提交的新檔根本不存在;
兩者都在回答錯的問題。所以紀錄自己宣告當時實作存不存在,並記下雜湊。

紀錄是**證據**(消失即失去判定依據),放 .dev/;append-only,不覆寫 ——
覆寫會讓歷史消失,而斷言需要歷史。

**F-036 修訂(票 31,2026-08-14)**:上一句原本寫「放 .dev/ **並進版控**」,
而 `.gitignore` 忽略整個 `/.dev/` —— **註解描述了一個不存在的機制**,
實測 `git ls-files .dev` = 0。三處說法不一致(本檔、`gate.py`、`.gitignore`)。

本檔寫的這一份(`test-runs.jsonl`)屬**高流量**那一類:每跑一次測試就長,
進版控會讓每次測試都髒工作樹。裁決是**不進版控,存續歸 R5 的週級異地備份**;
帳本類(`gate-exemptions.jsonl` / `provenance.jsonl`)才進版控,
因為豁免史要可逐筆對帳。

**「證據不能消失」這個判準沒變,變的是達成它的手段不只版控一條。**

> 為什麼兩處註解拖到現在才一起改:開票那一批想同時改,結果 `gate.py` 改成功
> (它有 R2 自我修改豁免)、本檔被 R2 擋下(當時在 `tickets` 站)——
> **豁免的顆粒度是單檔,而約定的顆粒度是一組檔案。**
> 那個中間狀態看起來像疏忽,其實是規則造成的(見票 31 的證據註記)。
"""

import hashlib
import io
import json
import os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUN_LOG = os.path.join(ROOT, ".dev", "test-runs.jsonl")
PIPELINE = os.path.join(ROOT, ".dev", "pipeline.json")   # 紅燈發生時是哪一張票


def content_hash(raw):
    """實作內容的雜湊。**行尾先正規化再算。**

    這個值要拿去跟 git blob 的內容比對(R3 判「紅燈是不是對著改動前的碼發生的」),
    而工作樹與 blob 的行尾未必相同:`core.autocrlf=true` 的 Windows 上,
    工作樹是 CRLF、blob 是 LF。本 repo 目前靠 `.gitattributes` 的 `*.py text eol=lf`
    讓兩者相同 —— 但那個檔案**不在 portable-manifest 裡**,不保證跟著裝到別的 repo。
    少了它,兩邊 hash 永遠對不上,R3 對每一支既有檔案無條件擋:方向是 fail-closed,
    擋的卻是做對事的人,而那種規則最後會被整條關掉。

    判準不掛在一個沒被宣告帶走的檔案上 —— 正規化之後,行尾設定怎麼變都不影響判定。

    **同判準的另外兩份在 `.claude/portable/sync.py`**:`_norm`(經 `file_hash`)
    與 `_read`(經 `canon_drift`)。三份**刻意不共用**(票 42:權威層 import
    `portable/` 會多一個失效點,而閘門起不來的樣子跟沒裝一模一樣)。
    行為一致由 `tests/test_line_ending_parity.py` 釘住 —— **綁行為,不綁字面**。
    """
    norm = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(norm).hexdigest()


def current_ticket():
    """紅燈發生當下的票號。讀不到回 None。

    **讀不到就是 None,不猜。** 猜一個票號的話,猜中的那次會靜默解鎖
    一個根本沒有紅燈的修改 —— 而那正是這個欄位要防的事。
    """
    try:
        with io.open(PIPELINE, encoding="utf-8") as f:
            return json.load(f).get("ticket_id")
    except Exception:
        return None

# 測試檔名對應到實作檔名的搜尋範圍。與 R3 反向:R3 由實作找測試,這裡由測試找實作。
#
# 跳過清單是**明列**的,不是「所有點開頭的目錄」—— 後者會跳過 .claude/hooks/,
# 而閘門自己就住在那裡:實作明明存在,紀錄卻宣告 impl_exists=False,
# R3 拿這種紀錄去判定會無條件放行。又是一次「以錯的來源決定可見範圍」(F-019)。
#
# ⚠ `gate.NON_SOURCE_DIRS` 看起來像本清單的副本,**兩份刻意不同,合併會 fail-open**
# —— 那份問「會不會被執行」,本份問「反查實作時要不要進去」。票 114 B-3 實測:
# 把本份併過去會讓 `.scratch/` 底下的碼脫離站別限制(R7 的官方出口就指向那裡),
# 並讓 `gate.PROTOTYPE_RE` 靜默變死碼。
# 差集由 `tests/test_non_source_list_parity.py` 釘住 —— **對的是差集,不是相等。**
_SEARCH_SKIP = {".git", ".venv", "node_modules", "__pycache__", ".cache",
                ".scratch", ".dev", "tests", "docs", ".agents", "skills",
                "build", "logs", "assets", "tradingagents.egg-info"}


def find_implementation(test_file):
    """tests/test_foo.py -> 專案裡的 foo.py。找不到回 None。

    找不到不是錯誤:測試檔可以不對應單一實作(例如整合測試)。
    R3 只在「由實作反查」時才需要這個對應,方向相反時允許落空。
    """
    base = os.path.basename(test_file)
    if not base.startswith("test_") or not base.endswith(".py"):
        return None
    target = base[len("test_"):]
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in _SEARCH_SKIP]
        if target in filenames:
            return os.path.relpath(os.path.join(dirpath, target), ROOT).replace("\\", "/")
    return None


def record_run(test_file, passed, failed_tests):
    """追加一筆紀錄。回傳寫入的內容(方便呼叫端斷言)。"""
    impl = find_implementation(test_file)
    impl_path = os.path.join(ROOT, impl.replace("/", os.sep)) if impl else None
    exists = bool(impl_path and os.path.exists(impl_path))

    digest = None
    if exists:
        try:
            digest = content_hash(io.open(impl_path, "rb").read())
        except Exception:
            digest = None

    rec = {
        "test_file": test_file.replace("\\", "/"),
        "time": datetime.now(timezone.utc).isoformat(),
        "result": "green" if passed else "red",
        "failed_tests": list(failed_tests or []),
        # 在事件當下留下的事實,不是事後從時間戳推斷出來的
        "impl_file": impl,
        "impl_exists": exists,
        "impl_hash": digest,
        # 紅燈屬於**某一張票**,不是屬於某個檔案。少了這個欄位,
        # 「hash 對得上改動前的碼」單獨用會把 R3 從「永遠不合格」翻成「永遠合格」:
        # 一筆舊紅燈只要該檔案之後沒被提交過,就永久解鎖後續每一次修改。
        "ticket_id": current_ticket(),
    }
    try:
        os.makedirs(os.path.dirname(RUN_LOG), exist_ok=True)
        with io.open(RUN_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return rec


# ─────────────────────────────────────────────────────────────────────────────
# 票 145(M1-a)—— run 事實:一次 test run 跑了什麼、結果是什麼
#
# 上面的 `record_run()` 一筆 = (一個測試檔 × 一次結果),**帳本裡沒有「一次執行」**
# 這個實體 ⇒ 窄選、全部 skip、0 collected、根本沒跑,在帳本上長得一樣(票 139)。
# 本段補上那個實體。
#
# **另一本帳**(`.dev/test-sessions.jsonl`),不寫進 `test-runs.jsonl`:
#   - `gate.redlight_missing()`(R3,權威層)逐行讀 `test-runs.jsonl`,
#     `test_file` 命中而缺 `impl_exists` 就擋 —— 同檔混放會讓 R3 的解析面跟著變;
#   - 既有 8 欄紀錄**一筆都不改、不補欄位**(票 145〈三〉Backward compatibility 1–4)。
# 落點由 `root` 參數推出,不由模組常數推出 —— status 依 root 載入本檔讀取,
# 測試以 tmp root 寫入,三方對同一個 root 說的是同一本帳。
# ─────────────────────────────────────────────────────────────────────────────

SESSION_LOG_NAME = "test-sessions.jsonl"

COLLECTION_ERROR = "<collection error>"


def session_log(root):
    """`<root>/.dev/test-sessions.jsonl`。"""
    return os.path.join(os.fspath(root), ".dev", SESSION_LOG_NAME)


def _ticket_of(root):
    """`<root>/.dev/pipeline.json` 的 `ticket_id`。讀不到回 None —— 不猜(同 `current_ticket`)。"""
    try:
        with io.open(os.path.join(os.fspath(root), ".dev", "pipeline.json"),
                     encoding="utf-8") as f:
            return json.load(f).get("ticket_id")
    except Exception:
        return None


def record_session(root, run_id=None, time=None, ticket_id=None, exit_code=None,
                   collected=(), deselected=(), outcomes=None):
    """追加一筆 run 事實到 `<root>` 的 session 帳本。回傳寫入的內容。

    - `collected`:本次收集到的身分(含被 deselect 的;收集錯誤以
      `<檔>::<collection error>` 標記)
    - `deselected`:被排除的身分;`selected` = collected − deselected
    - `outcomes`:`{身分: "passed" | "failed" | "skipped" | "other"}`,只含 selected
    - `exit_code`:runner 的原始退出碼;取不到為 None

    `run_id` / `time` / `ticket_id` 為 None 時自取(測試可指定以求決定性)。
    寫入失敗不拋例外 —— 紀錄器不得弄死執行器(`TestTheRecorderCannotKillTheRunner`)。
    """
    import uuid
    rec = {
        "kind": "session",
        "run_id": run_id or uuid.uuid4().hex,
        "time": time or datetime.now(timezone.utc).isoformat(),
        "ticket_id": ticket_id if ticket_id is not None else _ticket_of(root),
        "exit_code": None if exit_code is None else int(exit_code),
        "collected": [str(n).replace("\\", "/") for n in (collected or ())],
        "deselected": [str(n).replace("\\", "/") for n in (deselected or ())],
        "outcomes": {str(k).replace("\\", "/"): v for k, v in (outcomes or {}).items()},
    }
    path = session_log(root)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with io.open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return rec


def load_runs(root):
    """`<root>` 的 run 事實,依寫入順序。無帳本回 `[]`。

    **任何一行讀不動就整本回 `[]`** —— 讀到一半的帳本會讓「較晚的 run」
    看起來不存在,而那正是退紅判定最依賴的東西。回 `[]` 的效果是
    「無 run 證據 / 不可判定」:沒有任何紅可以因此退掉(fail-closed 的方向)。
    """
    path = session_log(root)
    if not os.path.exists(path):
        return []
    out = []
    try:
        with io.open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                if not isinstance(rec, dict) or not rec.get("run_id"):
                    return []
                out.append(rec)
    except Exception:
        return []
    return out


def run_state(run):
    """一個 run 事實的狀態 `"A"`–`"F"`(票 145〈三〉A)。**依序判定,先命中者為準。**

    | 條件 | 狀態 |
    |---|---|
    | exit code 不在 {0, 1, 5}(中斷 / 內部錯誤 / 用法錯誤 / 取不到),或有收集錯誤 | D |
    | 任一身分 failed | B |
    | 0 collected | C |
    | 沒有任何身分 passed(全 skip、全 deselect、或混合) | F |
    | 其餘(≥1 passed、0 failed) | A |

    **不只看 exit code**:全部 deselected 時 pytest 回 5,但有收集到 ⇒ F,不是 C。
    E(根本沒跑)沒有 run 事實可以輸入,不在本函式值域內。
    """
    ec = run.get("exit_code")
    collected = run.get("collected") or []
    outcomes = run.get("outcomes") or {}
    values = list(outcomes.values())
    if ec not in (0, 1, 5) or any(str(n).endswith("::" + COLLECTION_ERROR) for n in collected):
        return "D"
    if "failed" in values:
        return "B"
    if not collected:
        return "C"
    if "passed" not in values:
        return "F"
    return "A"
