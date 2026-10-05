# 票 145 M1-a Station 5i 增量獨立審查報告(只審 3i / 4i)

- 審查日期:2026-10-05
- 審查者:全新對話;未參與任何實作,未讀任何本機對話紀錄。
- 判斷來源:審查包 `docs/audits/2026-10-05-m1a-station5i-review-package.md`(S5i-0)、以完整 SHA 取得的 repo 內容、本機 git 2.53.0.windows.2 在 session scratchpad 內的臨時 repo 實驗。未跑 pytest / verify_gates.py / status.py。
- 行號一律以 TARGET `8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8` 為準。`<scratch>` = 本 session 的 scratchpad 目錄;本機使用者名稱寫為 `<user>`。

---

## 0. 身分與第 0 步原文

| 代號 | 完整 SHA |
|---|---|
| S5i-0(審查包所在 commit) | `55147ca78576a2eef8472b6761f50ff5b9c42b5c` |
| TARGET(S4I1) | `8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8` |
| TARGET_H | `ea6aba6452668982fee56f7a2f0faf2cd720ca6d` |
| REVIEW_HEAD(S4I4) | `36c978e1c20a51d40cac777dd5aee58625f97032` |
| S3I1 | `260ede30628c7d205b30ac12c94be73a75cd2812` |

第 0 步(各自單獨執行):

```
$ git status --porcelain
 M docs/agents/friction-log.md
?? docs/tickets/framework-updates/146-claude-code-enforcement-integrity.md
?? docs/tickets/framework-updates/147-turn-end-check-via-settings-stop-hook.md
```
→ 恰為 3 個外來變更(未讀、未碰)。

```
$ cat .dev/pipeline.json
{
  "current_stage": "review",
  "feature": "framework-updates",
  "ticket_id": "145",
  "updated": "2026-10-05"
}
```

```
$ git rev-parse 55147ca78576a2eef8472b6761f50ff5b9c42b5c:docs/audits/2026-10-05-m1a-station5i-review-package.md
fd6aadf7fe44ce5eaa3eb6abf85c6b45cc5d1275
$ git hash-object docs/audits/2026-10-05-m1a-station5i-review-package.md
fd6aadf7fe44ce5eaa3eb6abf85c6b45cc5d1275
$ sha256sum docs/audits/2026-10-05-m1a-station5i-review-package.md
e6033f0e8aeb9d64c24cd05f49a30d6302235f38d6297fb082947f3edd8d8c1f *docs/audits/2026-10-05-m1a-station5i-review-package.md
```

全部與預期相符 ⇒ 繼續審查。

**閘門攔截(照錄;依規則停手,未繞過、未換工具)**:審查中在 scratchpad 臨時 repo 內嘗試以 Bash 重導向寫一個假 policy 檔,被 R7 前哨擋下:

```
$ echo '{"schema":1}' > "<scratch>/g/p/.agents/evidence-policy.json"
PreToolUse:Bash hook error: [python "$CLAUDE_PROJECT_DIR/.claude/hooks/gate.py"]: [六站閘門/前哨] [R7][enforce] 這個 Bash 指令會寫到沒有被許可的位置((引號或跳脫使目標無法可靠切分))。
     **許可是逐段比對的**(`&&` / `;` / `||` 各算一段)。
     而**沒有任何一段在清單裡** —— 不是某一段的問題,整條要換寫法。
     請改用 Write / Edit。
     理由不是風格:從指令字串解析『寫到哪』解不完,而半套的解析器
     比零涵蓋更危險 —— 零涵蓋你知道它是零。所以入口收成一個,
     走檔案工具的話 R1–R6 全部適用。
     例外(附理由)在 gate.py 的 BASH_ALLOWED_CMDS / BASH_ALLOWED_TARGETS。
     指令裡出現 /dev/null **不會**讓其他寫入一起免檢。
(R7 只活在前哨:commit 看得到檔案內容,看不到你用什麼工具寫的。
 繞過前哨就沒有第二道了 —— 見 docs/adr/0008)
```

處置:沒有改用 Write 或其他方式寫那個檔(本輪 Write 只准用於本報告)。之後只做**不需要寫檔內容**的 `git init` / `mkdir` / `git config` / `git rev-parse` 實驗(第 4 節 X 系列)。因此第 4 節沒有「blob 相等」層級的實驗,只有 `rev-parse` 判準層級的實驗;blob 層級沿用 5h 的 E 系列。

---

## 1. 判決

**FAIL**(blocker 0、major 1、minor 0、nit 2)。

FAIL 的唯一原因是 S5i-F1:4i 把 `proc.stdout.strip() == b""` 換成 `split(b"\n")` 後只看 `lines[1]`,而 `--show-prefix` 輸出的是**未跳脫的原始路徑位元組**。在允許檔名含換行的檔案系統(Linux / macOS)上,名稱以換行開頭(前面可有空白)的子目錄,prefix 的第一行 strip 後為空 ⇒ `_root_is_toplevel` 回 True ⇒ 回到 S5g-F2 的原形狀(子目錄 root、上層 HEAD blob = 子目錄副本)⇒ 預期 `file_coverage == "true"`。**TARGET_H 對同一輸入回 False**(整段 strip 後剩 `sub/`),所以這是本輪引入的回歸。

**嚴重度的判斷依據與替代選項(給裁決者)**:

