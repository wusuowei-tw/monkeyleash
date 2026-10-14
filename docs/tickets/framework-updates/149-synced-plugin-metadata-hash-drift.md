# 票 149 —— synced 外掛 metadata 兩檔於 2026-10-07 兩次與已核准 hash 不符(R10 攔截紀錄)

**狀態**:~~**立案(未排程)。**~~ ~~**調查中（T149-1 補記觀測三；寫入者、消費方式、變動機制待唯讀偵察）。**~~ ~~**設計完成（方案 2 契約 v3 定稿，Jeff 裁定 2026-10-08）；待第四次核准後提交，接著進第三站紅燈。**~~ ~~**設計完成；第四次核准完成（26b2224，Jeff 2026-10-08）；待第三站紅燈。**~~ ~~**第四站實作中（S4-149-1；前檢通過）；待正式結果。**~~ ~~**第四站已實作並正式驗證（S4-149-1 b64a2d6a0a4168fd41a037c6516318eb59d49a74）；支援契約，待 Jeff 核准 version 2 名冊後啟用；待第五站獨立審查。**~~ ~~**第五站審查包已提交（S5-149-0）；待全新視窗獨立審查。**~~ ~~**第五站獨立審查完成（S5-149-1，PASS-with-notes，阻擋 0）；結果已記錄（S5-149-2）；推送前須補全套。**~~ ~~**第五站獨立審查完成（S5-149-1，PASS-with-notes，阻擋 0）；結果已記錄（S5-149-2）；第七次核准完成（60c5531，version 2 契約啟用）；推送前須補全套（先解決測試隔離範圍）**~~ **收尾完成：已推送 96db9ef（4d22101..96db9ef，fast-forward）；CI：Jeff 確認綠燈（run 明細未取得）；第九次核准已提交（6392ce4）；149 宣告生效（Jeff 2026-10-11）。**
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
      - **票 153 更正（2026-10-14，提交 `2344bb6`）**：本條「小數 6 位」已放寬為「小數秒可省略；若有，1–6 位 ASCII 數字」（票 153 P1=A）；其餘條件不變，契約名稱仍為 `synced-marketplaces-v1`（P2=A）。見 `153-synced-marketplaces-updated-at-fraction-digits.md`。
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
      - **票 153 更正（2026-10-14）**：「精確格式」依上方第 3 節 `updated_at` 的更正；對應測試見 `tests/test_redlight.py::TestTicket153UpdatedAtFraction`，原 `test_item07_format_blocks[updated_at-5digits]` 一格已移除（Jeff 核准）。
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
- N1–N4(`S0–S3_error`、`read_error`、`S0–S3_type`、名冊的 `$`/`schema`/`entries`/`path`/`note`/`sha256`/`contract`):`.dev/reports/2026-10-08T174022Z-ticket149-t149-8-r3-redlight.md` §3 封存檔全文。未新增 `contract_read/path`,~~也未使用表外代碼。~~ 更正（2026-10-09，S5-149-1 F-5）：實作另產生四種封存表未列的 contract_type 組合，經 Jeff 2026-10-09 裁決新增核准，見〈第五站獨立審查（S5-149）〉。
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

- ~~名冊 `.agents/extension-inventory.json` **仍為 version 1**,本站未改。S4-149-1 的成果是「支援契約、待 policy 啟用」:契約要等 Jeff 親自核准 version 2 名冊後才在現場生效。~~
- 更正（2026-10-10）：第七次核准 `60c5531` 起，名冊為 version 2，契約已啟用；見〈第七次攔截與 version 2 啟用（D7／V2P／V2S／V7）〉。
- runtime 仍 UNPROVEN;讀檔程序不宣稱能排除所有競態。

### 前檢證據摘要(工作樹,S4-149-1 提交前)【實測】

- 兩個新檔:120 passed。
- `tests/test_redlight.py`:302 passed、7 skipped、0 failed(t149 30 項、`test_t146_31` / `_35` / `_44` / `_45` 皆 passed)。
- 全套:2490 passed、10 skipped、3 xfailed、0 failed(= 基準 2349 passed + 141);skipped 原因逐行與基準相同。
- 淨室(`verify_gates.py`):rc 0;R1–R10 各擋下一次(R10 正控放行);新 repo 框架測試 2340 passed、14 skipped、3 xfailed;新 repo 帶入兩個新測試檔。
- 出處:`.dev/reports/` 本輪第四站報告。

### 第六次攔截與核准

- **S4-149-2 第一次送出被 R10 擋下**【引用】(報告 `2026-10-08T181701Z-ticket149-s4-implementation.md`;時間:美東 14:17 之前 —— 該報告產生於 18:17:01Z,commit 1 為 14:10:25 美東):

  ```
  [六站閘門/pre-commit] commit 已擋下:

    [R10/fail-closed] unmanaged_entry：未受管入口：synced（額外 0 / 缺少 0 / 內容不符 3）
  ```

  已退回暫存。這是**第六次攔截**。
