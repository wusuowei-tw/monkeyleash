# -*- coding: utf-8 -*-
"""票 94 —— 「六站」是**名稱**,不是計數;站別以 `.agents/pipeline-stages.yaml` 為準。

## 裁決(2026-09-07)

票面列了三種可能,裁決取**第一種**:

> **「六站」是產品名的一部分,不承諾等於 `id` 數 —— 那就寫明它不是計數。**

## 這個檔案守什麼

票 51 D3 立過的判準是「**條數不寫死,指向權威來源**」。R 系列照做了
(`rule_codes()` 從規則自己的訊息掃出來),**而「六站」這個數字寫死在散文與
程式碼註解裡,沒有任何一處從定義檔算出來,也沒有任何測試比對它** ——
`F-148`:一條紀律的範圍,大於守住它的那個機制的範圍。

本檔把那條判準套到站別上,**用裁決選的那個形狀**:不要求數字相等,
要求**文件說清楚它不是計數**,而**真的在數站別的句子**必須數對。

## ⚠ 本檔標 `skip`(不隨安裝走)—— 代價明寫

它斷言 `README.md` / `README.zh-TW.md` 的內容,而那兩個檔在
`.agents/portable-manifest.txt` 標 **`skip`**(各 repo 自己的檔案)。
下游沒有那兩個檔,這裡的斷言會**註定紅**,而那個紅與「下游違反命名規則」
長得一模一樣。

**不改成「找不到就 skip」**(票 16:測試從 pass 轉 skip 沒有東西會出聲)。

> ### **⇒ 下游因此完全沒有這個檢查。這是缺口,不是留白。**
> 與 `tests/test_adr_numbering.py` 同一個形狀、同一個理由(票 89 §4-4)。
"""
import io
import pathlib
import re

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
STAGES = ROOT / ".agents" / "pipeline-stages.yaml"

# ── 要求三份文件各含的那一句(裁決指定的文句)──────────────────────────────
ZH_DISCLAIMER = (
    "「六站」是名字不是站數,站別以 `.agents/pipeline-stages.yaml` 為準。")
EN_DISCLAIMER = (
    "\"Six-station\" is a name, not a count — "
    "the stages are defined by `.agents/pipeline-stages.yaml`.")

DOCS = {
    "CLAUDE.md": ZH_DISCLAIMER,
    "README.zh-TW.md": ZH_DISCLAIMER,
    "README.md": EN_DISCLAIMER,
}

# ── 產品名用法的白名單 ────────────────────────────────────────────────────
# **這些不是在數站別,是在叫一個東西的名字。** 掃描前先把它們拿掉。
#
# ⚠ **「六站主線流程」不在這裡** —— 那是**真的在數**(它接著列出六個 skill,
# 並說「另有兩個站不在主線上」)。它應該被檢查,而不是被白名單消音。
# 把一句正確的計數句白名單掉,等於讓它從此不受任何檢查 ——
# 那正是本票要修的那種「沒有人在守的數字」,只是換了個地方。
PRODUCT_NAME_PHRASES = (
    "六站流程閘門",
    "六站工作流程",
    "六站閘門",
    "六站事件",
    "六站流程",
    "six-stage",
    "six stage",
)

_CJK_DIGITS = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
               "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
_EN_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
             "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}

_ZH_COUNT = re.compile(r"([一二三四五六七八九十]|\d+)\s*站")

# 前面出現這些字時,那個數字**不是在數**:
#   `哪一站` / `這一站` / `每一站`  -> 指示詞,不是計數
#   `第六站`                        -> 序數,不是計數
#
# 🔴 **這一條是實測撞出來的,不是預先想到的**:第一版把 README 的
# 「目前在**哪一站**是一個由人編輯的檔案」讀成「1 站」,於是報了一個假陽性。
# **一個把「哪一站」讀成「一站」的偵測器,會在第一次跑就製造一個假缺陷** ——
# 而修它的人會去改一句完全正確的散文。
_ZH_NOT_A_COUNT_PREFIX = "哪每這那上下同前後第各本某整全"
_EN_COUNT = re.compile(
    r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)"
    r"[- ](?:stage|station)s?\b", re.IGNORECASE)


