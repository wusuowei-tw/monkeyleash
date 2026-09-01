# -*- coding: utf-8 -*-
"""框架更新路徑(票 09 / ticket 01 的實作)。

只碰 `copy` 桶,而且**事後要驗別的桶沒被動到** —— 「我沒碰它」是宣稱,
「它的 hash 沒變」才是證據。這條區別是本檔大部分測試的形狀。

失效方向:這支工具會**覆寫別的 repo 的檔案**,所以每一個「不確定」
都往「不寫」倒:桶標不確定 -> 跳過;目標髒 -> 拒絕;
friction-log 有沒搬遷的本地條目 -> 拒絕並列出來。
"""

import hashlib
import importlib.util
import io
import json
import os
import pathlib
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "sync_under_test", ROOT / ".claude" / "portable" / "sync.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sync = _load()


MANIFEST = (
    ".claude/hooks/          copy\n"
    ".agents/portable-manifest.txt  ask\n"
    "docs/agents/friction-log.md    copy\n"
    "docs/agents/friction-local.md  generate\n"
    ".agents/legacy-no-redlight.txt generate\n"
    "CLAUDE.md               generate\n"
    "project_only.py         skip\n"
)


# 票 53 II —— fixture 的 CLAUDE.md 必須帶界線標記,因為**真實的下游一定帶**:
# `install.py` 走 `claude_md.render_for_new_repo()`,那個函式一律寫進兩個標記。
# 舊 fixture 用的是不帶標記的純文字,那不是任何真實安裝的形態。
BEGIN = "<!-- FRAMEWORK:BEGIN -->"
END = "<!-- FRAMEWORK:END -->"
CANON = "## 開發流程\n框架的正典段,各 repo 一份、應當完全相同。\n"


def _claude_md(canon, project):
    return "# 專案開發規範\n\n%s\n%s%s\n\n## 這個專案自己的規範\n\n%s\n" % (
        BEGIN, canon, END, project)


def _w(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    io.open(p, "w", encoding="utf-8", newline="\n").write(text)
    return p


def _h(root, rel):
    p = root / rel
    if not p.exists():
        return None
    return hashlib.sha256(io.open(p, "rb").read().replace(b"\r\n", b"\n")
                          ).hexdigest()


def _git(root, *a):
    return subprocess.run(["git"] + list(a), cwd=str(root), capture_output=True)


@pytest.fixture()
def pair(tmp_path):
    """來源(框架)與目標(已裝 repo),兩個真的 git repo。"""
    src, dst = tmp_path / "src", tmp_path / "dst"
    for r in (src, dst):
        r.mkdir()
        _git(r, "init", "-q")
        _git(r, "config", "user.email", "t@t")
        _git(r, "config", "user.name", "t")

    _w(src, ".agents/portable-manifest.txt", MANIFEST)
    _w(src, ".claude/hooks/gate.py", "# 新版\nx = 2\n")
    _w(src, ".claude/hooks/newfile.py", "# 全新\n")
    _w(src, "docs/agents/friction-log.md", "# Friction\n\n## F-001 一\n## F-002 二\n")
    _w(src, ".agents/legacy-no-redlight.txt", "# go-live: aaa\n")
    _w(src, "CLAUDE.md", _claude_md(CANON, "(還沒有。)"))
    _git(src, "add", "-A")
    _git(src, "commit", "-qm", "src")

    _w(dst, ".agents/portable-manifest.txt", MANIFEST + "tests/test_mine.py skip\n")
    _w(dst, ".claude/hooks/gate.py", "# 舊版\nx = 1\n")
    _w(dst, "docs/agents/friction-log.md", "# Friction\n\n## F-001 一\n")
    _w(dst, ".agents/legacy-no-redlight.txt", "# go-live: zzz\n目標自己的\n")
    _w(dst, "CLAUDE.md", _claude_md(CANON, "台股收盤 13:30。"))
    _w(dst, "project_only.py", "專案自己的\n")
    _git(dst, "add", "-A")
    _git(dst, "commit", "-qm", "dst")
    return src, dst


# ─────────────────────────────────────────────────────────────────────────────
# 一、只碰 copy 桶
# ─────────────────────────────────────────────────────────────────────────────

class TestOnlyTheCopyBucketMoves:

    def test_a_stale_copy_file_is_updated(self, pair):
        src, dst = pair
        sync.update(str(src), str(dst), apply=True)
        assert _h(dst, ".claude/hooks/gate.py") == _h(src, ".claude/hooks/gate.py")

    def test_a_missing_copy_file_is_added(self, pair):
        src, dst = pair
        sync.update(str(src), str(dst), apply=True)
        assert (dst / ".claude/hooks/newfile.py").exists()

    @pytest.mark.parametrize("rel", [
        ".agents/legacy-no-redlight.txt",   # generate:綁目標 repo
        "CLAUDE.md",                        # generate:專案段在裡面
        "project_only.py",                  # skip:專案自己的
    ])
    def test_other_buckets_are_byte_identical_afterwards(self, pair, rel):
        """**「我沒碰它」是宣稱,「hash 沒變」才是證據。**

        這條不是重複上一條的反面 —— 上一條驗的是「該動的動了」,
        這條驗的是「不該動的一個位元組都沒動」,兩者可以同時錯。
        """
        src, dst = pair
        before = _h(dst, rel)
        sync.update(str(src), str(dst), apply=True)
        assert _h(dst, rel) == before, "%s 被動到了" % rel

    def test_the_manifest_itself_is_never_copied(self, pair):
        """manifest 標 `ask` —— 它列著各 repo 自己的測試歸類,copy 會刪掉那些。

        擋住它的是**桶標本身**,不是工具裡另一份寫死的清單:
        兩份真相會分岔(F-058),而桶標才是這件事的定義來源。
        """
        src, dst = pair
        before = _h(dst, ".agents/portable-manifest.txt")
        sync.update(str(src), str(dst), apply=True)
        assert _h(dst, ".agents/portable-manifest.txt") == before

    def test_a_differing_ask_file_is_reported_not_silently_skipped(self, pair):
        """`ask` 桶有差異時要**說出來**。

        靜默跳過的話,manifest 的漂移永遠沒有人看得到 —— 而「兩邊不一致
        而沒有人知道」正是這條更新路徑要消滅的東西(ticket 01)。
        跳過是對的,不出聲不對。
        """
        src, dst = pair
        plan = sync.update(str(src), str(dst))
        assert ".agents/portable-manifest.txt" in plan.needs_decision, plan


class TestItWritesProvenance:
    """同步成品在下游會撞 R3(紅綠燈迴圈在上游,下游拿的是成品)。

    sync 寫入時同步產 provenance:上游 commit + 路徑。R3 據此改判
    「與上游一致 ⇒ 紅燈責任在上游」——**而驗證是對到上游的 git 物件**,
    不是採信這裡寫下的 hash。所以這個檔案是**控制**,不是證據。
    """

    def test_each_copied_file_gets_a_record(self, pair):
        src, dst = pair
        plan = sync.update(str(src), str(dst), apply=True)
        recs = [json.loads(l) for l in
                io.open(dst / ".dev" / "provenance.jsonl", encoding="utf-8")
                if l.strip()]
        paths = {r["path"] for r in recs}
        for rel in plan.changed + plan.added:
            assert rel in paths, rel

    def test_the_record_carries_the_upstream_commit_and_root(self, pair):
        src, dst = pair
        sync.update(str(src), str(dst), apply=True)
        rec = [json.loads(l) for l in
               io.open(dst / ".dev" / "provenance.jsonl", encoding="utf-8")
               if l.strip()][0]
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(src),
                              capture_output=True).stdout.decode().strip()
        assert rec["upstream_commit"] == head
        assert rec["upstream_path"] == rec["path"]

    def test_the_record_does_not_carry_a_local_path(self, pair):
        """**去識別化**:上游位置是本機設定,不該跟著 commit 進版控。

        同時也是控制強度的問題:欄位可寫的話,指向一個自己控制的 repo
        就能造出任意「上游物件」。位置住使用者層的 G1 保護指標檔。
        """
        src, dst = pair
        sync.update(str(src), str(dst), apply=True)
        text = io.open(dst / ".dev" / "provenance.jsonl", encoding="utf-8").read()
        assert "upstream_root" not in text, text
        assert str(src).replace("\\", "/") not in text.replace("\\", "/"), \
            "provenance 裡出現了本機絕對路徑"

    def test_a_file_not_committed_upstream_gets_no_record(self, pair):
        """**上游沒提交的東西不得產生 provenance。**

        provenance 的整個效力來自「可以去上游的 git 物件查證」。
        對一個只存在於上游工作樹、沒進物件庫的檔案發一張憑證,
        下游查證時必然失敗 —— 那不是保護,是製造一筆查不到的紀錄。
        """
        src, dst = pair
        _w(src, ".claude/hooks/uncommitted.py", "# 沒提交\n")
        sync.update(str(src), str(dst), apply=True)
        recs = [json.loads(l) for l in
                io.open(dst / ".dev" / "provenance.jsonl", encoding="utf-8")
                if l.strip()]
        assert not any(r["path"].endswith("uncommitted.py") for r in recs)


