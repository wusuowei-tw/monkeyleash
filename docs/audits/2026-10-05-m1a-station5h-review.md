# 票 145 Station 5h 增量獨立審查報告

- 審查者:全新對話,未參與實作,未讀任何本機對話紀錄。
- 審查日期:2026-10-05
- 審查範圍:TARGET_G → TARGET 的 3h / 4h 增量;以及增量是否讓 5g 結論失效。
- 行號一律以 TARGET `ea6aba6452668982fee56f7a2f0faf2cd720ca6d` 為準。本機使用者名稱寫為 `<user>`;
  實驗路徑前綴 `C:/Users/<user>/AppData/Local/Temp/claude/c--projects-agent-gates/92efd092-a717-4320-a3c2-9e7ef9b3940d/scratchpad` 簡寫為 `<scratch>`。

---

## 0. 身分與第 0 步原文

| 代號 | 完整 SHA |
|---|---|
| S5h-0(審查包所在 commit) | `300b42a520b0a62fec0931d895200ea8817e47aa` |
| TARGET(S4H1) | `ea6aba6452668982fee56f7a2f0faf2cd720ca6d` |
| TARGET_G | `8e7775526e462d984abb0992ed74c1e1aa3648dd` |
| REVIEW_HEAD(S4H4) | `2f496b9d0a71d88995b2338c6b4440d693c9a879` |
| S3H1 | `7621e3ce8604ab72ab2f3fb3257cb1181b8a126e` |

第 0 步(各自單獨執行):

```
$ git status --porcelain
 M docs/agents/friction-log.md
?? docs/tickets/framework-updates/146-claude-code-enforcement-integrity.md
?? docs/tickets/framework-updates/147-turn-end-check-via-settings-stop-hook.md

$ cat .dev/pipeline.json
{
  "current_stage": "review",
  "feature": "framework-updates",
  "ticket_id": "145",
  "updated": "2026-10-05"
}

$ git rev-parse 300b42a520b0a62fec0931d895200ea8817e47aa:docs/audits/2026-10-05-m1a-station5h-review-package.md
d0260d087ccfac00376c4ac624c36b261eeb8fde

$ git hash-object docs/audits/2026-10-05-m1a-station5h-review-package.md
d0260d087ccfac00376c4ac624c36b261eeb8fde

$ sha256sum docs/audits/2026-10-05-m1a-station5h-review-package.md
f37743fb9e358ba33b07cb2ebe08f33e42092fb0a1525032de0089d4d13093cb *docs/audits/2026-10-05-m1a-station5h-review-package.md
```

五項全部符合預期(外來變更恰為 3 個;`current_stage` `review`、`ticket_id` `145`;blob 兩處相同;SHA-256 相同)。外來 3 檔未讀、未碰。

---

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

---

## 2. Findings 表

