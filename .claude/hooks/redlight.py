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
import ntpath
import os
import posixpath
import re
import stat
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


def _normalize_arg(arg, root, invocation_dir):
    """一個 pytest 位置參數 → root 相對的 posix 路徑(保留 `::` 之後那段)。

    無法判讀(空字串、落在 root 之外、跨磁碟)⇒ None。**絕對路徑不落帳** ——
    帳本只存 root 相對路徑,`invocation_dir` 只用來解析,不寫進紀錄。
    """
    s = str(arg).replace("\\", "/")
    path, sep, rest = s.partition("::")
    if not path:
        return None
    if _is_abs_path(path) and not os.path.isabs(path):
        return None                     # 他平台的絕對路徑(例:POSIX 上的 `C:/…`)不可能在本機 root 之內
    base = os.fspath(invocation_dir) if invocation_dir else os.fspath(root)
    full = path if os.path.isabs(path) else os.path.join(base, path)
    try:
        rel = os.path.relpath(os.path.normpath(full), os.path.normpath(os.fspath(root)))
    except ValueError:
        return None
    rel = rel.replace("\\", "/")
    if rel == ".." or rel.startswith("../"):
        return None
    return rel + (sep + rest if sep else "")


def _normalize_invocation(root, invocation):
    """producer 交來的 invocation 事實 → 落帳形狀。不是 dict ⇒ None(涵蓋範圍未知)。"""
    if not isinstance(invocation, dict):
        return None
    args = invocation.get("args")
    if isinstance(args, (list, tuple)):
        norm = [_normalize_arg(a, root, invocation.get("invocation_dir")) for a in args]
    else:
        norm = None
    src = invocation.get("args_source")
    return {
        "args": norm,
        "args_source": src if isinstance(src, str) else None,
        "pyargs": bool(invocation.get("pyargs")),
    }


