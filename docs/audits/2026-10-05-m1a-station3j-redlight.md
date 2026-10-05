# 票 145 Station 3j —— S5i-F1 / S5i-F3 補紅燈(`_root_is_toplevel` 的 stdout contract)

- 日期:2026-10-05
- 合約:票 145〈六十一〉61.3 裁決 2、3;Jeff 特別核准 J1 為 POSIX-only behavior-red、Windows 以 skipif 跳過。
- 上一個 commit:S5i-1 `ff859253ec74ee778ffc868307a4d66d452e4040`。
- 紅燈 commit:S3J1 `9990fd654275a0af25fa51ce374dea3e812ef54e`。
- 範圍:只新增 2 支測試(J2 參數化 4 案);不改產品碼、不改既有測試、不改 `.dev/pipeline.json`。

## 【給裁決者】

1. 加了 2 支測試:J1 抓「名稱以換行開頭的子目錄被誤認成最上層」(S5i-F1),J2 直接鎖住判斷函式四種佈置的正確答案(S5i-F3)。
2. Windows 不能建出含換行的檔名,所以 J1 在 Windows 依你的核准跳過;J1 修前會紅這件事,證據在裁決助手的 Linux 預演(第 4 節)。
3. Windows 全套只跑一次:0 失敗,J1 跳過、J2 四案全綠。結果和預期完全一致。
4. 帳本只往後加,舊內容沒有被改。外來 3 檔照前例先收起、做完再放回。
5. 下一步是 Station 4j 最小修正(stdout 正規化後須完整等於 `b"true\n\n"`)。

## 【給裁決助手】

### 1. S3J1

`tests/test_redlight.py` 檔尾新增 `class TestRootIsToplevelContract`;既有 helper(`_g_default_root` / `_g_coverage` / `_G_POLICY_FILE` / `_d_git` / `redlight._root_is_toplevel`)只呼叫、不修改。class 內私有 `_copy_into`(staticmethod)負責逐檔 `read_bytes` → `mkdir(parents=True, exist_ok=True)` → `write_bytes`。檔頭沒有 `import sys`,依指令在 class 內 `import sys`(未動檔頭 import 區),供 J1 的 `skipif` 在 class body 內取用。

```
$ python -X utf8 -m py_compile tests/test_redlight.py
(無輸出)
$ git diff --cached --name-only
tests/test_redlight.py
$ git diff --cached --check
(無輸出)
$ git diff --cached -U0 -- tests/test_redlight.py   → 恰一個 hunk,只有 + 行
@@ -2648,0 +2649,66 @@ class TestEvidenceRootIsInsideWorkTree:
$ git commit -F .scratch/m1a-s3j/s3j-1-msg.txt
[master 9990fd6] test(145): M1-a Station 3j-1 —— _root_is_toplevel stdout contract 紅燈(S5i-F1 / S5i-F3;2 支)
 1 file changed, 66 insertions(+)
$ git rev-parse HEAD
9990fd654275a0af25fa51ce374dea3e812ef54e
$ git status --porcelain
(無輸出)
```

| nodeid | 分類 | 在 S5i-1 上 |
|---|---|---|
| `tests/test_redlight.py::TestRootIsToplevelContract::test_j3_a_lf_prefixed_subdirectory_root_is_not_full_coverage` | J1 behavior-red(**POSIX-only**;Windows `skipif(sys.platform == "win32")`,Jeff 特別核准) | POSIX 必須失敗;Windows skipped |
| `tests/test_redlight.py::TestRootIsToplevelContract::test_j3_root_is_toplevel_follows_the_stdout_contract[toplevel]` | J2 regression-lock | 必須通過(True) |
| `tests/test_redlight.py::TestRootIsToplevelContract::test_j3_root_is_toplevel_follows_the_stdout_contract[subdir]` | J2 regression-lock | 必須通過(False) |
| `tests/test_redlight.py::TestRootIsToplevelContract::test_j3_root_is_toplevel_follows_the_stdout_contract[gitdir]` | J2 regression-lock | 必須通過(False) |
| `tests/test_redlight.py::TestRootIsToplevelContract::test_j3_root_is_toplevel_follows_the_stdout_contract[bare]` | J2 regression-lock | 必須通過(False) |

