# -*- coding: utf-8 -*-
"""票 152 批二(規格 v3 §7.2,AC-B20～B34;E1 F3 路徑格式)—— 包裝器 `redlight_run`。

被測模組:`.claude/hooks/redlight_run.py`(R3 對它的第一候選就是本檔)。
**全部用暫存 repo + 假工具程序 + 合成樣本**:本檔不執行 Gradle / Flutter / Dart / Kotlin,
假 runner 是 Python 可呼叫物件,不開任何子行程。不讀寫真實 `.dev/`。
(AC-B31 的判定端那一格用 `git` 建暫存 repo,沿用 `tests/test_gate.py` 批一的寫法 ——
那是判定端的前提,不是被測工具。)

## 介面(紅燈站定,實作站照做)

- `run(root, tests, *, runner, run_id=None) -> dict`
  - `tests`:呼叫端給的測試檔路徑清單,原樣傳入(可能含 `./` 或 `\\`,F3)。
  - `runner(language, argv, run_dir) -> int`:`language` 為 `"dart"` / `"kotlin"`;
    假 runner 在 `run_dir` 寫合成樣本並回退出碼。
  - 回傳至少含 `aborted`(bool)、`records`(本次寫出的紀錄 list)、
    `reasons`({測試檔 posix 路徑: 不寫紀錄的原因字串});中止時另含 `reason`。
- 輸出目錄 `<root>/.dev/runs/<run_id>/`,必須事先不存在;紀錄只追加到
  `<root>/.dev/test-runs.jsonl`,既有 8 欄(`redlight.py:127-140`);
  票號開跑前讀 `<root>/.dev/pipeline.json` 的 `ticket_id`,之後不再讀。
- `main(argv=None) -> int`:CLI(`--test <路徑>`,可重複)。**沒有**報告匯入選項(AC-B32)。
- Dart argv:含 `--file-reporter`、`json:<run_dir>/report.json` 兩個元素與被指定的測試檔,不含別的測試檔。
- Kotlin argv:含 `-I <初始化腳本>`;初始化腳本 = 包裝器同目錄的 `redlight_gradle_init.gradle`
  (repo 內上游檔案,`.claude/hooks/` 標 copy 隨框架出貨)。
- Kotlin 編譯失敗紅燈的 `failed_tests` 固定為 `["<compile error>"]`(比照 `<collection error>`)。
- `run_id`(票 152 S5f F1):只允許 `^[A-Za-z0-9_-]{1,64}$`;`None` 表示自動產生。
  空字串、`.`、`..`、任何分隔符、磁碟代號、絕對路徑 ⇒ **在任何副作用之前**中止
  (不建 `.dev/runs`、不呼叫 runner、不寫帳)。CLI `--run-id` 同一條規則,中止回 2。
  合法值的輸出目錄是 `<root>/.dev/runs/` 的**直接子目錄**。
  中止原因須含固定字串「run_id 格式不合法」(Jeff 2026-10-15 裁定 S3d-2 補強;S3d 初版沒有這一條)。
- 真實工具的工作目錄由 repo 根決定(F1):CLI 用工廠 `make_default_runner(root)` 取得
  `runner(language, argv, run_dir)`,它呼叫 `subprocess.run` 時 `cwd` = `root`,不由 `run_dir` 往上推。
- 測試檔路徑無法轉成 repo 根相對(例:與 root 不同磁碟代號)⇒ 中止,不丟例外(F3)。
- 磁碟相對路徑(S5g G2):呼叫端給的測試檔路徑把 `\\` 換成 `/` 之後,開頭符合 `^[A-Za-z]:`
  但不是 `^[A-Za-z]:/`(例:`C:x/…`、`Q:test/…`)⇒ **一律中止**,原因含固定字串「磁碟相對路徑」;
  拒絕發生在任何檔案系統存取之前。**所有平台都適用**(POSIX 上 `C:x` 雖是合法目錄名也一樣拒絕,
  讓 Windows 與 CI 行為一致 —— Station 3e 定的設計選擇)。
- 實作檔配對(F4 / F5):只採判定端認可(`gate.test_candidates(候選) == [測試檔]`)、
  而且本身不是測試路徑(`gate.is_test_path(候選)` 為 False)的候選;
  這樣的候選不只一支(包括檔名只剩副檔名、`splitext` 認得兩種寫法的情形)⇒ 中止。

## Dart 合成樣本(`run_dir/report.json`)

每行一個 〔D-json〕 事件。用到:`suite.path`(相對於套件根;本檔的暫存 repo 套件根 = repo 根)、
`testStart.test`(`id`、`name`、`suiteID`)、`testDone`(`testID`、`result` ∈
`success`/`failure`/`error`、`skipped`、`hidden`)、`done`(`success`)。
協定內其他事件型別(`start`、`allSuites`、`error`…)不影響判定。
- 紅:該 suite 任一測試(含 `hidden` 的載入虛擬測試)`failure` / `error`。
- 綠:有 `done`;該 suite 至少一個非隱藏測試沒被跳過;全部 `success`。
- 不寫:suite 不在輸出、沒有 `done`(中斷)、非隱藏測試全部 `skipped`、
  `result` 是協定外的值、檔案讀不到或解析不了。
- 歸屬(F2):一個 suite 同時對得上兩支以上被指定的測試檔 ⇒ 那幾支**都不寫**,
  原因含「suite 歸屬有歧義」;能用完整路徑唯一對上的照常各自判定。
  `suite.path` 無法轉成 repo 根相對(例:不同磁碟代號的絕對路徑)⇒ 該 suite 對不上任何測試檔,
  不丟例外(F3)。
- 絕對路徑只能精確配對(S5g G1):`suite.path` 是絕對路徑時,正規化成 repo 根相對 posix 路徑後
  **只接受與被指定測試檔完全相等**,不做字尾比對。相對路徑的字尾比對不變(已知限制 K12)。

## Kotlin 暫定協定(`run_dir/kotlin-result.json`)—— 初始化腳本 → 包裝器

**不是 Gradle 原生格式**,是批二初始化腳本(產出端)與包裝器(讀取端)之間的協定。
階段 3 以真實 Gradle 驗證;需要改協定時**先同步修改規格與本檔**,不得自行更換。

```
{
  "complete": bool,              # 建置結束時由初始化腳本寫 true;缺欄或 false = 中斷/不完整
  "tasks": [{
    "path": ":app:compileTestKotlin",
    "project": ":app",           # Gradle 專案路徑;":app" ⇔ 模組目錄 "app";":" ⇔ repo 根;":a:b" ⇔ "a/b"
    "kind": "main_compile" | "test_compile" | "test",
    "executed": bool,            # 本次是否真的執行了任務動作
    "outcome": "success" | "failed" | "up_to_date" | "from_cache" | "skipped" | "no_source" | "not_run"
  }],
  "compile_errors": str,         # 編譯錯誤輸出原文;只做「路徑字串對齊分隔點出現」的比對(見下)
  "tests": [{"project": ":app", "class": "x.FooTest", "method": "returnsOne",
             "result": "success" | "failure" | "skipped"}]
}
```
- 本次執行證據(R-RUN),**只套在 `test_compile` 與 `test`**:`executed: true` 且 `outcome` 是
  `success` / `failed`。`up_to_date` / `from_cache` / `skipped` / `no_source` / `not_run`、
  或 `executed: false` ⇒ 不是本次執行。
- `main_compile` 只問「產品程式編譯成功」,**不看 `executed`**:`outcome` ∈ {`success`,
  `up_to_date`, `from_cache`} 都算成功(規格 E2 ② 的「本次真的執行」只套在測試程式編譯;
  裁決助手記錄的解讀,規格 v4 會把字面寫清楚)。`failed` / `skipped` / `no_source` / `not_run`
  或協定外的值 ⇒ 不寫。
- `outcome` 不在上表、缺 `executed`(`test_compile` / `test`)⇒ 無法辨識 ⇒ 不寫(AC-B34)。
- 編譯紅燈(E2 ①～④):開跑前實作不存在;該專案 `main_compile` 編譯成功(上一條);
  `test_compile` 本次執行且 `failed`;`compile_errors` 含該測試檔路徑(下一條);
  **每一個**被指定的測試檔都各自滿足,否則全部不寫。
- `compile_errors` 含該測試檔路徑的判法:先把 `compile_errors` 裡的 `\\` 一律換成 `/`;
  測試檔的 repo 根相對路徑出現的位置,**前一個字元**必須是字串開頭或 `/`,
  **後一個字元**必須是字串結尾,或不是 `[A-Za-z0-9_.-]` 其中之一。
  (`otherapp/src/…/FooTest.kt` 不算 `app/src/…/FooTest.kt`;`FooTest.kts` 不算 `FooTest.kt`。)
- 測試結果:`<module>/src/test/kotlin/<套件路徑>/<類別名>.kt` 由 `project` + `class` 轉回;
  對不上被指定的測試檔 ⇒ 不寫(AC-B29)。`failed_tests` 用 `類別#方法`。

## 沒有釘住、留給實作站的(測試沒有斷言)

- `main_compile` 為 `skipped` / `no_source` / `not_run` 或協定外的值 ⇒ 不寫:沒有測試格
  (`failed` 由 AC-B28 `[main-compile-failed]` 釘住)。
- `compile_errors` 的反斜線形式與 `file:///` URI 形式只是**合成樣本**,真實 Gradle 輸出格式待階段 3。
- Kotlin 測試結果的 `failed_tests` 內容(`類別#方法`)、Dart / Kotlin 綠燈的 `failed_tests`(應為 `[]`):沒有斷言。
- `run_id` 自動產生的格式:沒有斷言。

## 紅燈原因

每個測試都經 `_load()` 載入模組:**只在確認模組檔不存在時**以固定一句失敗;
模組檔存在但載入失敗(語法錯、缺依賴、import 錯)讓原例外原樣拋出。
本站在模組不存在的狀態下跑,預期每個 nodeid 的失敗原因都是那一句。
"""

import hashlib
import importlib.util
import inspect
import io
import json
import pathlib
import re
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
_MODULE = ROOT / ".claude" / "hooks" / "redlight_run.py"
_INIT_SCRIPT = _MODULE.parent / "redlight_gradle_init.gradle"
_FIXTURES = ROOT / "tests" / "fixtures" / "redlight_run"

_TICKET = "152"
_FIELDS = {
    "test_file": (str,),
    "time": (str,),
    "result": (str,),
    "failed_tests": (list,),
    "impl_file": (str, type(None)),
    "impl_exists": (bool,),
    "impl_hash": (str, type(None)),
    "ticket_id": (str, type(None)),
}
_COMPILE_ERROR = "<compile error>"

_DART_TEST = "test/foo_test.dart"
_DART_IMPL = "lib/foo.dart"
_KT_TEST = "app/src/test/kotlin/x/FooTest.kt"
_KT_IMPL = "app/src/main/kotlin/x/Foo.kt"
_KT_TEST_2 = "app/src/test/kotlin/x/BarTest.kt"
_KT_IMPL_2 = "app/src/main/kotlin/x/Bar.kt"


def _load():
    """載入被測模組。**只有模組檔本身不存在時**才改寫成固定的紅燈原因。

    模組檔存在但載入失敗(語法錯、缺依賴、import 其他東西出錯)⇒ 原例外原樣拋出,
    不得被這一句蓋掉 —— 否則「實作壞了」會長得跟「實作還沒寫」一模一樣。
    """
    if not _MODULE.exists():
        pytest.fail("redlight_run 模組不存在（票 152 批二紅燈）")
    spec = importlib.util.spec_from_file_location("redlight_run_under_test", str(_MODULE))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── 暫存 repo 與合成樣本 ─────────────────────────────────────────────────────

def _write(root, rel_path, text, newline="\n"):
    p = pathlib.Path(str(root)).joinpath(*rel_path.split("/"))
    p.parent.mkdir(parents=True, exist_ok=True)
    with io.open(str(p), "w", encoding="utf-8", newline=newline) as f:
        f.write(text)
    return p


