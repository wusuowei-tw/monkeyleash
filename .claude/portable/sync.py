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
    """這個檔案哪個桶。**未分類回 None,不套預設。**

    用 `explicit_mark` 而不是 `mark_in`:後者的預設是 `copy`,
    那是安裝器的語意,在更新路徑上的意思是「覆蓋別人 repo 的既有檔案」。
    批次二把兩份實作合一時,搬了分類器卻沒搬讓它安全的那兩道護欄
    (`in_scope` 過濾、未涵蓋鄰居列給人確認),於是預設從「跳過」翻成「覆蓋」。
    """
    return manifest.explicit_mark(rel, marks)


def refuse_if_unclassified(src, marks):
    """來源有任何未分類的檔案就拒絕,並點名是哪些、缺的是哪個前提。

    **不是跳過,是拒絕。** 跳過的話,下一個人新增檔案忘了分類時,
    那個檔案會從更新路徑上無聲消失 —— 而「沒帶到」與「不該帶」在
    綠燈上長得一樣。拒絕會讓漏分類在第一次同步就現形。

    訊息要說出**是哪一個前提沒滿足**(票 13 的判準):
    只說「拒絕」的話,人會去找權限、找路徑、找 git 狀態。
    """
    bad = [rel for rel in tracked(src) if manifest.explicit_mark(rel, marks) is None]
    if bad:
        raise Refused(
            "來源有 %d 個檔案沒有標記,更新路徑不知道該不該搬它們。\n"
            "     缺的前提是**標記**:每個檔案都要在 "
            ".agents/portable-manifest.txt 裡有一筆。\n"
            "     未分類**不會**被當成 copy —— 那個預設是安裝器的,\n"
            "     在這裡的意思是覆蓋你 repo 裡已經存在的同名檔案。\n"
            "     %s"
            % (len(bad), "\n     ".join(bad)))


def tracked(root):
    out = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True)
    if out.returncode != 0:
        raise Refused("%s 不是 git repo,或 git 不可用" % root)
    return [p for p in out.stdout.decode("utf-8", "replace").split("\0")
            if p.strip()]


def _sha_at(target, ref, path):
    """`ref` 那一版裡這條路徑記的 sha。取不到回 None。"""
    out = subprocess.run(["git", "-C", target, "rev-parse", "%s:%s" % (ref, path)],
                         capture_output=True)
    if out.returncode != 0:
        return None
    return out.stdout.decode("utf-8", "replace").strip()


def gitlink_paths(target):
    """index 裡 mode 為 160000 的路徑 —— 內嵌 repo(submodule 或裸 gitlink)。"""
    out = subprocess.run(["git", "-C", target, "ls-files", "-s", "-z"],
                         capture_output=True)
    if out.returncode != 0:
        raise Refused("問不到 %s 的 index" % target)
    paths = []
    for rec in out.stdout.decode("utf-8", "replace").split("\0"):
        if not rec.strip():
            continue
        meta, _, path = rec.partition("\t")
        if meta.split()[0] == "160000":
            paths.append(path)
    return paths


def is_own_repo(target, path):
    """`target/path` 底下真的有一個**自己的** repo 嗎。

    **不能只看 `git -C <path> rev-parse HEAD` 的退出碼。**
    git 找不到 repo 時會**往上走**,於是它會回答**外層** repo 的 HEAD 並回 0 ——
    「內嵌 repo 讀不到」那一格因此從來沒有被走到過(票 42 實測)。

    這件事一直被另一個分支遮著:舊版在那之後比 `index_sha != inner_sha`,
    而逃到外層拿回來的 sha 幾乎必然不等於 index 記的 sha,於是**照樣判髒** ——
    結論對,理由錯。第二格一放寬,遮蔽消失,整格變成 fail-open。
    **一個從未被走到的 fail-closed 分支,在它前面那個分支被拿掉的當天才會現形。**

    判法是問 git「你認為的工作樹根在哪」,再確認那就是這個路徑本身:

        git -C <path> rev-parse --show-toplevel   ==  <path>

    **不看 `.git` 存不存在**:真正的 submodule 的 `.git` 是一個**檔案**
    (指向 `../.git/modules/…`),不是目錄 —— 拿 `os.path.isdir` 判會漏掉
    每一個標準 submodule。而且那又是把判定交給檔案系統,git 才是權威。
    """
    sub = os.path.join(target, path.replace("/", os.sep))
    out = subprocess.run(["git", "-C", sub, "rev-parse", "--show-toplevel"],
                         capture_output=True)
    if out.returncode != 0:
        return False                       # 路徑不在、不是 repo、git 不可用
    top = out.stdout.decode("utf-8", "replace").strip()
    if not top:
        return False
    try:
        same = os.path.samefile(top, sub)
    except Exception:
        # samefile 需要兩邊都存在;存不到就退回字面比較(正規化大小寫與分隔符)
        same = (os.path.normcase(os.path.normpath(os.path.realpath(top)))
                == os.path.normcase(os.path.normpath(os.path.realpath(sub))))
    return same


