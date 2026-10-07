# 票 148 第四站實作審計(S4-148-1)—— #1、#3 加 `--no-renames`

- 日期:2026-10-07
- 基準 HEAD:`96fc8b9c75e734bfc7af2a94c245cc96739aeb78`
- 實作 commit(commit 1):`9efca02d1508d828862cb4cb8afe699e4b60601a`
- 站別:`.dev/pipeline.json` 的 `current_stage` 是 `implement`、`ticket_id` 是 `148`。由 Jeff 切換,本輪沒有改。
- 前檢證據(工作樹)與正式結果(committed HEAD)分開記錄。

## 1. 契約(Jeff 裁決原文)

2026-10-07 16:37 美東(節錄;全文見票 148〈Jeff 裁決〉):

> 「裁 A，#5 本輪不改，但記入票 148 待辦。
> #1 與 #3 加 `--no-renames`，保留既有 `--diff-filter=ACM`，讓 rename 目的檔按新增檔進入檢查；刪除處置不變。」

2026-10-07 19:27 美東:

> 「信箱順手遮，只改票 149 的文件引用，不改 Git commit 身分或既有歷史；在 148 第四站准改清單明列這一處。
> VS 未重讀四份來源屬流程偏離，即使你已核對數值正確，也應保留紀錄。
> 切到 `implement` 的安排接受，只改 `current_stage`，保留 ticket 148 與其他欄位。切好後再審第四站指令；不 push。」

名詞:#1 = `.claude/hooks/gate.py` `staged_paths`;#3 = `.claude/portable/scanner.py` `staged_paths`;#5 = `scripts/e2e_authority_layer.py:1046`(不改)。

## 2. code diff(`git diff -- .claude/hooks/gate.py .claude/portable/scanner.py`,原樣)

```diff
diff --git a/.claude/hooks/gate.py b/.claude/hooks/gate.py
index c4d9235..d07a86b 100644
--- a/.claude/hooks/gate.py
+++ b/.claude/hooks/gate.py
@@ -4019,9 +4019,13 @@ def staged_paths(cwd=None, gitlinks=None):
     `gitlinks`:呼叫端傳入的收集串列(形狀同 `check(..., exemptions=[])`),
     跳過的那幾格會 append 進去,由 `mode_pre_commit` 印進報告。
     **回傳型別不變** —— 不改成 tuple,理由見票 13 C(忘了解包會靜默翻成 fail-open)。
+
+    `--no-renames`(票 148,裁 A):不做 rename 配對 —— 否則 git 把改名配成 `R`,
+    而 `R` 不在 `ACM` 裡,改名的目的檔整筆不進逐檔判定(R1/R2/R3/R8 都不評估它)。
+    不配對之後,目的檔以 `A` 進清單、按新增檔檢查;來源是 `D`,照舊不進清單(刪除處置不變)。
     """
     out = subprocess.check_output(
-        ["git", "diff", "--cached", "-z", "--name-only", "--diff-filter=ACM"],
+        ["git", "diff", "--cached", "-z", "--name-only", "--diff-filter=ACM", "--no-renames"],
         cwd=cwd or ROOT).decode("utf-8", "replace")
     paths = [p for p in out.split("\0") if p.strip()]
     if not paths:
diff --git a/.claude/portable/scanner.py b/.claude/portable/scanner.py
index 4910902..8d7cd0d 100644
--- a/.claude/portable/scanner.py
+++ b/.claude/portable/scanner.py
@@ -495,9 +495,13 @@ def staged_paths(cwd=None, gitlinks=None):
     票 13 C 的教訓是簽名一改,忘了解包的呼叫端會靜默拿到錯的東西 ——
     `(False, "…")` 在 `if` 裡是真的,fail-closed 整條翻成 fail-open 而測試全綠。
     走收集串列就沒有那個失敗模式(形狀同 `gate.check(..., exemptions=[])`)。
+
+    `--no-renames`(票 148,裁 A):不做 rename 配對 —— 否則 git 把改名配成 `R`,
+    而 `R` 不在 `ACM` 裡,改名的目的檔整筆不進掃描清單,改名時夾帶的內容不被掃。
+    不配對之後,目的檔以 `A` 進清單、按新增檔掃描;來源是 `D`,照舊不進清單(刪除處置不變)。
     """
     out = subprocess.run(["git", "diff", "--cached", "-z", "--name-only",
-                          "--diff-filter=ACM"], capture_output=True, cwd=cwd)
+                          "--diff-filter=ACM", "--no-renames"], capture_output=True, cwd=cwd)
     if out.returncode != 0:
         raise StagedListingFailed(
             "git diff --cached 失敗(退出碼 %s):%s"
```

- 除了兩處參數與 docstring 補段,沒有其他變動。
- `python -X utf8 -m py_compile .claude/hooks/gate.py .claude/portable/scanner.py`:無輸出。

## 3. 前檢證據(工作樹:基準 HEAD `96fc8b9` + 未提交實作)

