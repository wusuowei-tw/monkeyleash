# -*- coding: utf-8 -*-
"""票 156 —— 只在上游成立的那幾條:RT5(b)、RT12、上游 `.gitignore`。

**本檔標 skip(只在上游)**:它讀 `.claude/portable/gates-lock-upstream-tests.txt`
(G1:skip,下游沒有)與上游自己的 manifest / `.gitignore`。出貨到下游的話,
每個下游都會天生帶一條與自己無關的紅(F-031)。
"""
import importlib.util
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
RI_PATH = ROOT / ".claude" / "portable" / "runtime_identity.py"
UPSTREAM_LOCK = ROOT / ".claude" / "portable" / "gates-lock-upstream-tests.txt"
MANIFEST = ROOT / ".agents" / "portable-manifest.txt"


def _ri():
    assert RI_PATH.is_file(), "runtime_identity.py 不存在(票 156 實作站產生):%s" % RI_PATH
    spec = importlib.util.spec_from_file_location("runtime_identity_upstream_test", str(RI_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_rt5_the_upstream_tests_lock_pins_mcp_and_anyio():
    """RT5(b):只有上游測試鎖定檔可以含 mcp / anyio,而且版本釘死(D7、D9)。"""
    ri = _ri()
    assert UPSTREAM_LOCK.is_file(), "上游測試鎖定檔不存在:%s" % UPSTREAM_LOCK
    got = {n: v for n, v, _m in ri.parse_lock(UPSTREAM_LOCK.read_text(encoding="utf-8"))}
    assert got.get("mcp") == "1.29.1", got
    assert got.get("anyio") == "4.15.0", got


# ── RT12:G1 逐檔分類 ──────────────────────────────────────────────────────────
#
# **比對的是 manifest 裡逐字的那一行,不是 `explicit_mark()` 的結果。**
# G1 明文:「不得靠目錄前綴推斷」—— 而 `.claude/portable/` 本來就有一筆 copy 前綴,
# 用 `explicit_mark()` 問的話,四個 copy 檔在動工前就會「假綠」,
# 而那個綠是前綴給的,不是 G1 要的那一行給的。

G1_TABLE = {
    ".claude/portable/gates-lock.txt": "copy",
    ".claude/portable/runtime_identity.py": "copy",
    ".claude/portable/setup_gates_env.py": "copy",
    ".claude/bin/gatepy": "copy",
    ".claude/portable/gates-lock-upstream-tests.txt": "skip",
    # 本票新增的測試檔(S3a 6-7 的分類表,D-5)
    "tests/test_runtime_identity.py": "copy",
    "tests/test_runtime_identity_upstream.py": "skip",
    "tests/test_setup_gates_env.py": "copy",
    "tests/test_gatepy.py": "skip",
    "tests/fixtures/hooks/": "copy",
}


def _manifest_lines():
    out = {}
    for line in MANIFEST.read_text(encoding="utf-8-sig").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        if len(parts) >= 2:
            out[parts[0]] = parts[1]
    return out


@pytest.mark.parametrize("rel", sorted(G1_TABLE))
def test_rt12_each_new_file_has_its_own_manifest_line(rel):
    lines = _manifest_lines()
    assert rel in lines, "manifest 沒有 %s 自己的那一行(G1:不得靠前綴推斷)" % rel
    assert lines[rel] == G1_TABLE[rel], (rel, lines[rel], G1_TABLE[rel])


def test_the_upstream_gitignore_ignores_venv_gates():
    """上游自己的 `.gitignore` 要有 `.venv-gates/`(第三節第 1 條)。"""
    lines = [l.strip() for l in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()]
    assert any(l in (".venv-gates/", "/.venv-gates/") for l in lines), \
        "上游 .gitignore 沒有 .venv-gates/"