def gitlink_unsettled(target):
    """**外層**對這些 gitlink 的記錄還沒塵埃落定的清單。

    要問的是「我的寫入會不會壓到未提交的變更」,而內嵌 repo 的**內部**狀態
    在 sync 的寫入面之外 —— sync 從不寫那條路徑底下的東西。
    量化 repo 的 `data_collector` 就是這樣被永久拒絕的(判錯對象第六例,票 17)。

    **不靠 `--ignore-submodules=dirty`。** 本機實測(git 2.53)那個旗標行為正確,
    量化那台卻永久拒絕 —— 代表它的語意隨版本/組態變。
    一道護欄的正確性掛在「哪個 git 版本」上,那個依賴本身就是缺陷:
    它會在別人的機器上安靜地翻面,而在我的機器上永遠測不到。
    所以這裡自己比對 sha,版本無關:

    ## 票 42(b):三態,只有中間那一格放寬

    | 情況 | 判定 | 理由 |
    |---|---|---|
    | HEAD sha != index sha(已 stage 未提交的 bump) | **髒** | 它會被下一次提交掃進去 —— 那是真的未落定,**且落在寫入面上** |
    | index sha != 內層 HEAD(內層前進、外層未記錄) | **放行** | **不在 sync 的寫入面上** |
    | 內嵌 repo 讀不到 | **髒** | fail-closed,問不出來不等於乾淨 |

    中間那一格原本判髒,理由寫的是「那是**外層**的未落定狀態」。
    推翻它的是本函式自己的判準:`refuse_if_dirty` 要防的是
    「**在未提交的變更上覆寫,出事時分不出是誰改的**」,而 sync 不寫 submodule
    底下任何東西、也不寫 gitlink 本身 —— 指標落後時,sync 覆寫框架檔的結果
    **完全不變**。這與上面「內部 modified / untracked 不算」是同一句話,
    當時只套到了一半。

    下游代價(推翻的直接原因):在票 42 (a) 未修時,下游**無法**落定它 ——
    bump 需要新版 leak_scan,取得新版要跑 sync,而 sync 因此拒絕。**循環**。

    **放寬只有這一格。** 第一格與第三格原地不動,而且各有負控釘著 ——
    少了它們,下一次重構會把這次放寬順手擴大成「gitlink 一律不管」,
    而那會讓一個已 staged、下次就會被提交的 bump 在覆寫時無法歸屬,
    也就是把 `refuse_if_dirty` 存在的唯一理由拿掉。
    """
    out = []
    for path in gitlink_paths(target):
        head_sha = _sha_at(target, "HEAD", path)
        index_sha = _sha_at(target, "", path)      # `:path` = index
        # 內層 repo 仍然要問 —— 但問的是「**問得到嗎**」(第三格的 fail-closed),
        # 不再拿它的 HEAD 去跟 index 比(第二格已放寬,票 42 (b))。
        if not is_own_repo(target, path):
            out.append("%s:讀不到內嵌 repo —— 問不出來不等於乾淨" % path)
            continue
        if index_sha is None:
            out.append("%s:讀不到 index 裡記的 sha" % path)
        elif head_sha is not None and head_sha != index_sha:
            out.append("%s:gitlink 已 stage 但未提交(HEAD %s / index %s)"
                       % (path, (head_sha or "")[:8], index_sha[:8]))
    return out


def refuse_if_dirty(target):
    """外層樹必須乾淨。**內嵌 repo 的內部狀態不算**(見 `gitlink_unsettled`)。"""
    out = subprocess.run(["git", "status", "--porcelain",
                          "--ignore-submodules=all"],
                         cwd=target, capture_output=True)
    if out.returncode != 0:
        raise Refused("問不到 %s 的工作樹狀態" % target)
    dirty = [l for l in out.stdout.decode("utf-8", "replace").splitlines()
             if l.strip()]
    dirty += gitlink_unsettled(target)
    if dirty:
        raise Refused(
            "目標**外層**工作樹不乾淨(%d 項),先清乾淨再更新 —— "
            "在未提交的變更上覆寫,出事時分不出是誰改的。\n"
            "     (內嵌 repo 的內部 modified / untracked **不算** ——\n"
            "      那在 sync 的寫入面之外,sync 從不寫它底下的東西。)\n  %s"
            % (len(dirty), "\n  ".join(dirty[:10])))


def _headings(path):
    """回 [(號碼, 行號), ...]。**保留重複**,不是集合。"""
    out = []
    for lineno, line in enumerate(io.open(path, encoding="utf-8"), 1):
        m = HEADING.match(line)
        if m:
            out.append((m.group(1), lineno))
    return out


