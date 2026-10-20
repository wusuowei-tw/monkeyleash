# -*- coding: utf-8 -*-
"""票 156 RT11(G4)—— `setup_gates_env.py <target>` 只准動兩樣東西。

受測對象:`.claude/portable/setup_gates_env.py`(本檔寫下時**還不存在**)。

## 本檔釘住的介面(S3b 定;實作站照此實作)

    setup_gates_env.main(argv) -> int          argv = [<target>, ...]
    setup_gates_env._create_venv(venv_dir)     建 venv 的唯一入口(測試替換)
    setup_gates_env._install_lock(python, locks)  照鎖定檔 --require-hashes 安裝的唯一入口(測試替換)

**離線**:兩個接縫都換成假步驟 —— 本檔證明的是「只動兩樣東西」與
「用的是上游的核心鎖定檔、target 的直譯器」,不是 venv 真的建得起來
(那由 D-11 的整合層證明)。

**前置(Jeff 2026-10-19 約 16:56 定稿)**:target 必須是**乾淨、已 `git init`、
還沒裝 agent-gates** 的 repo —— setup 要改 `.git/info/exclude`,空資料夾不行。

manifest 分類:copy(S3a 6-7)。
"""
import hashlib
import importlib.util
import os
import pathlib
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SETUP_PATH = ROOT / ".claude" / "portable" / "setup_gates_env.py"
CORE_LOCK = ROOT / ".claude" / "portable" / "gates-lock.txt"


def _setup():
    assert SETUP_PATH.is_file(), "setup_gates_env.py 不存在(票 156 實作站產生):%s" % SETUP_PATH
    spec = importlib.util.spec_from_file_location("setup_gates_env_under_test", str(SETUP_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _git(root, *args):
    return subprocess.run(["git"] + list(args), cwd=str(root), capture_output=True, check=True)


def _clean_target(tmp_path):
    """乾淨、已 git init、還沒裝 agent-gates:一個已追蹤檔(已提交)+ 一個未追蹤檔。"""
    t = tmp_path / "target"
    t.mkdir()
    _git(t, "init", "-q")
    _git(t, "config", "user.email", "t@t")
    _git(t, "config", "user.name", "t")
    (t / "app.txt").write_text("tracked\n", encoding="utf-8")
    _git(t, "add", "app.txt")
    _git(t, "commit", "-q", "-m", "init")
    (t / "notes.txt").write_text("untracked\n", encoding="utf-8")
    return t


def _snapshot(root):
    """target 底下**全部**檔案(含 `.git/`)的 (相對路徑 -> (大小, sha256))。"""
    snap = {}
    for dp, _dn, fns in os.walk(str(root)):
        for fn in fns:
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, str(root)).replace("\\", "/")
            with open(p, "rb") as f:
                data = f.read()
            snap[rel] = (len(data), hashlib.sha256(data).hexdigest())
    return snap


def _fake_steps(mod, monkeypatch, calls):
    def fake_create(venv_dir):
        os.makedirs(str(venv_dir), exist_ok=True)
        with open(os.path.join(str(venv_dir), "fake-venv.txt"), "w", encoding="utf-8") as f:
            f.write("fake\n")
        calls.append(("create", str(venv_dir)))

    def fake_install(python, locks):
        calls.append(("install", str(python), [str(l) for l in locks]))

    monkeypatch.setattr(mod, "_create_venv", fake_create)
    monkeypatch.setattr(mod, "_install_lock", fake_install)


def test_rt11_setup_changes_only_venv_gates_and_the_exclude_entry(tmp_path, monkeypatch):
    """RT11:成功之後 target 只允許兩項變化 ——
    (1) 新增 `.venv-gates/**`;(2) `.git/info/exclude` 恰好多一行 `.venv-gates/`。"""
    mod = _setup()
    t = _clean_target(tmp_path)
    exclude = t / ".git" / "info" / "exclude"
    before_exclude = exclude.read_text(encoding="utf-8").splitlines() if exclude.exists() else []
    before = _snapshot(t)
    calls = []
    _fake_steps(mod, monkeypatch, calls)
    rc = mod.main([str(t)])
    assert rc in (0, None), rc
    after = _snapshot(t)

    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(k for k in set(before) & set(after) if before[k] != after[k])
    assert not removed, removed
    assert all(a.startswith(".venv-gates/") or a == ".git/info/exclude" for a in added), added
    assert changed in ([], [".git/info/exclude"]), changed
    assert ".git/info/exclude" in changed or ".git/info/exclude" in added
    after_exclude = exclude.read_text(encoding="utf-8").splitlines()
    assert after_exclude == before_exclude + [".venv-gates/"], (before_exclude, after_exclude)
    # 沒有產生任何其他 agent-gates 檔
    for p in (".claude", ".agents", ".githooks", "bootstrap.sh", ".dev"):
        assert not (t / p).exists(), p


def test_rt11_setup_uses_the_upstream_core_lock_and_the_target_interpreter(tmp_path, monkeypatch):
    """G4:用上游**已提交**的核心鎖定檔;安裝用的直譯器在 `<target>/.venv-gates` 底下。"""
    mod = _setup()
    t = _clean_target(tmp_path)
    calls = []
    _fake_steps(mod, monkeypatch, calls)
    mod.main([str(t)])
    installs = [c for c in calls if c[0] == "install"]
    assert len(installs) == 1, calls
    _, python, locks = installs[0]
    assert os.path.normcase(os.path.realpath(python)).startswith(
        os.path.normcase(os.path.realpath(str(t / ".venv-gates")))), python
    assert [os.path.normcase(os.path.realpath(l)) for l in locks] == \
        [os.path.normcase(os.path.realpath(str(CORE_LOCK)))], locks


def test_rt11_setup_without_a_target_is_refused(tmp_path, monkeypatch):
    """target 必須以明確參數傳入;沒有參數 ⇒ 拒絕,什麼都不建。"""
    mod = _setup()
    calls = []
    _fake_steps(mod, monkeypatch, calls)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as e:
        mod.main([])
    assert e.value.code not in (0, None)
    assert calls == [], calls
    assert list(tmp_path.iterdir()) == [], list(tmp_path.iterdir())


def test_rt11_setup_on_a_non_git_folder_is_refused(tmp_path, monkeypatch):
    """前置是「已 git init」:空資料夾沒有 `.git/info/exclude` 可登記 ⇒ 拒絕,什麼都不建。"""
    mod = _setup()
    t = tmp_path / "plain"
    t.mkdir()
    calls = []
    _fake_steps(mod, monkeypatch, calls)
    with pytest.raises(SystemExit) as e:
        mod.main([str(t)])
    assert e.value.code not in (0, None)
    assert calls == [], calls
    assert list(t.iterdir()) == [], list(t.iterdir())
