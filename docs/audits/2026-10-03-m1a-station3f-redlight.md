# 票 145(M1-a)Station 3f 紅燈證據 —— `--pdb`(xix)與 S5e-F2 / F3 / F4

## 【給裁決者】

1. 新增 36 支測試，只加在兩個測試檔的檔尾，既有行一字未改。產品碼沒有動。
2. 在紅燈 commit 上跑了一次固定全套：結果 `13 failed, 2038 passed, 3 skipped, 3 xfailed`,與預期相同。紅的 13 支恰好是預定要紅的那 13 支，其餘既有測試全部通過。
3. 每一支紅都是「對照組通過、破壞組失敗」,而且失敗的那一行就是我們要抓的缺陷，不是測試本身寫錯。其中 4 支直接用 pytest 自己的參數解析器處理 `--pdb`,確認讀到的是 pytest 真正的欄位名。
4. 有一支(R13)在本機 Windows 上是綠的，要到 Linux 才會紅。這是預先知道的，它的紅由 R9 / R10 在本機用模擬的方式補上。
5. 要你決定：驗收 3f 紅燈。驗收之後才進 4f(修正產品碼)。

## 【給裁決助手】

### 1. 身分

| 名稱 | 完整 SHA |
|---|---|
| S3F0(規劃,前置 HEAD) | `8bdc4f2072a6b4300deb011a7b5a0d574254fc9c` |
| S3F1(紅燈 commit,本次驗收對象) | `229b5e762f087193e138c7c8d0f0d0b0f3e5cbb5` |
| 產品碼(與 TARGET 相同) | `0139a7e803fc2d41eb354f1196a6206cfe304701` |

### 2. 前置(第 0 步,各自單獨執行)

```
$ git status --porcelain
(無輸出)
$ git rev-parse HEAD
8bdc4f2072a6b4300deb011a7b5a0d574254fc9c
$ cat .dev/pipeline.json
{
  "current_stage": "tickets",
  "feature": "framework-updates",
  "ticket_id": "145",
  "updated": "2026-10-02"
}
$ wc -c .dev/test-runs.jsonl
709048 .dev/test-runs.jsonl
$ wc -c .dev/test-sessions.jsonl
6308355 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl
5ae4e0d0747811a58cc8b786f725508bfbe43fcca80ef119cb81842a85367696 *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
e34472a1150559e93a5ab1a155774c025afd050433557c6c076e025731d41c92 *.dev/test-sessions.jsonl
$ wc -l tests/test_redlight.py
1850 tests/test_redlight.py
$ wc -l tests/test_status.py
2731 tests/test_status.py
```

N_r = 1850,N_s = 2731。

### 3. S3f-1 commit

```
$ python -X utf8 -m py_compile tests/test_redlight.py
(無輸出)
$ python -X utf8 -m py_compile tests/test_status.py
(無輸出)
$ git diff --cached --name-only
docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
tests/test_redlight.py
tests/test_status.py
$ git diff --cached --check
(無輸出)
```

`git diff --cached -U0`:每個測試檔恰一個 hunk,沒有任何以 `-` 開頭的內容行。hunk 標頭原文:

```
@@ -1850,0 +1851,293 @@ class TestProducerPathNormalization:
@@ -2731,0 +2732,125 @@ class TestPassValidityLocks:
```

(第一行屬 `tests/test_redlight.py`,第二行屬 `tests/test_status.py`。)

```
$ git commit -F .scratch/m1a-s3f/s3f-1-msg.txt
[master 229b5e7] test(145): M1-a Station 3f 紅燈 —— --pdb (xix) 與 S5e-F2/F3/F4(13 behavior-red + 23 regression-lock)
 3 files changed, 510 insertions(+), 3 deletions(-)
$ git rev-parse HEAD
229b5e762f087193e138c7c8d0f0d0b0f3e5cbb5
$ git status --porcelain
(無輸出)
```

`3 deletions(-)` 全部在票 145(狀態行、〈十〉3f 列、lifecycle 句的取代);兩個測試檔的 `-U0` diff 沒有刪除行。

### 4. 固定全套(在 S3F1 上只跑一次)

```
$ python -X utf8 -m pytest -q > <session scratch>/s3f-run.txt 2>&1
```

- 退出碼：**1**(工具回報 `Exit code 1`)。
- pytest 指令本身沒有加任何參數;輸出以 shell 重導向存到 session scratch,再用 Read 讀回(與 4e 驗收相同的做法)。
- 輸出檔共 408 行。以下照錄進度列、short test summary 與摘要行。中間 FAILURES 段的 traceback 含 `tmp_path` 的本機路徑，所以不照錄全文;各支失敗的行號與斷言改列在第 6 節。