- A(本報告採用):判 **major** ⇒ FAIL。理由:這是同一條 I-3 位置不變式、同一種 identity 錯位、方向是 fail-open;而且是**本輪的修正把 TARGET_H 已封住的輸入重新打開**。〈五十三〉53.3 裁決 1 與〈五十七〉57.3 裁決 1 的先例,都是「只有手動佈局才會產生」也定為 FAIL 等級。
- B:判 **minor**(佈局比 gitdir 內更不自然:要有名稱以換行開頭的目錄,而且 Windows NTFS 根本建不出來)⇒ 本輪 PASS,S5i-F1 列追蹤項。代價:`redlight.py:727-729` docstring「任一查詢失敗或條件不符 ⇒ False」與殘餘措辭「明確不支援(⇒ unknown):monorepo 中非最上層的普通子目錄」在 POSIX 上都不成立,錯的方向是 fail-open。
- 修法成本(供比較,不是本報告的要求):在 `:739-742` 改成完整比對,例如 `proc.stdout.replace(b"\r\n", b"\n") == b"true\n\n"`;或要求 `len(lines) == 3 and lines[2] == b""`,且 `lines[1]` 只去掉 `\r`、不做 `strip()`。任何一種寫法,TARGET_H 那種「整段 strip」的保護也就一起回來了。

---

## 2. Findings 表

| 編號 | 嚴重度 | 對應 G 題 | TARGET 檔名:行號 | 具體失敗情境(輸入 → 錯誤結果) | 依據 | 需要重現 |
|---|---|---|---|---|---|---|
| S5i-F1 | **major** | G9 / G2 / G1 / G8 | `.claude/hooks/redlight.py:739-742`(`split(b"\n")` 後只比 `lines[0]` / `lines[1]`,`lines[2:]` 完全不看);`:727-729` docstring;呼叫點 `:758`(`committed_blobs`)、`:874`(`evidence_policy_facts`)→ `:876` `HEAD:<POLICY_FILE>` / `:880` `hash-object <POLICY_FILE>`、`:765-766`;`tests/conftest.py:410-412` | POSIX 檔案系統。Git 最上層 `parent` 已提交合法 policy、`pyproject.toml`、`tests/conftest.py`;root = `parent/"\nsub"`(名稱以 LF 開頭的子目錄;或名稱恰為 `"\n"`、`" \n…"`、`"\t\nX"`),三份位元組相同的副本只在 root 下、從未提交。`git -C <root> rev-parse --is-inside-work-tree --show-prefix` 預期輸出 `true\n\nsub/\n` → `lines = [b"true", b"", b"sub/", b""]` → `lines[0] == b"true"` 且 `lines[1].strip() == b""` ⇒ **True** → `HEAD:<path>` 取上層 tree 根的 blob、`hash-object <path>` 讀 root 底下的副本 → head == worktree → 其餘條件與 H1 相同 ⇒ 預期 `file_coverage == "true"`。**TARGET_H 同一輸入**:`b"\nsub/\n".strip() == b"sub/"` ≠ `b""` ⇒ False ⇒ unknown。⇒ 本輪引入的回歸,重新打開 S5g-F2 原形狀 | (1) 程式:`:739-742`。(2) 實測(第 4 節 X3):`--show-prefix` 輸出原始位元組、不做 C 式引號跳脫 —— 目錄 `中` 的輸出是 `true\n` + `344 270 255 /\n`,不是 `"\344\270\255/"`;因此名稱裡的 LF 會原樣輸出。(3) 正常最上層 `true\n\n`(X1)、子目錄 `true\nsub/\n`(X2)的行結構與推演一致。(4) Windows NTFS 不允許檔名含控制字元,所以本機無法建出這個佈局 | **是**。git 原語層最小重現(POSIX):`mkdir -p "p/$(printf '\nsub')"`,然後 `git -C "p/$(printf '\nsub')" rev-parse --is-inside-work-tree --show-prefix > out`,`od -c out`;預期 `t r u e \n \n s u b / \n`。端到端:沿用 H1(`tests/test_redlight.py:2560-2567`),把 `sub = parent / "sub"` 改成 `sub = parent / "\nsub"`;預期 TARGET 得 `"true"`、TARGET_H 得非 `"true"` |
| S5i-F2 | nit | G7 / G9 | 殘餘措辭(REVIEW_HEAD `docs/audits/2026-10-05-m1a-station4i-fix.md` 第 7 節第 3 點;票 145〈五十九〉59.2);`.claude/hooks/redlight.py:727-728` docstring | 措辭把「位於 gitdir 或 bare repository 內的 root(I1 / I2)」列為**無條件的**「明確不支援(⇒ unknown)」。實測有兩種情況,root 就在 gitdir 內,Git 卻回報 `--is-inside-work-tree=true` 且 prefix 為空,所以會被接受:(a) 環境有 `GIT_DIR=<p/.git>`、沒有 `GIT_WORK_TREE`,cwd = `p/.git`(X9:`true`、空、`--show-toplevel` = `p/.git`);(b) 該 repo 的 `core.worktree` 指向它自己的 gitdir(X8:`r/.git` 得 `true`、空、toplevel = `r/.git`)。這兩種都是 Git 自己把 gitdir 當成工作樹,依 G9 判準(policy 在該 root 自己解析到的 HEAD)**不構成 F2**;而且措辭後半的「GIT_DIR / … core.worktree 等重新對應佈局 … 會被接受」已經涵蓋。所以這只是前後兩句重疊、前一句寫成了無條件 | X8、X9 原文(第 4 節) | 否 |
| S5i-F3 | nit | G5 | `tests/test_redlight.py:2600-2629`(I1 / I2 只斷言 `!= "true"`);全樹沒有直接呼叫 `_root_is_toplevel` 的測試(`git grep` 原文見第 4 節 X0) | (a) I1 / I2 跟 H1 一樣只斷言 `!= "true"`,區分不出「是 `_root_is_toplevel` 擋的」還是「別的條件剛好 unknown」。(b) I2 靠的是隱式 bare 探索:如果環境設了 `safe.bareRepository=explicit`,git 直接失敗,I2 會在修正前也綠(空洞地通過)。本輪 S3I1 的實跑紅燈已證明預設環境下形狀成立,所以不影響 G4。(c) 沒有任何測試直接鎖住 `:739-742` 的解析,所以 S5i-F1 這種只在解析層出錯的回歸,現有測試看不到 | 靜態閱讀;X0 | 否 |

