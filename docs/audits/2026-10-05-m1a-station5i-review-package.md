# M1-a Station 5i 增量獨立審查包(票 145)

**審查對象(TARGET,本輪最後一個程式 commit)**:`8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8`
**審查 HEAD(REVIEW_HEAD;review baseline)**:`36c978e1c20a51d40cac777dd5aee58625f97032`
**審查範圍**:只審 3i / 4i 增量(TARGET_H → TARGET)。5g / 5h 已審過 TARGET_H 之前的內容。

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
| **BASE_H** | `2f496b9d0a71d88995b2338c6b4440d693c9a879` | 5h 審查 HEAD(S4H4) |
| **TARGET_H** | `ea6aba6452668982fee56f7a2f0faf2cd720ca6d` | 5h 審過的最後程式 commit(S4H1) |
| S5h-0 | `300b42a520b0a62fec0931d895200ea8817e47aa` | 5h 審查包 |
| S5h-1 | `b62346136cd5ce3bcb0e8dfbc78e3c827f7da849` | 5h 審查報告入庫與 3i 裁決 |
| S3I1 | `260ede30628c7d205b30ac12c94be73a75cd2812` | I1 / I2 / I3 紅燈 |
| S3I2 | `b11dc9eb49912d1a639534aca14aed31b24a9dec` | 3i 紅燈證據(docs) |
| **TARGET**(S4I1) | `8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8` | 本輪最後程式 commit —— **審查對象** |
| S4I3 | `64da2ec2b78b64b6eb23822c7a0e018b82e2500a` | 4i 本機驗收證據(docs) |
| **REVIEW_HEAD**(S4I4) | `36c978e1c20a51d40cac777dd5aee58625f97032` | POSIX 外部驗收記錄、4i 升級為 PASS / COMPLETED(docs);review baseline |

- 本包所在的 commit(S5i-0)是 REVIEW_HEAD **之後**才建立的 docs-only commit;本包寫不進自己的 SHA,由裁決者交付審查時另附。S5i-0 **不屬於審查對象**。
- **CODE_FILES**(`git diff --name-only <TARGET_H>..<TARGET>` 中所有非 docs/ 的檔,2 個):`.claude/hooks/redlight.py` `tests/test_redlight.py`。
- TARGET 之後到 REVIEW_HEAD 只改 docs/。

建包時核對(原文輸出;各自單獨執行,全部以完整 SHA 為錨點):

```
$ git merge-base --is-ancestor 2f496b9d0a71d88995b2338c6b4440d693c9a879 36c978e1c20a51d40cac777dd5aee58625f97032
(無輸出;exit 0)
$ git rev-list --count 2f496b9d0a71d88995b2338c6b4440d693c9a879..36c978e1c20a51d40cac777dd5aee58625f97032
7
$ git diff --name-only 8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8..36c978e1c20a51d40cac777dd5aee58625f97032
docs/audits/2026-10-05-m1a-station4i-fix.md
docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
```

`git diff --name-only <TARGET_H>..<TARGET>` 全文見 D.2。

### A.2 審查者規則

1. **身分**:4g 實作 session、本輪實作 session(3h / 4h / 5h-0 / 5h-1 / 3i / 4i / 5i-0)、5g 與 5h 審查 session 皆不得擔任 5i 審查者;5i 審查須在全新對話進行。
2. **唯讀**:不改任何檔案、不 commit、不推、不改 `.dev/pipeline.json`。審查報告只寫到 `.scratch/m1a-s5i/review-report.md`,不寫其他位置。
3. **禁止 pytest**(含 `--collect-only`、`--version`)、`verify_gates.py` 與 `status.py`。帳本(`.dev/test-runs.jsonl`、`.dev/test-sessions.jsonl`)會被任何 pytest 執行追加,審查不得污染證據。需要驗證行為時,讀程式碼做紙上推演;必須實跑才能確定者,寫成「需要重現」並描述最小重現方式。
4. **查詢一律綁定 A.1 的完整 SHA**;不以 `HEAD`、`HEAD~n`、遠端追蹤分支、本地分支名、短 SHA 或工作樹當下狀態為錨點。範例:

```
git show 8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8:<路徑>
git diff ea6aba6452668982fee56f7a2f0faf2cd720ca6d..8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8 -- <路徑>
git log --oneline 2f496b9d0a71d88995b2338c6b4440d693c9a879..36c978e1c20a51d40cac777dd5aee58625f97032
git show 36c978e1c20a51d40cac777dd5aee58625f97032:docs/audits/2026-10-05-m1a-station4i-fix.md
```

5. **逐字段的邊界以各段標示的出處行號為準**(不以段內標題或圍籬判斷)。
6. 可用 Read / Grep 讀本機已安裝的 pytest / pluggy 原始碼與 git 文件;引用只寫 `_pytest/<檔名>:<行號>` 等相對形式,不寫本機絕對路徑。
7. **照錄任何系統訊息、錯誤訊息或路徑前,先把本機使用者名稱遮成 `<user>`。**
8. 被任何閘門(R1–R9、pre-commit、洩漏偵測)擋下:停手回報,不換工具、不繞過。
9. **結論只能是 `PASS` 或 `FAIL`**;finding 須標嚴重度,並附 `<TARGET>:<路徑>:<行號>` 形式的證據(以 TARGET 為準)。沒有檔名與行號證據的發現不計入判定。
10. **範圍**:5g / 5h 已審過 TARGET_H 之前的內容,本輪只審增量;但若增量使 5g / 5h 的任何結論失效,須指出。
11. G 段 G1–G9 每一題都必須回答(「無問題」也要附證據);不能回答的,寫明「無法判定」與原因,不得略過。
12. 不得用 python -c、heredoc 或把程式碼放進指令字串。

---

## B. 裁決與背景(逐字)

出處一律為 `36c978e1c20a51d40cac777dd5aee58625f97032:docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md`(以下稱「REVIEW_HEAD 的票 145」)。

### B.1 〈五十七〉Station 5h 獨立審查與 Station 3i 裁決

行號來源:REVIEW_HEAD 的票 145 第 2892–2929 行

<!-- 逐字開始 -->
## 五十七、Station 5h 獨立審查（FAIL）與 Station 3i 裁決（2026-10-05，Jeff）

### 57.1 審查報告

- 路徑 `docs/audits/2026-10-05-m1a-station5h-review.md`;raw = repo 副本(與審查者原檔 `.scratch/m1a-s5h/review-report.md` 以 `cmp` 逐位元組相同,無任何改動);
  sha256 `7dac1d2a145ac576ab8958d0c9fd9eb1275333ab79f70f07639c6f32e02ed8d0`;33480 bytes。
- 審查對象 TARGET `ea6aba6452668982fee56f7a2f0faf2cd720ca6d`;審查包所在 commit S5h-0 `300b42a520b0a62fec0931d895200ea8817e47aa`。
- **審查者判決:FAIL**(blocker 0、major 1、minor 1、nit 2)。
- Findings(報告第 2 節;一行摘要,不改寫結論):
  - S5h-F1【major;G9 / G1 / G7;需要重現(端到端)】`_root_is_toplevel` 只看 `--show-prefix` 為空;root 位於 gitdir 內(bare repo 目錄、bare 底下子目錄、非 bare 的 `.git/`)時 `--show-prefix` 同樣 exit 0 輸出空行,`HEAD:<path>` 取 tree 根的已提交 blob、`hash-object <path>` 讀 root 底下 Git 不對應任何 tree 路徑的副本 ⇒ head == worktree ⇒ 預期 `file_coverage == "true"`;同一 root 的 `--show-toplevel` exit 128,53.3 裁決 2 的等價式不成立。
  - S5h-F2【minor;G2 / G5;需要重現(突變測試)】刪掉 `committed_blobs` 的非最上層分支(`:755-757`)H1 仍會綠 —— `evidence_policy_facts` 已先回全 None;全樹沒有測試直接呼叫 `committed_blobs` 或 `_root_is_toplevel`,「不得留 (xi) 半套」只由程式碼保證、沒有測試鎖住。
  - S5h-F3【nit;G7】殘餘措辭漏列「被接受但不是獨立 repo」的佈局(`sub/.git` 檔指向上層 gitdir、只設 `GIT_DIR`、`core.worktree` 指向 sub):Git 把 sub 解析成同一 repository 的工作樹最上層;依 G9 判準不構成 F2,只是措辭涵蓋面不足。
  - S5h-F4【nit;G3 / G7】非最上層 root 沒有專屬 status 狀態字:monorepo 子專案的 policy 已提交於上層 repo 時 status 顯示「未提交」,照字面再提交也不會變;fail-closed,與 S5g-F1 同型;非本輪引入。
