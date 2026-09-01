# -*- coding: utf-8 -*-
"""friction log 的**發號標題**判準 —— portable 這一側的唯一一份。

`## F-123 …`、`## TSI-038 …` 是**發一個號**;
`## 併記於 F-118(…)` 與 `見 F-005 與 F-005 的討論` 是**提到一個號**。
兩者要分開,而分開的條件有兩個,缺一不可:

  1. 前綴必須是**字母**(`[A-Za-z]+`)
  2. 號碼必須**緊接在 `## ` 之後**

## 為什麼這一份存在(framework-updates/98)

在它之前,portable 這一側有**兩份各自的字面**:

  `sync.py:38`          `^## (\\S+)`    ← **鬆**:`## ` 之後第一個非空白詞就算號碼
  `verify_gates.py:118`  與 `gate.py` 逐字相同,而是 inline 的第二份

鬆的那一份把 `## 併記於 F-118(…)` 解析成一個叫 `併記於` 的號碼。
friction log 裡有**兩則**那樣的標題(`F-118` 與 `F-145`,兩個不同的號),
於是 `sync` 判定「同一個號碼出現兩次」而**拒絕整次更新** ——
2026-08-31 實測,`exit=1`。

**`sync` 沒有壞:`exit=1` + 說出缺的前提 = fail-closed 正確作動。
壞的是判準的對象。所以修法不是放寬它,是讓兩邊看同一份判準。**

## ⚠ 為什麼**不**與 `gate.py` 共用(票 42)

`.claude/hooks/gate.py:1283` 有一份語意相同的 `_FRICTION_HEADING`,
而它**刻意保持獨立**。理由逐字寫在 `tests/test_gate.py` 那條
`test_both_staged_listings_agree_on_a_gitlink` 的 docstring 裡:

> **兩份是刻意保留的,不是還沒清掉的重複**(票 42 裁決):
> 權威層要依賴最少的東西 —— **讓它 import `portable/` 會多一個失效點,
> 而閘門起不來的樣子跟沒裝一模一樣**(全靜默)。

**看到這個重複想合併之前,先讀那則裁決。**

**同缺陷的兩份實作必然漂開**(`F-058` 家族),所以有一條測試釘住兩者對同一組
標題行給出**相同判定** —— `tests/test_gate.py::TestBothHeadingCriteriaAgree`。
**綁的是行為,不是字面。**
"""

import re

# 與 `.claude/hooks/gate.py` 的 `_FRICTION_HEADING` **語意相同**。
# 兩者不共用程式碼(票 42),由上述那條對帳測試釘住行為一致。
HEADING = re.compile(r"^##\s+([A-Za-z]+-\d+)(?:\s|$|[^\w-])")
