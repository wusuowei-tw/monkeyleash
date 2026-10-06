# 票 146 第三站 3f —— synced 納管紅燈審計

| 欄 | 值 |
|---|---|
| 日期 | 2026-10-06 |
| 進入基準 | S3f-146-0 `41c8d9bd3c5fd160a464abec4cefe870ed27b8c1`,`git status --porcelain` 無輸出;pipeline `implement / framework-updates / 146` |
| S3f-146-0b | `8e1c286391666ee5da62eb032f1421c9375ea682`(裁決 (gg)–(tt)、補鎖 6 修訂版、v2 synced 契約、既有測試允許修改清單入票) |
| S3f-146-1 | `0a8a494237db7d50aedefc9f4056bc39c7f421cd`(紅燈) |
| 本審計 | S3f-146-2 |
| 實作 | 無(本站不寫 `.claude/`、不建 policy 檔) |

---

## 第一段【給裁決者】

1. 3f 紅燈完成：新增 47 個測試，其中 4 個用到 symlink(捷徑檔),在 Windows 跳過。另依允許清單改了 8 個既有測試的佈置；沒有寫實作，也沒有建 policy 檔。
2. 證紅結果與事先寫下的預期逐格相同:68 failed、2149 passed、10 skipped、3 xfailed(合計 2230)。既有的綠燈一個都沒變紅；帳本只有往後追加。
3. **4b 前要你裁**:兩支 3e 既有測試(T146-35、T146-21)在 v2 下 4b 後會一直紅，且不在允許修改清單上 —— 准改它們的佈置，還是改契約(見 C-1、C-2)。
4. 另有三處契約語意待釐清(見〈契約衝突與待釐清〉C-3、C-4、C-5)。不釐清的話,4b 會在實作時自己做選擇。
5. 下一步依 (qq):產生 policy 草稿與差異摘要，交給你核准並親自提交。程序寫在本檔最後一節。

---

## 第二段【給裁決助手】

### 1. 裁決(逐字;出處 S3f-146-0b 票 146〈3f 裁決與 v2 synced 契約〉)

(gg) 納管形狀：甲-2′，獨立 .agents/extension-inventory.json；與 allowlist 都採 HEAD blob + worktree identity 驗證。
(hh) 六個 metadata 檔目前全部驗 path + sha256，不准以 null 豁免；若日後有證據支持例外，再明文修訂契約。
(ii) 不寫 bucket id，但不能只驗唯一子目錄：skills、plugins 分別解析唯一 bucket；根層檔案也須納管，尤其 .bucket-<id>；須定義匿名邏輯路徑、marker 與 bucket 的一致性；禁止寬鬆 wildcard 忽略額外檔案。
(jj) 211 個 UNKNOWN 檔全部驗 path + sha256。
(kk) 缺檔算驗證失敗；新增、缺少、內容不符都不得通過。
(ll) plugins/synced 納入，三個檔同樣驗內容。
(mm) synced 帶 hash；路徑必須區分 skills／plugins，不能合併成會碰撞的 bucket-relative path；保留結構化列舉錯誤與納管結果；連動修訂範圍明列。
(nn) 已盤點入口的配置接受，但不稱「全機入口已齊」；CLAUDE_CODE_PLUGIN_DIRS 等盲區繼續揭露；專案 .claude/skills 仍由既有 R4／surface 路徑觀測，不能變成豁免。
(oo) agent 產草稿、Jeff 審核並親自 commit；票面保留 procedural invariant、尚未 machine-enforced。
(pp) 數量：inventory 是 synced 兩個根共 230 筆；commands 1 筆放 allowlist，另加 hook command 授權；commands 不算進 inventory。「六個 metadata 每輪都變」證據不足，只支持 mtime 曾變；獨立 inventory 不消除重新核准成本。
(qq) 順序：3f 紅燈 → 產生草稿與完整差異摘要 → Jeff 核准並提交兩個 policy 檔（獨立 commit，不含程式）→ 4b 接線。policy 核准後同步又改了內容，4b 被擋是預期結果，須重新審核快照，不新增例外。
(rr) inventory 是必要的 committed policy：即使兩個 synced 根都空，也須有合法的空 inventory；inventory 缺失／無效時不得 DECLARED_OK；仍保留已知 VIOLATION 優先序；gate 獨立硬擋。
(ss) 無效 inventory 不得讓判定器拋例外：先判 inventory state，再讀 entries；synced_verification 須接受 None 與任何非 ok 的 inventory，回結構化「未納管」。
(tt) 匿名邏輯路徑只允許四種形式；保留 token 不得出現在實際相對路徑中；synced 根、bucket 目錄與 marker 都以 lstat 確認型別，不跟隨 symlink；根為 symlink 或非目錄 ⇒ 結構錯誤、不走訪；bucket 內 symlink 與檔案讀不到 ⇒ 驗證失敗。
補鎖 6（3f 修訂版）：synced 未納管或驗證失敗仍獨立硬擋、不受 shadow 豁免；集合與逐檔內容完整驗證通過才可繼續。T146-23／38 同時保留通過與失敗對照情境。

