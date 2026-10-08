# 票 149 —— synced 外掛 metadata 兩檔於 2026-10-07 兩次與已核准 hash 不符(R10 攔截紀錄)

**狀態**:~~**立案(未排程)。**~~ ~~**調查中（T149-1 補記觀測三；寫入者、消費方式、變動機制待唯讀偵察）。**~~ ~~**設計完成（方案 2 契約 v3 定稿，Jeff 裁定 2026-10-08）；待第四次核准後提交，接著進第三站紅燈。**~~ ~~**設計完成；第四次核准完成（26b2224，Jeff 2026-10-08）；待第三站紅燈。**~~ **第四站實作中（S4-149-1；前檢通過）；待正式結果。**
**優先度**:~~**未定。**(排程由 Jeff 另裁。)~~ Jeff 原文:「148 收完後優先做 149」（2026-10-07 20:50 美東）、「做票149」（2026-10-08 08:56 美東）。
**發現於**:2026-10-07。
**交叉引用**:票 146(R10)、票 148(S3-148-1 被擋)。

---

## 範圍聲明

本票只記錄觀測、核准與攔截證據；寫入者、用途、變動原因 UNKNOWN；觀測到的最後修改時間（mtime）不當作寫入事件時間；不預裁放寬 metadata 檢查。

出處說明:
- 下列報告都在 `.dev/reports/`(ignored,只在本機)。
- 本票每個數值都標出處;在出處中找不到的原文寫 UNKNOWN。
- 路徑一律用邏輯路徑,同步桶真名遮罩為 `<bucket>`。

## 觀測一(票 146 S5-146-1 期間)

涉及路徑:`plugins/<bucket>/.last-complete-round`、`plugins/<bucket>/.marketplaces.json`。

每個檔各一行:

- `plugins/<bucket>/.last-complete-round`:
  - sha256 `b86387644d03dcff45011c3d02d3ff32f4c7555553f78b508046fea69fc5b421` → `b7817e9461f8948d8d8da8a037dc8703efd754fe6b59de88d0f9c2b148598762`
  - 觀測到的最後修改時間 2026-10-07 11:32:35 美東(觀測值)
  - 出處:`2026-10-07T174353Z-ticket146-s5-r1-resnapshot.md` §3 raw 輸出 :156-160
- `plugins/<bucket>/.marketplaces.json`:
  - sha256 `48a4a2af215dcb5c3ed5faeeb624bcdaf321f25fdc2e47cf4b231d8b61d2fbfd` → `0520f148d4424daf3922521b66e1dace3e8444109db5c03a648283eb544422dc`
  - 觀測到的最後修改時間 2026-10-07 11:32:35 美東(觀測值)
  - 出處:同報告 §3 raw 輸出 :162-166

其餘紀錄:

- **列舉結果**:HEAD inventory 230 筆、快照 230 筆;`match=228 content-mismatch=2 missing=0 extra=0`。兩次列舉逐位元組相同。出處:同報告 §3 :45、:153-154。
- **R10 擋下時點**:S5-146-1 第二次 commit 被 R10 擋,約 17:25Z。出處:同報告 §3 :173 的時間線。
  - 該報告把這條時間線整體標為【推論】,寫明「以 mtime 對時,不證明是誰寫的」。
- **R10 擋下原文**:UNKNOWN。本票指定的來源中沒有記錄這一次的擋下原文。
- **Jeff 核准 commit**:`b3cfe7187deb8fd88ff6c48a886a683880aef74e`,policy-only。出處:`git show --stat`,原文如下:

  ```
  commit b3cfe7187deb8fd88ff6c48a886a683880aef74e
  Author: wusuowei-tw <<id>>
  Date:   Wed Oct 7 14:08:07 2026 -0400

      policy(146): re-approve 2 synced plugin metadata entries via policy-only lane, approved by Jeff 2026-10-07

   .agents/extension-inventory.json | 8 ++++----
   1 file changed, 4 insertions(+), 4 deletions(-)
  ```

- **寫入者查證**:三版本機 Claude Code 擴充的 JS 中,兩個檔名都是 0 次命中;native `claude.exe` 超過 200MB 沒有搜尋;寫入者 UNKNOWN。出處:`2026-10-07T180022Z-ticket146-s5-r1c-verify.md`〈給裁決者〉第 1 點、Q1 表(:64-71、:90)。

## 觀測二(票 148 S3-148-1 期間)

- **R10 擋下原文**(出處:`2026-10-07T205822Z-ticket148-s3-redlight.md` §5):

  ```
  [六站閘門/pre-commit] commit 已擋下:

    [R10/fail-closed] unmanaged_entry：未受管入口：synced（額外 0 / 缺少 0 / 內容不符 2）
  ```

- 每個檔各一行:
  - `plugins/<bucket>/.last-complete-round`:
    - sha256 `b7817e9461f8948d8d8da8a037dc8703efd754fe6b59de88d0f9c2b148598762` → `6bf883c8c13e55c8bf113861600a866928ed9081d1b1de022f503a2f2abbcdad`
    - 觀測到的最後修改時間 2026-10-07 16:29:00 美東(觀測值)
    - 出處:`2026-10-07T211219Z-ticket148-r1-diagnosis.md` §1
  - `plugins/<bucket>/.marketplaces.json`:
    - sha256 `0520f148d4424daf3922521b66e1dace3e8444109db5c03a648283eb544422dc` → `ece5bb843ede81d2db3925e7425b0e8c3f88d5cdb258de08f37f3cb2aeba6ed0`
    - 觀測到的最後修改時間 2026-10-07 16:28:59 美東(觀測值)
    - 出處:同上 §1
- **完整快照**:兩次一致,230 筆;228 筆登記檔案 hash 相符;各類錯誤 0。出處:`2026-10-07T212031Z-ticket148-r2-reapproval-prep.md` §1。
- **Jeff 核准 commit**:`c91db49a620045d8d9122e6859c4732cd2c06479`,policy-only。出處:`git show --stat`,原文如下:

  ```
  commit c91db49a620045d8d9122e6859c4732cd2c06479
  Author: wusuowei-tw <<id>>
  Date:   Wed Oct 7 17:39:02 2026 -0400

      policy(148): re-approve 2 synced plugin metadata entries (second time on 2026-10-07) via policy-only lane, approved by Jeff 2026-10-07

   .agents/extension-inventory.json | 8 ++++----
   1 file changed, 4 insertions(+), 4 deletions(-)
  ```

