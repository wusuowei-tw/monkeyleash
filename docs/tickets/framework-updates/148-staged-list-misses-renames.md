# 票 148 —— staged 清單在 rename 時漏列(權威層／leak scan 側)

**狀態**:~~**立案(未排程)。**~~ ~~**第三站紅燈已寫（S3-148-1，工作樹證紅）；待第四站實作（裁 A）。**~~ ~~**第四站實作中（S4-148-1；前檢證據通過）；待正式結果。**~~ ~~**第四站已實作並正式驗證（S4-148-1 9efca02d1508d828862cb4cb8afe699e4b60601a）；待第五站獨立審查。**~~ **第五站審查包已提交（S5-148-0）；待全新視窗獨立審查。**
**優先度**:**未定。**(審查建議見下;排程由 Jeff 另裁。)
**發現於**:2026-10-07,票 146 第五站獨立審查 (k) O-1。
**來源**:`docs/audits/2026-10-07-146-station5-independent-review.md`(§4 (k) O-1、(d))。
**交叉引用**:票 140 A-1(`docs/tickets/framework-updates/140-sixth-station-2026-09-13-inventory.md` :38–51)。本票是該格「仍待確認：未實測 rename 是否真能繞過」的實測補件。

---

## 命題

staged 清單遇到 rename 時會漏列。漏法有兩種，不能統稱「只漏來源」:

### 1. 「來源被隱藏」—— 已由票 146 N-1 修正，不屬本票

- 位置:`gate.py` `_staged_names_all`。這個呼叫點沒有 diff-filter,原本也沒有 `--no-renames`。
- 審查 `probe_rename.py` case A(`git mv docs/draft-allowlist.json .agents/extension-allowlist.json`):只列出目的，沒有列出來源的刪除。【實測】
- 票 146 N-1 已加上 `--no-renames` 修正(`98099bae297b68e5c6cd4787ea8474d3f400ccc0`)。**這一項不屬本票**,列出只是為了和第 2 項區分。

### 2. 「rename 整筆被排除」—— 本票對象

- 位置:權威層與 leak scan 的 staged 清單使用 `--diff-filter=ACM`。審查當時的行號是 `gate.py:4024`、`scanner.py:499-500`;`leak_scan.py:321` 經由 `scanner.staged_paths` 取得清單。
- 機制:git 預設會做 rename 配對，配成的狀態是 `R`,而 `R` 不在 `ACM` 之內。
- 審查 `probe_rename.py` case B(`git mv src/a.py src/b.py`)原文:

  ```
    staged_paths 同款(--diff-filter=ACM): []
    加 --no-renames:                       ['src/b.py']
  ```

  ⇒ 來源與目的**都不在**清單裡。【實測】

### 3. 後果

- 改名的檔不會進入 R1 / R2 / R3 / R8 的逐檔判定(依審查原文，讀碼推論)。【推論】
- 改名的檔也不會進入 leak scan 的掃描清單;leak scan 對空清單回 0(`leak_scan.py:344`)。
- 「改名時夾帶秘密不會被掃」是從「清單為空」推出來的;審查沒有實際放入秘密去跑。【推論】

## 環境註記

- 審查實測環境:git 2.53.0.windows.2;repo 沒有 `diff.renames` 設定(`git config --get-all diff.renames` exit 1)。
- 行號是審查當時的版本，立票時沒有重新核對。

## 審查建議(非 Jeff 裁決)

審查者認為本票的嚴重度高於票 146 所有後補項，建議優先處理。**排程由 Jeff 另裁。**

## 範圍

- 立案本身不含任何修法。
- 下一步：唯讀盤點所有使用 `--diff-filter` 或會做 rename 配對的 staged 清單呼叫點。
- 本票只引用審查檔與票 140 既有的文字，沒有新增未經實測的主張。

---

## R0 盤點結果

