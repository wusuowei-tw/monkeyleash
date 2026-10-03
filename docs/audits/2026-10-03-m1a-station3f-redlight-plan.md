# 票 145(M1-a)Station 3f-0 紅燈規劃 —— `--pdb`(xix)與 S5e-F2 / F3 / F4

- 依據:票 145〈三十九〉39.3 的 Station 3f 範圍(以該節原文為準)。
- 基準(BASELINE):`e0459be46bfa5d3f7514526e57cf1f05127bb841`(S5e-1)。產品碼與 TARGET 相同。
- 程式碼引用:`<TARGET>` = `0139a7e803fc2d41eb354f1196a6206cfe304701`,格式 `<TARGET>:<路徑>:<行號>`。
- 環境:pytest 9.1.1(`python -m pip show pytest`)、Python 3.11。
- pytest 原始碼引用寫 `_pytest/<檔>:<行>`;CPython 標準庫寫 `ntpath.py:<行>`。
- **本輪沒有執行任何 pytest,也沒有寫任何 Python probe。** 下文的行為全部是讀原始碼推得的,紅綠預測也都未經實測(P9)。

---

## P1 S5e-F1(`--pdb`)

### 1.1 `usepdb` 的定義

| 項 | 值 | 出處 |
|---|---|---|
| 選項 | `--pdb` | `_pytest/debugging.py:43-48` |
| dest | `usepdb` | `_pytest/debugging.py:45` |
| 型別 / action | `store_true` ⇒ bool | `_pytest/debugging.py:46` |
| 預設值 | `False`(store_true 的 argparse 預設) | 同上 |
| 註冊者 | `_pytest.debugging` 的 `pytest_addoption` | `_pytest/debugging.py:41` |

### 1.2 `usepdb` 的全部使用點(Grep `usepdb` 於 `_pytest/`)

| # | 位置 | 作用 | 對 pass 語意的影響 |
|---|---|---|---|
| U-1 | `_pytest/debugging.py:70-71` | 為真時註冊 `PdbInvoke()`,名稱 `pdbinvoke` | 失敗後進 post-mortem(1.3)。`PdbInvoke` 定義在 `_pytest.debugging` ⇒ `classify_plugins` 判為 **builtin**(`<TARGET>:.claude/hooks/redlight.py:612-615`),所以 (vii) 擋不到 |
| U-2 | `_pytest/runner.py:262-267` | 為真時 `KeyboardInterrupt` **不在** reraise 清單 | Ctrl-C 變成一筆 failed report 並進 pdb;用 `c` 繼續的話 session 不中斷(沒有 `--pdb` 時是 exit 2 ⇒ D) |
| U-3 | `_pytest/doctest.py:410-417` | 為真時關掉 `doctest_continue_on_failure` | 第一個失敗就停在該 doctest,只會更早失敗,屬更嚴 |
| U-4 | `_pytest/unittest.py:393-404` | 為真時延後 `TestCase.tearDown` | 執行順序改變(tearDown 推遲到 teardown 階段) |

另有 `--pdbcls`(`usepdb_cls`)與 `--trace` 的 debugger 進入點,見 P2。

### 1.3 `--pdb` 下 post-mortem 後 `continue` 的執行路徑

1. `_pytest/runner.py:249-253`:`CallInfo.from_call` 執行 call 階段;測試拋出例外。
2. `_pytest/runner.py:254-256`:先 makereport、**先 logreport**。這一筆 failed report 已經交給 conftest 的 `pytest_runtest_logreport`(`<TARGET>:tests/conftest.py:207-223`)。
3. `_pytest/runner.py:257-258`:`check_interactive_exception` 為真(`:270-284`)⇒ `pytest_exception_interact`。
4. `_pytest/debugging.py:286-297`:`PdbInvoke.pytest_exception_interact` 暫停擷取,呼叫 `_enter_pdb`。
5. `_pytest/debugging.py:337-365`:`_enter_pdb` 印 traceback,呼叫 `post_mortem`。
6. `_pytest/debugging.py:399-404`:`post_mortem` 建立 debugger(`_init_pdb("post_mortem")`,`:240-276`),進入 `p.interaction(None, tb)`,**等使用者輸入**。
7. 使用者可以用 `!<任意 Python>` 改行程內狀態(pdb 標準功能),然後輸入 `c`:
   - `_pytest/debugging.py:164-188`:`do_continue` 恢復擷取、呼叫 `pytest_leave_pdb`、設 `_continued`。
   - 回到 `:402-403`:`p.quitting` 為假 ⇒ **不呼叫** `outcomes.exit` ⇒ `post_mortem` 正常返回。
8. 返回 `_pytest/runner.py:259`,`call_and_report` 回傳。session 照常進行後面的身分與檔案,**後面的測試是在被改過的行程狀態下執行**。

對照 `q` 的路徑:`_pytest/debugging.py:195-206`(`do_quit` ⇒ `outcomes.exit`)⇒ exit 2 ⇒ D。3e-0 規劃的 O-13 只考慮了這一條(見 P3)。

### 1.4 (xix) 的落點(4f 實作用;本輪不改 .py)

| 層 | 落點(TARGET 行號) | 內容 |
|---|---|---|
| 事實清單 | `<TARGET>:.claude/hooks/redlight.py:462-465` `COMPLETENESS_OPTIONS` | 加 `"usepdb"`。producer 經 `<TARGET>:tests/conftest.py:369-370` 自動以 `getattr(option, "usepdb", None)` 讀,經 `_plain` 落帳(bool 原樣) |
| 型別 | `<TARGET>:.claude/hooks/redlight.py:707`(缺鍵 ⇒ problems)與 `:743-746`(`for key in ("runxfail", "trace")` 加 `"usepdb"`:非 bool ⇒ problems) | 缺欄、None、字串、int 都進 problems ⇒ `:776-777` unknown |
| 值判定 | `<TARGET>:.claude/hooks/redlight.py:799`(與 (xv)(xvii) 同一句) | `options["usepdb"] is not False` ⇒ unknown |
| 出口 | `<TARGET>:.claude/hooks/redlight.py:820` | 仍是唯一的 `return "true"`;(xix) 只增加一個 `return "unknown"` |
| docstring | `<TARGET>:.claude/hooks/redlight.py:766` 附近 | 補一行 (xix) |

判定為 **unknown**,不是 false:與 (xvii) `trace` 同類(執行模式在支援邊界之外),不是縮小機制(縮小機制才判 false,見 `:803-805`)。

---

## P2 `usepdb_cls`(待證明項)

