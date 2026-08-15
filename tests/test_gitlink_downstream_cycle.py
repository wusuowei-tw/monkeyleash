# -*- coding: utf-8 -*-
"""票 42 —— 含 submodule 的下游那條**循環**,兩半都修好才解得開。

下游(台股資訊收集)實測的死結:

    bump 一格 gitlink  →  leak_scan 把它當檔案讀 → 擋下          (a)
    要拿修好的 leak_scan  →  得跑 sync
    sync                →  因 gitlink 未落定而拒絕                (b)

只修 (a):能 bump 了,但拿不到修好的 leak_scan(sync 還是拒絕)。
只修 (b):sync 過得去,但 bump 仍被 leak_scan 擋。
**兩個單測各自綠,不蘊含循環解開** —— 所以這一條把兩步接著跑。

下游當時沒有合法出口:`--no-verify` 等於關掉洩漏偵測、
改本地框架檔等於失去 provenance 豁免、手動複製上游檔案繞過 sync 同理。
"""

import importlib.util
import io
import os
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gate = _load("gate_for_cycle", ".claude/hooks/gate.py")
sync = _load("sync_for_cycle", ".claude/portable/sync.py")
leak_scan = _load("leak_scan_for_cycle", ".claude/portable/leak_scan.py")


def _git(cwd, *a):
    return subprocess.run(["git"] + list(a), cwd=str(cwd), capture_output=True)


def _downstream_with_an_advanced_inner_repo(tmp_path):
    """下游 repo:追蹤一格 gitlink,而內層已經前進、外層還沒記錄。

    這正是下游卡住時的狀態 —— 內層做完了一輪工作並提交,外層要 bump。
    """
    dst = tmp_path / "dst"
    dst.mkdir()
    inner = dst / "data_collector"
    inner.mkdir()
    io.open(inner / "collect.py", "w", encoding="utf-8",
            newline="\n").write("x = 1\n")
    for c in ("init -q", "config user.email t@t", "config user.name t",
              "add -A", "commit -qm inner1"):
        _git(inner, *c.split())

    for c in ("init -q", "config user.email t@t", "config user.name t"):
        _git(dst, *c.split())
    io.open(dst / "README.md", "w", encoding="utf-8").write("x\n")
    _git(dst, "add", "-A")
    _git(dst, "commit", "-qm", "embed")

    # 內層前進一步:外層 index 記的還是 inner1
    io.open(inner / "collect.py", "w", encoding="utf-8",
            newline="\n").write("x = 2\n")
    _git(inner, "add", "-A")
    _git(inner, "commit", "-qm", "inner2")

    mode = _git(dst, "ls-files", "-s", "data_collector").stdout.decode().split(" ")[0]
    assert mode == "160000", "fixture 沒種出 gitlink(mode=%r)" % mode
    return dst, inner


class TestTheDownstreamCycleIsSolved:

    def test_sync_then_bump_both_go_through(self, tmp_path, monkeypatch):
        """**一條測試走完整條循環**,順序與下游實際卡住的順序相同。

        第一步走 `refuse_if_dirty`(sync 真正的拒絕點),不是整支 `update` ——
        `update` 那條路由 `test_sync.py` 的
        `test_an_unrecorded_gitlink_advance_no_longer_blocks` 守著,
        這裡要釘的是**兩步接得起來**。
        """
        dst, inner = _downstream_with_an_advanced_inner_repo(tmp_path)

        # 一、sync 不再因為「內層前進、外層未記錄」而拒絕
        sync.refuse_if_dirty(str(dst))                 # 不得丟 Refused

        # 二、拿到修好的 leak_scan 之後,bump 過得了 pre-commit 的兩道
        _git(dst, "add", "data_collector")
        staged = _git(dst, "diff", "--cached", "--name-only").stdout.decode()
        assert "data_collector" in staged, "前提沒成立:bump 沒有被 stage"

        monkeypatch.setattr(leak_scan, "ROOT", str(dst))
        monkeypatch.setattr(leak_scan, "LOCAL_PATTERNS_FILE",
                            str(tmp_path / "none.local.txt"))
        assert leak_scan.main(["--staged"]) == 0, "洩漏偵測仍擋著 bump"

        assert "data_collector" not in gate.staged_paths(str(dst)), \
            "權威層仍把那一格當成待判定的原始碼"

    def test_the_bump_is_still_unsettled_for_sync_once_staged(self, tmp_path):
        """**負控**:bump 一 stage,sync 就要重新拒絕。

        放寬的只有「內層前進、外層未記錄」那一格。已 staged 未提交的 bump
        **在 sync 的寫入面上** —— 它會被下一次提交掃進去,而在它上面覆寫
        就是 `refuse_if_dirty` 存在的唯一理由。

        少了這條,「gitlink 一律不管」也會讓上面那條過,
        而那正是下一次重構最可能順手做的事。
        """
        dst, inner = _downstream_with_an_advanced_inner_repo(tmp_path)
        _git(dst, "add", "data_collector")
        try:
            sync.refuse_if_dirty(str(dst))
        except sync.Refused as e:
            assert "data_collector" in str(e), e
        else:
            raise AssertionError("已 staged 的 bump 沒有讓 sync 拒絕 —— 放寬擴大了")

    def test_an_unreadable_inner_repo_still_stops_sync(self, tmp_path):
        """**負控**:內嵌 repo 讀不到仍當髒(三態的第三格,fail-closed)。

        用 `os.rename` 不用 `rmtree` —— Windows 上 git 的鬆散物件唯讀,
        `rmtree(ignore_errors=True)` 是**部分刪除**(票 41 實測、票 42 第四件)。
        """
        dst, inner = _downstream_with_an_advanced_inner_repo(tmp_path)
        os.rename(str(inner / ".git"), str(inner / ".git-gone"))
        try:
            sync.refuse_if_dirty(str(dst))
        except sync.Refused:
            pass
        else:
            raise AssertionError("內嵌 repo 讀不到卻放行(fail-open)")
