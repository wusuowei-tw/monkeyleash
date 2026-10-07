# -*- coding: utf-8 -*-
"""票 05 — 紅燈紀錄的形狀。

只測寫出來的紀錄長什麼樣(直接呼叫寫入函式)。
「掛在測試執行器上會不會被觸發」不在這裡驗 —— 那需要另起行程跑一次測試,慢且脆;
改由安裝時的驗證腳本實際跑一次確認紀錄有長出來(可攜化票的產物)。

時序判準不用任何時間戳:要問的不是「檔案何時出現」,而是
「紅燈發生時,這個實作存不存在」—— 那件事在紅燈那一刻可以直接觀測。
"""

import importlib.util
import io
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "redlight_under_test", ROOT / ".claude" / "hooks" / "redlight.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


redlight = _load()


@pytest.fixture
def log(tmp_path, monkeypatch):
    p = tmp_path / "test-runs.jsonl"
    monkeypatch.setattr(redlight, "RUN_LOG", str(p))
    return p


def _records(p):
    return [json.loads(l) for l in io.open(p, encoding="utf-8") if l.strip()]


def test_a_run_produces_one_record_per_test_file(log, tmp_path, monkeypatch):
    monkeypatch.setattr(redlight, "ROOT", str(tmp_path))
    redlight.record_run("tests/test_thing.py", passed=False,
                        failed_tests=["test_a", "test_b"])
    recs = _records(log)
    assert len(recs) == 1
    assert recs[0]["test_file"] == "tests/test_thing.py"


def test_record_carries_result_and_failing_test_names(log, tmp_path, monkeypatch):
    monkeypatch.setattr(redlight, "ROOT", str(tmp_path))
    redlight.record_run("tests/test_thing.py", passed=False, failed_tests=["test_a"])
    rec = _records(log)[0]
    assert rec["result"] == "red"
    assert rec["failed_tests"] == ["test_a"]
    assert rec["time"], "沒有時間欄"


def test_record_states_whether_the_implementation_existed_at_that_moment(
        log, tmp_path, monkeypatch):
    """關鍵欄位:紅燈發生時實作存不存在。這是在事件當下留下的事實,不是事後推斷。"""
    monkeypatch.setattr(redlight, "ROOT", str(tmp_path))
    redlight.record_run("tests/test_thing.py", passed=False, failed_tests=["test_a"])
    rec = _records(log)[0]
    assert rec["impl_exists"] is False
    assert rec["impl_hash"] is None

    (tmp_path / "thing.py").write_text("x = 1", encoding="utf-8")
    redlight.record_run("tests/test_thing.py", passed=True, failed_tests=[])
    rec2 = _records(log)[1]
    assert rec2["impl_exists"] is True
    assert rec2["impl_hash"], "實作存在卻沒記雜湊,無法辨識還原式作弊"


def test_the_log_is_append_only(log, tmp_path, monkeypatch):
    """覆寫會讓歷史消失,而斷言需要歷史。"""
    monkeypatch.setattr(redlight, "ROOT", str(tmp_path))
    redlight.record_run("tests/test_a.py", passed=False, failed_tests=["x"])
    redlight.record_run("tests/test_b.py", passed=True, failed_tests=[])
    redlight.record_run("tests/test_a.py", passed=True, failed_tests=[])
    assert len(_records(log)) == 3


def test_the_log_lives_with_the_evidence_not_the_cache(tmp_path):
    """紀錄消失即失去判定依據 → 它是證據,放 .dev/,進版控。"""
    assert "/.dev/" in redlight.RUN_LOG.replace("\\", "/")


def test_implementation_path_is_derived_from_the_test_file_name(tmp_path, monkeypatch):
    """tests/test_foo.py 對應的實作是 foo.py —— 與 R3 找測試檔的規則互為反向。"""
    monkeypatch.setattr(redlight, "ROOT", str(tmp_path))
    (tmp_path / "macro_audit").mkdir()
    (tmp_path / "macro_audit" / "foo.py").write_text("x = 1", encoding="utf-8")
    found = redlight.find_implementation("tests/test_foo.py")
    assert found and found.endswith("foo.py")


class TestTheRecordCarriesTheTicketItBelongsTo:
    """紅燈屬於**某一張票**,不是屬於某個檔案。

    少了這個欄位,「impl_hash 對得上改動前的碼」單獨用會把 R3 的方向
    從「永遠不合格」翻成「永遠合格」:一筆三個月前的紅燈,只要該檔案
    自那次之後沒被提交過,就永久解鎖後續每一次修改。每張票要有自己的紅燈。
    """

    def _pipeline(self, root, **kw):
        (root / ".dev").mkdir(exist_ok=True)
        io.open(root / ".dev" / "pipeline.json", "w", encoding="utf-8").write(
            json.dumps(kw, ensure_ascii=False))

    def test_the_record_states_the_ticket_that_was_current(
            self, log, tmp_path, monkeypatch):
        monkeypatch.setattr(redlight, "ROOT", str(tmp_path))
        monkeypatch.setattr(redlight, "PIPELINE",
                            str(tmp_path / ".dev" / "pipeline.json"))
        self._pipeline(tmp_path, current_stage="implement", ticket_id="07")
        rec = redlight.record_run("tests/test_thing.py", passed=False,
                                  failed_tests=["test_a"])
        assert rec["ticket_id"] == "07"

    def test_an_unreadable_pipeline_records_no_ticket_rather_than_guessing(
            self, log, tmp_path, monkeypatch):
        """讀不到就是 None。**猜一個票號比沒有票號危險** ——
        猜中的那次會靜默解鎖一個沒有紅燈的修改。"""
        monkeypatch.setattr(redlight, "ROOT", str(tmp_path))
        monkeypatch.setattr(redlight, "PIPELINE", str(tmp_path / "nope.json"))
        rec = redlight.record_run("tests/test_thing.py", passed=False,
                                  failed_tests=["test_a"])
        assert rec["ticket_id"] is None


class TestTheHashDoesNotDependOnLineEndings:
    """hash 要拿來跟 **git blob** 比對,而工作樹與 blob 的行尾可能不同。

    本 repo 目前靠 `.gitattributes` 的 `*.py text eol=lf` 讓兩者位元組相同 ——
    但那個檔案**不在 portable-manifest 裡**,裝到別的 repo 不保證跟著走。
    在 `core.autocrlf=true` 的 Windows 上,少了它工作樹是 CRLF、blob 是 LF,
    兩邊 hash 永遠對不上,於是 R3 對每一支既有檔案無條件擋 ——
    fail-closed 的方向,但擋的是做對事的人。判準不該掛在一個沒被宣告帶走的檔案上。
    """

    def test_crlf_and_lf_content_hash_the_same(self):
        assert (redlight.content_hash(b"def f():\r\n    return 1\r\n")
                == redlight.content_hash(b"def f():\n    return 1\n"))

    def test_a_real_difference_still_changes_the_hash(self):
        """正規化不得把不同的內容抹成相同 —— 那會讓 hash 停止做事。"""
        assert (redlight.content_hash(b"return 1\n")
                != redlight.content_hash(b"return 2\n"))

    def test_the_recorded_hash_goes_through_the_same_function(
            self, log, tmp_path, monkeypatch):
        """紀錄端與判定端必須是同一個函式 —— 兩份實作就是 F-058 的形狀。"""
        monkeypatch.setattr(redlight, "ROOT", str(tmp_path))
        monkeypatch.setattr(redlight, "PIPELINE", str(tmp_path / "nope.json"))
        (tmp_path / "pkg").mkdir()
        raw = b"def f():\r\n    return 1\r\n"
        io.open(tmp_path / "pkg" / "thing.py", "wb").write(raw)
        rec = redlight.record_run("tests/test_thing.py", passed=False,
                                  failed_tests=["a"])
        assert rec["impl_hash"] == redlight.content_hash(raw)