### 2.1 全部讀取點

Grep `usepdb` 於 `_pytest/` 只有一個讀 `usepdb_cls` 的地方:

| # | 位置 | 說明 |
|---|---|---|
| C-1 | `_pytest/debugging.py:117` | `pytestPDB._import_pdb_cls` 內 `cls._config.getvalue("usepdb_cls")`;有值時才 `importlib.import_module(modname)`(`:122-137`),否則用 `pdb.Pdb`(`:138-141`) |

`--pdbcls` 在解析時只做字串切分(`_validate_usepdb_cls`,`_pytest/debugging.py:30-38`),**不 import**。

### 2.2 `_import_pdb_cls` 的呼叫鏈(它只在 debugger 被建立時執行)

`_import_pdb_cls` 只被 `_init_pdb` 呼叫(`_pytest/debugging.py:272`)。`_init_pdb` 的呼叫者:

| # | 呼叫者 | 何時會跑 | `usepdb=False` 且 `trace=False` 時 |
|---|---|---|---|
| D-1 | `post_mortem`(`:399-404`) | 由 `PdbInvoke` 的 `pytest_exception_interact`(`:286-297` → `_enter_pdb` `:364`)與 `pytest_internalerror`(`:299-301`)呼叫 | `PdbInvoke` 只在 `usepdb` 為真時註冊(`:70-71`)⇒ **不會跑** |
| D-2 | `wrap_pytest_function_for_tracing`(`:311-327`,`:316`) | `PdbTrace.pytest_pyfunc_call`(`:304-308`,只在 `trace` 為真時註冊 `:68-69`)與 `maybe_wrap_pytest_function_for_tracing`(`:330-334`,條件 `getvalue("trace")`;呼叫者 `_pytest/unittest.py:382-387`) | **不會跑** |
| D-3 | `pytestPDB.set_trace`(`:278-283`) | 被執行的程式碼呼叫 `pdb.set_trace()`(`pytest_configure` 把它換成 `pytestPDB.set_trace`,`:76`)、`pytest.set_trace()`(`pytest/__init__.py:96`)、或 `breakpoint()`(CPython 預設 hook 依 `PYTHONBREAKPOINT` 解析到 `pdb.set_trace`,依 CPython 文件) | **只在被執行的程式碼自己呼叫時才會跑** |

Grep `post_mortem(`、`_enter_pdb(`、`maybe_wrap_pytest_function_for_tracing`、`pytestPDB.` 於 `_pytest/`(排除 `debugging.py`),只命中 `_pytest/unittest.py:382, 387`,沒有其他進入點。

### 2.3 結論:**(a) 不能單獨改變執行**

- `usepdb=False` 且 `trace=False` 時,debugger 只會在 D-3 被叫出,而 D-3 的唯一觸發途徑是**被執行的程式碼自己**呼叫 `breakpoint()` / `pdb.set_trace()` / `pytest.set_trace()`。
- 沒有這種呼叫時,`usepdb_cls` 從頭到尾不會被讀取(C-1 唯一讀點在 D-1–D-3 之內),`modname` 也不會被 import。
- 有這種呼叫時,改變行為的是「被執行的程式碼要求進入 debugger」這件事,不是 `--pdbcls`。沒有 `--pdbcls` 時,同一段程式碼一樣會進入互動的 `pdb.Pdb`,人一樣可以改狀態再 `c`。
  - 這屬於 **P-1 殘餘 / scope 外 S-2**(行程內程式碼要求的行為;3e-0 規劃 I-10 對 `PYTHONBREAKPOINT` 也是同一判斷)。
  - `--pdbcls` 指向的類別若是非互動、會自動改狀態的 debugger,仍需要被執行的程式碼先呼叫進入點,同屬 P-1。
- **建議**:`usepdb_cls` **不加入** (xix)。改寫一支 regression-lock(P7 的 R5):`--pdbcls=pdb:Pdb` 單獨出現時仍為 `"true"`,避免不必要的 fail-closed。

---

## P3 複查 3e-0 規劃的選項盤點

出處:`f9d67d8e83778741cd5dcaf8ad13f11602d9b0b5:docs/audits/2026-10-03-m1a-station3e-redlight-plan.md`(以下稱 3e-0)。
檢查對象:3e-0 判為 (E)「不影響」的 33 列,與判為 (D)「只改 reporting」的 6 列。
檢查方式:問「這個理由是否只涵蓋單一路徑」,比照 O-13 的漏洞型態(只考慮 quit,沒考慮 continue)。

**只盤點,不擴大合約。**

### 3.1 有未涵蓋路徑的列

| 選項 | 3e-0 原判理由 | 未涵蓋的路徑 | 新結論與證據 |
|---|---|---|---|
| **O-13 `--pdb`** | 「只在失敗後進 post-mortem,report 已經是 failed;quit ⇒ exit 2 ⇒ D」(3e-0 第 105 行) | **continue**:人改行程狀態後 `c`,後面的測試在被改過的狀態下通過(P1 1.3)。另有 U-2 / U-4 兩個執行面的改變 | 已由〈三十九〉裁定為 (xix),本輪處理 |
| **I-9 `PYTHONPATH`**(及同族 F-5 `no_user_site`、F-6 `no_site`、F-12 `isolated`、F-16 `safe_path`) | 「改的是模組解析(受測物件是哪一份),不是 pass 語意。本 repo 的測試以檔案路徑載入受測物件」(3e-0 第 49 行) | 理由**只涵蓋本 repo 的載入寫法**。合約是框架層:下游 repo 的測試若以 `import pkg` 載入受測物件,`PYTHONPATH`、site-packages 裡另一份已安裝的同名套件、或 `-P` 讓 `sys.path[0]` 不同,都會讓測試**對另一份程式碼**通過。此時 passed 為真,但它證明的不是工作樹裡的程式碼 | **待 Jeff 裁**(P10 第 5 項)。性質是「受測物件的身分」,不是「斷言有沒有執行」;合約目前只鎖 `pyproject.toml` 與 `tests/conftest.py` 的 blob((xi)),沒有鎖受測模組的來源 |
| **I-6 pytest 改寫快取** | 「副檔名依 `__debug__` 區分;讀取時驗 magic / mtime / size」(3e-0 第 46 行) | 驗證只比 **mtime 的整數秒與 size**(`_pytest/assertion/rewrite.py:311-312, 368-369, 385-389`)。同一秒內、大小不變的編輯,會載入**舊的**改寫結果 ⇒ 執行的是舊版測試程式碼。非改寫模組的 CPython pyc 也是同一種 mtime + size 規則(I-5 的領域;依 CPython 文件) | **待 Jeff 裁**(與 I-9 併為同一項)。屬意外、低機率,與 I-9 同為「執行的程式碼不是工作樹那一份」 |
| **O-16 `--capture` / `-s`** | 「只影響 stdout / stderr 擷取」(3e-0 第 108 行) | 擷取時 stdin 被換成 `DontReadFromInput`,讀取就拋錯(`_pytest/capture.py:222-240`)。`-s` 時 stdin 是真的,**被執行的程式碼若呼叫 `input()`,人可以在執行中輸入答案** | 觸發途徑只有被執行的程式碼自己讀 stdin ⇒ 與 P2 同一判準,歸 **P-1 / S-2 殘餘**,不改合約 |

