# 票 145(M1-a)Station 5d 獨立審查報告

- 審查對象(TARGET):`889fbd8f666ea522ff6af172979a8d020e50b86b`
- 審查包所在 commit(S5d-0):`5ffae457f8c97d47f5cb649c107e584ca5219dd6`
- 審查包:`docs/audits/2026-10-02-m1a-station5d-review-package.md`(blob `8ea2d705057abcae7c7f5932837e92b991d42c99`)
- 審查者:獨立、無本票參與、未讀過往對話。
- pytest 執行 0 次。行為全部以紙上推演,依據為 TARGET 的程式碼與本機已安裝的 pytest 9.1.1 / pluggy 1.6.0 原始碼(只讀)。

---

## 1. 判決

**FAIL**

- 阻擋 1 項(S5d-F1)
- 非阻擋 5 項(S5d-F2–F6)

---

## 2. 身分核對結果(原始輸出)

```
$ git rev-parse 5ffae457f8c97d47f5cb649c107e584ca5219dd6:docs/audits/2026-10-02-m1a-station5d-review-package.md
8ea2d705057abcae7c7f5932837e92b991d42c99
```
⇒ 與指定值 `8ea2d705057abcae7c7f5932837e92b991d42c99` 相等。

```
$ git diff --name-only 889fbd8f666ea522ff6af172979a8d020e50b86b..5ffae457f8c97d47f5cb649c107e584ca5219dd6
docs/audits/2026-10-02-m1a-station4d-fix.md
docs/audits/2026-10-02-m1a-station5d-review-package.md
docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
```
⇒ 只有 `docs/` 底下 3 個檔(4d 報告、5d 審查包、票 145)。兩項檢查都通過,進入審查。

附帶核對(只讀):

```
$ git diff --stat 02a5e28adf5aee11a43d5a1063504f01beb1d67f 889fbd8f666ea522ff6af172979a8d020e50b86b -- .claude/portable/status.py
(無輸出)
```
⇒ status.py 在 4c → TARGET 之間未改,與審查包 A.4 的說法一致。

本機版本(`python -m pip show pytest pluggy anyio`,只取版本行;Location 行含本機路徑,遮成 `<user>`):
`pytest 9.1.1`、`pluggy 1.6.0`、`anyio 4.15.0`;Location `C:\Users\<user>\AppData\Local\Programs\Python\Python311\Lib\site-packages`。

---

## 3. G1–G13 逐題回答

以下 `T` = `889fbd8f666ea522ff6af172979a8d020e50b86b`。redlight 的行號以 `T:.claude/hooks/redlight.py` 為準。

### G1 S5c-F1 是否已修好 —— **成立**(四條管道都得不到 `"true"`)

共同機制:producer 讀的是 `config.option.override_ini`,也就是最終解析後的值(`T:tests/conftest.py:350`)。最終解析在 `_pytest/config/__init__.py:1620`,用的是合併後的整串 args。consumer 要求它**恰等於** `["strict_markers=true"]`(`T:.claude/hooks/redlight.py:705-706`),不等就判 `unknown`。

| 管道 | pytest 9.1.1 流程 | `override_ini`(推演) | TARGET 結果 |
|---|---|---|---|
| CLI `-o python_functions=test_b` | `-o` 是 `action="append"`(`_pytest/helpconfig.py:112-119`)。ini addopts 先被放到 args 最前面(`_pytest/config/__init__.py:1559-1562`),所以 `--strict-markers` 先出現 | `["strict_markers=true", "python_functions=test_b"]` | `:705` ≠ ⇒ `unknown` |
| `PYTEST_ADDOPTS="-o python_functions=test_b"` | 放在 CLI args 之前(`_pytest/config/__init__.py:1522-1528`),一樣進最終解析 | 同上 | `:705` ⇒ `unknown` |
| ini `addopts` 帶 `-o …`(工作樹改過) | 改了 `pyproject.toml` ⇒ worktree blob ≠ HEAD blob;同時 `override_ini` 多一筆 | 同上 | `:705` 先擋;`:711-714` 也會擋 |
| ini `addopts` 帶 `-o …`(已提交) | 同上,但 blob 相等 | 同上 | `:705` ⇒ `unknown`(另外鎖步測試 `T:tests/test_redlight.py:1487-1532` 在該 HEAD 會紅) |
| `@檔案` 帶 `-o …` | `fromfile_prefix_chars="@"`(`_pytest/config/argparsing.py:396`),argparse 在解析時展開 | 同上 | `:705` ⇒ `unknown` |
| `@檔案` 帶 nodeid | 展開後進 `config.args` ⇒ `invocation.args` 含 `::` | — | `:431-433, 440-441` ⇒ `"false"` |

pytest 內部用的值與落帳的值是否一致:`_inicfg` 吃的是 `ns.override_ini` 與 `known_args_namespace.override_ini`(`_pytest/config/__init__.py:1532-1539, 1564-1572`),兩者與 `:1620` 解析的是同一串 args。因此「pytest 實際套用的 override」與「落帳的 override」相同。

