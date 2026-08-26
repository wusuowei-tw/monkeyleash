# -*- coding: utf-8 -*-
"""票 63 —— `shadow_review` 不得把讀取失敗偽裝成空日誌。

## 這個檔案守的三件事

    1. 帶 BOM 的日誌要**全部讀到**            (utf-8-sig)
    2. 壞行要**大聲失敗**,不回部分也不回空    (出聲失敗)
    3. 重寫前筆數要守恆                       (第二道保險,負控釘著)

## 為什麼 1 與 2 必須成對(非空洞性)

    只有 1  -> 一支「讀得懂 BOM 但仍吞壞行」的實作**全綠**
    只有 2  -> 一支「壞行就炸但不處理 BOM」的實作**全綠**

> **兩條合起來,才排除得掉「因為錯的理由而通過」(F-103)。**

## 為什麼 3 需要負控

修好之後 `load_log` 要嘛回全部、要嘛丟例外,所以 2 與 3 在**當下**等價 ——
而那正是為什麼 3 需要一條把 `load_log` 換掉的測試:
**一個從未被走到的 fail-closed 分支,會在它前面那個分支被拿掉的當天才現形**
(票 42 的判準句)。負控直接製造「第一道不存在」的世界,讓第三道自己說話。

## 一律用 tmp_path,不碰真實帳本

`.dev/shadow-log.jsonl` 是**證據**。測試碰它就等於讓「跑測試」變成
「改證據」,而那是票 18 已經定案的事。
"""
import importlib.util
import io
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "shadow_review_under_test", ROOT / ".claude" / "portable" / "shadow_review.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sr = _load()


def _rec(rule, classification=None):
    r = {"ts": "2026-08-19T00:00:00+00:00", "rule": rule, "message": "x"}
    if classification:
        r["classification"] = classification
    return r


def _write(path, records, bom=False, encoding="utf-8", extra_lines=()):
    """寫一份日誌。**BOM 用位元組寫**,不靠編碼器的副作用 ——
    `encoding="utf-8-sig"` 會自己加 BOM,但那樣測試就依賴了
    「寫的那一端也用同一個編碼名」,而生產環境的 BOM 是**別的工具**留下的。
    """
    body = u""
    for r in records:
        body += json.dumps(r, ensure_ascii=False) + u"\n"
    for line in extra_lines:
        body += line + u"\n"
    raw = body.encode(encoding)
    if bom:
        raw = b"\xef\xbb\xbf" + raw
    with io.open(str(path), "wb") as f:
        f.write(raw)
    return path


class TestABomIsNotAnEmptyLog:
    """**哪一個 repo 狀態確定會讓這條紅**:日誌檔首位元組是 `EF BB BF`
    而 `load_log` 用 `encoding="utf-8"` 開檔 —— 第一行變 `\\ufeff{...}`,
    `json.loads` 丟例外,舊實作 `except: pass` 回 `[]`。
    """

    def test_every_record_is_read_from_a_bom_prefixed_log(self, tmp_path):
        recs = [_rec("R7", "真陽") for _ in range(12)]
        p = _write(tmp_path / "shadow-log.jsonl", recs, bom=True)
        assert len(sr.load_log(str(p))) == 12

    def test_the_first_record_is_not_mangled_by_the_bom(self, tmp_path):
        """**不只是數量對** —— BOM 若被當成鍵名的一部分留下來,
        筆數會對而 `rule` 欄位是 `\\ufeffts` 那種東西。
        數量斷言單獨用抓不到它。"""
        p = _write(tmp_path / "shadow-log.jsonl", [_rec("R2", "真陽")], bom=True)
        rows = sr.load_log(str(p))
        assert rows[0]["rule"] == "R2"
        assert "ts" in rows[0]
        assert not any(k.startswith(u"﻿") for k in rows[0])

    def test_promotion_status_counts_a_bom_prefixed_log(self, tmp_path):
        """端到端:讀取那一層修好了,晉升判定才拿得到分母。"""
        recs = [_rec("R7", "真陽") for _ in range(11)]
        p = _write(tmp_path / "shadow-log.jsonl", recs, bom=True)
        per = sr.promotion_status(str(p))
        assert per["R7"]["classified"] == 11

    def test_a_log_without_a_bom_still_works(self, tmp_path):
        """**負控**:改用 `utf-8-sig` 不能把沒有 BOM 的檔弄壞。
        少了這條,一支只認 BOM 檔的實作也會全綠。"""
        recs = [_rec("R3", "假陽/範圍") for _ in range(4)]
        p = _write(tmp_path / "shadow-log.jsonl", recs, bom=False)
        assert len(sr.load_log(str(p))) == 4


class TestBABadLineIsLoudNotSilent:
    """**哪一個 repo 狀態確定會讓這條紅**:日誌中間有一行不是合法 JSON
    (人工還原、編輯器截斷、磁碟寫一半)。舊實作靜默回前 k-1 筆。
    """

    def test_a_malformed_line_raises_instead_of_returning_a_short_list(self, tmp_path):
        recs = [_rec("R7", "真陽") for _ in range(50)]
        p = _write(tmp_path / "shadow-log.jsonl", recs,
                   extra_lines=[u"{壞掉的不是 JSON", ])
        with pytest.raises(sr.ShadowLogError):
            sr.load_log(str(p))

    def test_the_message_names_the_line_number(self, tmp_path):
        """**訊息要說出是哪一行** —— 只說「壞了」的話,人得自己去找,
        而 222 行的檔案沒有人會逐行找(票 13 的判準)。"""
        recs = [_rec("R7", "真陽") for _ in range(3)]
        p = _write(tmp_path / "shadow-log.jsonl", recs,
                   extra_lines=[u"NOT JSON"])
        with pytest.raises(sr.ShadowLogError) as e:
            sr.load_log(str(p))
        assert "4" in str(e.value)

    def test_a_missing_file_is_also_loud(self, tmp_path):
        """**「檔案不在」與「日誌是空的」也是兩件事。**
        舊實作對兩者都回 `[]`。"""
        with pytest.raises(sr.ShadowLogError):
            sr.load_log(str(tmp_path / "does-not-exist.jsonl"))

    def test_a_genuinely_empty_log_is_not_an_error(self, tmp_path):
        """**負控,而且是這一組最要緊的一條**:修法不能把
        「真的沒東西」也變成錯誤 —— 那會把一個假陰換成一個假陽,
        而本票的全部主張就是**這兩件事要分得開**。"""
        p = _write(tmp_path / "shadow-log.jsonl", [])
        assert sr.load_log(str(p)) == []

    def test_blank_lines_are_still_skipped(self, tmp_path):
        """空白行不是壞行 —— 舊行為要保住,否則尾端換行會變成錯誤。"""
        recs = [_rec("R2", "真陽")]
        p = _write(tmp_path / "shadow-log.jsonl", recs,
                   extra_lines=[u"", u"   ", u""])
        assert len(sr.load_log(str(p))) == 1


