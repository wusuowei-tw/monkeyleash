# 票 146 第三站紅燈審計(3-146 / Station 3a)

| 欄 | 值 |
|---|---|
| 日期 | 2026-10-06 |
| 進入基準 | `db134904ebb79dc5dea8adf43e64e4ce4fcf6581`(D-146-0) |
| S3-146-0 | `22e9624fefa94afcb9964f1c3f396007d9f894c5`(票 146:Q1–Q6 裁決、四態、介面契約) |
| S3-146-0b | `441c2b44f36a64cd8a194d37d1a62776b6d6a76a`(票 146:停點裁決 = C) |
| S3-146-1 | `0993d217a27bce8119587bf1553df49a3521e79e`(`tests/test_redlight.py` 追加 14 個紅燈) |
| pipeline | `tickets / 146`(本輪未寫) |

---

## 【給裁決者】

1. 第三站紅燈已提交:14 個測試全部放進 `tests/test_redlight.py` 的一個新 class(依裁決 C,不新增檔案、不改 `.agents/`)。
2. 在乾淨的 S3-146-1 上跑了一次全套:**13 failed、2110 passed、5 skipped、3 xfailed**。13 個 failed 全部是新 class;第 14 個(T146-9,symlink)在 Windows 照規格 skip。沒有任何 collection / setup / teardown ERROR。
3. 失敗原因都是「契約還沒實作」:11 個是缺 API(訊息 `v0 contract not implemented: …`),2 個(T146-5、T146-6)是現行 R4 只比 SKILL.md、抓不到新情境。
4. 測試帳本只有追加:截到跑之前長度的前綴雜湊與跑之前完全相同。
5. 下一步是第四站實作;介面名稱已鎖在票 146,改名必須回票記一筆。

---

## 【給裁決助手】

### 停點與裁決

- 停點報告:`.dev/reports/2026-10-06T145908Z-ticket146-s3-halted-before-B.md`(本機證據,不在 git 內)。
- 停點原因:原指令要新增 `tests/test_extension_integrity_146.py`;但 `tests/test_manifest.py:196-219`(`test_every_file_under_tests_is_marked_or_explicitly_excluded`)要求 `tests/` 底下每個檔都要在 `.agents/portable-manifest.txt` 標 copy / skip(tests 條目逐檔列在 `:127-383`,例如 `:135 tests/test_redlight.py copy`)。原指令同時禁止改 `.agents/`,又要求 C3「其餘既有測試全部 passed」⇒ 三條無法同時成立。
- 三選一:A 准改 manifest 一行;B 把 test_manifest 的紅列為預期;**C 併入已登記的 `tests/test_redlight.py`**。
- 裁決:**C**(Jeff,2026-10-06)。理由(裁決原文沒有寫理由;以下是我對 C 的效果描述,不是裁決者的理由):不新增檔案、不改 `.agents/`,而 `tests/test_redlight.py` 已經標 copy,下游拿得到同一組紅燈。

### 步驟 0d:import 關係與落點

| 從 | 到 | 依據 |
|---|---|---|
| gate.py | redlight.py | `.claude/hooks/gate.py:2051-2065` `_redlight()`(路徑載入);呼叫點 `:2085`、`:2437`、`:2592` |
| status.py | gate.py | `.claude/portable/status.py:98-111` `load_gate(root)` |
| status.py | redlight.py | `.claude/portable/status.py:355-370` `load_redlight(root)` |
| redlight.py | gate.py | 無(`redlight.py:33-40` 只有標準庫;`:18/27/86/89/157` 提到 gate 的都是註解) |
| verify_gates.py | gate.py / redlight.py | `.claude/portable/verify_gates.py:238`、`:295` |

⇒ 落點 = `.claude/hooks/redlight.py`(兩邊都已引用、沒有循環)。

### 新測試

`tests/test_redlight.py` sha256(S3-146-1):`e59f51cd45f3fd5f10a72da5ea4efb53e77a97dbf750c47a863cf4a8b53777d3`
diff:單一 hunk `@@ -2792,0 +2793,289 @@ class TestKnownDistBoundaryAnyio4151:`,289 行新增、0 行刪除,起點在原檔最後一行(2792)之後。檔頂 import 沒有新增。

| 方法 | T146 | 失敗類型 | 訊息第一行(pytest `E` 行) |
|---|---|---|---|
| `test_t146_0a` | 0a 常數鎖 | 缺 API | `AssertionError: v0 contract not implemented: EXT_ALLOWLIST_FILE` |
| `test_t146_1` | 1 工作樹 ≠ HEAD | 缺 API | `AssertionError: v0 contract not implemented: extension_allowlist_facts` |
| `test_t146_2` | 2 未提交 | 缺 API | `AssertionError: v0 contract not implemented: extension_allowlist_facts` |
| `test_t146_2b` | 2b 未初始化 | 缺 API | `AssertionError: v0 contract not implemented: extension_allowlist_facts` |
| `test_t146_2c` | 2c 鍵集合多一個 | 缺 API | `AssertionError: v0 contract not implemented: extension_allowlist_facts` |
| `test_t146_3` | 3 dev-mods 未登記檔 | 缺 API | `AssertionError: v0 contract not implemented: extension_surface_facts` |
| `test_t146_3b` | 3b 指紋已登記 | 缺 API | `AssertionError: v0 contract not implemented: extension_surface_facts` |
| `test_t146_4` | 4 空殼目錄 ⇒ DECLARED_OK | 缺 API | `AssertionError: v0 contract not implemented: extension_surface_facts` |
| `test_t146_4b` | 4b synced 有檔 ⇒ UNKNOWN | 缺 API | `AssertionError: v0 contract not implemented: extension_surface_facts` |
| `test_t146_5` | 5 鏡像多出檔 | 行為紅(現行 R4 回 `[]`) | `AssertionError: []` |
| `test_t146_6` | 6 輔助檔內容不同 | 行為紅(現行 R4 回 `[]`) | `AssertionError: []` |
| `test_t146_7` | 7 兩欄分開、無禁詞 | 缺 API | `AssertionError: v0 contract not implemented: extension_allowlist_facts` |
| `test_t146_8` | 8 VERIFIED 不可達 | 缺 API | `AssertionError: v0 contract not implemented: EXT_VIOLATION` |
| `test_t146_9` | 9 symlink 指向正典外 | **skip**(Windows) | —— |

