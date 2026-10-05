# 票 145 Station 4i —— S5h-F1 最小修正(root 必須是 Git 工作樹的最上層)與本機驗收

- 日期:2026-10-05
- 對象:S4I1 `8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8`(只改 `.claude/hooks/redlight.py` 的 `_root_is_toplevel()`)。
- 上一個 commit:S3I2 `b11dc9eb49912d1a639534aca14aed31b24a9dec`;紅燈 S3I1 `260ede30628c7d205b30ac12c94be73a75cd2812`。
- 合約:票 145〈五十七〉57.3 裁決 3;Jeff 裁決 Station 3i = PASS / ACCEPTED、Station 4i plan = APPROVED、只改 `_root_is_toplevel()`、I1–I3 / H1 / H2 不准修改。
- 範圍:**本機(Windows)驗收**。POSIX 外部 clean-room 驗收尚未執行(第 9 節)。**本報告不宣稱 4i 完成。**（S4I4 後更新：POSIX 已 PASS，見第 9 節；Station 4i = PASS / COMPLETED。）

## 【給裁決者】

1. 修正:判「root 是不是工作樹最上層」改成兩個條件都要成立 —— Git 說「在工作樹裡」且「prefix 為空」;只看 prefix 會把 `.git/` 內和 bare repo 內也放行。
2. 本機全套 2099 passed、0 failed;3i 那兩支紅(I1 / I2)轉綠,I3 / H1 / H2 維持綠。
3. 淨室兩正三負全部成立,正二仍可退紅。
4. 本 repo 的測試帳本只往後加,淨室驗收前後完全沒動。
5. 下一步是 POSIX 外部淨室驗收(裁決助手執行),通過後才升級狀態。（S4I4 後更新：POSIX 已 PASS，見第 9 節；狀態已升級。）

## 【給裁決助手】

### 1. 修正內容(行號以 S4I1 為準)

| 位置 | 內容 |
|---|---|
| `.claude/hooks/redlight.py:726-728` docstring | 「root 是否就是 git 工作樹的最上層:須同時 `--is-inside-work-tree` 為 true 且 `--show-prefix` 為空 … 任一查詢失敗或條件不符 ⇒ False。」 |
| `:731-733` | 一次呼叫 `["git", "-C", os.fspath(root), "rev-parse", "--is-inside-work-tree", "--show-prefix"]` |
| `:734-737` | 例外 ⇒ False;returncode ≠ 0 ⇒ False(不變) |
| `:739-742` | `lines = proc.stdout.split(b"\n")`;`len(lines) < 2` ⇒ False;`lines[0].strip() == b"true" and lines[1].strip() == b""` 才 True |

- 未改:`committed_blobs` / `evidence_policy_facts` 的呼叫處、consumer(`_completeness_problems` / `_completeness_verdict`)、`policy_state`、`tests/conftest.py`、status.py / install.py / verify_gates.py、任何測試。
- `content_hash` 及其呼叫鏈未動;唯一 `return "true"` 位置不變(函式淨增 6 行,其後行號 +6)。
- 一次 Edit;寫入後以 `python .claude/portable/status.py --root .` 探針,輸出沒有「redlight.py 無 run 事實讀取」,Evidence 區為 `evidence policy: 有效`。

`git diff --cached` 全文(照錄時,diff 中空白 context 行原為單一空格,此處去除以通過 `git diff --cached --check`;原文可由 `git show 8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8` 重現):