- **核准時的保全訊息**:
  - **來源性質**:Jeff 終端機輸出,由裁決者轉錄於 T149-0 指令。不是報告檔,本 repo 沒有獨立紀錄。
  - 原文:「[R10/policy-only] policy-only commit（policy_source=index）：staged 候選 policy 對現場成立（DECLARED_OK；runtime 仍 UNPROVEN）。這是候選驗證，不是 HEAD 已生效的 policy。」
- **核准後快查**:`MATCH-NEW-HEAD: True`;S3-148-1(`aeb4d51a26401fbe541837b4d51672ba594a60a3`)提交時 pre-commit 放行。出處:`2026-10-07T214331Z-ticket148-s3-commit.md` §1、§3。

## 內容檢視(第二次,遮罩後)

只列 R2 報告(`2026-10-07T212031Z-ticket148-r2-reapproval-prep.md`)§2 已記錄的事實。

- `plugins/<bucket>/.last-complete-round` 大小:37 bytes。
- `plugins/<bucket>/.marketplaces.json` 大小:392 bytes。
- `.marketplaces.json`:
  - 頂層鍵:`etag`、`rows`、`parserVersion`。
  - `rows[]` 鍵:`name`、`display_name`、`scope`、`source`、`id`、`updated_at`。
  - rows 筆數:1。
  - `parserVersion`:1002。
  - `rows[0].name`:`anthropic-plugin-directory`。
  - `rows[0].display_name`:`Anthropic Directory`。
  - `rows[0].updated_at`:`2026-10-07T20:25:33.764113Z`(檔內欄位值,不代表寫入時間)。

與第一次的比較(照 R2 報告 §2 逐欄表):

| 欄 | 結果 | 第一次值的出處 |
|---|---|---|
| 頂層鍵 | 相同 | R1c 報告 Q3 :133 |
| `rows[]` 鍵 | 相同 | R1c 報告 Q3 :134 |
| rows 筆數 | 相同 | R1c 報告 Q3 :135 |
| `parserVersion` | 相同 | R1c 報告 Q3 :136 |
| `.marketplaces.json` 大小 | 相同 | S5-R1 報告 :165 |
| `.last-complete-round` 大小 | 相同 | S5-R1 報告 :159 |
| `rows[0].name` / `display_name` | 第一次值 UNKNOWN(未記入報告檔) | — |
| `rows[0].updated_at` | 第一次值 UNKNOWN | — |
| `etag`、`scope`、`id`、`source` 內層 | 第一次值 UNKNOWN | — |
| `.last-complete-round` 內容 | 第一次值 UNKNOWN | — |

裁決層註記:第一次(R1b)於對話中已觀測相同市集名稱;該觀測未存入報告檔。

## 觀測三（票 148 S5-148-2 期間）

- **R10 擋下原文**（出處：`2026-10-08T003620Z-ticket148-s5-2-record.md` §4，:228-230）：

  ```
  [六站閘門/pre-commit] commit 已擋下:

    [R10/fail-closed] unmanaged_entry：未受管入口：synced（額外 0 / 缺少 0 / 內容不符 2）
  ```

- 每個檔各一行：
  - `plugins/<bucket>/.last-complete-round`：
    - sha256 `6bf883c8c13e55c8bf113861600a866928ed9081d1b1de022f503a2f2abbcdad` → `a4fd82fee8b80a275f74e0554fc595034e162766f4f79f697fce7d8edc3de49c`
    - 觀測到的最後修改時間 2026-10-07 20:14:43 美東（觀測值）
    - 出處：`2026-10-08T004652Z-ticket148-r3-diagnosis.md` §2 :113-117、§3 表 :138
  - `plugins/<bucket>/.marketplaces.json`：
    - sha256 `ece5bb843ede81d2db3925e7425b0e8c3f88d5cdb258de08f37f3cb2aeba6ed0` → `6b6bbe6de944280ce7f493a0f20c1b511e3a1856cc52ade855f88c8ab91d7b63`
    - 觀測到的最後修改時間 2026-10-07 20:14:43 美東（觀測值）
    - 出處：同上 §2 :119-123、§3 表 :139
- **完整列舉**：
  - R3 診斷連跑兩次，`cmp` 無輸出，兩次逐位元組相同。`registered=230 observed=230`；`match=228 content-mismatch=2 missing=0 extra=0 UNVERIFIED=0`；ENUM-ERROR / STRUCTURE-ERROR / READ-ERROR / NONREGULAR / SKIPPED-LINK 各 0。出處：`2026-10-08T004652Z-ticket148-r3-diagnosis.md` §2 :93-112。
  - R4 準備兩次完整快照（list-C / list-D），`cmp` 無輸出，兩次一致；`SUMMARY files=230`，五類錯誤各 0。diag 結果同上：228 筆登記檔案 hash 相符，content-mismatch 2，missing 0，extra 0，UNVERIFIED 0。出處：`2026-10-08T005639Z-ticket148-r4-reapproval-prep.md` §2 :140-161。
- **遮罩內容與 R2 比較**（只列 R4 報告 §3 :205-223 記錄的結果）：
  - 看得到的欄位中，只有 `.marketplaces.json` 的 `rows[0].updated_at` 不同：R2 為 `2026-10-07T20:25:33.764113Z`，本次為 `2026-10-08T00:12:35.286903Z`。兩者都只是檔內欄位值，不代表寫入時間。
  - 頂層鍵、rows 鍵、rows 筆數、`parserVersion`、`rows[0].name`、`rows[0].display_name`、兩檔大小、`.last-complete-round` 遮罩後形狀、各遮罩欄位的型別與長度：相同。
  - 被遮罩的值（`etag`、`rows[0].scope`、`rows[0].id`、`rows[0].source` 內層、`.last-complete-round` 原值）有沒有變：UNKNOWN（R2 未記錄原值）。
