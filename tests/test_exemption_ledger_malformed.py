# -*- coding: utf-8 -*-
"""票 167 —— 豁免帳本 malformed record。

malformed record = 該行 `json.loads` 拋例外,或回傳值不是 dict。
空行(strip 後為空)**不算**(裁決 ②:維持跳過)。

測試分兩類,類別寫在測試名的前綴(AC-7):

- `test_red_*`:針對本票**尚未具備**的行為 —— 改動前每一條都必須失敗。
- `test_baseline_*`:針對**現行已具備**的行為(回歸釘子)—— 改動前後都該綠,
  不算 AC-7 的紅燈。

證據隔離:`tests/conftest.py` 的 autouse `_isolate_live_gate_state` 會把本檔
模組層的 `gate` 的 `EXEMPTION_LOG` 換到 tmp;本檔每一條另外再明確
`monkeypatch.setattr(gate, "EXEMPTION_LOG", <tmp 檔>)`,**不碰真帳本**。
`status` / `ledger_verify` 的測試一律把路徑當參數傳,也不碰真帳本。
"""

import hashlib
import importlib.util
import io
import json
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PORTABLE = ROOT / ".claude" / "portable"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# 模組層載入是刻意的:conftest 的隔離 fixture 走訪測試模組的屬性找 gate 實例。
gate = _load("gate_ledger_malformed", ROOT / ".claude" / "hooks" / "gate.py")
lv = _load("ledger_verify_ledger_malformed", PORTABLE / "ledger_verify.py")

if str(PORTABLE) not in sys.path:
    sys.path.insert(0, str(PORTABLE))
import status                      # noqa: E402

LEDGER_REL = ".dev/gate-exemptions.jsonl"

# 四種壞行。(ii)～(iv) 的內容是獨特字串,用來斷言「訊息不回顯原文」。
BAD_LINES = {
    "null": u"null",
    "badjson": u'{"zq_unique_167_badjson":',
    "number": u"9876543210167",
    "string": u'"zq_unique_167_string"',
}
BAD_IDS = list(BAD_LINES)

