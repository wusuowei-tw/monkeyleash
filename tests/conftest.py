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
