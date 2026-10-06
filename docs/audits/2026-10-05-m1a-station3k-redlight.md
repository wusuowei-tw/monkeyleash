# 票 145 Station 3k —— 能力邊界 KNOWN_DISTS 納入 anyio 4.15.1 的紅燈

- 日期:2026-10-05(UTC 已跨 2026-10-06)
- 合約:票 145〈六十五〉65.5 裁決 A(擴大能力邊界,邊界跟著證據長);紅燈分「能力」與「policy」兩層,保留負控。
- 上一個 commit:S6-2 `0904cdbc3eafeb71a27c266cdd11ae151f21fb67`。
- 紅燈 commit:S3K1 `b0849792ff3e69df70cdd8a5d77d26af78d79021`。
- 範圍:只在 `tests/test_redlight.py` 檔尾新增 1 個 class、5 支測試(K-e 參數化 2 案,共 6 個 nodeid);不改產品碼、既有測試、`.dev/pipeline.json`。

## 【給裁決者】

1. 加了 6 個測試案例,把「能力邊界(框架認得哪些 anyio 版本)」和「宿主 policy(這個 repo 接受哪些版本)」分開驗。
2. 全套只跑一次:恰好 4 支紅,就是預期要紅的那 4 支。原因都是「4.15.1 還不在框架認得的版本裡」;另外 2 支負控是綠的。
3. status 已顯示 `tests/test_redlight.py` 在本票紅燈清單裡,所以 4k 改 `redlight.py` 時,R3(先有紅燈才准改程式的規則)會放行。
4. 帳本只往後加,舊內容沒動。外來 3 檔照前例先收起、做完放回。
5. 下一步是 Station 4k:在 `KNOWN_DISTS` 加上 4.15.1,並在真裝 4.15.1 的乾淨環境證明正二成立。

## 【給裁決助手】

### 1. S3K1

`tests/test_redlight.py` 檔尾新增 `class TestKnownDistBoundaryAnyio4151`;既有 helper(`_g_root` / `_g_policy` / `_g_policy_text` / `_g_coverage`)只呼叫、不修改。

```
$ python -m py_compile tests/test_redlight.py
(無輸出)
$ git add tests/test_redlight.py
(無輸出)
$ git diff --cached --stat
 tests/test_redlight.py | 42 ++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 42 insertions(+)
$ git diff --cached -U0 -- tests/test_redlight.py > <session scratchpad>/s3k-diff.txt   → 恰一個 hunk,只有 + 行
@@ -2750,0 +2751,42 @@ class TestRootIsToplevelParser:
$ git diff --cached --check
(無輸出)
$ git commit -F .scratch/m1a-s3k/s3k-1-msg.txt
[master b084979] test(145): M1-a Station 3k-1 —— 能力邊界 KNOWN_DISTS 納入 anyio 4.15.1 的紅燈（K-a/K-b/K-e 紅、K-c/K-d 負控；6 支）
 1 file changed, 42 insertions(+)
$ git rev-parse HEAD
b0849792ff3e69df70cdd8a5d77d26af78d79021
$ git status --porcelain
(無輸出)
```

| 代號 | nodeid | 分類 | 在 S6-2 上(預期) | S3K1 全套(實際) |
|---|---|---|---|---|
| K-a | `tests/test_redlight.py::TestKnownDistBoundaryAnyio4151::test_k3_anyio_4151_is_a_known_dist` | constant-lock(red) | 失敗 | **failed**(`:2767`) |
| K-b | `tests/test_redlight.py::TestKnownDistBoundaryAnyio4151::test_k3_a_committed_policy_accepting_4151_with_a_4151_plugin_is_full_coverage` | behavior-red | 失敗 | **failed**(`:2773`) |
| K-c | `tests/test_redlight.py::TestKnownDistBoundaryAnyio4151::test_k3_a_host_policy_without_4151_is_unknown` | negative-lock | 通過(修後仍須綠) | passed |
| K-d | `tests/test_redlight.py::TestKnownDistBoundaryAnyio4151::test_k3_an_uninventoried_version_is_unknown` | negative-lock | 通過(修後仍須綠) | passed |
| K-e[4.15.0] | `tests/test_redlight.py::TestKnownDistBoundaryAnyio4151::test_k3_a_policy_listing_both_versions_accepts_each[4.15.0]` | behavior-red | 失敗 | **failed**(`:2792`) |
| K-e[4.15.1] | `tests/test_redlight.py::TestKnownDistBoundaryAnyio4151::test_k3_a_policy_listing_both_versions_accepts_each[4.15.1]` | behavior-red | 失敗 | **failed**(`:2792`) |

### 2. 紅燈全套(在 S3K1 上只跑一次;Windows)

指令:`python -X utf8 -m pytest -q > <session scratchpad>/s3k-run.txt 2>&1`,exit 1;之後 `git status --porcelain` 無輸出。

```
$ grep -n -E "^FAILED|passed|failed" <session scratchpad>/s3k-run.txt
110:FAILED tests/test_redlight.py::TestKnownDistBoundaryAnyio4151::test_k3_anyio_4151_is_a_known_dist
111:FAILED tests/test_redlight.py::TestKnownDistBoundaryAnyio4151::test_k3_a_committed_policy_accepting_4151_with_a_4151_plugin_is_full_coverage
112:FAILED tests/test_redlight.py::TestKnownDistBoundaryAnyio4151::test_k3_a_policy_listing_both_versions_accepts_each[4.15.0]
113:FAILED tests/test_redlight.py::TestKnownDistBoundaryAnyio4151::test_k3_a_policy_listing_both_versions_accepts_each[4.15.1]
114:4 failed, 2106 passed, 4 skipped, 3 xfailed in 246.14s (0:04:06)
```

