# 票 146 第三站 3e 紅燈審計(S3e-146-1)

| 欄 | 值 |
|---|---|
| 日期 | 2026-10-06 |
| 進入基準 | S3e-146-0 `d5e890d353e42836fc0441271aa09b729f39a955` |
| S3e-146-0b | `ea2366e769b124ea8fb000b67e1061f93ab7b027`(票 146:3e 裁決 + v1 接線契約) |
| S3e-146-1 | `f625c19c10b60c0df5e0818dbc9b0e3b7d84951b`(三個測試檔) |
| BLOB-3e | `tests/test_redlight.py` `9a5d77d73ddabdf45e52de130ac056ce6edd60bc`;`tests/test_gate.py` `42e0c30e813bab514a77258caedbdb7a226e053e`;`tests/test_status.py` `891ca4db55f2c5edc805e7d49625b5a4a56c5f1a` |
| pipeline | `implement / 146`(本輪未寫) |

---

## 【給裁決者】

1. 3e 紅燈已提交:三支測試檔共新增 25 個 node,另把 `test_t146_14` 的鍵集合改成八鍵。
2. 在乾淨的 S3e-146-1 上跑一次全套:**25 failed、2149 passed、6 skipped、3 xfailed**(合計 2183),**與事先寫下的逐 node 預期表完全一致**;沒有 ERROR;既有測試全部通過;帳本只有追加。
3. 紅的原因幾乎都是「新契約還沒實作」:21 個缺 API、2 個結構 / 行為紅(R10 不在列舉、pre-commit 沒呼叫新檢查)、1 個三元組不符、`test_t146_14` 因鍵數不符。
4. **4b 動手前要先想好**:4b 的 commit 會被它自己新接的 pre-commit 擋下(這台機器 allowlist 沒建、synced 有 227 個檔),見第二段〈4b 已知衝突〉。
5. 146 尚未生效。

---

## 【給裁決助手】

### 裁決(Jeff,2026-10-06;逐字)

1 EXT_UNKNOWN 分 observation_missing / unmanaged_entry，以結構化 category 欄位承載：接受。
2 observation_missing 擋 pre-commit：擋。
3 unmanaged_entry（synced 有檔）擋 pre-commit：甲，擋。synced 是已知存在的未受管靜態入口，不是 runtime 未證明；v0 放行只是留下紀錄，沒有完成入口完整性的 enforcement。這台機器在 synced 納管前無法 commit 是已知成本；不為了接線後能提交而默認例外。
4 DECLARED_OK + runtime_assurance=UNPROVEN：放行；第二行維持固定原句；不得降級 static state。
5 規則代號：B，新代號 R10。
6 home 來源：只有 明確參數 → expanduser("~")/.claude；不納環境變數。
7 status.py:36 修訂字句接受，並同時修 :16「只呼叫 gate」與 :19「不重跑任何規則」。
8 surface 個別讀取失敗：維持 VIOLATION。
9 rule_codes 降級可見：另開 rule_sources()。
z1 判定一次、顯示消費同一結果：extension_report 只呼叫 _extension_first_reason 一次，渲染不再呼叫它；production 不得經 extension_status_lines wrapper 再判一次。
z2 authority 缺失走獨立硬擋，不受影子豁免。
z3 目錄列舉失敗 ⇒ observation_missing，不得洗成空集合。
z4 參數正名 claude_root（= ~/.claude），來源鏈唯一。
補鎖 1 所有 observation_missing 都走獨立硬擋，不受 shadow 豁免，包含 claude_root 無法確定、目錄列舉失敗；判定器缺失／載入失敗直接走 authority failure。unmanaged_entry 宣稱「擋」即不受 shadow 豁免。
補鎖 2 z3 保留既有違規優先序：有列舉錯誤 ⇒ 不得 DECLARED_OK；若已觀測到確定違規仍先回 VIOLATION；沒有確定違規時才回 UNKNOWN + observation_missing。gate 另外依結構化觀測結果硬擋：surfaces["errors"] 非空即硬擋，不論 state。
補鎖 3 明確注入失敗不得 fallback：claude_root=None 才使用 fallback；明確提供不存在、不可讀或無效路徑 ⇒ 前置觀測失敗，判定器呼叫 0 次，gate 直接硬擋。確認不存在的可選入口可以是空；無法確認是否存在或無法列舉不能是空。
補鎖 4 rule_sources() 必須在 redlight 缺失時仍可用，放在 gate 可直接使用的位置，以結構化欄位呈現來源的存在、可讀與完整性；列舉成功不代表模組可執行，import authority 仍由 enforcement 路徑判斷。
補鎖 5 146 authority 檢查必須在 R4（check_skill_copies）之前執行；缺 redlight 的測試不得停掉 check_skill_copies。
補鎖 6 gate 對 surfaces["synced_files"] 非空一律硬擋，不論 static state（static state 仍保留既有 VIOLATION 優先序）；硬擋訊息必須指出未受管入口，不能只重述未登記檔。
3e-0 報告修正（入票，不另開輪）：步驟 0 的明文是 allows_src_write 與 docs 不屬原始碼，不是 docs-write 授權欄位；Q-A 改為「未找到直接鎖定該契約的測試」；Q-G 列出檔名屬偏離；「接線後第一次 commit 一定被擋」標為推論。

