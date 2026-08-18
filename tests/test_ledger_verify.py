# -*- coding: utf-8 -*-
"""票 47 收尾 —— 帳本鏈的驗證工具本身要有測試。

## 為什麼這支工具存在

`.dev/gate-exemptions.jsonl` 的每一筆帶 `content_hash` 與 `result_hash`
(編輯前 / 編輯後)。連續的編輯因此串成一條鏈,而那條鏈可以**獨立於任何人的
宣稱**證明「檔案出去又回來了」—— 票 58 與票 47 的三次有界突變都靠它收尾。

## 為什麼它要進版控、而且要有測試

**票 47 批 3 的實測:第一版的檢查是錯的。**

v1 問的是「第一筆的 `content_hash` 等不等於最後一筆的 `result_hash`」。
那條斷言在**鏈中間斷過一次、又走回同一個雜湊**時**照樣通過** ——
而批 3 的鏈正是那個形狀:

    5  fa29d055 -> 795dff63     M4
    6  54dabea0 -> adcc5fb1     M5        ← 第 5 筆結束於 795dff63,這裡卻從 54dabea0 開始

斷點來自那次還原走了 `git checkout`(Bash 不經前哨,依設計不記帳)。
**v1 說「回到原點」,而它只看了兩端。**

> **首尾相等不蘊含逐段接續。**

而 v1 之所以沒被抓到,是因為它是 scratchpad 裡的拋棄式腳本 ——
**沒有測試、沒進版控、下一個人會重寫一次,而多半會重寫成 v1**
(2026-08-17 那支探針腳本已經因為同樣的理由消失了)。

## 斷點不等於缺陷

`chain_breaks()` 只回報,不判對錯。**斷點的意思是「有一次改動發生在前哨看不見的
地方」** —— 那可能是 `git checkout`、可能是外部編輯器、也可能是真的有人繞過。
**分辨它們要讀上下文,那是人的判斷**(同 `sync.refuse_if_duplicate_headings`
的理由:護欄讓它現形,不替人決定)。
"""
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "ledger_verify_under_test", ROOT / ".claude" / "portable" / "ledger_verify.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lv = _load()


def _rec(before, after):
    return {"content_hash": before, "result_hash": after}


CONTINUOUS = [_rec("a", "b"), _rec("b", "c"), _rec("c", "a")]
BROKEN = [_rec("a", "b"), _rec("b", "x"), _rec("a", "y"), _rec("y", "a")]


class TestChainBreaks:

    def test_a_continuous_chain_has_no_breaks(self):
        assert lv.chain_breaks(CONTINUOUS) == []

    def test_a_broken_chain_names_the_gap(self):
        breaks = lv.chain_breaks(BROKEN)
        assert len(breaks) == 1, breaks
        i, j, ended, started = breaks[0]
        assert (i, j) == (2, 3), "斷點的位置報錯了:%r" % (breaks,)
        assert ended == "x" and started == "a", (
            "斷點兩端的雜湊報錯了 —— 那正是人要拿去查的東西:%r" % (breaks,))

    def test_an_empty_or_single_record_chain_has_no_breaks(self):
        """邊界:0 或 1 筆沒有「段」可以斷。回 [] 而不是丟例外 ——
        帳本第一次被寫時就是 1 筆,而那不是異常狀態。"""
        assert lv.chain_breaks([]) == []
        assert lv.chain_breaks([_rec("a", "b")]) == []


class TestEndpointsAreADifferentQuestion:
    """**這一組是 v1 那個缺陷的紅燈,永久釘住。**

    v1 只有 `endpoints_match` 那一半,而它在斷鏈上照樣回 True。
    兩個述詞分開存在,就是為了讓「它們可以同時給出不同答案」這件事
    **在型別上就看得見**。
    """

    def test_a_broken_chain_can_still_have_matching_endpoints(self):
        """**核心紅燈。** 首尾相等,而中間斷了 —— v1 在這裡說「回到原點」。"""
        assert lv.endpoints_match(BROKEN) is True, "測試語料的首尾本來就該相等"
        assert lv.chain_breaks(BROKEN), (
            "語料沒有斷點 —— 那這一條就沒有在測 v1 的那個缺陷")

    def test_the_two_predicates_agree_on_a_continuous_chain(self):
        """**反控。** 少了它,一支「`chain_breaks` 永遠回非空」的實作
        也會讓上面那條綠。"""
        assert lv.endpoints_match(CONTINUOUS) is True
        assert lv.chain_breaks(CONTINUOUS) == []

    def test_endpoints_can_differ_while_the_chain_is_continuous(self):
        """另一個方向:鏈完整,但沒有走回起點(還原到一半就停)。

        這一格證明兩個述詞是**互相獨立**的,不是一個蘊含另一個。
        """
        half = [_rec("a", "b"), _rec("b", "c")]
        assert lv.chain_breaks(half) == []
        assert lv.endpoints_match(half) is False

    def test_an_empty_chain_is_not_claimed_to_match(self):
        """空鏈沒有端點可比。**回 False,不是 True** ——
        「沒有證據」不得回報成「證明了」(fail-closed 的同一條)。"""
        assert lv.endpoints_match([]) is False


class TestParsing:

    def test_it_reads_json_lines_and_ignores_blanks(self):
        text = ('{"content_hash": "a", "result_hash": "b"}\n'
                "\n"
                '{"content_hash": "b", "result_hash": "c"}\n')
        recs = lv.parse_records(text)
        assert len(recs) == 2
        assert lv.chain_breaks(recs) == []

    def test_a_malformed_line_is_refused_not_skipped(self):
        """**fail-closed。** 讀不動的行不得靜默跳過 ——
        跳過等於「那一段改動不存在」,而鏈會因此看起來是連續的。
        """
        import pytest
        with pytest.raises(ValueError):
            lv.parse_records('{"content_hash": "a", "result_hash": "b"}\n{壞掉\n')