v2 synced 契約與既有測試允許修改清單全文：票 146 同節(S3f-146-0b),此處不重抄。

### 2. BLOB-3f(S3f-146-1)

| 檔 | blob |
|---|---|
| `tests/test_redlight.py` | `2a2af9ba1b333942e5a62fa94e7f3342b0377edf` |
| `tests/test_gate.py` | `be0e51d6a6c41e0a4df1f7e2b8cd36cf8d7d32cf` |
| `tests/test_status.py` | `bbfd3758e930b991c6abd0345545e72da5f752cb` |

`git diff --cached --stat`(S3f-146-1):

```
 tests/test_gate.py     | 179 ++++++++++++++++++++++++
 tests/test_redlight.py | 372 ++++++++++++++++++++++++++++++++++++++++++++++++-
 tests/test_status.py   |  15 ++
 3 files changed, 560 insertions(+), 6 deletions(-)
```

### 3. 既有測試的修改

**- 行(全部 6 行，逐行;全在 `tests/test_redlight.py`)**

| hunk | 方法 | - 行 | 允許清單依據 |
|---|---|---|---|
| `@@ -3406,7 +3406,7 @@` | `test_t146_35` | `-            res = fn(*scen[label])` | T146-35 改傳 EXT_INVENTORY_UNCHECKED(用 _api 取得) |
| `@@ -3418,8 +3418,8 @@` | `test_t146_31` | `-        def counting(facts, surfaces):` | T146-31 計數 wrapper 可接收並轉交第三個 inventory 參數 |
| 同上 | `test_t146_31` | `-            res = orig(facts, surfaces)` | 同上 |
| `@@ -3520,7 +3520,9 @@` | `test_t146_24` | `-        root, claude = self._t3e_clean(tmp_path)` | T146-24 有效 claude_root 佈置改用新 helper(allowlist + 空 inventory) |
| `@@ -3529,9 +3531,367 @@` | `test_t146_36` | `-        """T146-36:extension_report 回傳恰好十一鍵;對應 invariant 前半。"""` | T146-36 十一鍵 → 十三鍵(docstring 同步) |
| 同上 | `test_t146_36` | `-                            "authority", "observation"}, sorted(rep)` | 同上 |

**只有 + 行的修改**(佈置加空 inventory:寫檔 + `git add` + `git commit`,每支 5 行):

- `tests/test_gate.py`:`test_t146_24b`(`@@ -6724,6 +6724,11 @@`)。
- `tests/test_status.py`:`test_t146_20` / `test_t146_28` / `test_t146_30`(`@@ -3235,6 +3235,11 @@`、`@@ -3248,6 +3253,11 @@`、`@@ -3277,6 +3287,11 @@`)。

**允許清單裡、但這次沒改的**:

- T146-27:它只斷言 fallback / param 與前置觀測失敗，不需要 DECLARED_OK。
- T146-14:依清單不動。

**檔尾追加**:

- `tests/test_redlight.py`:`TestTicket146ExtensionIntegrity` 檔尾新增以下 helper 與測試(仍在同一個 class 內)。
  - 新 helper:`_inventory`、`_repo_with_policies`(不改 `_repo`)、`_t3f_bucket`、`_t3f_layout`、`_t3f_report`、`_t3f_governed`,以及常數 `_INVENTORY_REL` / `_T3F_D` / `_T3F_E` / `_T3F_SHA`。
  - 新測試:T146-40 到 T146-45。
- `tests/test_gate.py`:新 class `TestTicket146SyncedGovernance`(T146-23b 到 23i、38b、38c)。載入、停鄰居、執行三件事都呼叫 `TestTicket146Integration` 的 staticmethod,不修改它們。