出處:R0 唯讀盤點報告 `.dev/reports/2026-10-07T203056Z-ticket148-r0-inventory.md`(ignored,不進版控)。
基準是 HEAD `6d80427b0bfd79d4c0477a8b93b2f8f65c44de09`。以下原樣引用該報告 §4 主表、§5 覆蓋表與 §7 選項名稱。

### §4 production 呼叫點(主表原樣)

| # | 檔案:行號 | 函式名 | git 指令參數原文(逐字) | `--diff-filter` | `--no-renames` | 清單的消費者(讀碼) | rename 時 | 證據等級 |
|---|---|---|---|---|---|---|---|---|
| 1 | `.claude/hooks/gate.py:4023-4025` | `staged_paths` | `["git", "diff", "--cached", "-z", "--name-only", "--diff-filter=ACM"]` | `ACM` | 無 | `mode_pre_commit`(`:4158`)⇒ `for f in staged: check(f, None, at_commit=True, exemptions=used)`(`:4178-4186`)逐檔判定,結果進 `violations`。check 內含哪些規則,本輪沒有逐條讀碼;依審查原文是 R1/R2/R3/R8 | **(B)** | 【推論(讀碼,本輪 HEAD)】。gate.py 自 eb3a3db 後有變動(`98099ba`),所以不引用審查實測。⚠ 指令字串與 #3 逐字同款 |
| 2a | `.claude/hooks/gate.py:4061`(修正前) | `_staged_names_all` | (修正前)`git diff --cached -z --name-only`(審查 :136 引文) | 無 | 無 | `check_extension_integrity` ⇒ `extension_policy_only_commit`(R10 policy-only 通道,H-6) | **(A)** | 【實測(第五站審查 probe_rename.py case A;審查當時版本與設定:git 2.53.0.windows.2、無 diff.renames)】。**只適用修正前版本** |
| 2b | `.claude/hooks/gate.py:4061`(現況) | `_staged_names_all` | `["git", "diff", "--cached", "--name-only", "-z", "--no-renames"]` | 無 | **有** | 同上:`mode_pre_commit` `:4166` ⇒ `check_extension_integrity(staged_all)`(`:4170`);另有 `staged_names is None` 時的 fallback(`:4080`) | **(C)** | 【實測(S4c:T146-80/T146-80b 於 98099bae297b68e5c6cd4787ea8474d3f400ccc0 綠)】。本輪只讀碼確認旗標仍在(`:4061`),未重測 |
| 3 | `.claude/portable/scanner.py:499-500` | `staged_paths` | `["git", "diff", "--cached", "-z", "--name-only", "--diff-filter=ACM"]` | `ACM` | 無 | `leak_scan.main` `--staged`(`leak_scan.py:321`)⇒ `scan(paths, review=review, staged=True) if paths else 0`(`:344`)。空清單回 0 | **(B)** | 【實測(審查 case B;審查當時版本與設定)】。scanner.py、leak_scan.py 自 eb3a3db 後都未變動(兩個 git log 皆無輸出),但本輪未重測。另附本輪讀碼:【推論(讀碼,本輪 HEAD)】`ACM` 不含 `R`,沒有 `--no-renames`,所以 rename 會整筆不在清單 ⇒ (B) |
| 4 | `.claude/portable/verify_gates.py:717` | `run_scenario` | `["git", "diff", "--cached", "--name-only"]` | 無 | 無 | 只判 `staged.strip()` 是否為空(N-4:排除 nothing-to-commit 假象),不逐檔使用 | **(D)** | 【推論(讀碼,本輪 HEAD)】。rename 時目的路徑仍會輸出,清單非空 ⇒ 判定不受影響 |
| 5 | `scripts/e2e_authority_layer.py:1046-1047` | 案例執行函式(`:1030` 起;本輪沒有往上讀到 `def` 行,**函式名 UNKNOWN**) | `["-C", clone, "diff", "--cached", "-z", "--name-only", "--diff-filter=ACM"]` | `ACM` | 無 | `res["evidence"]["staged"]`、`case["premise"](clone, staged)`(`:1058`)、靜態案例 `"pkg/__init__.py" in staged`(`:1063`)。這是 e2e 演練的證據收集,**不是權威層判定** | **(B)** | 【推論(讀碼,本輪 HEAD)】。該檔自 eb3a3db 未變動,但沒有任何歷史實測可引用 |
| 6 | `scripts/e2e_authority_layer.py:1127-1128` | 同上 | `["-C", clone, "diff", "--cached", "--name-only"]` | 無 | 無 | 只判 `bool(...strip())`(「暫存內容仍在 index」) | **(D)** | 【推論(讀碼,本輪 HEAD)】 |

