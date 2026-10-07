# 票 146 第三站 3f-2 —— synced_dirs 成對、空根、root 名錯誤、部分根走訪 紅燈審計

| 欄 | 值 |
|---|---|
| 日期 | 2026-10-06 |
| 進入基準 | S3f-146-2 `31877271441c1050255b027611ac3cd1ae681e8d`,`git status --porcelain` 無輸出;pipeline `implement / framework-updates / 146` |
| S3f2-146-0 | `09a3dc57469239eb4696e76c0ffaef87c21fff69`(裁決 (uu)–(zz)、契約修訂、允許修改清單入票) |
| S3f2-146-1 | `b5eb69d0c32b75b95251d65facec4edf3895cae6`(測試) |
| 本審計 | S3f2-146-2 |
| 實作 | 無(不寫 `.claude/`、不建 policy 檔) |

---

## 第一段【給裁決者】

1. 3f-2 紅燈完成：依清單改了既有佈置，新增 6 個紅燈。證紅結果 109 failed、2114 passed、10 skipped、3 xfailed(合計 2236),逐 node 都對上預測;帳本只追加。
2. passed 少了 35 個，是預期的。改傳成對的 `synced_dirs` 之後，現行實作把一對值(tuple,兩個值綁在一起)當成路徑去查，丟出 TypeError(型別錯誤)。所以 4a 經過 `_surfaces` 的 34 個測試，加上 T146-11c,在 4b 實作前都會紅。
3. **要你裁**:T146-23 / 38 的佈置(`manifest.json` 直接放在 synced 根)在 v2 下是結構錯誤。`_root` 提交空 inventory 之後，它們在 4b 的硬擋原因會從「未納管」變成「結構錯誤」,和 (vv)「原本的硬擋原因不得被替換」衝突;它們的佈置不在允許清單上(見 §9 D-1)。
4. 為了不讓 T146-24b 壞掉，`_root` 用緊湊 JSON 寫 inventory(§9 D-2)。T146-24b 那段重複的 inventory 寫入要不要准刪，也請一起裁。
5. 下一步仍是 policy 草稿與你的核准(3f 審計 §11);等你指示。

---

## 第二段【給裁決助手】

### 1. 裁決(逐字;出處 S3f2-146-0 票 146〈3f-2 裁決與契約修訂〉)

(uu) C-1：准改 _scenarios、T146-4b／11c 的 synced 佈置為合法 bucket + marker；保留「有檔、未納管 ⇒ UNKNOWN／unmanaged_entry」及頂層 synced 排除的原驗收。
(vv) C-2：准改 TestTicket146Integration._root，提交合法空 inventory；T146-21 只留下 dev-mod 未登記這個違規變數。其他測試原本的硬擋原因不得被替換。
(ww) C-3：synced 根經成功列舉、確認沒有任何直接子項 ⇒ 無項目、無錯誤。結果可與不存在同為空集合，但觀測事實不同。列舉失敗不得當空；有任何子項就套完整結構規則。必要的 committed inventory 不變。
(xx) C-4：synced_dirs 改為 (root_name, path) 對的串列，名稱只准 skills／plugins，不得重複 root_name；無效或重複名稱回結構化錯誤，不得忽略。production 明確傳兩根；測試可傳子集或 []。准改點名呼叫處。重複 root 名採「該名稱的所有項目都不走訪」，其他唯一且合法的 root 照常觀測。
(yy) C-5：根或直接子項結構錯誤 ⇒ 不走訪該 bucket、不產生該根的 synced entries；保留 errors。為辨識結構而列舉直接子項仍必要。另一個合法根繼續觀測。
(zz) C-6：准改 T146-23／38／14 的過期 docstring，不改斷言。
C0 要求：重新列出被改佈置之既有 node 的預期；不預設 2149 passed 不變，新參數契約在未實作基線上可能讓既有 node 轉紅，逐項說明。

契約修訂與允許修改清單全文見票 146 同節(S3f2-146-0)。

### 2. BLOB-3f2(S3f2-146-1)

| 檔 | blob |
|---|---|
| `tests/test_redlight.py` | `c3aa2b499bc9d057b28805cb52418dbe79637b09` |
| `tests/test_gate.py` | `dd2e0430ec38c09fc1d9cb9722fa193c09924d48` |

