# 票 145 Station 3g 紅燈證據

- 日期:2026-10-03(本機時間;帳本時戳為 UTC 2026-10-04)
- 對象:S3G1 `2737e02c64b88f4d0a39bdafbea2f3776993cf2b`(上一個 commit 是 S3G0 `560f618560ddac1a34e0e835b99a1e3a5cc7eda5`)
- 合約:票 145〈四十八〉48.1;預期集合:〈四十八〉48.2
- 規劃:`docs/audits/2026-10-03-m1a-station3g-redlight-plan.md` P6

## 【給裁決者】

1. 33 支新測試已寫好並提交,只加在測試檔尾端;產品程式一行都沒改。
2. 固定全套跑了一次:紅的恰好是預期的 26 支,其餘 2058 支(含 7 支「現在就該綠」的新測試)全綠。
3. 每一支紅都紅在預期的那一行,對照組全部通過,所以不是「測試自己壞掉」才紅的。
4. 測試帳本(每次跑測試留下的紀錄)只往後加了一筆,舊內容的指紋(sha256,內容變一個字就不同)完全沒變。
5. 要你決定:是否驗收 3g,並切到 implement 讓 4g 開工。不驗收的話,這 26 支紅會一直留著,CI 也維持紅。

## 【給裁決助手】

### 1. 前置(S3G0 上;各自單獨執行)

```
$ git status --porcelain
(無輸出)
$ git rev-parse HEAD
560f618560ddac1a34e0e835b99a1e3a5cc7eda5
$ cat .dev/pipeline.json
{
  "current_stage": "tickets",
  "feature": "framework-updates",
  "ticket_id": "145",
  "updated": "2026-10-02"
}
$ wc -c .dev/test-runs.jsonl
732856 .dev/test-runs.jsonl
$ wc -c .dev/test-sessions.jsonl
7751802 .dev/test-sessions.jsonl
$ wc -l .dev/test-runs.jsonl
2733 .dev/test-runs.jsonl
$ wc -l .dev/test-sessions.jsonl
21 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl
ec6bc011d51536f5d95058ebf6cd2da70adebc8d06c865822f3b4c5df831a5fb *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
33b920e92d34e5007432922ebc03ae8325d486ffc4c63fb522d438e21866b605 *.dev/test-sessions.jsonl
$ wc -l tests/test_redlight.py
2144 tests/test_redlight.py
$ wc -l tests/test_status.py
2858 tests/test_status.py
$ wc -l tests/test_verify_gates.py
291 tests/test_verify_gates.py
```

由此記錄:L9r = 2733、L9s = 21、N_r = 2144、N_s = 2858、N_v = 291。

### 2. S3G1 提交前檢查

```
$ python -X utf8 -m py_compile tests/test_redlight.py
(無輸出)
$ python -X utf8 -m py_compile tests/test_status.py
(無輸出)
$ python -X utf8 -m py_compile tests/test_verify_gates.py
(無輸出)
$ python -X utf8 -m py_compile tests/test_host_evidence_policy.py
(無輸出)
$ git diff --cached --name-only
.agents/portable-manifest.txt
docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
tests/test_host_evidence_policy.py
tests/test_redlight.py
tests/test_status.py
tests/test_verify_gates.py
$ git diff --cached --check
(無輸出)
```

`git diff --cached -U0` 的 hunk 標頭(各檔恰一個 hunk,沒有任何 `-` 開頭的內容行):

```
tests/test_redlight.py       @@ -2144,0 +2145,363 @@ class TestIdentifierFullMatch:
tests/test_status.py         @@ -2858,0 +2859,159 @@ class TestDebuggerModeLocks:
tests/test_verify_gates.py   @@ -291,0 +292,24 @@ class TestScenarioR4LeavesTheTargetClean:
```

`git diff --cached -U0 -- .agents/portable-manifest.txt` 全文:

```
diff --git a/.agents/portable-manifest.txt b/.agents/portable-manifest.txt
index 1ef4263..cc644b7 100644
--- a/.agents/portable-manifest.txt
+++ b/.agents/portable-manifest.txt
@@ -220,0 +221 @@ tests/test_adr_numbers_resolve_upstream.py skip
+tests/test_host_evidence_policy.py skip
```

