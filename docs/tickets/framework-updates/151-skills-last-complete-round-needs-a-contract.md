# 票 151 —— skills 的 .last-complete-round 沒有可用的內容契約

**狀態**:**candidate(未排程)。**
**優先度**:**待 Jeff 定。**
**發現於**:2026-10-11,票 149 D9(第九次攔截唯讀診斷)。
**來源**:`.dev/reports/2026-10-11T192112Z-ticket149-d9-diagnosis.md`(§1、§2、§3)。
**交叉引用**:票 149(synced 兩檔內容契約 v3;第八次核准 b9b4453、第九次核准 6392ce4)、`.dev/reports/2026-10-12T002718Z-ticket149-d10-r10-recheck.md`、票 146(R10)。

---

## 命題

- 反覆觀測到 `skills/<bucket>/.last-complete-round` 的 hash 與名冊不符。第八次已核准(b9b4453),第九次已核准(6392ce4)。
  - D9、D10 都觀測到不符【引用】;被擋當時是否就是觀測到的那一筆:UNKNOWN。
  - 寫入者、原因、變動頻率:UNKNOWN,本票不推論。
- 現有契約綁定 plugins 路徑、限 37 bytes,無法套用到這個檔【引用:D9 §2,HEAD 96db9ef 的 `.claude/hooks/redlight.py` 讀碼】:
  - `EXT_CONTRACT_PATHS` :1062-1063 把每個契約名稱寫死綁到一條 plugins 路徑;名冊驗證 `_inventory_check` :1418-1419 遇到路徑不符回 `inventory_schema/contract.path`。
  - `synced-last-round-v1` 的讀檔上限是 37 bytes(`_EXT_CONTRACT_CAPS` :1064;`_contract_read` :1502-1506 超過即 `contract_read/size_cap`;`_check_last_round` :1619-1620 要求長度 37)。這個檔觀測到的大小是 50 bytes。
  - ⇒ 只改名冊做不到,需要改程式。

## 範圍(只列最小修改位置,不寫解法、不做設計決定)

出處:D9 §2c【引用】(行號以 HEAD 96db9ef 為準)。

1. `EXT_CONTRACT_*` 常數與 `EXT_CONTRACT_PATHS`(:1060-1063):skills 用的契約名稱與路徑綁定。
2. `_EXT_CONTRACT_CAPS`(:1064):對應的讀檔上限。
3. `_contract_pins_ok`(:1354-1360):pins 形狀。
4. `synced_contract_check` 的分派(:1652-1654),以及新的格式檢查函式(比照 `_check_last_round` :1616-1634)。
5. 對應的紅燈測試。
6. 規格:契約 v3 第 1 節「範圍」只涵蓋 plugins 兩檔(票 149 :302-304),需要新的規格與 Jeff 的設計裁決。

## 已知事實(只列判定,不含內容)

- D9 格式核對【引用:D9 §3】:前 36 字元符合小寫 UUIDv4 樣式、第 37 byte 是空白;總長 50 bytes,不符合「剛好 37 bytes」與「不超過 37 bytes」。

## 未決

- 50 bytes 格式中,第 37 byte 之後那 13 bytes 的意義:UNKNOWN(本票不解析內容)。
- 是否走完整流程、優先度:由 Jeff 定。

## 範圍外

- 不顯示、不解析任何 synced 檔的內容;bucket 一律寫 `<bucket>`。
- 不預裁放寬 metadata 檢查(沿用票 149 的處置原則)。