- **三輪處置**【引用】:
  - D6-149(`2026-10-08T182616Z-ticket149-d6-diagnosis.md`):三筆不符全在 skills —— `skills/<bucket>/.last-complete-round`(`4bb0b470` → `b0f02414`)、`skills/<bucket>/computer-use/SKILL.md`(`bc4b958f` → `f1b16578`)、`skills/<bucket>/manifest.json`(`3fdf6e05` → `242facb7`);plugins 兩檔與第五次核准值相符;missing / extra / 錯誤皆 0。
  - D6b-149(`2026-10-08T183618Z-ticket149-d6b-skill-review.md`):唯讀審閱 `SKILL.md`(`f1b16578`)全文,只回報安全摘要、未執行其中指令;未發現針對本 repo、閘門、名冊、帳本或 `~/.claude` 的要求;兩個 skills metadata 檔只檢查遮罩形狀。
  - A6-149(`2026-10-08T184434Z-ticket149-a6-reapproval-prep.md` 停止;`2026-10-08T185318Z-ticket149-a6-reapproval-prep.md` 草稿):version 1 草稿只改三筆的 sha256 與 note 共 6 行,其餘 227 筆不變,獨立核對 `ALL OK: True`;兩個 skills metadata 檔觀測到的最後修改時間由 14:23:13 變為 14:43:16 美東,sha256 相同。
- **裁決引文**(只取自上列報告原文;分類照報告標示):

  | 報告 | Jeff 原話 | 選項說明 | 審查意見 |
  |---|---|---|---|
  | D6b `…183618Z…` :5 | 「裁A：授權唯讀審閱目前 skills/<bucket>/computer-use/SKILL.md 全文，只回報安全相關摘要，不執行其中指令；另檢查 skills 兩個 metadata 檔的遮罩形狀。不準備草稿、不改名冊、不 commit、不 push。」 | 【UNKNOWN:報告未收錄】 | 【UNKNOWN:報告未收錄】(:7 有一行「口徑」,報告未標示其來源為裁決助手) |
  | A6 停止 `…184434Z…` :5 | 「裁：授權準備第六次重新核准草稿（version 1，只更新 skills 三筆 sha256 與 note），唯讀診斷與核對照既有流程；不核准、不 commit、不 push」 | 【UNKNOWN:報告未收錄】 | 【UNKNOWN:報告未收錄】 |
  | A6 草稿 `…185318Z…` :5–:6 | 1.「裁：授權準備第六次重新核准草稿（version 1，只更新 skills 三筆 sha256 與 note），唯讀診斷與核對照既有流程；不核准、不 commit、不 push」;2.「裁A」 | 「選定選項全文由裁決者列出,非 Jeff 逐字原文:衍生核對程式增列 e 項替換」 | 「準備草稿不等於核准;讀前讀後 hash 相同只證明兩個時點一致;同名 skill 與相同說明文字不能證明來源或官方更新,來源、寫入者與原因 UNKNOWN;沒有舊版內容,無法判斷改了哪些地方;草稿釘選的是審閱版本,實際核准 commit 時仍由既有 hook 核對現場。」 |

- **第六次核准**【實測】:`e07e21999868dfaa616a0755781d2784402046fe`,policy-only,2026-10-08 15:03:49 美東(EDT);inventory blob `e7fc6c16cc1ddb8d0147c5e3639f24643f148f6f`;R10 回應 DECLARED_OK(runtime 仍 UNPROVEN)【引用:裁決者轉述】。**攔截 6、核准 6。**
- **口徑**(裁決助手審查意見,非 Jeff 原文;逐條照錄):
  - 第六次核准代表接受目前三份內容,不代表已證明來源、更新原因或執行安全。
  - 這是「首次觀測到」這三筆不符,不能證明第一次變動。
  - 同名 skill 與相同說明文字不能證明來源或官方更新。
  - 讀前讀後 hash 相同只證明兩個時點內容一致。
  - 兩個 skills metadata 檔在兩個觀測時點內容一致、修改時間不同,不能確定期間發生了什麼。
  - 沒有舊版內容,無法判斷改了哪些地方。
  - 「目前文件未描述可疑外部連線」不代表已驗證實際執行行為。
- **範圍說明**:~~名冊仍為 version 1。~~（更正 2026-10-10：第七次核准 `60c5531` 起為 version 2。）契約 v3 只涵蓋 plugins 兩檔,本次 skills 三筆不在契約範圍;version 2 仍會偵測並擋下這類變動(逐檔 hash)。
- **重送紀錄**:S4-149-2 重送第一版因指令使用 `cp` 被前哨 R7 擋下(報告 `2026-10-08T190946Z-ticket149-s4-2-commit.md`),屬指令錯誤,**不計入 R10 攔截**。

## 第五站獨立審查（S5-149）

### 裁定紀錄（逐字）

1. 「進第五站。先產審查包，再由全新視窗獨立審查；站別只改 current_stage 為 review，保留 ticket 149 與其他欄位。審查包須分清正式 pytest 對應的 code commit（b64a2d6）、後續 docs 與 policy commit，以及尚未實測的真實 POSIX 環境與 CI。重點核對 C1–C4 四項條件、version 1 名冊行為不變、id 核准值取自名冊不寫死、契約違反一律 fail-closed 且訊息不含欄位值。目前仍不 push、不改名冊。」
2. 「裁A＋C：接續複本三檔、突變探針與逐題審查，跳過原 repo 全套；全套證據缺口是否阻擋，由審查者判斷。F-1／F-2 測試隔離與 F-3 R7 漏判分別記為候選，立票與排程另裁。不 commit、不 push、不改名冊。」
3. 「裁：接受第五站 PASS-with-notes。F-5 選 A，新增核准四種代碼組合並保留更正紀錄，補測試列候選；F-6 選 A，記錄寫入範圍偏離並列候選，P6 不補做。進 S5-149-2 記錄結果。推送前補全套；若另裁允許先推再驗 CI，收票前確認對應 HEAD 的 CI。不 push、不改名冊。」

裁決助手審查意見(**非 Jeff 裁決原文**):

