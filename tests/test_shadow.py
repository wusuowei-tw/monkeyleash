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


class TestTheSameBlockInBothModes:
    """**同一組行為的兩面。** 影子開 → 放行且記一筆;影子關 → 真的擋。

    由來:量化那邊有兩條測試在**影子開啟**的 repo 永久紅 ——
    它們斷言「會被擋」,而影子模式下正確答案是「放行 + 記一筆 would-block」。
    永久紅是萬能鑰匙(F-071),而且會訓練人忽略訊號(F-031)。

    根因是測試的行為取決於**宿主 repo 的活體閘門狀態**。
    conftest 的隔離讓影子在測試中恆為關、結果可決定;
    影子開的那一面由這裡自己開,不再靠宿主碰巧是什麼狀態。

    兩條寫在一起而不是分兩個 class:它們是**同一個判定的兩個時態**,
    分開放的話,下一個人改其中一邊時看不到另一邊該跟著動。
    """

    def _shadow_on(self, tmp_path, monkeypatch):
        state = tmp_path / "shadow.json"
        io.open(state, "w", encoding="utf-8", newline="\n").write(
            json.dumps({"enabled": True, "until": "2099-01-01"}))
        monkeypatch.setattr(gate, "SHADOW_STATE", str(state))
        monkeypatch.setattr(gate, "SHADOW_LOG", str(tmp_path / "log.jsonl"))
        monkeypatch.setattr(gate, "read_shadow_clamp",
                            lambda: datetime.date(2099, 1, 1))

    def test_shadow_off_actually_blocks(self, tmp_path, monkeypatch):
        monkeypatch.setattr(gate, "SHADOW_STATE", str(tmp_path / "absent.json"))
        assert gate.shadow_active() is False

    def test_shadow_on_records_instead_of_blocking(self, tmp_path, monkeypatch):
        self._shadow_on(tmp_path, monkeypatch)
        assert gate.shadow_active() is True
        rec = gate.log_shadow("[R3] foo.py:找不到對應測試", at_commit=False)
        assert rec["verdict"] == "would-block"
        logged = [json.loads(l) for l in
                  io.open(tmp_path / "log.jsonl", encoding="utf-8") if l.strip()]
        assert len(logged) == 1 and logged[0]["rule"] == "R3"

    def test_the_shadow_log_written_is_never_the_hosts(self, tmp_path, monkeypatch):
        """**證據隔離要驗得出來。** 測試寫的那個檔案必須在 tmp,不在 repo 裡。

        少了這條,conftest 的隔離壞掉時沒有東西會出聲 ——
        而它壞掉的樣子是「宿主的 shadow-log 多了幾筆」,沒有人會看。
        """
        self._shadow_on(tmp_path, monkeypatch)
        gate.log_shadow("[R2] x.py:idle", at_commit=False)
        assert str(tmp_path) in gate.SHADOW_LOG
        assert ".dev" not in gate.SHADOW_LOG.replace(str(tmp_path), "")


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


