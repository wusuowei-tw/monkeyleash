# -*- coding: utf-8 -*-
"""票 156 RT1 —— 啟動器 `.claude/bin/gatepy` 只認 `.venv-gates`,絕不退回。

受測對象:`.claude/bin/gatepy`(sh;本檔寫下時**還不存在**)。

## 怎麼證明「不退回」

tmp 造一個假 repo,放三類**假直譯器**,每一支被執行就在記號目錄留一個檔:
PATH 上的 `python` / `python3` / `py` / `python.exe`、`<repo>/.venv/bin/python`、
`<repo>/.venv/Scripts/python.exe`。跑 gatepy 之後斷言記號**一個都沒有**。

**必要的正控**(S3a 6-1,Jeff 核准):每一支假直譯器先**直接**呼叫一次,
證明它真的叫得動、真的會留記號。少了它,「沒有記號」可能只是假直譯器
根本叫不動 —— 那個綠燈什麼都不證明。正控叫不動 ⇒ **fail,不 skip**。

## sh 從哪裡來(D-5)

載入 `tests/test_bootstrap.py` 的 `find_sh()` / `sh_env()`(PATH → Git for Windows
預設路徑 → `git --exec-path` 推導)。**找不到 sh ⇒ pytest.fail,不 skip** ——
沒有 sh 的機器上新的 hook 本身就跑不起來,這不是可以略過的環境差異。

**本檔標 skip(只在上游)**:它載入的 `test_bootstrap.py` 也是 skip 檔;另含讀上游
`.githooks/pre-commit` 與上游歷史(`git show f5815d3:…`)的兩條。
"""
import ast
import importlib.util
import os
import pathlib
import shutil
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
GATEPY = ROOT / ".claude" / "bin" / "gatepy"
FIXTURES = ROOT / "tests" / "fixtures" / "hooks"
# 本票立案提交(設計封版):HOOK v1 的權威來源是這一筆裡的 install.py,
# 不是「目前」的 install.py —— 實作站改 HOOK 之後,目前那一份就是 v2 了。
V1_SOURCE_COMMIT = "f5815d36805eee25ac748c9359953eb944b2b364"


