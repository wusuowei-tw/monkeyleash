# -*- coding: utf-8 -*-
"""安裝器 —— 預設值(F-062)與產出的標記表。

**為什麼這個檔案叫 `test_install.py`**:R3 由實作反查測試,規則問的是
`tests/test_<實作名>.py`。既有的測試叫 `test_install_defaults.py` ——
對人來說看得出是它的測試,**對規則來說 `install.py` 沒有測試**,
於是 R3 的前半永遠擋著它,而擋下的訊息說「請先寫測試」,
現場卻是測試早就寫好了。人看名字的意思,規則看名字的形狀。

`test_install_defaults.py` 的內容已併進本檔(`git mv` + 合併)。
先前判斷「R7 沒有刪除出口所以併不了」是錯的 —— 見 F-076:
被擋的是我加了 `cd` 前綴的指令形狀,不是 `git mv` 本身。
"""
import importlib.util
import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PORTABLE = os.path.join(HERE, "..", ".claude", "portable")


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(PORTABLE, filename))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def install_mod():
    return _load("install_under_test", "install.py")


@pytest.fixture(scope="module")
def manifest_mod():
    return _load("manifest_for_install_test", "manifest.py")


class TestInstallerDefaults:
    """安裝器預設值(F-062):洩漏 hook 接線 + .gitignore 秘密檔。

    負控實測(2026-08-11,真安裝出的 repo):HOOK 只接 gate.py 時,
    含真 API key 的 commit 直接成功 —— F-055(洩漏 hook 不隨 clone 走)
    的安裝端後果。這裡把兩個預設值釘成紅燈過的規格。
    """

    def test_hook_wires_leak_scan_before_gate(self, install_mod):
        """pre-commit 樣板必須先跑 leak_scan 再跑 gate —— 秘密進歷史前的唯一便宜時點。
        只比指令行,不比原始字串 index:註解裡提到腳本名不算接線。"""
        cmds = [l for l in install_mod.HOOK.splitlines()
                if l.strip() and not l.lstrip().startswith("#")]
        leak = [i for i, l in enumerate(cmds) if "leak_scan.py" in l]
        gate = [i for i, l in enumerate(cmds)
                if "gate.py" in l and "--pre-commit" in l]
        assert leak, "HOOK 沒有執行 leak_scan 的指令行:裝出的 repo 對洩漏 commit 全放行"
        assert gate, "HOOK 沒有執行 gate.py --pre-commit 的指令行"
        assert leak[0] < gate[0], "洩漏偵測要在權威判定之前"

    def test_hook_fails_closed_on_leak(self, install_mod):
        """leak_scan 非零退出必須終止 commit,不能只是印一句就往下走。"""
        line = next(l for l in install_mod.HOOK.splitlines() if "leak_scan.py" in l)
        assert "|| exit 1" in line

    def test_gitignore_secrets_cover_common_shapes(self, install_mod):
        """新 repo 的第一個秘密通常叫 .env —— 預設值必須守到它與常見變體。
        副檔名組裝而不寫死:寫死會被 leak_scan 擋住本檔的 commit。"""
        secrets = set(install_mod.GITIGNORE_SECRETS)
        must_have = ((".env", ".env.*", "credentials.json",
                      "service-account*.json")
                     + tuple("*." + ext for ext in ("pem", "pfx", "p12", "key")))
        for must in must_have:
            assert must in secrets, "秘密檔預設清單漏了 %s" % must
        assert "!.env.example" in secrets, ".env.example 是文件不是秘密,要留出口"

    def test_framework_ignores_unchanged(self, install_mod):
        """框架垃圾清單不因秘密清單的加入而變動(前導斜線語意見 install.py 註解)。"""
        assert install_mod.GITIGNORE_FRAMEWORK == (
            "__pycache__/", ".cache/", "/.claude/skills/", "/skills/")


