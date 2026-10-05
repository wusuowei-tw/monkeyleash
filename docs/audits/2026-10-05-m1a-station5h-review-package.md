# M1-a Station 5h 增量獨立審查包(票 145)

**審查對象(TARGET,本輪最後一個程式 commit)**:`ea6aba6452668982fee56f7a2f0faf2cd720ca6d`
**審查 HEAD(REVIEW_HEAD;review baseline)**:`2f496b9d0a71d88995b2338c6b4440d693c9a879`
**審查範圍**:只審 3h / 4h 增量(TARGET_G → TARGET)。5g 已審過 TARGET_G 之前的內容。

本包只是材料,不含任何審查結論。所有逐字段落皆以 `<!-- 逐字開始 -->` / `<!-- 逐字結束 -->` 標出邊界,
邊界之間的文字與標示的出處逐位元組相同(換行一律 LF)。
D 段與 E 段的逐字範圍是邊界內 ```` ``` ```` 圍籬**之間**的全部行(圍籬本身不屬於出處內容)。
E 段為 `git diff` / `git show` 原樣,**未去除行尾空白**(diff 的空白 context 行是單一空格)。
B、C、F、H 段的出處本身含有 ```` ``` ```` 圍籬或 markdown 標題;這些段不另加圍籬,邊界以該段標示的出處行號為準。

---

## A. 身分與規則

### A.1 身分

| 代號 | 完整 SHA | 說明 |
|---|---|---|
| **BASE_G** | `b5db3734f6795d8a371e4f58b172e0a8ffb066eb` | 5g 審查 HEAD(S4G5) |
| **TARGET_G** | `8e7775526e462d984abb0992ed74c1e1aa3648dd` | 5g 審過的最後程式 commit(S4G1C) |
| S5g-0 | `5e096acb899b3370f16018199627784af71b788e` | 5g 審查包 |
| S5g-1 | `3a9200c03bb8493ab5a789d4c4157a7b38392e79` | 5g 審查報告入庫與 3h 裁決 |
| S3H1 | `7621e3ce8604ab72ab2f3fb3257cb1181b8a126e` | H1 / H2 紅燈 |
| S3H2 | `66140896d03f32c4df73be01b2aaeb48353e0510` | 3h 紅燈證據(docs) |
| **TARGET**(S4H1) | `ea6aba6452668982fee56f7a2f0faf2cd720ca6d` | 本輪最後程式 commit —— **審查對象** |
| S4H3 | `569b57d2dd048d3317d51970757f3b41a7f28891` | 4h 本機驗收證據(docs) |
| **REVIEW_HEAD**(S4H4) | `2f496b9d0a71d88995b2338c6b4440d693c9a879` | POSIX 外部驗收記錄、4h 升級為 PASS / COMPLETED(docs);review baseline |

- 本包所在的 commit(S5h-0)是 REVIEW_HEAD **之後**才建立的 docs-only commit;本包寫不進自己的 SHA,由裁決者交付審查時另附。S5h-0 **不屬於審查對象**。
- **CODE_FILES**(`git diff --name-only <TARGET_G>..<TARGET>` 中所有非 docs/ 的檔,2 個):`.claude/hooks/redlight.py` `tests/test_redlight.py`。
- TARGET 之後到 REVIEW_HEAD 只改 docs/。

建包時核對(原文輸出;各自單獨執行,全部以完整 SHA 為錨點):

```
$ git merge-base --is-ancestor b5db3734f6795d8a371e4f58b172e0a8ffb066eb 2f496b9d0a71d88995b2338c6b4440d693c9a879
(無輸出;exit 0)
$ git rev-list --count b5db3734f6795d8a371e4f58b172e0a8ffb066eb..2f496b9d0a71d88995b2338c6b4440d693c9a879
7
$ git diff --name-only ea6aba6452668982fee56f7a2f0faf2cd720ca6d..2f496b9d0a71d88995b2338c6b4440d693c9a879
docs/audits/2026-10-05-m1a-station4h-fix.md
docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
```

`git diff --name-only <TARGET_G>..<TARGET>` 全文見 D.2。

### A.2 審查者規則

1. **身分**:5g 審查 session(亦執行了 S5g-1 / 3h / 4h)不得擔任 5h 審查者;5h 審查須在全新對話進行。
2. **唯讀**:不改任何檔案、不 commit、不推、不改 `.dev/pipeline.json`。審查報告只寫到 `.scratch/m1a-s5h/review-report.md`,不寫其他位置。
3. **禁止 pytest**(含 `--collect-only`、`--version`)、`verify_gates.py` 與 `status.py`。帳本(`.dev/test-runs.jsonl`、`.dev/test-sessions.jsonl`)會被任何 pytest 執行追加,審查不得污染證據。需要驗證行為時,讀程式碼做紙上推演;必須實跑才能確定者,寫成「需要重現」並描述最小重現方式。
4. **查詢一律綁定 A.1 的完整 SHA**;不以 `HEAD`、`HEAD~n`、遠端追蹤分支、本地分支名、短 SHA 或工作樹當下狀態為錨點。範例:

```
git show ea6aba6452668982fee56f7a2f0faf2cd720ca6d:<路徑>
git diff 8e7775526e462d984abb0992ed74c1e1aa3648dd..ea6aba6452668982fee56f7a2f0faf2cd720ca6d -- <路徑>
git log --oneline b5db3734f6795d8a371e4f58b172e0a8ffb066eb..2f496b9d0a71d88995b2338c6b4440d693c9a879
git show 2f496b9d0a71d88995b2338c6b4440d693c9a879:docs/audits/2026-10-05-m1a-station4h-fix.md
```

5. **逐字段的邊界以各段標示的出處行號為準**(不以段內標題或圍籬判斷)。
6. 可用 Read / Grep 讀本機已安裝的 pytest / pluggy 原始碼與 git 文件;引用只寫 `_pytest/<檔名>:<行號>` 等相對形式,不寫本機絕對路徑。
7. **照錄任何系統訊息、錯誤訊息或路徑前,先把本機使用者名稱遮成 `<user>`。**
8. 被任何閘門(R1–R9、pre-commit、洩漏偵測)擋下:停手回報,不換工具、不繞過。
9. **結論只能是 `PASS` 或 `FAIL`**;finding 須標嚴重度,並附 `<TARGET>:<路徑>:<行號>` 形式的證據(以 TARGET 為準)。沒有檔名與行號證據的發現不計入判定。
10. **範圍**:5g 已審過 TARGET_G 之前的內容,本輪只審增量;但若增量使 5g 的任何結論失效,須指出。
11. G 段 G1–G9 每一題都必須回答(「無問題」也要附證據);不能回答的,寫明「無法判定」與原因,不得略過。
12. 不得用 python -c、heredoc 或把程式碼放進指令字串。

---

## B. 裁決與背景(逐字)

出處一律為 `2f496b9d0a71d88995b2338c6b4440d693c9a879:docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md`(以下稱「REVIEW_HEAD 的票 145」)。

### B.1 〈五十三〉Station 5g 獨立審查與 Station 3h 裁決

行號來源:REVIEW_HEAD 的票 145 第 2711–2748 行