| 編號 | 嚴重度 | 對應 G 題 | TARGET 檔名:行號 | 具體失敗情境(輸入 → 錯誤結果) | 依據 | 需要重現 |
|---|---|---|---|---|---|---|
| S5h-F1 | **major** | G9 / G1 / G7 | `.claude/hooks/redlight.py:730-736`(判準只看 `--show-prefix`);`:727`(docstring「root 是否就是 git 工作樹的最上層」);`:868-869` → `:870` `HEAD:<POLICY_FILE>` / `:874` `hash-object <POLICY_FILE>`;`:752` → `:759-760`(`committed_blobs` 同一手法);`:825`(`cat-file blob HEAD:<config_file>`);`tests/conftest.py:130`、`:410-412`(以 `_ROOT` 呼叫) | root(= conftest 的上兩層)位於某個 gitdir 內 —— 例:`R.git` 是 bare repo(或 `R/.git`),HEAD 已提交合法 policy、`pyproject.toml`、`tests/conftest.py`;在 `R.git/`(或 `R.git/proj/`、`R/.git/`)放三份位元組相同、**Git 不視為任何工作樹檔**的副本 → `--show-prefix` exit 0 且輸出 `\n` ⇒ `_root_is_toplevel` True → `HEAD:<path>` 取 tree 根的已提交 blob、`hash-object <path>` 讀 root 底下的副本 → head == worktree → `evidence_policy_facts` 與 `committed_blobs` 全部成立 → 其餘條件與 H1 相同 ⇒ 預期 `file_coverage == "true"`。被驗證的 HEAD 物件與實際使用的檔案沒有任何 Git 意義上的路徑對應(identity 錯位);同一 root 的 `--show-toplevel` 為 `fatal: this operation must be run in a work tree`(exit 128),即 53.3 裁決 2 所稱的等價式在此不成立 | git 2.53.0.windows.2 實測(第 4 節 E3–E6):bare 目錄、bare 底下子目錄、`.git/`、`.git/refs` 的 `--show-prefix` 全為空且 exit 0;bare 目錄與 `.git/` 內 `rev-parse HEAD:.agents/evidence-policy.json` 與 `hash-object .agents/evidence-policy.json` 皆為 `30ed4d4db34fbf419031f0b767ca2d2fdad693f4`;`safe.bareRepository` 未設定(預設允許隱式 bare 探索) | **是**(端到端)。最小重現:沿用 H1 的 helper,把 `sub = parent / "sub"` 換成 `root = parent / ".git"`,把三份副本寫到 `parent/.git/` 底下,`_g_coverage(root, monkeypatch)`;預期 TARGET 上得 `"true"`。git 原語層已確認,不需重現 |
| S5h-F2 | minor | G2 / G5 | `.claude/hooks/redlight.py:752-757`(`committed_blobs` 的非最上層分支);`tests/test_redlight.py:2550-2567`(H1 只斷言 `!= "true"`) | 把 `:755-757` 刪掉(`committed_blobs` 在非最上層照舊呼叫 git、留 (xi) 半套),H1 **仍會綠**:`evidence_policy_facts` 在 `:868-869` 已回全 None ⇒ `_effective_policy` 於 `:980` 回 None ⇒ verdict `:1099-1101` unknown,根本走不到 `:1119-1123` 的 blob 檢查。TARGET 全樹沒有任何測試直接呼叫 `committed_blobs` 或 `_root_is_toplevel`(`git grep` 只命中 `redlight.py` 本身與 `tests/conftest.py:410`)。G2 要求的「不得只擋 policy、留 (xi) 半套」目前**只由程式碼保證,沒有測試鎖住** | 靜態閱讀 + `git grep -n -e committed_blobs -e _root_is_toplevel -e show-prefix ea6aba64…` 的原文(第 4 節 E0) | 是(突變測試:刪 `:755-757` 後跑 H1,預期仍 passed) |
| S5h-F3 | nit | G7 | 殘餘措辭(REVIEW_HEAD `docs/audits/2026-10-05-m1a-station4h-fix.md` 第 7 節第 3 點;票 145〈五十五〉55.2);`.claude/hooks/redlight.py:747-749`、`:861-863`(docstring「框架目前只支援一個 host evidence root = 一個 Git 最上層」) | 殘餘只列「巢狀獨立 Git repo / submodule 若自身被 Git 視為最上層會被接受」。另有一類**被接受、但不是獨立 repo** 的佈局沒列:`sub/.git` 為檔案且 `gitdir:` 指向上層 repo 的 gitdir、`GIT_DIR` 有設而 `GIT_WORK_TREE` 沒設、或上層 config 的 `core.worktree` 指向 sub —— Git 把 sub 解析成**同一個 repository** 的工作樹最上層,`--show-prefix` 為空、H1 形狀的副本可取得 head == worktree(第 4 節 E8、E9)。依 G9 判準(policy 存在於該 root 自己解析到的 HEAD)**不構成 F2**,所以只是措辭的涵蓋面不足,不是行為缺陷 | git 實測:`p/sub/.git`(內容 `gitdir: ../.git`)下 `--show-toplevel` = `<scratch>/g9/p/sub`、`--git-dir` = `<scratch>/g9/p/.git`、兩個 blob 皆 `30ed4d4…`;`--git-dir=<p/.git>` 而無 `--work-tree` 時 `--show-toplevel` = cwd | 否 |
| S5h-F4 | nit | G3 / G7 | `.claude/hooks/redlight.py:943-946`(`policy_state`:`head is None` ⇒ 只依工作樹有無分「未提交 / 未初始化」) | 本輪把「非最上層 root」定為明確不支援(⇒ unknown),但 status 沒有對應的狀態字:monorepo 子專案 `sub` 的 policy **已提交於上層 repo 的 `sub/.agents/evidence-policy.json`** 時,status 顯示「未提交」;操作者照字面再提交一次,畫面不會變,紅燈也不退。方向 fail-closed;與 S5g-F1 同型(永遠 unknown 而無正確訊號)。此標籤在 TARGET_G 對同一佈局也會出現(當時 `HEAD:<path>` 以 tree 根為基準同樣取不到),所以不是本輪引入,而是本輪把該佈局升格為「明確不支援」後仍沒有訊號 | 靜態閱讀 `:943-946`、`:868-869`;status.py 本輪未改(D.2) | 否 |

---

## 3. G1–G9 逐題結論與依據

### G1 判準等價性與 fail-closed —— **部分成立**

