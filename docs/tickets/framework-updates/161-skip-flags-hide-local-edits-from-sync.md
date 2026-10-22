# 票 161 —— assume-unchanged／skip-worktree 讓 sync 看不見計畫內的本地改動

**狀態**：**已結案。** 161-c 獨立審查 PASS（附註）；已 push `7f50e59`，CI 綠（Jeff 2026-10-22 約 14:57（美東）確認）。

## 發現

票 125-c 審查提出〔未驗證〕：帶 assume-unchanged／skip-worktree 旗標的檔，`git diff` 可能看不到本地改動，因此被 sync 覆寫。

R0（2026-10-22）在暫存 repo 實測確認：**新版（`2c86aff`）與舊版（`81bb907`）同有，非票 125 退化。**
舊版判髒靠整樹 `git status`，新版靠計畫內路徑的 `git diff` 與 `git diff --cached`；
兩者都讀 git 的 index 判定，而這兩種旗標正是叫 git 不去看 worktree。

R0 情境結果（copy 桶的檔：上游改過並提交；下游已提交後做本地改動，再設旗標）：

| # | 情境 | `ls-files -v` 首字 | 新版 | 舊版 |
|---|---|---|---|---|
| 1 | `baseline_no_flag` | `H` | 擋，未覆寫 | 擋，未覆寫 |
| 2 | `assume_unchanged` | `h` | **不擋，被覆寫成上游內容** | **不擋，被覆寫成上游內容** |
| 3 | `skip_worktree` | `S` | **不擋，被覆寫成上游內容** | **不擋，被覆寫成上游內容** |
| 4 | `assume_unchanged_staged`（先 stage 再設旗標） | `h` | 擋（`diff --cached` 抓到） | 未實測 |
| 5 | `skip_worktree_deleted`（設旗標後刪檔） | `S` | 擋（追蹤中而磁碟上不在） | 未實測 |
| 6 | `provenance_skip_worktree` | `S` | 不擋，追加；原內容完整保留為前綴 | 未實測 |
| 7 | `canon_assume_unchanged`（`regenerate_canon`） | `h` | **未實測**（R0 腳本前提寫錯） | 未實測 |

## 裁決

**裁決者**：Jeff，2026-10-22 約 13:25（美東）。由裁決助手記錄，非逐字原話。

1. 修法 **A**：`freeze_plan` 查計畫內路徑的 `git ls-files -v`，帶這類旗標就擋。
   「逐字比對」（修法 B）另開票評估，不在本票。
2. `.dev/provenance.jsonl` 帶旗標 **不擋**（比照它「只免未提交內容」的豁免；實測只追加、不蓋掉舊內容）。

裁決助手依既有授權定的細則：

- 旗標判準：`git ls-files -v` 首字為**小寫字母**（assume-unchanged，含同時設兩種旗標）或 **`S`**（skip-worktree）⇒ 視為帶旗標。紅燈測試把 `h`、`S`、兩者同設三種首字都釘住。
- 帶旗標的計畫內路徑，**即使內容其實沒改也擋**（git 已無法告訴我們它乾不乾淨；fail-closed）。
  **這是刻意收緊，有代價：內容乾淨但帶旗標的檔也會被拒絕。** 本票接受這個代價；這條規則**會誤擋**乾淨的檔，不是「不會誤判」。
  出口是下游自己解除旗標（`git update-index --no-assume-unchanged` / `--no-skip-worktree`）後再跑。

審查者 2026-10-22 約 13:27（美東）經 Jeff 轉達：

- #8 沿用既有髒檔拒絕判準；#5 的現行結果照實記錄，不湊紅；票面寫明收緊的代價（見上）。
- 計畫外的檔帶旗標 **不擋**（與票 125 裁決 C「計畫外的髒不擋」一致）。
- 拒絕訊息必須點名路徑與旗標（含 `assume-unchanged` 或 `skip-worktree` 字樣），也必須含「乾淨」或「髒」。

## 不在本票

- **修法 B**（經 git 屬性轉換的位元組比對，可涵蓋 fsmonitor／racy-clean／ignoreStat）—— 候選新票。
  R0 已列出 CRLF／clean filter 誤判風險，以及 B1（`io.open` 讀出的位元組經 stdin 交給 `git hash-object --stdin --path`）與 B2（`git cat-file --batch` 讀 blob、兩邊換行正規化後比）兩種做法。
