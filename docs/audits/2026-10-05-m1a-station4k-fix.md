# 票 145 Station 4k —— 能力邊界 KNOWN_DISTS 納入 anyio 4.15.1 與本機驗收

- 日期:2026-10-06(UTC)
- 對象:S4K1 `492b5de438ef9a306b112ac1fbc402729e219879`(只改 `.claude/hooks/redlight.py` 的 `KNOWN_DISTS`);S4K1B `c1eebd97ed197d7f653fbc1c680a0feca1837c6a`(只改 `.agents/evidence-policy.json` 的 `dists`)。
- 上一個 commit:S3K2 `16d29f7ee84c746f845d071e13dce93b85e26fb2`;紅燈 S3K1 `b0849792ff3e69df70cdd8a5d77d26af78d79021`。
- 合約:票 145〈六十五〉65.5 裁決 A(擴大能力邊界,邊界跟著證據長);裁決 4:4k 須在真裝 anyio 4.15.1 的乾淨環境證明正二成立(裁決助手 POSIX)。
- 範圍:**本機(Windows;本機 anyio 為 4.15.0)驗收**。本報告只宣稱:本機驗收通過;~~待 POSIX 外部驗收(真裝 anyio 4.15.1)~~。（S4K4 後更新：POSIX 外部 clean-room（真裝 anyio 4.15.1）驗收已 PASS，見第 9 節；Station 4k = PASS / COMPLETED；待 Station 5k 獨立審查。刪除線為 F-036 保存的舊狀態字樣，2026-10-06 由 S4K4 取代。）

## 【給裁決者】

1. 修正:框架認得的 anyio 版本從只有 4.15.0 改成 4.15.0 與 4.15.1 兩版;本 repo 的 policy 也同步接受兩版。各一行。
2. 本機全套 2110 passed、0 failed;3k 那 4 支紅燈全部轉綠,2 支負控維持綠。
3. 淨室兩正三負全部成立,正二仍可退紅;本 repo 測試帳本只往後加,淨室前後完全沒動。
4. 這台機器裝的是 anyio 4.15.0,所以「真裝 4.15.1 時正二成立」本機證明不了,要靠 POSIX 外部驗收。
5. 下一步是 POSIX 外部淨室驗收(裁決助手執行,須真裝 anyio 4.15.1)。

## 【給裁決助手】

### 1. 修正內容

S4K1(`git diff --cached -U0 -- .claude/hooks/redlight.py`,提交前):

```
diff --git a/.claude/hooks/redlight.py b/.claude/hooks/redlight.py
index d4d208a..0fe2f7a 100644
--- a/.claude/hooks/redlight.py
+++ b/.claude/hooks/redlight.py
@@ -486 +486,3 @@ KNOWN_PYTHON_VERSIONS = ("3.11",)
-KNOWN_DISTS = (("anyio", "4.15.0"),)
+# 票 145 Station 4k:anyio 4.15.1(PyPI 2026-09-05)納入;pytest_plugin.py 與 4.15.0 逐位元組相同(wheel 比對,外部來源),
+# 真實 4.15.1 環境的淨室正二由 4k POSIX 驗收證明。
+KNOWN_DISTS = (("anyio", "4.15.0"), ("anyio", "4.15.1"))
```

- 只有一個 hunk;`--stat` 為 `.claude/hooks/redlight.py | 4 +++-`(3 insertions(+), 1 deletion(-))。
- Edit 一次通過,沒有被 R3 擋。前提是本機紅燈:S3K1 上 status 為 `tests red under ticket 145: tests/test_redlight.py`。
- 寫入後 `py_compile` 無輸出。探針(`status.py`)的 `grep -n "redlight.py"` 只命中 `tests red under ticket 145: tests/test_redlight.py` 一行,沒有 redlight.py 讀取錯誤。
- `content_hash`、consumer、`policy_state`、conftest、status / install / verify_gates、任何測試都未改。

S4K1B(`git diff --cached -U0`,提交前):

```
diff --git a/.agents/evidence-policy.json b/.agents/evidence-policy.json
index 6e9aca1..82669a8 100644
--- a/.agents/evidence-policy.json
+++ b/.agents/evidence-policy.json
@@ -8 +8 @@
-  "dists": [["anyio", "4.15.0"]]
+  "dists": [["anyio", "4.15.0"], ["anyio", "4.15.1"]]
```

