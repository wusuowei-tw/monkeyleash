# 票 145(M1-a)Station 3e 紅燈證據 —— pass 有效性與路徑正規化

## 【給裁決者】

1. 依〈三十五〉在兩個測試檔的檔尾新增 28 支紅燈(18 支 behavior-red + 10 支 regression-lock),commit 為 S3e-1(`7ebbb81`)。只改了測試檔與票,沒有改產品碼。
2. 在 S3e-1 上只跑一次固定全套,失敗的恰好是預期的那 18 支;10 支 regression-lock 和其他既有測試全部通過;帳本(測試紀錄檔)只有追加。
3. **證據缺口**:這次執行的終端輸出被工具截斷,pytest 最後那一行摘要(例:`18 failed, 1997 passed …`)沒有留下原文。失敗清單與各項數字改由 producer 當次寫進帳本的紀錄,以及 status 的輸出取得(見第 5 節)。依規定不得重跑。
4. 要你決定:A 接受以帳本紀錄代替摘要行,驗收 3e;B 不接受,另行裁定補證方式(例如授權重跑一次並把輸出導進檔案)。
5. 不決定的話:票停在「3e 紅燈已寫,待驗收」,4e 不會開始。

---

## 1. 前置(S3e-1 之前)

```
$ git rev-list --left-right --count origin/master...HEAD
0	34
$ git rev-parse HEAD
22584908dcb791379b58da273dedefaadfbd5842
$ git status --porcelain
(無輸出)
$ cat .dev/pipeline.json
{
  "current_stage": "tickets",
  "feature": "framework-updates",
  "ticket_id": "145",
  "updated": "2026-10-02"
}
$ python --version
Python 3.11.9
$ wc -l tests/test_redlight.py tests/test_status.py
  1532 tests/test_redlight.py
  2565 tests/test_status.py
  4097 total
$ wc -c -l .dev/test-runs.jsonl .dev/test-sessions.jsonl
   2549  684893 .dev/test-runs.jsonl
     17 4891233 .dev/test-sessions.jsonl
   2566 5576126 total
$ sha256sum .dev/test-runs.jsonl
23f397d47c76bc6985daa73dd99afe73c84b53dd2220a4305ae64cb8b1e4086c *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
7463a45257c893ec9079f0f655782bfab11855eab9fcd5f93b314e5d60beb70c *.dev/test-sessions.jsonl
```

- `python -m pip show pytest`:`Version: 9.1.1`。`python -m pip show anyio`:`Version: 4.15.0`。兩者的 `Location` 行都含本機使用者路徑,不照錄。anyio 那次另有 pip 的 cp950 `Logging error` 回溯(stderr),與版本無關,不照錄。
- N_r = 1532、N_s = 2565。
- L5 = test-runs 684893 bytes / 2549 行、test-sessions 4891233 bytes / 17 行;H5r = `23f397d4…`、H5s = `7463a452…`。

### anyio 4.15.0 唯讀查證

以 Grep 搜尋已安裝 anyio 的 `pytest_plugin.py`:

| 搜尋項 | 結果 | 用途 |
|---|---|---|
| `addoption` | 有:`anyio/pytest_plugin.py:94-103`(`--anyio-mode`);ini `anyio_mode`(`:89-93`,預設 `strict`) | `auto` 時所有 async 測試由 anyio 執行(`:106-109, 192-207`) |
| `pytest_runtest_makereport` | 無 | — |
| `pytest_pyfunc_call` | 有:`anyio/pytest_plugin.py:268-302`(tryfirst) | 只處理帶 `anyio_backend` 的協程測試;例外一律重拋(`:291-298`),成功才回 True |
| `pytest_collection_modifyitems` | 無 | — |
| 附帶 | `pytest_configure`(`:112-128`)、`pytest_fixture_setup` hookwrapper(`:131-189`)、`pytest_pycollect_makeitem`(`:192-207`)、`pytest_collection_finish`(`:210-265`) | 不改 outcome |

**判斷:沒有找到會把失敗轉成通過的機制。**
- `--anyio-mode=auto` 只會讓原本因 pytest 不支援 async 而 `fail` 的測試(`_pytest/python.py:147-169`)真的執行,斷言照常評估。
- `pytest_collection_finish` 的項目替換屬 selection 面;身分對不上時由 `validate_session` 判為不合格(fail-closed)。

