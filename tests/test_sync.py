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
    _w(src, "CLAUDE.md", "框架版\n")
    _git(src, "add", "-A")
    _git(src, "commit", "-qm", "src")

    _w(dst, ".agents/portable-manifest.txt", MANIFEST + "tests/test_mine.py skip\n")
    _w(dst, ".claude/hooks/gate.py", "# 舊版\nx = 1\n")
    _w(dst, "docs/agents/friction-log.md", "# Friction\n\n## F-001 一\n")
    _w(dst, ".agents/legacy-no-redlight.txt", "# go-live: zzz\n目標自己的\n")
    _w(dst, "CLAUDE.md", "目標版 + 專案段\n")
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
    `.githooks/pre-commit` 會從三層掛載降成只剩 leak_scan ——
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

    def test_the_shipped_manifest_classifies_everything(self):
        """**上游自己不得有任何未分類檔案。**

        這條守的是「下一個人新增檔案卻忘了分類」——
        而忘記分類的後果不是漏帶,是**覆蓋下游的同名檔**。
        我自己在批次二就漏了一個(`docs/agents/adr-numbering.md`)。
        """
        m = self._manifest_mod() if hasattr(self, "_manifest_mod") else None
        spec = importlib.util.spec_from_file_location(
            "manifest_for_coverage", ROOT / ".claude" / "portable" / "manifest.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        table = m.load_table(str(ROOT / ".agents" / "portable-manifest.txt"))
        out = subprocess.run(["git", "ls-files", "-z"], cwd=str(ROOT),
                             capture_output=True)
        rels = [p for p in out.stdout.decode("utf-8", "replace").split("\0")
                if p.strip()]
        unclassified = [p for p in rels if m.explicit_mark(p, table) is None]
        assert not unclassified, (
            "這些檔案沒有標記,更新路徑會拿它們去覆蓋下游的同名檔:\n  %s"
            % "\n  ".join(unclassified))


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