<!-- 逐字開始 -->
## 五十三、Station 5g 獨立審查（審查者 PASS；依 Jeff 裁決 FAIL）與 Station 3h 裁決（2026-10-04，Jeff）

### 53.1 審查報告

- 路徑 `docs/audits/2026-10-04-m1a-station5g-review.md`;raw = repo 副本(與審查者原檔 `.scratch/m1a-s5g/review-report.md` 以 `cmp` 逐位元組相同,無任何改動);
  sha256 `8399be264fafa82d62bb3294762d17835b4429850aca68c57c545883adfd0a49`;28223 bytes。
- 審查對象 TARGET `8e7775526e462d984abb0992ed74c1e1aa3648dd`;審查包所在 commit S5g-0 `5e096acb899b3370f16018199627784af71b788e`。
- **審查者原始判決:PASS**(blocker 0、major 0、minor 2、nit 3)。
- Findings(報告第 2 節;一行摘要,不改寫結論):
  - S5g-F1【minor;G7(+G8)】`policy_state` 不查 addopts 鎖步;框架 pyproject 範本(addopts 帶 `--strict-markers`)+ policy 範本(`committed_overrides: []`)原樣採用 ⇒ status 顯示「有效」但每次固定全套都是 unknown,紅燈永遠不退且無訊號(fail-closed)。
  - S5g-F2【minor;G13 / G1 / G6;需要重現】`_ROOT` 不是 git toplevel 時,`rev-parse HEAD:<path>` 以 tree 根為基準、`hash-object <path>` 以 cwd 為基準;toplevel 已提交同內容 policy、子目錄放未提交副本 ⇒ 可得 `"true"`(內容等於某個已提交 blob;完整性成立,位置不成立)。
  - S5g-F3【nit;G3】pytest 9 原生 `[tool.pytest]`(無 `ini_options`)⇒ `_committed_addopts` 回 None ⇒ 永遠 unknown;status 仍顯示「有效」;fail-closed,H 段殘餘清單未列。
  - S5g-F4【nit;G12;需要重現】`.gitattributes` 的 clean filter 可讓 `pyproject.toml` / `tests/conftest.py` 工作樹 ≠ HEAD 但 `hash-object` 相等 ⇒ (xi) 誤判一致;policy 本身不受影響;BASE 已存在。
  - S5g-F5【nit;G9】正二不成立時負一~負三仍印「成立 ✓」;負情境的判別力完全來自同次執行中正二成立的差分,程式沒有把這個耦合寫進輸出。

### 53.2 裁決助手外部重現(隔離 Linux 環境;Python 3.11 + pytest 9.1.1;非獨立審查 finding;非本 repo 帳本證據)

來源:Jeff 的 Station 5g-1 指令,照錄。

- 事實層：建 git repo R，於 R 最上層提交合法 policy、pyproject.toml、tests/conftest.py；於 R/sub 放三份位元組相同、從未提交的副本（git ls-files 在 sub 下為空）。以 TARGET 的 redlight 讀 R/sub：evidence_policy_facts 的 head == worktree 成立、committed_addopts 取得、committed_blobs 兩檔 head == worktree、policy_state 顯示「有效」。
- 端到端：以 tests/test_redlight.py 的既有 helper（_g_default_root、_g_coverage）在 TARGET 上模擬固定全套，root = parent/sub ⇒ file_coverage == "true"（原型測試失敗於 assert got != "true"）。S5g-F2 為真，且可取得 true authority。
- 修法原型：redlight 新增「root 必須是 git 最上層」檢查（git -C <root> rev-parse --show-prefix 為空；不是 ⇒ evidence_policy_facts 與 committed_blobs 全記 None）。套用後上述原型轉為非 true；「root 為最上層、policy 正常提交」原型仍為 true；evidence 相關 5 檔共 279 支全過。

### 53.3 裁決(照錄)

1. Station 5g：獨立審查者判決 PASS（blocker 0、major 0、minor 2、nit 3）；Jeff acceptance = FAIL。理由：S5g-F2 違反〈四十六〉46.4 第 6 點與 I-3 —— canonical policy 必須是宿主 evidence root 對應路徑上、已提交的 HEAD blob；未提交 ⇒ unknown。現行 git rev-parse HEAD:<path> 以 git 最上層為基準、git hash-object <path> 以 root 為基準；root 不是 git 最上層時，被驗證的 HEAD 物件與實際使用的工作樹物件不是同一個邏輯路徑（identity 錯位），內容相同即可取得 true。
2. 修法方向：evidence root 必須就是 git 最上層（git -C <root> rev-parse --show-prefix 為空；與「resolved root == git rev-parse --show-toplevel」等價，但不需比對路徑字串）；不是 ⇒ policy 事實與 (xi) 的 blob 事實皆記 None ⇒ unknown ⇒ 不得退紅。框架目前明確只支援「一個 host evidence root = 一個 Git 最上層」；monorepo 子專案作為 evidence root 屬另案設計，不在本票。
3. Station 3h 紅燈至少兩支（皆經真實 conftest producer、真 git repo）：
   H1 behavior-red：git 最上層已提交合法 policy、pyproject.toml、tests/conftest.py；root = <最上層>/sub，三份位元組相同的副本只在工作樹、從未提交 ⇒ file_coverage 不得為 "true"。
   H2 regression-lock：root 本身就是 git 最上層，policy 正常提交、worktree = HEAD ⇒ 仍為 "true"。
   巢狀獨立 repo 的情境不在本輪。
4. S5g-F1、S5g-F3、S5g-F4、S5g-F5 列追蹤項（目前尚未 machine-enforced），不阻擋本輪；S5g-F1 列下一張票優先，須以機制處理 status 訊號（例：status 多一狀態，重用 verdict 的鎖步），不只改文字。
5. 流程：5g-1 記錄 → Jeff 切 tickets → 3h 紅燈 → Jeff 切 implement → 4h 最小修正（含 Windows 全套、本機 clean-room、裁決助手 POSIX）→ 5h 獨立審查（只審 3h/4h 增量）→ Station 6。

### 53.4 commit

- S5g-1(本節與審查報告入庫)`3a9200c03bb8493ab5a789d4c4157a7b38392e79`。
  (F-036:本行原文為「S5g-1(本節與審查報告入庫)於下一次提交回填。」;2026-10-04 於 S3H2 回填。)
<!-- 逐字結束 -->

### B.2 〈五十四〉Station 3h 紅燈證據

行號來源:REVIEW_HEAD 的票 145 第 2752–2770 行

<!-- 逐字開始 -->
## 五十四、Station 3h 紅燈證據

- Jeff 裁決(2026-10-04):S5g-1 = accepted;Station 3h plan = APPROVED。
- 報告:`docs/audits/2026-10-04-m1a-station3h-redlight.md`。
- S3H1 `7621e3ce8604ab72ab2f3fb3257cb1181b8a126e`:`tests/test_redlight.py` 檔尾一個 hunk `@@ -2534,0 +2535,42 @@`,只有 + 行;新增 `class TestEvidenceRootIsGitToplevel`,既有 helper 只呼叫、不修改。commit 前只跑 py_compile。
- 新增 2 支(完整 nodeid):
  - H1 behavior-red(在 S5g-1 上必須失敗):`tests/test_redlight.py::TestEvidenceRootIsGitToplevel::test_h3_a_parent_committed_policy_does_not_authorize_a_subdirectory_root`
  - H2 regression-lock(在 S5g-1 上必須通過):`tests/test_redlight.py::TestEvidenceRootIsGitToplevel::test_h3_a_git_toplevel_root_with_a_committed_policy_is_full_coverage`