- collected 2117(4 + 2106 + 4 + 3)。FAILED 恰為預期的 4 支;K-c / K-d 在 passed 之內。

失敗行(輸出檔第 39–43、55–61、75–81、95–101 行,以 `grep -n -E "^tests.test_redlight.py:[0-9]+: |^E   "` 取出):

```
39:E       AssertionError: (('anyio', '4.15.0'),)
40:E       assert ('anyio', '4.15.1') in (('anyio', '4.15.0'),)
41:E        +  where (('anyio', '4.15.0'),) = redlight.KNOWN_DISTS
43:tests\test_redlight.py:2767: AssertionError
55:E       AssertionError: unknown
56:E       assert 'unknown' == 'true'
57:E
58:E         - true
59:E         + unknown
61:tests\test_redlight.py:2773: AssertionError
75:E       AssertionError: unknown
76:E       assert 'unknown' == 'true'
77:E
78:E         - true
79:E         + unknown
81:tests\test_redlight.py:2792: AssertionError
95:E       AssertionError: unknown
96:E       assert 'unknown' == 'true'
97:E
98:E         - true
99:E         + unknown
101:tests\test_redlight.py:2792: AssertionError
```

(第 57、77、97 行的 `E         ` 是 pytest 原始輸出的行尾空白;本報告照錄時把它們去掉,以通過 `git diff --cached --check`。)

- K-a 失敗於 `KNOWN_DISTS` 只有 `('anyio', '4.15.0')`。K-b / K-e 都得到 `unknown`,原因是 4.15.1 在邊界外,policy 無效或 plugin 判為 other。紅的原因正是本站要修的能力邊界,不是測試本身的瑕疵。

### 3. 帳本

基準 V0(Step 0):test-runs 891928 bytes / `22148446c9cc8d11520cd6437f5a49c852b9b02cc17c47d2a4b53d8be8991fe4`;test-sessions 17351316 bytes / `3d7cde594d889bc71804c2af421b4c7d61078691c8644052bb68bbe7e03865f1`。

```
$ head -c 891928 .dev/test-runs.jsonl > <session scratchpad>/r23.bin
$ sha256sum <session scratchpad>/r23.bin
22148446c9cc8d11520cd6437f5a49c852b9b02cc17c47d2a4b53d8be8991fe4 *<session scratchpad>/r23.bin
$ head -c 17351316 .dev/test-sessions.jsonl > <session scratchpad>/s23.bin
$ sha256sum <session scratchpad>/s23.bin
3d7cde594d889bc71804c2af421b4c7d61078691c8644052bb68bbe7e03865f1 *<session scratchpad>/s23.bin
$ wc -l .dev/test-runs.jsonl
3391 .dev/test-runs.jsonl
$ wc -l .dev/test-sessions.jsonl
35 .dev/test-sessions.jsonl
$ wc -c .dev/test-runs.jsonl
903816 .dev/test-runs.jsonl
$ wc -c .dev/test-sessions.jsonl
18095023 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl
0edb6cd32349bf5477a5f1adef2e59188d91de8841239565a467b5fc39c56285 *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
75c4580bc54324b90391ccee222647a4933549872154e2af41c2aaaffe405763 *.dev/test-sessions.jsonl
```

- 前段 sha256 = V0 ⇒ 只追加。test-runs 3344 → 3391 行(+47)、test-sessions 34 → 35 行(+1)。
- 跑後全檔記為 **V1**:test-runs 903816 bytes / `0edb6cd32349bf5477a5f1adef2e59188d91de8841239565a467b5fc39c56285`;test-sessions 18095023 bytes / `75c4580bc54324b90391ccee222647a4933549872154e2af41c2aaaffe405763`。供 4k 使用。

### 4. status(節錄原文)

```
test-runs: 本票 red 1 / green 46 / run 事實未知 0 / orphaned 0 / schema 不合格 run 0;最後一筆 tests/test_verify_gates.py=green @ 2026-10-06T01:46:19.491434+00:00;最近一次 run:B(exit 1;collected 2117 / deselected 0 / passed 2106 / failed 4 / skipped 4)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl)
evidence policy: 有效  (source: .agents/evidence-policy.json)
tests red under ticket 145: tests/test_redlight.py  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
```

- `tests/test_redlight.py` 在 red ⇒ 4k 改 `redlight.py` 時 R3 所需的本機紅燈已存在,而且是對著 HEAD 的 `redlight.py`(S6-2 = S3K1 的同一 blob)跑出來的。

### 5. 裁決助手 Linux 預演(外部來源;**非本 repo 帳本證據**)

同一組測試在 S4J1 碼上 4 紅 2 綠;`KNOWN_DISTS` 加 4.15.1 後,`tests/test_redlight.py` 153 passed。(來源:Jeff 的 Station 3k 指令。)

### 6. 程序紀錄

- S6-2 由 5j 審查視窗提交;本站回原實作視窗執行。5j 審查視窗不得再擔任任何審查者;5k 須開第六個全新對話。
- 本站站別為 `implement`(Step 0 照指令核對)。
- 外來 3 檔以 `git stash push -u -m jeff-mods-recon-20261004-s3k -- <3 檔>` 收起,本輪結束後 `git stash pop` 放回。
- 沒有閘門擋下;沒有改產品碼、既有測試、`.dev/pipeline.json`;沒有 push / fetch。