- T146-1、2、2b、2c 的第一個缺口是 `extension_allowlist_facts`;補上之後才會走到 `extension_surface_facts`、`extension_state`、`extension_status_lines`。⇒ 第四站要分段確認每一條都由**自己的斷言**變綠,而不是只因為前一個 API 補上了。
- **T146-9 的設計**:現行 R4 的 symlink 分支(`gate.py:3733-3736`)已經會抓到「指向正典之外」;只測 `skill_mirror_violations` 的話,它在 POSIX 上會是綠的,和「POSIX failed = 14」不符。所以 T146-9 另外要求同一筆違規也出現在 `extension_surface_facts(...)["r4_violations"]`(新契約)⇒ POSIX 上會因為缺 API 而紅,並同時守住保留分支的回歸。
- T146-9 有被收集的依據:`-q` 進度列(輸出第 23 行)為 `...........s...........FFFFFFFFFFFFFs...`。13 個 F 之後緊接一個 `s`;該 class 是 `test_redlight.py` 的最後一個 class,`test_t146_9` 又是最後一個方法 ⇒ 這個 `s` 就是 T146-9。**這是由位置推論的,pytest 沒有逐條列出 skip**(本輪只准跑一次,沒有加 `-rs` 重跑)。
- `dev_mod_files` 的元素形狀(`{"sha256": …, "note": …}`)沿用 D-146-0 設計報告的提案;**票 146 的契約沒有鎖這個形狀**。第四站若採別的形狀,T146-3b 與 T146-8 的輸入要跟著改,並回票記一筆。

### pytest(S3-146-1,乾淨工作樹,只跑一次)

指令:`python -X utf8 -m pytest -q > <session scratchpad>/t146-s3-pytest.txt 2>&1`(exit 1)

最後 15 行原文:
```
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/backup/x] - monkeyleash framework-updates/04:ABS_PATH 的 POSIX 分支是頂層目錄白名單,未列名的根目錄第二級看不見。**變綠的條件**:那張票把它改成通用比對(或補上這些根)。屆時本測試會 XPASS,而 strict=True 讓 XPASS 算失敗 —— 強迫有人回來刪掉這個 marker,而不是讓一條長期紅的測試變成噪音。
FAILED tests/test_redlight.py::TestTicket146ExtensionIntegrity::test_t146_0a
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
13 failed, 2110 passed, 5 skipped, 3 xfailed in 202.42s (0:03:22)
```

驗收(以 pytest 的結果行與 node 列表判定):
- (i) 沒有 collection / setup / teardown ERROR:輸出中沒有 `^ERROR ` 行,也沒有 `errors during collection`。14 個 T146 都有被收集(13 FAILED 有逐條列出 + 1 skip 由位置推論,見上)。
- (ii) failed 13 = 14 − 1(Windows skip 1)。
- (iii) 13 個 failed 全部是 `tests/test_redlight.py::TestTicket146ExtensionIntegrity::*`;每個非 skip 的方法都在清單裡。
- (iv) 其餘 2110 passed,包括 `test_redlight.py` 的 K 組(進度列中沒有 F)。⚠ 另有 4 個非 146 的 skipped 與 3 個 xfailed(`test_g1_guard.py`,`strict=True` 的既有預期失敗)。它們**不是 passed**,但也不是失敗;我把它們判為不違反 (iv),這是**解讀**,不是字面相符。跑這次之前的基線沒有量,所以「這 4 + 3 是既有的」是從 marker 推論的。

### 帳本(LA → LC)

| 檔 | LA sha256 | LA bytes | LC sha256 | LC bytes |
|---|---|---|---|---|
| `.dev/test-runs.jsonl` | `3637077aea4d2bdaa3138bf9b2aa28b5306ab9e9bc317d04df78ddfee3382778` | 915335 | `d75a56adb67dd2cd95a4eb6766de0018965472266f345acdfc0725a10a639cf3` | 927479 |
| `.dev/test-sessions.jsonl` | `6d18a5c6567054da5f2d09d7655b8aa29129c34cbf948be69e8a9c58d09dddcd` | 18838751 | `30db5b558b4380c719eebf2b915b0230fc6c1284fba562ddf14812a834bd2f1d` | 19585659 |

前綴證明:
```
head -c 915335 .dev/test-runs.jsonl      → t146-s3-runs-prefix.bin     sha256 3637077aea4d2bdaa3138bf9b2aa28b5306ab9e9bc317d04df78ddfee3382778
head -c 18838751 .dev/test-sessions.jsonl → t146-s3-sessions-prefix.bin sha256 6d18a5c6567054da5f2d09d7655b8aa29129c34cbf948be69e8a9c58d09dddcd
```
⇒ 兩者都等於 LA ⇒ 本次執行只追加,沒有改到既有內容(+12144 / +746908 bytes)。追加的內容**沒有打開讀**。

### R3 聲明

紅燈由本機帳本記錄,對應 HEAD = S3-146-1(`0993d217a27bce8119587bf1553df49a3521e79e`)。帳本在 `.dev/`(ignored),**不在 git 內**;本審計只記錄它的雜湊與前綴證明。
