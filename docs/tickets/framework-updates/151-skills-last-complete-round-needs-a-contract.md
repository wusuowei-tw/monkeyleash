# 票 151 —— skills 的 .last-complete-round 沒有可用的內容契約

**狀態**:~~**candidate(未排程)。**~~ ~~**第一站 grill 完成(規格定稿:方案 B);待第二站 spec。**~~ ~~**第二站 spec 完成;待第三站紅燈。**~~ **第三站紅燈、第四站實作完成;第五站審查包已提交,待獨立審查。**
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

## 第二站 spec(2026-10-12)

本節為票 151 的正式規格(依 to-spec 範本);規格本文不含程式碼與 repo 路徑。

### 票 151 規格 —— skills 的 `.last-complete-round` 內容契約(方案 B)

> 規格狀態:第二站 spec 定稿。
> 依據:票 151〈第一站 grill〉的規格定稿 8 條(以下以「定稿第 N 條」標示對應)。本規格不加嚴、不放寬。

#### Problem Statement

R10 以名冊逐檔比對 synced 兩根的指紋。skills 那一根 bucket 內的 `.last-complete-round` 一直是逐檔 hash 項,它的內容會變,而每變一次 R10 就硬擋 commit,只能由 Jeff 重新核准名冊。六天內同一筆已核准三次(第六、八、九次),而核准時看不到內容,把關實質有限,核准次數越多越流於形式。

票 149 已為 plugins 那一根的兩個 metadata 檔建了「內容契約」(只驗格式,不比對指紋),但那兩個契約各自寫死綁在 plugins 的路徑上,讀檔上限是 37 bytes。skills 的這個檔觀測到是 50 bytes(前 37 bytes 與 plugins 的形狀相同,其後多一段),兩個既有契約都不能套用;只改名冊做不到,必須改程式。

#### Solution

為 skills 的 `.last-complete-round` 新增一個專用的內容契約 `synced-skills-last-round-v1`。名冊中這一筆從「逐檔 hash」改成「契約項」之後,R10 不再比對它的指紋,改為檢查格式與大小:

- 前 36 字元是小寫 UUIDv4（全小寫、版本位 4、variant 位 8／9／a／b）,第 37 byte 是空白,之後的尾段只允許一個固定的 ASCII 字元集合,總長不超過 1024 bytes。
- 符合 ⇒ 放行,不再需要人工重新核准;不符合 ⇒ R10 fail-closed 硬擋,訊息只說哪一類、哪一欄,不洩漏內容。

這是本票選定的**政策**:接受尾段內容會變,改以格式與大小限制把關。它不是已證明的上游格式保證,也不是因為上游的讀取端檢查較鬆就跟著放鬆。

plugins 那兩個既有契約的行為、以及它們的回歸測試,一律不變。

#### User Stories

