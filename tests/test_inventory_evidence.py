# -*- coding: utf-8 -*-
"""票 165 站一:`.claude/portable/inventory_evidence.py`(collect 與 resume 基本版)。

**全部在 tmp_path 建的暫存假 repo 與假同步樹裡做**:不碰本 repo 的 `.dev/`、名冊,
也不碰使用者層 —— `--claude-root` 一律指向假同步樹,I 區另以替身攔截 `expanduser`
並斷言它沒被呼叫。真實 R10 函式(`extension_report` 等)直接在假資料上跑。

題名帶區碼(`test_ie_<區><號>_...`),區碼對應站一指令 B1 的分區。
本檔與受測工具都標 skip(只供本專案使用,不出貨到下游)。
"""

import hashlib
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / ".claude" / "portable" / "inventory_evidence.py"

# 模組層載入:實作不存在時這裡就失敗(收集錯誤 = 紅燈,R3 的紅燈先行由此產生)。
_spec = importlib.util.spec_from_file_location("inventory_evidence_under_test", MODULE_PATH)
ie = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ie)

BUCKET = "zz-realbucket-77"
TOKEN = "<bucket>"
ROUND_OK = b"123e4567-e89b-42d3-a456-426614174000 "
MARKER = b"marker\n"
FILES = {"a.txt": b"alpha\n", "b.txt": b"beta\n"}
FAKE_ORIGIN = "example.invalid/fake/repo.git"
INVENTORY_REL = ".agents/extension-inventory.json"
ALLOWLIST_REL = ".agents/extension-allowlist.json"
RUN_RE = re.compile(r"\A\d{8}T\d{6}Z-[0-9a-f]{7}\Z")
ARTIFACTS_DONE = ["candidate-inventory.json", "checkpoint.jsonl", "diff.json",
                  "package.json", "snapshot.json", "summary.md"]

ALLOWLIST_DOC = {"schema": "monkeyleash.extension-allowlist", "version": 1, "dev_mod_files": [],
                 "user_skill_plugins": [], "user_commands": [], "project_settings_hook_commands": [],
                 "mcp_json_servers": []}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def logical(rel):
    return "plugins/%s/%s" % (TOKEN, rel)


def git(repo, *args, check=True):
    return subprocess.run(["git", "-C", str(repo)] + list(args), capture_output=True, check=check)


def git_out(repo, *args):
    return git(repo, *args).stdout.decode("utf-8").strip()


def inventory_doc(files):
    entries = [{"path": "plugins/.bucket-%s" % TOKEN, "sha256": sha(MARKER), "note": "seed"}]
    entries += [{"path": logical(rel), "sha256": sha(data), "note": "seed"}
                for rel, data in sorted(files.items())]
    entries.append({"path": logical(".last-complete-round"),
                    "contract": {"name": "synced-last-round-v1", "pins": {}}, "note": "seed"})
    return {"schema": "monkeyleash.extension-inventory", "version": 2, "entries": entries}


def dump(doc):
    return (json.dumps(doc, sort_keys=True, indent=2) + "\n").encode("utf-8")


def make_synced(claude, files, round_bytes=ROUND_OK):
    base = claude / "plugins" / "synced"
    bucket = base / BUCKET
    bucket.mkdir(parents=True)
    (base / (".bucket-" + BUCKET)).write_bytes(MARKER)
    for rel, data in files.items():
        p = bucket / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    (bucket / ".last-complete-round").write_bytes(round_bytes)
    return bucket


def tree_bytes(base, skip=(".git",)):
    """`base` 底下每個檔 → bytes(頂層 `skip` 目錄不進)。"""
    out = {}
    base = str(base)
    for dirpath, dirnames, filenames in os.walk(base):
        rel_dir = os.path.relpath(dirpath, base).replace("\\", "/")
        rel_dir = "" if rel_dir == "." else rel_dir
        dirnames[:] = [d for d in dirnames if not (rel_dir == "" and d in skip)]
        for f in filenames:
            with open(os.path.join(dirpath, f), "rb") as fh:
                out[(rel_dir + "/" + f) if rel_dir else f] = fh.read()
    return out


def read_lines(path):
    return path.read_bytes().split(b"\n")[:-1]


def write_lines(path, lines):
    path.write_bytes(b"".join(line + b"\n" for line in lines))


def line_of(rec):
    return json.dumps(rec, sort_keys=True, ensure_ascii=False).encode("utf-8")


class Clock(object):
    """每呼叫一次往前一秒 —— 同一題內多次 collect 的執行代號不會撞。"""

    def __init__(self):
        self.t = datetime(2026, 10, 29, tzinfo=timezone.utc)

    def __call__(self):
        self.t += timedelta(seconds=1)
        return self.t


class Fx(object):
    def __init__(self, tmp, repo, claude, bucket, capsys):
        self.tmp, self.repo, self.claude, self.bucket, self.capsys = tmp, repo, claude, bucket, capsys

    @property
    def evid(self):
        return self.repo / ".dev" / "inventory-evidence"

    def collect(self, *extra):
        code = ie.main(["collect", "--repo", str(self.repo), "--claude-root", str(self.claude),
                        "--settle-seconds", "0"] + list(extra))
        cap = self.capsys.readouterr()
        return code, cap.out, cap.err

    def resume(self, run):
        code = ie.main(["resume", "--repo", str(self.repo), "--run", run])
        cap = self.capsys.readouterr()
        return code, cap.out, cap.err

    def complete(self):
        code, out, err = self.collect()
        assert code == ie.EXIT_OK, err
        return self.runs()[-1]

    def runs(self):
        if not self.evid.is_dir():
            return []
        return sorted(p.name for p in self.evid.iterdir() if p.is_dir())

    def load(self, run, name):
        return json.loads((self.evid / run / name).read_bytes().decode("utf-8"))

    def events(self, run):
        return [json.loads(line) for line in read_lines(self.evid / run / "checkpoint.jsonl")]

    def index(self):
        path = self.evid / "index.jsonl"
        return [json.loads(line) for line in read_lines(path)] if path.exists() else []

    def commit_all(self, msg="c"):
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", msg)