---

## 3. G1–G9 逐題結論與依據

### G1 修正是否封住 S5h-F1、是否 fail-closed —— **部分成立**

- **S5h-F1 的形狀已封住**:`:732-734` 一次呼叫 `rev-parse --is-inside-work-tree --show-prefix`;在 `p/.git`、`bare.git`、`bare.git/proj`、`p/.git/refs` 實測第一行都是 `false`(X4、X5–X7)⇒ `:742` 的 `lines[0].strip() == b"true"` 不成立 ⇒ False ⇒ `:761-763` 逐路徑全 None、`:874-875` 全 None 7 鍵。
- **fail-closed 的分支成立**:`:731-736` subprocess 任何例外(含 git 不存在、timeout、`os.fspath` 失敗)⇒ False;`:737-738` returncode ≠ 0 ⇒ False;`:740-741` `len(lines) < 2` ⇒ False。`proc.stdout` 是 bytes(`capture_output=True`,沒有 `text=`),所以 `split(b"\n")` 不會出現型別例外。
- **「任一條件不符 ⇒ False」不完全成立**:`:742` 只看 `lines[1]`,`lines[2:]` 不看。prefix 本身含 LF 時,「prefix 為空」這個條件實際上不符,函式卻回 True ⇒ S5i-F1。

### G2 stdout 解析的健壯性 —— **部分成立(附 S5i-F1)**

- **正常最上層不會被誤判成 False**:
  - 實測原始位元組 `t r u e \n \n`(X1,`od -c`)⇒ `[b"true", b"", b""]` ⇒ True。
  - CRLF:Git for Windows 的 stdout 實測只有 LF(X1–X4 的 `od -c` 都沒有 `\r`)。即使某個環境輸出 `\r\n`,`lines[0].strip()` / `lines[1].strip()` 也會去掉 `\r` ⇒ 仍是 True。
  - 尾端多一個換行:多出來的元素落在 `lines[2:]`,不影響判斷。
  - 舊版 git 在最上層如果不印 `--show-prefix` 的空行(輸出只有 `true\n`):`[b"true", b""]`,`len == 2` ⇒ 仍是 True。本機只有 2.53.0,這一點是推演。
- **不健壯的地方**:`lines[1].strip()` 會把「prefix 第一行」當成「整個 prefix」。prefix 是原始路徑、可以含 LF(X3 證明輸出沒有跳脫)⇒ 非最上層可能被誤判成 True(S5i-F1)。方向是 **fail-open**,不是封死正常 host。
- 空白開頭的目錄名(` sub`):prefix ` sub/`,strip 後是 `sub/` ⇒ False,正確。只有 `\r`(`"\r"` 目錄):prefix `\r/`,strip 後是 `/` ⇒ False,正確。出問題的只有「第一個路徑成分是(可帶空白的)LF 開頭」這一類。

### G3 不變式未削弱 —— **成立**

- `git diff --stat ea6aba64…..8154a1ac…` 原文(本審查自行執行):非 docs 檔只有 `.claude/hooks/redlight.py | 12 +-`、`tests/test_redlight.py | 72 ++`。與 D.2 的 name-only 清單逐項相同 ⇒ `tests/conftest.py`、`status.py`、`install.py`、`verify_gates.py` 都沒有改。
- `git diff ea6aba64…..8154a1ac… -- .claude/hooks/redlight.py` 原文只有一個 hunk `@@ -724,16 +724,22 @@`,完全落在 `_root_is_toplevel`(`:726-742`)內。`committed_blobs`(`:745-772`)、`evidence_policy_facts`(`:851-897`)、`_effective_policy`(`:976-1000`)、`_completeness_problems`(`:1018-1071`)、`_completeness_verdict`(`:1074-1158`)、`policy_state`(`:943-960`)、`content_hash` 都不在 hunk 內。
- 呼叫點不變:`git grep` 只命中 `:758` 與 `:874` 兩處(X0)。單一 `"true"` 出口 `:1158`(TARGET_H 的 `:1152` + 6)。
- TARGET → REVIEW_HEAD 只改 docs(`git diff --name-only` 原文:`docs/audits/2026-10-05-m1a-station4i-fix.md`、`docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md`)。
- 附註:不變式的**程式結構**沒有被削弱,但判準本身在 POSIX 上比 TARGET_H 寬鬆(S5i-F1)。這一點歸在 G9 / G2,不重複計入。

### G4 紅綠時序 —— **成立(依證據原文 + blob 比對;未重跑)**