- 紅燈全套(在 S3H1 上只跑一次;外來 3 檔已 stash,跑前跑後 `git status --porcelain` 皆無輸出):exit 1;
  摘要行原文 `1 failed, 2095 passed, 3 skipped, 3 xfailed in 409.36s (0:06:49)`(collected 2102)。
  唯一的 FAILED 為 H1,失敗行 `tests\test_redlight.py:2567: AssertionError`(`assert 'true' != 'true'`);H2 在 2095 passed 之內。
- 帳本只追加:兩本前段 sha256 = Step 0 基準(`9fa98cc7…` / `27cccd2c…`);test-runs 3015 → 3062 行(+47)、test-sessions 27 → 28 行(+1)。
  跑後全檔記為 B15:test-runs 822547 bytes、`49fc32bc88ad7eb93840e070154953980fa40122388c2fce49645b411a254789`;
  test-sessions 12909484 bytes、`0539883a5548a9032ed0877aab4614bdde6fd748103a3db2524de99e9c589674`。
- 程序紀錄(Jeff 程序註記,照錄要點):S5g-1 由 5g 審查 session 執行(審查報告在 S5g-1 前已完成,RR = `8399be264fafa82d62bb3294762d17835b4429850aca68c57c545883adfd0a49`),
  不影響已凍結的 5g 審查結果,但該 session 不得擔任 5h 審查者;S5g-1 回報檔名的時間戳與實際提交時間不符,之後 `.dev/reports/` 檔名一律用實際 UTC 時間。
  本輪 3h 亦由同一 session 執行。
- commit:S3H1 `7621e3ce8604ab72ab2f3fb3257cb1181b8a126e`;S3H2(本節與證據報告)`66140896d03f32c4df73be01b2aaeb48353e0510`。
  (F-036:本行原文為「S3H2(本節與證據報告)於下一次提交回填。」;2026-10-05 於 S4H3 回填。)
<!-- 逐字結束 -->

### B.3 〈五十五〉Station 4h 修正

行號來源:REVIEW_HEAD 的票 145 第 2774–2819 行

<!-- 逐字開始 -->
## 五十五、Station 4h 修正

### 55.1 裁決(照錄要點;Jeff,2026-10-05)

- Station 3h = PASS / ACCEPTED;Station 4h plan = APPROVED;H1 / H2 不准修改;最小修正只動 redlight.py。
- 三段式:S4H1 實作 → S4H2 本機驗收 → S4H3 docs-only(只能宣稱本機驗收通過;待 POSIX 外部驗收)。POSIX 由裁決助手執行,通過後另以 S4H4 升級。

### 55.2 證據

- 報告:`docs/audits/2026-10-05-m1a-station4h-fix.md`。
- S4H1 `ea6aba6452668982fee56f7a2f0faf2cd720ca6d`:只改 `.claude/hooks/redlight.py`(+25 行,0 刪除)。
  - `:726` 新增 `_root_is_toplevel(root)`(`git -C <root> rev-parse --show-prefix` 為空才 True;失敗 ⇒ False);
  - `:752` / `:755` `committed_blobs`:不是最上層 ⇒ 每個路徑記 `{"worktree": None, "head": None}`;
  - `:868` `evidence_policy_facts`:不是最上層 ⇒ 全 None;
  - 兩個函式 docstring 補 I-3 位置不變式。
  - 未改 consumer、`policy_state` 判定字串、conftest、status / install / verify_gates、任何測試;`content_hash` 未動。
  - 兩刀,每刀後 status.py 探針;皆無「redlight.py 無 run 事實讀取」。
- S4H2 本機固定全套(S4H1 上只跑一次;外來 3 檔已 stash):exit 0;`2096 passed, 3 skipped, 3 xfailed in 380.00s (0:06:19)`(collected 2102、0 failed)。H1 由紅轉綠,H2 維持綠。
- 帳本只追加:前段 sha256 = B15;test-runs 3062 → 3109(+47)、test-sessions 28 → 29(+1)。
- status:`evidence policy: 有效`;`tests red under ticket 145: (無)`;run 事實未知 0;`tests/test_redlight.py` 在 green。
- 淨室(verify_gates;同一次執行):R1–R9 各擋下一次、權威層偵測三項成立、淨室框架測試 `1946 passed, 7 skipped, 3 xfailed`;兩正三負全部成立,正二 `file_coverage=true`、`green=tests/test_evidence_probe.py`。
  本 repo 兩本帳本前後 bytes 與 sha256 都等於 V0(test-runs 834066 / `5f0ffa92…`;test-sessions 13647838 / `74757aa6…`)。
- 裁決助手 Linux 預演(來源:Jeff 的 Station 4h 指令;隔離環境;非本 repo 帳本證據):H1 紅轉綠、H2 維持綠;evidence 相關 5 檔共 279 支全過;verify_gates 兩正三負全部成立、正二 file_coverage=true。
- 殘餘與未證明(目前尚未 machine-enforced):沿用 4g 證據報告第 8 節 + S5g-F1 / F3 / F4 / F5 追蹤項;本輪新增(照錄):
  「本輪檢查的語意是 git rev-parse --show-prefix 為空，即 root 必須是 Git 認定的該 repository 最上層。monorepo 中、非 Git 最上層的普通子專案，本輪明確不支援作為 evidence root（H1 鎖住）。巢狀獨立 Git repo / submodule 若自身被 Git 視為最上層，--show-prefix 同樣為空、會被接受；其行為本輪未納入 acceptance，屬未證明範圍，不得宣稱已拒絕或已支援。」
- commit:S4H1 `ea6aba6452668982fee56f7a2f0faf2cd720ca6d`;S4H3(本節與證據報告)`569b57d2dd048d3317d51970757f3b41a7f28891`。
  (F-036:本行原文為「S4H3(本節與證據報告)於下一次提交回填。」;2026-10-05 於 S4H4 回填。)
  - S4H4(POSIX 驗收記錄與狀態升級)於下一次提交回填。

### 55.3 POSIX 外部 clean-room 驗收

> **舊文字(F-036,保留不刪)**:本節原文為 ~~`待執行(裁決助手)。`~~;2026-10-05 S4H4 依 Jeff 裁決改為下方照錄段落。
> Jeff 裁決(2026-10-05):Station 4h 本機驗收(S4H2,見 S4H3 `569b57d2dd048d3317d51970757f3b41a7f28891`)與裁決助手 POSIX 外部驗收皆 PASS ⇒ Station 4h = PASS / COMPLETED;〈十〉3h 列依前裁改為 PASS / ACCEPTED(選 A);下一站 5h 獨立審查(只審 3h/4h 增量;須開全新對話)。

