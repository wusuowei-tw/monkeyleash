# 票 145(M1-a)Station 4e 修正證據 —— pass 有效性 (xiv)–(xviii) 與 producer 路徑正規化 F3-甲

## 【給裁決者】

1. 照〈三十五〉做了實作:判定那一側(redlight.py)加上五個新條件,紀錄那一側(conftest.py)開始記錄對應的事實,路徑遮罩改成不分平台都能認出的規則;測試只照授權動了三個預設值與兩支測試的資料(S4e-1 `0139a7e`)。
2. 在 S4e-1 上只跑一次固定全套:`2015 passed, 3 skipped, 3 xfailed`,exit 0。3e 的 18 支紅燈全部轉綠,10 支 regression-lock 仍綠。
3. 真實執行留下的新事實全部合格(未最佳化、Python 3.11、三個選項都是預設值);帳本只有追加;status 顯示 46 個測試檔全綠、沒有紅。
4. 要你決定:是否交付 Station 5e 獨立審查(須在全新對話執行)。
5. 不決定的話:票停在「4e 修正完成,待 5e 審查」。

---

## 【給裁決助手】

### 0. 前置(S4e-1 之前,原文)

```
$ git status --porcelain
(無輸出)
$ git rev-parse HEAD
1c771c400c620a03135971063c37b89d4d237c74
$ git rev-list --left-right --count origin/master...HEAD
0	36
$ cat .dev/pipeline.json
{
  "current_stage": "implement",
  "feature": "framework-updates",
  "ticket_id": "145",
  "updated": "2026-10-02"
}
$ wc -c -l .dev/test-runs.jsonl .dev/test-sessions.jsonl
   2595  697745 .dev/test-runs.jsonl
     18 5599744 .dev/test-sessions.jsonl
   2613 6297489 total
$ sha256sum .dev/test-runs.jsonl
a6ff861ecbd0963f5fb2c8bc5fb745f1b87c74d338711832a913218dec999f7e *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
e78a696887cfe660a7d2ea382ddea1109b73865255ea38ac2fbf7c44894e42f6 *.dev/test-sessions.jsonl
```

- S3E2 = `1c771c400c620a03135971063c37b89d4d237c74`。S3e-1 與 S3E2 已回填進票 145〈三十六〉。
- 動工前以 Grep 查帳本第 15–18 行全部 plugin 註冊名:只有識別字形狀的名稱與 `tests/conftest.py`。因此名稱欄位規則(`[A-Za-z0-9_.-]+` 原樣)不會改變真實 session 的落帳。

### 1. 實作摘要(S4e-1)

**`.claude/hooks/redlight.py`**
- import 新增 `ntpath`、`posixpath`、`re`。
- `COMPLETENESS_OPTIONS` 加 `runxfail`、`pythonwarnings`、`trace`。
- 新常數:`NON_IDENTIFIER = "<non-identifier>"`、`KNOWN_PYTHON_VERSIONS = ("3.11",)`。
- F3-甲:
  - `_is_abs_path`(`posixpath.isabs` 或 `ntpath.isabs` 或磁碟代號開頭)。
  - `_root_relative(value, root, base)`:相對路徑先以 base 解析;越出 root、跨磁碟、或「他平台才算絕對」⇒ `<outside>`。
  - `_plugin_name`:路徑名 ⇒ `_root_relative`;`[A-Za-z0-9_.-]+` 原樣;其他 `<non-identifier>`。
  - `classify_plugins` 以原始名稱判 kind(`is_path = _is_abs_path(name)`;root_conftest 判定用 `_plugin_path_name`),落帳字串用 `_plugin_name`。
  - `blocked_plugins(name_plugins, root=None)`:給 root 時正規化落帳字串。
  - `normalize_config_path(value, root, base=None)` 一律走 `_root_relative`。
  - `normalize_overrides(values, root, base=None)`:key 原樣;value 只在絕對或越出 root 時正規化。
  - `_normalize_arg` 對他平台的絕對路徑回 None(〈十九〉規則:root 以外不落帳)。
- `_completeness_problems` 加驗:
  - `optimize`:`type(...) is int`(不含 bool)。
  - `python_version`:字串。
  - `options.runxfail` / `options.trace`:bool。
  - `options.pythonwarnings`:None 或字串 list。