- **準備期間開頭與結尾複測**：結尾 diag 與開頭 diag `cmp` 無輸出，逐位元組相同。出處：R4 報告 §7 :320-332。這只證明兩個時點一致，不能排除期間變動後又恢復。
- **Jeff 核准 commit**：`499ab3ba202200b0bc6d2410675384b03287f573`，policy-only。出處：`git show --stat --format=%H%n%ai%n%ci%n%s 499ab3ba202200b0bc6d2410675384b03287f573`，原文如下（第二行為作者時間 `%ai`，第三行為提交時間 `%ci`）：

  ```
  499ab3ba202200b0bc6d2410675384b03287f573
  2026-10-08 07:45:53 -0400
  2026-10-08 07:45:53 -0400
  policy(148): re-approve 2 synced plugin metadata entries (third time on 2026-10-07) via policy-only lane, approved by Jeff 2026-10-07

   .agents/extension-inventory.json | 8 ++++----
   1 file changed, 4 insertions(+), 4 deletions(-)
  ```

- **核准時的保全訊息**：
  - **來源性質**：Jeff 終端機輸出，由裁決者轉錄於指令；本 repo 沒有獨立紀錄。
  - 原文：「[R10/policy-only] policy-only commit（policy_source=index）：staged 候選 policy 對現場成立（DECLARED_OK；runtime 仍 UNPROVEN）。這是候選驗證，不是 HEAD 已生效的 policy。」
- **核准後**：`95105993eb093ba87223a732f3adea2f22d0f3c4`（父 `499ab3b`）提交時 pre-commit 放行，沒有輸出擋下訊息。出處：`2026-10-08T115133Z-ticket148-s5-2-record-2.md` §2 :82-90、§3 :95-98。

### 日期更正

- 準備裁決：2026-10-07 20:50 美東（裁丙）。
- 499ab3b 作者時間（`%ai`）：`2026-10-08 07:45:53 -0400`。
- 499ab3b 提交時間（`%ci`）：`2026-10-08 07:45:53 -0400`。
- Jeff 親自作出核准決定的時間：UNKNOWN。Git 時間只代表 commit 的時間，不能單獨證明決定時間；本 repo 沒有其他紀錄。
- 499ab3b 的 inventory note「Jeff 核准 2026-10-07 第三次」（出處：T149-1 以 Grep 讀 `.agents/extension-inventory.json` :13、:18；當時工作樹乾淨，等同 HEAD `4d22101`），以及 commit 訊息中的「third time on 2026-10-07」「approved by Jeff 2026-10-07」，日期都與該 commit 的 Git 時間日期（2026-10-08）不一致。此日期由裁決者起草時寫入，屬裁決者疏失。依 Jeff 裁決（2026-10-08 07:48 美東）不 amend，以本節為準。

## 觀測四（票 149 T149-1 期間）

計數口徑：R10 攔截 4 次（觀測一～四）；Jeff 核准 3 次（`b3cfe71`、`c91db49`、`499ab3b`）。兩者分開計。

- **R10 擋下原文**【引用】（出處：`2026-10-08T130339Z-ticket149-t149-1-record.md` §D :121-125）：

  ```
  Exit code 1

  [六站閘門/pre-commit] commit 已擋下:

    [R10/fail-closed] unmanaged_entry：未受管入口：synced（額外 0 / 缺少 0 / 內容不符 2）
  ```

- **基準程式缺失而停止**【引用】：R5-149 第一次執行時，步驟 0 第 8 項要求的比對基準 `<scratchpad>/r1-148-diag.py` 不存在，依指令停止、未自行重建。出處：`2026-10-08T131137Z-ticket149-r5-diagnosis.md` §0 :35-37、表 :49。
- **基準程式重建**【引用】：依 Jeff 2026-10-08 09:14 美東授權，照 R1 報告 §3 原文重建；sha256 `87baf8bfd9f407869fe1b4854c5b8c087ee9803c4d84f637546a99b8851040e7`、7437 bytes，等於 R2-148／R3-148／R4-148 記錄的完整值。出處：`2026-10-08T131715Z-ticket149-r5b-diagnosis.md` §0-8 :57-64。
- **兩次列舉**【引用】：連跑兩次，`cmp` 無輸出，逐位元組相同。`registered=230 observed=230`；`match=228 content-mismatch=2 missing=0 extra=0 UNVERIFIED=0`；五類錯誤各 0。出處：同上 §2 :113-139。
- 每個檔各一行【引用】（出處：同上 §2 :140-151、§2-7 表 :165-166）：
  - `plugins/<bucket>/.last-complete-round`：
    - sha256 `a4fd82fee8b80a275f74e0554fc595034e162766f4f79f697fce7d8edc3de49c` → `88ddde5ddfe1bc70eada71fbf4a5ccdd0ff4c9d9c7c795693573b6a33652575c`
    - 觀測到的最後修改時間 2026-10-08 09:00:42 美東（13:00:42 UTC；觀測值）
  - `plugins/<bucket>/.marketplaces.json`：
    - sha256 `6b6bbe6de944280ce7f493a0f20c1b511e3a1856cc52ade855f88c8ab91d7b63` → `510cde9d71ac145dc8c403d63492ee90d9f5079f58676cda42d01229fabd5ea5`
    - 觀測到的最後修改時間 2026-10-08 09:00:42 美東（13:00:42 UTC；觀測值）
- **HEAD 登記值**【引用】：兩筆的 HEAD 登記值等於 `499ab3b` 核准值。出處：同上 :168-170。
- **路徑**【引用】：兩筆不符路徑與觀測一～三逐字相同。出處：同上表 :174-178。
- 寫入者、用途、消費方式、變動機制：UNKNOWN。

### 第四次核准

- **Jeff 核准 commit**【實測】：`26b22244f0869adab638acb9d55070407265fc67`，policy-only。出處：`git show --stat --format=%H%n%ai%n%ci%n%s 26b22244f0869adab638acb9d55070407265fc67`，原文如下（第二行為作者時間 `%ai`，第三行為提交時間 `%ci`）：

  ```
  26b22244f0869adab638acb9d55070407265fc67
  2026-10-08 10:36:34 -0400
  2026-10-08 10:36:34 -0400
  policy(149): re-approve 2 synced plugin metadata entries (fourth approval) via policy-only lane, approved by Jeff 2026-10-08

   .agents/extension-inventory.json | 8 ++++----
   1 file changed, 4 insertions(+), 4 deletions(-)
  ```

  - 作者時間:`2026-10-08 10:36:34 -0400`。
  - 提交時間:`2026-10-08 10:36:34 -0400`。
