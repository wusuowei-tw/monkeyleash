# M1-a Station 5j 增量獨立審查包(票 145)

**審查對象(TARGET,本輪最後一個程式 commit)**:`d4b6fafd4afdd70121278527194aeef4097bff33`
**審查 HEAD(REVIEW_HEAD;review baseline)**:`38691e0cc4c2a72fa7909d924975ca1f67da38d0`
**審查範圍**:只審 3j / 3j-1b / 4j 增量(TARGET_I → TARGET)與兩個程序偏差對證據完整性的影響。5g / 5h / 5i 已審過 TARGET_I 之前的內容。

本包只是材料,不含任何審查結論。所有逐字段落皆以 `<!-- 逐字開始 -->` / `<!-- 逐字結束 -->` 標出邊界,
邊界之間的文字與標示的出處逐位元組相同(換行一律 LF)。
D 段與 E 段的逐字範圍是邊界內 ```` ``` ```` 圍籬**之間**的全部行(圍籬本身不屬於出處內容)。
E 段為 `git diff` / `git show` 原樣,**未去除行尾空白**(diff 的空白 context 行是單一空格)。
B、C、F、H 段的出處本身含有 ```` ``` ```` 圍籬或 markdown 標題;這些段不另加圍籬,邊界以該段標示的出處行號為準。
G 段的出處是裁決者的 Station 5j-0 指令原文(不在任何 repo 檔案內)。

---

## A. 身分與規則

### A.1 身分

| 代號 | 完整 SHA | 說明 |
|---|---|---|
| **BASE_I** | `36c978e1c20a51d40cac777dd5aee58625f97032` | 5i 審查 HEAD(S4I4) |
| **TARGET_I** | `8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8` | 5i 審過的最後程式 commit(S4I1) |
| S5i-0 | `55147ca78576a2eef8472b6761f50ff5b9c42b5c` | 5i 審查包 |
| S5i-1 | `ff859253ec74ee778ffc868307a4d66d452e4040` | 5i 審查報告入庫與 3j 裁決 |
| S3J1 | `9990fd654275a0af25fa51ce374dea3e812ef54e` | J1 / J2 紅燈 |
| S3J2 | `ee33e2d46c3efd44225e335e7b6158e467d07a18` | 3j 紅燈證據(docs) |
| S3J1B | `35d100a3841486e2d75ba39aea71bda601e18075` | J1b 紅燈(3j-1b) |
| S3J1B-2 | `dccc4bfc9b390aad9687384fba9db374b7da67af` | 3j-1b 證據(docs) |
| **TARGET**(S4J1) | `d4b6fafd4afdd70121278527194aeef4097bff33` | 本輪最後程式 commit —— **審查對象** |
| S4J3 | `79b09c19689e2948aa1200d9d3e92fd75283db80` | 4j 本機驗收證據(docs) |
| **REVIEW_HEAD**(S4J4) | `38691e0cc4c2a72fa7909d924975ca1f67da38d0` | POSIX 外部驗收記錄、4j 升級 PASS / COMPLETED(docs);review baseline |

- 本包所在的 commit(S5j-0)是 REVIEW_HEAD **之後**才建立的 docs-only commit;本包寫不進自己的 SHA,由裁決者交付審查時另附。S5j-0 **不屬於審查對象**。
- **CODE_FILES**(`git diff --name-only <TARGET_I>..<TARGET>` 中所有非 docs/ 的檔,2 個):`.claude/hooks/redlight.py` `tests/test_redlight.py`。
- TARGET 之後到 REVIEW_HEAD 只改 docs/。
- A.2 第 10 條沿用 5i 包原文寫「TARGET_H」,本輪對應為 TARGET_I;第 11 條沿用原文寫「G1–G9」,本包 G 段為 G1–G10,全部適用。

建包時核對(原文輸出;各自單獨執行,全部以完整 SHA 為錨點):

```
$ git merge-base --is-ancestor 36c978e1c20a51d40cac777dd5aee58625f97032 38691e0cc4c2a72fa7909d924975ca1f67da38d0
(無輸出;exit 0)
$ git rev-list --count 36c978e1c20a51d40cac777dd5aee58625f97032..38691e0cc4c2a72fa7909d924975ca1f67da38d0
9
$ git diff --name-only 8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8..d4b6fafd4afdd70121278527194aeef4097bff33
.claude/hooks/redlight.py
docs/audits/2026-10-05-m1a-station3j-redlight.md
docs/audits/2026-10-05-m1a-station4i-fix.md
docs/audits/2026-10-05-m1a-station5i-review-package.md
docs/audits/2026-10-05-m1a-station5i-review.md
docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
tests/test_redlight.py
$ git diff --name-only d4b6fafd4afdd70121278527194aeef4097bff33..38691e0cc4c2a72fa7909d924975ca1f67da38d0
docs/audits/2026-10-05-m1a-station4j-fix.md
docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
```

`git diff --name-only <TARGET_I>..<TARGET>` 全文亦見 D.2。

### A.2 審查者規則

1. **身分**:4g 實作 session、本輪實作 session(3h 起至 5j-0,含 5i-0 / 5i-1 / 3j / 3j-1b / 4j)、5g / 5h / 5i 審查 session 皆不得擔任 5j 審查者;5j 須在第五個全新對話進行。
2. **唯讀**:不改任何檔案、不 commit、不推、不改 `.dev/pipeline.json`。審查報告只寫到 `.scratch/m1a-s5j/review-report.md`(用 Write),不寫其他位置。
3. **禁止 pytest**(含 `--collect-only`、`--version`)、`verify_gates.py` 與 `status.py`。帳本(`.dev/test-runs.jsonl`、`.dev/test-sessions.jsonl`)會被任何 pytest 執行追加,審查不得污染證據。需要驗證行為時,讀程式碼做紙上推演;必須實跑才能確定者,寫成「需要重現」並描述最小重現方式。
4. **查詢一律綁定 A.1 的完整 SHA**;不以 `HEAD`、`HEAD~n`、遠端追蹤分支、本地分支名、短 SHA 或工作樹當下狀態為錨點。範例:

```
git show d4b6fafd4afdd70121278527194aeef4097bff33:<路徑>
git diff 8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8..d4b6fafd4afdd70121278527194aeef4097bff33 -- <路徑>
git log --oneline 36c978e1c20a51d40cac777dd5aee58625f97032..38691e0cc4c2a72fa7909d924975ca1f67da38d0
git show 38691e0cc4c2a72fa7909d924975ca1f67da38d0:docs/audits/2026-10-05-m1a-station4j-fix.md
```

5. **逐字段的邊界以各段標示的出處行號為準**(不以段內標題或圍籬判斷)。
6. 可用 Read / Grep 讀本機已安裝的 pytest / pluggy 原始碼與 git 文件;引用只寫 `_pytest/<檔名>:<行號>` 等相對形式,不寫本機絕對路徑。
7. **照錄任何系統訊息、錯誤訊息或路徑前,先把本機使用者名稱遮成 `<user>`。**
8. 被任何閘門(R1–R9、pre-commit、洩漏偵測)擋下:停手回報,不換工具、不繞過。
9. **結論只能是 `PASS` 或 `FAIL`**;finding 須標嚴重度,並附 `<TARGET>:<路徑>:<行號>` 形式的證據(以 TARGET 為準)。沒有檔名與行號證據的發現不計入判定。
10. **範圍**:5g / 5h 已審過 TARGET_H 之前的內容,本輪只審增量;但若增量使 5g / 5h 的任何結論失效,須指出。
11. G 段 G1–G9 每一題都必須回答(「無問題」也要附證據);不能回答的,寫明「無法判定」與原因,不得略過。
12. 不得用 python -c、heredoc 或把程式碼放進指令字串。
13. **不得讀取本機 AI 對話紀錄檔**;兩本帳本只准 `sha256sum` / `wc`,不得開啟內容。
14. **範圍聲明**:5j 只審 3j / 3j-1b / 4j 增量與兩個程序偏差對證據完整性的影響;exotic Git 佈局的加固不在本票範圍,發現者列為追蹤項而非 FAIL,除非它構成「未提交／identity 錯位卻能得到 file_coverage == "true"」的同級漏洞。

---

## B. 裁決與背景(逐字)

出處一律為 `38691e0cc4c2a72fa7909d924975ca1f67da38d0:docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md`(以下稱「REVIEW_HEAD 的票 145」)。

### B.1 〈六十一〉Station 5i 獨立審查與 Station 3j 裁決

行號來源:REVIEW_HEAD 的票 145 第 3078–3118 行

<!-- 逐字開始 -->
## 六十一、Station 5i 獨立審查（FAIL）與 Station 3j 裁決（2026-10-05，Jeff）

### 61.1 審查報告

- 路徑 `docs/audits/2026-10-05-m1a-station5i-review.md`;raw = repo 副本(與審查者原檔 `.scratch/m1a-s5i/review-report.md` 以 `cmp` 逐位元組相同,無任何改動);
  sha256 `c0b6dd87096c97070e860c100f61750eef614b9f07dc070dce741f49d8c91f71`;34640 bytes。
- 審查對象 TARGET `8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8`;審查包所在 commit S5i-0 `55147ca78576a2eef8472b6761f50ff5b9c42b5c`。
- **審查者判決:FAIL**(blocker 0、major 1、minor 0、nit 2)。
- Findings(報告第 2 節;一行摘要,不改寫結論):
  - S5i-F1【major;G9 / G2 / G1 / G8;需要重現】4i 以 `split(b"\n")` 只比 `lines[0]` / `lines[1]`(`redlight.py:739-742`),而 `--show-prefix` 輸出未跳脫的原始路徑位元組;POSIX 上名稱以 LF 開頭的子目錄 `parent/"\nsub"` 使輸出為 `true\n\nsub/\n` ⇒ `lines[1].strip() == b""` ⇒ True ⇒ 回到 S5g-F2 原形狀 ⇒ 預期 `file_coverage == "true"`;TARGET_H 整段 strip 對同一輸入為 False ⇒ 本輪引入的回歸。
  - S5i-F2【nit;G7 / G9】殘餘措辭把「位於 gitdir 或 bare repository 內的 root ⇒ unknown」寫成無條件;實測只設 `GIT_DIR`(cwd 在 gitdir)或 `core.worktree` 指向自己的 gitdir 時,Git 回報 `true` + 空 prefix 而被接受;依 G9 判準不構成 F2,只是與措辭後半的重新對應佈局重疊。
  - S5i-F3【nit;G5】I1 / I2 只斷言 `!= "true"`、區分不出是哪個條件擋下;I2 依賴隱式 bare 探索(`safe.bareRepository=explicit` 時會空洞通過);沒有測試直接鎖住 `:739-742` 的解析,所以 S5i-F1 這種解析層回歸現有測試看不到。
- 5h 總表 #3–#6(gitdir / bare 內)在 TARGET 已封住(X4–X7:第一行 `false`)。
- 5g / 5h 其餘結論:報告第 5 節逐條判定仍成立(G1 / G6 / G13 的「例外形狀」更新為:普通 ASCII 子目錄與 gitdir / bare 已封住;POSIX 上 LF 開頭的子目錄名仍存在 = S5i-F1)。
- 審查中一次 R7 攔截(scratchpad 內以 Bash 重導向寫假 policy 檔);審查者停手、未繞過,改以不寫檔內容的 `git init` / `mkdir` / `git config` / `git rev-parse` 實驗替代,合規(報告第 0 節照錄)。

### 61.2 裁決助手外部重現(隔離 Linux 環境;git 2.43.0;Python 3.11 + pytest 9.1.1;非獨立審查 finding;非本 repo 帳本證據)

來源:Jeff 的 Station 5i-1 指令,照錄。

- git 原語：於 git 最上層建名稱為 "\nsub"（LF 開頭）的子目錄，git -C <該目錄> rev-parse --is-inside-work-tree --show-prefix 的原始輸出為 t r u e \n \n s u b / \n（od -c）。--show-prefix 不跳脫 LF，與 5i 審查者由 X3 外推的結論一致。
- 端到端：以 S4I1 8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8 的 redlight.py 與既有 helper（_g_default_root、_g_coverage），root = <parent>/"\nsub"、三份未提交副本放在 root 下 ⇒ file_coverage == "true"。S5i-F1 由「需要重現」升為已確認；同一輸入在 S4H1（整段 strip 比對）為非 true ⇒ 4i 引入的回歸。
- 修法原型：_root_is_toplevel 改為 proc.stdout.replace(b"\r\n", b"\n") == b"true\n\n"（完整 stdout 相等；不拆行）。套用後上述原型轉為非 true；I1 / I2 / I3 / H1 / H2 維持綠；evidence 相關 5 檔共 283 支全過。
- J2 原型：直接呼叫 redlight._root_is_toplevel 對 toplevel / subdir / gitdir / bare 四種佈置，預期 True / False / False / False；在 S4I1 與修法原型上皆通過（regression-lock）。

