# 票 145 Station 4j —— S5i-F1 最小修正(_root_is_toplevel 恢復完整 stdout contract)與本機驗收

- 日期:2026-10-05
- 對象:S4J1 `d4b6fafd4afdd70121278527194aeef4097bff33`(只改 `.claude/hooks/redlight.py` 的 `_root_is_toplevel()`)。
- 上一個 commit:S3J1B-2 `dccc4bfc9b390aad9687384fba9db374b7da67af`;紅燈 S3J1 `9990fd654275a0af25fa51ce374dea3e812ef54e`(J1 / J2)、S3J1B `35d100a3841486e2d75ba39aea71bda601e18075`(J1b)。
- 合約:票 145〈六十一〉61.3 裁決 3;Jeff 裁決:第一次 4j = BLOCKED BY R3(閘門照設計;不視為 FAIL、不繞過);Station 3j-1b = APPROVED;4j 只改 `_root_is_toplevel()`,恢復完整 stdout contract;J1 / J1b / J2 / I1–I3 / H1 / H2 不准修改。
- 範圍:**本機(Windows)驗收**。POSIX 外部 clean-room 驗收尚未執行(第 9 節)。本報告只宣稱:本機驗收通過;待 POSIX 外部驗收。

## 【給裁決者】

1. 第一次 4j 改程式時被 R3 擋下(本機沒有紅燈紀錄);依你的裁決先補 3j-1b 的 J1b(Windows 可紅),這次重送才動手。
2. 修正:判「root 是不是工作樹最上層」改成 Git 的輸出必須**整段**剛好是 `true` 加兩個換行,多一個位元組都不算;舊寫法只看前兩行,會被名稱以換行開頭的子目錄騙過。
3. 本機全套 2104 passed、0 failed;J1b 由紅轉綠;J1 在 Windows 照設計跳過(要靠 POSIX 驗收證明)。
4. 淨室兩正三負全部成立,正二仍可退紅;本 repo 測試帳本只往後加,淨室前後完全沒動。
5. 下一步是 POSIX 外部淨室驗收(裁決助手執行,須含 J1 由紅轉綠)。

## 【給裁決助手】

### 0. 第一次 4j:R3 攔截原文與裁決

第一次 4j 的 S4J1 對 `.claude/hooks/redlight.py` 的 Edit 被前哨擋下(原文照錄;亦見 `docs/audits/2026-10-05-m1a-station3j-redlight.md` 第 6.1 節與 `.dev/reports/2026-10-05T184454Z-ticket145-station4j-blocked-r3.md`):

```
PreToolUse:Edit hook error: [python "$CLAUDE_PROJECT_DIR/.claude/hooks/gate.py"]: [六站閘門/前哨] [R3/紅燈][enforce] .claude/hooks/redlight.py:測試檔存在,但沒有合格的紅燈紀錄。
     tests/test_redlight.py 有執行紀錄,但沒有任何一筆是「紅燈,且發生在這次改動之前」。
     合格的形狀:實作當時不存在,或紅燈是對著這支檔案在 HEAD 的
     內容跑出來的。先寫實作再補跑紅燈不算 —— 那是補測試,不是紅綠燈。
     先跑測試確認它在實作不存在時是紅的,再回來寫功能碼。
(權威判定在 pre-commit,繞過前哨仍會在 commit 被擋)
```

- 成因:本機帳本對 S4I1 版 `redlight.py` 沒有任何 `tests/test_redlight.py` 紅燈 —— J1 在 Windows 被跳過、J2 本來就綠,J1 的紅只在裁決助手的 Linux 證據裡。
- 裁決(Jeff):第一次 4j = BLOCKED BY R3(閘門照設計;不視為 FAIL、不繞過);選 A,補 Windows 可紅的解析層紅燈(3j-1b,J1b);Station 3j-1b = APPROVED。
- 本次重送:S3J1B 上的 J1b 紅燈(`tests red under ticket 145: tests/test_redlight.py`)即 R3 所需本機紅燈;S4J1 的 Edit 一次通過,沒有被擋。

### 1. 修正內容(行號以 S4J1 為準)

| 位置 | 內容 |
|---|---|
| `.claude/hooks/redlight.py:729-731` docstring | 原句「任一查詢失敗或條件不符 ⇒ False。」後補兩行:stdout 須完整等於 `b"true\n\n"`(`\r\n` 正規化後)及 S5i-F1 說明 |
| `:741` | `return proc.stdout.replace(b"\r\n", b"\n") == b"true\n\n"`(取代 `split(b"\n")` + `len(lines) < 2` + 前兩行 strip 比對) |