`git diff --cached --stat`:

```
 tests/test_gate.py     | 13 ++++---
 tests/test_redlight.py | 98 +++++++++++++++++++++++++++++++++++++++++++++++---
 2 files changed, 102 insertions(+), 9 deletions(-)
```

### 3. 既有修改的 - 行(全部 9 行，逐行)

| 檔 / hunk | 方法 | - 行 | 清單項 |
|---|---|---|---|
| test_redlight `@@ -2876,5 +2876,5 @@` | `_surfaces` | `-        return fn(str(dev), [str(synced)], str(canon), [], [], str(base / "absent.mcp.json"),` | (1) |
| test_redlight `@@ -2931,5 +2931,5 @@` | `_scenarios` | `-                                   synced_files={"manifest.json": b"{}\n"})))` | (2) |
| test_redlight `@@ -3021,5 +3021,5 @@` | `test_t146_4b` | `-                                  synced_files={"manifest.json": b"{}\n"})` | (3) |
| test_redlight `@@ -3140,5 +3141,5 @@` | `test_t146_11c` | `-        args = (str(dev), [str(user_skills / "synced")], str(canon), [], [], str(base / "absent.mcp.json"),` | (4) |
| test_redlight `@@ -3225,5 +3226,5 @@` | `test_t146_14` | `-        """T146-14:完整性前提 —— surfaces 鍵集合恰為七鍵才可能 DECLARED_OK;少一鍵或多一鍵都不得 DECLARED_OK;對應 invariant 後半。"""` | (5) |
| test_gate `@@ -6569,5 +6569,7 @@` | `_root` | `-        """臨時 repo(已提交空白 allowlist)+ 存在但空的 claude_root。"""` | (7) |
| test_gate `@@ -6581,8 +6583,11 @@` | `_root` | `-        self._git(root, "add", ".agents/extension-allowlist.json")` | (7) |
| test_gate `@@ -6666,5 +6671,5 @@` | `test_t146_23` | `-        """T146-23:synced 有檔、其他乾淨 ⇒ rc 1,[R10/fail-closed] +「未受管入口：synced」;影子開仍 rc 1;對應裁決 3。"""` | (8) |
| test_gate `@@ -6710,5 +6715,5 @@` | `test_t146_38` | `-        """T146-38:未登記檔 + synced 有檔 + 影子開 ⇒ rc 1,[R10/fail-closed] +「未受管入口：synced」(補鎖 6,不得只重述未登記檔);對應裁決 3。"""` | (8) |

**只有 + 行的修改**:

- `test_t146_11c` 新增 1 行，寫入 marker `.bucket-session-id`(清單項 (4))。
- `_root` 新增 3 行，寫入緊湊格式的空 inventory(清單項 (7))。

**沒改的清單項**:

- (6) `_t3f_layout` / `_t3f_report` 都經過 `extension_report`,不自己組 `synced_dirs`,所以不需要改。

**檔尾追加**(仍在 `TestTicket146ExtensionIntegrity`):

- helper `_t3f2_surfaces`;
- 測試 `test_t146_42b[empty-root]`、`test_t146_46[a/b/c/d]`、`test_t146_47`。

### 4. C0 逐 node 預期表與實測

**基準**:S3f-146-2 實測 68 failed / 2149 passed / 10 skipped / 3 xfailed,collected 2230。新增 node 6 個 ⇒ 預期 collected 2236。

**基線上 `_surfaces` 改傳成對值之後會發生什麼**:

- 現行 `extension_surface_facts` 對 `synced_dirs` 的每一項呼叫 `_walk_regular(d)`;
- 它的第一行是 `os.path.isdir(root_dir)`;
- 傳入 tuple ⇒ `os.stat(tuple)` 丟 **TypeError**。`isdir` 只攔 `OSError` / `ValueError`,所以 TypeError 不會被吞成 False。
- 結論：每個經過 `_surfaces`、`_scenarios`,或直接傳成對值的測試，在基線上都會**紅(TypeError)**,不是「空集合 ⇒ 綠」。

