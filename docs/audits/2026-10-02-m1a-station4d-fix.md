# 票 145(M1-a)Station 4d 修正證據 —— 收集定義完整性與版本邊界

## 【給裁決者】

1. 照〈二十九〉的合約改了 redlight.py(判定)與 tests/conftest.py(記錄),並補了 9 支授權測試的 fixture 與 1 支鎖步測試(S4d-1)。
2. 在 S4d-1 上只跑一次固定全套:`1987 passed, 3 skipped, 3 xfailed`,exit 0、失敗 0;3d 的 13 支全部轉綠。
3. 真實 session 的新事實全部合格,status 46 檔 green、red 無;帳本只追加。四項完成判定全部成立。
4. 要你決定:是否交付 Station 5d 獨立審查。
5. 不決定的話:票停在「4d 修正完成,待審查」;版本未 pin 的殘餘照〈三十一〉裁決 2 進結案後追蹤票。

---

## 1. 前置

```
$ git rev-list --left-right --count origin/master...HEAD
0	29
$ git rev-parse HEAD
5262828ab7f8fb89bb6bb85a6f63e24fdf852532
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
   2503  673590 .dev/test-runs.jsonl
     16 4192482 .dev/test-sessions.jsonl
   2519 4866072 total
$ sha256sum .dev/test-runs.jsonl
44c7a8fee77511678912a6acef33b8c5a449b7f6269dc1ad2b4f84e2e0e28eba *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
a2d1192f384e9f19258a59aa72496a3fe39e1dffa002706fd56c06ce37c2a2ea *.dev/test-sessions.jsonl
```

- `python -m pip show pytest`:`Version: 9.1.1`;anyio `Version: 4.15.0`。`Location` 一行含本機使用者路徑,不照錄。
- **tracked conftest inventory**:`tests/conftest.py`(只有這一個)。
- L4 = test-runs 673590 bytes / 2503 行、test-sessions 4192482 bytes / 16 行;H4r = `44c7a8fe…`、H4s = `a2d1192f…`。
- **程序偏離(照實記錄)**:查 anyio 版本時,為了濾掉 pip 的 cp950 `Logging error` 雜訊,用了 PowerShell 的 `python -m pip show anyio 2>$null | Select-String -Pattern '^Version'`。這是 pipe,偏離「每條指令只做一件事;不用 pipe」(該鐵則寫的是 Bash);只讀、不影響任何檔案。

## 2. 實作摘要

### producer(`tests/conftest.py`)

`_completeness_of`(`tests/conftest.py:322-358`)在原有事實之外另記:
- `blocked`(`:349`):`list_name_plugin()` 中值為 None 的名稱(`-p no:`)。
- `override_ini`(`:350`):`config.option.override_ini` 的**解析後**值。不掃 argv;絕對路徑的值轉成 root 相對路徑。
- `inifilename`(`:351`)、`inipath`(`:352`):root 相對路徑。
- `config_blobs`(`:353`):`pyproject.toml` 與 `tests/conftest.py` 的工作樹 blob 與 HEAD blob。
- `pytest_version`(`:339, 354`):取本檔 import 的 `pytest.__version__`。

全部在原有的 `try … except Exception: return None` 之內,出錯 ⇒ completeness 為 None ⇒ unknown,不讓 pytest 失敗。

### consumer(`.claude/hooks/redlight.py`)

- **常數**(變更須走票):
  - `KNOWN_DISTS = (("anyio", "4.15.0"),)`(`:473`)
  - `KNOWN_PYTEST_VERSIONS = ("9.1.1",)`(`:476`)
  - `COMMITTED_ADDOPTS_OVERRIDES = ("strict_markers=true",)`(`:480`)
  - `CONFIG_FILE`、`COMMITTED_FILES`(`:483-484`)
- **plugin 分類**:`_dist_version`(`:501`)。`classify_plugins`(`:533`)以 (dist 名稱, 精確版本) 判 known_dist,配對項目另記 `dists`。
- **producer 用的 helper**:
  - `blocked_plugins`(`:568`)
  - `normalize_config_path`(`:574`)
  - `normalize_overrides`(`:585`)
  - `_git_lines`(`:599`)/ `committed_blobs`(`:615`):`git -C <root> hash-object <檔…>`(套用 .gitattributes 正規化)與 `git -C <root> rev-parse HEAD:<檔…>`。輸出必須是 40 / 64 位 hex;任何失敗 ⇒ None;不拋例外。
