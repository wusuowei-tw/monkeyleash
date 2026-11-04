# 票 167 —— 豁免帳本 malformed record —— 讀取端 fail-closed、寫入端拒非物件、第 426 行隔離

**狀態**：~~**立案（2026-11-03）。本票只立案與記錄唯讀偵察結果；程式修改、帳本隔離皆未開始（屬輪二）。**~~ **實作完成，待驗收（2026-11-03，輪二）。** 證據見〈四｜AC〉各條；根因仍未證明（AC-5）。
**優先度**：LifeApp 接線的前提（裁決者 2026-11-03，見〈關聯〉）。
**立案**：2026-11-03。票號 167 於立案當下重查 `docs/tickets/framework-updates/` 取得（當時最大號 166；寫檔前確認無 167 開頭的檔案）。
**性質**：缺陷票。讀取端、寫入端、既有壞行三件事同一張票（裁決 Q3）。
**交叉引用**：LifeApp 規格目錄下的報告 `20261103T184416Z-lifeapp-gates-coverage-recon.md`（非本 repo）；票 168（test-runs.jsonl provenance，同輪立案）。

---

## 一｜背景

### 1.1 事實（來源：LifeApp 報告 `20261103T184416Z-lifeapp-gates-coverage-recon.md`）

以下行號為該報告查證時 HEAD `4bc2025ed7f150111c56b126b565693c9ee354e4` 的 `.claude/hooks/gate.py`。

1. `.dev/gate-exemptions.jsonl` 現有 430 行，第 426 行逐字為 `null`（長度 4），夾在兩筆相隔 3 秒的 `rule-pruning`／`Edit` 記錄之間；該行屬未提交的 112 行新增之內。
2. 讀取端 `logged_exemption_backed`（`:2461`）在 `:2488` 開檔逐行讀，try／except 只包 `:2492-2495` 的 `json.loads`；`json.loads("null")` 回傳 `None` 不拋例外 ⇒ `:2496` 的 `rec.get` 拋 `AttributeError`，不在 try 內；呼叫點 `:3987` 與 `check()` 的兩個呼叫點（`:4739`、`:5269`）皆無 try 包覆。
3. 寫入端 `_append_jsonl`（`:3625-3629`）寫 `json.dumps(rec)`；`rec` 為 `None` 時正好產生 `null`。`rec` 如何變成 `None`：未證明。
4. `.dev/test-runs.jsonl` 欄位含 `impl_file`／`impl_hash`（綁實作內容雜湊），無 commit SHA 欄位、無任何綁測試檔版本的欄位（另開票 168，不在本票）。

### 1.2 本 repo 唯讀偵察補充（2026-11-03，HEAD 同上；只讀原始碼與帳本，未執行任何程式）

- **第 426 行**：逐字為 `null`、長度 4（不含行尾）。全檔 430 行，行尾為 CRLF（與 `_append_jsonl` 在 Windows 以 `io.open(path, "a")` 文字模式寫入相容）。現行 `logged_exemption_backed` 對該行會走到非 dict 取值（`:2496`）。本票不引用該行的雜湊；雜湊於輪二隔離時對 quarantine 原文計算。
- **寫入端（偵察第 2 題 (2)）**：寫 `EXEMPTION_LOG` 的唯一路徑是 `log_exemptions`（`:3604-3622`）→ `exemption_record`（`:3563-3601`）。後者在 `:3582` 組 dict 字面值，`:3601` 無條件 `return rec`。**現行原始碼未找到 `rec` 為 `None` 的路徑。**
  檢索方式：全 repo（不含 `.dev/`）Grep `gate-exemptions|EXEMPTION_LOG|log_exemptions\(|exemption_record\(`，逐一讀命中處。repo 內另一寫入者 `scripts/e2e_authority_layer.py:867-869` 寫的是 e2e clone 內的帳本，且寫 dict 字面值。
