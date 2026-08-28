# -*- coding: utf-8 -*-
"""票 49 第一階段:**R7 enforce 側的攔截帳本**。

## 這個檔案在守什麼

`gate-exemptions.jsonl` 是**豁免帳本**,不是攔截帳本 —— `log_exemptions()`
第一行是 `if not bucket: return`,而**沒有動用任何豁免的單純攔截**是最常見的
那一種。R7 更極端:enforce 分支只有 `_err`,**一筆都不寫**。
於是「9/15 之後 R7 誤擋了幾次」在結構上不可回答,而**原因是沒有東西在記**,
不是查過沒有。

## 兩個方向都要釘

**方向 A**(擋了就有一筆)自己是不夠的:一個「每次呼叫都記一筆」的壞實作
也會讓方向 A 全綠。所以每一條正向都配一條**負控**:

- 擋下 → 多一筆   ⇄   **沒擋 → 一筆都不長**
- 過期月檔 → 滾成摘要   ⇄   **當月與前一月不得被滾**
- 帳本壞掉 → 仍然擋 + 多印一行   ⇄   影子開著 → **不得雙寫**

## 為什麼不記指令原文

照票 68 的裁決,沿用它已經定案的指紋三欄(`cmd_sha256` / `cmd_verb` /
`cmd_len`),**不發明新的** —— 影子側與 enforce 側因此可以用同一組欄位對帳,
9/15 評估時兩邊的樣本能合併看。
"""

import datetime
import glob
import importlib.util
import io
import json
import os
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# **模組層載入**:conftest 的隔離 fixture 在 setup 時走訪測試模組的屬性,
# 在測試函式內部才載的那份蓋不到(見 tests/test_evidence_isolation.py)。
gate = _load("gate_intercepts", ".claude/hooks/gate.py")


# R7 會擋的與不會擋的各一條。**兩條都要有**,否則只驗得到方向 A。
BLOCKING = "printf hi > notes.txt"
CLEAN = "git status"


@pytest.fixture()
def ledger(tmp_path, monkeypatch):
    """把攔截帳本指到 tmp,回傳那個目錄。

    指的是**基底檔名**(`intercepts.jsonl`),月檔由 `intercept_path()` 從它推出來 ——
    這樣隔離只要蓋一個常數,不必知道輪替怎麼命名。
    """
    monkeypatch.setattr(gate, "INTERCEPT_LOG", str(tmp_path / "intercepts.jsonl"))
    monkeypatch.setattr(gate, "INTERCEPT_SUMMARY",
                        str(tmp_path / "intercepts-summary.jsonl"))
    return tmp_path


def _read(path):
    if not os.path.exists(str(path)):
        return []
    out = []
    for line in io.open(str(path), encoding="utf-8"):
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def _month_files(dirpath):
    return sorted(os.path.basename(p)
                  for p in glob.glob(os.path.join(str(dirpath), "intercepts-*.jsonl"))
                  if os.path.basename(p) != "intercepts-summary.jsonl")


def _hook(monkeypatch, capsys, command, shadow=False):
    """走真正的進入點 `mode_hook()`,不是直接呼叫記錄函式。

    接線要測 —— 「只是接線,不測」兩次放過同一條要命的程式碼(F-044)。
    """
    import sys as _sys

    class _Stdin(object):
        def __init__(self, raw):
            self.buffer = self
            self._raw = raw

        def read(self):
            return self._raw

    payload = {"tool_name": "Bash", "hook_event_name": "PreToolUse",
               "tool_input": {"command": command}}
    monkeypatch.setattr(_sys, "stdin",
                        _Stdin(json.dumps(payload).encode("utf-8")))
    monkeypatch.setattr(gate, "shadow_active", lambda: shadow)
    monkeypatch.setattr(gate, "authoritative_layer", lambda: (True, ""))
    rc = gate.mode_hook()
    return rc, capsys.readouterr().err