- **新 inventory blob**【實測】：`be18c46048154e8f4a80f77bf505c355c25a7806`（`git rev-parse 26b2224:.agents/extension-inventory.json`）。
  - R8 草稿的 blob 是 `db96cec7cc0ff3b7bab8a20aa53fea403f6ff5e0`（R8 §5 :284），與核准後的 blob 不同。
  - 兩者的差異內容：本輪未查,UNKNOWN。
- **核准前的準備**【引用】：出處 `.dev/reports/2026-10-08T140931Z-ticket149-r8-reapproval-prep.md`。
  - 四支基準程式的 sha256 都等於指定值(第一段 :11)。
  - 兩次完整快照逐位元組一致:`SUMMARY files=230`,五類錯誤 0(§2 :159-162)。
  - 診斷:`match=228 content-mismatch=2 missing=0 extra=0 UNVERIFIED=0`;HEAD 登記值為 499ab3b 核准值;目前值 `88ddde5d…575c`、`510cde9d…5ea5` 等於 R7 值(§2 :176-189;第一段 :12)。
  - 遮罩內容與 R4 比較:看得到的欄位只有 `rows[0].updated_at` 不同(`2026-10-08T00:12:35.286903Z` → `2026-10-08T12:57:33.938059Z`,檔內欄位值);被遮罩的值有沒有變:UNKNOWN(§3 :228-244)。
  - inventory 草稿只改 4 行(2 sha256 + 2 note「待 Jeff 核准」),version 1(§5 :273-278)。
  - 獨立核對 `ALL OK: True`(§6 :340-348)。
  - 結尾複測與開頭逐位元組相同。只證明兩個時點一致,不能排除期間變動後又恢復(§7 :367-368、:388-389)。
- **核准時的保全訊息**：
  - **來源性質**：Jeff 終端機輸出，由裁決者轉錄於指令；本 repo 沒有獨立紀錄。
  - 原文：「[R10/policy-only] policy-only commit（policy_source=index）：staged 候選 policy 對現場成立（DECLARED_OK；runtime 仍 UNPROVEN）。這是候選驗證，不是 HEAD 已生效的 policy。」
- **Jeff 親自作出核准決定的時間**：UNKNOWN（Git 時間只代表 commit 時間）。
- **計數**：攔截 4 次；核准 4 次（`b3cfe71`、`c91db49`、`499ab3b`、`26b2224`）。

## 安裝檔查證（R6）

出處：`2026-10-08T132533Z-ticket149-r6-binscan.md`。方法：只讀安裝檔位元組、分段掃描固定字串、命中點前後各 300 bytes；未執行任何 Claude 程式、未讀 `~/.claude`。

- **四支 `claude.exe`**【引用】（§1 表 :45-50；路徑遮罩）：

  | # | 來源 | 版本 | bytes |
  |---|---|---|---|
  | 1 | `<~>/.vscode/extensions/anthropic.claude-code-2.1.289-win32-x64/…/claude.exe` | 2.1.289 | 249522848 |
  | 2 | `<~>/.vscode/extensions/anthropic.claude-code-2.1.291-win32-x64/…/claude.exe` | 2.1.291 | 253042848 |
  | 3 | `<~>/.vscode/extensions/anthropic.claude-code-2.1.292-win32-x64/…/claude.exe` | 2.1.292 | 254858400 |
  | 4 | `<~>/AppData/Local/Packages/Claude_<id>/…/claude-code/2.1.293/<id>/claude.exe` | 2.1.293 | 256155808 |

  掃描前後 sha256 相同，只證明兩個時點一致（:52）。
- **兩檔名以常數宣告出現**【引用】：四支都在壓縮程式碼中以常數宣告出現一次。例如檔 4 的 `$Et=".marketplaces.json"`、`gss=".last-complete-round"`（§6.2 表 :289-294）。另在字串常數表各出現一次（§7 :319）。
- **讀寫呼叫**【引用】：命中點 ±300 bytes 內沒有 writeFile / rename / mkdir / readFile / JSON.parse / exists（§7 :320）。
- **`syncClaudeAiPlugins` 說明原文節錄**【引用】（§6.1 :264，四支逐字相同 :313）：

  > "Set to false to turn off syncing of the plugins you have enabled on claude.ai. In your user settings (or managed settings): nothing more is downloaded, previously synced plugins (~/.claude/plugins/synced) are hidden from every session started afterwards and moved to ~/.claude/plugins/.trash at the next launch (deleted after cleanupPeriodDays; re-downloaded, not restored, if you re-enable)."

- **結論**（全部【推論】，§8 :339-360）：
  - Claude Code 本體是寫入者候選，在字串層級得到支持（VS Code 擴充與桌面 app 內附版本都帶有同一段程式）。
  - 實際的寫入呼叫沒有被看到。
  - 消費方式的線索很弱。
- **UNKNOWN**（§8 :351-356）：
  - 實際寫入呼叫的位置
  - 寫入時機、觸發條件、頻率
  - 哪一支程序寫入
  - `.marketplaces.json` 的消費方式
  - `marketplaces.json` 其餘 76 筆命中的內容

## 時間對照（推論，待驗證）

**只有相關性，不能證明因果；只有啟動後的紀錄不能證明因果；每次啟動不一定等於每個新視窗或 session。**「開新 session 就改寫」只是待驗證的推論。

| 觀測 | 兩檔觀測到的最後修改時間（美東） | UTC | 當時報告產出時間（UTC，取自報告檔名） |
|---|---|---|---|
| 一 | 2026-10-07 11:32:35（兩檔） | 15:32:35【推論：美東 +4 換算】 | `2026-10-07T174353Z` |
| 二 | 2026-10-07 16:29:00 / 16:28:59 | 20:29:00 / 20:28:59【引用：`2026-10-07T212031Z-ticket148-r2-reapproval-prep.md` :81、:87】 | `2026-10-07T211219Z` |
| 三 | 2026-10-07 20:14:43（兩檔） | 2026-10-08 00:14:43【推論：美東 +4 換算】 | `2026-10-08T004652Z` |
| 四 | 2026-10-08 09:00:42（兩檔） | 13:00:42【引用：`2026-10-08T131715Z-ticket149-r5b-diagnosis.md` :144、:150】 | `2026-10-08T131715Z` |