- **第 425／427 行（偵察第 2 題 (3)）**：兩筆皆 `ticket=rule-pruning`、`tool=Edit`、`at_commit=false`、無 `advisory` 鍵，對應 `mode_hook` 的 `:4757` 呼叫點（`:4745` 會帶 `advisory` 鍵，排除）。第 425 行 `result_hash` 為 `0594af02…`，第 427 行 `content_hash` 為 `5a48ac5a…`，**兩者不連續**，與「第 426 行為中間那次 Edit 的紀錄」相容。可能情境：`gate.py` 自我修改期間，磁碟上的版本裡函式暫時無 `return`。**⚠ 假設，未證明；中間版本不可重建。**
- **其他讀取端（偵察第 2 題 (4)；AC-3 的對象清單）**：
  - `.claude/portable/status.py` `_read_jsonl`（`:187-210`）：解析失敗或非 dict 的行**靜默跳過**（`:204-207`）。讀豁免帳本的呼叫點 `:733-734`、`:967-968`。
  - `.claude/portable/ledger_verify.py` `parse_records`（`:112-127`）：解析失敗丟 `ValueError`；但 `null` 解析得了，以 `None` 進串列，之後 `chain_breaks` 在 `:165` 的 `a.get` 取值（`report()` 的 `:270-274` 同型）。**⚠ 靜態推論，未執行。**
  - 其餘不解析 JSON：`scripts/e2e_authority_layer.py`（行數與字串比對，`:462`、`:885-887`、`:1085`）；`.claude/portable/install.py:206`（只寫空檔）；`.claude/patches/apply_patches.py:81`（code-review skill 散文，由 agent 讀帳本，非程式讀取）。
- **前哨與程序出口（偵察第 2 題 (6)）**：`logged_exemption_backed` 只在 `:3987`、且只在 `at_commit` 為真時被呼叫；`at_commit=True` 只出現在 `mode_pre_commit` 的 `:5269`；`mode_hook` 的 `:4739` 用預設 `at_commit=False` ⇒ **前哨 `mode_hook` 不讀此帳本**。`__main__`（`:5355-5360`）未包 try，未捕捉例外依靜態推論以退出碼 1 結束。**⚠ 靜態推論，未執行。**
- **既有測試（偵察第 2 題 (5)）**：見〈四｜AC〉AC-8 列表。

---

## 二｜裁決（裁決者 2026-11-03）

- **Q1**＝(a) 讀取端 fail-closed：任一行解析失敗或解析結果非物件 ⇒ 硬錯誤，不受降級組影響。
- **Q2**＝(b) 現有第 426 行隔離：搬到 `.dev/gate-exemptions.quarantine.jsonl`，主帳本刪該行。
- **Q3**＝寫入端根因與防呆納入本票。
- **Q4**＝test-runs.jsonl provenance 另開獨立票（票 168），不作為 LifeApp 接線 blocker。

---

## 三｜政策定義

- **malformed record**＝該行 `json.loads` 拋例外，或回傳值不是 dict。
  - **空行**：**裁決 ②（裁決者 2026-11-03）：不算 malformed，維持跳過**（strip 後為空即跳過；三個讀取端皆同）。
- **fail-closed**＝回硬錯誤訊息，走既有硬擋出口，**不經** `_check_is_advisory`。訊息必含：
  - 帳本相對路徑、行號、錯誤類型（解析失敗／非物件）、原始行長度、該行內容的 SHA-256、修復指引（指向隔離程序）。
  - **⚠ 訊息不得回顯該行任何原文**：壞行本身可能含路徑、帳號等受保護內容，回顯會再次觸發守衛（與已登記的「守衛訊息含受保護內容」同族）。若未來要 sanitized preview，另裁，不在本票。

---

## 四｜AC

測試檔：`tests/test_exemption_ledger_malformed.py`（以下簡稱 T）。測試名前綴 `test_red_` ＝紅燈類、`test_baseline_` ＝既有行為回歸類（AC-7）。

- ☑ **AC-1**：讀取端 `logged_exemption_backed` 遇 malformed record ⇒ 硬錯誤，不 `continue`、不靜默。
  證據：T `TestAC1LoggedExemptionBacked::test_red_malformed_line_is_a_hard_error`（null／壞 JSON／數字／字串四格，`SystemExit(2)`）；對照 `test_baseline_blank_lines_and_valid_records_are_read_normally`。實作：`gate.py` `logged_exemption_backed` → `_ledger_malformed`（`_err` ＋ `SystemExit(2)`，不經 `_check_is_advisory`）。
- ☑ **AC-2**：所有現行會讀 `EXEMPTION_LOG` 的 enforcement path，遇 malformed record 都必須硬擋，且各有測試。pre-commit 路徑（`:3987` 的 `at_commit` 分支）必須有覆蓋。
  ⚠ 偵察結果：前哨 `mode_hook` 現行不讀此帳本 ⇒ **不得為了滿足本 AC 而新增讀取**；是否讓 `mode_hook` 主動驗帳本，另裁、不在本票。
  證據：T `TestAC2CommitPath::test_red_commit_path_blocks_with_a_complete_message`（四格；`check(…, at_commit=True)` 經 `:3987` 那一格；斷言退出碼 2、非降級提示、訊息含帳本相對路徑／行號／錯誤類型／原始行長度／SHA-256／修復指引、不含該行原文、無 `Traceback`）；對照 `test_baseline_valid_ledger_reaches_the_ordinary_r3_verdict`、`test_baseline_write_time_path_does_not_read_the_ledger`（前哨不讀，未新增讀取）。
