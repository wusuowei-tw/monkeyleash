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


# ══ 站二:核准代記、登記前重驗、登記前後核對、完整 resume ═══════════════════════
#
# 「登記」與「接回」是 VS 依現有程序做的動作,工具不做;這裡在假 repo 裡用 git 模擬它們,
# 工具只負責前後核對。

APPROVED_AT = "2026-10-29T12:00:00-04:00"
STATEMENT = "代理人代記 Jeff 對此證據包指紋的明確核准；不是獨立人類授權證明"


def run_cmd(fx, sub, *rest, claude=False):
    argv = [sub, "--repo", str(fx.repo)] + list(rest)
    if claude:
        argv += ["--claude-root", str(fx.claude)]
    code = ie.main(argv)
    cap = fx.capsys.readouterr()
    return code, cap.out, cap.err


def fingerprint_of(fx, run):
    return ie.package_fingerprint(fx.load(run, "package.json"))


def approve(fx, run, fp=None, approved_at=APPROVED_AT):
    return run_cmd(fx, "record-approval", "--run", run, "--fingerprint", fp if fp is not None else fingerprint_of(fx, run),
                   "--approved-at", approved_at, "--note", "test approval")


def pre_register(fx, run):
    return run_cmd(fx, "pre-register", "--run", run, claude=True)


def post_register(fx, run):
    return run_cmd(fx, "post-register", "--run", run, claude=True)


def post_reattach(fx, run):
    return run_cmd(fx, "post-reattach", "--run", run)


def setup_partial(fx):
    p = fx.repo / "tracked.txt"
    p.write_bytes(b"two\n")
    git(fx.repo, "add", "--", "tracked.txt")
    p.write_bytes(b"three\n")


def setup_work(fx):
    """原工作:部分暫存(tracked.txt)、暫存新增(new.txt)、暫存刪除(gone.txt)。"""
    (fx.repo / "gone.txt").write_bytes(b"gone\n")
    fx.commit_all("gone")
    setup_partial(fx)
    (fx.repo / "new.txt").write_bytes(b"n\n")
    git(fx.repo, "add", "--", "new.txt")
    git(fx.repo, "rm", "-q", "--", "gone.txt")


def to_s5(fx):
    setup_work(fx)
    drift_live(fx)
    run = fx.complete()
    code, out, err = approve(fx, run)
    assert code == ie.EXIT_OK, err
    code, out, err = pre_register(fx, run)
    assert code == ie.EXIT_OK, err
    return run


def register(fx, run, extra=None, content=None):
    """模擬 VS 的登記:退出暫存,以候選名冊做一個只改名冊的 commit。"""
    git(fx.repo, "reset", "-q")
    data = content if content is not None else (fx.evid / run / "candidate-inventory.json").read_bytes()
    (fx.repo / INVENTORY_REL).write_bytes(data)
    git(fx.repo, "add", "--", INVENTORY_REL)
    if extra:
        extra()
    git(fx.repo, "commit", "-q", "-m", "register")


def reattach(fx, run, skip=()):
    """模擬 VS 的接回:把快照的待提交區端放回去。"""
    for s in fx.load(run, "snapshot.json")["staged"]:
        if s["path"] == INVENTORY_REL or s["path"] in skip:
            continue
        if s["index"]["exists"]:
            git(fx.repo, "update-index", "--add", "--cacheinfo",
                "%s,%s,%s" % (s["index"]["mode"], s["index"]["blob"], s["path"]))
        else:
            git(fx.repo, "rm", "-q", "--cached", "--", s["path"])


def to_s6(fx):
    run = to_s5(fx)
    register(fx, run)
    code, out, err = post_register(fx, run)
    assert code == ie.EXIT_OK, err
    return run


def to_s8(fx):
    run = to_s6(fx)
    reattach(fx, run)
    code, out, err = post_reattach(fx, run)
    assert code == ie.EXIT_OK, err
    return run


def steps_of(fx, run, result="completed"):
    return [e["step"] for e in fx.events(run) if e["result"] == result]


def frozen(fx):
    """repo(含證據目錄)、.git/index 與 HEAD 的完整狀態。"""
    return (tree_bytes(fx.repo), (fx.repo / ".git" / "index").read_bytes(), git_out(fx.repo, "rev-parse", "HEAD"))


def swap_steps(fx, run, a, b):
    cp = fx.evid / run / "checkpoint.jsonl"
    lines = read_lines(cp)
    ia = [i for i, line in enumerate(lines) if json.loads(line)["step"] == a][0]
    ib = [i for i, line in enumerate(lines) if json.loads(line)["step"] == b][0]
    lines[ia], lines[ib] = lines[ib], lines[ia]
    write_lines(cp, lines)


# ── U 區:網址常數 ─────────────────────────────────────────────────────────────

def test_ie_U1_origin_constant_is_single_full_literal():
    import urllib.parse
    parts = urllib.parse.urlsplit(ie.ORIGIN_URL)
    assert (parts.scheme, parts.netloc) == ("https", "github.com")
    assert len([seg for seg in parts.path.split("/") if seg]) == 2
    assert not parts.query and not parts.fragment
    lines = MODULE_PATH.read_bytes().decode("utf-8").splitlines()
    assert ('ORIGIN_URL = "%s"' % ie.ORIGIN_URL) in lines


def test_ie_U2_split_constants_removed():
    assert not hasattr(ie, "ORIGIN_SCHEME") and not hasattr(ie, "ORIGIN_LOCATION")
    src = MODULE_PATH.read_bytes().decode("utf-8")
    assert "ORIGIN_SCHEME" not in src and "ORIGIN_LOCATION" not in src


# ── B 區補:名冊或 allowlist 在待提交區有變更 ─────────────────────────────────

@pytest.mark.parametrize("rel", [INVENTORY_REL, ALLOWLIST_REL])
def test_ie_B3_policy_staged_change_refused(fx, rel):
    p = fx.repo / rel
    p.write_bytes(p.read_bytes() + b"\n")
    git(fx.repo, "add", "--", rel)
    code, out, err = fx.collect()
    assert code == ie.EXIT_UNSUPPORTED
    assert "待提交區" in err
    assert not (fx.repo / ".dev").exists()


# ── P 區:核准代記 ─────────────────────────────────────────────────────────────

def test_ie_P1_record_approval_writes_full_approval(fx):
    run = fx.complete()
    fp = fingerprint_of(fx, run)
    code, out, err = approve(fx, run)
    assert code == ie.EXIT_OK, err
    raw = (fx.evid / run / "approval.json").read_bytes()
    doc = json.loads(raw.decode("utf-8"))
    assert sorted(doc) == sorted(["format_version", "run_id", "package_fingerprint", "approved_at",
                                  "recorded_at", "recorded_by", "statement", "note"])
    assert (doc["run_id"], doc["package_fingerprint"], doc["approved_at"]) == (run, fp, APPROVED_AT)
    assert (doc["recorded_by"], doc["statement"], doc["note"]) == ("agent-proxy", STATEMENT, "test approval")
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", doc["recorded_at"])
    [s4] = [e for e in fx.events(run) if e["step"] == "S4"]
    assert s4["result"] == "completed"
    assert s4["fingerprints"] == {"package_fingerprint": fp, "approval.json": sha(raw)}
    last = fx.index()[-1]
    assert (last["event"], last["package_fingerprint"]) == ("approval_recorded", fp)
    assert not (fx.evid / ".lock").exists()


def assert_one_stop_recorded(fx, run, before):
    """修正站裁定 A1:停下後原件與 approval.json 位元組不變;checkpoint.jsonl 與 index.jsonl 各新增恰好一筆
    stopped(執行代號、步驟、事件種類、reason 相同,先 checkpoint 後 index);證據目錄沒有其他新增或改動。"""
    after = tree_bytes(fx.evid)
    cp_key = run + "/checkpoint.jsonl"
    assert sorted(after) == sorted(before)
    for key in before:
        if key not in (cp_key, "index.jsonl"):
            assert after[key] == before[key], key
    new = []
    for key in (cp_key, "index.jsonl"):
        assert after[key].startswith(before[key]), key
        added = after[key][len(before[key]):].split(b"\n")
        assert len(added) == 2 and added[1] == b"", key
        new.append(json.loads(added[0].decode("utf-8")))
    cp, ix = new
    assert cp["result"] == "stopped" and cp["run_id"] == run
    assert (cp["run_id"], cp["step"], cp["result"], cp["reason"]) == (ix["run_id"], ix["step"], ix["event"], ix["reason"])
    assert cp["time"] < ix["time"]


