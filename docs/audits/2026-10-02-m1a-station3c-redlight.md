# 票 145(M1-a)Station 3c 紅燈證據(含 3c-1b)

## 【給裁決者】

1. Station 3c 紅燈寫在兩個測試檔的檔尾(S3c-1),一支 driver 缺陷另外修過(S3c-1b)。
2. 第一次驗收:15 failed / 1952 passed,偏差是 C3e-1 因為錯的理由通過(driver 狀態殘留),依程序停手。
3. 第二次驗收:16 支預期紅燈全部失敗,5 支 regression-lock 與其他既有測試全部通過。
4. 第二次的 pytest 摘要行原文被 tool 輸出截斷而遺失;失敗集合以 pytest 自己的 lastfailed 快取與帳本兩個來源證明(裁決:照寫並標明)。
5. 帳本 H0 → H1 → H2 兩段都是只追加(前段雜湊相符)。

---

## 1. 前置值(S3c-1 第 0 步,當時實際記錄)

```
$ git rev-list --left-right --count origin/master...HEAD
0	19
$ git rev-parse HEAD
d122df42f1a90704961d6e07f98d5e6cd719f99e
$ git status --porcelain
(無輸出)
$ cat .dev/pipeline.json
{
  "current_stage": "tickets",
  "feature": "framework-updates",
  "ticket_id": "145",
  "updated": "2026-10-02"
}
$ wc -l tests/test_redlight.py tests/test_status.py
   632 tests/test_redlight.py
  1755 tests/test_status.py
  2387 total
$ sha256sum .dev/test-runs.jsonl
73737b7ddc353b2049d3bf8a61e831c9e2ab57e44b634ba91349447d1d0a8a93 *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
42bdc38e99695014d384f501cbf8517ca6a72d5bde690f090fcfc190d6c27e35 *.dev/test-sessions.jsonl
$ wc -c -l .dev/test-runs.jsonl .dev/test-sessions.jsonl
   2319  624488 .dev/test-runs.jsonl
     12 1873333 .dev/test-sessions.jsonl
   2331 2497821 total
```

## 2. S3c-1(`175da887f404fe0e1029de8bb2e438ab62f4aebb`)

`git diff --cached -U0` 的 hunk 標頭原文(兩檔各恰好一個 hunk,沒有任何 `-` 行;N_r = 632、N_s = 1755):

```
@@ -632,0 +633,409 @@ class TestFixedCommandCoverage:
@@ -1755,0 +1756,514 @@ class TestMalformedSessionIsVisible:
```

`git diff --cached --check`:無輸出。commit 輸出:

```
[master 175da88] test(145): M1-a Station 3c 紅燈 —— 選擇/執行完整性與 plugin 邊界(16 behavior-red + 5 regression-lock)
 3 files changed, 1025 insertions(+), 3 deletions(-)
```

## 3. 第一次驗收(在 S3c-1 上,只跑一次)

```
$ date -u +%Y-%m-%dT%H:%M:%SZ
2026-10-02T18:56:51Z
$ python -X utf8 -m pytest -q
...
FAILED tests/test_redlight.py::TestCompletenessCoverage::test_c3a_lf_silent_narrowing_is_not_full_coverage
FAILED tests/test_redlight.py::TestCompletenessCoverage::test_c3b_a_session_without_completeness_facts_is_not_full_coverage
FAILED tests/test_redlight.py::TestCompletenessCoverage::test_c3b_a_malformed_completeness_fact_is_not_full_coverage
FAILED tests/test_redlight.py::TestCompletenessCoverage::test_c3c_an_exitfirst_run_is_not_full_coverage
FAILED tests/test_redlight.py::TestCompletenessCoverage::test_c3p_an_unknown_plugin_dist_means_not_full_coverage
FAILED tests/test_redlight.py::TestCompletenessCoverage::test_c3p_a_plugin_loaded_by_name_means_not_full_coverage
FAILED tests/test_redlight.py::TestCompletenessCoverage::test_c3p_an_extra_conftest_means_not_full_coverage
FAILED tests/test_status.py::TestSilentNarrowingChain::test_c3a_lf_narrowing_does_not_retire_an_unidentified_red
FAILED tests/test_status.py::TestSilentNarrowingChain::test_c3a_lf_narrowing_does_not_make_a_clean_file_green
FAILED tests/test_status.py::TestEarlyStopChain::test_c3c_exitfirst_does_not_orphan_a_known_red
FAILED tests/test_status.py::TestEarlyStopChain::test_c3c_pytest_exit_zero_partial_file_is_not_green
FAILED tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_an_unknown_dist_plugin_as_other
FAILED tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_a_plugin_loaded_by_name_as_other
FAILED tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_an_extra_conftest_as_other_and_the_root_conftest_as_root_conftest
FAILED tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_builtin_root_conftest_and_known_dist_as_not_other
15 failed, 1952 passed, 3 skipped, 3 xfailed in 151.15s (0:02:31)
```

