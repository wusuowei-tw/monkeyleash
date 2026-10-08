# 票 149 第四站實作審計(S4-149-1)—— R10 支援 synced 兩檔內容契約 v3

- 日期:2026-10-08
- 基準 HEAD:`68c730edb58d48c1b170560272b14aa79bcdf4a8`
- 實作 commit(commit 1):`b64a2d6a0a4168fd41a037c6516318eb59d49a74`
- 站別:`.dev/pipeline.json` 的 `current_stage` 是 `implement`、`ticket_id` 是 `149`。本站沒有改。
- 成果性質:**支援契約、待 policy 啟用**。名冊 `.agents/extension-inventory.json` 仍為 version 1(本站未改);契約要等 Jeff 親自核准 version 2 名冊後才在現場生效。
- 前檢證據(工作樹)與正式結果(committed HEAD)分開記錄。路徑一律遮罩(`<path>` / `<scratchpad>`);本文件不含任何真實 id、UUID、etag 值。

## 1. 規格對照

| 規格 | 來源 | 本站落點 |
|---|---|---|
| S1 契約 v3 第 1–8 節 | 票 149〈方案 2 契約 v3(定稿)〉 | 讀檔 S0–S3(第 2 節)、`.marketplaces.json`(第 3 節)、`.last-complete-round`(第 4 節)、version 2 接線(第 5 節)、失敗處置(第 6 節) |
| S2 封存介面與代碼 | T149-4 §C、T149-6 §3、T149-8 封存檔(N1–N4) | 名稱、簽名、代碼照封存;未新增 `contract_read/path`;未使用表外代碼 |
| S3 四項條件 C1–C4 | 裁決助手審查定稿(非 Jeff 原文) | 見 §3 自查表 |
| S4 其他硬性要求 | 同上 | 平台預設取實際平台;id 核准 hash 只從 pins 讀;policy-only 通道、HEAD/index 選取、混合提交規則未改;version 1 行為不變;runtime 仍 UNPROVEN |

## 2. diff 摘要

`git show --stat b64a2d6`:

```
 .agents/portable-manifest.txt                      |   2 +
 .claude/hooks/redlight.py                          | 420 ++++++++++++++++++++-
 .../149-synced-plugin-metadata-hash-drift.md       |  74 +++-
 3 files changed, 486 insertions(+), 10 deletions(-)
```

### 2.1 `.claude/hooks/redlight.py`(+411 / −9)

- 新增常數:`EXT_INVENTORY_VERSION_CONTRACT = 2`、兩個契約名與其唯一合法邏輯路徑 `EXT_CONTRACT_PATHS`、上限 1024 / 37、`_SYNCED_PLATFORM`(A6)。
- `_extension_inventory_ok`:version 2 ⇒ `extension_inventory_check(doc) is None`;其餘 ⇒ `_extension_inventory_v1_ok`(原函式本體改名,0 行改動)。
- 新增 `extension_inventory_check`(A2)與 `_inventory_check`:version 2 唯一規則來源。
- 新增 `synced_contract_check`(A1)與 `_contract_read`(S0–S3)、`_contract_stat_bad`(先連結、再屬性、再 reparse、再一般檔)、`_check_marketplaces`、`_check_last_round`。
- `extension_inventory_facts`:version 2 判為 malformed 時另帶 `schema_error`(類別+欄位),供 reason 使用;version 1 為 None。
- `synced_verification`:新增參數 `claude_root=None`;契約項目在磁碟上 ⇒ 以實際路徑交給 A1,失敗計 mismatch 1 筆;不在 ⇒ 只計 missing;reason 只附代碼。
- `_extension_first_reason`:簽名 `(facts, surfaces, inventory, synced=None)`;`extension_report` 只評估一次 synced,以**第四個位置參數**傳入(見 §6 第三次送出)。
- gate.py 未改:`check_extension_integrity` 已把 synced 的 reason 原樣放進 R10 擋下訊息(gate.py:4132-4135)。

### 2.2 `.agents/portable-manifest.txt`(+2 / −0)

```
 tests/test_gitlink_downstream_cycle.py copy
+tests/test_synced_contract_149.py copy
+tests/test_synced_platform_149.py copy
```