### §5 覆蓋表(原樣)

| 呼叫點 | rename 測試 |
|---|---|
| #1 `gate.staged_paths` | **無測試** |
| #2b `gate._staged_names_all` | T146-80、T146-80b |
| #3 `scanner.staged_paths`(及 `leak_scan --staged`) | **無測試** |
| #4 `verify_gates.py:717` | **無測試**(rename 不影響其判定,推論) |
| #5 `e2e_authority_layer.py:1046` | **無測試** |
| #6 `e2e_authority_layer.py:1128` | **無測試**(同 #4) |

### §7 修法選項(名稱)

- **A** —— 兩個 ACM 呼叫點加 `--no-renames`,保留 `--diff-filter=ACM`
- **B** —— `--diff-filter` 加入 `R`(`ACMR`),取 R 的目的路徑
- **C** —— 集中成單一取清單函式
- **D** —— 改成黑名單 filter:`--no-renames --diff-filter=d`(小寫:只排除 D,其餘全收)

## Jeff 裁決(2026-10-07)

16:37 美東,逐字:

> 「裁 A，#5 本輪不改，但記入票 148 待辦。
> #1 與 #3 加 `--no-renames`，保留既有 `--diff-filter=ACM`，讓 rename 目的檔按新增檔進入檢查；刪除處置不變。
> 第三站紅燈須鎖住：
> * 未設定／true／false／copies 四種 `diff.renames` 下，目的檔都被列入；false 可列基線正控。
> * leak scan：新檔秘密被擋的正控，以及「rename＋少量修改＋秘密」仍被擋的負控；先確認佈置確實形成 rename。
> * 權威層另做實際規則驗證，不能只驗清單；目前其繞過仍是推論。
> * 純刪除維持既有處置。
> 沙盒結果記為外部 Linux 實測，不升格成本 repo 的 Windows 帳本證據。「秘密完全不被察覺」也限縮為「該佈置下 leak scan 回 rc 0」，避免泛化。」

名詞:#1 = `.claude/hooks/gate.py` `staged_paths`;#3 = `.claude/portable/scanner.py` `staged_paths`;#5 = `scripts/e2e_authority_layer.py:1046`。

16:50 美東,逐字(第三站步驟 3-2 的指令改寫):

> 「裁 A。允許將 `-k "T148 or t148"` 改為 `-k t148`，沿用原 C0 與停止條件，不改測試內容。
> 選取驗證須核對 14 個 node 的完整名稱與參數案都符合預定清單，不能只看 passed＋failed＝14；ERROR／skip／xfail 均應為 0。
> R7 的擋下訊息記為實測，`split()` 是否為觸發原因維持讀碼推論。另把「還沒存檔」改為「已寫入工作樹、尚未 commit」。
> 其餘接續安排接受，不 push。」

## 外部證據(裁決者 Linux 沙盒;不屬本 repo Windows 帳本)

以下是裁決者在外部 Linux 沙盒的實測。**不升格成本 repo 的 Windows 帳本證據。**

- **環境**:
  - git 2.43.0、Linux。
  - 程式碼為 `6bc98085e4c018e896cf252b945f51bfaa8ed7fb` 的樹(scanner.py、leak_scan.py 與 6d80427 相同)。