- 觀測一～三的美東值出處見〈待查問題〉第 7 項。
- 觀測四旁證【引用】:T149-1 所在 session 的 scratchpad 目錄,`ls -la` 顯示 `.` 為 `Oct  8 09:00`、`..` 為 `Oct  8 09:02`(`2026-10-08T131137Z-ticket149-r5-diagnosis.md` §0 :71-72)。
  - 【推論】`ls` 顯示的是本機時間,這裡推定為美東;精度只到分鐘。
  - 這只是同一分鐘的相關性,不證明 session 啟動造成改寫。
- 前三次觀測時,session 的啟動時刻:UNKNOWN(沒有紀錄)。

## 處置方案比較

設計（裁決者提供，2026-10-08）：

| 方案 | 保障 | 缺口 |
|---|---|---|
| 1 保留 hash 核准 | 任何變動都需人決定 | 操作負擔重;核准時看不到遮罩欄位,對內容的實際把關有限;次數多易流於形式 |
| 2 精確契約驗證 | 固定欄位符合 Jeff 核准值,擋多筆、換名、結構改變 | 允許變動的欄位是否影響載入 UNKNOWN;不能證明真正的市集身分;閘門需讀使用者層內容 |
| 3 停用同步 | 可能減少變動來源 | 停用後兩檔是否仍變動 UNKNOWN;synced 結構會改變,需再核准;屬改使用者設定的高風險動作;失去 claude.ai 外掛同步 |
| 4 完全排除兩檔 | 不再被擋 | 兩檔可被改成任何內容都不被發現(僅供比較) |
| 5 方案 1 加工具化 | 同方案 1 | 只減操作成本,不減核准次數 |

## 方案 2 契約 v3（定稿）

設計（Jeff 裁定）。下列條文為裁決者提供之設計內容,逐條寫入。

1. **範圍**
   - 只適用 `plugins/<bucket>/.marketplaces.json` 與 `plugins/<bucket>/.last-complete-round`。
   - 其餘登記與任何新出現的檔案,維持 hash 嚴格比對;多出或缺少都硬擋。
2. **讀檔**
   - 程序:S0 lstat → 開檔後 S1 fstat → 最多讀上限+1 byte → S2 fstat → 關檔後 S3 lstat。
   - S0:一般檔、非連結、非 reparse。
   - S1:一般檔、非 reparse;身分、大小、修改時間 = S0。
   - 讀取:超過上限即擋。
   - S2:一般檔、非 reparse;大小、修改時間 = S1。
   - S3:一般檔、非連結、非 reparse;身分、大小、修改時間 = S1。
   - 任一不符或錯誤即硬擋。不宣稱能排除所有競態。
3. **`.marketplaces.json`**
   - 基本:上限 1024 bytes;UTF-8;JSON 拒絕重複鍵;型別嚴格(布林不當整數、字串不當數字)。
   - 頂層:鍵剛好 `etag`、`rows`、`parserVersion`。
   - `parserVersion`:整數 1002,改變即擋。
   - `rows`:陣列,剛好 1 筆,且為物件。
   - `rows[0]`:鍵剛好 `name`、`display_name`、`scope`、`source`、`id`、`updated_at`。
   - 固定字串(逐字):`name` = `anthropic-plugin-directory`、`display_name` = `Anthropic Directory`、`scope` = `default`。
   - `source`:以解析後內容比對;物件,鍵剛好 `source`,值為字串 `claudeai`。
   - `id`:字串,以 `marketplace_` 開頭;sha256(解析後字串的 UTF-8 bytes)等於 Jeff 核准值 `41e3e4753c1d07398036cde9eb538cfda495c2a6deccd5899dc38458141a1e70`。
   - `etag`(允許變動):長度 1–128;只含可列印 ASCII;不含空白與控制字元。
   - `updated_at`(允許變動):完全符合 `YYYY-MM-DDTHH:MM:SS.ffffffZ`(小數 6 位、Z 結尾),且日期時間真實存在。
4. **`.last-complete-round`**
   - 一般檔,剛好 37 bytes,ASCII。
   - 前 36 字元為全小寫 UUID;版本位 `4`;variant 位屬於 `8`/`9`/`a`/`b`。
   - 第 37 byte 為 `0x20`。
   - 允許 UUID 值變動;寫入機制 UNKNOWN。
5. **接線**
   - 契約放進既有 `.agents/extension-inventory.json`。
   - schema 升為 version 2:
     - version 1 維持現行語意,出現 `contract` 即損壞。
     - version 2 每筆剛好有 `sha256` 或 `contract` 其一。
     - 其他版本號即損壞。
   - 契約名稱寫死在程式碼:
     - `synced-marketplaces-v1` 只能用在 `.marketplaces.json` 路徑。
     - `synced-last-round-v1` 只能用在 `.last-complete-round` 路徑。
   - 以下一律損壞(fail-closed):其他路徑使用 `contract`、兩契約互換路徑、pins 缺項/多項/型別錯誤。
   - 不變的部分:現行 policy-only 通道路徑、HEAD/index 選取與混合提交規則。
   - `redlight._extension_inventory_ok` 須擴充。
   - 測試、程式、policy 的提交順序依既有流程。
6. **失敗處置**
   - 任何違反 ⇒ R10 fail-closed 硬擋。
   - 原因代碼寫類別與欄位;錯誤訊息不含任何值。
   - 影子模式下仍硬擋。
7. **保障與限制**
   - 固定欄位只證明內容符合 Jeff 核准的值,不證明真正的市集身分。
   - 額外檔案檢查只能擋 commit,不能保證 commit 前沒有外掛被載入;runtime 仍 UNPROVEN。
   - 允許變動的欄位是否影響載入:UNKNOWN。
   - 閘門會讀這兩檔內容。