@pytest.mark.parametrize("variant", ["short", "upper", "space", "other"])
def test_ie_P2_fingerprint_must_match_exactly(fx, variant):
    run = fx.complete()
    fp = fingerprint_of(fx, run)
    given = {"short": fp[:12], "upper": fp.upper(), "space": " " + fp + " ", "other": "0" * 64}[variant]
    before = tree_bytes(fx.evid)
    code, out, err = approve(fx, run, given)
    assert code == ie.EXIT_MISMATCH
    assert_one_stop_recorded(fx, run, before)


def test_ie_P3_requires_completed_s3(fx, monkeypatch):
    monkeypatch.setattr(ie, "_sleep", lambda seconds: (fx.bucket / "a.txt").write_bytes(b"drifted\n"))
    assert fx.collect()[0] == ie.EXIT_MISMATCH
    [run] = fx.runs()
    before = tree_bytes(fx.evid)
    code, out, err = approve(fx, run, "0" * 64)
    assert code == ie.EXIT_MISMATCH
    assert_one_stop_recorded(fx, run, before)


def test_ie_P4_second_approval_refused_and_original_kept(fx):
    run = fx.complete()
    assert approve(fx, run)[0] == ie.EXIT_OK
    before = tree_bytes(fx.evid)
    code, out, err = approve(fx, run)
    assert code == ie.EXIT_MISMATCH
    assert_one_stop_recorded(fx, run, before)


def test_ie_P5_approved_at_requires_timezone(fx):
    run = fx.complete()
    before = tree_bytes(fx.evid)
    code, out, err = approve(fx, run, approved_at="2026-10-29T12:00:00")
    assert code == ie.EXIT_PRECONDITION
    assert "時區" in err
    assert tree_bytes(fx.evid) == before


# ── Q 區:登記前重驗(pre-register,已合併原 verify)───────────────────────────

def test_ie_Q1_pre_register_all_match_passes(fx):
    setup_work(fx)
    run = fx.complete()
    assert approve(fx, run)[0] == ie.EXIT_OK
    approval = (fx.evid / run / "approval.json").read_bytes()
    code, out, err = pre_register(fx, run)
    assert code == ie.EXIT_OK, err
    assert "登記" in out
    assert steps_of(fx, run)[-1] == "S5"
    [s5] = [e for e in fx.events(run) if e["step"] == "S5"]
    assert sorted(s5["fingerprints"]) == ["approval.json", "package_fingerprint", "sample_1", "sample_2"]
    assert s5["fingerprints"]["approval.json"] == sha(approval)
    assert len(s5["detail"]["sample_times"]) == 2
    assert (fx.evid / run / "approval.json").read_bytes() == approval


def test_ie_Q2_only_sample_time_differs_passes(fx):
    run = fx.complete()
    saved_times = [s["time"] for s in fx.load(run, "diff.json")["samples"]]
    assert approve(fx, run)[0] == ie.EXIT_OK
    code, out, err = pre_register(fx, run)
    assert code == ie.EXIT_OK, err
    [s5] = [e for e in fx.events(run) if e["step"] == "S5"]
    assert not set(s5["detail"]["sample_times"]) & set(saved_times)


def test_ie_Q3_resample_respects_settle_seconds(fx, monkeypatch):
    sleeps = []
    monkeypatch.setattr(ie, "_sleep", lambda seconds: sleeps.append(seconds))
    code, out, err = fx.collect("--settle-seconds", "7")
    assert code == ie.EXIT_OK, err
    run = fx.runs()[-1]
    assert sleeps == [7]
    assert approve(fx, run)[0] == ie.EXIT_OK
    assert pre_register(fx, run)[0] == ie.EXIT_OK
    assert sleeps == [7, 7]


def _q_change(fx, monkeypatch, kind):
    if kind == "head":
        git(fx.repo, "commit", "-q", "-m", "moved")
    elif kind == "staged":
        (fx.repo / "extra.txt").write_bytes(b"e\n")
        git(fx.repo, "add", "--", "extra.txt")
    elif kind == "partial":
        p = fx.repo / "tracked.txt"
        p.write_bytes(b"four\n")
        git(fx.repo, "add", "--", "tracked.txt")
        p.write_bytes(b"three\n")
    elif kind == "worktree":
        (fx.repo / "tracked.txt").write_bytes(b"five\n")
    elif kind in ("inventory_staged", "allowlist_staged"):
        rel = INVENTORY_REL if kind == "inventory_staged" else ALLOWLIST_REL
        p = fx.repo / rel
        p.write_bytes(p.read_bytes() + b"\n")
        git(fx.repo, "add", "--", rel)
    elif kind == "binding":
        (fx.bucket / "a.txt").write_bytes(b"rebound\n")
    elif kind == "candidate":
        real = ie.build_candidate
        monkeypatch.setattr(ie, "build_candidate", lambda inv, diffs, rid: dict(real(inv, diffs, rid), schema="x"))
    else:
        raise AssertionError(kind)


@pytest.mark.parametrize("kind", ["head", "staged", "partial", "worktree", "inventory_staged",
                                  "allowlist_staged", "binding", "candidate"])
def test_ie_Q4_mismatch_voids_approval(fx, monkeypatch, kind):
    setup_partial(fx)
    run = fx.complete()
    assert approve(fx, run)[0] == ie.EXIT_OK
    fp = fingerprint_of(fx, run)
    approval = (fx.evid / run / "approval.json").read_bytes()
    _q_change(fx, monkeypatch, kind)
    code, out, err = pre_register(fx, run)
    assert code == ie.EXIT_MISMATCH, err
    assert "不適用" in err
    assert "S5" not in steps_of(fx, run)
    [void] = [e for e in fx.events(run) if e["result"] == "approval_void"]
    assert void["fingerprints"] == {"package_fingerprint": fp, "approval.json": sha(approval)}
    assert void["detail"]["mismatches"]
    assert (fx.evid / run / "approval.json").read_bytes() == approval
    last = fx.index()[-1]
    assert (last["event"], last["package_fingerprint"]) == ("approval_void", fp)


@pytest.mark.parametrize("kind", ["no_approval", "approval_modified", "evidence_modified", "jsonl_truncated"])
def test_ie_Q5_untrusted_evidence_stops_without_writing(fx, kind):
    run = fx.complete()
    if kind != "no_approval":
        assert approve(fx, run)[0] == ie.EXIT_OK
    rd = fx.evid / run
    if kind == "approval_modified":
        (rd / "approval.json").write_bytes((rd / "approval.json").read_bytes() + b" ")
    elif kind == "evidence_modified":
        (rd / "diff.json").write_bytes((rd / "diff.json").read_bytes() + b" ")
    elif kind == "jsonl_truncated":
        with open(str(rd / "checkpoint.jsonl"), "ab") as fh:
            fh.write(b'{"step": "S5"')
    before = tree_bytes(fx.evid)
    code, out, err = pre_register(fx, run)
    assert code == ie.EXIT_MISMATCH
    if kind == "no_approval":
        assert_one_stop_recorded(fx, run, before)
    else:
        assert tree_bytes(fx.evid) == before


# ══ 修正站一(Y 區):安全追加寫入、失配紀錄前提、鎖釋放(站三 F-1～F-7)═══════════════

WRITERS = ["collect", "record-approval", "pre-register", "post-register", "post-reattach"]
OTHER_LOCK = b'{"pid": 1, "run_id": "someone-else"}\n'
WINDOWS_ONLY = pytest.mark.skipif(
    os.name != "nt", reason="junction 與目錄 handle 釘住只在 Windows 上可用;POSIX 由 dir_fd 題涵蓋(framework-updates/165)")
POSIX_DIRFD = pytest.mark.skipif(
    not (hasattr(os, "O_NOFOLLOW") and hasattr(os, "O_DIRECTORY") and os.open in os.supports_dir_fd),
    reason="平台沒有 dir_fd + O_NOFOLLOW + O_DIRECTORY;Windows 由 junction 與釘住題涵蓋(framework-updates/165)")


def run_any(fx, sub, run):
    if sub == "collect":
        return fx.collect()
    if sub == "resume":
        return fx.resume(run)
    if sub == "record-approval":
        return approve(fx, run, "0" * 64)
    return run_cmd(fx, sub, "--run", run, claude=(sub != "post-reattach"))


def site_of(fx):
    return ie._site(str(fx.repo))


def without_lock(tree):
    return dict((k, v) for k, v in tree.items() if k != ".lock")


def stop_marks(fx, run):
    cp = [e for e in fx.events(run) if e["result"] in ("stopped", "approval_void")]
    ix = [r for r in fx.index() if r["run_id"] == run and r["event"] in ("stopped", "approval_void")]
    return cp, ix


def work_tree(fx):
    return dict((k, v) for k, v in tree_bytes(fx.repo).items() if not k.startswith(".dev/"))