### 61.3 裁決(照錄)

1. Station 5i 獨立審查 = FAIL；S5i-F1 = major / confirmed end-to-end / 4i-introduced regression。4i 以 split(b"\n") 只比對前兩行，而 --show-prefix 輸出未跳脫的原始路徑位元組；POSIX 上名稱以 LF 開頭的子目錄使 prefix 第一行為空 ⇒ 誤判為最上層 ⇒ 重新打開 S5g-F2 的 identity 錯位 ⇒ 仍可 file_coverage == "true"。S4H1 的整段 strip 比對對同一輸入為 False，故屬本輪引入。責任歸屬：4i 指令中的解析方式由裁決助手指定。
2. 回 Station 3j，紅燈兩支：
   J1 behavior-red（POSIX-only）：root = <最上層>/"\nsub"，三份副本只在 root 下、未提交 ⇒ 不得為 "true"。以 pytest.mark.skipif(sys.platform == "win32", reason=...) 標為 Windows skip；Jeff 特別核准：Windows 檔名模型無法合法建立該輸入，紅燈由裁決助手的 POSIX 驗收證明，且 3j POSIX 證據須保留「修前 J1 red、修後 green」，不得只看 4j 最終全綠。
   J2 regression-lock：直接呼叫 _root_is_toplevel，參數化四種佈置：git 最上層 ⇒ True；普通子目錄 ⇒ False；<最上層>/.git ⇒ False；<bare clone>/proj ⇒ False。鎖住 parser contract（S5i-F3 轉為機器鎖）。
3. Station 4j 最小修正：_root_is_toplevel 恢復完整 stdout contract —— stdout 先把 \r\n 正規化為 \n，再與 b"true\n\n" 完整相等；不拆行、不 strip。任何多餘位元組（含 prefix 首位元組為 LF）⇒ False ⇒ fail-closed。
4. S5i-F2（gitdir ⇒ unknown 寫成無條件，與「GIT_DIR / core.worktree 重新對應佈局會被接受」重疊）於 4j 文件補準。S5i-F3 由 J2 機器鎖處理，不另列追蹤項。
5. 流程：5i-1 記錄 → Jeff 切 tickets → 3j 紅燈（Windows 全套：J1 skip、J2 綠；裁決助手 POSIX：J1 red）→ Jeff 切 implement → 4j（Windows 全套、本機 clean-room、裁決助手 POSIX 含 J1 green）→ 5j 增量審查（第五個全新對話；4g 實作、本實作、5g / 5h / 5i 審查 session 皆不得擔任）→ Station 6。

> **裁決註記(Jeff,2026-10-05;3j-1b)**:R3 只認本機帳本紅燈;POSIX-only 紅燈不能單獨作為實作的 R3 前提,須另補本機可紅的解析層紅燈(3j-1b)。此為流程教訓,寫入追蹤項。(見〈六十二〉62.1;追蹤項見「相關」。)

### 61.4 commit

- S5i-1(本節與審查報告入庫)`ff859253ec74ee778ffc868307a4d66d452e4040`。
  (F-036:本行原文為「S5i-1(本節與審查報告入庫)於下一次提交回填。」;2026-10-05 於 S3J2 回填。)
<!-- 逐字結束 -->

### B.2 〈六十二〉Station 3j 紅燈證據(含 62.1)

行號來源:REVIEW_HEAD 的票 145 第 3122–3157 行

<!-- 逐字開始 -->
## 六十二、Station 3j 紅燈證據

- 合約:〈六十一〉61.3 裁決 2;Jeff 特別核准 J1 為 POSIX-only behavior-red,Windows 以 `skipif(sys.platform == "win32")` 跳過(Windows 檔名模型無法合法建立該輸入),紅燈由裁決助手 POSIX 驗收證明。
- 報告:`docs/audits/2026-10-05-m1a-station3j-redlight.md`。
- S3J1 `9990fd654275a0af25fa51ce374dea3e812ef54e`:`tests/test_redlight.py` 檔尾一個 hunk `@@ -2648,0 +2649,66 @@`,只有 + 行;新增 `class TestRootIsToplevelContract`,既有 helper 只呼叫、不修改;`sys` 於 class 內 import(未動檔頭)。commit 前只跑 py_compile。
- 新增 2 支(J2 參數化 4 案;完整 nodeid):
  - J1 behavior-red(POSIX-only;在 S5i-1 上於 POSIX 必須失敗):`tests/test_redlight.py::TestRootIsToplevelContract::test_j3_a_lf_prefixed_subdirectory_root_is_not_full_coverage`
  - J2 regression-lock(在 S5i-1 上必須通過):`tests/test_redlight.py::TestRootIsToplevelContract::test_j3_root_is_toplevel_follows_the_stdout_contract[toplevel]` / `[subdir]` / `[gitdir]` / `[bare]`
- Windows 全套(在 S3J1 上只跑一次;外來 3 檔已 stash,跑前跑後 `git status --porcelain` 皆無輸出):exit 0;
  摘要行原文 `2103 passed, 4 skipped, 3 xfailed in 253.83s (0:04:13)`(collected 2110、0 failed)。
  4 skipped = 既有 3 + J1(`SKIPPED [1] tests\test_redlight.py:2673: Windows 檔名不得含 LF;本案例由 POSIX 驗收證明(〈六十一〉61.3 裁決 2)`);J2 四案、I1–I3、H1–H2 在 passed 之內。
  Windows 全套不是 J1 的紅燈證據。
- 帳本只追加:兩本前段 sha256 = Step 0 基準(`9e909520…` / `440406f6…`);test-runs 3203 → 3250 行(+47)、test-sessions 31 → 32 行(+1)。
  跑後全檔記為 B19:test-runs 868808 bytes、`9abb70439a21bc07c60c3f413f619b9851080dfe265ecd2faf2eeca5303ef7b1`;
  test-sessions 15868084 bytes、`767488b978c7a8ef84da1da57733455f361dd30c44970bd3b78e79708d92159d`。
- 裁決助手 Linux 預演(來源:Jeff 的 Station 3j 指令;隔離環境;非本 repo 帳本證據;**J1 修前 red 的證據**):以 S4I1 的 redlight.py,J1 原型失敗於 got == "true"、J2 原型四案全過;套用 4j 修法原型(stdout 正規化後 == b"true\n\n")後 J1 轉綠、J2 維持綠、I1–I3 / H1–H2 綠,evidence 相關 5 檔 283 支全過。
- commit:S3J1 `9990fd654275a0af25fa51ce374dea3e812ef54e`;S3J2(本節與證據報告)`ee33e2d46c3efd44225e335e7b6158e467d07a18`。
  (F-036:本行原文為「S3J2(本節與證據報告)於下一次提交回填。」;2026-10-05 於 S3J1B-2 回填。)

### 62.1 3j-1b:R3 攔截與 Windows 可紅的解析層紅燈

- 起因:4j S4J1 對 `.claude/hooks/redlight.py` 的 Edit 被 R3 前哨擋下(原文照錄於報告第 6.1 節與 `.dev/reports/2026-10-05T184454Z-ticket145-station4j-blocked-r3.md`):本機帳本對 S4I1 版 `redlight.py` 沒有任何 `tests/test_redlight.py` 紅燈 —— J1 在 Windows 被跳過、J2 本來就綠,J1 的紅只在裁決助手的 Linux 證據裡。
- 裁決(Jeff):R3 擋下 = 照設計;選 A(補 Windows 可紅的解析層紅燈);不走豁免、不換環境。
- 報告:`docs/audits/2026-10-05-m1a-station3j-redlight.md` 第 6 節。
- S3J1B `35d100a3841486e2d75ba39aea71bda601e18075`:`tests/test_redlight.py` 檔尾一個 hunk `@@ -2714,0 +2715,36 @@`,只有 + 行;新增 `class TestRootIsToplevelParser`;以 monkeypatch 替身讓 `subprocess.run` 回傳 stdout `b"true\n\nsub/\n"`,不依賴檔案系統。commit 前只跑 py_compile。
- 新增 1 支(完整 nodeid):J1b behavior-red(在 S3J2 上必須失敗):`tests/test_redlight.py::TestRootIsToplevelParser::test_j3_a_lf_prefixed_show_prefix_stdout_is_not_toplevel`
- 紅燈全套(在 S3J1B 上只跑一次;Windows;外來 3 檔已 stash,跑前跑後 `git status --porcelain` 皆無輸出):exit 1;
  摘要行原文 `1 failed, 2103 passed, 4 skipped, 3 xfailed in 238.90s (0:03:58)`(collected 2111)。
  唯一的 FAILED 為 J1b,失敗行 `tests\test_redlight.py:2749: AssertionError`(`assert True is False`);J1 skipped;J2 四案、I1–I3、H1–H2 在 passed 之內。
  status:`tests red under ticket 145: tests/test_redlight.py`(R3 要的本機紅燈)。
- 帳本只追加:兩本前段 sha256 = B19(`9abb7043…` / `767488b9…`);test-runs 3250 → 3297 行(+47)、test-sessions 32 → 33 行(+1)。
  跑後全檔記為 B21:test-runs 880409 bytes、`670237025036aeef8fd427aaccb6c9d2fae9ed624d1f38b2f8b23d2c16fc6ee5`;
  test-sessions 16609700 bytes、`2badaee4cc130d1ec9fed57ffbac1c093ccee20c9c5547189caf576d5cbcad0b`。
- 裁決助手 Linux 預演(來源:Jeff 的 Station 3j-1b 指令;隔離環境;非本 repo 帳本證據):J1b 以 monkeypatch 替身在 S4I1 的 redlight.py 上失敗(assert True is False),在 4j 修法原型上通過。
- commit:S3J1B `35d100a3841486e2d75ba39aea71bda601e18075`;S3J1B-2(本小節與證據報告第 6 節)`dccc4bfc9b390aad9687384fba9db374b7da67af`。
  (F-036:本行原文為「S3J1B-2(本小節與證據報告第 6 節)於下一次提交回填。」;2026-10-05 於 S4J3 回填。)
<!-- 逐字結束 -->

### B.3 〈六十三〉Station 4j 修正(含 63.1 / 63.2 / 63.3)

行號來源:REVIEW_HEAD 的票 145 第 3161–3201 行

<!-- 逐字開始 -->
## 六十三、Station 4j 修正

### 63.1 第一次 4j:R3 攔截與裁決

- 第一次 4j 的 S4J1 對 `.claude/hooks/redlight.py` 的 Edit 被 R3 前哨擋下(原文照錄於 `docs/audits/2026-10-05-m1a-station4j-fix.md` 第 0 節;亦見 `docs/audits/2026-10-05-m1a-station3j-redlight.md` 第 6.1 節):
  `[六站閘門/前哨] [R3/紅燈][enforce] .claude/hooks/redlight.py:測試檔存在,但沒有合格的紅燈紀錄。`
  成因:本機帳本對 S4I1 版 `redlight.py` 沒有任何 `tests/test_redlight.py` 紅燈(J1 Windows skip、J2 本來就綠)。
- Jeff 裁決(2026-10-05):第一次 4j = BLOCKED BY R3(閘門照設計;不視為 FAIL、不繞過);選 A,補 3j-1b(J1b,見〈六十二〉62.1);Station 3j-1b = APPROVED;4j 只改 `_root_is_toplevel()`,恢復完整 stdout contract;J1 / J1b / J2 / I1–I3 / H1 / H2 不准修改。
- 三段式:S4J1 實作 → S4J2 本機驗收 → S4J3 docs-only(只能宣稱本機驗收通過;待 POSIX 外部驗收)。

### 63.2 證據

