# M1-a Station 3 第一刀 —— 修正前 baseline(固定指令)

**這份檔案的身分**:Station 3 第一刀的正式報告,**進版控**
(位置依據:`docs/agents/handover.md:34`「**回報檔一律進版控**(`docs/audits/`)」)。
路徑一律寫 repo 相對路徑;執行機器名寫 `<執行機器>`。

| | |
|---|---|
| **撰寫時點** | 2026-10-02T13:29:26Z(寫入當下) |
| **baseline HEAD** | `4be8eeb01ce2a695d1170576432adc7b5f6dd3b2` |
| **本輪 commit** | 本報告所在的 commit;SHA 無法寫進自己 —— 見該 commit |

---

## 【給裁決者】

1. 用固定指令 `python -X utf8 -m pytest -q` 跑了一次 baseline:**exit code 0**,`1912 passed, 3 skipped, 3 xfailed in 146.72s (0:02:26)`,走「baseline 全過」分支。
2. 帳本(本機紅綠紀錄檔,不進版控)新增 46 筆,**全部 `ticket_id = "145"`、全部 green**;status.py 顯示票 145 底下 red 0 / green 46。
3. 票 145 第 3 行改為「動工 —— Station 3 進行中」,新增〈十二〉記錄 baseline 與 CI 指令差異;紅燈測試尚未寫。
4. 要你決定:票 145〈十〉第 386 行仍寫「未動工 —— 與票頭第 3 行一致」,現在已與第 3 行矛盾;本輪授權只改 Station 3 那一列,所以**未動它** —— A 下一輪一併改,還是 B 現在單獨授權一刀。
5. 不決定的話:票面〈十〉那一句會繼續與第 3 行不一致(機器只讀第 3 行,不受影響;人讀會困惑)。

### 最低必要內容

| # | 項目 | 值 |
|---|---|---|
| 1 | 步驟 0 | `.dev/pipeline.json`、`.dev/test-runs.jsonl` **皆未追蹤**、**皆命中** `.gitignore:30:/.dev/*` |
| 2 | baseline | exit code **0**;`1912 passed, 3 skipped, 3 xfailed in 146.72s (0:02:26)`;分支:**baseline 全過** |
| 3 | 新增 test-runs | **46** 行;`ticket_id` 全為 `"145"`:**是**;red **0** / green **46** / 其他 **0** |
| 4 | status.py | `tests red under ticket 145: (無)`;`tests green under ticket 145:` 46 檔(原文見證據段) |
| 5 | 與 CI 差異 | `-X utf8`(本次有、CI 無);`--ignore=tests/test_known_items_regression.py`(CI 有、本次無);OS / 前置步驟不同;兩邊皆無 `--deselect`、皆無額外環境變數 |
| 6 | 票 145 新第 3 行 | `**狀態**:動工 —— Station 3 進行中(baseline 已量,紅燈未寫);Station 4 未開始。` |
| 7 | 最終 numstat / check | 只印在視窗(不進本檔) |
| 8 | commit / `0 1` / 樹 | 發生在本檔 commit 之後,只在視窗回報 |
| 9 | 執行機器 hostname | 只在視窗 |
| 10 | push / 紅燈測試 / 改測試或原始碼 / 改 pipeline | **NO / NO / NO / NO** |

---

## 【給裁決助手】證據

### 步驟 0 —— operational 檔追蹤狀態(pytest 之前)

```
$ git ls-files .dev/pipeline.json
(無輸出)
$ git ls-files .dev/test-runs.jsonl
(無輸出)
$ git check-ignore -v .dev/pipeline.json
.gitignore:30:/.dev/*	.dev/pipeline.json
$ git check-ignore -v .dev/test-runs.jsonl
.gitignore:30:/.dev/*	.dev/test-runs.jsonl
```

⇒ 兩檔皆**未追蹤**、皆**命中 ignore**。走「兩者皆非 tracked」分支。

### 步驟 1 —— preflight

```
$ git fetch origin
(無輸出)
$ git rev-list --left-right --count origin/master...HEAD
0	0
$ git rev-parse HEAD
4be8eeb01ce2a695d1170576432adc7b5f6dd3b2
$ git status --porcelain
(無輸出)
```

### 步驟 2 —— pipeline.json

