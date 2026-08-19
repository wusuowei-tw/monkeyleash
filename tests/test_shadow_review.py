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


class TestETheErrorTypeIsItsOwn:
    """**不要用 `Exception`**:呼叫端要分得出「日誌壞了」與別的錯,
    而 `except Exception` 正是本票在修的東西 —— 修完又要求呼叫端
    寫一個同樣寬的 except,等於把坑往外挪一層。
    """

    def test_shadow_log_error_exists_and_is_an_exception(self):
        assert issubclass(sr.ShadowLogError, Exception)

    def test_it_is_not_just_an_alias_for_exception(self):
        assert sr.ShadowLogError is not Exception
