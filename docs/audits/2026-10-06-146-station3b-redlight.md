# 票 146 第三站紅燈補完審計(3b-146 / Station 3b)

| 欄 | 值 |
|---|---|
| 日期 | 2026-10-06 |
| 進入基準 | S3-146-2 `ad8bf70c29bbb89294b168e82fe3c7973222b202` |
| S3b-146-0 | `dc81b19e5195c666051f9a508f8dd0953db8df85`(票 146:3b 裁決 (a)–(g)、方向 B、增補契約) |
| S3b-146-1 | `8727882f9643f3aa386b546fd2bac0b99438972c`(`tests/test_redlight.py`:改 `_surfaces` + 追加 7 個紅燈) |
| pipeline | `tickets / 146`(本輪未寫) |

---

## 【給裁決者】

1. 補了三類紅燈,共 7 個,紅燈總數 20:使用者層 skills / commands(T146-11、11b、11c、12、12b)、依賴方向 B(T146-13)、DECLARED_OK 的完整性前提(T146-14)。
2. 在乾淨的 S3b-146-1 上跑一次全套:**20 failed、2110 passed、5 skipped、3 xfailed**,合計 2138 = 上一輪 2131 + 7。20 個 failed 全部是 `TestTicket146ExtensionIntegrity`;沒有 ERROR。帳本只有追加。
3. 既有測試只動了 `_surfaces` 一個 helper,而且只刪一行(舊的 6 參數呼叫)。
4. 要第四站注意兩件事:(a)**T146-9 仍用 6 參數呼叫 `extension_surface_facts`**,實作成 8 參數、沒有預設值之後,它在 POSIX 上會因為 `TypeError` 紅,Windows 上被 skip 所以本機看不到;(b)**T146-13 的禁字掃描會命中 `redlight.py:18`、`:27` 現有註解裡的 `gate.py`**,第四站要一併改寫那兩行註解,測試才會綠。
5. 146 尚未生效;依裁決 (c),第四站接上 status / pre-commit 之前,票面只能寫「核心判定已提交;146 尚未生效」。

---

## 【給裁決助手】

### 三個 blocker 與對應紅燈

來源:GPT 審查(Jeff 轉述;**我沒有看到審查原文**,只看到 Jeff 的裁決 (a)–(g),以下依裁決歸納)。

| blocker | 裁決 | 紅燈 |
|---|---|---|
| 第三站契約漏掃 `~/.claude/skills` 與 `~/.claude/commands` | (a)、(d)、(e)、(g) | T146-11、11b、11c、12、12b |
| 共用 facts 層會反向載入 gate.py | (b) 方向 B | T146-13 |
| DECLARED_OK 沒有完整性前提 | (f) | T146-14 |

### 方向 B 的裁決(逐字)

(b) 共用 facts 層不得反向載入 gate.py。架構方向 = B：R4 樹比對純函式下沉到 redlight.py；gate.skill_mirror_violations 改為薄包裝，簽名、訊息、呼叫點不變；依賴方向 gate → redlight、status → redlight，redlight 不依賴任何專案模組。

### `_surfaces` 的 diff(唯一被修改的既有函式)

```
@@ -2867,6 +2867,11 @@ class TestTicket146ExtensionIntegrity:
         canon = base / "canon"
         _g_write(canon, "s/SKILL.md", u"skill\n")
+        user_skills = base / "user-skills"
+        user_skills.mkdir(parents=True, exist_ok=True)
+        user_commands = base / "user-commands"
+        user_commands.mkdir(parents=True, exist_ok=True)
         fn = self._api("extension_surface_facts")
-        return fn(str(dev), [str(synced)], str(canon), [], [], str(base / "absent.mcp.json"))
+        return fn(str(dev), [str(synced)], str(canon), [], [], str(base / "absent.mcp.json"),
+                  str(user_skills), str(user_commands))
```
`-` 行只有一行:`        return fn(str(dev), [str(synced)], str(canon), [], [], str(base / "absent.mcp.json"))`。
另一個 hunk `@@ -3080,2 +3085,130 @@` 全部是 `+`(7 個新方法,追加在 `test_t146_9` 之後)。
`git commit` 輸出:`1 file changed, 134 insertions(+), 1 deletion(-)`。
`tests/test_redlight.py` sha256(S3b-146-1)= `b8de3ae5b309e13012f87f4547e81d74b6f5e674657483eeedbedcbf21fdc19a`

### 新測試的失敗類型與 E 行

| 方法 | 失敗類型 | E 行 |
|---|---|---|
| `test_t146_11` | 缺 API | `AssertionError: v0 contract not implemented: extension_surface_facts` |
| `test_t146_11b` | 缺 API | `AssertionError: v0 contract not implemented: extension_allowlist_facts` |
| `test_t146_11c` | 缺 API | `AssertionError: v0 contract not implemented: extension_surface_facts` |
| `test_t146_12` | 缺 API | `AssertionError: v0 contract not implemented: extension_surface_facts` |
| `test_t146_12b` | 缺 API | `AssertionError: v0 contract not implemented: extension_allowlist_facts` |
| `test_t146_13` | 缺 API | `AssertionError: v0 contract not implemented: extension_surface_facts` |
| `test_t146_14` | 缺 API | `AssertionError: v0 contract not implemented: extension_surface_facts` |