(exit code 1。tool 輸出中段截斷約 16790 字元;摘要行與 short test summary 完整。)

**偏差**:`tests/test_status.py::TestLfFalseGreenChain::test_c3e_full_then_lf_does_not_produce_a_false_green` 通過(預期失敗)。依程序不修、不重跑,停手回報。

**原因**(裁決助手在隔離環境以 d122df4 的 conftest / redlight / status 重現):
- C3e-1 用同一個 conftest 模組連續驅動 R1、R2、R3,中間沒有重置模組狀態(`tests/conftest.py:137` 的 `_outcomes`、`:143` 的 `_run`,`pytest_sessionfinish` 不會清掉它們)。
- R1 的收集錯誤殘留,R2 的 session 因此判 D。
- R2 的 outcome(S_A)殘留到 R3,而 R3 的 selected 只有 S_B ⇒ outcome 身分不屬於 selected ⇒ R3 判 **INVALID**(`.claude/hooks/redlight.py:331-334`)⇒ 不退紅 ⇒ 測試因錯誤的理由通過。
- 每次執行都是全新狀態時,R3 判 A、該檔判 green(即 S5b-F1),測試會如預期失敗。
- 更正:VS 第一次回報時把 R3 寫成「判 D」,依據不完整(只考慮了收集錯誤殘留,沒有考慮 outcome 殘留)。裁決助手的重現結果是 R3 為 INVALID,本報告以此為準。

## 4. S3c-1b(`49bcde20adc276632fa5bab456e8c7a80839fc0b`)

只改 `test_c3e_full_then_lf_does_not_produce_a_false_green`:R1 / R2 / R3 各自用新的 `_chain_conftest(root, monkeypatch)` 載入全新的 conftest;加上情境斷言 R1 = D、R2 = B、R3 = A 且 schema 合格;red / green 兩行斷言不變;docstring 補一句。

`git diff --cached -U0 -- tests/test_status.py` 的 hunk 標頭原文:

```
@@ -2142,0 +2143,2 @@ class TestLfFalseGreenChain:
@@ -2147,3 +2149,4 @@ class TestLfFalseGreenChain:
@@ -2151 +2154,8 @@ class TestLfFalseGreenChain:
```

函式範圍:修改前第 2137–2154 行,修改後第 2137–2164 行。三個 hunk(舊 2142–2151 / 新 2143–2161)都落在範圍內。
`git diff --cached --check`:無輸出。commit 輸出:

```
[master 49bcde2] test(145): M1-a Station 3c-1b —— C3e-1 每次執行改用全新 conftest(修 driver 狀態殘留)
 1 file changed, 14 insertions(+), 4 deletions(-)
```

## 5. 第二次驗收(在 S3c-1b 上,只跑一次)

```
$ date -u +%Y-%m-%dT%H:%M:%SZ
2026-10-02T19:06:34Z
$ python -X utf8 -m pytest -q
```