- 「接受附註不代表 F-5、F-6 已修復。」
- 「F-5：寫成『新增核准的四種組合』，保留原封存表與更正紀錄，不能回寫成當初已有封存或測試。」
- 「尚未 push，就無法取得該次 push 觸發的 CI。」
- 「F-6 要保留『本輪曾寫入未授權的系統暫存目錄』這項偏離；不能據此推定以前每輪也都如此。」
- 「先前報告中『未觀測使用者層／已隔離』的宣稱需要重新評估；不得斷言先前每次全套都讀過真實檔。」

### 結論摘要

- 審查對象 HEAD `cb3d1a81861d49a2dbbfc13a713a286ebbec38a5`;全新視窗。第一次因原 repo 全套隔離無法確認而停止;依裁決 2 改在獨立複本跑三檔、突變探針、逐題審查。
- **PASS-with-notes,阻擋 0**;複本三檔 422 passed / 7 skipped / 0 failed;探針 P1–P5 轉紅數與預期逐一相同;(h) 不符合但不阻擋;P6 未執行。
- 全套缺口:不阻擋本票審查結論;push / 收票前須補全套或 CI 紀錄。
- 詳見 `docs/audits/2026-10-09-149-station5-independent-review.md`。

### 新增核准的 contract_type 代碼組合（2026-10-09）

| category | field | 產生處(`.claude/hooks/redlight.py`,HEAD `cb3d1a8`) |
|---|---|---|
| `contract_type` | `rows[0].display_name` | :1582(`_CONTRACT_MJ_FIXED` 迴圈) |
| `contract_type` | `rows[0].scope` | :1582(同上) |
| `contract_type` | `rows[0].updated_at` | :1605 |
| `contract_type` | `etag` | :1610 |

- 此為 2026-10-09 新增核准,**非原封存表內容**;原封存表(T149-4 §C)不改。
- 目前沒有測試涵蓋這四種組合,補測試列為候選。
- 出處:續審報告 `2026-10-09T141914Z-ticket149-s5-1b-independent-review.md` (h) :102、F-5 :133。

### 寫入範圍偏離

- F-6:獨立審查的 pytest basetemp 寫入系統暫存目錄 `pytest-of-<使用者>`(未授權範圍),共 6 次;發現後停止,P6 不補做。
- 本輪曾寫入未授權的系統暫存目錄;不據此推定以前各輪也都如此。

### 候選事項（未立票）

- 甲類「測試隔離」:
  1. F-1 conftest 隔離未涵蓋 `SHADOW_CLAMP`(讀碼發現可能讀取真實檔案的路徑)。
  2. F-2 `test_mcp_server.py` 一支測試的子程序繼承真實環境。
  3. 未完成逐一盤點的呼叫點。
  4. F-4 `monkeyleash.egg-info/` 是否代表 editable install。
  5. F-6 pytest basetemp 落在 scratchpad 之外。
- 乙類「R7 判定」:
  1. F-3 `env -C <dir> python -c` 可能漏判(未實測)。
- 另列:F-5 四種組合補測試。
- 詳見審計 §7;先前報告中「未觀測使用者層／已隔離」的宣稱需要重新評估。

### 推送與收票條件

- 推送前補全套;若另裁允許先推再驗 CI,收票前確認對應 HEAD 的 CI(裁決 3)。
- 尚未 push,無法取得該次 push 觸發的 CI。

## 第七次攔截與 version 2 啟用（D7／V2P／V2S／V7）

- **第七次攔截**【引用】：S5-149-2 的紀錄 commit 被 R10 擋下，原文「[R10/fail-closed] unmanaged_entry：未受管入口：synced（額外 0 / 缺少 0 / 內容不符 2）」。兩檔已退回暫存。報告：`.dev/reports/2026-10-09T142944Z-ticket149-s5-2-record.md`（:12、:221）。
- **D7 診斷**【引用】：不符的只有 plugins 兩個契約檔（`plugins/<bucket>/.last-complete-round`、`plugins/<bucket>/.marketplaces.json`），兩檔都逐項符合契約 v3；其餘 228 筆相符；兩次診斷前後一致。報告：`.dev/reports/2026-10-09T144129Z-ticket149-d7-diagnosis.md`。
- **V2P**【引用】：version 2 草稿格式通過；以現場資料判定額外 0／缺少 0／內容不符 0；控制組（HEAD version 1）判定內容不符 2。驗證範圍只限 synced，其他入口（dev-mods、使用者 skills、commands、hooks、mcp、R4）UNKNOWN。報告：`.dev/reports/2026-10-09T145407Z-ticket149-v2p-prep.md`。
- **V2S**【引用】：在 scratchpad 隔離 clone 中以合成資料驗證：P 放行；N1／N2／N3 擋下；每案兩次輸出一致。N3 只證明「退出 policy-only、改用 HEAD 規則」（因 `worktree_differs` 擋下），沒有測到 HEAD 規則之後的檔案 hash 比對。報告：`.dev/reports/2026-10-09T150935Z-ticket149-v2s-iso.md`、`.dev/reports/2026-10-11T005923Z-ticket149-v2s-iso-b.md`。
- **V2S 範圍偏離**：有一條未帶 ISO_ENV 的唯讀 `git hash-object`，可能讀取真實 Git 全域／系統設定。依報告未影響四案；記錄，不重跑（v2s-iso-b §6）。
- **V7**【引用】：最終名冊 58787 bytes、sha256 `d75672363e24f055143dd0004104c5e54109c0b0259e3e468f66018cb9e0b5f3`、blob `ab245d5d77f5c5fafc41ef716c9de2d7c4f6fc40`；228 筆與 HEAD 相同、位置相同；兩筆契約與精確路徑一對一配對。報告：`.dev/reports/2026-10-11T011225Z-ticket149-v7-prep.md`。
- **第七次核准**：Jeff 親自 add 與 commit，產生 `60c55315538d83d6095e4ce85db0907865d973fe`（2026-10-10 21:19:09 美東；父 `cb3d1a8`；只含名冊一檔）。R10 policy-only 判定 DECLARED_OK，commit 輸出原文【引用：Jeff 貼上的終端輸出】：「[R10/policy-only] policy-only commit（policy_source=index）：staged 候選 policy 對現場成立（DECLARED_OK；runtime 仍 UNPROVEN）。這是候選驗證，不是 HEAD 已生效的 policy。」—— 這是候選驗證；runtime 仍 UNPROVEN。
- **計數**：R10 攔截 7 次、核准 7 次。第七次是首次啟用契約，plugins 兩檔從逐檔 hash 核准改為契約判定。