class TestEnumerationDoesNotLoseFilesToGitignore:
    """`--exclude-standard` 把 **ignored** 排除在外 —— 補了 untracked,少了這半。

    `source_files()` 的 docstring **描述了同一個病**:
    「只取 `git ls-files` 的話,還沒 commit 的框架檔會靜默漏帶:
    安裝照樣成功、閘門照樣擋、輸出全綠。」它修好了 untracked 那半就停了。

    量化實測:`.claude/` 被 gitignore → 框架檔完全不進列舉 →
    裝出**沒有閘門的 repo** → `verify_gates` 崩潰。而安裝本身是成功的、安靜的。
    """

    def test_ignored_framework_files_are_enumerated(self, install_mod, tmp_path,
                                                    monkeypatch):
        import subprocess
        root = tmp_path / "src"
        (root / ".claude" / "hooks").mkdir(parents=True)
        for c in ("init -q", "config user.email t@t", "config user.name t"):
            subprocess.run(["git"] + c.split(), cwd=str(root), capture_output=True)
        open(str(root / ".claude" / "hooks" / "gate.py"), "w").write("x = 1\n")
        open(str(root / ".gitignore"), "w").write(".claude/\n")
        subprocess.run(["git", "add", "-A"], cwd=str(root), capture_output=True)
        subprocess.run(["git", "commit", "-qm", "b"], cwd=str(root),
                       capture_output=True)
        monkeypatch.setattr(install_mod, "SRC_ROOT", str(root))

        all_files, _ = install_mod.source_files()
        assert ".claude/hooks/gate.py" in all_files, (
            "被 gitignore 蓋住的框架檔沒有進列舉 —— 會裝出沒有閘門的 repo:%s"
            % all_files)

    def test_it_says_so_when_framework_files_were_hidden(self, install_mod,
                                                        tmp_path, monkeypatch):
        """**被 gitignore 蓋住的框架檔本身是個怪狀態,所以不只帶,還要出聲。**

        少了這句,下一個人不會知道他的 .gitignore 正在對抗安裝器。
        """
        import subprocess
        root = tmp_path / "src2"
        (root / ".claude" / "hooks").mkdir(parents=True)
        for c in ("init -q", "config user.email t@t", "config user.name t"):
            subprocess.run(["git"] + c.split(), cwd=str(root), capture_output=True)
        open(str(root / ".claude" / "hooks" / "gate.py"), "w").write("x = 1\n")
        open(str(root / ".gitignore"), "w").write(".claude/\n")
        subprocess.run(["git", "add", "-A"], cwd=str(root), capture_output=True)
        subprocess.run(["git", "commit", "-qm", "b"], cwd=str(root),
                       capture_output=True)
        monkeypatch.setattr(install_mod, "SRC_ROOT", str(root))
        assert hasattr(install_mod, "ignored_framework_files")
        assert ".claude/hooks/gate.py" in install_mod.ignored_framework_files()

    def test_mirrors_and_bytecode_are_not_dragged_in(self, install_mod, tmp_path,
                                                     monkeypatch):
        """**負控**:不是「所有 ignored 都帶」。

        鏡像(`.claude/skills/`)不在任何框架前綴底下,`in_scope` 為假;
        `__pycache__` 在 `.claude/hooks/` 底下但標 `skip`,標記表擋住。
        少了這條,「一律帶」也會讓上面兩條過 —— 而那會把鏡像與位元碼裝進新 repo。
        """
        import subprocess
        root = tmp_path / "src3"
        (root / ".claude" / "skills" / "tdd").mkdir(parents=True)
        (root / ".claude" / "hooks" / "__pycache__").mkdir(parents=True)
        for c in ("init -q", "config user.email t@t", "config user.name t"):
            subprocess.run(["git"] + c.split(), cwd=str(root), capture_output=True)
        open(str(root / ".claude" / "skills" / "tdd" / "SKILL.md"), "w").write("x\n")
        open(str(root / ".claude" / "hooks" / "__pycache__" / "g.pyc"), "w").write("x")
        open(str(root / ".gitignore"), "w").write(".claude/\n")
        subprocess.run(["git", "add", "-A"], cwd=str(root), capture_output=True)
        subprocess.run(["git", "commit", "-qm", "b"], cwd=str(root),
                       capture_output=True)
        monkeypatch.setattr(install_mod, "SRC_ROOT", str(root))
        hidden = install_mod.ignored_framework_files()
        assert not [p for p in hidden if "/skills/" in p], hidden
        assert not [p for p in hidden if "__pycache__" in p], hidden