def move_head(fx):
    """只把 HEAD 移到一個新的空 commit;index 與工作區不動。"""
    new = git_out(fx.repo, "commit-tree", "HEAD^{tree}", "-p", "HEAD", "-m", "moved")
    git(fx.repo, "update-ref", "HEAD", new)
    return new


def unstable(fx, monkeypatch):
    monkeypatch.setattr(ie, "_sleep", lambda seconds: (fx.bucket / "a.txt").write_bytes(b"drifted\n"))


def fake_site(tmp, index=b'{"a": 1}\n'):
    """不需要 git 的最小證據目錄:直接測 W1 的開檔函式。"""
    base = tmp / "site"
    evid = base / ".dev" / "inventory-evidence"
    evid.mkdir(parents=True)
    if index is not None:
        (evid / "index.jsonl").write_bytes(index)
    return ie._site(str(base)), evid


def _symlink_file_or_skip(tmp):
    target, link = tmp / "probe-target", tmp / "probe-link"
    target.write_bytes(b"")
    try:
        os.symlink(str(target), str(link))
    except (OSError, NotImplementedError, AttributeError) as e:
        pytest.skip("平台不允許建立檔案 symlink(%s);硬連結題與 junction 題涵蓋(framework-updates/165)" % type(e).__name__)


def _hardlink_or_skip(src, dst):
    try:
        os.link(str(src), str(dst))
    except (OSError, NotImplementedError, AttributeError) as e:
        pytest.skip("平台不允許建立硬連結(%s)(framework-updates/165)" % type(e).__name__)


def _jsonl_path(fx, run, target):
    return fx.evid / "index.jsonl" if target == "index" else fx.evid / run / "checkpoint.jsonl"


def _junction(target, link):
    import _winapi
    _winapi.CreateJunction(str(target), str(link))


def _dir_symlink(target, link):
    os.symlink(str(target), str(link), target_is_directory=True)


def _swap_after_precheck(monkeypatch, evid, outside, moved, link):
    """替身包住開檔前檢查:它回傳之後,才把證據根目錄換成指向外部目錄的連結。"""
    real = ie._jsonl_precheck
    state = {"swapped": False}

    def swap(site, rel):
        st = real(site, rel)
        if not state["swapped"]:
            state["swapped"] = True
            os.rename(str(evid), str(moved))
            link(outside, evid)
        return st
    monkeypatch.setattr(ie, "_jsonl_precheck", swap)
    return state


# ── Y1 F-1:post-reattach 遇到 HEAD 已不是 S6' 記錄 ⇒ 記錄並停 ────────────────────

def test_ie_Y1_post_reattach_head_moved_records_stop(fx):
    run = to_s6(fx)
    reattach(fx, run)
    s6_head = git_out(fx.repo, "rev-parse", "HEAD")
    moved = move_head(fx)
    index = (fx.repo / ".git" / "index").read_bytes()
    work = work_tree(fx)
    kept = dict((k, v) for k, v in tree_bytes(fx.evid / run).items() if k != "checkpoint.jsonl")
    code, out, err = post_reattach(fx, run)
    assert code == ie.EXIT_MISMATCH, err
    last = fx.events(run)[-1]
    assert (last["step"], last["result"]) == ("S7'", "stopped")
    assert last["detail"]["mismatches"] == [{"item": "head", "snapshot": s6_head, "live": moved}]
    ix = fx.index()[-1]
    assert (ix["event"], ix["step"], ix["reason"]) == ("stopped", "S7'", last["reason"])
    assert git_out(fx.repo, "rev-parse", "HEAD") == moved
    assert (fx.repo / ".git" / "index").read_bytes() == index
    assert work_tree(fx) == work
    assert dict((k, v) for k, v in tree_bytes(fx.evid / run).items() if k != "checkpoint.jsonl") == kept
    assert not (fx.evid / ".lock").exists()


# ── Y2 F-2:受保護開檔(W1)────────────────────────────────────────────────────

@pytest.mark.parametrize("target", ["index", "checkpoint"])
@pytest.mark.parametrize("sub", WRITERS + ["resume"])
def test_ie_Y2_symlinked_jsonl_stops(fx, sub, target):
    _symlink_file_or_skip(fx.tmp)
    run = fx.complete()
    path = _jsonl_path(fx, run, target)
    outside = fx.tmp / "outside.jsonl"
    outside.write_bytes(path.read_bytes())
    path.unlink()
    os.symlink(str(outside), str(path))
    data = outside.read_bytes()
    before = tree_bytes(fx.evid)
    code, out, err = run_any(fx, sub, run)
    assert code == ie.EXIT_PRECONDITION, err
    assert "(d)" in err
    assert outside.read_bytes() == data
    assert tree_bytes(fx.evid) == before


@pytest.mark.parametrize("target", ["index", "checkpoint"])
@pytest.mark.parametrize("sub", WRITERS + ["resume"])
def test_ie_Y2_hardlinked_jsonl_stops(fx, sub, target):
    run = fx.complete()
    path = _jsonl_path(fx, run, target)
    outside = fx.tmp / "outside.jsonl"
    _hardlink_or_skip(path, outside)
    data = outside.read_bytes()
    before = tree_bytes(fx.evid)
    code, out, err = run_any(fx, sub, run)
    assert code == ie.EXIT_PRECONDITION, err
    assert "(d)" in err
    assert outside.read_bytes() == data
    assert tree_bytes(fx.evid) == before


@WINDOWS_ONLY
def test_ie_Y2_evidence_dir_swapped_after_precheck_resume_stops(fx, monkeypatch):
    import shutil
    run = fx.complete()
    outside, moved = fx.tmp / "outside", fx.tmp / "moved"
    shutil.copytree(str(fx.evid), str(outside))
    out_before = tree_bytes(outside)
    state = _swap_after_precheck(monkeypatch, fx.evid, outside, moved, _junction)
    code, out, err = fx.resume(run)
    assert state["swapped"]
    assert code == ie.EXIT_PRECONDITION, err
    assert "(d)" in err
    assert tree_bytes(outside) == out_before


@WINDOWS_ONLY
@pytest.mark.parametrize("mode", ["read", "append"])
def test_ie_Y2_parent_swapped_after_precheck_existing_stops(tmp_path, monkeypatch, mode):
    site, evid = fake_site(tmp_path)
    outside, moved = tmp_path / "outside", tmp_path / "moved"
    outside.mkdir()
    (outside / "index.jsonl").write_bytes(b'{"outside": 1}\n')
    state = _swap_after_precheck(monkeypatch, evid, outside, moved, _junction)
    with pytest.raises(ie.Stop) as e:
        if mode == "read":
            ie._read_jsonl(site, "index.jsonl", "index.jsonl")
        else:
            ie._append_records(site, [("index.jsonl", {"x": 1})])
    assert state["swapped"]
    assert e.value.code == ie.EXIT_PRECONDITION and "(d)" in e.value.reason
    assert (outside / "index.jsonl").read_bytes() == b'{"outside": 1}\n'
    assert (moved / "index.jsonl").read_bytes() == b'{"a": 1}\n'


@WINDOWS_ONLY
def test_ie_Y2_create_swap_before_pin_refused(tmp_path, monkeypatch):
    site, evid = fake_site(tmp_path, index=None)
    outside, moved = tmp_path / "outside", tmp_path / "moved"
    outside.mkdir()
    state = _swap_after_precheck(monkeypatch, evid, outside, moved, _junction)
    with pytest.raises(ie.Stop) as e:
        ie._append_records(site, [("index.jsonl", {"x": 1})])
    assert state["swapped"]
    assert e.value.code == ie.EXIT_PRECONDITION and "(d)" in e.value.reason
    assert os.listdir(str(outside)) == []
    assert os.listdir(str(moved)) == []


@WINDOWS_ONLY
def test_ie_Y2_create_with_pinned_parents_cannot_be_swapped(tmp_path, monkeypatch):
    site, evid = fake_site(tmp_path, index=None)
    outside, moved = tmp_path / "outside", tmp_path / "moved"
    outside.mkdir()
    real = ie._pin_dirs
    seen = []

    def pin_then_try_swap(site_, rel):
        pins = real(site_, rel)
        try:
            os.rename(str(evid), str(moved))
            seen.append("renamed")
        except PermissionError:
            seen.append("rename_refused")
        seen.append(len(pins))
        return pins
    monkeypatch.setattr(ie, "_pin_dirs", pin_then_try_swap)
    ie._append_records(site, [("index.jsonl", {"x": 1})])
    assert seen == ["rename_refused", 2]
    assert (evid / "index.jsonl").read_bytes() == b'{"x": 1}\n'
    assert os.listdir(str(outside)) == []
    assert not moved.exists()


