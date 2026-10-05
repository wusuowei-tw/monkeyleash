# 票 145 Station 5g 獨立審查報告

- 審查者:獨立審查(未參與實作、無先前對話記憶、未讀任何本機對話紀錄)
- 日期:2026-10-04
- 判斷來源:(1) 審查包;(2) 以完整 SHA 取得的 `git show` / `git diff` / `git grep` / `git log`;(3) 本機 pytest 9.1.1 原始碼(唯讀)
- 行號一律以 TARGET `8e7775526e462d984abb0992ed74c1e1aa3648dd` 為準;未跑 pytest / verify_gates.py / status.py

---

## 0. 身分與第 0 步原文

| 代號 | 完整 SHA |
|---|---|
| S5g-0(審查包所在) | `5e096acb899b3370f16018199627784af71b788e` |
| TARGET(S4G1C) | `8e7775526e462d984abb0992ed74c1e1aa3648dd` |
| REVIEW_HEAD(S4G5) | `b5db3734f6795d8a371e4f58b172e0a8ffb066eb` |
| BASE | `de36ebcbab284ef11064a9943b5191750482dd93` |

各自單獨執行,原文照錄:

```
$ git status --porcelain
 M docs/agents/friction-log.md
?? docs/tickets/framework-updates/146-claude-code-enforcement-integrity.md
?? docs/tickets/framework-updates/147-turn-end-check-via-settings-stop-hook.md
```

```
$ cat .dev/pipeline.json
{
  "current_stage": "review",
  "feature": "framework-updates",
  "ticket_id": "145",
  "updated": "2026-10-02"
}
```

```
$ git rev-parse 5e096acb899b3370f16018199627784af71b788e:docs/audits/2026-10-04-m1a-station5g-review-package.md
26141bdc40a83a0f2f85da97eefb64ace226cb4d
```

```
$ git hash-object docs/audits/2026-10-04-m1a-station5g-review-package.md
26141bdc40a83a0f2f85da97eefb64ace226cb4d
```

```
$ sha256sum docs/audits/2026-10-04-m1a-station5g-review-package.md
c88ddd71af4fd4f3038d0363c5372a51951c6f256aea9ac8bfcd75c00cfbcfb5 *docs/audits/2026-10-04-m1a-station5g-review-package.md
```

五項全部符合預期(3 個外來變更恰為指定的 3 檔;`current_stage` = `review`、`ticket_id` = `145`;blob 兩項皆 `26141bdc…`;sha256 = `c88ddd71…`)。

---

## 1. 判決

**PASS**

- blocker 0、major 0、minor 2、nit 3(見第 2 節)。
- 沒有找到任何能讓「沒有已提交、且與 runtime 一致的 policy」的 repo 取得 `file_coverage == "true"` 的路徑(G13,第 4 節)。
  S5g-F2 是唯一接近的形狀:它要求 git toplevel 的 HEAD 已提交一份**位元組相同**的 policy,內容仍來自已提交 blob;判為 minor。

---

## 2. Findings 表

