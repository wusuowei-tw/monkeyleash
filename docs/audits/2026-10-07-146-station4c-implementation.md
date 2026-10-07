# 票 146 第四站 4c 實作審計(S4c-146-1)—— 推送前修正 N-1～N-4

- 日期:2026-10-07
- 實作 commit(commit 1):`98099bae297b68e5c6cd4787ea8474d3f400ccc0`
- 基準 HEAD:`adc3ef572f9d3b0392eb0565fa2724b08646d3e5`(S3h-146-1 紅燈)
- 契約：票 146〈3h 契約與紅燈(N-1～N-4)〉+〈第四站 4c 實作(S4c-146-1)〉的 Jeff 裁決 (1)(2)(3)。

## 1. 改動摘要(只改兩個 production 檔;測試、policy、redlight 未動)

### `.claude/hooks/gate.py`

- **N-1**:`_staged_names_all` 的指令改為 `git diff --cached --name-only -z --no-renames`,docstring 記明理由。
- **N-2**:`check_extension_integrity` 非 policy-only 路徑,(a) 之後、(b)(c)(d) 之前新增 (a′):
  - `report["facts"]` 不是 dict 或 `state != "ok"` ⇒ `hard_block = "[R10/fail-closed] allowlist_state：allowlist <state>；本次無法判定"`,直接 return;
  - 在 `mode_pre_commit` 的影子分支之前生效(沿用既有硬擋路徑);
  - report 的 state / category 未改(redlight 不動)。

### `.claude/portable/verify_gates.py`

- **N-3**:
  - 新增 `_FILE_ATTRIBUTE_REPARSE_POINT = 0x400`、`_is_reparse(path)`。POSIX 用 `islink`;Windows 另看 lstat 的 `st_file_attributes`。不存在 ⇒ False;其他 lstat 失敗照常拋出。
  - 新增 `_reparse_or_exit(path, what)`:lstat 失敗或是 reparse ⇒ SystemExit。
  - `_require_isolation`:新增兩項檢查。
    - `realpath(claude_root) == join(realpath(home), ".claude")`(normcase 比較);
    - home / claude_root / marker 任一 `_is_reparse` ⇒ SystemExit。
  - `restore_user_layer`:`_require_isolation` 之後做全樹預檢。
    - `os.walk(topdown=True, followlinks=False, onerror=errors.append)`;
    - 每層先對 dirnames + filenames 逐一 lstat,再判 `_is_reparse`,失敗或是 reparse ⇒ SystemExit("未刪除任何內容");
    - `dirnames[:]` 原地剪成「非 reparse 的目錄」;
    - 列舉錯誤 ⇒ SystemExit;
    - 預檢全過才進原本的刪除迴圈。
- **N-3′**:`isolated_home` 在既有型別檢查中，對已存在的 home、home/.claude 呼叫 `_reparse_or_exit`。
  - 位置在任何 `makedirs`、marker 寫入、環境變數修改之前。
  - marker 原本就是「以任何型別存在 ⇒ SystemExit」,不另加。
- **N-4**:
  - 新增 `SCENARIO_TRIGGER_R10 = "docs/adr/verify-trigger-r10.md"`;`scenario_r10` 改寫此檔，內容與正控 trigger 不同。
  - `run_scenario` 對 commit 型情境：在 `git add -A` 之後、commit 之前執行 `git diff --cached --name-only`;為空 ⇒ `restore(target)`(iso 非 None 時再 `restore_user_layer(iso)`),回 `(False, "情境 staged 為空：" + code)`,不 commit。
  - R10 判定句不變(rc + marker + reason)。

### 詮釋點

- (i) staged 為空的提早返回，除契約寫的 `restore(target)` 之外，在 iso 非 None 時也呼叫 `restore_user_layer(iso)`,與正常路徑的清理對稱;測試以替身吸收，不影響斷言。
- (ii) 正控 commit 前不做 staged 檢查(契約只寫「情境」)。正控寫的是 HEAD 中不存在的 trigger。

## 2. 對應 node

| 契約 | node |
|---|---|
| N-1 | T146-80、T146-80b |
| N-2 | T146-81[uninitialized / worktree_differs / malformed];正控 T146-81d |
| N-3 | T146-82、82b、82c、82d、82e;T146-51b[vi-home-symlink](junction) |
| N-3′ | T146-50b[home-is-symlink](junction) |
| N-4 | T146-83、83b、83d;T146-53b(准改);回歸鎖 T146-83c;T146-55 六案(准改替身) |

