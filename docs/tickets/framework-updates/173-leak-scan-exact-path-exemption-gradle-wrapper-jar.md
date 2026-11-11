# 票 173：洩漏偵測對 gradle/wrapper/gradle-wrapper.jar 的精確路徑豁免

狀態：實作完成；本輪提交（2026-11-11）；未 push。

## 背景

**實證缺陷**
- 下游 LifeApp（第一個含 Gradle wrapper 的下游）提交 slice1 票 01 里程碑時，pre-commit 的 leak_scan 擋下 `gradle/wrapper/gradle-wrapper.jar`，訊息為「命中 pattern:<讀不到內容>」。
- 該檔是 Gradle 官方要求進版控的二進位檔。掃描器讀不懂二進位而 fail-closed，行為符合現有設計（票 109 一脈：讀不懂就擋），但使任何含 Gradle wrapper 的下游無法提交。

**偵察結論**（依據唯讀偵察報告 `20261111T163438Z-wrapper-jar-exemption-recon.md`）
- 唯一實際入口是 `.githooks/pre-commit` 的 `leak_scan.py --staged`；leak_scan.py 以外沒有非測試程式呼叫掃描。
- `scanner.SKIP_SUFFIX` 沒有 `.jar`。
- leak_scan.py／scanner.py 不在 R10 名冊；manifest 以 `.claude/portable/ copy` 帶到下游。

## 裁決（Jeff 2026-11-11）

美東 11:27 裁 A 甲；11:43 裁 1A 2A。

- **1A 精確路徑豁免**：
  - 只接受 repo 相對路徑 `gradle/wrapper/gradle-wrapper.jar`；大小寫敏感、正規化（反斜線轉正斜線、取 repo 相對）後完全相同才成立。
  - 不做全域 `.jar` 豁免；不綁內容雜湊（wrapper 的版本與 SHA-256 另由 wrapper 自己的治理線管，不在掃描器維護第二份）。
  - pre-commit 放行時必須有可見提示（不得靜默跳過）。
  - review 模式必須列入「未內容掃描」清單、需人工確認。
  - 「同一路徑若被換成其他二進位檔仍會放行」記為〈已知限制〉，不宣稱已消除。
- **2A**：開票 173；站牌 implement／framework-updates／173 由 Jeff 本人切好。
- **邊界**：本票不做通用的二進位政策框架；不新增設定檔、不新增可擴充的豁免登記機制；只修這一個已實際擋住下游的路徑。
- **後續（不在本輪）**：commit → push → 同步 LifeApp → 實測 R10 是否需要動作 → 回 LifeApp 完成原本 19 檔 commit。

### 設計（定案）

- **D1 常數**：在 leak_scan.py 新增一個模組層 tuple，名稱 `EXACT_PATH_UNSCANNED`，內容恰為一個元素 `"gradle/wrapper/gradle-wrapper.jar"`。放在 `SKIP_BASENAMES` 之後；附註解說明它是「身分豁免（綁 repo 相對路徑）」、為何不放進 `SELF_PATHS`（`SELF_PATHS` 還會傳進 `scan_paths` 表示「掃描器自己」）、以及已知限制。
- **D2 判定**：在 `scan()` 的逐檔迴圈裡，取得 `rel` 之後、`should_skip` 之前判斷 `rel in EXACT_PATH_UNSCANNED`（大小寫敏感全等；`rel` 已由 `scanner.rel_path` 正規化）。命中時：
  - review 模式：加入 `not_scanned`，理由字串恰為「精確路徑豁免(Gradle wrapper)—— 未內容掃描,需人工確認」；
  - 非 review 模式：記入本函式內的清單（`exempted`），該檔不進 certs／rest；
  - 兩種模式都 continue，不讀該檔內容。