| 編號 | 嚴重度 | 對應 G 題 | TARGET 檔名:行號 | 具體失敗情境(輸入 → 錯誤結果) | 依據 | 需要重現 |
|---|---|---|---|---|---|---|
| S5g-F1 | minor | G7(+G8) | `.claude/hooks/redlight.py:912-929`(`policy_state` 不查鎖步);`.claude/hooks/redlight.py:932-942`(範本 `committed_overrides: []`);`.claude/hooks/redlight.py:963-968`(鎖步只在 verdict);`.claude/portable/templates/pyproject.toml.template:27`(`addopts = "-ra --strict-markers"`);`.claude/portable/install.py:427-433` | 下游照框架自帶的 pyproject 範本(addopts 帶 `--strict-markers`),再把 `.agents/evidence-policy.template.json` **原樣**存成 canonical 並 commit → status 顯示 `evidence policy: 有效`,但每一次固定全套都是 `unknown`(推導 `["strict_markers=true"]` ≠ policy `[]`),紅燈永遠不退,且沒有任何一行指出原因。方向是 fail-closed(不會假綠),但正好是規劃檔 P4 說 status 行要消掉的「永遠 unknown 對下游是靜默的」那個形狀,而且是**最自然的初始化路徑** | 靜態閱讀:`policy_state` 只走 head / worktree / `policy_document_problems`,不呼叫 `addopts_overrides`;範本與 pyproject 範本兩份框架產物互相不一致 | 否(靜態可確定;若要端到端看畫面,最小重現:淨室安裝 → 放入 pyproject 範本 → `cp` policy 範本到 canonical → commit → 固定全套 → status) |
| S5g-F2 | minor | G13 / G1 / G6 | `.claude/hooks/redlight.py:845`(`rev-parse HEAD:<POLICY_FILE>`)、`:849`(`hash-object <POLICY_FILE>`)、`:739-740`(`committed_blobs` 同一手法)、`:805`(`cat-file blob HEAD:<config_file>`);`tests/conftest.py:410-412`(以 `_ROOT` 呼叫) | `_ROOT`(conftest 的上兩層)**不是** git toplevel 時(例:專案是某個大 repo 的子目錄、沒有自己的 `.git`):`git -C <root> rev-parse HEAD:<path>` 的 `<path>` 是**相對 tree 根**,而 `git -C <root> hash-object <path>` 是**相對 cwd**。若 toplevel 已提交一份 `.agents/evidence-policy.json`、`pyproject.toml`、`tests/conftest.py`,而子目錄內有**內容相同但從未提交於該路徑**的副本 → head == worktree 成立 → 可得 `"true"`,儘管子目錄自己的 canonical path 上沒有已提交的 policy。內容仍等於某個已提交 blob(完整性成立,位置不成立) | git 的 `<rev>:<path>` 語意(不以 `./` 開頭即相對 tree 根)與 `hash-object` 以 cwd 解析檔名;`install.main` 對無 `.git` 的目標會 `git init`(`.claude/portable/install.py:541-544`),所以**安裝器路徑**不會產生此佈局,只有手動佈局會 | **是**。最小重現:建 repo `R`,於 `R/` 提交合法 policy、pyproject、tests/conftest.py;在 `R/sub/` 放三份位元組相同的未追蹤副本與一支測試;於 `R/sub` 跑固定指令(或直接以 `redlight.evidence_policy_facts("R/sub")` / `committed_blobs("R/sub")` 讀事實)看 head 與 worktree 是否相等。修法方向:以 `HEAD:./<path>` 或先 `rev-parse --show-prefix` / 要求 `_ROOT == --show-toplevel` |
| S5g-F3 | nit | G3 | `.claude/hooks/redlight.py:812-816`(只認 `[tool.pytest.ini_options]`) | pytest 9 推薦的原生 TOML 寫法 `[tool.pytest]`(無 `ini_options`)→ `_committed_addopts` 回 None → 永遠 `unknown`;status 仍顯示「有效」。fail-closed。`[tool.pytest]` 與 `ini_options` 並存時 pytest 自己報錯(`_pytest/config/findpaths.py:120-134`),所以不構成假綠 | 規劃檔 P1 只盤點 `ini_options`(`redlight.py:491` 註解);但 H 段殘餘清單沒有列出這一型 | 否 |
| S5g-F4 | nit | G12 | `.claude/hooks/redlight.py:739-740`、`:1095-1098` | `.gitattributes` 對 `pyproject.toml` / `tests/conftest.py` 宣告 `filter=<driver>` 且本機設了 clean filter:`hash-object` 套 clean filter 後可與 HEAD blob 相等,而 pytest 實際讀的工作樹內容不同 → (xi) 誤判一致。需要 repo 已提交 filter 屬性 + 本機 filter 設定,屬刻意佈置。**policy 檔本身不受影響**(內容只從 HEAD blob 取,`:853-856`)。此手法在 BASE 即存在(S4d 的 `committed_blobs`),本票只改為逐路徑 | `git hash-object <file>` 預設套用轉換(含 filter)| 是(以 `filter.x.clean` 佈置即可) |
| S5g-F5 | nit | G9 | `.claude/portable/verify_gates.py:470-486`、`:420-426` | 正二不成立時,負一~負三仍各自印「成立 ✓」(S4G1 那一次即如此,F.1 第 3 節)。負情境只斷言 unknown,其判別力**完全來自**同一次執行中正二成立的差分;程式沒有把這個耦合寫進輸出,未來讀者可能把那幾行當證據 | 審查包 F.1 第 3 節自己也註明「本次負一到負三的成立不作為證據」—— 那是人寫的,不是機器印的 | 否 |

---

## 3. G1–G13 逐題結論與依據

### G1 I-3 bootstrap —— **成立**