已記入票 145〈三十五〉35.2。

## 2. 寫紅燈與靜態證明(S3e-1)

- 只在兩檔的**檔尾**新增;沒有改任何既有行。
- commit 前只跑 `python -X utf8 -m py_compile tests/test_redlight.py` 與 `… tests/test_status.py`,兩者皆無輸出。
- 跑完 py_compile 後,`wc -c -l` 兩本帳 = L5(未變)。

```
$ git diff --cached --name-only
docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
tests/test_redlight.py
tests/test_status.py
$ git diff --cached --check
(無輸出)
```

`-U0` 的 hunk 標頭(原文):

```
@@ -1532,0 +1533,317 @@ class TestCollectionDefinitionCoverage:
@@ -2565,0 +2566,160 @@ class TestCollectionDefinitionLocks:
```

- 每檔恰好一個 hunk,`<N>` 分別等於 N_r = 1532、N_s = 2565;兩份 `-U0` 輸出都沒有以 `-` 開頭的內容行。

```
$ git commit -F .scratch/m1a-s3e/s3e-1-msg.txt
[master 7ebbb81] test(145): M1-a Station 3e 紅燈 —— pass 有效性與路徑正規化(18 behavior-red + 10 regression-lock)
 3 files changed, 578 insertions(+), 3 deletions(-)
$ git status --porcelain
(無輸出)
$ git rev-list --left-right --count origin/master...HEAD
0	35
$ git rev-parse HEAD
7ebbb815fbba96124d971fe0066c096c3f1db8e8
```

(`3 deletions` 全部在票 145:第 3 行狀態、〈十〉Station 3e 列、現況句,舊值依 F-036 保存。)

## 3. 28 支逐支表

「經真實 conftest producer」= 該測試的每一次模擬執行都經 `_isolated_conftest`(test_redlight)或 `_chain_conftest`(test_status)載入的真實 `tests/conftest.py`,由它寫入帳本;沒有任何一支直接餵 completeness dict。實際結果取自第 5 節帳本第 18 行。

