# -*- coding: utf-8 -*-
"""安裝器產出的標記表(票 12)。

**為什麼這個檔案叫 `test_install.py`**:R3 由實作反查測試,規則問的是
`tests/test_<實作名>.py`。`install.py` 既有的測試叫 `test_install_defaults.py`
—— 對人來說看得出是它的測試,**對規則來說 `install.py` 沒有測試**。
於是 R3 的前半永遠擋著它,而擋下的訊息說「請先寫測試」,現場卻是測試早就寫好了。
又一次「規則判錯對象」:人看名字的意思,規則看名字的形狀。

兩個檔案並存是**這一批的權宜**:合併需要刪掉舊檔,而 R7 目前**沒有刪除出口**
(見票 13)。等那張票關掉再併,不在這裡靠繞路解決。
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