- blob 比對(本審查執行):`S3I1:tests/test_redlight.py` = `TARGET:tests/test_redlight.py` = `1b4869417c6318cf87c3d631781702afada3ebfc` ⇒ 3i 到 4i 之間測試沒有改。`S3I1:.claude/hooks/redlight.py` = `TARGET_H:.claude/hooks/redlight.py` = `d64d565653c5a0c28a2688a07dae44420e3095c7` ⇒ S3I1 上跑的是**修正前**的程式。
- S3I1 上:I1 / I2 失敗於 `assert 'true' != 'true'`,位置 `tests\test_redlight.py:2613` / `:2629`(審查包 F.2 原文)。TARGET 檔案第 2613 行、第 2629 行正好是 I1 / I2 的 `assert got != "true", got`(本審查 grep 確認)。FAILED 只有這兩支;摘要 `2 failed, 2097 passed, 3 skipped, 3 xfailed`;I3 / H1 / H2 在 passed 之內。
- S4I1 上:`2099 passed, 3 skipped, 3 xfailed`、0 failed、collected 2105(F.1 第 2 節原文)⇒ I1 / I2 由紅轉綠,I3 / H1 / H2 維持綠。
- 紙上推演一致:修正前,`.git` / bare 內的 `--show-prefix` 是空的 ⇒ True ⇒ 走到 `"true"`。修正後第一行是 `false` ⇒ False ⇒ unknown。I3 的 `sub` 在兩版都是 `sub/` ⇒ False。
- 限制:沒有重跑;POSIX 的紅綠是裁決助手的外部證據,本審查無法獨立核對。

### G5 三支測試是否真的測到宣稱的形狀 —— **成立(附 S5i-F3)**

- I1(`tests/test_redlight.py:2600-2613`):`parent = _g_default_root(...)`(`:2216-2218` → `_g_root`,在 parent 裡 add / commit 三檔);`root = parent / ".git"`;`_copy_into`(`:2593-2598`)只做 `read_bytes` / `write_bytes`,沒有 git add ⇒ 副本從未提交。`_g_coverage(root)` → `_g_run` → `_isolated_conftest`(`:298-312`,`:306` 把真實 conftest 的 `_ROOT` 設成 root)→ 真實 producer `tests/conftest.py:410-412`。
- I2(`:2615-2629`):`_d_git(tmp_path, "clone", "-q", "--bare", parent, bare)`;`root = bare / "proj"`;同樣只複製、不提交,同樣經過真實 producer。
- I3(`:2631-…`):直接呼叫 `redlight.committed_blobs(str(sub))`,不經 `evidence_policy_facts`;`sub = parent / "sub"`,只複製 `pyproject.toml`、`tests/conftest.py`,正好等於 `BLOB_FILES`(`redlight.py:497` = `("pyproject.toml",) + ("tests/conftest.py",)`)。斷言 key 集合 = `BLOB_FILES`、每一路徑 `{"worktree": None, "head": None}`;對照組 `committed_blobs(str(parent))` 每一路徑 worktree 非空且 == head ⇒ 對照組證明 git 在這個環境可用,None 不是因為 git 壞了。
- S3I1 上 I1 / I2 實際得到 `'true'`,本身就證明它們重現了 identity 錯位可達 true 的形狀。
- 弱點見 S5i-F3。

### G6 5g / 5h 的其他結論是否仍成立 —— **成立(逐條見第 5 節)**

- 本輪程式改動只在 `_root_is_toplevel` 內;5h 的 G3 / G4 / G5 / G8 結論不受影響。G8 的「正常最上層不會誤回 False」依然成立,但要補上 S5i-F1 這個 fail-open 的例外。
- S5g-F1 / F3 / F4 / F5、S5h-F3 / F4 仍未 machine-enforced;H 段與 F.1 第 7 節對它們的狀態描述正確。S5h-F3 的措辭已補準,但有 S5i-F2 的重疊問題。

### G7 殘餘措辭與程式一致 —— **部分成立**

- 「本輪檢查的語意是 `--is-inside-work-tree` 為 true 且 `--show-prefix` 為空」:**在 prefix 不含 LF 時**與 `:742` 一致。prefix 含 LF 時,程式實際接受的是「prefix 的第一行為空」(S5i-F1)。
- 「明確不支援(⇒ unknown):monorepo 中非最上層的普通子目錄(H1)」:在 POSIX 上,名稱以 LF 開頭的子目錄不成立(S5i-F1)。
- 「位於 gitdir 或 bare repository 內的 root(I1 / I2)⇒ unknown」:在預設環境成立(X4–X7);在 `GIT_DIR` 有設或 `core.worktree` 指向 gitdir 時,會被接受(X8、X9)⇒ S5i-F2(nit)。
- 「會被接受但本輪未納入 acceptance……不得宣稱已拒絕或已支援」:與實測一致(X8–X12 都是 `true` + 空 prefix),而且沒有宣稱已拒絕或已支援任何未測佈局 —— 這一點符合要求。

### G8 跨平台 —— **部分成立(附 S5i-F1)**

- 行序:rev-parse 依參數順序輸出。實測第一行是 `--is-inside-work-tree` 的 `true` / `false`,第二行開始是 prefix(X1–X4)。
- 行尾:Git for Windows 2.53.0 實測只有 LF;`strip()` 對 `\r` 有防護。行尾不會讓正常最上層被誤判成 False。
- 「工作樹最上層回報非 true」的 git 版本:本機只有一個版本,沒有找到這種版本,但無法窮舉(列為審查限制)。
- **平台差異正好落在 S5i-F1**:Windows NTFS 禁止檔名含控制字元 ⇒ Windows 上 S5i-F1 不可達。Linux / macOS 允許 ⇒ 可達。本輪的 POSIX 驗收(〈五十九〉59.3)沒有涵蓋這種輸入。

### G9 總問題(增量版)—— **不成立(找到反例:S5i-F1)**

- 5h 總表 #3–#6(gitdir / bare 內)**現在都被擋**(X4–X7:第一行 `false`)。
- 新反例:POSIX 上名稱以 LF 開頭的子目錄 root(S5i-F1)。被驗證的 HEAD 物件是上層 tree 根的 `<path>`,工作樹讀的是 `<子目錄>/<path>`;Git 本身會把後者對應到 tree 路徑 `"\nsub/<path>"`,不是 `<path>` ⇒ 正是要抓的 identity 錯位。git 原語層的推演依據是 X3(prefix 不跳脫);端到端需要重現。
- 其餘嘗試依 G9 判準都不構成 F2,清單見第 4 節。