@pytest.fixture
def fx(tmp_path, monkeypatch, capsys):
    repo = tmp_path / "repo"
    repo.mkdir()
    hooks = tmp_path / "nohooks"
    hooks.mkdir()
    git(repo, "init", "-q")
    for key, value in (("core.autocrlf", "false"), ("core.hooksPath", str(hooks)),
                       ("user.name", "t"), ("user.email", "t@example.invalid"),
                       ("commit.gpgsign", "false")):
        git(repo, "config", key, value)
    (repo / ".gitignore").write_bytes(b"/.dev/*\n")
    (repo / ".agents").mkdir()
    (repo / INVENTORY_REL).write_bytes(dump(inventory_doc(FILES)))
    (repo / ALLOWLIST_REL).write_bytes(dump(ALLOWLIST_DOC))
    (repo / "tracked.txt").write_bytes(b"one\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "seed")
    git(repo, "remote", "add", "origin", FAKE_ORIGIN)
    monkeypatch.setattr(ie, "ROOT_COMMIT", git_out(repo, "rev-list", "--max-parents=0", "HEAD"))
    monkeypatch.setattr(ie, "ORIGIN_URL", FAKE_ORIGIN)
    monkeypatch.setattr(ie, "_now", Clock())
    monkeypatch.setattr(ie, "_sleep", lambda seconds: None)
    claude = tmp_path / "claude"
    bucket = make_synced(claude, FILES)
    return Fx(tmp_path, repo, claude, bucket, capsys)


def drift_live(fx):
    """現場對名冊:a.txt 內容不符、b.txt 刪除、c.txt 新增。"""
    (fx.bucket / "a.txt").write_bytes(b"alpha2\n")
    (fx.bucket / "b.txt").unlink()
    (fx.bucket / "c.txt").write_bytes(b"gamma\n")


def scope_entry(snap, path):
    [entry] = [e for e in snap["protected_scope"] if e["path"] == path]
    return entry


# ── A 區:使用前提 ─────────────────────────────────────────────────────────────

def test_ie_A1_ignored_location_passes_and_produces_full_package(fx):
    code, out, err = fx.collect()
    assert code == ie.EXIT_OK, err
    [run] = fx.runs()
    assert RUN_RE.match(run)
    assert run.endswith("-" + git_out(fx.repo, "rev-parse", "HEAD")[:7])
    assert sorted(os.listdir(str(fx.evid / run))) == ARTIFACTS_DONE
    assert [r["event"] for r in fx.index()] == ["start", "collect_completed"]
    assert not (fx.evid / ".lock").exists()


def test_ie_A1_not_ignored_location_stops_without_writing(fx):
    (fx.repo / ".gitignore").write_bytes(b"")
    fx.commit_all()
    code, out, err = fx.collect()
    assert code == ie.EXIT_PRECONDITION
    assert "(a)" in err
    assert not (fx.repo / ".dev").exists()


def test_ie_A1_resume_also_checks_preconditions(fx):
    run = fx.complete()
    (fx.repo / ".gitignore").write_bytes(b"")
    before = tree_bytes(fx.evid)
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_PRECONDITION
    assert tree_bytes(fx.evid) == before


def test_ie_A2_tracked_file_under_evidence_dir_stops(fx):
    fx.evid.mkdir(parents=True)
    (fx.evid / "x.txt").write_bytes(b"x\n")
    git(fx.repo, "add", "-f", "--", ".dev/inventory-evidence/x.txt")
    git(fx.repo, "commit", "-q", "-m", "x")
    code, out, err = fx.collect()
    assert code == ie.EXIT_PRECONDITION
    assert "(b)" in err
    assert sorted(os.listdir(str(fx.evid))) == ["x.txt"]


def test_ie_A3_staged_item_under_evidence_dir_stops(fx):
    fx.evid.mkdir(parents=True)
    (fx.evid / "x.txt").write_bytes(b"x\n")
    git(fx.repo, "add", "-f", "--", ".dev/inventory-evidence/x.txt")
    git(fx.repo, "commit", "-q", "-m", "x")
    git(fx.repo, "rm", "-q", "--cached", "--", ".dev/inventory-evidence/x.txt")
    assert git_out(fx.repo, "ls-files", "--", ".dev/inventory-evidence") == ""
    code, out, err = fx.collect()
    assert code == ie.EXIT_PRECONDITION
    assert "(c)" in err
    assert sorted(os.listdir(str(fx.evid))) == ["x.txt"]


def _symlink_or_skip(target, link):
    try:
        os.symlink(str(target), str(link), target_is_directory=True)
    except (OSError, NotImplementedError, AttributeError) as e:
        pytest.skip("平台不允許建立 symlink(%s);連結類由其他平台或 junction 題涵蓋" % type(e).__name__)


def test_ie_A4_link_parent_stops_when_target_absent(fx):
    outside = fx.tmp / "outside"
    outside.mkdir()
    _symlink_or_skip(outside, fx.repo / ".dev")
    code, out, err = fx.collect()
    assert code == ie.EXIT_PRECONDITION
    assert "(d)" in err
    assert os.listdir(str(outside)) == []


def test_ie_A4_link_evidence_dir_stops(fx):
    outside = fx.tmp / "outside"
    outside.mkdir()
    (fx.repo / ".dev").mkdir()
    _symlink_or_skip(outside, fx.repo / ".dev" / "inventory-evidence")
    code, out, err = fx.collect()
    assert code == ie.EXIT_PRECONDITION
    assert "(d)" in err
    assert os.listdir(str(outside)) == []


@pytest.mark.skipif(os.name != "nt", reason="junction 只在 Windows 建得出來;其他平台由 symlink 題涵蓋(framework-updates/165)")
def test_ie_A4_junction_parent_stops(fx):
    import _winapi
    outside = fx.tmp / "outside"
    outside.mkdir()
    _winapi.CreateJunction(str(outside), str(fx.repo / ".dev"))
    code, out, err = fx.collect()
    assert code == ie.EXIT_PRECONDITION
    assert "(d)" in err
    assert os.listdir(str(outside)) == []


# ── B 區:支援範圍 ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("marker", ["MERGE_HEAD", "CHERRY_PICK_HEAD", "rebase-merge", "rebase-apply"])
def test_ie_B1_operation_in_progress_refused(fx, marker):
    gitdir = pathlib.Path(git_out(fx.repo, "rev-parse", "--absolute-git-dir"))
    if marker.startswith("rebase"):
        (gitdir / marker).mkdir()
    else:
        (gitdir / marker).write_bytes((git_out(fx.repo, "rev-parse", "HEAD") + "\n").encode("ascii"))
    code, out, err = fx.collect()
    assert code == ie.EXIT_UNSUPPORTED
    assert not (fx.repo / ".dev").exists()


def test_ie_B2_conflict_refused(fx):
    git(fx.repo, "checkout", "-q", "-b", "side")
    (fx.repo / "tracked.txt").write_bytes(b"side\n")
    fx.commit_all()
    git(fx.repo, "checkout", "-q", "-")
    (fx.repo / "tracked.txt").write_bytes(b"main\n")
    fx.commit_all()
    git(fx.repo, "merge", "-q", "side", check=False)
    assert git_out(fx.repo, "ls-files", "-u") != ""
    gitdir = pathlib.Path(git_out(fx.repo, "rev-parse", "--absolute-git-dir"))
    (gitdir / "MERGE_HEAD").unlink()
    code, out, err = fx.collect()
    assert code == ie.EXIT_UNSUPPORTED
    assert "衝突" in err
    assert not (fx.repo / ".dev").exists()


@pytest.mark.parametrize("rel", [INVENTORY_REL, ALLOWLIST_REL])
def test_ie_B3_policy_unstaged_change_refused(fx, rel):
    p = fx.repo / rel
    p.write_bytes(p.read_bytes() + b"\n")
    code, out, err = fx.collect()
    assert code == ie.EXIT_UNSUPPORTED
    assert not (fx.repo / ".dev").exists()


def test_ie_B4_partial_stage_of_other_file_allowed_and_recorded(fx):
    p = fx.repo / "tracked.txt"
    p.write_bytes(b"two\n")
    git(fx.repo, "add", "--", "tracked.txt")
    p.write_bytes(b"three\n")
    run = fx.complete()
    snap = fx.load(run, "snapshot.json")
    assert snap["partially_staged"] == [{"path": "tracked.txt", "mode": "100644",
                                         "blob": git_out(fx.repo, "rev-parse", ":tracked.txt")}]
    assert scope_entry(snap, "tracked.txt")["sha256"] == sha(b"three\n")


def test_ie_B5_submodule_refused(fx):
    head = git_out(fx.repo, "rev-parse", "HEAD")
    git(fx.repo, "update-index", "--add", "--cacheinfo", "160000,%s,sub" % head)
    code, out, err = fx.collect()
    assert code == ie.EXIT_UNSUPPORTED
    assert "submodule" in err
    assert not (fx.repo / ".dev").exists()


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="平台不支援建立 FIFO(framework-updates/165)")
def test_ie_B6_special_file_refused(fx):
    (fx.repo / "tracked.txt").unlink()
    os.mkfifo(str(fx.repo / "tracked.txt"))
    code, out, err = fx.collect()
    assert code == ie.EXIT_UNSUPPORTED
    assert not (fx.repo / ".dev").exists()