### 4. C0 逐 node 預期表與實測

**基準**:S3e-146-2 的 collected 2183(25 failed / 2149 passed / 6 skipped / 3 xfailed)。新增 node 47 個 ⇒ 預期 collected 2230。

| node | 預期(Windows) | 預期原因 | 實測 |
|---|---|---|---|
| T146-40[constants] | 紅 | `EXT_INVENTORY_FILE` 缺 | 紅(`v0 contract not implemented: EXT_INVENTORY_FILE`) |
| T146-40[uninitialized / uncommitted / worktree_differs / identity_mismatch / malformed-missing-note / malformed-null-sha256 / malformed-path-skills-x / malformed-path-other-root / malformed-path-no-R / malformed-path-token-twice / malformed-path-dotbucket-in-R / malformed-duplicate-path / malformed-dotdot / ok-empty / ok-four-forms](15) | 紅 | `extension_inventory_facts` 缺 | 15 紅(同一 E 行) |
| T146-41 | 紅 | `extension_report` 缺 | 紅 |
| T146-42[two-dirs / marker-mismatch / extra-root-file / root-is-file](4) | 紅 | `extension_report` 缺 | 4 紅 |
| T146-42[root-child-symlink / marker-symlink / root-is-symlink](3) | skip | `os.name == 'nt'` | 3 skip |
| T146-43[i … iv、vi … xi](10) | 紅 | `EXT_CAT_UNMANAGED` 缺(測試開頭第一個 `_api`) | 10 紅 |
| T146-43[v-symlink] | skip | `os.name == 'nt'` | skip |
| T146-44 | 紅 | `extension_inventory_facts` 缺 | 紅 |
| T146-45 | 紅 | `_extension_render_lines` 缺 | 紅 |
| T146-23b / c / d / e / f / g / h / i、T146-38b / c(10) | 紅 | `gate._extension_claude_root` 缺(`_wire` 的斷言) | 10 紅 |
| **既有、這次修改的** T146-24 / 31 / 36 | 紅(3e 起即紅) | `extension_report` 缺 | 紅 |
| **既有、這次修改的** T146-35 | 紅(3e 起即紅) | **紅因改變**:3e 時是「回二元組」;現在是先撞到 `EXT_INVENTORY_UNCHECKED` 缺 | 紅(`v0 contract not implemented: EXT_INVENTORY_UNCHECKED`) |
| **既有、這次修改的** T146-24b | 紅(3e 起即紅) | `gate._extension_claude_root` 缺 | 紅 |
| **既有、這次修改的** T146-20 / 28 / 30 | 紅(3e 起即紅) | `status._extension_claude_root` 缺 | 紅 |
| 3e 其餘紅(T146-14 / 34 / 27 / 32a–d / 25 / 21 / 22 / 23 / 26 / 37 / 38 / 29 / 33 / 20b) | 紅，紅因不變 | 同 3e 審計 | 紅 |

| 欄 | 預期 | 實測 |
|---|---|---|
| failed | 68(3e 的 25 + 新的 43) | **68** |
| passed | 2149 | **2149** |
| skipped | 10(6 + 新的 4) | **10** |
| xfailed | 3 | **3** |
| collected | 2230 | **2230**(68 + 2149 + 10 + 3) |
| ERROR | 0 | **0**(Grep `^ERROR\|error during collection\|^FAILED` 共 68 筆，全是 FAILED) |
| FAILED 的歸屬 | 只在四個 class | 68 / 68 屬 `TestTicket146ExtensionIntegrity` / `TestTicket146Integration` / `TestTicket146SyncedGovernance` / `TestTicket146StatusLines` |

### 5. 紅 node 的 E 行(新增 43 個 + 修改的 8 個;路徑遮罩)

