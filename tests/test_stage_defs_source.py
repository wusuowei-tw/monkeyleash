# -*- coding: utf-8 -*-
"""票 133 批二 #8/#9 —— 站別定義的來源綁執行上下文(**紅燈先行**)。

裁決(2026-09-22,採 B3,逐字見票 133〈#8/#9 的裁決〉):

  寫入:#8/#9 共用**同一次工作樹**站別定義讀取。
  提交:#8/#9 共用**同一次 index**站別定義讀取。
  `load_stage_defs` **預設維持工作樹**,其他呼叫端不連帶改變。
  來源語意:**提交時的站別定義以 index 為準**;工作樹尚未暫存的放寬,
  不影響本次提交(C3 在提交時不取得 research 豁免是**預期行為**)。

⚠ **本檔寫在 `gate.py` 被改之前,而且 `gate.py` 一個字未改。**
   紅燈必須來自**預期行為差異** —— 本檔的每一條行為斷言都走
   `check()` / `stage_allows_src_write()` / `mode_pre_commit()` 的**現有介面**,
   不依賴尚不存在的 `source` 參數。
   **需要新介面才驗得了的兩條**(規格 1 的 `*_REL`、規格 5 的不合法 `source` 值)
   放在 `TestContractPendingTheNewInterface`,以**執行期偵測**決定跑或跳過 ——
   `TypeError` / `AttributeError` **不算有效紅燈**(票面逐字)。

## 為什麼是真 git repo 而不是替身

被判的正是「index 那一份 vs 工作樹那一份」。用替身換掉讀取就等於把
**要測的那個差異**替身掉了 —— 剩下的只證明替身會回傳它被設定的值。
作法沿用批一 ④(R6)的 `r6_repo`:真 repo、`build(index=…, worktree=…)`。

## `ROOT` 與 `STAGES_DEF` 一起 patch

與 `r6_repo` 逐字同一個理由:`STAGES_DEF` 是 **import 時凍結的絕對路徑**,
只 patch `ROOT` 會讓兩條路指向不同 repo(批一 ① 那個 `../../..` 逃逸陷阱)。
**規格 1 要的「工作樹路徑由 `ROOT` 衍生」另有專屬一格**
(`TestTheWorktreePathDerivesFromRoot`),那一格**刻意只 patch `ROOT`**。
"""

import importlib.util
import inspect
import io
import json
import os
import pathlib
import re
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

STAGES_REL = ".agents/pipeline-stages.yaml"
TARGET_REL = "research/probe.py"