### G2 每條條件由哪幾行強制 —— 逐條**成立**;但有一個非縮小類的輸入能得到 `"true"`(見 S5d-F1)

| 條件 | 強制行(`T:.claude/hooks/redlight.py`) | 判定 |
|---|---|---|
| (i) 型別 | `:697-698` → `_completeness_problems` `:639-675` | unknown |
| (vii)(vii′) plugin kind / (dist, 版本) | `:699-700`;分類 `:551-553`(物件同一 `is` + `(名稱, 版本) in KNOWN_DISTS`) | unknown |
| (xii) `-p no:` | `:701-702`;取值 `:568-571`(producer `T:tests/conftest.py:349`) | unknown |
| (xiii) pytest 版本 | `:703-704`(producer `T:tests/conftest.py:339, 354`) | unknown |
| (viii) override 恰等於常數 | `:705-706`;常數 `:480` | unknown |
| (ix) `-c` | `:707-708` | unknown |
| (x) inipath | `:709-710` | unknown |
| (xi) blob | `:711-714`;取值 `:599-632` | unknown |
| (ii) lf / stepwise / stepwise_skip | `:715-718`(已不受 `cacheprovider_blocked` 影響) | false |
| (iii) maxfail / collectonly / setuponly / setupplan | `:719-723` | unknown |
| (iv) shouldstop / shouldfail | `:724-725` | unknown |
| (v) 縮小前全集 == collected | `:726-728` | false |
| (vi) 執行完成終態 | `:729-732`;`EXECUTED_OUTCOMES` `:488` | unknown |
| 唯一的 `"true"` 出口 | `:733` | — |

`_completeness_verdict` 只有一個呼叫點(`:438-439`),而且前面還有:invocation 涵蓋判定(`:420-437`)、deselected(`:418-419`)、收集錯誤(`:416-417`)、schema(`:411-412`)。我沒有找到任何能繞過上面任一條的「選擇縮小」型輸入。

**會繞過的輸入(不屬於縮小)**:`python -O`(或 `PYTHONOPTIMIZE=1`)加上 `--assert=plain`。這組輸入讓失敗的 assert 不執行。上表 14 條全部成立,於是得到 `"true"`(`:733`)⇒ 已知紅被退成 green。詳見 S5d-F1。

另一個要刻意才做得到的繞過:plugin 在 sessionfinish 前把自己 unregister,(vii) 就看不到它。詳見 S5d-F2。

### G3 雜湊比對語意 —— **成立**

- 工作樹側是 `git -C <root> hash-object pyproject.toml tests/conftest.py`(`:625`)。HEAD 側是 `git -C <root> rev-parse HEAD:pyproject.toml HEAD:tests/conftest.py`(`:626`)。兩側都是 Git blob 語意。`hash-object` 沒有加 `--no-filters`,所以會依路徑套用 `.gitattributes` / `core.autocrlf` 的轉換。
- **沒有**任何一處拿 Python 直接算的雜湊去和 Git blob 比。`content_hash`(`:46-62`,sha256)只用在 `record_run` 的 `impl_hash`(`:116-121`),不進 `committed_blobs`、也不進 `_completeness_verdict`。測試側的 blob 也是用真的 git 算的(`T:tests/test_status.py:575-577`;`T:tests/test_redlight.py:1137-1152`)。
- 各邊界情形(紙上推演):

| 情形 | 結果 | 依據 |
|---|---|---|
| 檔案未被追蹤 | `rev-parse HEAD:<p>` 退出碼非 0 ⇒ 兩個檔的 head 都是 None ⇒ unknown | `:606-607, 629, 712` |
| HEAD 不存在(新 repo) | 同上 ⇒ unknown | 同上 |
| 工作樹檔案不存在 | `hash-object` 失敗 ⇒ worktree 為 None ⇒ unknown | `:628, 712` |
| 路徑含空白 | argv 是 list、沒有經過 shell ⇒ 正常 | `:602` |
| git 不在 PATH | `FileNotFoundError` 被 `:604` 吞掉 ⇒ None ⇒ unknown | `:603-605` |
| 從子目錄執行 | `-C <_ROOT>`,而 `_ROOT` 來自 conftest 的 `__file__`(`T:tests/conftest.py:129`)⇒ 與 cwd 無關 | `:602` |
| 輸出不是 40 / 64 位小寫 hex,或行數不符 | None | `:608-611` |

方向:任何失敗都只會得到 None ⇒ unknown(fail-closed)。我沒有找到「內容不同卻判相等」的路徑。唯一的情形是只差 CRLF / LF,經正規化後相同,而那不改變 pytest 讀到的語意。

### G4 設定來源 —— **成立**

