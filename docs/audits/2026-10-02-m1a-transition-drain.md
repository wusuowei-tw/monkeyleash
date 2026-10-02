# M1-a Station 3→4 轉場 —— drain `.claude/hooks/redlight.py` 的 R3 豁免

**這份檔案的身分**:轉場刀的正式報告,**進版控**
(位置依據:`docs/agents/handover.md:34`「**回報檔一律進版控**(`docs/audits/`)」)。
路徑一律寫 repo 相對路徑。

| | |
|---|---|
| **撰寫時點** | 2026-10-02T14:27:42Z(寫入當下) |
| **依據** | 票 145〈十三〉裁決 6;Jeff 裁 Station 3 Red-light = PASS / ACCEPTED |
| **起點 HEAD** | `09e1e91317c3b9e24012451709dd8047abda0a92`(`0 4`,未推) |
| **T2 commit** | 本報告所在的 commit;SHA 無法寫進自己 —— 見該 commit |

---

## 【給裁決者】

1. 前提相符:Station 3 紅燈跑留下的 `tests/test_redlight.py` 紅燈,`impl_hash` 與 redlight.py 現在的內容**逐字相同**(`0dadc80d…f0ed7`)⇒ 豁免可以誠實移除。
2. 已 drain:豁免清單 9 筆 → 8 筆,移除的恰好是 `.claude/hooks/redlight.py`,其餘 8 筆不變,`# drained:` 行已加(T1 `b27ca30`)。從現在起,改 redlight.py 會被 R3 真的檢查。
3. 全套只跑一次:`14 failed, 1912 passed, 3 skipped, 3 xfailed` —— 紅的仍恰好是 Station 3 那 14 支,既有測試 0 失敗;清單完整性測試未失敗。
4. 要你決定:①**切 `current_stage` 為 implement**(之後才進 Station 4);②票 145〈十〉第 394 行仍寫「Station 3 進行中…(與票頭第 3 行一致)」,已與第 3 行矛盾 —— 本輪只授權改 Station 3 那一列,**未動**;A 下一刀一併改,或 B 另授權一刀。
5. 不決定的話:pipeline 仍是 `tickets`,R2 擋原始碼寫入,Station 4 無法開始;六個 commit 停在本機不推。

### 最低必要內容

| # | 項目 | 值 |
|---|---|---|
| 1 | drain 前提 | **相符**:`sha256sum` = `0dadc80d19a7f1d11246d0fdeb2d75ca3f5c170511ec14b142fba394512f0ed7`;帳本第 2074 行 `impl_hash` = `0dadc80d19a7f1d11246d0fdeb2d75ca3f5c170511ec14b142fba394512f0ed7` |
| 2 | active entries | drain 前 9 筆 / drain 後 8 筆;被移除:`.claude/hooks/redlight.py`;drained 行**存在**(清單第 28 行) |
| 3 | T1 | `b27ca301b058c60c3972eb247e2b701f4c38c3d4`;`.agents/legacy-no-redlight.txt` `4 1`(刪 1 條目行、加 1 行 drained、加 3 行散文) |
| 4 | 全套 | exit code **1**;`14 failed, 1912 passed, 3 skipped, 3 xfailed in 141.67s (0:02:21)`;失敗集合 **= 預期 14 支**;完整性測試:**未失敗;exact PASS 未由本次固定指令直接觀察** |
| 5 | 新增帳本紀錄 | 46 筆,全 `"145"`;red 2(`tests/test_redlight.py`、`tests/test_status.py`)/ green 44 / 其他 0 |
| 6 | T2 / 第 3 行 | T2 SHA 見視窗;第 3 行:`**狀態**:動工 —— Station 3 PASS(Jeff 驗收 2026-10-02);redlight.py 豁免已 drain;待 Jeff 切 implement;Station 4 未開始。` |
| 7 | `0 6` / 樹 | 發生在本檔 commit 之後,只在視窗回報 |
| 8 | push / 改 redlight.py / 改 tests/ / 改 pipeline / pytest 次數 | **NO / NO / NO / NO / 1** |

---

## 【給裁決助手】證據

### 前置

```
$ git fetch origin
(無輸出)
$ git rev-list --left-right --count origin/master...HEAD
0	4
$ git rev-parse HEAD
09e1e91317c3b9e24012451709dd8047abda0a92
$ git status --porcelain
(無輸出)
$ cat .dev/pipeline.json
{
  "current_stage": "tickets",
  "feature": "framework-updates",
  "ticket_id": "145",
  "updated": "2026-10-02"
}
```

### 0|drain 前提驗證(唯讀)

