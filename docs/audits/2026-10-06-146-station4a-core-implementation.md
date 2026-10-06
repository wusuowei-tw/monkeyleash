# 票 146 第四站 4a 核心判定審計(S4-146-1 … S4-146-1f)

| 欄 | 值 |
|---|---|
| 日期 | 2026-10-06 |
| 進入基準 | S3d-146-2 `2bb757ce55074bffcf99674ce87008df3e0d322d`(BLOB-3d `20cb16da363547daf233de2aca94e525cb7f4a0c`) |
| S4-146-1 | `44e9c87c9f4db56cfc9b838d9e2d832332a4a6fc`(核心實作) |
| S4-146-1r | `ff7f2bbf74dc4a51c17a5247e626c07765dc5024`(+T146-17 紅燈;BLOB-4a2 `39bae1f38e56c44974dbfa1328a0439c1737b0be`) |
| S4-146-1f | `6d45a7adb7453ff87a76b44255d7448036bbf483`(rule_codes 聯集 + R8 優先序) |
| pipeline | `implement / 146`(Jeff 手動切換;本站未寫) |

---

## 【給裁決者】

1. 第四站 4a 核心判定已提交:allowlist(路徑 + 指紋)、已知靜態入口的事實收集、四態判定、兩欄狀態文字,以及 R4 樹比對下沉到 `redlight.py`。
2. 證據鏈:S3d-146-1 有 39 個紅燈 → S4-146-1 時 T146 全綠、但 2 條既有測試紅 → 補 T146-17 共 3 紅 → S4-146-1f **全套 0 紅**(2150 passed / 5 skipped / 3 xfailed)。
3. 中途停了兩次:一次因為站別還是 tickets,一次因為規則列舉只掃 `gate.py`。兩次都依你的裁決修正。
4. **本站沒有接 status、沒有接 pre-commit**;Q1 的 `status.py:36` 修訂與 Q4 的顯示留待 3e-146 紅燈。**146 尚未生效。**
5. T146-9(symlink)在 Windows skip;POSIX 的證綠由裁決助手的 Linux 沙盒另行提供,**不是本 repo 帳本的證據**。

---

## 【給裁決助手】

### 停點

| 停點報告 | 原因 | 裁決 |
|---|---|---|
| `.dev/reports/2026-10-06T170246Z-ticket146-3d-done-4a-halted.md` | 4a 指令保留 `pipeline tickets / 146`;`tickets` 是 `allows_src_write: false`,而 `.claude/hooks/redlight.py` 屬原始碼(`.claude` 不在 `NON_SOURCE_DIRS`,`gate.py:272-287`)⇒ 規格寫錯 pipeline 前提。嘗試的第一處(`gate.py` docstring)因 `GATE_SELF`(`gate.py:227`)走自我修改豁免被放行並記帳 | **A**:Jeff 手動把 `current_stage` 切為 `implement`;既有 docstring 修改與那筆豁免紀錄隨 S4-146-1 進版,不回滾、不刪 |
| `.dev/reports/2026-10-06T172343Z-ticket146-4a-halted-at-I5.md` | S4-146-1 證綠時 2 條既有測試紅:`rule_codes()` 只掃 `gate.py`(`gate.py:1329-1343`),R4 訊息下沉後 `gate.py` 不再有 `[R4]` | 裁決 (q)(r)(s)(t),見下 |

切站由 Jeff 手動完成,本站沒有寫 `pipeline.json`。

### 前提區兩個 diff(4a 恢復時,原文)

