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
        """b01f5c2 的語意要跟著裝過去,否則新 repo 的更新路徑會 blind-copy 它。"""
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
