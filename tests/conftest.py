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
        # 票 49:攔截帳本。`INTERCEPT_LOG` 是**基底檔名**,月檔由
        # `intercept_path()` 從它推出來 —— 蓋住基底就蓋住整族,
        # 隔離不必知道輪替怎麼命名(新增一種月檔不必回來改這裡)。
        "INTERCEPT_LOG": tmp_path / "intercepts.jsonl",
        "INTERCEPT_SUMMARY": tmp_path / "intercepts-summary.jsonl",
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

# 票 145(M1-a):run 層級的事實 —— 這一次 session 收集了什麼、排除了什麼、
# 每個身分的結果、退出碼。上面的 `_outcomes` 是逐檔的(餵 `record_run`,R3 用),
# 這裡是逐身分的(餵 `record_session`,status 的退紅判定用)。兩份**並存**,
# 不互相推導:逐檔那份的語意(「這個檔這次有沒有失敗」)一個字都不改。
_run = {"selected": None, "deselected": [], "collect_errors": [], "outcomes": {}}


def _nodeid(obj):
    return str(getattr(obj, "nodeid", "") or "").replace("\\", "/")


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
    # 票 145:收集錯誤也是 run 事實(狀態 D 的來源之一)。不限 .py ——
    # conftest 或目錄層級的收集錯誤一樣讓這次 run 不可信。
    _run["collect_errors"].append("%s::<collection error>" % (f or "<session>"))


def pytest_deselected(items):
    """票 145:被 `-k` / `-m` / `--deselect` 排除的身分。

    **deselect 不產生任何 report**(RECON 二.2 B2)—— 不在這裡記,
    事後就看不出那一次的涵蓋範圍有多窄(票 139 的 645 deselected)。
    """
    if _redlight is None:
        return
    _run["deselected"].extend(_nodeid(i) for i in items)


def pytest_collection_finish(session):
    """票 145:deselect 之後真正要跑的身分(= selected)。"""
    if _redlight is None:
        return
    _run["selected"] = [_nodeid(i) for i in getattr(session, "items", None) or []]


def _run_outcome(report):
    """一份 report 對「這個身分的結果」的貢獻。回 None 表示這份 report 不改變結果。

    **屬性一律帶預設值讀** —— 既有測試的假 report 只有 `when` / `failed` /
    `nodeid` / `fspath`;直接讀 `report.skipped` 會讓它們 AttributeError
    (紅燈規劃書一、B-1 約束 4)。
    """
    if getattr(report, "failed", False):
        return "failed"
    # 票 145 Station 4c:xfail / xpass 明確辨識(〈二十三〉7 (vi)),不再籠統記成 other ——
    # other 不算「執行完成」,而 xfail(skipped + wasxfail)與 non-strict xpass(call passed +
    # wasxfail)都是測試確實跑完的終態。strict xpass 是 failed,上面已處理。
    xfail = getattr(report, "wasxfail", None) is not None
    when = getattr(report, "when", None)
    if getattr(report, "skipped", False):
        return "xfail" if xfail else "skipped"
    if when == "call" and getattr(report, "passed", False):
        return "xpass" if xfail else "passed"
    return None


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
    # 票 145:逐身分的結果。`failed` 一旦記下就不被後來的 report 蓋掉
    # (teardown 失敗之前的 call 可能是 passed)。
    got = _run_outcome(report)
    if got is not None and _run["outcomes"].get(_nodeid(report)) != "failed":
        _run["outcomes"][_nodeid(report)] = got


def pytest_sessionfinish(session, exitstatus):
    if _redlight is None:
        return
    for f, rec in _outcomes.items():
        _redlight.record_run(f, passed=not rec["failed"], failed_tests=rec["failed"])
    # 票 145:**每個 session 恰好一筆 run 事實**,寫在逐檔紀錄**之後** ——
    # 0 collected、全部 deselected、invocation 錯誤時上面的迴圈一筆都不寫
    # (RECON Collapse ①),這一筆是那些情形唯一留下的痕跡。
    # 舊版 redlight.py(下游未同步)沒有 record_session ⇒ 照舊只寫逐檔紀錄。
    if not hasattr(_redlight, "record_session"):
        return
    selected = _run["selected"] if _run["selected"] is not None else list(_run["outcomes"])
    kwargs = dict(
        exit_code=exitstatus,
        collected=list(selected) + list(_run["deselected"]) + list(_run["collect_errors"]),
        deselected=list(_run["deselected"]),
        outcomes=dict(_run["outcomes"]),
    )
    # 票 145 Station 4b:涵蓋範圍的判定依據(〈十七〉裁決 1)—— pytest 實際收到的
    # 位置參數與它們的來源。沒有 config ⇒ None ⇒ 涵蓋範圍未知(不知道,就不是完整)。
    # 舊版 redlight.py 的 record_session 沒有 `invocation` 參數 ⇒ 照舊不傳。
    import inspect as _inspect
    params = _inspect.signature(_redlight.record_session).parameters
    if "invocation" in params:
        kwargs["invocation"] = _invocation_of(session)
    # 票 145 Station 4c:選擇 / 執行完整性事實(〈二十三〉7)。收集失敗 ⇒ None ⇒ 涵蓋未知。
    if "completeness" in params:
        kwargs["completeness"] = _completeness_of(session)
    _redlight.record_session(_ROOT, **kwargs)