Jeff 裁決 (1):**正控 81d、回歸鎖 83c**。

## 3. 4c-2 前檢(工作樹;前檢證據)

### 3.1 工作樹 pytest

`python -X utf8 -m pytest -q -rs` ⇒ `2326 passed, 10 skipped, 3 xfailed in 260.98s`(0 failed、ERROR 0)。

10 skipped 全為 Windows 平台限制:

- `tests/test_gate.py:451 / :459 / :473`:此環境無法建立 symlink;
- `tests/test_redlight.py:2673`:Windows 檔名不得含 LF;
- `:3074`、`:3702` ×3、`:3752`:Windows 建 symlink 需要額外權限;
- `:3505`:chmod 000 在 Windows 不會讓目錄不可列舉。

### 3.2 淨室(`python -X utf8 .claude/portable/verify_gates.py <scratchpad>/vg-4c`;rc 0)

```
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
```

- 權威層偵測三項 ✓;新 repo 框架測試 `2176 passed, 14 skipped, 3 xfailed`;evidence 五情境皆「成立 ✓」。
- **R10 情境 staged 非空的證據**:
  - 程式結構:`run_scenario` 在 staged 為空時回 `"情境 staged 為空"` 而不 commit,所以出現「R10 擋下 ✓」就代表 staged 檢查已通過。
  - 唯讀觀測：目標 repo 的 `git log --oneline --name-status -2` 最上面是 `639e0cd verify R10 precontrol`(`M .dev/pipeline.json`、`A docs/adr/verify-trigger.md`),HEAD 樹中沒有 `docs/adr/verify-trigger-r10.md`;情境寫入該新檔 ⇒ `git add -A` 後 staged 非空。
- 結束後 `vg-4c/home/` 有 `.claude/`(空)與 `.verify-gates-isolated`(32 bytes)。

### 3.3 本機 report(唯讀;production 唯讀觀測真實使用者層)

`check_extension_integrity([])` 的結果:

- `hard_block None`、`violations []`、`policy_source 'head'`、`state 'DECLARED_OK'`;
- facts blob `40dec504c85cfca3910d2d85fc446cc9af791510`(ok)、inventory blob `c2b42dec0e1b8ec6ac93222ea6e06d067ba2b871`(ok);
- `synced.verified True`、`surfaces.errors []`;
- status 兩行與 `report["lines"]` 一致。

### 3.4 pre-commit 乾跑

- L1:`.claude/hooks/gate.py`、`.claude/portable/verify_gates.py`、`docs/tickets/framework-updates/146-claude-code-enforcement-integrity.md`,加上已有未提交變動的 `.dev/gate-exemptions.jsonl`。
- `git diff --cached --name-only`(乾跑前與乾跑後各一次)皆為 `.claude/hooks/gate.py`、`.claude/portable/verify_gates.py`、`.dev/gate-exemptions.jsonl`、`docs/tickets/framework-updates/146-claude-code-enforcement-integrity.md`,與 L1 一致。
- 乾跑 rc 0,輸出只有 `[R2/自我修改豁免] .claude/hooks/gate.py:閘門自身,不受站別限制 —— 已記錄。`(三行);沒有 `[R10`。
- 乾跑追加 1 筆豁免 ⇒ 再 add(294 → 295 行)。

## 4. commit 1 與正式結果

- `git diff --cached --check`:無輸出。
- commit 1 經 hook 提交:`98099ba…`,4 files changed, 115 insertions(+), 5 deletions(-)。
- 提交後 `git status --porcelain` ⇒ ` M .dev/gate-exemptions.jsonl`(commit 1 自己的 hook 追加 1 筆,295 → 296,留給 commit 2)。
- 正式結果(committed HEAD `98099ba…`):`python -X utf8 -m pytest -q -rs` ⇒ `2326 passed, 10 skipped, 3 xfailed in 250.24s`,與 3.1 數字相同;skipped 10 行逐字相同。
- 帳本只追加(`head -c` 上一輪長度的前綴後 sha256):
  - `test-runs.jsonl` 前 1150184 bytes ⇒ `138f9ce50cd7daa00878b0225beee96a5e574140176528b75d917441d65be563`(= 上一輪 LC);現長 1173222 bytes,整檔 `d9d3ffd5ceee0168c16c06d2a068eed99c2b4ea497ee32a280d5cbd311b21a24`。
  - `test-sessions.jsonl` 前 32015327 bytes ⇒ `02acecfa74cd3349486515dc044a1b96e92b5371b091c6c5823014ed70e8aac0`(= 上一輪 LC);現長 33635395 bytes,整檔 `6d6ec88ca7a3c5606ec29a5079a54b167cbf8eecd8aaf779ded3b4ee3fe7e23c`。