```
$ cat -A .dev/pipeline.json
{$
  "current_stage": "tickets",$
  "feature": "framework-updates",$
  "ticket_id": "145",$
  "updated": "2026-10-02"$
}
```

### 步驟 3 —— test-runs before

```
$ sha256sum .dev/test-runs.jsonl
d6c0da4d173388dc7d58ba30023c67620309059cd2bd1bc854faa45dc766f4ae *.dev/test-runs.jsonl
$ wc -c -l .dev/test-runs.jsonl
  1997 540862 .dev/test-runs.jsonl
```

L0 = 1997。

### 步驟 4 —— 環境

```
$ python --version
Python 3.11.9
$ python -m pytest --version
pytest 9.1.1
$ hostname
<執行機器>
```

(hostname 原值只在視窗回報,此處遮罩。)

### 步驟 5 —— CI 的 pytest 指令原文

```
$ grep -rn pytest .github/workflows
.github/workflows/tests.yml:19:  pytest:
.github/workflows/tests.yml:74:          python -m pytest -q \
.github/workflows/tests.yml:97:          python -m pytest --collect-only -q \
$ sed -n 72,76p .github/workflows/tests.yml
      - name: 跑測試
        run: |
          python -m pytest -q \
            --ignore=tests/test_known_items_regression.py

$ sed -n 95,99p .github/workflows/tests.yml
      - name: 收集清單(票 85)
        run: |
          python -m pytest --collect-only -q \
            --ignore=tests/test_known_items_regression.py

$ grep -n -E env:\|PYTHON\|run:\|runs-on\|python-version .github/workflows/tests.yml
20:    runs-on: ubuntu-latest
47:          python-version: '3.11'
50:        run: python -m pip install -e ".[dev]"
57:        run: sh bootstrap.sh
73:        run: |
96:        run: |
113:        run: python .claude/portable/verify_gates.py "${{ runner.temp }}/verify-gates"
```

`.github/workflows/` 只有 `tests.yml` 一檔。無 `env:` 區塊。
(`tests.yml` 的註解記載 `--deselect` 已於票 137 移除;票 139 立案時所述「兩處各有一行 `--deselect`」已不成立 —— 只記錄。)

### 步驟 6 —— baseline

```
$ date -u +%Y-%m-%dT%H:%M:%SZ
2026-10-02T13:25:31Z
$ python -X utf8 -m pytest -q
...(進度點略)...
1912 passed, 3 skipped, 3 xfailed in 146.72s (0:02:26)

[exited with code 0]
```

只跑這一次;未加任何 `--ignore` / `--deselect` / `-k` / 檔案參數。
執行方式:背景執行(避免前景逾時中斷),完成通知回報 `exit code 0`。
摘要行之前的輸出為進度點與 3 筆 XFAIL 說明(`tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[...]`)。

⇒ **exit code == 0 ⇒ baseline 全過分支。**

### 步驟 7 —— test-runs after

```
$ sha256sum .dev/test-runs.jsonl
460f714f02c527081d8242520021f611ad0a62c52e3ae592977ae7fc7be7684c *.dev/test-runs.jsonl
$ wc -c -l .dev/test-runs.jsonl
  2043 552165 .dev/test-runs.jsonl
```

新增行數 = 2043 − 1997 = **46**。

### 步驟 8 —— 新增紀錄驗證

以唯讀檔案讀取工具讀第 1998–2043 行(事前授權),逐筆讀過:46 筆全部 `"ticket_id": "145"`、全部 `"result": "green"`、`failed_tests` 全為 `[]`。
交叉核對(不依賴逐筆目視):

```
$ grep -c -F \"ticket_id\":\ \"145\" .dev/test-runs.jsonl
46
```

(baseline 之前帳本中 `"145"` 為 0 筆的依據:步驟 3 的 before 指紋 `d6c0da4d…f4ae` / 540862 / 1997,
與 Station 2 開始時(2026-10-02T12:11:19Z,票 145 尚不存在)量到的指紋**逐字相同** ⇒ 帳本在票 145 存在之後沒有任何寫入 ⇒ 46 筆全部是本次新增。)

| 計數 | 筆數 |
|---|---|
| 新增總筆數 | 46 |
| `ticket_id == "145"` | 46 |
| `ticket_id != "145"` | 0 |
| `result == "red"` | 0 |
| `result == "green"` | 46 |
| 其他 / 缺欄 | 0 |