### 裁定紀錄

1. D7（Jeff 於 2026-10-10 確認的授權內容；非當時逐字原話）：「裁A：授權唯讀診斷兩個 synced 根目錄，列出目前不符檔案的路徑、hash、大小與修改時間。若任一 plugins 契約檔不符，允許一併檢查契約內兩檔的格式；其他檔只算 hash，不解析或展示內容。不準備草稿、不改名冊、不 commit、不 push。」
2. V2P：Jeff 原話「裁A」（`.dev/reports/2026-10-09T145407Z-ticket149-v2p-prep.md` :6）。選項說明（非 Jeff 原話；由裁決者列出、經 Jeff 以「裁A」選定）：「裁A：授權準備 version 2 名冊草稿（plugins 兩檔改為契約項，其餘 228 筆照舊逐檔 hash），以隔離程式驗證草稿格式與現場判定；policy-only 通道只做讀碼與隔離合成驗證的設計，本輪不執行、不以實際 add／commit 試驗。不核准、不 commit、不 push。」（同報告 :7）
3. V2S（Jeff 於 2026-10-10 確認的授權內容；非當時逐字原話）：「裁A：授權依 V2P §5.3 在 scratchpad 隔離 clone 以合成資料驗證 version 2 經 index 進入 policy-only 通道的接線，可在 clone 內執行 gate.py 程式碼與 git add／reset；執行前讀碼確認 gate.py／redlight.py 載入期與實際呼叫鏈（含 git 子程序及其設定來源）只使用 clone 與合成資料，無法確認即停止。負向案例含：現場不符應擋、名冊無效應擋、混合暫存應退出 policy-only 改用 HEAD 規則（以 HEAD 必定不符的合成資料預期擋下）。原 repo 僅允許前後保全核對、讀碼與本機 clone，不執行其程式、不修改；不核准、不 commit、不 push。」
4. printf（Jeff 原文；`.dev/reports/2026-10-11T005923Z-ticket149-v2s-iso-b.md` :7）：「裁A：授權以一條 printf "%s\040" 指令在 scratchpad 寫出 37 bytes 的合成 .last-complete-round，寫後以 wc -c、最後一個 byte 為 0x20 及事先算好的預期 sha256 核對；N3 預期依讀碼改為 policy_source=head 且以 worktree_differs 擋下。其餘照 V2S-149 接續；不核准、不 commit、不 push。」
5. V7（Jeff 原文，2026-10-10 21:08 美東；`.dev/reports/2026-10-11T011225Z-ticket149-v7-prep.md` :5）：「裁A，核准日 2026-10-10。VS 準備並核對最終名冊；add 與核准 commit 由我親自執行。不 push。」

D7、V2S 兩項的依據是 Jeff 確認原文（2026-10-10 21:28 美東）：「確認上列 D7、V2S 內容符合我的授權意思；記為我本次確認的授權內容，不宣稱是當時逐字原話。原報告缺漏照實記錄，接續 S5-149-2b，不 push。」

附註：原報告未存逐字原文：D7 報告（2026-10-09T144129Z）無裁決來源一節；V2S 報告（2026-10-09T150935Z）:5 僅以『…』節錄。屬回報方缺漏，依 Jeff 2026-10-10 確認補記。

### 待辦

- 推送前補全套，但須先解決測試隔離範圍（候選 F-1／F-2／F-6）；不得直接重跑可能碰到真實使用者層的指令（審查意見）。
- 真實 POSIX 環境與 CI 尚未實測。
- 「v2 經 index」的正式測試、「HEAD hash 比對」案例：列為候選。
- 回報缺失：D7、V2S 報告未存裁決逐字原文；之後每份報告須含完整逐字裁決來源。
- 不 push。

## 測試隔離盤點與隔離全套（TI-149-0～3）

- **TI-149-0（唯讀盤點）**【讀碼】：
  - F-1（`SHADOW_CLAMP`）與 F-2（status 子程序）：讀碼確認程式路徑存在。
  - 實際有哪些測試走到這兩條路徑：UNKNOWN。
  - 舊全套是否實際讀到真實資料：無法單靠讀碼斷定。
  - 報告：`.dev/reports/2026-10-11T014351Z-ticket149-ti0-isolation-recon.md`。
- **TI-149-1（殘留風險）**：
  - 殘留 R2–R7（TI-149-1 報告編號）：
    - R2：第三方套件在 import 或執行時的讀取（例：mcp 的設定類別會讀工作目錄下的 `.env`）。
    - R3：動態組合的路徑，以及寫死路徑的漏網（Grep 只抓得到字面樣式）。
    - R4：Git for Windows 的 ProgramData 設定（隔離環境下查得的來源為 0 筆，只代表查得的部分）。
    - R5：重導 LOCALAPPDATA／APPDATA 的副作用（推論不影響 import，未實測）。
    - R6：啟動時會執行的三個 `.pth`（目標都不在 repo、也不觸及 .claude；這些檔將來可能被改）。
    - R7：測試中途刪除 HOME／USERPROFILE 後，可能改用 HOMEDRIVE＋HOMEPATH（推論）。
  - 範圍偏離：多讀了一個第三方原始碼檔（mcp `server.py`，Grep 3 行），它不在該輪允許讀取的清單內。
  - 報告：`.dev/reports/2026-10-11T015548Z-ticket149-ti1-residual-risk.md`。