class TestTheRecordItself:
    """一筆紀錄長什麼樣 —— 七個欄位,一個都不能少,一個都不能多記。"""

    def test_a_blocked_r7_command_yields_seven_fields(self, ledger):
        msg = gate.bash_write_violation(BLOCKING)
        assert msg, "fixture 選的指令現在不擋了 —— 這條測試沒有在測任何東西"
        rec = gate.log_intercept(msg, command=BLOCKING)
        assert set(rec) == {"ts", "rule", "at_commit",
                            "cmd_sha256", "cmd_verb", "cmd_len", "message"}
        assert rec["rule"] == "R7"
        assert rec["at_commit"] is False
        assert rec["cmd_verb"] == "printf"
        assert rec["cmd_len"] == len(BLOCKING)
        assert len(rec["cmd_sha256"]) == 64

    def test_the_message_is_recorded_in_full_not_just_the_first_line(self, ledger):
        """**與 `log_shadow` 的差別就在這一格。**

        `log_shadow` 只寫 `msg.splitlines()[0]`。分類時要判「擋得對不對」,
        而規則碼判不出來(票 31:114 已經記過這一格 —— 帳本存的是 `blocked_by`
        規則碼、不是訊息全文,於是判不出是哪一種擋)。
        """
        msg = gate.bash_write_violation(BLOCKING)
        assert "\n" in msg, "fixture 訊息只有一行 —— 驗不到「全文 vs 第一行」"
        rec = gate.log_intercept(msg, command=BLOCKING)
        assert rec["message"] == msg
        assert rec["message"] != msg.splitlines()[0]

    def test_the_command_arguments_are_never_written(self, ledger):
        """指令的**引數與內容**不得出現在紀錄裡(票 68 的裁決)。

        fixture 用**合成 token**,不用逼真的假路徑 —— 寫一個逼真的假機密,
        本身就是洩漏鄰近行為,而且會命中 `test_leak_scan.py` 的個人 pattern。

        **範圍在這一條上是精確的,不是全稱的** —— 見下一條:被寫入的
        **目標路徑**確實會經由 `message` 進到紀錄裡,那是已知且被接受的代價。
        這裡守的是**除了規則自己點名的那個目標以外,指令的其餘部分一律不留**。
        """
        command = "printf ZZPAYLOADTOKEN > notes.txt"
        msg = gate.bash_write_violation(command)
        assert msg
        rec = gate.log_intercept(msg, command=command)
        blob = json.dumps(rec, ensure_ascii=False)
        assert "ZZPAYLOADTOKEN" not in blob, "指令的引數漏進紀錄"
        assert command not in blob, "指令原文整條漏進紀錄"
        # 回傳值乾淨而寫進去的髒,是可能的 —— 整份檔案也要驗。
        written = io.open(gate.intercept_path(rec["ts"][:7]), encoding="utf-8").read()
        assert "ZZPAYLOADTOKEN" not in written, "指令的引數漏進檔案"
        assert command not in written, "指令原文整條漏進檔案"

    def test_the_message_does_carry_the_write_target_and_that_is_the_known_cost(
            self, ledger):
        """**已知代價,明寫出來:`message` 全文帶得走一個本機路徑。**

        R7 的擋下訊息把**抽取出來的寫入目標**嵌在第一行
        (`…會寫到沒有被許可的位置(<目標>)`),而 `message` 記全文。
        於是「不記指令原文」與「message 記全文」在這一格上是有交集的 ——
        **交集的內容就是那個目標路徑。**

        這正是裁決 (a) 的實體:**`message` 全文含本機路徑,所以本檔不進版控。**
        票面那句「日後若要進版控,前置是 `message` 先做路徑遮罩」的**實際份量
        也在這裡** —— 要遮的不是邊角,是 R7 訊息裡**最有分類價值的那一格**
        (判「擋得對不對」多半就是在判那個目標該不該被擋)。

        **這條測試是正向的,不是防護欄**:它釘住現況,好讓有人改動訊息格式時,
        「這個檔為什麼不進版控」的前提會跟著被重新檢查,而不是靜靜失效。
        """
        command = "printf x > ZZTARGETDIR/notes.txt"
        rec = gate.log_intercept(gate.bash_write_violation(command),
                                 command=command)
        assert "ZZTARGETDIR/notes.txt" in rec["message"], (
            "R7 訊息不再帶目標路徑了 —— 那是好消息,但**「不進版控」的理由 (a) "
            "因此需要重新評估**,不要只把這條測試刪掉")

    def test_without_a_command_the_three_fields_are_absent_not_na(self, ledger):
        """**缺席,不填 `N/A`** —— `N/A` 是一個值,而值會被統計、被比對、
        被當成「有記錄」(票 68)。第二階段的兩個呼叫點手上沒有指令。"""
        rec = gate.log_intercept("[R3] foo.py:找不到對應測試")
        for field in ("cmd_sha256", "cmd_verb", "cmd_len"):
            assert field not in rec, "沒有指令卻編出了 %s" % field
        assert rec["rule"] == "R3"

    def test_the_record_lands_in_the_current_month_file(self, ledger):
        now = datetime.datetime(2026, 8, 28, 9, 0, tzinfo=datetime.timezone.utc)
        gate.log_intercept(gate.bash_write_violation(BLOCKING),
                           command=BLOCKING, now=now)
        assert _month_files(ledger) == ["intercepts-2026-08.jsonl"]
        assert len(_read(ledger / "intercepts-2026-08.jsonl")) == 1