def _set_ticket(root, ticket):
    _write(root, ".dev/pipeline.json", json.dumps(
        {"current_stage": "implement", "feature": "t152", "ticket_id": ticket}))


def _repo(tmp_path, files=()):
    """暫存 repo:`.dev/pipeline.json` 屬本票;`files` 是 (路徑, 內容)。回 repo 根。"""
    root = tmp_path / "repo"
    root.mkdir()
    _set_ticket(root, _TICKET)
    for rel_path, text in files:
        _write(root, rel_path, text)
    return root


def _ledger(root):
    p = pathlib.Path(str(root)) / ".dev" / "test-runs.jsonl"
    if not p.exists():
        return []
    with io.open(str(p), encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _fixture(name):
    with io.open(str(_FIXTURES / name), encoding="utf-8") as f:
        return f.read()


def _kotlin(name, root):
    """Kotlin 合成樣本(dict);`{ROOT}` 換成暫存 repo 根(posix)。"""
    return json.loads(_fixture(name).replace("{ROOT}", pathlib.Path(str(root)).as_posix()))


def _norm_hash(raw):
    return hashlib.sha256(raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")).hexdigest()


class _Runner(object):
    """假工具程序。不開子行程:在 `run_dir` 寫合成樣本、可在「執行中」做事,回退出碼。"""

    def __init__(self, sample=None, filename=None, during=None, rc=1):
        self.sample = sample          # str(原文寫入)或 dict(json.dumps)或 None(不寫)
        self.filename = filename
        self.during = during
        self.rc = rc
        self.calls = []

    def __call__(self, language, argv, run_dir):
        self.calls.append((language, list(argv), str(run_dir)))
        if self.during is not None:
            self.during()
        if self.sample is not None:
            text = self.sample if isinstance(self.sample, str) else json.dumps(self.sample)
            with io.open(str(pathlib.Path(str(run_dir)) / self.filename), "w",
                         encoding="utf-8", newline="\n") as f:
                f.write(text)
        return self.rc


def _dart_runner(sample, **kw):
    return _Runner(sample, "report.json", **kw)


def _kotlin_runner(sample, **kw):
    return _Runner(sample, "kotlin-result.json", **kw)


def _dart_repo(tmp_path, impl=None):
    files = [(_DART_TEST, u"void main() {}\n")]
    if impl is not None:
        files.append((_DART_IMPL, impl))
    return _repo(tmp_path, files)


def _kotlin_repo(tmp_path, impl=None, second=False):
    files = [(_KT_TEST, u"class FooTest\n")]
    if second:
        files.append((_KT_TEST_2, u"class BarTest\n"))
    if impl is not None:
        files.append((_KT_IMPL, impl))
    return _repo(tmp_path, files)


def _no_record(res, root, test_file):
    assert res["records"] == [], res
    assert _ledger(root) == [], u"帳本被寫入了:%r" % _ledger(root)
    assert test_file in res["reasons"], res
    assert isinstance(res["reasons"][test_file], str) and res["reasons"][test_file], res


# ── AC-B20 / AC-B21:開跑前的中止 ───────────────────────────────────────────

@pytest.mark.parametrize("tests", [[], [_DART_IMPL], [_KT_IMPL]],
                         ids=["no-test", "dart-impl", "kotlin-impl"])
def test_ac_b20_no_test_or_a_non_test_file_aborts(tmp_path, tests):
    """AC-B20|必須先紅|現行:模組不存在 ⇒ 失敗。
    要求:不給測試檔、或給的不是 D3 判定的測試檔 ⇒ `aborted` 為 True、有 `reason`、
    帳本沒有新增、假 runner 沒有被呼叫。"""
    mod = _load()
    root = _repo(tmp_path, [(_DART_IMPL, u"int foo() => 1;\n"), (_KT_IMPL, u"class Foo\n")])
    runner = _dart_runner(_fixture("dart_failure.jsonl"))
    res = mod.run(str(root), list(tests), runner=runner)
    assert res["aborted"] is True, res
    assert res.get("reason"), res
    assert runner.calls == [], runner.calls
    assert _ledger(root) == []


def test_ac_b21_existing_run_dir_aborts_without_running(tmp_path):
    """AC-B21|必須先紅|現行:模組不存在 ⇒ 失敗。
    要求:指定 `run_id` 的 `.dev/runs/<id>/` 事先存在 ⇒ 中止;帳本沒有新增;
    假 runner 沒有被呼叫;既有目錄內容不被動到。"""
    mod = _load()
    root = _dart_repo(tmp_path)
    stale = _write(root, ".dev/runs/r-reused/report.json", _fixture("dart_failure.jsonl"))
    before = stale.read_bytes()
    runner = _dart_runner(_fixture("dart_failure.jsonl"))
    res = mod.run(str(root), [_DART_TEST], runner=runner, run_id="r-reused")
    assert res["aborted"] is True, res
    assert res.get("reason"), res
    assert runner.calls == []
    assert _ledger(root) == []
    assert sorted(p.name for p in stale.parent.iterdir()) == ["report.json"]
    assert stale.read_bytes() == before


# ── AC-B22 / AC-B22b / AC-B23:開跑前快照與票號 ──────────────────────────────

@pytest.mark.parametrize("impl_before", [u"int foo() => 1;\n", None],
                         ids=["modified", "created"])
def test_ac_b22_impl_changed_during_run_is_not_recorded(tmp_path, impl_before):
    """AC-B22|必須先紅|現行:模組不存在 ⇒ 失敗。
    要求:假 runner 執行中把實作改成不同內容(或從無到有),結束時沒有改回 ⇒
    該測試檔不寫紀錄,`reasons` 含「執行前後實作狀態不同」。"""
    mod = _load()
    root = _dart_repo(tmp_path, impl=impl_before)
    runner = _dart_runner(_fixture("dart_failure.jsonl"),
                          during=lambda: _write(root, _DART_IMPL, u"int foo() => 2;\n"))
    res = mod.run(str(root), [_DART_TEST], runner=runner)
    _no_record(res, root, _DART_TEST)
    assert u"執行前後實作狀態不同" in res["reasons"][_DART_TEST], res


def test_ac_b22b_change_then_restore_during_run_is_not_detected(tmp_path):
    """AC-B22b|釘住已知限制(R-a)|現行:模組不存在 ⇒ 失敗(本站照實記錄,不要求先紅)。
    斷言文件與行為一致:只比對開始與結束兩個時間點 —— 中途改動、結束前改回原樣,
    兩次指紋相同,**偵測不到**,依現行設計會寫紀錄。這不是要求擋下。"""
    mod = _load()
    original = u"int foo() => 1;\n"
    root = _dart_repo(tmp_path, impl=original)

    def change_then_restore():
        _write(root, _DART_IMPL, u"int foo() => 2;\n")
        _write(root, _DART_IMPL, original)

    runner = _dart_runner(_fixture("dart_failure.jsonl"), during=change_then_restore)
    res = mod.run(str(root), [_DART_TEST], runner=runner)
    assert len(res["records"]) == 1, res
    assert res["records"][0]["test_file"] == _DART_TEST
    assert res["records"][0]["result"] == "red"


def test_ac_b23_ticket_is_read_before_the_run(tmp_path):
    """AC-B23|必須先紅|現行:模組不存在 ⇒ 失敗。
    要求:假 runner 執行中把 `pipeline.json` 的 `ticket_id` 換成別張票 ⇒
    紀錄的 `ticket_id` 是開跑前的票。"""
    mod = _load()
    root = _dart_repo(tmp_path)
    runner = _dart_runner(_fixture("dart_failure.jsonl"),
                          during=lambda: _set_ticket(root, "999"))
    res = mod.run(str(root), [_DART_TEST], runner=runner)
    assert len(res["records"]) == 1, res
    assert res["records"][0]["ticket_id"] == _TICKET
    assert _ledger(root)[0]["ticket_id"] == _TICKET


# ── AC-B24～AC-B26:Dart 轉換 ──────────────────────────────────────────────

def test_ac_b24_designated_test_missing_from_output_is_not_recorded(tmp_path):
    """AC-B24|必須先紅|現行:模組不存在 ⇒ 失敗。
    要求:Dart 樣本裡沒有指定測試檔的 suite(只有 `test/bar_test.dart`)⇒ 不寫紀錄。"""
    mod = _load()
    root = _dart_repo(tmp_path)
    res = mod.run(str(root), [_DART_TEST],
                  runner=_dart_runner(_fixture("dart_other_suite.jsonl")))
    _no_record(res, root, _DART_TEST)


def test_ac_b25_dart_failure_is_red_and_impl_absent_before_and_after(tmp_path):
    """AC-B25 ①|必須先紅|現行:模組不存在 ⇒ 失敗。
    要求:一個測試 `failure` ⇒ 寫紅燈;`impl_file` 依 D1 反推為 `lib/foo.dart`;
    開跑前與結束時實作都不存在 ⇒ `impl_exists` false、`impl_hash` None;
    `failed_tests` 含該測試名稱;票號為本票。"""
    mod = _load()
    root = _dart_repo(tmp_path)
    res = mod.run(str(root), [_DART_TEST],
                  runner=_dart_runner(_fixture("dart_failure.jsonl")))
    assert len(res["records"]) == 1, res
    rec = res["records"][0]
    assert rec["test_file"] == _DART_TEST
    assert rec["result"] == "red"
    assert rec["impl_file"] == _DART_IMPL
    assert rec["impl_exists"] is False
    assert rec["impl_hash"] is None
    assert rec["ticket_id"] == _TICKET
    assert "foo returns 1" in rec["failed_tests"], rec
    assert _ledger(root) == res["records"]


def test_ac_b25_dart_failure_hashes_the_unchanged_impl_before_the_run(tmp_path):
    """AC-B25 ②|必須先紅|現行:模組不存在 ⇒ 失敗。
    要求:開跑前實作存在、執行中沒有改 ⇒ `impl_exists` true、`impl_hash` 等於
    開跑前內容的雜湊(行尾正規化:實作以 CRLF 寫入,雜湊以 LF 計)。"""
    mod = _load()
    root = _dart_repo(tmp_path)
    impl = _write(root, _DART_IMPL, u"int foo() => 0;\n", newline="\r\n")
    raw = impl.read_bytes()
    assert b"\r\n" in raw   # 前提:這一格真的有 CRLF
    res = mod.run(str(root), [_DART_TEST],
                  runner=_dart_runner(_fixture("dart_failure.jsonl")))
    assert len(res["records"]) == 1, res
    rec = res["records"][0]
    assert rec["result"] == "red"
    assert rec["impl_file"] == _DART_IMPL
    assert rec["impl_exists"] is True
    assert rec["impl_hash"] == _norm_hash(raw)


def test_ac_b26_dart_hidden_load_test_error_is_red(tmp_path):
    """AC-B26|必須先紅|現行:模組不存在 ⇒ 失敗。
    要求:該測試檔的載入虛擬測試(`hidden`)`error` ⇒ 寫紅燈,`impl_exists` false。
    樣本是合成的;真實載入失敗的長相待階段 3(規格 AC-B26 / AC-B43)。"""
    mod = _load()
    root = _dart_repo(tmp_path)
    res = mod.run(str(root), [_DART_TEST],
                  runner=_dart_runner(_fixture("dart_load_error.jsonl")))
    assert len(res["records"]) == 1, res
    rec = res["records"][0]
    assert rec["test_file"] == _DART_TEST
    assert rec["result"] == "red"
    assert rec["impl_file"] == _DART_IMPL
    assert rec["impl_exists"] is False


# ── AC-B27～AC-B29:Kotlin 轉換 ────────────────────────────────────────────

def test_ac_b27_kotlin_test_compile_failure_is_red(tmp_path):
    """AC-B27|必須先紅|現行:模組不存在 ⇒ 失敗。
    要求:測試編譯本次執行且失敗、產品編譯本次執行且成功、`compile_errors` 含該測試檔路徑、
    開跑前實作不存在 ⇒ 寫紅燈;`impl_exists` false;`failed_tests` 為 `["<compile error>"]`。"""
    mod = _load()
    root = _kotlin_repo(tmp_path)
    res = mod.run(str(root), [_KT_TEST],
                  runner=_kotlin_runner(_kotlin("kotlin_compile_red.json", root)))
    assert len(res["records"]) == 1, res
    rec = res["records"][0]
    assert rec["test_file"] == _KT_TEST
    assert rec["result"] == "red"
    assert rec["impl_file"] == _KT_IMPL
    assert rec["impl_exists"] is False
    assert rec["impl_hash"] is None
    assert rec["failed_tests"] == [_COMPILE_ERROR]
    assert rec["ticket_id"] == _TICKET


def _assert_one_compile_red(res, root):
    """AC-B27 的斷言(同上一格):一筆紅燈、`<compile error>`、實作當時不存在、本票。"""
    assert len(res["records"]) == 1, res
    rec = res["records"][0]
    assert rec["test_file"] == _KT_TEST
    assert rec["result"] == "red"
    assert rec["impl_file"] == _KT_IMPL
    assert rec["impl_exists"] is False
    assert rec["impl_hash"] is None
    assert rec["failed_tests"] == [_COMPILE_ERROR]
    assert rec["ticket_id"] == _TICKET
    assert _ledger(root) == res["records"]


@pytest.mark.parametrize("outcome", ["up_to_date", "from_cache"],
                         ids=["main-up-to-date", "main-from-cache"])
def test_ac_b27_kotlin_compile_red_with_cached_main_compile(tmp_path, outcome):
    """AC-B27(產品編譯沿用快取)|必須先紅|現行:模組不存在 ⇒ 失敗。
    要求:以 `kotlin_compile_red.json` 為底,只把 `main_compile` 改成 `executed: false`、
    `outcome` 為 `up_to_date` / `from_cache` ⇒ 仍算「產品程式編譯成功」(R-RUN 的「本次真的執行」
    只套在測試程式編譯,規格 E2 ②;裁決助手記錄的解讀)。其餘同 AC-B27 ⇒ 寫一筆紅燈。"""
    mod = _load()
    root = _kotlin_repo(tmp_path)
    sample = _kotlin("kotlin_compile_red.json", root)
    _kt_task(sample, "main_compile").update(executed=False, outcome=outcome)
    res = mod.run(str(root), [_KT_TEST], runner=_kotlin_runner(sample))
    _assert_one_compile_red(res, root)


def _errors_file_uri(root):
    return ("e: file:///%s/app/src/test/kotlin/x/FooTest.kt:3:5 Unresolved reference: Foo\n"
            % pathlib.Path(str(root)).as_posix())


def _errors_backslash(root):
    return ("e: %s\\app\\src\\test\\kotlin\\x\\FooTest.kt:3:5 Unresolved reference: Foo\n"
            % str(root).replace("/", "\\"))


@pytest.mark.parametrize("make_errors", [_errors_file_uri, _errors_backslash],
                         ids=["file-uri", "backslash"])
def test_ac_b27_kotlin_compile_error_path_forms(tmp_path, make_errors):
    """AC-B27(錯誤訊息的路徑形式)|必須先紅|現行:模組不存在 ⇒ 失敗。
    要求:`compile_errors` 只含一種形式 ——
    `[file-uri]`:`e: file:///<tmp 絕對路徑,正斜線>/app/src/test/kotlin/x/FooTest.kt:3:5 …`;
    `[backslash]`:`e: <tmp 絕對路徑>\\app\\src\\test\\kotlin\\x\\FooTest.kt:3:5 …`(全部反斜線)
    ⇒ `\\` 換成 `/` 後路徑對齊分隔點出現 ⇒ 寫一筆紅燈(斷言同 AC-B27)。
    兩種長相都是**合成樣本**,真實 Gradle 輸出格式待階段 3 實測。"""
    mod = _load()
    root = _kotlin_repo(tmp_path)
    sample = _kotlin("kotlin_compile_red.json", root)
    sample["compile_errors"] = make_errors(root)
    res = mod.run(str(root), [_KT_TEST], runner=_kotlin_runner(sample))
    _assert_one_compile_red(res, root)


def _b28_path_absent(sample, root):
    sample["compile_errors"] = (
        "e: file:///%s/app/src/test/kotlin/x/OtherTest.kt:5:16 Unresolved reference 'Other'.\n"
        % pathlib.Path(str(root)).as_posix())
    return [_KT_TEST], _KT_TEST, False


def _b28_main_failed(sample, root):
    for t in sample["tasks"]:
        if t["kind"] == "main_compile":
            t["outcome"] = "failed"
    return [_KT_TEST], _KT_TEST, False


def _b28_two_tests_one_attributable(sample, root):
    # 錯誤輸出只指向 FooTest;BarTest 無法歸屬 ⇒ E2 ④ 不成立
    return [_KT_TEST, _KT_TEST_2], _KT_TEST_2, True


def _b28_other_module_prefix(sample, root):
    # 只有 `otherapp/…/FooTest.kt`:`app/…` 只以子字串出現,前一個字元是 `r` 不是 `/`
    sample["compile_errors"] = (
        "e: file:///%s/otherapp/src/test/kotlin/x/FooTest.kt:3:5 Unresolved reference: Foo\n"
        % pathlib.Path(str(root)).as_posix())
    return [_KT_TEST], _KT_TEST, False


def _b28_longer_file_name(sample, root):
    # 只有 `FooTest.kts`:`FooTest.kt` 後一個字元是 `s`(屬於 `[A-Za-z0-9_.-]`)
    sample["compile_errors"] = (
        "e: file:///%s/app/src/test/kotlin/x/FooTest.kts:3:5 Unresolved reference: Foo\n"
        % pathlib.Path(str(root)).as_posix())
    return [_KT_TEST], _KT_TEST, False


@pytest.mark.parametrize("variant", [_b28_path_absent, _b28_main_failed,
                                     _b28_two_tests_one_attributable,
                                     _b28_other_module_prefix, _b28_longer_file_name],
                         ids=["path-not-in-errors", "main-compile-failed",
                              "two-tests-one-attributable",
                              "other-module-prefix", "longer-file-name"])
def test_ac_b28_kotlin_compile_failure_not_attributable_is_not_recorded(tmp_path, variant):
    """AC-B28|必須先紅|現行:模組不存在 ⇒ 失敗。
    要求(五格,合成樣本為 `kotlin_compile_red.json` 的變形):
    ① 錯誤輸出不含該測試檔路徑;② 產品編譯也失敗;③ 指定兩個測試檔、錯誤只能歸屬其中一個
    ⇒ 無法歸屬的那個不寫。依規格 E2 ④(每個被指定的測試檔都要各自滿足),③ 兩個都不寫。
    ④ `[other-module-prefix]`:錯誤只含 `…/otherapp/src/test/kotlin/x/FooTest.kt`;
    ⑤ `[longer-file-name]`:錯誤只含 `…/app/src/test/kotlin/x/FooTest.kts`
    ⇒ 路徑沒有對齊分隔點出現 ⇒ 不寫。④⑤ 的錯誤訊息**只含**那一種形式、不含正確路徑;
    長相是合成樣本,真實格式待階段 3 實測。"""
    mod = _load()
    sample = _kotlin("kotlin_compile_red.json", tmp_path / "repo")   # `_kotlin_repo` 的根
    tests, unattributable, second = variant(sample, tmp_path / "repo")
    root = _kotlin_repo(tmp_path, second=second)
    res = mod.run(str(root), tests, runner=_kotlin_runner(sample))
    _no_record(res, root, unattributable)


def test_ac_b29_kotlin_class_name_not_matching_the_test_file_is_not_recorded(tmp_path):
    """AC-B29|必須先紅|現行:模組不存在 ⇒ 失敗。
    要求:結果以類別名 `y.FooTest` 表示,轉回 `app/src/test/kotlin/y/FooTest.kt`,
    與指定的 `app/src/test/kotlin/x/FooTest.kt` 對不上 ⇒ 不寫紀錄。"""
    mod = _load()
    root = _kotlin_repo(tmp_path)
    res = mod.run(str(root), [_KT_TEST],
                  runner=_kotlin_runner(_kotlin("kotlin_class_mismatch.json", root)))
    _no_record(res, root, _KT_TEST)


# ── AC-B30:樣本壞掉或讀不到 ───────────────────────────────────────────────

def _truncated_dart():
    lines = _fixture("dart_failure.jsonl").splitlines()
    last = lines[-1]
    return "\n".join(lines[:-1]) + "\n" + last[:len(last) // 2]


_B30 = [
    ("dart-not-json", "dart", lambda: "this is not json\n"),
    ("dart-truncated", "dart", _truncated_dart),
    ("dart-missing", "dart", lambda: None),
    ("kotlin-not-json", "kotlin", lambda: '{"complete": true, "tasks": ['),
    ("kotlin-missing", "kotlin", lambda: None),
]


@pytest.mark.parametrize("lang,make", [(b[1], b[2]) for b in _B30], ids=[b[0] for b in _B30])
def test_ac_b30_broken_or_missing_sample_is_not_recorded(tmp_path, lang, make):
    """AC-B30|必須先紅|現行:模組不存在 ⇒ 失敗。
    要求:樣本壞掉(非 JSON、截斷)或讀不到(runner 沒寫檔)⇒ 不寫紀錄,
    `reasons` 有錯誤原因;**不得寫成綠**(帳本一筆都沒有)。"""
    mod = _load()
    if lang == "dart":
        root, test = _dart_repo(tmp_path), _DART_TEST
        runner = _dart_runner(make())
    else:
        root, test = _kotlin_repo(tmp_path), _KT_TEST
        runner = _kotlin_runner(make())
    res = mod.run(str(root), [test], runner=runner)
    _no_record(res, root, test)


# ── AC-B31:8 欄、判定端能直接讀 ───────────────────────────────────────────

def _isolated_git(tmp_path, monkeypatch):
    """git 設定與使用者層隔離(同 `tests/test_gate.py` 的 `_t148_env`)。"""
    home = tmp_path / "home"
    home.mkdir()
    empty = tmp_path / "empty-gitconfig"
    empty.write_bytes(b"")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))


def _git(root, *args):
    return subprocess.run(["git"] + list(args), cwd=str(root), capture_output=True, check=True)


def _load_gate():
    spec = importlib.util.spec_from_file_location(
        "gate_for_redlight_run", str(ROOT / ".claude" / "hooks" / "gate.py"))
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    return gate


def test_ac_b31_records_are_the_eight_fields_and_the_judge_reads_them(tmp_path, monkeypatch):
    """AC-B31|必須先紅|現行:模組不存在 ⇒ 失敗。
    要求:寫出的每一筆都正好是既有 8 欄(`redlight.py:127-140`),欄名、型別相同;
    帳本內容 = 回傳的 `records`;批一判定端 `gate.redlight_missing()` 對 `lib/foo.dart`
    (Dart、本票、`impl_rel` 相等)直接讀到這筆合格紅燈(回 None)。
    暫存 repo 寫法沿用 `tests/test_gate.py` 批一(`_t152_repo`:git init + 一次提交、
    `ROOT` / `RUN_LOG` 指進暫存 repo)。"""
    mod = _load()
    _isolated_git(tmp_path, monkeypatch)
    root = _dart_repo(tmp_path)
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@example.invalid")
    _git(root, "config", "user.name", "t")
    _write(root, "README.md", u"t152 batch 2\n")
    _git(root, "add", "README.md")
    _git(root, "commit", "-q", "-m", "base (t152 batch 2)")

    res = mod.run(str(root), [_DART_TEST],
                  runner=_dart_runner(_fixture("dart_failure.jsonl")))
    assert res["records"], res
    for rec in res["records"]:
        assert set(rec) == set(_FIELDS), sorted(rec)
        for key, types in _FIELDS.items():
            assert isinstance(rec[key], types), (key, rec[key])
        assert all(isinstance(t, str) for t in rec["failed_tests"]), rec
        assert rec["result"] in ("red", "green")
    assert _ledger(root) == res["records"]

    gate = _load_gate()
    monkeypatch.setattr(gate, "ROOT", str(root))
    monkeypatch.setattr(gate, "RUN_LOG", str(root / ".dev" / "test-runs.jsonl"))
    monkeypatch.chdir(str(root))
    cands = gate.test_candidates(_DART_IMPL, gate.R3_DART)
    assert cands == [_DART_TEST]
    why = gate.redlight_missing("foo", cands, impl_rel=_DART_IMPL,
                                ticket=_TICKET, lang=gate.R3_DART)
    assert why is None, why


# ── AC-B32:沒有報告匯入入口 ───────────────────────────────────────────────

_IMPORT_WORDS = ("report", "import", "ingest")


def test_ac_b32_cli_help_has_no_report_import_option(capsys):
    """AC-B32 ①|必須先紅|現行:模組不存在 ⇒ 失敗。
    要求:`main(["--help"])` 正常結束(SystemExit 0),說明含 `--test`;
    所有 `--選項` 都不含 report / import / ingest。"""
    mod = _load()
    with pytest.raises(SystemExit) as exc:
        mod.main(["--help"])
    assert exc.value.code in (0, None)
    out = capsys.readouterr().out
    assert "--test" in out, out
    opts = re.findall(r"--[A-Za-z][\w-]*", out)
    bad = [o for o in opts if any(w in o.lower() for w in _IMPORT_WORDS)]
    assert not bad, bad


def test_ac_b32_no_public_function_accepts_a_report(tmp_path):
    """AC-B32 ②|必須先紅|現行:模組不存在 ⇒ 失敗。
    要求:模組有 `run`;模組自己定義的公開函式(名稱不以 `_` 開頭)沒有一支的名稱含
    report / import / ingest,也沒有一支的參數名稱含 report。"""
    mod = _load()
    assert callable(getattr(mod, "run", None))
    bad = []
    for name, obj in sorted(vars(mod).items()):
        if name.startswith("_") or not inspect.isfunction(obj):
            continue
        if obj.__module__ != mod.__name__:
            continue
        if any(w in name.lower() for w in _IMPORT_WORDS):
            bad.append(name)
        for p in inspect.signature(obj).parameters:
            if "report" in p.lower():
                bad.append("%s(%s)" % (name, p))
    assert not bad, bad


# ── AC-B33 / AC-B34:沒有本次執行證據、無法辨識 ─────────────────────────────

def _kt_task(sample, kind):
    return next(t for t in sample["tasks"] if t["kind"] == kind)


def _kt_up_to_date(root):
    s = _kotlin("kotlin_test_red.json", root)
    _kt_task(s, "test").update(executed=False, outcome="up_to_date")
    return s


def _kt_from_cache(root):
    s = _kotlin("kotlin_test_red.json", root)
    _kt_task(s, "test").update(executed=False, outcome="from_cache")
    return s


def _kt_task_skipped(root):
    s = _kotlin("kotlin_test_red.json", root)
    _kt_task(s, "test").update(executed=False, outcome="skipped")
    return s


def _kt_incomplete(root):
    s = _kotlin("kotlin_test_red.json", root)
    s["complete"] = False
    return s


def _kt_all_tests_skipped(root):
    s = _kotlin("kotlin_green.json", root)
    for t in s["tests"]:
        t["result"] = "skipped"
    return s


def _dart_no_done(root):
    return "\n".join(l for l in _fixture("dart_failure.jsonl").splitlines()
                     if '"type":"done"' not in l) + "\n"


_B33 = [
    ("kotlin-up-to-date", "kotlin", _kt_up_to_date),
    ("kotlin-from-cache", "kotlin", _kt_from_cache),
    ("kotlin-task-skipped", "kotlin", _kt_task_skipped),
    ("kotlin-incomplete", "kotlin", _kt_incomplete),
    ("kotlin-all-tests-skipped", "kotlin", _kt_all_tests_skipped),
    ("dart-all-tests-skipped", "dart", lambda root: _fixture("dart_all_skipped.jsonl")),
    ("dart-interrupted-no-done", "dart", _dart_no_done),
]


@pytest.mark.parametrize("lang,make", [(b[1], b[2]) for b in _B33], ids=[b[0] for b in _B33])
def test_ac_b33_no_evidence_of_this_run_writes_neither_red_nor_green(tmp_path, lang, make):
    """AC-B33|必須先紅|現行:模組不存在 ⇒ 失敗。
    要求(R-RUN):沿用快取、判定不需重跑、被跳過、執行中斷或輸出不完整、
    該測試檔全部測試被跳過 ⇒ **不寫合格紅燈,也不寫綠燈**。
    Kotlin 的快取／跳過／中斷三類以 `kotlin_test_red.json` 變形 —— 樣本仍帶著
    看似紅燈的測試結果,只認結果不認任務狀態的實作會寫出紅燈。"""
    mod = _load()
    if lang == "dart":
        root, test = _dart_repo(tmp_path), _DART_TEST
        runner = _dart_runner(make(root))
    else:
        root, test = _kotlin_repo(tmp_path), _KT_TEST
        runner = _kotlin_runner(make(root))
    res = mod.run(str(root), [test], runner=runner)
    _no_record(res, root, test)


def _kt_unknown_outcome(root):
    s = _kotlin("kotlin_test_red.json", root)
    _kt_task(s, "test")["outcome"] = "partially_executed"
    return s


def _kt_missing_executed(root):
    s = _kotlin("kotlin_test_red.json", root)
    del _kt_task(s, "test")["executed"]
    return s


_B34 = [
    ("kotlin-unknown-outcome", "kotlin", _kt_unknown_outcome),
    ("kotlin-missing-executed", "kotlin", _kt_missing_executed),
    ("dart-unknown-result", "dart", lambda root: _fixture("dart_unknown_result.jsonl")),
]


@pytest.mark.parametrize("lang,make", [(b[1], b[2]) for b in _B34], ids=[b[0] for b in _B34])
def test_ac_b34_unrecognisable_state_is_not_recorded(tmp_path, lang, make):
    """AC-B34|必須先紅|現行:模組不存在 ⇒ 失敗。
    要求:樣本出現包裝器無法辨識是否為本次執行的狀態(`outcome` 未知值、缺 `executed`、
    Dart `result` 協定外的值)⇒ 不寫紀錄。"""
    mod = _load()
    if lang == "dart":
        root, test = _dart_repo(tmp_path), _DART_TEST
        runner = _dart_runner(make(root))
    else:
        root, test = _kotlin_repo(tmp_path), _KT_TEST
        runner = _kotlin_runner(make(root))
    res = mod.run(str(root), [test], runner=runner)
    _no_record(res, root, test)


# ── F3(規格 E1 第 171 行):路徑格式 ───────────────────────────────────────

@pytest.mark.parametrize("given", ["test\\foo_test.dart", "./test/foo_test.dart"],
                         ids=["backslash", "dot-slash"])
def test_f3_written_paths_are_repo_relative_posix(tmp_path, given):
    """F3|必須先紅|現行:模組不存在 ⇒ 失敗。
    要求:測試檔以 `test\\foo_test.dart` 或 `./test/foo_test.dart` 給入(等同 CLI `--test`)⇒
    寫出的 `test_file` / `impl_file` 是 repo 根相對、`/` 分隔、不含 `./`、不含反斜線、
    大小寫照實際檔名(`test/foo_test.dart`、`lib/foo.dart`)。"""
    mod = _load()
    root = _dart_repo(tmp_path)
    res = mod.run(str(root), [given], runner=_dart_runner(_fixture("dart_failure.jsonl")))
    assert len(res["records"]) == 1, res
    rec = res["records"][0]
    for key, want in (("test_file", _DART_TEST), ("impl_file", _DART_IMPL)):
        assert rec[key] == want, (key, rec[key])
        assert "\\" not in rec[key] and not rec[key].startswith("./"), rec[key]
    assert _ledger(root) == res["records"]


# ── E1:啟動工具的參數、只讀本次目錄 ───────────────────────────────────────

def _same_path(a, b):
    return pathlib.Path(str(a)).resolve() == pathlib.Path(str(b)).resolve()


def test_e1a_dart_argv_uses_the_file_reporter_and_only_the_designated_test(tmp_path):
    """E1-a|必須先紅|現行:模組不存在 ⇒ 失敗。
    要求:假 runner 被呼叫一次、`language` 為 `dart`;`run_dir` 是 `<root>/.dev/runs/<run_id>/`;
    argv 含 `--file-reporter` 與緊接的 `json:<run_dir>/report.json`;
    argv 中的 `.dart` 只有被指定的 `test/foo_test.dart`(repo 裡另有 `test/bar_test.dart` 不得出現)。"""
    mod = _load()
    root = _dart_repo(tmp_path)
    _write(root, "test/bar_test.dart", u"void main() {}\n")
    runner = _dart_runner(_fixture("dart_failure.jsonl"))
    mod.run(str(root), [_DART_TEST], runner=runner, run_id="r-e1a")
    assert len(runner.calls) == 1, runner.calls
    language, argv, run_dir = runner.calls[0]
    assert language == "dart"
    assert _same_path(run_dir, root / ".dev" / "runs" / "r-e1a")
    i = argv.index("--file-reporter")
    target = argv[i + 1]
    assert target.startswith("json:"), argv
    assert _same_path(target[len("json:"):], pathlib.Path(run_dir) / "report.json"), argv
    dart_args = [a.replace("\\", "/") for a in argv if a.endswith(".dart")]
    assert len(dart_args) == 1 and dart_args[0].endswith(_DART_TEST), argv
    assert not any("bar_test" in a for a in argv), argv


def test_e1b_kotlin_argv_passes_the_upstream_init_script(tmp_path):
    """E1-b ①|必須先紅|現行:模組不存在 ⇒ 失敗。
    要求:假 runner 收到 `language` 為 `kotlin`;argv 含 `-I`,緊接的是 repo 內上游初始化腳本
    (包裝器同目錄的 `redlight_gradle_init.gradle`),且該檔存在。"""
    mod = _load()
    root = _kotlin_repo(tmp_path, impl=u"class Foo\n")
    runner = _kotlin_runner(_kotlin("kotlin_green.json", root))
    mod.run(str(root), [_KT_TEST], runner=runner)
    assert len(runner.calls) == 1, runner.calls
    language, argv, _run_dir = runner.calls[0]
    assert language == "kotlin"
    i = argv.index("-I")
    assert _same_path(argv[i + 1], _INIT_SCRIPT), argv
    assert _INIT_SCRIPT.is_file(), _INIT_SCRIPT


def test_e1b_kotlin_only_reads_the_output_inside_run_dir(tmp_path):
    """E1-b ②|必須先紅|現行:模組不存在 ⇒ 失敗。
    要求:包裝器只讀 `run_dir` 內的輸出。`run_dir` 外(repo 根、`.dev/runs/`)各放一份
    紅燈樣本,`run_dir` 內是綠燈樣本 ⇒ 結果是綠,不受外面的樣本影響。"""
    mod = _load()
    root = _kotlin_repo(tmp_path, impl=u"class Foo\n")
    decoy = json.dumps(_kotlin("kotlin_test_red.json", root))
    _write(root, "kotlin-result.json", decoy)
    _write(root, ".dev/runs/kotlin-result.json", decoy)
    res = mod.run(str(root), [_KT_TEST],
                  runner=_kotlin_runner(_kotlin("kotlin_green.json", root), rc=0))
    assert len(res["records"]) == 1, res
    assert res["records"][0]["test_file"] == _KT_TEST
    assert res["records"][0]["result"] == "green"


# ═════════════════════════════════════════════════════════════════════════════
# 票 152 批二修補(S5f 審查 F1～F5,Station 3d)。
# 類別:「必須先紅」= 在 S4f 實作(`fc4f004e…`)上必須失敗,原因是該格要抓的缺陷;
#       「守住」= 現在就是綠,修完也必須維持綠。
# ═════════════════════════════════════════════════════════════════════════════

def _tree(base):
    """`base` 底下所有檔案與目錄(相對路徑,排序)—— 前後比對用。"""
    base = pathlib.Path(str(base))
    return sorted(p.relative_to(base).as_posix() for p in base.rglob("*"))


def _dart_sample(suites, done=True):
    """合成 〔D-json〕 事件流。`suites`:[(suite.path, [(測試名, result), …]), …]。
    每個 suite 前面有一個隱藏的載入測試(success)。"""
    lines, tid = [{"protocolVersion": "0.1.1", "runnerVersion": "synthetic", "pid": 1,
                   "type": "start", "time": 0}], 0
    ok = True
    for sid, (path, tests) in enumerate(suites):
        lines.append({"suite": {"id": sid, "platform": "vm", "path": path}, "type": "suite", "time": 1})
        for name, result, hidden in [("loading %s" % path, "success", True)] + \
                [(n, r, False) for n, r in tests]:
            tid += 1
            lines.append({"test": {"id": tid, "name": name, "suiteID": sid, "groupIDs": [],
                                   "metadata": {"skip": False, "skipReason": None}},
                          "type": "testStart", "time": 2})
            lines.append({"testID": tid, "result": result, "skipped": False, "hidden": hidden,
                          "type": "testDone", "time": 3})
            ok = ok and result == "success"
    if done:
        lines.append({"success": ok, "type": "done", "time": 4})
    return "".join(json.dumps(l) + "\n" for l in lines)


def _fake_subprocess(calls):
    """模組內 `subprocess` 的替身:`run()` 只記錄參數、回 returncode=0,不執行任何東西。"""
    import types

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))
        return types.SimpleNamespace(returncode=0)

    return types.SimpleNamespace(run=fake_run)


