# -*- coding: utf-8 -*-
"""影子模式:安全閥、fail-closed 方向、per-rule 晉升。

安全閥 SHADOW_MAX 住在 G1 保護的 ~/.claude/shadow-clamp.txt,gate.py 唯讀(乙案)。
**fail-closed 方向**:安全閥缺席/壞掉 → 影子不生效、照常擋 —— 往「閘門開著」倒。
"""

import datetime
import importlib.util
import io
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gate = _load("gate_shadow", ".claude/hooks/gate.py")


def _clamp(tmp_path, text, bom=False):
    p = tmp_path / "shadow-clamp.txt"
    data = text.encode("utf-8-sig" if bom else "utf-8")
    p.write_bytes(data)
    return str(p)


class TestReadShadowClamp:
    def test_a_valid_clamp_parses(self, tmp_path, monkeypatch):
        monkeypatch.setattr(gate, "SHADOW_CLAMP",
                            _clamp(tmp_path, "# 註解\nSHADOW_MAX=2026-09-15\n"))
        assert gate.read_shadow_clamp() == datetime.date(2026, 9, 15)

    def test_a_BOM_clamp_must_parse(self, tmp_path, monkeypatch):
        """PowerShell Set-Content -Encoding utf8 寫的是帶 BOM 的 UTF-8。
        用 utf-8 讀、哪天 BOM 黏上鍵名 -> 解析失敗 -> 影子永開不了、而訊息都說正常。
        輸入端的坑要在進門前排掉 —— 用 utf-8-sig 讀。"""
        monkeypatch.setattr(gate, "SHADOW_CLAMP",
                            _clamp(tmp_path, "SHADOW_MAX=2026-09-15\n", bom=True))
        assert gate.read_shadow_clamp() == datetime.date(2026, 9, 15)

    def test_missing_clamp_is_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr(gate, "SHADOW_CLAMP", str(tmp_path / "gone.txt"))
        assert gate.read_shadow_clamp() is None

    def test_multiple_max_lines_is_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr(gate, "SHADOW_CLAMP",
                            _clamp(tmp_path, "SHADOW_MAX=2026-09-15\nSHADOW_MAX=2099-01-01\n"))
        assert gate.read_shadow_clamp() is None

    def test_a_bad_date_is_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr(gate, "SHADOW_CLAMP",
                            _clamp(tmp_path, "SHADOW_MAX=not-a-date\n"))
        assert gate.read_shadow_clamp() is None

    def test_an_unknown_line_is_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr(gate, "SHADOW_CLAMP",
                            _clamp(tmp_path, "SHADOW_MAX=2026-09-15\nFOO=bar\n"))
        assert gate.read_shadow_clamp() is None


class TestShadowActiveFailsClosed:
    def _setup(self, tmp_path, monkeypatch, clamp_text=None, until=None):
        if clamp_text is not None:
            monkeypatch.setattr(gate, "SHADOW_CLAMP", _clamp(tmp_path, clamp_text))
        else:
            monkeypatch.setattr(gate, "SHADOW_CLAMP", str(tmp_path / "no-clamp.txt"))
        state = tmp_path / "shadow.json"
        if until is not None:
            state.write_text(json.dumps({"until": until}), encoding="utf-8")
        monkeypatch.setattr(gate, "SHADOW_STATE", str(state))

    def test_no_clamp_means_no_shadow(self, tmp_path, monkeypatch):
        """安全閥缺席 -> 影子不生效(往閘門開著倒,不往影子開著倒)。"""
        self._setup(tmp_path, monkeypatch, clamp_text=None, until="2026-09-15")
        assert gate.shadow_active(datetime.date(2026, 8, 20)) is False

    def test_no_repo_declaration_means_no_shadow(self, tmp_path, monkeypatch):
        self._setup(tmp_path, monkeypatch, clamp_text="SHADOW_MAX=2026-09-15\n", until=None)
        assert gate.shadow_active(datetime.date(2026, 8, 20)) is False

    def test_active_within_both_dates(self, tmp_path, monkeypatch):
        self._setup(tmp_path, monkeypatch, clamp_text="SHADOW_MAX=2026-09-15\n",
                    until="2026-09-10")
        assert gate.shadow_active(datetime.date(2026, 8, 20)) is True

    def test_clamp_caps_the_repo_date(self, tmp_path, monkeypatch):
        """repo 宣告 until=2099,但 clamp=9/15 -> 9/16 就不生效(安全閥壓過)。"""
        self._setup(tmp_path, monkeypatch, clamp_text="SHADOW_MAX=2026-09-15\n",
                    until="2099-01-01")
        assert gate.shadow_active(datetime.date(2026, 9, 16)) is False
        assert gate.shadow_active(datetime.date(2026, 9, 15)) is True