- **leak scan**:
  - 合成秘密放新檔 ⇒ rc 1(命中私鑰標頭樣式)。
  - 既有檔 `git mv` + 檔尾加合成秘密(name-status `R092`)⇒ rc 0。
  - 結論限縮為「該佈置下 leak scan 回 rc 0」。
- **清單參數**:`git diff --cached -z --name-only` 搭配下列參數,分別在 `diff.renames` 未設定 / true / false / copies 四種設定下測:

  | 加上的參數 | 未設定 | true | false | copies |
  |---|---|---|---|---|
  | `--diff-filter=ACM --no-renames` | 列出目的 | 列出目的 | 列出目的 | 列出目的 |
  | `--diff-filter=ACMR` | 列出目的 | 列出目的 | 列出目的 | 列出目的 |
  | `--diff-filter=d --no-renames` | 列出目的 | 列出目的 | 列出目的 | 列出目的 |
  | 只有 `--diff-filter=ACM` | 空 | 空 | 列出目的 | 空 |

- **更正 R0 §6 推論**:`diff.renames=copies` 時純 rename 仍為 R,不會以 C 進入 ACM(外部實測)。
- **R0 §3 缺口補查**(裁決者讀碼,推論):
  - production 沒有 `diff --staged` 用法。
  - `git status --porcelain` 有三處(`install.py:610`、`status.py:633`、`sync.py:291`),都是髒污檢查,不逐檔判定;rename 時仍非空。
- **權威層繞過**:仍為推論,待 T148-7 實測。
  - 本 repo 已有工作樹證紅,見〈第三站紅燈〉:T148-7 在現行程式下 rc 0。

## 待辦

- **#5 不改**:`scripts/e2e_authority_layer.py:1046` 的 `--diff-filter=ACM` 本輪不改(Jeff 裁決),另排。
- **R0 §3 剩餘缺口仍為 UNKNOWN**:`-C` / `copies` / `--raw`、字串拼接、二進位與編碼。
- **R7 前哨誤擋**(只記錄,不處理):
  - pytest `-k` 帶空白的引號字串(`-k "T148 or t148"`)被前哨以「引號或跳脫使目標無法可靠切分」整行擋下。
  - 擋下訊息是實測(2026-10-07,見停止報告 `.dev/reports/2026-10-07T204645Z-ticket148-s3-redlight.md` §3)。
  - 觸發點是否為 `gate.py` `_quoting_is_ambiguous` 以 `split()` 切 token,維持讀碼推論。
  - 與票 146 記錄的兩次 R7 誤擋同類。

## 第三站紅燈(S3-148-1)

審計:`docs/audits/2026-10-07-148-station3-redlight.md`。

- 測試已寫入工作樹、尚未 commit。
- 結果是**工作樹證紅**(測試基準 HEAD `6d80427b0bfd79d4c0477a8b93b2f8f65c44de09` + 未提交測試)。

