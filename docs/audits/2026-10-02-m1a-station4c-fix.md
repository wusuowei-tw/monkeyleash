# 票 145(M1-a)Station 4c 修正證據

## 【給裁決者】

1. 4c 依〈二十三〉合約實作完成(S4c-1 `02a5e28`),固定全套只跑一次:exit 0、`1967 passed`,3c 的 16 支紅燈全部轉綠。
2. (a) 固定全套 exit 0、failed 0:**成立**。(b) 3c 的 16 支全部轉綠:**成立**。
3. (c) completeness 合格、plugins 沒有 other、沒有絕對路徑:**成立**(依 Jeff 裁決 1 的三類欄位邊界;見第 8 節)。
4. (d) 帳本 H2 → H3 只追加:**成立**(前段雜湊相符)。
5. 實作偏離一處(pre_narrowing 也記子 collector 的 Item),已獲裁決接受;多層累積的正確性列為 Station 5c 必答題。

---

## 1. 前置值

```
$ git rev-list --left-right --count origin/master...HEAD
0	22
$ git rev-parse HEAD
4ff0310fa9f8fee1265847784f0a00484a08ad30
$ git status --porcelain
(無輸出)
$ cat .dev/pipeline.json
{
  "current_stage": "implement",
  "feature": "framework-updates",
  "ticket_id": "145",
  "updated": "2026-10-02"
}
$ git ls-files *conftest.py
tests/conftest.py
$ wc -c -l .dev/test-runs.jsonl .dev/test-sessions.jsonl
   2411  649789 .dev/test-runs.jsonl
     14 2803361 .dev/test-sessions.jsonl
   2425 3453150 total
$ sha256sum .dev/test-runs.jsonl
36bf61df9c2a4b68d109f419d2020184e101edbd8de8131723c085b86f8f2544 *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
0ef187e02160759dba4912650d7baa0d3642a3b1902e91add71a20f97e477c45 *.dev/test-sessions.jsonl
```

tracked conftest inventory:僅 `tests/conftest.py`。

## 2. 實作摘要(S4c-1 `02a5e28adf5aee11a43d5a1063504f01beb1d67f`)

`git diff --cached --numstat`:

```
174	6	.claude/hooks/redlight.py
77	3	tests/conftest.py
24	2	tests/test_redlight.py
23	4	tests/test_status.py
```

**`.claude/portable/status.py` 未改**:退紅 / green / orphan 全部經 `rl.file_coverage()`(`status.py:456`),新規則自動生效。

### 2.1 producer(`tests/conftest.py`,行號以 `02a5e28` 為準)

- `:197-202` `_run_outcome`:skipped + `wasxfail` ⇒ `"xfail"`;call passed + `wasxfail` ⇒ `"xpass"`(不再籠統記 `"other"`);passed / failed / skipped 語意不變。
- `:290-291` 模組層 `_pre_narrowing` / `_pre_narrowing_broken`(存在 `_run` 之外:既有 driver 會清空 `_run` 的每個值)。
- `:294-305` `@pytest.hookimpl(wrapper=True, trylast=True) pytest_make_collect_report`:`yield` 之後當下以 `list(...)` 複製 report 裡每個 `pytest.Item` 的 nodeid,以測試檔為 key 累積。出錯 ⇒ `_pre_narrowing_broken`。
- `:308-319` `_plain`(非 JSON 原生型別記型別名)、`_flag`(shouldstop / shouldfail → bool;屬性不存在 ⇒ None)。
- `:322-` `_completeness_of(session)`:options(`redlight.COMPLETENESS_OPTIONS`,屬性不存在記 null)、`cacheprovider_blocked`(`pm.is_blocked("cacheprovider")`)、shouldstop / shouldfail、pre_narrowing、plugins(`redlight.classify_plugins`)。任何一步出錯 ⇒ None。
- `:249-253` `pytest_sessionfinish`:`record_session` 簽名有 `completeness` 才傳(舊版 redlight 照舊不傳);逐檔 8 欄紀錄的寫入在它之前,不受影響。

### 2.2 consumer(`.claude/hooks/redlight.py`,行號以 `02a5e28` 為準)

