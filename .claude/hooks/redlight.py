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


def _normalize_arg(arg, root, invocation_dir):
    """一個 pytest 位置參數 → root 相對的 posix 路徑(保留 `::` 之後那段)。

    無法判讀(空字串、落在 root 之外、跨磁碟)⇒ None。**絕對路徑不落帳** ——
    帳本只存 root 相對路徑,`invocation_dir` 只用來解析,不寫進紀錄。
    """
    s = str(arg).replace("\\", "/")
    path, sep, rest = s.partition("::")
    if not path:
        return None
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
                        "maxfail", "collectonly", "setuponly", "setupplan")

PLUGIN_KINDS = ("builtin", "root_conftest", "known_dist", "other")
SUPPORTED_PLUGIN_KINDS = ("builtin", "root_conftest", "known_dist")
BUILTIN_MODULE = "_pytest"
ROOT_CONFTEST = "tests/conftest.py"
OUTSIDE = "<outside>"

# ── 票 145 Station 4d —— 收集定義完整性與版本邊界(〈二十九〉2 (vii′)–(xiii))
# 以下四組是「已盤點」清單,**變更須走票**。版本邊界總表(〈二十九〉2):
#   pytest 內建 ⇒ 鎖 pytest 版本;root producer ⇒ 鎖 tests/conftest.py 已提交 blob;
#   repo 收集設定 ⇒ 鎖 pyproject.toml 已提交 blob;已知第三方 plugin ⇒ 鎖 dist 名稱 + 精確版本;
#   未知 plugin ⇒ fail-closed。

# (vii′) 已知第三方 plugin:(dist 名稱, 精確版本)。只看名稱不算(名稱可被冒用),版本不同也不算。
KNOWN_DISTS = (("anyio", "4.15.0"),)

# (xiii) P1 的盤點只對這些 pytest 版本成立;換版後非 ini 的 CLI 選項要重新盤點。
KNOWN_PYTEST_VERSIONS = ("9.1.1",)

# (viii) 已提交 pyproject.toml 的 addopts 帶來的 override 清單(`--strict-markers` ⇒
# `strict_markers=true`)。由 tests/test_redlight.py 的鎖步測試對照已提交的 addopts。
COMMITTED_ADDOPTS_OVERRIDES = ("strict_markers=true",)

# (x) 唯一可接受的設定檔(root 相對路徑);(xi) 工作樹內容必須等於 HEAD blob 的檔。
CONFIG_FILE = "pyproject.toml"
COMMITTED_FILES = (CONFIG_FILE, ROOT_CONFTEST)

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


def _plugin_path_name(name, root):
    """路徑型名稱 → root 相對 posix 路徑;root 以外(含跨磁碟)⇒ `<outside>`。"""
    try:
        rel = os.path.relpath(os.path.normpath(name), os.path.normpath(os.fspath(root)))
    except ValueError:
        return OUTSIDE
    rel = rel.replace("\\", "/")
    if rel == ".." or rel.startswith("../") or os.path.isabs(rel):
        return OUTSIDE
    return rel


def classify_plugins(root, name_plugins, distinfo):
    """`list_name_plugin()` 與 `list_plugin_distinfo()` 的原始事實 → `[{"name", "kind"}]`。

    依序判定(〈二十三〉3,經〈二十九〉2 (vii′) 修訂):
      1. plugin **物件**出現在 distinfo 配對中 ⇒ (dist 名稱, 精確版本) 在 `KNOWN_DISTS` 為 known_dist,
         否則 other(只看名稱相同不算 —— 名稱可被冒用;版本缺失或不同也是 other)
      2. 名稱是絕對路徑(conftest 的註冊名稱)⇒ root 相對路徑恰為 `ROOT_CONFTEST` 為 root_conftest,否則 other
      3. 定義模組為 `_pytest` 或 `_pytest.*` ⇒ builtin
      4. 其他(含 `-p no:` 留下的 `(name, None)`)⇒ other
    帳本只記正規化名稱:路徑型一律轉 root 相對路徑(root 以外記 `<outside>`),不記絕對路徑。
    配對到 dist 的項目另記 `dists`(`[[名稱, 版本], ...]`)。
    """
    dists = [(p, _dist_name(d), _dist_version(d)) for p, d in (distinfo or [])]
    out = []
    for name, plugin in name_plugins or []:
        name = str(name)
        is_path = os.path.isabs(name)
        shown = _plugin_path_name(name, root) if is_path else name
        paired = [(dn, dv) for p, dn, dv in dists if p is plugin]
        if paired:
            kind = "known_dist" if all(pair in KNOWN_DISTS for pair in paired) else "other"
        elif is_path:
            kind = "root_conftest" if shown == ROOT_CONFTEST else "other"
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