| node | 第一個 E 行(原文) |
|---|---|
| T146-35 | `E       AssertionError: v0 contract not implemented: EXT_INVENTORY_UNCHECKED` |
| T146-31、T146-24、T146-36 | `E       AssertionError: v0 contract not implemented: extension_report` |
| T146-40[constants] | `E       AssertionError: v0 contract not implemented: EXT_INVENTORY_FILE` |
| T146-40 其餘 15 個、T146-44 | `E       AssertionError: v0 contract not implemented: extension_inventory_facts` |
| T146-41、T146-42 ×4 | `E       AssertionError: v0 contract not implemented: extension_report` |
| T146-43 ×10 | `E       AssertionError: v0 contract not implemented: EXT_CAT_UNMANAGED` |
| T146-45 | `E       AssertionError: v0 contract not implemented: _extension_render_lines` |
| T146-23b … 38c ×10、T146-24b | `E       AssertionError: v0 contract not implemented: gate._extension_claude_root`(下一行 `E        +  where False = hasattr(<module 'gate_t146_3f_23b' from '<pytest tmp>\\repo\\.claude\\hooks\\gate.py'>, '_extension_claude_root')`,模組名依 node 變) |
| T146-20 / 28 / 30 | `E       AssertionError: v0 contract not implemented: status._extension_claude_root` |

### 6. pytest 最後 30 行(原文)

```
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_40[malformed-path-other-root]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_40[malformed-path-no-R]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_40[malformed-path-token-twice]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_40[malformed-path-dotbucket-in-R]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_40[malformed-duplicate-path]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_40[malformed-dotdot]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_40[ok-empty]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_40[ok-four-forms]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_41
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_42[two-dirs]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_42[marker-mismatch]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_42[extra-root-file]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_42[root-is-file]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_43[i-match]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_43[ii-extra]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_43[iii-missing]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_43[iv-content]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_43[vi-worktree-only]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_43[vii-none-nonempty]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_43[viii-none-empty]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_43[ix-malformed-empty]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_43[x-empty-empty]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_43[xi-read-failure]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_44
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_45
FAILED tests/test_status.py::TestTicket146StatusLines::test_t146_20 - Asserti...
FAILED tests/test_status.py::TestTicket146StatusLines::test_t146_28 - Asserti...
FAILED tests/test_status.py::TestTicket146StatusLines::test_t146_30 - Asserti...
FAILED tests/test_status.py::TestTicket146StatusLines::test_t146_20b - Assert...
68 failed, 2149 passed, 10 skipped, 3 xfailed in 209.66s (0:03:29)
```

指令:`python -X utf8 -m pytest -q > <session scratchpad>/t146-s3f-pytest.txt 2>&1`,只跑一次，退出碼 1。

### 7. 帳本(只追加)

| | test-runs.jsonl | test-sessions.jsonl |
|---|---|---|
| LA(sha256 / bytes) | `32ec7f9b55637c0882ee1aaf7b9aabc293fa9c86e8c76eb8d3b0c0511d2a0c62` / 1014880 | `180cf1d4d1843a151a6aee649e6b1cd1ae7a26cce40acb058897489ed2c2b1f9` / 24863296 |
| LC(sha256 / bytes) | `c0820cf7e5408439fbeb54774b1353bd28012f2b8762617a0f39bbcbc0fc1c4d` / 1030149 | `99f2d75a88010c55da0ac8c54286a4b2c13271a1f21cae8fe136b52069f1cb22` / 25635232 |
| LC 的前 LA bytes(`t146-s3f-*-prefix.bin`)的 sha256 | `32ec7f9b…0c62`(= LA) | `180cf1d4…b2f9`(= LA) |

### 8. R3 聲明

- 本站只動測試與 docs,沒有寫任何 `.claude/` 原始碼。所以 R3(寫 `<name>.py` 需要 `tests/test_<name>.py`)沒有被觸發的機會。
- 紅燈由本機帳本記錄(上表 LA → LC 只有追加)。4b 的綠燈必須在同一份帳本上接續這次的紅，provenance(來歷證明)才完整。
- 本站沒有跑第二次全套。

### 9. 契約衝突與待釐清(**不自行改**)

**C-1(會讓 4b 永久紅)T146-35 的 `_scenarios` 佈置在 v2 下是結構錯誤**

- `_scenarios` 的 T146-4b 把 `manifest.json` 直接放在 synced 根底下，沒有 bucket 目錄，也沒有 marker。
- 依 v2「根合法時……必須恰好一個目錄 D 與恰好一個 marker」⇒ 結構錯誤 ⇒ 進 `surfaces["errors"]`。
- 這會在第 7 步就回 `observation_missing`,走不到第 8 步的 `unmanaged_entry`。
- 而 T146-35 期望 `"T146-4b": "unmanaged_entry"`。`_scenarios` 不在允許修改清單上。
- 同一佈置的 T146-4b、T146-8 只斷言 UNKNOWN / 值域，不受影響。

