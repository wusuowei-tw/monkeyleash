# 票 149 第五站審查包(S5-149-0)

- 日期:2026-10-08
- 基準 HEAD:`ad8b270cc4779cc5100821849c67ff3793831f44`
- 站別:`.dev/pipeline.json` 為 `current_stage: review`、`ticket_id: 149`(Jeff 切換)。
- 本文件只整理範圍、證據位置與審查題,**不下審查結論**;結論由全新視窗的獨立審查作出。
- 數字、行號、雜湊一律附出處(報告檔名 + 行號,或以 HEAD `ad8b270` 為準的 Grep / Read 實測行號)。報告在 `.dev/reports/`(ignored,只在本機)。
- 遮罩:路徑一律邏輯路徑;同步桶真名寫成 `<bucket>`。

## §1 範圍與 commit 分類

`git log --oneline --reverse 4d22101..HEAD`(9 個 commit,由舊到新)【實測】:

| # | SHA | 種類 | 改動檔案(`git show --stat`) | 與測試證據的關係 |
|---|---|---|---|---|
| 1 | `26b22244f0869adab638acb9d55070407265fc67` | policy(第四次核准) | `.agents/extension-inventory.json`(4/4) | 名冊基準;非測試對象 |
| 2 | `0d0531b0291af50da53782ee44c8170ce4c785e8` | docs | 票 149(+308 / −3) | T149-4 紅燈執行時的 HEAD(見 §3) |
| 3 | `6d667a3713dfe8760c28475ef1a0ff0835a8705b` | policy(第五次核准) | `.agents/extension-inventory.json`(4/4) | **在 code commit `b64a2d6` 之前** |
| 4 | `147a25ef6fe7e154ca0e72fec786cc48c8954d67` | test | `tests/test_synced_contract_149.py`(+658) | 第三站紅燈 102 項 |
| 5 | `407c481db128edb7cbbdc66c784c59e808a1f21c` | test | `tests/test_synced_platform_149.py`(+285) | 第三站紅燈 18 項 |
| 6 | `68c730edb58d48c1b170560272b14aa79bcdf4a8` | test | `tests/test_redlight.py`(+223) | 第三站補充紅燈 30 項;第四站基準全套的 HEAD |
| 7 | `b64a2d6a0a4168fd41a037c6516318eb59d49a74` | **code**(兼 docs、打包清單) | `.agents/portable-manifest.txt`(+2)、`.claude/hooks/redlight.py`(+411 / −9;stat 420)、票 149(+73 / −1;stat 74) | 第四站實作;測試紀錄見 §3(逐項標執行時點) |
| 8 | `e07e21999868dfaa616a0755781d2784402046fe` | **policy(第六次核准)** | `.agents/extension-inventory.json`(6/6) | 未改程式碼,**但改變 R10 的比對基準**;其後沒有任何測試紀錄;commit 時 R10 回應 DECLARED_OK(runtime 仍 UNPROVEN)【引用:裁決者轉述】 |
| 9 | `ad8b270cc4779cc5100821849c67ff3793831f44` | docs | 第四站審計(新檔 +173)、票 149(+36 / −1) | 無 |

改動範圍核對【實測】(**只證明 `b64a2d6` 之後未改程式與測試,不能代替 `b64a2d6` 之後的測試紀錄**):

```
$ git diff --stat b64a2d6 ad8b270 -- .claude tests scripts .githooks
(無輸出)
$ git diff --stat b64a2d6 e07e219
 .agents/extension-inventory.json | 12 ++++++------
 1 file changed, 6 insertions(+), 6 deletions(-)
$ git diff --stat e07e219 ad8b270
 .../2026-10-08-149-station4-implementation.md      | 173 +++++++++++++++++++++
 .../149-synced-plugin-metadata-hash-drift.md       |  37 ++++-
 2 files changed, 209 insertions(+), 1 deletion(-)
$ git diff --stat 68c730e b64a2d6
 .agents/portable-manifest.txt                      |   2 +
 .claude/hooks/redlight.py                          | 420 ++++++++++++++++++++-
 .../149-synced-plugin-metadata-hash-drift.md       |  74 +++-
 3 files changed, 486 insertions(+), 10 deletions(-)
$ git diff --stat 0d0531b 6d667a3
 .agents/extension-inventory.json | 8 ++++----
 1 file changed, 4 insertions(+), 4 deletions(-)
```