class TestCRewriteRefusesToLoseRecords:
    """**第二道保險的負控。**

    修好之後 `load_log` 不會回截斷清單,所以這一格在正常世界裡走不到 ——
    測試因此**直接製造那個世界**:把 `load_log` 換成回截斷清單的假貨,
    再要求 `review()` 拒絕寫入。

    **這不是在測 monkeypatch 出來的假象**:守的是
    「重寫那一行不准在筆數少掉時執行」,而那個性質與 `load_log` 怎麼實作無關。
    """

    def test_review_refuses_to_rewrite_when_records_went_missing(
            self, tmp_path, monkeypatch):
        recs = [_rec("R7") for _ in range(10)]          # 全部未分類
        p = _write(tmp_path / "shadow-log.jsonl", recs)
        before = io.open(str(p), "rb").read()

        monkeypatch.setattr(sr, "load_log", lambda _p: [dict(r) for r in recs[:4]])
        monkeypatch.setattr(sr, "input", lambda _prompt: "1", raising=False)

        with pytest.raises(sr.ShadowLogError):
            sr.review(str(p))

        assert io.open(str(p), "rb").read() == before, \
            "拒絕之後檔案必須逐位元組不變 —— 拒絕但已經寫了一半,比不拒絕更糟"

    def test_the_guard_is_not_vacuous(self, tmp_path, monkeypatch):
        """**非空洞性**:同樣的路徑,筆數**沒有**少掉時必須寫得成功。
        少了這條,一支「`review()` 永遠丟例外」的實作也會讓上一條全綠。"""
        recs = [_rec("R7") for _ in range(3)]
        p = _write(tmp_path / "shadow-log.jsonl", recs)

        monkeypatch.setattr(sr, "input", lambda _prompt: "1", raising=False)
        sr.review(str(p))

        rows = sr.load_log(str(p))
        assert len(rows) == 3
        assert all(r.get("classification") == "真陽" for r in rows)


class TestDStatusSeparatesEmptyFromUnclassified:
    """**同一個病在上一層又出現一次。**

    `load_log` 修好之後,量化那 222 筆讀得到了 —— 但它們**全部尚未分類**,
    所以 `promotion_status` 回空 dict,而 `print_status` 對空 dict 印的是

        「還沒有任何已分類的影子日誌。先跑一輪互動分類。」

    **與壞掉時逐字相同。** 於是修好與沒修好,從輸出上分不出來 ——
    連本票自己的驗收條件(「量化驗 --status 讀得到 222 筆」)都驗不了。

    > **`load_log` 那一層分開了「讀不到」與「空的」;
    > 這一層還壓著「讀到了但沒分類」與「什麼都沒讀到」。**

    處置:狀態一律先報**讀到幾筆**,再報分類情形。讀到的筆數是
    這支工具唯一能證明「我真的看到資料了」的東西。
    """

    def test_status_reports_how_many_records_were_read(self, tmp_path, capsys):
        recs = [_rec("R7") for _ in range(222)]          # 全部未分類
        p = _write(tmp_path / "shadow-log.jsonl", recs)
        sr.print_status(str(p))
        assert "222" in capsys.readouterr().out

    def test_an_unclassified_log_is_not_described_as_having_nothing(
            self, tmp_path, capsys):
        """**讀到 222 筆但 0 筆已分類**,與**檔案裡什麼都沒有**,
        必須是兩段不同的話。"""
        p = _write(tmp_path / "shadow-log.jsonl", [_rec("R7") for _ in range(5)])
        sr.print_status(str(p))
        unclassified_out = capsys.readouterr().out

        p2 = _write(tmp_path / "empty.jsonl", [])
        sr.print_status(str(p2))
        empty_out = capsys.readouterr().out

        assert unclassified_out != empty_out

    def test_a_truly_empty_log_says_so(self, tmp_path, capsys):
        """負控:別把「真的是空的」也講成「有資料」。"""
        p = _write(tmp_path / "shadow-log.jsonl", [])
        sr.print_status(str(p))
        assert "0" in capsys.readouterr().out

    def test_status_still_prints_the_per_rule_table_when_there_are_classifications(
            self, tmp_path, capsys):
        """負控:加了「讀到幾筆」不能把原本的晉升表擠掉。"""
        recs = [_rec("R7", "真陽") for _ in range(11)]
        p = _write(tmp_path / "shadow-log.jsonl", recs)
        sr.print_status(str(p))
        out = capsys.readouterr().out
        assert "R7" in out
        assert "11" in out


class TestFRecordIdentityIsBoundToContent:
    """票 64 約束 1:識別唯一綁定。

    **`ts` 在生產資料上已經撞號**(量化 222 筆:221 相異,1 組撞號涉及 2 筆),
    所以身分不能是時間戳,也不能是行號或順序。
    """

    def test_two_records_differing_only_in_message_get_different_ids(self):
        a = {"ts": "T", "rule": "R7", "message": "x"}
        b = {"ts": "T", "rule": "R7", "message": "y"}
        assert sr.record_id(a) != sr.record_id(b)

    def test_the_same_timestamp_and_rule_do_not_collide(self):
        """直接對著生產資料撞到的那一組形狀。"""
        a = {"ts": "T", "rule": "R7", "message": "a", "verdict": "block"}
        b = {"ts": "T", "rule": "R7", "message": "b", "verdict": "block"}
        assert sr.record_id(a) != sr.record_id(b)

    def test_key_order_does_not_change_the_id(self):
        a = {"ts": "T", "rule": "R7", "message": "x"}
        b = {"message": "x", "rule": "R7", "ts": "T"}
        assert sr.record_id(a) == sr.record_id(b)

    def test_classification_is_excluded_from_the_identity(self):
        """**套用前後身分必須不變** —— 否則卡片套完就再也指不回它動過的東西,
        而留檔會變成留一份指不回去的紙。"""
        a = {"ts": "T", "rule": "R7", "message": "x"}
        b = dict(a, classification="真陽")
        assert sr.record_id(a) == sr.record_id(b)


