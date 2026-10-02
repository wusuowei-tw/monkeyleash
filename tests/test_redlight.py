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
        _c_drive(c, tmp_path, {"tests/test_x.py": [X_A, X_B, X_XF]},
                 selected=[X_A, X_B, X_XF],
                 outcomes={X_A: "passed", X_B: "passed", X_XF: "xfail"},
                 option=_COption(), pm=_c_plugins(c, tmp_path), exitstatus=0)
        runs = redlight.load_runs(str(tmp_path))
        assert len(runs) == 1, runs
        got = redlight.file_coverage(runs[0], "tests/test_x.py")
        assert got == "true", got