- **TI-149-2（指定排除 known_items 後的隔離全套，執行一次）**：
  - 記為「**含 3 項失敗的功能測試證據**」，**不是隔離證據**。
  - 結果：2475 passed、3 failed、10 skipped、3 xfailed（合計 2491）。不能以 2475 項通過概括成程式正常。
  - 結尾的家目錄檢查不符合隔離條件。這只證明「結尾時」不符合；何時、如何改變、是否沒有還原，仍待查。
  - 工具框架曾把一次輸出另存到使用者層的 session 目錄；內容沒有檢視，不能斷言其中沒有個資。
  - 這不是原 repo 全套，也不涵蓋 runtime；目前的核對方法無法證明是否曾讀取真實資料。
  - 報告：`.dev/reports/2026-10-11T021247Z-ticket149-ti2-isolated-suite.md`。
- **TI-149-3（pdb 兩項讀碼查證）**：
  - 兩項的完整 test id：
    - `tests/test_redlight.py::TestDebuggerModeCoverage::test_f3p_pdb_parsed_by_pytest_is_not_full_coverage`
    - `tests/test_redlight.py::TestDebuggerModeCoverage::test_f3c_pdbcls_alone_does_not_lower_authority`
  - 結論：讀碼支持 `-p no:cacheprovider` 可解釋兩項失敗，尚未執行驗證。
  - 推導中關鍵的一步（停用 cacheprovider 後不註冊 `lf`／`stepwise`）依據的是 repo 內的註解，pytest 原始碼沒有讀。
  - `-p no:cacheprovider` 這個參數是裁決助手與審查者先前建議加入的。
  - 第三項失敗 `tests/test_gate.py::TestAuthorityLayerIsWired::test_this_repo_itself_is_wired`：clone 沒跑 bootstrap；該測試自述新 clone 在跑 bootstrap 之前會紅【推論】。
  - 報告：`.dev/reports/2026-10-11T023456Z-ticket149-ti3-pdb-readcode.md`。

### 裁定紀錄（逐字）

1. TI-149-0（Jeff 原文，2026-10-10 21:37 美東；`.dev/reports/2026-10-11T014351Z-ticket149-ti0-isolation-recon.md` :5）：「裁A：授權唯讀盤點全套測試的使用者層、子程序環境、Git 設定與暫存寫入來源，提出隔離全套測試方案。不觀測真實使用者層、不改檔、不跑測試、不 commit、不 push。」
2. TI-149-1（Jeff 原文，2026-10-10 21:49 美東；`.dev/reports/2026-10-11T015548Z-ticket149-ti1-residual-risk.md` :5）：「裁A：授權 TI-149-1，依所列範圍讀碼、列名稱，並核對 git 設定來源與套件安裝資訊；執行前列明讀取與可能副作用。一次提出殘留風險及可選驗收方案，不宣稱完全查清或完全隔離。不跑測試、不執行 repo 程式、不改既有檔、不 commit、不 push。」
3. TI-149-2（Jeff 原文，2026-10-10 22:00 美東；`.dev/reports/2026-10-11T021247Z-ticket149-ti2-isolated-suite.md` :5）：「裁甲：接受殘留 R2–R7（TI-149-1 報告編號），授權在 scratchpad 隔離 clone 跑一次指定排除 known_items 後的隔離全套（HOMEDRIVE／HOMEPATH 一併重導、外掛自動載入不關但開跑前確認只有 anyio、bootstrap 不跑）。不改既有檔、不 commit、不 push。」
4. TI-149-3（Jeff 原文，2026-10-10 22:31 美東；`.dev/reports/2026-10-11T023456Z-ticket149-ti3-pdb-readcode.md` :5）：「裁：TI-149-2 結果記為「含 3 項失敗的功能測試證據」、非隔離證據；授權唯讀讀碼查 pdb 兩項失敗是否由本輪額外參數造成，須引用完整 test id、失敗斷言、實際 pytest 參數與判定程式碼，無法解釋即標 UNKNOWN、不視為可忽略；結尾家目錄未符合隔離條件列甲類候選，不在票 149 追查。不跑測試、不改既有檔、不 commit、不 push。」
5. S6-149-0（Jeff 原文，2026-10-10 22:47 美東；取自 S6-149-0 指令）：「裁A：進入 S6-149-0 推送前準備。只修改並提交票 149：補記 TI-149-0～3 的證據與限制，並修正狀態列粗體；唯讀查核推送流程，包含有效的 core.hooksPath、實際 hook、它呼叫的腳本，以及 push-gate 是否接在推送流程上，只讀不執行。不改 hook、不跑測試、不 push。是否接受含失敗的驗收證據、是否以 CI 完成驗證，推送前另裁。」

### 候選事項（未立票）

- 甲類：結尾家目錄檢查未符合隔離條件；何時、如何變化仍 UNKNOWN。
- pdb 兩支測試會受本次執行參數（`-p no:cacheprovider`）影響，屬於測試的脆弱點。
- 沿用既有的甲類候選 F-1／F-2／F-6。

### 待辦

- 推送前另裁：是否接受這份含失敗的驗收證據；是否以 CI 完成驗證。
- 不 push。

