# -*- coding: utf-8 -*-
"""安裝器預設值(F-062):洩漏 hook 接線 + .gitignore 秘密檔。

負控實測(2026-08-11,真安裝出的 repo):HOOK 只接 gate.py 時,
含真 API key 的 commit 直接成功 —— F-055(洩漏 hook 不隨 clone 走)
的安裝端後果。這裡把兩個預設值釘成紅燈過的規格。
"""
import importlib.util
import os

import pytest


@pytest.fixture(scope="module")
def install_mod():
    p = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", ".claude", "portable", "install.py"))
    spec = importlib.util.spec_from_file_location("install_defaults_probe", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_hook_wires_leak_scan_before_gate(install_mod):
    """pre-commit 樣板必須先跑 leak_scan 再跑 gate —— 秘密進歷史前的唯一便宜時點。
    只比指令行,不比原始字串 index:註解裡提到腳本名不算接線。"""
    cmds = [l for l in install_mod.HOOK.splitlines()
            if l.strip() and not l.lstrip().startswith("#")]
    leak = [i for i, l in enumerate(cmds) if "leak_scan.py" in l]
    gate = [i for i, l in enumerate(cmds) if "gate.py" in l and "--pre-commit" in l]
    assert leak, "HOOK 沒有執行 leak_scan 的指令行:裝出的 repo 對洩漏 commit 全放行"
    assert gate, "HOOK 沒有執行 gate.py --pre-commit 的指令行"
    assert leak[0] < gate[0], "洩漏偵測要在權威判定之前"


def test_hook_fails_closed_on_leak(install_mod):
    """leak_scan 非零退出必須終止 commit,不能只是印一句就往下走。"""
    line = next(l for l in install_mod.HOOK.splitlines() if "leak_scan.py" in l)
    assert "|| exit 1" in line


def test_gitignore_secrets_cover_common_shapes(install_mod):
    """新 repo 的第一個秘密通常叫 .env —— 預設值必須守到它與常見變體。
    副檔名組裝而不寫死:寫死會被 leak_scan 擋住本檔的 commit(同 test_leak_scan 手法)。"""
    secrets = set(install_mod.GITIGNORE_SECRETS)
    must_have = ((".env", ".env.*", "credentials.json", "service-account*.json")
                 + tuple("*." + ext for ext in ("pem", "pfx", "p12", "key")))
    for must in must_have:
        assert must in secrets, "秘密檔預設清單漏了 %s" % must
    assert "!.env.example" in secrets, ".env.example 是文件不是秘密,要留出口"


def test_framework_ignores_unchanged(install_mod):
    """框架垃圾清單不因秘密清單的加入而變動(前導斜線語意見 install.py 註解)。"""
    assert install_mod.GITIGNORE_FRAMEWORK == (
        "__pycache__/", ".cache/", "/.claude/skills/", "/skills/")