- J1:最上層 `parent` 已提交合法 policy、`pyproject.toml`、`tests/conftest.py`;root = `parent / "\nsub"`,三份位元組相同的副本只在 root 下、從未提交 ⇒ `file_coverage` 不得為 `"true"`。
- J2:直接呼叫 `redlight._root_is_toplevel(str(root))`:toplevel = `parent` ⇒ True;subdir = `parent/sub`(mkdir)⇒ False;gitdir = `parent/.git` ⇒ False;bare = `_d_git(tmp_path, "clone", "-q", "--bare", …)` 後的 `bare.git/proj`(mkdir)⇒ False。

### 2. 紅燈全套(在 S3J1 上只跑一次;Windows)

指令:`python -X utf8 -m pytest -q > <session scratchpad>/s3j1-run.txt 2>&1`,exit 0;之後 `git status --porcelain` 無輸出。

SKIPPED 行(輸出檔第 32–35 行;第 35 行為 J1):

```
SKIPPED [1] tests\test_gate.py:451: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:459: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:473: 此環境無法建立 symlink
SKIPPED [1] tests\test_redlight.py:2673: Windows 檔名不得含 LF;本案例由 POSIX 驗收證明(〈六十一〉61.3 裁決 2)
```

摘要行(輸出檔第 39 行):

```
2103 passed, 4 skipped, 3 xfailed in 253.83s (0:04:13)
```

- collected 2110(2103 + 4 + 3)。0 failed;輸出沒有 `FAILED` / `ERROR` 行。
- 4 skipped = 既有 3 + J1;J2 四案、I1–I3、H1–H2 在 2103 passed 之內。與預期相符。
- J1 在 Windows 沒有跑,所以**本節不是 J1 的紅燈證據**;J1 修前 red 的證據見第 4 節(裁決助手 POSIX)。

### 3. 帳本

基準(Step 0):test-runs 857289 bytes / 3203 行 / `9e909520…`;test-sessions 15126808 bytes / 31 行 / `440406f6…`。

```
$ head -c 857289 .dev/test-runs.jsonl > <session scratchpad>/r19.bin
$ head -c 15126808 .dev/test-sessions.jsonl > <session scratchpad>/s19.bin
$ sha256sum <session scratchpad>/r19.bin
9e9095205317807c48dc59c56841d468db7400ec8a418c58b24dd5cdadb28f6e *<session scratchpad>/r19.bin
$ sha256sum <session scratchpad>/s19.bin
440406f60f5abe28a209c0c6ba082fc52bfc84227a6e84a96f8b3b3d81357784 *<session scratchpad>/s19.bin
$ wc -l .dev/test-runs.jsonl
3250 .dev/test-runs.jsonl
$ wc -l .dev/test-sessions.jsonl
32 .dev/test-sessions.jsonl
$ wc -c .dev/test-runs.jsonl
868808 .dev/test-runs.jsonl
$ wc -c .dev/test-sessions.jsonl
15868084 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl
9abb70439a21bc07c60c3f413f619b9851080dfe265ecd2faf2eeca5303ef7b1 *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
767488b978c7a8ef84da1da57733455f361dd30c44970bd3b78e79708d92159d *.dev/test-sessions.jsonl
```

- 前段 sha256 = 基準 ⇒ 只追加。
- test-runs 3203 → 3250 行(+47)、test-sessions 31 → 32 行(+1)。
- 跑後全檔記為 B19(868808 / 15868084;`9abb7043…` / `767488b9…`),供 4j 使用。

### 4. 裁決助手 Linux 預演(來源:Jeff 的 Station 3j 指令;隔離環境;**非本 repo 帳本證據**;非獨立審查 finding)

以 S4I1 的 redlight.py,J1 原型失敗於 got == "true"、J2 原型四案全過;套用 4j 修法原型(stdout 正規化後 == b"true\n\n")後 J1 轉綠、J2 維持綠、I1–I3 / H1–H2 綠,evidence 相關 5 檔 283 支全過。

- **J1 修前 red 的證據在此**(POSIX);〈六十一〉61.3 裁決 2 要求 3j 的 POSIX 證據保留「修前 J1 red、修後 green」,不得只看 4j 最終全綠。