### 3.2 理由成立、沒有單一路徑問題的列

| 選項 | 複查結果 |
|---|---|
| I-5(最佳化 pyc 不會被非最佳化執行載入) | 成立;依 CPython 檔名規則。內容與檔名不符的情形就是 I-7(已列殘餘) |
| I-8 直譯器 `-W` / `PYTHONWARNINGS` | 成立;〈三十五〉35.1 1 (d) 已外部實測三種寫法 |
| I-10 `PYTHONBREAKPOINT` | 成立;唯一觸發是被執行的程式碼呼叫 `breakpoint()`(P2 D-3 同一判準) |
| F-1–F-4、F-7、F-9、F-11、F-13–F-15、F-17 | 成立;這些旗標只會更嚴、只影響報告,或在 session 結束後才生效 |
| A-1、A-4、A-7、A-8 | 成立;改寫範圍與 pass hook 不會把失敗轉成通過 |
| O-5(mark filterwarnings) | 成立;屬已提交的測試程式碼 |
| O-7 `--max-warnings` | 成立;只會更嚴(`_pytest/main.py:128-136`) |
| O-12 停用 plugin 自動載入 | 成立;只會讓 anyio 消失,只會更嚴 |
| O-15 `--pdbcls` | 成立,見 P2 |
| O-17 logging 選項 | 成立;只影響依賴環境的斷言(S-3) |
| O-18 `--basetemp` / `--cache-clear` | 成立;給定的 basetemp 若已存在會先整個刪除再建立(`_pytest/tmpdir.py:154-159`),不會沿用舊內容 |
| O-19 pytester 選項 | 成立;子行程屬 S-1 |
| (D) F-8、F-10、A-2、O-6、R-1 | 成立;A-2 已由〈三十五〉35.1 1 (c) 外部實測 |

### 3.3 小結

- 新找到的 false-green 路徑只有一組:I-9 / I-6 這一族的「執行的程式碼不是工作樹那一份」。它不是 pass 有效性(斷言確實執行並評估了),而是受測物件的身分。列為 **待 Jeff 裁**。
- O-16 與 P2 同屬「被執行的程式碼自己要求互動」,歸 P-1 殘餘。
- 3e-0 判為 (C) selection / scope 的列與已鎖的列,本輪沒有重查。

---

## P4 S5e-F2 修法選項

### 4.1 pytest 9.1.1 自己用什麼基準解析 ini 的路徑值

| ini 種類 | pytest 的解析基準 | 出處 |
|---|---|---|
| `cache_dir`(string 型) | **rootpath**(`resolve_from_str(..., config.rootpath)`;另會先做 `expanduser` / `expandvars`) | `_pytest/cacheprovider.py:141`;`_pytest/pathlib.py:423-429` |
| `paths` 型(例 `pythonpath`) | **`inipath.parent`**;沒有 inipath 時才用 `invocation_params.dir` | `_pytest/config/__init__.py:1786-1793`(ini 模式)、`:1848-1853`(toml 模式) |
| `-c` / `inifilename` | invocation dir(屬 (1) 類,不在本題) | `_pytest/config/__init__.py:1533-1539` |

(x) 成立時 `inipath` 是 `<root>/pyproject.toml`,所以 `inipath.parent` 就是 root。因此,**pytest 解析 override 路徑值時從來不用 invocation dir**;TARGET 用 `inv_dir` 判越界(`<TARGET>:tests/conftest.py:378-379` → `<TARGET>:.claude/hooks/redlight.py:655`),與 pytest 的語意不一致。

### 4.2 三個方案

