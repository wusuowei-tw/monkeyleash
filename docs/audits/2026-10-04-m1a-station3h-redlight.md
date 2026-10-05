# 票 145 Station 3h —— S5g-F2 補紅燈(evidence root 必須是 Git 最上層)

- 日期:2026-10-04(紅燈全套跑完於 UTC 2026-10-05 前後)
- 合約:票 145〈五十三〉53.3 裁決 2、3;Jeff 裁決 S5g-1 = accepted、Station 3h plan = APPROVED。
- 上一個 commit:S5g-1 `3a9200c03bb8493ab5a789d4c4157a7b38392e79`。
- 紅燈 commit:S3H1 `7621e3ce8604ab72ab2f3fb3257cb1181b8a126e`。
- 範圍:只新增 2 支測試;不改產品碼、不改既有測試、不改 `.dev/pipeline.json`。

## 【給裁決者】

1. 加了 2 支測試,對應 S5g-F2(子目錄可借上層已提交的 policy 取得 true)。
2. 紅燈全套只跑一次:恰好 1 支紅,就是 H1;H2(正常 repo 仍可退紅)是綠的。
3. 帳本只往後加,舊內容沒有被改。
4. 外來 3 檔照前例先收起、做完再放回。
5. 下一步是 Station 4h 最小修正。

## 【給裁決助手】

### 1. S3H1

`tests/test_redlight.py` 檔尾新增 `class TestEvidenceRootIsGitToplevel`;既有 helper(`_g_default_root` / `_g_coverage` / `_G_POLICY_FILE`)只呼叫、不修改。

```
$ python -X utf8 -m py_compile tests/test_redlight.py
(無輸出)
$ git diff --cached --name-only
tests/test_redlight.py
$ git diff --cached --check
(無輸出)
$ git diff --cached -U0 -- tests/test_redlight.py   → 恰一個 hunk,只有 + 行
@@ -2534,0 +2535,42 @@ class TestEvidencePolicyNoOverride:
$ git commit -F .scratch/m1a-s3h/s3h-1-msg.txt
[master 7621e3c] test(145): M1-a Station 3h-1 —— evidence root 必須是 Git 最上層的紅燈(S5g-F2;2 支)
 1 file changed, 42 insertions(+)
$ git rev-parse HEAD
7621e3ce8604ab72ab2f3fb3257cb1181b8a126e
$ git status --porcelain
(無輸出)
```

| nodeid | 分類 | 在 S5g-1 上 |
|---|---|---|
| `tests/test_redlight.py::TestEvidenceRootIsGitToplevel::test_h3_a_parent_committed_policy_does_not_authorize_a_subdirectory_root` | H1 behavior-red | 必須失敗 |
| `tests/test_redlight.py::TestEvidenceRootIsGitToplevel::test_h3_a_git_toplevel_root_with_a_committed_policy_is_full_coverage` | H2 regression-lock | 必須通過 |

- H1:最上層 `parent` 已提交合法 policy、`pyproject.toml`、`tests/conftest.py`;root = `parent/sub`,三份位元組相同的副本只在工作樹、從未提交 ⇒ `file_coverage` 不得為 `"true"`。
- H2:root 本身是最上層、policy 正常提交、worktree = HEAD ⇒ `"true"`。

### 2. 紅燈全套(在 S3H1 上只跑一次)

指令:`python -X utf8 -m pytest -q > <session scratchpad>/s3h1-run.txt 2>&1`,exit 1;之後 `git status --porcelain` 無輸出。

H1 實際失敗段(輸出檔第 54–59 行):

```
        got = _g_coverage(sub, monkeypatch)
>       assert got != "true", got
E       AssertionError: true
E       assert 'true' != 'true'

tests\test_redlight.py:2567: AssertionError
```

FAILED 行與摘要行(輸出檔第 67–68 行):

```
FAILED tests/test_redlight.py::TestEvidenceRootIsGitToplevel::test_h3_a_parent_committed_policy_does_not_authorize_a_subdirectory_root
1 failed, 2095 passed, 3 skipped, 3 xfailed in 409.36s (0:06:49)
```

- collected 2102(1 + 2095 + 3 + 3)。唯一的 FAILED 是 H1;H2 在 2095 passed 之內。與預期相符。

### 3. 帳本

基準(Step 0):test-runs 810925 bytes / 3015 行 / `9fa98cc7…`;test-sessions 12171130 bytes / 27 行 / `27cccd2c…`。

```
$ head -c 810925 .dev/test-runs.jsonl > <session scratchpad>/r15.bin
$ head -c 12171130 .dev/test-sessions.jsonl > <session scratchpad>/s15.bin
$ sha256sum <session scratchpad>/r15.bin
9fa98cc71426865862deebbfcefcd78c49503251e6f20aca928656bb3ac93426 *<session scratchpad>/r15.bin
$ sha256sum <session scratchpad>/s15.bin
27cccd2c1a1506f96d2628c608487ccd394af1da2280ebdc983aa02c6645198b *<session scratchpad>/s15.bin
$ wc -l .dev/test-runs.jsonl
3062 .dev/test-runs.jsonl
$ wc -l .dev/test-sessions.jsonl
28 .dev/test-sessions.jsonl
$ wc -c .dev/test-runs.jsonl
822547 .dev/test-runs.jsonl
$ wc -c .dev/test-sessions.jsonl
12909484 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl
49fc32bc88ad7eb93840e070154953980fa40122388c2fce49645b411a254789 *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
0539883a5548a9032ed0877aab4614bdde6fd748103a3db2524de99e9c589674 *.dev/test-sessions.jsonl
```

- 前段 sha256 = 基準 ⇒ 只追加。
- test-runs 3015 → 3062 行(+47)、test-sessions 27 → 28 行(+1)。
- 跑後全檔記為 B15(822547 / 12909484;`49fc32bc…` / `0539883a…`),供 4h 使用。

### 4. 程序紀錄

- 外來 3 檔以 `git stash push -u -m jeff-mods-recon-20261004-s3h -- <3 檔>` 收起(Jeff 已同意),本輪結束後 `git stash pop` 放回。
- **程序註記(Jeff)**:S5g-1 由 5g 審查 session 執行(審查報告在 S5g-1 前已完成,RR = `8399be264fafa82d62bb3294762d17835b4429850aca68c57c545883adfd0a49`),不影響已凍結的 5g 審查結果,但該 session 不得擔任 5h 審查者;另 S5g-1 回報檔名的時間戳與實際提交時間不符,之後 `.dev/reports/` 檔名一律用實際 UTC 時間。
- 本輪(3h)亦由同一 session 執行。