def test_ie_B6_directory_where_file_expected_refused(fx):
    (fx.repo / "tracked.txt").unlink()
    (fx.repo / "tracked.txt").mkdir()
    code, out, err = fx.collect()
    assert code == ie.EXIT_UNSUPPORTED
    assert "目錄" in err
    assert not (fx.repo / ".dev").exists()


# ── S 區:快照 ─────────────────────────────────────────────────────────────────

def test_ie_S1_ids_are_full_length(fx):
    (fx.repo / "tracked.txt").write_bytes(b"two\n")
    git(fx.repo, "add", "--", "tracked.txt")
    run = fx.complete()
    snap = fx.load(run, "snapshot.json")
    [entry] = [s for s in snap["staged"] if s["path"] == "tracked.txt"]
    assert entry["status"] == "modified"
    assert entry["head"] == {"exists": True, "mode": "100644",
                             "blob": git_out(fx.repo, "rev-parse", "HEAD:tracked.txt")}
    assert entry["index"] == {"exists": True, "mode": "100644",
                              "blob": git_out(fx.repo, "rev-parse", ":tracked.txt")}
    for value in (entry["head"]["blob"], entry["index"]["blob"], snap["head"]["commit"],
                  snap["policy"]["inventory"]["head_blob"], snap["policy"]["inventory"]["index_blob"],
                  snap["policy"]["allowlist"]["head_blob"], snap["repo_identity"]["root_commit"]):
        assert len(value) == 40 and re.fullmatch(r"[0-9a-f]{40}", value)
    assert snap["repo_identity"]["object_format"] == "sha1"
    assert snap["head"]["commit"] == git_out(fx.repo, "rev-parse", "HEAD")


def test_ie_S2_added_and_deleted_zero_sides_recorded_as_absent(fx, monkeypatch):
    head_blob = git_out(fx.repo, "rev-parse", "HEAD:tracked.txt")
    (fx.repo / "new.txt").write_bytes(b"n\n")
    git(fx.repo, "add", "--", "new.txt")
    git(fx.repo, "rm", "-q", "--", "tracked.txt")
    calls = []
    real = subprocess.run

    def recorder(*args, **kwargs):
        calls.append([str(a) for a in (args[0] if args else kwargs["args"])])
        return real(*args, **kwargs)
    monkeypatch.setattr(subprocess, "run", recorder)
    run = fx.complete()
    snap = fx.load(run, "snapshot.json")
    by = dict((s["path"], s) for s in snap["staged"])
    assert by["new.txt"]["status"] == "added"
    assert by["new.txt"]["head"] == {"exists": False}
    assert by["new.txt"]["index"]["exists"] is True
    assert by["tracked.txt"]["status"] == "deleted"
    assert by["tracked.txt"]["index"] == {"exists": False}
    assert by["tracked.txt"]["head"]["blob"] == head_blob
    zero = "0" * 40
    assert calls and not any(zero in " ".join(c) for c in calls)


def test_ie_S4_deleted_status_recorded(fx):
    head_blob = git_out(fx.repo, "rev-parse", "HEAD:tracked.txt")
    git(fx.repo, "rm", "-q", "--", "tracked.txt")
    run = fx.complete()
    snap = fx.load(run, "snapshot.json")
    assert snap["staged"] == [{"path": "tracked.txt", "status": "deleted",
                               "head": {"exists": True, "mode": "100644", "blob": head_blob},
                               "index": {"exists": False}}]
    assert scope_entry(snap, "tracked.txt") == {"path": "tracked.txt", "exists": False}


A40, B40, Z40 = "a" * 40, "b" * 40, "0" * 40


