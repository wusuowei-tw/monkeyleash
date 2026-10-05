# 票 145 Station 4h —— S5g-F2 最小修正(evidence root 必須是 Git 最上層)與本機驗收

- 日期:2026-10-05
- 對象:S4H1 `ea6aba6452668982fee56f7a2f0faf2cd720ca6d`(只改 `.claude/hooks/redlight.py`)。
- 上一個 commit:S3H2 `66140896d03f32c4df73be01b2aaeb48353e0510`;紅燈 S3H1 `7621e3ce8604ab72ab2f3fb3257cb1181b8a126e`。
- 合約:票 145〈五十三〉53.3 裁決 2;Jeff 裁決 Station 3h = PASS / ACCEPTED、Station 4h plan = APPROVED、H1 / H2 不准修改、最小修正只動 redlight.py。
- 範圍:**本機(Windows)驗收**。POSIX 外部 clean-room 驗收尚未執行(第 7 節)。**本報告不宣稱 4h 完成。**

## 【給裁決者】

1. 修正:證據根目錄必須就是 Git 最上層;不是的話,policy 與設定檔的事實一律記「取不到」,這次執行就不能退紅。
2. 本機全套 2096 passed、0 failed;3h 那支紅(H1)轉綠,H2 維持綠。
3. 淨室(全新安裝的乾淨 repo)兩正三負全部成立,正二仍可退紅。
4. 本 repo 的測試帳本只往後加,淨室驗收前後完全沒動。
5. 下一步是 POSIX 外部淨室驗收(裁決助手執行),通過後才升級狀態。

## 【給裁決助手】

### 1. 修正內容(行號以 S4H1 為準)

| 位置 | 內容 |
|---|---|
| `.claude/hooks/redlight.py:726` `_root_is_toplevel(root)` | `git -C <root> rev-parse --show-prefix`;例外 / returncode ≠ 0 ⇒ False;stdout strip 後為空才 True |
| `:752` / `:755` `committed_blobs` | 迴圈前算 `top`;不是最上層 ⇒ 每個路徑記 `{"worktree": None, "head": None}`,不呼叫 git |
| `:868` `evidence_policy_facts` | try 內第一步:不是最上層 ⇒ 回傳全 None |
| 兩個函式 docstring | 補 I-3 位置不變式一段(見 diff) |

- 未改:consumer(`_completeness_problems` / `_completeness_verdict`)、`policy_state` 的判定字串、`tests/conftest.py`、status.py / install.py / verify_gates.py、任何測試。
- `content_hash`(`:47`)及其呼叫的函式未改;唯一 `return "true"` 在 `:1152`(行號因上方新增 25 行而位移)。
- 編輯分兩刀,每刀後以 `python .claude/portable/status.py --root .` 探針;兩次輸出都沒有「redlight.py 無 run 事實讀取」,Evidence 區皆為 `evidence policy: 有效`。

`git diff --cached` 全文(照錄時,diff 中空白 context 行原為單一空格,此處去除以通過 `git diff --cached --check`;原文可由 `git show ea6aba6452668982fee56f7a2f0faf2cd720ca6d` 重現):

