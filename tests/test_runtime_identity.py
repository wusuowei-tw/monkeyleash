# -*- coding: utf-8 -*-
"""票 156 RT3 / RT4 / RT5 / `--whoami` —— 閘門執行環境的身分自檢。

受測對象:`.claude/portable/runtime_identity.py`(本檔寫下時**還不存在**,
這就是紅燈本身)。

## 本檔釘住的介面(S3b 定;實作站照此實作)

    runtime_identity.normalize(name) -> str                 PEP 503 名稱正規化
    runtime_identity.parse_lock(text) -> [(name, version, marker_or_None)]
    runtime_identity.expected_set(lock_texts, marker_env) -> {name: version}
    runtime_identity.boundary_violations(dists, known_dists) -> [(name, version)]
    runtime_identity.evaluate(facts, locks, marker_env, profile) -> (ok, reasons)
        facts   = {"prefix", "base_prefix", "version_info", "repo", "dists": [(name, version)]}
        locks   = {"core": <gates-lock.txt 全文>, "upstream_tests": <全文或 None>}
        profile = "downstream" | "upstream"
    runtime_identity.BOOTSTRAP_EXCEPTIONS                   (名稱, 精確版本) 的 tuple
    CLI:runtime_identity.py --whoami --repo <repo> --profile <profile>

**延遲匯入**:模組在每條測試裡才載入,讓每條各自紅、各自說出原因,
而不是整支檔收集失敗。

**不碰真實環境**:`evaluate` 一律吃注入的 facts;真實的 `.venv-gates`
本檔不讀不寫。唯一的子行程(`--whoami`)跑在 tmp repo 上。

manifest 分類:copy(S3a 6-7;測的是 copy 檔,只用 fixture 與核心鎖定檔)。
只讀上游測試鎖定檔的那幾條在 `tests/test_runtime_identity_upstream.py`(skip)。
"""
import importlib.util
import os
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
RI_PATH = ROOT / ".claude" / "portable" / "runtime_identity.py"
CORE_LOCK = ROOT / ".claude" / "portable" / "gates-lock.txt"