- `_completeness_verdict` 在 (xi) 之後、(ii) 之前加:
  - `optimize != 0` ⇒ unknown
  - 版本不在清單 ⇒ unknown
  - `runxfail` / `trace` 不是 False ⇒ unknown
  - `pythonwarnings not in (None, [])` ⇒ unknown
  - 唯一 `"true"` 出口不變(`:820`)。
- 未改:`validate_session`;未新增 assertmode 條件;未帶入 `sys.warnoptions`。

**`tests/conftest.py`(producer)**
- 模組層 `import sys`。
- `_optimize_flag()`、`_python_version()` 在 sessionfinish 當下經模組層 `sys` 讀(不在 import 時快取,不用 `platform`)。
- completeness 新增 `optimize`、`python_version`。
- `_plain` 把字串 list 原樣記成 list。
- `blocked` / `override_ini` / `inifilename` 傳入 `_ROOT` 與 `invocation_params.dir`。

**未改**:`.claude/portable/status.py`。

```
$ git diff --stat HEAD~1 HEAD
 .claude/hooks/redlight.py                          | 137 +++++++++++++++++----
 .../145-m1a-run-level-evidence-correctness.md      |  67 +++++++++-
 tests/conftest.py                                  |  40 +++++-
 tests/test_redlight.py                             |   1 +
 tests/test_status.py                               |  14 ++-
 5 files changed, 222 insertions(+), 37 deletions(-)
```

### 2. commit 前靜態證明(原文)

- commit 前只跑了 py_compile(`.claude/hooks/redlight.py`、`tests/conftest.py`、`tests/test_redlight.py`、`tests/test_status.py`),四者皆無輸出。

```
$ git diff --cached --name-only
.claude/hooks/redlight.py
docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
tests/conftest.py
tests/test_redlight.py
tests/test_status.py
$ git diff --cached --check
(無輸出)
$ git diff --cached -U0 -- tests/test_redlight.py tests/test_status.py
diff --git a/tests/test_redlight.py b/tests/test_redlight.py
index ec7995c..b83a542 100644
--- a/tests/test_redlight.py
+++ b/tests/test_redlight.py
@@ -771,0 +772 @@ _C_OPTION_DEFAULTS = {
+    "runxfail": False, "pythonwarnings": None, "trace": False,
diff --git a/tests/test_status.py b/tests/test_status.py
index cf5db4f..24caaa0 100644
--- a/tests/test_status.py
+++ b/tests/test_status.py
@@ -586 +586,2 @@ class TestTestsUnderTicketUsesTheLatestRecordPerFile:
-                             u"setuponly": False, u"setupplan": False},
+                             u"setuponly": False, u"setupplan": False,
+                             u"runxfail": False, u"pythonwarnings": None, u"trace": False},
@@ -594 +595,2 @@ class TestTestsUnderTicketUsesTheLatestRecordPerFile:
-                u"inipath": u"pyproject.toml", u"config_blobs": blobs, u"pytest_version": u"9.1.1"})
+                u"inipath": u"pyproject.toml", u"config_blobs": blobs, u"pytest_version": u"9.1.1",
+                u"optimize": 0, u"python_version": u"3.11"})
@@ -1356 +1358,3 @@ class TestOrphans:
-                                                 u"setuponly": False, u"setupplan": False},
+                                                 u"setuponly": False, u"setupplan": False,
+                                                 u"runxfail": False, u"pythonwarnings": None,
+                                                 u"trace": False},
@@ -1367 +1371,2 @@ class TestOrphans:
-                                    u"config_blobs": blobs, u"pytest_version": u"9.1.1"})
+                                    u"config_blobs": blobs, u"pytest_version": u"9.1.1",
+                                    u"optimize": 0, u"python_version": u"3.11"})
@@ -1890,0 +1896 @@ _S_OPTION_DEFAULTS = {
+    "runxfail": False, "pythonwarnings": None, "trace": False,
```

逐 hunk 歸屬:

| hunk | 歸屬 |
|---|---|
| test_redlight `@@ -771,0 +772 @@` | 1c:`_C_OPTION_DEFAULTS` 加三鍵 |
| test_status `@@ -1890,0 +1896 @@` | 1c:`_S_OPTION_DEFAULTS` 加三鍵 |
| test_status `@@ -586 …` | 1d:570/571(`test_a_file_that_went_red_then_green_counts_as_green`)的 `options` 補三鍵(`-` 行是同一行 dict 的結尾,改成接續) |
| test_status `@@ -594 …` | 1d:同上,補 `optimize: 0`、`python_version: "3.11"` |
| test_status `@@ -1356 …` | 1d:ODC-2(`test_a_renamed_red_test_is_orphaned_not_green`)的 `options` 補三鍵 |
| test_status `@@ -1367 …` | 1d:同上,補 `optimize`、`python_version` |