class TestPrecedenceHasOneImplementation:
    """**同一件事只有一個實作。**

    更新路徑與安裝器都要回答「這個檔案哪個桶」。兩份實作會漂移,而漂移的那天
    不會有人發現:一個把檔案搬過去、一個以為沒搬(F-058 的形狀)。
    sync 原本有自己的一份,而且漏掉了重複標記與不認得標記的檢查 ——
    於是格式錯誤在更新路徑上會靜默退化成 copy。
    """

    def _manifest_mod(self):
        spec = importlib.util.spec_from_file_location(
            "manifest_for_sync_test", ROOT / ".claude" / "portable" / "manifest.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_sync_delegates_to_the_manifest_module(self):
        assert getattr(sync, "manifest", None) is not None, \
            "sync 沒有用 manifest 的判定 —— 它自己有一份"

    def test_an_unknown_mark_is_refused_not_defaulted(self, tmp_path):
        """打錯的標記不得靜默退化成 copy —— 那會把該 generate 的檔案照抄過去。

        這條是「借用同一個實作」帶來的:sync 自己那份沒有這個檢查。
        """
        p = tmp_path / "m.txt"
        io.open(p, "w", encoding="utf-8", newline="\n").write("pkg/  copyy\n")
        with pytest.raises(ValueError):
            self._manifest_mod().load_table(str(p))

    def test_precedence_is_longest_prefix_not_read_order(self, tmp_path):
        """把兩行對調,結果必須不變 —— 這是唯一分得開兩種實作的對照組。"""
        m = self._manifest_mod()
        rows = ["tests/  ask", "tests/test_mine.py  skip"]
        got = []
        for order in (rows, list(reversed(rows))):
            p = tmp_path / ("m%d.txt" % len(got))
            io.open(p, "w", encoding="utf-8", newline="\n").write(
                "\n".join(order) + "\n")
            t = m.load_table(str(p))
            got.append((m.mark_in("tests/test_gate.py", t),
                        m.mark_in("tests/test_mine.py", t)))
        assert got[0] == got[1] == ("ask", "skip"), got


class TestUnclassifiedIsRefusedNotCopied:
    """**「未標記 → copy」在安裝器是對的,在更新路徑是災難。**

    下游第三輪 dry-run 攔到:sync 要覆蓋目標的六個根目錄檔,其中
    `.githooks/pre-commit` 會從**兩段都接**降成只剩 leak_scan ——
    (原寫「三層掛載」,票 51:⑥ 更正:那個 hook 只有兩個階段)
    **權威層靜默消失**。hook 還在、還會跑、還會擋洩漏,只是不再呼叫
    `gate.py --pre-commit`,而整個過程看起來像一次成功的更新。

    安裝器有兩道護欄讓那個預設安全:`in_scope()` 先濾掉範圍外的檔案,
    未涵蓋的鄰居會被列出來讓人確認。更新路徑**兩道都沒有**,
    而它的寫入對象是別人 repo 裡已經存在的檔案。
    同一個預設,兩邊的風險方向相反:安裝器裡「多帶」是吵鬧的(空 repo),
    更新路徑裡「多帶」是**覆蓋**,而覆蓋是靜默的。
    """

    def test_an_unclassified_source_file_is_refused(self, pair):
        src, dst = pair
        _w(src, "README.md", "上游自己的 README\n")
        _git(src, "add", "-A")
        _git(src, "commit", "-qm", "add readme")
        with pytest.raises(sync.Refused) as e:
            sync.update(str(src), str(dst), apply=True)
        assert "README.md" in str(e.value), "拒絕了但沒點名是哪個檔:%s" % e.value

    def test_the_refusal_names_the_missing_premise(self, pair):
        """票 13 的判準:fail-closed 的訊息要說出**是哪一個前提沒滿足**。

        只說「拒絕」的話,人會去找權限、找路徑、找 git 狀態 ——
        而現場是「這個檔案沒有標記」。
        """
        src, dst = pair
        _w(src, "README.md", "x\n")
        _git(src, "add", "-A")
        _git(src, "commit", "-qm", "add readme")
        with pytest.raises(sync.Refused) as e:
            sync.update(str(src), str(dst), apply=True)
        assert "標記" in str(e.value), e.value

    def test_dry_run_refuses_too(self, pair):
        """dry-run 也要擋 —— 它的用途是「看看會動到什麼」,
        而一份把未分類檔案列成「將覆蓋」的清單本身就是錯的答案。"""
        src, dst = pair
        _w(src, "README.md", "x\n")
        _git(src, "add", "-A")
        _git(src, "commit", "-qm", "add readme")
        with pytest.raises(sync.Refused):
            sync.update(str(src), str(dst))

    def test_an_explicitly_skipped_file_is_left_alone(self, pair):
        """**負控**:明列 skip 之後放行,而且目標的同名檔逐位元組不變。

        少了這條,「一律拒絕」也會讓上面三條過 —— 那是另一種壞掉,只是吵。
        """
        src, dst = pair
        _w(src, "README.md", "上游自己的 README\n")
        _w(src, ".agents/portable-manifest.txt", MANIFEST + "README.md  skip\n")
        _git(src, "add", "-A")
        _git(src, "commit", "-qm", "mark readme skip")
        _w(dst, "README.md", "目標自己的 README\n")
        _git(dst, "add", "-A")
        _git(dst, "commit", "-qm", "dst readme")
        before = _h(dst, "README.md")
        sync.update(str(src), str(dst), apply=True)
        assert _h(dst, "README.md") == before, "標了 skip 還是被覆蓋"

    # 「上游每一筆追蹤檔案都要有標記」那條**不在這裡** ——
    # 它是**上游**的性質,不是每個 repo 的性質,而本檔會隨框架出貨。
    # 放在這裡的話,任何裝了框架、又有自己專案檔案的 repo 都天生帶紅
    # (實測:先有 myapp/core.py 的 repo 裝完立刻紅)。
    # 見 tests/test_upstream_manifest.py,那個檔案標 skip、不出貨。


class TestDirtinessIsAboutTheOuterTree:
    """**規則要問「我的寫入會不會壓到未提交的變更」,不是「整棵樹有沒有髒」。**

    量化 repo 的 `data_collector` 是內嵌 git repo(gitlink,無 `.gitmodules`)。
    它內部的髒在 sync 的寫入面之外 —— sync 從不寫那條路徑底下的東西 ——
    卻讓 sync 永久拒絕。判錯對象的第六例。

    不靠 `--ignore-submodules=dirty`:本機實測那個旗標行為正確,
    量化那邊卻永久拒絕,代表它的語意在不同 git 版本/組態下不一致。
    **一道護欄的正確性掛在「哪個 git 版本」上,那個依賴本身就是缺陷** ——
    它會在別人的機器上安靜地翻面。
    """

    @pytest.fixture()
    def embedded(self, pair):
        """外層 repo 裡放一個內嵌 git repo(gitlink,不寫 .gitmodules)。"""
        src, dst = pair
        inner = dst / "data_collector"
        inner.mkdir()
        for c in ("init -q", "config user.email t@t", "config user.name t"):
            subprocess.run(["git"] + c.split(), cwd=str(inner), capture_output=True)
        _w(inner, "collect.py", "x = 1\n")
        _git(inner, "add", "-A")
        _git(inner, "commit", "-qm", "inner1")
        _git(dst, "add", "-A")
        _git(dst, "commit", "-qm", "embed")
        return src, dst, inner

    def test_internal_dirt_does_not_block(self, embedded):
        """**主張**:內嵌 repo 內部髒 + 外層乾淨 → 放行。"""
        src, dst, inner = embedded
        _w(inner, "collect.py", "x = 2\n")          # modified content
        _w(inner, "scratch.tmp", "untracked\n")     # untracked content
        sync.update(str(src), str(dst), apply=True)   # 不得丟 Refused

    def test_sync_never_writes_inside_the_embedded_repo(self, embedded):
        """證明「在寫入面之外」不是宣稱:內嵌 repo 的內容逐位元組不變。"""
        src, dst, inner = embedded
        _w(inner, "collect.py", "x = 2\n")
        before = _h(inner, "collect.py")
        plan = sync.update(str(src), str(dst), apply=True)
        assert _h(inner, "collect.py") == before
        assert not [r for r in plan.changed + plan.added
                    if r.startswith("data_collector/")], plan

    def test_an_unrecorded_gitlink_advance_no_longer_blocks(self, embedded):
        """**票 42 (b):推翻票 17 在這一格的裁決。**

        原本這條叫 `test_an_unrecorded_gitlink_advance_still_blocks`,
        斷言「內部前進、外層未記錄 → 擋」。理由是「那是**外層**的未落定狀態」。

        推翻的理由:`refuse_if_dirty` 要防的是
        「**在未提交的變更上覆寫,出事時分不出是誰改的**」——
        而 gitlink 指標落沒落定**不在 sync 的寫入面上**。
        sync 不寫 submodule 底下任何東西,也不寫 gitlink 本身;
        指標落後時,sync 覆寫框架檔的結果完全不變。
        這與同組 `test_internal_dirt_does_not_block` 是同一個判準,
        當時只套到了「內部髒」那一半。

        下游代價(這條被推翻的直接原因):在 (a) 未修時,下游**無法**落定它 ——
        bump 需要新版 leak_scan,取得新版要跑 sync,而 sync 因此拒絕。循環。

        **不刪掉原測試改寫成新的**:記名推翻,理由留在這裡(F-036 的規矩)。
        """
        src, dst, inner = embedded
        _w(inner, "collect.py", "x = 3\n")
        _git(inner, "add", "-A")
        _git(inner, "commit", "-qm", "inner2")
        sync.update(str(src), str(dst), apply=True)          # 不得丟 Refused

    def test_a_staged_but_uncommitted_gitlink_bump_blocks(self, embedded):
        """已 stage 未提交的 bump 也是外層的未落定狀態 → 擋。"""
        src, dst, inner = embedded
        _w(inner, "collect.py", "x = 4\n")
        _git(inner, "add", "-A")
        _git(inner, "commit", "-qm", "inner3")
        _git(dst, "add", "data_collector")
        with pytest.raises(sync.Refused):
            sync.update(str(src), str(dst), apply=True)

    def test_outer_dirt_still_blocks(self, embedded):
        """**負控**:外層髒照樣拒絕。少了它,「一律放行」也會讓上面幾條過。"""
        src, dst, inner = embedded
        _w(dst, "untracked_outer.txt", "x\n")
        with pytest.raises(sync.Refused):
            sync.update(str(src), str(dst), apply=True)

    # ── 判定不得掛在 git 旗標的語意上 ────────────────────────────────
    #
    # 上面那幾條在本機 git(2.53)是綠的 —— 因為這個版本的
    # `--ignore-submodules=dirty` 行為正確。**量化那台不是**,
    # 而我在這台機器上重現不出來。
    # 所以真正要釘的不是「行為對不對」,是「**判定有沒有依賴那個旗標**」:
    # 依賴它的話,同一份程式碼在兩台機器上會給出相反的答案,
    # 而那種缺陷在本機永遠測不到。

    def test_the_gitlink_check_is_explicit_not_flag_dependent(self, embedded):
        """gitlink 的判定要自己比對 sha,不靠 git 幫忙過濾。"""
        src, dst, inner = embedded
        assert hasattr(sync, "gitlink_unsettled"), \
            "沒有明確的 gitlink 比對 —— 判定還掛在 --ignore-submodules 的語意上"
        assert sync.gitlink_unsettled(str(dst)) == []

    def test_gitlink_unsettled_ignores_internal_dirt(self, embedded):
        src, dst, inner = embedded
        _w(inner, "collect.py", "x = 9\n")
        _w(inner, "junk.tmp", "u\n")
        assert sync.gitlink_unsettled(str(dst)) == []

    def test_gitlink_unsettled_ignores_an_advanced_inner_repo(self, embedded):
        """**票 42 (b):推翻票 17 在這一格的裁決**(理由見上一條)。

        原名 `test_gitlink_unsettled_reports_an_advanced_inner_repo`,
        斷言 index ≠ 內層 HEAD 要被回報為未落定。現在**不回報** ——
        那一格不在 sync 的寫入面上。
        """
        src, dst, inner = embedded
        _w(inner, "collect.py", "x = 9\n")
        _git(inner, "add", "-A")
        _git(inner, "commit", "-qm", "advance")
        assert sync.gitlink_unsettled(str(dst)) == [], \
            "內層前進、外層未記錄仍被判為未落定 —— 放寬沒生效"

    # ── 放寬只有一格,另外兩格原地不動 ──────────────────────────────
    #
    # 三態的分界要**釘死**,否則下一次重構會把這次放寬順手擴大成
    # 「gitlink 一律不管」—— 而那會讓一個已 staged、下次就會被提交的 bump
    # 在 sync 覆寫時無法歸屬,正是 refuse_if_dirty 存在的唯一理由。
    #
    #   HEAD ≠ index      已 stage 未提交的 bump   -> 維持為髒(在寫入面上)
    #   index ≠ 內層 HEAD 內層前進、外層未記錄     -> 放寬(不在寫入面上)
    #   內嵌 repo 讀不到                           -> 維持為髒(fail-closed)

    def test_a_staged_bump_is_still_unsettled(self, embedded):
        """**負控一**:已 stage 未提交的 bump 仍被判髒。

        `test_a_staged_but_uncommitted_gitlink_bump_blocks` 走的是
        `sync.update` 那條路;這條直接問 `gitlink_unsettled`,
        因為放寬是動在它身上 —— 分界要釘在被改的那個函式上。
        """
        src, dst, inner = embedded
        _w(inner, "collect.py", "x = 5\n")
        _git(inner, "add", "-A")
        _git(inner, "commit", "-qm", "inner5")
        _git(dst, "add", "data_collector")
        out = sync.gitlink_unsettled(str(dst))
        assert out and "data_collector" in out[0], \
            "已 staged 的 bump 被一起放寬了 —— 那一格在 sync 的寫入面上:%r" % out

    def test_an_unreadable_embedded_repo_fails_closed(self, embedded):
        """**負控二**:讀不到內嵌 repo(不是 git repo、權限問題)-> 當髒。
        問不出來不等於乾淨。

        **票 42 第四件**:原本用 `shutil.rmtree(..., ignore_errors=True)`。
        Windows 上 git 的鬆散物件檔是**唯讀**的,`rmtree` 會
        `PermissionError: [WinError 5]`(票 41 實測),而 `ignore_errors=True`
        把它吞掉 —— 結果是**部分刪除**:這條測試綠的理由變成
        「`HEAD`/`config` 剛好可寫、被刪掉了」,而不是「`.git` 真的不見了」。
        放寬了上面那一格之後,這條是三態裡「讀不到仍髒」的**唯一守衛**,
        它不能只有名義上的守護。

        改用 `os.rename`:結果是確定的,而且更像真實情形 ——
        **未 init 的 submodule 就是「目錄在、工作樹在、`.git` 不在」**。
        """
        src, dst, inner = embedded
        os.rename(str(inner / ".git"), str(inner / ".git-gone"))
        assert not (inner / ".git").exists(), "前提沒成立:.git 還在"
        out = sync.gitlink_unsettled(str(dst))
        assert out, "內嵌 repo 讀不到卻回報乾淨(fail-open)"

    def test_a_missing_inner_repo_is_not_answered_by_the_outer_one(self, embedded):
        """**這一格從來沒有被走到過**(票 42 實測),所以直接釘住偵測本身。

        `git -C <路徑> rev-parse HEAD` 在該路徑沒有 repo 時會**往上走**,
        回答**外層** repo 的 HEAD 並回 0 —— 退出碼永遠是 0,
        「讀不到內嵌 repo」那個分支因此不可達。

        它一直被下一個分支遮著:舊版接著比 `index_sha != inner_sha`,
        而逃到外層拿回來的 sha 幾乎必然不等於 index 記的,於是照樣判髒 ——
        **結論對,理由錯**。第二格一放寬(票 42 (b)),遮蔽消失,整格 fail-open。

        判法改成問 git「你認為的工作樹根在哪」,再確認那就是這個路徑本身。
        """
        src, dst, inner = embedded
        assert sync.is_own_repo(str(dst), "data_collector") is True
        os.rename(str(inner / ".git"), str(inner / ".git-gone"))
        assert sync.is_own_repo(str(dst), "data_collector") is False, \
            "查詢逃到外層 repo,卻被當成內嵌 repo 讀得到"

        # 逃逸的證據:同一個路徑,git 照樣回 0,而那個 sha 是**外層**的
        out = subprocess.run(["git", "-C", str(inner), "rev-parse", "HEAD"],
                             capture_output=True)
        outer = subprocess.run(["git", "-C", str(dst), "rev-parse", "HEAD"],
                               capture_output=True)
        assert out.returncode == 0 and out.stdout == outer.stdout, \
            "這台機器上 git 不往上走了 —— 那本條的前提要重寫,不是刪掉"


class TestDuplicateFrictionHeadingsAreRefused:
    """**撞號正是這道護欄的獵物,而它被撞號打穿。**

    現行實作用集合差:目標若有**兩則** `## F-046`(本地一則 + 上游同號一則),
    集合把兩則塌成一員,`th - sh` 把 F-046 整個消掉 ——
    於是 sync 放行,並靜默刪掉本地那則。

    這道護欄存在的唯一理由就是「本地條目不能被覆蓋刪掉」,
    而它用的資料結構恰好對「同號多則」不可見。
    """

    def _log(self, root, body):
        _w(root, "docs/agents/friction-log.md", body)
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "log")

    def test_duplicate_headings_in_the_target_are_refused(self, pair):
        src, dst = pair
        self._log(dst, "# Friction\n\n## F-001 一\n## F-046 本地的 hook-session\n"
                       "## F-047 別的\n## F-046 上游同號那則\n")
        self._log(src, "# Friction\n\n## F-001 一\n## F-002 二\n## F-046 上游同號那則\n")
        with pytest.raises(sync.Refused) as e:
            sync.update(str(src), str(dst), apply=True)
        assert "F-046" in str(e.value), e.value

    def test_the_refusal_names_both_line_numbers(self, pair):
        """票 13 判準:說出是哪一個前提沒滿足 —— 這裡是「哪個號碼、在哪兩行」。"""
        src, dst = pair
        self._log(dst, "# Friction\n\n## F-046 甲\n## F-047 乙\n## F-046 丙\n")
        self._log(src, "# Friction\n\n## F-046 甲\n")
        with pytest.raises(sync.Refused) as e:
            sync.update(str(src), str(dst), apply=True)
        msg = str(e.value)
        assert "3" in msg and "5" in msg, "沒有點名兩處行號:%s" % msg

    def test_duplicates_on_the_source_side_are_refused_too(self, pair):
        """兩側都驗:上游自己撞號同樣是「這份表不可信」。"""
        src, dst = pair
        self._log(src, "# Friction\n\n## F-050 甲\n## F-050 乙\n")
        self._log(dst, "# Friction\n\n## F-050 甲\n")
        with pytest.raises(sync.Refused) as e:
            sync.update(str(src), str(dst), apply=True)
        assert "F-050" in str(e.value), e.value

    def test_no_duplicates_still_passes(self, pair):
        """**負控**:沒有撞號時照舊放行,不是一律拒絕。"""
        src, dst = pair
        self._log(src, "# Friction\n\n## F-001 一\n## F-002 二\n")
        self._log(dst, "# Friction\n\n## F-001 一\n")
        sync.update(str(src), str(dst), apply=True)