(v1 接線契約全文在票 146〈3e 裁決與 v1 接線契約〉。)

### T146-14 的 `-` 行(唯一的既有修改)

```
@@ -3227,5 +3227,5 @@ class TestTicket146ExtensionIntegrity:
         """T146-14:完整性前提 —— surfaces 鍵集合恰為七鍵才可能 DECLARED_OK;少一鍵或多一鍵都不得 DECLARED_OK;對應 invariant 後半。"""
         keys = ("dev_mod_files", "synced_files", "r4_violations", "project_hook_commands",
-                "mcp_json_servers", "user_skill_plugins", "user_commands")
+                "mcp_json_servers", "user_skill_plugins", "user_commands", "errors")
```
`git diff --cached --stat`:`tests/test_gate.py | 223 +++…`、`tests/test_redlight.py | 193 +++…-`、`tests/test_status.py | 120 +++…` / `3 files changed, 535 insertions(+), 1 deletion(-)`。
(docstring 仍寫「七鍵」;依「只改鍵集合」的限制沒有動它。)

### C0 逐 node 預期表與實測

| node | 預期 | 紅的原因(預期) | 實測 | E 行(第一行) |
|---|---|---|---|---|
| redlight `test_t146_14`(既有,改八鍵) | 紅 | 行為紅:surfaces 只有七鍵 | FAILED | `AssertionError: ['dev_mod_files', 'mcp_json_servers', 'project_hook_commands', 'r4_violations', 'synced_files', 'user_commands', ...]` |
| redlight `test_t146_34` | 紅 | 缺 API | FAILED | `AssertionError: v0 contract not implemented: EXT_CAT_ALLOWLIST` |
| redlight `test_t146_35` | 紅 | 行為紅:回二元組 | FAILED | `AssertionError: v0 contract not implemented: _extension_first_reason 三元組(T146-1 → ('VIOLATION', 'allowlist 工作樹與 HEAD 不同；只採用 HEAD，本次無法判定'))` |
| redlight `test_t146_31` | 紅 | 缺 API | FAILED | `AssertionError: v0 contract not implemented: extension_report` |
| redlight `test_t146_27` | 紅 | 缺 API | FAILED | 同上 |
| redlight `test_t146_32a` | 紅 | 缺 API | FAILED | 同上 |
| redlight `test_t146_32b` | 紅 | 缺 API | FAILED | 同上 |
| redlight `test_t146_32c` | 紅 | 缺 API | FAILED | 同上 |
| redlight `test_t146_32d` | 紅 | 缺 API | FAILED | 同上 |
| redlight `test_t146_32e` | **skip**(Windows) | — | SKIPPED(`test_redlight.py:3504`) | — |
| redlight `test_t146_24` | 紅 | 缺 API | FAILED | `…extension_report` |
| redlight `test_t146_36` | 紅 | 缺 API | FAILED | `…extension_report` |
| gate `test_t146_25` | 紅 | 結構紅 | FAILED | `assert 'check_extension_integrity' in ('upstream_shadow_violation', '_err', 'staged_paths', 'Exception', 'gitlink_note', 'check', ...)` |
| gate `test_t146_21` | 紅 | 缺 API | FAILED | `AssertionError: v0 contract not implemented: gate._extension_claude_root` |
| gate `test_t146_22` | 紅 | 缺 API | FAILED | 同上 |
| gate `test_t146_23` | 紅 | 缺 API | FAILED | 同上 |
| gate `test_t146_26` | 紅 | 缺 API(先撞 `_extension_claude_root`) | FAILED | 同上 |
| gate `test_t146_37` | 紅 | 缺 API | FAILED | 同上 |
| gate `test_t146_38` | 紅 | 缺 API | FAILED | 同上 |
| gate `test_t146_24b` | 紅 | 缺 API | FAILED | 同上 |
| gate `test_t146_29` | 紅 | 缺 API | FAILED | `AssertionError: v0 contract not implemented: gate.rule_sources` |
| gate `test_t146_33` | 紅 | 行為紅:R10 不在列舉 | FAILED | `AssertionError: {'R1', 'R2', 'R3', 'R4', 'R5', 'R6', ...}` / `assert 'R10' in {…}` |
| status `test_t146_20` | 紅 | 缺 API | FAILED | `AssertionError: v0 contract not implemented: status._extension_claude_root` |
| status `test_t146_28` | 紅 | 缺 API | FAILED | 同上 |
| status `test_t146_30` | 紅 | 缺 API | FAILED | 同上 |
| status `test_t146_20b` | 紅 | 缺 API | FAILED | 同上 |

