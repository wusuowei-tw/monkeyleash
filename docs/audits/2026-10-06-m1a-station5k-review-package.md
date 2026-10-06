# M1-a Station 5k 增量獨立審查包(票 145)

**審查對象(TARGET,本輪最後一個程式 commit)**:`c1eebd97ed197d7f653fbc1c680a0feca1837c6a`(S4K1B;含 S4K1)
**審查 HEAD(REVIEW_HEAD;review baseline)**:`95cd4490f181537e530be516d7ef61c5f7c3e587`
**審查範圍**:只審 3k / 4k 增量(TARGET_J → TARGET)與 S6-2 的根因推定措辭。5g / 5h / 5i / 5j 已審過 TARGET_J 之前的內容。

本包只是材料,不含任何審查結論。所有逐字段落皆以 `<!-- 逐字開始 -->` / `<!-- 逐字結束 -->` 標出邊界,
邊界之間的文字與標示的出處逐位元組相同(換行一律 LF)。
D 段與 E 段的逐字範圍是邊界內 ```` ``` ```` 圍籬**之間**的全部行(圍籬本身不屬於出處內容)。
E 段為 `git diff` / `git show` / `git grep` 原樣,**未去除行尾空白**(diff 的空白 context 行是單一空格)。
B、C、F、H 段的出處本身含有 ```` ``` ```` 圍籬或 markdown 標題;這些段不另加圍籬,邊界以該段標示的出處行號為準。
G 段的出處是裁決者的 Station 5k-0 指令原文(不在任何 repo 檔案內)。

---

## A. 身分與規則

### A.1 身分

| 代號 | 完整 SHA | 說明 |
|---|---|---|
| **BASE_J** | `774e7351e07ebdfc267a37b58bc09579e1de5646` | 5j 審查 HEAD(S5j-1) |
| **TARGET_J** | `d4b6fafd4afdd70121278527194aeef4097bff33` | 5j 審過的最後程式 commit(S4J1) |
| S6-2 | `0904cdbc3eafeb71a27c266cdd11ae151f21fb67` | push 紀錄、CI 淨室 FAIL、3k 裁決(docs;由 5j 審查視窗提交) |
| S3K1 | `b0849792ff3e69df70cdd8a5d77d26af78d79021` | K-a/K-b/K-c/K-d/K-e 紅燈(tests) |
| S3K2 | `16d29f7ee84c746f845d071e13dce93b85e26fb2` | 3k 證據(docs) |
| S4K1 | `492b5de438ef9a306b112ac1fbc402729e219879` | KNOWN_DISTS 納入 anyio 4.15.1(redlight.py) |
| **TARGET**(S4K1B) | `c1eebd97ed197d7f653fbc1c680a0feca1837c6a` | 宿主 policy dists 納入 4.15.1(json)—— **審查對象**(含 S4K1) |
| S4K3 | `9fbfeb9210455f0485365fec7a7125456bc8da7a` | 4k 本機驗收證據(docs) |
| **REVIEW_HEAD**(S4K4) | `95cd4490f181537e530be516d7ef61c5f7c3e587` | POSIX(真裝 4.15.1)驗收記錄、4k 升級(docs);review baseline |

- 本包所在的 commit(S5k-0)是 REVIEW_HEAD **之後**才建立的 docs-only commit;本包寫不進自己的 SHA,由裁決者交付審查時另附。S5k-0 **不屬於審查對象**。
- **CODE_FILES**(`git diff --name-only <TARGET_J>..<TARGET>` 中所有非 docs/ 的檔,3 個):`.claude/hooks/redlight.py` `tests/test_redlight.py` `.agents/evidence-policy.json`。
- **程式 commit**(3 個):S3K1、S4K1、S4K1B。
- TARGET 之後到 REVIEW_HEAD 只改 docs/。

建包時核對(原文輸出;各自單獨執行,全部以完整 SHA 為錨點):

```
$ git merge-base --is-ancestor 774e7351e07ebdfc267a37b58bc09579e1de5646 95cd4490f181537e530be516d7ef61c5f7c3e587
(無輸出;exit 0)
$ git rev-list --count 774e7351e07ebdfc267a37b58bc09579e1de5646..95cd4490f181537e530be516d7ef61c5f7c3e587
7
$ git diff --name-only d4b6fafd4afdd70121278527194aeef4097bff33..c1eebd97ed197d7f653fbc1c680a0feca1837c6a
.agents/evidence-policy.json
.claude/hooks/redlight.py
docs/audits/2026-10-05-m1a-station3k-redlight.md
docs/audits/2026-10-05-m1a-station4i-fix.md
docs/audits/2026-10-05-m1a-station4j-fix.md
docs/audits/2026-10-05-m1a-station5j-review-package.md
docs/audits/2026-10-05-m1a-station5j-review.md
docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
tests/test_redlight.py
$ git diff --name-only c1eebd97ed197d7f653fbc1c680a0feca1837c6a..95cd4490f181537e530be516d7ef61c5f7c3e587
docs/audits/2026-10-05-m1a-station4k-fix.md
docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
```

`git diff --name-only <TARGET_J>..<TARGET>` 全文亦見 D.2。

### A.2 審查者規則

1. **身分**:4g 實作 session、本輪實作 session(3h 起至 5k-0)、5g / 5h / 5i / 5j 審查 session、以及提交 S6-2 的那個 5j 審查視窗,皆不得擔任 5k 審查者;5k 須在第六個全新對話進行。
2. **唯讀**:不改任何檔案、不 commit、不推、不改 `.dev/pipeline.json`。審查報告只寫到 `.scratch/m1a-s5k/review-report.md`(用 Write),不寫其他位置。
3. **禁止 pytest**(含 `--collect-only`、`--version`)、`verify_gates.py` 與 `status.py`。帳本(`.dev/test-runs.jsonl`、`.dev/test-sessions.jsonl`)會被任何 pytest 執行追加,審查不得污染證據。需要驗證行為時,讀程式碼做紙上推演;必須實跑才能確定者,寫成「需要重現」並描述最小重現方式。
4. **查詢一律綁定 A.1 的完整 SHA**;不以 `HEAD`、`HEAD~n`、遠端追蹤分支、本地分支名、短 SHA 或工作樹當下狀態為錨點。範例:

```
git show c1eebd97ed197d7f653fbc1c680a0feca1837c6a:<路徑>
git diff d4b6fafd4afdd70121278527194aeef4097bff33..c1eebd97ed197d7f653fbc1c680a0feca1837c6a -- <路徑>
git log --oneline 774e7351e07ebdfc267a37b58bc09579e1de5646..95cd4490f181537e530be516d7ef61c5f7c3e587
git show 95cd4490f181537e530be516d7ef61c5f7c3e587:docs/audits/2026-10-05-m1a-station4k-fix.md
```

5. **逐字段的邊界以各段標示的出處行號為準**(不以段內標題或圍籬判斷)。
6. 可用 Read / Grep 讀本機已安裝的 pytest / pluggy 原始碼與 git 文件;引用只寫 `_pytest/<檔名>:<行號>` 等相對形式,不寫本機絕對路徑。
7. **照錄任何系統訊息、錯誤訊息或路徑前,先把本機使用者名稱遮成 `<user>`。**
8. 被任何閘門(R1–R9、pre-commit、洩漏偵測)擋下:停手回報,不換工具、不繞過。
9. **結論只能是 `PASS` 或 `FAIL`**;finding 須標嚴重度,並附 `<TARGET>:<路徑>:<行號>` 形式的證據(以 TARGET 為準)。沒有檔名與行號證據的發現不計入判定。
10. **範圍**:5g / 5h / 5i / 5j 已審過 TARGET_J 之前的內容,本輪只審增量;但若增量使 5g–5j 的任何結論失效,須指出。
11. G 段 G1–G10 每一題都必須回答(「無問題」也要附證據);不能回答的,寫明「無法判定」與原因,不得略過。
12. 不得用 python -c、heredoc 或把程式碼放進指令字串。
13. **不得讀取本機 AI 對話紀錄檔**;兩本帳本只准 `sha256sum` / `wc`,不得開啟內容。
14. **範圍聲明**:只審 3k / 4k 增量與 S6-2 的根因推定措辭;相依漂移的機制化不在本票範圍,列追蹤項而非 FAIL,除非增量讓「邊界外 dist 仍可得 file_coverage == "true"」成立。
15. 審查者本機 anyio 若為 4.15.0,無法實裝 4.15.1 驗證行為;該部分依 F.1 第 9 節外部證據做紙上核對,無法判定者寫「需要重現」。

---

## B. 裁決與背景(逐字)

出處一律為 `95cd4490f181537e530be516d7ef61c5f7c3e587:docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md`(以下稱「REVIEW_HEAD 的票 145」)。

### B.1 〈六十五〉Station 6(第二次)push 紀錄、CI 淨室驗證 FAIL 與 Station 3k 裁決

行號來源:REVIEW_HEAD 的票 145 第 3292–3336 行

<!-- 逐字開始 -->
## 六十五、Station 6（第二次）push 紀錄、CI 淨室驗證 FAIL 與 Station 3k 裁決（2026-10-05，Jeff）

### 65.1 push

- 2026-10-05(美東)Jeff 說「推」;`git push origin master` 一次、未被擋。
- `git ls-remote origin refs/heads/master` = `774e7351e07ebdfc267a37b58bc09579e1de5646`(= S5j-1)。
- 證據報告:`.dev/reports/2026-10-06T002652Z-ticket145-station6b-push-ci.md`(未入庫)。
- 本機無 `gh`,CI 由裁決助手以瀏覽器讀取公開 checks 頁取得。

### 65.2 CI(外部證據;來源:Jeff 轉述裁決助手讀取公開 checks 頁)

- workflow `tests` / job `pytest`。
- run:https://github.com/wusuowei-tw/monkeyleash/actions/runs/37393958765
- job:https://github.com/wusuowei-tw/monkeyleash/actions/runs/37393958765/job/112045357993
- headSha `774e7351e07ebdfc267a37b58bc09579e1de5646`;結果 **failed**(1m 34s)。
- 步驟:Set up job ✓ / checkout ✓ / setup-python ✓ / 安裝相依 ✓ / 接上權威層 ✓ / 跑測試 ✓ / 收集清單（票 85）✓ / **淨室驗證（每條規則各擋一次 + 安裝後形態）✗** / Complete job ✓。
- Annotation:`Process completed with exit code 1`。
- 完整 log 需登入,未取得;**CI 實際安裝的套件版本尚未取得 log 直接核驗**。

### 65.3 根因推定(來源:Jeff 轉述裁決助手隔離 Linux 重現;非本 repo 帳本證據)

- 公開 checks 顯示 CI「跑測試」通過、「淨室驗證」失敗。
- 隔離 Linux 環境以全新 venv 依 CI 方式 `pip install -e ".[dev]"`,實際安裝 anyio 4.15.1(PyPI 2026-09-05 發布;anyio 為 mcp / httpx 的間接相依,未釘版),可重現 verify_gates 正二「已初始化且相符」不成立(`file_coverage=unknown`、exit 1);同一 commit 在 anyio 4.15.0 對照環境下正二成立、exit 0。
- 機制:`redlight.py` 的 `KNOWN_DISTS` 與 `.agents/evidence-policy.json` 的 `dists` 只有 `("anyio","4.15.0")` ⇒ 4.15.1 的 anyio plugin 判為未盤點(other)⇒ unknown。
- 據此**推定** CI 失敗與 anyio 版本超出邊界有關;CI 實際安裝版本尚未取得 log 直接核驗。
- wheel 比對(外部來源):anyio-4.15.0 sha256 `7ecd9937369ffce8bba0b5ccb9b3a9507b101b0ed50256aecfbab27e6c2acb99`、anyio-4.15.1 sha256 `6152fdbbf9a77fdec97731721bebf7c4c44f7c29b424b0065826173efc7ed101`;`anyio/pytest_plugin.py` 與 `entry_points.txt` 逐位元組相同,差異僅 `anyio/__init__.py`、`anyio/_lazyimport.py`(檔案相同不等於行為等價;真實 4.15.1 環境的行為驗收於 4k 另行記錄)。

### 65.4 分類