| node | S3f-146-2 | 預期 | 預期理由 | 實測 |
|---|---|---|---|---|
| T146-1、2、2b、2c、3、3b、4、4b、7、8、11、11b、12、12b、17(15 個) | 綠 | **紅** | 經 `_surfaces`(T146-8 經 `_scenarios`)⇒ TypeError | 15 紅(TypeError) |
| T146-15 ×3、15b ×3、15c ×10、16 ×3(19 個) | 綠 | **紅** | 經 `_surfaces` ⇒ TypeError | 19 紅(TypeError) |
| T146-11c | 綠 | **紅** | 直接傳 `[("skills", …)]` ⇒ TypeError | 紅(TypeError) |
| T146-14 | 紅(缺 `errors` 鍵) | 紅，紅因改變 | `_surfaces` 先 TypeError | 紅(TypeError) |
| T146-35 | 紅(缺 `EXT_INVENTORY_UNCHECKED`) | 紅 | —— **C0 沒有逐項寫出紅因變化**(見偏離 1) | 紅(**TypeError**,`_scenarios` 先丟出) |
| T146-0a、5、6、13 | 綠 | 綠 | 不經 `_surfaces` | 綠 |
| T146-9 | skip | skip | `os.name == 'nt'`;傳的是 `synced_dirs=[]`,不受影響 | skip |
| gate 3e 經 `_root` 的 T146-21、22、23、26、37、38、24b | 紅(缺 `gate._extension_claude_root`) | 紅，紅因不變 | `_root` 只多提交 inventory;T146-24b 的重寫因位元組不同可以提交(§9 D-2),之後在 `_wire` 斷言紅 | 7 紅，紅因不變 |
| 其餘 3e / 3f 紅(T146-25、29、33、34、31、27、32a–d、24、36、40 ×16、41、42 ×4、43 ×10、44、45、gate 3f ×10、status ×4) | 紅 | 紅，紅因不變 | 本輪沒有碰 | 紅 |
| **新** T146-42b[empty-root] | — | 紅 | `extension_report` 缺 | 紅(`v0 contract not implemented: extension_report`) |
| **新** T146-46[a / b / c / d] | — | 紅 | `extension_surface_facts` 收成對值 ⇒ TypeError | 4 紅(TypeError) |
| **新** T146-47 | — | 紅 | `extension_report` 缺 | 紅(`v0 contract not implemented: extension_report`) |

| 欄 | 預期 | 實測 |
|---|---|---|
| failed | 109(68 + 35 + 6) | **109** |
| passed | 2114(2149 − 35) | **2114** |
| skipped | 10 | **10** |
| xfailed | 3 | **3** |
| collected | 2236(2230 + 6) | **2236** |
| ERROR | 0 | **0**(Grep `^ERROR\|error during collection` 0 筆) |
| FAILED 歸屬 | 四個 146 class | 109 / 109 |
| `E   TypeError` 行數 | —— | 41(35 個轉紅 + T146-14 + T146-35 + T146-46 ×4) |

**轉綠**:無。**轉紅**:上表 35 個，理由都是 TypeError。4b 依 (xx) 實作成對參數之後，它們應回到原本的驗收。

### 5. 4a 的 T146-0a ～ 17 在本輪基線的狀態

依 node 計是 **41 個**(題述的「40 條」是概數;parametrize 展開後的實數如下):

| 狀態 | 個數 | node |
|---|---|---|
| 綠 | 4 | 0a、5、6、13 |
| skip | 1 | 9(Windows) |
| 紅(本輪因 `_surfaces` 改成對值而轉紅，屬預期) | 35 | 1、2、2b、2c、3、3b、4、4b、7、8、11、11b、11c、12、12b、15 ×3、15b ×3、15c ×10、16 ×3、17 |
| 紅(3e 起即紅，本輪紅因改為 TypeError) | 1 | 14 |

### 6. 新紅 node 的 E 行(原文)

