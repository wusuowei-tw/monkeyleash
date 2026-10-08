# 票 148 第五站審查包(S5-148-0)

- 日期:2026-10-07
- 製作時 HEAD:`4d35073c4503f4bec8daca35082beb3d52139348`
- 站別:`.dev/pipeline.json` 的 `current_stage` 是 `review`、`ticket_id` 是 `148`(Jeff 切換)
- 本包只是索引,不是審查結論

Jeff 裁決原文(2026-10-07 19:56 美東,逐字):

> 「進第五站。先產審查包，再由全新視窗獨立審查；站別只改 `current_stage` 為 `review`，保留 ticket 148 與其他欄位。
> 審查包須分清正式 pytest 對應的 code commit、後續 docs commit，以及外部 Linux 預演。重點核對 rename 目的檔確實進入 R2／leak scan、純刪除處置不變、#5 未改的限制。
> 目前仍不 push。」

---

## §1 審查範圍

### 審查對象 commit

| commit | 內容 |
|---|---|
| `aeb4d51a26401fbe541837b4d51672ba594a60a3` | S3 紅燈測試(3 個測試檔 + 票 148 + S3 審計) |
| `9efca02d1508d828862cb4cb8afe699e4b60601a` | S4 程式(gate.py、scanner.py 的 `staged_paths` + 票 148 + 豁免帳本) |
| `4d35073c4503f4bec8daca35082beb3d52139348` | S4 文件(S4 審計、票 148、票 149、豁免帳本) |

### 背景(不屬本審查標的)

| commit | 內容 |
|---|---|
| `c91db49a620045d8d9122e6859c4732cd2c06479` | Jeff policy-only 重新核准 inventory |
| `96fc8b9c75e734bfc7af2a94c245cc96739aeb78` | 立票 149 |

`git log --oneline 6d80427b0bfd79d4c0477a8b93b2f8f65c44de09..HEAD`(製作時實測):

```
4d35073 docs(148): S4-148-2 —— 第四站審計、票面更新；票 149 信箱遮罩與流程偏離紀錄
9efca02 fix(148): S4-148-1 —— staged_paths（gate、scanner）加 --no-renames，rename 目的檔進入逐檔檢查與 leak scan
96fc8b9 docs(149): 立票 —— synced 外掛 metadata 兩次 hash 不符的觀測、核准與攔截紀錄
aeb4d51 test(148): S3-148-1 紅燈 —— rename 目的檔進入 staged 檢查（四種 diff.renames、leak scan、權威層 R2）
c91db49 policy(148): re-approve 2 synced plugin metadata entries (second time on 2026-10-07) via policy-only lane, approved by Jeff 2026-10-07
```

### 要讀的檔與行範圍

行號以 `4d35073` 為準。

**production**

- `.claude/hooks/gate.py`
  - `staged_paths` `:3996-4041`:旗標在 `:4028`,docstring 補段在 `:4023-4025`。
  - `mode_pre_commit` `:4148` 起:`staged = staged_paths(gitlinks=gitlinks)` 在 `:4162`,逐檔迴圈 `for f in staged:` 在 `:4182`,`check(f, None, at_commit=True, …)` 在 `:4184`。
  - `check()` `:2705` 起:R2 提交時點分支 `elif at_commit:` 在 `:2862`,`[R2/commit]` 訊息在 `:2889-2894`。
  - `is_source_path` `:2204-2230`;`NON_SOURCE_DIRS` `:272-287`。
- `.claude/portable/scanner.py`
  - `staged_paths` `:469` 起:docstring 補段在 `:499-501`,旗標在 `:504`。
- `.claude/portable/leak_scan.py`
  - `--staged` 路徑 `:318-344`:`scanner.staged_paths(cwd=ROOT, …)` 在 `:321`;空清單回 0 在 `:344`。
- 程式 diff:`git diff 96fc8b9 9efca02 -- .claude/hooks/gate.py .claude/portable/scanner.py`。S4 審計 §2 有原樣。

**測試(T148 全部 node)**