- **fail-closed 成立**:`redlight.py:729-733` subprocess 任何例外(含 git 不存在、timeout)⇒ False;`:734-735` returncode ≠ 0 ⇒ False;
  `:736` 只有 stdout strip 後恰為 `b""` 才 True。`os.fspath(root)` 在 try 內(`:730`)。
  空白目錄名不會被 strip 誤判:prefix 一律以 `/` 結尾(實測子目錄輸出 `sub/`),strip 後不可能為空。
- **等價性不成立**:`--show-prefix` 為空 ≠「root 是 Git 認定的工作樹最上層」。在 gitdir 內(bare 目錄、bare 子目錄、`.git/`、`.git/refs`)
  `--show-prefix` 同樣 exit 0、輸出空行,而 `--show-toplevel` exit 128、`--is-inside-work-tree` 為 `false`(第 4 節 E3、E4、E7)。⇒ S5h-F1。
- 對 S5g-F2 原形狀(普通子目錄)**封住**:實測 `p/sub` 輸出 `sub/`(E1),`_root_is_toplevel` False ⇒ `:868-869` 全 None、`:755-757` 全 None。

### G2 兩處都擋 —— **成立(附 S5h-F2)**

- `evidence_policy_facts`:`:868-869` 是 try 內第一步,在 `:870` 的 `rev-parse` 之前;回傳 `:865-866` 的全 None 7 鍵。
- `committed_blobs`:`:752` 迴圈前算一次 `top`;`:755-757` 非最上層 ⇒ 每個路徑都寫入 `{"worktree": None, "head": None}` 並 `continue`,不呼叫 `:759-760` 的 git。
  `paths` 預設 `BLOB_FILES`,所以 `config_file` 與 `ROOT_CONFTEST` 都有 None 記錄;verdict `:1119-1123` 對 None 判 unknown。
- `_committed_addopts`(`:825`)只在 `:887-888` 被呼叫,在 `:868-869` 之後,非最上層時走不到。
- 殘餘:`committed_blobs` 這一半沒有任何測試鎖住(S5h-F2)。

### G3 不變式未削弱 —— **成立**

- `git diff --name-only 8e77755…..ea6aba6…`(本審查自行執行,與 D.2 逐行相同)非 docs 檔只有 `.claude/hooks/redlight.py`、`tests/test_redlight.py`;
  `--stat` 為 `redlight.py | 25 +`、`test_redlight.py | 42 +`,`2 files changed, 67 insertions(+)`,**0 刪除**。
  ⇒ `tests/conftest.py`、`status.py`、`install.py`、`verify_gates.py` 皆未改。
- redlight.py 的 3 個 hunk(E.1 / E.3,與 `git show` 一致)只落在 `_root_is_toplevel` 新增、`committed_blobs` 與 `evidence_policy_facts` 內;
  `_completeness_problems`(`:1012-1065`)、`_completeness_verdict`(`:1068-1152`)、`_effective_policy`(`:970-994`)、`policy_state`(`:937-954`)、`content_hash` 都不在 hunk 範圍。
- 單一 `"true"` 出口:TARGET 全檔 grep `return "true"|== "true"` 只命中 `:1152`。
- 新增的兩段都只會把欄位改成 None ⇒ 只會多出 unknown,不會多出 true。
- blob 佐證:`S3H1:redlight.py` = `TARGET_G:redlight.py` = `0616c17239a388a9495fcccf3da6e514adae02ce`;`TARGET:redlight.py` = `d64d565653c5a0c28a2688a07dae44420e3095c7`(與 E.1 index 行一致)。

### G4 紅綠時序 —— **成立(依證據原文 + 紙上推演;未重跑)**

- 測試本體在 S3H1 與 TARGET 相同:兩者 `tests/test_redlight.py` blob 都是 `26da0b5ad3e6505c1bc0aecbb0d2853b92ad6af3`;`git diff --name-only 7621e3c…..ea6aba6…` 不含 tests。
- S3H1 上跑的是**修正前**程式:S3H1 的 redlight.py blob = TARGET_G 的 `0616c17…`。
- H1 在 S3H1 red,且失敗於 got == "true":REVIEW_HEAD `docs/audits/2026-10-04-m1a-station3h-redlight.md:61` `tests\test_redlight.py:2567: AssertionError`、`:68` `1 failed, 2095 passed, 3 skipped, 3 xfailed in 409.36s (0:06:49)`(`git grep` 原文,第 4 節 E0)。
  第 2567 行 = H1 的 `assert got != "true", got`(S3H1 檔案第 2550-2567 行,本審查讀過);包內 F.2 照錄的 `assert 'true' != 'true'` 與此一致。