加總:新 node 25(redlight 11、gate 10、status 4)⇒ collected 預期 2158 + 25 = **2183**;failed 預期 = 新紅 24 + `test_t146_14` = **25**;skipped 5 + 1 = **6**;passed 2150 − 1 = **2149**;xfailed **3**。
實測:`25 failed, 2149 passed, 6 skipped, 3 xfailed`;collected 2183;**逐格相符**。ERROR 計數 0。

### pytest(S3e-146-1,乾淨工作樹,一次)最後 30 行

```
SKIPPED [1] tests\test_redlight.py:3504: chmod 000 在 Windows 不會讓目錄不可列舉;POSIX 才產得出來
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/srv/x] - …
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/data/x] - …
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/backup/x] - …
FAILED tests/test_gate.py::TestTicket146Integration::test_t146_25 - assert 'c...
FAILED tests/test_gate.py::TestTicket146Integration::test_t146_21 - Assertion...
FAILED tests/test_gate.py::TestTicket146Integration::test_t146_22 - Assertion...
FAILED tests/test_gate.py::TestTicket146Integration::test_t146_23 - Assertion...
FAILED tests/test_gate.py::TestTicket146Integration::test_t146_26 - Assertion...
FAILED tests/test_gate.py::TestTicket146Integration::test_t146_37 - Assertion...
FAILED tests/test_gate.py::TestTicket146Integration::test_t146_38 - Assertion...
FAILED tests/test_gate.py::TestTicket146Integration::test_t146_24b - Assertio...
FAILED tests/test_gate.py::TestTicket146Integration::test_t146_29 - Assertion...
FAILED tests/test_gate.py::TestTicket146Integration::test_t146_33 - Assertion...
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_14
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_34
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_35
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_31
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_27
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_32a
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_32b
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_32c
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_32d
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_24
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_36
FAILED tests/test_status.py::TestTicket146StatusLines::test_t146_20 - Asserti...
FAILED tests/test_status.py::TestTicket146StatusLines::test_t146_28 - Asserti...
FAILED tests/test_status.py::TestTicket146StatusLines::test_t146_30 - Asserti...
FAILED tests/test_status.py::TestTicket146StatusLines::test_t146_20b - Assert...
25 failed, 2149 passed, 6 skipped, 3 xfailed in 220.42s (0:03:40)
```
(XFAIL 行尾 strict marker 說明以 `…` 省略。)

### 帳本(LA → LC)

| 檔 | LA | LC |
|---|---|---|
| `.dev/test-runs.jsonl` | `918aaabd71147c2a460a0b8d22117fe5e8acf30029c08ecb7536701adb367755` / 1002240 | `32ec7f9b55637c0882ee1aaf7b9aabc293fa9c86e8c76eb8d3b0c0511d2a0c62` / 1014880 |
| `.dev/test-sessions.jsonl` | `f2d87cf59123c50688302c2111a65f4df6f55fa906605e72f8ecc486cb2af4c1` / 24103765 | `180cf1d4d1843a151a6aee649e6b1cd1ae7a26cce40acb058897489ed2c2b1f9` / 24863296 |