| 檔 | 類別 / 函式 | 行 |
|---|---|---|
| `tests/test_gate.py` | helper:`_T148_RENAMES` :7317、`_t148_env` :7320、`_t148_git` :7333、`_t148_repo` :7337、`_t148_name_status` :7347、`_t148_assert_rename` :7352、`_t148_assert_delete_add` :7360、`_t148_mv_repo` :7367、`_t148_scanner` :7383 | — |
| `tests/test_gate.py` | `TestTicket148RenameDestinationIsListed`(:7391)`::test_t148_1_gate_staged_paths_lists_rename_destination[unset/true/copies/false]` | :7395 |
| `tests/test_gate.py` | 同類 `::test_t148_3_rename_source_stays_out_of_both_listings` | :7402 |
| `tests/test_gate.py` | 同類 `::test_t148_4_pure_deletion_stays_out_of_both_listings` | :7409 |
| `tests/test_gate.py` | `TestTicket148AuthorityLayerJudgesRenamedSource`(:7426)`::test_t148_7c_new_source_file_is_blocked_by_r2` | :7474 |
| `tests/test_gate.py` | 同類 `::test_t148_7_renamed_into_source_is_blocked_by_r2` | :7485 |
| `tests/test_scanner.py` | helper:`_t148_git` :1062、`_t148_mv_repo` :1067;`test_t148_2_scanner_staged_paths_lists_rename_destination[unset/true/copies/false]` | :1102 |
| `tests/test_leak_scan.py` | helper:`_t148_secret_block` :1138、`_t148_rule` :1144、`_t148_git` :1149、`_t148_repo` :1154、`_t148_assert_hit` :1176 | — |
| `tests/test_leak_scan.py` | `TestTicket148RenamedFileIsScanned`(:1182)`::test_t148_5_secret_in_a_new_file_is_caught` | :1184 |
| `tests/test_leak_scan.py` | 同類 `::test_t148_6_secret_added_during_rename_is_caught` | :1194 |

**文件**

- 票 148 全文:`docs/tickets/framework-updates/148-staged-list-misses-renames.md`。含〈R0 盤點結果〉〈Jeff 裁決〉〈外部證據〉〈待辦〉〈第三站紅燈〉〈第四站實作〉。
- S3 審計:`docs/audits/2026-10-07-148-station3-redlight.md`。
- S4 審計:`docs/audits/2026-10-07-148-station4-implementation.md`。
- 相關報告(ignored,只在本機 `.dev/reports/`):
  - `2026-10-07T203056Z-ticket148-r0-inventory.md`
  - `2026-10-07T204645Z-ticket148-s3-redlight.md`
  - `2026-10-07T205822Z-ticket148-s3-redlight.md`
  - `2026-10-07T214331Z-ticket148-s3-commit.md`
  - `2026-10-07T234835Z-ticket148-s4-implementation.md`

## §2 證據分級(逐項標明對應的 commit 或基準,不得混用)

**(1) 工作樹證紅(S3)**

- 基準:HEAD `6d80427b0bfd79d4c0477a8b93b2f8f65c44de09` + 當時未提交的測試。
- 結果:`8 failed, 2332 passed, 10 skipped, 3 xfailed`;14 個 node 的 C0 全中(8 紅 6 綠)。
- 出處:S3 審計 §2;報告 `205822Z` §1-§3。
- 測試後來以 `aeb4d51` 提交,blob 與證紅時相同(index 記錄 cmp 相同,見報告 `214331Z` §2)。

**(2) 前檢證據(S4,工作樹)**

- 基準:HEAD `96fc8b9` + 未提交實作。
- 結果:`-k t148` 14 passed;全套 `2340 passed, 10 skipped, 3 xfailed`;淨室 `verify_gates.py` rc 0。
- 出處:S4 審計 §3、§4。

**(3) 正式結果**

- 對應 code commit `9efca02d1508d828862cb4cb8afe699e4b60601a`(**不是** `4d35073`)。
- 結果:全套 `2340 passed, 10 skipped, 3 xfailed`。
- 帳本前綴證明:`head -c` 步驟 0 長度後的 sha256 等於步驟 0 整檔 sha256。
- 出處:S4 審計 §6、§7。

**(4) docs commit `4d35073`**

- 未重跑測試。
- 製作本包時實測 `git diff --stat 9efca02 4d35073`:

  ```
   .dev/gate-exemptions.jsonl                         |   1 +
   .../2026-10-07-148-station4-implementation.md      | 216 +++++++++++++++++++++
   .../148-staged-list-misses-renames.md              |   2 +-
   .../149-synced-plugin-metadata-hash-drift.md       |   8 +-
   4 files changed, 224 insertions(+), 3 deletions(-)
  ```

- `git diff --name-only 9efca02 4d35073`:

  ```
  .dev/gate-exemptions.jsonl
  docs/audits/2026-10-07-148-station4-implementation.md
  docs/tickets/framework-updates/148-staged-list-misses-renames.md
  docs/tickets/framework-updates/149-synced-plugin-metadata-hash-drift.md
  ```

