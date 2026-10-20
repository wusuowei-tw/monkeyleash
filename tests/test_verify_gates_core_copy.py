# -*- coding: utf-8 -*-
"""verify_gates 核心模式的離線複製(票 156 S4f-甲,方案 (d))—— **上游專屬,不出貨**。

由 `tests/test_verify_gates.py` 原樣搬來(裁決 S4f-丁,Jeff 2026-10-20 約 15:31):
這組讀上游 repo 自己已安裝的 `.venv-gates`,在下游與淨室 target 裡沒有意義,
所以 manifest 標 skip,比照 `tests/test_runtime_identity_upstream.py`。
"""
import importlib.util
import os
import subprocess

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PORTABLE = os.path.join(HERE, "..", ".claude", "portable")


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(PORTABLE, filename))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


vg = _load("verify_gates_under_test_core_copy", "verify_gates.py")


# ─────────────────────────────────────────────────────────────────────────────
# 票 156 S4f-1 紅燈 —— 裁決 S4f-甲:核心模式的假安裝步驟改成「離線複製」
# (Jeff 2026-10-20 約 13:53)
#
# 核心模式從**上游已安裝**的 `<SRC_ROOT>/.venv-gates` 複製 downstream 有效集合
# (payload + `*.dist-info`)進暫存 target 的 `.venv-gates`,讓 install 的事前檢查
# 與其後的端到端情境在**不連網**時也走得通。
#
# **這裡證明的是自洽**:上游 venv 的子集能通過 downstream 身分檢查。
# 鎖定檔「真的裝得起來」由 CI 整合步驟(`id: gates-bootstrap-integration`)證明。
#
# 接縫:`_core_install_offline` 是既有的(D-11)。來源路徑的接縫 `_core_source_venv`
# 是本站**假設**的名字 —— 紅燈要的是「來源缺失 / 不合法時 fail-closed」,不是這個名字;
# S4f-2 選的接縫若不同,改 patch 目標不算改規格,斷言不得放寬。
#
# **只在上游跑**:本檔在 manifest 標 skip,不出貨、上游專屬(裁決 S4f-丁)。
# 下游與 verify_gates 的淨室 target 沒有「上游已安裝的 .venv-gates」可言(那裡的 `SRC_ROOT` 是 target 自己)。
# 自動跳過的守衛仍保留,判別用上游測試鎖定檔是否存在 —— 與 `bootstrap.sh` 選 profile 同一個慣例。
# ─────────────────────────────────────────────────────────────────────────────

_S4F_UPSTREAM_VENV = os.path.join(vg.SRC_ROOT, ".venv-gates")
_S4F_RI = os.path.join(vg.SRC_ROOT, ".claude", "portable", "runtime_identity.py")
_S4F_MARK = "[verify_gates/核心]"


def _s4f_is_upstream():
    return os.path.isfile(os.path.join(vg.SRC_ROOT, *vg.runtime_identity.LOCK_UPSTREAM_TESTS_REL.split("/")))


def _s4f_python(venv_dir):
    if os.name == "nt":
        return os.path.join(venv_dir, "Scripts", "python.exe")
    return os.path.join(venv_dir, "bin", "python")


def _s4f_site(venv_dir):
    import glob
    if os.name == "nt":
        cands = [os.path.join(venv_dir, "Lib", "site-packages")]
    else:
        cands = sorted(glob.glob(os.path.join(venv_dir, "lib", "python3.*", "site-packages")))
    cands = [c for c in cands if os.path.isdir(c)]
    assert len(cands) == 1, "找不到唯一的 site-packages:%s → %r" % (venv_dir, cands)
    return cands[0]


def _s4f_downstream_set():
    """downstream 有效集合 `{正規化名稱: 版本}`(核心鎖定檔、目前平台的 marker)。"""
    ri = vg.runtime_identity
    return ri.expected_set([ri.load_locks()["core"]], ri._marker_env())