### 5. 程序紀錄

- 外來 3 檔以 `git stash push -u -m jeff-mods-recon-20261004-s3j -- <3 檔>` 收起,本輪結束後 `git stash pop` 放回。
- 沒有閘門擋下;沒有改產品碼、既有測試、`.dev/pipeline.json`;沒有 push / fetch。
- 本輪由實作 session 執行;5j 審查依裁決須用第五個全新對話。

### 6. 3j-1b:R3 攔截與 Windows 可紅的解析層紅燈

#### 6.1 R3 攔截原文(4j S4J1 的 Edit;照錄自 `.dev/reports/2026-10-05T184454Z-ticket145-station4j-blocked-r3.md`)

```
PreToolUse:Edit hook error: [python "$CLAUDE_PROJECT_DIR/.claude/hooks/gate.py"]: [六站閘門/前哨] [R3/紅燈][enforce] .claude/hooks/redlight.py:測試檔存在,但沒有合格的紅燈紀錄。
     tests/test_redlight.py 有執行紀錄,但沒有任何一筆是「紅燈,且發生在這次改動之前」。
     合格的形狀:實作當時不存在,或紅燈是對著這支檔案在 HEAD 的
     內容跑出來的。先寫實作再補跑紅燈不算 —— 那是補測試,不是紅綠燈。
     先跑測試確認它在實作不存在時是紅的,再回來寫功能碼。
(權威判定在 pre-commit,繞過前哨仍會在 commit 被擋)
```

- 成因:J1 在 Windows 被 skipif 跳過、J2 本來就綠 ⇒ 本機帳本對 S4I1 版 `redlight.py` 沒有任何 `tests/test_redlight.py` 紅燈;J1 的紅燈只在裁決助手的 Linux 證據裡,R3 看不到。
- 裁決(Jeff):R3 擋下 = 照設計;選 A —— 補一支 Windows 可紅的解析層 behavior-red;不走豁免、不換環境。

#### 6.2 S3J1B

`tests/test_redlight.py` 檔尾(既有 `TestRootIsToplevelContract` 之後)新增 `class TestRootIsToplevelParser`;以 monkeypatch 把 `subprocess.run` 換成回傳 stdout `b"true\n\nsub/\n"`(returncode 0)的替身,不依賴檔案系統;`subprocess` 於測試內 import(未動檔頭);既有 helper 只呼叫、不修改。

```
$ python -X utf8 -m py_compile tests/test_redlight.py
(無輸出)
$ git diff --cached --name-only
tests/test_redlight.py
$ git diff --cached --check
(無輸出)
$ git diff --cached -U0 -- tests/test_redlight.py   → 恰一個 hunk,只有 + 行
@@ -2714,0 +2715,36 @@ class TestRootIsToplevelContract:
$ git commit -F .scratch/m1a-s3j/s3j-1b-msg.txt
[master 35d100a] test(145): M1-a Station 3j-1b —— Windows 可紅的 _root_is_toplevel 解析層紅燈(S5i-F1;1 支)
 1 file changed, 36 insertions(+)
$ git rev-parse HEAD
35d100a3841486e2d75ba39aea71bda601e18075
$ git status --porcelain
(無輸出)
```

| nodeid | 分類 | 在 S3J2 上 |
|---|---|---|
| `tests/test_redlight.py::TestRootIsToplevelParser::test_j3_a_lf_prefixed_show_prefix_stdout_is_not_toplevel` | J1b behavior-red(解析層;Windows 可紅;與 J1 POSIX 端到端互補) | 必須失敗 |

#### 6.3 紅燈全套(在 S3J1B 上只跑一次;Windows)

指令:`python -X utf8 -m pytest -q > <session scratchpad>/s3j1b-run.txt 2>&1`,exit 1;之後 `git status --porcelain` 無輸出。

J1b 實際失敗段(輸出檔第 61–66 行;路徑中的本機使用者名稱遮為 `<user>`):