```
$ git diff -- .claude/hooks/gate.py
diff --git a/.claude/hooks/gate.py b/.claude/hooks/gate.py
index a39e02d..707b316 100644
--- a/.claude/hooks/gate.py
+++ b/.claude/hooks/gate.py
@@ -3686,6 +3686,8 @@ def _should_renotice():
 def skill_mirror_violations(canon_dir, mirror_dirs):
     """R4 —— **一條規則,依當下佈局分支**。
(此處原為只含一個空格的空上下文行;為通過 git diff --check 改為本說明)
+    本體已下沉 redlight.py(票 146 方向 B)。
+
     不寫成兩個檢查並排:並排會讓其中一個分支在當下佈局永遠不跑,
     那正是這條規則改寫前的處境(佈局改成 symlink 後,內容比對永遠不可能觸發,
     全輪唯一一次觸發還是人工製造的負向測試)。
$ git diff -- .dev/gate-exemptions.jsonl
diff --git a/.dev/gate-exemptions.jsonl b/.dev/gate-exemptions.jsonl
index 238a5e3..173b79e 100644
--- a/.dev/gate-exemptions.jsonl
+++ b/.dev/gate-exemptions.jsonl
@@ -279,3 +279,4 @@
 (3 行既有內容)
+{"ts": "2026-10-06T17:02:02.764845+00:00", "file": ".claude/hooks/gate.py", "module": "gate", "ticket": "146", "stage": "tickets", "declared_in": "0004", "reason": "gate-self-modification", "tool": "Edit", "outcome": "granted", "blocked_by": null, "at_commit": false, "content_hash": "530dc4eea3e1c9c8471e296fefc49b7730450946124be98ed34fa5c247bf3dcb", "result_hash": "f55f21f2121a587af309d91fa31405ff758f6d73ad5967af08a7263b29e9310d", "changes_bytes": true}
```

### 裁決(Jeff,2026-10-06;逐字)

(q) rule_codes() 改為掃 gate.py 與同目錄 redlight.py 的聯集（方向 B：規則本體搬家，列舉跟著搬）。source_path 參數語意不變：給定時掃該檔與其同目錄的 redlight.py（存在才掃）。
(r) _extension_first_reason 的優先序改為：1 facts["state"] != "ok" ⇒ VIOLATION；2 surfaces 鍵集合不符 ⇒ UNKNOWN；3 之後不變。對應裁決 (o)：較高優先級的 VIOLATION 不得被完整性 UNKNOWN 遮蔽。
(s) gate 自我修改豁免紀錄不得刪改。進入某次 code commit 前已存在的未提交紀錄，必須隨該次 code commit 進版；若該次 commit 的 pre-commit 執行期間新追加 at_commit: true 紀錄，因其產生於 index 建立之後，照實留在工作樹，隨下一個允許的 commit 進版，不得為了工作樹乾淨而刪除、回滾或改寫。
(t) S4-146-1 的四個實作判斷全部接受並列入票 146 契約附註：root 非 git 最上層或 HEAD blob 讀不到 ⇒ "identity_mismatch"；exclude_top 以 normcase 比對 dirpath == root_dir；「鏡像整個缺 <name>」沿用舊訊息含第二行；.mcp.json 非物件或 mcpServers 非物件 ⇒ ["<path>: unreadable"]，無 mcpServers 鍵 ⇒ []。

### 程式檔(S4-146-1f)

| 檔 | git hash-object | sha256 |
|---|---|---|
| `.claude/hooks/redlight.py` | `7486cd18f211c2691463a1edbba416834b71e517` | `51bfe132b7b620cd02044ea516155130bf1592f9a2a5406d6e4589c8b6024801` |
| `.claude/hooks/gate.py` | `0c53c5705b0500ebebe79bf06f6757b2129a225d` | `fbc586c52b161ba0dba3466957b8004daed28db8cb93957b87062d34536a4372` |
| `tests/test_redlight.py`(BLOB-4a2) | `39bae1f38e56c44974dbfa1328a0439c1737b0be` | `8c680e89742171c1601a27739e5465cbcac5dcb8caba425ef07ed5f700c572e2` |

`--stat`:
- S4-146-1:`.claude/hooks/gate.py | 68 +---------`、`.claude/hooks/redlight.py | 330 ++++…`、`.dev/gate-exemptions.jsonl | 2 +` / `3 files changed, 334 insertions(+), 66 deletions(-)`
- S4-146-1r:`tests/test_redlight.py | 11 +++++++++++` / `1 file changed, 11 insertions(+)`
- S4-146-1f:`.claude/hooks/gate.py | 13 ++++++++++++-`、`.claude/hooks/redlight.py | 6 +++---`、`.dev/gate-exemptions.jsonl | 2 ++` / `3 files changed, 17 insertions(+), 4 deletions(-)`

pre-commit:三次 code commit 都**沒有擋下**;S4-146-1 與 S4-146-1f 各印出一次
```
[R2/自我修改豁免] .claude/hooks/gate.py:閘門自身,不受站別限制 —— 已記錄。
     理由:閘門把站別卡住時,修法需要改本檔;R2 管到它就把人鎖在外面(docs/adr/0004)。
     R3 沒有例外:寫測試不需要先解鎖任何東西。
```

