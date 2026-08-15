# -*- coding: utf-8 -*-
"""票 34 —— pytest 版本上限,以及讓上限過期時**會出聲**的機制。

裁決選 A(設上限)。A 的代價票面寫得很清楚:

    上限會過期。而過期的上限**不會出聲** —— 它只是安靜地擋住升級,
    直到有人去查為什麼裝不上新版。

所以「設上限」不是一行相依宣告就結束的事:光設上限只是**把靜默換個地方** ——
從「兩台機器版本不同」換成「新版裝不上而沒人知道為什麼」。
這一檔就是那個「會出聲」的部分。

三條各守一件事:

1. 上限**還在**(有人把它刪掉會紅)
2. **實際裝的**那一版落在宣告的區間裡(繞過宣告硬裝會紅)
3. 複審日**還沒過**(到期會紅,並給出複審程序)

刻意不用 `tomllib`:`requires-python` 是 `>=3.10`,而 `tomllib` 是 3.11 才進標準庫。
在 3.10 上 `skip` 掉等於這一檔在最舊的支援版本上靜靜消失 —— 那正是本檔在防的東西。
兩個要讀的值都是單行、格式由本 repo 自己定,直接讀原文比引入版本分歧安全。
"""
from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path

import pytest

PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"

# 宣告形如:"pytest>=8.0,<10"
SPEC_RE = re.compile(r'"pytest>=(?P<low>[0-9][0-9.]*),<(?P<high>[0-9][0-9.]*)"')
REVIEW_RE = re.compile(
    r'^pytest-ceiling-review\s*=\s*"(?P<date>\d{4}-\d{2}-\d{2})"', re.M
)

_HOWTO = (
    "複審程序:\n"
    "  1. `python -m pip install -U pytest` 裝下一個大版本\n"
    "  2. `python -m pytest` 跑全套\n"
    "  3. 全綠 -> 把 pyproject.toml 的上限與複審日**一起**往上推\n"
    "     有紅 -> 上限留著,把紅的成因寫進票 34,複審日往後推並註明理由\n"
    "不要只改日期不做 1-2 步 —— 那會把這條測試變成一個沒有內容的儀式。"
)


def _text() -> str:
    return PYPROJECT.read_text(encoding="utf-8")


def _version_tuple(v: str) -> tuple[int, ...]:
    return tuple(int(p) for p in v.split(".") if p.isdigit())


def test_pytest_dependency_declares_an_upper_bound() -> None:
    """上限被刪掉時要紅。

    這是三條裡唯一守「決定本身」的:另外兩條都預設上限存在。
    """
    m = SPEC_RE.search(_text())
    assert m is not None, (
        "pyproject.toml 的 dev 相依讀不到 `pytest>=X,<Y` 形狀的宣告。\n"
        "要嘛上限被拿掉了,要嘛格式改了而這條測試沒跟著改。\n"
        "兩種都不能靜靜過去 —— 上限沒了,兩台機器就會再次跑不同的大版本(票 34)。"
    )


def test_installed_pytest_is_inside_the_declared_range() -> None:
    """實際裝的那一版必須落在宣告的區間裡。

    宣告只在**透過宣告安裝**時有效。手動 `pip install -U pytest` 繞得過去,
    而繞過去之後一切照跑 —— 這條就是那個情況唯一的聲音。
    """
    m = SPEC_RE.search(_text())
    assert m is not None, "先看 test_pytest_dependency_declares_an_upper_bound"
    low, high = _version_tuple(m["low"]), _version_tuple(m["high"])
    installed = _version_tuple(pytest.__version__)

    assert low <= installed < high, (
        "實際安裝的 pytest %s 落在宣告區間 [>=%s, <%s) 之外。\n"
        "宣告只約束「照宣告安裝」的路徑,手動升級繞得過去 —— 這條是那個情況的聲音。\n"
        "如果是刻意要試新大版本,那就是一次複審:\n%s"
        % (pytest.__version__, m["low"], m["high"], _HOWTO)
    )


def test_ceiling_review_date_has_not_passed() -> None:
    """複審日到了就紅 —— 這是「上限過期會出聲」的那個機制本身。

    一條會在某天自己轉紅的測試是刻意的:上限的危害正是**它不會自己出聲**,
    而唯一不依賴外部網路、不依賴有人想起來的辦法,就是讓時間本身當觸發器。
    """
    m = REVIEW_RE.search(_text())
    assert m is not None, (
        "pyproject.toml 讀不到 `pytest-ceiling-review = \"YYYY-MM-DD\"`。\n"
        "沒有複審日的上限就是一個不會出聲的上限(票 34 的整個代價都在這裡)。"
    )
    review = _dt.date.fromisoformat(m["date"])
    today = _dt.date.today()

    assert today <= review, (
        "pytest 上限的複審日 %s 已經過了(今天 %s)。\n"
        "這條紅燈不是壞掉,是它在做它被寫出來要做的事。\n%s" % (review, today, _HOWTO)
    )