- 報告:`docs/audits/2026-10-05-m1a-station4j-fix.md`。
- S4J1 `d4b6fafd4afdd70121278527194aeef4097bff33`:只改 `.claude/hooks/redlight.py` 的 `_root_is_toplevel()`(+4 / −5,兩個 hunk `@@ -726,7 +726,9 @@`(docstring)與 `@@ -736,10 +738,7 @@`(本體),皆在該函式內)。
  - 本體改為 `return proc.stdout.replace(b"\r\n", b"\n") == b"true\n\n"`:不拆行、不 strip,任何多餘位元組(含 prefix 首位元組為 LF)⇒ False;例外 / returncode ≠ 0 ⇒ False 不變。
  - 未改 `committed_blobs` / `evidence_policy_facts` 的呼叫處、consumer、`policy_state`、conftest、status / install / verify_gates、任何測試;`content_hash` 未動。
  - 一次 Edit(本次重送未被擋),寫入後 status.py 探針無「redlight.py 無 run 事實讀取」。
- S4J2 本機固定全套(S4J1 上只跑一次;Windows;外來 3 檔已 stash):exit 0;`2104 passed, 4 skipped, 3 xfailed in 251.83s (0:04:11)`(collected 2111、0 failed)。
  J1 於 Windows 為 skipped(`tests\test_redlight.py:2673`);J1b 由紅轉綠;J2 四案、I1–I3、H1–H2 維持綠。
- 帳本只追加:前段 sha256 = B21;test-runs 3297 → 3344(+47)、test-sessions 33 → 34(+1)。
- status:`evidence policy: 有效`;`tests red under ticket 145: (無)`;run 事實未知 0;`tests/test_redlight.py` 在 green。
- 淨室(verify_gates;同一次執行):R1–R9 各擋下一次、權威層偵測三項成立、淨室框架測試 `1954 passed, 8 skipped, 3 xfailed`;兩正三負全部成立,正二 `file_coverage=true`、`green=tests/test_evidence_probe.py`。
  本 repo 兩本帳本前後 bytes 與 sha256 都等於 V0(test-runs 891928 / `22148446…`;test-sessions 17351316 / `3d7cde59…`)。
- 裁決助手 Linux 證據(來源:Jeff 的 Station 4j 重送指令;隔離環境;git 2.43.0;Python 3.11 + pytest 9.1.1;非本 repo 帳本證據):以 S3J1B 的 tests/test_redlight.py 原檔 + S4I1 的 redlight.py,J1 與 J1b failed、J2 四案 passed;套用修正形狀後 J1 / J1b / J2 / H1 / H2 / I1–I3 全 passed,evidence 相關 5 檔 288 支全過。
- 殘餘與未證明(目前尚未 machine-enforced):沿用 4i 證據報告第 7 節 + S5g-F1 / F3 / F4 / F5、S5h-F4 追蹤項;S5h-F3 已補準;S5i-F3 由 J2 / J1b 機器鎖處理;流程教訓追蹤項「R3 與 POSIX-only 紅燈」(見「相關」)。本輪依 S5i-F2 補準措辭(照錄於報告第 7 節第 4 點,取代 4i 版本對應段落):
  「本輪檢查的語意是 git rev-parse --is-inside-work-tree --show-prefix 的 stdout（\r\n 正規化後）完整等於 b"true\n\n"，即 Git 對該 root 回報「在工作樹內」且 prefix 為空且沒有任何其他位元組。在預設環境（未設 GIT_DIR / GIT_WORK_TREE / core.worktree）下明確不支援（⇒ unknown）：monorepo 中非最上層的普通子目錄（H1；含 POSIX 上名稱以 LF 開頭者，J1 / J1b）、位於 gitdir 或 bare repository 內的 root（I1 / I2）。會被接受但本輪未納入 acceptance、屬未證明：巢狀獨立 Git repo、submodule、linked worktree、.git 為檔案且 gitdir 指向他處，以及 GIT_DIR / GIT_WORK_TREE / core.worktree 等重新對應佈局（含 Git 因此把 gitdir 本身視為工作樹的情形）。上述佈局若 Git 對該 root 實際回報上述 stdout，即會被本檢查接受；其 HEAD 與工作樹是否符合既定 identity invariant，本輪未完整 acceptance，不得宣稱已拒絕或已支援。」
- commit:S4J1 `d4b6fafd4afdd70121278527194aeef4097bff33`;S4J3 `79b09c19689e2948aa1200d9d3e92fd75283db80`(本節與證據報告)。
  (F-036:本行原文為「S4J3(本節與證據報告)於下一次提交回填。」;2026-10-05 於 S4J4 回填。)

### 63.3 POSIX 外部 clean-room 驗收

> **舊文字(F-036,保留不刪)**:~~待執行(裁決助手)。須含 J1 在 S4J1 原檔上由紅(3j 證據)轉綠。~~
> —— 2026-10-05 由 S4J4 的 POSIX 驗收紀錄取代。

- 來源：Jeff 轉述裁決助手 2026-10-05 Linux 證據（隔離沙盒；git 2.43.0；Python 3.11.16 + pytest 9.1.1 + anyio 4.15.0；非本 repo 帳本證據；本 repo 兩本帳本未動）。
- 受測物：S4J1 的 `.claude/hooks/redlight.py` 原檔（blob `d4d208af69340e369f1e263bc620217c66e7a683`，sha256 `1fd20bc3b02669f7e0f779a00cbf6d420d8e12474b327cdba74affa5f6ef2782`，與本機 S4J2 run 紀錄的 impl_hash 相同）；`tests/test_redlight.py` = S3J1B 原檔（blob `c284bc8c56e005b334595185c5d54a6bc11ae6b9`）。置於全新 clone、提交後工作樹乾淨。
- evidence 相關 5 檔（test_redlight / test_host_evidence_policy / test_evidence_isolation / test_status / test_gate）：`1 failed, 961 passed`；唯一 failed 為已知環境性 `tests/test_gate.py::TestAuthorityLayerIsWired::test_this_repo_itself_is_wired`。J1 於 Linux 實際執行（非 skip）且 passed —— 由 3j 證據（對 S4I1 failed）轉綠；J1b、J2 四案、I1–I3、H1 / H2、T1 / T2 共 13 支全 passed。
- `verify_gates.py` 淨室：R1–R9 各擋下一次、權威層偵測三項成立、框架測試 `1958 passed, 4 skipped, 3 xfailed`；兩正三負全部成立，正二 `file_coverage=true`、`green=tests/test_evidence_probe.py`。
- 固定全套 `python -X utf8 -m pytest -q`：`13 failed, 2095 passed, 3 xfailed`（collected 2111；0 skipped，Linux 可建 symlink 且 J1 實跑）。依 Jeff 轉述，13 個 failed 與 4i POSIX 驗收那次逐字相同（test_gate 1 支 + test_known_items_regression 12 支）；推測為環境性、未新增 4j 回歸，尚未獨立核驗或 machine-enforced。Jeff 據此外部證據裁決 Station 4j = PASS / COMPLETED。
- Jeff 裁決（2026-10-05）：Station 4j = PASS / COMPLETED（Windows 本機 + POSIX 外部 clean-room）；待 Station 5j 獨立審查（第五個全新對話）。
- 程序偏差（S4J2/S4J3 期間）：(a) 3d 後 5 條唯讀檢查並行送出；(b) 以 grep 讀取本 session 對話紀錄檔以找回 S5i-F2 補準措辭，違反「不得讀取本機對話紀錄」規則。兩者皆唯讀、未寫入 repo，證據不受影響；S5i-F2 finding 本身已在已提交的 5i 審查報告與本票〈六十一〉內，對話紀錄不是唯一來源。Jeff 裁決記錄為程序偏差、不重做，後續各站不得再犯；5j 審查須自行核對最終措辭與已提交的 S5i-F2 finding 相符。
<!-- 逐字結束 -->

---

## C. 5i 審查報告中與 S5i-F1 / F2 / F3 相關的段落(逐字)

出處一律為 `38691e0cc4c2a72fa7909d924975ca1f67da38d0:docs/audits/2026-10-05-m1a-station5i-review.md`(以下稱「5i 審查報告」)。

### C.1 第 1 節判決與嚴重度依據

行號來源:5i 審查報告第 72–82 行

<!-- 逐字開始 -->
## 1. 判決

**FAIL**(blocker 0、major 1、minor 0、nit 2)。

FAIL 的唯一原因是 S5i-F1:4i 把 `proc.stdout.strip() == b""` 換成 `split(b"\n")` 後只看 `lines[1]`,而 `--show-prefix` 輸出的是**未跳脫的原始路徑位元組**。在允許檔名含換行的檔案系統(Linux / macOS)上,名稱以換行開頭(前面可有空白)的子目錄,prefix 的第一行 strip 後為空 ⇒ `_root_is_toplevel` 回 True ⇒ 回到 S5g-F2 的原形狀(子目錄 root、上層 HEAD blob = 子目錄副本)⇒ 預期 `file_coverage == "true"`。**TARGET_H 對同一輸入回 False**(整段 strip 後剩 `sub/`),所以這是本輪引入的回歸。

**嚴重度的判斷依據與替代選項(給裁決者)**:

- A(本報告採用):判 **major** ⇒ FAIL。理由:這是同一條 I-3 位置不變式、同一種 identity 錯位、方向是 fail-open;而且是**本輪的修正把 TARGET_H 已封住的輸入重新打開**。〈五十三〉53.3 裁決 1 與〈五十七〉57.3 裁決 1 的先例,都是「只有手動佈局才會產生」也定為 FAIL 等級。
- B:判 **minor**(佈局比 gitdir 內更不自然:要有名稱以換行開頭的目錄,而且 Windows NTFS 根本建不出來)⇒ 本輪 PASS,S5i-F1 列追蹤項。代價:`redlight.py:727-729` docstring「任一查詢失敗或條件不符 ⇒ False」與殘餘措辭「明確不支援(⇒ unknown):monorepo 中非最上層的普通子目錄」在 POSIX 上都不成立,錯的方向是 fail-open。
- 修法成本(供比較,不是本報告的要求):在 `:739-742` 改成完整比對,例如 `proc.stdout.replace(b"\r\n", b"\n") == b"true\n\n"`;或要求 `len(lines) == 3 and lines[2] == b""`,且 `lines[1]` 只去掉 `\r`、不做 `strip()`。任何一種寫法,TARGET_H 那種「整段 strip」的保護也就一起回來了。
<!-- 逐字結束 -->

### C.2 Findings 表的表頭與 S5i-F1 / F2 / F3 列

行號來源:5i 審查報告第 88–92 行