class TestGCardIsDryRunByDefault:
    """票 64 約束 3。"""

    def _log_and_card(self, tmp_path, n=5, klass="1"):
        recs = [_rec("R7") for _ in range(n)]
        for i, r in enumerate(recs):
            r["message"] = "m%d" % i
        log = _write(tmp_path / "shadow-log.jsonl", recs)
        card = tmp_path / "card.jsonl"
        with io.open(str(card), "w", encoding="utf-8", newline="\n") as f:
            for r in recs:
                f.write(json.dumps({"id": sr.record_id(r)[:16],
                                    "class": klass,
                                    "why": "測試"}, ensure_ascii=False) + "\n")
        return log, card

    def test_plan_does_not_touch_the_log(self, tmp_path):
        log, card = self._log_and_card(tmp_path)
        before = io.open(str(log), "rb").read()
        sr.apply_card(str(log), str(card), apply=False)
        assert io.open(str(log), "rb").read() == before

    def test_plan_reports_counts_per_class(self, tmp_path):
        log, card = self._log_and_card(tmp_path, n=7, klass="5")
        plan = sr.apply_card(str(log), str(card), apply=False)
        assert plan.by_class == {"5": 7}
        assert plan.applied == 0          # dry-run 沒有套用任何東西

    def test_apply_writes_and_reports(self, tmp_path):
        log, card = self._log_and_card(tmp_path, n=3, klass="1")
        plan = sr.apply_card(str(log), str(card), apply=True)
        assert plan.applied == 3
        rows = sr.load_log(str(log))
        assert [r["classification"] for r in rows] == ["真陽"] * 3

    def test_the_untouched_fields_survive_the_rewrite(self, tmp_path):
        """套用只加 `classification`,不動別的欄位。"""
        log, card = self._log_and_card(tmp_path, n=2)
        before = sr.load_log(str(log))
        sr.apply_card(str(log), str(card), apply=True)
        after = sr.load_log(str(log))
        for b, a in zip(before, after):
            for k in b:
                assert a[k] == b[k]


class TestHAllOrNothing:
    """票 64 約束 2 與 5:任一條件不滿足 -> 整批拒絕,檔案逐位元組不變。"""

    def _setup(self, tmp_path, card_lines, n=4):
        recs = [_rec("R7") for _ in range(n)]
        for i, r in enumerate(recs):
            r["message"] = "m%d" % i
        log = _write(tmp_path / "shadow-log.jsonl", recs)
        card = tmp_path / "card.jsonl"
        with io.open(str(card), "w", encoding="utf-8", newline="\n") as f:
            for line in card_lines(recs):
                f.write(json.dumps(line, ensure_ascii=False) + "\n")
        return log, card, recs

    def _refuses(self, log, card):
        before = io.open(str(log), "rb").read()
        with pytest.raises(sr.ShadowLogError) as e:
            sr.apply_card(str(log), str(card), apply=True)
        assert io.open(str(log), "rb").read() == before, \
            "拒絕之後檔案必須逐位元組不變 —— 拒絕但已寫了一半,比不拒絕更糟"
        return str(e.value)

    def test_an_unknown_id_refuses_the_whole_batch(self, tmp_path):
        log, card, recs = self._setup(tmp_path, lambda rs: [
            {"id": sr.record_id(rs[0])[:16], "class": "1", "why": "ok"},
            {"id": "0" * 16, "class": "1", "why": "指不到任何一筆"},
        ])
        assert "0000" in self._refuses(log, card)

    def test_a_duplicate_id_in_the_card_refuses(self, tmp_path):
        log, card, recs = self._setup(tmp_path, lambda rs: [
            {"id": sr.record_id(rs[0])[:16], "class": "1", "why": "一"},
            {"id": sr.record_id(rs[0])[:16], "class": "5", "why": "二"},
        ])
        assert "重複" in self._refuses(log, card)

    def test_a_duplicate_record_in_the_log_refuses(self, tmp_path):
        """**日誌自己撞號** —— 卡片指過去會指到兩筆,而「套哪一筆」
        不是工具能決定的。"""
        r = _rec("R7")
        log = _write(tmp_path / "shadow-log.jsonl", [dict(r), dict(r)])
        card = tmp_path / "card.jsonl"
        with io.open(str(card), "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps({"id": sr.record_id(r)[:16], "class": "1",
                                "why": "x"}, ensure_ascii=False) + "\n")
        assert "重複" in self._refuses(log, card)

    def test_an_unknown_class_refuses(self, tmp_path):
        log, card, recs = self._setup(tmp_path, lambda rs: [
            {"id": sr.record_id(rs[0])[:16], "class": "9", "why": "沒有第 9 類"},
        ])
        assert "9" in self._refuses(log, card)

    def test_a_missing_why_refuses(self, tmp_path):
        log, card, recs = self._setup(tmp_path, lambda rs: [
            {"id": sr.record_id(rs[0])[:16], "class": "1"},
        ])
        assert "why" in self._refuses(log, card)

    def test_an_already_classified_record_refuses(self, tmp_path):
        r = _rec("R7", "真陽")
        log = _write(tmp_path / "shadow-log.jsonl", [r])
        card = tmp_path / "card.jsonl"
        with io.open(str(card), "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps({"id": sr.record_id(r)[:16], "class": "5",
                                "why": "想覆蓋"}, ensure_ascii=False) + "\n")
        assert "已" in self._refuses(log, card)

    def test_dry_run_refuses_for_the_same_reasons(self, tmp_path):
        """**dry-run 也要擋。** 一份把不合法的卡列成「將套用」的清單,
        本身就是錯的答案(同 sync 的 refuse_if_unclassified)。"""
        log, card, recs = self._setup(tmp_path, lambda rs: [
            {"id": "0" * 16, "class": "1", "why": "指不到"},
        ])
        with pytest.raises(sr.ShadowLogError):
            sr.apply_card(str(log), str(card), apply=False)

    def test_a_valid_card_is_not_refused(self, tmp_path):
        """**非空洞性**:一支「永遠拒絕」的實作會讓上面每一條全綠。"""
        log, card, recs = self._setup(tmp_path, lambda rs: [
            {"id": sr.record_id(rs[0])[:16], "class": "1", "why": "ok"},
        ])
        plan = sr.apply_card(str(log), str(card), apply=True)
        assert plan.applied == 1