class TestAProseHeadingIsNotAnEntryNumber:
    """framework-updates/98:**`## 併記於 F-118(…)` 不是一個叫 `併記於` 的號碼。**

    本檔原本自帶 `^## (\\S+)` —— `## ` 之後第一個非空白詞就算號碼。
    上游的 friction log 裡有**兩則**以 `## 併記於 ` 開頭的標題
    (`F-118` 與 `F-145`,兩個**不同**的號),於是
    `refuse_if_duplicate_headings` 判定「`併記於` 出現 2 次」而**拒絕整次更新**
    —— 2026-08-31 實測,`exit=1`,而那個誤判從 2026-08-29 起就存在。

    **`sync` 沒有壞**:`exit=1` + 說出缺的前提 = fail-closed 正確作動。
    壞的是判準的對象。所以修法不是放寬它,是與 R9 看同一份判準
    (`.claude/portable/friction_heading.py`)。

    **本條是行為紅**:它對著 HEAD 版的 `sync.py` 跑會紅,對著修好的跑會綠。
    「兩份判準一不一致」是另一個問題,由
    `tests/test_gate.py::TestBothHeadingCriteriaAgree` 回答。
    """

    def _log(self, root, body):
        _w(root, "docs/agents/friction-log.md", body)
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "log")

    PROSE_LOG = (u"# Friction\n\n"
                 u"## F-118 甲\n"
                 u"## 併記於 F-118(2026-08-26):那次相撞真的發生了\n"
                 u"## F-145 乙\n"
                 u"## 併記於 F-145(2026-08-29):裁決者側採用的處置\n")

    def test_two_prose_headings_are_not_a_duplicate_number(self, pair):
        """**兩則 `## 併記於 …` 不是撞號** —— 它們提到的是兩個不同的號。"""
        src, dst = pair
        self._log(src, self.PROSE_LOG)
        self._log(dst, u"# Friction\n\n## F-118 甲\n")
        sync.update(str(src), str(dst), apply=True)

    def test_a_prose_heading_is_not_collected_as_a_number(self):
        """直接問判準本身:`## 併記於 …` 不得被擷取成一個號碼。"""
        assert sync.HEADING.match(
            u"## 併記於 F-118(2026-08-26):那次相撞真的發生了") is None
        assert sync.HEADING.match(u"## 這份規則(附決策)") is None

    def test_a_real_issuing_heading_still_is(self):
        """**反控**:修窄之後,真的發號標題照樣認得,擷取到的還是號碼本身。"""
        m = sync.HEADING.match(u"## F-118 甲")
        assert m is not None and m.group(1) == u"F-118"

    def test_a_real_duplicate_is_still_refused(self, pair):
        """**反控**:修窄不得把這道護欄關掉 —— 真的撞號照樣拒絕。"""
        src, dst = pair
        self._log(src, u"# Friction\n\n## F-050 甲\n## F-050 乙\n")
        self._log(dst, u"# Friction\n\n## F-050 甲\n")
        with pytest.raises(sync.Refused) as e:
            sync.update(str(src), str(dst), apply=True)
        assert "F-050" in str(e.value), e.value