- H2 在 S3H1 green:FAILED 清單只有 H1(F.2 第 67 行);摘要 1 failed。
- S4H1 後兩者 green:REVIEW_HEAD `docs/audits/2026-10-05-m1a-station4h-fix.md:121` `2096 passed, 3 skipped, 3 xfailed in 380.00s (0:06:19)`(0 failed),collected 2102 與 S3H1 相同。
- 紙上推演一致:修正前 H1 走到 `:1152`(S3H1 實得 `'true'`);修正後唯一差異是 `:868-869` 與 `:755-757` 對 `sub` 回 None ⇒ `:1099-1101` unknown ⇒ `!= "true"` 成立;H2 的 root 為最上層 ⇒ `:736` True ⇒ 與修正前同路徑 ⇒ `"true"`。

### G5 H1 / H2 是否測到 F2 形狀 —— **成立(附 S5h-F2)**

- `_g_default_root(parent)`(`tests/test_redlight.py:2216-2218` → `_g_root` `:2187-2213`)只在 `parent` 寫入並 `git add` `pyproject.toml`、`tests/conftest.py`、policy,`commit`。
- H1(`:2560-2565`)把三檔 `read_bytes` 複製到 `parent/sub/` 底下,**沒有任何 git add / commit** ⇒ 三份副本從未提交於 `sub/`。
- root = `sub`:`_g_coverage(sub)` → `_g_run` → `_isolated_conftest(monkeypatch, root)`(`:298-312`)把真實 conftest 的 `_ROOT` 設為 `sub`(`:306`),
  經真實 producer(`tests/conftest.py:410-412`)呼叫 `committed_blobs(_ROOT)` / `evidence_policy_facts(_ROOT)`。
- H1 在 S3H1 實得 `'true'` 本身就證明它重現了 identity 錯位可達 true 的形狀;我另在 git 層重現同一形狀(E1、E2:子目錄 hash = 上層 HEAD blob = `30ed4d4…`)。
- H2(`:2569-2576`)root 本身為 `git init` 的最上層、policy 已提交、worktree = HEAD ⇒ 斷言 `== "true"`,證明正常最上層不受影響。
- 弱點:H1 只斷言 `!= "true"`,不區分是哪一半擋下的(S5h-F2)。

### G6 5g 其他結論是否仍成立 —— **成立**

逐條見第 5 節。S5g-F1 / F3 / F4 / F5 仍未 machine-enforced,票與證據報告的追蹤項描述正確。

### G7 殘餘措辭與程式一致 —— **部分成立**

- 「monorepo 中、非 Git 最上層的普通子專案明確不支援(H1 鎖住)」:與程式一致(E1 `sub/` ⇒ False)。
- 「巢狀獨立 Git repo / submodule 若自身被 Git 視為最上層,`--show-prefix` 同樣為空、會被接受」:與程式一致(E10 submodule `--show-prefix` 為空、用 submodule 自己的 HEAD blob `75e2c15…`)。
- 措辭**沒有**宣稱「已拒絕所有巢狀 repo」,反而明寫「不得宣稱已拒絕或已支援」—— 這一點符合要求。
- 不一致處:「本輪檢查的語意是 `--show-prefix` 為空,**即** root 必須是 Git 認定的該 repository 最上層」—— 這個「即」不成立:gitdir / bare 內也被接受(S5h-F1);
  `redlight.py:727` docstring「root 是否就是 git 工作樹的最上層」同樣不成立。另有一類被接受的重新對應佈局未列(S5h-F3)。

### G8 跨平台 —— **成立**

- 最上層的 `--show-prefix` 原始位元組恰為 `\n`(1 byte,E1b `od -c`);`capture_output` 取的是 bytes,不經主控台編碼,CRLF 主控台無關;`:736` `strip()` 也涵蓋 `\r\n`。
- 路徑大小寫:以全大寫路徑 `git -C` 進入最上層,輸出仍為空;全大寫進入子目錄輸出 `sub/`(git 正規化成實際大小寫,E1c)。反斜線路徑進入最上層輸出為空(E1d)。
- `_ROOT` 為 `Path(__file__).resolve().parents[1]`(`tests/conftest.py:130`),已解析符號連結;root 自己含 `.git` 時 git 探索在 cwd 當層即命中,prefix 必為空,不會因 junction / subst 路徑字串差異誤回非空。
- 可能誤回 False 的情形:`safe.directory`「dubious ownership」⇒ returncode 128 ⇒ False ⇒ unknown。但同一情形下 `:870` / `:759-760` 的 git 本來就會失敗,TARGET_G 已是 unknown,**不是本輪造成的回歸**。
- POSIX:依 REVIEW_HEAD 票 145〈五十五〉55.3 照錄,H2 在 Linux 維持綠(裁決助手外部證據,本審查無法獨立核對)。