def _stages():
    with io.open(str(STAGES), encoding="utf-8") as f:
        return yaml.safe_load(f)["stages"]


def _counts():
    """三個從**定義檔算出來**的數字。**一個都不寫死。**

    | 名字 | 怎麼算 | 這台機器上 |
    |---|---|---|
    | `ids` | `stages` 的長度 | 8 |
    | `work` | 扣掉 `idle`(`skill` 是 null 的那個) | 7 |
    | `main_line` | 再扣掉**不在主線上**的(有 `src_write_scope` 的 `research`) | 6 |

    `main_line` 為什麼也要算:兩份 README 逐字寫著「**六站主線流程**」
    /「**Six-station main-line pipeline**」,而它們接著列出六個 skill、
    並明說「另有兩個站不在主線上」——**那是一句正確的計數句**。
    只認 `work` 的話,這句正確的話會被判成錯,而唯一的修法會是把它白名單掉,
    **於是它從此不受任何檢查**。
    """
    stages = _stages()
    work = [s for s in stages if s.get("skill")]
    main_line = [s for s in work if not s.get("src_write_scope")]
    return {"ids": len(stages), "work": len(work), "main_line": len(main_line)}


def _strip_product_names(text):
    low = text
    for phrase in PRODUCT_NAME_PHRASES:
        low = re.sub(re.escape(phrase), " ", low, flags=re.IGNORECASE)
    return low


def _counting_claims(text):
    """文字裡**在數站別**的那些句子,回 [(原字串, N), ...]。"""
    body = _strip_product_names(text)
    out = []
    for m in _ZH_COUNT.finditer(body):
        before = body[m.start() - 1] if m.start() else ""
        # ⚠ `before and` **不可省**:`"" in "任何字串"` 在 Python 是 **True**,
        # 所以少了它,**每一個出現在字串開頭的計數句都會被靜默跳過** ——
        # 而那正是這個偵測器最該抓到的那種句子(標題、表格欄位的第一個字)。
        # 本檔的兩條反控在寫完的第一次跑就抓到它。
        if before and before in _ZH_NOT_A_COUNT_PREFIX:
            continue
        tok = m.group(1)
        out.append((m.group(0), _CJK_DIGITS.get(tok) or int(tok)))
    for m in _EN_COUNT.finditer(body):
        tok = m.group(1).lower()
        out.append((m.group(0), _EN_WORDS.get(tok) or int(tok)))
    return out