class TestProvenanceCertifiesIdentityNotWrites:
    """**判準是「它與上游一致」,不是「我寫了它」。**

    原本只替 `changed + added` 發證,於是**從未需要更新的檔案永遠拿不到證**:
    量化的 `g1_verify.py`、`shadow_review.py` 一直與上游相同,
    每一輪同步都不在那個集合裡,R3 一醒就紅而且永遠不會自己好。
    `verify_gates.py` 那輪是綠的,那是**巧合** —— 它剛好有變。
    一個靠「剛好有改」才成立的保證,不是保證。

    「與上游逐位元組相同」才是 R3 要問的(ADR F-0014)。
    """

    def test_a_file_never_written_by_sync_still_gets_a_record(self, pair):
        """量化的實際情境:`g1_verify.py` 同步**之前**就已經與上游相同,
        所以每一輪都不在 `changed + added` 裡,從來沒拿到過證。"""
        src, dst = pair
        _w(src, ".claude/hooks/steady.py", "# 從來不用更新\n")
        _git(src, "add", "-A")
        _git(src, "commit", "-qm", "steady")
        _w(dst, ".claude/hooks/steady.py", "# 從來不用更新\n")   # 目標已經一樣
        _git(dst, "add", "-A")
        _git(dst, "commit", "-qm", "already有")

        plan = sync.update(str(src), str(dst), apply=True)
        assert ".claude/hooks/steady.py" not in plan.changed + plan.added, \
            "這個檔案根本沒被寫過 —— 測試的前提垮了"
        recs = [json.loads(l) for l in
                io.open(dst / ".dev" / "provenance.jsonl", encoding="utf-8")
                if l.strip()]
        assert any(r["path"] == ".claude/hooks/steady.py" for r in recs), \
            "沒被寫過但與上游相同的檔案拿不到證 —— R3 一醒就紅:%r" % recs

    def test_a_locally_drifted_file_gets_no_record(self, pair):
        """**負控**:本地改過的 copy 檔不發證 —— 它已經不是「上游的成品」。"""
        src, dst = pair
        sync.update(str(src), str(dst), apply=True)
        _w(dst, ".claude/hooks/gate.py", "# 本地亂改\n")
        _git(dst, "add", "-A")
        _git(dst, "commit", "-qm", "drift")
        os.remove(str(dst / ".dev" / "provenance.jsonl"))
        sync.update(str(src), str(dst), apply=False)
        sync.certify(str(src), str(dst))
        recs = [json.loads(l) for l in
                io.open(dst / ".dev" / "provenance.jsonl", encoding="utf-8")
                if l.strip()] if (dst / ".dev" / "provenance.jsonl").exists() else []
        assert not [r for r in recs if r["path"] == ".claude/hooks/gate.py"], recs