**甲:只對「路徑形狀」的值做越界判定**
- 定義「路徑形狀」:值含 `/` 或 `\`,或恰為 `.` / `..`(不含分隔符的值,例 `true`、`test_b`,一律原樣)。
- 基準仍是 `inv_dir`。
- 對 S5e-F2 重現情境:`strict_markers=true` 不是路徑形狀 ⇒ 原樣 ⇒ 修好。
- 缺口:`python_files=tests/test_*.py` 是路徑形狀(含 `/`)。從 root 外執行時,它以 `inv_dir` 解析會越界 ⇒ 仍被改寫成 `<outside>` ⇒ 非路徑的 glob 證據被改寫。
- 對 (viii):固定指令的 override 只有 `strict_markers=true` ⇒ 修好。

**乙(建議):override value 一律以 root 為基準判越界**
- `normalize_overrides` 的非絕對值改用 `_root_relative(val, root)`(不傳 base);producer 端不再傳 `inv_dir` 給它(或 redlight 端忽略)。
- 推論:以 root 為基準,一個**不含 `..` 段**的相對值 join 之後永遠在 root 之內 ⇒ 原樣。只有含 `..` 而且真的越界的值才會被改寫。所以 `true`、`test_b`、`tests/test_*.py` 從任何目錄執行都原樣,不需要另外定義「路徑形狀」。
- 與 pytest 的語意一致(4.1)。
- 對 S5e-F2 重現情境:`_root_relative("true", R)` 得 `true`,不是 `OUTSIDE` ⇒ 原樣 ⇒ (viii) 相等 ⇒ 其他條件成立時得 `"true"`。
- 對 (viii):比較的仍是正規化後的值;乙只會讓更多值原樣保留,不會讓任何值**變成** `strict_markers=true`。G5 的推論(〈三十九〉所附報告 G5)不受影響:「正規化後恰好等於常數」的輸入仍不存在。
- 合約面:〈三十五〉35.1 第 4 點的「相對 ⇒ 先以 invocation_params.dir 解析」寫在 (1) 類;(2) 類只寫「normpath 後越出 root」,沒有寫基準。乙等於把 (2) 類的基準明定為 root。**需要 Jeff 確認這個澄清**(P10 第 3 項)。

**丙:甲 + 乙**
- 只對路徑形狀的值、以 root 為基準判越界。
- 結果與乙相同(不含 `..` 的值在乙之下本來就原樣),只是多一層定義要維護。不建議。

### 4.3 對既有 3e 測試的影響

- 3e 的 E3p 測試用的 fake config,`invocation_params.dir` 就是 tmp root(`<TARGET>:tests/test_redlight.py:854`)⇒ `inv_dir == root`,三案的結果都與 TARGET 相同:
  - E3p-3 `[rel-escape]`:`cache_dir=../../e3p-user/c` 以 root 為基準仍越界 ⇒ `<outside>`。
  - E3p-4:非路徑值原樣。
  - `[win-abs]` / `[posix-abs]`:絕對路徑分支不變。
- 3d 的 `TestCollectionDefinitionCoverage` 與 3c / 3d 串接測試:override 值為 `strict_markers=true` 等非路徑值,invocation dir 也是 root ⇒ 不受影響。
- `inifilename` 與 `invocation.args` 屬 (1) 類,維持 `inv_dir` 為基準,與 pytest 一致(`-c` 與位置參數都相對 invocation dir)⇒ 不受影響。

---

## P5 S5e-F3 修法

### 5.1 位置

在 `_root_relative`(`<TARGET>:.claude/hooks/redlight.py:549-569`)中:

1. **保留** `:557-559` 的順序:先用**原字串**判「他平台絕對」(`_is_abs_path(text) and not host_abs` ⇒ `<outside>`)。不能先換分隔符,否則 `\\server\share\x` 在 POSIX 上會變成 `//server/share/x`,被當成本機絕對路徑,改走另一條分支(結果雖然仍是 `<outside>`,但判定理由改變了)。
2. **新增**:接著把 `text` 的 `\` 換成 `/`,再 `os.path.join` / `os.path.normpath`(`:561-563`)。
   - POSIX:`posixpath.normpath` 因此看得到 `..` 段,越界會被收合。
   - Windows:`ntpath` 本來就兩種分隔符都認,行為不變。
3. `:566-567` 維持現狀(relpath 之後再換一次分隔符、檢查 `../` 與 `_is_abs_path(rel)`)。

與 `_normalize_arg` 的一致性:`_normalize_arg` 先換分隔符(`:190`),再判他平台絕對(`:194`),再 normpath(`:199`)。兩者的差別只在「他平台絕對」的判定是看換前還是換後的字串。對 G3 的全部輸入,兩種順序得到的落帳結果相同(`C:\x` 換成 `C:/x` 仍命中 `_DRIVE_PREFIX`;`\\server\…` 換成 `//server/…` 時,兩邊都會走到 `<outside>` / None)。建議兩者都保留現有順序,不為了對齊而改 `_normalize_arg`。

