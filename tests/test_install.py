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
            "__pycache__/", ".cache/", "/.claude/skills/", "/skills/",
            ".venv-gates/")  # 票 156 G4:framework 清單含 .venv-gates/


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


def _lines(path):
    return [l.strip() for l in
            open(str(path), encoding="utf-8").read().splitlines() if l.strip()]


class TestGitignoreDedupIsLineExact:
    """票 78 —— 安裝器對 `.gitignore` 的查重必須是**行精確**,不是子字串。

    ## 病灶

    `install.py` 舊寫法是 `[p for p in GITIGNORE_FRAMEWORK if p not in have]`
    —— `have` 是**整檔內容的字串**。於是檔裡任何位置出現那串字元(例如一行
    註解「keep .env.example」)就當成「已經有了」,**真的防護行不補**。

    > **查重要問的是「這個 pattern 行存不存在」,
    > 而子字串答的是「這串字元出現過沒有」—— 問錯對象。**

    失效方向是 `F-062` 要防的那一邊:**裝出來的 repo 第一個放進去的秘密沒人守**,
    而且**完全靜默**。

    ## 三條反控,缺一不可

    | | 驗什麼 | 少了它會怎樣 |
    |---|---|---|
    | ① | 註解裡有那串字 → 真的防護行**仍被補上** | 這是病灶本身 |
    | ② | 已有真的那一行 → **不重複追加** | 一個「一律追加」的實作也會讓 ① 綠 |
    | ③ | 無 / 空 `.gitignore` → 兩組清單**全部**補上 | 一個「什麼都不補」的實作也會讓 ② 綠 |

    **三條互相封住對方的退化解** —— 這是本組存在的理由,不是湊數。
    """

    def _state(self, install_mod, tmp_path, initial=None):
        if initial is not None:
            open(str(tmp_path / ".gitignore"), "w", encoding="utf-8").write(initial)
        install_mod.generate_state(str(tmp_path))
        return tmp_path / ".gitignore"

    def test_a_comment_mentioning_the_pattern_does_not_suppress_the_real_line(
            self, install_mod, tmp_path):
        """① **病灶本身。** 註解提到那串字,不等於那條防護在。

        取 `.env` 當樣本的理由:它是本票與 `F-062` 逐字點名的那一個
        (「裝出來的 repo 第一個放進去的秘密」),而且它**不是憑證副檔名**
        —— 副檔名字面會被本 repo 自己的洩漏偵測擋下(票 73 / 票 78 的先例)。
        """
        ignore = self._state(install_mod, tmp_path,
                             "# keep .env.example around for docs\n")
        assert ".env" in _lines(ignore), (
            "註解裡出現 .env 字樣就不補真的 .env 行 —— 查重是子字串,不是行。\n"
            "  現況:%r" % _lines(ignore))

    def test_an_existing_real_line_is_not_appended_twice(
            self, install_mod, tmp_path):
        """② **反控:查重的本意不得丟。**

        少了這條,一個「一律追加」的實作也會讓 ① 綠 ——
        而重複的 ignore 行雖然無害,卻會讓下一次有人讀這個檔時
        以為安裝器壞了,然後去「修」一個沒有壞的東西。
        """
        ignore = self._state(install_mod, tmp_path, ".env\n")
        assert _lines(ignore).count(".env") == 1, (
            ".env 被追加了第二次:%r" % _lines(ignore))

    @pytest.mark.parametrize("initial", [None, ""])
    def test_an_absent_or_empty_gitignore_gets_both_lists_in_full(
            self, install_mod, tmp_path, initial):
        """③ **反控:兩組清單【全部】補上,不是補一部分。**

        少了這條,一個「什麼都不補」的實作也會讓 ② 綠。

        **枚舉,不抽查** —— 兩組清單是**封閉且可窮舉**的集合
        (`CLAUDE.md` 常駐檢查項:封閉集合用枚舉,比對的漏是未知的,
        枚舉的漏是不存在的)。
        """
        ignore = self._state(install_mod, tmp_path, initial)
        got = _lines(ignore)
        want = list(install_mod.GITIGNORE_FRAMEWORK) + list(install_mod.GITIGNORE_SECRETS)
        missing = [p for p in want if p not in got]
        assert not missing, "空 / 無 .gitignore 的新 repo 少了 %d 條:%r" % (
            len(missing), missing)

    def test_every_entry_of_both_lists_survives_the_comment_case(
            self, install_mod, tmp_path):
        """①的枚舉版:**每一條**都要在,不只 `.env`。

        註解只提到 `.env`,但子字串查重會讓**任何**「碰巧是註解子字串」的
        條目一起消失。逐條驗,免得下一次有人在範本 `.gitignore` 裡
        寫了一行提到別條的註解,而我們只守住了 `.env` 那一條。
        """
        ignore = self._state(install_mod, tmp_path,
                             "# keep .env.example around\n"
                             "# 產生物:__pycache__/ 之類的東西不要進版控\n")
        got = _lines(ignore)
        want = list(install_mod.GITIGNORE_FRAMEWORK) + list(install_mod.GITIGNORE_SECRETS)
        missing = [p for p in want if p not in got]
        assert not missing, "註解吃掉了 %d 條真防護行:%r" % (len(missing), missing)


# ─────────────────────────────────────────────────────────────────────────────
# 票 145 Station 3g-1b 紅燈 —— 安裝範本(〈四十八〉48.1 第 6 點;〈五十〉50.1)
#
# 合約:安裝器只在**非 canonical** 路徑 `.agents/evidence-policy.template.json` 寫範本(內容 = 框架能力邊界常數),
# 並在 `docs/decisions-pending.md` 加 evidence policy 初始化的待決項;canonical `.agents/evidence-policy.json`
# **只有人**放上去並 commit 才存在。
# 下文 `<BASELINE>` = 7a15ea081da1bf23cc79e04aef76065438f65219(S3G2)。
#
# **呼叫真的 `install.main()`**,在 tmp 目錄裝一個新 repo(module 範圍只裝一次,三支共用)。
# `install.main()` 會往 `sys.path` 插入目標 repo 的 hooks 目錄、從 `sys.modules` 移除 `gate`
# (`.claude/portable/install.py:364-366`)—— fixture 先存再還原,不讓它漏到其他測試。
# **不斷言範本「已提交」或「未提交」**(〈五十〉50.1 第 2 點:那不是本票裁決的需求)。
# 本段 helper 全部新寫;既有 helper(`_load`)只呼叫、不修改。
# ─────────────────────────────────────────────────────────────────────────────

_G_POLICY_FILE = ".agents/evidence-policy.json"
_G_TEMPLATE_FILE = ".agents/evidence-policy.template.json"
_G_TEST_X = ("tests/test_x.py::test_a", "tests/test_x.py::test_b")


