# -*- coding: utf-8 -*-
"""research 站:探索區,寫入綁路徑不綁階段;R8 生產碼不得 import research/。

設計裁決(見 docs/adr/0011):
- research 是**階段**(pipeline-stages.yaml),不是規則開關 —— 階段定義已是唯讀凍結
  來源,不需要 per-rule 開關的 C 案(那卡在凍結來源不存在)。
- allows_src_write 綁**路徑**(src_write_scope),不綁階段:只對 research/** 生效。
  agent 能自己寫 pipeline.json 宣告階段,所以把豁免爆炸半徑縮到零 ——
  **宣告 research 之後仍不能寫 src/。** 這是本檔的主測試。
- R8:生產程式碼不得 import research/。反方向放行(research 可 import 生產資料層)。
- 出口只有兩個:殺掉、或移出 research/ 走六站。移出就是六站事件,沒有第三條出口。
"""

import importlib.util
import io
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "gate_research", ROOT / ".claude" / "hooks" / "gate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gate = _load()


class TestResearchWriteIsPathScoped:
    """allows_src_write 綁路徑不綁階段。"""

    def test_declaring_research_still_cannot_write_src(self, monkeypatch):
        """**主測試**:宣告 research 之後,寫生產碼(src/)仍然被擋。

        豁免爆炸半徑縮到零 —— 不管誰宣告 research(agent 自己也能),都寫不了生產碼。
        """
        monkeypatch.setattr(gate, "load_stage", lambda: ("research", None))
        msg = gate.check("macro_audit/model.py", "x = 1", at_commit=False)
        assert msg and "R2" in msg, "宣告 research 就寫得了 src/(豁免爆炸):%r" % msg

    def test_research_can_write_under_its_scope(self, monkeypatch):
        monkeypatch.setattr(gate, "load_stage", lambda: ("research", None))
        assert gate.check("research/explore.py", "x = 1", at_commit=False) is None

    def test_the_scope_is_boundary_matched_not_prefix(self, monkeypatch):
        """`research/` 不得讓 `research_utils/`(生產目錄)一起可寫 —— F-051。"""
        monkeypatch.setattr(gate, "load_stage", lambda: ("research", None))
        msg = gate.check("research_utils/helper.py", "x = 1", at_commit=False)
        assert msg and "R2" in msg, "research_utils 被當成 research/ 放行了:%r" % msg

    def test_the_scope_holds_at_commit_time_too(self, monkeypatch):
        """範圍是路徑規則,與時點無關 —— 提交時寫 src/ 一樣擋。"""
        monkeypatch.setattr(gate, "load_stage", lambda: ("research", None))
        msg = gate.check("macro_audit/model.py", "x = 1", at_commit=True)
        assert msg and "R2" in msg, msg


class TestResearchExemptsR3InScope:
    """research/ 底下豁免 R3(探索不必先寫測試),範圍外照常。"""

    def test_research_file_needs_no_test(self, monkeypatch):
        monkeypatch.setattr(gate, "load_stage", lambda: ("research", None))
        # research/foo.py 沒有 tests/test_foo.py,但在 research 站不該被 R3 擋
        assert gate.check("research/foo.py", "def explore(): pass") is None

    def test_r3_still_applies_in_implement(self, monkeypatch):
        """豁免只在 research 站的 research/ 底下 —— implement 站照常要測試。"""
        monkeypatch.setattr(gate, "load_stage", lambda: ("implement", "01"))
        msg = gate.check("research/foo.py", "def explore(): pass")
        # implement 站沒有 research 的 scope 豁免;research/ 也不是非原始碼 -> R3 該管
        assert msg and "R3" in msg, msg