- **schema**:`_completeness_problems`(`:639`)加驗 `override_ini`、`inifilename`、`inipath`、`pytest_version`、`blocked`、`config_blobs`。Station 4d 之前的 session 缺這些欄位 ⇒ 不合格 ⇒ **unknown**;`validate_session` 不變,所以舊 session 仍是合格的 run。
- **判定** `_completeness_verdict`(`:678`),依序:
  - (vii)(vii′) kind 支援;
  - (xii) `blocked` 為空(`:701`);
  - (xiii) 版本在清單(`:703`);
  - (viii) `override_ini` 恰等於常數(`:705`);
  - (ix) `inifilename is None`(`:707`);
  - (x) `inipath == "pyproject.toml"`(`:709`);
  - (xi) 每個 `COMMITTED_FILES` 的 worktree blob 非空且等於 head(`:712`);
  - (ii) 無條件要求 lf / stepwise / stepwise_skip 為 False(`:716`),`cacheprovider_blocked` 不再有判定權;
  - 其後 (iii)–(vi) 不變;唯一的 `"true"` 出口在 `:733`。
- **沒有**為固定指令、TESTPATHS 或特定字串寫任何特殊分支;`.claude/portable/status.py` 未改。

`git diff --cached --numstat`(S4d-1):

```
152	16	.claude/hooks/redlight.py
18	2	tests/conftest.py
60	6	tests/test_redlight.py
30	8	tests/test_status.py
```

## 3. 授權補件與鎖步測試的 hunk 清單

`git diff --cached -U0 -- tests/test_redlight.py`:

| hunk 標頭 | 所屬測試 | 內容 |
|---|---|---|
| `@@ -531,0 +532 @@ class TestFileCoverage:` | b1c | 加 `_d_committed_root(tmp_path)` |
| `@@ -533 +534 @@ class TestFileCoverage:` | b1c | `_CConfig` 的 option / pm 改為 `_d_option()` / `_d_plugins(...)` |
| `@@ -534,0 +536 @@ class TestFileCoverage:` | b1c | 加 `session.config.inipath = …` |
| `@@ -547,0 +550 @@ class TestFileCoverage:` | b1d | 同 b1c |
| `@@ -549 +552 @@ class TestFileCoverage:` | b1d | 同 b1c |
| `@@ -550,0 +554 @@ class TestFileCoverage:` | b1d | 同 b1c |
| `@@ -643,2 +647,4 @@ class TestFixedCommandCoverage:` | b10 | option / pm 換新事實;加 inipath 與 `_d_committed_root` |
| `@@ -1056 +1062,2 @@ class TestCompletenessCoverage:` | C3d-1 | 加 `_d_committed_root`;`_c_drive` → `_d_drive` |
| `@@ -1059 +1066 @@ class TestCompletenessCoverage:` | C3d-1 | `option=_d_option(), pm=_d_plugins(...)` |
| `@@ -1478,0 +1486,47 @@ class TestCollectionDefinitionCoverage:` | **鎖步測試**(檔尾) | 新增 `test_d4_the_committed_addopts_override_constant_matches_pyproject` |

`git diff --cached -U0 -- tests/test_status.py`:

| hunk 標頭 | 所屬測試 | 內容 |
|---|---|---|
| `@@ -573,0 +574,4 @@ class TestTestsUnderTicketUsesTheLatestRecordPerFile:` | 570/571 | `_t_committed(root)`;以真的 git 算出兩個檔的 blob |
| `@@ -586 +590,5 @@ class TestTestsUnderTicketUsesTheLatestRecordPerFile:` | 570/571 | completeness dict 補新事實(含 anyio 4.15.0) |
| `@@ -1335,0 +1344,4 @@ class TestOrphans:` | ODC-2 | 同 570/571 |
| `@@ -1350 +1362,6 @@ class TestOrphans:` | ODC-2 | 同 570/571 |
| `@@ -1719,2 +1736,3 @@ class TestChainRegressionLocks:` | L3 | `_t_committed`;`_s_drive` → `_t_drive` |
| `@@ -2197,3 +2215,4 @@ class TestCompletenessLocks:` | C3d-2 | 同 L3 |
| `@@ -2293 +2312,4 @@ class TestPluginProducerChain:` | C3p-7 | `_t_committed`;`_s_full_run_session(...)` → `_t_drive` + `load_runs(root)[-1]` |