# ── F1 run_id / --run-id ────────────────────────────────────────────────────

_F1_BAD = [
    ("dotdot-slash", lambda tmp: "../x"),
    ("dotdot-backslash", lambda tmp: "..\\x"),
    ("dotdot-twice", lambda tmp: "../../x"),
    ("absolute", lambda tmp: str(tmp / "elsewhere" / "r1")),
    ("nested", lambda tmp: "a/b"),
    ("dot", lambda tmp: "."),
    ("dotdot", lambda tmp: ".."),
    ("empty", lambda tmp: ""),
]


@pytest.mark.parametrize("make", [b[1] for b in _F1_BAD], ids=[b[0] for b in _F1_BAD])
def test_f1a_illegal_run_id_is_rejected_before_any_side_effect(tmp_path, make):
    """F1-a|必須先紅|S4f:`run_id` 不驗證,`os.path.join(.dev/runs, run_id)` 可跳出 `.dev/runs/`;
    `""` 被換成自動 id;非法值在拒絕前已建立 `.dev/runs`。
    要求:`aborted` True、`reason` 非空、runner 0 次、`tmp_path` 檔案樹前後完全相同、帳本無新增。
    中止原因須含固定字串「run_id 格式不合法」(Jeff 2026-10-15 裁定 S3d-2 補強;S3d 初版沒有這一條)。"""
    mod = _load()
    root = _dart_repo(tmp_path)
    run_id = make(tmp_path)
    before = _tree(tmp_path)
    runner = _dart_runner(_fixture("dart_failure.jsonl"))
    res = mod.run(str(root), [_DART_TEST], runner=runner, run_id=run_id)
    assert res["aborted"] is True, res
    assert res.get("reason"), res
    assert u"run_id 格式不合法" in res["reason"], res
    assert runner.calls == [], runner.calls
    assert _tree(tmp_path) == before, sorted(set(_tree(tmp_path)) ^ set(before))
    assert _ledger(root) == []