- 5g 結論:報告第 5 節逐條判定 5g 的 G1–G13 與 S5g-F1 / F3 / F4 / F5 仍成立(G1 / G6 / G13 的「例外形狀」更新為:普通子目錄已封住,gitdir / bare 內仍存在 = S5h-F1)。

### 57.2 裁決助手外部重現(隔離 Linux 環境;git 2.43.0;Python 3.11 + pytest 9.1.1;非獨立審查 finding;非本 repo 帳本證據)

來源:Jeff 的 Station 5h-1 指令,照錄。

- 端到端：以 S4H1 ea6aba6452668982fee56f7a2f0faf2cd720ca6d 的 redlight.py 與 tests/test_redlight.py 既有 helper（_g_default_root、_g_coverage），分別把 root 設為 <parent>/.git（parent 為已提交合法 policy 的最上層）與 <bare.git>/proj（bare clone 底下子目錄），三份未提交副本放在 root 下 ⇒ 兩者皆得 file_coverage == "true"。S5h-F1 由「需要重現」升為已確認。
- 修法原型：_root_is_toplevel 改為一次 git rev-parse --is-inside-work-tree --show-prefix，須第一行為 true 且第二行為空；指令失敗 / 非零 / 任一條件不符 ⇒ False。套用後上述兩個原型轉為非 true；H1 / H2 維持綠；evidence 相關 5 檔共 281 支全過。
- I3 原型：直接呼叫 redlight.committed_blobs(<parent>/sub)（不經 evidence_policy_facts），要求 BLOB_FILES 每一路徑都為 {"worktree": None, "head": None}，且 committed_blobs(<parent>) 每一路徑 worktree 非空且 == head；在 S4H1 與修法原型上皆通過（regression-lock）。

### 57.3 裁決(照錄)

1. Station 5h 獨立審查 = FAIL；S5h-F1 = major / confirmed end-to-end。4h 的 _root_is_toplevel 以 rev-parse --show-prefix 為空當作「root 是工作樹最上層」，但 .git/ 內部或 bare repository 內同樣滿足此條件，而該處並非工作樹 ⇒ HEAD 證明的是 repository 內某個 path、工作樹實際讀的是另一個 filesystem root ⇒ identity mismatch ⇒ 仍可能 file_coverage == "true"。與 S5g-F2 同一條 I-3 位置不變式，不得列追蹤項。〈五十三〉53.3 裁決 2 所稱「與 resolved root == git rev-parse --show-toplevel 等價」實測不成立，於此更正。
2. 回 Station 3i，紅燈三支（皆經真實 conftest producer 或直接呼叫 producer helper，真 git repo）：
   I1 behavior-red：root = <最上層>/.git，三份副本只在 root 下、未提交 ⇒ 不得為 "true"。
   I2 behavior-red：root = <bare clone>/proj，同上 ⇒ 不得為 "true"。
   I3 regression-lock：直接呼叫 committed_blobs 對非法 root（<最上層>/sub）：BLOB_FILES 每一路徑皆 {"worktree": None, "head": None}；對照組 committed_blobs(<最上層>) 每一路徑 worktree 非空且 == head。目的：獨立證明 committed_blobs 那一半 fail-closed，不被 evidence_policy_facts 的 guard 間接遮蔽（S5h-F2）。
3. Station 4i 最小修正方向：_root_is_toplevel 須同時滿足 rev-parse --show-prefix 為空 且 rev-parse --is-inside-work-tree 為 true；任一查詢失敗、非零、或條件不符 ⇒ False ⇒ policy facts / committed_blobs facts 全 None ⇒ unknown ⇒ 不得退紅。對應的 invariant：root 必須是 Git 工作樹的最上層，不只是 Git repository context 中 prefix 恰為空的位置。
4. S5h-F3（殘餘措辭漏列「被接受但非獨立 repo」的重新對應佈局）於 4i 文件補準；S5h-F4（非最上層 root 的 status 無專屬狀態字）併入 S5g-F1 類的 operator / status 追蹤項。兩者不阻擋本輪，目前尚未 machine-enforced。
5. 流程：5h-1 記錄 → Jeff 切 tickets → 3i 紅燈 → Jeff 切 implement → 4i（含 Windows 全套、本機 clean-room、裁決助手 POSIX）→ 5i 增量審查（全新對話；4g 實作 session、5g 與 5h 審查 session 皆不得擔任）→ Station 6。

### 57.4 commit

- S5h-1(本節與審查報告入庫)`b62346136cd5ce3bcb0e8dfbc78e3c827f7da849`。
  (F-036:本行原文為「S5h-1(本節與審查報告入庫)於下一次提交回填。」;2026-10-05 於 S3I2 回填。)
<!-- 逐字結束 -->

### B.2 〈五十八〉Station 3i 紅燈證據

行號來源:REVIEW_HEAD 的票 145 第 2933–2951 行

<!-- 逐字開始 -->
## 五十八、Station 3i 紅燈證據

- Jeff 裁決(2026-10-05):S5h-1 = accepted。**身分更正**:本 session 自 3h 起為事實上的實作 session(3h、4h、5h-0、5h-1 皆由本 session 執行);3i / 4i 繼續由本 session 執行;5i 審查須開全新對話,5g / 5h 審查 session 與本 session 皆不得擔任。
- 報告:`docs/audits/2026-10-05-m1a-station3i-redlight.md`。
- S3I1 `260ede30628c7d205b30ac12c94be73a75cd2812`:`tests/test_redlight.py` 檔尾一個 hunk `@@ -2576,0 +2577,72 @@`,只有 + 行;新增 `class TestEvidenceRootIsInsideWorkTree`,既有 helper 只呼叫、不修改。commit 前只跑 py_compile。
- 新增 3 支(完整 nodeid):
  - I1 behavior-red(在 S5h-1 上必須失敗):`tests/test_redlight.py::TestEvidenceRootIsInsideWorkTree::test_i3_a_root_inside_the_gitdir_is_not_full_coverage`
  - I2 behavior-red(在 S5h-1 上必須失敗):`tests/test_redlight.py::TestEvidenceRootIsInsideWorkTree::test_i3_a_root_inside_a_bare_repository_is_not_full_coverage`
  - I3 regression-lock(在 S5h-1 上必須通過;不經 `evidence_policy_facts`,直接呼叫 `committed_blobs`):`tests/test_redlight.py::TestEvidenceRootIsInsideWorkTree::test_i3_committed_blobs_alone_is_fail_closed_for_a_subdirectory_root`
- 紅燈全套(在 S3I1 上只跑一次;外來 3 檔已 stash,跑前跑後 `git status --porcelain` 皆無輸出):exit 1;
  摘要行原文 `2 failed, 2097 passed, 3 skipped, 3 xfailed in 256.98s (0:04:16)`(collected 2105)。
  FAILED 恰為 I1、I2:失敗行 `tests\test_redlight.py:2613: AssertionError` 與 `tests\test_redlight.py:2629: AssertionError`(皆 `assert 'true' != 'true'`);I3、H1、H2 在 2097 passed 之內。
  ⇒ S5h-F1 在本樹(Windows)端到端重現。
- 帳本只追加:兩本前段 sha256 = Step 0 基準(`5f0ffa92…` / `74757aa6…`);test-runs 3109 → 3156 行(+47)、test-sessions 29 → 30 行(+1)。
  跑後全檔記為 B17:test-runs 845770 bytes、`5c91ea58af19e13d181af2c8ae471738d313d61b60a47fde20f40dfdbde10098`;
  test-sessions 14387323 bytes、`52ef61774703e5b9feff6de02462b878c22ce47b1cface87511b74d14e45ff1a`。