- 未改:subprocess 呼叫(`--is-inside-work-tree --show-prefix` 一次呼叫)、例外 ⇒ False、returncode ≠ 0 ⇒ False;`committed_blobs` / `evidence_policy_facts` 的呼叫處、consumer、`policy_state`、`tests/conftest.py`、status.py / install.py / verify_gates.py、任何測試。
- `content_hash` 及其呼叫鏈未動。
- 一次 Edit;寫入後以 `python .claude/portable/status.py --root .` 探針,輸出沒有「redlight.py 無 run 事實讀取」。
- diff 有兩個 hunk(docstring 與函式本體),**兩個都在 `_root_is_toplevel()` 之內**;指令寫「預期只有一個 hunk」,差異來自 docstring 補述與本體相隔 7 行以上,git 預設 3 行 context 切成兩段。

`git show d4b6fafd4afdd70121278527194aeef4097bff33` 的 diff 全文(照錄時,diff 中空白 context 行原為單一空格,此處去除以通過 `git diff --cached --check`):

```
diff --git a/.claude/hooks/redlight.py b/.claude/hooks/redlight.py
index 996f151..d4d208a 100644
--- a/.claude/hooks/redlight.py
+++ b/.claude/hooks/redlight.py
@@ -726,7 +726,9 @@ def _git_bytes(root, args):
 def _root_is_toplevel(root):
     """root 是否就是 git 工作樹的最上層:須同時 `--is-inside-work-tree` 為 true 且 `--show-prefix` 為空
     (票 145 Station 4i,S5h-F1:gitdir / bare repository 內 `--show-prefix` 同樣為空,但不是工作樹)。
-    任一查詢失敗或條件不符 ⇒ False。"""
+    任一查詢失敗或條件不符 ⇒ False。
+    stdout 須完整等於 b"true\n\n"(\r\n 正規化後):--show-prefix 輸出未跳脫的原始路徑位元組,
+    拆行只看前兩行會把 LF 開頭的子目錄名誤判為空 prefix(票 145 Station 4j,S5i-F1)。"""
     import subprocess
     try:
         proc = subprocess.run(["git", "-C", os.fspath(root), "rev-parse",
@@ -736,10 +738,7 @@ def _root_is_toplevel(root):
         return False
     if proc.returncode != 0:
         return False
-    lines = proc.stdout.split(b"\n")
-    if len(lines) < 2:
-        return False
-    return lines[0].strip() == b"true" and lines[1].strip() == b""
+    return proc.stdout.replace(b"\r\n", b"\n") == b"true\n\n"


 def committed_blobs(root, paths=BLOB_FILES):
```

提交前檢查摘要:`py_compile` 無輸出;`git diff --cached --name-only` 只有 `.claude/hooks/redlight.py`;`--stat` 為 `9 ++++-----`(4 insertions(+), 5 deletions(-));`git diff --cached --check` 無輸出;commit 後 `git rev-parse HEAD` = `d4b6fafd4afdd70121278527194aeef4097bff33`,`git status --porcelain` 無輸出。

### 2. 3a 固定全套(S4J1 上只跑一次;Windows)

`python -X utf8 -m pytest -q > <session scratchpad>/s4j-run.txt 2>&1`,exit 0;之後 `git status --porcelain` 無輸出。

輸出檔第 32–35、39 行:

```
SKIPPED [1] tests\test_gate.py:451: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:459: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:473: 此環境無法建立 symlink
SKIPPED [1] tests\test_redlight.py:2673: Windows 檔名不得含 LF;本案例由 POSIX 驗收證明(〈六十一〉61.3 裁決 2)
2104 passed, 4 skipped, 3 xfailed in 251.83s (0:04:11)
```

- collected 2111(2104 + 4 + 3)。0 failed;輸出沒有任何 `FAILED` / `ERROR` 行。
- **J1 於 Windows 為 skipped**(第 35 行;照 3j 設計),J1 的紅→綠須由 POSIX 驗收證明。
- **J1b 由紅轉綠**:S3J1B 上為唯一 FAILED(`tests\test_redlight.py:2749: AssertionError`,`assert True is False`),S4J1 上在 passed 之內。
- J2 四案、I1–I3、H1–H2 維持綠。