- 每個 hunk 都落在 9 支授權測試的 fake / fixture 呼叫上,或是檔尾的鎖步測試;沒有任何 assertion、docstring、test identity 被改;3c、3d 新增的其他測試與 C3p-6 一字未動。
- `git diff --cached --check`:無輸出。

## 4. 鎖步測試的推導方式(pytest 9.1.1 出處)

`tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d4_the_committed_addopts_override_constant_matches_pyproject`:

1. 來源:`git -C <repo 根> show HEAD:pyproject.toml`(唯讀;失敗 ⇒ `assert proc.returncode == 0` 失敗,不 skip)。以 tomllib(3.10 用 tomli)解析,取 `[tool.pytest.ini_options] addopts`。
2. addopts 是 type="args"(`_pytest/config/__init__.py:1547`),被放到 args 最前面一起解析(`:1559-1562`)⇒ 以 shlex 切成旗標。
3. 旗標 → override 項目的對應:

| 旗標 | override 項目 | 出處 |
|---|---|---|
| `--strict-config` | `strict_config=true` | `_pytest/main.py:76-82`(`OverrideIniAction`) |
| `--strict-markers` | `strict_markers=true` | `_pytest/main.py:83-89` |
| `--strict` | `strict=true` | `_pytest/main.py:90-96` |
| `-o KEY=VAL` / `--override-ini KEY=VAL` | `KEY=VAL` | `_pytest/helpconfig.py:113-116`(append) |
| 其他旗標(例 `-ra`) | (無) | — |

`OverrideIniAction` 把 `f"{ini_option}={ini_value}"` 附加到 `override_ini`(`_pytest/config/argparsing.py:491-503`)。

4. 依出現順序組成清單,必須恰等於 `redlight.COMMITTED_ADDOPTS_OVERRIDES`。已提交的 `-ra --strict-markers` ⇒ `["strict_markers=true"]`。這與〈二十九〉1 (a) 的隔離實測、以及下面真實 session 的 `override_ini` 一致。

## 5. 驗收(在 S4d-1 上只跑一次)

- S4d-1:`889fbd8f666ea522ff6af172979a8d020e50b86b`(`4 files changed, 260 insertions(+), 32 deletions(-)`);commit 後 `git status --porcelain` 無輸出;rev-list `0	30`。

```
$ date -u +%Y-%m-%dT%H:%M:%SZ
2026-10-02T23:49:40Z
$ python -X utf8 -m pytest -q
...
=========================== short test summary info ===========================
SKIPPED [1] tests\test_gate.py:451: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:459: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:473: 此環境無法建立 symlink
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/srv/x] - …
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/data/x] - …
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/backup/x] - …
1987 passed, 3 skipped, 3 xfailed in 149.54s (0:02:29)
```

- XFAIL 三行的說明文字以 `…` 截斷,所以本區塊不是逐字全文;SKIPPED 與摘要行逐字。
- exit code 0;輸出沒有任何 FAILED / ERROR 行;tool 輸出沒有截斷。
- collected 1993 = 1987 + 3 + 3 = 1992 + 1 支鎖步測試。
- 失敗清單為空 ⇒ 3d 的 13 支、3c / 3d 的 regression-lock、9 支授權測試、鎖步測試、其他全部測試都通過。

## 6. 帳本 H4 → H5 只追加

```
$ git status --porcelain
(無輸出)
$ wc -c -l .dev/test-runs.jsonl .dev/test-sessions.jsonl
   2549  684893 .dev/test-runs.jsonl
     17 4891233 .dev/test-sessions.jsonl
   2566 5576126 total
$ sha256sum .dev/test-runs.jsonl
23f397d47c76bc6985daa73dd99afe73c84b53dd2220a4305ae64cb8b1e4086c *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
7463a45257c893ec9079f0f655782bfab11855eab9fcd5f93b314e5d60beb70c *.dev/test-sessions.jsonl
$ head -c 673590 .dev/test-runs.jsonl > <session scratch>/r4.bin
$ head -c 4192482 .dev/test-sessions.jsonl > <session scratch>/s4.bin
$ sha256sum <session scratch>/r4.bin
44c7a8fee77511678912a6acef33b8c5a449b7f6269dc1ad2b4f84e2e0e28eba *<session scratch>/r4.bin
$ sha256sum <session scratch>/s4.bin
a2d1192f384e9f19258a59aa72496a3fe39e1dffa002706fd56c06ce37c2a2ea *<session scratch>/s4.bin
```