- 精確版本能力邊界與乾淨環境相依漂移(`KNOWN_DISTS` 為精確版本 pin;乾淨環境自動取得新版即落在邊界外)。
- 不是 3j / 4j 的回歸;亦非 S5g-F3(pytest 9 設定格式)或 S5g-F4(Git clean filter)。
- 本輪為外部重現確認的第一個邊界外案例;追蹤項:相依漂移的機制化(目前尚未 machine-enforced;見「相關」)。

### 65.5 Jeff 裁決(2026-10-05)

1. Station 6(第二次)= push PASS、CI FAIL。
2. 選 A(擴大能力邊界,邊界跟著證據長);B(釘 `anyio==4.15.0`)保留為環境重現策略、不採用;C(削弱正二)不採用。
3. 回 Station 3k:紅燈分「能力」與「policy」兩層,保留負控(負控直接斷言 unknown)。
4. 4k 須在真裝 anyio 4.15.1 的乾淨環境證明正二成立(裁決助手 POSIX,另行記錄)。
5. 5k 增量審查;再回 Station 6 第三次 push / CI。

### 65.6 commit

- S6-2(本節)`0904cdbc3eafeb71a27c266cdd11ae151f21fb67`。
  (F-036:本行原文為「S6-2(本節)於下一次提交回填。」;2026-10-05 於 S3K2 回填。)
<!-- 逐字結束 -->

### B.2 〈六十六〉Station 3k 紅燈證據

行號來源:REVIEW_HEAD 的票 145 第 3340–3366 行

<!-- 逐字開始 -->
## 六十六、Station 3k 紅燈證據

- 合約:〈六十五〉65.5 裁決 2、3(選 A 擴大能力邊界;紅燈分「能力」與「policy」兩層,保留負控)。
- 報告:`docs/audits/2026-10-05-m1a-station3k-redlight.md`。
- S3K1 `b0849792ff3e69df70cdd8a5d77d26af78d79021`:`tests/test_redlight.py` 檔尾一個 hunk `@@ -2750,0 +2751,42 @@`,只有 + 行;新增 `class TestKnownDistBoundaryAnyio4151`,既有 helper(`_g_root` / `_g_policy` / `_g_policy_text` / `_g_coverage`)只呼叫、不修改。commit 前只跑 py_compile。
- 新增 5 支(K-e 參數化 2 案,共 6 個 nodeid):

| 代號 | nodeid | 分類 | S3K1 全套 |
|---|---|---|---|
| K-a | `tests/test_redlight.py::TestKnownDistBoundaryAnyio4151::test_k3_anyio_4151_is_a_known_dist` | constant-lock(red) | failed(`:2767`) |
| K-b | `tests/test_redlight.py::TestKnownDistBoundaryAnyio4151::test_k3_a_committed_policy_accepting_4151_with_a_4151_plugin_is_full_coverage` | behavior-red | failed(`:2773`) |
| K-c | `tests/test_redlight.py::TestKnownDistBoundaryAnyio4151::test_k3_a_host_policy_without_4151_is_unknown` | negative-lock | passed |
| K-d | `tests/test_redlight.py::TestKnownDistBoundaryAnyio4151::test_k3_an_uninventoried_version_is_unknown` | negative-lock | passed |
| K-e[4.15.0] | `tests/test_redlight.py::TestKnownDistBoundaryAnyio4151::test_k3_a_policy_listing_both_versions_accepts_each[4.15.0]` | behavior-red | failed(`:2792`) |
| K-e[4.15.1] | `tests/test_redlight.py::TestKnownDistBoundaryAnyio4151::test_k3_a_policy_listing_both_versions_accepts_each[4.15.1]` | behavior-red | failed(`:2792`) |

- 紅燈全套(在 S3K1 上只跑一次;Windows;外來 3 檔已 stash,跑前跑後 `git status --porcelain` 皆無輸出):exit 1;
  摘要行原文 `4 failed, 2106 passed, 4 skipped, 3 xfailed in 246.14s (0:04:06)`(collected 2117)。FAILED 恰為 K-a、K-b、K-e[4.15.0]、K-e[4.15.1];K-c / K-d 在 passed 之內。
  K-a 失敗於 `assert ('anyio', '4.15.1') in (('anyio', '4.15.0'),)`;K-b / K-e 失敗於 `assert 'unknown' == 'true'`。
- 帳本只追加:兩本前段 sha256 = V0(`22148446…` / `3d7cde59…`);test-runs 3344 → 3391 行(+47)、test-sessions 34 → 35 行(+1)。
  跑後全檔記為 V1:test-runs 903816 bytes、`0edb6cd32349bf5477a5f1adef2e59188d91de8841239565a467b5fc39c56285`;
  test-sessions 18095023 bytes、`75c4580bc54324b90391ccee222647a4933549872154e2af41c2aaaffe405763`。
- status:`tests red under ticket 145: tests/test_redlight.py`(4k 過 R3 的本機紅燈);`evidence policy: 有效`。
- 裁決助手 Linux 預演(外部來源;非本 repo 帳本證據):同一組測試在 S4J1 碼上 4 紅 2 綠,KNOWN_DISTS 加 4.15.1 後 tests/test_redlight.py 153 passed。
- 程序:S6-2 由 5j 審查視窗提交;本站回原實作視窗。5j 審查視窗不得再擔任任何審查者;5k 須開第六個全新對話。
- commit:S3K1 `b0849792ff3e69df70cdd8a5d77d26af78d79021`;S3K2(本節與證據報告)`16d29f7ee84c746f845d071e13dce93b85e26fb2`。
  (F-036:本行原文為「S3K2(本節與證據報告)於下一次提交回填。」;2026-10-06 於 S4K3 回填。)
<!-- 逐字結束 -->

### B.3 〈六十七〉Station 4k 修正

行號來源:REVIEW_HEAD 的票 145 第 3370–3404 行

<!-- 逐字開始 -->
## 六十七、Station 4k 修正

### 67.1 裁決(照錄要點;Jeff)

- 〈六十五〉65.5 裁決 A:擴大能力邊界(邊界跟著證據長);B(釘 `anyio==4.15.0`)與 C(削弱正二)不採用。
- 4k 只改 `.claude/hooks/redlight.py` 第 486 行一處與 `.agents/evidence-policy.json` 的 `dists` 一筆;不改任何測試。
- 三段式:S4K1 / S4K1B 實作 → S4K2 本機驗收 → S4K3 docs-only(只能宣稱本機驗收通過;待 POSIX 外部驗收(真裝 anyio 4.15.1))。
- 〈六十五〉65.5 裁決 4:4k 須在真裝 anyio 4.15.1 的乾淨環境證明正二成立(裁決助手 POSIX,另行記錄)。

### 67.2 證據

- 報告:`docs/audits/2026-10-05-m1a-station4k-fix.md`。
- S4K1 `492b5de438ef9a306b112ac1fbc402729e219879`:`.claude/hooks/redlight.py` 一個 hunk `@@ -486 +486,3 @@`(+3 / −1),`KNOWN_DISTS = (("anyio", "4.15.0"), ("anyio", "4.15.1"))`,上方加兩行註解;Edit 未被 R3 擋(本機紅燈 = S3K1);寫入後 py_compile 與 status 探針正常。
- S4K1B `c1eebd97ed197d7f653fbc1c680a0feca1837c6a`:`.agents/evidence-policy.json` 一行 `"dists": [["anyio", "4.15.0"], ["anyio", "4.15.1"]]`(+1 / −1)。
- S4K2 本機固定全套(S4K1B 上只跑一次;Windows;外來 3 檔已 stash):exit 0;`2110 passed, 4 skipped, 3 xfailed in 296.19s (0:04:56)`(collected 2117、0 failed)。K-a / K-b / K-e[4.15.0] / K-e[4.15.1] 由紅轉綠,K-c / K-d 維持綠。
- 帳本只追加:前段 sha256 = V1;test-runs 3391 → 3438(+47)、test-sessions 35 → 36(+1)。
  跑後全檔記為 V2:test-runs 915335 bytes、`3637077aea4d2bdaa3138bf9b2aa28b5306ab9e9bc317d04df78ddfee3382778`;
  test-sessions 18838751 bytes、`6d18a5c6567054da5f2d09d7655b8aa29129c34cbf948be69e8a9c58d09dddcd`。
- status:`evidence policy: 有效`;`tests red under ticket 145: (無)`;最近一次 run A(exit 0;collected 2117 / passed 2110 / failed 0)。
- 淨室(verify_gates;本機 anyio 4.15.0):R1–R9 各擋下一次、淨室框架測試 `1960 passed, 8 skipped, 3 xfailed`;兩正三負全部成立,正二 `file_coverage=true`;本 repo 兩本帳本前後 = V2。**此淨室不證明真裝 4.15.1 的正二。**
- 殘餘與未證明(目前尚未 machine-enforced):沿用 4j 證據報告第 7 節;相依漂移(KNOWN_DISTS 仍為精確版本 pin,下一次相依升版會再落在邊界外;見「相關」追蹤項)。
- commit:S4K1 `492b5de438ef9a306b112ac1fbc402729e219879`;S4K1B `c1eebd97ed197d7f653fbc1c680a0feca1837c6a`;S4K3 `9fbfeb9210455f0485365fec7a7125456bc8da7a`(本節與證據報告)。
  (F-036:原文「~~S4K3(本節與證據報告)於下一次提交回填。~~」;2026-10-06 於 S4K4 回填,理由:S4K3 SHA 於提交後才確定。)

### 67.3 POSIX 外部 clean-room 驗收(真裝 anyio 4.15.1)

> **舊文字(F-036,保留不刪)**:~~待執行(裁決助手)。~~
> —— 2026-10-06 由 S4K4 的 POSIX 驗收紀錄取代。

- 來源：Jeff 轉述裁決助手 2026-10-06 Linux 證據（隔離沙盒；git 2.43.0；Python 3.11.16；全新 venv 依 CI 方式 pip install -e ".[dev]" 實際安裝 anyio 4.15.1、pytest 9.1.1；非本 repo 帳本證據；本 repo 兩本帳本未動）。
- 受測物：S4K1B 的 .claude/hooks/redlight.py（blob 0fe2f7ab0e600a18db1079462db80eddee6eae13，sha256 30ee60f9e501788ee2e3a065f0bfc4725d9258fd3f2cdb68288719c7382d30ed，與本機 S4K2 run 紀錄 impl_hash 相同）、tests/test_redlight.py（blob e9f4c82e6b879db998f9ebe8289aa458b1475c9f = S3K1）、.agents/evidence-policy.json（blob 82669a8c0f0c59eaf8b507e00639b9700aafb172）。置於全新 clone、提交後工作樹乾淨、歷史完整（unshallow）。
- verify_gates.py 淨室（anyio 4.15.1 實裝）：R1–R9 各擋下一次、權威層偵測三項成立、框架測試 1964 passed, 4 skipped, 3 xfailed；兩正三負全部成立，正二 file_coverage=true、green=tests/test_evidence_probe.py；exit 0。對照：S4J1 碼在同一 venv 下正二不成立 ✗、exit 1（〈六十五〉65.3 的重現）。
- 6 支 K 測試（TestKnownDistBoundaryAnyio4151）全 passed；evidence 相關 5 檔 1 failed, 963 passed：唯一 failed 為先前 4g–4j 各次 POSIX 驗收亦出現的 tests/test_gate.py::TestAuthorityLayerIsWired::test_this_repo_itself_is_wired；環境性原因仍屬推定，尚未獨立核驗。淺層 clone 時另有 4 支 R6 相關失敗，git fetch --unshallow 後消失，對應 CI workflow fetch-depth: 0 的既有註解，判為 clone 深度所致而非回歸（同屬推定）。
- 固定全套：13 failed, 2101 passed, 3 xfailed（collected 2117）；13 個 failed 與 4j POSIX 驗收那次逐字相同（test_gate 1 + test_known_items_regression 12），可支持「未新增該類失敗」，環境性根因仍屬推定、尚未獨立核驗或 machine-enforced。
- Jeff 裁決（2026-10-06）：Station 4k = PASS / COMPLETED（Windows 本機 + POSIX 外部 clean-room，真裝 anyio 4.15.1）；待 Station 5k 獨立審查（第六個全新對話）。CI 是否轉綠仍須 Station 6 第三次 push 後由 CI 本身證明。
<!-- 逐字結束 -->