def _s4f_dists(site):
    """site-packages 內的 dist:`{正規化名稱: Distribution}`。"""
    import importlib.metadata as md
    out = {}
    for d in md.distributions(path=[site]):
        name = d.metadata.get("Name") if d.metadata else None
        if name:
            out[vg.runtime_identity.normalize(name)] = d
    return out


def _s4f_payload(site, dist):
    """dist 在 `site` 之內、實際存在的檔案(相對 site 的路徑;不含 __pycache__)。site 之外的(Scripts/bin 進入點)不算。"""
    assert dist.files is not None, "%s 沒有 RECORD,判不出 payload" % dist.metadata.get("Name")
    site_abs = os.path.normcase(os.path.realpath(site))
    out = []
    for f in dist.files:
        p = os.path.realpath(str(dist.locate_file(f)))
        if not os.path.normcase(p).startswith(site_abs + os.sep) or not os.path.isfile(p):
            continue
        rel = os.path.relpath(p, os.path.realpath(site))
        if "__pycache__" in rel.split(os.sep):
            continue
        out.append(rel)
    return out


def _s4f_identity(target):
    """D-10 / 規格 4:target 的直譯器跑**上游**的 runtime_identity,`--repo` 指向 target。"""
    argv = [_s4f_python(os.path.join(str(target), ".venv-gates")), _S4F_RI,
            "--whoami", "--repo", str(target), "--profile", "downstream"]
    p = subprocess.run(argv, capture_output=True)
    out = (p.stdout + p.stderr).decode("utf-8", "replace")
    lines = [l for l in out.splitlines() if l.strip()]
    return p.returncode, (lines[-1] if lines else ""), out


def _s4f_sysexit_text(excinfo):
    return str(excinfo.value.code)