(scratch 絕對路徑以 `<session scratch>` 代替 —— 這四行經遮罩,不是逐字原文。)

| 點 | test-runs | test-sessions |
|---|---|---|
| H4(驗收前) | 673590 bytes / 2503 行 / `44c7a8fee77511678912a6acef33b8c5a449b7f6269dc1ad2b4f84e2e0e28eba` | 4192482 bytes / 16 行 / `a2d1192f384e9f19258a59aa72496a3fe39e1dffa002706fd56c06ce37c2a2ea` |
| H5(驗收後) | 684893 bytes / 2549 行 / `23f397d47c76bc6985daa73dd99afe73c84b53dd2220a4305ae64cb8b1e4086c` | 4891233 bytes / 17 行 / `7463a45257c893ec9079f0f655782bfab11855eab9fcd5f93b314e5d60beb70c` |

⇒ 兩本前段都等於 H4;test-runs +46 行(= 測試檔數)、test-sessions +1 行。

## 7. 真實 session(`.dev/test-sessions.jsonl` 第 17 行)的新事實

該行約 700 KB,以 Grep `-o` 取片段(不是整行 Read):

```
17:"blocked": []
17:"override_ini": ["strict_markers=true"]
17:"inifilename": null
17:"inipath": "pyproject.toml"
17:"pytest_version": "9.1.1"
17:"config_blobs": {"pyproject.toml": {"worktree": "b3a0836d4f1c4b6b0d7d13ce384408af413cc58d", "head": "b3a0836d4f1c4b6b0d7d13ce384408af413cc58d"}, "tests/conftest.py": {"worktree": "93a1316fb6fb5c7b4e16f35d8f34357a9adac5f1", "head": "93a1316fb6fb5c7b4e16f35d8f34357a9adac5f1"}}
17:{"name": "anyio", "kind": "known_dist", "dists": [["anyio", "4.15.0"]]}
17:"cacheprovider_blocked": false
```

- `plugins`:第 17 行 `"kind"` 共 43 個:builtin 41、known_dist 1、root_conftest 1、**other 0**。
- None 項目(`blocked`):0。
- 兩個雜湊比對:`pyproject.toml` 與 `tests/conftest.py` 的 worktree blob 都等於 head blob。
- **三類邊界**:
  - (1) producer 自行產生的欄位:`inipath` 為 `pyproject.toml`;`plugins[].name` 中唯一的路徑型名稱是 `tests/conftest.py`(Grep `"name": "[^"]*(\\\\|/)[^"]*", "kind"` 在第 17 行只命中它);`override_ini`、`config_blobs`、`blocked`、`pytest_version` 不含路徑 ⇒ **無絕對路徑**。
  - (2) 測試身分:全帳本 Grep `<user>|[A-Za-z]:(\\\\|/)Users`(`<user>` 為遮罩後的本機使用者名稱)命中 9 行,全部來自測試身分的 parametrize ID(〈二十五〉裁決 1 的 (2) 類,原樣保存,依鐵則不停手、不改寫)。
  - **全帳本 Grep 本機使用者名稱:test-sessions 0 筆、test-runs 0 筆。**

## 8. status.py(驗收後)

`python .claude/portable/status.py --root .` 的 Evidence 與 Derived 兩段(逐字):

