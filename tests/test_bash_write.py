# -*- coding: utf-8 -*-
"""票 11 — R7:Bash 寫入 repo 一律擋,請改用 Write/Edit。

**這是收口,不是擴涵蓋。**

不採用「加 Bash 進 matcher + 解析寫入目標」:從指令字串解析「寫到哪」解不完
(heredoc 內文的路徑、sed -i、> 重導、tee、自己算路徑的腳本),
而 **60% 有效的解析器比零涵蓋更危險** —— 零涵蓋你知道它是零,
60% 你會以為 Bash 被守住了。那是 R4 的形狀。

改為:述詞只回答「**有沒有在寫**」,不回答「寫到哪」。
判斷不出來就當作在寫(fail-closed),所有寫入被逼回檔案工具 ——
而那條路 R1–R6 已經守得住,且在兩個環境各驗過一次。

**殘留缺口(明寫,不假裝擋得住)**:`python foo.py` 這種「指令本身看不出在寫」的
仍然穿得過去。不假裝 —— 那正是本票拒絕解析器的同一個理由。
"""

import importlib.util
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load_gate():
    spec = importlib.util.spec_from_file_location(
        "gate_for_bash", ROOT / ".claude" / "hooks" / "gate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gate = _load_gate()


@pytest.mark.parametrize("cmd", [
    "echo x > notes.txt",
    "printf 'a' >> docs/agents/friction-log.md",
    "sed -i 's/a/b/' macro_audit/classify.py",
    "cat x | tee out.txt",
    "cp a.py b.py",
    "mv a.py b.py",
    "touch newfile.py",
    "mkdir -p newdir",
    "python - <<'PY'\nimport io\nio.open('x.py','w').write('x')\nPY",
])
def test_writing_commands_are_blocked(cmd):
    """每一種都是「明顯在寫」。heredoc 那條順帶結構性消滅 F-028。"""
    msg = gate.bash_write_violation(cmd)
    assert msg and "R7" in msg, "沒擋到:%r -> %r" % (cmd, msg)
    assert "Write" in msg or "Edit" in msg, "訊息沒告訴人改用什麼:%r" % msg


@pytest.mark.parametrize("cmd", [
    "cat macro_audit/classify.py",
    "python -m pytest tests/ -q",
    "grep -rn foo tests/",
    "ls -la",
    "python .claude/hooks/gate.py --pre-commit",
    "git commit -m 'x'",
    "git add -A",
    "bash scripts/skills-update.sh",
])
def test_non_writing_or_sanctioned_commands_pass(cmd):
    """誤擋的代價不是不方便,是規則會被關掉 —— 而關掉的涵蓋率是零。"""
    assert gate.bash_write_violation(cmd) is None, "誤擋:%r" % cmd


@pytest.mark.parametrize("cmd", [
    "ls > /dev/null",
    "python x.py 2>&1",
    "echo probe > /tmp/probe.txt",
])
def test_targets_that_are_certainly_outside_the_repo_pass(cmd):
    """「確定在 repo 外」與「不知道寫到哪」是兩件事。

    前者可以放行:R7 管的是 repo 內,repo 外是 G1 的事。
    後者必須擋:不知道就當作在寫。
    """
    assert gate.bash_write_violation(cmd) is None, "誤擋:%r" % cmd


def test_every_exception_carries_a_reason():
    """理由欄是讓判準漂移看得見的東西 —— 與三份非原始碼清單同一個規矩。"""
    for name in ("BASH_ALLOWED_CMDS", "BASH_ALLOWED_TARGETS"):
        table = getattr(gate, name)
        assert isinstance(table, dict), "%s 必須是 {項目: 理由}" % name
        for k, why in table.items():
            assert isinstance(why, str) and why.strip(), "%s 的 %r 沒有理由" % (name, k)


def test_the_rule_is_enumerated_like_every_other_rule():
    """R7 要進 rule_codes,否則 verify_gates 不會替它準備情境 —— 規則存在卻沒被證明擋得住。"""
    assert "R7" in gate.rule_codes()


class TestEveryWriteTargetMustBeAllowed:
    """**「提到一個許可目標」不等於「每個寫入目標都被許可」。**

    原本的檢查是 `if target in cmd: return None` —— 只要指令**字串裡出現**
    任何一個許可目標,整條就免檢。於是在任何指令後面加 `2>/dev/null`
    就整條免檢,而抑制 stderr 是每個人本來就有的習慣:
    **這不是要刻意繞才踩得到的洞,是日常寫法會誤觸的洞**,
    只是誤觸的方向是「被放行」,所以沒有人會發現。

    判錯對象第七例(票 19)。
    """

    @pytest.mark.parametrize("cmd,named", [
        ("python x.py > out.txt 2>/dev/null", "out.txt"),
        ("python x.py >out.txt 2>/dev/null", "out.txt"),
        ("cat a > b.txt 2>/dev/null", "b.txt"),
    ])
    def test_a_suppressed_stderr_does_not_whitelist_a_real_write(self, cmd, named):
        msg = gate.bash_write_violation(cmd)
        assert msg, "加了 2>/dev/null 就免檢:%r" % cmd
        assert named in msg, "沒有點名真正的寫入目標(%s):%s" % (named, msg)

    @pytest.mark.parametrize("cmd", [
        "rm -rf important_dir >/dev/null",
        "cp secret.env backup.env 2>/dev/null",
        "mv a.txt b.txt >/dev/null",
        "tee gate.py < evil 2>/dev/null",
    ])
    def test_a_write_command_is_not_rescued_by_dev_null(self, cmd):
        assert gate.bash_write_violation(cmd), "寫入指令被 /dev/null 救了:%r" % cmd

    # ── 正控:不得回歸 ────────────────────────────────────────────────
    @pytest.mark.parametrize("cmd", [
        "ls >/dev/null",
        "ls > /dev/null",
        "ls >/dev/null 2>&1",
        "python -m pytest -q > /dev/null 2>&1",
        "grep -c foo bar >/dev/null",
    ])
    def test_writing_only_to_dev_null_is_still_allowed(self, cmd):
        assert gate.bash_write_violation(cmd) is None, cmd

    @pytest.mark.parametrize("cmd", [
        "python x.py > /tmp/out.txt",
        "rm -rf /tmp/scratch",
        "python x.py > C:/x/scratchpad/out.txt",
    ])
    def test_allowed_targets_still_pass(self, cmd):
        assert gate.bash_write_violation(cmd) is None, cmd

    def test_an_unparseable_write_is_blocked(self):
        """解析不出目標 → 擋。**半套的解析器比零涵蓋更危險**,
        所以不確定時往嚴的倒(ADR 0008 的同一句話)。"""
        assert gate.bash_write_violation("Set-Content -Path (Join-Path $a $b) -Value x")
