# 票 145(M1-a)Station 3d 紅燈證據 —— 收集定義完整性與版本邊界

## 【給裁決者】

1. 依〈二十九〉的合約(裁 C)寫了 19 支紅燈:13 支 behavior-red 現在必須失敗、6 支 regression-lock 現在必須通過,只接在兩個測試檔的最末尾(S3d-1)。
2. 在 S3d-1 上只跑了一次固定全套:`13 failed, 1973 passed, 3 skipped, 3 xfailed`,失敗的正好是預期的 13 支,其他全部通過。
3. 帳本只追加(前段雜湊與跑之前相同);status 的紅只剩 test_redlight 與 test_status 兩檔,最近一次 run 為 B。
4. 要你決定:是否驗收 3d、開始 4d;以及 pytest / anyio 要不要另行 pin(目前沒有結構性固定,見前置 (a)(b)(c))。
5. 不決定的話:4d 不能動工;版本沒 pin 的影響是換環境後無法退紅(fail-closed,不會假綠)。

---

## 1. 前置

```
$ git rev-list --left-right --count origin/master...HEAD
0	27
$ git rev-parse HEAD
9d1446a716cb0cc1258b7e16d6915b405e2c0c76
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
  1063 tests/test_redlight.py
  2298 tests/test_status.py
  3361 total
$ wc -c -l .dev/test-runs.jsonl .dev/test-sessions.jsonl
   2457  661092 .dev/test-runs.jsonl
     15 3494564 .dev/test-sessions.jsonl
   2472 4155656 total
$ sha256sum .dev/test-runs.jsonl
352e7d2653301e11d16494c100d67231e47efcabe2a7a047a297402046972172 *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
b48ee090beb214f264476c2efc827b6d244cb6b70cf0d669adffd6d3ce871870 *.dev/test-sessions.jsonl
```

- `python -m pip show pytest`:`Version: 9.1.1`。
- `python -m pip show anyio`:`Version: 4.15.0`。這次輸出夾帶多段 pip 自己的 `--- Logging error ---`(`UnicodeEncodeError: 'cp950' codec can't encode character '\xf6'`,作者名含 `ö`),是終端編碼問題,不影響版本值。`Location` 一行含本機使用者路徑,不照錄。
- N_r = 1063、N_s = 2298;L3 = test-runs 661092 bytes / 2457 行、test-sessions 3494564 bytes / 15 行;H3r、H3s 如上,與預期相同。

### 版本是否被結構性固定(補充裁決,只讀查證)

`git ls-tree -r --name-only 02a5e28adf5aee11a43d5a1063504f01beb1d67f` 中可能控制安裝版本的檔,只有 `pyproject.toml` 與 `.github/workflows/tests.yml`。**沒有** requirements*.txt、*.lock、constraints*.txt。

| 問題 | 結論 | 證據 |
|---|---|---|
| (a) pytest 是否精確固定為 9.1.1 | **否** | `02a5e28adf5aee11a43d5a1063504f01beb1d67f:pyproject.toml:34` 為 `"pytest>=8.0,<10",`(範圍) |
| (b) anyio 是否精確固定為 4.15.0 | **否**:pyproject.toml 完全沒有宣告 anyio(`git grep -n -E "pytest\|anyio\|mcp\|dependencies"` 對該檔沒有 anyio 命中);它是間接相依(本機 `pip show anyio` 的 `Required-by: httpx, mcp, sse-starlette, starlette`) | 同左 |
| (c) CI 實際如何決定版本 | 執行當下由 pip 依範圍解析 | `02a5e28adf5aee11a43d5a1063504f01beb1d67f:.github/workflows/tests.yml:50` `run: python -m pip install -e ".[dev]"`;`:47` `python-version: '3.11'` |

⇒ 已依補充裁決在〈二十九〉第 3 點追加一條「已知殘餘」。

## 2. 靜態證明(commit 前)

```
$ python -X utf8 -m py_compile tests/test_redlight.py
(無輸出)
$ python -X utf8 -m py_compile tests/test_status.py
(無輸出)
$ wc -c -l .dev/test-runs.jsonl .dev/test-sessions.jsonl
   2457  661092 .dev/test-runs.jsonl
     15 3494564 .dev/test-sessions.jsonl
   2472 4155656 total
$ git diff --cached --name-only
docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
tests/test_redlight.py
tests/test_status.py
```

`git diff --cached -U0` 的 hunk 標頭(原文;每檔恰好一個 hunk,沒有任何以 `-` 開頭的內容行):

```
@@ -1063,0 +1064,415 @@ class TestCompletenessCoverage:
```
```
@@ -2298,0 +2299,245 @@ class TestPluginProducerChain:
```

