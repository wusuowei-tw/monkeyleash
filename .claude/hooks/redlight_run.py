# -*- coding: utf-8 -*-
"""紅燈包裝器(票 152 批二,規格 v3 E1～E3)—— Kotlin / Dart 紅燈紀錄唯一的產生端。

**為什麼是包裝器,不是「匯入報告」**:讀一份報告檔、在匯入時才算實作快照,
等於讓一份舊的紅燈報告替一支已經寫好的新程式補出「實作不存在」的紅燈(規格 E1)。
所以這裡**沒有任何匯入入口**:一次呼叫 = 一次由本模組親自啟動的執行,
快照在開跑前拍、票號在開跑前讀、只讀本次專用輸出目錄裡的輸出。

**能宣告的只有**:「包裝器的綁定與轉換邏輯以樣本驗證」(規格 §6 階段 2)。
真實工具鏈從未在本票執行過 —— 預設 runner 的指令、初始化腳本的 Gradle API 對應、
錯誤訊息的真實路徑格式,全部**待階段 3 實測**。

介面與兩種輸出格式的權威全文在 `tests/test_redlight_run.py` 的模組 docstring
(Dart 判定規則、Kotlin 暫定協定、沒有釘住的項目)。本檔照它實作,不另立一份。

**對應規則只有一份**:測試檔 ↔ 實作檔的配對、語言、測試檔分類一律問判定端
(`gate.r3_language` / `gate.is_test_path` / `gate.test_candidates`),
雜湊用 `redlight.content_hash`。判定端只有「實作 → 測試」這個方向;反向時本檔只
**產生候選**,由 `gate.test_candidates(候選) == [測試檔]` 決定哪一個成立 ——
「哪一段算角色段」之類的規則一個字都不在本檔。兩者若有分歧,結果是「找不到實作」而中止,
不是一筆對不上判定端的紀錄。

已知限制(規格 P3 殘餘風險,原樣):只比對開始與結束兩個時間點,
**中途改動、結束前改回原樣偵測不到**(R-a,`tests/test_redlight_run.py` 的 AC-B22b 釘住);
執行期間往本次輸出目錄塞入假結果偵測不到(R-b)。
"""

import argparse
import importlib.util
import io
import json
import os
import posixpath
import re
import secrets
import subprocess
import sys
from datetime import datetime, timezone

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(_HERE))
INIT_SCRIPT = os.path.join(_HERE, "redlight_gradle_init.gradle")