class TestICardIsKeptOnRecord:
    """票 64 約束 4:套用卡留檔。"""

    def _apply(self, tmp_path):
        recs = [_rec("R7"), _rec("R3")]
        for i, r in enumerate(recs):
            r["message"] = "m%d" % i
        log = _write(tmp_path / "shadow-log.jsonl", recs)
        card = tmp_path / "card.jsonl"
        with io.open(str(card), "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps({"id": sr.record_id(recs[0])[:16], "class": "1",
                                "why": "a"}, ensure_ascii=False) + "\n")
            f.write(json.dumps({"id": sr.record_id(recs[1])[:16], "class": "5",
                                "why": "b"}, ensure_ascii=False) + "\n")
        return log, card

    def test_applying_appends_a_ledger_record(self, tmp_path):
        log, card = self._apply(tmp_path)
        sr.apply_card(str(log), str(card), apply=True)
        ledger = tmp_path / "shadow-cards.jsonl"
        assert ledger.exists()
        rec = json.loads(io.open(str(ledger), encoding="utf-8").read().strip())
        assert rec["applied"] == 2
        assert rec["by_class"] == {"1": 1, "5": 1}

    def test_the_ledger_records_the_card_fingerprint(self, tmp_path):
        """**指紋要能被獨立查證** —— 事後有人可以拿卡片重算一次。
        同 provenance 的判準:寫下來的東西不得只能自我背書。"""
        log, card = self._apply(tmp_path)
        sr.apply_card(str(log), str(card), apply=True)
        rec = json.loads(io.open(str(tmp_path / "shadow-cards.jsonl"),
                                 encoding="utf-8").read().strip())
        import hashlib
        expect = hashlib.sha256(io.open(str(card), "rb").read()).hexdigest()
        assert rec["card_sha256"] == expect

    def test_dry_run_writes_no_ledger_record(self, tmp_path):
        log, card = self._apply(tmp_path)
        sr.apply_card(str(log), str(card), apply=False)
        assert not (tmp_path / "shadow-cards.jsonl").exists()

    def test_a_refused_apply_writes_no_ledger_record(self, tmp_path):
        """**驗證沒過就不該有憑證** —— 否則帳面上會出現一張替沒發生的
        套用背書的紀錄(同 sync:provenance 在 hash 重驗之後才寫)。"""
        recs = [_rec("R7")]
        log = _write(tmp_path / "shadow-log.jsonl", recs)
        card = tmp_path / "card.jsonl"
        with io.open(str(card), "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps({"id": "0" * 16, "class": "1", "why": "指不到"},
                               ensure_ascii=False) + "\n")
        with pytest.raises(sr.ShadowLogError):
            sr.apply_card(str(log), str(card), apply=True)
        assert not (tmp_path / "shadow-cards.jsonl").exists()


class TestJDeliberateRefuseIsItsOwnBucket:
    """票 65 —— 「刻意 refuse」不是假陽,也不是真陽。

    **哪一個 repo 狀態確定會讓這條紅**:五類的工具遇到一筆 fail-closed
    保守觸發,按 `1` 會把刻意成本算成真陽、按 `5` 會把規則的正確行為算成誤判,
    而兩者對同一批資料給出相反的假陽率(ADR 0012 §2:R7 202 筆
    在五類公式下 FP > 80%,三分類下 6.9–11.9%)。

    判準(上游票 21 的既有裁決,非新裁):
    **fail-closed 保守觸發是規則照設計動作** —— 成本是真的、要算進分母,
    但它不是誤判。把它算成假陽,等於要求一條 fail-closed 規則
    證明自己從不 fail-closed。
    """

    def test_the_sixth_class_exists(self):
        assert "6" in sr.CLASSES
        assert "refuse" in sr.CLASSES["6"] or "刻意" in sr.CLASSES["6"]

    def test_deliberate_refuse_is_not_a_false_positive(self):
        assert not sr._is_false_positive(sr.CLASSES["6"])

    def test_deliberate_refuse_still_counts_in_the_denominator(self, tmp_path):
        """**成本是真的,要算進分母。** 不計分母的話,一條規則只要
        大量 fail-closed 就能把自己的假陽率稀釋掉。"""
        recs = ([_rec("R7", sr.CLASSES["6"]) for _ in range(9)]
                + [_rec("R7", "假陽/範圍")])
        p = _write(tmp_path / "shadow-log.jsonl", recs)
        per = sr.promotion_status(str(p))
        assert per["R7"]["classified"] == 10
        assert per["R7"]["false_positives"] == 1
        assert abs(per["R7"]["fp_rate"] - 0.1) < 1e-9

    def test_the_two_readings_of_the_same_data_now_agree(self, tmp_path):
        """五類時代的病:同一批資料按 `1` 或按 `5` 給出相反的 FP。
        補桶之後,fail-closed 保守觸發有自己的鍵,不必二選一。"""
        recs = [_rec("R7", sr.CLASSES["6"]) for _ in range(10)]
        p = _write(tmp_path / "shadow-log.jsonl", recs)
        per = sr.promotion_status(str(p))
        assert per["R7"]["false_positives"] == 0
        assert per["R7"]["deliberate"] == 10