class TestTheInstallerProducesAManifest:
    """標記表自己標 `ask`,所以**不會被 copy 桶帶過去** —— 安裝器必須產它。

    沒有的話,裝出來的 repo 一張標記表都沒有:`_table()` 回空 ->
    每個檔案都退化成預設 `copy`、`in_scope` 跟著失真。
    而那個狀態是**靜默**的:安裝成功、hook 裝好、大部分測試照樣綠,
    只有兩條會紅,而且紅得像是那兩條測試自己的問題。

    實測(淨室安裝 2026-08-13):`.agents/` 底下只有 legacy 清單、站別定義、
    skills —— 沒有 portable-manifest.txt。
    """

    def test_the_installer_can_generate_one(self, install_mod, tmp_path):
        assert hasattr(install_mod, "generate_manifest"), \
            "安裝器不會產標記表 —— 而它標 ask,不會被 copy 桶帶過去"
        install_mod.generate_manifest(str(tmp_path))
        assert (tmp_path / ".agents" / "portable-manifest.txt").exists()

    def test_the_generated_table_marks_itself_ask(self, install_mod, manifest_mod,
                                                  tmp_path):
        """db7205b 的語意要跟著裝過去,否則新 repo 的更新路徑會 blind-copy 它。"""
        install_mod.generate_manifest(str(tmp_path))
        table = manifest_mod.load_table(
            str(tmp_path / ".agents" / "portable-manifest.txt"))
        assert manifest_mod.mark_in(".agents/portable-manifest.txt", table) == "ask"

    def test_the_generated_table_covers_the_framework_tests(
            self, install_mod, manifest_mod, tmp_path):
        """新加的框架測試也要在表裡 —— 漏一個框架測試是**靜默**的。"""
        install_mod.generate_manifest(str(tmp_path))
        table = manifest_mod.load_table(
            str(tmp_path / ".agents" / "portable-manifest.txt"))
        for t in ("tests/test_scanner.py", "tests/test_sync.py",
                  "tests/test_edit_result.py", "tests/test_install.py"):
            assert manifest_mod.mark_in(t, table) == "copy", t

    def test_the_generated_table_leaves_room_for_the_new_repo(
            self, install_mod, tmp_path):
        """產到框架列為止,底下留給人補。

        分類是**決定**,不是安裝器推導得出來的事實:
        「這個測試屬於框架還是專案」沒有任何機器答得出來。
        """
        install_mod.generate_manifest(str(tmp_path))
        body = open(str(tmp_path / ".agents" / "portable-manifest.txt"),
                    encoding="utf-8").read()
        assert "本 repo 自己的檔案" in body, "產出的表沒有留下「這裡由人補」的界線"