@pytest.mark.parametrize("meta", [
    ":100644 100644 %s %s M" % (Z40, B40),     # 模式非零而 ID 零值
    ":100644 000000 %s %s M" % (A40, Z40),     # 修改狀態卻在待提交區端出現零值
    ":000000 100644 %s %s D" % (Z40, B40),     # 刪除狀態卻在 HEAD 端出現零值
    ":100644 000000 %s %s A" % (A40, Z40),     # 新增狀態卻在待提交區端出現零值
    ":000000 000000 %s %s A" % (Z40, Z40),     # 兩端都是零值
    ":000000 100644 %s %s A" % (A40, B40),     # 只有模式是零值
    ":100644 100644 %s %s M" % (A40[:7], B40),  # 短碼
])
def test_ie_S3_bad_zero_or_short_ids_stop_internal(meta):
    with pytest.raises(ie.Stop) as e:
        ie.parse_cached_raw(meta.encode("ascii") + b"\0p.txt\0", 40)
    assert e.value.code == ie.EXIT_INTERNAL


def test_ie_S3_valid_zero_sides_parse_as_absent():
    raw = ((":000000 100644 %s %s A" % (Z40, B40)).encode("ascii") + b"\0n.txt\0"
           + (":100644 000000 %s %s D" % (A40, Z40)).encode("ascii") + b"\0d.txt\0")
    assert ie.parse_cached_raw(raw, 40) == [
        {"path": "n.txt", "status": "added", "head": {"exists": False},
         "index": {"exists": True, "mode": "100644", "blob": B40}},
        {"path": "d.txt", "status": "deleted", "head": {"exists": True, "mode": "100644", "blob": A40},
         "index": {"exists": False}},
    ]


def test_ie_S3_substituted_git_output_stops_collect(fx, monkeypatch):
    bad = (":100644 000000 %s %s M" % (A40, Z40)).encode("ascii") + b"\0p.txt\0"
    monkeypatch.setattr(ie, "_cached_raw", lambda root: bad)
    code, out, err = fx.collect()
    assert code == ie.EXIT_INTERNAL
    assert "零值" in err
    assert not (fx.repo / ".dev").exists()


def test_ie_S5_rename_split_into_delete_and_add(fx):
    git(fx.repo, "mv", "tracked.txt", "moved.txt")
    run = fx.complete()
    by = dict((s["path"], s) for s in fx.load(run, "snapshot.json")["staged"])
    assert sorted(by) == ["moved.txt", "tracked.txt"]
    assert by["tracked.txt"]["status"] == "deleted"
    assert by["moved.txt"]["status"] == "added"
    assert by["moved.txt"]["index"]["blob"] == by["tracked.txt"]["head"]["blob"]


def test_ie_S6_worktree_sha_changes_with_content(fx):
    p = fx.repo / "tracked.txt"
    p.write_bytes(b"x\r\n")
    first = scope_entry(fx.load(fx.complete(), "snapshot.json"), "tracked.txt")
    p.write_bytes(b"y\r\n")
    second = scope_entry(fx.load(fx.complete(), "snapshot.json"), "tracked.txt")
    assert first["type"] == second["type"] == "file"
    assert first["sha256"] == sha(b"x\r\n")          # 原始位元組,不轉換換行
    assert second["sha256"] == sha(b"y\r\n")
    assert first["sha256"] != second["sha256"]


@pytest.mark.parametrize("reliable", [True, False])
def test_ie_S7_executable_mode_recorded_or_unconfirmed(fx, monkeypatch, reliable):
    monkeypatch.setattr(ie, "_exec_reliable", lambda root: reliable)
    (fx.repo / "tracked.txt").write_bytes(b"two\n")
    snap = fx.load(fx.complete(), "snapshot.json")
    assert snap["executable_mode_reliable"] is reliable
    for entry in snap["protected_scope"]:
        if reliable:
            assert isinstance(entry["executable"], bool)
        else:
            assert entry["executable"] == "未確認"


def test_ie_S7_platform_reliability(fx):
    got = ie._exec_reliable(str(fx.repo))
    if os.name != "posix":
        assert got is False
    else:
        value = git(fx.repo, "config", "--get", "core.filemode", check=False).stdout.decode().strip()
        assert got is (value.lower() != "false")


def test_ie_S8_untracked_listed_without_content(fx):
    (fx.repo / "u.txt").write_bytes(b"secret-content-u\n")
    snap = fx.load(fx.complete(), "snapshot.json")
    assert snap["untracked"] == {"count": 1, "paths": ["u.txt"], "content_verified": False,
                                 "note": "未驗證其內容是否改變"}
    assert sha(b"secret-content-u\n") not in json.dumps(snap)
    assert all(e["path"] != "u.txt" for e in snap["protected_scope"])


def test_ie_S9_evidence_dir_excluded_from_work_comparison(fx):
    first = fx.complete()
    second = fx.complete()
    snap = fx.load(second, "snapshot.json")
    assert not any(p.startswith(".dev/") for p in snap["untracked"]["paths"])
    assert not any(e["path"].startswith(".dev/") for e in snap["protected_scope"])
    code, out, err = fx.resume(first)
    assert code == ie.EXIT_OK, err
    assert ie._is_evidence_path(".dev/inventory-evidence/x/y")
    assert ie._is_evidence_path(".dev/inventory-evidence")
    assert not ie._is_evidence_path(".dev/inventory-evidence-other")


# ── C 區:差異分類 ─────────────────────────────────────────────────────────────

def test_ie_C1_classification_categories():
    entries = [
        {"path": "p/1", "sha256": "1" * 64, "note": "n"},
        {"path": "p/2", "sha256": "2" * 64, "note": "n"},
        {"path": "p/3", "sha256": "3" * 64, "note": "n"},
        {"path": "p/4", "contract": {"name": "c4", "pins": {}}, "note": "n"},
        {"path": "p/5", "contract": {"name": "c5", "pins": {}}, "note": "n"},
        {"path": "p/6", "contract": {"name": "c6", "pins": {}}, "note": "n"},
    ]
    synced = [("p/1", "1" * 64), ("p/2", "9" * 64), ("p/4", "4" * 64), ("p/5", "5" * 64), ("p/7", "7" * 64)]
    bad = {"category": "contract_format", "field": "size"}
    missing = {"category": "contract_read", "field": "missing"}
    seen = []

    def resolve(path, contract):
        seen.append(path)
        return True, (bad if path == "p/5" else None)
    got = ie.classify(entries, synced, resolve)
    assert got["differences"] == [
        {"category": "mismatch", "path": "p/2", "inventory_value": "2" * 64, "live_value": "9" * 64},
        {"category": "deleted", "path": "p/3", "inventory_value": "3" * 64, "live_value": None},
        {"category": "contract", "path": "p/5", "inventory_value": {"name": "c5", "pins": {}}, "live_value": bad},
        {"category": "contract", "path": "p/6", "inventory_value": {"name": "c6", "pins": {}},
         "live_value": missing},
        {"category": "added", "path": "p/7", "inventory_value": None, "live_value": "7" * 64},
    ]
    assert got["contracts"] == [
        {"path": "p/4", "name": "c4", "present": True, "result": None},
        {"path": "p/5", "name": "c5", "present": True, "result": bad},
        {"path": "p/6", "name": "c6", "present": False, "result": missing},
    ]
    assert got["counts"] == {"extra": 1, "missing": 2, "mismatch": 2}
    assert got["unclassified"] == []
    assert seen == ["p/4", "p/5"]


