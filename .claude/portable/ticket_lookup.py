# -*- coding: utf-8 -*-
"""依票號找票檔 —— **portable 這一側的唯一一份**(票 114 刀三 B-2)。

在它之前,portable 側有**兩份各自的實作**:

    `status._find_ticket_file`   給人看(印 `ticket file <路徑>` 那一行)
    `mcp_server._ticket_path`    端內容(把票檔原文回給 Claude Desktop)

兩份對 2026-09-08 那組語料答案全同 —— **而那是巧合,不是保證**。
同缺陷的兩份實作必然漂開(`F-058` 家族),所以收成一份。

## ⚠ 為什麼 `gate` 不在其中

`.claude/hooks/gate.py` 的 `ticket_untested_modules` 做同一件事,
**而它刻意不共用**(票 42):

> 權威層要依賴最少的東西 —— 讓它 import `portable/` 會多一個失效點,
> 而閘門起不來的樣子跟沒裝一模一樣(全靜默)。

而且那一支**不只找檔**:它同時讀「Untested by decision」宣告、驗票在不在 HEAD,
找檔只是內嵌在迴圈裡的一段,沒有獨立的函式邊界。
兩邊的行為一致由 `tests/test_ticket_path_parity.py` 釘住 —— **綁行為,不綁字面。**

## 契約

    find(dirs, ticket) -> 絕對路徑字串 或 None

**回絕對路徑。** 三個呼叫端原本兩種形式(`status`/`mcp` 絕對、`gate` 相對),
契約不寫死的話每個呼叫端都要猜,而猜錯不會有東西說話。
要相對路徑的呼叫端自己折。

`dirs` 是**已展開且存在**的目錄清單(絕對路徑)。**本模組不讀 `gate` 的那份模板** ——
來源留在各自的呼叫端:`status` 從它已載入的 gate 模組取,
`mcp_server` 用自己的同名常數(那份的一致性由它自己的對帳測試釘)。
傳進不存在的目錄不得炸,只是跳過(呼叫端與本模組之間會有時間差)。

## ⚠ 硬性約束:這支不得長出相依(裁 3,見 `mcp_server.py:10-20`)

`mcp_server` 會 import 它,而那個行程**從頭到尾不得有 `gate`、不得自己開 git**:

    不 import gate / status,不開 git,不跑子程序,只靠 `os`。

`mcp_server.py:12-14` 逐字:「`status.render()` 會 `exec_module` 目標 repo 的
`gate.py`,而 `render_all` 會開 git。**走子程序不是效能取捨,是把那兩件事
關到另一個行程去**」。這支若長出那些相依,那道隔離就從 import 這一側被繞過了。

**守它的是 `tests/test_ticket_lookup.py::TestTheModuleStaysDependencyFree`,
不是上面這段散文** —— 散文不是機制。

## 兩條判準,缺一不可

**一、前綴要帶邊界**:比的是 `<號>-`,不是 `<號>`(票 101 裁 4)。
裸前綴下 `"1"` 命中 `10-*.md`,而本 repo 的票號補零到兩位,
`"1"` 這個字串不對應任何票。**回錯一份票比回不出來糟得多** ——
回不出來的人會再查,拿到一份看起來對的票的人不會。

**二、副檔名要是 `.md`**:票檔是 `.md`。少了這一條,票目錄裡任何一個
`<號>-` 開頭的檔案都會被當成票 —— 而 `gate` 那一側拿它去**發 R3 豁免**
(票 114 實測:`114-a.txt` 的 sorted 位置在 `114-c.md` 之前,於是蓋掉真票)。

**⚠ 補零不在這一層。** `find(dirs, "1")` 回 `None` 是正確行為 ——
這裡只答「這個字串有沒有邊界命中」。補零是呼叫者對**本 repo 命名慣例**的知識,
下游 repo 不見得補零,埋進來會在別的 repo 出錯。
需要補零的呼叫端自己試兩式(`mcp_server.ticket()` 就是那樣做的)。
"""

import os


def find(dirs, ticket):
    """`dirs` 裡第一個 `<ticket>-` 開頭且 `.md` 結尾的檔的絕對路徑。找不到回 `None`。

    目錄按 `dirs` 的順序找,同一個目錄內按檔名排序找 ——
    **順序由呼叫端的清單決定**,不是由檔名決定哪個目錄贏。
    """
    if not ticket:
        return None
    prefix = str(ticket) + "-"
    for d in dirs:
        try:
            names = sorted(os.listdir(d))
        except OSError:
            # 目錄不在(或讀不動)只是跳過 —— 一個例外會讓整份輸出消失,
            # 只為了一格算不出來(`status._ticket_dirs` 記過同一句)。
            continue
        for name in names:
            if name.startswith(prefix) and name.endswith(".md"):
                return os.path.join(d, name)
    return None