## 3. 自查表(S4-149-1 版本 `redlight.py` 行號)

| 項 | 位置 |
|---|---|
| C1 實際路徑接線 | `_synced_contract_real_path` :1911-1925;呼叫與計數 :1970-1978;額外 :1961、缺少 :1962(算式未改);六鍵初值 :1940(未改);reason 附代碼 :1979-1988 |
| C2 單一判定來源 | :1309-1318 |
| C3 屬性 / 平台 | `_contract_stat_bad` :1452-1466(平台每次讀取 :1459);連結判定只在 S0 / S3 |
| C4 缺檔只計 missing | :1962、:1966-1969 |
| A1 `synced_contract_check` | :1637-1656 |
| A2 `extension_inventory_check` | :1363-1375;規則 :1378-1422 |
| A3 `_extension_inventory_ok` | :1309-1318;v1 本體 `_extension_inventory_v1_ok` :1321 |
| A4 `extension_report` | :2061-2118(synced 一次評估 :2115;位置參數呼叫 :2116) |
| A5 `gate.mode_pre_commit` | 未改 |
| A6 `_SYNCED_PLATFORM` 預設取自實際平台 | :1069 |
| pins 讀取 | :1601;pins 形狀 `_contract_pins_ok` :1354-1360;名冊 pins 傳入 :1975 |
| 封存 `contract_value` / `contract_keys` / `contract_duplicate_key` / `contract_type` | :1558-1610 |
| 封存 `contract_format`、`contract_pin`、`contract_rows_count` | :1600、:1602、:1607、:1612、:1572、:1620-1633 |
| 封存 `contract_encoding` / `contract_json` | :1552、:1556、:1622 |
| 封存 `contract_read`(missing / size_cap / 連結・reparse / 競態 / attr_missing) | :1477、:1506、:1455、:1463、:1496-1532、:1460 |
| 封存 `inventory_schema`(entry_kind / contract.name / contract.pins / version / contract.path) | :1399、:1417 / :1646、:1421 / :1648、:1387 / :1392、:1419 |
| N1 `S0_error`–`S3_error` | :1479、:1491、:1510、:1523 |
| N2 `read_error` | :1486、:1504、:1656 |
| N3 `S0_type`–`S3_type` | :1465 |
| N4 `$` / `schema` / `entries` / `path` / `note` / `sha256` / `contract` | :1375、:1382 / :1384 / :1389、:1393、:1397、:1401 / :1404 / :1407 / :1410 / :1414 |
| version 1 路徑未改 | `_extension_inventory_v1_ok` 本體 0 行改動;額外 / 缺少兩行未改;mismatch 一行只加 `p not in contracts`(version 1 的 contracts 恆空) |

- 契約檔實際路徑解析不了 ⇒ `structure_errors = 1`、reason「synced 結構錯誤：…」(:1971-1974),沿用結構錯誤處理,不另立代碼。
- JSON 過深巢狀的 `RecursionError` 歸封存的 `contract_json/parse`(:1555-1556)。

## 4. 基準 / 前檢 / 正式結果對照【實測】

| 項 | 基準(`68c730e`,T149-8 `t149-8-full.txt`) | 前檢(工作樹) | 正式(committed `b64a2d6`) |
|---|---|---|---|
| 兩個新檔 120 項 | 111 失敗 / 9 通過 | 120 passed | (含在全套) |
| `tests/test_redlight.py` | 30 failed、272 passed、7 skipped | 0 failed、302 passed、7 skipped | (含在全套) |
| 全套 failed | 141 | 0 | 0 |
| 全套 passed | 2349 | 2490 | 2490 |
| skipped / xfailed | 10 / 3 | 10 / 3 | 10 / 3 |
| skipped 原因 | 8 行 | 與基準逐行相同 | 與基準逐行相同 |

- 第三站 150 項(不是「150 項紅燈」):`147a25e` 102 項(基準 95 失敗 / 7 通過)、`407c481` 18 項(16 失敗 / 2 通過)、`68c730e` t149 30 項(30 失敗);基準合計 141 失敗、9 通過。前檢與正式:150 項全部 passed。
- 指定守住的既有測試 `test_t146_31` / `_35` / `_44` / `_45`:前檢皆 passed。

