# 票 145 Station 3i —— S5h-F1 / S5h-F2 補紅燈(root 必須是 Git 工作樹的最上層)

- 日期:2026-10-05
- 合約:票 145〈五十七〉57.3 裁決 2、3;Jeff 裁決 S5h-1 = accepted。
- 上一個 commit:S5h-1 `b62346136cd5ce3bcb0e8dfbc78e3c827f7da849`。
- 紅燈 commit:S3I1 `260ede30628c7d205b30ac12c94be73a75cd2812`。
- 範圍:只新增 3 支測試;不改產品碼、不改既有測試、不改 `.dev/pipeline.json`。

## 【給裁決者】

1. 加了 3 支測試,對應 S5h-F1(root 在 `.git/` 內或 bare repo 內也能退紅)與 S5h-F2(`committed_blobs` 那一半沒有測試鎖住)。
2. 紅燈全套只跑一次:恰好 2 支紅,就是 I1、I2;I3(直接驗 `committed_blobs`)、H1、H2 都是綠的。
3. 帳本只往後加,舊內容沒有被改。
4. 外來 3 檔照前例先收起、做完再放回。
5. 下一步是 Station 4i 最小修正(`--is-inside-work-tree` 為 true 且 `--show-prefix` 為空)。

## 【給裁決助手】

### 1. S3I1

`tests/test_redlight.py` 檔尾新增 `class TestEvidenceRootIsInsideWorkTree`;既有 helper(`_g_default_root` / `_g_coverage` / `_G_POLICY_FILE` / `_d_git` / `redlight.committed_blobs` / `redlight.BLOB_FILES`)只呼叫、不修改。class 內私有 `_copy_into`(staticmethod)負責逐檔 `read_bytes` → `mkdir(parents=True, exist_ok=True)` → `write_bytes`。

```
$ python -X utf8 -m py_compile tests/test_redlight.py
(無輸出)
$ git diff --cached --name-only
tests/test_redlight.py
$ git diff --cached --check
(無輸出)
$ git diff --cached -U0 -- tests/test_redlight.py   → 恰一個 hunk,只有 + 行
@@ -2576,0 +2577,72 @@ class TestEvidenceRootIsGitToplevel:
$ git commit -F .scratch/m1a-s3i/s3i-1-msg.txt
[master 260ede3] test(145): M1-a Station 3i-1 —— root 必須是 Git 工作樹最上層的紅燈(S5h-F1 / S5h-F2;3 支)
 1 file changed, 72 insertions(+)
$ git rev-parse HEAD
260ede30628c7d205b30ac12c94be73a75cd2812
$ git status --porcelain
(無輸出)
```

| nodeid | 分類 | 在 S5h-1 上 |
|---|---|---|
| `tests/test_redlight.py::TestEvidenceRootIsInsideWorkTree::test_i3_a_root_inside_the_gitdir_is_not_full_coverage` | I1 behavior-red | 必須失敗 |
| `tests/test_redlight.py::TestEvidenceRootIsInsideWorkTree::test_i3_a_root_inside_a_bare_repository_is_not_full_coverage` | I2 behavior-red | 必須失敗 |
| `tests/test_redlight.py::TestEvidenceRootIsInsideWorkTree::test_i3_committed_blobs_alone_is_fail_closed_for_a_subdirectory_root` | I3 regression-lock | 必須通過 |

- I1:最上層 `parent` 已提交合法 policy、`pyproject.toml`、`tests/conftest.py`;root = `parent/.git`,三份位元組相同的副本只在 root 下、從未提交 ⇒ `file_coverage` 不得為 `"true"`。
- I2:以 `parent` 建 bare clone(`_d_git(tmp_path, "clone", "-q", "--bare", …)`);root = `bare.git/proj`,同上 ⇒ 不得為 `"true"`。
- I3:不經 `evidence_policy_facts`,直接 `redlight.committed_blobs(str(sub))`(`sub` 下只有 `pyproject.toml` 與 `tests/conftest.py` 的未提交副本)⇒ `BLOB_FILES` 每一路徑皆 `{"worktree": None, "head": None}`;對照組 `committed_blobs(str(parent))` 每一路徑 worktree 非空且 == head。

### 2. 紅燈全套(在 S3I1 上只跑一次)