class TestS4fCoreCopiesFromUpstreamVenv:

    @pytest.fixture(autouse=True)
    def _upstream_only(self):
        if not _s4f_is_upstream():
            pytest.skip("上游專屬:沒有上游測試鎖定檔(下游或淨室 target)")
        assert os.path.isfile(_s4f_python(_S4F_UPSTREAM_VENV)), \
            "上游 .venv-gates 不存在 —— 這組測試只依賴上游已存在且合法的 .venv-gates,不自己建"

    def test_s4f_d_copied_target_is_complete_usable_and_passes_downstream_identity(self, tmp_path):
        """規格 2 + 4:真建環境。(i) target 直譯器 `-I` 匯入 yaml / pytest,且模組在 target 的 venv 之內;
        (ii) 每個 downstream 套件在來源 site-packages 內的檔案,target 都有同一相對路徑;不得多複製;
        (4) 上游 runtime_identity 對 target 的 downstream 身分為 ok。"""
        target = tmp_path / "target"
        vg.prepare_target_env(str(target))
        venv = os.path.join(str(target), ".venv-gates")
        py = _s4f_python(venv)

        # (i) 可用性
        p = subprocess.run([py, "-I", "-c", "import yaml, pytest; print(yaml.__file__); print(pytest.__file__)"],
                           capture_output=True)
        out = (p.stdout + p.stderr).decode("utf-8", "replace")
        assert p.returncode == 0, out
        venv_abs = os.path.normcase(os.path.realpath(venv))
        for line in [l for l in out.splitlines() if l.strip()][-2:]:
            assert os.path.normcase(os.path.realpath(line.strip())).startswith(venv_abs + os.sep), (line, venv)

        # (ii) 完整性:逐套件、逐檔
        src_site, dst_site = _s4f_site(_S4F_UPSTREAM_VENV), _s4f_site(venv)
        src = _s4f_dists(src_site)
        expected = _s4f_downstream_set()
        missing = []
        for name in sorted(expected):
            assert name in src, "上游 .venv-gates 沒有 %s —— 上游環境本身不合法" % name
            for rel in _s4f_payload(src_site, src[name]):
                if not os.path.isfile(os.path.join(dst_site, rel)):
                    missing.append((name, rel))
        assert not missing, "target 缺 %d 個檔(前 10 個):%r" % (len(missing), missing[:10])

        # 不得多複製:target 的 dist = downstream 有效集合 ∪ runtime-bootstrap 例外
        allowed = set(expected) | set(vg.runtime_identity.normalize(n)
                                      for n, _v in vg.runtime_identity.BOOTSTRAP_EXCEPTIONS)
        got = set(_s4f_dists(dst_site))
        assert got <= allowed, "多複製了:%s" % sorted(got - allowed)

        # (4) 結果可驗
        rc, last, full = _s4f_identity(target)
        assert rc == 0 and last == "identity: ok", full

    def test_s4f_d_source_is_the_upstream_repo_venv_checked_first(self, tmp_path, monkeypatch):
        """規格 1:來源是 `<SRC_ROOT>/.venv-gates`,不是 `sys.prefix`;複製**之前**先以來源直譯器跑
        上游 runtime_identity `--profile upstream`(`--repo` = 上游根)。"""
        import sys
        target = tmp_path / "target"
        bogus = tmp_path / "bogus-prefix"
        bogus.mkdir()
        monkeypatch.setattr(sys, "prefix", str(bogus))
        real_run = subprocess.run
        seen = []

        def recording_run(args, *a, **k):
            argv = [str(x) for x in args] if isinstance(args, (list, tuple)) else [str(args)]
            dst = os.path.join(str(target), ".venv-gates")
            yaml_there = os.path.isdir(dst) and any(
                os.path.isdir(os.path.join(s, "yaml")) for s in
                [os.path.join(dst, "Lib", "site-packages")] + [os.path.join(dst, "lib", v, "site-packages")
                                                             for v in ("python3.11",)])
            seen.append((argv, yaml_there))
            return real_run(args, *a, **k)
        monkeypatch.setattr(subprocess, "run", recording_run)
        vg.prepare_target_env(str(target))
        monkeypatch.undo()

        up_abs = os.path.normcase(os.path.realpath(_S4F_UPSTREAM_VENV))
        root_abs = os.path.normcase(os.path.realpath(vg.SRC_ROOT))
        checks = [(argv, yaml_there) for argv, yaml_there in seen
                  if any(os.path.basename(x) == "runtime_identity.py" for x in argv)
                  and "--profile" in argv and argv[argv.index("--profile") + 1:argv.index("--profile") + 2] == ["upstream"]]
        assert checks, "沒有看到以 upstream profile 檢查來源的呼叫:%r" % [a for a, _ in seen]
        argv, yaml_there = checks[0]
        assert os.path.normcase(os.path.realpath(argv[0])).startswith(up_abs + os.sep), argv
        assert "--repo" in argv and \
            os.path.normcase(os.path.realpath(argv[argv.index("--repo") + 1])) == root_abs, argv
        assert not yaml_there, "來源檢查發生在複製之後"

        # 複製出來的位元組來自上游 venv(不是 sys.prefix,也不是別的環境)
        src_site, dst_site = _s4f_site(_S4F_UPSTREAM_VENV), _s4f_site(os.path.join(str(target), ".venv-gates"))
        rel = os.path.join("yaml", "__init__.py")
        assert os.path.isfile(os.path.join(dst_site, rel)), "target 沒有 %s" % rel
        with open(os.path.join(src_site, rel), "rb") as a, open(os.path.join(dst_site, rel), "rb") as b:
            assert a.read() == b.read()

    def test_s4f_d_no_network_no_pip_install_and_still_identity_ok(self, tmp_path, monkeypatch):
        """規格 3:prepare 期間真的 `_install_lock` 一次都不呼叫、不起任何 `pip install` 子行程 ——
        **而且**結果仍然合法(只監測不連網的話,現行什麼都不裝的假步驟會恆綠)。"""
        def no_install_lock(*a, **k):
            raise AssertionError("核心模式呼叫了真正的 _install_lock(會連網)")
        monkeypatch.setattr(vg.setup_gates_env, "_install_lock", no_install_lock)

        def is_pip_install(args):
            argv = [str(x) for x in args] if isinstance(args, (list, tuple)) else str(args).split()
            return "pip" in argv and "install" in argv

        real_run, real_popen = subprocess.run, subprocess.Popen

        def guarded_run(args, *a, **k):
            if is_pip_install(args):
                raise AssertionError("核心模式啟動了 pip install:%r" % (args,))
            return real_run(args, *a, **k)

        def guarded_popen(args, *a, **k):
            if is_pip_install(args):
                raise AssertionError("核心模式啟動了 pip install:%r" % (args,))
            return real_popen(args, *a, **k)
        monkeypatch.setattr(subprocess, "run", guarded_run)
        monkeypatch.setattr(subprocess, "Popen", guarded_popen)

        target = tmp_path / "target"
        vg.prepare_target_env(str(target))
        monkeypatch.undo()
        rc, last, full = _s4f_identity(target)
        assert rc == 0 and last == "identity: ok", full

    def test_s4f_d_missing_source_venv_is_fail_closed(self, tmp_path, monkeypatch):
        """規格 5(一):上游沒有 `.venv-gates` ⇒ 明確 SystemExit(含 `[verify_gates/核心]`),target 不得有任何套件。"""
        nowhere = tmp_path / "no-upstream" / ".venv-gates"
        monkeypatch.setattr(vg, "_core_source_venv", lambda *a, **k: str(nowhere), raising=False)
        target = tmp_path / "target"
        with pytest.raises(SystemExit) as e:
            vg.prepare_target_env(str(target))
        assert _S4F_MARK in _s4f_sysexit_text(e), _s4f_sysexit_text(e)
        dst = os.path.join(str(target), ".venv-gates")
        if os.path.isdir(dst):
            assert not set(_s4f_dists(_s4f_site(dst))) & set(_s4f_downstream_set()), "來源缺失卻寫入了套件"

    def test_s4f_d_invalid_source_identity_is_fail_closed(self, tmp_path, monkeypatch):
        """規格 1 + 5(二):來源存在但過不了 upstream 身分(這裡用一個空 venv 當壞來源 ——
        它**不是**上游環境,只是一個離線建的反例)⇒ SystemExit(含 `[verify_gates/核心]`),target 不寫入套件。"""
        import venv
        bad = tmp_path / "bad-upstream" / ".venv-gates"
        venv.EnvBuilder(with_pip=False).create(str(bad))
        monkeypatch.setattr(vg, "_core_source_venv", lambda *a, **k: str(bad), raising=False)
        target = tmp_path / "target"
        with pytest.raises(SystemExit) as e:
            vg.prepare_target_env(str(target))
        assert _S4F_MARK in _s4f_sysexit_text(e), _s4f_sysexit_text(e)
        dst = os.path.join(str(target), ".venv-gates")
        if os.path.isdir(dst):
            assert not set(_s4f_dists(_s4f_site(dst))) & set(_s4f_downstream_set()), "來源不合法卻寫入了套件"

    def test_s4f_d_negative_control_metadata_only_copy_is_rejected(self, tmp_path, monkeypatch):
        """規格 2 負控:壞的複製(除 `packaging` 外**只**複製 `*.dist-info`、不複製 payload)
        ⇒ 正式程式碼必須在宣告成功**之前**拒絕它(SystemExit)。正常回傳 = 本測試 FAIL。

        `packaging` 例外照完整複製:runtime_identity 自己要 import 它。不留它的話,壞實作會先在
        身分檢查就倒下,而本條要逼出的是「身分 ok 之外的 payload 驗證」—— metadata 全在時
        `identity: ok` 仍可能成立,光靠它不夠。"""
        import shutil
        src_site = _s4f_site(_S4F_UPSTREAM_VENV)
        src = _s4f_dists(src_site)
        expected = _s4f_downstream_set()

        def metadata_only_copy(python, locks):
            dst_site = _s4f_site(os.path.dirname(os.path.dirname(python)))
            for name in sorted(expected):
                for rel in _s4f_payload(src_site, src[name]):
                    top = rel.split(os.sep)[0]
                    if name != "packaging" and not top.endswith(".dist-info"):
                        continue
                    os.makedirs(os.path.dirname(os.path.join(dst_site, rel)), exist_ok=True)
                    shutil.copy2(os.path.join(src_site, rel), os.path.join(dst_site, rel))
        monkeypatch.setattr(vg, "_core_install_offline", metadata_only_copy)

        target = tmp_path / "target"
        with pytest.raises(SystemExit):
            vg.prepare_target_env(str(target))