| node | 驗什麼 | C0 | 工作樹證紅結果 |
|---|---|---|---|
| T148-1[unset] / [true] / [copies] | `gate.staged_paths` 在 `git mv src/a.py src/b.py` 後含 src/b.py | 紅 | 紅(AssertionError,清單 `[]`) |
| T148-1[false] | 同上,diff.renames=false(基線正控) | 綠 | 綠 |
| T148-2[unset] / [true] / [copies] | `scanner.staged_paths`,同上 | 紅 | 紅(AssertionError,清單 `[]`) |
| T148-2[false] | 同上(基線正控) | 綠 | 綠 |
| T148-3 | rename 後兩個 staged_paths 都不含來源 | 綠 | 綠 |
| T148-4 | 純刪除後兩個 staged_paths 都不含該檔 | 綠 | 綠 |
| T148-5 | leak scan 正控:新檔合成秘密 ⇒ 非 0、命中私鑰標頭規則與檔名 | 綠 | 綠 |
| T148-6 | leak scan 負控:git mv + 少量修改 + 合成秘密(前提:R、非 R100)⇒ 非 0 | 紅 | 紅(AssertionError,rc 0) |
| T148-7c | 權威層正控:tickets 站新增 pkg/fresh.py ⇒ rc 1、含 [R2、不含 [R10 | 綠 | 綠 |
| T148-7 | 權威層:tickets 站 git mv docs/tool.py pkg/tool.py(R)⇒ rc 1、含 [R2、不含 [R10 | 紅 | 紅(AssertionError,rc 0) |

- 新 node(`-k t148 -rA`):`8 failed, 6 passed, 2339 deselected`。14 個 node 名稱與參數 id 逐一相符,ERROR / skip / xfail 皆 0。
- 全套:`8 failed, 2332 passed, 10 skipped, 3 xfailed`。failed 恰為上表 8 個紅 node。
- R10 隔離採 (a):
  - tmp HOME / USERPROFILE 下建立空的使用者層 `.claude`。
  - tmp repo 提交合法空白 allowlist / inventory。
  - R10 走真實判定,不注入 `_extension_claude_root`。
  - R10 以外的鄰居照 `TestTicket146Integration._wire` 的同一份清單停掉,**不停 `staged_paths`**。

## 第四站實作(S4-148-1)

### 裁決(逐字節錄)

2026-10-07 16:37 美東:

> 「裁 A，#5 本輪不改，但記入票 148 待辦。
> #1 與 #3 加 `--no-renames`，保留既有 `--diff-filter=ACM`，讓 rename 目的檔按新增檔進入檢查；刪除處置不變。」

全文見〈Jeff 裁決(2026-10-07)〉。

2026-10-07 19:27 美東:

> 「信箱順手遮，只改票 149 的文件引用，不改 Git commit 身分或既有歷史；在 148 第四站准改清單明列這一處。
> VS 未重讀四份來源屬流程偏離，即使你已核對數值正確，也應保留紀錄。
> 切到 `implement` 的安排接受，只改 `current_stage`，保留 ticket 148 與其他欄位。切好後再審第四站指令；不 push。」

### 改動摘要

只改兩個 production 函式,另各補 docstring 說明理由。

| 呼叫點 | 改前 | 改後 |
|---|---|---|
| #1 `.claude/hooks/gate.py` `staged_paths` | `["git", "diff", "--cached", "-z", "--name-only", "--diff-filter=ACM"]` | `["git", "diff", "--cached", "-z", "--name-only", "--diff-filter=ACM", "--no-renames"]` |
| #3 `.claude/portable/scanner.py` `staged_paths` | `["git", "diff", "--cached", "-z", "--name-only", "--diff-filter=ACM"]` | `["git", "diff", "--cached", "-z", "--name-only", "--diff-filter=ACM", "--no-renames"]` |

- #5(`scripts/e2e_authority_layer.py:1046`)不改(Jeff 裁決)。
- 測試、policy 都沒有改動。

### 前檢證據(工作樹;測試基準 HEAD `96fc8b9c75e734bfc7af2a94c245cc96739aeb78` + 未提交實作)

- 新 node(`-k t148 -rA`):`14 passed, 2339 deselected`。
  - 14 個名稱與參數 id 和 S3 清單逐字相同。
  - failed / error / skipped / xfailed 都是 0。
- 全套:`2340 passed, 10 skipped, 3 xfailed`,0 failed。
  - 2340 = 2332 + 8,即 S3 的 8 個紅 node 轉綠。
  - 10 行 skipped 與 S3 相同。
- 淨室(`verify_gates.py`):rc 0。
  - R1~R10 各「擋下 ✓」。
  - R10 正控放行,「額外 2」擋下。
  - 權威層偵測三項 ✓。
  - 新 repo 框架測試 `2190 passed, 14 skipped, 3 xfailed`。
  - evidence 五情境皆「成立 ✓」。

審計:`docs/audits/2026-10-07-148-station4-implementation.md`。