- 裁決助手 Linux 預演(來源:Jeff 的 Station 3i 指令;隔離環境;非本 repo 帳本證據):以 S4H1 的 redlight.py,I1 / I2 原型皆失敗於 got == "true"、I3 原型通過;套用 4i 修法原型後 I1 / I2 / I3 / H1 / H2 全綠,evidence 相關 5 檔 281 支全過。
- commit:S3I1 `260ede30628c7d205b30ac12c94be73a75cd2812`;S3I2(本節與證據報告)`b11dc9eb49912d1a639534aca14aed31b24a9dec`。
  (F-036:本行原文為「S3I2(本節與證據報告)於下一次提交回填。」;2026-10-05 於 S4I3 回填。)
<!-- 逐字結束 -->

### B.3 〈五十九〉Station 4i 修正

行號來源:REVIEW_HEAD 的票 145 第 2955–2997 行

<!-- 逐字開始 -->
## 五十九、Station 4i 修正

### 59.1 裁決(照錄要點;Jeff,2026-10-05)

- Station 3i = PASS / ACCEPTED(I1 / I2 behavior-red、I3 regression-lock 成立);Station 4i plan = APPROVED;只改 `_root_is_toplevel()`,I1–I3 / H1 / H2 不准修改。
- 三段式:S4I1 實作 → S4I2 本機驗收 → S4I3 docs-only(只能宣稱本機驗收通過;待 POSIX 外部驗收)。POSIX 由裁決助手執行,通過後另以 S4I4 升級。

### 59.2 證據

- 報告:`docs/audits/2026-10-05-m1a-station4i-fix.md`。
- S4I1 `8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8`:只改 `.claude/hooks/redlight.py` 的 `_root_is_toplevel()`(+9 / −3,一個 hunk `@@ -724,16 +724,22 @@`)。
  - 一次呼叫 `git -C <root> rev-parse --is-inside-work-tree --show-prefix`;須第一行 strip 後為 `b"true"` 且第二行 strip 後為空才 True;任何例外 / returncode ≠ 0 / `len(lines) < 2` / 條件不符 ⇒ False。
  - 未改 `committed_blobs` / `evidence_policy_facts` 的呼叫處、consumer、`policy_state`、conftest、status / install / verify_gates、任何測試;`content_hash` 未動。
  - 一次 Edit,寫入後 status.py 探針無「redlight.py 無 run 事實讀取」。
- S4I2 本機固定全套(S4I1 上只跑一次;外來 3 檔已 stash):exit 0;`2099 passed, 3 skipped, 3 xfailed in 241.02s (0:04:01)`(collected 2105、0 failed)。I1 / I2 由紅轉綠,I3 / H1 / H2 維持綠。
- 帳本只追加:前段 sha256 = B17;test-runs 3156 → 3203(+47)、test-sessions 30 → 31(+1)。
- status:`evidence policy: 有效`;`tests red under ticket 145: (無)`;run 事實未知 0;`tests/test_redlight.py` 在 green。
- 淨室(verify_gates;同一次執行):R1–R9 各擋下一次、權威層偵測三項成立、淨室框架測試 `1949 passed, 7 skipped, 3 xfailed`;兩正三負全部成立,正二 `file_coverage=true`、`green=tests/test_evidence_probe.py`。
  本 repo 兩本帳本前後 bytes 與 sha256 都等於 V0(test-runs 857289 / `9e909520…`;test-sessions 15126808 / `440406f6…`)。
- 裁決助手 Linux 預演(來源:Jeff 的 Station 4i 指令;隔離環境;非本 repo 帳本證據):以 S3I1 的 tests 與 S4H1 的程式,I1 / I2 失敗於 got == "true"、I3 通過;套用本修正形狀後 I1 / I2 / I3 / H1 / H2 全綠,evidence 相關 5 檔 282 支全過。
- 殘餘與未證明(目前尚未 machine-enforced):沿用 4h 證據報告第 7 節 + S5g-F1 / F3 / F4 / F5、S5h-F3 / F4 追蹤項;本輪依 S5h-F3 補準措辭(照錄於報告第 7 節第 3 點):
  「本輪檢查的語意是 git rev-parse --is-inside-work-tree 為 true 且 --show-prefix 為空，即 root 必須是 Git 對該 root 解析出的工作樹的最上層。明確不支援（⇒ unknown）：monorepo 中非最上層的普通子目錄（H1）、位於 gitdir 或 bare repository 內的 root（I1 / I2）。會被接受但本輪未納入 acceptance、屬未證明：巢狀獨立 Git repo、submodule、linked worktree（git worktree add）、.git 為檔案且 gitdir 指向他處、GIT_DIR / GIT_WORK_TREE / core.worktree 等重新對應佈局。上述佈局若 Git 對該 root 實際回報 --is-inside-work-tree=true 且 --show-prefix 為空，即會被本檢查接受；其 HEAD 與工作樹是否符合既定 identity invariant，本輪未完整 acceptance，不得宣稱已拒絕或已支援。」
- commit:S4I1 `8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8`;S4I3(本節與證據報告)`64da2ec2b78b64b6eb23822c7a0e018b82e2500a`。
  (F-036:本行原文為「S4I3(本節與證據報告)於下一次提交回填。」;2026-10-05 於 S4I4 回填。)
  - S4I4(POSIX 驗收記錄與狀態升級)於下一次提交回填。

### 59.3 POSIX 外部 clean-room 驗收

> **舊文字(F-036,保留不刪)**:本節原文為 ~~`待執行(裁決助手)。`~~;2026-10-05 S4I4 依 Jeff 裁決改為下方照錄段落。
> Jeff 裁決(2026-10-05):Station 4i 本機驗收(S4I2,見 S4I3 `64da2ec2b78b64b6eb23822c7a0e018b82e2500a`)與裁決助手 POSIX 外部驗收皆 PASS ⇒ Station 4i = PASS / COMPLETED;下一站 5i 增量獨立審查(只審 3i/4i 增量;須開全新對話;4g 實作 session、本實作 session、5g 與 5h 審查 session 皆不得擔任)。

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
<!-- 逐字結束 -->

---

## C. 5h 審查報告中與 S5h-F1 / F2 / F3 相關的段落(逐字)

出處一律為 `36c978e1c20a51d40cac777dd5aee58625f97032:docs/audits/2026-10-05-m1a-station5h-review.md`(以下稱「5h 審查報告」)。

### C.1 第 1 節判決與嚴重度依據

行號來源:5h 審查報告第 51–69 行

<!-- 逐字開始 -->
## 1. 判決

**FAIL**(blocker 0、major 1、minor 1、nit 2)。

FAIL 的唯一原因是 S5h-F1:`_root_is_toplevel` 的判準(`--show-prefix` 為空)**不等價**於「root 是 Git 最上層」——
root 位於 **gitdir 內**(bare repo 目錄、bare repo 底下的任何子目錄、非 bare repo 的 `.git/` 內)時,
`git rev-parse --show-prefix` 以 exit 0 輸出空行,而 `--show-toplevel` 失敗(exit 128)。
此時 `HEAD:<path>` 以 tree 根為基準、`hash-object <path>` 讀 root 底下一個 **Git 不對應到任何 tree 路徑**的檔,
正是 S5g-F2 的 identity 錯位形狀;git 原語層已在 scratchpad 實驗確認(第 4 節 E3–E6)。

**嚴重度的判斷依據與替代選項(給裁決者)**:

- A(本報告採用):判 **major** ⇒ FAIL。理由:這是同一條 I-3 位置不變式、同一種錯位,而且出現在本輪**專門為了封住它**的修正上;
  〈五十三〉53.3 裁決 1 已把 S5g-F2 這一型定為 FAIL 等級,而 S5g-F2 當時同樣「只有手動佈局會產生」。
  另外,53.3 裁決 2 寫明此判準「與 resolved root == `git rev-parse --show-toplevel` 等價」,實測不等價。
