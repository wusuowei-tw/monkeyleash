# 票 151 —— skills 的 .last-complete-round 沒有可用的內容契約

**狀態**:~~**candidate(未排程)。**~~ **第一站 grill 完成(規格定稿:方案 B);待第二站 spec。**
**優先度**:~~**待 Jeff 定。**~~ **高(Jeff 2026-10-12)。**
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

## 第一站 grill(2026-10-12)

### 證據
- R0 唯讀偵察:`.dev/reports/2026-10-12T123630Z-ticket151-r0-recon.md`(現有契約讀碼、兩檔形狀比對、設計方案)。
- G0 來源查證:`.dev/reports/2026-10-12T131215Z-ticket151-g0-source.md`。
  - 在 Claude Code 2.1.291／292／295／296 的程式片段中,可見排版函式把內容組成「token + 空白 + listedFor 以逗號串接」;讀取端只驗第一段符合 `/^[0-9a-f-]{36}$/`【實測(讀碼)】。
  - 實際寫檔呼叫、skills／plugins 兩條路徑的接線、清單元素規則的使用位置:UNKNOWN。
  - 只代表上述 4 個版本,每支約 600 bytes 上下文,不是跨版本的正式格式保證。
- 「skills 與 plugins 兩檔是同一種格式」:【推論】,寫檔呼叫與路徑接線尚未確認。

### 規格定稿(方案 B)
以下各條是本票選定的政策,不是已證明的上游格式保證。

- 理由:接受尾段內容會變,改以格式與大小限制把關,降低固定 hash 造成的反覆核准。不是因為上游檢查較鬆就跟著放鬆。
- 範圍:只處理 `skills/<bucket>/.last-complete-round`。票 149 的 plugins 契約與其回歸測試一律不變。

1. 前段:第 1～36 字元為小寫 UUIDv4,規則與票 149 `synced-last-round-v1` 相同(全小寫、版本位 `4`、variant 位 `8`/`9`/`a`/`b`)。
2. 第 37 byte 為 `0x20`。
3. 尾段(第 38 byte 起)只允許 ASCII `a-z`、`A-Z`、`0-9`、`_`、`.`、`-`、`,`;不允許空白、`0x0A`、`0x0D`、其他符號、控制字元、非 ASCII。此字元集合是本票的政策選擇;上游程式中相近規則的使用位置尚未確認。
4. 只驗字元,不驗逗號清單結構:開頭逗號、結尾逗號、連續逗號都通過。實作不得自行加嚴。
5. 允許空尾段(總長 37 bytes)。理由是容許空清單;目前不能證明 skills 寫入流程一定會產生空尾段。
6. 總長度上限 1024 bytes。這是本票訂的明確限制,不代表上游保證不會超過。
7. 新契約名稱明確綁定 `skills/<bucket>/.last-complete-round` 一條路徑;pins 必須為 `{}`(只驗格式,不比對指紋);未知契約名稱一律 fail-closed。
8. 實作時,`_contract_pins_ok`(:1360)與 `synced_contract_check`(:1652-1654)的隱含預設必須改成明確分派:新契約不得默默套用 last-round 規則,未知名稱不得被當成 last-round 處理。

### 候選事項(本票不處理)
- plugins 的 `.last-complete-round` 契約(票 149,剛好 37 bytes)可能過嚴:上游若寫入非空清單就會被擋【推論】。
- 第二輪來源查證(擴大上下文找實際寫檔呼叫):本票不做。
- 票 149 收尾推送 `c67a484` 的 CI 綠燈紀錄(Jeff 2026-10-12 08:24 美東確認;只代表該輪 CI 整體通過,不等於每項測試都執行且通過)尚未寫入票 149。

### 裁定紀錄
1. 優先度(Jeff 原文,2026-10-12 08:16 美東):「現在推送，151 高」。
2. 進入第一站與來源查證(Jeff 原文,2026-10-12 09:08 美東):「是我改的，同意查來源」。`.dev/pipeline.json` 由 Jeff 改為 151／grill。
3. 規格定稿與寫入(Jeff 原文,2026-10-12 09:31 美東):「確認定稿，同意寫入票 151 並 commit，不 push。」定稿內容由裁決助手整理,經 Jeff 確認。