8. **紅燈測試清單(18 項)**
   1. 合法內容放行;只改允許變動的值(`etag`、`updated_at`、`.last-complete-round` 的 UUID 值)放行。
   2. 每個固定欄位各改一個值 ⇒ 擋。
   3. 多一個鍵或少一個鍵(頂層、`rows[0]`、`source`)⇒ 擋。
   4. 重複鍵(頂層、`rows[0]`、`source` 內)⇒ 擋。
   5. 型別錯誤 ⇒ 擋:`parserVersion` 為 `true` 或 `"1002"`、`rows` 為物件、`rows[0]` 為陣列、`source` 為字串、`source.source` 不是字串、`name` 為數字、`id` 不是字串。
   6. `id`:沒有 `marketplace_` 前綴、hash 不等於核准值 ⇒ 擋;含跳脫字元的 `id` 以解析後的值算 hash,不符即擋。
   7. `etag` 違反長度 1–128,或含空白、控制字元、非 ASCII ⇒ 擋;`updated_at` 不符合精確格式或日期不存在 ⇒ 擋。
   8. `rows` 為 0 筆或 2 筆 ⇒ 擋。
   9. 不是 UTF-8、不是 JSON、頂層不是物件 ⇒ 擋。
   10. 實際讀到的大小超過上限(包括開檔前看起來小、讀的時候變大)⇒ 擋。
   11. `.last-complete-round` 以下任一 ⇒ 擋:36 或 38 bytes、結尾不是 `0x20`、不是 UUID 形狀、含大寫、版本位不是 `4`、variant 不屬 `8`/`9`/`a`/`b`、含非 ASCII。
   12. 連結或 reparse 點(在 S0、S1、S2、S3 任何一步出現)⇒ 擋;檔案缺少 ⇒ 擋。
   13. 讀取競態 ⇒ 擋:S0 與 S1 的身分、大小或修改時間不一致;S1 與 S2 不一致;S3 與 S1 不一致。
   14. 契約與 schema 損壞 ⇒ 擋:同時有 `sha256` 和 `contract`、兩者都沒有、契約名稱不認得、pins 缺項/多項/型別錯誤、version 1 出現 `contract`、版本號不明。
   15. 把契約掛到外掛本體檔或其他任何路徑 ⇒ 擋;兩個契約互換路徑 ⇒ 擋。
   16. 影子模式下,以上各情況仍然硬擋。
   17. 所有錯誤訊息都不含任何欄位值。
   18. 回歸:其餘登記的 hash 行為不變;version 1 的 inventory 行為不變。

**固定值的觀測出處**【引用】(設計值本身由裁決者提供,下列只記錄觀測支持):

- `name` / `display_name`:R2 報告 `2026-10-07T212031Z-ticket148-r2-reapproval-prep.md` :108-109。
- `parserVersion` 1002、頂層鍵、rows 鍵、rows 筆數:同報告 :103-107。
- `scope` / `source`:
  - R2 只記錄 `scope` 是長度 7 的字串(:110)、`source` 是鍵為 `['source']` 的物件(:111)。
  - 值 `default` / `claudeai` 在 `.dev/reports/` 中最早只出現於 R7 程式的比對常數(`2026-10-08T134434Z-ticket149-r7-format-check.md` :254、:266)。
  - R7 輸出 `MJ_SCOPE_EQ=True`(:479)、`MJ_SOURCE_VALUE_EQ=True`(:483)。
  - ~~更早記錄原值的報告:UNKNOWN(Grep `claudeai`、`"default"` 只命中 R7)。~~
  - 在既有報告檔（.dev/reports/）中未找到更早紀錄（Grep 只命中 R7）。聊天紀錄中的 R1b 原文有記錄 `scope: "default"` 與 `source: {"source":"claudeai"}`；來源性質：聊天紀錄，不在 repo 內，由裁決層轉述，本 repo 沒有獨立紀錄。
- `.last-complete-round` 結尾為空白:R2 報告 :100(遮罩後 `'<id> '`);R7 `LCR_LAST_BYTE_IS_0x20=True`(:525)。

### 裁定紀錄

- 2026-10-08 09:10 美東,逐字:

  > 「裁 C：先唯讀診斷，再查安裝檔中的讀寫控制流；乙限被動記錄，不啟動或操作 app、不觸發同步。接受唯讀核對 repo 名冊的偏離並記錄來源。暫不重新核准、不改 index、不 push。」

- 2026-10-08 09:14 美東,逐字:

  > 「授權依 R1 報告 §3 原文重建 r1-148-diag.py；sha256 必須符合指令中的完整值才可使用，不符即停止。其餘沿用既有唯讀診斷授權，不改 index、不重新核准、不 commit、不 push。」

- 2026-10-08 09:39 美東,逐字:

  > 「1a、2a、3 依檢查結果決定、4a、5 照辦、6 授權、7b、8a。只做格式檢查與設計；不變更現行 policy、不改 index、不commit、不 push。」

- 2026-10-08 09:52 美東,逐字:

  > 「裁決：裁:UUID 採小寫版本 4，variant 為 8/9/a/b；id 採用 R7 候選 hash。流程照上述順序進行，不 push。」

  - 「R7 候選 hash」= `41e3e4753c1d07398036cde9eb538cfda495c2a6deccd5899dc38458141a1e70`。
  - 「上述順序」依指令轉述:T149-2 寫入設計與觀測並重新暫存 → 第四次核准準備(只準備、不核准)→ Jeff 親自核准 → 提交票 149 → 149 第三站紅燈與第四站實作;實作期間若再被擋,照規定停下,不繞過。
  - 「上述順序」的轉述來源性質:由裁決者轉錄於指令,本 repo 沒有獨立紀錄。

## 格式檢查（R7）

出處:`2026-10-08T134434Z-ticket149-r7-format-check.md`。輸出只有真假、整數、字元種類計數、sha256、UUID 版本位、固定格式時間,沒有印出任何原值。

- **讀檔程序在本機可行**【引用】:
  - 兩檔的 `S1_ident_nonzero`、`S0S1_same_ident`、`S3S1_same_ident` 都是 True(:443-444、:456、:503-504、:516)。
  - ⇒ 此環境 fstat / lstat 的身分欄位可用。
  - 其他檔案系統(網路磁碟、FAT 等):UNKNOWN(:594)。
- **各項檢查全部符合 v3 預期**【引用】:不符 0 項,沒有任何檔在讀檔程序中被停止(§4 表 :538-560)。
- **id 後段**【引用】:`marketplace_` 之後 24 字元,`lower=6,upper=14,digit=4,underscore=0,hyphen=0,other=0`(:486-487)。
  - 【推論】單一樣本,不能推定其他 id 的格式(:575)。