- B:判 **minor**(佈局比 monorepo 子專案更不自然:專案得放在 bare repo 目錄或 `.git/` 底下)⇒ 本輪 PASS,S5h-F1 列追蹤項。
  代價:修正後的 docstring(`:727`)、殘餘措辭與 53.3 的等價宣稱都繼續是錯的,而錯的方向是 fail-open。
- 修法成本(供比較,不是本報告的要求):在 `_root_is_toplevel` 一併要求 `--is-inside-work-tree` 為 `true`
  (實測:gitdir / bare 內為 `false`,正常最上層為 `true`;第 4 節 E7),或改採 53.3 自己寫的另一個形式 `--show-toplevel`。
<!-- 逐字結束 -->

### C.2 Findings 表的表頭與 S5h-F1 / F2 / F3 列

行號來源:5h 審查報告第 75–79 行

<!-- 逐字開始 -->
| 編號 | 嚴重度 | 對應 G 題 | TARGET 檔名:行號 | 具體失敗情境(輸入 → 錯誤結果) | 依據 | 需要重現 |
|---|---|---|---|---|---|---|
| S5h-F1 | **major** | G9 / G1 / G7 | `.claude/hooks/redlight.py:730-736`(判準只看 `--show-prefix`);`:727`(docstring「root 是否就是 git 工作樹的最上層」);`:868-869` → `:870` `HEAD:<POLICY_FILE>` / `:874` `hash-object <POLICY_FILE>`;`:752` → `:759-760`(`committed_blobs` 同一手法);`:825`(`cat-file blob HEAD:<config_file>`);`tests/conftest.py:130`、`:410-412`(以 `_ROOT` 呼叫) | root(= conftest 的上兩層)位於某個 gitdir 內 —— 例:`R.git` 是 bare repo(或 `R/.git`),HEAD 已提交合法 policy、`pyproject.toml`、`tests/conftest.py`;在 `R.git/`(或 `R.git/proj/`、`R/.git/`)放三份位元組相同、**Git 不視為任何工作樹檔**的副本 → `--show-prefix` exit 0 且輸出 `\n` ⇒ `_root_is_toplevel` True → `HEAD:<path>` 取 tree 根的已提交 blob、`hash-object <path>` 讀 root 底下的副本 → head == worktree → `evidence_policy_facts` 與 `committed_blobs` 全部成立 → 其餘條件與 H1 相同 ⇒ 預期 `file_coverage == "true"`。被驗證的 HEAD 物件與實際使用的檔案沒有任何 Git 意義上的路徑對應(identity 錯位);同一 root 的 `--show-toplevel` 為 `fatal: this operation must be run in a work tree`(exit 128),即 53.3 裁決 2 所稱的等價式在此不成立 | git 2.53.0.windows.2 實測(第 4 節 E3–E6):bare 目錄、bare 底下子目錄、`.git/`、`.git/refs` 的 `--show-prefix` 全為空且 exit 0;bare 目錄與 `.git/` 內 `rev-parse HEAD:.agents/evidence-policy.json` 與 `hash-object .agents/evidence-policy.json` 皆為 `30ed4d4db34fbf419031f0b767ca2d2fdad693f4`;`safe.bareRepository` 未設定(預設允許隱式 bare 探索) | **是**(端到端)。最小重現:沿用 H1 的 helper,把 `sub = parent / "sub"` 換成 `root = parent / ".git"`,把三份副本寫到 `parent/.git/` 底下,`_g_coverage(root, monkeypatch)`;預期 TARGET 上得 `"true"`。git 原語層已確認,不需重現 |
| S5h-F2 | minor | G2 / G5 | `.claude/hooks/redlight.py:752-757`(`committed_blobs` 的非最上層分支);`tests/test_redlight.py:2550-2567`(H1 只斷言 `!= "true"`) | 把 `:755-757` 刪掉(`committed_blobs` 在非最上層照舊呼叫 git、留 (xi) 半套),H1 **仍會綠**:`evidence_policy_facts` 在 `:868-869` 已回全 None ⇒ `_effective_policy` 於 `:980` 回 None ⇒ verdict `:1099-1101` unknown,根本走不到 `:1119-1123` 的 blob 檢查。TARGET 全樹沒有任何測試直接呼叫 `committed_blobs` 或 `_root_is_toplevel`(`git grep` 只命中 `redlight.py` 本身與 `tests/conftest.py:410`)。G2 要求的「不得只擋 policy、留 (xi) 半套」目前**只由程式碼保證,沒有測試鎖住** | 靜態閱讀 + `git grep -n -e committed_blobs -e _root_is_toplevel -e show-prefix ea6aba64…` 的原文(第 4 節 E0) | 是(突變測試:刪 `:755-757` 後跑 H1,預期仍 passed) |
| S5h-F3 | nit | G7 | 殘餘措辭(REVIEW_HEAD `docs/audits/2026-10-05-m1a-station4h-fix.md` 第 7 節第 3 點;票 145〈五十五〉55.2);`.claude/hooks/redlight.py:747-749`、`:861-863`(docstring「框架目前只支援一個 host evidence root = 一個 Git 最上層」) | 殘餘只列「巢狀獨立 Git repo / submodule 若自身被 Git 視為最上層會被接受」。另有一類**被接受、但不是獨立 repo** 的佈局沒列:`sub/.git` 為檔案且 `gitdir:` 指向上層 repo 的 gitdir、`GIT_DIR` 有設而 `GIT_WORK_TREE` 沒設、或上層 config 的 `core.worktree` 指向 sub —— Git 把 sub 解析成**同一個 repository** 的工作樹最上層,`--show-prefix` 為空、H1 形狀的副本可取得 head == worktree(第 4 節 E8、E9)。依 G9 判準(policy 存在於該 root 自己解析到的 HEAD)**不構成 F2**,所以只是措辭的涵蓋面不足,不是行為缺陷 | git 實測:`p/sub/.git`(內容 `gitdir: ../.git`)下 `--show-toplevel` = `<scratch>/g9/p/sub`、`--git-dir` = `<scratch>/g9/p/.git`、兩個 blob 皆 `30ed4d4…`;`--git-dir=<p/.git>` 而無 `--work-tree` 時 `--show-toplevel` = cwd | 否 |
<!-- 逐字結束 -->

### C.3 G1 結論

行號來源:5h 審查報告第 86–93 行

<!-- 逐字開始 -->
### G1 判準等價性與 fail-closed —— **部分成立**

- **fail-closed 成立**:`redlight.py:729-733` subprocess 任何例外(含 git 不存在、timeout)⇒ False;`:734-735` returncode ≠ 0 ⇒ False;
  `:736` 只有 stdout strip 後恰為 `b""` 才 True。`os.fspath(root)` 在 try 內(`:730`)。
  空白目錄名不會被 strip 誤判:prefix 一律以 `/` 結尾(實測子目錄輸出 `sub/`),strip 後不可能為空。
- **等價性不成立**:`--show-prefix` 為空 ≠「root 是 Git 認定的工作樹最上層」。在 gitdir 內(bare 目錄、bare 子目錄、`.git/`、`.git/refs`)
  `--show-prefix` 同樣 exit 0、輸出空行,而 `--show-toplevel` exit 128、`--is-inside-work-tree` 為 `false`(第 4 節 E3、E4、E7)。⇒ S5h-F1。
- 對 S5g-F2 原形狀(普通子目錄)**封住**:實測 `p/sub` 輸出 `sub/`(E1),`_root_is_toplevel` False ⇒ `:868-869` 全 None、`:755-757` 全 None。
<!-- 逐字結束 -->

### C.4 G2 結論

行號來源:5h 審查報告第 95–101 行

<!-- 逐字開始 -->
### G2 兩處都擋 —— **成立(附 S5h-F2)**

- `evidence_policy_facts`:`:868-869` 是 try 內第一步,在 `:870` 的 `rev-parse` 之前;回傳 `:865-866` 的全 None 7 鍵。
- `committed_blobs`:`:752` 迴圈前算一次 `top`;`:755-757` 非最上層 ⇒ 每個路徑都寫入 `{"worktree": None, "head": None}` 並 `continue`,不呼叫 `:759-760` 的 git。
  `paths` 預設 `BLOB_FILES`,所以 `config_file` 與 `ROOT_CONFTEST` 都有 None 記錄;verdict `:1119-1123` 對 None 判 unknown。