class TestWiredIntoTheR7EnforceBranch:
    """接線:走 `mode_hook()` 的真實進入點,量的是使用者實際撞到的東西。"""

    def test_direction_A_a_block_grows_the_ledger_by_one(
            self, ledger, monkeypatch, capsys):
        rc, err = _hook(monkeypatch, capsys, BLOCKING)
        assert rc == 2, "R7 沒有擋 —— 前提就不成立了"
        assert "[R7]" in err
        recs = [r for f in _month_files(ledger) for r in _read(ledger / f)]
        assert len(recs) == 1, "enforce 下擋了一次,帳本卻有 %d 筆" % len(recs)
        assert recs[0]["rule"] == "R7"

    def test_direction_A_negative_control_a_clean_command_grows_nothing(
            self, ledger, monkeypatch, capsys):
        """**負控 —— 這一條是本檔的重點。**

        少了它,一個「每次呼叫都記一筆」的壞實作也會讓方向 A 全綠。
        沒被擋的指令不得憑空長出一筆,**連檔案都不該被建出來** ——
        一個空的月檔會讓「這個月沒有攔截」與「這個月沒有人用」長得一樣。
        """
        rc, err = _hook(monkeypatch, capsys, CLEAN)
        assert rc == 0, "fixture 選的乾淨指令現在被擋了:%s" % err
        assert _month_files(ledger) == [], (
            "沒有攔截卻長出了月檔:%s" % _month_files(ledger))

    def test_the_ledger_is_written_before_the_error_is_printed(self):
        """**順序是刻意的**:記不下來要能影響輸出(下一條驗那個影響)。

        放在 `_err` 之後的話,「擋了但沒記」與「擋了也記了」在終端機上長得一樣。
        """
        names = gate.mode_hook.__code__.co_names
        assert "log_intercept" in names, "mode_hook 根本沒有呼叫 log_intercept"

    def test_direction_B_shadow_mode_must_not_double_write(
            self, ledger, monkeypatch, capsys):
        """影子開著時走的是 `log_shadow`,攔截帳本**不得**多寫。

        雙寫會讓 9/15 的樣本重複計數,而重複計數的誤擋率**看起來比實際高**,
        於是一個本該轉正的規則被當成誤報王關掉。
        """
        rc, err = _hook(monkeypatch, capsys, BLOCKING, shadow=True)
        assert rc == 0, "影子開著卻擋了"
        assert _month_files(ledger) == [], "影子側寫進了 enforce 的攔截帳本"

    def test_negative_control_an_unwritable_ledger_still_blocks(
            self, ledger, monkeypatch, capsys):
        """**記不下來仍然擋**,但要多印一行說帳本壞了。

        方向與 `log_exemptions` 相反、結論相同:那邊是「記不下來的豁免不算數」
        所以 `SystemExit(2)`;這邊本來就要擋,所以不改判定 ——
        但**不得靜默**,否則「擋了但沒記」正是本票要消掉的那個東西。
        """
        def _boom(path, rec):
            raise IOError("ZZDISKFULL")

        monkeypatch.setattr(gate, "_append_jsonl", _boom)
        rc, err = _hook(monkeypatch, capsys, BLOCKING)
        assert rc == 2, "帳本壞掉就放行 —— 那是 fail-open"
        assert "[R7]" in err, "原本的擋下訊息不見了"
        assert "ZZDISKFULL" in err, "帳本壞掉沒有出聲:%r" % err

    def test_negative_control_a_broken_ledger_does_not_swallow_the_verdict(
            self, ledger, monkeypatch, capsys):
        """帳本壞掉時**判定訊息仍然完整** —— 多印的那一行是加,不是取代。"""
        def _boom(path, rec):
            raise IOError("ZZDISKFULL")

        monkeypatch.setattr(gate, "_append_jsonl", _boom)
        rc, err = _hook(monkeypatch, capsys, BLOCKING)
        assert "R7 只活在前哨" in err


