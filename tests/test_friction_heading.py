# -*- coding: utf-8 -*-
"""`.claude/portable/friction_heading.py` —— portable 這一側的發號標題判準。

**本檔只問一件事:這份判準自己對不對。**
「它與 `gate.py` 那份一不一致」是另一個問題,由
`tests/test_gate.py::TestBothHeadingCriteriaAgree` 回答 ——
那條對帳**不住在這裡**,因為它的另一端是權威層,而本檔刻意不 import `gate.py`。

兩個問題分開的理由:一致可能是**一起錯**。
先釘住這一份自己對,再談兩份一致 —— 少了前者,對帳綠燈證明不了任何事。

framework-updates/98。
"""

import importlib.util
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / ".claude" / "portable" / "friction_heading.py"


def _load():
    spec = importlib.util.spec_from_file_location("friction_heading_ut", SRC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


fh = _load()


class TestItSeparatesIssuingANumberFromMentioningOne:
    """**發一個號** vs **提到一個號** —— 分開的條件有兩個,缺一不可:
    前綴必須是字母、號碼必須緊接在 `## ` 之後。
    """

    @pytest.mark.parametrize("line", [
        u"## F-118 甲",
        u"## TSI-038 前哨在場的三段驗收",
        u"## F-005",                      # 行尾就結束,沒有後續文字
    ])
    def test_an_issuing_heading_is_recognised(self, line):
        assert fh.HEADING.match(line) is not None, line

    @pytest.mark.parametrize("line", [
        u"## 併記於 F-118(2026-08-26):那次相撞真的發生了",  # 號碼不在開頭
        u"## 這份規則(附決策)",                              # 根本沒有號碼
        u"見 F-005 與 F-005 的討論",                          # 不是 `## ` 開頭
        u"### F-118 甲",                                      # 三級標題不是發號位置
        u"## 118 甲",                                         # 沒有字母前綴
    ])
    def test_merely_mentioning_a_number_is_not_recognised(self, line):
        assert fh.HEADING.match(line) is None, (
            "%r 被判成發號 —— 而 `sync` 用這個判準做差集,"
            "把散文標題當成條目號碼的後果是整次更新被拒絕(framework-updates/98)" % line)

    def test_the_captured_group_is_the_number_itself(self):
        """**擷取到的要是號碼本身**,不是整行。

        差集是拿這個群組去比的:擷取錯了,兩份表比的就不是同一種東西,
        而那個錯誤在「有沒有重複」這個問題上是靜默的。
        """
        assert fh.HEADING.match(u"## F-118 甲").group(1) == u"F-118"
        assert fh.HEADING.match(u"## TSI-038 前哨").group(1) == u"TSI-038"

    def test_a_number_like_prefix_is_not_swallowed_by_a_longer_word(self):
        """**邊界**:`## F-118x 甲` 不得被讀成 `F-118`。

        少了邊界條件,一個打錯的號碼會靜靜地被算成另一個號碼 ——
        而差集看不見那種錯,它只看見兩個相同的字串。
        """
        assert fh.HEADING.match(u"## F-118x 甲") is None
