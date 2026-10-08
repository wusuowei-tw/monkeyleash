# -*- coding: utf-8 -*-
"""票 149 第三站紅燈補充 T149-6:平台屬性與缺檔(第四站條件)。

三組(測試名帶組號):
- g1:平台為 Windows 時,S0–S3 任一步的 stat 缺 `st_file_attributes` ⇒ 無法驗證,硬擋。
- g2:平台為 POSIX 時,S0–S3 都沒有 `st_file_attributes` 且內容合法 ⇒ 放行;S0 / S3 為符號連結 ⇒ 仍擋。
- g3:端到端,version 2 名冊的契約檔缺少 ⇒ 只計 missing,不另計 mismatch。

平台判斷只透過 redlight 模組內的單一替換點 `_SYNCED_PLATFORM`(值 "windows" / "posix"),
以 monkeypatch 替換該模組屬性;**不碰全域的 os.name / sys.platform**。
尚不存在的名稱一律在測試函式內 getattr 取得,取不到就 `pytest.fail("介面缺失: <名稱>")`。

不 import tests/test_synced_contract_149.py;必要的輔助函式在此複製。測試資料全部合成。
"""

import hashlib
import importlib.util
import io
import json
import os
import pathlib
import stat
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load_redlight():
    spec = importlib.util.spec_from_file_location(
        "redlight_t149_6", ROOT / ".claude" / "hooks" / "redlight.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


redlight = _load_redlight()

PLATFORM_HOOK = "_SYNCED_PLATFORM"

# ── 合成資料(沿用 T149-4)───────────────────────────────────────────────────

MJ_NAME = "synced-marketplaces-v1"
LCR_NAME = "synced-last-round-v1"
MJ_REL = "plugins/<bucket>/.marketplaces.json"
LCR_REL = "plugins/<bucket>/.last-complete-round"
MARKER_REL = "plugins/.bucket-<bucket>"
BUCKET = "zz149-bucket"
MARKER_BYTES = b"marker149\n"

SYNTH_ID = "marketplace_SynthTestId0000000000000A"
SYNTH_ID_SHA = hashlib.sha256(SYNTH_ID.encode("utf-8")).hexdigest()
SYNTH_UUID = "0f0f0f0f-1111-4222-8333-444455556666"
SYNTH_ETAG = "W/\"synthetic-etag-0001\""


def _row(**over):
    row = {"name": "anthropic-plugin-directory", "display_name": "Anthropic Directory", "scope": "default",
           "source": {"source": "claudeai"}, "id": SYNTH_ID, "updated_at": "2026-01-02T03:04:05.123456Z"}
    row.update(over)
    return row


def _mj_doc(**over):
    doc = {"etag": SYNTH_ETAG, "rows": [_row()], "parserVersion": 1002}
    doc.update(over)
    return doc


def _mj_bytes(doc=None):
    return json.dumps(_mj_doc() if doc is None else doc, ensure_ascii=False).encode("utf-8")


def _lcr_bytes(uuid=SYNTH_UUID, tail=b" "):
    return uuid.encode("ascii") + tail


MJ_PINS = {"id_sha256": SYNTH_ID_SHA}
LCR_PINS = {}

_CONTRACTS = {
    "mj": (MJ_NAME, ".marketplaces.json", _mj_bytes, MJ_PINS),
    "lcr": (LCR_NAME, ".last-complete-round", _lcr_bytes, LCR_PINS),
}


def _write(path, data):
    path = pathlib.Path(str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _api(name):
    value = getattr(redlight, name, None)
    if value is None:
        pytest.fail("介面缺失: %s" % name)
    return value


def _set_platform(monkeypatch, value):
    """唯一的平台替換點:redlight 模組屬性 `_SYNCED_PLATFORM`。不存在 ⇒ 介面缺失。"""
    if getattr(redlight, PLATFORM_HOOK, None) is None:
        pytest.fail("介面缺失: %s" % PLATFORM_HOOK)
    monkeypatch.setattr(redlight, PLATFORM_HOOK, value)


def _assert_blocked(res, category, field):
    assert res == {"category": category, "field": field}, res


# ── 假 stat:可指定哪幾步「沒有」st_file_attributes ────────────────────────────


class _St(object):
    def __init__(self, base, with_attrs=True, **over):
        self.st_mode = base.st_mode
        self.st_size = base.st_size
        self.st_mtime_ns = base.st_mtime_ns
        self.st_dev = base.st_dev
        self.st_ino = base.st_ino
        if with_attrs:
            self.st_file_attributes = getattr(base, "st_file_attributes", 0)
        for k, v in over.items():
            setattr(self, k, v)


def _seq(values):
    calls = [0]

    def fn(_arg):
        i = min(calls[0], len(values) - 1)
        calls[0] += 1
        v = values[i]
        if isinstance(v, BaseException):
            raise v
        return v
    return fn


def _fakes(path, no_attrs=(), over=None):
    """lstat 依序回 S0、S3;fstat 依序回 S1、S2。`no_attrs` 列出的步驟(0–3)不帶 st_file_attributes;
    `over` 為 {步驟: {欄位: 值}}。其餘欄位取真值;身分欄位 0 時補 1。"""
    real = os.stat(str(path))
    base = dict(st_dev=real.st_dev or 1, st_ino=real.st_ino or 1)
    over = over or {}
    vals = [_St(real, with_attrs=(i not in no_attrs), **dict(base, **over.get(i, {}))) for i in range(4)]
    for i in no_attrs:
        assert not hasattr(vals[i], "st_file_attributes"), i
    return {"lstat": _seq([vals[0], vals[3]]), "fstat": _seq([vals[1], vals[2]])}


def _contract_file(tmp_path, key):
    name, fname, make, pins = _CONTRACTS[key]
    return name, _write(tmp_path / "f" / fname, make()), pins


_LINK_MODE = stat.S_IFLNK | 0o777

# ── g1:Windows 屬性缺失 ⇒ 硬擋 ───────────────────────────────────────────────

_G1 = [(k, s) for k in ("mj", "lcr") for s in (0, 1, 2, 3)]


@pytest.mark.parametrize("key, step", _G1, ids=["%s-s%d" % c for c in _G1])
def test_g1_windows_attr_missing_blocks(tmp_path, monkeypatch, key, step):
    """g1:平台 windows,只有 S<step> 缺 st_file_attributes、內容合法 ⇒ contract_read / S<step>_attr_missing。"""
    fn = _api("synced_contract_check")
    _set_platform(monkeypatch, "windows")
    name, p, pins = _contract_file(tmp_path, key)
    res = fn(name, str(p), pins, **_fakes(p, no_attrs=(step,)))
    _assert_blocked(res, "contract_read", "S%d_attr_missing" % step)


# ── g2:POSIX 合法放行;連結仍擋 ──────────────────────────────────────────────


@pytest.mark.parametrize("key", ["mj", "lcr"])
def test_g2_posix_no_attrs_valid_passes(tmp_path, monkeypatch, key):
    """g2:平台 posix,S0–S3 都沒有 st_file_attributes、內容合法 ⇒ None。"""
    fn = _api("synced_contract_check")
    _set_platform(monkeypatch, "posix")
    name, p, pins = _contract_file(tmp_path, key)
    res = fn(name, str(p), pins, **_fakes(p, no_attrs=(0, 1, 2, 3)))
    assert res is None, (key, res)


_G2L = [(k, s) for k in ("mj", "lcr") for s in (0, 3)]


@pytest.mark.parametrize("key, step", _G2L, ids=["%s-s%d" % c for c in _G2L])
def test_g2_posix_link_still_blocks(tmp_path, monkeypatch, key, step):
    """g2:平台 posix,S0–S3 都沒有 st_file_attributes,S<step> 為符號連結 ⇒ contract_read / S<step>_link(沿用已封存代碼)。"""
    fn = _api("synced_contract_check")
    _set_platform(monkeypatch, "posix")
    name, p, pins = _contract_file(tmp_path, key)
    res = fn(name, str(p), pins, **_fakes(p, no_attrs=(0, 1, 2, 3), over={step: {"st_mode": _LINK_MODE}}))
    _assert_blocked(res, "contract_read", "S%d_link" % step)


# ── g3:端到端缺檔只計 missing ───────────────────────────────────────────────

_MARKER_SHA = hashlib.sha256(MARKER_BYTES).hexdigest()

_ALLOWLIST = {"schema": "monkeyleash.extension-allowlist", "version": 1,
              "dev_mod_files": [], "user_skill_plugins": [], "user_commands": [],
              "project_settings_hook_commands": [], "mcp_json_servers": []}


def _sha_entry(path, sha):
    return {"path": path, "sha256": sha, "note": "t149"}


def _contract_entry(path, name, pins):
    return {"path": path, "contract": {"name": name, "pins": pins}, "note": "t149"}


def _v2_doc():
    return {"schema": "monkeyleash.extension-inventory", "version": 2,
            "entries": [_sha_entry(MARKER_REL, _MARKER_SHA), _contract_entry(MJ_REL, MJ_NAME, dict(MJ_PINS)),
                        _contract_entry(LCR_REL, LCR_NAME, dict(LCR_PINS))]}


def _v1_doc():
    return {"schema": "monkeyleash.extension-inventory", "version": 1,
            "entries": [_sha_entry(MARKER_REL, _MARKER_SHA),
                        _sha_entry(MJ_REL, hashlib.sha256(_mj_bytes()).hexdigest()),
                        _sha_entry(LCR_REL, hashlib.sha256(_lcr_bytes()).hexdigest())]}


def _git(root, *args):
    subprocess.run(["git"] + list(args), cwd=str(root), capture_output=True, check=True)


def _text_file(path, doc):
    path = pathlib.Path(str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    with io.open(str(path), "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")


def _setup(tmp_path, inventory_doc, absent):
    """tmp repo(提交 allowlist + inventory)與 tmp claude_root(plugins/synced 唯一 bucket + marker + 兩檔);
    `absent` ∈ {"mj","lcr"} 的那一個契約檔不建立。"""
    root = tmp_path / "repo"
    (root / ".agents").mkdir(parents=True)
    _text_file(root / ".agents" / "extension-allowlist.json", _ALLOWLIST)
    _text_file(root / ".agents" / "extension-inventory.json", inventory_doc)
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@example.invalid")
    _git(root, "config", "user.name", "t")
    _git(root, "add", ".agents/extension-allowlist.json", ".agents/extension-inventory.json")
    _git(root, "commit", "-q", "-m", "baseline")
    claude = tmp_path / "claude"
    base = claude / "plugins" / "synced"
    _write(base / (".bucket-" + BUCKET), MARKER_BYTES)
    if absent != "mj":
        _write(base / BUCKET / ".marketplaces.json", _mj_bytes())
    if absent != "lcr":
        _write(base / BUCKET / ".last-complete-round", _lcr_bytes())
    assert not (base / BUCKET / _CONTRACTS[absent][1]).exists()
    return root, claude


@pytest.mark.parametrize("absent", ["mj", "lcr"], ids=["mj-absent", "lcr-absent"])
def test_g3_end_to_end_v2_missing_counts_only_missing(tmp_path, absent):
    """g3:version 2 合法名冊、一個契約檔缺少、另一個合法 ⇒ verified False、missing 1、mismatch 0、extra 0;
    reason 含 contract_read 與 missing,且不含欄位值。"""
    root, claude = _setup(tmp_path, _v2_doc(), absent)
    v = redlight.extension_report(str(root), str(claude))["synced"]
    assert (v["verified"], v["missing"], v["extra"], v["mismatch"]) == (False, 1, 0, 0), (absent, v)
    reason = v["reason"]
    assert isinstance(reason, str), v
    assert "contract_read" in reason and "missing" in reason, reason
    for needle in (SYNTH_ID, SYNTH_ID_SHA, SYNTH_UUID, "synthetic-etag", BUCKET):
        assert needle not in reason, (needle, reason)


@pytest.mark.parametrize("absent", ["mj", "lcr"], ids=["mj-absent", "lcr-absent"])
def test_g3_control_v1_missing_counts_only_missing(tmp_path, absent):
    """g3(正控):同一個 fixture、version 1 名冊 ⇒ 現行即只計 missing 1、mismatch 0(證明缺檔 fixture 有效)。"""
    root, claude = _setup(tmp_path, _v1_doc(), absent)
    v = redlight.extension_report(str(root), str(claude))["synced"]
    assert (v["verified"], v["missing"], v["extra"], v["mismatch"]) == (False, 1, 0, 0), (absent, v)
