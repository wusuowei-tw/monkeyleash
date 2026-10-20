# -*- coding: utf-8 -*-
"""閘門執行環境的身分自檢(票 156)。

閘門(hook、pre-commit、安裝器驗證)只能跑在 **`<repo>/.venv-gates`** 這個專用 venv 裡,
而且裡面裝的必須**恰好**是鎖定檔說的那一組(依 profile、依平台 marker 評估後的有效集合)。

    profile  downstream:預期集合 = gates-lock.txt
             upstream  :預期集合 = gates-lock.txt ∪ gates-lock-upstream-tests.txt

**預期集合依平台評估**(票面第三節第 4 條,Jeff 2026-10-19 16:32):同一份帶 hash 的
鎖定檔收多個平台的 artifact;身分比對比的是「這個平台實際應該安裝的那一組」。
只在 Windows 才裝的相依(例如 colorama)在 Linux 缺席,不算錯。

**import 本模組不讀任何鎖定檔**(S4b C2):只有呼叫 `load_locks()` / CLI 時才讀,
讀不到 ⇒ 由 `evaluate()` 明確 fail-closed,原因寫在 reasons 裡。

版本一律用 `importlib.metadata` 讀,不用 `pip show`(R0 §B6:cp950 主控台上會崩)。

CLI:runtime_identity.py --whoami --repo <repo> --profile <downstream|upstream>
     不帶 --whoami 時只在失敗時印原因。退出碼:0 = 合法;1 = 不合法;2 = 參數錯誤。
"""

import argparse
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_ROOT = os.path.dirname(os.path.dirname(HERE))

LOCK_CORE_REL = ".claude/portable/gates-lock.txt"
LOCK_UPSTREAM_TESTS_REL = ".claude/portable/gates-lock-upstream-tests.txt"
PROFILES = ("downstream", "upstream")
VENV_DIRNAME = ".venv-gates"
PYTHON_MAJOR_MINOR = (3, 11)

# runtime-bootstrap 例外(D-4,**暫定**):`python -m venv` 依底座 3.11.9 的
# `Lib/ensurepip/_bundled/` 預裝的兩個套件(S3a 第 5 節,〔讀碼推論〕)。
# **名稱＋精確版本**:版本不同就不是例外。實作站建出真的 `.venv-gates` 後觀測確認;
# 觀測不同就停,不得為了轉綠擴大這份清單。
BOOTSTRAP_EXCEPTIONS = (("pip", "24.0"), ("setuptools", "65.5.0"))


def normalize(name):
    """PEP 503 名稱正規化:`PyYAML` ≡ `pyyaml`、`typing_extensions` ≡ `typing-extensions`。

    這是**套件名稱**的標準等價,不是 hook 內容那種「能不正規化就不正規化」(G2)。
    不做的話,metadata 寫 `PyYAML`、鎖定檔寫 `pyyaml`,每台機器都會誤紅。
    """
    return re.sub(r"[-_.]+", "-", str(name)).lower()


def _logical_lines(text):
    """把 `\\` 續行接起來、丟掉註解與空行。"""
    out, buf = [], ""
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.endswith("\\"):
            buf += line[:-1] + " "
            continue
        buf += line
        s = buf.strip()
        buf = ""
        if s and not s.startswith("#"):
            out.append(s)
    if buf.strip() and not buf.strip().startswith("#"):
        out.append(buf.strip())
    return out


_REQ = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?\s*==\s*([^\s;]+)$")


def parse_lock(text):
    """鎖定檔 → `[(正規化名稱, 精確版本, marker 或 None)]`。

    每一筆必須是 `名稱==版本`(可帶 `; marker` 與 `--hash=`)。其他形狀一律 ValueError ——
    鎖定檔裡出現一筆沒釘死版本的需求,不是可以略過的格式問題。
    """
    out = []
    for line in _logical_lines(text):
        if line.startswith("-"):
            continue                       # pip 選項行(例如 --index-url)
        req = re.sub(r"\s--hash=\S+", "", " " + line).strip()
        marker = None
        if ";" in req:
            req, marker = req.split(";", 1)
            req, marker = req.strip(), marker.strip() or None
        m = _REQ.match(req)
        if not m:
            raise ValueError("鎖定檔有一筆不是「名稱==精確版本」:%r" % line)
        out.append((normalize(m.group(1)), m.group(2), marker))
    return out


