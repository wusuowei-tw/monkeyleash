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


class TestETheErrorTypeIsItsOwn:
    """**不要用 `Exception`**:呼叫端要分得出「日誌壞了」與別的錯,
    而 `except Exception` 正是本票在修的東西 —— 修完又要求呼叫端
    寫一個同樣寬的 except,等於把坑往外挪一層。
    """

    def test_shadow_log_error_exists_and_is_an_exception(self):
        assert issubclass(sr.ShadowLogError, Exception)

    def test_it_is_not_just_an_alias_for_exception(self):
        assert sr.ShadowLogError is not Exception
