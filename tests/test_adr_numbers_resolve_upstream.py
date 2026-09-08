# -*- coding: utf-8 -*-
"""票 116 B-8 的**上游專屬**那一半:被記錄的 ADR 編號在 `docs/adr/` 解析得到。

## 為什麼獨立成一檔,而且標 `skip` 不出貨

`tests/test_declared_in_is_an_identity.py` 驗的是**框架的性質** ——
`gate.py` 的呼叫點寫的是編號不是路徑。那件事在任何 repo 都成立,所以它標 `copy`。

**本檔驗的是資料**:「**這個 repo 的 `docs/adr/` 集合**跟得上 `gate.py` 的引用」。
而那在下游**不成立**,不是因為壞了,是因為設計:

  `docs/adr/` 在 portable-manifest 標 **`ask`** —— **安裝時不帶過去**。
  兩個下游手上那份停在裝機時那一版(2026-09-08 實測:兩邊都**沒有** `F-0016`)。

出貨的話它會在每個下游紅,**而那些紅與新專案無關 ⇒ 訓練人忽略訊號**(`F-031`)。
淨室 `verify_gates` 的收尾判準逐字:**框架測試只能斷言框架的性質。**

**前例**:`tests/test_adr_numbering.py` 同樣標 `skip`,同樣是 ADR 集合的性質。

> **票 114 收尾那一刀就是踩了這一格**(一條反控斷言「這個 repo 有票目錄」,
> 在淨室紅)。**這次是拆檔 + 標 skip,不是 loud skip** ——
> 因為那一次的條件是「有沒有票目錄」(同一個 repo 可能有可能沒有),
> 而這一次是「上游 vs 下游」(**由 manifest 的桶決定,是構造不是狀態**)。
> **能用構造消掉的不要用紀律管,也不要用 skip 管。**

## 它守得住什麼

**編號打錯。** 那是改成編號之後**新出現的**失敗方式:
路徑打錯至少還看得出來像個檔名(`docs/adr/0004-typo.md`),
**編號打錯就只是一個短字串**(`0O04`),而沒有東西會說話。
"""

import ast
import importlib.util
import io
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
GATE_SRC = ROOT / ".claude" / "hooks" / "gate.py"
ADR_DIR = ROOT / "docs" / "adr"


def _load_sibling():
    """借用同組那一檔的枚舉器,**不重寫一份**。

    重寫的話兩份會漂(`F-058`),而漂掉的那天兩邊都還是綠的。
    """
    spec = importlib.util.spec_from_file_location(
        "declared_in_identity_for_adr",
        ROOT / "tests" / "test_declared_in_is_an_identity.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_sib = _load_sibling()


def _recorded_numbers():
    out = []
    for lineno, reason, node in _sib._call_sites():
        form, _expect = _sib.CALL_SITE_FORMS.get(reason, (None, None))
        if form != _sib.ADR_NUMBER:
            continue
        out.append((lineno, reason, _sib._literal_or_none(node)))
    return out


def test_the_corpus_is_not_empty():
    """**反控**:掃到 0 個的話,底下那條恆綠。"""
    assert _recorded_numbers(), "一個 ADR 型呼叫點都沒掃到 —— 底下的斷言是空的"


def test_each_recorded_number_matches_exactly_one_adr_file():
    """每一個被記錄的編號,在 `docs/adr/` 底下**恰好**對應一個檔。

    「恰好一個」不是「至少一個」:兩個檔同前綴的話,
    帳本上那個編號**指向哪一個是不確定的**,而讀的人不會知道有這回事。
    """
    names = sorted(os.listdir(str(ADR_DIR)))
    bad = []
    for lineno, reason, num in _recorded_numbers():
        if not num:
            bad.append("gate.py:%d reason=%r 的 declared_in 不是字面值" % (lineno, reason))
            continue
        hits = [n for n in names if n.startswith(str(num) + "-")]
        if len(hits) != 1:
            bad.append("gate.py:%d reason=%r 編號 %r -> %d 個檔(要恰好 1 個):%s"
                       % (lineno, reason, num, len(hits), hits))
    assert not bad, "\n  ".join([""] + bad)


def test_a_wrong_number_would_be_caught():
    """**反控**:證明上一條會咬。拿一個公認不存在的編號,它必須對應到 0 個檔。"""
    names = sorted(os.listdir(str(ADR_DIR)))
    assert not [n for n in names if n.startswith("F-9999-")]


def test_the_dash_boundary_is_required():
    """比的是 `<編號>-`,不是 `<編號>` —— 否則 `0001` 會命中 `00010-…`。

    (票 101 裁 4 的同一條判準;票 114 刀三剛把三份找檔實作統一成它。)
    """
    names = sorted(os.listdir(str(ADR_DIR)))
    assert [n for n in names if n.startswith("0001-")], "語料前提不成立:沒有 0001-*"
    assert not [n for n in names if n.startswith("00010-")]


def test_this_file_is_not_shipped():
    """**釘住本檔自己標 `skip`** —— 它是本檔存在理由的機器保證。

    改成 `copy` 的那一天,它會在每個下游紅,而**改的人不會知道**。
    """
    table = io.open(str(ROOT / ".agents" / "portable-manifest.txt"),
                    encoding="utf-8").read()
    me = "tests/test_adr_numbers_resolve_upstream.py"
    hit = [l for l in table.splitlines() if l.strip().startswith(me)]
    assert len(hit) == 1, "本檔在 portable-manifest 裡不是恰好一行:%s" % hit
    assert hit[0].split()[-1] == "skip", (
        "本檔被標成 %r 而不是 skip —— 出貨的話它會在每個下游紅,"
        "因為 `docs/adr/` 標 ask 不出貨(見本檔 docstring)" % hit[0].split()[-1])