| # | nodeid | 分類 | 實際結果 | 經真實 conftest producer |
|---|---|---|---|---|
| 1 | `tests/test_redlight.py::TestPassValidityCoverage::test_e3o_an_optimized_interpreter_is_not_full_coverage[1]` | behavior-red | failed | 是 |
| 2 | `tests/test_redlight.py::TestPassValidityCoverage::test_e3o_an_optimized_interpreter_is_not_full_coverage[2]` | behavior-red | failed | 是 |
| 3 | `tests/test_redlight.py::TestPassValidityCoverage::test_e3o_a_missing_optimize_fact_is_not_full_coverage` | behavior-red | failed | 是 |
| 4 | `tests/test_redlight.py::TestPassValidityCoverage::test_e3x_runxfail_alone_is_not_full_coverage` | behavior-red | failed | 是 |
| 5 | `tests/test_redlight.py::TestPassValidityCoverage::test_e3w_a_pytest_warning_filter_alone_is_not_full_coverage` | behavior-red | failed | 是 |
| 6 | `tests/test_redlight.py::TestPassValidityCoverage::test_e3t_trace_alone_is_not_full_coverage` | behavior-red | failed | 是 |
| 7 | `tests/test_redlight.py::TestPassValidityCoverage::test_e3v_an_unrecognized_python_version_is_not_full_coverage` | behavior-red | failed | 是 |
| 8 | `tests/test_redlight.py::TestPassValidityCoverage::test_e3o_the_producer_records_the_interpreter_optimize_flag` | behavior-red | failed | 是 |
| 9 | `tests/test_redlight.py::TestPassValidityCoverage::test_e3x_the_producer_records_runxfail_and_pythonwarnings` | behavior-red | failed | 是 |
| 10 | `tests/test_redlight.py::TestProducerPathNormalization::test_e3p_blocked_plugin_names_never_persist_a_path[win-abs]` | behavior-red | failed | 是 |
| 11 | `tests/test_redlight.py::TestProducerPathNormalization::test_e3p_blocked_plugin_names_never_persist_a_path[posix-abs]` | behavior-red | failed | 是 |
| 12 | `tests/test_redlight.py::TestProducerPathNormalization::test_e3p_blocked_plugin_names_never_persist_a_path[rel-escape]` | behavior-red | failed | 是 |
| 13 | `tests/test_redlight.py::TestProducerPathNormalization::test_e3p_a_config_file_option_never_persists_a_path[rel-escape]` | behavior-red | failed | 是 |
| 14 | `tests/test_redlight.py::TestProducerPathNormalization::test_e3p_an_override_value_never_persists_a_path[rel-escape]` | behavior-red | failed | 是 |
| 15 | `tests/test_status.py::TestPassValidityChain::test_e3o_optimized_pass_does_not_retire_a_known_red` | behavior-red | failed | 是 |
| 16 | `tests/test_status.py::TestPassValidityChain::test_e3o_optimized_run_does_not_make_a_clean_file_green` | behavior-red | failed | 是 |
| 17 | `tests/test_status.py::TestPassValidityChain::test_e3x_runxfail_pass_does_not_retire_a_known_red` | behavior-red | failed | 是 |
| 18 | `tests/test_status.py::TestPassValidityChain::test_e3w_warning_filter_pass_does_not_retire_a_known_red` | behavior-red | failed | 是 |
| 19 | `tests/test_redlight.py::TestPassValidityCoverage::test_e3d_the_fixed_command_with_a_plain_interpreter_is_full_coverage` | regression-lock | passed | 是 |
| 20 | `tests/test_redlight.py::TestPassValidityCoverage::test_e3a_plain_assert_mode_on_a_plain_interpreter_is_still_full_coverage` | regression-lock | passed | 是 |
| 21 | `tests/test_redlight.py::TestProducerPathNormalization::test_e3p_a_config_file_option_never_persists_a_path[win-abs]` | regression-lock(本機 Windows) | passed | 是 |
| 22 | `tests/test_redlight.py::TestProducerPathNormalization::test_e3p_a_config_file_option_never_persists_a_path[posix-abs]` | regression-lock(本機 Windows) | passed | 是 |
| 23 | `tests/test_redlight.py::TestProducerPathNormalization::test_e3p_an_override_value_never_persists_a_path[win-abs]` | regression-lock(本機 Windows) | passed | 是 |
| 24 | `tests/test_redlight.py::TestProducerPathNormalization::test_e3p_an_override_value_never_persists_a_path[posix-abs]` | regression-lock(本機 Windows) | passed | 是 |
| 25 | `tests/test_redlight.py::TestProducerPathNormalization::test_e3p_non_path_override_values_are_persisted_verbatim` | regression-lock | passed | 是 |
| 26 | `tests/test_redlight.py::TestProducerPathNormalization::test_e3p_non_path_plugin_names_are_persisted_verbatim` | regression-lock | passed | 是 |
| 27 | `tests/test_redlight.py::TestProducerPathNormalization::test_e3p_a_root_relative_config_file_option_is_persisted_as_given` | regression-lock | passed | 是 |
| 28 | `tests/test_status.py::TestPassValidityLocks::test_e3d_the_fixed_command_full_run_still_retires_the_red` | regression-lock | passed | 是 |

## 4. 驗收(在 S3e-1 上只跑一次)

```
$ date -u +%Y-%m-%dT%H:%M:%SZ
2026-10-03T12:04:13Z
$ python -X utf8 -m pytest -q
```

- 退出碼:**1**(工具回報 `Exit code 1`)。
- **終端輸出的保存範圍**:工具回傳的輸出被截斷。中段被省略(工具標示 `[18570 characters truncated]`),尾端停在 `test_e3p_an_override_value_never_persists_a_path[rel-escape]` 那一段失敗說明的中間。`-ra` 的 short test summary 與最後的摘要行**沒有出現在工具回傳內容裡**。
  - 依規定不得重跑,所以**摘要行原文缺失**。
  - 以下數字改由第 5 節的帳本(producer 在同一次 session 寫入的紀錄)與第 6 節的 status 輸出取得。
- 輸出中保存下來的進度列(逐字,原檔無使用者路徑):