指令:`python -X utf8 -m pytest -q > <session scratchpad>/s3i1-run.txt 2>&1`,exit 1;之後 `git status --porcelain` 無輸出。

I1 實際失敗段(輸出檔第 50–55 行):

```
        got = _g_coverage(root, monkeypatch)
>       assert got != "true", got
E       AssertionError: true
E       assert 'true' != 'true'

tests\test_redlight.py:2613: AssertionError
```

I2 實際失敗段(輸出檔第 75–80 行):

```
        got = _g_coverage(root, monkeypatch)
>       assert got != "true", got
E       AssertionError: true
E       assert 'true' != 'true'

tests\test_redlight.py:2629: AssertionError
```

FAILED 行與摘要行(輸出檔第 88–90 行):

```
FAILED tests/test_redlight.py::TestEvidenceRootIsInsideWorkTree::test_i3_a_root_inside_the_gitdir_is_not_full_coverage
FAILED tests/test_redlight.py::TestEvidenceRootIsInsideWorkTree::test_i3_a_root_inside_a_bare_repository_is_not_full_coverage
2 failed, 2097 passed, 3 skipped, 3 xfailed in 256.98s (0:04:16)
```

- collected 2105(2 + 2097 + 3 + 3)。FAILED 恰為 I1、I2,皆失敗於 `got == "true"`;I3、H1、H2 在 2097 passed 之內。與預期相符。
- S5h-F1 在本樹(Windows)端到端重現:5h 審查報告標「需要重現」的那一項,I1 / I2 實跑即為重現。

### 3. 帳本

基準(Step 0):test-runs 834066 bytes / 3109 行 / `5f0ffa92…`;test-sessions 13647838 bytes / 29 行 / `74757aa6…`。

```
$ head -c 834066 .dev/test-runs.jsonl > <session scratchpad>/r17.bin
$ head -c 13647838 .dev/test-sessions.jsonl > <session scratchpad>/s17.bin
$ sha256sum <session scratchpad>/r17.bin
5f0ffa923b38a4bd7b51b4c3580212fd8dc5e8f050e5f3f1c07f08b177b7934a *<session scratchpad>/r17.bin
$ sha256sum <session scratchpad>/s17.bin
74757aa64374588adaec7918bce4e86f30a8a3b430869c352f3c51b84c66b182 *<session scratchpad>/s17.bin
$ wc -l .dev/test-runs.jsonl
3156 .dev/test-runs.jsonl
$ wc -l .dev/test-sessions.jsonl
30 .dev/test-sessions.jsonl
$ wc -c .dev/test-runs.jsonl
845770 .dev/test-runs.jsonl
$ wc -c .dev/test-sessions.jsonl
14387323 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl
5c91ea58af19e13d181af2c8ae471738d313d61b60a47fde20f40dfdbde10098 *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
52ef61774703e5b9feff6de02462b878c22ce47b1cface87511b74d14e45ff1a *.dev/test-sessions.jsonl
```

- 前段 sha256 = 基準 ⇒ 只追加。
- test-runs 3109 → 3156 行(+47)、test-sessions 29 → 30 行(+1)。
- 跑後全檔記為 B17(845770 / 14387323;`5c91ea58…` / `52ef6177…`),供 4i 使用。

### 4. 裁決助手 Linux 預演(來源:Jeff 的 Station 3i 指令;隔離環境;**非本 repo 帳本證據**;非獨立審查 finding)

以 S4H1 的 redlight.py,I1 / I2 原型皆失敗於 got == "true";I3 原型通過。套用 4i 修法原型(`--is-inside-work-tree` 為 true 且 `--show-prefix` 為空)後 I1 / I2 / I3 / H1 / H2 全綠,evidence 相關 5 檔 281 支全過。

### 5. 程序紀錄

- 外來 3 檔以 `git stash push -u -m jeff-mods-recon-20261004-s3i -- <3 檔>` 收起(Jeff 已同意),本輪結束後 `git stash pop` 放回。
- **身分更正(Jeff 裁決)**:本 session 自 3h 起為事實上的實作 session(3h、4h、5h-0、5h-1 皆由本 session 執行);3i / 4i 繼續由本 session 執行;5i 審查須開全新對話,5g / 5h 審查 session 與本 session 皆不得擔任。
- 沒有閘門擋下;沒有改產品碼、既有測試、`.dev/pipeline.json`;沒有 push / fetch。