1. 身為維護者 Jeff,我希望 skills 的 `.last-complete-round` 在 UUID 或尾段正常變動時不再擋下 commit,這樣我不必每隔一兩天就重新核准一筆看不到內容的 hash。
2. 身為維護者 Jeff,我希望這個檔一旦變成不合格式的內容(例如夾帶空白、換行、控制字元、非 ASCII、或異常變大),R10 仍然硬擋,這樣放寬的只是「值」,不是「形狀」。
3. 身為維護者 Jeff,我希望新契約只能掛在 skills 那一條邏輯路徑上,這樣它不會被誤用到 plugins 或其他檔案而形成一個漏洞。
4. 身為維護者 Jeff,我希望 plugins 兩個既有契約的判定結果在本票前後完全相同,這樣票 149 已宣告生效的保障不會被本票順手改動。
5. 身為維護者 Jeff,我希望名冊從 hash 項切換到契約項,是一次獨立、需要我核准的 policy 變更,而且排在程式與測試完成之後,這樣不會出現「名冊先改、程式還不認得」的空窗。
6. 身為維護者 Jeff,我希望規格明寫尾段的字元集合是本票的政策選擇,而不是上游保證,這樣日後上游改版造成誤擋時,大家知道要回來修的是政策,不是去找程式缺陷。
7. 身為 R10 閘門,我需要每一個契約名稱都有明確對應的 pins 規則、讀檔上限與格式檢查,這樣不認得的名稱會被 fail-closed 擋下,而不是默默落到某個預設分支。
8. 身為 R10 閘門,我需要新契約的 pins 必須恰為空物件,這樣名冊不能偷偷塞進一個看似被比對、其實沒被使用的指紋。
9. 身為 R10 閘門,我需要新契約讀檔時沿用既有的安全讀取程序(連結、reparse、屬性缺失、讀取前後的身分大小時間一致性),這樣放寬格式不會連帶放寬讀檔的安全判定。
10. 身為 R10 閘門,我需要實際讀到的內容超過 1024 bytes 就擋(包括開檔前看起來小、讀的時候變大),這樣無法用一個超大的檔塞進任意內容。
11. 身為 R10 閘門,我需要新契約在影子模式下仍然硬擋,這樣它和既有契約一樣不受影子豁免。
12. 身為 R10 閘門,我需要擋下時的原因代碼沿用既有的「類別/欄位」形式,這樣訊息格式一致,而且不含任何值。
13. 身為執行者 VS,我希望紅燈測試清單把每一種放行與擋下的情境都寫成可驗證的外部行為,這樣我可以先寫紅燈、再實作,而不用猜規格的意思。
14. 身為執行者 VS,我希望規格明寫「只驗字元,不驗逗號清單結構」,這樣我不會自行加上「不得有連續逗號」之類的檢查而造成誤擋。
15. 身為執行者 VS,我希望規格明寫空尾段(總長剛好 37 bytes)要放行,這樣我不會沿用 plugins 契約「必須剛好 37 bytes」的直覺把邊界寫反。
16. 身為執行者 VS,我希望規格點出兩處現有的隱含預設(pins 預設要求空、格式預設套 last-round 規則),並要求改成明確分派,這樣我不會只在名稱表加一個新名字就以為接好了。
17. 身為執行者 VS,我希望規格列出哪些測試可以沿用票 149 的前例,這樣新測試的寫法和既有測試一致,也容易審查。
18. 身為未來的審查者,我希望能從規格對到票 151 定稿的每一條,這樣我可以確認實作沒有加嚴或放寬。
19. 身為未來的審查者,我希望規格寫清楚這個契約的依據限制(只看過 4 個版本、每支只看了片段、寫入呼叫沒看到),這樣日後上游行為改變時,我知道當初的依據有多薄。
20. 身為未來的審查者,我希望擋下訊息與測試輸出都不含檔案內容,這樣這個檔的 UUID 與尾段不會因為報告、log 或 CI 輸出而外流。
21. 身為未來的審查者,我希望票 149 的既有回歸鎖(把 plugins 的 last-round 契約掛到 skills 路徑必須被擋)保持原樣,這樣「一名一路徑」的原則在本票之後仍然成立。

#### Implementation Decisions

**一、新契約與綁定(定稿第 7 條)**

- 新增契約名稱 `synced-skills-last-round-v1`,明確綁定名冊邏輯路徑 `skills/<bucket>/.last-complete-round` 這一條,且只有這一條。
- 「一名一路徑」原則不變:新契約掛到任何其他路徑(包括 plugins 的 `.last-complete-round`)⇒ 名冊損壞;既有的 `synced-last-round-v1` 掛到 skills 路徑 ⇒ 仍然損壞(既有回歸鎖不動)。
- plugins 的兩個既有契約(`synced-marketplaces-v1`、`synced-last-round-v1`)的名稱、綁定路徑、讀檔上限、pins 規則與格式規則,一律不變。

**二、pins、未知名稱與明確分派(定稿第 7、8 條)**