- `redlight.py` 在 `b64a2d6` 的 sha256:`58a2cf23d7f0e9bbb01b17d9347edce7f894002d33ed7b3dac911b78f08ddc26`(`git show b64a2d6:.claude/hooks/redlight.py` 後 sha256sum)【實測】;與 `ad8b270` 工作樹相同。
- policy commit(`6d667a3`、`e07e219`)只改名冊,但名冊是 R10 的比對基準 ⇒ **不能稱為「不影響程式行為」**:同一份程式碼對不同名冊會得出不同判定。

## §2 規格來源(只列位置)

| 規格 | 位置 |
|---|---|
| 契約 v3(定稿)第 1–8 節 | 票 149〈方案 2 契約 v3(定稿)〉:298 起(條文 :302-369) |
| 封存介面 A1–A5、version 2 項目形狀、pins 形狀、原因代碼表 | `2026-10-08T150245Z-ticket149-t149-4-redlight.md` §C(封存檔全文 :79-125) |
| A6 平台替換點、A1 / A4 語意增補、`S0–S3_attr_missing`、檢查順序 | `2026-10-08T164833Z-ticket149-t149-6-redlight.md` §3(:93-118) |
| N1–N4 新增代碼表 | `2026-10-08T174022Z-ticket149-t149-8-r3-redlight.md` §3 封存檔全文(§3 起於 :349) |
| 第四站條件 C1–C4、其他硬性要求的落點 | 票 149〈第四站實作(S4-149)〉:421 起;C1–C4 表 :434-441;介面與代碼引用 :443-448 |

## §3 測試證據表

| 項目 | 結果數字 | 執行時點 | 出處 |
|---|---|---|---|
| 第三站紅燈 `test_synced_contract_149.py` | 95 failed / 7 passed | commit 前工作樹(HEAD `0d0531b0291af50da53782ee44c8170ce4c785e8`,測試檔 untracked) | `…150245Z…t149-4…` :4-5、:370 |
| 第三站紅燈 `test_synced_platform_149.py` | 16 failed / 2 passed | commit 前工作樹(HEAD `147a25ef6fe7e154ca0e72fec786cc48c8954d67`,測試檔 untracked) | `…164833Z…t149-6…` :4-5、:626 |
| 第三站補充 `test_redlight.py`(t149 30 項 + 既有) | 30 failed / 272 passed / 7 skipped | commit 前工作樹(HEAD `407c481db128edb7cbbdc66c784c59e808a1f21c`;commit `68c730e` 在 §6 才做) | `…174022Z…t149-8…` §5 :526 起、:606 |
| 第三站基準全套(第四站基準) | 141 failed / 2349 passed / 10 skipped / 3 xfailed | commit 前工作樹(同上) | `…174022Z…` §5.2 :620 起、:638 |
| 第四站第三次送出:兩新檔 | 120 passed | commit 前工作樹(呼叫點修正前的版本) | `…175131Z…s4-implementation…` §3 :628 起、:634 |
| 第四站第三次送出:`test_redlight.py` | 1 failed(`test_t146_31`)/ 301 passed / 7 skipped —— 已停止 | commit 前工作樹(同上) | `…175131Z…` :645 |
| 第四站接續:兩新檔 | 120 passed | commit 前工作樹 | `…181701Z…s4-implementation…` §2 :115 起、:121;時點標示 :280 |
| 第四站接續:`test_redlight.py` | 302 passed / 7 skipped / 0 failed | commit 前工作樹 | `…181701Z…` :138;時點 :280 |
| 第四站全套(前檢) | 2490 passed / 10 skipped / 3 xfailed / 0 failed | commit 前工作樹 | `…181701Z…` :156;時點 :280 |
| 第四站淨室 `verify_gates.py` | rc 0;R1–R10 各擋下一次;新 repo 2340 passed / 14 skipped / 3 xfailed | commit 前工作樹 | `…181701Z…` :161、:182(§2,前檢) |
| 第四站全套(正式) | 2490 passed / 10 skipped / 3 xfailed / 0 failed | commit 後 HEAD `b64a2d6a0a4168fd41a037c6516318eb59d49a74` | `…181701Z…` §5 :255 起、:261;對照表 :280-286 |
| 帳本前綴證明(第四站) | `test-runs` 1297634 → 1322250、`test-sessions` 42309469 → 44158594,前綴 = 起點 H | commit 後 HEAD `b64a2d6…`(正式全套之後) | `…181701Z…` §5.2 :288-294 |
| `e07e219` 之後 | **無任何測試紀錄** | — | — |

## §4 已知限制與 UNKNOWN