提交與確認:

```
$ git commit -F .scratch/m1a-s3g/s3g-1-msg.txt
[master 2737e02] test(145): M1-a Station 3g-1 —— Host evidence policy 紅燈(33 支)
 6 files changed, 717 insertions(+), 3 deletions(-)
 create mode 100644 tests/test_host_evidence_policy.py
$ git rev-parse HEAD
2737e02c64b88f4d0a39bdafbea2f3776993cf2b
$ git status --porcelain
(無輸出)
```

`3 deletions(-)` 全部出自票 145:狀態行、〈十〉3g 列、lifecycle 句的取代;舊值依 F-036 保存在票內。三個測試檔都沒有刪除行(見上方 hunk)。

### 3. 固定全套(在 S3G1 上只跑一次)

指令:`python -X utf8 -m pytest -q > <session scratch>/s3g-run.txt 2>&1`,exit 1。

摘要行原文:

```
26 failed, 2058 passed, 3 skipped, 3 xfailed in 243.99s (0:04:03)
```

collected 2090(26 + 2058 + 3 + 3;status 也顯示 collected 2090)。

FAILED 行原文(輸出檔第 737–762 行):

```
FAILED tests/test_host_evidence_policy.py::test_the_committed_policy_matches_the_committed_pyproject
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_a_repo_without_a_policy_is_not_full_coverage
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_uncommitted_policy_state_is_not_full_coverage[worktree-only]
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_uncommitted_policy_state_is_not_full_coverage[worktree-differs]
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_uncommitted_policy_state_is_not_full_coverage[staged-only]
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_uncommitted_policy_state_is_not_full_coverage[deleted-in-worktree]
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[malformed-json]
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[unknown-schema]
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[unknown-version]
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[unknown-key]
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[missing-field]
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_a_policy_outside_the_canonical_path_is_not_full_coverage
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_the_producer_records_the_policy_identity
FAILED tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_environment_mismatch_is_not_full_coverage[override]
FAILED tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_environment_mismatch_is_not_full_coverage[narrowed-dist]
FAILED tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[strict-markers]
FAILED tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[strict-config]
FAILED tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[o-flag]
FAILED tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[override-ini-eq]
FAILED tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[no-addopts]
FAILED tests/test_redlight.py::TestAddoptsDerivation::test_g3_a_policy_disagreeing_with_the_committed_addopts_is_not_full_coverage
FAILED tests/test_status.py::TestEvidencePolicyChain::test_g3_no_policy_does_not_retire_a_known_red
FAILED tests/test_status.py::TestEvidencePolicyChain::test_g3_an_uncommitted_policy_does_not_retire_a_known_red[worktree-only]
FAILED tests/test_status.py::TestEvidencePolicyChain::test_g3_an_uncommitted_policy_does_not_retire_a_known_red[worktree-differs]
FAILED tests/test_status.py::TestEvidencePolicyChain::test_g3_a_policy_environment_mismatch_does_not_retire_a_known_red
FAILED tests/test_verify_gates.py::test_every_evidence_policy_scenario_is_wired
```

與 48.2 的 26 支 behavior-red 對照:**逐支相同,沒有多、也沒有少**。

### 4. 33 支逐支表

- 「實際結果」:帳本最後一行 `outcomes` 的值。
- 「真實 producer」:是否經真實 `tests/conftest.py` 驅動。
- 「失敗行」:pytest 輸出裡的位置與 `E` 行原文。