def expected_set(lock_texts, marker_env):
    """依平台 marker 評估後的**有效集合** `{正規化名稱: 版本}`。

    marker 用 `packaging.markers` 評估(D-7)—— 與 pip 同一套語意,不另寫第二份直譯器。
    同一套件在不同鎖定檔裡版本不一致 ⇒ ValueError(不得有兩套會互相漂移的版本)。
    """
    from packaging.markers import Marker

    out = {}
    for text in lock_texts:
        for name, version, marker in parse_lock(text):
            if marker is not None and not Marker(marker).evaluate(environment=dict(marker_env)):
                continue
            if name in out and out[name] != version:
                raise ValueError("%s 在鎖定檔之間版本不一致:%s 與 %s" % (name, out[name], version))
            out[name] = version
    return out


def boundary_violations(dists, known_dists):
    """能力邊界只看**實際出現**的項目:屬於邊界家族(名稱出現在 `known_dists`)的 dist,
    其 (名稱, 版本) 必須落在邊界內。沒出現的不要求存在(downstream 沒有 anyio 是合法的)。"""
    known = set((normalize(n), v) for n, v in known_dists)
    family = set(n for n, _v in known)
    return [(n, v) for n, v in dists if normalize(n) in family and (normalize(n), v) not in known]


def _same_path(a, b):
    return os.path.normcase(os.path.realpath(str(a))) == os.path.normcase(os.path.realpath(str(b)))


def evaluate(facts, locks, marker_env, profile):
    """身分判定。回 `(ok, reasons)`;reasons 每一條都要說出是哪一項不成立。

    facts   = {"prefix", "base_prefix", "version_info", "repo", "dists": [(name, version)]}
    locks   = {"core": <gates-lock.txt 全文或 None>, "upstream_tests": <全文或 None>}
    profile = "downstream" | "upstream"
    """
    reasons = []
    if profile not in PROFILES:
        reasons.append("profile 只能是 %s,收到 %r" % ("/".join(PROFILES), profile))
        return False, reasons
    repo = facts.get("repo")
    venv = os.path.join(str(repo), VENV_DIRNAME)
    prefix, base = facts.get("prefix"), facts.get("base_prefix")
    if prefix is None or base is None or _same_path(prefix, base):
        reasons.append("不在 venv 裡(sys.prefix == sys.base_prefix:%s);閘門只認 %s" % (prefix, venv))
    elif not _same_path(prefix, venv):
        reasons.append("sys.prefix 不是本 repo 的 .venv-gates:實得 %s,應為 %s" % (prefix, venv))
    vi = tuple(facts.get("version_info") or ())
    if tuple(vi[:2]) != PYTHON_MAJOR_MINOR:
        reasons.append("Python 必須是 %d.%d.x,實得 %s"
                       % (PYTHON_MAJOR_MINOR + (".".join(str(x) for x in vi) or "?",)))

    texts = []
    if not locks.get("core"):
        reasons.append("核心鎖定檔讀不到(%s);無法判定預期集合" % LOCK_CORE_REL)
    else:
        texts.append(locks["core"])
    if profile == "upstream":
        if not locks.get("upstream_tests"):
            reasons.append("上游測試鎖定檔讀不到(%s);upstream profile 無法判定" % LOCK_UPSTREAM_TESTS_REL)
        else:
            texts.append(locks["upstream_tests"])
    if len(texts) != (2 if profile == "upstream" else 1):
        return False, reasons
    try:
        expected = expected_set(texts, marker_env)
    except Exception as e:                       # 解析失敗 / marker 失敗 / packaging 不在 ⇒ fail-closed
        reasons.append("預期集合算不出來(%s:%s)" % (type(e).__name__, e))
        return False, reasons

    installed = {}
    for name, version in facts.get("dists") or []:
        installed[normalize(name)] = version
    for name in sorted(expected):
        got = installed.get(name)
        if got is None:
            reasons.append("缺少 %s==%s(%s profile 的預期集合)" % (name, expected[name], profile))
        elif got != expected[name]:
            reasons.append("%s 版本 %s 與鎖定檔 %s 不符" % (name, got, expected[name]))
    exceptions = set((normalize(n), v) for n, v in BOOTSTRAP_EXCEPTIONS)
    for name in sorted(installed):
        if name in expected or (name, installed[name]) in exceptions:
            continue
        reasons.append("額外套件 %s==%s(不在 %s profile 的預期集合,也不是已登記的 runtime-bootstrap 例外)"
                       % (name, installed[name], profile))
    return not reasons, reasons