```
=== Evidence ===
test-runs: 本票 red 0 / green 46 / run 事實未知 0 / orphaned 0 / schema 不合格 run 0;最後一筆 tests/test_verify_gates.py=green @ 2026-10-02T23:52:06.501012+00:00;最近一次 run:A(exit 0;collected 1993 / deselected 0 / passed 1987 / failed 0 / skipped 3)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl)
intercepts (當月): 4 筆  (source: .dev/intercepts-2026-10.jsonl)
intercepts (最新存在月): 2026-10 4 筆;末筆 R7@2026-10-02T22:44:19.109578+00:00  (source: .dev/intercepts-2026-10.jsonl)
exemptions: 總 281 筆;granted 240 筆;blocked 1 筆;未記錄(無此欄)40 筆;最後一筆 2026-09-24T08:17:49.073745+00:00  (source: .dev/gate-exemptions.jsonl)
provenance: 未記錄(上游無此檔屬正常)  (source: .dev/provenance.jsonl)
report: 2026-10-02T174245Z-ticket145-station5b-0.md;HEAD 2026-10-02T19:49:33-04:00;回報後 13 筆  (source: .dev/reports/)

=== Derived ===
src write allowed in implement: yes  (source: gate.stage_allows_src_write() <- .agents/pipeline-stages.yaml)
tests red under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests green under ticket 145: tests/test_adr_numbering.py / tests/test_adr_numbers_resolve_upstream.py / tests/test_apply_patches.py / tests/test_bash_write.py / tests/test_bootstrap.py / tests/test_canon_section.py / tests/test_ci_workflow.py / tests/test_cjk_git_paths.py / tests/test_claude_md.py / tests/test_declared_in_is_an_identity.py / tests/test_dependency_ceiling.py / tests/test_edit_result.py / tests/test_evidence_isolation.py / tests/test_friction_heading.py / tests/test_g1_guard.py / tests/test_g1_verify.py / tests/test_gate.py / tests/test_gate_boundaries.py / tests/test_gitlink_downstream_cycle.py / tests/test_install.py / tests/test_intercepts.py / tests/test_known_items_regression.py / tests/test_leak_scan.py / tests/test_ledger_verify.py / tests/test_line_ending_parity.py / tests/test_manifest.py / tests/test_mcp_server.py / tests/test_non_source_list_parity.py / tests/test_portable_output_encoding.py / tests/test_r5_mounts.py / tests/test_redlight.py / tests/test_research_stage.py / tests/test_scanner.py / tests/test_shadow.py / tests/test_shadow_review.py / tests/test_source_hygiene.py / tests/test_stage_defs_source.py / tests/test_stage_naming.py / tests/test_status.py / tests/test_sync.py / tests/test_ticket_dirs_are_md_only.py / tests/test_ticket_lookup.py / tests/test_ticket_path_parity.py / tests/test_upstream_manifest.py / tests/test_user_layer.py / tests/test_verify_gates.py  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests green (run 事實未知) under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests orphaned under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
rules defined: R1 R2 R3 R4 R5 R6 R7 R8 R9  (source: gate.rule_codes())
```

## 9. 四項完成判定

| 項 | 判定 | 依據 |
|---|---|---|
| (a) 固定全套 exit 0、failed 0 | **成立** | 第 5 節摘要行原文 |
| (b) 3d 的 13 支全部轉綠 | **成立** | 失敗清單為空;status red (無) |
| (c) 真實 session 新事實全部合格,且依三類邊界無絕對路徑 / 無本機使用者名稱 | **成立** | 第 7 節:override_ini、inifilename、inipath、兩個雜湊、pytest 9.1.1、anyio 4.15.0 known_dist、None 0、other 0;使用者名稱 0 筆 |
| (d) 帳本 H4 → H5 只追加 | **成立** | 第 6 節前段雜湊相符 |

## 10. 尚未證明

1. **TOCTOU**:執行中途改設定再改回,雜湊比對看不到(〈二十九〉3)。
2. **版本未在 dependency 結構性固定**(〈三十一〉裁決 2):`pyproject.toml` 只有 `pytest>=8.0,<10`,anyio 沒有宣告;換環境若取得其他版本 ⇒ fail-closed(無法退紅,不會假綠)。
3. **非 ini 的 CLI 選項以 pytest 版本鎖住**:(xiii) 的前提是「3d 規劃檔 P1 對 pytest 9.1.1 的盤點完整」;那份盤點是讀原始碼推得的,沒有對全部選項窮舉(規劃檔 P5 第 7 點)。
4. **git 子程序的行為只在本機驗證**:`git hash-object` 依 .gitattributes / `core.autocrlf` 正規化,只在這台 Windows 機器、這組 git 設定下驗過(真實 session 兩個雜湊相符)。其他 autocrlf 組合、其他平台未驗。
5. **鎖步測試依賴 repo 的 git 歷史可讀**:淺層 clone 以外的情形未驗;沒有 git 或 HEAD 不可讀時,它會失敗(依裁決 3,不 skip)。
6. 每一次模擬執行的 sessionfinish 現在多跑 2 個 git 子程序;本次全套耗時 149.54s,上一次(3d)147.44s,只是一次觀測,不是效能結論。
7. 3d 的 13 支轉綠「為了對的理由」:只從失敗清單為空推得「不再是 `"true"`」,沒有逐支記錄是哪一條新條件判定的(5d 可逐支追)。
8. CLEAN / REAL 層未證明。