class TestKClassSemanticsAreNotCarriedByAStringPrefix:
    """**這一組比加桶重要。**

    `_is_false_positive()` 原本是 `classification.startswith("假陽")` ——
    **分類語意藏在中文字串的前兩個字裡**。任何人把「假陽/範圍」改名成
    「範圍誤判」,假陽率會**當場歸零而且全綠**。

    分類集合是**封閉且可窮舉**的,而
    **封閉集合用枚舉勝過比對** —— 比對的漏是未知的,枚舉的漏是不存在的。
    """

    def test_the_false_positive_set_is_explicit(self):
        assert isinstance(sr.FALSE_POSITIVE_CLASSES, (set, frozenset))
        assert sr.FALSE_POSITIVE_CLASSES == {
            sr.CLASSES["2"], sr.CLASSES["3"], sr.CLASSES["4"], sr.CLASSES["5"]}

    def test_a_class_not_starting_with_the_prefix_can_still_be_a_false_positive(self):
        """反向釘子:判定不得**依賴**那個前綴。
        這裡直接問集合,若實作退回 startswith,這條仍會綠 ——
        所以它的搭檔是下一條。"""
        for name in sr.FALSE_POSITIVE_CLASSES:
            assert sr._is_false_positive(name)

    def test_an_unknown_classification_is_loud_not_silently_bucketed(self, tmp_path):
        """**正面釘死 startswith 那條路**:`假陽/沒登記過的` 在前綴實作下
        會被靜默算成假陽,在枚舉實作下不屬於任何桶。

        兩種靜默都不行 —— 一個高估、一個低估,而**兩者都印得出一個
        看起來權威的百分比**。所以:出聲。
        """
        p = _write(tmp_path / "shadow-log.jsonl",
                   [_rec("R7", "假陽/沒登記過的")])
        with pytest.raises(sr.ShadowLogError) as e:
            sr.promotion_status(str(p))
        assert "沒登記過的" in str(e.value)

    def test_the_known_classes_do_not_raise(self, tmp_path):
        """負控:一支「什麼都當未知」的實作會讓上一條全綠。"""
        recs = [_rec("R%d" % i, sr.CLASSES[k])
                for i, k in enumerate(sorted(sr.CLASSES), 1)]
        p = _write(tmp_path / "shadow-log.jsonl", recs)
        assert len(sr.promotion_status(str(p))) == len(sr.CLASSES)


class TestLStatusReportsTheThreeWaySplit:
    """票 65:`--status` 要說出三分類的三個數,不只印一個 FP。

    ADR 0012 §2 寫「三分類的真相以建議清單與評估報告為準,不以工具輸出為準」——
    那句話是**過渡期的但書**,而它存在的理由就是工具印不出三分類。
    印得出來之後,那句但書才拿得掉(拿掉要改下游 ADR,見票 66,不在本票)。
    """

    def test_status_shows_true_positive_deliberate_and_false_positive(
            self, tmp_path, capsys):
        recs = ([_rec("R7", "真陽") for _ in range(5)]
                + [_rec("R7", sr.CLASSES["6"]) for _ in range(3)]
                + [_rec("R7", "假陽/解析") for _ in range(2)])
        p = _write(tmp_path / "shadow-log.jsonl", recs)
        sr.print_status(str(p))
        out = capsys.readouterr().out
        assert "真陽" in out
        assert "refuse" in out or "刻意" in out
        for n in ("5", "3", "2"):
            assert n in out

    def test_the_rate_uses_the_full_denominator(self, tmp_path, capsys):
        """10 筆裡 1 筆誤報 -> 10.0%,不是「扣掉 refuse 之後的 1/7」。"""
        recs = ([_rec("R7", sr.CLASSES["6"]) for _ in range(3)]
                + [_rec("R7", "真陽") for _ in range(6)]
                + [_rec("R7", "假陽/時點")])
        p = _write(tmp_path / "shadow-log.jsonl", recs)
        sr.print_status(str(p))
        assert "10.0" in capsys.readouterr().out


class TestMUndecidableIsNeitherEvidenceNorFault:
    """票 67 —— 「無法判定」是**判定不能**,不是判定結果。

    由來:R7 202 筆裡有 72 筆從日誌本身判不出真陽/誤報,因為
    **日誌沒有記指令**(欄位只有 ts / rule / at_commit / verdict / message)。

    所以它既不進假陽率的分子,**也不進分母** ——
    把它算進分母會稀釋假陽率,算進分子會誣賴規則。
    """

    def test_the_seventh_class_exists(self):
        assert "7" in sr.CLASSES
        assert "無法判定" in sr.CLASSES["7"]

    def test_undecidable_is_not_a_false_positive(self):
        assert not sr._is_false_positive(sr.CLASSES["7"])

    def test_undecidable_is_excluded_from_the_rate_denominator(self, tmp_path):
        """**與刻意 refuse 的差別就在這一條。**

        5 筆誤報 + 5 筆無法判定:
          舊算法(分母 = 已分類)   -> 5/10 = 50%
          本票算法(分母 = 可判定) -> 5/5  = 100%
        """
        recs = ([_rec("R7", "假陽/解析") for _ in range(5)]
                + [_rec("R7", sr.CLASSES["7"]) for _ in range(5)])
        p = _write(tmp_path / "shadow-log.jsonl", recs)
        d = sr.promotion_status(str(p))["R7"]
        assert d["undecidable"] == 5
        assert d["decidable"] == 5
        assert abs(d["fp_rate"] - 1.0) < 1e-9

    def test_deliberate_refuse_stays_in_the_denominator(self, tmp_path):
        """負控:別把刻意 refuse 一起踢出分母。
        **成本是真的**(ADR 0012 §2),它算分母、只是不算分子。"""
        recs = ([_rec("R7", "假陽/解析")]
                + [_rec("R7", sr.CLASSES["6"]) for _ in range(9)])
        p = _write(tmp_path / "shadow-log.jsonl", recs)
        d = sr.promotion_status(str(p))["R7"]
        assert d["decidable"] == 10
        assert abs(d["fp_rate"] - 0.1) < 1e-9