@POSIX_DIRFD
@pytest.mark.parametrize("mode", ["read", "append", "create"])
def test_ie_Y2_posix_parent_swapped_after_precheck_stops(tmp_path, monkeypatch, mode):
    site, evid = fake_site(tmp_path, index=None if mode == "create" else b'{"a": 1}\n')
    outside, moved = tmp_path / "outside", tmp_path / "moved"
    outside.mkdir()
    if mode != "create":
        (outside / "index.jsonl").write_bytes(b'{"outside": 1}\n')
    state = _swap_after_precheck(monkeypatch, evid, outside, moved, _dir_symlink)
    with pytest.raises(ie.Stop) as e:
        if mode == "read":
            ie._read_jsonl(site, "index.jsonl", "index.jsonl")
        else:
            ie._append_records(site, [("index.jsonl", {"x": 1})])
    assert state["swapped"]
    assert e.value.code == ie.EXIT_PRECONDITION
    if mode == "create":
        assert os.listdir(str(outside)) == []
    else:
        assert (outside / "index.jsonl").read_bytes() == b'{"outside": 1}\n'


def test_ie_Y2_cannot_pin_parents_refuses_create(tmp_path, monkeypatch):
    site, evid = fake_site(tmp_path, index=None)
    monkeypatch.setattr(ie, "_w1_method", lambda: "finalpath")
    monkeypatch.setattr(ie, "_win32", lambda: None)
    with pytest.raises(ie.Stop) as e:
        ie._append_records(site, [("index.jsonl", {"x": 1})])
    assert e.value.code == ie.EXIT_PRECONDITION
    assert os.listdir(str(evid)) == []


@pytest.mark.parametrize("mode", ["read", "append"])
def test_ie_Y2_target_replaced_after_check_stops(tmp_path, monkeypatch, mode):
    from types import SimpleNamespace
    site, evid = fake_site(tmp_path)
    real = ie._fstat

    def other_identity(fd):
        st = real(fd)
        return SimpleNamespace(st_mode=st.st_mode, st_nlink=st.st_nlink, st_dev=st.st_dev, st_ino=st.st_ino + 1)
    monkeypatch.setattr(ie, "_fstat", other_identity)
    with pytest.raises(ie.Stop) as e:
        if mode == "read":
            ie._read_jsonl(site, "index.jsonl", "index.jsonl")
        else:
            ie._append_records(site, [("index.jsonl", {"x": 1})])
    assert e.value.code == ie.EXIT_PRECONDITION and "(d)" in e.value.reason
    assert (evid / "index.jsonl").read_bytes() == b'{"a": 1}\n'


@pytest.mark.parametrize("mode", ["read", "append"])
def test_ie_Y2_reparse_attribute_stops(tmp_path, monkeypatch, mode):
    from types import SimpleNamespace
    site, evid = fake_site(tmp_path)
    real = ie._lstat

    def reparse(path):
        st = real(path)
        if str(path).endswith("index.jsonl"):
            return SimpleNamespace(st_mode=st.st_mode, st_nlink=st.st_nlink, st_dev=st.st_dev, st_ino=st.st_ino,
                                   st_file_attributes=0x400)
        return st
    monkeypatch.setattr(ie, "_lstat", reparse)
    with pytest.raises(ie.Stop) as e:
        if mode == "read":
            ie._read_jsonl(site, "index.jsonl", "index.jsonl")
        else:
            ie._append_records(site, [("index.jsonl", {"x": 1})])
    assert e.value.code == ie.EXIT_PRECONDITION and "(d)" in e.value.reason
    assert (evid / "index.jsonl").read_bytes() == b'{"a": 1}\n'


@pytest.mark.parametrize("sub", ["collect", "record-approval", "resume"])
def test_ie_Y2_no_safe_open_method_refuses(fx, monkeypatch, sub):
    run = fx.complete()
    monkeypatch.setattr(ie, "_w1_method", lambda: None)
    before = tree_bytes(fx.evid)
    code, out, err = run_any(fx, sub, run)
    assert code == ie.EXIT_PRECONDITION, err
    assert "平台無法保證" in err
    assert tree_bytes(fx.evid) == before


def test_ie_Y2_bad_tail_checked_on_same_fd(tmp_path, monkeypatch):
    import io
    site, evid = fake_site(tmp_path, index=b'{"a": 1}\n{"b": 2}')
    opened = []
    real_open_fd = ie._open_fd

    def spy_open_fd(path, flags, dir_fd=None):
        opened.append(str(path))
        return real_open_fd(path, flags, dir_fd=dir_fd)
    real_io_open = io.open
    path_opened = []

    def spy_io_open(file, *args, **kwargs):
        path_opened.append(str(file))
        return real_io_open(file, *args, **kwargs)
    monkeypatch.setattr(ie, "_open_fd", spy_open_fd)
    monkeypatch.setattr(ie.io, "open", spy_io_open)
    with pytest.raises(ie.Stop) as e:
        ie._append_records(site, [("index.jsonl", {"x": 1})])
    monkeypatch.setattr(ie.io, "open", real_io_open)     # 之後是測試自己讀檔,不屬工具的開檔
    assert not [p for p in path_opened if p.endswith(".jsonl")]
    assert e.value.code == ie.EXIT_MISMATCH and "最後一行不完整" in e.value.reason
    assert (evid / "index.jsonl").read_bytes() == b'{"a": 1}\n{"b": 2}'
    assert len([p for p in opened if p.endswith("index.jsonl")]) == 1


# ── Y3 W2:紀錄前提與寫入失敗 ─────────────────────────────────────────────────

@pytest.mark.parametrize("kind", ["lock", "hardlink", "tail"])
def test_ie_Y3_record_refused_before_write(fx, monkeypatch, kind):
    run = fx.complete()
    real = ie.verify_run
    snap = {}

    def sabotage(site, run_id):
        info = real(site, run_id)
        if kind == "lock":
            (fx.evid / ".lock").write_bytes(OTHER_LOCK)
        elif kind == "hardlink":
            _hardlink_or_skip(fx.evid / "index.jsonl", fx.tmp / "outside.jsonl")
        else:
            with open(str(fx.evid / "index.jsonl"), "ab") as fh:
                fh.write(b"{")
        snap["tree"] = tree_bytes(fx.evid)
        return info
    monkeypatch.setattr(ie, "verify_run", sabotage)
    code, out, err = approve(fx, run, "0" * 64)
    assert code == ie.EXIT_INTERNAL, err
    assert "失配未記錄" in err
    assert without_lock(tree_bytes(fx.evid)) == without_lock(snap["tree"])
    if kind == "lock":
        assert (fx.evid / ".lock").read_bytes() == OTHER_LOCK