def test_f1b_cli_rejects_an_illegal_run_id(tmp_path, monkeypatch):
    """F1-b|必須先紅|S4f:CLI `--run-id ../x` 原樣傳入,會建目錄、呼叫工具。
    要求:`main()` 回 2、模組內 `subprocess.run` 的替身 0 次、`tmp_path` 檔案樹前後相同。"""
    mod = _load()
    root = _dart_repo(tmp_path)
    calls = []
    monkeypatch.setattr(mod, "subprocess", _fake_subprocess(calls))
    before = _tree(tmp_path)
    rc = mod.main(["--root", str(root), "--test", _DART_TEST, "--run-id", "../x"])
    assert rc == 2, rc
    assert calls == [], calls
    assert _tree(tmp_path) == before, sorted(set(_tree(tmp_path)) ^ set(before))


def test_f1c_legal_run_id_lands_directly_under_dev_runs(tmp_path):
    """F1-c|守住|合法 `run_id="ok-1_A"`:runner 收到的 `run_dir` 經 realpath 後
    等於 `<root>/.dev/runs/ok-1_A`,是 `.dev/runs/` 的直接子目錄;寫一筆紅燈。"""
    import os
    mod = _load()
    root = _dart_repo(tmp_path)
    runner = _dart_runner(_fixture("dart_failure.jsonl"))
    res = mod.run(str(root), [_DART_TEST], runner=runner, run_id="ok-1_A")
    assert len(runner.calls) == 1, runner.calls
    run_dir = os.path.realpath(runner.calls[0][2])
    runs = os.path.realpath(str(root / ".dev" / "runs"))
    assert run_dir == os.path.realpath(str(root / ".dev" / "runs" / "ok-1_A")), run_dir
    assert os.path.dirname(run_dir) == runs, run_dir
    assert len(res["records"]) == 1 and res["records"][0]["result"] == "red", res