- 內容只來自 HEAD blob:`redlight.py:845` 取 `HEAD:<POLICY_FILE>` 的 blob sha;`:849` `hash-object` 取工作樹 blob;`:851-852` 不等即返回;`:853` `cat-file blob <head sha>`;`:856` `json.loads` 只解析那份 bytes。工作樹檔在 `:849` 之後不再出現。
- 任一步失敗 ⇒ 欄位 None:`:842-843` 預設全 None;`:846-847`、`:854-855`、`:857-858` 提前返回;`:864-865` 吞例外。consumer `_effective_policy`(`:955-956`)要求 `head` 為非空字串且 `worktree == head`;`policy_document_problems(None)` ⇒ 格式問題(`:881-882`)⇒ None(`:959-960`)⇒ verdict `unknown`(`:1074-1076`)。
- 唯一 Python 層讀檔是 `policy_state` 的 `os.path.exists`(`:920`),只用來區分「未提交 / 未初始化」兩個狀態字,不進 verdict。
- 迴歸鎖 `tests/test_redlight.py:2364-2389`(#13)以攔截 `open` / `io.open` 驗證。
- 例外形狀見 S5g-F2(root ≠ toplevel)。

### G2 能力邊界 —— **成立**

- 界外 ⇒ 整份不合格:`redlight.py:900-909` 對 `config_file` / `python_versions` / `pytest_versions` / `dists` 逐一比 B 常數;任一 ⇒ `bnd` 非空 ⇒ `_effective_policy` None(`:959-960`)。
- 格式先於邊界:`:884-885` schema / version 不認得即停;`type(version) is int` 排除 `True`;`:888-899` 鍵集合恰等、型別。
- effective = B ∩ policy:`:972-974`;使用處 `:1077`、`:1085`、`:1102`,每一處都以 B 常數為第一個參數,**沒有任何路徑從 policy 取得 B 以外的值**。`config_file` 另在 `:1092` 再比一次 `FRAMEWORK_CONFIG_FILES`。
- `committed_overrides` 不屬 B,由鎖步(`:963-968`)與 runtime(`:1087`)雙重約束。
- 迴歸鎖 `tests/test_redlight.py:2403-2429`(#15–#18)。

### G3 `committed_addopts` 合約 —— **成立**

- None vs `""`:`redlight.py:801-804`(無 tomllib)、`:805-807`(blob 讀不到)、`:808-811`(UTF-8 / TOML 錯)、`:815-816`(無 `ini_options` 段)、`:822`(型別錯)⇒ None;`:817-818` 段在、無鍵 ⇒ `""`。
- consumer:`:964-965` None ⇒ unknown;`""` 經 `addopts_overrides("")` ⇒ `shlex.split("")` = `[]`(`:763-766`)⇒ 與 policy `[]` 比。兩者不混用。
- `addopts_overrides` 不讀 git / 檔案:`:762-788` 只用 `shlex`,型別不符 ⇒ None(`:770-771`)。
- 判定只在 consumer:producer `evidence_policy_facts` 只記原值(`:862-863`)。
- 旗標表封閉性:pytest 9.1.1 的 `OverrideIniAction` 只有三處使用(`_pytest/main.py:76-96`:`--strict-config` / `--strict-markers` / `--strict`),與 `OVERRIDE_FLAGS`(`redlight.py:524-526`)逐一相符;`-o` 為 `action="append"`、無 default(`_pytest/helpconfig.py:112-119`);動作本體 `_pytest/config/argparsing.py:491-503`。
- 推導錯誤的方向:runtime `override_ini` 必須另外等於 policy(`:1087`),而 policy 必須等於推導(`:967`)。推導漏項只會讓三者不等 ⇒ unknown。
- 殘餘見 S5g-F3(原生 `[tool.pytest]`)。

### G4 override_ini(修法 B)—— **成立**

- 程式:`tests/conftest.py:346` `_MISSING = object()`;`:358` **單次** `getattr(option, "override_ini", _MISSING)`;`:359-360` 不存在 ⇒ None;`:361` 值為 None ⇒ `[]`;其他照舊。`:406` 交給 `normalize_overrides`(`redlight.py:675-696`:非 list/tuple ⇒ None)。
- 屬性不存在 ⇒ 落帳 None ⇒ `_completeness_problems` 接受 None(`redlight.py:1008-1010`)⇒ verdict `None != list(policy["committed_overrides"])`(`:1087`)⇒ unknown。consumer 未改(S4G1→TARGET numstat 只有 `tests/conftest.py` 22/2 與 `tests/test_redlight.py` 42/0)。
- 真實 pytest 下屬性必定存在(argparse 為每個 dest 設預設)、未給旗標時值為 None —— 與 `_pytest/helpconfig.py:112-119`、`_pytest/config/argparsing.py:499-503` 一致。
- **T2 能擋修法 A**:T2(`tests/test_redlight.py:2522-2534`)以 `_d_option(missing=("override_ini",))` 讓屬性不存在(`_COption` 以 `values.pop` 刪鍵,`tests/test_redlight.py:795-800`),policy `committed_overrides: []`、addopts `-ra`。若 consumer 把 None 當 `[]`,`:1087` 會相等,其餘條件同 T1 ⇒ `"true"` ⇒ T2 斷言 `!= "true"` 失敗。若改在 producer 把「不存在」也變 `[]`,同樣失敗。
- **紅綠時序(按包內要求逐段確認,不只看最終全綠)**:
  - S4G1B 上 T1 為 red:F.1 原文(審查包第 5379-5391 行)`tests\test_redlight.py:2520: AssertionError`、`assert 'unknown' == 'true'`、`FAILED …test_g3_no_override_anywhere_is_full_coverage`、摘要 `1 failed, 2093 passed, 3 skipped, 3 xfailed`、「唯一的 FAILED 是 T1;T2 在 2093 passed 之內」。
    紙上推演一致:S4G1B 的 conftest 仍是 `getattr(option, "override_ini", None)`(E.3 / F.1 第 5 節的 `-` 行)⇒ T1 的 None 原樣落帳 ⇒ `None != []` ⇒ unknown。失敗行 2520 = TARGET 的 `assert got == "true", got`(S4G1B→TARGET 未改 test_redlight.py,行號不動)。
  - S4G1B 上 T2 為 green:屬性不存在 ⇒ None ⇒ unknown ⇒ `!= "true"` 成立。
  - TARGET 上兩者 green:F.1 原文 `2094 passed, 3 skipped, 3 xfailed`(0 failed);推演:T1 的 None ⇒ `[]` ⇒ 與 policy `[]`、推導 `addopts_overrides("-ra") == []` 三者相等 ⇒ 其餘同對照組 ⇒ `"true"`;T2 不變。
  - 外部(裁決助手)原型驗證「T1 在 S4G1 失敗、在 B 通過;T2 在 S4G1 與 B 都通過、在 A 失敗」(F.1 第 3 節)—— 屬非本 repo 帳本證據,本審查只作旁證。

### G5 不變式 —— **成立**

- 單一 `"true"` 出口:`git show <TARGET>:.claude/hooks/redlight.py` 全檔 grep `return "true"|== "true"` 只命中 `:1127`。
- `content_hash`(`:47`)未改:BASE..TARGET 的 redlight.py diff 共 5 個 hunk(`@@ -488`、`@@ -683`、`@@ -736`、`@@ -763`、`@@ -786`),沒有一個落在 `content_hash` 或其呼叫的函式。
- (i)–(xix) 未削弱:diff 中 verdict 的每一條既有判定都保留,只把比較對象由 B 常數換成 `_effective(B, policy)`(本身 ⊆ B)或 policy 欄位(已驗 ⊆ B);新增 (P)(`:1074-1076`)與 known_dist 接受檢查(`:1080-1082`),兩者都只會多出 unknown。
- `_completeness_problems` 的 `config_blobs` 驗法由「`COMMITTED_FILES` 每項都在」改為「`ROOT_CONFTEST` 必在 + 全部值型別正確」(`:1017-1022`),`config_file` 那一項移到 verdict(`:1095-1098` 以 `blobs.get(p)` + `isinstance(b, dict)` 驗)。強度等價。

### G6 `committed_blobs` 逐路徑 —— **成立**

- `redlight.py:735-746`:每個路徑各一次 `hash-object` 與一次 `rev-parse`,各自 try;缺一檔只影響該項。
- 預設路徑 `BLOB_FILES = FRAMEWORK_CONFIG_FILES + (ROOT_CONFTEST,)`(`:497`);policy 的 `config_file` 必屬 `FRAMEWORK_CONFIG_FILES`(`:901-902`、`:1092`),所以必有記錄。
- verdict `:1095-1098` 同時檢查 `config_file` 與 `ROOT_CONFTEST`,工作樹 blob 須非空且等於 HEAD blob。
- 例外形狀見 S5g-F2(root ≠ toplevel 時兩個 git 指令的路徑基準不同)。

### G7 status 行 —— **部分成立**

- 六種狀態判定正確:`redlight.py:912-929`(HEAD 無 ⇒ 依工作樹有無分「未提交 / 未初始化」;`worktree != head` ⇒「工作樹與 HEAD 不同」;格式 ⇒「格式不明」;邊界 ⇒「超出框架能力邊界」;其餘「有效」)。`status.py:563-575` 只轉呼叫 `policy_state`,不另寫判準;`:867` 接在 test-runs 行之後。
- deleted-in-worktree:`hash-object` 失敗 ⇒ worktree None ⇒「工作樹與 HEAD 不同」;staged-only:HEAD 無、工作樹有 ⇒「未提交」。合理。
- **殘餘判斷**:「有效」不含 addopts 鎖步(H 段第 2 點)。方向 fail-closed,**可接受到下一張票**;但它不只是理論上的殘餘 —— 框架自己的兩份範本組合起來就會觸發(S5g-F1)。建議下一張票至少二選一:(a) status 在「有效」之外多一個狀態(例:「與已提交設定的 addopts 不一致」),判準直接重用 `_effective_policy` 的鎖步那一段;(b) 讓 policy 範本或 decisions-pending 明示「若沿用 pyproject 範本,`committed_overrides` 要填 `["strict_markers=true"]`」。(b) 只是文字,不會有東西叫;(a) 才有機制。
- 「部分成立」的理由:判定本身正確(成立),「足不足夠」的那一半有一個具體的、預設路徑上的缺口(S5g-F1)。

### G8 安裝器 —— **成立**

- 只寫非 canonical:`install.py:386` `POLICY_TEMPLATE = ".agents/evidence-policy.template.json"`;`:399-412` 寫到該路徑;`evidence_policy_facts` 只認 `POLICY_FILE` 常數(`redlight.py:506`、`:845`),沒有任何程式讀範本路徑 ⇒ 不論是否提交都不能成為 authority。
- 內容 = B 常數完整列舉:`redlight.py:932-942`,由目標 repo 自己的 redlight 產生(`install.py:389-396`、`:407`),不讀本機觀察值。
- decisions-pending:`install.py:426-433` 只要 `policy_file` 有值就加一項,含 canonical 路徑;`:571-572` 一律傳入。
- 不從本機觀察值產草稿:install.py 中沒有讀版本 / dist 的程式。(`verify_gates.py:324-346` 的 `_ev_matching_policy` 會讀本機版本,但那是淨室驗收工具,不是安裝流程。)
- 3g-1b I1(`tests/test_install.py` 的 `TestEvidencePolicyTemplate`)以真安裝 + 真 producer / consumer 驗範本非 authority。

### G9 verify_gates —— **成立(殘餘可接受)**

- 佈置對應宣稱:
  - 正一 `verify_gates.py:387-404`:讀框架測試那一次的最後一筆 session,所有檔皆 unknown,且 status 為「未初始化」。
  - 正二 `:407-417`:policy = 當下環境 ∩ B(`:324-346`)、`committed_overrides: []`、pyproject 無 addopts(`EV_PYPROJECT`)⇒ `_committed_addopts` = `""` ⇒ 推導 `[]`;runtime 不帶任何 `-o` ⇒ 修法 B 後 `[]`。斷言 rc 1→0、`cov == "true"`、status green / 非 red、「有效」。這正是 S4G1 漏掉的「無 override」路徑。
  - 負一 `:429-432`:`PYTEST_ADDOPTS="-o python_functions=test"` ⇒ runtime 多一個 override(探針 `test_probe` 仍符合 `test` 前綴,所以仍有 passed)。
  - 負二 `:435-437`:policy 已提交後工作樹多一行。
  - 負三 `:440-442`:policy 從未 `git add`。
  - 每個情境從同一 base 出發、結束 `git reset --hard` + `git clean -qfd`(`:463-467`、`:470-486`)。
- 負情境只斷言 unknown:各負情境與正二只差一個變因,而正二在同一次執行成立(F.1 第 6 節 5d)⇒ 成因由差分可歸屬。**可接受到下一張票**;附帶 S5g-F5(程式沒有把這個耦合印出來)。
- 不寫宿主帳本:子行程 cwd = target(`:349-354`),target 的 conftest 以自身位置求 `_ROOT`;本行程只讀 target 帳本(`load_runs(target)`)。F.1 第 6 節 V0 與事後 bytes / sha256 相同為實測證據(本審查未重跑)。
- 接線測試 `tests/test_verify_gates.py::test_every_evidence_policy_scenario_is_wired` 只驗鍵(規劃檔 P5 本來就如此定位)。

### G10 測試授權與紅燈鏈 —— **成立**

三段依序確認(全部以完整 SHA 為錨點):

- **E.4 BASE→S3G1**(`git diff --numstat de36ebc…..2737e02…`):
  `91 0 tests/test_host_evidence_policy.py`、`363 0 tests/test_redlight.py`、`159 0 tests/test_status.py`、`24 0 tests/test_verify_gates.py` —— 全部只增不刪;每檔恰一個檔尾 hunk(審查包 E.4 的 `@@ -2142,3 +2142,366`、`@@ -2856,3 +2856,162`、`@@ -289,3 +289,27`、新檔 `@@ -0,0 +1,91`)。對應 48.2 的 33 支(26 behavior-red + 7 regression-lock),紅燈集合與 F.3 的 26 行 FAILED 逐支相同。
- **E.5 S3G1→S3G1B**(`git diff --numstat 2737e02…..83258dd…`):
  `205 0 tests/test_install.py`、`117 0 tests/test_status.py` —— 只增;hunk `@@ -463,0 +464,205`、`@@ -3017,0 +3018,117`(檔尾),前 33 支所在範圍未觸及。新增 9 支 behavior-red,F.2 的 35 行 FAILED = 26 + 9。
- **E.2 S3G1B→TARGET**(`git diff -U0 83258dd…..8e77755… -- <TEST_FILES>`):
  - `tests/test_redlight.py`(S3G1B 共 2507 行,`git grep -c ""`):舊側 hunk 位置 289、298、1130、1148、1152、1489-1534、2507(檔尾追加)。3g 段(S3G1B 的 helper 自約 2142 起、`TestEvidencePolicyBootstrap` 2283、`TestEvidencePolicyBoundary` 2427、`TestAddoptsDerivation` 2481 至 2507)**沒有任何 hunk**;2507 之後的追加 = T1 / T2。
  - `tests/test_status.py`(S3G1B 共 3134 行):舊側 hunk 位置 597、1373、1497、1511、2364、2376、2380、2384;3g 段(2856 起;`TestEvidencePolicyChain` 2946、`TestEvidencePolicyStatusLine` 3110)**沒有任何 hunk**。
  - `tests/test_install.py`、`tests/test_verify_gates.py`、`tests/test_host_evidence_policy.py`:S3G1B→TARGET 無變更(`--stat` 不列)。
  ⇒ 42 支(35 behavior-red + 7 regression-lock)在 4g 未被改動。
- 授權對照(改動都在 helper / driver / 常數,不在 3g 測試本體):
  - G1:`_D_POLICY_FILE` / `_D_BASELINE_POLICY`(`tests/test_redlight.py` 新 1143-1155)、`_d_committed_root` 加寫並 add policy;`_T_POLICY_FILE` / `_T_BASELINE_POLICY` / `_T_BASELINE_ADDOPTS`、`_t_committed`(test_status)。
  - G2:`TestTestsUnderTicketUsesTheLatestRecordPerFile`、`TestOrphans` 兩處 completeness dict 只多一鍵 `evidence_policy`(+ helper `_t_policy_facts`)。
  - G3:`_isolated_conftest`(`tests/test_redlight.py:290-310`)與 `_chain_conftest` 固定 3.11 / 9.1.1,先記 `_REAL_PYTEST_VERSION`,測試先改版本時不覆蓋。
  - G4:`test_d4` 刪除(舊 1489-1534),原位留註解。
  - G5:manifest(見 G11)。
  - 既有測試的 assertion / docstring / test identity:上列 hunk 中除 G4 的整支刪除外,沒有改到任何 `assert`、docstring 或 `def test_` 行。
- S4G1B 合法新增 T1 / T2:`git diff --numstat f4fa041…..8e77755…` = `22 2 tests/conftest.py`、`42 0 tests/test_redlight.py`;T1 / T2 的紅綠見 G4。
- test_d4 的宿主語意由 `tests/test_host_evidence_policy.py` 承接:`git show HEAD:<path>`(`_git_show_head`,`returncode != 0` ⇒ `assert` 失敗)、無 `skip` / `skipif`、推導在該檔獨立實作(不呼叫 redlight 的推導,材料不取自被量對象)、唯讀;BASE→TARGET 該檔只在 S3G1 新增,之後未改。本 repo `HEAD:pyproject.toml` 第 72 行 `addopts = "-ra --strict-markers"`,與 `.agents/evidence-policy.json` 的 `["strict_markers=true"]` 一致。

### G11 manifest —— **成立**

- `.agents/portable-manifest.txt:106` `.agents/evidence-policy.json    skip` —— agent-gates 自己的 policy 不出貨。
- `:124` `.agents/evidence-policy.template.json generate`。
- `:229` `tests/test_host_evidence_policy.py skip`。
- 一併確認:`:69` `pyproject.toml skip`、`:71` `.gitattributes skip`(後者與 G12 相關)。

### G12 跨平台 —— **成立(附 nit)**

- policy 與設定檔的工作樹 blob 都用 `git hash-object <path>`(`redlight.py:739`、`:849`),預設套用 `.gitattributes` / `core.autocrlf` 的轉換;本 repo `.gitattributes` 為 `* text=auto`(TARGET 版本)。
- CRLF 工作樹:有 `text=auto` 或 `core.autocrlf=true|input` 時,hash 前轉回 LF ⇒ 與 LF 的 HEAD blob 相等,不誤判。下游 `.gitattributes` 標 skip 不出貨,若下游既無屬性又 `autocrlf=false`、而編輯器存成 CRLF ⇒ hash 不等 ⇒ unknown —— 此時 `git status` 也會顯示該檔已修改,屬一致的 fail-closed,不是誤判。
- 不可能因行尾造成假綠:policy 內容只從 HEAD blob 取;設定檔與 conftest 的行尾差異對 TOML / Python 語意無影響。
- 例外形狀:clean filter(S5g-F4,nit,BASE 已存在)。

### G13 總問題 —— **成立(未找到反例;最接近的形狀判 minor)**

見第 4 節。

---

## 4. G13 反例嘗試清單

目標:讓一個沒有「已提交、且與 runtime 一致的 policy」的 repo 得到 `file_coverage == "true"`。`"true"` 唯一出口 `redlight.py:1127`,必經 `:1072-1076`。

| # | 嘗試路徑 | 結果 | 擋在哪 |
|---|---|---|---|
| 1 | HEAD 沒有 policy(未初始化) | 擋 | `:845-847` head None ⇒ `:955-956` |
| 2 | 只在工作樹(負三)/ 只 staged | 擋 | 同上(`HEAD:` 不看 index) |
| 3 | HEAD 有、工作樹改過(負二)/ 工作樹刪除 | 擋 | `:849-852`;consumer `:955` |
| 4 | staged 改過、工作樹還原成 HEAD | 不構成反例 | 內容取自 HEAD blob,與 runtime 無關;此時 HEAD 即為已提交 policy |
| 5 | policy 放在非 canonical 路徑(含安裝範本) | 擋 | 只讀 `POLICY_FILE`(`:506`、`:845`) |
| 6 | policy 內含自我指定位置的鍵 | 擋 | 鍵集合恰等(`:888-890`) |
| 7 | schema / version 不認得;version 為 `true` 或 `1.0` | 擋 | `:884-885`(`type(version) is int`) |
| 8 | JSON 格式錯、帶 BOM、頂層不是物件 | 擋 | `:856` 例外 ⇒ `:864`;`:857-858` |
| 9 | 欄位界外(擴張 B) | 擋 | `:900-909` |
| 10 | 界內但與 runtime 不符(python / pytest / dist / config_file / override) | 擋 | `:1077-1092`、`:1102` |
| 11 | policy 的 `committed_overrides` 與 HEAD addopts 推導不符 | 擋 | `:963-968` |
| 12 | HEAD 設定檔讀不到 / 不是 TOML / 無 `ini_options` / 原生 `[tool.pytest]` | 擋(unknown) | `:801-822` ⇒ `:964-965` |
| 13 | 推導漏寫法(`-qo x`、長旗標縮寫) | 擋 | 推導 ≠ runtime ⇒ `:967` 或 `:1087` |
| 14 | 推導多算(某個值剛好以 `-o` 開頭被誤認) | 不構成反例 | 要得 true,runtime 必須真的有同一個 override,且已提交 policy 明列接受它 |
| 15 | runtime `override_ini` 屬性不存在(事實取不到) | 擋 | `tests/conftest.py:358-360` ⇒ None ⇒ `:1087`;T2 鎖 |
| 16 | `PYTEST_ADDOPTS` / CLI 加 `-o` | 擋 | runtime ≠ policy(`:1087`)|
| 17 | `-c` / 不同 inifile / 從子目錄跑使 inipath 不同 | 擋 | `:1089-1093` |
| 18 | 設定檔或 conftest 工作樹 ≠ HEAD | 擋 | `:1095-1098` |
| 19 | 舊 producer(無 `evidence_policy` 欄)+ 新 consumer | 擋 | `:1024-1026` ⇒ `:1072-1073` |
| 20 | 新 conftest + 舊 redlight(無 `evidence_policy_facts`) | 擋 | `tests/conftest.py:411-412` 記 None ⇒ 同上 |
| 21 | `[tool.pytest]` 與 `ini_options` 並存,讓推導看 ini、pytest 看原生 | 不可能 | pytest 直接報錯(`_pytest/config/findpaths.py:120-134`) |
| 22 | CRLF / `text=auto` 讓不同內容 hash 相等 | 不構成反例 | 只有行尾差異;policy 內容來自 HEAD |
| 23 | clean filter 讓設定檔 / conftest 的工作樹 ≠ HEAD 但 hash 相等 | 理論上可對 (xi) 誤判;**policy 不受影響** | S5g-F4(nit;BASE 已存在;需本機 filter 設定) |
| 24 | `_ROOT` 不是 git toplevel,toplevel 已提交同內容 policy、子目錄放未提交副本 | **可得 true**,但 policy 內容等於某個已提交 blob | S5g-F2(minor;需要重現;安裝器路徑不會產生此佈局) |
| 25 | 直接手寫 / 竄改 `.dev/test-sessions.jsonl` | 不在本票威脅模型內 | consumer 信任 producer 帳本(既有設計,BASE 已審) |
| 26 | HEAD 在 run 期間改變(TOCTOU) | 已列殘餘(H 段第 5 點) | — |

---

## 5. 殘餘評估(G7、G9 及 H 段)

| 項目 | 評估 | 可延到下一張票? |
|---|---|---|
| G7 / H-2:status「有效」不含 addopts 鎖步 | fail-closed;但框架兩份範本組合即觸發(S5g-F1),讓下游永遠退不了紅而沒有訊號 | **可以**,但建議下一張票以機制(status 多一狀態,重用 `_effective_policy` 的鎖步)處理,不要只改文字 |
| G9 / H-3:負一~負三只斷言 unknown 不斷言成因 | 成因由「同一次執行中正二成立」的單一變因差分歸屬;邏輯上足夠 | **可以**;附 S5g-F5:建議在正二不成立時把負情境標為「無判別力」 |
| H-1:閘門依賴 redlight.py 可 import | fail-closed、照設計 | 可以 |
| H-4:cp950 主控台亂碼 | 既有、與證據正確性無關 | 可以 |
| H-5:P7 照舊各項 | 皆 fail-closed 或程序性;無一會產生假綠 | 可以 |
| H-6:G3 殘餘(以 `_e_sys(version_info=None)` 換掉 sys 的測試在非 3.11 上未證明) | 只影響框架自測在其他直譯器上的綠燈,不影響 verdict 方向 | 可以 |
| H-7:推導不了的寫法 | 已核對方向為 unknown(第 4 節 #13) | 可以 |
| H-8:本機只驗 Windows | S4G4 已記 POSIX 外部驗收 PASS(非本 repo 帳本證據);本審查未重現 | 可以 |
| 新增(本審查):S5g-F2 root ≠ toplevel | 位置不變式未綁定;內容完整性仍成立 | **可以**,建議與 S5g-F4 一起開一張「(xi) / I-3 的 git 路徑基準」追蹤票 |
| 新增(本審查):S5g-F3 原生 `[tool.pytest]` | fail-closed;H 段未列 | 可以;建議補進殘餘清單,並與 S5g-F1 同一張票處理 status 訊號 |

結論:**沒有必須在本票修的殘餘**。

---

## 6. 審查限制

1. **沒有跑任何測試或驗收**(依規則)。T1 / T2 的紅綠、固定全套摘要、淨室五情境、帳本不變,全部依審查包 F 段照錄的輸出,加上紙上推演;推演與照錄一致,但兩者都不是我實測的。
2. S5g-F2、S5g-F4 標「需要重現」:結論依 git 的路徑 / 屬性語意推得,未實際建 repo 驗證。
3. 外部 POSIX 驗收(S4G4)與裁決助手的原型驗證屬非本 repo 帳本證據,無法獨立核對。
4. 未逐行讀 `tests/test_status.py` 的 3g 測試本體、`tests/test_install.py` 的 I1 全流程、`status.py` 的退紅判定其餘部分(BASE 已審);G10 的「未改動」是以 hunk 位置對 class 範圍判定,不是逐行比對內容(numstat 與 `-U0` hunk 已足以排除改動)。
5. 未讀 `classify_plugins` 的完整實作(BASE 已存在,本票未改);G2 中「known_dist 只對 `KNOWN_DISTS` 內的 (名, 版本) 分類」依其既有語意與 4g 註解。
6. 審查包 A.2 第 1 點寫「不寫任何暫存檔」;本次依交付指令的唯一例外只寫了本檔,未寫其他檔、未用 scratchpad 重導向。