# ─────────────────────────────────────────────────────────────────────────────
# 票 156 S3b 紅燈 D-11 (b)(c) —— 由 `tests/test_verify_gates.py::TestT156D11OfflineCore` 原樣搬來
# (裁決 S4f-丁之二,Jeff 2026-10-20 約 16:06)。D-11 (a) 留在原檔。
#
# 兩條都依賴上游:(b) 呼叫真的 `prepare_target_env`,而它先驗上游已安裝的 `.venv-gates`;
# (c) 讀上游測試鎖定檔。淨室 target 裡兩者都不存在 ⇒ 出貨的話,淨室的框架測試會紅。
# ─────────────────────────────────────────────────────────────────────────────

class TestT156D11OfflineCoreUpstream:

    def test_d11_b_the_core_mode_never_runs_the_real_install_or_touches_the_network(self, tmp_path,
                                                                                  monkeypatch):
        """(b):核心模式下 setup 的安裝步驟是假步驟 —— 真正的 `_install_lock` 一次都沒被呼叫;
        行程內任何 socket 連線都會撞上哨兵。"""
        import socket
        prepare = getattr(vg, "prepare_target_env", None)
        setup_mod = getattr(vg, "setup_gates_env", None)
        assert prepare is not None and setup_mod is not None, \
            "verify_gates 沒有 prepare_target_env / setup_gates_env(票 156 實作站產生)"
        real_install = []

        def sentinel_install(*a, **k):
            real_install.append(a)
            raise AssertionError("核心模式呼叫了真正的 _install_lock(會連網)")
        monkeypatch.setattr(setup_mod, "_install_lock", sentinel_install)

        def no_network(*a, **k):
            raise AssertionError("核心模式發出了網路連線:%r" % (a,))
        monkeypatch.setattr(socket.socket, "connect", no_network)
        t = tmp_path / "target"
        t.mkdir()
        for args in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
            subprocess.run(["git"] + args, cwd=str(t), capture_output=True, check=True)
        prepare(str(t))
        assert real_install == []
        assert (t / ".venv-gates").is_dir()

    def test_d11_c_the_pos2_policy_uses_the_upstream_profile_set(self, tmp_path, monkeypatch):
        """(c):正二政策的 dists = upstream profile 的有效集合 ∩ `KNOWN_DISTS`,**不讀全域環境**。
        環境裡裝的是 anyio 4.15.1(也在能力邊界內),鎖定檔是 4.15.0 ⇒ 政策必須是 4.15.0。"""
        import importlib.metadata as md
        import shutil
        t = tmp_path / "target"
        (t / ".claude" / "hooks").mkdir(parents=True)
        shutil.copy2(os.path.join(HERE, "..", ".claude", "hooks", "redlight.py"),
                     str(t / ".claude" / "hooks" / "redlight.py"))
        real_version = md.version

        def fake_version(name):
            return {"anyio": "4.15.1", "pytest": "9.1.1"}.get(name) or real_version(name)
        monkeypatch.setattr(md, "version", fake_version)
        pol = vg._ev_matching_policy(str(t))
        assert pol["dists"] == [["anyio", "4.15.0"]], pol["dists"]
        assert pol["pytest_versions"] == ["9.1.1"], pol["pytest_versions"]