| # | nodeid | 分類 | 實際結果 | 真實 producer | 失敗行(實際斷言) |
|---|---|---|---|---|---|
| 1 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_a_repo_without_a_policy_is_not_full_coverage` | behavior-red | failed | 是 | `test_redlight.py:2295` `assert broken != "true"` → `AssertionError: true` |
| 2 | `…::test_g3_an_uncommitted_policy_state_is_not_full_coverage[worktree-only]` | behavior-red | failed | 是 | `:2325` `assert broken != "true"` → `true` |
| 3 | `…[worktree-differs]` | behavior-red | failed | 是 | `:2325` 同上 |
| 4 | `…[staged-only]` | behavior-red | failed | 是 | `:2325` 同上 |
| 5 | `…[deleted-in-worktree]` | behavior-red | failed | 是 | `:2325` 同上 |
| 6 | `…::test_g3_an_unknown_policy_document_is_not_full_coverage[malformed-json]` | behavior-red | failed | 是 | `:2341` `assert broken != "true"` → `true` |
| 7 | `…[unknown-schema]` | behavior-red | failed | 是 | `:2341` 同上 |
| 8 | `…[unknown-version]` | behavior-red | failed | 是 | `:2341` 同上 |
| 9 | `…[unknown-key]` | behavior-red | failed | 是 | `:2341` 同上 |
| 10 | `…[missing-field]` | behavior-red | failed | 是 | `:2341` 同上 |
| 11 | `…::test_g3_a_policy_outside_the_canonical_path_is_not_full_coverage` | behavior-red | failed | 是 | `:2354` `assert broken != "true"` → `true` |
| 12 | `…::test_g3_the_producer_records_the_policy_identity` | behavior-red | failed | 是 | `:2372` `assert isinstance(ep, dict)` → `isinstance(None, dict)` 為 False |
| 13 | `…::test_g3_policy_content_is_not_read_from_the_worktree` | regression-lock | passed | 是 | — |
| 14 | `…::test_g3_a_matching_committed_policy_is_full_coverage` | regression-lock | passed | 是 | — |
| 15 | `tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_cannot_widen_the_capability_boundary[python]` | regression-lock | passed | 是 | — |
| 16 | `…[pytest]` | regression-lock | passed | 是 | — |
| 17 | `…[dist]` | regression-lock | passed | 是 | — |
| 18 | `…[config-file]` | regression-lock | passed | 是 | — |
| 19 | `…::test_g3_a_policy_environment_mismatch_is_not_full_coverage[override]` | behavior-red | failed | 是 | `:2465` `assert broken != "true"` → `true` |
| 20 | `…[narrowed-dist]` | behavior-red | failed | 是 | `:2465` 同上 |
| 21 | `tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[strict-markers]` | behavior-red | failed | 否(純函式) | `:2491` `AttributeError: module 'redlight_under_test' has no attribute 'addopts_overrides'` |
| 22 | `…[strict-config]` | behavior-red | failed | 否 | `:2491` 同上 |
| 23 | `…[o-flag]` | behavior-red | failed | 否 | `:2491` 同上 |
| 24 | `…[override-ini-eq]` | behavior-red | failed | 否 | `:2491` 同上 |
| 25 | `…[no-addopts]` | behavior-red | failed | 否 | `:2491` 同上 |
| 26 | `…::test_g3_a_policy_disagreeing_with_the_committed_addopts_is_not_full_coverage` | behavior-red | failed | 是 | `:2507` `assert broken != "true"` → `true` |
| 27 | `tests/test_host_evidence_policy.py::test_the_committed_policy_matches_the_committed_pyproject` | behavior-red | failed | 否(讀本 repo HEAD) | `test_host_evidence_policy.py:43` `assert proc.returncode == 0` → `assert 128 == 0`;stderr `fatal: path '.agents/evidence-policy.json' does not exist in 'HEAD'` |
| 28 | `tests/test_status.py::TestEvidencePolicyChain::test_g3_no_policy_does_not_retire_a_known_red` | behavior-red | failed | 是 | `test_status.py:2961` `assert "tests/test_x.py" in got["red"]` → `{'red': '(無)', 'green': 'tests/test_x.py', 'orphaned': '(無)'}` |
| 29 | `…::test_g3_an_uncommitted_policy_does_not_retire_a_known_red[worktree-only]` | behavior-red | failed | 是 | `:2983` 同上(red `(無)`、green `tests/test_x.py`) |
| 30 | `…[worktree-differs]` | behavior-red | failed | 是 | `:2983` 同上 |
| 31 | `…::test_g3_a_policy_environment_mismatch_does_not_retire_a_known_red` | behavior-red | failed | 是 | `:3001` 同上 |
| 32 | `…::test_g3_a_matching_committed_policy_retires_the_red` | regression-lock | passed | 是 | — |
| 33 | `tests/test_verify_gates.py::test_every_evidence_policy_scenario_is_wired` | behavior-red | failed | 否 | `test_verify_gates.py:313` `assert isinstance(table, dict)` → `verify_gates 沒有 EVIDENCE_SCENARIOS:淨室的兩正三負沒有接線` |

表中 `…` 為該列上方同類別的完整前綴。

**紅在正確的那一行**:
- 有對照組的測試(#1–#11、#19、#20、#26),失敗行都是**破壞組**的斷言。對照組的斷言排在前面,而且已經通過。
- 鏈條測試(#28–#31)在檢查 status 紅綠之前,`_g_assert_scenario` 的情境斷言(R1 為 B、R2 合格且為 A)已全部通過,失敗點在 status 的 red 行。
- #31 的 `override_ini == ["strict_markers=true"]` 情境斷言也已通過。

### 5. 帳本(各自單獨執行)

```
$ head -c 732856 .dev/test-runs.jsonl > <session scratch>/r9.bin
$ head -c 7751802 .dev/test-sessions.jsonl > <session scratch>/s9.bin
$ sha256sum <session scratch>/r9.bin
ec6bc011d51536f5d95058ebf6cd2da70adebc8d06c865822f3b4c5df831a5fb *<session scratch>/r9.bin
$ sha256sum <session scratch>/s9.bin
33b920e92d34e5007432922ebc03ae8325d486ffc4c63fb522d438e21866b605 *<session scratch>/s9.bin
$ wc -l .dev/test-runs.jsonl
2780 .dev/test-runs.jsonl
$ wc -l .dev/test-sessions.jsonl
22 .dev/test-sessions.jsonl
```

- 前段 sha256 = H9r / H9s ⇒ 只追加。
- test-runs:2733 → 2780(+47)。本次 session 涵蓋的測試檔是 S4F1 那次的 46 個,加上新檔 `tests/test_host_evidence_policy.py`,共 47 個,每檔一行。
- test-sessions:21 → 22(+1)。

**帳本最後一行**(以 `tail -n 1` 寫到 `<session scratch>/last-session.jsonl` 後 Grep):
- `outcomes` 值為 `"failed"` 的鍵**恰 26 個**,與第 3 節的 FAILED 清單逐支相同。
- 7 支 regression-lock 的值都是 `"passed"`:

```
"tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_policy_content_is_not_read_from_the_worktree": "passed"
"tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_a_matching_committed_policy_is_full_coverage": "passed"
"tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_cannot_widen_the_capability_boundary[python]": "passed"
"tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_cannot_widen_the_capability_boundary[pytest]": "passed"
"tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_cannot_widen_the_capability_boundary[dist]": "passed"
"tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_cannot_widen_the_capability_boundary[config-file]": "passed"
"tests/test_status.py::TestEvidencePolicyChain::test_g3_a_matching_committed_policy_retires_the_red": "passed"
```

### 6. status(`python .claude/portable/status.py --root .`,節錄原文)

```
test-runs: 本票 red 4 / green 43 / run 事實未知 0 / orphaned 0 / schema 不合格 run 0;最後一筆 tests/test_verify_gates.py=red @ 2026-10-04T01:26:46.362153+00:00;最近一次 run:B(exit 1;collected 2090 / deselected 0 / passed 2058 / failed 26 / skipped 3)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl)
tests red under ticket 145: tests/test_host_evidence_policy.py / tests/test_redlight.py / tests/test_status.py / tests/test_verify_gates.py  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests orphaned under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
```

red 恰為本輪新增紅燈所在的 4 個檔;最近一次 run 為 B(collected 2090)。

### 7. 限制與未證明

- 本機只驗 Windows。POSIX 上未實測,也沒有預期差異:本輪沒有平台相依的案例。
- 新測試的正控已固定版本事實(Python 3.11、pytest 9.1.1)。既有正控的 driver 固定屬 4g 的授權(〈四十八〉48.1 第 5 點),本輪未動。
- #33 只證明情境有接線;五情境的實際結果待 4g 本機實跑 `verify_gates.py`(48.1 第 7 點)。
- 未 push;未改產品碼與 `.dev/pipeline.json`;未執行 `verify_gates.py`。