- `:220-249` `record_session` 新增 `completeness`(不是 dict ⇒ 記 None)。
- `:289` `OUTCOME_VALUES` 加 `xfail` / `xpass`(保留 `other`,只為讀得動 4c 之前的 session)。
- `:352-354` `validate_session`:completeness 非 null 時須為 dict;沒有這個欄位的舊 session 仍合格。
- `:439` `file_coverage`:位置參數涵蓋該檔之後交給 `_completeness_verdict`;固定指令沒有特殊分支。
- `:457-469` 白名單常數:`COMPLETENESS_OPTIONS`、`PLUGIN_KINDS`、`SUPPORTED_PLUGIN_KINDS`、`BUILTIN_MODULE`、`ROOT_CONFTEST = "tests/conftest.py"`、`KNOWN_DISTS = ("anyio",)`、`OUTSIDE`、`EXECUTED_OUTCOMES`。
- `:504-` `classify_plugins`:依序判 ① plugin **物件**出現在 distinfo 配對中 ⇒ dist 名稱在已知清單為 known_dist、否則 other;② 名稱為絕對路徑 ⇒ root 相對路徑恰為 `tests/conftest.py` 為 root_conftest、否則 other;③ 定義模組為 `_pytest` / `_pytest.*` ⇒ builtin;④ 其他 ⇒ other。路徑型名稱只記 root 相對路徑,root 以外記 `<outside>`。
- `:539-` `_completeness_problems`:〈二十三〉7 (i) 的型別檢查。
- `:562-` `_completeness_verdict`:(i) 缺欄 / 型別錯 ⇒ unknown;(vii) 有 other ⇒ unknown;(ii) lf / stepwise / stepwise_skip 生效(cacheprovider 未封鎖時)⇒ false;(iii) maxfail 非 None/0、collectonly / setuponly / setupplan ⇒ unknown;(iv) shouldstop / shouldfail ⇒ unknown;(v) pre_narrowing 集合 != 該檔 collected ⇒ false;(vi) 有 selected 身分不在 `EXECUTED_OUTCOMES` ⇒ unknown;全部成立 ⇒ true。

## 3. 實作偏離(已獲裁決 2 接受)

指令寫「只對 File collector」。實作改為記錄**每個 collector report 裡的 `pytest.Item`**(File 的直接子項,以及 Class 等子 collector 的子項)。
理由:class 內的測試不在 File 的 report 裡,只記 File 的話 class 型測試檔的全集永遠對不上 collected;`--lf` 只在 File 層過濾(`_pytest/cacheprovider.py:282-290`),子 collector 不受影響。
佐證:真實固定全套 46 檔全部以同一套一般規則判 `"true"`(第 9 節 status green 46)。

## 4. 授權補件 hunk(〈二十三〉裁決 5;assertion / docstring / test identity 未改)

| hunk | 所屬測試 |
|---|---|
| `@@ -529 +529,9 @@` | `tests/test_redlight.py::TestFileCoverage::test_b1c_a_file_argument_without_deselection_is_full_coverage` |
| `@@ -537 +545,9 @@` | `tests/test_redlight.py::TestFileCoverage::test_b1d_a_parent_directory_argument_is_full_coverage` |
| `@@ -626,0 +643,6 @@` | `tests/test_redlight.py::TestFixedCommandCoverage::test_b10_the_fixed_command_without_positional_args_is_full_coverage` |
| `@@ -578 +578,9 @@` | `tests/test_status.py::TestTestsUnderTicketUsesTheLatestRecordPerFile::test_a_file_that_went_red_then_green_counts_as_green` |
| `@@ -1331 +1339,12 @@` | `tests/test_status.py::TestOrphans::test_a_renamed_red_test_is_orphaned_not_green` |
| `@@ -1700,2 +1719,2 @@` | `tests/test_status.py::TestChainRegressionLocks::test_l3_a_full_directory_run_retires_the_red` |

b1c / b1d:原本的 `got = self._coverage_after(...)` 一行換成送出縮小前全集與白名單事實的驅動;b10:在既有 session 上補 option / pluginmanager / shouldstop / shouldfail 與縮小前全集;546 / ODC-2:`record_session` 尾端補 `completeness=`;L3:`_chain_drive(...)` 換成 `_s_drive(...)`。3c 新增的 21 支未改。

`git diff --cached --check`:無輸出。commit 輸出:

```
[master 02a5e28] fix(145): M1-a Station 4c —— 選擇/執行完整性事實與 plugin 邊界(coverage authority)
 4 files changed, 298 insertions(+), 15 deletions(-)
```

## 5. 驗收(在 S4c-1 上,只跑一次)

```
$ date -u +%Y-%m-%dT%H:%M:%SZ
2026-10-02T20:55:13Z
$ python -X utf8 -m pytest -q
...
=========================== short test summary info ===========================
SKIPPED [1] tests\test_gate.py:451: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:459: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:473: 此環境無法建立 symlink
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/srv/x] - …
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/data/x] - …
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/backup/x] - …
1967 passed, 3 skipped, 3 xfailed in 150.21s (0:02:30)
```

(XFAIL 三行的說明文字以 `…` 截斷 —— 本區塊不是逐字全文;SKIPPED 與摘要行逐字。exit code 0;輸出沒有任何 FAILED / ERROR 行;tool 輸出沒有截斷。)