---

## 4. G9 反例嘗試清單

### 4.1 5h 總表 18 項重判(TARGET)

| # | 嘗試路徑 | TARGET 輸出(`--is-inside-work-tree` / `--show-prefix`) | `_root_is_toplevel` | 結論 |
|---|---|---|---|---|
| 1 | 普通子目錄 `p/sub` | `true` / `sub/`(X2 實測) | False | 擋 |
| 2 | 同上,全大寫路徑 | 依 5h E1c,prefix 是 `sub/` | False | 擋(未重測) |
| 3 | bare repo 目錄 `bare.git` | `false` / 空(X5 實測) | False | **擋**(5h 反例已封住) |
| 4 | `bare.git/proj` | `false` / 空(X6 實測) | False | **擋** |
| 5 | `p/.git/` | `false` / 空(X4 實測,`od -c` = `f a l s e \n \n`) | False | **擋** |
| 6 | `p/.git/refs` | `false` / 空(X7 實測) | False | **擋** |
| 7 | linked worktree `wt` | 依語意 `true` / 空 | True | 不構成 F2(該 root 自己的 HEAD);未重測 |
| 8 | submodule `p/mod` | 依語意 `true` / 空 | True | 不構成 F2;未重測 |
| 9 | `p/sub/.git` 檔,`gitdir: ../.git` | 依語意 `true` / 空 | True | 不構成 F2(Git 自己把 sub 對應到 tree 根);未重測 |
| 10 | 外部 `p2/sub/.git` 指向 `p/.git` | 同 #9 | True | 不構成 F2;未重測 |
| 11 | `GIT_DIR=p/.git`、無 `GIT_WORK_TREE`,cwd 在子目錄 | `true` / 空(同型的 X9 / X11 實測) | True | 不構成 F2 |
| 12 | `GIT_DIR=p/.git` + `GIT_WORK_TREE=p`,cwd = `p/sub` | `true` / `sub/`(X12 實測) | False | 擋 |
| 13 | `core.worktree` 指向 sub | `true` / 空,toplevel = `q/sub`(X10 **實測**;5h 未實驗) | True | 不構成 F2(Git 把 sub 解析成工作樹最上層);從 `q` 本身查則是 `false` |
| 14 | root 路徑是符號連結 | — | — | 不構成 F2(`tests/conftest.py:130` 已 `resolve()`);本輪未改 |
| 15 | policy 檔是符號連結 | — | — | 同 5h;本輪未改 |
| 16 | 名稱只含空白的子目錄 | `true` / `" /"` | False(`lines[1].strip()` = `/`) | 擋;**但見 N1:以 LF 開頭的名稱不同** |
| 17 | `safe.directory` dubious ownership | exit 128 | False | 擋(fail-closed) |
| 18 | `_committed_addopts`(`:831`) | — | — | 只在 `:874-875` 之後被呼叫(`:893-894`),跟著 #1–#6 一起擋或一起放 |

### 4.2 新構造的嘗試