class TestTheInstallerProducesThePortableAuthorityLayer:
    """票 58 D3 —— 執行 `F-065:1115`(標「未做,待裁決」的框架待辦)。

    ## 在此之前,裝出來的 repo 沒有 `.githooks/`

    `install_hook()` 只寫 `.git/hooks/pre-commit`,而**那個目錄依 git 設計
    不進版控** —— clone 拿不到它。於是 `bootstrap.sh` 宣稱的那條路
    (「hook 進版控,靠一行 config 指過去」)在裝出來的 repo 上**不存在**:
    那一步實際是「先手工造一個 hook,再跑一行 config」。

    > **本組測試守的是:那一步從此只剩「一行 config」。**

    ## ⚠ 本票不關掉 ADR 0007 那個缺口

    `ADR 0007:19-22` 已經寫著 `core.hooksPath` 只是把「複製一個檔案」換成
    「跑一行 config」,**沒有消除那一步**;`:33` 寫著三個偵測點都碰不到
    「clone 下來直接手動 commit 的人」。**本票對他零影響。**
    受益的是**會跑 `bootstrap.sh` 的人** —— 在他身上,`ADR 0007:20` 那句
    **第一次成為真的**。

    ## 甲的裁決是 C:產 + 不設 config + 續寫 `.git/hooks/`

    設 config 是**這台機器的 local 狀態**,不是 repo 的內容;install 設了它,
    「裝好了」在兩台機器上意思會不同。而續寫 `.git/hooks/` 讓
    `authoritative_layer()`(沒設 hooksPath 就查那裡)在安裝當下就判「已安裝」——
    不續寫的話,安裝的強制驗證會**假失敗**。
    """

    HOOK_REL = ".githooks/pre-commit"

    def _repo(self, tmp_path, name):
        import subprocess
        repo = tmp_path / name
        repo.mkdir()
        for c in ("init -q", "config user.email t@t", "config user.name t"):
            subprocess.run(["git"] + c.split(), cwd=str(repo), capture_output=True)
        return repo

    def test_it_produces_the_versioned_hook_and_bootstrap(self, install_mod,
                                                          tmp_path):
        """**核心紅燈。** 兩個檔都要產,少一個那條路就還是斷的。"""
        target = self._repo(tmp_path, "t1")
        assert hasattr(install_mod, "install_portable_layer"), (
            "安裝器不會產進版控的那一半 —— F-065:1115 的待辦仍未執行")
        install_mod.install_portable_layer(str(target))
        assert (target / ".githooks" / "pre-commit").exists(), \
            "沒產 .githooks/pre-commit —— clone 拿不到 hook,bootstrap 指向空目錄"
        assert (target / "bootstrap.sh").exists(), \
            "沒產 bootstrap.sh —— 下一個 clone 不知道要跑什麼"

    def test_both_hooks_are_byte_identical(self, install_mod, tmp_path):
        """兩支必須逐位元組相同。

        不同的話,走 `core.hooksPath` 與走 `.git/hooks/` 的判定會不一樣,
        而**哪一支會跑取決於一行本機 config** —— 那是票 27 的整件事。
        """
        target = self._repo(tmp_path, "t2")
        install_mod.install_hook(str(target))
        install_mod.install_portable_layer(str(target))
        a = open(str(target / ".git" / "hooks" / "pre-commit"),
                 encoding="utf-8").read()
        b = open(str(target / ".githooks" / "pre-commit"), encoding="utf-8").read()
        assert a == b, "兩支 hook 內容不同 —— 走哪條路徑判定會不一樣"

    def test_bootstrap_comes_from_the_source_file_not_a_second_copy(
            self, install_mod, tmp_path):
        """**單一來源。** `bootstrap.sh` 的內容要從來源檔讀,不得在 install.py
        裡再寫一份常數。

        兩份的話就是**同一個事實有兩個可寫的位置**
        (`legacy-no-redlight.txt:12` 的同一條規矩),而下一次改 bootstrap
        會漏掉其中一份 —— 漏掉的那一份正是出貨給下游的那一份。
        """
        target = self._repo(tmp_path, "t3")
        install_mod.install_portable_layer(str(target))
        produced = open(str(target / "bootstrap.sh"), encoding="utf-8").read()
        source = open(os.path.join(install_mod.SRC_ROOT, "bootstrap.sh"),
                      encoding="utf-8").read()
        assert produced == source, "產出的 bootstrap.sh 與來源不同 —— 有第二份在別處"

    def test_the_produced_bootstrap_carries_the_three_checks(self, install_mod,
                                                             tmp_path):
        """**超集斷言(票 58 的硬理由)。**

        D3 之後安裝器開始產 `bootstrap.sh`,而下游那份是手寫的;
        `bootstrap.sh` 標 `skip`,兩份**永遠不會自動對齊**。
        上游若少一道,下游將來重跑 install 就會被**降級** ——
        丟掉它自己那三道 fail-closed,而且完全無聲。
        """
        target = self._repo(tmp_path, "t4")
        install_mod.install_portable_layer(str(target))
        body = open(str(target / "bootstrap.sh"), encoding="utf-8").read()
        for needle, name in (('[ ! -f "$hook" ]', "缺 hook 檔"),
                             ('[ -z "$mode" ]', "不在 index"),
                             ('[ "$mode" != "100755" ]', "mode 不對")):
            assert needle in body, (
                "產出的 bootstrap.sh 少了「%s」那一道 —— 下游重跑 install 會被降級"
                % name)

    def test_the_versioned_hook_is_staged_executable(self, install_mod, tmp_path):
        """**D0 量到的那一格,在安裝器這一側。**

        `os.chmod` 不夠:Windows 沒有 POSIX 執行位元,而 `filemode=false` 時
        git 一律把新檔記成 `100644`,**不看檔案系統**。
        唯一的解是明確寫 index 的 mode。

        Linux 上 git 不執行沒有執行位元的 hook,**而且不出聲** ——
        所以這一格錯了,裝出來的 repo 在 CI 上是靜默沒有權威層的。
        """
        import subprocess
        target = self._repo(tmp_path, "t5")
        install_mod.install_portable_layer(str(target))
        subprocess.run(["git", "add", "-A"], cwd=str(target), capture_output=True)
        assert hasattr(install_mod, "stage_hook_executable"), \
            "安裝器沒有把 index mode 設成 100755 的那一步"
        install_mod.stage_hook_executable(str(target))
        p = subprocess.run(["git", "ls-files", "-s", "--", self.HOOK_REL],
                           cwd=str(target), capture_output=True)
        rec = p.stdout.decode("utf-8", "replace").strip()
        assert rec, "%s 不在 index 裡" % self.HOOK_REL
        assert rec.split()[0] == "100755", (
            "index mode 是 %s,不是 100755 —— Linux 上 git 不會執行它,且不出聲"
            % rec.split()[0])

    def test_the_installer_does_not_set_hookspath(self, install_mod, tmp_path):
        """**甲的裁決 C 的釘子。**

        `core.hooksPath` 是 local config,**不隨 clone 走**(ADR 0007:19)。
        install 設了它,等於把這台機器的狀態混進安裝產物,而下一個 clone
        拿不到 —— 「裝好了」在兩台機器上意思不同。那一行留給人跑 bootstrap。

        **這一條驗的是本組函式,不是整支 `main()`** —— 端到端由 CI 的
        淨室驗證(`verify_gates`,每次 CI 跑真安裝)守著。誠實寫出來,
        免得它被讀成「已證明 main() 不設 config」。
        """
        import subprocess
        target = self._repo(tmp_path, "t6")
        install_mod.install_portable_layer(str(target))
        subprocess.run(["git", "add", "-A"], cwd=str(target), capture_output=True)
        install_mod.stage_hook_executable(str(target))
        p = subprocess.run(["git", "config", "--local", "--get", "core.hooksPath"],
                           cwd=str(target), capture_output=True)
        assert p.stdout.decode("utf-8", "replace").strip() == "", (
            "安裝器設了 core.hooksPath —— 那是 local 狀態,不是安裝產物")

    def test_the_local_hook_is_still_written(self, install_mod, tmp_path):
        """**反控:C 不是 B。**

        只產 `.githooks/` 而停寫 `.git/hooks/`,又不設 config 的話,
        `authoritative_layer()` 會去查 `.git/hooks/pre-commit`(沒設 hooksPath
        就查那裡)—— 找不到 → `install.py:328` 的強制驗證 **raise SystemExit**,
        安裝當場失敗。兩支並存才是票 27 裁過的正解。
        """
        target = self._repo(tmp_path, "t7")
        install_mod.install_hook(str(target))
        install_mod.install_portable_layer(str(target))
        assert (target / ".git" / "hooks" / "pre-commit").exists(), \
            "停寫 .git/hooks/pre-commit —— 沒設 hooksPath 時安裝驗證會假失敗"