失敗清單:無。3c 的 16 支、5 支 regression-lock、六支授權測試、其他全部既有測試都通過(1967 = 1951 + 16)。

## 6. 帳本 H2 → H3 只追加

| 點 | test-runs | test-sessions |
|---|---|---|
| H2(驗收前) | 649789 bytes / 2411 行 / `36bf61df9c2a4b68d109f419d2020184e101edbd8de8131723c085b86f8f2544` | 2803361 bytes / 14 行 / `0ef187e02160759dba4912650d7baa0d3642a3b1902e91add71a20f97e477c45` |
| H3(驗收後) | 661092 bytes / 2457 行 / `352e7d2653301e11d16494c100d67231e47efcabe2a7a047a297402046972172` | 3494564 bytes / 15 行 / `b48ee090beb214f264476c2efc827b6d244cb6b70cf0d669adffd6d3ce871870` |

```
$ head -c 649789 .dev/test-runs.jsonl > <session scratch>/r.bin
$ sha256sum <session scratch>/r.bin
36bf61df9c2a4b68d109f419d2020184e101edbd8de8131723c085b86f8f2544 *<session scratch>/r.bin
$ head -c 2803361 .dev/test-sessions.jsonl > <session scratch>/s.bin
$ sha256sum <session scratch>/s.bin
0ef187e02160759dba4912650d7baa0d3642a3b1902e91add71a20f97e477c45 *<session scratch>/s.bin
```

(scratch 絕對路徑以 `<session scratch>` 代替 —— 這四行經遮罩,不是逐字原文。)
⇒ 兩本前段都等於 H2;test-runs +46 行(= 測試檔數)、test-sessions +1 行。跑完 `git status --porcelain` 無輸出。

## 7. 真實 session(`.dev/test-sessions.jsonl` 第 15 行)的 completeness

該行約 691 KB,以 Grep `-o` 取片段(不是整行 Read):

```
15:"options": {"lf": false, "last_failed_no_failures": "all", "stepwise": false, "stepwise_skip": false, "maxfail": null, "collectonly": false, "setuponly": false, "setupplan": false}
15:"cacheprovider_blocked": false
15:"shouldstop": false
15:"shouldfail": false
```

- `pre_narrowing`:46 個檔(Grep `"tests/[^":]+\.py": \[` 命中 46 個,全部在第 15 行)。
- `plugins`:43 項,builtin 41、known_dist 1、root_conftest 1;全帳本 Grep `"kind": "other"`:0 筆。

| kind | name |
|---|---|
| builtin | `2082416878800`(數字名稱)、pytestconfig、mark、main、runner、fixtures、helpconfig、python、terminal、debugging、unittest、capture、skipping、legacypath、tmpdir、monkeypatch、recwarn、pastebin、assertion、junitxml、doctest、cacheprovider、setuponly、setupplan、stepwise、unraisableexception、threadexception、warnings、logging、reports、faulthandler、subtests、capturemanager、session、lfplugin、nfplugin、legacypath-tmpdir、terminalreporter、terminalprogress、logging-plugin、funcmanage |
| known_dist | anyio |
| root_conftest | tests/conftest.py |

## 8. 絕對路徑檢查與裁決 1(三類欄位)

- Grep `[A-Za-z]:(\\\\|/)|Users`:命中第 1、6、11–14、15 行;第 1、6、11–14 行每行 2 組、第 15 行 3 組,每組 53 個片段。
  片段全部位於測試身分的 parametrize ID(例:`…test_no_secrets_are_referenced[C://projects//agent-gates//.github//workflo…`、`…[rm C://Users//fake//thing.py-…`)。
  第 15 行多出的一組位於 `completeness.pre_narrowing`(由組數推得;plugins 片段已確認不含路徑)。
- 全帳本 Grep 本機使用者名稱:0 筆。
- 裁決助手獨立核對:類似絕對路徑的字串只出現在 collected、outcomes 的鍵、completeness.pre_narrowing 三處,共 29 個身分;pre_narrowing 中的這些身分全部也在 collected 中;plugins 與 invocation 不含;本次 invocation.args 為相對的 `tests`。
- **裁決 1**:(1) producer 自身產生的 path-valued metadata(如 `completeness.plugins[].name`)不得有絕對路徑 —— 成立;(2) pytest 提供、作為 identity 逐字保存的 nodeid 不因本條改寫;(3) invocation.args 依〈十九〉的正規化 —— 不屬本條。⇒ **(c) 成立**。(2) 類原始事實本身帶本機敏感路徑的問題列入 M1-a 結案後追蹤票。

## 9. status.py(驗收後)

`python .claude/portable/status.py --root .` 的 Evidence 與 Derived 兩段(逐字):