附帶影響:POSIX 上檔名本身含 `\` 的合法路徑(例:`a\b.toml`)會被當成 `a/b.toml` 落帳。這只發生在 `-c`((ix) 一律 unknown)與 override 值((viii) 一律 unknown),判定不受影響,只是落帳字串改了。列入 P9。

### 5.2 G3 輸入表(修正後的預期落帳)

前提:Windows root `C:\projects\agent-gates`;POSIX root `/home/u/repo`;base = root。
- 「(1) 類」指 `inifilename` / `inipath` / 路徑型 plugin 名,即 `_root_relative` 的回傳值。
- override value:回傳 `<outside>` 時記 `<outside>`;是絕對路徑時記回傳值;其他情形**原字串**。

| 輸入 | Windows | POSIX | 與 TARGET 的差異 |
|---|---|---|---|
| `C:\x` | `<outside>` | `<outside>` | 無 |
| `C:/x` | `<outside>` | `<outside>` | 無 |
| `D:rel` | `<outside>` | `<outside>` | 無 |
| `\\server\share\x` | `<outside>` | `<outside>` | 無 |
| `\\?\C:\x` | `<outside>` | `<outside>` | 無 |
| `/etc/x` | `<outside>` | `<outside>` | 無 |
| `../../x` | `<outside>` | `<outside>` | 無 |
| `sub/x` | `sub/x` | `sub/x` | 無 |
| 混用分隔符、會越界 `sub\..\..\..\x` | `<outside>` | **`<outside>`** | POSIX 由 `sub/../../../x` 改為 `<outside>`(S5e-F3) |
| 混用分隔符、不越界 `sub\y/z` | `sub/y/z` | `sub/y/z` | 無(override value 時記原字串 `sub\y/z`) |
| 跨磁碟 `D:\x`(root 在 `C:`) | `<outside>` | (不適用) | 無 |
| root 內絕對 `<root>\tests\conftest.py` | `tests/conftest.py` | `tests/conftest.py` | 無 |

---

## P6 S5e-F4

- 改法:`_IDENTIFIER`(`<TARGET>:.claude/hooks/redlight.py:540`)的比對改成整串比對。
  - 寫法一:`re.compile(r"[A-Za-z0-9_.\-]+")` 配 `_IDENTIFIER.fullmatch(name)`。
  - 寫法二:pattern 結尾改 `\Z`,保留 `.match`。
  - 兩者語意相同;建議 `fullmatch`(讀的人不需要知道 `$` 的換行例外)。
- 影響範圍:
  - `_IDENTIFIER` 只在 `_plugin_name`(`:582`)使用(`git grep` 於 TARGET:`re.compile` / `.match(` 只命中 `:539, 540, 546, 582`)。
  - `_DRIVE_PREFIX`(`:539`)沒有 `$`,不受影響。
  - 落帳:結尾帶換行的名稱改記 `<non-identifier>`。
  - 判定:kind 用原始名稱(`:604-615`);`blocked` 只看非空(`:780`)⇒ **判定不受影響**。
  - 既有測試:E3p-5 的名稱(`cacheprovider`、`pytest_cacheprovider`、`main`、數字 id、`anyio`)都不含換行 ⇒ 不受影響。

---

## P7 紅燈清單草案

### 7.1 driver 原則(沿用 3c-1b / 3d / 3e)

- 每次模擬執行載入全新的 conftest;tmp root 是真的 git repo。
- 新 helper 一律接在檔尾,既有 helper 只呼叫、不修改(例外只限 7.4 的授權)。
- 單點測試在同一支測試內放對照組。

### 7.2 「防錯欄位」測試的作法

**問題**:如果測試只用 `_COption(usepdb=True)` 這類人工屬性,4f 就算把欄位名寫錯(例如寫成 `pdb`),只要測試也用同一個錯名,仍然會綠。

**作法(建議;P10 第 2 項)**:由 pytest 自己的 parser 解析真實參數:
- 測試向 `pytestconfig` fixture 取得本次 session 的 `Config`,呼叫 `pytestconfig._parser.parse_known_args([...])`。
  - `_parser` 在 `_pytest/config/__init__.py:1128` 建立;`parse_known_args` 只做 argparse 解析,回傳 namespace,沒有其他副作用(`_pytest/config/argparsing.py:145-179`)。
- 得到的 namespace 就是 pytest 9.1.1 實際註冊的 dest 與預設值,直接當作 fake config 的 `option`,交給真實 conftest producer。
- 解析 `["--strict-markers"]`:`OverrideIniAction` 會帶出 `override_ini == ["strict_markers=true"]`(`_pytest/config/argparsing.py:491-503`),其他選項都是 pytest 的真實預設值 ⇒ 等同固定全套 ⇒ 對照組應為 `"true"`。
- 解析 `["--strict-markers", "--pdb"]`:破壞組。

**為何不違反既有規則**:
- 不執行巢狀 session、不收集、不跑任何測試、不啟子行程,只呼叫 argparse。
- 不寫入真實帳本(producer 寫 tmp root,與既有 driver 相同)。
- 不改全域狀態:`parse_known_args` 不觸發 `pytest_configure`,所以不會註冊 `PdbInvoke`。

**前提與代價**:
- 用了私有屬性 `_parser`。pytest 版本已由 (xiii) 鎖在 9.1.1。
- 結果依賴本次 session 載入的 plugin 註冊了哪些選項。例如以 `-p no:cacheprovider` 執行時,`lf` 不存在 ⇒ 對照組判 unknown ⇒ 測試失敗,而且是大聲失敗,不會靜默變綠。

**替代方案(P10 第 2 項 B)**:自建 `Parser(_ispytest=True)`,只呼叫 `_pytest.debugging.pytest_addoption(parser)` 後解析。
- 不依賴本次 session。
- 但只得到 debugging 群組的三個選項,其他欄位仍要人工補。
- 「固定全套 ⇒ true」的對照組就不再是真實解析的結果。

### 7.3 清單(完整 nodeid)

預測以本機 Windows、BASELINE `e0459be4…`(產品碼 = TARGET)為準;「紅」= 該支在 BASELINE 上失敗。

**tests/test_redlight.py**

| # | nodeid | 情境 | 分類 | BASELINE 預測與理由 |
|---|---|---|---|---|
| R1 | `tests/test_redlight.py::TestDebuggerModeCoverage::test_f3p_pdb_alone_is_not_full_coverage` | 對照 `usepdb=False` ⇒ `"true"`;破壞 `usepdb=True`,其他事實同固定全套 | behavior-red | **紅**:TARGET 不記也不判 usepdb(`<TARGET>:.claude/hooks/redlight.py:462-465, 795-802`)⇒ 破壞組得 `"true"` |
| R2 | `tests/test_redlight.py::TestDebuggerModeCoverage::test_f3p_a_missing_usepdb_fact_is_not_full_coverage` | 對照同上;破壞組的 option 沒有 `usepdb` 屬性 | behavior-red | **紅**:同 R1 |
| R3 | `tests/test_redlight.py::TestDebuggerModeCoverage::test_f3p_the_producer_records_usepdb_from_the_pytest_parser` | **防錯欄位**:7.2 的真實解析;`["--strict-markers", "--pdb"]` ⇒ 持久化 `options["usepdb"] is True`;`["--strict-markers"]` ⇒ `is False` | behavior-red | **紅**:持久化的 options 沒有 `usepdb` 鍵 |
| R4 | `tests/test_redlight.py::TestDebuggerModeCoverage::test_f3p_pdb_parsed_by_pytest_is_not_full_coverage` | 7.2 的真實解析;對照 `["--strict-markers"]` ⇒ `"true"`;破壞 `["--strict-markers", "--pdb"]` ⇒ `!= "true"` | behavior-red | **紅**:破壞組得 `"true"` |
| R5 | `tests/test_redlight.py::TestDebuggerModeCoverage::test_f3c_pdbcls_alone_does_not_lower_authority` | 7.2 的真實解析 `["--strict-markers", "--pdbcls=pdb:Pdb"]` ⇒ `"true"`(P2 結論 (a)) | regression-lock | **綠**:TARGET 不讀 usepdb_cls |
| R6 | `tests/test_redlight.py::TestOverrideBaseCoverage::test_f3o_an_invocation_dir_outside_the_root_keeps_non_path_override_values` | fake config 的 `invocation_params.dir` = root 的上一層;override `["strict_markers=true"]` ⇒ 持久化 `override_ini == ["strict_markers=true"]` | behavior-red | **紅**:`<TARGET>:.claude/hooks/redlight.py:655-656` 改寫成 `<outside>` |
| R7 | `tests/test_redlight.py::TestOverrideBaseCoverage::test_f3o_the_fixed_command_from_the_parent_dir_is_full_coverage` | 同 R6,`args == ["<root 目錄名>"]`(`_normalize_arg` 解析成 `.`)、其他事實同固定全套 ⇒ `"true"` | behavior-red | **紅**:`:784` 不相等 ⇒ unknown |
| R8 | `tests/test_redlight.py::TestOverrideBaseCoverage::test_f3o_an_escaping_relative_override_is_outside_from_the_parent_dir` | 同 R6,另加 `cache_dir=../../e3p-user/c` ⇒ 持久化行不含 `e3p-user` | regression-lock | **綠**:以上一層為基準也越界 ⇒ `<outside>`;乙之後以 root 為基準仍越界 |
| R9 | `tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_a_backslash_escape_is_outside_under_posix_semantics[override]` | 以 POSIX 語意(見 7.3 附註)呼叫 `normalize_overrides(["cache_dir=a\..\..\..\e3p-user\c"], "/home/u/repo", "/home/u/repo")` ⇒ 結果不含 `e3p-user` | behavior-red | **紅**:原字串保留(S5e-F3) |
| R10 | `tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_a_backslash_escape_is_outside_under_posix_semantics[config-file]` | 同上,`normalize_config_path("a\..\..\..\e3p-user\alt.toml", …)` ⇒ `<outside>` | behavior-red | **紅**:得 `a/../../../e3p-user/alt.toml` |
| R11 | `tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_g3_inputs_under_posix_semantics[<id>]`,9 個參數:`win-drive-backslash`、`win-drive-slash`、`drive-relative`、`unc`、`device`、`posix-abs`、`rel-escape`、`rel-inside`、`mixed-inside` | P5 表 POSIX 欄(不含「混用、會越界」那一列,它由 R9 / R10 負責) | regression-lock(×9) | **綠**:這 9 列在 TARGET 上已與修正後相同 |
| R12 | `tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_g3_inputs_under_windows_semantics[<id>]`,10 個參數:R11 的 9 個 + `cross-drive` | P5 表 Windows 欄(以 Windows 語意呼叫,見附註) | regression-lock(×10) | **綠** |
| R13 | `tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_a_backslash_escape_override_never_persists_a_path` | 經真實 producer、在**本機平台**上:override `cache_dir=a\..\..\..\e3p-user\c` ⇒ 持久化行不含 `e3p-user` | regression-lock(本機 Windows) | **Windows 綠 / POSIX 紅**:Windows 的 `ntpath.normpath` 本來就會收合 |
| R14 | `tests/test_redlight.py::TestIdentifierFullMatch::test_f3i_a_plugin_name_with_a_trailing_newline_is_not_persisted_verbatim` | 經真實 producer:`list_name_plugin()` 含 `("abc\n", None)` ⇒ 持久化 `blocked == ["<non-identifier>"]` | behavior-red | **紅**:`:582` 的 `match` + `$` ⇒ 原樣 `"abc\n"` |

**R9–R12 的平台語意模擬(附註;P10 第 4 項)**:
- 以 `monkeypatch.setattr(redlight, "os", <proxy>)` 只替換 **redlight 模組所見的** `os`。proxy 的 `path` 為 `posixpath`(POSIX 語意)或 `ntpath`(Windows 語意),其他屬性一律轉給真的 `os`(與 3e 的 `_ESys` 同一手法)。
- 不改全域 `os.path`。
- 只呼叫 producer 的正規化函式,不經 consumer。這不違反鏈條要求,因為鏈條要求針對的是 completeness 判定事實;本組驗的是落帳字串。
- 輸入一律是絕對 root 或 join 後的絕對路徑,所以 `posixpath` / `ntpath` 的 `abspath` 不會用到本機 `os.getcwd()` 的另一種格式。
- `posix-abs`(`/etc/x`)在 Windows 語意下依賴 Python 3.11 `ntpath.isabs("/x")` 為真(`ntpath.py:98-102`)。

**tests/test_status.py**

| # | nodeid | 情境 | 分類 | BASELINE 預測與理由 |
|---|---|---|---|---|
| S1 | `tests/test_status.py::TestDebuggerModeChain::test_f3p_pdb_pass_does_not_retire_a_known_red` | R1 固定全套:test_a failed ⇒ 已知紅;R2 `usepdb=True`,全 passed ⇒ 仍紅、不 green。情境斷言:R1 為 B、R2 合格且為 A | behavior-red | **紅**:R2 得 `"true"` ⇒ `<TARGET>:.claude/portable/status.py:474-475` 退紅、green |
| S2 | `tests/test_status.py::TestDebuggerModeChain::test_f3p_pdb_parsed_by_pytest_does_not_retire_a_known_red` | 同 S1,R2 的 option 由 7.2 真實解析 `["--strict-markers", "--pdb"]` 取得(防錯欄位的串接版) | behavior-red | **紅**:同 S1 |
| S3 | `tests/test_status.py::TestOverrideBaseChain::test_f3o_the_fixed_command_from_the_parent_dir_retires_the_red` | 已知紅;之後一次從 root 上一層執行的固定全套(R7 的事實)⇒ 退紅、green | behavior-red | **紅**:unknown ⇒ 不退紅 |
| S4 | `tests/test_status.py::TestDebuggerModeLocks::test_f3d_the_fixed_command_full_run_still_retires_the_red` | 固定全套、`usepdb=False` ⇒ 退紅、green | regression-lock | **綠** |

### 7.4 需要的授權(比照〈三十五〉35.1 第 5 點的格式)

> 授權(明文例外):4f 可在兩個共用預設 dict(`tests/test_redlight.py` 的 `_C_OPTION_DEFAULTS`、`tests/test_status.py` 的 `_S_OPTION_DEFAULTS`)只新增一個鍵 `"usepdb": False`(真實 pytest 預設值,`_pytest/debugging.py:43-48`),其他 helper 內容一律不改;並在「直接以 record_session 寫入 completeness dict」的 2 支測試的 `options` 補上 `u"usepdb": False`。assertion、docstring、test identity 一律不改。

S5e-F2 / F3 / F4 的修法不需要改既有測試(4.3、5.1、P6)。

**受影響的既有測試**(4f 加入 (xix) 後,若沒有上述授權,會因 `usepdb` 缺欄判 unknown 而失敗;判準是「經 `_COption` / `_CompletenessOption`,斷言 `"true"`、green 或 orphan」或「直接寫 dict」):

經 producer(由兩個 dict 的授權涵蓋):
- 3e-0 規劃已列的 12 支:
  - `tests/test_redlight.py::TestFileCoverage::test_b1c_a_file_argument_without_deselection_is_full_coverage`
  - `tests/test_redlight.py::TestFileCoverage::test_b1d_a_parent_directory_argument_is_full_coverage`
  - `tests/test_redlight.py::TestFixedCommandCoverage::test_b10_the_fixed_command_without_positional_args_is_full_coverage`
  - `tests/test_redlight.py::TestCompletenessCoverage::test_c3d_the_fixed_command_with_everything_off_is_full_coverage`
  - `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3i_lf_alone_is_not_full_coverage`
  - `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3i_maxfail_alone_is_not_full_coverage`
  - `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3i_shouldfail_alone_is_not_full_coverage`
  - `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3d_the_fixed_command_with_the_committed_config_is_full_coverage`
  - `tests/test_status.py::TestChainRegressionLocks::test_l3_a_full_directory_run_retires_the_red`
  - `tests/test_status.py::TestCompletenessLocks::test_c3d_the_fixed_command_full_run_still_retires_the_red`
  - `tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_builtin_root_conftest_and_known_dist_as_not_other`
  - `tests/test_status.py::TestCollectionDefinitionLocks::test_d3d_the_fixed_command_full_run_still_retires_the_red`
- 3e 新增、斷言 `"true"` 或 green 的 10 支:
  - `tests/test_redlight.py::TestPassValidityCoverage::test_e3o_an_optimized_interpreter_is_not_full_coverage[1]`(對照組)
  - `tests/test_redlight.py::TestPassValidityCoverage::test_e3o_an_optimized_interpreter_is_not_full_coverage[2]`(對照組)
  - `tests/test_redlight.py::TestPassValidityCoverage::test_e3o_a_missing_optimize_fact_is_not_full_coverage`(對照組)
  - `tests/test_redlight.py::TestPassValidityCoverage::test_e3x_runxfail_alone_is_not_full_coverage`(對照組)
  - `tests/test_redlight.py::TestPassValidityCoverage::test_e3w_a_pytest_warning_filter_alone_is_not_full_coverage`(對照組)
  - `tests/test_redlight.py::TestPassValidityCoverage::test_e3t_trace_alone_is_not_full_coverage`(對照組)
  - `tests/test_redlight.py::TestPassValidityCoverage::test_e3v_an_unrecognized_python_version_is_not_full_coverage`(對照組)
  - `tests/test_redlight.py::TestPassValidityCoverage::test_e3d_the_fixed_command_with_a_plain_interpreter_is_full_coverage`
  - `tests/test_redlight.py::TestPassValidityCoverage::test_e3a_plain_assert_mode_on_a_plain_interpreter_is_still_full_coverage`
  - `tests/test_status.py::TestPassValidityLocks::test_e3d_the_fixed_command_full_run_still_retires_the_red`

直接寫 dict(由 2 支的授權涵蓋):
- `tests/test_status.py::TestTestsUnderTicketUsesTheLatestRecordPerFile::test_a_file_that_went_red_then_green_counts_as_green`
- `tests/test_status.py::TestOrphans::test_a_renamed_red_test_is_orphaned_not_green`

合計 **24 支**(12 + 10 + 2)。3e 的 `_e_option` 經 `_d_option` / `_t_option` 建出 `_COption` / `_CompletenessOption`,所以由兩個 dict 的授權涵蓋;3e 程式碼本身不需要改。

**本清單的限制**:這 24 支是依「斷言需要 `"true"`」的判準,以 3e-0 的清單加上 3e 新增測試整理的,**沒有逐支重跑推演**。4f 報告應以實際結果核對(與 4e 報告 4e 節同樣的做法)。

### 7.5 預期的固定全套計數

基準:`collected 2021`,取自 S4e-1(`0139a7e8…`)的固定全套(4e 報告第 3 節;S4e-1 之後到 BASELINE 只有 docs 改動)。

| 項 | 計數 |
|---|---|
| 新增 | 35 支(behavior-red 12 + regression-lock 23;R11 計 9、R12 計 10) |
| 預期 collected | **2056**(= 2021 + 35) |
| 預期 failed(在 3f 紅燈 commit 上,本機 Windows) | **12**(R1、R2、R3、R4、R6、R7、R9、R10、R14、S1、S2、S3) |
| 預期其餘 | passed 2038(= 2015 + 23)、skipped 3、xfailed 3 |

POSIX(CI)上 R13 也會紅 ⇒ failed 13。

---

## P8 S5e-F5 更正(4e 報告 4e 表中 c3 生產端各列)

依據:
- c3 的 producer driver 用 `_c_plugins` / `_s_plugins`,它們把 anyio 配對到假 dist,而假 dist 的版本是 `"0"`(`<TARGET>:tests/test_redlight.py:790-794, 835-840`;`<TARGET>:tests/test_status.py:1911-1915, 1946-1961`)。
- `("anyio", "0")` 不在 `KNOWN_DISTS`(`<TARGET>:.claude/hooks/redlight.py:484`)⇒ kind `other`(`:606-608`)⇒ 第一道是 (vii′) `:778-779`。
- 這些 producer 驅動的 session 都帶齊 4d / 4e 欄位(型別允許 None),所以不會先在 `:776-777` 被擋下。

| 測試 | 4e 表原寫 | 正確的第一個擋下條件 |
|---|---|---|
| `tests/test_redlight.py::TestCompletenessCoverage::test_c3a_lf_silent_narrowing_is_not_full_coverage` | (viii) `:784-785` | **(vii′) `<TARGET>:.claude/hooks/redlight.py:778-779`**(`_c_plugins`,`<TARGET>:tests/test_redlight.py:976-977`) |
| `tests/test_redlight.py::TestCompletenessCoverage::test_c3c_an_exitfirst_run_is_not_full_coverage` | (viii) `:784-785` | **(vii′) `:778-779`**(`<TARGET>:tests/test_redlight.py:1015`) |
| `tests/test_redlight.py::TestCompletenessCoverage::test_c3b_a_session_without_completeness_facts_is_not_full_coverage` | `:776-777` | 正確(無須更正) |
| `tests/test_redlight.py::TestCompletenessCoverage::test_c3b_a_malformed_completeness_fact_is_not_full_coverage` | `:776-777` | 正確 |
| `tests/test_redlight.py::TestCompletenessCoverage::test_c3p_*`(consumer 三支) | `:776-777` | 正確(手寫 `_c_all_off()` 缺 4d 欄位) |
| `tests/test_status.py::TestSilentNarrowingChain` ×2 | (viii) `:784-785` | **(vii′) `:778-779`**(`_s_lf_pm` → `_s_plugins`,`<TARGET>:tests/test_status.py:2045-2056`) |
| `tests/test_status.py::TestEarlyStopChain::test_c3c_exitfirst_does_not_orphan_a_known_red`、`…::test_c3c_exitfirst_does_not_make_unrun_files_green` | (viii) `:784-785` | **(vii′) `:778-779`**(`_s_drive` 預設 pm,`<TARGET>:tests/test_status.py:2012-2013, 2059-2064`) |
| `tests/test_status.py::TestEarlyStopChain::test_c3c_stepwise_stop_is_d_and_retires_nothing` | exit 2 ⇒ D | 正確:`run_state` D(`<TARGET>:.claude/hooks/redlight.py:384-385`)⇒ status `<TARGET>:.claude/portable/status.py:456` 短路,不評估 coverage |
| `tests/test_status.py::TestEarlyStopChain::test_c3c_pytest_exit_zero_partial_file_is_not_green` | (viii) `:784-785` | **(vii′) `:778-779`**(`<TARGET>:tests/test_status.py:2158-2159`) |
| `tests/test_status.py::TestEarlyStopChain::test_setup_only_run_is_not_green` | (viii) `:784-785` | **(vii′) `:778-779`**(`<TARGET>:tests/test_status.py:2171-2173`) |
| `tests/test_status.py::TestLfFalseGreenChain::test_c3e_full_then_lf_does_not_produce_a_false_green`(R3) | (viii) `:784-785` | **(vii′) `:778-779`**(`<TARGET>:tests/test_status.py:2198`) |
| `tests/test_status.py::TestPluginProducerChain` 的 C3p-4 / 5 / 6 | (viii) `:784-785` | **(vii′) `:778-779`**(額外 plugin 本身就是 other,anyio 也是 other;`<TARGET>:tests/test_status.py:2260, 2276, 2295`) |

結論不變:這些測試都在 4e 新條件(`:795-802`)之前就被擋下。依〈三十九〉39.3,本更正寫進 3f 報告的 correction 段,不回寫 4e 報告。

---

## P9 殘餘與未證明

1. **全部結論都是讀原始碼推得的,沒有實測**,包括 P1 1.3 的 continue 路徑、P2 的呼叫鏈、P4 的 pytest 基準、P5 的表、P7 每一支的紅綠預測與 7.5 的計數。〈三十九〉39.2 的外部重現只證明了 S5e-F1–F4 成立。
2. **P2 D-3 的 `breakpoint()` 路徑**依 CPython 文件(`sys.breakpointhook` 預設依 `PYTHONBREAKPOINT` 解析成 `pdb.set_trace`),本機沒有 C 原始碼可引。
3. **S5e-F6**(override 的 key、`pythonwarnings` 原樣落帳):依〈三十九〉列入 privacy / provenance 追蹤票,本票不修。
4. **P-1 殘餘**:S5c-F4、S5d-F2;本輪新增歸入 P-1 的有兩項:P2 D-3(被執行的程式碼叫出 debugger,含 `--pdbcls` 指向的類別)與 P3 的 O-16(`-s` 下被執行的程式碼讀 stdin)。
5. **I-7**(刻意製作的最佳化 bytecode):維持殘餘。
6. **P3 新找到的 I-9 / I-6 族**(執行的程式碼不是工作樹那一份):待 Jeff 裁(P10 第 5 項)。在裁定之前,它是一條未被任何條件擋住的路徑。
7. **7.2 的私有屬性 `Config._parser`**:依賴 pytest 9.1.1 的內部結構;升版時由 (xiii) 讓 run fail-closed,但測試本身可能需要調整。
8. **P5 的附帶影響**:POSIX 上檔名本身含 `\` 的路徑會改以 `/` 落帳(只影響必定 unknown 的 run 的落帳字串)。
9. **`cache_dir` 的 `~` / 環境變數展開**(`_pytest/pathlib.py:424-425`):`-o cache_dir=~/x` 在乙方案下以原字串 `~/x` 落帳(不含使用者名稱),但 pytest 實際寫到家目錄。這種 run 必定 unknown((viii)),只是落帳字串無法表達實際位置。
10. **7.4 的 24 支**沒有逐支重跑推演(見 7.4 末段)。
11. **R13 只在 POSIX 上能紅**;本機的紅燈驗收看不到它的紅(由 R9 / R10 的模擬補上)。
12. CLEAN / REAL 層不在本輪範圍。

---

## P10 要 Jeff 裁的事

| # | 事項 | 選項 | 建議與理由 |
|---|---|---|---|
| 1 | `usepdb_cls` 是否加入 (xix) | **A**:不加,只寫 regression-lock R5。**B**:一併加入 (xix)(`usepdb_cls` 非 None ⇒ unknown) | **A**。P2:`usepdb=False` 且 `trace=False` 時,`usepdb_cls` 的唯一讀點只在 debugger 被建立時執行,而能建立 debugger 的只剩被執行的程式碼自己呼叫(P-1)。B 的代價是 `--pdbcls` 單獨出現時無法退紅,換不到任何保護 |
| 2 | 防錯欄位測試的取得方式 | **A**:`pytestconfig._parser.parse_known_args(...)`(本次 session 的完整 parser)。**B**:自建 `Parser(_ispytest=True)` + `_pytest.debugging.pytest_addoption` | **A**。只有 A 能讓「固定全套 ⇒ `"true"`」的對照組也是真實解析的結果(含 `--strict-markers` ⇒ `override_ini`)。兩案都用私有 API;A 依賴本次 session 的 plugin,缺選項時會大聲失敗 |
| 3 | S5e-F2 修法 | **甲**:只對路徑形狀的值判越界(基準仍為 invocation dir)。**乙**:override value 以 root 為基準判越界。**丙**:甲 + 乙 | **乙**。與 pytest 解析 `cache_dir`(rootpath)與 `paths` 型 ini(`inipath.parent`)的基準一致;不需要定義「路徑形狀」。甲在從 root 外執行時仍會改寫 `tests/test_*.py` 這類 glob。乙需要 Jeff 確認:〈三十五〉35.1 4 (2) 類的「越出 root」以 **root** 為基準(這是合約澄清) |
| 4 | S5e-F3 的紅燈怎麼在本機紅 | **A**:以 proxy 替換 redlight 模組所見的 `os`,用 `posixpath` / `ntpath` 模擬兩種平台(R9–R12),另加真實平台的 producer 測試 R13。**B**:只寫真實平台測試(本機 Windows 上全綠,只有 POSIX CI 會紅) | **A**。B 會讓 3f 的本機驗收看不到 F3 的紅,紅燈失去「為對的理由紅」的證據。A 只替換 redlight 模組的名稱,不動全域 |
| 5 | P3 新找到的「執行的程式碼不是工作樹那一份」(I-9 `PYTHONPATH` / site-packages 的另一份 / `-P`;I-6 同秒同大小的改寫快取) | **A**:列為殘餘,另開追蹤票(受測物件身分 / provenance),本票不處理。**B**:納入 M1-a,另立合約條件(例如記錄並比對受測模組的來源路徑與 blob) | **A**。它不是 pass 有效性(斷言確實執行並評估了),而是受測物件的身分;要鎖它,得記錄每個被 import 的模組的來源,成本與 3e-0 的「丙:枚舉白名單」同級,而且會擴大 S5d-F3 的路徑正規化面。若選 B,3f 範圍要重新規劃 |
| 6 | 7.4 的授權文字 | **A**:照 7.4 的文字授權(兩個 dict 各加 `"usepdb": False`;2 支直接寫 dict 的測試補 `u"usepdb": False`)。**B**:逐支在 22 處呼叫帶 `usepdb=False`,不改 helper | **A**。與〈三十五〉35.1 第 5 點同一做法;值是 pytest 的真實預設值 |