### G9 總問題(增量版)—— **不成立(找到反例)**

- 反例:root 位於 gitdir 內(S5h-F1)。git 原語層已確認(E3–E6),端到端需要重現。
- 其餘嘗試(submodule、`git worktree add`、`.git` 檔、`GIT_DIR` / `GIT_WORK_TREE`、`core.worktree`、大小寫、符號連結)依 G9 判準都不構成 F2,清單見第 4 節。

---

## 4. G9 反例嘗試清單

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

### 4.2 實驗原文(scratchpad 內臨時 repo;未匯入或執行本 repo 任何程式)

E0 —— 本 repo 唯讀查詢:

```
$ git grep -n -e committed_blobs -e _root_is_toplevel -e show-prefix ea6aba6452668982fee56f7a2f0faf2cd720ca6d -- tests .claude
ea6aba6452668982fee56f7a2f0faf2cd720ca6d:.claude/hooks/redlight.py:726:def _root_is_toplevel(root):
ea6aba6452668982fee56f7a2f0faf2cd720ca6d:.claude/hooks/redlight.py:727:    """root 是否就是 git 工作樹的最上層(`git rev-parse --show-prefix` 為空)。失敗 ⇒ False。"""
ea6aba6452668982fee56f7a2f0faf2cd720ca6d:.claude/hooks/redlight.py:730:        proc = subprocess.run(["git", "-C", os.fspath(root), "rev-parse", "--show-prefix"],
ea6aba6452668982fee56f7a2f0faf2cd720ca6d:.claude/hooks/redlight.py:739:def committed_blobs(root, paths=BLOB_FILES):
ea6aba6452668982fee56f7a2f0faf2cd720ca6d:.claude/hooks/redlight.py:752:    top = _root_is_toplevel(root)
ea6aba6452668982fee56f7a2f0faf2cd720ca6d:.claude/hooks/redlight.py:851:      4. `git hash-object <path>`(套用 .gitattributes,與 `committed_blobs` 同一手法)取 worktree blob;
ea6aba6452668982fee56f7a2f0faf2cd720ca6d:.claude/hooks/redlight.py:868:        if not _root_is_toplevel(root):
ea6aba6452668982fee56f7a2f0faf2cd720ca6d:tests/conftest.py:384:    `redlight.evidence_policy_facts`(與 `committed_blobs` 同一處,status 共用);本檔只擷取事實,不判定。
ea6aba6452668982fee56f7a2f0faf2cd720ca6d:tests/conftest.py:410:            "config_blobs": _redlight.committed_blobs(_ROOT),

$ git rev-parse 7621e3ce8604ab72ab2f3fb3257cb1181b8a126e:tests/test_redlight.py ea6aba6452668982fee56f7a2f0faf2cd720ca6d:tests/test_redlight.py 8e7775526e462d984abb0992ed74c1e1aa3648dd:.claude/hooks/redlight.py 7621e3ce8604ab72ab2f3fb3257cb1181b8a126e:.claude/hooks/redlight.py ea6aba6452668982fee56f7a2f0faf2cd720ca6d:.claude/hooks/redlight.py
26da0b5ad3e6505c1bc0aecbb0d2853b92ad6af3
26da0b5ad3e6505c1bc0aecbb0d2853b92ad6af3
0616c17239a388a9495fcccf3da6e514adae02ce
0616c17239a388a9495fcccf3da6e514adae02ce
d64d565653c5a0c28a2688a07dae44420e3095c7

$ git grep -n -e "1 failed, 2095 passed" -e "2096 passed, 3 skipped" -e "test_redlight.py:2567" 2f496b9d0a71d88995b2338c6b4440d693c9a879 -- docs/audits/2026-10-04-m1a-station3h-redlight.md docs/audits/2026-10-05-m1a-station4h-fix.md
2f496b9d0a71d88995b2338c6b4440d693c9a879:docs/audits/2026-10-04-m1a-station3h-redlight.md:61:tests\test_redlight.py:2567: AssertionError
2f496b9d0a71d88995b2338c6b4440d693c9a879:docs/audits/2026-10-04-m1a-station3h-redlight.md:68:1 failed, 2095 passed, 3 skipped, 3 xfailed in 409.36s (0:06:49)
2f496b9d0a71d88995b2338c6b4440d693c9a879:docs/audits/2026-10-05-m1a-station4h-fix.md:121:2096 passed, 3 skipped, 3 xfailed in 380.00s (0:06:19)

$ git diff --stat 8e7775526e462d984abb0992ed74c1e1aa3648dd..ea6aba6452668982fee56f7a2f0faf2cd720ca6d -- .claude tests
 .claude/hooks/redlight.py | 25 +++++++++++++++++++++++++
 tests/test_redlight.py    | 42 ++++++++++++++++++++++++++++++++++++++++++
 2 files changed, 67 insertions(+)

$ git diff --name-only 7621e3ce8604ab72ab2f3fb3257cb1181b8a126e..ea6aba6452668982fee56f7a2f0faf2cd720ca6d
.claude/hooks/redlight.py
docs/audits/2026-10-04-m1a-station3h-redlight.md
docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
```