class TestCertifyRunsOnADirtyTree:
    """**發證與淨樹互為前提是死循環。**

    量化需要在「把東西納入管理」之前先補證,而發證原本要求淨樹。
    補證模式只寫 `.dev/provenance.jsonl`,**不寫任何 repo 內容** ——
    `refuse_if_dirty` 的理由是「在未提交的變更上覆寫,出事時分不出是誰改的」,
    而補證什麼都不覆寫,那道檢查對它不適用。

    判準不放寬:仍然是「與上游逐位元組相同」,漂移的檔案照樣不發證。
    **髒樹不會換來假證。**
    """

    def test_it_works_with_a_dirty_tree(self, pair):
        src, dst = pair
        sync.update(str(src), str(dst), apply=True)
        _w(dst, "untracked_mess.txt", "髒\n")
        os.remove(str(dst / ".dev" / "provenance.jsonl"))
        issued = sync.certify(str(src), str(dst))          # 不得丟 Refused
        assert issued, "髒樹上補證什麼都沒發"

    def test_it_writes_nothing_but_provenance(self, pair):
        """逐位元組驗:除了 provenance,repo 內容一個位元組都不能動。"""
        src, dst = pair
        sync.update(str(src), str(dst), apply=True)
        _w(dst, "untracked_mess.txt", "髒\n")
        before = {}
        for root_dir, _dirs, files in os.walk(str(dst)):
            if ".git" in root_dir:
                continue
            for f in files:
                p = os.path.join(root_dir, f)
                if p.endswith("provenance.jsonl"):
                    continue
                before[p] = hashlib.sha256(io.open(p, "rb").read()).hexdigest()
        sync.certify(str(src), str(dst))
        for p, digest in before.items():
            assert hashlib.sha256(io.open(p, "rb").read()).hexdigest() == digest, p

    def test_a_dirty_tree_still_yields_no_fake_certificate(self, pair):
        """**負控**:髒樹 + 漂移的檔案 -> 那個檔案仍然不發證。"""
        src, dst = pair
        sync.update(str(src), str(dst), apply=True)
        _w(dst, ".claude/hooks/gate.py", "# 漂移\n")
        _w(dst, "untracked_mess.txt", "髒\n")
        os.remove(str(dst / ".dev" / "provenance.jsonl"))
        issued = sync.certify(str(src), str(dst))
        assert ".claude/hooks/gate.py" not in [r["path"] for r in issued], issued


