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
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "ledger_verify_under_test", ROOT / ".claude" / "portable" / "ledger_verify.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lv = _load()


def _load_gate():
    """票 116 B-6 步驟 4:桶4 的守衛釘在**產生端**,所以要載 `gate`。

    模組層載入是刻意的 —— `tests/conftest.py` 的證據隔離 fixture 走訪
    測試模組的屬性去找 gate 實例,**在測試函式內部才載的那份它蓋不到**
    (那條限制寫在該 fixture 的 docstring 裡)。
    """
    spec = importlib.util.spec_from_file_location(
        "gate_for_ledger_verify", ROOT / ".claude" / "hooks" / "gate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gate = _load_gate()


def _rec(before, after):
    return {"content_hash": before, "result_hash": after}


CONTINUOUS = [_rec("a", "b"), _rec("b", "c"), _rec("c", "a")]
BROKEN = [_rec("a", "b"), _rec("b", "x"), _rec("a", "y"), _rec("y", "a")]


# ── 票 116 B-6:四桶 ──────────────────────────────────────────────────────────
#
# `chain_breaks` 原本回一個扁平的斷點清單,而那個清單裡混著**三種完全不同**的東西
# 外加一個**根本沒被報出來**的第四種(實測 2026-09-08,帳本 223 筆):
#
#     設計上的斷(pre-commit,result_hash=None)   29 對  ← 是設計,不是缺陷
#     格式交界(5 鍵 -> 13 鍵)                     1 對  ← 是歷史,不是缺陷
#     真的對不上                                   4 對  ← 要人看的
#     無從驗證(相鄰兩筆都沒有雜湊欄位)            39 對  ← **一個都沒被報** = fail-open
#
# 前三種一起報 34 個,而其中 30 個是設計或歷史 ⇒ 噪音訓練人忽略訊號(`F-031`)。
# 第四種完全看不見 ⇒ 40 筆沒有雜湊的紀錄「看起來像一條完好的鏈」。

def _pre(before):
    """pre-commit 那一半:`result_hash` 是 `None`(**不是 False**),`at_commit=true`。"""
    return {"content_hash": before, "result_hash": None, "at_commit": True}


def _nohash():
    """票 08 之前的 5 鍵舊格式:**連鍵都沒有**。"""
    return {"file": "x.py", "module": "x", "ticket": "01",
            "declared_in": "0004", "reason": "gate-self-modification"}


BY_DESIGN = [_rec("a", "b"), _pre("b"), _rec("b", "c")]
FORMAT_SEAM = [_nohash(), _nohash(), _rec("a", "b")]
UNVERIFIABLE = [_nohash(), _nohash(), _nohash()]


def _no_anomalies(buckets):
    """**四個異常桶都空**(`BUCKET_LINKED` 不算異常)——「沒有斷點」的四桶版說法。

    ⚠ **票 116 B-6 的一個判斷,寫在這裡讓它可搜尋**:
    既有那幾條斷言原本是 `chain_breaks(...) == []`,而四桶之後
    「沒有斷點」有兩種讀法 ——「桶1~3 都空」還是「**桶1~4 都空**」。

    **選了後者(含「無從驗證」)**,理由:寬的讀法會讓那幾條**默許
    「無從驗證」混進來**,而那正是本刀要讓它現形的東西。
    用嚴的讀法,那幾條的意思**一個字都沒變** ——
    它們的語料都是完整雜湊的合成鏈,本來就不會落進那一桶。

    `BUCKET_LINKED` **不能**一起要求為空:連續鏈的每一對都在那裡,
    要求它空等於要求語料只有一筆。
    """
    return not any(buckets[k] for k in lv.BUCKET_ORDER)


class TestTheFourBuckets:
    """**紅燈甲乙**:三種不是缺陷的東西各自有桶,而真的對不上仍然進斷點桶。"""

    def test_a_pre_commit_record_goes_to_the_by_design_bucket(self):
        """**甲前半**:`result_hash=None` 且 `at_commit=true` 是設計,不是斷點。

        `gate.exemption_record` 的 docstring 逐字:「**None 不是 False**」——
        提交時算不出結果內容,所以記 `None`(= 不知道),
        不得寫成 `False`(= 確定沒變)。
        """
        b = lv.chain_breaks(BY_DESIGN)
        assert len(b[lv.BUCKET_BY_DESIGN]) == 1, b
        assert b[lv.BUCKET_MISMATCH] == [], (
            "設計上的斷被歸進「真的對不上」—— 那正是 34 個裡面 29 個的噪音來源:%s" % b)

    def test_a_real_mismatch_still_goes_to_the_mismatch_bucket(self):
        """**甲後半(反控)**:分桶不得把真的對不上一起吃掉。

        少了這一條,一支「什麼都歸進設計桶」的實作會讓上一條過 ——
        那是把功能拿掉,不是修好。
        """
        b = lv.chain_breaks(BROKEN)
        assert len(b[lv.BUCKET_MISMATCH]) == 1, b
        i, j, ended, started = b[lv.BUCKET_MISMATCH][0]
        assert (i, j) == (2, 3) and ended == "x" and started == "a", b

    def test_two_hashless_records_go_to_the_unverifiable_bucket(self):
        """**乙 —— 本刀最重要的一格。**

        相鄰兩筆都沒有雜湊欄位時,舊實作兩邊都 `.get()` 到 `None`,
        `None != None` 為假 ⇒ **不算斷**。於是 40 筆完全沒有雜湊、
        **無從驗證**的紀錄,在輸出上與「驗過而且接得上」長得一模一樣。

        **那是 fail-open。** `parse_records` 的 docstring 已經寫過同一條的另一半
        (「壞行不能跳過,否則鏈會**看起來是連續的**」)——
        它管的是壞行,沒管到「解析得了但沒有雜湊欄位的行」,**而後果相同**。
        """
        b = lv.chain_breaks(UNVERIFIABLE)
        assert len(b[lv.BUCKET_UNVERIFIABLE]) == 2, b
        assert b[lv.BUCKET_MISMATCH] == [] and b[lv.BUCKET_BY_DESIGN] == [], b

    def test_the_seam_between_the_two_formats_has_its_own_bucket(self):
        """格式交界:前一筆沒有雜湊欄位、後一筆有 —— 是歷史,不是缺陷。"""
        b = lv.chain_breaks(FORMAT_SEAM)
        assert len(b[lv.BUCKET_FORMAT_SEAM]) == 1, b
        assert b[lv.BUCKET_MISMATCH] == [], b

    def test_the_four_buckets_partition_every_adjacent_pair(self):
        """**四桶 + 接得上 = 每一對相鄰,一個都不漏。**

        少了這一條,分類裡多一個沒人注意的 `else` 分支就會靜靜吃掉一群東西 ——
        而**被吃掉的與不存在的在輸出上長得一樣**。
        """
        for corpus in (CONTINUOUS, BROKEN, BY_DESIGN, FORMAT_SEAM, UNVERIFIABLE):
            b = lv.chain_breaks(corpus)
            counted = sum(len(b[k]) for k in lv.BUCKET_ORDER) + len(b[lv.BUCKET_LINKED])
            assert counted == max(len(corpus) - 1, 0), (
                "分桶沒有涵蓋所有相鄰對:語料 %d 筆,桶裡共 %d 對"
                % (len(corpus), counted))


class TestKnownBreaksWhitelist:
    """**紅燈丙**:白名單外的「真的對不上」要紅;登記進去(附理由)才綠。

    ## 這張白名單的由來 —— 它有主詞了

    第六站 2026-08-24 首跑就寫下「帳本鏈已知斷點非缺陷;若帳本鏈驗證常態化,
    需『已知斷點附理由』白名單」,**而它從未落地** —— `F-110` 的形狀
    (規矩寫下來了,而沒有東西會因為它沒被做而叫)。
    **本刀是那句話的主詞。**

    ⚠ **當時 1 處,今天 4 處** —— 集合長大了而沒有人回頭看。
    那正是「祈使句沒有主詞」的代價。

    ## 定位鍵是**雜湊對**,不是索引

    索引會隨帳本增長而漂(帳本每天都在長)。**引身分,不引位置** ——
    與票 114 B-2 的「引符號名不引行號」、票 116 B-8 的「記 ADR 編號不記路徑」
    是同一條,今天第四次。
    """

    ENTRY = "x a  git checkout 還原,不經前哨,依設計不記帳"

    def test_an_unregistered_mismatch_is_reported(self, tmp_path):
        p = tmp_path / "known.txt"
        p.write_text("", encoding="utf-8")
        left = lv.unregistered_mismatches(BROKEN, str(p))
        assert len(left) == 1, left

    def test_a_registered_mismatch_is_cleared(self, tmp_path):
        p = tmp_path / "known.txt"
        p.write_text(self.ENTRY + "\n", encoding="utf-8")
        assert lv.unregistered_mismatches(BROKEN, str(p)) == []

    def test_a_missing_whitelist_file_clears_nothing(self, tmp_path):
        """**fail-closed**:檔案不存在 = 空白名單,不是「全部放行」。"""
        left = lv.unregistered_mismatches(BROKEN, str(tmp_path / "nope.txt"))
        assert len(left) == 1, left

    def test_an_entry_without_a_reason_is_refused(self, tmp_path):
        """**理由欄硬性**:只有兩個雜湊沒有理由 ⇒ 拒絕,不是靜默接受。

        理由欄是讓「這一處為什麼是對的」看得見的東西。少了它,
        白名單會退化成一張「把紅燈消掉」的清單 —— 那正是它要防的。
        """
        p = tmp_path / "known.txt"
        p.write_text("x a\n", encoding="utf-8")
        with pytest.raises(ValueError):
            lv.known_breaks(str(p))

    def test_the_whitelist_does_not_clear_other_buckets(self, tmp_path):
        """白名單只作用在「真的對不上」那一桶,不得拿來消掉別的。"""
        p = tmp_path / "known.txt"
        p.write_text(self.ENTRY + "\n", encoding="utf-8")
        b = lv.chain_breaks(UNVERIFIABLE)
        assert len(b[lv.BUCKET_UNVERIFIABLE]) == 2, (
            "白名單把「無從驗證」也消掉了 —— 那一桶不是給人登記的:%s" % b)


class TestTheExitCodeStaysZero:
    """**釘子丁 —— 改動前後都綠,它不是紅燈。**

    照票 114 收尾那一刀的先例明說:
    **為儀式造一個恆綠的東西並稱之為紅燈,比沒有紅燈更糟。**

    它守的是 `ledger_verify.py` 自己寫下的那個決定(該檔 docstring):

    > 因此本檔**永遠回 0**,不用退出碼表達「有沒有斷點」——
    > 把「需要人看一眼」講成「失敗」,會讓它被當成紅燈去消除,
    > 而消除的方法多半是不再跑它(F-031)。

    **四桶是為了讓人讀得懂,不是為了製造一個紅燈。**
    而那 4 筆「真的對不上」實測是合法還原(其中一筆就是本檔開頭引的那個例子),
    綁上退出碼等於在一份已知良好的帳本上製造永久紅燈。
    """

    def test_main_returns_zero_even_with_breaks(self, tmp_path, capsysbinary):
        p = tmp_path / "led.jsonl"
        p.write_text("\n".join(json.dumps(r) for r in BROKEN) + "\n",
                     encoding="utf-8")
        assert lv.main([str(p)]) == 0

    def test_main_returns_zero_on_a_clean_ledger(self, tmp_path, capsysbinary):
        p = tmp_path / "led.jsonl"
        p.write_text("\n".join(json.dumps(r) for r in CONTINUOUS) + "\n",
                     encoding="utf-8")
        assert lv.main([str(p)]) == 0


class TestTheProducerAlwaysWritesBothHashKeys:
    """**步驟 4:桶4 的守衛釘在產生端,不是筆數。**

    斷言「桶4 恰好 39 對」等於把一個會漂的數字凍起來,而且那是**這個 repo 的資料**
    (下游① 48 筆、下游② 0 筆 —— 票 116 B-8 實測)。

    **能用構造解決的不要用條件**:`gate.exemption_record` 一律寫兩個雜湊鍵
    ⇒ 桶4 由構造不會長大。它長大只可能是「有人手改帳本」或「有人用舊版 gate 寫入」,
    **那兩件都是真的要看的事,而且零誤報。**
    """

    def test_every_produced_record_carries_both_hash_keys(self):
        rec = gate.exemption_record(
            {"file": "pkg/thing.py", "module": "thing", "ticket": "01",
             "declared_in": "0004", "reason": "gate-self-modification"},
            None, False, "implement", "01", "x = 1\n")
        assert "content_hash" in rec, rec
        assert "result_hash" in rec, rec

    def test_the_keys_are_present_even_when_the_value_is_none(self):
        """**鍵必須在,值可以是 None** —— 那正是「None 不是 False」的另一半。

        pre-commit 那一半算不出結果內容,`result_hash` 是 `None`;
        但**鍵不在**的話,它就掉進「無從驗證」桶,而那是舊格式才有的形態。
        """
        rec = gate.exemption_record(
            {"file": "pkg/thing.py", "module": "thing", "ticket": "01",
             "declared_in": "0004", "reason": "gate-self-modification"},
            None, True, "implement", "01", None)
        assert "result_hash" in rec and rec["result_hash"] is None, rec

    def test_dropping_a_key_would_be_caught(self):
        """**反控**:證明上面兩條會咬,而不是恆綠。

        拿掉其中一個鍵的紀錄,必須被歸進「無從驗證」桶。
        """
        rec = gate.exemption_record(
            {"file": "pkg/thing.py", "module": "thing", "ticket": "01",
             "declared_in": "0004", "reason": "gate-self-modification"},
            None, False, "implement", "01", "x = 1\n")
        stripped = {k: v for k, v in rec.items()
                    if k not in ("content_hash", "result_hash")}
        b = lv.chain_breaks([stripped, dict(stripped)])
        assert len(b[lv.BUCKET_UNVERIFIABLE]) == 1, (
            "少了兩個雜湊鍵的紀錄沒有落進「無從驗證」桶 —— 那條路徑又變回 fail-open:%s" % b)


class TestChainBreaks:

    def test_a_continuous_chain_has_no_breaks(self):
        assert _no_anomalies(lv.chain_breaks(CONTINUOUS))

    def test_a_broken_chain_names_the_gap(self):
        """斷點要**指名**兩端的雜湊 —— 那正是人要拿去查的東西。

        ⚠ 票 116 B-6:原本讀的是扁平清單,現在讀「真的對不上」那一桶。
        **斷言的內容一個字沒改**(位置 `(2,3)`、兩端 `x` / `a`)。
        """
        breaks = lv.chain_breaks(BROKEN)[lv.BUCKET_MISMATCH]
        assert len(breaks) == 1, breaks
        i, j, ended, started = breaks[0]
        assert (i, j) == (2, 3), "斷點的位置報錯了:%r" % (breaks,)
        assert ended == "x" and started == "a", (
            "斷點兩端的雜湊報錯了 —— 那正是人要拿去查的東西:%r" % (breaks,))

    def test_an_empty_or_single_record_chain_has_no_breaks(self):
        """邊界:0 或 1 筆沒有「段」可以斷。**五個桶都空**而不是丟例外 ——
        帳本第一次被寫時就是 1 筆,而那不是異常狀態。

        ⚠ 票 116 B-6:原本斷言 `== []`(扁平清單)。四桶之後改成
        `_all_empty(...)`,**意思一個字沒變**。
        """
        assert _no_anomalies(lv.chain_breaks([]))
        assert _no_anomalies(lv.chain_breaks([_rec("a", "b")]))


class TestEndpointsAreADifferentQuestion:
    """**這一組是 v1 那個缺陷的紅燈,永久釘住。**

    v1 只有 `endpoints_match` 那一半,而它在斷鏈上照樣回 True。
    兩個述詞分開存在,就是為了讓「它們可以同時給出不同答案」這件事
    **在型別上就看得見**。
    """

    def test_a_broken_chain_can_still_have_matching_endpoints(self):
        """**核心紅燈。** 首尾相等,而中間斷了 —— v1 在這裡說「回到原點」。"""
        assert lv.endpoints_match(BROKEN) is True, "測試語料的首尾本來就該相等"
        assert lv.chain_breaks(BROKEN)[lv.BUCKET_MISMATCH], (
            "語料沒有斷點 —— 那這一條就沒有在測 v1 的那個缺陷")

    def test_the_two_predicates_agree_on_a_continuous_chain(self):
        """**反控。** 少了它,一支「`chain_breaks` 永遠回非空」的實作
        也會讓上面那條綠。"""
        assert lv.endpoints_match(CONTINUOUS) is True
        assert _no_anomalies(lv.chain_breaks(CONTINUOUS))

    def test_endpoints_can_differ_while_the_chain_is_continuous(self):
        """另一個方向:鏈完整,但沒有走回起點(還原到一半就停)。

        這一格證明兩個述詞是**互相獨立**的,不是一個蘊含另一個。
        """
        half = [_rec("a", "b"), _rec("b", "c")]
        assert _no_anomalies(lv.chain_breaks(half))
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
        assert _no_anomalies(lv.chain_breaks(recs))

    def test_a_malformed_line_is_refused_not_skipped(self):
        """**fail-closed。** 讀不動的行不得靜默跳過 ——
        跳過等於「那一段改動不存在」,而鏈會因此看起來是連續的。
        """
        import pytest
        with pytest.raises(ValueError):
            lv.parse_records('{"content_hash": "a", "result_hash": "b"}\n{壞掉\n')