- 新契約的 pins 必須恰為空物件;非空、或不是物件 ⇒ 名冊損壞(`inventory_schema/contract.pins`)。新契約只驗格式,不比對任何指紋。
- 未知契約名稱一律 fail-closed:名冊驗證與契約檢查兩處都擋(`inventory_schema/contract.name`)。
- 目前有兩處「隱含預設」必須改成明確分派:
  - `_contract_pins_ok`:現在對「不是 marketplaces 的任何名稱」一律要求 pins 為空。改成每個已知名稱各自明確對應規則;不在已知集合內的名稱 ⇒ 判不合格。
  - `synced_contract_check` 的格式分派:現在「不是 marketplaces 的任何名稱」一律走 last-round 規則。改成每個已知名稱各自明確對應一個格式檢查;新契約不得默默套用 last-round 的 37 bytes 規則,未知名稱不得被當成 last-round 處理。
- 讀檔上限表同樣以名稱明確查表;新名稱的上限是 1024。

**三、讀檔(定稿第 6 條)**

- 沿用既有契約的安全讀取程序,不另寫一套:開檔前 lstat、開檔後 fstat、最多讀「上限 + 1」bytes、讀後 fstat、關檔後 lstat;連結、reparse、Windows 屬性缺失、非一般檔、各步驟之間身分/大小/修改時間不一致、缺檔、讀取錯誤,判定全部照舊。
- 唯一的差別是上限:新契約為 1024 bytes。實際讀到超過 1024 ⇒ `contract_read/size_cap`。
- 這個上限是本票訂的明確限制,不代表上游保證不會超過。

**四、格式檢查(定稿第 1～5 條)**

新增一個格式檢查,只用於新契約。判定規則:

1. 長度至少 37 bytes;不足 ⇒ 擋。
2. 前段第 1～36 字元為小寫 UUIDv4（全小寫、版本位 4、variant 位 8／9／a／b）,規則與 `synced-last-round-v1` 相同:UUID 形狀、全小寫、版本位為 `4`、variant 位屬於 `8`/`9`/`a`/`b`。
3. 第 37 byte 為 `0x20`。
4. 尾段(第 38 byte 起,到檔尾)每一個 byte 都必須屬於 ASCII 集合:`a-z`、`A-Z`、`0-9`、`_`、`.`、`-`、`,`。不允許空白、`0x0A`、`0x0D`、其他任何符號、控制字元、非 ASCII。此集合是本票的政策選擇。
5. **只驗字元,不驗逗號清單結構**:開頭逗號、結尾逗號、連續逗號都通過。實作不得自行加嚴(例如不得要求每一項非空、不得限制項數、不得套用單項長度或單項樣式)。
6. 允許空尾段:總長剛好 37 bytes 放行。理由是容許空清單;目前不能證明 skills 寫入流程一定會產生空尾段。

**五、原因代碼(沿用既有 category/field 命名)**

- 沿用既有形式:恰好兩鍵 `{category, field}`,只有類別與欄位,不含任何值。
- 確定對應(與 `synced-last-round-v1` 同名欄位者沿用同一代碼):
  - 讀檔類照舊(`contract_read/…`,含 `size_cap`、`missing`、連結/reparse/競態等既有欄位)。
  - 總長不足 37 ⇒ `contract_format/size`。
  - 前段含非 ASCII ⇒ `contract_encoding/ascii`。
  - 第 37 byte 不是空白 ⇒ `contract_format/trailer`。
  - 前段 UUID 形狀、大小寫、版本位、variant 位 ⇒ `contract_format/uuid`、`uuid_case`、`uuid_version`、`uuid_variant`。
  - 尾段出現集合外的 byte(含空白、LF、CR、控制字元、非 ASCII)⇒ 新欄位 `contract_format/tail`(確定)。
- 檢查順序與上列相同;同一份內容有多處不合時只回報第一個,與既有契約一致。

**六、R10 接線**

- R10 對契約項的既有處理不變:契約項不計入指紋比對;檔案在磁碟上 ⇒ 交給契約檢查,失敗計「內容不符」1 筆並附代碼;不在磁碟上 ⇒ 只計「缺少」。
- 邏輯路徑到實際路徑的解析已支援 skills 根,不需改動。
- 失敗一律 fail-closed 硬擋,影子模式下仍硬擋(沿用票 149 契約第 6 節與 R10 規則)。

**七、名冊 policy 變更與順序**