```
E       AssertionError: assert True is False
E        +  where True = <function _root_is_toplevel at 0x000002114AD47560>('C:\\Users\\<user>\\AppData\\Local\\Temp\\pytest-of-<user>\\pytest-225\\test_j3_a_lf_prefixed_show_pre0')
E        +    where <function _root_is_toplevel at 0x000002114AD47560> = redlight._root_is_toplevel
E        +    and   'C:\\Users\\<user>\\AppData\\Local\\Temp\\pytest-of-<user>\\pytest-225\\test_j3_a_lf_prefixed_show_pre0' = str(WindowsPath('C:/Users/<user>/AppData/Local/Temp/pytest-of-<user>/pytest-225/test_j3_a_lf_prefixed_show_pre0'))

tests\test_redlight.py:2749: AssertionError
```

J1 的 SKIPPED 行(輸出檔第 71 行)、FAILED 行與摘要行(輸出檔第 75–76 行):

```
SKIPPED [1] tests\test_redlight.py:2673: Windows 檔名不得含 LF;本案例由 POSIX 驗收證明(〈六十一〉61.3 裁決 2)
FAILED tests/test_redlight.py::TestRootIsToplevelParser::test_j3_a_lf_prefixed_show_prefix_stdout_is_not_toplevel
1 failed, 2103 passed, 4 skipped, 3 xfailed in 238.90s (0:03:58)
```

- collected 2111(1 + 2103 + 4 + 3)。唯一的 FAILED 是 J1b,失敗於 `assert True is False`;J1 skipped;J2 四案、I1–I3、H1–H2 在 passed 之內。與預期相符。

status(Derived 節錄)—— R3 要的本機紅燈:

```
tests red under ticket 145: tests/test_redlight.py  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
```

#### 6.4 帳本

基準(Step 0)= B19:test-runs 868808 bytes / 3250 行 / `9abb7043…`;test-sessions 15868084 bytes / 32 行 / `767488b9…`。

```
$ head -c 868808 .dev/test-runs.jsonl > <session scratchpad>/r21.bin
$ head -c 15868084 .dev/test-sessions.jsonl > <session scratchpad>/s21.bin
$ sha256sum <session scratchpad>/r21.bin
9abb70439a21bc07c60c3f413f619b9851080dfe265ecd2faf2eeca5303ef7b1 *<session scratchpad>/r21.bin
$ sha256sum <session scratchpad>/s21.bin
767488b978c7a8ef84da1da57733455f361dd30c44970bd3b78e79708d92159d *<session scratchpad>/s21.bin
$ wc -l .dev/test-runs.jsonl
3297 .dev/test-runs.jsonl
$ wc -l .dev/test-sessions.jsonl
33 .dev/test-sessions.jsonl
$ wc -c .dev/test-runs.jsonl
880409 .dev/test-runs.jsonl
$ wc -c .dev/test-sessions.jsonl
16609700 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl
670237025036aeef8fd427aaccb6c9d2fae9ed624d1f38b2f8b23d2c16fc6ee5 *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
2badaee4cc130d1ec9fed57ffbac1c093ccee20c9c5547189caf576d5cbcad0b *.dev/test-sessions.jsonl
```

- 前段 sha256 = B19 ⇒ 只追加。test-runs 3250 → 3297(+47)、test-sessions 32 → 33(+1)。
- 跑後全檔記為 B21(880409 / 16609700;`67023702…` / `2badaee4…`),供 4j 使用。

#### 6.5 裁決助手 Linux 預演(來源:Jeff 的 Station 3j-1b 指令;隔離環境;**非本 repo 帳本證據**)

J1b 以 monkeypatch 替身在 S4I1 的 redlight.py 上失敗(assert True is False),在 4j 修法原型上通過。

#### 6.6 程序紀錄

- 第一次送出 3j-1b 指令時,`.dev/pipeline.json` 為 `implement`(指令要求 `tickets`),依規定在 Step 0 停手(`.dev/reports/2026-10-05T184923Z-ticket145-station3j1b-stopped-stage.md`);Jeff 切回 `tickets` 後重送,本節為重送後的結果。
- 外來 3 檔以 `git stash push -u -m jeff-mods-recon-20261004-s3j1b -- <3 檔>` 收起,本輪結束後 `git stash pop` 放回。
- 沒有閘門擋下;沒有改產品碼、既有測試、`.dev/pipeline.json`;沒有 push / fetch。
