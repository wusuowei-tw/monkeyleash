# -*- coding: utf-8 -*-
"""票 89 第 2 條 —— **`0013` 起的 ADR 必須帶前綴**,而在本檔之前沒有機器擋著。

由來:`docs/audits/2026-08-28-f110-inventory.md` 第 2 條。
`docs/agents/adr-numbering.md:33` 逐字自承:

    **沒有機器擋著「有人又發了一個裸號」。** 目前只有這份文件在約束。
    `0013` 之後出現裸號會靜默通過 —— 而靜默正是這套東西一路在修的東西。

## 為什麼這條可以做,而且便宜

判定的對象是**檔名** —— `CLAUDE.md` 那條「封閉集合用枚舉,不用 pattern」
列的封閉集合之一。零判斷、零誤報:一個檔名要嘛帶前綴,要嘛沒有。

## ⚠ 狀態欄:**叫的時機太晚**,不是「已守住」

本檔掛在測試層,而測試層繼承盤點表第 11 條(元缺口):
`.githooks/pre-commit` 只跑 `leak_scan --staged` 與 `gate.py --pre-commit`,
**不跑 pytest**;CI 只在 push / PR to master 觸發。
所以違反的**當下**沒有東西會叫 —— 收票時**不得**把這條記成「已守住」。

同一件事在本庫是**量到的**,不是推的:`CLAUDE.md` 正典段的六條漂移偵測
由 21 條測試守著,而它的實際狀態仍然是「叫的時機太晚」(見盤點表第四節對照組)。

## 為什麼沒有紅燈先行

**本檔沒有生產模組:它的實作就是斷言本身**,而現況已經全綠(15 份 ADR 都合規)。
照字面造一個紅燈只有兩條路,兩條都是造假(票 53 B1/B2 已裁過同一個形狀):
先寫 `assert False` 是**假紅燈**(紅的原因與要抓的缺陷無關);
先把一個裸號檔案放進 `docs/adr/` 是**真的製造缺陷**。
替代物是**合成負對照** —— 見 `test_a_bare_number_after_the_switch_point_is_caught`。
少了它,一個 `assert True` 的實作也會全綠。
"""
from __future__ import annotations

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
ADR_DIR = ROOT / "docs" / "adr"

# **凍結白名單,不是「小於 13 就放行」。**
# 寫成範圍的話,`0009` 被刪掉之後範圍仍然涵蓋它,而清單會少一項且沒有人知道
# (`F-137`:一份清單不會帶著它自己的長度)。逐項列出來,長度就看得見。
#
# 出處:`docs/agents/adr-numbering.md:21`「`0001`–`0012` 維持裸號,不追溯改名」。
# 理由同檔:已經發出去的號碼被引用在 ADR 內文、CLAUDE.md、`gate.py` 的
# `RULE_DIVERGENCE`、票、friction log 裡,而**漏改是靜默的**。
FROZEN_BARE = frozenset(
    "%04d" % n for n in range(1, 13)
)

# 框架層用 `F-`;每個安裝的 repo 用自己的三字母前綴(`TSA-` / `TSI-`),
# 而**前綴進號碼本身**(`docs/agents/adr-numbering.md:9-13`)。
# 本檔標 `copy`,所以判準要對下游同樣成立 —— 只認 `F-` 的話,
# 下游第一次發自己的 ADR 就會被自己的測試擋下。
PREFIXED = re.compile(r"^[A-Z]{1,3}-\d{4}-")
BARE = re.compile(r"^(\d{4})-")


def classify(name):
    """回 `"prefixed"` / `"frozen"` / `"bare"` / `"unknown"`。

    **`unknown` 不併進任何一邊。** 併進 `bare` 會讓一個命名慣例之外的檔案
    被報成裸號(訊息指錯方向);併進 `prefixed` 則是把沒判定過的東西
    當成合格 —— 票 67 那 72 筆「無法判定」的同一句話:
    **留白比蓋章誠實。**
    """
    if PREFIXED.match(name):
        return "prefixed"
    m = BARE.match(name)
    if m:
        return "frozen" if m.group(1) in FROZEN_BARE else "bare"
    return "unknown"


