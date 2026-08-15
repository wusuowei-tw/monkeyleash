# -*- coding: utf-8 -*-
"""已知項回歸的**防過度擬合**那一半(票 39,裁決 2 / 回件失效模式 A)。

回件點名的失效模式 A:

  > 為使已知洩漏通過「未清除應掃得到」的回歸測試,開發者會被迫寫出特製的
  > pattern。這導致測試恆為綠,但僅證明「能抓到特定字串」,而非
  > 「能抓到該類型的洩漏」。

所以每一條回歸驅動的新 pattern,除了要打中**真樣本**,還必須打中
**同類但不同字串**的合成樣本 —— 換使用者名、換資料夾名、換深度、換分隔符。
打不中就是過度擬合,pattern 要重寫。

**合成樣本寫在這裡,不寫進 pattern 清單。**
清單只放真正要守的東西;把合成樣本塞進清單等於把測試資料當成規則。
**真實字串一律不進版控** —— 個人 pattern 只走 age 匯出(裁決 2 鎖死條款),
所以本檔一個真實字串都沒有,只有結構相同的假資料。

本檔在 `portable-manifest` 標 `skip`:它驗的是**這台機器的個人清單**,
出貨到下游只會天生帶紅(同 `test_upstream_manifest.py` 的理由)。
"""
from __future__ import annotations

import importlib.util
import os
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load(name):
    spec = importlib.util.spec_from_file_location(
        name + "_under_test", ROOT / ".claude" / "portable" / (name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ls = _load("leak_scan")
sc = _load("scanner")


# ─────────────────────────────────────────────────────────────────────────────
# 樣本一律**執行時拼裝**,不得靜置成文 —— 與 `test_scanner.py` 檔頭同一條家規。
#
# 這一檔比別處更需要它:本檔的合成樣本**就是設計來被 pattern 打中的**,
# 靜置成文的話 `leak_scan` 會擋下這個檔案自己的 commit。
# **第一次寫就是靜置的,pre-commit 當場擋下** —— 家規在這裡付了一次房租。
#
# 切點落在第一個詞的中間(`One` + `Drive…`),讓每一段靜置文字
# 都不是任何 pattern 的完整前綴。
# ─────────────────────────────────────────────────────────────────────────────
_OD = "One" + "Drive"

# 同類、不同字串。每一個都刻意與真樣本**沒有共用的具體字串**,
# 只共用結構 —— 這正是「不是過度擬合」的定義。
SAME_CLASS_DIFFERENT_STRING = [
    ("換資料夾名", r"C:\Users\x" + "\\" + _OD + "\\" + r"my-archive\a.txt"),
    ("換資料夾名(非拉丁)", "D:/data/" + _OD + "/專案備份/b.txt"),
    ("換深度", _OD + "\\" + r"deep\nested\c.txt"),
    ("換分隔符", _OD + "/another-folder/d.txt"),
]

# 不該中的:遮罩過的佔位符、以及把 OneDrive 當產品名講的散文。
# 少了這組,「一律命中」也會讓上面那組全綠 —— 而那條 pattern 會擋掉整份文件。
MUST_NOT_MATCH = [
    ("角括號佔位符", r"C:\...\ " + _OD + "\\" + "<備份資料夾>\\ "),
    ("星號遮罩", _OD + "\\" + "***已遮罩***\\ "),
    ("產品名散文", "資料放在 " + _OD + " 上面,會自動同步到筆電"),
]


def _personal_group():
    """只取**個人**那一組 —— 通用組不是本檔的對象。"""
    if not os.path.exists(ls.LOCAL_PATTERNS_FILE):
        pytest.fail(
            "找不到個人 pattern 清單,無法驗證防過度擬合。\n"
            "  這不是測試壞了,是**這台機器的涵蓋不完整** —— 而涵蓋不完整時\n"
            "  掃描報告仍然會是綠的(票 39 缺口二)。\n"
            "  修法:用票 22 的 age 匯出把清單帶過來;\n"
            "  **不得改成進版控**(裁決 2 鎖死條款)。")
    groups = [g for g in ls.load_patterns() if g.name == "個人"]
    if not groups:
        pytest.fail("個人清單存在但載不出任何 pattern —— 讀不到一律當違規。")
    return groups[0]


def _matches(group, text):
    return any(rx.search(text) for _raw, rx in group.patterns)


@pytest.mark.parametrize("label,sample", SAME_CLASS_DIFFERENT_STRING,
                         ids=[l for l, _ in SAME_CLASS_DIFFERENT_STRING])
def test_same_class_different_string_is_caught(label, sample):
    """**這一條紅 = 過度擬合。**

    它不是在說「掃描器漏了一個秘密」—— 合成樣本裡沒有秘密。
    它是在說:**那條 pattern 認得的是字串,不是形狀**,
    於是它只保得住我們已經知道的那一筆,對下一筆完全沒有作用。
    處置是**重寫 pattern**,不是把樣本加進清單。
    """
    assert _matches(_personal_group(), sample), (
        "同類但不同字串的樣本沒被抓到(%s)—— 這條 pattern 過度擬合了。\n"
        "     它認得的是字串不是形狀,對下一筆同類洩漏沒有作用。" % label)


@pytest.mark.parametrize("label,sample", MUST_NOT_MATCH,
                         ids=[l for l, _ in MUST_NOT_MATCH])
def test_redacted_and_generic_forms_are_not_flagged(label, sample):
    """**反控:遮過的與泛稱的不得命中。**

    少了這組,一條 `.` 也能讓上面四條全綠 —— 而那條 pattern 會把
    每一份提到 OneDrive 的文件都擋下來,然後被關掉。
    **被煩到的規則會被關掉**,所以誤判率是涵蓋率的一部分,不是另一件事。
    """
    assert not _matches(_personal_group(), sample), (
        "遮罩過/泛稱的形式被命中了(%s)—— 誤判會讓規則被關掉。" % label)


def test_the_escaped_form_is_documented_as_out_of_scope():
    """**跳脫形式不在範圍內** —— 這條釘住的是妥協聲明,不是功能(裁決 4)。

    K3 的真樣本是 JSON 跳脫(路徑分隔符是連續兩個反斜線)。
    現行 pattern **刻意只打未跳脫形式**,涵蓋跳脫要不要做是裁決者的事。

    將來若擴張到跳脫形式,本條會紅 —— **那時是刻意改它**,不是它壞了,
    而且要同時更新妥協聲明。
    """
    escaped = r'"cwd":"C:\\Users\\someone\\' + _OD + "\\\\" + r'some-folder\\x"'
    assert not _matches(_personal_group(), escaped), (
        "跳脫形式被命中了 —— 若是刻意擴張範圍,請一併更新妥協聲明"
        "(票 39 / ADR F-0015)。")