**C-2(會讓 4b 永久紅)T146-21(gate,3e)沒有 inventory**

- `TestTicket146Integration._root` 只提交 allowlist。v2 下 inventory 是 uninitialized ⇒ (d) 硬擋 `[R10/fail-closed] 未受管入口：synced（synced 未納管：inventory uninitialized）`。
- T146-21 斷言 `"[R10]" in err` 與 `"dev-mods 未登記" in err`。但 `[R10/fail-closed]` 不含子字串 `[R10]`;3e 契約對硬擋訊息帶未登記第一筆用的是「可」,不是「須」。
- `_root` 與 T146-21 都不在允許修改清單上。T146-22 / 23 / 26 / 37 / 38 不受影響(它們本來就期待 fail-closed)。

**C-3(語意待釐清)「synced 根存在但為空目錄」**

- v2 字面:根合法時必須恰好一個目錄 + 一個 marker ⇒ 空目錄是結構錯誤。
- (rr) 的「兩個 synced 根都空」可能指不存在，也可能指空目錄。
- 本站測試的「synced 空」一律是**根不存在**(`FileNotFoundError` ⇒ 無項目、無錯誤),兩種讀法都成立。空目錄的處置要明文。

**C-4(語意待釐清)`extension_surface_facts(…, synced_dirs, …)` 怎麼決定邏輯路徑的 `<root>`**

- 契約以 `<claude_root>/<root>/synced/` 定義邏輯路徑，但這個函式收的是任意路徑串列。既有呼叫端傳的路徑，父目錄名都不是 `skills` / `plugins`:
  - `_surfaces` 傳 `<tmp>/s/synced`;
  - T146-11c 傳 `<tmp>/s/user-skills/synced`。
- 要靠串列位置、父目錄名，還是改成 (root 名, 路徑) 對?未定。
- 本站新測試一律經 `extension_report`(路徑由契約固定),不依賴這一點。

**C-5(測試比契約字面嚴)T146-42 的「不走訪」**

- v2 只對「根為 symlink 或非目錄」明寫不走訪。任務 B2 的 T146-42 把「synced_files 不含該根的任何項目」寫在整組 parametrize 之後，本站照 B2 對**全部**案例斷言。
- 也就是說，直接子項層級的結構錯誤(兩個目錄、marker 不符、多餘檔、子項 symlink、marker 是 symlink)也鎖成「該根不走訪」。若契約本意是「報結構錯誤但仍走訪 D」,這 7 個 node 要改。

**C-6(文字過期，不影響斷言)**

- T146-23 / T146-38(3e)的 docstring 仍是「synced 有檔 ⇒ 擋」的舊語意;T146-14 的 docstring 仍寫七鍵。三者都不在允許清單上，沒有動。
- (dd)「T146-23 / 38 同步修訂」的實際做法：舊兩支的斷言在 v2 下仍成立(屬「未納管」);通過 / 失敗對照由新增的 23b–23i、38b、38c 承擔。

### 10. 測試設計上的選擇(規格沒寫死的地方)

1. `_repo_with_policies` 的 `commit` 只控制 inventory;`allowlist_text` 不為 None 一律提交。這樣 T146-40[uncommitted] 與 T146-43[vi] 只讓 inventory 一個變數變動。
2. T146-40 的「常數鎖」做成 parametrize 的一個案例(`constants`)。`EXT_INVENTORY_UNCHECKED` 的斷言是：存在、不是 str / bytes / bool / int / dict / list / tuple、與模組屬性同一物件。
3. T146-43 的 ii / iii / iv / v / vi / xi 除了規格指定的計數與字樣，也一律斷言 `(state, category) == (UNKNOWN, unmanaged_entry)` 且 reason 含「未受管入口：synced」(由 v2 第 8 步推得)。規格只對 (ii) 寫了這一條。
4. Gate 的失敗對照 23c–23i 一律開影子。規格只對 23c、23h 寫明，其他各支同樣開，用來鎖「硬擋不受影子豁免」。23b、38b 關影子;38c 開影子。
5. T146-38c 的影子帳本讀 `mod.SHADOW_LOG`(臨時 root 底下的 `.dev/shadow-log.jsonl`),斷言有一筆 `rule == "R10"`。
6. 測試佈置的 bucket 名是 `d0d0-skills-bucket` / `e0e0-plugins-bucket`(假名);期望值一律寫邏輯路徑。