exit code 1。**tool 輸出在結尾被截斷**:摘要行原文與 short test summary 的後半沒有顯示。以下是保留下來的部分原文:

```
........................................FFFFFFF......................... [ 76%]
...
..........FFF..F.F.FFFF................................................. [ 94%]
...
FAILED tests/test_redlight.py::TestCompletenessCoverage::test_c3a_lf_silent_narrowing_is_not_full_coverage
FAILED tests/test_redlight.py::TestCompletenessCoverage::test_c3b_a_session_without_completeness_facts_is_not_full_coverage
FAILED tests/test_redlight.py::TestCompletenessCoverage::test_c3b_a_malformed_completeness_fact_is_not_full_coverage
FAILED tests/test_redlight.py::TestCompletenessCoverage::test_c3c_an_exitfirst_run_is_not_full_coverage
FAILED tests/test_redlight.py::TestCompletenessCoverage::test_c3p_an_unknown_plugin_dist_means_not_full_coverage
FAILED tests/test_redlight.py::TestCompletenessCoverage::test_c3p_a_plugin_loaded_by_name_means_not_
```

(進度列上的 `F` 共 7 + 9 = 16 個。)**依裁決不重跑**,失敗集合與計數改由下列來源證明:

**來源 A —— pytest 自己寫的 `.pytest_cache/v/cache/lastfailed`(pytest 原始資料)**:

```
{
  "tests/test_gate.py::TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce": true,
  "tests/test_stage_defs_source.py::TestTheWorktreePathDerivesFromRoot::test_patching_root_moves_the_worktree_definition": true,
  "tests/test_redlight.py::TestCompletenessCoverage::test_c3a_lf_silent_narrowing_is_not_full_coverage": true,
  "tests/test_redlight.py::TestCompletenessCoverage::test_c3b_a_session_without_completeness_facts_is_not_full_coverage": true,
  "tests/test_redlight.py::TestCompletenessCoverage::test_c3b_a_malformed_completeness_fact_is_not_full_coverage": true,
  "tests/test_redlight.py::TestCompletenessCoverage::test_c3c_an_exitfirst_run_is_not_full_coverage": true,
  "tests/test_redlight.py::TestCompletenessCoverage::test_c3p_an_unknown_plugin_dist_means_not_full_coverage": true,
  "tests/test_redlight.py::TestCompletenessCoverage::test_c3p_a_plugin_loaded_by_name_means_not_full_coverage": true,
  "tests/test_redlight.py::TestCompletenessCoverage::test_c3p_an_extra_conftest_means_not_full_coverage": true,
  "tests/test_status.py::TestSilentNarrowingChain::test_c3a_lf_narrowing_does_not_retire_an_unidentified_red": true,
  "tests/test_status.py::TestSilentNarrowingChain::test_c3a_lf_narrowing_does_not_make_a_clean_file_green": true,
  "tests/test_status.py::TestEarlyStopChain::test_c3c_exitfirst_does_not_orphan_a_known_red": true,
  "tests/test_status.py::TestEarlyStopChain::test_c3c_pytest_exit_zero_partial_file_is_not_green": true,
  "tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_an_unknown_dist_plugin_as_other": true,
  "tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_a_plugin_loaded_by_name_as_other": true,
  "tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_an_extra_conftest_as_other_and_the_root_conftest_as_root_conftest": true,
  "tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_builtin_root_conftest_and_known_dist_as_not_other": true,
  "tests/test_status.py::TestLfFalseGreenChain::test_c3e_full_then_lf_does_not_produce_a_false_green": true
}
```

- 第 3–19 行恰好是預期的 16 支。
- 前兩筆是**身分已不存在的舊紀錄**:pytest 只在本次有收集、而且通過時才移除 lastfailed 項目(`_pytest/cacheprovider.py:348-350, 354-359`)。
  Grep 證明:`tests/test_stage_defs_source.py` 沒有 `TestTheWorktreePathDerivesFromRoot` 類別;`tests/test_gate.py:834` 的 `TestLegacyNoRedlightList` 類別還在,但其中已經沒有 `test_the_list_is_what_the_generator_would_produce` 方法。

