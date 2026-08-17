# -*- coding: utf-8 -*-
"""verify_gates 的情境隔離 —— `restore()` 要真的把 target 還原成乾淨。

票 56。由來(2026-08-17 唯讀實測):全新安裝、單次執行,跑到 R5 那一步時
commit 的輸出裡帶著一筆 **R4** 違規:

    [R4][enforce] 鏡像缺少 .claude/skills/tdd/SKILL.md —— 正典有而鏡像沒有。

來源只可能是同一次執行裡前一步的 `scenario_r4`。`restore()` 用
`git reset --hard` + `git clean -fd`,而鏡像目錄被 `.gitignore` 忽略 ——
兩個指令都碰不到它,那個刪除因此永久留著。

**為什麼這一條非有不可**:`run_scenario` 的判定是連言

    blocked = rc != 0 and ("[%s]" % code in out or "[%s/" % code in out)

殘留讓 `rc != 0` 對後續每一條走 commit 的情境(R5 / R6 / R8)**恆真** ——
真正在做事的只剩第二個連言項。今天還不產生錯判,但「讀起來在驗兩件事、
實際只驗一件」正是本專案付過三次錢的那個形狀。

**測的是 `restore()` 的後置條件,不是它的實作。** 不斷言它有沒有呼叫
`build_mirrors`,只斷言「跑完之後鏡像回得來」—— 斷言實作的話,
換一種同樣正確的修法會讓這條測試假紅。
"""
import importlib.util
import io
import os
import subprocess

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PORTABLE = os.path.join(HERE, "..", ".claude", "portable")

MIRROR_REL = ".claude/skills/tdd/SKILL.md"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(PORTABLE, filename))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


vg = _load("verify_gates_under_test", "verify_gates.py")


def _git(args, cwd):
    p = subprocess.run(["git"] + args, cwd=cwd, capture_output=True)
    assert p.returncode == 0, (
        "測試自己的 git 前置失敗:%s\n%s"
        % (" ".join(args), (p.stdout + p.stderr).decode("utf-8", "replace")))
    return p


def _write(root, rel, text):
    dst = os.path.join(root, rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    io.open(dst, "w", encoding="utf-8", newline="\n").write(text)


@pytest.fixture()
def target(tmp_path):
    """最小的「安裝後」形狀:正典 + 兩個**被 gitignore 的**鏡像。

    鏡像被忽略是重現缺陷的必要條件,不是佈景 —— 鏡像若進版控,
    `git reset --hard` 自己就會把它還原,這條測試會綠得毫無理由。
    """
    root = str(tmp_path / "target")
    os.makedirs(root)
    _write(root, ".agents/skills/tdd/SKILL.md", "# tdd 正典\n")
    _write(root, ".claude/skills/tdd/SKILL.md", "# tdd 正典\n")
    _write(root, "skills/tdd/SKILL.md", "# tdd 正典\n")
    _write(root, ".gitignore", "/.dev/\n.claude/skills/\n/skills/\n")
    _write(root, "docs/adr/keep.md", "讓 docs/adr 在版控裡\n")
    os.makedirs(os.path.join(root, ".dev"))

    _git(["init", "-q"], root)
    _git(["config", "user.email", "t@example.invalid"], root)
    _git(["config", "user.name", "test"], root)
    _git(["add", "-A"], root)
    _git(["commit", "-qm", "base"], root)

    # 前置條件:鏡像確實不在版控裡,否則本測試量到的是 git 而不是 restore
    tracked = subprocess.run(["git", "ls-files", MIRROR_REL],
                             cwd=root, capture_output=True).stdout
    assert not tracked.strip(), (
        "%s 竟然進了版控 —— 缺陷的前提不成立,這條測試會綠在錯的理由上" % MIRROR_REL)
    return root


class TestScenarioR4LeavesTheTargetClean:
    """`scenario_r4` 跑完再 `restore()`,target 必須回到乾淨。"""

    def test_the_scenario_really_deletes_the_mirror_file(self, target):
        """**前置控制**:情境真的做了它宣稱的事。

        少了這一條,主紅燈可能綠在「情境根本沒刪東西」上 ——
        而那種綠與修好了長得一模一樣。
        """
        vg.scenario_r4(target)
        assert not os.path.exists(os.path.join(target, MIRROR_REL.replace("/", os.sep))), \
            "scenario_r4 沒有刪掉鏡像檔,這條測試底下的主張全部落空"

    def test_restore_brings_the_deleted_mirror_file_back(self, target):
        """**主紅燈**:被忽略的鏡像檔,`restore()` 之後要回得來。

        紅的時候代表:R4 之後的每一條情境都在一個帶著 R4 違規的 repo 上跑。
        """
        vg.scenario_r4(target)
        vg.restore(target)
        assert os.path.exists(os.path.join(target, MIRROR_REL.replace("/", os.sep))), \
            ("restore() 之後 %s 仍然不見 —— 下一條規則會在一個帶著 R4 違規的 "
             "repo 上跑,而它的 `rc != 0` 那一半因此是白送的。" % MIRROR_REL)

    def test_restore_still_cleans_the_tracked_side(self, target):
        """**反控**:追蹤側本來就還原得了。

        沒有這一條的話,主紅燈可能被讀成「restore 整個壞掉」——
        實際上它對追蹤側是好的,壞的只有被忽略的那一半。
        """
        vg.scenario_r4(target)
        vg.restore(target)
        dirty = subprocess.run(["git", "status", "--porcelain"],
                               cwd=target, capture_output=True).stdout
        assert not dirty.strip(), \
            "追蹤側沒有被還原乾淨:%r" % dirty.decode("utf-8", "replace")
        assert not os.path.exists(os.path.join(target, "docs", "adr", "verify-trigger.md")), \
            "情境寫的未追蹤檔沒有被清掉"