<!-- 逐字開始 -->
| 編號 | 嚴重度 | 對應 G 題 | TARGET 檔名:行號 | 具體失敗情境(輸入 → 錯誤結果) | 依據 | 需要重現 |
|---|---|---|---|---|---|---|
| S5i-F1 | **major** | G9 / G2 / G1 / G8 | `.claude/hooks/redlight.py:739-742`(`split(b"\n")` 後只比 `lines[0]` / `lines[1]`,`lines[2:]` 完全不看);`:727-729` docstring;呼叫點 `:758`(`committed_blobs`)、`:874`(`evidence_policy_facts`)→ `:876` `HEAD:<POLICY_FILE>` / `:880` `hash-object <POLICY_FILE>`、`:765-766`;`tests/conftest.py:410-412` | POSIX 檔案系統。Git 最上層 `parent` 已提交合法 policy、`pyproject.toml`、`tests/conftest.py`;root = `parent/"\nsub"`(名稱以 LF 開頭的子目錄;或名稱恰為 `"\n"`、`" \n…"`、`"\t\nX"`),三份位元組相同的副本只在 root 下、從未提交。`git -C <root> rev-parse --is-inside-work-tree --show-prefix` 預期輸出 `true\n\nsub/\n` → `lines = [b"true", b"", b"sub/", b""]` → `lines[0] == b"true"` 且 `lines[1].strip() == b""` ⇒ **True** → `HEAD:<path>` 取上層 tree 根的 blob、`hash-object <path>` 讀 root 底下的副本 → head == worktree → 其餘條件與 H1 相同 ⇒ 預期 `file_coverage == "true"`。**TARGET_H 同一輸入**:`b"\nsub/\n".strip() == b"sub/"` ≠ `b""` ⇒ False ⇒ unknown。⇒ 本輪引入的回歸,重新打開 S5g-F2 原形狀 | (1) 程式:`:739-742`。(2) 實測(第 4 節 X3):`--show-prefix` 輸出原始位元組、不做 C 式引號跳脫 —— 目錄 `中` 的輸出是 `true\n` + `344 270 255 /\n`,不是 `"\344\270\255/"`;因此名稱裡的 LF 會原樣輸出。(3) 正常最上層 `true\n\n`(X1)、子目錄 `true\nsub/\n`(X2)的行結構與推演一致。(4) Windows NTFS 不允許檔名含控制字元,所以本機無法建出這個佈局 | **是**。git 原語層最小重現(POSIX):`mkdir -p "p/$(printf '\nsub')"`,然後 `git -C "p/$(printf '\nsub')" rev-parse --is-inside-work-tree --show-prefix > out`,`od -c out`;預期 `t r u e \n \n s u b / \n`。端到端:沿用 H1(`tests/test_redlight.py:2560-2567`),把 `sub = parent / "sub"` 改成 `sub = parent / "\nsub"`;預期 TARGET 得 `"true"`、TARGET_H 得非 `"true"` |
| S5i-F2 | nit | G7 / G9 | 殘餘措辭(REVIEW_HEAD `docs/audits/2026-10-05-m1a-station4i-fix.md` 第 7 節第 3 點;票 145〈五十九〉59.2);`.claude/hooks/redlight.py:727-728` docstring | 措辭把「位於 gitdir 或 bare repository 內的 root(I1 / I2)」列為**無條件的**「明確不支援(⇒ unknown)」。實測有兩種情況,root 就在 gitdir 內,Git 卻回報 `--is-inside-work-tree=true` 且 prefix 為空,所以會被接受:(a) 環境有 `GIT_DIR=<p/.git>`、沒有 `GIT_WORK_TREE`,cwd = `p/.git`(X9:`true`、空、`--show-toplevel` = `p/.git`);(b) 該 repo 的 `core.worktree` 指向它自己的 gitdir(X8:`r/.git` 得 `true`、空、toplevel = `r/.git`)。這兩種都是 Git 自己把 gitdir 當成工作樹,依 G9 判準(policy 在該 root 自己解析到的 HEAD)**不構成 F2**;而且措辭後半的「GIT_DIR / … core.worktree 等重新對應佈局 … 會被接受」已經涵蓋。所以這只是前後兩句重疊、前一句寫成了無條件 | X8、X9 原文(第 4 節) | 否 |
| S5i-F3 | nit | G5 | `tests/test_redlight.py:2600-2629`(I1 / I2 只斷言 `!= "true"`);全樹沒有直接呼叫 `_root_is_toplevel` 的測試(`git grep` 原文見第 4 節 X0) | (a) I1 / I2 跟 H1 一樣只斷言 `!= "true"`,區分不出「是 `_root_is_toplevel` 擋的」還是「別的條件剛好 unknown」。(b) I2 靠的是隱式 bare 探索:如果環境設了 `safe.bareRepository=explicit`,git 直接失敗,I2 會在修正前也綠(空洞地通過)。本輪 S3I1 的實跑紅燈已證明預設環境下形狀成立,所以不影響 G4。(c) 沒有任何測試直接鎖住 `:739-742` 的解析,所以 S5i-F1 這種只在解析層出錯的回歸,現有測試看不到 | 靜態閱讀;X0 | 否 |
<!-- 逐字結束 -->

### C.3 G2 結論

行號來源:5i 審查報告第 104–112 行

<!-- 逐字開始 -->
### G2 stdout 解析的健壯性 —— **部分成立(附 S5i-F1)**

- **正常最上層不會被誤判成 False**:
  - 實測原始位元組 `t r u e \n \n`(X1,`od -c`)⇒ `[b"true", b"", b""]` ⇒ True。
  - CRLF:Git for Windows 的 stdout 實測只有 LF(X1–X4 的 `od -c` 都沒有 `\r`)。即使某個環境輸出 `\r\n`,`lines[0].strip()` / `lines[1].strip()` 也會去掉 `\r` ⇒ 仍是 True。
  - 尾端多一個換行:多出來的元素落在 `lines[2:]`,不影響判斷。
  - 舊版 git 在最上層如果不印 `--show-prefix` 的空行(輸出只有 `true\n`):`[b"true", b""]`,`len == 2` ⇒ 仍是 True。本機只有 2.53.0,這一點是推演。
- **不健壯的地方**:`lines[1].strip()` 會把「prefix 第一行」當成「整個 prefix」。prefix 是原始路徑、可以含 LF(X3 證明輸出沒有跳脫)⇒ 非最上層可能被誤判成 True(S5i-F1)。方向是 **fail-open**,不是封死正常 host。
- 空白開頭的目錄名(` sub`):prefix ` sub/`,strip 後是 `sub/` ⇒ False,正確。只有 `\r`(`"\r"` 目錄):prefix `\r/`,strip 後是 `/` ⇒ False,正確。出問題的只有「第一個路徑成分是(可帶空白的)LF 開頭」這一類。
<!-- 逐字結束 -->

### C.4 G5 結論

行號來源:5i 審查報告第 130–136 行

<!-- 逐字開始 -->
### G5 三支測試是否真的測到宣稱的形狀 —— **成立(附 S5i-F3)**

- I1(`tests/test_redlight.py:2600-2613`):`parent = _g_default_root(...)`(`:2216-2218` → `_g_root`,在 parent 裡 add / commit 三檔);`root = parent / ".git"`;`_copy_into`(`:2593-2598`)只做 `read_bytes` / `write_bytes`,沒有 git add ⇒ 副本從未提交。`_g_coverage(root)` → `_g_run` → `_isolated_conftest`(`:298-312`,`:306` 把真實 conftest 的 `_ROOT` 設成 root)→ 真實 producer `tests/conftest.py:410-412`。
- I2(`:2615-2629`):`_d_git(tmp_path, "clone", "-q", "--bare", parent, bare)`;`root = bare / "proj"`;同樣只複製、不提交,同樣經過真實 producer。
- I3(`:2631-…`):直接呼叫 `redlight.committed_blobs(str(sub))`,不經 `evidence_policy_facts`;`sub = parent / "sub"`,只複製 `pyproject.toml`、`tests/conftest.py`,正好等於 `BLOB_FILES`(`redlight.py:497` = `("pyproject.toml",) + ("tests/conftest.py",)`)。斷言 key 集合 = `BLOB_FILES`、每一路徑 `{"worktree": None, "head": None}`;對照組 `committed_blobs(str(parent))` 每一路徑 worktree 非空且 == head ⇒ 對照組證明 git 在這個環境可用,None 不是因為 git 壞了。
- S3I1 上 I1 / I2 實際得到 `'true'`,本身就證明它們重現了 identity 錯位可達 true 的形狀。
- 弱點見 S5i-F3。
<!-- 逐字結束 -->

### C.5 G7 結論

行號來源:5i 審查報告第 143–148 行

<!-- 逐字開始 -->
### G7 殘餘措辭與程式一致 —— **部分成立**

- 「本輪檢查的語意是 `--is-inside-work-tree` 為 true 且 `--show-prefix` 為空」:**在 prefix 不含 LF 時**與 `:742` 一致。prefix 含 LF 時,程式實際接受的是「prefix 的第一行為空」(S5i-F1)。
- 「明確不支援(⇒ unknown):monorepo 中非最上層的普通子目錄(H1)」:在 POSIX 上,名稱以 LF 開頭的子目錄不成立(S5i-F1)。
- 「位於 gitdir 或 bare repository 內的 root(I1 / I2)⇒ unknown」:在預設環境成立(X4–X7);在 `GIT_DIR` 有設或 `core.worktree` 指向 gitdir 時,會被接受(X8、X9)⇒ S5i-F2(nit)。
- 「會被接受但本輪未納入 acceptance……不得宣稱已拒絕或已支援」:與實測一致(X8–X12 都是 `true` + 空 prefix),而且沒有宣稱已拒絕或已支援任何未測佈局 —— 這一點符合要求。
<!-- 逐字結束 -->

### C.6 G9 結論

行號來源:5i 審查報告第 157–161 行

<!-- 逐字開始 -->
### G9 總問題(增量版)—— **不成立(找到反例:S5i-F1)**

- 5h 總表 #3–#6(gitdir / bare 內)**現在都被擋**(X4–X7:第一行 `false`)。
- 新反例:POSIX 上名稱以 LF 開頭的子目錄 root(S5i-F1)。被驗證的 HEAD 物件是上層 tree 根的 `<path>`,工作樹讀的是 `<子目錄>/<path>`;Git 本身會把後者對應到 tree 路徑 `"\nsub/<path>"`,不是 `<path>` ⇒ 正是要抓的 identity 錯位。git 原語層的推演依據是 X3(prefix 不跳脫);端到端需要重現。
- 其餘嘗試依 G9 判準都不構成 F2,清單見第 4 節。
<!-- 逐字結束 -->

### C.7 S5i-F1 的重現步驟原文

行號來源:5i 審查報告第 90 行(Findings 表 S5i-F1 列;重現步驟在該列最後一欄「需要重現」:「**是**。git 原語層最小重現(POSIX):…」。表格列無法以行切出單欄,所以取整行;與 C.2 第 3 行相同)

<!-- 逐字開始 -->
| S5i-F1 | **major** | G9 / G2 / G1 / G8 | `.claude/hooks/redlight.py:739-742`(`split(b"\n")` 後只比 `lines[0]` / `lines[1]`,`lines[2:]` 完全不看);`:727-729` docstring;呼叫點 `:758`(`committed_blobs`)、`:874`(`evidence_policy_facts`)→ `:876` `HEAD:<POLICY_FILE>` / `:880` `hash-object <POLICY_FILE>`、`:765-766`;`tests/conftest.py:410-412` | POSIX 檔案系統。Git 最上層 `parent` 已提交合法 policy、`pyproject.toml`、`tests/conftest.py`;root = `parent/"\nsub"`(名稱以 LF 開頭的子目錄;或名稱恰為 `"\n"`、`" \n…"`、`"\t\nX"`),三份位元組相同的副本只在 root 下、從未提交。`git -C <root> rev-parse --is-inside-work-tree --show-prefix` 預期輸出 `true\n\nsub/\n` → `lines = [b"true", b"", b"sub/", b""]` → `lines[0] == b"true"` 且 `lines[1].strip() == b""` ⇒ **True** → `HEAD:<path>` 取上層 tree 根的 blob、`hash-object <path>` 讀 root 底下的副本 → head == worktree → 其餘條件與 H1 相同 ⇒ 預期 `file_coverage == "true"`。**TARGET_H 同一輸入**:`b"\nsub/\n".strip() == b"sub/"` ≠ `b""` ⇒ False ⇒ unknown。⇒ 本輪引入的回歸,重新打開 S5g-F2 原形狀 | (1) 程式:`:739-742`。(2) 實測(第 4 節 X3):`--show-prefix` 輸出原始位元組、不做 C 式引號跳脫 —— 目錄 `中` 的輸出是 `true\n` + `344 270 255 /\n`,不是 `"\344\270\255/"`;因此名稱裡的 LF 會原樣輸出。(3) 正常最上層 `true\n\n`(X1)、子目錄 `true\nsub/\n`(X2)的行結構與推演一致。(4) Windows NTFS 不允許檔名含控制字元,所以本機無法建出這個佈局 | **是**。git 原語層最小重現(POSIX):`mkdir -p "p/$(printf '\nsub')"`,然後 `git -C "p/$(printf '\nsub')" rev-parse --is-inside-work-tree --show-prefix > out`,`od -c out`;預期 `t r u e \n \n s u b / \n`。端到端:沿用 H1(`tests/test_redlight.py:2560-2567`),把 `sub = parent / "sub"` 改成 `sub = parent / "\nsub"`;預期 TARGET 得 `"true"`、TARGET_H 得非 `"true"` |
<!-- 逐字結束 -->

---

## D. 本輪 commit 與檔案範圍

### D.1 `git log --oneline 36c978e1c20a51d40cac777dd5aee58625f97032..38691e0cc4c2a72fa7909d924975ca1f67da38d0`(9 筆,與 A.1 的 S5i-0…S4J4 逐一對應)