**來源 B —— 帳本 `.dev/test-runs.jsonl` 本次新增的 46 行(第 2366–2411 行)**:
- 第 2396 行 `tests/test_redlight.py` red,`failed_tests` 7 項(上表 test_redlight 的 7 支);
- 第 2404 行 `tests/test_status.py` red,`failed_tests` 9 項(上表 test_status 的 9 支,含 C3e-1);
- 其餘 44 行全部 `"result": "green"`。

**來源 C —— `status.py`(受測系統的 producer 紀錄,不是 pytest 原文)**:`最近一次 run:B(exit 1;collected 1973 / deselected 0 / passed 1951 / failed 16 / skipped 3)`。
collected 1973 = 1951 + 16 + 3 + 3(xfail 記為 other)。

## 6. 21 支逐支結果

| ID | nodeid | 分類 | 第一次(S3c-1) | 第二次(S3c-1b) |
|---|---|---|---|---|
| C3a-1 | tests/test_redlight.py::TestCompletenessCoverage::test_c3a_lf_silent_narrowing_is_not_full_coverage | behavior-red | failed | failed |
| C3a-2 | tests/test_status.py::TestSilentNarrowingChain::test_c3a_lf_narrowing_does_not_retire_an_unidentified_red | behavior-red | failed | failed |
| C3a-3 | tests/test_status.py::TestSilentNarrowingChain::test_c3a_lf_narrowing_does_not_make_a_clean_file_green | behavior-red | failed | failed |
| C3b-1 | tests/test_redlight.py::TestCompletenessCoverage::test_c3b_a_session_without_completeness_facts_is_not_full_coverage | behavior-red | failed | failed |
| C3b-2 | tests/test_redlight.py::TestCompletenessCoverage::test_c3b_a_malformed_completeness_fact_is_not_full_coverage | behavior-red | failed | failed |
| C3c-1 | tests/test_redlight.py::TestCompletenessCoverage::test_c3c_an_exitfirst_run_is_not_full_coverage | behavior-red | failed | failed |
| C3c-2 | tests/test_status.py::TestEarlyStopChain::test_c3c_exitfirst_does_not_orphan_a_known_red | behavior-red | failed | failed |
| C3c-5 | tests/test_status.py::TestEarlyStopChain::test_c3c_pytest_exit_zero_partial_file_is_not_green | behavior-red | failed | failed |
| C3e-1 | tests/test_status.py::TestLfFalseGreenChain::test_c3e_full_then_lf_does_not_produce_a_false_green | behavior-red | **passed(偏差)** | failed |
| C3p-1 | tests/test_redlight.py::TestCompletenessCoverage::test_c3p_an_unknown_plugin_dist_means_not_full_coverage | behavior-red | failed | failed |
| C3p-2 | tests/test_redlight.py::TestCompletenessCoverage::test_c3p_a_plugin_loaded_by_name_means_not_full_coverage | behavior-red | failed | failed |
| C3p-3 | tests/test_redlight.py::TestCompletenessCoverage::test_c3p_an_extra_conftest_means_not_full_coverage | behavior-red | failed | failed |
| C3p-4 | tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_an_unknown_dist_plugin_as_other | behavior-red | failed | failed |
| C3p-5 | tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_a_plugin_loaded_by_name_as_other | behavior-red | failed | failed |
| C3p-6 | tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_an_extra_conftest_as_other_and_the_root_conftest_as_root_conftest | behavior-red | failed | failed |
| C3p-7 | tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_builtin_root_conftest_and_known_dist_as_not_other | behavior-red | failed | failed |
| C3c-3 | tests/test_status.py::TestEarlyStopChain::test_c3c_exitfirst_does_not_make_unrun_files_green | regression-lock | passed | passed |
| C3c-4 | tests/test_status.py::TestEarlyStopChain::test_c3c_stepwise_stop_is_d_and_retires_nothing | regression-lock | passed | passed |
| C3d-1 | tests/test_redlight.py::TestCompletenessCoverage::test_c3d_the_fixed_command_with_everything_off_is_full_coverage | regression-lock | passed | passed |
| C3d-2 | tests/test_status.py::TestCompletenessLocks::test_c3d_the_fixed_command_full_run_still_retires_the_red | regression-lock | passed | passed |
| C3x-1 | tests/test_status.py::TestEarlyStopChain::test_setup_only_run_is_not_green | regression-lock | passed | passed |