`git diff --cached --check`:無輸出。

- S3d-1:`33b8bb4ba6e5601c011d6a50eda9504610c69665`(`3 files changed, 755 insertions(+), 3 deletions(-)`;3 行刪除全部在票 145)。
- commit 後 `git status --porcelain` 無輸出;`git rev-list --left-right --count origin/master...HEAD` = `0	28`。

## 3. 19 支逐支表

「經真實 conftest producer」:由 `_isolated_conftest` / `_chain_conftest` 每次載入全新的 `tests/conftest.py`,經它的 hook 寫入 tmp root 帳本,再由 `file_coverage` / status 讀回。19 支全部如此;沒有任何一支直接餵 completeness dict。「真 git」:在 tmp root 建立真的 git repo,並提交 `pyproject.toml` 與 `tests/conftest.py`;19 支全部如此。

| # | nodeid | 分類 | 實際結果 | 真實 producer | 真 git |
|---|---|---|---|---|---|
| 1 | tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3a_an_override_ini_narrowing_is_not_full_coverage | behavior-red | FAILED | 是 | 是 |
| 2 | tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3b_an_override_from_pytest_addopts_is_not_full_coverage | behavior-red | FAILED | 是 | 是 |
| 3 | tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3c_a_config_file_option_is_not_full_coverage | behavior-red | FAILED | 是 | 是 |
| 4 | tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3c_a_config_file_option_naming_the_committed_config | behavior-red | FAILED | 是 | 是 |
| 5 | tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3w_an_unexpected_config_file_is_not_full_coverage | behavior-red | FAILED | 是 | 是 |
| 6 | tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3w_an_uncommitted_config_change_is_not_full_coverage | behavior-red | FAILED | 是 | 是 |
| 7 | tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3w_a_non_collection_edit_to_the_config_file | behavior-red | FAILED | 是 | 是 |
| 8 | tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3w_an_uncommitted_root_conftest_change_is_not_full_coverage | behavior-red | FAILED | 是 | 是 |
| 9 | tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3v_an_unrecognized_pytest_version_is_not_full_coverage | behavior-red | FAILED | 是 | 是 |
| 10 | tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3v_a_known_plugin_with_unrecognized_version_is_not_full_coverage | behavior-red | FAILED | 是 | 是 |
| 11 | tests/test_status.py::TestOverrideIniChain::test_d3a_full_then_override_ini_does_not_produce_a_false_green | behavior-red | FAILED | 是(三次,各一個新 conftest) | 是 |
| 12 | tests/test_status.py::TestOverrideIniChain::test_d3a_override_ini_does_not_orphan_a_known_red | behavior-red | FAILED | 是 | 是 |
| 13 | tests/test_status.py::TestOverrideIniChain::test_d3a_override_ini_does_not_make_a_clean_file_green | behavior-red | FAILED | 是 | 是 |
| 14 | tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3i_lf_alone_is_not_full_coverage | regression-lock | passed | 是(對照組與破壞組各一個新 conftest) | 是 |
| 15 | tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3i_maxfail_alone_is_not_full_coverage | regression-lock | passed | 是(同上) | 是 |
| 16 | tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3i_shouldfail_alone_is_not_full_coverage | regression-lock | passed | 是(同上) | 是 |
| 17 | tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3x_a_blocked_plugin_is_not_full_coverage | regression-lock | passed | 是 | 是 |
| 18 | tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3d_the_fixed_command_with_the_committed_config_is_full_coverage | regression-lock | passed | 是 | 是 |
| 19 | tests/test_status.py::TestCollectionDefinitionLocks::test_d3d_the_fixed_command_full_run_still_retires_the_red | regression-lock | passed | 是 | 是 |

regression-lock 的「passed」由兩件事推得:摘要行的失敗清單不含它們,且 `13 failed` 恰為預期紅集合。pytest 沒有逐一列出通過的測試名。

## 4. 驗收(在 S3d-1 上只跑一次)

```
$ date -u +%Y-%m-%dT%H:%M:%SZ
2026-10-02T23:32:15Z
$ python -X utf8 -m pytest -q
```

exit code 1。tool 輸出中段截斷約 12573 字元(FAILURES 區的部分 traceback);進度列、short test summary info 與摘要行完整。以下為保留的原文(tmp 路徑中的本機使用者名稱已遮成 `<user>`,**這兩處不是逐字原文**):