- `+` / `-` 行中沒有任何 `assert`、docstring 或 `def`。
- 四個 `-` 行都是 dict 字面值的最後一行,被改成接續新鍵(內容不變,只把結尾的 `}` / `})` 移到新增行之後)。

```
$ git commit -F .scratch/m1a-s4e/s4e-1-msg.txt
[master 0139a7e] fix(145): M1-a Station 4e —— pass 有效性 (xiv)–(xviii) 與 producer 路徑正規化 F3-甲
 5 files changed, 222 insertions(+), 37 deletions(-)
$ git rev-parse HEAD
0139a7e803fc2d41eb354f1196a6206cfe304701
$ git status --porcelain
(無輸出)
```

### 3. 驗收(在 S4e-1 上只跑一次)

```
$ date -u +%Y-%m-%dT%H:%M:%SZ
2026-10-03T13:47:39Z
$ python -X utf8 -m pytest -q > <session scratch>/s4e-run.txt 2>&1
```

- 退出碼:**0**(工具沒有回報錯誤;帳本第 19 行 `"exit_code": 0`)。
- **與指令的差異(照實記錄)**:pytest 指令本身沒有加任何參數。但 stdout / stderr 由 shell 導進 session scratch 的檔案,再以 Read / Grep 讀回。理由:3e 那一次工具把終端輸出截斷,摘要行遺失。重導向不是 pytest 參數,也不影響執行。
- 輸出檔共 37 行,全文如下(`<session scratch>` 為遮罩;檔案內沒有本機路徑):

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
........................................................................ [ 74%]
........................................................................ [ 78%]
........................................................................ [ 81%]
........................................................................ [ 85%]
........................................................................ [ 89%]
........................................................................ [ 92%]
........................................................................ [ 96%]
........................................................................ [ 99%]
.....                                                                    [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_gate.py:451: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:459: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:473: 此環境無法建立 symlink
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/srv/x] - …
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/data/x] - …
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/backup/x] - …
2015 passed, 3 skipped, 3 xfailed in 159.82s (0:02:39)
```

- XFAIL 三行的說明文字以 `…` 截斷(原文是一段很長的中文理由),所以這三行不是逐字全文。其他行逐字。
- **摘要行原文**:`2015 passed, 3 skipped, 3 xfailed in 159.82s (0:02:39)`,等於預期。collected 2021 = 2015 + 3 + 3。
- 沒有任何 FAILED / ERROR 行。

### 4. 驗收判定

#### 4a. 3e 的 18 支全部轉綠;10 支 regression-lock 仍綠

帳本第 19 行(Grep `-o`,原文):

```
19:"tests/test_redlight.py::TestPassValidityCoverage::test_e3o_an_optimized_interpreter_is_not_full_coverage[1]": "passed"
19:"tests/test_redlight.py::TestPassValidityCoverage::test_e3o_an_optimized_interpreter_is_not_full_coverage[2]": "passed"
19:"tests/test_redlight.py::TestPassValidityCoverage::test_e3o_a_missing_optimize_fact_is_not_full_coverage": "passed"
19:"tests/test_redlight.py::TestPassValidityCoverage::test_e3x_runxfail_alone_is_not_full_coverage": "passed"
19:"tests/test_redlight.py::TestPassValidityCoverage::test_e3w_a_pytest_warning_filter_alone_is_not_full_coverage": "passed"
19:"tests/test_redlight.py::TestPassValidityCoverage::test_e3t_trace_alone_is_not_full_coverage": "passed"
19:"tests/test_redlight.py::TestPassValidityCoverage::test_e3v_an_unrecognized_python_version_is_not_full_coverage": "passed"
19:"tests/test_redlight.py::TestPassValidityCoverage::test_e3o_the_producer_records_the_interpreter_optimize_flag": "passed"
19:"tests/test_redlight.py::TestPassValidityCoverage::test_e3x_the_producer_records_runxfail_and_pythonwarnings": "passed"
19:"tests/test_redlight.py::TestPassValidityCoverage::test_e3d_the_fixed_command_with_a_plain_interpreter_is_full_coverage": "passed"
19:"tests/test_redlight.py::TestPassValidityCoverage::test_e3a_plain_assert_mode_on_a_plain_interpreter_is_still_full_coverage": "passed"
19:"tests/test_redlight.py::TestProducerPathNormalization::test_e3p_blocked_plugin_names_never_persist_a_path[win-abs]": "passed"
19:"tests/test_redlight.py::TestProducerPathNormalization::test_e3p_blocked_plugin_names_never_persist_a_path[posix-abs]": "passed"
19:"tests/test_redlight.py::TestProducerPathNormalization::test_e3p_blocked_plugin_names_never_persist_a_path[rel-escape]": "passed"
19:"tests/test_redlight.py::TestProducerPathNormalization::test_e3p_a_config_file_option_never_persists_a_path[win-abs]": "passed"
19:"tests/test_redlight.py::TestProducerPathNormalization::test_e3p_a_config_file_option_never_persists_a_path[posix-abs]": "passed"
19:"tests/test_redlight.py::TestProducerPathNormalization::test_e3p_a_config_file_option_never_persists_a_path[rel-escape]": "passed"
19:"tests/test_redlight.py::TestProducerPathNormalization::test_e3p_an_override_value_never_persists_a_path[win-abs]": "passed"
19:"tests/test_redlight.py::TestProducerPathNormalization::test_e3p_an_override_value_never_persists_a_path[posix-abs]": "passed"
19:"tests/test_redlight.py::TestProducerPathNormalization::test_e3p_an_override_value_never_persists_a_path[rel-escape]": "passed"
19:"tests/test_redlight.py::TestProducerPathNormalization::test_e3p_non_path_override_values_are_persisted_verbatim": "passed"
19:"tests/test_redlight.py::TestProducerPathNormalization::test_e3p_non_path_plugin_names_are_persisted_verbatim": "passed"
19:"tests/test_redlight.py::TestProducerPathNormalization::test_e3p_a_root_relative_config_file_option_is_persisted_as_given": "passed"
19:"tests/test_status.py::TestPassValidityChain::test_e3o_optimized_pass_does_not_retire_a_known_red": "passed"
19:"tests/test_status.py::TestPassValidityChain::test_e3o_optimized_run_does_not_make_a_clean_file_green": "passed"
19:"tests/test_status.py::TestPassValidityChain::test_e3x_runxfail_pass_does_not_retire_a_known_red": "passed"
19:"tests/test_status.py::TestPassValidityChain::test_e3w_warning_filter_pass_does_not_retire_a_known_red": "passed"
19:"tests/test_status.py::TestPassValidityLocks::test_e3d_the_fixed_command_full_run_still_retires_the_red": "passed"
```

⇒ 28 支全部 `passed`(18 支 behavior-red 轉綠、10 支 regression-lock 仍綠)。**成立。**

#### 4b. 帳本第 19 行(真實 session)的新事實

Grep `-o`(原文,只列第 19 行):

```
19:"exit_code": 0
19:"runxfail": false
19:"pythonwarnings": null
19:"trace": false
19:{"name": "anyio", "kind": "known_dist", "dists": [["anyio", "4.15.0"]]}
19:"blocked": []
19:"override_ini": ["strict_markers=true"]
19:"inifilename": null
19:"inipath": "pyproject.toml"
19:"config_blobs": {"pyproject.toml": {"worktree": "b3a0836d4f1c4b6b0d7d13ce384408af413cc58d", "head": "b3a0836d4f1c4b6b0d7d13ce384408af413cc58d"}, "tests/conftest.py": {"worktree": "7156c3430f48018166f6395438060bb996b3dee1", "head": "7156c3430f48018166f6395438060bb996b3dee1"}}
19:"pytest_version": "9.1.1"
19:"optimize": 0
19:"python_version": "3.11"
```

- **新事實**:`optimize` 0、`python_version` "3.11"、`runxfail` false、`pythonwarnings` null、`trace` false。**成立。**
- **3c / 3d 舊事實不變**:
  - `override_ini == ["strict_markers=true"]`、`inifilename` null、`inipath` "pyproject.toml"。
  - 兩個 blob worktree = head。`tests/conftest.py` 的 blob 由 `93a1316f…` 變為 `7156c343…`,是 S4e-1 改了 conftest 的結果;仍是 worktree = head。
  - `pytest_version` "9.1.1"、anyio 4.15.0 為 known_dist、`blocked` 為空(None 項目 0)。
  - 第 19 行的 `"kind"`:session 1 項 + plugin 43 項,其中 builtin 41、known_dist 1、root_conftest 1、**other 0**。
  - **成立。**
- **producer 產生的欄位無絕對路徑**:對全帳本 Grep `"name": "[^"]*[/\\:][^"]*", "kind"`,第 15–19 行都只命中 `tests/conftest.py`;`inipath` / `inifilename` / `override_ini` / `blocked` 的值見上。**成立。**
- **全帳本本機使用者名稱**:對 `.dev/test-runs.jsonl`、`.dev/test-sessions.jsonl` 以 Grep count 搜尋本機使用者名稱 ⇒ **0 筆**(`Found 0 total occurrences across 0 files.`;搜尋字串不照錄)。

#### 4c. 帳本 H6 → H7 只追加

```
$ git status --porcelain
(無輸出)
$ wc -c -l .dev/test-runs.jsonl .dev/test-sessions.jsonl
   2641  709048 .dev/test-runs.jsonl
     19 6308355 .dev/test-sessions.jsonl
   2660 7017403 total
$ head -c 697745 .dev/test-runs.jsonl > <session scratch>/r6.bin
$ head -c 5599744 .dev/test-sessions.jsonl > <session scratch>/s6.bin
$ sha256sum <session scratch>/r6.bin
a6ff861ecbd0963f5fb2c8bc5fb745f1b87c74d338711832a913218dec999f7e *<session scratch>/r6.bin
$ sha256sum <session scratch>/s6.bin
e78a696887cfe660a7d2ea382ddea1109b73865255ea38ac2fbf7c44894e42f6 *<session scratch>/s6.bin
$ sha256sum .dev/test-runs.jsonl
5ae4e0d0747811a58cc8b786f725508bfbe43fcca80ef119cb81842a85367696 *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
e34472a1150559e93a5ab1a155774c025afd050433557c6c076e025731d41c92 *.dev/test-sessions.jsonl
```

(`<session scratch>` 為遮罩 —— 這幾行不是逐字原文。)

| 點 | test-runs | test-sessions |
|---|---|---|
| H6(驗收前) | 697745 bytes / 2595 行 / `a6ff861e…` | 5599744 bytes / 18 行 / `e78a6968…` |
| H7(驗收後) | 709048 bytes / 2641 行 / `5ae4e0d0747811a58cc8b786f725508bfbe43fcca80ef119cb81842a85367696` | 6308355 bytes / 19 行 / `e34472a1150559e93a5ab1a155774c025afd050433557c6c076e025731d41c92` |

⇒ 兩本前段都等於 H6;test-runs +46 行、test-sessions +1 行。**成立。**

#### 4d. status.py

`python .claude/portable/status.py --root .` 的 Evidence 與 Derived(逐字):

```
=== Evidence ===
test-runs: 本票 red 0 / green 46 / run 事實未知 0 / orphaned 0 / schema 不合格 run 0;最後一筆 tests/test_verify_gates.py=green @ 2026-10-03T13:50:13.760384+00:00;最近一次 run:A(exit 0;collected 2021 / deselected 0 / passed 2015 / failed 0 / skipped 3)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl)
intercepts (當月): 5 筆  (source: .dev/intercepts-2026-10.jsonl)
intercepts (最新存在月): 2026-10 5 筆;末筆 R7@2026-10-03T00:29:01.715824+00:00  (source: .dev/intercepts-2026-10.jsonl)
exemptions: 總 281 筆;granted 240 筆;blocked 1 筆;未記錄(無此欄)40 筆;最後一筆 2026-09-24T08:17:49.073745+00:00  (source: .dev/gate-exemptions.jsonl)
provenance: 未記錄(上游無此檔屬正常)  (source: .dev/provenance.jsonl)
report: 2026-10-03T004050Z-ticket145-station5d-0.md;HEAD 2026-10-03T09:47:26-04:00;回報後 5 筆  (source: .dev/reports/)