def test_ie_C1_unreadable_live_value_is_unclassified():
    got = ie.classify([{"path": "p/1", "sha256": "1" * 64, "note": "n"}],
                      [("p/1", None), ("p/2", None)], lambda path, contract: (True, None))
    assert [u["path"] for u in got["unclassified"]] == ["p/1", "p/2"]
    assert got["differences"] == []
    assert got["counts"] == {"extra": 1, "missing": 0, "mismatch": 1}


def test_ie_C2_unstable_samples_stop_without_candidate(fx, monkeypatch):
    monkeypatch.setattr(ie, "_sleep", lambda seconds: (fx.bucket / "a.txt").write_bytes(b"drifted\n"))
    code, out, err = fx.collect()
    assert code == ie.EXIT_MISMATCH
    assert "stable" in err
    [run] = fx.runs()
    assert sorted(os.listdir(str(fx.evid / run))) == ["checkpoint.jsonl", "snapshot.json"]
    last = fx.events(run)[-1]
    assert (last["step"], last["result"]) == ("S1", "stopped")
    assert [r["event"] for r in fx.index()] == ["start", "stopped"]


# ── I 區:真實 R10 介面 ────────────────────────────────────────────────────────

def _no_expanduser(monkeypatch):
    calls = []
    monkeypatch.setattr(os.path, "expanduser", lambda p: calls.append(p) or p)
    return calls


def test_ie_I1_real_r10_itemized_classification(fx, monkeypatch):
    calls = _no_expanduser(monkeypatch)
    drift_live(fx)
    s = ie.sample(str(fx.repo), str(fx.claude))
    cls = s["classification"]
    assert cls["differences"] == [
        {"category": "mismatch", "path": logical("a.txt"), "inventory_value": sha(b"alpha\n"),
         "live_value": sha(b"alpha2\n")},
        {"category": "deleted", "path": logical("b.txt"), "inventory_value": sha(b"beta\n"), "live_value": None},
        {"category": "added", "path": logical("c.txt"), "inventory_value": None, "live_value": sha(b"gamma\n")},
    ]
    assert cls["contracts"] == [{"path": logical(".last-complete-round"), "name": "synced-last-round-v1",
                                 "present": True, "result": None}]
    assert cls["unclassified"] == []
    assert cls["counts"] == {"extra": 1, "missing": 1, "mismatch": 1}
    synced = s["synced"]
    assert (synced["extra"], synced["missing"], synced["mismatch"], synced["structure_errors"]) == (1, 1, 1, 0)
    ie.cross_check(cls["counts"], synced, s["structure_errors"])
    assert sorted(item["path"] for item in s["live"]) == sorted([
        "plugins/.bucket-%s" % TOKEN, logical(".last-complete-round"), logical("a.txt"), logical("c.txt")])
    assert BUCKET not in json.dumps(s["live"])
    assert calls == []


def test_ie_I1_real_contract_failure_classified(fx, monkeypatch):
    calls = _no_expanduser(monkeypatch)
    (fx.bucket / ".last-complete-round").write_bytes(b"bad")
    s = ie.sample(str(fx.repo), str(fx.claude))
    code = {"category": "contract_format", "field": "size"}
    assert s["classification"]["differences"] == [
        {"category": "contract", "path": logical(".last-complete-round"),
         "inventory_value": {"name": "synced-last-round-v1", "pins": {}}, "live_value": code}]
    assert s["classification"]["counts"] == {"extra": 0, "missing": 0, "mismatch": 1}
    assert s["synced"]["mismatch"] == 1
    assert calls == []


def test_ie_I2_cross_check_unit():
    ie.cross_check({"extra": 1, "missing": 0, "mismatch": 0},
                   {"extra": 1, "missing": 0, "mismatch": 0, "structure_errors": 0}, 0)
    with pytest.raises(ie.Stop) as e:
        ie.cross_check({"extra": 1, "missing": 0, "mismatch": 0},
                       {"extra": 0, "missing": 0, "mismatch": 0, "structure_errors": 0}, 0)
    assert e.value.code == ie.EXIT_MISMATCH


def test_ie_I2_cross_check_mismatch_stops_collect(fx, monkeypatch):
    real = ie._extension_report

    def skewed(root, claude_root):
        report = real(root, claude_root)
        report["synced"] = dict(report["synced"], missing=report["synced"]["missing"] + 1)
        return report
    monkeypatch.setattr(ie, "_extension_report", skewed)
    code, out, err = fx.collect()
    assert code == ie.EXIT_MISMATCH
    assert "交叉核對" in err
    [run] = fx.runs()
    assert sorted(os.listdir(str(fx.evid / run))) == ["checkpoint.jsonl", "snapshot.json"]


def test_ie_I3_collect_never_reads_real_user_layer(fx, monkeypatch):
    calls = _no_expanduser(monkeypatch)
    drift_live(fx)
    code, out, err = fx.collect()
    assert code == ie.EXIT_OK, err
    assert calls == []


# ── D 區:候選名冊 ─────────────────────────────────────────────────────────────

def test_ie_D1_candidate_only_changes_differences(fx):
    drift_live(fx)
    run = fx.complete()
    cand = fx.load(run, "candidate-inventory.json")
    base = inventory_doc(FILES)
    note = "inventory-evidence " + run
    assert (cand["schema"], cand["version"]) == (base["schema"], base["version"])
    assert cand["entries"] == [
        base["entries"][0],
        {"path": logical("a.txt"), "sha256": sha(b"alpha2\n"), "note": note},
        base["entries"][3],
        {"path": logical("c.txt"), "sha256": sha(b"gamma\n"), "note": note},
    ]


