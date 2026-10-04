# M1-a Station 5g 獨立審查包(票 145)

**審查對象(TARGET,最後一個程式 commit)**:`8e7775526e462d984abb0992ed74c1e1aa3648dd`
**審查 HEAD(REVIEW_HEAD;review baseline)**:`b5db3734f6795d8a371e4f58b172e0a8ffb066eb`

本包只是材料,不含任何審查結論。所有逐字段落皆以 `<!-- 逐字開始 -->` / `<!-- 逐字結束 -->` 標出邊界,
邊界之間的文字與標示的出處逐位元組相同(換行一律 LF)。
D 段與 E 段的逐字範圍是邊界內 ```` ``` ```` 圍籬**之間**的全部行(圍籬本身不屬於出處內容)。
E 段為 `git diff` 原樣,**未去除行尾空白**(diff 的空白 context 行是單一空格)。
F.1 的出處(4g 報告)本身含有 ```` ``` ```` 圍籬與 diff 片段;F.1 的邊界以該段標示的出處行號為準。

---

## A. 身分與規則

### A.1 身分、受測檔與數量用語

| 代號 | 完整 SHA | 說明 |
|---|---|---|
| **BASE** | `de36ebcbab284ef11064a9943b5191750482dd93` | 已推送、5f 審過的最後狀態(S5f-1) |
| S6-1 | `faf7cb47823e33b65c2a21ffd85db3dd416adea1` | Station 6 push 紀錄、CI 淨室 FAIL 與 3g 裁決(只改票) |
| S3g-0 | `560f618560ddac1a34e0e835b99a1e3a5cc7eda5` | 3g 紅燈規劃(C 段出處) |
| S3G1 | `2737e02c64b88f4d0a39bdafbea2f3776993cf2b` | 3g 主紅燈基線:新增 33 支 = 26 behavior-red + 7 regression-lock |
| S3G2 | `7a15ea081da1bf23cc79e04aef76065438f65219` | 3g 紅燈證據(docs) |
| S3G1B | `83258dd9ab415a793eaf2b140a9e34c5b91069f2` | 3g-1b 補紅燈基線:再新增 9 支 behavior-red |
| S3G1B-2 | `3eb112b1cafb399f2757274264281436729e7e42` | 3g-1b 紅燈證據(docs) |
| S4G1 | `f4fa0418aa037f95ef7d1f59c6fe6a812a80414c` | 4g 實作 |
| S4G1B | `f581a02a5b7a65c8eaf150bf7231acc464f99072` | 4g 合法新增 T1(behavior-red)+ T2(regression-lock) |
| **TARGET**(S4G1C) | `8e7775526e462d984abb0992ed74c1e1aa3648dd` | 修法 B;**最後一個程式 commit —— 審查對象** |
| S4G3 | `2fe52d0ea7ec2d465768b5e907d64726bb1d9256` | 4g 本機驗收證據(docs) |
| S4G4 | `b127ae016ce6a7a7d096742e5771f1e6d328f52a` | POSIX 外部驗收記錄、4g 升級為 PASS / COMPLETED(docs) |
| **REVIEW_HEAD**(S4G5) | `b5db3734f6795d8a371e4f58b172e0a8ffb066eb` | 證據報告三句舊述加更新註記(docs);review baseline |

- 本包所在的 commit(S5g-0)是 REVIEW_HEAD **之後**才建立的 docs-only commit;本包寫不進自己的 SHA,由裁決者交付審查時另附。S5g-0 **不屬於審查對象**。
- TARGET 之後到 REVIEW_HEAD 只改 docs/(見下方核對)。

**TEST_FILES**:`tests/test_redlight.py` `tests/test_status.py` `tests/test_install.py` `tests/test_verify_gates.py` `tests/test_host_evidence_policy.py`

**CODE_FILES**(`git diff --name-only <BASE>..<TARGET>` 中所有非 docs/ 的檔,12 個):
`.agents/evidence-policy.json` `.agents/portable-manifest.txt` `.claude/hooks/redlight.py` `.claude/portable/install.py` `.claude/portable/status.py` `.claude/portable/verify_gates.py` `tests/conftest.py` `tests/test_host_evidence_policy.py` `tests/test_install.py` `tests/test_redlight.py` `tests/test_status.py` `tests/test_verify_gates.py`

**數量用語**(本包與審查報告一律照此,不得簡稱):
- 3g(S3G1)新增 33 支 = 26 behavior-red + 7 regression-lock;
- 3g-1b(S3G1B)再新增 9 支 behavior-red;
- 3g / 3g-1b 合計 42 支 = 35 behavior-red + 7 regression-lock;這 42 支在 4g 都不得被改動;
- 4g 另合法新增 T1(behavior-red)+ T2(regression-lock)於 S4G1B。

建包時核對(原文輸出;各自單獨執行,全部以完整 SHA 為錨點):

```
$ git merge-base --is-ancestor de36ebcbab284ef11064a9943b5191750482dd93 b5db3734f6795d8a371e4f58b172e0a8ffb066eb
(無輸出;exit 0)
$ git rev-list --count de36ebcbab284ef11064a9943b5191750482dd93..b5db3734f6795d8a371e4f58b172e0a8ffb066eb
12
$ git diff --name-only de36ebcbab284ef11064a9943b5191750482dd93..8e7775526e462d984abb0992ed74c1e1aa3648dd
.agents/evidence-policy.json
.agents/portable-manifest.txt
.claude/hooks/redlight.py
.claude/portable/install.py
.claude/portable/status.py
.claude/portable/verify_gates.py
docs/audits/2026-10-03-m1a-station3g-redlight-plan.md
docs/audits/2026-10-03-m1a-station3g-redlight.md
docs/audits/2026-10-04-m1a-station3g-1b-redlight.md
docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
tests/conftest.py
tests/test_host_evidence_policy.py
tests/test_install.py
tests/test_redlight.py
tests/test_status.py
tests/test_verify_gates.py
$ git diff --name-only 8e7775526e462d984abb0992ed74c1e1aa3648dd..b5db3734f6795d8a371e4f58b172e0a8ffb066eb
docs/audits/2026-10-04-m1a-station4g-fix.md
docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
```

### A.2 審查者規則

1. **唯讀**:不改任何檔案、不 commit、不推、不改 `.dev/pipeline.json`;**不寫任何暫存檔**。
2. **禁止 pytest**(含 `--collect-only`、`--version`)與 `verify_gates.py`。帳本(`.dev/test-runs.jsonl`、`.dev/test-sessions.jsonl`)會被任何 pytest 執行追加,審查不得污染證據。需要驗證行為時,讀程式碼做紙上推演。
3. **查詢一律綁定 A.1 的完整 SHA**;不以 `HEAD`、遠端追蹤分支(remote-tracking ref)、本地分支名、短 SHA 或工作樹當下狀態為錨點。範例:

```
git show 8e7775526e462d984abb0992ed74c1e1aa3648dd:<路徑>
git diff de36ebcbab284ef11064a9943b5191750482dd93..8e7775526e462d984abb0992ed74c1e1aa3648dd -- <路徑>
git diff 83258dd9ab415a793eaf2b140a9e34c5b91069f2..8e7775526e462d984abb0992ed74c1e1aa3648dd -- <路徑>
git diff f4fa0418aa037f95ef7d1f59c6fe6a812a80414c..8e7775526e462d984abb0992ed74c1e1aa3648dd -- <路徑>
git log --oneline de36ebcbab284ef11064a9943b5191750482dd93..b5db3734f6795d8a371e4f58b172e0a8ffb066eb
git show b5db3734f6795d8a371e4f58b172e0a8ffb066eb:docs/audits/2026-10-04-m1a-station4g-fix.md
```

4. **逐字段的邊界以各段標示的出處行號為準**(不以段內標題或圍籬判斷)。
5. 審查報告**只寫到** `.scratch/m1a-s5g/review-report.md`,不寫其他位置。
6. 可用 Read / Grep 讀本機已安裝的 pytest / pluggy 原始碼;引用只寫 `_pytest/<檔名>:<行號>`、`pluggy/<檔名>:<行號>`,不寫本機絕對路徑。找安裝位置只准用 `python -m pip show pytest`、`python -m pip show pluggy`。
7. **照錄任何系統訊息、錯誤訊息或路徑前,先把本機使用者名稱遮成 `<user>`。**
8. 被任何閘門(R1–R9、pre-commit、洩漏偵測)擋下:停手回報,不換工具、不繞過。
9. **結論只能是 `PASS` 或 `FAIL`**。只要有任何一項「阻擋」發現,就是 `FAIL`。
10. 每一項發現須標**「阻擋」或「非阻擋」**,並附 `<TARGET>:<路徑>:<行號>` 形式的證據(以 TARGET 為準;例:`8e7775526e462d984abb0992ed74c1e1aa3648dd:.claude/hooks/redlight.py:1127`)。沒有檔名與行號證據的發現不計入判定。
11. 〈G〉的 G1–G13 每一題都必須回答(「無問題」也要附證據);不能回答的,寫明「無法判定」與原因,不得略過。
12. 不得用 python -c、heredoc 或把程式碼放進指令字串。

---

## B. 裁決原文(逐字)

出處一律為 `b5db3734f6795d8a371e4f58b172e0a8ffb066eb:docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md`(以下稱「REVIEW_HEAD 的票 145」)。

### B.1 〈四十六〉46.4 裁決

行號來源:REVIEW_HEAD 的票 145 第 2377–2403 行

<!-- 逐字開始 -->
### 46.4 裁決(照錄)

1. Station 6 = FAIL。公開的紅 CI 保留,不撤回、不 force rewrite;後續以正常 commit 修好再 push。
2. 票 145 回 Station 3g-0;3g 同時處理兩層:
   (第一層)框架 self-test 錯置:tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d4_the_committed_addopts_override_constant_matches_pyproject
     斷言宿主 repo(agent-gates)已提交的 pyproject.toml,違反「框架測試只能斷言框架的性質」;在淨室安裝的 repo 必紅。
   (第二層)downstream evidence-policy 可移植性:全新安裝的 repo 跑固定指令,所有檔案 file_coverage 永遠 unknown,既有紅永遠無法合法退休。
     這直接碰到 M1-a 的核心交付(框架裝到 downstream 後,可信的 pass 能否取得 true authority),屬票 145,不是之後再改善的可用性問題。
3. 設計原則(3g-0 須遵守):
   - 三類拆分:(a) Framework invariant —— 所有安裝都必須一致;框架 self-test 不得要求宿主 repo 剛好有 agent-gates 的 pyproject.toml。
     (b) Framework capability boundary —— 框架實際驗證 / 支援到哪裡(例:Python major.minor、pytest audited versions、known plugin / dist)。
     (c) Host evidence policy —— 宿主 repo 在 (b) 之內,自己選擇接受哪些已提交設定;必須來自宿主已提交、可審計的 policy / config,不得在執行當下自動猜測。
   - 最終可取得 authority 的集合 = Framework capability boundary ∩ Host 已提交 policy。host policy 只能收窄,不能擴張框架未驗證的能力。
   - 不得把「缺少 host policy」解讀成可信。狀態模型:新 repo 尚未建立 / 提交 evidence policy ⇒ unknown ⇒ 不得退紅(正確的 fail-closed);
     經框架初始化流程,宿主提交自己的 policy ⇒ 實際有效環境 == 宿主已提交 policy(且在 capability boundary 內)⇒ 才可能 true。
   - 不得修成「新 repo 沒有 pyproject.toml 也直接給 true」。
4. 驗收須包含 clean-room 兩正三負:
   - (正一)Uninitialized clean repo:框架測試本身全綠;host evidence authority 為 unknown(預期結果)。
   - (正二)Initialized + matching policy:提交合法 policy → 製造 red → 正常固定指令 → true → red 合法退休(端到端證據)。
   - (負一)Initialized + policy / environment mismatch(例:policy 認可某 override,實際不同)⇒ unknown,不能退休。
   - (負二)HEAD 有 policy,但 worktree 與 HEAD 不同(本地改了未 commit)⇒ unknown,不能退休。
   - (負三)worktree 有 policy,但 HEAD 根本沒有 policy(從未提交)⇒ unknown,不能退休。
5. 流程教訓:Station 6 push 前,clean-room verification(.claude/portable/verify_gates.py)成為固定 pre-push acceptance 項,不得只靠 GitHub CI 第一次發現。
6. Policy bootstrap trust root:policy 的 canonical location、schema bootstrap 與 policy 自身的 HEAD / worktree integrity 屬 framework invariant,
   不得由 policy 內容自行指定或自我授權。缺檔、未提交、worktree ≠ HEAD、schema / version 未知 ⇒ 只能 unknown。
   policy authority 內容必須由 HEAD committed blob 解析;worktree 僅用來做 HEAD / worktree identity check,不作為 authority policy 的內容來源
   (不得在比對相等後再把 worktree 檔案當 authority source)。
<!-- 逐字結束 -->

### B.2 〈四十八〉Station 3g 裁決與紅燈集合(48.1 + 48.2)

行號來源:REVIEW_HEAD 的票 145 第 2428–2490 行

<!-- 逐字開始 -->
## 四十八、Station 3g 裁決與紅燈集合（2026-10-03，Jeff）

### 48.1 裁決(照錄;針對 S3g-0 560f618560ddac1a34e0e835b99a1e3a5cc7eda5 規劃檔 P8)

1. policy 載體:甲 —— 獨立檔 .agents/evidence-policy.json(JSON,schema "monkeyleash.evidence-policy" v1)。
2. 誰解析:A —— producer 依 I-3 從 HEAD committed blob 解析並記入 session 的 evidence_policy 欄;consumer 驗型別、identity、schema / version 後判定。
3. 界外值:A —— policy 任一欄位超出 framework capability boundary ⇒ 整份不合格 ⇒ unknown(不取交集、不靜默忽略)。
4. test_d4:C —— 框架推導規則以 fixture 測(TestAddoptsDerivation)+ verdict 時機器鎖步;agent-gates 自身「policy ↔ pyproject」鎖步移到宿主專用檔
   tests/test_host_evidence_policy.py(manifest 標 skip)。
   〈三十一〉裁決 3 修訂(Jeff 明文):語意不變(git show HEAD、不得以 tmp repo / 寫死字串代替、讀取失敗 ⇒ 失敗、不得 skip、唯讀),
   適用位置由「出貨的 tests/test_redlight.py」改為「宿主專用、不出貨的 tests/test_host_evidence_policy.py」。原 test_d4 於 4g 刪除。
5. 環境相依正控(P2-B):A —— 3g / 4g 一併在共用 driver 固定版本事實(授權於 4g)。
6. 初始化:A —— 安裝器只在非 canonical 路徑 .agents/evidence-policy.template.json 寫範本(內容 = B 常數)+ decisions-pending + status 顯示 policy 狀態;
   不做從本機觀察值產草稿的指令。
7. 補充(裁決助手):
   - 4g 驗收須在本機實跑一次 python .claude/portable/verify_gates.py <session scratchpad>/verify-gates,照錄五情境(正一、正二、負一、負二、負三)各一行結果,
     並證明本 repo .dev/ 兩本帳本前後 bytes 與 sha256 不變。規劃檔 #33 只證明情境有接線,不證明情境結果。
   - 3g-1 須把 tests/test_host_evidence_policy.py 登記進 .agents/portable-manifest.txt(skip),否則 test_upstream_manifest 會多紅一支、紅燈集合不準。
   - 其餘未裁事項照規劃檔「不需裁、已依原則定案」段。

### 48.2 預期集合(33 支,完整 nodeid)

預期紅集合(behavior-red,26 支,在 S3G1 上必須失敗):

- tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_a_repo_without_a_policy_is_not_full_coverage
- tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_uncommitted_policy_state_is_not_full_coverage[worktree-only]
- tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_uncommitted_policy_state_is_not_full_coverage[worktree-differs]
- tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_uncommitted_policy_state_is_not_full_coverage[staged-only]
- tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_uncommitted_policy_state_is_not_full_coverage[deleted-in-worktree]
- tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[malformed-json]
- tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[unknown-schema]
- tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[unknown-version]
- tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[unknown-key]
- tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[missing-field]
- tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_a_policy_outside_the_canonical_path_is_not_full_coverage
- tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_the_producer_records_the_policy_identity
- tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_environment_mismatch_is_not_full_coverage[override]
- tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_environment_mismatch_is_not_full_coverage[narrowed-dist]
- tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[strict-markers]
- tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[strict-config]
- tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[o-flag]
- tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[override-ini-eq]
- tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[no-addopts]
- tests/test_redlight.py::TestAddoptsDerivation::test_g3_a_policy_disagreeing_with_the_committed_addopts_is_not_full_coverage
- tests/test_host_evidence_policy.py::test_the_committed_policy_matches_the_committed_pyproject
- tests/test_status.py::TestEvidencePolicyChain::test_g3_no_policy_does_not_retire_a_known_red
- tests/test_status.py::TestEvidencePolicyChain::test_g3_an_uncommitted_policy_does_not_retire_a_known_red[worktree-only]
- tests/test_status.py::TestEvidencePolicyChain::test_g3_an_uncommitted_policy_does_not_retire_a_known_red[worktree-differs]
- tests/test_status.py::TestEvidencePolicyChain::test_g3_a_policy_environment_mismatch_does_not_retire_a_known_red
- tests/test_verify_gates.py::test_every_evidence_policy_scenario_is_wired

預期綠集合(regression-lock,7 支,在 S3G1 上必須通過):

- tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_policy_content_is_not_read_from_the_worktree
- tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_a_matching_committed_policy_is_full_coverage
- tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_cannot_widen_the_capability_boundary[python]
- tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_cannot_widen_the_capability_boundary[pytest]
- tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_cannot_widen_the_capability_boundary[dist]
- tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_cannot_widen_the_capability_boundary[config-file]
- tests/test_status.py::TestEvidencePolicyChain::test_g3_a_matching_committed_policy_retires_the_red

- 預期固定全套:collected 2090(以 S4F1 實測的 collected 2057 為底;S5f-0 到 S3G0 都沒有改測試)。
- 本機 Windows 預期:26 failed、2058 passed、3 skipped、3 xfailed。
<!-- 逐字結束 -->

### B.3 〈五十〉Station 3g-1b 補紅燈

行號來源:REVIEW_HEAD 的票 145 第 2508–2572 行

<!-- 逐字開始 -->
## 五十、Station 3g-1b 補紅燈

### 50.1 裁決(照錄)

1. Station 3g 現有 26 behavior-red + 7 regression-lock(S3G2 7a15ea081da1bf23cc79e04aef76065438f65219)= PASS / ACCEPTED。
   〈四十八〉48.1 第 6 點的兩項設計(安裝範本、status policy 狀態行)沒有對應紅燈;缺口處理選 A:先補 3g-1b,再進 4g。
2. 裁決助手外部驗證(隔離環境;非本 repo 帳本證據;寫進票並標明來源):
   - Linux + Python 3.11 + pytest 9.1.1,以 S3G1 2737e02c64b88f4d0a39bdafbea2f3776993cf2b 的測試檔:3g 新增 33 支為 26 failed / 7 passed,失敗集合同〈四十八〉48.2。
   - 以 S3G1 的樹跑 verify_gates.py:淨室安裝的 repo 不含 tests/test_host_evidence_policy.py;淨室框架測試 26 failed(25 支出貨的 3g 紅燈 + 原 test_d4)、1911 passed;
     7 支 regression-lock 在淨室為綠。
   - 既有事實:install.main 既有流程即以 git add -A + commit 提交安裝結果(.claude/portable/install.py 約 :516–:520);本輪紅燈不得把「範本已提交」列為要求。
3. 本輪新增紅燈(全部 behavior-red;在 S3G2 上必須失敗):
   tests/test_install.py(檔尾新增 class TestEvidencePolicyTemplate):
     I1 test_g3_install_writes_the_template_outside_the_canonical_path:install.main(<tmp 新 repo>) 後,
        .agents/evidence-policy.template.json 存在;.agents/evidence-policy.json 不存在。
        並以真實 producer / consumer 驗證:該 repo(安裝後、未建立 canonical policy)的固定全套 session,其 file_coverage 不得為 "true"
        —— 範本位於非 canonical path,無論是否 tracked / committed,都不得成為 evidence authority。
        (不得斷言範本「已提交」或「未提交」;那不是本票裁決的需求。)
     I2 test_g3_the_template_lists_exactly_the_capability_boundary:範本為 schema "monkeyleash.evidence-policy" v1;python_versions / pytest_versions / dists
        分別等於 redlight 的框架能力邊界常數;config_file 屬 FRAMEWORK_CONFIG_FILES。(常數名稱以 4g 實作為準,測試以 getattr 取得;取不到 ⇒ 失敗。)
     I3 test_g3_decisions_pending_asks_to_initialize_the_policy:docs/decisions-pending.md 含 evidence policy 初始化的待決項(含 canonical 路徑 .agents/evidence-policy.json)。
   tests/test_status.py(檔尾新增 class TestEvidencePolicyStatusLine;參數化 6 案;經真 git tmp repo):
     test_g3_status_shows_the_policy_state[<state>],state ∈ uninitialized / uncommitted / worktree-differs / unknown-schema / outside-boundary / valid;
     status 輸出須有一行以 "evidence policy: " 開頭,其後依序為:未初始化 / 未提交 / 工作樹與 HEAD 不同 / 格式不明 / 超出框架能力邊界 / 有效,
     且該行帶 (source: .agents/evidence-policy.json)。
     [unknown-schema] 必須在同一支測試內依序涵蓋四種已提交文件:JSON malformed、schema 名稱不認得、version 不支援、必要欄位缺失 / 型別錯誤;
     每一種都須顯示「格式不明」(逐一斷言,不得只測一種)。
   ⇒ 新增 9 支;預期固定全套:collected 2099;failed 35(既有 26 + 新 9);passed 2058;skipped 3;xfailed 3。

### 50.2 外部驗證(來源)

50.1 第 2 點為裁決助手在隔離環境的外部驗證,來源是 Jeff 的 Station 3g-1b 指令(修正版),照錄於上。
**非獨立審查 finding;非本 repo 帳本證據。**

### 50.3 新增 9 支(完整 nodeid;全部 behavior-red,在 S3G1B 上必須失敗)

- tests/test_install.py::TestEvidencePolicyTemplate::test_g3_install_writes_the_template_outside_the_canonical_path
- tests/test_install.py::TestEvidencePolicyTemplate::test_g3_the_template_lists_exactly_the_capability_boundary
- tests/test_install.py::TestEvidencePolicyTemplate::test_g3_decisions_pending_asks_to_initialize_the_policy
- tests/test_status.py::TestEvidencePolicyStatusLine::test_g3_status_shows_the_policy_state[uninitialized]
- tests/test_status.py::TestEvidencePolicyStatusLine::test_g3_status_shows_the_policy_state[uncommitted]
- tests/test_status.py::TestEvidencePolicyStatusLine::test_g3_status_shows_the_policy_state[worktree-differs]
- tests/test_status.py::TestEvidencePolicyStatusLine::test_g3_status_shows_the_policy_state[unknown-schema]
- tests/test_status.py::TestEvidencePolicyStatusLine::test_g3_status_shows_the_policy_state[outside-boundary]
- tests/test_status.py::TestEvidencePolicyStatusLine::test_g3_status_shows_the_policy_state[valid]

附註:
- `[unknown-schema]` 逐一涵蓋五份已提交文件。「必要欄位缺失 / 型別錯誤」那一類兩種都測:缺 `dists`、`python_versions` 為字串。
- I1 為了讓「範本不得成為 authority」不被其他 unknown 原因遮蔽,在安裝出的 repo 另提交一份 `pyproject.toml`(以 `--no-verify` 提交,同 install.main 自己的 commit),再驅動真實 producer。

### 50.4 紅燈證據

- 報告:`docs/audits/2026-10-04-m1a-station3g-1b-redlight.md`。
- S3G1B `83258dd9ab415a793eaf2b140a9e34c5b91069f2`:`tests/test_install.py`、`tests/test_status.py` 各只在檔尾新增一個 hunk(`-U0` 標頭 `@@ -463,0 +464,205 @@`、`@@ -3017,0 +3018,117 @@`;沒有刪除行);另改票 145。commit 前只跑 py_compile。
- 固定全套在 S3G1B 上跑了兩次:
  - (a) 第一次:工作樹含 3 個外來 docs 變更(` M docs/agents/friction-log.md`、`?? …/146-…`、`?? …/147-…`)⇒ **不作為正式證據**。
    摘要行原文 `35 failed, 2058 passed, 3 skipped, 3 xfailed in 351.04s (0:05:51)`;停手報告 `.dev/reports/2026-10-04T112500Z-ticket145-station3g-1b-stop.md`。
  - (b) 依 Jeff 裁決 B,外來 3 檔以 `git stash push -u -m jeff-mods-recon-20261004` 收起後重跑一次 ⇒ **正式證據**。
    跑前、跑後 `git status --porcelain` 皆無輸出。exit 1;摘要行原文 `35 failed, 2058 passed, 3 skipped, 3 xfailed in 351.00s (0:05:50)`(collected 2099)。
- 失敗集合恰為〈四十八〉48.2 的 26 支 + 50.3 的 9 支,沒有多、也沒有少;與第一次執行逐條相同。其餘 2058 支(含 3g 的 7 支 regression-lock)通過。
- 新 9 支的失敗點:I1 / I2 在 `test_install.py:617` / `:648`(範本不存在);I3 在 `:667`(decisions-pending 沒有 evidence policy);
  status 6 案都在 `test_status.py:3071`(`evidence policy:` 行 0 行);`[unknown-schema]` 在第一份文件 `malformed-json` 就失敗。
- 帳本 H11 → H12 只追加:兩本前段 sha256 = H11r / H11s;test-runs 2827 → 2874 行(+47)、test-sessions 23 → 24 行(+1)。
- commit(回填):S3G1B `83258dd9ab415a793eaf2b140a9e34c5b91069f2`;S3G1B-2(證據)`3eb112b1cafb399f2757274264281436729e7e42`。
  (F-036:本行原文為「S3G1B-2(證據)於下一次提交回填」;2026-10-04 於 S4G3 回填。)
<!-- 逐字結束 -->

### B.4 〈五十一〉Station 4g 修正

行號來源:REVIEW_HEAD 的票 145 第 2576–2633 行

<!-- 逐字開始 -->
## 五十一、Station 4g 修正

### 51.1 裁決(照錄要點;Jeff,2026-10-04)

1. Station 3g-1b = PASS / ACCEPTED(證據 S3G1B-2 `3eb112b1cafb399f2757274264281436729e7e42`)。4g plan = APPROVED WITH 2 FIXES。
   4g 期間外來 3 檔 stash,票 146 / 147 視窗暫停。三段式:S4G1 實作 → S4G2 本機驗收 → S4G3 docs-only;POSIX 外部 clean-room 由裁決助手執行,通過後另以 S4G4 升級。
2. R3 擋下後續作:
   - R3 擋下屬預期的 fail-closed 行為(非產品缺陷);允許 `git restore` 丟棄 redlight.py 半成品。
   - 編輯規矩:漸進遷移或一次 Write;每次寫入 redlight.py 後以 status.py 為 import 探針;不得修改 `content_hash` 及其呼叫的函式。
   - 第 7 鍵 `committed_addopts` = APPROVED:`evidence_policy` 為 7 鍵。`committed_addopts` 的語意:None = 取得或解析失敗;`""` = config 合法但沒有 addopts;`str` / `list[str]` = 原值。
   - `addopts_overrides(value)` 只接受 `str` / `list[str]`,不讀 git / 檔案。
3. 淨室正二不成立後續作:
   - 修法 B = APPROVED:producer 先判欄位是否存在、再解讀值。
   - A = REJECTED:在 consumer 把 None 當 [],會把「事實取不到」當成「確定沒有 override」⇒ fail-open。
   - C = REJECTED:只是繞過缺陷。
   - 授權新增 T1 + T2;負一到負三須在正二修好後的同一次淨室執行中重新驗證。

### 51.2 證據

- 報告:`docs/audits/2026-10-04-m1a-station4g-fix.md`。
- commit:
  - S4G1 `f4fa0418aa037f95ef7d1f59c6fe6a812a80414c`(實作);
  - S4G1B `f581a02a5b7a65c8eaf150bf7231acc464f99072`(T1 / T2;`tests/test_redlight.py` 檔尾一個 hunk `@@ -2492,0 +2493,42 @@`,只有 + 行);
  - S4G1C `8e7775526e462d984abb0992ed74c1e1aa3648dd`(`tests/conftest.py` 的 producer 修正);
  - S4G3(證據提交)`2fe52d0ea7ec2d465768b5e907d64726bb1d9256`。
    (F-036:本行原文為「S4G3(本次證據提交)於下一次提交回填。」;2026-10-04 於 S4G4 回填。)
  - S4G4(POSIX 驗收記錄與狀態升級)於下一次提交回填。
- 第一次淨室(S4G1):正二不成立(`file_coverage=unknown`)。成因:pytest 9.1.1 沒給 `-o` 時 `override_ini` 為 None,producer 原樣落帳,consumer (viii) 比 `None != []`。該次負一到負三不作為證據。
- 裁決助手外部驗證(Linux,Python 3.11 + pytest 9.1.1;隔離環境;**非本 repo 帳本證據**),照錄於報告第 3 節。
- S4G1B 紅燈全套(只跑一次):`1 failed, 2093 passed, 3 skipped, 3 xfailed in 342.54s (0:05:42)`(collected 2100)。唯一的 FAILED 為 T1,失敗行為 `assert 'unknown' == 'true'`。
- S4G1C 本機全套(只跑一次):`2094 passed, 3 skipped, 3 xfailed in 341.79s (0:05:41)`(collected 2100、0 failed)。
- status:`evidence policy: 有效`;`tests red under ticket 145: (無)`;run 事實未知 0;原本的 5 個紅檔都在 green。
  - 「有效」只代表 policy 文件本身有效,不代表 runtime 一定取得 true authority(報告第 8 節第 2 點)。
- 第二次淨室(S4G1C;同一次執行):兩正三負全部成立。正二 `file_coverage=true`、`green=tests/test_evidence_probe.py`;淨室框架測試 `1944 passed, 7 skipped, 3 xfailed`。
- 帳本只追加:
  - B13 → B14:test-runs 2921 → 2968、test-sessions 25 → 26;
  - B14 → 本次:test-runs 2968 → 3015、test-sessions 26 → 27;
  - 兩次前段 sha256 都等於基準。
  - 淨室驗收前後,本 repo 兩本帳本的 bytes 與 sha256 都不變。
- 殘餘與未證明:見報告第 8 節。其中 status 行不檢查 addopts 鎖步、淨室負情境不斷言成因、logging 鎖步絆線,**目前尚未 machine-enforced**。

### 51.3 POSIX 外部 clean-room 驗收

> **舊文字(F-036,保留不刪)**:本節原文為 ~~`待執行(裁決助手)。`~~;2026-10-04 S4G4 依 Jeff 裁決改為下方照錄段落。
> Jeff 裁決(2026-10-04):Station 4g 本機驗收(S4G2,見 S4G3 `2fe52d0ea7ec2d465768b5e907d64726bb1d9256`)與裁決助手 POSIX 外部驗收皆 PASS ⇒ Station 4g = PASS / COMPLETED;下一站 5g 獨立審查。

POSIX 外部 clean-room 驗收（裁決助手；隔離環境；非本 repo 帳本證據）——2026-10-04 約 18:50 ET
- 環境：Linux，Python 3.11.16，pytest 9.1.1，anyio 4.15.0。
- 受測樹：以公開 repo de36ebcbab284ef11064a9943b5191750482dd93 的 clone 為底，覆蓋 Windows 工作樹於 S4G3 時點的 12 個程式 / 測試 / 設定檔（.claude/hooks/redlight.py、.claude/portable/install.py、.claude/portable/status.py、.claude/portable/verify_gates.py、tests/conftest.py、tests/test_redlight.py、tests/test_status.py、tests/test_install.py、tests/test_verify_gates.py、tests/test_host_evidence_policy.py、.agents/portable-manifest.txt、.agents/evidence-policy.json；CRLF→LF）。docs 未同步（不影響程式行為）。
- verify_gates.py：R1–R9 各擋下一次；權威層偵測三項成立；淨室框架測試 1945 passed、4 skipped、3 xfailed、0 failed；evidence policy 兩正三負全部成立：
    正一 未初始化 成立（35 個框架測試檔皆 unknown；evidence policy: 未初始化）
    正二 已初始化且相符 成立（rc 1→0；file_coverage=true；green=tests/test_evidence_probe.py；evidence policy: 有效）
    負一 policy / 環境不符 成立（file_coverage=unknown；紅仍在）
    負二 HEAD 有、工作樹不同 成立（file_coverage=unknown；evidence policy: 工作樹與 HEAD 不同）
    負三 工作樹有、HEAD 沒有 成立（file_coverage=unknown；evidence policy: 未提交）
- 宿主固定全套（Linux）：collected 2100；2084 passed、13 failed、3 xfailed。13 支為 tests/test_gate.py::TestAuthorityLayerIsWired::test_this_repo_itself_is_wired 與 tests/test_known_items_regression.py 的 12 支；同一沙盒在 4g 之前的已推送版本 de36ebc 上同樣恰為這 13 支失敗 ⇒ 屬沙盒環境因素（推測：clone 未設 hooksPath、缺本機私有資料），與 4g 無關。evidence 相關 5 檔（test_redlight / test_status / test_install / test_verify_gates / test_host_evidence_policy）全過。
- 先前的 S4G1 Linux 重現（正二不成立、成因 override_ini 為 None）與修法 B 原型驗證，見〈五十一〉51.1 / 證據報告。
- 結論：POSIX 外部 clean-room 驗收 PASS。
<!-- 逐字結束 -->

---

## C. 規劃(逐字)

出處一律為 `560f618560ddac1a34e0e835b99a1e3a5cc7eda5:docs/audits/2026-10-03-m1a-station3g-redlight-plan.md`(以下稱「S3g-0 的規劃檔」)。

### C.1 P3 Host evidence policy 設計

行號來源:S3g-0 的規劃檔第 114–221 行

<!-- 逐字開始 -->
## P3 Host evidence policy 設計

### 共同不變式(兩案皆同;屬 I,寫在 redlight.py,不可由 policy 指定)

**I-1 canonical location**:`POLICY_FILE` 是框架常數(兩案各自的值見下)。policy 內容**不得**含任何指定位置、路徑、include 或 extends 的鍵。

**I-2 schema bootstrap**:框架常數列出認得的 `(schema id, version)` 組合。不在清單內 ⇒ unknown。policy 不能宣告自己用哪一套解析規則。

**I-3 bootstrap 順序**(producer 在 sessionfinish 執行;任一步失敗 ⇒ 記 None,consumer 判 unknown):
1. 固定 canonical path(`POLICY_FILE`)。
2. 用 `git rev-parse HEAD:<POLICY_FILE>` 確認檔案存在於 HEAD。否 ⇒ unknown(狀態「未初始化」)。
3. 取得 HEAD committed blob sha(同上一步的輸出)。
4. 用 `git hash-object <POLICY_FILE>`(套用 .gitattributes 正規化,與 `committed_blobs` 同一手法)取得 worktree blob,確認與 HEAD blob 相等。
   不相等、worktree 缺檔 ⇒ unknown。
   - worktree 被改:對應負二。
   - worktree 被刪:同屬負二家族。
   - 只 staged:第 2 步已失敗。
   - 只在 worktree:第 2 步已失敗,對應負三。
5. 用 `git cat-file blob <HEAD blob sha>` 取得內容,解析 schema、version 與 policy 內容。未知、格式錯、多鍵或缺鍵 ⇒ unknown。
   **內容只從這個 blob 來**;第 4 步的 worktree 檔**只用於 identity 比對,之後不再讀取**。
6. 之後才與 runtime environment 比對:
   - 先算 `effective = boundary ∩ policy`;
   - 再要求每一項 runtime 事實都屬於 effective。

**I-4 收窄不擴張**:每個 policy 欄位都必須是 B 常數的子集。界外值怎麼處理見 P8-3:
- 建議:整份 policy 不合格 ⇒ unknown。
- 替代:取交集。

**I-5 缺 policy 不是可信**:沒有 policy、未提交、不一致、看不懂 ⇒ 一律 unknown。不得退回「沿用框架預設值」—— 那正是本票要拆掉的狀態。

### 甲案(建議):獨立 JSON 檔 `.agents/evidence-policy.json`

格式與欄位(schema v1;所有欄位必填;不得有多餘鍵):

```json
{
  "schema": "monkeyleash.evidence-policy",
  "version": 1,
  "config_file": "pyproject.toml",
  "committed_overrides": ["strict_markers=true"],
  "python_versions": ["3.11"],
  "pytest_versions": ["9.1.1"],
  "dists": [["anyio", "4.15.0"]]
}
```

| 欄位 | 語意 | 能力邊界(B 常數) | 與 runtime 比對 |
|---|---|---|---|
| `config_file` | 宿主採用的 pytest 設定檔(root 相對路徑) | `FRAMEWORK_CONFIG_FILES = ("pyproject.toml",)` | `inipath == config_file`;`inifilename is None`(ix 不變);該檔的 worktree blob == HEAD blob(xi 的宿主那一半) |
| `committed_overrides` | 宿主接受的、由已提交 addopts 帶來的 override 清單 | 推導規則(`addopts_overrides(text)`,pytest 9.1.1 盤點) | 兩項都要成立:(a) `== addopts_overrides(HEAD:<config_file> 的 [tool.pytest.ini_options].addopts)`,這是 policy 自洽的機器鎖步,取代 test_d4;(b) runtime `override_ini == committed_overrides`(viii) |
| `python_versions` | 宿主接受的 Python major.minor | ⊆ `KNOWN_PYTHON_VERSIONS` | runtime 屬於 effective(xviii) |
| `pytest_versions` | 宿主接受的 pytest 版本 | ⊆ `KNOWN_PYTEST_VERSIONS` | (xiii) |
| `dists` | 宿主接受的第三方 plugin(名稱與精確版本) | ⊆ `KNOWN_DISTS` | `known_dist` 改為「(名, 版本) ∈ effective」(vii′) |

- **為什麼用 JSON**:`json` 是標準庫,能力邊界外的 Python 版本也解析得了,producer 不必依賴 `tomllib`(3.11 起才有)。
- `config_file` 的 TOML 解析只在 (a) 用到,而能力邊界目前只有 3.11,屬 `tomllib` 可用的範圍;邊界外反正是 unknown。
- **為什麼放 `.agents/`**:它與 `pipeline-stages.yaml` 同一層,都是流程定義。manifest 要明列 `.agents/evidence-policy.json skip`:
  上游自己那一份描述的是 agent-gates,絕不能被抄到下游(P4)。

### 乙案:寫在設定檔裡,`pyproject.toml` 的 `[tool.monkeyleash.evidence-policy]`

- canonical location = 固定的 TOML table。policy 的 integrity 直接沿用 (xi) 的 pyproject blob 比對,不必另做一組 identity check。
- 優點:少一個檔。改設定與改 policy 一定在同一個 commit。
- 缺點:
  1. policy 與「被它管的設定檔」綁在同一份 blob,只要改 pyproject 的任何一行(包括非 pytest 段落),policy 的 identity 就跟著變。
  2. 宿主若選擇其他設定檔型態(將來 B 擴張到 `pytest.ini`),policy 會失去固定位置,違反 I-1。
  3. 解析要 `tomllib`。
  4. 「沒有 pyproject 的 repo」根本沒有地方放 policy。

### 兩案共同:producer / consumer 怎麼讀(P8-2)

- **建議 A**:producer(`tests/conftest.py` 的 `_completeness_of`)依 I-3 讀 policy,在 session 的 `completeness` 新增 `evidence_policy` 欄位:
  `{"path", "head", "worktree", "schema", "version", "policy"}`(`policy` 為從 HEAD blob 解析的內容)。
  consumer(`_completeness_problems` / `_completeness_verdict`)做三件事:驗型別、驗 `head == worktree` 且非 None、驗 schema 與 version;
  然後對 B 常數算交集並比對 runtime 事實。
  - 理由:與既有的 `config_blobs` 同一套「producer 記事實、consumer 判定」模式。
  - 歷史 run 依**當時**的 policy 判定,不會因為之後改 policy 就被重審。
- **B**:consumer 在 status 時依記錄的 blob sha 以 `git cat-file` 重新解析。
  - 好處:不信任 producer 的解析結果。
  - 代價:`file_coverage` 需要 root 與 git,判定變成依賴「status 執行當下的物件庫」。

### fail-closed 一覽

| 情形 | 結果 |
|---|---|
| 缺 policy(HEAD 沒有) | unknown(「未初始化」) |
| worktree 有、HEAD 沒有(負三) | unknown |
| HEAD 有、worktree 不同或缺(負二) | unknown |
| schema / version 未知、JSON 錯、缺鍵或多鍵 | unknown |
| 欄位值超出 B(P8-3) | 建議:unknown |
| policy 與 HEAD 設定檔的 addopts 推導不一致 | unknown |
| runtime 與 effective 不符(負一) | unknown |
| git 不可用 | unknown |

### agent-gates 自身的遷移

1. 提交 `.agents/evidence-policy.json`,內容即上方範例,等於現有常數的值。
2. redlight.py 刪除 `COMMITTED_ADDOPTS_OVERRIDES`。`CONFIG_FILE` 改為 B 常數 `FRAMEWORK_CONFIG_FILES`。
   `KNOWN_*` 三組維持為 B 常數。`COMMITTED_FILES` 拆成兩組:I 的 `ROOT_CONFTEST`,以及由 policy 指定的 `config_file`。
3. `committed_blobs` 改為**逐路徑**呼叫 git,避免 P1 #3 那種「缺一個、全部 None」的連坐。
4. 新增宿主專用測試 `tests/test_host_evidence_policy.py`(skip),繼承 test_d4 的鎖步。

### 版本演進

- 新增 schema 版本時,框架常數列出可接受的 `(schema, version)`。舊版本是否繼續接受,依票裁決。
- 變更 policy 的語意(新增欄位、改比對規則)必須升 version,不得在同一個 version 內改語意。
- 擴張 B(新的 Python、pytest、dist 或設定檔型態)仍須走票重做盤點(沿用〈二十九〉的規則)。
  宿主 policy 只能在 B 擴張**之後**才收得進新值。
<!-- 逐字結束 -->

### C.2 P4 初始化流程

行號來源:S3g-0 的規劃檔第 225–252 行

<!-- 逐字開始 -->
## P4 初始化流程

**原則**:不得自動信任首次觀察值;**只有**人把檔案放到 canonical path 並 commit,policy 才生效。

- **A(建議)**:
  - 安裝器(`<BASELINE>:.claude/portable/install.py:497-530`)新增一步,把範本寫到**非 canonical** 路徑 `.agents/evidence-policy.template.json`。
    範本內容是**框架 B 常數的完整列舉**,不是觀察值。安裝器 `:516`、`:520` 的 `git add -A` 與 commit 會把範本一起提交,
    但因為它不在 canonical path,**永遠不會被當成 authority**。
  - 同時在 `docs/decisions-pending.md`(`install.py:386-422`)加一項:「evidence policy 未初始化:審閱範本 → 依需要收窄 → 存成 `.agents/evidence-policy.json` → commit」。
  - status 新增一行顯示 policy 狀態(未初始化 / 未提交 / worktree ≠ HEAD / schema 不明 / 有效)。
    沒有這一行的話,第二層「永遠 unknown」對下游仍然是靜默的。
  - 範本與 status 行都由框架產生;**「放進 canonical path 並 commit」只有人做**。
- **B**:另做 `python .claude/portable/evidence_policy.py draft`,從**本機觀察值**產一份草稿到 scratch(不 commit)。
  - 好處:方便。
  - 風險:人很容易不審就照抄,實質上等於信任首次觀察值。

**manifest**:
- `.agents/evidence-policy.json`:標 `skip`(各 repo 自己的檔)。
- `.agents/evidence-policy.template.json`:標 `generate`(由安裝器在目標 repo 產生)。
- 範本來源:放在 `.claude/portable/templates/`(標 `copy`)。

**既有 downstream(已 sync 的 repo)的影響**:
- sync 帶入新 redlight 之後,在下游提交 policy 之前,所有 run 都是 unknown,無法退紅。
- 原本若有剛好吻合的下游(例如 pyproject 照舊範本 `<BASELINE>:.claude/portable/templates/pyproject.toml.template:27`,addopts 與 agent-gates 相同),
  在升級後會從「可能 true」降為 unknown。
- 這是 fail-closed 方向的行為改變,不會假綠,但**會讓已有的退紅能力暫時消失**。
- 遷移步驟:sync 的 dry-run 列出「需建立 evidence policy」→ 人在下游審範本、commit → 之後才恢復。
- sync 端是否要加這一項提示,列 P7(本票先只做 status 行)。
<!-- 逐字結束 -->

### C.3 P5 clean-room acceptance 設計

行號來源:S3g-0 的規劃檔第 256–298 行

<!-- 逐字開始 -->
## P5 clean-room acceptance 設計

### verify_gates.py 新增的五個情境(裁決 4)

每個情境都在淨室 repo 內進行(`<BASELINE>:.claude/portable/verify_gates.py:287` `target = <workdir>/verify-gates-repo`)。
每個情境用 `run_scenario` 同一套「佈置 → 執行 → `restore`(`:246-269`)」。

| 情境 | 佈置 | 執行 | 驗收 |
|---|---|---|---|
| **正一** Uninitialized | 安裝後不動 | 在淨室 repo 跑框架測試(既有 `:380`) | 框架測試全綠(既有 `:383-390`);**另外**讀淨室帳本最後一筆 session,對一個框架測試檔算 `file_coverage`,必須是 `"unknown"`;status 的 policy 行為「未初始化」 |
| **正二** Initialized + matching | 建立 pyproject(與 `FRAMEWORK_CONFIG_FILES` 相容)+ policy(值 = 當下環境 ∩ B),commit;再提交一支故意失敗的測試檔 | 固定指令跑一次(紅)→ 修好那支測試、commit → 固定指令再跑一次 | 第二次 `file_coverage == "true"`;status 顯示該紅已退休(**端到端**) |
| **負一** policy / environment mismatch | 同正二,但 runtime 多一個 override(`PYTEST_ADDOPTS="-o python_functions=test"`,或任何 policy 未列的值) | 修好後的那一次改在這個環境跑 | `file_coverage == "unknown"`;紅**仍在** |
| **負二** HEAD 有、worktree 不同 | 同正二,但 policy 的 worktree 多一行(未 commit) | 修好後的那一次 | unknown;紅仍在 |
| **負三** worktree 有、HEAD 沒有 | 同正二,但 policy 從未 commit(只在 worktree) | 修好後的那一次 | unknown;紅仍在 |

- 負二、負三在 verify_gates 內可以共用一個參數化的 helper,但輸出必須**各印一行**,不得合併成一行。
- 「固定指令」在淨室內寫成 `[sys.executable, "-X", "utf8", "-m", "pytest", "-q"]`,在淨室 repo 根執行。
- 新增一個常數表 `EVIDENCE_SCENARIOS`(五個鍵),比照 `SCENARIOS`(`:225-235`)的「規則 ↔ 情境」對照。
  由 `tests/test_verify_gates.py` 斷言五個鍵都在(P6 #33)。

### CI 接線

- 沿用 `<BASELINE>:.github/workflows/tests.yml:112-113` 那一步,不另開步驟。五個情境在 `main()` 內接在「框架測試」(`:375-390`)之後。
- 失敗訊息照 `:345-352` 的格式,點名是**哪一個情境**沒有成立。
- `.github/` 標 `skip`(manifest `:83`),只動上游自己的 CI。

### 本機 Station 6 pre-push 的淨室驗證(裁決 5)

**它寫到哪裡**:
- `verify_gates.py:287`:全部產物在 `<workdir>/verify-gates-repo`。
- `:302` `install.main(target)`:只**讀**來源 repo(`install.py:506` `source_files()`),寫入的都是 target。
- `:380`:淨室內的 pytest 以淨室 repo 為 cwd。該 repo 的 `tests/conftest.py` 以自己的位置推出 `_ROOT`(`tests/conftest.py:130`),
  redlight 的 `ROOT` 也由自己的 `__file__` 推出(`redlight.py:42-43`)。
  ⇒ 帳本寫進 `<workdir>/verify-gates-repo/.dev/`,**不寫本 repo 的 `.dev/`**(靜態推論)。

**程序**(建議寫進 Station 6 的固定步驟):
1. `git status --porcelain` 必須無輸出。
   理由:安裝器讀的是**工作樹**(含未追蹤檔,`install.py:506-508`)。工作樹 ≠ HEAD 時,驗到的不是要 push 的那一版。
2. `<workdir>` 必須在 repo 之外,用 session scratchpad。放在 repo 內會讓本 repo 多一個巢狀 git repo、工作樹變髒。
3. 執行 `python .claude/portable/verify_gates.py <scratchpad>/verify-gates`,照錄最後的摘要行與情境結果。
4. 事後 `git status --porcelain` 仍然無輸出,本 repo `.dev/` 兩本帳本的 bytes 與 sha256 前後不變(作為「不污染」的實測證據)。

**是否另做機器化的 pre-push hook**(per-clone、會拖慢 push):本票不做,列 P7。
<!-- 逐字結束 -->

### C.4 P6 紅燈清單草案(含「需要的授權」)

行號來源:S3g-0 的規劃檔第 302–406 行

<!-- 逐字開始 -->
## P6 紅燈清單草案

**前提**:P8 全部採建議選項。BASELINE = S6-1。預測是**靜態推論**,本機 Windows + Python 3.11 + pytest 9.1.1。

- 分類 behavior-red:在 BASELINE 上必須失敗。
- 分類 regression-lock:在 BASELINE 上必須通過。

### `tests/test_redlight.py`(出貨)

`class TestEvidencePolicyBootstrap`:

| # | nodeid | 分類 | BASELINE 預測 |
|---|---|---|---|
| 1 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_a_repo_without_a_policy_is_not_full_coverage` | behavior-red | 紅(現在 "true") |
| 2 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_uncommitted_policy_state_is_not_full_coverage[worktree-only]` | behavior-red | 紅 —— **「worktree-only policy 未提交 ⇒ unknown」**(負三) |
| 3 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_uncommitted_policy_state_is_not_full_coverage[worktree-differs]` | behavior-red | 紅 —— **「HEAD 有 policy 但 worktree 不同 ⇒ unknown」**(負二) |
| 4 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_uncommitted_policy_state_is_not_full_coverage[staged-only]` | behavior-red | 紅 |
| 5 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_uncommitted_policy_state_is_not_full_coverage[deleted-in-worktree]` | behavior-red | 紅 |
| 6 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[malformed-json]` | behavior-red | 紅 |
| 7 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[unknown-schema]` | behavior-red | 紅 |
| 8 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[unknown-version]` | behavior-red | 紅 |
| 9 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[unknown-key]` | behavior-red | 紅(含自我指定位置的鍵,I-1) |
| 10 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[missing-field]` | behavior-red | 紅 |
| 11 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_a_policy_outside_the_canonical_path_is_not_full_coverage` | behavior-red | 紅 |
| 12 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_the_producer_records_the_policy_identity` | behavior-red | 紅(session 沒有 `evidence_policy` 欄) |
| 13 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_policy_content_is_not_read_from_the_worktree` | regression-lock | 綠(現在根本不讀 policy)。上線後鎖住 I-3 第 5 步:讓 Python 層 open canonical path 一律拋例外,仍須 "true" |
| 14 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_a_matching_committed_policy_is_full_coverage` | regression-lock | 綠(正控) |

`class TestEvidencePolicyBoundary`:

| # | nodeid | 分類 | BASELINE 預測 |
|---|---|---|---|
| 15 | `tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_cannot_widen_the_capability_boundary[python]` | regression-lock | 綠(現在由常數擋下) |
| 16 | `tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_cannot_widen_the_capability_boundary[pytest]` | regression-lock | 綠 |
| 17 | `tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_cannot_widen_the_capability_boundary[dist]` | regression-lock | 綠 |
| 18 | `tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_cannot_widen_the_capability_boundary[config-file]` | regression-lock | 綠 |
| 19 | `tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_environment_mismatch_is_not_full_coverage[override]` | behavior-red | 紅:已提交 addopts 為 `-ra`、policy `committed_overrides: []`,runtime 經 `PYTEST_ADDOPTS` 得到 `["strict_markers=true"]`;現在與常數相等 ⇒ "true"(負一) |
| 20 | `tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_environment_mismatch_is_not_full_coverage[narrowed-dist]` | behavior-red | 紅:policy `dists: []`,runtime 有 anyio 4.15.0 |

`class TestAddoptsDerivation`(框架推導規則,以 fixture 文字驗;取代 test_d4 的框架那一半):

| # | nodeid | 分類 | BASELINE 預測 |
|---|---|---|---|
| 21 | `tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[strict-markers]` | behavior-red | 紅(函式不存在) |
| 22 | `tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[strict-config]` | behavior-red | 紅 |
| 23 | `tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[o-flag]` | behavior-red | 紅 |
| 24 | `tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[override-ini-eq]` | behavior-red | 紅 |
| 25 | `tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[no-addopts]` | behavior-red | 紅 |
| 26 | `tests/test_redlight.py::TestAddoptsDerivation::test_g3_a_policy_disagreeing_with_the_committed_addopts_is_not_full_coverage` | behavior-red | 紅:已提交 addopts `-ra`,policy 與 runtime 都是 `["strict_markers=true"]`;現在 "true" |

### `tests/test_host_evidence_policy.py`(新檔,宿主專用,manifest 標 `skip`)

| # | nodeid | 分類 | BASELINE 預測 |
|---|---|---|---|
| 27 | `tests/test_host_evidence_policy.py::test_the_committed_policy_matches_the_committed_pyproject` | behavior-red | 紅(`git show HEAD:.agents/evidence-policy.json` 失敗;依〈三十一〉裁決 3:失敗、不 skip) |

### `tests/test_status.py`(出貨)

`class TestEvidencePolicyChain`:

| # | nodeid | 分類 | BASELINE 預測 |
|---|---|---|---|
| 28 | `tests/test_status.py::TestEvidencePolicyChain::test_g3_no_policy_does_not_retire_a_known_red` | behavior-red | 紅(現在會退紅) |
| 29 | `tests/test_status.py::TestEvidencePolicyChain::test_g3_an_uncommitted_policy_does_not_retire_a_known_red[worktree-only]` | behavior-red | 紅 —— 負三的鏈條版 |
| 30 | `tests/test_status.py::TestEvidencePolicyChain::test_g3_an_uncommitted_policy_does_not_retire_a_known_red[worktree-differs]` | behavior-red | 紅 —— 負二的鏈條版 |
| 31 | `tests/test_status.py::TestEvidencePolicyChain::test_g3_a_policy_environment_mismatch_does_not_retire_a_known_red` | behavior-red | 紅 —— 負一的鏈條版 |
| 32 | `tests/test_status.py::TestEvidencePolicyChain::test_g3_a_matching_committed_policy_retires_the_red` | regression-lock | 綠 —— 正二的鏈條版 |

### `tests/test_verify_gates.py`(出貨)

| # | nodeid | 分類 | BASELINE 預測 |
|---|---|---|---|
| 33 | `tests/test_verify_gates.py::test_every_evidence_policy_scenario_is_wired` | behavior-red | 紅(`EVIDENCE_SCENARIOS` 不存在) |

### 計數

- 新增 33 支:behavior-red 26、regression-lock 7。
- 檔別:test_redlight 26、test_host_evidence_policy 1、test_status 5、test_verify_gates 1。
- 預期固定全套 collected 2090(以 S4F1 實測的 collected 2057 為底;S5f-0 到 S6-1 都沒有改測試;**未在 BASELINE 實測**)。
  本機預期 failed 26。
- 原 test_d4 在 3g 不動。它在 4g 刪除時,collected 再減 1,前提是 Jeff 裁 P8-4。

### 鏈條要求(延續〈二十九〉29.1 第 5 點)

- #1–#20、#26、#28–#32 必須經**真實** `tests/conftest.py` producer。
- 必須在 tmp root 建**真的** git repo,並提交或修改 policy 檔;不得以假雜湊值代替。
- 每次模擬執行都用全新的 conftest(`_isolated_conftest`,`<BASELINE>:tests/test_redlight.py:290`)。
- #1 需要一個**不提交 policy** 的新 helper(建議 `_g_root(policy=…)`)。它不得改用 `_d_committed_root`,因為後者在 4g 後會一併提交 policy。

### 需要的授權(4g 動既有測試或 helper;assertion、docstring 與 test identity 一律不改)

1. `tests/test_redlight.py:1143` `_d_committed_root`(46 個呼叫點)與 `tests/test_status.py:2370` `_t_committed`(19 個呼叫點):
   加入「寫入並提交與 baseline 相符的 `.agents/evidence-policy.json`」。
   否則上線後所有既有正控都會轉為 unknown —— 包括 P2-B 列出的 22 + 7 個命中,以及 `TestFixedCommandCoverage`、`TestCompletenessLocks`、`TestCollectionDefinitionLocks`、`TestPassValidityLocks`、`TestOverrideBaseChain`、`TestDebuggerModeLocks` 等。
2. `tests/test_status.py` 兩支直接寫 completeness dict 的測試:
   - `TestTestsUnderTicketUsesTheLatestRecordPerFile::test_a_file_that_went_red_then_green_counts_as_green`(`:583`)
   - `TestOrphans::test_a_renamed_red_test_is_orphaned_not_green`(`:1355`)
   兩支都在 `completeness` 補 `evidence_policy` 事實(同 3f 的 `usepdb` 授權形式)。Grep `completeness={` 只命中這兩處。
3. 若 P8-5 選 A:在 `_isolated_conftest`(`test_redlight.py:290`)與 test_status 的對應 driver,以 monkeypatch 把 `pytest.__version__` 與 conftest 所見的 `sys.version_info` 固定為能力邊界內的值。
   只改 driver,不改各測試。
4. `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d4_the_committed_addopts_override_constant_matches_pyproject`:4g 刪除。需要 P8-4 與〈三十一〉裁決 3 的位置修訂。
5. `.agents/portable-manifest.txt`(`ask`):新增 `tests/test_host_evidence_policy.py skip`、`.agents/evidence-policy.json skip`、`.agents/evidence-policy.template.json generate`。
   否則 `tests/test_upstream_manifest.py` 會因未分類而紅。

**受影響的既有測試(預期 4g 後須經授權 1–3 才會維持原判)**:上列 helper 的全部呼叫者,以及授權 2 的兩支。
<!-- 逐字結束 -->

### C.5 P7 殘餘與未證明

行號來源:S3g-0 的規劃檔第 410–424 行

<!-- 逐字開始 -->
## P7 殘餘與未證明

1. **未實測**:P6 的紅綠預測、collected 2090、failed 26,以及 P1 #3「缺一檔、全部 None」的成因,都是靜態推論。
2. **未逐支驗證**:P2-B 的 22 + 7 個命中是否都經真實 producer 讀版本。另外,出貨測試之中是否還有其他依賴 3.11 / 9.1.1 的斷言。
3. **未驗證**:`verify_gates.py` 在本機執行時,本 repo `.dev/` 是否確實不變。只有靜態推論(P5);要等 Station 6 的步驟 4 實測。
   此外,session 的 PreToolUse 閘門在執行期間是否寫本 repo 的 intercepts 帳本,未查。
4. **宿主佈局前提**:測試不在 `tests/` 底下的下游,producer 不會載入(P1 #10)。本票不處理。
5. **「無設定檔」狀態不在能力邊界內**:沒有 pyproject 的下游必須先建立一份才能初始化。
   這是收窄(fail-closed),不是缺陷;要擴張須走票重做盤點。
6. **「人審」無法機器驗證**:機制只能要求「canonical path 上有一個已 commit 的檔」。是誰、有沒有審,框架看不到(同 CLAUDE.md「核准是一段文字,不帶身分」)。
7. **sync 端提示**:只規劃了 status 行,沒有規劃 sync 的 dry-run 列出「需建立 evidence policy」(P4)。
8. **logging 鎖步絆線**(〈四十五〉45.3):實作時必須放進宿主專用檔(P2-A 連帶影響);本票不實作。
9. **`tests/test_leak_scan.py` 的宿主樹掃描**(P2-A):它刻意斷言宿主狀態,而且出貨。它在下游的意義是否成立,本票不判定。
10. **機器化 pre-push**:裁決 5 的淨室驗證,本票規劃為程序步驟(P5),不做 hook。
11. 〈二十九〉29.1 第 3 點的殘餘照舊:TOCTOU、未 pin 版本。policy 的引入讓「改 policy 但未 commit」也進入同一類(該期間無法退紅)。
<!-- 逐字結束 -->

### C.6 P8 要 Jeff 裁的事

行號來源:S3g-0 的規劃檔第 428–443 行

<!-- 逐字開始 -->
## P8 要 Jeff 裁的事

| # | 題目 | 選項 | 建議 | 理由 |
|---|---|---|---|---|
| 1 | policy 載體 | **甲** 獨立檔 `.agents/evidence-policy.json`(JSON,schema v1);**乙** `pyproject.toml` 的 `[tool.monkeyleash.evidence-policy]` | 甲 | 位置與設定檔型態脫鉤(I-1 不受將來擴張影響);沒有 pyproject 的 repo 也有地方放;解析不依賴 `tomllib`;identity 不被 pyproject 的無關改動牽動 |
| 2 | 誰解析 policy | **A** producer 依 I-3 從 HEAD blob 解析,記入 session,consumer 驗型別與 identity;**B** consumer 在 status 時依記錄的 blob sha 以 git 重解析 | A | 與既有 `config_blobs` 同一套模式;歷史 run 依當時的 policy 判定,不被事後重審;`file_coverage` 不必依賴 status 當下的 git |
| 3 | policy 列出能力邊界外的值 | **A** 整份 policy 不合格 ⇒ unknown;**B** 取交集,界外值靜默忽略 | A | 兩者都不會擴張(都滿足「只能收窄」),但 B 會把宿主的誤解藏起來,而且 status 會顯示「有效」;A 會出聲 |
| 4 | test_d4 處置 | **A** 只把 test_d4 原樣搬到宿主專用檔(skip);**B** 刪除,只換成框架推導測試 + verdict 時的機器鎖步;**C** = B + 宿主專用檔保留 agent-gates 自身的鎖步(原樣保留〈三十一〉裁決 3 的「git show HEAD、不得 skip」,只改適用位置) | C | A 留著常數,第二層修不好;B 會失去 agent-gates 自身「policy ↔ pyproject」的獨立檢查;C 兩層都顧到,且不違反票 16(不轉 skip) |
| 5 | 環境相依正控(P2-B) | **A** 3g / 4g 一併在共用 driver 固定版本事實;**B** 列殘餘,另開追蹤票 | A | 裁決 4 (正一) 要求框架測試在新 repo 全綠;下游若不是 3.11 + 9.1.1,B 會重演本次 CI 的形狀(紅與下游無關)。代價:授權 3 會動兩個 driver |
| 6 | 初始化 | **A** 安裝器只在非 canonical 路徑寫範本(內容 = B 常數)+ decisions-pending + status 顯示 policy 狀態;**B** 另做 `draft` 指令,從本機觀察值產草稿 | A | 不自動信任首次觀察值;status 行讓「未初始化 ⇒ 永遠 unknown」不再靜默。B 的方便正是風險所在 |

**不需裁、已依原則定案的設計**(有異議請指出):
- canonical path 與 schema 屬框架常數(裁決 6)。
- 缺 policy 與各種不一致一律 unknown(裁決 3、6)。
- `committed_blobs` 改為逐路徑呼叫(P3 遷移第 3 點)。
- 「無設定檔」不在能力邊界內(P7 #5)。
<!-- 逐字結束 -->

---

## D. 本票 commit 清單

`git log --oneline de36ebcbab284ef11064a9943b5191750482dd93..b5db3734f6795d8a371e4f58b172e0a8ffb066eb` 原樣(12 筆,與 A.1 的 S6-1…S4G5 逐一對應):

<!-- 逐字開始 -->
```
b5db373 docs(145): M1-a Station 4g-5 —— 證據報告三句舊述加 S4G4 後更新註記
b127ae0 docs(145): M1-a Station 4g-4 —— POSIX 外部 clean-room 驗收 PASS;Station 4g = PASS / COMPLETED
2fe52d0 docs(145): M1-a Station 4g-3 —— 本機固定全套與 clean-room 驗收證據;待 POSIX 外部驗收
8e77755 fix(145): M1-a Station 4g-1c —— producer 區分「沒有 -o」與「override 事實取不到」(修法 B)
f581a02 test(145): M1-a Station 4g-1b —— 「沒有任何 override」正控與「override 事實取不到」鎖(2 支)
f4fa041 fix(145): M1-a Station 4g-1 —— host evidence policy(框架能力邊界 B ∩ 宿主 policy H)
3eb112b docs(145): M1-a Station 3g-1b-2 —— 紅燈證據(乾淨工作樹重跑)
83258dd test(145): M1-a Station 3g-1b —— 安裝範本與 status policy 狀態行紅燈(9 支)
7a15ea0 docs(145): M1-a Station 3g-2 —— 紅燈證據
2737e02 test(145): M1-a Station 3g-1 —— Host evidence policy 紅燈(33 支)
560f618 docs(145): M1-a Station 3g-0 —— 紅燈規劃(框架 self-test 錯置 + evidence policy 可移植性)
faf7cb4 docs(145): M1-a Station 6 —— push 紀錄、CI 淨室驗證 FAIL 與 Station 3g 裁決
```
<!-- 逐字結束 -->

---

## E. 程式差異(原樣)

以下 `<CODE_FILES>` / `<TEST_FILES>` 為 A.1 所列檔案,依 A.1 的順序傳給 `git diff -- <路徑...>`。

### E.1 `git diff de36ebcbab284ef11064a9943b5191750482dd93..8e7775526e462d984abb0992ed74c1e1aa3648dd -- <CODE_FILES>`(全部程式與測試改動)

<!-- 逐字開始 -->
```diff
diff --git a/.agents/evidence-policy.json b/.agents/evidence-policy.json
new file mode 100644
index 0000000..6e9aca1
--- /dev/null
+++ b/.agents/evidence-policy.json
@@ -0,0 +1,9 @@
+{
+  "schema": "monkeyleash.evidence-policy",
+  "version": 1,
+  "config_file": "pyproject.toml",
+  "committed_overrides": ["strict_markers=true"],
+  "python_versions": ["3.11"],
+  "pytest_versions": ["9.1.1"],
+  "dists": [["anyio", "4.15.0"]]
+}
diff --git a/.agents/portable-manifest.txt b/.agents/portable-manifest.txt
index 1ef4263..0545c50 100644
--- a/.agents/portable-manifest.txt
+++ b/.agents/portable-manifest.txt
@@ -100,6 +100,10 @@ bootstrap.sh                    skip
 # 那就是合併,而合併是逐次判斷、覆蓋是每次都跑,一個會出錯的合併比較糟。
 # 代價:框架每新增一個檔案,各目標 repo 要人手動補一行。接受。
 .agents/portable-manifest.txt   ask
+# 票 145 Station 4g:host evidence policy(canonical path)。**skip**:它描述的是**這個 repo** 接受哪些
+# 已提交設定與執行環境,每個 repo 自己的那一份只能由人放上去並 commit(〈四十八〉48.1 第 6 點)。
+# 照抄到下游等於替下游自動信任上游的環境 —— 那正是本票要拆掉的狀態。
+.agents/evidence-policy.json    skip
 scripts/skills-update.sh        copy
 # 票 84 專用的一次性探針(寫死 wusuowei-tw/monkeyleash、寫死那組 sha、
 # 讀本 repo 的 commit-map)。**標 skip 不標 copy**:照抄到下游,它會去打
@@ -114,6 +118,10 @@ scripts/e2e_authority_layer.py  skip
 # ── 綁死這個 repo,必須重新產生 ────────────────────────────────
 .agents/legacy-no-redlight.txt  generate
 .dev/                           generate
+# 票 145 Station 4g:evidence policy 範本,由安裝器以目標 repo 的 `redlight.policy_template()` 產生
+# (框架能力邊界常數的完整列舉,不是觀察值)。放在非 canonical 路徑,永遠不是 authority。
+# 不另放範本來源檔(常數只有 redlight 那一份)。
+.agents/evidence-policy.template.json generate
 
 # ── 框架的測試(閘門自己的) ───────────────────────────────────
 tests/conftest.py               copy
@@ -218,6 +226,7 @@ tests/test_declared_in_is_an_identity.py copy
 # 出貨的話它會在每個下游紅,而那些紅與新專案無關 —— 訓練人忽略訊號(F-031)。
 # 前例:`tests/test_adr_numbering.py` 同樣標 skip,同樣是 ADR 集合的性質。
 tests/test_adr_numbers_resolve_upstream.py skip
+tests/test_host_evidence_policy.py skip
 # 票 89 第 3 條:`KNOWN_GAPS` 每一項必須有票號。**出貨**:它驗的
 # `.claude/portable/g1_verify.py` 落在 `.claude/portable/` 前綴底下(標 copy),
 # 所以下游一定有那個 list —— 「帶走測試卻不帶走它驗的東西」那個形狀不成立。
diff --git a/.claude/hooks/redlight.py b/.claude/hooks/redlight.py
index 0be0050..0616c17 100644
--- a/.claude/hooks/redlight.py
+++ b/.claude/hooks/redlight.py
@@ -488,13 +488,42 @@ KNOWN_DISTS = (("anyio", "4.15.0"),)
 # (xiii) P1 的盤點只對這些 pytest 版本成立;換版後非 ini 的 CLI 選項要重新盤點。
 KNOWN_PYTEST_VERSIONS = ("9.1.1",)
 
-# (viii) 已提交 pyproject.toml 的 addopts 帶來的 override 清單(`--strict-markers` ⇒
-# `strict_markers=true`)。由 tests/test_redlight.py 的鎖步測試對照已提交的 addopts。
-COMMITTED_ADDOPTS_OVERRIDES = ("strict_markers=true",)
-
-# (x) 唯一可接受的設定檔(root 相對路徑);(xi) 工作樹內容必須等於 HEAD blob 的檔。
-CONFIG_FILE = "pyproject.toml"
-COMMITTED_FILES = (CONFIG_FILE, ROOT_CONFTEST)
+# (x) 框架盤點過的設定檔型態(root 相對路徑;P1 只盤點了 pyproject 的 `[tool.pytest.ini_options]`)。
+# 宿主用哪一個由 evidence policy 的 `config_file` 指定,必須屬於這裡。
+FRAMEWORK_CONFIG_FILES = ("pyproject.toml",)
+
+# (xi) producer 記錄工作樹 blob 與 HEAD blob 的檔:框架能盤點的設定檔 + root producer 本身。
+# consumer 只看 `ROOT_CONFTEST` 與 policy 指定的 `config_file` 兩項。
+BLOB_FILES = FRAMEWORK_CONFIG_FILES + (ROOT_CONFTEST,)
+
+# ── 票 145 Station 4g —— Host evidence policy(〈四十八〉48.1;規劃檔 S3g-0 P3)
+# 上面的 `KNOWN_*` 與 `FRAMEWORK_CONFIG_FILES` 是框架能力邊界(B);宿主在 B 之內自己選擇接受什麼(H),
+# 寫在 canonical path 的 policy 檔、並且**已提交**。原本的 `COMMITTED_ADDOPTS_OVERRIDES` / `CONFIG_FILE`
+# 是 agent-gates 自己的宿主事實被寫成了框架常數 —— 淨室 repo 因此永遠 unknown(〈四十六〉46.2)。
+#
+# I-1:位置是框架常數,policy 內容不得指定位置(多一個鍵 ⇒ 整份不合格)。
+# I-2:認得的 (schema, version) 由框架列舉;policy 不能宣告自己用哪一套解析規則。
+POLICY_FILE = ".agents/evidence-policy.json"
+POLICY_SCHEMAS = (("monkeyleash.evidence-policy", 1),)
+POLICY_FIELDS = ("schema", "version", "config_file", "committed_overrides",
+                 "python_versions", "pytest_versions", "dists")
+
+# producer 記在 `completeness["evidence_policy"]` 的 7 鍵(〈五十一〉裁決 3)。
+EVIDENCE_POLICY_KEYS = ("path", "head", "worktree", "schema", "version", "policy", "committed_addopts")
+
+# status 的 policy 狀態行(〈五十〉50.1 第 3 點);文字以裁決為準。
+POLICY_UNINITIALIZED = u"未初始化"
+POLICY_UNCOMMITTED = u"未提交"
+POLICY_WORKTREE_DIFFERS = u"工作樹與 HEAD 不同"
+POLICY_UNKNOWN_FORMAT = u"格式不明"
+POLICY_OUTSIDE_BOUNDARY = u"超出框架能力邊界"
+POLICY_VALID = u"有效"
+
+# (viii) 的推導規則(pytest 9.1.1):`OverrideIniAction` 旗標(`_pytest/main.py:76-96`;
+# 動作本體 `_pytest/config/argparsing.py:491-503`)與 `-o` / `--override-ini`(`_pytest/helpconfig.py:113-116`)。
+OVERRIDE_FLAGS = {"--strict-config": "strict_config=true",
+                  "--strict-markers": "strict_markers=true",
+                  "--strict": "strict=true"}
 
 # 「執行完成」的終態:call 的 passed / failed、任何 phase 的 skip、明確辨識的 xfail / xpass。
 # 籠統的 "other"(4c 之前的 xfail 記法)不算 —— 不得讓 other 自動取得 completeness。
@@ -683,26 +712,274 @@ def _git_lines(root, args, expected):
     return lines
 
 
-def committed_blobs(root, paths=COMMITTED_FILES):
+def _git_bytes(root, args):
+    """一條 git 的原始 stdout;失敗 ⇒ None。不拋例外。"""
+    import subprocess
+    try:
+        proc = subprocess.run(["git", "-C", os.fspath(root)] + list(args),
+                              capture_output=True, timeout=30)
+    except Exception:
+        return None
+    return proc.stdout if proc.returncode == 0 else None
+
+
+def committed_blobs(root, paths=BLOB_FILES):
     """`{path: {"worktree": blob, "head": blob}}` —— 工作樹檔案(`git hash-object`,依
     .gitattributes 正規化)與 `HEAD:<path>` 的 blob。〈二十九〉2 (xi)。
 
     git 不可用、不是 repo、檔案不存在或任何一步出錯 ⇒ 該值 None(缺欄 ⇒ 不得為 `"true"`)。
+    **逐路徑各呼叫一次 git**(票 145 Station 4g;規劃檔 P3 遷移第 3 點):一次處理全部路徑的話,
+    缺一個檔整次失敗、所有路徑都成 None —— 淨室 repo 沒有 pyproject 時,conftest 的 blob 也一起遺失。
     **不拋例外**:這是 producer 在 sessionfinish 呼叫的,不得讓 pytest 失敗。
     """
-    paths = list(paths)
-    out = dict((p, {"worktree": None, "head": None}) for p in paths)
+    out = {}
+    for p in list(paths):
+        entry = {"worktree": None, "head": None}
+        try:
+            worktree = _git_lines(root, ["hash-object", p], 1)
+            head = _git_lines(root, ["rev-parse", "HEAD:" + p], 1)
+            entry["worktree"] = worktree[0] if worktree else None
+            entry["head"] = head[0] if head else None
+        except Exception:
+            pass
+        out[p] = entry
+    return out
+
+
+def addopts_overrides(value):
+    """已提交設定的 addopts **原值** → 它帶來的 override 清單,依出現順序(pytest 9.1.1;(viii) 的推導規則)。
+
+    輸入合約(票 145〈五十一〉裁決 3):`value` 是 HEAD config 經 TOML 解析後的 raw addopts —— 只接受
+    `str`(依 shlex 切開;ini 的 type="args",`_pytest/config/__init__.py:1547`)或 `list[str]`(逐項使用);
+    沒有 addopts 時呼叫端傳 `""`。**本函式不讀 git、工作樹或任何檔案。**
+      - `OVERRIDE_FLAGS` 的旗標 → 對應的 `<ini>=true`;`-o VAL` / `-oVAL` / `--override-ini VAL` /
+        `--override-ini=VAL` → `VAL`;其他 token 不產生 override;
+      - 型別不符、引號不成對、`-o` 後面沒有值 ⇒ None,由呼叫端判 unknown —— 不猜。
+
+    推導漏掉的寫法(例:合併短旗標 `-qo x`、長旗標縮寫)會讓「推導值 ≠ 實際 override」,
+    方向是 unknown(fail-closed),不是假綠:runtime 的 `override_ini` 仍要另外等於 policy(viii)。
+    """
+    import shlex
+    if isinstance(value, str):
+        try:
+            tokens = shlex.split(value)
+        except ValueError:
+            return None
+    elif isinstance(value, list) and all(isinstance(t, str) for t in value):
+        tokens = list(value)
+    else:
+        return None
+    out = []
+    i = 0
+    while i < len(tokens):
+        tok = tokens[i]
+        if tok in OVERRIDE_FLAGS:
+            out.append(OVERRIDE_FLAGS[tok])
+        elif tok in ("-o", "--override-ini"):
+            i += 1
+            if i >= len(tokens):
+                return None
+            out.append(tokens[i])
+        elif tok.startswith("--override-ini="):
+            out.append(tok.split("=", 1)[1])
+        elif tok.startswith("-o") and not tok.startswith("--"):
+            out.append(tok[2:])
+        i += 1
+    return out
+
+
+def _committed_addopts(root, config_file):
+    """`HEAD:<config_file>` 的 `[tool.pytest.ini_options].addopts` 原值(事實擷取,不判定)。
+
+    語意(〈五十一〉裁決 3,不得混用):
+      - `str` / `list[str]` = 原值照錄;
+      - `""` = config 存在且合法、`[tool.pytest.ini_options]` 段在、只是沒有 addopts 鍵;
+      - None = 取得或解析事實失敗:blob 讀不到、不是 UTF-8 / TOML、沒有 `[tool.pytest.ini_options]` 段、
+        addopts 型別不是 str / list[str]、或直譯器沒有 `tomllib`(3.11 起的標準庫;沒有它本來就在能力邊界外)。
+    只讀 HEAD 的 blob(`git cat-file`),不讀工作樹(工作樹 ≠ HEAD 由 (xi) 另外判)。
+    """
+    try:
+        import tomllib
+    except ImportError:
+        return None
+    raw = _git_bytes(root, ["cat-file", "blob", "HEAD:" + config_file])
+    if raw is None:
+        return None
     try:
-        worktree = _git_lines(root, ["hash-object"] + paths, len(paths))
-        head = _git_lines(root, ["rev-parse"] + ["HEAD:" + p for p in paths], len(paths))
-        for i, p in enumerate(paths):
-            out[p]["worktree"] = worktree[i] if worktree else None
-            out[p]["head"] = head[i] if head else None
+        doc = tomllib.loads(raw.decode("utf-8"))
+    except Exception:
+        return None
+    tool = doc.get("tool")
+    pytest_section = tool.get("pytest") if isinstance(tool, dict) else None
+    section = pytest_section.get("ini_options") if isinstance(pytest_section, dict) else None
+    if not isinstance(section, dict):
+        return None
+    if "addopts" not in section:
+        return ""
+    value = section["addopts"]
+    if isinstance(value, str) or (isinstance(value, list) and all(isinstance(v, str) for v in value)):
+        return value
+    return None
+
+
+def evidence_policy_facts(root):
+    """producer 的 policy 事實(票 145 規劃檔 P3 I-3;〈四十八〉48.1 第 2 點)。依序:
+
+      1. 固定 canonical path `POLICY_FILE`;
+      2. `git rev-parse HEAD:<path>` —— HEAD 沒有 ⇒ 停在這裡(`head` 為 None);
+      3. 第 2 步的輸出就是 HEAD committed blob;
+      4. `git hash-object <path>`(套用 .gitattributes,與 `committed_blobs` 同一手法)取 worktree blob;
+         ≠ HEAD blob 或缺檔 ⇒ 停在這裡;
+      5. 內容**只從 HEAD blob** 取(`git cat-file blob <sha>`)並解析 JSON —— 第 4 步的工作樹檔只做
+         identity 比對,之後不再讀;記下 `schema` / `version` 與整份內容 `policy`;
+      6. policy 的 `config_file` 屬於 `FRAMEWORK_CONFIG_FILES` 時,另記它在 HEAD 的 addopts 原值
+         `committed_addopts`(`_committed_addopts`),供 consumer 做「policy ↔ 已提交設定」的機器鎖步。
+
+    回傳 7 鍵 `{"path", "head", "worktree", "schema", "version", "policy", "committed_addopts"}`
+    (〈五十一〉裁決 3);走不下去的那一步之後的欄位都是 None。
+    **只擷取事實,不判定** —— 型別、schema、邊界、鎖步都由 consumer 驗。不拋例外(sessionfinish 呼叫)。
+    """
+    out = {"path": POLICY_FILE, "head": None, "worktree": None, "schema": None,
+           "version": None, "policy": None, "committed_addopts": None}
+    try:
+        head = _git_lines(root, ["rev-parse", "HEAD:" + POLICY_FILE], 1)
+        if not head:
+            return out
+        out["head"] = head[0]
+        worktree = _git_lines(root, ["hash-object", POLICY_FILE], 1)
+        out["worktree"] = worktree[0] if worktree else None
+        if out["worktree"] != out["head"]:
+            return out
+        raw = _git_bytes(root, ["cat-file", "blob", out["head"]])
+        if raw is None:
+            return out
+        doc = json.loads(raw.decode("utf-8"))
+        if not isinstance(doc, dict):
+            return out
+        out["schema"] = doc.get("schema")
+        out["version"] = doc.get("version")
+        out["policy"] = doc
+        if doc.get("config_file") in FRAMEWORK_CONFIG_FILES:
+            out["committed_addopts"] = _committed_addopts(root, doc["config_file"])
     except Exception:
         pass
     return out
 
 
+def _is_pair_list(v):
+    return isinstance(v, list) and all(
+        isinstance(d, list) and len(d) == 2 and all(isinstance(x, str) for x in d) for d in v)
+
+
+def policy_document_problems(policy):
+    """`(格式問題, 邊界問題)` 兩個 list;都空 = 合格。consumer 與 status 共用。
+
+    - 格式(I-1、I-2):不是物件、`(schema, version)` 不在 `POLICY_SCHEMAS`、鍵集合不恰為 `POLICY_FIELDS`、
+      欄位型別不對。**schema 不認得就不往下看** —— 別的 version 的欄位語意不是本版能判讀的。
+    - 邊界(I-4;〈四十八〉48.1 第 3 點 A):任一欄位超出框架能力邊界 ⇒ 整份不合格,不取交集、不靜默忽略。
+    """
+    if not isinstance(policy, dict):
+        return [u"不是物件"], []
+    schema, version = policy.get("schema"), policy.get("version")
+    if not (isinstance(schema, str) and type(version) is int and (schema, version) in POLICY_SCHEMAS):
+        return [u"schema / version 不認得"], []
+    fmt = []
+    keys = set(policy)
+    if keys != set(POLICY_FIELDS):
+        fmt.append(u"欄位不符(多 %s;缺 %s)" % (sorted(keys - set(POLICY_FIELDS)),
+                                              sorted(set(POLICY_FIELDS) - keys)))
+    if not isinstance(policy.get("config_file"), str):
+        fmt.append(u"config_file 型別不符")
+    for key in ("committed_overrides", "python_versions", "pytest_versions"):
+        if not _is_str_list(policy.get(key)):
+            fmt.append(u"%s 型別不符" % key)
+    if not _is_pair_list(policy.get("dists")):
+        fmt.append(u"dists 型別不符")
+    if fmt:
+        return fmt, []
+    bnd = []
+    if policy["config_file"] not in FRAMEWORK_CONFIG_FILES:
+        bnd.append(u"config_file")
+    if not set(policy["python_versions"]) <= set(KNOWN_PYTHON_VERSIONS):
+        bnd.append(u"python_versions")
+    if not set(policy["pytest_versions"]) <= set(KNOWN_PYTEST_VERSIONS):
+        bnd.append(u"pytest_versions")
+    if not set(tuple(d) for d in policy["dists"]) <= set(KNOWN_DISTS):
+        bnd.append(u"dists")
+    return [], bnd
+
+
+def policy_state(root):
+    """`<root>` 現在的 policy 狀態(status 行用;〈五十〉50.1 第 3 點)。依序:
+    HEAD 沒有 ⇒ 工作樹有檔為「未提交」、否則「未初始化」;工作樹 ≠ HEAD ⇒「工作樹與 HEAD 不同」;
+    格式問題 ⇒「格式不明」;邊界問題 ⇒「超出框架能力邊界」;其餘「有效」。
+
+    「有效」只說**文件本身**可用;一次 run 能不能退紅,還要看那次的環境與鎖步(`_completeness_verdict`)。"""
+    facts = evidence_policy_facts(root)
+    if facts["head"] is None:
+        exists = os.path.exists(os.path.join(os.fspath(root), *POLICY_FILE.split("/")))
+        return POLICY_UNCOMMITTED if exists else POLICY_UNINITIALIZED
+    if facts["worktree"] != facts["head"]:
+        return POLICY_WORKTREE_DIFFERS
+    fmt, bnd = policy_document_problems(facts["policy"])
+    if fmt:
+        return POLICY_UNKNOWN_FORMAT
+    if bnd:
+        return POLICY_OUTSIDE_BOUNDARY
+    return POLICY_VALID
+
+
+def policy_template():
+    """安裝器寫到非 canonical 路徑的範本內容(〈四十八〉48.1 第 6 點 A):框架能力邊界常數的完整列舉,
+    **不是本機觀察值**。`committed_overrides` 留空 —— 它必須等於宿主自己已提交 addopts 的推導,
+    框架不替人填。"""
+    schema, version = POLICY_SCHEMAS[0]
+    return {"schema": schema, "version": version,
+            "config_file": FRAMEWORK_CONFIG_FILES[0],
+            "committed_overrides": [],
+            "python_versions": list(KNOWN_PYTHON_VERSIONS),
+            "pytest_versions": list(KNOWN_PYTEST_VERSIONS),
+            "dists": [list(d) for d in KNOWN_DISTS]}
+
+
+def _effective_policy(ep):
+    """session 記下的 `evidence_policy` → 可用的 policy(dict);任何一項不成立 ⇒ None(unknown)。
+
+    驗:型別、path 為 canonical、`head == worktree` 且非 None、文件格式與邊界(`policy_document_problems`)、
+    記錄的 schema / version 與文件一致、`committed_overrides == addopts_overrides(committed_addopts)`
+    (機器鎖步,取代原 test_d4;`committed_addopts` 為 None 或推導不了 ⇒ unknown)。
+    policy 已驗過 ⊆ 能力邊界,所以 effective = B ∩ policy = policy。"""
+    if not isinstance(ep, dict) or ep.get("path") != POLICY_FILE:
+        return None
+    head = ep.get("head")
+    if not (isinstance(head, str) and head and ep.get("worktree") == head):
+        return None
+    policy = ep.get("policy")
+    fmt, bnd = policy_document_problems(policy)
+    if fmt or bnd:
+        return None
+    if ep.get("schema") != policy["schema"] or ep.get("version") != policy["version"]:
+        return None
+    committed = ep.get("committed_addopts")
+    if committed is None:
+        return None
+    derived = addopts_overrides(committed)
+    if derived is None or derived != policy["committed_overrides"]:
+        return None
+    return policy
+
+
+def _effective(boundary, chosen):
+    """effective = B ∩ policy(I-3 第 6 步)。"""
+    return [v for v in chosen if v in boundary]
+
+
+def _known_dists_accepted(plugin, accepted):
+    """known_dist 項目的每個 (名稱, 版本) 都要在 effective 的 dists 內;沒有 `dists` 事實 ⇒ 不成立。"""
+    dists = plugin.get("dists")
+    return _is_pair_list(dists) and bool(dists) and all(tuple(d) in accepted for d in dists)
+
+
 def _is_str_list(v):
     return isinstance(v, list) and all(isinstance(n, str) for n in v)
 
@@ -736,13 +1013,17 @@ def _completeness_problems(comp):
             problems.append("%s 缺欄或型別不符" % key)
     if not _is_str_list(comp.get("blocked")):
         problems.append("blocked 缺欄或型別不符")
+    # (xi):root producer 那一項必須在;policy 指定的設定檔那一項由 verdict 在知道 config_file 之後查。
     blobs = comp.get("config_blobs")
-    if not isinstance(blobs, dict) or not all(
-            isinstance(blobs.get(p), dict)
-            and all(blobs[p].get(k) is None or isinstance(blobs[p].get(k), str)
-                    for k in ("worktree", "head"))
-            for p in COMMITTED_FILES):
+    if not isinstance(blobs, dict) or ROOT_CONFTEST not in blobs or not all(
+            isinstance(b, dict)
+            and all(b.get(k) is None or isinstance(b.get(k), str) for k in ("worktree", "head"))
+            for b in blobs.values()):
         problems.append("config_blobs 缺欄或型別不符")
+    # 票 145 Station 4g:policy 事實(7 鍵;〈五十一〉裁決 3)。Station 4g 之前的 session 沒有 ⇒ 不合格 ⇒ unknown。
+    ep = comp.get("evidence_policy")
+    if not isinstance(ep, dict) or any(k not in ep for k in EVIDENCE_POLICY_KEYS):
+        problems.append("evidence_policy 缺欄或型別不符")
     # 〈三十五〉3 (xiv)–(xviii) 的事實。Station 4e 之前的 session 沒有這些欄位 ⇒ 不合格 ⇒ unknown。
     # 型別在這裡驗,malformed 的事實不得只靠 verdict 的值判斷而繞過。
     if type(comp.get("optimize")) is not int:            # int,不含 bool
@@ -763,15 +1044,19 @@ def _completeness_verdict(run, tf, idents):
     """位置參數已涵蓋 `tf` 之後,依〈二十三〉7 (i)–(vii) 判 `"true"` / `"false"` / `"unknown"`。
 
     - (i) 缺欄 / 型別錯 ⇒ unknown
-    - (vii)(vii′) 有 plugin 不在受支援範圍(含版本不在清單的 dist)⇒ unknown(在支援邊界之外,不知道)
+    - (P) evidence policy 不可用(未提交、工作樹 ≠ HEAD、格式不明、超出能力邊界、與 HEAD 設定檔的 addopts
+      推導不一致;`_effective_policy`)⇒ unknown(票 145 Station 4g;〈四十八〉48.1)。
+      以下的「effective」= 框架能力邊界 B ∩ policy
+    - (vii)(vii′) 有 plugin 不在受支援範圍(含版本不在清單的 dist),或 known_dist 的 (名稱, 版本) 不在
+      effective 的 `dists` ⇒ unknown(在支援邊界之外,不知道)
     - (xii) 有任何 `-p no:<name>` ⇒ unknown
-    - (xiii) pytest 版本不在 `KNOWN_PYTEST_VERSIONS` ⇒ unknown
-    - (viii) `override_ini` 不恰等於 `COMMITTED_ADDOPTS_OVERRIDES` ⇒ unknown(本次的收集定義被覆寫)
+    - (xiii) pytest 版本不在 effective 的 `pytest_versions` ⇒ unknown
+    - (viii) `override_ini` 不恰等於 policy 的 `committed_overrides` ⇒ unknown(本次的收集定義被覆寫)
     - (ix) 有 `-c` / `--config-file` ⇒ unknown(即使指向已提交的權威檔)
-    - (x) 實際採用的設定檔不是 `CONFIG_FILE` ⇒ unknown
-    - (xi) `COMMITTED_FILES` 任一檔的工作樹 blob ≠ HEAD blob,或取不到 ⇒ unknown
+    - (x) 實際採用的設定檔不是 policy 的 `config_file` ⇒ unknown
+    - (xi) `ROOT_CONFTEST` 與 policy 的 `config_file` 任一檔的工作樹 blob ≠ HEAD blob,或取不到 ⇒ unknown
     - (xiv) `sys.flags.optimize` 不是 0 ⇒ unknown(assert 可能沒有執行;〈三十五〉3)
-    - (xviii) Python major.minor 不在 `KNOWN_PYTHON_VERSIONS` ⇒ unknown
+    - (xviii) Python major.minor 不在 effective 的 `python_versions` ⇒ unknown
     - (xv)(xvii) `runxfail` / `trace` 不是 False ⇒ unknown;(xvi) pytest `-W` 有值 ⇒ unknown
       (assertmode 不判定:`optimize == 0` 時 plain 只影響 reporting)
     - (xix) `usepdb`(`--pdb`)不是 False ⇒ unknown(〈三十九〉39.3 第 3 點;與 (xvii) 同理:除錯模式下人可在
@@ -786,26 +1071,35 @@ def _completeness_verdict(run, tf, idents):
     comp = run.get("completeness")
     if _completeness_problems(comp):
         return "unknown"
+    policy = _effective_policy(comp["evidence_policy"])
+    if policy is None:
+        return "unknown"
+    accepted_dists = set(tuple(d) for d in _effective(KNOWN_DISTS, [tuple(d) for d in policy["dists"]]))
     if any(p["kind"] not in SUPPORTED_PLUGIN_KINDS for p in comp["plugins"]):
         return "unknown"
+    if any(p["kind"] == "known_dist" and not _known_dists_accepted(p, accepted_dists)
+           for p in comp["plugins"]):
+        return "unknown"
     if comp["blocked"]:
         return "unknown"
-    if comp["pytest_version"] not in KNOWN_PYTEST_VERSIONS:
+    if comp["pytest_version"] not in _effective(KNOWN_PYTEST_VERSIONS, policy["pytest_versions"]):
         return "unknown"
-    if comp["override_ini"] != list(COMMITTED_ADDOPTS_OVERRIDES):
+    if comp["override_ini"] != list(policy["committed_overrides"]):
         return "unknown"
     if comp["inifilename"] is not None:
         return "unknown"
-    if comp["inipath"] != CONFIG_FILE:
+    config_file = policy["config_file"]
+    if config_file not in FRAMEWORK_CONFIG_FILES or comp["inipath"] != config_file:
         return "unknown"
     blobs = comp["config_blobs"]
-    if not all(blobs[p]["worktree"] and blobs[p]["worktree"] == blobs[p]["head"]
-               for p in COMMITTED_FILES):
-        return "unknown"
+    for p in (config_file, ROOT_CONFTEST):
+        b = blobs.get(p)
+        if not (isinstance(b, dict) and b.get("worktree") and b.get("worktree") == b.get("head")):
+            return "unknown"
     options = comp["options"]
     if comp["optimize"] != 0:
         return "unknown"
-    if comp["python_version"] not in KNOWN_PYTHON_VERSIONS:
+    if comp["python_version"] not in _effective(KNOWN_PYTHON_VERSIONS, policy["python_versions"]):
         return "unknown"
     if options["runxfail"] is not False or options["trace"] is not False:
         return "unknown"
diff --git a/.claude/portable/install.py b/.claude/portable/install.py
index bde60dd..e9c76a6 100644
--- a/.claude/portable/install.py
+++ b/.claude/portable/install.py
@@ -383,14 +383,54 @@ def generate_legacy_list(target, go_live):
     return files
 
 
-def write_decisions_pending(target, buckets, carried_untracked, unmarked):
+POLICY_TEMPLATE = ".agents/evidence-policy.template.json"
+
+
+def _target_redlight(target):
+    """目標 repo 的 `.claude/hooks/redlight.py`(剛複製過去的那一份)。"""
+    import importlib.util
+    spec = importlib.util.spec_from_file_location(
+        "target_redlight", os.path.join(target, ".claude", "hooks", "redlight.py"))
+    mod = importlib.util.module_from_spec(spec)
+    spec.loader.exec_module(mod)
+    return mod
+
+
+def write_policy_template(target):
+    """evidence policy 範本 —— 寫到**非 canonical** 路徑(票 145〈四十八〉48.1 第 6 點 A)。
+
+    內容取自目標 repo 的 redlight `policy_template()`:框架能力邊界常數的完整列舉,**不是本機觀察值**
+    (不自動信任首次觀察值)。範本會隨安裝 commit 一起提交,但它不在 canonical path
+    (`redlight.POLICY_FILE`),**永遠不會被當成 authority**;canonical 那一份只有人放上去並 commit 才存在。
+    不另放範本來源檔:常數只有 redlight 那一份,範本由它產生,兩者不會漂移。
+    """
+    rl = _target_redlight(target)
+    dst = os.path.join(target, *POLICY_TEMPLATE.split("/"))
+    os.makedirs(os.path.dirname(dst), exist_ok=True)
+    with io.open(dst, "w", encoding="utf-8", newline="\n") as f:
+        f.write(json.dumps(rl.policy_template(), ensure_ascii=False, indent=2) + "\n")
+    return dst, rl.POLICY_FILE
+
+
+def write_decisions_pending(target, buckets, carried_untracked, unmarked, policy_file=None):
     """把需要人決定的項目**寫成檔案**,不只印終端機。
 
     印出來沒人看等於沒列(F-036 的同一個病:訊號不落地就等於沒有訊號)。
     寫成 docs/decisions-pending.md —— 人回頭找得到,也進得了版控、能被 review。
     沒有任何待決項目時回 None(不留空檔案佔位)。
+
+    `policy_file`(canonical evidence policy 路徑)給了 ⇒ 一律加一項「evidence policy 未初始化」
+    (票 145〈四十八〉48.1 第 6 點 A):安裝後 canonical policy 必然不存在,在人建立之前任何 run 都退不了紅。
     """
     sections = []
+    if policy_file:
+        sections.append(("evidence policy 未初始化 —— 在建立之前,任何測試執行都不會讓紅燈退休",
+                         [policy_file],
+                         "審閱 `%s`(框架能力邊界的完整列舉)→ 依本 repo 需要收窄;"
+                         "`committed_overrides` 必須等於本 repo 已提交設定檔 addopts 帶來的 override"
+                         "(例:`--strict-markers` ⇒ `strict_markers=true`)→ 存成 `%s` → commit。"
+                         "**這一步只有人做**;status 的 `evidence policy:` 行會顯示目前狀態。"
+                         % (POLICY_TEMPLATE, policy_file)))
     if buckets.get("ask"):
         sections.append(("需要你決定帶不帶(標記為 ask,安裝時沒有帶過去)",
                          buckets["ask"],
@@ -512,6 +552,7 @@ def main(target):
     generate_state(target)
     hook = install_hook(target)
     portable_hook, boot = install_portable_layer(target)
+    _template, policy_file = write_policy_template(target)
 
     run(["git", "add", "-A"], target)
     # **在 add 之後、commit 之前。** `update-index --chmod` 改的是既有 index 條目,
@@ -527,7 +568,8 @@ def main(target):
          "凍結既有 .py 的紅燈豁免清單(go-live %s)" % go_live[:7]], target)
 
     blocked = verify(target)
-    pending = write_decisions_pending(target, buckets, carried_untracked, unmarked)
+    pending = write_decisions_pending(target, buckets, carried_untracked, unmarked,
+                                      policy_file=policy_file)
 
     _out("裝好了:%s" % target)
     _out("  複製      %d 個檔案" % len(buckets["copy"]))
diff --git a/.claude/portable/status.py b/.claude/portable/status.py
index 55e7fcc..2e1ab31 100644
--- a/.claude/portable/status.py
+++ b/.claude/portable/status.py
@@ -557,6 +557,24 @@ def _invalid_count(facts, rl, ticket):
                 and rl.validate_session(r)])
 
 
+POLICY_SOURCE = u".agents/evidence-policy.json"
+
+
+def _policy_line(root, rl):
+    """`evidence policy: <狀態>`(票 145〈五十〉50.1 第 3 點)。狀態由該 root 的 redlight
+    `policy_state()` 判(未初始化 / 未提交 / 工作樹與 HEAD 不同 / 格式不明 / 超出框架能力邊界 / 有效);
+    本檔不另寫判準。沒有這一行的話,「未初始化 ⇒ 永遠 unknown、永遠退不了紅」對下游是靜默的。
+    舊版 redlight(無該函式)或判定拋例外 ⇒ 未記錄,不猜。"""
+    src = getattr(rl, "POLICY_FILE", None) or POLICY_SOURCE
+    if rl is None or not hasattr(rl, "policy_state"):
+        return _line(u"evidence policy", NO_FUNC.replace(u"gate", u"redlight"), src)
+    try:
+        state = rl.policy_state(root)
+    except Exception as e:
+        state = u"%s(%s)" % (UNRECORDED, type(e).__name__)
+    return _line(u"evidence policy", state, src)
+
+
 def _run_source(root, run_log, rl):
     left = _rel(root, run_log) if run_log else NO_FUNC
     right = (_rel(root, rl.session_log(root)) if rl is not None and hasattr(rl, "session_log")
@@ -846,6 +864,7 @@ def _evidence(root, gate, ticket):
             _invalid_count(facts, rl, ticket), tail,
             _last_run_text(facts, rl, ticket))
     out.append(_line(u"test-runs", val, _run_source(root, run_log, rl)))
+    out.append(_policy_line(root, rl))
 
     # ── intercepts 印**兩行**,不是一行 ────────────────────────────────
     # 合成一行的話,「這個月還沒有人被擋」與「這個 repo 從來沒有攔截紀錄」
diff --git a/.claude/portable/verify_gates.py b/.claude/portable/verify_gates.py
index b9f9e0a..7e81067 100644
--- a/.claude/portable/verify_gates.py
+++ b/.claude/portable/verify_gates.py
@@ -269,6 +269,224 @@ def restore(target):
     install.build_mirrors(target)
 
 
+# ── 票 145 Station 4g —— evidence policy 的淨室兩正三負(〈四十六〉46.4 第 4 點;規劃檔 S3g-0 P5)
+#
+# 接在「框架測試在新 repo 跑一次」之後。正一直接讀那一次留下的帳本;其餘四個各自從同一個
+# 基準 commit(安裝 + 規則情境之後的 HEAD)出發,做完 `_ev_restore` 回到基準 ——
+# 目標 repo 的 `.dev/` 是被追蹤的(安裝器不 ignore 它),不回到基準的話上一個情境的帳本與 commit
+# 會留給下一個。
+#
+# 探針只收一支測試檔:已提交的 pyproject 以 `python_files` 把收集範圍定成探針那一支
+# (那是宿主自己的已提交設定,不是窄選 —— consumer 鎖 `inipath` 與 blob,不看 `python_files` 的值)。
+# 否則每個情境的固定指令都要把整套框架測試再跑兩次。
+#
+# 佈置用的 commit 以 `--no-verify` 提交,同 `install.main` 自己的兩個 commit(`install.py` 的 main):
+# 這裡驗的是證據鏈,不是閘門;閘門由上面的規則情境各擋一次。
+
+EV_PROBE = "tests/test_evidence_probe.py"
+EV_RED = "def test_probe():\n    assert False\n"
+EV_GREEN = "def test_probe():\n    assert True\n"
+EV_PYPROJECT = ('[tool.pytest.ini_options]\n'
+                'testpaths = ["tests"]\n'
+                'python_files = ["test_evidence_probe.py"]\n')
+FIXED_COMMAND = [sys.executable, "-X", "utf8", "-m", "pytest", "-q"]
+
+
+def load_target_redlight(target):
+    """每次重新載入(帳本是讀檔,模組本身不快取 run 事實;重新載入只是避免沿用上一個情境的模組狀態)。"""
+    spec = importlib.util.spec_from_file_location(
+        "target_redlight", os.path.join(target, ".claude", "hooks", "redlight.py"))
+    mod = importlib.util.module_from_spec(spec)
+    spec.loader.exec_module(mod)
+    return mod
+
+
+def _ev_status(target):
+    """在子行程跑目標 repo 自己的 status.py,回傳 `{欄位: 值}`(值去掉 `(source: …)`)。"""
+    _rc, out = sh([sys.executable, "-X", "utf8",
+                   os.path.join(target, ".claude", "portable", "status.py"), "--root", target],
+                  target, check=False)
+    fields = {}
+    for line in out.splitlines():
+        key, sep, rest = line.partition(": ")
+        if sep:
+            fields[key.strip()] = rest.split("  (source:")[0].strip()
+    return fields
+
+
+def _ev_set_ticket(target, ticket):
+    p = os.path.join(target, ".dev", "pipeline.json")
+    io.open(p, "w", encoding="utf-8", newline="\n").write(
+        json.dumps({"current_stage": "implement", "feature": "verify",
+                    "ticket_id": ticket, "updated": ""}, ensure_ascii=False, indent=2) + "\n")
+
+
+def _ev_matching_policy(target):
+    """正二的 policy:值 = 當下環境 ∩ 框架能力邊界(規劃檔 P5)。不在邊界內的環境 ⇒ 對應欄位為空,
+    正二會因此不成立 —— 那是正確的(那個環境本來就退不了紅),而失敗訊息會點名正二。"""
+    from importlib import metadata
+    rl = load_target_redlight(target)
+    here = "%d.%d" % tuple(sys.version_info[:2])
+    try:
+        pytest_version = metadata.version("pytest")
+    except Exception:
+        pytest_version = None
+    dists = []
+    for name, version in rl.KNOWN_DISTS:
+        try:
+            if metadata.version(name) == version:
+                dists.append([name, version])
+        except Exception:
+            pass
+    return {"schema": rl.POLICY_SCHEMAS[0][0], "version": rl.POLICY_SCHEMAS[0][1],
+            "config_file": rl.FRAMEWORK_CONFIG_FILES[0],
+            "committed_overrides": [],
+            "python_versions": [v for v in rl.KNOWN_PYTHON_VERSIONS if v == here],
+            "pytest_versions": [v for v in rl.KNOWN_PYTEST_VERSIONS if v == pytest_version],
+            "dists": dists}
+
+
+def _ev_fixed_run(target, extra_env=None):
+    env = dict(os.environ)
+    env.pop("PYTEST_ADDOPTS", None)
+    env.update(extra_env or {})
+    p = subprocess.run(FIXED_COMMAND, cwd=target, capture_output=True, env=env)
+    return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")
+
+
+def _ev_red_then_green(target, ticket, commit_policy=True, dirty_policy=False, extra_env=None):
+    """佈置 pyproject + 失敗的探針(+ policy)並提交 → 固定指令(紅)→ 修好探針、提交
+    →(負二:policy 工作樹多一行)→ 固定指令(依 `extra_env`)。
+    回傳 `(第一次 rc, 第二次 rc, 第二次的 file_coverage, status 欄位, 第二次輸出尾行)`。"""
+    _ev_set_ticket(target, ticket)
+    rl = load_target_redlight(target)
+    policy_text = json.dumps(_ev_matching_policy(target), ensure_ascii=False, indent=2) + "\n"
+    write(target, "pyproject.toml", EV_PYPROJECT)
+    write(target, EV_PROBE, EV_RED)
+    write(target, rl.POLICY_FILE, policy_text)
+    tracked = ["pyproject.toml", EV_PROBE] + ([rl.POLICY_FILE] if commit_policy else [])
+    sh(["git", "add"] + tracked, target)
+    sh(["git", "commit", "-q", "--no-verify", "-m", "evidence %s: red probe" % ticket], target)
+    rc1, _out1 = _ev_fixed_run(target)
+    write(target, EV_PROBE, EV_GREEN)
+    sh(["git", "add", EV_PROBE], target)
+    sh(["git", "commit", "-q", "--no-verify", "-m", "evidence %s: fix probe" % ticket], target)
+    if dirty_policy:
+        write(target, rl.POLICY_FILE, policy_text + "\n")
+    rc2, out2 = _ev_fixed_run(target, extra_env)
+    runs = load_target_redlight(target).load_runs(target)
+    cov = rl.file_coverage(runs[-1], EV_PROBE) if runs else "(沒有 run 事實)"
+    tail = [l for l in out2.strip().splitlines() if l.strip()][-1:]
+    return rc1, rc2, cov, _ev_status(target), (tail[0] if tail else "(沒有輸出)")
+
+
+def _ev_verdict_line(fields, ticket, kind):
+    return fields.get("tests %s under ticket %s" % (kind, ticket), "")
+
+
+def ev_pos1_uninitialized(target, _base=None):
+    """正一:安裝後不動 —— 框架測試全綠(由 main 的上一步保證);那一次 run 對框架測試檔的
+    `file_coverage` 必須是 unknown,status 的 policy 行為「未初始化」。"""
+    rl = load_target_redlight(target)
+    runs = rl.load_runs(target)
+    if not runs:
+        return False, "淨室帳本沒有 run 事實 —— 框架測試那一次沒有留下 session"
+    last = runs[-1]
+    files = sorted(set(n.split("::", 1)[0] for n in last.get("collected") or []))
+    if not files:
+        return False, "最後一筆 session 沒有收集到任何檔"
+    covs = dict((f, rl.file_coverage(last, f)) for f in files)
+    not_unknown = sorted(f for f, c in covs.items() if c != "unknown")
+    state = _ev_status(target).get("evidence policy")
+    ok = not not_unknown and state == rl.POLICY_UNINITIALIZED
+    return ok, "%d 個框架測試檔皆 unknown=%s;evidence policy: %s%s" % (
+        len(files), not not_unknown, state,
+        (";非 unknown 的檔:%s" % ", ".join(not_unknown)) if not_unknown else "")
+
+
+def ev_pos2_initialized(target, _base=None):
+    """正二:已提交且與環境相符的 policy ⇒ 紅 → 固定全套 → true → 合法退休(status 端到端)。"""
+    ticket = "ev-pos2"
+    rc1, rc2, cov, fields, tail = _ev_red_then_green(target, ticket)
+    green = _ev_verdict_line(fields, ticket, "green")
+    red = _ev_verdict_line(fields, ticket, "red")
+    ok = (rc1 == 1 and rc2 == 0 and cov == "true"
+          and EV_PROBE in green and EV_PROBE not in red
+          and fields.get("evidence policy") == load_target_redlight(target).POLICY_VALID)
+    return ok, "rc %s→%s;file_coverage=%s;red=%s;green=%s;evidence policy: %s;%s" % (
+        rc1, rc2, cov, red, green, fields.get("evidence policy"), tail)
+
+
+def _ev_negative(target, ticket, **kw):
+    rc1, rc2, cov, fields, tail = _ev_red_then_green(target, ticket, **kw)
+    red = _ev_verdict_line(fields, ticket, "red")
+    green = _ev_verdict_line(fields, ticket, "green")
+    ok = rc1 == 1 and rc2 == 0 and cov == "unknown" and EV_PROBE in red and EV_PROBE not in green
+    return ok, "rc %s→%s;file_coverage=%s;red=%s;green=%s;evidence policy: %s;%s" % (
+        rc1, rc2, cov, red, green, fields.get("evidence policy"), tail)
+
+
+def ev_neg1_mismatch(target, _base=None):
+    """負一:policy 與環境不符 —— 修好後那一次多一個 policy 未列的 override ⇒ unknown,紅仍在。"""
+    return _ev_negative(target, "ev-neg1",
+                        extra_env={"PYTEST_ADDOPTS": "-o python_functions=test"})
+
+
+def ev_neg2_worktree_differs(target, _base=None):
+    """負二:HEAD 有 policy、工作樹多一行(未 commit)⇒ unknown,紅仍在。"""
+    return _ev_negative(target, "ev-neg2", dirty_policy=True)
+
+
+def ev_neg3_worktree_only(target, _base=None):
+    """負三:policy 只在工作樹、從未 commit ⇒ unknown,紅仍在。"""
+    return _ev_negative(target, "ev-neg3", commit_policy=False)
+
+
+# 鍵 ↔ 情境,比照 `SCENARIOS`。`tests/test_verify_gates.py` 斷言五個鍵都在。
+EVIDENCE_SCENARIOS = {
+    "pos1-uninitialized": ev_pos1_uninitialized,
+    "pos2-initialized": ev_pos2_initialized,
+    "neg1-mismatch": ev_neg1_mismatch,
+    "neg2-worktree-differs": ev_neg2_worktree_differs,
+    "neg3-worktree-only": ev_neg3_worktree_only,
+}
+
+EVIDENCE_LABELS = {
+    "pos1-uninitialized": "正一 未初始化",
+    "pos2-initialized": "正二 已初始化且相符",
+    "neg1-mismatch": "負一 policy / 環境不符",
+    "neg2-worktree-differs": "負二 HEAD 有、工作樹不同",
+    "neg3-worktree-only": "負三 工作樹有、HEAD 沒有",
+}
+
+
+def _ev_restore(target, base):
+    """回到證據情境的基準 commit(兩半,同 `restore`:追蹤側由 git、鏡像重建)。"""
+    sh(["git", "reset", "-q", "--hard", base], target)
+    sh(["git", "clean", "-qfd"], target)
+    install.build_mirrors(target)
+
+
+def run_evidence_scenarios(target):
+    """依序跑五個情境;每個各印一行(不合併)。回傳失敗的 `[(鍵, 細節)]`。"""
+    _rc, base = sh(["git", "rev-parse", "HEAD"], target)
+    base = base.strip()
+    failures = []
+    for key in ("pos1-uninitialized", "pos2-initialized", "neg1-mismatch",
+                "neg2-worktree-differs", "neg3-worktree-only"):
+        try:
+            ok, detail = EVIDENCE_SCENARIOS[key](target, base)
+        except SystemExit as e:
+            ok, detail = False, "情境執行失敗:%s" % e
+        finally:
+            if key != "pos1-uninitialized":
+                _ev_restore(target, base)
+        _out("    %-24s %s  %s" % (EVIDENCE_LABELS[key], "成立 ✓" if ok else "不成立 ✗", detail))
+        if not ok:
+            failures.append((key, detail))
+    return failures
+
+
 def run_scenario(target, code):
     marker = SCENARIOS[code](target)
     if marker == "predicate":
@@ -389,7 +607,16 @@ def main(workdir):
             "框架測試在新 repo 裡不是全綠 —— 那些紅與新專案無關,"
             "會訓練人忽略訊號。框架測試只能斷言框架的性質。")
 
-    _out("\n全部 %d 條規則各擋下一次,權威層偵測正常,框架測試在新 repo 全綠。"
+    # 票 145 Station 4g:evidence policy 的兩正三負。正一讀的就是上面那一次框架測試的帳本,
+    # 所以必須緊接在它之後、任何 reset 之前。
+    _out("\n=== evidence policy 淨室情境(兩正三負;每個情境各一行)===")
+    ev_failures = run_evidence_scenarios(target)
+    if ev_failures:
+        raise SystemExit("\n%d 個 evidence policy 情境沒有成立:%s"
+                         % (len(ev_failures), " ".join(EVIDENCE_LABELS[k] for k, _ in ev_failures)))
+
+    _out("\n全部 %d 條規則各擋下一次,權威層偵測正常,框架測試在新 repo 全綠,"
+         "evidence policy 兩正三負成立。"
          "\n安裝位置:%s" % (len(codes), target))
 
 
diff --git a/tests/conftest.py b/tests/conftest.py
index 7156c34..565deb3 100644
--- a/tests/conftest.py
+++ b/tests/conftest.py
@@ -342,6 +342,25 @@ def _flag(session, name):
     return bool(getattr(session, name))
 
 
+# 「屬性不存在」的 sentinel(票 145 Station 4g 修法 B):與「屬性存在、值為 None」分開。
+_MISSING = object()
+
+
+def _override_ini_of(option):
+    """交給 `normalize_overrides` 的 `override_ini` 原值。**先判欄位是否存在,再解讀值;只讀一次。**
+
+    pytest 9.1.1 的 `-o` 為 `action="append"`、沒有 default(`_pytest/helpconfig.py:112-119`),
+    未給任何 `-o` / OverrideIniAction 旗標時值為 None —— 語意是「沒有 override」,與「屬性取不到」不同:
+      - 屬性不存在 ⇒ None(事實取不到;consumer 判 unknown);
+      - 值為 None ⇒ 以 `[]` 交給 `normalize_overrides`,落帳 `[]`(事實取得成功:pytest 明確表示沒有 -o);
+      - 其他 ⇒ `normalize_overrides` 照舊(非 list ⇒ None)。
+    """
+    raw = getattr(option, "override_ini", _MISSING)
+    if raw is _MISSING:
+        return None
+    return raw if raw is not None else []
+
+
 def _completeness_of(session):
     """本次 session 的完整性事實。任何一步出錯 ⇒ None(寧可多紅,不讓 pytest 失敗)。
 
@@ -351,10 +370,19 @@ def _completeness_of(session):
     pyproject.toml 與本檔的工作樹 blob vs HEAD blob(git 子程序,失敗 ⇒ None);`pytest_version`
     取自本檔 import 的 `pytest`;`blocked` 是 `list_name_plugin()` 中值為 None 的名稱(`-p no:`)。
     路徑型事實一律轉成 root 相對路徑,不落帳絕對路徑。
+    `override_ini` 先判屬性是否存在(`_override_ini_of`):pytest 9.1.1 的 -o 為 action="append" 無 default,
+    未給時為 None,語意是「沒有 override」(落帳 `[]`),與「屬性取不到」(落帳 None ⇒ unknown)不同。
 
     票 145 Station 4e(〈三十五〉3 (xiv)–(xviii)、4)另記 pass 有效性的事實:`optimize` 與 `python_version`
     在此刻經模組層 `sys` 讀;`runxfail` / `pythonwarnings` / `trace` 隨 `COMPLETENESS_OPTIONS` 記在 `options`。
     路徑型 metadata 依欄位類別正規化(F3-甲):相對路徑以 `invocation_params.dir` 解析。
+
+    票 145 Station 4g(〈四十八〉48.1 第 2 點 A)另記 host evidence policy 的事實 `evidence_policy`(7 鍵),
+    依規劃檔 P3 I-3 的六步:HEAD 有沒有 → HEAD blob → 工作樹 blob(`git hash-object`)是否相同 →
+    內容**只從 HEAD blob**(`git cat-file`)解析 → schema / version → 記錄;另記 policy 指定的設定檔
+    在 HEAD 的 addopts 原值。工作樹的 policy 檔只做 identity 比對,之後不再讀。步驟本體在
+    `redlight.evidence_policy_facts`(與 `committed_blobs` 同一處,status 共用);本檔只擷取事實,不判定。
+    舊版 redlight.py(下游未同步)沒有該函式 ⇒ 記 None(涵蓋未知)。
     """
     try:
         if _pre_narrowing_broken:
@@ -375,12 +403,13 @@ def _completeness_of(session):
             "plugins": _redlight.classify_plugins(_ROOT, name_plugins,
                                                   pm.list_plugin_distinfo()),
             "blocked": _redlight.blocked_plugins(name_plugins, _ROOT),
-            "override_ini": _redlight.normalize_overrides(getattr(option, "override_ini", None),
-                                                          _ROOT, inv_dir),
+            "override_ini": _redlight.normalize_overrides(_override_ini_of(option), _ROOT, inv_dir),
             "inifilename": _redlight.normalize_config_path(getattr(option, "inifilename", None),
                                                            _ROOT, inv_dir),
             "inipath": _redlight.normalize_config_path(getattr(cfg, "inipath", None), _ROOT),
             "config_blobs": _redlight.committed_blobs(_ROOT),
+            "evidence_policy": (_redlight.evidence_policy_facts(_ROOT)
+                                if hasattr(_redlight, "evidence_policy_facts") else None),
             "pytest_version": version if isinstance(version, str) else None,
             "optimize": _optimize_flag(),
             "python_version": _python_version(),
diff --git a/tests/test_host_evidence_policy.py b/tests/test_host_evidence_policy.py
new file mode 100644
index 0000000..ac1fd02
--- /dev/null
+++ b/tests/test_host_evidence_policy.py
@@ -0,0 +1,91 @@
+# -*- coding: utf-8 -*-
+"""宿主專用:agent-gates **自己**已提交的 evidence policy ↔ 已提交的 `pyproject.toml`(票 145)。
+
+**不出貨**(`.agents/portable-manifest.txt` 標 `skip`)。它斷言的是**這個 repo** 的已提交事實,
+而那兩個檔都是各 repo 自己的(`pyproject.toml` 標 `skip`、`.agents/evidence-policy.json` 標 `skip`)——
+帶到下游就是「帶走測試卻不帶走它讀的檔案 = 到站即紅」(票 145〈四十六〉46.2 的 CI 失敗正是這個形狀)。
+
+規格沿用票 145〈三十一〉裁決 3,**語意不變、只改適用位置**(〈四十八〉48.1 第 4 點,Jeff 明文):
+  - 來源固定為 `git show HEAD:<path>`(在 repo 根執行,唯讀);不讀工作樹檔案;
+  - 不得以 tmp repo 或寫死的 addopts 字串代替 —— 用自造設定只會驗到測試自己;
+  - git 不可用或讀取失敗 ⇒ **失敗**(不得 skip、不得靜默通過);
+  - 唯讀:不寫任何檔案、不改 repo 狀態。
+
+推導(pytest 9.1.1;與原 test_d4 相同,**在本檔獨立實作**,不呼叫 redlight 的推導函式 ——
+材料不從被量的東西身上拿):addopts 以 shlex 切開(`_pytest/config/__init__.py:1547`),逐一對應:
+  - `OverrideIniAction` 旗標(`_pytest/main.py:76-96`):`--strict-config` → `strict_config=true`、
+    `--strict-markers` → `strict_markers=true`、`--strict` → `strict=true`;
+  - `-o` / `--override-ini KEY=VAL`(`_pytest/helpconfig.py:113-116`)→ `KEY=VAL`;
+  - 其他旗標不產生 override 項目。
+"""
+
+import importlib.util
+import json
+import pathlib
+import shlex
+import subprocess
+
+ROOT = pathlib.Path(__file__).resolve().parents[1]
+
+POLICY_FILE = ".agents/evidence-policy.json"
+
+
+def _load_redlight():
+    spec = importlib.util.spec_from_file_location(
+        "redlight_for_host_policy", str(ROOT / ".claude" / "hooks" / "redlight.py"))
+    mod = importlib.util.module_from_spec(spec)
+    spec.loader.exec_module(mod)
+    return mod
+
+
+def _git_show_head(rel):
+    proc = subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:" + rel], capture_output=True)
+    assert proc.returncode == 0, (rel, proc.stderr)
+    return proc.stdout.decode("utf-8")
+
+
+def _derive_overrides(addopts):
+    tokens = shlex.split(addopts) if isinstance(addopts, str) else list(addopts or [])
+    flags = {"--strict-config": "strict_config=true",
+             "--strict-markers": "strict_markers=true",
+             "--strict": "strict=true"}
+    out = []
+    i = 0
+    while i < len(tokens):
+        tok = tokens[i]
+        if tok in flags:
+            out.append(flags[tok])
+        elif tok in ("-o", "--override-ini"):
+            i += 1
+            out.append(tokens[i])
+        elif tok.startswith("--override-ini="):
+            out.append(tok.split("=", 1)[1])
+        elif tok.startswith("-o"):
+            out.append(tok[2:])
+        i += 1
+    return out
+
+
+def test_the_committed_policy_matches_the_committed_pyproject():
+    """票 145 Station 3g #27。分類:behavior-red(BASELINE 560f618 上 HEAD 沒有 policy ⇒ `git show` 失敗)。
+
+    agent-gates 的 `HEAD:.agents/evidence-policy.json`:
+      - schema / version 為 `monkeyleash.evidence-policy` / 1;
+      - `config_file == "pyproject.toml"`;
+      - `committed_overrides` 恰等於 `HEAD:pyproject.toml` 的 `[tool.pytest.ini_options].addopts` 依上方規則的推導;
+      - 版本與 dist 欄位都在框架能力邊界之內(〈四十八〉48.1 第 3 點:界外 ⇒ 整份不合格,宿主自己這份必須先過)。
+    """
+    try:
+        import tomllib as _toml
+    except ImportError:                      # Python 3.10
+        import tomli as _toml
+    policy = json.loads(_git_show_head(POLICY_FILE))
+    cfg = _toml.loads(_git_show_head("pyproject.toml"))
+    addopts = cfg["tool"]["pytest"]["ini_options"].get("addopts")
+    assert policy.get("schema") == "monkeyleash.evidence-policy" and policy.get("version") == 1, policy
+    assert policy.get("config_file") == "pyproject.toml", policy
+    assert policy.get("committed_overrides") == _derive_overrides(addopts), (addopts, policy)
+    redlight = _load_redlight()
+    assert set(policy.get("python_versions") or ()) <= set(redlight.KNOWN_PYTHON_VERSIONS), policy
+    assert set(policy.get("pytest_versions") or ()) <= set(redlight.KNOWN_PYTEST_VERSIONS), policy
+    assert set(tuple(d) for d in policy.get("dists") or ()) <= set(redlight.KNOWN_DISTS), policy
diff --git a/tests/test_install.py b/tests/test_install.py
index 89a0794..37e9695 100644
--- a/tests/test_install.py
+++ b/tests/test_install.py
@@ -461,3 +461,208 @@ class TestGitignoreDedupIsLineExact:
         want = list(install_mod.GITIGNORE_FRAMEWORK) + list(install_mod.GITIGNORE_SECRETS)
         missing = [p for p in want if p not in got]
         assert not missing, "註解吃掉了 %d 條真防護行:%r" % (len(missing), missing)
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# 票 145 Station 3g-1b 紅燈 —— 安裝範本(〈四十八〉48.1 第 6 點;〈五十〉50.1)
+#
+# 合約:安裝器只在**非 canonical** 路徑 `.agents/evidence-policy.template.json` 寫範本(內容 = 框架能力邊界常數),
+# 並在 `docs/decisions-pending.md` 加 evidence policy 初始化的待決項;canonical `.agents/evidence-policy.json`
+# **只有人**放上去並 commit 才存在。
+# 下文 `<BASELINE>` = 7a15ea081da1bf23cc79e04aef76065438f65219(S3G2)。
+#
+# **呼叫真的 `install.main()`**,在 tmp 目錄裝一個新 repo(module 範圍只裝一次,三支共用)。
+# `install.main()` 會往 `sys.path` 插入目標 repo 的 hooks 目錄、從 `sys.modules` 移除 `gate`
+# (`.claude/portable/install.py:364-366`)—— fixture 先存再還原,不讓它漏到其他測試。
+# **不斷言範本「已提交」或「未提交」**(〈五十〉50.1 第 2 點:那不是本票裁決的需求)。
+# 本段 helper 全部新寫;既有 helper(`_load`)只呼叫、不修改。
+# ─────────────────────────────────────────────────────────────────────────────
+
+_G_POLICY_FILE = ".agents/evidence-policy.json"
+_G_TEMPLATE_FILE = ".agents/evidence-policy.template.json"
+_G_TEST_X = ("tests/test_x.py::test_a", "tests/test_x.py::test_b")
+
+
+@pytest.fixture(scope="module")
+def g3_installed_repo(tmp_path_factory):
+    """`install.main(<tmp>/repo)` 裝好的新 repo(真安裝)。回傳 repo 路徑(pathlib.Path)。"""
+    import sys
+    target = tmp_path_factory.mktemp("g3-install") / "repo"
+    mp = pytest.MonkeyPatch()
+    try:
+        mp.setattr(sys, "path", list(sys.path))
+        if "gate" in sys.modules:
+            mp.setitem(sys.modules, "gate", sys.modules["gate"])
+        mod = _load("install_for_g3_template", "install.py")
+        mod.main(str(target))
+    finally:
+        mp.undo()
+    return target
+
+
+def _g_load_from(path, name):
+    spec = importlib.util.spec_from_file_location(name, str(path))
+    m = importlib.util.module_from_spec(spec)
+    spec.loader.exec_module(m)
+    return m
+
+
+class _GInstallItem(pytest.Item):
+    """真的 `pytest.Item` 子類;只帶 nodeid(producer 以 isinstance 判斷)。"""
+
+    def runtest(self):
+        pass
+
+
+def _g_install_item(nodeid):
+    it = object.__new__(_GInstallItem)
+    it._nodeid = nodeid
+    it.name = nodeid.split("::")[-1]
+    return it
+
+
+class _GSys(object):
+    """conftest 所見的 `sys` 替身:版本固定為 3.11、`flags.optimize` 為 0,其他屬性轉給真的 `sys`。"""
+
+    def __init__(self):
+        import sys as real
+        import types
+        self._real = real
+        self.version_info = (3, 11, 0, "final", 0)
+        self.flags = types.SimpleNamespace(optimize=0)
+
+    def __getattr__(self, name):
+        return getattr(self._real, name)
+
+
+class _GPluginManager(object):
+    def __init__(self, name_plugins):
+        self._name_plugins = list(name_plugins)
+
+    def list_name_plugin(self):
+        return list(self._name_plugins)
+
+    def list_plugin_distinfo(self):
+        return []
+
+    def is_blocked(self, name):
+        return False
+
+    def get_plugin(self, name):
+        return dict(self._name_plugins).get(name)
+
+    def has_plugin(self, name):
+        return self.get_plugin(name) is not None
+
+
+def _g_drive_fixed_command(c, root):
+    """依 pytest 9.1.1 的呼叫順序驅動**安裝出來的** `tests/conftest.py`,模擬一次固定全套
+    `python -X utf8 -m pytest -q`:tests/test_x.py 的兩個身分全收集、全 passed、exit 0;
+    選項全部關閉、`override_ini == ["strict_markers=true"]`、`inipath` 為 `pyproject.toml`;
+    plugin 只有 `_pytest` 內建與 root conftest。"""
+    import types
+    files = {"tests/test_x.py": list(_G_TEST_X)}
+    for path, ids in sorted(files.items()):
+        report = types.SimpleNamespace(nodeid=path, result=[_g_install_item(n) for n in ids],
+                                       failed=False, passed=True, skipped=False, outcome="passed")
+        collector = types.SimpleNamespace(nodeid=path, path=root / path)
+        gen = c.pytest_make_collect_report(collector)
+        next(gen)
+        try:
+            gen.send(report)
+        except StopIteration:
+            pass
+        c.pytest_collectreport(report)
+    option_values = {"lf": False, "last_failed_no_failures": "all", "stepwise": False, "stepwise_skip": False,
+                     "maxfail": None, "collectonly": False, "setuponly": False, "setupplan": False,
+                     "runxfail": False, "pythonwarnings": None, "trace": False, "usepdb": False,
+                     "override_ini": ["strict_markers=true"], "inifilename": None, "pyargs": False}
+    option = types.SimpleNamespace(**option_values)
+    pm = _GPluginManager([("main", types.ModuleType("_pytest.main")),
+                          (os.path.join(str(root), "tests", "conftest.py"), c)])
+    config = types.SimpleNamespace(
+        args=["tests"], args_source=pytest.Config.ArgsSource.TESTPATHS, rootpath=root,
+        invocation_params=types.SimpleNamespace(args=("-q",), plugins=None, dir=root),
+        option=option, pluginmanager=pm, inipath=root / "pyproject.toml",
+        getoption=lambda name, default=None, skip=False: getattr(option, name, default))
+    selected = [n for ids in files.values() for n in ids]
+    session = types.SimpleNamespace(items=[_g_install_item(n) for n in selected],
+                                    testscollected=len(selected), config=config,
+                                    shouldstop=False, shouldfail=False)
+    c.pytest_collection_finish(session)
+    for nodeid in selected:
+        for when in ("setup", "call", "teardown"):
+            c.pytest_runtest_logreport(types.SimpleNamespace(
+                nodeid=nodeid, fspath=nodeid.split("::", 1)[0], when=when, outcome="passed",
+                passed=True, failed=False, skipped=False))
+    c.pytest_sessionfinish(session, 0)
+
+
+class TestEvidencePolicyTemplate:
+
+    def test_g3_install_writes_the_template_outside_the_canonical_path(self, g3_installed_repo, monkeypatch):
+        """I1(〈五十〉50.1 第 3 點)。分類:behavior-red。
+
+        `install.main(<tmp 新 repo>)` 之後:`.agents/evidence-policy.template.json` 存在;
+        `.agents/evidence-policy.json`(canonical)**不存在**。
+        再以安裝出來的**真實** producer(`tests/conftest.py`)與 consumer(`.claude/hooks/redlight.py`)驗證:
+        在該 repo 提交一份 `pyproject.toml`(與 install.main 自己的 commit 同樣以 `--no-verify` 提交,
+        `.claude/portable/install.py:520, :526`)後,模擬一次固定全套(版本事實固定為 3.11 / 9.1.1)——
+        session 合格且為 A,但 `file_coverage` 不得為 `"true"`:範本位於非 canonical path,
+        無論是否 tracked / committed,都不得成為 evidence authority。
+        BASELINE 上失敗的原因:`<BASELINE>:.claude/portable/install.py:497-530` 不寫任何範本。
+        """
+        import subprocess
+        root = g3_installed_repo
+        assert (root / _G_TEMPLATE_FILE).is_file(), "安裝器沒有寫 %s" % _G_TEMPLATE_FILE
+        assert not (root / _G_POLICY_FILE).exists(), "安裝器寫了 canonical policy —— 那等於自動信任"
+        with open(str(root / "pyproject.toml"), "w", encoding="utf-8", newline="\n") as f:
+            f.write(u'[tool.pytest.ini_options]\ntestpaths = ["tests"]\naddopts = "-ra --strict-markers"\n')
+        for args in (["add", "pyproject.toml"], ["commit", "-q", "--no-verify", "-m", "g3 pyproject"]):
+            subprocess.run(["git"] + args, cwd=str(root), capture_output=True, check=True)
+        c = _g_load_from(root / "tests" / "conftest.py", "conftest_in_installed_repo_g3")
+        assert c._redlight is not None, "安裝出來的 conftest 載不到 redlight"
+        monkeypatch.setattr(c, "sys", _GSys(), raising=False)
+        monkeypatch.setattr(pytest, "__version__", "9.1.1")
+        _g_drive_fixed_command(c, c._ROOT)
+        rl = _g_load_from(root / ".claude" / "hooks" / "redlight.py", "redlight_in_installed_repo_g3")
+        runs = rl.load_runs(str(c._ROOT))
+        assert runs, runs
+        run = runs[-1]
+        assert rl.validate_session(run) == [], run
+        assert rl.run_state(run) == "A", run
+        got = rl.file_coverage(run, "tests/test_x.py")
+        assert got != "true", got
+
+    def test_g3_the_template_lists_exactly_the_capability_boundary(self, g3_installed_repo):
+        """I2(〈五十〉50.1 第 3 點)。分類:behavior-red。
+
+        範本為 schema `"monkeyleash.evidence-policy"` v1;`python_versions` / `pytest_versions` / `dists`
+        分別等於安裝出來的 redlight 的框架能力邊界常數(`KNOWN_PYTHON_VERSIONS` / `KNOWN_PYTEST_VERSIONS` /
+        `KNOWN_DISTS`);`config_file` 屬 `FRAMEWORK_CONFIG_FILES`。常數以 getattr 取得,取不到 ⇒ 失敗。
+        BASELINE 上失敗的原因:沒有範本檔(`<BASELINE>:.claude/portable/install.py:497-530`)。
+        """
+        import json
+        root = g3_installed_repo
+        path = root / _G_TEMPLATE_FILE
+        assert path.is_file(), "安裝器沒有寫 %s" % _G_TEMPLATE_FILE
+        template = json.loads(path.read_text(encoding="utf-8"))
+        rl = _g_load_from(root / ".claude" / "hooks" / "redlight.py", "redlight_for_template_g3")
+        assert template.get("schema") == "monkeyleash.evidence-policy" and template.get("version") == 1, template
+        assert template.get("python_versions") == list(getattr(rl, "KNOWN_PYTHON_VERSIONS")), template
+        assert template.get("pytest_versions") == list(getattr(rl, "KNOWN_PYTEST_VERSIONS")), template
+        assert template.get("dists") == [list(d) for d in getattr(rl, "KNOWN_DISTS")], template
+        assert template.get("config_file") in getattr(rl, "FRAMEWORK_CONFIG_FILES"), template
+
+    def test_g3_decisions_pending_asks_to_initialize_the_policy(self, g3_installed_repo):
+        """I3(〈五十〉50.1 第 3 點)。分類:behavior-red。
+
+        `docs/decisions-pending.md` 含 evidence policy 初始化的待決項,且點名 canonical 路徑
+        `.agents/evidence-policy.json`。
+        BASELINE 上失敗的原因:`<BASELINE>:.claude/portable/install.py:386-422` 的待決項沒有 evidence policy。
+        """
+        path = g3_installed_repo / "docs" / "decisions-pending.md"
+        assert path.is_file(), "安裝器沒有寫 docs/decisions-pending.md"
+        body = path.read_text(encoding="utf-8")
+        assert "evidence policy" in body.lower(), body
+        assert _G_POLICY_FILE in body, body
diff --git a/tests/test_redlight.py b/tests/test_redlight.py
index 877b131..6f444db 100644
--- a/tests/test_redlight.py
+++ b/tests/test_redlight.py
@@ -287,6 +287,14 @@ class _Session:
         self.testscollected = len(self.items)
 
 
+# 票 145 Station 4g 授權 G3(〈四十八〉48.1 第 5 點;規劃檔 S3g-0 P2-B):driver 把 conftest 所見的版本事實
+# 固定在能力邊界內,正控不再依賴執行它的直譯器 / pytest 版本。模組載入當下的真實版本記在這裡 ——
+# 測試在呼叫 driver **之前**自己設過 `pytest.__version__`(例:測「版本不在清單」的那支)時不覆蓋它。
+_REAL_PYTEST_VERSION = pytest.__version__
+_PINNED_PYTEST_VERSION = "9.1.1"
+_PINNED_PYTHON = (3, 11, 0, "final", 0)
+
+
 def _isolated_conftest(monkeypatch, tmp_path):
     c = TestTheRecorderCannotKillTheRunner._conftest()
     monkeypatch.setattr(redlight, "ROOT", str(tmp_path))
@@ -296,6 +304,10 @@ def _isolated_conftest(monkeypatch, tmp_path):
                         str(tmp_path / ".dev" / "pipeline.json"))
     monkeypatch.setattr(c, "_redlight", redlight)
     monkeypatch.setattr(c, "_ROOT", tmp_path)
+    monkeypatch.setattr(c, "sys", _e_sys(optimize=_e_real_sys.flags.optimize,
+                                         version_info=_EVersion(*_PINNED_PYTHON)), raising=False)
+    if pytest.__version__ == _REAL_PYTEST_VERSION:
+        monkeypatch.setattr(pytest, "__version__", _PINNED_PYTEST_VERSION)
     c._outcomes.clear()
     return c
 
@@ -1128,6 +1140,19 @@ _D_CACHEPROVIDER_BLOCKED = ("cacheprovider", "pytest_cacheprovider", "stepwise",
 _D_FULL = {"tests/test_x.py": [X_A, X_B]}
 _D_ONLY_B = {"tests/test_x.py": [X_B]}
 
+# 票 145 Station 4g 授權 G1(規劃檔 S3g-0 P6「需要的授權」1):與 baseline 相符的已提交 evidence policy ——
+# 已提交 addopts `-ra --strict-markers` ⇒ `strict_markers=true`;版本與 dist 等於 driver 固定的事實(授權 3)。
+_D_POLICY_FILE = ".agents/evidence-policy.json"
+_D_BASELINE_POLICY = {
+    "schema": "monkeyleash.evidence-policy",
+    "version": 1,
+    "config_file": "pyproject.toml",
+    "committed_overrides": list(_D_FIXED_OVERRIDES),
+    "python_versions": ["3.11"],
+    "pytest_versions": ["9.1.1"],
+    "dists": [["anyio", "4.15.0"]],
+}
+
 
 def _d_write(root, rel, text):
     p = pathlib.Path(str(root)) / rel
@@ -1146,10 +1171,11 @@ def _d_committed_root(root):
     conftest = pathlib.Path(str(root)) / "tests" / "conftest.py"
     conftest.parent.mkdir(parents=True, exist_ok=True)
     conftest.write_bytes((ROOT / "tests" / "conftest.py").read_bytes())
+    _d_write(root, _D_POLICY_FILE, json.dumps(_D_BASELINE_POLICY, ensure_ascii=False, indent=2) + u"\n")
     _d_git(root, "init", "-q")
     _d_git(root, "config", "user.email", "t@example.invalid")
     _d_git(root, "config", "user.name", "t")
-    _d_git(root, "add", "pyproject.toml", "tests/conftest.py")
+    _d_git(root, "add", "pyproject.toml", "tests/conftest.py", _D_POLICY_FILE)
     _d_git(root, "commit", "-q", "-m", "baseline")
     return root
 
@@ -1486,52 +1512,11 @@ class TestCollectionDefinitionCoverage:
         got = _d_coverage(tmp_path, monkeypatch)
         assert got == "true", got
 
-    def test_d4_the_committed_addopts_override_constant_matches_pyproject(self):
-        """D4-1(票 145〈三十一〉裁決 3;〈二十九〉2 (viii) 的鎖步測試)。Station 4d 授權新增。
-
-        鎖的是「`redlight.COMMITTED_ADDOPTS_OVERRIDES` ↔ agent-gates repo **真正提交**的
-        `pyproject.toml` addopts」。來源固定為 `git show HEAD:pyproject.toml`(在 repo 根執行,唯讀);
-        不讀工作樹、不用 tmp repo、不寫死 addopts 字串 —— 用自造的設定只會驗到測試自己。
-        git 不可用或讀取失敗 ⇒ 失敗(不 skip)。
-
-        推導(pytest 9.1.1):addopts 以 shlex 切開(ini 模式下 type="args",`_pytest/config/__init__.py:1547`;
-        放到 args 最前面一起解析,`:1559-1562`),逐一對應:
-          - `OverrideIniAction` 旗標(`_pytest/main.py:76-96`;動作本體 `_pytest/config/argparsing.py:491-503`):
-            `--strict-config` → `strict_config=true`、`--strict-markers` → `strict_markers=true`、
-            `--strict` → `strict=true`;
-          - `-o` / `--override-ini KEY=VAL`(`_pytest/helpconfig.py:113-116`,append)→ `KEY=VAL`;
-          - 其他旗標不產生 override 項目。
-        依出現順序組成清單,必須恰等於常數。
-        """
-        import shlex
-        try:
-            import tomllib as _toml
-        except ImportError:                      # Python 3.10
-            import tomli as _toml
-        proc = _d_subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:pyproject.toml"],
-                                 capture_output=True)
-        assert proc.returncode == 0, proc.stderr
-        cfg = _toml.loads(proc.stdout.decode("utf-8"))
-        addopts = cfg["tool"]["pytest"]["ini_options"]["addopts"]
-        tokens = shlex.split(addopts) if isinstance(addopts, str) else list(addopts)
-        flags = {"--strict-config": "strict_config=true",
-                 "--strict-markers": "strict_markers=true",
-                 "--strict": "strict=true"}
-        expected = []
-        i = 0
-        while i < len(tokens):
-            tok = tokens[i]
-            if tok in flags:
-                expected.append(flags[tok])
-            elif tok in ("-o", "--override-ini"):
-                i += 1
-                expected.append(tokens[i])
-            elif tok.startswith("--override-ini="):
-                expected.append(tok.split("=", 1)[1])
-            elif tok.startswith("-o"):
-                expected.append(tok[2:])
-            i += 1
-        assert list(redlight.COMMITTED_ADDOPTS_OVERRIDES) == expected, (addopts, expected)
+    # 原 `test_d4_the_committed_addopts_override_constant_matches_pyproject` 於票 145 Station 4g 刪除
+    # (〈四十八〉48.1 第 4 點 C,Jeff 明文修訂〈三十一〉裁決 3 的**適用位置**,語意不變):
+    # 常數 `COMMITTED_ADDOPTS_OVERRIDES` 已移進宿主 policy;框架那一半由 `TestAddoptsDerivation`(fixture)
+    # 與 verdict 時的機器鎖步承接,agent-gates 自身「policy ↔ pyproject」的鎖步由宿主專用、不出貨的
+    # tests/test_host_evidence_policy.py 承接(git show HEAD、讀不到即失敗、不 skip)。
 
 
 # ─────────────────────────────────────────────────────────────────────────────
@@ -2142,3 +2127,408 @@ class TestIdentifierFullMatch:
         broken = _e_run(tmp_path, monkeypatch, blocked=("abc\n",))
         assert control["completeness"]["blocked"] == ["abc"], control["completeness"]
         assert broken["completeness"]["blocked"] == [redlight.NON_IDENTIFIER], broken["completeness"]
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# 票 145 Station 3g 紅燈 —— Host evidence policy(〈四十六〉46.4、〈四十八〉48.1)
+#
+# 合約:票 145〈四十八〉48.1(Jeff 對 S3g-0 規劃檔 P8 的裁決)。規劃:docs/audits/2026-10-03-m1a-station3g-redlight-plan.md P3、P6。
+# 下文 `<BASELINE>` = 560f618560ddac1a34e0e835b99a1e3a5cc7eda5(S3G0;產品碼與 S6-1 faf7cb4 相同)。
+#
+# 介面(本刀定稿;語意依規劃檔 P3):
+#   - canonical path `.agents/evidence-policy.json`(框架常數,不可由 policy 指定);
+#   - schema `"monkeyleash.evidence-policy"` version 1;欄位全部必填、不得有多餘鍵:
+#     `config_file` / `committed_overrides` / `python_versions` / `pytest_versions` / `dists`;
+#   - producer 在 session 的 `completeness["evidence_policy"]` 記 `{"path", "head", "worktree", "schema", "version", "policy"}`,
+#     內容由 HEAD committed blob 解析;worktree 只做 identity 比對;
+#   - 框架推導函式 `redlight.addopts_overrides(addopts)`:已提交 addopts → override 清單(pytest 9.1.1 的對應)。
+#
+# driver 原則(沿用 3c-1b / 3d / 3e / 3f):
+#   - 每次模擬執行載入全新 conftest(`_isolated_conftest`);tmp root 是**真的** git repo,policy 檔**真的**提交 / 修改;
+#   - **版本事實一律固定**(〈四十八〉48.1 第 5 點):conftest 所見的 `sys.version_info` 為 3.11、`pytest.__version__` 為 9.1.1,
+#     除非該案例本身就在測版本 —— 本段的正控不依賴執行它的直譯器;
+#   - 需要兩種 repo 狀態的案例,對照組與破壞組各用 `tmp_path` 底下一個子目錄當 root;
+#   - 單點測試在同一支測試內放對照組。
+# 本段 helper 全部新寫;既有 helper(`_isolated_conftest` / `_d_plugins` / `_d_drive` / `_D_FULL` / `_e_option` /
+# `_e_sys` / `_EVersion` 等)只呼叫、不修改。
+# ─────────────────────────────────────────────────────────────────────────────
+
+_G_POLICY_FILE = ".agents/evidence-policy.json"
+_G_SCHEMA = "monkeyleash.evidence-policy"
+_G_FIXED_ADDOPTS = "-ra --strict-markers"
+
+
+def _g_policy(**overrides):
+    """與 agent-gates 現行常數一致、且在能力邊界之內的 policy(dict)。"""
+    policy = {
+        "schema": _G_SCHEMA,
+        "version": 1,
+        "config_file": "pyproject.toml",
+        "committed_overrides": ["strict_markers=true"],
+        "python_versions": ["3.11"],
+        "pytest_versions": ["9.1.1"],
+        "dists": [["anyio", "4.15.0"]],
+    }
+    policy.update(overrides)
+    return policy
+
+
+def _g_policy_text(policy):
+    return json.dumps(policy, ensure_ascii=False, indent=2) + "\n"
+
+
+def _g_write(root, rel, text):
+    p = pathlib.Path(str(root)) / rel
+    p.parent.mkdir(parents=True, exist_ok=True)
+    with io.open(str(p), "w", encoding="utf-8", newline="\n") as f:
+        f.write(text)
+
+
+def _g_root(root, policy_text=None, commit_policy=True, addopts=_G_FIXED_ADDOPTS,
+            policy_path=_G_POLICY_FILE, extra_files=None):
+    """在 `root` 建真的 git repo:提交 `pyproject.toml`(addopts 由參數決定)、root conftest(真檔內容)、
+    `extra_files`;`policy_text` 不為 None ⇒ 寫到 `policy_path`,`commit_policy` 為真才一起提交。"""
+    root = pathlib.Path(str(root))
+    root.mkdir(parents=True, exist_ok=True)
+    pyproject = u'[tool.pytest.ini_options]\ntestpaths = ["tests"]\n'
+    if addopts is not None:
+        pyproject += u'addopts = "%s"\n' % addopts
+    _g_write(root, "pyproject.toml", pyproject)
+    conftest = root / "tests" / "conftest.py"
+    conftest.parent.mkdir(parents=True, exist_ok=True)
+    conftest.write_bytes((ROOT / "tests" / "conftest.py").read_bytes())
+    tracked = ["pyproject.toml", "tests/conftest.py"]
+    for rel, text in (extra_files or {}).items():
+        _g_write(root, rel, text)
+        tracked.append(rel)
+    if policy_text is not None:
+        _g_write(root, policy_path, policy_text)
+        if commit_policy:
+            tracked.append(policy_path)
+    _d_git(root, "init", "-q")
+    _d_git(root, "config", "user.email", "t@example.invalid")
+    _d_git(root, "config", "user.name", "t")
+    _d_git(root, "add", *tracked)
+    _d_git(root, "commit", "-q", "-m", "baseline")
+    return root
+
+
+def _g_default_root(root):
+    """提交了合法、與執行環境一致的 policy 的 repo(正控用)。"""
+    return _g_root(root, policy_text=_g_policy_text(_g_policy()))
+
+
+def _g_run(root, monkeypatch, option=None, python=(3, 11), pytest_version="9.1.1",
+           anyio_version="4.15.0", inipath="pyproject.toml", ini=None):
+    """一次模擬執行(全新 conftest;`_D_FULL` 全收集、全 passed、exit 0;其他事實同固定全套)。
+    版本事實固定為參數值(預設 3.11 / 9.1.1 / anyio 4.15.0)。回傳**最後一筆** session。"""
+    root = pathlib.Path(str(root))
+    selected = [n for ids in _D_FULL.values() for n in ids]
+    c = _isolated_conftest(monkeypatch, root)
+    monkeypatch.setattr(c, "sys", _e_sys(optimize=0, version_info=_EVersion(python[0], python[1], 0, "final", 0)),
+                        raising=False)
+    monkeypatch.setattr(pytest, "__version__", pytest_version)
+    pm = _d_plugins(c, root, anyio_version=anyio_version)
+    _d_drive(c, root, _D_FULL, selected, dict((n, "passed") for n in selected),
+             option=option if option is not None else _e_option(usepdb=False), pm=pm,
+             inipath=inipath, ini=ini)
+    runs = redlight.load_runs(str(root))
+    assert runs, runs
+    return runs[-1]
+
+
+def _g_coverage(root, monkeypatch, **kw):
+    return redlight.file_coverage(_g_run(root, monkeypatch, **kw), "tests/test_x.py")
+
+
+def _g_control(tmp_path, monkeypatch):
+    """對照組:`tmp_path/control` 是提交了合法 policy 的 repo,固定全套 ⇒ 應為 `"true"`。"""
+    return _g_coverage(_g_default_root(tmp_path / "control"), monkeypatch)
+
+
+def _g_without(policy, key):
+    out = dict(policy)
+    out.pop(key)
+    return out
+
+
+# 規劃檔 P6 #2–#5:policy 自身的 HEAD / worktree integrity 不成立的四種狀態。
+_G_UNCOMMITTED_STATES = ["worktree-only", "worktree-differs", "staged-only", "deleted-in-worktree"]
+
+# 規劃檔 P6 #6–#10:HEAD 與 worktree 一致,但文件本身看不懂。
+_G_UNKNOWN_DOCUMENTS = [
+    pytest.param(u"{not json\n", id="malformed-json"),
+    pytest.param(_g_policy_text(_g_policy(schema="other.evidence-policy")), id="unknown-schema"),
+    pytest.param(_g_policy_text(_g_policy(version=2)), id="unknown-version"),
+    pytest.param(_g_policy_text(_g_policy(location=".agents/elsewhere.json")), id="unknown-key"),
+    pytest.param(_g_policy_text(_g_without(_g_policy(), "dists")), id="missing-field"),
+]
+
+
+class TestEvidencePolicyBootstrap:
+
+    def test_g3_a_repo_without_a_policy_is_not_full_coverage(self, tmp_path, monkeypatch):
+        """#1(〈四十六〉46.4 第 3 點:缺少 host policy 不得解讀成可信;規劃檔 P3 I-3 第 2 步)。分類:behavior-red。
+
+        對照組:提交了合法 policy 的 repo ⇒ `"true"`。破壞組:同樣的已提交設定與 conftest,但 repo 從未有 policy
+        (淨室安裝後、尚未初始化的狀態)⇒ 不得為 `"true"`。
+        BASELINE 上失敗的原因:`<BASELINE>:.claude/hooks/redlight.py:786-833` 不讀任何 policy ⇒ `:833` 回 `"true"`。
+        """
+        control = _g_control(tmp_path, monkeypatch)
+        broken = _g_coverage(_g_root(tmp_path / "broken"), monkeypatch)
+        assert control == "true", control
+        assert broken != "true", broken
+
+    @pytest.mark.parametrize("state", _G_UNCOMMITTED_STATES)
+    def test_g3_an_uncommitted_policy_state_is_not_full_coverage(self, tmp_path, monkeypatch, state):
+        """#2–#5(〈四十六〉46.4 第 4 點 負二 / 負三、第 6 點;規劃檔 P3 I-3 第 2、4 步)。分類:behavior-red。
+
+        對照組:提交了合法 policy 的 repo ⇒ `"true"`。破壞組(policy 內容皆為同一份合法 policy):
+          - `[worktree-only]`:policy 只在工作樹,HEAD 從未有它(負三)⇒ 不得為 `"true"`;
+          - `[worktree-differs]`:HEAD 有 policy,工作樹內容不同(本地改了未 commit)(負二)⇒ 不得為 `"true"`;
+          - `[staged-only]`:policy 已 `git add` 但未 commit ⇒ 不得為 `"true"`;
+          - `[deleted-in-worktree]`:HEAD 有 policy,工作樹把它刪了 ⇒ 不得為 `"true"`。
+        BASELINE 上失敗的原因:同 #1(`<BASELINE>:.claude/hooks/redlight.py:833`)。
+        """
+        control = _g_control(tmp_path, monkeypatch)
+        text = _g_policy_text(_g_policy())
+        broken_root = tmp_path / "broken"
+        if state == "worktree-only":
+            _g_root(broken_root, policy_text=text, commit_policy=False)
+        elif state == "staged-only":
+            _g_root(broken_root, policy_text=text, commit_policy=False)
+            _d_git(broken_root, "add", _G_POLICY_FILE)
+        else:
+            _g_root(broken_root, policy_text=text)
+            policy = broken_root / _G_POLICY_FILE
+            if state == "worktree-differs":
+                _g_write(broken_root, _G_POLICY_FILE, text + u"\n")
+            else:
+                policy.unlink()
+        broken = _g_coverage(broken_root, monkeypatch)
+        assert control == "true", control
+        assert broken != "true", broken
+
+    @pytest.mark.parametrize("text", _G_UNKNOWN_DOCUMENTS)
+    def test_g3_an_unknown_policy_document_is_not_full_coverage(self, tmp_path, monkeypatch, text):
+        """#6–#10(〈四十六〉46.4 第 6 點:schema / version 未知 ⇒ 只能 unknown;規劃檔 P3 I-1、I-2、I-3 第 5 步)。
+        分類:behavior-red。
+
+        對照組:提交了合法 policy 的 repo ⇒ `"true"`。破壞組:policy 已提交且工作樹 = HEAD,但內容為
+        `[malformed-json]` 不是 JSON、`[unknown-schema]` schema 不是 `monkeyleash.evidence-policy`、
+        `[unknown-version]` version 2、`[unknown-key]` 多一個自我指定位置的鍵 `location`(I-1)、
+        `[missing-field]` 缺 `dists` ⇒ 不得為 `"true"`。
+        BASELINE 上失敗的原因:同 #1(`<BASELINE>:.claude/hooks/redlight.py:833`)。
+        """
+        control = _g_control(tmp_path, monkeypatch)
+        broken = _g_coverage(_g_root(tmp_path / "broken", policy_text=text), monkeypatch)
+        assert control == "true", control
+        assert broken != "true", broken
+
+    def test_g3_a_policy_outside_the_canonical_path_is_not_full_coverage(self, tmp_path, monkeypatch):
+        """#11(〈四十六〉46.4 第 6 點:canonical location 屬框架不變式;規劃檔 P3 I-1)。分類:behavior-red。
+
+        對照組:policy 提交在 `.agents/evidence-policy.json` ⇒ `"true"`。破壞組:同一份合法 policy 只提交在
+        repo 根的 `evidence-policy.json`(canonical path 沒有檔)⇒ 不得為 `"true"`。
+        BASELINE 上失敗的原因:同 #1(`<BASELINE>:.claude/hooks/redlight.py:833`)。
+        """
+        control = _g_control(tmp_path, monkeypatch)
+        broken = _g_coverage(_g_root(tmp_path / "broken", policy_text=_g_policy_text(_g_policy()),
+                                     policy_path="evidence-policy.json"), monkeypatch)
+        assert control == "true", control
+        assert broken != "true", broken
+
+    def test_g3_the_producer_records_the_policy_identity(self, tmp_path, monkeypatch):
+        """#12(〈四十八〉48.1 第 2 點:producer 依 I-3 從 HEAD committed blob 解析並記入 session)。分類:behavior-red。
+
+        對照組:repo 沒有 policy ⇒ `evidence_policy` 沒有 HEAD blob(整欄 None 或 `head` 為 None)。
+        破壞組(主斷言):提交了合法 policy ⇒ 持久化的 `completeness["evidence_policy"]` 為
+        `{"path": ".agents/evidence-policy.json", "head": <HEAD blob>, "worktree": <同一個 blob>,
+        "schema": "monkeyleash.evidence-policy", "version": 1, "policy": <解析後內容>}`;
+        `<HEAD blob>` 由測試自己以 `git rev-parse HEAD:<path>` 取得。
+        BASELINE 上失敗的原因:`<BASELINE>:tests/conftest.py:368-387` 的 completeness 沒有 `evidence_policy` 欄。
+        """
+        none_run = _g_run(_g_root(tmp_path / "none"), monkeypatch)
+        none_ep = (none_run.get("completeness") or {}).get("evidence_policy")
+        root = _g_default_root(tmp_path / "with")
+        head = _d_git(root, "rev-parse", "HEAD:" + _G_POLICY_FILE).stdout.decode("ascii").strip()
+        run = _g_run(root, monkeypatch)
+        ep = (run.get("completeness") or {}).get("evidence_policy")
+        assert isinstance(ep, dict), run.get("completeness")
+        assert ep.get("path") == _G_POLICY_FILE, ep
+        assert ep.get("head") == head and ep.get("worktree") == head, (ep, head)
+        assert ep.get("schema") == _G_SCHEMA and ep.get("version") == 1, ep
+        assert ep.get("policy") == _g_policy(), ep
+        assert none_ep is None or none_ep.get("head") is None, none_ep
+
+    def test_g3_policy_content_is_not_read_from_the_worktree(self, tmp_path, monkeypatch):
+        """#13(〈四十六〉46.4 第 6 點:worktree 只做 identity check,不作為 authority 內容來源;規劃檔 P3 I-3 第 5 步)。
+        分類:regression-lock。
+
+        提交了合法 policy;模擬執行期間,Python 層的 `open` / `io.open` 只要開 canonical path 就拋例外
+        (`git hash-object` / `git cat-file` 由子行程自己讀,不受影響)⇒ 仍須為 `"true"`。
+        前置控制:guard 確實擋得住對 canonical path 的 open。
+        BASELINE 上通過:根本不讀 policy。上線後鎖住「內容只從 HEAD blob 來」。
+        """
+        import builtins
+        root = _g_default_root(tmp_path / "root")
+        policy_path = str(root / _G_POLICY_FILE)
+        real_open = builtins.open
+
+        def guarded(file, *args, **kwargs):
+            if str(file).replace("\\", "/").endswith(_G_POLICY_FILE):
+                raise OSError("worktree policy must not be read as authority content: %s" % file)
+            return real_open(file, *args, **kwargs)
+
+        with monkeypatch.context() as m:
+            m.setattr(builtins, "open", guarded)
+            m.setattr(io, "open", guarded)
+            with pytest.raises(OSError):
+                io.open(policy_path, encoding="utf-8")
+            got = _g_coverage(root, monkeypatch)
+        assert got == "true", got
+
+    def test_g3_a_matching_committed_policy_is_full_coverage(self, tmp_path, monkeypatch):
+        """#14(〈四十六〉46.4 第 3 點:宿主已提交 policy 且實際環境 == policy ⇒ 才可能 true;正二的單元版)。
+        分類:regression-lock。
+
+        提交了合法 policy(值 = 現行常數)、工作樹 = HEAD、版本事實 3.11 / 9.1.1 / anyio 4.15.0、
+        `override_ini == ["strict_markers=true"]`、全收集、全 passed ⇒ `"true"`。
+        """
+        got = _g_coverage(_g_default_root(tmp_path / "root"), monkeypatch)
+        assert got == "true", got
+
+
+# 規劃檔 P6 #15–#18:(policy 的覆寫, 執行事實, 額外提交的檔)
+_G_WIDENING = [
+    pytest.param({"python_versions": ["3.11", "3.12"]}, {"python": (3, 12)}, None, id="python"),
+    pytest.param({"pytest_versions": ["9.1.1", "9.2.0"]}, {"pytest_version": "9.2.0"}, None, id="pytest"),
+    pytest.param({"dists": [["anyio", "4.15.0"], ["anyio", "9.9.9"]]}, {"anyio_version": "9.9.9"}, None, id="dist"),
+    pytest.param({"config_file": "pytest.ini"}, {"inipath": "pytest.ini"},
+                 {"pytest.ini": u"[pytest]\ntestpaths = tests\naddopts = -ra --strict-markers\n"}, id="config-file"),
+]
+
+
+class TestEvidencePolicyBoundary:
+
+    @pytest.mark.parametrize("policy_overrides, run_kw, extra_files", _G_WIDENING)
+    def test_g3_a_policy_cannot_widen_the_capability_boundary(self, tmp_path, monkeypatch,
+                                                              policy_overrides, run_kw, extra_files):
+        """#15–#18(〈四十六〉46.4 第 3 點:host policy 只能收窄,不能擴張;〈四十八〉48.1 第 3 點)。分類:regression-lock。
+
+        對照組:合法 policy、環境在邊界內 ⇒ `"true"`。破壞組:policy 列出能力邊界外的值,且執行環境正是那個值 ——
+        `[python]` 3.12、`[pytest]` 9.2.0、`[dist]` anyio 9.9.9、`[config-file]` `pytest.ini`(另提交該檔)⇒ 不得為 `"true"`。
+        BASELINE 上通過:框架常數已擋下這四種環境(`<BASELINE>:.claude/hooks/redlight.py:793-794, 799-800, 808-809, 613`)。
+        上線後鎖住「policy 不能把它們加回來」。
+        """
+        control = _g_control(tmp_path, monkeypatch)
+        broken_root = _g_root(tmp_path / "broken", policy_text=_g_policy_text(_g_policy(**policy_overrides)),
+                              extra_files=extra_files)
+        broken = _g_coverage(broken_root, monkeypatch, **run_kw)
+        assert control == "true", control
+        assert broken != "true", broken
+
+    @pytest.mark.parametrize("case", ["override", "narrowed-dist"])
+    def test_g3_a_policy_environment_mismatch_is_not_full_coverage(self, tmp_path, monkeypatch, case):
+        """#19–#20(〈四十六〉46.4 第 4 點 負一:policy / environment mismatch ⇒ unknown)。分類:behavior-red。
+
+        對照組:合法 policy、固定全套 ⇒ `"true"`。破壞組:
+          - `[override]`:已提交 addopts 為 `-ra`、policy `committed_overrides: []`(兩者自洽);
+            執行時經 `PYTEST_ADDOPTS` 帶入 `--strict-markers` ⇒ `override_ini == ["strict_markers=true"]`(policy 未列)⇒ 不得為 `"true"`;
+          - `[narrowed-dist]`:policy `dists: []`(宿主不接受 anyio);執行時 anyio 4.15.0 已載入 ⇒ 不得為 `"true"`。
+        BASELINE 上失敗的原因:`<BASELINE>:.claude/hooks/redlight.py:795` 的比較對象是框架常數 `["strict_markers=true"]`、
+        `:613` 的 `KNOWN_DISTS` 含 anyio 4.15.0 ⇒ `:833` 回 `"true"`。
+        """
+        control = _g_control(tmp_path, monkeypatch)
+        if case == "override":
+            broken_root = _g_root(tmp_path / "broken", addopts="-ra",
+                                  policy_text=_g_policy_text(_g_policy(committed_overrides=[])))
+        else:
+            broken_root = _g_root(tmp_path / "broken", policy_text=_g_policy_text(_g_policy(dists=[])))
+        broken = _g_coverage(broken_root, monkeypatch)
+        assert control == "true", control
+        assert broken != "true", broken
+
+
+# 規劃檔 P6 #21–#25:已提交 addopts → override 清單(pytest 9.1.1:`_pytest/main.py:76-96` 的 OverrideIniAction 旗標、
+# `_pytest/helpconfig.py:113-116` 的 `-o` / `--override-ini`;其他旗標不產生 override)
+_G_DERIVATIONS = [
+    pytest.param("-ra --strict-markers", ["strict_markers=true"], id="strict-markers"),
+    pytest.param("--strict-config -q", ["strict_config=true"], id="strict-config"),
+    pytest.param("-o python_files=check_*.py -oxfail_strict=true", ["python_files=check_*.py", "xfail_strict=true"],
+                 id="o-flag"),
+    pytest.param("--override-ini=cache_dir=.c --strict-markers", ["cache_dir=.c", "strict_markers=true"],
+                 id="override-ini-eq"),
+    pytest.param("", [], id="no-addopts"),
+]
+
+
+class TestAddoptsDerivation:
+
+    @pytest.mark.parametrize("addopts, expected", _G_DERIVATIONS)
+    def test_g3_overrides_are_derived_from_committed_addopts(self, addopts, expected):
+        """#21–#25(〈四十八〉48.1 第 4 點:框架推導規則以 fixture 測)。分類:behavior-red。
+
+        `redlight.addopts_overrides(addopts)` 依出現順序回傳 override 清單,必須恰等於預期。
+        這裡驗的是**推導規則**(框架性質),不是「常數 ↔ 宿主設定」—— 後者在 tests/test_host_evidence_policy.py。
+        BASELINE 上失敗的原因:`<BASELINE>:.claude/hooks/redlight.py` 沒有 `addopts_overrides`(只有常數 `:493`)。
+        """
+        derive = getattr(redlight, "addopts_overrides")
+        assert derive(addopts) == expected, (addopts, derive(addopts))
+
+    def test_g3_a_policy_disagreeing_with_the_committed_addopts_is_not_full_coverage(self, tmp_path, monkeypatch):
+        """#26(〈四十八〉48.1 第 4 點:verdict 時機器鎖步 —— policy 必須與 HEAD 設定檔的 addopts 推導一致)。
+        分類:behavior-red。
+
+        對照組:已提交 addopts `-ra --strict-markers`、policy `["strict_markers=true"]` ⇒ `"true"`。
+        破壞組:只改已提交 addopts 為 `-ra`(policy 與執行時 override 都仍是 `["strict_markers=true"]`,
+        後者經 `PYTEST_ADDOPTS` 帶入)⇒ policy 與已提交設定不一致 ⇒ 不得為 `"true"`。
+        BASELINE 上失敗的原因:`<BASELINE>:.claude/hooks/redlight.py:795` 只比框架常數,不讀已提交 addopts ⇒ `:833` 回 `"true"`。
+        """
+        control = _g_control(tmp_path, monkeypatch)
+        broken = _g_coverage(_g_root(tmp_path / "broken", addopts="-ra",
+                                     policy_text=_g_policy_text(_g_policy())), monkeypatch)
+        assert control == "true", control
+        assert broken != "true", broken
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# 票 145 Station 4g 補紅燈 —— 「沒有任何 override」的正控與「override 事實取不到」的鎖
+#
+# 成因:pytest 9.1.1 的 `-o` 是 `action="append"`、沒有 default(`_pytest/helpconfig.py:112-119`),
+# 沒給任何 `-o` / OverrideIniAction 旗標時 `config.option.override_ini` 為 **None**(屬性存在)。
+# 3g / 3g-1b 的正控都帶 `--strict-markers`,沒有一支走到這條路徑;S4G1 的淨室「正二」因此不成立
+# (`.dev/reports/2026-10-04T213043Z-ticket145-station4g-s4g1-local-pass-cleanroom-pos2-fail.md`)。
+# 裁決:修法 B(producer 先判欄位是否存在、再解讀值);A(consumer 把 None 當 [])否決。
+# 既有 helper(`_g_root` / `_g_policy` / `_g_policy_text` / `_g_coverage` / `_e_option` / `_d_option`)只呼叫、不修改。
+# ─────────────────────────────────────────────────────────────────────────────
+
+class TestEvidencePolicyNoOverride:
+
+    def test_g3_no_override_anywhere_is_full_coverage(self, tmp_path, monkeypatch):
+        """T1。分類:behavior-red(在 S4G1 上必須失敗)。
+
+        已提交 addopts `-ra`(推導出的 override 為 `[]`)、policy `committed_overrides: []`(兩者自洽)、
+        執行時沒有任何 `-o`:pytest 明確表示「沒有 override」,`option.override_ini is None`(屬性存在)
+        ⇒ 必須能取得 full coverage(`"true"`)。否則設定裡沒有 `-o` 類旗標的宿主永遠退不了紅。
+        S4G1 上失敗的原因:`tests/conftest.py` 的 producer 把 None 原樣交給 `normalize_overrides`,
+        落帳 `override_ini: null`;`.claude/hooks/redlight.py` 的 (viii) 比 `None != []` ⇒ unknown。
+        """
+        root = _g_root(tmp_path / "root", policy_text=_g_policy_text(_g_policy(committed_overrides=[])),
+                       addopts="-ra")
+        got = _g_coverage(root, monkeypatch, option=_e_option(usepdb=False, override_ini=None))
+        assert got == "true", got
+
+    def test_g3_a_missing_override_fact_is_not_full_coverage(self, tmp_path, monkeypatch):
+        """T2。分類:regression-lock(在 S4G1 上必須通過)。
+
+        與 T1 同一種佈置,但 `config.option` 根本沒有 `override_ini` 屬性 ⇒ 事實取不到 ⇒ 不得為 `"true"`。
+        **事實取不到 ≠ 沒有 override**:鎖住修法 B 的語意,防止日後改成在 consumer 把 None 當 `[]`
+        (修法 A;那會把「取不到」當成「確定沒有」⇒ fail-open)。
+        """
+        root = _g_root(tmp_path / "root", policy_text=_g_policy_text(_g_policy(committed_overrides=[])),
+                       addopts="-ra")
+        option = _d_option(missing=("override_ini",), runxfail=False, pythonwarnings=None, trace=False,
+                           usepdb=False)
+        got = _g_coverage(root, monkeypatch, option=option)
+        assert got != "true", got
diff --git a/tests/test_status.py b/tests/test_status.py
index 05e0c67..6a5ab2b 100644
--- a/tests/test_status.py
+++ b/tests/test_status.py
@@ -594,7 +594,8 @@ class TestTestsUnderTicketUsesTheLatestRecordPerFile:
                               u"dists": [[u"anyio", u"4.15.0"]]}],
                 u"blocked": [], u"override_ini": list(_T_FIXED_OVERRIDES), u"inifilename": None,
                 u"inipath": u"pyproject.toml", u"config_blobs": blobs, u"pytest_version": u"9.1.1",
-                u"optimize": 0, u"python_version": u"3.11"})
+                u"optimize": 0, u"python_version": u"3.11",
+                u"evidence_policy": _t_policy_facts(root)})
 
         out = render(root)
         red = _value_of(out, u"tests red under ticket 99")
@@ -1370,7 +1371,8 @@ class TestOrphans:
                                     u"blocked": [], u"override_ini": list(_T_FIXED_OVERRIDES),
                                     u"inifilename": None, u"inipath": u"pyproject.toml",
                                     u"config_blobs": blobs, u"pytest_version": u"9.1.1",
-                                    u"optimize": 0, u"python_version": u"3.11"})
+                                    u"optimize": 0, u"python_version": u"3.11",
+                                    u"evidence_policy": _t_policy_facts(root)})
         out = render(root)
         orphaned = _value_of(out, u"tests orphaned under ticket 99")
         green = _value_of(out, u"tests green under ticket 99")
@@ -1495,6 +1497,14 @@ class _ChainSession:
         self.config = _ChainConfig(args, root)
 
 
+# 票 145 Station 4g 授權 G3(〈四十八〉48.1 第 5 點;規劃檔 S3g-0 P2-B):driver 把 conftest 所見的版本事實
+# 固定在能力邊界內,正控不再依賴執行它的直譯器 / pytest 版本。模組載入當下的真實版本記在這裡 ——
+# 測試在呼叫 driver **之前**自己設過 `pytest.__version__` 時不覆蓋它(與 tests/test_redlight.py 同式)。
+_REAL_PYTEST_VERSION = pytest.__version__
+_PINNED_PYTEST_VERSION = u"9.1.1"
+_PINNED_PYTHON = (3, 11, 0, u"final", 0)
+
+
 def _chain_conftest(root, monkeypatch):
     """載入 tests/conftest.py,並把它與本檔那一份 redlight 的所有寫入都導到 `root`。"""
     import importlib.util
@@ -1509,6 +1519,10 @@ def _chain_conftest(root, monkeypatch):
                         str(pathlib.Path(root) / ".dev" / "pipeline.json"))
     monkeypatch.setattr(c, "_redlight", redlight)
     monkeypatch.setattr(c, "_ROOT", pathlib.Path(root))
+    monkeypatch.setattr(c, "sys", _e_sys(optimize=sys.flags.optimize,
+                                         version_info=_EVersion(*_PINNED_PYTHON)), raising=False)
+    if pytest.__version__ == _REAL_PYTEST_VERSION:
+        monkeypatch.setattr(pytest, "__version__", _PINNED_PYTEST_VERSION)
     return c
 
 
@@ -2362,6 +2376,20 @@ _T_BASELINE_INI = {
 
 _T_FIXED_OVERRIDES = [u"strict_markers=true"]
 
+# 票 145 Station 4g 授權 G1(規劃檔 S3g-0 P6「需要的授權」1):與 baseline 相符的已提交 evidence policy ——
+# 已提交 addopts `-ra --strict-markers` ⇒ `strict_markers=true`;版本與 dist 等於 driver 固定的事實(授權 3)。
+_T_POLICY_FILE = u".agents/evidence-policy.json"
+_T_BASELINE_POLICY = {
+    u"schema": u"monkeyleash.evidence-policy",
+    u"version": 1,
+    u"config_file": u"pyproject.toml",
+    u"committed_overrides": list(_T_FIXED_OVERRIDES),
+    u"python_versions": [u"3.11"],
+    u"pytest_versions": [u"9.1.1"],
+    u"dists": [[u"anyio", u"4.15.0"]],
+}
+_T_BASELINE_ADDOPTS = u"-ra --strict-markers"
+
 
 def _t_git(root, *args):
     return subprocess.run(["git"] + list(args), cwd=str(root), capture_output=True, check=True)
@@ -2374,14 +2402,28 @@ def _t_committed(root):
     conftest = pathlib.Path(root) / "tests" / "conftest.py"
     conftest.parent.mkdir(parents=True, exist_ok=True)
     conftest.write_bytes((ROOT / "tests" / "conftest.py").read_bytes())
+    policy = pathlib.Path(root) / ".agents" / "evidence-policy.json"
+    policy.parent.mkdir(parents=True, exist_ok=True)
+    with io.open(str(policy), "w", encoding="utf-8", newline="\n") as f:
+        f.write(json.dumps(_T_BASELINE_POLICY, ensure_ascii=False, indent=2) + u"\n")
     _t_git(root, "init", "-q")
     _t_git(root, "config", "user.email", "t@example.invalid")
     _t_git(root, "config", "user.name", "t")
-    _t_git(root, "add", "pyproject.toml", "tests/conftest.py")
+    _t_git(root, "add", "pyproject.toml", "tests/conftest.py", _T_POLICY_FILE)
     _t_git(root, "commit", "-q", "-m", "baseline")
     return root
 
 
+def _t_policy_facts(root):
+    """`_t_committed(root)` 之後的 `completeness["evidence_policy"]` 事實(7 鍵;授權 G2 用):
+    blob 由 git 實際取得,內容 = 已提交的 baseline policy,`committed_addopts` = 已提交的 addopts 原值。"""
+    head = _t_git(root, "rev-parse", "HEAD:" + _T_POLICY_FILE).stdout.decode().strip()
+    worktree = _t_git(root, "hash-object", _T_POLICY_FILE).stdout.decode().strip()
+    return {u"path": _T_POLICY_FILE, u"head": head, u"worktree": worktree,
+            u"schema": _T_BASELINE_POLICY[u"schema"], u"version": _T_BASELINE_POLICY[u"version"],
+            u"policy": dict(_T_BASELINE_POLICY), u"committed_addopts": _T_BASELINE_ADDOPTS}
+
+
 class _TDist:
     def __init__(self, name, version):
         self.project_name = name
@@ -2856,3 +2898,279 @@ class TestDebuggerModeLocks:
         got = _lines_of(root)
         assert u"tests/test_x.py" in got[u"green"], got
         assert u"tests/test_x.py" not in got[u"red"], got
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 票 145 Station 3g 紅燈 —— Host evidence policy 的串接(producer → 持久化 run 事實 → status)
+#
+# 合約:票 145〈四十八〉48.1。規劃:docs/audits/2026-10-03-m1a-station3g-redlight-plan.md P3、P6。
+# 下文 `<BASELINE>` = 560f618560ddac1a34e0e835b99a1e3a5cc7eda5(S3G0)。
+#
+# 每一次模擬執行都經**真實 tests/conftest.py**(`_chain_conftest` 每次載入全新模組)寫入 tmp root 的帳本,
+# 再由 status 讀回判定;tmp root 是真的 git repo,policy 檔**真的**提交 / 修改(canonical path
+# `.agents/evidence-policy.json`;schema 與欄位同 tests/test_redlight.py 的 3g 段)。
+# **版本事實一律固定**(〈四十八〉48.1 第 5 點):conftest 所見的 `sys.version_info` 為 3.11、`pytest.__version__` 為 9.1.1。
+# 本段 helper 全部新寫;既有 helper(`_root_with_redlight` / `_chain_conftest` / `_lines_of` / `_t_option` /
+# `_t_drive` / `_e_option` / `_e_sys` / `_EVersion`)只呼叫、不修改。
+# ═══════════════════════════════════════════════════════════════════════════
+
+_G_POLICY_FILE = u".agents/evidence-policy.json"
+
+
+def _g_policy(**overrides):
+    policy = {
+        u"schema": u"monkeyleash.evidence-policy",
+        u"version": 1,
+        u"config_file": u"pyproject.toml",
+        u"committed_overrides": [u"strict_markers=true"],
+        u"python_versions": [u"3.11"],
+        u"pytest_versions": [u"9.1.1"],
+        u"dists": [[u"anyio", u"4.15.0"]],
+    }
+    policy.update(overrides)
+    return policy
+
+
+def _g_write(root, rel, text):
+    p = pathlib.Path(str(root)) / rel
+    p.parent.mkdir(parents=True, exist_ok=True)
+    with io.open(str(p), "w", encoding="utf-8", newline="\n") as f:
+        f.write(text)
+
+
+def _g_committed(root, policy=None, commit_policy=True, addopts=u"-ra --strict-markers"):
+    """把 `root` 變成真的 git repo:提交 `pyproject.toml`(addopts 由參數決定)與 root conftest(真檔內容);
+    `policy` 不為 None ⇒ 寫到 canonical path,`commit_policy` 為真才一起提交。"""
+    _g_write(root, u"pyproject.toml",
+             u'[tool.pytest.ini_options]\ntestpaths = ["tests"]\naddopts = "%s"\n' % addopts)
+    conftest = pathlib.Path(root) / "tests" / "conftest.py"
+    conftest.parent.mkdir(parents=True, exist_ok=True)
+    conftest.write_bytes((ROOT / "tests" / "conftest.py").read_bytes())
+    tracked = [u"pyproject.toml", u"tests/conftest.py"]
+    if policy is not None:
+        _g_write(root, _G_POLICY_FILE, json.dumps(policy, ensure_ascii=False, indent=2) + u"\n")
+        if commit_policy:
+            tracked.append(_G_POLICY_FILE)
+    _t_git(root, "init", "-q")
+    _t_git(root, "config", "user.email", "t@example.invalid")
+    _t_git(root, "config", "user.name", "t")
+    _t_git(root, "add", *tracked)
+    _t_git(root, "commit", "-q", "-m", "baseline")
+    return root
+
+
+def _g_drive(root, monkeypatch, outcomes, exitstatus, option=None):
+    """一次模擬執行:全新 conftest;tests/test_x.py 的 S_A / S_B 全收集;版本事實固定為 3.11 / 9.1.1。"""
+    c = _chain_conftest(root, monkeypatch)
+    monkeypatch.setattr(c, "sys", _e_sys(optimize=0, version_info=_EVersion(3, 11, 0, "final", 0)), raising=False)
+    monkeypatch.setattr(pytest, "__version__", "9.1.1")
+    _t_drive(c, root, {u"tests/test_x.py": [S_A, S_B]}, [S_A, S_B], outcomes,
+             exitstatus=exitstatus, option=option if option is not None else _e_option(usepdb=False))
+
+
+def _g_red_then(root, monkeypatch, option=None):
+    """R1 固定全套:S_A failed、S_B passed(exit 1)⇒ S_A 為已知紅;R2:S_A、S_B 皆 passed(exit 0,`option`)。
+    回傳兩筆 run 事實(各自用全新 conftest)。"""
+    _g_drive(root, monkeypatch, {S_A: "failed", S_B: "passed"}, 1)
+    _g_drive(root, monkeypatch, {S_A: "passed", S_B: "passed"}, 0, option=option)
+    runs = redlight.load_runs(root)
+    assert len(runs) == 2, runs
+    return runs
+
+
+def _g_assert_scenario(runs):
+    """情境斷言:R1 為 B;R2 schema 合格且為 A(紅留著,是因為 coverage 不是 "true",不是因為 run 本身不合格)。"""
+    assert redlight.run_state(runs[0]) == u"B", runs[0]
+    assert redlight.validate_session(runs[1]) == [], runs[1]
+    assert redlight.run_state(runs[1]) == u"A", runs[1]
+
+
+class TestEvidencePolicyChain:
+
+    def test_g3_no_policy_does_not_retire_a_known_red(self, tmp_path, monkeypatch):
+        """#28(〈四十六〉46.4 第 3 點、第 4 點 正一的鏈條面:未初始化 ⇒ unknown ⇒ 不得退紅)。分類:behavior-red。
+
+        repo 已提交設定與 conftest,但從未有 policy。R1 固定全套:test_a failed ⇒ 已知紅。
+        R2 固定全套:全 passed ⇒ 不得退紅、不得 green。
+        BASELINE 上失敗的原因:R2 在 `<BASELINE>:.claude/hooks/redlight.py:833` 判 `"true"` ⇒
+        `<BASELINE>:.claude/portable/status.py:456-474` 退掉 test_a ⇒ green。
+        """
+        root = _root_with_redlight(tmp_path)
+        _g_committed(root)
+        runs = _g_red_then(root, monkeypatch)
+        _g_assert_scenario(runs)
+        got = _lines_of(root)
+        assert u"tests/test_x.py" in got[u"red"], got
+        assert u"tests/test_x.py" not in got[u"green"], got
+
+    @pytest.mark.parametrize("state", ["worktree-only", "worktree-differs"])
+    def test_g3_an_uncommitted_policy_does_not_retire_a_known_red(self, tmp_path, monkeypatch, state):
+        """#29–#30(〈四十六〉46.4 第 4 點 負三 / 負二 的鏈條版)。分類:behavior-red。
+
+        `[worktree-only]`:合法 policy 只在工作樹,HEAD 從未有它(負三)。
+        `[worktree-differs]`:HEAD 有合法 policy,工作樹內容不同、未 commit(負二)。
+        R1 固定全套:test_a failed ⇒ 已知紅。R2 固定全套:全 passed ⇒ 不得退紅、不得 green。
+        BASELINE 上失敗的原因:同 #28(`<BASELINE>:.claude/hooks/redlight.py:833`;`<BASELINE>:.claude/portable/status.py:456-474`)。
+        """
+        root = _root_with_redlight(tmp_path)
+        if state == "worktree-only":
+            _g_committed(root, policy=_g_policy(), commit_policy=False)
+        else:
+            _g_committed(root, policy=_g_policy())
+            _g_write(root, _G_POLICY_FILE,
+                     json.dumps(_g_policy(), ensure_ascii=False, indent=2) + u"\n\n")
+        runs = _g_red_then(root, monkeypatch)
+        _g_assert_scenario(runs)
+        got = _lines_of(root)
+        assert u"tests/test_x.py" in got[u"red"], got
+        assert u"tests/test_x.py" not in got[u"green"], got
+
+    def test_g3_a_policy_environment_mismatch_does_not_retire_a_known_red(self, tmp_path, monkeypatch):
+        """#31(〈四十六〉46.4 第 4 點 負一的鏈條版)。分類:behavior-red。
+
+        已提交 addopts `-ra`、policy `committed_overrides: []`(兩者自洽)並已提交。R1 固定全套:test_a failed ⇒ 已知紅。
+        R2:經 `PYTEST_ADDOPTS` 帶入 `--strict-markers` ⇒ `override_ini == ["strict_markers=true"]`(policy 未列),
+        全 passed ⇒ 不得退紅、不得 green。
+        BASELINE 上失敗的原因:`<BASELINE>:.claude/hooks/redlight.py:795` 的比較對象是框架常數 ⇒ `:833` 判 `"true"` ⇒
+        `<BASELINE>:.claude/portable/status.py:456-474` 退紅。
+        """
+        root = _root_with_redlight(tmp_path)
+        _g_committed(root, policy=_g_policy(committed_overrides=[]), addopts=u"-ra")
+        runs = _g_red_then(root, monkeypatch)
+        _g_assert_scenario(runs)
+        assert runs[1]["completeness"]["override_ini"] == [u"strict_markers=true"], runs[1]["completeness"]
+        got = _lines_of(root)
+        assert u"tests/test_x.py" in got[u"red"], got
+        assert u"tests/test_x.py" not in got[u"green"], got
+
+    def test_g3_a_matching_committed_policy_retires_the_red(self, tmp_path, monkeypatch):
+        """#32(〈四十六〉46.4 第 4 點 正二的鏈條版:提交合法 policy → 製造 red → 固定全套 → true → red 合法退休)。
+        分類:regression-lock。
+
+        提交合法 policy(值 = 現行常數)、工作樹 = HEAD。R1 固定全套:test_a failed ⇒ 已知紅。
+        R2 固定全套:全 passed ⇒ X 退紅、在 green。
+        """
+        root = _root_with_redlight(tmp_path)
+        _g_committed(root, policy=_g_policy())
+        runs = _g_red_then(root, monkeypatch)
+        _g_assert_scenario(runs)
+        got = _lines_of(root)
+        assert u"tests/test_x.py" in got[u"green"], got
+        assert u"tests/test_x.py" not in got[u"red"], got
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 票 145 Station 3g-1b 紅燈 —— status 的 evidence policy 狀態行(〈四十八〉48.1 第 6 點;〈五十〉50.1)
+#
+# 合約:status 輸出恰有一行以 `evidence policy: ` 開頭,值依 policy 狀態為
+# 未初始化 / 未提交 / 工作樹與 HEAD 不同 / 格式不明 / 超出框架能力邊界 / 有效,
+# 並帶 `(source: .agents/evidence-policy.json)`。沒有這一行,「未初始化 ⇒ 永遠 unknown」對下游是靜默的。
+# 下文 `<BASELINE>` = 7a15ea081da1bf23cc79e04aef76065438f65219(S3G2)。
+#
+# 每一案都在**真的** git tmp repo(`_g_committed`)上佈置 policy 狀態,再呼叫 `render(root)`。
+# 本段 helper 全部新寫;既有 helper(`_root_with_redlight` / `_g_committed` / `_g_policy` / `_g_write` /
+# `_t_git` / `_lines` / `render`)只呼叫、不修改。
+# ═══════════════════════════════════════════════════════════════════════════
+
+_G_STATUS_PREFIX = u"evidence policy: "
+_G_STATUS_SOURCE = u"(source: .agents/evidence-policy.json)"
+
+_G_STATUS_EXPECTED = {
+    u"uninitialized": u"未初始化",
+    u"uncommitted": u"未提交",
+    u"worktree-differs": u"工作樹與 HEAD 不同",
+    u"unknown-schema": u"格式不明",
+    u"outside-boundary": u"超出框架能力邊界",
+    u"valid": u"有效",
+}
+
+
+def _g_policy_json(policy):
+    return json.dumps(policy, ensure_ascii=False, indent=2) + u"\n"
+
+
+def _g_without_key(policy, key):
+    out = dict(policy)
+    out.pop(key)
+    return out
+
+
+# [unknown-schema] 依序涵蓋的已提交文件:JSON malformed、schema 名稱不認得、version 不支援、
+# 必要欄位缺失、型別錯誤(後兩者同屬「必要欄位缺失 / 型別錯誤」一類,兩種都測)。
+_G_UNKNOWN_DOCUMENTS = [
+    (u"malformed-json", u"{not json\n"),
+    (u"unknown-schema-name", _g_policy_json(_g_policy(schema=u"other.evidence-policy"))),
+    (u"unsupported-version", _g_policy_json(_g_policy(version=2))),
+    (u"missing-field", _g_policy_json(_g_without_key(_g_policy(), u"dists"))),
+    (u"wrong-type", _g_policy_json(_g_policy(python_versions=u"3.11"))),
+]
+
+
+def _g_policy_status_line(root):
+    """`render(root)` 裡以 `evidence policy: ` 開頭的行;必須恰有一行。"""
+    out = render(root)
+    hits = [ln.strip() for ln in _lines(out) if ln.strip().startswith(_G_STATUS_PREFIX)]
+    assert len(hits) == 1, (hits, out)
+    return hits[0]
+
+
+def _g_assert_status(line, expected):
+    value = line[len(_G_STATUS_PREFIX):].split(u"(source:")[0].strip()
+    assert value.startswith(expected), (expected, line)
+    assert _G_STATUS_SOURCE in line, line
+
+
+def _g_status_root(base, state):
+    """在 `base` 底下造一個帶 redlight 的 tmp repo,佈置成 `state`;回傳 root。"""
+    root = _root_with_redlight(base)
+    if state == u"uninitialized":
+        _g_committed(root)
+    elif state == u"uncommitted":
+        _g_committed(root, policy=_g_policy(), commit_policy=False)
+    elif state == u"worktree-differs":
+        _g_committed(root, policy=_g_policy())
+        _g_write(root, _G_POLICY_FILE, _g_policy_json(_g_policy()) + u"\n")
+    elif state == u"outside-boundary":
+        _g_committed(root, policy=_g_policy(python_versions=[u"3.11", u"3.12"]))
+    elif state == u"valid":
+        _g_committed(root, policy=_g_policy())
+    else:
+        raise ValueError(state)
+    return root
+
+
+def _g_committed_raw_policy(base, text):
+    """已提交設定與 conftest 的 repo,再把 `text`(原樣)提交為 canonical policy。"""
+    root = _root_with_redlight(base)
+    _g_committed(root)
+    _g_write(root, _G_POLICY_FILE, text)
+    _t_git(root, "add", _G_POLICY_FILE)
+    _t_git(root, "commit", "-q", "-m", "policy")
+    return root
+
+
+class TestEvidencePolicyStatusLine:
+
+    @pytest.mark.parametrize("state", list(_G_STATUS_EXPECTED))
+    def test_g3_status_shows_the_policy_state(self, tmp_path, state):
+        """〈五十〉50.1 第 3 點(status 的 policy 狀態行)。分類:behavior-red。
+
+        - `[uninitialized]`:repo 從未有 policy ⇒ `未初始化`;
+        - `[uncommitted]`:合法 policy 只在工作樹 ⇒ `未提交`;
+        - `[worktree-differs]`:HEAD 有合法 policy,工作樹內容不同 ⇒ `工作樹與 HEAD 不同`;
+        - `[unknown-schema]`:依序五份**已提交**文件(JSON malformed、schema 名稱不認得、version 2、
+          缺 `dists`、`python_versions` 為字串),**逐一**斷言 ⇒ 都是 `格式不明`;
+        - `[outside-boundary]`:已提交 policy 的 `python_versions` 含 3.12(框架能力邊界外)⇒ `超出框架能力邊界`;
+        - `[valid]`:已提交合法 policy、工作樹 = HEAD ⇒ `有效`。
+        每一案的那一行都須帶 `(source: .agents/evidence-policy.json)`。
+        BASELINE 上失敗的原因:`<BASELINE>:.claude/portable/status.py` 沒有 `evidence policy:` 這一行
+        (`_g_policy_status_line` 的「恰有一行」斷言)。
+        """
+        expected = _G_STATUS_EXPECTED[state]
+        if state == u"unknown-schema":
+            for name, text in _G_UNKNOWN_DOCUMENTS:
+                root = _g_committed_raw_policy(tmp_path / name, text)
+                _g_assert_status(_g_policy_status_line(root), expected)
+            return
+        root = _g_status_root(tmp_path, state)
+        _g_assert_status(_g_policy_status_line(root), expected)
diff --git a/tests/test_verify_gates.py b/tests/test_verify_gates.py
index 95b4b53..ff1a3b6 100644
--- a/tests/test_verify_gates.py
+++ b/tests/test_verify_gates.py
@@ -289,3 +289,27 @@ class TestScenarioR4LeavesTheTargetClean:
             "追蹤側沒有被還原乾淨:%r" % dirty.decode("utf-8", "replace")
         assert not os.path.exists(os.path.join(target, "docs", "adr", "verify-trigger.md")), \
             "情境寫的未追蹤檔沒有被清掉"
+
+
+# 票 145 Station 3g 紅燈 #33(〈四十六〉46.4 第 4、5 點;規劃檔 docs/audits/2026-10-03-m1a-station3g-redlight-plan.md P5)。
+# 淨室的兩正三負由 `verify_gates.EVIDENCE_SCENARIOS` 列舉,比照 `SCENARIOS` 的「規則 ↔ 情境」對照。
+# **這一條只證明情境有接線,不證明情境結果** —— 結果由 4g 本機實跑 verify_gates 照錄(〈四十八〉48.1 第 7 點)。
+_EVIDENCE_SCENARIO_KEYS = {
+    "pos1-uninitialized",       # 正一:未初始化 ⇒ 框架測試全綠、authority 為 unknown
+    "pos2-initialized",         # 正二:已提交且相符的 policy ⇒ 紅 → 固定全套 → true → 合法退休
+    "neg1-mismatch",            # 負一:policy / environment 不符 ⇒ unknown
+    "neg2-worktree-differs",    # 負二:HEAD 有 policy、worktree 不同 ⇒ unknown
+    "neg3-worktree-only",       # 負三:worktree 有 policy、HEAD 沒有 ⇒ unknown
+}
+
+
+def test_every_evidence_policy_scenario_is_wired():
+    """#33。分類:behavior-red。
+
+    `verify_gates.EVIDENCE_SCENARIOS` 必須是 dict,鍵恰為兩正三負五個情境,值皆可呼叫。
+    BASELINE(560f618)上失敗的原因:`.claude/portable/verify_gates.py` 沒有 `EVIDENCE_SCENARIOS`(只有 `SCENARIOS`,`:225-235`)。
+    """
+    table = getattr(vg, "EVIDENCE_SCENARIOS", None)
+    assert isinstance(table, dict), "verify_gates 沒有 EVIDENCE_SCENARIOS:淨室的兩正三負沒有接線"
+    assert set(table) == _EVIDENCE_SCENARIO_KEYS, sorted(table)
+    assert all(callable(f) for f in table.values()), table
```
<!-- 逐字結束 -->

### E.2 `git diff 83258dd9ab415a793eaf2b140a9e34c5b91069f2..8e7775526e462d984abb0992ed74c1e1aa3648dd -- <CODE_FILES>`(S3G1B → TARGET)

用途:審查 3g / 3g-1b 新增的 42 支測試(35 behavior-red + 7 regression-lock)在 4g 是否維持原內容;另辨識 4g 合法新增的 T1 / T2 與 G1–G5 授權改動。

<!-- 逐字開始 -->
```diff
diff --git a/.agents/evidence-policy.json b/.agents/evidence-policy.json
new file mode 100644
index 0000000..6e9aca1
--- /dev/null
+++ b/.agents/evidence-policy.json
@@ -0,0 +1,9 @@
+{
+  "schema": "monkeyleash.evidence-policy",
+  "version": 1,
+  "config_file": "pyproject.toml",
+  "committed_overrides": ["strict_markers=true"],
+  "python_versions": ["3.11"],
+  "pytest_versions": ["9.1.1"],
+  "dists": [["anyio", "4.15.0"]]
+}
diff --git a/.agents/portable-manifest.txt b/.agents/portable-manifest.txt
index cc644b7..0545c50 100644
--- a/.agents/portable-manifest.txt
+++ b/.agents/portable-manifest.txt
@@ -100,6 +100,10 @@ bootstrap.sh                    skip
 # 那就是合併,而合併是逐次判斷、覆蓋是每次都跑,一個會出錯的合併比較糟。
 # 代價:框架每新增一個檔案,各目標 repo 要人手動補一行。接受。
 .agents/portable-manifest.txt   ask
+# 票 145 Station 4g:host evidence policy(canonical path)。**skip**:它描述的是**這個 repo** 接受哪些
+# 已提交設定與執行環境,每個 repo 自己的那一份只能由人放上去並 commit(〈四十八〉48.1 第 6 點)。
+# 照抄到下游等於替下游自動信任上游的環境 —— 那正是本票要拆掉的狀態。
+.agents/evidence-policy.json    skip
 scripts/skills-update.sh        copy
 # 票 84 專用的一次性探針(寫死 wusuowei-tw/monkeyleash、寫死那組 sha、
 # 讀本 repo 的 commit-map)。**標 skip 不標 copy**:照抄到下游,它會去打
@@ -114,6 +118,10 @@ scripts/e2e_authority_layer.py  skip
 # ── 綁死這個 repo,必須重新產生 ────────────────────────────────
 .agents/legacy-no-redlight.txt  generate
 .dev/                           generate
+# 票 145 Station 4g:evidence policy 範本,由安裝器以目標 repo 的 `redlight.policy_template()` 產生
+# (框架能力邊界常數的完整列舉,不是觀察值)。放在非 canonical 路徑,永遠不是 authority。
+# 不另放範本來源檔(常數只有 redlight 那一份)。
+.agents/evidence-policy.template.json generate
 
 # ── 框架的測試(閘門自己的) ───────────────────────────────────
 tests/conftest.py               copy
diff --git a/.claude/hooks/redlight.py b/.claude/hooks/redlight.py
index 0be0050..0616c17 100644
--- a/.claude/hooks/redlight.py
+++ b/.claude/hooks/redlight.py
@@ -488,13 +488,42 @@ KNOWN_DISTS = (("anyio", "4.15.0"),)
 # (xiii) P1 的盤點只對這些 pytest 版本成立;換版後非 ini 的 CLI 選項要重新盤點。
 KNOWN_PYTEST_VERSIONS = ("9.1.1",)
 
-# (viii) 已提交 pyproject.toml 的 addopts 帶來的 override 清單(`--strict-markers` ⇒
-# `strict_markers=true`)。由 tests/test_redlight.py 的鎖步測試對照已提交的 addopts。
-COMMITTED_ADDOPTS_OVERRIDES = ("strict_markers=true",)
-
-# (x) 唯一可接受的設定檔(root 相對路徑);(xi) 工作樹內容必須等於 HEAD blob 的檔。
-CONFIG_FILE = "pyproject.toml"
-COMMITTED_FILES = (CONFIG_FILE, ROOT_CONFTEST)
+# (x) 框架盤點過的設定檔型態(root 相對路徑;P1 只盤點了 pyproject 的 `[tool.pytest.ini_options]`)。
+# 宿主用哪一個由 evidence policy 的 `config_file` 指定,必須屬於這裡。
+FRAMEWORK_CONFIG_FILES = ("pyproject.toml",)
+
+# (xi) producer 記錄工作樹 blob 與 HEAD blob 的檔:框架能盤點的設定檔 + root producer 本身。
+# consumer 只看 `ROOT_CONFTEST` 與 policy 指定的 `config_file` 兩項。
+BLOB_FILES = FRAMEWORK_CONFIG_FILES + (ROOT_CONFTEST,)
+
+# ── 票 145 Station 4g —— Host evidence policy(〈四十八〉48.1;規劃檔 S3g-0 P3)
+# 上面的 `KNOWN_*` 與 `FRAMEWORK_CONFIG_FILES` 是框架能力邊界(B);宿主在 B 之內自己選擇接受什麼(H),
+# 寫在 canonical path 的 policy 檔、並且**已提交**。原本的 `COMMITTED_ADDOPTS_OVERRIDES` / `CONFIG_FILE`
+# 是 agent-gates 自己的宿主事實被寫成了框架常數 —— 淨室 repo 因此永遠 unknown(〈四十六〉46.2)。
+#
+# I-1:位置是框架常數,policy 內容不得指定位置(多一個鍵 ⇒ 整份不合格)。
+# I-2:認得的 (schema, version) 由框架列舉;policy 不能宣告自己用哪一套解析規則。
+POLICY_FILE = ".agents/evidence-policy.json"
+POLICY_SCHEMAS = (("monkeyleash.evidence-policy", 1),)
+POLICY_FIELDS = ("schema", "version", "config_file", "committed_overrides",
+                 "python_versions", "pytest_versions", "dists")
+
+# producer 記在 `completeness["evidence_policy"]` 的 7 鍵(〈五十一〉裁決 3)。
+EVIDENCE_POLICY_KEYS = ("path", "head", "worktree", "schema", "version", "policy", "committed_addopts")
+
+# status 的 policy 狀態行(〈五十〉50.1 第 3 點);文字以裁決為準。
+POLICY_UNINITIALIZED = u"未初始化"
+POLICY_UNCOMMITTED = u"未提交"
+POLICY_WORKTREE_DIFFERS = u"工作樹與 HEAD 不同"
+POLICY_UNKNOWN_FORMAT = u"格式不明"
+POLICY_OUTSIDE_BOUNDARY = u"超出框架能力邊界"
+POLICY_VALID = u"有效"
+
+# (viii) 的推導規則(pytest 9.1.1):`OverrideIniAction` 旗標(`_pytest/main.py:76-96`;
+# 動作本體 `_pytest/config/argparsing.py:491-503`)與 `-o` / `--override-ini`(`_pytest/helpconfig.py:113-116`)。
+OVERRIDE_FLAGS = {"--strict-config": "strict_config=true",
+                  "--strict-markers": "strict_markers=true",
+                  "--strict": "strict=true"}
 
 # 「執行完成」的終態:call 的 passed / failed、任何 phase 的 skip、明確辨識的 xfail / xpass。
 # 籠統的 "other"(4c 之前的 xfail 記法)不算 —— 不得讓 other 自動取得 completeness。
@@ -683,26 +712,274 @@ def _git_lines(root, args, expected):
     return lines
 
 
-def committed_blobs(root, paths=COMMITTED_FILES):
+def _git_bytes(root, args):
+    """一條 git 的原始 stdout;失敗 ⇒ None。不拋例外。"""
+    import subprocess
+    try:
+        proc = subprocess.run(["git", "-C", os.fspath(root)] + list(args),
+                              capture_output=True, timeout=30)
+    except Exception:
+        return None
+    return proc.stdout if proc.returncode == 0 else None
+
+
+def committed_blobs(root, paths=BLOB_FILES):
     """`{path: {"worktree": blob, "head": blob}}` —— 工作樹檔案(`git hash-object`,依
     .gitattributes 正規化)與 `HEAD:<path>` 的 blob。〈二十九〉2 (xi)。
 
     git 不可用、不是 repo、檔案不存在或任何一步出錯 ⇒ 該值 None(缺欄 ⇒ 不得為 `"true"`)。
+    **逐路徑各呼叫一次 git**(票 145 Station 4g;規劃檔 P3 遷移第 3 點):一次處理全部路徑的話,
+    缺一個檔整次失敗、所有路徑都成 None —— 淨室 repo 沒有 pyproject 時,conftest 的 blob 也一起遺失。
     **不拋例外**:這是 producer 在 sessionfinish 呼叫的,不得讓 pytest 失敗。
     """
-    paths = list(paths)
-    out = dict((p, {"worktree": None, "head": None}) for p in paths)
+    out = {}
+    for p in list(paths):
+        entry = {"worktree": None, "head": None}
+        try:
+            worktree = _git_lines(root, ["hash-object", p], 1)
+            head = _git_lines(root, ["rev-parse", "HEAD:" + p], 1)
+            entry["worktree"] = worktree[0] if worktree else None
+            entry["head"] = head[0] if head else None
+        except Exception:
+            pass
+        out[p] = entry
+    return out
+
+
+def addopts_overrides(value):
+    """已提交設定的 addopts **原值** → 它帶來的 override 清單,依出現順序(pytest 9.1.1;(viii) 的推導規則)。
+
+    輸入合約(票 145〈五十一〉裁決 3):`value` 是 HEAD config 經 TOML 解析後的 raw addopts —— 只接受
+    `str`(依 shlex 切開;ini 的 type="args",`_pytest/config/__init__.py:1547`)或 `list[str]`(逐項使用);
+    沒有 addopts 時呼叫端傳 `""`。**本函式不讀 git、工作樹或任何檔案。**
+      - `OVERRIDE_FLAGS` 的旗標 → 對應的 `<ini>=true`;`-o VAL` / `-oVAL` / `--override-ini VAL` /
+        `--override-ini=VAL` → `VAL`;其他 token 不產生 override;
+      - 型別不符、引號不成對、`-o` 後面沒有值 ⇒ None,由呼叫端判 unknown —— 不猜。
+
+    推導漏掉的寫法(例:合併短旗標 `-qo x`、長旗標縮寫)會讓「推導值 ≠ 實際 override」,
+    方向是 unknown(fail-closed),不是假綠:runtime 的 `override_ini` 仍要另外等於 policy(viii)。
+    """
+    import shlex
+    if isinstance(value, str):
+        try:
+            tokens = shlex.split(value)
+        except ValueError:
+            return None
+    elif isinstance(value, list) and all(isinstance(t, str) for t in value):
+        tokens = list(value)
+    else:
+        return None
+    out = []
+    i = 0
+    while i < len(tokens):
+        tok = tokens[i]
+        if tok in OVERRIDE_FLAGS:
+            out.append(OVERRIDE_FLAGS[tok])
+        elif tok in ("-o", "--override-ini"):
+            i += 1
+            if i >= len(tokens):
+                return None
+            out.append(tokens[i])
+        elif tok.startswith("--override-ini="):
+            out.append(tok.split("=", 1)[1])
+        elif tok.startswith("-o") and not tok.startswith("--"):
+            out.append(tok[2:])
+        i += 1
+    return out
+
+
+def _committed_addopts(root, config_file):
+    """`HEAD:<config_file>` 的 `[tool.pytest.ini_options].addopts` 原值(事實擷取,不判定)。
+
+    語意(〈五十一〉裁決 3,不得混用):
+      - `str` / `list[str]` = 原值照錄;
+      - `""` = config 存在且合法、`[tool.pytest.ini_options]` 段在、只是沒有 addopts 鍵;
+      - None = 取得或解析事實失敗:blob 讀不到、不是 UTF-8 / TOML、沒有 `[tool.pytest.ini_options]` 段、
+        addopts 型別不是 str / list[str]、或直譯器沒有 `tomllib`(3.11 起的標準庫;沒有它本來就在能力邊界外)。
+    只讀 HEAD 的 blob(`git cat-file`),不讀工作樹(工作樹 ≠ HEAD 由 (xi) 另外判)。
+    """
+    try:
+        import tomllib
+    except ImportError:
+        return None
+    raw = _git_bytes(root, ["cat-file", "blob", "HEAD:" + config_file])
+    if raw is None:
+        return None
     try:
-        worktree = _git_lines(root, ["hash-object"] + paths, len(paths))
-        head = _git_lines(root, ["rev-parse"] + ["HEAD:" + p for p in paths], len(paths))
-        for i, p in enumerate(paths):
-            out[p]["worktree"] = worktree[i] if worktree else None
-            out[p]["head"] = head[i] if head else None
+        doc = tomllib.loads(raw.decode("utf-8"))
+    except Exception:
+        return None
+    tool = doc.get("tool")
+    pytest_section = tool.get("pytest") if isinstance(tool, dict) else None
+    section = pytest_section.get("ini_options") if isinstance(pytest_section, dict) else None
+    if not isinstance(section, dict):
+        return None
+    if "addopts" not in section:
+        return ""
+    value = section["addopts"]
+    if isinstance(value, str) or (isinstance(value, list) and all(isinstance(v, str) for v in value)):
+        return value
+    return None
+
+
+def evidence_policy_facts(root):
+    """producer 的 policy 事實(票 145 規劃檔 P3 I-3;〈四十八〉48.1 第 2 點)。依序:
+
+      1. 固定 canonical path `POLICY_FILE`;
+      2. `git rev-parse HEAD:<path>` —— HEAD 沒有 ⇒ 停在這裡(`head` 為 None);
+      3. 第 2 步的輸出就是 HEAD committed blob;
+      4. `git hash-object <path>`(套用 .gitattributes,與 `committed_blobs` 同一手法)取 worktree blob;
+         ≠ HEAD blob 或缺檔 ⇒ 停在這裡;
+      5. 內容**只從 HEAD blob** 取(`git cat-file blob <sha>`)並解析 JSON —— 第 4 步的工作樹檔只做
+         identity 比對,之後不再讀;記下 `schema` / `version` 與整份內容 `policy`;
+      6. policy 的 `config_file` 屬於 `FRAMEWORK_CONFIG_FILES` 時,另記它在 HEAD 的 addopts 原值
+         `committed_addopts`(`_committed_addopts`),供 consumer 做「policy ↔ 已提交設定」的機器鎖步。
+
+    回傳 7 鍵 `{"path", "head", "worktree", "schema", "version", "policy", "committed_addopts"}`
+    (〈五十一〉裁決 3);走不下去的那一步之後的欄位都是 None。
+    **只擷取事實,不判定** —— 型別、schema、邊界、鎖步都由 consumer 驗。不拋例外(sessionfinish 呼叫)。
+    """
+    out = {"path": POLICY_FILE, "head": None, "worktree": None, "schema": None,
+           "version": None, "policy": None, "committed_addopts": None}
+    try:
+        head = _git_lines(root, ["rev-parse", "HEAD:" + POLICY_FILE], 1)
+        if not head:
+            return out
+        out["head"] = head[0]
+        worktree = _git_lines(root, ["hash-object", POLICY_FILE], 1)
+        out["worktree"] = worktree[0] if worktree else None
+        if out["worktree"] != out["head"]:
+            return out
+        raw = _git_bytes(root, ["cat-file", "blob", out["head"]])
+        if raw is None:
+            return out
+        doc = json.loads(raw.decode("utf-8"))
+        if not isinstance(doc, dict):
+            return out
+        out["schema"] = doc.get("schema")
+        out["version"] = doc.get("version")
+        out["policy"] = doc
+        if doc.get("config_file") in FRAMEWORK_CONFIG_FILES:
+            out["committed_addopts"] = _committed_addopts(root, doc["config_file"])
     except Exception:
         pass
     return out
 
 
+def _is_pair_list(v):
+    return isinstance(v, list) and all(
+        isinstance(d, list) and len(d) == 2 and all(isinstance(x, str) for x in d) for d in v)
+
+
+def policy_document_problems(policy):
+    """`(格式問題, 邊界問題)` 兩個 list;都空 = 合格。consumer 與 status 共用。
+
+    - 格式(I-1、I-2):不是物件、`(schema, version)` 不在 `POLICY_SCHEMAS`、鍵集合不恰為 `POLICY_FIELDS`、
+      欄位型別不對。**schema 不認得就不往下看** —— 別的 version 的欄位語意不是本版能判讀的。
+    - 邊界(I-4;〈四十八〉48.1 第 3 點 A):任一欄位超出框架能力邊界 ⇒ 整份不合格,不取交集、不靜默忽略。
+    """
+    if not isinstance(policy, dict):
+        return [u"不是物件"], []
+    schema, version = policy.get("schema"), policy.get("version")
+    if not (isinstance(schema, str) and type(version) is int and (schema, version) in POLICY_SCHEMAS):
+        return [u"schema / version 不認得"], []
+    fmt = []
+    keys = set(policy)
+    if keys != set(POLICY_FIELDS):
+        fmt.append(u"欄位不符(多 %s;缺 %s)" % (sorted(keys - set(POLICY_FIELDS)),
+                                              sorted(set(POLICY_FIELDS) - keys)))
+    if not isinstance(policy.get("config_file"), str):
+        fmt.append(u"config_file 型別不符")
+    for key in ("committed_overrides", "python_versions", "pytest_versions"):
+        if not _is_str_list(policy.get(key)):
+            fmt.append(u"%s 型別不符" % key)
+    if not _is_pair_list(policy.get("dists")):
+        fmt.append(u"dists 型別不符")
+    if fmt:
+        return fmt, []
+    bnd = []
+    if policy["config_file"] not in FRAMEWORK_CONFIG_FILES:
+        bnd.append(u"config_file")
+    if not set(policy["python_versions"]) <= set(KNOWN_PYTHON_VERSIONS):
+        bnd.append(u"python_versions")
+    if not set(policy["pytest_versions"]) <= set(KNOWN_PYTEST_VERSIONS):
+        bnd.append(u"pytest_versions")
+    if not set(tuple(d) for d in policy["dists"]) <= set(KNOWN_DISTS):
+        bnd.append(u"dists")
+    return [], bnd
+
+
+def policy_state(root):
+    """`<root>` 現在的 policy 狀態(status 行用;〈五十〉50.1 第 3 點)。依序:
+    HEAD 沒有 ⇒ 工作樹有檔為「未提交」、否則「未初始化」;工作樹 ≠ HEAD ⇒「工作樹與 HEAD 不同」;
+    格式問題 ⇒「格式不明」;邊界問題 ⇒「超出框架能力邊界」;其餘「有效」。
+
+    「有效」只說**文件本身**可用;一次 run 能不能退紅,還要看那次的環境與鎖步(`_completeness_verdict`)。"""
+    facts = evidence_policy_facts(root)
+    if facts["head"] is None:
+        exists = os.path.exists(os.path.join(os.fspath(root), *POLICY_FILE.split("/")))
+        return POLICY_UNCOMMITTED if exists else POLICY_UNINITIALIZED
+    if facts["worktree"] != facts["head"]:
+        return POLICY_WORKTREE_DIFFERS
+    fmt, bnd = policy_document_problems(facts["policy"])
+    if fmt:
+        return POLICY_UNKNOWN_FORMAT
+    if bnd:
+        return POLICY_OUTSIDE_BOUNDARY
+    return POLICY_VALID
+
+
+def policy_template():
+    """安裝器寫到非 canonical 路徑的範本內容(〈四十八〉48.1 第 6 點 A):框架能力邊界常數的完整列舉,
+    **不是本機觀察值**。`committed_overrides` 留空 —— 它必須等於宿主自己已提交 addopts 的推導,
+    框架不替人填。"""
+    schema, version = POLICY_SCHEMAS[0]
+    return {"schema": schema, "version": version,
+            "config_file": FRAMEWORK_CONFIG_FILES[0],
+            "committed_overrides": [],
+            "python_versions": list(KNOWN_PYTHON_VERSIONS),
+            "pytest_versions": list(KNOWN_PYTEST_VERSIONS),
+            "dists": [list(d) for d in KNOWN_DISTS]}
+
+
+def _effective_policy(ep):
+    """session 記下的 `evidence_policy` → 可用的 policy(dict);任何一項不成立 ⇒ None(unknown)。
+
+    驗:型別、path 為 canonical、`head == worktree` 且非 None、文件格式與邊界(`policy_document_problems`)、
+    記錄的 schema / version 與文件一致、`committed_overrides == addopts_overrides(committed_addopts)`
+    (機器鎖步,取代原 test_d4;`committed_addopts` 為 None 或推導不了 ⇒ unknown)。
+    policy 已驗過 ⊆ 能力邊界,所以 effective = B ∩ policy = policy。"""
+    if not isinstance(ep, dict) or ep.get("path") != POLICY_FILE:
+        return None
+    head = ep.get("head")
+    if not (isinstance(head, str) and head and ep.get("worktree") == head):
+        return None
+    policy = ep.get("policy")
+    fmt, bnd = policy_document_problems(policy)
+    if fmt or bnd:
+        return None
+    if ep.get("schema") != policy["schema"] or ep.get("version") != policy["version"]:
+        return None
+    committed = ep.get("committed_addopts")
+    if committed is None:
+        return None
+    derived = addopts_overrides(committed)
+    if derived is None or derived != policy["committed_overrides"]:
+        return None
+    return policy
+
+
+def _effective(boundary, chosen):
+    """effective = B ∩ policy(I-3 第 6 步)。"""
+    return [v for v in chosen if v in boundary]
+
+
+def _known_dists_accepted(plugin, accepted):
+    """known_dist 項目的每個 (名稱, 版本) 都要在 effective 的 dists 內;沒有 `dists` 事實 ⇒ 不成立。"""
+    dists = plugin.get("dists")
+    return _is_pair_list(dists) and bool(dists) and all(tuple(d) in accepted for d in dists)
+
+
 def _is_str_list(v):
     return isinstance(v, list) and all(isinstance(n, str) for n in v)
 
@@ -736,13 +1013,17 @@ def _completeness_problems(comp):
             problems.append("%s 缺欄或型別不符" % key)
     if not _is_str_list(comp.get("blocked")):
         problems.append("blocked 缺欄或型別不符")
+    # (xi):root producer 那一項必須在;policy 指定的設定檔那一項由 verdict 在知道 config_file 之後查。
     blobs = comp.get("config_blobs")
-    if not isinstance(blobs, dict) or not all(
-            isinstance(blobs.get(p), dict)
-            and all(blobs[p].get(k) is None or isinstance(blobs[p].get(k), str)
-                    for k in ("worktree", "head"))
-            for p in COMMITTED_FILES):
+    if not isinstance(blobs, dict) or ROOT_CONFTEST not in blobs or not all(
+            isinstance(b, dict)
+            and all(b.get(k) is None or isinstance(b.get(k), str) for k in ("worktree", "head"))
+            for b in blobs.values()):
         problems.append("config_blobs 缺欄或型別不符")
+    # 票 145 Station 4g:policy 事實(7 鍵;〈五十一〉裁決 3)。Station 4g 之前的 session 沒有 ⇒ 不合格 ⇒ unknown。
+    ep = comp.get("evidence_policy")
+    if not isinstance(ep, dict) or any(k not in ep for k in EVIDENCE_POLICY_KEYS):
+        problems.append("evidence_policy 缺欄或型別不符")
     # 〈三十五〉3 (xiv)–(xviii) 的事實。Station 4e 之前的 session 沒有這些欄位 ⇒ 不合格 ⇒ unknown。
     # 型別在這裡驗,malformed 的事實不得只靠 verdict 的值判斷而繞過。
     if type(comp.get("optimize")) is not int:            # int,不含 bool
@@ -763,15 +1044,19 @@ def _completeness_verdict(run, tf, idents):
     """位置參數已涵蓋 `tf` 之後,依〈二十三〉7 (i)–(vii) 判 `"true"` / `"false"` / `"unknown"`。
 
     - (i) 缺欄 / 型別錯 ⇒ unknown
-    - (vii)(vii′) 有 plugin 不在受支援範圍(含版本不在清單的 dist)⇒ unknown(在支援邊界之外,不知道)
+    - (P) evidence policy 不可用(未提交、工作樹 ≠ HEAD、格式不明、超出能力邊界、與 HEAD 設定檔的 addopts
+      推導不一致;`_effective_policy`)⇒ unknown(票 145 Station 4g;〈四十八〉48.1)。
+      以下的「effective」= 框架能力邊界 B ∩ policy
+    - (vii)(vii′) 有 plugin 不在受支援範圍(含版本不在清單的 dist),或 known_dist 的 (名稱, 版本) 不在
+      effective 的 `dists` ⇒ unknown(在支援邊界之外,不知道)
     - (xii) 有任何 `-p no:<name>` ⇒ unknown
-    - (xiii) pytest 版本不在 `KNOWN_PYTEST_VERSIONS` ⇒ unknown
-    - (viii) `override_ini` 不恰等於 `COMMITTED_ADDOPTS_OVERRIDES` ⇒ unknown(本次的收集定義被覆寫)
+    - (xiii) pytest 版本不在 effective 的 `pytest_versions` ⇒ unknown
+    - (viii) `override_ini` 不恰等於 policy 的 `committed_overrides` ⇒ unknown(本次的收集定義被覆寫)
     - (ix) 有 `-c` / `--config-file` ⇒ unknown(即使指向已提交的權威檔)
-    - (x) 實際採用的設定檔不是 `CONFIG_FILE` ⇒ unknown
-    - (xi) `COMMITTED_FILES` 任一檔的工作樹 blob ≠ HEAD blob,或取不到 ⇒ unknown
+    - (x) 實際採用的設定檔不是 policy 的 `config_file` ⇒ unknown
+    - (xi) `ROOT_CONFTEST` 與 policy 的 `config_file` 任一檔的工作樹 blob ≠ HEAD blob,或取不到 ⇒ unknown
     - (xiv) `sys.flags.optimize` 不是 0 ⇒ unknown(assert 可能沒有執行;〈三十五〉3)
-    - (xviii) Python major.minor 不在 `KNOWN_PYTHON_VERSIONS` ⇒ unknown
+    - (xviii) Python major.minor 不在 effective 的 `python_versions` ⇒ unknown
     - (xv)(xvii) `runxfail` / `trace` 不是 False ⇒ unknown;(xvi) pytest `-W` 有值 ⇒ unknown
       (assertmode 不判定:`optimize == 0` 時 plain 只影響 reporting)
     - (xix) `usepdb`(`--pdb`)不是 False ⇒ unknown(〈三十九〉39.3 第 3 點;與 (xvii) 同理:除錯模式下人可在
@@ -786,26 +1071,35 @@ def _completeness_verdict(run, tf, idents):
     comp = run.get("completeness")
     if _completeness_problems(comp):
         return "unknown"
+    policy = _effective_policy(comp["evidence_policy"])
+    if policy is None:
+        return "unknown"
+    accepted_dists = set(tuple(d) for d in _effective(KNOWN_DISTS, [tuple(d) for d in policy["dists"]]))
     if any(p["kind"] not in SUPPORTED_PLUGIN_KINDS for p in comp["plugins"]):
         return "unknown"
+    if any(p["kind"] == "known_dist" and not _known_dists_accepted(p, accepted_dists)
+           for p in comp["plugins"]):
+        return "unknown"
     if comp["blocked"]:
         return "unknown"
-    if comp["pytest_version"] not in KNOWN_PYTEST_VERSIONS:
+    if comp["pytest_version"] not in _effective(KNOWN_PYTEST_VERSIONS, policy["pytest_versions"]):
         return "unknown"
-    if comp["override_ini"] != list(COMMITTED_ADDOPTS_OVERRIDES):
+    if comp["override_ini"] != list(policy["committed_overrides"]):
         return "unknown"
     if comp["inifilename"] is not None:
         return "unknown"
-    if comp["inipath"] != CONFIG_FILE:
+    config_file = policy["config_file"]
+    if config_file not in FRAMEWORK_CONFIG_FILES or comp["inipath"] != config_file:
         return "unknown"
     blobs = comp["config_blobs"]
-    if not all(blobs[p]["worktree"] and blobs[p]["worktree"] == blobs[p]["head"]
-               for p in COMMITTED_FILES):
-        return "unknown"
+    for p in (config_file, ROOT_CONFTEST):
+        b = blobs.get(p)
+        if not (isinstance(b, dict) and b.get("worktree") and b.get("worktree") == b.get("head")):
+            return "unknown"
     options = comp["options"]
     if comp["optimize"] != 0:
         return "unknown"
-    if comp["python_version"] not in KNOWN_PYTHON_VERSIONS:
+    if comp["python_version"] not in _effective(KNOWN_PYTHON_VERSIONS, policy["python_versions"]):
         return "unknown"
     if options["runxfail"] is not False or options["trace"] is not False:
         return "unknown"
diff --git a/.claude/portable/install.py b/.claude/portable/install.py
index bde60dd..e9c76a6 100644
--- a/.claude/portable/install.py
+++ b/.claude/portable/install.py
@@ -383,14 +383,54 @@ def generate_legacy_list(target, go_live):
     return files
 
 
-def write_decisions_pending(target, buckets, carried_untracked, unmarked):
+POLICY_TEMPLATE = ".agents/evidence-policy.template.json"
+
+
+def _target_redlight(target):
+    """目標 repo 的 `.claude/hooks/redlight.py`(剛複製過去的那一份)。"""
+    import importlib.util
+    spec = importlib.util.spec_from_file_location(
+        "target_redlight", os.path.join(target, ".claude", "hooks", "redlight.py"))
+    mod = importlib.util.module_from_spec(spec)
+    spec.loader.exec_module(mod)
+    return mod
+
+
+def write_policy_template(target):
+    """evidence policy 範本 —— 寫到**非 canonical** 路徑(票 145〈四十八〉48.1 第 6 點 A)。
+
+    內容取自目標 repo 的 redlight `policy_template()`:框架能力邊界常數的完整列舉,**不是本機觀察值**
+    (不自動信任首次觀察值)。範本會隨安裝 commit 一起提交,但它不在 canonical path
+    (`redlight.POLICY_FILE`),**永遠不會被當成 authority**;canonical 那一份只有人放上去並 commit 才存在。
+    不另放範本來源檔:常數只有 redlight 那一份,範本由它產生,兩者不會漂移。
+    """
+    rl = _target_redlight(target)
+    dst = os.path.join(target, *POLICY_TEMPLATE.split("/"))
+    os.makedirs(os.path.dirname(dst), exist_ok=True)
+    with io.open(dst, "w", encoding="utf-8", newline="\n") as f:
+        f.write(json.dumps(rl.policy_template(), ensure_ascii=False, indent=2) + "\n")
+    return dst, rl.POLICY_FILE
+
+
+def write_decisions_pending(target, buckets, carried_untracked, unmarked, policy_file=None):
     """把需要人決定的項目**寫成檔案**,不只印終端機。
 
     印出來沒人看等於沒列(F-036 的同一個病:訊號不落地就等於沒有訊號)。
     寫成 docs/decisions-pending.md —— 人回頭找得到,也進得了版控、能被 review。
     沒有任何待決項目時回 None(不留空檔案佔位)。
+
+    `policy_file`(canonical evidence policy 路徑)給了 ⇒ 一律加一項「evidence policy 未初始化」
+    (票 145〈四十八〉48.1 第 6 點 A):安裝後 canonical policy 必然不存在,在人建立之前任何 run 都退不了紅。
     """
     sections = []
+    if policy_file:
+        sections.append(("evidence policy 未初始化 —— 在建立之前,任何測試執行都不會讓紅燈退休",
+                         [policy_file],
+                         "審閱 `%s`(框架能力邊界的完整列舉)→ 依本 repo 需要收窄;"
+                         "`committed_overrides` 必須等於本 repo 已提交設定檔 addopts 帶來的 override"
+                         "(例:`--strict-markers` ⇒ `strict_markers=true`)→ 存成 `%s` → commit。"
+                         "**這一步只有人做**;status 的 `evidence policy:` 行會顯示目前狀態。"
+                         % (POLICY_TEMPLATE, policy_file)))
     if buckets.get("ask"):
         sections.append(("需要你決定帶不帶(標記為 ask,安裝時沒有帶過去)",
                          buckets["ask"],
@@ -512,6 +552,7 @@ def main(target):
     generate_state(target)
     hook = install_hook(target)
     portable_hook, boot = install_portable_layer(target)
+    _template, policy_file = write_policy_template(target)
 
     run(["git", "add", "-A"], target)
     # **在 add 之後、commit 之前。** `update-index --chmod` 改的是既有 index 條目,
@@ -527,7 +568,8 @@ def main(target):
          "凍結既有 .py 的紅燈豁免清單(go-live %s)" % go_live[:7]], target)
 
     blocked = verify(target)
-    pending = write_decisions_pending(target, buckets, carried_untracked, unmarked)
+    pending = write_decisions_pending(target, buckets, carried_untracked, unmarked,
+                                      policy_file=policy_file)
 
     _out("裝好了:%s" % target)
     _out("  複製      %d 個檔案" % len(buckets["copy"]))
diff --git a/.claude/portable/status.py b/.claude/portable/status.py
index 55e7fcc..2e1ab31 100644
--- a/.claude/portable/status.py
+++ b/.claude/portable/status.py
@@ -557,6 +557,24 @@ def _invalid_count(facts, rl, ticket):
                 and rl.validate_session(r)])
 
 
+POLICY_SOURCE = u".agents/evidence-policy.json"
+
+
+def _policy_line(root, rl):
+    """`evidence policy: <狀態>`(票 145〈五十〉50.1 第 3 點)。狀態由該 root 的 redlight
+    `policy_state()` 判(未初始化 / 未提交 / 工作樹與 HEAD 不同 / 格式不明 / 超出框架能力邊界 / 有效);
+    本檔不另寫判準。沒有這一行的話,「未初始化 ⇒ 永遠 unknown、永遠退不了紅」對下游是靜默的。
+    舊版 redlight(無該函式)或判定拋例外 ⇒ 未記錄,不猜。"""
+    src = getattr(rl, "POLICY_FILE", None) or POLICY_SOURCE
+    if rl is None or not hasattr(rl, "policy_state"):
+        return _line(u"evidence policy", NO_FUNC.replace(u"gate", u"redlight"), src)
+    try:
+        state = rl.policy_state(root)
+    except Exception as e:
+        state = u"%s(%s)" % (UNRECORDED, type(e).__name__)
+    return _line(u"evidence policy", state, src)
+
+
 def _run_source(root, run_log, rl):
     left = _rel(root, run_log) if run_log else NO_FUNC
     right = (_rel(root, rl.session_log(root)) if rl is not None and hasattr(rl, "session_log")
@@ -846,6 +864,7 @@ def _evidence(root, gate, ticket):
             _invalid_count(facts, rl, ticket), tail,
             _last_run_text(facts, rl, ticket))
     out.append(_line(u"test-runs", val, _run_source(root, run_log, rl)))
+    out.append(_policy_line(root, rl))
 
     # ── intercepts 印**兩行**,不是一行 ────────────────────────────────
     # 合成一行的話,「這個月還沒有人被擋」與「這個 repo 從來沒有攔截紀錄」
diff --git a/.claude/portable/verify_gates.py b/.claude/portable/verify_gates.py
index b9f9e0a..7e81067 100644
--- a/.claude/portable/verify_gates.py
+++ b/.claude/portable/verify_gates.py
@@ -269,6 +269,224 @@ def restore(target):
     install.build_mirrors(target)
 
 
+# ── 票 145 Station 4g —— evidence policy 的淨室兩正三負(〈四十六〉46.4 第 4 點;規劃檔 S3g-0 P5)
+#
+# 接在「框架測試在新 repo 跑一次」之後。正一直接讀那一次留下的帳本;其餘四個各自從同一個
+# 基準 commit(安裝 + 規則情境之後的 HEAD)出發,做完 `_ev_restore` 回到基準 ——
+# 目標 repo 的 `.dev/` 是被追蹤的(安裝器不 ignore 它),不回到基準的話上一個情境的帳本與 commit
+# 會留給下一個。
+#
+# 探針只收一支測試檔:已提交的 pyproject 以 `python_files` 把收集範圍定成探針那一支
+# (那是宿主自己的已提交設定,不是窄選 —— consumer 鎖 `inipath` 與 blob,不看 `python_files` 的值)。
+# 否則每個情境的固定指令都要把整套框架測試再跑兩次。
+#
+# 佈置用的 commit 以 `--no-verify` 提交,同 `install.main` 自己的兩個 commit(`install.py` 的 main):
+# 這裡驗的是證據鏈,不是閘門;閘門由上面的規則情境各擋一次。
+
+EV_PROBE = "tests/test_evidence_probe.py"
+EV_RED = "def test_probe():\n    assert False\n"
+EV_GREEN = "def test_probe():\n    assert True\n"
+EV_PYPROJECT = ('[tool.pytest.ini_options]\n'
+                'testpaths = ["tests"]\n'
+                'python_files = ["test_evidence_probe.py"]\n')
+FIXED_COMMAND = [sys.executable, "-X", "utf8", "-m", "pytest", "-q"]
+
+
+def load_target_redlight(target):
+    """每次重新載入(帳本是讀檔,模組本身不快取 run 事實;重新載入只是避免沿用上一個情境的模組狀態)。"""
+    spec = importlib.util.spec_from_file_location(
+        "target_redlight", os.path.join(target, ".claude", "hooks", "redlight.py"))
+    mod = importlib.util.module_from_spec(spec)
+    spec.loader.exec_module(mod)
+    return mod
+
+
+def _ev_status(target):
+    """在子行程跑目標 repo 自己的 status.py,回傳 `{欄位: 值}`(值去掉 `(source: …)`)。"""
+    _rc, out = sh([sys.executable, "-X", "utf8",
+                   os.path.join(target, ".claude", "portable", "status.py"), "--root", target],
+                  target, check=False)
+    fields = {}
+    for line in out.splitlines():
+        key, sep, rest = line.partition(": ")
+        if sep:
+            fields[key.strip()] = rest.split("  (source:")[0].strip()
+    return fields
+
+
+def _ev_set_ticket(target, ticket):
+    p = os.path.join(target, ".dev", "pipeline.json")
+    io.open(p, "w", encoding="utf-8", newline="\n").write(
+        json.dumps({"current_stage": "implement", "feature": "verify",
+                    "ticket_id": ticket, "updated": ""}, ensure_ascii=False, indent=2) + "\n")
+
+
+def _ev_matching_policy(target):
+    """正二的 policy:值 = 當下環境 ∩ 框架能力邊界(規劃檔 P5)。不在邊界內的環境 ⇒ 對應欄位為空,
+    正二會因此不成立 —— 那是正確的(那個環境本來就退不了紅),而失敗訊息會點名正二。"""
+    from importlib import metadata
+    rl = load_target_redlight(target)
+    here = "%d.%d" % tuple(sys.version_info[:2])
+    try:
+        pytest_version = metadata.version("pytest")
+    except Exception:
+        pytest_version = None
+    dists = []
+    for name, version in rl.KNOWN_DISTS:
+        try:
+            if metadata.version(name) == version:
+                dists.append([name, version])
+        except Exception:
+            pass
+    return {"schema": rl.POLICY_SCHEMAS[0][0], "version": rl.POLICY_SCHEMAS[0][1],
+            "config_file": rl.FRAMEWORK_CONFIG_FILES[0],
+            "committed_overrides": [],
+            "python_versions": [v for v in rl.KNOWN_PYTHON_VERSIONS if v == here],
+            "pytest_versions": [v for v in rl.KNOWN_PYTEST_VERSIONS if v == pytest_version],
+            "dists": dists}
+
+
+def _ev_fixed_run(target, extra_env=None):
+    env = dict(os.environ)
+    env.pop("PYTEST_ADDOPTS", None)
+    env.update(extra_env or {})
+    p = subprocess.run(FIXED_COMMAND, cwd=target, capture_output=True, env=env)
+    return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")
+
+
+def _ev_red_then_green(target, ticket, commit_policy=True, dirty_policy=False, extra_env=None):
+    """佈置 pyproject + 失敗的探針(+ policy)並提交 → 固定指令(紅)→ 修好探針、提交
+    →(負二:policy 工作樹多一行)→ 固定指令(依 `extra_env`)。
+    回傳 `(第一次 rc, 第二次 rc, 第二次的 file_coverage, status 欄位, 第二次輸出尾行)`。"""
+    _ev_set_ticket(target, ticket)
+    rl = load_target_redlight(target)
+    policy_text = json.dumps(_ev_matching_policy(target), ensure_ascii=False, indent=2) + "\n"
+    write(target, "pyproject.toml", EV_PYPROJECT)
+    write(target, EV_PROBE, EV_RED)
+    write(target, rl.POLICY_FILE, policy_text)
+    tracked = ["pyproject.toml", EV_PROBE] + ([rl.POLICY_FILE] if commit_policy else [])
+    sh(["git", "add"] + tracked, target)
+    sh(["git", "commit", "-q", "--no-verify", "-m", "evidence %s: red probe" % ticket], target)
+    rc1, _out1 = _ev_fixed_run(target)
+    write(target, EV_PROBE, EV_GREEN)
+    sh(["git", "add", EV_PROBE], target)
+    sh(["git", "commit", "-q", "--no-verify", "-m", "evidence %s: fix probe" % ticket], target)
+    if dirty_policy:
+        write(target, rl.POLICY_FILE, policy_text + "\n")
+    rc2, out2 = _ev_fixed_run(target, extra_env)
+    runs = load_target_redlight(target).load_runs(target)
+    cov = rl.file_coverage(runs[-1], EV_PROBE) if runs else "(沒有 run 事實)"
+    tail = [l for l in out2.strip().splitlines() if l.strip()][-1:]
+    return rc1, rc2, cov, _ev_status(target), (tail[0] if tail else "(沒有輸出)")
+
+
+def _ev_verdict_line(fields, ticket, kind):
+    return fields.get("tests %s under ticket %s" % (kind, ticket), "")
+
+
+def ev_pos1_uninitialized(target, _base=None):
+    """正一:安裝後不動 —— 框架測試全綠(由 main 的上一步保證);那一次 run 對框架測試檔的
+    `file_coverage` 必須是 unknown,status 的 policy 行為「未初始化」。"""
+    rl = load_target_redlight(target)
+    runs = rl.load_runs(target)
+    if not runs:
+        return False, "淨室帳本沒有 run 事實 —— 框架測試那一次沒有留下 session"
+    last = runs[-1]
+    files = sorted(set(n.split("::", 1)[0] for n in last.get("collected") or []))
+    if not files:
+        return False, "最後一筆 session 沒有收集到任何檔"
+    covs = dict((f, rl.file_coverage(last, f)) for f in files)
+    not_unknown = sorted(f for f, c in covs.items() if c != "unknown")
+    state = _ev_status(target).get("evidence policy")
+    ok = not not_unknown and state == rl.POLICY_UNINITIALIZED
+    return ok, "%d 個框架測試檔皆 unknown=%s;evidence policy: %s%s" % (
+        len(files), not not_unknown, state,
+        (";非 unknown 的檔:%s" % ", ".join(not_unknown)) if not_unknown else "")
+
+
+def ev_pos2_initialized(target, _base=None):
+    """正二:已提交且與環境相符的 policy ⇒ 紅 → 固定全套 → true → 合法退休(status 端到端)。"""
+    ticket = "ev-pos2"
+    rc1, rc2, cov, fields, tail = _ev_red_then_green(target, ticket)
+    green = _ev_verdict_line(fields, ticket, "green")
+    red = _ev_verdict_line(fields, ticket, "red")
+    ok = (rc1 == 1 and rc2 == 0 and cov == "true"
+          and EV_PROBE in green and EV_PROBE not in red
+          and fields.get("evidence policy") == load_target_redlight(target).POLICY_VALID)
+    return ok, "rc %s→%s;file_coverage=%s;red=%s;green=%s;evidence policy: %s;%s" % (
+        rc1, rc2, cov, red, green, fields.get("evidence policy"), tail)
+
+
+def _ev_negative(target, ticket, **kw):
+    rc1, rc2, cov, fields, tail = _ev_red_then_green(target, ticket, **kw)
+    red = _ev_verdict_line(fields, ticket, "red")
+    green = _ev_verdict_line(fields, ticket, "green")
+    ok = rc1 == 1 and rc2 == 0 and cov == "unknown" and EV_PROBE in red and EV_PROBE not in green
+    return ok, "rc %s→%s;file_coverage=%s;red=%s;green=%s;evidence policy: %s;%s" % (
+        rc1, rc2, cov, red, green, fields.get("evidence policy"), tail)
+
+
+def ev_neg1_mismatch(target, _base=None):
+    """負一:policy 與環境不符 —— 修好後那一次多一個 policy 未列的 override ⇒ unknown,紅仍在。"""
+    return _ev_negative(target, "ev-neg1",
+                        extra_env={"PYTEST_ADDOPTS": "-o python_functions=test"})
+
+
+def ev_neg2_worktree_differs(target, _base=None):
+    """負二:HEAD 有 policy、工作樹多一行(未 commit)⇒ unknown,紅仍在。"""
+    return _ev_negative(target, "ev-neg2", dirty_policy=True)
+
+
+def ev_neg3_worktree_only(target, _base=None):
+    """負三:policy 只在工作樹、從未 commit ⇒ unknown,紅仍在。"""
+    return _ev_negative(target, "ev-neg3", commit_policy=False)
+
+
+# 鍵 ↔ 情境,比照 `SCENARIOS`。`tests/test_verify_gates.py` 斷言五個鍵都在。
+EVIDENCE_SCENARIOS = {
+    "pos1-uninitialized": ev_pos1_uninitialized,
+    "pos2-initialized": ev_pos2_initialized,
+    "neg1-mismatch": ev_neg1_mismatch,
+    "neg2-worktree-differs": ev_neg2_worktree_differs,
+    "neg3-worktree-only": ev_neg3_worktree_only,
+}
+
+EVIDENCE_LABELS = {
+    "pos1-uninitialized": "正一 未初始化",
+    "pos2-initialized": "正二 已初始化且相符",
+    "neg1-mismatch": "負一 policy / 環境不符",
+    "neg2-worktree-differs": "負二 HEAD 有、工作樹不同",
+    "neg3-worktree-only": "負三 工作樹有、HEAD 沒有",
+}
+
+
+def _ev_restore(target, base):
+    """回到證據情境的基準 commit(兩半,同 `restore`:追蹤側由 git、鏡像重建)。"""
+    sh(["git", "reset", "-q", "--hard", base], target)
+    sh(["git", "clean", "-qfd"], target)
+    install.build_mirrors(target)
+
+
+def run_evidence_scenarios(target):
+    """依序跑五個情境;每個各印一行(不合併)。回傳失敗的 `[(鍵, 細節)]`。"""
+    _rc, base = sh(["git", "rev-parse", "HEAD"], target)
+    base = base.strip()
+    failures = []
+    for key in ("pos1-uninitialized", "pos2-initialized", "neg1-mismatch",
+                "neg2-worktree-differs", "neg3-worktree-only"):
+        try:
+            ok, detail = EVIDENCE_SCENARIOS[key](target, base)
+        except SystemExit as e:
+            ok, detail = False, "情境執行失敗:%s" % e
+        finally:
+            if key != "pos1-uninitialized":
+                _ev_restore(target, base)
+        _out("    %-24s %s  %s" % (EVIDENCE_LABELS[key], "成立 ✓" if ok else "不成立 ✗", detail))
+        if not ok:
+            failures.append((key, detail))
+    return failures
+
+
 def run_scenario(target, code):
     marker = SCENARIOS[code](target)
     if marker == "predicate":
@@ -389,7 +607,16 @@ def main(workdir):
             "框架測試在新 repo 裡不是全綠 —— 那些紅與新專案無關,"
             "會訓練人忽略訊號。框架測試只能斷言框架的性質。")
 
-    _out("\n全部 %d 條規則各擋下一次,權威層偵測正常,框架測試在新 repo 全綠。"
+    # 票 145 Station 4g:evidence policy 的兩正三負。正一讀的就是上面那一次框架測試的帳本,
+    # 所以必須緊接在它之後、任何 reset 之前。
+    _out("\n=== evidence policy 淨室情境(兩正三負;每個情境各一行)===")
+    ev_failures = run_evidence_scenarios(target)
+    if ev_failures:
+        raise SystemExit("\n%d 個 evidence policy 情境沒有成立:%s"
+                         % (len(ev_failures), " ".join(EVIDENCE_LABELS[k] for k, _ in ev_failures)))
+
+    _out("\n全部 %d 條規則各擋下一次,權威層偵測正常,框架測試在新 repo 全綠,"
+         "evidence policy 兩正三負成立。"
          "\n安裝位置:%s" % (len(codes), target))
 
 
diff --git a/tests/conftest.py b/tests/conftest.py
index 7156c34..565deb3 100644
--- a/tests/conftest.py
+++ b/tests/conftest.py
@@ -342,6 +342,25 @@ def _flag(session, name):
     return bool(getattr(session, name))
 
 
+# 「屬性不存在」的 sentinel(票 145 Station 4g 修法 B):與「屬性存在、值為 None」分開。
+_MISSING = object()
+
+
+def _override_ini_of(option):
+    """交給 `normalize_overrides` 的 `override_ini` 原值。**先判欄位是否存在,再解讀值;只讀一次。**
+
+    pytest 9.1.1 的 `-o` 為 `action="append"`、沒有 default(`_pytest/helpconfig.py:112-119`),
+    未給任何 `-o` / OverrideIniAction 旗標時值為 None —— 語意是「沒有 override」,與「屬性取不到」不同:
+      - 屬性不存在 ⇒ None(事實取不到;consumer 判 unknown);
+      - 值為 None ⇒ 以 `[]` 交給 `normalize_overrides`,落帳 `[]`(事實取得成功:pytest 明確表示沒有 -o);
+      - 其他 ⇒ `normalize_overrides` 照舊(非 list ⇒ None)。
+    """
+    raw = getattr(option, "override_ini", _MISSING)
+    if raw is _MISSING:
+        return None
+    return raw if raw is not None else []
+
+
 def _completeness_of(session):
     """本次 session 的完整性事實。任何一步出錯 ⇒ None(寧可多紅,不讓 pytest 失敗)。
 
@@ -351,10 +370,19 @@ def _completeness_of(session):
     pyproject.toml 與本檔的工作樹 blob vs HEAD blob(git 子程序,失敗 ⇒ None);`pytest_version`
     取自本檔 import 的 `pytest`;`blocked` 是 `list_name_plugin()` 中值為 None 的名稱(`-p no:`)。
     路徑型事實一律轉成 root 相對路徑,不落帳絕對路徑。
+    `override_ini` 先判屬性是否存在(`_override_ini_of`):pytest 9.1.1 的 -o 為 action="append" 無 default,
+    未給時為 None,語意是「沒有 override」(落帳 `[]`),與「屬性取不到」(落帳 None ⇒ unknown)不同。
 
     票 145 Station 4e(〈三十五〉3 (xiv)–(xviii)、4)另記 pass 有效性的事實:`optimize` 與 `python_version`
     在此刻經模組層 `sys` 讀;`runxfail` / `pythonwarnings` / `trace` 隨 `COMPLETENESS_OPTIONS` 記在 `options`。
     路徑型 metadata 依欄位類別正規化(F3-甲):相對路徑以 `invocation_params.dir` 解析。
+
+    票 145 Station 4g(〈四十八〉48.1 第 2 點 A)另記 host evidence policy 的事實 `evidence_policy`(7 鍵),
+    依規劃檔 P3 I-3 的六步:HEAD 有沒有 → HEAD blob → 工作樹 blob(`git hash-object`)是否相同 →
+    內容**只從 HEAD blob**(`git cat-file`)解析 → schema / version → 記錄;另記 policy 指定的設定檔
+    在 HEAD 的 addopts 原值。工作樹的 policy 檔只做 identity 比對,之後不再讀。步驟本體在
+    `redlight.evidence_policy_facts`(與 `committed_blobs` 同一處,status 共用);本檔只擷取事實,不判定。
+    舊版 redlight.py(下游未同步)沒有該函式 ⇒ 記 None(涵蓋未知)。
     """
     try:
         if _pre_narrowing_broken:
@@ -375,12 +403,13 @@ def _completeness_of(session):
             "plugins": _redlight.classify_plugins(_ROOT, name_plugins,
                                                   pm.list_plugin_distinfo()),
             "blocked": _redlight.blocked_plugins(name_plugins, _ROOT),
-            "override_ini": _redlight.normalize_overrides(getattr(option, "override_ini", None),
-                                                          _ROOT, inv_dir),
+            "override_ini": _redlight.normalize_overrides(_override_ini_of(option), _ROOT, inv_dir),
             "inifilename": _redlight.normalize_config_path(getattr(option, "inifilename", None),
                                                            _ROOT, inv_dir),
             "inipath": _redlight.normalize_config_path(getattr(cfg, "inipath", None), _ROOT),
             "config_blobs": _redlight.committed_blobs(_ROOT),
+            "evidence_policy": (_redlight.evidence_policy_facts(_ROOT)
+                                if hasattr(_redlight, "evidence_policy_facts") else None),
             "pytest_version": version if isinstance(version, str) else None,
             "optimize": _optimize_flag(),
             "python_version": _python_version(),
diff --git a/tests/test_redlight.py b/tests/test_redlight.py
index cbe1322..6f444db 100644
--- a/tests/test_redlight.py
+++ b/tests/test_redlight.py
@@ -287,6 +287,14 @@ class _Session:
         self.testscollected = len(self.items)
 
 
+# 票 145 Station 4g 授權 G3(〈四十八〉48.1 第 5 點;規劃檔 S3g-0 P2-B):driver 把 conftest 所見的版本事實
+# 固定在能力邊界內,正控不再依賴執行它的直譯器 / pytest 版本。模組載入當下的真實版本記在這裡 ——
+# 測試在呼叫 driver **之前**自己設過 `pytest.__version__`(例:測「版本不在清單」的那支)時不覆蓋它。
+_REAL_PYTEST_VERSION = pytest.__version__
+_PINNED_PYTEST_VERSION = "9.1.1"
+_PINNED_PYTHON = (3, 11, 0, "final", 0)
+
+
 def _isolated_conftest(monkeypatch, tmp_path):
     c = TestTheRecorderCannotKillTheRunner._conftest()
     monkeypatch.setattr(redlight, "ROOT", str(tmp_path))
@@ -296,6 +304,10 @@ def _isolated_conftest(monkeypatch, tmp_path):
                         str(tmp_path / ".dev" / "pipeline.json"))
     monkeypatch.setattr(c, "_redlight", redlight)
     monkeypatch.setattr(c, "_ROOT", tmp_path)
+    monkeypatch.setattr(c, "sys", _e_sys(optimize=_e_real_sys.flags.optimize,
+                                         version_info=_EVersion(*_PINNED_PYTHON)), raising=False)
+    if pytest.__version__ == _REAL_PYTEST_VERSION:
+        monkeypatch.setattr(pytest, "__version__", _PINNED_PYTEST_VERSION)
     c._outcomes.clear()
     return c
 
@@ -1128,6 +1140,19 @@ _D_CACHEPROVIDER_BLOCKED = ("cacheprovider", "pytest_cacheprovider", "stepwise",
 _D_FULL = {"tests/test_x.py": [X_A, X_B]}
 _D_ONLY_B = {"tests/test_x.py": [X_B]}
 
+# 票 145 Station 4g 授權 G1(規劃檔 S3g-0 P6「需要的授權」1):與 baseline 相符的已提交 evidence policy ——
+# 已提交 addopts `-ra --strict-markers` ⇒ `strict_markers=true`;版本與 dist 等於 driver 固定的事實(授權 3)。
+_D_POLICY_FILE = ".agents/evidence-policy.json"
+_D_BASELINE_POLICY = {
+    "schema": "monkeyleash.evidence-policy",
+    "version": 1,
+    "config_file": "pyproject.toml",
+    "committed_overrides": list(_D_FIXED_OVERRIDES),
+    "python_versions": ["3.11"],
+    "pytest_versions": ["9.1.1"],
+    "dists": [["anyio", "4.15.0"]],
+}
+
 
 def _d_write(root, rel, text):
     p = pathlib.Path(str(root)) / rel
@@ -1146,10 +1171,11 @@ def _d_committed_root(root):
     conftest = pathlib.Path(str(root)) / "tests" / "conftest.py"
     conftest.parent.mkdir(parents=True, exist_ok=True)
     conftest.write_bytes((ROOT / "tests" / "conftest.py").read_bytes())
+    _d_write(root, _D_POLICY_FILE, json.dumps(_D_BASELINE_POLICY, ensure_ascii=False, indent=2) + u"\n")
     _d_git(root, "init", "-q")
     _d_git(root, "config", "user.email", "t@example.invalid")
     _d_git(root, "config", "user.name", "t")
-    _d_git(root, "add", "pyproject.toml", "tests/conftest.py")
+    _d_git(root, "add", "pyproject.toml", "tests/conftest.py", _D_POLICY_FILE)
     _d_git(root, "commit", "-q", "-m", "baseline")
     return root
 
@@ -1486,52 +1512,11 @@ class TestCollectionDefinitionCoverage:
         got = _d_coverage(tmp_path, monkeypatch)
         assert got == "true", got
 
-    def test_d4_the_committed_addopts_override_constant_matches_pyproject(self):
-        """D4-1(票 145〈三十一〉裁決 3;〈二十九〉2 (viii) 的鎖步測試)。Station 4d 授權新增。
-
-        鎖的是「`redlight.COMMITTED_ADDOPTS_OVERRIDES` ↔ agent-gates repo **真正提交**的
-        `pyproject.toml` addopts」。來源固定為 `git show HEAD:pyproject.toml`(在 repo 根執行,唯讀);
-        不讀工作樹、不用 tmp repo、不寫死 addopts 字串 —— 用自造的設定只會驗到測試自己。
-        git 不可用或讀取失敗 ⇒ 失敗(不 skip)。
-
-        推導(pytest 9.1.1):addopts 以 shlex 切開(ini 模式下 type="args",`_pytest/config/__init__.py:1547`;
-        放到 args 最前面一起解析,`:1559-1562`),逐一對應:
-          - `OverrideIniAction` 旗標(`_pytest/main.py:76-96`;動作本體 `_pytest/config/argparsing.py:491-503`):
-            `--strict-config` → `strict_config=true`、`--strict-markers` → `strict_markers=true`、
-            `--strict` → `strict=true`;
-          - `-o` / `--override-ini KEY=VAL`(`_pytest/helpconfig.py:113-116`,append)→ `KEY=VAL`;
-          - 其他旗標不產生 override 項目。
-        依出現順序組成清單,必須恰等於常數。
-        """
-        import shlex
-        try:
-            import tomllib as _toml
-        except ImportError:                      # Python 3.10
-            import tomli as _toml
-        proc = _d_subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:pyproject.toml"],
-                                 capture_output=True)
-        assert proc.returncode == 0, proc.stderr
-        cfg = _toml.loads(proc.stdout.decode("utf-8"))
-        addopts = cfg["tool"]["pytest"]["ini_options"]["addopts"]
-        tokens = shlex.split(addopts) if isinstance(addopts, str) else list(addopts)
-        flags = {"--strict-config": "strict_config=true",
-                 "--strict-markers": "strict_markers=true",
-                 "--strict": "strict=true"}
-        expected = []
-        i = 0
-        while i < len(tokens):
-            tok = tokens[i]
-            if tok in flags:
-                expected.append(flags[tok])
-            elif tok in ("-o", "--override-ini"):
-                i += 1
-                expected.append(tokens[i])
-            elif tok.startswith("--override-ini="):
-                expected.append(tok.split("=", 1)[1])
-            elif tok.startswith("-o"):
-                expected.append(tok[2:])
-            i += 1
-        assert list(redlight.COMMITTED_ADDOPTS_OVERRIDES) == expected, (addopts, expected)
+    # 原 `test_d4_the_committed_addopts_override_constant_matches_pyproject` 於票 145 Station 4g 刪除
+    # (〈四十八〉48.1 第 4 點 C,Jeff 明文修訂〈三十一〉裁決 3 的**適用位置**,語意不變):
+    # 常數 `COMMITTED_ADDOPTS_OVERRIDES` 已移進宿主 policy;框架那一半由 `TestAddoptsDerivation`(fixture)
+    # 與 verdict 時的機器鎖步承接,agent-gates 自身「policy ↔ pyproject」的鎖步由宿主專用、不出貨的
+    # tests/test_host_evidence_policy.py 承接(git show HEAD、讀不到即失敗、不 skip)。
 
 
 # ─────────────────────────────────────────────────────────────────────────────
@@ -2505,3 +2490,45 @@ class TestAddoptsDerivation:
                                      policy_text=_g_policy_text(_g_policy())), monkeypatch)
         assert control == "true", control
         assert broken != "true", broken
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# 票 145 Station 4g 補紅燈 —— 「沒有任何 override」的正控與「override 事實取不到」的鎖
+#
+# 成因:pytest 9.1.1 的 `-o` 是 `action="append"`、沒有 default(`_pytest/helpconfig.py:112-119`),
+# 沒給任何 `-o` / OverrideIniAction 旗標時 `config.option.override_ini` 為 **None**(屬性存在)。
+# 3g / 3g-1b 的正控都帶 `--strict-markers`,沒有一支走到這條路徑;S4G1 的淨室「正二」因此不成立
+# (`.dev/reports/2026-10-04T213043Z-ticket145-station4g-s4g1-local-pass-cleanroom-pos2-fail.md`)。
+# 裁決:修法 B(producer 先判欄位是否存在、再解讀值);A(consumer 把 None 當 [])否決。
+# 既有 helper(`_g_root` / `_g_policy` / `_g_policy_text` / `_g_coverage` / `_e_option` / `_d_option`)只呼叫、不修改。
+# ─────────────────────────────────────────────────────────────────────────────
+
+class TestEvidencePolicyNoOverride:
+
+    def test_g3_no_override_anywhere_is_full_coverage(self, tmp_path, monkeypatch):
+        """T1。分類:behavior-red(在 S4G1 上必須失敗)。
+
+        已提交 addopts `-ra`(推導出的 override 為 `[]`)、policy `committed_overrides: []`(兩者自洽)、
+        執行時沒有任何 `-o`:pytest 明確表示「沒有 override」,`option.override_ini is None`(屬性存在)
+        ⇒ 必須能取得 full coverage(`"true"`)。否則設定裡沒有 `-o` 類旗標的宿主永遠退不了紅。
+        S4G1 上失敗的原因:`tests/conftest.py` 的 producer 把 None 原樣交給 `normalize_overrides`,
+        落帳 `override_ini: null`;`.claude/hooks/redlight.py` 的 (viii) 比 `None != []` ⇒ unknown。
+        """
+        root = _g_root(tmp_path / "root", policy_text=_g_policy_text(_g_policy(committed_overrides=[])),
+                       addopts="-ra")
+        got = _g_coverage(root, monkeypatch, option=_e_option(usepdb=False, override_ini=None))
+        assert got == "true", got
+
+    def test_g3_a_missing_override_fact_is_not_full_coverage(self, tmp_path, monkeypatch):
+        """T2。分類:regression-lock(在 S4G1 上必須通過)。
+
+        與 T1 同一種佈置,但 `config.option` 根本沒有 `override_ini` 屬性 ⇒ 事實取不到 ⇒ 不得為 `"true"`。
+        **事實取不到 ≠ 沒有 override**:鎖住修法 B 的語意,防止日後改成在 consumer 把 None 當 `[]`
+        (修法 A;那會把「取不到」當成「確定沒有」⇒ fail-open)。
+        """
+        root = _g_root(tmp_path / "root", policy_text=_g_policy_text(_g_policy(committed_overrides=[])),
+                       addopts="-ra")
+        option = _d_option(missing=("override_ini",), runxfail=False, pythonwarnings=None, trace=False,
+                           usepdb=False)
+        got = _g_coverage(root, monkeypatch, option=option)
+        assert got != "true", got
diff --git a/tests/test_status.py b/tests/test_status.py
index bccda18..6a5ab2b 100644
--- a/tests/test_status.py
+++ b/tests/test_status.py
@@ -594,7 +594,8 @@ class TestTestsUnderTicketUsesTheLatestRecordPerFile:
                               u"dists": [[u"anyio", u"4.15.0"]]}],
                 u"blocked": [], u"override_ini": list(_T_FIXED_OVERRIDES), u"inifilename": None,
                 u"inipath": u"pyproject.toml", u"config_blobs": blobs, u"pytest_version": u"9.1.1",
-                u"optimize": 0, u"python_version": u"3.11"})
+                u"optimize": 0, u"python_version": u"3.11",
+                u"evidence_policy": _t_policy_facts(root)})
 
         out = render(root)
         red = _value_of(out, u"tests red under ticket 99")
@@ -1370,7 +1371,8 @@ class TestOrphans:
                                     u"blocked": [], u"override_ini": list(_T_FIXED_OVERRIDES),
                                     u"inifilename": None, u"inipath": u"pyproject.toml",
                                     u"config_blobs": blobs, u"pytest_version": u"9.1.1",
-                                    u"optimize": 0, u"python_version": u"3.11"})
+                                    u"optimize": 0, u"python_version": u"3.11",
+                                    u"evidence_policy": _t_policy_facts(root)})
         out = render(root)
         orphaned = _value_of(out, u"tests orphaned under ticket 99")
         green = _value_of(out, u"tests green under ticket 99")
@@ -1495,6 +1497,14 @@ class _ChainSession:
         self.config = _ChainConfig(args, root)
 
 
+# 票 145 Station 4g 授權 G3(〈四十八〉48.1 第 5 點;規劃檔 S3g-0 P2-B):driver 把 conftest 所見的版本事實
+# 固定在能力邊界內,正控不再依賴執行它的直譯器 / pytest 版本。模組載入當下的真實版本記在這裡 ——
+# 測試在呼叫 driver **之前**自己設過 `pytest.__version__` 時不覆蓋它(與 tests/test_redlight.py 同式)。
+_REAL_PYTEST_VERSION = pytest.__version__
+_PINNED_PYTEST_VERSION = u"9.1.1"
+_PINNED_PYTHON = (3, 11, 0, u"final", 0)
+
+
 def _chain_conftest(root, monkeypatch):
     """載入 tests/conftest.py,並把它與本檔那一份 redlight 的所有寫入都導到 `root`。"""
     import importlib.util
@@ -1509,6 +1519,10 @@ def _chain_conftest(root, monkeypatch):
                         str(pathlib.Path(root) / ".dev" / "pipeline.json"))
     monkeypatch.setattr(c, "_redlight", redlight)
     monkeypatch.setattr(c, "_ROOT", pathlib.Path(root))
+    monkeypatch.setattr(c, "sys", _e_sys(optimize=sys.flags.optimize,
+                                         version_info=_EVersion(*_PINNED_PYTHON)), raising=False)
+    if pytest.__version__ == _REAL_PYTEST_VERSION:
+        monkeypatch.setattr(pytest, "__version__", _PINNED_PYTEST_VERSION)
     return c
 
 
@@ -2362,6 +2376,20 @@ _T_BASELINE_INI = {
 
 _T_FIXED_OVERRIDES = [u"strict_markers=true"]
 
+# 票 145 Station 4g 授權 G1(規劃檔 S3g-0 P6「需要的授權」1):與 baseline 相符的已提交 evidence policy ——
+# 已提交 addopts `-ra --strict-markers` ⇒ `strict_markers=true`;版本與 dist 等於 driver 固定的事實(授權 3)。
+_T_POLICY_FILE = u".agents/evidence-policy.json"
+_T_BASELINE_POLICY = {
+    u"schema": u"monkeyleash.evidence-policy",
+    u"version": 1,
+    u"config_file": u"pyproject.toml",
+    u"committed_overrides": list(_T_FIXED_OVERRIDES),
+    u"python_versions": [u"3.11"],
+    u"pytest_versions": [u"9.1.1"],
+    u"dists": [[u"anyio", u"4.15.0"]],
+}
+_T_BASELINE_ADDOPTS = u"-ra --strict-markers"
+
 
 def _t_git(root, *args):
     return subprocess.run(["git"] + list(args), cwd=str(root), capture_output=True, check=True)
@@ -2374,14 +2402,28 @@ def _t_committed(root):
     conftest = pathlib.Path(root) / "tests" / "conftest.py"
     conftest.parent.mkdir(parents=True, exist_ok=True)
     conftest.write_bytes((ROOT / "tests" / "conftest.py").read_bytes())
+    policy = pathlib.Path(root) / ".agents" / "evidence-policy.json"
+    policy.parent.mkdir(parents=True, exist_ok=True)
+    with io.open(str(policy), "w", encoding="utf-8", newline="\n") as f:
+        f.write(json.dumps(_T_BASELINE_POLICY, ensure_ascii=False, indent=2) + u"\n")
     _t_git(root, "init", "-q")
     _t_git(root, "config", "user.email", "t@example.invalid")
     _t_git(root, "config", "user.name", "t")
-    _t_git(root, "add", "pyproject.toml", "tests/conftest.py")
+    _t_git(root, "add", "pyproject.toml", "tests/conftest.py", _T_POLICY_FILE)
     _t_git(root, "commit", "-q", "-m", "baseline")
     return root
 
 
+def _t_policy_facts(root):
+    """`_t_committed(root)` 之後的 `completeness["evidence_policy"]` 事實(7 鍵;授權 G2 用):
+    blob 由 git 實際取得,內容 = 已提交的 baseline policy,`committed_addopts` = 已提交的 addopts 原值。"""
+    head = _t_git(root, "rev-parse", "HEAD:" + _T_POLICY_FILE).stdout.decode().strip()
+    worktree = _t_git(root, "hash-object", _T_POLICY_FILE).stdout.decode().strip()
+    return {u"path": _T_POLICY_FILE, u"head": head, u"worktree": worktree,
+            u"schema": _T_BASELINE_POLICY[u"schema"], u"version": _T_BASELINE_POLICY[u"version"],
+            u"policy": dict(_T_BASELINE_POLICY), u"committed_addopts": _T_BASELINE_ADDOPTS}
+
+
 class _TDist:
     def __init__(self, name, version):
         self.project_name = name
```
<!-- 逐字結束 -->

### E.3 `git diff f4fa0418aa037f95ef7d1f59c6fe6a812a80414c..8e7775526e462d984abb0992ed74c1e1aa3648dd -- <CODE_FILES>`(S4G1 → TARGET;修法 B 與 T1 / T2)

<!-- 逐字開始 -->
```diff
diff --git a/tests/conftest.py b/tests/conftest.py
index 64d5dd0..565deb3 100644
--- a/tests/conftest.py
+++ b/tests/conftest.py
@@ -342,6 +342,25 @@ def _flag(session, name):
     return bool(getattr(session, name))
 
 
+# 「屬性不存在」的 sentinel(票 145 Station 4g 修法 B):與「屬性存在、值為 None」分開。
+_MISSING = object()
+
+
+def _override_ini_of(option):
+    """交給 `normalize_overrides` 的 `override_ini` 原值。**先判欄位是否存在,再解讀值;只讀一次。**
+
+    pytest 9.1.1 的 `-o` 為 `action="append"`、沒有 default(`_pytest/helpconfig.py:112-119`),
+    未給任何 `-o` / OverrideIniAction 旗標時值為 None —— 語意是「沒有 override」,與「屬性取不到」不同:
+      - 屬性不存在 ⇒ None(事實取不到;consumer 判 unknown);
+      - 值為 None ⇒ 以 `[]` 交給 `normalize_overrides`,落帳 `[]`(事實取得成功:pytest 明確表示沒有 -o);
+      - 其他 ⇒ `normalize_overrides` 照舊(非 list ⇒ None)。
+    """
+    raw = getattr(option, "override_ini", _MISSING)
+    if raw is _MISSING:
+        return None
+    return raw if raw is not None else []
+
+
 def _completeness_of(session):
     """本次 session 的完整性事實。任何一步出錯 ⇒ None(寧可多紅,不讓 pytest 失敗)。
 
@@ -351,6 +370,8 @@ def _completeness_of(session):
     pyproject.toml 與本檔的工作樹 blob vs HEAD blob(git 子程序,失敗 ⇒ None);`pytest_version`
     取自本檔 import 的 `pytest`;`blocked` 是 `list_name_plugin()` 中值為 None 的名稱(`-p no:`)。
     路徑型事實一律轉成 root 相對路徑,不落帳絕對路徑。
+    `override_ini` 先判屬性是否存在(`_override_ini_of`):pytest 9.1.1 的 -o 為 action="append" 無 default,
+    未給時為 None,語意是「沒有 override」(落帳 `[]`),與「屬性取不到」(落帳 None ⇒ unknown)不同。
 
     票 145 Station 4e(〈三十五〉3 (xiv)–(xviii)、4)另記 pass 有效性的事實:`optimize` 與 `python_version`
     在此刻經模組層 `sys` 讀;`runxfail` / `pythonwarnings` / `trace` 隨 `COMPLETENESS_OPTIONS` 記在 `options`。
@@ -382,8 +403,7 @@ def _completeness_of(session):
             "plugins": _redlight.classify_plugins(_ROOT, name_plugins,
                                                   pm.list_plugin_distinfo()),
             "blocked": _redlight.blocked_plugins(name_plugins, _ROOT),
-            "override_ini": _redlight.normalize_overrides(getattr(option, "override_ini", None),
-                                                          _ROOT, inv_dir),
+            "override_ini": _redlight.normalize_overrides(_override_ini_of(option), _ROOT, inv_dir),
             "inifilename": _redlight.normalize_config_path(getattr(option, "inifilename", None),
                                                            _ROOT, inv_dir),
             "inipath": _redlight.normalize_config_path(getattr(cfg, "inipath", None), _ROOT),
diff --git a/tests/test_redlight.py b/tests/test_redlight.py
index d3fc25e..6f444db 100644
--- a/tests/test_redlight.py
+++ b/tests/test_redlight.py
@@ -2490,3 +2490,45 @@ class TestAddoptsDerivation:
                                      policy_text=_g_policy_text(_g_policy())), monkeypatch)
         assert control == "true", control
         assert broken != "true", broken
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# 票 145 Station 4g 補紅燈 —— 「沒有任何 override」的正控與「override 事實取不到」的鎖
+#
+# 成因:pytest 9.1.1 的 `-o` 是 `action="append"`、沒有 default(`_pytest/helpconfig.py:112-119`),
+# 沒給任何 `-o` / OverrideIniAction 旗標時 `config.option.override_ini` 為 **None**(屬性存在)。
+# 3g / 3g-1b 的正控都帶 `--strict-markers`,沒有一支走到這條路徑;S4G1 的淨室「正二」因此不成立
+# (`.dev/reports/2026-10-04T213043Z-ticket145-station4g-s4g1-local-pass-cleanroom-pos2-fail.md`)。
+# 裁決:修法 B(producer 先判欄位是否存在、再解讀值);A(consumer 把 None 當 [])否決。
+# 既有 helper(`_g_root` / `_g_policy` / `_g_policy_text` / `_g_coverage` / `_e_option` / `_d_option`)只呼叫、不修改。
+# ─────────────────────────────────────────────────────────────────────────────
+
+class TestEvidencePolicyNoOverride:
+
+    def test_g3_no_override_anywhere_is_full_coverage(self, tmp_path, monkeypatch):
+        """T1。分類:behavior-red(在 S4G1 上必須失敗)。
+
+        已提交 addopts `-ra`(推導出的 override 為 `[]`)、policy `committed_overrides: []`(兩者自洽)、
+        執行時沒有任何 `-o`:pytest 明確表示「沒有 override」,`option.override_ini is None`(屬性存在)
+        ⇒ 必須能取得 full coverage(`"true"`)。否則設定裡沒有 `-o` 類旗標的宿主永遠退不了紅。
+        S4G1 上失敗的原因:`tests/conftest.py` 的 producer 把 None 原樣交給 `normalize_overrides`,
+        落帳 `override_ini: null`;`.claude/hooks/redlight.py` 的 (viii) 比 `None != []` ⇒ unknown。
+        """
+        root = _g_root(tmp_path / "root", policy_text=_g_policy_text(_g_policy(committed_overrides=[])),
+                       addopts="-ra")
+        got = _g_coverage(root, monkeypatch, option=_e_option(usepdb=False, override_ini=None))
+        assert got == "true", got
+
+    def test_g3_a_missing_override_fact_is_not_full_coverage(self, tmp_path, monkeypatch):
+        """T2。分類:regression-lock(在 S4G1 上必須通過)。
+
+        與 T1 同一種佈置,但 `config.option` 根本沒有 `override_ini` 屬性 ⇒ 事實取不到 ⇒ 不得為 `"true"`。
+        **事實取不到 ≠ 沒有 override**:鎖住修法 B 的語意,防止日後改成在 consumer 把 None 當 `[]`
+        (修法 A;那會把「取不到」當成「確定沒有」⇒ fail-open)。
+        """
+        root = _g_root(tmp_path / "root", policy_text=_g_policy_text(_g_policy(committed_overrides=[])),
+                       addopts="-ra")
+        option = _d_option(missing=("override_ini",), runxfail=False, pythonwarnings=None, trace=False,
+                           usepdb=False)
+        got = _g_coverage(root, monkeypatch, option=option)
+        assert got != "true", got
```
<!-- 逐字結束 -->

### E.4 `git diff de36ebcbab284ef11064a9943b5191750482dd93..2737e02c64b88f4d0a39bdafbea2f3776993cf2b -- <TEST_FILES>`(BASE → S3G1)

用途:3g 主紅燈 —— 新增 33 支 = 26 behavior-red + 7 regression-lock,含新檔 `tests/test_host_evidence_policy.py`。

<!-- 逐字開始 -->
```diff
diff --git a/tests/test_host_evidence_policy.py b/tests/test_host_evidence_policy.py
new file mode 100644
index 0000000..ac1fd02
--- /dev/null
+++ b/tests/test_host_evidence_policy.py
@@ -0,0 +1,91 @@
+# -*- coding: utf-8 -*-
+"""宿主專用:agent-gates **自己**已提交的 evidence policy ↔ 已提交的 `pyproject.toml`(票 145)。
+
+**不出貨**(`.agents/portable-manifest.txt` 標 `skip`)。它斷言的是**這個 repo** 的已提交事實,
+而那兩個檔都是各 repo 自己的(`pyproject.toml` 標 `skip`、`.agents/evidence-policy.json` 標 `skip`)——
+帶到下游就是「帶走測試卻不帶走它讀的檔案 = 到站即紅」(票 145〈四十六〉46.2 的 CI 失敗正是這個形狀)。
+
+規格沿用票 145〈三十一〉裁決 3,**語意不變、只改適用位置**(〈四十八〉48.1 第 4 點,Jeff 明文):
+  - 來源固定為 `git show HEAD:<path>`(在 repo 根執行,唯讀);不讀工作樹檔案;
+  - 不得以 tmp repo 或寫死的 addopts 字串代替 —— 用自造設定只會驗到測試自己;
+  - git 不可用或讀取失敗 ⇒ **失敗**(不得 skip、不得靜默通過);
+  - 唯讀:不寫任何檔案、不改 repo 狀態。
+
+推導(pytest 9.1.1;與原 test_d4 相同,**在本檔獨立實作**,不呼叫 redlight 的推導函式 ——
+材料不從被量的東西身上拿):addopts 以 shlex 切開(`_pytest/config/__init__.py:1547`),逐一對應:
+  - `OverrideIniAction` 旗標(`_pytest/main.py:76-96`):`--strict-config` → `strict_config=true`、
+    `--strict-markers` → `strict_markers=true`、`--strict` → `strict=true`;
+  - `-o` / `--override-ini KEY=VAL`(`_pytest/helpconfig.py:113-116`)→ `KEY=VAL`;
+  - 其他旗標不產生 override 項目。
+"""
+
+import importlib.util
+import json
+import pathlib
+import shlex
+import subprocess
+
+ROOT = pathlib.Path(__file__).resolve().parents[1]
+
+POLICY_FILE = ".agents/evidence-policy.json"
+
+
+def _load_redlight():
+    spec = importlib.util.spec_from_file_location(
+        "redlight_for_host_policy", str(ROOT / ".claude" / "hooks" / "redlight.py"))
+    mod = importlib.util.module_from_spec(spec)
+    spec.loader.exec_module(mod)
+    return mod
+
+
+def _git_show_head(rel):
+    proc = subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:" + rel], capture_output=True)
+    assert proc.returncode == 0, (rel, proc.stderr)
+    return proc.stdout.decode("utf-8")
+
+
+def _derive_overrides(addopts):
+    tokens = shlex.split(addopts) if isinstance(addopts, str) else list(addopts or [])
+    flags = {"--strict-config": "strict_config=true",
+             "--strict-markers": "strict_markers=true",
+             "--strict": "strict=true"}
+    out = []
+    i = 0
+    while i < len(tokens):
+        tok = tokens[i]
+        if tok in flags:
+            out.append(flags[tok])
+        elif tok in ("-o", "--override-ini"):
+            i += 1
+            out.append(tokens[i])
+        elif tok.startswith("--override-ini="):
+            out.append(tok.split("=", 1)[1])
+        elif tok.startswith("-o"):
+            out.append(tok[2:])
+        i += 1
+    return out
+
+
+def test_the_committed_policy_matches_the_committed_pyproject():
+    """票 145 Station 3g #27。分類:behavior-red(BASELINE 560f618 上 HEAD 沒有 policy ⇒ `git show` 失敗)。
+
+    agent-gates 的 `HEAD:.agents/evidence-policy.json`:
+      - schema / version 為 `monkeyleash.evidence-policy` / 1;
+      - `config_file == "pyproject.toml"`;
+      - `committed_overrides` 恰等於 `HEAD:pyproject.toml` 的 `[tool.pytest.ini_options].addopts` 依上方規則的推導;
+      - 版本與 dist 欄位都在框架能力邊界之內(〈四十八〉48.1 第 3 點:界外 ⇒ 整份不合格,宿主自己這份必須先過)。
+    """
+    try:
+        import tomllib as _toml
+    except ImportError:                      # Python 3.10
+        import tomli as _toml
+    policy = json.loads(_git_show_head(POLICY_FILE))
+    cfg = _toml.loads(_git_show_head("pyproject.toml"))
+    addopts = cfg["tool"]["pytest"]["ini_options"].get("addopts")
+    assert policy.get("schema") == "monkeyleash.evidence-policy" and policy.get("version") == 1, policy
+    assert policy.get("config_file") == "pyproject.toml", policy
+    assert policy.get("committed_overrides") == _derive_overrides(addopts), (addopts, policy)
+    redlight = _load_redlight()
+    assert set(policy.get("python_versions") or ()) <= set(redlight.KNOWN_PYTHON_VERSIONS), policy
+    assert set(policy.get("pytest_versions") or ()) <= set(redlight.KNOWN_PYTEST_VERSIONS), policy
+    assert set(tuple(d) for d in policy.get("dists") or ()) <= set(redlight.KNOWN_DISTS), policy
diff --git a/tests/test_redlight.py b/tests/test_redlight.py
index 877b131..cbe1322 100644
--- a/tests/test_redlight.py
+++ b/tests/test_redlight.py
@@ -2142,3 +2142,366 @@ class TestIdentifierFullMatch:
         broken = _e_run(tmp_path, monkeypatch, blocked=("abc\n",))
         assert control["completeness"]["blocked"] == ["abc"], control["completeness"]
         assert broken["completeness"]["blocked"] == [redlight.NON_IDENTIFIER], broken["completeness"]
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# 票 145 Station 3g 紅燈 —— Host evidence policy(〈四十六〉46.4、〈四十八〉48.1)
+#
+# 合約:票 145〈四十八〉48.1(Jeff 對 S3g-0 規劃檔 P8 的裁決)。規劃:docs/audits/2026-10-03-m1a-station3g-redlight-plan.md P3、P6。
+# 下文 `<BASELINE>` = 560f618560ddac1a34e0e835b99a1e3a5cc7eda5(S3G0;產品碼與 S6-1 faf7cb4 相同)。
+#
+# 介面(本刀定稿;語意依規劃檔 P3):
+#   - canonical path `.agents/evidence-policy.json`(框架常數,不可由 policy 指定);
+#   - schema `"monkeyleash.evidence-policy"` version 1;欄位全部必填、不得有多餘鍵:
+#     `config_file` / `committed_overrides` / `python_versions` / `pytest_versions` / `dists`;
+#   - producer 在 session 的 `completeness["evidence_policy"]` 記 `{"path", "head", "worktree", "schema", "version", "policy"}`,
+#     內容由 HEAD committed blob 解析;worktree 只做 identity 比對;
+#   - 框架推導函式 `redlight.addopts_overrides(addopts)`:已提交 addopts → override 清單(pytest 9.1.1 的對應)。
+#
+# driver 原則(沿用 3c-1b / 3d / 3e / 3f):
+#   - 每次模擬執行載入全新 conftest(`_isolated_conftest`);tmp root 是**真的** git repo,policy 檔**真的**提交 / 修改;
+#   - **版本事實一律固定**(〈四十八〉48.1 第 5 點):conftest 所見的 `sys.version_info` 為 3.11、`pytest.__version__` 為 9.1.1,
+#     除非該案例本身就在測版本 —— 本段的正控不依賴執行它的直譯器;
+#   - 需要兩種 repo 狀態的案例,對照組與破壞組各用 `tmp_path` 底下一個子目錄當 root;
+#   - 單點測試在同一支測試內放對照組。
+# 本段 helper 全部新寫;既有 helper(`_isolated_conftest` / `_d_plugins` / `_d_drive` / `_D_FULL` / `_e_option` /
+# `_e_sys` / `_EVersion` 等)只呼叫、不修改。
+# ─────────────────────────────────────────────────────────────────────────────
+
+_G_POLICY_FILE = ".agents/evidence-policy.json"
+_G_SCHEMA = "monkeyleash.evidence-policy"
+_G_FIXED_ADDOPTS = "-ra --strict-markers"
+
+
+def _g_policy(**overrides):
+    """與 agent-gates 現行常數一致、且在能力邊界之內的 policy(dict)。"""
+    policy = {
+        "schema": _G_SCHEMA,
+        "version": 1,
+        "config_file": "pyproject.toml",
+        "committed_overrides": ["strict_markers=true"],
+        "python_versions": ["3.11"],
+        "pytest_versions": ["9.1.1"],
+        "dists": [["anyio", "4.15.0"]],
+    }
+    policy.update(overrides)
+    return policy
+
+
+def _g_policy_text(policy):
+    return json.dumps(policy, ensure_ascii=False, indent=2) + "\n"
+
+
+def _g_write(root, rel, text):
+    p = pathlib.Path(str(root)) / rel
+    p.parent.mkdir(parents=True, exist_ok=True)
+    with io.open(str(p), "w", encoding="utf-8", newline="\n") as f:
+        f.write(text)
+
+
+def _g_root(root, policy_text=None, commit_policy=True, addopts=_G_FIXED_ADDOPTS,
+            policy_path=_G_POLICY_FILE, extra_files=None):
+    """在 `root` 建真的 git repo:提交 `pyproject.toml`(addopts 由參數決定)、root conftest(真檔內容)、
+    `extra_files`;`policy_text` 不為 None ⇒ 寫到 `policy_path`,`commit_policy` 為真才一起提交。"""
+    root = pathlib.Path(str(root))
+    root.mkdir(parents=True, exist_ok=True)
+    pyproject = u'[tool.pytest.ini_options]\ntestpaths = ["tests"]\n'
+    if addopts is not None:
+        pyproject += u'addopts = "%s"\n' % addopts
+    _g_write(root, "pyproject.toml", pyproject)
+    conftest = root / "tests" / "conftest.py"
+    conftest.parent.mkdir(parents=True, exist_ok=True)
+    conftest.write_bytes((ROOT / "tests" / "conftest.py").read_bytes())
+    tracked = ["pyproject.toml", "tests/conftest.py"]
+    for rel, text in (extra_files or {}).items():
+        _g_write(root, rel, text)
+        tracked.append(rel)
+    if policy_text is not None:
+        _g_write(root, policy_path, policy_text)
+        if commit_policy:
+            tracked.append(policy_path)
+    _d_git(root, "init", "-q")
+    _d_git(root, "config", "user.email", "t@example.invalid")
+    _d_git(root, "config", "user.name", "t")
+    _d_git(root, "add", *tracked)
+    _d_git(root, "commit", "-q", "-m", "baseline")
+    return root
+
+
+def _g_default_root(root):
+    """提交了合法、與執行環境一致的 policy 的 repo(正控用)。"""
+    return _g_root(root, policy_text=_g_policy_text(_g_policy()))
+
+
+def _g_run(root, monkeypatch, option=None, python=(3, 11), pytest_version="9.1.1",
+           anyio_version="4.15.0", inipath="pyproject.toml", ini=None):
+    """一次模擬執行(全新 conftest;`_D_FULL` 全收集、全 passed、exit 0;其他事實同固定全套)。
+    版本事實固定為參數值(預設 3.11 / 9.1.1 / anyio 4.15.0)。回傳**最後一筆** session。"""
+    root = pathlib.Path(str(root))
+    selected = [n for ids in _D_FULL.values() for n in ids]
+    c = _isolated_conftest(monkeypatch, root)
+    monkeypatch.setattr(c, "sys", _e_sys(optimize=0, version_info=_EVersion(python[0], python[1], 0, "final", 0)),
+                        raising=False)
+    monkeypatch.setattr(pytest, "__version__", pytest_version)
+    pm = _d_plugins(c, root, anyio_version=anyio_version)
+    _d_drive(c, root, _D_FULL, selected, dict((n, "passed") for n in selected),
+             option=option if option is not None else _e_option(usepdb=False), pm=pm,
+             inipath=inipath, ini=ini)
+    runs = redlight.load_runs(str(root))
+    assert runs, runs
+    return runs[-1]
+
+
+def _g_coverage(root, monkeypatch, **kw):
+    return redlight.file_coverage(_g_run(root, monkeypatch, **kw), "tests/test_x.py")
+
+
+def _g_control(tmp_path, monkeypatch):
+    """對照組:`tmp_path/control` 是提交了合法 policy 的 repo,固定全套 ⇒ 應為 `"true"`。"""
+    return _g_coverage(_g_default_root(tmp_path / "control"), monkeypatch)
+
+
+def _g_without(policy, key):
+    out = dict(policy)
+    out.pop(key)
+    return out
+
+
+# 規劃檔 P6 #2–#5:policy 自身的 HEAD / worktree integrity 不成立的四種狀態。
+_G_UNCOMMITTED_STATES = ["worktree-only", "worktree-differs", "staged-only", "deleted-in-worktree"]
+
+# 規劃檔 P6 #6–#10:HEAD 與 worktree 一致,但文件本身看不懂。
+_G_UNKNOWN_DOCUMENTS = [
+    pytest.param(u"{not json\n", id="malformed-json"),
+    pytest.param(_g_policy_text(_g_policy(schema="other.evidence-policy")), id="unknown-schema"),
+    pytest.param(_g_policy_text(_g_policy(version=2)), id="unknown-version"),
+    pytest.param(_g_policy_text(_g_policy(location=".agents/elsewhere.json")), id="unknown-key"),
+    pytest.param(_g_policy_text(_g_without(_g_policy(), "dists")), id="missing-field"),
+]
+
+
+class TestEvidencePolicyBootstrap:
+
+    def test_g3_a_repo_without_a_policy_is_not_full_coverage(self, tmp_path, monkeypatch):
+        """#1(〈四十六〉46.4 第 3 點:缺少 host policy 不得解讀成可信;規劃檔 P3 I-3 第 2 步)。分類:behavior-red。
+
+        對照組:提交了合法 policy 的 repo ⇒ `"true"`。破壞組:同樣的已提交設定與 conftest,但 repo 從未有 policy
+        (淨室安裝後、尚未初始化的狀態)⇒ 不得為 `"true"`。
+        BASELINE 上失敗的原因:`<BASELINE>:.claude/hooks/redlight.py:786-833` 不讀任何 policy ⇒ `:833` 回 `"true"`。
+        """
+        control = _g_control(tmp_path, monkeypatch)
+        broken = _g_coverage(_g_root(tmp_path / "broken"), monkeypatch)
+        assert control == "true", control
+        assert broken != "true", broken
+
+    @pytest.mark.parametrize("state", _G_UNCOMMITTED_STATES)
+    def test_g3_an_uncommitted_policy_state_is_not_full_coverage(self, tmp_path, monkeypatch, state):
+        """#2–#5(〈四十六〉46.4 第 4 點 負二 / 負三、第 6 點;規劃檔 P3 I-3 第 2、4 步)。分類:behavior-red。
+
+        對照組:提交了合法 policy 的 repo ⇒ `"true"`。破壞組(policy 內容皆為同一份合法 policy):
+          - `[worktree-only]`:policy 只在工作樹,HEAD 從未有它(負三)⇒ 不得為 `"true"`;
+          - `[worktree-differs]`:HEAD 有 policy,工作樹內容不同(本地改了未 commit)(負二)⇒ 不得為 `"true"`;
+          - `[staged-only]`:policy 已 `git add` 但未 commit ⇒ 不得為 `"true"`;
+          - `[deleted-in-worktree]`:HEAD 有 policy,工作樹把它刪了 ⇒ 不得為 `"true"`。
+        BASELINE 上失敗的原因:同 #1(`<BASELINE>:.claude/hooks/redlight.py:833`)。
+        """
+        control = _g_control(tmp_path, monkeypatch)
+        text = _g_policy_text(_g_policy())
+        broken_root = tmp_path / "broken"
+        if state == "worktree-only":
+            _g_root(broken_root, policy_text=text, commit_policy=False)
+        elif state == "staged-only":
+            _g_root(broken_root, policy_text=text, commit_policy=False)
+            _d_git(broken_root, "add", _G_POLICY_FILE)
+        else:
+            _g_root(broken_root, policy_text=text)
+            policy = broken_root / _G_POLICY_FILE
+            if state == "worktree-differs":
+                _g_write(broken_root, _G_POLICY_FILE, text + u"\n")
+            else:
+                policy.unlink()
+        broken = _g_coverage(broken_root, monkeypatch)
+        assert control == "true", control
+        assert broken != "true", broken
+
+    @pytest.mark.parametrize("text", _G_UNKNOWN_DOCUMENTS)
+    def test_g3_an_unknown_policy_document_is_not_full_coverage(self, tmp_path, monkeypatch, text):
+        """#6–#10(〈四十六〉46.4 第 6 點:schema / version 未知 ⇒ 只能 unknown;規劃檔 P3 I-1、I-2、I-3 第 5 步)。
+        分類:behavior-red。
+
+        對照組:提交了合法 policy 的 repo ⇒ `"true"`。破壞組:policy 已提交且工作樹 = HEAD,但內容為
+        `[malformed-json]` 不是 JSON、`[unknown-schema]` schema 不是 `monkeyleash.evidence-policy`、
+        `[unknown-version]` version 2、`[unknown-key]` 多一個自我指定位置的鍵 `location`(I-1)、
+        `[missing-field]` 缺 `dists` ⇒ 不得為 `"true"`。
+        BASELINE 上失敗的原因:同 #1(`<BASELINE>:.claude/hooks/redlight.py:833`)。
+        """
+        control = _g_control(tmp_path, monkeypatch)
+        broken = _g_coverage(_g_root(tmp_path / "broken", policy_text=text), monkeypatch)
+        assert control == "true", control
+        assert broken != "true", broken
+
+    def test_g3_a_policy_outside_the_canonical_path_is_not_full_coverage(self, tmp_path, monkeypatch):
+        """#11(〈四十六〉46.4 第 6 點:canonical location 屬框架不變式;規劃檔 P3 I-1)。分類:behavior-red。
+
+        對照組:policy 提交在 `.agents/evidence-policy.json` ⇒ `"true"`。破壞組:同一份合法 policy 只提交在
+        repo 根的 `evidence-policy.json`(canonical path 沒有檔)⇒ 不得為 `"true"`。
+        BASELINE 上失敗的原因:同 #1(`<BASELINE>:.claude/hooks/redlight.py:833`)。
+        """
+        control = _g_control(tmp_path, monkeypatch)
+        broken = _g_coverage(_g_root(tmp_path / "broken", policy_text=_g_policy_text(_g_policy()),
+                                     policy_path="evidence-policy.json"), monkeypatch)
+        assert control == "true", control
+        assert broken != "true", broken
+
+    def test_g3_the_producer_records_the_policy_identity(self, tmp_path, monkeypatch):
+        """#12(〈四十八〉48.1 第 2 點:producer 依 I-3 從 HEAD committed blob 解析並記入 session)。分類:behavior-red。
+
+        對照組:repo 沒有 policy ⇒ `evidence_policy` 沒有 HEAD blob(整欄 None 或 `head` 為 None)。
+        破壞組(主斷言):提交了合法 policy ⇒ 持久化的 `completeness["evidence_policy"]` 為
+        `{"path": ".agents/evidence-policy.json", "head": <HEAD blob>, "worktree": <同一個 blob>,
+        "schema": "monkeyleash.evidence-policy", "version": 1, "policy": <解析後內容>}`;
+        `<HEAD blob>` 由測試自己以 `git rev-parse HEAD:<path>` 取得。
+        BASELINE 上失敗的原因:`<BASELINE>:tests/conftest.py:368-387` 的 completeness 沒有 `evidence_policy` 欄。
+        """
+        none_run = _g_run(_g_root(tmp_path / "none"), monkeypatch)
+        none_ep = (none_run.get("completeness") or {}).get("evidence_policy")
+        root = _g_default_root(tmp_path / "with")
+        head = _d_git(root, "rev-parse", "HEAD:" + _G_POLICY_FILE).stdout.decode("ascii").strip()
+        run = _g_run(root, monkeypatch)
+        ep = (run.get("completeness") or {}).get("evidence_policy")
+        assert isinstance(ep, dict), run.get("completeness")
+        assert ep.get("path") == _G_POLICY_FILE, ep
+        assert ep.get("head") == head and ep.get("worktree") == head, (ep, head)
+        assert ep.get("schema") == _G_SCHEMA and ep.get("version") == 1, ep
+        assert ep.get("policy") == _g_policy(), ep
+        assert none_ep is None or none_ep.get("head") is None, none_ep
+
+    def test_g3_policy_content_is_not_read_from_the_worktree(self, tmp_path, monkeypatch):
+        """#13(〈四十六〉46.4 第 6 點:worktree 只做 identity check,不作為 authority 內容來源;規劃檔 P3 I-3 第 5 步)。
+        分類:regression-lock。
+
+        提交了合法 policy;模擬執行期間,Python 層的 `open` / `io.open` 只要開 canonical path 就拋例外
+        (`git hash-object` / `git cat-file` 由子行程自己讀,不受影響)⇒ 仍須為 `"true"`。
+        前置控制:guard 確實擋得住對 canonical path 的 open。
+        BASELINE 上通過:根本不讀 policy。上線後鎖住「內容只從 HEAD blob 來」。
+        """
+        import builtins
+        root = _g_default_root(tmp_path / "root")
+        policy_path = str(root / _G_POLICY_FILE)
+        real_open = builtins.open
+
+        def guarded(file, *args, **kwargs):
+            if str(file).replace("\\", "/").endswith(_G_POLICY_FILE):
+                raise OSError("worktree policy must not be read as authority content: %s" % file)
+            return real_open(file, *args, **kwargs)
+
+        with monkeypatch.context() as m:
+            m.setattr(builtins, "open", guarded)
+            m.setattr(io, "open", guarded)
+            with pytest.raises(OSError):
+                io.open(policy_path, encoding="utf-8")
+            got = _g_coverage(root, monkeypatch)
+        assert got == "true", got
+
+    def test_g3_a_matching_committed_policy_is_full_coverage(self, tmp_path, monkeypatch):
+        """#14(〈四十六〉46.4 第 3 點:宿主已提交 policy 且實際環境 == policy ⇒ 才可能 true;正二的單元版)。
+        分類:regression-lock。
+
+        提交了合法 policy(值 = 現行常數)、工作樹 = HEAD、版本事實 3.11 / 9.1.1 / anyio 4.15.0、
+        `override_ini == ["strict_markers=true"]`、全收集、全 passed ⇒ `"true"`。
+        """
+        got = _g_coverage(_g_default_root(tmp_path / "root"), monkeypatch)
+        assert got == "true", got
+
+
+# 規劃檔 P6 #15–#18:(policy 的覆寫, 執行事實, 額外提交的檔)
+_G_WIDENING = [
+    pytest.param({"python_versions": ["3.11", "3.12"]}, {"python": (3, 12)}, None, id="python"),
+    pytest.param({"pytest_versions": ["9.1.1", "9.2.0"]}, {"pytest_version": "9.2.0"}, None, id="pytest"),
+    pytest.param({"dists": [["anyio", "4.15.0"], ["anyio", "9.9.9"]]}, {"anyio_version": "9.9.9"}, None, id="dist"),
+    pytest.param({"config_file": "pytest.ini"}, {"inipath": "pytest.ini"},
+                 {"pytest.ini": u"[pytest]\ntestpaths = tests\naddopts = -ra --strict-markers\n"}, id="config-file"),
+]
+
+
+class TestEvidencePolicyBoundary:
+
+    @pytest.mark.parametrize("policy_overrides, run_kw, extra_files", _G_WIDENING)
+    def test_g3_a_policy_cannot_widen_the_capability_boundary(self, tmp_path, monkeypatch,
+                                                              policy_overrides, run_kw, extra_files):
+        """#15–#18(〈四十六〉46.4 第 3 點:host policy 只能收窄,不能擴張;〈四十八〉48.1 第 3 點)。分類:regression-lock。
+
+        對照組:合法 policy、環境在邊界內 ⇒ `"true"`。破壞組:policy 列出能力邊界外的值,且執行環境正是那個值 ——
+        `[python]` 3.12、`[pytest]` 9.2.0、`[dist]` anyio 9.9.9、`[config-file]` `pytest.ini`(另提交該檔)⇒ 不得為 `"true"`。
+        BASELINE 上通過:框架常數已擋下這四種環境(`<BASELINE>:.claude/hooks/redlight.py:793-794, 799-800, 808-809, 613`)。
+        上線後鎖住「policy 不能把它們加回來」。
+        """
+        control = _g_control(tmp_path, monkeypatch)
+        broken_root = _g_root(tmp_path / "broken", policy_text=_g_policy_text(_g_policy(**policy_overrides)),
+                              extra_files=extra_files)
+        broken = _g_coverage(broken_root, monkeypatch, **run_kw)
+        assert control == "true", control
+        assert broken != "true", broken
+
+    @pytest.mark.parametrize("case", ["override", "narrowed-dist"])
+    def test_g3_a_policy_environment_mismatch_is_not_full_coverage(self, tmp_path, monkeypatch, case):
+        """#19–#20(〈四十六〉46.4 第 4 點 負一:policy / environment mismatch ⇒ unknown)。分類:behavior-red。
+
+        對照組:合法 policy、固定全套 ⇒ `"true"`。破壞組:
+          - `[override]`:已提交 addopts 為 `-ra`、policy `committed_overrides: []`(兩者自洽);
+            執行時經 `PYTEST_ADDOPTS` 帶入 `--strict-markers` ⇒ `override_ini == ["strict_markers=true"]`(policy 未列)⇒ 不得為 `"true"`;
+          - `[narrowed-dist]`:policy `dists: []`(宿主不接受 anyio);執行時 anyio 4.15.0 已載入 ⇒ 不得為 `"true"`。
+        BASELINE 上失敗的原因:`<BASELINE>:.claude/hooks/redlight.py:795` 的比較對象是框架常數 `["strict_markers=true"]`、
+        `:613` 的 `KNOWN_DISTS` 含 anyio 4.15.0 ⇒ `:833` 回 `"true"`。
+        """
+        control = _g_control(tmp_path, monkeypatch)
+        if case == "override":
+            broken_root = _g_root(tmp_path / "broken", addopts="-ra",
+                                  policy_text=_g_policy_text(_g_policy(committed_overrides=[])))
+        else:
+            broken_root = _g_root(tmp_path / "broken", policy_text=_g_policy_text(_g_policy(dists=[])))
+        broken = _g_coverage(broken_root, monkeypatch)
+        assert control == "true", control
+        assert broken != "true", broken
+
+
+# 規劃檔 P6 #21–#25:已提交 addopts → override 清單(pytest 9.1.1:`_pytest/main.py:76-96` 的 OverrideIniAction 旗標、
+# `_pytest/helpconfig.py:113-116` 的 `-o` / `--override-ini`;其他旗標不產生 override)
+_G_DERIVATIONS = [
+    pytest.param("-ra --strict-markers", ["strict_markers=true"], id="strict-markers"),
+    pytest.param("--strict-config -q", ["strict_config=true"], id="strict-config"),
+    pytest.param("-o python_files=check_*.py -oxfail_strict=true", ["python_files=check_*.py", "xfail_strict=true"],
+                 id="o-flag"),
+    pytest.param("--override-ini=cache_dir=.c --strict-markers", ["cache_dir=.c", "strict_markers=true"],
+                 id="override-ini-eq"),
+    pytest.param("", [], id="no-addopts"),
+]
+
+
+class TestAddoptsDerivation:
+
+    @pytest.mark.parametrize("addopts, expected", _G_DERIVATIONS)
+    def test_g3_overrides_are_derived_from_committed_addopts(self, addopts, expected):
+        """#21–#25(〈四十八〉48.1 第 4 點:框架推導規則以 fixture 測)。分類:behavior-red。
+
+        `redlight.addopts_overrides(addopts)` 依出現順序回傳 override 清單,必須恰等於預期。
+        這裡驗的是**推導規則**(框架性質),不是「常數 ↔ 宿主設定」—— 後者在 tests/test_host_evidence_policy.py。
+        BASELINE 上失敗的原因:`<BASELINE>:.claude/hooks/redlight.py` 沒有 `addopts_overrides`(只有常數 `:493`)。
+        """
+        derive = getattr(redlight, "addopts_overrides")
+        assert derive(addopts) == expected, (addopts, derive(addopts))
+
+    def test_g3_a_policy_disagreeing_with_the_committed_addopts_is_not_full_coverage(self, tmp_path, monkeypatch):
+        """#26(〈四十八〉48.1 第 4 點:verdict 時機器鎖步 —— policy 必須與 HEAD 設定檔的 addopts 推導一致)。
+        分類:behavior-red。
+
+        對照組:已提交 addopts `-ra --strict-markers`、policy `["strict_markers=true"]` ⇒ `"true"`。
+        破壞組:只改已提交 addopts 為 `-ra`(policy 與執行時 override 都仍是 `["strict_markers=true"]`,
+        後者經 `PYTEST_ADDOPTS` 帶入)⇒ policy 與已提交設定不一致 ⇒ 不得為 `"true"`。
+        BASELINE 上失敗的原因:`<BASELINE>:.claude/hooks/redlight.py:795` 只比框架常數,不讀已提交 addopts ⇒ `:833` 回 `"true"`。
+        """
+        control = _g_control(tmp_path, monkeypatch)
+        broken = _g_coverage(_g_root(tmp_path / "broken", addopts="-ra",
+                                     policy_text=_g_policy_text(_g_policy())), monkeypatch)
+        assert control == "true", control
+        assert broken != "true", broken
diff --git a/tests/test_status.py b/tests/test_status.py
index 05e0c67..3d05029 100644
--- a/tests/test_status.py
+++ b/tests/test_status.py
@@ -2856,3 +2856,162 @@ class TestDebuggerModeLocks:
         got = _lines_of(root)
         assert u"tests/test_x.py" in got[u"green"], got
         assert u"tests/test_x.py" not in got[u"red"], got
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 票 145 Station 3g 紅燈 —— Host evidence policy 的串接(producer → 持久化 run 事實 → status)
+#
+# 合約:票 145〈四十八〉48.1。規劃:docs/audits/2026-10-03-m1a-station3g-redlight-plan.md P3、P6。
+# 下文 `<BASELINE>` = 560f618560ddac1a34e0e835b99a1e3a5cc7eda5(S3G0)。
+#
+# 每一次模擬執行都經**真實 tests/conftest.py**(`_chain_conftest` 每次載入全新模組)寫入 tmp root 的帳本,
+# 再由 status 讀回判定;tmp root 是真的 git repo,policy 檔**真的**提交 / 修改(canonical path
+# `.agents/evidence-policy.json`;schema 與欄位同 tests/test_redlight.py 的 3g 段)。
+# **版本事實一律固定**(〈四十八〉48.1 第 5 點):conftest 所見的 `sys.version_info` 為 3.11、`pytest.__version__` 為 9.1.1。
+# 本段 helper 全部新寫;既有 helper(`_root_with_redlight` / `_chain_conftest` / `_lines_of` / `_t_option` /
+# `_t_drive` / `_e_option` / `_e_sys` / `_EVersion`)只呼叫、不修改。
+# ═══════════════════════════════════════════════════════════════════════════
+
+_G_POLICY_FILE = u".agents/evidence-policy.json"
+
+
+def _g_policy(**overrides):
+    policy = {
+        u"schema": u"monkeyleash.evidence-policy",
+        u"version": 1,
+        u"config_file": u"pyproject.toml",
+        u"committed_overrides": [u"strict_markers=true"],
+        u"python_versions": [u"3.11"],
+        u"pytest_versions": [u"9.1.1"],
+        u"dists": [[u"anyio", u"4.15.0"]],
+    }
+    policy.update(overrides)
+    return policy
+
+
+def _g_write(root, rel, text):
+    p = pathlib.Path(str(root)) / rel
+    p.parent.mkdir(parents=True, exist_ok=True)
+    with io.open(str(p), "w", encoding="utf-8", newline="\n") as f:
+        f.write(text)
+
+
+def _g_committed(root, policy=None, commit_policy=True, addopts=u"-ra --strict-markers"):
+    """把 `root` 變成真的 git repo:提交 `pyproject.toml`(addopts 由參數決定)與 root conftest(真檔內容);
+    `policy` 不為 None ⇒ 寫到 canonical path,`commit_policy` 為真才一起提交。"""
+    _g_write(root, u"pyproject.toml",
+             u'[tool.pytest.ini_options]\ntestpaths = ["tests"]\naddopts = "%s"\n' % addopts)
+    conftest = pathlib.Path(root) / "tests" / "conftest.py"
+    conftest.parent.mkdir(parents=True, exist_ok=True)
+    conftest.write_bytes((ROOT / "tests" / "conftest.py").read_bytes())
+    tracked = [u"pyproject.toml", u"tests/conftest.py"]
+    if policy is not None:
+        _g_write(root, _G_POLICY_FILE, json.dumps(policy, ensure_ascii=False, indent=2) + u"\n")
+        if commit_policy:
+            tracked.append(_G_POLICY_FILE)
+    _t_git(root, "init", "-q")
+    _t_git(root, "config", "user.email", "t@example.invalid")
+    _t_git(root, "config", "user.name", "t")
+    _t_git(root, "add", *tracked)
+    _t_git(root, "commit", "-q", "-m", "baseline")
+    return root
+
+
+def _g_drive(root, monkeypatch, outcomes, exitstatus, option=None):
+    """一次模擬執行:全新 conftest;tests/test_x.py 的 S_A / S_B 全收集;版本事實固定為 3.11 / 9.1.1。"""
+    c = _chain_conftest(root, monkeypatch)
+    monkeypatch.setattr(c, "sys", _e_sys(optimize=0, version_info=_EVersion(3, 11, 0, "final", 0)), raising=False)
+    monkeypatch.setattr(pytest, "__version__", "9.1.1")
+    _t_drive(c, root, {u"tests/test_x.py": [S_A, S_B]}, [S_A, S_B], outcomes,
+             exitstatus=exitstatus, option=option if option is not None else _e_option(usepdb=False))
+
+
+def _g_red_then(root, monkeypatch, option=None):
+    """R1 固定全套:S_A failed、S_B passed(exit 1)⇒ S_A 為已知紅;R2:S_A、S_B 皆 passed(exit 0,`option`)。
+    回傳兩筆 run 事實(各自用全新 conftest)。"""
+    _g_drive(root, monkeypatch, {S_A: "failed", S_B: "passed"}, 1)
+    _g_drive(root, monkeypatch, {S_A: "passed", S_B: "passed"}, 0, option=option)
+    runs = redlight.load_runs(root)
+    assert len(runs) == 2, runs
+    return runs
+
+
+def _g_assert_scenario(runs):
+    """情境斷言:R1 為 B;R2 schema 合格且為 A(紅留著,是因為 coverage 不是 "true",不是因為 run 本身不合格)。"""
+    assert redlight.run_state(runs[0]) == u"B", runs[0]
+    assert redlight.validate_session(runs[1]) == [], runs[1]
+    assert redlight.run_state(runs[1]) == u"A", runs[1]
+
+
+class TestEvidencePolicyChain:
+
+    def test_g3_no_policy_does_not_retire_a_known_red(self, tmp_path, monkeypatch):
+        """#28(〈四十六〉46.4 第 3 點、第 4 點 正一的鏈條面:未初始化 ⇒ unknown ⇒ 不得退紅)。分類:behavior-red。
+
+        repo 已提交設定與 conftest,但從未有 policy。R1 固定全套:test_a failed ⇒ 已知紅。
+        R2 固定全套:全 passed ⇒ 不得退紅、不得 green。
+        BASELINE 上失敗的原因:R2 在 `<BASELINE>:.claude/hooks/redlight.py:833` 判 `"true"` ⇒
+        `<BASELINE>:.claude/portable/status.py:456-474` 退掉 test_a ⇒ green。
+        """
+        root = _root_with_redlight(tmp_path)
+        _g_committed(root)
+        runs = _g_red_then(root, monkeypatch)
+        _g_assert_scenario(runs)
+        got = _lines_of(root)
+        assert u"tests/test_x.py" in got[u"red"], got
+        assert u"tests/test_x.py" not in got[u"green"], got
+
+    @pytest.mark.parametrize("state", ["worktree-only", "worktree-differs"])
+    def test_g3_an_uncommitted_policy_does_not_retire_a_known_red(self, tmp_path, monkeypatch, state):
+        """#29–#30(〈四十六〉46.4 第 4 點 負三 / 負二 的鏈條版)。分類:behavior-red。
+
+        `[worktree-only]`:合法 policy 只在工作樹,HEAD 從未有它(負三)。
+        `[worktree-differs]`:HEAD 有合法 policy,工作樹內容不同、未 commit(負二)。
+        R1 固定全套:test_a failed ⇒ 已知紅。R2 固定全套:全 passed ⇒ 不得退紅、不得 green。
+        BASELINE 上失敗的原因:同 #28(`<BASELINE>:.claude/hooks/redlight.py:833`;`<BASELINE>:.claude/portable/status.py:456-474`)。
+        """
+        root = _root_with_redlight(tmp_path)
+        if state == "worktree-only":
+            _g_committed(root, policy=_g_policy(), commit_policy=False)
+        else:
+            _g_committed(root, policy=_g_policy())
+            _g_write(root, _G_POLICY_FILE,
+                     json.dumps(_g_policy(), ensure_ascii=False, indent=2) + u"\n\n")
+        runs = _g_red_then(root, monkeypatch)
+        _g_assert_scenario(runs)
+        got = _lines_of(root)
+        assert u"tests/test_x.py" in got[u"red"], got
+        assert u"tests/test_x.py" not in got[u"green"], got
+
+    def test_g3_a_policy_environment_mismatch_does_not_retire_a_known_red(self, tmp_path, monkeypatch):
+        """#31(〈四十六〉46.4 第 4 點 負一的鏈條版)。分類:behavior-red。
+
+        已提交 addopts `-ra`、policy `committed_overrides: []`(兩者自洽)並已提交。R1 固定全套:test_a failed ⇒ 已知紅。
+        R2:經 `PYTEST_ADDOPTS` 帶入 `--strict-markers` ⇒ `override_ini == ["strict_markers=true"]`(policy 未列),
+        全 passed ⇒ 不得退紅、不得 green。
+        BASELINE 上失敗的原因:`<BASELINE>:.claude/hooks/redlight.py:795` 的比較對象是框架常數 ⇒ `:833` 判 `"true"` ⇒
+        `<BASELINE>:.claude/portable/status.py:456-474` 退紅。
+        """
+        root = _root_with_redlight(tmp_path)
+        _g_committed(root, policy=_g_policy(committed_overrides=[]), addopts=u"-ra")
+        runs = _g_red_then(root, monkeypatch)
+        _g_assert_scenario(runs)
+        assert runs[1]["completeness"]["override_ini"] == [u"strict_markers=true"], runs[1]["completeness"]
+        got = _lines_of(root)
+        assert u"tests/test_x.py" in got[u"red"], got
+        assert u"tests/test_x.py" not in got[u"green"], got
+
+    def test_g3_a_matching_committed_policy_retires_the_red(self, tmp_path, monkeypatch):
+        """#32(〈四十六〉46.4 第 4 點 正二的鏈條版:提交合法 policy → 製造 red → 固定全套 → true → red 合法退休)。
+        分類:regression-lock。
+
+        提交合法 policy(值 = 現行常數)、工作樹 = HEAD。R1 固定全套:test_a failed ⇒ 已知紅。
+        R2 固定全套:全 passed ⇒ X 退紅、在 green。
+        """
+        root = _root_with_redlight(tmp_path)
+        _g_committed(root, policy=_g_policy())
+        runs = _g_red_then(root, monkeypatch)
+        _g_assert_scenario(runs)
+        got = _lines_of(root)
+        assert u"tests/test_x.py" in got[u"green"], got
+        assert u"tests/test_x.py" not in got[u"red"], got
diff --git a/tests/test_verify_gates.py b/tests/test_verify_gates.py
index 95b4b53..ff1a3b6 100644
--- a/tests/test_verify_gates.py
+++ b/tests/test_verify_gates.py
@@ -289,3 +289,27 @@ class TestScenarioR4LeavesTheTargetClean:
             "追蹤側沒有被還原乾淨:%r" % dirty.decode("utf-8", "replace")
         assert not os.path.exists(os.path.join(target, "docs", "adr", "verify-trigger.md")), \
             "情境寫的未追蹤檔沒有被清掉"
+
+
+# 票 145 Station 3g 紅燈 #33(〈四十六〉46.4 第 4、5 點;規劃檔 docs/audits/2026-10-03-m1a-station3g-redlight-plan.md P5)。
+# 淨室的兩正三負由 `verify_gates.EVIDENCE_SCENARIOS` 列舉,比照 `SCENARIOS` 的「規則 ↔ 情境」對照。
+# **這一條只證明情境有接線,不證明情境結果** —— 結果由 4g 本機實跑 verify_gates 照錄(〈四十八〉48.1 第 7 點)。
+_EVIDENCE_SCENARIO_KEYS = {
+    "pos1-uninitialized",       # 正一:未初始化 ⇒ 框架測試全綠、authority 為 unknown
+    "pos2-initialized",         # 正二:已提交且相符的 policy ⇒ 紅 → 固定全套 → true → 合法退休
+    "neg1-mismatch",            # 負一:policy / environment 不符 ⇒ unknown
+    "neg2-worktree-differs",    # 負二:HEAD 有 policy、worktree 不同 ⇒ unknown
+    "neg3-worktree-only",       # 負三:worktree 有 policy、HEAD 沒有 ⇒ unknown
+}
+
+
+def test_every_evidence_policy_scenario_is_wired():
+    """#33。分類:behavior-red。
+
+    `verify_gates.EVIDENCE_SCENARIOS` 必須是 dict,鍵恰為兩正三負五個情境,值皆可呼叫。
+    BASELINE(560f618)上失敗的原因:`.claude/portable/verify_gates.py` 沒有 `EVIDENCE_SCENARIOS`(只有 `SCENARIOS`,`:225-235`)。
+    """
+    table = getattr(vg, "EVIDENCE_SCENARIOS", None)
+    assert isinstance(table, dict), "verify_gates 沒有 EVIDENCE_SCENARIOS:淨室的兩正三負沒有接線"
+    assert set(table) == _EVIDENCE_SCENARIO_KEYS, sorted(table)
+    assert all(callable(f) for f in table.values()), table
```
<!-- 逐字結束 -->

### E.5 `git diff 2737e02c64b88f4d0a39bdafbea2f3776993cf2b..83258dd9ab415a793eaf2b140a9e34c5b91069f2 -- <TEST_FILES>`(S3G1 → S3G1B)

用途:3g-1b —— 只應新增 9 支 behavior-red,不得改動 E.4 的 33 支。

<!-- 逐字開始 -->
```diff
diff --git a/tests/test_install.py b/tests/test_install.py
index 89a0794..37e9695 100644
--- a/tests/test_install.py
+++ b/tests/test_install.py
@@ -461,3 +461,208 @@ class TestGitignoreDedupIsLineExact:
         want = list(install_mod.GITIGNORE_FRAMEWORK) + list(install_mod.GITIGNORE_SECRETS)
         missing = [p for p in want if p not in got]
         assert not missing, "註解吃掉了 %d 條真防護行:%r" % (len(missing), missing)
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# 票 145 Station 3g-1b 紅燈 —— 安裝範本(〈四十八〉48.1 第 6 點;〈五十〉50.1)
+#
+# 合約:安裝器只在**非 canonical** 路徑 `.agents/evidence-policy.template.json` 寫範本(內容 = 框架能力邊界常數),
+# 並在 `docs/decisions-pending.md` 加 evidence policy 初始化的待決項;canonical `.agents/evidence-policy.json`
+# **只有人**放上去並 commit 才存在。
+# 下文 `<BASELINE>` = 7a15ea081da1bf23cc79e04aef76065438f65219(S3G2)。
+#
+# **呼叫真的 `install.main()`**,在 tmp 目錄裝一個新 repo(module 範圍只裝一次,三支共用)。
+# `install.main()` 會往 `sys.path` 插入目標 repo 的 hooks 目錄、從 `sys.modules` 移除 `gate`
+# (`.claude/portable/install.py:364-366`)—— fixture 先存再還原,不讓它漏到其他測試。
+# **不斷言範本「已提交」或「未提交」**(〈五十〉50.1 第 2 點:那不是本票裁決的需求)。
+# 本段 helper 全部新寫;既有 helper(`_load`)只呼叫、不修改。
+# ─────────────────────────────────────────────────────────────────────────────
+
+_G_POLICY_FILE = ".agents/evidence-policy.json"
+_G_TEMPLATE_FILE = ".agents/evidence-policy.template.json"
+_G_TEST_X = ("tests/test_x.py::test_a", "tests/test_x.py::test_b")
+
+
+@pytest.fixture(scope="module")
+def g3_installed_repo(tmp_path_factory):
+    """`install.main(<tmp>/repo)` 裝好的新 repo(真安裝)。回傳 repo 路徑(pathlib.Path)。"""
+    import sys
+    target = tmp_path_factory.mktemp("g3-install") / "repo"
+    mp = pytest.MonkeyPatch()
+    try:
+        mp.setattr(sys, "path", list(sys.path))
+        if "gate" in sys.modules:
+            mp.setitem(sys.modules, "gate", sys.modules["gate"])
+        mod = _load("install_for_g3_template", "install.py")
+        mod.main(str(target))
+    finally:
+        mp.undo()
+    return target
+
+
+def _g_load_from(path, name):
+    spec = importlib.util.spec_from_file_location(name, str(path))
+    m = importlib.util.module_from_spec(spec)
+    spec.loader.exec_module(m)
+    return m
+
+
+class _GInstallItem(pytest.Item):
+    """真的 `pytest.Item` 子類;只帶 nodeid(producer 以 isinstance 判斷)。"""
+
+    def runtest(self):
+        pass
+
+
+def _g_install_item(nodeid):
+    it = object.__new__(_GInstallItem)
+    it._nodeid = nodeid
+    it.name = nodeid.split("::")[-1]
+    return it
+
+
+class _GSys(object):
+    """conftest 所見的 `sys` 替身:版本固定為 3.11、`flags.optimize` 為 0,其他屬性轉給真的 `sys`。"""
+
+    def __init__(self):
+        import sys as real
+        import types
+        self._real = real
+        self.version_info = (3, 11, 0, "final", 0)
+        self.flags = types.SimpleNamespace(optimize=0)
+
+    def __getattr__(self, name):
+        return getattr(self._real, name)
+
+
+class _GPluginManager(object):
+    def __init__(self, name_plugins):
+        self._name_plugins = list(name_plugins)
+
+    def list_name_plugin(self):
+        return list(self._name_plugins)
+
+    def list_plugin_distinfo(self):
+        return []
+
+    def is_blocked(self, name):
+        return False
+
+    def get_plugin(self, name):
+        return dict(self._name_plugins).get(name)
+
+    def has_plugin(self, name):
+        return self.get_plugin(name) is not None
+
+
+def _g_drive_fixed_command(c, root):
+    """依 pytest 9.1.1 的呼叫順序驅動**安裝出來的** `tests/conftest.py`,模擬一次固定全套
+    `python -X utf8 -m pytest -q`:tests/test_x.py 的兩個身分全收集、全 passed、exit 0;
+    選項全部關閉、`override_ini == ["strict_markers=true"]`、`inipath` 為 `pyproject.toml`;
+    plugin 只有 `_pytest` 內建與 root conftest。"""
+    import types
+    files = {"tests/test_x.py": list(_G_TEST_X)}
+    for path, ids in sorted(files.items()):
+        report = types.SimpleNamespace(nodeid=path, result=[_g_install_item(n) for n in ids],
+                                       failed=False, passed=True, skipped=False, outcome="passed")
+        collector = types.SimpleNamespace(nodeid=path, path=root / path)
+        gen = c.pytest_make_collect_report(collector)
+        next(gen)
+        try:
+            gen.send(report)
+        except StopIteration:
+            pass
+        c.pytest_collectreport(report)
+    option_values = {"lf": False, "last_failed_no_failures": "all", "stepwise": False, "stepwise_skip": False,
+                     "maxfail": None, "collectonly": False, "setuponly": False, "setupplan": False,
+                     "runxfail": False, "pythonwarnings": None, "trace": False, "usepdb": False,
+                     "override_ini": ["strict_markers=true"], "inifilename": None, "pyargs": False}
+    option = types.SimpleNamespace(**option_values)
+    pm = _GPluginManager([("main", types.ModuleType("_pytest.main")),
+                          (os.path.join(str(root), "tests", "conftest.py"), c)])
+    config = types.SimpleNamespace(
+        args=["tests"], args_source=pytest.Config.ArgsSource.TESTPATHS, rootpath=root,
+        invocation_params=types.SimpleNamespace(args=("-q",), plugins=None, dir=root),
+        option=option, pluginmanager=pm, inipath=root / "pyproject.toml",
+        getoption=lambda name, default=None, skip=False: getattr(option, name, default))
+    selected = [n for ids in files.values() for n in ids]
+    session = types.SimpleNamespace(items=[_g_install_item(n) for n in selected],
+                                    testscollected=len(selected), config=config,
+                                    shouldstop=False, shouldfail=False)
+    c.pytest_collection_finish(session)
+    for nodeid in selected:
+        for when in ("setup", "call", "teardown"):
+            c.pytest_runtest_logreport(types.SimpleNamespace(
+                nodeid=nodeid, fspath=nodeid.split("::", 1)[0], when=when, outcome="passed",
+                passed=True, failed=False, skipped=False))
+    c.pytest_sessionfinish(session, 0)
+
+
+class TestEvidencePolicyTemplate:
+
+    def test_g3_install_writes_the_template_outside_the_canonical_path(self, g3_installed_repo, monkeypatch):
+        """I1(〈五十〉50.1 第 3 點)。分類:behavior-red。
+
+        `install.main(<tmp 新 repo>)` 之後:`.agents/evidence-policy.template.json` 存在;
+        `.agents/evidence-policy.json`(canonical)**不存在**。
+        再以安裝出來的**真實** producer(`tests/conftest.py`)與 consumer(`.claude/hooks/redlight.py`)驗證:
+        在該 repo 提交一份 `pyproject.toml`(與 install.main 自己的 commit 同樣以 `--no-verify` 提交,
+        `.claude/portable/install.py:520, :526`)後,模擬一次固定全套(版本事實固定為 3.11 / 9.1.1)——
+        session 合格且為 A,但 `file_coverage` 不得為 `"true"`:範本位於非 canonical path,
+        無論是否 tracked / committed,都不得成為 evidence authority。
+        BASELINE 上失敗的原因:`<BASELINE>:.claude/portable/install.py:497-530` 不寫任何範本。
+        """
+        import subprocess
+        root = g3_installed_repo
+        assert (root / _G_TEMPLATE_FILE).is_file(), "安裝器沒有寫 %s" % _G_TEMPLATE_FILE
+        assert not (root / _G_POLICY_FILE).exists(), "安裝器寫了 canonical policy —— 那等於自動信任"
+        with open(str(root / "pyproject.toml"), "w", encoding="utf-8", newline="\n") as f:
+            f.write(u'[tool.pytest.ini_options]\ntestpaths = ["tests"]\naddopts = "-ra --strict-markers"\n')
+        for args in (["add", "pyproject.toml"], ["commit", "-q", "--no-verify", "-m", "g3 pyproject"]):
+            subprocess.run(["git"] + args, cwd=str(root), capture_output=True, check=True)
+        c = _g_load_from(root / "tests" / "conftest.py", "conftest_in_installed_repo_g3")
+        assert c._redlight is not None, "安裝出來的 conftest 載不到 redlight"
+        monkeypatch.setattr(c, "sys", _GSys(), raising=False)
+        monkeypatch.setattr(pytest, "__version__", "9.1.1")
+        _g_drive_fixed_command(c, c._ROOT)
+        rl = _g_load_from(root / ".claude" / "hooks" / "redlight.py", "redlight_in_installed_repo_g3")
+        runs = rl.load_runs(str(c._ROOT))
+        assert runs, runs
+        run = runs[-1]
+        assert rl.validate_session(run) == [], run
+        assert rl.run_state(run) == "A", run
+        got = rl.file_coverage(run, "tests/test_x.py")
+        assert got != "true", got
+
+    def test_g3_the_template_lists_exactly_the_capability_boundary(self, g3_installed_repo):
+        """I2(〈五十〉50.1 第 3 點)。分類:behavior-red。
+
+        範本為 schema `"monkeyleash.evidence-policy"` v1;`python_versions` / `pytest_versions` / `dists`
+        分別等於安裝出來的 redlight 的框架能力邊界常數(`KNOWN_PYTHON_VERSIONS` / `KNOWN_PYTEST_VERSIONS` /
+        `KNOWN_DISTS`);`config_file` 屬 `FRAMEWORK_CONFIG_FILES`。常數以 getattr 取得,取不到 ⇒ 失敗。
+        BASELINE 上失敗的原因:沒有範本檔(`<BASELINE>:.claude/portable/install.py:497-530`)。
+        """
+        import json
+        root = g3_installed_repo
+        path = root / _G_TEMPLATE_FILE
+        assert path.is_file(), "安裝器沒有寫 %s" % _G_TEMPLATE_FILE
+        template = json.loads(path.read_text(encoding="utf-8"))
+        rl = _g_load_from(root / ".claude" / "hooks" / "redlight.py", "redlight_for_template_g3")
+        assert template.get("schema") == "monkeyleash.evidence-policy" and template.get("version") == 1, template
+        assert template.get("python_versions") == list(getattr(rl, "KNOWN_PYTHON_VERSIONS")), template
+        assert template.get("pytest_versions") == list(getattr(rl, "KNOWN_PYTEST_VERSIONS")), template
+        assert template.get("dists") == [list(d) for d in getattr(rl, "KNOWN_DISTS")], template
+        assert template.get("config_file") in getattr(rl, "FRAMEWORK_CONFIG_FILES"), template
+
+    def test_g3_decisions_pending_asks_to_initialize_the_policy(self, g3_installed_repo):
+        """I3(〈五十〉50.1 第 3 點)。分類:behavior-red。
+
+        `docs/decisions-pending.md` 含 evidence policy 初始化的待決項,且點名 canonical 路徑
+        `.agents/evidence-policy.json`。
+        BASELINE 上失敗的原因:`<BASELINE>:.claude/portable/install.py:386-422` 的待決項沒有 evidence policy。
+        """
+        path = g3_installed_repo / "docs" / "decisions-pending.md"
+        assert path.is_file(), "安裝器沒有寫 docs/decisions-pending.md"
+        body = path.read_text(encoding="utf-8")
+        assert "evidence policy" in body.lower(), body
+        assert _G_POLICY_FILE in body, body
diff --git a/tests/test_status.py b/tests/test_status.py
index 3d05029..bccda18 100644
--- a/tests/test_status.py
+++ b/tests/test_status.py
@@ -3015,3 +3015,120 @@ class TestEvidencePolicyChain:
         got = _lines_of(root)
         assert u"tests/test_x.py" in got[u"green"], got
         assert u"tests/test_x.py" not in got[u"red"], got
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 票 145 Station 3g-1b 紅燈 —— status 的 evidence policy 狀態行(〈四十八〉48.1 第 6 點;〈五十〉50.1)
+#
+# 合約:status 輸出恰有一行以 `evidence policy: ` 開頭,值依 policy 狀態為
+# 未初始化 / 未提交 / 工作樹與 HEAD 不同 / 格式不明 / 超出框架能力邊界 / 有效,
+# 並帶 `(source: .agents/evidence-policy.json)`。沒有這一行,「未初始化 ⇒ 永遠 unknown」對下游是靜默的。
+# 下文 `<BASELINE>` = 7a15ea081da1bf23cc79e04aef76065438f65219(S3G2)。
+#
+# 每一案都在**真的** git tmp repo(`_g_committed`)上佈置 policy 狀態,再呼叫 `render(root)`。
+# 本段 helper 全部新寫;既有 helper(`_root_with_redlight` / `_g_committed` / `_g_policy` / `_g_write` /
+# `_t_git` / `_lines` / `render`)只呼叫、不修改。
+# ═══════════════════════════════════════════════════════════════════════════
+
+_G_STATUS_PREFIX = u"evidence policy: "
+_G_STATUS_SOURCE = u"(source: .agents/evidence-policy.json)"
+
+_G_STATUS_EXPECTED = {
+    u"uninitialized": u"未初始化",
+    u"uncommitted": u"未提交",
+    u"worktree-differs": u"工作樹與 HEAD 不同",
+    u"unknown-schema": u"格式不明",
+    u"outside-boundary": u"超出框架能力邊界",
+    u"valid": u"有效",
+}
+
+
+def _g_policy_json(policy):
+    return json.dumps(policy, ensure_ascii=False, indent=2) + u"\n"
+
+
+def _g_without_key(policy, key):
+    out = dict(policy)
+    out.pop(key)
+    return out
+
+
+# [unknown-schema] 依序涵蓋的已提交文件:JSON malformed、schema 名稱不認得、version 不支援、
+# 必要欄位缺失、型別錯誤(後兩者同屬「必要欄位缺失 / 型別錯誤」一類,兩種都測)。
+_G_UNKNOWN_DOCUMENTS = [
+    (u"malformed-json", u"{not json\n"),
+    (u"unknown-schema-name", _g_policy_json(_g_policy(schema=u"other.evidence-policy"))),
+    (u"unsupported-version", _g_policy_json(_g_policy(version=2))),
+    (u"missing-field", _g_policy_json(_g_without_key(_g_policy(), u"dists"))),
+    (u"wrong-type", _g_policy_json(_g_policy(python_versions=u"3.11"))),
+]
+
+
+def _g_policy_status_line(root):
+    """`render(root)` 裡以 `evidence policy: ` 開頭的行;必須恰有一行。"""
+    out = render(root)
+    hits = [ln.strip() for ln in _lines(out) if ln.strip().startswith(_G_STATUS_PREFIX)]
+    assert len(hits) == 1, (hits, out)
+    return hits[0]
+
+
+def _g_assert_status(line, expected):
+    value = line[len(_G_STATUS_PREFIX):].split(u"(source:")[0].strip()
+    assert value.startswith(expected), (expected, line)
+    assert _G_STATUS_SOURCE in line, line
+
+
+def _g_status_root(base, state):
+    """在 `base` 底下造一個帶 redlight 的 tmp repo,佈置成 `state`;回傳 root。"""
+    root = _root_with_redlight(base)
+    if state == u"uninitialized":
+        _g_committed(root)
+    elif state == u"uncommitted":
+        _g_committed(root, policy=_g_policy(), commit_policy=False)
+    elif state == u"worktree-differs":
+        _g_committed(root, policy=_g_policy())
+        _g_write(root, _G_POLICY_FILE, _g_policy_json(_g_policy()) + u"\n")
+    elif state == u"outside-boundary":
+        _g_committed(root, policy=_g_policy(python_versions=[u"3.11", u"3.12"]))
+    elif state == u"valid":
+        _g_committed(root, policy=_g_policy())
+    else:
+        raise ValueError(state)
+    return root
+
+
+def _g_committed_raw_policy(base, text):
+    """已提交設定與 conftest 的 repo,再把 `text`(原樣)提交為 canonical policy。"""
+    root = _root_with_redlight(base)
+    _g_committed(root)
+    _g_write(root, _G_POLICY_FILE, text)
+    _t_git(root, "add", _G_POLICY_FILE)
+    _t_git(root, "commit", "-q", "-m", "policy")
+    return root
+
+
+class TestEvidencePolicyStatusLine:
+
+    @pytest.mark.parametrize("state", list(_G_STATUS_EXPECTED))
+    def test_g3_status_shows_the_policy_state(self, tmp_path, state):
+        """〈五十〉50.1 第 3 點(status 的 policy 狀態行)。分類:behavior-red。
+
+        - `[uninitialized]`:repo 從未有 policy ⇒ `未初始化`;
+        - `[uncommitted]`:合法 policy 只在工作樹 ⇒ `未提交`;
+        - `[worktree-differs]`:HEAD 有合法 policy,工作樹內容不同 ⇒ `工作樹與 HEAD 不同`;
+        - `[unknown-schema]`:依序五份**已提交**文件(JSON malformed、schema 名稱不認得、version 2、
+          缺 `dists`、`python_versions` 為字串),**逐一**斷言 ⇒ 都是 `格式不明`;
+        - `[outside-boundary]`:已提交 policy 的 `python_versions` 含 3.12(框架能力邊界外)⇒ `超出框架能力邊界`;
+        - `[valid]`:已提交合法 policy、工作樹 = HEAD ⇒ `有效`。
+        每一案的那一行都須帶 `(source: .agents/evidence-policy.json)`。
+        BASELINE 上失敗的原因:`<BASELINE>:.claude/portable/status.py` 沒有 `evidence policy:` 這一行
+        (`_g_policy_status_line` 的「恰有一行」斷言)。
+        """
+        expected = _G_STATUS_EXPECTED[state]
+        if state == u"unknown-schema":
+            for name, text in _G_UNKNOWN_DOCUMENTS:
+                root = _g_committed_raw_policy(tmp_path / name, text)
+                _g_assert_status(_g_policy_status_line(root), expected)
+            return
+        root = _g_status_root(tmp_path, state)
+        _g_assert_status(_g_policy_status_line(root), expected)
```
<!-- 逐字結束 -->

---

## F. 證據(逐字)

出處一律為 REVIEW_HEAD(`b5db3734f6795d8a371e4f58b172e0a8ffb066eb`)。

### F.0 T1 / T2 紅綠定位表(非逐字;每格附 F.1 出處行號)

F.1 的行號 = `b5db3734f6795d8a371e4f58b172e0a8ffb066eb:docs/audits/2026-10-04-m1a-station4g-fix.md` 的行號(本包 F.1 逐字段與之逐行對應)。

| 測試 | S4G1B 上的固定全套 | S4G1C(TARGET)上的固定全套 |
|---|---|---|
| T1 `tests/test_redlight.py::TestEvidencePolicyNoOverride::test_g3_no_override_anywhere_is_full_coverage`(behavior-red;F.1 第 144 行) | **failed**:F.1 第 156 行 `tests\test_redlight.py:2520: AssertionError`、第 157 行 `FAILED …test_g3_no_override_anywhere_is_full_coverage`、第 158 行摘要 `1 failed, 2093 passed, 3 skipped, 3 xfailed`;第 161 行「唯一的 FAILED 是 T1」 | **passed**:F.1 第 270 行摘要 `2094 passed, 3 skipped, 3 xfailed`(0 failed) |
| T2 `tests/test_redlight.py::TestEvidencePolicyNoOverride::test_g3_a_missing_override_fact_is_not_full_coverage`(regression-lock;F.1 第 145 行) | **passed**:F.1 第 161 行「T2 在 2093 passed 之內」;第 157 行的 FAILED 清單只有 T1 | **passed**:F.1 第 270 行摘要 `2094 passed, 3 skipped, 3 xfailed`(0 failed) |

### F.1 `docs/audits/2026-10-04-m1a-station4g-fix.md` 全文

行號來源:REVIEW_HEAD 的該檔第 1–416 行

<!-- 逐字開始 -->
# 票 145 Station 4g —— host evidence policy 修正與本機驗收

- 日期:2026-10-04
- 對象:
  - S4G1 `f4fa0418aa037f95ef7d1f59c6fe6a812a80414c`:實作;
  - S4G1B `f581a02a5b7a65c8eaf150bf7231acc464f99072`:補紅燈 T1 / T2;
  - S4G1C `8e7775526e462d984abb0992ed74c1e1aa3648dd`:producer 修正(修法 B)。
  - 上一個 commit 是 S3G1B-2 `3eb112b1cafb399f2757274264281436729e7e42`。
- 合約:
  - 票 145〈四十八〉48.1 裁決 1–7、〈五十〉50.1;
  - 4g 續作裁決:R3 擋下後的還原與編輯規矩、第 7 鍵 `committed_addopts` 與 `addopts_overrides` 輸入合約、修法 B 與 T1 / T2;
  - 規劃檔 `docs/audits/2026-10-03-m1a-station3g-redlight-plan.md` P3 / P4 / P5 / P6。
- 範圍:**本機(Windows)驗收**。POSIX 外部 clean-room 驗收尚未執行(第 9 節)。**本報告不宣稱 4g 完成。**（S4G4 b127ae016ce6a7a7d096742e5771f1e6d328f52a 後更新：POSIX 外部 clean-room 驗收已 PASS，見第 9 節；Station 4g = PASS / COMPLETED。）

## 【給裁決者】

1. 「哪些測試結果能當退紅證據」原本寫死成 agent-gates 自己的設定。現在改成每個 repo 自己提交一份 policy,框架只檢查它有沒有超出框架驗證過的範圍。
2. 本機全套 2094 passed、0 failed。原本的 35 支紅加上補的 1 支紅全部轉綠。status 顯示 policy 有效,票 145 底下沒有紅。
3. 淨室(全新安裝的乾淨 repo)第一次驗收時「正二」失敗:沒有 `-o` 類旗標的 repo 退不了紅。依裁決改在記錄端分清「沒有」與「取不到」之後,同一次淨室執行裡兩正三負全部成立。
4. 本 repo 的測試帳本只往後加,淨室驗收前後完全沒動。
5. 下一步是 POSIX 外部淨室驗收(由裁決助手執行)。通過後才升級狀態。（S4G4 後更新：POSIX 外部 clean-room 驗收已執行並 PASS，狀態已升級，見第 9 節。）

## 【給裁決助手】

### 1. 實作摘要(行號以 S4G1 為準;`tests/conftest.py` 以 S4G1C 為準)

**`.claude/hooks/redlight.py`**(S4G1 之後未再修改)

| 位置 | 內容 |
|---|---|
| `:493` `FRAMEWORK_CONFIG_FILES = ("pyproject.toml",)` | B 常數;取代 `CONFIG_FILE` |
| `:497` `BLOB_FILES` | producer 記 blob 的檔 = `FRAMEWORK_CONFIG_FILES + (ROOT_CONFTEST,)`;取代 `COMMITTED_FILES` |
| `:506`–`:507` `POLICY_FILE` / `POLICY_SCHEMAS` | I-1 / I-2 |
| `:512` `EVIDENCE_POLICY_KEYS` | 7 鍵(續作裁決 3) |
| `:524` `OVERRIDE_FLAGS` | 推導規則的旗標表(pytest 9.1.1) |
| `:715` `_git_bytes` | git 原始 stdout |
| `:726` `committed_blobs` | 逐路徑各一次 git(缺一檔不連坐) |
| `:749` `addopts_overrides(value)` | 只接受 `str` / `list[str]`;不讀 git / 檔案;推導不了 ⇒ None |
| `:791` `_committed_addopts` | `git cat-file blob HEAD:<config_file>` → `tomllib` → `[tool.pytest.ini_options].addopts` 原值。`""` = 段落在、沒有 addopts;None = 取得或解析失敗 |
| `:825` `evidence_policy_facts` | I-3 六步,只擷取事實,回傳 7 鍵 |
| `:874` `policy_document_problems` | (格式, 邊界);schema 不認得就不往下看;界外 ⇒ 整份不合格 |
| `:912` `policy_state` | status 行的六種狀態 |
| `:932` `policy_template` | 範本 = B 常數完整列舉;`committed_overrides: []` |
| `:945` `_effective_policy` | identity、格式、邊界、schema / version 一致、`committed_overrides == addopts_overrides(committed_addopts)`(`committed_addopts` 為 None ⇒ unknown) |
| `:972` / `:977` | `_effective`(B ∩ policy)、`_known_dists_accepted` |
| `:987` `_completeness_problems` | config_blobs 改驗 `ROOT_CONFTEST` 必在;`:1026` 新增 evidence_policy 7 鍵型別檢查 |
| `:1043` `_completeness_verdict` | `:1074` `policy = _effective_policy(...)`;(vii′)(xiii)(viii)(x)(xi)(xviii) 改為對 effective 判定;唯一的 `return "true"` 仍在 `:1127` |

- 刪除:`COMMITTED_ADDOPTS_OVERRIDES`、`CONFIG_FILE`、`COMMITTED_FILES`。
- `content_hash` 及其呼叫的函式未修改。

**`tests/conftest.py`**
- `:346` `_MISSING`、`:349` `_override_ini_of`(S4G1C;修法 B):先判屬性是否存在,再解讀值,只讀一次。
- `:406` `override_ini` 改經 `_override_ini_of`。
- `:411` `completeness["evidence_policy"]`(S4G1):舊版 redlight 沒有該函式 ⇒ None。

**`.claude/portable/status.py`**:`:560` `POLICY_SOURCE`、`:563` `_policy_line`、`:867` Evidence 區在 test-runs 行之後輸出 `evidence policy: <狀態>  (source: .agents/evidence-policy.json)`。

**`.claude/portable/install.py`**:
- `:386` `POLICY_TEMPLATE`、`:389` `_target_redlight`;
- `:399` `write_policy_template`:由目標 repo 的 `redlight.policy_template()` 產生,不另放範本來源檔;
- `:415` `write_decisions_pending(..., policy_file=None)`:一律加「evidence policy 未初始化」待決項,含 canonical 路徑;
- `:555` / `:572` 接線。

**`.claude/portable/verify_gates.py`**:
- `:286`–`:476` 新增:探針、正二的 policy(= 當下環境 ∩ B)、`_ev_red_then_green`、五個情境函式、`EVIDENCE_SCENARIOS`(`:446`)、`_ev_restore`、`run_evidence_scenarios`;
- `:613` 接在「框架測試在新 repo 跑一次」之後;每個情境各印一行,失敗訊息點名情境。

**`.agents/evidence-policy.json`**:= 規劃檔 P3 甲案範例(`config_file` `pyproject.toml`、`committed_overrides` `["strict_markers=true"]`、`python_versions` `["3.11"]`、`pytest_versions` `["9.1.1"]`、`dists` `[["anyio","4.15.0"]]`)。本 repo `HEAD:pyproject.toml` 的 `addopts = "-ra --strict-markers"` 推導值相同,步驟 F 的停手條件不成立。

**`.agents/portable-manifest.txt`**:`:106` `.agents/evidence-policy.json skip`、`:124` `.agents/evidence-policy.template.json generate`。

### 2. 授權改動對照(assertion / docstring / test identity 一律不改)

| 授權 | 位置(S4G1) | 內容 |
|---|---|---|
| G1 | `tests/test_redlight.py` `_D_POLICY_FILE` / `_D_BASELINE_POLICY`、`_d_committed_root`;`tests/test_status.py` `_T_POLICY_FILE` / `_T_BASELINE_POLICY` / `_T_BASELINE_ADDOPTS`、`_t_committed` | 寫入並提交與 baseline 相符的 policy |
| G2 | `tests/test_status.py` 兩支 completeness dict(`TestTestsUnderTicketUsesTheLatestRecordPerFile::test_a_file_that_went_red_then_green_counts_as_green`、`TestOrphans::test_a_renamed_red_test_is_orphaned_not_green`)+ helper `_t_policy_facts` | 只補 `evidence_policy`(含第 7 鍵) |
| G3 | `tests/test_redlight.py` `_isolated_conftest`;`tests/test_status.py` `_chain_conftest` | 固定 conftest 所見的 `sys.version_info` 為 3.11、`pytest.__version__` 為 9.1.1。測試在呼叫 driver 前自己設過 pytest 版本時不覆蓋(以模組載入時的真實版本判斷) |
| G4 | `tests/test_redlight.py` | 刪除 `TestCollectionDefinitionCoverage::test_d4_the_committed_addopts_override_constant_matches_pyproject` |
| G5 | `.agents/portable-manifest.txt` | 見第 1 節;`tests/test_host_evidence_policy.py skip` 已在 S3G1 加過,未重複 |

- 3g / 3g-1b 的 35 支與 `tests/test_host_evidence_policy.py` 一字未改。
- S4G1 的 `git diff --cached -- tests/` 全文可由 `git show f4fa041 -- tests/` 重現。

### 3. 第一次淨室驗收(S4G1)—— 正二不成立

`python .claude/portable/verify_gates.py <session scratch>/verify-gates`,exit 1。情境段原文:

```
=== 框架自己的測試,在這個新 repo 裡跑一次 ===
    1942 passed, 7 skipped, 3 xfailed in 399.28s (0:06:39)

=== evidence policy 淨室情境(兩正三負;每個情境各一行)===
    正一 未初始化                  成立 ✓  35 個框架測試檔皆 unknown=True;evidence policy: 未初始化
    正二 已初始化且相符               不成立 ✗  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 有效;1 passed in 26.91s
    負一 policy / 環境不符         成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 有效;1 passed in 0.34s
    負二 HEAD 有、工作樹不同          成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 工作樹與 HEAD 不同;1 passed in 0.30s
    負三 工作樹有、HEAD 沒有          成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 未提交;1 passed in 0.23s
```

- 同一輪的本機全套(S4G1):`2092 passed, 3 skipped, 3 xfailed in 392.31s (0:06:32)`。
- 本次負一到負三的「成立」**不作為證據**:成因相同,機制正確與否它們都會是 unknown。
- 細節見 `.dev/reports/2026-10-04T213043Z-ticket145-station4g-s4g1-local-pass-cleanroom-pos2-fail.md`。

**成因**:
- pytest 9.1.1 的 `-o` 是 `action="append"`,沒有 default(`_pytest/helpconfig.py:112-119`)。沒給任何 `-o` / OverrideIniAction 旗標時,`config.option.override_ini` 為 **None**。
- S4G1 的 producer 把 None 原樣交給 `normalize_overrides`,落帳 `null`。
- consumer (viii) 比 `None != []` ⇒ unknown。
- 本 repo 與 3g / 3g-1b 的正控都帶 `--strict-markers`,沒有一支走到這條路徑。

**裁決(Jeff)**:
- 修法 B = APPROVED:producer 先判欄位是否存在,再解讀值。
- A = REJECTED:在 consumer 把 None 當 [],等於丟掉 None 的來源資訊,會把「事實取不到」當成「確定沒有 override」⇒ fail-open。
- C = REJECTED:只是繞過缺陷。
- 授權新增 T1 + T2。負一到負三須在正二修好後的同一次淨室執行中重新驗證。

**裁決助手外部驗證**(Linux,Python 3.11 + pytest 9.1.1;隔離環境;**來源:Jeff 的 4g 續作指令;非本 repo 帳本證據、非獨立審查 finding**):
- pytest 9.1.1 不帶 `-o` 時 `config.option.override_ini` 為 None、屬性存在;帶 `-o xfail_strict=true` 時為 `['xfail_strict=true']`。
- 以 S4G1 的樹跑 verify_gates.py:正二不成立(`file_coverage=unknown`),與 Windows 一致。
- 套用 B 後跑 verify_gates.py:兩正三負全部成立,正二 `file_coverage=true`;test_redlight / test_status / test_install / test_verify_gates / test_host_evidence_policy 共 275 支全過。
- 原型測試:T1 在 S4G1 失敗、在 B 通過;T2 在 S4G1 與 B 都通過、在 A 失敗。

### 4. S4G1B 補紅燈

```
$ python -X utf8 -m py_compile tests/test_redlight.py
(無輸出)
$ git diff --cached --name-only
tests/test_redlight.py
$ git diff --cached --check
(無輸出)
$ git diff --cached -U0 -- tests/test_redlight.py   → 恰一個 hunk,只有 + 行
@@ -2492,0 +2493,42 @@ class TestAddoptsDerivation:
$ git commit -F .scratch/m1a-s4g/s4g-1b-msg.txt
[master f581a02] test(145): M1-a Station 4g-1b —— 「沒有任何 override」正控與「override 事實取不到」鎖(2 支)
 1 file changed, 42 insertions(+)
$ git rev-parse HEAD
f581a02a5b7a65c8eaf150bf7231acc464f99072
$ git status --porcelain
(無輸出)
```

- `TestEvidencePolicyNoOverride::test_g3_no_override_anywhere_is_full_coverage`(T1,behavior-red):addopts `-ra`、policy `committed_overrides: []`、`override_ini=None` ⇒ 必須 `"true"`。
- `TestEvidencePolicyNoOverride::test_g3_a_missing_override_fact_is_not_full_coverage`(T2,regression-lock):`override_ini` 屬性不存在 ⇒ 不得為 `"true"`。

**紅燈全套(S4G1B 上只跑一次)**:`python -X utf8 -m pytest -q > <session scratch>/s4g1b-run.txt 2>&1`,exit 1;之後 `git status --porcelain` 無輸出。照錄時第三行 `E` 的行尾空白已去除。

```
E       AssertionError: unknown
E       assert 'unknown' == 'true'
E
E         - true
E         + unknown

tests\test_redlight.py:2520: AssertionError
FAILED tests/test_redlight.py::TestEvidencePolicyNoOverride::test_g3_no_override_anywhere_is_full_coverage
1 failed, 2093 passed, 3 skipped, 3 xfailed in 342.54s (0:05:42)
```

- collected 2100。唯一的 FAILED 是 T1;T2 在 2093 passed 之內。

帳本(各自單獨執行):

```
$ head -c 787812 .dev/test-runs.jsonl > <session scratch>/r13.bin
$ head -c 10696010 .dev/test-sessions.jsonl > <session scratch>/s13.bin
$ sha256sum <session scratch>/r13.bin
d2cb491719cb9ec3c694b9ead332d08b41c8b5676603baebf42d126e627dc9f2 *<session scratch>/r13.bin
$ sha256sum <session scratch>/s13.bin
e593a945fc4dce41a7f4c0ae77d919e0c37c22da1f0c94cc3ed0561de4e6fa11 *<session scratch>/s13.bin
$ wc -l .dev/test-runs.jsonl
2968 .dev/test-runs.jsonl
$ wc -l .dev/test-sessions.jsonl
26 .dev/test-sessions.jsonl
$ wc -c .dev/test-runs.jsonl
799406 .dev/test-runs.jsonl
$ wc -c .dev/test-sessions.jsonl
11433570 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl
ab5070782e058c19090a82f139a717853f6fb1d07104e13cc7ff2a73c1d71bba *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
14fbbfb3ded7af07da0eac68c0b41a481c39ffd3f6d20c405658e12860de339d *.dev/test-sessions.jsonl
```

- 前段 sha256 = B13 ⇒ 只追加。
- test-runs 2921 → 2968(+47 行)、test-sessions 25 → 26(+1 行)。
- 跑後全檔記為 B14(799406 / 11433570;`ab507078…` / `14fbbfb3…`)。

### 5. S4G1C 修正

```
$ python -X utf8 -m py_compile tests/conftest.py
(無輸出)
$ git diff --cached --name-only
tests/conftest.py
$ git diff --cached --check
(無輸出)
$ git commit -F .scratch/m1a-s4g/s4g-1c-msg.txt
[master 8e77755] fix(145): M1-a Station 4g-1c —— producer 區分「沒有 -o」與「override 事實取不到」(修法 B)
 1 file changed, 22 insertions(+), 2 deletions(-)
$ git rev-parse HEAD
8e7775526e462d984abb0992ed74c1e1aa3648dd
$ git status --porcelain
(無輸出)
```

`git diff --cached` 全文(照錄時去除了行尾空白,以通過 `git diff --cached --check`:diff 的空白 context 行原為單一空格。原文可由 `git show 8e77755` 重現):

```
diff --git a/tests/conftest.py b/tests/conftest.py
index 64d5dd0..565deb3 100644
--- a/tests/conftest.py
+++ b/tests/conftest.py
@@ -342,6 +342,25 @@ def _flag(session, name):
     return bool(getattr(session, name))


+# 「屬性不存在」的 sentinel(票 145 Station 4g 修法 B):與「屬性存在、值為 None」分開。
+_MISSING = object()
+
+
+def _override_ini_of(option):
+    """交給 `normalize_overrides` 的 `override_ini` 原值。**先判欄位是否存在,再解讀值;只讀一次。**
+
+    pytest 9.1.1 的 `-o` 為 `action="append"`、沒有 default(`_pytest/helpconfig.py:112-119`),
+    未給任何 `-o` / OverrideIniAction 旗標時值為 None —— 語意是「沒有 override」,與「屬性取不到」不同:
+      - 屬性不存在 ⇒ None(事實取不到;consumer 判 unknown);
+      - 值為 None ⇒ 以 `[]` 交給 `normalize_overrides`,落帳 `[]`(事實取得成功:pytest 明確表示沒有 -o);
+      - 其他 ⇒ `normalize_overrides` 照舊(非 list ⇒ None)。
+    """
+    raw = getattr(option, "override_ini", _MISSING)
+    if raw is _MISSING:
+        return None
+    return raw if raw is not None else []
+
+
 def _completeness_of(session):
     """本次 session 的完整性事實。任何一步出錯 ⇒ None(寧可多紅,不讓 pytest 失敗)。

@@ -351,6 +370,8 @@ def _completeness_of(session):
     pyproject.toml 與本檔的工作樹 blob vs HEAD blob(git 子程序,失敗 ⇒ None);`pytest_version`
     取自本檔 import 的 `pytest`;`blocked` 是 `list_name_plugin()` 中值為 None 的名稱(`-p no:`)。
     路徑型事實一律轉成 root 相對路徑,不落帳絕對路徑。
+    `override_ini` 先判屬性是否存在(`_override_ini_of`):pytest 9.1.1 的 -o 為 action="append" 無 default,
+    未給時為 None,語意是「沒有 override」(落帳 `[]`),與「屬性取不到」(落帳 None ⇒ unknown)不同。

     票 145 Station 4e(〈三十五〉3 (xiv)–(xviii)、4)另記 pass 有效性的事實:`optimize` 與 `python_version`
     在此刻經模組層 `sys` 讀;`runxfail` / `pythonwarnings` / `trace` 隨 `COMPLETENESS_OPTIONS` 記在 `options`。
@@ -382,8 +403,7 @@ def _completeness_of(session):
             "plugins": _redlight.classify_plugins(_ROOT, name_plugins,
                                                   pm.list_plugin_distinfo()),
             "blocked": _redlight.blocked_plugins(name_plugins, _ROOT),
-            "override_ini": _redlight.normalize_overrides(getattr(option, "override_ini", None),
-                                                          _ROOT, inv_dir),
+            "override_ini": _redlight.normalize_overrides(_override_ini_of(option), _ROOT, inv_dir),
             "inifilename": _redlight.normalize_config_path(getattr(option, "inifilename", None),
                                                            _ROOT, inv_dir),
             "inipath": _redlight.normalize_config_path(getattr(cfg, "inipath", None), _ROOT),
```

- `redlight.py` 未改:consumer (viii) 維持 None ⇒ unknown。`normalize_overrides` 未改。
- 既有 option 替身(`_C_OPTION_DEFAULTS`、`_S_OPTION_DEFAULTS`)都沒有明寫 `override_ini=None`。缺屬性時仍落帳 None,行為不變。

### 6. S4G2 本機驗收(S4G1C 上)

**5a 固定全套(只跑一次)**:`python -X utf8 -m pytest -q > <session scratch>/s4g-run2.txt 2>&1`,exit 0;之後 `git status --porcelain` 無輸出。

```
2094 passed, 3 skipped, 3 xfailed in 341.79s (0:05:41)
```

- collected 2100(2094 + 3 + 3)。0 failed。輸出沒有任何 `FAILED` / `ERROR` 行。

**5b 帳本(以 B14 為前段基準;各自單獨執行)**

```
$ head -c 799406 .dev/test-runs.jsonl > <session scratch>/r14.bin
$ head -c 11433570 .dev/test-sessions.jsonl > <session scratch>/s14.bin
$ sha256sum <session scratch>/r14.bin
ab5070782e058c19090a82f139a717853f6fb1d07104e13cc7ff2a73c1d71bba *<session scratch>/r14.bin
$ sha256sum <session scratch>/s14.bin
14fbbfb3ded7af07da0eac68c0b41a481c39ffd3f6d20c405658e12860de339d *<session scratch>/s14.bin
$ wc -l .dev/test-runs.jsonl
3015 .dev/test-runs.jsonl
$ wc -l .dev/test-sessions.jsonl
27 .dev/test-sessions.jsonl
```

- 前段 sha256 = B14 ⇒ 只追加。
- test-runs 2968 → 3015(+47 行;47 個測試檔各一行)、test-sessions 26 → 27(+1 行)。

**5c status(節錄原文)**

```
test-runs: 本票 red 0 / green 47 / run 事實未知 0 / orphaned 0 / schema 不合格 run 0;最後一筆 tests/test_verify_gates.py=green @ 2026-10-04T22:04:53.003363+00:00;最近一次 run:A(exit 0;collected 2100 / deselected 0 / passed 2094 / failed 0 / skipped 3)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl)
evidence policy: 有效  (source: .agents/evidence-policy.json)
tests red under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests green (run 事實未知) under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests orphaned under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
```

- 原本的 5 個紅檔都在 green:`tests/test_host_evidence_policy.py`、`tests/test_install.py`、`tests/test_redlight.py`、`tests/test_status.py`、`tests/test_verify_gates.py`。

**5d 淨室**

V0(各自單獨執行):

```
$ wc -c .dev/test-runs.jsonl
810925 .dev/test-runs.jsonl
$ wc -c .dev/test-sessions.jsonl
12171130 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl
9fa98cc71426865862deebbfcefcd78c49503251e6f20aca928656bb3ac93426 *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
27cccd2c1a1506f96d2628c608487ccd394af1da2280ebdc983aa02c6645198b *.dev/test-sessions.jsonl
```

`python .claude/portable/verify_gates.py <session scratch>/verify-gates2 > <session scratch>/s4g-verify2.txt 2>&1`,exit 0。末段原文:

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
    1944 passed, 7 skipped, 3 xfailed in 327.25s (0:05:27)

=== evidence policy 淨室情境(兩正三負;每個情境各一行)===
    正一 未初始化                  成立 ✓  35 個框架測試檔皆 unknown=True;evidence policy: 未初始化
    正二 已初始化且相符               成立 ✓  rc 1→0;file_coverage=true;red=(無);green=tests/test_evidence_probe.py;evidence policy: 有效;1 passed in 17.36s
    負一 policy / 環境不符         成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 有效;1 passed in 0.32s
    負二 HEAD 有、工作樹不同          成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 工作樹與 HEAD 不同;1 passed in 0.24s
    負三 工作樹有、HEAD 沒有          成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 未提交;1 passed in 0.21s

全部 9 條規則各擋下一次,權威層偵測正常,框架測試在新 repo 全綠,evidence policy 兩正三負成立。
安裝位置:<session scratch>/verify-gates2/verify-gates-repo
```

- 五情境在**同一次**淨室執行中全部成立。
- 正二含 `file_coverage=true` 與 `green=tests/test_evidence_probe.py`。
- 負一到負三是在正二成立的同一次執行中得到的。

事後(各自單獨執行):

```
$ wc -c .dev/test-runs.jsonl
810925 .dev/test-runs.jsonl
$ wc -c .dev/test-sessions.jsonl
12171130 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl
9fa98cc71426865862deebbfcefcd78c49503251e6f20aca928656bb3ac93426 *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
27cccd2c1a1506f96d2628c608487ccd394af1da2280ebdc983aa02c6645198b *.dev/test-sessions.jsonl
$ git status --porcelain
(無輸出)
```

⇒ 本 repo 兩本帳本前後 bytes 與 sha256 都等於 V0。

### 7. 程序紀錄

- R3 擋下與還原:S4G1 之前,第一次嘗試在 redlight.py 半改狀態被前哨 R3 擋下(`.dev/reports/2026-10-04T205524Z-ticket145-station4g-blocked-r3-self-import.md`)。依裁決以 `git restore` 丟棄半成品後重做。
- 重做採漸進遷移:新增 → 改引用 → 刪舊,每刀後以 `python .claude/portable/status.py --root .` 為 import 探針。
  - **違規**:3a–3c 三次寫入後沒有立刻探針。裁決已記錄並接受,本輪(S4G1B / S4G1C)沒有再寫 redlight.py。
- 淨室 `.dev/` 在目標 repo 是被追蹤的。證據情境之間以 `git reset --hard <基準>` 還原,所以單一情境的 session 不留存。結果只以每個情境當場印出的那一行為準。

### 8. 殘餘與未證明(依規劃檔 P7 與 4g 續作裁決;不擴張)

1. **閘門依賴 redlight.py 可 import**:`gate.head_content_hash` 經 `_redlight()` 載入工作樹的 redlight.py。半改狀態載不起來時,全部 R3 判定都會被擋。屬 fail-closed、照設計,不在本票修。
2. **status 的 `evidence policy: 有效` 只代表 policy 文件本身有效**:已提交、工作樹 = HEAD、schema / version 認得、在能力邊界內。它不代表本次 runtime 一定能取得 true authority。`committed_overrides` 與 HEAD addopts 推導是否一致,只在 verdict 時判定,status 行不檢查。屬追蹤項,**目前尚未 machine-enforced**。
3. **淨室負一到負三只斷言 unknown,不斷言 unknown 的成因**(追蹤項)。
4. **verify_gates 的 `SystemExit` 訊息**在 cp950 主控台重導向時為亂碼(既有行為)。
5. 規劃檔 P7 照舊、本票不處理:
   - 下游測試不在 `tests/` 底下時 producer 不載入;
   - 「無設定檔」不在能力邊界內;
   - 「人審」無法機器驗證;
   - sync 端沒有「需建立 evidence policy」提示;
   - logging 鎖步絆線(〈四十五〉45.3)**目前尚未 machine-enforced**,實作時須放進宿主專用檔;
   - `tests/test_leak_scan.py` 的宿主樹掃描在下游的意義;
   - 機器化 pre-push;
   - TOCTOU 與未 pin 版本;policy 改了但未 commit 的期間無法退紅。
6. **G3 的殘餘**:driver 固定的是 `_isolated_conftest` / `_chain_conftest` 預設所見的版本。測試事後以 `_e_sys(version_info=None)` 換掉 `sys` 的那些(例:3e 的 optimize 對照組),仍讀真實 Python 版本。在 3.11 以外的直譯器上,它們的正控是否仍綠:**未證明**。
7. **`addopts_overrides` 推導不了的寫法**(合併短旗標 `-qo x`、長旗標縮寫):方向是 unknown(fail-closed),不是假綠。
8. **本機只驗 Windows**。POSIX 的淨室結果目前只有裁決助手的原型驗證(第 3 節),不是本樹的實測。（S4G4 後更新：POSIX 已於本樹內容實測——裁決助手於隔離 Linux 環境以 S4G3 時點的 12 個程式 / 測試 / 設定檔跑 verify_gates 與宿主全套，見第 9 節；屬外部驗證，非本 repo 帳本證據。）

### 9. POSIX 外部 clean-room 驗收

> **舊文字(F-036,保留不刪)**:本節標題原為 ~~`### 9. POSIX 外部 clean-room 驗收:待執行(裁決助手)`~~,沒有內文。
> 2026-10-04 S4G4 依 Jeff 裁決改為下方照錄段落。

POSIX 外部 clean-room 驗收（裁決助手；隔離環境；非本 repo 帳本證據）——2026-10-04 約 18:50 ET
- 環境：Linux，Python 3.11.16，pytest 9.1.1，anyio 4.15.0。
- 受測樹：以公開 repo de36ebcbab284ef11064a9943b5191750482dd93 的 clone 為底，覆蓋 Windows 工作樹於 S4G3 時點的 12 個程式 / 測試 / 設定檔（.claude/hooks/redlight.py、.claude/portable/install.py、.claude/portable/status.py、.claude/portable/verify_gates.py、tests/conftest.py、tests/test_redlight.py、tests/test_status.py、tests/test_install.py、tests/test_verify_gates.py、tests/test_host_evidence_policy.py、.agents/portable-manifest.txt、.agents/evidence-policy.json；CRLF→LF）。docs 未同步（不影響程式行為）。
- verify_gates.py：R1–R9 各擋下一次；權威層偵測三項成立；淨室框架測試 1945 passed、4 skipped、3 xfailed、0 failed；evidence policy 兩正三負全部成立：
    正一 未初始化 成立（35 個框架測試檔皆 unknown；evidence policy: 未初始化）
    正二 已初始化且相符 成立（rc 1→0；file_coverage=true；green=tests/test_evidence_probe.py；evidence policy: 有效）
    負一 policy / 環境不符 成立（file_coverage=unknown；紅仍在）
    負二 HEAD 有、工作樹不同 成立（file_coverage=unknown；evidence policy: 工作樹與 HEAD 不同）
    負三 工作樹有、HEAD 沒有 成立（file_coverage=unknown；evidence policy: 未提交）
- 宿主固定全套（Linux）：collected 2100；2084 passed、13 failed、3 xfailed。13 支為 tests/test_gate.py::TestAuthorityLayerIsWired::test_this_repo_itself_is_wired 與 tests/test_known_items_regression.py 的 12 支；同一沙盒在 4g 之前的已推送版本 de36ebc 上同樣恰為這 13 支失敗 ⇒ 屬沙盒環境因素（推測：clone 未設 hooksPath、缺本機私有資料），與 4g 無關。evidence 相關 5 檔（test_redlight / test_status / test_install / test_verify_gates / test_host_evidence_policy）全過。
- 先前的 S4G1 Linux 重現（正二不成立、成因 override_ini 為 None）與修法 B 原型驗證，見〈五十一〉51.1 / 證據報告。
- 結論：POSIX 外部 clean-room 驗收 PASS。
<!-- 逐字結束 -->

### F.2 `docs/audits/2026-10-04-m1a-station3g-1b-redlight.md` 第 4 節(固定全套與 FAILED 清單)

行號來源:REVIEW_HEAD 的該檔第 87–151 行

<!-- 逐字開始 -->
### 4. 固定全套(在乾淨的 S3G1B 上只跑一次;正式證據)

指令:`python -X utf8 -m pytest -q > <session scratch>/s3g1b-rerun.txt 2>&1`,exit 1。

跑完立刻:

```
$ git status --porcelain
(無輸出)
```

摘要行原文:

```
35 failed, 2058 passed, 3 skipped, 3 xfailed in 351.00s (0:05:50)
```

collected 2099(35 + 2058 + 3 + 3)。

FAILED 行原文(輸出檔第 1285–1319 行):

```
FAILED tests/test_host_evidence_policy.py::test_the_committed_policy_matches_the_committed_pyproject
FAILED tests/test_install.py::TestEvidencePolicyTemplate::test_g3_install_writes_the_template_outside_the_canonical_path
FAILED tests/test_install.py::TestEvidencePolicyTemplate::test_g3_the_template_lists_exactly_the_capability_boundary
FAILED tests/test_install.py::TestEvidencePolicyTemplate::test_g3_decisions_pending_asks_to_initialize_the_policy
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_a_repo_without_a_policy_is_not_full_coverage
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_uncommitted_policy_state_is_not_full_coverage[worktree-only]
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_uncommitted_policy_state_is_not_full_coverage[worktree-differs]
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_uncommitted_policy_state_is_not_full_coverage[staged-only]
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_uncommitted_policy_state_is_not_full_coverage[deleted-in-worktree]
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[malformed-json]
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[unknown-schema]
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[unknown-version]
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[unknown-key]
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[missing-field]
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_a_policy_outside_the_canonical_path_is_not_full_coverage
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_the_producer_records_the_policy_identity
FAILED tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_environment_mismatch_is_not_full_coverage[override]
FAILED tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_environment_mismatch_is_not_full_coverage[narrowed-dist]
FAILED tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[strict-markers]
FAILED tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[strict-config]
FAILED tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[o-flag]
FAILED tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[override-ini-eq]
FAILED tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[no-addopts]
FAILED tests/test_redlight.py::TestAddoptsDerivation::test_g3_a_policy_disagreeing_with_the_committed_addopts_is_not_full_coverage
FAILED tests/test_status.py::TestEvidencePolicyChain::test_g3_no_policy_does_not_retire_a_known_red
FAILED tests/test_status.py::TestEvidencePolicyChain::test_g3_an_uncommitted_policy_does_not_retire_a_known_red[worktree-only]
FAILED tests/test_status.py::TestEvidencePolicyChain::test_g3_an_uncommitted_policy_does_not_retire_a_known_red[worktree-differs]
FAILED tests/test_status.py::TestEvidencePolicyChain::test_g3_a_policy_environment_mismatch_does_not_retire_a_known_red
FAILED tests/test_status.py::TestEvidencePolicyStatusLine::test_g3_status_shows_the_policy_state[uninitialized]
FAILED tests/test_status.py::TestEvidencePolicyStatusLine::test_g3_status_shows_the_policy_state[uncommitted]
FAILED tests/test_status.py::TestEvidencePolicyStatusLine::test_g3_status_shows_the_policy_state[worktree-differs]
FAILED tests/test_status.py::TestEvidencePolicyStatusLine::test_g3_status_shows_the_policy_state[unknown-schema]
FAILED tests/test_status.py::TestEvidencePolicyStatusLine::test_g3_status_shows_the_policy_state[outside-boundary]
FAILED tests/test_status.py::TestEvidencePolicyStatusLine::test_g3_status_shows_the_policy_state[valid]
FAILED tests/test_verify_gates.py::test_every_evidence_policy_scenario_is_wired
```

集合對照:

- 〈四十八〉48.2 的 26 支 behavior-red:`test_redlight.py` 20 支 + `test_host_evidence_policy.py` 1 支 + `test_status.py::TestEvidencePolicyChain` 4 支 + `test_verify_gates.py` 1 支。上表**逐支都在**。
- 〈五十〉50.3 的 9 支:`test_install.py::TestEvidencePolicyTemplate` 3 支 + `test_status.py::TestEvidencePolicyStatusLine` 6 案。上表**逐支都在**。
- 26 + 9 = 35 = FAILED 行數。**沒有多、也沒有少**。
- 與第一次執行(stop 報告)的 FAILED 集合逐條相同。
<!-- 逐字結束 -->

### F.3 `docs/audits/2026-10-03-m1a-station3g-redlight.md` 第 3 節(固定全套與失敗集合)

行號來源:REVIEW_HEAD 的該檔第 110–153 行

<!-- 逐字開始 -->
### 3. 固定全套(在 S3G1 上只跑一次)

指令:`python -X utf8 -m pytest -q > <session scratch>/s3g-run.txt 2>&1`,exit 1。

摘要行原文:

```
26 failed, 2058 passed, 3 skipped, 3 xfailed in 243.99s (0:04:03)
```

collected 2090(26 + 2058 + 3 + 3;status 也顯示 collected 2090)。

FAILED 行原文(輸出檔第 737–762 行):

```
FAILED tests/test_host_evidence_policy.py::test_the_committed_policy_matches_the_committed_pyproject
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_a_repo_without_a_policy_is_not_full_coverage
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_uncommitted_policy_state_is_not_full_coverage[worktree-only]
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_uncommitted_policy_state_is_not_full_coverage[worktree-differs]
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_uncommitted_policy_state_is_not_full_coverage[staged-only]
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_uncommitted_policy_state_is_not_full_coverage[deleted-in-worktree]
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[malformed-json]
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[unknown-schema]
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[unknown-version]
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[unknown-key]
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[missing-field]
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_a_policy_outside_the_canonical_path_is_not_full_coverage
FAILED tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_the_producer_records_the_policy_identity
FAILED tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_environment_mismatch_is_not_full_coverage[override]
FAILED tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_environment_mismatch_is_not_full_coverage[narrowed-dist]
FAILED tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[strict-markers]
FAILED tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[strict-config]
FAILED tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[o-flag]
FAILED tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[override-ini-eq]
FAILED tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[no-addopts]
FAILED tests/test_redlight.py::TestAddoptsDerivation::test_g3_a_policy_disagreeing_with_the_committed_addopts_is_not_full_coverage
FAILED tests/test_status.py::TestEvidencePolicyChain::test_g3_no_policy_does_not_retire_a_known_red
FAILED tests/test_status.py::TestEvidencePolicyChain::test_g3_an_uncommitted_policy_does_not_retire_a_known_red[worktree-only]
FAILED tests/test_status.py::TestEvidencePolicyChain::test_g3_an_uncommitted_policy_does_not_retire_a_known_red[worktree-differs]
FAILED tests/test_status.py::TestEvidencePolicyChain::test_g3_a_policy_environment_mismatch_does_not_retire_a_known_red
FAILED tests/test_verify_gates.py::test_every_evidence_policy_scenario_is_wired
```

與 48.2 的 26 支 behavior-red 對照:**逐支相同,沒有多、也沒有少**。
<!-- 逐字結束 -->

---

## G. 審查重點

<!-- 逐字開始 -->
G1 I-3 bootstrap：policy 內容只來自 HEAD committed blob；worktree 只做 identity 比對、之後不再讀；任何一步失敗 ⇒ 記 None ⇒ unknown。
G2 能力邊界：任一欄位超出 B ⇒ 整份不合格 ⇒ unknown；effective = B ∩ policy；沒有任何路徑能擴張 B。
G3 committed_addopts 合約：None（取得 / 解析失敗）與 ""（合法、無 addopts）不得混用；addopts_overrides(value) 不讀 git / 檔案；判定只在 consumer。
G4 override_ini（修法 B）：producer 單次 getattr + sentinel；屬性不存在 ⇒ None ⇒ unknown；值為 None ⇒ []；T2 能擋下「consumer 把 None 當 []」的 fail-open。
   審查者必須確認 T1 在 S4G1B 為 red、T2 為 green，且 S4G1C 後兩者都 green（見 F 段紅綠定位表與 F.1 原文），不得只看最終全綠。
G5 不變式：(i)–(xix) 判定、單一 "true" 出口、content_hash 皆未被削弱或改動。
G6 committed_blobs 逐路徑：缺一檔不連坐；policy 指定的 config_file 與 ROOT_CONFTEST 都在 verdict 檢查。
G7 status 行：六種狀態的判定；「有效」只代表 policy 文件本身有效，不代表本次 runtime 能取得 true authority（殘餘，是否足夠請判斷）。
G8 安裝器：範本只在非 canonical 路徑；任何情況下都不能成為 authority；decisions-pending 有初始化待決項；不從本機觀察值產草稿。
G9 verify_gates：EVIDENCE_SCENARIOS 兩正三負的佈置是否真的測到宣稱的情境；負一～負三只斷言 unknown 不斷言成因（殘餘，是否足夠請判斷）；淨室不寫宿主帳本。
G10 測試授權與紅燈鏈：3g / 3g-1b 既有測試共 42 支 = 35 behavior-red + 7 regression-lock；E.4（BASE→S3G1 新增 33 支）與 E.5（S3G1→S3G1B 只新增 9 支、未改前 33 支）驗來源，E.2（S3G1B→TARGET）驗 4g 後這 42 支皆未被改動；S4G1B 另合法新增 T1/T2。既有測試只有授權 G1–G5 的改動，assertion / docstring / test identity 未改；test_d4 刪除後其宿主語意由 tests/test_host_evidence_policy.py 承接（讀 HEAD、讀不到就失敗、不 skip）。
G11 manifest：agent-gates 自己的 policy 不會被抄到下游；範本為 generate；宿主專用測試為 skip。
G12 跨平台：policy 與設定檔的 worktree blob 以 git hash-object（套用 .gitattributes）比對；CRLF 工作樹是否可能誤判。
G13 總問題：是否存在任何路徑，讓一個沒有「已提交、且與 runtime 一致的 policy」的 repo 取得 file_coverage == "true"。
<!-- 逐字結束 -->

---

## H. 已知殘餘與追蹤項

出處:F.1 的「殘餘與未證明」一節,即 REVIEW_HEAD 的 `docs/audits/2026-10-04-m1a-station4g-fix.md` 第 381–398 行。

<!-- 逐字開始 -->
### 8. 殘餘與未證明(依規劃檔 P7 與 4g 續作裁決;不擴張)

1. **閘門依賴 redlight.py 可 import**:`gate.head_content_hash` 經 `_redlight()` 載入工作樹的 redlight.py。半改狀態載不起來時,全部 R3 判定都會被擋。屬 fail-closed、照設計,不在本票修。
2. **status 的 `evidence policy: 有效` 只代表 policy 文件本身有效**:已提交、工作樹 = HEAD、schema / version 認得、在能力邊界內。它不代表本次 runtime 一定能取得 true authority。`committed_overrides` 與 HEAD addopts 推導是否一致,只在 verdict 時判定,status 行不檢查。屬追蹤項,**目前尚未 machine-enforced**。
3. **淨室負一到負三只斷言 unknown,不斷言 unknown 的成因**(追蹤項)。
4. **verify_gates 的 `SystemExit` 訊息**在 cp950 主控台重導向時為亂碼(既有行為)。
5. 規劃檔 P7 照舊、本票不處理:
   - 下游測試不在 `tests/` 底下時 producer 不載入;
   - 「無設定檔」不在能力邊界內;
   - 「人審」無法機器驗證;
   - sync 端沒有「需建立 evidence policy」提示;
   - logging 鎖步絆線(〈四十五〉45.3)**目前尚未 machine-enforced**,實作時須放進宿主專用檔;
   - `tests/test_leak_scan.py` 的宿主樹掃描在下游的意義;
   - 機器化 pre-push;
   - TOCTOU 與未 pin 版本;policy 改了但未 commit 的期間無法退紅。
6. **G3 的殘餘**:driver 固定的是 `_isolated_conftest` / `_chain_conftest` 預設所見的版本。測試事後以 `_e_sys(version_info=None)` 換掉 `sys` 的那些(例:3e 的 optimize 對照組),仍讀真實 Python 版本。在 3.11 以外的直譯器上,它們的正控是否仍綠:**未證明**。
7. **`addopts_overrides` 推導不了的寫法**(合併短旗標 `-qo x`、長旗標縮寫):方向是 unknown(fail-closed),不是假綠。
8. **本機只驗 Windows**。POSIX 的淨室結果目前只有裁決助手的原型驗證(第 3 節),不是本樹的實測。（S4G4 後更新：POSIX 已於本樹內容實測——裁決助手於隔離 Linux 環境以 S4G3 時點的 12 個程式 / 測試 / 設定檔跑 verify_gates 與宿主全套，見第 9 節；屬外部驗證，非本 repo 帳本證據。）
<!-- 逐字結束 -->

**註**:上列追蹤項目前尚未 machine-enforced。
