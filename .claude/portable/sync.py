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
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import manifest                                             # noqa: E402

FRICTION = "docs/agents/friction-log.md"
PROVENANCE = ".dev/provenance.jsonl"
FRICTION_LOCAL = "docs/agents/friction-local.md"

HEADING = re.compile(r"^## (\S+)", re.M)


class Refused(Exception):
    """拒絕執行。**回傳空計畫不是拒絕** —— 那會被讀成「沒事要做」。"""


class Plan(object):
    __slots__ = ("changed", "added", "needs_decision", "verified", "untouched")

    def __init__(self):
        self.changed = []
        self.added = []
        # `ask` 桶裡兩邊不一樣的檔案。**跳過是對的,不出聲不對** ——
        # 靜默跳過的話,那些檔案的漂移永遠沒有人看得到,而
        # 「兩邊不一致而沒有人知道」正是這條路徑要消滅的東西(ticket 01)。
        self.needs_decision = []
        self.untouched = {}
        self.verified = False

    def __repr__(self):
        return ("Plan(changed=%d, added=%d, needs_decision=%d, verified=%s)"
                % (len(self.changed), len(self.added),
                   len(self.needs_decision), self.verified))


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
    """讀來源 repo 的標記表。**解析與優先序都用 `manifest.py` 那一份實作。**

    原本這裡有一份自己的:兩份會漂移,而漂移的那天不會有人發現 ——
    一個把檔案搬過去、一個以為沒搬(F-058)。而且自己那份還漏掉了
    重複標記與不認得標記的檢查,於是格式錯誤在更新路徑上會靜默退化成 copy。
    """
    return manifest.load_table(
        os.path.join(src, ".agents", "portable-manifest.txt"))


def mark_for(rel, marks):
    """這個檔案哪個桶。判定在 `manifest.mark_in`,本函式只是轉呼叫。"""
    return manifest.mark_in(rel, marks)


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


def head_commit(root):
    out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True)
    if out.returncode != 0:
        raise Refused("問不到 %s 的 HEAD" % root)
    return out.stdout.decode("utf-8", "replace").strip()


def in_commit(root, commit, rel):
    """這個路徑在那個 commit 的樹裡嗎。"""
    return subprocess.run(["git", "-C", root, "cat-file", "-e",
                           "%s:%s" % (commit, rel)],
                          capture_output=True).returncode == 0


def write_provenance(src, target, rels, commit):
    """替同步進來的檔案產 provenance:上游 commit + 路徑。

    下游的 R3 據此改判「與上游一致 ⇒ 紅燈責任在上游」——
    紅綠燈迴圈在上游,下游拿到的是成品,它從來沒有機會讓那些測試紅過。

    **這個檔案是控制,不是證據,所以寫的東西要能被獨立查證。**
    `content_hash` 只是給人看的;下游驗證一律拿 `git show <commit>:<path>`
    自己算,不採信這裡宣稱的值 —— 否則手寫一筆就換得到豁免。

    **上游沒提交的檔案不發憑證**:provenance 的效力全部來自「查得到那個 git 物件」,
    對一個不在物件庫裡的檔案發憑證,下游查證時必然失敗 ——
    那不是保護,是製造一筆查不到的紀錄。
    """
    out = []
    for rel in rels:
        if not in_commit(src, commit, rel):
            continue
        # **不寫 upstream_root。** 那是本機設定,不該跟著 commit 進版控
        # (去識別化);而且欄位一旦可寫,指向一個自己控制的 repo 就能造出
        # 任意「上游物件」。位置改住使用者層的 G1 保護指標檔,gate 唯讀。
        out.append({
            "path": rel,
            "upstream_path": rel,
            "upstream_commit": commit,
            "content_hash": file_hash(os.path.join(src, rel.replace("/", os.sep))),
        })
    if not out:
        return []
    p = os.path.join(target, PROVENANCE.replace("/", os.sep))
    d = os.path.dirname(p)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(p, "a", encoding="utf-8", newline="\n") as f:
        for rec in out:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return out


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
        mark = mark_for(rel, marks)
        if mark != "copy":
            # `ask` 桶:不自動搬,但兩邊不一樣就要說出來。
            if mark == "ask":
                sp = os.path.join(src, rel.replace("/", os.sep))
                tp = os.path.join(target, rel.replace("/", os.sep))
                if file_hash(sp) != file_hash(tp):
                    plan.needs_decision.append(rel)
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
    # provenance 在 hash 重驗**之後**才寫 —— 驗證沒過就不該有憑證,
    # 否則帳面上會出現一張替沒寫成功的檔案背書的憑證。
    write_provenance(src, target, plan.changed + plan.added, head_commit(src))
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
    out.append(u"內容不同 %d / 新增 %d / 要人決定 %d"
               % (len(plan.changed), len(plan.added), len(plan.needs_decision)))
    for rel in plan.changed:
        out.append(u"  M %s" % rel)
    for rel in plan.added:
        out.append(u"  + %s" % rel)
    for rel in plan.needs_decision:
        out.append(u"  ? %s(ask 桶:兩邊不同,不自動搬,要人決定帶哪些)" % rel)
    out.append(u"")
    out.append(u"寫入並通過 hash 重驗" if plan.verified
               else u"(dry-run,沒有寫任何東西;要實際更新加 --apply)")
    sys.stdout.buffer.write((u"\n".join(out) + u"\n").encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