```
diff --git a/.claude/hooks/redlight.py b/.claude/hooks/redlight.py
index d64d565..996f151 100644
--- a/.claude/hooks/redlight.py
+++ b/.claude/hooks/redlight.py
@@ -724,16 +724,22 @@ def _git_bytes(root, args):


 def _root_is_toplevel(root):
-    """root 是否就是 git 工作樹的最上層(`git rev-parse --show-prefix` 為空)。失敗 ⇒ False。"""
+    """root 是否就是 git 工作樹的最上層:須同時 `--is-inside-work-tree` 為 true 且 `--show-prefix` 為空
+    (票 145 Station 4i,S5h-F1:gitdir / bare repository 內 `--show-prefix` 同樣為空,但不是工作樹)。
+    任一查詢失敗或條件不符 ⇒ False。"""
     import subprocess
     try:
-        proc = subprocess.run(["git", "-C", os.fspath(root), "rev-parse", "--show-prefix"],
+        proc = subprocess.run(["git", "-C", os.fspath(root), "rev-parse",
+                               "--is-inside-work-tree", "--show-prefix"],
                               capture_output=True, timeout=30)
     except Exception:
         return False
     if proc.returncode != 0:
         return False
-    return proc.stdout.strip() == b""
+    lines = proc.stdout.split(b"\n")
+    if len(lines) < 2:
+        return False
+    return lines[0].strip() == b"true" and lines[1].strip() == b""


 def committed_blobs(root, paths=BLOB_FILES):
```

提交前檢查:

```
$ python -X utf8 -m py_compile .claude/hooks/redlight.py
(無輸出)
$ git diff --cached --name-only
.claude/hooks/redlight.py
$ git diff --cached --stat
 .claude/hooks/redlight.py | 12 +++++++++---
 1 file changed, 9 insertions(+), 3 deletions(-)
$ git diff --cached --check
(無輸出)
$ git commit -F .scratch/m1a-s4i/s4i-1-msg.txt
[master 8154a1a] fix(145): M1-a Station 4i-1 —— root 必須是 Git 工作樹的最上層(S5h-F1)
 1 file changed, 9 insertions(+), 3 deletions(-)
$ git rev-parse HEAD
8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8
$ git status --porcelain
(無輸出)
```

### 2. 3a 固定全套(S4I1 上只跑一次)

`python -X utf8 -m pytest -q > <session scratchpad>/s4i-run.txt 2>&1`,exit 0;之後 `git status --porcelain` 無輸出。

```
2099 passed, 3 skipped, 3 xfailed in 241.02s (0:04:01)
```

- collected 2105(2099 + 3 + 3)。0 failed;輸出沒有任何 `FAILED` / `ERROR` 行。
- I1 / I2 由紅轉綠(S3I1 上為僅有的兩個 FAILED),I3 / H1 / H2 維持綠。

### 3. 3b 帳本(以 B17 為前段基準;各自單獨執行)

```
$ head -c 845770 .dev/test-runs.jsonl > <session scratchpad>/r18.bin
$ head -c 14387323 .dev/test-sessions.jsonl > <session scratchpad>/s18.bin
$ sha256sum <session scratchpad>/r18.bin
5c91ea58af19e13d181af2c8ae471738d313d61b60a47fde20f40dfdbde10098 *<session scratchpad>/r18.bin
$ sha256sum <session scratchpad>/s18.bin
52ef61774703e5b9feff6de02462b878c22ce47b1cface87511b74d14e45ff1a *<session scratchpad>/s18.bin
$ wc -l .dev/test-runs.jsonl
3203 .dev/test-runs.jsonl
$ wc -l .dev/test-sessions.jsonl
31 .dev/test-sessions.jsonl
```

- 前段 sha256 = B17 ⇒ 只追加。test-runs 3156 → 3203(+47)、test-sessions 30 → 31(+1)。

### 4. 3c status(節錄原文)

```
test-runs: 本票 red 0 / green 47 / run 事實未知 0 / orphaned 0 / schema 不合格 run 0;最後一筆 tests/test_verify_gates.py=green @ 2026-10-05T17:04:33.377615+00:00;最近一次 run:A(exit 0;collected 2105 / deselected 0 / passed 2099 / failed 0 / skipped 3)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl)
evidence policy: 有效  (source: .agents/evidence-policy.json)
tests red under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests green (run 事實未知) under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests orphaned under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
```

- 原紅檔 `tests/test_redlight.py` 列在 `tests green under ticket 145`。

### 5. 3d 淨室

V0(各自單獨執行):