```
................................................FFFFFFFFFF.............. [ 75%]
...
......................................FFF............................... [ 93%]
...
E       AssertionError: {'red': '(無)', 'green': '(無)', 'orphaned': 'tests/test_x.py(tests/test_x.py::test_a)'}
...
E       AssertionError: {'red': '(無)', 'green': 'tests/test_x.py', 'orphaned': '(無)'}
...
tmp_path = WindowsPath('C:/Users/<user>/AppData/Local/Temp/pytest-of-<user>/pytest-172/test_d3a_an_override_ini_narro0')
...
E       AssertionError: true
E       assert 'true' != 'true'
...
=========================== short test summary info ===========================
SKIPPED [1] tests\test_gate.py:451: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:459: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:473: 此環境無法建立 symlink
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/srv/x] - …
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/data/x] - …
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/backup/x] - …
FAILED tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3a_an_override_ini_narrowing_is_not_full_coverage
FAILED tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3b_an_override_from_pytest_addopts_is_not_full_coverage
FAILED tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3c_a_config_file_option_is_not_full_coverage
FAILED tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3c_a_config_file_option_naming_the_committed_config
FAILED tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3w_an_unexpected_config_file_is_not_full_coverage
FAILED tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3w_an_uncommitted_config_change_is_not_full_coverage
FAILED tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3w_a_non_collection_edit_to_the_config_file
FAILED tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3w_an_uncommitted_root_conftest_change_is_not_full_coverage
FAILED tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3v_an_unrecognized_pytest_version_is_not_full_coverage
FAILED tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3v_a_known_plugin_with_unrecognized_version_is_not_full_coverage
FAILED tests/test_status.py::TestOverrideIniChain::test_d3a_full_then_override_ini_does_not_produce_a_false_green
FAILED tests/test_status.py::TestOverrideIniChain::test_d3a_override_ini_does_not_orphan_a_known_red
FAILED tests/test_status.py::TestOverrideIniChain::test_d3a_override_ini_does_not_make_a_clean_file_green
13 failed, 1973 passed, 3 skipped, 3 xfailed in 147.44s (0:02:27)
```

(XFAIL 三行的說明文字以 `…` 截斷;FAILED、SKIPPED 與摘要行逐字。)

- **失敗集合 = 預期紅集合**:FAILED 13 行與〈二十九〉29.2 的 13 個 nodeid 逐字相同,沒有多、沒有少。
- **摘要 = 預期**:`13 failed, 1973 passed, 3 skipped, 3 xfailed`;collected 1992 = 13 + 1973 + 3 + 3(status 的 `collected 1992` 也一致)。
- 規劃檔 P4 那 9 支既有測試、6 支 regression-lock、其他全部既有測試都不在失敗清單 ⇒ 全部通過。
- 失敗的原因與預期一致:redlight 側 10 支都是 `AssertionError: true`(TARGET 判 `"true"`);status 側一支判 orphan、一支判 green。

## 5. 帳本 H3 → H4 只追加

```
$ git status --porcelain
(無輸出)
$ wc -c -l .dev/test-runs.jsonl .dev/test-sessions.jsonl
   2503  673590 .dev/test-runs.jsonl
     16 4192482 .dev/test-sessions.jsonl
   2519 4866072 total
$ sha256sum .dev/test-runs.jsonl
44c7a8fee77511678912a6acef33b8c5a449b7f6269dc1ad2b4f84e2e0e28eba *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
a2d1192f384e9f19258a59aa72496a3fe39e1dffa002706fd56c06ce37c2a2ea *.dev/test-sessions.jsonl
$ head -c 661092 .dev/test-runs.jsonl > <session scratch>/r.bin
$ head -c 3494564 .dev/test-sessions.jsonl > <session scratch>/s.bin
$ sha256sum <session scratch>/r.bin
352e7d2653301e11d16494c100d67231e47efcabe2a7a047a297402046972172 *<session scratch>/r.bin
$ sha256sum <session scratch>/s.bin
b48ee090beb214f264476c2efc827b6d244cb6b70cf0d669adffd6d3ce871870 *<session scratch>/s.bin
```

(scratch 絕對路徑以 `<session scratch>` 代替 —— 這四行經遮罩,不是逐字原文。)

| 點 | test-runs | test-sessions |
|---|---|---|
| H3(驗收前) | 661092 bytes / 2457 行 / `352e7d2653301e11d16494c100d67231e47efcabe2a7a047a297402046972172` | 3494564 bytes / 15 行 / `b48ee090beb214f264476c2efc827b6d244cb6b70cf0d669adffd6d3ce871870` |
| H4(驗收後) | 673590 bytes / 2503 行 / `44c7a8fee77511678912a6acef33b8c5a449b7f6269dc1ad2b4f84e2e0e28eba` | 4192482 bytes / 16 行 / `a2d1192f384e9f19258a59aa72496a3fe39e1dffa002706fd56c06ce37c2a2ea` |

⇒ 兩本前段都等於 H3;test-runs +46 行(= 測試檔數)、test-sessions +1 行。