`python .claude/portable/status.py --root .` 的 Evidence 與 Derived 區塊原文
(**一處遮罩**:`report:` 行的 HEAD 時間含本地時區偏移,以 `<本地時間>` 代替;其餘逐字):

```
=== Evidence ===
test-runs: 本票(每檔最新一筆)red 0 / green 46;最後一筆 tests/test_verify_gates.py=green @ 2026-10-02T13:27:56.459505+00:00;全套結果:未記錄(帳本不記全套)  (source: .dev/test-runs.jsonl)
intercepts (當月): 1 筆  (source: .dev/intercepts-2026-10.jsonl)
intercepts (最新存在月): 2026-10 1 筆;末筆 R7@2026-10-02T12:12:16.405577+00:00  (source: .dev/intercepts-2026-10.jsonl)
exemptions: 總 281 筆;granted 240 筆;blocked 1 筆;未記錄(無此欄)40 筆;最後一筆 2026-09-24T08:17:49.073745+00:00  (source: .dev/gate-exemptions.jsonl)
provenance: 未記錄(上游無此檔屬正常)  (source: .dev/provenance.jsonl)
report: 2026-09-24T084909Z-ticket137-status-line.md;HEAD <本地時間>;回報後 2 筆  (source: .dev/reports/)

=== Derived ===
src write allowed in tickets: no  (source: gate.stage_allows_src_write() <- .agents/pipeline-stages.yaml)
tests red under ticket 145: (無)  (source: .dev/test-runs.jsonl 每檔最新一筆)
tests green under ticket 145: tests/test_adr_numbering.py / tests/test_adr_numbers_resolve_upstream.py / tests/test_apply_patches.py / tests/test_bash_write.py / tests/test_bootstrap.py / tests/test_canon_section.py / tests/test_ci_workflow.py / tests/test_cjk_git_paths.py / tests/test_claude_md.py / tests/test_declared_in_is_an_identity.py / tests/test_dependency_ceiling.py / tests/test_edit_result.py / tests/test_evidence_isolation.py / tests/test_friction_heading.py / tests/test_g1_guard.py / tests/test_g1_verify.py / tests/test_gate.py / tests/test_gate_boundaries.py / tests/test_gitlink_downstream_cycle.py / tests/test_install.py / tests/test_intercepts.py / tests/test_known_items_regression.py / tests/test_leak_scan.py / tests/test_ledger_verify.py / tests/test_line_ending_parity.py / tests/test_manifest.py / tests/test_mcp_server.py / tests/test_non_source_list_parity.py / tests/test_portable_output_encoding.py / tests/test_r5_mounts.py / tests/test_redlight.py / tests/test_research_stage.py / tests/test_scanner.py / tests/test_shadow.py / tests/test_shadow_review.py / tests/test_source_hygiene.py / tests/test_stage_defs_source.py / tests/test_stage_naming.py / tests/test_status.py / tests/test_sync.py / tests/test_ticket_dirs_are_md_only.py / tests/test_ticket_lookup.py / tests/test_ticket_path_parity.py / tests/test_upstream_manifest.py / tests/test_user_layer.py / tests/test_verify_gates.py  (source: .dev/test-runs.jsonl 每檔最新一筆)
rules defined: R1 R2 R3 R4 R5 R6 R7 R8 R9  (source: gate.rule_codes())
```

pytest 後工作樹:

```
$ git status --porcelain
(無輸出)
```

### 步驟 9 —— baseline 指令 vs CI 指令(只列)

| 項 | 本次 baseline | CI(`tests.yml:73-75`) |
|---|---|---|
| 指令 | `python -X utf8 -m pytest -q` | `python -m pytest -q --ignore=tests/test_known_items_regression.py` |
| 直譯器旗標 | `-X utf8` | 無 |
| 排除項 | 無 | `--ignore=tests/test_known_items_regression.py` |
| `--deselect` | 無 | 無 |
| 環境變數 | 未設定額外變數 | 無 `env:` 區塊 |
| 作業系統 | Windows(`<執行機器>`) | `ubuntu-latest`(`:20`) |
| Python | 3.11.9 | `'3.11'`(`:47`) |
| 前置步驟 | 無 | `pip install -e ".[dev]"`(`:50`)、`sh bootstrap.sh`(`:57`) |

