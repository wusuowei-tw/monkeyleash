# -*- coding: utf-8 -*-
"""票 89 第 3 條 —— **`KNOWN_GAPS` 每一項必須有票號**,而在本檔之前只有註解。

由來:`docs/audits/2026-08-28-f110-inventory.md` 第 3 條。
門檻**逐字寫在那個結構旁邊**(`.claude/portable/g1_verify.py`):

    ⚠ 進這一桶的門檻:必須有**票號**。沒有票的缺口不叫已知缺口,叫沒人管的洞。

**而它只是註解,沒有測試在守。** 資料就在同一個檔的同一個 list 裡 ——
不必讀 git、不必解析散文,這是整份盤點裡最便宜的一條。

## 這一桶為什麼需要守

`KNOWN_GAPS` 是**把已知漏擋編碼進驗收工具**的地方:它裡面的每一條
在 `g1_verify` 跑起來時是「放行 = 通過」。一條**沒有票**的條目,
等於把一個缺口永久合法化,而且 `g1_verify` 會為它印一行綠字。

> **一個缺口進了這一桶而沒有票,它就從「待修」變成「規格」——
> 而那個轉變沒有任何人簽名。**

`KNOWN_GAPS` 是**會長的**:第 2 項是 2026-08-28 當天才加的(`056bcd3`)。

## ⚠ 狀態欄:**叫的時機太晚**,不是「已守住」

本檔掛測試層,繼承盤點表第 11 條(元缺口)——`pre-commit` 不跑 pytest。
違反的**當下**沒有東西會叫。收票時**不得**記成「已守住」。

## 為什麼沒有紅燈先行

同 `tests/test_adr_numbering.py` 檔頭:**本檔沒有生產模組,實作就是斷言本身**,
而現況已經全綠(2 項都有票)。替代物是**合成負對照**——
見 `test_a_gap_without_a_ticket_is_caught`。

## ⚠ 本檔不讀保護清單

`g1_verify` 的 `protected_entries()` 會讀 `~/.claude/g1-protected.txt`,
而票 88 八之一的界線 A 是 **agent 對受保護路徑一律不碰,連 `ls` 都不**。
本檔只 import 模組並讀它的 `KNOWN_GAPS` 常數 ——
**`protected_entries()` 不在 import 期被呼叫**(實查:它是函式,`main()` 才用),
所以載入本身不碰那個檔。**不得**在本檔加任何會走到那條路的斷言。
"""
from __future__ import annotations

import importlib.util
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load_g1_verify():
    spec = importlib.util.spec_from_file_location(
        "g1_verify_under_test", ROOT / ".claude" / "portable" / "g1_verify.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


g1v = _load_g1_verify()

# 票號的形狀:框架票(`票 88`)、framework friction(`F-139`)、
# 或安裝 repo 的三字母前綴號(`TSI-029`)。
# **不接受空字串、不接受純散文** —— 那正是這條要擋的東西。
TICKET = re.compile(r"(票\s*\d+|\bF-\d+|\b[A-Z]{3}-\d+)")


def has_ticket(value):
    return bool(value) and bool(TICKET.search(str(value)))


class TestEveryKnownGapCarriesATicket:

    def test_the_bucket_is_not_empty(self):
        """**先證明有東西被檢查。**

        `KNOWN_GAPS` 空掉的話底下每一條都 vacuously 通過,
        而「全部合規」與「一項都沒有」在畫面上一模一樣(`F-134`)。
        空掉本身也值得出聲:那代表有人把缺口刪了而沒有收票。
        """
        assert g1v.KNOWN_GAPS, "KNOWN_GAPS 是空的 —— 是缺口都修好了,還是條目被刪了?"

    def test_every_entry_has_the_expected_shape(self):
        """三欄:`(label, cmd, ticket)`。

        **形狀先驗**:少一欄的話下面那條會 `IndexError` 而不是給出可讀的失敗,
        而一個看不懂的失敗訊息,人會照著繞不是照著修(`F-031`)。
        """
        for entry in g1v.KNOWN_GAPS:
            assert isinstance(entry, tuple) and len(entry) == 3, (
                "KNOWN_GAPS 條目應為 (label, cmd, ticket) 三欄,實得:%r" % (entry,))

    def test_every_gap_carries_a_ticket_number(self):
        """本檔的正題 —— `g1_verify.py` 檔頭那句話的機器版。"""
        naked = [(lb, tk) for lb, _cmd, tk in g1v.KNOWN_GAPS
                 if not has_ticket(tk)]
        assert not naked, (
            "這些已知缺口沒有票號:\n  %s\n"
            "  門檻逐字寫在 .claude/portable/g1_verify.py 的 KNOWN_GAPS 檔頭:\n"
            "  **沒有票的缺口不叫已知缺口,叫沒人管的洞。**"
            % "\n  ".join("%s -> %r" % (lb, tk) for lb, tk in naked))

    def test_the_sample_command_uses_a_harmless_verb(self):
        """順帶守住同一段檔頭的第二句家規:**樣本一律用無害動詞。**

        理由寫在那裡:第一級**不分讀寫、判準是路徑**,所以讀取就足以示範缺口;
        而這一格**隨 `copy` 進每一個下游 repo** ——
        不該在別人的樹裡放一條 `rm -rf` 樣本。

        ⚠ **既有那條 UNC 樣本(票 80)保留原樣**,照票 80「舊文不改」——
        所以它列在例外裡,而例外**逐條列出**、不是一個範圍。
        """
        GRANDFATHERED = {"bash 寫法 UNC"}
        DESTRUCTIVE = re.compile(
            r"\b(rm|del|rmdir|rd|Remove-Item|shutil\.rmtree|mkfs|dd)\b")
        offenders = [(lb, cmd) for lb, cmd, _tk in g1v.KNOWN_GAPS
                     if lb not in GRANDFATHERED and DESTRUCTIVE.search(cmd)]
        assert not offenders, (
            "這些樣本用了破壞性動詞,而它們會隨 copy 進下游的樹:\n  %s"
            % "\n  ".join("%s -> %s" % (lb, c) for lb, c in offenders))

    # ── 合成負對照:少了這組,`assert True` 也會全綠 ──────────────────
    @pytest.mark.parametrize("ticket", [
        "", None, "待補", "TODO", "以後再說", "見上",
    ])
    def test_a_gap_without_a_ticket_is_caught(self, ticket):
        assert not has_ticket(ticket), repr(ticket)

    @pytest.mark.parametrize("ticket", [
        "票 88", "票80(裁 A 明訂不動)", "F-139", "TSI-029", "見票 12 與 F-100",
    ])
    def test_a_gap_with_a_ticket_is_accepted(self, ticket):
        """**反控的另一半:合法的不得被擋。**

        只驗「壞的抓得到」的話,一條 `return False` 的判定也會通過上面那組,
        而它會擋掉每一個合規的條目。
        """
        assert has_ticket(ticket), repr(ticket)