### R4 下沉對照(gate.py @ S3d-146-2 → redlight.py @ S4-146-1f)

| 內容 | gate.py 舊行號 | redlight.py 新行號 |
|---|---|---|
| `def skill_mirror_violations` | 3686 | 1090 |
| docstring | 3687-3696(含佈局對照表) | 1091-1097(前兩段;對照表未搬) |
| `import hashlib`(函式內) | 3697 | —(模組層已 import) |
| 正典不存在 ⇒ `[]` | 3698-3700 | 1098-1100 |
| 迭代來源 = 正典 ∪ 鏡像 | 3702-3708 | 1102-1108 |
| 鏡像不存在 ⇒ 跳過 | 3711-3718 | 1111-1118(`rel` → `_rel`) |
| 鏡像缺 `<name>`(舊訊息含第二行) | 3719-3725 | 1119-1122 |
| symlink 分支(訊息逐字) | 3727-3737 | 1124-1134 |
| 正典缺 SKILL.md 而鏡像還在 | 3741-3745 | 1137-1141 |
| 實體副本:只比 SKILL.md(md5) | 3739-3754 | **改為**遞迴 tree parity 1142-1164(多檔 / 缺檔 / 內容 md5 不同 / 鏡像內 symlink) |
| `return out` | 3755 | 1165 |
| gate 端 | 3686-3755 | **薄包裝** `gate.py:3697-3703`:`return _redlight().skill_mirror_violations(canon_dir, mirror_dirs)` |

### pytest

**紅(S4-146-1r)** —— `python -X utf8 -m pytest -q`,最後 15 行:
```
tests\test_redlight.py:3345: AssertionError
=========================== short test summary info ===========================
SKIPPED [1] tests\test_gate.py:451: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:459: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:473: 此環境無法建立 symlink
SKIPPED [1] tests\test_redlight.py:2673: Windows 檔名不得含 LF;本案例由 POSIX 驗收證明(〈六十一〉61.3 裁決 2)
SKIPPED [1] tests\test_redlight.py:3074: Windows 建 symlink 需要額外權限;POSIX 才產得出來
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/srv/x] - …
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/data/x] - …
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/backup/x] - …
FAILED tests/test_claude_md.py::test_the_canon_names_no_rule_that_does_not_exist
FAILED tests/test_gate.py::TestRulesAreEnumeratedFromTheDefinition::test_the_shipped_gate_enumerates_all_of_its_rules
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_17
3 failed, 2147 passed, 5 skipped, 3 xfailed in 215.36s (0:03:35)
```
(XFAIL 行尾的 strict marker 說明以 `…` 省略。)
3 failed / 2147 passed / 5 skipped / 3 xfailed;collected 2158;ERROR 0。T146-17 的 E 行:
`AssertionError: ('UNKNOWN', ["static surfaces: UNKNOWN —— surfaces 不完整：缺 ['synced_files'] / 多 []；fail-closed", 'runtime loaded set: 未證明（沒有獨立 runtime authority source）'])`

**綠(S4-146-1f)** —— 最後 15 行:
```
........................................................................ [ 86%]
........................................................................ [ 90%]
........................................................................ [ 93%]
........................................................................ [ 96%]
......................................................................   [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_gate.py:451: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:459: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:473: 此環境無法建立 symlink
SKIPPED [1] tests\test_redlight.py:2673: Windows 檔名不得含 LF;本案例由 POSIX 驗收證明(〈六十一〉61.3 裁決 2)
SKIPPED [1] tests\test_redlight.py:3074: Windows 建 symlink 需要額外權限;POSIX 才產得出來
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/srv/x] - …
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/data/x] - …
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/backup/x] - …
2150 passed, 5 skipped, 3 xfailed in 216.78s (0:03:36)
```
0 failed / 2150 passed / 5 skipped / 3 xfailed;collected 2158;ERROR 0。

(參考:S4-146-1 那次 `2 failed, 2147 passed, 5 skipped, 3 xfailed`,collected 2157;見第二份停點報告。)

### 帳本