def test_ie_D2_agents_not_written(fx):
    before = tree_bytes(fx.repo / ".agents")
    drift_live(fx)
    fx.complete()
    assert tree_bytes(fx.repo / ".agents") == before


def test_ie_D3_candidate_blob_recorded_without_writing(fx):
    drift_live(fx)
    run = fx.complete()
    path = fx.evid / run / "candidate-inventory.json"
    data = path.read_bytes()
    [s2] = [e for e in fx.events(run) if e["step"] == "S2"]
    expected = git_out(fx.repo, "hash-object", "--no-filters", str(path))
    assert s2["fingerprints"]["candidate-inventory.json"] == sha(data)
    assert s2["fingerprints"]["candidate_blob"] == expected
    assert fx.load(run, "package.json")["candidate"] == {"blob": expected, "sha256": sha(data)}


# ── E 區:證據包 ───────────────────────────────────────────────────────────────

def _s3(fx, run):
    [s3] = [e for e in fx.events(run) if e["step"] == "S3" and e["result"] == "completed"]
    return s3


def test_ie_E1_same_input_same_fingerprint(fx):
    run = fx.complete()
    pkg = fx.load(run, "package.json")
    fp = ie.package_fingerprint(pkg)
    shuffled = json.loads(json.dumps(dict(reversed(list(pkg.items())))))
    assert ie.package_fingerprint(shuffled) == fp
    assert re.fullmatch(r"[0-9a-f]{64}", fp)
    assert _s3(fx, run)["fingerprints"]["package_fingerprint"] == fp


def test_ie_E2_fingerprint_binds_exactly_three_artifacts(fx):
    run = fx.complete()
    pkg = fx.load(run, "package.json")
    fp = ie.package_fingerprint(pkg)
    assert sorted(pkg["artifacts"]) == ["candidate-inventory.json", "diff.json", "snapshot.json"]
    for name in sorted(pkg["artifacts"]):
        assert pkg["artifacts"][name] == sha((fx.evid / run / name).read_bytes())
        changed = json.loads(json.dumps(pkg))
        changed["artifacts"][name] = "0" * 64
        assert ie.package_fingerprint(changed) != fp
    assert "summary.md" not in json.dumps(pkg)


def test_ie_E3_summary_change_does_not_affect_fingerprint(fx):
    run = fx.complete()
    [done] = [r for r in fx.index() if r["event"] == "collect_completed"]
    (fx.evid / run / "summary.md").write_bytes(b"changed\n")
    assert ie.package_fingerprint(fx.load(run, "package.json")) == done["package_fingerprint"]


def test_ie_E4_s3_event_records_summary_sha(fx):
    run = fx.complete()
    s3 = _s3(fx, run)
    assert s3["fingerprints"]["summary.md"] == sha((fx.evid / run / "summary.md").read_bytes())
    assert s3["fingerprints"]["package.json"] == sha((fx.evid / run / "package.json").read_bytes())


def test_ie_E5_summary_has_no_sensitive_values(fx):
    drift_live(fx)
    run = fx.complete()
    text = (fx.evid / run / "summary.md").read_bytes().decode("utf-8")
    fp = ie.package_fingerprint(fx.load(run, "package.json"))
    assert fp in text
    assert "未追蹤檔內容未驗證" in text
    for bad in (FAKE_ORIGIN, ie.ROOT_COMMIT, git_out(fx.repo, "rev-parse", "HEAD"), BUCKET,
                str(fx.tmp), str(fx.repo), "t@example.invalid", logical("a.txt")):
        assert bad not in text
    assert set(re.findall(r"[0-9a-f]{40,}", text)) == {fp}


def test_ie_E6_collect_prints_full_fingerprint(fx):
    code, out, err = fx.collect()
    assert code == ie.EXIT_OK, err
    [run] = fx.runs()
    fp = ie.package_fingerprint(fx.load(run, "package.json"))
    assert re.findall(r"[0-9a-f]{64}", out) == [fp]


# ── R 區:repo 識別 ─────────────────────────────────────────────────────────────

def test_ie_R1_root_commit_mismatch_stops(fx, monkeypatch):
    monkeypatch.setattr(ie, "ROOT_COMMIT", "f" * 40)
    code, out, err = fx.collect()
    assert code == ie.EXIT_UNSUPPORTED
    assert not (fx.repo / ".dev").exists()


def test_ie_R1_resume_identity_mismatch_stops(fx, monkeypatch):
    run = fx.complete()
    monkeypatch.setattr(ie, "ROOT_COMMIT", "f" * 40)
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_UNSUPPORTED


def test_ie_R2_origin_mismatch_stops(fx, monkeypatch):
    monkeypatch.setattr(ie, "ORIGIN_URL", "example.invalid/other.git")
    code, out, err = fx.collect()
    assert code == ie.EXIT_UNSUPPORTED
    assert not (fx.repo / ".dev").exists()


def test_ie_R2_origin_missing_stops(fx):
    git(fx.repo, "remote", "remove", "origin")
    code, out, err = fx.collect()
    assert code == ie.EXIT_UNSUPPORTED
    assert not (fx.repo / ".dev").exists()


# ── K 區:resume 中斷點 ────────────────────────────────────────────────────────

def test_ie_K1_resume_complete_prints_fingerprint(fx):
    run = fx.complete()
    [done] = [r for r in fx.index() if r["event"] == "collect_completed"]
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_OK, err
    assert done["package_fingerprint"] in out


def test_ie_K2_resume_after_s0b_prints_next_step(fx, monkeypatch):
    monkeypatch.setattr(ie, "_sleep", lambda seconds: (fx.bucket / "a.txt").write_bytes(b"drifted\n"))
    code, out, err = fx.collect()
    assert code == ie.EXIT_MISMATCH
    [run] = fx.runs()
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_OK, err
    assert "下一步" in out and "S1" in out


@pytest.mark.parametrize("func,expected", [("step_s2", "S2"), ("step_s3", "S3")])
def test_ie_K3_resume_after_interrupted_step_prints_next_step(fx, monkeypatch, func, expected):
    def boom(ctx):
        raise ie.Stop(ie.EXIT_INTERNAL, "test interruption")
    monkeypatch.setattr(ie, func, boom)
    code, out, err = fx.collect()
    assert code == ie.EXIT_INTERNAL
    [run] = fx.runs()
    last = fx.events(run)[-1]
    assert (last["step"], last["result"]) == (expected, "stopped")
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_OK, err
    assert "下一步" in out and expected in out