def _ri():
    """延遲載入受測模組。檔案不存在 ⇒ 這一條在這裡紅,訊息說出缺的是什麼。"""
    assert RI_PATH.is_file(), "runtime_identity.py 不存在(票 156 實作站產生):%s" % RI_PATH
    spec = importlib.util.spec_from_file_location("runtime_identity_under_test", str(RI_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _redlight():
    spec = importlib.util.spec_from_file_location(
        "redlight_for_identity", str(ROOT / ".claude" / "hooks" / "redlight.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# 平台 marker 環境(PEP 508 的鍵)。**同一份鎖定檔,兩個平台各自評估** ——
# 測試不問「跑測試的這台機器是什麼」,而是把兩個平台都明寫出來。
WIN_ENV = {
    "os_name": "nt", "sys_platform": "win32", "platform_system": "Windows",
    "platform_machine": "AMD64", "platform_release": "10", "platform_version": "10.0",
    "python_version": "3.11", "python_full_version": "3.11.9",
    "implementation_name": "cpython", "platform_python_implementation": "CPython",
    "implementation_version": "3.11.9", "extra": "",
}
LINUX_ENV = dict(WIN_ENV, os_name="posix", sys_platform="linux", platform_system="Linux",
                 platform_machine="x86_64", platform_release="6.5", platform_version="#1")

# 帶 hash、帶續行、帶平台 marker 的最小鎖定檔(pip --require-hashes 的寫法)。
H = "sha256:" + "a" * 64
CORE_FIXTURE = (
    "# 測試用最小核心鎖定檔\n"
    "pyyaml==6.0.3 \\\n"
    "    --hash=%s\n"
    "pytest==9.1.1 \\\n"
    "    --hash=%s\n"
    "colorama==0.4.6 ; sys_platform == \"win32\" \\\n"
    "    --hash=%s\n" % (H, H, H))
UPSTREAM_FIXTURE = (
    "mcp==1.29.1 \\\n"
    "    --hash=%s\n"
    "anyio==4.15.0 \\\n"
    "    --hash=%s\n" % (H, H))


def _facts(repo, dists, prefix=None, base_prefix="/base", version_info=(3, 11, 9)):
    return {
        "prefix": str(prefix if prefix is not None else pathlib.Path(repo) / ".venv-gates"),
        "base_prefix": base_prefix,
        "version_info": version_info,
        "repo": str(repo),
        "dists": list(dists),
    }


CORE_LINUX_DISTS = [("PyYAML", "6.0.3"), ("pytest", "9.1.1"), ("pip", "24.0")]


# ── RT3:不在 venv / prefix 不是本 repo 的 .venv-gates / 版本不是 3.11 ───────────

class TestRT3PrefixAndVersion:

    def test_rt3_not_in_a_venv_is_refused(self, tmp_path):
        """RT3(a):`sys.prefix == sys.base_prefix` ⇒ 不在 venv ⇒ fail-closed。"""
        ri = _ri()
        f = _facts(tmp_path, CORE_LINUX_DISTS, prefix="/base", base_prefix="/base")
        ok, reasons = ri.evaluate(f, {"core": CORE_FIXTURE, "upstream_tests": None},
                                  LINUX_ENV, "downstream")
        assert ok is False, reasons
        assert any("venv" in r for r in reasons), reasons

    def test_rt3_a_foreign_prefix_is_refused(self, tmp_path):
        """RT3(b):在 venv 裡,但 prefix 不是 `<repo>/.venv-gates` ⇒ fail-closed,訊息指名 `.venv-gates`。"""
        ri = _ri()
        f = _facts(tmp_path, CORE_LINUX_DISTS, prefix=tmp_path / ".venv")
        ok, reasons = ri.evaluate(f, {"core": CORE_FIXTURE, "upstream_tests": None},
                                  LINUX_ENV, "downstream")
        assert ok is False, reasons
        assert any(".venv-gates" in r for r in reasons), reasons

    def test_rt3_python_other_than_3_11_is_refused(self, tmp_path):
        """RT3(c):Python 3.12 ⇒ fail-closed,訊息指名 3.11。"""
        ri = _ri()
        f = _facts(tmp_path, CORE_LINUX_DISTS, version_info=(3, 12, 1))
        ok, reasons = ri.evaluate(f, {"core": CORE_FIXTURE, "upstream_tests": None},
                                  LINUX_ENV, "downstream")
        assert ok is False, reasons
        assert any("3.11" in r for r in reasons), reasons

    def test_rt3_a_correct_downstream_environment_passes(self, tmp_path):
        """RT3 正控:三項都合法、套件恰為 Linux 有效集合 ⇒ ok。
        少了這條,「一律 fail」的實作會讓上面三條全綠。"""
        ri = _ri()
        f = _facts(tmp_path, CORE_LINUX_DISTS)
        ok, reasons = ri.evaluate(f, {"core": CORE_FIXTURE, "upstream_tests": None},
                                  LINUX_ENV, "downstream")
        assert ok is True, reasons


# ── RT4:版本與鎖定檔不符 ⇒ 指名是哪一個套件 ─────────────────────────────────

class TestRT4VersionsMatchTheLock:

    def test_rt4_a_version_mismatch_names_the_package(self, tmp_path):
        ri = _ri()
        dists = [("PyYAML", "6.0.2"), ("pytest", "9.1.1"), ("pip", "24.0")]
        ok, reasons = ri.evaluate(_facts(tmp_path, dists),
                                  {"core": CORE_FIXTURE, "upstream_tests": None},
                                  LINUX_ENV, "downstream")
        assert ok is False, reasons
        assert any("pyyaml" in r.lower() and "6.0.2" in r for r in reasons), reasons

    def test_rt4_a_missing_package_names_the_package(self, tmp_path):
        ri = _ri()
        dists = [("PyYAML", "6.0.3"), ("pip", "24.0")]
        ok, reasons = ri.evaluate(_facts(tmp_path, dists),
                                  {"core": CORE_FIXTURE, "upstream_tests": None},
                                  LINUX_ENV, "downstream")
        assert ok is False, reasons
        assert any("pytest" in r for r in reasons), reasons

    def test_rt4_names_are_compared_after_pep503_normalisation(self, tmp_path):
        """metadata 名稱 `PyYAML` 與鎖定檔名稱 `pyyaml` 是同一個套件(PEP 503)。
        不正規化的話每台機器都會誤紅(R0 B7:metadata 名稱是 `PyYAML`)。"""
        ri = _ri()
        assert ri.normalize("PyYAML") == ri.normalize("pyyaml") == "pyyaml"
        assert ri.normalize("typing_extensions") == ri.normalize("Typing.Extensions")


# ── RT5:依 profile、依平台 marker 的有效集合 ─────────────────────────────────

class TestRT5ProfilesAndMarkers:

    def test_rt5_the_core_lock_has_no_mcp_or_anyio(self):
        """RT5(a):真實的核心鎖定檔不得含 mcp / anyio(D9)。"""
        ri = _ri()
        assert CORE_LOCK.is_file(), "核心鎖定檔不存在:%s" % CORE_LOCK
        names = {n for n, _v, _m in ri.parse_lock(CORE_LOCK.read_text(encoding="utf-8"))}
        assert "mcp" not in names and "anyio" not in names, sorted(names)

    def test_rt5_boundary_only_checks_what_is_present(self):
        """RT5(c):能力邊界只看**實際出現**的項目。"""
        ri = _ri()
        known = _redlight().KNOWN_DISTS
        assert ri.boundary_violations([("anyio", "9.9.9")], known) == [("anyio", "9.9.9")]
        assert ri.boundary_violations([("anyio", "4.15.1")], known) == []
        assert ri.boundary_violations([("PyYAML", "6.0.3")], known) == [], \
            "downstream 沒有 anyio 是合法的,不得要求它存在"

    def test_rt5_upstream_expected_set_is_the_union(self):
        """RT5(d):upstream 的預期集合 = 兩份鎖定檔的聯集(依平台評估之後)。"""
        ri = _ri()
        got = ri.expected_set([CORE_FIXTURE, UPSTREAM_FIXTURE], LINUX_ENV)
        assert got == {"pyyaml": "6.0.3", "pytest": "9.1.1",
                       "mcp": "1.29.1", "anyio": "4.15.0"}, got

    def test_rt5_windows_marker_environment(self):
        """RT5(e) Windows:`sys_platform == "win32"` 的 colorama 屬於有效集合。"""
        ri = _ri()
        got = ri.expected_set([CORE_FIXTURE], WIN_ENV)
        assert got == {"pyyaml": "6.0.3", "pytest": "9.1.1", "colorama": "0.4.6"}, got

    def test_rt5_linux_marker_environment(self, tmp_path):
        """RT5(e) Linux:同一份鎖定檔在 Linux 評估,colorama 不在有效集合;
        Linux 上缺 colorama **不得判紅**。"""
        ri = _ri()
        got = ri.expected_set([CORE_FIXTURE], LINUX_ENV)
        assert got == {"pyyaml": "6.0.3", "pytest": "9.1.1"}, got
        ok, reasons = ri.evaluate(_facts(tmp_path, CORE_LINUX_DISTS),
                                  {"core": CORE_FIXTURE, "upstream_tests": None},
                                  LINUX_ENV, "downstream")
        assert ok is True, reasons

    def test_rt5_an_extra_package_is_refused(self, tmp_path):
        """RT5(f):出現不在預期集合裡的額外套件 ⇒ fail-closed,指名它。"""
        ri = _ri()
        dists = CORE_LINUX_DISTS + [("requests", "2.32.0")]
        ok, reasons = ri.evaluate(_facts(tmp_path, dists),
                                  {"core": CORE_FIXTURE, "upstream_tests": None},
                                  LINUX_ENV, "downstream")
        assert ok is False, reasons
        assert any("requests" in r for r in reasons), reasons

    def test_rt5_downstream_with_mcp_is_refused(self, tmp_path):
        """D9:downstream 不得有 mcp / anyio —— 它們對 downstream profile 就是額外套件。"""
        ri = _ri()
        dists = CORE_LINUX_DISTS + [("mcp", "1.29.1"), ("anyio", "4.15.0")]
        ok, reasons = ri.evaluate(_facts(tmp_path, dists),
                                  {"core": CORE_FIXTURE, "upstream_tests": UPSTREAM_FIXTURE},
                                  LINUX_ENV, "downstream")
        assert ok is False, reasons
        assert any("mcp" in r for r in reasons), reasons

    def test_rt5_upstream_profile_accepts_the_union(self, tmp_path):
        """upstream profile:核心 + 上游測試兩份都裝齊 ⇒ ok。"""
        ri = _ri()
        dists = CORE_LINUX_DISTS + [("mcp", "1.29.1"), ("anyio", "4.15.0")]
        ok, reasons = ri.evaluate(_facts(tmp_path, dists),
                                  {"core": CORE_FIXTURE, "upstream_tests": UPSTREAM_FIXTURE},
                                  LINUX_ENV, "upstream")
        assert ok is True, reasons


# ── D-4:runtime-bootstrap 例外(暫定,實作站觀測後確認)────────────────────────
#
# ⚠ **暫定**(Jeff 2026-10-19 約 20:01,D-4):候選取自底座 Python 3.11.9 的
# `Lib/ensurepip/_bundled/` 檔名(S3a 第 5 節,〔讀碼推論〕)。實作站建出真的
# `.venv-gates` 之後要觀測確認;**觀測結果不同就停下,不得為了讓測試轉綠擴大這份清單。**

class TestD4BootstrapExceptions:

    def test_d4_the_exception_list_is_exactly_pip_and_setuptools(self):
        ri = _ri()
        assert tuple(sorted(ri.BOOTSTRAP_EXCEPTIONS)) == (("pip", "24.0"), ("setuptools", "65.5.0")), \
            ri.BOOTSTRAP_EXCEPTIONS

    def test_d4_setuptools_65_5_0_passes(self, tmp_path):
        ri = _ri()
        dists = CORE_LINUX_DISTS + [("setuptools", "65.5.0")]
        ok, reasons = ri.evaluate(_facts(tmp_path, dists),
                                  {"core": CORE_FIXTURE, "upstream_tests": None},
                                  LINUX_ENV, "downstream")
        assert ok is True, reasons

    def test_d4_setuptools_66_0_is_refused(self, tmp_path):
        """名稱對、版本不對 ⇒ 不是例外 ⇒ fail-closed(名稱＋精確版本)。"""
        ri = _ri()
        dists = CORE_LINUX_DISTS + [("setuptools", "66.0")]
        ok, reasons = ri.evaluate(_facts(tmp_path, dists),
                                  {"core": CORE_FIXTURE, "upstream_tests": None},
                                  LINUX_ENV, "downstream")
        assert ok is False, reasons
        assert any("setuptools" in r for r in reasons), reasons


# ── 鎖定檔解析 ────────────────────────────────────────────────────────────────

def test_parse_lock_reads_names_versions_and_markers():
    ri = _ri()
    got = ri.parse_lock(CORE_FIXTURE)
    assert ("pyyaml", "6.0.3", None) in got, got
    assert ("colorama", "0.4.6", 'sys_platform == "win32"') in got, got
    assert len(got) == 3, got


# ── `--whoami`(D-3:直接呼叫 runtime_identity.py,不經 gatepy 子命令)────────────

def test_whoami_prints_the_identity_and_fails_outside_venv_gates(tmp_path):
    """`runtime_identity.py --whoami --repo <tmp> --profile downstream`。

    在**目前這支直譯器**上跑(它不是 `<tmp>/.venv-gates`)⇒ 必須印出
    profile、直譯器路徑、sys.prefix、Python 版本、套件清單,而且**退出碼非 0**。
    """
    assert RI_PATH.is_file(), "runtime_identity.py 不存在:%s" % RI_PATH
    p = subprocess.run([sys.executable, str(RI_PATH), "--whoami",
                        "--repo", str(tmp_path), "--profile", "downstream"],
                       capture_output=True)
    out = (p.stdout + p.stderr).decode("utf-8", "replace")
    assert p.returncode != 0, "不在 <repo>/.venv-gates 卻回 0:%s" % out
    for needle in ("profile", "downstream", "sys.prefix", sys.prefix,
                   "%d.%d" % sys.version_info[:2]):
        assert needle in out, (needle, out)
    assert os.path.normcase(sys.executable) in os.path.normcase(out), out