- 名冊需要另做一次 policy 變更:把 skills 那一筆從 sha256 項改成契約項(`synced-skills-last-round-v1`、pins 為空)。名冊 version 維持 2,schema 不變。
- 這次變更要 Jeff 核准,順序在程式實作與測試全部完成並提交之後;走既有的 policy-only 提交通道。
- 程式先上、名冊後改,中間這段期間 skills 那一筆仍是 hash 項,行為與現在相同。
- 新增的測試檔需要依既有慣例登記到 portable-manifest(前例:票 149 的兩個測試檔都登記為 `copy`)。

#### Testing Decisions

**好測試的標準**

- 只測外部行為:給定名冊內容與磁碟上的檔案位元組,斷言放行或擋下,以及擋下時的 `{category, field}`。不測內部函式的呼叫順序或中間狀態。
- 測試內容一律用合成的 UUID 與尾段,不讀任何真實 synced 檔。
- 任何層級的測試都不得讀取真實的 synced 檔或真實家目錄。

**測試切入點(seam)**

原則是「最高、最少」,而且優先用既有切入點。採用三個,都是票 149 已在使用的:

1. **契約檢查的公開入口**(`synced_contract_check`,輸入契約名稱、實際路徑、pins,可注入 lstat/fstat):涵蓋全部格式規則、讀檔上限與讀檔安全判定。這是能直接餵位元組的最高點。
2. **名冊驗證的公開入口**(`extension_inventory_check`,輸入名冊文件):涵蓋路徑綁定、pins 形狀、未知名稱。這一層不碰磁碟。
3. **R10 pre-commit 端到端**:測試自行建立臨時 git repo 與合成的使用者家目錄(含合成的 synced 兩根與名冊),在該臨時 repo 中觸發 pre-commit 的 R10 檢查。這不是對本 repo 的實際 commit,也不接觸真實使用者層;所有內容都是合成資料。只放少量案例,證明接線(名冊契約項 → R10 → 放行或硬擋、影子模式仍硬擋、訊息只有代碼)。

理由:第 1、2 個切入點已存在,而且票 149 的測試就是以它們為主;第 3 個是使用者真正感受到的行為,但搭建成本高,只用來證明接線。不新增任何切入點。

**紅燈測試清單(只描述情境與預期,不寫程式碼)**

以下「新契約」指 `synced-skills-last-round-v1`;「掛在 skills」指綁定在 skills 那一條邏輯路徑。

A. 合法放行

1. 前段合法 UUIDv4、第 37 byte 空白、尾段為單一字母數字段 ⇒ 放行。
2. 尾段為多項逗號清單(例如由字母、數字、`_`、`.`、`-` 組成的數項,以逗號分隔)⇒ 放行。
3. 空尾段(總長剛好 37 bytes)⇒ 放行。
4. 逗號邊界:尾段只有一個逗號、以逗號開頭、以逗號結尾、含連續逗號 ⇒ 全部放行。
5. 尾段使用到集合中每一類字元(大小寫字母、數字、`_`、`.`、`-`、`,`)⇒ 放行。
6. 總長剛好 1024 bytes ⇒ 放行。
6b. 總長剛好 1023 bytes ⇒ 放行。
7. 只改 UUID 值或尾段內容(仍合法)⇒ 放行,不比對任何指紋。

B. 前段不合法(沿用票 149 item11 的前例)

8. 總長不足 37(例如 36 bytes)⇒ 擋,`contract_format/size`。
9. 前段不是 UUID 形狀 ⇒ 擋,`contract_format/uuid`。
10. 前段含大寫 ⇒ 擋,`contract_format/uuid_case`。
11. 版本位不是 `4` ⇒ 擋,`contract_format/uuid_version`。
12. variant 位不屬 `8`/`9`/`a`/`b` ⇒ 擋,`contract_format/uuid_variant`。
13. 前段含非 ASCII ⇒ 擋,`contract_encoding/ascii`。

C. 第 37 byte

14. 第 37 byte 不是 `0x20`(例如是逗號、字母、Tab、LF)⇒ 擋,`contract_format/trailer`。

D. 尾段非法字元