- `-c` / `--config-file`:`inifilename` 不是 None(`_pytest/config/findpaths.py:306-311`)⇒ `:707-708` unknown。即使指向 `pyproject.toml` 也一樣(D3c-2 鎖住,`T:tests/test_redlight.py:1329-1341`)。
- 搜尋順位是 `pytest.toml`、`.pytest.toml`、`pytest.ini`、`.pytest.ini`、`pyproject.toml`、`tox.ini`、`setup.cfg`(`_pytest/config/findpaths.py:166-174`),同一層找到就返回(`:181-199`):
  - 根目錄有未追蹤的 `pytest.ini` / `pytest.toml` / `.pytest.ini` / `.pytest.toml` ⇒ `inipath` 為該檔 ⇒ `:709-710` unknown。
  - 根目錄有 `tox.ini` / `setup.cfg`:它們排在 `pyproject.toml` 之後;只要 `pyproject.toml` 有 pytest 段就不會被採用,只列在 ignored_config_files,不影響設定。
  - `tests/` 底下的設定檔:只有給了位置參數 `tests` 時才會先搜到它,這時 `inipath` = `tests/…` ⇒ unknown。固定指令沒有位置參數,`determine_setup` 的 `args` 是空的(`_pytest/config/__init__.py:1533-1539`)⇒ 從 invocation_dir(根)開始搜,碰不到 `tests/` 的檔。兩種情形都不會得到 `"true"`。
