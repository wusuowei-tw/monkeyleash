# -*- coding: utf-8 -*-
"""票 165:R10 名冊的證據蒐集、核准代記、登記前重驗、登記前後核對與接續驗證。

**只讀比記。** 讀 git、讀 R10 的觀測結果(`redlight.extension_report`),把指紋寫進
`.dev/inventory-evidence/`;**不改 index、不改 refs、不寫 `.agents/`** —— 登記與接回原工作
是 VS 依現有程序與另行授權做的動作,工具只在那兩個動作的前後核對。
工具只呼叫唯讀 git 子命令(`_git` 的白名單是封閉集合,枚舉不比對)。

repo 識別(根 commit + origin)只是**防誤用檢查**,不是安全邊界,也不是授權;
不保證擋住所有下游或刻意複製設定的副本。不論識別結果,每次仍逐項過四項使用前提。

本檔標 skip(只供本專案使用,不出貨到下游):識別值寫死的是這個 repo。

步驟:S0b 快照 → S1 現場兩次取樣 → S2 候選名冊 → S3 證據包(collect);
S4 核准代記(record-approval);S5 登記前重驗(pre-register,含原 verify);
S6' 登記後核對(post-register);S7' 接回後核對與 S8 收尾(post-reattach)。
resume 完全唯讀、不取鎖,依階段核對現場並指出下一步。

用法(經 gatepy):
  sh .claude/bin/gatepy .claude/portable/inventory_evidence.py collect [--repo R] [--claude-root C] [--settle-seconds N]
  sh .claude/bin/gatepy .claude/portable/inventory_evidence.py record-approval --run <代號> --fingerprint <64 碼> --approved-at <ISO 8601> --note <文字>
  sh .claude/bin/gatepy .claude/portable/inventory_evidence.py pre-register --run <代號> [--claude-root C]
  sh .claude/bin/gatepy .claude/portable/inventory_evidence.py post-register --run <代號> [--claude-root C]
  sh .claude/bin/gatepy .claude/portable/inventory_evidence.py post-reattach --run <代號>
  sh .claude/bin/gatepy .claude/portable/inventory_evidence.py resume --run <代號>

退出碼:0 通過;2 使用前提不符;3 不支援狀態(含 submodule、特殊檔案、repo 識別不符);
4 失配或不穩定;5 內部錯誤(不確定一律當失敗)。
"""

import argparse
import hashlib
import importlib.util
import io
import json
import os
import re
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone

FORMAT_VERSION = 1
TOOL_VERSION = "165.2"

# repo 識別值(站一 A4 實讀,物件格式 sha1)。
ROOT_COMMIT = "91335c8e212d21230b03bd26acc04a7e87590f3c"
ORIGIN_URL = "https://github.com/wusuowei-tw/monkeyleash"

EXIT_OK = 0
EXIT_PRECONDITION = 2
EXIT_UNSUPPORTED = 3
EXIT_MISMATCH = 4
EXIT_INTERNAL = 5

EVIDENCE_REL = ".dev/inventory-evidence"
INDEX_NAME = "index.jsonl"
LOCK_NAME = ".lock"
CHECKPOINT_NAME = "checkpoint.jsonl"
TMP_PREFIX = ".tmp-"
INVENTORY_REL = ".agents/extension-inventory.json"
ALLOWLIST_REL = ".agents/extension-allowlist.json"

STEPS = ("S0b", "S1", "S2", "S3", "S4", "S5", "S6'", "S7'", "S8")
STEP_ARTIFACTS = {"S0b": ("snapshot.json",), "S1": ("diff.json",), "S2": ("candidate-inventory.json",),
                  "S3": ("package.json", "summary.md"), "S4": ("approval.json",)}
ARTIFACT_STEP = dict((name, step) for step, names in STEP_ARTIFACTS.items() for name in names)
PACKAGE_ARTIFACTS = ("snapshot.json", "diff.json", "candidate-inventory.json")
RESULT_COMPLETED, RESULT_STOPPED, RESULT_VOID = "completed", "stopped", "approval_void"
RUN_ID_RE = re.compile(r"\A\d{8}T\d{6}Z-[0-9a-f]{7}\Z")
NOTE_PREFIX = "inventory-evidence "
UNCONFIRMED = u"未確認"
UNTRACKED_NOTE = u"未驗證其內容是否改變"
APPROVAL_KEYS = ("format_version", "run_id", "package_fingerprint", "approved_at", "recorded_at",
                 "recorded_by", "statement", "note")
APPROVAL_BY = "agent-proxy"
APPROVAL_STATEMENT = u"代理人代記 Jeff 對此證據包指紋的明確核准；不是獨立人類授權證明"

_ID_LENGTH = {"sha1": 40, "sha256": 64}
_ZERO_MODE = "000000"
_GITLINK = "160000"
_REPARSE_POINT = 0x400
_STATUS = {"A": "added", "M": "modified", "T": "modified", "D": "deleted"}
_EXPECT_SIDES = {"added": (False, True), "deleted": (True, False), "modified": (True, True)}
# 唯讀 git 子命令(封閉集合)。`remote` 只准 `get-url`,`config` 只准 `--get`。
_GIT_READ_ONLY = frozenset(("rev-parse", "rev-list", "remote", "diff", "ls-files", "check-ignore", "config"))
_VIEW_KEYS = ("repo_identity", "head", "state_flags", "staged", "partially_staged", "protected_scope", "policy")
_LABELS = (("added", u"新增"), ("deleted", u"刪除"), ("mismatch", u"內容不符"), ("contract", u"contract"))
_COUNT_KEYS = ("missing", "extra", "mismatch", "structure_errors")
_VOID_ADVICE = u"此核准已不適用;需重新 collect,並重新取得 Jeff 對新證據包的核准"

_REDLIGHT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hooks", "redlight.py")