class TestGenerateIsNeverOverwritten:
    """`generate` 的語意是**缺才建、有就不碰**。

    sync 連建都不建 —— 它的不變式是「copy 以外的桶前後逐位元組不變」,
    在裡面加一個「有時候會建檔」的分支,那個不變式就不再驗得動。
    產生 generate 檔是安裝器的工作,不是更新路徑的。
    """

    def test_an_existing_generate_file_is_untouched(self, pair):
        src, dst = pair
        _w(dst, "docs/agents/friction-local.md", "## TSA-001 專案自己的\n")
        _git(dst, "add", "-A")
        _git(dst, "commit", "-qm", "local")
        before = _h(dst, "docs/agents/friction-local.md")
        sync.update(str(src), str(dst), apply=True)
        assert _h(dst, "docs/agents/friction-local.md") == before

    def test_a_missing_generate_file_is_not_created_by_sync(self, pair):
        src, dst = pair
        sync.update(str(src), str(dst), apply=True)
        assert not (dst / "docs/agents/friction-local.md").exists(), \
            "更新路徑自己造了 generate 檔 —— 那會讓『其他桶前後不變』驗不動"


class TestTheShippedManifestSaysSo:
    def test_the_manifest_marks_itself_ask(self):
        """裁決要落在檔案裡,不是只落在對話裡。"""
        marks = sync.load_manifest(str(ROOT))
        assert sync.mark_for(".agents/portable-manifest.txt", marks) == "ask"


# ─────────────────────────────────────────────────────────────────────────────
# 二、dry-run 預設
# ─────────────────────────────────────────────────────────────────────────────

class TestDryRunIsTheDefault:

    def test_nothing_is_written_without_apply(self, pair):
        src, dst = pair
        before = _h(dst, ".claude/hooks/gate.py")
        plan = sync.update(str(src), str(dst))
        assert _h(dst, ".claude/hooks/gate.py") == before
        assert not (dst / ".claude/hooks/newfile.py").exists()
        assert plan.changed and plan.added, plan

    def test_the_plan_names_what_would_change(self, pair):
        src, dst = pair
        plan = sync.update(str(src), str(dst))
        assert ".claude/hooks/gate.py" in plan.changed
        assert ".claude/hooks/newfile.py" in plan.added


# ─────────────────────────────────────────────────────────────────────────────
# 三、拒絕的條件(每一個「不確定」都往不寫倒)
# ─────────────────────────────────────────────────────────────────────────────

class TestItRefusesRatherThanGuesses:

    def test_a_dirty_target_is_refused(self, pair):
        """與 install.py 同規矩:髒工作樹上覆寫,出事時分不出是誰改的。"""
        src, dst = pair
        _w(dst, "untracked_change.txt", "x")
        with pytest.raises(sync.Refused):
            sync.update(str(src), str(dst), apply=True)

    def test_an_unmigrated_local_friction_entry_blocks_the_overwrite(self, pair):
        """目標的 friction-log 有來源沒有的條目 -> 那是還沒搬去 friction-local.md
        的 per-repo 條目。覆蓋會刪掉它們,所以拒絕,而且要說是哪幾則。"""
        src, dst = pair
        _w(dst, "docs/agents/friction-log.md",
           "# Friction\n\n## F-001 一\n## TSA-001 專案自己的\n")
        _git(dst, "add", "-A")
        _git(dst, "commit", "-qm", "local entry")
        with pytest.raises(sync.Refused) as e:
            sync.update(str(src), str(dst), apply=True)
        assert "TSA-001" in str(e.value), e.value

    def test_a_migrated_repo_can_sync_its_friction_log(self, pair):
        """反控:條目搬走之後就該過 —— 少了它,「一律拒絕」也會讓上面那條過。"""
        src, dst = pair
        _w(dst, "docs/agents/friction-local.md", "## TSA-001 專案自己的\n")
        _git(dst, "add", "-A")
        _git(dst, "commit", "-qm", "migrated")
        sync.update(str(src), str(dst), apply=True)
        assert _h(dst, "docs/agents/friction-log.md") == \
            _h(src, "docs/agents/friction-log.md")
        assert (dst / "docs/agents/friction-local.md").exists(), \
            "本地檔被更新路徑刪掉了"