class TestR8ProductionMustNotImportResearch:
    """R8:生產程式碼不得 import research/。反方向放行。"""

    @pytest.mark.parametrize("content", [
        "import research\n",
        "import research.explore\n",
        "from research import explore\n",
        "from research.explore import thing\n",
    ])
    def test_production_importing_research_is_blocked(self, content):
        assert gate.imports_research(content) is True, content

    @pytest.mark.parametrize("content", [
        "import research_utils\n",           # F-051:不是 research/
        "from research_helpers import x\n",  # 同上
        "import researched\n",
        "from my_research import x\n",
    ])
    def test_a_boundary_neighbour_is_not_a_research_import(self, content):
        assert gate.imports_research(content) is False, content

    def test_research_importing_production_is_allowed(self, monkeypatch):
        """反方向:research/ 底下的碼 import 生產資料層 —— 放行。"""
        monkeypatch.setattr(gate, "load_stage", lambda: ("research", None))
        assert gate.check("research/explore.py",
                          "from macro_audit import data\nx = 1") is None

    def test_a_production_file_importing_research_is_blocked_by_r8(self, monkeypatch):
        monkeypatch.setattr(gate, "load_stage", lambda: ("implement", "01"))
        # 生產檔有對應測試(避免被 R3 先擋),但 import 了 research -> R8 擋
        (ROOT / "tests").mkdir(exist_ok=True)
        msg = gate.check("macro_audit/model.py",
                         "from research import explore\n", at_commit=True)
        assert msg and "R8" in msg, "生產碼 import research 沒被 R8 擋:%r" % msg

    def test_malformed_python_fails_closed(self):
        """AST 解析不了 -> 不能當作『沒 import research』放行。"""
        # 語法壞掉時,保守起見當作可能有問題(呼叫端據此處理)
        assert gate.imports_research("import research\nthis is not python(") is True


class TestTheSyntaxAxisIsEnumeratedNotSampled:
    """票 104 —— **語法軸是封閉集合,所以用枚舉,不是用樣本。**

    `imports_research()` 只認兩個 AST 節點型別(`ast.Import` / `ast.ImportFrom`),
    而那兩個型別底下的形式**是 Python 文法決定的,窮舉得完** ——
    不是本專案定的,所以更硬。

    `CLAUDE.md` 逐字:「封閉且可窮舉時,**枚舉勝過比對** ——
    因為**比對的漏是未知的,枚舉的漏是不存在的**。」

    上面那組(`TestR8ProductionMustNotImportResearch`)是**樣本**:
    4 個正控落在 4 格、4 個反控落在邊界。本組補的是**剩下的 7 格**。

    **全部是特徵化測試**(釘現行行為),寫完當下應為全綠 ——
    紅燈由票面第三節的七輪有界突變提供。
    """

    # ── ast.Import 的四個未測形式 ────────────────────────────────────

    def test_an_aliased_import_is_still_a_research_import(self):
        """`as` 只改本地綁定的名字,**不改被 import 的是什麼**。

        判定讀的是 `alias.name`(不是 `alias.asname`),所以別名不影響 ——
        而「不影響」這件事今天沒有斷言問過。
        少了它,一個改讀 `asname` 的重構會讓 `import research as r` 靜靜放行。
        """
        assert gate.imports_research("import research as r\n") is True

    def test_an_aliased_dotted_import_is_still_a_research_import(self):
        """點號 + 別名 —— 兩個變化疊在一起的那一格。

        `alias.name` 是 `research.explore`,取頂層 `split(".")[0]` 仍是 `research`。
        分開測是因為**點號與別名走的是不同的兩段程式碼**,一起壞與各自壞不一樣。
        """
        assert gate.imports_research("import research.explore as e\n") is True

    def test_research_among_several_names_on_one_line_is_caught(self):
        """一行多名:`import os, research`。

        `node.names` 是一個**串列**,而判定 `for alias in node.names` 要走完它。
        只看第一個的話,把 research 放在第二位就繞過了 ——
        **而繞過的寫法是合法 Python,不是什麼奇技。**
        """
        assert gate.imports_research("import os, research\n") is True

    # ── ast.ImportFrom 的三個未測形式 ────────────────────────────────

    def test_a_star_import_is_still_a_research_import(self):
        """`from research import *` —— 判定看的是 `node.module`,不是 `names`,
        所以星號不影響。這一格今天沒有斷言。
        """
        assert gate.imports_research("from research import *\n") is True

    def test_a_relative_import_of_the_package_name_is_not_caught(self):
        """**這一條釘的是 `gate.py:905` 註解【逐字宣告過】的行為**:

            # from research / from research.x import ...；相對 import(module=None)不算

        `from . import research` 的 `node.module` 是 `None`(實測),所以不算。
        **今天有註解、沒有斷言** —— 而註解不是機制。
        """
        assert gate.imports_research("from . import research\n") is False

    def test_a_two_level_relative_import_is_not_caught(self):
        """兩層的相對 import,`node.module` 同樣是 `None`(實測 level=2)。

        與上一條分開測:`level` 從 1 變 2 走的是同一段程式碼,
        但**判定完全不讀 `level`**(全庫 `grep node.level` 零命中),
        所以「1 跟 2 一樣」這件事要有一條斷言說出來。
        """
        assert gate.imports_research("from .. import research\n") is False

    def test_a_relative_import_whose_module_is_research_is_caught(self):
        """🔴 **現行行為,未裁是否正確。**

        `from .research import x` 的 `module='research'`、`level=1`(2026-09-04 實測),
        而 `gate.py` **不讀 `level`**(全庫 `grep "node.level"` 零命中)
        ⇒ 它被判成「import 了頂層 research/ 套件」。

        **但它 import 的是【同層一個叫 research 的模組】,不是頂層套件。**

        `gate.py:905` 的註解只講了 `module=None` 那一種相對 import,
        **沒說 `module` 非 None 的相對 import 算什麼** ——
        而讀的人會把那句讀成「相對 import 都不算」。

        **這一條釘的是「今天會擋」,不是「應該擋」。**
        要不要改成只認絕對 import(加 `node.level == 0`)是票 104 的候選一,
        **本票不裁**。改判的那一天,這條測試會紅 —— 那時它的工作就是
        **讓改判成為一個看得見的動作**,而不是一次沒有人注意到的行為漂移。
        """
        assert gate.imports_research("from .research import x\n") is True