全套尾段(前檢與正式相同):

```
SKIPPED [1] tests\test_gate.py:451: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:459: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:473: 此環境無法建立 symlink
SKIPPED [1] tests\test_redlight.py:2673: Windows 檔名不得含 LF;本案例由 POSIX 驗收證明(〈六十一〉61.3 裁決 2)
SKIPPED [1] tests\test_redlight.py:3074: Windows 建 symlink 需要額外權限;POSIX 才產得出來
SKIPPED [1] tests\test_redlight.py:3505: chmod 000 在 Windows 不會讓目錄不可列舉;POSIX 才產得出來
SKIPPED [3] tests\test_redlight.py:3702: Windows 建 symlink 需要額外權限;POSIX 才產得出來
SKIPPED [1] tests\test_redlight.py:3752: Windows 建 symlink 需要額外權限;POSIX 才產得出來
2490 passed, 10 skipped, 3 xfailed
```

(耗時:前檢 261.83s、正式 260.82s。)

## 5. 淨室摘錄(`python -X utf8 .claude/portable/verify_gates.py <scratchpad>/vg-149`,rc 0)【實測】

```
=== 規則清單(從 gate.py 的定義列舉,不是對照表)===
    R1 R2 R3 R4 R5 R6 R7 R8 R9 R10

=== 逐條實測(每條各擋一次)===
    R1   擋下 ✓
    R2   擋下 ✓
    R3   擋下 ✓
    R4   擋下 ✓
    R5   擋下 ✓
    R6   擋下 ✓
    R7   擋下 ✓
    R8   擋下 ✓
    R9   擋下 ✓
    R10  擋下 ✓
         正控放行 ✓(同一佈置、家目錄未放情境物)
         [R10/fail-closed] unmanaged_entry：未受管入口：synced（額外 2 / 缺少 0 / 內容不符 0）

=== 框架自己的測試,在這個新 repo 裡跑一次 ===
    2340 passed, 14 skipped, 3 xfailed in 243.39s (0:04:03)

全部 10 條規則各擋下一次,權威層偵測正常,框架測試在新 repo 全綠,evidence policy 兩正三負成立。
```

- 新 repo 帶入兩個新測試檔:`tests/test_synced_contract_149.py`、`tests/test_synced_platform_149.py` 都存在於淨室 repo【實測:Glob】。
- 淨室使用隔離家目錄(`<scratchpad>/vg-149/home`);真實 `~/.claude` 不讀不寫(verify_gates.py:744-747)。

## 6. 第四站三次送出與本次偏離

1. **第一次**:基準 113 failed(預期 111)—— 兩個新測試檔未登記在打包清單。依 Jeff「裁:兩檔標 copy，併入第四站 L1；只加打包清單兩條登記，不動名冊，不 push」處理。
2. **第二次**:第一刀改 `redlight.py` 被前哨 R3 擋下 —— 紅燈不在配對測試檔 `tests/test_redlight.py`。依 Jeff 裁甲由 T149-8 在該檔尾補 30 項(`68c730e`)。
3. **第三次**:R3 放行,150 項全過;但既有 `test_t146_31` 失敗 —— `extension_report` 以關鍵字 `synced=synced` 呼叫,測試替身 `counting(facts, surfaces, *inventory)` 不收關鍵字參數。停下回報。
4. **第三次・接續(偏離紀錄)**:依裁決助手 13:55 美東接續意見(非 Jeff 原文),只把呼叫改為第四個位置參數 `_extension_first_reason(facts, surfaces, inventory, synced)`(:2116),函式簽名維持 `synced=None` 預設;**未改任何測試**。之後重跑 150 項、全套、淨室,全部符合才 commit。

流程教訓:第三站紅燈除新檔外也須跑全套;紅燈測試須放在 R3 認可的配對測試檔;內部函式加參數時以既有測試替身的呼叫形式為準。

## 7. 證據帳本