class TestTheRecorderCannotKillTheRunner:
    """紀錄器崩潰比 fail-open 更糟:它讓整個測試執行器停擺(INTERNALERROR),
    連綠燈都跑不完 —— 而 R3 的判定完全建立在「測試真的跑過」上面。

    實際發生過:外掛拿 report.fspath 去 relative_to(ROOT),遇到會 chdir 到
    暫存目錄的測試就 ValueError,整個 session 當場中止。
    正確的來源是 nodeid —— 它本來就帶著相對 rootdir 的路徑,不必事後重建。
    """

    @staticmethod
    def _conftest():
        spec = importlib.util.spec_from_file_location(
            "conftest_under_test", ROOT / "tests" / "conftest.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    class _Report:
        when = "call"
        failed = True

        def __init__(self, nodeid, fspath):
            self.nodeid = nodeid
            self.fspath = fspath

    def test_a_test_that_changed_directory_does_not_crash_the_recorder(self):
        c = self._conftest()
        c._outcomes.clear()
        r = self._Report("tests/test_thing.py::test_x",
                         "/somewhere/completely/else/tests/test_thing.py")
        c.pytest_runtest_logreport(r)          # 不得拋例外
        assert "tests/test_thing.py" in c._outcomes, \
            "紀錄鍵值應取自 nodeid,實得:%s" % list(c._outcomes)

    def test_a_collection_error_is_recorded_as_red(self):
        """**新模組的第一次紅燈幾乎都是收集錯誤** —— 實作還不存在,import 就掛了。

        只吃 when=="call" 的話這種紅燈完全不會產生紀錄,
        於是 R3 的後半對每一個新模組都不可能誠實滿足,規則只剩繞過一條路。
        實際撞到:可攜化票 01 寫完 tests/test_manifest.py 跑出 collection error,
        紀錄零筆,R3 當場擋死。
        """
        c = self._conftest()
        c._outcomes.clear()

        class _CollectReport:
            failed = True
            nodeid = "tests/test_manifest.py"

        c.pytest_collectreport(_CollectReport())
        assert "tests/test_manifest.py" in c._outcomes
        assert c._outcomes["tests/test_manifest.py"]["failed"], "收集錯誤沒被記成紅燈"

    def test_a_setup_failure_counts_as_red(self):
        """fixture 拋例外只產生 setup 報告。不算的話,一次不綠的執行會被記成綠。"""
        c = self._conftest()
        c._outcomes.clear()
        r = self._Report("tests/test_thing.py::test_x", "tests/test_thing.py")
        r.when = "setup"
        c.pytest_runtest_logreport(r)
        assert c._outcomes.get("tests/test_thing.py", {}).get("failed"), \
            "setup 失敗沒被記成紅燈"


# ─────────────────────────────────────────────────────────────────────────────
# 票 145(M1-a)Station 3 紅燈 —— run 事實(producer 側)
#
# 觀察契約:docs/audits/2026-10-02-m1a-station3-redlight-plan.md 一、A,
# 經票 145〈十三〉裁決修正。
#
# **新介面(`load_runs` / `run_state`)只在測試函式內部取用**,不在模組層 ——
# 它們不存在時只有這幾支失敗,不會讓整個檔收集錯誤、拖垮上面既有的測試。
#
# **隔離**:conftest 模組載入時會自己載一份 redlight.py,而那一份的 RUN_LOG
# 指向真實帳本(`tests/conftest.py:129-133`)。驅動前一律把 conftest 的
# `_redlight` 換成本檔這一份、並把路徑指到 tmp —— 少一個,假紀錄就會寫進真實帳本。
# ─────────────────────────────────────────────────────────────────────────────


class _Item:
    def __init__(self, nodeid):
        self.nodeid = nodeid


class _CollectRep:
    def __init__(self, nodeid, failed=False):
        self.nodeid = nodeid
        self.failed = failed
        self.passed = not failed
        self.outcome = "failed" if failed else "passed"


class _RunRep:
    def __init__(self, nodeid, when, outcome):
        self.nodeid = nodeid
        self.fspath = nodeid.split("::", 1)[0]
        self.when = when
        self.outcome = outcome
        self.passed = outcome == "passed"
        self.failed = outcome == "failed"
        self.skipped = outcome == "skipped"


def _reports_for(nodeid, outcome):
    """一條測試在 pytest 裡實際產生的 report 序列。

    passed / failed:setup → call → teardown;skipped:setup(skipped)→ teardown,
    **沒有 call**(skip 在 setup 階段就決定了)。
    """
    if outcome == "skipped":
        return [_RunRep(nodeid, "setup", "skipped"),
                _RunRep(nodeid, "teardown", "passed")]
    return [_RunRep(nodeid, "setup", "passed"),
            _RunRep(nodeid, "call", outcome),
            _RunRep(nodeid, "teardown", "passed")]


class _Session:
    def __init__(self, items):
        self.items = list(items)
        self.testscollected = len(self.items)


# 票 145 Station 4g 授權 G3(〈四十八〉48.1 第 5 點;規劃檔 S3g-0 P2-B):driver 把 conftest 所見的版本事實
# 固定在能力邊界內,正控不再依賴執行它的直譯器 / pytest 版本。模組載入當下的真實版本記在這裡 ——
# 測試在呼叫 driver **之前**自己設過 `pytest.__version__`(例:測「版本不在清單」的那支)時不覆蓋它。
_REAL_PYTEST_VERSION = pytest.__version__
_PINNED_PYTEST_VERSION = "9.1.1"
_PINNED_PYTHON = (3, 11, 0, "final", 0)


def _isolated_conftest(monkeypatch, tmp_path):
    c = TestTheRecorderCannotKillTheRunner._conftest()
    monkeypatch.setattr(redlight, "ROOT", str(tmp_path))
    monkeypatch.setattr(redlight, "RUN_LOG",
                        str(tmp_path / ".dev" / "test-runs.jsonl"))
    monkeypatch.setattr(redlight, "PIPELINE",
                        str(tmp_path / ".dev" / "pipeline.json"))
    monkeypatch.setattr(c, "_redlight", redlight)
    monkeypatch.setattr(c, "_ROOT", tmp_path)
    monkeypatch.setattr(c, "sys", _e_sys(optimize=_e_real_sys.flags.optimize,
                                         version_info=_EVersion(*_PINNED_PYTHON)), raising=False)
    if pytest.__version__ == _REAL_PYTEST_VERSION:
        monkeypatch.setattr(pytest, "__version__", _PINNED_PYTEST_VERSION)
    c._outcomes.clear()
    return c


def _drive_session(c, collect_files=(), collect_errors=(), selected=(),
                   deselected=(), outcomes=None, exitstatus=0):
    """依 pytest 的實際呼叫順序,對 conftest 呼叫**標準 hook 名稱**。

    conftest 沒實作的 hook 以 no-op 跳過 —— 測試不依賴 producer 用了哪幾個 hook
    (那是 Station 4 的實體決定)。
    """
    def hook(name):
        return getattr(c, name, None) or (lambda *a, **k: None)

    for f in collect_files:
        hook("pytest_collectreport")(_CollectRep(f))
    for f in collect_errors:
        hook("pytest_collectreport")(_CollectRep(f, failed=True))
    items = [_Item(n) for n in selected]
    gone = [_Item(n) for n in deselected]
    if gone:
        hook("pytest_deselected")(gone)
    session = _Session(items)
    hook("pytest_collection_finish")(session)
    for nodeid, outcome in (outcomes or {}).items():
        for rep in _reports_for(nodeid, outcome):
            hook("pytest_runtest_logreport")(rep)
    hook("pytest_sessionfinish")(session, exitstatus)


class TestRunFacts:

    def test_a_full_pass_is_state_a_with_coverage_visible(self, tmp_path, monkeypatch):
        """RL-1 Full pass。現行 HEAD:**介面紅**(`redlight.load_runs` 不存在)。"""
        c = _isolated_conftest(monkeypatch, tmp_path)
        ids = ["tests/test_thing.py::test_a", "tests/test_thing.py::test_b"]
        _drive_session(c, collect_files=["tests/test_thing.py"], selected=ids,
                       outcomes={ids[0]: "passed", ids[1]: "passed"}, exitstatus=0)
        runs = redlight.load_runs(str(tmp_path))
        assert len(runs) == 1, runs
        assert redlight.run_state(runs[0]) == "A", runs[0]
        assert sorted(runs[0]["collected"]) == sorted(ids), runs[0]
        assert list(runs[0]["deselected"]) == [], runs[0]

    def test_one_failure_is_state_b_and_names_the_test(self, tmp_path, monkeypatch):
        """RL-2 One failure。現行 HEAD:**介面紅**(`redlight.load_runs` 不存在)。"""
        c = _isolated_conftest(monkeypatch, tmp_path)
        ids = ["tests/test_thing.py::test_a", "tests/test_thing.py::test_b"]
        _drive_session(c, collect_files=["tests/test_thing.py"], selected=ids,
                       outcomes={ids[0]: "passed", ids[1]: "failed"}, exitstatus=1)
        runs = redlight.load_runs(str(tmp_path))
        assert len(runs) == 1, runs
        assert redlight.run_state(runs[0]) == "B", runs[0]
        assert runs[0]["outcomes"][ids[1]] == "failed", runs[0]

    def test_zero_collected_is_state_c_and_the_run_is_visible(self, tmp_path, monkeypatch):
        """RL-3 Zero tests collected。現行 HEAD:**介面紅**(`redlight.load_runs` 不存在)。

        底層行為缺口:HEAD 對此情形一筆都不寫(`conftest.py:171-172` 迴圈 0 次),
        與「根本沒跑」不可分 —— 修後必須留下一筆 run 事實。
        """
        c = _isolated_conftest(monkeypatch, tmp_path)
        _drive_session(c, exitstatus=5)
        runs = redlight.load_runs(str(tmp_path))
        assert len(runs) == 1, u"0 collected 的 run 沒有留下事實,與 E 不可分:%r" % runs
        assert redlight.run_state(runs[0]) == "C", runs[0]

    def test_a_collection_error_is_state_d(self, tmp_path, monkeypatch):
        """RL-4(a) Collection failure。現行 HEAD:**介面紅**(`redlight.load_runs` 不存在)。"""
        c = _isolated_conftest(monkeypatch, tmp_path)
        _drive_session(c, collect_errors=["tests/test_broken.py"], exitstatus=2)
        runs = redlight.load_runs(str(tmp_path))
        assert len(runs) == 1, runs
        assert redlight.run_state(runs[0]) == "D", runs[0]

    def test_a_usage_error_is_state_d_not_green(self, tmp_path, monkeypatch):
        """RL-4(b) Runner invocation error。現行 HEAD:**介面紅**(`redlight.load_runs` 不存在)。

        producer 本身沒被載入的子情形不在這裡 —— 那是 ODC-3(見 tests/test_status.py)。
        """
        c = _isolated_conftest(monkeypatch, tmp_path)
        _drive_session(c, exitstatus=4)
        runs = redlight.load_runs(str(tmp_path))
        assert len(runs) == 1, runs
        assert redlight.run_state(runs[0]) == "D", runs[0]

    def test_an_interrupted_run_is_state_d_even_with_passes(self, tmp_path, monkeypatch):
        """RL-4(c) 執行被中斷。現行 HEAD:**介面紅**(`redlight.load_runs` 不存在)。

        中斷前已有一條通過 —— 那不得讓這個 run 變成 A。
        """
        c = _isolated_conftest(monkeypatch, tmp_path)
        ids = ["tests/test_thing.py::test_a", "tests/test_thing.py::test_b"]
        _drive_session(c, collect_files=["tests/test_thing.py"], selected=ids,
                       outcomes={ids[0]: "passed"}, exitstatus=2)
        runs = redlight.load_runs(str(tmp_path))
        assert len(runs) == 1, runs
        assert redlight.run_state(runs[0]) == "D", runs[0]

    def test_three_skipped_645_deselected_is_state_f_with_counts(self, tmp_path, monkeypatch):
        """RL-6' 票 139 現場重現(producer 側)。現行 HEAD:**介面紅**(`redlight.load_runs` 不存在)。

        `-k "symlink"` 的形狀:選到 3 條、全部 skip,645 條 deselected,0 passed、0 failed。
        """
        c = _isolated_conftest(monkeypatch, tmp_path)
        chosen = ["tests/test_gate.py::test_symlink_%d" % i for i in range(3)]
        gone = ["tests/test_gate.py::test_other_%d" % i for i in range(645)]
        _drive_session(c, collect_files=["tests/test_gate.py"], selected=chosen,
                       deselected=gone,
                       outcomes={n: "skipped" for n in chosen}, exitstatus=0)
        runs = redlight.load_runs(str(tmp_path))
        assert len(runs) == 1, runs
        run = runs[0]
        assert redlight.run_state(run) == "F", run
        assert len(run["deselected"]) == 645, len(run["deselected"])
        assert [v for v in run["outcomes"].values()].count("skipped") == 3, run["outcomes"]
        assert "passed" not in run["outcomes"].values(), run["outcomes"]


# ─────────────────────────────────────────────────────────────────────────────
# 票 145 Station 3b 紅燈 —— coverage authority(F3)與 session schema(F1)
#
# 依據:票 145〈十七〉裁決 1(full_file_coverage ∈ {true, false, unknown},
# 只有 producer 能正向證明整檔涵蓋時才為 true)、裁決 3(schema fail-closed)。
#
# **新介面 `redlight.file_coverage(run, test_file)` 只在測試函式內部取用。**
# producer 以 pytest 實際的位置參數(`session.config.args`)判斷窄選;
# 這裡以帶 `config` 的假 session 模擬 —— 屬性照真實 pytest 的名字給
# (`args`、`rootpath`、`invocation_params.dir`、`option.pyargs`、`getoption`)。
# ─────────────────────────────────────────────────────────────────────────────


class _InvocationParams:
    def __init__(self, d):
        self.dir = d


class _Option:
    pyargs = False


class _Config:
    def __init__(self, args, root):
        self.args = list(args)
        self.rootpath = root
        self.invocation_params = _InvocationParams(root)
        self.option = _Option()

    def getoption(self, name, default=None):
        return getattr(self.option, name, default)


class _SessionWithConfig(_Session):
    def __init__(self, items, args, root, with_config=True):
        _Session.__init__(self, items)
        if with_config:
            self.config = _Config(args, root)


def _reset_conftest_state(c):
    """每次驅動前把 conftest 模組的累積狀態歸零(避免案例互相污染)。"""
    c._outcomes.clear()
    run = getattr(c, "_run", None)
    if isinstance(run, dict):
        for k, v in list(run.items()):
            if hasattr(v, "clear"):
                v.clear()
            else:
                run[k] = None


def _drive_with_args(c, root, args, selected=(), deselected=(), outcomes=None,
                     exitstatus=0, with_config=True):
    """同 `_drive_session`,但 session 帶 `config.args`(pytest 實際收到的位置參數)。"""
    def hook(name):
        return getattr(c, name, None) or (lambda *a, **k: None)

    _reset_conftest_state(c)
    files = sorted(set(n.split("::", 1)[0] for n in list(selected) + list(deselected)))
    for f in files:
        hook("pytest_collectreport")(_CollectRep(f))
    gone = [_Item(n) for n in deselected]
    if gone:
        hook("pytest_deselected")(gone)
    session = _SessionWithConfig([_Item(n) for n in selected], args, root,
                                 with_config=with_config)
    hook("pytest_collection_finish")(session)
    for nodeid, outcome in (outcomes or {}).items():
        for rep in _reports_for(nodeid, outcome):
            hook("pytest_runtest_logreport")(rep)
    hook("pytest_sessionfinish")(session, exitstatus)


X_A = "tests/test_x.py::test_a"
X_B = "tests/test_x.py::test_b"


class TestFileCoverage:

    def _coverage_after(self, tmp_path, monkeypatch, args, selected, deselected=(),
                        with_config=True):
        c = _isolated_conftest(monkeypatch, tmp_path)
        _drive_with_args(c, tmp_path, args, selected=selected, deselected=deselected,
                         outcomes={n: "passed" for n in selected}, exitstatus=0,
                         with_config=with_config)
        runs = redlight.load_runs(str(tmp_path))
        assert len(runs) == 1, runs
        return redlight.file_coverage(runs[0], "tests/test_x.py")

    def test_b1a_a_nodeid_argument_is_not_full_coverage(self, tmp_path, monkeypatch):
        """B1a(F3 producer)。分類:interface-red(`redlight.file_coverage` 不存在)。

        位置參數 `tests/test_x.py::test_a` —— 以 nodeid 指名,未收集的身分不產生 deselected。
        """
        got = self._coverage_after(tmp_path, monkeypatch, [X_A], [X_A])
        assert got == "false", got

    def test_b1b_a_backslash_nodeid_argument_is_not_full_coverage(self, tmp_path, monkeypatch):
        """B1b(F3 producer)。分類:interface-red(`redlight.file_coverage` 不存在)。

        位置參數 `tests\\test_x.py::test_a`(Windows 反斜線)—— 仍是 nodeid 指名。
        """
        got = self._coverage_after(tmp_path, monkeypatch, ["tests\\test_x.py::test_a"], [X_A])
        assert got == "false", got

    def test_b1c_a_file_argument_without_deselection_is_full_coverage(self, tmp_path, monkeypatch):
        """B1c(F3 producer)。分類:interface-red(`redlight.file_coverage` 不存在)。

        位置參數 `tests/test_x.py`(不含 `::`)、無 deselected ⇒ 整檔涵蓋。
        """
        c = _isolated_conftest(monkeypatch, tmp_path)
        _c_call_collect_wrapper(c, _c_file(tmp_path, "tests/test_x.py"),
                                _CCollectReport("tests/test_x.py", [_c_item(X_A), _c_item(X_B)]))
        _d_committed_root(tmp_path)
        session = _CompletenessSession([_c_item(X_A), _c_item(X_B)],
                                       _CConfig(tmp_path, _d_option(), _d_plugins(c, tmp_path),
                                                args=["tests/test_x.py"]))
        session.config.inipath = tmp_path / "pyproject.toml"
        _drive_with_session(c, session, selected=[X_A, X_B],
                            outcomes={X_A: "passed", X_B: "passed"}, exitstatus=0)
        got = redlight.file_coverage(redlight.load_runs(str(tmp_path))[0], "tests/test_x.py")
        assert got == "true", got

    def test_b1d_a_parent_directory_argument_is_full_coverage(self, tmp_path, monkeypatch):
        """B1d(F3 producer)。分類:interface-red(`redlight.file_coverage` 不存在)。

        位置參數 `tests`(上層目錄)、無 deselected ⇒ 整檔涵蓋。
        """
        c = _isolated_conftest(monkeypatch, tmp_path)
        _c_call_collect_wrapper(c, _c_file(tmp_path, "tests/test_x.py"),
                                _CCollectReport("tests/test_x.py", [_c_item(X_A), _c_item(X_B)]))
        _d_committed_root(tmp_path)
        session = _CompletenessSession([_c_item(X_A), _c_item(X_B)],
                                       _CConfig(tmp_path, _d_option(), _d_plugins(c, tmp_path),
                                                args=["tests"]))
        session.config.inipath = tmp_path / "pyproject.toml"
        _drive_with_session(c, session, selected=[X_A, X_B],
                            outcomes={X_A: "passed", X_B: "passed"}, exitstatus=0)
        got = redlight.file_coverage(redlight.load_runs(str(tmp_path))[0], "tests/test_x.py")
        assert got == "true", got

    def test_b1e_a_file_argument_with_deselection_is_not_full_coverage(self, tmp_path, monkeypatch):
        """B1e(F3 producer)。分類:interface-red(`redlight.file_coverage` 不存在)。

        位置參數 `tests/test_x.py`,但該檔有 deselected(`-k` 之類)⇒ 不是整檔涵蓋。
        """
        got = self._coverage_after(tmp_path, monkeypatch, ["tests/test_x.py"], [X_A],
                                   deselected=[X_B])
        assert got == "false", got

    def test_b1f_no_config_means_unknown(self, tmp_path, monkeypatch):
        """B1f(F3 producer)。分類:interface-red(`redlight.file_coverage` 不存在)。

        假 session 沒有 config / args ⇒ 證明不了整檔涵蓋 ⇒ unknown(不知道,就不是完整)。
        """
        got = self._coverage_after(tmp_path, monkeypatch, [], [X_A, X_B], with_config=False)
        assert got == "unknown", got

    def test_b1g_an_argument_outside_the_root_means_unknown(self, tmp_path, monkeypatch):
        """B1g(F3 producer)。分類:interface-red(`redlight.file_coverage` 不存在)。

        位置參數是 root 之外的絕對路徑 —— 無法判讀它與 `tests/test_x.py` 的關係 ⇒ unknown。
        """
        outside = str(tmp_path.parent / "elsewhere" / "test_x.py")
        got = self._coverage_after(tmp_path, monkeypatch, [outside], [X_A, X_B])
        assert got == "unknown", got


class TestRunStateSchema:

    def test_b6_a_session_without_collected_is_not_state_c(self):
        """B6(F1 缺欄)。分類:behavior-red。

        session 缺 `collected` 欄位 —— 那不是「0 collected」,是證據不完整;
        不得被判成 C(〈十七〉裁決 3:不得以「缺欄 ⇒ 空集合」處理)。
        """
        run = {"kind": "session", "run_id": "b6", "time": "2999-01-01T00:00:00+00:00",
               "ticket_id": "99", "exit_code": 0, "deselected": [], "outcomes": {}}
        assert redlight.run_state(run) != "C", run


# ─────────────────────────────────────────────────────────────────────────────
# 票 145 Station 3b 補件 —— B10:固定指令(無使用者位置參數)的整檔涵蓋
#
# 假 session 的 `config` 依本機 pytest 9.1.1 原始碼與本 repo 設定**靜態推導**:
#   - `_pytest/config/__init__.py:1411-1438` `_decide_args()`:未給位置參數、且
#     invocation dir == rootpath ⇒ `source = ArgsSource.TESTPATHS`,
#     `result` = testpaths 各項經 `glob.iglob(path, recursive=True)` 展開後排序;
#   - `pyproject.toml:71` `testpaths = ["tests"]` ⇒ `config.args == ["tests"]`;
#   - rootdir 由 repo 根的 `pyproject.toml`(含 `[tool.pytest.ini_options]`)決定
#     (`_pytest/config/findpaths.py:313-315`)⇒ 從 repo 根執行時 invocation dir == rootpath。
# 這是推導,不是實際執行時觀察到的值。
# ─────────────────────────────────────────────────────────────────────────────


def _drive_with_session(c, session, selected=(), deselected=(), outcomes=None, exitstatus=0):
    """同 `_drive_with_args`,但 session 由呼叫端建構(以便帶 `args_source`)。"""
    def hook(name):
        return getattr(c, name, None) or (lambda *a, **k: None)

    _reset_conftest_state(c)
    files = sorted(set(n.split("::", 1)[0] for n in list(selected) + list(deselected)))
    for f in files:
        hook("pytest_collectreport")(_CollectRep(f))
    gone = [_Item(n) for n in deselected]
    if gone:
        hook("pytest_deselected")(gone)
    hook("pytest_collection_finish")(session)
    for nodeid, outcome in (outcomes or {}).items():
        for rep in _reports_for(nodeid, outcome):
            hook("pytest_runtest_logreport")(rep)
    hook("pytest_sessionfinish")(session, exitstatus)


class TestFixedCommandCoverage:

    def test_b10_the_fixed_command_without_positional_args_is_full_coverage(
            self, tmp_path, monkeypatch):
        """B10(F3;〈十七〉3b 補件)。分類:interface-red(`redlight.file_coverage` 不存在)。

        固定指令 `python -X utf8 -m pytest -q` 沒有使用者位置參數 —— pytest 以 testpaths
        補上 `config.args == ["tests"]`、`args_source == TESTPATHS`(靜態推導,見上方註解)。
        tests/test_x.py 被正常收集、無 deselected ⇒ full_file_coverage 必須為 "true";
        否則固定全套永遠無法退紅。
        """
        c = _isolated_conftest(monkeypatch, tmp_path)
        session = _SessionWithConfig([_Item(X_A), _Item(X_B)], ["tests"], tmp_path)
        session.config.args_source = pytest.Config.ArgsSource.TESTPATHS
        session.config.option = _d_option()
        session.config.pluginmanager = _d_plugins(c, tmp_path)
        session.config.inipath = tmp_path / "pyproject.toml"
        _d_committed_root(tmp_path)
        session.shouldstop = False
        session.shouldfail = False
        _c_call_collect_wrapper(c, _c_file(tmp_path, "tests/test_x.py"),
                                _CCollectReport("tests/test_x.py", [_c_item(X_A), _c_item(X_B)]))
        _drive_with_session(c, session, selected=[X_A, X_B],
                            outcomes={X_A: "passed", X_B: "passed"}, exitstatus=0)
        runs = redlight.load_runs(str(tmp_path))
        assert len(runs) == 1, runs
        got = redlight.file_coverage(runs[0], "tests/test_x.py")
        assert got == "true", got


# ─────────────────────────────────────────────────────────────────────────────
# 票 145 Station 3c 紅燈 —— 選擇 / 執行完整性與 plugin 邊界(〈二十三〉)
#
# 合約:票 145〈二十三〉7 —— session 新增 `completeness`(options / cacheprovider_blocked /
# shouldstop / shouldfail / pre_narrowing / plugins),`file_coverage == "true"` 多七條必要條件。
# 規劃:docs/audits/2026-10-02-m1a-station3c-redlight-plan.md P4。
#
# **假物件盡量是 pytest 的真型別**:item 是 `pytest.Item` 子類、collector 是 `pytest.File`
# 子類(以 `object.__new__` 建立、不經 `from_parent`),producer 用 isinstance 判斷時也成立。
# **driver 依 pytest 9.1.1 的呼叫順序**:每個檔先對 conftest 的
# `pytest_make_collect_report`(new-style `wrapper=True`;〈二十三〉2(a))送出**完整**結果,
# wrapper 返回後才**就地**縮小 `report.result`(模擬外層 `LFPluginCollWrapper`,
# `_pytest/cacheprovider.py:282`)—— producer 若沒有當下複製 nodeid,會看到縮小後的內容。
# 之後才是 `pytest_collectreport`(縮小後)、`pytest_deselected`、`pytest_collection_finish`、
# 逐身分的 runtest report、session 結束時的 `shouldstop` / `shouldfail`、`pytest_sessionfinish`。
# 全部寫在 tmp root,不碰真實帳本(`_isolated_conftest`)。
# ─────────────────────────────────────────────────────────────────────────────

import inspect as _c_inspect
import os as _c_os
import types as _c_types


class _CItem(pytest.Item):
    """真的 `pytest.Item` 子類;只帶 nodeid。"""

    def runtest(self):
        pass


class _CFile(pytest.File):
    """真的 `pytest.File` 子類;只帶 nodeid / path。"""

    def collect(self):
        return []


def _c_item(nodeid):
    it = object.__new__(_CItem)
    it._nodeid = nodeid
    it.name = nodeid.split("::")[-1]
    return it


def _c_file(root, path):
    f = object.__new__(_CFile)
    f._nodeid = path
    f.name = path.split("/")[-1]
    f.path = pathlib.Path(str(root)) / path
    return f


class _CCollectReport:
    def __init__(self, nodeid, result, failed=False):
        self.nodeid = nodeid
        self.result = list(result)
        self.failed = failed
        self.passed = not failed
        self.skipped = False
        self.outcome = "failed" if failed else "passed"


class _CRunReport:
    def __init__(self, nodeid, when, outcome, wasxfail=None):
        self.nodeid = nodeid
        self.fspath = nodeid.split("::", 1)[0]
        self.when = when
        self.outcome = outcome
        self.passed = outcome == "passed"
        self.failed = outcome == "failed"
        self.skipped = outcome == "skipped"
        if wasxfail is not None:
            self.wasxfail = wasxfail


def _c_reports(nodeid, kind):
    """一個身分在 pytest 裡實際產生的 report 序列。

    - passed / failed:setup → call → teardown
    - skipped:setup(skipped)→ teardown,沒有 call
    - xfail:setup → call(skipped,帶 `wasxfail`)→ teardown —— 明確辨識的 xfail
    - setup_only:只有 setup(例:call 中 `pytest.exit()`,`_pytest/runner.py:262-267` 重拋,沒有 call / teardown report)
    - setup_teardown:setup → teardown,沒有 call(`--setup-only`,`_pytest/runner.py:134-139`)
    """
    if kind in ("passed", "failed"):
        return [_CRunReport(nodeid, "setup", "passed"),
                _CRunReport(nodeid, "call", kind),
                _CRunReport(nodeid, "teardown", "passed")]
    if kind == "skipped":
        return [_CRunReport(nodeid, "setup", "skipped"),
                _CRunReport(nodeid, "teardown", "passed")]
    if kind == "xfail":
        return [_CRunReport(nodeid, "setup", "passed"),
                _CRunReport(nodeid, "call", "skipped", wasxfail="reason"),
                _CRunReport(nodeid, "teardown", "passed")]
    if kind == "setup_only":
        return [_CRunReport(nodeid, "setup", "passed")]
    if kind == "setup_teardown":
        return [_CRunReport(nodeid, "setup", "passed"),
                _CRunReport(nodeid, "teardown", "passed")]
    raise ValueError(kind)


_C_OPTION_DEFAULTS = {
    "pyargs": False, "lf": False, "last_failed_no_failures": "all",
    "failedfirst": False, "newfirst": False, "stepwise": False, "stepwise_skip": False,
    "stepwise_reset": False, "maxfail": None, "collectonly": False, "setuponly": False,
    "setupplan": False, "setupshow": False, "keyword": "", "markexpr": "",
    "deselect": None, "ignore": None, "ignore_glob": None,
    "runxfail": False, "pythonwarnings": None, "trace": False,
    "usepdb": False,
}


class _COption:
    """`config.option`:預設值為「全部關閉」(`maxfail` 預設 None,〈二十三〉2(f))。

    `missing` 中的屬性不存在(例:`-p no:cacheprovider` 時沒有 `lf` / `stepwise`,〈二十三〉2(d))。
    """

    def __init__(self, missing=(), **overrides):
        values = dict(_C_OPTION_DEFAULTS)
        values.update(overrides)
        for k in missing:
            values.pop(k, None)
        self.__dict__.update(values)


class _CDist:
    def __init__(self, name):
        self.project_name = name
        self.version = "0"
        self.metadata = {"name": name}


class _FakePluginManager:
    """`config.pluginmanager` 的四個讀取點(`pluggy/_manager.py:235, 312, 422-429`)。"""

    def __init__(self, name_plugins, distinfo=(), blocked=()):
        self._name_plugins = list(name_plugins)
        self._distinfo = list(distinfo)
        self._blocked = set(blocked)

    def list_name_plugin(self):
        return list(self._name_plugins)

    def list_plugin_distinfo(self):
        return list(self._distinfo)

    def is_blocked(self, name):
        return name in self._blocked

    def get_plugin(self, name):
        return dict(self._name_plugins).get(name)

    def has_plugin(self, name):
        return self.get_plugin(name) is not None


def _c_internal(module, label):
    """類別定義在 `module` 的物件(模擬 `_pytest` 內部物件)。"""
    return type(label, (), {"__module__": module})()


def _c_plugins(c, root, extra=(), extra_dist=()):
    """白名單內的 plugin 集合 + `extra`。

    builtin:模組 `_pytest.main`、一個數字名稱(`str(id(...))`)而類別定義在 `_pytest.config` 的物件;
    root_conftest:`<root>/tests/conftest.py`(絕對路徑,與 pytest 的 conftest 註冊名稱同形)—— 就是 producer 本身;
    known_dist:`anyio.pytest_plugin`,在 `list_plugin_distinfo()` 中與 dist `anyio` 配對。
    """
    builtin_mod = _c_types.ModuleType("_pytest.main")
    internal = _c_internal("_pytest.config", "_InternalHelper")
    anyio_mod = _c_types.ModuleType("anyio.pytest_plugin")
    names = [("main", builtin_mod),
             (str(id(internal)), internal),
             (_c_os.path.join(str(root), "tests", "conftest.py"), c),
             ("anyio", anyio_mod)] + list(extra)
    dist = [(anyio_mod, _CDist("anyio"))] + list(extra_dist)
    return _FakePluginManager(names, dist)


class _CInvocationParams:
    def __init__(self, d):
        self.dir = d


class _CConfig:
    def __init__(self, root, option, pluginmanager, args=("tests",)):
        self.args = list(args)
        self.args_source = pytest.Config.ArgsSource.TESTPATHS
        self.rootpath = pathlib.Path(str(root))
        self.invocation_params = _CInvocationParams(pathlib.Path(str(root)))
        self.option = option
        self.pluginmanager = pluginmanager

    def getoption(self, name, default=None, skip=False):
        return getattr(self.option, name, default)


class _CompletenessSession:
    def __init__(self, items, config):
        self.items = list(items)
        self.testscollected = len(self.items)
        self.config = config
        self.shouldstop = False
        self.shouldfail = False


def _c_call_collect_wrapper(c, collector, report):
    """依 new-style wrapper 協定呼叫 conftest 的 `pytest_make_collect_report`(沒有就跳過)。"""
    fn = getattr(c, "pytest_make_collect_report", None)
    if fn is None:
        return
    gen = fn(collector)
    if not _c_inspect.isgenerator(gen):
        return
    next(gen)
    try:
        gen.send(report)
    except StopIteration:
        pass


def _c_drive(c, root, files, selected, outcomes=None, deselected=(), filtered_out=(),
             collect_errors=(), exitstatus=0, option=None, pm=None,
             shouldstop=False, shouldfail=False):
    """依 pytest 9.1.1 的呼叫順序驅動 conftest(見本段開頭註解)。

    `files`:{測試檔: 縮小前的完整 nodeid 清單};`filtered_out`:收集期被悄悄移除的身分
    (不發 deselected 通知)。
    """
    def hook(name):
        return getattr(c, name, None) or (lambda *a, **k: None)

    dropped = set(filtered_out)
    for path in sorted(files):
        report = _CCollectReport(path, [_c_item(n) for n in files[path]])
        _c_call_collect_wrapper(c, _c_file(root, path), report)
        report.result[:] = [x for x in report.result if x.nodeid not in dropped]
        hook("pytest_collectreport")(report)
    for path in collect_errors:
        hook("pytest_collectreport")(_CCollectReport(path, [], failed=True))
    gone = [_c_item(n) for n in deselected]
    if gone:
        hook("pytest_deselected")(gone)
    session = _CompletenessSession([_c_item(n) for n in selected],
                                   _CConfig(root, option or _COption(), pm))
    hook("pytest_collection_finish")(session)
    for nodeid, kind in (outcomes or {}).items():
        for rep in _c_reports(nodeid, kind):
            hook("pytest_runtest_logreport")(rep)
    session.shouldstop = shouldstop
    session.shouldfail = shouldfail
    hook("pytest_sessionfinish")(session, exitstatus)


_C_MISSING = object()

X_XF = "tests/test_x.py::test_xf"
W_A = "tests/test_w.py::test_w_a"


def _c_all_off(plugins=None):
    """一份「全部關閉、白名單內」的完整性事實(consumer 側用;欄位名稱依〈二十三〉7)。"""
    return {
        "options": {"lf": False, "last_failed_no_failures": "all", "stepwise": False,
                    "stepwise_skip": False, "maxfail": None, "collectonly": False,
                    "setuponly": False, "setupplan": False},
        "cacheprovider_blocked": False,
        "shouldstop": False,
        "shouldfail": False,
        "pre_narrowing": {"tests/test_x.py": [X_A, X_B]},
        "plugins": plugins if plugins is not None else [
            {"name": "main", "kind": "builtin"},
            {"name": "tests/conftest.py", "kind": "root_conftest"},
            {"name": "anyio", "kind": "known_dist"},
        ],
    }


def _c_raw_coverage(tmp_path, completeness=_C_MISSING):
    """手寫一筆 session(全收集、全 passed、args `tests`)到 tmp root,讀回後判 `tests/test_x.py`。

    除 `completeness` 外,形狀與 d122df4 的 producer 實際寫出的相同。
    """
    rec = {"kind": "session", "run_id": "c3-raw", "time": "2999-01-01T00:00:00+00:00",
           "ticket_id": "99", "exit_code": 0, "collected": [X_A, X_B], "deselected": [],
           "outcomes": {X_A: "passed", X_B: "passed"},
           "invocation": {"args": ["tests"], "args_source": "TESTPATHS", "pyargs": False}}
    if completeness is not _C_MISSING:
        rec["completeness"] = completeness
    path = redlight.session_log(str(tmp_path))
    _c_os.makedirs(_c_os.path.dirname(path), exist_ok=True)
    with io.open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    runs = redlight.load_runs(str(tmp_path))
    assert len(runs) == 1, runs
    return redlight.file_coverage(runs[0], "tests/test_x.py")


class TestCompletenessCoverage:

    def test_c3a_lf_silent_narrowing_is_not_full_coverage(self, tmp_path, monkeypatch):
        """C3a-1(〈二十三〉7 (ii)(v))。分類:behavior-red。

        `--lf`:縮小前全集 [X_A, X_B],收集期悄悄移除 X_A(沒有 deselected 通知),
        `session.items` 只剩 X_B 且 passed;`lfplugin-collskip` 已註冊(〈二十三〉2(e))。
        d122df4 上失敗的原因:`.claude/hooks/redlight.py:405-406` 只看 deselected,
        `:423-426` 位置參數 `tests` 為上層目錄 ⇒ `"true"`。
        """
        c = _isolated_conftest(monkeypatch, tmp_path)
        skip_marker = _c_internal("_pytest.cacheprovider", "LFPluginCollSkipfiles")
        wrapper = _c_internal("_pytest.cacheprovider", "LFPluginCollWrapper")
        pm = _c_plugins(c, tmp_path, extra=[("lfplugin-collwrapper", wrapper),
                                            ("lfplugin-collskip", skip_marker)])
        _c_drive(c, tmp_path, {"tests/test_x.py": [X_A, X_B]}, selected=[X_B],
                 outcomes={X_B: "passed"}, filtered_out=[X_A],
                 option=_COption(lf=True), pm=pm, exitstatus=0)
        runs = redlight.load_runs(str(tmp_path))
        assert len(runs) == 1, runs
        got = redlight.file_coverage(runs[0], "tests/test_x.py")
        assert got != "true", got

    def test_c3b_a_session_without_completeness_facts_is_not_full_coverage(self, tmp_path):
        """C3b-1(〈二十三〉7 (i))。分類:behavior-red。

        session 正好是 d122df4 的 producer 寫出的形狀,沒有 `completeness` ⇒ 不得為 `"true"`。
        d122df4 上失敗的原因:`.claude/hooks/redlight.py:407-426` 不讀任何完整性事實 ⇒ `"true"`。
        """
        got = _c_raw_coverage(tmp_path)
        assert got != "true", got

    def test_c3b_a_malformed_completeness_fact_is_not_full_coverage(self, tmp_path):
        """C3b-2(〈二十三〉7 (i))。分類:behavior-red。

        `completeness` 存在,其餘全部關閉,但 `shouldstop` 是字串 `"False"`(型別錯)⇒ 不得為 `"true"`。
        d122df4 上失敗的原因:`.claude/hooks/redlight.py:335-343` 不驗新欄位、`:407-426` 不讀它 ⇒ `"true"`。
        """
        comp = _c_all_off()
        comp["shouldstop"] = "False"
        got = _c_raw_coverage(tmp_path, comp)
        assert got != "true", got

    def test_c3c_an_exitfirst_run_is_not_full_coverage(self, tmp_path, monkeypatch):
        """C3c-1(〈二十三〉7 (iii)(iv)(vi))。分類:behavior-red。

        `-x`:`maxfail = 1`;W_A failed 後 `shouldfail` 設定、exit 1;X 全收集但沒有執行。
        d122df4 上失敗的原因:`.claude/hooks/redlight.py:423-426` 不讀 maxfail / shouldfail ⇒ X 為 `"true"`。
        """
        c = _isolated_conftest(monkeypatch, tmp_path)
        _c_drive(c, tmp_path, {"tests/test_w.py": [W_A], "tests/test_x.py": [X_A, X_B]},
                 selected=[W_A, X_A, X_B], outcomes={W_A: "failed"},
                 option=_COption(maxfail=1), pm=_c_plugins(c, tmp_path),
                 shouldfail="stopping after 1 failures", exitstatus=1)
        runs = redlight.load_runs(str(tmp_path))
        assert len(runs) == 1, runs
        got = redlight.file_coverage(runs[0], "tests/test_x.py")
        assert got != "true", got

    def test_c3p_an_unknown_plugin_dist_means_not_full_coverage(self, tmp_path):
        """C3p-1 consumer(〈二十三〉3、7 (vii))。分類:behavior-red。

        完整性事實全部關閉,`plugins` 多一項 `{"name": "evilplug", "kind": "other"}`(未知 dist)。
        d122df4 上失敗的原因:`.claude/hooks/redlight.py:407-426` 不讀 plugins ⇒ `"true"`。
        """
        comp = _c_all_off()
        comp["plugins"].append({"name": "evilplug", "kind": "other"})
        got = _c_raw_coverage(tmp_path, comp)
        assert got != "true", got

    def test_c3p_a_plugin_loaded_by_name_means_not_full_coverage(self, tmp_path):
        """C3p-2 consumer(〈二十三〉3、7 (vii))。分類:behavior-red。

        完整性事實全部關閉,`plugins` 多一項 `{"name": "myplug", "kind": "other"}`(`-p myplug` 之類)。
        d122df4 上失敗的原因:同 C3p-1。
        """
        comp = _c_all_off()
        comp["plugins"].append({"name": "myplug", "kind": "other"})
        got = _c_raw_coverage(tmp_path, comp)
        assert got != "true", got

    def test_c3p_an_extra_conftest_means_not_full_coverage(self, tmp_path):
        """C3p-3 consumer(〈二十三〉3、7 (vii))。分類:behavior-red。

        完整性事實全部關閉,`plugins` 多一項 `{"name": "tests/sub/conftest.py", "kind": "other"}`。
        d122df4 上失敗的原因:同 C3p-1。
        """
        comp = _c_all_off()
        comp["plugins"].append({"name": "tests/sub/conftest.py", "kind": "other"})
        got = _c_raw_coverage(tmp_path, comp)
        assert got != "true", got

    def test_c3d_the_fixed_command_with_everything_off_is_full_coverage(self, tmp_path, monkeypatch):
        """C3d-1(〈二十三〉7 全部條件成立)。分類:regression-lock。

        固定全套:args `tests` / TESTPATHS、選項全部關閉、沒有 shouldstop / shouldfail、
        縮小前全集 = 收集結果、plugin 全在白名單;X_A、X_B passed,X_XF 為明確辨識的 xfail
        (call 為 skipped 且帶 `wasxfail`)⇒ `"true"`。
        """
        c = _isolated_conftest(monkeypatch, tmp_path)
        _d_committed_root(tmp_path)
        _d_drive(c, tmp_path, {"tests/test_x.py": [X_A, X_B, X_XF]},
                 selected=[X_A, X_B, X_XF],
                 outcomes={X_A: "passed", X_B: "passed", X_XF: "xfail"},
                 option=_d_option(), pm=_d_plugins(c, tmp_path), exitstatus=0)
        runs = redlight.load_runs(str(tmp_path))
        assert len(runs) == 1, runs
        got = redlight.file_coverage(runs[0], "tests/test_x.py")
        assert got == "true", got


# ─────────────────────────────────────────────────────────────────────────────
# 票 145 Station 3d 紅燈 —— 收集定義完整性與版本邊界(〈二十九〉)
#
# 合約:票 145〈二十九〉2 (vii′)–(xiii)。規劃:docs/audits/2026-10-02-m1a-station3d-redlight-plan.md P4。
# 下文 `<TARGET>` = 02a5e28adf5aee11a43d5a1063504f01beb1d67f(與 9d1446a 之間程式碼相同)。
#
# **每一支都經真實 tests/conftest.py 的 producer**(`_isolated_conftest` 每次載入全新模組,沿用 3c-1b),
# 再由 `redlight.file_coverage` 判定 —— 不直接餵預先做好的 completeness(〈二十九〉5)。
# **pytest 層級的假物件照 pytest 9.1.1 的實際形狀**(規劃檔 P2;〈二十九〉1 實測):
#   - `config.option.override_ini` 是解析後的合併清單(CLI、PYTEST_ADDOPTS、ini addopts 都附加在這裡);
#     固定全套因已提交的 `--strict-markers` 而為 `["strict_markers=true"]`;
#   - `config.invocation_params.args` 只有 CLI 的 argv(不含 PYTEST_ADDOPTS);
#   - `config.inipath` 是實際採用的設定檔;`config.getini()` 回傳與它一致的有效值;
#   - `list_name_plugin()` 照 pluggy 的表示方式含 `(name, None)`(`-p no:`),`is_blocked()` 由同一份資料推出;
#   - `list_plugin_distinfo()` 的 dist 物件帶名稱與版本。
# **在 `collect()` 之內就被縮掉的身分(例:`-o python_functions=test_b` 的 test_a)從一開始就不在
# collect report 裡** —— driver 直接以縮小後的清單送出,不經「收集後移除」。
# **設定檔雜湊的情境用真的 git repo**:tmp root 先 `git init`,提交 `pyproject.toml` 與
# `tests/conftest.py`(真檔內容),再依情境改工作樹 —— 不以假雜湊值代替。
# 本段 helper 全部新寫;既有 helper(`_isolated_conftest` / `_COption` / `_c_item` / `_c_file` /
# `_c_internal` / `_CCollectReport` / `_c_call_collect_wrapper` / `_c_reports` / `_CompletenessSession`)
# 只呼叫、不修改。
#
# 本刀定稿的介面細節(語意依〈二十九〉2):pytest 版本取 conftest 所 import 的 `pytest` 模組的
# `__version__`;設定檔雜湊以 producer 的 `_ROOT` 為 repo 根(測試中為 tmp root)。
# ─────────────────────────────────────────────────────────────────────────────

import subprocess as _d_subprocess

_D_COMMITTED_PYPROJECT = (
    u'[tool.pytest.ini_options]\n'
    u'testpaths = ["tests"]\n'
    u'addopts = "-ra --strict-markers"\n')

# 已提交設定之下的有效值(規劃檔 P2(b);未設定的 key 取 pytest 9.1.1 預設)。
_D_BASELINE_INI = {
    "testpaths": ["tests"],
    "addopts": ["-ra", "--strict-markers"],
    "python_files": ["test_*.py", "*_test.py"],
    "python_classes": ["Test"],
    "python_functions": ["test"],
    "norecursedirs": ["*.egg", ".*", "_darcs", "build", "CVS", "dist", "node_modules", "venv", "{arch}"],
    "collect_imported_tests": True,
}

_D_FIXED_OVERRIDES = ["strict_markers=true"]

# `-p no:cacheprovider`:這些選項由 cacheprovider / stepwise 的 pytest_addoption 加入,停用後不存在;
# 停用的名稱(`_pytest/config/__init__.py:850-857`)。
_D_CACHEPROVIDER_OPTIONS = ("lf", "last_failed_no_failures", "failedfirst", "newfirst",
                            "stepwise", "stepwise_skip", "stepwise_reset")
_D_CACHEPROVIDER_BLOCKED = ("cacheprovider", "pytest_cacheprovider", "stepwise", "pytest_stepwise")

_D_FULL = {"tests/test_x.py": [X_A, X_B]}
_D_ONLY_B = {"tests/test_x.py": [X_B]}

# 票 145 Station 4g 授權 G1(規劃檔 S3g-0 P6「需要的授權」1):與 baseline 相符的已提交 evidence policy ——
# 已提交 addopts `-ra --strict-markers` ⇒ `strict_markers=true`;版本與 dist 等於 driver 固定的事實(授權 3)。
_D_POLICY_FILE = ".agents/evidence-policy.json"
_D_BASELINE_POLICY = {
    "schema": "monkeyleash.evidence-policy",
    "version": 1,
    "config_file": "pyproject.toml",
    "committed_overrides": list(_D_FIXED_OVERRIDES),
    "python_versions": ["3.11"],
    "pytest_versions": ["9.1.1"],
    "dists": [["anyio", "4.15.0"]],
}


def _d_write(root, rel, text):
    p = pathlib.Path(str(root)) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    with io.open(str(p), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _d_git(root, *args):
    return _d_subprocess.run(["git"] + list(args), cwd=str(root), capture_output=True, check=True)


def _d_committed_root(root):
    """在 `root` 建真的 git repo,提交 baseline `pyproject.toml` 與 root conftest(真檔內容)。"""
    _d_write(root, "pyproject.toml", _D_COMMITTED_PYPROJECT)
    conftest = pathlib.Path(str(root)) / "tests" / "conftest.py"
    conftest.parent.mkdir(parents=True, exist_ok=True)
    conftest.write_bytes((ROOT / "tests" / "conftest.py").read_bytes())
    _d_write(root, _D_POLICY_FILE, json.dumps(_D_BASELINE_POLICY, ensure_ascii=False, indent=2) + u"\n")
    _d_git(root, "init", "-q")
    _d_git(root, "config", "user.email", "t@example.invalid")
    _d_git(root, "config", "user.name", "t")
    _d_git(root, "add", "pyproject.toml", "tests/conftest.py", _D_POLICY_FILE)
    _d_git(root, "commit", "-q", "-m", "baseline")
    return root


class _DDist:
    """`list_plugin_distinfo()` 的 dist:帶名稱與版本(pluggy DistFacade 的讀取點)。"""

    def __init__(self, name, version):
        self.project_name = name
        self.version = version
        self.metadata = {"name": name, "version": version}


class _DPluginManager:
    """`config.pluginmanager`。`list_name_plugin()` 照 pluggy 實際表示方式含 `(name, None)`
    (`pluggy/_manager.py:230-233, 427-429`);`is_blocked()` 由同一份資料推出,兩者必然一致。"""

    def __init__(self, name_plugins, distinfo=()):
        self._name_plugins = list(name_plugins)
        self._distinfo = list(distinfo)

    def list_name_plugin(self):
        return list(self._name_plugins)

    def list_plugin_distinfo(self):
        return list(self._distinfo)

    def is_blocked(self, name):
        return any(n == name and p is None for n, p in self._name_plugins)

    def get_plugin(self, name):
        return dict(self._name_plugins).get(name)

    def has_plugin(self, name):
        return self.get_plugin(name) is not None


def _d_plugins(c, root, blocked=(), anyio_version="4.15.0"):
    """固定全套的 plugin 集合(`_pytest` 內建、root conftest、anyio)+ `blocked` 的 `(name, None)`。"""
    builtin_mod = _c_types.ModuleType("_pytest.main")
    internal = _c_internal("_pytest.config", "_InternalHelper")
    anyio_mod = _c_types.ModuleType("anyio.pytest_plugin")
    names = [("main", builtin_mod),
             (str(id(internal)), internal),
             (_c_os.path.join(str(root), "tests", "conftest.py"), c),
             ("anyio", anyio_mod)]
    names += [(n, None) for n in blocked]
    return _DPluginManager(names, [(anyio_mod, _DDist("anyio", anyio_version))])


class _DInvocationParams:
    def __init__(self, args, d):
        self.args = tuple(args)
        self.plugins = None
        self.dir = d


class _DConfig:
    """`config`:args / args_source / rootpath / invocation_params / option / pluginmanager /
    inipath / getini —— 彼此一致(同一個 pytest 世界)。"""

    def __init__(self, root, option, pluginmanager, argv=("-q",), inipath="pyproject.toml", ini=None):
        self.args = ["tests"]
        self.args_source = pytest.Config.ArgsSource.TESTPATHS
        self.rootpath = pathlib.Path(str(root))
        self.invocation_params = _DInvocationParams(argv, self.rootpath)
        self.option = option
        self.pluginmanager = pluginmanager
        self.inipath = self.rootpath / inipath
        self._ini = dict(_D_BASELINE_INI)
        self._ini.update(ini or {})

    def getini(self, name):
        if name not in self._ini:
            raise ValueError("unknown configuration value: %r" % (name,))
        value = self._ini[name]
        return list(value) if isinstance(value, list) else value

    def getoption(self, name, default=None, skip=False):
        return getattr(self.option, name, default)


def _d_option(missing=(), **overrides):
    """固定全套的 `config.option`:3c 的「全部關閉」+ `override_ini == ["strict_markers=true"]`、
    `inifilename is None`(沒有 `-c`)。"""
    values = {"override_ini": list(_D_FIXED_OVERRIDES), "inifilename": None}
    values.update(overrides)
    return _COption(missing=missing, **values)


def _d_drive(c, root, files, selected, outcomes, option=None, pm=None, argv=("-q",),
             inipath="pyproject.toml", ini=None, shouldstop=False, shouldfail=False, exitstatus=0):
    """依 pytest 9.1.1 的呼叫順序驅動真實 conftest(同 `_c_drive`),session 帶 `_DConfig`。

    `files`:{測試檔: collect report 裡的完整 nodeid 清單} —— 在 `collect()` 之內就被縮掉的身分不在清單裡。
    """
    def hook(name):
        return getattr(c, name, None) or (lambda *a, **k: None)

    for path in sorted(files):
        report = _CCollectReport(path, [_c_item(n) for n in files[path]])
        _c_call_collect_wrapper(c, _c_file(root, path), report)
        hook("pytest_collectreport")(report)
    config = _DConfig(root, option if option is not None else _d_option(),
                      pm if pm is not None else _d_plugins(c, root),
                      argv=argv, inipath=inipath, ini=ini)
    session = _CompletenessSession([_c_item(n) for n in selected], config)
    hook("pytest_collection_finish")(session)
    for nodeid, kind in outcomes.items():
        for rep in _c_reports(nodeid, kind):
            hook("pytest_runtest_logreport")(rep)
    session.shouldstop = shouldstop
    session.shouldfail = shouldfail
    hook("pytest_sessionfinish")(session, exitstatus)


def _d_coverage(tmp_path, monkeypatch, files=None, blocked=(), anyio_version="4.15.0", **kw):
    """一次模擬執行(全新 conftest;`files` 的身分全部 passed、exit 0);回傳**最後一筆** session 對
    `tests/test_x.py` 的 `file_coverage`。`kw` 交給 `_d_drive`(option / argv / inipath / ini / shouldfail…)。"""
    files = files if files is not None else _D_FULL
    selected = [n for ids in files.values() for n in ids]
    c = _isolated_conftest(monkeypatch, tmp_path)
    pm = _d_plugins(c, tmp_path, blocked=blocked, anyio_version=anyio_version)
    _d_drive(c, tmp_path, files, selected, dict((n, "passed") for n in selected), pm=pm, **kw)
    runs = redlight.load_runs(str(tmp_path))
    assert runs, runs
    return redlight.file_coverage(runs[-1], "tests/test_x.py")


class TestCollectionDefinitionCoverage:

    def test_d3a_an_override_ini_narrowing_is_not_full_coverage(self, tmp_path, monkeypatch):
        """D3a-1(〈二十九〉2 (viii);S5c-F1)。分類:behavior-red。

        CLI `python -X utf8 -m pytest -q -o python_functions=test_b`:test_a 在 `Module.collect()` 之內
        就不被收集 ⇒ 縮小前快照與 collected 都只有 X_B;`override_ini` 多一筆 `python_functions=test_b`。
        其他條件(已提交設定、沒有 `-c`、沒有 `-p no:`、pytest 9.1.1、anyio 4.15.0)全部成立 ⇒ 不得為 `"true"`。
        9d1446a 上失敗的原因:`<TARGET>:tests/conftest.py:322-341` 不記任何 override 事實;
        `<TARGET>:.claude/hooks/redlight.py:590-592` {X_B} == {X_B} ⇒ `:597` 回 `"true"`。
        """
        _d_committed_root(tmp_path)
        got = _d_coverage(tmp_path, monkeypatch, files=_D_ONLY_B,
                          option=_d_option(override_ini=_D_FIXED_OVERRIDES + ["python_functions=test_b"]),
                          argv=("-q", "-o", "python_functions=test_b"),
                          ini={"python_functions": ["test_b"]})
        assert got != "true", got

    def test_d3b_an_override_from_pytest_addopts_is_not_full_coverage(self, tmp_path, monkeypatch):
        """D3b-1(〈二十九〉2 (viii)、「不得掃 argv」;〈二十九〉1 (b)(c))。分類:behavior-red。

        `PYTEST_ADDOPTS="-o python_functions=test_b"`:override 只出現在解析後的 `config.option.override_ini`,
        `invocation_params.args == ("-q",)` 裡**沒有** `-o` ⇒ 掃 argv 的實作會漏;不得為 `"true"`。
        9d1446a 上失敗的原因:同 D3a-1(`<TARGET>:tests/conftest.py:322-341`;
        `<TARGET>:.claude/hooks/redlight.py:590-592, 597`)。
        """
        _d_committed_root(tmp_path)
        got = _d_coverage(tmp_path, monkeypatch, files=_D_ONLY_B,
                          option=_d_option(override_ini=_D_FIXED_OVERRIDES + ["python_functions=test_b"]),
                          argv=("-q",),
                          ini={"python_functions": ["test_b"]})
        assert got != "true", got

    def test_d3c_a_config_file_option_is_not_full_coverage(self, tmp_path, monkeypatch):
        """D3c-1(〈二十九〉2 (ix)(x))。分類:behavior-red。

        `-c alt.toml`(未追蹤,內容 = 已提交設定 + `python_functions = ["test_b"]`):
        `inifilename == "alt.toml"`、`inipath` 指向它;沒有額外 `-o` ⇒ 不得為 `"true"`。
        9d1446a 上失敗的原因:`<TARGET>:tests/conftest.py:322-341` 不記 `inifilename` / `inipath`;
        `<TARGET>:.claude/hooks/redlight.py:590-592, 597`。
        """
        _d_committed_root(tmp_path)
        _d_write(tmp_path, "alt.toml", _D_COMMITTED_PYPROJECT + u'python_functions = ["test_b"]\n')
        got = _d_coverage(tmp_path, monkeypatch, files=_D_ONLY_B,
                          option=_d_option(inifilename="alt.toml"),
                          argv=("-q", "-c", "alt.toml"), inipath="alt.toml",
                          ini={"python_functions": ["test_b"]})
        assert got != "true", got

    def test_d3c_a_config_file_option_naming_the_committed_config(self, tmp_path, monkeypatch):
        """D3c-2(〈二十九〉2 (ix):`-c` 一律 fail-closed,即使指向已提交的權威檔)。分類:behavior-red。

        `-c pyproject.toml`(就是已提交、工作樹未改的那一份;有效值 = baseline;全收集、全 passed)
        ⇒ 仍不得為 `"true"`。
        9d1446a 上失敗的原因:`<TARGET>:tests/conftest.py:322-341` 不記 `inifilename`;
        `<TARGET>:.claude/hooks/redlight.py:597` 回 `"true"`。
        """
        _d_committed_root(tmp_path)
        got = _d_coverage(tmp_path, monkeypatch,
                          option=_d_option(inifilename="pyproject.toml"),
                          argv=("-q", "-c", "pyproject.toml"))
        assert got != "true", got

    def test_d3w_an_unexpected_config_file_is_not_full_coverage(self, tmp_path, monkeypatch):
        """D3w-1(〈二十九〉2 (x);〈二十九〉1 (e))。分類:behavior-red。

        repo 根多一份未追蹤的 `pytest.ini`(`python_functions = test_b`):沒有任何 `-o`、沒有 `-c`,
        `inipath` 改指向 `pytest.ini`,test_a 不被收集 ⇒ 不得為 `"true"`。
        9d1446a 上失敗的原因:`<TARGET>:tests/conftest.py:322-341` 不記 `inipath`;
        `<TARGET>:.claude/hooks/redlight.py:590-592, 597`。
        """
        _d_committed_root(tmp_path)
        _d_write(tmp_path, "pytest.ini",
                 u"[pytest]\ntestpaths = tests\naddopts = -ra --strict-markers\npython_functions = test_b\n")
        got = _d_coverage(tmp_path, monkeypatch, files=_D_ONLY_B,
                          inipath="pytest.ini", ini={"python_functions": ["test_b"]})
        assert got != "true", got

    def test_d3w_an_uncommitted_config_change_is_not_full_coverage(self, tmp_path, monkeypatch):
        """D3w-2(〈二十九〉2 (xi))。分類:behavior-red。

        tmp git repo 已提交 baseline `pyproject.toml`;工作樹再加上 `python_functions = ["test_b"]`
        (`inipath` 不變、沒有 `-o`)⇒ test_a 不被收集 ⇒ 不得為 `"true"`。
        9d1446a 上失敗的原因:`<TARGET>:tests/conftest.py:322-341` 沒有設定檔內容的事實;
        `<TARGET>:.claude/hooks/redlight.py:590-592, 597`。
        """
        _d_committed_root(tmp_path)
        _d_write(tmp_path, "pyproject.toml", _D_COMMITTED_PYPROJECT + u'python_functions = ["test_b"]\n')
        got = _d_coverage(tmp_path, monkeypatch, files=_D_ONLY_B,
                          ini={"python_functions": ["test_b"]})
        assert got != "true", got

    def test_d3w_a_non_collection_edit_to_the_config_file(self, tmp_path, monkeypatch):
        """D3w-3(〈二十九〉2 (xi);〈二十九〉3「只改註解也判不等」)。分類:behavior-red。

        工作樹的 `pyproject.toml` 只多一行註解(有效值全部 = baseline;全收集、全 passed)
        ⇒ blob 雜湊 ≠ HEAD ⇒ 不得為 `"true"`(fail-closed 的代價,裁決明定)。
        9d1446a 上失敗的原因:`<TARGET>:tests/conftest.py:322-341` 沒有設定檔內容的事實;
        `<TARGET>:.claude/hooks/redlight.py:597` 回 `"true"`。
        """
        _d_committed_root(tmp_path)
        _d_write(tmp_path, "pyproject.toml", u"# 只改註解\n" + _D_COMMITTED_PYPROJECT)
        got = _d_coverage(tmp_path, monkeypatch)
        assert got != "true", got

    def test_d3w_an_uncommitted_root_conftest_change_is_not_full_coverage(self, tmp_path, monkeypatch):
        """D3w-4(〈二十九〉2 (xi):root conftest 是 producer 本身)。分類:behavior-red。

        tmp git repo 已提交 `tests/conftest.py`;工作樹再改它(多一行)⇒ blob 雜湊 ≠ HEAD ⇒ 不得為 `"true"`。
        9d1446a 上失敗的原因:`<TARGET>:tests/conftest.py:322-341` 沒有 conftest 內容的事實;
        `<TARGET>:.claude/hooks/redlight.py:597` 回 `"true"`。
        """
        _d_committed_root(tmp_path)
        conftest = tmp_path / "tests" / "conftest.py"
        conftest.write_bytes(conftest.read_bytes() + b"\n# working tree edit\n")
        got = _d_coverage(tmp_path, monkeypatch)
        assert got != "true", got

    def test_d3v_an_unrecognized_pytest_version_is_not_full_coverage(self, tmp_path, monkeypatch):
        """D3v-1(〈二十九〉2 (xiii))。分類:behavior-red。

        其他條件全部成立,pytest 版本事實(conftest 所 import 的 `pytest.__version__`)為 `"9.2.0"`
        ⇒ 不在已盤點清單 {"9.1.1"} ⇒ 不得為 `"true"`。
        9d1446a 上失敗的原因:`<TARGET>:tests/conftest.py:322-341` 不記 pytest 版本;
        `<TARGET>:.claude/hooks/redlight.py:597` 回 `"true"`。
        """
        _d_committed_root(tmp_path)
        monkeypatch.setattr(pytest, "__version__", "9.2.0")
        got = _d_coverage(tmp_path, monkeypatch)
        assert got != "true", got

    def test_d3v_a_known_plugin_with_unrecognized_version_is_not_full_coverage(self, tmp_path, monkeypatch):
        """D3v-2(〈二十九〉2 (vii′))。分類:behavior-red。

        其他條件全部成立;`list_plugin_distinfo()` 中 `anyio.pytest_plugin` 物件配對到名稱 `anyio`、
        版本 `9.9.9` 的 dist ⇒ (名稱, 版本) 不在已盤點清單 {("anyio", "4.15.0")} ⇒ kind = other ⇒ 不得為 `"true"`。
        9d1446a 上失敗的原因:`<TARGET>:.claude/hooks/redlight.py:521-523` 只比 dist 名稱 ⇒ known_dist;
        `:597` 回 `"true"`。
        """
        _d_committed_root(tmp_path)
        got = _d_coverage(tmp_path, monkeypatch, anyio_version="9.9.9")
        assert got != "true", got

    def test_d3i_lf_alone_is_not_full_coverage(self, tmp_path, monkeypatch):
        """D3i-1(S5c-F2;〈二十三〉7 (ii) 單獨鎖住)。分類:regression-lock。

        對照組:固定全套事實 ⇒ `"true"`。破壞組:只把 `lf` 設為 True(快照 = collected、
        每個身分都 passed、exit 0、其他條件不變)⇒ 不得為 `"true"`。兩次執行各用全新 conftest。
        """
        _d_committed_root(tmp_path)
        control = _d_coverage(tmp_path, monkeypatch)
        broken = _d_coverage(tmp_path, monkeypatch, option=_d_option(lf=True))
        assert control == "true", control
        assert broken != "true", broken

    def test_d3i_maxfail_alone_is_not_full_coverage(self, tmp_path, monkeypatch):
        """D3i-2(S5c-F2;〈二十三〉7 (iii) 的 maxfail 單獨鎖住)。分類:regression-lock。

        對照組:固定全套事實 ⇒ `"true"`。破壞組:只把 `maxfail` 設為 1(shouldfail 為 False、
        每個身分都 passed、其他條件不變)⇒ 不得為 `"true"`。
        """
        _d_committed_root(tmp_path)
        control = _d_coverage(tmp_path, monkeypatch)
        broken = _d_coverage(tmp_path, monkeypatch, option=_d_option(maxfail=1))
        assert control == "true", control
        assert broken != "true", broken

    def test_d3i_shouldfail_alone_is_not_full_coverage(self, tmp_path, monkeypatch):
        """D3i-3(S5c-F2;〈二十三〉7 (iv) 單獨鎖住)。分類:regression-lock。

        對照組:固定全套事實 ⇒ `"true"`。破壞組:只讓 session 結束時 `shouldfail` 為 True
        (maxfail 為 None、每個身分都 passed、其他條件不變)⇒ 不得為 `"true"`。
        """
        _d_committed_root(tmp_path)
        control = _d_coverage(tmp_path, monkeypatch)
        broken = _d_coverage(tmp_path, monkeypatch, shouldfail=True)
        assert control == "true", control
        assert broken != "true", broken

    def test_d3x_a_blocked_plugin_is_not_full_coverage(self, tmp_path, monkeypatch):
        """D3x-1(S5c-X1;〈二十九〉2 (xii))。分類:regression-lock。

        `-p no:cacheprovider`:`list_name_plugin()` 含 cacheprovider / pytest_cacheprovider / stepwise /
        pytest_stepwise 四筆 `None`(〈二十九〉1 (d)),`is_blocked` 一致,`config.option` 沒有 lf / stepwise
        等屬性;其他條件全部成立 ⇒ 不得為 `"true"`。
        9d1446a 上已通過:`<TARGET>:.claude/hooks/redlight.py:489, 526-530` 把 `(name, None)` 判為 other
        ⇒ `:576-577` 回 `unknown`。
        """
        _d_committed_root(tmp_path)
        got = _d_coverage(tmp_path, monkeypatch, blocked=_D_CACHEPROVIDER_BLOCKED,
                          option=_d_option(missing=_D_CACHEPROVIDER_OPTIONS),
                          argv=("-q", "-p", "no:cacheprovider"))
        assert got != "true", got

    def test_d3d_the_fixed_command_with_the_committed_config_is_full_coverage(self, tmp_path, monkeypatch):
        """D3d-1(〈二十九〉2 全部條件成立)。分類:regression-lock。

        固定全套 `python -X utf8 -m pytest -q`:`override_ini == ["strict_markers=true"]`(已提交的
        `--strict-markers` 帶來的,**不是空的**)、`inifilename is None`、`inipath` 為 `pyproject.toml`、
        工作樹的 `pyproject.toml` 與 `tests/conftest.py` = 已提交 blob、沒有 `(name, None)`、
        pytest 9.1.1、anyio 4.15.0;全收集、全 passed ⇒ `"true"`。
        專門擋「override_ini 非空 ⇒ 不是 true」那種照字面的實作。
        """
        _d_committed_root(tmp_path)
        got = _d_coverage(tmp_path, monkeypatch)
        assert got == "true", got

    # 原 `test_d4_the_committed_addopts_override_constant_matches_pyproject` 於票 145 Station 4g 刪除
    # (〈四十八〉48.1 第 4 點 C,Jeff 明文修訂〈三十一〉裁決 3 的**適用位置**,語意不變):
    # 常數 `COMMITTED_ADDOPTS_OVERRIDES` 已移進宿主 policy;框架那一半由 `TestAddoptsDerivation`(fixture)
    # 與 verdict 時的機器鎖步承接,agent-gates 自身「policy ↔ pyproject」的鎖步由宿主專用、不出貨的
    # tests/test_host_evidence_policy.py 承接(git show HEAD、讀不到即失敗、不 skip)。


# ─────────────────────────────────────────────────────────────────────────────
# 票 145 Station 3e 紅燈 —— pass 有效性 / 受支援執行環境(〈三十五〉3 (xiv)–(xviii))
# 與 producer 路徑正規化(S5d-F3;〈三十五〉4 的 F3-甲)
#
# 合約:票 145〈三十五〉。規劃:docs/audits/2026-10-03-m1a-station3e-redlight-plan.md P4。
# 下文 `<TARGET>` = 889fbd8f666ea522ff6af172979a8d020e50b86b(與 2258490 之間程式碼相同)。
#
# **每一支都經真實 tests/conftest.py 的 producer**(`_isolated_conftest` 每次載入全新模組,沿用 3c-1b),
# 再由 `redlight.file_coverage` 判定或直接檢查持久化的那一行 —— 不直接餵預先做好的 completeness。
# tmp root 是真的 git repo(`_d_committed_root`)。
#
# 本刀定稿的介面細節(語意依〈三十五〉3):
#   - producer 在 sessionfinish 當下經 conftest **模組層的 `sys`** 讀 `sys.flags.optimize` 與
#     `sys.version_info`(major.minor);driver 以 `monkeypatch.setattr(c, "sys", _e_sys(...), raising=False)`
#     換掉**該 conftest 所見的** `sys`。**不改全域 `sys.flags`** —— import 機制以它決定 pyc 檔名
#     (CPython importlib._bootstrap_external:470-473),全域替換會波及 driver 期間的任何 import。
#   - `runxfail` / `pythonwarnings` / `trace` 以 `_e_option(...)` 明確帶入真實 pytest 的預設值
#     (False / None / False);`_C_OPTION_DEFAULTS` 依〈三十五〉5 到 4e 才補這三個鍵,本段不改既有 helper。
#   - S5d-F3 的輸入以「一類」驅動:三種形狀(win-abs / posix-abs / rel-escape),合成使用者名稱一律 `e3p-user`;
#     斷言持久化行的**原文**不含 `e3p-user`(不比對 JSON 跳脫後的整串)。
# 本段 helper 全部新寫;既有 helper(`_isolated_conftest` / `_d_committed_root` / `_d_option` / `_d_plugins` /
# `_d_drive` / `_D_FULL`)只呼叫、不修改。
# ─────────────────────────────────────────────────────────────────────────────

import collections as _e_collections
import sys as _e_real_sys

# 真實 `sys.flags` 的公開欄位(structseq 的 `n_*` 計數與 count / index 方法除外)。
_E_FLAG_FIELDS = tuple(
    n for n in dir(_e_real_sys.flags)
    if not n.startswith(("_", "n_")) and not callable(getattr(_e_real_sys.flags, n)))

_EVersion = _e_collections.namedtuple("_EVersion", "major minor micro releaselevel serial")

_E_USER = "e3p-user"

_E_PATH_SHAPES = [
    pytest.param("C:\\Users\\" + _E_USER + "\\{}", id="win-abs"),
    pytest.param("/home/" + _E_USER + "/{}", id="posix-abs"),
    pytest.param("../../" + _E_USER + "/{}", id="rel-escape"),
]


class _ESys(object):
    """conftest 所見的 `sys` 替身:`flags` / `version_info` 由測試指定,其他屬性一律轉給真的 `sys`。"""

    def __init__(self, flags, version_info):
        self.flags = flags
        self.version_info = version_info

    def __getattr__(self, name):
        return getattr(_e_real_sys, name)


def _e_sys(optimize=0, drop=(), version_info=None):
    """複製真實 `sys.flags` 的全部公開欄位,只把 `optimize` 換成指定值;`drop` 中的欄位不存在(缺欄)。
    `version_info` 為 None ⇒ 沿用真實版本。"""
    values = dict((n, getattr(_e_real_sys.flags, n)) for n in _E_FLAG_FIELDS)
    values["optimize"] = optimize
    for k in drop:
        values.pop(k, None)
    vi = version_info if version_info is not None else _EVersion(*tuple(_e_real_sys.version_info))
    return _ESys(_c_types.SimpleNamespace(**values), vi)


def _e_option(**overrides):
    """固定全套的 `config.option`(`_d_option`)+ 三個 pass 有效性選項的真實預設值。"""
    values = {"runxfail": False, "pythonwarnings": None, "trace": False}
    values.update(overrides)
    return _d_option(**values)


def _e_run(tmp_path, monkeypatch, sys_=None, option=None, blocked=()):
    """一次模擬執行(全新 conftest;`_D_FULL` 全收集、全 passed、exit 0;其他事實同固定全套)。
    回傳**最後一筆** session。`sys_` 為 None ⇒ 不注入(producer 看到真的 `sys`)。"""
    selected = [n for ids in _D_FULL.values() for n in ids]
    c = _isolated_conftest(monkeypatch, tmp_path)
    if sys_ is not None:
        monkeypatch.setattr(c, "sys", sys_, raising=False)
    pm = _d_plugins(c, tmp_path, blocked=blocked)
    _d_drive(c, tmp_path, _D_FULL, selected, dict((n, "passed") for n in selected),
             option=option if option is not None else _e_option(), pm=pm)
    runs = redlight.load_runs(str(tmp_path))
    assert runs, runs
    return runs[-1]


def _e_coverage(tmp_path, monkeypatch, **kw):
    return redlight.file_coverage(_e_run(tmp_path, monkeypatch, **kw), "tests/test_x.py")


def _e_persisted_line(tmp_path):
    """帳本裡最後一筆 session 的**原文**(未經 json 解析)。"""
    with io.open(redlight.session_log(str(tmp_path)), encoding="utf-8") as f:
        lines = [ln for ln in f if ln.strip()]
    assert lines, lines
    return lines[-1]


class TestPassValidityCoverage:

    @pytest.mark.parametrize("optimize", [1, 2])
    def test_e3o_an_optimized_interpreter_is_not_full_coverage(self, tmp_path, monkeypatch, optimize):
        """E3o-1(〈三十五〉3 (xiv);S5d-F1 / S5d-X1)。分類:behavior-red。

        對照組:`optimize=0`、其他事實同固定全套 ⇒ `"true"`。破壞組:只把 conftest 所見的
        `sys.flags.optimize` 換成 1(`-O` / `PYTHONOPTIMIZE=1`)或 2(`-OO`)⇒ 不得為 `"true"`。
        TARGET 上失敗的原因:`<TARGET>:tests/conftest.py:335-355` 不記 optimize;
        `<TARGET>:.claude/hooks/redlight.py:696-733` 沒有對應條件 ⇒ `:733` 回 `"true"`。
        """
        _d_committed_root(tmp_path)
        control = _e_coverage(tmp_path, monkeypatch, sys_=_e_sys(optimize=0))
        broken = _e_coverage(tmp_path, monkeypatch, sys_=_e_sys(optimize=optimize))
        assert control == "true", control
        assert broken != "true", broken

    def test_e3o_a_missing_optimize_fact_is_not_full_coverage(self, tmp_path, monkeypatch):
        """E3o-2(〈三十五〉3 (xiv):缺欄 ⇒ 不得為 "true")。分類:behavior-red。

        對照組:`optimize=0` ⇒ `"true"`。破壞組:conftest 所見的 `sys.flags` 沒有 `optimize` 欄位 ⇒ 不得為 `"true"`。
        TARGET 上失敗的原因:同 E3o-1(`<TARGET>:tests/conftest.py:335-355`;`<TARGET>:.claude/hooks/redlight.py:733`)。
        """
        _d_committed_root(tmp_path)
        control = _e_coverage(tmp_path, monkeypatch, sys_=_e_sys(optimize=0))
        broken = _e_coverage(tmp_path, monkeypatch, sys_=_e_sys(drop=("optimize",)))
        assert control == "true", control
        assert broken != "true", broken

    def test_e3x_runxfail_alone_is_not_full_coverage(self, tmp_path, monkeypatch):
        """E3x-1(〈三十五〉3 (xv);〈三十五〉1 (a))。分類:behavior-red。

        對照組:`runxfail=False` ⇒ `"true"`。破壞組:只把 `runxfail` 設為 True ⇒ 不得為 `"true"`。
        TARGET 上失敗的原因:`<TARGET>:.claude/hooks/redlight.py:457-458` 的 `COMPLETENESS_OPTIONS` 沒有 runxfail,
        `:696-733` 沒有對應條件 ⇒ `:733` 回 `"true"`。
        """
        _d_committed_root(tmp_path)
        control = _e_coverage(tmp_path, monkeypatch, option=_e_option())
        broken = _e_coverage(tmp_path, monkeypatch, option=_e_option(runxfail=True))
        assert control == "true", control
        assert broken != "true", broken

    def test_e3w_a_pytest_warning_filter_alone_is_not_full_coverage(self, tmp_path, monkeypatch):
        """E3w-1(〈三十五〉3 (xvi);〈三十五〉1 (b))。分類:behavior-red。

        對照組:`pythonwarnings=None` ⇒ `"true"`。破壞組:只帶 pytest 的 `-W ignore::UserWarning` ⇒ 不得為 `"true"`。
        TARGET 上失敗的原因:同 E3x-1(`<TARGET>:.claude/hooks/redlight.py:457-458, 733`)。
        """
        _d_committed_root(tmp_path)
        control = _e_coverage(tmp_path, monkeypatch, option=_e_option())
        broken = _e_coverage(tmp_path, monkeypatch,
                             option=_e_option(pythonwarnings=["ignore::UserWarning"]))
        assert control == "true", control
        assert broken != "true", broken

    def test_e3t_trace_alone_is_not_full_coverage(self, tmp_path, monkeypatch):
        """E3t-1(〈三十五〉3 (xvii))。分類:behavior-red。

        對照組:`trace=False` ⇒ `"true"`。破壞組:只把 `trace` 設為 True(`--trace`)⇒ 不得為 `"true"`。
        TARGET 上失敗的原因:同 E3x-1(`<TARGET>:.claude/hooks/redlight.py:457-458, 733`)。
        """
        _d_committed_root(tmp_path)
        control = _e_coverage(tmp_path, monkeypatch, option=_e_option())
        broken = _e_coverage(tmp_path, monkeypatch, option=_e_option(trace=True))
        assert control == "true", control
        assert broken != "true", broken

    def test_e3v_an_unrecognized_python_version_is_not_full_coverage(self, tmp_path, monkeypatch):
        """E3v-1(〈三十五〉3 (xviii))。分類:behavior-red。

        對照組:真實 Python 版本(3.11)⇒ `"true"`。破壞組:conftest 所見的 `sys.version_info` 為 (3, 12, 0, ...)
        ⇒ 不在已盤點清單 {"3.11"} ⇒ 不得為 `"true"`。
        TARGET 上失敗的原因:`<TARGET>:tests/conftest.py:335-355` 不記 Python 版本;
        `<TARGET>:.claude/hooks/redlight.py:696-733` 沒有對應條件 ⇒ `:733` 回 `"true"`。
        """
        _d_committed_root(tmp_path)
        control = _e_coverage(tmp_path, monkeypatch, sys_=_e_sys())
        broken = _e_coverage(tmp_path, monkeypatch,
                             sys_=_e_sys(version_info=_EVersion(3, 12, 0, "final", 0)))
        assert control == "true", control
        assert broken != "true", broken

    def test_e3o_the_producer_records_the_interpreter_optimize_flag(self, tmp_path, monkeypatch):
        """E3o-3(〈三十五〉3 (xiv) 的 producer 側)。分類:behavior-red。

        注入 `optimize=1` ⇒ 持久化的 `completeness["optimize"] == 1`;不注入 ⇒ 等於真實的 `sys.flags.optimize`。
        鎖住「producer 真的在 sessionfinish 當下經模組層 `sys` 讀它」—— 不是 consumer 收到預先做好的 dict。
        TARGET 上失敗的原因:`<TARGET>:tests/conftest.py:340-355` 的 completeness 沒有 `optimize` 鍵。
        """
        _d_committed_root(tmp_path)
        injected = _e_run(tmp_path, monkeypatch, sys_=_e_sys(optimize=1))
        plain = _e_run(tmp_path, monkeypatch)
        got_injected = (injected.get("completeness") or {}).get("optimize")
        got_plain = (plain.get("completeness") or {}).get("optimize")
        assert got_injected == 1, injected.get("completeness")
        assert got_plain == _e_real_sys.flags.optimize, plain.get("completeness")

    def test_e3x_the_producer_records_runxfail_and_pythonwarnings(self, tmp_path, monkeypatch):
        """E3x-2(〈三十五〉3 (xv)(xvi)(xvii) 的 producer 側)。分類:behavior-red。

        `runxfail=True`、`pythonwarnings=["ignore::UserWarning"]`、`trace=True` ⇒ 持久化的 `options`
        含這三鍵,值分別為 True、非 None 且非空、True。
        TARGET 上失敗的原因:`<TARGET>:tests/conftest.py:341-342` 的 `options` 只含
        `<TARGET>:.claude/hooks/redlight.py:457-458` 的 8 鍵。
        """
        _d_committed_root(tmp_path)
        run = _e_run(tmp_path, monkeypatch,
                     option=_e_option(runxfail=True, pythonwarnings=["ignore::UserWarning"], trace=True))
        options = (run.get("completeness") or {}).get("options") or {}
        assert options.get("runxfail") is True, options
        assert options.get("pythonwarnings") not in (None, []), options
        assert options.get("trace") is True, options

    def test_e3d_the_fixed_command_with_a_plain_interpreter_is_full_coverage(self, tmp_path, monkeypatch):
        """E3d-1(〈三十五〉3 全部條件成立)。分類:regression-lock。

        固定全套 `python -X utf8 -m pytest -q`:`optimize=0`、真實 Python 版本、`runxfail=False`、
        `pythonwarnings=None`、`trace=False`,其他事實同 4d 的 D3d-1 ⇒ `"true"`。
        """
        _d_committed_root(tmp_path)
        got = _e_coverage(tmp_path, monkeypatch, sys_=_e_sys(optimize=0), option=_e_option())
        assert got == "true", got

    def test_e3a_plain_assert_mode_on_a_plain_interpreter_is_still_full_coverage(self, tmp_path, monkeypatch):
        """E3a-1(〈三十五〉1 (c)、3 末句:不新增 assertmode 條件)。分類:regression-lock。

        同 E3d-1,另帶 `assertmode="plain"`:`optimize == 0` 時 plain 只失去 introspection(reporting)
        ⇒ 仍為 `"true"`。防止 4e 多鎖。
        """
        _d_committed_root(tmp_path)
        got = _e_coverage(tmp_path, monkeypatch, sys_=_e_sys(optimize=0),
                          option=_e_option(assertmode="plain"))
        assert got == "true", got


class TestProducerPathNormalization:

    @pytest.mark.parametrize("shape", _E_PATH_SHAPES)
    def test_e3p_blocked_plugin_names_never_persist_a_path(self, tmp_path, monkeypatch, shape):
        """E3p-1(S5d-F3;〈三十五〉4 名稱欄位)。分類:behavior-red(三種形狀皆是)。

        `-p no:<X>`:`list_name_plugin()` 含 `(X, None)` 與 `("pytest_" + X, None)`
        (照 `_pytest/config/__init__.py:855-857` 的成對表示),X 為路徑形狀 ⇒ 持久化行不含 `e3p-user`。
        TARGET 上失敗的原因:`<TARGET>:.claude/hooks/redlight.py:568-571` 的 `blocked` 原樣落帳;
        `pytest_` + X 不是絕對路徑,`:549-550` 也讓它在 `plugins[].name` 原樣落帳。
        """
        _d_committed_root(tmp_path)
        name = shape.format("x.py")
        _e_run(tmp_path, monkeypatch, blocked=(name, "pytest_" + name))
        line = _e_persisted_line(tmp_path)
        assert _E_USER not in line, line

    @pytest.mark.parametrize("shape", _E_PATH_SHAPES)
    def test_e3p_a_config_file_option_never_persists_a_path(self, tmp_path, monkeypatch, shape):
        """E3p-2(S5d-F3;〈三十五〉4 (1) 類欄位 `inifilename`)。
        分類:`[rel-escape]` behavior-red;`[win-abs]` / `[posix-abs]` regression-lock(以本機 Windows 為準)。

        `-c <路徑形狀>` ⇒ 持久化行不含 `e3p-user`。
        TARGET 上 `[rel-escape]` 失敗的原因:`<TARGET>:.claude/hooks/redlight.py:582` 相對路徑只換反斜線、原樣落帳。
        `[win-abs]` / `[posix-abs]` 在 Windows 上由 `:580-581` 正規化;在 POSIX 上 `os.path.isabs` 不認 `C:\\…`
        ⇒ `[win-abs]` 會紅(S5d-F3 的跨平台缺口)。
        """
        _d_committed_root(tmp_path)
        _e_run(tmp_path, monkeypatch, option=_e_option(inifilename=shape.format("alt.toml")))
        line = _e_persisted_line(tmp_path)
        assert _E_USER not in line, line

    @pytest.mark.parametrize("shape", _E_PATH_SHAPES)
    def test_e3p_an_override_value_never_persists_a_path(self, tmp_path, monkeypatch, shape):
        """E3p-3(S5d-F3;〈三十五〉4 (2) 類欄位 `override_ini` 的 value)。
        分類:`[rel-escape]` behavior-red;`[win-abs]` / `[posix-abs]` regression-lock(以本機 Windows 為準)。

        `-o cache_dir=<路徑形狀>` ⇒ 持久化行不含 `e3p-user`。
        TARGET 上 `[rel-escape]` 失敗的原因:`<TARGET>:.claude/hooks/redlight.py:593-594` 只有 `os.path.isabs` 為真才正規化。
        `[win-abs]` 在 POSIX 上同樣會紅(平台相依)。
        """
        _d_committed_root(tmp_path)
        _e_run(tmp_path, monkeypatch,
               option=_e_option(override_ini=["strict_markers=true", "cache_dir=" + shape.format("c")]))
        line = _e_persisted_line(tmp_path)
        assert _E_USER not in line, line

    def test_e3p_non_path_override_values_are_persisted_verbatim(self, tmp_path, monkeypatch):
        """E3p-4(〈三十五〉4 (2):key 一律原樣;非路徑 value 一律原樣)。分類:regression-lock。

        `override_ini` 全是非路徑值(含帶 `/` 的 glob `tests/test_*.py`)⇒ 持久化值逐字相等。
        """
        _d_committed_root(tmp_path)
        values = ["strict_markers=true", "python_functions=test_b", "python_files=tests/test_*.py"]
        run = _e_run(tmp_path, monkeypatch, option=_e_option(override_ini=list(values)))
        assert run["completeness"]["override_ini"] == values, run["completeness"]

    def test_e3p_non_path_plugin_names_are_persisted_verbatim(self, tmp_path, monkeypatch):
        """E3p-5(〈三十五〉4 名稱欄位:符合 `[A-Za-z0-9_.-]+`(含數字 id)者原樣)。分類:regression-lock。

        `blocked` 為 `cacheprovider` / `pytest_cacheprovider`;`plugins` 含 `main`、數字 id、`anyio`
        ⇒ 持久化名稱逐字相等。
        """
        _d_committed_root(tmp_path)
        run = _e_run(tmp_path, monkeypatch, blocked=("cacheprovider", "pytest_cacheprovider"))
        comp = run["completeness"]
        assert comp["blocked"] == ["cacheprovider", "pytest_cacheprovider"], comp
        names = [p["name"] for p in comp["plugins"]]
        for expected in ("main", "anyio", "cacheprovider", "pytest_cacheprovider"):
            assert expected in names, names
        assert any(n.isdigit() for n in names), names

    def test_e3p_a_root_relative_config_file_option_is_persisted_as_given(self, tmp_path, monkeypatch):
        """E3p-6(〈三十五〉4 (1) 類欄位:root 內的相對路徑以 invocation dir(= root)解析後不變)。
        分類:regression-lock。

        `-c alt.toml` ⇒ 持久化的 `inifilename == "alt.toml"`。
        """
        _d_committed_root(tmp_path)
        run = _e_run(tmp_path, monkeypatch, option=_e_option(inifilename="alt.toml"))
        assert run["completeness"]["inifilename"] == "alt.toml", run["completeness"]


# ─────────────────────────────────────────────────────────────────────────────
# 票 145 Station 3f 紅燈 —— `--pdb`(xix)與 S5e-F2 / F3 / F4
#
# 合約:票 145〈三十九〉39.3、〈四十一〉41.1。規劃:docs/audits/2026-10-03-m1a-station3f-redlight-plan.md P7。
# 下文 `<TARGET>` = 0139a7e803fc2d41eb354f1196a6206cfe304701(與 BASELINE e0459be4 之間產品碼相同)。
#
# driver 原則(沿用 3c-1b / 3d / 3e):
#   - 每次模擬執行載入全新的 conftest(`_isolated_conftest`);tmp root 是真的 git repo(`_d_committed_root`)。
#   - **防錯欄位**(〈四十一〉41.1 第 2 點):R3 / R4 / R5 的 `config.option` 是本次 session 的 pytest parser
#     (`pytestconfig._parser.parse_known_args(...)`)解析出的 namespace —— dest 與預設值都是 pytest 9.1.1 自己的,
#     不是測試自造的同名屬性。只呼叫 argparse,不執行巢狀 session、不觸發 `pytest_configure`。
#   - **平台語意模擬**(〈四十一〉41.1 第 4 點):R9–R12 以 `monkeypatch.setattr(redlight, "os", _FOs(...))`
#     只替換 **redlight 模組所見的** `os`;`path` 換成 `posixpath` / `ntpath`,其他屬性轉給真的 `os`。不改全域。
#   - 單點測試在同一支測試內放對照組。
# 本段 helper 全部新寫;既有 helper(`_isolated_conftest` / `_d_committed_root` / `_d_option` / `_d_plugins` /
# `_DConfig` / `_DInvocationParams` / `_e_run` / `_e_option` / `_e_coverage` / `_e_persisted_line` 等)只呼叫、不修改。
# ─────────────────────────────────────────────────────────────────────────────

import ntpath as _f_ntpath
import os as _f_real_os
import posixpath as _f_posixpath

_F_USER = "e3p-user"


class _FOs(object):
    """redlight 模組所見的 `os` 替身:`path` 由測試指定,其他屬性一律轉給真的 `os`。"""

    def __init__(self, pathmod):
        self.path = pathmod

    def __getattr__(self, name):
        return getattr(_f_real_os, name)


def _f_parse(pytestconfig, args):
    """本次 session 的 pytest parser 解析 `args` ⇒ namespace(pytest 真正的 dest 與預設值)。"""
    return pytestconfig._parser.parse_known_args(list(args))


def _f_run(tmp_path, monkeypatch, option, from_parent=False):
    """一次模擬執行(全新 conftest;`_D_FULL` 全收集、全 passed、exit 0;其他事實同固定全套)。

    `from_parent` ⇒ 從 root 的上一層執行 `python -X utf8 -m pytest -q <root 目錄名>`:
    `config.args == [<root 目錄名>]`、`invocation_params.dir` = root 的上一層(rootdir / inipath 不變)。
    回傳**最後一筆** session。"""
    def hook(name):
        return getattr(c, name, None) or (lambda *a, **k: None)

    root = pathlib.Path(str(tmp_path))
    selected = [n for ids in _D_FULL.values() for n in ids]
    c = _isolated_conftest(monkeypatch, tmp_path)
    for path in sorted(_D_FULL):
        report = _CCollectReport(path, [_c_item(n) for n in _D_FULL[path]])
        _c_call_collect_wrapper(c, _c_file(tmp_path, path), report)
        hook("pytest_collectreport")(report)
    config = _DConfig(tmp_path, option, _d_plugins(c, tmp_path))
    if from_parent:
        config.args = [root.name]
        config.args_source = pytest.Config.ArgsSource.ARGS
        config.invocation_params = _DInvocationParams(("-q", root.name), root.parent)
    session = _CompletenessSession([_c_item(n) for n in selected], config)
    hook("pytest_collection_finish")(session)
    for nodeid in selected:
        for rep in _c_reports(nodeid, "passed"):
            hook("pytest_runtest_logreport")(rep)
    hook("pytest_sessionfinish")(session, 0)
    runs = redlight.load_runs(str(tmp_path))
    assert runs, runs
    return runs[-1]


class TestDebuggerModeCoverage:

    def test_f3p_pdb_alone_is_not_full_coverage(self, tmp_path, monkeypatch):
        """R1(〈三十九〉39.3 第 3 點 (xix);S5e-F1)。分類:behavior-red。

        對照組:`usepdb=False`、其他事實同固定全套 ⇒ `"true"`。破壞組:只把 `usepdb` 設為 True(`--pdb`)
        ⇒ 不得為 `"true"`。
        TARGET 上失敗的原因:`<TARGET>:.claude/hooks/redlight.py:462-465` 的 `COMPLETENESS_OPTIONS` 沒有 usepdb,
        `:795-802` 沒有對應條件 ⇒ `:820` 回 `"true"`。
        """
        _d_committed_root(tmp_path)
        control = _e_coverage(tmp_path, monkeypatch, option=_e_option(usepdb=False))
        broken = _e_coverage(tmp_path, monkeypatch, option=_e_option(usepdb=True))
        assert control == "true", control
        assert broken != "true", broken

    @pytest.mark.parametrize("shape", ["missing", "str"])
    def test_f3p_a_missing_or_malformed_usepdb_fact_is_not_full_coverage(self, tmp_path, monkeypatch, shape):
        """R2(〈三十九〉39.3 第 3 點:缺欄或型別錯 ⇒ 不得為 "true";〈四十一〉41.1 第 7 點)。分類:behavior-red。

        對照組:`usepdb=False` ⇒ `"true"`。破壞組:`[missing]` option 沒有 `usepdb` 屬性;
        `[str]` `usepdb == "False"`(字串)⇒ 不得為 `"true"`。
        TARGET 上失敗的原因:同 R1(`<TARGET>:.claude/hooks/redlight.py:462-465`;`:820`)。
        """
        _d_committed_root(tmp_path)
        control = _e_coverage(tmp_path, monkeypatch, option=_e_option(usepdb=False))
        if shape == "missing":
            option = _d_option(missing=("usepdb",), runxfail=False, pythonwarnings=None, trace=False)
        else:
            option = _e_option(usepdb="False")
        broken = _e_coverage(tmp_path, monkeypatch, option=option)
        assert control == "true", control
        assert broken != "true", broken

    def test_f3p_the_producer_records_usepdb_from_the_pytest_parser(self, tmp_path, monkeypatch, pytestconfig):
        """R3(防錯欄位;〈四十一〉41.1 第 2 點)。分類:behavior-red。

        option 由本次 session 的 pytest parser 解析:`["--strict-markers", "--pdb"]` ⇒ 持久化的
        `options["usepdb"] is True`;`["--strict-markers"]` ⇒ `is False`。鎖住「producer 讀的是 pytest 真正的 dest」。
        TARGET 上失敗的原因:`<TARGET>:tests/conftest.py:369-370` 只記 `COMPLETENESS_OPTIONS`
        (`<TARGET>:.claude/hooks/redlight.py:462-465`)的鍵,沒有 usepdb。
        """
        _d_committed_root(tmp_path)
        with_pdb = _f_parse(pytestconfig, ["--strict-markers", "--pdb"])
        without = _f_parse(pytestconfig, ["--strict-markers"])
        assert with_pdb.usepdb is True and without.usepdb is False, (with_pdb, without)
        got_pdb = (_e_run(tmp_path, monkeypatch, option=with_pdb).get("completeness") or {}).get("options") or {}
        got_plain = (_e_run(tmp_path, monkeypatch, option=without).get("completeness") or {}).get("options") or {}
        assert got_pdb.get("usepdb") is True, got_pdb
        assert got_plain.get("usepdb") is False, got_plain

    def test_f3p_pdb_parsed_by_pytest_is_not_full_coverage(self, tmp_path, monkeypatch, pytestconfig):
        """R4(防錯欄位的判定版;(xix))。分類:behavior-red。

        對照組:pytest parser 解析 `["--strict-markers"]`(等同已提交 addopts 帶來的 override)⇒ `"true"`。
        破壞組:解析 `["--strict-markers", "--pdb"]` ⇒ 不得為 `"true"`。
        TARGET 上失敗的原因:同 R1(`<TARGET>:.claude/hooks/redlight.py:820`)。
        """
        _d_committed_root(tmp_path)
        control = _e_coverage(tmp_path, monkeypatch, option=_f_parse(pytestconfig, ["--strict-markers"]))
        broken = _e_coverage(tmp_path, monkeypatch,
                             option=_f_parse(pytestconfig, ["--strict-markers", "--pdb"]))
        assert control == "true", control
        assert broken != "true", broken

    def test_f3c_pdbcls_alone_does_not_lower_authority(self, tmp_path, monkeypatch, pytestconfig):
        """R5(〈四十一〉41.1 第 1 點:usepdb_cls 不加入 (xix))。分類:regression-lock。

        pytest parser 解析 `["--strict-markers", "--pdbcls=pdb:Pdb"]`:`usepdb_cls == ("pdb", "Pdb")`、`usepdb` False
        ⇒ 仍為 `"true"`(規劃檔 P2:`usepdb_cls` 只在 debugger 被建立時才讀,`_pytest/debugging.py:117`)。
        """
        _d_committed_root(tmp_path)
        option = _f_parse(pytestconfig, ["--strict-markers", "--pdbcls=pdb:Pdb"])
        assert tuple(option.usepdb_cls) == ("pdb", "Pdb") and option.usepdb is False, option
        got = _e_coverage(tmp_path, monkeypatch, option=option)
        assert got == "true", got


class TestOverrideBaseCoverage:

    def test_f3o_an_invocation_dir_outside_the_root_keeps_non_path_override_values(self, tmp_path, monkeypatch):
        """R6(S5e-F2;〈四十一〉41.1 第 3 點:(2) 類「越出 root」以 root 為基準)。分類:behavior-red。

        對照組:從 root 執行 ⇒ 持久化 `override_ini == ["strict_markers=true"]`。破壞組:從 root 的上一層執行
        (`invocation_params.dir` = 上一層)⇒ 仍須為 `["strict_markers=true"]`(`true` 不是路徑,不得改寫)。
        TARGET 上失敗的原因:`<TARGET>:tests/conftest.py:378-379` 以 invocation dir 為基準,
        `<TARGET>:.claude/hooks/redlight.py:655-656` 把 `true` 判為越界 ⇒ `strict_markers=<outside>`。
        """
        _d_committed_root(tmp_path)
        control = _f_run(tmp_path, monkeypatch, _e_option(usepdb=False))
        from_parent = _f_run(tmp_path, monkeypatch, _e_option(usepdb=False), from_parent=True)
        assert control["completeness"]["override_ini"] == ["strict_markers=true"], control["completeness"]
        assert from_parent["completeness"]["override_ini"] == ["strict_markers=true"], from_parent["completeness"]

    def test_f3o_the_fixed_command_from_the_parent_dir_is_full_coverage(self, tmp_path, monkeypatch):
        """R7(S5e-F2)。分類:behavior-red。

        對照組:從 root 執行固定全套 ⇒ `"true"`。破壞組:從 root 的上一層執行 `pytest -q <root 目錄名>`
        (位置參數經 `_normalize_arg` 得 `.`)、其他事實同固定全套 ⇒ 仍須為 `"true"`。
        情境斷言:兩筆 session 的 `invocation.args` 分別為 `["tests"]` 與 `["."]`。
        TARGET 上失敗的原因:R6 的改寫使 `<TARGET>:.claude/hooks/redlight.py:784` 不相等 ⇒ unknown。
        """
        _d_committed_root(tmp_path)
        control = _f_run(tmp_path, monkeypatch, _e_option(usepdb=False))
        from_parent = _f_run(tmp_path, monkeypatch, _e_option(usepdb=False), from_parent=True)
        assert control["invocation"]["args"] == ["tests"], control["invocation"]
        assert from_parent["invocation"]["args"] == ["."], from_parent["invocation"]
        got_control = redlight.file_coverage(control, "tests/test_x.py")
        got_parent = redlight.file_coverage(from_parent, "tests/test_x.py")
        assert got_control == "true", got_control
        assert got_parent == "true", got_parent

    def test_f3o_an_escaping_relative_override_is_outside_from_the_parent_dir(self, tmp_path, monkeypatch):
        """R8(S5e-F2 修正後仍不洩漏)。分類:regression-lock。

        從 root 的上一層執行,`override_ini` 另有 `cache_dir=../../e3p-user/c`(以 root 為基準也越界)
        ⇒ 持久化行不含 `e3p-user`。
        """
        _d_committed_root(tmp_path)
        _f_run(tmp_path, monkeypatch,
               _e_option(usepdb=False, override_ini=["strict_markers=true", "cache_dir=../../" + _F_USER + "/c"]),
               from_parent=True)
        line = _e_persisted_line(tmp_path)
        assert _F_USER not in line, line


# P5 的 G3 輸入(「混用分隔符、會越界」那一列由 R9 / R10 負責)
_F_G3_POSIX = [
    pytest.param(r"C:\x", "<outside>", id="win-drive-backslash"),
    pytest.param("C:/x", "<outside>", id="win-drive-slash"),
    pytest.param("D:rel", "<outside>", id="drive-relative"),
    pytest.param(r"\\server\share\x", "<outside>", id="unc"),
    pytest.param("\\\\?\\C:\\x", "<outside>", id="device"),
    pytest.param("/etc/x", "<outside>", id="posix-abs"),
    pytest.param("../../x", "<outside>", id="rel-escape"),
    pytest.param("sub/x", "sub/x", id="rel-inside"),
    pytest.param(r"sub\y/z", "sub/y/z", id="mixed-inside"),
]

_F_G3_WINDOWS = _F_G3_POSIX + [
    pytest.param(r"D:\x", "<outside>", id="cross-drive"),
]

_F_POSIX_ROOT = "/home/u/repo"
_F_WINDOWS_ROOT = r"C:\r\repo"


class TestPlatformIndependentNormalization:

    @pytest.mark.parametrize("field", ["override", "config-file"])
    def test_f3s_a_backslash_escape_is_outside_under_posix_semantics(self, monkeypatch, field):
        """R9 / R10(S5e-F3;〈四十一〉41.1 第 4 點)。分類:behavior-red。

        以 POSIX 語意(redlight 所見的 `os.path` = `posixpath`)正規化 `a\\..\\..\\..\\e3p-user\\…`(混用分隔符、越出 root):
        `[override]` ⇒ `normalize_overrides` 的結果不含 `e3p-user`;`[config-file]` ⇒ `normalize_config_path` 為 `<outside>`。
        TARGET 上失敗的原因:`<TARGET>:.claude/hooks/redlight.py:561-563` 先以 posixpath join / normpath(看不到反斜線的 `..`),
        `:566` relpath 之後才換分隔符 ⇒ `a/../../../e3p-user/…` 不以 `../` 開頭;override 另在 `:655-657` 保留原字串。
        """
        monkeypatch.setattr(redlight, "os", _FOs(_f_posixpath))
        if field == "override":
            got = redlight.normalize_overrides(["cache_dir=a\\..\\..\\..\\" + _F_USER + "\\c"],
                                               _F_POSIX_ROOT, _F_POSIX_ROOT)
            assert got is not None and all(_F_USER not in v for v in got), got
        else:
            got = redlight.normalize_config_path("a\\..\\..\\..\\" + _F_USER + "\\alt.toml",
                                                 _F_POSIX_ROOT, _F_POSIX_ROOT)
            assert got == redlight.OUTSIDE, got

    @pytest.mark.parametrize("value, expected", _F_G3_POSIX)
    def test_f3s_g3_inputs_under_posix_semantics(self, monkeypatch, value, expected):
        """R11(規劃檔 P5 表 POSIX 欄)。分類:regression-lock。

        以 POSIX 語意呼叫 `normalize_config_path(value, root, root)`((1) 類)⇒ 預期落帳值。
        """
        monkeypatch.setattr(redlight, "os", _FOs(_f_posixpath))
        got = redlight.normalize_config_path(value, _F_POSIX_ROOT, _F_POSIX_ROOT)
        assert got == expected, (value, got)

    @pytest.mark.parametrize("value, expected", _F_G3_WINDOWS)
    def test_f3s_g3_inputs_under_windows_semantics(self, monkeypatch, value, expected):
        """R12(規劃檔 P5 表 Windows 欄)。分類:regression-lock。

        以 Windows 語意(redlight 所見的 `os.path` = `ntpath`)呼叫 `normalize_config_path(value, root, root)` ⇒ 預期落帳值。
        `posix-abs` 依賴 Python 3.11 的 `ntpath.isabs("/x")` 為真(`ntpath.py:98-102`)。
        """
        monkeypatch.setattr(redlight, "os", _FOs(_f_ntpath))
        got = redlight.normalize_config_path(value, _F_WINDOWS_ROOT, _F_WINDOWS_ROOT)
        assert got == expected, (value, got)

    def test_f3s_a_backslash_escape_override_never_persists_a_path(self, tmp_path, monkeypatch):
        """R13(S5e-F3 的真實平台 producer 版)。分類:regression-lock(本機 Windows;POSIX 上為紅)。

        經真實 conftest producer、在本機平台上:`override_ini` 含 `cache_dir=a\\..\\..\\..\\e3p-user\\c`
        ⇒ 持久化行不含 `e3p-user`。
        """
        _d_committed_root(tmp_path)
        _e_run(tmp_path, monkeypatch,
               option=_e_option(usepdb=False,
                                override_ini=["strict_markers=true",
                                              "cache_dir=a\\..\\..\\..\\" + _F_USER + "\\c"]))
        line = _e_persisted_line(tmp_path)
        assert _F_USER not in line, line


class TestIdentifierFullMatch:

    def test_f3i_a_plugin_name_with_a_trailing_newline_is_not_persisted_verbatim(self, tmp_path, monkeypatch):
        """R14(S5e-F4)。分類:behavior-red。

        對照組:`-p no:abc` ⇒ 持久化 `blocked == ["abc"]`。破壞組:`-p no:abc\\n`(結尾帶換行)
        ⇒ 持久化 `blocked == ["<non-identifier>"]`(合約字元集 `[A-Za-z0-9_.-]+` 不含換行)。
        TARGET 上失敗的原因:`<TARGET>:.claude/hooks/redlight.py:540` 的 `$` 配 `:582` 的 `match`
        會匹配結尾換行之前 ⇒ 原樣 `"abc\\n"`。
        """
        _d_committed_root(tmp_path)
        control = _e_run(tmp_path, monkeypatch, blocked=("abc",))
        broken = _e_run(tmp_path, monkeypatch, blocked=("abc\n",))
        assert control["completeness"]["blocked"] == ["abc"], control["completeness"]
        assert broken["completeness"]["blocked"] == [redlight.NON_IDENTIFIER], broken["completeness"]


# ─────────────────────────────────────────────────────────────────────────────
# 票 145 Station 3g 紅燈 —— Host evidence policy(〈四十六〉46.4、〈四十八〉48.1)
#
# 合約:票 145〈四十八〉48.1(Jeff 對 S3g-0 規劃檔 P8 的裁決)。規劃:docs/audits/2026-10-03-m1a-station3g-redlight-plan.md P3、P6。
# 下文 `<BASELINE>` = 560f618560ddac1a34e0e835b99a1e3a5cc7eda5(S3G0;產品碼與 S6-1 faf7cb4 相同)。
#
# 介面(本刀定稿;語意依規劃檔 P3):
#   - canonical path `.agents/evidence-policy.json`(框架常數,不可由 policy 指定);
#   - schema `"monkeyleash.evidence-policy"` version 1;欄位全部必填、不得有多餘鍵:
#     `config_file` / `committed_overrides` / `python_versions` / `pytest_versions` / `dists`;
#   - producer 在 session 的 `completeness["evidence_policy"]` 記 `{"path", "head", "worktree", "schema", "version", "policy"}`,
#     內容由 HEAD committed blob 解析;worktree 只做 identity 比對;
#   - 框架推導函式 `redlight.addopts_overrides(addopts)`:已提交 addopts → override 清單(pytest 9.1.1 的對應)。
#
# driver 原則(沿用 3c-1b / 3d / 3e / 3f):
#   - 每次模擬執行載入全新 conftest(`_isolated_conftest`);tmp root 是**真的** git repo,policy 檔**真的**提交 / 修改;
#   - **版本事實一律固定**(〈四十八〉48.1 第 5 點):conftest 所見的 `sys.version_info` 為 3.11、`pytest.__version__` 為 9.1.1,
#     除非該案例本身就在測版本 —— 本段的正控不依賴執行它的直譯器;
#   - 需要兩種 repo 狀態的案例,對照組與破壞組各用 `tmp_path` 底下一個子目錄當 root;
#   - 單點測試在同一支測試內放對照組。
# 本段 helper 全部新寫;既有 helper(`_isolated_conftest` / `_d_plugins` / `_d_drive` / `_D_FULL` / `_e_option` /
# `_e_sys` / `_EVersion` 等)只呼叫、不修改。
# ─────────────────────────────────────────────────────────────────────────────

_G_POLICY_FILE = ".agents/evidence-policy.json"
_G_SCHEMA = "monkeyleash.evidence-policy"
_G_FIXED_ADDOPTS = "-ra --strict-markers"


def _g_policy(**overrides):
    """與 agent-gates 現行常數一致、且在能力邊界之內的 policy(dict)。"""
    policy = {
        "schema": _G_SCHEMA,
        "version": 1,
        "config_file": "pyproject.toml",
        "committed_overrides": ["strict_markers=true"],
        "python_versions": ["3.11"],
        "pytest_versions": ["9.1.1"],
        "dists": [["anyio", "4.15.0"]],
    }
    policy.update(overrides)
    return policy


def _g_policy_text(policy):
    return json.dumps(policy, ensure_ascii=False, indent=2) + "\n"


def _g_write(root, rel, text):
    p = pathlib.Path(str(root)) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    with io.open(str(p), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _g_root(root, policy_text=None, commit_policy=True, addopts=_G_FIXED_ADDOPTS,
            policy_path=_G_POLICY_FILE, extra_files=None):
    """在 `root` 建真的 git repo:提交 `pyproject.toml`(addopts 由參數決定)、root conftest(真檔內容)、
    `extra_files`;`policy_text` 不為 None ⇒ 寫到 `policy_path`,`commit_policy` 為真才一起提交。"""
    root = pathlib.Path(str(root))
    root.mkdir(parents=True, exist_ok=True)
    pyproject = u'[tool.pytest.ini_options]\ntestpaths = ["tests"]\n'
    if addopts is not None:
        pyproject += u'addopts = "%s"\n' % addopts
    _g_write(root, "pyproject.toml", pyproject)
    conftest = root / "tests" / "conftest.py"
    conftest.parent.mkdir(parents=True, exist_ok=True)
    conftest.write_bytes((ROOT / "tests" / "conftest.py").read_bytes())
    tracked = ["pyproject.toml", "tests/conftest.py"]
    for rel, text in (extra_files or {}).items():
        _g_write(root, rel, text)
        tracked.append(rel)
    if policy_text is not None:
        _g_write(root, policy_path, policy_text)
        if commit_policy:
            tracked.append(policy_path)
    _d_git(root, "init", "-q")
    _d_git(root, "config", "user.email", "t@example.invalid")
    _d_git(root, "config", "user.name", "t")
    _d_git(root, "add", *tracked)
    _d_git(root, "commit", "-q", "-m", "baseline")
    return root


def _g_default_root(root):
    """提交了合法、與執行環境一致的 policy 的 repo(正控用)。"""
    return _g_root(root, policy_text=_g_policy_text(_g_policy()))


def _g_run(root, monkeypatch, option=None, python=(3, 11), pytest_version="9.1.1",
           anyio_version="4.15.0", inipath="pyproject.toml", ini=None):
    """一次模擬執行(全新 conftest;`_D_FULL` 全收集、全 passed、exit 0;其他事實同固定全套)。
    版本事實固定為參數值(預設 3.11 / 9.1.1 / anyio 4.15.0)。回傳**最後一筆** session。"""
    root = pathlib.Path(str(root))
    selected = [n for ids in _D_FULL.values() for n in ids]
    c = _isolated_conftest(monkeypatch, root)
    monkeypatch.setattr(c, "sys", _e_sys(optimize=0, version_info=_EVersion(python[0], python[1], 0, "final", 0)),
                        raising=False)
    monkeypatch.setattr(pytest, "__version__", pytest_version)
    pm = _d_plugins(c, root, anyio_version=anyio_version)
    _d_drive(c, root, _D_FULL, selected, dict((n, "passed") for n in selected),
             option=option if option is not None else _e_option(usepdb=False), pm=pm,
             inipath=inipath, ini=ini)
    runs = redlight.load_runs(str(root))
    assert runs, runs
    return runs[-1]


def _g_coverage(root, monkeypatch, **kw):
    return redlight.file_coverage(_g_run(root, monkeypatch, **kw), "tests/test_x.py")


def _g_control(tmp_path, monkeypatch):
    """對照組:`tmp_path/control` 是提交了合法 policy 的 repo,固定全套 ⇒ 應為 `"true"`。"""
    return _g_coverage(_g_default_root(tmp_path / "control"), monkeypatch)


def _g_without(policy, key):
    out = dict(policy)
    out.pop(key)
    return out


# 規劃檔 P6 #2–#5:policy 自身的 HEAD / worktree integrity 不成立的四種狀態。
_G_UNCOMMITTED_STATES = ["worktree-only", "worktree-differs", "staged-only", "deleted-in-worktree"]

# 規劃檔 P6 #6–#10:HEAD 與 worktree 一致,但文件本身看不懂。
_G_UNKNOWN_DOCUMENTS = [
    pytest.param(u"{not json\n", id="malformed-json"),
    pytest.param(_g_policy_text(_g_policy(schema="other.evidence-policy")), id="unknown-schema"),
    pytest.param(_g_policy_text(_g_policy(version=2)), id="unknown-version"),
    pytest.param(_g_policy_text(_g_policy(location=".agents/elsewhere.json")), id="unknown-key"),
    pytest.param(_g_policy_text(_g_without(_g_policy(), "dists")), id="missing-field"),
]


class TestEvidencePolicyBootstrap:

    def test_g3_a_repo_without_a_policy_is_not_full_coverage(self, tmp_path, monkeypatch):
        """#1(〈四十六〉46.4 第 3 點:缺少 host policy 不得解讀成可信;規劃檔 P3 I-3 第 2 步)。分類:behavior-red。

        對照組:提交了合法 policy 的 repo ⇒ `"true"`。破壞組:同樣的已提交設定與 conftest,但 repo 從未有 policy
        (淨室安裝後、尚未初始化的狀態)⇒ 不得為 `"true"`。
        BASELINE 上失敗的原因:`<BASELINE>:.claude/hooks/redlight.py:786-833` 不讀任何 policy ⇒ `:833` 回 `"true"`。
        """
        control = _g_control(tmp_path, monkeypatch)
        broken = _g_coverage(_g_root(tmp_path / "broken"), monkeypatch)
        assert control == "true", control
        assert broken != "true", broken

    @pytest.mark.parametrize("state", _G_UNCOMMITTED_STATES)
    def test_g3_an_uncommitted_policy_state_is_not_full_coverage(self, tmp_path, monkeypatch, state):
        """#2–#5(〈四十六〉46.4 第 4 點 負二 / 負三、第 6 點;規劃檔 P3 I-3 第 2、4 步)。分類:behavior-red。

        對照組:提交了合法 policy 的 repo ⇒ `"true"`。破壞組(policy 內容皆為同一份合法 policy):
          - `[worktree-only]`:policy 只在工作樹,HEAD 從未有它(負三)⇒ 不得為 `"true"`;
          - `[worktree-differs]`:HEAD 有 policy,工作樹內容不同(本地改了未 commit)(負二)⇒ 不得為 `"true"`;
          - `[staged-only]`:policy 已 `git add` 但未 commit ⇒ 不得為 `"true"`;
          - `[deleted-in-worktree]`:HEAD 有 policy,工作樹把它刪了 ⇒ 不得為 `"true"`。
        BASELINE 上失敗的原因:同 #1(`<BASELINE>:.claude/hooks/redlight.py:833`)。
        """
        control = _g_control(tmp_path, monkeypatch)
        text = _g_policy_text(_g_policy())
        broken_root = tmp_path / "broken"
        if state == "worktree-only":
            _g_root(broken_root, policy_text=text, commit_policy=False)
        elif state == "staged-only":
            _g_root(broken_root, policy_text=text, commit_policy=False)
            _d_git(broken_root, "add", _G_POLICY_FILE)
        else:
            _g_root(broken_root, policy_text=text)
            policy = broken_root / _G_POLICY_FILE
            if state == "worktree-differs":
                _g_write(broken_root, _G_POLICY_FILE, text + u"\n")
            else:
                policy.unlink()
        broken = _g_coverage(broken_root, monkeypatch)
        assert control == "true", control
        assert broken != "true", broken

    @pytest.mark.parametrize("text", _G_UNKNOWN_DOCUMENTS)
    def test_g3_an_unknown_policy_document_is_not_full_coverage(self, tmp_path, monkeypatch, text):
        """#6–#10(〈四十六〉46.4 第 6 點:schema / version 未知 ⇒ 只能 unknown;規劃檔 P3 I-1、I-2、I-3 第 5 步)。
        分類:behavior-red。

        對照組:提交了合法 policy 的 repo ⇒ `"true"`。破壞組:policy 已提交且工作樹 = HEAD,但內容為
        `[malformed-json]` 不是 JSON、`[unknown-schema]` schema 不是 `monkeyleash.evidence-policy`、
        `[unknown-version]` version 2、`[unknown-key]` 多一個自我指定位置的鍵 `location`(I-1)、
        `[missing-field]` 缺 `dists` ⇒ 不得為 `"true"`。
        BASELINE 上失敗的原因:同 #1(`<BASELINE>:.claude/hooks/redlight.py:833`)。
        """
        control = _g_control(tmp_path, monkeypatch)
        broken = _g_coverage(_g_root(tmp_path / "broken", policy_text=text), monkeypatch)
        assert control == "true", control
        assert broken != "true", broken

    def test_g3_a_policy_outside_the_canonical_path_is_not_full_coverage(self, tmp_path, monkeypatch):
        """#11(〈四十六〉46.4 第 6 點:canonical location 屬框架不變式;規劃檔 P3 I-1)。分類:behavior-red。

        對照組:policy 提交在 `.agents/evidence-policy.json` ⇒ `"true"`。破壞組:同一份合法 policy 只提交在
        repo 根的 `evidence-policy.json`(canonical path 沒有檔)⇒ 不得為 `"true"`。
        BASELINE 上失敗的原因:同 #1(`<BASELINE>:.claude/hooks/redlight.py:833`)。
        """
        control = _g_control(tmp_path, monkeypatch)
        broken = _g_coverage(_g_root(tmp_path / "broken", policy_text=_g_policy_text(_g_policy()),
                                     policy_path="evidence-policy.json"), monkeypatch)
        assert control == "true", control
        assert broken != "true", broken

    def test_g3_the_producer_records_the_policy_identity(self, tmp_path, monkeypatch):
        """#12(〈四十八〉48.1 第 2 點:producer 依 I-3 從 HEAD committed blob 解析並記入 session)。分類:behavior-red。

        對照組:repo 沒有 policy ⇒ `evidence_policy` 沒有 HEAD blob(整欄 None 或 `head` 為 None)。
        破壞組(主斷言):提交了合法 policy ⇒ 持久化的 `completeness["evidence_policy"]` 為
        `{"path": ".agents/evidence-policy.json", "head": <HEAD blob>, "worktree": <同一個 blob>,
        "schema": "monkeyleash.evidence-policy", "version": 1, "policy": <解析後內容>}`;
        `<HEAD blob>` 由測試自己以 `git rev-parse HEAD:<path>` 取得。
        BASELINE 上失敗的原因:`<BASELINE>:tests/conftest.py:368-387` 的 completeness 沒有 `evidence_policy` 欄。
        """
        none_run = _g_run(_g_root(tmp_path / "none"), monkeypatch)
        none_ep = (none_run.get("completeness") or {}).get("evidence_policy")
        root = _g_default_root(tmp_path / "with")
        head = _d_git(root, "rev-parse", "HEAD:" + _G_POLICY_FILE).stdout.decode("ascii").strip()
        run = _g_run(root, monkeypatch)
        ep = (run.get("completeness") or {}).get("evidence_policy")
        assert isinstance(ep, dict), run.get("completeness")
        assert ep.get("path") == _G_POLICY_FILE, ep
        assert ep.get("head") == head and ep.get("worktree") == head, (ep, head)
        assert ep.get("schema") == _G_SCHEMA and ep.get("version") == 1, ep
        assert ep.get("policy") == _g_policy(), ep
        assert none_ep is None or none_ep.get("head") is None, none_ep

    def test_g3_policy_content_is_not_read_from_the_worktree(self, tmp_path, monkeypatch):
        """#13(〈四十六〉46.4 第 6 點:worktree 只做 identity check,不作為 authority 內容來源;規劃檔 P3 I-3 第 5 步)。
        分類:regression-lock。

        提交了合法 policy;模擬執行期間,Python 層的 `open` / `io.open` 只要開 canonical path 就拋例外
        (`git hash-object` / `git cat-file` 由子行程自己讀,不受影響)⇒ 仍須為 `"true"`。
        前置控制:guard 確實擋得住對 canonical path 的 open。
        BASELINE 上通過:根本不讀 policy。上線後鎖住「內容只從 HEAD blob 來」。
        """
        import builtins
        root = _g_default_root(tmp_path / "root")
        policy_path = str(root / _G_POLICY_FILE)
        real_open = builtins.open

        def guarded(file, *args, **kwargs):
            if str(file).replace("\\", "/").endswith(_G_POLICY_FILE):
                raise OSError("worktree policy must not be read as authority content: %s" % file)
            return real_open(file, *args, **kwargs)

        with monkeypatch.context() as m:
            m.setattr(builtins, "open", guarded)
            m.setattr(io, "open", guarded)
            with pytest.raises(OSError):
                io.open(policy_path, encoding="utf-8")
            got = _g_coverage(root, monkeypatch)
        assert got == "true", got

    def test_g3_a_matching_committed_policy_is_full_coverage(self, tmp_path, monkeypatch):
        """#14(〈四十六〉46.4 第 3 點:宿主已提交 policy 且實際環境 == policy ⇒ 才可能 true;正二的單元版)。
        分類:regression-lock。

        提交了合法 policy(值 = 現行常數)、工作樹 = HEAD、版本事實 3.11 / 9.1.1 / anyio 4.15.0、
        `override_ini == ["strict_markers=true"]`、全收集、全 passed ⇒ `"true"`。
        """
        got = _g_coverage(_g_default_root(tmp_path / "root"), monkeypatch)
        assert got == "true", got


# 規劃檔 P6 #15–#18:(policy 的覆寫, 執行事實, 額外提交的檔)
_G_WIDENING = [
    pytest.param({"python_versions": ["3.11", "3.12"]}, {"python": (3, 12)}, None, id="python"),
    pytest.param({"pytest_versions": ["9.1.1", "9.2.0"]}, {"pytest_version": "9.2.0"}, None, id="pytest"),
    pytest.param({"dists": [["anyio", "4.15.0"], ["anyio", "9.9.9"]]}, {"anyio_version": "9.9.9"}, None, id="dist"),
    pytest.param({"config_file": "pytest.ini"}, {"inipath": "pytest.ini"},
                 {"pytest.ini": u"[pytest]\ntestpaths = tests\naddopts = -ra --strict-markers\n"}, id="config-file"),
]


class TestEvidencePolicyBoundary:

    @pytest.mark.parametrize("policy_overrides, run_kw, extra_files", _G_WIDENING)
    def test_g3_a_policy_cannot_widen_the_capability_boundary(self, tmp_path, monkeypatch,
                                                              policy_overrides, run_kw, extra_files):
        """#15–#18(〈四十六〉46.4 第 3 點:host policy 只能收窄,不能擴張;〈四十八〉48.1 第 3 點)。分類:regression-lock。

        對照組:合法 policy、環境在邊界內 ⇒ `"true"`。破壞組:policy 列出能力邊界外的值,且執行環境正是那個值 ——
        `[python]` 3.12、`[pytest]` 9.2.0、`[dist]` anyio 9.9.9、`[config-file]` `pytest.ini`(另提交該檔)⇒ 不得為 `"true"`。
        BASELINE 上通過:框架常數已擋下這四種環境(`<BASELINE>:.claude/hooks/redlight.py:793-794, 799-800, 808-809, 613`)。
        上線後鎖住「policy 不能把它們加回來」。
        """
        control = _g_control(tmp_path, monkeypatch)
        broken_root = _g_root(tmp_path / "broken", policy_text=_g_policy_text(_g_policy(**policy_overrides)),
                              extra_files=extra_files)
        broken = _g_coverage(broken_root, monkeypatch, **run_kw)
        assert control == "true", control
        assert broken != "true", broken

    @pytest.mark.parametrize("case", ["override", "narrowed-dist"])
    def test_g3_a_policy_environment_mismatch_is_not_full_coverage(self, tmp_path, monkeypatch, case):
        """#19–#20(〈四十六〉46.4 第 4 點 負一:policy / environment mismatch ⇒ unknown)。分類:behavior-red。

        對照組:合法 policy、固定全套 ⇒ `"true"`。破壞組:
          - `[override]`:已提交 addopts 為 `-ra`、policy `committed_overrides: []`(兩者自洽);
            執行時經 `PYTEST_ADDOPTS` 帶入 `--strict-markers` ⇒ `override_ini == ["strict_markers=true"]`(policy 未列)⇒ 不得為 `"true"`;
          - `[narrowed-dist]`:policy `dists: []`(宿主不接受 anyio);執行時 anyio 4.15.0 已載入 ⇒ 不得為 `"true"`。
        BASELINE 上失敗的原因:`<BASELINE>:.claude/hooks/redlight.py:795` 的比較對象是框架常數 `["strict_markers=true"]`、
        `:613` 的 `KNOWN_DISTS` 含 anyio 4.15.0 ⇒ `:833` 回 `"true"`。
        """
        control = _g_control(tmp_path, monkeypatch)
        if case == "override":
            broken_root = _g_root(tmp_path / "broken", addopts="-ra",
                                  policy_text=_g_policy_text(_g_policy(committed_overrides=[])))
        else:
            broken_root = _g_root(tmp_path / "broken", policy_text=_g_policy_text(_g_policy(dists=[])))
        broken = _g_coverage(broken_root, monkeypatch)
        assert control == "true", control
        assert broken != "true", broken


# 規劃檔 P6 #21–#25:已提交 addopts → override 清單(pytest 9.1.1:`_pytest/main.py:76-96` 的 OverrideIniAction 旗標、
# `_pytest/helpconfig.py:113-116` 的 `-o` / `--override-ini`;其他旗標不產生 override)
_G_DERIVATIONS = [
    pytest.param("-ra --strict-markers", ["strict_markers=true"], id="strict-markers"),
    pytest.param("--strict-config -q", ["strict_config=true"], id="strict-config"),
    pytest.param("-o python_files=check_*.py -oxfail_strict=true", ["python_files=check_*.py", "xfail_strict=true"],
                 id="o-flag"),
    pytest.param("--override-ini=cache_dir=.c --strict-markers", ["cache_dir=.c", "strict_markers=true"],
                 id="override-ini-eq"),
    pytest.param("", [], id="no-addopts"),
]


class TestAddoptsDerivation:

    @pytest.mark.parametrize("addopts, expected", _G_DERIVATIONS)
    def test_g3_overrides_are_derived_from_committed_addopts(self, addopts, expected):
        """#21–#25(〈四十八〉48.1 第 4 點:框架推導規則以 fixture 測)。分類:behavior-red。

        `redlight.addopts_overrides(addopts)` 依出現順序回傳 override 清單,必須恰等於預期。
        這裡驗的是**推導規則**(框架性質),不是「常數 ↔ 宿主設定」—— 後者在 tests/test_host_evidence_policy.py。
        BASELINE 上失敗的原因:`<BASELINE>:.claude/hooks/redlight.py` 沒有 `addopts_overrides`(只有常數 `:493`)。
        """
        derive = getattr(redlight, "addopts_overrides")
        assert derive(addopts) == expected, (addopts, derive(addopts))

    def test_g3_a_policy_disagreeing_with_the_committed_addopts_is_not_full_coverage(self, tmp_path, monkeypatch):
        """#26(〈四十八〉48.1 第 4 點:verdict 時機器鎖步 —— policy 必須與 HEAD 設定檔的 addopts 推導一致)。
        分類:behavior-red。

        對照組:已提交 addopts `-ra --strict-markers`、policy `["strict_markers=true"]` ⇒ `"true"`。
        破壞組:只改已提交 addopts 為 `-ra`(policy 與執行時 override 都仍是 `["strict_markers=true"]`,
        後者經 `PYTEST_ADDOPTS` 帶入)⇒ policy 與已提交設定不一致 ⇒ 不得為 `"true"`。
        BASELINE 上失敗的原因:`<BASELINE>:.claude/hooks/redlight.py:795` 只比框架常數,不讀已提交 addopts ⇒ `:833` 回 `"true"`。
        """
        control = _g_control(tmp_path, monkeypatch)
        broken = _g_coverage(_g_root(tmp_path / "broken", addopts="-ra",
                                     policy_text=_g_policy_text(_g_policy())), monkeypatch)
        assert control == "true", control
        assert broken != "true", broken


# ─────────────────────────────────────────────────────────────────────────────
# 票 145 Station 4g 補紅燈 —— 「沒有任何 override」的正控與「override 事實取不到」的鎖
#
# 成因:pytest 9.1.1 的 `-o` 是 `action="append"`、沒有 default(`_pytest/helpconfig.py:112-119`),
# 沒給任何 `-o` / OverrideIniAction 旗標時 `config.option.override_ini` 為 **None**(屬性存在)。
# 3g / 3g-1b 的正控都帶 `--strict-markers`,沒有一支走到這條路徑;S4G1 的淨室「正二」因此不成立
# (`.dev/reports/2026-10-04T213043Z-ticket145-station4g-s4g1-local-pass-cleanroom-pos2-fail.md`)。
# 裁決:修法 B(producer 先判欄位是否存在、再解讀值);A(consumer 把 None 當 [])否決。
# 既有 helper(`_g_root` / `_g_policy` / `_g_policy_text` / `_g_coverage` / `_e_option` / `_d_option`)只呼叫、不修改。
# ─────────────────────────────────────────────────────────────────────────────

class TestEvidencePolicyNoOverride:

    def test_g3_no_override_anywhere_is_full_coverage(self, tmp_path, monkeypatch):
        """T1。分類:behavior-red(在 S4G1 上必須失敗)。

        已提交 addopts `-ra`(推導出的 override 為 `[]`)、policy `committed_overrides: []`(兩者自洽)、
        執行時沒有任何 `-o`:pytest 明確表示「沒有 override」,`option.override_ini is None`(屬性存在)
        ⇒ 必須能取得 full coverage(`"true"`)。否則設定裡沒有 `-o` 類旗標的宿主永遠退不了紅。
        S4G1 上失敗的原因:`tests/conftest.py` 的 producer 把 None 原樣交給 `normalize_overrides`,
        落帳 `override_ini: null`;`.claude/hooks/redlight.py` 的 (viii) 比 `None != []` ⇒ unknown。
        """
        root = _g_root(tmp_path / "root", policy_text=_g_policy_text(_g_policy(committed_overrides=[])),
                       addopts="-ra")
        got = _g_coverage(root, monkeypatch, option=_e_option(usepdb=False, override_ini=None))
        assert got == "true", got

    def test_g3_a_missing_override_fact_is_not_full_coverage(self, tmp_path, monkeypatch):
        """T2。分類:regression-lock(在 S4G1 上必須通過)。

        與 T1 同一種佈置,但 `config.option` 根本沒有 `override_ini` 屬性 ⇒ 事實取不到 ⇒ 不得為 `"true"`。
        **事實取不到 ≠ 沒有 override**:鎖住修法 B 的語意,防止日後改成在 consumer 把 None 當 `[]`
        (修法 A;那會把「取不到」當成「確定沒有」⇒ fail-open)。
        """
        root = _g_root(tmp_path / "root", policy_text=_g_policy_text(_g_policy(committed_overrides=[])),
                       addopts="-ra")
        option = _d_option(missing=("override_ini",), runxfail=False, pythonwarnings=None, trace=False,
                           usepdb=False)
        got = _g_coverage(root, monkeypatch, option=option)
        assert got != "true", got


# ─────────────────────────────────────────────────────────────────────────────
# 票 145 Station 3h 補紅燈 —— S5g-F2:evidence root 必須就是 Git 最上層(〈五十三〉53.3 裁決 2、3)
#
# 成因:`git -C <root> rev-parse HEAD:<path>` 的 `<path>` 以 **Git 最上層**(tree 根)為基準,
# `git -C <root> hash-object <path>` 以 **root(cwd)** 為基準。root 不是最上層時,被驗證的 HEAD 物件與
# 實際使用的工作樹物件不是同一個邏輯路徑(identity 錯位),內容相同即可取得 `"true"`。
# 框架目前只支援「一個 host evidence root = 一個 Git 最上層」;monorepo 子專案作為 evidence root 屬另案,
# 巢狀獨立 repo 的情境不在本輪。
# 既有 helper(`_g_default_root` / `_g_coverage` / `_G_POLICY_FILE`)只呼叫、不修改。
# ─────────────────────────────────────────────────────────────────────────────

class TestEvidenceRootIsGitToplevel:

    def test_h3_a_parent_committed_policy_does_not_authorize_a_subdirectory_root(self, tmp_path, monkeypatch):
        """H1。分類:behavior-red(在 S5g-1 上必須失敗)。

        Git 最上層 `parent` 已提交合法 policy、`pyproject.toml`、`tests/conftest.py`;root = `parent/sub`,
        三份位元組相同的副本只在工作樹、從未提交於 `sub/` 底下。`sub` 的 canonical policy 從未提交
        ⇒ 不得為 `"true"`(〈四十六〉46.4 第 6 點、I-3:canonical policy 必須是 evidence root 對應路徑上、
        已提交的 HEAD blob)。
        S5g-1 上失敗的原因:`git rev-parse HEAD:<path>` 以最上層為基準、`git hash-object <path>` 以 root 為基準
        ⇒ 兩者指向 `parent/<path>` 與 `sub/<path>`,內容相同即 head == worktree ⇒ identity 錯位即可取得 `"true"`。
        """
        parent = _g_default_root(tmp_path / "parent")
        sub = parent / "sub"
        for rel in (_G_POLICY_FILE, "pyproject.toml", "tests/conftest.py"):
            dst = sub / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes((parent / rel).read_bytes())
        got = _g_coverage(sub, monkeypatch)
        assert got != "true", got

    def test_h3_a_git_toplevel_root_with_a_committed_policy_is_full_coverage(self, tmp_path, monkeypatch):
        """H2。分類:regression-lock(在 S5g-1 上必須通過)。

        root 本身就是 Git 最上層,policy 正常提交、worktree = HEAD ⇒ 仍為 `"true"`。
        鎖住 4h 的修正不得封死正常的最上層 host。
        """
        got = _g_coverage(_g_default_root(tmp_path / "root"), monkeypatch)
        assert got == "true", got


# ─────────────────────────────────────────────────────────────────────────────
# 票 145 Station 3i 補紅燈 —— S5h-F1 / S5h-F2:root 必須是 Git **工作樹**的最上層(〈五十七〉57.3 裁決 2、3)
#
# 4h 的 `_root_is_toplevel` 只看 `git rev-parse --show-prefix` 為空。但 `.git/` 內部或 bare repository 內
# 同樣滿足此條件,而該處並非工作樹:`HEAD:<path>` 證明的是 repository 內某個 tree 路徑,`hash-object <path>`
# 讀的是另一個 filesystem root 底下、Git 不對應任何 tree 路徑的檔 ⇒ identity 錯位 ⇒ 內容相同即可取得 `"true"`。
# root 必須是 Git 工作樹的最上層,不只是 repository context 中 prefix 恰為空的位置。
# 既有 helper(`_g_default_root` / `_g_coverage` / `_G_POLICY_FILE` / `_d_git` / `redlight.committed_blobs` /
# `redlight.BLOB_FILES`)只呼叫、不修改。
# ─────────────────────────────────────────────────────────────────────────────

class TestEvidenceRootIsInsideWorkTree:

    @staticmethod
    def _copy_into(parent, root, rels):
        """把 `parent` 底下的 `rels` 逐一以位元組複製到 `root` 底下(只寫工作樹,不 git add / commit)。"""
        for rel in rels:
            dst = root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes((parent / rel).read_bytes())

    def test_i3_a_root_inside_the_gitdir_is_not_full_coverage(self, tmp_path, monkeypatch):
        """I1。分類:behavior-red(在 S5h-1 上必須失敗)。

        Git 最上層 `parent` 已提交合法 policy、`pyproject.toml`、`tests/conftest.py`;root = `parent/.git`
        (gitdir 內部),三份位元組相同的副本只在 root 下、從未提交 ⇒ 不得為 `"true"`。
        S5h-1 上失敗的原因:在 `.git/` 內 `git rev-parse --show-prefix` 以 exit 0 輸出空行 ⇒ `_root_is_toplevel`
        True;但該處不是工作樹(`--is-inside-work-tree` 為 false),`HEAD:<path>` 與 `hash-object <path>`
        對應的不是同一邏輯路徑 ⇒ head == worktree ⇒ identity 錯位即可取得 `"true"`(S5h-F1)。
        """
        parent = _g_default_root(tmp_path / "parent")
        root = parent / ".git"
        self._copy_into(parent, root, (_G_POLICY_FILE, "pyproject.toml", "tests/conftest.py"))
        got = _g_coverage(root, monkeypatch)
        assert got != "true", got

    def test_i3_a_root_inside_a_bare_repository_is_not_full_coverage(self, tmp_path, monkeypatch):
        """I2。分類:behavior-red(在 S5h-1 上必須失敗)。

        以 `parent` 建 bare clone `bare.git`;root = `bare.git/proj`(bare repository 底下的普通子目錄,
        隱式 bare 探索),三份位元組相同的副本只在 root 下、從未提交 ⇒ 不得為 `"true"`。
        S5h-1 上失敗的原因:同 I1 —— bare 內 `--show-prefix` 為空但非工作樹,`HEAD:<path>` 與
        `hash-object <path>` 對應的不是同一邏輯路徑(S5h-F1)。
        """
        parent = _g_default_root(tmp_path / "parent")
        bare = tmp_path / "bare.git"
        _d_git(tmp_path, "clone", "-q", "--bare", str(parent), str(bare))
        root = bare / "proj"
        self._copy_into(parent, root, (_G_POLICY_FILE, "pyproject.toml", "tests/conftest.py"))
        got = _g_coverage(root, monkeypatch)
        assert got != "true", got

    def test_i3_committed_blobs_alone_is_fail_closed_for_a_subdirectory_root(self, tmp_path, monkeypatch):
        """I3。分類:regression-lock(在 S5h-1 上必須通過)。**不經 `evidence_policy_facts`**,直接呼叫
        `redlight.committed_blobs`。

        非法 root(`parent/sub`,只有 `pyproject.toml` 與 `tests/conftest.py` 的未提交副本):`BLOB_FILES`
        每一路徑皆 `{"worktree": None, "head": None}`;對照組 `committed_blobs(parent)`:每一路徑 worktree
        非空且 == head。
        目的:獨立證明 `committed_blobs` 那一半 fail-closed,不被 `evidence_policy_facts` 的 guard 間接遮蔽
        (S5h-F2:H1 只斷言 `!= "true"`,policy 那一半先回 None 就擋住了,(xi) 那一半有沒有擋看不出來)。
        """
        parent = _g_default_root(tmp_path / "parent")
        sub = parent / "sub"
        self._copy_into(parent, sub, ("pyproject.toml", "tests/conftest.py"))
        blobs = redlight.committed_blobs(str(sub))
        assert set(blobs) == set(redlight.BLOB_FILES), blobs
        assert all(v == {"worktree": None, "head": None} for v in blobs.values()), blobs
        control = redlight.committed_blobs(str(parent))
        assert all(v["worktree"] and v["worktree"] == v["head"] for v in control.values()), control


# ─────────────────────────────────────────────────────────────────────────────
# 票 145 Station 3j 補紅燈 —— S5i-F1 / S5i-F3:`_root_is_toplevel` 的 stdout contract(〈六十一〉61.3 裁決 2、3)
#
# `git rev-parse --is-inside-work-tree --show-prefix` 的 stdout 須**完整**等於 `b"true\n\n"`;不得拆行只看前兩行。
# `--show-prefix` 輸出未跳脫的原始路徑位元組 —— POSIX 上名稱以 LF 開頭的子目錄,prefix 的第一行為空,
# 拆行只看 `lines[1]` 的解析會把它誤判為最上層 ⇒ 重新打開 S5g-F2 的 identity 錯位(S5i-F1)。
# 既有 helper(`_g_default_root` / `_g_coverage` / `_G_POLICY_FILE` / `_d_git` / `redlight._root_is_toplevel`)
# 只呼叫、不修改。
# ─────────────────────────────────────────────────────────────────────────────

class TestRootIsToplevelContract:

    import sys

    @staticmethod
    def _copy_into(parent, root, rels):
        """把 `parent` 底下的 `rels` 逐一以位元組複製到 `root` 底下(只寫工作樹,不 git add / commit)。"""
        for rel in rels:
            dst = root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes((parent / rel).read_bytes())

    @pytest.mark.skipif(sys.platform == "win32",
                        reason="Windows 檔名不得含 LF;本案例由 POSIX 驗收證明(〈六十一〉61.3 裁決 2)")
    def test_j3_a_lf_prefixed_subdirectory_root_is_not_full_coverage(self, tmp_path, monkeypatch):
        """J1。分類:behavior-red(POSIX-only;在 S5i-1 上於 POSIX 必須失敗)。Windows 以 skipif 跳過
        (Jeff 特別核准:Windows 檔名模型無法合法建立該輸入,紅燈由裁決助手的 POSIX 驗收證明)。

        Git 最上層 `parent` 已提交合法 policy、`pyproject.toml`、`tests/conftest.py`;root = `parent/"\\nsub"`
        (名稱以 LF 開頭的子目錄),三份位元組相同的副本只在 root 下、從未提交 ⇒ 不得為 `"true"`。
        S5i-1 上失敗的原因:`--show-prefix` 輸出未跳脫的原始路徑位元組,stdout 為 `true\\n\\nsub/\\n`;
        4i 拆行後只看 `lines[1]`(為空)⇒ 誤判為最上層 ⇒ identity 錯位即可取得 `"true"`(S5i-F1)。
        """
        parent = _g_default_root(tmp_path / "parent")
        root = parent / "\nsub"
        self._copy_into(parent, root, (_G_POLICY_FILE, "pyproject.toml", "tests/conftest.py"))
        got = _g_coverage(root, monkeypatch)
        assert got != "true", got

    @pytest.mark.parametrize("layout, expected", [
        pytest.param("toplevel", True, id="toplevel"),
        pytest.param("subdir", False, id="subdir"),
        pytest.param("gitdir", False, id="gitdir"),
        pytest.param("bare", False, id="bare"),
    ])
    def test_j3_root_is_toplevel_follows_the_stdout_contract(self, tmp_path, layout, expected):
        """J2。分類:regression-lock(在 S5i-1 上必須通過)。直接鎖 `redlight._root_is_toplevel` 的 parser contract
        (S5i-F3 轉機器鎖):git 最上層 ⇒ True;普通子目錄 ⇒ False;`<最上層>/.git` ⇒ False;
        `<bare clone>/proj` ⇒ False。
        """
        parent = _g_default_root(tmp_path / "parent")
        if layout == "toplevel":
            root = parent
        elif layout == "subdir":
            root = parent / "sub"
            root.mkdir()
        elif layout == "gitdir":
            root = parent / ".git"
        else:
            bare = tmp_path / "bare.git"
            _d_git(tmp_path, "clone", "-q", "--bare", str(parent), str(bare))
            root = bare / "proj"
            root.mkdir()
        assert redlight._root_is_toplevel(str(root)) is expected


# ─────────────────────────────────────────────────────────────────────────────
# 票 145 Station 3j-1b 補紅燈 —— S5i-F1 解析層(Windows 可紅)
#
# 以 monkeypatch 替身供給「LF 開頭 prefix」的 stdout,不依賴檔案系統 —— Windows 檔名不得含 LF,
# J1(POSIX 端到端)在 Windows 被跳過,本機帳本因此沒有 R3 要的紅燈。J1b 與 J1 互補:J1 證明端到端形狀,
# J1b 在任何平台證明解析層。既有 helper(`redlight._root_is_toplevel`)只呼叫、不修改。
# ─────────────────────────────────────────────────────────────────────────────

class TestRootIsToplevelParser:

    def test_j3_a_lf_prefixed_show_prefix_stdout_is_not_toplevel(self, tmp_path, monkeypatch):
        """J1b。分類:behavior-red(在 S3J2 上必須失敗)。

        stdout `b"true\\n\\nsub/\\n"` 即 POSIX 上名稱以 LF 開頭的子目錄(`"\\nsub"`)所得:`--show-prefix`
        輸出未跳脫的原始路徑位元組。拆行只看前兩行(`lines[0] == b"true"`、`lines[1]` 為空)會誤判 True;
        修正後 stdout 須完整等於 `b"true\\n\\n"`(\\r\\n 正規化後)才為 True ⇒ 這裡必須是 False。
        另斷言呼叫的確是 `rev-parse --is-inside-work-tree --show-prefix`,替身沒有被別的指令吃掉。
        """
        import subprocess as _sp

        class _Proc:
            returncode = 0
            stdout = b"true\n\nsub/\n"
            stderr = b""

        calls = []

        def fake_run(args, **kw):
            calls.append(list(args))
            return _Proc()

        monkeypatch.setattr(_sp, "run", fake_run)
        assert redlight._root_is_toplevel(str(tmp_path)) is False
        assert calls and calls[0][-2:] == ["--is-inside-work-tree", "--show-prefix"], calls


# ─────────────────────────────────────────────────────────────────────────────
# 票 145 Station 3k 紅燈 —— 能力邊界 KNOWN_DISTS 納入 anyio 4.15.1(〈六十五〉65.5 裁決 A)
#
# 能力(KNOWN_DISTS)與宿主 policy 分開驗:K-a 鎖常數;K-b 正控 = 已提交、明確接受 4.15.1 的 policy
# + 4.15.1 的 plugin 事實 ⇒ "true";K-c / K-d 負控 = 宿主 policy 未接受 / 未盤點版本 ⇒ "unknown";
# K-e = policy 同列兩版時各版各自 ⇒ "true"(參數化,兩案各自獨立執行)。
# 既有 helper(`_g_root` / `_g_policy` / `_g_policy_text` / `_g_coverage`)只呼叫、不修改。
# ─────────────────────────────────────────────────────────────────────────────


class TestKnownDistBoundaryAnyio4151:

    def test_k3_anyio_4151_is_a_known_dist(self):
        """K-a(constant-lock;S6-2 上必須失敗:KNOWN_DISTS 只有 4.15.0)。"""
        assert ("anyio", "4.15.1") in redlight.KNOWN_DISTS, redlight.KNOWN_DISTS

    def test_k3_a_committed_policy_accepting_4151_with_a_4151_plugin_is_full_coverage(self, tmp_path, monkeypatch):
        """K-b(behavior-red;S6-2 上必須失敗:4.15.1 在邊界外 ⇒ policy 無效且 plugin 為 other ⇒ unknown)。"""
        root = _g_root(tmp_path / "r", policy_text=_g_policy_text(_g_policy(dists=[["anyio", "4.15.1"]])))
        got = _g_coverage(root, monkeypatch, anyio_version="4.15.1")
        assert got == "true", got

    def test_k3_a_host_policy_without_4151_is_unknown(self, tmp_path, monkeypatch):
        """K-c(negative-lock;S6-2 上即綠,修後仍須綠):宿主 policy 只接受 4.15.0,環境是 4.15.1 ⇒ unknown。"""
        root = _g_root(tmp_path / "r", policy_text=_g_policy_text(_g_policy()))
        got = _g_coverage(root, monkeypatch, anyio_version="4.15.1")
        assert got == "unknown", got

    def test_k3_an_uninventoried_version_is_unknown(self, tmp_path, monkeypatch):
        """K-d(negative-lock;S6-2 上即綠,修後仍須綠):9.9.9 不在 KNOWN_DISTS ⇒ policy 無效 ⇒ unknown。"""
        root = _g_root(tmp_path / "r", policy_text=_g_policy_text(_g_policy(dists=[["anyio", "9.9.9"]])))
        got = _g_coverage(root, monkeypatch, anyio_version="9.9.9")
        assert got == "unknown", got

    @pytest.mark.parametrize("version", ["4.15.0", "4.15.1"])
    def test_k3_a_policy_listing_both_versions_accepts_each(self, tmp_path, monkeypatch, version):
        """K-e(behavior-red;S6-2 上兩案皆失敗:policy 含邊界外版本 ⇒ 整份 policy 無效)。"""
        pol = _g_policy(dists=[["anyio", "4.15.0"], ["anyio", "4.15.1"]])
        got = _g_coverage(_g_root(tmp_path / "r", policy_text=_g_policy_text(pol)), monkeypatch, anyio_version=version)
        assert got == "true", got


# ─────────────────────────────────────────────────────────────────────────────
# 票 146 第三站紅燈(S3-146-1)—— Claude Code Enforcement Integrity v0 介面契約
#
# 契約在票 146〈設計決策 Q1–Q6〉;落點 = redlight.py。新 API 一律在測試內 getattr 取得,
# 缺 API ⇒ 測試內 AssertionError("v0 contract not implemented: <name>"),不得 collection error。
# 檔頂 import 不新增;標準庫在各測試內 import。既有 helper(`_d_git` / `_g_write`)只呼叫、不修改。
# ─────────────────────────────────────────────────────────────────────────────


class TestTicket146ExtensionIntegrity:
    """票 146 第三站紅燈。

    Invariant(逐字):146 可以證明「所有已知靜態載入入口符合 committed policy」，但在沒有獨立 runtime authority source 前，不得把這件事升格成「本 session 實際載入集合已驗證」。

    全部在 S3-146-1 預期各自失敗;缺 API 以測試內 AssertionError 呈現。
    """

    _ALLOWLIST_REL = ".agents/extension-allowlist.json"

    @staticmethod
    def _api(name):
        value = getattr(redlight, name, None)
        assert value is not None, "v0 contract not implemented: %s" % name
        return value

    @staticmethod
    def _allowlist(dev_mod_files=(), user_skill_plugins=(), user_commands=(), **extra):
        """檔案型欄位收 (path, sha256) 對,產生 {"path","sha256","note"}(3c 裁決 (k))。"""
        def entries(pairs):
            return [{"path": path, "sha256": sha, "note": "t146"} for path, sha in pairs]
        doc = {"schema": "monkeyleash.extension-allowlist", "version": 1,
               "dev_mod_files": entries(dev_mod_files),
               "user_skill_plugins": entries(user_skill_plugins),
               "user_commands": entries(user_commands),
               "project_settings_hook_commands": [], "mcp_json_servers": []}
        doc.update(extra)
        return doc

    @staticmethod
    def _text(doc):
        return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"

    def _repo(self, root, allowlist_text=None, commit_allowlist=True):
        """真的 git repo:提交 README;`allowlist_text` 不為 None ⇒ 寫到 allowlist 位置,`commit_allowlist` 為真才一起提交。"""
        root = pathlib.Path(str(root))
        root.mkdir(parents=True, exist_ok=True)
        _g_write(root, "README.md", u"t146\n")
        tracked = ["README.md"]
        if allowlist_text is not None:
            _g_write(root, self._ALLOWLIST_REL, allowlist_text)
            if commit_allowlist:
                tracked.append(self._ALLOWLIST_REL)
        _d_git(root, "init", "-q")
        _d_git(root, "config", "user.email", "t@example.invalid")
        _d_git(root, "config", "user.name", "t")
        _d_git(root, "add", *tracked)
        _d_git(root, "commit", "-q", "-m", "baseline")
        return root

    def _surfaces(self, base, dev_mod_files=None, dev_mod_dirs=(), synced_files=None):
        """乾淨的 surface 佈置(全部在 tmp,路徑注入)+ 指定的 dev-mods / synced 內容 → `extension_surface_facts`。
        `synced_files` 為 None ⇒ synced 目錄不存在。"""
        base = pathlib.Path(str(base))
        dev = base / "dev-mods"
        dev.mkdir(parents=True, exist_ok=True)
        for d in dev_mod_dirs:
            (dev / d).mkdir(parents=True, exist_ok=True)
        for rel, data in (dev_mod_files or {}).items():
            p = dev / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        synced = base / "synced"
        for rel, data in (synced_files or {}).items():
            p = synced / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        canon = base / "canon"
        _g_write(canon, "s/SKILL.md", u"skill\n")
        user_skills = base / "user-skills"
        user_skills.mkdir(parents=True, exist_ok=True)
        user_commands = base / "user-commands"
        user_commands.mkdir(parents=True, exist_ok=True)
        fn = self._api("extension_surface_facts")
        return fn(str(dev), [("skills", str(synced))], str(canon), [], [], str(base / "absent.mcp.json"),
                  str(user_skills), str(user_commands))

    def _facts(self, root):
        return self._api("extension_allowlist_facts")(str(root))

    def _evaluate(self, facts, surfaces):
        state = self._api("extension_state")(facts, surfaces)
        lines = self._api("extension_status_lines")(facts, surfaces)
        return state, lines

    @staticmethod
    def _gate():
        spec = importlib.util.spec_from_file_location(
            "gate_for_t146", ROOT / ".claude" / "hooks" / "gate.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def _scenarios(self, tmp_path):
        """T146-1 到 T146-4b 的輸入組合:[(標籤, facts, surfaces)]。T146-8 用。"""
        import hashlib
        text = self._text(self._allowlist())
        note = b"not code\n"
        note_sha = hashlib.sha256(note).hexdigest()
        out = []

        r = self._repo(tmp_path / "r1", allowlist_text=text)
        _g_write(r, self._ALLOWLIST_REL, text + "\n")
        out.append(("T146-1", self._facts(r), self._surfaces(tmp_path / "s1")))

        r = self._repo(tmp_path / "r2", allowlist_text=text, commit_allowlist=False)
        out.append(("T146-2", self._facts(r), self._surfaces(tmp_path / "s2")))

        r = self._repo(tmp_path / "r2b")
        out.append(("T146-2b", self._facts(r), self._surfaces(tmp_path / "s2b")))

        r = self._repo(tmp_path / "r2c", allowlist_text=self._text(self._allowlist(extra=[])))
        out.append(("T146-2c", self._facts(r), self._surfaces(tmp_path / "s2c")))

        r = self._repo(tmp_path / "r3", allowlist_text=text)
        out.append(("T146-3", self._facts(r),
                    self._surfaces(tmp_path / "s3", dev_mod_files={"note.txt": note})))

        r = self._repo(tmp_path / "r3b", allowlist_text=self._text(self._allowlist(dev_mod_files=[("note.txt", note_sha)])))
        out.append(("T146-3b", self._facts(r),
                    self._surfaces(tmp_path / "s3b", dev_mod_files={"note.txt": note})))

        r = self._repo(tmp_path / "r4", allowlist_text=text)
        out.append(("T146-4", self._facts(r),
                    self._surfaces(tmp_path / "s4", dev_mod_dirs=("session-id-shell",))))

        r = self._repo(tmp_path / "r4b", allowlist_text=text)
        out.append(("T146-4b", self._facts(r),
                    self._surfaces(tmp_path / "s4b", dev_mod_dirs=("session-id-shell",),
                                   synced_files={"bkt/manifest.json": b"{}\n", ".bucket-bkt": b"marker\n"})))
        return out

    def test_t146_0a(self):
        """T146-0a:常數鎖 —— allowlist 位置 / schema / 欄位與四態常數的值如契約;對應 invariant 前半。"""
        expected = {
            "EXT_ALLOWLIST_FILE": ".agents/extension-allowlist.json",
            "EXT_ALLOWLIST_SCHEMA": "monkeyleash.extension-allowlist",
            "EXT_ALLOWLIST_FIELDS": ("schema", "version", "dev_mod_files", "user_skill_plugins",
                                     "user_commands", "project_settings_hook_commands", "mcp_json_servers"),
            "EXT_VIOLATION": "VIOLATION",
            "EXT_UNKNOWN": "UNKNOWN",
            "EXT_DECLARED_OK": "DECLARED_OK",
            "EXT_VERIFIED": "VERIFIED",
        }
        for name, value in expected.items():
            assert self._api(name) == value, (name, getattr(redlight, name, None))

    def test_t146_1(self, tmp_path):
        """T146-1:allowlist 已提交後工作樹多一行 ⇒ worktree_differs、VIOLATION;對應 invariant 前半。"""
        text = self._text(self._allowlist())
        root = self._repo(tmp_path / "r", allowlist_text=text)
        _g_write(root, self._ALLOWLIST_REL, text + "\n")
        facts = self._facts(root)
        assert {"state", "blob", "policy"} <= set(facts), sorted(facts)
        assert facts["state"] == "worktree_differs", facts
        state, lines = self._evaluate(facts, self._surfaces(tmp_path / "s"))
        assert state == self._api("EXT_VIOLATION"), state
        assert u"allowlist 工作樹與 HEAD 不同" in lines[0], lines

    def test_t146_2(self, tmp_path):
        """T146-2:allowlist 只在工作樹、從未提交 ⇒ uncommitted、VIOLATION;對應 invariant 前半。"""
        root = self._repo(tmp_path / "r", allowlist_text=self._text(self._allowlist()), commit_allowlist=False)
        facts = self._facts(root)
        assert facts["state"] == "uncommitted", facts
        state, lines = self._evaluate(facts, self._surfaces(tmp_path / "s"))
        assert state == self._api("EXT_VIOLATION"), state
        assert u"allowlist 未提交" in lines[0], lines

    def test_t146_2b(self, tmp_path):
        """T146-2b:HEAD 與工作樹都沒有 allowlist ⇒ uninitialized、VIOLATION;對應 invariant 前半。"""
        root = self._repo(tmp_path / "r")
        facts = self._facts(root)
        assert facts["state"] == "uninitialized", facts
        state, lines = self._evaluate(facts, self._surfaces(tmp_path / "s"))
        assert state == self._api("EXT_VIOLATION"), state
        assert u"allowlist 未初始化" in lines[0], lines

    def test_t146_2c(self, tmp_path):
        """T146-2c:已提交但鍵集合多一個鍵 ⇒ malformed、VIOLATION;對應 invariant 前半。"""
        root = self._repo(tmp_path / "r", allowlist_text=self._text(self._allowlist(extra=[])))
        facts = self._facts(root)
        assert facts["state"] == "malformed", facts
        state, _lines = self._evaluate(facts, self._surfaces(tmp_path / "s"))
        assert state == self._api("EXT_VIOLATION"), state

    def test_t146_3(self, tmp_path):
        """T146-3:dev-mods 根目錄有未登記的 note.txt(副檔名刻意非程式碼)⇒ VIOLATION;對應 invariant 前半。"""
        import hashlib
        data = b"not code\n"
        sha = hashlib.sha256(data).hexdigest()
        root = self._repo(tmp_path / "r", allowlist_text=self._text(self._allowlist()))
        surfaces = self._surfaces(tmp_path / "s", dev_mod_files={"note.txt": data})
        assert ("note.txt", sha) in [tuple(x) for x in surfaces["dev_mod_files"]], surfaces["dev_mod_files"]
        state, lines = self._evaluate(self._facts(root), surfaces)
        assert state == self._api("EXT_VIOLATION"), state
        assert "note.txt" in lines[0], lines

    def test_t146_3b(self, tmp_path):
        """T146-3b:同 T146-3 但 allowlist 的 dev_mod_files 登記了該檔 sha256 ⇒ 不是 VIOLATION(Q6 指紋模型);對應 invariant 前半。"""
        import hashlib
        data = b"not code\n"
        sha = hashlib.sha256(data).hexdigest()
        root = self._repo(tmp_path / "r", allowlist_text=self._text(self._allowlist(dev_mod_files=[("note.txt", sha)])))
        surfaces = self._surfaces(tmp_path / "s", dev_mod_files={"note.txt": data})
        state, _lines = self._evaluate(self._facts(root), surfaces)
        assert state != self._api("EXT_VIOLATION"), state

    def test_t146_4(self, tmp_path):
        """T146-4:dev-mods 只有 <id> 空殼子目錄、synced 不存在 ⇒ DECLARED_OK,runtime 欄含「未證明」;對應 invariant 前半(負控)。"""
        root = self._repo(tmp_path / "r", allowlist_text=self._text(self._allowlist()))
        surfaces = self._surfaces(tmp_path / "s", dev_mod_dirs=("session-id-shell",))
        state, lines = self._evaluate(self._facts(root), surfaces)
        assert state == self._api("EXT_DECLARED_OK"), state
        assert u"未證明" in lines[1], lines

    def test_t146_4b(self, tmp_path):
        """T146-4b:同 T146-4 但 synced 目錄有一個 manifest.json ⇒ UNKNOWN(Q2:未受管入口不算 static clean);對應 invariant 前半。"""
        root = self._repo(tmp_path / "r", allowlist_text=self._text(self._allowlist()))
        surfaces = self._surfaces(tmp_path / "s", dev_mod_dirs=("session-id-shell",),
                                  synced_files={"bkt/manifest.json": b"{}\n", ".bucket-bkt": b"marker\n"})
        state, lines = self._evaluate(self._facts(root), surfaces)
        assert state == self._api("EXT_UNKNOWN"), state
        assert "UNKNOWN" in lines[0], lines

    def test_t146_5(self, tmp_path):
        """T146-5:實體鏡像多出正典沒有的 .claude-plugin/plugin.json ⇒ R4 違規;對應 invariant 前半。"""
        canon = tmp_path / "canon"
        mirror = tmp_path / "mirror"
        _g_write(canon, "s/SKILL.md", u"skill\n")
        _g_write(mirror, "s/SKILL.md", u"skill\n")
        _g_write(mirror, "s/.claude-plugin/plugin.json", u'{"name": "s"}\n')
        out = self._gate().skill_mirror_violations(str(canon), [str(mirror)])
        assert any(u"鏡像多出正典沒有的檔" in v for v in out), out

    def test_t146_6(self, tmp_path):
        """T146-6:鏡像輔助檔 references/a.md 內容與正典不同(SKILL.md 相同)⇒ R4 違規;對應 invariant 前半。"""
        canon = tmp_path / "canon"
        mirror = tmp_path / "mirror"
        _g_write(canon, "s/SKILL.md", u"skill\n")
        _g_write(canon, "s/references/a.md", u"canon\n")
        _g_write(mirror, "s/SKILL.md", u"skill\n")
        _g_write(mirror, "s/references/a.md", u"drifted\n")
        out = self._gate().skill_mirror_violations(str(canon), [str(mirror)])
        assert any(u"實體副本內容不一致" in v and "references/a.md" in v for v in out), out

    def test_t146_7(self, tmp_path):
        """T146-7:全乾淨 ⇒ 恰好兩行、兩欄分開、只掃這兩行不含 pass / 有效 / verified;對應 invariant 後半。"""
        root = self._repo(tmp_path / "r", allowlist_text=self._text(self._allowlist()))
        _state, lines = self._evaluate(self._facts(root), self._surfaces(tmp_path / "s"))
        assert isinstance(lines, list) and len(lines) == 2, lines
        assert lines[0].startswith("static surfaces: "), lines
        assert lines[1].startswith("runtime loaded set: "), lines
        assert u"未證明" in lines[1], lines
        joined = u"\n".join(lines).lower()
        for word in (u"pass", u"有效", u"verified"):
            assert word not in joined, (word, lines)

    def test_t146_8(self, tmp_path):
        """T146-8:EXT_VERIFIED 不可達 —— 已知輸入空間的行為鎖 + 結構性 regression lock;對應 invariant 後半。

        結構性 regression lock + 已知輸入空間的行為鎖;不是不可達性的形式證明。
        """
        import inspect
        allowed = {self._api("EXT_VIOLATION"), self._api("EXT_UNKNOWN"), self._api("EXT_DECLARED_OK")}
        fn = self._api("extension_state")
        got = dict((label, fn(facts, surfaces)) for label, facts, surfaces in self._scenarios(tmp_path))
        assert set(got.values()) <= allowed, got
        forbidden = "return " + "EXT_VERIFIED"
        assert forbidden not in inspect.getsource(fn), "extension_state 原始碼含 %s" % forbidden

    @pytest.mark.skipif("os.name == 'nt'", reason="Windows 建 symlink 需要額外權限;POSIX 才產得出來")
    def test_t146_9(self, tmp_path):
        """T146-9:鏡像 symlink 指向正典之外 ⇒ R4 違規,且同一筆出現在 extension_surface_facts 的 r4_violations;對應 invariant 前半(保留分支回歸)。"""
        import os
        canon = tmp_path / "canon"
        outside = tmp_path / "outside"
        mirror = tmp_path / "mirror"
        _g_write(canon, "s/SKILL.md", u"skill\n")
        _g_write(outside, "s/SKILL.md", u"skill\n")
        mirror.mkdir()
        os.symlink(str(outside / "s"), str(mirror / "s"))
        out = self._gate().skill_mirror_violations(str(canon), [str(mirror)])
        assert any(u"symlink 指向正典之外" in v for v in out), out
        user_skills = tmp_path / "user-skills"
        user_skills.mkdir()
        user_commands = tmp_path / "user-commands"
        user_commands.mkdir()
        fn = self._api("extension_surface_facts")
        surfaces = fn(str(tmp_path / "no-dev-mods"), [], str(canon), [str(mirror)], [],
                      str(tmp_path / "absent.mcp.json"), str(user_skills), str(user_commands))
        assert any(u"symlink 指向正典之外" in v for v in surfaces["r4_violations"]), surfaces["r4_violations"]

    def test_t146_11(self, tmp_path):
        """T146-11:user-skills 目錄有未登記的 foo/SKILL.md ⇒ VIOLATION;對應 invariant 前半。"""
        import hashlib
        data = b"user skill\n"
        sha = hashlib.sha256(data).hexdigest()
        base = tmp_path / "s"
        target = base / "user-skills" / "foo" / "SKILL.md"
        target.parent.mkdir(parents=True)
        target.write_bytes(data)
        root = self._repo(tmp_path / "r", allowlist_text=self._text(self._allowlist()))
        surfaces = self._surfaces(base)
        got = [tuple(x) for x in surfaces.get("user_skill_plugins", [])]
        assert ("foo/SKILL.md", sha) in got, got
        state, lines = self._evaluate(self._facts(root), surfaces)
        assert state == self._api("EXT_VIOLATION"), state
        assert "foo/SKILL.md" in lines[0], lines

    def test_t146_11b(self, tmp_path):
        """T146-11b:同 T146-11 但 allowlist 的 user_skill_plugins 登記了該檔 sha256 ⇒ 不是 VIOLATION;對應 invariant 前半。"""
        import hashlib
        data = b"user skill\n"
        sha = hashlib.sha256(data).hexdigest()
        base = tmp_path / "s"
        target = base / "user-skills" / "foo" / "SKILL.md"
        target.parent.mkdir(parents=True)
        target.write_bytes(data)
        policy = self._allowlist(user_skill_plugins=[("foo/SKILL.md", sha)])
        root = self._repo(tmp_path / "r", allowlist_text=self._text(policy))
        state, _lines = self._evaluate(self._facts(root), self._surfaces(base))
        assert state != self._api("EXT_VIOLATION"), state

    def test_t146_11c(self, tmp_path):
        """T146-11c:只排除 <user_skills_dir>/synced 整棵(頂層 synced ⇒ 交給 synced_dirs、UNKNOWN);非頂層的 synced 不排除;對應 invariant 前半。"""
        import hashlib
        base = tmp_path / "s"
        user_skills = base / "user-skills"
        manifest = user_skills / "synced" / "session-id" / "manifest.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_bytes(b"{}\n")
        (user_skills / "synced" / ".bucket-session-id").write_bytes(b"marker\n")
        user_commands = base / "user-commands"
        user_commands.mkdir(parents=True)
        dev = base / "dev-mods"
        dev.mkdir(parents=True)
        canon = base / "canon"
        _g_write(canon, "s/SKILL.md", u"skill\n")
        fn = self._api("extension_surface_facts")
        args = (str(dev), [("skills", str(user_skills / "synced"))], str(canon), [], [], str(base / "absent.mcp.json"),
                str(user_skills), str(user_commands))
        surfaces = fn(*args)
        assert list(surfaces.get("user_skill_plugins", ["<missing>"])) == [], surfaces.get("user_skill_plugins")
        root = self._repo(tmp_path / "r", allowlist_text=self._text(self._allowlist()))
        state, _lines = self._evaluate(self._facts(root), surfaces)
        assert state == self._api("EXT_UNKNOWN"), state
        evil = user_skills / "foo" / "synced" / "evil.md"
        evil.parent.mkdir(parents=True)
        evil.write_bytes(b"not excluded\n")
        sha = hashlib.sha256(b"not excluded\n").hexdigest()
        got = [tuple(x) for x in fn(*args).get("user_skill_plugins", [])]
        assert ("foo/synced/evil.md", sha) in got, got

    def test_t146_12(self, tmp_path):
        """T146-12:user-commands 目錄有未登記的 finmind.md ⇒ VIOLATION;對應 invariant 前半。"""
        import hashlib
        data = b"command\n"
        sha = hashlib.sha256(data).hexdigest()
        base = tmp_path / "s"
        target = base / "user-commands" / "finmind.md"
        target.parent.mkdir(parents=True)
        target.write_bytes(data)
        root = self._repo(tmp_path / "r", allowlist_text=self._text(self._allowlist()))
        surfaces = self._surfaces(base)
        got = [tuple(x) for x in surfaces.get("user_commands", [])]
        assert ("finmind.md", sha) in got, got
        state, lines = self._evaluate(self._facts(root), surfaces)
        assert state == self._api("EXT_VIOLATION"), state
        assert "finmind.md" in lines[0], lines

    def test_t146_12b(self, tmp_path):
        """T146-12b:同 T146-12 但 allowlist 的 user_commands 登記了該檔 sha256 ⇒ 不是 VIOLATION;對應 invariant 前半。"""
        import hashlib
        data = b"command\n"
        sha = hashlib.sha256(data).hexdigest()
        base = tmp_path / "s"
        target = base / "user-commands" / "finmind.md"
        target.parent.mkdir(parents=True)
        target.write_bytes(data)
        policy = self._allowlist(user_commands=[("finmind.md", sha)])
        root = self._repo(tmp_path / "r", allowlist_text=self._text(policy))
        state, _lines = self._evaluate(self._facts(root), self._surfaces(base))
        assert state != self._api("EXT_VIOLATION"), state

    def test_t146_13(self, tmp_path):
        """T146-13:依賴方向 B —— facts 層住在 redlight.py、不反向載入 gate;R4 純函式下沉且與 gate 薄包裝結果相同;對應 invariant 前半。

        AST 層級,不掃註解(3c 裁決 (i));redlight.py:18、:27 的歷史註解不在掃描範圍。
        """
        import ast
        import inspect
        fn = self._api("extension_surface_facts")
        src = inspect.getsourcefile(fn)
        assert pathlib.Path(src).name == "redlight.py", src
        tree = ast.parse((ROOT / ".claude" / "hooks" / "redlight.py").read_text(encoding="utf-8"))
        bad = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                bad += ["import %s" % a.name for a in node.names if a.name.split(".")[0] == "gate"]
            elif isinstance(node, ast.ImportFrom):
                if (node.module or "").split(".")[0] == "gate":
                    bad.append("from %s import" % node.module)
            elif isinstance(node, ast.Call):
                func = node.func
                name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
                if name in ("spec_from_file_location", "import_module"):
                    for arg in list(node.args) + [k.value for k in node.keywords]:
                        for sub in ast.walk(arg):
                            if isinstance(sub, ast.Constant) and isinstance(sub.value, str) and "gate" in sub.value:
                                bad.append("%s(%r)" % (name, sub.value))
        assert not bad, bad
        primitive = self._api("skill_mirror_violations")
        for f in (fn, primitive):
            assert ("gate" + ".py") not in inspect.getsource(f), f.__name__
        canon = tmp_path / "canon"
        mirror = tmp_path / "mirror"
        _g_write(canon, "s/SKILL.md", u"skill\n")
        _g_write(mirror, "s/SKILL.md", u"skill\n")
        _g_write(mirror, "s/.claude-plugin/plugin.json", u'{"name": "s"}\n')
        via_gate = self._gate().skill_mirror_violations(str(canon), [str(mirror)])
        via_redlight = primitive(str(canon), [str(mirror)])
        assert via_gate == via_redlight, (via_gate, via_redlight)

    def test_t146_14(self, tmp_path):
        """T146-14:完整性前提 —— surfaces 鍵集合恰為八鍵才可能 DECLARED_OK;少一鍵或多一鍵都不得 DECLARED_OK;對應 invariant 後半。"""
        keys = ("dev_mod_files", "synced_files", "r4_violations", "project_hook_commands",
                "mcp_json_servers", "user_skill_plugins", "user_commands", "errors")
        root = self._repo(tmp_path / "r", allowlist_text=self._text(self._allowlist()))
        surfaces = self._surfaces(tmp_path / "s")
        assert set(surfaces) == set(keys), sorted(surfaces)
        facts = self._facts(root)
        state_fn = self._api("extension_state")
        ok = self._api("EXT_DECLARED_OK")
        assert state_fn(facts, surfaces) == ok
        for key in keys:
            partial = dict((k, v) for k, v in surfaces.items() if k != key)
            assert state_fn(facts, partial) != ok, "少了 %s 仍為 DECLARED_OK" % key
        extra = dict(surfaces)
        extra["unexpected"] = []
        assert state_fn(facts, extra) != ok, "多一個未知鍵仍為 DECLARED_OK"

    _T146_FIELDS = {"dev-mods": "dev_mod_files", "user-skills": "user_skill_plugins",
                    "user-commands": "user_commands"}

    @pytest.mark.parametrize("entry", ["dev-mods", "user-skills", "user-commands"])
    def test_t146_15(self, tmp_path, entry):
        """T146-15:同 hash 不同 path ⇒ VIOLATION(登記 safe.md,目錄放內容相同的 admin.md);對應 invariant 前半。"""
        import hashlib
        field = self._T146_FIELDS[entry]
        data = b"same bytes\n"
        sha = hashlib.sha256(data).hexdigest()
        base = tmp_path / "s"
        target = base / entry / "admin.md"
        target.parent.mkdir(parents=True)
        target.write_bytes(data)
        policy = self._allowlist(**{field: [("safe.md", sha)]})
        root = self._repo(tmp_path / "r", allowlist_text=self._text(policy))
        surfaces = self._surfaces(base)
        got = [tuple(x) for x in surfaces.get(field, [])]
        assert ("admin.md", sha) in got, got
        state, lines = self._evaluate(self._facts(root), surfaces)
        assert state == self._api("EXT_VIOLATION"), state
        assert "admin.md" in lines[0], lines

    @pytest.mark.parametrize("entry", ["dev-mods", "user-skills", "user-commands"])
    def test_t146_15b(self, tmp_path, entry):
        """T146-15b:同 path 不同 hash ⇒ VIOLATION(登記 safe.md 的 sha_X,目錄的 safe.md 內容是 sha_Y);對應 invariant 前半。"""
        import hashlib
        field = self._T146_FIELDS[entry]
        sha_x = hashlib.sha256(b"registered\n").hexdigest()
        base = tmp_path / "s"
        target = base / entry / "safe.md"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"tampered\n")
        policy = self._allowlist(**{field: [("safe.md", sha_x)]})
        root = self._repo(tmp_path / "r", allowlist_text=self._text(policy))
        state, lines = self._evaluate(self._facts(root), self._surfaces(base))
        assert state == self._api("EXT_VIOLATION"), state
        assert "safe.md" in lines[0], lines

    @pytest.mark.parametrize("kind, value", [
        ("positive", "dev-mods"),
        ("positive", "user-skills"),
        ("positive", "user-commands"),
        ("malformed", "./safe.md"),
        ("malformed", "foo/../safe.md"),
        ("malformed", "foo//safe.md"),
        ("malformed", "foo\\safe.md"),
        ("malformed", "/safe.md"),
        ("malformed", "C:/safe.md"),
        ("malformed", "safe.md/"),
    ], ids=["positive-dev-mods", "positive-user-skills", "positive-user-commands",
            "malformed-dot-segment", "malformed-dotdot-segment", "malformed-empty-segment",
            "malformed-backslash", "malformed-leading-slash", "malformed-drive-prefix",
            "malformed-trailing-slash"])
    def test_t146_15c(self, tmp_path, kind, value):
        """T146-15c:(path, sha256) 都相同才授權(正向,含 foo..bar.md);policy 的 path 不是 canonical 形式 ⇒ malformed(只對 user-commands);對應 invariant 前半。"""
        import hashlib
        if kind == "positive":
            field = self._T146_FIELDS[value]
            safe, odd = b"safe\n", b"odd name\n"
            base = tmp_path / "s"
            (base / value).mkdir(parents=True)
            (base / value / "safe.md").write_bytes(safe)
            (base / value / "foo..bar.md").write_bytes(odd)
            pairs = [("safe.md", hashlib.sha256(safe).hexdigest()),
                     ("foo..bar.md", hashlib.sha256(odd).hexdigest())]
            root = self._repo(tmp_path / "r", allowlist_text=self._text(self._allowlist(**{field: pairs})))
            state, _lines = self._evaluate(self._facts(root), self._surfaces(base))
            assert state != self._api("EXT_VIOLATION"), state
        else:
            sha = hashlib.sha256(b"x\n").hexdigest()
            policy = self._allowlist(user_commands=[(value, sha)])
            root = self._repo(tmp_path / "r", allowlist_text=self._text(policy))
            facts = self._facts(root)
            assert facts["state"] == "malformed", (value, facts)
            state, _lines = self._evaluate(facts, self._surfaces(tmp_path / "s"))
            assert state == self._api("EXT_VIOLATION"), (value, state)

    @pytest.mark.parametrize("field", ["dev_mod_files", "user_skill_plugins", "user_commands"])
    def test_t146_16(self, tmp_path, field):
        """T146-16:同一欄位 path 重複 ⇒ malformed(sha 不同、sha 相同兩子案;3d 裁決 (m));對應 invariant 前半。"""
        import hashlib
        sha_a = hashlib.sha256(b"a\n").hexdigest()
        sha_b = hashlib.sha256(b"b\n").hexdigest()
        for label, pairs in (("different sha", [("safe.md", sha_a), ("safe.md", sha_b)]),
                             ("same sha", [("safe.md", sha_a), ("safe.md", sha_a)])):
            root = self._repo(tmp_path / ("r-" + label.replace(" ", "-")),
                              allowlist_text=self._text(self._allowlist(**{field: pairs})))
            facts = self._facts(root)
            assert facts["state"] == "malformed", (label, facts)
            state, _lines = self._evaluate(facts, self._surfaces(tmp_path / ("s-" + label.replace(" ", "-"))))
            assert state == self._api("EXT_VIOLATION"), (label, state)

    def test_t146_17(self, tmp_path):
        """T146-17:allowlist malformed 且 surfaces 少一鍵 ⇒ 仍是 VIOLATION,原因是 allowlist(4a-2 裁決 (r));對應 invariant 前半。"""
        root = self._repo(tmp_path / "r", allowlist_text=self._text(self._allowlist(extra=[])))
        facts = self._facts(root)
        assert facts["state"] == "malformed", facts
        surfaces = dict(self._surfaces(tmp_path / "s"))
        surfaces.pop("synced_files")
        state, lines = self._evaluate(facts, surfaces)
        assert state == self._api("EXT_VIOLATION"), (state, lines)
        assert u"allowlist 格式不明" in lines[0], lines

    # ── 3e(S3e-146-1):category、extension_report、claude_root、errors ─────────

    def _t3e_clean(self, tmp_path):
        """已提交的空白 allowlist + 一個存在但空的 claude_root(tmp,不碰真的 ~/.claude)。"""
        root = self._repo(tmp_path / "r", allowlist_text=self._text(self._allowlist()))
        claude = tmp_path / "claude"
        claude.mkdir()
        return root, claude

    def _t3e_report(self, repo_root, claude_root, **kw):
        fn = self._api("extension_report")
        return fn(str(repo_root), None if claude_root is None else str(claude_root), **kw)

    def _t3e_kw(self, name):
        """extension_report 的注入參數;缺 ⇒ 測試內紅。"""
        import inspect
        fn = self._api("extension_report")
        assert name in inspect.signature(fn).parameters, \
            "v0 contract not implemented: extension_report(%s=)" % name
        return fn

    @staticmethod
    def _t3e_fake_walk(target, first_level=False):
        """包住 os.walk:走到 `target` 時經 onerror 注入一個 OSError(first_level ⇒ 第一層就失敗、不產出任何項目)。"""
        import os

        def same(a, b):
            return os.path.normcase(os.path.abspath(str(a))) == os.path.normcase(os.path.abspath(str(b)))

        def fake_walk(top, topdown=True, onerror=None, followlinks=False):
            hit = same(top, target)
            if hit and first_level:
                if onerror is not None:
                    onerror(OSError(13, "injected first-level failure", str(target)))
                return
            for item in os.walk(top, topdown=topdown, onerror=onerror, followlinks=followlinks):
                yield item
            if hit and onerror is not None:
                onerror(OSError(13, "injected walk failure", os.path.join(str(target), "sub")))
        return fake_walk

    def test_t146_34(self):
        """T146-34:常數鎖 —— 七個 EXT_CAT_*、EXT_CATEGORIES、EXT_RUNTIME_UNPROVEN、EXT_SURFACE_KEYS 八鍵;對應 invariant 前半。"""
        cats = {"EXT_CAT_ALLOWLIST": "allowlist_state", "EXT_CAT_UNREGISTERED": "unregistered",
                "EXT_CAT_R4": "r4", "EXT_CAT_HOOK": "hook", "EXT_CAT_MCP": "mcp",
                "EXT_CAT_OBSERVATION": "observation_missing", "EXT_CAT_UNMANAGED": "unmanaged_entry"}
        for name, value in cats.items():
            assert self._api(name) == value, (name, getattr(redlight, name, None))
        assert self._api("EXT_CATEGORIES") == frozenset(cats.values())
        assert self._api("EXT_RUNTIME_UNPROVEN") == "UNPROVEN"
        assert self._api("EXT_SURFACE_KEYS") == frozenset((
            "dev_mod_files", "synced_files", "r4_violations", "project_hook_commands",
            "mcp_json_servers", "user_skill_plugins", "user_commands", "errors"))

    def test_t146_35(self, tmp_path):
        """T146-35:_extension_first_reason 回 (state, category, reason);T146-1 / 3 / 4 / 4b 佈置的 category 為 allowlist_state / unregistered / None / unmanaged_entry;對應 invariant 前半。"""
        fn = self._api("_extension_first_reason")
        scen = dict((label, (facts, surfaces)) for label, facts, surfaces in self._scenarios(tmp_path))
        expected = {"T146-1": "allowlist_state", "T146-3": "unregistered",
                    "T146-4": None, "T146-4b": "unmanaged_entry"}
        for label, category in expected.items():
            res = fn(*(scen[label] + (self._api("EXT_INVENTORY_UNCHECKED"),)))
            assert isinstance(res, tuple) and len(res) == 3, \
                "v0 contract not implemented: _extension_first_reason 三元組(%s → %r)" % (label, res)
            assert res[1] == category, (label, res)

    def test_t146_31(self, tmp_path, monkeypatch):
        """T146-31:判定一次(z1)—— 有效 claude_root ⇒ _extension_first_reason 恰好 1 次且 lines 由同一結果渲染;無效 ⇒ 0 次;對應 invariant 後半。"""
        self._api("extension_report")
        render = self._api("_extension_render_lines")
        orig = self._api("_extension_first_reason")
        calls = []

        def counting(facts, surfaces, *inventory):
            res = orig(facts, surfaces, *inventory)
            calls.append(res)
            return res
        monkeypatch.setattr(redlight, "_extension_first_reason", counting)
        root, claude = self._t3e_clean(tmp_path)
        report = self._t3e_report(root, claude)
        assert len(calls) == 1, calls
        state, category, reason = calls[0]
        assert list(report["lines"]) == list(render(state, category, reason, report["facts"])), report["lines"]
        del calls[:]
        bad = self._t3e_report(root, tmp_path / "missing-claude-root")
        assert calls == [], calls
        assert bad["observation"] == "claude_root_invalid", bad

    def test_t146_27(self, tmp_path, monkeypatch):
        """T146-27:claude_root=None ⇒ fallback = expanduser("~")/.claude;明確給不存在路徑 ⇒ 前置觀測失敗、不 fallback(補鎖 3);對應 invariant 前半。"""
        import os
        home = tmp_path / "home"
        (home / ".claude").mkdir(parents=True)
        real = os.path.expanduser
        monkeypatch.setattr(os.path, "expanduser", lambda p: str(home) if p == "~" else real(p))
        root = self._repo(tmp_path / "r", allowlist_text=self._text(self._allowlist()))
        rep = self._t3e_report(root, None)
        assert rep["claude_root_source"] == "fallback", rep
        assert os.path.normcase(rep["claude_root"]) == os.path.normcase(os.path.join(str(home), ".claude")), rep
        bad = self._t3e_report(root, tmp_path / "nope")
        assert bad["claude_root_source"] == "param", bad
        assert bad["observation"] == "claude_root_invalid", bad
        assert bad["state"] == self._api("EXT_UNKNOWN"), bad
        assert bad["category"] == self._api("EXT_CAT_OBSERVATION"), bad
        assert bad["surfaces"] is None and bad["facts"] is None, bad
        assert u"claude_root 無法確定" in (bad["reason"] or u""), bad

    def test_t146_32a(self, tmp_path):
        """T146-32a:列舉中途經 onerror 回 OSError ⇒ errors 非空、UNKNOWN / observation_missing(z3,跨平台必跑);對應 invariant 前半。"""
        fn = self._t3e_kw("walk")
        root, claude = self._t3e_clean(tmp_path)
        dev = claude / "dev-mods"
        (dev / "sub").mkdir(parents=True)
        rep = fn(str(root), str(claude), walk=self._t3e_fake_walk(dev))
        assert rep["surfaces"]["errors"], rep["surfaces"]
        assert rep["state"] == self._api("EXT_UNKNOWN"), rep
        assert rep["category"] == self._api("EXT_CAT_OBSERVATION"), rep

    def test_t146_32b(self, tmp_path):
        """T146-32b:同 32a 再加一個未登記 dev-mod 檔 ⇒ VIOLATION 且 errors 仍非空(補鎖 2,跨平台必跑);對應 invariant 前半。"""
        fn = self._t3e_kw("walk")
        root, claude = self._t3e_clean(tmp_path)
        dev = claude / "dev-mods"
        (dev / "sub").mkdir(parents=True)
        (dev / "x.txt").write_bytes(b"x\n")
        rep = fn(str(root), str(claude), walk=self._t3e_fake_walk(dev))
        assert rep["state"] == self._api("EXT_VIOLATION"), rep
        assert rep["surfaces"]["errors"], rep["surfaces"]

    def test_t146_32c(self, tmp_path):
        """T146-32c:lstat 對 dev-mods 根丟 PermissionError ⇒ errors 含 ("dev-mods", <path>, <error_text>)(跨平台必跑);對應 invariant 前半。"""
        import os
        fn = self._t3e_kw("lstat")
        root, claude = self._t3e_clean(tmp_path)
        dev = claude / "dev-mods"
        dev.mkdir()
        real = os.lstat

        def fake_lstat(p, *a, **k):
            if os.path.normcase(os.path.abspath(str(p))) == os.path.normcase(os.path.abspath(str(dev))):
                raise PermissionError(13, "injected lstat failure", str(dev))
            return real(p, *a, **k)
        rep = fn(str(root), str(claude), lstat=fake_lstat)
        errors = rep["surfaces"]["errors"]
        assert any(e[0] == "dev-mods" and len(e) == 3 for e in errors), errors

    def test_t146_32d(self, tmp_path):
        """T146-32d:列舉第一層就 onerror ⇒ errors 非空、entries 可空(不得洗成空集合;跨平台必跑);對應 invariant 前半。"""
        fn = self._t3e_kw("walk")
        root, claude = self._t3e_clean(tmp_path)
        dev = claude / "dev-mods"
        dev.mkdir()
        rep = fn(str(root), str(claude), walk=self._t3e_fake_walk(dev, first_level=True))
        assert rep["surfaces"]["errors"], rep["surfaces"]
        assert rep["state"] != self._api("EXT_DECLARED_OK"), rep

    @pytest.mark.skipif("os.name == 'nt'", reason="chmod 000 在 Windows 不會讓目錄不可列舉;POSIX 才產得出來")
    def test_t146_32e(self, tmp_path):
        """T146-32e:POSIX 實體權限 —— chmod 000 的子目錄 ⇒ errors 非空(finally 恢復權限);對應 invariant 前半。"""
        import os
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            pytest.skip("root 不受 chmod 000 限制")
        root, claude = self._t3e_clean(tmp_path)
        sub = claude / "dev-mods" / "sub"
        sub.mkdir(parents=True)
        (sub / "x.txt").write_bytes(b"x\n")
        os.chmod(str(sub), 0)
        try:
            rep = self._t3e_report(root, claude)
            assert rep["surfaces"]["errors"], rep["surfaces"]
        finally:
            os.chmod(str(sub), 0o755)

    def test_t146_24(self, tmp_path):
        """T146-24:DECLARED_OK 佈置 ⇒ category None、runtime_assurance UNPROVEN、第二行含「未證明」(runtime 未證明不得降級 static state);對應 invariant 後半。"""
        root = self._repo_with_policies(tmp_path / "r", self._text(self._allowlist()), self._text(self._inventory()))
        claude = tmp_path / "claude"
        claude.mkdir()
        rep = self._t3e_report(root, claude)
        assert rep["observation"] == "ok", rep
        assert rep["state"] == self._api("EXT_DECLARED_OK"), rep
        assert rep["category"] is None, rep
        assert rep["runtime_assurance"] == "UNPROVEN", rep
        assert u"未證明" in rep["lines"][1], rep["lines"]

    def test_t146_36(self, tmp_path):
        """T146-36:extension_report 回傳恰好十三鍵(3f:+inventory、+synced);對應 invariant 前半。"""
        root, claude = self._t3e_clean(tmp_path)
        rep = self._t3e_report(root, claude)
        assert set(rep) == {"facts", "surfaces", "state", "category", "reason", "lines",
                            "runtime_assurance", "claude_root", "claude_root_source",
                            "authority", "observation", "inventory", "synced", "policy_source"}, sorted(rep)

    # ── 3f(S3f-146-1):synced 納管 —— inventory、匿名邏輯路徑、逐檔驗證 ─────────
    #
    # 契約在票 146〈3f 裁決與 v2 synced 契約〉。claude_root 一律 tmp;bucket 真名只出現在磁碟佈置,
    # 期望值一律寫邏輯路徑("<bucket>" 字面值;常數本身由 T146-40 鎖)。「synced 空」= 兩個根都不存在。

    _INVENTORY_REL = ".agents/extension-inventory.json"
    _T3F_D = "d0d0-skills-bucket"
    _T3F_E = "e0e0-plugins-bucket"
    _T3F_SHA = "a" * 64

    @staticmethod
    def _inventory(pairs=(), **extra):
        """inventory 文件:pairs 為 (邏輯路徑, sha256),產生 {"path","sha256","note"}(v2 synced 契約)。"""
        doc = {"schema": "monkeyleash.extension-inventory", "version": 1,
               "entries": [{"path": p, "sha256": s, "note": "t146"} for p, s in pairs]}
        doc.update(extra)
        return doc

    def _repo_with_policies(self, root, allowlist_text, inventory_text, commit=True):
        """真的 git repo:README + allowlist(不為 None ⇒ 寫入並提交)+ inventory(不為 None ⇒ 寫入;
        `commit` 為真才一起提交,為假 ⇒ 只在工作樹)。不改 `_repo`。"""
        root = pathlib.Path(str(root))
        root.mkdir(parents=True, exist_ok=True)
        _g_write(root, "README.md", u"t146\n")
        tracked = ["README.md"]
        if allowlist_text is not None:
            _g_write(root, self._ALLOWLIST_REL, allowlist_text)
            tracked.append(self._ALLOWLIST_REL)
        if inventory_text is not None:
            _g_write(root, self._INVENTORY_REL, inventory_text)
            if commit:
                tracked.append(self._INVENTORY_REL)
        _d_git(root, "init", "-q")
        _d_git(root, "config", "user.email", "t@example.invalid")
        _d_git(root, "config", "user.name", "t")
        _d_git(root, "add", *tracked)
        _d_git(root, "commit", "-q", "-m", "baseline")
        return root

    @staticmethod
    def _t3f_bucket(claude, root_name, bucket, files, marker=b"marker\n"):
        """<claude>/<root_name>/synced/ 佈置唯一 bucket(目錄 + 同名 marker);回 {邏輯路徑: sha256}。"""
        import hashlib
        base = pathlib.Path(str(claude)) / root_name / "synced"
        (base / bucket).mkdir(parents=True, exist_ok=True)
        (base / (".bucket-" + bucket)).write_bytes(marker)
        out = {root_name + "/.bucket-<bucket>": hashlib.sha256(marker).hexdigest()}
        for rel, data in files.items():
            p = base / bucket / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
            out[root_name + "/<bucket>/" + rel] = hashlib.sha256(data).hexdigest()
        return out

    def _t3f_layout(self, claude):
        """兩個 synced 根各一個 bucket;回 {邏輯路徑: sha256}(四筆)。"""
        exp = self._t3f_bucket(claude, "skills", self._T3F_D, {"foo/SKILL.md": b"skill\n"})
        exp.update(self._t3f_bucket(claude, "plugins", self._T3F_E, {".marketplaces.json": b"{}\n"}))
        return exp

    def _t3f_report(self, repo_root, claude_root, **kw):
        """extension_report;注入參數不在簽名上 ⇒ 測試內紅。"""
        import inspect
        fn = self._api("extension_report")
        for name in kw:
            assert name in inspect.signature(fn).parameters, \
                "v0 contract not implemented: extension_report(%s=)" % name
        return fn(str(repo_root), str(claude_root), **kw)

    def _t3f_governed(self, tmp_path, extra_pairs=(), commit=True):
        """claude 佈兩根;inventory = 實際集合(+ extra_pairs);allowlist 空白。回 (repo, claude, 期望 mapping)。"""
        claude = tmp_path / "claude"
        claude.mkdir()
        exp = self._t3f_layout(claude)
        pairs = sorted(exp.items()) + list(extra_pairs)
        root = self._repo_with_policies(tmp_path / "r", self._text(self._allowlist()),
                                        self._text(self._inventory(pairs)), commit=commit)
        return root, claude, exp

    @pytest.mark.parametrize("case", [
        "constants", "uninitialized", "uncommitted", "worktree_differs", "identity_mismatch",
        "malformed-missing-note", "malformed-null-sha256",
        "malformed-path-skills-x", "malformed-path-other-root", "malformed-path-no-R",
        "malformed-path-token-twice", "malformed-path-dotbucket-in-R",
        "malformed-duplicate-path", "malformed-dotdot", "ok-empty", "ok-four-forms"])
    def test_t146_40(self, tmp_path, case):
        """T146-40:inventory 常數鎖 + extension_inventory_facts 六態(malformed 子案;合法含空 entries ⇒ ok);對應裁決 (gg)(hh)(tt)。"""
        if case == "constants":
            expected = {"EXT_INVENTORY_FILE": ".agents/extension-inventory.json",
                        "EXT_INVENTORY_SCHEMA": "monkeyleash.extension-inventory",
                        "EXT_INVENTORY_FIELDS": ("schema", "version", "entries"),
                        "EXT_SYNCED_ROOTS": ("skills", "plugins"),
                        "EXT_BUCKET_TOKEN": "<bucket>"}
            for name, value in expected.items():
                assert self._api(name) == value, (name, getattr(redlight, name, None))
            version = self._api("EXT_INVENTORY_VERSION")
            assert type(version) is int and version == 1, version
            sentinel = self._api("EXT_INVENTORY_UNCHECKED")
            assert not isinstance(sentinel, (str, bytes, bool, int, dict, list, tuple)), sentinel
            assert sentinel is getattr(redlight, "EXT_INVENTORY_UNCHECKED"), sentinel
            return
        fn = self._api("extension_inventory_facts")
        allow = self._text(self._allowlist())
        sha = self._T3F_SHA
        good = [("skills/<bucket>/a.md", sha)]
        docs = {
            "malformed-missing-note": {"schema": "monkeyleash.extension-inventory", "version": 1,
                                       "entries": [{"path": "skills/<bucket>/a.md", "sha256": sha}]},
            "malformed-null-sha256": {"schema": "monkeyleash.extension-inventory", "version": 1,
                                      "entries": [{"path": "skills/<bucket>/a.md", "sha256": None, "note": "t146"}]},
            "malformed-path-skills-x": self._inventory([("skills/x.md", sha)]),
            "malformed-path-other-root": self._inventory([("other/<bucket>/x", sha)]),
            "malformed-path-no-R": self._inventory([("skills/<bucket>", sha)]),
            "malformed-path-token-twice": self._inventory([("skills/<bucket>/a/<bucket>/b", sha)]),
            "malformed-path-dotbucket-in-R": self._inventory([("skills/<bucket>/.bucket-x", sha)]),
            "malformed-duplicate-path": self._inventory(good + [("skills/<bucket>/a.md", "b" * 64)]),
            "malformed-dotdot": self._inventory([("skills/<bucket>/a/../b.md", sha)]),
            "ok-empty": self._inventory(),
            "ok-four-forms": self._inventory([("skills/<bucket>/a.md", sha), ("plugins/<bucket>/b.json", sha),
                                              ("skills/.bucket-<bucket>", sha), ("plugins/.bucket-<bucket>", sha)]),
        }
        if case == "uninitialized":
            root = self._repo_with_policies(tmp_path / "r", allow, None)
        elif case == "uncommitted":
            root = self._repo_with_policies(tmp_path / "r", allow, self._text(self._inventory(good)), commit=False)
        elif case == "worktree_differs":
            text = self._text(self._inventory(good))
            root = self._repo_with_policies(tmp_path / "r", allow, text)
            _g_write(root, self._INVENTORY_REL, text + "\n")
        elif case == "identity_mismatch":
            root = self._repo_with_policies(tmp_path / "r", allow, self._text(self._inventory(good)))
            (root / ".agents" / "extension-inventory.json").unlink()
        else:
            root = self._repo_with_policies(tmp_path / "r", allow, self._text(docs[case]))
        facts = fn(str(root))
        if case.startswith("ok-"):
            want = "ok"
        elif case.startswith("malformed-"):
            want = "malformed"
        else:
            want = case
        assert facts["state"] == want, (case, facts)
        if want == "ok":
            assert facts["policy"] is not None, facts
        else:
            assert facts["policy"] is None, facts

    def test_t146_41(self, tmp_path):
        """T146-41:匿名邏輯路徑 —— 兩根各一個 bucket ⇒ synced_files 恰為四筆 (邏輯路徑, sha256),不含 bucket 真名,errors 為空;對應裁決 (ii)(mm)(tt)。"""
        claude = tmp_path / "claude"
        claude.mkdir()
        exp = self._t3f_layout(claude)
        root = self._repo_with_policies(tmp_path / "r", self._text(self._allowlist()), None)
        rep = self._t3f_report(root, claude)
        surfaces = rep["surfaces"]
        got = dict(tuple(x) for x in surfaces["synced_files"])
        assert got == exp, (got, exp)
        assert not [p for p in got if self._T3F_D in p or self._T3F_E in p], sorted(got)
        assert list(surfaces["errors"]) == [], surfaces["errors"]

    @pytest.mark.parametrize("case", [
        "two-dirs", "marker-mismatch", "extra-root-file",
        pytest.param("root-child-symlink", marks=pytest.mark.skipif(
            "os.name == 'nt'", reason="Windows 建 symlink 需要額外權限;POSIX 才產得出來")),
        pytest.param("marker-symlink", marks=pytest.mark.skipif(
            "os.name == 'nt'", reason="Windows 建 symlink 需要額外權限;POSIX 才產得出來")),
        pytest.param("root-is-symlink", marks=pytest.mark.skipif(
            "os.name == 'nt'", reason="Windows 建 symlink 需要額外權限;POSIX 才產得出來")),
        "root-is-file"])
    def test_t146_42(self, tmp_path, case):
        """T146-42:bucket 結構錯誤 ⇒ errors 含 ("synced", <path>, "bucket structure: …"),該根不走訪,synced_verification 不通過;對應裁決 (ii)(tt)。"""
        import os
        claude = tmp_path / "claude"
        claude.mkdir()
        base = claude / "skills" / "synced"
        bucket = self._T3F_D
        if case == "root-is-file":
            base.parent.mkdir(parents=True)
            base.write_bytes(b"not a directory\n")
        elif case == "root-is-symlink":
            elsewhere = tmp_path / "elsewhere"
            self._t3f_bucket(elsewhere, "skills", bucket, {"foo/SKILL.md": b"skill\n"})
            base.parent.mkdir(parents=True)
            os.symlink(str(elsewhere / "skills" / "synced"), str(base))
        else:
            self._t3f_bucket(claude, "skills", bucket, {"foo/SKILL.md": b"skill\n"})
            marker = base / (".bucket-" + bucket)
            if case == "two-dirs":
                (base / "second-bucket").mkdir()
            elif case == "marker-mismatch":
                os.rename(str(marker), str(base / ".bucket-someone-else"))
            elif case == "extra-root-file":
                (base / "stray.txt").write_bytes(b"stray\n")
            elif case == "root-child-symlink":
                os.symlink(str(base / bucket / "foo" / "SKILL.md"), str(base / "link"))
            elif case == "marker-symlink":
                target = tmp_path / "marker-target"
                target.write_bytes(marker.read_bytes())
                marker.unlink()
                os.symlink(str(target), str(marker))
        root = self._repo_with_policies(tmp_path / "r", self._text(self._allowlist()), self._text(self._inventory()))
        rep = self._t3f_report(root, claude)
        errors = [tuple(e) for e in rep["surfaces"]["errors"]]
        hits = [e for e in errors if len(e) == 3 and e[0] == "synced" and str(e[2]).startswith("bucket structure:")]
        assert hits, (case, errors)
        walked = [tuple(x)[0] for x in rep["surfaces"]["synced_files"] if tuple(x)[0].startswith("skills/")]
        assert walked == [], (case, walked)
        v = rep["synced"]
        assert v["verified"] is False and v["structure_errors"] >= 1, (case, v)

    @pytest.mark.parametrize("case", [
        "i-match", "ii-extra", "iii-missing", "iv-content",
        pytest.param("v-symlink", marks=pytest.mark.skipif(
            "os.name == 'nt'", reason="Windows 建 symlink 需要額外權限;POSIX 才產得出來")),
        "vi-worktree-only", "vii-none-nonempty", "viii-none-empty", "ix-malformed-empty",
        "x-empty-empty", "xi-read-failure"])
    def test_t146_43(self, tmp_path, case):
        """T146-43:逐檔驗證 —— 集合與內容完全一致才通過;額外 / 缺少 / 內容不符 / symlink / 讀取失敗 / 未納管都不通過且不得 DECLARED_OK;對應裁決 (jj)(kk)(rr)(ss)。"""
        import os
        ok = self._api("EXT_DECLARED_OK")
        unknown = self._api("EXT_UNKNOWN")
        unmanaged = self._api("EXT_CAT_UNMANAGED")
        verify = self._api("synced_verification")
        first = self._api("_extension_first_reason")
        if case in ("i-match", "x-empty-empty"):
            if case == "i-match":
                root, claude, _exp = self._t3f_governed(tmp_path)
            else:
                claude = tmp_path / "claude"
                claude.mkdir()
                root = self._repo_with_policies(tmp_path / "r", self._text(self._allowlist()),
                                                self._text(self._inventory()))
            rep = self._t3f_report(root, claude)
            assert rep["synced"]["verified"] is True, rep["synced"]
            assert rep["state"] == ok, rep
            return
        if case in ("vii-none-nonempty", "viii-none-empty", "ix-malformed-empty"):
            claude = tmp_path / "claude"
            claude.mkdir()
            if case == "vii-none-nonempty":
                self._t3f_layout(claude)
            inventory_text = None
            if case == "ix-malformed-empty":
                inventory_text = self._text(self._inventory(entries=None))
            root = self._repo_with_policies(tmp_path / "r", self._text(self._allowlist()), inventory_text)
            rep = self._t3f_report(root, claude)
            inv = None
            if case == "ix-malformed-empty":
                inv = self._api("extension_inventory_facts")(str(root))
                assert inv["state"] == "malformed", inv
            v = verify(inv, rep["surfaces"])
            assert v["verified"] is False and u"未納管" in v["reason"], (case, v)
            if case == "vii-none-nonempty":
                assert u"未納管：inventory absent" in v["reason"], v
            res = first(rep["facts"], rep["surfaces"], inv)
            assert res[0] != ok, (case, res)
            return
        extra = []
        if case == "iii-missing":
            extra = [("skills/<bucket>/gone.md", self._T3F_SHA)]
        elif case == "v-symlink":
            extra = [("skills/<bucket>/link.md", self._T3F_SHA)]
        root, claude, _exp = self._t3f_governed(tmp_path, extra_pairs=extra, commit=(case != "vi-worktree-only"))
        bucket = claude / "skills" / "synced" / self._T3F_D
        kw = {}
        if case == "ii-extra":
            (bucket / "extra.md").write_bytes(b"extra\n")
        elif case == "iv-content":
            (bucket / "foo" / "SKILL.md").write_bytes(b"skilL\n")
        elif case == "v-symlink":
            os.symlink(str(bucket / "foo" / "SKILL.md"), str(bucket / "link.md"))
        elif case == "xi-read-failure":
            target = os.path.normcase(os.path.abspath(str(bucket / "foo" / "SKILL.md")))

            def read_bytes(p):
                if os.path.normcase(os.path.abspath(str(p))) == target:
                    raise PermissionError(13, "injected read failure", str(p))
                with open(str(p), "rb") as f:
                    return f.read()
            kw["read_bytes"] = read_bytes
        rep = self._t3f_report(root, claude, **kw)
        v = rep["synced"]
        assert v["verified"] is False, (case, v)
        if case == "ii-extra":
            assert v["extra"] == 1 and u"額外" in v["reason"], v
        elif case == "iii-missing":
            assert v["missing"] == 1 and u"缺少" in v["reason"], v
        elif case == "iv-content":
            assert v["mismatch"] == 1 and u"內容不符" in v["reason"], v
        elif case == "v-symlink":
            assert v["mismatch"] >= 1, v
        elif case == "vi-worktree-only":
            assert u"未納管" in v["reason"], v
        elif case == "xi-read-failure":
            assert ("skills/<bucket>/foo/SKILL.md", None) in [tuple(x) for x in rep["surfaces"]["synced_files"]], \
                rep["surfaces"]["synced_files"]
            assert v["mismatch"] >= 1 and u"內容不符" in v["reason"], v
        assert (rep["state"], rep["category"]) == (unknown, unmanaged), (case, rep["state"], rep["category"])
        assert u"未受管入口：synced" in (rep["reason"] or u""), (case, rep["reason"])

    def test_t146_44(self, tmp_path, monkeypatch):
        """T146-44:extension_report 十三鍵、synced 六鍵、inventory 與 extension_inventory_facts 同態;沒有 inventory ⇒ uninitialized 且 UNKNOWN;前置觀測失敗 ⇒ inventory / synced 為 None;判定恰好 1 次並收到 report["inventory"];對應裁決 (rr)、z1。"""
        keys = {"facts", "surfaces", "state", "category", "reason", "lines", "runtime_assurance",
                "claude_root", "claude_root_source", "authority", "observation", "inventory", "synced",
                "policy_source"}
        six = {"verified", "reason", "missing", "extra", "mismatch", "structure_errors"}
        inventory_facts = self._api("extension_inventory_facts")
        orig = self._api("_extension_first_reason")
        root, claude, _exp = self._t3f_governed(tmp_path)
        calls = []

        def counting(*a, **k):
            calls.append((a, k))
            return orig(*a, **k)
        monkeypatch.setattr(redlight, "_extension_first_reason", counting)
        rep = self._t3f_report(root, claude)
        assert set(rep) == keys, sorted(rep)
        assert set(rep["synced"]) == six, sorted(rep["synced"])
        assert rep["inventory"]["state"] == inventory_facts(str(root))["state"], rep["inventory"]
        assert len(calls) == 1, calls
        a, k = calls[0]
        passed = a[2] if len(a) > 2 else k.get("inventory")
        assert passed == rep["inventory"], (passed, rep["inventory"])
        bare = self._repo_with_policies(tmp_path / "bare", self._text(self._allowlist()), None)
        rep2 = self._t3f_report(bare, claude)
        assert rep2["inventory"] is not None and rep2["inventory"]["state"] == "uninitialized", rep2["inventory"]
        assert rep2["state"] == self._api("EXT_UNKNOWN"), rep2
        del calls[:]
        bad = self._api("extension_report")(str(root), str(tmp_path / "missing-claude-root"))
        assert bad["inventory"] is None and bad["synced"] is None, bad
        assert calls == [], calls

    def test_t146_45(self, tmp_path):
        """T146-45:兩參數相容 wrapper 傳 EXT_INVENTORY_UNCHECKED —— synced 非空 ⇒ UNKNOWN「未評估」;synced 空 ⇒ 不因 synced 變 UNKNOWN;與三參數直接呼叫一致;對應 v2 契約第 8 步。"""
        lines_fn = self._api("extension_status_lines")
        state_fn = self._api("extension_state")
        first = self._api("_extension_first_reason")
        render = self._api("_extension_render_lines")
        unchecked = self._api("EXT_INVENTORY_UNCHECKED")
        ok = self._api("EXT_DECLARED_OK")
        claude = tmp_path / "claude"
        claude.mkdir()
        self._t3f_layout(claude)
        root = self._repo_with_policies(tmp_path / "r", self._text(self._allowlist()), None)
        rep = self._t3f_report(root, claude)
        facts, surfaces = rep["facts"], rep["surfaces"]
        lines = lines_fn(facts, surfaces)
        assert "UNKNOWN" in lines[0] and u"未評估" in lines[0], lines
        res = first(facts, surfaces, unchecked)
        assert res[0] == state_fn(facts, surfaces), (res, state_fn(facts, surfaces))
        assert list(lines) == list(render(res[0], res[1], res[2], facts)), (lines, res)
        empty = tmp_path / "claude-empty"
        empty.mkdir()
        rep2 = self._t3f_report(root, empty)
        lines2 = lines_fn(rep2["facts"], rep2["surfaces"])
        assert state_fn(rep2["facts"], rep2["surfaces"]) == ok, lines2
        assert "UNKNOWN" not in lines2[0], lines2
        assert first(rep2["facts"], rep2["surfaces"], unchecked)[0] == ok

    # ── 3f-2(S3f2-146-1):synced_dirs 成對、空根、root 名錯誤、部分根走訪 ─────────

    def _t3f2_surfaces(self, base, synced_dirs):
        """其他入口乾淨(tmp、路徑注入)、synced_dirs 照傳 → extension_surface_facts。"""
        base = pathlib.Path(str(base))
        dev = base / "dev-mods"
        dev.mkdir(parents=True, exist_ok=True)
        canon = base / "canon"
        _g_write(canon, "s/SKILL.md", u"skill\n")
        user_skills = base / "user-skills"
        user_skills.mkdir(parents=True, exist_ok=True)
        user_commands = base / "user-commands"
        user_commands.mkdir(parents=True, exist_ok=True)
        fn = self._api("extension_surface_facts")
        return fn(str(dev), list(synced_dirs), str(canon), [], [], str(base / "absent.mcp.json"),
                  str(user_skills), str(user_commands))

    @pytest.mark.parametrize("case", ["empty-root"])
    def test_t146_42b(self, tmp_path, case):
        """T146-42[empty-root]:skills/synced 存在、列舉成功、沒有任何直接子項(跨平台)⇒ synced_files 空、errors 空;與合法空 inventory ⇒ synced_verification True;對應裁決 (ww)。"""
        claude = tmp_path / "claude"
        (claude / "skills" / "synced").mkdir(parents=True)
        root = self._repo_with_policies(tmp_path / "r", self._text(self._allowlist()), self._text(self._inventory()))
        rep = self._t3f_report(root, claude)
        assert list(rep["surfaces"]["synced_files"]) == [], rep["surfaces"]["synced_files"]
        assert list(rep["surfaces"]["errors"]) == [], rep["surfaces"]["errors"]
        assert rep["synced"]["verified"] is True, rep["synced"]

    @pytest.mark.parametrize("case", ["a-invalid-name", "b-duplicate-skills", "c-duplicate-skills-plus-plugins",
                                      "d-valid-pair"])
    def test_t146_46(self, tmp_path, case):
        """T146-46:synced_dirs 為 (root_name, path) 對 —— 無效名 / 重複名 ⇒ 結構化錯誤且該名所有項目不走訪;其他唯一合法根照常;對應裁決 (xx)。"""
        p0 = tmp_path / "p0"
        p1 = tmp_path / "p1"
        p2 = tmp_path / "p2"
        p3 = tmp_path / "p3"
        self._t3f_bucket(p0, "skills", self._T3F_D, {"foo/SKILL.md": b"skill\n"})
        self._t3f_bucket(p1, "skills", self._T3F_D, {"foo/SKILL.md": b"skill\n"})
        self._t3f_bucket(p2, "skills", "f0f0-second-bucket", {"bar/SKILL.md": b"other\n"})
        exp_plugins = self._t3f_bucket(p3, "plugins", self._T3F_E, {".marketplaces.json": b"{}\n"})
        exp_skills = self._t3f_bucket(tmp_path / "p1-expected", "skills", self._T3F_D, {"foo/SKILL.md": b"skill\n"})
        s0 = str(p0 / "skills" / "synced")
        s1 = str(p1 / "skills" / "synced")
        s2 = str(p2 / "skills" / "synced")
        s3 = str(p3 / "plugins" / "synced")
        pairs = {"a-invalid-name": [("other", s0)],
                 "b-duplicate-skills": [("skills", s1), ("skills", s2)],
                 "c-duplicate-skills-plus-plugins": [("skills", s1), ("skills", s2), ("plugins", s3)],
                 "d-valid-pair": [("skills", s1), ("plugins", s3)]}[case]
        surfaces = self._t3f2_surfaces(tmp_path / "s", pairs)
        errors = [tuple(e) for e in surfaces["errors"]]
        got = dict(tuple(x) for x in surfaces["synced_files"])
        if case == "a-invalid-name":
            hits = [e for e in errors if len(e) == 3 and e[0] == "synced" and "invalid root name" in str(e[2])]
            assert hits, errors
            assert got == {}, got
        elif case in ("b-duplicate-skills", "c-duplicate-skills-plus-plugins"):
            hits = [e for e in errors if len(e) == 3 and e[0] == "synced" and "duplicate root name" in str(e[2])]
            assert len(hits) == 2, errors
            assert not [p for p in got if p.startswith("skills/")], sorted(got)
            if case == "c-duplicate-skills-plus-plugins":
                for path, sha in exp_plugins.items():
                    assert got.get(path) == sha, (path, sorted(got))
        else:
            assert errors == [], errors
            want = dict(exp_skills)
            want.update(exp_plugins)
            assert got == want, (sorted(got), sorted(want))

    def test_t146_47(self, tmp_path):
        """T146-47:skills 根結構錯誤(兩個目錄)+ plugins 根合法 ⇒ errors 有 skills 的結構錯誤、無任何 skills/ 項目;plugins 的 marker 與檔照常觀測;對應裁決 (yy)。"""
        claude = tmp_path / "claude"
        claude.mkdir()
        self._t3f_bucket(claude, "skills", self._T3F_D, {"foo/SKILL.md": b"skill\n"})
        (claude / "skills" / "synced" / "second-bucket").mkdir()
        exp_plugins = self._t3f_bucket(claude, "plugins", self._T3F_E, {".marketplaces.json": b"{}\n"})
        root = self._repo_with_policies(tmp_path / "r", self._text(self._allowlist()), self._text(self._inventory()))
        rep = self._t3f_report(root, claude)
        errors = [tuple(e) for e in rep["surfaces"]["errors"]]
        hits = [e for e in errors if len(e) == 3 and e[0] == "synced" and str(e[2]).startswith("bucket structure:")
                and "skills" in str(e[1])]
        assert hits, errors
        got = dict(tuple(x) for x in rep["surfaces"]["synced_files"])
        assert not [p for p in got if p.startswith("skills/")], sorted(got)
        assert got.get("plugins/.bucket-<bucket>") == exp_plugins["plugins/.bucket-<bucket>"], sorted(got)
        assert [p for p in got if p.startswith("plugins/<bucket>/")], sorted(got)


# ─────────────────────────────────────────────────────────────────────────────
# 票 146 第三站 3g 紅燈(S3g-146-1)—— policy-only commit 的 index 通道(H-6)與完整 inventory validator
#
# 契約在票 146〈3g 契約與紅燈〉。新名稱 / 新參數一律在測試內取得;缺 ⇒ 該 node 以 AttributeError / TypeError 紅。
# 文件形狀沿用 `TestTicket146ExtensionIntegrity` 的 staticmethod(`_allowlist` / `_inventory` / `_text`),只呼叫、不修改。
# ─────────────────────────────────────────────────────────────────────────────

_IP = TestTicket146ExtensionIntegrity
_IP_FACTS = {"allowlist": ("extension_allowlist_facts", ".agents/extension-allowlist.json"),
             "inventory": ("extension_inventory_facts", ".agents/extension-inventory.json")}


def _ip_git(root, *args, **kw):
    return _d_subprocess.run(["git"] + list(args), cwd=str(root), capture_output=True, check=True, **kw)


def _ip_repo(root):
    """真的 git repo:只提交 README(policy 由各案自己 stage)。"""
    root = pathlib.Path(str(root))
    root.mkdir(parents=True, exist_ok=True)
    _g_write(root, "README.md", u"t146 index\n")
    _ip_git(root, "init", "-q")
    _ip_git(root, "config", "user.email", "t@example.invalid")
    _ip_git(root, "config", "user.name", "t")
    _ip_git(root, "add", "README.md")
    _ip_git(root, "commit", "-q", "-m", "baseline")
    return root


def _ip_valid_text(kind):
    return _IP._text(_IP._allowlist() if kind == "allowlist" else _IP._inventory())


class TestTicket146IndexPolicy:
    """票 146 3g:facts 的 policy_source="index"、report 的 policy_source 鍵、inventory validator、gate 的純字串路徑常數。"""

    @pytest.mark.parametrize("case", ["a-missing", "b-ok", "c-worktree-garbage", "d-worktree-deleted",
                                      "e-conflict", "f-nonregular", "g-malformed", "h-bad-source"])
    @pytest.mark.parametrize("kind", ["allowlist", "inventory"])
    def test_t146_71_facts_policy_source_index_states(self, tmp_path, kind, case):
        """T146-71(behavior-red):index 模式的六種結果與 ValueError;index 合法時 worktree 的內容或存在與否不影響結果。
        BASELINE 紅因:allowlist facts 沒有 policy_source 參數(TypeError);inventory facts 不存在(AttributeError)。"""
        import json
        name, rel = _IP_FACTS[kind]
        fn = getattr(redlight, name)
        root = _ip_repo(tmp_path / "r")
        text = _ip_valid_text(kind)
        if case == "h-bad-source":
            with pytest.raises(ValueError):
                fn(str(root), policy_source="worktree")
            return
        if case in ("b-ok", "c-worktree-garbage", "d-worktree-deleted"):
            _g_write(root, rel, text)
            _ip_git(root, "add", rel)
            if case == "c-worktree-garbage":
                _g_write(root, rel, u"{garbage")
            elif case == "d-worktree-deleted":
                (root / rel).unlink()
            facts = fn(str(root), policy_source="index")
            assert facts["state"] == "ok", facts
            staged = _ip_git(root, "rev-parse", ":" + rel).stdout.decode().strip()
            assert facts["blob"] == staged, (facts, staged)
            assert facts["policy"] == json.loads(text), facts
            return
        if case == "e-conflict":
            blob = _ip_git(root, "hash-object", "-w", "--stdin", input=text.encode("utf-8")).stdout.decode().strip()
            info = "".join("100644 %s %d\t%s\n" % (blob, st, rel) for st in (1, 2, 3))
            _ip_git(root, "update-index", "--index-info", input=info.encode("utf-8"))
            want = "index_conflict"
        elif case == "f-nonregular":
            blob = _ip_git(root, "hash-object", "-w", "--stdin", input=b"target-of-link").stdout.decode().strip()
            _ip_git(root, "update-index", "--index-info", input=("120000 %s 0\t%s\n" % (blob, rel)).encode("utf-8"))
            want = "index_nonregular"
        elif case == "g-malformed":
            _g_write(root, rel, u"not json at all\n")
            _ip_git(root, "add", rel)
            want = "malformed"
        else:
            want = "index_missing"
        facts = fn(str(root), policy_source="index")
        assert facts["state"] == want, (case, facts)

    def test_t146_72_report_policy_source_key(self, tmp_path):
        """T146-72(behavior-red):extension_report 十四鍵、policy_source 預設 "head";傳 "index" ⇒ "index";無效 ⇒ ValueError;
        claude_root 無效時仍有該鍵。BASELINE 紅因:`extension_report` 不存在。"""
        fn = getattr(redlight, "extension_report")
        helper = _IP()
        root = helper._repo_with_policies(tmp_path / "r", _IP._text(_IP._allowlist()), _IP._text(_IP._inventory()))
        claude = tmp_path / "claude"
        claude.mkdir()
        keys = {"facts", "surfaces", "state", "category", "reason", "lines", "runtime_assurance", "claude_root",
                "claude_root_source", "authority", "observation", "inventory", "synced", "policy_source"}
        rep = fn(str(root), str(claude))
        assert set(rep) == keys, sorted(rep)
        assert rep["policy_source"] == "head", rep["policy_source"]
        assert fn(str(root), str(claude), policy_source="index")["policy_source"] == "index"
        with pytest.raises(ValueError):
            fn(str(root), str(claude), policy_source="worktree")
        bad = fn(str(root), str(tmp_path / "missing-claude-root"), policy_source="index")
        assert bad.get("policy_source") == "index", sorted(bad)

    @pytest.mark.parametrize("case", [
        "ok-empty", "ok-one", "missing-key", "extra-key", "schema-wrong", "version-str", "entries-not-list",
        "entry-extra-key", "path-bad-form", "path-duplicate", "sha-upper", "sha-63", "note-not-str"])
    def test_t146_73_inventory_ok_validator(self, case):
        """T146-73(behavior-red):`_extension_inventory_ok` 完整驗 schema / version 型別 / 鍵集合 / 每項鍵 / 四種邏輯路徑 /
        path 唯一 / sha256 / note;不拋例外。BASELINE 紅因:`_extension_inventory_ok` 不存在。"""
        ok = getattr(redlight, "_extension_inventory_ok")
        good = {"path": "skills/<bucket>/SKILL.md", "sha256": "a" * 64, "note": "t146"}
        base = {"schema": "monkeyleash.extension-inventory", "version": 1}
        docs = {
            "ok-empty": dict(base, entries=[]),
            "ok-one": dict(base, entries=[good]),
            "missing-key": {"schema": base["schema"], "entries": []},
            "extra-key": dict(base, entries=[], extra=1),
            "schema-wrong": dict(base, schema="other.schema", entries=[]),
            "version-str": dict(base, version="1", entries=[]),
            "entries-not-list": dict(base, entries={}),
            "entry-extra-key": dict(base, entries=[dict(good, more="x")]),
            "path-bad-form": dict(base, entries=[dict(good, path="skills/x")]),
            "path-duplicate": dict(base, entries=[good, dict(good, sha256="b" * 64)]),
            "sha-upper": dict(base, entries=[dict(good, sha256="A" * 64)]),
            "sha-63": dict(base, entries=[dict(good, sha256="a" * 63)]),
            "note-not-str": dict(base, entries=[dict(good, note=1)]),
        }
        want = case.startswith("ok-")
        assert ok(docs[case]) is want, (case, docs[case])

    def test_t146_74_gate_policy_paths_match_redlight(self):
        """T146-74(behavior-red):gate.EXT_POLICY_PATHS == (EXT_ALLOWLIST_FILE, EXT_INVENTORY_FILE);
        gate.py 中它的賦值右側是純字串常數 tuple(AST;不呼叫任何函式)。BASELINE 紅因:`gate.EXT_POLICY_PATHS` 不存在。"""
        import ast
        g = _IP._gate()
        paths = getattr(g, "EXT_POLICY_PATHS")
        assert paths == (redlight.EXT_ALLOWLIST_FILE, getattr(redlight, "EXT_INVENTORY_FILE")), paths
        tree = ast.parse((ROOT / ".claude" / "hooks" / "gate.py").read_text(encoding="utf-8"))
        values = [n.value for n in tree.body if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == "EXT_POLICY_PATHS" for t in n.targets)]
        assert len(values) == 1, len(values)
        v = values[0]
        assert isinstance(v, ast.Tuple) and v.elts, ast.dump(v)
        assert all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in v.elts), ast.dump(v)