GOOD = {"file": "pkg/other.py", "module": "other",
        "declared_in": ".scratch/f/issues/01-x.md"}


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_ledger(path, lines):
    """逐行寫入(每行補 `\\n`)。回傳寫入後的位元組,供「沒有被改」的比對。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with io.open(str(path), "w", encoding="utf-8", newline="\n") as f:
        for ln in lines:
            f.write(ln + u"\n")
    return path.read_bytes()


def _good_line():
    return json.dumps(GOOD, ensure_ascii=False)


# ══════════════════════════════════════════════════════════════════════════
# AC-1 —— `logged_exemption_backed` 遇 malformed ⇒ 硬錯誤
# ══════════════════════════════════════════════════════════════════════════

class TestAC1LoggedExemptionBacked:

    @pytest.mark.parametrize("kind", BAD_IDS)
    def test_red_malformed_line_is_a_hard_error(self, kind, tmp_path, monkeypatch, capsys):
        """壞行在**合法紀錄之後**(第 2 行)—— 不得 continue、不得回 False。"""
        led = tmp_path / "gate-exemptions.jsonl"
        _write_ledger(led, [_good_line(), BAD_LINES[kind]])
        monkeypatch.setattr(gate, "EXEMPTION_LOG", str(led))
        with pytest.raises(SystemExit) as ei:
            gate.logged_exemption_backed("pkg/thing.py", "thing")
        assert ei.value.code == 2, u"硬錯誤的退出碼不是 2:%r" % ei.value.code
        err = capsys.readouterr().err
        assert u"行號:2" in err, err

    def test_baseline_blank_lines_and_valid_records_are_read_normally(
            self, tmp_path, monkeypatch):
        """對照(裁決 ②):空行與純空白行跳過,合法紀錄照讀 ⇒ 不匹配就回 False。"""
        led = tmp_path / "gate-exemptions.jsonl"
        _write_ledger(led, [u"", _good_line(), u"   ", u"", _good_line()])
        monkeypatch.setattr(gate, "EXEMPTION_LOG", str(led))
        assert gate.logged_exemption_backed("pkg/thing.py", "thing") is False


# ══════════════════════════════════════════════════════════════════════════
# AC-2 —— 提交時路徑(`check(at_commit=True)` → `:3987` 那一格)硬擋
# ══════════════════════════════════════════════════════════════════════════

WITH_DEF = u"def f():\n    return 1\n"
TARGET = "research/__init__.py"


def _git(args, cwd):
    subprocess.run(["git"] + list(args), cwd=str(cwd), capture_output=True, check=False)


def _commit_world(tmp_path, monkeypatch, ledger_lines):
    """真 git repo,讓 `check(TARGET, None, at_commit=True)` 走到帳本回查(#12)。

    構造沿用 `tests/test_gate.py::TestBarePackageMarkerJudgesTheStagedContent._repo`:
    `research/__init__.py` 含 `def` 且已 `add` ⇒ #11(純套件標記)不豁免;
    R8 對 `research/` 跳過;站別 `implement`、`ticket_id` 為 null ⇒ 票宣告不豁免;
    其餘豁免來源都指向不存在的位置 ⇒ 下一格就是 `logged_exemption_backed`。
    帳本放在 repo 內的 `.dev/gate-exemptions.jsonl`,訊息裡的相對路徑因此與正式環境相同。
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    for c in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        _git(c, repo)
    defs = io.open(str(ROOT / ".agents" / "pipeline-stages.yaml"), encoding="utf-8").read()
    dp = repo / ".agents" / "pipeline-stages.yaml"
    dp.parent.mkdir(parents=True, exist_ok=True)
    io.open(str(dp), "w", encoding="utf-8", newline="\n").write(defs)
    _git(["add", "-A"], repo)
    _git(["commit", "-qm", "seed"], repo)

    p = repo / TARGET
    p.parent.mkdir(parents=True, exist_ok=True)
    io.open(str(p), "w", encoding="utf-8", newline="\n").write(WITH_DEF)
    _git(["add", "-f", "--", TARGET], repo)

    (repo / ".dev").mkdir(exist_ok=True)
    io.open(str(repo / ".dev" / "pipeline.json"), "w", encoding="utf-8",
            newline="\n").write(json.dumps(
                {"current_stage": "implement", "feature": "f", "ticket_id": None}))
    led = repo / ".dev" / "gate-exemptions.jsonl"
    _write_ledger(led, ledger_lines)

    monkeypatch.setattr(gate, "ROOT", str(repo))
    monkeypatch.setattr(gate, "PIPELINE", str(repo / ".dev" / "pipeline.json"))
    monkeypatch.setattr(gate, "EXEMPTION_LOG", str(led))
    monkeypatch.setattr(gate, "PROVENANCE", str(repo / ".dev" / "no-provenance.jsonl"))
    monkeypatch.setattr(gate, "UPSTREAM_ROOTS", str(tmp_path / "no-upstream-roots.txt"))
    monkeypatch.setattr(gate, "LEGACY_LIST", str(repo / ".agents" / "no-legacy.txt"))
    monkeypatch.chdir(repo)
    return repo


class TestAC2CommitPath:

    @pytest.mark.parametrize("kind", BAD_IDS)
    def test_red_commit_path_blocks_with_a_complete_message(
            self, kind, tmp_path, monkeypatch, capsys):
        bad = BAD_LINES[kind]
        _commit_world(tmp_path, monkeypatch, [_good_line(), u"", bad])
        assert gate.staged_text(TARGET)[0] is not None, u"前提垮了:目標不在 index 裡"
        with pytest.raises(SystemExit) as ei:
            gate.check(TARGET, None, at_commit=True, trace=[], exemptions=[])
        assert ei.value.code == 2, u"不是硬擋(退出碼 %r)" % ei.value.code
        err = capsys.readouterr().err
        assert gate.ADVISORY_HEAD not in err, u"走了降級提示:\n%s" % err
        # 訊息必含的六項
        assert LEDGER_REL in err, err
        assert u"行號:3" in err, err
        expected_kind = u"解析失敗" if kind == "badjson" else u"非物件"
        assert u"錯誤類型:" + expected_kind in err, err
        assert u"原始行長度:%d" % len(bad) in err, err
        assert _sha(bad) in err, err
        assert u"修復:" in err and u"quarantine" in err, err
        # 不得回顯原文、不得有 traceback
        assert bad not in err, u"訊息回顯了壞行原文:\n%s" % err
        if kind == "null":
            assert u"null" not in err, err
        assert u"Traceback" not in err, err

    def test_baseline_valid_ledger_reaches_the_ordinary_r3_verdict(
            self, tmp_path, monkeypatch, capsys):
        """對照:帳本只有合法紀錄與空行 ⇒ 不是硬錯誤,照舊走到一般 R3 判定。"""
        _commit_world(tmp_path, monkeypatch, [u"", _good_line(), u""])
        msg = gate.check(TARGET, None, at_commit=True, trace=[], exemptions=[])
        assert msg and u"R3" in msg, msg

    def test_baseline_write_time_path_does_not_read_the_ledger(
            self, tmp_path, monkeypatch):
        """前哨那一半(`at_commit=False`)現行不讀這份帳本 —— 本票不為 AC-2 新增讀取。"""
        _commit_world(tmp_path, monkeypatch, [BAD_LINES["null"]])
        gate.check(TARGET, WITH_DEF, at_commit=False, trace=[], exemptions=[])


# ══════════════════════════════════════════════════════════════════════════
# AC-3 —— 其他讀取端:status 出聲不擋(裁決 ③);ledger_verify 維持 fail
# ══════════════════════════════════════════════════════════════════════════

class TestAC3Status:

    @pytest.mark.parametrize("kind", BAD_IDS)
    def test_red_read_jsonl_lists_the_malformed_line(self, kind, tmp_path):
        led = tmp_path / "x.jsonl"
        _write_ledger(led, [_good_line(), u"", BAD_LINES[kind], _good_line()])
        recs = status._read_jsonl(str(led))
        assert isinstance(recs, list) and len(recs) == 2, recs
        bad = getattr(recs, "malformed", None)
        assert bad, u"壞行被靜默跳過,回傳結構裡沒有它"
        assert len(bad) == 1 and bad[0][0] == 3, bad
        expected_kind = u"解析失敗" if kind == "badjson" else u"非物件"
        assert bad[0][1].startswith(expected_kind), bad

    def test_red_render_names_the_malformed_line(self, tmp_path, monkeypatch):
        root = _status_root(tmp_path, monkeypatch,
                            [_good_line(), BAD_LINES["null"], _good_line()])
        out = status.render(root)
        line = [ln for ln in out.splitlines() if ln.startswith(u"exemptions:")]
        assert line, out
        assert u"壞行" in line[0] and u"第 2 行" in line[0], line[0]
        assert u"總 2 筆" in line[0], u"其餘紀錄沒有照讀:%s" % line[0]

    def test_baseline_read_jsonl_still_returns_the_valid_records(self, tmp_path):
        led = tmp_path / "x.jsonl"
        _write_ledger(led, [_good_line(), u"", u"  ", _good_line()])
        recs = status._read_jsonl(str(led))
        assert recs == [GOOD, GOOD]


def _status_root(tmp_path, monkeypatch, ledger_lines):
    """status 的最小 root(取自 `tests/test_status.py::_make_root` 的必要部分)。"""
    import shutil
    root = tmp_path / "repo"
    (root / ".dev").mkdir(parents=True)
    (root / ".claude" / "hooks").mkdir(parents=True)
    (root / ".agents").mkdir(parents=True)
    with io.open(str(root / ".dev" / "pipeline.json"), "w", encoding="utf-8") as f:
        json.dump({"current_stage": "implement", "feature": "testfeat",
                   "ticket_id": "99", "updated": "2026-11-03"}, f)
    with io.open(str(root / ".claude" / "settings.json"), "w", encoding="utf-8") as f:
        json.dump({"hooks": {}}, f)
    shutil.copy2(str(ROOT / ".claude" / "hooks" / "gate.py"),
                 str(root / ".claude" / "hooks" / "gate.py"))
    shutil.copy2(str(ROOT / ".agents" / "pipeline-stages.yaml"),
                 str(root / ".agents" / "pipeline-stages.yaml"))
    _write_ledger(root / ".dev" / "gate-exemptions.jsonl", ledger_lines)
    claude = tmp_path / "_isolated_claude_root"
    claude.mkdir()
    monkeypatch.setattr(status, "_extension_claude_root", lambda: str(claude))
    return str(root)


class TestAC3LedgerVerify:

    @pytest.mark.parametrize("kind", ["null", "number", "string"])
    def test_red_non_object_line_raises_value_error(self, kind):
        text = u"\n".join([_good_line(), u"", BAD_LINES[kind]]) + u"\n"
        with pytest.raises(ValueError) as ei:
            lv.parse_records(text)
        msg = str(ei.value)
        assert u"第 3 行" in msg and u"不是物件" in msg, msg
        assert BAD_LINES[kind] not in msg, u"訊息回顯了原文:%s" % msg

    def test_baseline_unparseable_line_raises_value_error(self):
        text = u"\n".join([_good_line(), BAD_LINES["badjson"]]) + u"\n"
        with pytest.raises(ValueError) as ei:
            lv.parse_records(text)
        assert u"第 2 行" in str(ei.value)

    def test_baseline_blank_lines_are_skipped(self):
        assert lv.parse_records(u"\n" + _good_line() + u"\n  \n") == [GOOD]


# ══════════════════════════════════════════════════════════════════════════
# AC-4 —— 寫入端 `_append_jsonl` 拒非物件
# ══════════════════════════════════════════════════════════════════════════

class TestAC4AppendJsonl:

    @pytest.mark.parametrize("rec", [None, 42, "x", []], ids=["None", "int", "str", "list"])
    def test_red_non_dict_is_refused(self, rec, tmp_path, capsys):
        led = tmp_path / "x.jsonl"
        before = _write_ledger(led, [_good_line()])
        with pytest.raises(TypeError):
            gate._append_jsonl(str(led), rec)
        assert led.read_bytes() == before, u"非物件被寫進帳本了"
        assert capsys.readouterr().err.strip(), u"拒絕寫入卻沒有出聲"

    def test_red_log_exemptions_turns_a_refused_record_into_a_hard_stop(
            self, tmp_path, monkeypatch):
        """`exemption_record` 若回 None(票 167 §1.2 的假設情境)⇒ 硬擋,帳本不變。"""
        led = tmp_path / "gate-exemptions.jsonl"
        before = _write_ledger(led, [_good_line()])
        monkeypatch.setattr(gate, "EXEMPTION_LOG", str(led))
        monkeypatch.setattr(gate, "exemption_record", lambda *a, **k: None)
        monkeypatch.setattr(gate, "load_stage", lambda: ("implement", "167"))
        with pytest.raises(SystemExit) as ei:
            gate.log_exemptions([dict(GOOD, ticket=None, reason="r")],
                                verdict=None, at_commit=False, content="x")
        assert ei.value.code == 2
        assert led.read_bytes() == before

    def test_baseline_dict_is_appended(self, tmp_path):
        led = tmp_path / "x.jsonl"
        _write_ledger(led, [_good_line()])
        gate._append_jsonl(str(led), {"a": 1})
        lines = led.read_text(encoding="utf-8").splitlines()
        assert lines[-1] == u'{"a": 1}' and len(lines) == 2
