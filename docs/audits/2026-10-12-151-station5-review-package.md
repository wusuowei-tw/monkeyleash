# 票 151 第五站審查包 —— skills 的 `.last-complete-round` 內容契約(`synced-skills-last-round-v1`)

- 審查基準:HEAD `05ff2febdee5ef2108f10fec79b767d2b874c7cf`;比較起點 `c67a484`(票 149 收尾)。
- 規格:`docs/tickets/framework-updates/151-skills-last-complete-round-needs-a-contract.md`〈第二站 spec(2026-10-12)〉(票面 blob `ae8aeef1ec279b983cc3f02a7d44ceaf7efcdd9e`)。
- 名冊:HEAD 的 `.agents/extension-inventory.json` blob `ba6859dec904f2448113ceb308485839e99e5a90`(本票未改)。
- 本文件不下審查結論。

## 1. 範圍與分層

`git diff --stat c67a484 HEAD`:`.claude/hooks/redlight.py` +53/−6;票 151 +283/−2;`tests/test_redlight.py` +379。合計 3 檔,713 insertions、8 deletions。

| commit | 類型 | 改了哪些檔 | 影響 runtime 行為 |
|---|---|---|---|
| `d464752` | 第一站 grill(docs) | 票 151 | 否 |
| `903af31` | 第二站 spec(docs) | 票 151 | 否 |
| `6fb7305` | 第三站紅燈測試(test) | `tests/test_redlight.py`(只在檔尾追加 379 行) | 否(只新增測試) |
| `05ff2fe` | 第四站實作(feat) | `.claude/hooks/redlight.py`(+53/−6) | 程式行為有變;但名冊尚未切換,現場 skills 那一筆仍走 sha256 比對,實際判定結果與改動前相同【推論:依讀碼,`synced_verification` 只對名冊中的契約項呼叫 `synced_contract_check`】 |

## 2. 規格出處對照(Implementation Decisions 一～七 → `05ff2fe` 的 `.claude/hooks/redlight.py`)

| 規格 | 內容 | 位置(檔:行,HEAD 05ff2fe) |
|---|---|---|
| 一 | 新名稱只綁 skills 一條邏輯路徑;既有兩契約不變 | `EXT_CONTRACT_SK` :1063;`EXT_CONTRACT_PATHS` :1064-1066;`_EXT_CONTRACT_CAPS` :1067 |
| 二 | pins 恰為空;未知名稱 fail-closed;兩處隱含預設改為明確分派 | `_contract_pins_ok` :1357-1370(MJ :1364、LCR :1366、SK :1368、其他 :1370 `return False`);`synced_contract_check` 分派 :1695-1701(其他 ⇒ :1701 `inventory_schema/contract.name`);名稱第一步檢查 :1688-1689(未改) |
| 三 | 讀檔沿用既有安全程序,只多上限 1024 | `_contract_read` :1479 起(未改);上限查表 :1067 |
| 四 | 格式檢查(長度、前段 ASCII、第 37 byte、UUIDv4、尾段字元集合;只驗字元;空尾段放行) | `_SK_TAIL_BYTES` :1648;`_check_skills_last_round` :1651-1676(尾段 :1674) |
| 五 | 原因代碼沿用 category/field;新欄位 `contract_format/tail` | `_check_skills_last_round` :1651-1676 各 `return c(...)` |
| 六 | R10 接線不改 | `_inventory_check` :1388 起、`synced_verification`(未改);名稱與路徑綁定經查表自動涵蓋 |
| 七 | 名冊切換(skills 那一筆改成契約項) | **未執行**(需 Jeff 核准,走 policy-only) |

`_check_last_round` :1626 起的本體未改(diff 見 `05ff2fe`)。

## 3. 測試證據

| 時點 | 範圍 | 結果 | 報告 |
|---|---|---|---|
| T1b 基準(HEAD `903af31`,測試追加前) | REL3 三檔:`tests/test_redlight.py`、`tests/test_synced_contract_149.py`、`tests/test_synced_platform_149.py` | 422 passed / 7 skipped / 0 failed | `.dev/reports/2026-10-12T182551Z-ticket151-t1b-redlight-commit.md` |
| T1b 紅燈(工作樹:`903af31` + 追加的測試;redlight.py = HEAD) | 同上(收集 511) | 75 failed / 429 passed / 7 skipped;75 個失敗全部是 AssertionError,實際值為 `inventory_schema/contract.name` | 同上 |
| I4 綠燈(工作樹:`6fb7305` + 修改後的 redlight.py,sha256 `ecec28d9…61ee`) | 同上 | 504 passed / 7 skipped / 0 failed | `.dev/reports/2026-10-12T190510Z-ticket151-i4-implement-commit.md` |

