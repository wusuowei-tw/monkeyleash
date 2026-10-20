# -*- coding: utf-8 -*-
"""為一個 repo 建立閘門專用的 `.venv-gates/`(票 156,G4)。

用法:python .claude/portable/setup_gates_env.py <target> [--profile downstream|upstream]

**從一份已經存在的上游 agent-gates checkout 執行**,target 以明確參數傳入。
使用的是**上游已提交**的鎖定檔(不是 target 裡的),照 `--require-hashes` 安裝。

**只准在 target 建立兩樣東西**:
  1. `<target>/.venv-gates/`
  2. `<target>/.git/info/exclude` 裡 `.venv-gates/` 那一行(只加這一行,已有就不重複)
不得要求 target 事先有任何 agent-gates 的檔案;target 必須是已 `git init` 的 repo
(要登記 exclude —— 空資料夾不行)。正式安裝時,`install.py` 會再把 `.venv-gates/`
永久寫進它產生的 `.gitignore`。

**需要連網**(從套件索引下載)⇒ 只在 Jeff 授權的站執行。`bootstrap.sh` 只驗證、不安裝。

兩個接縫是測試的替換點,也是唯二會碰外界的地方:
  `_create_venv(venv_dir)`          建 venv(離線)
  `_install_lock(python, locks)`    照鎖定檔 --require-hashes 安裝(連網)
"""

import argparse
import io
import os
import subprocess
import sys
import venv

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import runtime_identity  # noqa: E402  (鎖定檔路徑與 profile 只有一個定義處)

VENV_DIRNAME = runtime_identity.VENV_DIRNAME
EXCLUDE_LINE = VENV_DIRNAME + "/"


def _out(text):
    sys.stdout.flush()
    sys.stdout.buffer.write((text + "\n").encode("utf-8"))
    sys.stdout.buffer.flush()


def venv_python(venv_dir):
    """venv 裡的直譯器路徑(Windows 版面 / POSIX 版面)。"""
    if os.name == "nt":
        return os.path.join(venv_dir, "Scripts", "python.exe")
    return os.path.join(venv_dir, "bin", "python")


def lock_paths(profile, src_root=None):
    """profile 對應的**上游**鎖定檔(順序固定:核心在前)。"""
    root = src_root or SRC_ROOT
    rels = [runtime_identity.LOCK_CORE_REL]
    if profile == "upstream":
        rels.append(runtime_identity.LOCK_UPSTREAM_TESTS_REL)
    return [os.path.join(root, *r.split("/")) for r in rels]


def _create_venv(venv_dir):
    """以**正在執行的這支直譯器**為底座建 venv(底座必須是 3.11,`main` 先驗)。離線。"""
    venv.EnvBuilder(with_pip=True).create(venv_dir)


def _install_lock(python, locks):
    """照鎖定檔安裝。`--require-hashes`:任何沒釘版本或沒有 hash 的遞移相依都會被拒,
    所以「裝得起來」本身就是閉包完整的證明。鎖定檔不存在 ⇒ 明確失敗,不裝半套。"""
    missing = [p for p in locks if not os.path.isfile(p)]
    if missing:
        raise SystemExit("[setup_gates_env] 鎖定檔不存在:%s —— 拒絕安裝(不裝半套)。" % ", ".join(missing))
    cmd = [python, "-m", "pip", "install", "--require-hashes", "--only-binary=:all:",
           "--no-cache-dir", "--disable-pip-version-check"]
    for p in locks:
        cmd += ["-r", p]
    rc = subprocess.run(cmd).returncode
    if rc != 0:
        raise SystemExit("[setup_gates_env] 照鎖定檔安裝失敗(退出碼 %d)。" % rc)


def register_exclude(target):
    """在 `<target>/.git/info/exclude` 登記 `.venv-gates/`(只加這一行;已有就不動)。"""
    path = os.path.join(target, ".git", "info", "exclude")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    have = ""
    if os.path.exists(path):
        with io.open(path, encoding="utf-8") as f:
            have = f.read()
    if EXCLUDE_LINE in [l.strip() for l in have.splitlines()]:
        return False
    with io.open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(("\n" if have and not have.endswith("\n") else "") + EXCLUDE_LINE + "\n")
    return True


def main(argv=None, install_step=None):
    """`install_step`:安裝步驟的替換點(預設是真的 `_install_lock`)。
    `verify_gates` 的核心模式傳入離線的假步驟(D-11:核心驗證不得以網路為必要條件)。"""
    ap = argparse.ArgumentParser(description="為 target repo 建立 .venv-gates(票 156)")
    ap.add_argument("target", help="target repo 根目錄(必須已 git init)")
    ap.add_argument("--profile", default="downstream", choices=runtime_identity.PROFILES)
    args = ap.parse_args(argv)
    target = os.path.abspath(args.target)

    # ── 所有檢查都在第一次寫入之前 ─────────────────────────────────
    if not os.path.isdir(os.path.join(target, ".git")):
        raise SystemExit("[setup_gates_env] %s 不是已 git init 的 repo(沒有 .git/)—— 拒絕。"
                         "要登記 .git/info/exclude,空資料夾不行。" % target)
    if tuple(sys.version_info[:2]) != runtime_identity.PYTHON_MAJOR_MINOR:
        raise SystemExit("[setup_gates_env] 底座必須是 Python %d.%d,目前是 %s —— 拒絕。"
                         % (runtime_identity.PYTHON_MAJOR_MINOR
                            + (".".join(str(x) for x in sys.version_info[:3]),)))
    venv_dir = os.path.join(target, VENV_DIRNAME)
    if os.path.exists(venv_dir):
        raise SystemExit("[setup_gates_env] %s 已存在 —— 不覆寫。要重建請先由人確認後移除。" % venv_dir)
    locks = lock_paths(args.profile)

    # ── 寫入:先 exclude(讓 venv 從頭就不會以未追蹤檔出現),再建 venv、裝鎖定檔 ──
    register_exclude(target)
    _create_venv(venv_dir)
    (install_step or _install_lock)(venv_python(venv_dir), locks)
    _out("[setup_gates_env] 完成:%s(profile=%s)" % (venv_dir, args.profile))
    _out("    下一步:經 gatepy 執行 runtime_identity.py --whoami --repo %s --profile %s 核對身分。"
         % (target, args.profile))
    return 0


if __name__ == "__main__":
    sys.exit(main())