- `.dev/gate-exemptions.jsonl`:本站全程未變(sha256 `3a1be81b0a334289a137536a2ea7f884cd73fff14bb537b48c39a9f73a36755e`、129175 bytes);**沒有新增行**。前哨放行本站所有 Edit、乾跑與 commit 1 的 hook 都未追加。
- 測試帳本(只做雜湊與長度):
  - 本輪起點 (LC, H):`test-runs.jsonl` 1297634 bytes / `ba0b052832342f1b66fd6bb9f780081b6e248877ec6f391a9f2cf536fe2e4bf9`;`test-sessions.jsonl` 42309469 bytes / `8a3da61d90515556b9e0b98e47202cfbfaea5fd428d1cc63d2779f836f0ce548`。
  - 正式結果後:`test-runs.jsonl` 1322250 bytes / `e937224b154a9b2d80b9f864fdbac0dbd70608b9954b9e931e210546ab157a72`;`test-sessions.jsonl` 44158594 bytes / `a0a4840395a30f354c374e0d92aa6f80b9df6e6ffb0133e29c3dc38707cc248a`。
  - 前綴證明:前 1297634 / 42309469 bytes 的 sha256 分別等於起點 H ⇒ 只在尾端追加。

## 8. 偏離與 UNKNOWN

- 偏離:第三次送出的步驟 1 內多跑一次開發檢查(兩新檔 120 passed);全套與淨室以背景方式執行(指令形式不變)。
- 偏離:第三次・接續的相容性修正依裁決助手意見進行,未另取 Jeff 裁決原文(見 §6 第 4 點)。
- 【UNKNOWN】POSIX 與 CI 未跑(本機 Windows)。posix 分支(缺屬性視為無 reparse)只由測試以 `_SYNCED_PLATFORM` 替換驗證。
- 【UNKNOWN】現場 synced 兩檔在 version 2 名冊下的實際判定:名冊仍為 version 1,本站未以 version 2 名冊對現場執行。
- 【推論】T149-8 寫入的紅燈紀錄被 R3 認可(第一刀未被擋);紀錄內容未讀(只准雜湊)。
- runtime 仍 UNPROVEN;讀檔程序不宣稱能排除所有競態。

## 附錄:S4-149-2 第一次被擋與第六次核准

詳見票 149〈第四站實作(S4-149)〉→〈第六次攔截與核准〉;此處只列精簡版。

- **第一次送出被 R10 擋下**【引用】(`2026-10-08T181701Z-ticket149-s4-implementation.md`,美東 14:17 之前):`[R10/fail-closed] unmanaged_entry：未受管入口：synced（額外 0 / 缺少 0 / 內容不符 3）`;已退回暫存。第六次攔截。
- **處置三輪**【引用】:D6-149(`…182616Z…`)三筆不符全在 skills(`.last-complete-round`、`computer-use/SKILL.md`、`manifest.json`);D6b-149(`…183618Z…`)唯讀審閱 `SKILL.md`(`f1b16578`),未執行其中指令;A6-149(`…184434Z…` 停止、`…185318Z…` 草稿)version 1 草稿只改 6 行,其餘 227 筆不變。
- **裁決引文**:三份報告的「Jeff 原話 / 選項說明 / 審查意見」分類表見票 149 該小節(只取自報告原文;D6b 與 A6 停止報告的「選項說明」「審查意見」為【UNKNOWN:報告未收錄】)。A6 草稿報告的 Jeff 原話:1.「裁：授權準備第六次重新核准草稿（version 1，只更新 skills 三筆 sha256 與 note），唯讀診斷與核對照既有流程；不核准、不 commit、不 push」;2.「裁A」。
- **第六次核准**【實測】:`e07e21999868dfaa616a0755781d2784402046fe`(2026-10-08 15:03:49 美東),inventory blob `e7fc6c16cc1ddb8d0147c5e3639f24643f148f6f`,DECLARED_OK(runtime 仍 UNPROVEN)【引用】。攔截 6、核准 6。
- **口徑**:第六次核准不代表已證明來源、更新原因或執行安全;「首次觀測到」不能證明第一次變動;其餘口徑逐條見票 149 該小節。
- **範圍**:名冊仍為 version 1;契約 v3 只涵蓋 plugins 兩檔,skills 三筆不在契約範圍;version 2 仍會偵測並擋下這類變動。
- **重送紀錄**:重送第一版因 `cp` 被前哨 R7 擋下(`2026-10-08T190946Z-ticket149-s4-2-commit.md`),屬指令錯誤,不計入 R10 攔截。
