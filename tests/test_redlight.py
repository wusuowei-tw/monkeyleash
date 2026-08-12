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