## 第八次攔截與核准（D8／V8）

- **第八次攔截**【引用】：S6-149-0 的票 149 commit 被 R10 擋下，原文「[R10/fail-closed] unmanaged_entry：未受管入口：synced（額外 0 / 缺少 0 / 內容不符 1）」。這是 version 2 啟用後的第一次攔截。報告：`.dev/reports/2026-10-11T142153Z-ticket149-s6-0-prepush.md`。
- **D8（診斷當下的狀態）**【引用】：
  - 不符的只有 `skills/<bucket>/.last-complete-round`，屬於逐檔 hash 項。名冊值為 `b0f02414…`（第六次核准值），現場值為 `695ec9ec…`，50 bytes。
  - 觀測到的最後修改時間是 2026-10-11T14:30:16Z，晚於 commit 被擋的時間 ⇒ 被擋當下是否就是這一筆、當時內容為何，都是 UNKNOWN。
  - 擋下訊息沒有原因代碼，只能當作線索。
  - 契約判定本輪為 UNKNOWN：R10 的 `_walk_regular` 對目錄沒有檢查 reparse，因此改用自寫腳本，不呼叫判定函式。
  - 報告：`.dev/reports/2026-10-11T143246Z-ticket149-d8-diagnosis.md`。
- **V8（唯讀核對，沒有審閱內容）**【引用】：
  - 五層路徑檢查通過；sha256 與 D8 相同；觀測到的最後修改時間是 14:40:17Z。
  - 草稿只改這一筆的 sha256 與 note，其餘 229 筆與契約項都沒變。
  - 最終 sha256 `c488412644647ca88991e669d95ea75cb77d521f0e917d0c8248d0fefb7d8c12`、blob `e4087853414706dd9ade295fcc272b51c5789fe0`。
  - add 前的現場複核（14:47:50Z）仍相符。
  - 指紋相同、修改時間不同，只能證明兩個觀測時點的結果，不能確認是否曾重新寫入相同內容。
  - 報告：`.dev/reports/2026-10-11T144126Z-ticket149-v8-prep.md`、`.dev/reports/2026-10-11T144750Z-ticket149-v8-final.md`。
- **第八次核准**：
  - Jeff 親自 add 與 commit，產生 `b9b44537542b54a56077bdb3fdf84d419cec1900`（2026-10-11 10:50:57 美東，只含名冊一檔）。
  - R10 policy-only 的輸出原文【引用：Jeff 貼上的終端輸出】：「[R10/policy-only] policy-only commit（policy_source=index）：staged 候選 policy 對現場成立（DECLARED_OK；runtime 仍 UNPROVEN）。這是候選驗證，不是 HEAD 已生效的 policy。」
  - 接受的是新的內容指紋，沒有審閱內容；寫入者與觸發條件 UNKNOWN。
- **重送**：票 149 的 commit `96db9efc56f63ffee23a47bb88edeb10a8aecf5b`。commit 成功；R10 當次執行情況 UNKNOWN；runtime 未驗證。報告：`.dev/reports/2026-10-11T145413Z-ticket149-s6-0b-commit.md`。
- **計數**：R10 攔截 8 次、核准 8 次。

### 裁定紀錄（逐字）

1. D8（Jeff 原文，2026-10-11 10:28 美東；`.dev/reports/2026-10-11T143246Z-ticket149-d8-diagnosis.md` :5）：「裁A：授權唯讀診斷第八次攔截：兩個 synced 根目錄中，列出目前與 HEAD 名冊（version 2）不符的檔案路徑、hash、大小與修改時間，並註明屬於契約項或逐檔 hash 項。若為 plugins 契約檔，允許檢查契約內兩檔的格式；其他檔只算 hash，不解析或展示內容。不準備草稿、不改名冊、不 commit、不 push。」
2. V8 準備（Jeff 原文，2026-10-11 10:36 美東；`.dev/reports/2026-10-11T144126Z-ticket149-v8-prep.md` :5）：「裁A：授權準備第八次核准：唯讀核對 skills/<bucket>/.last-complete-round（只算 hash、大小、觀測到的最後修改時間，不解析、不審閱內容），準備 version 2 名冊草稿，只更新該筆 sha256 與 note。草稿 note 先寫「待 Jeff 核准」，並計算草稿 hash／blob。草稿須核對：version 2 不變、230 筆路徑順序與 HEAD 完全相同、其餘 229 筆內容完全不變、兩個契約項與 pins 不變。準備好後停止，交我確認；我決定實際核准後，才將 note 改為「Jeff 核准 YYYY-MM-DD 第八次」（使用實際核准日），重新計算並核對最終 hash／blob。add 前再次唯讀核對現場指紋，不符即停止；正式 add 與核准 commit 由我親自執行，被擋不重試。不 push。skills 該檔納入契約列為新票候選，立票與排程另裁；R10 目錄 reparse 檢查列為候選。」
3. 第八次核准（Jeff 原文，2026-10-11 10:45 美東；`.dev/reports/2026-10-11T144750Z-ticket149-v8-final.md` :5）：「裁：核准第八次，核准日 2026-10-11，接受 skills/<bucket>/.last-complete-round 的新內容指紋，未審閱內容。VS 將該筆 note 改為「Jeff 核准 2026-10-11 第八次」，核對最終 sha256／blob，並再次唯讀核對現場指紋；任一不符即停。我親自 add 與核准 commit，被擋不重試。核准 commit 成功後，授權 VS 以同內容、同訊息重送 S6-149-0 票 149 的 commit，被擋依原規定退回暫存並停止，不重試。不 push。」
4. C0 本輪（Jeff 原文，2026-10-11 11:03 美東；取自 C0-149 指令）：「裁A：進入收尾準備，合併三項：(1) 唯讀核對六站正式定義（.agents/pipeline-stages.yaml、CLAUDE.md、docs/decisions.md 等原文），引用檔名與行號，核對票 149 是否需要、是否已完成第六站要求；只回報證據與差異，不定案。(2) 只修改並提交票 149，補記第八次攔截、D8、V8 與第八次核准（b9b4453）的證據與限制；推送相關新節暫稱「收尾」，不得以改名取代第六站要求。(3) 唯讀查核 Claude Code 前哨對 git push 指令的判定，只讀碼、不執行。不改 hook、不改名冊、不跑測試、不 push；提交只限票 149，被擋依原規定退回暫存並停止，不重試。推送、驗收證據與第六站後續安排另裁。」