### 步驟 10 —— 票 145 改動

| 項 | 改動 |
|---|---|
| a | 第 3 行改為 `**狀態**:動工 —— Station 3 進行中(baseline 已量,紅燈未寫);Station 4 未開始。`;舊第 3 行併入票頭既有 F-036 block(`- 狀態(舊,第二代):~~…~~`,以 `>` 開頭) |
| b | 第 4 行時鐘未動 |
| c | 新增〈十二、Station 3 baseline(固定指令)〉:固定指令、裁決句、12.1 結果、12.2 帳本指紋與計數、12.3 追蹤狀態、12.4 與 CI 差異 |
| d | 〈十〉表格 Station 3 列改為 `IN PROGRESS(baseline 已量,紅燈未寫)` |

**e. 檢查**

```
$ grep -n ^\*\*狀態\*\* docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
3:**狀態**:動工 —— Station 3 進行中(baseline 已量,紅燈未寫);Station 4 未開始。
$ grep -n ^\*\*時鐘\*\* docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
4:**時鐘**:2026-10-02 —— 自此時點起,任何依 status aggregate 判斷「沒有未解紅燈」的行為,都暴露於已證明的 partial-selection false-green failure mode。此日期為 Jeff 於 2026-10-02 的排程裁決,不是由證據唯一推出;痛點最早的證據為票 139(2026-09-13)。
$ grep -c -F <磁碟代號>: docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
0
$ grep -c -F <執行機器> docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
0
$ grep -c -F <本機使用者名> docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
0
```

(**後三條指令經遮罩**:實際搜尋字串分別是磁碟代號加冒號、實際 hostname、實際使用者名;輸出 `0` 未改動。)

PRIVATE-CONTEXT CHECK:**PASS** —— 本輪新增文字只來自 baseline 量測、帳本、CI 檔與裁決原文;
未帶入旅行、住宿、個人背景。`status.py` 原文中含本地時區偏移的一個時間值已遮罩(見步驟 8)。

**發現的不一致(未改,待裁)**:

```
$ grep -n -F 未動工 docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
17:> - 狀態(舊,第二代):~~`立案(時鐘已定 2026-10-02);未動工 —— Station 2 DONE、Station 3 NOT STARTED。`~~
386:Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 立案、時鐘已定(2026-10-02)、未動工 —— 與票頭第 3 行一致,不代表 Station 3 已開工。
```

第 17 行是 provenance(正確)。**第 386 行**(〈十〉)仍描述舊 lifecycle,且自稱「與票頭第 3 行一致」—— 已不成立。
本輪授權的〈十〉改動只有 Station 3 那一列(d),故未改。

---

## 尚未證明 / 本輪未做

1. **紅燈測試未寫**(本輪範圍外)。
2. **票 145〈十〉第 386 行與第 3 行不一致**(見上)—— 待裁。
3. **baseline 的「全套」事實只在本票與本報告**:帳本只有 46 筆 per-file green;`1912 passed, 3 skipped, 3 xfailed` 與 exit code 0 **不在帳本裡**(`status.py`:「全套結果:未記錄(帳本不記全套)」)。這正是本票要修的缺口,本輪不處理。
4. **帳本新增的 46 筆只存在本機**(`.dev/` 被 ignore);換機或清除後只剩本票〈十二〉的指紋與計數。
5. **上一輪的 residual 仍在**:`_ticket()` direct probe 未執行。本輪 `status.py` 的 Ticket 區塊讀到票 145 第 3 行(baseline 前的舊值),但那是 `render()` 的輸出,不是對 `_ticket()` 的直接探針。
6. **CI 對本 commit 的結果**:本輪不推、不查。

---

## 六站狀態

| 站 | 狀態 |
|---|---|
| Station 1 — Spec | PASS / CLOSED |
| Station 2 — Ticket | DONE |
| Station 3 — Red-light | IN PROGRESS(baseline 已量,紅燈未寫) |
| Station 4 — Implementation | NOT STARTED |
| Station 5 — Review | NOT STARTED |
| Station 6 — Acceptance | NOT STARTED |