- `_committed_addopts`(`:825`)只在 `:887-888` 被呼叫,在 `:868-869` 之後,非最上層時走不到。
- 殘餘:`committed_blobs` 這一半沒有任何測試鎖住(S5h-F2)。
<!-- 逐字結束 -->

### C.5 G7 結論

行號來源:5h 審查報告第 138–144 行

<!-- 逐字開始 -->
### G7 殘餘措辭與程式一致 —— **部分成立**

- 「monorepo 中、非 Git 最上層的普通子專案明確不支援(H1 鎖住)」:與程式一致(E1 `sub/` ⇒ False)。
- 「巢狀獨立 Git repo / submodule 若自身被 Git 視為最上層,`--show-prefix` 同樣為空、會被接受」:與程式一致(E10 submodule `--show-prefix` 為空、用 submodule 自己的 HEAD blob `75e2c15…`)。
- 措辭**沒有**宣稱「已拒絕所有巢狀 repo」,反而明寫「不得宣稱已拒絕或已支援」—— 這一點符合要求。
- 不一致處:「本輪檢查的語意是 `--show-prefix` 為空,**即** root 必須是 Git 認定的該 repository 最上層」—— 這個「即」不成立:gitdir / bare 內也被接受(S5h-F1);
  `redlight.py:727` docstring「root 是否就是 git 工作樹的最上層」同樣不成立。另有一類被接受的重新對應佈局未列(S5h-F3)。
<!-- 逐字結束 -->

### C.6 G9 結論

行號來源:5h 審查報告第 154–157 行

<!-- 逐字開始 -->
### G9 總問題(增量版)—— **不成立(找到反例)**

- 反例:root 位於 gitdir 內(S5h-F1)。git 原語層已確認(E3–E6),端到端需要重現。
- 其餘嘗試(submodule、`git worktree add`、`.git` 檔、`GIT_DIR` / `GIT_WORK_TREE`、`core.worktree`、大小寫、符號連結)依 G9 判準都不構成 F2,清單見第 4 節。
<!-- 逐字結束 -->

### C.7 第 4 節 4.1 總表

行號來源:5h 審查報告第 163–184 行

<!-- 逐字開始 -->
### 4.1 總表