class TestLogShadow:
    def test_a_would_block_is_logged_with_rule(self, tmp_path, monkeypatch):
        monkeypatch.setattr(gate, "SHADOW_LOG", str(tmp_path / "log.jsonl"))
        gate.log_shadow("[R3] foo.py:找不到對應測試", at_commit=True)
        rec = json.loads(io.open(tmp_path / "log.jsonl", encoding="utf-8").readline())
        assert rec["rule"] == "R3" and rec["at_commit"] is True
        assert rec["verdict"] == "would-block"


class TestEnforceTag:
    """正式擋下的訊息要帶 `[enforce]` 狀態標示 —— 從任何一次攔截訊息就能讀出
    『現在是影子還是正式』,不必查 .dev/。影子側靠 shadow-log 的 verdict,
    正式側沒有檔案軌跡,所以標示必須進訊息本身。"""

    def test_inserts_enforce_after_rule_code(self):
        out = gate.tag_enforce("[R2] foo.py:idle 不可寫入原始碼")
        assert out.startswith("[R2][enforce]")

    def test_handles_rule_variant_with_slash(self):
        # 規則代號可能是 [R2/commit];標示要插在整個括號之後,不是 [R2 之後。
        out = gate.tag_enforce("[R2/commit] foo.py:前置站卻要提交原始碼")
        assert out.startswith("[R2/commit][enforce]")

    def test_rule_of_still_reads_code_after_tagging(self):
        # 加標示不能打壞既有的規則抽取(shadow_review 靠它逐條算晉升)。
        assert gate.rule_of(gate.tag_enforce("[R3] bar.py:找不到測試")) == "R3"

    def test_no_rule_code_falls_back_to_prefix_tag(self):
        assert gate.tag_enforce("something odd").startswith("[enforce] ")

    def test_empty_message_untouched(self):
        assert gate.tag_enforce("") == ""

    def test_enforce_and_shadow_are_distinguishable(self, tmp_path, monkeypatch):
        """同一條規則:正式擋 → 訊息含 [enforce];影子 → 日誌 verdict=would-block。
        兩態必須能從輸出區分,否則『閘門在擋還是在放』只能翻檔案。"""
        msg = "[R2] foo.py:idle 不可寫入原始碼"
        enforced = gate.tag_enforce(msg)
        monkeypatch.setattr(gate, "SHADOW_LOG", str(tmp_path / "log.jsonl"))
        rec = gate.log_shadow(msg, at_commit=False)
        assert "[enforce]" in enforced
        assert "[enforce]" not in rec["message"]      # 影子側不冒充正式
        assert rec["verdict"] == "would-block"          # 影子側自己的狀態標示


class TestPerRulePromotion:
    """晉升 per-rule 不全局:每條規則自己 ≥10 筆已分類且假陽率 <5% 才轉正。
    全局比率會讓一條規則的真陽稀釋另一條的假陽。"""

    def _load_review(self):
        return _load("shadow_review", ".claude/portable/shadow_review.py")

    def _log(self, tmp_path, rows):
        p = tmp_path / "log.jsonl"
        with io.open(p, "w", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        return str(p)

    def test_a_rule_with_enough_clean_classifications_promotes(self, tmp_path):
        sr = self._load_review()
        rows = [{"rule": "R2", "classification": "真陽"} for _ in range(10)]
        status = sr.promotion_status(self._log(tmp_path, rows))
        assert status["R2"]["promotable"] is True

    def test_under_ten_classified_holds(self, tmp_path):
        sr = self._load_review()
        rows = [{"rule": "R2", "classification": "真陽"} for _ in range(9)]
        status = sr.promotion_status(self._log(tmp_path, rows))
        assert status["R2"]["promotable"] is False

    def test_five_percent_false_positive_blocks_promotion(self, tmp_path):
        sr = self._load_review()
        # 20 筆,2 筆假陽 = 10% > 5% -> 不晉升
        rows = ([{"rule": "R3", "classification": "真陽"}] * 18 +
                [{"rule": "R3", "classification": "假陽/既有"}] * 2)
        status = sr.promotion_status(self._log(tmp_path, rows))
        assert status["R3"]["promotable"] is False

    def test_one_rule_does_not_dilute_another(self, tmp_path):
        """R2 全真陽(可晉升)、R3 全假陽(不可)—— 各算各的,不混成全局比率。"""
        sr = self._load_review()
        rows = ([{"rule": "R2", "classification": "真陽"}] * 10 +
                [{"rule": "R3", "classification": "假陽/範圍"}] * 10)
        status = sr.promotion_status(self._log(tmp_path, rows))
        assert status["R2"]["promotable"] is True
        assert status["R3"]["promotable"] is False

    def test_unclassified_entries_do_not_count(self, tmp_path):
        sr = self._load_review()
        rows = ([{"rule": "R2", "classification": "真陽"}] * 5 +
                [{"rule": "R2"}] * 10)   # 10 筆未分類
        status = sr.promotion_status(self._log(tmp_path, rows))
        assert status["R2"]["classified"] == 5 and status["R2"]["promotable"] is False