- ☑ **AC-3**：一.1.2 列出的其他讀取端（`status.py` `_read_jsonl`、`ledger_verify.py` `parse_records`／`chain_breaks`／`report`），對 malformed record 的行為有明確定義（擋或明確出聲），不得靜默跳過；各有測試。
  定義（裁決 ③）：`status.py` 出聲不擋 —— `_read_jsonl` 回傳仍為 list of dict，另帶 `malformed`（行號＋錯誤類型），`exemptions` 那一行附「壞行 N 筆（第 X 行 類型）」；`ledger_verify.py` 維持 fail —— 非物件也丟 `ValueError`（只給行號與型別）。
  證據：T `TestAC3Status::test_red_read_jsonl_lists_the_malformed_line`（四格）、`test_red_render_names_the_malformed_line`、`test_baseline_read_jsonl_still_returns_the_valid_records`；T `TestAC3LedgerVerify::test_red_non_object_line_raises_value_error`（null／數字／字串）、`test_baseline_unparseable_line_raises_value_error`、`test_baseline_blank_lines_are_skipped`。
- ☑ **AC-4**：寫入端 `_append_jsonl` 拒絕非 dict 的 `rec`：不寫入、stderr 出聲、回傳或拋出可被呼叫端察覺的錯誤；有測試。
  證據：T `TestAC4AppendJsonl::test_red_non_dict_is_refused`（None／int／str／list：`TypeError`、檔案不變、stderr 非空）、`test_red_log_exemptions_turns_a_refused_record_into_a_hard_stop`（`exemption_record` 回 None ⇒ `log_exemptions` 照舊 `SystemExit(2)`、帳本不變）、`test_baseline_dict_is_appended`。
- ☑ **AC-5**：根因：`rec` 為 `None` 的來源查明並修正；查不明則票面明寫「未證明」且 AC-4 已擋住再發生。
  **根因未證明；AC-4 已擋住再發生**（同一情境由 `test_red_log_exemptions_turns_a_refused_record_into_a_hard_stop` 覆蓋）。一.1.2 的「自我修改期間函式暫時無 return」仍是假設。
- ☑ **AC-6**：隔離程序：新檔 `.dev/gate-exemptions.quarantine.jsonl`，每筆為 dict，含 `source_file`、`original_line_no`、`original_text`、`moved_at`（UTC ISO）、`reason`、`ticket`；主帳本刪該行前先備份；備份檔名、刪除前後的 numstat、該行前後各一行的原文，全部寫進票面與 commit 說明。
  執行紀錄（2026-11-03／04，UTC；承重欄位，不貼整行原文）：
  - 備份：`.dev/gate-exemptions.jsonl.pre-167-20261103T201240Z.bak`，SHA-256 `fa34e09e75cbfc8fffd594998fdc640ab0d7bede366d846d2ea19b290057b6f1`（與備份當下主帳本相同）。備份檔在 `.dev/` 的 ignore 規則下，不進版控。
  - quarantine：`.dev/gate-exemptions.quarantine.jsonl`（以 `git add -f` 納入版控，只此一路徑），1 筆；`original_line_no` 426、`original_text` `"null"`、`original_sha256` `74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b`、`hash_def` `sha256(utf-8 bytes of line content, CR/LF excluded)`、`moved_at` `2026-11-04T00:00:15Z`、`ticket` `167`；另記 `prev_line_result_hash`／`next_line_content_hash`。
  - numstat（相對 HEAD `4bc2025`）：刪除前 `114 0`（推得：備份 432 行 − HEAD 318 行，皆為追加）；刪除後 `113 0`（實量）。備份檔對刪除後主帳本：`0 1`。
  - 各行（canonical SHA-256 定義同 `hash_def`）：

    | 時點 | 行號 | 型態 | ticket | tool | at_commit | content_hash | result_hash | canonical SHA-256 |
    |---|---|---|---|---|---|---|---|---|
    | 隔離前 | 425 | dict | rule-pruning | Edit | false | `49a503901339191dc8517583feb938c526a584c60a342758cfd582cba8005064` | `0594af02b10a2c0fd09cca273173b656fb3a6f7335a569725a6ade0fd063276c` | `95650e0fc30371ce9023b898f8db9da1218b4777ebe7d6277caf313e24b848b1` |
    | 隔離前 | 426 | `record_type="non-object/null"`，`original_text="null"` | — | — | — | — | — | `74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b` |
    | 隔離前 | 427 | dict | rule-pruning | Edit | false | `5a48ac5a9d7e403ed5228f8f85b8a10c1a10b9260b6a9600c0fd2c7f983e6965` | `6e8a5a763b63ac6c46f11b5f83647c372e0fbeb82fa22635fa04e9b9624ba5f4` | `c96461a844edad8c9984305a088cf5bef6b7b995fadd7d368bfb89af5ebc26eb` |
    | 隔離後 | 425 | dict | rule-pruning | Edit | false | `49a503901339191dc8517583feb938c526a584c60a342758cfd582cba8005064` | `0594af02b10a2c0fd09cca273173b656fb3a6f7335a569725a6ade0fd063276c` | `95650e0fc30371ce9023b898f8db9da1218b4777ebe7d6277caf313e24b848b1` |
    | 隔離後 | 426 | dict | rule-pruning | Edit | false | `5a48ac5a9d7e403ed5228f8f85b8a10c1a10b9260b6a9600c0fd2c7f983e6965` | `6e8a5a763b63ac6c46f11b5f83647c372e0fbeb82fa22635fa04e9b9624ba5f4` | `c96461a844edad8c9984305a088cf5bef6b7b995fadd7d368bfb89af5ebc26eb` |

    第 426 行為非物件，**不填也不推導** ticket／tool／at_commit／content_hash／result_hash。