POSIX 外部 clean-room 驗收（裁決助手；隔離環境；非本 repo 帳本證據）——2026-10-05 約 09:45 ET
- 環境：Linux，Python 3.11.16，pytest 9.1.1，anyio 4.15.0。
- 受測樹：4g POSIX 驗收所用的樹（BASE de36ebcbab284ef11064a9943b5191750482dd93 + S4G3 時點 12 檔）再覆蓋 S3H1 的 tests/test_redlight.py 與 S4H1 ea6aba6452668982fee56f7a2f0faf2cd720ca6d 的 .claude/hooks/redlight.py 原檔（CRLF→LF）。
- 修正前（S3H1 tests + 4g 程式）：H1 失敗於 got == "true"、H2 通過，與 Windows 3h 一致。
- 修正後：verify_gates.py R1–R9 各擋下一次；權威層偵測三項成立；淨室框架測試 0 failed；evidence policy 兩正三負全部成立：
    正一 未初始化 成立（35 個框架測試檔皆 unknown；evidence policy: 未初始化）
    正二 已初始化且相符 成立（rc 1→0；file_coverage=true；green=tests/test_evidence_probe.py；evidence policy: 有效）
    負一 policy / 環境不符 成立（file_coverage=unknown；紅仍在）
    負二 HEAD 有、工作樹不同 成立（file_coverage=unknown；evidence policy: 工作樹與 HEAD 不同）
    負三 工作樹有、HEAD 沒有 成立（file_coverage=unknown；evidence policy: 未提交）
- 宿主固定全套（Linux）：collected 2102；2086 passed、13 failed、3 xfailed。13 支與 4g POSIX 驗收及 de36ebc 基準在同一沙盒的失敗集合完全相同（tests/test_gate.py::TestAuthorityLayerIsWired::test_this_repo_itself_is_wired 與 tests/test_known_items_regression.py 的 12 支）⇒ 沙盒環境因素（推測：clone 未設 hooksPath、缺本機私有資料），與 3h/4h 無關。evidence 相關 5 檔全過。
- 結論：POSIX 外部 clean-room 驗收 PASS。
<!-- 逐字結束 -->

---

## C. 5g 審查報告中與 S5g-F2 相關的段落(逐字)

出處一律為 `2f496b9d0a71d88995b2338c6b4440d693c9a879:docs/audits/2026-10-04-m1a-station5g-review.md`(以下稱「5g 審查報告」)。

### C.1 Findings 表的表頭與 S5g-F2 列

行號來源:5g 審查報告第 69–70 行(表頭)

<!-- 逐字開始 -->
| 編號 | 嚴重度 | 對應 G 題 | TARGET 檔名:行號 | 具體失敗情境(輸入 → 錯誤結果) | 依據 | 需要重現 |
|---|---|---|---|---|---|---|
<!-- 逐字結束 -->

行號來源:5g 審查報告第 72 行(S5g-F2 列)

<!-- 逐字開始 -->
| S5g-F2 | minor | G13 / G1 / G6 | `.claude/hooks/redlight.py:845`(`rev-parse HEAD:<POLICY_FILE>`)、`:849`(`hash-object <POLICY_FILE>`)、`:739-740`(`committed_blobs` 同一手法)、`:805`(`cat-file blob HEAD:<config_file>`);`tests/conftest.py:410-412`(以 `_ROOT` 呼叫) | `_ROOT`(conftest 的上兩層)**不是** git toplevel 時(例:專案是某個大 repo 的子目錄、沒有自己的 `.git`):`git -C <root> rev-parse HEAD:<path>` 的 `<path>` 是**相對 tree 根**,而 `git -C <root> hash-object <path>` 是**相對 cwd**。若 toplevel 已提交一份 `.agents/evidence-policy.json`、`pyproject.toml`、`tests/conftest.py`,而子目錄內有**內容相同但從未提交於該路徑**的副本 → head == worktree 成立 → 可得 `"true"`,儘管子目錄自己的 canonical path 上沒有已提交的 policy。內容仍等於某個已提交 blob(完整性成立,位置不成立) | git 的 `<rev>:<path>` 語意(不以 `./` 開頭即相對 tree 根)與 `hash-object` 以 cwd 解析檔名;`install.main` 對無 `.git` 的目標會 `git init`(`.claude/portable/install.py:541-544`),所以**安裝器路徑**不會產生此佈局,只有手動佈局會 | **是**。最小重現:建 repo `R`,於 `R/` 提交合法 policy、pyproject、tests/conftest.py;在 `R/sub/` 放三份位元組相同的未追蹤副本與一支測試;於 `R/sub` 跑固定指令(或直接以 `redlight.evidence_policy_facts("R/sub")` / `committed_blobs("R/sub")` 讀事實)看 head 與 worktree 是否相等。修法方向:以 `HEAD:./<path>` 或先 `rev-parse --show-prefix` / 要求 `_ROOT == --show-toplevel` |
<!-- 逐字結束 -->

### C.2 G1 結論

行號來源:5g 審查報告第 81–87 行

<!-- 逐字開始 -->
### G1 I-3 bootstrap —— **成立**