```
diff --git a/.claude/hooks/redlight.py b/.claude/hooks/redlight.py
index 0616c17..d64d565 100644
--- a/.claude/hooks/redlight.py
+++ b/.claude/hooks/redlight.py
@@ -723,6 +723,19 @@ def _git_bytes(root, args):
     return proc.stdout if proc.returncode == 0 else None


+def _root_is_toplevel(root):
+    """root 是否就是 git 工作樹的最上層(`git rev-parse --show-prefix` 為空)。失敗 ⇒ False。"""
+    import subprocess
+    try:
+        proc = subprocess.run(["git", "-C", os.fspath(root), "rev-parse", "--show-prefix"],
+                              capture_output=True, timeout=30)
+    except Exception:
+        return False
+    if proc.returncode != 0:
+        return False
+    return proc.stdout.strip() == b""
+
+
 def committed_blobs(root, paths=BLOB_FILES):
     """`{path: {"worktree": blob, "head": blob}}` —— 工作樹檔案(`git hash-object`,依
     .gitattributes 正規化)與 `HEAD:<path>` 的 blob。〈二十九〉2 (xi)。
@@ -731,10 +744,17 @@ def committed_blobs(root, paths=BLOB_FILES):
     **逐路徑各呼叫一次 git**(票 145 Station 4g;規劃檔 P3 遷移第 3 點):一次處理全部路徑的話,
     缺一個檔整次失敗、所有路徑都成 None —— 淨室 repo 沒有 pyproject 時,conftest 的 blob 也一起遺失。
     **不拋例外**:這是 producer 在 sessionfinish 呼叫的,不得讓 pytest 失敗。
+    root 必須是 git 最上層(I-3 位置不變式;票 145 Station 4h,S5g-F2):HEAD:<path> 以最上層為基準、
+    hash-object 以 root 為基準,root 不是最上層時兩者不是同一邏輯路徑 ⇒ 事實一律 None ⇒ unknown。
+    框架目前只支援一個 host evidence root = 一個 Git 最上層。
     """
     out = {}
+    top = _root_is_toplevel(root)
     for p in list(paths):
         entry = {"worktree": None, "head": None}
+        if not top:
+            out[p] = entry
+            continue
         try:
             worktree = _git_lines(root, ["hash-object", p], 1)
             head = _git_lines(root, ["rev-parse", "HEAD:" + p], 1)
@@ -838,10 +858,15 @@ def evidence_policy_facts(root):
     回傳 7 鍵 `{"path", "head", "worktree", "schema", "version", "policy", "committed_addopts"}`
     (〈五十一〉裁決 3);走不下去的那一步之後的欄位都是 None。
     **只擷取事實,不判定** —— 型別、schema、邊界、鎖步都由 consumer 驗。不拋例外(sessionfinish 呼叫)。
+    root 必須是 git 最上層(I-3 位置不變式;票 145 Station 4h,S5g-F2):HEAD:<path> 以最上層為基準、
+    hash-object 以 root 為基準,root 不是最上層時兩者不是同一邏輯路徑 ⇒ 事實一律 None ⇒ unknown。
+    框架目前只支援一個 host evidence root = 一個 Git 最上層。
     """
     out = {"path": POLICY_FILE, "head": None, "worktree": None, "schema": None,
            "version": None, "policy": None, "committed_addopts": None}
     try:
+        if not _root_is_toplevel(root):
+            return out
         head = _git_lines(root, ["rev-parse", "HEAD:" + POLICY_FILE], 1)
         if not head:
             return out
```

提交前檢查:

```
$ python -X utf8 -m py_compile .claude/hooks/redlight.py
(無輸出)
$ git diff --cached --name-only
.claude/hooks/redlight.py
$ git diff --cached --stat
 .claude/hooks/redlight.py | 25 +++++++++++++++++++++++++
 1 file changed, 25 insertions(+)
$ git diff --cached --check
(無輸出)
$ git commit -F .scratch/m1a-s4h/s4h-1-msg.txt
[master ea6aba6] fix(145): M1-a Station 4h-1 —— evidence root 必須是 Git 最上層(S5g-F2)
 1 file changed, 25 insertions(+)
$ git rev-parse HEAD
ea6aba6452668982fee56f7a2f0faf2cd720ca6d
$ git status --porcelain
(無輸出)
```

### 2. 3a 固定全套(S4H1 上只跑一次)

`python -X utf8 -m pytest -q > <session scratchpad>/s4h-run.txt 2>&1`,exit 0;之後 `git status --porcelain` 無輸出。

```
2096 passed, 3 skipped, 3 xfailed in 380.00s (0:06:19)
```

- collected 2102(2096 + 3 + 3)。0 failed;輸出沒有任何 `FAILED` / `ERROR` 行。
- H1 由紅轉綠(S3H1 上為唯一 FAILED),H2 維持綠。

### 3. 3b 帳本(以 B15 為前段基準;各自單獨執行)

```
$ head -c 822547 .dev/test-runs.jsonl > <session scratchpad>/r16.bin
$ head -c 12909484 .dev/test-sessions.jsonl > <session scratchpad>/s16.bin
$ sha256sum <session scratchpad>/r16.bin
49fc32bc88ad7eb93840e070154953980fa40122388c2fce49645b411a254789 *<session scratchpad>/r16.bin
$ sha256sum <session scratchpad>/s16.bin
0539883a5548a9032ed0877aab4614bdde6fd748103a3db2524de99e9c589674 *<session scratchpad>/s16.bin
$ wc -l .dev/test-runs.jsonl
3109 .dev/test-runs.jsonl
$ wc -l .dev/test-sessions.jsonl
29 .dev/test-sessions.jsonl
```

- 前段 sha256 = B15 ⇒ 只追加。test-runs 3062 → 3109(+47)、test-sessions 28 → 29(+1)。

### 4. 3c status(節錄原文)