### 3. 3b 帳本(以 B21 為前段基準;各自單獨執行)

```
$ head -c 880409 .dev/test-runs.jsonl > <session scratchpad>/r22.bin
$ head -c 16609700 .dev/test-sessions.jsonl > <session scratchpad>/s22.bin
$ sha256sum <session scratchpad>/r22.bin
670237025036aeef8fd427aaccb6c9d2fae9ed624d1f38b2f8b23d2c16fc6ee5 *<session scratchpad>/r22.bin
$ sha256sum <session scratchpad>/s22.bin
2badaee4cc130d1ec9fed57ffbac1c093ccee20c9c5547189caf576d5cbcad0b *<session scratchpad>/s22.bin
$ wc -l .dev/test-runs.jsonl
3344 .dev/test-runs.jsonl
$ wc -l .dev/test-sessions.jsonl
34 .dev/test-sessions.jsonl
```

- 前段 sha256 = B21 ⇒ 只追加。test-runs 3297 → 3344 行(+47)、test-sessions 33 → 34 行(+1)。

### 4. 3c status(節錄原文)

```
test-runs: 本票 red 0 / green 47 / run 事實未知 0 / orphaned 0 / schema 不合格 run 0;最後一筆 tests/test_verify_gates.py=green @ 2026-10-05T20:03:52.351078+00:00;最近一次 run:A(exit 0;collected 2111 / deselected 0 / passed 2104 / failed 0 / skipped 4)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl)
evidence policy: 有效  (source: .agents/evidence-policy.json)
tests red under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests green (run 事實未知) under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests orphaned under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
```

- 原紅檔 `tests/test_redlight.py` 列在 `tests green under ticket 145`。
- 上方原文取自 3d 之後重跑的 status(`<session scratchpad>/s4j-status2.txt` 第 23、24、38、40、41 行);3d 前後兩本帳本皆等於 V0(第 5 節),status 讀的資料相同。

### 5. 3d 淨室

V0(各自單獨執行):

```
$ wc -c .dev/test-runs.jsonl
891928 .dev/test-runs.jsonl
$ wc -c .dev/test-sessions.jsonl
17351316 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl
22148446c9cc8d11520cd6437f5a49c852b9b02cc17c47d2a4b53d8be8991fe4 *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
3d7cde594d889bc71804c2af421b4c7d61078691c8644052bb68bbe7e03865f1 *.dev/test-sessions.jsonl
```

`python .claude/portable/verify_gates.py <session scratchpad>/verify-gates5 > <session scratchpad>/s4j-verify.txt 2>&1`,exit 0。輸出檔第 185–199 行與末段原文:

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
    1954 passed, 8 skipped, 3 xfailed in 243.04s (0:04:03)

=== evidence policy 淨室情境(兩正三負;每個情境各一行)===
    正一 未初始化                  成立 ✓  35 個框架測試檔皆 unknown=True;evidence policy: 未初始化
    正二 已初始化且相符               成立 ✓  rc 1→0;file_coverage=true;red=(無);green=tests/test_evidence_probe.py;evidence policy: 有效;1 passed in 9.23s
    負一 policy / 環境不符         成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 有效;1 passed in 0.26s
    負二 HEAD 有、工作樹不同          成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 工作樹與 HEAD 不同;1 passed in 0.21s
    負三 工作樹有、HEAD 沒有          成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 未提交;1 passed in 0.18s

