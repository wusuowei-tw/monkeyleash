# 160 — 找不到實作被記成「實作不存在」，R3 Python 路徑因此略過 HEAD 雜湊比對

**狀態**：**160-b 實作完成（本機），待獨立審查。**
**來源**：票 159 獨立審查 N1（2026-10-22）；Jeff 2026-10-22 約 07:58（美東）決定另開票登記，之後再修，連同 K3 一起看（裁決助手記錄，非逐字原話）。
**相關**：K3（`find_implementation` 取第一個同名檔）、`F-167`、票 159。

---

## 一、現象

`redlight.record_run` 拿到 `find_implementation` 回的 None 時，寫出 `impl_file: null, impl_exists: false, impl_hash: null`；`gate.redlight_missing` 的 Python 路徑看到 `impl_exists` 為 False 就直接放行，不走 HEAD 雜湊比對。於是「找不到實作」與「實作不存在（新檔）」混成同一種紀錄。

## 二、影響

票 159 讓 None 變多，這個混同的影響面跟著變大。

## 三、可能方向（未裁）

- `impl=None` 時 `impl_exists` 記為 null；
- 或 R3 那側改用實作檔是否存在於 HEAD 來判定。

兩者都要動 gate.py（權威層），需裁決。

## 四、裁決

（裁決助手記錄，非逐字原話。）

**Jeff 2026-10-22 約 09:05（美東）裁定：票 160 採 (b′)。**

- Python 路徑的 R3 紅燈出口「`impl_exists is False` ⇒ 放行」加一個條件：**而且 `impl_rel` 確定不在 HEAD**，才放行。
- 「在不在 HEAD」用三態判定（gate 既有的 `_git_object_exists` 或等價做法）：
  - 確定不在 ⇒ 可放行；
  - 確定在 ⇒ 不走此出口，改走 HEAD 雜湊出口；
  - 問不動（不是 git、git 失敗、`impl_rel` 為 None）⇒ 不放行。
- 純收緊。只改 `gate.redlight_missing` 的 Python 分支（160-b）；紀錄器（redlight.py）與帳本格式不動；非 Python（Kotlin／Dart）路徑不動。K3 不在本票。

**R0 報告**：完整帳本 7737 筆，impl_exists False 4506 筆，其中紅燈 94 筆；帳本無法區分其中新檔與找不到各幾筆。

**Jeff 2026-10-22 約 13:06（美東）裁定 A：准許「修改三」，只限 P1、P2。**

- P1：`TestR3ReadsRedlight::test_a_proper_red_then_green_sequence_passes`；P2：`TestRedlightAcceptsTheSameTestLocationsAsR3::test_a_sibling_test_file_can_satisfy_the_redlight_half`。
- 修改三：呼叫補上 `impl_rel=<確定不在 HEAD 的路徑>`，setup 改成真 git repo（patch `ROOT`）；「放行」的預期（`is None`）不變。
- 只限 P1、P2 的理由：這兩條測的不是本票形狀，只是呼叫時沒給 `impl_rel`；生產環境唯一呼叫點（`gate.check()`）恆傳 `impl_rel`。

**Jeff 2026-10-22 約 15:14（美東）裁定：全新、還沒有任何 commit 的 repo（HEAD 指向尚未誕生的分支），算「問不動」⇒ 擋。**

- 代價：全新 repo 要先 commit 一個初始版本，才能寫第一支 Python 實作。
- 判定只看「HEAD 是否指向一個存在的 commit」，不另外分辨「全新」與「git 壞掉」——兩者都擋。

**實作時的判定細節（160-b，審查者 2026-10-22 約 15:15（美東）經 Jeff 轉達）：**

- 「不是 git」要另外判：`_git_object_exists` 在非 git 目錄回 `(False, None)`（它自己的 docstring 寫明），只靠它的話「不是 git」會被判成「確定不在」而放行。
- `ROOT` 必須就是 git 找到的工作樹根目錄（`git rev-parse --show-toplevel` 正規化後等於 `ROOT`）；不相等或查詢失敗 ⇒ 問不動。
- gitlink 範圍：落在 gitlink（子模組）底下、而且拿不到其 HEAD 內容時，不准走 not-found 出口；既有的 HEAD 雜湊出口保留（不是「gitlink 底下一律擋」）。gitlink 清單取不到（git 失敗、輸出無法解析、無法確認路徑歸屬）也算問不動。

**Jeff 2026-10-22 約 15:23（美東）授權：共用那一行可改，非 Python 結果不變，由測試與獨立審查確認。**

- 160-b 改到了 Python 與非 Python 共用的 not-found 出口那一行（條件加上 `(absent or not python)`）；非 Python 時 `absent` 恆為 False、`not python` 恆為 True，結果不變。這不是「一字不動」。

## 五、修正紀錄

- 2026-10-22（美東）：立案（候選）。
- 2026-10-22（美東）：記錄裁決 (b′) 與修改三；160-a 紅燈測試（錨點 160-a）。
- 2026-10-22（美東）：160-b 實作（錨點 160-b）：redlight_missing Python 分支三態判定，只有確定不在 HEAD 才走 not-found 出口；新增 #9（全新 repo 擋）。