@pytest.mark.parametrize("change", ["worktree", "staged", "head"])
def test_ie_K4_resume_state_changed_requires_recollect(fx, change):
    run = fx.complete()
    if change == "worktree":
        (fx.repo / "tracked.txt").write_bytes(b"changed\n")
    elif change == "staged":
        (fx.repo / "new.txt").write_bytes(b"n\n")
        git(fx.repo, "add", "--", "new.txt")
    else:
        (fx.repo / "tracked.txt").write_bytes(b"changed\n")
        fx.commit_all()
    before = tree_bytes(fx.evid)
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_MISMATCH
    assert "重新 collect" in err
    assert tree_bytes(fx.evid) == before


# ── V 區:resume 證據重驗 ──────────────────────────────────────────────────────

def _tamper(fx, run, kind):
    rd = fx.evid / run
    cp = rd / "checkpoint.jsonl"
    if kind == "artifact_modified":
        (rd / "diff.json").write_bytes((rd / "diff.json").read_bytes() + b" ")
    elif kind == "summary_modified":
        (rd / "summary.md").write_bytes((rd / "summary.md").read_bytes() + b"x")
    elif kind == "package_modified":
        pkg = fx.load(run, "package.json")
        pkg["created_at"] = "2000-01-01T00:00:00Z"
        (rd / "package.json").write_bytes(line_of(pkg))
    elif kind == "package_artifact_sha_mismatch":
        pkg = fx.load(run, "package.json")
        pkg["artifacts"]["snapshot.json"] = "0" * 64
        (rd / "package.json").write_bytes(line_of(pkg))
    elif kind == "index_fingerprint_mismatch":
        recs = fx.index()
        for r in recs:
            if r["event"] == "collect_completed":
                r["package_fingerprint"] = "1" * 64
        write_lines(fx.evid / "index.jsonl", [line_of(r) for r in recs])
    elif kind == "missing_event":
        write_lines(cp, [line for line in read_lines(cp) if json.loads(line)["step"] != "S1"])
    elif kind == "duplicate_event":
        lines = read_lines(cp)
        write_lines(cp, lines[:2] + [lines[1]] + lines[2:])
    elif kind == "reversed_events":
        lines = read_lines(cp)
        write_lines(cp, [lines[1], lines[0]] + lines[2:])
    elif kind == "run_id_mismatch":
        recs = fx.events(run)
        recs[2]["run_id"] = "20000101T000000Z-0000000"
        write_lines(cp, [line_of(r) for r in recs])
    elif kind == "artifact_missing":
        (rd / "candidate-inventory.json").unlink()
    else:
        raise AssertionError(kind)


@pytest.mark.parametrize("kind", [
    "artifact_modified", "summary_modified", "package_modified", "package_artifact_sha_mismatch",
    "index_fingerprint_mismatch", "missing_event", "duplicate_event", "reversed_events",
    "run_id_mismatch", "artifact_missing"])
def test_ie_V1_resume_stops_on_tampered_evidence_without_touching_it(fx, kind):
    run = fx.complete()
    _tamper(fx, run, kind)
    before = tree_bytes(fx.evid)
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_MISMATCH, (kind, err)
    assert tree_bytes(fx.evid) == before


# ── L 區:鎖與並行 ─────────────────────────────────────────────────────────────

CHILD = r'''
import importlib.util, json, os, sys, time
from datetime import datetime
cfg = json.load(open(sys.argv[1], encoding="utf-8"))
spec = importlib.util.spec_from_file_location("ie_child", cfg["module"])
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.ROOT_COMMIT = cfg["root_commit"]
m.ORIGIN_URL = cfg["origin"]
fixed = datetime.fromisoformat(cfg["now"])
m._now = lambda: fixed
hold = cfg.get("hold")
if hold:
    def _hold(seconds):
        open(os.path.join(hold, "holding"), "w").close()
        deadline = time.time() + 120
        while not os.path.exists(os.path.join(hold, "release")):
            if time.time() > deadline:
                raise SystemExit(9)
            time.sleep(0.05)
    m._sleep = _hold
sys.exit(m.main(cfg["argv"]))
'''


def _child_cmd(fx, name, now, hold=None):
    cfg = {"module": str(MODULE_PATH), "root_commit": ie.ROOT_COMMIT, "origin": ie.ORIGIN_URL, "now": now,
           "hold": hold, "argv": ["collect", "--repo", str(fx.repo), "--claude-root", str(fx.claude),
                                  "--settle-seconds", "0"]}
    cfg_path = fx.tmp / (name + ".json")
    cfg_path.write_bytes(json.dumps(cfg).encode("utf-8"))
    script = fx.tmp / "child.py"
    if not script.exists():
        script.write_bytes(CHILD.encode("utf-8"))
    return [sys.executable, str(script), str(cfg_path)]


