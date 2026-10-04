# -*- coding: utf-8 -*-
"""宿主專用:agent-gates **自己**已提交的 evidence policy ↔ 已提交的 `pyproject.toml`(票 145)。

**不出貨**(`.agents/portable-manifest.txt` 標 `skip`)。它斷言的是**這個 repo** 的已提交事實,
而那兩個檔都是各 repo 自己的(`pyproject.toml` 標 `skip`、`.agents/evidence-policy.json` 標 `skip`)——
帶到下游就是「帶走測試卻不帶走它讀的檔案 = 到站即紅」(票 145〈四十六〉46.2 的 CI 失敗正是這個形狀)。

規格沿用票 145〈三十一〉裁決 3,**語意不變、只改適用位置**(〈四十八〉48.1 第 4 點,Jeff 明文):
  - 來源固定為 `git show HEAD:<path>`(在 repo 根執行,唯讀);不讀工作樹檔案;
  - 不得以 tmp repo 或寫死的 addopts 字串代替 —— 用自造設定只會驗到測試自己;
  - git 不可用或讀取失敗 ⇒ **失敗**(不得 skip、不得靜默通過);
  - 唯讀:不寫任何檔案、不改 repo 狀態。

推導(pytest 9.1.1;與原 test_d4 相同,**在本檔獨立實作**,不呼叫 redlight 的推導函式 ——
材料不從被量的東西身上拿):addopts 以 shlex 切開(`_pytest/config/__init__.py:1547`),逐一對應:
  - `OverrideIniAction` 旗標(`_pytest/main.py:76-96`):`--strict-config` → `strict_config=true`、
    `--strict-markers` → `strict_markers=true`、`--strict` → `strict=true`;
  - `-o` / `--override-ini KEY=VAL`(`_pytest/helpconfig.py:113-116`)→ `KEY=VAL`;
  - 其他旗標不產生 override 項目。
"""

import importlib.util
import json
import pathlib
import shlex
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]

POLICY_FILE = ".agents/evidence-policy.json"


def _load_redlight():
    spec = importlib.util.spec_from_file_location(
        "redlight_for_host_policy", str(ROOT / ".claude" / "hooks" / "redlight.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _git_show_head(rel):
    proc = subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:" + rel], capture_output=True)
    assert proc.returncode == 0, (rel, proc.stderr)
    return proc.stdout.decode("utf-8")


def _derive_overrides(addopts):
    tokens = shlex.split(addopts) if isinstance(addopts, str) else list(addopts or [])
    flags = {"--strict-config": "strict_config=true",
             "--strict-markers": "strict_markers=true",
             "--strict": "strict=true"}
    out = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in flags:
            out.append(flags[tok])
        elif tok in ("-o", "--override-ini"):
            i += 1
            out.append(tokens[i])
        elif tok.startswith("--override-ini="):
            out.append(tok.split("=", 1)[1])
        elif tok.startswith("-o"):
            out.append(tok[2:])
        i += 1
    return out


def test_the_committed_policy_matches_the_committed_pyproject():
    """票 145 Station 3g #27。分類:behavior-red(BASELINE 560f618 上 HEAD 沒有 policy ⇒ `git show` 失敗)。

    agent-gates 的 `HEAD:.agents/evidence-policy.json`:
      - schema / version 為 `monkeyleash.evidence-policy` / 1;
      - `config_file == "pyproject.toml"`;
      - `committed_overrides` 恰等於 `HEAD:pyproject.toml` 的 `[tool.pytest.ini_options].addopts` 依上方規則的推導;
      - 版本與 dist 欄位都在框架能力邊界之內(〈四十八〉48.1 第 3 點:界外 ⇒ 整份不合格,宿主自己這份必須先過)。
    """
    try:
        import tomllib as _toml
    except ImportError:                      # Python 3.10
        import tomli as _toml
    policy = json.loads(_git_show_head(POLICY_FILE))
    cfg = _toml.loads(_git_show_head("pyproject.toml"))
    addopts = cfg["tool"]["pytest"]["ini_options"].get("addopts")
    assert policy.get("schema") == "monkeyleash.evidence-policy" and policy.get("version") == 1, policy
    assert policy.get("config_file") == "pyproject.toml", policy
    assert policy.get("committed_overrides") == _derive_overrides(addopts), (addopts, policy)
    redlight = _load_redlight()
    assert set(policy.get("python_versions") or ()) <= set(redlight.KNOWN_PYTHON_VERSIONS), policy
    assert set(policy.get("pytest_versions") or ()) <= set(redlight.KNOWN_PYTEST_VERSIONS), policy
    assert set(tuple(d) for d in policy.get("dists") or ()) <= set(redlight.KNOWN_DISTS), policy