- 內容只來自 HEAD blob:`redlight.py:845` 取 `HEAD:<POLICY_FILE>` 的 blob sha;`:849` `hash-object` 取工作樹 blob;`:851-852` 不等即返回;`:853` `cat-file blob <head sha>`;`:856` `json.loads` 只解析那份 bytes。工作樹檔在 `:849` 之後不再出現。
- 任一步失敗 ⇒ 欄位 None:`:842-843` 預設全 None;`:846-847`、`:854-855`、`:857-858` 提前返回;`:864-865` 吞例外。consumer `_effective_policy`(`:955-956`)要求 `head` 為非空字串且 `worktree == head`;`policy_document_problems(None)` ⇒ 格式問題(`:881-882`)⇒ None(`:959-960`)⇒ verdict `unknown`(`:1074-1076`)。
- 唯一 Python 層讀檔是 `policy_state` 的 `os.path.exists`(`:920`),只用來區分「未提交 / 未初始化」兩個狀態字,不進 verdict。
- 迴歸鎖 `tests/test_redlight.py:2364-2389`(#13)以攔截 `open` / `io.open` 驗證。
- 例外形狀見 S5g-F2(root ≠ toplevel)。
<!-- 逐字結束 -->

### C.3 G6 結論

行號來源:5g 審查報告第 127–132 行

<!-- 逐字開始 -->
### G6 `committed_blobs` 逐路徑 —— **成立**

- `redlight.py:735-746`:每個路徑各一次 `hash-object` 與一次 `rev-parse`,各自 try;缺一檔只影響該項。
- 預設路徑 `BLOB_FILES = FRAMEWORK_CONFIG_FILES + (ROOT_CONFTEST,)`(`:497`);policy 的 `config_file` 必屬 `FRAMEWORK_CONFIG_FILES`(`:901-902`、`:1092`),所以必有記錄。
- verdict `:1095-1098` 同時檢查 `config_file` 與 `ROOT_CONFTEST`,工作樹 blob 須非空且等於 HEAD blob。
- 例外形狀見 S5g-F2(root ≠ toplevel 時兩個 git 指令的路徑基準不同)。
<!-- 逐字結束 -->

### C.4 G13 結論

行號來源:5g 審查報告第 199–201 行

<!-- 逐字開始 -->
### G13 總問題 —— **成立(未找到反例;最接近的形狀判 minor)**

見第 4 節。
<!-- 逐字結束 -->

### C.5 第 4 節反例清單的表頭與第 24 項

行號來源:5g 審查報告第 209–210 行(表頭)

<!-- 逐字開始 -->
| # | 嘗試路徑 | 結果 | 擋在哪 |
|---|---|---|---|
<!-- 逐字結束 -->

行號來源:5g 審查報告第 234 行(第 24 項)

<!-- 逐字開始 -->
| 24 | `_ROOT` 不是 git toplevel,toplevel 已提交同內容 policy、子目錄放未提交副本 | **可得 true**,但 policy 內容等於某個已提交 blob | S5g-F2(minor;需要重現;安裝器路徑不會產生此佈局) |
<!-- 逐字結束 -->

---

## D. 本輪 commit 與檔案範圍

### D.1 `git log --oneline b5db3734f6795d8a371e4f58b172e0a8ffb066eb..2f496b9d0a71d88995b2338c6b4440d693c9a879`(7 筆,與 A.1 的 S5g-0…S4H4 逐一對應)

<!-- 逐字開始 -->
```
2f496b9 docs(145): M1-a Station 4h-4 —— POSIX 外部 clean-room 驗收 PASS;Station 4h = PASS / COMPLETED
569b57d docs(145): M1-a Station 4h-3 —— 本機固定全套與 clean-room 驗收證據;待 POSIX 外部驗收
ea6aba6 fix(145): M1-a Station 4h-1 —— evidence root 必須是 Git 最上層(S5g-F2)
6614089 docs(145): M1-a Station 3h-2 —— 紅燈證據(H1 紅、H2 綠;S5g-F2)
7621e3c test(145): M1-a Station 3h-1 —— evidence root 必須是 Git 最上層的紅燈(S5g-F2;2 支)
3a9200c docs(145): M1-a Station 5g-1 —— 獨立審查入庫(審查者 PASS;依 Jeff 裁決 FAIL:S5g-F2)與 Station 3h 裁決
5e096ac docs(145): M1-a Station 5g-0 —— 獨立審查包
```
<!-- 逐字結束 -->

### D.2 `git diff --name-only 8e7775526e462d984abb0992ed74c1e1aa3648dd..ea6aba6452668982fee56f7a2f0faf2cd720ca6d`(NAMEONLY_FULL;TARGET_G..TARGET 全範圍)

這是「CODE_FILES 以外的非 docs 檔(conftest、status.py、install.py、verify_gates.py 等)都沒變」的證據;E.1 / E.3 只餵了 CODE_FILES,不足以證明這一點。

<!-- 逐字開始 -->
```
.claude/hooks/redlight.py
docs/audits/2026-10-04-m1a-station3h-redlight.md
docs/audits/2026-10-04-m1a-station4g-fix.md
docs/audits/2026-10-04-m1a-station5g-review-package.md
docs/audits/2026-10-04-m1a-station5g-review.md
docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
tests/test_redlight.py
```
<!-- 逐字結束 -->

---

## E. 程式差異(原樣)

### E.1 `git diff 8e7775526e462d984abb0992ed74c1e1aa3648dd..ea6aba6452668982fee56f7a2f0faf2cd720ca6d -- .claude/hooks/redlight.py tests/test_redlight.py`(本輪全部程式與測試改動)

<!-- 逐字開始 -->
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
diff --git a/tests/test_redlight.py b/tests/test_redlight.py
index 6f444db..26da0b5 100644
--- a/tests/test_redlight.py
+++ b/tests/test_redlight.py
@@ -2532,3 +2532,45 @@ class TestEvidencePolicyNoOverride:
                            usepdb=False)
         got = _g_coverage(root, monkeypatch, option=option)
         assert got != "true", got
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# 票 145 Station 3h 補紅燈 —— S5g-F2:evidence root 必須就是 Git 最上層(〈五十三〉53.3 裁決 2、3)
+#
+# 成因:`git -C <root> rev-parse HEAD:<path>` 的 `<path>` 以 **Git 最上層**(tree 根)為基準,
+# `git -C <root> hash-object <path>` 以 **root(cwd)** 為基準。root 不是最上層時,被驗證的 HEAD 物件與
+# 實際使用的工作樹物件不是同一個邏輯路徑(identity 錯位),內容相同即可取得 `"true"`。
+# 框架目前只支援「一個 host evidence root = 一個 Git 最上層」;monorepo 子專案作為 evidence root 屬另案,
+# 巢狀獨立 repo 的情境不在本輪。
+# 既有 helper(`_g_default_root` / `_g_coverage` / `_G_POLICY_FILE`)只呼叫、不修改。
+# ─────────────────────────────────────────────────────────────────────────────
+
+class TestEvidenceRootIsGitToplevel:
+
+    def test_h3_a_parent_committed_policy_does_not_authorize_a_subdirectory_root(self, tmp_path, monkeypatch):
+        """H1。分類:behavior-red(在 S5g-1 上必須失敗)。
+
+        Git 最上層 `parent` 已提交合法 policy、`pyproject.toml`、`tests/conftest.py`;root = `parent/sub`,
+        三份位元組相同的副本只在工作樹、從未提交於 `sub/` 底下。`sub` 的 canonical policy 從未提交
+        ⇒ 不得為 `"true"`(〈四十六〉46.4 第 6 點、I-3:canonical policy 必須是 evidence root 對應路徑上、
+        已提交的 HEAD blob)。
+        S5g-1 上失敗的原因:`git rev-parse HEAD:<path>` 以最上層為基準、`git hash-object <path>` 以 root 為基準
+        ⇒ 兩者指向 `parent/<path>` 與 `sub/<path>`,內容相同即 head == worktree ⇒ identity 錯位即可取得 `"true"`。
+        """
+        parent = _g_default_root(tmp_path / "parent")
+        sub = parent / "sub"
+        for rel in (_G_POLICY_FILE, "pyproject.toml", "tests/conftest.py"):
+            dst = sub / rel
+            dst.parent.mkdir(parents=True, exist_ok=True)
+            dst.write_bytes((parent / rel).read_bytes())
+        got = _g_coverage(sub, monkeypatch)
+        assert got != "true", got
+
+    def test_h3_a_git_toplevel_root_with_a_committed_policy_is_full_coverage(self, tmp_path, monkeypatch):
+        """H2。分類:regression-lock(在 S5g-1 上必須通過)。
+
+        root 本身就是 Git 最上層,policy 正常提交、worktree = HEAD ⇒ 仍為 `"true"`。
+        鎖住 4h 的修正不得封死正常的最上層 host。
+        """
+        got = _g_coverage(_g_default_root(tmp_path / "root"), monkeypatch)
+        assert got == "true", got
```
<!-- 逐字結束 -->

### E.2 `git diff 8e7775526e462d984abb0992ed74c1e1aa3648dd..7621e3ce8604ab72ab2f3fb3257cb1181b8a126e -- tests/test_redlight.py`(3h)

<!-- 逐字開始 -->
```
diff --git a/tests/test_redlight.py b/tests/test_redlight.py
index 6f444db..26da0b5 100644
--- a/tests/test_redlight.py
+++ b/tests/test_redlight.py
@@ -2532,3 +2532,45 @@ class TestEvidencePolicyNoOverride:
                            usepdb=False)
         got = _g_coverage(root, monkeypatch, option=option)
         assert got != "true", got
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# 票 145 Station 3h 補紅燈 —— S5g-F2:evidence root 必須就是 Git 最上層(〈五十三〉53.3 裁決 2、3)
+#
+# 成因:`git -C <root> rev-parse HEAD:<path>` 的 `<path>` 以 **Git 最上層**(tree 根)為基準,
+# `git -C <root> hash-object <path>` 以 **root(cwd)** 為基準。root 不是最上層時,被驗證的 HEAD 物件與
+# 實際使用的工作樹物件不是同一個邏輯路徑(identity 錯位),內容相同即可取得 `"true"`。
+# 框架目前只支援「一個 host evidence root = 一個 Git 最上層」;monorepo 子專案作為 evidence root 屬另案,
+# 巢狀獨立 repo 的情境不在本輪。
+# 既有 helper(`_g_default_root` / `_g_coverage` / `_G_POLICY_FILE`)只呼叫、不修改。
+# ─────────────────────────────────────────────────────────────────────────────
+
+class TestEvidenceRootIsGitToplevel:
+
+    def test_h3_a_parent_committed_policy_does_not_authorize_a_subdirectory_root(self, tmp_path, monkeypatch):
+        """H1。分類:behavior-red(在 S5g-1 上必須失敗)。
+
+        Git 最上層 `parent` 已提交合法 policy、`pyproject.toml`、`tests/conftest.py`;root = `parent/sub`,
+        三份位元組相同的副本只在工作樹、從未提交於 `sub/` 底下。`sub` 的 canonical policy 從未提交
+        ⇒ 不得為 `"true"`(〈四十六〉46.4 第 6 點、I-3:canonical policy 必須是 evidence root 對應路徑上、
+        已提交的 HEAD blob)。
+        S5g-1 上失敗的原因:`git rev-parse HEAD:<path>` 以最上層為基準、`git hash-object <path>` 以 root 為基準
+        ⇒ 兩者指向 `parent/<path>` 與 `sub/<path>`,內容相同即 head == worktree ⇒ identity 錯位即可取得 `"true"`。
+        """
+        parent = _g_default_root(tmp_path / "parent")
+        sub = parent / "sub"
+        for rel in (_G_POLICY_FILE, "pyproject.toml", "tests/conftest.py"):
+            dst = sub / rel
+            dst.parent.mkdir(parents=True, exist_ok=True)
+            dst.write_bytes((parent / rel).read_bytes())
+        got = _g_coverage(sub, monkeypatch)
+        assert got != "true", got
+
+    def test_h3_a_git_toplevel_root_with_a_committed_policy_is_full_coverage(self, tmp_path, monkeypatch):
+        """H2。分類:regression-lock(在 S5g-1 上必須通過)。
+
+        root 本身就是 Git 最上層,policy 正常提交、worktree = HEAD ⇒ 仍為 `"true"`。
+        鎖住 4h 的修正不得封死正常的最上層 host。
+        """
+        got = _g_coverage(_g_default_root(tmp_path / "root"), monkeypatch)
+        assert got == "true", got
```
<!-- 逐字結束 -->

### E.3 `git diff 7621e3ce8604ab72ab2f3fb3257cb1181b8a126e..ea6aba6452668982fee56f7a2f0faf2cd720ca6d -- .claude/hooks/redlight.py tests/test_redlight.py`(4h)

<!-- 逐字開始 -->
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
<!-- 逐字結束 -->

### E.4 `git show ea6aba6452668982fee56f7a2f0faf2cd720ca6d:.claude/hooks/redlight.py` 的三段函式全文

#### E.4.1 `_root_is_toplevel`(第 726–736 行)

<!-- 逐字開始 -->
```
def _root_is_toplevel(root):
    """root 是否就是 git 工作樹的最上層(`git rev-parse --show-prefix` 為空)。失敗 ⇒ False。"""
    import subprocess
    try:
        proc = subprocess.run(["git", "-C", os.fspath(root), "rev-parse", "--show-prefix"],
                              capture_output=True, timeout=30)
    except Exception:
        return False
    if proc.returncode != 0:
        return False
    return proc.stdout.strip() == b""