### 11. policy 草稿產生程序(給 (qq) 第二步;待 Jeff 指示才做)

1. **列舉程式**(唯讀，放 session scratchpad,不進 repo):
   - 對 `~/.claude/skills/synced` 與 `~/.claude/plugins/synced` 各做以下事:
     - 先 `os.lstat` 根本身(型別);
     - 再 `os.lstat` 每個直接子項(型別、名稱是否 `.bucket-` + 唯一目錄名);
     - 合法時 `os.walk(followlinks=False)` 走 bucket 目錄，每個項目 `lstat` 確認是 regular file 才讀 bytes 算 sha256。
   - 輸出:
     - 每筆一行 `<邏輯路徑>\t<sha256>`(**只輸出 `<bucket>` token,不輸出 bucket 真名**);
     - 根與直接子項的 lstat 型別檢查結果各一行;
     - `onerror` 與讀取失敗各一行 `ERROR …`。
   - 程式全文抄進回報。
2. **草稿**:由上面的輸出組成 `.agents/extension-inventory.json` 的草稿(schema / version / entries;`note` 寫來源根與日期),以及 `.agents/extension-allowlist.json` 的草稿(commands 1 筆 + hook command 授權，依 (pp))。兩份都只放 scratchpad。
3. **摘要必附判準**(依 CLAUDE.md〈會寫入證據檔的批次套用〉的精神):
   - 兩根各幾筆(預期 skills 227、plugins 3,合計 230,與 3f-0 計數對照;不同就先說差在哪);
   - 結構檢查結果(兩根各：根型別、唯一目錄、marker 名稱一致、多餘子項 0);
   - symlink 0、ERROR 0 的原始輸出行;
   - 與 3f-0 的 mtime 對照(只談變動時間，依 (ff))。
4. **Jeff 核准並親自 commit 兩個 policy 檔**(獨立 commit,不含程式;依 (oo))。agent 不代為提交。
5. **核准之後同步若又改了內容**,4b 被擋是預期結果，重新產生快照、重新審核，不新增例外(依 (qq))。

### 12. Bash 清單(本站，依序)

```
git rev-parse HEAD
git status --porcelain
cat .dev/pipeline.json
sha256sum .dev/test-runs.jsonl .dev/test-sessions.jsonl
wc -c .dev/test-runs.jsonl .dev/test-sessions.jsonl
git add docs/tickets/framework-updates/146-claude-code-enforcement-integrity.md
git diff --cached --name-only
git diff --cached --check
git diff --cached --stat
git commit -m "docs(146): 3f rulings + v2 synced governance contract (S3f-146-0b)"
git rev-parse HEAD
python -X utf8 -m py_compile tests/test_redlight.py
python -X utf8 -m py_compile tests/test_gate.py
python -X utf8 -m py_compile tests/test_status.py
git add tests/test_redlight.py tests/test_gate.py tests/test_status.py
git diff --cached --name-only
git diff --cached --check
git diff --cached --stat
git diff --cached -U3 -G. --diff-filter=M -- tests/test_redlight.py tests/test_gate.py tests/test_status.py
git commit -m "test(146): 3f synced governance red lights — inventory, logical paths, verification, hard-block (S3f-146-1)"
git rev-parse HEAD
git hash-object tests/test_redlight.py tests/test_gate.py tests/test_status.py
git status --porcelain
python -X utf8 -m pytest -q > <session scratchpad>/t146-s3f-pytest.txt 2>&1
tail -n 30 <session scratchpad>/t146-s3f-pytest.txt
sha256sum .dev/test-runs.jsonl .dev/test-sessions.jsonl
wc -c .dev/test-runs.jsonl .dev/test-sessions.jsonl
head -c 1014880 .dev/test-runs.jsonl > <session scratchpad>/t146-s3f-runs-prefix.bin
head -c 24863296 .dev/test-sessions.jsonl > <session scratchpad>/t146-s3f-sessions-prefix.bin
sha256sum <session scratchpad>/t146-s3f-runs-prefix.bin <session scratchpad>/t146-s3f-sessions-prefix.bin
```

(之後 C5 的 `git add` / `--name-only` / `--check` / `commit` / `rev-parse` / `status` 由回報列出。)