def test_f1d_tool_working_directory_is_the_repo_root(tmp_path, monkeypatch):
    """F1-d|守住|CLI 走 `make_default_runner(root)` 回傳的 runner:模組內 `subprocess.run` 的替身記到的 `cwd`
    經 realpath 後等於暫存 repo 根。替身不寫輸出,這次不寫紀錄是預期的;本格只看 `cwd`。"""
    import os
    mod = _load()
    root = _dart_repo(tmp_path)
    calls = []
    monkeypatch.setattr(mod, "subprocess", _fake_subprocess(calls))
    mod.main(["--root", str(root), "--test", _DART_TEST, "--run-id", "ok-2"])
    assert len(calls) == 1, calls
    assert os.path.realpath(calls[0][1]["cwd"]) == os.path.realpath(str(root)), calls


# ── F2 Dart suite 歸屬 ──────────────────────────────────────────────────────

_F2_P = "packages/p/test/foo_test.dart"
_F2_Q = "packages/q/test/foo_test.dart"


def _f2_repo(tmp_path, tests):
    return _repo(tmp_path, [(t, u"void main() {}\n") for t in tests])


_F2_IMPL = {_DART_TEST: _DART_IMPL, _F2_P: "packages/p/lib/foo.dart", _F2_Q: "packages/q/lib/foo.dart"}


def _f2_premise(tests):
    """前提:每支測試檔是判定端認可的測試檔,且判定端把對應實作配到它。"""
    gate = _load_gate()
    for t in tests:
        if not gate.is_test_path(t):
            pytest.fail(u"前提不成立:is_test_path(%r) 不是 True" % t)
        if gate.test_candidates(_F2_IMPL[t], gate.R3_DART) != [t]:
            pytest.fail(u"前提不成立:test_candidates(%r) = %r"
                        % (_F2_IMPL[t], gate.test_candidates(_F2_IMPL[t], gate.R3_DART)))


@pytest.mark.parametrize("tests", [[_F2_P, _F2_Q], [_DART_TEST, _F2_P]],
                         ids=["two-packages", "root-and-package"])
def test_f2a_ambiguous_suite_is_written_for_neither(tmp_path, tests):
    """F2-a|必須先紅|S4f:`suite.path` 以字尾比對,唯一的 suite `test/foo_test.dart`
    同時對上兩支指定檔,兩支都寫 red。
    要求:`records == []`;兩支都在 `reasons`,原因含「歧義」;帳本無新增。"""
    mod = _load()
    _f2_premise(tests)
    root = _f2_repo(tmp_path, tests)
    sample = _dart_sample([("test/foo_test.dart", [("foo returns 1", "failure")])])
    res = mod.run(str(root), tests, runner=_dart_runner(sample))
    assert res["records"] == [], res
    for t in tests:
        assert u"歧義" in res["reasons"].get(t, ""), res
    assert _ledger(root) == []


@pytest.mark.parametrize("absolute", [False, True], ids=["full-paths", "absolute-paths"])
def test_f2b_uniquely_matched_suites_are_each_recorded(tmp_path, absolute):
    """F2-b|守住|兩個 suite 的 `path` 是完整路徑(或暫存 repo 底下的絕對路徑):
    p 一筆 red、`impl_file=packages/p/lib/foo.dart`;q 一筆 green、`impl_file=packages/q/lib/foo.dart`;
    兩支都不在 `reasons`。防止修成「同尾名一律不寫」。"""
    mod = _load()
    tests = [_F2_P, _F2_Q]
    _f2_premise(tests)
    root = _f2_repo(tmp_path, tests)
    path = (lambda t: str(root.joinpath(*t.split("/")))) if absolute else (lambda t: t)
    sample = _dart_sample([(path(_F2_P), [("p fails", "failure")]),
                           (path(_F2_Q), [("q passes", "success")])])
    res = mod.run(str(root), tests, runner=_dart_runner(sample))
    by = {r["test_file"]: r for r in res["records"]}
    assert set(by) == {_F2_P, _F2_Q}, res
    assert by[_F2_P]["result"] == "red" and by[_F2_P]["impl_file"] == "packages/p/lib/foo.dart", by
    assert by[_F2_Q]["result"] == "green" and by[_F2_Q]["impl_file"] == "packages/q/lib/foo.dart", by
    assert _F2_P not in res["reasons"] and _F2_Q not in res["reasons"], res


# ── F3 不同磁碟代號(純字串;不碰任何 tmp_path 以外的路徑)────────────────────

_FAKE_DRIVE = "Q:"


def _on_fake_drive(p):
    return str(p).replace("\\", "/").lower().startswith(_FAKE_DRIVE.lower())


def _isolate_fake_drive(mod, monkeypatch):
    """把被測模組的 `os` / `io` 換成本地代理:
    `relpath` 碰到假磁碟代號 ⇒ 丟 Windows 那句 `ValueError`(重現錯誤來源,兩個平台一致);
    檔案系統函式碰到假磁碟代號 ⇒ 測試直接失敗(證明沒有去探查那條路徑)。只影響被測模組。"""
    import os
    import types

    real_relpath = os.path.relpath

    def relpath(path, start=os.curdir):
        if _on_fake_drive(path) or _on_fake_drive(start):
            raise ValueError("path is on mount %r, start on mount %r"
                             % (_FAKE_DRIVE, os.path.splitdrive(os.path.abspath(str(start)))[0]))
        return real_relpath(path, start)

    def guard(fn):
        def wrapped(*args, **kwargs):
            if args and _on_fake_drive(args[0]):
                pytest.fail(u"碰到假磁碟路徑:%s(%r)" % (fn.__name__, args[0]))
            return fn(*args, **kwargs)
        return wrapped

    path_ns = types.SimpleNamespace(**{k: getattr(os.path, k) for k in dir(os.path) if not k.startswith("__")})
    path_ns.relpath = relpath
    for name in ("exists", "isfile", "isdir", "lexists"):
        setattr(path_ns, name, guard(getattr(os.path, name)))
    os_ns = types.SimpleNamespace(**{k: getattr(os, k) for k in dir(os) if not k.startswith("__")})
    os_ns.path = path_ns
    for name in ("listdir", "mkdir", "makedirs"):
        setattr(os_ns, name, guard(getattr(os, name)))
    io_ns = types.SimpleNamespace(**{k: getattr(io, k) for k in dir(io) if not k.startswith("__")})
    io_ns.open = guard(io.open)
    monkeypatch.setattr(mod, "os", os_ns)
    monkeypatch.setattr(mod, "io", io_ns)