class TestNDecidableRateIsAThirdGate:
    """票 67 —— 轉正要同時滿足三條:已分類 ≥ 10、假陽率 < 5%、**可判定率 ≥ 90%**。

    **哪一個 repo 狀態確定會讓這條紅**:量化 2026-08-19 的實況 ——
    R7 202 筆,130 筆標刻意 refuse、72 筆還沒判。
    舊判定只看「已分類 130 ≥ 10」與「假陽率 0.0% < 5%」,於是印出 `可轉正`。

    > **36% 判不出來的規則,它的 0% 假陽率不代表它準,
    > 只代表我們只看了它願意讓我們看的那部分。**
    """

    def test_the_real_world_case_is_not_promotable(self, tmp_path):
        """量化 2026-08-19 的實況:130 判定 / 72 未判定。"""
        recs = ([_rec("R7", sr.CLASSES["6"]) for _ in range(130)]
                + [_rec("R7") for _ in range(72)])
        for i, r in enumerate(recs):
            r["message"] = "m%d" % i
        p = _write(tmp_path / "shadow-log.jsonl", recs)
        d = sr.promotion_status(str(p))["R7"]
        assert d["total"] == 202
        assert d["classified"] == 130
        assert abs(d["decidable_rate"] - 130.0 / 202.0) < 1e-9
        assert d["decidable_rate"] < sr.MIN_DECIDABLE_RATE
        assert d["promotable"] is False, \
            "130/202 = 64% 可判定,不得可轉正 —— 誤報全在沒判的那 72 筆裡"

    def test_marking_the_remainder_undecidable_does_not_unlock_it(self, tmp_path):
        """**這一條釘住 (c) 那個漏。**

        把 72 筆全標「無法判定」之後,「已分類」變成 202/202 ——
        若可判定率沒有把無法判定排除在分子外,這裡就會變成可轉正,
        而那與「只印不擋」同結果。
        """
        recs = ([_rec("R7", sr.CLASSES["6"]) for _ in range(130)]
                + [_rec("R7", sr.CLASSES["7"]) for _ in range(72)])
        for i, r in enumerate(recs):
            r["message"] = "m%d" % i
        p = _write(tmp_path / "shadow-log.jsonl", recs)
        d = sr.promotion_status(str(p))["R7"]
        assert d["classified"] == 202
        assert d["undecidable"] == 72
        assert d["promotable"] is False

    def test_a_rule_meeting_all_three_is_promotable(self, tmp_path):
        """**非空洞性**:少了這條,一支「永遠回 False」的實作全綠。"""
        recs = [_rec("R2", sr.CLASSES["6"]) for _ in range(20)]
        for i, r in enumerate(recs):
            r["message"] = "m%d" % i
        p = _write(tmp_path / "shadow-log.jsonl", recs)
        d = sr.promotion_status(str(p))["R2"]
        assert d["decidable_rate"] == 1.0
        assert d["promotable"] is True

    def test_each_of_the_three_gates_can_veto_alone(self, tmp_path):
        """三條各自都要擋得住 —— 否則其中一條是裝飾。"""
        # 只差筆數:9 筆全可判定、零誤報
        recs = [dict(_rec("R3", sr.CLASSES["6"]), message="a%d" % i)
                for i in range(9)]
        p = _write(tmp_path / "a.jsonl", recs)
        assert sr.promotion_status(str(p))["R3"]["promotable"] is False

        # 只差假陽率:20 筆全可判定,2 筆誤報 = 10%
        recs = ([dict(_rec("R3", sr.CLASSES["6"]), message="b%d" % i)
                 for i in range(18)]
                + [dict(_rec("R3", "假陽/解析"), message="c%d" % i)
                   for i in range(2)])
        p = _write(tmp_path / "b.jsonl", recs)
        assert sr.promotion_status(str(p))["R3"]["promotable"] is False

        # 只差可判定率:20 筆已分類全無法判定 + 20 筆刻意 refuse
        recs = ([dict(_rec("R3", sr.CLASSES["7"]), message="d%d" % i)
                 for i in range(20)]
                + [dict(_rec("R3", sr.CLASSES["6"]), message="e%d" % i)
                   for i in range(20)])
        p = _write(tmp_path / "c.jsonl", recs)
        d = sr.promotion_status(str(p))["R3"]
        assert abs(d["decidable_rate"] - 0.5) < 1e-9
        assert d["promotable"] is False

    def test_the_threshold_is_a_named_constant(self):
        """畫在哪裡要看得見、改得動,而不是埋在判斷式裡(票 34 先例)。"""
        assert sr.MIN_DECIDABLE_RATE == 0.90


class TestOStatusShowsTheDecidableRate:
    """票 67:`print_status` 單獨列一欄。"""

    def test_status_shows_undecidable_and_the_decidable_rate(self, tmp_path, capsys):
        recs = ([dict(_rec("R7", sr.CLASSES["6"]), message="m%d" % i)
                 for i in range(8)]
                + [dict(_rec("R7", sr.CLASSES["7"]), message="n%d" % i)
                   for i in range(2)])
        p = _write(tmp_path / "shadow-log.jsonl", recs)
        sr.print_status(str(p))
        out = capsys.readouterr().out
        assert "無法判定" in out
        assert "可判定率" in out
        assert "80.0" in out

    def test_status_names_the_unclassified_remainder(self, tmp_path, capsys):
        """**未判定的餘量要印出來** —— 它是可判定率掉下來的主要原因,
        而不印的話讀者只看得到一個低百分比、看不出低在哪。"""
        recs = ([dict(_rec("R7", sr.CLASSES["6"]), message="m%d" % i)
                 for i in range(5)]
                + [dict(_rec("R7"), message="u%d" % i) for i in range(5)])
        p = _write(tmp_path / "shadow-log.jsonl", recs)
        sr.print_status(str(p))
        out = capsys.readouterr().out
        assert "未判定" in out