```
$ wc -c .dev/test-runs.jsonl
857289 .dev/test-runs.jsonl
$ wc -c .dev/test-sessions.jsonl
15126808 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl
9e9095205317807c48dc59c56841d468db7400ec8a418c58b24dd5cdadb28f6e *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
440406f60f5abe28a209c0c6ba082fc52bfc84227a6e84a96f8b3b3d81357784 *.dev/test-sessions.jsonl
```

`python .claude/portable/verify_gates.py <session scratchpad>/verify-gates4 > <session scratchpad>/s4i-verify.txt 2>&1`,exit 0。末段原文:

```
=== 逐條實測(每條各擋一次)===
    R1   擋下 ✓
    R2   擋下 ✓
    R3   擋下 ✓
    R4   擋下 ✓
    R5   擋下 ✓
    R6   擋下 ✓
    R7   擋下 ✓
    R8   擋下 ✓
    R9   擋下 ✓

=== 權威層偵測(只驗未安裝路徑)===
    hook 刪掉        -> 偵測到沒裝 ✓(找不到 pre-commit(查過 .git/hooks/pre-commit))
    別人的 hook 佔位 -> 偵測到沒裝 ✓(.git/hooks/pre-commit 存在,但它不呼叫 gate.py —— 那是別人的 hook 佔著位子,不是本框架的權威層。)
    裝回去           -> 偵測到已裝 ✓

=== 框架自己的測試,在這個新 repo 裡跑一次 ===
    1949 passed, 7 skipped, 3 xfailed in 230.83s (0:03:50)

=== evidence policy 淨室情境(兩正三負;每個情境各一行)===
    正一 未初始化                  成立 ✓  35 個框架測試檔皆 unknown=True;evidence policy: 未初始化
    正二 已初始化且相符               成立 ✓  rc 1→0;file_coverage=true;red=(無);green=tests/test_evidence_probe.py;evidence policy: 有效;1 passed in 8.89s
    負一 policy / 環境不符         成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 有效;1 passed in 0.26s
    負二 HEAD 有、工作樹不同          成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 工作樹與 HEAD 不同;1 passed in 0.21s
    負三 工作樹有、HEAD 沒有          成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 未提交;1 passed in 0.19s

全部 9 條規則各擋下一次,權威層偵測正常,框架測試在新 repo 全綠,evidence policy 兩正三負成立。
安裝位置:<session scratchpad>\verify-gates4\verify-gates-repo
```

(權威層偵測段與框架測試段之間的說明行未照錄;全文在 `<session scratchpad>/s4i-verify.txt`。)

事後(各自單獨執行):

```
$ wc -c .dev/test-runs.jsonl
857289 .dev/test-runs.jsonl
$ wc -c .dev/test-sessions.jsonl
15126808 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl
9e9095205317807c48dc59c56841d468db7400ec8a418c58b24dd5cdadb28f6e *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
440406f60f5abe28a209c0c6ba082fc52bfc84227a6e84a96f8b3b3d81357784 *.dev/test-sessions.jsonl
$ git status --porcelain
(無輸出)
```

⇒ 本 repo 兩本帳本前後 bytes 與 sha256 都等於 V0。五情境在同一次淨室執行中全部成立。

### 6. 裁決助手 Linux 預演(來源:Jeff 的 Station 4i 指令;隔離環境;**非本 repo 帳本證據**;非獨立審查 finding)

以 S3I1 的 tests 與 S4H1 的程式,I1 / I2 失敗於 got == "true"、I3 通過;套用本修正形狀後 I1 / I2 / I3 / H1 / H2 全綠,evidence 相關 5 檔 282 支全過。

### 7. 殘餘與未證明(目前尚未 machine-enforced)

