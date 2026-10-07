# 票 149 —— synced 外掛 metadata 兩檔於 2026-10-07 兩次與已核准 hash 不符(R10 攔截紀錄)

**狀態**:**立案(未排程)。**
**優先度**:**未定。**(排程由 Jeff 另裁。)
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

## 待查問題(全部 UNKNOWN,本票不作答)

1. 寫入者。
2. 用途與消費方式。R1c 報告 Q2(b) 的結論是:`.marketplaces.json` 的消費方式 UNKNOWN,不能判定「沒有載入效果」(:120、:126)。
3. 變動原因。
4. 變動頻率,以及是否每輪同步都會改。
5. 兩次觀測之間,是否還有未觀測到的改寫。
6. `rows[0].updated_at` 欄位與觀測到的 mtime 之間的關係。

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
