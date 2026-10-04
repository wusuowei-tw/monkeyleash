# 票 145 Station 3g-1b 紅燈證據

- 日期:2026-10-04
- 對象:S3G1B `83258dd9ab415a793eaf2b140a9e34c5b91069f2`(上一個 commit 是 S3G2 `7a15ea081da1bf23cc79e04aef76065438f65219`)
- 合約:票 145〈五十〉50.1;預期集合:〈四十八〉48.2 的 26 支 behavior-red + 〈五十〉50.3 的 9 支
- 固定全套在 S3G1B 上**跑了兩次**,兩次分開記錄:
  - (a) 第一次:工作樹含 3 個外來 docs 變更 ⇒ **不作為正式證據**,只照錄摘要行;
  - (b) 第二次(重跑):外來變更以 `git stash` 收起、工作樹乾淨 ⇒ **正式 red-light evidence**。
  - 依據:Jeff 對 stop 報告(`.dev/reports/2026-10-04T112500Z-ticket145-station3g-1b-stop.md`)的裁決 B。

## 【給裁決者】

1. 第一次全套時工作樹裡混了 3 個別人改的文件,所以那次只當參考;這次先把它們暫時收起來(git stash,像把東西先放進抽屜),在乾淨的狀態重跑了一次。
2. 重跑結果與預期完全相同:35 支紅,恰好是舊的 26 支加新的 9 支;其餘 2058 支全綠。
3. 跑之前與跑之後,工作樹都是乾淨的,證明執行期間沒有人動過檔案。
4. 測試帳本只往後加,舊內容的指紋(sha256,內容變一個字就不同)沒有變。
5. 要你決定:是否驗收 3g-1b,讓 4g 開工。不驗收的話,這 35 支紅會一直留著,CI 也維持紅。

## 【給裁決助手】

### 1. 第一次執行(不作為正式證據)

- 對象:S3G1B;工作樹當時含 ` M docs/agents/friction-log.md`、`?? docs/tickets/framework-updates/146-claude-code-enforcement-integrity.md`、`?? docs/tickets/framework-updates/147-turn-end-check-via-settings-stop-hook.md`。
- 這 3 個變更不是 Station 3g-1b 的工作階段寫的。執行期間已存在:I3 的失敗輸出中,安裝器寫出的 `docs/decisions-pending.md` 列出了票 146、147 兩檔。
- 摘要行原文(exit 1):

```
35 failed, 2058 passed, 3 skipped, 3 xfailed in 351.04s (0:05:51)
```

- 帳本:test-runs 2780 → 2827、test-sessions 22 → 23。
- 完整紀錄在上述 stop 報告。本報告**不以它為證據**。
- S3G1B 的提交前檢查(py_compile、`git diff --cached --check`、各檔恰一個無刪除行的 hunk)也記在 stop 報告,本報告不重抄。

### 2. 前置(S3G1B 上,第二次執行之前;各自單獨執行)

```
$ git rev-parse HEAD
83258dd9ab415a793eaf2b140a9e34c5b91069f2
$ cat .dev/pipeline.json
{
  "current_stage": "tickets",
  "feature": "framework-updates",
  "ticket_id": "145",
  "updated": "2026-10-02"
}
$ git status --porcelain
 M docs/agents/friction-log.md
?? docs/tickets/framework-updates/146-claude-code-enforcement-integrity.md
?? docs/tickets/framework-updates/147-turn-end-check-via-settings-stop-hook.md
$ wc -c .dev/test-runs.jsonl
761554 .dev/test-runs.jsonl
$ wc -c .dev/test-sessions.jsonl
9222325 .dev/test-sessions.jsonl
$ wc -l .dev/test-runs.jsonl
2827 .dev/test-runs.jsonl
$ wc -l .dev/test-sessions.jsonl
23 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl
52548c1e068f857dd47d9a856503efdc1c923b978d8d2fe318e21771697c6dc2 *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
79050cac5e3fb56f6454bb78ceb1266c0e1c170646f0063d66848c493b13aa80 *.dev/test-sessions.jsonl
```

- 由此記錄:B11r = 761554、B11s = 9222325、L11r = 2827、L11s = 23;H11r / H11s 為上面兩個 sha256。
- 程序註記:本節後 6 條唯讀查詢(`wc` ×4、`sha256sum` ×2)是在同一則訊息裡並行送出的,不是逐條。都是唯讀,結果與預期逐項相同。