- **D3 可見提示**：非 review 模式下 `exempted` 非空時，在 `scan()` 回傳前一律印到 stderr（用既有 `_err`），不論最後回 0 或 1。第一行含「[洩漏偵測] 依精確路徑豁免」與「未內容掃描」與檔數；其後每個路徑一行；最後一行說明「只認 repo 相對路徑,不認內容 —— 這不是「掃過沒事」」。提示不影響退出碼（比照 `gitlink_note`）。
- **D4** 不改 scanner.py：`SKIP_SUFFIX`、`_globally_skipped`、`scan_paths` 都不動。
- **D5** `scan()` 的 docstring 補一兩句說明這個分流；其他函式不動。

## AC

| AC | 內容 | 測試（tests/test_leak_scan.py） |
|---|---|---|
| AC-1 | 精確路徑 ⇒ pre-commit 放行且有可見提示；提示不遮蔽其他命中 | `test_t173_exact_wrapper_path_passes_with_visible_notice`、`test_t173_notice_does_not_mask_other_hits` |
| AC-2 | 同名檔在其他目錄、其他 `.jar`、大小寫變體 ⇒ 仍擋 | `test_t173_same_name_elsewhere_still_blocked`、`test_t173_other_jars_still_blocked`、`test_t173_case_variant_still_blocked` |
| AC-3 | review 模式 ⇒ 列入未內容掃描且退出碼非 0 | `test_t173_review_lists_wrapper_as_unscanned` |
| AC-4 | 豁免集合恰為一個路徑 | `test_t173_exemption_set_is_exactly_one_path` |

## 已知限制

- 只綁路徑不綁內容：同一路徑被換成其他二進位檔（或可解碼且含機密的檔）仍會放行。
- 緩解：pre-commit 可見提示＋review 模式列出。
- 無實際案例；有案例再另案處理。

## 證到哪一層

- UNIT：本輪測試。
- CLEAN：push 後 CI（未證明）。
- REAL：同步後 LifeApp 的真實 commit（未證明）。

## 不在本票

全域 `.jar`／二進位政策、內容雜湊綁定、zip 魔數判定、只在解不出文字時才豁免、`SELF_PATHS` 的大小寫行為、其他下游。

## 文件同步

- `docs/adr/F-0015-going-public-requires-history-review.md` 第 90、93 行引用 `SELF_PATHS` 的內容（只列掃描器自己）；不列舉全部豁免，本票不改。若日後要讓該 ADR 涵蓋全部豁免，另案處理。
- 其他命中皆為歷史票面（23、72、73、132、133、143），不改。

## 關聯

- 下游 LifeApp slice1 票 01（被擋的那次提交）。
- 票 109 一脈的 fail-closed 設計（讀不懂就擋）——本票不改它，只在它之前開一個精確路徑的分流。

## 第 1 題對位結論

- leak_scan.py：`SKIP_BASENAMES` 73；`scan()` 逐檔迴圈 226、`rel` 取得 227、`should_skip` 分流 228、review 輸出段 245–252、return 255／258／265（另 223 為 pattern 讀不到的 return 2）。D2 插入點（227 與 228 之間）、D3 插入點（245 前）存在。
- 測試做法：`_t148_repo`（隔離 git config 的臨時 repo、`monkeypatch.setattr(ls, "ROOT", ...)`）、`ls.main(["--staged"])`、`capsys.readouterr().err`（`test_t148_5_secret_in_a_new_file_is_caught`）。新測試沿用。

## 驗證

引自報告 `20261111T175518Z-ticket173-wrapper-jar.md`（只引不重跑）：

- P1（實作前，紅燈首跑）：`4 failed, 3 passed, 79 deselected in 90.50s (0:01:30)`
- P2（實作後，票 173 測試）：`7 passed, 79 deselected in 8.59s`
- P3（test_leak_scan.py＋test_scanner.py）：`164 passed in 86.56s (0:01:26)`
- P4（全套）：`3542 passed, 39 skipped, 3 xfailed in 3297.60s (0:54:57)`

## 實作備註

- 測試用的二進位樣本不是單純的 0～31 位元組：依 scanner 的 UTF-16 解碼流程推得（未單獨實測），那樣的樣本可能被解成可讀文字、使反對照假綠；因此樣本交錯插入 NUL，並在測試內斷言 decode_bytes 對樣本回「讀不到」。