class TestSixIsANameNotACount:

    def test_the_counts_come_from_the_definition_file(self):
        """① **數字從定義檔算,不寫死。**

        這一條本身不比對任何文件 —— 它守的是**後面兩條的材料是量來的**。
        少了它,下面兩條可以拿一個寫死的常數去比,而那正是本票的病灶
        (一個沒有人在守的數字,換一個地方繼續沒有人守)。
        """
        c = _counts()
        stages = _stages()
        assert c["ids"] == len(stages) >= 3, c
        # idle 是唯一 skill 為 null 的那個 —— 用**性質**認它,不用名字。
        assert c["work"] == c["ids"] - 1, (
            "扣掉的不只一個(或一個都沒扣)—— `skill: null` 的站不只 idle?%r"
            % [s["id"] for s in stages if not s.get("skill")])
        assert 0 < c["main_line"] <= c["work"], c

    @pytest.mark.parametrize("name", sorted(DOCS))
    def test_each_doc_says_the_number_is_not_a_count(self, name):
        """② **三份文件各含那一句。**

        裁決取的是「名稱就是名稱」那條路,而那條路的**全部內容**就是這一句:
        不寫明的話,「六站」與 `pipeline-stages.yaml` 的 8 個 `id` 之間
        那個落差**仍然沒有任何東西說**。
        """
        body = io.open(str(ROOT / name), encoding="utf-8").read()
        assert DOCS[name] in body, (
            "%s 沒有那句免責 —— 「六站」讀起來仍然像一個承諾。\n"
            "  應含:%s" % (name, DOCS[name]))

    @pytest.mark.parametrize("name", sorted(DOCS))
    def test_any_real_counting_sentence_matches_the_definition_file(self, name):
        """③ **真的在數站別的句子,數字必須對得上定義檔。**

        產品名用法(`PRODUCT_NAME_PHRASES`)掃描前先拿掉 —— 它們不是在數。

        ⚠ **允許的值有三個**(`ids` / `work` / `main_line`),不是只有一個。
        理由寫在 `_counts()` 的 docstring:兩份 README 的「六站主線流程」
        是**正確的**計數句,只認 `work` 會把它判成錯,
        而唯一的修法會是把一句真話白名單掉。
        """
        body = io.open(str(ROOT / name), encoding="utf-8").read()
        c = _counts()
        allowed = set(c.values())
        bad = [(s, n) for s, n in _counting_claims(body) if n not in allowed]
        assert not bad, (
            "%s 有 %d 句在數站別,而數字對不上定義檔:%r\n"
            "  定義檔算出來的:總 id %d / 工作站 %d / 主線 %d\n"
            "  產品名用法請加進 PRODUCT_NAME_PHRASES;真的在數就把數字改對。"
            % (name, len(bad), bad, c["ids"], c["work"], c["main_line"]))

    def test_the_counting_detector_can_actually_see_a_wrong_number(self):
        """③的反控:**這個偵測器真的看得到錯的數字。**

        少了它,一個永遠回空串列的 `_counting_claims` 會讓上面三個檔全綠 ——
        而那是本票最容易犯的錯:**把一個沒有人在守的數字,換成一個
        看起來有人守、實際上偵測不到東西的數字。**
        """
        c = _counts()
        wrong = c["ids"] + 99
        assert _counting_claims("這是一條 %d 站的流程" % wrong) == [
            ("%d 站" % wrong, wrong)]
        assert _counting_claims("a %d-stage pipeline" % wrong) == [
            ("%d-stage" % wrong, wrong)]
        # 中文數詞也要認得(「九站」不是阿拉伯數字,而散文裡就是這樣寫的)
        assert _counting_claims("九站流程") == [("九站", 9)]

    def test_a_demonstrative_or_ordinal_is_not_a_count(self):
        """🔴 **反控:「哪一站」不是「1 站」。**

        **這一條是實測撞出來的。** 第一版把 README 的
        「目前在**哪一站**是一個由人編輯的檔案」讀成一句「1 站」的計數句,
        於是報了一個**假陽性**。

        > **一個把「哪一站」讀成「一站」的偵測器,在第一次跑就製造一個假缺陷 ——
        > 而修它的人會去改一句完全正確的散文。**

        誤擋的代價在這裡不是不方便,是**這條規則會被關掉**(同票 23 的判準)。
        """
        assert _counting_claims("目前在哪一站是一個由人編輯的檔案") == []
        assert _counting_claims("第六站是架構掃除") == []
        assert _counting_claims("每一站都有自己的 skill") == []
        # 而**真的在數**的仍然要抓到 —— 少了這半,一個「一律不算」的實作也會綠
        assert _counting_claims("這是一條 六站 的流程") == [("六站", 6)]

    def test_the_product_name_whitelist_does_not_swallow_everything(self):
        """**白名單的反控:它不得把整篇文章都吃掉。**

        `PRODUCT_NAME_PHRASES` 是用字串取代做的,而一個過寬的片語
        (例如只寫「站」)會讓 ③ 永遠找不到任何東西。
        """
        assert _strip_product_names("六站閘門").strip() == ""
        assert _counting_claims("六站主線流程") == [("六站", 6)], (
            "「六站主線流程」被白名單吃掉了 —— 那是一句真的在數的句子,"
            "它應該被檢查,不是被消音")