15. 尾段含空白 ⇒ 擋,`contract_format/tail`。
16. 尾段含 `0x0A`(包括只在檔尾多一個換行)⇒ 擋,`contract_format/tail`。
17. 尾段含 `0x0D` ⇒ 擋,`contract_format/tail`。
18. 尾段含集合外的可列印符號(逐一涵蓋具代表性的,例如 `/`、`:`、`;`、`=`、引號、反斜線)⇒ 擋,`contract_format/tail`。
19. 尾段含其他控制字元(例如 `0x00`、`0x09`、`0x7F`)⇒ 擋,`contract_format/tail`。
20. 尾段含非 ASCII(例如 UTF-8 多位元組字元)⇒ 擋,`contract_format/tail`。

E. 大小上限(沿用票 149 item10 的前例)

21. 總長 1025 bytes ⇒ 擋,`contract_read/size_cap`。
22. 開檔前看起來不超過上限、讀的時候實際超過 ⇒ 擋,`contract_read/size_cap`。

F. 讀檔安全判定(沿用票 149 item12、item13 與平台測試的前例,只需證明新契約走的是同一套程序)

23. 連結或 reparse 點(任一步驟)⇒ 擋;缺檔 ⇒ 擋。
24. 讀取競態(各步驟之間身分、大小或修改時間不一致)⇒ 擋。
25. Windows 平台缺少檔案屬性 ⇒ 擋;posix 平台無屬性而內容合法 ⇒ 放行。

G. 路徑綁定、pins 與名稱(沿用票 149 item14、item15 的前例)

26. 新契約掛在 plugins 的 `.last-complete-round` ⇒ 名冊損壞,`inventory_schema/contract.path`。
27. 新契約掛在 plugins 的 `.marketplaces.json`、外掛本體檔或任何其他路徑 ⇒ `inventory_schema/contract.path`。
28. 既有的 `synced-last-round-v1` 掛在 skills 路徑 ⇒ 仍然 `inventory_schema/contract.path`(既有回歸鎖保持原樣)。
29. 新契約的 pins 非空(例如帶一個指紋欄位)、或 pins 不是物件 ⇒ `inventory_schema/contract.pins`。
30. 未知契約名稱(名冊驗證與契約檢查兩個入口都要測)⇒ `inventory_schema/contract.name`。
31. 明確分派:新契約遇到 37 bytes 的合法內容放行,遇到 50 bytes 的合法內容也放行(證明沒有落到 last-round 的 37 bytes 規則);`synced-last-round-v1` 遇到 50 bytes 仍擋(證明舊規則沒有被新規則取代)。

H. 回歸不變(沿用票 149 item01、item11、item18 的前例)

32. plugins 兩個既有契約:票 149 全部既有測試不修改、全部通過。
33. `synced-last-round-v1` 仍然只接受剛好 37 bytes;`synced-marketplaces-v1` 上限仍是 1024 且規則不變。
34. version 1 名冊行為不變;version 2 中 sha256 項仍以指紋比對。

I. 訊息不洩漏內容(沿用票 149 item16、item17 的前例)

35. 每一種擋下情境的原因代碼都只有 `{category, field}`,不含 UUID、尾段或任何 byte 值。
36. 端到端:R10 擋下訊息只含「額外/缺少/內容不符」計數與代碼,不含檔案內容;影子模式下仍硬擋。
37. 端到端:名冊把 skills 那一筆設為新契約項、磁碟上的檔合法 ⇒ R10 放行。
38. 尾段非法字元被擋時,原因代碼恰為 {category: contract_format, field: tail} 兩鍵,不含任何 byte 值或檔案內容。

**沿用前例的對照**:B 對應票 149 item11;E 對應 item10;F 對應 item12、item13 與平台測試 g1、g2;G 對應 item14、item15;H 對應 item01、item18;I 的第 35～37 項對應 item16、item17。A(含 6b)、C、D、G 的第 31 項與 I 的第 38 項是本票新增的情境。

**紅燈預期與提交順序**