@pytest.fixture(scope="module")
def g3_installed_repo(tmp_path_factory):
    """`install.main(<tmp>/repo)` 裝好的新 repo(真安裝)。產出 repo 路徑(pathlib.Path)。

    票 146 3g(G-1 / H-6 隔離契約第 3 點):USERPROFILE 與 HOME 在 `install.main` **之前**指到 tmp 家目錄
    (含空的 `.claude`),並涵蓋整個 module 的使用期 —— 後續 node 仍會呼叫安裝目標的 gate。
    真實使用者層因此不被讀寫。"""
    import sys
    target = tmp_path_factory.mktemp("g3-install") / "repo"
    home = tmp_path_factory.mktemp("g3-home")
    (home / ".claude").mkdir()
    mp = pytest.MonkeyPatch()
    try:
        mp.setenv("USERPROFILE", str(home))
        mp.setenv("HOME", str(home))
        mp.setattr(sys, "path", list(sys.path))
        if "gate" in sys.modules:
            mp.setitem(sys.modules, "gate", sys.modules["gate"])
        mod = _load("install_for_g3_template", "install.py")
        _g3_bootstrap_like_setup(target)
        # 票 156 D-6:事前檢查換成一律通過的替身。system-site venv 一定帶到額外套件,
        # 完整身分檢查不可能過 —— 「寫入前就失敗」只由 RT9 / RT10 驗。
        # `raising=False`:本站(實作前)install 還沒有 `_run_target_identity`。
        mp.setattr(mod, "_run_target_identity", lambda *a, **k: (True, "g3 stub"), raising=False)
        mod.main(str(target))
        yield target
    finally:
        mp.undo()


def _g3_bootstrap_like_setup(target):
    """票 156 D-6 (A):照 G4 新下游流程,在 install 之前先備好 target ——
    `git init`、`.git/info/exclude` 登記 `.venv-gates/`、建一個**真的** venv
    (`system_site_packages=True, with_pip=False`,離線)。

    exclude 要先登記:target 的 `.gitignore` 由 install 產生,而 install 的
    `git add -A` 在那之前就會跑;不先排除的話,整個 venv 會被收進安裝提交。
    提交身分沿用 install 自己的設定值(`install.py:629-630`)——
    target 已有 `.git` 時 install 不再設它。
    """
    import subprocess
    import venv
    target.mkdir(parents=True, exist_ok=True)
    for args in (["init", "-q"], ["config", "user.email", "gate@local"], ["config", "user.name", "gate"]):
        subprocess.run(["git"] + args, cwd=str(target), capture_output=True, check=True)
    exclude = target / ".git" / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    with open(str(exclude), "a", encoding="utf-8", newline="\n") as f:
        f.write(".venv-gates/\n")
    venv.EnvBuilder(system_site_packages=True, with_pip=False).create(str(target / ".venv-gates"))