class TestR8BlocksThroughCheckNotJustThePredicate:
    """票 104 —— **述詞對 ≠ 規則會擋。**

    上面兩組斷言的都是 `gate.imports_research()` 這個**述詞**。
    而使用者撞到的是 `check()`,中間隔著四個前置:

      `is_source_path(r)`     gate.py:1863  —— 不是原始碼就直接放行
      R2 的站別               gate.py:1936  —— 站別不可寫就先被 R2 擋
      `r.endswith(".py")`     gate.py:1948  —— 非 .py 連 R3/R8 都不進
      `not _under_research(r)` gate.py:1956 —— research/ 底下反方向放行

    **任何一個前置壞掉,述詞再對也擋不到人** —— 而述詞測試對那四層是盲的。

    既有只有一條走 `check()`(`test_a_production_file_importing_research_is_blocked_by_r8`,
    語料 `from research import explore`)。**本組不重複它、不重構它。**
    """

    @staticmethod
    def _verdict(monkeypatch, content):
        # `implement` 有 allows_src_write 且**沒有** src_write_scope
        # (只有 research 站有)—— 所以生產路徑寫得進去,R2 不擋。
        monkeypatch.setattr(gate, "load_stage", lambda: ("implement", "01"))
        # `is_source_path` 是純字串判定,目錄不必真的存在。
        return gate.check("macro_audit/model.py", content)

    def test_a_plain_import_is_blocked_through_check(self, monkeypatch):
        """對應述詞測試的 `import research\\n`,但走完整條 `check()`。"""
        msg = self._verdict(monkeypatch, "import research\n")
        assert msg and "R8" in msg, "走 check() 時 import research 沒被擋:%r" % msg

    def test_a_dotted_import_is_blocked_through_check(self, monkeypatch):
        """對應 `import research.explore\\n`。"""
        msg = self._verdict(monkeypatch, "import research.explore\n")
        assert msg and "R8" in msg, "走 check() 時點號 import 沒被擋:%r" % msg

    def test_a_dotted_from_import_is_blocked_through_check(self, monkeypatch):
        """對應 `from research.explore import thing\\n`。

        `from research import explore` 刻意不寫 —— 既有
        `test_a_production_file_importing_research_is_blocked_by_r8` 用的正是它。
        """
        msg = self._verdict(monkeypatch, "from research.explore import thing\n")
        assert msg and "R8" in msg, "走 check() 時點號 from-import 沒被擋:%r" % msg


class TestR8IsEnumerated:
    def test_r8_is_in_rule_codes(self):
        assert "R8" in gate.rule_codes()