「passed」的依據:第一次是不在 FAILED 清單內(清單完整);第二次是不在 lastfailed 內(來源 A),而且帳本中該檔的 `failed_tests` 不含它(來源 B)。規劃檔 P4 那六支受影響的既有測試兩次都不在失敗集合內。

## 7. 帳本只追加證據鏈

| 點 | test-runs | test-sessions | 值的來源 |
|---|---|---|---|
| H0(第一次驗收前) | 624488 bytes / 2319 行 / `73737b7ddc353b2049d3bf8a61e831c9e2ab57e44b634ba91349447d1d0a8a93` | 1873333 bytes / 12 行 / `42bdc38e99695014d384f501cbf8517ca6a72d5bde690f090fcfc190d6c27e35` | VS 當時記錄(S3c-1 第 0 步);與裁決助手獨立量測相同 |
| H1(第一次驗收後) | 637099 bytes / 2365 行 / `95cee485cf98c1e9fb45e4a77641a59d9798756f268f10fd591fd79719aa2ad3` | 2338347 bytes / 13 行 / `5dbe56fea2e22747058b826269ce8023974dc45b561bcb82d94a42ccf73c9863` | VS 量測(3c-1b 第 0 步);與裁決助手獨立量測相同 |
| H2(第二次驗收後) | 649789 bytes / 2411 行 / `36bf61df9c2a4b68d109f419d2020184e101edbd8de8131723c085b86f8f2544` | 2803361 bytes / 14 行 / `0ef187e02160759dba4912650d7baa0d3642a3b1902e91add71a20f97e477c45` | VS 量測(3c-1b 第 3 步) |

prefix 驗證(`head -c <前一點的 bytes>` 寫到 session scratch,再取 sha256;scratch 路徑以 `<session scratch>` 代替):

| 段 | 檔 | 前段 bytes | 前段 sha256 | 等於 |
|---|---|---|---|---|
| H0 → H1 | test-runs | 624488 | `73737b7ddc353b2049d3bf8a61e831c9e2ab57e44b634ba91349447d1d0a8a93` | H0r ✓ |
| H0 → H1 | test-sessions | 1873333 | `42bdc38e99695014d384f501cbf8517ca6a72d5bde690f090fcfc190d6c27e35` | H0s ✓ |
| H1 → H2 | test-runs | 637099 | `95cee485cf98c1e9fb45e4a77641a59d9798756f268f10fd591fd79719aa2ad3` | H1r ✓ |
| H1 → H2 | test-sessions | 2338347 | `5dbe56fea2e22747058b826269ce8023974dc45b561bcb82d94a42ccf73c9863` | H1s ✓ |

- 每段 test-runs 增加 46 行(= 測試檔數),test-sessions 增加 1 行。
- H0 → H1 的驗證是在 3c-1b 第 0 步做的(在第二次驗收之前)。
- 兩次驗收之後,`git status --porcelain` 都沒有輸出。

## 8. status.py(第二次驗收後)

`python .claude/portable/status.py --root .` 的 Evidence 與 Derived 兩段(逐字):