```
$ git ls-files --eol .claude/hooks/redlight.py
i/lf    w/lf    attr/text eol=lf      	.claude/hooks/redlight.py
$ sha256sum .claude/hooks/redlight.py
0dadc80d19a7f1d11246d0fdeb2d75ca3f5c170511ec14b142fba394512f0ed7 *.claude/hooks/redlight.py
```

以唯讀工具(`Grep` pattern `"test_file": "tests/test_redlight.py", "time": "2026-10-02T14:0`)在 `.dev/test-runs.jsonl` 找到第 2074 行,原文:

```
{"test_file": "tests/test_redlight.py", "time": "2026-10-02T14:08:27.690782+00:00", "result": "red", "failed_tests": ["TestRunFacts::test_a_full_pass_is_state_a_with_coverage_visible", "TestRunFacts::test_one_failure_is_state_b_and_names_the_test", "TestRunFacts::test_zero_collected_is_state_c_and_the_run_is_visible", "TestRunFacts::test_a_collection_error_is_state_d", "TestRunFacts::test_a_usage_error_is_state_d_not_green", "TestRunFacts::test_an_interrupted_run_is_state_d_even_with_passes", "TestRunFacts::test_three_skipped_645_deselected_is_state_f_with_counts"], "impl_file": ".claude/hooks/redlight.py", "impl_exists": true, "impl_hash": "0dadc80d19a7f1d11246d0fdeb2d75ca3f5c170511ec14b142fba394512f0ed7", "ticket_id": "145"}
```

判定:`impl_file == .claude/hooks/redlight.py`、`ticket_id == "145"`、`impl_hash` 與 `sha256sum` **逐字相同**(工作樹與 index 皆 lf ⇒ `content_hash` 的行尾正規化不改變內容)⇒ **前提成立**。

排水格式依據:票 137 `:152-167`(節標題在 `:152`;格式行 `# drained: <path> <YYYY-MM-DD> <ticket>` 在 `:155`;規矩表 `:158-165`;契約在 `:167`)。

drain 前 `.agents/legacy-no-redlight.txt` 的條目行(非註解、非空行)= 第 25–33 行,**9 筆**:

```
    25	.claude/hooks/gate.py
    26	.claude/hooks/redlight.py
    27	.claude/patches/apply_patches.py
    28	.claude/portable/claude_md.py
    29	.claude/portable/g1_verify.py
    30	.claude/portable/install.py
    31	.claude/portable/leak_scan.py
    32	.claude/portable/manifest.py
    33	.claude/portable/verify_gates.py
```

(取自 `cat -n .agents/legacy-no-redlight.txt`;全檔 33 行,第 1–24 行皆以 `#` 開頭,無空行。)

### T1|drain

```
$ git diff .agents/legacy-no-redlight.txt
diff --git a/.agents/legacy-no-redlight.txt b/.agents/legacy-no-redlight.txt
index 4b99674..97fde6b 100644
--- a/.agents/legacy-no-redlight.txt
+++ b/.agents/legacy-no-redlight.txt
@@ -15,6 +15,9 @@
 #   2026-08-14  移除 .claude/portable/g1_guard.py
 #               票 25 的紅燈對著它在 HEAD 的內容發生過(impl_hash 相符兩筆),
 #               R3 後半已能誠實滿足,不必再靠豁免。10 -> 9。
+#   2026-10-02  移除 .claude/hooks/redlight.py
+#               票 145 Station 3 的紅燈對著它在 HEAD 的內容發生過(impl_hash 相符),
+#               R3 後半已能誠實滿足,不必再靠豁免。9 -> 8。
 #
 # 機器可讀的排水紀錄(票 137,格式定義在該票票面)。
 # 上面那段散文**原地保留不刪**(F-036):散文記的是「為什麼」,
@@ -22,8 +25,8 @@
 # ⚠ 本行是**註解**,`_entries_from_lines()` 照舊把它丟掉:
 #   它**不是**豁免條目,既有 9 筆豁免條目一筆未增未減,runtime 判定不變。
 # drained: .claude/portable/g1_guard.py 2026-08-14 25
+# drained: .claude/hooks/redlight.py 2026-10-02 145
 .claude/hooks/gate.py
-.claude/hooks/redlight.py
 .claude/patches/apply_patches.py
 .claude/portable/claude_md.py
 .claude/portable/g1_verify.py
```

drain 後條目行 = 第 29–36 行,**8 筆**(取自 `cat -n`;全檔 36 行,第 1–28 行皆以 `#` 開頭,無空行):

```
    29	.claude/hooks/gate.py
    30	.claude/patches/apply_patches.py
    31	.claude/portable/claude_md.py
    32	.claude/portable/g1_verify.py
    33	.claude/portable/install.py
    34	.claude/portable/leak_scan.py
    35	.claude/portable/manifest.py
    36	.claude/portable/verify_gates.py
```

**正式判定(acceptance)**:

| 條件 | 結果 |
|---|---|
| 9 → 8 | **成立** |
| 被移除的恰為 `.claude/hooks/redlight.py` | **成立** |
| 其餘 8 筆逐字不變 | **成立**(與 drain 前第 25、27–33 行逐字相同) |
| `.claude/hooks/redlight.py` 不在 active entries | **成立** |
| `# drained: .claude/hooks/redlight.py 2026-10-02 145` 存在 | **成立**(第 28 行) |

**原始觀察(僅記錄,不作 acceptance gate)**:

```
$ grep -n redlight .agents/legacy-no-redlight.txt
18:#   2026-10-02  移除 .claude/hooks/redlight.py
28:# drained: .claude/hooks/redlight.py 2026-10-02 145
$ grep -c -v ^# .agents/legacy-no-redlight.txt
8
```

(本檔恰好沒有空行,所以後者與 active entries 數字相同;那是巧合,不是同一個量。)

⚠ 清單第 26 行既有註解「既有 9 筆豁免條目一筆未增未減」是票 137 當時的陳述,drain 後已不精確;依「其餘行一字不改」未動。

```
$ git check-ignore -v .scratch/m1a-transition/t1-msg.txt
.gitignore:67:/.scratch/	.scratch/m1a-transition/t1-msg.txt
$ git diff --cached --numstat
4	1	.agents/legacy-no-redlight.txt
$ git diff --cached --check
(無輸出)
$ git commit -F .scratch/m1a-transition/t1-msg.txt
[master b27ca30] chore(145): drain .claude/hooks/redlight.py 的 R3 豁免(9 -> 8)
 1 file changed, 4 insertions(+), 1 deletion(-)
$ git rev-parse HEAD
b27ca301b058c60c3972eb247e2b701f4c38c3d4
```

pre-commit 未擋。

### 驗證|在 `b27ca30` 上跑固定全套(只跑一次)

```
$ sha256sum .dev/test-runs.jsonl
05c819a047bd83bf88bfb3aba040c4d55a6e63eddd3de5a396bca03a2457d632 *.dev/test-runs.jsonl
$ wc -c -l .dev/test-runs.jsonl
  2089 564441 .dev/test-runs.jsonl
$ date -u +%Y-%m-%dT%H:%M:%SZ
2026-10-02T14:24:08Z
$ python -X utf8 -m pytest -q
...
SKIPPED [1] tests\test_gate.py:451: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:459: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:473: 此環境無法建立 symlink
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/srv/x] - …
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/data/x] - …
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/backup/x] - …
FAILED tests/test_redlight.py::TestRunFacts::test_a_full_pass_is_state_a_with_coverage_visible
FAILED tests/test_redlight.py::TestRunFacts::test_one_failure_is_state_b_and_names_the_test
FAILED tests/test_redlight.py::TestRunFacts::test_zero_collected_is_state_c_and_the_run_is_visible
FAILED tests/test_redlight.py::TestRunFacts::test_a_collection_error_is_state_d
FAILED tests/test_redlight.py::TestRunFacts::test_a_usage_error_is_state_d_not_green
FAILED tests/test_redlight.py::TestRunFacts::test_an_interrupted_run_is_state_d_even_with_passes
FAILED tests/test_redlight.py::TestRunFacts::test_three_skipped_645_deselected_is_state_f_with_counts
FAILED tests/test_status.py::TestTicket139::test_a_narrow_all_skip_record_does_not_retire_the_earlier_red
FAILED tests/test_status.py::TestNarrowSelection::test_a_later_green_without_run_facts_does_not_retire_x
FAILED tests/test_status.py::TestNarrowSelection::test_a_narrow_run_that_did_not_select_x_does_not_retire_x
FAILED tests/test_status.py::TestHistoricalRecords::test_old_green_rows_are_shown_as_run_unknown_not_green
FAILED tests/test_status.py::TestOrphans::test_a_renamed_red_test_is_orphaned_not_green
FAILED tests/test_status.py::TestRunEvidence::test_no_run_at_all_is_not_zero_tests_and_not_a_pass
FAILED tests/test_status.py::TestRunEvidence::test_no_producer_means_undecidable_not_green_not_c
14 failed, 1912 passed, 3 skipped, 3 xfailed in 141.67s (0:02:21)

[exit code 1]
```

(XFAIL 三行的說明文字以 `…` 截斷 —— 本區塊**不是逐字全文**;FAILED / SKIPPED / 摘要行逐字。背景執行,完成通知回報 `exit code 1`。)

**判定**