def _f3_premise(mod, tmp_path):
    """前提:patch 之後,被測模組看到的 `relpath` 對假磁碟代號確實丟 `ValueError`。"""
    try:
        mod.os.path.relpath(_FAKE_DRIVE + "/x", str(tmp_path))
    except ValueError:
        return
    pytest.fail(u"前提不成立:patch 後 relpath(%r, tmp_path) 沒有丟 ValueError" % (_FAKE_DRIVE + "/x"))


def test_f3a_test_path_on_another_drive_aborts(tmp_path, monkeypatch):
    """F3-a|必須先紅|S4f:`_repo_relative()` 的 `os.path.relpath` 對不同磁碟丟 `ValueError`,
    `run()` 沒接住、往外丟。
    要求:不丟例外;`aborted` True、`reason` 非空;runner 0 次;帳本無新增;沒碰到假磁碟路徑。"""
    mod = _load()
    root = _dart_repo(tmp_path)
    _isolate_fake_drive(mod, monkeypatch)
    _f3_premise(mod, tmp_path)
    runner = _dart_runner(_fixture("dart_failure.jsonl"))
    try:
        res = mod.run(str(root), [_FAKE_DRIVE + "/nowhere/test/foo_test.dart"], runner=runner)
    except ValueError as e:
        pytest.fail(u"run() 丟出未接住的例外:%r" % (e,))
    assert res["aborted"] is True, res
    assert res.get("reason"), res
    assert runner.calls == [], runner.calls
    assert _ledger(root) == []


def test_f3b_suite_path_on_another_drive_matches_nothing(tmp_path, monkeypatch):
    """F3-b|必須先紅|S4f:`_dart_suite_matches()` 對不同磁碟的絕對 `suite.path` 呼叫
    `os.path.relpath`,丟 `ValueError` 沒接住。
    要求:不丟例外;`records == []`;`test/foo_test.dart` 在 `reasons`;帳本無新增;沒碰到假磁碟路徑。"""
    mod = _load()
    root = _dart_repo(tmp_path)
    _isolate_fake_drive(mod, monkeypatch)
    _f3_premise(mod, tmp_path)
    sample = _dart_sample([(_FAKE_DRIVE + "/elsewhere/test/foo_test.dart",
                            [("foo returns 1", "failure")])])
    try:
        res = mod.run(str(root), [_DART_TEST], runner=_dart_runner(sample))
    except ValueError as e:
        pytest.fail(u"run() 丟出未接住的例外:%r" % (e,))
    assert res["records"] == [], res
    assert _DART_TEST in res["reasons"], res
    assert _ledger(root) == []


# ── F4 檔名只剩副檔名的隱藏式多候選 ─────────────────────────────────────────

_F4_DART_TEST = "test/.dart_test.dart"
_F4_KT_TEST = "app/src/test/kotlin/x/.ktTest.kt"


@pytest.mark.parametrize("lang", ["dart", "kotlin"], ids=["dart-dotname", "kotlin-dotname"])
def test_f4_dotname_with_two_accepted_impls_aborts(tmp_path, lang):
    """F4|必須先紅|S4f:`_impl_for()` 只產生 `.dart.dart` / `.kt.kt` 一支並宣稱唯一,照寫紀錄;
    但判定端(`splitext` 不去隱藏檔的副檔名)同時認可 `lib/.dart` 與 `lib/.dart.dart`(Kotlin 同形)。
    要求:`aborted` True、`reason` 非空;runner 0 次;帳本無新增。"""
    mod = _load()
    gate = _load_gate()
    if lang == "dart":
        test, impls, glang = _F4_DART_TEST, ["lib/.dart", "lib/.dart.dart"], gate.R3_DART
    else:
        test = _F4_KT_TEST
        impls = ["app/src/main/kotlin/x/.kt", "app/src/main/kotlin/x/.kt.kt"]
        glang = gate.R3_KOTLIN
    for impl in impls:
        if gate.test_candidates(impl, glang) != [test]:
            pytest.fail(u"前提不成立:判定端行為與 S5f 不同(test_candidates(%r) = %r)"
                        % (impl, gate.test_candidates(impl, glang)))
    root = _repo(tmp_path, [(test, u"// synthetic\n")])
    if lang == "dart":
        runner = _dart_runner(_dart_sample([(test, [("dot fails", "failure")])]))
    else:
        sample = _kotlin("kotlin_compile_red.json", root)
        sample["compile_errors"] = "e: file:///%s/%s:3:5 Unresolved reference\n" % (root.as_posix(), test)
        runner = _kotlin_runner(sample)
    res = mod.run(str(root), [test], runner=runner)
    assert res["aborted"] is True, res
    assert res.get("reason"), res
    assert runner.calls == [], runner.calls
    assert _ledger(root) == []


# ── F5 候選本身是測試路徑時的漏配 ───────────────────────────────────────────

_F5 = [
    ("root-module", "src/test/kotlin/a/src/test/kotlin/FooTest.kt",
     "src/main/kotlin/a/src/test/kotlin/Foo.kt", "src/test/kotlin/a/src/main/kotlin/Foo.kt", ":"),
    ("app-module", "app/src/test/kotlin/x/src/test/kotlin/FooTest.kt",
     "app/src/main/kotlin/x/src/test/kotlin/Foo.kt", "app/src/test/kotlin/x/src/main/kotlin/Foo.kt", ":app"),
]


@pytest.mark.parametrize("test,want,excluded,project", [f[1:] for f in _F5], ids=[f[0] for f in _F5])
def test_f5_candidate_that_is_itself_a_test_path_is_ignored(tmp_path, test, want, excluded, project):
    """F5|必須先紅|S4f:`_impl_for()` 把本身是測試路徑的候選也算進多候選而中止,
    判定端唯一會問紅燈的那支實作永遠拿不到紅燈。
    要求(Kotlin 編譯紅燈樣本,開跑前實作不存在):不中止、runner 1 次、一筆 red,
    `impl_file` 正好是判定端認可且不是測試路徑的那一支;帳本 = `records`。"""
    mod = _load()
    gate = _load_gate()
    if gate.test_candidates(want, gate.R3_KOTLIN) != [test]:
        pytest.fail(u"前提不成立:test_candidates(%r) = %r" % (want, gate.test_candidates(want, gate.R3_KOTLIN)))
    if gate.is_test_path(want) is not False:
        pytest.fail(u"前提不成立:is_test_path(%r) 不是 False" % want)
    if gate.is_test_path(excluded) is not True:
        pytest.fail(u"前提不成立:is_test_path(%r) 不是 True" % excluded)
    root = _repo(tmp_path, [(test, u"class FooTest\n")])
    sample = _kotlin("kotlin_compile_red.json", root)
    for t in sample["tasks"]:
        t["project"] = project
        t["path"] = (project if project != ":" else "") + ":" + t["path"].rsplit(":", 1)[-1]
    sample["compile_errors"] = "e: file:///%s/%s:3:5 Unresolved reference: Foo\n" % (root.as_posix(), test)
    runner = _kotlin_runner(sample)
    res = mod.run(str(root), [test], runner=runner)
    assert res["aborted"] is False, res
    assert len(runner.calls) == 1, runner.calls
    assert len(res["records"]) == 1, res
    rec = res["records"][0]
    assert rec["result"] == "red" and rec["impl_file"] == want, rec
    assert rec["impl_exists"] is False and rec["impl_hash"] is None, rec
    assert _ledger(root) == res["records"]


# ═════════════════════════════════════════════════════════════════════════════
# 票 152 批二 G1 / G2(S5g 複審,Station 3e)。
# 類別:「必須先紅」= 在 S4g 實作(`3ab6ef4d…`)上必須失敗,原因是該格要抓的缺陷;
#       「守住」= 現在就是綠,修完也必須維持綠。
# ═════════════════════════════════════════════════════════════════════════════

# ── G1 絕對路徑的 Dart suite 只能精確配對 ───────────────────────────────────

def _g1_repo(tmp_path, tests):
    """指定的測試檔＋repo 根另一支 `test/foo_test.dart`(不一定被指定)。"""
    files = {t: u"void main() {}\n" for t in tests}
    files.setdefault(_DART_TEST, u"void main() {}\n")
    return _repo(tmp_path, sorted(files.items()))


def test_g1_single_pkg_abs_root_suite_is_not_attributed(tmp_path):
    """G1 `g1-single-pkg-abs-root`|必須先紅|S4g:絕對路徑 `<root>/test/foo_test.dart` 轉成
    repo 根相對後仍走字尾比對,被當成「相對於 `packages/p/` 的 `test/foo_test.dart`」,紅燈記給 p。
    要求:只指定 p ⇒ `records == []`;p 在 `reasons`,原因含「沒有出現」;帳本無新增。"""
    mod = _load()
    _f2_premise([_F2_P])
    root = _g1_repo(tmp_path, [_F2_P])
    sample = _dart_sample([(str(root / "test" / "foo_test.dart"), [("root fails", "failure")])])
    res = mod.run(str(root), [_F2_P], runner=_dart_runner(sample))
    assert res["records"] == [], res
    assert u"沒有出現" in res["reasons"].get(_F2_P, ""), res
    assert _ledger(root) == []


def test_g1_root_and_pkg_abs_root_suite_goes_to_its_owner(tmp_path):
    """G1 `g1-root-and-pkg-abs-root`|必須先紅|S4g:同上的絕對路徑同時對上 `test/foo_test.dart`
    (精確)與 p(字尾)⇒ 判成歧義,正確擁有者也被擋。
    要求:`test/foo_test.dart` 一筆 red、`impl_file=lib/foo.dart`;p 不寫,原因含「沒有出現」、不含「歧義」。"""
    mod = _load()
    tests = [_DART_TEST, _F2_P]
    _f2_premise(tests)
    root = _g1_repo(tmp_path, tests)
    sample = _dart_sample([(str(root / "test" / "foo_test.dart"), [("root fails", "failure")])])
    res = mod.run(str(root), tests, runner=_dart_runner(sample))
    by = {r["test_file"]: r for r in res["records"]}
    assert set(by) == {_DART_TEST}, res
    assert by[_DART_TEST]["result"] == "red" and by[_DART_TEST]["impl_file"] == _DART_IMPL, by
    why = res["reasons"].get(_F2_P, "")
    assert u"沒有出現" in why and u"歧義" not in why, res
    assert _ledger(root) == res["records"]


@pytest.mark.parametrize("backslash", [False, True], ids=["g1-abs-exact-fwd", "g1-abs-exact-back"])
def test_g1_absolute_full_path_still_matches_exactly(tmp_path, backslash):
    """G1 對照組|守住|`suite.path` 是 p 的完整絕對路徑(正斜線 / 全部反斜線),repo 根另有
    `test/foo_test.dart`(不指定)⇒ p 一筆 red、`impl_file=packages/p/lib/foo.dart`。
    防止修成「絕對路徑一律拒絕」。"""
    mod = _load()
    _f2_premise([_F2_P])
    root = _g1_repo(tmp_path, [_F2_P])
    path = root.as_posix() + "/" + _F2_P
    if backslash:
        path = path.replace("/", "\\")
    sample = _dart_sample([(path, [("p fails", "failure")])])
    res = mod.run(str(root), [_F2_P], runner=_dart_runner(sample))
    assert len(res["records"]) == 1, res
    rec = res["records"][0]
    assert rec["test_file"] == _F2_P and rec["result"] == "red", rec
    assert rec["impl_file"] == "packages/p/lib/foo.dart", rec