```
........................................................................ [  3%]
........................................................................ [  7%]
........................................................................ [ 10%]
........................................................................ [ 14%]
..............................................xxx....................... [ 17%]
........................................................................ [ 21%]
........................................................................ [ 24%]
........................................................................ [ 28%]
............sss......................................................... [ 31%]
........................................................................ [ 35%]
........................................................................ [ 38%]
........................................................................ [ 42%]
........................................................................ [ 45%]
........................................................................ [ 49%]
........................................................................ [ 52%]
........................................................................ [ 56%]
........................................................................ [ 59%]
........................................................................ [ 63%]
........................................................................ [ 66%]
........................................................................ [ 70%]
........................................................................ [ 73%]
...............FFFFF.FF.FF....................F......................... [ 77%]
........................................................................ [ 80%]
........................................................................ [ 84%]
........................................................................ [ 87%]
........................................................................ [ 91%]
...............................FFF...................................... [ 94%]
........................................................................ [ 98%]
.........................................                                [100%]
```

```
FAILED tests/test_redlight.py::TestDebuggerModeCoverage::test_f3p_pdb_alone_is_not_full_coverage
FAILED tests/test_redlight.py::TestDebuggerModeCoverage::test_f3p_a_missing_or_malformed_usepdb_fact_is_not_full_coverage[missing]
FAILED tests/test_redlight.py::TestDebuggerModeCoverage::test_f3p_a_missing_or_malformed_usepdb_fact_is_not_full_coverage[str]
FAILED tests/test_redlight.py::TestDebuggerModeCoverage::test_f3p_the_producer_records_usepdb_from_the_pytest_parser
FAILED tests/test_redlight.py::TestDebuggerModeCoverage::test_f3p_pdb_parsed_by_pytest_is_not_full_coverage
FAILED tests/test_redlight.py::TestOverrideBaseCoverage::test_f3o_an_invocation_dir_outside_the_root_keeps_non_path_override_values
FAILED tests/test_redlight.py::TestOverrideBaseCoverage::test_f3o_the_fixed_command_from_the_parent_dir_is_full_coverage
FAILED tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_a_backslash_escape_is_outside_under_posix_semantics[override]
FAILED tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_a_backslash_escape_is_outside_under_posix_semantics[config-file]
FAILED tests/test_redlight.py::TestIdentifierFullMatch::test_f3i_a_plugin_name_with_a_trailing_newline_is_not_persisted_verbatim
FAILED tests/test_status.py::TestDebuggerModeChain::test_f3p_pdb_pass_does_not_retire_a_known_red
FAILED tests/test_status.py::TestDebuggerModeChain::test_f3p_pdb_parsed_by_pytest_does_not_retire_a_known_red
FAILED tests/test_status.py::TestOverrideBaseChain::test_f3o_the_fixed_command_from_the_parent_dir_retires_the_red
13 failed, 2038 passed, 3 skipped, 3 xfailed in 169.02s (0:02:49)
```

- **摘要行原文**:`13 failed, 2038 passed, 3 skipped, 3 xfailed in 169.02s (0:02:49)`,等於〈四十一〉41.1 第 7 點的預期。collected 2057 = 13 + 2038 + 3 + 3。
- 進度列中 `F` 共 13 個(5 + 2 + 2 + 1 + 3)。
- short test summary 另有 3 行 SKIPPED(`tests\test_gate.py:451 / 459 / 473`,此環境無法建立 symlink)與 3 行 XFAIL(`tests/test_g1_guard.py::TestLevelTwoIsUnchanged::…[/srv/x] / [/data/x] / [/backup/x]`),與 4e 驗收相同。
- 沒有 ERROR 行。

### 5. 帳本 H7 → H8 只追加

```
$ wc -c -l .dev/test-runs.jsonl .dev/test-sessions.jsonl
   2687  721553 .dev/test-runs.jsonl
     20 7030070 .dev/test-sessions.jsonl
   2707 7751623 total
$ head -c 709048 .dev/test-runs.jsonl > <session scratch>/r7.bin
$ head -c 6308355 .dev/test-sessions.jsonl > <session scratch>/s7.bin
$ sha256sum <session scratch>/r7.bin
5ae4e0d0747811a58cc8b786f725508bfbe43fcca80ef119cb81842a85367696 *<session scratch>/r7.bin
$ sha256sum <session scratch>/s7.bin
e34472a1150559e93a5ab1a155774c025afd050433557c6c076e025731d41c92 *<session scratch>/s7.bin
$ sha256sum .dev/test-runs.jsonl
f7a025c6de2ad0d97ef38eac1725ea0e8d566fb0a0d453d3a5e530b84018a379 *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
4ceb819ea08f78e3c9aa5849bf89e3ab2a54ca42619427fb0dfeab36e4f576fc *.dev/test-sessions.jsonl
```