# ─────────────────────────────────────────────────────────────────────────────
# 四、寫完要重驗(宣稱 vs 證據)
# ─────────────────────────────────────────────────────────────────────────────

class TestItVerifiesAfterWriting:

    def test_every_copied_file_is_rehashed_against_the_source(self, pair):
        src, dst = pair
        plan = sync.update(str(src), str(dst), apply=True)
        assert plan.verified, "寫完沒有重算 hash —— 那只是宣稱寫對了"
        for rel in plan.changed + plan.added:
            assert _h(dst, rel) == _h(src, rel), rel

    def test_a_write_that_lands_wrong_is_caught(self, pair, monkeypatch):
        """把寫入換成「寫了但內容不對」,重驗必須抓到。

        沒有這條的話,`verified` 只是一個永遠為真的旗標 —— 那種旗標比沒有更糟,
        因為它會被當成證據。
        """
        src, dst = pair

        def _bad(path, raw):
            io.open(path, "wb").write(raw + b"# tampered\n")

        monkeypatch.setattr(sync, "_write_bytes", _bad)
        with pytest.raises(sync.Refused) as e:
            sync.update(str(src), str(dst), apply=True)
        assert "驗證" in str(e.value) or "hash" in str(e.value), e.value


# ─────────────────────────────────────────────────────────────────────────────
# 票 53 偵測器 II —— `generate` 桶的混血條目(`CLAUDE.md` 的正典段)
# ─────────────────────────────────────────────────────────────────────────────
#
# 現況:`generate` 桶只被驗「sync 自己有沒有亂碰它」(寫入前後 hash 相同),
# **不驗「它跟正典一不一致」**。而 `CLAUDE.md` 是這個桶裡唯一的混血 ——
# `FRAMEWORK:END` 之後是各 repo 自己的,界線之間是正典、應當完全相同。
#
# 判準:比 `claude_md.framework_section()` 抽出來的子範圍,**不比整個檔**。
# 比整檔的話每個有專案規範的下游都會被判漂移,而**永遠吵的檢查等於沒有檢查**。
#
# 失效方向:漂移 -> **拒絕**,不是警告。這個 repo 自己記過警告會失效
# (`unmigrated_friction` 的 docstring:「這是拒絕的條件,不是警告 ——
# 警告會被略過,而被刪掉的條目沒有第二份」)。
# 而拒絕必須有出口,否則第一次擋住就會被拿掉(票 66)——
# 出口是 `--regenerate-canon`(B5),本批不含。