def test_ie_Y3_half_line_kept_and_detected(fx, monkeypatch):
    run = fx.complete()
    real_write, orig = os.write, ie._os_write
    monkeypatch.setattr(ie, "_os_write", lambda fd, data: real_write(fd, data[:len(data) // 2]))
    code, out, err = approve(fx, run, "0" * 64)
    monkeypatch.setattr(ie, "_os_write", orig)
    assert code == ie.EXIT_INTERNAL, err
    assert "寫入途中失敗" in err
    assert not (fx.evid / run / "checkpoint.jsonl").read_bytes().endswith(b"\n")
    before = without_lock(tree_bytes(fx.evid))
    for call in (lambda: fx.resume(run), lambda: approve(fx, run), fx.collect):
        code, out, err = call()
        assert code == ie.EXIT_MISMATCH, err
        assert "不完整" in err
        assert without_lock(tree_bytes(fx.evid)) == before


def test_ie_Y3_checkpoint_written_index_failed_is_inconsistent(fx, monkeypatch):
    run = fx.complete()
    real_write, orig = os.write, ie._os_write
    calls = []

    def second_fails(fd, data):
        calls.append(len(data))
        if len(calls) == 2:
            raise OSError("simulated")
        return real_write(fd, data)
    monkeypatch.setattr(ie, "_os_write", second_fails)
    code, out, err = approve(fx, run, "0" * 64)
    monkeypatch.setattr(ie, "_os_write", orig)
    assert code == ie.EXIT_INTERNAL, err
    assert "寫入途中失敗" in err
    cp, ix = stop_marks(fx, run)
    assert len(cp) == 1 and ix == []
    before = tree_bytes(fx.evid)
    for call in (lambda: fx.resume(run), lambda: approve(fx, run)):
        code, out, err = call()
        assert code == ie.EXIT_MISMATCH, err
        assert "紀錄不一致" in err
        assert tree_bytes(fx.evid) == before
    with pytest.raises(ie.Stop) as e:
        ie.verify_run(site_of(fx), run)
    assert e.value.code == ie.EXIT_MISMATCH and "紀錄不一致" in e.value.reason


def test_ie_Y3_index_without_checkpoint_is_inconsistent(fx):
    run = fx.complete()
    assert approve(fx, run, "0" * 64)[0] == ie.EXIT_MISMATCH
    cp = fx.evid / run / "checkpoint.jsonl"
    lines = read_lines(cp)
    assert json.loads(lines[-1])["result"] == "stopped"
    write_lines(cp, lines[:-1])
    before = tree_bytes(fx.evid)
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_MISMATCH
    assert "紀錄不一致" in err
    assert tree_bytes(fx.evid) == before


# ── Y4 F-3:名冊工作區位置變成目錄 ⇒ 失配,記錄並停 ──────────────────────────────

def test_ie_Y4_inventory_path_became_directory_records_stop(fx):
    run = to_s6(fx)
    reattach(fx, run)
    inv = fx.repo / INVENTORY_REL
    inv.unlink()
    inv.mkdir()
    head = git_out(fx.repo, "rev-parse", "HEAD")
    index = (fx.repo / ".git" / "index").read_bytes()
    work = work_tree(fx)
    code, out, err = post_reattach(fx, run)
    assert code == ie.EXIT_MISMATCH, err
    last = fx.events(run)[-1]
    assert (last["step"], last["result"]) == ("S7'", "stopped")
    assert "inventory_worktree" in [m["item"] for m in last["detail"]["mismatches"]]
    ix = fx.index()[-1]
    assert (ix["event"], ix["step"], ix["reason"]) == ("stopped", "S7'", last["reason"])
    assert git_out(fx.repo, "rev-parse", "HEAD") == head
    assert (fx.repo / ".git" / "index").read_bytes() == index
    assert work_tree(fx) == work
    assert inv.is_dir()


# ── Y5 F-4:帶時區的對照題 ─────────────────────────────────────────────────────

def test_ie_Y5_approved_at_with_timezone_passes_argument_check(fx, monkeypatch):
    unstable(fx, monkeypatch)
    assert fx.collect()[0] == ie.EXIT_MISMATCH
    [run] = fx.runs()
    code, out, err = approve(fx, run, "0" * 64, approved_at="2026-10-29T12:00:00-04:00")
    assert code == ie.EXIT_MISMATCH, err
    assert "S3 尚未完成" in err
    assert "時區" not in err


# ── Y6 F-5:經 _locked 的停下各記一筆 ──────────────────────────────────────────

def test_ie_Y6_order_error_records_exactly_one_stop_pair(fx):
    run = fx.complete()
    assert approve(fx, run)[0] == ie.EXIT_OK
    before = tree_bytes(fx.evid)
    code, out, err = post_register(fx, run)
    assert code == ie.EXIT_MISMATCH
    assert "S5 尚未完成" in err
    assert_one_stop_recorded(fx, run, before)
    ie.verify_run(site_of(fx), run)
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_OK, err
    assert "停下" in out and "S5 尚未完成" in out and "pre-register" in out


def test_ie_Y6_retry_after_recorded_stop_succeeds(fx):
    run = fx.complete()
    assert approve(fx, run, "0" * 64)[0] == ie.EXIT_MISMATCH
    code, out, err = approve(fx, run)
    assert code == ie.EXIT_OK, err
    assert steps_of(fx, run)[-1] == "S4"
    ie.verify_run(site_of(fx), run)
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_OK, err
    assert "pre-register" in out


@pytest.mark.parametrize("kind", ["artifact_missing", "tail_incomplete", "order_conflict"])
def test_ie_Y6_incomplete_run_with_bad_evidence_not_recorded(fx, monkeypatch, kind):
    unstable(fx, monkeypatch)
    assert fx.collect()[0] == ie.EXIT_MISMATCH
    [run] = fx.runs()
    rd = fx.evid / run
    cp = rd / "checkpoint.jsonl"
    if kind == "artifact_missing":
        (rd / "snapshot.json").unlink()
    elif kind == "tail_incomplete":
        with open(str(cp), "ab") as fh:
            fh.write(b'{"step"')
    else:
        lines = read_lines(cp)
        write_lines(cp, [lines[0]] + lines)
    before = tree_bytes(fx.evid)
    code, out, err = approve(fx, run, "0" * 64)
    assert code == ie.EXIT_MISMATCH, err
    assert tree_bytes(fx.evid) == before


def test_ie_Y6_recorded_mismatch_not_recorded_twice(fx):
    run = to_s5(fx)
    _g_change(fx, run, "work")
    assert post_register(fx, run)[0] == ie.EXIT_MISMATCH
    cp, ix = stop_marks(fx, run)
    assert [(e["step"], e["result"]) for e in cp] == [("S6'", "stopped")]
    assert [(r["step"], r["event"]) for r in ix] == [("S6'", "stopped")]


def test_ie_Y6_void_not_recorded_twice(fx):
    run = fx.complete()
    assert approve(fx, run)[0] == ie.EXIT_OK
    (fx.repo / "tracked.txt").write_bytes(b"changed\n")
    assert pre_register(fx, run)[0] == ie.EXIT_MISMATCH
    cp, ix = stop_marks(fx, run)
    assert [(e["step"], e["result"]) for e in cp] == [("S5", "approval_void")]
    assert [(r["step"], r["event"]) for r in ix] == [("S5", "approval_void")]


def test_ie_Y6_untrusted_evidence_writes_nothing(fx):
    run = fx.complete()
    rd = fx.evid / run
    (rd / "diff.json").write_bytes((rd / "diff.json").read_bytes() + b" ")
    before = tree_bytes(fx.evid)
    code, out, err = approve(fx, run, "0" * 64)
    assert code == ie.EXIT_MISMATCH
    assert tree_bytes(fx.evid) == before


# ── Y7 F-6:證據目錄本身是 junction ───────────────────────────────────────────

@pytest.mark.skipif(os.name != "nt", reason="junction 只在 Windows 建得出來;其他平台由 symlink 題涵蓋(framework-updates/165)")
@pytest.mark.parametrize("sub", WRITERS + ["resume"])
def test_ie_Y7_junction_evidence_dir_stops(fx, sub):
    run = fx.complete()
    outside = fx.tmp / "outside"
    os.rename(str(fx.evid), str(outside))
    _junction(outside, fx.evid)
    before = tree_bytes(outside)
    code, out, err = run_any(fx, sub, run)
    assert code == ie.EXIT_PRECONDITION, err
    assert "(d)" in err
    assert tree_bytes(outside) == before


# ── Y8 F-7:鎖釋放失敗不回成功 ─────────────────────────────────────────────────

@pytest.mark.parametrize("path", ["collect", "locked"])
@pytest.mark.parametrize("fail", [False, True])
def test_ie_Y8_lock_release_failure_never_reports_success(fx, monkeypatch, path, fail):
    if path == "collect":
        if fail:
            unstable(fx, monkeypatch)
        monkeypatch.setattr(ie, "_release_lock", lambda lock_path, content: False)
        code, out, err = fx.collect()
    else:
        run = fx.complete()
        monkeypatch.setattr(ie, "_release_lock", lambda lock_path, content: False)
        code, out, err = approve(fx, run, "0" * 64 if fail else None)
    assert code == (ie.EXIT_MISMATCH if fail else ie.EXIT_INTERNAL), err
    assert "鎖釋放失敗" in err


# ── Y9 結構:JSONL 只經 W1 的受保護開檔 ─────────────────────────────────────────

def test_ie_Y9_jsonl_only_through_protected_open():
    import ast
    tree = ast.parse(MODULE_PATH.read_bytes().decode("utf-8"))
    funcs = dict((n.name, n) for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))

    def calls(fn):
        out = []
        for n in ast.walk(fn):
            if isinstance(n, ast.Call):
                f = n.func
                if isinstance(f, ast.Name):
                    out.append((f.id, n))
                elif isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
                    out.append((f.value.id + "." + f.attr, n))
        return out

    def called(fn):
        return set(name for name, _n in calls(fn))

    def names(node):
        return set(n.id for n in ast.walk(node) if isinstance(n, ast.Name))

    jsonl = {"CHECKPOINT_NAME", "INDEX_NAME"}
    jsonl_funcs = [name for name, fn in funcs.items() if names(fn) & jsonl]
    assert jsonl_funcs
    for name in jsonl_funcs:
        assert not called(funcs[name]) & {"open", "io.open", "os.open", "os.fdopen", "_open_fd"}, name
    for name, fn in funcs.items():
        for callee, node in calls(fn):
            if callee in ("_file_sha", "_load", "io.open", "open", "os.open"):
                assert not any(names(a) & jsonl for a in node.args), (name, callee)
        for n in ast.walk(fn):
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                assert not re.fullmatch(r"[\w./-]*\.jsonl", n.value), (name, n.value)
    assert "_jsonl_open" in called(funcs["_read_jsonl"])
    assert "_jsonl_open" in called(funcs["_open_for_append"])
    assert "_open_for_append" in called(funcs["_append_records"])

    def owners(callee):
        return sorted(name for name, fn in funcs.items() if callee in called(fn))
    assert owners("_open_fd") == ["_jsonl_open", "_open_dirfd"]
    assert owners("os.open") == ["_acquire_lock", "_open_fd", "_write_artifact"]
    assert owners("io.open") == sorted(["_file_sha", "_load", "_release_lock", "_require_own_lock",
                                        "_worktree_state", "pre_register"])
    appends = sorted(name for name, fn in funcs.items()
                     if any(isinstance(n, ast.Attribute) and n.attr == "O_APPEND" for n in ast.walk(fn)))
    assert appends == ["_jsonl_open"]


# ── Y10 收尾補寫(裁定 B1 例外)────────────────────────────────────────────────

@pytest.mark.parametrize("target", ["_write_s8", "_index_run_completed"])
@pytest.mark.parametrize("change", ["head", "reattach", "lock"])
def test_ie_Y10_closing_requires_all_checks(fx, monkeypatch, target, change):
    run = _closing_interrupted(fx, monkeypatch, target)
    s8_before = steps_of(fx, run).count("S8")
    before = None
    if change == "head":
        move_head(fx)
    elif change == "reattach":
        (fx.repo / "tracked.txt").write_bytes(b"five\n")
    else:
        real = ie._reattach_mismatches

        def steal(*args):
            (fx.evid / ".lock").write_bytes(OTHER_LOCK)
            return real(*args)
        monkeypatch.setattr(ie, "_reattach_mismatches", steal)
        before = without_lock(tree_bytes(fx.evid))
    code, out, err = post_reattach(fx, run)
    assert code == (ie.EXIT_INTERNAL if change == "lock" else ie.EXIT_MISMATCH), err
    assert steps_of(fx, run).count("S8") == s8_before
    assert [r["event"] for r in fx.index()].count("run_completed") == 0
    if change == "lock":
        assert "失配未記錄" in err
        assert without_lock(tree_bytes(fx.evid)) == before


@pytest.mark.parametrize("target", ["_write_s8", "_index_run_completed"])
def test_ie_Y10_closing_completed_then_rerun_writes_nothing(fx, monkeypatch, target):
    run = _closing_interrupted(fx, monkeypatch, target)
    code, out, err = post_reattach(fx, run)
    assert code == ie.EXIT_OK, err
    [s8] = [e for e in fx.events(run) if e["step"] == "S8" and e["result"] == "completed"]
    [final] = [r for r in fx.index() if r["event"] == "run_completed"]
    assert (final["run_id"], final["package_fingerprint"], final["new_head"]) == (
        s8["detail"]["run_id"], s8["detail"]["package_fingerprint"], s8["detail"]["new_head"])
    before = frozen(fx)
    code, out, err = post_reattach(fx, run)
    assert code == ie.EXIT_OK, err
    assert frozen(fx) == before


# ── Y11 停下／核准不適用的逐筆配對 ──────────────────────────────────────────────

@pytest.mark.parametrize("kind", ["step", "fingerprint"])
def test_ie_Y11_stop_pairing_mismatch_is_inconsistent(fx, kind):
    run = fx.complete()
    assert approve(fx, run, "0" * 64)[0] == ie.EXIT_MISMATCH
    if kind == "step":
        recs = fx.index()
        assert recs[-1]["event"] == "stopped"
        recs[-1]["step"] = "S5"
        write_lines(fx.evid / "index.jsonl", [line_of(r) for r in recs])
    else:
        cp = fx.evid / run / "checkpoint.jsonl"
        recs = fx.events(run)
        assert recs[-1]["result"] == "stopped"
        recs[-1]["fingerprints"]["package_fingerprint"] = "1" * 64
        write_lines(cp, [line_of(r) for r in recs])
    before = tree_bytes(fx.evid)
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_MISMATCH
    assert "紀錄不一致" in err
    assert tree_bytes(fx.evid) == before


# ── Y12 收尾追加:檢查與寫入在同一個 fd(不得另開核對)───────────────────────────

@pytest.mark.parametrize("target", ["_write_s8", "_index_run_completed"])
def test_ie_Y12_closing_index_append_uses_one_fd(fx, monkeypatch, target):
    run = _closing_interrupted(fx, monkeypatch, target)
    events = []
    state = {"after_verify": False}
    real_verify, real_open_fd, real_fstat, real_write = ie.verify_run, ie._open_fd, ie._fstat, ie._os_write
    real_tail = ie._JsonlFile.check_tail

    def verify(site, run_id):
        info = real_verify(site, run_id)
        state["after_verify"] = True            # 之前證據重驗的唯讀開檔不計入
        return info

    def open_fd(path, flags, dir_fd=None):
        fd = real_open_fd(path, flags, dir_fd=dir_fd)
        if state["after_verify"]:
            events.append(("open", str(path), fd))
        return fd

    def fstat(fd):
        if state["after_verify"]:
            events.append(("fstat", fd))
        return real_fstat(fd)

    def tail(self):
        if state["after_verify"]:
            events.append(("tail", self.fd))
        return real_tail(self)

    def write(fd, data):
        if state["after_verify"]:
            events.append(("write", fd, data))
        return real_write(fd, data)
    monkeypatch.setattr(ie, "verify_run", verify)
    monkeypatch.setattr(ie, "_open_fd", open_fd)
    monkeypatch.setattr(ie, "_fstat", fstat)
    monkeypatch.setattr(ie, "_os_write", write)
    monkeypatch.setattr(ie._JsonlFile, "check_tail", tail)
    code, out, err = post_reattach(fx, run)
    assert code == ie.EXIT_OK, err
    opens = [i for i, e in enumerate(events) if e[0] == "open" and e[1].endswith("index.jsonl")]
    writes = [i for i, e in enumerate(events) if e[0] == "write" and b'"run_completed"' in e[2]]
    assert len(opens) == 1, events
    assert len(writes) == 1
    fd = events[opens[0]][2]
    assert opens[0] < writes[0] and events[writes[0]][1] == fd
    between = events[opens[0]:writes[0]]
    assert ("fstat", fd) in between and ("tail", fd) in between


# ── Y13 POSIX:原件、鎖、目錄的建立與刪除走方式甲(dir_fd 鏈)───────────────────────
#
# 本機(Windows)skip:本機未實測,先紅無法在本機驗證,待 CI。

RUN_X = "20261029T000000Z-0000000"


def _posix_swap(path, outside):
    """把 `path` 換成指向 `outside` 的目錄 symlink(建立前父目錄被換掉)。"""
    os.rename(str(path), str(path) + "-moved")
    os.symlink(str(outside), str(path), target_is_directory=True)


@POSIX_DIRFD
def test_ie_Y13_posix_artifact_not_created_through_link(tmp_path):
    site, evid = fake_site(tmp_path, index=None)
    (evid / RUN_X).mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    _posix_swap(evid / RUN_X, outside)
    ctx = dict(site, run_id=RUN_X, run_dir=str(evid / RUN_X))
    with pytest.raises(ie.Stop) as e:
        ie._write_artifact(ctx, "snapshot.json", b"x\n")
    assert e.value.code == ie.EXIT_PRECONDITION
    assert os.listdir(str(outside)) == []


@POSIX_DIRFD
def test_ie_Y13_posix_lock_not_created_through_link(tmp_path):
    site, evid = fake_site(tmp_path, index=None)
    outside = tmp_path / "outside"
    outside.mkdir()
    _posix_swap(evid, outside)
    with pytest.raises(ie.Stop) as e:
        ie._acquire_lock(str(evid), RUN_X)
    assert e.value.code == ie.EXIT_PRECONDITION
    assert os.listdir(str(outside)) == []


@POSIX_DIRFD
def test_ie_Y13_posix_lock_not_removed_through_link(tmp_path):
    site, evid = fake_site(tmp_path, index=None)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / ".lock").write_bytes(b"mine")
    _posix_swap(evid, outside)
    assert ie._release_lock(str(evid / ".lock"), b"mine") is False
    assert (outside / ".lock").read_bytes() == b"mine"


@POSIX_DIRFD
@pytest.mark.parametrize("which", ["evidence_root", "run_dir"])
def test_ie_Y13_posix_dir_not_created_through_link(tmp_path, which):
    site, evid = fake_site(tmp_path, index=None)
    outside = tmp_path / "outside"
    outside.mkdir()
    if which == "evidence_root":
        evid.rmdir()
        _posix_swap(evid.parent, outside)
        parts = [".dev", "inventory-evidence"]
    else:
        _posix_swap(evid, outside)
        parts = [".dev", "inventory-evidence", RUN_X]
    with pytest.raises(ie.Stop) as e:
        ie._make_dir(site, parts, exist_ok=which == "evidence_root")
    assert e.value.code == ie.EXIT_PRECONDITION
    assert os.listdir(str(outside)) == []


# ── X 區:核准不適用 ───────────────────────────────────────────────────────────

def test_ie_X1_void_approval_never_reusable(fx):
    run = fx.complete()
    assert approve(fx, run)[0] == ie.EXIT_OK
    fp = fingerprint_of(fx, run)
    approval = (fx.evid / run / "approval.json").read_bytes()
    p = fx.repo / "tracked.txt"
    original = p.read_bytes()
    p.write_bytes(b"changed\n")
    code, out, err = pre_register(fx, run)
    assert code == ie.EXIT_MISMATCH and "不適用" in err
    p.write_bytes(original)                      # 現場改回與快照完全相同
    for step in (pre_register, post_register, post_reattach):
        code, out, err = step(fx, run)
        assert code == ie.EXIT_MISMATCH, step.__name__
        assert "不適用" in err, step.__name__
    assert approve(fx, run)[0] == ie.EXIT_MISMATCH
    assert (fx.evid / run / "approval.json").read_bytes() == approval
    [void] = [e for e in fx.events(run) if e["result"] == "approval_void"]
    assert void["fingerprints"] == {"package_fingerprint": fp, "approval.json": sha(approval)}
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_MISMATCH
    assert "重新 collect" in out


# ── G 區:登記後核對 ───────────────────────────────────────────────────────────

def test_ie_G1_post_register_passes(fx):
    run = to_s5(fx)
    register(fx, run)
    code, out, err = post_register(fx, run)
    assert code == ie.EXIT_OK, err
    assert "接回" in out
    [s6] = [e for e in fx.events(run) if e["step"] == "S6'" and e["result"] == "completed"]
    assert s6["detail"]["new_head"] == git_out(fx.repo, "rev-parse", "HEAD")


def _g_change(fx, run, kind):
    if kind == "parent":
        register(fx, run)
        (fx.repo / "later.txt").write_bytes(b"l\n")
        git(fx.repo, "add", "--", "later.txt")
        git(fx.repo, "commit", "-q", "-m", "later")
    elif kind == "extra_file":
        def extra():
            (fx.repo / "other.txt").write_bytes(b"o\n")
            git(fx.repo, "add", "--", "other.txt")
        register(fx, run, extra=extra)
    elif kind == "mode":
        register(fx, run, extra=lambda: git(fx.repo, "update-index", "--chmod=+x", "--", ".gitignore"))
    elif kind == "blob":
        register(fx, run, content=(fx.evid / run / "candidate-inventory.json").read_bytes() + b"\n")
    elif kind == "r10":
        register(fx, run)
        (fx.bucket / "c.txt").write_bytes(b"changed after register\n")
    elif kind == "work":
        register(fx, run)
        (fx.repo / "tracked.txt").write_bytes(b"four\n")
    else:
        raise AssertionError(kind)


@pytest.mark.parametrize("kind", ["parent", "extra_file", "mode", "blob", "r10", "work"])
def test_ie_G2_post_register_mismatch_keeps_commit(fx, kind):
    run = to_s5(fx)
    _g_change(fx, run, kind)
    head = git_out(fx.repo, "rev-parse", "HEAD")
    index = (fx.repo / ".git" / "index").read_bytes()
    work = dict((k, v) for k, v in tree_bytes(fx.repo).items() if not k.startswith(".dev/"))
    code, out, err = post_register(fx, run)
    assert code == ie.EXIT_MISMATCH, err
    assert git_out(fx.repo, "rev-parse", "HEAD") == head
    assert (fx.repo / ".git" / "index").read_bytes() == index
    assert dict((k, v) for k, v in tree_bytes(fx.repo).items() if not k.startswith(".dev/")) == work
    last = fx.events(run)[-1]
    assert (last["step"], last["result"]) == ("S6'", "stopped")
    assert "S6'" not in steps_of(fx, run)


# ── H 區:接回後核對 ───────────────────────────────────────────────────────────

def test_ie_H1_post_reattach_passes_and_closes(fx):
    run = to_s6(fx)
    reattach(fx, run)
    code, out, err = post_reattach(fx, run)
    assert code == ie.EXIT_OK, err
    assert steps_of(fx, run)[-2:] == ["S7'", "S8"]
    fp = fingerprint_of(fx, run)
    head = git_out(fx.repo, "rev-parse", "HEAD")
    [s8] = [e for e in fx.events(run) if e["step"] == "S8"]
    assert (s8["detail"]["run_id"], s8["detail"]["package_fingerprint"], s8["detail"]["new_head"]) == (run, fp, head)
    last = fx.index()[-1]
    assert (last["event"], last["package_fingerprint"], last["new_head"]) == ("run_completed", fp, head)


def _h_change(fx, run, kind):
    if kind == "missing_one":
        reattach(fx, run, skip={"new.txt"})
    elif kind == "extra_one":
        reattach(fx, run)
        (fx.repo / "u.txt").write_bytes(b"u\n")
        git(fx.repo, "add", "--", "u.txt")
    elif kind == "blob_differs":
        reattach(fx, run, skip={"tracked.txt"})
        git(fx.repo, "add", "--", "tracked.txt")
    elif kind == "deleted_present":
        reattach(fx, run, skip={"gone.txt"})
    elif kind == "partial_differs":
        reattach(fx, run)
        blob = git_out(fx.repo, "rev-parse", "HEAD:tracked.txt")
        git(fx.repo, "update-index", "--cacheinfo", "100644,%s,tracked.txt" % blob)
    elif kind == "worktree":
        reattach(fx, run)
        (fx.repo / "tracked.txt").write_bytes(b"five\n")
    else:
        raise AssertionError(kind)


@pytest.mark.parametrize("kind", ["missing_one", "extra_one", "blob_differs", "deleted_present",
                                  "partial_differs", "worktree"])
def test_ie_H2_post_reattach_mismatch_stops_without_changes(fx, kind):
    run = to_s6(fx)
    _h_change(fx, run, kind)
    head = git_out(fx.repo, "rev-parse", "HEAD")
    index = (fx.repo / ".git" / "index").read_bytes()
    work = dict((k, v) for k, v in tree_bytes(fx.repo).items() if not k.startswith(".dev/"))
    code, out, err = post_reattach(fx, run)
    assert code == ie.EXIT_MISMATCH, err
    assert git_out(fx.repo, "rev-parse", "HEAD") == head
    assert (fx.repo / ".git" / "index").read_bytes() == index
    assert dict((k, v) for k, v in tree_bytes(fx.repo).items() if not k.startswith(".dev/")) == work
    assert "S7'" not in steps_of(fx, run)
    assert (fx.events(run)[-1]["step"], fx.events(run)[-1]["result"]) == ("S7'", "stopped")


def test_ie_H3_untracked_difference_listed_unverified(fx):
    run = to_s6(fx)
    reattach(fx, run)
    (fx.repo / "late.txt").write_bytes(b"late\n")
    code, out, err = post_reattach(fx, run)
    assert code == ie.EXIT_OK, err
    assert "late.txt" in out and "內容未驗證" in out
    [s7] = [e for e in fx.events(run) if e["step"] == "S7'"]
    assert s7["detail"]["untracked_added"] == ["late.txt"]
    assert s7["detail"]["content_verified"] is False
    [s8] = [e for e in fx.events(run) if e["step"] == "S8"]
    assert s8["detail"]["untracked_diff_count"] == 1


# ── W 區:resume 完整版 ───────────────────────────────────────────────────────

def test_ie_W1_resume_after_s3_and_s4(fx):
    run = fx.complete()
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_OK and "record-approval" in out
    assert approve(fx, run)[0] == ie.EXIT_OK
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_OK and "pre-register" in out


def test_ie_W2_s5_not_registered_points_to_registration(fx):
    run = to_s5(fx)
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_OK, err
    assert "尚未登記" in out and "post-register" in out


def test_ie_W3_s5_registered_points_to_post_register_only(fx):
    run = to_s5(fx)
    register(fx, run)
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_OK, err
    assert "post-register" in out
    assert "尚未登記" not in out


@pytest.mark.parametrize("kind", ["two_commits", "other_file"])
def test_ie_W4_s5_unrecognized_state_stops(fx, kind):
    run = to_s5(fx)
    if kind == "two_commits":
        register(fx, run)
        git(fx.repo, "commit", "-q", "--allow-empty", "-m", "second")
    else:
        _g_change(fx, run, "extra_file")
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_MISMATCH
    assert "無法辨識" in err


def test_ie_W5_s6_not_reattached_points_to_reattach(fx):
    run = to_s6(fx)
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_OK, err
    assert "尚未接回" in out and "post-reattach" in out


@pytest.mark.parametrize("skip", [(), ("new.txt",)])
def test_ie_W6_s6_reattached_points_to_post_reattach_only(fx, skip):
    run = to_s6(fx)
    reattach(fx, run, skip=skip)
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_OK, err
    assert "post-reattach" in out
    assert "尚未接回" not in out


@pytest.mark.parametrize("kind", ["foreign_staged", "head_moved"])
def test_ie_W7_s6_unrecognized_state_stops(fx, kind):
    run = to_s6(fx)
    if kind == "foreign_staged":
        (fx.repo / "u.txt").write_bytes(b"u\n")
        git(fx.repo, "add", "--", "u.txt")
    else:
        git(fx.repo, "commit", "-q", "--allow-empty", "-m", "moved")
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_MISMATCH


def test_ie_W8_void_points_to_recollect_only(fx):
    run = fx.complete()
    assert approve(fx, run)[0] == ie.EXIT_OK
    (fx.repo / "tracked.txt").write_bytes(b"changed\n")
    assert pre_register(fx, run)[0] == ie.EXIT_MISMATCH
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_MISMATCH
    assert "重新 collect" in out
    assert "下一步:pre-register" not in out and "post-register" not in out


def _closing_interrupted(fx, monkeypatch, target):
    run = to_s6(fx)
    reattach(fx, run)
    real = getattr(ie, target)

    def boom(*args):
        raise ie.Stop(ie.EXIT_INTERNAL, "test interruption")
    monkeypatch.setattr(ie, target, boom)
    code, out, err = post_reattach(fx, run)
    assert code == ie.EXIT_INTERNAL
    monkeypatch.setattr(ie, target, real)
    return run


@pytest.mark.parametrize("target,s8_before", [("_write_s8", 0), ("_index_run_completed", 1)])
def test_ie_W9_closing_interrupted_then_completed(fx, monkeypatch, target, s8_before):
    run = _closing_interrupted(fx, monkeypatch, target)
    assert steps_of(fx, run).count("S7'") == 1
    assert steps_of(fx, run).count("S8") == s8_before
    before = frozen(fx)
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_OK, err
    assert "核對已完成、收尾紀錄未完成" in out
    assert "流程已完成" not in out
    assert frozen(fx) == before
    code, out, err = post_reattach(fx, run)
    assert code == ie.EXIT_OK, err
    assert steps_of(fx, run).count("S7'") == 1
    assert steps_of(fx, run).count("S8") == 1
    assert [r["event"] for r in fx.index()].count("run_completed") == 1
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_OK, err
    assert "流程已完成" in out


def test_ie_W10_s8_and_index_completion_inconsistent_stops(fx):
    run = to_s8(fx)
    recs = fx.index()
    for r in recs:
        if r["event"] == "run_completed":
            r["new_head"] = "0" * 40
    write_lines(fx.evid / "index.jsonl", [line_of(r) for r in recs])
    before = frozen(fx)
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_MISMATCH
    assert frozen(fx) == before


@pytest.mark.parametrize("kind", ["swap_s4_s5", "duplicate_s5"])
def test_ie_W11_new_step_order_violation_stops(fx, kind):
    run = to_s5(fx)
    if kind == "swap_s4_s5":
        swap_steps(fx, run, "S4", "S5")
    else:
        cp = fx.evid / run / "checkpoint.jsonl"
        lines = read_lines(cp)
        write_lines(cp, lines + [lines[-1]])
    before = frozen(fx)
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_MISMATCH
    assert frozen(fx) == before


def test_ie_W12_stopped_event_reason_printed(fx):
    run = to_s5(fx)
    _g_change(fx, run, "work")
    assert post_register(fx, run)[0] == ie.EXIT_MISMATCH
    (fx.repo / "tracked.txt").write_bytes(b"three\n")
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_OK, err
    assert "停下" in out and "post-register" in out


def test_ie_W13_resume_never_writes_or_locks(fx, monkeypatch):
    run = to_s6(fx)
    reattach(fx, run, skip={"new.txt"})
    calls = []

    def no_lock(*args):
        calls.append(args)
        raise AssertionError("resume 不得取鎖")
    monkeypatch.setattr(ie, "_acquire_lock", no_lock)
    before = frozen(fx)
    code, out, err = fx.resume(run)
    assert code == ie.EXIT_OK, err
    assert frozen(fx) == before
    assert calls == []


# ── L 區補:每個會寫入的子命令都要拿鎖 ─────────────────────────────────────────

@pytest.mark.parametrize("sub", ["record-approval", "pre-register", "post-register", "post-reattach"])
def test_ie_L5_writers_stop_when_lock_held(fx, sub):
    run = fx.complete()
    fp = fingerprint_of(fx, run)
    (fx.evid / ".lock").write_bytes(b'{"pid": 1, "run_id": "someone-else"}\n')
    before = tree_bytes(fx.evid)
    if sub == "record-approval":
        code, out, err = approve(fx, run, fp)
    else:
        code, out, err = run_cmd(fx, sub, "--run", run, claude=(sub != "post-reattach"))
    assert code == ie.EXIT_MISMATCH
    assert "鎖" in err
    assert tree_bytes(fx.evid) == before


def test_ie_L6_run_dir_created_after_lock(fx, monkeypatch):
    real = ie._acquire_lock
    seen = []

    def spy(evid, run_id):
        seen.append(os.path.exists(os.path.join(evid, run_id)))
        return real(evid, run_id)
    monkeypatch.setattr(ie, "_acquire_lock", spy)
    fx.complete()
    assert seen == [False]


# ── M 區補:新增子命令仍只用唯讀 git ───────────────────────────────────────────

def test_ie_M5_new_subcommands_only_read_only_git(fx, monkeypatch):
    calls = []
    state = {"on": False}
    real = subprocess.run

    def recorder(*args, **kwargs):
        if state["on"]:
            calls.append([str(a) for a in (args[0] if args else kwargs["args"])])
        return real(*args, **kwargs)
    monkeypatch.setattr(subprocess, "run", recorder)

    def tool(fn, *args):
        state["on"] = True
        try:
            return fn(*args)
        finally:
            state["on"] = False
    setup_work(fx)
    drift_live(fx)
    assert tool(fx.collect)[0] == ie.EXIT_OK
    run = fx.runs()[-1]
    assert tool(approve, fx, run)[0] == ie.EXIT_OK
    assert tool(pre_register, fx, run)[0] == ie.EXIT_OK
    register(fx, run)
    assert tool(post_register, fx, run)[0] == ie.EXIT_OK
    reattach(fx, run)
    assert tool(post_reattach, fx, run)[0] == ie.EXIT_OK
    assert tool(fx.resume, run)[0] == ie.EXIT_OK
    assert calls
    for argv in calls:
        assert os.path.basename(argv[0]).lower().startswith("git"), argv
        sub, rest = _git_subcommand(argv)
        assert sub in READ_ONLY_GIT and sub not in FORBIDDEN_GIT, argv
        if sub == "hash-object":
            assert "-w" not in rest, argv
        if sub == "remote":
            assert rest[:1] == ["get-url"], argv
        if sub == "config":
            assert "--get" in rest, argv


# ── V 區補:新增原件與事件的證據重驗 ───────────────────────────────────────────

@pytest.mark.parametrize("kind", ["approval_modified", "s4_event_missing", "s5_before_s4", "void_fingerprint_mismatch"])
def test_ie_V2_extended_evidence_tamper_stops(fx, kind):
    run = fx.complete()
    assert approve(fx, run)[0] == ie.EXIT_OK
    rd = fx.evid / run
    cp = rd / "checkpoint.jsonl"
    if kind == "approval_modified":
        (rd / "approval.json").write_bytes((rd / "approval.json").read_bytes() + b" ")
    elif kind == "s4_event_missing":
        write_lines(cp, [line for line in read_lines(cp) if json.loads(line)["step"] != "S4"])
    elif kind == "s5_before_s4":
        assert pre_register(fx, run)[0] == ie.EXIT_OK
        swap_steps(fx, run, "S4", "S5")
    else:
        (fx.repo / "tracked.txt").write_bytes(b"changed\n")
        assert pre_register(fx, run)[0] == ie.EXIT_MISMATCH
        recs = fx.events(run)
        for r in recs:
            if r["result"] == "approval_void":
                r["fingerprints"]["package_fingerprint"] = "1" * 64
        write_lines(cp, [line_of(r) for r in recs])
    before = frozen(fx)
    assert fx.resume(run)[0] == ie.EXIT_MISMATCH
    assert pre_register(fx, run)[0] == ie.EXIT_MISMATCH
    assert frozen(fx) == before