```
........................................................................ [  3%]
........................................................................ [  7%]
........................................................................ [ 10%]
........................................................................ [ 14%]
..............................................xxx....................... [ 17%]
........................................................................ [ 21%]
........................................................................ [ 24%]
........................................................................ [ 28%]
............sss......................................................... [ 32%]
........................................................................ [ 35%]
........................................................................ [ 39%]
........................................................................ [ 42%]
........................................................................ [ 46%]
........................................................................ [ 49%]
........................................................................ [ 53%]
........................................................................ [ 57%]
........................................................................ [ 60%]
........................................................................ [ 64%]
........................................................................ [ 67%]
........................................................................ [ 71%]
................................................................FFFFFFFF [ 74%]
F..FFF..F..F............................................................ [ 78%]
........................................................................ [ 81%]
........................................................................ [ 85%]
........................................................................ [ 89%]
..................................................................FFFF.. [ 92%]
........................................................................ [ 96%]
........................................................................ [ 99%]
.....                                                                    [100%]
```

- 進度列的計數:`F` 共 18 個(8 + 6 + 4)、`x` 3 個、`s` 3 個。
- 輸出中保存下來的失敗原因片段(只列工具回傳內容裡完整可見者;本機路徑已遮成 `<user>`):
  - `test_e3o_an_optimized_interpreter_is_not_full_coverage[1]`、`[2]`:`tests\test_redlight.py:1649: AssertionError` —— `assert 'true' != 'true'`。對照組那一行(`assert control == "true"`)已通過,失敗在破壞組 ⇒ 紅的理由是「TARGET 不看 optimize」。
  - `test_e3p_blocked_plugin_names_never_persist_a_path[rel-escape]`:`tests\test_redlight.py:1784: AssertionError`。持久化行含 `"blocked": ["../../e3p-user/x.py", "pytest_../../e3p-user/x.py"]`,`plugins[].name` 也含這兩個原樣字串。
  - `test_e3p_a_config_file_option_never_persists_a_path[rel-escape]`:`tests\test_redlight.py:1799: AssertionError`。持久化行含 `"inifilename": "../../e3p-user/alt.toml"`。
  - 其他各支的失敗說明落在被截斷的範圍內,沒有保存。

### 失敗清單(取自帳本第 18 行 `outcomes` 中值為 `"failed"` 的鍵;Grep `-o` 原文)

```
18:"tests/test_redlight.py::TestPassValidityCoverage::test_e3o_an_optimized_interpreter_is_not_full_coverage[1]": "failed"
18:"tests/test_redlight.py::TestPassValidityCoverage::test_e3o_an_optimized_interpreter_is_not_full_coverage[2]": "failed"
18:"tests/test_redlight.py::TestPassValidityCoverage::test_e3o_a_missing_optimize_fact_is_not_full_coverage": "failed"
18:"tests/test_redlight.py::TestPassValidityCoverage::test_e3x_runxfail_alone_is_not_full_coverage": "failed"
18:"tests/test_redlight.py::TestPassValidityCoverage::test_e3w_a_pytest_warning_filter_alone_is_not_full_coverage": "failed"
18:"tests/test_redlight.py::TestPassValidityCoverage::test_e3t_trace_alone_is_not_full_coverage": "failed"
18:"tests/test_redlight.py::TestPassValidityCoverage::test_e3v_an_unrecognized_python_version_is_not_full_coverage": "failed"
18:"tests/test_redlight.py::TestPassValidityCoverage::test_e3o_the_producer_records_the_interpreter_optimize_flag": "failed"
18:"tests/test_redlight.py::TestPassValidityCoverage::test_e3x_the_producer_records_runxfail_and_pythonwarnings": "failed"
18:"tests/test_redlight.py::TestProducerPathNormalization::test_e3p_blocked_plugin_names_never_persist_a_path[win-abs]": "failed"
18:"tests/test_redlight.py::TestProducerPathNormalization::test_e3p_blocked_plugin_names_never_persist_a_path[posix-abs]": "failed"
18:"tests/test_redlight.py::TestProducerPathNormalization::test_e3p_blocked_plugin_names_never_persist_a_path[rel-escape]": "failed"
18:"tests/test_redlight.py::TestProducerPathNormalization::test_e3p_a_config_file_option_never_persists_a_path[rel-escape]": "failed"
18:"tests/test_redlight.py::TestProducerPathNormalization::test_e3p_an_override_value_never_persists_a_path[rel-escape]": "failed"
18:"tests/test_status.py::TestPassValidityChain::test_e3o_optimized_pass_does_not_retire_a_known_red": "failed"
18:"tests/test_status.py::TestPassValidityChain::test_e3o_optimized_run_does_not_make_a_clean_file_green": "failed"
18:"tests/test_status.py::TestPassValidityChain::test_e3x_runxfail_pass_does_not_retire_a_known_red": "failed"
18:"tests/test_status.py::TestPassValidityChain::test_e3w_warning_filter_pass_does_not_retire_a_known_red": "failed"
```