def _g_load_from(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class _GInstallItem(pytest.Item):
    """真的 `pytest.Item` 子類;只帶 nodeid(producer 以 isinstance 判斷)。"""

    def runtest(self):
        pass


def _g_install_item(nodeid):
    it = object.__new__(_GInstallItem)
    it._nodeid = nodeid
    it.name = nodeid.split("::")[-1]
    return it


class _GSys(object):
    """conftest 所見的 `sys` 替身:版本固定為 3.11、`flags.optimize` 為 0,其他屬性轉給真的 `sys`。"""

    def __init__(self):
        import sys as real
        import types
        self._real = real
        self.version_info = (3, 11, 0, "final", 0)
        self.flags = types.SimpleNamespace(optimize=0)

    def __getattr__(self, name):
        return getattr(self._real, name)


class _GPluginManager(object):
    def __init__(self, name_plugins):
        self._name_plugins = list(name_plugins)

    def list_name_plugin(self):
        return list(self._name_plugins)

    def list_plugin_distinfo(self):
        return []

    def is_blocked(self, name):
        return False

    def get_plugin(self, name):
        return dict(self._name_plugins).get(name)

    def has_plugin(self, name):
        return self.get_plugin(name) is not None


def _g_drive_fixed_command(c, root):
    """依 pytest 9.1.1 的呼叫順序驅動**安裝出來的** `tests/conftest.py`,模擬一次固定全套
    `python -X utf8 -m pytest -q`:tests/test_x.py 的兩個身分全收集、全 passed、exit 0;
    選項全部關閉、`override_ini == ["strict_markers=true"]`、`inipath` 為 `pyproject.toml`;
    plugin 只有 `_pytest` 內建與 root conftest。"""
    import types
    files = {"tests/test_x.py": list(_G_TEST_X)}
    for path, ids in sorted(files.items()):
        report = types.SimpleNamespace(nodeid=path, result=[_g_install_item(n) for n in ids],
                                       failed=False, passed=True, skipped=False, outcome="passed")
        collector = types.SimpleNamespace(nodeid=path, path=root / path)
        gen = c.pytest_make_collect_report(collector)
        next(gen)
        try:
            gen.send(report)
        except StopIteration:
            pass
        c.pytest_collectreport(report)
    option_values = {"lf": False, "last_failed_no_failures": "all", "stepwise": False, "stepwise_skip": False,
                     "maxfail": None, "collectonly": False, "setuponly": False, "setupplan": False,
                     "runxfail": False, "pythonwarnings": None, "trace": False, "usepdb": False,
                     "override_ini": ["strict_markers=true"], "inifilename": None, "pyargs": False}
    option = types.SimpleNamespace(**option_values)
    pm = _GPluginManager([("main", types.ModuleType("_pytest.main")),
                          (os.path.join(str(root), "tests", "conftest.py"), c)])
    config = types.SimpleNamespace(
        args=["tests"], args_source=pytest.Config.ArgsSource.TESTPATHS, rootpath=root,
        invocation_params=types.SimpleNamespace(args=("-q",), plugins=None, dir=root),
        option=option, pluginmanager=pm, inipath=root / "pyproject.toml",
        getoption=lambda name, default=None, skip=False: getattr(option, name, default))
    selected = [n for ids in files.values() for n in ids]
    session = types.SimpleNamespace(items=[_g_install_item(n) for n in selected],
                                    testscollected=len(selected), config=config,
                                    shouldstop=False, shouldfail=False)
    c.pytest_collection_finish(session)
    for nodeid in selected:
        for when in ("setup", "call", "teardown"):
            c.pytest_runtest_logreport(types.SimpleNamespace(
                nodeid=nodeid, fspath=nodeid.split("::", 1)[0], when=when, outcome="passed",
                passed=True, failed=False, skipped=False))
    c.pytest_sessionfinish(session, 0)


class TestEvidencePolicyTemplate:

    def test_g3_install_writes_the_template_outside_the_canonical_path(self, g3_installed_repo, monkeypatch):
        """I1(〈五十〉50.1 第 3 點)。分類:behavior-red。

        `install.main(<tmp 新 repo>)` 之後:`.agents/evidence-policy.template.json` 存在;
        `.agents/evidence-policy.json`(canonical)**不存在**。
        再以安裝出來的**真實** producer(`tests/conftest.py`)與 consumer(`.claude/hooks/redlight.py`)驗證:
        在該 repo 提交一份 `pyproject.toml`(與 install.main 自己的 commit 同樣以 `--no-verify` 提交,
        `.claude/portable/install.py:520, :526`)後,模擬一次固定全套(版本事實固定為 3.11 / 9.1.1)——
        session 合格且為 A,但 `file_coverage` 不得為 `"true"`:範本位於非 canonical path,
        無論是否 tracked / committed,都不得成為 evidence authority。
        BASELINE 上失敗的原因:`<BASELINE>:.claude/portable/install.py:497-530` 不寫任何範本。
        """
        import subprocess
        root = g3_installed_repo
        assert (root / _G_TEMPLATE_FILE).is_file(), "安裝器沒有寫 %s" % _G_TEMPLATE_FILE
        assert not (root / _G_POLICY_FILE).exists(), "安裝器寫了 canonical policy —— 那等於自動信任"
        with open(str(root / "pyproject.toml"), "w", encoding="utf-8", newline="\n") as f:
            f.write(u'[tool.pytest.ini_options]\ntestpaths = ["tests"]\naddopts = "-ra --strict-markers"\n')
        for args in (["add", "pyproject.toml"], ["commit", "-q", "--no-verify", "-m", "g3 pyproject"]):
            subprocess.run(["git"] + args, cwd=str(root), capture_output=True, check=True)
        c = _g_load_from(root / "tests" / "conftest.py", "conftest_in_installed_repo_g3")
        assert c._redlight is not None, "安裝出來的 conftest 載不到 redlight"
        monkeypatch.setattr(c, "sys", _GSys(), raising=False)
        monkeypatch.setattr(pytest, "__version__", "9.1.1")
        _g_drive_fixed_command(c, c._ROOT)
        rl = _g_load_from(root / ".claude" / "hooks" / "redlight.py", "redlight_in_installed_repo_g3")
        runs = rl.load_runs(str(c._ROOT))
        assert runs, runs
        run = runs[-1]
        assert rl.validate_session(run) == [], run
        assert rl.run_state(run) == "A", run
        got = rl.file_coverage(run, "tests/test_x.py")
        assert got != "true", got

    def test_g3_the_template_lists_exactly_the_capability_boundary(self, g3_installed_repo):
        """I2(〈五十〉50.1 第 3 點)。分類:behavior-red。

        範本為 schema `"monkeyleash.evidence-policy"` v1;`python_versions` / `pytest_versions` / `dists`
        分別等於安裝出來的 redlight 的框架能力邊界常數(`KNOWN_PYTHON_VERSIONS` / `KNOWN_PYTEST_VERSIONS` /
        `KNOWN_DISTS`);`config_file` 屬 `FRAMEWORK_CONFIG_FILES`。常數以 getattr 取得,取不到 ⇒ 失敗。
        BASELINE 上失敗的原因:沒有範本檔(`<BASELINE>:.claude/portable/install.py:497-530`)。
        """
        import json
        root = g3_installed_repo
        path = root / _G_TEMPLATE_FILE
        assert path.is_file(), "安裝器沒有寫 %s" % _G_TEMPLATE_FILE
        template = json.loads(path.read_text(encoding="utf-8"))
        rl = _g_load_from(root / ".claude" / "hooks" / "redlight.py", "redlight_for_template_g3")
        assert template.get("schema") == "monkeyleash.evidence-policy" and template.get("version") == 1, template
        assert template.get("python_versions") == list(getattr(rl, "KNOWN_PYTHON_VERSIONS")), template
        assert template.get("pytest_versions") == list(getattr(rl, "KNOWN_PYTEST_VERSIONS")), template
        assert template.get("dists") == [list(d) for d in getattr(rl, "KNOWN_DISTS")], template
        assert template.get("config_file") in getattr(rl, "FRAMEWORK_CONFIG_FILES"), template

    def test_g3_decisions_pending_asks_to_initialize_the_policy(self, g3_installed_repo):
        """I3(〈五十〉50.1 第 3 點)。分類:behavior-red。

        `docs/decisions-pending.md` 含 evidence policy 初始化的待決項,且點名 canonical 路徑
        `.agents/evidence-policy.json`。
        BASELINE 上失敗的原因:`<BASELINE>:.claude/portable/install.py:386-422` 的待決項沒有 evidence policy。
        """
        path = g3_installed_repo / "docs" / "decisions-pending.md"
        assert path.is_file(), "安裝器沒有寫 docs/decisions-pending.md"
        body = path.read_text(encoding="utf-8")
        assert "evidence policy" in body.lower(), body
        assert _G_POLICY_FILE in body, body


# ─────────────────────────────────────────────────────────────────────────────
# 票 146 第三站 3g 紅燈(S3g-146-1)—— 安裝器最小 policy(G-2)、R10 演習(G-3)、policy-only 通道(H-6)
#
# 契約在票 146〈3g 契約與紅燈〉。全部經 `g3_installed_repo`(USERPROFILE / HOME 已指到 tmp 家目錄);
# 會改目標狀態的 node 進入時記 SHA,finally `git reset --hard` 回去並清掉自己放的檔。
# 寫入家目錄前一律先確認它是隔離出來的 tmp(`_t146_isolated_claude_root`),否則拒絕。
# ─────────────────────────────────────────────────────────────────────────────

_T146_ALLOW = ".agents/extension-allowlist.json"
_T146_INV = ".agents/extension-inventory.json"
# 票 156 S3b:改成新指令(啟動器)。T146-56 / T146-58(a-none) 因此轉紅 ——
# 它們拿的是**上游** `.claude/settings.json` 的 hook 指令,實作站改了 settings.json 才轉綠。
_T146_HOOK = 'sh "$CLAUDE_PROJECT_DIR/.claude/bin/gatepy" "$CLAUDE_PROJECT_DIR/.claude/hooks/gate.py"'
_T146_ALLOW_KEYS = {"schema", "version", "dev_mod_files", "user_skill_plugins", "user_commands",
                    "project_settings_hook_commands", "mcp_json_servers"}
_T146_TRIGGER = "docs/adr/verify-trigger.md"


def _t146_git(root, *args, **kw):
    import subprocess
    return subprocess.run(["git"] + list(args), cwd=str(root), capture_output=True, **kw)


def _t146_isolated_claude_root():
    """隔離出來的 `<home>/.claude`。家目錄不是 `g3_installed_repo` 的 tmp ⇒ 拒絕(不碰真實使用者層)。"""
    import pathlib
    home = os.path.expanduser("~")
    assert os.environ.get("USERPROFILE") == home and os.environ.get("HOME") == home, \
        "USERPROFILE / HOME / expanduser 不一致 —— 拒絕寫入家目錄"
    assert os.path.basename(home).startswith("g3-home"), "家目錄沒有隔離 —— 拒絕碰真實使用者層"
    return pathlib.Path(home) / ".claude"


def _t146_hook_commands(settings_path):
    """settings.json 的 hooks 內全部 command 字串(出現順序、去重)。"""
    import json
    with open(str(settings_path), encoding="utf-8") as f:
        doc = json.load(f)
    out = []

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "command" and isinstance(v, str):
                    if v not in out:
                        out.append(v)
                else:
                    walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(doc.get("hooks"))
    return out


def _t146_set_stage(root, stage):
    import json
    with open(str(root / ".dev" / "pipeline.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({"current_stage": stage, "feature": "t146", "ticket_id": None, "updated": ""},
                           ensure_ascii=False, indent=2) + "\n")


def _t146_write_trigger(root):
    p = root / _T146_TRIGGER
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes("觸發一次 commit 用(t146)\n".encode("utf-8"))
    return p


def _t146_pre_commit(root):
    """票 156 S4e-2(D-S4-1):用 target 自己的 `.venv-gates` 直譯器跑 gate —— gate-B 只認它。
    venv 由 `_g3_bootstrap_like_setup` 建好(真的 venv);候選順序照 gatepy。不繞過、不替換身分檢查。"""
    import subprocess
    cands = [root / ".venv-gates" / "Scripts" / "python.exe", root / ".venv-gates" / "bin" / "python"]
    py = next((c for c in cands if c.is_file()), None)
    assert py is not None, "target 沒有 .venv-gates 直譯器:%s" % cands
    p = subprocess.run([str(py), os.path.join(".claude", "hooks", "gate.py"), "--pre-commit"],
                       cwd=str(root), capture_output=True)
    return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")


def _t146_plant_bucket(claude_root):
    """在隔離 claude_root/skills/synced 放合法 bucket + marker 兩筆;回 {邏輯路徑: sha256}。"""
    import hashlib
    base = claude_root / "skills" / "synced"
    (base / "vgbucket").mkdir(parents=True)
    skill = b"# verify_gates r10\n"
    marker = b"vgbucket\n"
    (base / "vgbucket" / "SKILL.md").write_bytes(skill)
    (base / ".bucket-vgbucket").write_bytes(marker)
    return {"skills/<bucket>/SKILL.md": hashlib.sha256(skill).hexdigest(),
            "skills/.bucket-<bucket>": hashlib.sha256(marker).hexdigest()}


def _t146_unplant(claude_root):
    import shutil
    if (claude_root / "skills").exists():
        shutil.rmtree(str(claude_root / "skills"))


def _t146_dump(doc):
    import json
    return (json.dumps(doc, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


class TestTicket146InstallPolicy:
    """票 146 3g:安裝器寫最小 policy 並隨第一個安裝 commit 進 HEAD;R10 演習;policy-only 通道。"""

    def test_t146_56_install_commits_minimal_policy(self, g3_installed_repo):
        """T146-56(behavior-red):兩份 canonical policy 存在、tracked、HEAD blob == 工作樹;inventory 為合法空;
        allowlist 七鍵、四個 list 欄位為 []、hook 清單 == 目標 settings.json 的 command;無 BOM、無 CR、單一 LF。
        BASELINE 紅因:安裝器不寫這兩份檔(`install.write_extension_policy` 不存在)。"""
        import json
        root = g3_installed_repo
        for rel in (_T146_ALLOW, _T146_INV):
            assert (root / rel).is_file(), "安裝器沒有寫 %s" % rel
        tracked = _t146_git(root, "ls-files", check=True).stdout.decode("utf-8").split("\n")
        for rel in (_T146_ALLOW, _T146_INV):
            assert rel in tracked, (rel, "沒有進 HEAD")
            head = _t146_git(root, "rev-parse", "HEAD:" + rel, check=True).stdout.decode().strip()
            wt = _t146_git(root, "hash-object", rel, check=True).stdout.decode().strip()
            assert head == wt, (rel, head, wt)
            raw = (root / rel).read_bytes()
            assert not raw.startswith(b"\xef\xbb\xbf") and b"\r" not in raw, rel
            assert raw.endswith(b"\n") and not raw.endswith(b"\n\n"), rel
        inv = json.loads((root / _T146_INV).read_text(encoding="utf-8"))
        assert inv == {"schema": "monkeyleash.extension-inventory", "version": 1, "entries": []}, inv
        allow = json.loads((root / _T146_ALLOW).read_text(encoding="utf-8"))
        assert set(allow) == _T146_ALLOW_KEYS, sorted(allow)
        assert allow["schema"] == "monkeyleash.extension-allowlist" and allow["version"] == 1, allow
        for k in ("dev_mod_files", "user_skill_plugins", "user_commands", "mcp_json_servers"):
            assert allow[k] == [], (k, allow[k])
        hooks = _t146_hook_commands(root / ".claude" / "settings.json")
        assert allow["project_settings_hook_commands"] == hooks == [_T146_HOOK], (allow, hooks)

    def test_t146_57_decisions_pending_names_installer_policy(self, g3_installed_repo):
        """T146-57(behavior-red):decisions-pending 點名兩個 policy 路徑並寫「未登記任何使用者擴充」。
        BASELINE 紅因:待決項沒有這一段。"""
        body = (g3_installed_repo / "docs" / "decisions-pending.md").read_text(encoding="utf-8")
        assert _T146_ALLOW in body and _T146_INV in body, body
        assert u"未登記任何使用者擴充" in body, body

    @pytest.mark.parametrize("case", ["a-none", "b-valid-both", "c-only-allowlist", "d-allowlist-schema",
                                      "e-inventory-entry-invalid"])
    def test_t146_58_write_extension_policy_keeps_valid_refuses_partial_or_invalid(self, install_mod, tmp_path, case):
        """T146-58(behavior-red):都不存在 ⇒ 產生;兩份合法 ⇒ 保留不覆寫;只有一份 / 任一不合法 ⇒ SystemExit、不寫任何檔。
        BASELINE 紅因:`install.write_extension_policy` 不存在(AttributeError)。"""
        import json
        import shutil
        fn = getattr(install_mod, "write_extension_policy")
        target = tmp_path / "target"
        (target / ".claude" / "hooks").mkdir(parents=True)
        (target / ".agents").mkdir()
        src_root = os.path.join(HERE, "..")
        shutil.copy2(os.path.join(src_root, ".claude", "hooks", "redlight.py"),
                     str(target / ".claude" / "hooks" / "redlight.py"))
        shutil.copy2(os.path.join(src_root, ".claude", "settings.json"), str(target / ".claude" / "settings.json"))
        allow_p, inv_p = target / _T146_ALLOW, target / _T146_INV
        good_allow = {"schema": "monkeyleash.extension-allowlist", "version": 1, "dev_mod_files": [],
                      "user_skill_plugins": [], "user_commands": [],
                      "project_settings_hook_commands": [_T146_HOOK], "mcp_json_servers": []}
        good_inv = {"schema": "monkeyleash.extension-inventory", "version": 1,
                    "entries": [{"path": "skills/<bucket>/SKILL.md", "sha256": "a" * 64, "note": "t146"}]}
        if case == "a-none":
            res = fn(str(target))
            assert res[2] is True, res
            assert json.loads(inv_p.read_text(encoding="utf-8")) == \
                {"schema": "monkeyleash.extension-inventory", "version": 1, "entries": []}
            allow = json.loads(allow_p.read_text(encoding="utf-8"))
            assert set(allow) == _T146_ALLOW_KEYS and allow["project_settings_hook_commands"] == [_T146_HOOK], allow
            for p in (allow_p, inv_p):
                raw = p.read_bytes()
                assert b"\r" not in raw and raw.endswith(b"\n") and not raw.endswith(b"\n\n"), p
            return
        if case == "b-valid-both":
            allow_p.write_bytes(_t146_dump(good_allow))
            inv_p.write_bytes(_t146_dump(good_inv))
            before = (allow_p.read_bytes(), inv_p.read_bytes())
            res = fn(str(target))
            assert res[2] is False, res
            assert (allow_p.read_bytes(), inv_p.read_bytes()) == before
            return
        if case == "c-only-allowlist":
            allow_p.write_bytes(_t146_dump(good_allow))
        elif case == "d-allowlist-schema":
            bad = dict(good_allow, schema="wrong.schema")
            allow_p.write_bytes(_t146_dump(bad))
            inv_p.write_bytes(_t146_dump(good_inv))
        else:
            bad_inv = dict(good_inv, entries=[{"path": "skills/x", "sha256": "a" * 64, "note": "t146"}])
            allow_p.write_bytes(_t146_dump(good_allow))
            inv_p.write_bytes(_t146_dump(bad_inv))
        before = {p: p.read_bytes() for p in (allow_p, inv_p) if p.exists()}
        with pytest.raises(SystemExit):
            fn(str(target))
        after = {p: p.read_bytes() for p in (allow_p, inv_p) if p.exists()}
        assert after == before, case

    def test_t146_59_installed_repo_precommit_passes_under_empty_isolated_home(self, g3_installed_repo):
        """T146-59(正控;BASELINE **綠**):隔離家目錄為空時,安裝出來的 repo 的 pre-commit 放行,且不含 "[R10"。"""
        root = g3_installed_repo
        claude_root = _t146_isolated_claude_root()
        assert not any(claude_root.iterdir()), "隔離 claude_root 不是空的"
        sha = _t146_git(root, "rev-parse", "HEAD", check=True).stdout.decode().strip()
        trigger = None
        try:
            _t146_set_stage(root, "implement")
            trigger = _t146_write_trigger(root)
            _t146_git(root, "add", _T146_TRIGGER, check=True)
            rc, out = _t146_pre_commit(root)
            assert rc == 0, out
            assert "[R10" not in out, out
        finally:
            _t146_git(root, "reset", "-q", "--hard", sha)
            if trigger is not None and trigger.exists():
                trigger.unlink()

    def test_t146_60_installed_repo_blocks_unregistered_synced_bucket(self, g3_installed_repo):
        """T146-60(behavior-red):隔離 claude_root 放 bucket + marker 兩筆 ⇒ rc 1、"[R10/fail-closed]"、
        「未受管入口：synced（額外 2」。BASELINE 紅因:R10 未接線,pre-commit 放行(rc 0)。"""
        root = g3_installed_repo
        claude_root = _t146_isolated_claude_root()
        sha = _t146_git(root, "rev-parse", "HEAD", check=True).stdout.decode().strip()
        trigger = None
        try:
            _t146_plant_bucket(claude_root)
            _t146_set_stage(root, "implement")
            trigger = _t146_write_trigger(root)
            _t146_git(root, "add", _T146_TRIGGER, check=True)
            rc, out = _t146_pre_commit(root)
            assert rc == 1, out
            assert "[R10/fail-closed]" in out and u"未受管入口：synced（額外 2" in out, out
        finally:
            _t146_unplant(claude_root)
            _t146_git(root, "reset", "-q", "--hard", sha)
            if trigger is not None and trigger.exists():
                trigger.unlink()

    def test_t146_60b_policy_only_approval_then_normal_commit_passes(self, g3_installed_repo):
        """T146-60b(behavior-red):獨立佈置兩筆;inventory 寫成那兩筆、**只** stage inventory(trigger 不存在)
        ⇒ pre-commit rc 0 且含 "policy_source=index";走 hook 提交;再 stage trigger ⇒ rc 0、不含 "policy_source=index"。
        BASELINE 紅因:沒有 policy-only 通道,輸出不含 "policy_source=index"。"""
        root = g3_installed_repo
        claude_root = _t146_isolated_claude_root()
        sha = _t146_git(root, "rev-parse", "HEAD", check=True).stdout.decode().strip()
        trigger = root / _T146_TRIGGER
        try:
            planted = _t146_plant_bucket(claude_root)
            _t146_set_stage(root, "implement")
            inv = {"schema": "monkeyleash.extension-inventory", "version": 1,
                   "entries": [{"path": p, "sha256": s, "note": "t146-60b"} for p, s in sorted(planted.items())]}
            inv_path = root / _T146_INV
            inv_path.parent.mkdir(parents=True, exist_ok=True)
            inv_path.write_bytes(_t146_dump(inv))
            _t146_git(root, "add", _T146_INV, check=True)
            staged = [n for n in _t146_git(root, "diff", "--cached", "--name-only", check=True)
                      .stdout.decode("utf-8").split("\n") if n]
            assert staged == [_T146_INV], staged
            assert not trigger.exists(), "trigger 此時不得存在"
            rc, out = _t146_pre_commit(root)
            assert rc == 0, out
            assert "policy_source=index" in out, out
            _t146_git(root, "commit", "-q", "-m", "approve extension inventory (t146-60b)", check=True)
            _t146_write_trigger(root)
            _t146_git(root, "add", _T146_TRIGGER, check=True)
            rc, out = _t146_pre_commit(root)
            assert rc == 0, out
            assert "policy_source=index" not in out, out
        finally:
            _t146_unplant(claude_root)
            _t146_git(root, "reset", "-q", "--hard", sha)
            if trigger.exists():
                trigger.unlink()


# ─────────────────────────────────────────────────────────────────────────────
# 票 156 S3b 紅燈 —— 閘門執行環境的 Python 隔離(RT2 / RT6 / RT8 / RT9 / RT10)
#
# 本段釘住的 install 介面(S3b 定;實作站照此實作):
#   install.HOOK                 = hook-v2-gatepy(LF)
#   install.KNOWN_HOOKS          = {版本 ID: sha256(LF 標準形)}
#   install.GITIGNORE_FRAMEWORK  含 `.venv-gates/`
#   install.verify(target)       以 `<target>/.venv-gates` 的直譯器執行 gate(D-10;不經 sh / gatepy)
#   install._run_target_identity(target)  事前檢查唯一的子行程入口(D-10 / F0c (b))
#   install.rehook(target) -> "updated" | "no-op";拒絕 ⇒ SystemExit
#   install._replace_hook(path, data)     `--rehook` 替換單一檔案的唯一入口(RT8(i) 注入點)
#   CLI:install.py --rehook <target>
#
# 測試不碰真實 repo、不連網。會跑 `install.main` 的一律先把 USERPROFILE / HOME
# 指到 tmp 家目錄(同 `g3_installed_repo`),不讀寫真實使用者層。
# ─────────────────────────────────────────────────────────────────────────────

import hashlib as _t156_hashlib
import stat as _t156_stat
import subprocess as _t156_subprocess
import sys as _t156_sys

_T156_FIXTURES = os.path.join(HERE, "fixtures", "hooks")
_T156_V1 = open(os.path.join(_T156_FIXTURES, "hook-v1-bare-python.sh"), "rb").read()
_T156_V2 = open(os.path.join(_T156_FIXTURES, "hook-v2-gatepy.sh"), "rb").read()
# S3b 以 `sha256sum` 量得(LF 標準形,UTF-8,無 BOM)。
_T156_KNOWN = {
    "hook-v1-bare-python": "eb6ee62cfb31803c26c3547822ba76b8104d111f759a960774d425a6b1f1c807",
    "hook-v2-gatepy": "091c0290f0e9c43441678f3c33391a31d8260c84764c9c86270e688fa1ccd83d",
}
_T156_T = 1000000000 * 10 ** 9      # 固定的過去 mtime(ns)—— 用來看「有沒有被碰過」


class _T156Stop(Exception):
    pass


def _t156_heads(text):
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


def _t156_venv_pythons(target):
    return {os.path.normcase(os.path.abspath(os.path.join(str(target), ".venv-gates", "Scripts", "python.exe"))),
            os.path.normcase(os.path.abspath(os.path.join(str(target), ".venv-gates", "bin", "python")))}


def _t156_fake_venv(target):
    for rel in (("Scripts", "python.exe"), ("bin", "python")):
        p = os.path.join(str(target), ".venv-gates", *rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "wb").close()


def _t156_snapshot(root):
    """target 底下**全部**檔案(含 `.git/`)的 (相對路徑 -> (mode, sha256))。"""
    snap = {}
    for dp, _dn, fns in os.walk(str(root)):
        for fn in fns:
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, str(root)).replace("\\", "/")
            with open(p, "rb") as f:
                data = f.read()
            snap[rel] = (_t156_stat.S_IMODE(os.stat(p).st_mode), _t156_hashlib.sha256(data).hexdigest())
    return snap


def _t156_git(root, *args):
    return _t156_subprocess.run(["git"] + list(args), cwd=str(root), capture_output=True, check=True)


def _t156_isolated_home(tmp_path, monkeypatch):
    home = tmp_path / "t156-home"
    (home / ".claude").mkdir(parents=True)
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(_t156_sys, "path", list(_t156_sys.path))
    if "gate" in _t156_sys.modules:
        monkeypatch.setitem(_t156_sys.modules, "gate", _t156_sys.modules["gate"])


def _t156_clean_git_target(tmp_path, name="target"):
    t = tmp_path / name
    t.mkdir()
    _t156_git(t, "init", "-q")
    _t156_git(t, "config", "user.email", "t@t")
    _t156_git(t, "config", "user.name", "t")
    (t / "app.txt").write_text("app\n", encoding="utf-8")
    _t156_git(t, "add", "app.txt")
    _t156_git(t, "commit", "-q", "-m", "init")
    return t


class TestT156RT2ExecutableEntriesDoNotStartWithBarePython:
    """RT2(G3 / D-10):四個會實際執行的入口。允許清單不在這裡(G3:改由各站核對)。
    `.githooks/pre-commit` 那一格在 `tests/test_gatepy.py`(下游的那支是下游自己的)。"""

    def test_rt2_install_hook_has_no_bare_python_command(self, install_mod):
        heads = _t156_heads(install_mod.HOOK)
        assert not [h for h in heads if h in ("python", "python3", "py")], heads

    def test_rt2_settings_json_hook_has_no_bare_python_command(self):
        import json
        doc = json.load(open(os.path.join(HERE, "..", ".claude", "settings.json"), encoding="utf-8"))
        cmds = []

        def walk(n):
            if isinstance(n, dict):
                for k, v in n.items():
                    if k == "command" and isinstance(v, str):
                        cmds.append(v)
                    else:
                        walk(v)
            elif isinstance(n, list):
                for v in n:
                    walk(v)
        walk(doc.get("hooks"))
        assert cmds, "settings.json 沒有任何 hook 指令"
        assert not [c for c in cmds if c.split()[0] in ("python", "python3", "py")], cmds

    def test_rt2_verify_runs_gate_with_the_target_venv_interpreter(self, tmp_path, monkeypatch):
        """D-10:`verify()` 執行 gate 的直譯器是 `<target>/.venv-gates` 那一支 ——
        不是 `"python"`、不是 `sys.executable`、**不經 sh 或 gatepy**。"""
        mod = _load("install_t156_verify", "install.py")
        t = tmp_path / "t"
        t.mkdir()
        _t156_fake_venv(t)
        seen = []

        def fake_run(args, cwd, check=True):
            seen.append(list(args))
            raise _T156Stop()
        monkeypatch.setattr(mod, "run", fake_run)
        with pytest.raises(_T156Stop):
            mod.verify(str(t))
        argv = seen[0]
        exe = os.path.normcase(os.path.abspath(argv[0])) if os.path.dirname(argv[0]) else argv[0]
        assert exe in _t156_venv_pythons(t), argv
        assert argv[0] != _t156_sys.executable and argv[0] != "python", argv
        assert os.path.basename(argv[0]) not in ("sh", "sh.exe", "bash", "bash.exe"), argv
        assert not [a for a in argv if "gatepy" in str(a)], argv


class TestT156HookTemplates:

    def test_the_fixture_shas_match_the_recorded_table(self):
        """**綠燈對照**:fixture 與本檔記下的 sha256 一致(表與範本不漂移)。"""
        assert _t156_hashlib.sha256(_T156_V1).hexdigest() == _T156_KNOWN["hook-v1-bare-python"]
        assert _t156_hashlib.sha256(_T156_V2).hexdigest() == _T156_KNOWN["hook-v2-gatepy"]

    def test_install_registers_the_known_hook_table(self, install_mod):
        """第三節第 7 條第 6 點:「版本 ID → sha256」對照表登記在程式裡。"""
        assert getattr(install_mod, "KNOWN_HOOKS", None) == _T156_KNOWN, \
            getattr(install_mod, "KNOWN_HOOKS", None)

    def test_install_hook_is_v2(self, install_mod):
        assert install_mod.HOOK.encode("utf-8") == _T156_V2

    def test_the_generated_gitignore_ignores_venv_gates(self, install_mod):
        """G4 第 5 步:install 產生的 `.gitignore` 永久含 `.venv-gates/`。"""
        assert ".venv-gates/" in install_mod.GITIGNORE_FRAMEWORK, install_mod.GITIGNORE_FRAMEWORK


class TestT156RT6InstalledRepoUsesTheLauncher:
    """RT6:乾淨 target 裝完之後,兩支 pre-commit 都是 HOOK v2(經啟動器)。"""

    def test_rt6_git_hooks_pre_commit_is_v2(self, g3_installed_repo):
        assert (g3_installed_repo / ".git" / "hooks" / "pre-commit").read_bytes() == _T156_V2

    def test_rt6_githooks_pre_commit_is_v2(self, g3_installed_repo):
        assert (g3_installed_repo / ".githooks" / "pre-commit").read_bytes() == _T156_V2


# ── RT8:`--rehook` ──────────────────────────────────────────────────────────

def _t156_rehook_target(tmp_path, git_hook=_T156_V1, githooks=_T156_V1, venv=True, installed=True):
    """已安裝的下游(最小形):gate.py + 允許清單 + 帳本 + CLAUDE.md,`.githooks/pre-commit` 已提交。"""
    t = tmp_path / "rt"
    t.mkdir()
    _t156_git(t, "init", "-q")
    _t156_git(t, "config", "user.email", "t@t")
    _t156_git(t, "config", "user.name", "t")
    files = {"CLAUDE.md": b"# project\n", "app.txt": b"app\n",
             ".dev/pipeline.json": b'{"current_stage": "idle"}\n',
             ".dev/test-runs.jsonl": b'{"r": 1}\n', ".dev/gate-exemptions.jsonl": b'{"e": 1}\n'}
    if installed:
        files[".claude/hooks/gate.py"] = b"# gate\n"
        files[".agents/extension-allowlist.json"] = b"{}\n"
    for rel, data in files.items():
        p = t / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    if githooks is not None:
        (t / ".githooks").mkdir()
        (t / ".githooks" / "pre-commit").write_bytes(githooks)
    _t156_git(t, "add", "-A")
    _t156_git(t, "commit", "-q", "-m", "installed")
    if venv:
        _t156_fake_venv(t)
        with open(str(t / ".git" / "info" / "exclude"), "a", encoding="utf-8", newline="\n") as f:
            f.write(".venv-gates/\n")
    hooks = [t / ".git" / "hooks" / "pre-commit", t / ".githooks" / "pre-commit"]
    if git_hook is not None:
        hooks[0].parent.mkdir(parents=True, exist_ok=True)
        hooks[0].write_bytes(git_hook)
    for h in hooks:
        if h.exists():
            os.utime(str(h), ns=(_T156_T, _T156_T))
    return t


def _t156_hook_state(t):
    out = {}
    for rel in (".git/hooks/pre-commit", ".githooks/pre-commit"):
        p = t / rel
        if p.exists():
            st = os.stat(str(p))
            out[rel] = (p.read_bytes(), _t156_stat.S_IMODE(st.st_mode), st.st_mtime_ns)
        else:
            out[rel] = None
    return out


def _t156_rehook_mod():
    return _load("install_t156_rehook", "install.py")


class TestT156RT8Rehook:

    def _refused_and_unchanged(self, t):
        mod = _t156_rehook_mod()
        before = _t156_snapshot(t)
        with pytest.raises(SystemExit) as e:
            mod.rehook(str(t))
        assert e.value.code not in (0, None)
        assert _t156_snapshot(t) == before

    def test_rt8_a_no_venv_gates_is_refused(self, tmp_path):
        self._refused_and_unchanged(_t156_rehook_target(tmp_path, venv=False))

    def test_rt8_a_cli_rehook_mode_refuses_without_venv_gates(self, tmp_path):
        """`install.py --rehook <target>` 這個 CLI 模式存在,拒絕時說出缺的是 `.venv-gates`。"""
        t = _t156_rehook_target(tmp_path, venv=False)
        before = _t156_snapshot(t)
        p = _t156_subprocess.run([_t156_sys.executable, os.path.join(PORTABLE, "install.py"),
                                  "--rehook", str(t)], capture_output=True)
        out = (p.stdout + p.stderr).decode("utf-8", "replace")
        assert p.returncode != 0, out
        assert ".venv-gates" in out, out
        assert _t156_snapshot(t) == before

    def test_rt8_b_never_installed_is_refused(self, tmp_path):
        self._refused_and_unchanged(_t156_rehook_target(tmp_path, installed=False))

    def test_rt8_c_unknown_hook_content_is_refused(self, tmp_path):
        custom = b"#!/bin/sh\nnpm run lint\n"
        self._refused_and_unchanged(_t156_rehook_target(tmp_path, git_hook=custom, githooks=custom))

    def test_rt8_d_only_the_two_hooks_change(self, tmp_path):
        """(d):除了兩支 pre-commit,所有受追蹤檔、`.dev/`、允許清單、CLAUDE.md、`.git/` 其餘部分逐位元組不變;
        兩支都變成 v2(LF)。"""
        t = _t156_rehook_target(tmp_path)
        mod = _t156_rehook_mod()
        before = _t156_snapshot(t)
        assert mod.rehook(str(t)) == "updated"
        after = _t156_snapshot(t)
        changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
        assert changed == [".git/hooks/pre-commit", ".githooks/pre-commit"], changed
        assert (t / ".git" / "hooks" / "pre-commit").read_bytes() == _T156_V2
        assert (t / ".githooks" / "pre-commit").read_bytes() == _T156_V2

    def test_rt8_e_already_v2_is_a_no_op(self, tmp_path):
        t = _t156_rehook_target(tmp_path, git_hook=_T156_V2, githooks=_T156_V2)
        mod = _t156_rehook_mod()
        before, hooks = _t156_snapshot(t), _t156_hook_state(t)
        assert mod.rehook(str(t)) == "no-op"
        assert _t156_snapshot(t) == before
        assert _t156_hook_state(t) == hooks

    def test_rt8_f_no_commit_is_created(self, tmp_path):
        t = _t156_rehook_target(tmp_path)
        head = _t156_git(t, "rev-parse", "HEAD").stdout
        count = _t156_git(t, "rev-list", "--all", "--count").stdout
        _t156_rehook_mod().rehook(str(t))
        assert _t156_git(t, "rev-parse", "HEAD").stdout == head
        assert _t156_git(t, "rev-list", "--all", "--count").stdout == count

    def test_rt8_g_one_hook_missing_is_refused(self, tmp_path):
        """沒有 `.githooks/`(舊下游的形狀)⇒ fail-closed,另一支也不寫。"""
        self._refused_and_unchanged(_t156_rehook_target(tmp_path, githooks=None))

    def test_rt8_h_one_known_one_custom_is_refused(self, tmp_path):
        self._refused_and_unchanged(
            _t156_rehook_target(tmp_path, git_hook=_T156_V1, githooks=b"#!/bin/sh\necho custom\n"))

    def test_rt8_i_a_failed_second_replacement_rolls_back(self, tmp_path, monkeypatch):
        """(i):第二支替換失敗 ⇒ 第一支回滾;兩支的內容、mode、mtime 都回原狀。"""
        t = _t156_rehook_target(tmp_path)
        mod = _t156_rehook_mod()
        real = mod._replace_hook
        calls = []

        def flaky(path, data):
            calls.append(path)
            if len(calls) == 2:
                raise OSError("injected failure on the second replacement")
            return real(path, data)
        monkeypatch.setattr(mod, "_replace_hook", flaky)
        before, hooks = _t156_snapshot(t), _t156_hook_state(t)
        with pytest.raises((OSError, SystemExit)):
            mod.rehook(str(t))
        assert len(calls) == 2, calls
        assert _t156_hook_state(t) == hooks
        assert _t156_snapshot(t) == before

    @pytest.mark.parametrize("variant", ["crlf-v1-is-known", "trailing-space-is-unknown", "bom-is-unknown"])
    def test_rt8_j_only_crlf_is_normalised(self, tmp_path, variant):
        """(j)(G2):唯一允許的正規化是 CRLF→LF。行尾空白、BOM 一律「不認得」。"""
        if variant == "crlf-v1-is-known":
            crlf = _T156_V1.replace(b"\n", b"\r\n")
            t = _t156_rehook_target(tmp_path, git_hook=crlf, githooks=crlf)
            assert _t156_rehook_mod().rehook(str(t)) == "updated"
            assert (t / ".git" / "hooks" / "pre-commit").read_bytes() == _T156_V2
            assert (t / ".githooks" / "pre-commit").read_bytes() == _T156_V2
            return
        bad = (_T156_V1.replace(b"--pre-commit\n", b"--pre-commit \n")
               if variant == "trailing-space-is-unknown" else b"\xef\xbb\xbf" + _T156_V1)
        assert bad != _T156_V1
        self._refused_and_unchanged(_t156_rehook_target(tmp_path, git_hook=_T156_V1, githooks=bad))

    def test_rt8_k_crlf_v2_is_a_no_op(self, tmp_path):
        """(k)(F0c (a)):CRLF 版的 v2 經 CRLF→LF 等於 v2 ⇒ 已是最新 ⇒ no-op,內容與 mtime 都不變。"""
        crlf = _T156_V2.replace(b"\n", b"\r\n")
        t = _t156_rehook_target(tmp_path, git_hook=crlf, githooks=crlf)
        mod = _t156_rehook_mod()
        before, hooks = _t156_snapshot(t), _t156_hook_state(t)
        assert mod.rehook(str(t)) == "no-op"
        assert _t156_snapshot(t) == before
        assert _t156_hook_state(t) == hooks


# ── RT9 / RT10:install 的事前檢查(G4、D-10、F0c (b))─────────────────────────

class TestT156RT9RT10InstallPrecheck:

    def test_rt9_no_venv_gates_fails_before_the_first_write(self, tmp_path, monkeypatch):
        """RT9:乾淨、已 git init 的 target,沒有 `.venv-gates` ⇒ install 在第一次寫入之前失敗;
        工作區、index、`.git/hooks/` 全部不變(快照涵蓋 `.git/` 全部)。"""
        _t156_isolated_home(tmp_path, monkeypatch)
        t = _t156_clean_git_target(tmp_path)
        mod = _load("install_t156_rt9", "install.py")
        before = _t156_snapshot(t)
        with pytest.raises(SystemExit) as e:
            mod.main(str(t))
        assert e.value.code not in (0, None)
        assert _t156_snapshot(t) == before

    def test_rt9_a_missing_target_directory_is_not_created(self, tmp_path, monkeypatch):
        """`install.py:625` 的 `os.makedirs(target)` 本身就是一次寫入 —— 事前檢查要排在它之前。"""
        _t156_isolated_home(tmp_path, monkeypatch)
        t = tmp_path / "does-not-exist"
        mod = _load("install_t156_rt9b", "install.py")
        with pytest.raises(SystemExit) as e:
            mod.main(str(t))
        assert e.value.code not in (0, None)
        assert not t.exists()

    @pytest.mark.parametrize("installer_python", ["as-is", "pretend-upstream-venv"])
    def test_rt10_an_invalid_identity_fails_before_the_first_write(self, tmp_path, monkeypatch,
                                                                    installer_python):
        """RT10:`.venv-gates` 存在但身分不合法 ⇒ 在第一次寫入之前失敗。
        驗證用的直譯器必須是 `<target>/.venv-gates` 那一支,執行**上游**的 `runtime_identity.py`,
        帶 `--repo <target> --profile downstream`;不是 install 自己的 `sys.executable` ——
        install 本身在合法的上游 `.venv-gates` 裡執行時,結果也必須相同(F0c (b))。"""
        _t156_isolated_home(tmp_path, monkeypatch)
        t = _t156_clean_git_target(tmp_path)
        _t156_fake_venv(t)
        with open(str(t / ".git" / "info" / "exclude"), "a", encoding="utf-8", newline="\n") as f:
            f.write(".venv-gates/\n")
        if installer_python == "pretend-upstream-venv":
            fake_up = os.path.join(str(tmp_path), "upstream", ".venv-gates", "Scripts", "python.exe")
            monkeypatch.setattr(_t156_sys, "executable", fake_up)
        mod = _load("install_t156_rt10_" + installer_python.replace("-", "_"), "install.py")
        real_run = _t156_subprocess.run
        identity_calls = []

        def spy(args, *a, **kw):
            if any("runtime_identity.py" in str(x) for x in args):
                identity_calls.append([str(x) for x in args])
                return _t156_subprocess.CompletedProcess(args, 1, b"", b"identity: profile mismatch")
            return real_run(args, *a, **kw)
        monkeypatch.setattr(mod.subprocess, "run", spy)
        before = _t156_snapshot(t)
        with pytest.raises(SystemExit) as e:
            mod.main(str(t))
        assert e.value.code not in (0, None)
        assert identity_calls, "install 沒有執行身分檢查就往下走了"
        argv = identity_calls[0]
        assert os.path.normcase(os.path.abspath(argv[0])) in _t156_venv_pythons(t), argv
        assert argv[0] != _t156_sys.executable and argv[0] != "python", argv
        want_ri = os.path.normcase(os.path.realpath(os.path.join(mod.SRC_ROOT, ".claude", "portable",
                                                                 "runtime_identity.py")))
        assert os.path.normcase(os.path.realpath(argv[1])) == want_ri, argv
        i, j = argv.index("--repo"), argv.index("--profile")
        assert os.path.normcase(os.path.realpath(argv[i + 1])) == os.path.normcase(os.path.realpath(str(t)))
        assert argv[j + 1] == "downstream", argv
        assert _t156_snapshot(t) == before