def _sibling(name):
    """載入同目錄的判定端模組。兩支在 module 層只定義常數與函式,不讀寫任何檔案。"""
    spec = importlib.util.spec_from_file_location(
        "_redlight_run_" + name, os.path.join(_HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_gate = _sibling("gate")
_redlight = _sibling("redlight")

DART = _gate.R3_DART
KOTLIN = _gate.R3_KOTLIN
COMPILE_ERROR = "<compile error>"      # 比照 redlight.COLLECTION_ERROR
DART_OUTPUT = "report.json"
KOTLIN_OUTPUT = "kotlin-result.json"
RUN_DIR_PROPERTY = "redlightRunDir"    # 初始化腳本讀的 Gradle 專案屬性(-P)

_DART_RESULTS = ("success", "failure", "error")
_KT_KINDS = ("main_compile", "test_compile", "test")
_KT_OUTCOMES = ("success", "failed", "up_to_date", "from_cache", "skipped", "no_source", "not_run")
_KT_MAIN_OK = ("success", "up_to_date", "from_cache")
_KT_TEST_RESULTS = ("success", "failure", "skipped")
_PATH_TAIL = re.compile(r"[A-Za-z0-9_.\-]")
_RUN_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")      # 用 fullmatch:`$` 會放過結尾的換行
_ABS_DRIVE = re.compile(r"[A-Za-z]:/")             # 絕對路徑開頭的 `X:/`(`\` 已先換成 `/`);冒號的唯一例外

REASON_CHANGED = u"執行前後實作狀態不同"
REASON_BAD_RUN_ID = u"run_id 格式不合法"
REASON_AMBIGUOUS_SUITE = u"suite 歸屬有歧義"
REASON_DRIVE_RELATIVE = u"磁碟相對路徑"
REASON_COLON_SEGMENT = u"含冒號的路徑段"


# ── 路徑 ─────────────────────────────────────────────────────────────────────

def _actual_case(root, rel):
    """把 `rel` 的每一段換成磁碟上的實際大小寫;找不到就原樣。"""
    cur, out = root, []
    for seg in rel.split("/"):
        name = seg
        try:
            if not os.path.exists(os.path.join(cur, seg)) or seg not in os.listdir(cur):
                hits = [n for n in os.listdir(cur) if n.lower() == seg.lower()]
                if len(hits) == 1:
                    name = hits[0]
        except OSError:
            pass
        out.append(name)
        cur = os.path.join(cur, name)
    return "/".join(out)


def _colon_segment(given):
    """第一個含冒號的路徑段;沒有回 None。**純字串,不碰檔案系統。**

    唯一例外是字串開頭的 ASCII `X:/`(絕對路徑的磁碟代號):先切掉,再看其餘的段。
    其餘任何一段只要含 `:` 就命中(S5h-2 J1,Jeff 選「A 一次封死」)——
    `ntpath` 把「第二個字元是冒號」就當磁碟代號,不限字母(`Q:x`、`1:x`、`Ｑ:x`、`_:`),
    `os.path.join(root, …)` 會換掉前綴;其他位置的冒號在 NTFS 是替代資料流(`a:b`、`x.dart:s`)。
    **正規化前的原始各段與 `posixpath.normpath` 之後的各段都檢查**:`pkg/a:b/../…` 正規化後
    冒號段已被 `..` 消掉,只看正規化後的結果會放過它。所有平台一律算(POSIX 上合法的含冒號
    檔名也拒絕,票 152 §6 J4)。
    """
    s = str(given).replace("\\", "/")
    if _ABS_DRIVE.match(s):
        s = s[3:]
    for seg in s.split("/") + posixpath.normpath(s).split("/"):
        if ":" in seg:
            return seg
    return None


def _repo_relative(root, given):
    """呼叫端給的路徑 → repo 根相對、`/` 分隔、無 `./` 的 posix 路徑;落在 root 外回 None(規格 E1 F3)。"""
    text = str(given).replace("\\", "/")
    if os.path.isabs(text) or re.match(r"^[A-Za-z]:/", text):
        try:
            text = os.path.relpath(text, root).replace("\\", "/")
        except ValueError:                     # 不同磁碟代號:轉不成 repo 根相對(S5f F3)
            return None
    rel = posixpath.normpath(text)
    if rel in (".", "") or rel == ".." or rel.startswith("../") or rel.startswith("/"):
        return None
    return _actual_case(root, rel)


def _impl_for(test_rel, lang):
    """測試檔 → 依 D1 對應的實作檔(repo 根相對 posix);判定端不認任何候選就回 None。

    這裡只**產生候選**(把測試側的段落換成實作側);哪一個成立完全由判定端決定,
    篩選條件與 `check()` 走到 R3 的條件同形:
      - `gate.r3_language(候選) == lang`(R3 只對這個語言的檔案問配對);
      - `gate.is_test_path(候選)` 為 False(測試路徑在 `check()` 就放行,R3 永遠不問它;S5f F5);
      - `gate.test_candidates(候選, lang) == [test_rel]`。
    檔名候選同時列出 `<stem><ext>` 與 `<stem>` 兩種寫法:判定端用 `os.path.splitext`
    取 base,隱藏檔(`.dart`、`.kt`)的 splitext 不去副檔名,所以兩種都可能被認可(S5f F4)。
    通過篩選的不只一支 ⇒ 回 None(中止)。
    """
    parts = test_rel.split("/")
    name = parts[-1]
    cands = []
    if lang == DART and name.endswith("_test.dart"):
        stem = name[:-len("_test.dart")]
        for i, seg in enumerate(parts[:-1]):
            if seg in ("test", "integration_test"):
                for leaf in (stem + ".dart", stem):
                    cands.append("/".join(parts[:i] + ["lib"] + parts[i + 1:-1] + [leaf]))
    elif lang == KOTLIN and name.endswith("Test.kt"):
        stem = name[:-len("Test.kt")]
        for i in range(len(parts) - 3):
            if parts[i:i + 3] == ["src", "test", "kotlin"]:
                for leaf in (stem + ".kt", stem):
                    cands.append("/".join(parts[:i] + ["src", "main", "kotlin"] + parts[i + 3:-1] + [leaf]))
    ok = {c for c in cands
          if c and _gate.r3_language(c) == lang
          and not _gate.is_test_path(c)
          and _gate.test_candidates(c, lang) == [test_rel]}
    return ok.pop() if len(ok) == 1 else None


def _kotlin_module(impl_rel):
    """Kotlin 實作 → 模組目錄(`app`;repo 根為 "")。錨點與 D1 同一個函式。"""
    parts = impl_rel.split("/")
    j = _gate._find_segments(parts, _gate._KOTLIN_MAIN)
    return "/".join(parts[:j])


def _kotlin_project_path(module):
    return ":" + module.replace("/", ":") if module else ":"


def _kotlin_class(test_rel, module):
    """測試檔 → 完整類別名(`x.FooTest`)。"""
    tail = test_rel[len(module) + 1:] if module else test_rel
    return tail[len("src/test/kotlin/"):-len(".kt")].replace("/", ".")


# ── 快照與票號 ───────────────────────────────────────────────────────────────

def _snapshot(root, impl_rel):
    """(存在與否, 行尾正規化雜湊);讀不動回 (True, None, 錯誤)。"""
    path = os.path.join(root, *impl_rel.split("/"))
    if not os.path.isfile(path):
        return (False, None, None)
    try:
        with io.open(path, "rb") as f:
            return (True, _redlight.content_hash(f.read()), None)
    except Exception as e:
        return (True, None, "%s: %s" % (type(e).__name__, e))


def _ticket(root):
    """開跑前的票號。站牌格式不合格回 None 並往 stderr 警告、照常開跑;B 組照舊 —— 不猜
    (同 `redlight.current_ticket`,走同一支 `redlight._ticket_from`)。"""
    try:
        path = os.path.join(root, ".dev", "pipeline.json")
    except Exception:
        path = None         # 開檔必失敗 ⇒ 依 A 組處理;讀取端不得丟例外
    return _redlight._ticket_from(path)


# ── Dart:〔D-json〕事件流 ───────────────────────────────────────────────────

def _dart_events(run_dir):
    path = os.path.join(run_dir, DART_OUTPUT)
    if not os.path.isfile(path):
        return None, u"本次輸出目錄裡沒有 %s(工具沒有寫出輸出)" % DART_OUTPUT
    events = []
    try:
        with io.open(path, encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                if not line.strip():
                    continue
                ev = json.loads(line)
                if not isinstance(ev, dict):
                    return None, u"%s 第 %d 行不是 JSON 物件" % (DART_OUTPUT, n)
                events.append(ev)
    except Exception as e:
        return None, u"%s 無法解析(%s: %s)—— 輸出壞掉或不完整,不寫紀錄" % (DART_OUTPUT, type(e).__name__, e)
    return events, None


def _dart_suite_matches(root, suite_path, test_rel):
    """`suite.path` 對不對得上這支測試檔。

    - 絕對路徑(含 `X:/`):本身就是完整身分(E3 的「補套件根前綴」只適用相對路徑)。
      轉成 repo 根相對後**只接受完全相等**(S5g G1);轉不了(不同磁碟代號,S5f F3)
      或落在 repo 外 ⇒ 對不上。不碰檔案系統。
    - 相對路徑:完整路徑相等,或相對於套件根的字尾(對齊 `/`)—— 已知限制 K12。
    """
    p = str(suite_path).replace("\\", "/")
    absolute = bool(os.path.isabs(p) or re.match(r"^[A-Za-z]:/", p))
    if absolute:
        try:
            p = os.path.relpath(p, root).replace("\\", "/")
        except ValueError:
            return False
        p = posixpath.normpath(p)
        if p == ".." or p.startswith("../"):
            return False
        return p == test_rel
    p = posixpath.normpath(p)
    return p == test_rel or test_rel.endswith("/" + p)


def _dart_parse(events):
    suites = {}
    tests = {}
    done = {}
    finished = False
    for ev in events:
        kind = ev.get("type")
        if kind == "suite":
            s = ev.get("suite") or {}
            suites[s.get("id")] = s.get("path")
        elif kind == "testStart":
            t = ev.get("test") or {}
            tests[t.get("id")] = t
        elif kind == "testDone":
            done[ev.get("testID")] = ev
        elif kind == "done":
            finished = True
    return suites, tests, done, finished


def _dart_verdicts(root, events, tests_rel):
    """回 {test_rel: (result, failed_tests, reason)}。

    歸屬(S5f F2):先算每個 suite 對得上哪些被指定的測試檔;一個 suite 對上兩支以上 ⇒
    那幾支都不寫(歧義)。只對上一支的 suite 才歸給那一支。字尾比對保留(E3:`suite.path`
    可以相對於套件根),所以「唯一」的意思是:在這一次被指定的測試檔裡,只有一支對得上。
    """
    suites, tests, done, finished = _dart_parse(events)
    owners = {sid: [t for t in tests_rel if _dart_suite_matches(root, p, t)]
              for sid, p in suites.items() if p is not None}
    out = {}
    for test_rel in tests_rel:
        ids = [sid for sid, who in owners.items() if test_rel in who]
        shared = [sid for sid in ids if len(owners[sid]) > 1]
        if shared:
            out[test_rel] = (None, None, u"%s:同一個 suite(%s)同時對得上 %s"
                             % (REASON_AMBIGUOUS_SUITE, suites[shared[0]], "、".join(owners[shared[0]])))
            continue
        out[test_rel] = _dart_verdict(ids, tests, done, finished)
    return out


def _dart_verdict(ids, tests, done, finished):
    """回 (result, failed_tests, reason);result 為 None 表示不寫。`ids`:歸給這支測試檔的 suite。"""
    if not ids:
        return None, None, u"指定的測試檔沒有出現在本次輸出中"
    if not finished:
        return None, None, u"本次輸出不完整(沒有 done 事件)—— 執行中斷或未完成"
    mine = [(tid, t) for tid, t in tests.items() if t.get("suiteID") in ids]
    failed, ran = [], 0
    for tid, t in mine:
        d = done.get(tid)
        if d is None:
            return None, None, u"測試「%s」開始了但沒有結束事件 —— 輸出不完整" % t.get("name")
        result, skipped, hidden = d.get("result"), d.get("skipped"), d.get("hidden")
        if result not in _DART_RESULTS or not isinstance(skipped, bool) or not isinstance(hidden, bool):
            return None, None, u"無法辨識的測試結果(result=%r, skipped=%r, hidden=%r)" % (result, skipped, hidden)
        if result in ("failure", "error"):
            failed.append(t.get("name"))
        elif not hidden and not skipped:
            ran += 1
    if failed:
        return "red", failed, None
    if ran == 0:
        return None, None, u"該測試檔沒有任何一個測試在本次真的跑完(全部被跳過或沒有測試)"
    return "green", [], None


# ── Kotlin:初始化腳本 → 包裝器的暫定協定 ───────────────────────────────────

def _kotlin_doc(run_dir):
    path = os.path.join(run_dir, KOTLIN_OUTPUT)
    if not os.path.isfile(path):
        return None, u"本次輸出目錄裡沒有 %s(工具沒有寫出輸出)" % KOTLIN_OUTPUT
    try:
        with io.open(path, encoding="utf-8") as f:
            doc = json.load(f)
    except Exception as e:
        return None, u"%s 無法解析(%s: %s)—— 輸出壞掉或不完整,不寫紀錄" % (KOTLIN_OUTPUT, type(e).__name__, e)
    if not isinstance(doc, dict):
        return None, u"%s 不是 JSON 物件" % KOTLIN_OUTPUT
    if doc.get("complete") is not True:
        return None, u"建置沒有完整結束(complete 不是 true)—— 執行中斷或未完成"
    tasks, tests, errors = doc.get("tasks"), doc.get("tests"), doc.get("compile_errors")
    if not isinstance(tasks, list) or not isinstance(tests, list) or not isinstance(errors, str):
        return None, u"%s 缺欄或型別不對(tasks / tests / compile_errors)" % KOTLIN_OUTPUT
    for t in tasks:
        if not isinstance(t, dict) or t.get("kind") not in _KT_KINDS or t.get("outcome") not in _KT_OUTCOMES \
                or not isinstance(t.get("project"), str):
            return None, u"無法辨識的任務狀態:%r" % (t,)
        if t["kind"] != "main_compile" and not isinstance(t.get("executed"), bool):
            return None, u"無法辨識的任務狀態(缺 executed):%r" % (t,)
    for r in tests:
        if not isinstance(r, dict) or r.get("result") not in _KT_TEST_RESULTS:
            return None, u"無法辨識的測試結果:%r" % (r,)
    return doc, None


def _kt_task(doc, project, kind):
    hits = [t for t in doc["tasks"] if t["project"] == project and t["kind"] == kind]
    return hits[0] if len(hits) == 1 else None


def _ran(task, outcome=None):
    """本次執行證據(R-RUN):executed 為 true 且 outcome 是 success / failed。"""
    return (task is not None and task.get("executed") is True
            and task.get("outcome") in ("success", "failed")
            and (outcome is None or task.get("outcome") == outcome))


def _path_in_errors(errors, test_rel):
    """`compile_errors` 是否在分隔點對齊處含這支測試檔的 repo 根相對路徑(協定)。"""
    s = errors.replace("\\", "/")
    start = 0
    while True:
        i = s.find(test_rel, start)
        if i < 0:
            return False
        j = i + len(test_rel)
        if (i == 0 or s[i - 1] == "/") and (j == len(s) or not _PATH_TAIL.match(s[j])):
            return True
        start = i + 1


def _kotlin_verdicts(doc, specs, before):
    """回 {test_rel: (result, failed_tests, reason)}。`specs`:[(test_rel, impl_rel, module)]。"""
    out = {}
    compile_mode = {}
    for test_rel, impl_rel, module in specs:
        project = _kotlin_project_path(module)
        tc = _kt_task(doc, project, "test_compile")
        compile_mode[test_rel] = _ran(tc, "failed")

    if any(compile_mode.values()):
        # E2 ①～④:**每一個**被指定的測試檔都要各自滿足,否則全部不寫。
        why = {}
        for test_rel, impl_rel, module in specs:
            project = _kotlin_project_path(module)
            main = _kt_task(doc, project, "main_compile")
            if not compile_mode[test_rel]:
                why[test_rel] = u"測試程式編譯不是「本次執行且失敗」"
            elif main is None or main.get("outcome") not in _KT_MAIN_OK:
                why[test_rel] = u"產品程式編譯沒有成功(main_compile=%r)" % (main and main.get("outcome"),)
            elif before[test_rel][0]:
                why[test_rel] = u"開跑前實作已存在 —— 編譯失敗只在實作不存在時算紅燈(E2 ①)"
            elif not _path_in_errors(doc["compile_errors"], test_rel):
                why[test_rel] = u"編譯錯誤輸出裡找不到這支測試檔的路徑,無法歸屬(E2 ③)"
        for test_rel, _impl, _module in specs:
            if not why:
                out[test_rel] = ("red", [COMPILE_ERROR], None)
            elif test_rel in why:
                out[test_rel] = (None, None, why[test_rel])
            else:
                out[test_rel] = (None, None, u"同次指定的其他測試檔無法歸屬編譯錯誤,全部不寫(E2 ④)")
        return out

    for test_rel, impl_rel, module in specs:
        project = _kotlin_project_path(module)
        tc = _kt_task(doc, project, "test_compile")
        task = _kt_task(doc, project, "test")
        if tc is None or tc.get("outcome") == "failed":
            out[test_rel] = (None, None, u"測試程式編譯沒有成功,也不符合編譯紅燈條件")
            continue
        if not _ran(task):
            out[test_rel] = (None, None, u"測試任務沒有本次執行證據(test=%r)" % (task and task.get("outcome"),))
            continue
        cls = _kotlin_class(test_rel, module)
        mine = [r for r in doc["tests"]
                 if r.get("project") == project and r.get("class") == cls]
        if not mine:
            out[test_rel] = (None, None, u"測試結果裡沒有對應這支測試檔的類別(類別名轉回的路徑對不上)")
            continue
        failed = ["%s#%s" % (r.get("class"), r.get("method")) for r in mine if r["result"] == "failure"]
        ran = [r for r in mine if r["result"] != "skipped"]
        if failed:
            out[test_rel] = ("red", failed, None)
        elif not ran:
            out[test_rel] = (None, None, u"該測試檔的測試全部被跳過")
        else:
            out[test_rel] = ("green", [], None)
    return out


# ── 啟動工具 ─────────────────────────────────────────────────────────────────

def _dart_argv(run_dir, tests):
    return (["dart", "test", "--file-reporter", "json:" + os.path.join(run_dir, DART_OUTPUT)]
            + list(tests))


def _kotlin_argv(root, run_dir, specs):
    wrapper = "gradlew.bat" if os.name == "nt" else "gradlew"
    exe = os.path.join(root, wrapper) if os.path.isfile(os.path.join(root, wrapper)) else "gradle"
    argv = [exe, "-I", INIT_SCRIPT, "-P%s=%s" % (RUN_DIR_PROPERTY, run_dir)]
    for test_rel, _impl, module in specs:
        project = _kotlin_project_path(module)
        argv += ["%s:test" % (project if project != ":" else ""), "--tests", _kotlin_class(test_rel, module)]
    return argv


def make_default_runner(root):
    """真實工具程序(CLI 用)的工廠:回一個 `runner(language, argv, run_dir)`。
    **本票從未執行過它**;指令待階段 3 實測。

    工作目錄**由 `root` 決定**,不由 `run_dir` 往上推(S5f F1:`run_dir` 一旦跳出
    `.dev/runs/`,往上推的工作目錄就會落到別的地方)。不用 shell。
    """
    cwd = os.path.abspath(str(root))

    def runner(language, argv, run_dir):
        return subprocess.run(list(argv), cwd=cwd, shell=False).returncode

    return runner


# ── 主流程 ───────────────────────────────────────────────────────────────────

def _abort(reason):
    return {"aborted": True, "reason": reason, "records": [], "reasons": {}}


def _new_run_id():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(4)


def run(root, tests, *, runner, run_id=None):
    """一次呼叫 = 一次由本模組啟動的真實執行。回 `{aborted, records, reasons[, reason]}`。"""
    root = os.path.abspath(str(root))
    # S5f F1:呼叫端給的 run_id 在任何副作用之前驗證。None 才自動產生;
    # 空字串、`.`、`..`、分隔符、磁碟代號、絕對路徑都過不了這一條。
    if run_id is not None and not (isinstance(run_id, str) and _RUN_ID.fullmatch(run_id)):
        return _abort(u"%s:%r(只允許 [A-Za-z0-9_-],1～64 字)" % (REASON_BAD_RUN_ID, run_id))
    # S5h H2:下面要走訪兩次(先掃描、再解析),只能讀一次的序列(iterator)會被第一次讀空。
    tests = list(tests) if tests is not None else []
    if not tests:
        return _abort(u"沒有指定測試檔(--test 至少一個;不接受「全部」)")
    # S5g G2 / S5h H1 / S5h-2 J1:除了開頭的 ASCII `X:/`,任何一段含冒號都拒絕
    # (磁碟相對段 `C:x`、`./Q:x`、`pkg/1:x`、替代資料流 `a:b`、被 `..` 消掉的 `pkg/a:b/..`)。
    # 正規化前、後的各段都看(`_colon_segment`,純字串),所有平台一律拒絕,而且放在
    # **任何檔案系統存取之前**:下面的 `_repo_relative()` 才會開始 `relpath` / `exists` / `listdir`。
    for given in tests:
        seg = _colon_segment(given)
        if seg is not None:
            return _abort(u"%s／%s:%r 含 %r(只有開頭的 `X:/` 可以帶冒號;其他段的冒號可能被當成"
                          u"磁碟代號或 NTFS 替代資料流,實際指到的位置不可靠)"
                          % (REASON_DRIVE_RELATIVE, REASON_COLON_SEGMENT, given, seg))

    rels = []
    for given in tests:
        rel = _repo_relative(root, given)
        if rel is None:
            return _abort(u"測試檔不在 repo 內:%r" % (given,))
        if rel not in rels:
            rels.append(rel)

    lang = None
    specs = []
    for rel in rels:
        this = _gate.r3_language(rel)
        if this not in (DART, KOTLIN) or not _gate.is_test_path(rel):
            return _abort(u"不是 Kotlin / Dart 測試檔(D3):%s" % rel)
        if lang is not None and this != lang:
            return _abort(u"一次只能跑一種語言的測試檔:%s" % rel)
        lang = this
        if not os.path.isfile(os.path.join(root, *rel.split("/"))):
            return _abort(u"測試檔不存在:%s" % rel)
        impl = _impl_for(rel, lang)
        if impl is None:
            return _abort(u"依配對規則(D1)找不到 %s 對應的實作檔位置" % rel)
        specs.append((rel, impl, _kotlin_module(impl) if lang == KOTLIN else None))

    ticket = _ticket(root)                                   # 開跑前讀,之後不再讀
    before = {rel: _snapshot(root, impl) for rel, impl, _m in specs}

    run_id = _new_run_id() if run_id is None else run_id
    runs = os.path.join(root, ".dev", "runs")
    run_dir = os.path.join(runs, run_id)
    # 第二道:最終落點必須正是 `.dev/runs` 的直接子目錄,名稱與 run_id 一字不差。
    # 只用路徑運算與 realpath;不為了核對而先建立任何目錄。
    real_runs, real_dir = os.path.realpath(runs), os.path.realpath(run_dir)
    if os.path.dirname(real_dir) != real_runs or os.path.basename(real_dir) != run_id:
        return _abort(u"%s:%r 解析後不在 %s 底下" % (REASON_BAD_RUN_ID, run_id, runs))
    if os.path.lexists(run_dir):
        return _abort(u"本次輸出目錄事先已存在:%s —— 不重用舊目錄" % run_dir)
    try:
        os.makedirs(runs, exist_ok=True)
        os.mkdir(run_dir)                                    # 已存在就失敗,不覆寫
    except OSError as e:
        return _abort(u"無法建立本次輸出目錄 %s(%s)" % (run_dir, e))

    tests_rel = [rel for rel, _i, _m in specs]
    argv = _dart_argv(run_dir, tests_rel) if lang == DART else _kotlin_argv(root, run_dir, specs)
    reasons = {}
    try:
        runner(lang, argv, run_dir)
    except Exception as e:
        for rel in tests_rel:
            reasons[rel] = u"工具程序異常結束(%s: %s)" % (type(e).__name__, e)
        return {"aborted": False, "records": [], "reasons": reasons, "run_id": run_id}

    after = {rel: _snapshot(root, impl) for rel, impl, _m in specs}

    if lang == DART:
        events, err = _dart_events(run_dir)
        verdicts = ({rel: (None, None, err) for rel in tests_rel} if err
                    else _dart_verdicts(root, events, tests_rel))
    else:
        doc, err = _kotlin_doc(run_dir)
        verdicts = ({rel: (None, None, err) for rel in tests_rel} if err
                    else _kotlin_verdicts(doc, specs, before))

    records = []
    for rel, impl, _m in specs:
        b, a = before[rel], after[rel]
        if b[2] or a[2]:
            reasons[rel] = u"讀不到實作檔:%s" % (b[2] or a[2])
            continue
        if b[:2] != a[:2]:
            reasons[rel] = REASON_CHANGED
            continue
        result, failed, why = verdicts[rel]
        if result is None:
            reasons[rel] = why
            continue
        records.append({
            "test_file": rel,
            "time": datetime.now(timezone.utc).isoformat(),
            "result": result,
            "failed_tests": list(failed),
            "impl_file": impl,
            "impl_exists": b[0],
            "impl_hash": b[1],
            "ticket_id": ticket,
        })

    if records:
        log = os.path.join(root, ".dev", "test-runs.jsonl")
        with io.open(log, "a", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return {"aborted": False, "records": records, "reasons": reasons, "run_id": run_id}


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="redlight_run.py",
        description=u"親自啟動 Kotlin / Dart 測試並寫紅燈紀錄(票 152 批二)。"
                    u"只讀本次專用輸出目錄;沒有任何把既有輸出檔轉成紀錄的入口。")
    parser.add_argument("--test", action="append", default=[], metavar="PATH",
                        help=u"要跑的測試檔(可重複;至少一個)")
    parser.add_argument("--root", default=ROOT, help=u"repo 根目錄(預設:本檔所在的 repo)")
    parser.add_argument("--run-id", default=None, help=u"本次輸出目錄名稱(預設自動產生)")
    args = parser.parse_args(argv)
    res = run(args.root, args.test, runner=make_default_runner(args.root), run_id=args.run_id)
    sys.stdout.write(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    if res["aborted"]:
        return 2
    return 0 if not res["reasons"] else 1


if __name__ == "__main__":
    sys.exit(main())