- 其他欄位、縮排、行尾都沒動。兩版都在能力邊界 B(KNOWN_DISTS)內,所以 effective = B ∩ H 兩版皆接受。

提交:

```
$ git commit -F .scratch/m1a-s4k/s4k-1-msg.txt
[master 492b5de] fix(145): M1-a Station 4k-1 —— KNOWN_DISTS 納入 anyio 4.15.1（能力邊界跟著證據長；S6 CI 淨室 FAIL）
 1 file changed, 3 insertions(+), 1 deletion(-)
$ git rev-parse HEAD
492b5de438ef9a306b112ac1fbc402729e219879
$ git commit -F .scratch/m1a-s4k/s4k-1b-msg.txt
[master c1eebd9] fix(145): M1-a Station 4k-1b —— 宿主 evidence policy dists 納入 anyio 4.15.1（B ∩ H，兩版皆在 B 內）
 1 file changed, 1 insertion(+), 1 deletion(-)
$ git rev-parse HEAD
c1eebd97ed197d7f653fbc1c680a0feca1837c6a
```

兩次提交前 `git diff --cached --check` 都無輸出;提交後 `git status --porcelain` 都無輸出。

### 2. 3a 固定全套(S4K1B 上只跑一次;Windows)

`python -X utf8 -m pytest -q > <session scratchpad>/s4k-run.txt 2>&1`,exit 0。

```
$ grep -n -E "^FAILED|^ERROR|SKIPPED|passed|failed" <session scratchpad>/s4k-run.txt
32:SKIPPED [1] tests\test_gate.py:451: 此環境無法建立 symlink
33:SKIPPED [1] tests\test_gate.py:459: 此環境無法建立 symlink
34:SKIPPED [1] tests\test_gate.py:473: 此環境無法建立 symlink
35:SKIPPED [1] tests\test_redlight.py:2673: Windows 檔名不得含 LF;本案例由 POSIX 驗收證明(〈六十一〉61.3 裁決 2)
39:2110 passed, 4 skipped, 3 xfailed in 296.19s (0:04:56)
```

- collected 2117(2110 + 4 + 3)。0 failed;沒有 `FAILED` / `ERROR` 行。

| 代號 | S3K1(修前) | S4K1B(修後) |
|---|---|---|
| K-a `test_k3_anyio_4151_is_a_known_dist` | failed(`:2767`) | passed |
| K-b `test_k3_a_committed_policy_accepting_4151_with_a_4151_plugin_is_full_coverage` | failed(`:2773`) | passed |
| K-c `test_k3_a_host_policy_without_4151_is_unknown` | passed | passed |
| K-d `test_k3_an_uninventoried_version_is_unknown` | passed | passed |
| K-e[4.15.0] `test_k3_a_policy_listing_both_versions_accepts_each[4.15.0]` | failed(`:2792`) | passed |
| K-e[4.15.1] `test_k3_a_policy_listing_both_versions_accepts_each[4.15.1]` | failed(`:2792`) | passed |

(修前欄出自 `docs/audits/2026-10-05-m1a-station3k-redlight.md`。修後欄的依據是:S4K1B 全套 0 failed,而 6 支都在收集範圍內 —— collected 2117 與 3k 相同。)

### 3. 3b 帳本(以 V1 為前段基準;各自單獨執行)

```
$ head -c 903816 .dev/test-runs.jsonl > <session scratchpad>/r24.bin
$ sha256sum <session scratchpad>/r24.bin
0edb6cd32349bf5477a5f1adef2e59188d91de8841239565a467b5fc39c56285 *<session scratchpad>/r24.bin
$ head -c 18095023 .dev/test-sessions.jsonl > <session scratchpad>/s24.bin
$ sha256sum <session scratchpad>/s24.bin
75c4580bc54324b90391ccee222647a4933549872154e2af41c2aaaffe405763 *<session scratchpad>/s24.bin
$ wc -l .dev/test-runs.jsonl
3438 .dev/test-runs.jsonl
$ wc -l .dev/test-sessions.jsonl
36 .dev/test-sessions.jsonl
$ wc -c .dev/test-runs.jsonl
915335 .dev/test-runs.jsonl
$ wc -c .dev/test-sessions.jsonl
18838751 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl
3637077aea4d2bdaa3138bf9b2aa28b5306ab9e9bc317d04df78ddfee3382778 *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
6d18a5c6567054da5f2d09d7655b8aa29129c34cbf948be69e8a9c58d09dddcd *.dev/test-sessions.jsonl
```