# ── G2 磁碟相對路徑必須在任何檔案存取之前拒絕 ───────────────────────────────

_DRIVE_RELATIVE = re.compile(r"^[A-Za-z]:(?!/)")


def _isolate_drive_relative(mod, monkeypatch, root, given):
    """把被測模組的 `os` / `io` 換成本地代理:參數是磁碟相對路徑,或落在
    `os.path.join(root, <給的路徑第一段>)` 底下 ⇒ 測試直接失敗(「碰到磁碟相對路徑」)。
    只攔截、不重現:不讀寫任何真正的磁碟相對路徑。只影響被測模組。"""
    import os
    import types

    first = given.replace("\\", "/").split("/")[0]
    trap = os.path.normcase(os.path.join(str(root), first))

    def hit(p):
        s = str(p)
        if _DRIVE_RELATIVE.match(s.replace("\\", "/")):
            return True
        n = os.path.normcase(s)
        return n == trap or n.startswith(trap + os.sep) or n.startswith(trap + "/")

    def guard(fn):
        def wrapped(*args, **kwargs):
            if args and hit(args[0]):
                pytest.fail(u"碰到磁碟相對路徑:%s(%r)" % (fn.__name__, args[0]))
            return fn(*args, **kwargs)
        return wrapped

    path_ns = types.SimpleNamespace(**{k: getattr(os.path, k) for k in dir(os.path) if not k.startswith("__")})
    for name in ("exists", "isfile", "isdir", "lexists", "realpath"):
        setattr(path_ns, name, guard(getattr(os.path, name)))
    os_ns = types.SimpleNamespace(**{k: getattr(os, k) for k in dir(os) if not k.startswith("__")})
    os_ns.path = path_ns
    for name in ("listdir", "mkdir", "makedirs"):
        setattr(os_ns, name, guard(getattr(os, name)))
    io_ns = types.SimpleNamespace(**{k: getattr(io, k) for k in dir(io) if not k.startswith("__")})
    io_ns.open = guard(io.open)
    monkeypatch.setattr(mod, "os", os_ns)
    monkeypatch.setattr(mod, "io", io_ns)


def test_g2_same_drive_relative_path_is_rejected_before_any_access(tmp_path, monkeypatch):
    """G2 `g2-same-drive`|必須先紅|S4g:`<D>x/test/foo_test.dart`(有磁碟代號、沒有斜線)
    不進 `relpath` 分支,被當成 repo 根相對字串,`_actual_case` 先對 `<root>/x…` 做檔案存取。
    要求:`aborted` True、`reason` 含「磁碟相對路徑」、runner 0 次、帳本無新增、
    `tmp_path` 檔案樹前後相同、沒有觸發攔截。不建立任何對應的檔案。"""
    import os
    mod = _load()
    root = _dart_repo(tmp_path)
    # Windows:`tmp_path` 所在的磁碟代號;POSIX:固定 `C:`(純字串)
    drive = os.path.splitdrive(str(tmp_path))[0] if os.name == "nt" else "C:"
    given = drive + "x/test/foo_test.dart"
    _isolate_drive_relative(mod, monkeypatch, root, given)
    try:
        mod.os.path.exists(drive + "x")
    except pytest.fail.Exception:
        pass
    else:
        pytest.fail(u"前提不成立:攔截生效後 exists(%r) 沒有失敗" % (drive + "x"))
    before = _tree(tmp_path)
    runner = _dart_runner(_fixture("dart_failure.jsonl"))
    res = mod.run(str(root), [given], runner=runner)
    assert res["aborted"] is True, res
    assert u"磁碟相對路徑" in res.get("reason", ""), res
    assert runner.calls == [], runner.calls
    assert _ledger(root) == []
    assert _tree(tmp_path) == before, sorted(set(_tree(tmp_path)) ^ set(before))


def test_g2_other_drive_relative_path_is_rejected_before_any_access(tmp_path, monkeypatch):
    """G2 `g2-other-drive`|必須先紅|S4g:`Q:x/test/foo_test.dart` 同上不進 `relpath` 分支,
    Windows 上 `os.path.join(root, "Q:x")` 變成 `Q:x`,對另一個磁碟做檔案存取。
    要求:不丟例外;`aborted` True、`reason` 含「磁碟相對路徑」;runner 0 次;帳本無新增;
    沒有觸發「碰到假磁碟路徑」(用 `_isolate_fake_drive()` 受控模擬,不真的探查其他磁碟)。"""
    mod = _load()
    root = _dart_repo(tmp_path)
    _isolate_fake_drive(mod, monkeypatch)
    try:
        mod.os.path.exists(_FAKE_DRIVE + "/x")
    except pytest.fail.Exception:
        pass
    else:
        pytest.fail(u"前提不成立:_isolate_fake_drive() 生效後 exists(%r) 沒有失敗" % (_FAKE_DRIVE + "/x"))
    runner = _dart_runner(_fixture("dart_failure.jsonl"))
    given = _FAKE_DRIVE[0] + ":x/test/foo_test.dart"
    try:
        res = mod.run(str(root), [given], runner=runner)
    except ValueError as e:
        pytest.fail(u"run() 丟出未接住的例外:%r" % (e,))
    assert res["aborted"] is True, res
    assert u"磁碟相對路徑" in res.get("reason", ""), res
    assert runner.calls == [], runner.calls
    assert _ledger(root) == []


# ═════════════════════════════════════════════════════════════════════════════
# 票 152 批二 H1 / H2(S5h 複審,Station 3f)。
# 類別:「必須先紅」= 在 S4h 實作(`06faf9dd…`)上必須失敗,原因是該格要抓的缺陷;
#       「守住」= 現在就是綠,修完也必須維持綠。
# ═════════════════════════════════════════════════════════════════════════════

# ── H1 正規化後才出現的磁碟相對段 ───────────────────────────────────────────

_H1_OTHER_DRIVE = [
    ("dot-slash", "./Q:x/test/foo_test.dart"),
    ("dot-backslash", ".\\Q:x\\test\\foo_test.dart"),
    ("mid-segment", "pkg/Q:x/test/foo_test.dart"),
    ("dotdot", "a/../Q:x/test/foo_test.dart"),
]


@pytest.mark.parametrize("given", [g[1] for g in _H1_OTHER_DRIVE], ids=[g[0] for g in _H1_OTHER_DRIVE])
def test_h1_drive_relative_segment_after_normalisation_other_drive(tmp_path, monkeypatch, given):
    """H1(不同磁碟)|必須先紅|S4h:G2 只比原始字串開頭;`./Q:x/…`、`.\\Q:x\\…`、
    `pkg/Q:x/…`、`a/../Q:x/…` 正規化或分段後才出現磁碟相對段,繞過 G2,
    `_actual_case` / `isfile` 經 `os.path.join` 對 `Q:x…` 做檔案存取。
    要求:不丟例外;`aborted` True、原因含「磁碟相對路徑」;runner 0 次;帳本無新增;
    沒有觸發「碰到假磁碟路徑」(`_isolate_fake_drive()` 受控模擬,不真的探查其他磁碟)。"""
    mod = _load()
    root = _dart_repo(tmp_path)
    _isolate_fake_drive(mod, monkeypatch)
    try:
        mod.os.path.exists(_FAKE_DRIVE + "/x")
    except pytest.fail.Exception:
        pass
    else:
        pytest.fail(u"前提不成立:_isolate_fake_drive() 生效後 exists(%r) 沒有失敗" % (_FAKE_DRIVE + "/x"))
    runner = _dart_runner(_fixture("dart_failure.jsonl"))
    try:
        res = mod.run(str(root), [given], runner=runner)
    except ValueError as e:
        pytest.fail(u"run() 丟出未接住的例外:%r" % (e,))
    assert res["aborted"] is True, res
    assert u"磁碟相對路徑" in res.get("reason", ""), res
    assert runner.calls == [], runner.calls
    assert _ledger(root) == []


def test_h1_drive_relative_segment_after_normalisation_same_drive(tmp_path, monkeypatch):
    """H1(同磁碟)|必須先紅|S4h:`./<D>x/test/foo_test.dart` 去掉 `./` 之後才出現 `<D>x`,
    繞過 G2;Windows 上 `os.path.join(root, "<D>x")` 落在 `<root>\\x`,寫出非 repo 根相對的紀錄。
    `<D>`:Windows 取 `tmp_path` 自己的磁碟代號,POSIX 固定 `C:`(純字串)。攔截器沿用
    `_isolate_drive_relative()`,傳入**正規化後**的路徑,攔截點是 `os.path.join(root, "<D>x")`。
    要求:`aborted` True、原因含「磁碟相對路徑」、runner 0 次、帳本無新增、
    `tmp_path` 檔案樹前後相同、沒有觸發攔截。不建立任何對應的檔案。"""
    import os
    import posixpath
    mod = _load()
    root = _dart_repo(tmp_path)
    drive = os.path.splitdrive(str(tmp_path))[0] if os.name == "nt" else "C:"
    given = "./" + drive + "x/test/foo_test.dart"
    _isolate_drive_relative(mod, monkeypatch, root, posixpath.normpath(given))
    try:
        mod.os.path.exists(drive + "x")
    except pytest.fail.Exception:
        pass
    else:
        pytest.fail(u"前提不成立:攔截生效後 exists(%r) 沒有失敗" % (drive + "x"))
    before = _tree(tmp_path)
    runner = _dart_runner(_fixture("dart_failure.jsonl"))
    res = mod.run(str(root), [given], runner=runner)
    assert res["aborted"] is True, res
    assert u"磁碟相對路徑" in res.get("reason", ""), res
    assert runner.calls == [], runner.calls
    assert _ledger(root) == []
    assert _tree(tmp_path) == before, sorted(set(_tree(tmp_path)) ^ set(before))


_H1_LEGAL = [
    ("abs-fwd", lambda root: root.as_posix() + "/" + _DART_TEST),
    ("abs-back", lambda root: (root.as_posix() + "/" + _DART_TEST).replace("/", "\\")),
    ("abs-lower-drive", lambda root: (lambda s: s[:1].lower() + s[1:])(str(root / "test" / "foo_test.dart"))),
]


@pytest.mark.parametrize("make", [g[1] for g in _H1_LEGAL], ids=[g[0] for g in _H1_LEGAL])
def test_h1_legal_absolute_test_paths_are_not_blocked(tmp_path, make):
    """H1 對照組|守住|落在 `tmp_path` 內的完整絕對路徑(正斜線、反斜線、磁碟代號小寫)
    照常記錄:不中止、1 筆 red、`test_file=test/foo_test.dart`、`impl_file=lib/foo.dart`。
    防止修 H1 時把絕對路徑開頭的 `X:/` 也當成磁碟相對段。
    (`./test/foo_test.dart` 已由既有 `test_f3_written_paths_are_repo_relative_posix[dot-slash]` 守住。)"""
    mod = _load()
    root = _dart_repo(tmp_path)
    runner = _dart_runner(_fixture("dart_failure.jsonl"))
    res = mod.run(str(root), [make(root)], runner=runner)
    assert res["aborted"] is False, res
    assert len(res["records"]) == 1, res
    rec = res["records"][0]
    assert rec["test_file"] == _DART_TEST and rec["impl_file"] == _DART_IMPL, rec
    assert rec["result"] == "red", rec


# ── H2 只能讀一次的序列 ─────────────────────────────────────────────────────

def _h2_run(tmp_path, tests):
    mod = _load()
    root = _dart_repo(tmp_path)
    runner = _dart_runner(_fixture("dart_failure.jsonl"))
    return mod.run(str(root), tests, runner=runner), runner, root