- 新 node:`python -X utf8 -m pytest -q -rA -k t148`
  - 結果:`14 passed, 2339 deselected in 17.53s`
  - 14 個 PASSED 名稱與參數 id 和 S3 清單逐字相同:
    - `t148_1[unset/true/copies/false]`、`t148_3`、`t148_4`、`t148_7c`、`t148_7`
    - `t148_5`、`t148_6`
    - `t148_2[unset/true/copies/false]`
  - failed / error / skipped / xfailed 都是 0。
- 全套:`python -X utf8 -m pytest -q -rs`
  - 結果:`2340 passed, 10 skipped, 3 xfailed in 260.64s (0:04:20)`,0 failed。
  - 2340 = 2332 + 8,也就是 S3 的 8 個紅 node 轉綠。
  - skipped 10 行與 S3 相同:`test_gate.py:451/459/473`、`test_redlight.py:2673/3074/3505/3702×3/3752`。

## 4. 淨室

- 指令:`python -X utf8 .claude/portable/verify_gates.py <scratchpad>/vg-148`
- rc 0(Bash 工具沒有回報非 0)。
- 摘錄(raw;絕對路徑遮罩):

```
=== 規則清單(從 gate.py 的定義列舉,不是對照表)===
    R1 R2 R3 R4 R5 R6 R7 R8 R9 R10

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
    R10  擋下 ✓
         正控放行 ✓(同一佈置、家目錄未放情境物)
         [R10/fail-closed] unmanaged_entry：未受管入口：synced（額外 2 / 缺少 0 / 內容不符 0）

=== 權威層偵測(只驗未安裝路徑)===
    hook 刪掉        -> 偵測到沒裝 ✓(找不到 pre-commit(查過 .git/hooks/pre-commit))
    別人的 hook 佔位 -> 偵測到沒裝 ✓(.git/hooks/pre-commit 存在,但它不呼叫 gate.py —— 那是別人的 hook 佔著位子,不是本框架的權威層。)
    裝回去           -> 偵測到已裝 ✓

=== 框架自己的測試,在這個新 repo 裡跑一次 ===
    2190 passed, 14 skipped, 3 xfailed in 247.92s (0:04:07)

=== evidence policy 淨室情境(兩正三負;每個情境各一行)===
    正一 未初始化                  成立 ✓  35 個框架測試檔皆 unknown=True;evidence policy: 未初始化
    正二 已初始化且相符               成立 ✓  rc 1→0;file_coverage=true;red=(無);green=tests/test_evidence_probe.py;evidence policy: 有效;1 passed in 11.29s
    負一 policy / 環境不符         成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 有效;1 passed in 0.21s
    負二 HEAD 有、工作樹不同          成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 工作樹與 HEAD 不同;1 passed in 0.16s
    負三 工作樹有、HEAD 沒有          成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 未提交;1 passed in 0.15s

全部 10 條規則各擋下一次,權威層偵測正常,框架測試在新 repo 全綠,evidence policy 兩正三負成立。
```

- 安裝段同時印出「來源的 .gitignore 蓋住了這些框架檔,已強制帶過去」清單,其中列了 `.dev/reports/*.md`、`.dev/test-runs.jsonl` 等。
  - 這是 146 審查 N-8 已記錄的訊息字面問題(`generate` 項目實際上不是被複製)。本輪沒有處理,只記錄。

## 5. commit 1

**L1 判定**

- `git status --porcelain`(add 前):

  ```
   M .claude/hooks/gate.py
   M .claude/portable/scanner.py
   M .dev/gate-exemptions.jsonl
   M docs/tickets/framework-updates/148-staged-list-misses-renames.md
  ```

- 豁免帳本有變動(Edit gate.py 時前哨記帳 1 筆),所以 L1 = 上列 4 檔。

**乾跑與提交**

- 逐檔 add 後,`git diff --cached --name-only` = L1。
- 乾跑 `python -X utf8 .claude/hooks/gate.py --pre-commit`:exit 0,輸出全文:

  ```
  [R2/自我修改豁免] .claude/hooks/gate.py:閘門自身,不受站別限制 —— 已記錄。
       理由:閘門把站別卡住時,修法需要改本檔;R2 管到它就把人鎖在外面(docs/adr/0004)。
       R3 沒有例外:寫測試不需要先解鎖任何東西。
  ```

- 乾跑使豁免帳本追加 1 筆(`MM .dev/gate-exemptions.jsonl`),再 add 一次;staged 仍 = L1。
- `git diff --cached --check`:無輸出。
- commit 輸出:

  ```
  [R2/自我修改豁免] .claude/hooks/gate.py:閘門自身,不受站別限制 —— 已記錄。
       理由:閘門把站別卡住時,修法需要改本檔;R2 管到它就把人鎖在外面(docs/adr/0004)。
       R3 沒有例外:寫測試不需要先解鎖任何東西。
  [master 9efca02] fix(148): S4-148-1 —— staged_paths（gate、scanner）加 --no-renames，rename 目的檔進入逐檔檢查與 leak scan
   4 files changed, 59 insertions(+), 3 deletions(-)
  ```

