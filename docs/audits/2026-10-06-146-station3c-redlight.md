# 票 146 第三站補強審計(3c-146 / Station 3c)

| 欄 | 值 |
|---|---|
| 日期 | 2026-10-06 |
| 進入基準 | S3b-146-2 `db34bb9fa8aa388fab1eefe936924f75eec490d8` |
| S3c-146-0 | `f6cd57a755a9501bb0811d5527c2f18607e7c56f`(票 146:3c 裁決 (h)–(l)) |
| S3c-146-0b | `ea41d5a08f4720cc7da3e686d001a346599870cf`(票 146:停點三題裁決) |
| S3c-146-1 | `e79c393d800c7c68fbf7afe6f5d9082afbaa6a03`(`tests/test_redlight.py`) |
| **test blob** | `git hash-object tests/test_redlight.py` = `HEAD:tests/test_redlight.py` = **`3c75d69a142aa34ecf8ea29a667969d1cb673c08`**;sha256 `e3aa12419e3daca9f0e303b3011e672f7c8f17a1f854f64ac3994bfd9346332a` |
| pipeline | `tickets / 146`(本輪未寫) |

---

## 【給裁決者】

1. 第三站補強完成:T146-9 改成 8 參數、T146-13 改成 AST 層級;allowlist 的檔案型項目改成「路徑 + 指紋」一起綁;新增 3 個測試方法(16 個 node),驗「同指紋不同路徑」「同路徑不同指紋」「路徑不是標準形式」。
2. 在乾淨的 S3c-146-1 上跑一次全套:**36 failed、2110 passed、5 skipped、3 xfailed**(合計 2154 = 2138 + 16);36 個 failed 全部是 `TestTicket146ExtensionIntegrity`;沒有 ERROR。帳本只有追加。
3. **第四站要變綠的精確測試檔**:blob `3c75d69a142a…`。依裁決 (j),第四站的綠必須對應這個 blob。
4. 依停點裁決,`_scenarios` 也改了一行(讓 T146-8 的「已登記」情境維持原意)。
5. 146 尚未生效。

---

## 【給裁決助手】

### 來源與對應裁決

來源:GPT 審查(Jeff 轉述;**審查原文我沒有看到**,以下依裁決 (h)–(l) 歸納)。

| 項目 | 裁決 | 對應 |
|---|---|---|
| blocker 1:T146-9 用 6 參數呼叫,實作後在 POSIX 必紅 | (h) | `test_t146_9` 改 8 參數;新參數不給預設值 |
| blocker 2:T146-13 的全文禁字會撞 `redlight.py:18`、`:27` 歷史註解 | (i) | `test_t146_13` 改 AST 層級 + 兩個函式各自的 `inspect.getsource` |
| canonical-path 收緊:只綁 sha256 時同內容換名也會被授權 | (k)、(l) | `_allowlist` 改 (path, sha256);新 T146-15 / 15b / 15c |
| 推論紅 ≠ 機器紅 | (j) | 本次在乾淨 HEAD 實跑,帳本對應精確 blob |

### 停點與裁決

- 停點報告:`.dev/reports/2026-10-06T162625Z-ticket146-s3c-halted-before-B.md`
- 三題:
  1. `_scenarios` 第 2918 行仍用舊參數 `dev_mod_sha=[note_sha]`;不改它的話,T146-8 的「已登記」情境會靜默變成 malformed → **裁 A:准改那一行為 `("note.txt", note_sha)`**。
  2. 〈增補後的契約〉的 policy 形狀 bullet 與 3c 矛盾 → **裁:劃線 + 理由「被 3c 裁決 (k) 取代」**;裁決助手自加的理由句保留並標「(裁決助手補述)」(S3c-146-0b)。
  3. T146-15c 的 malformed 七案是否疊三入口 → **裁:不疊,只對 user-commands;正向三入口各一**。

### B1′ 五處修改的 `-` 行(逐行)

(1) `_allowlist`:
```
-    def _allowlist(dev_mod_sha=(), **extra):
-               "dev_mod_files": [{"sha256": h, "note": "t146"} for h in dev_mod_sha],
-               "user_skill_plugins": [], "user_commands": [],
```
(2) `test_t146_3b` / `test_t146_11b` / `test_t146_12b`:
```
-        root = self._repo(tmp_path / "r", allowlist_text=self._text(self._allowlist(dev_mod_sha=[sha])))
-        policy = self._allowlist(user_skill_plugins=[{"sha256": sha, "note": "t146"}])
-        policy = self._allowlist(user_commands=[{"sha256": sha, "note": "t146"}])
```
(3) `test_t146_9`:
```
-                      str(tmp_path / "absent.mcp.json"))
```
(4) `test_t146_13`:
```
-        """T146-13:依賴方向 B —— facts 層住在 redlight.py、不反向載入 gate;R4 純函式下沉且與 gate 薄包裝結果相同;對應 invariant 前半。"""
-        text = (ROOT / ".claude" / "hooks" / "redlight.py").read_text(encoding="utf-8")
-        for needle in ("gate" + ".py", "import " + "gate", "load_" + "gate"):
-            assert needle not in text, "redlight.py 含 %s" % needle
```
(5) `_scenarios`:
```
-        r = self._repo(tmp_path / "r3b", allowlist_text=self._text(self._allowlist(dev_mod_sha=[note_sha])))
```
合計 12 行 `-`(`git commit`:`1 file changed, 118 insertions(+), 12 deletions(-)`),全部落在這五處。
另外新增的 class 屬性 `_T146_FIELDS`(入口 → 欄位對照)放在 `test_t146_14` 之後、三個新方法之前;它是屬性,不是方法。

### 新 node 的失敗類型與 E 行

