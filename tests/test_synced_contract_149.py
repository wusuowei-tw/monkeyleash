# -*- coding: utf-8 -*-
"""票 149 第三站紅燈:synced metadata 兩檔的方案 2 契約 v3(規格唯一來源:票 149〈方案 2 契約 v3(定稿)〉)。

測試名一律帶契約第 8 節的項號(item01 … item18)。

兩種進入點:
- 單元:`redlight.synced_contract_check(name, path, pins, lstat=None, fstat=None)` 與
  `redlight.extension_inventory_check(doc)`。兩者**尚不存在**,一律在測試函式內 getattr 取得,
  取不到就 `pytest.fail("介面缺失: <名稱>")` —— 那只證明介面還沒有,不證明各驗證分支有缺口。
- 端到端:現行已存在的 `redlight.extension_report` / `gate.mode_pre_commit`。

測試資料全部合成:自造的小寫版本 4 UUID、自造的 `marketplace_` id、自造 etag;
合法分支的 pins 放「合成 id 的自算 sha256」。不讀寫真實 inventory 或真實外掛檔。
"""

import hashlib
import importlib.util
import io
import json
import os
import pathlib
import shutil
import stat
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load_redlight():
    spec = importlib.util.spec_from_file_location(
        "redlight_t149", ROOT / ".claude" / "hooks" / "redlight.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


redlight = _load_redlight()

# ── 合成資料 ─────────────────────────────────────────────────────────────────

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
SYNTH_UUID_2 = "a0a0a0a0-2222-4333-9444-555566667777"


def _row(**over):
    row = {"name": "anthropic-plugin-directory", "display_name": "Anthropic Directory", "scope": "default",
           "source": {"source": "claudeai"}, "id": SYNTH_ID, "updated_at": "2026-01-02T03:04:05.123456Z"}
    row.update(over)
    return row


def _mj_doc(**over):
    doc = {"etag": "W/\"synthetic-etag-0001\"", "rows": [_row()], "parserVersion": 1002}
    doc.update(over)
    return doc


def _mj_bytes(doc=None):
    return json.dumps(_mj_doc() if doc is None else doc, ensure_ascii=False).encode("utf-8")


def _lcr_bytes(uuid=SYNTH_UUID, tail=b" "):
    return uuid.encode("ascii") + tail


MJ_PINS = {"id_sha256": SYNTH_ID_SHA}
LCR_PINS = {}


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


def _check_file(tmp_path, name, data, pins, **kw):
    fn = _api("synced_contract_check")
    fname = ".marketplaces.json" if name == MJ_NAME else ".last-complete-round"
    p = _write(tmp_path / "f" / fname, data)
    return fn(name, str(p), pins, **kw)


def _assert_blocked(res, category, field):
    assert res == {"category": category, "field": field}, res


# ── 假 stat(第 10、12、13 項)────────────────────────────────────────────────


class _St(object):
    def __init__(self, base, **over):
        self.st_mode = base.st_mode
        self.st_size = base.st_size
        self.st_mtime_ns = base.st_mtime_ns
        self.st_dev = base.st_dev
        self.st_ino = base.st_ino
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


def _fakes(path, s0=None, s1=None, s2=None, s3=None):
    """lstat 依序回 S0、S3;fstat 依序回 S1、S2。未給的那一步用真值(以 `_St` 包一層,含 st_file_attributes)。"""
    real = os.stat(str(path))
    base = dict(st_dev=real.st_dev or 1, st_ino=real.st_ino or 1)
    s0 = s0 or {}
    s1 = s1 or {}
    s2 = s2 or {}
    s3 = s3 or {}
    v0 = _St(real, **dict(base, **s0))
    v1 = _St(real, **dict(base, **s1))
    v2 = _St(real, **dict(base, **s2))
    v3 = _St(real, **dict(base, **s3))
    return {"lstat": _seq([v0, v3]), "fstat": _seq([v1, v2])}


# ── item01:合法內容放行;只改允許變動的值也放行 ─────────────────────────────


@pytest.mark.parametrize("case", ["mj-base", "mj-etag", "mj-updated_at", "lcr-base", "lcr-uuid"])
def test_item01_valid_passes(tmp_path, case):
    """item01:合法內容放行;只改 etag、updated_at、.last-complete-round 的 UUID 值也放行。"""
    if case == "mj-base":
        res = _check_file(tmp_path, MJ_NAME, _mj_bytes(), MJ_PINS)
    elif case == "mj-etag":
        res = _check_file(tmp_path, MJ_NAME, _mj_bytes(_mj_doc(etag="\"other-synthetic-etag-9\"")), MJ_PINS)
    elif case == "mj-updated_at":
        doc = _mj_doc(rows=[_row(updated_at="2027-12-31T23:59:59.000001Z")])
        res = _check_file(tmp_path, MJ_NAME, _mj_bytes(doc), MJ_PINS)
    elif case == "lcr-base":
        res = _check_file(tmp_path, LCR_NAME, _lcr_bytes(), LCR_PINS)
    else:
        res = _check_file(tmp_path, LCR_NAME, _lcr_bytes(SYNTH_UUID_2), LCR_PINS)
    assert res is None, (case, res)


# ── item02:每個固定欄位各改一個值 ⇒ 擋 ─────────────────────────────────────


@pytest.mark.parametrize("case, doc, field", [
    ("parserVersion", _mj_doc(parserVersion=1003), "parserVersion"),
    ("name", _mj_doc(rows=[_row(name="other-plugin-directory")]), "rows[0].name"),
    ("display_name", _mj_doc(rows=[_row(display_name="Other Directory")]), "rows[0].display_name"),
    ("scope", _mj_doc(rows=[_row(scope="nondefault")]), "rows[0].scope"),
    ("source.source", _mj_doc(rows=[_row(source={"source": "otherorigin"})]), "rows[0].source.source"),
], ids=["parserVersion", "name", "display_name", "scope", "source.source"])
def test_item02_fixed_field_changed_blocks(tmp_path, case, doc, field):
    """item02:固定欄位改值 ⇒ contract_value / <欄位>。"""
    _assert_blocked(_check_file(tmp_path, MJ_NAME, _mj_bytes(doc), MJ_PINS), "contract_value", field)


# ── item03:多一個鍵或少一個鍵 ⇒ 擋 ─────────────────────────────────────────


def _drop(d, key):
    d = dict(d)
    del d[key]
    return d


@pytest.mark.parametrize("doc, field", [
    (dict(_mj_doc(), extra=1), "$"),
    (_drop(_mj_doc(), "etag"), "$"),
    (_mj_doc(rows=[dict(_row(), extra=1)]), "rows[0]"),
    (_mj_doc(rows=[_drop(_row(), "updated_at")]), "rows[0]"),
    (_mj_doc(rows=[_row(source={"source": "claudeai", "extra": "x"})]), "rows[0].source"),
    (_mj_doc(rows=[_row(source={})]), "rows[0].source"),
], ids=["top-extra", "top-missing", "row0-extra", "row0-missing", "source-extra", "source-missing"])
def test_item03_key_set_mismatch_blocks(tmp_path, doc, field):
    """item03:鍵集合不等 ⇒ contract_keys / <物件位置>。"""
    _assert_blocked(_check_file(tmp_path, MJ_NAME, _mj_bytes(doc), MJ_PINS), "contract_keys", field)


# ── item04:重複鍵 ⇒ 擋 ───────────────────────────────────────────────────────

_ROW_TEXT = (u'{"name": "anthropic-plugin-directory", "display_name": "Anthropic Directory", "scope": "default", '
             u'"source": %s, "id": "' + SYNTH_ID + u'", "updated_at": "2026-01-02T03:04:05.123456Z"%s}')


def _mj_text(row_text, top_extra=u""):
    return (u'{"etag": "W/\\"synthetic-etag-0001\\"", "rows": [%s], "parserVersion": 1002%s}'
            % (row_text, top_extra)).encode("utf-8")


@pytest.mark.parametrize("data, field", [
    (_mj_text(_ROW_TEXT % (u'{"source": "claudeai"}', u""), u', "parserVersion": 1002'), "$"),
    (_mj_text(_ROW_TEXT % (u'{"source": "claudeai"}', u', "scope": "default"')), "rows[0]"),
    (_mj_text(_ROW_TEXT % (u'{"source": "claudeai", "source": "claudeai"}', u"")), "rows[0].source"),
], ids=["top", "row0", "source"])
def test_item04_duplicate_key_blocks(tmp_path, data, field):
    """item04:重複鍵(值相同也算)⇒ contract_duplicate_key / <物件位置>。"""
    _assert_blocked(_check_file(tmp_path, MJ_NAME, data, MJ_PINS), "contract_duplicate_key", field)


# ── item05:型別錯誤 ⇒ 擋 ─────────────────────────────────────────────────────


@pytest.mark.parametrize("doc, field", [
    (_mj_doc(parserVersion=True), "parserVersion"),
    (_mj_doc(parserVersion="1002"), "parserVersion"),
    (_mj_doc(rows={"0": _row()}), "rows"),
    (_mj_doc(rows=[[_row()]]), "rows[0]"),
    (_mj_doc(rows=[_row(source="claudeai")]), "rows[0].source"),
    (_mj_doc(rows=[_row(source={"source": 1})]), "rows[0].source.source"),
    (_mj_doc(rows=[_row(name=1)]), "rows[0].name"),
    (_mj_doc(rows=[_row(id=12345)]), "rows[0].id"),
], ids=["parserVersion-true", "parserVersion-str", "rows-object", "row0-array", "source-str",
        "source.source-int", "name-int", "id-int"])
def test_item05_type_error_blocks(tmp_path, doc, field):
    """item05:型別錯誤 ⇒ contract_type / <欄位>(布林不當整數、字串不當數字)。"""
    _assert_blocked(_check_file(tmp_path, MJ_NAME, _mj_bytes(doc), MJ_PINS), "contract_type", field)


# ── item06:id ────────────────────────────────────────────────────────────────

_ESCAPED_ID_JSON = SYNTH_ID.replace("_", "\\u005f")


@pytest.mark.parametrize("case", ["no-prefix", "pin-mismatch", "escaped-parsed-pin-passes", "escaped-raw-pin-blocks"])
def test_item06_id(tmp_path, case):
    """item06:沒有 marketplace_ 前綴 ⇒ contract_format;hash ≠ 核准值 ⇒ contract_pin;
    含跳脫字元的 id 以解析後的值算 hash(以解析值為 pin ⇒ 放行;以原始跳脫字串為 pin ⇒ 擋)。"""
    if case == "no-prefix":
        bad = "mkt_SynthTestId0000000000000A"
        pins = {"id_sha256": hashlib.sha256(bad.encode("utf-8")).hexdigest()}
        res = _check_file(tmp_path, MJ_NAME, _mj_bytes(_mj_doc(rows=[_row(id=bad)])), pins)
        _assert_blocked(res, "contract_format", "rows[0].id")
        return
    if case == "pin-mismatch":
        res = _check_file(tmp_path, MJ_NAME, _mj_bytes(), {"id_sha256": "0" * 64})
        _assert_blocked(res, "contract_pin", "rows[0].id")
        return
    text = _mj_bytes().decode("utf-8").replace(SYNTH_ID, _ESCAPED_ID_JSON).encode("utf-8")
    assert _ESCAPED_ID_JSON.encode("utf-8") in text
    if case == "escaped-parsed-pin-passes":
        assert _check_file(tmp_path, MJ_NAME, text, MJ_PINS) is None
    else:
        raw_pin = {"id_sha256": hashlib.sha256(_ESCAPED_ID_JSON.encode("utf-8")).hexdigest()}
        _assert_blocked(_check_file(tmp_path, MJ_NAME, text, raw_pin), "contract_pin", "rows[0].id")


# ── item07:etag / updated_at 格式 ────────────────────────────────────────────


@pytest.mark.parametrize("doc, field", [
    (_mj_doc(etag=""), "etag"),
    (_mj_doc(etag="e" * 129), "etag"),
    (_mj_doc(etag="has space"), "etag"),
    (_mj_doc(etag="ctl\u0001x"), "etag"),
    (_mj_doc(etag="café"), "etag"),
    (_mj_doc(rows=[_row(updated_at="2026-01-02T03:04:05.123456")]), "rows[0].updated_at"),
    (_mj_doc(rows=[_row(updated_at="2026-01-02T03:04:05.123456+00:00")]), "rows[0].updated_at"),
    (_mj_doc(rows=[_row(updated_at="2026-02-30T03:04:05.123456Z")]), "rows[0].updated_at"),
], ids=["etag-empty", "etag-129", "etag-space", "etag-control", "etag-nonascii",
        "updated_at-noZ", "updated_at-offset", "updated_at-feb30"])
def test_item07_format_blocks(tmp_path, doc, field):
    """item07:etag 長度 1–128、可列印 ASCII、無空白與控制字元;updated_at 精確格式且日期存在 ⇒ 違反即 contract_format。"""
    _assert_blocked(_check_file(tmp_path, MJ_NAME, _mj_bytes(doc), MJ_PINS), "contract_format", field)


# ── item08:rows 筆數 ─────────────────────────────────────────────────────────


@pytest.mark.parametrize("doc", [_mj_doc(rows=[]), _mj_doc(rows=[_row(), _row()])], ids=["zero", "two"])
def test_item08_rows_count_blocks(tmp_path, doc):
    """item08:rows 為 0 筆或 2 筆 ⇒ contract_rows_count / rows。"""
    _assert_blocked(_check_file(tmp_path, MJ_NAME, _mj_bytes(doc), MJ_PINS), "contract_rows_count", "rows")


# ── item09:不是 UTF-8、不是 JSON、頂層不是物件 ──────────────────────────────


@pytest.mark.parametrize("data, category, field", [
    (b'{"etag": "\xff"}', "contract_encoding", "utf8"),
    (b'{"etag": ', "contract_json", "parse"),
    (b'[1, 2, 3]', "contract_type", "$"),
], ids=["not-utf8", "not-json", "top-not-object"])
def test_item09_not_utf8_json_object_blocks(tmp_path, data, category, field):
    """item09:不是 UTF-8 / 不是 JSON / 頂層不是物件 ⇒ 擋。"""
    _assert_blocked(_check_file(tmp_path, MJ_NAME, data, MJ_PINS), category, field)


# ── item10:實際讀到的大小超過上限 ───────────────────────────────────────────


@pytest.mark.parametrize("case", ["real-1025", "stat-small-read-large"])
def test_item10_size_cap_blocks(tmp_path, case):
    """item10:.marketplaces.json 上限 1024 bytes;以實際讀到的量判定(含 stat 看起來小、讀的時候大)。"""
    fn = _api("synced_contract_check")
    p = _write(tmp_path / "f" / ".marketplaces.json", b" " * (1025 if case == "real-1025" else 2000))
    kw = {}
    if case == "stat-small-read-large":
        small = {"st_size": 10}
        kw = _fakes(p, s0=small, s1=small, s2=small, s3=small)
    _assert_blocked(fn(MJ_NAME, str(p), MJ_PINS, **kw), "contract_read", "size_cap")


# ── item11:.last-complete-round ─────────────────────────────────────────────


@pytest.mark.parametrize("data, category, field", [
    (SYNTH_UUID[:35].encode("ascii") + b" ", "contract_format", "size"),
    (_lcr_bytes(tail=b"  "), "contract_read", "size_cap"),
    (_lcr_bytes(tail=b"\n"), "contract_format", "trailer"),
    (b"0f0f0f0f_1111_4222_8333_444455556666 ", "contract_format", "uuid"),
    (_lcr_bytes("0F0F0F0F-1111-4222-8333-444455556666"), "contract_format", "uuid_case"),
    (_lcr_bytes("0f0f0f0f-1111-1222-8333-444455556666"), "contract_format", "uuid_version"),
    (_lcr_bytes("0f0f0f0f-1111-4222-c333-444455556666"), "contract_format", "uuid_variant"),
    (b"0f0f0f0f-1111-4222-8333-44445555666\xff ", "contract_encoding", "ascii"),
], ids=["36-bytes", "38-bytes", "trailer-not-0x20", "not-uuid-shape", "uppercase", "version-not-4",
        "variant-not-89ab", "non-ascii"])
def test_item11_last_round_blocks(tmp_path, data, category, field):
    """item11:.last-complete-round 上限 37 bytes;剛好 37、ASCII、全小寫 UUID、版本 4、variant 8/9/a/b、結尾 0x20。"""
    _assert_blocked(_check_file(tmp_path, LCR_NAME, data, LCR_PINS), category, field)


# ── item12:連結 / reparse(S0–S3)與缺檔 ────────────────────────────────────

_LINK_MODE = stat.S_IFLNK | 0o777


@pytest.mark.parametrize("case, field", [
    ("s0-link", "S0_link"), ("s0-reparse", "S0_reparse"), ("s1-reparse", "S1_reparse"),
    ("s2-reparse", "S2_reparse"), ("s3-link", "S3_link"), ("s3-reparse", "S3_reparse"), ("missing", "missing"),
], ids=["s0-link", "s0-reparse", "s1-reparse", "s2-reparse", "s3-link", "s3-reparse", "missing"])
def test_item12_link_reparse_missing_blocks(tmp_path, case, field):
    """item12:任何一步看到連結或 reparse ⇒ contract_read / <步驟>;檔案缺少 ⇒ contract_read / missing。
    以 monkeypatch 的 lstat / fstat 模擬;不建立真的連結或 reparse 點。"""
    fn = _api("synced_contract_check")
    if case == "missing":
        _assert_blocked(fn(MJ_NAME, str(tmp_path / "absent" / ".marketplaces.json"), MJ_PINS),
                        "contract_read", "missing")
        return
    p = _write(tmp_path / "f" / ".marketplaces.json", _mj_bytes())
    rp = {"st_file_attributes": 0x400}
    over = {"s0-link": {"s0": {"st_mode": _LINK_MODE}}, "s0-reparse": {"s0": rp}, "s1-reparse": {"s1": rp},
            "s2-reparse": {"s2": rp}, "s3-link": {"s3": {"st_mode": _LINK_MODE}}, "s3-reparse": {"s3": rp}}[case]
    _assert_blocked(fn(MJ_NAME, str(p), MJ_PINS, **_fakes(p, **over)), "contract_read", field)


# ── item13:讀取競態 ─────────────────────────────────────────────────────────


@pytest.mark.parametrize("over, field", [
    ({"s1": {"st_ino": 999001}}, "S0S1_ident"),
    ({"s1": {"st_size": 1}}, "S0S1_size"),
    ({"s1": {"st_mtime_ns": 1}}, "S0S1_mtime"),
    ({"s2": {"st_size": 1}}, "S1S2_size"),
    ({"s2": {"st_mtime_ns": 1}}, "S1S2_mtime"),
    ({"s3": {"st_ino": 999003}}, "S3S1_ident"),
    ({"s3": {"st_size": 1}}, "S3S1_size"),
    ({"s3": {"st_mtime_ns": 1}}, "S3S1_mtime"),
], ids=["s0s1-ident", "s0s1-size", "s0s1-mtime", "s1s2-size", "s1s2-mtime", "s3s1-ident", "s3s1-size", "s3s1-mtime"])
def test_item13_read_race_blocks(tmp_path, over, field):
    """item13:S0≠S1(身分/大小/修改時間)、S1≠S2(大小/修改時間)、S3≠S1(身分/大小/修改時間)⇒ contract_read。"""
    fn = _api("synced_contract_check")
    p = _write(tmp_path / "f" / ".marketplaces.json", _mj_bytes())
    _assert_blocked(fn(MJ_NAME, str(p), MJ_PINS, **_fakes(p, **over)), "contract_read", field)


# ── inventory 文件 ───────────────────────────────────────────────────────────

_MARKER_SHA = hashlib.sha256(MARKER_BYTES).hexdigest()


def _sha_entry(path, sha):
    return {"path": path, "sha256": sha, "note": "t149"}


def _contract_entry(path, name, pins):
    return {"path": path, "contract": {"name": name, "pins": pins}, "note": "t149"}


def _v2_doc(entries=None):
    if entries is None:
        entries = [_sha_entry(MARKER_REL, _MARKER_SHA), _contract_entry(MJ_REL, MJ_NAME, dict(MJ_PINS)),
                   _contract_entry(LCR_REL, LCR_NAME, dict(LCR_PINS))]
    return {"schema": "monkeyleash.extension-inventory", "version": 2, "entries": entries}


def _v1_doc(pairs):
    return {"schema": "monkeyleash.extension-inventory", "version": 1,
            "entries": [_sha_entry(p, s) for p, s in pairs]}


def _both_entry():
    e = _contract_entry(MJ_REL, MJ_NAME, dict(MJ_PINS))
    e["sha256"] = "a" * 64
    return e


def _v2_with(entry):
    return _v2_doc([_sha_entry(MARKER_REL, _MARKER_SHA), entry, _contract_entry(LCR_REL, LCR_NAME, {})])


_ITEM14 = [
    ("v2-valid", _v2_doc(), None),
    ("both", _v2_with(_both_entry()), ("inventory_schema", "entry_kind")),
    ("neither", _v2_with({"path": MJ_REL, "note": "t149"}), ("inventory_schema", "entry_kind")),
    ("unknown-name", _v2_with(_contract_entry(MJ_REL, "synced-unknown-v9", dict(MJ_PINS))),
     ("inventory_schema", "contract.name")),
    ("pins-missing", _v2_with(_contract_entry(MJ_REL, MJ_NAME, {})), ("inventory_schema", "contract.pins")),
    ("pins-extra", _v2_with(_contract_entry(MJ_REL, MJ_NAME, dict(MJ_PINS, extra=1))),
     ("inventory_schema", "contract.pins")),
    ("pins-type", _v2_with(_contract_entry(MJ_REL, MJ_NAME, {"id_sha256": 123})),
     ("inventory_schema", "contract.pins")),
    ("v1-with-contract", dict(_v2_doc(), version=1), ("inventory_schema", "version")),
    ("version-3", dict(_v2_doc(), version=3), ("inventory_schema", "version")),
]


@pytest.mark.parametrize("case, doc, want", _ITEM14, ids=[c[0] for c in _ITEM14])
def test_item14_inventory_schema(case, doc, want):
    """item14:schema 損壞 ⇒ inventory_schema / <欄位>;合法 version 2 ⇒ None。"""
    fn = _api("extension_inventory_check")
    res = fn(doc)
    if want is None:
        assert res is None, (case, res)
    else:
        _assert_blocked(res, *want)


def test_item14_existing_ok_accepts_valid_v2():
    """item14:既有 `_extension_inventory_ok` 須擴充 ⇒ 合法 version 2 文件為 True(契約第 5 節)。"""
    assert redlight._extension_inventory_ok(_v2_doc()) is True


# ── item15:契約掛錯路徑 ─────────────────────────────────────────────────────

_ITEM15 = [
    ("plugin-body-file", _contract_entry("plugins/<bucket>/foo/plugin.json", MJ_NAME, dict(MJ_PINS))),
    ("skills-root", _contract_entry("skills/<bucket>/.last-complete-round", LCR_NAME, {})),
    ("mj-contract-on-lcr", _contract_entry(LCR_REL, MJ_NAME, dict(MJ_PINS))),
    ("lcr-contract-on-mj", _contract_entry(MJ_REL, LCR_NAME, {})),
]


@pytest.mark.parametrize("case, entry", _ITEM15, ids=[c[0] for c in _ITEM15])
def test_item15_contract_on_wrong_path(case, entry):
    """item15:契約掛到外掛本體檔或其他任何路徑、兩契約互換路徑 ⇒ inventory_schema / contract.path。"""
    fn = _api("extension_inventory_check")
    doc = _v2_doc([_sha_entry(MARKER_REL, _MARKER_SHA), entry])
    _assert_blocked(fn(doc), "inventory_schema", "contract.path")


# ── 端到端 helper(tmp git repo + tmp claude_root)────────────────────────────

_ALLOWLIST = {"schema": "monkeyleash.extension-allowlist", "version": 1,
              "dev_mod_files": [], "user_skill_plugins": [], "user_commands": [],
              "project_settings_hook_commands": [], "mcp_json_servers": []}


def _git(root, *args):
    subprocess.run(["git"] + list(args), cwd=str(root), capture_output=True, check=True)


def _text_file(path, doc):
    path = pathlib.Path(str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    with io.open(str(path), "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")


def _setup(tmp_path, inventory_doc, mj=None, lcr=None, extra_files=None, copy_gate=False):
    """tmp repo(提交 allowlist + inventory)與 tmp claude_root(plugins/synced 唯一 bucket + marker + 兩檔)。"""
    root = tmp_path / "repo"
    (root / ".agents").mkdir(parents=True)
    if copy_gate:
        hooks = root / ".claude" / "hooks"
        hooks.mkdir(parents=True)
        (root / ".dev").mkdir()
        shutil.copy2(str(ROOT / ".claude" / "hooks" / "gate.py"), str(hooks / "gate.py"))
        shutil.copy2(str(ROOT / ".claude" / "hooks" / "redlight.py"), str(hooks / "redlight.py"))
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
    _write(base / BUCKET / ".marketplaces.json", _mj_bytes() if mj is None else mj)
    _write(base / BUCKET / ".last-complete-round", _lcr_bytes() if lcr is None else lcr)
    for rel, data in (extra_files or {}).items():
        _write(base / BUCKET / rel, data)
    return root, claude


def _v1_pairs(mj=None, lcr=None):
    return [(MARKER_REL, _MARKER_SHA),
            (MJ_REL, hashlib.sha256(_mj_bytes() if mj is None else mj).hexdigest()),
            (LCR_REL, hashlib.sha256(_lcr_bytes() if lcr is None else lcr).hexdigest())]


def _report(root, claude):
    return redlight.extension_report(str(root), str(claude))


def _pre_commit(tmp_path, monkeypatch, capsys, inventory_doc, shadow, **files):
    root, claude = _setup(tmp_path, inventory_doc, copy_gate=True, **files)
    spec = importlib.util.spec_from_file_location("gate_t149_%s" % tmp_path.name,
                                                  str(root / ".claude" / "hooks" / "gate.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "_extension_claude_root", lambda: str(claude))
    monkeypatch.setattr(mod, "upstream_shadow_violation", lambda *a, **k: (None, None))
    monkeypatch.setattr(mod, "staged_paths", lambda *a, **k: [])
    for name in ("check_third_axis_mount", "check_to_spec_override", "check_legacy_list",
                 "check_friction_numbers", "check_skill_copies"):
        monkeypatch.setattr(mod, name, lambda *a, **k: [])
    monkeypatch.setattr(mod, "shadow_active", lambda *a, **k: shadow)
    rc = mod.mode_pre_commit()
    return rc, capsys.readouterr().err


def test_item01_end_to_end_valid_v2_declared_ok(tmp_path):
    """item01(端到端):合法 version 2 inventory + 合法兩檔 ⇒ synced verified 且 DECLARED_OK。"""
    root, claude = _setup(tmp_path, _v2_doc())
    rep = _report(root, claude)
    assert rep["synced"]["verified"] is True, rep["synced"]
    assert rep["state"] == redlight.EXT_DECLARED_OK, (rep["state"], rep["reason"])


# ── item16:影子模式下仍硬擋 ─────────────────────────────────────────────────

_ITEM16 = [
    ("contract-value", _v2_doc(), {"mj": _mj_bytes(_mj_doc(rows=[_row(name="other-plugin-directory")]))},
     ("contract_value", "rows[0].name")),
    ("contract-size-cap", _v2_doc(), {"mj": b" " * 1025}, ("contract_read", "size_cap")),
    ("inventory-schema", _v2_with(_contract_entry(MJ_REL, "synced-unknown-v9", dict(MJ_PINS))), {},
     ("inventory_schema", "contract.name")),
]


@pytest.mark.parametrize("case, doc, files, codes", _ITEM16, ids=[c[0] for c in _ITEM16])
def test_item16_shadow_still_hard_blocks_with_codes(tmp_path, monkeypatch, capsys, case, doc, files, codes):
    """item16:影子開著 ⇒ 仍硬擋(rc=1),擋下訊息帶類別與欄位代碼。"""
    rc, err = _pre_commit(tmp_path, monkeypatch, capsys, doc, True, **files)
    assert rc == 1, (case, rc, err)
    assert "[R10/fail-closed]" in err, err
    assert codes[0] in err and codes[1] in err, (case, codes, err)


def test_item16_shadow_v1_hash_mismatch_still_hard_blocks(tmp_path, monkeypatch, capsys):
    """item16(正控):影子開著、version 1 hash 不符 ⇒ 現行即硬擋,不進 violations。"""
    pairs = _v1_pairs()
    pairs[2] = (LCR_REL, "0" * 64)
    rc, err = _pre_commit(tmp_path, monkeypatch, capsys, _v1_doc(pairs), True)
    assert rc == 1, (rc, err)
    assert "[R10/fail-closed] unmanaged_entry" in err and u"內容不符 1" in err, err


# ── item17:錯誤訊息不含欄位值 ───────────────────────────────────────────────

_S17 = "zz17sentinel"
_ITEM17 = [
    ("name", MJ_NAME, _mj_bytes(_mj_doc(rows=[_row(name=_S17 + "-name")])), MJ_PINS),
    ("etag", MJ_NAME, _mj_bytes(_mj_doc(etag=_S17 + " etag")), MJ_PINS),
    ("updated_at", MJ_NAME, _mj_bytes(_mj_doc(rows=[_row(updated_at=_S17 + "-updated")])), MJ_PINS),
    ("id", MJ_NAME, _mj_bytes(_mj_doc(rows=[_row(id="marketplace_" + _S17 + "Id")])), MJ_PINS),
    ("lcr-uuid", LCR_NAME, _lcr_bytes("ABCDEF01-1111-4222-8333-444455556666"), LCR_PINS),
]


@pytest.mark.parametrize("case, name, data, pins", _ITEM17, ids=[c[0] for c in _ITEM17])
def test_item17_reason_has_no_values(tmp_path, case, name, data, pins):
    """item17:擋下結果只有類別與欄位,不含任何欄位值。"""
    res = _check_file(tmp_path, name, data, pins)
    assert isinstance(res, dict) and set(res) == {"category", "field"}, res
    blob = json.dumps(res, ensure_ascii=False)
    for needle in (_S17, "ABCDEF01"):
        assert needle not in blob, (case, blob)


def test_item17_end_to_end_message_has_codes_not_values(tmp_path, monkeypatch, capsys):
    """item17(端到端):擋下訊息帶代碼,但不含測試放入的欄位值。"""
    mj = _mj_bytes(_mj_doc(rows=[_row(name=_S17 + "-name")]))
    rc, err = _pre_commit(tmp_path, monkeypatch, capsys, _v2_doc(), False, mj=mj)
    assert rc == 1, (rc, err)
    assert "contract_value" in err and "rows[0].name" in err, err
    assert _S17 not in err, err


# ── item18:回歸 ─────────────────────────────────────────────────────────────


@pytest.mark.parametrize("case", ["v1-match", "v1-content", "v1-missing", "v1-extra"])
def test_item18_v1_inventory_behavior_unchanged(tmp_path, case):
    """item18(回歸鎖):version 1 inventory 的 hash 嚴格比對行為不變。"""
    pairs = _v1_pairs()
    extra = None
    if case == "v1-content":
        pairs[2] = (LCR_REL, "0" * 64)
    elif case == "v1-missing":
        pairs.append(("plugins/<bucket>/gone.txt", "1" * 64))
    elif case == "v1-extra":
        extra = {"stray.txt": b"stray\n"}
    root, claude = _setup(tmp_path, _v1_doc(pairs), extra_files=extra)
    v = _report(root, claude)["synced"]
    want = {"v1-match": (True, 0, 0, 0), "v1-content": (False, 0, 0, 1),
            "v1-missing": (False, 1, 0, 0), "v1-extra": (False, 0, 1, 0)}[case]
    assert (v["verified"], v["missing"], v["extra"], v["mismatch"]) == want, (case, v)


@pytest.mark.parametrize("case", ["v1-valid", "v1-entry-with-contract-key"])
def test_item18_v1_existing_ok_unchanged(case):
    """item18(回歸鎖):`_extension_inventory_ok` 對 version 1 的判定不變(合法 ⇒ True;項目多出 contract ⇒ False)。"""
    if case == "v1-valid":
        assert redlight._extension_inventory_ok(_v1_doc(_v1_pairs())) is True
    else:
        doc = _v1_doc(_v1_pairs())
        doc["entries"][1]["contract"] = {"name": MJ_NAME, "pins": dict(MJ_PINS)}
        assert redlight._extension_inventory_ok(doc) is False


def test_item18_v2_sha_entries_keep_hash_semantics(tmp_path):
    """item18:version 2 裡的 sha256 項目仍是 hash 嚴格比對(marker 不符 ⇒ 內容不符 1);契約項目合法不計入。"""
    entries = [_sha_entry(MARKER_REL, "0" * 64), _contract_entry(MJ_REL, MJ_NAME, dict(MJ_PINS)),
               _contract_entry(LCR_REL, LCR_NAME, {})]
    root, claude = _setup(tmp_path, _v2_doc(entries))
    v = _report(root, claude)["synced"]
    assert (v["verified"], v["missing"], v["extra"], v["mismatch"]) == (False, 0, 0, 1), v