<!-- 逐字開始 -->
```
38691e0 docs(145): M1-a Station 4j-4 —— POSIX 外部 clean-room 驗收通過，4j = PASS / COMPLETED；待 5j 審查
79b09c1 docs(145): M1-a Station 4j-3 —— S5i-F1 修正的本機驗收證據(待 POSIX 外部驗收)
d4b6faf fix(145): M1-a Station 4j-1 —— _root_is_toplevel 恢復完整 stdout contract(S5i-F1)
dccc4bf docs(145): M1-a Station 3j-1b-2 —— R3 攔截與 Windows 可紅的解析層紅燈證據(J1b red)
35d100a test(145): M1-a Station 3j-1b —— Windows 可紅的 _root_is_toplevel 解析層紅燈(S5i-F1;1 支)
ee33e2d docs(145): M1-a Station 3j-2 —— 紅燈證據(J1 POSIX-only、J2 lock 綠;S5i-F1 / S5i-F3)
9990fd6 test(145): M1-a Station 3j-1 —— _root_is_toplevel stdout contract 紅燈(S5i-F1 / S5i-F3;2 支)
ff85925 docs(145): M1-a Station 5i-1 —— 增量審查入庫(FAIL:S5i-F1 major,4i 引入)與 Station 3j 裁決
55147ca docs(145): M1-a Station 5i-0 —— 增量獨立審查包(只審 3i / 4i)
```
<!-- 逐字結束 -->

### D.2 `git diff --name-only 8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8..d4b6fafd4afdd70121278527194aeef4097bff33`(NAMEONLY_FULL;TARGET_I..TARGET 全範圍)

這是「CODE_FILES 以外的非 docs 檔(conftest、status.py、install.py、verify_gates.py 等)都沒變」的證據;E.1 / E.4 只餵了 CODE_FILES,不足以證明這一點。

<!-- 逐字開始 -->
```
.claude/hooks/redlight.py
docs/audits/2026-10-05-m1a-station3j-redlight.md
docs/audits/2026-10-05-m1a-station4i-fix.md
docs/audits/2026-10-05-m1a-station5i-review-package.md
docs/audits/2026-10-05-m1a-station5i-review.md
docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
tests/test_redlight.py
```
<!-- 逐字結束 -->

---

## E. 程式差異(原樣)

### E.1 `git diff 8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8..d4b6fafd4afdd70121278527194aeef4097bff33 -- .claude/hooks/redlight.py tests/test_redlight.py`(本輪全部程式與測試改動)

<!-- 逐字開始 -->
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
diff --git a/tests/test_redlight.py b/tests/test_redlight.py
index 1b48694..c284bc8 100644
--- a/tests/test_redlight.py
+++ b/tests/test_redlight.py
@@ -2646,3 +2646,105 @@ class TestEvidenceRootIsInsideWorkTree:
         assert all(v == {"worktree": None, "head": None} for v in blobs.values()), blobs
         control = redlight.committed_blobs(str(parent))
         assert all(v["worktree"] and v["worktree"] == v["head"] for v in control.values()), control
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# 票 145 Station 3j 補紅燈 —— S5i-F1 / S5i-F3:`_root_is_toplevel` 的 stdout contract(〈六十一〉61.3 裁決 2、3)
+#
+# `git rev-parse --is-inside-work-tree --show-prefix` 的 stdout 須**完整**等於 `b"true\n\n"`;不得拆行只看前兩行。
+# `--show-prefix` 輸出未跳脫的原始路徑位元組 —— POSIX 上名稱以 LF 開頭的子目錄,prefix 的第一行為空,
+# 拆行只看 `lines[1]` 的解析會把它誤判為最上層 ⇒ 重新打開 S5g-F2 的 identity 錯位(S5i-F1)。
+# 既有 helper(`_g_default_root` / `_g_coverage` / `_G_POLICY_FILE` / `_d_git` / `redlight._root_is_toplevel`)
+# 只呼叫、不修改。
+# ─────────────────────────────────────────────────────────────────────────────
+
+class TestRootIsToplevelContract:
+
+    import sys
+
+    @staticmethod
+    def _copy_into(parent, root, rels):
+        """把 `parent` 底下的 `rels` 逐一以位元組複製到 `root` 底下(只寫工作樹,不 git add / commit)。"""
+        for rel in rels:
+            dst = root / rel
+            dst.parent.mkdir(parents=True, exist_ok=True)
+            dst.write_bytes((parent / rel).read_bytes())
+
+    @pytest.mark.skipif(sys.platform == "win32",
+                        reason="Windows 檔名不得含 LF;本案例由 POSIX 驗收證明(〈六十一〉61.3 裁決 2)")
+    def test_j3_a_lf_prefixed_subdirectory_root_is_not_full_coverage(self, tmp_path, monkeypatch):
+        """J1。分類:behavior-red(POSIX-only;在 S5i-1 上於 POSIX 必須失敗)。Windows 以 skipif 跳過
+        (Jeff 特別核准:Windows 檔名模型無法合法建立該輸入,紅燈由裁決助手的 POSIX 驗收證明)。
+
+        Git 最上層 `parent` 已提交合法 policy、`pyproject.toml`、`tests/conftest.py`;root = `parent/"\\nsub"`
+        (名稱以 LF 開頭的子目錄),三份位元組相同的副本只在 root 下、從未提交 ⇒ 不得為 `"true"`。
+        S5i-1 上失敗的原因:`--show-prefix` 輸出未跳脫的原始路徑位元組,stdout 為 `true\\n\\nsub/\\n`;
+        4i 拆行後只看 `lines[1]`(為空)⇒ 誤判為最上層 ⇒ identity 錯位即可取得 `"true"`(S5i-F1)。
+        """
+        parent = _g_default_root(tmp_path / "parent")
+        root = parent / "\nsub"
+        self._copy_into(parent, root, (_G_POLICY_FILE, "pyproject.toml", "tests/conftest.py"))
+        got = _g_coverage(root, monkeypatch)
+        assert got != "true", got
+
+    @pytest.mark.parametrize("layout, expected", [
+        pytest.param("toplevel", True, id="toplevel"),
+        pytest.param("subdir", False, id="subdir"),
+        pytest.param("gitdir", False, id="gitdir"),
+        pytest.param("bare", False, id="bare"),
+    ])
+    def test_j3_root_is_toplevel_follows_the_stdout_contract(self, tmp_path, layout, expected):
+        """J2。分類:regression-lock(在 S5i-1 上必須通過)。直接鎖 `redlight._root_is_toplevel` 的 parser contract
+        (S5i-F3 轉機器鎖):git 最上層 ⇒ True;普通子目錄 ⇒ False;`<最上層>/.git` ⇒ False;
+        `<bare clone>/proj` ⇒ False。
+        """
+        parent = _g_default_root(tmp_path / "parent")
+        if layout == "toplevel":
+            root = parent
+        elif layout == "subdir":
+            root = parent / "sub"
+            root.mkdir()
+        elif layout == "gitdir":
+            root = parent / ".git"
+        else:
+            bare = tmp_path / "bare.git"
+            _d_git(tmp_path, "clone", "-q", "--bare", str(parent), str(bare))
+            root = bare / "proj"
+            root.mkdir()
+        assert redlight._root_is_toplevel(str(root)) is expected
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# 票 145 Station 3j-1b 補紅燈 —— S5i-F1 解析層(Windows 可紅)
+#
+# 以 monkeypatch 替身供給「LF 開頭 prefix」的 stdout,不依賴檔案系統 —— Windows 檔名不得含 LF,
+# J1(POSIX 端到端)在 Windows 被跳過,本機帳本因此沒有 R3 要的紅燈。J1b 與 J1 互補:J1 證明端到端形狀,
+# J1b 在任何平台證明解析層。既有 helper(`redlight._root_is_toplevel`)只呼叫、不修改。
+# ─────────────────────────────────────────────────────────────────────────────
+
+class TestRootIsToplevelParser:
+
+    def test_j3_a_lf_prefixed_show_prefix_stdout_is_not_toplevel(self, tmp_path, monkeypatch):
+        """J1b。分類:behavior-red(在 S3J2 上必須失敗)。
+
+        stdout `b"true\\n\\nsub/\\n"` 即 POSIX 上名稱以 LF 開頭的子目錄(`"\\nsub"`)所得:`--show-prefix`
+        輸出未跳脫的原始路徑位元組。拆行只看前兩行(`lines[0] == b"true"`、`lines[1]` 為空)會誤判 True;
+        修正後 stdout 須完整等於 `b"true\\n\\n"`(\\r\\n 正規化後)才為 True ⇒ 這裡必須是 False。
+        另斷言呼叫的確是 `rev-parse --is-inside-work-tree --show-prefix`,替身沒有被別的指令吃掉。
+        """
+        import subprocess as _sp
+
+        class _Proc:
+            returncode = 0
+            stdout = b"true\n\nsub/\n"
+            stderr = b""
+
+        calls = []
+
+        def fake_run(args, **kw):
+            calls.append(list(args))
+            return _Proc()
+
+        monkeypatch.setattr(_sp, "run", fake_run)
+        assert redlight._root_is_toplevel(str(tmp_path)) is False
+        assert calls and calls[0][-2:] == ["--is-inside-work-tree", "--show-prefix"], calls
```
<!-- 逐字結束 -->

### E.2 `git diff 8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8..9990fd654275a0af25fa51ce374dea3e812ef54e -- tests/test_redlight.py`(3j:J1 / J2)

<!-- 逐字開始 -->
```
diff --git a/tests/test_redlight.py b/tests/test_redlight.py
index 1b48694..54557c3 100644
--- a/tests/test_redlight.py
+++ b/tests/test_redlight.py
@@ -2646,3 +2646,69 @@ class TestEvidenceRootIsInsideWorkTree:
         assert all(v == {"worktree": None, "head": None} for v in blobs.values()), blobs
         control = redlight.committed_blobs(str(parent))
         assert all(v["worktree"] and v["worktree"] == v["head"] for v in control.values()), control
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# 票 145 Station 3j 補紅燈 —— S5i-F1 / S5i-F3:`_root_is_toplevel` 的 stdout contract(〈六十一〉61.3 裁決 2、3)
+#
+# `git rev-parse --is-inside-work-tree --show-prefix` 的 stdout 須**完整**等於 `b"true\n\n"`;不得拆行只看前兩行。
+# `--show-prefix` 輸出未跳脫的原始路徑位元組 —— POSIX 上名稱以 LF 開頭的子目錄,prefix 的第一行為空,
+# 拆行只看 `lines[1]` 的解析會把它誤判為最上層 ⇒ 重新打開 S5g-F2 的 identity 錯位(S5i-F1)。
+# 既有 helper(`_g_default_root` / `_g_coverage` / `_G_POLICY_FILE` / `_d_git` / `redlight._root_is_toplevel`)
+# 只呼叫、不修改。
+# ─────────────────────────────────────────────────────────────────────────────
+
+class TestRootIsToplevelContract:
+
+    import sys
+
+    @staticmethod
+    def _copy_into(parent, root, rels):
+        """把 `parent` 底下的 `rels` 逐一以位元組複製到 `root` 底下(只寫工作樹,不 git add / commit)。"""
+        for rel in rels:
+            dst = root / rel
+            dst.parent.mkdir(parents=True, exist_ok=True)
+            dst.write_bytes((parent / rel).read_bytes())
+
+    @pytest.mark.skipif(sys.platform == "win32",
+                        reason="Windows 檔名不得含 LF;本案例由 POSIX 驗收證明(〈六十一〉61.3 裁決 2)")
+    def test_j3_a_lf_prefixed_subdirectory_root_is_not_full_coverage(self, tmp_path, monkeypatch):
+        """J1。分類:behavior-red(POSIX-only;在 S5i-1 上於 POSIX 必須失敗)。Windows 以 skipif 跳過
+        (Jeff 特別核准:Windows 檔名模型無法合法建立該輸入,紅燈由裁決助手的 POSIX 驗收證明)。
+
+        Git 最上層 `parent` 已提交合法 policy、`pyproject.toml`、`tests/conftest.py`;root = `parent/"\\nsub"`
+        (名稱以 LF 開頭的子目錄),三份位元組相同的副本只在 root 下、從未提交 ⇒ 不得為 `"true"`。
+        S5i-1 上失敗的原因:`--show-prefix` 輸出未跳脫的原始路徑位元組,stdout 為 `true\\n\\nsub/\\n`;
+        4i 拆行後只看 `lines[1]`(為空)⇒ 誤判為最上層 ⇒ identity 錯位即可取得 `"true"`(S5i-F1)。
+        """
+        parent = _g_default_root(tmp_path / "parent")
+        root = parent / "\nsub"
+        self._copy_into(parent, root, (_G_POLICY_FILE, "pyproject.toml", "tests/conftest.py"))
+        got = _g_coverage(root, monkeypatch)
+        assert got != "true", got
+
+    @pytest.mark.parametrize("layout, expected", [
+        pytest.param("toplevel", True, id="toplevel"),
+        pytest.param("subdir", False, id="subdir"),
+        pytest.param("gitdir", False, id="gitdir"),
+        pytest.param("bare", False, id="bare"),
+    ])
+    def test_j3_root_is_toplevel_follows_the_stdout_contract(self, tmp_path, layout, expected):
+        """J2。分類:regression-lock(在 S5i-1 上必須通過)。直接鎖 `redlight._root_is_toplevel` 的 parser contract
+        (S5i-F3 轉機器鎖):git 最上層 ⇒ True;普通子目錄 ⇒ False;`<最上層>/.git` ⇒ False;
+        `<bare clone>/proj` ⇒ False。
+        """
+        parent = _g_default_root(tmp_path / "parent")
+        if layout == "toplevel":
+            root = parent
+        elif layout == "subdir":
+            root = parent / "sub"
+            root.mkdir()
+        elif layout == "gitdir":
+            root = parent / ".git"
+        else:
+            bare = tmp_path / "bare.git"
+            _d_git(tmp_path, "clone", "-q", "--bare", str(parent), str(bare))
+            root = bare / "proj"
+            root.mkdir()
+        assert redlight._root_is_toplevel(str(root)) is expected
```
<!-- 逐字結束 -->

### E.3 `git diff ee33e2d46c3efd44225e335e7b6158e467d07a18..35d100a3841486e2d75ba39aea71bda601e18075 -- tests/test_redlight.py`(3j-1b:J1b)

<!-- 逐字開始 -->
```
diff --git a/tests/test_redlight.py b/tests/test_redlight.py
index 54557c3..c284bc8 100644
--- a/tests/test_redlight.py
+++ b/tests/test_redlight.py
@@ -2712,3 +2712,39 @@ class TestRootIsToplevelContract:
             root = bare / "proj"
             root.mkdir()
         assert redlight._root_is_toplevel(str(root)) is expected
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# 票 145 Station 3j-1b 補紅燈 —— S5i-F1 解析層(Windows 可紅)
+#
+# 以 monkeypatch 替身供給「LF 開頭 prefix」的 stdout,不依賴檔案系統 —— Windows 檔名不得含 LF,
+# J1(POSIX 端到端)在 Windows 被跳過,本機帳本因此沒有 R3 要的紅燈。J1b 與 J1 互補:J1 證明端到端形狀,
+# J1b 在任何平台證明解析層。既有 helper(`redlight._root_is_toplevel`)只呼叫、不修改。
+# ─────────────────────────────────────────────────────────────────────────────
+
+class TestRootIsToplevelParser:
+
+    def test_j3_a_lf_prefixed_show_prefix_stdout_is_not_toplevel(self, tmp_path, monkeypatch):
+        """J1b。分類:behavior-red(在 S3J2 上必須失敗)。
+
+        stdout `b"true\\n\\nsub/\\n"` 即 POSIX 上名稱以 LF 開頭的子目錄(`"\\nsub"`)所得:`--show-prefix`
+        輸出未跳脫的原始路徑位元組。拆行只看前兩行(`lines[0] == b"true"`、`lines[1]` 為空)會誤判 True;
+        修正後 stdout 須完整等於 `b"true\\n\\n"`(\\r\\n 正規化後)才為 True ⇒ 這裡必須是 False。
+        另斷言呼叫的確是 `rev-parse --is-inside-work-tree --show-prefix`,替身沒有被別的指令吃掉。
+        """
+        import subprocess as _sp
+
+        class _Proc:
+            returncode = 0
+            stdout = b"true\n\nsub/\n"
+            stderr = b""
+
+        calls = []
+
+        def fake_run(args, **kw):
+            calls.append(list(args))
+            return _Proc()
+
+        monkeypatch.setattr(_sp, "run", fake_run)
+        assert redlight._root_is_toplevel(str(tmp_path)) is False
+        assert calls and calls[0][-2:] == ["--is-inside-work-tree", "--show-prefix"], calls
```
<!-- 逐字結束 -->

### E.4 `git diff dccc4bfc9b390aad9687384fba9db374b7da67af..d4b6fafd4afdd70121278527194aeef4097bff33 -- .claude/hooks/redlight.py tests/test_redlight.py`(4j)

輸出只有 `.claude/hooks/redlight.py`;`tests/test_redlight.py` 在 S3J1B-2..TARGET 之間沒有差異(預期為空,實際為空)。

<!-- 逐字開始 -->
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
<!-- 逐字結束 -->

### E.5 `git show d4b6fafd4afdd70121278527194aeef4097bff33:.claude/hooks/redlight.py` 的 `_root_is_toplevel` 全文(第 726–741 行)

<!-- 逐字開始 -->
```
def _root_is_toplevel(root):
    """root 是否就是 git 工作樹的最上層:須同時 `--is-inside-work-tree` 為 true 且 `--show-prefix` 為空
    (票 145 Station 4i,S5h-F1:gitdir / bare repository 內 `--show-prefix` 同樣為空,但不是工作樹)。
    任一查詢失敗或條件不符 ⇒ False。
    stdout 須完整等於 b"true\n\n"(\r\n 正規化後):--show-prefix 輸出未跳脫的原始路徑位元組,
    拆行只看前兩行會把 LF 開頭的子目錄名誤判為空 prefix(票 145 Station 4j,S5i-F1)。"""
    import subprocess
    try:
        proc = subprocess.run(["git", "-C", os.fspath(root), "rev-parse",
                               "--is-inside-work-tree", "--show-prefix"],
                              capture_output=True, timeout=30)
    except Exception:
        return False
    if proc.returncode != 0:
        return False
    return proc.stdout.replace(b"\r\n", b"\n") == b"true\n\n"