class TestCanonSectionDrift:

    def test_editing_only_the_project_section_is_not_drift(self, pair):
        """**這一格是整個設計成不成立的關鍵。**

        下游本來就會在專案段寫自己的規矩 —— 那是那道界線存在的理由。
        把它判成漂移的話,每一個有專案規範的 repo 都會永遠被擋。
        """
        src, dst = pair
        _w(dst, "CLAUDE.md", _claude_md(CANON, "台股收盤 13:30。\n加了一整段。"))
        _git(dst, "add", "-A")
        _git(dst, "commit", "-qm", "專案段")
        sync.update(str(src), str(dst), apply=True)   # 不得丟例外

    def test_editing_the_canon_section_refuses_and_names_the_file(self, pair):
        src, dst = pair
        _w(dst, "CLAUDE.md",
           _claude_md(CANON.replace("完全相同", "不太一樣"), "台股收盤 13:30。"))
        _git(dst, "add", "-A")
        _git(dst, "commit", "-qm", "動正典段")
        with pytest.raises(sync.Refused) as e:
            sync.update(str(src), str(dst), apply=True)
        assert "CLAUDE.md" in str(e.value), e.value
        assert "--regenerate-canon" in str(e.value), \
            "拒絕了卻沒給出口 —— 沒有出口的守衛第一次擋住就會被拿掉(票 66)"

    def test_drift_is_refused_in_dry_run_too(self, pair):
        """**dry-run 也要擋。**

        dry-run 的用途是「看看會動到什麼」,而一份沒提到正典段已經分歧的清單
        本身就是錯的答案 —— 同 `refuse_if_unclassified` 的理由。
        """
        src, dst = pair
        _w(dst, "CLAUDE.md", _claude_md("## 開發流程\n完全不同。\n", "專案段"))
        _git(dst, "add", "-A")
        _git(dst, "commit", "-qm", "動正典段")
        with pytest.raises(sync.Refused):
            sync.update(str(src), str(dst), apply=False)

    def test_a_target_without_markers_refuses(self, pair):
        """目標沒有界線 —— **不是全新安裝,是被動過或是舊版**。

        全新安裝一定有界線(`render_for_new_repo()` 一律寫進去),
        所以這裡拒絕不會撞上票 19 的死循環形狀。
        """
        src, dst = pair
        _w(dst, "CLAUDE.md", "沒有任何標記的一份\n")
        _git(dst, "add", "-A")
        _git(dst, "commit", "-qm", "拿掉界線")
        with pytest.raises(sync.Refused) as e:
            sync.update(str(src), str(dst), apply=True)
        assert "CLAUDE.md" in str(e.value), e.value

    def test_a_target_with_two_marker_pairs_refuses(self, pair):
        """兩組界線 —— 取哪一組取決於實作,而那是隱形的。"""
        src, dst = pair
        _w(dst, "CLAUDE.md",
           _claude_md(CANON, "專案段") + "\n%s\nx\n%s\n" % (BEGIN, END))
        _git(dst, "add", "-A")
        _git(dst, "commit", "-qm", "兩組界線")
        with pytest.raises(sync.Refused):
            sync.update(str(src), str(dst), apply=True)

    def test_a_source_without_markers_refuses(self, pair):
        """**來源壞了不該往外傳。**

        方向與目標那一格相反但理由相同:抽不出正典段時不知道該比什麼,
        而「不知道該比什麼」的正解是停,不是跳過。
        """
        src, dst = pair
        _w(src, "CLAUDE.md", "上游自己掉了界線\n")
        _git(src, "add", "-A")
        _git(src, "commit", "-qm", "來源掉界線")
        with pytest.raises(sync.Refused):
            sync.update(str(src), str(dst), apply=True)

    def test_identical_canon_sections_leave_canon_drift_empty(self, pair):
        """沒有漂移時,**要看得出來檢查跑過了**。

        沒有這一格的話,「守衛沒說話」與「守衛根本沒跑」在退出碼上長得一樣。
        """
        src, dst = pair
        plan = sync.update(str(src), str(dst), apply=True)
        assert plan.canon_drift == []

    def test_apply_leaves_claude_md_byte_identical(self, pair):
        """**II 不碰寫入面。**

        這一格釘住那件事:偵測與寫入分開,寫入要人打第二個指令
        (`--regenerate-canon`,B5)。少了它,`--apply` 有一天會「順手」
        把正典段補上,而 `CLAUDE.md` 的失效方向是往「不帶」倒
        (`claude_md.py` 的 docstring),自動改寫與那個方向相反。
        """
        src, dst = pair
        before = _h(dst, "CLAUDE.md")
        sync.update(str(src), str(dst), apply=True)
        assert _h(dst, "CLAUDE.md") == before

    def test_the_refusal_messages_do_not_promise_a_command_that_is_missing(self):
        """B4 留的釘子:B5 落地時,兩處訊息裡的「尚未落地」要拿掉。

        **一個名字寫在訊息裡而指令不存在,比沒有出口更糟** ——
        `main()` 對未知旗標不報錯,照著打的人會拿到同一個拒絕,無限迴圈。
        所以 B4 把能用的手動出口寫在前面、把這個明標為未落地。
        B5 之後那個標註本身變成謊話,由本條釘住。
        """
        src = io.open(ROOT / ".claude" / "portable" / "sync.py",
                      encoding="utf-8").read()
        assert "尚未落地" not in src, (
            "`--regenerate-canon` 已經落地了,而拒絕訊息還說它沒有 —— "
            "照訊息做的人會走一條它自己說不通的路")

    def test_regenerate_canon_replaces_only_what_lies_between_the_markers(self, pair):
        """**第 1 條釘子:界線之外逐位元組不變。**

        這是本指令唯一的寫入面保證。少了它,「重新產生正典段」與
        「用上游那份蓋掉整個檔」在結果上分不出來 —— 而後者會刪掉專案段,
        那正是 `CLAUDE.md` 標 `generate`(不整檔照抄)的全部理由。
        """
        src, dst = pair
        before = io.open(dst / "CLAUDE.md", "rb").read()
        i = before.index(BEGIN.encode("utf-8")) + len(BEGIN)
        j = before.index(END.encode("utf-8"))

        _w(dst, "CLAUDE.md",
           _claude_md(CANON.replace("完全相同", "被下游改過了"), "台股收盤 13:30。"))
        _git(dst, "add", "-A")
        _git(dst, "commit", "-qm", "動正典段")

        sync.regenerate_canon(str(src), str(dst))

        after = io.open(dst / "CLAUDE.md", "rb").read()
        assert after[:i] == before[:i], "界線**之前**的位元組被動到了"
        assert after[after.index(END.encode("utf-8")):] == before[j:], \
            "界線**之後**的位元組被動到了 —— 專案段就住在那裡"
        assert "台股收盤 13:30。" in after.decode("utf-8"), "專案段不見了"

    def test_after_regenerating_the_drift_guard_is_quiet(self, pair):
        """做完之後 II 不再出聲 —— **出口要真的通到出口**。

        票 66:一道沒有出口的 fail-closed 守衛,第一次擋住的時候就會被繞過或拿掉。
        「有一個指令」不等於「那個指令解得掉」,兩者差一階。
        """
        src, dst = pair
        _w(dst, "CLAUDE.md", _claude_md("## 完全不同的正典段\n", "台股收盤 13:30。"))
        _git(dst, "add", "-A")
        _git(dst, "commit", "-qm", "動正典段")
        with pytest.raises(sync.Refused):
            sync.update(str(src), str(dst), apply=False)

        sync.regenerate_canon(str(src), str(dst))
        _git(dst, "add", "-A")
        _git(dst, "commit", "-qm", "重新產生")

        plan = sync.update(str(src), str(dst), apply=True)   # 不得丟例外
        assert plan.canon_drift == []

    def test_a_broken_target_refuses_and_writes_nothing(self, pair):
        """界線壞掉 -> 拒絕,而且**一個位元組都不寫**。

        「拒絕了但已經寫了一半」比不擋更糟:它看起來像一次失敗的操作,
        實際是一次部分成功的。
        """
        src, dst = pair
        _w(dst, "CLAUDE.md", "沒有任何標記的一份\n")
        _git(dst, "add", "-A")
        _git(dst, "commit", "-qm", "拿掉界線")
        before = io.open(dst / "CLAUDE.md", "rb").read()
        with pytest.raises(sync.Refused):
            sync.regenerate_canon(str(src), str(dst))
        assert io.open(dst / "CLAUDE.md", "rb").read() == before

    def test_a_dirty_target_refuses(self, pair):
        """與 `--apply` 同規矩:在未提交的變更上覆寫,出事時分不出是誰改的。"""
        src, dst = pair
        _w(dst, "CLAUDE.md",
           _claude_md(CANON.replace("完全相同", "改過"), "台股收盤 13:30。"))
        # 刻意**不** commit —— 工作樹髒
        with pytest.raises(sync.Refused) as e:
            sync.regenerate_canon(str(src), str(dst))
        assert "乾淨" in str(e.value) or "髒" in str(e.value), e.value

    def test_a_write_that_lands_wrong_is_caught_by_regenerate(self, pair, monkeypatch):
        """寫完要重驗 —— 沒有這條的話「寫對了」只是宣稱。

        與 `--apply` 那條同形狀(`test_a_write_that_lands_wrong_is_caught`),
        因為它們是同一類動作:**寫到別人的 repo 裡**。
        """
        src, dst = pair
        _w(dst, "CLAUDE.md",
           _claude_md(CANON.replace("完全相同", "改過"), "台股收盤 13:30。"))
        _git(dst, "add", "-A")
        _git(dst, "commit", "-qm", "動正典段")

        def _bad(path, raw):
            io.open(path, "wb").write(raw + b"# tampered\n")

        monkeypatch.setattr(sync, "_write_bytes", _bad)
        with pytest.raises(sync.Refused) as e:
            sync.regenerate_canon(str(src), str(dst))
        assert "驗證" in str(e.value) or "重驗" in str(e.value), e.value

    def test_every_hybrid_key_is_marked_generate_in_the_real_manifest(self):
        """`HYBRID` 表與標記表要一致。

        **這條守的是一致,不是完整** —— 它答不出「所有該進 `HYBRID` 的都進了」,
        那要判斷「這個 `generate` 條目有沒有可比對的子範圍」,是人的事。
        票 53 卷首那根釘子(第二個混血條目要回頭擴範圍)因此仍然是釘子。
        """
        marks = sync.load_manifest(str(ROOT))
        assert sync.HYBRID, "`HYBRID` 是空的 —— 枚舉本身壞了,不是通過"
        for rel in sync.HYBRID:
            assert sync.mark_for(rel, marks) == "generate", (
                "`HYBRID` 收了 %s,而標記表把它標成 %s —— "
                "混血分支只對 `generate` 桶有意義" % (rel, sync.mark_for(rel, marks)))