```
<!-- 逐字結束 -->

#### E.4.2 `committed_blobs`(第 739–766 行)

<!-- 逐字開始 -->
```
def committed_blobs(root, paths=BLOB_FILES):
    """`{path: {"worktree": blob, "head": blob}}` —— 工作樹檔案(`git hash-object`,依
    .gitattributes 正規化)與 `HEAD:<path>` 的 blob。〈二十九〉2 (xi)。

    git 不可用、不是 repo、檔案不存在或任何一步出錯 ⇒ 該值 None(缺欄 ⇒ 不得為 `"true"`)。
    **逐路徑各呼叫一次 git**(票 145 Station 4g;規劃檔 P3 遷移第 3 點):一次處理全部路徑的話,
    缺一個檔整次失敗、所有路徑都成 None —— 淨室 repo 沒有 pyproject 時,conftest 的 blob 也一起遺失。
    **不拋例外**:這是 producer 在 sessionfinish 呼叫的,不得讓 pytest 失敗。
    root 必須是 git 最上層(I-3 位置不變式;票 145 Station 4h,S5g-F2):HEAD:<path> 以最上層為基準、
    hash-object 以 root 為基準,root 不是最上層時兩者不是同一邏輯路徑 ⇒ 事實一律 None ⇒ unknown。
    框架目前只支援一個 host evidence root = 一個 Git 最上層。
    """
    out = {}
    top = _root_is_toplevel(root)
    for p in list(paths):
        entry = {"worktree": None, "head": None}
        if not top:
            out[p] = entry
            continue
        try:
            worktree = _git_lines(root, ["hash-object", p], 1)
            head = _git_lines(root, ["rev-parse", "HEAD:" + p], 1)
            entry["worktree"] = worktree[0] if worktree else None
            entry["head"] = head[0] if head else None
        except Exception:
            pass
        out[p] = entry
    return out