- 全部**在列明的殘留下執行**。殘留清單(照抄 T1b 報告):
  - UNKNOWN:(U-a) Python 啟動 `.pth` 匯入的模組與其行為;(U-b) pytest 自動載入的 anyio 外掛的行為;(U-c) git ProgramData 設定層(開跑前實測,出現即不跑)。
  - 只能偵測、不能阻止:(D-a) 不該動的證據檔被改;(D-b) 兩次檢查點之間環境被改掉又改回;(D-c) 兩本帳本只驗證只在尾端追加,不驗內容;(D-d) pytest 自建的 `.pytest_cache`;(D-e) 外掛清單只在開跑前比對。
- **沒有**跑原 repo 全套。
- **沒有**在真實 POSIX 上跑過,也沒有 CI(7 個 skipped 是 Windows 上不可產生的情境)。

## 4. 已知限制

- 名冊尚未切換:skills 那筆仍是 sha256 項,新契約在現場尚未生效。
- E2E(I36、I37)是在 tmp git repo 內以同一行程呼叫 pre-commit 的 R10 路徑,並依票 149 前例替換了 `_extension_claude_root`、`upstream_shadow_violation`、`staged_paths`、`shadow_active` 等函式;不是真正的 git hook。
- `6fb7305`、`05ff2fe` 兩次 commit 時,hook 沒有輸出 R3、R10 的判定細節(UNKNOWN)。
- 尾段字元集合與 1024 上限是本票的政策選擇,不是上游保證。
- 依據樣本只有 1 份(skills 這個檔)。
- 票面 :188 的 portable-manifest 登記不適用:依裁定 1a,沒有新增測試檔。

## 5. 審查題(只附「去哪裡看」,不附答案)

1. 新契約是否只綁 skills 一條路徑?掛到 plugins 的兩條路徑或其他路徑是否都被擋?——看 `redlight.py` :1063-1067、`_inventory_check` :1388 起(:1426-1429 名稱與路徑綁定段);測試 `tests/test_redlight.py` :4651、:4656。
2. `_contract_pins_ok` 是否已無「不是 MJ 就要求空」的落空分支?未知名稱是否回 False?——看 `redlight.py` :1357-1370;測試 :4662、:4668。
3. `synced_contract_check` 的格式分派是否明確對應三個名稱,未知名稱是否不落到 `_check_last_round`?——看 `redlight.py` :1695-1701;測試 :4678(new-50-passes 與 lcr-50-still-blocks)。
4. `_check_skills_last_round` 的檢查順序與原因代碼是否符合規格五(size → ascii → trailer → uuid 系列 → tail)?前段非 ASCII 是否只看前 36 bytes?——看 `redlight.py` :1651-1676;票 151〈第二站 spec〉Implementation Decisions 四、五。
5. 尾段是否只驗字元、不驗逗號結構?空尾段(37 bytes)是否放行?1023/1024 放行、1025 擋?——看 `redlight.py` :1648、:1674;測試 :4589(a3、a4、a6、a6b)、:4613。
6. 讀檔安全程序(`_contract_read`)是否未改,而新契約確實走同一程序(連結、reparse、屬性缺失、競態)?——看 `git show 05ff2fe -- .claude/hooks/redlight.py`;測試 :4622、:4631、:4638。
7. plugins 兩個契約(MJ、LCR)與 `_check_last_round` 本體是否未改?——看 `git show 05ff2fe`;測試 :4691;REL3 中票 149 既有測試的 I4 結果。
8. 新測試是否全部以等值比對代碼(而非只斷言「被擋」),可防止假綠?——看 `tests/test_redlight.py` :4585-4733;T0 計畫 `.dev/reports/2026-10-12T164625Z-ticket151-t0-redlight-plan.md`(假綠風險 59 項)。
9. T1b 紅燈的 75 個失敗是否全部是「新契約尚未實作」的同一形狀,沒有其他原因?——看 T1b 報告〈E 段〉與 sealed-expectations 的 sha256。
10. E2E 的性質與限制是否被正確描述(同一行程、函式替換、不是真 hook)?I37 的合成 skills 根與合成名冊是否一一對應?——看 `tests/test_redlight.py` :4548-4582、:4713-4726。
11. 「測過的就是提交的」證據鏈是否完整(工作樹 sha256 = 測試時的 H_RL1;staged blob = 工作樹 blob)?——看 I4 報告〈F3〉〈G2〉。
12. 報告與票面是否有把殘留聲明過度解讀成「已確認隔離」或「完整隔離」?——看 T1a、T1b-0、T1b、I4 四份報告與票 151〈第三站紅燈與第四站實作〉。

## 6. 未決事項

- 名冊切換(規格第七條):把 skills 那一筆從 sha256 項改成 `synced-skills-last-round-v1` 契約項(pins 為 `{}`),需 Jeff 核准,走 policy-only 提交通道。
- push:未執行。
- CI:未執行。