- **`.last-complete-round`**【引用】:前 36 字元為全小寫 UUID、版本位 `4`、variant 屬 `8`/`9`/`a`/`b`(:526-529);37 bytes、結尾 `0x20`(:523、:525)。
- **id 的 hash**【引用】:`41e3e4753c1d07398036cde9eb538cfda495c2a6deccd5899dc38458141a1e70`(:488)。
  - 這是 Jeff 裁定採用的核准值,尚未寫入 policy。
- **兩檔指紋**【引用】:與 R5 目前值相同(:584-587)。這只是兩個時點的比較,不能排除期間變動後又恢復。

## 第四站實作（S4-149）

### 裁定紀錄（逐字）

- 2026-10-08 09:52 美東(見〈裁定紀錄〉):「裁決：裁:UUID 採小寫版本 4，variant 為 8/9/a/b；id 採用 R7 候選 hash。流程照上述順序進行，不 push。」
- 2026-10-08 11:16 美東:「裁：接受 -rA 並記錄；介面照封存版並附第四站條件；紅燈測試獨立 commit，不 push。」
- 打包登記:「裁:兩檔標 copy，併入第四站 L1；只加打包清單兩條登記，不動名冊，不 push」
- 裁甲:「裁甲：授權在 tests/test_redlight.py 檔尾追加票 149 測試；先列定新增代碼與契約對照、封存逐 node 預期，再取得紅燈並獨立 commit。既有測試與封存代碼不改；打包清單留待第四站，不動名冊、不 push。」
- 裁決助手審查意見(**非 Jeff 裁決原文**):
  - 「直接進第四站，避免再多一個文件 commit 與被擋的機會。第四站指令要完整附上已定的四項條件、介面與原因代碼；紀錄隨第四站審計與票面更新一併提交，不用等整票收尾。」「version 2 名冊仍由你親自核准；本輪不 push。」「這是新測試檔必要的打包登記，不涉及放寬 R10 或修改名冊。」
  - 13:55 美東接續:「建議 A。這是 production 呼叫方式的相容性修正，仍在既有實作範圍內，不必再要求你填一次裁決。將呼叫改為第四個位置參數，保留 synced=None，不改測試；接著重跑 150 項、全套與淨室，全部符合才 commit。接續指令記錄這次偏離與完整帳本基準即可。不動名冊、不 push。」
- `-rA` 偏離:T149-4 執行時多加 `-rA`,已依 11:16 裁決接受並記錄。

### 四項條件與實作位置(`.claude/hooks/redlight.py`,S4-149-1 版本行號)

| 條件 | 原文(裁決助手審查定稿) | 實作 |
|---|---|---|
| C1 路徑接線 | 把兩個契約檔的實際路徑傳給 synced_contract_check;「額外」「缺少」的現行算法不變;extension_report 的 synced 六鍵形狀不變;契約檢查失敗 ⇒ mismatch 計 1 筆,reason 附「類別+欄位」 | 實際路徑 `_synced_contract_real_path` :1911-1925;呼叫與計數 :1970-1978;額外 :1961、缺少 :1962(算式未改);六鍵初值 :1940(未改);reason 附代碼 :1979-1988 |
| C2 單一判定來源 | version 2 名冊時,`_extension_inventory_ok(doc)` 必須等於 `(extension_inventory_check(doc) is None)` | `_extension_inventory_ok` :1309-1318;version 1 本體改名 `_extension_inventory_v1_ok` :1321(本體未改) |
| C3 檔案屬性 | posix ⇒ 缺 `st_file_attributes` 視為無 reparse;windows ⇒ 任一步取不到即擋(`contract_read/S<n>_attr_missing`);連結判定 S0、S3 兩平台都做;`_SYNCED_PLATFORM` 每次呼叫時讀取 | `_contract_stat_bad` :1452-1466(平台讀取 :1459);預設值取自實際平台 :1069 |
| C4 缺檔 | 只計 missing 1,不另計 mismatch;reason 含 contract_read 與 missing,不含欄位值 | :1962、:1966-1969 |

### 介面與原因代碼(引用,不重抄)

- A1–A5、version 2 項目形狀、pins 形狀、原因代碼表:`.dev/reports/2026-10-08T150245Z-ticket149-t149-4-redlight.md` §C :79-125。
- A6 平台替換點、A1/A4 語意增補、`S0–S3_attr_missing`、檢查順序:`.dev/reports/2026-10-08T164833Z-ticket149-t149-6-redlight.md` §3 :93-118。
- N1–N4(`S0–S3_error`、`read_error`、`S0–S3_type`、名冊的 `$`/`schema`/`entries`/`path`/`note`/`sha256`/`contract`):`.dev/reports/2026-10-08T174022Z-ticket149-t149-8-r3-redlight.md` §3 封存檔全文。未新增 `contract_read/path`,也未使用表外代碼。
- A1 定義 `synced_contract_check` :1637-1656;A2 `extension_inventory_check` :1363-1375(規則 :1378-1422);id 核准 hash 只從名冊 pins 讀(:1601),程式內沒有寫死。

### 第三站測試(共 150 項,不是「150 項紅燈」)

| commit | 檔案 | 項數 | 基準結果 |
|---|---|---|---|
| `147a25ef6fe7e154ca0e72fec786cc48c8954d67` | `tests/test_synced_contract_149.py` | 102 | 95 失敗 / 7 通過 |
| `407c481db128edb7cbbdc66c784c59e808a1f21c` | `tests/test_synced_platform_149.py` | 18 | 16 失敗 / 2 通過 |
| `68c730edb58d48c1b170560272b14aa79bcdf4a8` | `tests/test_redlight.py` 檔尾 t149 | 30 | 30 失敗 |

合計基準 141 失敗、9 通過。

### 第四站三次送出

1. **第一次**:基準全套 113 failed(預期 111);多出的 2 個是 `test_manifest.py:216`、`test_upstream_manifest.py:69` —— 兩個新測試檔沒有登記在 `.agents/portable-manifest.txt`。依打包登記裁決標 `copy`,併入 S4-149-1。出處:`2026-10-08T170843Z-ticket149-s4-implementation.md`。
2. **第二次**:第一刀改 `redlight.py` 被前哨 R3 擋下 —— R3 只認配對測試檔 `tests/test_redlight.py` 的票 149 紅燈。依裁甲由 T149-8 在該檔尾補 30 項紅燈(`68c730e`)。出處:`2026-10-08T172211Z-ticket149-s4-implementation.md`。
3. **第三次**:R3 放行;150 項全過,但既有 `test_t146_31` 失敗 —— 呼叫處以關鍵字 `synced=synced` 傳參,測試替身 `counting(facts, surfaces, *inventory)` 不收關鍵字參數。停下回報。出處:`2026-10-08T175131Z-ticket149-s4-implementation.md`。
4. **第三次・接續(本輪)**:依 13:55 接續意見,只把呼叫改為第四個位置參數(:2116),函式簽名維持 `(facts, surfaces, inventory, synced=None)`;**未改任何測試**。