- dry-run 不跑 `freeze_plan`（票 125 待辦第 2 條）。
- 其他會讓 git 看不見 worktree 改動的機制（`core.fsmonitor`、racy-clean、`core.ignoreStat`、sparse-checkout 自動設的 skip-worktree 等）〔未驗證〕。

## 紅燈測試（`tests/test_sync.py::TestT161FlaggedPlanPathsBlock`）

| # | 名稱 | 形狀 | 現行預期 | 實作後預期 |
|---|---|---|---|---|
| 1 | `test_t161_01_assume_unchanged_with_local_edit_blocks` | copy 桶檔本地改動、設 assume-unchanged（`h`） | 紅（不擋、被覆寫） | 擋，檔不變 |
| 2 | `test_t161_02_skip_worktree_with_local_edit_blocks` | 同上，設 skip-worktree（`S`） | 紅 | 擋，檔不變 |
| 3 | `test_t161_03_both_flags_block` | 同上，兩種旗標都設（首字應為小寫） | 紅 | 擋，檔不變 |
| 4 | `test_t161_04_flag_without_local_edit_still_blocks` | 檔沒改、設 assume-unchanged | 紅（不擋、被寫成上游內容） | 擋（fail-closed），檔不變 |
| 5 | `test_t161_05_canon_with_flag_blocks` | `CLAUDE.md` 界線外本地改動、設 assume-unchanged、上游正典段不同；`regenerate_canon` | 紅（R0 未實測，照實記錄） | 擋，檔不變 |
| 6 | `test_t161_06_flag_outside_the_plan_does_not_block` | 計畫外（`skip` 桶）的檔帶旗標＋本地改動；計畫內另有正常 copy 改動 | 綠 | 綠：apply 成功，計畫外的檔不變 |
| 7 | `test_t161_07_flagged_provenance_still_appends` | provenance 已追蹤、設 skip-worktree、本地內容；計畫內另有正常 copy 改動 | 綠 | 綠：apply 成功，原內容完整保留為開頭 |
| 8 | `test_t161_08_staged_then_flagged_still_blocks` | 先 stage 本地改動再設 assume-unchanged | 綠（`diff --cached` 已擋） | 綠，擋 |

#1～#5 的原因斷言：訊息點名路徑與旗標字樣，並含「乾淨」或「髒」。
#8 的原因斷言：沿用既有髒檔判準，訊息含路徑與「未提交」，不要求提到旗標。

161-b（錨點 161-b）後 #1～#8 全綠。

## 161-c 審查後待辦（不在本票）

1. #8 沒斷言旗標理由也附加：同時髒＋帶旗標時「兩條理由都說」沒有測試守著。
2. 測試缺口：`_flags_z` 的失敗路徑、檔名含空白／非 ASCII、超過 100 條的分批、`GIT_OPTIONAL_LOCKS` 都沒有測試；#3 沒釘死訊息說的是哪一種旗標；「不存在＋帶旗標」的訊息沒有測試。
3. 兩種旗標同設時，訊息只提示解除 assume-unchanged；解除後 skip-worktree 仍在，要再跑一次才會看到第二個提示〔讀碼推論〕。
4. sparse-checkout 下游：若計畫含範圍外的檔，會一直被擋（票 161 之前就成立）；解除旗標後 git 會不會依 sparse 規則重設〔未驗證〕。
5. 「不存在＋帶旗標」的訊息同時寫「本地刪除」與「內容沒改也擋」：在 sparse 情境前者不成立，後者語意不貼切。
6. 非 UTF-8 路徑解碼後對不上，旗標判定落空；檔案存在時由既有「未追蹤」擋下，不存在時不擋（既有行為）〔讀碼推論〕。
7. 修法 B（經 git 屬性轉換的位元組比對）仍是候選新票（見〈不在本票〉）。

## 修正紀錄

- 2026-10-22（美東）：立案；161-a 紅燈測試（錨點 161-a）。
- 2026-10-22（美東）：161-b 實作（錨點 161-b）：freeze_plan 對計畫內路徑查 ls-files -v，assume-unchanged／skip-worktree 一律擋（provenance 豁免）。
- 2026-10-22（美東）：161-c 獨立審查 PASS（附註），push 7f50e59，CI 綠；收票，審查後待辦入票（錨點 161-d）。