| node | E 行 |
|---|---|
| T146-42b[empty-root] | `E       AssertionError: v0 contract not implemented: extension_report` |
| T146-46[a-invalid-name / b-duplicate-skills / c-duplicate-skills-plus-plugins / d-valid-pair] | `E   TypeError: stat: path should be string, bytes, os.PathLike or integer, not tuple` |
| T146-47 | `E       AssertionError: v0 contract not implemented: extension_report` |
| 轉紅的 35 個與 T146-14 / 35 | `E   TypeError: stat: path should be string, bytes, os.PathLike or integer, not tuple`(frame `<frozen genericpath>:42: TypeError`;呼叫鏈 `_surfaces` → `redlight.py:1270 extension_surface_facts` → `redlight.py:1062 _walk_regular` → `os.path.isdir`) |

### 7. pytest 最後 30 行(原文)

```
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
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_42b[empty-root]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_46[a-invalid-name]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_46[b-duplicate-skills]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_46[c-duplicate-skills-plus-plugins]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_46[d-valid-pair]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_47
FAILED tests/test_status.py::TestTicket146StatusLines::test_t146_20 - Asserti...
FAILED tests/test_status.py::TestTicket146StatusLines::test_t146_28 - Asserti...
FAILED tests/test_status.py::TestTicket146StatusLines::test_t146_30 - Asserti...
FAILED tests/test_status.py::TestTicket146StatusLines::test_t146_20b - Assert...
109 failed, 2114 passed, 10 skipped, 3 xfailed in 233.65s (0:03:53)
```

指令:`python -X utf8 -m pytest -q > <session scratchpad>/t146-s3f2-pytest.txt 2>&1`,只跑一次，退出碼 1。

### 8. 帳本(只追加)

| | test-runs.jsonl | test-sessions.jsonl |
|---|---|---|
| LA | `c0820cf7e5408439fbeb54774b1353bd28012f2b8762617a0f39bbcbc0fc1c4d` / 1030149 | `99f2d75a88010c55da0ac8c54286a4b2c13271a1f21cae8fe136b52069f1cb22` / 25635232 |
| LC | `d7ccbb9276de1b4c173f6f01436ef86dfb338bb284cccd8b094dcae8a65470e0` / 1047894 | `427950604d9f53526ca566b4da129b9d392ecf3254960cfafad832e3a2a6b5d4` / 26408830 |
| LC 的前 LA bytes(`t146-s3f2-*-prefix.bin`) | `c0820cf7…1c4d`(= LA) | `99f2d75a…cb22`(= LA) |

**R3 聲明**:

- 本站只動測試與 docs,沒有寫任何 `.claude/` 原始碼。
- 紅燈由本機帳本記錄，上表只有追加。
- 本站只跑一次全套。

### 9. 契約衝突與待裁(**不自行改**)

**D-1 T146-23 / 38 的硬擋原因，4b 後會被替換**

- 兩支的佈置是 `skills/synced/manifest.json`(直接放在根底下，沒有 bucket、沒有 marker),在 v2 下是**結構錯誤**。
- 本輪 `_root` 依 (vv) 提交了合法空 inventory,所以 4b 之後的實際硬擋原因會是 (c)「觀測失敗」加上 (d)「未受管入口：synced（synced 結構錯誤：…）」,不再是「未納管」。
- 斷言(`[R10/fail-closed]`、`未受管入口：synced`)仍會成立，但 (vv)「其他測試原本的硬擋原因不得被替換」字面上不成立。
- 依 (zz),docstring 已改成「未納管」語意，但與 4b 的實際路徑不符。
- 兩支的佈置不在本輪允許清單上，所以沒改。修法候選(待裁):
  - 准把兩支改成合法 bucket + marker。這樣 4b 後原因是「額外 N」,即有檔但 inventory 沒登記;
  - 或接受原因改變，並改 docstring 措辭。

**D-2 T146-24b 與 `_root` 的重複寫入**

- T146-24b(3f 修改)會在 `_root` 之後**再寫一次空 inventory 並 `git commit`**。
- 如果 `_root` 寫的位元組完全相同，`git commit` 會因為沒有變更而失敗(`check=True` ⇒ CalledProcessError),T146-24b 就會在 4b 之後永久紅。
- T146-24b 不在本輪允許清單上。所以 `_root` 改用**緊湊 JSON**(不縮排)寫 inventory,讓 T146-24b 的縮排版本位元組不同、提交得進去。兩者語意都是合法空 inventory。
- 這是為了不違反清單而做的格式選擇，已寫在 `_root` 的 docstring。是否准刪 T146-24b 的那 5 行，待裁。