```
<!-- 逐字結束 -->

#### E.4.3 `evidence_policy_facts`(第 845–891 行)

<!-- 逐字開始 -->
```
def evidence_policy_facts(root):
    """producer 的 policy 事實(票 145 規劃檔 P3 I-3;〈四十八〉48.1 第 2 點)。依序:

      1. 固定 canonical path `POLICY_FILE`;
      2. `git rev-parse HEAD:<path>` —— HEAD 沒有 ⇒ 停在這裡(`head` 為 None);
      3. 第 2 步的輸出就是 HEAD committed blob;
      4. `git hash-object <path>`(套用 .gitattributes,與 `committed_blobs` 同一手法)取 worktree blob;
         ≠ HEAD blob 或缺檔 ⇒ 停在這裡;
      5. 內容**只從 HEAD blob** 取(`git cat-file blob <sha>`)並解析 JSON —— 第 4 步的工作樹檔只做
         identity 比對,之後不再讀;記下 `schema` / `version` 與整份內容 `policy`;
      6. policy 的 `config_file` 屬於 `FRAMEWORK_CONFIG_FILES` 時,另記它在 HEAD 的 addopts 原值
         `committed_addopts`(`_committed_addopts`),供 consumer 做「policy ↔ 已提交設定」的機器鎖步。

    回傳 7 鍵 `{"path", "head", "worktree", "schema", "version", "policy", "committed_addopts"}`
    (〈五十一〉裁決 3);走不下去的那一步之後的欄位都是 None。
    **只擷取事實,不判定** —— 型別、schema、邊界、鎖步都由 consumer 驗。不拋例外(sessionfinish 呼叫)。
    root 必須是 git 最上層(I-3 位置不變式;票 145 Station 4h,S5g-F2):HEAD:<path> 以最上層為基準、
    hash-object 以 root 為基準,root 不是最上層時兩者不是同一邏輯路徑 ⇒ 事實一律 None ⇒ unknown。
    框架目前只支援一個 host evidence root = 一個 Git 最上層。
    """
    out = {"path": POLICY_FILE, "head": None, "worktree": None, "schema": None,
           "version": None, "policy": None, "committed_addopts": None}
    try:
        if not _root_is_toplevel(root):
            return out
        head = _git_lines(root, ["rev-parse", "HEAD:" + POLICY_FILE], 1)
        if not head:
            return out
        out["head"] = head[0]
        worktree = _git_lines(root, ["hash-object", POLICY_FILE], 1)
        out["worktree"] = worktree[0] if worktree else None
        if out["worktree"] != out["head"]:
            return out
        raw = _git_bytes(root, ["cat-file", "blob", out["head"]])
        if raw is None:
            return out
        doc = json.loads(raw.decode("utf-8"))
        if not isinstance(doc, dict):
            return out
        out["schema"] = doc.get("schema")
        out["version"] = doc.get("version")
        out["policy"] = doc
        if doc.get("config_file") in FRAMEWORK_CONFIG_FILES:
            out["committed_addopts"] = _committed_addopts(root, doc["config_file"])
    except Exception:
        pass
    return out
```
<!-- 逐字結束 -->

---

## F. 證據(逐字)

出處一律為 REVIEW_HEAD(`2f496b9d0a71d88995b2338c6b4440d693c9a879`)。

### F.0 H1 / H2 紅綠定位表(非逐字;每格附 F.2 / F.1 出處行號)

F.1 / F.2 的行號 = REVIEW_HEAD 上該檔的行號(本包 F.1 / F.2 逐字段與之逐行對應)。

| 測試 | S3H1 上的固定全套 | S4H1(TARGET)上的固定全套 |
|---|---|---|
| H1 `tests/test_redlight.py::TestEvidenceRootIsGitToplevel::test_h3_a_parent_committed_policy_does_not_authorize_a_subdirectory_root`(behavior-red;F.2 第 43 行) | **failed**:F.2 第 57–59 行 `assert got != "true", got` / `AssertionError: true` / `assert 'true' != 'true'`、第 61 行 `tests\test_redlight.py:2567: AssertionError`、第 67 行 `FAILED …test_h3_a_parent_committed_policy_does_not_authorize_a_subdirectory_root`、第 68 行摘要 `1 failed, 2095 passed, 3 skipped, 3 xfailed`;第 71 行「唯一的 FAILED 是 H1」 | **passed**:F.1 第 121 行摘要 `2096 passed, 3 skipped, 3 xfailed`(0 failed);第 124 行「0 failed;輸出沒有任何 `FAILED` / `ERROR` 行」;第 125 行「H1 由紅轉綠」 |
| H2 `tests/test_redlight.py::TestEvidenceRootIsGitToplevel::test_h3_a_git_toplevel_root_with_a_committed_policy_is_full_coverage`(regression-lock;F.2 第 44 行) | **passed**:F.2 第 71 行「H2 在 2095 passed 之內」;第 67 行的 FAILED 清單只有 H1 | **passed**:F.1 第 121 行摘要(0 failed);第 125 行「H2 維持綠」 |

POSIX 旁證(裁決助手;非本 repo 帳本證據):F.1 第 249 行「修正前 … H1 失敗於 got == "true"、H2 通過」。

### F.1 `docs/audits/2026-10-05-m1a-station4h-fix.md` 全文

行號來源:REVIEW_HEAD 的該檔第 1–257 行

<!-- 逐字開始 -->
# 票 145 Station 4h —— S5g-F2 最小修正(evidence root 必須是 Git 最上層)與本機驗收

- 日期:2026-10-05
- 對象:S4H1 `ea6aba6452668982fee56f7a2f0faf2cd720ca6d`(只改 `.claude/hooks/redlight.py`)。
- 上一個 commit:S3H2 `66140896d03f32c4df73be01b2aaeb48353e0510`;紅燈 S3H1 `7621e3ce8604ab72ab2f3fb3257cb1181b8a126e`。
- 合約:票 145〈五十三〉53.3 裁決 2;Jeff 裁決 Station 3h = PASS / ACCEPTED、Station 4h plan = APPROVED、H1 / H2 不准修改、最小修正只動 redlight.py。
- 範圍:**本機(Windows)驗收**。POSIX 外部 clean-room 驗收尚未執行(第 7 節)。**本報告不宣稱 4h 完成。**（S4H4 後更新：POSIX 已 PASS，見第 9 節；Station 4h = PASS / COMPLETED。另：本句原文「第 7 節」指向有誤，POSIX 驗收實為第 9 節，原文保留不改。）

## 【給裁決者】

1. 修正:證據根目錄必須就是 Git 最上層;不是的話,policy 與設定檔的事實一律記「取不到」,這次執行就不能退紅。
2. 本機全套 2096 passed、0 failed;3h 那支紅(H1)轉綠,H2 維持綠。
3. 淨室(全新安裝的乾淨 repo)兩正三負全部成立,正二仍可退紅。
4. 本 repo 的測試帳本只往後加,淨室驗收前後完全沒動。
5. 下一步是 POSIX 外部淨室驗收(裁決助手執行),通過後才升級狀態。（S4H4 後更新：POSIX 已 PASS，見第 9 節；狀態已升級。）

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
4. 本機只驗 Windows。（S4H4 後更新：POSIX 已 PASS，見第 9 節；屬裁決助手外部驗證，非本 repo 帳本證據。）

### 8. 程序紀錄

- 外來 3 檔以 `git stash push -u -m jeff-mods-recon-20261004-s4h -- <3 檔>` 收起,本輪結束後 `git stash pop` 放回。
- 沒有閘門擋下;沒有改測試、`.dev/pipeline.json`;沒有 push / fetch。
- 本輪與 5g 審查、5g-1、3h 由同一 session 執行(依 Jeff 程序註記,該 session 不得擔任 5h 審查者)。

### 9. POSIX 外部 clean-room 驗收

> **舊文字(F-036,保留不刪)**:本節標題原為 ~~`### 9. POSIX 外部 clean-room 驗收:待執行(裁決助手)`~~,沒有內文。
> 2026-10-05 S4H4 依 Jeff 裁決改為下方照錄段落。