---

## C. 5j 審查報告的追蹤項(逐字)

出處:`95cd4490f181537e530be516d7ef61c5f7c3e587:docs/audits/2026-10-05-m1a-station5j-review.md`(以下稱「5j 審查報告」)。供 G6 核對追蹤項狀態;相依漂移的來源是票〈六十五〉65.4 與 4k 證據報告第 7 節(B.1、H),不在此節。

### C.1 第 6 節「追蹤項建議」全文

行號來源:5j 審查報告第 270–278 行

<!-- 逐字開始 -->
## 6. 追蹤項建議(都不構成 FAIL;全部**目前尚未 machine-enforced**)

1. **舊版 git 的最上層輸出**:2.43.0 以前是否一定輸出 `true\n\n`,本審查沒有版本證據(G2)。不符時的方向是 fail-closed(封死正常 host)。
2. **GIT_DIR / GIT_WORK_TREE / core.worktree 重新對應佈局**(X5、X6;5h #11、#13):會被接受,依判準不構成 F2,4j §7.4 已列為未證明。補充:git hook 的執行環境會匯出 `GIT_DIR` 等變數,producer 若在 hook 內被呼叫,會繼承它(5h #11 已註「conftest 子行程會繼承環境變數」)。
3. **linked worktree / submodule / gitfile 佈局**(X7;5h #7–#10):接受,沒有 acceptance 測試。
4. **S5i-F3(b) 殘留**(S5j-F2):J2[bare] 在 `safe.bareRepository=explicit` 下空洞通過;建議在 4j §7.3 改回「部分處理」,或補一個以 `-c safe.bareRepository=all` 固定設定的 bare 案例。
5. **TOCTOU**:`_root_is_toplevel` 與後續 `hash-object` / `rev-parse HEAD:` 之間的佈局競態,本輪無法判定,非本輪引入。
6. **4i 報告 §7.3 指向**(S5j-F1):在 4i 報告該點加一行「已由 4j 報告 §7 第 4 點取代」。
7. 流程教訓「R3 與 POSIX-only 紅燈」(4j §7.3 已列)—— 本審查確認那條路徑沒有繞過 R3(G4),不另加。
<!-- 逐字結束 -->

---

## D. 本輪 commit 與檔案範圍

### D.1 `git log --oneline 774e7351e07ebdfc267a37b58bc09579e1de5646..95cd4490f181537e530be516d7ef61c5f7c3e587`(7 筆,與 A.1 的 S6-2…S4K4 逐一對應)

<!-- 逐字開始 -->
```
95cd449 docs(145): M1-a Station 4k-4 —— POSIX 外部 clean-room（真裝 anyio 4.15.1）驗收通過，4k = PASS / COMPLETED；待 5k 審查
9fbfeb9 docs(145): M1-a Station 4k-3 —— KNOWN_DISTS anyio 4.15.1 的本機驗收證據（待 POSIX 真裝 4.15.1 驗收）
c1eebd9 fix(145): M1-a Station 4k-1b —— 宿主 evidence policy dists 納入 anyio 4.15.1（B ∩ H，兩版皆在 B 內）
492b5de fix(145): M1-a Station 4k-1 —— KNOWN_DISTS 納入 anyio 4.15.1（能力邊界跟著證據長；S6 CI 淨室 FAIL）
16d29f7 docs(145): M1-a Station 3k-2 —— 紅燈證據（KNOWN_DISTS anyio 4.15.1；K-a/K-b/K-e 紅、K-c/K-d 綠）
b084979 test(145): M1-a Station 3k-1 —— 能力邊界 KNOWN_DISTS 納入 anyio 4.15.1 的紅燈（K-a/K-b/K-e 紅、K-c/K-d 負控；6 支）
0904cdb docs(145): M1-a Station 6-2 —— push 紀錄、CI 淨室驗證 FAIL（推定 anyio 4.15.1 超出 KNOWN_DISTS）與 Station 3k 裁決
```
<!-- 逐字結束 -->

### D.2 `git diff --name-only d4b6fafd4afdd70121278527194aeef4097bff33..c1eebd97ed197d7f653fbc1c680a0feca1837c6a`(NAMEONLY_FULL;TARGET_J..TARGET 全範圍)

這是「CODE_FILES 以外的非 docs 檔(conftest、status.py、install.py、verify_gates.py 等)都沒變」的證據;E.1 只餵了 CODE_FILES,不足以證明這一點。

<!-- 逐字開始 -->
```
.agents/evidence-policy.json
.claude/hooks/redlight.py
docs/audits/2026-10-05-m1a-station3k-redlight.md
docs/audits/2026-10-05-m1a-station4i-fix.md
docs/audits/2026-10-05-m1a-station4j-fix.md
docs/audits/2026-10-05-m1a-station5j-review-package.md
docs/audits/2026-10-05-m1a-station5j-review.md
docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
tests/test_redlight.py
```
<!-- 逐字結束 -->

---

## E. 程式差異與使用點(原樣)

### E.1 `git diff d4b6fafd4afdd70121278527194aeef4097bff33..c1eebd97ed197d7f653fbc1c680a0feca1837c6a -- .claude/hooks/redlight.py tests/test_redlight.py .agents/evidence-policy.json`(本輪全部程式、測試與 policy 改動)

<!-- 逐字開始 -->
```
diff --git a/.agents/evidence-policy.json b/.agents/evidence-policy.json
index 6e9aca1..82669a8 100644
--- a/.agents/evidence-policy.json
+++ b/.agents/evidence-policy.json
@@ -5,5 +5,5 @@
   "committed_overrides": ["strict_markers=true"],
   "python_versions": ["3.11"],
   "pytest_versions": ["9.1.1"],
-  "dists": [["anyio", "4.15.0"]]
+  "dists": [["anyio", "4.15.0"], ["anyio", "4.15.1"]]
 }
diff --git a/.claude/hooks/redlight.py b/.claude/hooks/redlight.py
index d4d208a..0fe2f7a 100644
--- a/.claude/hooks/redlight.py
+++ b/.claude/hooks/redlight.py
@@ -483,7 +483,9 @@ KNOWN_PYTHON_VERSIONS = ("3.11",)
 #   未知 plugin ⇒ fail-closed。
 
 # (vii′) 已知第三方 plugin:(dist 名稱, 精確版本)。只看名稱不算(名稱可被冒用),版本不同也不算。
-KNOWN_DISTS = (("anyio", "4.15.0"),)
+# 票 145 Station 4k:anyio 4.15.1(PyPI 2026-09-05)納入;pytest_plugin.py 與 4.15.0 逐位元組相同(wheel 比對,外部來源),
+# 真實 4.15.1 環境的淨室正二由 4k POSIX 驗收證明。
+KNOWN_DISTS = (("anyio", "4.15.0"), ("anyio", "4.15.1"))
 
 # (xiii) P1 的盤點只對這些 pytest 版本成立;換版後非 ini 的 CLI 選項要重新盤點。
 KNOWN_PYTEST_VERSIONS = ("9.1.1",)
diff --git a/tests/test_redlight.py b/tests/test_redlight.py
index c284bc8..e9f4c82 100644
--- a/tests/test_redlight.py
+++ b/tests/test_redlight.py
@@ -2748,3 +2748,45 @@ class TestRootIsToplevelParser:
         monkeypatch.setattr(_sp, "run", fake_run)
         assert redlight._root_is_toplevel(str(tmp_path)) is False
         assert calls and calls[0][-2:] == ["--is-inside-work-tree", "--show-prefix"], calls
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# 票 145 Station 3k 紅燈 —— 能力邊界 KNOWN_DISTS 納入 anyio 4.15.1(〈六十五〉65.5 裁決 A)
+#
+# 能力(KNOWN_DISTS)與宿主 policy 分開驗:K-a 鎖常數;K-b 正控 = 已提交、明確接受 4.15.1 的 policy
+# + 4.15.1 的 plugin 事實 ⇒ "true";K-c / K-d 負控 = 宿主 policy 未接受 / 未盤點版本 ⇒ "unknown";
+# K-e = policy 同列兩版時各版各自 ⇒ "true"(參數化,兩案各自獨立執行)。
+# 既有 helper(`_g_root` / `_g_policy` / `_g_policy_text` / `_g_coverage`)只呼叫、不修改。
+# ─────────────────────────────────────────────────────────────────────────────
+
+
+class TestKnownDistBoundaryAnyio4151:
+
+    def test_k3_anyio_4151_is_a_known_dist(self):
+        """K-a(constant-lock;S6-2 上必須失敗:KNOWN_DISTS 只有 4.15.0)。"""
+        assert ("anyio", "4.15.1") in redlight.KNOWN_DISTS, redlight.KNOWN_DISTS
+
+    def test_k3_a_committed_policy_accepting_4151_with_a_4151_plugin_is_full_coverage(self, tmp_path, monkeypatch):
+        """K-b(behavior-red;S6-2 上必須失敗:4.15.1 在邊界外 ⇒ policy 無效且 plugin 為 other ⇒ unknown)。"""
+        root = _g_root(tmp_path / "r", policy_text=_g_policy_text(_g_policy(dists=[["anyio", "4.15.1"]])))
+        got = _g_coverage(root, monkeypatch, anyio_version="4.15.1")
+        assert got == "true", got
+
+    def test_k3_a_host_policy_without_4151_is_unknown(self, tmp_path, monkeypatch):
+        """K-c(negative-lock;S6-2 上即綠,修後仍須綠):宿主 policy 只接受 4.15.0,環境是 4.15.1 ⇒ unknown。"""
+        root = _g_root(tmp_path / "r", policy_text=_g_policy_text(_g_policy()))
+        got = _g_coverage(root, monkeypatch, anyio_version="4.15.1")
+        assert got == "unknown", got
+
+    def test_k3_an_uninventoried_version_is_unknown(self, tmp_path, monkeypatch):
+        """K-d(negative-lock;S6-2 上即綠,修後仍須綠):9.9.9 不在 KNOWN_DISTS ⇒ policy 無效 ⇒ unknown。"""
+        root = _g_root(tmp_path / "r", policy_text=_g_policy_text(_g_policy(dists=[["anyio", "9.9.9"]])))
+        got = _g_coverage(root, monkeypatch, anyio_version="9.9.9")
+        assert got == "unknown", got
+
+    @pytest.mark.parametrize("version", ["4.15.0", "4.15.1"])
+    def test_k3_a_policy_listing_both_versions_accepts_each(self, tmp_path, monkeypatch, version):
+        """K-e(behavior-red;S6-2 上兩案皆失敗:policy 含邊界外版本 ⇒ 整份 policy 無效)。"""
+        pol = _g_policy(dists=[["anyio", "4.15.0"], ["anyio", "4.15.1"]])
+        got = _g_coverage(_g_root(tmp_path / "r", policy_text=_g_policy_text(pol)), monkeypatch, anyio_version=version)
+        assert got == "true", got
```
<!-- 逐字結束 -->

### E.2 `git diff 0904cdbc3eafeb71a27c266cdd11ae151f21fb67..b0849792ff3e69df70cdd8a5d77d26af78d79021 -- tests/test_redlight.py`(3k:S3K1)

<!-- 逐字開始 -->
```
diff --git a/tests/test_redlight.py b/tests/test_redlight.py
index c284bc8..e9f4c82 100644
--- a/tests/test_redlight.py
+++ b/tests/test_redlight.py
@@ -2748,3 +2748,45 @@ class TestRootIsToplevelParser:
         monkeypatch.setattr(_sp, "run", fake_run)
         assert redlight._root_is_toplevel(str(tmp_path)) is False
         assert calls and calls[0][-2:] == ["--is-inside-work-tree", "--show-prefix"], calls
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# 票 145 Station 3k 紅燈 —— 能力邊界 KNOWN_DISTS 納入 anyio 4.15.1(〈六十五〉65.5 裁決 A)
+#
+# 能力(KNOWN_DISTS)與宿主 policy 分開驗:K-a 鎖常數;K-b 正控 = 已提交、明確接受 4.15.1 的 policy
+# + 4.15.1 的 plugin 事實 ⇒ "true";K-c / K-d 負控 = 宿主 policy 未接受 / 未盤點版本 ⇒ "unknown";
+# K-e = policy 同列兩版時各版各自 ⇒ "true"(參數化,兩案各自獨立執行)。
+# 既有 helper(`_g_root` / `_g_policy` / `_g_policy_text` / `_g_coverage`)只呼叫、不修改。
+# ─────────────────────────────────────────────────────────────────────────────
+
+
+class TestKnownDistBoundaryAnyio4151:
+
+    def test_k3_anyio_4151_is_a_known_dist(self):
+        """K-a(constant-lock;S6-2 上必須失敗:KNOWN_DISTS 只有 4.15.0)。"""
+        assert ("anyio", "4.15.1") in redlight.KNOWN_DISTS, redlight.KNOWN_DISTS
+
+    def test_k3_a_committed_policy_accepting_4151_with_a_4151_plugin_is_full_coverage(self, tmp_path, monkeypatch):
+        """K-b(behavior-red;S6-2 上必須失敗:4.15.1 在邊界外 ⇒ policy 無效且 plugin 為 other ⇒ unknown)。"""
+        root = _g_root(tmp_path / "r", policy_text=_g_policy_text(_g_policy(dists=[["anyio", "4.15.1"]])))
+        got = _g_coverage(root, monkeypatch, anyio_version="4.15.1")
+        assert got == "true", got
+
+    def test_k3_a_host_policy_without_4151_is_unknown(self, tmp_path, monkeypatch):
+        """K-c(negative-lock;S6-2 上即綠,修後仍須綠):宿主 policy 只接受 4.15.0,環境是 4.15.1 ⇒ unknown。"""
+        root = _g_root(tmp_path / "r", policy_text=_g_policy_text(_g_policy()))
+        got = _g_coverage(root, monkeypatch, anyio_version="4.15.1")
+        assert got == "unknown", got
+
+    def test_k3_an_uninventoried_version_is_unknown(self, tmp_path, monkeypatch):
+        """K-d(negative-lock;S6-2 上即綠,修後仍須綠):9.9.9 不在 KNOWN_DISTS ⇒ policy 無效 ⇒ unknown。"""
+        root = _g_root(tmp_path / "r", policy_text=_g_policy_text(_g_policy(dists=[["anyio", "9.9.9"]])))
+        got = _g_coverage(root, monkeypatch, anyio_version="9.9.9")
+        assert got == "unknown", got
+
+    @pytest.mark.parametrize("version", ["4.15.0", "4.15.1"])
+    def test_k3_a_policy_listing_both_versions_accepts_each(self, tmp_path, monkeypatch, version):
+        """K-e(behavior-red;S6-2 上兩案皆失敗:policy 含邊界外版本 ⇒ 整份 policy 無效)。"""
+        pol = _g_policy(dists=[["anyio", "4.15.0"], ["anyio", "4.15.1"]])
+        got = _g_coverage(_g_root(tmp_path / "r", policy_text=_g_policy_text(pol)), monkeypatch, anyio_version=version)
+        assert got == "true", got
```
<!-- 逐字結束 -->

### E.3 `git diff 16d29f7ee84c746f845d071e13dce93b85e26fb2..492b5de438ef9a306b112ac1fbc402729e219879 -- .claude/hooks/redlight.py`(4k:S4K1)

<!-- 逐字開始 -->
```
diff --git a/.claude/hooks/redlight.py b/.claude/hooks/redlight.py
index d4d208a..0fe2f7a 100644
--- a/.claude/hooks/redlight.py
+++ b/.claude/hooks/redlight.py
@@ -483,7 +483,9 @@ KNOWN_PYTHON_VERSIONS = ("3.11",)
 #   未知 plugin ⇒ fail-closed。
 
 # (vii′) 已知第三方 plugin:(dist 名稱, 精確版本)。只看名稱不算(名稱可被冒用),版本不同也不算。
-KNOWN_DISTS = (("anyio", "4.15.0"),)
+# 票 145 Station 4k:anyio 4.15.1(PyPI 2026-09-05)納入;pytest_plugin.py 與 4.15.0 逐位元組相同(wheel 比對,外部來源),
+# 真實 4.15.1 環境的淨室正二由 4k POSIX 驗收證明。
+KNOWN_DISTS = (("anyio", "4.15.0"), ("anyio", "4.15.1"))
 
 # (xiii) P1 的盤點只對這些 pytest 版本成立;換版後非 ini 的 CLI 選項要重新盤點。
 KNOWN_PYTEST_VERSIONS = ("9.1.1",)
```
<!-- 逐字結束 -->

### E.4 `git diff 492b5de438ef9a306b112ac1fbc402729e219879..c1eebd97ed197d7f653fbc1c680a0feca1837c6a -- .agents/evidence-policy.json`(4k:S4K1B)

<!-- 逐字開始 -->
```
diff --git a/.agents/evidence-policy.json b/.agents/evidence-policy.json
index 6e9aca1..82669a8 100644
--- a/.agents/evidence-policy.json
+++ b/.agents/evidence-policy.json
@@ -5,5 +5,5 @@
   "committed_overrides": ["strict_markers=true"],
   "python_versions": ["3.11"],
   "pytest_versions": ["9.1.1"],
-  "dists": [["anyio", "4.15.0"]]
+  "dists": [["anyio", "4.15.0"], ["anyio", "4.15.1"]]
 }
```
<!-- 逐字結束 -->

### E.5 `KNOWN_DISTS` 的使用點(TARGET)

#### E.5.0 `git grep -n KNOWN_DISTS c1eebd97ed197d7f653fbc1c680a0feca1837c6a -- "*.py"` 原始輸出

<!-- 逐字開始 -->
```
c1eebd97ed197d7f653fbc1c680a0feca1837c6a:.claude/hooks/redlight.py:488:KNOWN_DISTS = (("anyio", "4.15.0"), ("anyio", "4.15.1"))
c1eebd97ed197d7f653fbc1c680a0feca1837c6a:.claude/hooks/redlight.py:627:      1. plugin **物件**出現在 distinfo 配對中 ⇒ (dist 名稱, 精確版本) 在 `KNOWN_DISTS` 為 known_dist,
c1eebd97ed197d7f653fbc1c680a0feca1837c6a:.claude/hooks/redlight.py:644:            kind = "known_dist" if all(pair in KNOWN_DISTS for pair in paired) else "other"
c1eebd97ed197d7f653fbc1c680a0feca1837c6a:.claude/hooks/redlight.py:939:    if not set(tuple(d) for d in policy["dists"]) <= set(KNOWN_DISTS):
c1eebd97ed197d7f653fbc1c680a0feca1837c6a:.claude/hooks/redlight.py:974:            "dists": [list(d) for d in KNOWN_DISTS]}
c1eebd97ed197d7f653fbc1c680a0feca1837c6a:.claude/hooks/redlight.py:1109:    accepted_dists = set(tuple(d) for d in _effective(KNOWN_DISTS, [tuple(d) for d in policy["dists"]]))
c1eebd97ed197d7f653fbc1c680a0feca1837c6a:.claude/portable/verify_gates.py:335:    for name, version in rl.KNOWN_DISTS:
c1eebd97ed197d7f653fbc1c680a0feca1837c6a:tests/test_host_evidence_policy.py:91:    assert set(tuple(d) for d in policy.get("dists") or ()) <= set(redlight.KNOWN_DISTS), policy
c1eebd97ed197d7f653fbc1c680a0feca1837c6a:tests/test_install.py:642:        `KNOWN_DISTS`);`config_file` 屬 `FRAMEWORK_CONFIG_FILES`。常數以 getattr 取得,取不到 ⇒ 失敗。
c1eebd97ed197d7f653fbc1c680a0feca1837c6a:tests/test_install.py:654:        assert template.get("dists") == [list(d) for d in getattr(rl, "KNOWN_DISTS")], template
c1eebd97ed197d7f653fbc1c680a0feca1837c6a:tests/test_redlight.py:2440:        `:613` 的 `KNOWN_DISTS` 含 anyio 4.15.0 ⇒ `:833` 回 `"true"`。
c1eebd97ed197d7f653fbc1c680a0feca1837c6a:tests/test_redlight.py:2754:# 票 145 Station 3k 紅燈 —— 能力邊界 KNOWN_DISTS 納入 anyio 4.15.1(〈六十五〉65.5 裁決 A)
c1eebd97ed197d7f653fbc1c680a0feca1837c6a:tests/test_redlight.py:2756:# 能力(KNOWN_DISTS)與宿主 policy 分開驗:K-a 鎖常數;K-b 正控 = 已提交、明確接受 4.15.1 的 policy
c1eebd97ed197d7f653fbc1c680a0feca1837c6a:tests/test_redlight.py:2766:        """K-a(constant-lock;S6-2 上必須失敗:KNOWN_DISTS 只有 4.15.0)。"""
c1eebd97ed197d7f653fbc1c680a0feca1837c6a:tests/test_redlight.py:2767:        assert ("anyio", "4.15.1") in redlight.KNOWN_DISTS, redlight.KNOWN_DISTS
c1eebd97ed197d7f653fbc1c680a0feca1837c6a:tests/test_redlight.py:2782:        """K-d(negative-lock;S6-2 上即綠,修後仍須綠):9.9.9 不在 KNOWN_DISTS ⇒ policy 無效 ⇒ unknown。"""
```
<!-- 逐字結束 -->

#### E.5.1 `.claude/hooks/redlight.py` 第 476–493 行(KNOWN_PYTHON_VERSIONS 至 KNOWN_PYTEST_VERSIONS 整段定義與註解;含 :488)

<!-- 逐字開始 -->
```
# (xviii) P1 對 sys.flags 與 assert 移除的盤點只對這些 Python 版本(major.minor)成立;升級須走票。
KNOWN_PYTHON_VERSIONS = ("3.11",)

# ── 票 145 Station 4d —— 收集定義完整性與版本邊界(〈二十九〉2 (vii′)–(xiii))
# 以下四組是「已盤點」清單,**變更須走票**。版本邊界總表(〈二十九〉2):
#   pytest 內建 ⇒ 鎖 pytest 版本;root producer ⇒ 鎖 tests/conftest.py 已提交 blob;
#   repo 收集設定 ⇒ 鎖 pyproject.toml 已提交 blob;已知第三方 plugin ⇒ 鎖 dist 名稱 + 精確版本;
#   未知 plugin ⇒ fail-closed。

# (vii′) 已知第三方 plugin:(dist 名稱, 精確版本)。只看名稱不算(名稱可被冒用),版本不同也不算。
# 票 145 Station 4k:anyio 4.15.1(PyPI 2026-09-05)納入;pytest_plugin.py 與 4.15.0 逐位元組相同(wheel 比對,外部來源),
# 真實 4.15.1 環境的淨室正二由 4k POSIX 驗收證明。
KNOWN_DISTS = (("anyio", "4.15.0"), ("anyio", "4.15.1"))

# (xiii) P1 的盤點只對這些 pytest 版本成立;換版後非 ini 的 CLI 選項要重新盤點。
KNOWN_PYTEST_VERSIONS = ("9.1.1",)

# (x) 框架盤點過的設定檔型態(root 相對路徑;P1 只盤點了 pyproject 的 `[tool.pytest.ini_options]`)。
```
<!-- 逐字結束 -->

#### E.5.2 `.claude/hooks/redlight.py` 第 622–649 行(:627 docstring 與 :644 plugin 配對,各前後 5 行)

<!-- 逐字開始 -->
```

def classify_plugins(root, name_plugins, distinfo):
    """`list_name_plugin()` 與 `list_plugin_distinfo()` 的原始事實 → `[{"name", "kind"}]`。

    依序判定(〈二十三〉3,經〈二十九〉2 (vii′) 修訂):
      1. plugin **物件**出現在 distinfo 配對中 ⇒ (dist 名稱, 精確版本) 在 `KNOWN_DISTS` 為 known_dist,
         否則 other(只看名稱相同不算 —— 名稱可被冒用;版本缺失或不同也是 other)
      2. 名稱是絕對路徑(conftest 的註冊名稱)⇒ root 相對路徑恰為 `ROOT_CONFTEST` 為 root_conftest,否則 other
      3. 定義模組為 `_pytest` 或 `_pytest.*` ⇒ builtin
      4. 其他(含 `-p no:` 留下的 `(name, None)`)⇒ other
    帳本只記正規化名稱(`_plugin_name`;〈三十五〉4):路徑型轉 root 相對路徑(root 以外記 `<outside>`),
    非識別字形狀的名稱記 `<non-identifier>`,不記絕對路徑。**kind 用原始名稱判定**,正規化只作用於落帳字串。
    配對到 dist 的項目另記 `dists`(`[[名稱, 版本], ...]`)。
    """
    dists = [(p, _dist_name(d), _dist_version(d)) for p, d in (distinfo or [])]
    out = []
    for name, plugin in name_plugins or []:
        name = str(name)
        is_path = _is_abs_path(name)
        shown = _plugin_name(name, root)
        paired = [(dn, dv) for p, dn, dv in dists if p is plugin]
        if paired:
            kind = "known_dist" if all(pair in KNOWN_DISTS for pair in paired) else "other"
        elif is_path:
            kind = "root_conftest" if _plugin_path_name(name, root) == ROOT_CONFTEST else "other"
        else:
            mod = _defining_module(plugin)
            builtin = isinstance(mod, str) and (
```
<!-- 逐字結束 -->

#### E.5.3 `.claude/hooks/redlight.py` 第 934–944 行(:939 policy 邊界檢查)

<!-- 逐字開始 -->
```
        bnd.append(u"config_file")
    if not set(policy["python_versions"]) <= set(KNOWN_PYTHON_VERSIONS):
        bnd.append(u"python_versions")
    if not set(policy["pytest_versions"]) <= set(KNOWN_PYTEST_VERSIONS):
        bnd.append(u"pytest_versions")
    if not set(tuple(d) for d in policy["dists"]) <= set(KNOWN_DISTS):
        bnd.append(u"dists")
    return [], bnd


def policy_state(root):
```
<!-- 逐字結束 -->

#### E.5.4 `.claude/hooks/redlight.py` 第 969–979 行(:974 安裝範本)

<!-- 逐字開始 -->
```
    return {"schema": schema, "version": version,
            "config_file": FRAMEWORK_CONFIG_FILES[0],
            "committed_overrides": [],
            "python_versions": list(KNOWN_PYTHON_VERSIONS),
            "pytest_versions": list(KNOWN_PYTEST_VERSIONS),
            "dists": [list(d) for d in KNOWN_DISTS]}


def _effective_policy(ep):
    """session 記下的 `evidence_policy` → 可用的 policy(dict);任何一項不成立 ⇒ None(unknown)。

```
<!-- 逐字結束 -->

#### E.5.5 `.claude/hooks/redlight.py` 第 1104–1114 行(:1109 verdict 的 accepted_dists)

<!-- 逐字開始 -->
```
    if _completeness_problems(comp):
        return "unknown"
    policy = _effective_policy(comp["evidence_policy"])
    if policy is None:
        return "unknown"
    accepted_dists = set(tuple(d) for d in _effective(KNOWN_DISTS, [tuple(d) for d in policy["dists"]]))
    if any(p["kind"] not in SUPPORTED_PLUGIN_KINDS for p in comp["plugins"]):
        return "unknown"
    if any(p["kind"] == "known_dist" and not _known_dists_accepted(p, accepted_dists)
           for p in comp["plugins"]):
        return "unknown"
```
<!-- 逐字結束 -->

#### E.5.6 `.claude/portable/verify_gates.py` 第 330–340 行(:335 淨室 policy 的 dists 推導)

<!-- 逐字開始 -->
```
    try:
        pytest_version = metadata.version("pytest")
    except Exception:
        pytest_version = None
    dists = []
    for name, version in rl.KNOWN_DISTS:
        try:
            if metadata.version(name) == version:
                dists.append([name, version])
        except Exception:
            pass
```
<!-- 逐字結束 -->

(tests/ 底下的命中只列在 E.5.0,不另取前後行;`tests/test_redlight.py` 的 3k 測試全文見 E.6。)

### E.6 `git show c1eebd97ed197d7f653fbc1c680a0feca1837c6a:tests/test_redlight.py` 的 `TestKnownDistBoundaryAnyio4151` 全文(第 2763–2792 行)

<!-- 逐字開始 -->
```
class TestKnownDistBoundaryAnyio4151:

    def test_k3_anyio_4151_is_a_known_dist(self):
        """K-a(constant-lock;S6-2 上必須失敗:KNOWN_DISTS 只有 4.15.0)。"""
        assert ("anyio", "4.15.1") in redlight.KNOWN_DISTS, redlight.KNOWN_DISTS

    def test_k3_a_committed_policy_accepting_4151_with_a_4151_plugin_is_full_coverage(self, tmp_path, monkeypatch):
        """K-b(behavior-red;S6-2 上必須失敗:4.15.1 在邊界外 ⇒ policy 無效且 plugin 為 other ⇒ unknown)。"""
        root = _g_root(tmp_path / "r", policy_text=_g_policy_text(_g_policy(dists=[["anyio", "4.15.1"]])))
        got = _g_coverage(root, monkeypatch, anyio_version="4.15.1")
        assert got == "true", got

    def test_k3_a_host_policy_without_4151_is_unknown(self, tmp_path, monkeypatch):
        """K-c(negative-lock;S6-2 上即綠,修後仍須綠):宿主 policy 只接受 4.15.0,環境是 4.15.1 ⇒ unknown。"""
        root = _g_root(tmp_path / "r", policy_text=_g_policy_text(_g_policy()))
        got = _g_coverage(root, monkeypatch, anyio_version="4.15.1")
        assert got == "unknown", got

    def test_k3_an_uninventoried_version_is_unknown(self, tmp_path, monkeypatch):
        """K-d(negative-lock;S6-2 上即綠,修後仍須綠):9.9.9 不在 KNOWN_DISTS ⇒ policy 無效 ⇒ unknown。"""
        root = _g_root(tmp_path / "r", policy_text=_g_policy_text(_g_policy(dists=[["anyio", "9.9.9"]])))
        got = _g_coverage(root, monkeypatch, anyio_version="9.9.9")
        assert got == "unknown", got

    @pytest.mark.parametrize("version", ["4.15.0", "4.15.1"])
    def test_k3_a_policy_listing_both_versions_accepts_each(self, tmp_path, monkeypatch, version):
        """K-e(behavior-red;S6-2 上兩案皆失敗:policy 含邊界外版本 ⇒ 整份 policy 無效)。"""
        pol = _g_policy(dists=[["anyio", "4.15.0"], ["anyio", "4.15.1"]])
        got = _g_coverage(_g_root(tmp_path / "r", policy_text=_g_policy_text(pol)), monkeypatch, anyio_version=version)
        assert got == "true", got
```
<!-- 逐字結束 -->

### E.7 `git show c1eebd97ed197d7f653fbc1c680a0feca1837c6a:.agents/evidence-policy.json` 全文(第 1–9 行)

<!-- 逐字開始 -->
```
{
  "schema": "monkeyleash.evidence-policy",
  "version": 1,
  "config_file": "pyproject.toml",
  "committed_overrides": ["strict_markers=true"],
  "python_versions": ["3.11"],
  "pytest_versions": ["9.1.1"],
  "dists": [["anyio", "4.15.0"], ["anyio", "4.15.1"]]
}
```
<!-- 逐字結束 -->

---

## F. 證據(逐字)

F.1 / F.2 出處為 REVIEW_HEAD(`95cd4490f181537e530be516d7ef61c5f7c3e587`);F.3 出處為本機未入庫檔(見 F.3 段首)。

### F.0 K 測試紅綠定位表(非逐字;每格附 F.1 / F.2 出處行號)

F.1 / F.2 的行號 = REVIEW_HEAD 上該檔的行號(本包 F.1 / F.2 逐字段與之逐行對應)。

| 測試 | S3K1 上的固定全套(Windows) | S4K1B(TARGET)上的固定全套(Windows) | S4K1B Linux 真裝 4.15.1(裁決助手;非本 repo 帳本) |
|---|---|---|---|
| K-a `test_k3_anyio_4151_is_a_known_dist`(constant-lock;F.2 第 46 行) | **failed**:F.2 第 59 行 `FAILED …test_k3_anyio_4151_is_a_known_dist`、第 72 行 `assert ('anyio', '4.15.1') in (('anyio', '4.15.0'),)`、第 74 行 `tests\test_redlight.py:2767: AssertionError`、第 63 行摘要 `4 failed, 2106 passed, 4 skipped, 3 xfailed` | **passed**:F.1 第 81 行摘要 `2110 passed, 4 skipped, 3 xfailed`(0 failed)、第 84 行、第 88 行 | **passed**:F.1 第 197 行「6 支 K 測試…全 passed」 |
| K-b `…_with_a_4151_plugin_is_full_coverage`(behavior-red;F.2 第 47 行) | **failed**:F.2 第 60 行、第 76 行 `assert 'unknown' == 'true'`、第 80 行 `tests\test_redlight.py:2773: AssertionError` | **passed**:F.1 第 81、84、89 行 | **passed**:F.1 第 197 行 |
| K-c `test_k3_a_host_policy_without_4151_is_unknown`(negative-lock;F.2 第 48 行) | **passed**:F.2 第 66 行「K-c / K-d 在 passed 之內」;第 59–62 行 FAILED 清單沒有它 | **passed**:F.1 第 81、84、90 行 | **passed**:F.1 第 197 行 |
| K-d `test_k3_an_uninventoried_version_is_unknown`(negative-lock;F.2 第 49 行) | **passed**:F.2 第 66 行 | **passed**:F.1 第 81、84、91 行 | **passed**:F.1 第 197 行 |
| K-e[4.15.0](behavior-red;F.2 第 50 行) | **failed**:F.2 第 61 行、第 82 行、第 86 行 `tests\test_redlight.py:2792: AssertionError` | **passed**:F.1 第 81、84、92 行 | **passed**:F.1 第 197 行 |
| K-e[4.15.1](behavior-red;F.2 第 51 行) | **failed**:F.2 第 62 行、第 88 行、第 92 行 `tests\test_redlight.py:2792: AssertionError` | **passed**:F.1 第 81、84、93 行 | **passed**:F.1 第 197 行 |

- R3 前提:F.2 第 132 行 `tests red under ticket 145: tests/test_redlight.py`、第 135 行;F.1 第 36 行。
- 帳本:F.2 第 101–125 行(V0 → V1);F.1 第 97–122 行(V1 → V2)。
- 淨室:F.1 第 134–170 行(Windows,anyio 4.15.0);F.1 第 196 行(Linux,真裝 4.15.1,含 S4J1 對照)。

### F.1 `docs/audits/2026-10-05-m1a-station4k-fix.md` 全文

行號來源:REVIEW_HEAD 的該檔第 1–199 行

<!-- 逐字開始 -->
# 票 145 Station 4k —— 能力邊界 KNOWN_DISTS 納入 anyio 4.15.1 與本機驗收

- 日期:2026-10-06(UTC)
- 對象:S4K1 `492b5de438ef9a306b112ac1fbc402729e219879`(只改 `.claude/hooks/redlight.py` 的 `KNOWN_DISTS`);S4K1B `c1eebd97ed197d7f653fbc1c680a0feca1837c6a`(只改 `.agents/evidence-policy.json` 的 `dists`)。
- 上一個 commit:S3K2 `16d29f7ee84c746f845d071e13dce93b85e26fb2`;紅燈 S3K1 `b0849792ff3e69df70cdd8a5d77d26af78d79021`。
- 合約:票 145〈六十五〉65.5 裁決 A(擴大能力邊界,邊界跟著證據長);裁決 4:4k 須在真裝 anyio 4.15.1 的乾淨環境證明正二成立(裁決助手 POSIX)。
- 範圍:**本機(Windows;本機 anyio 為 4.15.0)驗收**。本報告只宣稱:本機驗收通過;~~待 POSIX 外部驗收(真裝 anyio 4.15.1)~~。（S4K4 後更新：POSIX 外部 clean-room（真裝 anyio 4.15.1）驗收已 PASS，見第 9 節；Station 4k = PASS / COMPLETED；待 Station 5k 獨立審查。刪除線為 F-036 保存的舊狀態字樣，2026-10-06 由 S4K4 取代。）

## 【給裁決者】

1. 修正:框架認得的 anyio 版本從只有 4.15.0 改成 4.15.0 與 4.15.1 兩版;本 repo 的 policy 也同步接受兩版。各一行。
2. 本機全套 2110 passed、0 failed;3k 那 4 支紅燈全部轉綠,2 支負控維持綠。
3. 淨室兩正三負全部成立,正二仍可退紅;本 repo 測試帳本只往後加,淨室前後完全沒動。
4. 這台機器裝的是 anyio 4.15.0,所以「真裝 4.15.1 時正二成立」本機證明不了,要靠 POSIX 外部驗收。
5. 下一步是 POSIX 外部淨室驗收(裁決助手執行,須真裝 anyio 4.15.1)。

## 【給裁決助手】

### 1. 修正內容

S4K1(`git diff --cached -U0 -- .claude/hooks/redlight.py`,提交前):

```
diff --git a/.claude/hooks/redlight.py b/.claude/hooks/redlight.py
index d4d208a..0fe2f7a 100644
--- a/.claude/hooks/redlight.py
+++ b/.claude/hooks/redlight.py
@@ -486 +486,3 @@ KNOWN_PYTHON_VERSIONS = ("3.11",)
-KNOWN_DISTS = (("anyio", "4.15.0"),)
+# 票 145 Station 4k:anyio 4.15.1(PyPI 2026-09-05)納入;pytest_plugin.py 與 4.15.0 逐位元組相同(wheel 比對,外部來源),
+# 真實 4.15.1 環境的淨室正二由 4k POSIX 驗收證明。
+KNOWN_DISTS = (("anyio", "4.15.0"), ("anyio", "4.15.1"))
```

- 只有一個 hunk;`--stat` 為 `.claude/hooks/redlight.py | 4 +++-`(3 insertions(+), 1 deletion(-))。
- Edit 一次通過,沒有被 R3 擋。前提是本機紅燈:S3K1 上 status 為 `tests red under ticket 145: tests/test_redlight.py`。
- 寫入後 `py_compile` 無輸出。探針(`status.py`)的 `grep -n "redlight.py"` 只命中 `tests red under ticket 145: tests/test_redlight.py` 一行,沒有 redlight.py 讀取錯誤。
- `content_hash`、consumer、`policy_state`、conftest、status / install / verify_gates、任何測試都未改。

S4K1B(`git diff --cached -U0`,提交前):

```
diff --git a/.agents/evidence-policy.json b/.agents/evidence-policy.json
index 6e9aca1..82669a8 100644
--- a/.agents/evidence-policy.json
+++ b/.agents/evidence-policy.json
@@ -8 +8 @@
-  "dists": [["anyio", "4.15.0"]]
+  "dists": [["anyio", "4.15.0"], ["anyio", "4.15.1"]]
```

- 其他欄位、縮排、行尾都沒動。兩版都在能力邊界 B(KNOWN_DISTS)內,所以 effective = B ∩ H 兩版皆接受。

提交:

```
$ git commit -F .scratch/m1a-s4k/s4k-1-msg.txt
[master 492b5de] fix(145): M1-a Station 4k-1 —— KNOWN_DISTS 納入 anyio 4.15.1（能力邊界跟著證據長；S6 CI 淨室 FAIL）
 1 file changed, 3 insertions(+), 1 deletion(-)
$ git rev-parse HEAD
492b5de438ef9a306b112ac1fbc402729e219879
$ git commit -F .scratch/m1a-s4k/s4k-1b-msg.txt
[master c1eebd9] fix(145): M1-a Station 4k-1b —— 宿主 evidence policy dists 納入 anyio 4.15.1（B ∩ H，兩版皆在 B 內）
 1 file changed, 1 insertion(+), 1 deletion(-)
$ git rev-parse HEAD
c1eebd97ed197d7f653fbc1c680a0feca1837c6a
```

兩次提交前 `git diff --cached --check` 都無輸出;提交後 `git status --porcelain` 都無輸出。

### 2. 3a 固定全套(S4K1B 上只跑一次;Windows)

`python -X utf8 -m pytest -q > <session scratchpad>/s4k-run.txt 2>&1`,exit 0。

```
$ grep -n -E "^FAILED|^ERROR|SKIPPED|passed|failed" <session scratchpad>/s4k-run.txt
32:SKIPPED [1] tests\test_gate.py:451: 此環境無法建立 symlink
33:SKIPPED [1] tests\test_gate.py:459: 此環境無法建立 symlink
34:SKIPPED [1] tests\test_gate.py:473: 此環境無法建立 symlink
35:SKIPPED [1] tests\test_redlight.py:2673: Windows 檔名不得含 LF;本案例由 POSIX 驗收證明(〈六十一〉61.3 裁決 2)
39:2110 passed, 4 skipped, 3 xfailed in 296.19s (0:04:56)
```

- collected 2117(2110 + 4 + 3)。0 failed;沒有 `FAILED` / `ERROR` 行。

| 代號 | S3K1(修前) | S4K1B(修後) |
|---|---|---|
| K-a `test_k3_anyio_4151_is_a_known_dist` | failed(`:2767`) | passed |
| K-b `test_k3_a_committed_policy_accepting_4151_with_a_4151_plugin_is_full_coverage` | failed(`:2773`) | passed |
| K-c `test_k3_a_host_policy_without_4151_is_unknown` | passed | passed |
| K-d `test_k3_an_uninventoried_version_is_unknown` | passed | passed |
| K-e[4.15.0] `test_k3_a_policy_listing_both_versions_accepts_each[4.15.0]` | failed(`:2792`) | passed |
| K-e[4.15.1] `test_k3_a_policy_listing_both_versions_accepts_each[4.15.1]` | failed(`:2792`) | passed |

(修前欄出自 `docs/audits/2026-10-05-m1a-station3k-redlight.md`。修後欄的依據是:S4K1B 全套 0 failed,而 6 支都在收集範圍內 —— collected 2117 與 3k 相同。)

### 3. 3b 帳本(以 V1 為前段基準;各自單獨執行)

```
$ head -c 903816 .dev/test-runs.jsonl > <session scratchpad>/r24.bin
$ sha256sum <session scratchpad>/r24.bin
0edb6cd32349bf5477a5f1adef2e59188d91de8841239565a467b5fc39c56285 *<session scratchpad>/r24.bin
$ head -c 18095023 .dev/test-sessions.jsonl > <session scratchpad>/s24.bin
$ sha256sum <session scratchpad>/s24.bin
75c4580bc54324b90391ccee222647a4933549872154e2af41c2aaaffe405763 *<session scratchpad>/s24.bin
$ wc -l .dev/test-runs.jsonl
3438 .dev/test-runs.jsonl
$ wc -l .dev/test-sessions.jsonl
36 .dev/test-sessions.jsonl
$ wc -c .dev/test-runs.jsonl
915335 .dev/test-runs.jsonl
$ wc -c .dev/test-sessions.jsonl
18838751 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl
3637077aea4d2bdaa3138bf9b2aa28b5306ab9e9bc317d04df78ddfee3382778 *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
6d18a5c6567054da5f2d09d7655b8aa29129c34cbf948be69e8a9c58d09dddcd *.dev/test-sessions.jsonl
```

- 前段 sha256 = V1 ⇒ 只追加。test-runs 3391 → 3438(+47)、test-sessions 35 → 36(+1)。
- **V1**:903816 / `0edb6cd32349bf5477a5f1adef2e59188d91de8841239565a467b5fc39c56285`;18095023 / `75c4580bc54324b90391ccee222647a4933549872154e2af41c2aaaffe405763`。
- **V2**:915335 / `3637077aea4d2bdaa3138bf9b2aa28b5306ab9e9bc317d04df78ddfee3382778`;18838751 / `6d18a5c6567054da5f2d09d7655b8aa29129c34cbf948be69e8a9c58d09dddcd`。

### 4. 3c status(節錄原文)

```
23:test-runs: 本票 red 0 / green 47 / run 事實未知 0 / orphaned 0 / schema 不合格 run 0;最後一筆 tests/test_verify_gates.py=green @ 2026-10-06T11:42:12.930658+00:00;最近一次 run:A(exit 0;collected 2117 / deselected 0 / passed 2110 / failed 0 / skipped 4)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl)
24:evidence policy: 有效  (source: .agents/evidence-policy.json)
38:tests red under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
```

- `evidence policy: 有效` 說明修改後的 policy(兩版 dists)仍落在能力邊界內,並且已提交、與工作樹一致。

### 5. 3d 淨室(本機 Windows;本機 anyio 4.15.0)

`python .claude/portable/verify_gates.py <session scratchpad>/verify-gates7 > <session scratchpad>/s4k-verify.txt 2>&1`,exit 0(工具沒有標示非零退出碼)。

```
$ grep -n -E "擋下 ✓|成立|不成立|passed, " <session scratchpad>/s4k-verify.txt
194:    R1   擋下 ✓
195:    R2   擋下 ✓
196:    R3   擋下 ✓
197:    R4   擋下 ✓
198:    R5   擋下 ✓
199:    R6   擋下 ✓
200:    R7   擋下 ✓
201:    R8   擋下 ✓
202:    R9   擋下 ✓
217:    1960 passed, 8 skipped, 3 xfailed in 271.46s (0:04:31)
220:    正一 未初始化                  成立 ✓  35 個框架測試檔皆 unknown=True;evidence policy: 未初始化
221:    正二 已初始化且相符               成立 ✓  rc 1→0;file_coverage=true;red=(無);green=tests/test_evidence_probe.py;evidence policy: 有效;1 passed in 18.87s
222:    負一 policy / 環境不符         成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 有效;1 passed in 0.33s
223:    負二 HEAD 有、工作樹不同          成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 工作樹與 HEAD 不同;1 passed in 0.25s
224:    負三 工作樹有、HEAD 沒有          成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 未提交;1 passed in 0.25s
226:全部 9 條規則各擋下一次,權威層偵測正常,框架測試在新 repo 全綠,evidence policy 兩正三負成立。
```

事後(各自單獨執行):

```
$ sha256sum .dev/test-runs.jsonl
3637077aea4d2bdaa3138bf9b2aa28b5306ab9e9bc317d04df78ddfee3382778 *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
6d18a5c6567054da5f2d09d7655b8aa29129c34cbf948be69e8a9c58d09dddcd *.dev/test-sessions.jsonl
$ git status --porcelain
(無輸出)
```

- 本 repo 帳本 = V2,淨室沒有碰。
- **限制**:這次淨室的 anyio 是本機的 4.15.0。它證明修改後 4.15.0 環境沒有退化,但**不證明**真裝 4.15.1 時正二成立(第 9 節)。

### 6. 裁決助手外部來源(照錄自〈六十五〉65.3 / 〈六十六〉;非本 repo 帳本證據)

- 同一組 3k 測試在 S4J1 碼上 4 紅 2 綠;KNOWN_DISTS 加 4.15.1 後 `tests/test_redlight.py` 153 passed。
- anyio-4.15.0 與 4.15.1 的 wheel:`anyio/pytest_plugin.py` 與 `entry_points.txt` 逐位元組相同。但檔案相同不等於行為等價,真實 4.15.1 環境的行為以第 9 節驗收為準。

### 7. 殘餘與未證明(目前尚未 machine-enforced)

1. 沿用 4j 證據報告(`docs/audits/2026-10-05-m1a-station4j-fix.md`)第 7 節全部項目(含 S5j-1 依 S5j-F2 / F3 補準後的第 3 點、第 4 點殘餘措辭),不擴張。
2. **相依漂移**:KNOWN_DISTS 仍為精確版本 pin,下一次相依升版會再落在邊界外;候選機制見票「相關」追蹤項(〈六十五〉65.4 登記的「相依漂移(精確版本能力邊界 vs 乾淨環境自動升版)」)。
3. 本機只驗 anyio 4.15.0;真裝 4.15.1 的淨室正二尚未證明(第 9 節)。

### 8. 程序紀錄

- 外來 3 檔以 `git stash push -u -m jeff-mods-recon-20261004-s4k -- <3 檔>` 收起,本輪結束後 `git stash pop` 放回。
- 沒有閘門擋下;沒有改測試、`.dev/pipeline.json`;沒有 push / fetch。
- 本視窗 = 原實作視窗;5k 須開第六個全新對話。

### 9. POSIX 外部 clean-room 驗收(真裝 anyio 4.15.1)

> **舊文字(F-036,保留不刪)**:本節標題原為 ~~`### 9. POSIX 外部 clean-room 驗收(真裝 anyio 4.15.1):待執行(裁決助手)`~~,沒有內文。
> —— 2026-10-06 由 S4K4 的 POSIX 驗收紀錄取代。

- 來源：Jeff 轉述裁決助手 2026-10-06 Linux 證據（隔離沙盒；git 2.43.0；Python 3.11.16；全新 venv 依 CI 方式 pip install -e ".[dev]" 實際安裝 anyio 4.15.1、pytest 9.1.1；非本 repo 帳本證據；本 repo 兩本帳本未動）。
- 受測物：S4K1B 的 .claude/hooks/redlight.py（blob 0fe2f7ab0e600a18db1079462db80eddee6eae13，sha256 30ee60f9e501788ee2e3a065f0bfc4725d9258fd3f2cdb68288719c7382d30ed，與本機 S4K2 run 紀錄 impl_hash 相同）、tests/test_redlight.py（blob e9f4c82e6b879db998f9ebe8289aa458b1475c9f = S3K1）、.agents/evidence-policy.json（blob 82669a8c0f0c59eaf8b507e00639b9700aafb172）。置於全新 clone、提交後工作樹乾淨、歷史完整（unshallow）。
- verify_gates.py 淨室（anyio 4.15.1 實裝）：R1–R9 各擋下一次、權威層偵測三項成立、框架測試 1964 passed, 4 skipped, 3 xfailed；兩正三負全部成立，正二 file_coverage=true、green=tests/test_evidence_probe.py；exit 0。對照：S4J1 碼在同一 venv 下正二不成立 ✗、exit 1（〈六十五〉65.3 的重現）。
- 6 支 K 測試（TestKnownDistBoundaryAnyio4151）全 passed；evidence 相關 5 檔 1 failed, 963 passed：唯一 failed 為先前 4g–4j 各次 POSIX 驗收亦出現的 tests/test_gate.py::TestAuthorityLayerIsWired::test_this_repo_itself_is_wired；環境性原因仍屬推定，尚未獨立核驗。淺層 clone 時另有 4 支 R6 相關失敗，git fetch --unshallow 後消失，對應 CI workflow fetch-depth: 0 的既有註解，判為 clone 深度所致而非回歸（同屬推定）。
- 固定全套：13 failed, 2101 passed, 3 xfailed（collected 2117）；13 個 failed 與 4j POSIX 驗收那次逐字相同（test_gate 1 + test_known_items_regression 12），可支持「未新增該類失敗」，環境性根因仍屬推定、尚未獨立核驗或 machine-enforced。
- Jeff 裁決（2026-10-06）：Station 4k = PASS / COMPLETED（Windows 本機 + POSIX 外部 clean-room，真裝 anyio 4.15.1）；待 Station 5k 獨立審查（第六個全新對話）。CI 是否轉綠仍須 Station 6 第三次 push 後由 CI 本身證明。
<!-- 逐字結束 -->

### F.2 `docs/audits/2026-10-05-m1a-station3k-redlight.md` 全文

行號來源:REVIEW_HEAD 的該檔第 1–146 行

<!-- 逐字開始 -->
# 票 145 Station 3k —— 能力邊界 KNOWN_DISTS 納入 anyio 4.15.1 的紅燈

- 日期:2026-10-05(UTC 已跨 2026-10-06)
- 合約:票 145〈六十五〉65.5 裁決 A(擴大能力邊界,邊界跟著證據長);紅燈分「能力」與「policy」兩層,保留負控。
- 上一個 commit:S6-2 `0904cdbc3eafeb71a27c266cdd11ae151f21fb67`。
- 紅燈 commit:S3K1 `b0849792ff3e69df70cdd8a5d77d26af78d79021`。
- 範圍:只在 `tests/test_redlight.py` 檔尾新增 1 個 class、5 支測試(K-e 參數化 2 案,共 6 個 nodeid);不改產品碼、既有測試、`.dev/pipeline.json`。

## 【給裁決者】

1. 加了 6 個測試案例,把「能力邊界(框架認得哪些 anyio 版本)」和「宿主 policy(這個 repo 接受哪些版本)」分開驗。
2. 全套只跑一次:恰好 4 支紅,就是預期要紅的那 4 支。原因都是「4.15.1 還不在框架認得的版本裡」;另外 2 支負控是綠的。
3. status 已顯示 `tests/test_redlight.py` 在本票紅燈清單裡,所以 4k 改 `redlight.py` 時,R3(先有紅燈才准改程式的規則)會放行。
4. 帳本只往後加,舊內容沒動。外來 3 檔照前例先收起、做完放回。
5. 下一步是 Station 4k:在 `KNOWN_DISTS` 加上 4.15.1,並在真裝 4.15.1 的乾淨環境證明正二成立。

## 【給裁決助手】

### 1. S3K1

`tests/test_redlight.py` 檔尾新增 `class TestKnownDistBoundaryAnyio4151`;既有 helper(`_g_root` / `_g_policy` / `_g_policy_text` / `_g_coverage`)只呼叫、不修改。

```
$ python -m py_compile tests/test_redlight.py
(無輸出)
$ git add tests/test_redlight.py
(無輸出)
$ git diff --cached --stat
 tests/test_redlight.py | 42 ++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 42 insertions(+)
$ git diff --cached -U0 -- tests/test_redlight.py > <session scratchpad>/s3k-diff.txt   → 恰一個 hunk,只有 + 行
@@ -2750,0 +2751,42 @@ class TestRootIsToplevelParser:
$ git diff --cached --check
(無輸出)
$ git commit -F .scratch/m1a-s3k/s3k-1-msg.txt
[master b084979] test(145): M1-a Station 3k-1 —— 能力邊界 KNOWN_DISTS 納入 anyio 4.15.1 的紅燈（K-a/K-b/K-e 紅、K-c/K-d 負控；6 支）
 1 file changed, 42 insertions(+)
$ git rev-parse HEAD
b0849792ff3e69df70cdd8a5d77d26af78d79021
$ git status --porcelain
(無輸出)
```

| 代號 | nodeid | 分類 | 在 S6-2 上(預期) | S3K1 全套(實際) |
|---|---|---|---|---|
| K-a | `tests/test_redlight.py::TestKnownDistBoundaryAnyio4151::test_k3_anyio_4151_is_a_known_dist` | constant-lock(red) | 失敗 | **failed**(`:2767`) |
| K-b | `tests/test_redlight.py::TestKnownDistBoundaryAnyio4151::test_k3_a_committed_policy_accepting_4151_with_a_4151_plugin_is_full_coverage` | behavior-red | 失敗 | **failed**(`:2773`) |
| K-c | `tests/test_redlight.py::TestKnownDistBoundaryAnyio4151::test_k3_a_host_policy_without_4151_is_unknown` | negative-lock | 通過(修後仍須綠) | passed |
| K-d | `tests/test_redlight.py::TestKnownDistBoundaryAnyio4151::test_k3_an_uninventoried_version_is_unknown` | negative-lock | 通過(修後仍須綠) | passed |
| K-e[4.15.0] | `tests/test_redlight.py::TestKnownDistBoundaryAnyio4151::test_k3_a_policy_listing_both_versions_accepts_each[4.15.0]` | behavior-red | 失敗 | **failed**(`:2792`) |
| K-e[4.15.1] | `tests/test_redlight.py::TestKnownDistBoundaryAnyio4151::test_k3_a_policy_listing_both_versions_accepts_each[4.15.1]` | behavior-red | 失敗 | **failed**(`:2792`) |

### 2. 紅燈全套(在 S3K1 上只跑一次;Windows)

指令:`python -X utf8 -m pytest -q > <session scratchpad>/s3k-run.txt 2>&1`,exit 1;之後 `git status --porcelain` 無輸出。

```
$ grep -n -E "^FAILED|passed|failed" <session scratchpad>/s3k-run.txt
110:FAILED tests/test_redlight.py::TestKnownDistBoundaryAnyio4151::test_k3_anyio_4151_is_a_known_dist
111:FAILED tests/test_redlight.py::TestKnownDistBoundaryAnyio4151::test_k3_a_committed_policy_accepting_4151_with_a_4151_plugin_is_full_coverage
112:FAILED tests/test_redlight.py::TestKnownDistBoundaryAnyio4151::test_k3_a_policy_listing_both_versions_accepts_each[4.15.0]
113:FAILED tests/test_redlight.py::TestKnownDistBoundaryAnyio4151::test_k3_a_policy_listing_both_versions_accepts_each[4.15.1]
114:4 failed, 2106 passed, 4 skipped, 3 xfailed in 246.14s (0:04:06)
```

- collected 2117(4 + 2106 + 4 + 3)。FAILED 恰為預期的 4 支;K-c / K-d 在 passed 之內。

失敗行(輸出檔第 39–43、55–61、75–81、95–101 行,以 `grep -n -E "^tests.test_redlight.py:[0-9]+: |^E   "` 取出):

```
39:E       AssertionError: (('anyio', '4.15.0'),)
40:E       assert ('anyio', '4.15.1') in (('anyio', '4.15.0'),)
41:E        +  where (('anyio', '4.15.0'),) = redlight.KNOWN_DISTS
43:tests\test_redlight.py:2767: AssertionError
55:E       AssertionError: unknown
56:E       assert 'unknown' == 'true'
57:E
58:E         - true
59:E         + unknown
61:tests\test_redlight.py:2773: AssertionError
75:E       AssertionError: unknown
76:E       assert 'unknown' == 'true'
77:E
78:E         - true
79:E         + unknown
81:tests\test_redlight.py:2792: AssertionError
95:E       AssertionError: unknown
96:E       assert 'unknown' == 'true'
97:E
98:E         - true
99:E         + unknown
101:tests\test_redlight.py:2792: AssertionError
```

(第 57、77、97 行的 `E         ` 是 pytest 原始輸出的行尾空白;本報告照錄時把它們去掉,以通過 `git diff --cached --check`。)

- K-a 失敗於 `KNOWN_DISTS` 只有 `('anyio', '4.15.0')`。K-b / K-e 都得到 `unknown`,原因是 4.15.1 在邊界外,policy 無效或 plugin 判為 other。紅的原因正是本站要修的能力邊界,不是測試本身的瑕疵。

### 3. 帳本

基準 V0(Step 0):test-runs 891928 bytes / `22148446c9cc8d11520cd6437f5a49c852b9b02cc17c47d2a4b53d8be8991fe4`;test-sessions 17351316 bytes / `3d7cde594d889bc71804c2af421b4c7d61078691c8644052bb68bbe7e03865f1`。

```
$ head -c 891928 .dev/test-runs.jsonl > <session scratchpad>/r23.bin
$ sha256sum <session scratchpad>/r23.bin
22148446c9cc8d11520cd6437f5a49c852b9b02cc17c47d2a4b53d8be8991fe4 *<session scratchpad>/r23.bin
$ head -c 17351316 .dev/test-sessions.jsonl > <session scratchpad>/s23.bin
$ sha256sum <session scratchpad>/s23.bin
3d7cde594d889bc71804c2af421b4c7d61078691c8644052bb68bbe7e03865f1 *<session scratchpad>/s23.bin
$ wc -l .dev/test-runs.jsonl
3391 .dev/test-runs.jsonl
$ wc -l .dev/test-sessions.jsonl
35 .dev/test-sessions.jsonl
$ wc -c .dev/test-runs.jsonl
903816 .dev/test-runs.jsonl
$ wc -c .dev/test-sessions.jsonl
18095023 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl
0edb6cd32349bf5477a5f1adef2e59188d91de8841239565a467b5fc39c56285 *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
75c4580bc54324b90391ccee222647a4933549872154e2af41c2aaaffe405763 *.dev/test-sessions.jsonl
```

- 前段 sha256 = V0 ⇒ 只追加。test-runs 3344 → 3391 行(+47)、test-sessions 34 → 35 行(+1)。
- 跑後全檔記為 **V1**:test-runs 903816 bytes / `0edb6cd32349bf5477a5f1adef2e59188d91de8841239565a467b5fc39c56285`;test-sessions 18095023 bytes / `75c4580bc54324b90391ccee222647a4933549872154e2af41c2aaaffe405763`。供 4k 使用。

### 4. status(節錄原文)

```
test-runs: 本票 red 1 / green 46 / run 事實未知 0 / orphaned 0 / schema 不合格 run 0;最後一筆 tests/test_verify_gates.py=green @ 2026-10-06T01:46:19.491434+00:00;最近一次 run:B(exit 1;collected 2117 / deselected 0 / passed 2106 / failed 4 / skipped 4)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl)
evidence policy: 有效  (source: .agents/evidence-policy.json)
tests red under ticket 145: tests/test_redlight.py  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
```

- `tests/test_redlight.py` 在 red ⇒ 4k 改 `redlight.py` 時 R3 所需的本機紅燈已存在,而且是對著 HEAD 的 `redlight.py`(S6-2 = S3K1 的同一 blob)跑出來的。

### 5. 裁決助手 Linux 預演(外部來源;**非本 repo 帳本證據**)

同一組測試在 S4J1 碼上 4 紅 2 綠;`KNOWN_DISTS` 加 4.15.1 後,`tests/test_redlight.py` 153 passed。(來源:Jeff 的 Station 3k 指令。)

### 6. 程序紀錄

- S6-2 由 5j 審查視窗提交;本站回原實作視窗執行。5j 審查視窗不得再擔任任何審查者;5k 須開第六個全新對話。
- 本站站別為 `implement`(Step 0 照指令核對)。
- 外來 3 檔以 `git stash push -u -m jeff-mods-recon-20261004-s3k -- <3 檔>` 收起,本輪結束後 `git stash pop` 放回。
- 沒有閘門擋下;沒有改產品碼、既有測試、`.dev/pipeline.json`;沒有 push / fetch。
<!-- 逐字結束 -->

### F.3 `.dev/reports/2026-10-06T002652Z-ticket145-station6b-push-ci.md` 全文

來源:本機 `.dev/reports/2026-10-06T002652Z-ticket145-station6b-push-ci.md`(未入庫;`.dev/` 被 .gitignore 忽略,不在任何 commit 裡,**不是**「逐字自 REVIEW_HEAD」);sha256 = `969f6729e99d91ef24f6f6b8142109efc9ff681e6ede3bb26960aa04f28d02aa`;wc -c = 3988。行號來源:該本機檔第 1–89 行。

<!-- 逐字開始 -->
# 票 145 Station 6b —— push 完成;CI 查詢因本機沒有 gh 而停手

## 【給裁決者】

1. push 成功:遠端 master 現在是 `774e7351e07ebdfc267a37b58bc09579e1de5646`(S5j-1),已直接向遠端查證(`git ls-remote`)。只推了一次,沒有被擋。
2. CI 結果:**還不知道**。這台機器沒有安裝 GitHub CLI(`gh`),所以查不到 CI。我沒有改用別的方式去查,依「指令沒涵蓋就停手」處理。
3. 沒有改任何檔案、沒有 commit;兩本帳本沒碰;外來 3 檔沒動。
4. 要你決定,三選一:
   - A:由你在 GitHub 網頁看 `774e735` 的 Actions 結果,把結果告訴我(最快,本機不必改)。
   - B:授權我在本機安裝 `gh` 並登入,再照原指令查(會改本機環境,要做驗證)。
   - C:授權我用 `curl` 直接讀 GitHub 公開 API(`/repos/wusuowei-tw/monkeyleash/actions/runs?head_sha=…`)。唯讀,但是是指令沒寫的工具;若 repo 是私有的就需要 token。
5. 不決定的話:push 已完成,但 CI 綠不綠沒有證據,6c 收票不能開始。

## 【給裁決助手】

### Step 0(各自單獨送出;全部符合)

```
$ git rev-parse HEAD
774e7351e07ebdfc267a37b58bc09579e1de5646
$ git rev-parse origin/master
de36ebcbab284ef11064a9943b5191750482dd93
$ git status --porcelain
 M docs/agents/friction-log.md
?? docs/tickets/framework-updates/146-claude-code-enforcement-integrity.md
?? docs/tickets/framework-updates/147-turn-end-check-via-settings-stop-hook.md
$ git stash list
(無輸出)
$ git remote -v
origin	https://github.com/wusuowei-tw/monkeyleash (fetch)
origin	https://github.com/wusuowei-tw/monkeyleash (push)
$ git ls-remote origin refs/heads/master
de36ebcbab284ef11064a9943b5191750482dd93	refs/heads/master
```

### Step 1 push(只一次)

```
$ git push origin master
To https://github.com/wusuowei-tw/monkeyleash
   de36ebc..774e735  master -> master
```

- 上面就是工具顯示的全部輸出。沒有出現任何 pre-push hook 訊息,也沒有被擋。本站沒有去查本機是否設有 pre-push hook。

```
$ git ls-remote origin refs/heads/master
774e7351e07ebdfc267a37b58bc09579e1de5646	refs/heads/master
$ git rev-parse origin/master
774e7351e07ebdfc267a37b58bc09579e1de5646
$ git rev-list --left-right --count origin/master...HEAD
0	0
$ git status --porcelain
 M docs/agents/friction-log.md
?? docs/tickets/framework-updates/146-claude-code-enforcement-integrity.md
?? docs/tickets/framework-updates/147-turn-end-check-via-settings-stop-hook.md
```

⇒ 遠端本人(ls-remote)= S5j-1;本機與遠端 0 / 0;工作樹仍是 P0 三行。

### Step 2 CI —— 停手

```
$ gh run list --repo wusuowei-tw/monkeyleash --commit 774e7351e07ebdfc267a37b58bc09579e1de5646 --json databaseId,headSha,workflowName,event,status,conclusion,url,createdAt
Exit code 127
/usr/bin/bash: line 1: gh: command not found
```

在 Windows 端做唯讀確認,判斷是沒裝還是 PATH 問題:

```
PS> try { (Get-Command gh -ErrorAction Stop).Source } catch { "gh not found" }
gh not found
PS> Test-Path "C:\Program Files\GitHub CLI\gh.exe"
False
```

- 結論:本機沒有安裝 `gh`(Git Bash 的 PATH、PowerShell 的 PATH、預設安裝路徑都沒有)。
- 這不是閘門攔截。指令沒有寫「`gh` 不存在」時怎麼辦,依「指令沒涵蓋就停手」處理:沒有改用 curl / API / 瀏覽器,也沒有安裝任何東西。
- 兩條 PowerShell 指令都是唯讀查詢,不寫檔。它們是指令以外的額外步驟,用來分辨「沒裝」和「PATH 問題」。
- 沒有任何 run 的 JSON、watch 結論或 view 輸出可以照錄。CI 狀態:**未知**。

### 確認

- push 只做了一次:沒有 force、沒有 `--no-verify`、沒有改 refspec、沒有推其他分支或 tag。
- 沒有改檔、沒有 commit;未改 `.dev/pipeline.json`(維持 review)。
- 未讀對話紀錄檔;兩本帳本本站沒有碰(指令本站沒有要求帳本核對)。
- 每條指令都單獨送出。
- 回報檔名用實際 UTC 時間(`date -u` = `2026-10-06T002652Z`)。
<!-- 逐字結束 -->

---

## G. 審查重點

<!-- 逐字開始 -->
G1 邊界擴張是否正確且不 fail-open：KNOWN_DISTS 由一元組變二元組後，所有使用點（policy 驗證的 ⊆ 檢查、plugin 配對的 kind 判定、verify_gates _ev_matching_policy、status 顯示）語意是否不變；是否存在「policy 列 4.15.0、環境 4.15.1」或反向時誤判 true 的路徑。
G2 宿主 policy：dists 兩筆是否 ⊆ KNOWN_DISTS；schema / version / 其他欄位未動；B ∩ H 語意下兩版同列是否合法（4k 文件的理由是否成立）。
G3 不變式未削弱：D.2 + E.1 證明只改 KNOWN_DISTS 一處（含註解）、json 一行、測試檔尾新增（E.2 一個 hunk、無 - 行）；其他 consumer / conftest / status / install / verify_gates 未改。
G4 紅綠時序：K-a / K-b / K-e[4.15.0] / K-e[4.15.1] 在 S3K1 紅、S4K1B 綠；K-c / K-d 一直綠；帳本 V1 → V2 前段不變；R3 在 S4K1 放行的紅燈是否正是對著 S3K2 時的 redlight.py 跑出來的。
G5 測試是否測到宣稱形狀：K-b 的 policy 是已提交、明確只列 4.15.1；K-c 斷言 == "unknown"（非 != "true"）；K-d 9.9.9；K-e 參數化兩案各自獨立；_g_root / _g_policy / _g_coverage 未改。
G6 5g–5j 結論是否仍成立；5j 第 6 節追蹤項（C.1）狀態；S5j-F2（bare 空洞）不受影響。
G7 措辭與程式一致：4k §7「相依漂移」殘餘、S6-2 65.3「推定」口徑、67.3「尚未獨立核驗」是否與可得證據相符；沒有宣稱 CI 已綠。
G8 證據邊界：先從 E.5 核對 KNOWN_DISTS 在程式中的實際定義與用途（含 (vii′) known_dist 的配對判定、以及它所代表的 plugin 選項盤點前提；注意 (xiii) 註解屬 KNOWN_PYTEST_VERSIONS，不得直接套用），再評估本輪納入 4.15.1 的依據 —— wheel 內 pytest_plugin.py 逐位元組相同（外部）+ 真裝 4.15.1 淨室正二成立（外部）—— 是否足以滿足該定義；若審查者本機無 4.15.1，寫「需要重現」並描述最小重現。
G9 總問題（增量版）：TARGET 上是否存在任何路徑，讓邊界外的 dist（或邊界內 dist 搭配未接受它的宿主 policy）得到 file_coverage == "true"；至少檢查：policy 列兩版 + 環境第三版；policy 只列 4.15.1 + 環境 4.15.0；KNOWN_DISTS 含同名兩版時 all(pair in KNOWN_DISTS) 的配對邏輯；找不到也要列檢查過的路徑。
G10 程序：S6-2 由 5j 審查視窗提交、3k 指令曾誤貼至該視窗並停手、4k 由原實作視窗執行 —— 是否影響任何證據的可信度；若無，寫「不影響」並附依據。
判定規則：結論只能 PASS 或 FAIL；FAIL 門檻 = G9 找到同級漏洞、或 G1 / G3 / G4 任一不成立；其他題列 finding 與追蹤項。
<!-- 逐字結束 -->

---

## H. 已知殘餘與追蹤項

出處:F.1 的「殘餘與未證明」一節,即 REVIEW_HEAD 的 `docs/audits/2026-10-05-m1a-station4k-fix.md` 第 177–181 行。

<!-- 逐字開始 -->
### 7. 殘餘與未證明(目前尚未 machine-enforced)

1. 沿用 4j 證據報告(`docs/audits/2026-10-05-m1a-station4j-fix.md`)第 7 節全部項目(含 S5j-1 依 S5j-F2 / F3 補準後的第 3 點、第 4 點殘餘措辭),不擴張。
2. **相依漂移**:KNOWN_DISTS 仍為精確版本 pin,下一次相依升版會再落在邊界外;候選機制見票「相關」追蹤項(〈六十五〉65.4 登記的「相依漂移(精確版本能力邊界 vs 乾淨環境自動升版)」)。
3. 本機只驗 anyio 4.15.0;真裝 4.15.1 的淨室正二尚未證明(第 9 節)。
<!-- 逐字結束 -->

**註**:上列追蹤項目前尚未 machine-enforced。