def refuse_if_duplicate_headings(path, whose):
    """同一個號碼出現多次就拒絕,並點名號碼與**每一處行號**。

    由來:量化本地有兩則 `## F-046`(本地的 hook-session 那則 + 上游同號那則)。
    原本的差集用集合,兩則塌成一員,`th - sh` 把 F-046 整個消掉 ——
    於是 sync 放行,並**靜默刪掉本地那則**。

    **撞號正是這道護欄的獵物,而它被撞號打穿。**
    這道護欄存在的唯一理由就是「本地條目不能被覆蓋刪掉」,
    而它用的資料結構恰好對「同號多則」不可見。

    不自動判斷「哪一則該搬」:同號的兩則是**兩件不同的事**,
    分辨它們要讀內容,那是人的判斷。護欄的職責是讓它現形,不是替人決定。
    """
    seen = {}
    for token, lineno in _headings(path):
        seen.setdefault(token, []).append(lineno)
    dup = {t: ls for t, ls in seen.items() if len(ls) > 1}
    if dup:
        detail = "\n     ".join(
            "%s 出現 %d 次,在第 %s 行"
            % (t, len(ls), "、".join(str(x) for x in ls))
            for t, ls in sorted(dup.items()))
        raise Refused(
            "%s 的 %s 有重複的條目號碼,這份表無法用來判斷哪些是本地條目。\n"
            "     缺的前提是**號碼唯一**:差集看不見同號多則,\n"
            "     於是本地那一則會被靜默刪掉(票 17)。\n"
            "     同號的兩則是兩件不同的事,要分辨它們得讀內容 —— 那是人的判斷。\n"
            "     %s" % (whose, FRICTION, detail))


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
        # **先驗號碼唯一,再做差集。** 順序不能反:差集本身對同號多則是盲的,
        # 先做差集就等於在一份不可信的表上下結論。
        if os.path.exists(a):
            refuse_if_duplicate_headings(a, "來源")
        refuse_if_duplicate_headings(b, "目標")
        sh = set(t for t, _ in _headings(a)) if os.path.exists(a) else set()
        th = set(t for t, _ in _headings(b))
    except Refused:
        raise
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


def identical_copy_files(src, target, marks):
    """`copy` 桶裡**與上游逐位元組相同**的檔案。

    判準是「它與上游一致」,不是「我這輪寫了它」。原本只替 `changed + added`
    發證,於是**從未需要更新的檔案永遠拿不到證** —— 量化的 `g1_verify.py`、
    `shadow_review.py` 一直與上游相同,每一輪都不在那個集合裡,
    R3 一醒就紅而且永遠不會自己好(票 19)。

    「與上游那個 commit 的物件逐位元組相同 ⇒ 紅燈責任在上游」才是 R3 問的
    問題(ADR F-0014),而那與「這輪有沒有寫過」無關。
    """
    out = []
    for rel in sorted(tracked(src)):
        if manifest.explicit_mark(rel, marks) != "copy":
            continue
        sp = os.path.join(src, rel.replace("/", os.sep))
        tp = os.path.join(target, rel.replace("/", os.sep))
        if file_hash(sp) is not None and file_hash(sp) == file_hash(tp):
            out.append(rel)
    return out


def certify(src, target):
    """**補證模式**:只發 provenance,不寫任何 repo 內容。

    要解的死循環:發證原本要求淨樹,而下游需要**在把東西納入管理之前**先補證
    —— 發證與淨樹互為前提(票 19)。

    `refuse_if_dirty` 對這條路徑不適用,理由是那道檢查的**理由**:
    「在未提交的變更上覆寫,出事時分不出是誰改的」。補證什麼都不覆寫,
    所以那個風險不存在。**判準完全不放寬**:仍然是「與上游逐位元組相同」,
    漂移的檔案照樣不發證 —— **髒樹不會換來假證**。

    回傳實際發出的紀錄。
    """
    src, target = os.path.abspath(src), os.path.abspath(target)
    marks = load_manifest(src)
    refuse_if_unclassified(src, marks)
    rels = identical_copy_files(src, target, marks)
    return write_provenance(src, target, rels, head_commit(src))


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

    # **dry-run 也要擋。** dry-run 的用途是「看看會動到什麼」,
    # 而一份把未分類檔案列成「將覆蓋」的清單本身就是錯的答案。
    refuse_if_unclassified(src, marks)

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
    #
    # 發給**所有與上游一致的 copy 檔**,不只這輪寫過的:判準是
    # 「它與上游一致」,不是「我寫了它」(票 19)。
    write_provenance(src, target, identical_copy_files(src, target, marks),
                     head_commit(src))
    plan.verified = True
    return plan


def main(argv):
    if not argv:
        sys.stderr.write("用法:sync.py <目標 repo> [--apply]\n")
        return 2
    target = argv[0]
    apply = "--apply" in argv
    if "--certify" in argv:
        src = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))
        try:
            issued = certify(src, target)
        except Refused as e:
            sys.stderr.buffer.write((u"[補證/拒絕] %s\n" % e).encode("utf-8"))
            return 1
        sys.stdout.buffer.write(
            (u"補證完成:%d 個檔案與上游逐位元組相同,已發 provenance。\n"
             u"(只寫 .dev/provenance.jsonl,repo 內容一個位元組都沒動;"
             u"漂移的檔案不發證。)\n" % len(issued)).encode("utf-8"))
        return 0
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
