# -*- coding: utf-8 -*-
"""git 輸出的非 ASCII 路徑(F-042 第三次)。

git 對非 ASCII 檔名預設回傳 C-quoted 路徑:`"docs/plans/\\345\\217\\260….md"`。
拿 `--name-only` + `splitlines()` 取路徑的地方,全部收到帶引號與 octal escape
的字串;下游 `replace("\\\\", "/")`(為了正規化 os.path.relpath 的 Windows
反斜線而存在,本身正當)會把 escape 的反斜線也換掉 —— 路徑徹底壞掉。

後果依位置不同,方向也不同:
  gate.py       路徑壞 → top 不是 docs → 判成原始碼 → R2 誤擋(fail-closed,看得見)
  leak_scan.py  路徑壞 → io.open 失敗 → `except: continue` → **靜默不掃(fail-open)**
  install.py    路徑壞 → 檔案漏帶 / legacy 清單寫入壞路徑,R6 的 cat-file 必失敗

**結構上正確的解是 `-z`(NUL 分隔),不是 `core.quotePath=false`。**
quotePath 只關掉引號,檔名若含換行或引號本身仍有歧義;NUL 是唯一不可能出現在
路徑裡的位元組,分隔語意無歧義。

紅燈語料一律用非 ASCII 檔名 —— 只用 ASCII 測的話,這個缺陷永遠不會現身(F-042)。
"""
import io
import os
import subprocess

import pytest

CJK_DOC = "docs/plans/台股計畫書_v2.md"
CJK_SRC = "src/探針模組.py"


def _git(args, cwd):
    subprocess.run(["git"] + args, cwd=str(cwd), capture_output=True, check=False)


@pytest.fixture()
def repo(tmp_path):
    """一個真的 git repo,staged 一份中文檔名的文件與一份中文檔名的 .py。"""
    _git(["init", "-q"], tmp_path)
    _git(["config", "user.email", "t@local"], tmp_path)
    _git(["config", "user.name", "t"], tmp_path)
    for rel in (CJK_DOC, CJK_SRC):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("內容\n", encoding="utf-8")
    _git(["add", "-A"], tmp_path)
    return tmp_path


def _load(name, rel):
    import importlib.util
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", rel))
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class TestPathsComeBackIntact:
    """三支各自獨立可攜,所以各自要有取路徑的正確做法 —— 逐一斷言,
    避免其中一支修好、另一支留著同一個洞(F-042 正是這樣散開的)。"""

    def test_gate_reads_staged_paths_intact(self, repo):
        gate = _load("gate_cjk", ".claude/hooks/gate.py")
        got = gate.staged_paths(str(repo))
        assert CJK_DOC in got, "gate 取到的 staged 路徑不是原樣:%r" % got
        assert CJK_SRC in got
        assert not any('\\' in p or p.startswith('"') for p in got), \
            "路徑帶引號或反斜線 escape:%r" % got

    def test_leak_scan_reads_staged_paths_intact(self, repo):
        ls = _load("ls_cjk", ".claude/portable/leak_scan.py")
        got = ls.staged_files(cwd=str(repo))
        assert CJK_DOC in got, "leak_scan 取到的 staged 路徑不是原樣:%r" % got
        assert not any('\\' in p or p.startswith('"') for p in got)

    def test_install_lists_cjk_files(self, repo):
        install = _load("install_cjk", ".claude/portable/install.py")
        got = install.git_paths(["ls-files"], str(repo))
        assert CJK_DOC in got, "install 列不到中文檔名:%r" % got
        assert CJK_SRC in got


class TestClassificationSurvivesCJK:
    """路徑取對只是第一步 —— 判定要跟著對,否則只是把壞值搬到下一站。"""

    def test_a_cjk_document_is_not_source(self):
        gate = _load("gate_cls", ".claude/hooks/gate.py")
        assert gate.is_source_path(CJK_DOC) is False, \
            "中文檔名的 docs/ 文件被判成原始碼 —— R2 會誤擋"

    def test_a_cjk_python_file_is_still_source(self):
        gate = _load("gate_cls2", ".claude/hooks/gate.py")
        assert gate.is_source_path(CJK_SRC) is True, \
            "中文檔名的 .py 被判成非原始碼 —— 那是 fail-open"


class TestLeakScanActuallyReadsCJKFiles:
    """leak_scan 的失效方向是 fail-open:路徑壞 → 開檔失敗 → except 吞掉 → 不掃。
    所以要驗的不是「有沒有報錯」,是「秘密有沒有被抓到」。"""

    def test_a_secret_in_a_cjk_named_file_is_caught(self, tmp_path):
        ls = _load("ls_read", ".claude/portable/leak_scan.py")
        f = tmp_path / "報告_機密.md"
        f.write_text("key = " + "AIza" + "B" * 35 + "\n", encoding="utf-8")
        assert ls.scan([str(f)]) == 1, "中文檔名檔案裡的 key 沒被抓到"


class TestNulSeparatedNotQuotePath:
    """明文釘住做法:必須是 -z,不是 core.quotePath=false。
    後者只解引號,檔名含換行或引號時仍有歧義 —— 剛好夠用不是正確。"""

    @pytest.mark.parametrize("rel", [
        ".claude/hooks/gate.py",
        ".claude/portable/leak_scan.py",
        ".claude/portable/install.py",
    ])
    def test_uses_nul_separator(self, rel):
        src = io.open(os.path.join(os.path.dirname(__file__), "..", rel),
                      encoding="utf-8").read()
        assert '"-z"' in src, "%s 沒有用 -z 取 git 路徑" % rel
        # 偵測**使用**而不是**提及**:git 參數是 Python 字串常數(雙引號),
        # 散文裡的說明用反引號。字面 grep 分不出兩者 —— 同一個坑在
        # leak_scan 掃 friction-log 時撞過(防禦清單長得像洩漏,F-062)。
        assert '"core.quotePath' not in src, \
            "%s 把 core.quotePath 當 git 參數用了 —— 那是剛好夠用的解,不是結構上正確的解" % rel