佈置:`git version 2.53.0.windows.2`。以 Write 建 `<scratch>/g9/p/.agents/evidence-policy.json` 與 `<scratch>/g9/p/sub/.agents/evidence-policy.json`(內容相同:`{"policy": "committed-at-parent-root"}` + LF);
`git -C <scratch>/g9/p init -q`;`git -C <scratch>/g9/p add .agents/evidence-policy.json`(只加上層那份;輸出 `warning: in the working copy of '.agents/evidence-policy.json', LF will be replaced by CRLF the next time Git touches it`);
`git -C <scratch>/g9/p -c user.name=t -c user.email=t@example.invalid commit -q -m base`(無輸出)。

E1 —— 最上層與普通子目錄:

```
$ git -C "<scratch>/g9/p" rev-parse --show-prefix
(無輸出)
$ git -C "<scratch>/g9/p/sub" rev-parse --show-prefix
sub/
$ git -C "<scratch>/g9/p" rev-parse HEAD:.agents/evidence-policy.json
30ed4d4db34fbf419031f0b767ca2d2fdad693f4
$ git -C "<scratch>/g9/p/sub" hash-object .agents/evidence-policy.json
30ed4d4db34fbf419031f0b767ca2d2fdad693f4
```

(E2:上兩行即 S5g-F2 在 git 層的形狀 —— 子目錄未追蹤副本的 hash = 上層 HEAD blob。)

E1b —— 最上層輸出的原始位元組:

```
$ git -C "<scratch>/g9/p" rev-parse --show-prefix > "<scratch>/g9/prefix_top.bin"
(無輸出)
$ od -c "<scratch>/g9/prefix_top.bin"
0000000  \n
0000001
```

E1c / E1d —— 大小寫與分隔符(路徑以全大寫或反斜線傳入,使用者名稱亦遮為 `<user>` / `<USER>`):

```
$ git -C "C:/USERS/<USER>/APPDATA/LOCAL/TEMP/CLAUDE/C--PROJECTS-AGENT-GATES/92EFD092-A717-4320-A3C2-9E7EF9B3940D/SCRATCHPAD/G9/P" rev-parse --show-prefix
(無輸出)
$ git -C "C:\Users\<user>\AppData\Local\Temp\claude\c--projects-agent-gates\92efd092-a717-4320-a3c2-9e7ef9b3940d\scratchpad\g9\p" rev-parse --show-prefix
(無輸出)
$ git -C "C:/USERS/<USER>/APPDATA/LOCAL/TEMP/CLAUDE/C--PROJECTS-AGENT-GATES/92EFD092-A717-4320-A3C2-9E7EF9B3940D/SCRATCHPAD/G9/P/SUB" rev-parse --show-prefix
sub/
```

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

E4 / E5 —— 在 gitdir 內放未追蹤副本(以 Write 建 `<scratch>/g9/bare.git/.agents/evidence-policy.json`、`<scratch>/g9/p/.git/.agents/evidence-policy.json`,內容同上):

```
$ git -C "<scratch>/g9/bare.git" rev-parse HEAD:.agents/evidence-policy.json
30ed4d4db34fbf419031f0b767ca2d2fdad693f4
$ git -C "<scratch>/g9/bare.git" hash-object .agents/evidence-policy.json
30ed4d4db34fbf419031f0b767ca2d2fdad693f4
$ git -C "<scratch>/g9/p/.git" rev-parse HEAD:.agents/evidence-policy.json
30ed4d4db34fbf419031f0b767ca2d2fdad693f4
$ git -C "<scratch>/g9/p/.git" hash-object .agents/evidence-policy.json
30ed4d4db34fbf419031f0b767ca2d2fdad693f4
$ git -C "<scratch>/g9/bare.git" cat-file blob HEAD:.agents/evidence-policy.json
{"policy": "committed-at-parent-root"}
```