def _bootstrap_helpers():
    spec = importlib.util.spec_from_file_location(
        "test_bootstrap_for_gatepy", str(ROOT / "tests" / "test_bootstrap.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_BH = _bootstrap_helpers()


def _sh():
    sh = _BH.find_sh()
    if sh is None:
        pytest.fail("找不到 sh(PATH、Git for Windows 預設路徑、git --exec-path 都試過)—— "
                    "新的 hook 經 sh 執行 gatepy,沒有 sh 這條就驗不了,不得 skip 當綠燈")
    return sh


def _posix(p):
    return str(p).replace("\\", "/")


def _fake_interpreter(path, marker):
    """一支假直譯器:被執行就寫記號檔。shebang 腳本,Linux 給執行位元。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(path), "w", encoding="utf-8", newline="\n") as f:
        f.write('#!/bin/sh\necho hit > "%s"\nexit 0\n' % _posix(marker))
    os.chmod(str(path), 0o755)


def _layout(tmp_path):
    """假 repo + 假 PATH 目錄 + 記號目錄。回 (repo, fakebin, marks, fakes)。"""
    repo = tmp_path / "repo"
    (repo / ".claude" / "bin").mkdir(parents=True)
    fakebin = tmp_path / "fakebin"
    marks = tmp_path / "marks"
    marks.mkdir()
    fakes = {
        "path-python": fakebin / "python",
        "path-python3": fakebin / "python3",
        "path-py": fakebin / "py",
        "path-python.exe": fakebin / "python.exe",
        "venv-bin-python": repo / ".venv" / "bin" / "python",
        "venv-scripts-python.exe": repo / ".venv" / "Scripts" / "python.exe",
    }
    for name, p in fakes.items():
        _fake_interpreter(p, marks / name)
    return repo, fakebin, marks, fakes


def _env(sh, fakebin):
    """假 PATH 在最前面;只帶 sh 自己的目錄(它需要 dirname / pwd 等工具)。"""
    base = dict(os.environ)
    base["PATH"] = str(fakebin) + os.pathsep + os.path.dirname(sh)
    return _BH.sh_env(sh=sh, environ=base)


def _install_gatepy(repo):
    assert GATEPY.is_file(), "啟動器不存在(票 156 實作站產生):%s" % GATEPY
    dst = repo / ".claude" / "bin" / "gatepy"
    shutil.copy2(str(GATEPY), str(dst))
    return dst


def _run_gatepy(sh, gatepy, fakebin):
    p = subprocess.run([sh, str(gatepy), "-c", "print(1)"], capture_output=True,
                       env=_env(sh, fakebin))
    return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")


# ── 正控:每一支假直譯器真的叫得動、真的會留記號 ───────────────────────────────

@pytest.mark.parametrize("name", ["path-python", "path-python3", "path-py", "path-python.exe",
                                  "venv-bin-python", "venv-scripts-python.exe"])
def test_rt1_control_each_fake_interpreter_really_leaves_a_mark(tmp_path, name):
    """**綠燈對照**(不依賴 gatepy)。這條紅 ⇒ 下面「沒有記號」的斷言不證明任何事。"""
    sh = _sh()
    _repo, fakebin, marks, fakes = _layout(tmp_path)
    if name.startswith("path-"):
        cmd = [sh, "-c", "%s -c x" % fakes[name].name]
    else:
        cmd = [sh, "-c", '"%s" -c x' % _posix(fakes[name])]
    p = subprocess.run(cmd, capture_output=True, env=_env(sh, fakebin))
    assert (marks / name).exists(), (
        "假直譯器 %s 直接呼叫也沒留記號 —— 它叫不動,RT1 的「沒有記號」因此不成證據:rc=%s %s"
        % (name, p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")))


# ── RT1 ─────────────────────────────────────────────────────────────────────

def test_rt1_without_venv_gates_exits_2_and_never_falls_back(tmp_path):
    """RT1:沒有 `.venv-gates` ⇒ exit 2;PATH 上的與 `.venv` 裡的假直譯器**都沒被呼叫**。"""
    sh = _sh()
    repo, fakebin, marks, _fakes = _layout(tmp_path)
    gatepy = _install_gatepy(repo)
    rc, out = _run_gatepy(sh, gatepy, fakebin)
    hit = sorted(p.name for p in marks.iterdir())
    assert hit == [], "gatepy 退回了別的直譯器:%s\n%s" % (hit, out)
    assert rc == 2, "沒有 .venv-gates 時應 exit 2,實得 %s:%s" % (rc, out)


def test_rt1_the_refusal_names_venv_gates(tmp_path):
    """找不到時的訊息要說出缺的是 `.venv-gates`(而不是只有一個退出碼)。"""
    sh = _sh()
    repo, fakebin, _marks, _fakes = _layout(tmp_path)
    gatepy = _install_gatepy(repo)
    _rc, out = _run_gatepy(sh, gatepy, fakebin)
    assert ".venv-gates" in out, out


def test_rt1_the_venv_gates_interpreter_is_the_one_used(tmp_path):
    """`.venv-gates/bin/python` 存在 ⇒ gatepy 執行的是它,而且只有它。"""
    sh = _sh()
    repo, fakebin, marks, _fakes = _layout(tmp_path)
    _fake_interpreter(repo / ".venv-gates" / "bin" / "python", marks / "venv-gates")
    gatepy = _install_gatepy(repo)
    rc, out = _run_gatepy(sh, gatepy, fakebin)
    hit = sorted(p.name for p in marks.iterdir())
    assert hit == ["venv-gates"], "執行到的不是(只是)<repo>/.venv-gates:%s\n%s" % (hit, out)
    assert rc == 0, out


# ── RT2 的 `.githooks/pre-commit` 那一格(下游的這支是下游自己的,所以放 skip 檔)──

def _command_heads(text):
    """非註解、非空行的第一個 token;`exec` 開頭的取下一個。"""
    heads = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        toks = s.split()
        if toks[0] == "exec" and len(toks) > 1:
            toks = toks[1:]
        heads.append(toks[0])
    return heads


def test_rt2_the_upstream_githook_does_not_start_with_bare_python():
    text = (ROOT / ".githooks" / "pre-commit").read_text(encoding="utf-8")
    heads = _command_heads(text)
    bad = [h for h in heads if h in ("python", "python3", "py")]
    assert not bad, "上游 .githooks/pre-commit 仍有裸 python 開頭的指令:%s" % heads


# ── 範本 fixture 的綠燈對照 ──────────────────────────────────────────────────

def _hook_from_install_source(src):
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "HOOK" for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError("install.py 裡找不到 HOOK")


def test_the_v1_fixture_is_byte_identical_to_hook_at_the_ticket_commit():
    """**綠燈對照**:`hook-v1-bare-python.sh` = 立案提交 `f5815d3` 的 `install.HOOK`(UTF-8),
    兩者都不含 `\\r`。比的是那一筆而不是「目前」的 install.py —— 實作站把 HOOK 改成 v2 之後,
    這條仍然在問同一件事。"""
    p = subprocess.run(["git", "show", "%s:.claude/portable/install.py" % V1_SOURCE_COMMIT],
                       cwd=str(ROOT), capture_output=True)
    assert p.returncode == 0, p.stderr.decode("utf-8", "replace")
    hook = _hook_from_install_source(p.stdout.decode("utf-8"))
    fixture = (FIXTURES / "hook-v1-bare-python.sh").read_bytes()
    assert fixture == hook.encode("utf-8")
    assert b"\r" not in fixture and "\r" not in hook


def test_the_v2_fixture_keeps_the_three_substrings_and_no_bare_python():
    """**綠燈對照**:v2 仍含 `gate.py` / `--pre-commit` / `leak_scan`(`authoritative_layer`
    靠這三個判定,`gate.py:400-418`),且沒有裸 python 開頭的指令、沒有 `\\r`、沒有 BOM。"""
    raw = (FIXTURES / "hook-v2-gatepy.sh").read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf") and b"\r" not in raw
    text = raw.decode("utf-8")
    for needle in ("gate.py", "--pre-commit", "leak_scan"):
        assert needle in text, needle
    assert not [h for h in _command_heads(text) if h in ("python", "python3", "py")]


# ── S4b′:gatepy 的 LF 是**持久化政策**,不是「這一刻剛好是 LF」───────────────────
#
# S4e-1 之後,所有 active hook 都只經 `sh → gatepy → .venv-gates` 啟動 —— gatepy 一旦被
# checkout 成 CRLF,唯一的正式入口就壞了,閘門把自己鎖死。gatepy 沒有副檔名,
# `*.sh text eol=lf` 涵蓋不到它;本機 `git add` 時 Git 已警告「LF will be replaced by CRLF」。
# **問 Git 實際套用了什麼**(`git check-attr`),不綁某一行字面 —— 等價的寫法都會通過。

def test_s4b_prime_gitattributes_pins_gatepy_to_lf():
    p = subprocess.run(["git", "check-attr", "text", "eol", "--", ".claude/bin/gatepy"],
                       cwd=str(ROOT), capture_output=True)
    assert p.returncode == 0, p.stderr.decode("utf-8", "replace")
    attrs = {}
    for line in p.stdout.decode("utf-8", "replace").splitlines():
        parts = [s.strip() for s in line.split(":")]
        if len(parts) == 3:
            attrs[parts[1]] = parts[2]
    assert attrs.get("eol") == "lf", "gatepy 沒有被 .gitattributes 釘成 eol=lf:%r" % attrs
    assert attrs.get("text") == "set", "gatepy 的 text 屬性不是 set:%r" % attrs


def test_s4b_prime_gatepy_has_no_carriage_return():
    """結果檢查(不負責先紅):gatepy 本體的原始位元組沒有 `\\r`。"""
    assert b"\r" not in GATEPY.read_bytes()