| node | 失敗類型 | E 行 |
|---|---|---|
| `test_t146_15[dev-mods]` / `[user-skills]` / `[user-commands]` | 缺 API | `AssertionError: v0 contract not implemented: extension_surface_facts` |
| `test_t146_15b[dev-mods]` / `[user-skills]` / `[user-commands]` | 缺 API | `AssertionError: v0 contract not implemented: extension_allowlist_facts` |
| `test_t146_15c[positive-dev-mods]` / `[positive-user-skills]` / `[positive-user-commands]` | 缺 API | `AssertionError: v0 contract not implemented: extension_allowlist_facts` |
| `test_t146_15c[malformed-dot-segment]` / `[malformed-dotdot-segment]` / `[malformed-empty-segment]` / `[malformed-backslash]` / `[malformed-leading-slash]` / `[malformed-drive-prefix]` / `[malformed-trailing-slash]` | 缺 API | `AssertionError: v0 contract not implemented: extension_allowlist_facts` |

修改過的既有方法:`test_t146_13` 的 E 行仍是 `v0 contract not implemented: extension_surface_facts`;`test_t146_3b` / `11b` / `12b` 仍先撞 `extension_allowlist_facts`。

T146-15 先撞 `extension_surface_facts`(`self._surfaces(base)` 在 `_evaluate` 之前呼叫);15b / 15c 先撞 `extension_allowlist_facts`(`self._facts(root)` 先求值)。⇒ 第四站要逐段確認每個 node 是由**自己的斷言**變綠。

### 已知注意點

- **T146-13 的 AST 規則**用「字串引數**含** `"gate"`」判定。現在 `redlight.py` 沒有任何 `spec_from_file_location` / `import_module` 呼叫(Grep 0 筆),所以不會誤判;但如果將來出現含 `agent-gates` 的路徑字串,這條規則會把它當成違規。照裁決 (i) 逐字實作,沒有放寬。
- **T146-9 在 Windows 仍是 skip**,8 參數的修正在本機沒有被執行過;它的機器紅要等 POSIX(例如 CI)。

### pytest(S3c-146-1,乾淨工作樹,只跑一次)

指令:`python -X utf8 -m pytest -q > <session scratchpad>/t146-s3c-pytest.txt 2>&1`(exit 1)

最後 20 行原文:
```
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_12b
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_13
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_14
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_15[dev-mods]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_15[user-skills]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_15[user-commands]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_15b[dev-mods]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_15b[user-skills]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_15b[user-commands]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_15c[positive-dev-mods]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_15c[positive-user-skills]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_15c[positive-user-commands]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_15c[malformed-dot-segment]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_15c[malformed-dotdot-segment]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_15c[malformed-empty-segment]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_15c[malformed-backslash]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_15c[malformed-leading-slash]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_15c[malformed-drive-prefix]
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_15c[malformed-trailing-slash]
36 failed, 2110 passed, 5 skipped, 3 xfailed in 196.84s (0:03:16)
```

驗收:
- 沒有 `^ERROR ` 行,也沒有 `errors during collection`。
- **collected = 36 + 2110 + 5 + 3 = 2154**;算法:S3b 的 2138 + 新 node 16(T146-15 三入口 3 + 15b 三入口 3 + 15c 正向三入口 3 + malformed 七案 7)= 2154 ✔。
- failed 36 = 20(既有)+ 16(新);全部是 `TestTicket146ExtensionIntegrity::*`(FAILED 清單 36 列逐一核對),除 `test_t146_9` 外每個方法 / node 都在清單上。
- `test_t146_9` 的 skip:進度列第 23 行 `...........s...........FFFFFFFFFFFFFsFFFFFFFFFFFFFFFFFFFFFFF....` 中,第 13 個 F 之後緊接 `s`,之後 23 個 F;與方法定義順序一致(位置推論,沒有 `-rs`)。
- 其餘:2110 passed;5 skipped 中有 4 個非 146;3 xfailed 是 `test_g1_guard.py` 的既有 strict marker(同 S3-146 審計的解讀)。

### 帳本(LA → LC)

| 檔 | LA sha256 | LA bytes | LC sha256 | LC bytes |
|---|---|---|---|---|
| `.dev/test-runs.jsonl` | `361e2f4ba1760bce9b5859eab273a5f45e7578a7ba478e98d9d05dac683866a8` | 939969 | `918f33abc16ffaa2fcfe56f9abbe913159ac8e155952d00f871ec918a287b3af` | 953567 |
| `.dev/test-sessions.jsonl` | `27ed12dabb2f55d74217f1e0fdb136d0fe8c2c6fc3d48823521a12e5b8e31a51` | 20334179 | `797a626fc326d9377b4ed5fcd16e98dcc1c3cbed19daecdd477488b19ddc077a` | 21087335 |

前綴證明:
```
head -c 939969 .dev/test-runs.jsonl       → t146-s3c-runs-prefix.bin     sha256 361e2f4ba1760bce9b5859eab273a5f45e7578a7ba478e98d9d05dac683866a8
head -c 20334179 .dev/test-sessions.jsonl → t146-s3c-sessions-prefix.bin sha256 27ed12dabb2f55d74217f1e0fdb136d0fe8c2c6fc3d48823521a12e5b8e31a51
```
⇒ 兩者都等於 LA ⇒ 只追加(+13598 / +753156 bytes);追加的內容沒有打開讀。

### R3 聲明

紅燈由本機帳本記錄,對應 HEAD = S3c-146-1(`e79c393d800c7c68fbf7afe6f5d9082afbaa6a03`),test blob = `3c75d69a142aa34ecf8ea29a667969d1cb673c08`。帳本在 `.dev/`(ignored),不在 git 內;本審計只記錄雜湊與前綴證明。