```
<!-- 逐字結束 -->

### E.6 `git show d4b6fafd4afdd70121278527194aeef4097bff33:tests/test_redlight.py` 的兩個 class 全文

#### E.6.1 `TestRootIsToplevelContract`(第 2661–2714 行)

<!-- 逐字開始 -->
```
class TestRootIsToplevelContract:

    import sys

    @staticmethod
    def _copy_into(parent, root, rels):
        """把 `parent` 底下的 `rels` 逐一以位元組複製到 `root` 底下(只寫工作樹,不 git add / commit)。"""
        for rel in rels:
            dst = root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes((parent / rel).read_bytes())

    @pytest.mark.skipif(sys.platform == "win32",
                        reason="Windows 檔名不得含 LF;本案例由 POSIX 驗收證明(〈六十一〉61.3 裁決 2)")
    def test_j3_a_lf_prefixed_subdirectory_root_is_not_full_coverage(self, tmp_path, monkeypatch):
        """J1。分類:behavior-red(POSIX-only;在 S5i-1 上於 POSIX 必須失敗)。Windows 以 skipif 跳過
        (Jeff 特別核准:Windows 檔名模型無法合法建立該輸入,紅燈由裁決助手的 POSIX 驗收證明)。

        Git 最上層 `parent` 已提交合法 policy、`pyproject.toml`、`tests/conftest.py`;root = `parent/"\\nsub"`
        (名稱以 LF 開頭的子目錄),三份位元組相同的副本只在 root 下、從未提交 ⇒ 不得為 `"true"`。
        S5i-1 上失敗的原因:`--show-prefix` 輸出未跳脫的原始路徑位元組,stdout 為 `true\\n\\nsub/\\n`;
        4i 拆行後只看 `lines[1]`(為空)⇒ 誤判為最上層 ⇒ identity 錯位即可取得 `"true"`(S5i-F1)。
        """
        parent = _g_default_root(tmp_path / "parent")
        root = parent / "\nsub"
        self._copy_into(parent, root, (_G_POLICY_FILE, "pyproject.toml", "tests/conftest.py"))
        got = _g_coverage(root, monkeypatch)
        assert got != "true", got

    @pytest.mark.parametrize("layout, expected", [
        pytest.param("toplevel", True, id="toplevel"),
        pytest.param("subdir", False, id="subdir"),
        pytest.param("gitdir", False, id="gitdir"),
        pytest.param("bare", False, id="bare"),
    ])
    def test_j3_root_is_toplevel_follows_the_stdout_contract(self, tmp_path, layout, expected):
        """J2。分類:regression-lock(在 S5i-1 上必須通過)。直接鎖 `redlight._root_is_toplevel` 的 parser contract
        (S5i-F3 轉機器鎖):git 最上層 ⇒ True;普通子目錄 ⇒ False;`<最上層>/.git` ⇒ False;
        `<bare clone>/proj` ⇒ False。
        """
        parent = _g_default_root(tmp_path / "parent")
        if layout == "toplevel":
            root = parent
        elif layout == "subdir":
            root = parent / "sub"
            root.mkdir()
        elif layout == "gitdir":
            root = parent / ".git"
        else:
            bare = tmp_path / "bare.git"
            _d_git(tmp_path, "clone", "-q", "--bare", str(parent), str(bare))
            root = bare / "proj"
            root.mkdir()
        assert redlight._root_is_toplevel(str(root)) is expected
```
<!-- 逐字結束 -->

#### E.6.2 `TestRootIsToplevelParser`(第 2725–2750 行)

<!-- 逐字開始 -->
```
class TestRootIsToplevelParser:

    def test_j3_a_lf_prefixed_show_prefix_stdout_is_not_toplevel(self, tmp_path, monkeypatch):
        """J1b。分類:behavior-red(在 S3J2 上必須失敗)。

        stdout `b"true\\n\\nsub/\\n"` 即 POSIX 上名稱以 LF 開頭的子目錄(`"\\nsub"`)所得:`--show-prefix`
        輸出未跳脫的原始路徑位元組。拆行只看前兩行(`lines[0] == b"true"`、`lines[1]` 為空)會誤判 True;
        修正後 stdout 須完整等於 `b"true\\n\\n"`(\\r\\n 正規化後)才為 True ⇒ 這裡必須是 False。
        另斷言呼叫的確是 `rev-parse --is-inside-work-tree --show-prefix`,替身沒有被別的指令吃掉。
        """
        import subprocess as _sp

        class _Proc:
            returncode = 0
            stdout = b"true\n\nsub/\n"
            stderr = b""

        calls = []

        def fake_run(args, **kw):
            calls.append(list(args))
            return _Proc()

        monkeypatch.setattr(_sp, "run", fake_run)
        assert redlight._root_is_toplevel(str(tmp_path)) is False
        assert calls and calls[0][-2:] == ["--is-inside-work-tree", "--show-prefix"], calls