- 第三站寫紅燈測試前,先把「逐項預期結果」封存成清單(每一項測試標明預期 FAIL 或預期 PASS),再執行。
- 新增行為的測試(新契約的放行、擋下、明確分派、tail 代碼等):預期 FAIL;必須逐項核對失敗原因是「新契約尚未實作」(例如名稱不被認得、分派不存在),不是其他原因。
- 既有行為的正控與回歸測試(plugins 兩契約不變、`synced-last-round-v1` 掛 skills 仍被擋、version 1 名冊行為不變等):預期 PASS。若它們在紅燈階段失敗,代表測試或環境有問題,不是正確紅燈。
- 收集錯誤、語法錯誤、import 錯誤、fixture 錯誤:一律判為異常,不能當成正確紅燈;遇到就停止並回報。
- 實際結果與封存的預期逐項比對,全部相符才算紅燈成立。
- 第三站除了跑新測試,也要跑全套:打包清單登記這一類全庫性質的檢查只在全套裡出現(票 149 第四站第一次送出的前例)。
- 第四站實作才改程式。R3 對被修改的契約模組有兩半要求:前半是該模組的配對測試檔(以模組名命名的測試檔,放在測試目錄或模組旁)必須存在;後半是配對測試檔必須有一筆合格的紅燈紀錄 —— 結果為紅、屬於本票票號,而且是對著該模組在 HEAD 的內容跑出來的(先寫實作再補跑的紀錄不算)。另開的新測試檔不在配對範圍內,不滿足後半;因此紅燈測試中必須有一部分放在該模組的配對測試檔裡,並在實作前跑出紅燈(票 149 第四站第一刀被 R3 擋下、才在配對測試檔補紅燈的前例)。
- 新測試檔依既有慣例登記到 portable-manifest。

#### Out of Scope

- 放寬 plugins 的 `.last-complete-round` 契約(它可能過嚴的問題,記為候選事項,本票不處理)。
- 第二輪來源查證(擴大上下文去找上游實際的寫檔呼叫)。
- 解析或命名尾段的意義;不驗逗號清單的結構,也不驗每一項的內容。
- 任何 synced 檔內容的展示:報告、測試輸出、擋下訊息都不顯示真實內容。
- 改動 R10 的指紋比對、額外/缺少的算法、policy-only 通道、HEAD/index 選取規則。
- 名冊 schema 或 version 的任何變更。

#### Further Notes

- 依據的限制:
  - 上游格式的線索來自 G0 來源查證,只涵蓋 Claude Code 2.1.291、292、295、296 四個版本,每支只看了約 600 bytes 的上下文。
  - 在那些片段中,可見排版函式把內容組成「token、空白、listedFor 以逗號串接」,讀取端只驗第一段是 36 個 `0-9a-f-` 字元。實際的寫檔呼叫、skills 與 plugins 兩條路徑的接線、清單元素規則在哪裡被使用:都還是 UNKNOWN。
  - 「skills 與 plugins 兩檔是同一種格式」是推論,未確認。
  - 本規格的前段規則(小寫 UUIDv4（全小寫、版本位 4、variant 位 8／9／a／b）)、字元集合、空尾段放行與 1024 上限都是本票的政策選擇,不是已證明的上游格式保證。上游改版造成誤擋時,處置是回來修政策。
- 保障與限制(與票 149 契約相同性質):
  - 契約只證明內容符合這份格式政策,不證明內容來源或寫入者。
  - R10 只能擋 commit,不能保證 commit 前沒有任何東西被載入;runtime 仍 UNPROVEN。
  - 閘門會讀這個檔的內容(只做判定,不輸出)。
- 依據觀測:目前只有 skills 這個檔的 1 份樣本(50 bytes,尾段 13 bytes,全 ASCII,無換行)。本政策的設計目標是不依賴那一份樣本的細節。

#### 已裁定

Jeff 2026-10-12 送出 S1 指令確認;授權內容由裁決助手整理,非逐字原話。

1. 名稱:1a,`synced-skills-last-round-v1`。
2. 測試入口:2a,三個既有切入點(契約檢查入口、名冊驗證入口、R10 pre-commit 端到端少量)。
3. 規格位置:3a,寫入票 151。

### 實作位置附註(不屬規格本文)
- 新增契約時最少要動的位置,見 `.dev/reports/2026-10-12T123630Z-ticket151-r0-recon.md` §1-3a;兩處隱含預設見本票〈第一站 grill〉第 8 條。
- 規格位置裁定 3a:本票不另開規格檔。

