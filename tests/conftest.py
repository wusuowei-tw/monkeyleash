"""Shared pytest fixtures that prevent CI hangs when API keys are absent."""

import os
from unittest.mock import MagicMock, patch

import pytest


def pytest_configure(config):
    for marker in ("unit", "integration", "smoke"):
        config.addinivalue_line("markers", f"{marker}: {marker}-level tests")


_API_KEY_ENV_VARS = (
    "OPENAI_API_KEY",
    "GOOGLE_API_KEY",
    "ANTHROPIC_API_KEY",
    "XAI_API_KEY",
    "DEEPSEEK_API_KEY",
    "DASHSCOPE_API_KEY",
    "DASHSCOPE_CN_API_KEY",
    "ZHIPU_API_KEY",
    "ZHIPU_CN_API_KEY",
    "MINIMAX_API_KEY",
    "MINIMAX_CN_API_KEY",
    "OPENROUTER_API_KEY",
    "AZURE_OPENAI_API_KEY",
    "ALPHA_VANTAGE_API_KEY",
)


@pytest.fixture(autouse=True)
def _dummy_api_keys(monkeypatch):
    for env_var in _API_KEY_ENV_VARS:
        monkeypatch.setenv(env_var, os.environ.get(env_var, "placeholder"))


@pytest.fixture(autouse=True)
def _isolate_live_gate_state(tmp_path, monkeypatch):
    """把**每一個**已載入的 gate 模組的證據路徑指到 tmp。

    由來(量化實測):框架測試把合成的 fixture 條目寫進宿主真實的
    `shadow-log`(4 筆變 13 筆)。證據檔是**閘門的判定依據** ——
    shadow-log 決定影子要不要晉升,test-runs.jsonl 決定 R3 的紅燈半。
    往裡面寫測試造的假紀錄,等於讓測試去改變閘門之後的判斷。

    **不靠「每條測試記得 monkeypatch」**:那是紀律,而紀律會漏 ——
    上游的 test_shadow.py 兩處都有 patch,漏掉的是**間接**走到
    `log_shadow()` 的那些(影子開著時,任何 check 被擋都會寫一筆)。
    所以改成機制:autouse,而且走訪 `sys.modules` ——
    各測試檔用 `spec_from_file_location` 各載一份 gate,只改一個沒有用。

    **同時修掉「測試假設影子是關的」**:`SHADOW_STATE` 指到 tmp 的不存在路徑,
    影子在測試中因此恆為關、可決定。影子開的那個方向由**成對的**測試
    自己開(見 tests/test_shadow.py),不再靠宿主 repo 碰巧是什麼狀態。

    `test-runs.jsonl` **不在這裡改**:紅燈紀錄是由 conftest 的紀錄器在
    每次真實執行後追加的,那是機制的正常產出,不是污染。
    """
    fields = {
        "SHADOW_LOG": tmp_path / "shadow-log.jsonl",
        "SHADOW_STATE": tmp_path / "shadow.json",
        "EXEMPTION_LOG": tmp_path / "gate-exemptions.jsonl",
        "PROVENANCE": tmp_path / "provenance.jsonl",
    }
    for mod in _loaded_gate_modules():
        for name, path in fields.items():
            if hasattr(mod, name):
                monkeypatch.setattr(mod, name, str(path))


def _loaded_gate_modules():
    """找出所有已載入的 gate 模組實例。

    **不能只走訪 `sys.modules`**:各測試檔用
    `importlib.util.module_from_spec()` + `exec_module()` 載入,
    那條路徑**不會把模組註冊進 `sys.modules`** ——
    第一版的隔離 fixture 因此是空轉的,而且完全無聲。
    (抓到它的是本檔配套的接線測試,不是我。)

    改成從**測試模組的屬性**去找:每個測試檔都把載進來的 gate 綁在模組層變數上
    (`gate = _load()`),所以走訪 tests/ 底下的模組、看它們持有什麼就找得到。
    新增的測試檔不必做任何事就會被涵蓋 —— 這是機制,不是紀律。

    限制(誠實寫出來):在**測試函式內部**才載入的那份蓋不到,
    因為 fixture 在 setup 時就跑完了。所以測試檔要在模組層載 gate。
    """
    import sys as _sys
    out, seen = [], set()
    for mod in list(_sys.modules.values()):
        f = (getattr(mod, "__file__", None) or "").replace("\\", "/")
        if "/tests/" not in f:
            continue
        for attr in vars(mod).values():
            gf = (getattr(attr, "__file__", None) or "").replace("\\", "/")
            if gf.endswith(".claude/hooks/gate.py") and id(attr) not in seen:
                seen.add(id(attr))
                out.append(attr)
    return out


@pytest.fixture()
def mock_llm_client():
    client = MagicMock()
    client.get_llm.return_value = MagicMock()
    with patch(
        "tradingagents.llm_clients.factory.create_llm_client",
        return_value=client,
    ):
        yield client


# ─────────────────────────────────────────────────────────────────────────────
# 紅燈紀錄外掛 —— R3 的另一半(F-012 的規格掉件)。
#
# 綁在**執行測試這個動作本身**上,不是綁在「記得用某個指令」上:
# 用 IDE 跑、用 python -m pytest 跑、CI 跑,都會被記錄。
# 這也是靜默替換失敗的解藥:替換沒中 → 行為沒變 → 測試不會從紅轉綠 → 機制當場抓到。
# ─────────────────────────────────────────────────────────────────────────────

import importlib.util as _ilu
import pathlib as _pl

_ROOT = _pl.Path(__file__).resolve().parents[1]
_spec = _ilu.spec_from_file_location("_redlight", _ROOT / ".claude" / "hooks" / "redlight.py")
_redlight = _ilu.module_from_spec(_spec)
try:
    _spec.loader.exec_module(_redlight)
except Exception:
    _redlight = None

_outcomes = {}


def pytest_collectreport(report):
    """收集錯誤也算紅燈。

    **新模組的第一次紅燈幾乎都是這種** —— 實作還不存在,import 就掛了。
    只吃 when=="call" 的話這種紅燈完全不產生紀錄,於是 R3 的後半對每一個新模組
    都不可能誠實滿足,規則只剩繞過一條路。實際撞到過(可攜化票 01)。
    """
    if _redlight is None or not getattr(report, "failed", False):
        return
    f = str(getattr(report, "nodeid", "")).split("::", 1)[0].replace("\\", "/")
    if f.endswith(".py"):
        _outcomes.setdefault(f, {"failed": []})["failed"].append("<collection error>")


def pytest_runtest_logreport(report):
    # setup/teardown 失敗同樣算數:fixture 拋例外只產生 setup 報告,
    # 只認 call 的話「一次不綠的執行」會被記成綠。
    if report.when not in ("call", "setup", "teardown") or _redlight is None:
        return
    # 取自 nodeid,不是 fspath。nodeid 本來就帶著相對 rootdir 的路徑;
    # fspath 在會 chdir 的測試底下 resolve 到別處,relative_to 直接 ValueError,
    # 整個 session INTERNALERROR 中止 —— 紀錄器把它要觀測的東西弄死了。
    f = report.nodeid.split("::", 1)[0].replace("\\", "/")
    rec = _outcomes.setdefault(f, {"failed": []})
    if report.failed:
        rec["failed"].append(report.nodeid.split("::", 1)[-1])


def pytest_sessionfinish(session, exitstatus):
    if _redlight is None:
        return
    for f, rec in _outcomes.items():
        _redlight.record_run(f, passed=not rec["failed"], failed_tests=rec["failed"])
