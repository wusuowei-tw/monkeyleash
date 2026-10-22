# 159 — find_implementation 誤入任意名稱的虛擬環境

**狀態**：**立案；159-a 紅燈完成（本機）。** 159-b 實作待開工。
**立案**：2026-10-21（美東）。建檔前以 Glob `docs/tickets/framework-updates/159-*` 確認無命中。
**性質**：小票 —— `redlight.find_implementation` 跳過判準的修正（只動一個函式的跳過邏輯）。
**交叉引用**：`F-167`（`docs/agents/friction-log.md`）；票 156 D-1；`F-021`。

---

## 一、根因

`find_implementation` 以 `os.walk` 由 repo 根往下找，回傳**第一個**同名檔。
跳過清單 `_SEARCH_SKIP` 只有字面名稱 ⇒ 任何不在清單裡的 venv 目錄名都會被走進去，
而 venv 裡的第三方套件很容易有與測試檔對應的同名檔。

## 二、下游事故

依桌機裁決助手轉述的偵察結果，**本站未親驗**：

- 某下游研究 repo 的 `.venv-research` 裡有第三方套件的同名檔；
- 該 repo 的 `test-runs.jsonl` 有一筆紀錄的 `impl_file` 指向 `yfinance/domain/market.py`；
- 結果 R3 擋下第二刀（紅燈紀錄記的是 venv 裡那一份，而不是該 repo 自己的實作）。

## 三、同族

- `F-021`：跳過判準按名字猜類別（「點開頭 = 基礎設施」），結果對閘門自己盲。本票是同一個習慣的反面：按名字列舉 venv，名字不在清單就走進去。
- 票 156 D-1：只把 `.venv-gates` 一個名字加進清單，解了那一個實例，沒有解決同類。
- 「取第一個同名檔」本身的問題（K3）**本票不解**。

## 四、裁決

上游修法裁決（桌機下游研究 repo 的裁決助手經 Jeff 確認，Jeff 2026-10-21 約 19:53（美東）轉達；裁決助手記錄，非逐字原話）——修法「丙」：

1. 只修 `redlight.find_implementation` 的跳過判準：
   - 目錄內含 `pyvenv.cfg` → 跳過整棵子樹（看內容，不看名字）；
   - 目錄名是 `site-packages` 或 `node_modules` → 跳過；
   - **不用** `.venv*` 這類名稱前綴（`F-021`）；
   - `_SEARCH_SKIP` 既有的字面名保留，不刪。
2. **不動**：`gate.NON_SOURCE_DIRS`、`gate.is_source_path`、`_H2_SKIP_DIRS`。

實作方式（裁決助手依既有授權調整，不改變裁決內容）：`site-packages` 以加進 `_SEARCH_SKIP` 字面集合的方式實作（159-b），因此 159-a 先在 `tests/test_non_source_list_parity.py` 的 `ONLY_IN_REDLIGHT` 補這一筆並附理由；`pyvenv.cfg` 是內容判定，不進集合。

Jeff 2026-10-21 約 19:55（美東）決定（裁決助手記錄，非逐字原話）：本票在筆電做，等 158 推完才開工；commit 訊息照本 repo「恰好三行、不加署名」。

## 五、風險（審查重點）

本修法讓 `find_implementation` 回 `None` 的情況變多，**等於 R3 第一個出口放寬**。
審查時要逐條問：**每一個新增的 `None`，是不是「真的沒有本 repo 的實作」。**

## 六、與票 158 的關係

同檔（`.claude/hooks/redlight.py`）不同函式。158 C0-1c 已先落地（`78c3a14`），本票接在其後，不需要任何歷史改寫。

## 七、驗收

紅燈測試在 `tests/test_redlight.py` 的 `TestT159FindImplementationSkipsArbitraryVenvs`，皆以 `tmp_path` 自建假 repo 根，呼叫 `find_implementation("tests/test_market.py")`：

| # | 假 repo 裡的檔案 | 預期 |
|---|---|---|
| ① | `.venv-research/pyvenv.cfg`、`.venv-research/Lib/site-packages/yfinance/domain/market.py` | `None` |
| ② | `env/pyvenv.cfg`、`env/lib/other/market.py`（不經過 `site-packages`） | `None` |
| ③ | `vendor/site-packages/x/market.py`（無 `pyvenv.cfg`） | `None` |
| ④ | `src/market.py`，另有 ① 那一份 venv 副本 | `"src/market.py"` |
| ⑤ | `tools/market.py`（無 `pyvenv.cfg`） | `"tools/market.py"` |

1. 159-a：①②③ 必須因預期的斷言失敗而紅；④ 是混合情境的診斷測試，159-a 依現行 `os.walk` 的實際走訪順序可紅可綠，但實作完成後必須綠；⑤ 必須維持綠。parity 因新增 `site-packages` 宣告而產生預期紅燈。
2. 159-b：轉綠後，相關測試及全套皆 0 failed。
3. 獨立審查通過。
4. push 後 CI 綠，由 Jeff 目視。

## 八、修正紀錄

- 2026-10-21（美東）：立案；159-a 紅燈測試（錨點 159-a）。
- 2026-10-21（美東）：159-a 同一 session 並行一次（步驟 8 一則訊息送出 5 個唯讀呼叫：兩次 git diff 導向 scratchpad、兩次 Read、一次 git diff），Jeff 約 21:16 接受，由原 session 完成本機提交；紅燈結果在並行前已記錄，未重跑。