## 第三站紅燈與第四站實作(2026-10-12)

### commit

- `6fb7305`:第三站紅燈測試,只在 `tests/test_redlight.py` 檔尾追加 `TestTicket151SkillsLastRound`,82 項(預期 FAIL 75 / PASS 7)。
- `05ff2fe`:第四站實作,只改 `.claude/hooks/redlight.py`(新增 `synced-skills-last-round-v1`;pins 與格式明確分派;新增 `_check_skills_last_round`)。

### 測試結果與時點

範圍一律是 REL3 三檔(`tests/test_redlight.py`、`tests/test_synced_contract_149.py`、`tests/test_synced_platform_149.py`),全部**在列明的殘留下執行**。

| 時點 | 結果 | 報告 |
|---|---|---|
| T1b 基準(HEAD `903af31`,測試追加前) | 422 passed / 7 skipped / 0 failed | `.dev/reports/2026-10-12T182551Z-ticket151-t1b-redlight-commit.md` |
| T1b 紅燈(`903af31` + 追加的測試;redlight.py = HEAD) | 75 failed / 429 passed / 7 skipped(75 個失敗都是 `inventory_schema/contract.name`) | 同上 |
| I4 綠燈(`6fb7305` + 修改後的 redlight.py) | 504 passed / 7 skipped / 0 failed | `.dev/reports/2026-10-12T190510Z-ticket151-i4-implement-commit.md` |

殘留清單(照抄 T1b 報告):
- UNKNOWN:(U-a) Python 啟動 `.pth` 匯入的模組與其行為;(U-b) pytest 自動載入的 anyio 外掛的行為;(U-c) git ProgramData 設定層(開跑前實測,出現即不跑)。
- 只能偵測、不能阻止:(D-a) 不該動的證據檔被改;(D-b) 兩次檢查點之間環境被改掉又改回;(D-c) 兩本帳本只驗證只在尾端追加,不驗內容;(D-d) pytest 自建的 `.pytest_cache`;(D-e) 外掛清單只在開跑前比對。

沒有跑原 repo 全套;沒有在真實 POSIX 上跑過,也沒有 CI。名冊尚未切換,新契約在現場尚未生效。

### 隔離盤點經過

- T1a 隔離缺口唯讀盤點:`.dev/reports/2026-10-12T174010Z-ticket151-t1a-isolation-recon.md`。
- T1b-0 隔離殘留縮小盤點:`.dev/reports/2026-10-12T180007Z-ticket151-t1b0-residual.md`。

### 裁定紀錄

1. Jeff 原文(2026-10-12 12:52 美東):「1a、2b；3先跑已確認隔離的相關測試基準，原 repo 全套先不跑。完整指令須列出執行範圍與隔離方式。不 push」
2. 方向 K1a、K2a、K3a、K4a、U1b,刪 ii(2026-10-12 13:53 美東;裁決助手記錄的選定內容)。
3. Jeff 原文(2026-10-12 14:05 美東):「甲」(接受範圍見 T1b 報告〈授權來源〉)。
4. Jeff 原文(2026-10-12 14:51 美東):「同意」(第四站沿用同一組殘留,綠燈一次)。
5. Jeff 原文:「改好了」(2026-10-12 14:50 美東,`.dev/pipeline.json` 改為 implement;15:20 美東改為 review)。
6. 本輪的文件更新與 commit:Jeff 親自送出 S5-151-0 指令(裁決助手記錄)。

### 程序偏離彙整

- T1b-0:用了不在允許清單內的 `ls` 列出 site-packages,之後改用 Glob 重做。
- T1b、I4:各有指令單以外的唯讀指令(例如 `git rev-list`、`date -u`、另取一次 HEAD blob),都已在各自報告中列出。

### 附註

- 第二站規格 :188「新增的測試檔需要依既有慣例登記到 portable-manifest」不適用:依裁定 1a,本票沒有新增測試檔。
- 第五站審查包:`docs/audits/2026-10-12-151-station5-review-package.md`。