class TestPOldRecordIdentitiesMustNotDrift:
    """票 68 的連帶:`record_id` 是「除 `classification` 外全欄位」的雜湊,
    所以**加欄位會改變新紀錄的身分**。舊紀錄沒有新欄位,身分理應不變 ——
    但那是**目前實作**的性質,不是這條路徑的性質。

    > **已發出去的套用卡指的是身分。身分漂了,卡片就指不到東西 ——
    > 而那不會報錯,它只會變成「這張卡的 id 對不到任何一筆」。**

    所以這裡釘一個**黃金雜湊**:任何讓舊形態紀錄算出別的 id 的改動
    (補預設值、正規化欄位、換序列化)都會在這裡紅。
    """

    OLD_SHAPE = {
        "ts": "2026-08-15T03:47:37.702840+00:00",
        "rule": "R7",
        "at_commit": False,
        "verdict": "would-block",
        "message": "[R7] x",
    }
    GOLDEN = "af5d40aa258c7575e7544501fa8e169ae7cd045af5f154bc5bf7f9590b3641c0"

    def test_the_old_shape_still_hashes_to_the_same_id(self):
        assert sr.record_id(dict(self.OLD_SHAPE)) == self.GOLDEN

    def test_adding_the_new_fields_changes_the_id(self):
        """**負控**:若 `record_id` 忽略未知欄位,上一條會永遠綠而這條會紅。
        身分必須涵蓋全欄位 —— 那正是它不用 `ts` 的理由(票 64)。"""
        new_shape = dict(self.OLD_SHAPE,
                         cmd_sha256="0" * 64, cmd_verb="python", cmd_len=12)
        assert sr.record_id(new_shape) != self.GOLDEN

    def test_classification_still_does_not_affect_the_id(self):
        """既有性質不得被票 68 順手改掉。"""
        assert sr.record_id(dict(self.OLD_SHAPE, classification="真陽")) \
            == self.GOLDEN

    def test_a_log_mixing_old_and_new_shapes_reads_and_counts(self, tmp_path):
        """**向後相容是硬需求**:現有 222 筆是舊形態,新紀錄是新形態,
        兩種會在同一個檔案裡並存。"""
        old = dict(self.OLD_SHAPE, classification="真陽")
        new = dict(self.OLD_SHAPE, message="[R7] y", classification="真陽",
                   cmd_sha256="a" * 64, cmd_verb="python", cmd_len=9)
        p = _write(tmp_path / "shadow-log.jsonl", [old, new])
        rows = sr.load_log(str(p))
        assert len(rows) == 2
        d = sr.promotion_status(str(p))["R7"]
        assert d["classified"] == 2 and d["true_positives"] == 2


class TestETheErrorTypeIsItsOwn:
    """**不要用 `Exception`**:呼叫端要分得出「日誌壞了」與別的錯,
    而 `except Exception` 正是本票在修的東西 —— 修完又要求呼叫端
    寫一個同樣寬的 except,等於把坑往外挪一層。
    """

    def test_shadow_log_error_exists_and_is_an_exception(self):
        assert issubclass(sr.ShadowLogError, Exception)

    def test_it_is_not_just_an_alias_for_exception(self):
        assert sr.ShadowLogError is not Exception


class TestEStatusShowsRulesThatHaveNoClassificationsYet:
    """**同一個病在第三層** —— 這一次是 per-rule。

    上面 `TestDStatusSeparatesEmptyFromUnclassified` 修的是**整份日誌**那一層:
    「讀到了但沒分類」不得與「什麼都沒讀到」講同一句話。
    **而 per-rule 那一層還壓著同一件事。**

    `promotion_status` 先算全量 `totals`(每條規則各幾筆),但 `per` 只在
    **遇到有 `classification` 的紀錄時**才 `setdefault` 建鍵;
    `print_status` 走的是 `for rule in sorted(per)`。

    > 於是**一條規則只要一筆都沒分類過,它在表上就不存在** ——
    > 與「這條規則從來沒有記錄過」**逐字相同:都是不存在**。

    量化 2026-08-25 的實測正是這個形狀:日誌 476 筆,表上只有 R7 一行
    (總 400)。**差的 76 筆不是被歸進 R7,是整行沒有印。**

    ### 為什麼這是必修而不是美化

    這份輸出**就是 9/15 晉升決策的依據**。一條有 76 筆待判的規則
    看起來像不存在,決策者不會知道有東西要判 ——
    **留白被讀成蓋章**,與那 72 筆「無法判定」是同一句話。

    而它是同一支工具、同一族的**第二次**:票 63 才剛修過
    「讀取失敗偽裝成空日誌」。**修好一層之後,要問的是下一層有沒有同一個洞** ——
    這一次沒有人回頭問,是靠對帳時「476 與 400 對不上」才撞出來的,
    而**兩個數字剛好都被印出來**是運氣,不是設計。
    """

    def test_a_rule_with_no_classifications_still_appears(self, tmp_path, capsys):
        """正向:R2 有 76 筆全未分類,它必須出現在輸出裡。"""
        recs = ([_rec("R7", "刻意 refuse") for _ in range(10)]
                + [_rec("R2") for _ in range(76)])
        p = _write(tmp_path / "shadow-log.jsonl", recs)
        sr.print_status(str(p))
        assert "R2" in capsys.readouterr().out, "零分類的規則整行不見了"

    def test_the_line_carries_the_count_not_just_the_name(self, tmp_path, capsys):
        """只印規則名不夠 —— **決策者要知道有多少待判**,那是工作量。"""
        recs = ([_rec("R7", "刻意 refuse") for _ in range(10)]
                + [_rec("R2") for _ in range(76)])
        p = _write(tmp_path / "shadow-log.jsonl", recs)
        out = capsys.readouterr().out
        sr.print_status(str(p))
        out = capsys.readouterr().out
        assert "76" in out, "沒說出那條規則有幾筆待判"

    def test_zero_classified_differs_from_absent(self, tmp_path, capsys):
        """**本類的核心負控。**

        「R2 有 76 筆全未分類」與「日誌裡根本沒有 R2」必須是兩段不同的話。
        沒有這一條的話,一個「把所有零分類規則都印成同一句罐頭」的實作也會全綠。
        """
        with_r2 = ([_rec("R7", "刻意 refuse") for _ in range(10)]
                   + [_rec("R2") for _ in range(76)])
        p1 = _write(tmp_path / "a.jsonl", with_r2)
        sr.print_status(str(p1))
        out_with = capsys.readouterr().out

        p2 = _write(tmp_path / "b.jsonl",
                    [_rec("R7", "刻意 refuse") for _ in range(10)])
        sr.print_status(str(p2))
        out_without = capsys.readouterr().out

        assert out_with != out_without, "有 76 筆待判與根本沒這條規則,輸出一樣"
        # **差異必須是 R2 本身,不是別的東西。**
        # 只斷言 `!=` 的話,這一條在修好之前就會綠 —— 兩份日誌的
        # 「讀到 N 筆」那一行本來就不同(86 vs 10)。
        # 那是 F-103「因為錯的理由而通過」:負控通過了,而它證明的不是要證明的事。
        assert "R2" in out_with and "R2" not in out_without

    def test_a_classified_rule_still_prints_its_full_row(self, tmp_path, capsys):
        """負控:加了零分類那一行,不得把原本的晉升表擠掉(票 63 的同款負控)。"""
        recs = ([_rec("R7", "刻意 refuse") for _ in range(10)]
                + [_rec("R2") for _ in range(76)])
        p = _write(tmp_path / "shadow-log.jsonl", recs)
        sr.print_status(str(p))
        out = capsys.readouterr().out
        assert "假陽率" in out and "可判定率" in out, "原本的 per-rule 表被擠掉了"

    def test_totals_already_knew_about_the_hidden_rule(self, tmp_path):
        """**釘住根因,不只釘住症狀。**

        資料一直都在 —— `promotion_status` 的 `totals` 迴圈數過每一筆。
        丟掉它的是 `per` 只在有分類時建鍵。所以這一條斷言:
        **修法必須讓那條規則進得了回傳值**,而不是在列印層另外補一個旁路。

        差別在哪:旁路版的 `promotion_status` 回傳值仍然缺那條規則,
        於是**任何別的消費者**(未來的 CI 檢查、批次卡工具)照樣看不到它。
        """
        recs = ([_rec("R7", "刻意 refuse") for _ in range(10)]
                + [_rec("R2") for _ in range(76)])
        p = _write(tmp_path / "shadow-log.jsonl", recs)
        per = sr.promotion_status(str(p))
        assert "R2" in per, "promotion_status 的回傳值裡沒有零分類的規則"
        assert per["R2"]["total"] == 76
        assert per["R2"]["classified"] == 0
        assert per["R2"]["unclassified"] == 76