- ⇒ 相對 `9efca02` 只動文件與豁免帳本(實測 diff)。
- 因此 `9efca02` 的正式結果適用於 `4d35073` 的程式與測試內容(推論,基於 diff)。

**(5) 外部 Linux 預演**

- 性質:裁決者沙盒。不屬本 repo 的 Windows 帳本,也不取代 CI。
- 環境:Linux、git 2.43.0、Python 3.11、非 root、家目錄沒有 `~/.claude`。
- 程式來源:
  - 以 `6bc98085e4c018e896cf252b945f51bfaa8ed7fb` 樹為底。
  - 用本機工作樹覆蓋 5 個檔:`.claude/hooks/gate.py`、`.claude/portable/scanner.py`、`tests/test_gate.py`、`tests/test_scanner.py`、`tests/test_leak_scan.py`(CRLF 轉 LF)。
- 限制:
  - 本次未核對整樹 hash 與 `9efca02` 相同。
  - `6bc9808` 之後的其他差異(文件與 inventory)對預演的影響尚未核對。
- 結果:
  - `pytest -q --ignore=tests/test_known_items_regression.py` ⇒ `2338 passed, 3 xfailed, 0 skipped, 0 failed`
  - `-k t148` ⇒ `14 passed`
- 出處:裁決者於 S5-148-0 指令提供。本 repo 沒有獨立紀錄。

## §3 已知限制與未驗

- **#5 未改**:`scripts/e2e_authority_layer.py:1046` 仍為 `--diff-filter=ACM`、沒有 `--no-renames`(Jeff 裁決本輪不改;票 148〈待辦〉)。
- **R0 §3 剩餘缺口**:`-C` / copies / `--raw`、字串拼接、二進位與編碼,仍為 UNKNOWN。
- **CI**:POSIX 正式 CI 未跑(未 push)。
- **R10 攔截**:本地 R10 曾兩次因 synced metadata 擋下(見票 149)。目前沒有證據顯示與本票修改有關,原因 UNKNOWN。

## §4 審查題

請逐題作答,並標註 實測 / 讀碼推論 / UNKNOWN。

**(a) rename 目的檔是否確實進入權威層 R2**

- T148-7 / 7c 的佈置是否有效。
- R10 隔離(採 (a):tmp 使用者層 + 合法空白 policy)是否有效。
- 7c 是否確實走到 R2(斷言含 `[R2`、不含 `[R10`)。
- 撤回修正後 T148-7 是否會轉紅。可在 scratchpad 的獨立複本做突變探針,不得改 repo 工作樹。

**(b) rename 目的檔是否確實進入 leak scan**

- T148-5 / 6 是否用同一合成樣式。
- 是否斷言命中特定規則與檔名。
- T148-6 是否有 R 前提斷言。

**(c) 四種 `diff.renames` 設定**

- `GIT_CONFIG_GLOBAL` / `GIT_CONFIG_NOSYSTEM` 隔離是否真的讓「未設定」成立。
- 被測子行程是否繼承這份環境。

**(d) 純刪除與 rename 來源的處置是否維持不變(T148-3 / 4)**

- `--no-renames` 後,來源成為 `D`、被 ACM 排除,是否與純刪除一致。
- 是否因此產生新的未覆蓋情形,例如原始碼檔被改名移出原始碼目錄。只描述,不擴範圍。

**(e) #5 未改的影響**

- e2e 演練的證據收集是否會在 rename 情境誤判。
- 是否應另排。

**(f) 其他 staged 清單呼叫點**

- 對照 R0 表與現行程式,是否仍有會做 rename 配對、卻未被涵蓋的呼叫點。

**(g) 程式改動範圍**

- 是否僅限兩處旗標與 docstring。
- docstring 的敘述是否正確。

**(h) 證據分級**

- 是否被混用,特別是 (3)(4)(5)。
- 帳本只追加的證明是否成立。

**(i) 豁免帳本**

- 3 筆的分配是否符合裁決 (s)。S4 審計 §8:2 筆隨 `9efca02`、1 筆隨 `4d35073`。

## §5 審查者須知

- 本審查包只是索引。獨立審查仍須自行核對原始契約(票 148 與 Jeff 裁決)、程式、測試與報告,不得只依本包摘要下結論。
- 必須在全新視窗進行。
- 只讀 repo 與報告;探針只能在 `<scratchpad>` 的獨立複本裡做。
- 不得改 repo、不得 commit、不得 push。
- 審查結論寫入一份新報告,是否入庫由 Jeff 另裁。
- PASS / PASS-with-notes 不等於推送授權。