def _load():
    spec = importlib.util.spec_from_file_location(
        "gate_stage_defs_source", ROOT / ".claude" / "hooks" / "gate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gate = _load()


def _git(args, cwd):
    return subprocess.run(["git"] + list(args), cwd=str(cwd),
                          capture_output=True, check=False)


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with io.open(str(path), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def stage_yaml(allows=True, scope="research/", exempts=True):
    """站別定義。`None` = **該欄位不存在**(不是 `false`)。

    **永遠保留一個 `implement`(`allows_src_write: true`)** ——
    否則 `load_stage_defs()` 的「沒有任何站宣告 allows_src_write」會整份
    fail-closed,案例之間就歸因不了(是這一格的設計造成的,還是全域 fail-closed)。
    """
    out = ["stages:",
           "  - id: idle", "    skill: null", "    zh: 待命",
           "    allows_src_write: false", "",
           "  - id: research", "    skill: research", "    zh: 探索研究"]
    if allows is not None:
        out.append("    allows_src_write: %s" % ("true" if allows else "false"))
    if scope is not None:
        out.append("    src_write_scope: %s" % scope)
    if exempts is not None:
        out.append("    exempts_r3_in_scope: %s" % ("true" if exempts else "false"))
    out += ["", "  - id: implement", "    skill: implement", "    zh: TDD實作",
            "    allows_src_write: true", ""]
    return "\n".join(out) + "\n"


BASE = dict(allows=True, scope="research/", exempts=True)


def variant(**over):
    kw = dict(BASE)
    kw.update(over)
    return stage_yaml(**kw)


@pytest.fixture
def defs_repo(tmp_path, monkeypatch):
    """真 repo + `build(index_yaml, worktree_yaml, stage=…)`。

    回 `(repo, build)`。`build` 回一個 `probe`(dict),裡面是**這一格的前提**,
    每個案例都 assert 它 —— 前提在執行期斷言,不是事後推論。
    """
    repo = tmp_path / "defsrepo"
    repo.mkdir()
    for c in ("init -q", "config user.email t@t", "config user.name t"):
        _git(c.split(), repo)
    _write(repo / "pkg" / "base.py", "y = 2\n")
    # legacy 清單:**刻意不含目標** ⇒ `legacy_exemption` 走「未命中 ⇒ 不查樹」
    # 那一條(docstring 逐字),一個子行程都不跑,也就不可能掩蓋目標。
    _write(repo / ".agents" / "legacy-no-redlight.txt",
           "# go-live: (本格不使用)\npkg/base.py\n")
    _git(["add", "-A"], repo)
    _git(["commit", "-qm", "base"], repo)

    stages_path = repo / ".agents" / "pipeline-stages.yaml"
    pipeline_path = repo / ".dev" / "pipeline.json"
    # **cwd 也要進臨時 repo**,不只是 patch `ROOT`。
    # `rel()` 走的是 `os.path.relpath(os.path.abspath(path), ROOT)`,而
    # `os.path.abspath` 用的是**行程 cwd**,不是 `ROOT` ——
    # cwd 留在真 repo 的話,相對路徑會被解析到真 repo 底下,
    # 再對臨時 `ROOT` 取 relpath 就吐出 `../../..`,`check()` 當場判定
    # 「repo 以外的路徑不歸這裡管」而回 `None`。
    # **那會讓每一個「該擋」的斷言紅、每一個「該放行」的斷言綠** ——
    # 綠的那一半看起來完全正常,而它證明的是「路徑逃出去了」。
    # 這也是 `mode_pre_commit()` 的真實執行條件(cwd = repo 根)。
    monkeypatch.chdir(str(repo))
    monkeypatch.setattr(gate, "ROOT", str(repo))
    monkeypatch.setattr(gate, "STAGES_DEF", str(stages_path))
    monkeypatch.setattr(gate, "LEGACY_LIST",
                        str(repo / ".agents" / "legacy-no-redlight.txt"))
    monkeypatch.setattr(gate, "PIPELINE", str(pipeline_path))

    def build(index_yaml, worktree_yaml, stage="research", add_target=True,
              stage_in_index=True):
        if stage_in_index:
            _write(stages_path, index_yaml)
            _git(["add", "-f", "--", STAGES_REL], repo)
        _write(stages_path, worktree_yaml)
        _write(repo / "research" / "probe.py", "x = 1\n")   # 無 tests/test_probe.py
        if add_target:
            _git(["add", "-f", "--", TARGET_REL], repo)
        _write(pipeline_path, json.dumps(
            {"current_stage": stage, "feature": "probefeat", "ticket_id": None},
            ensure_ascii=False) + "\n")

        staged = subprocess.run(["git", "show", ":%s" % STAGES_REL], cwd=str(repo),
                                capture_output=True)
        probe = {
            "stage": gate.load_stage()[0],
            "index_yaml": (staged.stdout.decode("utf-8")
                           if staged.returncode == 0 else None),
            "worktree_yaml": io.open(str(stages_path), encoding="utf-8").read(),
            "target_in_staged": TARGET_REL in gate.staged_paths(cwd=str(repo)),
            "staged_paths": sorted(gate.staged_paths(cwd=str(repo))),
            "legacy": gate.legacy_exemption(TARGET_REL, path=gate.LEGACY_LIST),
            "test_file_absent": not (repo / "tests" / "test_probe.py").exists(),
            # ⚠ **用的是測試自己餵給 `check()` 的那個字串**,不是另外組一個
            # 絕對路徑去問。兩者會給出不同答案(絕對路徑那條永遠對),
            # 而**對一個沒被使用的運算式做前提檢查,證明不了被使用的那個**。
            "rel_of_target": gate.rel(TARGET_REL),
        }
        return probe

    return repo, build


def assert_premises(probe, expect_stage="research", expect_target_staged=True):
    """**每一格都跑** —— 上一輪的 rig 缺陷 2 就是死在沒有這一段:
    目標沒進 staged 清單時,輸出**看起來完全正常**,而被量的東西不在裡面。
    """
    assert probe["stage"] == expect_stage, (
        u"站別前提垮了:%r" % (probe["stage"],))
    assert probe["rel_of_target"] == TARGET_REL, (
        u"目標逃出 repo 了(rel 反算出逃逸路徑):%r" % (probe["rel_of_target"],))
    assert probe["test_file_absent"], u"tests/test_probe.py 竟然存在 —— R3 前提垮了"
    assert probe["legacy"] == (False, None), (
        u"legacy(#10)竟然命中或擋下,會掩蓋目標:%r" % (probe["legacy"],))
    if expect_target_staged:
        assert probe["target_in_staged"], (
            u"目標不在 staged 清單裡,提交時點根本沒判到它:%r"
            % (probe["staged_paths"],))


def commit_check(path_rel=TARGET_REL):
    return gate.check(path_rel, None, at_commit=True, trace=[], exemptions=[])


def write_check(path_rel=TARGET_REL, content="x = 1\n"):
    return gate.check(path_rel, content, at_commit=False, trace=[], exemptions=[])


# ─────────────────────────────────────────────────────────────────────────────
# C3 —— 本裁決的核心格:工作樹放寬但**尚未暫存**
# ─────────────────────────────────────────────────────────────────────────────
class TestC3TheUnstagedLoosenDoesNotReachTheCommit:
    """index 沒有 `exempts_r3_in_scope`、工作樹有(改了還沒 `git add`)。

    裁決逐字:「**C3 在提交時不取得 research 豁免是預期行為;
    工作樹尚未暫存的定義放寬,不應影響本次提交。**」
    """

    def test_the_write_still_gets_the_exemption(self, defs_repo):
        """**綠燈側**:寫入照工作樹 ⇒ 豁免照常成立。B3 不得把寫入一起收緊。"""
        _repo, build = defs_repo
        assert_premises(build(index_yaml=variant(exempts=None),
                              worktree_yaml=variant()))
        assert write_check() is None, u"寫入時點被收緊了 —— B3 只換提交那一側"

    def test_the_commit_must_not_get_the_exemption(self, defs_repo):
        """🔴 **本格本體**:提交照 index ⇒ 拿不到豁免,必須被 R3 擋。

        現行讀工作樹 ⇒ 回 `None` ⇒ 一次提交靠**不會進這個 commit 的定義**過關。
        """
        _repo, build = defs_repo
        assert_premises(build(index_yaml=variant(exempts=None),
                              worktree_yaml=variant()))
        msg = commit_check()
        assert msg, (u"提交時拿到了 research 豁免,而授予它的那一行 "
                     u"`exempts_r3_in_scope` 只在工作樹、不在 index —— "
                     u"判的是一份不會進這次 commit 的定義")
        assert "R3" in msg, u"擋下了,但不是 R3:%r" % msg


# ─────────────────────────────────────────────────────────────────────────────
# C2 —— 反方向:index 放寬、工作樹較嚴
# ─────────────────────────────────────────────────────────────────────────────
class TestC2TheCommitFollowsTheIndexNotTheStricterWorktree:
    """**鑑別格**:C3 只證明「提交變嚴」,單看它分不出
    「真的改讀 index」與「提交時一律不給豁免」—— 後者在本格會現形。
    """

    def test_the_commit_takes_the_index_exemption(self, defs_repo):
        """🔴 index 有豁免、工作樹沒有 ⇒ 提交必須**放行**。"""
        _repo, build = defs_repo
        assert_premises(build(index_yaml=variant(),
                              worktree_yaml=variant(exempts=None)))
        msg = commit_check()
        assert msg is None, (
            u"index 的定義授予了 research 豁免,提交卻被擋 —— "
            u"提交判的仍是工作樹那份(較嚴)。這是誤擋:%r" % msg)

    def test_the_write_follows_the_stricter_worktree(self, defs_repo):
        """**綠燈側**:寫入照工作樹 ⇒ 沒有豁免,照常被 R3 擋。"""
        _repo, build = defs_repo
        assert_premises(build(index_yaml=variant(),
                              worktree_yaml=variant(exempts=None)))
        msg = write_check()
        assert msg and "R3" in msg, u"寫入時點改讀 index 了 —— 不該動那一側:%r" % msg


# ─────────────────────────────────────────────────────────────────────────────
# C4 / C6 —— #8 那一半(`allows_src_write` 與 `src_write_scope`)
# ─────────────────────────────────────────────────────────────────────────────
class TestC4WriteKeepsTheWorktreeCommitUsesTheIndex:
    """工作樹說這一站不可寫、index 說可寫。"""

    def test_the_write_is_blocked_by_the_worktree(self, defs_repo):
        """**綠燈側**:寫入照工作樹 ⇒ `[R2]`。"""
        _repo, build = defs_repo
        assert_premises(build(index_yaml=variant(),
                              worktree_yaml=variant(allows=False)))
        msg = write_check()
        assert msg and "R2" in msg, u"寫入時點沒照工作樹:%r" % msg

    def test_the_commit_uses_the_index(self, defs_repo):
        """🔴 提交照 index(可寫 + 有豁免)⇒ 放行。"""
        _repo, build = defs_repo
        assert_premises(build(index_yaml=variant(),
                              worktree_yaml=variant(allows=False)))
        msg = commit_check()
        assert msg is None, (
            u"index 說 research 可寫且豁免 R3,提交卻被擋 —— 判的是工作樹:%r" % msg)


class TestC6TheScopeBranchAlsoSwitchesSource:
    """`src_write_scope` 的分支排在 #9 之前 —— 它也吃同一份定義。"""

    def test_the_write_is_blocked_by_the_worktree_scope(self, defs_repo):
        """**綠燈側**:工作樹 scope=`lab/` ⇒ 寫 `research/` 被範圍擋。"""
        _repo, build = defs_repo
        assert_premises(build(index_yaml=variant(),
                              worktree_yaml=variant(scope="lab/")))
        msg = write_check()
        assert msg and "R2" in msg, u"寫入時點沒照工作樹的 scope:%r" % msg

    def test_the_commit_uses_the_index_scope(self, defs_repo):
        """🔴 提交照 index 的 scope=`research/` ⇒ 通過範圍、拿到豁免。"""
        _repo, build = defs_repo
        assert_premises(build(index_yaml=variant(),
                              worktree_yaml=variant(scope="lab/")))
        msg = commit_check()
        assert msg is None, (
            u"index 的 scope 是 research/,提交卻被範圍擋 —— 判的是工作樹:%r" % msg)


# ─────────────────────────────────────────────────────────────────────────────
# C7 —— 兩時點各自用**單一**版本,不混搭
# ─────────────────────────────────────────────────────────────────────────────
class TestC7EachTimepointUsesExactlyOneVersion:
    """index 只有 `exempts`(沒有 `allows`)、工作樹只有 `allows`(沒有 `exempts`)。

    **這一格是為什麼 B1(只換 #9)被排除的那一格**:
    前一輪實測 B1 在這裡用一份「這一站不可寫」的定義發出了 research 豁免。
    兩個時點的正確答案因此是**兩個不同的單一版本**,而不是任何一種混搭。
    """

    def _build(self, build):
        return build(index_yaml=stage_yaml(allows=None, scope=None, exempts=True),
                     worktree_yaml=stage_yaml(allows=True, scope=None, exempts=None))

    def test_the_write_uses_only_the_worktree(self, defs_repo):
        """**綠燈側**:工作樹說可寫、沒有豁免 ⇒ 過 R2、被 R3 擋。

        **不得**是 `[R2]` —— 那表示它拿了 index 的「沒有 allows」。
        """
        _repo, build = defs_repo
        assert_premises(self._build(build))
        msg = write_check()
        assert msg and "R3" in msg, (
            u"寫入時點沒有單獨用工作樹那一版(混搭或用了 index):%r" % msg)

    def test_the_commit_uses_only_the_index(self, defs_repo):
        """🔴 index 沒宣告 `allows_src_write` ⇒ research 是前置站 ⇒ `[R2/commit]`。

        **不得**是 `[R3]` —— 那表示它拿了工作樹的 `allows`;
        **更不得**放行 —— 那表示它混搭了 index 的 `exempts` 與工作樹的 `allows`。
        """
        _repo, build = defs_repo
        assert_premises(self._build(build))
        msg = commit_check()
        assert msg, u"提交被放行 —— 混搭了兩版定義(index 的豁免 × 工作樹的可寫)"
        assert "R2" in msg, (
            u"提交沒有單獨用 index 那一版:index 沒宣告 allows_src_write,"
            u"research 就是前置站,應該是 R2 那一族:%r" % msg)


# ─────────────────────────────────────────────────────────────────────────────
# 規格 2 —— 其他呼叫端的**預設來源反控**
# ─────────────────────────────────────────────────────────────────────────────
class TestStageAllowsSrcWriteKeepsTheWorktreeDefault:
    """`load_stage_defs` **預設維持工作樹**,其他呼叫端不連帶改變。

    ⚠ **本格現在就是綠的,而它非有不可** —— 它守的是
    「修 `check()` 的時候順手把預設值一起換掉」。
    前一輪實測:候選 **B2**(無條件讀 index)正是這樣,
    `stage_allows_src_write('research')` 由 `False` 變成 `True`,
    而 `status.py:788` 的 authority 欄位**一個字沒改就換了答案**。
    """

    def test_the_default_source_is_still_the_worktree(self, defs_repo):
        _repo, build = defs_repo
        probe = build(index_yaml=variant(allows=True),
                      worktree_yaml=variant(allows=False))
        assert_premises(probe)
        assert gate.stage_allows_src_write("research") is False, (
            u"index 說可寫、工作樹說不可寫,而它回了 index 的答案 —— "
            u"預設來源被連帶換掉了(status.py:788 的 authority 欄位會跟著變)")

    def test_it_still_reads_the_worktree_when_the_two_agree(self, defs_repo):
        """反向:工作樹說可寫就要回 True —— 不能靠「一律 False」混過上一格。"""
        _repo, build = defs_repo
        assert_premises(build(index_yaml=variant(allows=False),
                              worktree_yaml=variant(allows=True)))
        assert gate.stage_allows_src_write("research") is True


# ─────────────────────────────────────────────────────────────────────────────
# 規格 5 —— index 不可用/無效時 **fail-closed,不退回工作樹**
# ─────────────────────────────────────────────────────────────────────────────
class TestIndexUnusableMustNotFallBackToTheWorktree:
    """**工作樹是合法的** —— 所以「放行」與「照工作樹判」在這裡長得一樣,
    而兩者都是退回工作樹。斷言要的是**擋下**。
    """

    def test_a_definition_missing_from_the_index_is_fail_closed(self, defs_repo):
        """🔴 定義檔從未 `git add`,工作樹那份完全合法 ⇒ 提交必須擋。"""
        _repo, build = defs_repo
        probe = build(index_yaml=variant(), worktree_yaml=variant(),
                      stage_in_index=False)
        assert probe["index_yaml"] is None, (
            u"前提垮了:定義檔竟然在 index 裡 —— 本格要的是它不在")
        assert_premises(probe)
        msg = commit_check()
        assert msg, (u"定義檔不在 index 裡,提交卻放行了 —— "
                     u"退回工作樹判了,而工作樹那份不會進這次 commit")

    def test_an_unparseable_index_definition_is_fail_closed(self, defs_repo):
        """🔴 index 那份是壞 YAML、工作樹那份合法 ⇒ 提交必須擋。"""
        _repo, build = defs_repo
        probe = build(index_yaml="stages: [ 這不是合法的 yaml\n",
                      worktree_yaml=variant())
        assert_premises(probe)
        msg = commit_check()
        assert msg, (u"index 的定義解析失敗,提交卻放行了 —— 退回工作樹判了")

    def test_the_write_is_unaffected_by_a_broken_index(self, defs_repo):
        """**鑑別格**:寫入照工作樹 ⇒ index 壞掉不該影響它。

        少了這一格,「提交與寫入都一律擋」也能讓上面兩格變綠。
        """
        _repo, build = defs_repo
        assert_premises(build(index_yaml="stages: [ 這不是合法的 yaml\n",
                              worktree_yaml=variant()))
        assert write_check() is None, u"index 壞掉波及了寫入時點"


# ─────────────────────────────────────────────────────────────────────────────
# 規格 3 —— 提交判定的來源**須能看懂**(裁定:語意要求,非逐字)
# ─────────────────────────────────────────────────────────────────────────────
_PROMISE = re.compile(
    u"git add[^\n]{0,24}(就|即可|便|一定|必)[^\n]{0,12}(通過|過關|放行|會綠|沒事)")


def assert_names_its_source(msg):
    """裁決逐字要求的三件事,**綁語意不綁字面**(用字可自行決定)。

    ⚠ 條件 (3) 是**否定式**,用的是一組「承諾句型」的樣式比對 ——
    **樣式比對的漏是未知的**,所以這一條只擋得住寫成那幾種句型的承諾,
    不等於證明了訊息沒有以別的寫法做出承諾。本檔不宣稱後者。
    """
    assert msg, u"沒有擋下,談不上訊息"
    assert ("index" in msg) or ("暫存區" in msg), (
        u"(1) 訊息沒說出本次站別定義取自暫存區(index):%r" % msg)
    assert ("未暫存" in msg) or ("尚未暫存" in msg) or ("還沒" in msg), (
        u"(2) 訊息沒說出工作樹未暫存的定義修改不影響本次提交:%r" % msg)
    assert _PROMISE.search(msg) is None, (
        u"(3) 訊息承諾了 `git add` 之後一定通過 —— 不得承諾:%r" % msg)


class TestTheCommitBlockNamesItsSource:

    def test_the_r3_block_names_its_source(self, defs_repo):
        """🔴 C3 提交的 `[R3]` 要說得出它判的是哪一份定義。"""
        _repo, build = defs_repo
        assert_premises(build(index_yaml=variant(exempts=None),
                              worktree_yaml=variant()))
        assert_names_its_source(commit_check())

    def test_the_r2_block_names_its_source(self, defs_repo):
        """🔴 C7 提交的 `[R2/commit]` 同樣要說得出來源。"""
        _repo, build = defs_repo
        assert_premises(build(
            index_yaml=stage_yaml(allows=None, scope=None, exempts=True),
            worktree_yaml=stage_yaml(allows=True, scope=None, exempts=None)))
        assert_names_its_source(commit_check())

    def test_the_missing_index_message_names_the_source_too(self, defs_repo):
        """🔴 規格 3 末句:index 缺失/解析失敗的訊息**須清楚標明來源**。"""
        _repo, build = defs_repo
        probe = build(index_yaml=variant(), worktree_yaml=variant(),
                      stage_in_index=False)
        assert probe["index_yaml"] is None
        msg = commit_check()
        assert msg, u"定義檔不在 index 裡卻放行了"
        assert ("index" in msg) or ("暫存區" in msg), (
            u"沒說出讀不到的是 index 那一份:%r" % msg)

    def test_the_write_block_does_not_claim_an_index_source(self, defs_repo):
        """**鑑別格**:寫入判的是工作樹 —— 訊息不得宣稱來自暫存區。

        少了這一格,「每一則訊息都貼上同一句話」也能讓上面三格變綠,
        而那會在寫入時點說一句**假話**。
        """
        _repo, build = defs_repo
        assert_premises(build(index_yaml=variant(),
                              worktree_yaml=variant(allows=False)))
        msg = write_check()
        assert msg, u"寫入沒被擋,前提垮了"
        assert "暫存區" not in msg and "index" not in msg, (
            u"寫入時點判的是工作樹,訊息卻宣稱來自暫存區:%r" % msg)


# ─────────────────────────────────────────────────────────────────────────────
# 規格 4 —— 每次 `check()` 只有**一次**權威定義讀取
# ─────────────────────────────────────────────────────────────────────────────
class TestOneAuthoritativeReadPerCheck:
    """⚠ **本格現在就是綠的** —— 它守的是修法**不要**多讀一次。

    「#8/#9 共用同一個 `stages`」這半**不是由本格證明的**:
    本格數的是呼叫次數。共用那一半由 C7 兩格承擔 ——
    兩個消費端若各拿各的來源,C7 必然現形(前一輪 B1 就是那樣被抓到的)。
    **保證範圍是單次 `check()`,不是整次提交快照**,所以本格逐次量,不跨 `check()` 累計。
    """

    def _count(self, monkeypatch, at_commit):
        calls = []
        real = gate.load_stage_defs

        def counting(*a, **kw):
            calls.append((a, kw))
            return real(*a, **kw)

        monkeypatch.setattr(gate, "load_stage_defs", counting)
        gate.check(TARGET_REL, None if at_commit else "x = 1\n",
                   at_commit=at_commit, trace=[], exemptions=[])
        return calls

    def test_the_write_reads_the_definition_once(self, defs_repo, monkeypatch):
        _repo, build = defs_repo
        assert_premises(build(index_yaml=variant(), worktree_yaml=variant()))
        calls = self._count(monkeypatch, at_commit=False)
        assert len(calls) == 1, u"一次 check() 讀了 %d 次站別定義" % len(calls)

    def test_the_commit_reads_the_definition_once(self, defs_repo, monkeypatch):
        _repo, build = defs_repo
        assert_premises(build(index_yaml=variant(), worktree_yaml=variant()))
        calls = self._count(monkeypatch, at_commit=True)
        assert len(calls) == 1, u"一次 check() 讀了 %d 次站別定義" % len(calls)


# ─────────────────────────────────────────────────────────────────────────────
# 隔離 `mode_pre_commit()` 正反控
# ─────────────────────────────────────────────────────────────────────────────
_PRE_COMMIT_STUBS = {
    "upstream_shadow_violation": lambda *a, **k: (None, None),
    "check_skill_copies": lambda *a, **k: [],
    "check_third_axis_mount": lambda *a, **k: [],
    "check_to_spec_override": lambda *a, **k: [],
    "check_friction_numbers": lambda *a, **k: [],
    "check_legacy_list": lambda *a, **k: [],
    "shadow_active": lambda *a, **k: False,
}


@pytest.fixture
def pre_commit(monkeypatch):
    """把 `mode_pre_commit()` 收到只剩 `check()` 那一圈。

    **替身逐項列在 `_PRE_COMMIT_STUBS`**,不是一句「其他都 mock 掉」——
    沒有被列出來的東西就是真的在跑,而讀的人有權知道是哪些。
    `check_legacy_list`(R6)這一輪**也替身**:本檔的 rig 用的是假 go-live sha,
    留著它只會讓 R6 對一個不存在的 commit 紅,**蓋掉要測的東西**
    (上一輪 rig 缺陷 1 就是這個)。
    """
    for name, fn in _PRE_COMMIT_STUBS.items():
        monkeypatch.setattr(gate, name, fn)

    def run(repo):
        buf = io.BytesIO()

        class _Err(object):
            buffer = buf

            def write(self, s):
                buf.write(s.encode("utf-8"))

            def flush(self):
                pass

        monkeypatch.setattr(gate.sys, "stderr", _Err())
        monkeypatch.chdir(str(repo))
        rc = gate.mode_pre_commit()
        return rc, buf.getvalue().decode("utf-8", "replace")

    return run


class TestIsolatedPreCommit:

    def test_the_unstaged_loosen_does_not_carry_the_commit(self, defs_repo,
                                                           pre_commit):
        """🔴 **正控**:C3 走到 `mode_pre_commit()` 必須回非 0 並點名目標。"""
        repo, build = defs_repo
        probe = build(index_yaml=variant(exempts=None), worktree_yaml=variant())
        assert_premises(probe)
        rc, err = pre_commit(repo)
        assert probe["target_in_staged"], (
            u"目標不在 staged 清單,這一格根本沒判到它:%r" % (probe["staged_paths"],))
        assert rc != 0, (
            u"pre-commit 放行了,而授予豁免的那一行只在工作樹、不在 index。"
            u"staged=%r stderr=%r" % (probe["staged_paths"], err))
        assert TARGET_REL in err, u"擋下了但沒點名目標:%r" % err
        assert "R3" in err, u"擋下了但不是 R3:%r" % err

    def test_a_definition_that_is_staged_passes(self, defs_repo, pre_commit):
        """**反控**:同一份定義兩邊一致(且授予豁免)⇒ 必須回 0。

        少了這一格,「提交一律擋」也能讓正控變綠,而那是誤擋。
        """
        repo, build = defs_repo
        probe = build(index_yaml=variant(), worktree_yaml=variant())
        assert_premises(probe)
        rc, err = pre_commit(repo)
        assert rc == 0, (
            u"兩版定義一致且授予 research 豁免,pre-commit 卻擋下 —— 誤擋。"
            u"staged=%r stderr=%r" % (probe["staged_paths"], err))

    def test_the_cwd_and_staged_list_are_what_we_think(self, defs_repo,
                                                       pre_commit):
        """前提本身也要有一格 —— 不是靠別格的 assert 順帶證明。"""
        repo, build = defs_repo
        probe = build(index_yaml=variant(), worktree_yaml=variant())
        rc, _err = pre_commit(repo)
        assert pathlib.Path.cwd() == pathlib.Path(str(repo)), (
            u"cwd 不是臨時 repo:%r" % (pathlib.Path.cwd(),))
        assert probe["staged_paths"] == sorted([STAGES_REL, TARGET_REL]), (
            u"staged 清單不是預期的兩筆:%r" % (probe["staged_paths"],))
        assert rc == 0


# ─────────────────────────────────────────────────────────────────────────────
# 需要新介面才驗得了的兩條 —— **契約案例,不是有效紅燈**
# ─────────────────────────────────────────────────────────────────────────────
class TestContractPendingTheNewInterface:
    """票面逐字:「**不能用新增 `source` 參數尚不存在造成的 `TypeError` 充當紅燈**」。

    所以本類的每一格都**先偵測介面在不在**:不在就 `skip`(理由寫明),
    在了就**真的跑那條斷言**。

    **為什麼是執行期偵測而不是寫死 `skip`**:寫死的話,介面落地那天
    沒有任何東西會提醒人回來拿掉它 —— 那正是 `F-086`
    (「修好偵測器之後回頭重掃」)家族的形狀。**自己會醒來的跳過才不會被遺忘。**
    """

    def test_an_invalid_source_value_must_not_silently_fall_back(self, defs_repo):
        """規格 5 後半:不合法 `source` 值**不得靜默退回工作樹**。

        原型的 `else` 分支正是會靜默退回的寫法 —— **它不會自己出聲**。
        """
        if "source" not in inspect.signature(gate.load_stage_defs).parameters:
            pytest.skip(
                u"契約案例:`load_stage_defs` 還沒有 `source` 參數。"
                u"介面一加上去本格自己會醒 —— 屆時要驗的是:"
                u"不合法值必須出聲(拋例外或回 err),不得靜默走 worktree 那條。")
        _repo, build = defs_repo
        assert_premises(build(index_yaml=variant(), worktree_yaml=variant()))
        try:
            stages, _flow, err = gate.load_stage_defs(source="這不是合法來源")
        except (ValueError, AssertionError):
            return                      # 出聲了 —— 合格
        assert err, (
            u"不合法的 source 值被靜默接受了,而且沒有 err —— "
            u"它退回了工作樹那條(stages=%r)" % (stages,))

    def test_the_relative_path_constant_is_the_single_source(self):
        """規格 1:單一 `*_REL` 常數作為 repo 相對路徑來源(**值**的那一半)。

        ⚠ 規格逐字:「**不是禁止常數本身含路徑字串**」——
        所以本格驗的是「有一個相對常數、而且它是 repo 相對路徑」,不是去禁止什麼。

        ⚠ **本格只驗值,證明不了它是實際讀取來源** ——
        那一半在 `TestContractTheRelativeConstantIsTheRealSource`。
        兩格分開是因為它們失敗時要指向不同的地方:
        這一格紅 = 常數本身錯;那一格紅 = 常數是對的但沒人用它。

        **介面已落地,所以不再 skip** —— 缺失時以明確斷言失敗,
        不以 `AttributeError` 充當證據。
        """
        assert hasattr(gate, "STAGES_DEF_REL"), (
            u"`gate.STAGES_DEF_REL` 不存在 —— 站別定義檔沒有單一相對路徑來源常數")
        rel_value = gate.STAGES_DEF_REL
        assert rel_value == STAGES_REL, (
            u"相對常數的值不是預期的 repo 相對路徑:%r" % (rel_value,))
        assert not pathlib.PurePath(rel_value).is_absolute(), (
            u"相對常數竟然是絕對路徑:%r" % (rel_value,))


# ─────────────────────────────────────────────────────────────────────────────
# W8:相對常數**真的是**讀取來源 —— 不是擺著好看的第二份字面
# ─────────────────────────────────────────────────────────────────────────────
class TestContractTheRelativeConstantIsTheRealSource:
    """**「有一個正確的常數」與「讀取真的用它」是兩件事。**

    只比對常數的值,擋不住這個形狀:
    **新增一個正確的 `*_REL` 常數,而實際讀取仍用另一份寫死的字面路徑。**
    那時兩個值**碰巧相等**,值比對全綠,而常數對行為**沒有任何影響力**。

    所以本類驗的是**依賴**:把常數換掉,讀取要跟著換。
    （`_REL` 換掉之後真 repo 那一份就不該再被讀到 —— 這是「跟著換」的可觀測面。)
    """

    def test_the_worktree_path_is_derived_from_root_and_the_constant(self):
        """**載入時**由 `ROOT` 與相對常數衍生 —— 驗的是這個關係,不是動態重算。

        錯誤變體「保留正確相對常數,但工作樹路徑改成固定絕對路徑」
        會讓這一格紅:那時 `STAGES_DEF` 與 `join(ROOT, *REL)` 不再相等。
        """
        assert gate.STAGES_DEF == os.path.join(
            gate.ROOT, *gate.STAGES_DEF_REL.split("/")), (
            u"`STAGES_DEF` 不是由 `ROOT` + `STAGES_DEF_REL` 衍生出來的:\n"
            u"  STAGES_DEF     = %r\n  ROOT + REL     = %r"
            % (gate.STAGES_DEF,
               os.path.join(gate.ROOT, *gate.STAGES_DEF_REL.split("/"))))

    def test_the_index_read_follows_the_relative_constant(self, defs_repo,
                                                          monkeypatch):
        """**index 讀取要用同一個相對常數** —— 換掉它,讀取要跟著換。

        錯誤變體「index 讀取改回獨立路徑字面」會讓這一格紅:
        常數換到 `.agents/moved-stages.yaml`,而讀取仍去問
        `git show :.agents/pipeline-stages.yaml`。

        **單比對兩個值相等不夠**,所以這裡換的是常數、看的是行為。
        """
        repo, build = defs_repo
        # 先把正常那一份建好(index 與工作樹都有 `.agents/pipeline-stages.yaml`)
        assert_premises(build(index_yaml=variant(), worktree_yaml=variant()))

        moved_rel = ".agents/moved-stages.yaml"
        moved_yaml = variant().replace("id: research", "id: 只在搬走的那一份裡")
        _write(repo / ".agents" / "moved-stages.yaml", moved_yaml)
        _git(["add", "-f", "--", moved_rel], repo)
        # 原本那一份**留在原地**:讀取若用寫死的字面,它會讀到這一份而不是搬走的那份。
        monkeypatch.setattr(gate, "STAGES_DEF_REL", moved_rel)

        stages, _flow, err = gate.load_stage_defs(source="index")
        assert err is None, u"換了相對常數之後讀不到 index 那一份:%r" % (err,)
        ids = [s.get("id") for s in stages]
        assert "只在搬走的那一份裡" in ids, (
            u"`STAGES_DEF_REL` 已換成 %r,index 讀取卻仍去拿原本那一份 —— "
            u"常數不是實際讀取來源(讀取端另有一份寫死的字面路徑):%r"
            % (moved_rel, ids))

    def test_the_index_read_reports_the_constant_it_used(self, defs_repo,
                                                         monkeypatch):
        """反控:常數指到 index 裡沒有的路徑 ⇒ fail-closed,而且訊息點名**那個**路徑。

        少了這一格,「讀取端完全忽略常數」在上一格會紅、在這一格卻可能碰巧綠 ——
        兩格方向相反,一起才鎖得住。
        """
        repo, build = defs_repo
        assert_premises(build(index_yaml=variant(), worktree_yaml=variant()))
        missing_rel = ".agents/never-staged-stages.yaml"
        monkeypatch.setattr(gate, "STAGES_DEF_REL", missing_rel)
        stages, _flow, err = gate.load_stage_defs(source="index")
        assert err, u"常數指到 index 裡沒有的路徑,卻沒有 err"
        assert missing_rel in err, (
            u"訊息沒點名它實際用的那個相對路徑 —— 讀取端可能用的是別的字面:%r" % (err,))
        assert stages == []


# ─────────────────────────────────────────────────────────────────────────────
# 工作樹那一份:**明確指定的定義檔確實會被讀到**
# ─────────────────────────────────────────────────────────────────────────────
class TestTheSpecifiedWorktreeDefinitionIsRead:
    """依既有慣例**同時** patch `ROOT` 與 `STAGES_DEF`(同 `r6_repo` 的作法)。

    ## ⚠ 本類的契約在 2026-09-22 被**放寬過**,不得寫成「斷言完全沒有放寬」

    **原契約(較強)**:只 patch `ROOT`,要求 `load_stage_defs()` 在**呼叫時**
    重新由當下的 `ROOT` 算出工作樹路徑 —— 亦即「載入後只改 `ROOT`,
    `STAGES_DEF` 要自動重算」。

    **裁決(2026-09-22,規格時機的澄清)**:工作樹路徑**允許在模組載入時**
    由 `ROOT` 與 `STAGES_DEF_REL` 衍生,**不要求載入後只改 `ROOT` 就自動重算**;
    並**保留 `STAGES_DEF` 可單獨替換**的既有測試方式(票 99 那組靠它)。

    ⇒ 本類**改驗較弱的那件事**:*明確指定*的工作樹定義檔確實被讀取。
    「載入時由 `ROOT` + 相對常數衍生」那一半改由
    `TestContractTheRelativeConstantIsTheRealSource` 承擔。
    """

    def test_the_specified_worktree_definition_is_the_one_read(self, tmp_path,
                                                               monkeypatch):
        """指到哪一份工作樹定義,就要讀那一份(不是真 repo 那一份)。"""
        defs = tmp_path / ".agents" / "pipeline-stages.yaml"
        _write(defs, stage_yaml(allows=True, scope=None, exempts=None)
               .replace("id: research", "id: 只存在於這個臨時樹"))
        monkeypatch.setattr(gate, "ROOT", str(tmp_path))
        monkeypatch.setattr(gate, "STAGES_DEF", str(defs))
        stages, _flow, err = gate.load_stage_defs()
        assert err is None, u"讀不到指定的工作樹定義檔:%r" % (err,)
        ids = [s.get("id") for s in stages]
        assert "只存在於這個臨時樹" in ids, (
            u"`STAGES_DEF` 已指向這一份,它卻讀了別的地方的定義檔:%r" % (ids,))

    def test_a_missing_specified_definition_is_fail_closed(self, tmp_path,
                                                           monkeypatch):
        """反控:指定的那一份不存在 ⇒ 回 err,**不得**改讀真 repo 那一份。

        少了這一格,「其實還是讀真 repo」也能讓上一格綠 ——
        因為真 repo 那份也是合法的,只是 `ids` 不同。
        """
        monkeypatch.setattr(gate, "ROOT", str(tmp_path))
        monkeypatch.setattr(gate, "STAGES_DEF",
                            str(tmp_path / "no-such-file.yaml"))
        stages, _flow, err = gate.load_stage_defs()
        assert err, u"指定的定義檔不存在,卻沒有 err —— 它讀了別的地方"
        assert stages == []