### 候選事項（未立票）

- 把 skills 的 `.last-complete-round` 納入契約：新票候選，立票與排程另裁。
- R10 目錄的 reparse 檢查：redlight 的 `_walk_regular` 對目錄只看 `S_ISDIR`。

## 收尾（暫稱）

- 本節是推送相關事項的暫稱，不取代第六站要求；第六站是否適用、後續如何安排，另裁。
- 第六站定義核對與前哨對 git push 的判定：結果見本輪報告（C0-149），待 Jeff 裁決。
- 推送前另裁：是否接受含失敗的驗收證據；是否以 CI 完成驗證；push 需另行授權。
- 不 push。

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

## 收尾（推送、CI、收票）

本節接續〈收尾（暫稱）〉。推送、CI、收票一律稱「收尾」。本節只記錄證據與限制；第九次核准已提交（6392ce4）；Jeff 已確認本節並宣告 149 生效（見〈生效範圍〉與〈裁定紀錄〉第 4 點）。

### 推送【引用】

- 授權來源：Jeff 親自送出收尾 P1 指令（含 push）。授權內容由裁決助手整理，非逐字原話：
  - C：現有隔離全套結果只當部分證據；推送本機領先的 14 個 commit（HEAD 96db9ef）；由對應 96db9ef 的必要 CI 檢查完成驗證，必要檢查沒通過就不收票。
  - D：本次不排 arch。
  - B：skills 契約另開新票（P1 當輪不建票）。
  - A：P1 當輪不做第九次核准（後由 V9 另行授權，見下）。
  - C0 補記：留在工作樹。
- 推送前唯讀核對 20 項全部相符，摘要：
  - HEAD 96db9ef、分支 master、工作樹只有票 149 一行、暫存區空；
  - 遠端 4d22101 是 HEAD 的祖先，領先 14、落後 0 ⇒ 可以快轉；
  - push URL 只有一個，ls-remote 與本機追蹤參照一致；
  - 有效 hook 目錄 `.githooks`（local 設定），裡面只有 `pre-commit`，沒有 pre-push；
  - workflow 只有 `tests.yml`，讀碼符合這次推送的觸發條件（`push: branches: [master]`，沒有 paths 條件）；
  - 三本帳本等於基準。
- 結果【引用】：`git push origin master` 只執行一次，輸出 `4d22101..96db9ef  master -> master`（fast-forward；沒有 force；沒有被 hook 或前哨擋下）。推送後 ls-remote 為 `96db9efc56f63ffee23a47bb88edeb10a8aecf5b`。
- 報告：`.dev/reports/2026-10-12T001307Z-ticket149-closeout-p1-push.md`。

### CI【引用】

- Jeff 2026-10-11 20:20 美東確認：對應 96db9ef 的 CI 為綠燈（授權內容由裁決助手整理，非逐字原話）。
- run 明細（run id、workflow／event、各 job）：未取得，UNKNOWN。本機環境沒有 `gh`（P1 報告 步驟 3）。
- 必要檢查設定（branch protection）：未取得，UNKNOWN。
- Linux 上各 job 的細節（含 symlink 分支、R10）：UNKNOWN。

### 驗收證據的定位

- TI-149-2 含 3 項失敗的結果，只作為部分證據；以 CI 完成驗證（依 Jeff 核准的 C 選項；授權內容由裁決助手整理，非逐字原話）。
- 3 項失敗的說明維持本票〈測試隔離盤點與隔離全套（TI-149-0～3）〉一節的記錄（TI-149-3）：pdb 兩項讀碼支持由 `-p no:cacheprovider` 解釋、尚未執行驗證；第三項由「clone 沒跑 bootstrap」解釋【推論】。

### 第九次攔截與第九次核准

- **第九次攔截**【引用】：C0 的票 149 commit 被 R10 擋下，原文「`[R10/fail-closed] unmanaged_entry：未受管入口：synced（額外 0 / 缺少 0 / 內容不符 1）`」。已退回暫存，沒有重試。報告：`.dev/reports/2026-10-11T190733Z-ticket149-c0-closeout-prep.md` :27。
- **D9、D10（診斷當下的狀態）**【引用】：兩次都觀測到 `skills/<bucket>/.last-complete-round` 的 hash 與名冊不符（逐檔 hash 項）；其餘 227 筆相符，plugins 兩個契約檔的 sha256 與 D7／D8 相同。

  | 輪次 | 名冊 sha256 | 現場 sha256 | size | 觀測到的最後修改時間 |
  |---|---|---|---|---|
  | D9 | `695ec9ec…0f07`（第八次核准值） | `34294c23…ce18` | 50 bytes | 2026-10-11T19:15:12Z |
  | D10 | `695ec9ec…0f07` | `34294c23…ce18` | 50 bytes | 2026-10-12T00:17:26Z |

  - D9 的觀測時間晚於 commit 被擋的時間 ⇒ 被擋當時是否就是這一筆、當時的狀態：UNKNOWN。
  - 擋下訊息沒有原因代碼，只能當作線索。不推論寫入者、原因或變動頻率。
  - 報告：`.dev/reports/2026-10-11T192112Z-ticket149-d9-diagnosis.md`、`.dev/reports/2026-10-12T002718Z-ticket149-d10-r10-recheck.md`。