```
<!-- 逐字結束 -->

---

## F. 證據(逐字)

F.1 / F.2 出處為 REVIEW_HEAD(`38691e0cc4c2a72fa7909d924975ca1f67da38d0`);F.3 出處為本機未入庫檔(見 F.3 段首)。

### F.0 J1 / J1b / J2 紅綠定位表(非逐字;每格附 F.1 / F.2 出處行號)

F.1 / F.2 的行號 = REVIEW_HEAD 上該檔的行號(本包 F.1 / F.2 逐字段與之逐行對應)。

| 測試 | 修前(S3J1 / S3J1B 上) | S4J1(TARGET)Windows 固定全套 | S4J1(TARGET)Linux(裁決助手) |
|---|---|---|---|
| J1 `tests/test_redlight.py::TestRootIsToplevelContract::test_j3_a_lf_prefixed_subdirectory_root_is_not_full_coverage`(behavior-red,POSIX-only;F.2 第 43 行) | **Windows skipped**:F.2 第 62 行 `SKIPPED [1] tests\test_redlight.py:2673: …`、第 72–73 行「4 skipped = 既有 3 + J1」「本節不是 J1 的紅燈證據」;F.2 第 176 行(S3J1B 上同樣 SKIPPED)。**Linux failed(裁決助手;非本 repo 帳本)**:F.2 第 106 行「以 S4I1 的 redlight.py,J1 原型失敗於 got == "true"」、第 108 行;F.1 第 200 行「以 S3J1B 的 tests/test_redlight.py 原檔 + S4I1 的 redlight.py:J1 與 J1b failed」 | **skipped**:F.1 第 92 行 `SKIPPED [1] tests\test_redlight.py:2673: …`、第 97 行「J1 於 Windows 為 skipped」 | **passed**:F.1 第 228 行「J1 於 Linux 實際執行(非 skip)且 passed —— 由 3j 證據(對 S4I1 failed)轉綠」 |
| J1b `tests/test_redlight.py::TestRootIsToplevelParser::test_j3_a_lf_prefixed_show_prefix_stdout_is_not_toplevel`(behavior-red,解析層;F.2 第 156 行) | **Windows failed(本機帳本)**:F.2 第 165 行 `E       AssertionError: assert True is False`、第 170 行 `tests\test_redlight.py:2749: AssertionError`、第 177 行 `FAILED …test_j3_a_lf_prefixed_show_prefix_stdout_is_not_toplevel`、第 178 行摘要 `1 failed, 2103 passed, 4 skipped, 3 xfailed`、第 181 行「唯一的 FAILED 是 J1b」、第 186 行 `tests red under ticket 145: tests/test_redlight.py`。Linux:F.1 第 200 行「J1 與 J1b failed」 | **passed**:F.1 第 93 行摘要 `2104 passed, 4 skipped, 3 xfailed`(0 failed)、第 96 行、第 98 行「J1b 由紅轉綠」 | **passed**:F.1 第 228 行「J1b、J2 四案、I1–I3、H1 / H2、T1 / T2 共 13 支全 passed」 |
| J2 `tests/test_redlight.py::TestRootIsToplevelContract::test_j3_root_is_toplevel_follows_the_stdout_contract[toplevel/subdir/gitdir/bare]`(regression-lock;F.2 第 44–47 行) | **passed**:F.2 第 68 行摘要 `2103 passed, 4 skipped, 3 xfailed`(0 failed)、第 71–72 行「J2 四案…在 2103 passed 之內」;F.2 第 181 行(S3J1B 上 J2 四案在 passed 之內)。Linux:F.1 第 200 行「J2 四案 passed」 | **passed**:F.1 第 93 行摘要(0 failed)、第 99 行「J2 四案…維持綠」 | **passed**:F.1 第 228 行 |

R3 攔截的原文與時序:F.3 第 56–69 行(第一次 4j,HEAD = S3J2,帳本 = B19);F.2 第 116–130 行;F.1 第 19–34 行。

### F.1 `docs/audits/2026-10-05-m1a-station4j-fix.md` 全文

行號來源:REVIEW_HEAD 的該檔第 1–232 行

<!-- 逐字開始 -->
# 票 145 Station 4j —— S5i-F1 最小修正(_root_is_toplevel 恢復完整 stdout contract)與本機驗收

- 日期:2026-10-05
- 對象:S4J1 `d4b6fafd4afdd70121278527194aeef4097bff33`(只改 `.claude/hooks/redlight.py` 的 `_root_is_toplevel()`)。
- 上一個 commit:S3J1B-2 `dccc4bfc9b390aad9687384fba9db374b7da67af`;紅燈 S3J1 `9990fd654275a0af25fa51ce374dea3e812ef54e`(J1 / J2)、S3J1B `35d100a3841486e2d75ba39aea71bda601e18075`(J1b)。
- 合約:票 145〈六十一〉61.3 裁決 3;Jeff 裁決:第一次 4j = BLOCKED BY R3(閘門照設計;不視為 FAIL、不繞過);Station 3j-1b = APPROVED;4j 只改 `_root_is_toplevel()`,恢復完整 stdout contract;J1 / J1b / J2 / I1–I3 / H1 / H2 不准修改。
- 範圍:**本機(Windows)驗收**。POSIX 外部 clean-room 驗收尚未執行(第 9 節)。本報告只宣稱:本機驗收通過;~~待 POSIX 外部驗收~~。（S4J4 後更新：POSIX 外部 clean-room 驗收已 PASS，見第 9 節；Station 4j = PASS / COMPLETED；待 Station 5j 獨立審查。刪除線為 F-036 保存的舊狀態字樣，2026-10-05 由 S4J4 取代。）

## 【給裁決者】

1. 第一次 4j 改程式時被 R3 擋下(本機沒有紅燈紀錄);依你的裁決先補 3j-1b 的 J1b(Windows 可紅),這次重送才動手。
2. 修正:判「root 是不是工作樹最上層」改成 Git 的輸出必須**整段**剛好是 `true` 加兩個換行,多一個位元組都不算;舊寫法只看前兩行,會被名稱以換行開頭的子目錄騙過。
3. 本機全套 2104 passed、0 failed;J1b 由紅轉綠;J1 在 Windows 照設計跳過(要靠 POSIX 驗收證明)。
4. 淨室兩正三負全部成立,正二仍可退紅;本 repo 測試帳本只往後加,淨室前後完全沒動。
5. 下一步是 POSIX 外部淨室驗收(裁決助手執行,須含 J1 由紅轉綠)。（S4J4 後更新：POSIX 已 PASS，J1 於 Linux 實跑並轉綠，見第 9 節；狀態已升級。）

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
- **程序偏差(b)(S4J4 補記)**:以 grep 讀取本 session 對話紀錄檔以找回 S5i-F2 補準措辭，違反「不得讀取本機對話紀錄」規則。兩者皆唯讀、未寫入 repo，證據不受影響；S5i-F2 finding 本身已在已提交的 5i 審查報告與本票〈六十一〉內，對話紀錄不是唯一來源。Jeff 裁決記錄為程序偏差、不重做，後續各站不得再犯；5j 審查須自行核對最終措辭與已提交的 S5i-F2 finding 相符。
- 本 session 自 3h 起為實作 session;5j 審查須開第五個全新對話,4g 實作 session、本 session、5g / 5h / 5i 審查 session 皆不得擔任。

### 9. POSIX 外部 clean-room 驗收

> **舊文字(F-036,保留不刪)**:本節標題原為 ~~`### 9. POSIX 外部 clean-room 驗收:待執行(裁決助手)`~~,沒有內文。
> 2026-10-05 S4J4 依 Jeff 裁決改為下方照錄段落。

- 來源：Jeff 轉述裁決助手 2026-10-05 Linux 證據（隔離沙盒；git 2.43.0；Python 3.11.16 + pytest 9.1.1 + anyio 4.15.0；非本 repo 帳本證據；本 repo 兩本帳本未動）。
- 受測物：S4J1 的 `.claude/hooks/redlight.py` 原檔（blob `d4d208af69340e369f1e263bc620217c66e7a683`，sha256 `1fd20bc3b02669f7e0f779a00cbf6d420d8e12474b327cdba74affa5f6ef2782`，與本機 S4J2 run 紀錄的 impl_hash 相同）；`tests/test_redlight.py` = S3J1B 原檔（blob `c284bc8c56e005b334595185c5d54a6bc11ae6b9`）。置於全新 clone、提交後工作樹乾淨。
- evidence 相關 5 檔（test_redlight / test_host_evidence_policy / test_evidence_isolation / test_status / test_gate）：`1 failed, 961 passed`；唯一 failed 為已知環境性 `tests/test_gate.py::TestAuthorityLayerIsWired::test_this_repo_itself_is_wired`。J1 於 Linux 實際執行（非 skip）且 passed —— 由 3j 證據（對 S4I1 failed）轉綠；J1b、J2 四案、I1–I3、H1 / H2、T1 / T2 共 13 支全 passed。
- `verify_gates.py` 淨室：R1–R9 各擋下一次、權威層偵測三項成立、框架測試 `1958 passed, 4 skipped, 3 xfailed`；兩正三負全部成立，正二 `file_coverage=true`、`green=tests/test_evidence_probe.py`。
- 固定全套 `python -X utf8 -m pytest -q`：`13 failed, 2095 passed, 3 xfailed`（collected 2111；0 skipped，Linux 可建 symlink 且 J1 實跑）。依 Jeff 轉述，13 個 failed 與 4i POSIX 驗收那次逐字相同（test_gate 1 支 + test_known_items_regression 12 支）；推測為環境性、未新增 4j 回歸，尚未獨立核驗或 machine-enforced。Jeff 據此外部證據裁決 Station 4j = PASS / COMPLETED。
- Jeff 裁決（2026-10-05）：Station 4j = PASS / COMPLETED（Windows 本機 + POSIX 外部 clean-room）；待 Station 5j 獨立審查（第五個全新對話）。
- 程序偏差（S4J2/S4J3 期間）：(a) 3d 後 5 條唯讀檢查並行送出；(b) 以 grep 讀取本 session 對話紀錄檔以找回 S5i-F2 補準措辭，違反「不得讀取本機對話紀錄」規則。兩者皆唯讀、未寫入 repo，證據不受影響；S5i-F2 finding 本身已在已提交的 5i 審查報告與本票〈六十一〉內，對話紀錄不是唯一來源。Jeff 裁決記錄為程序偏差、不重做，後續各站不得再犯；5j 審查須自行核對最終措辭與已提交的 S5i-F2 finding 相符。
<!-- 逐字結束 -->

### F.2 `docs/audits/2026-10-05-m1a-station3j-redlight.md` 全文

行號來源:REVIEW_HEAD 的該檔第 1–225 行

<!-- 逐字開始 -->
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
<!-- 逐字結束 -->

### F.3 `.dev/reports/2026-10-05T184454Z-ticket145-station4j-blocked-r3.md` 全文

來源:本機 `.dev/reports/2026-10-05T184454Z-ticket145-station4j-blocked-r3.md`(未入庫;`.dev/` 被 .gitignore 忽略,不在任何 commit 裡,**不是**「逐字自 REVIEW_HEAD」);sha256 = `49e64c90b778be7f9bd19f7a0636ff4555da01c32c0178fe745ef1b578880056`;wc -c = 7045。行號來源:該本機檔第 1–133 行。

<!-- 逐字開始 -->
# 票 145 Station 4j —— 停手回報:S4J1 的 Edit 被 R3 前哨擋下

## 【給裁決者】

1. 4j 修正還沒做成:改 `redlight.py` 的那一次 Edit 被閘門 R3(紅燈規則:改實作前必須有本機紅燈紀錄)擋下。照規則停手,沒有繞過、沒有換工具,檔案沒有任何改動,也沒有 commit。外來 3 檔已放回原狀。
2. 原因:R3 只認本機帳本上「對著現在這版 redlight.py 跑出來的紅燈」。J1 在 Windows 被跳過,J2 本來就是綠的,所以本機帳本上 `tests/test_redlight.py` 沒有任何紅燈;J1 的紅燈只存在裁決助手的 Linux 證據裡,閘門看不到。
3. 這是你核准「J1 只在 POSIX 紅」時沒有預見的後果:權威層(pre-commit)也會用同一條 R3 擋 commit,所以就算有人手改檔案,commit 一樣會被擋。
4. 要你決定怎麼讓 4j 合法通過 R3(選項見下段,建議 A)。
5. 不決定的話:S4J1 無法提交,流程停在 4j 開始前;S5i-F1 仍開著。

## 【給裁決助手】

### Step 0(各自單獨執行;全部符合)

```
$ cat .dev/pipeline.json
{
  "current_stage": "implement",
  "feature": "framework-updates",
  "ticket_id": "145",
  "updated": "2026-10-05"
}
$ git rev-parse HEAD
ee33e2d46c3efd44225e335e7b6158e467d07a18
$ git status --porcelain
 M docs/agents/friction-log.md
?? docs/tickets/framework-updates/146-claude-code-enforcement-integrity.md
?? docs/tickets/framework-updates/147-turn-end-check-via-settings-stop-hook.md
$ wc -c .dev/test-runs.jsonl
868808 .dev/test-runs.jsonl
$ wc -c .dev/test-sessions.jsonl
15868084 .dev/test-sessions.jsonl
$ wc -l .dev/test-runs.jsonl
3250 .dev/test-runs.jsonl
$ wc -l .dev/test-sessions.jsonl
32 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl
9abb70439a21bc07c60c3f413f619b9851080dfe265ecd2faf2eeca5303ef7b1 *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
767488b978c7a8ef84da1da57733455f361dd30c44970bd3b78e79708d92159d *.dev/test-sessions.jsonl
```

與 S3J2 回報的 B19 一致。

### Step 1

```
$ git stash push -u -m jeff-mods-recon-20261004-s4j -- docs/agents/friction-log.md docs/tickets/framework-updates/146-claude-code-enforcement-integrity.md docs/tickets/framework-updates/147-turn-end-check-via-settings-stop-hook.md
Saved working directory and index state On master: jeff-mods-recon-20261004-s4j
$ git stash list
stash@{0}: On master: jeff-mods-recon-20261004-s4j
$ git status --porcelain
(無輸出)
```

### Step 2 —— 攔截(原始擋下訊息,照錄)

對 `.claude/hooks/redlight.py` 的 Edit(把 `lines = proc.stdout.split(b"\n")` … `return lines[0].strip() == b"true" and lines[1].strip() == b""` 換成 `return proc.stdout.replace(b"\r\n", b"\n") == b"true\n\n"`,並補 docstring):