E6 —— bare repo 底下的普通子目錄(以 Write 建 `<scratch>/g9/bare.git/proj/.agents/evidence-policy.json`):

```
$ git -C "<scratch>/g9/bare.git/proj" rev-parse --show-prefix
(無輸出)
$ git -C "<scratch>/g9/bare.git/proj" rev-parse HEAD:.agents/evidence-policy.json
30ed4d4db34fbf419031f0b767ca2d2fdad693f4
$ git -C "<scratch>/g9/bare.git/proj" hash-object .agents/evidence-policy.json
30ed4d4db34fbf419031f0b767ca2d2fdad693f4
$ git config --get safe.bareRepository
Exit code 1
```

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

E8 —— `.git` 檔指向上層 gitdir(以 Write 建 `<scratch>/g9/p/sub/.git`,內容 `gitdir: ../.git`;另建 `<scratch>/g9/p2/sub/.git`,內容 `gitdir: ../../p/.git`,與 `p2/sub/.agents/evidence-policy.json`):

```
$ git -C "<scratch>/g9/p/sub" rev-parse --show-prefix --show-toplevel --git-dir
<scratch>/g9/p/sub
<scratch>/g9/p/.git
$ git -C "<scratch>/g9/p/sub" rev-parse HEAD:.agents/evidence-policy.json
30ed4d4db34fbf419031f0b767ca2d2fdad693f4
$ git -C "<scratch>/g9/p/sub" hash-object .agents/evidence-policy.json
30ed4d4db34fbf419031f0b767ca2d2fdad693f4
$ git -C "<scratch>/g9/p2/sub" rev-parse --show-prefix --show-toplevel
<scratch>/g9/p2/sub
```

E9 —— `GIT_DIR` / `GIT_WORK_TREE`(以 `--git-dir` / `--work-tree` 旗標代替環境變數,語意相同;以 Write 建 `<scratch>/g9/p/sub2/.agents/evidence-policy.json`):

```
$ git --git-dir="<scratch>/g9/p/.git" -C "<scratch>/g9/p/sub2" rev-parse --show-prefix --show-toplevel
<scratch>/g9/p/sub2
$ git --git-dir="<scratch>/g9/p/.git" --work-tree="<scratch>/g9/p" -C "<scratch>/g9/p/sub2" rev-parse --show-prefix
sub2/
```

E10 —— linked worktree 與 submodule:

```
$ git -C "<scratch>/g9/p" worktree add -q --detach "<scratch>/g9/wt"
(無輸出)
$ git -C "<scratch>/g9/wt" rev-parse --show-prefix --show-toplevel --git-dir HEAD:.agents/evidence-policy.json
<scratch>/g9/wt
<scratch>/g9/p/.git/worktrees/wt
30ed4d4db34fbf419031f0b767ca2d2fdad693f4
$ git -C "<scratch>/g9/wt" hash-object .agents/evidence-policy.json
30ed4d4db34fbf419031f0b767ca2d2fdad693f4
```

submodule 佈置:以 Write 建 `<scratch>/g9/q/.agents/evidence-policy.json`(`{"policy": "committed-in-submodule"}`);`git -C <scratch>/g9/q init -q`;`add`(同樣的 LF→CRLF warning);`commit -q -m q`;
`git -C <scratch>/g9/p -c protocol.file.allow=always submodule add -q <scratch>/g9/q mod`(輸出 `warning: in the working copy of '.gitmodules', LF will be replaced by CRLF the next time Git touches it`)。

```
$ git -C "<scratch>/g9/p/mod" rev-parse --show-prefix --show-toplevel --git-dir HEAD:.agents/evidence-policy.json
<scratch>/g9/p/mod
<scratch>/g9/p/.git/modules/mod
75e2c159b88f814607e8750d548e943b4e4d26c3
$ git -C "<scratch>/g9/p/mod" hash-object .agents/evidence-policy.json
75e2c159b88f814607e8750d548e943b4e4d26c3
```

---

## 5. 5g 結論是否仍成立

前提:增量只在 `redlight.py` 新增 25 行(`_root_is_toplevel` 與兩個函式內的提前返回),0 刪除;5g 所引行號在 TARGET 上整體下移(`:726` 之後 +13、`committed_blobs` 內 +17~、`evidence_policy_facts` 之後 +25),內容不變。