## 6. status.py(驗收後)

`python .claude/portable/status.py --root .` 的 Evidence 與 Derived 兩段(逐字):

```
=== Evidence ===
test-runs: 本票 red 2 / green 44 / run 事實未知 0 / orphaned 0 / schema 不合格 run 0;最後一筆 tests/test_verify_gates.py=green @ 2026-10-02T23:34:38.330854+00:00;最近一次 run:B(exit 1;collected 1992 / deselected 0 / passed 1973 / failed 13 / skipped 3)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl)
intercepts (當月): 4 筆  (source: .dev/intercepts-2026-10.jsonl)
intercepts (最新存在月): 2026-10 4 筆;末筆 R7@2026-10-02T22:44:19.109578+00:00  (source: .dev/intercepts-2026-10.jsonl)
exemptions: 總 281 筆;granted 240 筆;blocked 1 筆;未記錄(無此欄)40 筆;最後一筆 2026-09-24T08:17:49.073745+00:00  (source: .dev/gate-exemptions.jsonl)
provenance: 未記錄(上游無此檔屬正常)  (source: .dev/provenance.jsonl)
report: 2026-10-02T174245Z-ticket145-station5b-0.md;HEAD 2026-10-02T19:32:08-04:00;回報後 11 筆  (source: .dev/reports/)

=== Derived ===
src write allowed in tickets: no  (source: gate.stage_allows_src_write() <- .agents/pipeline-stages.yaml)
tests red under ticket 145: tests/test_redlight.py / tests/test_status.py  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests green under ticket 145: tests/test_adr_numbering.py / tests/test_adr_numbers_resolve_upstream.py / tests/test_apply_patches.py / tests/test_bash_write.py / tests/test_bootstrap.py / tests/test_canon_section.py / tests/test_ci_workflow.py / tests/test_cjk_git_paths.py / tests/test_claude_md.py / tests/test_declared_in_is_an_identity.py / tests/test_dependency_ceiling.py / tests/test_edit_result.py / tests/test_evidence_isolation.py / tests/test_friction_heading.py / tests/test_g1_guard.py / tests/test_g1_verify.py / tests/test_gate.py / tests/test_gate_boundaries.py / tests/test_gitlink_downstream_cycle.py / tests/test_install.py / tests/test_intercepts.py / tests/test_known_items_regression.py / tests/test_leak_scan.py / tests/test_ledger_verify.py / tests/test_line_ending_parity.py / tests/test_manifest.py / tests/test_mcp_server.py / tests/test_non_source_list_parity.py / tests/test_portable_output_encoding.py / tests/test_r5_mounts.py / tests/test_research_stage.py / tests/test_scanner.py / tests/test_shadow.py / tests/test_shadow_review.py / tests/test_source_hygiene.py / tests/test_stage_defs_source.py / tests/test_stage_naming.py / tests/test_sync.py / tests/test_ticket_dirs_are_md_only.py / tests/test_ticket_lookup.py / tests/test_ticket_path_parity.py / tests/test_upstream_manifest.py / tests/test_user_layer.py / tests/test_verify_gates.py  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests green (run 事實未知) under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests orphaned under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
rules defined: R1 R2 R3 R4 R5 R6 R7 R8 R9  (source: gate.rule_codes())
```

⇒ red 只有 tests/test_redlight.py 與 tests/test_status.py;最近一次 run 為 B。與預期相符。

## 7. 尚未證明

1. **regression-lock 在 4d 之後仍會通過**:它們的固定全套事實(tmp git repo、`override_ini == ["strict_markers=true"]`、`pytest.__version__`、anyio 4.15.0)是依〈二十九〉的合約與 29.3 的介面細節建構的,4d 實作要照這些讀取點才會讓它們維持綠。目前只證明它們在 S3d-1 上通過。
2. **behavior-red 在 4d 之後「為了對的理由」轉綠**:現在每一支只證明「S3d-1 判 `"true"`」。4d 報告應逐支說明轉綠的主因是哪一條新條件(延續 S5c-F2 的關切)。
3. 29.3 的介面細節(pytest 版本讀 `pytest.__version__`、雜湊以 `_ROOT` 為根)是本刀定稿,不是裁決原文。
4. tmp git repo 的建立依賴本機 git;在沒有 git 的環境,這 19 支會在 setup 階段出錯(`check=True`),不是靜默通過。
5. `-p no:cacheprovider` 那支(D3x-1)在 S3d-1 上通過的理由是分類器的副作用(`(name, None)` 被判 other),不是明文規則;4d 改成明文的 (xii) 之後,它要繼續通過。
6. CLEAN / REAL 層未證明。