- commit 後 `git status --porcelain` ⇒ ` M .dev/gate-exemptions.jsonl`。這是 commit 1 自己的 hook 追加,留給 commit 2。
- R10 沒有擋(pre-commit 沒有 `[R10` 輸出)。

## 6. 正式結果(committed HEAD `9efca02`)

- `python -X utf8 -m pytest -q -rs` ⇒ `2340 passed, 10 skipped, 3 xfailed in 259.14s (0:04:19)`。
  - 數字與前檢相同。
  - skipped 10 行逐字相同。

## 7. 帳本前綴(只追加)

| 檔 | LC(步驟 0,bytes) | `head -c LC` 的 sha256 | 步驟 0 整檔 sha256 | 現長(bytes) | 現整檔 sha256 |
|---|---|---|---|---|---|
| `.dev/test-runs.jsonl` | 1186991 | `6f10bda5995fa68795195a5999fa1000fb52b2f5c3424c39b42ad25a060bd1da` | `6f10bda5…` | 1210891 | `6a0a01a45df181e56c5752f52159c0e339b536a68457d5d2c3cfa8a55879b962` |
| `.dev/test-sessions.jsonl` | 35241650 | `20ce69ff16b80f5a52fb7565dcca5052dcadfaea4c1ad2d546a10152ba8a6fa9` | `20ce69ff…` | 37662732 | `0d38e3d86ddb1c2773ff4c69839476b87857c43211d82617a2a562878c05b71f` |

- 追加量:runs +23900 bytes,sessions +2421082 bytes。
- 來源是本 repo 三次 pytest:新 node、工作樹全套、HEAD 全套。淨室的 pytest 寫在隔離 repo 的帳本(推論:依 `verify_gates` 的隔離設計)。

## 8. 豁免帳本新增行(原樣;不含使用者路徑)

隨 commit 1 進版(296 → 298 行):

```
{"ts": "2026-10-07T23:31:25.908935+00:00", "file": ".claude/hooks/gate.py", "module": "gate", "ticket": "148", "stage": "implement", "declared_in": "0004", "reason": "gate-self-modification", "tool": "Edit", "outcome": "granted", "blocked_by": null, "at_commit": false, "content_hash": "d167456ab50ce976c2a40d9a1a4c8633b8f93215a1529fd6a57741e558b08d36", "result_hash": "6fe33699193b246ec90e1e9c8f3ccd04449c0e121f6b1589fdc593a9e17057b6", "changes_bytes": true}
{"ts": "2026-10-07T23:42:09.409612+00:00", "file": ".claude/hooks/gate.py", "module": "gate", "ticket": "148", "stage": "implement", "declared_in": "0004", "reason": "gate-self-modification", "tool": "pre-commit", "outcome": "granted", "blocked_by": null, "at_commit": true, "content_hash": "6fe33699193b246ec90e1e9c8f3ccd04449c0e121f6b1589fdc593a9e17057b6", "result_hash": null, "changes_bytes": null}
```

隨 commit 2 進版(commit 1 的 hook 追加,298 → 299):

```
{"ts": "2026-10-07T23:42:19.693016+00:00", "file": ".claude/hooks/gate.py", "module": "gate", "ticket": "148", "stage": "implement", "declared_in": "0004", "reason": "gate-self-modification", "tool": "pre-commit", "outcome": "granted", "blocked_by": null, "at_commit": true, "content_hash": "6fe33699193b246ec90e1e9c8f3ccd04449c0e121f6b1589fdc593a9e17057b6", "result_hash": null, "changes_bytes": null}
```

## 9. 偏離與詮釋

1. **票 149 信箱遮罩**(准改清單第 4 項 (a))。
   - 兩段 `git show --stat` 引用的 `Author:` 行,作者信箱改為 `<id>`,結果是 `Author: wusuowei-tw <<id>>`。只替換信箱字串,外層原有的角括號保留,所以呈現為 `<<id>>`。本審計不重寫原信箱。
   - 修改後 Grep 檢查票 149:`noreply` 0 處。
   - Git commit 身分與既有歷史沒有改動。
2. **票 149〈流程紀錄〉**:照准改清單第 4 項 (b) 逐字加入一行。
3. **commit 訊息**:第一段逐字照指令,第二段 `-m` 是署名行。
4. **淨室安裝訊息**的 N-8 字面問題:只記錄,不處理(不在准改範圍)。

## 10. 未驗

- POSIX 未跑。
- CI 未跑(未 push)。
- #5(`scripts/e2e_authority_layer.py:1046`)未改,仍是 `--diff-filter=ACM` 且沒有 `--no-renames`(Jeff 裁決;票 148〈待辦〉)。
- R0 §3 的剩餘 UNKNOWN 缺口(`-C` / copies / `--raw`、字串拼接、二進位與編碼)本輪沒有處理。