### 3. 收起外來檔(Jeff 同意本次 stash)

```
$ git stash push -u -m jeff-mods-recon-20261004 -- docs/agents/friction-log.md docs/tickets/framework-updates/146-claude-code-enforcement-integrity.md docs/tickets/framework-updates/147-turn-end-check-via-settings-stop-hook.md
warning: in the working copy of 'docs/tickets/framework-updates/146-claude-code-enforcement-integrity.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'docs/tickets/framework-updates/147-turn-end-check-via-settings-stop-hook.md', LF will be replaced by CRLF the next time Git touches it
Saved working directory and index state On master: jeff-mods-recon-20261004
warning: in the working copy of 'docs/tickets/framework-updates/146-claude-code-enforcement-integrity.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'docs/tickets/framework-updates/147-turn-end-check-via-settings-stop-hook.md', LF will be replaced by CRLF the next time Git touches it
$ git stash list
stash@{0}: On master: jeff-mods-recon-20261004
$ git status --porcelain
(無輸出)
$ git rev-parse HEAD
83258dd9ab415a793eaf2b140a9e34c5b91069f2
```

外來 3 檔的內容未讀。

### 4. 固定全套(在乾淨的 S3G1B 上只跑一次;正式證據)

指令:`python -X utf8 -m pytest -q > <session scratch>/s3g1b-rerun.txt 2>&1`,exit 1。

跑完立刻:

```
$ git status --porcelain
(無輸出)
```

摘要行原文:

```
35 failed, 2058 passed, 3 skipped, 3 xfailed in 351.00s (0:05:50)
```

collected 2099(35 + 2058 + 3 + 3)。

FAILED 行原文(輸出檔第 1285–1319 行):

```
FAILED tests/test_host_evidence_policy.py::test_the_committed_policy_matches_the_committed_pyproject
FAILED tests/test_install.py::TestEvidencePolicyTemplate::test_g3_install_writes_the_template_outside_the_canonical_path
FAILED tests/test_install.py::TestEvidencePolicyTemplate::test_g3_the_template_lists_exactly_the_capability_boundary
FAILED tests/test_install.py::TestEvidencePolicyTemplate::test_g3_decisions_pending_asks_to_initialize_the_policy
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
FAILED tests/test_status.py::TestEvidencePolicyStatusLine::test_g3_status_shows_the_policy_state[uninitialized]
FAILED tests/test_status.py::TestEvidencePolicyStatusLine::test_g3_status_shows_the_policy_state[uncommitted]
FAILED tests/test_status.py::TestEvidencePolicyStatusLine::test_g3_status_shows_the_policy_state[worktree-differs]
FAILED tests/test_status.py::TestEvidencePolicyStatusLine::test_g3_status_shows_the_policy_state[unknown-schema]
FAILED tests/test_status.py::TestEvidencePolicyStatusLine::test_g3_status_shows_the_policy_state[outside-boundary]
FAILED tests/test_status.py::TestEvidencePolicyStatusLine::test_g3_status_shows_the_policy_state[valid]
FAILED tests/test_verify_gates.py::test_every_evidence_policy_scenario_is_wired
```

集合對照:

- 〈四十八〉48.2 的 26 支 behavior-red:`test_redlight.py` 20 支 + `test_host_evidence_policy.py` 1 支 + `test_status.py::TestEvidencePolicyChain` 4 支 + `test_verify_gates.py` 1 支。上表**逐支都在**。
- 〈五十〉50.3 的 9 支:`test_install.py::TestEvidencePolicyTemplate` 3 支 + `test_status.py::TestEvidencePolicyStatusLine` 6 案。上表**逐支都在**。
- 26 + 9 = 35 = FAILED 行數。**沒有多、也沒有少**。
- 與第一次執行(stop 報告)的 FAILED 集合逐條相同。

### 5. 新 9 支的實際失敗行(本次輸出)

