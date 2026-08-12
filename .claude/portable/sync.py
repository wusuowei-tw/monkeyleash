# -*- coding: utf-8 -*-
"""框架更新路徑:把 `copy` 桶從框架推到已安裝的 repo(票 09 / ticket 01)。

用法:
  python .claude/portable/sync.py <目標 repo>            列出會動到什麼(不寫)
  python .claude/portable/sync.py <目標 repo> --apply    實際寫入並重驗

**這支工具會覆寫別的 repo 的檔案**,所以每一個「不確定」都往**不寫**倒:

  目標工作樹髒                 -> 拒絕(與 install.py 同規矩)
  桶標未裁決(portable-manifest)-> 跳過那個檔
  friction-log 有未搬遷的本地條目 -> 拒絕,並列出是哪幾則
  寫完 hash 對不上來源           -> 拒絕(而不是回報成功)

而且「我沒碰別的桶」是宣稱,不是證據 —— 所以 `generate` / `ask` / `skip`
桶的 hash 在寫入前後各算一次,變了就是缺陷。

**判定邏輯不放 `scripts/`。** 這支工具決定哪些檔案被覆蓋,那是判定邏輯;
放進非原始碼清單等於讓它不受 R2/R3 管,而那個位置已經撞過三次(見 CLAUDE.md)。
"""

import hashlib
import io
import os
import re
import subprocess
import sys

# 桶標未裁決之前一律跳過(票 10)。它列著各 repo 自己的測試歸類,
# blind-copy 會把那些刪掉 —— 而「哪個測試屬於哪一邊」是判斷,不是可推導的事實。
NEVER_COPY = (".agents/portable-manifest.txt",)

FRICTION = "docs/agents/friction-log.md"
FRICTION_LOCAL = "docs/agents/friction-local.md"

HEADING = re.compile(r"^## (\S+)", re.M)


class Refused(Exception):
    """拒絕執行。**回傳空計畫不是拒絕** —— 那會被讀成「沒事要做」。"""


class Plan(object):
    __slots__ = ("changed", "added", "skipped", "verified", "untouched")

    def __init__(self):
        self.changed = []
        self.added = []
        self.skipped = []
        self.untouched = {}
        self.verified = False

    def __repr__(self):
        return ("Plan(changed=%d, added=%d, skipped=%d, verified=%s)"
                % (len(self.changed), len(self.added), len(self.skipped),
                   self.verified))


def _norm(raw):
    """行尾正規化後雜湊。跨 repo 比對時 autocrlf 設定可能不同,
    不正規化的話每一個檔案都會看起來不一樣(見 ADR 0013 的同一個理由)。"""
    return hashlib.sha256(raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
                          ).hexdigest()


def file_hash(path):
    try:
        with io.open(path, "rb") as f:
            return _norm(f.read())
    except Exception:
        return None


def _write_bytes(path, raw):
    """抽成函式是為了讓「寫了但內容不對」可以被測試注入 ——
    沒有那條測試的話,寫完重驗只是一個永遠為真的旗標。"""
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(path, "wb") as f:
        f.write(raw)


def load_manifest(src):
    out = []
    p = os.path.join(src, ".agents", "portable-manifest.txt")
    for line in io.open(p, encoding="utf-8-sig"):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 2:
            out.append((parts[0].replace("\\", "/"), parts[1]))
    return out


def mark_for(rel, marks):
    """最長前綴者勝 —— **不是讀取順序**。順序決定的話,換個排法就換個行為,
    而那是隱形的。"""
    best, best_mark = "", None
    for p, m in marks:
        if p.endswith("/"):
            if rel.startswith(p) and len(p) > len(best):
                best, best_mark = p, m
        elif rel == p and len(p) > len(best):
            best, best_mark = p, m
    return best_mark


def tracked(root):
    out = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True)
    if out.returncode != 0:
        raise Refused("%s 不是 git repo,或 git 不可用" % root)
    return [p for p in out.stdout.decode("utf-8", "replace").split("\0")
            if p.strip()]


def refuse_if_dirty(target):
    out = subprocess.run(["git", "status", "--porcelain",
                          "--ignore-submodules=dirty"],
                         cwd=target, capture_output=True)
    if out.returncode != 0:
        raise Refused("問不到 %s 的工作樹狀態" % target)
    dirty = [l for l in out.stdout.decode("utf-8", "replace").splitlines()
             if l.strip()]
    if dirty:
        raise Refused(
            "目標工作樹不乾淨(%d 項),先清乾淨再更新 —— "
            "在未提交的變更上覆寫,出事時分不出是誰改的:\n  %s"
            % (len(dirty), "\n  ".join(dirty[:10])))