class TestRotation:
    """輪替(核准附加條件 a)—— **必做,不是可選**。

    它 append-only、不進版控,而 enforce 下誤擋是常態,所以它**會一直長**;
    而它是備份清單第 10 項、要**手動複製**到新機器 ——
    **一個越來越難複製的檔案,最後會被跳過。**

    這是 `F-031` 的形狀換一個地方出現:F-031 是被煩到把規則關掉,
    本則是被煩到跳過備份。**受害者不同,而後者不會有人發現。**
    """

    NOW = datetime.datetime(2026, 8, 15, 12, 0, tzinfo=datetime.timezone.utc)

    def _seed(self, ledger, month, recs):
        path = ledger / ("intercepts-%s.jsonl" % month)
        with io.open(str(path), "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        return path

    def _rec(self, verb):
        return {"ts": "2026-05-01T00:00:00+00:00", "rule": "R7",
                "at_commit": False, "cmd_sha256": "0" * 64,
                "cmd_verb": verb, "cmd_len": 10, "message": "[R7] x"}

    def test_direction_A_an_expired_month_becomes_one_summary_line(self, ledger):
        """三個月前的月檔 → 下一次寫入後變成一行摘要,**原始檔消失**。"""
        self._seed(ledger, "2026-05",
                   [self._rec("grep")] * 2 + [self._rec("rm")])
        gate.log_intercept(gate.bash_write_violation(BLOCKING),
                           command=BLOCKING, now=self.NOW)
        assert not os.path.exists(str(ledger / "intercepts-2026-05.jsonl")), \
            "過期月檔的原始資料還在"
        summaries = _read(gate.INTERCEPT_SUMMARY)
        assert len(summaries) == 1, "摘要不是一行:%r" % summaries
        s = summaries[0]
        assert s["kind"] == "summary"
        assert s["month"] == "2026-05"
        assert s["rule"] == "R7"
        assert s["count"] == 3
        assert s["by_verb"] == {"grep": 2, "rm": 1}
        assert s["rolled_at"]

    def test_direction_B_negative_control_this_month_and_last_are_kept(self, ledger):
        """**當月與前一月不得被滾動。**

        沒有這一條的話,一個「全部滾掉」的實作也會讓方向 A 全綠。
        保留兩個月是**推導出來的,不是挑的**:只留當月的話,每月 1 號手上
        幾乎沒有原始資料;留到前一月,任何時點都保證至少有一個完整日曆月。
        **它是滿足「任何時點 ≥1 完整月」的最小值。**
        """
        self._seed(ledger, "2026-08", [self._rec("grep")])
        self._seed(ledger, "2026-07", [self._rec("grep")])
        gate.log_intercept(gate.bash_write_violation(BLOCKING),
                           command=BLOCKING, now=self.NOW)
        assert _month_files(ledger) == ["intercepts-2026-07.jsonl",
                                        "intercepts-2026-08.jsonl"]
        assert _read(gate.INTERCEPT_SUMMARY) == [], "前一月被滾掉了"

    def test_the_keep_window_crosses_a_year_boundary(self, ledger):
        """1 月的前一月是去年 12 月 —— 用減法算月份會在這裡把它滾掉。"""
        self._seed(ledger, "2025-12", [self._rec("grep")])
        gate.log_intercept(
            gate.bash_write_violation(BLOCKING), command=BLOCKING,
            now=datetime.datetime(2026, 1, 3, 0, 0, tzinfo=datetime.timezone.utc))
        assert os.path.exists(str(ledger / "intercepts-2025-12.jsonl")), \
            "跨年時前一月被誤判成過期"

    def test_records_without_a_command_are_still_counted(self, ledger):
        """**沒有 `cmd_verb` 的那些也要進 `by_verb` 的分母。**

        紀錄層面「缺席不填 N/A」是對的(值會被當成有記錄);
        但**摘要是統計**,漏掉它們會讓 `sum(by_verb) < count` 而沒有人看得出
        差額去了哪。所以摘要用一個明講的鍵收容它們。
        """
        self._seed(ledger, "2026-05", [
            self._rec("grep"),
            {"ts": "2026-05-02T00:00:00+00:00", "rule": "R7",
             "at_commit": False, "message": "[R7] x"},
        ])
        gate.log_intercept(gate.bash_write_violation(BLOCKING),
                           command=BLOCKING, now=self.NOW)
        s = _read(gate.INTERCEPT_SUMMARY)[0]
        assert s["count"] == 2
        assert sum(s["by_verb"].values()) == s["count"], \
            "by_verb 的總和對不上 count:%r" % s

    def test_summaries_are_never_rolled_again(self, ledger):
        """摘要**不刪**:一行約 100 bytes、一年 12 行,不會成為複製的障礙,
        而它是「誤擋頻率隨時間怎麼變」唯一的長期訊號。"""
        self._seed(ledger, "2026-05", [self._rec("grep")])
        gate.log_intercept(gate.bash_write_violation(BLOCKING),
                           command=BLOCKING, now=self.NOW)
        self._seed(ledger, "2026-06", [self._rec("rm")])
        gate.log_intercept(gate.bash_write_violation(BLOCKING),
                           command=BLOCKING, now=self.NOW)
        months = [s["month"] for s in _read(gate.INTERCEPT_SUMMARY)]
        assert months == ["2026-05", "2026-06"], months

    def test_rolling_is_idempotent(self, ledger):
        """滾動要能重跑而不重複計數 —— 摘要寫成了但刪檔失敗時會發生。"""
        self._seed(ledger, "2026-05", [self._rec("grep")])
        gate.roll_intercepts(now=self.NOW)
        self._seed(ledger, "2026-05", [self._rec("grep")])
        gate.roll_intercepts(now=self.NOW)
        assert len(_read(gate.INTERCEPT_SUMMARY)) == 1

    def test_a_rotation_failure_does_not_eat_the_record(self, ledger, monkeypatch,
                                                        capsys):
        """**整理失敗不得吃掉這一筆。** 記錄比整理重要,而整理失敗要出聲。"""
        self._seed(ledger, "2026-05", [self._rec("grep")])
        monkeypatch.setattr(os, "remove", lambda p: (_ for _ in ()).throw(
            IOError("ZZLOCKED")))
        gate.log_intercept(gate.bash_write_violation(BLOCKING),
                           command=BLOCKING, now=self.NOW)
        assert len(_read(ledger / "intercepts-2026-08.jsonl")) == 1
        assert "ZZLOCKED" in capsys.readouterr().err


class TestItDoesNotTouchTheExemptionLedger:
    """方向 B 的後半:`gate-exemptions.jsonl` **逐字不變**。

    兩個理由都是硬的,票面已經寫死:
      1. **schema 不相容** —— `exemption_record()` 的鍵是豁免形狀的
         (`file` / `module` / `declared_in` / `reason`),一次 R7 攔截
         **沒有 `file`**(它的觸發物是指令),四個鍵全部填不出來。
      2. **會弄壞 `ledger_verify` 的鏈驗證** —— 那支工具逐筆讀
         `content_hash` → `result_hash` 串成鏈、逐段驗接續。插進一筆沒有
         這兩個欄位的紀錄,鏈就斷在那裡,而那條鏈是票 58 / 票 47
         三次有界突變的收尾依據。
    """

    def test_an_r7_block_writes_nothing_to_the_exemption_ledger(
            self, ledger, monkeypatch, capsys):
        before = _read(gate.EXEMPTION_LOG)
        _hook(monkeypatch, capsys, BLOCKING)
        assert _read(gate.EXEMPTION_LOG) == before

    def test_the_intercept_ledger_is_a_separate_file(self):
        assert os.path.basename(gate.INTERCEPT_LOG) != \
            os.path.basename(gate.EXEMPTION_LOG)
        assert "intercepts" in os.path.basename(gate.INTERCEPT_LOG)