- 前段 sha256 = V1 ⇒ 只追加。test-runs 3391 → 3438(+47)、test-sessions 35 → 36(+1)。
- **V1**:903816 / `0edb6cd32349bf5477a5f1adef2e59188d91de8841239565a467b5fc39c56285`;18095023 / `75c4580bc54324b90391ccee222647a4933549872154e2af41c2aaaffe405763`。
- **V2**:915335 / `3637077aea4d2bdaa3138bf9b2aa28b5306ab9e9bc317d04df78ddfee3382778`;18838751 / `6d18a5c6567054da5f2d09d7655b8aa29129c34cbf948be69e8a9c58d09dddcd`。

### 4. 3c status(節錄原文)

```
23:test-runs: 本票 red 0 / green 47 / run 事實未知 0 / orphaned 0 / schema 不合格 run 0;最後一筆 tests/test_verify_gates.py=green @ 2026-10-06T11:42:12.930658+00:00;最近一次 run:A(exit 0;collected 2117 / deselected 0 / passed 2110 / failed 0 / skipped 4)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl)
24:evidence policy: 有效  (source: .agents/evidence-policy.json)
38:tests red under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
```

- `evidence policy: 有效` 說明修改後的 policy(兩版 dists)仍落在能力邊界內,並且已提交、與工作樹一致。

### 5. 3d 淨室(本機 Windows;本機 anyio 4.15.0)

`python .claude/portable/verify_gates.py <session scratchpad>/verify-gates7 > <session scratchpad>/s4k-verify.txt 2>&1`,exit 0(工具沒有標示非零退出碼)。

```
$ grep -n -E "擋下 ✓|成立|不成立|passed, " <session scratchpad>/s4k-verify.txt
194:    R1   擋下 ✓
195:    R2   擋下 ✓
196:    R3   擋下 ✓
197:    R4   擋下 ✓
198:    R5   擋下 ✓
199:    R6   擋下 ✓
200:    R7   擋下 ✓
201:    R8   擋下 ✓
202:    R9   擋下 ✓
217:    1960 passed, 8 skipped, 3 xfailed in 271.46s (0:04:31)
220:    正一 未初始化                  成立 ✓  35 個框架測試檔皆 unknown=True;evidence policy: 未初始化
221:    正二 已初始化且相符               成立 ✓  rc 1→0;file_coverage=true;red=(無);green=tests/test_evidence_probe.py;evidence policy: 有效;1 passed in 18.87s
222:    負一 policy / 環境不符         成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 有效;1 passed in 0.33s
223:    負二 HEAD 有、工作樹不同          成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 工作樹與 HEAD 不同;1 passed in 0.25s
224:    負三 工作樹有、HEAD 沒有          成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 未提交;1 passed in 0.25s
226:全部 9 條規則各擋下一次,權威層偵測正常,框架測試在新 repo 全綠,evidence policy 兩正三負成立。
```

事後(各自單獨執行):

```
$ sha256sum .dev/test-runs.jsonl
3637077aea4d2bdaa3138bf9b2aa28b5306ab9e9bc317d04df78ddfee3382778 *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
6d18a5c6567054da5f2d09d7655b8aa29129c34cbf948be69e8a9c58d09dddcd *.dev/test-sessions.jsonl
$ git status --porcelain
(無輸出)
```

- 本 repo 帳本 = V2,淨室沒有碰。
- **限制**:這次淨室的 anyio 是本機的 4.15.0。它證明修改後 4.15.0 環境沒有退化,但**不證明**真裝 4.15.1 時正二成立(第 9 節)。

### 6. 裁決助手外部來源(照錄自〈六十五〉65.3 / 〈六十六〉;非本 repo 帳本證據)

- 同一組 3k 測試在 S4J1 碼上 4 紅 2 綠;KNOWN_DISTS 加 4.15.1 後 `tests/test_redlight.py` 153 passed。
- anyio-4.15.0 與 4.15.1 的 wheel:`anyio/pytest_plugin.py` 與 `entry_points.txt` 逐位元組相同。但檔案相同不等於行為等價,真實 4.15.1 環境的行為以第 9 節驗收為準。