## 5. 豁免帳本新增行(欄位原樣;不含使用者路徑)

隨 commit 1 進版(292 → 295):

```
{"ts": "2026-10-07T18:48:45.642763+00:00", "file": ".claude/hooks/gate.py", "module": "gate", "ticket": "146", "stage": "implement", "declared_in": "0004", "reason": "gate-self-modification", "tool": "Edit", "outcome": "granted", "blocked_by": null, "at_commit": false, "content_hash": "63f76a5b1f4546cb8ada21d2ace012789368fb5fc5bec3877937c4c7380c8164", "result_hash": "20acea4c5ae37ad3c5ae922615dd9f0536431c7c07591b066ac12ddc76474078", "changes_bytes": true}
{"ts": "2026-10-07T18:48:49.831074+00:00", "file": ".claude/hooks/gate.py", "module": "gate", "ticket": "146", "stage": "implement", "declared_in": "0004", "reason": "gate-self-modification", "tool": "Edit", "outcome": "granted", "blocked_by": null, "at_commit": false, "content_hash": "20acea4c5ae37ad3c5ae922615dd9f0536431c7c07591b066ac12ddc76474078", "result_hash": "d167456ab50ce976c2a40d9a1a4c8633b8f93215a1529fd6a57741e558b08d36", "changes_bytes": true}
{"ts": "2026-10-07T19:00:38.843962+00:00", "file": ".claude/hooks/gate.py", "module": "gate", "ticket": "146", "stage": "implement", "declared_in": "0004", "reason": "gate-self-modification", "tool": "pre-commit", "outcome": "granted", "blocked_by": null, "at_commit": true, "content_hash": "d167456ab50ce976c2a40d9a1a4c8633b8f93215a1529fd6a57741e558b08d36", "result_hash": null, "changes_bytes": null}
```

隨 commit 2 進版(commit 1 的 hook 追加，295 → 296):

```
{"ts": "2026-10-07T19:00:50.726404+00:00", "file": ".claude/hooks/gate.py", "module": "gate", "ticket": "146", "stage": "implement", "declared_in": "0004", "reason": "gate-self-modification", "tool": "pre-commit", "outcome": "granted", "blocked_by": null, "at_commit": true, "content_hash": "d167456ab50ce976c2a40d9a1a4c8633b8f93215a1529fd6a57741e558b08d36", "result_hash": null, "changes_bytes": null}
```

## 6. Jeff 裁決(2026-10-07)

(1) T146-83c 在 BASELINE 已綠(C0 已列綠),定位為「既有行為回歸鎖」,不改測試;審計與票面記為「正控 81d、回歸鎖 83c」。
(2) 契約增補 N-3′:verify_gates.isolated_home 必須在任何建立目錄、寫入 marker 或修改環境變數之前，檢查所有已存在的 home、home/.claude、marker:除既有型別檢查外,lstat 為 symlink 或 _is_reparse 為真 ⇒ SystemExit(不建立任何東西、環境不變)。由既有 T146-50b[home-is-symlink] 驗收，不新增測試。
(3) T146-53b 用 getattr 取常數(該檔無 _api)屬可接受偏離，審計記明。

⇒ 依 (3):T146-53b 以 `getattr(vg, "SCENARIO_TRIGGER_R10")` 取常數(3h 審計 §2 已記)。

## 7. 待裁 / 未驗

- POSIX 未驗:symlink 版的 T146-82 系列與 50b / 51b 在 POSIX 走 `os.symlink` 分支;本輪只有 Windows(junction)實跑。
- CI 未跑(未 push)。
- 獨立審查的其餘後補項(審查檔 §5:(h) 第 2 項例外硬擋 node、N-6、`index_unreadable` node、(h) 第 7 / 9 項、N-5、(h) 其餘、N-8)不在本輪範圍，仍待排。
- 第六站是否進入：待 Jeff 裁定。