def unmigrated_friction(src, target):
    """目標的 friction-log 有、來源沒有的條目 = 還沒搬去 friction-local.md。

    覆蓋會把它們刪掉,所以這是拒絕的條件,不是警告 ——
    警告會被略過,而被刪掉的條目沒有第二份。
    """
    a = os.path.join(src, FRICTION.replace("/", os.sep))
    b = os.path.join(target, FRICTION.replace("/", os.sep))
    if not os.path.exists(b):
        return []
    try:
        sh = set(HEADING.findall(io.open(a, encoding="utf-8").read()))
        th = set(HEADING.findall(io.open(b, encoding="utf-8").read()))
    except Exception as e:
        raise Refused("讀不到 friction-log,無法判定有沒有本地條目:%s" % e)
    return sorted(th - sh)


def update(src, target, apply=False):
    """回傳 `Plan`。`apply=False`(預設)不寫任何東西。"""
    src, target = os.path.abspath(src), os.path.abspath(target)
    marks = load_manifest(src)
    plan = Plan()

    if apply:
        refuse_if_dirty(target)

    stale = unmigrated_friction(src, target)
    if stale:
        raise Refused(
            "目標的 %s 有 %d 則來源沒有的條目 —— 那是還沒搬去 %s 的專案條目,"
            "覆蓋會刪掉它們:\n  %s"
            % (FRICTION, len(stale), FRICTION_LOCAL, "\n  ".join(stale)))

    # 別的桶的現況 —— 寫入前先記下來,寫完要驗它們沒變
    for rel in tracked(target):
        if mark_for(rel, marks) != "copy":
            plan.untouched[rel] = file_hash(
                os.path.join(target, rel.replace("/", os.sep)))

    for rel in sorted(tracked(src)):
        if mark_for(rel, marks) != "copy":
            continue
        if rel in NEVER_COPY:
            plan.skipped.append(rel)
            continue
        sp = os.path.join(src, rel.replace("/", os.sep))
        tp = os.path.join(target, rel.replace("/", os.sep))
        sh, th = file_hash(sp), file_hash(tp)
        if th is None:
            plan.added.append(rel)
        elif sh != th:
            plan.changed.append(rel)
        else:
            continue
        if apply:
            with io.open(sp, "rb") as f:
                _write_bytes(tp, f.read())

    if not apply:
        return plan

    # 寫完重驗 —— 宣稱寫對了不算數
    bad = [rel for rel in plan.changed + plan.added
           if file_hash(os.path.join(target, rel.replace("/", os.sep)))
           != file_hash(os.path.join(src, rel.replace("/", os.sep)))]
    if bad:
        raise Refused("寫入後 hash 驗證不通過(%d 個檔案):\n  %s"
                      % (len(bad), "\n  ".join(bad)))

    moved = [rel for rel, h in plan.untouched.items()
             if file_hash(os.path.join(target, rel.replace("/", os.sep))) != h]
    if moved:
        raise Refused("不該被動到的桶變了(%d 個檔案)—— 這是缺陷,不是設定:\n  %s"
                      % (len(moved), "\n  ".join(moved)))
    plan.verified = True
    return plan


def main(argv):
    if not argv:
        sys.stderr.write("用法:sync.py <目標 repo> [--apply]\n")
        return 2
    target = argv[0]
    apply = "--apply" in argv
    src = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        plan = update(src, target, apply=apply)
    except Refused as e:
        sys.stderr.buffer.write((u"[更新/拒絕] %s\n" % e).encode("utf-8"))
        return 1
    out = [u"來源:%s" % src, u"目標:%s" % os.path.abspath(target), u""]
    out.append(u"內容不同 %d / 新增 %d / 跳過 %d"
               % (len(plan.changed), len(plan.added), len(plan.skipped)))
    for rel in plan.changed:
        out.append(u"  M %s" % rel)
    for rel in plan.added:
        out.append(u"  + %s" % rel)
    for rel in plan.skipped:
        out.append(u"  - %s(桶標未裁決,跳過)" % rel)
    out.append(u"")
    out.append(u"寫入並通過 hash 重驗" if plan.verified
               else u"(dry-run,沒有寫任何東西;要實際更新加 --apply)")
    sys.stdout.buffer.write((u"\n".join(out) + u"\n").encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