=== Derived ===
src write allowed in implement: yes  (source: gate.stage_allows_src_write() <- .agents/pipeline-stages.yaml)
tests red under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests green under ticket 145: tests/test_adr_numbering.py / tests/test_adr_numbers_resolve_upstream.py / tests/test_apply_patches.py / tests/test_bash_write.py / tests/test_bootstrap.py / tests/test_canon_section.py / tests/test_ci_workflow.py / tests/test_cjk_git_paths.py / tests/test_claude_md.py / tests/test_declared_in_is_an_identity.py / tests/test_dependency_ceiling.py / tests/test_edit_result.py / tests/test_evidence_isolation.py / tests/test_friction_heading.py / tests/test_g1_guard.py / tests/test_g1_verify.py / tests/test_gate.py / tests/test_gate_boundaries.py / tests/test_gitlink_downstream_cycle.py / tests/test_install.py / tests/test_intercepts.py / tests/test_known_items_regression.py / tests/test_leak_scan.py / tests/test_ledger_verify.py / tests/test_line_ending_parity.py / tests/test_manifest.py / tests/test_mcp_server.py / tests/test_non_source_list_parity.py / tests/test_portable_output_encoding.py / tests/test_r5_mounts.py / tests/test_redlight.py / tests/test_research_stage.py / tests/test_scanner.py / tests/test_shadow.py / tests/test_shadow_review.py / tests/test_source_hygiene.py / tests/test_stage_defs_source.py / tests/test_stage_naming.py / tests/test_status.py / tests/test_sync.py / tests/test_ticket_dirs_are_md_only.py / tests/test_ticket_lookup.py / tests/test_ticket_path_parity.py / tests/test_upstream_manifest.py / tests/test_user_layer.py / tests/test_verify_gates.py  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests green (run 事實未知) under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests orphaned under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
rules defined: R1 R2 R3 R4 R5 R6 R7 R8 R9  (source: gate.rule_codes())
```

⇒ red(無)、green 46 檔、最近一次 run 為 A。**成立。**

#### 4e. 3c / 3d 中斷言 `!= "true"` 的既有測試:主因條件(靜態推理,未另跑程式)

**前提**:
- 判定順序以 S4e-1 的 `_completeness_verdict` 為準(`0139a7e…:.claude/hooks/redlight.py:776-820`)。
- 4e 新條件位於 `:795-802`,排在 (vii)(xii)(xiii)(viii)(ix)(x)(xi)(`:778-793`)**之後**,排在 (ii)(iii)(iv)(v)(vi)(`:803-819`)**之前**。
- 固定全套之下,producer 從真實直譯器讀到 `optimize` 0、`python_version` "3.11"。授權補件後,fake option 帶 `runxfail=False`、`pythonwarnings=None`、`trace=False`。因此 `_completeness_problems` 不會因 4e 欄位報錯,`:795-802` 對這些測試全部成立(不擋)。

| 測試 | 第一個擋下的條件(S4e-1 行號) | 4e 新條件是否參與 |
|---|---|---|
| `test_redlight.py::TestCompletenessCoverage::test_c3a_lf_silent_narrowing_is_not_full_coverage` | (viii):`_COption` 沒有 `override_ini` ⇒ None ≠ 常數(`:784-785`);原設計主因 (ii) `:803-805` 與 (v) `:814-815` 排在其後 | 否(在 `:795` 之前就回 unknown) |
| `…::test_c3b_a_session_without_completeness_facts_is_not_full_coverage` | completeness 缺 ⇒ `_completeness_problems` 非空(`:776-777`) | 否(4c 起即缺) |
| `…::test_c3b_a_malformed_completeness_fact_is_not_full_coverage` | `shouldstop` 為字串 ⇒ problems(`:776-777`);同時缺 4d 欄位 | 4e 只是**多加**缺欄問題;原本的 `shouldstop` 型別問題本身就足以擋 |
| `…::test_c3c_an_exitfirst_run_is_not_full_coverage` | (viii) `:784-785`;原設計主因 (iii) `:806-808`、(iv) `:811-812`、(vi) `:818-819` 在其後 | 否 |
| `…::test_c3p_an_unknown_plugin_dist_means_not_full_coverage` / `…_a_plugin_loaded_by_name…` / `…_an_extra_conftest…` | 手寫 `_c_all_off()` 缺 4d 欄位 ⇒ problems(`:776-777`);原設計主因 (vii) `:778-779` 在其後 | 4e 只多加缺欄問題;**4d 起**就已由缺欄擋下(S5c-F2 的同類關切,非 4e 新增) |
| `test_redlight.py::TestCollectionDefinitionCoverage::test_d3a_…` / `test_d3b_…` | (viii) `:784-785` | 否 |
| `…::test_d3c_a_config_file_option_is_not_full_coverage` / `test_d3c_…naming_the_committed_config` | (ix) `:786-787` | 否 |
| `…::test_d3w_an_unexpected_config_file_is_not_full_coverage` | (x) `:788-789` | 否 |
| `…::test_d3w_an_uncommitted_config_change…` / `test_d3w_a_non_collection_edit…` / `test_d3w_an_uncommitted_root_conftest_change…` | (xi) `:790-793` | 否 |
| `…::test_d3v_an_unrecognized_pytest_version_is_not_full_coverage` | (xiii) `:782-783` | 否 |
| `…::test_d3v_a_known_plugin_with_unrecognized_version_is_not_full_coverage` | (vii′):`classify_plugins` 判 other(`(名稱, 版本)` 不在 `KNOWN_DISTS`)⇒ `:778-779` | 否 |
| `…::test_d3x_a_blocked_plugin_is_not_full_coverage` | `(name, None)` 判 other ⇒ `:778-779`(其後 (xii) `:780-781` 也會擋) | 否 |
| `…::test_d3i_lf_alone_is_not_full_coverage`(破壞組) | 4e 條件全部成立 ⇒ (ii) `:803-805` 回 `"false"` | 否(對照組 `== "true"` 證明 4e 條件在同一組事實下不擋) |
| `…::test_d3i_maxfail_alone_is_not_full_coverage`(破壞組) | (iii) `:806-808` | 否(同上) |
| `…::test_d3i_shouldfail_alone_is_not_full_coverage`(破壞組) | (iv) `:811-812` | 否(同上) |
| `test_status.py` 的 3c 串接(`TestSilentNarrowingChain` ×2、`TestEarlyStopChain` 的 `!= true` / 不 green 各支、`TestLfFalseGreenChain`、`TestPluginProducerChain` 的 C3p-4 / 5 / 6) | 與 test_redlight 的 3c 同型:`_CompletenessOption` 沒有 `override_ini` ⇒ (viii) `:784-785`;C3c-4 為 exit 2 ⇒ `run_state` D(`:385`),status 直接不退紅 | 否 |
| `test_status.py::TestOverrideIniChain` ×3(D3a-2 / 3 / 4) | (viii) `:784-785` | 否 |

**結論**:
- 沒有任何一支 3c / 3d 的 `!= "true"` 測試是因為 4e 新條件(`:795-802`)才通過的。
- 3d 的 D3i 三支在 4e 條件全部成立之後,仍由各自的原條件擋下,同支內的對照組 `== "true"` 證明了這一點。
- 3c 的 consumer 手寫 dict 與 3c 的 producer 測試,在 4d 起就先被 4d 的缺欄 / (viii) 擋下;這是 4d 已記錄的 S5c-F2 同類關切,4e 沒有讓它變得更多或更少。

### 5. 程序事件與尚未證明

1. **驗收輸出以 shell 重導向保存**(見第 3 節);pytest 指令本身沒有改。
2. **〈十〉的 Station 3e 列**:在 S4e-1 中依 Jeff 的 3e 裁決(「Station 3e = PASS / ACCEPTED」),由「紅燈已寫,待驗收」改為「PASS / ACCEPTED」。4e 指令明文只列了 Station 4e 列,這一列是**依裁決推得的同步**,照實記錄。
3. **跨平台**:F3-甲 在 Linux 上的行為(外部觀察指出的 `[win-abs]` 兩支)**本機沒有實測**。推演:
   - `C:\Users\…` 在 POSIX 上 `os.path.isabs` 為假、`_is_abs_path` 為真 ⇒ `_root_relative` 回 `<outside>` ⇒ 不落帳原樣。
   - 列為 5e 審查題(〈三十七〉外部觀察)。
4. `invocation.args` 的他平台絕對路徑改回 None:沒有專屬測試鎖住(3e 紅燈沒有列這一項)。
5. intercepts 仍為 5 筆、末筆時間與 3e 報告相同 ⇒ 本輪沒有新增攔截。
6. CLEAN / REAL 層未證明。