- 第 18 行值為 `"failed"` 的鍵**恰好這 18 個**,與〈三十五〉35.3 的預期紅集合逐一相同。Grep 的 pattern 為 `"tests/[^"]+": "failed"`,對全帳本執行,第 18 行的命中只有以上 18 筆。
- 3e 新增 28 支在第 18 行的值:18 支 `failed`、10 支 `passed`,與預期集合逐一相同(第 3 節)。
- 同一行:`"ticket_id": "145", "exit_code": 1`;`xfail` 3 筆(`tests/test_g1_guard.py::TestLevelTwoIsUnchanged::…[/srv/x]`、`[/data/x]`、`[/backup/x]`)、`skipped` 3 筆(`tests/test_gate.py::TestSkillMirrorSingleRule::…` 三支)。
- **以帳本與 status 重建的計數**:collected 2021 / passed 1997 / failed 18 / skipped 3 / xfail 3(2021 − 1997 − 18 − 3 = 3)。這等於預期的 `18 failed, 1997 passed, 3 skipped, 3 xfailed`(collected 2021),**但不是 pytest 摘要行的原文**。

## 5. 帳本 H5 → H6 只追加

```
$ git status --porcelain
(無輸出)
$ wc -c -l .dev/test-runs.jsonl .dev/test-sessions.jsonl
   2595  697745 .dev/test-runs.jsonl
     18 5599744 .dev/test-sessions.jsonl
   2613 6297489 total
$ head -c 684893 .dev/test-runs.jsonl > <session scratch>/r.bin
$ head -c 4891233 .dev/test-sessions.jsonl > <session scratch>/s.bin
$ sha256sum <session scratch>/r.bin
23f397d47c76bc6985daa73dd99afe73c84b53dd2220a4305ae64cb8b1e4086c *<session scratch>/r.bin
$ sha256sum <session scratch>/s.bin
7463a45257c893ec9079f0f655782bfab11855eab9fcd5f93b314e5d60beb70c *<session scratch>/s.bin
$ sha256sum .dev/test-runs.jsonl
a6ff861ecbd0963f5fb2c8bc5fb745f1b87c74d338711832a913218dec999f7e *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
e78a696887cfe660a7d2ea382ddea1109b73865255ea38ac2fbf7c44894e42f6 *.dev/test-sessions.jsonl
```

(scratch 的絕對路徑以 `<session scratch>` 代替 —— 這四行經遮罩,不是逐字原文。)

| 點 | test-runs | test-sessions |
|---|---|---|
| H5(驗收前) | 684893 bytes / 2549 行 / `23f397d47c76bc6985daa73dd99afe73c84b53dd2220a4305ae64cb8b1e4086c` | 4891233 bytes / 17 行 / `7463a45257c893ec9079f0f655782bfab11855eab9fcd5f93b314e5d60beb70c` |
| H6(驗收後) | 697745 bytes / 2595 行 / `a6ff861ecbd0963f5fb2c8bc5fb745f1b87c74d338711832a913218dec999f7e` | 5599744 bytes / 18 行 / `e78a696887cfe660a7d2ea382ddea1109b73865255ea38ac2fbf7c44894e42f6` |

⇒ 兩本前段都等於 H5。test-runs +46 行(= 測試檔數)、test-sessions +1 行。

## 6. status.py(驗收後)

`python .claude/portable/status.py --root .` 的 Evidence 與 Derived 兩段(逐字):

