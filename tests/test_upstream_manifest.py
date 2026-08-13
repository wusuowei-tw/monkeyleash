# -*- coding: utf-8 -*-
"""上游標記表的完整性 —— **這個檔案不隨框架出貨**(manifest 標 skip)。

## 為什麼不出貨

「每一個追蹤檔案都要有標記」是**上游**的性質,不是每個 repo 的性質。

上游(agent-gates)是 sync 的**來源**,所以它的每一個檔案都必須有明確歸屬:
漏一筆的後果不是漏帶,是**拿它去覆蓋下游的同名檔**(票 15、F-077)。

裝了框架的 repo 不是任何人的來源。它裡面住著整個宿主專案 ——
`myapp/`、`analyst_tracker/`、它自己的測試。要求那些檔案全部進標記表,
是把上游的職責攤到每一個下游身上,而且**天生帶紅**:
新裝的 repo 第一次跑測試就看到一條與它做的事無關的紅。

實測(2026-08-13):空白 repo 裝完是綠的;而一個先有 `myapp/core.py`、
`myapp/util.py` 的 repo 裝完立刻紅在這條上。**影音正是後者。**

## 為什麼這是「判錯對象」的第五例

規則要問的是「**上游**有沒有漏分類」,而我原本量的是
「**這個 repo** 裡有沒有未分類的檔案」。在 agent-gates 兩者重合,
在任何裝了框架的 repo 分岔 —— 又一次多數情況重合、邊界分岔
(F-075 的對照表)。

## 為什麼不用 `in_scope()` 圈範圍

`in_scope()` 的定義就是「表裡有前綴命中它」,所以
「每個 in_scope 的檔案都有標記」是套套邏輯,驗不出任何東西(F-032 的形狀)。
範圍不能用「已經被分類」來定義。

分檔是現成、且用既有機制的解:標記表自己就有 `skip`,意思正是
「這個檔案只屬於這個 repo」。
"""

import importlib.util
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _manifest():
    spec = importlib.util.spec_from_file_location(
        "manifest_for_upstream_test", ROOT / ".claude" / "portable" / "manifest.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _table(m):
    return m.load_table(str(ROOT / ".agents" / "portable-manifest.txt"))


def test_every_tracked_file_is_classified():
    """**上游不得有任何未分類檔案。**

    守的是「下一個人新增檔案卻忘了分類」—— 我自己在批次二漏過一筆
    (`docs/agents/adr-numbering.md`),而那一筆會被 sync 拿去覆蓋下游的同名檔。
    """
    m = _manifest()
    table = _table(m)
    out = subprocess.run(["git", "ls-files", "-z"], cwd=str(ROOT),
                         capture_output=True)
    rels = [p for p in out.stdout.decode("utf-8", "replace").split("\0")
            if p.strip()]
    assert rels, "git ls-files 回空 —— 掃不到東西的綠燈不算綠燈"
    unclassified = [p for p in rels if m.explicit_mark(p, table) is None]
    assert not unclassified, (
        "這些檔案沒有標記,更新路徑會拿它們去覆蓋下游的同名檔:\n  %s"
        % "\n  ".join(unclassified))


def test_this_file_does_not_travel():
    """**本檔必須標 `skip`。**

    這條是上面那條能存在的前提:它一旦出貨,每個裝了框架的 repo
    都會天生帶著一條與自己無關的紅,而**出生即紅會訓練人忽略訊號**(F-031)。
    被訓練出來的那個習慣,下次會濾掉一條真的紅。
    """
    m = _manifest()
    assert m.explicit_mark("tests/test_upstream_manifest.py", _table(m)) == "skip"