- POSIX 分支已有模擬測試(`tests/test_synced_platform_149.py` 的 `test_g2_posix_no_attrs_valid_passes` 2 node、`test_g2_posix_link_still_blocks` 4 node,以 `_set_platform(monkeypatch, "posix")` 替換,:180-196【實測:Grep】);尚未在真實 POSIX 環境執行。
- 這批 commit 尚未 push,GitHub CI 結果 UNKNOWN。
- `e07e219` 之後沒有任何測試紀錄。
- 名冊仍為 version 1;契約 v3 尚未在現場生效,現場 synced 檔在 version 2 名冊下的實際判定 UNKNOWN。
- 契約 v3 只涵蓋 plugins 兩檔;skills 三筆不在契約範圍。
- runtime UNPROVEN;讀檔程序不宣稱能排除所有競態。

## §5 審查題(不附答案)

行號以 HEAD `ad8b270` 的 `.claude/hooks/redlight.py` 為準【實測:Grep】。

| # | 題目 | 去哪裡看 |
|---|---|---|
| (a) | C1 路徑接線:「額外」「缺少」算法不變;synced 六鍵形狀不變;契約失敗 ⇒ mismatch 計 1,reason 附類別 + 欄位 | `synced_verification` :1928;六鍵 :1940;額外 / 缺少 :1961-1962;實際路徑 `_synced_contract_real_path` :1911;對照 `git show 68c730e:.claude/hooks/redlight.py` 的舊版 |
| (b) | C2 單一判定來源:version 2 名冊時 `_extension_inventory_ok(doc)` 等於 `(extension_inventory_check(doc) is None)` | `_extension_inventory_ok` :1309;`_extension_inventory_v1_ok` :1321;`extension_inventory_check` :1363;`_inventory_check` :1378;測試 `tests/test_redlight.py` `TestTicket149SyncedContractR3` :4296 起(h2) |
| (c) | C3 檔案屬性:posix 缺 `st_file_attributes` 視為無 reparse;windows 取不到即擋(`S<n>_attr_missing`);連結判定兩平台都做;每次呼叫時讀取 `_SYNCED_PLATFORM` | `_contract_stat_bad` :1452(平台判斷 :1459);`_contract_read` :1469;測試 `tests/test_synced_platform_149.py` g1 / g2 |
| (d) | C4 缺檔:只計 missing 1,不另計 mismatch;reason 含 `contract_read` 與 `missing`,不含欄位值 | `synced_verification` :1962 起;測試 `tests/test_synced_platform_149.py` :267(g3)、:281(正控) |
| (e) | version 1 名冊行為完全不變 | `_extension_inventory_v1_ok` :1321;`synced_verification` :1961-1964;測試 `tests/test_synced_contract_149.py` :624、:642、:652(item18) |
| (f) | id 核准 hash 取自名冊 pins,程式碼不寫死 | `_check_marketplaces` :1546(比對 :1601);`_contract_pins_ok` :1354 |
| (g) | 任何契約違反一律 fail-closed(含影子模式);訊息不含任何欄位值 | `.claude/hooks/gate.py` `check_extension_integrity` :4075(synced 訊息 :4135);測試 `tests/test_synced_contract_149.py` :572、:580(item16)及 item17 |
| (h) | 原因代碼只出自封存表,無表外新增 | 封存表見 §2;產生點:`_contract_code(` / `fail(` / `bad(` / `c(` 呼叫(`_inventory_check` :1378 起、`_contract_stat_bad` :1452、`_contract_read` :1469、`_check_marketplaces` :1546、`_check_last_round` :1616、`synced_contract_check` :1637) |
| (i) | `_SYNCED_PLATFORM` 的 production 預設值取自實際平台 | :1069;測試 `TestTicket149SyncedContractR3`(h1) |
| (j) | policy-only 通道、HEAD / index 選取、混合提交規則不變 | `_policy_facts` :1659;`gate.py` `extension_policy_only_commit` :4069、`check_extension_integrity` :4075;`git diff 68c730e b64a2d6 -- .claude/hooks/gate.py`(gate.py 是否有改) |
| (k) | `_extension_first_reason` 簽名與位置參數呼叫;三參數呼叫相容 | 定義 :1993;呼叫 :2052 起(`extension_state`)、:2057、:2116;測試 `tests/test_redlight.py` `test_t146_31` |
| (l) | 證據分層:§3 各項執行時點是否支持「正式 pytest 對應 `b64a2d6`」;`e07e219` 改變比對基準且其後無測試紀錄,對審查結論的影響 | 本文件 §1、§3 |

審查者可自行決定是否重跑全套與做突變探針;本文件不預設結論。

## §6 未決事項(列出,不處理)

- version 2 名冊待 Jeff 核准。
- push 待另行授權。