def test_h2_iterator_tests_behave_like_a_list(tmp_path):
    """H2|必須先紅|S4h:G2 的掃描迴圈把 iterator 讀空,第二個迴圈拿到空序列 ⇒
    沒有測試檔也啟動工具(`language=None`),回傳像成功。
    要求:`tests=iter(["test/foo_test.dart"])` 與傳 list 相同:不中止、1 筆紀錄、
    runner 1 次且 `language` 不是 None。"""
    res, runner, root = _h2_run(tmp_path, iter([_DART_TEST]))
    assert res["aborted"] is False, res
    assert len(runner.calls) == 1, runner.calls
    assert runner.calls[0][0] is not None, runner.calls
    assert len(res["records"]) == 1 and res["records"][0]["test_file"] == _DART_TEST, res
    assert _ledger(root) == res["records"]


def test_h2_tuple_tests_behave_like_a_list(tmp_path):
    """H2 對照組|守住|`tests=("test/foo_test.dart",)`:不中止、1 筆紀錄、runner 1 次、`language=dart`。"""
    res, runner, root = _h2_run(tmp_path, (_DART_TEST,))
    assert res["aborted"] is False, res
    assert len(runner.calls) == 1 and runner.calls[0][0] == "dart", runner.calls
    assert len(res["records"]) == 1 and res["records"][0]["test_file"] == _DART_TEST, res
    assert _ledger(root) == res["records"]


# ═════════════════════════════════════════════════════════════════════════════
# 票 152 批二 J1(S5h-2 核對,Station 3g)。
# 類別:「必須先紅」= 在 S4i 實作(`8c24ab7b…`)上必須失敗,原因是該格要抓的缺陷。
# Jeff 2026-10-15 約 20:43 選「A 一次封死」:除了開頭的 ASCII `X:/`,任一段含冒號就拒絕;
# 正規化前、後的各段都要檢查(審查方補充第 1、2 點;裁決助手記錄,非逐字原話)。
# 「一次封死」是政策目標,這幾格只支持它們自己列出的寫法。
# ═════════════════════════════════════════════════════════════════════════════

_ASCII_ABS_DRIVE = re.compile(r"^[A-Za-z]:/")


def _isolate_outside_tmp(mod, monkeypatch, tmp_path):
    """把被測模組的 `os` / `io` 換成本地代理,回 `(calls, blocked)`:
    - `calls`:經代理的每一次檔案系統呼叫(含放行的)—— 用來斷言「在任何存取之前」;
    - `blocked`:參數落在 `tmp_path` 外,或去掉開頭 ASCII `X:/` 之後仍含冒號
      (磁碟代號段、NTFS 替代資料流)⇒ 記錄後讓測試直接失敗,**不呼叫原函式**。
    只攔截、不重現:不探查其他磁碟、磁碟相對路徑或替代資料流。只影響被測模組。"""
    import os
    import types

    base = os.path.normcase(os.path.abspath(str(tmp_path)))
    calls, blocked = [], []

    def outside_or_colon(p):
        s = str(p)
        posix = s.replace("\\", "/")
        rest = posix[3:] if _ASCII_ABS_DRIVE.match(posix) else posix
        if ":" in rest or not os.path.isabs(s):
            return True
        n = os.path.normcase(os.path.normpath(s))
        return not (n == base or n.startswith(base + os.sep))

    def guard(fn):
        def wrapped(*args, **kwargs):
            calls.append((fn.__name__, args[0] if args else None))
            if args and outside_or_colon(args[0]):
                blocked.append((fn.__name__, args[0]))
                pytest.fail(u"碰到 tmp_path 外或含冒號的路徑:%s(%r)" % (fn.__name__, args[0]))
            return fn(*args, **kwargs)
        return wrapped

    path_ns = types.SimpleNamespace(**{k: getattr(os.path, k) for k in dir(os.path) if not k.startswith("__")})
    for name in ("exists", "isfile", "isdir", "lexists", "islink", "realpath", "relpath",
                 "getsize", "getmtime"):
        setattr(path_ns, name, guard(getattr(os.path, name)))
    os_ns = types.SimpleNamespace(**{k: getattr(os, k) for k in dir(os) if not k.startswith("__")})
    os_ns.path = path_ns
    for name in ("listdir", "mkdir", "makedirs", "stat", "lstat", "scandir", "open",
                 "remove", "unlink", "rmdir", "rename", "replace"):
        setattr(os_ns, name, guard(getattr(os, name)))
    io_ns = types.SimpleNamespace(**{k: getattr(io, k) for k in dir(io) if not k.startswith("__")})
    io_ns.open = guard(io.open)
    monkeypatch.setattr(mod, "os", os_ns)
    monkeypatch.setattr(mod, "io", io_ns)
    return calls, blocked


def _j1_premise(mod, tmp_path, calls, blocked):
    """前提:攔截生效後,repo 外(`1:x`)與 tmp_path 內含冒號的路徑都會讓測試失敗;然後清空紀錄。"""
    import os
    for probe in ("1:x", str(tmp_path / "premise") + os.sep + "a:b"):
        try:
            mod.os.path.exists(probe)
        except pytest.fail.Exception:
            continue
        pytest.fail(u"前提不成立:攔截生效後 exists(%r) 沒有失敗" % probe)
    del calls[:], blocked[:]


# ── J1 非 ASCII 字母的「磁碟代號」段 ────────────────────────────────────────

_J1_DRIVE_LIKE = [
    ("mid-digit", "pkg/1:x/test/foo_test.dart"),
    ("dot-plus", "./+:x/test/foo_test.dart"),
    ("mid-fullwidth-Q", u"pkg/\uff31:x/test/foo_test.dart"),     # 全形 Q
    ("lead-digit", "1:x/test/foo_test.dart"),
    ("mid-underscore-sep", "pkg/_:/x/test/foo_test.dart"),
]


@pytest.mark.parametrize("given", [g[1] for g in _J1_DRIVE_LIKE], ids=[g[0] for g in _J1_DRIVE_LIKE])
def test_j1_non_ascii_drive_letter_segment_is_rejected_before_any_access(tmp_path, monkeypatch, given):
    """J1(非 ASCII 字母的磁碟代號段)|必須先紅|S4i:`_DRIVE_SEGMENT` 只認 `[A-Za-z]:`;
    Windows 的 `ntpath.splitdrive` 把「第二個字元是冒號」就當磁碟代號,`1:x`、`+:x`、`Ｑ:x`、`_:`
    經 `os.path.join` 換掉前綴,`_actual_case` 對 repo 外做檔案存取(S5h-2 §5.2)。
    要求:不丟例外;`aborted` True、原因含「磁碟相對路徑」;runner 0 次;帳本無新增;
    攔截器沒有被觸發,而且被測模組沒有做任何檔案系統呼叫(在任何存取之前中止)。"""
    mod = _load()
    root = _dart_repo(tmp_path)
    calls, blocked = _isolate_outside_tmp(mod, monkeypatch, tmp_path)
    _j1_premise(mod, tmp_path, calls, blocked)
    runner = _dart_runner(_fixture("dart_failure.jsonl"))
    try:
        res = mod.run(str(root), [given], runner=runner)
    except Exception as e:
        pytest.fail(u"run() 丟出未接住的例外:%r" % (e,))
    assert res["aborted"] is True, res
    assert u"磁碟相對路徑" in res.get("reason", ""), res
    assert runner.calls == [], runner.calls
    assert _ledger(root) == []
    assert blocked == [], blocked
    assert calls == [], calls


# ── J1 任一段含冒號(例:NTFS 替代資料流)──────────────────────────────────

_J1_COLON = [
    ("mid-colon", "pkg/ab:c/test/foo_test.dart"),
    ("ads-stream", "test/foo_test.dart:s"),
]


@pytest.mark.parametrize("given", [g[1] for g in _J1_COLON], ids=[g[0] for g in _J1_COLON])
def test_j1_any_colon_segment_is_rejected_before_any_access(tmp_path, monkeypatch, given):
    """J1(任一段含冒號)|必須先紅|S4i:`ab:c`、`foo_test.dart:s` 不以「字母＋冒號」開頭,
    不算磁碟相對段;`_actual_case` 對 `<root>/pkg/ab:c`、`<root>/test/foo_test.dart:s` 做檔案存取
    (Windows 上是替代資料流的寫法)。落點在 `tmp_path` 內,但硬性限制不准探查替代資料流,
    所以同一個攔截器把含冒號的參數一律擋下、不呼叫原函式。不建立任何含冒號的檔名或串流。
    要求:`aborted` True、原因含「冒號」;runner 0 次;帳本無新增;`tmp_path` 檔案樹前後相同;
    攔截器沒有被觸發、被測模組沒有做任何檔案系統呼叫。"""
    mod = _load()
    root = _dart_repo(tmp_path)
    calls, blocked = _isolate_outside_tmp(mod, monkeypatch, tmp_path)
    _j1_premise(mod, tmp_path, calls, blocked)
    before = _tree(tmp_path)
    runner = _dart_runner(_fixture("dart_failure.jsonl"))
    try:
        res = mod.run(str(root), [given], runner=runner)
    except Exception as e:
        pytest.fail(u"run() 丟出未接住的例外:%r" % (e,))
    assert res["aborted"] is True, res
    assert u"冒號" in res.get("reason", ""), res
    assert runner.calls == [], runner.calls
    assert _ledger(root) == []
    assert _tree(tmp_path) == before, sorted(set(_tree(tmp_path)) ^ set(before))
    assert blocked == [], blocked
    assert calls == [], calls


# ── J1 冒號段在正規化時被消掉 ───────────────────────────────────────────────

_J1_PKG_TEST = "pkg/test/foo_test.dart"
_J1_PKG_IMPL = "pkg/lib/foo.dart"
_J1_NORMALISED_AWAY = [
    ("colon-then-dotdot", "pkg/a:b/../test/foo_test.dart"),
    ("digit-drive-then-dotdot", "pkg/1:x/../test/foo_test.dart"),
]


@pytest.mark.parametrize("given", [g[1] for g in _J1_NORMALISED_AWAY], ids=[g[0] for g in _J1_NORMALISED_AWAY])
def test_j1_colon_segment_removed_by_normalisation_is_still_rejected(tmp_path, monkeypatch, given):
    """J1(冒號段在正規化時被消掉)|必須先紅|S4i:只檢查 `posixpath.normpath` 之後的段;
    `pkg/a:b/../…`、`pkg/1:x/../…` 正規化成合法的 `pkg/test/foo_test.dart`,冒號段被吃掉,照常寫紀錄。
    正規化前的原始各段也要檢查(審查方補充第 2 點)。暫存 repo 放好 `pkg/test/foo_test.dart`、
    樣本的 suite 就是它 ⇒ 沒擋就會照常記錄一筆紅燈。
    要求:`aborted` True、原因含「冒號」;runner 0 次;帳本無新增;攔截器沒有被觸發
    (不准觸發 repo 外的存取)、被測模組沒有做任何檔案系統呼叫。"""
    mod = _load()
    gate = _load_gate()
    if not gate.is_test_path(_J1_PKG_TEST):
        pytest.fail(u"前提不成立:is_test_path(%r) 不是 True" % _J1_PKG_TEST)
    if gate.test_candidates(_J1_PKG_IMPL, gate.R3_DART) != [_J1_PKG_TEST]:
        pytest.fail(u"前提不成立:test_candidates(%r) = %r"
                    % (_J1_PKG_IMPL, gate.test_candidates(_J1_PKG_IMPL, gate.R3_DART)))
    root = _repo(tmp_path, [(_J1_PKG_TEST, u"void main() {}\n")])
    calls, blocked = _isolate_outside_tmp(mod, monkeypatch, tmp_path)
    _j1_premise(mod, tmp_path, calls, blocked)
    runner = _dart_runner(_dart_sample([(_J1_PKG_TEST, [("foo returns 1", "failure")])]))
    try:
        res = mod.run(str(root), [given], runner=runner)
    except Exception as e:
        pytest.fail(u"run() 丟出未接住的例外:%r" % (e,))
    assert res["aborted"] is True, res
    assert u"冒號" in res.get("reason", ""), res
    assert runner.calls == [], runner.calls
    assert _ledger(root) == []
    assert blocked == [], blocked
    assert calls == [], calls