| nodeid | 結果 | 失敗行(實際斷言) |
|---|---|---|
| `tests/test_install.py::TestEvidencePolicyTemplate::test_g3_install_writes_the_template_outside_the_canonical_path` | failed | `test_install.py:617` `AssertionError: 安裝器沒有寫 .agents/evidence-policy.template.json`(`is_file()` 為 False) |
| `…::test_g3_the_template_lists_exactly_the_capability_boundary` | failed | `test_install.py:648` 同上訊息 |
| `…::test_g3_decisions_pending_asks_to_initialize_the_policy` | failed | `test_install.py:667` `assert 'evidence policy' in <decisions-pending.md 全文>.lower()` 為 False |
| `tests/test_status.py::TestEvidencePolicyStatusLine::test_g3_status_shows_the_policy_state[uninitialized]` | failed | `test_status.py:3134` → `:3071` `assert len(hits) == 1` → `assert 0 == 1`(status 沒有 `evidence policy:` 行) |
| `…[uncommitted]` | failed | 同上(`:3134` → `:3071`) |
| `…[worktree-differs]` | failed | 同上 |
| `…[unknown-schema]` | failed | `:3131` → `:3071`,**在第一份文件 `malformed-json`** 即失敗(輸出中 `root` 為 `…\malformed-json\repo`);其餘四份未執行到 |
| `…[outside-boundary]` | failed | 同 `[uninitialized]`(`:3134` → `:3071`) |
| `…[valid]` | failed | 同上 |

表中 `…` 為該列上方同類別的完整前綴。9 支的位置與訊息與第一次執行相同。

**與第一次執行的唯一可見差異**:本次 I3 失敗輸出中的 `docs/decisions-pending.md` 全文**不再列出**票 146 / 147。
對輸出檔 grep `146-claude-code|147-turn-end` 計數為 `0`。這與「工作樹已乾淨」一致。

### 6. 帳本(各自單獨執行)

```
$ head -c 761554 .dev/test-runs.jsonl > <session scratch>/r11.bin
$ head -c 9222325 .dev/test-sessions.jsonl > <session scratch>/s11.bin
$ sha256sum <session scratch>/r11.bin
52548c1e068f857dd47d9a856503efdc1c923b978d8d2fe318e21771697c6dc2 *<session scratch>/r11.bin
$ sha256sum <session scratch>/s11.bin
79050cac5e3fb56f6454bb78ceb1266c0e1c170646f0063d66848c493b13aa80 *<session scratch>/s11.bin
$ wc -l .dev/test-runs.jsonl
2874 .dev/test-runs.jsonl
$ wc -l .dev/test-sessions.jsonl
24 .dev/test-sessions.jsonl
```

- 前段 sha256 = H11r / H11s ⇒ 只追加。
- test-runs:2827 → 2874(+47 行)。與前兩次相同,47 個被涵蓋的測試檔各一行。
- test-sessions:23 → 24(+1 行)。
- 程序註記:兩條 `head -c` 是在同一則訊息裡並行送出的,不是逐條。兩者都只寫到 session scratch;之後的 `sha256sum` / `wc` 逐條執行。

跑後全檔(供下一輪當基準;各自單獨執行):

```
$ wc -c .dev/test-runs.jsonl
776293 .dev/test-runs.jsonl
$ wc -c .dev/test-sessions.jsonl
9959109 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl
826b52afc4d91e1e423e138c69b8b7dd719704d8c6a445011efd34ac8f24e609 *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
50370cecd7fbdbdadf8ab5b8ff527fb2b883e779194a8ceb2c6c78768a233306 *.dev/test-sessions.jsonl
```

記為 B12r = 776293、B12s = 9959109、L12r = 2874、L12s = 24;H12r / H12s 為上面兩個 sha256。

### 7. 限制與未證明

- 本機只驗 Windows;POSIX 未實測。
- 舊 26 支本次只對照了 **nodeid 集合**,沒有逐支重抄失敗行。逐支表在 `docs/audits/2026-10-03-m1a-station3g-redlight.md` 第 4 節(以 S3G1 為對象)。
- 本次沒有跑 `status.py`。
- 外來 3 檔是否影響第一次執行的任何測試:**未驗證**。本次乾淨重跑的結果與第一次完全相同,但這只說明「兩次結果相同」,不證明「外來檔沒有影響」。
- 未 push、未 fetch;未改產品碼與 `.dev/pipeline.json`;未執行 `verify_gates.py`。
- 輸出檔路徑含本機使用者名稱,本報告寫為 `<session scratch>`;原始輸出中的 tmp 路徑也含該名稱,未整段引用。