1. 沿用 4h 證據報告(`docs/audits/2026-10-05-m1a-station4h-fix.md`)第 7 節全部項目(含其沿用的 4g 第 8 節),不擴張。
2. 5g 追蹤項:S5g-F1(下一張票優先)、S5g-F3、S5g-F4、S5g-F5;5h 追蹤項:S5h-F3(本節第 3 點已補準措辭)、S5h-F4(併入 S5g-F1 類的 operator / status 追蹤項)。
3. 本輪依 S5h-F3 補準的殘餘措辭(照錄):
   「本輪檢查的語意是 git rev-parse --is-inside-work-tree 為 true 且 --show-prefix 為空，即 root 必須是 Git 對該 root 解析出的工作樹的最上層。明確不支援（⇒ unknown）：monorepo 中非最上層的普通子目錄（H1）、位於 gitdir 或 bare repository 內的 root（I1 / I2）。會被接受但本輪未納入 acceptance、屬未證明：巢狀獨立 Git repo、submodule、linked worktree（git worktree add）、.git 為檔案且 gitdir 指向他處、GIT_DIR / GIT_WORK_TREE / core.worktree 等重新對應佈局。上述佈局若 Git 對該 root 實際回報 --is-inside-work-tree=true 且 --show-prefix 為空，即會被本檢查接受；其 HEAD 與工作樹是否符合既定 identity invariant，本輪未完整 acceptance，不得宣稱已拒絕或已支援。」
4. 本機只驗 Windows。（S4I4 後更新：POSIX 已 PASS，見第 9 節；屬裁決助手外部驗證，非本 repo 帳本證據。）

### 8. 程序紀錄

- 外來 3 檔以 `git stash push -u -m jeff-mods-recon-20261004-s4i -- <3 檔>` 收起,本輪結束後 `git stash pop` 放回。
- 沒有閘門擋下;沒有改測試、`.dev/pipeline.json`;沒有 push / fetch。
- 依 Jeff 身分更正,本 session 自 3h 起為實作 session;5i 審查須開全新對話,5g / 5h 審查 session 與本 session 皆不得擔任。

### 9. POSIX 外部 clean-room 驗收

> **舊文字(F-036,保留不刪)**:本節標題原為 ~~`### 9. POSIX 外部 clean-room 驗收:待執行(裁決助手)`~~,沒有內文。
> 2026-10-05 S4I4 依 Jeff 裁決改為下方照錄段落。

POSIX 外部 clean-room 驗收（裁決助手；隔離環境；非本 repo 帳本證據）——2026-10-05 約 13:20 ET
- 環境：Linux，Python 3.11.16，pytest 9.1.1，anyio 4.15.0，git 2.43.0。
- 受測樹：4h POSIX 驗收所用的樹再覆蓋 S3I1 的 tests/test_redlight.py 與 S4I1 8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8 的 .claude/hooks/redlight.py 原檔（CRLF→LF）。
- 修正前（S3I1 tests + S4H1 程式）：I1 / I2 失敗於 got == "true"、I3 通過，與 Windows 3i 一致。
- 修正後：verify_gates.py R1–R9 各擋下一次；權威層偵測三項成立；淨室框架測試 0 failed；evidence policy 兩正三負全部成立：
    正一 未初始化 成立（35 個框架測試檔皆 unknown；evidence policy: 未初始化）
    正二 已初始化且相符 成立（rc 1→0；file_coverage=true；green=tests/test_evidence_probe.py；evidence policy: 有效）
    負一 policy / 環境不符 成立（file_coverage=unknown；紅仍在）
    負二 HEAD 有、工作樹不同 成立（file_coverage=unknown；evidence policy: 工作樹與 HEAD 不同）
    負三 工作樹有、HEAD 沒有 成立（file_coverage=unknown；evidence policy: 未提交）
- 宿主固定全套（Linux）：collected 2105；2089 passed、13 failed、3 xfailed。13 支與 4g / 4h POSIX 驗收及 de36ebc 基準在同一沙盒的失敗集合完全相同（tests/test_gate.py::TestAuthorityLayerIsWired::test_this_repo_itself_is_wired 與 tests/test_known_items_regression.py 的 12 支）⇒ 沙盒環境因素（推測：clone 未設 hooksPath、缺本機私有資料），與 3i/4i 無關。evidence 相關 5 檔（含 I1–I3 / H1–H2）全過。
- 結論：POSIX 外部 clean-room 驗收 PASS。