| 條件 | 結果 |
|---|---|
| exit code = 1 | **成立** |
| 失敗集合 = Station 3 預期 Red-light 集合(14 支) | **成立**(逐支與票 145〈十四〉14.2 相同;差集兩方向皆空) |
| 既有測試不在失敗集合 | **成立**(1912 passed,與 baseline 及 Station 3 紅燈跑相同) |
| `tests/test_gate.py::TestT137TheRealListUnderTheNewRule::test_the_real_list_is_the_generator_output_minus_drained` | **未失敗;exact PASS 未由本次固定指令直接觀察。** 佐證:`pyproject.toml:72` `addopts = "-ra --strict-markers"` 使所有非通過結果逐條列出;本次 3 筆 SKIPPED 皆為 `tests\test_gate.py:451 / 459 / 473`、3 筆 XFAIL 皆在 `tests/test_g1_guard.py`,該測試不在其中 |

**帳本 after**

```
$ sha256sum .dev/test-runs.jsonl
6069453b9c0624ad42b898afded146bf01dd906cbd8be44f9c4fafa5655d9bd2 *.dev/test-runs.jsonl
$ wc -c -l .dev/test-runs.jsonl
  2135 576717 .dev/test-runs.jsonl
$ grep -c -F \"ticket_id\":\ \"145\" .dev/test-runs.jsonl
138
$ grep -c -F test_thing .dev/test-runs.jsonl
0
$ git status --porcelain
(無輸出)
```

新增 = 2135 − 2089 = **46** 行;`"145"` 92 → 138 ⇒ 新增 46 筆全部 `"145"`。以 `tail -n 46` 逐筆讀過:red **2** 筆(`tests/test_redlight.py`、`tests/test_status.py`,`failed_tests` 與 Station 3 紅燈跑相同)、green **44** 筆(含 `tests/test_gate.py`)、其他 **0** 筆。

### T2|落票

票 145:
- 第 3 行改為 `**狀態**:動工 —— Station 3 PASS(Jeff 驗收 2026-10-02);redlight.py 豁免已 drain;待 Jeff 切 implement;Station 4 未開始。`;舊第 3 行併入票頭 F-036 block(第四代)
- 新增〈十五、Station 3→4 轉場〉
- 〈十〉Station 3 列改為 `PASS / ACCEPTED`;新增一行「Transition：redlight.py 豁免已 drain」

```
$ grep -n ^\*\*狀態\*\* docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
3:**狀態**:動工 —— Station 3 PASS(Jeff 驗收 2026-10-02);redlight.py 豁免已 drain;待 Jeff 切 implement;Station 4 未開始。
$ grep -n ^\*\*時鐘\*\* docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
4:**時鐘**:2026-10-02 —— 自此時點起,任何依 status aggregate 判斷「沒有未解紅燈」的行為,都暴露於已證明的 partial-selection false-green failure mode。此日期為 Jeff 於 2026-10-02 的排程裁決,不是由證據唯一推出;痛點最早的證據為票 139(2026-09-13)。
$ grep -n -F 進行中 docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
20:> - 狀態(舊,第三代):~~`動工 —— Station 3 進行中(baseline 已量,紅燈未寫);Station 4 未開始。`~~
394:Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 3 進行中,Station 4 未開始(與票頭第 3 行一致)。
```

**發現的不一致(未改,待裁)**:第 394 行(〈十〉)仍寫「Station 3 進行中」並自稱「與票頭第 3 行一致」—— 已不成立。本輪授權的〈十〉改動只有 Station 3 列與新增一行,故未動。第 20 行是 provenance(正確)。

PRIVATE-CONTEXT CHECK:**PASS** —— 本輪新增文字只來自清單 diff、帳本、測試輸出、票 137 格式定義與裁決;未帶入旅行、住宿或個人背景。

---

## 尚未證明 / 本輪未做

1. **`TestT137TheRealListUnderTheNewRule` 的 exact PASS** 未由本次固定指令直接觀察(見上)。
2. **R3 現在真的會檢查 redlight.py**:由清單內容推得(`_entries_from_lines()` 只認條目行),**未以實際寫入測試門禁** —— 依裁決 6「不得為了測門禁而修改 redlight.py」。
3. **票 145〈十〉第 394 行與第 3 行不一致**(待裁)。
4. **清單第 26 行既有註解的「9 筆」已不精確**(未改,依指令)。
5. **未切 `current_stage`**:pipeline 仍為 `tickets`;切 implement 由 Jeff 手動。
6. 六個 commit 均未推。

---

## 六站狀態

| 站 | 狀態 |
|---|---|
| Station 1 — Spec | PASS / CLOSED |
| Station 2 — Ticket | DONE |
| Station 3 — Red-light | PASS / ACCEPTED |
| Transition | redlight.py 豁免已 drain |
| Station 4 — Implementation | NOT STARTED |
| Station 5 — Review | NOT STARTED |
| Station 6 — Acceptance | NOT STARTED |