### 流程教訓

- 第三站紅燈除了新檔,也要跑全套(打包清單這一類「全庫性質」的測試只在全套裡出現)。
- 紅燈測試要放在 R3 認可的配對測試檔(`tests/test_<模組>.py`),否則第四站第一刀就被擋。
- 內部函式加參數時,以既有測試替身的呼叫形式為準(本次:替身只轉交位置參數)。

### 第五次攔截與第五次核准

- **第五次攔截**【引用】:T149-5 提交紅燈測試時被 R10 擋下(2026-10-08 美東約 11:17;報告 `2026-10-08T151758Z-ticket149-t149-5-redlight-commit.md`)。
- **第五次核准**【實測】:`6d667a3713dfe8760c28475ef1a0ff0835a8705b`,policy-only,Jeff 2026-10-08 12:36:55 美東;inventory blob `b3fb9fd5cf840c081a8ca3f0b9904ff4eb64da22`。
- **計數**:攔截 5、核准 5。
- **R9 觀測**【實測,並列事實不推論】:兩檔觀測到的最後修改時間 12:22:21 美東;R9 視窗 scratchpad 的建立時間同在 12:22 這一分鐘。寫入者 UNKNOWN。目前內容符合契約 v3;被遮罩值的歷史比較 UNKNOWN。

### 現場狀態

- 名冊 `.agents/extension-inventory.json` **仍為 version 1**,本站未改。S4-149-1 的成果是「支援契約、待 policy 啟用」:契約要等 Jeff 親自核准 version 2 名冊後才在現場生效。
- runtime 仍 UNPROVEN;讀檔程序不宣稱能排除所有競態。

### 前檢證據摘要(工作樹,S4-149-1 提交前)【實測】

- 兩個新檔:120 passed。
- `tests/test_redlight.py`:302 passed、7 skipped、0 failed(t149 30 項、`test_t146_31` / `_35` / `_44` / `_45` 皆 passed)。
- 全套:2490 passed、10 skipped、3 xfailed、0 failed(= 基準 2349 passed + 141);skipped 原因逐行與基準相同。
- 淨室(`verify_gates.py`):rc 0;R1–R10 各擋下一次(R10 正控放行);新 repo 框架測試 2340 passed、14 skipped、3 xfailed;新 repo 帶入兩個新測試檔。
- 出處:`.dev/reports/` 本輪第四站報告。

## 待查問題(全部 UNKNOWN,本票不作答)

1. 寫入者。
2. 用途與消費方式。R1c 報告 Q2(b) 的結論是:`.marketplaces.json` 的消費方式 UNKNOWN,不能判定「沒有載入效果」(:120、:126)。
3. 變動原因。
4. 變動頻率,以及是否每輪同步都會改。
5. 兩次觀測之間,是否還有未觀測到的改寫。（觀測三之後仍無法回答）
6. `rows[0].updated_at` 欄位與觀測到的 mtime 之間的關係。
7. 三次觀測中，兩檔觀測到的最後修改時間是否總在同一時刻附近（只列觀測值，不推論機制）。
   - 觀測一：`.last-complete-round` 2026-10-07 11:32:35 美東；`.marketplaces.json` 2026-10-07 11:32:35 美東。出處：`2026-10-07T174353Z-ticket146-s5-r1-resnapshot.md` §3 raw :160、:166。
   - 觀測二：`.last-complete-round` 2026-10-07 16:29:00 美東；`.marketplaces.json` 2026-10-07 16:28:59 美東。出處：`2026-10-07T211219Z-ticket148-r1-diagnosis.md` §1 :71、:77。
   - 觀測三：`.last-complete-round` 2026-10-07 20:14:43 美東；`.marketplaces.json` 2026-10-07 20:14:43 美東。出處：`2026-10-08T004652Z-ticket148-r3-diagnosis.md` §2 :117、:123。
8. `.marketplaces.json` 與 `.last-complete-round` 的實際消費方式（R6 後仍 UNKNOWN）。
9. 開新 session 與改寫之間的關係（只有相關性證據）。

## 處置原則(Jeff 裁決)

2026-10-07 19:07 美東,逐字:

> 「選甲：先立票 149，單獨 docs commit，再進 148 第四站。
> 149 只記錄兩次 hash 不符的觀測、核准與攔截證據；写入者、用途、變動原因仍 UNKNOWN，mtime 不當作寫入事件時間，不預裁放寬檢查。
> 若 R10 再擋，先停下診斷；是否重新核准仍由你決定，不能預設自動照辦。此輪不 push。」

2026-10-07 17:14 美東,逐字節錄:

> 「同意另立票 149，只記錄證據與待查問題，先確認號碼未占用。」「票 149 不預裁放寬 metadata 檢查。眼前核准與立票分開提交」

歸納:
- R10 再擋時,先停下診斷。
- 是否重新核准由 Jeff 決定,不預設自動照辦。
- 本票不預裁放寬 metadata 檢查。

## 流程紀錄

- T149-0 流程偏離：指令要求 Read 的七項來源中，有四份報告（205822Z、211219Z、212031Z、214331Z）該輪未重新 Read，數值憑同 session 先前內容寫入；裁決者事後對照報告核對數值一致（2026-10-07）。偏離依 Jeff 裁決保留紀錄。
- T149-1：本輪 Read 的來源清單見報告；依 Jeff 2026-10-08 07:48 裁決補記日期更正。
- T149-2：本輪 Read 的來源清單見報告；T149-1 的 Grep 名冊偏離已依 Jeff 2026-10-08 09:10 裁決接受，來源 .agents/extension-inventory.json。
- T149-3：修正 scope／source 出處說明（區分 repo 報告與聊天紀錄）；補記第四次核准。