(`<session scratch>` 是遮罩,這幾行不是逐字原文。)

| 點 | test-runs | test-sessions |
|---|---|---|
| H7(驗收前) | 709048 bytes / 2641 行 / `5ae4e0d0747811a58cc8b786f725508bfbe43fcca80ef119cb81842a85367696` | 6308355 bytes / 19 行 / `e34472a1150559e93a5ab1a155774c025afd050433557c6c076e025731d41c92` |
| H8(驗收後) | 721553 bytes / 2687 行 / `f7a025c6de2ad0d97ef38eac1725ea0e8d566fb0a0d453d3a5e530b84018a379` | 7030070 bytes / 20 行 / `4ceb819ea08f78e3c9aa5849bf89e3ab2a54ca42619427fb0dfeab36e4f576fc` |

⇒ 兩本帳的前段都等於 H7。test-runs +46 行(= 測試檔數),test-sessions +1 行。H7 的行數取自 4e 報告 4c 節(2641 / 19)。

### 6. 36 支逐支表(帳本第 20 行;Grep `-o` 原文見 6.1)

- 「經 producer」= 經真實 `tests/conftest.py` 的 producer 寫帳本。
- 「經 parser」= option 來自 `pytestconfig._parser.parse_known_args(...)`。

| # | nodeid | 分類 | 實際 | 經 producer | 經 parser | 失敗行(實際斷言) |
|---|---|---|---|---|---|---|
| R1 | `tests/test_redlight.py::TestDebuggerModeCoverage::test_f3p_pdb_alone_is_not_full_coverage` | behavior-red | failed | 是 | 否 | `tests\test_redlight.py:1939`:`assert 'true' != 'true'`(對照組 `== "true"` 已通過) |
| R2 | `…::test_f3p_a_missing_or_malformed_usepdb_fact_is_not_full_coverage[missing]` | behavior-red | failed | 是 | 否 | `:1957`:`assert 'true' != 'true'` |
| R2 | `…::test_f3p_a_missing_or_malformed_usepdb_fact_is_not_full_coverage[str]` | behavior-red | failed | 是 | 否 | `:1957`:`assert 'true' != 'true'` |
| R3 | `…::test_f3p_the_producer_records_usepdb_from_the_pytest_parser` | behavior-red | failed | 是 | **是** | `:1973`:`assert None is True`(持久化 options 沒有 `usepdb`;前置斷言 `with_pdb.usepdb is True` 已通過) |
| R4 | `…::test_f3p_pdb_parsed_by_pytest_is_not_full_coverage` | behavior-red | failed | 是 | **是** | `:1988`:`assert 'true' != 'true'`(對照組以真實解析的 `["--strict-markers"]` 得 `"true"`) |
| R5 | `…::test_f3c_pdbcls_alone_does_not_lower_authority` | regression-lock | passed | 是 | **是** | — |
| R6 | `tests/test_redlight.py::TestOverrideBaseCoverage::test_f3o_an_invocation_dir_outside_the_root_keeps_non_path_override_values` | behavior-red | failed | 是 | 否 | `:2017`:`['strict_markers=<outside>'] == ['strict_markers=true']` |
| R7 | `…::test_f3o_the_fixed_command_from_the_parent_dir_is_full_coverage` | behavior-red | failed | 是 | 否 | `:2035`:`assert 'unknown' == 'true'`(情境斷言 args `["tests"]` / `["."]` 已通過) |
| R8 | `…::test_f3o_an_escaping_relative_override_is_outside_from_the_parent_dir` | regression-lock | passed | 是 | 否 | — |
| R9 | `tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_a_backslash_escape_is_outside_under_posix_semantics[override]` | behavior-red | failed | 否(正規化函式) | 否 | `:2087`:結果為 `['cache_dir=a\\..\\..\\..\\e3p-user\\c']`(原字串保留) |
| R10 | `…::test_f3s_a_backslash_escape_is_outside_under_posix_semantics[config-file]` | behavior-red | failed | 否(正規化函式) | 否 | `:2091`:`'a/../../../e3p-user/alt.toml' == '<outside>'` |
| R11 ×9 | `…::test_f3s_g3_inputs_under_posix_semantics[win-drive-backslash / win-drive-slash / drive-relative / unc / device / posix-abs / rel-escape / rel-inside / mixed-inside]` | regression-lock | 9 支皆 passed | 否 | 否 | — |
| R12 ×10 | `…::test_f3s_g3_inputs_under_windows_semantics[同上 9 個 + cross-drive]` | regression-lock | 10 支皆 passed | 否 | 否 | — |
| R13 | `…::test_f3s_a_backslash_escape_override_never_persists_a_path` | regression-lock(本機 Windows;POSIX 紅) | passed | 是 | 否 | — |
| R14 | `tests/test_redlight.py::TestIdentifierFullMatch::test_f3i_a_plugin_name_with_a_trailing_newline_is_not_persisted_verbatim` | behavior-red | failed | 是 | 否 | `:2143`:`['abc\n'] == ['<non-identifier>']`(對照組 `["abc"]` 已通過) |
| S1 | `tests/test_status.py::TestDebuggerModeChain::test_f3p_pdb_pass_does_not_retire_a_known_red` | behavior-red | failed | 是 | 否 | `tests\test_status.py:2789`:`{'red': '(無)', 'green': 'tests/test_x.py', …}`(情境斷言 B / 合格 / A 已通過) |
| S2 | `…::test_f3p_pdb_parsed_by_pytest_does_not_retire_a_known_red` | behavior-red | failed | 是 | **是** | `:2808`:同 S1 |
| S3 | `tests/test_status.py::TestOverrideBaseChain::test_f3o_the_fixed_command_from_the_parent_dir_retires_the_red` | behavior-red | failed | 是 | 否 | `:2833`:`['strict_markers=<outside>'] == ['strict_markers=true']`(情境斷言 A、args `["."]` 已通過) |
| S4 | `tests/test_status.py::TestDebuggerModeLocks::test_f3d_the_fixed_command_full_run_still_retires_the_red` | regression-lock | passed | 是 | 否 | — |