```
=== Evidence ===
test-runs: 本票 red 2 / green 44 / run 事實未知 0 / orphaned 0 / schema 不合格 run 0;最後一筆 tests/test_verify_gates.py=green @ 2026-10-02T19:08:53.377214+00:00;最近一次 run:B(exit 1;collected 1973 / deselected 0 / passed 1951 / failed 16 / skipped 3)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl)
intercepts (當月): 2 筆  (source: .dev/intercepts-2026-10.jsonl)
intercepts (最新存在月): 2026-10 2 筆;末筆 R7@2026-10-02T18:03:07.370596+00:00  (source: .dev/intercepts-2026-10.jsonl)
exemptions: 總 281 筆;granted 240 筆;blocked 1 筆;未記錄(無此欄)40 筆;最後一筆 2026-09-24T08:17:49.073745+00:00  (source: .dev/gate-exemptions.jsonl)
provenance: 未記錄(上游無此檔屬正常)  (source: .dev/provenance.jsonl)
report: 2026-10-02T174245Z-ticket145-station5b-0.md;HEAD 2026-10-02T15:06:26-04:00;回報後 4 筆  (source: .dev/reports/)

=== Derived ===
src write allowed in tickets: no  (source: gate.stage_allows_src_write() <- .agents/pipeline-stages.yaml)
tests red under ticket 145: tests/test_redlight.py / tests/test_status.py  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests green under ticket 145: tests/test_adr_numbering.py / tests/test_adr_numbers_resolve_upstream.py / tests/test_apply_patches.py / tests/test_bash_write.py / tests/test_bootstrap.py / tests/test_canon_section.py / tests/test_ci_workflow.py / tests/test_cjk_git_paths.py / tests/test_claude_md.py / tests/test_declared_in_is_an_identity.py / tests/test_dependency_ceiling.py / tests/test_edit_result.py / tests/test_evidence_isolation.py / tests/test_friction_heading.py / tests/test_g1_guard.py / tests/test_g1_verify.py / tests/test_gate.py / tests/test_gate_boundaries.py / tests/test_gitlink_downstream_cycle.py / tests/test_install.py / tests/test_intercepts.py / tests/test_known_items_regression.py / tests/test_leak_scan.py / tests/test_ledger_verify.py / tests/test_line_ending_parity.py / tests/test_manifest.py / tests/test_mcp_server.py / tests/test_non_source_list_parity.py / tests/test_portable_output_encoding.py / tests/test_r5_mounts.py / tests/test_research_stage.py / tests/test_scanner.py / tests/test_shadow.py / tests/test_shadow_review.py / tests/test_source_hygiene.py / tests/test_stage_defs_source.py / tests/test_stage_naming.py / tests/test_sync.py / tests/test_ticket_dirs_are_md_only.py / tests/test_ticket_lookup.py / tests/test_ticket_path_parity.py / tests/test_upstream_manifest.py / tests/test_user_layer.py / tests/test_verify_gates.py  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests green (run 事實未知) under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests orphaned under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
rules defined: R1 R2 R3 R4 R5 R6 R7 R8 R9  (source: gate.rule_codes())
```

符合預期:red 只有 `tests/test_redlight.py` 與 `tests/test_status.py`;最近一次 run 為 B。

## 9. 尚未證明

1. **第二次驗收的 pytest 摘要行原文未保存**(tool 輸出截斷)。預期的 `16 failed, 1951 passed, 3 skipped, 3 xfailed` 沒有以 pytest 原文證明;failed 集合由 lastfailed(pytest 原始資料)與帳本證明,計數由 status.py(producer 紀錄)得出。xfailed 3 是由 collected − passed − failed − skipped 推得。
2. 兩次驗收的 tool 輸出都有截斷;第一次只截中段,摘要行與失敗清單完整。
3. driver 的假物件(`pytest.Item` / `pytest.File` 子類以 `object.__new__` 建立、new-style wrapper 協定、xfail 以 `wasxfail` 表達)是否符合 4c 實作的實際需求,要到 4c 才驗得到。
4. 6 支受影響的既有測試(規劃檔 P4)在 4c 才會受新規則影響;本站只證明它們在 d122df4 + 新測試上仍通過。
5. CLEAN / REAL 層未證明。