POSIX 外部 clean-room 驗收（裁決助手；隔離環境；非本 repo 帳本證據）——2026-10-05 約 09:45 ET
- 環境：Linux，Python 3.11.16，pytest 9.1.1，anyio 4.15.0。
- 受測樹：4g POSIX 驗收所用的樹（BASE de36ebcbab284ef11064a9943b5191750482dd93 + S4G3 時點 12 檔）再覆蓋 S3H1 的 tests/test_redlight.py 與 S4H1 ea6aba6452668982fee56f7a2f0faf2cd720ca6d 的 .claude/hooks/redlight.py 原檔（CRLF→LF）。
- 修正前（S3H1 tests + 4g 程式）：H1 失敗於 got == "true"、H2 通過，與 Windows 3h 一致。
- 修正後：verify_gates.py R1–R9 各擋下一次；權威層偵測三項成立；淨室框架測試 0 failed；evidence policy 兩正三負全部成立：
    正一 未初始化 成立（35 個框架測試檔皆 unknown；evidence policy: 未初始化）
    正二 已初始化且相符 成立（rc 1→0；file_coverage=true；green=tests/test_evidence_probe.py；evidence policy: 有效）
    負一 policy / 環境不符 成立（file_coverage=unknown；紅仍在）
    負二 HEAD 有、工作樹不同 成立（file_coverage=unknown；evidence policy: 工作樹與 HEAD 不同）
    負三 工作樹有、HEAD 沒有 成立（file_coverage=unknown；evidence policy: 未提交）
- 宿主固定全套（Linux）：collected 2102；2086 passed、13 failed、3 xfailed。13 支與 4g POSIX 驗收及 de36ebc 基準在同一沙盒的失敗集合完全相同（tests/test_gate.py::TestAuthorityLayerIsWired::test_this_repo_itself_is_wired 與 tests/test_known_items_regression.py 的 12 支）⇒ 沙盒環境因素（推測：clone 未設 hooksPath、缺本機私有資料），與 3h/4h 無關。evidence 相關 5 檔全過。
- 結論：POSIX 外部 clean-room 驗收 PASS。
<!-- 逐字結束 -->

### F.2 `docs/audits/2026-10-04-m1a-station3h-redlight.md` 全文

行號來源:REVIEW_HEAD 的該檔第 1–106 行

<!-- 逐字開始 -->
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
<!-- 逐字結束 -->

---

## G. 審查重點

<!-- 逐字開始 -->
G1 修正是否封住 S5g-F2：_root_is_toplevel 的判準（rev-parse --show-prefix 為空）是否等價於「root 是 Git 認定的該 repository 最上層」；指令失敗 / 例外 / 非零 returncode 是否一律 False（fail-closed）。
G2 是否兩處都擋：evidence_policy_facts 與 committed_blobs 都在呼叫 git 之前先檢查；committed_blobs 非最上層時每個路徑都記 None（不得只擋 policy、留 (xi) 半套）。
G3 不變式未削弱：consumer（_completeness_problems / _completeness_verdict）、policy_state 判定字串、content_hash 及其呼叫鏈未改（以 E.1 / E.3 驗）；conftest、status.py / install.py / verify_gates.py 及其他非 docs 檔皆未改（以 D.2 的 TARGET_G..TARGET 全範圍 name-only 驗，不得只靠 E.1 / E.3，因為那兩段只餵了 CODE_FILES）。
G4 紅綠時序：H1 在 S3H1 為 red（失敗於 got == "true"）、H2 為 green；S4H1 後兩者 green（見 F 段定位表與 F.2 / F.1 原文），不得只看最終全綠。
G5 H1 是否真的測到 F2 的形狀：sub 下三份副本從未提交（_g_default_root 只在 parent 建立並提交基準內容），root = parent/sub、經真實 conftest producer；H2 是否真的證明正常最上層不受影響。
G6 5g 的其他結論是否仍成立：本輪改動是否影響 5g 報告 G1 / G6 / G13 以外的任何結論；S5g-F1 / F3 / F4 / F5 的追蹤項狀態是否正確（仍未 machine-enforced）。
G7 殘餘措辭與程式一致：證據報告寫「monorepo 中非 Git 最上層的普通子專案不支援；巢狀獨立 Git repo / submodule 若自身為最上層會被接受、未納入 acceptance、屬未證明」—— 是否與 _root_is_toplevel 的實際行為一致，不得宣稱已拒絕所有巢狀 repo。
G8 跨平台：--show-prefix 在 Windows（CRLF 主控台、路徑大小寫、分隔符）下是否仍為空字串判定；是否有可能在最上層誤回非空導致正常 host 一律 unknown（fail-closed 但會封死正常 host；若有，須指出）。
G9 總問題（增量版）：在 TARGET 上，是否仍存在任何路徑，讓 root 的 canonical policy 沒有提交在「Git 對該 root 實際解析出的 repository / HEAD」中，卻能取得 file_coverage == "true"（要抓的是工作樹所用物件與 HEAD 所證明物件的 identity 錯位；policy 確實存在於該 root 自己解析到的 HEAD 者，不構成 F2）；請主動嘗試構造反例（含：root 為 submodule、root 為 worktree（git worktree add）、root 含 .git 檔而非目錄、GIT_DIR / GIT_WORK_TREE 環境變數、符號連結），找不到也要列出檢查過的路徑。
<!-- 逐字結束 -->

---

## H. 已知殘餘與追蹤項

出處:F.1 的「殘餘與未證明」一節,即 REVIEW_HEAD 的 `docs/audits/2026-10-05-m1a-station4h-fix.md` 第 227–233 行。

<!-- 逐字開始 -->
### 7. 殘餘與未證明(目前尚未 machine-enforced)

1. 沿用 4g 證據報告(`docs/audits/2026-10-04-m1a-station4g-fix.md`)第 8 節全部項目,不擴張。
2. 5g 追蹤項:S5g-F1(下一張票優先;status「有效」不含 addopts 鎖步)、S5g-F3(原生 `[tool.pytest]` 永遠 unknown)、S5g-F4(clean filter 讓 (xi) 誤判)、S5g-F5(正二不成立時負情境仍印成立)。
3. 本輪新增(照錄):
   「本輪檢查的語意是 git rev-parse --show-prefix 為空，即 root 必須是 Git 認定的該 repository 最上層。monorepo 中、非 Git 最上層的普通子專案，本輪明確不支援作為 evidence root（H1 鎖住）。巢狀獨立 Git repo / submodule 若自身被 Git 視為最上層，--show-prefix 同樣為空、會被接受；其行為本輪未納入 acceptance，屬未證明範圍，不得宣稱已拒絕或已支援。」
4. 本機只驗 Windows。（S4H4 後更新：POSIX 已 PASS，見第 9 節；屬裁決助手外部驗證，非本 repo 帳本證據。）
<!-- 逐字結束 -->

**註**:上列追蹤項目前尚未 machine-enforced。