合計:behavior-red 13 支全部 failed;regression-lock 23 支(1 + 1 + 9 + 10 + 1 + 1)全部 passed。每一支 behavior-red 都在「對照組 / 情境斷言已通過之後」的那一行失敗,失敗值就是〈四十一〉41.3 預期的缺陷形狀。

#### 6.1 帳本第 20 行

Grep pattern `"tests/[^"]+": "failed"`(`-o -n`,對全帳本):第 20 行的命中**恰為 13 筆**,與第 4 節的 FAILED 清單逐一相同(第 6–18 行的命中屬於先前各站的紅燈 session)。

36 支新測試在第 20 行的值:Grep pattern `"tests/test_(redlight|status)\.py::Test(DebuggerMode\w*|OverrideBase\w*|PlatformIndependentNormalization|IdentifierFullMatch)::[^"]+": "[a-z]+"`(`-o -n`)。命中 36 筆,全部在第 20 行:13 筆 `"failed"`、23 筆 `"passed"`,與上表一致。

### 7. status.py

`python .claude/portable/status.py --root .`(節錄,逐字):

```
test-runs: 本票 red 2 / green 44 / run 事實未知 0 / orphaned 0 / schema 不合格 run 0;最後一筆 tests/test_verify_gates.py=green @ 2026-10-03T19:40:24.453456+00:00;最近一次 run:B(exit 1;collected 2057 / deselected 0 / passed 2038 / failed 13 / skipped 3)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl)
intercepts (當月): 7 筆  (source: .dev/intercepts-2026-10.jsonl)
intercepts (最新存在月): 2026-10 7 筆;末筆 R7@2026-10-03T18:48:00.112571+00:00  (source: .dev/intercepts-2026-10.jsonl)
tests red under ticket 145: tests/test_redlight.py / tests/test_status.py  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests orphaned under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
```

- red 只有 `tests/test_redlight.py`、`tests/test_status.py`;green 44 檔;最近一次 run 為 **B**(collected 2057)。**成立。**
- intercepts 由 4e 報告時的 5 筆增為 7 筆,末筆為 R7 @ 18:48:00Z。本輪(3f-1)的指令沒有被任何閘門擋下,所以推定這 2 筆不屬於本輪;但本報告**沒有逐筆核對**它們的內容與時間,這個歸屬只是推定,照實記錄。

### 8. 照實記錄 / 未證明

1. R13 在本機 Windows 為綠;它在 POSIX 上會紅,本輪沒有實測(〈四十一〉41.3 平台附註)。
2. R3 / R4 / R5 / S2 依賴私有屬性 `Config._parser`(〈四十一〉41.1 第 2 點);以 `-p no:cacheprovider` 執行時,R4 / S2 的對照組會因缺 `lf` 而失敗(41.2 已由裁決助手外部驗證,本輪未測)。
3. 規劃檔 7.4 列的 24 支「4f 後受 (xix) 影響的既有測試」,本輪不適用:產品碼未改,它們在本次全部 passed(屬於 2038 passed 之內)。
4. CLEAN / REAL 層不在本輪範圍。