```
PreToolUse:Edit hook error: [python "$CLAUDE_PROJECT_DIR/.claude/hooks/gate.py"]: [六站閘門/前哨] [R3/紅燈][enforce] .claude/hooks/redlight.py:測試檔存在,但沒有合格的紅燈紀錄。
     tests/test_redlight.py 有執行紀錄,但沒有任何一筆是「紅燈,且發生在這次改動之前」。
     合格的形狀:實作當時不存在,或紅燈是對著這支檔案在 HEAD 的
     內容跑出來的。先寫實作再補跑紅燈不算 —— 那是補測試,不是紅綠燈。
     先跑測試確認它在實作不存在時是紅的,再回來寫功能碼。
(權威判定在 pre-commit,繞過前哨仍會在 commit 被擋)
```

處置:停手。Edit 未生效(`git status --porcelain` 無輸出);未 py_compile、未 add、未 commit;沒有改用其他工具、沒有改路徑、沒有改 `.dev/pipeline.json`。

```
$ git status --porcelain
(無輸出)
```

### Step 3 / Step 4

未執行(依「任何攔截 ⇒ 停手回報」)。沒有跑 pytest / verify_gates,帳本未動(仍為 B19)。

### Step 5

```
$ git stash pop
On branch master
Your branch is ahead of 'origin/master' by 30 commits.
  (use "git push" to publish your local commits)

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   docs/agents/friction-log.md

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	docs/tickets/framework-updates/146-claude-code-enforcement-integrity.md
	docs/tickets/framework-updates/147-turn-end-check-via-settings-stop-hook.md

no changes added to commit (use "git add" and/or "git commit -a")
Dropped refs/stash@{0} (7fd30ec6847715002b245d80ec95e06ad9848183)
$ git status --porcelain
 M docs/agents/friction-log.md
?? docs/tickets/framework-updates/146-claude-code-enforcement-integrity.md
?? docs/tickets/framework-updates/147-turn-end-check-via-settings-stop-hook.md
$ git diff --stat
 docs/agents/friction-log.md | 33 +++++++++++++++++++++++++++++++++
 1 file changed, 33 insertions(+)
$ git stash list
(無輸出)
```

主判準:與 P0 三行逐字相同。

### 成因分析(推論;未讀 gate.py 原始碼驗證細節)

- R3 判斷依據是本機 `.dev/test-runs.jsonl`:要有一筆 `tests/test_redlight.py` 的紅燈,且是對著 `redlight.py` 目前 HEAD 內容跑出來的。
- 目前 HEAD 的 `redlight.py` = S4I1 版本(blob `996f151…`)。在這個版本之後,本機只跑過 S3J1 全套(Windows),結果 `tests/test_redlight.py` 全綠:J1 skipped、J2 綠。4i(S4I2)那一輪也是全綠。⇒ 沒有合格紅燈。
- 前幾輪(3h / 3i)都是 Windows 能紅的測試,所以沒碰到這條。本輪 J1 是 POSIX-only red,它的紅只在裁決助手的 Linux 環境,不在本機帳本 —— R3 看不到。
- 權威層 pre-commit 用同一條 R3(訊息末句),所以「人手改 + commit」也會被擋;這不是前哨單獨的問題。

### 選項(要你裁)

| 選項 | 做法 | 代價 |
|---|---|---|
| **A(建議)3j-1b 補一支 Windows 也會紅的測試** | 新增一支 behavior-red,直接呼叫 `_root_is_toplevel`,用 monkeypatch 把 `subprocess.run` 換成回傳 stdout `b"true\n\nsub/\n"`(returncode 0)的替身,斷言結果為 False。這就是 S5i-F1 在解析層的形狀,不需要建出含 LF 的檔名,Windows 上對 S4I1 會紅、對 4j 修法會綠。跑一次全套留下本機紅燈後,4j 即可通過 R3 | 多一個 3j-1b 回合;測試用替身而非真 git,只鎖解析層(端到端仍由 J1 在 POSIX 鎖) |
| B 走既有豁免機制 | 用 `.dev/gate-exemptions.jsonl` 的豁免流程(依 CLAUDE.md:寫入證據檔的批次須裁決者本人核准判準)讓這次改動過 R3 | 依賴豁免;判準是「紅燈在別的平台」,這個判準在 R3 的設計裡沒有先例 |
| C 在 POSIX 環境實作 4j | 由能在 POSIX 跑本 repo 帳本的環境做 4j(J1 在那裡會紅、留下紅燈紀錄) | 本 repo 帳本與證據流程目前都綁在這台 Windows;換環境影響帳本連續性 |

- 建議 A:它讓紅燈留在本機帳本、符合 R3 的原意(先紅後綠),而且補上 S5i-F3 指出的「沒有測試直接鎖住解析」的 Windows 版本。

### 程序紀錄

- 沒有閘門以外的異常;沒有 push / fetch。
- 本回報檔名用實際 UTC 時間(`date -u` = `2026-10-05T184454Z`)。
<!-- 逐字結束 -->

---

## G. 審查重點

<!-- 逐字開始 -->
G1 修正是否封住 S5i-F1：_root_is_toplevel 以 proc.stdout.replace(b"\r\n", b"\n") == b"true\n\n" 整段精確比對；例外 / 非零 returncode / 任何多餘位元組（含 prefix 首位元組為 LF、CR、空白）是否一律 False（fail-closed）。
G2 精確比對的健壯性：git rev-parse --is-inside-work-tree --show-prefix 合併輸出在正常最上層是否恰為 true + LF + 空行 LF（兩個 LF）；在 Windows（可能 \r\n）、不同 git 版本、core.* 設定下是否可能在正常最上層誤回 False（fail-closed 但封死正常 host；若有，須指出並給 git 版本證據）。
G3 不變式未削弱：本輪只改 _root_is_toplevel 一個函式（以 D.2 + E.1 / E.4 驗）；committed_blobs / evidence_policy_facts 的呼叫處、consumer、policy_state、content_hash 及其呼叫鏈、conftest、status.py / install.py / verify_gates.py 皆未改；測試只在檔尾新增（E.2 / E.3 各一個 hunk、無 - 行）。
G4 紅綠時序與 R3：J1 為 POSIX-only red（本機帳本看不到）、第一次 4j 被 R3 擋（F.3）、3j-1b 補 J1b 在本機帳本留下紅燈後 4j 才通過 —— 這條路徑是否符合 R3 原意（先紅後綠、紅燈對著 HEAD 的實作跑出來），而非繞過；J1b 在 S3J1B 為 red、J2 在 S3J1 為 green、三者在 S4J1 為 green（見 F.0 與 F.1 / F.2 原文），不得只看最終全綠。
G5 三支測試是否真的測到宣稱的形狀：J1 的 root = <parent>/"\nsub"、三份未提交副本、經真實 conftest producer、skipif win32 的條件是否正確；J1b 的 monkeypatch 是否替換到 _root_is_toplevel 實際呼叫的 subprocess.run（import 路徑）、是否斷言 args 以 --is-inside-work-tree --show-prefix 結尾、stdout b"true\n\nsub/\n" 是否就是 S5i-F1 的形狀、monkeypatch 是否會外漏到其他測試；J2 四種佈置是否各自獨立成立。
G6 5g / 5h / 5i 的其他結論是否仍成立：本輪改動是否影響 5i 報告 G2 / G5 / G7 / G9 以外的任何結論、5h 的 G1–G9、5g 的 13 題；S5g-F1 / F3 / F4 / F5、S5h-F4 追蹤項狀態是否正確（仍未 machine-enforced）；S5i-F3 是否確由 J2 / J1b 機器鎖關閉。
G7 殘餘措辭與程式一致：4j 證據報告第 7 節第 4 點（S5i-F2 補準版）是否與 _root_is_toplevel 的實際行為一致、沒有宣稱已拒絕或已支援任何未測的佈局；且該措辭是否與已提交的 S5i-F2 finding（C.2）相符 —— 這是對程序偏差 (b) 的獨立核對：最終措辭的來源須能由已提交文件支撐，不依賴對話紀錄。
G8 跨平台：\r\n 正規化是否足夠；是否存在 git 版本或平台讓最上層輸出含 \r 單獨出現或尾端多一個 LF；Windows 本機 J1 skip 是否使 Windows 端對 LF 開頭子目錄完全沒有端到端證據（若是，說明 J1b 是否足以補位）。
G9 總問題（增量版）：在 TARGET 上，是否仍存在任何路徑，讓 root 的 canonical policy 沒有提交在「Git 對該 root 實際解析出的 repository / HEAD」中，卻能取得 file_coverage == "true"（判準同 5h / 5i G9：工作樹所用物件與 HEAD 所證明物件的 identity 錯位）；請在 5h 第 4 節總表 18 項 + 5i 的 LF 反例基礎上重新檢查，並主動構造新反例（含：prefix 只含 \r、prefix 含 NUL、子目錄名為空白、GIT_DIR / GIT_WORK_TREE / core.worktree 重新對應、linked worktree、submodule），找不到也要列出檢查過的路徑。
G10 程序偏差對證據完整性：(a) 並行送出的 5 條唯讀檢查、(b) 讀取對話紀錄檔 —— 是否有任何證據（帳本 sha、blob、run 紀錄、報告內容）因此不可信；若無，明確寫「不影響」並附依據。
判定規則：結論只能 PASS 或 FAIL。FAIL 的門檻是 G9 找到同級漏洞、或 G1 / G3 / G4 任一不成立；G2 / G5 / G7 / G8 / G10 的問題若不構成同級漏洞，列為 finding 與追蹤項，不單獨導致 FAIL。
<!-- 逐字結束 -->

---

## H. 已知殘餘與追蹤項

出處:F.1 的「殘餘與未證明」一節,即 REVIEW_HEAD 的 `docs/audits/2026-10-05-m1a-station4j-fix.md` 第 204–211 行。

<!-- 逐字開始 -->
### 7. 殘餘與未證明(目前尚未 machine-enforced)

1. 沿用 4i 證據報告(`docs/audits/2026-10-05-m1a-station4i-fix.md`)第 7 節全部項目(含其沿用的 4h 第 7 節與 4g 第 8 節),不擴張;唯 4i 第 7 節第 3 點的殘餘措辭由本節第 4 點取代。
2. 5g 追蹤項:S5g-F1(下一張票優先)、S5g-F3、S5g-F4、S5g-F5;5h 追蹤項:S5h-F4(併入 S5g-F1 類的 operator / status 追蹤項)。S5h-F3 已於 4i 補準措辭(本輪再由第 4 點取代)。
3. S5i-F3 已由機器鎖處理:J2(直接呼叫 `_root_is_toplevel` 的四種佈置)與 J1b(解析層替身,鎖住「多餘位元組 ⇒ False」),不另列追蹤項。新增流程教訓追蹤項「R3 與 POSIX-only 紅燈」(R3 只認本機帳本紅燈;規劃平台限定紅燈時須同時規劃本機可紅的對應案例;見票 145「相關」)。
4. 依 S5i-F2 補準的殘餘措辭(照錄,取代 4i 版本中的對應段落):
   「本輪檢查的語意是 git rev-parse --is-inside-work-tree --show-prefix 的 stdout（\r\n 正規化後）完整等於 b"true\n\n"，即 Git 對該 root 回報「在工作樹內」且 prefix 為空且沒有任何其他位元組。在預設環境（未設 GIT_DIR / GIT_WORK_TREE / core.worktree）下明確不支援（⇒ unknown）：monorepo 中非最上層的普通子目錄（H1；含 POSIX 上名稱以 LF 開頭者，J1 / J1b）、位於 gitdir 或 bare repository 內的 root（I1 / I2）。會被接受但本輪未納入 acceptance、屬未證明：巢狀獨立 Git repo、submodule、linked worktree、.git 為檔案且 gitdir 指向他處，以及 GIT_DIR / GIT_WORK_TREE / core.worktree 等重新對應佈局（含 Git 因此把 gitdir 本身視為工作樹的情形）。上述佈局若 Git 對該 root 實際回報上述 stdout，即會被本檢查接受；其 HEAD 與工作樹是否符合既定 identity invariant，本輪未完整 acceptance，不得宣稱已拒絕或已支援。」
5. 本機只驗 Windows;J1(LF 開頭子目錄的端到端)在 Windows 不可建立,未在本機執行。
<!-- 逐字結束 -->

**註**:上列追蹤項目前尚未 machine-enforced。