@pytest.mark.parametrize("same_run_id", [True, False])
def test_ie_L1_second_process_cannot_take_lock(fx, same_run_id):
    hold = fx.tmp / "hold"
    hold.mkdir()
    t1 = "2026-10-29T01:00:00+00:00"
    t2 = t1 if same_run_id else "2026-10-29T02:00:00+00:00"
    head7 = git_out(fx.repo, "rev-parse", "HEAD")[:7]
    first_run = "20261029T010000Z-" + head7
    first = subprocess.Popen(_child_cmd(fx, "first", t1, str(hold)),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        deadline = time.time() + 120
        while not (hold / "holding").exists():
            assert first.poll() is None, first.communicate()
            assert time.time() < deadline
            time.sleep(0.05)
        second = subprocess.run(_child_cmd(fx, "second", t2), capture_output=True, timeout=120)
        second_err = second.stderr.decode("utf-8", "replace")
        assert second.returncode == ie.EXIT_MISMATCH, second_err
        assert "鎖" in second_err
        recs = fx.index()
        assert [(r["event"], r["run_id"]) for r in recs] == [("start", first_run)]
        assert json.loads((fx.evid / ".lock").read_bytes().decode("utf-8"))["run_id"] == first_run
    finally:
        (hold / "release").write_bytes(b"")
        out, err = first.communicate(timeout=120)
    assert first.returncode == ie.EXIT_OK, err.decode("utf-8", "replace")
    assert [(r["event"], r["run_id"]) for r in fx.index()] == [("start", first_run),
                                                               ("collect_completed", first_run)]
    assert not (fx.evid / ".lock").exists()
    assert fx.runs() == [first_run]


def test_ie_L3_leftover_lock_not_removed_not_continued(fx):
    run = fx.complete()
    (fx.evid / ".lock").write_bytes(b'{"pid": 1, "run_id": "someone-else"}\n')
    before = tree_bytes(fx.evid)
    code, out, err = fx.collect()
    assert code == ie.EXIT_MISMATCH
    assert "鎖" in err
    assert tree_bytes(fx.evid) == before
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_MISMATCH
    assert "鎖" in err
    assert tree_bytes(fx.evid) == before


def test_ie_L4_normal_end_removes_only_own_lock(fx):
    fx.complete()
    assert not (fx.evid / ".lock").exists()
    p = fx.tmp / "lockfile"
    p.write_bytes(b"other")
    assert ie._release_lock(str(p), b"mine") is False
    assert p.read_bytes() == b"other"
    p.write_bytes(b"mine")
    assert ie._release_lock(str(p), b"mine") is True
    assert not p.exists()


# ── J 區:中斷 ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("kind", ["tmp_file", "artifact_without_event", "package_without_s3", "truncated_jsonl"])
def test_ie_J1_interrupted_data_refused_by_collect_and_resume(fx, kind):
    run = fx.complete()
    rd = fx.evid / run
    if kind == "tmp_file":
        (rd / ".tmp-diff.json").write_bytes(b"{")
    elif kind == "artifact_without_event":
        other = fx.evid / "20261029T235959Z-0000000"
        other.mkdir()
        (other / "snapshot.json").write_bytes(b"{}\n")
    elif kind == "package_without_s3":
        lines = read_lines(rd / "checkpoint.jsonl")
        assert json.loads(lines[-1])["step"] == "S3"
        write_lines(rd / "checkpoint.jsonl", lines[:-1])
    else:
        with open(str(fx.evid / "index.jsonl"), "ab") as fh:
            fh.write(b'{"event": "start"')
    before = tree_bytes(fx.evid)
    code, out, err = fx.collect()
    assert code == ie.EXIT_MISMATCH, err
    assert tree_bytes(fx.evid) == before
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_MISMATCH, err
    assert tree_bytes(fx.evid) == before


# ── M 區:結構 ────────────────────────────────────────────────────────────────

READ_ONLY_GIT = {"rev-parse", "rev-list", "remote", "diff", "ls-files", "check-ignore", "config",
                 "hash-object", "cat-file"}
FORBIDDEN_GIT = ("add", "commit", "reset", "update-index", "checkout", "stash", "restore", "rm", "mv")


def _git_subcommand(argv):
    i = 1
    while i < len(argv):
        if argv[i] in ("-C", "-c"):
            i += 2
            continue
        if argv[i].startswith("-"):
            i += 1
            continue
        return argv[i], argv[i + 1:]
    return None, []


def test_ie_M1_only_read_only_git_subcommands(fx, monkeypatch):
    calls = []
    real = subprocess.run

    def recorder(*args, **kwargs):
        calls.append([str(a) for a in (args[0] if args else kwargs["args"])])
        return real(*args, **kwargs)
    monkeypatch.setattr(subprocess, "run", recorder)
    drift_live(fx)
    run = fx.complete()
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_OK, err
    gits = [c for c in calls if os.path.basename(c[0]).lower().startswith("git")]
    assert gits and len(gits) == len(calls)
    for argv in gits:
        sub, rest = _git_subcommand(argv)
        assert sub in READ_ONLY_GIT and sub not in FORBIDDEN_GIT, argv
        if sub == "hash-object":
            assert "-w" not in rest, argv
        if sub == "remote":
            assert rest[:1] == ["get-url"], argv
        if sub == "config":
            assert "--get" in rest, argv


@pytest.mark.parametrize("args", [[sub] for sub in FORBIDDEN_GIT]
                         + [["hash-object", "-w", "x"], ["remote", "add", "x", "y"], ["config", "core.x", "y"]])
def test_ie_M2_guard_refuses_write_subcommands(fx, args):
    with pytest.raises(ie.Stop) as e:
        ie._git(str(fx.repo), args)
    assert e.value.code == ie.EXIT_INTERNAL


def test_ie_M3_publish_never_overwrites(tmp_path):
    final = tmp_path / "snapshot.json"
    final.write_bytes(b"original")
    tmp = tmp_path / ".tmp-snapshot.json"
    tmp.write_bytes(b"new")
    with pytest.raises(ie.Stop) as e:
        ie._publish(str(tmp), str(final))
    assert e.value.code == ie.EXIT_MISMATCH
    assert final.read_bytes() == b"original"


def test_ie_M4_writes_only_inside_evidence_dir(fx):
    drift_live(fx)
    repo_before = tree_bytes(fx.repo)
    claude_before = tree_bytes(fx.claude)
    index_before = (fx.repo / ".git" / "index").read_bytes()
    refs_before = (git_out(fx.repo, "rev-parse", "HEAD"), git_out(fx.repo, "for-each-ref"))
    run = fx.complete()
    assert fx.resume(run)[0] == ie.EXIT_OK
    repo_after = tree_bytes(fx.repo)
    for key, value in repo_before.items():
        assert repo_after.get(key) == value, key
    assert all(k.startswith(".dev/inventory-evidence/") for k in set(repo_after) - set(repo_before))
    assert tree_bytes(fx.claude) == claude_before
    assert (fx.repo / ".git" / "index").read_bytes() == index_before
    assert (git_out(fx.repo, "rev-parse", "HEAD"), git_out(fx.repo, "for-each-ref")) == refs_before


# ── N 區:contract 失敗或無法分類 ──────────────────────────────────────────────

def test_ie_N1_contract_failure_stops_without_package(fx):
    (fx.bucket / ".last-complete-round").write_bytes(b"bad")
    code, out, err = fx.collect()
    assert code == ie.EXIT_MISMATCH
    assert "contract" in err
    [run] = fx.runs()
    assert sorted(os.listdir(str(fx.evid / run))) == ["checkpoint.jsonl", "snapshot.json"]


def test_ie_N2_unclassified_stops_without_package(fx):
    (fx.claude / "plugins" / "synced" / "second-bucket").mkdir()
    code, out, err = fx.collect()
    assert code == ie.EXIT_MISMATCH
    assert "無法分類" in err
    [run] = fx.runs()
    assert sorted(os.listdir(str(fx.evid / run))) == ["checkpoint.jsonl", "snapshot.json"]