def record_session(root, run_id=None, time=None, ticket_id=None, exit_code=None,
                   collected=(), deselected=(), outcomes=None, invocation=None,
                   completeness=None):
    """追加一筆 run 事實到 `<root>` 的 session 帳本。回傳寫入的內容。

    - `collected`:本次收集到的身分(含被 deselect 的;收集錯誤以
      `<檔>::<collection error>` 標記)
    - `deselected`:被排除的身分;`selected` = collected − deselected
    - `outcomes`:`{身分: OUTCOME_VALUES 之一}`,只含 selected
    - `exit_code`:runner 的原始退出碼;取不到為 None
    - `invocation`:producer 觀察到的呼叫事實 `{"args", "args_source", "invocation_dir",
      "pyargs"}`(票 145〈十七〉裁決 1 的判定依據);None ⇒ 涵蓋範圍未知
    - `completeness`:選擇 / 執行完整性事實(票 145〈二十三〉7);不是 dict ⇒ 記 None
      (涵蓋範圍未知)。producer 負責只放 root 相對路徑與 JSON 原生型別

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
        "invocation": _normalize_invocation(root, invocation),
        "completeness": completeness if isinstance(completeness, dict) else None,
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


# "other" 只為讀得動 Station 4c 之前的 session(當時 xfail / xpass 都記成 other);
# 4c 之後的 producer 寫 "xfail" / "xpass"。"other" 不算「執行完成」(〈二十三〉7 (vi))。
OUTCOME_VALUES = ("passed", "failed", "skipped", "xfail", "xpass", "other")


def validate_session(run):
    """一筆 run 事實的 schema 問題清單。**空 list = 合格。**(票 145〈十七〉裁決 3)

    合格的條件(缺一即不合格,**不得**以「缺欄 ⇒ 空集合」或「錯型別照常迭代」處理):
      - `run_id`、`time` 為非空字串;`ticket_id` 欄位存在(字串或 null)
      - `exit_code` 欄位存在,為 int(非 bool)或 null
      - `collected`、`deselected` 為字串 list;`deselected ⊆ collected`
      - `outcomes` 為 `{字串: OUTCOME_VALUES 之一}`;其鍵 ⊆ selected
      - `invocation` 若存在且非 null:為 dict,`args` 為 list(元素為字串或 null)或 null
      - `completeness` 若存在且非 null:為 dict(內部欄位由 `file_coverage` 逐項驗;
        不合格 ⇒ 涵蓋 `"unknown"`,不讓整筆 run 失去加紅的效果)。沒有這個欄位的舊 session 仍合格
    """
    if not isinstance(run, dict):
        return ["不是物件"]
    problems = []
    for key in ("run_id", "time"):
        v = run.get(key)
        if not isinstance(v, str) or not v:
            problems.append("%s 缺欄或非字串" % key)
    if "ticket_id" not in run:
        problems.append("ticket_id 缺欄")
    if "exit_code" not in run:
        problems.append("exit_code 缺欄")
    else:
        ec = run["exit_code"]
        if ec is not None and (isinstance(ec, bool) or not isinstance(ec, int)):
            problems.append("exit_code 型別不符")
    lists = {}
    for key in ("collected", "deselected"):
        if key not in run:
            problems.append("%s 缺欄" % key)
        elif not isinstance(run[key], list) or not all(isinstance(n, str) for n in run[key]):
            problems.append("%s 型別不符" % key)
        else:
            lists[key] = run[key]
    outcomes = run.get("outcomes", None)
    if "outcomes" not in run:
        problems.append("outcomes 缺欄")
    elif not isinstance(outcomes, dict) or not all(
            isinstance(k, str) and v in OUTCOME_VALUES for k, v in outcomes.items()):
        problems.append("outcomes 型別不符")
        outcomes = None
    if "collected" in lists and "deselected" in lists:
        collected = set(lists["collected"])
        deselected = set(lists["deselected"])
        if not deselected <= collected:
            problems.append("deselected 不屬於 collected")
        if isinstance(outcomes, dict):
            stray = sorted(set(outcomes) - (collected - deselected))
            if stray:
                problems.append("outcome 身分不屬於 selected:%s" % ", ".join(stray))
    inv = run.get("invocation")
    if inv is not None:
        if not isinstance(inv, dict):
            problems.append("invocation 型別不符")
        else:
            args = inv.get("args")
            if args is not None and (not isinstance(args, list) or not all(
                    a is None or isinstance(a, str) for a in args)):
                problems.append("invocation.args 型別不符")
    comp = run.get("completeness")
    if comp is not None and not isinstance(comp, dict):
        problems.append("completeness 型別不符")
    return problems


def run_state(run):
    """一個 run 事實的狀態 `"A"`–`"F"`(票 145〈三〉A)。**依序判定,先命中者為準。**

    | 條件 | 狀態 |
    |---|---|
    | schema 不合格(`validate_session()` 非空) | INVALID —— 不是 A–F 任何一個 |
    | exit code 不在 {0, 1, 5}(中斷 / 內部錯誤 / 用法錯誤 / 取不到),或有收集錯誤 | D |
    | 任一身分 failed | B |
    | 0 collected | C |
    | 沒有任何身分 passed(全 skip、全 deselect、或混合) | F |
    | 其餘(≥1 passed、0 failed) | A |

    **不只看 exit code**:全部 deselected 時 pytest 回 5,但有收集到 ⇒ F,不是 C。
    E(根本沒跑)沒有 run 事實可以輸入,不在本函式值域內。
    """
    if validate_session(run):
        return "INVALID"
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


def file_coverage(run, test_file):
    """這個 run 對 `test_file` 是否整檔涵蓋:`"true"` / `"false"` / `"unknown"`。

    票 145〈十七〉裁決 1:**只有 producer 能正向證明整檔涵蓋時才為 true;不知道,就不是完整。**
    依序判定(先命中者為準):

    | 條件 | 結果 |
    |---|---|
    | run schema 不合格 | unknown |
    | 本 run 沒有收集到該檔的任何身分,或該檔有收集錯誤 | unknown |
    | 該檔有任何 deselected 身分(`-k` / `-m` / `--deselect` / `--lf` 等) | false |
    | 沒有 invocation 事實、`pyargs`、或 `args` 不是非空 list | unknown |
    | 某個位置參數是**該檔本身或其上層目錄**、且不含 `::` | true |
    | 位置參數只以 nodeid(含 `::`)指名該檔 | false |
    | 其餘(參數無法判讀、或都與該檔無關) | unknown |
    | 位置參數涵蓋該檔之後:完整性事實(〈二十三〉7、〈二十九〉2)不全部成立 | 見 `_completeness_verdict` |

    **沒有為固定指令另寫分支**:pytest 未給位置參數時以 testpaths 補上
    `config.args == ["tests"]`,與「位置參數為上層目錄 tests」走同一條規則;
    完整性事實也一樣 —— 固定全套只是「每一條都剛好成立」的那一種 run。
    """
    if validate_session(run):
        return "unknown"
    tf = str(test_file).replace("\\", "/")
    deselected = set(run["deselected"])
    idents = [n for n in run["collected"] if n.split("::", 1)[0] == tf]
    if not idents or any(n.endswith("::" + COLLECTION_ERROR) for n in idents):
        return "unknown"
    if any(n in deselected for n in idents):
        return "false"
    inv = run.get("invocation")
    if not isinstance(inv, dict) or inv.get("pyargs"):
        return "unknown"
    args = inv.get("args")
    if not isinstance(args, list) or not args:
        return "unknown"
    covering = narrowed = False
    for a in args:
        if not isinstance(a, str):
            continue                        # 無法判讀的參數:不證明任何事
        path, sep, _rest = a.partition("::")
        if path == tf:
            if sep:
                narrowed = True
            else:
                covering = True
        elif not sep and (path == "." or tf.startswith(path.rstrip("/") + "/")):
            covering = True
    if covering:
        return _completeness_verdict(run, tf, idents)
    if narrowed:
        return "false"
    return "unknown"


# ─────────────────────────────────────────────────────────────────────────────
# 票 145 Station 4c —— 選擇 / 執行完整性(〈二十三〉)
#
# 「沒有 deselected」證明不了選擇完整(`--lf` 在收集期就悄悄移除身分),
# 「有一筆 report」證明不了已執行(`pytest.exit(returncode=0)` 只留 setup report)。
# 所以 `"true"` 另外要 producer 的正向事實:選項全部關閉、沒有提前停止、
# 縮小前全集 == 收集結果、每個 selected 身分都到了執行完成的終態、
# 本次註冊的每個 plugin 都在受支援範圍(白名單)內。**任一缺欄或型別錯 ⇒ unknown。**
#
# 白名單變更須走票(〈二十三〉3)。
# ─────────────────────────────────────────────────────────────────────────────

COMPLETENESS_OPTIONS = ("lf", "last_failed_no_failures", "stepwise", "stepwise_skip",
                        "maxfail", "collectonly", "setuponly", "setupplan",
                        # 票 145 Station 4e(〈三十五〉3 (xv)–(xvii)):pass 有效性的 pytest 層事實
                        "runxfail", "pythonwarnings", "trace",
                        # 票 145 Station 4f(〈三十九〉39.3 第 3 點 (xix)):`--pdb`
                        "usepdb")

PLUGIN_KINDS = ("builtin", "root_conftest", "known_dist", "other")
SUPPORTED_PLUGIN_KINDS = ("builtin", "root_conftest", "known_dist")
BUILTIN_MODULE = "_pytest"
ROOT_CONFTEST = "tests/conftest.py"
OUTSIDE = "<outside>"
NON_IDENTIFIER = "<non-identifier>"

# (xviii) P1 對 sys.flags 與 assert 移除的盤點只對這些 Python 版本(major.minor)成立;升級須走票。
KNOWN_PYTHON_VERSIONS = ("3.11",)

# ── 票 145 Station 4d —— 收集定義完整性與版本邊界(〈二十九〉2 (vii′)–(xiii))
# 以下四組是「已盤點」清單,**變更須走票**。版本邊界總表(〈二十九〉2):
#   pytest 內建 ⇒ 鎖 pytest 版本;root producer ⇒ 鎖 tests/conftest.py 已提交 blob;
#   repo 收集設定 ⇒ 鎖 pyproject.toml 已提交 blob;已知第三方 plugin ⇒ 鎖 dist 名稱 + 精確版本;
#   未知 plugin ⇒ fail-closed。

# (vii′) 已知第三方 plugin:(dist 名稱, 精確版本)。只看名稱不算(名稱可被冒用),版本不同也不算。
# 票 145 Station 4k:anyio 4.15.1(PyPI 2026-09-05)納入;pytest_plugin.py 與 4.15.0 逐位元組相同(wheel 比對,外部來源),
# 真實 4.15.1 環境的淨室正二由 4k POSIX 驗收證明。
KNOWN_DISTS = (("anyio", "4.15.0"), ("anyio", "4.15.1"))

# (xiii) P1 的盤點只對這些 pytest 版本成立;換版後非 ini 的 CLI 選項要重新盤點。
KNOWN_PYTEST_VERSIONS = ("9.1.1",)

# (x) 框架盤點過的設定檔型態(root 相對路徑;P1 只盤點了 pyproject 的 `[tool.pytest.ini_options]`)。
# 宿主用哪一個由 evidence policy 的 `config_file` 指定,必須屬於這裡。
FRAMEWORK_CONFIG_FILES = ("pyproject.toml",)

# (xi) producer 記錄工作樹 blob 與 HEAD blob 的檔:框架能盤點的設定檔 + root producer 本身。
# consumer 只看 `ROOT_CONFTEST` 與 policy 指定的 `config_file` 兩項。
BLOB_FILES = FRAMEWORK_CONFIG_FILES + (ROOT_CONFTEST,)

# ── 票 145 Station 4g —— Host evidence policy(〈四十八〉48.1;規劃檔 S3g-0 P3)
# 上面的 `KNOWN_*` 與 `FRAMEWORK_CONFIG_FILES` 是框架能力邊界(B);宿主在 B 之內自己選擇接受什麼(H),
# 寫在 canonical path 的 policy 檔、並且**已提交**。原本的 `COMMITTED_ADDOPTS_OVERRIDES` / `CONFIG_FILE`
# 是 agent-gates 自己的宿主事實被寫成了框架常數 —— 淨室 repo 因此永遠 unknown(〈四十六〉46.2)。
#
# I-1:位置是框架常數,policy 內容不得指定位置(多一個鍵 ⇒ 整份不合格)。
# I-2:認得的 (schema, version) 由框架列舉;policy 不能宣告自己用哪一套解析規則。
POLICY_FILE = ".agents/evidence-policy.json"
POLICY_SCHEMAS = (("monkeyleash.evidence-policy", 1),)
POLICY_FIELDS = ("schema", "version", "config_file", "committed_overrides",
                 "python_versions", "pytest_versions", "dists")

# producer 記在 `completeness["evidence_policy"]` 的 7 鍵(〈五十一〉裁決 3)。
EVIDENCE_POLICY_KEYS = ("path", "head", "worktree", "schema", "version", "policy", "committed_addopts")

# status 的 policy 狀態行(〈五十〉50.1 第 3 點);文字以裁決為準。
POLICY_UNINITIALIZED = u"未初始化"
POLICY_UNCOMMITTED = u"未提交"
POLICY_WORKTREE_DIFFERS = u"工作樹與 HEAD 不同"
POLICY_UNKNOWN_FORMAT = u"格式不明"
POLICY_OUTSIDE_BOUNDARY = u"超出框架能力邊界"
POLICY_VALID = u"有效"

# (viii) 的推導規則(pytest 9.1.1):`OverrideIniAction` 旗標(`_pytest/main.py:76-96`;
# 動作本體 `_pytest/config/argparsing.py:491-503`)與 `-o` / `--override-ini`(`_pytest/helpconfig.py:113-116`)。
OVERRIDE_FLAGS = {"--strict-config": "strict_config=true",
                  "--strict-markers": "strict_markers=true",
                  "--strict": "strict=true"}

# 「執行完成」的終態:call 的 passed / failed、任何 phase 的 skip、明確辨識的 xfail / xpass。
# 籠統的 "other"(4c 之前的 xfail 記法)不算 —— 不得讓 other 自動取得 completeness。
EXECUTED_OUTCOMES = ("passed", "failed", "skipped", "xfail", "xpass")


def _dist_name(dist):
    name = getattr(dist, "project_name", None)
    if not isinstance(name, str):
        try:
            name = dist.metadata["name"]
        except Exception:
            name = None
    return name.strip().lower().replace("_", "-") if isinstance(name, str) else None


def _dist_version(dist):
    version = getattr(dist, "version", None)
    if not isinstance(version, str):
        try:
            version = dist.metadata["version"]
        except Exception:
            version = None
    return version.strip() if isinstance(version, str) and version.strip() else None


def _defining_module(plugin):
    """模組物件看 `__name__`;類別看自己的 `__module__`;其他物件看其類別的 `__module__`。"""
    import types
    if isinstance(plugin, types.ModuleType):
        return getattr(plugin, "__name__", None)
    if isinstance(plugin, type):
        return getattr(plugin, "__module__", None)
    return getattr(type(plugin), "__module__", None)


# ── 票 145 Station 4e —— producer 自行產生的路徑型 metadata 的正規化(S5d-F3;〈三十五〉4 的 F3-甲)
# 依**欄位類別**套規則,不依特定字串:
#   (1) 類(inipath、inifilename、invocation.args、conftest 註冊的路徑名)⇒ root 相對 posix 路徑或 `<outside>`;
#   名稱欄位(plugins[].name、blocked[])⇒ 路徑名依 (1);模組 / entry-point 名稱(含數字 id)原樣;其他 `<non-identifier>`;
#   (2) 類(override_ini)⇒ key 原樣;value 只在是絕對路徑、或以 root 為基準解析後越出 root 時正規化(4f,S5e-F2)。
# **絕對路徑的判定與平台無關**:只用 `os.path.isabs` 的話,POSIX 上認不出 `C:\…`,同一個輸入在兩種平台落帳不同。

_DRIVE_PREFIX = re.compile(r"^[A-Za-z]:")
_IDENTIFIER = re.compile(r"[A-Za-z0-9_.\-]+")         # 以 fullmatch 整串比對(S5e-F4:`$` 會放過結尾換行)


def _is_abs_path(text):
    """任一平台意義下的絕對路徑:`posixpath.isabs` 或 `ntpath.isabs`,或以磁碟代號開頭。"""
    text = str(text)
    return posixpath.isabs(text) or ntpath.isabs(text) or bool(_DRIVE_PREFIX.match(text))


def _root_relative(value, root, base=None):
    """(1) 類路徑 → root 相對 posix 路徑;root 以外(含跨磁碟、他平台的絕對路徑)⇒ `<outside>`。

    相對路徑先以 `base`(producer 給的 `invocation_params.dir`;沒有就用 root)解析。
    本機意義下的絕對 / 相對用 `os.path`(Windows 上大小寫不敏感,與 pytest 給的路徑一致);
    只有「他平台才算絕對」的值(例:POSIX 上的 `C:\\…`)直接記 `<outside>` —— 它不可能在本機 root 之內。
    「他平台絕對」以**原字串**判定;之後才把 `\\` 換成 `/` 再 join / normpath(S5e-F3:否則 POSIX 的
    `posixpath.normpath` 看不到以反斜線分隔的 `..`,越界的值不會被認出)。
    """
    text = os.fspath(value) if isinstance(value, os.PathLike) else str(value)
    host_abs = os.path.isabs(text)
    if _is_abs_path(text) and not host_abs:
        return OUTSIDE
    text = text.replace("\\", "/")
    start = os.fspath(base) if base is not None else os.fspath(root)
    full = text if host_abs else os.path.join(start, text)
    try:
        rel = os.path.relpath(os.path.normpath(full), os.path.normpath(os.fspath(root)))
    except (ValueError, OSError, TypeError):
        return OUTSIDE
    rel = rel.replace("\\", "/")
    if rel == ".." or rel.startswith("../") or _is_abs_path(rel):
        return OUTSIDE
    return rel


def _plugin_path_name(name, root):
    """路徑型名稱 → root 相對 posix 路徑;root 以外(含跨磁碟)⇒ `<outside>`。"""
    return _root_relative(name, root)


def _plugin_name(name, root):
    """名稱欄位的落帳字串(〈三十五〉4):路徑名依 (1) 類;模組 / entry-point 名稱(含數字 id)原樣;
    其他(例:`-p no:<路徑>` 留下的 `pytest_<路徑>`)⇒ `<non-identifier>`。"""
    if _is_abs_path(name):
        return _root_relative(name, root)
    if _IDENTIFIER.fullmatch(name):
        return name
    return NON_IDENTIFIER


def classify_plugins(root, name_plugins, distinfo):
    """`list_name_plugin()` 與 `list_plugin_distinfo()` 的原始事實 → `[{"name", "kind"}]`。

    依序判定(〈二十三〉3,經〈二十九〉2 (vii′) 修訂):
      1. plugin **物件**出現在 distinfo 配對中 ⇒ (dist 名稱, 精確版本) 在 `KNOWN_DISTS` 為 known_dist,
         否則 other(只看名稱相同不算 —— 名稱可被冒用;版本缺失或不同也是 other)
      2. 名稱是絕對路徑(conftest 的註冊名稱)⇒ root 相對路徑恰為 `ROOT_CONFTEST` 為 root_conftest,否則 other
      3. 定義模組為 `_pytest` 或 `_pytest.*` ⇒ builtin
      4. 其他(含 `-p no:` 留下的 `(name, None)`)⇒ other
    帳本只記正規化名稱(`_plugin_name`;〈三十五〉4):路徑型轉 root 相對路徑(root 以外記 `<outside>`),
    非識別字形狀的名稱記 `<non-identifier>`,不記絕對路徑。**kind 用原始名稱判定**,正規化只作用於落帳字串。
    配對到 dist 的項目另記 `dists`(`[[名稱, 版本], ...]`)。
    """
    dists = [(p, _dist_name(d), _dist_version(d)) for p, d in (distinfo or [])]
    out = []
    for name, plugin in name_plugins or []:
        name = str(name)
        is_path = _is_abs_path(name)
        shown = _plugin_name(name, root)
        paired = [(dn, dv) for p, dn, dv in dists if p is plugin]
        if paired:
            kind = "known_dist" if all(pair in KNOWN_DISTS for pair in paired) else "other"
        elif is_path:
            kind = "root_conftest" if _plugin_path_name(name, root) == ROOT_CONFTEST else "other"
        else:
            mod = _defining_module(plugin)
            builtin = isinstance(mod, str) and (
                mod == BUILTIN_MODULE or mod.startswith(BUILTIN_MODULE + "."))
            kind = "builtin" if builtin else "other"
        entry = {"name": shown, "kind": kind}
        if paired:
            entry["dists"] = [[dn, dv] for dn, dv in paired]
        out.append(entry)
    return out


def blocked_plugins(name_plugins, root=None):
    """`list_name_plugin()` 中值為 None 的名稱 —— `-p no:<name>` 的 pluggy 表示方式
    (`pluggy/_manager.py:230-233`)。〈二十九〉2 (xii)。

    給 `root` ⇒ 落帳字串依名稱欄位規則正規化(`_plugin_name`;〈三十五〉4)。判定只看「非空」,不受正規化影響。"""
    names = [str(name) for name, plugin in (name_plugins or []) if plugin is None]
    return names if root is None else [_plugin_name(n, root) for n in names]


def normalize_config_path(value, root, base=None):
    """`inifilename` / `inipath` → 落帳形狀(〈三十五〉4 的 (1) 類)。None ⇒ None;
    其他 ⇒ root 相對 posix 路徑,root 以外 `<outside>`。相對路徑先以 `base`(invocation dir)解析。
    **不落帳絕對路徑,也不落帳越出 root 的相對路徑。**"""
    if value is None:
        return None
    return _root_relative(value, root, base)


def normalize_overrides(values, root, base=None):
    """`config.option.override_ini`(解析後清單)→ 落帳形狀(〈三十五〉4 的 (2) 類)。不是 list ⇒ None。

    key 一律原樣;value 只在是絕對路徑(平台無關判定)、或以 **root** 為基準解析後越出 root 時,
    換成 root 相對路徑或 `<outside>`。其他值一律原樣(例:`true`、`test_b`、`tests/test_*.py`)——
    不改寫證據本身。

    「越出 root」的基準是 root,不是 `base`(invocation dir)(S5e-F2;〈四十一〉41.1 第 3 點):
    pytest 解析 ini 的路徑值也不用 invocation dir(`cache_dir` 用 rootpath),
    而以 invocation dir 為基準時,從 root 外執行會把 `true` 這類非路徑值判成越界。"""
    if not isinstance(values, (list, tuple)):
        return None
    out = []
    for item in values:
        key, sep, val = str(item).partition("=")
        if sep and val:
            if _is_abs_path(val):
                val = _root_relative(val, root, base)
            elif _root_relative(val, root) == OUTSIDE:
                val = OUTSIDE
        out.append(key + sep + val)
    return out


def _git_lines(root, args, expected):
    import subprocess
    try:
        proc = subprocess.run(["git", "-C", os.fspath(root)] + list(args),
                              capture_output=True, timeout=30)
    except Exception:
        return None
    if proc.returncode != 0:
        return None
    lines = proc.stdout.decode("ascii", "replace").split()
    if len(lines) != expected or not all(
            len(x) in (40, 64) and all(c in "0123456789abcdef" for c in x) for x in lines):
        return None
    return lines


def _git_bytes(root, args):
    """一條 git 的原始 stdout;失敗 ⇒ None。不拋例外。"""
    import subprocess
    try:
        proc = subprocess.run(["git", "-C", os.fspath(root)] + list(args),
                              capture_output=True, timeout=30)
    except Exception:
        return None
    return proc.stdout if proc.returncode == 0 else None


def _root_is_toplevel(root):
    """root 是否就是 git 工作樹的最上層:須同時 `--is-inside-work-tree` 為 true 且 `--show-prefix` 為空
    (票 145 Station 4i,S5h-F1:gitdir / bare repository 內 `--show-prefix` 同樣為空,但不是工作樹)。
    任一查詢失敗或條件不符 ⇒ False。
    stdout 須完整等於 b"true\n\n"(\r\n 正規化後):--show-prefix 輸出未跳脫的原始路徑位元組,
    拆行只看前兩行會把 LF 開頭的子目錄名誤判為空 prefix(票 145 Station 4j,S5i-F1)。"""
    import subprocess
    try:
        proc = subprocess.run(["git", "-C", os.fspath(root), "rev-parse",
                               "--is-inside-work-tree", "--show-prefix"],
                              capture_output=True, timeout=30)
    except Exception:
        return False
    if proc.returncode != 0:
        return False
    return proc.stdout.replace(b"\r\n", b"\n") == b"true\n\n"


def committed_blobs(root, paths=BLOB_FILES):
    """`{path: {"worktree": blob, "head": blob}}` —— 工作樹檔案(`git hash-object`,依
    .gitattributes 正規化)與 `HEAD:<path>` 的 blob。〈二十九〉2 (xi)。

    git 不可用、不是 repo、檔案不存在或任何一步出錯 ⇒ 該值 None(缺欄 ⇒ 不得為 `"true"`)。
    **逐路徑各呼叫一次 git**(票 145 Station 4g;規劃檔 P3 遷移第 3 點):一次處理全部路徑的話,
    缺一個檔整次失敗、所有路徑都成 None —— 淨室 repo 沒有 pyproject 時,conftest 的 blob 也一起遺失。
    **不拋例外**:這是 producer 在 sessionfinish 呼叫的,不得讓 pytest 失敗。
    root 必須是 git 最上層(I-3 位置不變式;票 145 Station 4h,S5g-F2):HEAD:<path> 以最上層為基準、
    hash-object 以 root 為基準,root 不是最上層時兩者不是同一邏輯路徑 ⇒ 事實一律 None ⇒ unknown。
    框架目前只支援一個 host evidence root = 一個 Git 最上層。
    """
    out = {}
    top = _root_is_toplevel(root)
    for p in list(paths):
        entry = {"worktree": None, "head": None}
        if not top:
            out[p] = entry
            continue
        try:
            worktree = _git_lines(root, ["hash-object", p], 1)
            head = _git_lines(root, ["rev-parse", "HEAD:" + p], 1)
            entry["worktree"] = worktree[0] if worktree else None
            entry["head"] = head[0] if head else None
        except Exception:
            pass
        out[p] = entry
    return out


def addopts_overrides(value):
    """已提交設定的 addopts **原值** → 它帶來的 override 清單,依出現順序(pytest 9.1.1;(viii) 的推導規則)。

    輸入合約(票 145〈五十一〉裁決 3):`value` 是 HEAD config 經 TOML 解析後的 raw addopts —— 只接受
    `str`(依 shlex 切開;ini 的 type="args",`_pytest/config/__init__.py:1547`)或 `list[str]`(逐項使用);
    沒有 addopts 時呼叫端傳 `""`。**本函式不讀 git、工作樹或任何檔案。**
      - `OVERRIDE_FLAGS` 的旗標 → 對應的 `<ini>=true`;`-o VAL` / `-oVAL` / `--override-ini VAL` /
        `--override-ini=VAL` → `VAL`;其他 token 不產生 override;
      - 型別不符、引號不成對、`-o` 後面沒有值 ⇒ None,由呼叫端判 unknown —— 不猜。

    推導漏掉的寫法(例:合併短旗標 `-qo x`、長旗標縮寫)會讓「推導值 ≠ 實際 override」,
    方向是 unknown(fail-closed),不是假綠:runtime 的 `override_ini` 仍要另外等於 policy(viii)。
    """
    import shlex
    if isinstance(value, str):
        try:
            tokens = shlex.split(value)
        except ValueError:
            return None
    elif isinstance(value, list) and all(isinstance(t, str) for t in value):
        tokens = list(value)
    else:
        return None
    out = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in OVERRIDE_FLAGS:
            out.append(OVERRIDE_FLAGS[tok])
        elif tok in ("-o", "--override-ini"):
            i += 1
            if i >= len(tokens):
                return None
            out.append(tokens[i])
        elif tok.startswith("--override-ini="):
            out.append(tok.split("=", 1)[1])
        elif tok.startswith("-o") and not tok.startswith("--"):
            out.append(tok[2:])
        i += 1
    return out


def _committed_addopts(root, config_file):
    """`HEAD:<config_file>` 的 `[tool.pytest.ini_options].addopts` 原值(事實擷取,不判定)。

    語意(〈五十一〉裁決 3,不得混用):
      - `str` / `list[str]` = 原值照錄;
      - `""` = config 存在且合法、`[tool.pytest.ini_options]` 段在、只是沒有 addopts 鍵;
      - None = 取得或解析事實失敗:blob 讀不到、不是 UTF-8 / TOML、沒有 `[tool.pytest.ini_options]` 段、
        addopts 型別不是 str / list[str]、或直譯器沒有 `tomllib`(3.11 起的標準庫;沒有它本來就在能力邊界外)。
    只讀 HEAD 的 blob(`git cat-file`),不讀工作樹(工作樹 ≠ HEAD 由 (xi) 另外判)。
    """
    try:
        import tomllib
    except ImportError:
        return None
    raw = _git_bytes(root, ["cat-file", "blob", "HEAD:" + config_file])
    if raw is None:
        return None
    try:
        doc = tomllib.loads(raw.decode("utf-8"))
    except Exception:
        return None
    tool = doc.get("tool")
    pytest_section = tool.get("pytest") if isinstance(tool, dict) else None
    section = pytest_section.get("ini_options") if isinstance(pytest_section, dict) else None
    if not isinstance(section, dict):
        return None
    if "addopts" not in section:
        return ""
    value = section["addopts"]
    if isinstance(value, str) or (isinstance(value, list) and all(isinstance(v, str) for v in value)):
        return value
    return None


def evidence_policy_facts(root):
    """producer 的 policy 事實(票 145 規劃檔 P3 I-3;〈四十八〉48.1 第 2 點)。依序:

      1. 固定 canonical path `POLICY_FILE`;
      2. `git rev-parse HEAD:<path>` —— HEAD 沒有 ⇒ 停在這裡(`head` 為 None);
      3. 第 2 步的輸出就是 HEAD committed blob;
      4. `git hash-object <path>`(套用 .gitattributes,與 `committed_blobs` 同一手法)取 worktree blob;
         ≠ HEAD blob 或缺檔 ⇒ 停在這裡;
      5. 內容**只從 HEAD blob** 取(`git cat-file blob <sha>`)並解析 JSON —— 第 4 步的工作樹檔只做
         identity 比對,之後不再讀;記下 `schema` / `version` 與整份內容 `policy`;
      6. policy 的 `config_file` 屬於 `FRAMEWORK_CONFIG_FILES` 時,另記它在 HEAD 的 addopts 原值
         `committed_addopts`(`_committed_addopts`),供 consumer 做「policy ↔ 已提交設定」的機器鎖步。

    回傳 7 鍵 `{"path", "head", "worktree", "schema", "version", "policy", "committed_addopts"}`
    (〈五十一〉裁決 3);走不下去的那一步之後的欄位都是 None。
    **只擷取事實,不判定** —— 型別、schema、邊界、鎖步都由 consumer 驗。不拋例外(sessionfinish 呼叫)。
    root 必須是 git 最上層(I-3 位置不變式;票 145 Station 4h,S5g-F2):HEAD:<path> 以最上層為基準、
    hash-object 以 root 為基準,root 不是最上層時兩者不是同一邏輯路徑 ⇒ 事實一律 None ⇒ unknown。
    框架目前只支援一個 host evidence root = 一個 Git 最上層。
    """
    out = {"path": POLICY_FILE, "head": None, "worktree": None, "schema": None,
           "version": None, "policy": None, "committed_addopts": None}
    try:
        if not _root_is_toplevel(root):
            return out
        head = _git_lines(root, ["rev-parse", "HEAD:" + POLICY_FILE], 1)
        if not head:
            return out
        out["head"] = head[0]
        worktree = _git_lines(root, ["hash-object", POLICY_FILE], 1)
        out["worktree"] = worktree[0] if worktree else None
        if out["worktree"] != out["head"]:
            return out
        raw = _git_bytes(root, ["cat-file", "blob", out["head"]])
        if raw is None:
            return out
        doc = json.loads(raw.decode("utf-8"))
        if not isinstance(doc, dict):
            return out
        out["schema"] = doc.get("schema")
        out["version"] = doc.get("version")
        out["policy"] = doc
        if doc.get("config_file") in FRAMEWORK_CONFIG_FILES:
            out["committed_addopts"] = _committed_addopts(root, doc["config_file"])
    except Exception:
        pass
    return out


def _is_pair_list(v):
    return isinstance(v, list) and all(
        isinstance(d, list) and len(d) == 2 and all(isinstance(x, str) for x in d) for d in v)


def policy_document_problems(policy):
    """`(格式問題, 邊界問題)` 兩個 list;都空 = 合格。consumer 與 status 共用。

    - 格式(I-1、I-2):不是物件、`(schema, version)` 不在 `POLICY_SCHEMAS`、鍵集合不恰為 `POLICY_FIELDS`、
      欄位型別不對。**schema 不認得就不往下看** —— 別的 version 的欄位語意不是本版能判讀的。
    - 邊界(I-4;〈四十八〉48.1 第 3 點 A):任一欄位超出框架能力邊界 ⇒ 整份不合格,不取交集、不靜默忽略。
    """
    if not isinstance(policy, dict):
        return [u"不是物件"], []
    schema, version = policy.get("schema"), policy.get("version")
    if not (isinstance(schema, str) and type(version) is int and (schema, version) in POLICY_SCHEMAS):
        return [u"schema / version 不認得"], []
    fmt = []
    keys = set(policy)
    if keys != set(POLICY_FIELDS):
        fmt.append(u"欄位不符(多 %s;缺 %s)" % (sorted(keys - set(POLICY_FIELDS)),
                                              sorted(set(POLICY_FIELDS) - keys)))
    if not isinstance(policy.get("config_file"), str):
        fmt.append(u"config_file 型別不符")
    for key in ("committed_overrides", "python_versions", "pytest_versions"):
        if not _is_str_list(policy.get(key)):
            fmt.append(u"%s 型別不符" % key)
    if not _is_pair_list(policy.get("dists")):
        fmt.append(u"dists 型別不符")
    if fmt:
        return fmt, []
    bnd = []
    if policy["config_file"] not in FRAMEWORK_CONFIG_FILES:
        bnd.append(u"config_file")
    if not set(policy["python_versions"]) <= set(KNOWN_PYTHON_VERSIONS):
        bnd.append(u"python_versions")
    if not set(policy["pytest_versions"]) <= set(KNOWN_PYTEST_VERSIONS):
        bnd.append(u"pytest_versions")
    if not set(tuple(d) for d in policy["dists"]) <= set(KNOWN_DISTS):
        bnd.append(u"dists")
    return [], bnd


def policy_state(root):
    """`<root>` 現在的 policy 狀態(status 行用;〈五十〉50.1 第 3 點)。依序:
    HEAD 沒有 ⇒ 工作樹有檔為「未提交」、否則「未初始化」;工作樹 ≠ HEAD ⇒「工作樹與 HEAD 不同」;
    格式問題 ⇒「格式不明」;邊界問題 ⇒「超出框架能力邊界」;其餘「有效」。

    「有效」只說**文件本身**可用;一次 run 能不能退紅,還要看那次的環境與鎖步(`_completeness_verdict`)。"""
    facts = evidence_policy_facts(root)
    if facts["head"] is None:
        exists = os.path.exists(os.path.join(os.fspath(root), *POLICY_FILE.split("/")))
        return POLICY_UNCOMMITTED if exists else POLICY_UNINITIALIZED
    if facts["worktree"] != facts["head"]:
        return POLICY_WORKTREE_DIFFERS
    fmt, bnd = policy_document_problems(facts["policy"])
    if fmt:
        return POLICY_UNKNOWN_FORMAT
    if bnd:
        return POLICY_OUTSIDE_BOUNDARY
    return POLICY_VALID


def policy_template():
    """安裝器寫到非 canonical 路徑的範本內容(〈四十八〉48.1 第 6 點 A):框架能力邊界常數的完整列舉,
    **不是本機觀察值**。`committed_overrides` 留空 —— 它必須等於宿主自己已提交 addopts 的推導,
    框架不替人填。"""
    schema, version = POLICY_SCHEMAS[0]
    return {"schema": schema, "version": version,
            "config_file": FRAMEWORK_CONFIG_FILES[0],
            "committed_overrides": [],
            "python_versions": list(KNOWN_PYTHON_VERSIONS),
            "pytest_versions": list(KNOWN_PYTEST_VERSIONS),
            "dists": [list(d) for d in KNOWN_DISTS]}


def _effective_policy(ep):
    """session 記下的 `evidence_policy` → 可用的 policy(dict);任何一項不成立 ⇒ None(unknown)。

    驗:型別、path 為 canonical、`head == worktree` 且非 None、文件格式與邊界(`policy_document_problems`)、
    記錄的 schema / version 與文件一致、`committed_overrides == addopts_overrides(committed_addopts)`
    (機器鎖步,取代原 test_d4;`committed_addopts` 為 None 或推導不了 ⇒ unknown)。
    policy 已驗過 ⊆ 能力邊界,所以 effective = B ∩ policy = policy。"""
    if not isinstance(ep, dict) or ep.get("path") != POLICY_FILE:
        return None
    head = ep.get("head")
    if not (isinstance(head, str) and head and ep.get("worktree") == head):
        return None
    policy = ep.get("policy")
    fmt, bnd = policy_document_problems(policy)
    if fmt or bnd:
        return None
    if ep.get("schema") != policy["schema"] or ep.get("version") != policy["version"]:
        return None
    committed = ep.get("committed_addopts")
    if committed is None:
        return None
    derived = addopts_overrides(committed)
    if derived is None or derived != policy["committed_overrides"]:
        return None
    return policy


def _effective(boundary, chosen):
    """effective = B ∩ policy(I-3 第 6 步)。"""
    return [v for v in chosen if v in boundary]


def _known_dists_accepted(plugin, accepted):
    """known_dist 項目的每個 (名稱, 版本) 都要在 effective 的 dists 內;沒有 `dists` 事實 ⇒ 不成立。"""
    dists = plugin.get("dists")
    return _is_pair_list(dists) and bool(dists) and all(tuple(d) in accepted for d in dists)


def _is_str_list(v):
    return isinstance(v, list) and all(isinstance(n, str) for n in v)


# ── 票 146 Extension Integrity v0(宣告層;runtime 未證明)────────────────────
# 只證明「已知靜態載入入口符合已提交的 allowlist」;不證明本 session 實際載入了什麼。
# allowlist 的讀取沿用 145 的 authority 模式(只認 HEAD blob,工作樹只做一次 identity 比對)。
# R4 的樹比對純函式自閘門下沉到這裡(方向 B);本模組不載入任何專案模組。
EXT_ALLOWLIST_FILE = ".agents/extension-allowlist.json"
EXT_ALLOWLIST_SCHEMA = "monkeyleash.extension-allowlist"
EXT_ALLOWLIST_VERSION = 1
EXT_ALLOWLIST_FIELDS = ("schema", "version", "dev_mod_files", "user_skill_plugins", "user_commands",
                        "project_settings_hook_commands", "mcp_json_servers")
EXT_VIOLATION = "VIOLATION"
EXT_UNKNOWN = "UNKNOWN"
EXT_DECLARED_OK = "DECLARED_OK"
EXT_VERIFIED = "VERIFIED"
EXT_SURFACE_KEYS = frozenset(("dev_mod_files", "synced_files", "r4_violations", "project_hook_commands",
                              "mcp_json_servers", "user_skill_plugins", "user_commands", "errors"))

# 3e(v1 接線契約):EXT_UNKNOWN 的結構化原因類別;state 與 category 分開承載。
EXT_CAT_ALLOWLIST = "allowlist_state"
EXT_CAT_UNREGISTERED = "unregistered"
EXT_CAT_R4 = "r4"
EXT_CAT_HOOK = "hook"
EXT_CAT_MCP = "mcp"
EXT_CAT_OBSERVATION = "observation_missing"
EXT_CAT_UNMANAGED = "unmanaged_entry"
EXT_CATEGORIES = frozenset((EXT_CAT_ALLOWLIST, EXT_CAT_UNREGISTERED, EXT_CAT_R4, EXT_CAT_HOOK,
                            EXT_CAT_MCP, EXT_CAT_OBSERVATION, EXT_CAT_UNMANAGED))
EXT_RUNTIME_UNPROVEN = "UNPROVEN"

# 3f(v2 synced 契約):synced 兩根以獨立 inventory 納管;路徑一律是匿名邏輯路徑,不寫 bucket 真名。
EXT_INVENTORY_FILE = ".agents/extension-inventory.json"
EXT_INVENTORY_SCHEMA = "monkeyleash.extension-inventory"
EXT_INVENTORY_VERSION = 1
EXT_INVENTORY_FIELDS = ("schema", "version", "entries")
EXT_SYNCED_ROOTS = ("skills", "plugins")
EXT_BUCKET_TOKEN = "<bucket>"
EXT_POLICY_SOURCES = ("head", "index")


class _InventoryUnchecked(object):
    """「synced 納管未評估」的哨兵:只給兩參數相容 wrapper 用,production 不得傳入。"""

    def __repr__(self):
        return "EXT_INVENTORY_UNCHECKED"


EXT_INVENTORY_UNCHECKED = _InventoryUnchecked()

# 檔案型欄位(policy 與 surfaces 同名)與它在訊息裡的入口名,順序即判定順序。
_EXT_FILE_FIELDS = (("dev_mod_files", "dev-mods"), ("user_skill_plugins", "user-skills"),
                    ("user_commands", "user-commands"))
_EXT_ENTRY_KEYS = frozenset(("path", "sha256", "note"))
_EXT_STATE_TEXT = {
    "uninitialized": u"allowlist 未初始化（HEAD 無 .agents/extension-allowlist.json）；靜態入口無法判定",
    "uncommitted": u"allowlist 未提交；工作樹的版本不被採用",
    "worktree_differs": u"allowlist 工作樹與 HEAD 不同；只採用 HEAD，本次無法判定",
    "identity_mismatch": u"allowlist 工作樹與 HEAD 身分不符；本次無法判定",
    "malformed": u"allowlist 格式不明；本次無法判定",
}
_EXT_RUNTIME_LINE = u"runtime loaded set: 未證明（沒有獨立 runtime authority source）"


def _rel(path):
    try:
        return os.path.relpath(os.path.abspath(path), ROOT).replace("\\", "/")
    except ValueError:
        return path.replace("\\", "/")


def _read_all_bytes(path):
    with io.open(path, "rb") as fh:
        return fh.read()


def _error_text(exc):
    """例外 → 錯誤文字。**只帶型別與 strerror,不帶路徑**(訊息會被貼出去;路徑另有欄位)。"""
    detail = getattr(exc, "strerror", None)
    return "%s: %s" % (type(exc).__name__, detail) if detail else type(exc).__name__


def _walk_regular(root_dir, exclude_top=None, walk=None, lstat=None, read_bytes=None):
    """`root_dir` 底下每個檔 → `(entries, errors)`。

    entries:`[(posix 相對路徑, sha256 或 None), ...]`,依路徑排序;errors:`[(path, error_text), ...]`。
    存在性用 lstat(預設 `os.lstat`):FileNotFoundError ⇒ 確認不存在 ⇒ `([], [])`;其他 OSError ⇒
    `([], [(root_dir, err)])`;存在但不是目錄 ⇒ `([], [(root_dir, "not a directory")])`。
    列舉用 walk(預設 `os.walk`),以 onerror 收集例外 —— 列舉失敗不得洗成空集合(3e 裁決 z3)。
    symlink(檔或目錄)記 None 且不追;symlink 目錄從走訪中移除(3d 裁決 (n))。讀不到 ⇒ None。
    `exclude_top` 只排除 `root_dir` 這一層同名的子目錄(及其整棵),更深層同名的不排除。
    """
    walk = walk or os.walk
    lstat = lstat or os.lstat
    read_bytes = read_bytes or _read_all_bytes
    try:
        st = lstat(root_dir)
    except FileNotFoundError:
        return [], []
    except OSError as e:
        return [], [(root_dir, _error_text(e))]
    if not stat.S_ISDIR(st.st_mode):
        return [], [(root_dir, "not a directory")]
    out, errors = [], []

    def onerror(e):
        errors.append((getattr(e, "filename", None) or root_dir, _error_text(e)))

    for dirpath, dirnames, filenames in walk(root_dir, onerror=onerror, followlinks=False):
        if exclude_top is not None and os.path.normcase(dirpath) == os.path.normcase(root_dir):
            dirnames[:] = [d for d in dirnames if d != exclude_top]
        keep = []
        for d in dirnames:
            full = os.path.join(dirpath, d)
            relp = os.path.relpath(full, root_dir).replace("\\", "/")
            try:
                mode = lstat(full).st_mode
            except OSError as e:
                errors.append((full, _error_text(e)))
                continue
            if stat.S_ISDIR(mode):
                keep.append(d)
            else:
                out.append((relp, None))
        dirnames[:] = keep
        for f in filenames:
            full = os.path.join(dirpath, f)
            relp = os.path.relpath(full, root_dir).replace("\\", "/")
            try:
                mode = lstat(full).st_mode
            except OSError:
                out.append((relp, None))
                continue
            if not stat.S_ISREG(mode):
                out.append((relp, None))
                continue
            try:
                out.append((relp, hashlib.sha256(read_bytes(full)).hexdigest()))
            except Exception:
                out.append((relp, None))
    return sorted(out, key=lambda item: item[0]), errors


def skill_mirror_violations(canon_dir, mirror_dirs):
    """R4 —— **一條規則,依當下佈局分支**。

    不寫成兩個檢查並排:並排會讓其中一個分支在當下佈局永遠不跑,
    那正是這條規則改寫前的處境(佈局改成 symlink 後,內容比對永遠不可能觸發,
    全輪唯一一次觸發還是人工製造的負向測試)。
    單一規則每次執行都必須回答「現在是哪種佈局」,沒有假裝在守的死路徑。
    """
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
            rel_entry = _rel(entry)
            if not os.path.lexists(entry):
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
                               "上游更新不會傳播到別處的副本。" % (rel_entry, target, _rel(canon_dir)))
                continue

            # 分支二:實體副本佈局 —— 兩份各自獨立,會 drift;遞迴 tree parity(票 146)
            if not os.path.exists(src):
                out.append("[R4] 正典缺少 %s/SKILL.md,鏡像 %s 卻還留著。\n"
                           "     正典被刪而鏡像留著舊的,一樣是不一致。"
                           % (_rel(os.path.join(canon_dir, name)), rel_entry))
                continue
            canon_entry = os.path.join(canon_dir, name)
            canon_files = set(p for p, _ in _walk_regular(canon_entry)[0])
            mirror_files = set()
            for p, _ in _walk_regular(entry)[0]:
                if os.path.islink(os.path.join(entry, *p.split("/"))):
                    out.append(u"[R4] 鏡像內含 symlink：%s/%s（第一版不追連結）" % (rel_entry, p))
                else:
                    mirror_files.add(p)
            for p in sorted(mirror_files - canon_files):
                out.append(u"[R4] 鏡像多出正典沒有的檔：%s/%s" % (rel_entry, p))
            for p in sorted(canon_files - mirror_files):
                out.append(u"[R4] 鏡像缺少 %s/%s —— 正典有而鏡像沒有。" % (rel_entry, p))
            for p in sorted(canon_files & mirror_files):
                try:
                    with io.open(os.path.join(entry, *p.split("/")), "rb") as fm:
                        mirror_md5 = hashlib.md5(fm.read()).hexdigest()
                    with io.open(os.path.join(canon_entry, *p.split("/")), "rb") as fc:
                        canon_md5 = hashlib.md5(fc.read()).hexdigest()
                    same = mirror_md5 == canon_md5
                except Exception:
                    same = False
                if not same:
                    out.append(u"[R4] 實體副本內容不一致：%s/%s 與正典不同。" % (rel_entry, p))
    return out


def _canonical_relpath_ok(p):
    """policy 內 path 是否已是 canonical POSIX 相對檔案路徑(3c 裁決 (k))。只判定,不修正。"""
    if not isinstance(p, str) or not p:
        return False
    if "\\" in p or p.startswith("/") or p.endswith("/"):
        return False
    if (len(p) >= 2 and p[1] == ":") or "://" in p or p.startswith("file:"):
        return False
    return all(seg not in ("", ".", "..") for seg in p.split("/"))


def _is_sha256_hex(v):
    return isinstance(v, str) and len(v) == 64 and all(c in "0123456789abcdef" for c in v)


def _extension_allowlist_ok(doc):
    """allowlist 文件是否合格(schema / 鍵集合 / 型別 / 檔案型項目 / path 唯一)。"""
    if not isinstance(doc, dict):
        return False
    version = doc.get("version")
    if doc.get("schema") != EXT_ALLOWLIST_SCHEMA or type(version) is not int \
            or version != EXT_ALLOWLIST_VERSION:
        return False
    if set(doc) != set(EXT_ALLOWLIST_FIELDS):
        return False
    for field, _label in _EXT_FILE_FIELDS:
        items = doc[field]
        if not isinstance(items, list):
            return False
        seen = set()
        for item in items:
            if not isinstance(item, dict) or set(item) != _EXT_ENTRY_KEYS:
                return False
            if not (_is_sha256_hex(item["sha256"]) and isinstance(item["note"], str)
                    and _canonical_relpath_ok(item["path"])):
                return False
            if item["path"] in seen:
                return False
            seen.add(item["path"])
    return _is_str_list(doc["project_settings_hook_commands"]) and _is_str_list(doc["mcp_json_servers"])


def _logical_path_ok(p):
    """inventory 的 path 是否屬四種合法匿名邏輯路徑(v2 synced 契約)。只判定,不修正。"""
    if not isinstance(p, str):
        return False
    if p in ("%s/.bucket-%s" % (r, EXT_BUCKET_TOKEN) for r in EXT_SYNCED_ROOTS):
        return True
    parts = p.split("/")
    if len(parts) < 3 or parts[0] not in EXT_SYNCED_ROOTS or parts[1] != EXT_BUCKET_TOKEN:
        return False
    rest = parts[2:]
    if not _canonical_relpath_ok("/".join(rest)):
        return False
    return all(seg != EXT_BUCKET_TOKEN and not seg.startswith(".bucket-") for seg in rest)


def _extension_inventory_ok(doc):
    """inventory 文件是否合格:鍵集合、schema、version(int)、entries 每項鍵 / 四種邏輯路徑 / path 唯一 /
    sha256 / note 型別(3g 契約;五處閉合裁決第 5 點)。不拋例外。"""
    try:
        if not isinstance(doc, dict) or set(doc) != set(EXT_INVENTORY_FIELDS):
            return False
        version = doc["version"]
        if doc["schema"] != EXT_INVENTORY_SCHEMA or type(version) is not int \
                or version != EXT_INVENTORY_VERSION:
            return False
        entries = doc["entries"]
        if not isinstance(entries, list):
            return False
        seen = set()
        for item in entries:
            if not isinstance(item, dict) or set(item) != _EXT_ENTRY_KEYS:
                return False
            if not (_logical_path_ok(item["path"]) and _is_sha256_hex(item["sha256"])
                    and isinstance(item["note"], str)):
                return False
            if item["path"] in seen:
                return False
            seen.add(item["path"])
        return True
    except Exception:
        return False


def _policy_facts(root, rel, ok_fn, policy_source):
    """canonical policy 檔的事實:`{"path", "state", "blob", "worktree", "policy"}`。

    `policy_source="head"`:流程同 `evidence_policy_facts` 第 1–5 步 —— 只認 HEAD blob;工作樹只做一次
    hash-object 比對,之後只讀 HEAD blob。state ∈ uninitialized / uncommitted / identity_mismatch /
    worktree_differs / malformed / ok。root 不是 git 最上層 ⇒ identity_mismatch。
    `policy_source="index"`(H-6,policy-only commit):只讀 index(`git ls-files -s` + `git cat-file`),
    **不做 worktree identity 比對**,worktree 的內容或存在與否不影響結果。state ∈ index_missing /
    index_conflict / index_nonregular / index_unreadable / malformed / ok。
    非 ok 時 policy 為 None。除 policy_source 不合法(ValueError)外不拋例外。
    """
    if policy_source not in EXT_POLICY_SOURCES:
        raise ValueError("policy_source 只接受 %s,收到 %r" % ("/".join(EXT_POLICY_SOURCES), policy_source))
    out = {"path": rel, "state": "identity_mismatch", "blob": None, "worktree": None, "policy": None}
    if policy_source == "index":
        out["state"] = "index_unreadable"
        try:
            if not _root_is_toplevel(root):
                return out
            listed = _git_bytes(root, ["ls-files", "-s", "--", rel])
            if listed is None:
                return out
            rows = []
            for line in listed.decode("utf-8", "replace").splitlines():
                meta, _, path = line.partition("\t")
                if path == rel:
                    rows.append(meta.split())
            if not rows:
                out["state"] = "index_missing"
                return out
            if any(len(r) != 3 or r[2] != "0" for r in rows):
                out["state"] = "index_conflict"
                return out
            mode, blob, _stage = rows[0]
            if mode not in ("100644", "100755"):
                out["state"] = "index_nonregular"
                return out
            raw = _git_bytes(root, ["cat-file", "blob", blob])
            if raw is None:
                return out
            out["blob"] = blob
            try:
                doc = json.loads(raw.decode("utf-8"))
            except Exception:
                doc = None
            if not ok_fn(doc):
                out["state"] = "malformed"
                return out
            out["policy"] = doc
            out["state"] = "ok"
        except Exception:
            pass
        return out
    try:
        exists = os.path.exists(os.path.join(os.fspath(root), *rel.split("/")))
        if not _root_is_toplevel(root):
            return out
        head = _git_lines(root, ["rev-parse", "HEAD:" + rel], 1)
        if not head:
            out["state"] = "uncommitted" if exists else "uninitialized"
            return out
        out["blob"] = head[0]
        worktree = _git_lines(root, ["hash-object", rel], 1) if exists else None
        if not worktree:
            return out
        out["worktree"] = worktree[0]
        if worktree[0] != head[0]:
            out["state"] = "worktree_differs"
            return out
        raw = _git_bytes(root, ["cat-file", "blob", head[0]])
        if raw is None:
            return out
        try:
            doc = json.loads(raw.decode("utf-8"))
        except Exception:
            doc = None
        if not ok_fn(doc):
            out["state"] = "malformed"
            return out
        out["policy"] = doc
        out["state"] = "ok"
    except Exception:
        pass
    return out


def extension_allowlist_facts(root, policy_source="head"):
    """`<root>` 的 allowlist 事實(形狀與狀態見 `_policy_facts`)。"""
    return _policy_facts(root, EXT_ALLOWLIST_FILE, _extension_allowlist_ok, policy_source)


def extension_inventory_facts(root, policy_source="head"):
    """`<root>` 的 synced inventory 事實(形狀與狀態見 `_policy_facts`;malformed 經 `_extension_inventory_ok`)。"""
    return _policy_facts(root, EXT_INVENTORY_FILE, _extension_inventory_ok, policy_source)


def _hook_commands(node, acc):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "command" and isinstance(value, str):
                acc.append(value)
            else:
                _hook_commands(value, acc)
    elif isinstance(node, list):
        for value in node:
            _hook_commands(value, acc)


def _synced_root(name, root, walk, lstat, read_bytes):
    """一個 synced 根 → `(entries, errors)`。entries 是 `(邏輯路徑, sha256 或 None)`;errors 是
    `("synced", path, text)`。根不存在 ⇒ 空;列舉成功且無直接子項 ⇒ 空(3f-2 裁決 (ww))。
    根或直接子項結構錯誤 ⇒ 不走訪 bucket、不產生該根的 entries(裁決 (yy))。bucket 真名不進任何輸出。"""
    entries, errors = [], []
    try:
        st = lstat(root)
    except FileNotFoundError:
        return entries, errors
    except OSError as e:
        errors.append(("synced", root, "lstat failed: " + _error_text(e)))
        return entries, errors
    if not stat.S_ISDIR(st.st_mode):
        errors.append(("synced", root, "bucket structure: root is symlink/not a directory"))
        return entries, errors
    try:
        names = sorted(os.listdir(root))
    except OSError as e:
        errors.append(("synced", root, "listdir failed: " + _error_text(e)))
        return entries, errors
    if not names:
        return entries, errors
    dirs, files, other = [], [], []
    for n in names:
        try:
            mode = lstat(os.path.join(root, n)).st_mode
        except OSError as e:
            errors.append(("synced", root, "child lstat failed: " + _error_text(e)))
            return entries, errors
        if stat.S_ISDIR(mode):
            dirs.append(n)
        elif stat.S_ISREG(mode):
            files.append(n)
        else:
            other.append(n)
    if other or len(dirs) != 1:
        errors.append(("synced", root, "bucket structure: expected exactly one bucket directory and its marker"
                       "(directories=%d, non-regular children=%d)" % (len(dirs), len(other))))
        return entries, errors
    marker = ".bucket-" + dirs[0]
    extra = [f for f in files if f != marker]
    if marker not in files or extra:
        errors.append(("synced", root, "bucket structure: marker missing or mismatched, or extra root files"
                       "(regular children=%d)" % len(files)))
        return entries, errors
    try:
        msha = hashlib.sha256(read_bytes(os.path.join(root, marker))).hexdigest()
    except Exception:
        msha = None
    entries.append(("%s/.bucket-%s" % (name, EXT_BUCKET_TOKEN), msha))
    sub, sub_errors = _walk_regular(os.path.join(root, dirs[0]), walk=walk, lstat=lstat, read_bytes=read_bytes)
    entries.extend(("%s/%s/%s" % (name, EXT_BUCKET_TOKEN, p), s) for p, s in sub)
    errors.extend(("synced", p, t) for p, t in sub_errors)
    return entries, errors


def extension_surface_facts(dev_mods_dir, synced_dirs, canon_dir, mirror_dirs, project_settings_paths,
                            mcp_json_path, user_skills_dir, user_commands_dir,
                            walk=None, lstat=None, read_bytes=None):
    """已知靜態載入入口的事實(恰好八鍵)。純讀、無副作用、所有路徑由參數注入,不讀任何快取。

    `synced_dirs`:`[(root_name, path), ...]`,root_name ∈ EXT_SYNCED_ROOTS(3f-2 裁決 (xx))。
    無效名 / 重複名 ⇒ 結構化錯誤,該名稱的所有項目都不走訪;其他唯一且合法的根照常觀測。
    `errors`:`[(surface_name, path, error_text), ...]`;列舉失敗不得洗成空集合。
    """
    lstat_fn = lstat or os.lstat
    read_fn = read_bytes or _read_all_bytes
    errors = []

    def walked(surface, root_dir, exclude_top=None):
        found, errs = _walk_regular(root_dir, exclude_top=exclude_top, walk=walk, lstat=lstat, read_bytes=read_bytes)
        errors.extend((surface, p, t) for p, t in errs)
        return found

    dev_mod_files = walked("dev-mods", dev_mods_dir)
    user_skill_plugins = walked("user-skills", user_skills_dir, exclude_top="synced")
    user_commands = walked("user-commands", user_commands_dir)
    synced_files = []
    valid = []
    for item in synced_dirs or []:
        if isinstance(item, (tuple, list)) and len(item) == 2 and item[0] in EXT_SYNCED_ROOTS:
            valid.append((item[0], item[1]))
        else:
            where = item[1] if isinstance(item, (tuple, list)) and len(item) == 2 else item
            errors.append(("synced", str(where), "bucket structure: invalid root name"))
    seen = {}
    for name, _p in valid:
        seen[name] = seen.get(name, 0) + 1
    for name, path in valid:
        if seen[name] > 1:
            errors.append(("synced", path, "bucket structure: duplicate root name"))
            continue
        found, errs = _synced_root(name, path, walk, lstat_fn, read_fn)
        synced_files.extend(found)
        errors.extend(errs)
    hook_commands = []
    for path in project_settings_paths:
        if not os.path.exists(path):
            continue
        try:
            with io.open(path, encoding="utf-8") as f:
                doc = json.load(f)
            if not isinstance(doc, dict):
                raise ValueError("not an object")
            _hook_commands(doc.get("hooks"), hook_commands)
        except Exception:
            hook_commands.append(u"%s: unreadable" % path)
    mcp_servers = []
    if os.path.exists(mcp_json_path):
        try:
            with io.open(mcp_json_path, encoding="utf-8") as f:
                doc = json.load(f)
            servers = doc.get("mcpServers", {}) if isinstance(doc, dict) else None
            if not isinstance(servers, dict):
                raise ValueError("mcpServers is not an object")
            mcp_servers = list(servers)
        except Exception:
            mcp_servers = [u"%s: unreadable" % mcp_json_path]
    return {
        "dev_mod_files": dev_mod_files,
        "synced_files": synced_files,
        "r4_violations": skill_mirror_violations(canon_dir, mirror_dirs),
        "project_hook_commands": hook_commands,
        "mcp_json_servers": mcp_servers,
        "user_skill_plugins": user_skill_plugins,
        "user_commands": user_commands,
        "errors": errors,
    }


def synced_verification(inventory_facts, surfaces):
    """synced 納管的結構化結果:恰好六鍵 `{"verified","reason","missing","extra","mismatch","structure_errors"}`。

    順序(v2 契約):inventory 為 None 或非 ok ⇒ 未納管(不讀 entries、不拋例外);synced 結構錯誤 ⇒ 不通過;
    否則以 entries 的 {path: sha256} 與 synced_files 比對 —— 額外 / 缺少 / 內容不符(含磁碟 sha 為 None)任一 > 0
    ⇒ 不通過;全 0 ⇒ 通過(含兩邊皆空)。
    """
    out = {"verified": False, "reason": None, "missing": 0, "extra": 0, "mismatch": 0, "structure_errors": 0}
    if inventory_facts is None:
        out["reason"] = u"synced 未納管：inventory absent"
        return out
    state = inventory_facts.get("state") if isinstance(inventory_facts, dict) else "malformed"
    if state != "ok":
        out["reason"] = u"synced 未納管：inventory %s" % state
        return out
    surfaces = surfaces if isinstance(surfaces, dict) else {}
    structure = [e for e in (surfaces.get("errors") or []) if e and e[0] == "synced"]
    if structure:
        out["structure_errors"] = len(structure)
        out["reason"] = u"synced 結構錯誤：%s" % structure[0][2]
        return out
    want = dict((e["path"], e["sha256"]) for e in inventory_facts["policy"]["entries"])
    have = dict((p, s) for p, s in (surfaces.get("synced_files") or []))
    out["extra"] = len([p for p in have if p not in want])
    out["missing"] = len([p for p in want if p not in have])
    out["mismatch"] = len([p for p in have if p in want and (have[p] is None or have[p] != want[p])])
    if out["extra"] or out["missing"] or out["mismatch"]:
        out["reason"] = u"額外 %d / 缺少 %d / 內容不符 %d" % (out["extra"], out["missing"], out["mismatch"])
        return out
    out["verified"] = True
    return out


def _extension_first_reason(facts, surfaces, inventory):
    """`(state, category, reason)`。判定只在這裡發生一次;渲染不再判定(3e 裁決 z1)。

    順序:1 allowlist 非 ok ⇒ VIOLATION;2 鍵集合 ≠ 八鍵 ⇒ UNKNOWN / observation_missing;3 檔案型入口未登記
    ⇒ VIOLATION;4 R4;5 hook;6 mcp;7 errors 非空 ⇒ UNKNOWN / observation_missing;8 synced(inventory 為
    `EXT_INVENTORY_UNCHECKED` ⇒ 舊語意「非空即未受管(未評估)」;否則依 `synced_verification`);9 DECLARED_OK。
    """
    state = facts.get("state") if isinstance(facts, dict) else None
    if state != "ok":
        return (EXT_VIOLATION, EXT_CAT_ALLOWLIST, _EXT_STATE_TEXT.get(state, _EXT_STATE_TEXT["malformed"]))
    keys = set(surfaces) if isinstance(surfaces, dict) else set()
    if keys != EXT_SURFACE_KEYS:
        return (EXT_UNKNOWN, EXT_CAT_OBSERVATION, u"surfaces 不完整：缺 %s / 多 %s；fail-closed"
                % (sorted(EXT_SURFACE_KEYS - keys), sorted(keys - EXT_SURFACE_KEYS)))
    policy = facts["policy"]
    for field, label in _EXT_FILE_FIELDS:
        allowed = set((item["path"], item["sha256"]) for item in policy[field])
        bad = [relp for relp, sha in surfaces[field] if sha is None or (relp, sha) not in allowed]
        if bad:
            return (EXT_VIOLATION, EXT_CAT_UNREGISTERED,
                    u"%s 未登記（path, sha256）：%s（共 %d 筆）" % (label, bad[0], len(bad)))
    r4 = surfaces["r4_violations"]
    if r4:
        return (EXT_VIOLATION, EXT_CAT_R4, u"%s（共 %d 筆）" % (str(r4[0]).splitlines()[0], len(r4)))
    bad = [c for c in surfaces["project_hook_commands"] if c not in policy["project_settings_hook_commands"]]
    if bad:
        return (EXT_VIOLATION, EXT_CAT_HOOK, u"專案 settings hook 未登記：%s（共 %d 筆）" % (bad[0], len(bad)))
    bad = [s for s in surfaces["mcp_json_servers"] if s not in policy["mcp_json_servers"]]
    if bad:
        return (EXT_VIOLATION, EXT_CAT_MCP, u".mcp.json server 未登記：%s（共 %d 筆）" % (bad[0], len(bad)))
    errors = surfaces["errors"]
    if errors:
        first = errors[0]
        return (EXT_UNKNOWN, EXT_CAT_OBSERVATION,
                u"觀測失敗：%s: %s（共 %d 筆）" % (first[0], first[-1], len(errors)))
    if inventory is EXT_INVENTORY_UNCHECKED:
        if surfaces["synced_files"]:
            return (EXT_UNKNOWN, EXT_CAT_UNMANAGED, u"未受管入口：synced（未評估）")
    else:
        v = synced_verification(inventory, surfaces)
        if v["verified"] is not True:
            return (EXT_UNKNOWN, EXT_CAT_UNMANAGED, u"未受管入口：synced（" + v["reason"] + u"）")
    return (EXT_DECLARED_OK, None, None)


def _extension_render_lines(state, category, reason, facts):
    """恰好兩行:static surfaces 與 runtime loaded set 分欄;runtime 欄固定未證明。facts 可為 None(不帶 blob)。"""
    if state == EXT_DECLARED_OK:
        blob = (facts.get("blob") or "")[:12] if isinstance(facts, dict) else ""
        first = u"static surfaces: 已知靜態入口符合已提交的 allowlist（%s）" % blob
    else:
        first = u"static surfaces: %s —— %s" % (state, reason)
    return [first, _EXT_RUNTIME_LINE]


def extension_state(facts, surfaces):
    """四態之一(實際可回的只有 VIOLATION / UNKNOWN / DECLARED_OK)。兩參數相容 wrapper:synced 未評估。"""
    return _extension_first_reason(facts, surfaces, EXT_INVENTORY_UNCHECKED)[0]


def extension_status_lines(facts, surfaces):
    """兩參數相容 wrapper = 一次判定 + 渲染;synced 未評估。production 不經這裡(3e 裁決 z1)。"""
    state, category, reason = _extension_first_reason(facts, surfaces, EXT_INVENTORY_UNCHECKED)
    return _extension_render_lines(state, category, reason, facts)


def extension_report(repo_root, claude_root=None, walk=None, lstat=None, read_bytes=None, policy_source="head"):
    """146 的單一判定入口(十四鍵)。gate 的 pre-commit 與 status 都消費這一份。

    claude_root 為 None ⇒ `expanduser("~")/.claude`(fallback);給值 ⇒ 該值(param),不 fallback(補鎖 3)。
    前置觀測失敗(不存在 / 不是目錄 / lstat 失敗 / `~` 沒展開)⇒ observation="claude_root_invalid",
    facts / surfaces / inventory / synced 皆 None,判定 0 次。否則判定恰好 1 次,lines 由同一結果渲染。
    authority 固定 "ok";runtime_assurance 固定 UNPROVEN —— 本函式不證明本 session 實際載入了什麼。
    """
    if policy_source not in EXT_POLICY_SOURCES:
        raise ValueError("policy_source 只接受 %s,收到 %r" % ("/".join(EXT_POLICY_SOURCES), policy_source))
    lstat_fn = lstat or os.lstat
    if claude_root is None:
        home = os.path.expanduser("~")
        claude_root = os.path.join(home, ".claude")
        source = "fallback"
        unexpanded = home.startswith("~")
    else:
        claude_root = os.fspath(claude_root)
        source = "param"
        unexpanded = False
    report = {"facts": None, "surfaces": None, "state": EXT_UNKNOWN, "category": EXT_CAT_OBSERVATION,
              "reason": None, "lines": None, "runtime_assurance": EXT_RUNTIME_UNPROVEN,
              "claude_root": claude_root, "claude_root_source": source, "authority": "ok",
              "observation": "ok", "inventory": None, "synced": None, "policy_source": policy_source}
    why = None
    if unexpanded:
        why = u"家目錄沒有展開"
    else:
        try:
            if not stat.S_ISDIR(lstat_fn(claude_root).st_mode):
                why = u"不是目錄"
        except FileNotFoundError:
            why = u"不存在"
        except OSError as e:
            why = u"lstat 失敗（%s）" % type(e).__name__
    if why is not None:
        report["observation"] = "claude_root_invalid"
        report["reason"] = u"claude_root 無法確定：%s（%s）" % (why, source)
        report["lines"] = _extension_render_lines(EXT_UNKNOWN, EXT_CAT_OBSERVATION, report["reason"], None)
        return report
    root = os.fspath(repo_root)
    facts = extension_allowlist_facts(root, policy_source=policy_source)
    inventory = extension_inventory_facts(root, policy_source=policy_source)
    surfaces = extension_surface_facts(
        os.path.join(claude_root, "dev-mods"),
        [("skills", os.path.join(claude_root, "skills", "synced")),
         ("plugins", os.path.join(claude_root, "plugins", "synced"))],
        os.path.join(root, ".agents", "skills"),
        [os.path.join(root, ".claude", "skills"), os.path.join(root, "skills")],
        [os.path.join(root, ".claude", "settings.json"), os.path.join(root, ".claude", "settings.local.json")],
        os.path.join(root, ".mcp.json"),
        os.path.join(claude_root, "skills"),
        os.path.join(claude_root, "commands"),
        walk=walk, lstat=lstat, read_bytes=read_bytes)
    state, category, reason = _extension_first_reason(facts, surfaces, inventory)
    report.update({"facts": facts, "surfaces": surfaces, "state": state, "category": category,
                   "reason": reason, "lines": _extension_render_lines(state, category, reason, facts),
                   "inventory": inventory, "synced": synced_verification(inventory, surfaces)})
    return report


def _completeness_problems(comp):
    """completeness 的型別問題清單(空 = 型別正確)。〈二十三〉7 (i)。"""
    if not isinstance(comp, dict):
        return ["completeness 缺欄或型別不符"]
    problems = []
    options = comp.get("options")
    if not isinstance(options, dict) or any(k not in options for k in COMPLETENESS_OPTIONS):
        problems.append("options 缺欄或型別不符")
    for key in ("cacheprovider_blocked", "shouldstop", "shouldfail"):
        if not isinstance(comp.get(key), bool):
            problems.append("%s 缺欄或型別不符" % key)
    pre = comp.get("pre_narrowing")
    if not isinstance(pre, dict) or not all(
            isinstance(k, str) and _is_str_list(v) for k, v in pre.items()):
        problems.append("pre_narrowing 缺欄或型別不符")
    plugins = comp.get("plugins")
    if not isinstance(plugins, list) or not plugins or not all(
            isinstance(p, dict) and isinstance(p.get("name"), str)
            and p.get("kind") in PLUGIN_KINDS for p in plugins):
        problems.append("plugins 缺欄或型別不符")
    # 〈二十九〉2 (viii)–(xiii) 的事實。Station 4d 之前的 session 沒有這些欄位 ⇒ 不合格 ⇒ unknown。
    for key in ("override_ini",):
        if key not in comp or not (comp[key] is None or _is_str_list(comp[key])):
            problems.append("%s 缺欄或型別不符" % key)
    for key in ("inifilename", "inipath", "pytest_version"):
        if key not in comp or not (comp[key] is None or isinstance(comp[key], str)):
            problems.append("%s 缺欄或型別不符" % key)
    if not _is_str_list(comp.get("blocked")):
        problems.append("blocked 缺欄或型別不符")
    # (xi):root producer 那一項必須在;policy 指定的設定檔那一項由 verdict 在知道 config_file 之後查。
    blobs = comp.get("config_blobs")
    if not isinstance(blobs, dict) or ROOT_CONFTEST not in blobs or not all(
            isinstance(b, dict)
            and all(b.get(k) is None or isinstance(b.get(k), str) for k in ("worktree", "head"))
            for b in blobs.values()):
        problems.append("config_blobs 缺欄或型別不符")
    # 票 145 Station 4g:policy 事實(7 鍵;〈五十一〉裁決 3)。Station 4g 之前的 session 沒有 ⇒ 不合格 ⇒ unknown。
    ep = comp.get("evidence_policy")
    if not isinstance(ep, dict) or any(k not in ep for k in EVIDENCE_POLICY_KEYS):
        problems.append("evidence_policy 缺欄或型別不符")
    # 〈三十五〉3 (xiv)–(xviii) 的事實。Station 4e 之前的 session 沒有這些欄位 ⇒ 不合格 ⇒ unknown。
    # 型別在這裡驗,malformed 的事實不得只靠 verdict 的值判斷而繞過。
    if type(comp.get("optimize")) is not int:            # int,不含 bool
        problems.append("optimize 缺欄或型別不符")
    if not isinstance(comp.get("python_version"), str):
        problems.append("python_version 缺欄或型別不符")
    if isinstance(options, dict):
        for key in ("runxfail", "trace", "usepdb"):
            if not isinstance(options.get(key), bool):
                problems.append("options.%s 缺欄或型別不符" % key)
        warn = options.get("pythonwarnings")
        if not (warn is None or _is_str_list(warn)):
            problems.append("options.pythonwarnings 型別不符")
    return problems


def _completeness_verdict(run, tf, idents):
    """位置參數已涵蓋 `tf` 之後,依〈二十三〉7 (i)–(vii) 判 `"true"` / `"false"` / `"unknown"`。

    - (i) 缺欄 / 型別錯 ⇒ unknown
    - (P) evidence policy 不可用(未提交、工作樹 ≠ HEAD、格式不明、超出能力邊界、與 HEAD 設定檔的 addopts
      推導不一致;`_effective_policy`)⇒ unknown(票 145 Station 4g;〈四十八〉48.1)。
      以下的「effective」= 框架能力邊界 B ∩ policy
    - (vii)(vii′) 有 plugin 不在受支援範圍(含版本不在清單的 dist),或 known_dist 的 (名稱, 版本) 不在
      effective 的 `dists` ⇒ unknown(在支援邊界之外,不知道)
    - (xii) 有任何 `-p no:<name>` ⇒ unknown
    - (xiii) pytest 版本不在 effective 的 `pytest_versions` ⇒ unknown
    - (viii) `override_ini` 不恰等於 policy 的 `committed_overrides` ⇒ unknown(本次的收集定義被覆寫)
    - (ix) 有 `-c` / `--config-file` ⇒ unknown(即使指向已提交的權威檔)
    - (x) 實際採用的設定檔不是 policy 的 `config_file` ⇒ unknown
    - (xi) `ROOT_CONFTEST` 與 policy 的 `config_file` 任一檔的工作樹 blob ≠ HEAD blob,或取不到 ⇒ unknown
    - (xiv) `sys.flags.optimize` 不是 0 ⇒ unknown(assert 可能沒有執行;〈三十五〉3)
    - (xviii) Python major.minor 不在 effective 的 `python_versions` ⇒ unknown
    - (xv)(xvii) `runxfail` / `trace` 不是 False ⇒ unknown;(xvi) pytest `-W` 有值 ⇒ unknown
      (assertmode 不判定:`optimize == 0` 時 plain 只影響 reporting)
    - (xix) `usepdb`(`--pdb`)不是 False ⇒ unknown(〈三十九〉39.3 第 3 點;與 (xvii) 同理:除錯模式下人可在
      中途改變狀態)。`usepdb_cls`(`--pdbcls`)不判定(〈四十一〉41.1 第 1 點)
    - (ii) `lf` / `stepwise` / `stepwise_skip` 不是 False ⇒ false(縮小機制作用中)。
      `cacheprovider_blocked` 只是紀錄,不再有判定權(〈二十九〉2 (xii) 取代〈二十三〉裁決 4)
    - (iii) maxfail / collectonly / setuponly / setupplan ⇒ unknown
    - (iv) shouldstop / shouldfail ⇒ unknown
    - (v) 縮小前全集 != 本 run 該檔的 collected ⇒ false
    - (vi) 有 selected 身分沒到執行完成的終態 ⇒ unknown
    """
    comp = run.get("completeness")
    if _completeness_problems(comp):
        return "unknown"
    policy = _effective_policy(comp["evidence_policy"])
    if policy is None:
        return "unknown"
    accepted_dists = set(tuple(d) for d in _effective(KNOWN_DISTS, [tuple(d) for d in policy["dists"]]))
    if any(p["kind"] not in SUPPORTED_PLUGIN_KINDS for p in comp["plugins"]):
        return "unknown"
    if any(p["kind"] == "known_dist" and not _known_dists_accepted(p, accepted_dists)
           for p in comp["plugins"]):
        return "unknown"
    if comp["blocked"]:
        return "unknown"
    if comp["pytest_version"] not in _effective(KNOWN_PYTEST_VERSIONS, policy["pytest_versions"]):
        return "unknown"
    if comp["override_ini"] != list(policy["committed_overrides"]):
        return "unknown"
    if comp["inifilename"] is not None:
        return "unknown"
    config_file = policy["config_file"]
    if config_file not in FRAMEWORK_CONFIG_FILES or comp["inipath"] != config_file:
        return "unknown"
    blobs = comp["config_blobs"]
    for p in (config_file, ROOT_CONFTEST):
        b = blobs.get(p)
        if not (isinstance(b, dict) and b.get("worktree") and b.get("worktree") == b.get("head")):
            return "unknown"
    options = comp["options"]
    if comp["optimize"] != 0:
        return "unknown"
    if comp["python_version"] not in _effective(KNOWN_PYTHON_VERSIONS, policy["python_versions"]):
        return "unknown"
    if options["runxfail"] is not False or options["trace"] is not False:
        return "unknown"
    if options["usepdb"] is not False:
        return "unknown"
    if options["pythonwarnings"] not in (None, []):
        return "unknown"
    if not (options["lf"] is False and options["stepwise"] is False
            and options["stepwise_skip"] is False):
        return "false"
    maxfail = options["maxfail"]
    if not (maxfail is None or (type(maxfail) is int and maxfail == 0)):
        return "unknown"
    if not all(options[k] is False for k in ("collectonly", "setuponly", "setupplan")):
        return "unknown"
    if comp["shouldstop"] is not False or comp["shouldfail"] is not False:
        return "unknown"
    pre = comp["pre_narrowing"].get(tf)
    if pre is None or set(pre) != set(idents):
        return "false"
    deselected = set(run["deselected"])
    outcomes = run["outcomes"]
    if any(outcomes.get(n) not in EXECUTED_OUTCOMES for n in idents if n not in deselected):
        return "unknown"
    return "true"