- inipath 的正規化:`config.inipath` 是絕對路徑 ⇒ `_plugin_path_name` 做 relpath(`:521-530, 580-581`)⇒ `"pyproject.toml"`。Windows 的 `ntpath.relpath` 不分大小寫。限制:`_ROOT` 用 `resolve()`,`inipath` 用 `absolutepath()` 不解析 ⇒ 兩邊路徑形式不同時永遠 unknown(fail-closed,見 S5d-F6)。
- `--rootdir`(規劃檔 P5 #2 未推演):nodeid 改以新的 rootdir 為基準,而位置參數仍以 `_ROOT` 正規化,兩者對不上 ⇒ `covering` 為假 ⇒ unknown(`:426-442`)。帳本裡既有的 `tests/…` 鍵不會被碰到。沒有假綠。

### G5 plugin 邊界 —— **成立**(S5c-F4 現況未變,屬已知例外)

- known_dist 判定:plugin 物件以 `is` 比對,出現在 distinfo 配對中(`:551`),**而且** `(dist 名稱, 精確版本) in KNOWN_DISTS`(`:553`,常數在 `:473`)。只有名稱相同不算。
- 版本來源:`_dist_version` 先讀 `dist.version`;pluggy 的 `DistFacade.__getattr__` 會轉到 `importlib.metadata.Distribution.version`(`pluggy/_manager.py:62-74`)。讀不到就退回 `metadata["version"]`。缺失或空字串時回 None(`:501-508`)⇒ `("anyio", None)` 不在清單 ⇒ other ⇒ unknown。
- `(name, None)` 一律不得 `"true"`,有兩道:
  1. `blocked` 非空 ⇒ `:701-702`
  2. `_defining_module(None)` 得到 `"builtins"` ⇒ other(`:557-560`)⇒ `:699-700`
- S5c-X1:已依〈二十九〉2 (xii) 改成明文條件。`cacheprovider_blocked` 不再有判定權(`:715-718` 沒有引用它)。pluggy 的表示方式 `set_blocked` 會設 `_name2plugin[name] = None`(`pluggy/_manager.py:230-233`),`list_name_plugin` 原樣回傳(`:427-429`);一個 `-p no:X` 會產生 X 與 pytest_X 兩筆,cacheprovider 另加 stepwise 兩筆(`_pytest/config/__init__.py:850-857`)。`-p no:X -p X` 會 unblock(`:858-864`;`pluggy/_manager.py:239-247`)⇒ 已恢復註冊,不留 None,這是正確的語意。
- S5c-F4:現況未變(`:514-515` 仍看模組 `__name__`)。屬 H 段已知例外,不重複列。相鄰的新路徑(plugin 自行 unregister)另列為 S5d-F2。

### G6 pytest 版本事實 —— **成立**

- 來源:conftest 模組層 `import pytest` 的 `__version__`(`T:tests/conftest.py:339`)。conftest 由執行中的 pytest import,這時 `sys.modules["pytest"]` 已經是正在執行的那一份 ⇒ 工作目錄裡的同名模組影響不到。沒有任何環境變數參與。
- 只有行程內的程式碼(plugin 或測試的 monkeypatch)能改它。測試的 monkeypatch 在 teardown 就還原,早於 sessionfinish。plugin 不在白名單 ⇒ other。
- 缺失或不是字串 ⇒ None(`T:tests/conftest.py:354`)⇒ 不在清單 ⇒ `:703-704` unknown。fail-closed。

### G7 override_ini 比較與鎖步測試 —— **成立**(鎖步推導有小缺口,只會 fail-closed / fail-loud,見 S5d-F5)

- 比較方式:`comp["override_ini"] != list(COMMITTED_ADDOPTS_OVERRIDES)`(`:705`)是 list 相等,順序與重複都算。
- 鎖步測試 `T:tests/test_redlight.py:1487-1532` 逐一核對它引用的出處:
  - `_pytest/main.py:76-96`:三個 OverrideIniAction 旗標(`--strict-config` / `--strict-markers` / `--strict`)。**相符。**
  - `_pytest/config/argparsing.py:491-503`:附加 `f"{ini_option}={ini_value}"`。**相符。**
  - `_pytest/helpconfig.py:112-119`:`-o` / `--override-ini`,append(包審查包寫 113-116,實際範圍 112-119,不影響結論)。**相符。**
  - `_pytest/config/__init__.py:1547`(addopts type="args")、`:1559-1562`(放到最前面)。**相符。**
  - 全 `_pytest` 只有這三個 OverrideIniAction 使用點(Grep `OverrideIniAction`:`main.py:78, 85, 92`)。
- addopts 是 list 時:pytest 對 `args` 型別的 list 不再 shlex,直接用(`_pytest/config/__init__.py:1794-1795`)。鎖步測試寫 `list(addopts)`(`:1514`)。**相符。**
- 方向:常數 = `("strict_markers=true",)`。實際 `override_ini` 恰等於它,就表示實際**沒有其他 override**。所以鎖步推導就算有誤,結果也只會是「真實 run 全部 unknown」(fail-closed),或測試紅(fail-loud),不可能造成假綠。

### G8 producer 失敗安全 —— **大致成立**(逾時在 Windows 上不是嚴格上界,見 S5d-F4)

- 逾時:每個 git 子程序 `timeout=30`(`:603`),最多 2 次 ⇒ 正常情況下最多延遲約 60 秒。
- 例外:`_git_lines` 吞掉 `Exception`(`:604-605`),`committed_blobs` 再包一層(`:624-631`),`_completeness_of` 又包一層(`T:tests/conftest.py:335-357`)。最壞是 `completeness` 整份變 None ⇒ unknown,pytest 不會失敗。
- 既有 8 欄紀錄:`record_run` 迴圈(`T:tests/conftest.py:228-229`)在 `_completeness_of` 呼叫(`:252`)**之前**執行;E.3 diff 沒有任何 hunk 碰到 `record_run`(`:110-143`)⇒ 不受影響。
- 卡死:CPython `subprocess.run` 逾時後在 Windows 上會 `kill()`,接著呼叫**沒有逾時**的 `communicate()`(CPython 3.11 `subprocess.py:551-559`)。若 PATH 上的 git 是會再開子行程的啟動器,而孫行程握著 pipe,就可能卡住。本機 `where git` 第一筆是 `C:\Program Files\Git\mingw64\bin\git.exe`(真正的執行檔),所以本機不觸發。條件式風險,列為非阻擋。

### G9 測試沒有被放寬 —— **成立**

以 E.3(`git diff 5262828ab7f8fb89bb6bb85a6f63e24fdf852532..889fbd8f666ea522ff6af172979a8d020e50b86b`)逐一核對:

- `tests/test_redlight.py`:
  - b1c(新檔 `:532-536`)、b1d(`:550-554`)、b10(`:647-650`)、C3d-1(`:1062-1066`):只換 fixture(`_d_committed_root`、`_d_option()`、`_d_plugins(...)`、`inipath`)。
  - 檔尾新增 `test_d4_the_committed_addopts_override_constant_matches_pyproject`(`:1487-1532`),就是〈三十一〉裁決 3 指定的那一支。
- `tests/test_status.py`:
  - 570/571 `test_a_file_that_went_red_then_green_counts_as_green`(`:574-577, 590-594`)
  - ODC-2 `TestOrphans`(`:1344-1347, 1362-1367`)
  - L3(`:1736-1738`)
  - C3d-2(`:2215-2218`)
  - C3p-7(`:2312-2315`)
- 合計 9 支,與規劃檔 P4「4d 後會受新合約影響的既有測試」表(`T:docs/audits/2026-10-02-m1a-station3d-redlight-plan.md:269-279`)完全一致。
- 被刪的行(`-`)沒有一行是 `assert`、docstring 或 `def test_…`。3c / 3d 新增的測試區段(test_redlight `:1280-1485`、test_status `:2485-2565`)在 E.3 裡沒有 hunk。C3p-6(test_status `:2258-2299` 一帶)未動。
- C3p-7 的 driver 從 `_s_full_run_session` 換成 `_t_drive`。新的 `_t_plugins`(test_status `:2407-2415`)仍然包含 docstring 要求的三類(含數字名稱的 `_pytest.config` 內部物件、root conftest、配對 dist 的 anyio)⇒ 測試的語意沒有被削弱。

### G10 driver 忠實度 —— **成立**(有一處限制已記錄)

- tmp git repo 是真的建立並提交:`_d_committed_root` / `_t_committed` 都用 `check=True` 執行 `git init / config / add / commit`(test_redlight `:1137-1152`;test_status `:2358-2374`)。producer 的 `_ROOT` 被導到 tmp root(test_redlight `:290-300` 的 `monkeypatch.setattr(c, "_ROOT", tmp_path)`;test_status `:1505`)⇒ `committed_blobs` 真的在 tmp repo 上執行。
- `(name, None)`:`_d_plugins` 直接附加 `(n, None)`(test_redlight `:1197`);`is_blocked` 由同一份資料推出(`:1178-1179`),與 `pluggy/_manager.py:235-237` 的語意一致。fake dist 帶 `project_name` / `version` / `metadata`(`:1155-1161`),與 DistFacade 的讀取點一致。
- 「為了錯的理由通過」的風險:behavior-red 測試只斷言 `!= "true"`。如果 tmp git 失敗,blob 會變 None,這些測試也會通過。但同一套 driver 下有正向對照組:D3d-1 `== "true"`(`:1474-1485`)、D3i-1..3 的 control(`:1430-1432, 1442-1444, 1454-1456`)、D3d-2 green(test_status `:2550-2565`)。只要它們通過,就能排除「git 壞掉 ⇒ 全部 unknown」造成的假通過。限制:behavior-red 測試本身沒有同支內的對照組,所以「每支是由哪一條擋下」只能靠 G11 的紙上推演,沒有被測試鎖住。
- 忠實度的限制:`_DConfig.args` 固定為 `["tests"]`(`:1213`),`argv` 只是陳述用,producer 不讀它。因為 producer 只讀解析後的值,這不影響結論;但也表示 driver 沒有驗證「argv → config.option」這一段(那是 pytest 自己的行為,G1 已用原始碼推演)。

### G11 3d 的 13 支轉綠是否「為了對的理由」 —— **成立**(逐支追到第一個擋下的條件)

前提:driver 的其他事實都等於固定全套(D3d-1 證明那組事實會得 `"true"`)。`_completeness_verdict` 依序判定,以下列出第一個不成立的條件:

| # | 測試 | 第一個擋下的條件 | 行 |
|---|---|---|---|
| 1 | D3a-1 `test_d3a_an_override_ini_narrowing_is_not_full_coverage` | override_ini 多了 `python_functions=test_b` | `:705-706` |
| 2 | D3b-1 `test_d3b_…pytest_addopts…` | 同上(argv 裡沒有 `-o`,但事實裡有) | `:705-706` |
| 3 | D3c-1 `test_d3c_a_config_file_option_is_not_full_coverage` | `inifilename="alt.toml"` | `:707-708` |
| 4 | D3c-2 `test_d3c_…naming_the_committed_config` | `inifilename="pyproject.toml"` | `:707-708` |
| 5 | D3w-1 `test_d3w_an_unexpected_config_file…` | `inipath="pytest.ini"` | `:709-710` |
| 6 | D3w-2 `test_d3w_an_uncommitted_config_change…` | pyproject 的 worktree blob ≠ head | `:711-714` |
| 7 | D3w-3 `test_d3w_a_non_collection_edit…` | 同上(只改註解) | `:711-714` |
| 8 | D3w-4 `test_d3w_an_uncommitted_root_conftest_change…` | `tests/conftest.py` 的 worktree blob ≠ head | `:711-714` |
| 9 | D3v-1 `test_d3v_an_unrecognized_pytest_version…` | `pytest_version="9.2.0"`(monkeypatch 的是 conftest 所 import 的同一個 `pytest` 模組) | `:703-704` |
| 10 | D3v-2 `test_d3v_a_known_plugin_with_unrecognized_version…` | `("anyio","9.9.9")` ⇒ other | `:553` → `:699-700` |
| 11 | D3a-2 `TestOverrideIniChain::test_d3a_full_then_override_ini…` | R3 在 `:705` 判 unknown ⇒ status `:456-458` 不退紅、不 green | redlight `:705`;status `:456` |
| 12 | D3a-3 `…does_not_orphan_a_known_red` | 同上 ⇒ 走不到 orphan 分支(status `:464-468`) | 同上 |
| 13 | D3a-4 `…does_not_make_a_clean_file_green` | 同上 ⇒ `green_now=False`(status `:457`) | 同上 |

在第 1–8 支與第 11–13 支的情境裡,(v) / (vi) 都成立(快照 = collected、全部 passed)。所以它們不是靠舊防線擋下的,而是靠 4d 新增的條件。第 9、10 支也一樣。

### G12 隱私與欄位邊界 —— **在固定指令與正常用法下成立**;有刻意構造的輸入會漏(見 S5d-F3)

- `inipath` / `inifilename`:絕對路徑會被轉成 root 相對路徑或 `<outside>`(`:574-582`)。
- `override_ini`:值是絕對路徑時會被轉換(`:585-596`)。
- `config_blobs`:只有 hex。
- `pytest_version`:版本字串。
- `plugins[].dists`:名稱與版本。
- 4d 報告第 7 節對真實 session 的實測:使用者名稱 0 筆(這是報告方的量測,本審查沒有重跑,也不得重跑)。
- 漏洞(類別 (1),producer 自己產生的欄位):
  - `blocked`(`:568-571`)不做任何正規化。
  - `-p no:<絕對路徑>` 會額外產生 `pytest_<絕對路徑>`。這個名稱不是絕對路徑,所以在 `plugins[].name` 裡也照原樣寫入(`:549-550`)。
  - `inifilename` 是相對路徑但越出 root 時照原樣寫入(`:582`)。
  - 都要刻意構造才會發生,而且那次 run 本來就是 unknown。

### G13 既往修正未退步 —— **成立**

| 項目 | TARGET 上的強制點 |
|---|---|
| F1 schema fail-closed | `validate_session` `:292-355`(E.3 沒有改);status 對不合格的 run 不產生任何效果(status `:430-431`) |
| F2 D 無退紅權 | `run_state` `:379-380`;status `:456` |
| F3 nodeid 窄選 | `:431-433, 440-441` ⇒ false;沒有任何位置參數涵蓋 ⇒ unknown(`:442`) |
| F4 串接 | 3d 的串接測試經由真實 conftest 寫入、再由 status 讀回(test_status `:2485-2565`) |
| S5b-F1 `--lf` | `options.lf` 為 True ⇒ `:715-718` false;快照 ⇒ `:726-728` |
| S5c-F1 | 見 G1 |
| 向下相容 | 舊 session(4b 以前沒有 completeness;4c 沒有新欄位)⇒ `_completeness_problems` 回報缺欄(`:659-674`)⇒ unknown;`validate_session` 不要求 completeness ⇒ 舊 run 仍然合格,仍能加紅 |

---

## 4. 發現清單

### S5d-F1【阻擋】`python -O`(或 `PYTHONOPTIMIZE`)加上 `--assert=plain`,失敗的 assert 不執行,所有完整性事實與固定全套相同 ⇒ `"true"` ⇒ 已知紅被退成 green

**證據行**
- `T:.claude/hooks/redlight.py:457-458`:`COMPLETENESS_OPTIONS` 沒有 `assertmode`。
- `T:tests/conftest.py:322-354`:`_completeness_of` 沒有記 `sys.flags.optimize`,也沒有記 assertion 是否實際執行。
- `T:.claude/hooks/redlight.py:696-733`:全部條件都與 assertion 無關 ⇒ `:733` 回 `"true"`。
- `T:tests/conftest.py:202`:call 是 passed ⇒ 記成 `"passed"`。
- `T:.claude/portable/status.py:456, 474-475`:coverage 為 true 時,已知紅身分 passed ⇒ 移出紅;`green_now = True`。
- pytest 9.1.1(只讀原始碼):
  - `_pytest/assertion/__init__.py:28-41`:`--assert` 是一般的 store 選項,`dest="assertmode"`,不是 OverrideIniAction ⇒ 不進 `override_ini`。
  - `_pytest/config/__init__.py:1332-1346`:plain 模式不裝 rewrite hook,只呼叫 `_warn_about_missing_assertion`。
  - `_pytest/config/__init__.py:2041-2060, 2070-2075`:直譯器不執行 assert 時,pytest 只發出 `PytestConfigWarning`,文字是 **"ASSERTIONS ARE NOT EXECUTED and FAILING TESTS WILL PASS. Are you using python -O?"**。只是警告,不中止。

**具體情境(紙上推演)**
1. `tests/test_x.py` 有 `def test_a(): assert impl.f() == 2`(實作回 1)和 `def test_b(): assert True`。R1 固定全套 `python -X utf8 -m pytest -q` ⇒ test_a failed(exit 1)⇒ 已知紅 `tests/test_x.py::test_a`(status `:449-454`)。
2. R2:環境設 `PYTHONOPTIMIZE=1`、`PYTEST_ADDOPTS=--assert=plain`,執行**同一條固定指令**。
   - `override_ini == ["strict_markers=true"]`、`inifilename` None、`inipath` `pyproject.toml`、兩個 blob 相等、plugins 都是 builtin / root_conftest / anyio 4.15.0、`blocked == []`、`pytest_version` 9.1.1。
   - options 全部 False / maxfail 0;shouldstop / shouldfail False;快照 = collected。
   - 測試模組以最佳化層級 1 編譯,`assert` 被移除 ⇒ test_a 的 call passed。
3. `file_coverage(run, "tests/test_x.py")`:走完 `:411-439` 與 `:696-732` 全部條件 ⇒ `:733` 回 **`"true"`**。即使別的檔在 -O 下失敗(run_state B),依 ODC-1「其他 file 的 failure 不影響本 file」,結果不變。
4. `_apply_run`:`:474` 把 test_a 移出紅;`:475` `green_now = True`。

**錯誤輸出**:`tests green under ticket <N>` 列出 `tests/test_x.py`,`tests red` 不含它。
**應有輸出**:test_a 在正常執行下仍是紅的。依 ODC-1 第 2 項(「本次**確實執行並通過**」)與〈十七〉裁決 1(「不知道,就不是完整」),應判 `!= "true"`,檔案仍紅。

**為什麼判阻擋**
- 後果與 S5b-F1、S5c-F1 相同:status 的紅被一次假的「通過」退掉。這正是 M1-a 要防的事。
- 這是**使用方式**,不是對抗。只需要兩個環境變數,不用改任何檔案,也不用寫 plugin。S5c-F4 判非阻擋的理由(「防的是誤用,不是對抗」)在這裡反過來成立。
- 依專案分流判準「不改會不會讓別的規則失效」:會。退紅的證據層會接受 pytest 自己都聲明為「FAILING TESTS WILL PASS」的 run。
- H 段的已知例外 #3 講的是「非 ini 的 CLI 選項是否會**檔內縮小**」;`-O` 不是 pytest 選項,也不是縮小,不在任何已知例外裡。

**要裁決的事**:這是「通過是否有效」,不是「選擇是否完整」。是否屬於 M1-a 的範圍,由裁決者決定:
- A:納入 M1-a 的 completeness(producer 已讀得到 `sys.flags.optimize` 與 `config.option.assertmode`)。
- B:另開票並明文列為已知例外。

本審查依 ODC-1 第 2 項的字面判 A,所以判 FAIL。若裁決為 B,本項降為非阻擋,判決即無其他阻擋。

**未證明**:純屬紙上推演,沒有實際執行(本審查禁止 pytest)。rewrite 模式(預設)下只加 `-O` 時,測試模組的 assert 會被改寫成 `if/raise`(`_pytest/assertion/rewrite.py:350, 916-936`),不會被移除,所以本發現只成立於 plain 模式。

### S5d-F2【非阻擋】plugin 在 sessionfinish 前自行 unregister,(vii) 看不到它

- **證據**:
  - `T:tests/conftest.py:338`:plugin 清單只在 sessionfinish 讀一次 `list_name_plugin()`。
  - `pluggy/_manager.py:224-226`:`unregister` 會把名稱從 `_name2plugin` 刪掉。
  - `pluggy/_manager.py:422-425`:distinfo 不會跟著清掉,但 `classify_plugins` 只走訪 name_plugins(`T:.claude/hooks/redlight.py:547`)。
- **情境**:`-p myplug`。`myplug` 實作 `pytest_pycollect_makeitem`,在 `collect()` 內丟掉 test_a,然後在 `pytest_collection_finish` 呼叫 `config.pluginmanager.unregister(myplug)` ⇒ sessionfinish 時清單裡沒有它 ⇒ 沒有 other。快照與 collected 一樣少 ⇒ `"true"`。
- **影響**:要刻意撰寫才做得到,與 S5c-F4 同一類(行程內程式碼可以讓事實說謊)。建議把 S5c-F4 的追蹤票範圍擴大到「行程內 plugin 的自我隱藏」。

### S5d-F3【非阻擋】producer 自己產生的欄位,在刻意構造的輸入下會寫入未正規化的路徑

- **證據**:
  - `T:.claude/hooks/redlight.py:568-571`:`blocked_plugins` 照原樣寫 `str(name)`。
  - `:549-550`:`pytest_<絕對路徑>` 不是絕對路徑 ⇒ `shown = name`。
  - `:582`:相對的 `inifilename` 只換反斜線。
  - `_pytest/config/__init__.py:839-857`:`-p no:` 只拒絕 essential plugin 與結尾是 `conftest.py` 的名稱。
- **情境**:`-p no:C:\Users\<user>\x.py` ⇒ `blocked` 含 `C:\Users\<user>\x.py` 與 `pytest_C:\Users\<user>\x.py`;`plugins[].name` 含 `pytest_C:\Users\<user>\x.py`。`-c ..\..\Users\<user>\alt.toml` ⇒ `inifilename` 照原樣寫入。
- **影響**:違反〈二十五〉裁決 1 (1) 的字面。輸入要刻意構造,而且這種 run 一律 unknown,所以判非阻擋。

### S5d-F4【非阻擋】`timeout=30` 在 Windows 上不保證有上界

- **證據**:`T:.claude/hooks/redlight.py:602-603`;CPython 3.11 `subprocess.py:551-559`(Windows 分支在 `kill()` 之後呼叫沒有逾時的 `communicate()`)。
- **情境**:PATH 上的 `git` 是 Git for Windows 的 `cmd\git.exe` 啟動器,而真正的 git 子行程卡住、握著 stdout ⇒ 逾時後殺掉的是啟動器,`communicate()` 等待孫行程 ⇒ sessionfinish 卡住。
- **影響**:條件式。本機 PATH 第一筆是 `mingw64\bin\git.exe`,不觸發。而且 `hash-object` / `rev-parse` 不取鎖,實際卡住的機率低。

### S5d-F5【非阻擋】鎖步測試的 addopts 推導有幾個寫法沒涵蓋(只會 fail-closed / fail-loud)

- **證據**:`T:tests/test_redlight.py:1513, 1520-1531`。
- **情境**:
  - 合併短選項 `-qo key=val`:沒有被辨識。
  - `-o=key=val`:argparse 取值為 `key=val`,測試推成 `=key=val`。
  - addopts 欄位不存在,或改用 pytest 9 的原生 `[tool.pytest]` 表:`KeyError`。
- **影響**:常數與實際值不同時,真實 run 一律 unknown(G7 的方向論證),或測試紅。不會造成假綠。目前已提交的 `-ra --strict-markers` 不受影響。

### S5d-F6【非阻擋】`_ROOT` 用 `resolve()`,`inipath` 用 `absolutepath()`,路徑形式不同時永遠 unknown

- **證據**:`T:tests/conftest.py:129`;`T:.claude/hooks/redlight.py:521-530`(跨磁碟時 ValueError ⇒ `<outside>`);`_pytest/config/findpaths.py:182, 307`。
- **情境**:在 `subst` 磁碟機、或經 symlink 路徑以絕對位置參數執行 ⇒ `inipath` 正規化成 `<outside>` ⇒ `:709-710` unknown ⇒ 該 checkout 永遠不能退紅。
- **影響**:fail-closed,只影響可用性。4b 的位置參數正規化(`:191-196`)也有同樣的前提。

---

## 5. 沒有查、或無法判定的部分

1. **沒有任何實測**。所有 pytest / pluggy / CPython 行為都是讀原始碼推得的;S5d-F1 的結論同樣如此。
2. 沒有對 pytest 9.1.1 的**全部**選項做窮舉。本審查額外找到 `--assert`(S5d-F1),但沒有逐一走過其他非縮小類、可能改變 pass / fail 語意的輸入(例如 `-W` 與 mark 的優先順序,只做了概略判斷)。
3. `git hash-object` 在其他平台、其他 `core.autocrlf` / `.gitattributes` 組合下的一致性沒有驗(H.1 #4 已列)。
4. 審查包 E.1、E.2 的完整 diff 沒有逐行讀。本審查改為直接讀 TARGET 的完整檔案:redlight.py 全檔、conftest.py 全檔、test_redlight.py 的 3d 段、test_status.py 的 3d 段與受影響測試、status.py 的 `_apply_run`。C.1、C.2 只讀了標題。F 段(4d 報告)讀的是 S4D2 上的原檔。
5. status.py 除了 `_apply_run`(`:414-475`)以外沒有重新審查(4c、4d 都沒有改它)。
6. 4d 報告的真實 session 數字(第 17 行的欄位、使用者名稱 0 筆、H4 → H5)沒有重驗:重驗需要讀帳本,而那不在 TARGET 樹內。
7. Python 3.10 的 `tomli` 分支(鎖步測試 `:1507-1508`)沒有推演。
8. CLEAN / REAL 層不在本審查範圍。

---

## 6. 程序事件

1. **違反規則 6(Bash 不用 pipe)一次。** 我以一條含正規表示式 `|` 的 `git grep` 查 helper 定義,沒有加引號,於是 `|` 被 shell 當成 pipe。git grep 本身只讀,後面的幾段因為「command not found」沒有執行,沒有寫入任何檔案。原始錯誤輸出(不含使用者名稱):
   ```
   /usr/bin/bash: line 1: ^defs_d_: command not found
   /usr/bin/bash: line 1: ^_T_: command not found
   /usr/bin/bash: line 1: ^_D_: command not found
   /usr/bin/bash: line 1: ^classs_D: command not found
   /usr/bin/bash: line 1: ^classs_T: command not found
   /usr/bin/bash: line 1: _s_full_run_session: command not found
   ```
   之後改為 `git show <T>:<路徑>` 輸出全檔,再用 Grep 工具查詢;報告裡的引用都來自重做的結果。
2. **暫存檔**:審查者沒有用 Write 或指令寫入任何暫存檔。但有 6 次 `git show` / Bash 的輸出超過大小上限,工具環境(harness)自動把輸出存到本 session 的 tool-results 目錄(`C:\Users\<user>\.claude\projects\…\tool-results\`,在 repo 外)。我再用 Read / Grep 讀那些檔。這不是審查者主動寫入,但照實記錄。
3. `python -m pip show pytest pluggy anyio`:為了取得 pytest / pluggy 原始碼的位置與版本而執行,不是 pytest。pip 因為 cp950 編碼在 stderr 印出多段 `Logging error` 回溯,內含本機路徑(本報告已遮成 `<user>`,不照錄全文)。
4. 讀 pytest / pluggy / CPython 原始碼時,工具呼叫用的是本機絕對路徑(Read / Grep 的必要參數)。報告內的引用一律寫成 `_pytest/…`、`pluggy/…`、`subprocess.py`。
5. 沒有被任何閘門(R1–R9、pre-commit、洩漏偵測)擋下。沒有詢問使用者。所有 Git 查詢都以完整 SHA 為錨點,沒有使用 `HEAD`、短 SHA 或工作樹內容。唯一的例外是 `where git`:它查的是本機環境,不是 TARGET 內容。