def _invocation_of(session):
    """session 的呼叫事實:`config.args`、`args_source`、`invocation_params.dir`、`option.pyargs`。

    屬性一律帶預設值讀;沒有 config ⇒ None。
    """
    cfg = getattr(session, "config", None)
    if cfg is None:
        return None
    args = getattr(cfg, "args", None)
    src = getattr(cfg, "args_source", None)
    params = getattr(cfg, "invocation_params", None)
    inv_dir = getattr(params, "dir", None) if params is not None else None
    option = getattr(cfg, "option", None)
    return {
        "args": list(args) if isinstance(args, (list, tuple)) else None,
        "args_source": getattr(src, "name", None) if src is not None else None,
        "invocation_dir": os.fspath(inv_dir) if inv_dir is not None else None,
        "pyargs": bool(getattr(option, "pyargs", False)),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 票 145 Station 4c:選擇 / 執行完整性事實(〈二十三〉7)
#
# **縮小前全集**:`--lf` 在外層 wrapper(`LFPluginCollWrapper`)裡就地改寫 collector 的
# `report.result`,不發 deselected 通知。本 wrapper 標 trylast ⇒ 在 wrapper 鏈的最內層,
# `yield` 之後最先拿到 report,當下**複製** nodeid(之後的就地改寫碰不到這份)。
# 記的是 report 裡的 `pytest.Item`:File collector 的直接子項,以及 Class 之類子 collector 的子項 ——
# class 內的測試不在 File 的 report 裡,只記 File 的話 class 型測試檔的全集永遠對不上。
#
# 存在 `_run` 之外:既有的測試 driver 會在驅動前清空 `_run` 的每個值。
# 收集出錯 ⇒ `_pre_narrowing_broken` ⇒ 本次 completeness 不寫(涵蓋未知)。
# ─────────────────────────────────────────────────────────────────────────────

_pre_narrowing = {}
_pre_narrowing_broken = []


@pytest.hookimpl(wrapper=True, trylast=True)
def pytest_make_collect_report(collector):
    report = yield
    try:
        if _redlight is not None:
            for node in list(getattr(report, "result", None) or []):
                if isinstance(node, pytest.Item):
                    nodeid = _nodeid(node)
                    _pre_narrowing.setdefault(nodeid.split("::", 1)[0], []).append(nodeid)
    except Exception:
        _pre_narrowing_broken.append(True)
    return report


def _plain(value):
    """config.option 的值照原樣記;不是 JSON 原生型別的,記型別名(寫不出來就整筆 session 遺失)。"""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return "<%s>" % type(value).__name__


def _flag(session, name):
    """session 結束時的 shouldstop / shouldfail → bool;屬性不存在 ⇒ None(缺欄 ⇒ 涵蓋未知)。"""
    if not hasattr(session, name):
        return None
    return bool(getattr(session, name))


def _completeness_of(session):
    """本次 session 的完整性事實。任何一步出錯 ⇒ None(寧可多紅,不讓 pytest 失敗)。

    票 145 Station 4d(〈二十九〉2 (vii′)–(xiii))另記收集定義與版本邊界的事實:
    `override_ini` / `inifilename` 讀 `config.option` 的**解析後**值(CLI、PYTEST_ADDOPTS、ini addopts
    都已合併在裡面;不掃 argv);`inipath` 是 pytest 實際採用的設定檔;`config_blobs` 是
    pyproject.toml 與本檔的工作樹 blob vs HEAD blob(git 子程序,失敗 ⇒ None);`pytest_version`
    取自本檔 import 的 `pytest`;`blocked` 是 `list_name_plugin()` 中值為 None 的名稱(`-p no:`)。
    路徑型事實一律轉成 root 相對路徑,不落帳絕對路徑。
    """
    try:
        if _pre_narrowing_broken:
            return None
        cfg = session.config
        option = cfg.option
        pm = cfg.pluginmanager
        name_plugins = pm.list_name_plugin()
        version = getattr(pytest, "__version__", None)
        return {
            "options": dict((k, _plain(getattr(option, k, None)))
                            for k in _redlight.COMPLETENESS_OPTIONS),
            "cacheprovider_blocked": bool(pm.is_blocked("cacheprovider")),
            "shouldstop": _flag(session, "shouldstop"),
            "shouldfail": _flag(session, "shouldfail"),
            "pre_narrowing": dict((f, list(ids)) for f, ids in _pre_narrowing.items()),
            "plugins": _redlight.classify_plugins(_ROOT, name_plugins,
                                                  pm.list_plugin_distinfo()),
            "blocked": _redlight.blocked_plugins(name_plugins),
            "override_ini": _redlight.normalize_overrides(getattr(option, "override_ini", None), _ROOT),
            "inifilename": _redlight.normalize_config_path(getattr(option, "inifilename", None), _ROOT),
            "inipath": _redlight.normalize_config_path(getattr(cfg, "inipath", None), _ROOT),
            "config_blobs": _redlight.committed_blobs(_ROOT),
            "pytest_version": version if isinstance(version, str) else None,
        }
    except Exception:
        return None
