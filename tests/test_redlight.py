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


def _isolated_conftest(monkeypatch, tmp_path):
    c = TestTheRecorderCannotKillTheRunner._conftest()
    monkeypatch.setattr(redlight, "ROOT", str(tmp_path))
    monkeypatch.setattr(redlight, "RUN_LOG",
                        str(tmp_path / ".dev" / "test-runs.jsonl"))
    monkeypatch.setattr(redlight, "PIPELINE",
                        str(tmp_path / ".dev" / "pipeline.json"))
    monkeypatch.setattr(c, "_redlight", redlight)
    monkeypatch.setattr(c, "_ROOT", tmp_path)
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
        got = self._coverage_after(tmp_path, monkeypatch, ["tests/test_x.py"], [X_A, X_B])
        assert got == "true", got

    def test_b1d_a_parent_directory_argument_is_full_coverage(self, tmp_path, monkeypatch):
        """B1d(F3 producer)。分類:interface-red(`redlight.file_coverage` 不存在)。

        位置參數 `tests`(上層目錄)、無 deselected ⇒ 整檔涵蓋。
        """
        got = self._coverage_after(tmp_path, monkeypatch, ["tests"], [X_A, X_B])
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