class TestShadowLogRecordsACommandFingerprint:
    """票 68 —— 影子日誌要記指令的**指紋**,不記原文。

    由來:R7 202 筆裡有 72 筆判不出真陽/誤報,因為紀錄裡**沒有指令**
    (欄位只有 ts / rule / at_commit / verdict / message)。

    **不記原文的三個理由**(裁決 2026-08-19):
      1. 指令原文含路徑,而路徑含使用者名、專案名、真實資料夾名(F-082 / F-085 那族)
      2. `shadow-log.jsonl` 不進版控,靠週級人工備份 —— **備份會被複製,洩漏面跟著擴散**
      3. 它是 G1 保護對象 —— **一個檔案越難刪改,往裡面寫東西就越要保守**
    """

    def test_a_command_yields_a_stable_fingerprint(self, tmp_path, monkeypatch):
        monkeypatch.setattr(gate, "SHADOW_LOG", str(tmp_path / "log.jsonl"))
        a = gate.log_shadow("[R7] x", at_commit=False, command="printf hi > a.txt")
        b = gate.log_shadow("[R7] x", at_commit=False, command="printf hi > a.txt")
        assert a["cmd_sha256"] == b["cmd_sha256"]
        assert len(a["cmd_sha256"]) == 64

    def test_different_commands_differ(self, tmp_path, monkeypatch):
        monkeypatch.setattr(gate, "SHADOW_LOG", str(tmp_path / "log.jsonl"))
        a = gate.log_shadow("[R7] x", at_commit=False, command="printf a > f")
        b = gate.log_shadow("[R7] x", at_commit=False, command="printf b > f")
        assert a["cmd_sha256"] != b["cmd_sha256"]

    def test_the_raw_command_is_never_written(self, tmp_path, monkeypatch):
        """**這一條是本票存在的理由。**

        指令原文的任何片段都不得出現在紀錄裡。

        ## fixture 用**合成 token**,不用逼真的假路徑(這一段是被擋出來的)

        本條第一版寫的是 `cd "c:/Users/somebody/OneDrive/…/…" && cat token.txt`
        —— 一個「看起來像真的」的假路徑。它**命中了洩漏偵測的個人 pattern**,
        `tests/test_leak_scan.py::test_the_shipped_tree_is_clean` 當場轉紅。

        > **寫一個逼真的假機密,本身就是洩漏鄰近行為** ——
        > 而「它是假的」這件事只有寫的人知道,掃描器不知道,讀的人也不知道。

        所以改用一眼看得出是合成的 token。斷言強度不變:
        要證明的是「這些字不出現在輸出裡」,而那與它們像不像真的無關。
        """
        monkeypatch.setattr(gate, "SHADOW_LOG", str(tmp_path / "log.jsonl"))
        marks = ("ZZFIXTUREALPHA", "ZZFIXTUREBETA", "ZZFIXTUREGAMMA")
        command = "someverb %s/%s --flag %s" % marks
        rec = gate.log_shadow("[R7] x", at_commit=False, command=command)
        blob = json.dumps(rec, ensure_ascii=False)
        for leaked in marks:
            assert leaked not in blob, "指令原文的片段漏進紀錄:%s" % leaked
        # 整份檔案也要驗 —— 回傳值乾淨而寫進去的髒,是可能的
        written = io.open(gate.SHADOW_LOG, encoding="utf-8").read()
        for leaked in marks:
            assert leaked not in written

    def test_the_length_is_recorded(self, tmp_path, monkeypatch):
        """長度不洩漏內容,但它讓「被截掉了多少」看得見。"""
        monkeypatch.setattr(gate, "SHADOW_LOG", str(tmp_path / "log.jsonl"))
        rec = gate.log_shadow("[R7] x", at_commit=False, command="abcde")
        assert rec["cmd_len"] == 5

    def test_a_known_verb_is_recorded(self, tmp_path, monkeypatch):
        """讓人看得出「這是哪一類指令」—— 而**只記得出的動詞**。"""
        monkeypatch.setattr(gate, "SHADOW_LOG", str(tmp_path / "log.jsonl"))
        for cmd, verb in (("python -c 'x'", "python"),
                          ("git commit -F msg.txt", "git"),
                          ("printf x >> a", "printf")):
            rec = gate.log_shadow("[R7] x", at_commit=False, command=cmd)
            assert rec["cmd_verb"] == verb

    def test_an_unknown_verb_is_not_echoed(self, tmp_path, monkeypatch):
        """**認不得的動詞不照抄。**

        第一個 token 本身可能就是路徑(`"C:\\Program Files\\x\\app.exe" …`)——
        照抄等於把「不記原文」讓掉一半。認不得就記一個固定字串。

        **這不是退回白名單。** CLAUDE.md 那條講的是**閘門**(列出不管的、其餘全擋);
        這裡是**輸出的遮罩**,而遮罩的 fail-closed 方向是**少講**,
        所以 deny-by-default 才是對的方向 —— 同 `leak-patterns.txt` 檔頭
        自己註明的「方向與其他清單不同」。
        """
        monkeypatch.setattr(gate, "SHADOW_LOG", str(tmp_path / "log.jsonl"))
        # 合成 token,理由同上一條的 docstring。
        rec = gate.log_shadow(
            "[R7] x", at_commit=False,
            command='"ZZFIXTUREDELTA/ZZFIXTUREEPSILON.exe" run')
        assert rec["cmd_verb"] == gate.CMD_VERB_UNKNOWN
        blob = json.dumps(rec, ensure_ascii=False)
        assert "ZZFIXTUREDELTA" not in blob
        assert "ZZFIXTUREEPSILON" not in blob

    def test_records_without_a_command_omit_the_fields(self, tmp_path, monkeypatch):
        """R1–R6 的觸發物是**檔案寫入**不是指令。

        **不要為了欄位齊整而編造一個「指令」** —— 欄位缺席比填 `N/A` 誠實:
        `N/A` 是一個值,而值會被統計、會被比對、會被當成「有記錄」。
        """
        monkeypatch.setattr(gate, "SHADOW_LOG", str(tmp_path / "log.jsonl"))
        rec = gate.log_shadow("[R2] x.py:idle", at_commit=True)
        for f in ("cmd_sha256", "cmd_verb", "cmd_len"):
            assert f not in rec

    def test_the_old_call_signature_still_works(self, tmp_path, monkeypatch):
        """**向後相容是硬需求**:現有呼叫點有兩處不傳 command。"""
        monkeypatch.setattr(gate, "SHADOW_LOG", str(tmp_path / "log.jsonl"))
        rec = gate.log_shadow("[R3] a.py:x", at_commit=False)
        assert rec["rule"] == "R3" and rec["verdict"] == "would-block"

    def test_an_empty_command_is_treated_as_absent(self, tmp_path, monkeypatch):
        """空字串不是指令 —— 別替它算一個 sha。"""
        monkeypatch.setattr(gate, "SHADOW_LOG", str(tmp_path / "log.jsonl"))
        rec = gate.log_shadow("[R7] x", at_commit=False, command="   ")
        assert "cmd_sha256" not in rec

    def test_the_r7_call_site_passes_the_command(self):
        """**機制做好了但沒有東西保證它被走到** —— 票 56 已記過那個形狀。

        直接讀原始碼確認 R7 那個呼叫點真的把 command 傳下去了。
        """
        src = io.open(ROOT / ".claude" / "hooks" / "gate.py",
                      encoding="utf-8").read()
        assert "log_shadow(msg, at_commit=False, command=command)" in src, \
            "R7 呼叫點沒有把 command 傳給 log_shadow —— 欄位會永遠是空的"