```
=== Evidence ===
test-runs: 本票 red 0 / green 46 / run 事實未知 0 / orphaned 0 / schema 不合格 run 0;最後一筆 tests/test_verify_gates.py=green @ 2026-10-02T20:57:42.829998+00:00;最近一次 run:A(exit 0;collected 1973 / deselected 0 / passed 1967 / failed 0 / skipped 3)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl)
intercepts (當月): 2 筆  (source: .dev/intercepts-2026-10.jsonl)
intercepts (最新存在月): 2026-10 2 筆;末筆 R7@2026-10-02T18:03:07.370596+00:00  (source: .dev/intercepts-2026-10.jsonl)
exemptions: 總 281 筆;granted 240 筆;blocked 1 筆;未記錄(無此欄)40 筆;最後一筆 2026-09-24T08:17:49.073745+00:00  (source: .dev/gate-exemptions.jsonl)
provenance: 未記錄(上游無此檔屬正常)  (source: .dev/provenance.jsonl)
report: 2026-10-02T174245Z-ticket145-station5b-0.md;HEAD 2026-10-02T16:55:06-04:00;回報後 6 筆  (source: .dev/reports/)

=== Derived ===
src write allowed in implement: yes  (source: gate.stage_allows_src_write() <- .agents/pipeline-stages.yaml)
tests red under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests green under ticket 145: tests/test_adr_numbering.py / tests/test_adr_numbers_resolve_upstream.py / tests/test_apply_patches.py / tests/test_bash_write.py / tests/test_bootstrap.py / tests/test_canon_section.py / tests/test_ci_workflow.py / tests/test_cjk_git_paths.py / tests/test_claude_md.py / tests/test_declared_in_is_an_identity.py / tests/test_dependency_ceiling.py / tests/test_edit_result.py / tests/test_evidence_isolation.py / tests/test_friction_heading.py / tests/test_g1_guard.py / tests/test_g1_verify.py / tests/test_gate.py / tests/test_gate_boundaries.py / tests/test_gitlink_downstream_cycle.py / tests/test_install.py / tests/test_intercepts.py / tests/test_known_items_regression.py / tests/test_leak_scan.py / tests/test_ledger_verify.py / tests/test_line_ending_parity.py / tests/test_manifest.py / tests/test_mcp_server.py / tests/test_non_source_list_parity.py / tests/test_portable_output_encoding.py / tests/test_r5_mounts.py / tests/test_redlight.py / tests/test_research_stage.py / tests/test_scanner.py / tests/test_shadow.py / tests/test_shadow_review.py / tests/test_source_hygiene.py / tests/test_stage_defs_source.py / tests/test_stage_naming.py / tests/test_status.py / tests/test_sync.py / tests/test_ticket_dirs_are_md_only.py / tests/test_ticket_lookup.py / tests/test_ticket_path_parity.py / tests/test_upstream_manifest.py / tests/test_user_layer.py / tests/test_verify_gates.py  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests green (run 事實未知) under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests orphaned under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
rules defined: R1 R2 R3 R4 R5 R6 R7 R8 R9  (source: gate.rule_codes())
```

## 10. 四項完成判定

| 項 | 判定 | 依據 |
|---|---|---|
| (a) 固定全套 exit 0、failed 0 | **成立** | 第 5 節摘要行原文 |
| (b) 3c 的 16 支全部轉綠 | **成立** | 失敗集合為空;status red 0 |
| (c) completeness 合格、plugins 無 other、無絕對路徑 | **成立** | 第 7、8 節;依裁決 1 的欄位邊界 |
| (d) 帳本 H2 → H3 只追加 | **成立** | 第 6 節前段雜湊相符 |

## 11. 尚未證明

1. plugin completeness 以 producer 在 sessionfinish 時觀察到的已註冊 plugin 集合為依據;**某 plugin 在 session 中途自行 unregister、且已改過 collection** 這類非標準生命週期未證明。標準的 `-p`、`PYTEST_PLUGINS`、conftest、entry-point dist 已由〈二十三〉合約與 3c 測試涵蓋。
2. 未被 Git 追蹤或被 ignore 的 conftest 不在第 0 步盤點內;若真實執行載入它,會被分類為 other ⇒ 驗收 fail-closed。
3. `_pre_narrowing` 是模組層狀態,同一程序內多次 `pytest.main()` 會累積(集合只會多不會少 ⇒ 與 collected 不等 ⇒ false),屬 fail-closed 方向,未另驗。
4. 多層 collector 累積的正確性(裁決 2 的 Station 5c 必答題:重複、巢狀 class、parametrize、hook 順序;`--lf` 的 File 層縮小是否確實發生在本 snapshot 之後)只由真實固定全套佐證,未逐案證明。
5. CLEAN / REAL 層未證明。