| 5g 項目 | 是否仍成立 | 依據 |
|---|---|---|
| G1 I-3 bootstrap | **成立**;「例外形狀見 S5g-F2」改為:普通子目錄已封住(`:868-869`),gitdir / bare 內仍存在(S5h-F1) | 內容只取 HEAD blob 的步驟原樣(`:870`、`:874`、`:876-877`、`:878`、`:881`) |
| G2 能力邊界 | 成立 | `policy_document_problems`(`:899-934`)、`_effective`(`:997-999`)未改 |
| G3 `committed_addopts` 合約 | 成立 | `_committed_addopts`(`:811-842`)、`addopts_overrides`(`:769-808`)未改;新增的提前返回讓 `committed_addopts` 在非最上層為 None ⇒ `:988-990` unknown,方向一致 |
| G4 override_ini(修法 B) | 成立 | conftest 未改(D.2);verdict `:1112` 未改 |
| G5 不變式 | 成立 | 單一 `"true"` 出口 `:1152`;新增碼只產生 None |
| G6 `committed_blobs` 逐路徑 | 成立;逐路徑各自 try 保留(`:758-765`),非最上層時改為逐路徑全 None(`:755-757`);例外形狀同 G1 的更新 | — |
| G7 status 行(部分成立) | 仍為部分成立;S5g-F1 未處理;另見 S5h-F4(非最上層無專屬狀態字) | `policy_state`(`:937-954`)、status.py 未改 |
| G8 安裝器 | 成立 | install.py 未改(D.2);`install.main` 對無 `.git` 目標 `git init` ⇒ 安裝器路徑產生的 root 為最上層,H2 形狀 |
| G9 verify_gates(殘餘可接受) | 成立 | verify_gates.py 未改;淨室 root 為 `git init` 的最上層 ⇒ 正二不受新檢查影響(REVIEW_HEAD 證據:正二 `file_coverage=true`) |
| G10 測試授權與紅燈鏈 | 成立(本輪部分:S3H1 只在檔尾追加 42 行、S3H1→TARGET 未改測試,見 G4) | blob `26da0b5…` 兩處相同 |
| G11 manifest | 成立 | manifest 不在 D.2 |
| G12 跨平台 | 成立 | `hash-object` 手法未改;新增判準跨平台見 G8 |
| G13 總問題 | 第 4 節 #24 由「可得 true」變為「擋」;**新增**一條仍可得 true 的形狀(S5h-F1)。5g 的「未找到反例」結論在其範圍內不受影響 | — |
| S5g-F1 | 仍存在,未 machine-enforced;追蹤項描述正確 | `policy_state` 未改 |
| S5g-F3 | 仍存在,未 machine-enforced | `_committed_addopts` `:832-836` 未改 |
| S5g-F4 | 仍存在,未 machine-enforced;最上層 root 時 clean filter 手法照舊 | `:759`、`:874` 仍為 `hash-object` |
| S5g-F5 | 仍存在,未 machine-enforced | verify_gates.py 未改 |

---

## 6. 審查限制

1. **沒有跑任何 pytest、verify_gates.py、status.py**(依規則)。H1 / H2 紅綠、全套摘要、淨室五情境、帳本不變,全部依 REVIEW_HEAD 的證據原文與紙上推演。
2. S5h-F1 的**端到端** `"true"` 未實跑;結論是「三個 git 原語在 gitdir 內的行為已實測」+「其餘條件與 H1 相同」的推演。推演有一處未驗:pytest 在 bare 目錄 / `.git/` 底下作為 rootdir 時,conftest 其他事實(plugins、inipath 正規化等)是否與 H1 完全相同 —— 我判斷相同(都不依賴 git),但未證明。
3. S5h-F2 的「刪 `:755-757` 後 H1 仍綠」是推演,未做突變測試。
4. 實驗只在 Windows、git 2.53.0.windows.2;POSIX 與其他 git 版本未驗。`safe.bareRepository=explicit` 會擋住 #4(bare 子目錄的隱式探索),對 #3、#5 是否也擋未實驗。
5. 符號連結情形(#14、#15)與 `core.worktree`(#13)未實驗,只依程式與 git 語意推論。
6. 未確認 git hook 執行 pytest 時 `GIT_DIR` 是否被匯出;#11 依 G9 判準本就不構成 F2,只影響 S5h-F3 的措辭。
7. 裁決助手的 Linux 預演與 POSIX 外部驗收屬非本 repo 帳本證據,無法獨立核對。
8. 讀碼範圍:TARGET 的 `redlight.py` 第 680–1153 行、`tests/conftest.py` 相關呼叫點、`tests/test_redlight.py` 的 helper 與 H1 / H2;未讀 status.py 與 install.py 本體(本輪未改)。未讀 pytest / Python 原始碼(本輪判斷不需要)。
9. scratchpad 內留有臨時 repo `<scratch>/g9/`(含 `p`、`p2`、`q`、`bare.git`、`wt`),與本 repo 無關。