前綴:`t146-s3e-runs-prefix.bin` = `918aaabd…367755`、`t146-s3e-sessions-prefix.bin` = `f2d87cf5…2af4c1`,= LA ⇒ 只追加。

### R3 聲明

紅燈由本機帳本記錄,對應 HEAD = S3e-146-1(`f625c19c10b60c0df5e0818dbc9b0e3b7d84951b`);test blob:`tests/test_redlight.py` `9a5d77d7…`、`tests/test_gate.py` `42e0c30e…`、`tests/test_status.py` `891ca4db…`。T146-32e 在 Windows skip,POSIX 證紅 / 證綠待外部。

### 4b 必須處理的既有隔離點

新增的 `check_extension_integrity()` 會在 `mode_pre_commit` 裡、R4 之前執行。下列「把 pre-commit 鄰居停掉」的既有 helper 都沒有停它,4b 實作後:臨時 repo 沒有 allowlist ⇒ R10 判 `uninitialized` ⇒ VIOLATION;而且 `_extension_claude_root()` 回 None ⇒ 會讀**真的** `~/.claude`。

1. `tests/test_r5_mounts.py:588-612` `_wire_pre_commit`(`:707` 斷言 `mode_pre_commit() == 0`)
2. `tests/test_gate.py:6194-6215` `_d_silence_the_neighbours`(`:6235`、`:6255` 斷言 rc)
3. `tests/test_stage_defs_source.py:522-530` `_PRE_COMMIT_STUBS`
4. `tests/test_gate.py:1066`(單點 patch `check_skill_copies` 後斷言 `mode_pre_commit() == 1`)
5. `tests/test_gate.py:3042`(同上形狀)
6. `tests/test_status.py:70-113` `_make_root`:只複製 `gate.py` ⇒ 4b 之後每個既有 status 測試都會走「146 判定器不在」那一行;那一行必須經 `_line()` 帶 `(source:`,否則 `TestEveryLineIsTraceable`(`:129-137`)會紅。
(另:`tests/test_gate.py:1313-1333` 要求 `rule_codes()` ⊆ `verify_gates.SCENARIOS` —— R10 一進 `rule_codes`,4b 必須同時補 `SCENARIOS["R10"]` 與 CLAUDE.md 正典段的 R10,否則 `test_claude_md.py:249-272` I-1b 與該條會紅。)

### 4b 已知衝突(交裁決,本站不處理)

1. **4b 的 commit 會被自己擋下。** pre-commit 跑的是工作樹的 `.claude/hooks/gate.py`;4b 一加上 `check_extension_integrity`,在這台機器上 `_extension_claude_root()` = None ⇒ fallback 到真的 `~/.claude` ⇒ ① allowlist 未建 ⇒ VIOLATION(走影子規則,影子關 ⇒ 擋);② `~/.claude/skills/synced` 有檔(3e-0 Q-G:227,Glob 計數)⇒ 補鎖 6 硬擋。裁決 3 接受「synced 納管前無法 commit」,但沒有說 **4b 自己這個 commit** 怎麼進版(是否需要先納管 synced、或先建 allowlist、或其他程序)。這是推論(依 3e-0 Q-G 與契約),未實測。
2. **status 的 runtime 行會出現重複前綴**:契約規定欄名 `"runtime loaded set"`、值 = `report["lines"][1]`,而 `lines[1]` 本身就以 `runtime loaded set: ` 開頭 ⇒ 實際輸出 `runtime loaded set: runtime loaded set: 未證明（…）  (source: …)`。T146-20 / 30 用 `startswith("runtime loaded set: ")` 與值不含 VERDICT_TOKENS 判定,不會因此紅;只記錄,不改。
3. **T146-22 要求硬擋訊息含 `claude_root_invalid`**:契約寫 `"[R10/fail-closed] <原因類別>：<說明>"`,4b 須把 `report["observation"]` 的值寫進訊息,否則 T146-22 不會綠。
4. **T146-26 在 S3e-146-1 上先撞 `_extension_claude_root`**(與其他 gate node 同一個缺口);它真正要鎖的「缺 redlight ⇒ 可讀 fail-closed、無 traceback」要等 4b 補上 `_extension_claude_root` 之後才會被執行到。