def _load_redlight():
    """以檔案位置載入 R10 的判定模組。只呼叫它的函式,不改它的任何狀態。"""
    spec = importlib.util.spec_from_file_location("_inventory_evidence_redlight", _REDLIGHT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_rl = _load_redlight()


class Stop(Exception):
    """停下:`code` 是退出碼,`reason` 說明哪一項前提或檢查沒滿足(不帶完整路徑、身分、桶實名)。"""

    def __init__(self, code, reason):
        Exception.__init__(self, reason)
        self.code = code
        self.reason = reason


def _now():
    return datetime.now(timezone.utc)


def _sleep(seconds):
    time.sleep(seconds)


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _write(stream, text):
    try:
        stream.flush()
        stream.buffer.write(text.encode("utf-8"))
        stream.buffer.flush()
    except AttributeError:
        stream.write(text)


def _out(text):
    _write(sys.stdout, text)


def _err(text):
    _write(sys.stderr, u"[inventory_evidence] %s\n" % text)


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _json_bytes(obj):
    return (json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _canonical(obj):
    """鍵名排序、不加多餘空白、UTF-8。"""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def package_fingerprint(pkg):
    """證據包指紋 = package.json 內容的正規序列化之 SHA256(完整 64 碼)。summary.md 不參與。"""
    return _sha256(_canonical(pkg))


def git_blob_id(data, object_format):
    """以不寫入的方式算 git blob ID(等同 `git hash-object --no-filters`,不帶 `-w`)。"""
    h = hashlib.sha1() if object_format == "sha1" else hashlib.sha256()
    h.update(b"blob %d\0" % len(data))
    h.update(data)
    return h.hexdigest()


# ── git(只准唯讀)───────────────────────────────────────────────────────────

def _git(root, args):
    args = list(args)
    sub = args[0] if args else None
    if sub not in _GIT_READ_ONLY or (sub == "remote" and args[1:2] != ["get-url"]) \
            or (sub == "config" and "--get" not in args):
        raise Stop(EXIT_INTERNAL, u"內部錯誤:工具只准唯讀 git 子命令(%s 被拒)" % sub)
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    if sub != "check-ignore":       # check-ignore 不接受 literal pathspec magic(會回 128)
        env["GIT_LITERAL_PATHSPECS"] = "1"
    try:
        return subprocess.run(["git", "-C", os.fspath(root)] + args, capture_output=True, env=env, timeout=120)
    except Exception as e:
        raise Stop(EXIT_INTERNAL, u"git %s 無法執行(%s)" % (sub, type(e).__name__))


def _git_ok(root, args):
    proc = _git(root, args)
    if proc.returncode != 0:
        raise Stop(EXIT_INTERNAL, u"git %s 失敗(退出碼 %d)" % (args[0], proc.returncode))
    return proc.stdout


def _z(raw):
    return [p.decode("utf-8", "surrogateescape") for p in raw.split(b"\0") if p]


def _text(raw):
    return raw.decode("utf-8", "surrogateescape").strip()


def _full_id(value, length, what):
    if not (isinstance(value, str) and len(value) == length and all(c in "0123456789abcdef" for c in value)):
        raise Stop(EXIT_INTERNAL, u"%s 不是完整長度的 ID(期望 %d 碼)" % (what, length))
    return value


def _abs(root, rel):
    return os.path.join(os.fspath(root), *rel.split("/"))


def _is_evidence_path(rel):
    rel = rel.replace("\\", "/")
    return rel == EVIDENCE_REL or rel.startswith(EVIDENCE_REL + "/")


# ── 使用前提與 repo 識別 ──────────────────────────────────────────────────────

def _toplevel(root):
    if not os.path.isdir(root):
        raise Stop(EXIT_PRECONDITION, u"使用前提不符:指定的 repo 位置不是目錄")
    proc = _git(root, ["rev-parse", "--show-toplevel"])
    if proc.returncode != 0:
        raise Stop(EXIT_PRECONDITION, u"使用前提不符:指定位置不是 git 工作樹")
    top = _text(proc.stdout)
    if os.path.normcase(os.path.realpath(top)) != os.path.normcase(os.path.realpath(root)):
        raise Stop(EXIT_PRECONDITION, u"使用前提不符:指定位置不是 git 工作樹的最上層")


def _check_chain(root, rel):
    """前提 (d):從 `.dev/` 到 `rel` 每一層都不是 symlink/junction/reparse point。
    目標不存在時,檢查到第一個不存在的那一層為止(之前的都是已存在的父目錄)。"""
    parts = rel.split("/")
    for i in range(1, len(parts) + 1):
        sub = "/".join(parts[:i])
        try:
            st = os.lstat(_abs(root, sub))
        except FileNotFoundError:
            return
        except OSError as e:
            raise Stop(EXIT_PRECONDITION, u"使用前提(d)不符:%s 無法檢查(%s)" % (sub, type(e).__name__))
        if stat.S_ISLNK(st.st_mode) or (getattr(st, "st_file_attributes", 0) & _REPARSE_POINT):
            raise Stop(EXIT_PRECONDITION, u"使用前提(d)不符:%s 是 symlink/junction/reparse point" % sub)
        if not stat.S_ISDIR(st.st_mode):
            raise Stop(EXIT_PRECONDITION, u"使用前提(d)不符:%s 不是目錄" % sub)


def check_preconditions(root, write_rel=None):
    """四項使用前提。任一不符 ⇒ Stop(2),不寫入。`write_rel` 是本次要寫的最深位置。"""
    # 檢查順序 (d)(b)(c)(a):目錄下有已追蹤檔時 git 也會把該位置判成「未忽略」,
    # 先判 (b)(c) 訊息才指得出真正的原因。四項仍全部要過。
    _check_chain(root, write_rel or EVIDENCE_REL)
    if _z(_git_ok(root, ["ls-files", "-z", "--", EVIDENCE_REL])):
        raise Stop(EXIT_PRECONDITION, u"使用前提(b)不符:證據目錄下有已追蹤檔")
    if _z(_git_ok(root, ["diff", "--cached", "--name-only", "-z", "--", EVIDENCE_REL])):
        raise Stop(EXIT_PRECONDITION, u"使用前提(c)不符:證據目錄下有待提交項目")
    for rel in (EVIDENCE_REL, EVIDENCE_REL + "/" + INDEX_NAME, write_rel or EVIDENCE_REL):
        proc = _git(root, ["check-ignore", "-q", "--", rel])
        if proc.returncode == 1:
            raise Stop(EXIT_PRECONDITION, u"使用前提(a)不符:寫入位置 %s 沒有被 git 忽略" % rel)
        if proc.returncode != 0:
            raise Stop(EXIT_INTERNAL, u"git check-ignore 失敗(退出碼 %d)" % proc.returncode)


def _head(root, length):
    proc = _git(root, ["rev-parse", "--verify", "-q", "HEAD"])
    if proc.returncode != 0:
        raise Stop(EXIT_UNSUPPORTED, u"不支援的狀態:HEAD 不存在")
    return _full_id(_text(proc.stdout), length, u"HEAD")


def _identity(root):
    fmt = _text(_git_ok(root, ["rev-parse", "--show-object-format"]))
    if fmt not in _ID_LENGTH:
        raise Stop(EXIT_INTERNAL, u"不認得的物件格式")
    length = _ID_LENGTH[fmt]
    head = _head(root, length)
    roots = _text(_git_ok(root, ["rev-list", "--max-parents=0", "HEAD"])).split()
    for r in roots:
        _full_id(r, length, u"根 commit")
    if roots != [ROOT_COMMIT]:
        raise Stop(EXIT_UNSUPPORTED, u"repo 識別不符:根 commit 不相符或不只一個(防誤用檢查,不是授權)")
    proc = _git(root, ["remote", "get-url", "origin"])
    origin = _text(proc.stdout) if proc.returncode == 0 else None
    if origin != ORIGIN_URL:
        raise Stop(EXIT_UNSUPPORTED, u"repo 識別不符:origin 不存在或不相符(防誤用檢查,不是授權)")
    branch = _text(_git_ok(root, ["rev-parse", "--abbrev-ref", "HEAD"]))
    return {"root_commit": roots[0], "origin": origin, "object_format": fmt, "id_length": length,
            "head": head, "branch": None if branch == "HEAD" else branch}


# ── 快照(S0b)────────────────────────────────────────────────────────────────

def _ls_stage(root, paths=None):
    """`git ls-files -s -z [-- paths]` → `[(path, mode, blob, stage)]`。"""
    args = ["ls-files", "-s", "-z"] + (["--"] + list(paths) if paths else [])
    out = []
    for rec in _z(_git_ok(root, args)):
        meta, _, path = rec.partition("\t")
        parts = meta.split(" ")
        if len(parts) != 3 or not path:
            raise Stop(EXIT_INTERNAL, u"git ls-files -s 輸出格式不符")
        out.append((path, parts[0], parts[1], parts[2]))
    return out


def state_flags(root):
    gitdir = _text(_git_ok(root, ["rev-parse", "--absolute-git-dir"]))
    has = lambda name: os.path.lexists(os.path.join(gitdir, name))
    conflicts = sorted(set(path for path, _m, _b, stage in _ls_stage_unmerged(root)))
    return {"merge": has("MERGE_HEAD"), "rebase": has("rebase-merge") or has("rebase-apply"),
            "cherry_pick": has("CHERRY_PICK_HEAD"), "revert": has("REVERT_HEAD"), "conflict_paths": conflicts}


def _ls_stage_unmerged(root):
    out = []
    for rec in _z(_git_ok(root, ["ls-files", "-u", "-z"])):
        meta, _, path = rec.partition("\t")
        parts = meta.split(" ")
        out.append((path, parts[0] if parts else "", parts[1] if len(parts) > 1 else "",
                    parts[2] if len(parts) > 2 else ""))
    return out


def _refuse_unsupported_state(root, flags):
    busy = [name for name in ("merge", "rebase", "cherry_pick", "revert") if flags[name]]
    if busy:
        raise Stop(EXIT_UNSUPPORTED, u"不支援的狀態:%s 進行中" % "、".join(busy))
    if flags["conflict_paths"]:
        raise Stop(EXIT_UNSUPPORTED, u"不支援的狀態:有 %d 個衝突路徑" % len(flags["conflict_paths"]))
    if _z(_git_ok(root, ["diff", "--name-only", "-z", "--", INVENTORY_REL, ALLOWLIST_REL])):
        raise Stop(EXIT_UNSUPPORTED, u"不支援的狀態:名冊或 allowlist 有未暫存修改")
    if _z(_git_ok(root, ["diff", "--cached", "--name-only", "-z", "--", INVENTORY_REL, ALLOWLIST_REL])):
        raise Stop(EXIT_UNSUPPORTED, u"不支援的狀態:名冊或 allowlist 在待提交區有變更")


def _cached_raw(root):
    return _git_ok(root, ["diff", "--cached", "--raw", "-z", "--no-renames", "--no-abbrev"])


def _side(mode, oid, length):
    if not re.fullmatch(r"[0-7]{6}", mode):
        raise Stop(EXIT_INTERNAL, u"待提交項目的模式格式不符")
    _full_id(oid, length, u"blob ID")
    zero_mode, zero_id = mode == _ZERO_MODE, oid == "0" * length
    if zero_mode != zero_id:
        raise Stop(EXIT_INTERNAL, u"待提交項目的模式與 ID 只有一個是零值")
    if zero_mode:
        return {"exists": False}
    return {"exists": True, "mode": mode, "blob": oid}


def parse_cached_raw(raw, length):
    """`git diff --raw -z --no-renames --no-abbrev`(`--cached` 或兩個 commit 之間)→ 項目清單。

    零值(全零、完整長度)是「這一端不存在」的標記:記成 `{"exists": False}`,不當 blob。
    零值出現在與狀態不符的一端、兩端皆零、模式與 ID 只有一個是零值、ID 不是完整長度 ⇒ Stop(5)。
    """
    toks = raw.split(b"\0")
    if toks and toks[-1] == b"":
        toks.pop()
    if len(toks) % 2:
        raise Stop(EXIT_INTERNAL, u"git diff --raw 輸出不完整")
    out = []
    for i in range(0, len(toks), 2):
        parts = toks[i].decode("ascii", "replace").split(" ")
        if len(parts) != 5 or not parts[0].startswith(":"):
            raise Stop(EXIT_INTERNAL, u"git diff --raw 輸出格式不符")
        src_mode, dst_mode, src_id, dst_id, status = parts[0][1:], parts[1], parts[2], parts[3], parts[4]
        if status not in _STATUS:
            raise Stop(EXIT_INTERNAL, u"不支援的待提交狀態 %s" % status)
        kind = _STATUS[status]
        head, index = _side(src_mode, src_id, length), _side(dst_mode, dst_id, length)
        if (head["exists"], index["exists"]) != _EXPECT_SIDES[kind]:
            raise Stop(EXIT_INTERNAL, u"零值 ID 出現在與狀態不符的一端(狀態 %s)" % kind)
        out.append({"path": toks[i + 1].decode("utf-8", "surrogateescape"), "status": kind,
                    "head": head, "index": index})
    return out


def _exec_reliable(root):
    """可執行模式能否可靠辨識:只在 posix 且 core.filemode 不是 false 時為真。"""
    if os.name != "posix":
        return False
    proc = _git(root, ["config", "--get", "core.filemode"])
    return _text(proc.stdout).lower() != "false"


def _worktree_state(root, rel, reliable):
    path = _abs(root, rel)
    try:
        st = os.lstat(path)
    except FileNotFoundError:
        return {"path": rel, "exists": False}
    except OSError as e:
        raise Stop(EXIT_INTERNAL, u"待保護範圍內有路徑無法檢查(%s)" % type(e).__name__)
    if stat.S_ISLNK(st.st_mode):
        target = os.readlink(path)
        return {"path": rel, "exists": True, "type": "link", "link_target_sha256": _sha256(os.fsencode(target))}
    if getattr(st, "st_file_attributes", 0) & _REPARSE_POINT:
        raise Stop(EXIT_UNSUPPORTED, u"不支援的狀態:待保護範圍內有 reparse point(不是 symlink)")
    if stat.S_ISDIR(st.st_mode):
        raise Stop(EXIT_UNSUPPORTED, u"不支援的狀態:待保護範圍內有該是檔案的位置是目錄")
    if not stat.S_ISREG(st.st_mode):
        raise Stop(EXIT_UNSUPPORTED, u"不支援的狀態:待保護範圍內有特殊檔案(FIFO/裝置/socket)")
    with io.open(path, "rb") as fh:
        data = fh.read()
    return {"path": rel, "exists": True, "type": "file", "sha256": _sha256(data),
            "executable": bool(st.st_mode & 0o111) if reliable else UNCONFIRMED}


def _policy_ids(root, rel, length, worktree):
    proc = _git(root, ["rev-parse", "--verify", "-q", "HEAD:" + rel])
    head_blob = _full_id(_text(proc.stdout), length, u"名冊 HEAD blob") if proc.returncode == 0 else None
    rows = _ls_stage(root, [rel])
    index_blob = _full_id(rows[0][2], length, u"名冊 index blob") if rows else None
    return {"path": rel, "head_blob": head_blob, "index_blob": index_blob,
            "worktree_sha256": worktree.get("sha256") if worktree.get("type") == "file" else None}


def build_snapshot(root, ident):
    """S0b 的內容(不寫入)。不支援的狀態在這裡就 Stop(3),什麼都還沒寫。"""
    flags = state_flags(root)
    _refuse_unsupported_state(root, flags)
    length = ident["id_length"]
    staged = [s for s in parse_cached_raw(_cached_raw(root), length) if not _is_evidence_path(s["path"])]
    for s in staged:
        if _GITLINK in (s["head"].get("mode"), s["index"].get("mode")):
            raise Stop(EXIT_UNSUPPORTED, u"不支援的狀態:待提交項目含 submodule(160000)")
    staged_paths = set(s["path"] for s in staged)
    modified = set(p for p in _z(_git_ok(root, ["diff", "--name-only", "-z"])) if not _is_evidence_path(p))
    partial = []
    for p in sorted(staged_paths & modified):
        for path, mode, blob, stage in _ls_stage(root, [p]):
            if path == p:
                partial.append({"path": p, "mode": mode, "blob": _full_id(blob, length, u"部分暫存 blob")})
    scope = sorted(staged_paths | modified | {INVENTORY_REL, ALLOWLIST_REL})
    for path, mode, _blob, _stage in _ls_stage(root, scope):
        if mode == _GITLINK:
            raise Stop(EXIT_UNSUPPORTED, u"不支援的狀態:待保護範圍含 submodule(160000)")
    reliable = _exec_reliable(root)
    protected = [_worktree_state(root, p, reliable) for p in scope]
    by_path = dict((e["path"], e) for e in protected)
    return {
        "repo_identity": {"root_commit": ident["root_commit"], "origin": ident["origin"],
                          "object_format": ident["object_format"], "id_length": length},
        "head": {"commit": ident["head"], "branch": ident["branch"]},
        "state_flags": flags,
        "staged": staged,
        "partially_staged": partial,
        "policy": {"inventory": _policy_ids(root, INVENTORY_REL, length, by_path[INVENTORY_REL]),
                   "allowlist": _policy_ids(root, ALLOWLIST_REL, length, by_path[ALLOWLIST_REL])},
        "protected_scope": protected,
        "executable_mode_reliable": reliable,
        "untracked": _untracked_record(_untracked(root)),
    }


def _untracked(root):
    return sorted(p for p in _z(_git_ok(root, ["ls-files", "-o", "--exclude-standard", "-z"]))
                  if not _is_evidence_path(p))


def _untracked_record(paths):
    return {"count": len(paths), "paths": paths, "content_verified": False, "note": UNTRACKED_NOTE}


def state_view(snap):
    return dict((k, snap.get(k)) for k in _VIEW_KEYS)


# ── 現場取樣與分類(S1)──────────────────────────────────────────────────────

def _extension_report(root, claude_root):
    return _rl.extension_report(os.fspath(root), claude_root=claude_root)


def _contract_resolver(claude_root):
    def resolve(path, contract):
        real = _rl._synced_contract_real_path(claude_root, path)
        if real is None:
            return False, None
        return True, _rl.synced_contract_check(contract["name"], real, contract["pins"])
    return resolve


def classify(entries, synced_files, resolve_contract):
    """名冊 entries 對現場 synced_files 逐項分類。

    算法與 `synced_verification` 的計數同一套(額外 / 缺少 / 內容不符),但逐項列出:
    `differences` 的類別是 added / deleted / mismatch / contract;現場值讀不到、契約檔實際
    路徑解析不了 ⇒ `unclassified`。`counts` 供交叉核對。
    """
    want = dict((e["path"], e) for e in entries)
    have = dict((p, s) for p, s in synced_files)
    diffs, contracts, unclassified = [], [], []
    counts = {"extra": 0, "missing": 0, "mismatch": 0}
    for p in sorted(set(want) | set(have)):
        e = want.get(p)
        if e is None:
            counts["extra"] += 1
            if have[p] is None:
                unclassified.append({"path": p, "why": "live_unreadable"})
            else:
                diffs.append({"category": "added", "path": p, "inventory_value": None, "live_value": have[p]})
            continue
        if "contract" in e:
            name = e["contract"]["name"]
            if p not in have:
                counts["missing"] += 1
                code = {"category": "contract_read", "field": "missing"}
                contracts.append({"path": p, "name": name, "present": False, "result": code})
                diffs.append({"category": "contract", "path": p, "inventory_value": e["contract"],
                              "live_value": code})
                continue
            resolved, code = resolve_contract(p, e["contract"])
            if not resolved:
                unclassified.append({"path": p, "why": "contract_path_unresolved"})
                continue
            contracts.append({"path": p, "name": name, "present": True, "result": code})
            if code is not None:
                counts["mismatch"] += 1
                diffs.append({"category": "contract", "path": p, "inventory_value": e["contract"],
                              "live_value": code})
            continue
        if p not in have:
            counts["missing"] += 1
            diffs.append({"category": "deleted", "path": p, "inventory_value": e["sha256"], "live_value": None})
        elif have[p] is None:
            counts["mismatch"] += 1
            unclassified.append({"path": p, "why": "live_unreadable"})
        elif have[p] != e["sha256"]:
            counts["mismatch"] += 1
            diffs.append({"category": "mismatch", "path": p, "inventory_value": e["sha256"],
                          "live_value": have[p]})
    return {"differences": diffs, "contracts": contracts, "unclassified": unclassified, "counts": counts}


def cross_check(counts, synced, structure_errors):
    """逐項分類的少 / 多 / 不符 / 結構錯誤數,必須與同一次 `synced_verification` 的計數完全相同。
    相符只代表數量一致,不代表逐項分類一定正確。"""
    mine = (counts["missing"], counts["extra"], counts["mismatch"], structure_errors)
    theirs = tuple(synced.get(k) for k in _COUNT_KEYS) if isinstance(synced, dict) else None
    if mine != theirs:
        raise Stop(EXIT_MISMATCH, u"交叉核對不符:逐項分類(少 %d／多 %d／不符 %d／結構錯誤 %d)與 R10 計數不同;"
                                  u"視為無法分類" % mine)


def sample(root, claude_root):
    """一次現場取樣:真實 R10 觀測 + 逐項分類。名冊狀態不是 ok ⇒ Stop(4)。"""
    report = _extension_report(root, claude_root)
    inv = report.get("inventory")
    state = inv.get("state") if isinstance(inv, dict) else None
    if state != "ok":
        raise Stop(EXIT_MISMATCH, u"名冊狀態不是 ok(%s);無法分類" % (state or report.get("observation")))
    surfaces = report.get("surfaces") or {}
    structure = [e for e in (surfaces.get("errors") or []) if e and e[0] == "synced"]
    live = sorted(surfaces.get("synced_files") or [], key=lambda item: item[0])
    cls = classify(inv["policy"]["entries"], live, _contract_resolver(report.get("claude_root")))
    for _e in structure:
        cls["unclassified"].append({"path": None, "why": "synced_structure"})
    return {"time": _iso(_now()), "r10_state": report.get("state"),
            "live": [{"path": p, "sha256": s} for p, s in live], "contracts": cls["contracts"],
            "classification": cls, "synced": report.get("synced"), "structure_errors": len(structure),
            "inventory": inv["policy"], "inventory_blob": inv.get("blob")}


def _sample_key(s):
    return (s["live"], s["contracts"], s["r10_state"], s["classification"]["differences"])


def _sample_record(s):
    synced = s["synced"] if isinstance(s["synced"], dict) else {}
    return {"time": s["time"], "r10_state": s["r10_state"], "live": s["live"], "contracts": s["contracts"],
            "counts": {"classification": s["classification"]["counts"],
                       "r10": dict((k, synced.get(k)) for k in _COUNT_KEYS)}}


def _binding(record):
    """樣本的綁定資料:每項路徑、內容指紋、contract 結果、R10 狀態與計數。取樣時間不屬綁定資料。"""
    return dict((k, record.get(k)) for k in ("live", "contracts", "r10_state", "counts"))


# ── 寫檔(暫存檔 → 改名;不覆寫)與 JSONL ───────────────────────────────────

def _publish(tmp, final):
    """暫存檔 → 正式檔名。正式檔名已存在 ⇒ Stop(4),不覆寫(`os.link` 本身就不覆寫)。"""
    try:
        os.link(tmp, final)
    except FileExistsError:
        raise Stop(EXIT_MISMATCH, u"原件 %s 已存在;不覆寫" % os.path.basename(final))
    except OSError as e:
        raise Stop(EXIT_INTERNAL, u"原件 %s 改名失敗(%s)" % (os.path.basename(final), type(e).__name__))
    os.unlink(tmp)


def _write_artifact(ctx, name, data):
    final = os.path.join(ctx["run_dir"], name)
    if os.path.lexists(final):
        raise Stop(EXIT_MISMATCH, u"原件 %s 已存在;不覆寫" % name)
    tmp = os.path.join(ctx["run_dir"], TMP_PREFIX + name)
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o644)
    with os.fdopen(fd, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    _publish(tmp, final)
    return _sha256(data)


def _read_jsonl(path, label):
    """讀 JSONL:任何一行不是完整 JSON 物件,或最後一個字元不是換行 ⇒ Stop(4),不修補。"""
    try:
        with io.open(path, "rb") as fh:
            data = fh.read()
    except FileNotFoundError:
        return []
    if not data:
        return []
    if not data.endswith(b"\n"):
        raise Stop(EXIT_MISMATCH, u"%s 最後一行不完整(不以換行結尾);視為壞資料,不修補" % label)
    out = []
    for n, line in enumerate(data[:-1].split(b"\n"), 1):
        try:
            rec = json.loads(line.decode("utf-8"))
        except Exception:
            rec = None
        if not isinstance(rec, dict):
            raise Stop(EXIT_MISMATCH, u"%s 第 %d 行不是完整 JSON;視為壞資料,不修補" % (label, n))
        out.append(rec)
    return out


def _append_jsonl(path, rec, label):
    _read_jsonl(path, label)        # 尾行不完整就不接著寫
    line = (json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    with io.open(path, "ab") as fh:
        fh.write(line)
        fh.flush()
        os.fsync(fh.fileno())


def _event(ctx, step, result, reason, fingerprints, detail=None):
    rec = {"time": _iso(_now()), "run_id": ctx["run_id"], "step": step, "result": result,
           "reason": reason, "fingerprints": fingerprints or {}}
    if detail is not None:
        rec["detail"] = detail
    _append_jsonl(os.path.join(ctx["run_dir"], CHECKPOINT_NAME), rec, CHECKPOINT_NAME)


def _index(ctx, event, reason=None, fingerprint=None, extra=None):
    rec = {"time": _iso(_now()), "run_id": ctx["run_id"], "event": event, "reason": reason,
           "package_fingerprint": fingerprint}
    rec.update(extra or {})
    _append_jsonl(os.path.join(ctx["evid"], INDEX_NAME), rec, INDEX_NAME)


def _load(run_dir, name):
    try:
        with io.open(os.path.join(run_dir, name), "rb") as fh:
            return json.loads(fh.read().decode("utf-8"))
    except Exception:
        raise Stop(EXIT_MISMATCH, u"%s 無法解析" % name)


# ── 全域鎖 ────────────────────────────────────────────────────────────────────

_LOCK_HELD = u"全域鎖已存在(並行執行中或前次遺留);不刪除、不接續,請人工確認後處理"


def _acquire_lock(evid, run_id):
    path = os.path.join(evid, LOCK_NAME)
    content = _canonical({"pid": os.getpid(), "run_id": run_id, "started": _iso(_now())}) + b"\n"
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o644)
    except FileExistsError:
        raise Stop(EXIT_MISMATCH, _LOCK_HELD)
    with os.fdopen(fd, "wb") as fh:
        fh.write(content)
    return path, content


def _release_lock(path, content):
    """只刪內容與自己相符的鎖。回傳是否刪了。"""
    try:
        with io.open(path, "rb") as fh:
            current = fh.read()
    except FileNotFoundError:
        return False
    if current != content:
        return False
    os.unlink(path)
    return True


# ── 既有證據的掃描與重驗 ──────────────────────────────────────────────────────

def scan_evidence(evid, holding_lock):
    """未完成資料、遺留鎖、壞 JSONL、不認得的項目 ⇒ Stop,不自動清理。"""
    if not os.path.isdir(evid):
        return
    for name in sorted(os.listdir(evid)):
        full = os.path.join(evid, name)
        if name == LOCK_NAME:
            if holding_lock:
                continue
            raise Stop(EXIT_MISMATCH, _LOCK_HELD)
        if name == INDEX_NAME:
            _read_jsonl(full, INDEX_NAME)
            continue
        st = os.lstat(full)
        if stat.S_ISLNK(st.st_mode) or (getattr(st, "st_file_attributes", 0) & _REPARSE_POINT):
            raise Stop(EXIT_PRECONDITION, u"使用前提(d)不符:證據目錄內有 symlink/junction/reparse point")
        if not RUN_ID_RE.match(name) or not stat.S_ISDIR(st.st_mode):
            raise Stop(EXIT_MISMATCH, u"證據目錄內有不認得的項目;不自動清理")
        _scan_run(full, name)


def _scan_run(run_dir, run_id):
    files = os.listdir(run_dir)
    if any(f.startswith(TMP_PREFIX) for f in files):
        raise Stop(EXIT_MISMATCH, u"執行 %s 留有暫存檔(未完成資料);不自動清理" % run_id)
    events = _read_jsonl(os.path.join(run_dir, CHECKPOINT_NAME), CHECKPOINT_NAME)
    done = set(e.get("step") for e in events if e.get("result") == RESULT_COMPLETED)
    for f in sorted(files):
        if f == CHECKPOINT_NAME:
            continue
        step = ARTIFACT_STEP.get(f)
        if step is None:
            raise Stop(EXIT_MISMATCH, u"執行 %s 有不認得的檔案;不自動清理" % run_id)
        if step not in done:
            raise Stop(EXIT_MISMATCH, u"執行 %s 的 %s 存在但沒有對應的完成事件(未完成資料)" % (run_id, f))


def _file_sha(path):
    with io.open(path, "rb") as fh:
        return _sha256(fh.read())


def _is_full_hex(value):
    return isinstance(value, str) and len(value) in _ID_LENGTH.values() \
        and all(c in "0123456789abcdef" for c in value)


def verify_run(evid, run_id):
    """重驗保存的證據本身:原件 SHA256、證據包指紋、摘要、approval.json、事件順序與一致性。

    任一不符 ⇒ Stop(4),不覆寫、不修補。回傳本執行的狀態摘要(`info`)。
    """
    run_dir = os.path.join(evid, run_id)
    events = _read_jsonl(os.path.join(run_dir, CHECKPOINT_NAME), CHECKPOINT_NAME)
    for e in events:
        if e.get("run_id") != run_id:
            raise Stop(EXIT_MISMATCH, u"事件的執行代號與目錄不符")
        if e.get("result") not in (RESULT_COMPLETED, RESULT_STOPPED, RESULT_VOID):
            raise Stop(EXIT_MISMATCH, u"事件結果欄不認得")
    completed = [e for e in events if e.get("result") == RESULT_COMPLETED]
    steps = [e.get("step") for e in completed]
    if steps != list(STEPS[:len(steps)]):
        raise Stop(EXIT_MISMATCH, u"完成事件順序不符(跳步、重複或倒序)")
    by_step = dict((e["step"], e) for e in completed)
    for e in completed:
        recorded = e.get("fingerprints") or {}
        for name in STEP_ARTIFACTS.get(e["step"], ()):
            path = os.path.join(run_dir, name)
            if not os.path.isfile(path):
                raise Stop(EXIT_MISMATCH, u"%s 有完成事件,但原件 %s 不存在" % (e["step"], name))
            if recorded.get(name) != _file_sha(path):
                raise Stop(EXIT_MISMATCH, u"原件 %s 的 SHA256 與完成事件不符" % name)
    mine = [r for r in _read_jsonl(os.path.join(evid, INDEX_NAME), INDEX_NAME) if r.get("run_id") == run_id]
    if not any(r.get("event") == "start" for r in mine):
        raise Stop(EXIT_MISMATCH, u"index.jsonl 沒有本執行的開始紀錄")
    done = [r for r in mine if r.get("event") == "collect_completed"]
    fp = None
    if "S3" in steps:
        pkg = _load(run_dir, "package.json")
        fp = package_fingerprint(pkg)
        if fp != (by_step["S3"].get("fingerprints") or {}).get("package_fingerprint"):
            raise Stop(EXIT_MISMATCH, u"依 package.json 重算的證據包指紋與 S3 完成事件不符")
        if len(done) != 1 or done[0].get("package_fingerprint") != fp:
            raise Stop(EXIT_MISMATCH, u"index.jsonl 的 collect 完成紀錄與 S3 完成事件不符")
        arts = pkg.get("artifacts") if isinstance(pkg, dict) else None
        for name in PACKAGE_ARTIFACTS:
            if not isinstance(arts, dict) or arts.get(name) != _file_sha(os.path.join(run_dir, name)):
                raise Stop(EXIT_MISMATCH, u"package.json 記錄的 %s SHA256 與實際不符" % name)
        for e in completed[3:]:
            if (e.get("fingerprints") or {}).get("package_fingerprint") != fp:
                raise Stop(EXIT_MISMATCH, u"%s 完成事件的證據包指紋與證據包不符" % e["step"])
    elif done:
        raise Stop(EXIT_MISMATCH, u"index.jsonl 有 collect 完成紀錄,但 checkpoint 沒有 S3 完成事件")
    for r in mine:
        if r.get("package_fingerprint") is not None and r.get("package_fingerprint") != fp:
            raise Stop(EXIT_MISMATCH, u"index.jsonl 紀錄的證據包指紋與證據包不符")
    approval_sha = None
    if "S4" in steps:
        approval_sha = _file_sha(os.path.join(run_dir, "approval.json"))
        doc = _load(run_dir, "approval.json")
        if not isinstance(doc, dict) or set(doc) != set(APPROVAL_KEYS) or doc.get("run_id") != run_id \
                or doc.get("package_fingerprint") != fp or doc.get("recorded_by") != APPROVAL_BY \
                or doc.get("statement") != APPROVAL_STATEMENT:
            raise Stop(EXIT_MISMATCH, u"approval.json 內容不完整或與證據包不符")
    voids = [e for e in events if e.get("result") == RESULT_VOID]
    for v in voids:
        if "S4" not in steps or len(steps) > STEPS.index("S4") + 1:
            raise Stop(EXIT_MISMATCH, u"核准不適用事件與完成步驟矛盾")
        fps = v.get("fingerprints") or {}
        if fps.get("package_fingerprint") != fp or fps.get("approval.json") != approval_sha:
            raise Stop(EXIT_MISMATCH, u"核准不適用事件的指紋與證據包或 approval.json 不符")
    s6_head = None
    if "S6'" in steps:
        s6_head = (by_step["S6'"].get("detail") or {}).get("new_head")
        if not _is_full_hex(s6_head):
            raise Stop(EXIT_MISMATCH, u"S6' 完成事件沒有完整的新 HEAD")
    s8 = (by_step["S8"].get("detail") or {}) if "S8" in steps else None
    if s8 is not None and (s8.get("run_id"), s8.get("package_fingerprint"), s8.get("new_head")) != (run_id, fp, s6_head):
        raise Stop(EXIT_MISMATCH, u"S8 收尾事件與證據包或 S6' 不一致")
    finals = [r for r in mine if r.get("event") == "run_completed"]
    if len(finals) > 1:
        raise Stop(EXIT_MISMATCH, u"index.jsonl 有重複的全域完成紀錄")
    if finals:
        if s8 is None:
            raise Stop(EXIT_MISMATCH, u"index.jsonl 有全域完成紀錄,但 checkpoint 沒有 S8 收尾事件")
        if (finals[0].get("package_fingerprint"), finals[0].get("new_head")) != (s8.get("package_fingerprint"),
                                                                               s8.get("new_head")):
            raise Stop(EXIT_MISMATCH, u"S8 收尾事件與全域完成紀錄不一致(證據包指紋或新 HEAD)")
    last_done = max([i for i, e in enumerate(events) if e.get("result") == RESULT_COMPLETED] or [-1])
    return {"steps": steps, "last": steps[-1] if steps else None, "fp": fp, "by_step": by_step,
            "voids": voids, "approval_sha": approval_sha, "s6_head": s6_head, "s8": s8,
            "final_recorded": bool(finals),
            "stopped_after": [e for e in events[last_done + 1:] if e.get("result") == RESULT_STOPPED]}


# ── collect 的步驟 ────────────────────────────────────────────────────────────

def step_s0b(ctx, core):
    snap = dict(core)
    snap.update({"format_version": FORMAT_VERSION, "run_id": ctx["run_id"], "tool_version": TOOL_VERSION,
                 "created_at": _iso(_now())})
    digest = _write_artifact(ctx, "snapshot.json", _json_bytes(snap))
    _event(ctx, "S0b", RESULT_COMPLETED, None, {"snapshot.json": digest})
    ctx["snapshot"] = snap
    ctx["sha"] = {"snapshot.json": digest}


def _sample_problems(s):
    """一次樣本本身的問題(無法分類、contract 失敗、交叉核對)→ 原因文字或 None。"""
    if s["classification"]["unclassified"]:
        return u"有 %d 項無法分類" % len(s["classification"]["unclassified"])
    failed = sorted(set(u"%s/%s" % (c["result"]["category"], c["result"]["field"])
                        for c in s["contracts"] if c["result"] is not None))
    if failed:
        return u"contract 驗證失敗(%s)" % u"、".join(failed)
    try:
        cross_check(s["classification"]["counts"], s["synced"], s["structure_errors"])
    except Stop as e:
        return e.reason
    return None


def step_s1(ctx):
    first = sample(ctx["root"], ctx["claude_root"])
    _sleep(ctx["settle"])
    second = sample(ctx["root"], ctx["claude_root"])
    head_blob = ctx["snapshot"]["policy"]["inventory"]["head_blob"]
    for s in (first, second):
        if s["inventory_blob"] != head_blob:
            raise Stop(EXIT_MISMATCH, u"R10 讀到的名冊與快照的 HEAD 端不符")
        problem = _sample_problems(s)
        if problem:
            raise Stop(EXIT_MISMATCH, u"%s;不產生候選與證據包" % problem)
    if _sample_key(first) != _sample_key(second):
        raise Stop(EXIT_MISMATCH, u"兩次樣本不同(stable 為假);不產生候選")
    doc = {"format_version": FORMAT_VERSION, "run_id": ctx["run_id"], "settle_seconds": ctx["settle"],
           "samples": [_sample_record(first), _sample_record(second)], "stable": True,
           "differences": second["classification"]["differences"], "unclassified": []}
    digest = _write_artifact(ctx, "diff.json", _json_bytes(doc))
    _event(ctx, "S1", RESULT_COMPLETED, None, {"diff.json": digest})
    ctx["sha"]["diff.json"] = digest
    ctx["sample"] = second


def build_candidate(inventory, differences, run_id):
    """候選名冊全文:只動差異項;contract 項原樣保留;新增或更新項目的 note = `inventory-evidence <執行代號>`。"""
    note = NOTE_PREFIX + run_id
    by_path = dict((d["path"], d) for d in differences)
    entries = []
    for e in inventory["entries"]:
        d = by_path.get(e["path"])
        if "contract" in e or d is None:
            entries.append(e)
        elif d["category"] == "mismatch":
            entries.append({"path": e["path"], "sha256": d["live_value"], "note": note})
        elif d["category"] != "deleted":
            entries.append(e)
    for d in sorted((d for d in differences if d["category"] == "added"), key=lambda d: d["path"]):
        entries.append({"path": d["path"], "sha256": d["live_value"], "note": note})
    out = dict(inventory)
    out["entries"] = entries
    return out


def step_s2(ctx):
    s = ctx["sample"]
    cand = build_candidate(s["inventory"], s["classification"]["differences"], ctx["run_id"])
    if _rl.extension_inventory_check(cand) is not None:
        raise Stop(EXIT_INTERNAL, u"候選名冊不合名冊 schema")
    data = _json_bytes(cand)
    digest = _write_artifact(ctx, "candidate-inventory.json", data)
    blob = git_blob_id(data, ctx["ident"]["object_format"])
    _event(ctx, "S2", RESULT_COMPLETED, None, {"candidate-inventory.json": digest, "candidate_blob": blob})
    ctx["sha"]["candidate-inventory.json"] = digest
    ctx["candidate"] = {"blob": blob, "sha256": digest}


def _mask(path):
    return path.split("/", 1)[0] + u"/…"


def render_summary(differences, fingerprint, untracked_count):
    """衍生呈現,不參與指紋:各類別數量、遮罩後的項目、完整證據包指紋。不含其他完整雜湊、
    完整路徑、身分、桶實名。"""
    counts = dict((key, len([d for d in differences if d["category"] == key])) for key, _l in _LABELS)
    lines = [u"# inventory evidence 摘要", u"", u"- 證據包指紋:%s" % fingerprint,
             u"- " + u" / ".join(u"%s %d" % (label, counts[key]) for key, label in _LABELS),
             u"- 未追蹤檔內容未驗證(共 %d 個;只記數量與清單,不納入指紋)" % untracked_count,
             u"", u"## 項目(遮罩後)", u""]
    labels = dict(_LABELS)
    if not differences:
        lines.append(u"(無差異)")
    for n, d in enumerate(differences, 1):
        lines.append(u"%d. %s:%s" % (n, labels[d["category"]], _mask(d["path"])))
    return u"\n".join(lines) + u"\n"


def step_s3(ctx):
    snap, ident, s = ctx["snapshot"], ctx["ident"], ctx["sample"]
    diffs = s["classification"]["differences"]
    pkg = {
        "format_version": FORMAT_VERSION, "run_id": ctx["run_id"], "tool_version": TOOL_VERSION,
        "created_at": _iso(_now()),
        "repo_identity": {"root_commit": ident["root_commit"], "origin": ident["origin"],
                          "object_format": ident["object_format"]},
        "baseline": {"head": ident["head"], "inventory_head_blob": snap["policy"]["inventory"]["head_blob"],
                     "allowlist_head_blob": snap["policy"]["allowlist"]["head_blob"],
                     "inventory_schema_version": s["inventory"]["version"]},
        "candidate": ctx["candidate"],
        "differences": diffs,
        "settle_seconds": ctx["settle"],
        "artifacts": dict((name, ctx["sha"][name]) for name in PACKAGE_ARTIFACTS),
    }
    pkg_sha = _write_artifact(ctx, "package.json", _canonical(pkg))
    fp = package_fingerprint(pkg)
    summary = render_summary(diffs, fp, snap["untracked"]["count"]).encode("utf-8")
    sum_sha = _write_artifact(ctx, "summary.md", summary)
    _event(ctx, "S3", RESULT_COMPLETED, None, {"package_fingerprint": fp, "package.json": pkg_sha,
                                               "summary.md": sum_sha})
    ctx["fingerprint"] = fp


# ── collect ───────────────────────────────────────────────────────────────────

def _log_stop(ctx, reason):
    try:
        if ctx["run_dir_created"]:
            _event(ctx, ctx["step"] or "S0a", RESULT_STOPPED, reason, None)
        _index(ctx, "stopped", reason=reason)
    except Exception:
        _err(u"停下事件無法記錄;證據可能不完整")


def collect(root, claude_root, settle):
    root = os.path.abspath(os.fspath(root))
    _toplevel(root)
    check_preconditions(root)
    ident = _identity(root)
    core = build_snapshot(root, ident)
    run_id = "%s-%s" % (_now().strftime("%Y%m%dT%H%M%SZ"), ident["head"][:7])
    evid = _abs(root, EVIDENCE_REL)
    _check_chain(root, EVIDENCE_REL)
    os.makedirs(evid, exist_ok=True)            # 證據根目錄:鎖檔要有地方放,取鎖前建立
    _check_chain(root, EVIDENCE_REL)
    lock_path, lock_content = _acquire_lock(evid, run_id)
    ctx = {"root": root, "run_id": run_id, "run_dir": os.path.join(evid, run_id), "evid": evid,
           "ident": ident, "claude_root": claude_root, "settle": settle, "step": None,
           "run_dir_created": False}
    started = False
    code, reason = EXIT_INTERNAL, None
    try:
        scan_evidence(evid, holding_lock=True)
        _index(ctx, "start")
        started = True
        check_preconditions(root, EVIDENCE_REL + "/" + run_id)
        try:
            os.mkdir(ctx["run_dir"])            # 執行目錄:取鎖之後才建立
        except FileExistsError:
            raise Stop(EXIT_MISMATCH, u"執行目錄 %s 已存在;不覆寫" % run_id)
        ctx["run_dir_created"] = True
        ctx["step"] = "S0b"
        step_s0b(ctx, core)
        ctx["step"] = "S1"
        step_s1(ctx)
        ctx["step"] = "S2"
        step_s2(ctx)
        ctx["step"] = "S3"
        step_s3(ctx)
        _index(ctx, "collect_completed", fingerprint=ctx["fingerprint"])
        _out(u"證據包指紋:%s\n" % ctx["fingerprint"])
        code = EXIT_OK
    except Stop as e:
        code, reason = e.code, e.reason
    except Exception as e:
        code, reason = EXIT_INTERNAL, u"內部錯誤(%s);不確定一律當失敗" % type(e).__name__
    if reason is not None:
        if started:
            _log_stop(ctx, reason)
        _err(reason)
    if not _release_lock(lock_path, lock_content):
        _err(u"全域鎖已不存在或內容與本次不符;未刪除")
        if code == EXIT_OK:
            code = EXIT_INTERNAL
    return code


# ── 既有執行的子命令(取鎖 → 掃描 → 證據重驗 → 本體)──────────────────────────

def _open_run(root, run_id):
    """唯讀前置:使用前提、repo 識別、執行代號與目錄。回傳 `(root, ident, evid)`。"""
    root = os.path.abspath(os.fspath(root))
    _toplevel(root)
    check_preconditions(root)
    ident = _identity(root)
    if not RUN_ID_RE.match(run_id or ""):
        raise Stop(EXIT_PRECONDITION, u"執行代號格式不符")
    check_preconditions(root, EVIDENCE_REL + "/" + run_id)
    evid = _abs(root, EVIDENCE_REL)
    if not os.path.isdir(os.path.join(evid, run_id)):
        raise Stop(EXIT_MISMATCH, u"找不到執行 %s" % run_id)
    return root, ident, evid


def _locked(root, run_id, body, claude_root=None):
    root, ident, evid = _open_run(root, run_id)
    lock_path, lock_content = _acquire_lock(evid, run_id)
    try:
        scan_evidence(evid, holding_lock=True)
        info = verify_run(evid, run_id)       # 證據本身不可信 ⇒ Stop(4),什麼都不寫
        ctx = {"root": root, "run_id": run_id, "run_dir": os.path.join(evid, run_id), "evid": evid,
               "ident": ident, "info": info, "claude_root": claude_root}
        return body(ctx)
    finally:
        if not _release_lock(lock_path, lock_content):
            _err(u"全域鎖已不存在或內容與本次不符;未刪除")


def _require_usable_approval(info):
    if info["voids"]:
        raise Stop(EXIT_MISMATCH, u"核准不適用事件存在,不得沿用該核准;" + _VOID_ADVICE)
    if "S4" not in info["steps"]:
        raise Stop(EXIT_MISMATCH, u"沒有核准代記(S4 未完成)")


def _fps(info):
    return {"package_fingerprint": info["fp"], "approval.json": info["approval_sha"]}


def _stop_with_record(ctx, step, label, mismatches):
    """失配:保留現狀,寫停下事件與 index 紀錄,停(4)。不還原、不改 index、不刪任何東西。"""
    reason = u"%s不符:%s;保留現狀,不自動還原" % (label, u"、".join(m["item"] for m in mismatches))
    _event(ctx, step, RESULT_STOPPED, reason, _fps(ctx["info"]), {"mismatches": mismatches})
    _index(ctx, "stopped", reason=reason, fingerprint=ctx["info"]["fp"])
    raise Stop(EXIT_MISMATCH, reason)


# ── S4 record-approval ────────────────────────────────────────────────────────

def record_approval(root, run_id, fingerprint, approved_at, note):
    try:
        when = datetime.fromisoformat(approved_at)
    except (TypeError, ValueError):
        raise Stop(EXIT_PRECONDITION, u"--approved-at 不是 ISO 8601 時間")
    if when.tzinfo is None:
        raise Stop(EXIT_PRECONDITION, u"--approved-at 必須帶時區")

    def body(ctx):
        info = ctx["info"]
        if "S3" not in info["steps"]:
            raise Stop(EXIT_MISMATCH, u"S3 尚未完成;沒有可核准的證據包")
        if "S4" in info["steps"] or os.path.lexists(os.path.join(ctx["run_dir"], "approval.json")):
            raise Stop(EXIT_MISMATCH, u"已有核准代記;不得第二次代記、不得覆寫")
        if fingerprint != info["fp"]:
            raise Stop(EXIT_MISMATCH, u"--fingerprint 與證據包指紋不逐字相同(不接受短碼、大小寫不同或前後空白)")
        doc = {"format_version": FORMAT_VERSION, "run_id": run_id, "package_fingerprint": info["fp"],
               "approved_at": approved_at, "recorded_at": _iso(_now()), "recorded_by": APPROVAL_BY,
               "statement": APPROVAL_STATEMENT, "note": note}
        digest = _write_artifact(ctx, "approval.json", _json_bytes(doc))
        _event(ctx, "S4", RESULT_COMPLETED, None, {"package_fingerprint": info["fp"], "approval.json": digest})
        _index(ctx, "approval_recorded", fingerprint=info["fp"])
        _out(u"已代記核准:證據包指紋 %s\n下一步:pre-register\n" % info["fp"])
        return EXIT_OK
    return _locked(root, run_id, body)


# ── S5 pre-register(含原 verify)─────────────────────────────────────────────

def _resample(ctx, settle):
    """照 settle_seconds 間隔重新取樣兩次。樣本本身出問題 ⇒ 回 `(None, 原因)`。"""
    try:
        first = sample(ctx["root"], ctx["claude_root"])
        _sleep(settle)
        second = sample(ctx["root"], ctx["claude_root"])
    except Stop as e:
        if e.code == EXIT_INTERNAL:
            raise
        return None, e.reason
    return (first, second), None


def pre_register(root, run_id, claude_root):
    """登記前重驗。五項要求:(1) 證據原件、指紋、摘要、事件順序重驗(`_locked` → `verify_run`);
    (2) 核准代記有效(`verify_run` + `_require_usable_approval`);(3) 現場狀態與快照完全相符;
    (4) 重新取樣的綁定資料與已保存樣本相符;(5) 候選名冊重算位元組相同。
    (1)(2) 失敗 ⇒ 什麼都不寫;(3)～(5) 任一不符 ⇒ 核准不適用。"""
    def body(ctx):
        info = ctx["info"]
        _require_usable_approval(info)
        if "S5" in info["steps"]:
            raise Stop(EXIT_MISMATCH, u"S5 已完成;不重做")
        snap = _load(ctx["run_dir"], "snapshot.json")
        diff = _load(ctx["run_dir"], "diff.json")
        with io.open(os.path.join(ctx["run_dir"], "candidate-inventory.json"), "rb") as fh:
            saved_candidate = fh.read()
        mismatches = []
        # (3) 現場狀態與快照
        try:
            current = build_snapshot(ctx["root"], ctx["ident"])
        except Stop as e:
            if e.code == EXIT_INTERNAL:
                raise
            current = None
            mismatches.append({"item": "state", "snapshot": None, "live": e.reason})
        if current is not None:
            for key in _VIEW_KEYS:
                if current.get(key) != snap.get(key):
                    mismatches.append({"item": key, "snapshot": snap.get(key), "live": current.get(key)})
        # (4) 重新取樣:兩次本身須穩定、與已保存樣本的綁定資料相符
        saved = _binding(diff["samples"][-1])
        samples, problem = _resample(ctx, diff["settle_seconds"])
        records = []
        if samples is None:
            mismatches.append({"item": "resample", "snapshot": None, "live": problem})
        else:
            records = [_sample_record(s) for s in samples]
            b1, b2 = _binding(records[0]), _binding(records[1])
            if b1 != b2:
                mismatches.append({"item": "resample_unstable", "snapshot": b1, "live": b2})
            if b2 != saved:
                mismatches.append({"item": "resample_binding", "snapshot": saved, "live": b2})
            # (5) 候選名冊重算
            second = samples[1]
            again = _json_bytes(build_candidate(second["inventory"], second["classification"]["differences"],
                                                run_id))
            if again != saved_candidate:
                mismatches.append({"item": "candidate", "snapshot": _sha256(saved_candidate),
                                   "live": _sha256(again)})
        if mismatches:
            reason = u"核准不適用:%s 與快照或已保存證據不符;%s" % (
                u"、".join(m["item"] for m in mismatches), _VOID_ADVICE)
            _event(ctx, "S5", RESULT_VOID, reason, _fps(info), {"mismatches": mismatches})
            _index(ctx, "approval_void", reason=reason, fingerprint=info["fp"])
            raise Stop(EXIT_MISMATCH, reason)
        fps = _fps(info)
        fps.update({"sample_1": _sha256(_canonical(records[0])), "sample_2": _sha256(_canonical(records[1]))})
        _event(ctx, "S5", RESULT_COMPLETED, None, fps, {"sample_times": [r["time"] for r in records]})
        _index(ctx, "pre_register_completed", fingerprint=info["fp"])
        _out(u"登記前重驗通過。\n下一步:由 VS 依現有程序與另行授權退出暫存、以候選名冊登記;"
             u"工具不執行這些動作。登記後執行 post-register。\n")
        return EXIT_OK
    return _locked(root, run_id, body, claude_root)


# ── S6' post-register ─────────────────────────────────────────────────────────

def _commit_parents(root, length):
    toks = _text(_git_ok(root, ["rev-list", "--parents", "-n", "1", "HEAD"])).split()
    for t in toks:
        _full_id(t, length, u"commit ID")
    return toks[0], toks[1:]


def _registration_commit_problem(root, snap_head, length):
    """HEAD 是否恰好是「父節點 = 快照 HEAD、只改名冊一檔(不改模式)」的登記 commit。
    是 ⇒ None;否 ⇒ 不符項目清單。"""
    head, parents = _commit_parents(root, length)
    if parents != [snap_head]:
        return [{"item": "parent", "snapshot": snap_head, "live": parents}]
    entries = parse_cached_raw(_git_ok(root, ["diff", "--raw", "-z", "--no-renames", "--no-abbrev",
                                              parents[0], head]), length)
    only = len(entries) == 1 and entries[0]["path"] == INVENTORY_REL and entries[0]["status"] == "modified" \
        and entries[0]["head"]["mode"] == entries[0]["index"]["mode"]
    if not only:
        return [{"item": "changed_paths", "snapshot": [INVENTORY_REL],
                 "live": [{"path": e["path"], "status": e["status"], "from_mode": e["head"].get("mode"),
                           "to_mode": e["index"].get("mode")} for e in entries]}]
    return None


def _scope_mismatches(root, snap, exclude):
    """待保護範圍(`exclude` 除外)的工作區指紋與快照比較。"""
    out = []
    reliable = snap["executable_mode_reliable"]
    if _exec_reliable(root) != reliable:
        out.append({"item": "executable_mode_reliable", "snapshot": reliable, "live": not reliable})
    for e in snap["protected_scope"]:
        if e["path"] in exclude:
            continue
        try:
            cur = _worktree_state(root, e["path"], reliable)
        except Stop as s:
            if s.code == EXIT_INTERNAL:
                raise
            cur = {"path": e["path"], "unsupported": s.reason}
        if cur != e:
            out.append({"item": "worktree", "path": e["path"], "snapshot": e, "live": cur})
    return out


def post_register(root, run_id, claude_root):
    def body(ctx):
        info = ctx["info"]
        _require_usable_approval(info)
        if "S5" not in info["steps"]:
            raise Stop(EXIT_MISMATCH, u"S5 尚未完成;先執行 pre-register")
        if "S6'" in info["steps"]:
            raise Stop(EXIT_MISMATCH, u"S6' 已完成;不重做")
        rroot, length = ctx["root"], ctx["ident"]["id_length"]
        snap = _load(ctx["run_dir"], "snapshot.json")
        cand_blob = (info["by_step"]["S2"].get("fingerprints") or {}).get("candidate_blob")
        mismatches = _registration_commit_problem(rroot, snap["head"]["commit"], length) or []
        proc = _git(rroot, ["rev-parse", "--verify", "-q", "HEAD:" + INVENTORY_REL])
        blob = _text(proc.stdout) if proc.returncode == 0 else None
        if blob != cand_blob:
            mismatches.append({"item": "inventory_blob", "snapshot": cand_blob, "live": blob})
        report = _extension_report(rroot, ctx["claude_root"])
        inv = report.get("inventory") if isinstance(report.get("inventory"), dict) else {}
        synced = report.get("synced") if isinstance(report.get("synced"), dict) else {}
        if inv.get("state") != "ok" or synced.get("verified") is not True:
            mismatches.append({"item": "r10", "snapshot": {"inventory": "ok", "synced_verified": True},
                               "live": {"inventory": inv.get("state"), "synced_verified": synced.get("verified"),
                                        "synced_reason": synced.get("reason")}})
        mismatches += _scope_mismatches(rroot, snap, {INVENTORY_REL})
        if mismatches:
            _stop_with_record(ctx, "S6'", u"登記後核對", mismatches)
        head = _head(rroot, length)
        _event(ctx, "S6'", RESULT_COMPLETED, None, _fps(info), {"new_head": head})
        _index(ctx, "post_register_completed", fingerprint=info["fp"], extra={"new_head": head})
        _out(u"登記後核對通過;新 HEAD %s\n下一步:由 VS 依現有程序與另行授權接回原工作,然後執行 post-reattach。\n"
             % head)
        return EXIT_OK
    return _locked(root, run_id, body, claude_root)


# ── S7' post-reattach 與 S8 收尾 ──────────────────────────────────────────────

def _reattach_mismatches(root, snap, candidate_sha):
    out = []
    staged = [s for s in snap["staged"] if s["path"] != INVENTORY_REL]
    for s in staged:
        rows = [(r[1], r[2], r[3]) for r in _ls_stage(root, [s["path"]]) if r[0] == s["path"]]
        if s["index"]["exists"]:
            want = [(s["index"]["mode"], s["index"]["blob"], "0")]
            if rows != want:
                out.append({"item": "staged", "path": s["path"], "snapshot": s["index"], "live": rows})
        elif rows:
            out.append({"item": "deleted_present", "path": s["path"], "snapshot": s["index"], "live": rows})
    expected = sorted(s["path"] for s in staged)
    cached = sorted(p for p in _z(_git_ok(root, ["diff", "--cached", "--name-only", "-z"]))
                    if not _is_evidence_path(p))
    if cached != expected:
        out.append({"item": "cached_diff", "snapshot": expected, "live": cached})
    for p in snap["partially_staged"]:
        rows = [(r[1], r[2]) for r in _ls_stage(root, [p["path"]]) if r[0] == p["path"]]
        if rows != [(p["mode"], p["blob"])]:
            out.append({"item": "partially_staged", "path": p["path"], "snapshot": p, "live": rows})
    out += _scope_mismatches(root, snap, {INVENTORY_REL})
    inv = _worktree_state(root, INVENTORY_REL, snap["executable_mode_reliable"])
    if inv.get("sha256") != candidate_sha:
        out.append({"item": "inventory_worktree", "snapshot": candidate_sha, "live": inv.get("sha256")})
    return out


def _write_s8(ctx, summary):
    _event(ctx, "S8", RESULT_COMPLETED, None, {"package_fingerprint": ctx["info"]["fp"]}, summary)


def _index_run_completed(ctx, summary):
    _index(ctx, "run_completed", fingerprint=summary["package_fingerprint"],
           extra={"new_head": summary["new_head"], "untracked_diff_count": summary["untracked_diff_count"]})


def post_reattach(root, run_id):
    def body(ctx):
        info = ctx["info"]
        _require_usable_approval(info)
        if "S6'" not in info["steps"]:
            raise Stop(EXIT_MISMATCH, u"S6' 尚未完成;先執行 post-register")
        rroot, length = ctx["root"], ctx["ident"]["id_length"]
        head = _head(rroot, length)
        if head != info["s6_head"]:
            raise Stop(EXIT_MISMATCH, u"HEAD 已不是 S6' 記錄的 HEAD;不核對、不寫入")
        if "S8" in info["steps"] and info["final_recorded"]:
            _out(u"流程已完成:執行 %s、證據包指紋 %s、新 HEAD %s;不重寫\n" % (run_id, info["fp"], head))
            return EXIT_OK
        snap = _load(ctx["run_dir"], "snapshot.json")
        cand_sha = (info["by_step"]["S2"].get("fingerprints") or {}).get("candidate-inventory.json")
        mismatches = _reattach_mismatches(rroot, snap, cand_sha)
        current = _untracked(rroot)
        added = sorted(set(current) - set(snap["untracked"]["paths"]))
        removed = sorted(set(snap["untracked"]["paths"]) - set(current))
        if mismatches:
            _stop_with_record(ctx, "S7'", u"接回後核對", mismatches)
        detail = {"untracked_added": added, "untracked_removed": removed, "content_verified": False,
                  "note": UNTRACKED_NOTE}
        if "S7'" not in info["steps"]:
            _event(ctx, "S7'", RESULT_COMPLETED, None, _fps(info), detail)
        summary = {"run_id": run_id, "package_fingerprint": info["fp"], "new_head": head,
                   "untracked_diff_count": len(added) + len(removed)}
        if "S8" not in info["steps"]:
            _write_s8(ctx, summary)
        if not info["final_recorded"]:
            _index_run_completed(ctx, summary)
        lines = [u"接回後核對通過。"]
        for p in added:
            lines.append(u"未追蹤檔新增:%s(內容未驗證)" % p)
        for p in removed:
            lines.append(u"未追蹤檔消失:%s(內容未驗證)" % p)
        lines.append(u"流程已完成:執行 %s、證據包指紋 %s、新 HEAD %s" % (run_id, info["fp"], head))
        _out(u"\n".join(lines) + u"\n")
        return EXIT_OK
    return _locked(root, run_id, body)


# ── resume(完全唯讀,不取鎖)────────────────────────────────────────────────

def _resume_s5(root, snap, length):
    snap_head = snap["head"]["commit"]
    if _head(root, length) == snap_head:
        return u"尚未登記:由 VS 依現有程序與授權登記,然後執行 post-register"
    problem = _registration_commit_problem(root, snap_head, length)
    if problem is None:
        return u"已登記:直接執行 post-register(不需再登記)"
    raise Stop(EXIT_MISMATCH, u"無法辨識目前狀態:HEAD 不是快照 HEAD,也不是只改名冊的單一登記 commit(%s)"
               % u"、".join(p["item"] for p in problem))


def _resume_s6(root, snap, info, length):
    if _head(root, length) != info["s6_head"]:
        raise Stop(EXIT_MISMATCH, u"無法辨識目前狀態:HEAD 已不是 S6' 記錄的 HEAD")
    cached = set(p for p in _z(_git_ok(root, ["diff", "--cached", "--name-only", "-z"])) if not _is_evidence_path(p))
    expected = set(s["path"] for s in snap["staged"] if s["path"] != INVENTORY_REL)
    if not cached:
        return u"尚未接回:由 VS 依現有程序與授權接回原工作,然後執行 post-reattach"
    if cached <= expected:
        return u"已接回或部分接回:直接執行 post-reattach 核對(不需再接回)"
    raise Stop(EXIT_MISMATCH, u"無法辨識目前狀態:待提交區有 %d 個快照以外的差異路徑" % len(cached - expected))


def resume(root, run_id):
    root, ident, evid = _open_run(root, run_id)
    if os.path.lexists(os.path.join(evid, LOCK_NAME)):
        raise Stop(EXIT_MISMATCH, _LOCK_HELD)
    scan_evidence(evid, holding_lock=False)
    info = verify_run(evid, run_id)
    last = info["last"]
    if last is None:
        raise Stop(EXIT_MISMATCH, u"執行 %s 沒有任何完成步驟;請重新 collect" % run_id)
    for e in info["stopped_after"]:
        _out(u"前一次在 %s 停下:%s(不建議自動修復)\n" % (e.get("step"), e.get("reason")))
    if info["voids"]:
        _out(u"核准不適用:%s\n%s\n" % (info["voids"][-1].get("reason"), _VOID_ADVICE))
        return EXIT_MISMATCH
    snap = _load(os.path.join(evid, run_id), "snapshot.json")
    length = ident["id_length"]
    pos = STEPS.index(last)
    if pos <= STEPS.index("S4"):
        if state_view(build_snapshot(root, ident)) != state_view(snap):
            raise Stop(EXIT_MISMATCH, u"目前狀態(HEAD／待提交項目／待保護範圍／名冊與 allowlist)與快照不符;"
                                      u"請重新 collect")
        if last == "S3":
            _out(u"執行 %s 證據包已完成;證據包指紋:%s\n下一步:等待 Jeff 核准此證據包指紋,再執行 record-approval 代記\n"
                 % (run_id, info["fp"]))
        elif last == "S4":
            _out(u"執行 %s 已有核准代記;證據與目前狀態相符\n下一步:pre-register\n" % run_id)
        else:
            _out(u"執行 %s 最後完成步驟 %s;證據與目前狀態相符\n下一步:%s(resume 不代寫;請重新 collect)\n"
                 % (run_id, last, STEPS[pos + 1]))
        return EXIT_OK
    if last == "S5":
        _out(u"下一步:%s\n" % _resume_s5(root, snap, length))
        return EXIT_OK
    if last == "S6'":
        _out(u"下一步:%s\n" % _resume_s6(root, snap, info, length))
        return EXIT_OK
    if last == "S7'" or not info["final_recorded"]:
        _out(u"核對已完成、收尾紀錄未完成;下一步:執行 post-reattach 補完收尾(resume 不補寫、不宣稱完成)\n")
        return EXIT_OK
    _out(u"流程已完成:執行 %s、證據包指紋 %s、新 HEAD %s\n" % (run_id, info["fp"], info["s8"]["new_head"]))
    return EXIT_OK


# ── 命令列 ────────────────────────────────────────────────────────────────────

def main(argv=None):
    parser = argparse.ArgumentParser(prog="inventory_evidence")
    sub = parser.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect")
    c.add_argument("--repo", default=".")
    c.add_argument("--claude-root", default=None)
    c.add_argument("--settle-seconds", type=int, default=60)
    a = sub.add_parser("record-approval")
    a.add_argument("--repo", default=".")
    a.add_argument("--run", required=True)
    a.add_argument("--fingerprint", required=True)
    a.add_argument("--approved-at", required=True)
    a.add_argument("--note", required=True)
    for name in ("pre-register", "post-register"):
        p = sub.add_parser(name)
        p.add_argument("--repo", default=".")
        p.add_argument("--run", required=True)
        p.add_argument("--claude-root", default=None)
    for name in ("post-reattach", "resume"):
        p = sub.add_parser(name)
        p.add_argument("--repo", default=".")
        p.add_argument("--run", required=True)
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return EXIT_PRECONDITION if e.code else EXIT_OK
    try:
        if args.cmd == "collect":
            if args.settle_seconds < 0:
                raise Stop(EXIT_PRECONDITION, u"--settle-seconds 不得為負")
            return collect(args.repo, args.claude_root, args.settle_seconds)
        if args.cmd == "record-approval":
            return record_approval(args.repo, args.run, args.fingerprint, args.approved_at, args.note)
        if args.cmd == "pre-register":
            return pre_register(args.repo, args.run, args.claude_root)
        if args.cmd == "post-register":
            return post_register(args.repo, args.run, args.claude_root)
        if args.cmd == "post-reattach":
            return post_reattach(args.repo, args.run)
        return resume(args.repo, args.run)
    except Stop as e:
        _err(e.reason)
        return e.code
    except Exception as e:
        _err(u"內部錯誤(%s);不確定一律當失敗" % type(e).__name__)
        return EXIT_INTERNAL


if __name__ == "__main__":
    sys.exit(main())
