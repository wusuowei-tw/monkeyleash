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


class TestR8IsEnumerated:
    def test_r8_is_in_rule_codes(self):
        assert "R8" in gate.rule_codes()