```
=== Evidence ===
test-runs: 本票 red 2 / green 44 / run 事實未知 0 / orphaned 0 / schema 不合格 run 0;最後一筆 tests/test_verify_gates.py=green @ 2026-10-03T12:06:48.616989+00:00;最近一次 run:B(exit 1;collected 2021 / deselected 0 / passed 1997 / failed 18 / skipped 3)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl)
intercepts (當月): 5 筆  (source: .dev/intercepts-2026-10.jsonl)
intercepts (最新存在月): 2026-10 5 筆;末筆 R7@2026-10-03T00:29:01.715824+00:00  (source: .dev/intercepts-2026-10.jsonl)
exemptions: 總 281 筆;granted 240 筆;blocked 1 筆;未記錄(無此欄)40 筆;最後一筆 2026-09-24T08:17:49.073745+00:00  (source: .dev/gate-exemptions.jsonl)
provenance: 未記錄(上游無此檔屬正常)  (source: .dev/provenance.jsonl)
report: 2026-10-03T004050Z-ticket145-station5d-0.md;HEAD 2026-10-03T08:04:04-04:00;回報後 3 筆  (source: .dev/reports/)

=== Derived ===
src write allowed in tickets: no  (source: gate.stage_allows_src_write() <- .agents/pipeline-stages.yaml)
tests red under ticket 145: tests/test_redlight.py / tests/test_status.py  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests green under ticket 145: tests/test_adr_numbering.py / tests/test_adr_numbers_resolve_upstream.py / tests/test_apply_patches.py / tests/test_bash_write.py / tests/test_bootstrap.py / tests/test_canon_section.py / tests/test_ci_workflow.py / tests/test_cjk_git_paths.py / tests/test_claude_md.py / tests/test_declared_in_is_an_identity.py / tests/test_dependency_ceiling.py / tests/test_edit_result.py / tests/test_evidence_isolation.py / tests/test_friction_heading.py / tests/test_g1_guard.py / tests/test_g1_verify.py / tests/test_gate.py / tests/test_gate_boundaries.py / tests/test_gitlink_downstream_cycle.py / tests/test_install.py / tests/test_intercepts.py / tests/test_known_items_regression.py / tests/test_leak_scan.py / tests/test_ledger_verify.py / tests/test_line_ending_parity.py / tests/test_manifest.py / tests/test_mcp_server.py / tests/test_non_source_list_parity.py / tests/test_portable_output_encoding.py / tests/test_r5_mounts.py / tests/test_research_stage.py / tests/test_scanner.py / tests/test_shadow.py / tests/test_shadow_review.py / tests/test_source_hygiene.py / tests/test_stage_defs_source.py / tests/test_stage_naming.py / tests/test_sync.py / tests/test_ticket_dirs_are_md_only.py / tests/test_ticket_lookup.py / tests/test_ticket_path_parity.py / tests/test_upstream_manifest.py / tests/test_user_layer.py / tests/test_verify_gates.py  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests green (run 事實未知) under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests orphaned under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
rules defined: R1 R2 R3 R4 R5 R6 R7 R8 R9  (source: gate.rule_codes())
```

- red 只有 `tests/test_redlight.py` 與 `tests/test_status.py`;最近一次 run 為 B。**與預期相符。**
- intercepts 由 4d 報告時的 4 筆變為 5 筆,末筆 R7 在 `2026-10-03T00:29:01Z`。本輪(S3e-1)期間沒有任何指令被閘門擋下;這一筆不是本輪產生的。是哪一次操作產生的,本報告沒有查。

## 7. 尚未證明

1. **pytest 摘要行原文缺失**(第 4 節):計數與失敗清單由帳本第 18 行與 status 重建,不是 pytest 終端輸出的原文。
2. 18 支 behavior-red 中,只有 4 支的失敗說明在工具輸出內完整可見(第 4 節);其餘 14 支「紅的理由是對的」,只由失敗清單與各支 docstring 的推演支撐,沒有逐支看到 assertion 訊息。
3. `[win-abs]` / `[posix-abs]` 那 4 支的綠是本機 Windows 的結果;在 POSIX(CI)上 `[win-abs]` 預期會紅(S5d-F3 的跨平台缺口),未在 POSIX 實測。
4. 注入方式(`monkeypatch.setattr(c, "sys", …, raising=False)`)要求 4e 的 producer 經 conftest **模組層的 `sys`** 讀 `sys.flags.optimize` 與 `sys.version_info`。這是本刀定稿的介面細節(test_redlight 3e 段開頭註解);若 4e 改從其他來源讀(例如 `platform`),E3v-1 / E3o-3 會持續紅。
5. 觀察(未查原因):status 的 Derived 顯示 `src write allowed in tickets: no`,但本輪在 `tickets` 站對 `tests/` 的寫入沒有被擋下。tests/ 是否屬 R2 的原始碼範圍,本輪沒有查。
6. CLEAN / REAL 層未證明。