- ☑ **AC-7**：紅燈先行：AC-1～AC-4 各先有失敗測試，含正控（故意塞 `null` 行、壞 JSON 行、數字行、字串行）。
  證據：實作前首跑 T：紅燈類 21 條全部失敗、回歸類 7 條全綠（`21 failed, 7 passed`）；實作後 `28 passed`。
- ☑ **AC-8**：回歸：下列既有測試仍綠（偵察第 2 題 (5)；命中行 → 函式 → def 行號）。
  證據：T 28 綠；下列具名測試 9 綠（`_premises` 為 helper，由 `TestBarePackageMarkerJudgesTheStagedContent` 的測試帶入）。全套一次：`1 failed, 3499 passed, 39 skipped, 3 xfailed`，唯一 failure 為新測試檔未登記 manifest；補登記後 `tests/test_manifest.py` 與 T 重跑 `44 passed`，未再跑全套。各次 pytest 皆加 `-p no:randomly`（原指令未要求）。
  測試登記：`tests/test_exemption_ledger_malformed.py` 在 `.agents/portable-manifest.txt` 登記為 `copy`（裁決者 2026-11-03：下游帶 gate.py 就要帶對應保護測試）。
  - `tests/test_gate.py:2296` → `test_the_commit_time_check_does_not_accept_an_uncommitted_ticket`（def `:2280`）
  - `tests/test_gate.py:2308` → `test_the_commit_time_check_accepts_a_committed_ticket`（def `:2300`）
  - `tests/test_gate.py:2327` → `test_the_same_ledger_flips_when_the_ticket_reaches_head`（def `:2312`）
  - `tests/test_gate.py:2743` → `_premises`（helper，def `:2736`；由呼叫它的測試帶入）
  - `tests/test_gate.py:2913` → `test_an_unreadable_index_still_lets_a_later_exemption_run`（def `:2866`）
  - `tests/test_gate.py:3031` → `test_a_record_only_under_root_does_not_grant`（def `:3020`）
  - `tests/test_gate.py:3045` → `test_a_record_only_in_the_isolated_ledger_grants`（def `:3035`）
  - `tests/test_gate_boundaries.py:72` → `test_a_failed_exemption_record_blocks_the_exemption`（def `:65`）
  - `tests/test_intercepts.py:258` → `test_negative_control_an_unwritable_ledger_still_blocks`（def `:247`）
  - `tests/test_intercepts.py:270` → `test_negative_control_a_broken_ledger_does_not_swallow_the_verdict`（def `:264`）
  - `tests/test_declared_in_is_an_identity.py:250-257`：**模組層註解**（`:248` 起），不屬於任何函式；往前最近的 def 為 `test_ticket_untested_modules_still_returns_a_relative_path`（`:234`），但命中不在其內。該註解引用的是上列 `test_the_commit_time_check_accepts_a_committed_ticket`。

---

## 五｜不在本票範圍

- `test-runs.jsonl` provenance（見票 168）。
- R3 降級組本身。

## 六｜關聯

- LifeApp 接線以本票驗收為前提（裁決者主線第 1～3 步）。
- 票 168：同輪立案，互不阻擋。