def _adr_names():
    return sorted(p.name for p in ADR_DIR.glob("*.md"))


class TestAdrNumbersCarryTheirPrefix:

    def test_the_adr_directory_is_not_empty(self):
        """**先證明有東西被掃。**

        空目錄會讓底下每一條斷言 vacuously 通過,而
        「掃過沒事」與「什麼都沒掃」在畫面上一模一樣(`F-134`)。
        """
        assert _adr_names(), "docs/adr/ 掃不到任何 .md —— 是路徑錯了,不是全部合規"

    def test_no_bare_number_after_the_switch_point(self):
        """本檔的正題。"""
        bare = [n for n in _adr_names() if classify(n) == "bare"]
        assert not bare, (
            "這些 ADR 用了裸號,而切換點在 `0013`(docs/agents/adr-numbering.md:29):\n"
            "  %s\n"
            "  框架層用 `F-`,安裝的 repo 用自己的三字母前綴,**前綴進號碼本身**。"
            % "\n  ".join(bare))

    def test_nothing_is_unclassified(self):
        """命名慣例之外的檔案要浮上來,**不得預設放行**(票 15 同一條)。"""
        unknown = [n for n in _adr_names() if classify(n) == "unknown"]
        assert not unknown, (
            "這些檔名不符合任何一種 ADR 命名形態,判不出來:\n  %s\n"
            "  判不出來不等於合格 —— 要嘛改名,要嘛把慣例補進 adr-numbering.md。"
            % "\n  ".join(unknown))

    def test_the_frozen_whitelist_still_matches_reality(self):
        """凍結清單本身會過期 —— **而過期時沒有東西會說**。

        白名單列了 12 個號,若其中某一號的檔案被刪掉或改名,
        清單會靜靜地多出一個指向不存在檔案的條目
        (與盤點表第 6 條、票 90 的死 sha 同一個形狀:**指標壞了沒有人會叫**)。
        """
        present = {m.group(1) for m in
                   (BARE.match(n) for n in _adr_names()) if m}
        missing = sorted(FROZEN_BARE - present)
        assert not missing, (
            "凍結白名單列了這些裸號,而 docs/adr/ 裡沒有對應檔案:%s\n"
            "  清單過期了 —— 回去對一次 docs/agents/adr-numbering.md:21。"
            % ", ".join(missing))

    # ── 合成負對照:少了這組,`assert True` 也會全綠 ──────────────────
    @pytest.mark.parametrize("name", [
        "0013-something-new.md",
        "0099-much-later.md",
        "0013-F-not-a-prefix.md",
    ])
    def test_a_bare_number_after_the_switch_point_is_caught(self, name):
        assert classify(name) == "bare", name

    @pytest.mark.parametrize("name", [
        "F-0013-r3-redlight-judges-the-implementation.md",
        "F-0100-much-later.md",
        "TSA-0001-downstream.md",
        "TSI-0042-downstream.md",
    ])
    def test_a_prefixed_number_is_accepted(self, name):
        """**反控的另一半:合法的不得被擋。**

        只驗「壞的抓得到」的話,一條 `return "bare"` 的判定也會通過上面那組,
        而它會擋掉每一份合規的 ADR。
        """
        assert classify(name) == "prefixed", name

    @pytest.mark.parametrize("name", ["0001-refactoring.md", "0012-shadow.md"])
    def test_the_frozen_bare_numbers_are_not_flagged(self, name):
        assert classify(name) == "frozen", name

    @pytest.mark.parametrize("name", ["README.md", "index.md", "draft.md"])
    def test_an_unrecognised_shape_is_not_silently_accepted(self, name):
        assert classify(name) == "unknown", name