| # | 嘗試路徑 | `--show-prefix` | `_root_is_toplevel` | HEAD 物件 vs 工作樹物件 | 結論 |
|---|---|---|---|---|---|
| 1 | 普通子目錄 `p/sub`(S5g-F2 原形狀) | `sub/` | False | — | **擋**(`:868-869`、`:755-757`) |
| 2 | 同上,以全大寫路徑進入 | `sub/` | False | — | 擋 |
| 3 | bare repo 目錄 `bare.git` | 空,exit 0 | **True** | HEAD tree 根 `30ed4d4…` = bare 目錄內未追蹤副本 `30ed4d4…`;Git 不把該副本對應到任何 tree 路徑 | **反例(S5h-F1)** |
| 4 | bare repo 底下的普通子目錄 `bare.git/proj`(隱式 bare 探索) | 空,exit 0 | **True** | 同上,`30ed4d4…` = `30ed4d4…` | **反例(S5h-F1)** |
| 5 | 非 bare repo 的 `p/.git/` | 空,exit 0 | **True** | 同上,`30ed4d4…` = `30ed4d4…` | **反例(S5h-F1)** |
| 6 | `p/.git/refs`(gitdir 子目錄) | 空,exit 0 | **True** | 未另放副本;機制同 #5 | 反例同型 |
| 7 | `git worktree add` 的 linked worktree `wt` | 空 | True | worktree 自己的 HEAD(`p/.git/worktrees/wt`)、檔案是該 HEAD 的 checkout,`30ed4d4…` = `30ed4d4…` | 不構成 F2(policy 在該 root 解析到的 HEAD) |
| 8 | submodule `p/mod` | 空 | True | submodule 自己的 HEAD(`p/.git/modules/mod`),`75e2c15…` = `75e2c15…`,不同於上層的 `30ed4d4…` | 不構成 F2 |
| 9 | `p/sub/.git` 為檔案,`gitdir: ../.git` | 空 | True | Git 解析 toplevel = `p/sub`、gitdir = `p/.git`;`30ed4d4…` = `30ed4d4…` | 不構成 F2(Git 自己把 sub 對應到 tree 根);措辭涵蓋面見 S5h-F3 |
| 10 | 外部目錄 `p2/sub/.git` 指向 `p/.git` | 空 | True | 同 #9 | 不構成 F2 |
| 11 | `GIT_DIR=p/.git`、不設 `GIT_WORK_TREE`,cwd = `p/sub2` | 空 | True | Git 文件語意:cwd 視為工作樹最上層;`--show-toplevel` = `p/sub2` | 不構成 F2(同 #9);conftest 子行程會繼承環境變數 |
| 12 | `GIT_DIR=p/.git` + `GIT_WORK_TREE=p`,cwd = `p/sub2` | `sub2/` | False | — | 擋 |
| 13 | 上層 config `core.worktree` 指向 sub | 未實驗 | 依語意 True | Git 把 sub 解析為工作樹最上層 | 依判準不構成 F2(未實測) |
| 14 | root 路徑為符號連結 | 未實驗 | — | `_ROOT` 已 `resolve()`(`tests/conftest.py:130`) | 不構成 F2(依程式) |
| 15 | root 內 `.agents/` 或 policy 檔本身為符號連結、HEAD 有一般檔 | 未實驗(Windows 未取得 symlink) | True | `hash-object` 讀連結目標內容;HEAD 在同一 canonical path 有已提交 blob | 依判準不構成 F2(policy 確實提交在該 root 的 HEAD canonical path);HEAD 存 symlink(120000)時 blob 是連結字串,與目標內容不等 ⇒ unknown |
| 16 | 名稱只含空白的子目錄 | 依語意 `" /"` | False | prefix 一律以 `/` 結尾,strip 後非空 | 擋 |
| 17 | `safe.directory` dubious ownership | exit 128 | False | — | 擋(fail-closed;TARGET_G 已是 unknown) |
| 18 | `_committed_addopts` 的 `HEAD:<config_file>`(`:825`) | — | — | 只在 `:868-869` 之後呼叫 | 隨 #1–#6 同進退 |
<!-- 逐字結束 -->

### C.8 第 4 節 E3 實驗原文

行號來源:5h 審查報告第 265–289 行

<!-- 逐字開始 -->
E3 —— gitdir / bare 的 `--show-prefix` 與 `--show-toplevel`:

```
$ git clone -q --bare "<scratch>/g9/p" "<scratch>/g9/bare.git"
(無輸出)
$ git -C "<scratch>/g9/p/.git" rev-parse --show-prefix
(無輸出)
$ git -C "<scratch>/g9/p/.git" rev-parse --show-toplevel
Exit code 128
fatal: this operation must be run in a work tree
$ git -C "<scratch>/g9/bare.git" rev-parse --show-prefix
(無輸出)
$ git -C "<scratch>/g9/bare.git" rev-parse --show-toplevel
Exit code 128
fatal: this operation must be run in a work tree
$ git -C "<scratch>/g9/bare.git" rev-parse --is-bare-repository --is-inside-work-tree
true
false
$ git -C "<scratch>/g9/p/.git/refs" rev-parse --show-prefix
(無輸出)
$ git -C "<scratch>/g9/bare.git/refs" rev-parse --show-prefix
(無輸出)
```

(Bash 工具對非零退出碼會印 `Exit code N`;上列「無輸出」的指令皆為 exit 0。)
<!-- 逐字結束 -->

### C.9 第 4 節 E7 實驗原文

行號來源:5h 審查報告第 319–333 行

<!-- 逐字開始 -->
E7 —— 可區分的判準(修法方向參考):

```
$ git -C "<scratch>/g9/p/.git" rev-parse --is-inside-work-tree --is-inside-git-dir --show-prefix
false
true
$ git -C "<scratch>/g9/bare.git/proj" rev-parse --is-inside-work-tree --is-inside-git-dir --show-prefix
false
true
$ git -C "<scratch>/g9/p" rev-parse --is-inside-work-tree --is-inside-git-dir --show-prefix
true
false
```

(三者的 `--show-prefix` 都是空行,顯示時被吃掉。)
<!-- 逐字結束 -->

---

## D. 本輪 commit 與檔案範圍

### D.1 `git log --oneline 2f496b9d0a71d88995b2338c6b4440d693c9a879..36c978e1c20a51d40cac777dd5aee58625f97032`(7 筆,與 A.1 的 S5h-0…S4I4 逐一對應)

<!-- 逐字開始 -->
```
36c978e docs(145): M1-a Station 4i-4 —— POSIX 外部 clean-room 驗收 PASS;Station 4i = PASS / COMPLETED
64da2ec docs(145): M1-a Station 4i-3 —— 本機固定全套與 clean-room 驗收證據;待 POSIX 外部驗收
8154a1a fix(145): M1-a Station 4i-1 —— root 必須是 Git 工作樹的最上層(S5h-F1)
b11dc9e docs(145): M1-a Station 3i-2 —— 紅燈證據(I1 / I2 紅、I3 綠;S5h-F1 / S5h-F2)
260ede3 test(145): M1-a Station 3i-1 —— root 必須是 Git 工作樹最上層的紅燈(S5h-F1 / S5h-F2;3 支)
b623461 docs(145): M1-a Station 5h-1 —— 增量審查入庫(FAIL:S5h-F1 major)與 Station 3i 裁決
300b42a docs(145): M1-a Station 5h-0 —— 增量獨立審查包(只審 3h / 4h)
```
<!-- 逐字結束 -->

### D.2 `git diff --name-only ea6aba6452668982fee56f7a2f0faf2cd720ca6d..8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8`(NAMEONLY_FULL;TARGET_H..TARGET 全範圍)

這是「CODE_FILES 以外的非 docs 檔(conftest、status.py、install.py、verify_gates.py 等)都沒變」的證據;E.1 / E.3 只餵了 CODE_FILES,不足以證明這一點。

<!-- 逐字開始 -->
```
.claude/hooks/redlight.py
docs/audits/2026-10-05-m1a-station3i-redlight.md
docs/audits/2026-10-05-m1a-station4h-fix.md
docs/audits/2026-10-05-m1a-station5h-review-package.md
docs/audits/2026-10-05-m1a-station5h-review.md
docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
tests/test_redlight.py
```
<!-- 逐字結束 -->

---

## E. 程式差異(原樣)

### E.1 `git diff ea6aba6452668982fee56f7a2f0faf2cd720ca6d..8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8 -- .claude/hooks/redlight.py tests/test_redlight.py`(本輪全部程式與測試改動)

<!-- 逐字開始 -->
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
diff --git a/tests/test_redlight.py b/tests/test_redlight.py
index 26da0b5..1b48694 100644
--- a/tests/test_redlight.py
+++ b/tests/test_redlight.py
@@ -2574,3 +2574,75 @@ class TestEvidenceRootIsGitToplevel:
         """
         got = _g_coverage(_g_default_root(tmp_path / "root"), monkeypatch)
         assert got == "true", got
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# 票 145 Station 3i 補紅燈 —— S5h-F1 / S5h-F2:root 必須是 Git **工作樹**的最上層(〈五十七〉57.3 裁決 2、3)
+#
+# 4h 的 `_root_is_toplevel` 只看 `git rev-parse --show-prefix` 為空。但 `.git/` 內部或 bare repository 內
+# 同樣滿足此條件,而該處並非工作樹:`HEAD:<path>` 證明的是 repository 內某個 tree 路徑,`hash-object <path>`
+# 讀的是另一個 filesystem root 底下、Git 不對應任何 tree 路徑的檔 ⇒ identity 錯位 ⇒ 內容相同即可取得 `"true"`。
+# root 必須是 Git 工作樹的最上層,不只是 repository context 中 prefix 恰為空的位置。
+# 既有 helper(`_g_default_root` / `_g_coverage` / `_G_POLICY_FILE` / `_d_git` / `redlight.committed_blobs` /
+# `redlight.BLOB_FILES`)只呼叫、不修改。
+# ─────────────────────────────────────────────────────────────────────────────
+
+class TestEvidenceRootIsInsideWorkTree:
+
+    @staticmethod
+    def _copy_into(parent, root, rels):
+        """把 `parent` 底下的 `rels` 逐一以位元組複製到 `root` 底下(只寫工作樹,不 git add / commit)。"""
+        for rel in rels:
+            dst = root / rel
+            dst.parent.mkdir(parents=True, exist_ok=True)
+            dst.write_bytes((parent / rel).read_bytes())
+
+    def test_i3_a_root_inside_the_gitdir_is_not_full_coverage(self, tmp_path, monkeypatch):
+        """I1。分類:behavior-red(在 S5h-1 上必須失敗)。
+
+        Git 最上層 `parent` 已提交合法 policy、`pyproject.toml`、`tests/conftest.py`;root = `parent/.git`
+        (gitdir 內部),三份位元組相同的副本只在 root 下、從未提交 ⇒ 不得為 `"true"`。
+        S5h-1 上失敗的原因:在 `.git/` 內 `git rev-parse --show-prefix` 以 exit 0 輸出空行 ⇒ `_root_is_toplevel`
+        True;但該處不是工作樹(`--is-inside-work-tree` 為 false),`HEAD:<path>` 與 `hash-object <path>`
+        對應的不是同一邏輯路徑 ⇒ head == worktree ⇒ identity 錯位即可取得 `"true"`(S5h-F1)。
+        """
+        parent = _g_default_root(tmp_path / "parent")
+        root = parent / ".git"
+        self._copy_into(parent, root, (_G_POLICY_FILE, "pyproject.toml", "tests/conftest.py"))
+        got = _g_coverage(root, monkeypatch)
+        assert got != "true", got
+
+    def test_i3_a_root_inside_a_bare_repository_is_not_full_coverage(self, tmp_path, monkeypatch):
+        """I2。分類:behavior-red(在 S5h-1 上必須失敗)。
+
+        以 `parent` 建 bare clone `bare.git`;root = `bare.git/proj`(bare repository 底下的普通子目錄,
+        隱式 bare 探索),三份位元組相同的副本只在 root 下、從未提交 ⇒ 不得為 `"true"`。
+        S5h-1 上失敗的原因:同 I1 —— bare 內 `--show-prefix` 為空但非工作樹,`HEAD:<path>` 與
+        `hash-object <path>` 對應的不是同一邏輯路徑(S5h-F1)。
+        """
+        parent = _g_default_root(tmp_path / "parent")
+        bare = tmp_path / "bare.git"
+        _d_git(tmp_path, "clone", "-q", "--bare", str(parent), str(bare))
+        root = bare / "proj"
+        self._copy_into(parent, root, (_G_POLICY_FILE, "pyproject.toml", "tests/conftest.py"))
+        got = _g_coverage(root, monkeypatch)
+        assert got != "true", got
+
+    def test_i3_committed_blobs_alone_is_fail_closed_for_a_subdirectory_root(self, tmp_path, monkeypatch):
+        """I3。分類:regression-lock(在 S5h-1 上必須通過)。**不經 `evidence_policy_facts`**,直接呼叫
+        `redlight.committed_blobs`。
+
+        非法 root(`parent/sub`,只有 `pyproject.toml` 與 `tests/conftest.py` 的未提交副本):`BLOB_FILES`
+        每一路徑皆 `{"worktree": None, "head": None}`;對照組 `committed_blobs(parent)`:每一路徑 worktree
+        非空且 == head。
+        目的:獨立證明 `committed_blobs` 那一半 fail-closed,不被 `evidence_policy_facts` 的 guard 間接遮蔽
+        (S5h-F2:H1 只斷言 `!= "true"`,policy 那一半先回 None 就擋住了,(xi) 那一半有沒有擋看不出來)。
+        """
+        parent = _g_default_root(tmp_path / "parent")
+        sub = parent / "sub"
+        self._copy_into(parent, sub, ("pyproject.toml", "tests/conftest.py"))
+        blobs = redlight.committed_blobs(str(sub))
+        assert set(blobs) == set(redlight.BLOB_FILES), blobs
+        assert all(v == {"worktree": None, "head": None} for v in blobs.values()), blobs
+        control = redlight.committed_blobs(str(parent))
+        assert all(v["worktree"] and v["worktree"] == v["head"] for v in control.values()), control
```
<!-- 逐字結束 -->

### E.2 `git diff ea6aba6452668982fee56f7a2f0faf2cd720ca6d..260ede30628c7d205b30ac12c94be73a75cd2812 -- tests/test_redlight.py`(3i)

<!-- 逐字開始 -->
```
diff --git a/tests/test_redlight.py b/tests/test_redlight.py
index 26da0b5..1b48694 100644
--- a/tests/test_redlight.py
+++ b/tests/test_redlight.py
@@ -2574,3 +2574,75 @@ class TestEvidenceRootIsGitToplevel:
         """
         got = _g_coverage(_g_default_root(tmp_path / "root"), monkeypatch)
         assert got == "true", got
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# 票 145 Station 3i 補紅燈 —— S5h-F1 / S5h-F2:root 必須是 Git **工作樹**的最上層(〈五十七〉57.3 裁決 2、3)
+#
+# 4h 的 `_root_is_toplevel` 只看 `git rev-parse --show-prefix` 為空。但 `.git/` 內部或 bare repository 內
+# 同樣滿足此條件,而該處並非工作樹:`HEAD:<path>` 證明的是 repository 內某個 tree 路徑,`hash-object <path>`
+# 讀的是另一個 filesystem root 底下、Git 不對應任何 tree 路徑的檔 ⇒ identity 錯位 ⇒ 內容相同即可取得 `"true"`。
+# root 必須是 Git 工作樹的最上層,不只是 repository context 中 prefix 恰為空的位置。
+# 既有 helper(`_g_default_root` / `_g_coverage` / `_G_POLICY_FILE` / `_d_git` / `redlight.committed_blobs` /
+# `redlight.BLOB_FILES`)只呼叫、不修改。
+# ─────────────────────────────────────────────────────────────────────────────
+
+class TestEvidenceRootIsInsideWorkTree:
+
+    @staticmethod
+    def _copy_into(parent, root, rels):
+        """把 `parent` 底下的 `rels` 逐一以位元組複製到 `root` 底下(只寫工作樹,不 git add / commit)。"""
+        for rel in rels:
+            dst = root / rel
+            dst.parent.mkdir(parents=True, exist_ok=True)
+            dst.write_bytes((parent / rel).read_bytes())
+
+    def test_i3_a_root_inside_the_gitdir_is_not_full_coverage(self, tmp_path, monkeypatch):
+        """I1。分類:behavior-red(在 S5h-1 上必須失敗)。
+
+        Git 最上層 `parent` 已提交合法 policy、`pyproject.toml`、`tests/conftest.py`;root = `parent/.git`
+        (gitdir 內部),三份位元組相同的副本只在 root 下、從未提交 ⇒ 不得為 `"true"`。
+        S5h-1 上失敗的原因:在 `.git/` 內 `git rev-parse --show-prefix` 以 exit 0 輸出空行 ⇒ `_root_is_toplevel`
+        True;但該處不是工作樹(`--is-inside-work-tree` 為 false),`HEAD:<path>` 與 `hash-object <path>`
+        對應的不是同一邏輯路徑 ⇒ head == worktree ⇒ identity 錯位即可取得 `"true"`(S5h-F1)。
+        """
+        parent = _g_default_root(tmp_path / "parent")
+        root = parent / ".git"
+        self._copy_into(parent, root, (_G_POLICY_FILE, "pyproject.toml", "tests/conftest.py"))
+        got = _g_coverage(root, monkeypatch)
+        assert got != "true", got
+
+    def test_i3_a_root_inside_a_bare_repository_is_not_full_coverage(self, tmp_path, monkeypatch):
+        """I2。分類:behavior-red(在 S5h-1 上必須失敗)。
+
+        以 `parent` 建 bare clone `bare.git`;root = `bare.git/proj`(bare repository 底下的普通子目錄,
+        隱式 bare 探索),三份位元組相同的副本只在 root 下、從未提交 ⇒ 不得為 `"true"`。
+        S5h-1 上失敗的原因:同 I1 —— bare 內 `--show-prefix` 為空但非工作樹,`HEAD:<path>` 與
+        `hash-object <path>` 對應的不是同一邏輯路徑(S5h-F1)。
+        """
+        parent = _g_default_root(tmp_path / "parent")
+        bare = tmp_path / "bare.git"
+        _d_git(tmp_path, "clone", "-q", "--bare", str(parent), str(bare))
+        root = bare / "proj"
+        self._copy_into(parent, root, (_G_POLICY_FILE, "pyproject.toml", "tests/conftest.py"))
+        got = _g_coverage(root, monkeypatch)
+        assert got != "true", got
+
+    def test_i3_committed_blobs_alone_is_fail_closed_for_a_subdirectory_root(self, tmp_path, monkeypatch):
+        """I3。分類:regression-lock(在 S5h-1 上必須通過)。**不經 `evidence_policy_facts`**,直接呼叫
+        `redlight.committed_blobs`。
+
+        非法 root(`parent/sub`,只有 `pyproject.toml` 與 `tests/conftest.py` 的未提交副本):`BLOB_FILES`
+        每一路徑皆 `{"worktree": None, "head": None}`;對照組 `committed_blobs(parent)`:每一路徑 worktree
+        非空且 == head。
+        目的:獨立證明 `committed_blobs` 那一半 fail-closed,不被 `evidence_policy_facts` 的 guard 間接遮蔽
+        (S5h-F2:H1 只斷言 `!= "true"`,policy 那一半先回 None 就擋住了,(xi) 那一半有沒有擋看不出來)。
+        """
+        parent = _g_default_root(tmp_path / "parent")
+        sub = parent / "sub"
+        self._copy_into(parent, sub, ("pyproject.toml", "tests/conftest.py"))
+        blobs = redlight.committed_blobs(str(sub))
+        assert set(blobs) == set(redlight.BLOB_FILES), blobs
+        assert all(v == {"worktree": None, "head": None} for v in blobs.values()), blobs
+        control = redlight.committed_blobs(str(parent))
+        assert all(v["worktree"] and v["worktree"] == v["head"] for v in control.values()), control
```
<!-- 逐字結束 -->

### E.3 `git diff 260ede30628c7d205b30ac12c94be73a75cd2812..8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8 -- .claude/hooks/redlight.py tests/test_redlight.py`(4i)

<!-- 逐字開始 -->
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
<!-- 逐字結束 -->

### E.4 `git show 8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8:.claude/hooks/redlight.py` 的三段函式全文

#### E.4.1 `_root_is_toplevel`(第 726–742 行)

<!-- 逐字開始 -->
```
def _root_is_toplevel(root):
    """root 是否就是 git 工作樹的最上層:須同時 `--is-inside-work-tree` 為 true 且 `--show-prefix` 為空
    (票 145 Station 4i,S5h-F1:gitdir / bare repository 內 `--show-prefix` 同樣為空,但不是工作樹)。
    任一查詢失敗或條件不符 ⇒ False。"""
    import subprocess
    try:
        proc = subprocess.run(["git", "-C", os.fspath(root), "rev-parse",
                               "--is-inside-work-tree", "--show-prefix"],
                              capture_output=True, timeout=30)
    except Exception:
        return False
    if proc.returncode != 0:
        return False
    lines = proc.stdout.split(b"\n")
    if len(lines) < 2:
        return False
    return lines[0].strip() == b"true" and lines[1].strip() == b""
```
<!-- 逐字結束 -->

#### E.4.2 `committed_blobs`(第 745–772 行)

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

#### E.4.3 `evidence_policy_facts`(第 851–897 行)

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

出處一律為 REVIEW_HEAD(`36c978e1c20a51d40cac777dd5aee58625f97032`)。

### F.0 I1 / I2 / I3 紅綠定位表(非逐字;每格附 F.2 / F.1 出處行號)

F.1 / F.2 的行號 = REVIEW_HEAD 上該檔的行號(本包 F.1 / F.2 逐字段與之逐行對應)。

| 測試 | S3I1 上的固定全套 | S4I1(TARGET)上的固定全套 |
|---|---|---|
| I1 `tests/test_redlight.py::TestEvidenceRootIsInsideWorkTree::test_i3_a_root_inside_the_gitdir_is_not_full_coverage`(behavior-red;F.2 第 43 行) | **failed**:F.2 第 59–61 行 `assert got != "true", got` / `AssertionError: true` / `assert 'true' != 'true'`、第 63 行 `tests\test_redlight.py:2613: AssertionError`、第 80 行 `FAILED …test_i3_a_root_inside_the_gitdir_is_not_full_coverage`、第 82 行摘要 `2 failed, 2097 passed, 3 skipped, 3 xfailed`;第 85 行「FAILED 恰為 I1、I2」 | **passed**:F.1 第 93 行摘要 `2099 passed, 3 skipped, 3 xfailed`(0 failed);第 96 行「0 failed;輸出沒有任何 `FAILED` / `ERROR` 行」;第 97 行「I1 / I2 由紅轉綠」 |
| I2 `tests/test_redlight.py::TestEvidenceRootIsInsideWorkTree::test_i3_a_root_inside_a_bare_repository_is_not_full_coverage`(behavior-red;F.2 第 44 行) | **failed**:F.2 第 70–72 行(同上三行)、第 74 行 `tests\test_redlight.py:2629: AssertionError`、第 81 行 `FAILED …test_i3_a_root_inside_a_bare_repository_is_not_full_coverage`、第 82 行摘要 | **passed**:F.1 第 93 行摘要(0 failed);第 97 行「I1 / I2 由紅轉綠」 |
| I3 `tests/test_redlight.py::TestEvidenceRootIsInsideWorkTree::test_i3_committed_blobs_alone_is_fail_closed_for_a_subdirectory_root`(regression-lock;F.2 第 45 行) | **passed**:F.2 第 85 行「I3、H1、H2 在 2097 passed 之內」;第 80–81 行的 FAILED 清單只有 I1、I2 | **passed**:F.1 第 93 行摘要(0 failed);第 97 行「I3 / H1 / H2 維持綠」 |

POSIX 旁證(裁決助手;非本 repo 帳本證據):F.1 第 221 行「修正前 … I1 / I2 失敗於 got == "true"、I3 通過」。

### F.1 `docs/audits/2026-10-05-m1a-station4i-fix.md` 全文

行號來源:REVIEW_HEAD 的該檔第 1–229 行

<!-- 逐字開始 -->
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
<!-- 逐字結束 -->

### F.2 `docs/audits/2026-10-05-m1a-station3i-redlight.md` 全文

行號來源:REVIEW_HEAD 的該檔第 1–125 行

<!-- 逐字開始 -->
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
<!-- 逐字結束 -->

---

## G. 審查重點

<!-- 逐字開始 -->
G1 修正是否封住 S5h-F1：_root_is_toplevel 同時要求 --is-inside-work-tree 為 true 且 --show-prefix 為空；指令失敗 / 例外 / 非零 returncode / 輸出少於兩行 / 任一條件不符是否一律 False（fail-closed）。
G2 stdout 解析的健壯性：split(b"\n") 後 lines[0] / lines[1] 的取法在 CRLF（\r\n）、尾端多餘換行、git 版本差異下是否仍正確；是否可能在正常最上層誤回 False（fail-closed 但會封死正常 host；若有，須指出）。
G3 不變式未削弱：本輪只改 _root_is_toplevel 一個函式（以 D.2 全範圍 name-only + E.1 / E.3 驗）；committed_blobs / evidence_policy_facts 的呼叫處、consumer、policy_state、content_hash 及其呼叫鏈、conftest、status.py / install.py / verify_gates.py 皆未改。
G4 紅綠時序：I1 / I2 在 S3I1 為 red（失敗於 got == "true"）、I3 為 green；S4I1 後三者 green（見 F 段定位表與 F.2 / F.1 原文），不得只看最終全綠。
G5 三支測試是否真的測到宣稱的形狀：I1 的 root = <最上層>/.git、I2 的 root = <bare clone>/proj，副本從未提交、經真實 conftest producer；I3 直接呼叫 committed_blobs（不經 evidence_policy_facts）、對照組為最上層。
G6 5g / 5h 的其他結論是否仍成立：本輪改動是否影響 5h 報告 G1 / G2 / G7 / G9 以外的任何結論，以及 5g 報告的 13 題；S5g-F1 / F3 / F4 / F5、S5h-F3 / F4 追蹤項狀態是否正確（仍未 machine-enforced）。
G7 殘餘措辭與程式一致：證據報告寫「若 Git 對該 root 實際回報 --is-inside-work-tree=true 且 --show-prefix 為空即會被接受；其 HEAD 與工作樹是否符合 identity invariant 本輪未完整 acceptance」—— 是否與 _root_is_toplevel 的實際行為一致，且沒有宣稱已拒絕或已支援任何未測的佈局。
G8 跨平台：--is-inside-work-tree 與 --show-prefix 合併輸出在 Windows / POSIX 下的行序與行尾是否一致；是否存在 git 版本讓 --is-inside-work-tree 在工作樹最上層回報非 true。
G9 總問題（增量版）：在 TARGET 上，是否仍存在任何路徑，讓 root 的 canonical policy 沒有提交在「Git 對該 root 實際解析出的 repository / HEAD」中，卻能取得 file_coverage == "true"（判準同 5h G9：要抓的是工作樹所用物件與 HEAD 所證明物件的 identity 錯位）；請在 5h 第 4 節總表 18 項的基礎上重新檢查（特別是 #3–#6 現在是否被擋），並主動構造新反例（含：--is-inside-work-tree 回 true 但 --show-prefix 為空的非最上層情境是否存在、core.worktree 指向他處、GIT_WORK_TREE 指向 root 本身但 GIT_DIR 指向他處的 repo），找不到也要列出檢查過的路徑。
<!-- 逐字結束 -->

---

## H. 已知殘餘與追蹤項

出處:F.1 的「殘餘與未證明」一節,即 REVIEW_HEAD 的 `docs/audits/2026-10-05-m1a-station4i-fix.md` 第 199–205 行。

<!-- 逐字開始 -->
### 7. 殘餘與未證明(目前尚未 machine-enforced)

1. 沿用 4h 證據報告(`docs/audits/2026-10-05-m1a-station4h-fix.md`)第 7 節全部項目(含其沿用的 4g 第 8 節),不擴張。
2. 5g 追蹤項:S5g-F1(下一張票優先)、S5g-F3、S5g-F4、S5g-F5;5h 追蹤項:S5h-F3(本節第 3 點已補準措辭)、S5h-F4(併入 S5g-F1 類的 operator / status 追蹤項)。
3. 本輪依 S5h-F3 補準的殘餘措辭(照錄):
   「本輪檢查的語意是 git rev-parse --is-inside-work-tree 為 true 且 --show-prefix 為空，即 root 必須是 Git 對該 root 解析出的工作樹的最上層。明確不支援（⇒ unknown）：monorepo 中非最上層的普通子目錄（H1）、位於 gitdir 或 bare repository 內的 root（I1 / I2）。會被接受但本輪未納入 acceptance、屬未證明：巢狀獨立 Git repo、submodule、linked worktree（git worktree add）、.git 為檔案且 gitdir 指向他處、GIT_DIR / GIT_WORK_TREE / core.worktree 等重新對應佈局。上述佈局若 Git 對該 root 實際回報 --is-inside-work-tree=true 且 --show-prefix 為空，即會被本檢查接受；其 HEAD 與工作樹是否符合既定 identity invariant，本輪未完整 acceptance，不得宣稱已拒絕或已支援。」
4. 本機只驗 Windows。（S4I4 後更新：POSIX 已 PASS，見第 9 節；屬裁決助手外部驗證，非本 repo 帳本證據。）
<!-- 逐字結束 -->

**註**:上列追蹤項目前尚未 machine-enforced。