**D-3 T146-42b 的 node id**

- 題述要的是 `T146-42[empty-root]`。但 `test_t146_42` 不在允許清單上，加 parametrize 案例就得改它的 decorator 與本體(斷言相反)。
- 所以新增獨立函式 `test_t146_42b`,parametrize 唯一的 id `empty-root`,node 是 `test_t146_42b[empty-root]`,docstring 標 `T146-42[empty-root]`。

### 10. Bash 清單(本站，依序)

```
git rev-parse HEAD
git status --porcelain
cat .dev/pipeline.json
sha256sum .dev/test-runs.jsonl .dev/test-sessions.jsonl
wc -c .dev/test-runs.jsonl .dev/test-sessions.jsonl
git add docs/tickets/framework-updates/146-claude-code-enforcement-integrity.md
git diff --cached --name-only
git diff --cached --check
git diff --cached -- docs/tickets/framework-updates/146-claude-code-enforcement-integrity.md
git commit -m "docs(146): 3f-2 rulings C-1..C-6, synced_dirs pairs, empty-root semantics (S3f2-146-0)"
git rev-parse HEAD
python --version
where python
python -X utf8 -m py_compile tests/test_redlight.py
python -X utf8 -m py_compile tests/test_gate.py
git add tests/test_redlight.py tests/test_gate.py
git diff --cached --name-only
git diff --cached --check
git diff --cached --stat
git diff --cached -U2 -- tests/test_redlight.py tests/test_gate.py
git commit -m "test(146): 3f-2 — synced_dirs pairs, empty root, invalid/duplicate root names, partial-root walk (S3f2-146-1)"
git rev-parse HEAD
git hash-object tests/test_redlight.py tests/test_gate.py
git status --porcelain
python -X utf8 -m pytest -q > <session scratchpad>/t146-s3f2-pytest.txt 2>&1
tail -n 30 <session scratchpad>/t146-s3f2-pytest.txt
sha256sum .dev/test-runs.jsonl .dev/test-sessions.jsonl
wc -c .dev/test-runs.jsonl .dev/test-sessions.jsonl
head -c 1030149 .dev/test-runs.jsonl > <session scratchpad>/t146-s3f2-runs-prefix.bin
head -c 25635232 .dev/test-sessions.jsonl > <session scratchpad>/t146-s3f2-sessions-prefix.bin
sha256sum <session scratchpad>/t146-s3f2-runs-prefix.bin <session scratchpad>/t146-s3f2-sessions-prefix.bin
```

### 11. 偏離

1. **C0 漏列 T146-35 的紅因變化。** 跑之前列出的預測只寫了 T146-14 的紅因改變。T146-35 原本的紅因是缺 `EXT_INVENTORY_UNCHECKED`,實測先在 `_scenarios` 丟 TypeError。紅綠狀態與四個數字都符合預測;紅因這一格當時沒寫，實測後才補進表。
2. **預測的機制寫錯了，結果碰巧對。** 跑之前我依據的是「Windows 的 `os.path.isdir` 是 `nt._isdir`,遇到 tuple 會丟 TypeError」。實測 frame 是 `<frozen genericpath>:42`,也就是 `genericpath.isdir` 的 `os.stat` 丟 TypeError、沒有被攔。結論(TypeError ⇒ 紅)對，依據不對。依 CLAUDE.md「碰巧對與驗過，在結果上長得一樣」,如實記錄。
3. **劃線位置。** A2 要求在〈3f 裁決與 v2 synced 契約〉裡劃「synced_dirs 為路徑串列」,但 v2 節沒有這一句;原句在〈3e 裁決與 v1 接線契約〉的「八個路徑」那一行，劃線劃在那裡。
4. **契約修訂的位置。** 修訂全文寫在新節〈3f-2 裁決與契約修訂〉,不是插進 v2 節本體;v2 節本體只有劃線與一句改寫(「有任何直接子項時：」)。
5. **A3「全文讀一次」。** 讀的是 `git diff --cached` 的全文(本次變更的完整內容),不是整份票。
6. **D-2、D-3** 屬設計選擇，見 §9。