全部 9 條規則各擋下一次,權威層偵測正常,框架測試在新 repo 全綠,evidence policy 兩正三負成立。
安裝位置:<session scratchpad>\verify-gates5\verify-gates-repo
```

(權威層偵測段與框架測試段之間的說明行未照錄;全文在 `<session scratchpad>/s4j-verify.txt`。淨室框架測試 8 skipped 較 4i 的 7 多 1,即 J1 在 Windows 淨室同樣被跳過。)

事後(各自單獨執行;程序偏差見第 8 節):

```
$ wc -c .dev/test-runs.jsonl
891928 .dev/test-runs.jsonl
$ wc -c .dev/test-sessions.jsonl
17351316 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl
22148446c9cc8d11520cd6437f5a49c852b9b02cc17c47d2a4b53d8be8991fe4 *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
3d7cde594d889bc71804c2af421b4c7d61078691c8644052bb68bbe7e03865f1 *.dev/test-sessions.jsonl
$ git status --porcelain
(無輸出)
```

⇒ 本 repo 兩本帳本前後 bytes 與 sha256 都等於 V0。五情境在同一次淨室執行中全部成立,正二 `file_coverage=true`。

### 6. 裁決助手 Linux 證據(來源:Jeff 的 Station 4j 重送指令,照錄;隔離環境;git 2.43.0;Python 3.11 + pytest 9.1.1;**非本 repo 帳本證據**;非獨立審查 finding)

「以 S3J1B 的 tests/test_redlight.py 原檔 + S4I1 的 redlight.py：J1 與 J1b failed、J2 四案 passed。套用下方修正形狀後：J1 / J1b / J2 / H1 / H2 / I1–I3 全 passed，evidence 相關 5 檔 288 支全過。」

(這是修法原型的預演,不是對 S4J1 原檔的 POSIX 驗收;後者見第 9 節。)

### 7. 殘餘與未證明(目前尚未 machine-enforced)

1. 沿用 4i 證據報告(`docs/audits/2026-10-05-m1a-station4i-fix.md`)第 7 節全部項目(含其沿用的 4h 第 7 節與 4g 第 8 節),不擴張;唯 4i 第 7 節第 3 點的殘餘措辭由本節第 4 點取代。
2. 5g 追蹤項:S5g-F1(下一張票優先)、S5g-F3、S5g-F4、S5g-F5;5h 追蹤項:S5h-F4(併入 S5g-F1 類的 operator / status 追蹤項)。S5h-F3 已於 4i 補準措辭(本輪再由第 4 點取代)。
3. S5i-F3 已由機器鎖處理:J2(直接呼叫 `_root_is_toplevel` 的四種佈置)與 J1b(解析層替身,鎖住「多餘位元組 ⇒ False」),不另列追蹤項。新增流程教訓追蹤項「R3 與 POSIX-only 紅燈」(R3 只認本機帳本紅燈;規劃平台限定紅燈時須同時規劃本機可紅的對應案例;見票 145「相關」)。
4. 依 S5i-F2 補準的殘餘措辭(照錄,取代 4i 版本中的對應段落):
   「本輪檢查的語意是 git rev-parse --is-inside-work-tree --show-prefix 的 stdout（\r\n 正規化後）完整等於 b"true\n\n"，即 Git 對該 root 回報「在工作樹內」且 prefix 為空且沒有任何其他位元組。在預設環境（未設 GIT_DIR / GIT_WORK_TREE / core.worktree）下明確不支援（⇒ unknown）：monorepo 中非最上層的普通子目錄（H1；含 POSIX 上名稱以 LF 開頭者，J1 / J1b）、位於 gitdir 或 bare repository 內的 root（I1 / I2）。會被接受但本輪未納入 acceptance、屬未證明：巢狀獨立 Git repo、submodule、linked worktree、.git 為檔案且 gitdir 指向他處，以及 GIT_DIR / GIT_WORK_TREE / core.worktree 等重新對應佈局（含 Git 因此把 gitdir 本身視為工作樹的情形）。上述佈局若 Git 對該 root 實際回報上述 stdout，即會被本檢查接受；其 HEAD 與工作樹是否符合既定 identity invariant，本輪未完整 acceptance，不得宣稱已拒絕或已支援。」
5. 本機只驗 Windows;J1(LF 開頭子目錄的端到端)在 Windows 不可建立,未在本機執行。

### 8. 程序紀錄

- 外來 3 檔以 `git stash push -u -m jeff-mods-recon-20261004-s4j -- <3 檔>` 收起,本輪結束後 `git stash pop` 放回。
- 本輪重送沒有閘門擋下(第一次 4j 的 R3 攔截見第 0 節);沒有改測試、`.dev/pipeline.json`;沒有 push / fetch。
- **程序偏差**:3d 事後的 5 條唯讀檢查(`wc -c` ×2、`sha256sum` ×2、`git status --porcelain`)在同一則訊息中並行送出,違反「Bash 逐條單獨送出、不並行」;皆為唯讀指令,輸出各自獨立取得(第 5 節)。未重跑。
- 本 session 自 3h 起為實作 session;5j 審查須開第五個全新對話,4g 實作 session、本 session、5g / 5h / 5i 審查 session 皆不得擔任。

### 9. POSIX 外部 clean-room 驗收:待執行(裁決助手)