### 7. 殘餘與未證明(目前尚未 machine-enforced)

1. 沿用 4j 證據報告(`docs/audits/2026-10-05-m1a-station4j-fix.md`)第 7 節全部項目(含 S5j-1 依 S5j-F2 / F3 補準後的第 3 點、第 4 點殘餘措辭),不擴張。
2. **相依漂移**:KNOWN_DISTS 仍為精確版本 pin,下一次相依升版會再落在邊界外;候選機制見票「相關」追蹤項(〈六十五〉65.4 登記的「相依漂移(精確版本能力邊界 vs 乾淨環境自動升版)」)。
3. 本機只驗 anyio 4.15.0;真裝 4.15.1 的淨室正二尚未證明(第 9 節)。

### 8. 程序紀錄

- 外來 3 檔以 `git stash push -u -m jeff-mods-recon-20261004-s4k -- <3 檔>` 收起,本輪結束後 `git stash pop` 放回。
- 沒有閘門擋下;沒有改測試、`.dev/pipeline.json`;沒有 push / fetch。
- 本視窗 = 原實作視窗;5k 須開第六個全新對話。

### 9. POSIX 外部 clean-room 驗收(真裝 anyio 4.15.1)

> **舊文字(F-036,保留不刪)**:本節標題原為 ~~`### 9. POSIX 外部 clean-room 驗收(真裝 anyio 4.15.1):待執行(裁決助手)`~~,沒有內文。
> —— 2026-10-06 由 S4K4 的 POSIX 驗收紀錄取代。

- 來源：Jeff 轉述裁決助手 2026-10-06 Linux 證據（隔離沙盒；git 2.43.0；Python 3.11.16；全新 venv 依 CI 方式 pip install -e ".[dev]" 實際安裝 anyio 4.15.1、pytest 9.1.1；非本 repo 帳本證據；本 repo 兩本帳本未動）。
- 受測物：S4K1B 的 .claude/hooks/redlight.py（blob 0fe2f7ab0e600a18db1079462db80eddee6eae13，sha256 30ee60f9e501788ee2e3a065f0bfc4725d9258fd3f2cdb68288719c7382d30ed，與本機 S4K2 run 紀錄 impl_hash 相同）、tests/test_redlight.py（blob e9f4c82e6b879db998f9ebe8289aa458b1475c9f = S3K1）、.agents/evidence-policy.json（blob 82669a8c0f0c59eaf8b507e00639b9700aafb172）。置於全新 clone、提交後工作樹乾淨、歷史完整（unshallow）。
- verify_gates.py 淨室（anyio 4.15.1 實裝）：R1–R9 各擋下一次、權威層偵測三項成立、框架測試 1964 passed, 4 skipped, 3 xfailed；兩正三負全部成立，正二 file_coverage=true、green=tests/test_evidence_probe.py；exit 0。對照：S4J1 碼在同一 venv 下正二不成立 ✗、exit 1（〈六十五〉65.3 的重現）。
- 6 支 K 測試（TestKnownDistBoundaryAnyio4151）全 passed；evidence 相關 5 檔 1 failed, 963 passed：唯一 failed 為先前 4g–4j 各次 POSIX 驗收亦出現的 tests/test_gate.py::TestAuthorityLayerIsWired::test_this_repo_itself_is_wired；環境性原因仍屬推定，尚未獨立核驗。淺層 clone 時另有 4 支 R6 相關失敗，git fetch --unshallow 後消失，對應 CI workflow fetch-depth: 0 的既有註解，判為 clone 深度所致而非回歸（同屬推定）。
- 固定全套：13 failed, 2101 passed, 3 xfailed（collected 2117）；13 個 failed 與 4j POSIX 驗收那次逐字相同（test_gate 1 + test_known_items_regression 12），可支持「未新增該類失敗」，環境性根因仍屬推定、尚未獨立核驗或 machine-enforced。
- Jeff 裁決（2026-10-06）：Station 4k = PASS / COMPLETED（Windows 本機 + POSIX 外部 clean-room，真裝 anyio 4.15.1）；待 Station 5k 獨立審查（第六個全新對話）。CI 是否轉綠仍須 Station 6 第三次 push 後由 CI 本身證明。