def load_locks(src_root=None):
    """讀**本模組所在 repo** 的兩份鎖定檔;讀不到的那一份為 None(由 evaluate 判 fail-closed)。"""
    root = src_root or SRC_ROOT
    out = {}
    for key, rel in (("core", LOCK_CORE_REL), ("upstream_tests", LOCK_UPSTREAM_TESTS_REL)):
        p = os.path.join(root, *rel.split("/"))
        try:
            with io.open(p, encoding="utf-8") as f:
                out[key] = f.read()
        except (IOError, OSError):
            out[key] = None
    return out


def collect_facts(repo):
    """**正在執行的這支直譯器**的事實。版本取自 `importlib.metadata`(安裝器寫的那一側)。"""
    from importlib import metadata

    dists, seen = [], set()
    for d in metadata.distributions():
        name = d.metadata.get("Name") if d.metadata else None
        if not name or normalize(name) in seen:
            continue
        seen.add(normalize(name))
        dists.append((name, d.version))
    return {"prefix": sys.prefix, "base_prefix": sys.base_prefix,
            "version_info": tuple(sys.version_info[:3]), "repo": repo, "dists": sorted(dists)}


def _marker_env():
    from packaging.markers import default_environment
    return default_environment()


def _write(text):
    """utf-8 位元組輸出(與 install._out 同一手法:cp950 主控台上不得崩)。"""
    sys.stdout.flush()
    sys.stdout.buffer.write((text + "\n").encode("utf-8"))
    sys.stdout.buffer.flush()


def main(argv=None):
    ap = argparse.ArgumentParser(description="閘門執行環境的身分自檢(票 156)")
    ap.add_argument("--whoami", action="store_true", help="印出完整身分")
    ap.add_argument("--repo", required=True, help="repo 根目錄(預期 venv 為 <repo>/.venv-gates)")
    ap.add_argument("--profile", required=True, choices=PROFILES)
    args = ap.parse_args(argv)
    facts = collect_facts(os.path.abspath(args.repo))
    try:
        env = _marker_env()
    except Exception as e:
        env, env_err = {}, "marker 環境取不到(%s:%s)" % (type(e).__name__, e)
    else:
        env_err = None
    ok, reasons = evaluate(facts, load_locks(), env, args.profile)
    if env_err:
        ok, reasons = False, reasons + [env_err]
    if args.whoami:
        _write("profile: %s" % args.profile)
        _write("interpreter: %s" % sys.executable)
        _write("sys.prefix: %s" % sys.prefix)
        _write("python: %s" % ".".join(str(x) for x in facts["version_info"]))
        _write("packages:")
        for name, version in facts["dists"]:
            _write("  %s==%s" % (name, version))
        _write("identity: %s" % ("ok" if ok else "FAIL"))
    if not ok:
        for r in reasons:
            _write("  - %s" % r)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