- 11b、12b 先撞到 `extension_allowlist_facts`,因為 `_evaluate` 的引數裡 `self._facts(root)` 比 `self._surfaces(base)` 先求值。
- 既有 13 個的 E 行與 S3-146 審計相同(`T146-5`、`T146-6` 仍是 `AssertionError: []`)。

### 交給第四站的兩個已知問題(本輪依 B1 不得修)

1. **T146-9 的呼叫簽名過期**:`test_t146_9` 用 6 個參數呼叫 `extension_surface_facts(str(tmp_path / "no-dev-mods"), [], str(canon), [str(mirror)], [], str(tmp_path / "absent.mcp.json"))`。增補後的契約是 8 個參數,而且沒有寫預設值 ⇒ 實作後,它在 POSIX 上會因為 `TypeError` 紅,和實作正不正確無關;Windows 上被 skip,所以本機的綠燈看不出這件事。處理方式(擇一,需裁決):修改 T146-9(屬於既有測試的修改),或在契約裡給兩個新參數預設值。
2. **T146-13 的禁字命中既有註解**:`redlight.py:18`「…三處說法不一致(本檔、`gate.py`、`.gitignore`)。」;`:27`「…結果 `gate.py` 改成功…」。T146-13 要求全文不含 `"gate" + ".py"` ⇒ 第四站要改寫這兩行註解,否則就算依賴方向正確也不會綠。是否要把測試放寬到「排除註解」,需裁決。

### pytest(S3b-146-1,乾淨工作樹,只跑一次)

指令:`python -X utf8 -m pytest -q > <session scratchpad>/t146-s3b-pytest.txt 2>&1`(exit 1)

最後 20 行原文:
```
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_1
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_2
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_2b
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_2c
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_3
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_3b
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_4
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_4b
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_5
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_6
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_7
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_8
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_11
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_11b
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_11c
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_12
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_12b
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_13
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_14
20 failed, 2110 passed, 5 skipped, 3 xfailed in 185.86s (0:03:05)
```
(第 1 個 FAILED `test_t146_0a` 在倒數第 21 行。)

驗收:
- 沒有 `^ERROR ` 行,也沒有 `errors during collection`。
- collected = 20 + 2110 + 5 + 3 = **2138** = S3-146 審計的 13 + 2110 + 5 + 3 = 2131,加 7。
- 20 failed / 2110 passed / 5 skipped / 3 xfailed,與預期相同。
- 20 個 FAILED 全部是 `tests/test_redlight.py::TestTicket146ExtensionIntegrity::*`;除 `test_t146_9` 外的 20 個方法都在清單裡。
- `test_t146_9` 的 skip:`-q` 進度列第 23 行 `...........s...........FFFFFFFFFFFFFsFFFFFFF....` 中,`s` 夾在第 13 個 F 與後面 7 個 F 之間,與方法定義順序(9 在 8 之後、11 之前)一致。這是**位置推論**,沒有 `-rs`。

### 帳本(LA → LC)

| 檔 | LA sha256 | LA bytes | LC sha256 | LC bytes |
|---|---|---|---|---|
| `.dev/test-runs.jsonl` | `d75a56adb67dd2cd95a4eb6766de0018965472266f345acdfc0725a10a639cf3` | 927479 | `361e2f4ba1760bce9b5859eab273a5f45e7578a7ba478e98d9d05dac683866a8` | 939969 |
| `.dev/test-sessions.jsonl` | `30db5b558b4380c719eebf2b915b0230fc6c1284fba562ddf14812a834bd2f1d` | 19585659 | `27ed12dabb2f55d74217f1e0fdb136d0fe8c2c6fc3d48823521a12e5b8e31a51` | 20334179 |

前綴證明:
```
head -c 927479 .dev/test-runs.jsonl       → t146-s3b-runs-prefix.bin     sha256 d75a56adb67dd2cd95a4eb6766de0018965472266f345acdfc0725a10a639cf3
head -c 19585659 .dev/test-sessions.jsonl → t146-s3b-sessions-prefix.bin sha256 30db5b558b4380c719eebf2b915b0230fc6c1284fba562ddf14812a834bd2f1d
```
⇒ 兩者都等於 LA ⇒ 只追加(+12490 / +748520 bytes);追加的內容沒有打開讀。

### R3 聲明

紅燈由本機帳本記錄,對應 HEAD = S3b-146-1(`8727882f9643f3aa386b546fd2bac0b99438972c`)。帳本在 `.dev/`(ignored),不在 git 內;本審計只記錄雜湊與前綴證明。