class TestFTheThresholdsAnnounceThatTheyAreNotAGate:
    """票 67 / `F-126` —— 三條門檻是**報表**,不是閘門,而輸出要自己說出來。

    ## 事實(2026-08-26 逐點追蹤)

    `MIN_CLASSIFIED` / `MAX_FALSE_POSITIVE_RATE` / `MIN_DECIDABLE_RATE`
    算出 `d["promotable"]`,而**那個值全庫只有一個讀取點**:
    `print_status` 拿它選「可轉正」或「留影子」兩個字串。
    `main()` 只有 `ShadowLogError` 回 1;`gate.py` 沒有 import 本模組。

    更深一層:`shadow_active()` 是 **per-repo 的布林值**,三個呼叫點
    (`gate.py:2145` / `:2180` / `:2538`)全是裸的 `if shadow_active():`,
    **沒有規則參數**。所以 ADR 0012 的「晉升 per-rule,不全局」未實作,
    而**「晉升」這個動作本身也不存在** —— 實際會發生的只有到期。

    ## 為什麼要一條測試而不是只改註解

    > **報表與閘門在文件裡長得一模一樣**,因為兩者都用「條件…才可…」的句式。

    「可轉正」三個字讀起來就是一道門的判決。裁決(2026-08-26)是
    **保留為報表、不補實作成閘門**,而那個決定只有在**輸出自己說得出來**時
    才擋得住下一個人重新誤讀 —— 註解不是機制,而這一層的「機制」
    就是輸出字串本身。
    """

    def test_the_status_output_says_it_is_a_report_not_a_gate(
            self, tmp_path, capsys):
        recs = [_rec("R7", "刻意 refuse") for _ in range(10)]
        p = _write(tmp_path / "shadow-log.jsonl", recs)
        sr.print_status(str(p))
        out = capsys.readouterr().out
        assert "報表" in out and "非閘門" in out, \
            "輸出沒有說出自己是報表:%r" % out

    def test_the_verdict_word_does_not_stand_alone(self, tmp_path, capsys):
        """**「可轉正」不得單獨出現。**

        它是本檔最容易被誤讀成判決的三個字。要嘛不用它,
        要嘛旁邊就有一句話說明沒有任何東西會因為它而改變行為。
        """
        recs = [_rec("R7", "刻意 refuse") for _ in range(10)]
        p = _write(tmp_path / "shadow-log.jsonl", recs)
        sr.print_status(str(p))
        out = capsys.readouterr().out
        if "可轉正" in out:
            assert "報表" in out or "不改變" in out or "非閘門" in out, \
                "印了「可轉正」卻沒有任何一句話說它不是閘門"

    def test_the_docstring_records_the_single_read_site(self):
        """**docstring 要說出那個追蹤結果**,不只說「這是報表」。

        一句沒有證據的宣稱,下一個人改動時不會相信它;
        而「`promotable` 只有一個讀取點」是**可複驗的**,他自己就能查一次。
        """
        doc = (sr.promotion_status.__doc__ or "") + (sr.print_status.__doc__ or "")
        assert "報表" in doc, "docstring 沒有標明報表性質"
        assert "promotable" in doc, "docstring 沒有指出那個值本身"

    def test_a_promotable_rule_still_computes_the_same_booleans(
            self, tmp_path):
        """**負控:標注不得改變計算。**

        本刀只加字,不動判定 —— 三條門檻算出來的 `promotable`
        必須與標注前逐位元組相同。沒有這一條的話,「順手改一下」
        會在一次措辭調整裡靜默改掉門檻語意。
        """
        recs = [_rec("R7", "刻意 refuse") for _ in range(10)]
        p = _write(tmp_path / "shadow-log.jsonl", recs)
        per = sr.promotion_status(str(p))
        d = per["R7"]
        assert d["classified"] == 10
        assert d["decidable"] == 10
        assert d["fp_rate"] == 0.0
        assert d["decidable_rate"] == 1.0
        assert d["promotable"] is True