- **只改名冊，無法把 skills 這個檔納入現有契約**【引用：D9 §2，HEAD 96db9ef 的 redlight.py 讀碼】：
  - 契約名稱與路徑寫死綁定：`EXT_CONTRACT_PATHS` :1062-1063 只對應 plugins 兩條路徑；`_inventory_check` :1418-1419 遇到路徑不符回 `inventory_schema/contract.path`。
  - `synced-last-round-v1` 的讀檔上限是 37 bytes（`_EXT_CONTRACT_CAPS` :1064；`_check_last_round` :1619-1620 要求長度 37），skills 這個檔是 50 bytes；硬套的推論結果是 `contract_read/size_cap`【推論：重現】。
  - 要讓 skills 這個檔走契約，需要改程式 ⇒ 另開票 151。
- **V9（唯讀核對，沒有審閱內容）**【引用】：
  - 逐層路徑檢查通過；sha256 `34294c2321581040b5ff624be5f4d0f41ce2c4d2c2a9638584b4ad3839d5ce18`、50 bytes；觀測到的最後修改時間 2026-10-12T00:38:41Z。
  - 名冊只改這一筆的 sha256 與 note（「Jeff 核准 2026-10-11 第九次」）；version 2、其餘 229 筆、兩個契約項與 pins 都不變。
  - 最終名冊 sha256 `707822a09132d8b4591b0a460a68715d09da642e30ed119520ee2715c7f81b4c`、blob `ba6859dec904f2448113ceb308485839e99e5a90`。
  - add 前的現場複核（2026-10-12T00:43:57Z）仍相符；這只代表複核當時的狀態，不代表 Jeff 實際 add 時的狀態。
  - 報告：`.dev/reports/2026-10-12T004549Z-ticket149-v9-prep.md`。
- **第九次核准**：
  - 授權：Jeff 2026-10-11 20:32 美東簡答「核准第九次，起草。」授權內容由裁決助手整理，非逐字原話：接受上述新內容指紋，未審閱內容；核准日 2026-10-11；VS 只改名冊該筆的 sha256 與 note；Jeff 親手 add 與 commit，被擋不重試。
  - 核准結果：已提交 `6392ce4a0b2d347783b0aa069d1461c7f2e7780e`（Jeff 親手 add 與 commit，2026-10-11 20:56 美東；只含名冊一檔，名冊 blob `ba6859dec904f2448113ceb308485839e99e5a90`）。
  - R10 policy-only 的輸出原文【引用：Jeff 貼上的終端輸出】：「[R10/policy-only] policy-only commit（policy_source=index）：staged 候選 policy 對現場成立（DECLARED_OK；runtime 仍 UNPROVEN）。這是候選驗證，不是 HEAD 已生效的 policy。」
  - runtime 未驗證。
  - 接受的是新的內容指紋，沒有審閱內容；寫入者與觸發條件 UNKNOWN。
  - 提交後核對報告：`.dev/reports/2026-10-12T005925Z-ticket149-v9b-finalize.md`。
- **計數**：R10 攔截 9 次；核准已提交 9 次。

### arch

- 本次不排 arch（D；授權內容由裁決助手整理，非逐字原話）。
- arch 的觸發條件在搜尋範圍內沒有明文，只有「累積性、非每票」（CLAUDE.md :21）與「只能手動呼叫」（SKILL.md :4）（D9 §4）⇒ 列為後續，本票不定案。

### 後續（只寫指向，不展開、不排順序）

- 票 151：把 `skills/<bucket>/.last-complete-round` 納入契約（新票，candidate）。
- 候選事項（未立票）：
  - R10 目錄的 reparse 檢查：redlight `_walk_regular` 對目錄只看 `S_ISDIR`。
  - `docs/decisions.md` 缺檔：`.agents/pipeline-stages.yaml` :10 把它列為消費端，但檔案不存在。
  - TI-149-2 結尾的家目錄檢查不符合隔離條件（甲類候選）。
  - 用語統一：推送、CI、收票一律稱「收尾」。

### 生效範圍

- 生效限於 plugins 兩檔（`plugins/<bucket>/.marketplaces.json`、`plugins/<bucket>/.last-complete-round`）的契約規則（契約 v3，名冊 version 2）。
- 不代表 runtime 已驗證。
- `skills/<bucket>/.last-complete-round` 仍採逐檔 hash 比對；要不要納入契約，見票 151。

### 裁定紀錄

1. 收尾 P1：Jeff 親自送出含 push 的指令；授權內容由裁決助手整理，非逐字原話（見本節〈推送〉）。
2. CI：Jeff 2026-10-11 20:20 美東確認 96db9ef 的 CI 為綠燈；授權內容由裁決助手整理，非逐字原話。同一份紀錄：收尾方向為票 149（含 C0 補記與收票）與票 151 兩個檔合併成一個 commit，正式提交另待 Jeff 確認。
3. 第九次核准與起草（Jeff 原文，2026-10-11 20:32 美東）：「核准第九次，起草。」
4. 收尾定稿、狀態列與宣告生效（Jeff 原文，2026-10-11 21:09 美東）：「版本二，宣告 149 生效，同意合併提交；不 push。」
