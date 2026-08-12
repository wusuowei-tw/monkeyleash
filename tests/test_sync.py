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
    ".agents/portable-manifest.txt  copy\n"
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
        """桶標未裁決(票 10)—— 在裁決之前一律跳過。

        它列著各 repo 自己的測試,blind-copy 會把那些歸類刪掉。
        """
        src, dst = pair
        before = _h(dst, ".agents/portable-manifest.txt")
        sync.update(str(src), str(dst), apply=True)
        assert _h(dst, ".agents/portable-manifest.txt") == before


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