| 回合 | 起點 | 終點 | 前綴 |
|---|---|---|---|
| 紅(S4-146-1r) | LA3 runs `b7447bfa77508860ffe5ef37aa57ce682bc975ed7bc1e25b70e062003ceb1947` / 979019;sessions `37f0ef9beee2956acaa95e44f967eeb2165370630f64f1a17dfff4fc8ed14245` / 22595321 | LC3 runs `f5c1b3a7d056df4917be2343f16b72c01185ea6aed58ac9ea588847ecfbbd71b` / 990721;sessions `12f6ae60f7ba859264398b31bc9fddc7fa0510585e138a2aacb86b53e968ed86` / 23349543 | `t146-s4a2-red-runs-prefix.bin` = `b7447bfa…`、`…-sessions-prefix.bin` = `37f0ef9b…` ⇒ = LA3 |
| 綠(S4-146-1f) | LC3 | LC4 runs `918aaabd71147c2a460a0b8d22117fe5e8acf30029c08ecb7536701adb367755` / 1002240;sessions `f2d87cf59123c50688302c2111a65f4df6f55fa906605e72f8ecc486cb2af4c1` / 24103765 | `t146-s4a2-green-runs-prefix.bin` = `f5c1b3a7…`、`…-sessions-prefix.bin` = `12f6ae60…` ⇒ = LC3 |

(S4-146-1 那次:LA2 → LC2 前綴相等,見第二份停點報告。)

### 豁免帳本紀錄(`.dev/gate-exemptions.jsonl`;本站相關的全部 5 筆)

```
{"ts": "2026-10-06T17:02:02.764845+00:00", "file": ".claude/hooks/gate.py", "module": "gate", "ticket": "146", "stage": "tickets", "declared_in": "0004", "reason": "gate-self-modification", "tool": "Edit", "outcome": "granted", "blocked_by": null, "at_commit": false, "content_hash": "530dc4ee…3dcb", "result_hash": "f55f21f2…310d", "changes_bytes": true}
{"ts": "2026-10-06T17:18:42.566532+00:00", …, "stage": "implement", …, "tool": "Edit", …, "at_commit": false, "content_hash": "f55f21f2…310d", "result_hash": "12dfbe7d…7225", "changes_bytes": true}
{"ts": "2026-10-06T17:19:06.699395+00:00", …, "stage": "implement", …, "tool": "pre-commit", …, "at_commit": true, "content_hash": "12dfbe7d…7225", "result_hash": null, "changes_bytes": null}
{"ts": "2026-10-06T17:38:35.993613+00:00", …, "stage": "implement", …, "tool": "Edit", …, "at_commit": false, "content_hash": "12dfbe7d…7225", "result_hash": "fbc586c5…4372", "changes_bytes": true}
{"ts": "2026-10-06T17:39:02.440263+00:00", …, "stage": "implement", …, "tool": "pre-commit", …, "at_commit": true, "content_hash": "fbc586c5…4372", "result_hash": null, "changes_bytes": null}
```
(5 筆;省略處的欄位皆為 `"file": ".claude/hooks/gate.py", "module": "gate", "ticket": "146", "declared_in": "0004", "reason": "gate-self-modification", "outcome": "granted", "blocked_by": null`。雜湊縮寫為前 8 + 後 4 碼。紀錄內不含使用者路徑,無需遮罩。)
進版位置:前 2 筆隨 S4-146-1;第 3、4 筆隨 S4-146-1f;第 5 筆(S4-146-1f 的 pre-commit 產生)依裁決 (s) 隨本審計的 S4-146-2。

### R3 聲明

紅→綠:S3d-146-1(BLOB-3d,39 紅)→ S4-146-1(T146 全綠、既有 2 紅)→ S4-146-1r(+T146-17,3 紅)→ S4-146-1f(0 紅),由本機帳本記錄;T146-9 在 Windows skip,POSIX 證綠由裁決助手 Linux 沙盒另行提供(非本 repo 帳本證據)。

### 範圍聲明

本站未接 status / pre-commit;Q1 的 status.py:36 修訂與 Q4 顯示留待 3e-146 紅燈;146 尚未生效。

### 已知 / 交接

- `rule_codes()`:`redlight.py` 存在但讀不到時回空集合(與主檔讀不到時的既有行為一致,下游把空集合判成「權威來源讀不到」)。
- `skill_mirror_violations` 下沉後,`gate.py` 與 status 在**沒有 `redlight.py` 的臨時 root**(例如只複製 `gate.py` 的測試 fixture)裡呼叫 R4 會因載入失敗而被 status 記為「未記錄」;本次全套測試沒有因此失敗。