| # | 嘗試路徑 | 輸出 | `_root_is_toplevel` | 結論 |
|---|---|---|---|---|
| N1 | POSIX:名稱以 LF 開頭的子目錄 `p/"\nsub"`(或 `"\n"`、`" \nX"`) | 依 X3(不跳脫)推得 `true\n\nsub/\n` | **True**(TARGET_H:False) | **反例(S5i-F1)**;需要重現 |
| N2 | 名稱含 `\r` 的子目錄(`"\r"`) | 推演 `true\n\r/\n` | False(`lines[1].strip()` = `/`) | 擋 |
| N3 | `--is-inside-work-tree` 為 true、prefix 為空、又不是最上層,而且沒有環境變數或設定 | 除 N1 外找不到 | — | 未找到 |
| N4 | `core.worktree` 指向 repo 自己的 gitdir `r/.git` | `true` / 空,toplevel = `r/.git`(X8 實測) | True | 不構成 F2(Git 把 gitdir 當工作樹,HEAD 就是該 repo 的);措辭重疊見 S5i-F2。從 `r` 查是 `false` ⇒ 正常 host 變 unknown(fail-closed) |
| N5 | `GIT_DIR=p/.git`(無 `GIT_WORK_TREE`),cwd = `p/.git` | `true` / 空,toplevel = `p/.git`(X9 實測) | True | 不構成 F2(同 #11);措辭見 S5i-F2 |
| N6 | `GIT_DIR=<bare.git>` + `GIT_WORK_TREE=<ext>`(root 本身),cwd = `ext` | `true` / 空,toplevel = `ext`,git-dir = `bare.git`(X11 實測) | True | 不構成 F2(policy 必須在 bare.git 的 HEAD;Git 把 `ext/<path>` 對應到 tree 路徑 `<path>`) |
| N7 | 只設 `GIT_WORK_TREE=p/sub`(gitdir 由探索找到 `p/.git`),cwd = `p/sub` | `true` / 空,toplevel = `p/sub`(X13 實測) | True | 不構成 F2(同 #11) |
| N8 | linked worktree 的管理目錄 `p/.git/worktrees/wt` | 未實驗(需要 commit;R7 攔截後不建內容) | 依語意是 gitdir ⇒ `false` | 推演為擋;未證明 |

### 4.3 scratchpad git 語意實驗原文(git 2.53.0.windows.2;路徑已遮成 `<scratch>` / `<user>`)

X0 —— 呼叫點與測試覆蓋:

```
$ git grep -n -e _root_is_toplevel -e show-prefix -e is-inside-work-tree 8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8 -- .claude tests
8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8:.claude/hooks/redlight.py:726:def _root_is_toplevel(root):
8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8:.claude/hooks/redlight.py:727:    """root 是否就是 git 工作樹的最上層:須同時 `--is-inside-work-tree` 為 true 且 `--show-prefix` 為空
8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8:.claude/hooks/redlight.py:728:    (票 145 Station 4i,S5h-F1:gitdir / bare repository 內 `--show-prefix` 同樣為空,但不是工作樹)。
8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8:.claude/hooks/redlight.py:733:                               "--is-inside-work-tree", "--show-prefix"],
8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8:.claude/hooks/redlight.py:758:    top = _root_is_toplevel(root)
8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8:.claude/hooks/redlight.py:874:        if not _root_is_toplevel(root):
8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8:tests/test_redlight.py:2582:# 4h 的 `_root_is_toplevel` 只看 `git rev-parse --show-prefix` 為空。但 `.git/` 內部或 bare repository 內
8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8:tests/test_redlight.py:2605:        S5h-1 上失敗的原因:在 `.git/` 內 `git rev-parse --show-prefix` 以 exit 0 輸出空行 ⇒ `_root_is_toplevel`
8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8:tests/test_redlight.py:2606:        True;但該處不是工作樹(`--is-inside-work-tree` 為 false),`HEAD:<path>` 與 `hash-object <path>`
8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8:tests/test_redlight.py:2620:        S5h-1 上失敗的原因:同 I1 —— bare 內 `--show-prefix` 為空但非工作樹,`HEAD:<path>` 與
```

(測試檔只在註解與 docstring 命中;沒有任何測試直接呼叫 `_root_is_toplevel`。)

blob 比對:

```
$ git rev-parse 260ede30628c7d205b30ac12c94be73a75cd2812:tests/test_redlight.py 8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8:tests/test_redlight.py ea6aba6452668982fee56f7a2f0faf2cd720ca6d:.claude/hooks/redlight.py 260ede30628c7d205b30ac12c94be73a75cd2812:.claude/hooks/redlight.py
1b4869417c6318cf87c3d631781702afada3ebfc
1b4869417c6318cf87c3d631781702afada3ebfc
d64d565653c5a0c28a2688a07dae44420e3095c7
d64d565653c5a0c28a2688a07dae44420e3095c7
```

範圍:

```
$ git diff --stat ea6aba6452668982fee56f7a2f0faf2cd720ca6d 8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8
 .claude/hooks/redlight.py                          |   12 +-
 docs/audits/2026-10-05-m1a-station3i-redlight.md   |  125 +++
 docs/audits/2026-10-05-m1a-station4h-fix.md        |  257 +++++
 .../2026-10-05-m1a-station5h-review-package.md     | 1085 ++++++++++++++++++++
 docs/audits/2026-10-05-m1a-station5h-review.md     |  421 ++++++++
 .../145-m1a-run-level-evidence-correctness.md      |  194 +++-
 tests/test_redlight.py                             |   72 ++
 7 files changed, 2159 insertions(+), 7 deletions(-)
$ git diff --name-only 8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8 36c978e1c20a51d40cac777dd5aee58625f97032
docs/audits/2026-10-05-m1a-station4i-fix.md
docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
```

佈置(`p` 為空的 `git init`,`p/sub`、`p/中` 為空目錄;沒有 commit,因為 R7 攔截後不建檔案內容):

```
$ git init -q "<scratch>/g/p"
(無輸出)
$ mkdir -p "<scratch>/g/p/.agents" "<scratch>/g/p/sub" "<scratch>/g/p/中"
(無輸出)
```

X1 —— 正常最上層的原始位元組:

```
$ git -C "<scratch>/g/p" rev-parse --is-inside-work-tree --show-prefix > "<scratch>/x1.txt"
(無輸出)
$ od -c "<scratch>/x1.txt"
0000000   t   r   u   e  \n  \n
0000006
```

X2 —— 子目錄:

```
$ git -C "<scratch>/g/p/sub" rev-parse --is-inside-work-tree --show-prefix > "<scratch>/x2.txt"
(無輸出)
$ od -c "<scratch>/x2.txt"
0000000   t   r   u   e  \n   s   u   b   /  \n
0000012
```

X3 —— prefix 是否跳脫(非 ASCII 目錄名):

```
$ git -C "<scratch>/g/p/中" rev-parse --is-inside-work-tree --show-prefix > "<scratch>/x3.txt"
(無輸出)
$ od -c "<scratch>/x3.txt"
0000000   t   r   u   e  \n 344 270 255   /  \n
0000012
```

(原始 UTF-8 位元組,沒有 `core.quotePath` 式的 `"\344\270\255/"` 引號跳脫 ⇒ 路徑裡的 LF 也會原樣輸出。這是 S5i-F1 的原語依據。)

X4 —— `.git/` 內:

```
$ git -C "<scratch>/g/p/.git" rev-parse --is-inside-work-tree --show-prefix > "<scratch>/x4.txt"
(無輸出)
$ od -c "<scratch>/x4.txt"
0000000   f   a   l   s   e  \n  \n
0000007
```

X5–X7 —— bare 與 gitdir 子目錄(Bash 工具顯示時吃掉尾端空行):

```
$ git clone -q --bare "<scratch>/g/p" "<scratch>/g/bare.git"
warning: You appear to have cloned an empty repository.
$ mkdir -p "<scratch>/g/bare.git/proj" "<scratch>/g/q/sub" "<scratch>/g/r" "<scratch>/g/ext"
(無輸出)
$ git -C "<scratch>/g/bare.git" rev-parse --is-inside-work-tree --show-prefix
false
$ git -C "<scratch>/g/bare.git/proj" rev-parse --is-inside-work-tree --show-prefix
false
$ git -C "<scratch>/g/p/.git/refs" rev-parse --is-inside-work-tree --show-prefix
false
```

X8 —— `core.worktree` 指向自己的 gitdir:

```
$ git init -q "<scratch>/g/r"
(無輸出)
$ git -C "<scratch>/g/r" config core.worktree "<scratch>/g/r/.git"
(無輸出)
$ git -C "<scratch>/g/r/.git" rev-parse --is-inside-work-tree --show-prefix --show-toplevel --git-dir
true

C:/Users/<user>/AppData/Local/Temp/claude/c--projects-agent-gates/<session>/scratchpad/g/r/.git
.
$ git -C "<scratch>/g/r" rev-parse --is-inside-work-tree --show-prefix
false
```

X9 —— 只設 `GIT_DIR`,cwd 在 gitdir:

```
$ GIT_DIR="<scratch>/g/p/.git" git -C "<scratch>/g/p/.git" rev-parse --is-inside-work-tree --show-prefix --show-toplevel
true

C:/Users/<user>/AppData/Local/Temp/claude/c--projects-agent-gates/<session>/scratchpad/g/p/.git
```

X10 —— `core.worktree` 指向子目錄(5h #13,首次實測):

```
$ git init -q "<scratch>/g/q"
(無輸出)
$ git -C "<scratch>/g/q" config core.worktree "<scratch>/g/q/sub"
(無輸出)
$ git -C "<scratch>/g/q/sub" rev-parse --is-inside-work-tree --show-prefix --show-toplevel --git-dir
true

C:/Users/<user>/AppData/Local/Temp/claude/c--projects-agent-gates/<session>/scratchpad/g/q/sub
C:/Users/<user>/AppData/Local/Temp/claude/c--projects-agent-gates/<session>/scratchpad/g/q/.git
$ git -C "<scratch>/g/q" rev-parse --is-inside-work-tree --show-prefix
false
```

X11 —— `GIT_DIR` 指向他處的 bare repo、`GIT_WORK_TREE` = root 本身:

```
$ GIT_DIR="<scratch>/g/bare.git" GIT_WORK_TREE="<scratch>/g/ext" git -C "<scratch>/g/ext" rev-parse --is-inside-work-tree --show-prefix --show-toplevel --git-dir
true

C:/Users/<user>/AppData/Local/Temp/claude/c--projects-agent-gates/<session>/scratchpad/g/ext
C:/Users/<user>/AppData/Local/Temp/claude/c--projects-agent-gates/<session>/scratchpad/g/bare.git
```

X12 —— `GIT_DIR` + `GIT_WORK_TREE=p`,cwd = 子目錄:

```
$ GIT_DIR="<scratch>/g/p/.git" GIT_WORK_TREE="<scratch>/g/p" git -C "<scratch>/g/p/sub" rev-parse --is-inside-work-tree --show-prefix
true
sub/
```

X13 —— 只設 `GIT_WORK_TREE` = 子目錄:

```
$ GIT_WORK_TREE="<scratch>/g/p/sub" git -C "<scratch>/g/p/sub" rev-parse --is-inside-work-tree --show-prefix --show-toplevel --git-dir
true

C:/Users/<user>/AppData/Local/Temp/claude/c--projects-agent-gates/<session>/scratchpad/g/p/sub
C:/Users/<user>/AppData/Local/Temp/claude/c--projects-agent-gates/<session>/scratchpad/g/p/.git
```

其他:

```
$ git --version
git version 2.53.0.windows.2
$ wsl.exe -l -q
Exit code 1
(Windows 子系統 Linux 未安裝的訊息;主控台編碼亂碼,不照錄)
```

(實際指令裡的 scratchpad 是絕對路徑,上面已遮成 `<scratch>`;輸出裡的 session 目錄名遮成 `<session>`。)

---

## 5. 5g / 5h 結論是否仍成立(逐條)

前提:本輪程式只改 `_root_is_toplevel`(+9 / −3),其後行號 +6,內容不變。

### 5.1 5h 結論

| 5h 項目 | 是否仍成立 | 依據 |
|---|---|---|
| 判決 FAIL / S5h-F1 | **已封住**(#3–#6 在 TARGET 被擋,X4–X7);但同一不變式在 POSIX 出現新的回歸(S5i-F1) | `:742` |
| S5h-F2(`committed_blobs` 沒有測試鎖住) | **已處理**:I3(`tests/test_redlight.py:2631-…`)直接呼叫 `committed_blobs`,不經 `evidence_policy_facts`。附註:I3 只鎖「普通子目錄」形狀,沒有鎖 gitdir 形狀,也沒有鎖 `:739-742` 的解析(S5i-F3) | E.1 |
| S5h-F3(措辭漏列重新對應佈局) | 已補準;補準後的措辭與「gitdir ⇒ unknown」那句無條件寫法重疊(S5i-F2,nit) | F.1 第 7 節第 3 點 |
| S5h-F4(非最上層沒有狀態字) | 仍存在,未 machine-enforced;本輪未改 `policy_state`(`:943-960`) | D.2 |
| G1 判準等價性 | 對 gitdir / bare **已成立**;對「LF 開頭的子目錄名」**不成立**(S5i-F1,TARGET_H 在這一點反而正確) | X3、`:742` |
| G2 兩處都擋 | 成立:`:758`、`:874` 呼叫同一判準;非最上層時兩處都回 None | `:761-763`、`:874-875` |
| G3 不變式未削弱 | 成立 | 本報告 G3 |
| G4 / G5(H1 / H2) | 成立:H1 / H2 在 TARGET 維持綠(F.1 第 2 節);H1 的 `sub` 名稱是普通 ASCII,不受 S5i-F1 影響 | `tests/test_redlight.py:2550-2576` |
| G6(5g 結論) | 見 5.2 | — |
| G7 殘餘措辭 | 部分成立(本報告 G7) | — |
| G8 跨平台 | 「正常最上層不會誤回 False」仍成立;要補上 POSIX 專屬的 fail-open 例外(S5i-F1) | X1、X3 |
| G9 | #3–#6 已擋;新反例 N1 | 第 4 節 |

### 5.2 5g 結論(以 5h 第 5 節的重判為底)

| 5g 項目 | 是否仍成立 | 依據 |
|---|---|---|
| G1 I-3 bootstrap | 成立;「例外形狀」更新為:普通 ASCII 子目錄與 gitdir / bare 已封住;**POSIX 上 LF 開頭的子目錄名仍存在**(S5i-F1) | `:876-894` 未改 |
| G2 能力邊界 | 成立 | 未改 |
| G3 `committed_addopts` 合約 | 成立 | `:817-848` 未改 |
| G4 override_ini | 成立 | conftest 未改 |
| G5 不變式 | 成立;單一 `"true"` 出口 `:1158` | — |
| G6 `committed_blobs` 逐路徑 | 成立;例外形狀同 G1 的更新 | `:757-772` 未改 |
| G7 status 行 | 仍是部分成立(S5g-F1、S5h-F4) | 未改 |
| G8 安裝器 | 成立(安裝器產生的 root 是 `git init` 的最上層,名稱不由使用者控制成 LF 開頭) | install.py 未改 |
| G9 verify_gates | 成立 | 未改;淨室正二 `file_coverage=true`(F.1 第 5 節) |
| G10 測試授權與紅燈鏈 | 成立(本輪:S3I1 只在檔尾追加 72 行,S3I1 → TARGET 沒有改測試,blob `1b48694…`) | X0 blob 比對 |
| G11 manifest | 成立 | 不在 D.2 |
| G12 跨平台 | 成立(`hash-object` 手法未改);新判準的跨平台例外見 S5i-F1 | — |
| G13 總問題 | 5g「未找到反例」在它自己的範圍內不受影響;5h 的反例已封住;新增 S5i-F1 | — |
| S5g-F1 / F3 / F4 / F5 | 仍存在,未 machine-enforced;追蹤項描述正確 | 相關程式未改 |

---

## 6. 審查限制

1. **沒有跑 pytest、verify_gates.py、status.py**(依規則)。I1 / I2 / I3 / H1 / H2 的紅綠、全套摘要、淨室五情境、帳本不變,全部依審查包 F 段證據原文、blob 比對與紙上推演。
2. **S5i-F1 沒有在任何環境重現**:本機是 Windows(NTFS 禁止檔名含控制字元),沒有 WSL(`wsl.exe -l -q` exit 1)。結論依據是「`--show-prefix` 不跳脫」(X3,用非 ASCII 字元推論到 LF)+ `:742` 的程式。我沒有讀 git 原始碼,所以「LF 也不跳脫」是由 X3 外推,沒有直接觀察到。端到端同樣有 5h 第 6 節第 2 點的未驗處:pytest 以名稱含 LF 的目錄當 rootdir 時,conftest 其他事實(inipath 正規化等)是否與 H1 完全相同,我判斷相同,但沒有證明。
3. **R7 攔截之後,沒有建立任何帶檔案內容或 commit 的臨時 repo**。因此本輪沒有 blob 相等層級的實驗,也沒有重測 #7–#10(linked worktree、submodule、`.git` 檔),N8 也沒有實驗;這些都沿用 5h 的 E 系列或依語意推演。
4. 只驗了 git 2.53.0.windows.2;其他 git 版本(特別是很舊的版本)的 `--show-prefix` 在最上層是否輸出空行、`--is-inside-work-tree` 的輸出格式,沒有驗證。G2 中「舊版不印空行仍然正確」是推演。
5. 沒有確認 git hook 執行 pytest 時是否匯出 `GIT_DIR`(影響 N5 / #11 在實務上是否可達;依 G9 判準本來就不構成 F2)。
6. `safe.bareRepository=explicit` 對 I2 的影響(S5i-F3 (b))是依 git 文件語意推演,沒有實驗。
7. 讀碼範圍:TARGET 的 `redlight.py` 第 690–1158 行與常數 `:472-507`;`tests/conftest.py` 的 `_ROOT` 與 producer 呼叫點;`tests/test_redlight.py` 的 `_isolated_conftest`、`_g_*` helper、H1 / H2、I1–I3;5h 報告第 2–6 節;5g 報告的標題與 findings 表。沒有讀 status.py、install.py、verify_gates.py 本體(本輪未改)。沒有讀 pytest / Python 原始碼(本輪判斷不需要)。
8. 裁決助手的 Linux 預演與 POSIX 外部驗收屬非本 repo 帳本證據,無法獨立核對。
9. scratchpad 留有臨時 repo `<scratch>/g/`(`p`、`bare.git`、`q`、`r`、`ext`)與 `x1.txt`–`x4.txt`、`redlight_T.py`、`test_redlight_T.py`、`conftest_T.py`、`r5h.md`、`r5g.md`(`git show` 的唯讀副本),與本 repo 無關。