```
test-runs: 本票 red 0 / green 47 / run 事實未知 0 / orphaned 0 / schema 不合格 run 0;最後一筆 tests/test_verify_gates.py=green @ 2026-10-05T13:22:26.290054+00:00;最近一次 run:A(exit 0;collected 2102 / deselected 0 / passed 2096 / failed 0 / skipped 3)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl)
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
834066 .dev/test-runs.jsonl
$ wc -c .dev/test-sessions.jsonl
13647838 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl
5f0ffa923b38a4bd7b51b4c3580212fd8dc5e8f050e5f3f1c07f08b177b7934a *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
74757aa64374588adaec7918bce4e86f30a8a3b430869c352f3c51b84c66b182 *.dev/test-sessions.jsonl
```

`python .claude/portable/verify_gates.py <session scratchpad>/verify-gates3 > <session scratchpad>/s4h-verify.txt 2>&1`,exit 0。末段原文:

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
    1946 passed, 7 skipped, 3 xfailed in 360.91s (0:06:00)

=== evidence policy 淨室情境(兩正三負;每個情境各一行)===
    正一 未初始化                  成立 ✓  35 個框架測試檔皆 unknown=True;evidence policy: 未初始化
    正二 已初始化且相符               成立 ✓  rc 1→0;file_coverage=true;red=(無);green=tests/test_evidence_probe.py;evidence policy: 有效;1 passed in 21.18s
    負一 policy / 環境不符         成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 有效;1 passed in 0.41s
    負二 HEAD 有、工作樹不同          成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 工作樹與 HEAD 不同;1 passed in 0.33s
    負三 工作樹有、HEAD 沒有          成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 未提交;1 passed in 0.30s

全部 9 條規則各擋下一次,權威層偵測正常,框架測試在新 repo 全綠,evidence policy 兩正三負成立。
安裝位置:<session scratchpad>\verify-gates3\verify-gates-repo
```

(權威層偵測段與框架測試段之間的說明行未照錄;全文在 `<session scratchpad>/s4h-verify.txt`。)

事後(各自單獨執行):

```
$ wc -c .dev/test-runs.jsonl
834066 .dev/test-runs.jsonl
$ wc -c .dev/test-sessions.jsonl
13647838 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl
5f0ffa923b38a4bd7b51b4c3580212fd8dc5e8f050e5f3f1c07f08b177b7934a *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
74757aa64374588adaec7918bce4e86f30a8a3b430869c352f3c51b84c66b182 *.dev/test-sessions.jsonl
$ git status --porcelain
(無輸出)
```

⇒ 本 repo 兩本帳本前後 bytes 與 sha256 都等於 V0。五情境在同一次淨室執行中全部成立。

### 6. 裁決助手 Linux 預演(來源:Jeff 的 Station 4h 指令;隔離環境;**非本 repo 帳本證據**;非獨立審查 finding)

以 S3H1 的 tests 與 TARGET 的程式套用本修正形狀:H1 由紅轉綠、H2 維持綠;test_redlight / test_status / test_install / test_verify_gates / test_host_evidence_policy 共 279 支全過;verify_gates 兩正三負全部成立、正二 file_coverage=true。

### 7. 殘餘與未證明(目前尚未 machine-enforced)

1. 沿用 4g 證據報告(`docs/audits/2026-10-04-m1a-station4g-fix.md`)第 8 節全部項目,不擴張。
2. 5g 追蹤項:S5g-F1(下一張票優先;status「有效」不含 addopts 鎖步)、S5g-F3(原生 `[tool.pytest]` 永遠 unknown)、S5g-F4(clean filter 讓 (xi) 誤判)、S5g-F5(正二不成立時負情境仍印成立)。
3. 本輪新增(照錄):
   「本輪檢查的語意是 git rev-parse --show-prefix 為空，即 root 必須是 Git 認定的該 repository 最上層。monorepo 中、非 Git 最上層的普通子專案，本輪明確不支援作為 evidence root（H1 鎖住）。巢狀獨立 Git repo / submodule 若自身被 Git 視為最上層，--show-prefix 同樣為空、會被接受；其行為本輪未納入 acceptance，屬未證明範圍，不得宣稱已拒絕或已支援。」
4. 本機只驗 Windows。

### 8. 程序紀錄

- 外來 3 檔以 `git stash push -u -m jeff-mods-recon-20261004-s4h -- <3 檔>` 收起,本輪結束後 `git stash pop` 放回。
- 沒有閘門擋下;沒有改測試、`.dev/pipeline.json`;沒有 push / fetch。
- 本輪與 5g 審查、5g-1、3h 由同一 session 執行(依 Jeff 程序註記,該 session 不得擔任 5h 審查者)。

### 9. POSIX 外部 clean-room 驗收:待執行(裁決助手)