def blocked_plugins(name_plugins):
    """`list_name_plugin()` 中值為 None 的名稱 —— `-p no:<name>` 的 pluggy 表示方式
    (`pluggy/_manager.py:230-233`)。〈二十九〉2 (xii)。"""
    return [str(name) for name, plugin in (name_plugins or []) if plugin is None]


def normalize_config_path(value, root):
    """`inifilename` / `inipath` → 落帳形狀。None ⇒ None;絕對路徑 ⇒ root 相對 posix 路徑
    (root 以外 `<outside>`);相對路徑 ⇒ 反斜線換成 `/`。**不落帳絕對路徑。**"""
    if value is None:
        return None
    text = os.fspath(value) if isinstance(value, os.PathLike) else str(value)
    if os.path.isabs(text):
        return _plugin_path_name(text, root)
    return text.replace("\\", "/")


def normalize_overrides(values, root):
    """`config.option.override_ini`(解析後清單)→ 落帳形狀。不是 list ⇒ None。
    值是絕對路徑的項目(例 `-o cache_dir=…`)只把值換成 root 相對路徑或 `<outside>`,不落帳絕對路徑。"""
    if not isinstance(values, (list, tuple)):
        return None
    out = []
    for item in values:
        key, sep, val = str(item).partition("=")
        if sep and os.path.isabs(val):
            val = _plugin_path_name(val, root)
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


def committed_blobs(root, paths=COMMITTED_FILES):
    """`{path: {"worktree": blob, "head": blob}}` —— 工作樹檔案(`git hash-object`,依
    .gitattributes 正規化)與 `HEAD:<path>` 的 blob。〈二十九〉2 (xi)。

    git 不可用、不是 repo、檔案不存在或任何一步出錯 ⇒ 該值 None(缺欄 ⇒ 不得為 `"true"`)。
    **不拋例外**:這是 producer 在 sessionfinish 呼叫的,不得讓 pytest 失敗。
    """
    paths = list(paths)
    out = dict((p, {"worktree": None, "head": None}) for p in paths)
    try:
        worktree = _git_lines(root, ["hash-object"] + paths, len(paths))
        head = _git_lines(root, ["rev-parse"] + ["HEAD:" + p for p in paths], len(paths))
        for i, p in enumerate(paths):
            out[p]["worktree"] = worktree[i] if worktree else None
            out[p]["head"] = head[i] if head else None
    except Exception:
        pass
    return out


def _is_str_list(v):
    return isinstance(v, list) and all(isinstance(n, str) for n in v)


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
    blobs = comp.get("config_blobs")
    if not isinstance(blobs, dict) or not all(
            isinstance(blobs.get(p), dict)
            and all(blobs[p].get(k) is None or isinstance(blobs[p].get(k), str)
                    for k in ("worktree", "head"))
            for p in COMMITTED_FILES):
        problems.append("config_blobs 缺欄或型別不符")
    return problems


def _completeness_verdict(run, tf, idents):
    """位置參數已涵蓋 `tf` 之後,依〈二十三〉7 (i)–(vii) 判 `"true"` / `"false"` / `"unknown"`。

    - (i) 缺欄 / 型別錯 ⇒ unknown
    - (vii)(vii′) 有 plugin 不在受支援範圍(含版本不在清單的 dist)⇒ unknown(在支援邊界之外,不知道)
    - (xii) 有任何 `-p no:<name>` ⇒ unknown
    - (xiii) pytest 版本不在 `KNOWN_PYTEST_VERSIONS` ⇒ unknown
    - (viii) `override_ini` 不恰等於 `COMMITTED_ADDOPTS_OVERRIDES` ⇒ unknown(本次的收集定義被覆寫)
    - (ix) 有 `-c` / `--config-file` ⇒ unknown(即使指向已提交的權威檔)
    - (x) 實際採用的設定檔不是 `CONFIG_FILE` ⇒ unknown
    - (xi) `COMMITTED_FILES` 任一檔的工作樹 blob ≠ HEAD blob,或取不到 ⇒ unknown
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
    if any(p["kind"] not in SUPPORTED_PLUGIN_KINDS for p in comp["plugins"]):
        return "unknown"
    if comp["blocked"]:
        return "unknown"
    if comp["pytest_version"] not in KNOWN_PYTEST_VERSIONS:
        return "unknown"
    if comp["override_ini"] != list(COMMITTED_ADDOPTS_OVERRIDES):
        return "unknown"
    if comp["inifilename"] is not None:
        return "unknown"
    if comp["inipath"] != CONFIG_FILE:
        return "unknown"
    blobs = comp["config_blobs"]
    if not all(blobs[p]["worktree"] and blobs[p]["worktree"] == blobs[p]["head"]
               for p in COMMITTED_FILES):
        return "unknown"
    options = comp["options"]
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
