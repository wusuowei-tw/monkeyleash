# 票 145(M1-a)Station 3e-0 紅燈規劃 —— pass 有效性 / 受支援執行環境

- 依據:票 145〈三十三〉33.3 裁決 1–3,以及 Jeff 併入本輪 3e-0 指令的補充裁決 1–3。
- 程式碼錨點:`<TARGET>` = `889fbd8f666ea522ff6af172979a8d020e50b86b`(Station 4d 實作,Station 5d 判 FAIL)。
- 本規劃建立時的 HEAD:`741f74fcf56b582a95fe20585dfbb7fa94ba9c2a`(S5d-1;與 TARGET 之間只差 `docs/`)。
- 環境:Python 3.11.9、pytest 9.1.1(`python -m pip show`)、pluggy 1.6.0。
- **本輪沒有執行任何 pytest,也沒有寫任何 Python probe。** 下文的 pytest / pluggy / CPython 行為全部是讀原始碼推得的。引用格式為 `_pytest/<檔>:<行>`、`pluggy/<檔>:<行>`、`CPython <模組>:<行>`。
  CPython 用 C 寫的部分(`sys.flags` 的建立、`assert` 的編譯)本機沒有原始碼,只依 CPython 文件與可讀的 Python 層原始碼推得,這一點在 P5 照實列出。
- repo 設定一律綁 TARGET(`git show <TARGET>:pyproject.toml`):`addopts = "-ra --strict-markers"`、`filterwarnings = ["ignore::DeprecationWarning"]`,沒有 `xfail_strict` / `strict_xfail`,也沒有 `log_level`(`<TARGET>:pyproject.toml:70-80`)。

---

## 0. 本輪的 authority scope(Jeff 補充裁決 1,照錄語意)

在**受 agent-gates 管控的 pytest 主執行環境**中,pytest 記錄的 `passed` outcome,**沒有因為 interpreter / pytest execution mode 而失去通常的 pass 語意**。

**不在範圍內**:測試自己啟動的外部程式、子行程(例如測試裡另開 `python -O`)、其他 runtime、第三方工具的行為。那些屬於**測試實作品質**,不屬於 run-level coverage authority。P1 遇到這類情形一律標為「scope 外」,並簡述理由。

selection / collection 已由 3c、3d 處理。本輪只標註,不重查;某項同時影響 pass 有效性時才展開。

---

## P1 pass 有效性輸入盤點表

**分類**(五選一;另有「scope 外」標記):
- **(A)** 讓 assertion 或測試本體不執行
- **(B)** 改變 outcome 的解讀(把失敗轉成通過、把未執行記成通過等)
- **(C)** 只改 selection / execution scope(3c / 3d 已處理,只標註)
- **(D)** 只改 reporting
- **(E)** 不影響 authority

**「producer 讀得到?」**指 sessionfinish 時,在 `<TARGET>:tests/conftest.py:322-357`(`_completeness_of`)的位置能否**正向讀到**。
**「TARGET 後果」**指在 TARGET 上會不會得到 `"true"` 並退紅(`<TARGET>:.claude/hooks/redlight.py:678-733`;status 的退紅在 `<TARGET>:.claude/portable/status.py:456, 469-475`)。

**載具不另立列**:`PYTEST_ADDOPTS`、ini `addopts`、`@檔案` 只是把選項帶進 `config.option`(3d 規劃 P2(a))。分類依它帶進來的選項而定。

### 1. 直譯器(I)

| # | 輸入 | 分類 | 機制 / 出處 | producer 讀得到? | TARGET 後果 |
|---|---|---|---|---|---|
| I-1 | `-O` | **A** | `sys.flags.optimize = 1`;所有**沒被 pytest 改寫**的模組的 `assert` 在編譯時被移除(CPython 語意;pytest 自己的偵測 `_pytest/config/__init__.py:2070-2075`,警告文字 `:2041-2060`) | 可:`sys.flags.optimize` | **`"true"` 並退紅**(S5d-F1、S5d-X1;〈三十三〉33.2 已外部重現)。TARGET 不記這個事實(`<TARGET>:tests/conftest.py:335-355`) |
| I-2 | `-OO` | **A** | 同 I-1,`optimize = 2`(另外移除 docstring) | 可 | 同 I-1 |
| I-3 | `PYTHONOPTIMIZE=N` | **A** | 等同 `-O` × N;只在沒有 `-E` / `-I` 時生效(CPython 文件) | 可:同一個 `sys.flags.optimize` | 同 I-1(33.2 的觸發方式就是這個) |
| I-4 | `__debug__` | **A**(與 I-1–I-3 是同一個事實) | `__debug__ == (optimize == 0)`,是編譯期常數,不能賦值(CPython 文件)。pytest 也拿它決定改寫快取的副檔名(`_pytest/assertion/rewrite.py:69`) | 不需另讀;是 `sys.flags.optimize` 的投影 | 同 I-1 |
| I-5 | 既有的 `opt-1` / `opt-2` `.pyc`,在**非最佳化**執行時 | **E** | 快取檔名帶最佳化層級:`optimize == 0` 時沒有 `opt-` 標記,否則為 `.opt-N.pyc`(CPython `importlib._bootstrap_external:437-478`)⇒ 非最佳化執行不會載入最佳化 pyc | — | 不影響 |
| I-6 | pytest 改寫快取(`.pyc` / `.pyo`) | **E** | 副檔名依 `__debug__` 區分(`_pytest/assertion/rewrite.py:68-70`);讀取時驗 magic / mtime / size(`:374-391`) | — | 不影響 |
| I-7 | 以**非最佳化檔名**存放的最佳化 bytecode(要刻意製作,例如自行以 optimize=1 編譯並寫成一般 `.pyc` 檔名) | **A** | `optimize == 0` 時 import 機制照樣載入該檔(I-5 的檔名規則不檢查內容) | **讀不到** | 理論上 `"true"`;要刻意製作 ⇒ 列為殘餘(P3) |
| I-8 | 直譯器 `-W` / `PYTHONWARNINGS`(`sys.warnoptions`) | **E** | pytest 每個測試在 `warnings.catch_warnings` 內,依序疊上 ini `filterwarnings`、pytest `-W`、mark;後加的優先(`_pytest/warnings.py:36-54`;`_pytest/config/__init__.py:2224-2241`)⇒ 直譯器層的 filter 優先序最低,蓋不過已提交的 ini / mark。翻得了盤的,只剩「依賴環境預設 filter 的斷言」(見 S-3) | 可(`sys.warnoptions`),但不需要 | 不影響 |
| I-9 | `PYTHONPATH` | **E** | 改的是模組解析(受測物件是哪一份),不是 pass 語意。本 repo 的測試以檔案路徑載入受測物件(例:`<TARGET>:tests/test_redlight.py:22-27`) | — | 不影響 |
| I-10 | `PYTHONBREAKPOINT` | **E** | 只在測試呼叫 `breakpoint()` 時有作用(測試程式碼) | — | 不影響 |

### 2. `sys.flags` 其他欄位(F;Python 3.11 的欄位清單依 CPython 文件逐一列,`optimize` 見 I-1–I-3)

| # | 欄位(來源) | 分類 | 為何相關 / 不相關 |
|---|---|---|---|
| F-1 | `debug`(`-d`,debug build 才有) | E | 只增加剖析器除錯輸出 |
| F-2 | `inspect`(`-i`) | E | 執行完才進互動模式,pytest 的 session 已經結束 |
| F-3 | `interactive` | E | 同上 |
| F-4 | `dont_write_bytecode`(`-B`) | E | 不寫 pyc;改寫流程照常(`_pytest/assertion/rewrite.py:164-170`) |
| F-5 | `no_user_site`(`-s`) | E | 改變可 import 的套件集合 ⇒ plugin 集合可能不同;由 (vii)(vii′) 的白名單管 |
| F-6 | `no_site`(`-S`) | E | 同 F-5 |
| F-7 | `ignore_environment`(`-E`) | E | 會**關掉** `PYTHONOPTIMIZE` 等環境變數(方向更安全) |
| F-8 | `verbose`(`-v`) | D | import 追蹤輸出 |
| F-9 | `bytes_warning`(`-b` / `-bb`) | E | 只會讓更多東西失敗(更嚴) |
| F-10 | `quiet`(`-q`) | D | 啟動訊息 |
| F-11 | `hash_randomization`(`PYTHONHASHSEED`) | E | 依賴雜湊順序的斷言屬測試實作品質(S-3) |
| F-12 | `isolated`(`-I`) | E | 含 `-E`、`-s`、`-P`;同 F-5 / F-7 |
| F-13 | `dev_mode`(`-X dev`) | E | 更多警告、asyncio debug;只會更嚴 |
| F-14 | `utf8_mode`(`-X utf8`) | E | 固定指令本身就帶;只影響編碼 |
| F-15 | `warn_default_encoding`(`-X warn_default_encoding`) | E | 只多 EncodingWarning;更嚴或報告 |
| F-16 | `safe_path`(`-P`) | E | `sys.path[0]` 不放 cwd ⇒ 受測模組解析可能不同;同 I-9 |
| F-17 | `int_max_str_digits` | E | 超限時 ValueError;只會更嚴 |

**小結**:`sys.flags` 是封閉集合。逐欄看過之後,只有 `optimize` 屬 (A)。

### 3. pytest assertion 模式與改寫範圍(A)

| # | 輸入 | 分類 | 機制 / 出處 | producer 讀得到? | TARGET 後果 |
|---|---|---|---|---|---|
| A-1 | `--assert=rewrite`(預設) | E | `_pytest/assertion/__init__.py:28-41`;安裝 import hook(`_pytest/config/__init__.py:1332-1345`) | 可(`config.option.assertmode`) | 不影響 |
| A-2 | `--assert=plain`,`optimize == 0` | **D** | plain 只是不裝 rewrite hook(`_pytest/config/__init__.py:1337-1346`)。`optimize == 0` 時 CPython 照常執行 `assert`,失敗就拋 `AssertionError` ⇒ 測試 failed。差別只在失去 introspection 訊息(選項說明 `_pytest/assertion/__init__.py:36-40`);pytest 只在 `_assertion_supported()` 為假(也就是 assert 不執行)時才警告(`_pytest/config/__init__.py:2041-2075`) | 可 | 不影響 |
| A-3 | `--assert=plain`,`optimize > 0` | **A** | 測試模組也不改寫 ⇒ 全部 `assert` 被移除;pytest 只發出 PytestConfigWarning「ASSERTIONS ARE NOT EXECUTED and FAILING TESTS WILL PASS」(`_pytest/config/__init__.py:2043-2048`) | 可(歸結為 `optimize`) | **`"true"` 並退紅**(S5d-F1) |
| A-4 | **被改寫**的模組在 `optimize > 0` 時 | E | 改寫範圍:conftest 一律改寫(`_pytest/assertion/rewrite.py:229-233`)、命令列 init path(`:235-238`)、符合 `python_files` 者(`:240-246`)、被 mark 者(`:248-261`)。改寫後 assert 變成 `ast.If(not cond, [..., raise AssertionError])`(`:933-950`),以 `compile(..., dont_inherit=True)` 編譯(`:350`)⇒ **不是 `assert` 語句,不會被 `-O` 移除**(與 33.2「PYTHONOPTIMIZE=1 ⇒ 測試模組 1 failed」一致) | — | 不影響 |
| A-5 | **未被改寫**的輔助模組在 `optimize > 0` 時(S5d-X1) | **A** | 不符合 A-4 任一條的模組由一般 import 載入 ⇒ `assert` 被移除。本 repo 測試以 `spec_from_file_location` 載入的模組(例:`<TARGET>:tests/test_redlight.py:22-27`)也走不到 rewrite hook(`_pytest/assertion/rewrite.py:102-141` 只攔 meta path 的 import) | 可(歸結為 `optimize`) | **`"true"` 並退紅**(S5d-X1;33.2 已外部重現) |
| A-6 | docstring 含 `PYTEST_DONT_REWRITE` 的模組在 `optimize > 0` 時 | **A** | 不改寫(`_pytest/assertion/rewrite.py:691-694, 763-764`)⇒ 同 A-5。TARGET 的 `tests/` 沒有這個字樣(`git grep` 於 TARGET 無命中) | 可(歸結為 `optimize`) | 有這種模組時同 A-5 |
| A-7 | `register_assert_rewrite` / `pytest_plugins` / `-p` 匯入的模組(mark_rewrite) | E | `_pytest/assertion/__init__.py:84-106`;`_pytest/config/__init__.py:904, 1369` ⇒ 擴大改寫範圍 | — | 不影響 |
| A-8 | `enable_assertion_pass_hook`(ini) | E | 只多一個 pass hook(`_pytest/assertion/rewrite.py:672-676, 884-931`);經 ini 改值時由 (viii) / (xi) 管 | — | 不影響 |

### 4. outcome 解讀與 outcome 相關 plugin(O)

| # | 輸入 | 分類 | 機制 / 出處 | producer 讀得到? | TARGET 後果 |
|---|---|---|---|---|---|
| O-1 | `--runxfail` | **B** | ① `pytest.xfail` 被換成 no-op(`_pytest/skipping.py:50-62`)⇒ 測試本體裡的**命令式** `pytest.xfail(...)` 不再中止,程式往下走,走到結尾就是 **passed**;② makereport 不做 xfail 解讀(`:282-283`)。①會把「本來是 xfail(未通過)」變成 `passed` ⇒ 已知紅身分被退 | 可:`config.option.runxfail`(`:31-36`,預設 False) | **`"true"` 並退紅**(紙上推演:R1 test_a failed ⇒ 已知紅;R2 `--runxfail`,test_a 在 `pytest.xfail()` 之後的程式碼沒有斷言 ⇒ passed ⇒ `<TARGET>:.claude/portable/status.py:474` 退紅)。TARGET 的 `tests/` 沒有命令式 `pytest.xfail(`(`git grep` 於 TARGET 無命中),但合約是框架層 |
| O-2 | `strict_xfail` / `xfail_strict`(ini) | B(**已鎖**) | 決定 XPASS 算 passed 還是 failed(`_pytest/skipping.py:39-47, 305-311`)。經 `-o` ⇒ (viii);經設定檔 ⇒ (xi) | 經 (viii)(xi) 間接 | 已是 unknown |
| O-3 | pytest `-W` / `--pythonwarnings` | **B** | cmdline filter 疊在 ini **之後**,優先於已提交的 `filterwarnings`(`_pytest/config/__init__.py:2228-2241`;`_pytest/warnings.py:36-47`)⇒ 已提交設定若有 `error::X`(下游 repo 常見),`-W ignore::X` 會讓「因警告而失敗」的測試變成 passed | 可:`config.option.pythonwarnings`(`_pytest/main.py:122-127`,append,預設 None)。warnings plugin 讀的是 `known_args_namespace.pythonwarnings`(`_pytest/warnings.py:37`),兩者解析自同一串 args | **`"true"`**(在有 error filter 的 repo)。TARGET 已提交的 filter 只有 `ignore::DeprecationWarning`,本 repo 實際能翻的只有 S-3 類 |
| O-4 | `filterwarnings`(ini) | B(**已鎖**) | 已提交的值由 (xi) 鎖;`-o filterwarnings=…` 由 (viii) 擋 | 間接 | 已是 unknown |
| O-5 | `@pytest.mark.filterwarnings` | E | 已提交的測試程式碼;優先序最高(`_pytest/warnings.py:49-54`) | — | 不影響 |
| O-6 | `--disable-warnings` | **D** | 只影響摘要(`_pytest/terminal.py:204-210, 325-328`) | — | 不影響 |
| O-7 | `--max-warnings` / `max_warnings` | E | 超量時以錯誤結束(`_pytest/main.py:129-136, 144-147`);只會更嚴 | — | 不影響 |
| O-8 | `-p no:skipping` | B(**已鎖**) | skip / xfail mark 失效 | `(name, None)` | (xii) ⇒ unknown(`<TARGET>:.claude/hooks/redlight.py:701-702`) |
| O-9 | `-p no:warnings` | B(**已鎖**) | ini 的 error filter 不再套用 ⇒ 因警告而失敗的測試變 passed | 同上 | (xii) ⇒ unknown |
| O-10 | `-p no:assertion` | D(**已鎖**) | 不改寫;`optimize == 0` 時同 A-2 | 同上 | (xii) ⇒ unknown |
| O-11 | `-p no:unraisableexception` / `-p no:threadexception` | B(**已鎖**) | 這兩個 plugin 把 unraisable / thread exception 轉成警告(`_pytest/unraisableexception.py:49-68`),搭配 error filter 會讓測試失敗;停用後就不會失敗 | 同上 | (xii) ⇒ unknown |
| O-12 | `PYTEST_DISABLE_PLUGIN_AUTOLOAD` / `--disable-plugin-autoload` | E | anyio 不載入;async 測試在 pytest 9.1.1 會 `fail`(`_pytest/python.py:147-169`);`@pytest.mark.anyio` 在 `--strict-markers` 下是未註冊 marker ⇒ 收集錯誤(D)。只會更嚴。TARGET 的 `tests/` 沒有 async 測試(`git grep` 無命中)。不留 None 項目(`_pytest/config/__init__.py:1577-1586`) | plugin 清單少了 anyio | 不影響 |
| O-13 | `--pdb` | E | 只在失敗後進 post-mortem,report 已經是 failed;quit ⇒ `outcomes.exit`(`_pytest/debugging.py:399-404`)⇒ exit 2 ⇒ D | 可(`config.option.usepdb`) | 不影響 |
| O-14 | `--trace` | **B**(只在**人為互動**時) | 每個測試開始時進 pdb(`_pytest/debugging.py:58-63`);有人在 pdb 裡改變狀態後 `continue`,斷言就是對著被改過的狀態評估。非互動 stdin 時 quit ⇒ `outcomes.exit`(`:195-206`)⇒ D | 可(`config.option.trace`) | 有人為互動時可能 `"true"`;無互動時 D |
| O-15 | `--pdbcls` | E | 自訂 debugger class,只在進入 debugger 時才 import(行程內程式碼的旁門;同 P-1 的殘餘) | 可 | 不影響 |
| O-16 | `--capture` / `-s` | E | 只影響 stdout / stderr 擷取;`capsys` / `capfd` 照常 | — | 不影響 |
| O-17 | `--log-level` / `--log-cli-level` / `--log-file-level` / `--log-disable` | E | 改變 logging 的擷取層級 / 停用 logger(`_pytest/logging.py:245-332`)。翻得了盤的,只有「斷言某層級的 log **不存在**」這類依賴環境的斷言(S-3) | 可 | 不影響 |
| O-18 | `--basetemp` / `--cache-clear` | E | 暫存目錄 / cache 位置 | — | 不影響 |
| O-19 | `-p pytester` 的 `--lsof` / `--runpytest` | E | `--runpytest=subprocess` 把 pytester 型測試放到子行程跑;子行程部分屬 S-1 | — | 不影響 |

### 5. selection / execution scope(C;3c / 3d 已處理,只標註)

| # | 輸入 | 分類 | 已由哪一條處理 |
|---|---|---|---|
| C-1 | `pytest.exit(...)` | C | (vi)(3c) |
| C-2 | `-x` / `--maxfail` | C | (iii)(iv) |
| C-3 | `--lf` / `--ff` / `--nf` / `--lfnf` | C | (ii)(v);`--ff` / `--nf` 只重排 |
| C-4 | `--sw` / `--sw-skip` / `--sw-reset` | C | (ii) |
| C-5 | `--co` / `--setup-only` / `--setup-plan` / `--fixtures` / `--fixtures-per-test` / `--markers` / `--cache-show` / `-h` / `-V` | C | (iii)(vi);沒有 outcome |
| C-6 | `-k` / `-m` / `--deselect` | C | deselected ⇒ `"false"` |
| C-7 | `--ignore` / `--ignore-glob` / `--pyargs` / `--keep-duplicates` / `--collect-in-virtualenv` / `--continue-on-collection-errors` / `--import-mode` | C | 3d P1 #8, #16, #20, #25, #26 |
| C-8 | `-c` / `--rootdir` / `--confcutdir` / `--noconftest` / `-o` / `--strict*` | C | (viii)–(xi) |
| C-9 | `--doctest-modules` / `--doctest-glob` / `--doctest-ignore-import-errors` / `--doctest-continue-on-failure` | C | 3d P1 #15(只會擴增) |

### 6. 報告類(R)

| # | 輸入 | 分類 |
|---|---|---|
| R-1 | `-v` / `-q` / `--verbosity` / `-r` / `--tb` / `--xfail-tb` / `--show-capture` / `--full-trace` / `--color` / `--code-highlight` / `-l` / `--no-showlocals` / `--no-header` / `--no-summary` / `--no-fold-skipped` / `--force-short-summary` / `--durations` / `--durations-min` / `--setup-show` / `--junitxml` / `--junitprefix` / `--pastebin` / `--debug` / `--traceconfig` / `--log-format` 等格式與檔案類 logging 選項 / `--doctest-report` | D |

這張表連同 C-1–C-9、O-1–O-19、A-1–A-8,涵蓋了以 Grep `addoption(` 於 `_pytest/` 找到的全部 pytest 9.1.1 內建 CLI 選項,以及 `logging.py` 的 `add_option_ini`(`_pytest/logging.py:239-332`)。

### 7. 行程內程式碼(P)

| # | 輸入 | 分類 | 目前由哪一層鎖住 | 殘餘 |
|---|---|---|---|---|
| P-1 | plugin 或非 root conftest 以 hookwrapper 改寫 `pytest_runtest_makereport` 等的結果 | B(**已鎖**) | (vii)(vii′) plugin 白名單(`<TARGET>:.claude/hooks/redlight.py:699-700`);非 root conftest ⇒ other(`:554-555`);內建 plugin 的行為由 (xiii) 的 pytest 版本鎖住(`:703-704`) | S5c-F4(模組 `__name__` 冒充,`:514-515`)與 S5d-F2(sessionfinish 前自行 unregister):追蹤票 |
| P-2 | root conftest(`tests/conftest.py`)本身 | B(**已鎖**) | (xi) 工作樹 blob = HEAD blob(`:711-714`) | 無新增 |

### 8. scope 外(S)

| # | 情形 | 理由 |
|---|---|---|
| S-1 | 測試自行啟動子行程(`python -O`、`pytester --runpytest=subprocess`、外部工具) | 補充裁決 1:不屬 run-level coverage authority |
| S-2 | 測試程式碼在執行期改寫 pytest、`sys` 或斷言機制(例:monkeypatch pytest 內部) | 屬已提交的測試程式碼,即測試實作品質 |
| S-3 | 依賴環境預設值的斷言(例:沒設 `simplefilter("always")` 的 `catch_warnings` 再斷言「沒有警告」;斷言 `caplog` 為空;依賴雜湊順序) | 斷言**確實執行並評估**了,只是它觀察的環境被改了;是否該寫得不依賴環境,屬測試實作品質 |

### P1 統計

| 分類 | 列數 | 列 |
|---|---|---|
| (A) | 8 | I-1、I-2、I-3、I-4、I-7、A-3、A-5、A-6 |
| (B) | 10 | O-1、O-2、O-3、O-4、O-8、O-9、O-11、O-14、P-1、P-2 |
| (C) | 9 | C-1 – C-9 |
| (D) | 6 | F-8、F-10、A-2、O-6、O-10、R-1 |
| (E) | 33 | I-5、I-6、I-8、I-9、I-10;F-1–F-7、F-9、F-11–F-17(15);A-1、A-4、A-7、A-8;O-5、O-7、O-12、O-13、O-15–O-19 |
| scope 外 | 3 | S-1、S-2、S-3 |
| **合計** | **69** | |

**(A)(B) 中「producer 讀得到」而且「TARGET 上會得 `"true"`」的**:
- I-1、I-2、I-3、I-4、A-3、A-5、A-6:全部歸結為同一個事實 `sys.flags.optimize`
- O-1:`runxfail`
- O-3:`pythonwarnings`
- O-14:`trace`(只在人為互動時)

其餘 (A)(B):
- 已由現行條件鎖住:O-2、O-4、O-8、O-9、O-11、P-1、P-2
- 讀不到:I-7(要刻意製作)

---

## P2 特別查證

### (a) `sys.flags.optimize` 的語意與讀取點

- **來源**:`-O` ⇒ 1、`-OO` ⇒ 2、`PYTHONOPTIMIZE=N` ⇒ N;`-E` / `-I` 時忽略環境變數(CPython 文件)。
  - import 機制本身就拿 `sys.flags.optimize` 決定讀哪一個 pyc(CPython `importlib._bootstrap_external:470-473`),所以它是執行期最佳化層級的權威值。
  - pytest 的偵測 `_assertion_supported()`(`_pytest/config/__init__.py:2070-2075`)是同一件事的另一面。
- **事後能否改變**:
  - `sys.flags` 是唯讀的 structseq,欄位不能賦值。
  - `__debug__` 不能賦值(CPython 文件)。
  - 最佳化層級在直譯器啟動時就定了,行程內沒有公開的途徑可以改。
  - 唯一的例外是行程內程式碼直接替換 `sys.flags` 這個名稱,或用 `compile(..., optimize=N)` 自行編譯。這屬於 P-1 / S-2 的同類殘餘。
- **讀取點**:放在 `_completeness_of` 的 try 區塊內(`<TARGET>:tests/conftest.py:335-357`),與 `version = getattr(pytest, "__version__", None)`(`:339`)並列。
  - TARGET 的 conftest 在模組層只有 `import os`(`:3`);`sys` 只在 `_loaded_gate_modules` 內局部 import(`:93`)。
  - 建議 4e 在模組層 `import sys`,在 sessionfinish 當下讀 `sys.flags.optimize`,不在 import 時快取。理由見 P4 的 driver 原則:測試要能經由 conftest 所見的 `sys` 注入替身。
  - 讀不到或不是 int(不含 bool)⇒ 記 None ⇒ 不得為 `"true"`。

### (b) assertion rewrite 的覆蓋範圍,以及 `optimize == 0` 時 `--assert=plain` 是否仍讓 assert 不執行

- **改寫範圍**:見 A-4。conftest、命令列 init path、符合 `python_files` 者、被 mark 者會改寫;docstring 含 `PYTEST_DONT_REWRITE` 者不改寫(A-6);不經 meta path import 的模組不改寫(A-5)。
- **`optimize == 0` 時**:plain 模式只是不裝 hook。CPython 照常執行 `assert`,失敗拋 `AssertionError` ⇒ 測試 failed。pytest 的警告只在 `_assertion_supported()` 為假時才發(`_pytest/config/__init__.py:2041-2060`)。⇒ **`--assert=plain` 在 `optimize == 0` 時歸 (D)**。
- **依補充裁決 2 的結論**:合約**不需要** `assertmode == "rewrite"`,也**不需要**記錄 assertmode。真正必要的 invariant 是 `optimize == 0`:它同時涵蓋 A-3(plain + 最佳化)與 A-5 / A-6(未改寫模組 + 最佳化)。P4 另附一支 regression-lock(`assertmode="plain"`、`optimize == 0` ⇒ 仍為 `"true"`),防止 4e 多鎖。

### (c) S5c-X1 /〈二十九〉2 (xii) 的最終寫法

**不需要調整**。維持「`list_name_plugin()` 中有任何值為 None 的項目 ⇒ 不得為 `"true"`」(實作為 `<TARGET>:.claude/hooks/redlight.py:701-702`)。理由:

1. 本輪盤點中,會改變 outcome 解讀的停用(`-p no:skipping`、`-p no:warnings`、`-p no:unraisableexception`、`-p no:threadexception`)全部靠這一條擋(O-8、O-9、O-11)。
2. essential plugin 不能停用(`_pytest/config/__init__.py:306-312, 841-842`)。預設執行時只有 `consider_pluginarg` 會產生 None(`:850-857`),所以固定全套不受影響。
3. `-p no:X -p X` 會 unblock(`:858-864`;`pluggy/_manager.py:239-247`),None 被移除,表示 X 實際已恢復,不擋是正確的。
4. `PYTEST_DISABLE_PLUGIN_AUTOLOAD` 不留 None(O-12),但它只會更嚴,不需要改寫法。

### (d) S5d-F3:producer 寫入的欄位逐欄分類(補充裁決 3)

| 欄位 | 類 | TARGET 正規化現況 | 缺口 |
|---|---|---|---|
| `run_id`、`time`、`ticket_id`、`exit_code` | (3) | —(`<TARGET>:.claude/hooks/redlight.py:239-244`) | — |
| `collected`、`deselected`、`outcomes` 的鍵、`completeness.pre_narrowing` | (3) opaque identity(〈二十五〉裁決 1 (2)) | 只換反斜線(`:245-247`) | —(不改寫,依〈二十五〉) |
| `outcomes` 的值 | (3) | — | — |
| `invocation.args` | (1) | 〈十九〉規則:`_normalize_arg`(`:181-200`),root 以外 ⇒ None | **平台相依**:用 `os.path.isabs`(`:192`)。在 POSIX 上 `C:\…` 不是絕對路徑 ⇒ 被當成相對路徑接到 base 後面 ⇒ 以 `C:/…` 形式落帳 |
| `invocation.args_source`、`pyargs` | (3) | — | — |
| `completeness.options.*` | (3) | `_plain`(`<TARGET>:tests/conftest.py:308-312`) | — |
| `cacheprovider_blocked`、`shouldstop`、`shouldfail` | (3) | — | — |
| `plugins[].name` 中的**路徑型名稱**(conftest 註冊名) | (1) | 絕對路徑 ⇒ `_plugin_path_name`(`:549-550, 521-530`) | ① 平台相依(`os.path.isabs`);② `-p no:<路徑>` 產生的 `pytest_<路徑>`(`_pytest/config/__init__.py:856-857`)不是絕對路徑 ⇒ 原樣落帳 |
| `plugins[].name` 中的模組名 / entry-point 名 / 數字 id | (3) | 原樣 | — |
| `plugins[].kind`、`plugins[].dists` | (3) | — | — |
| `blocked[]` | 名稱欄位:與 `plugins[].name` 同規則 | **完全不正規化**(`:568-571`) | `-p no:<絕對路徑>` / `-p no:<越界相對路徑>` 原樣落帳 |
| `override_ini` 的 **key** | (3) | 原樣 | —(不得改寫) |
| `override_ini` 的 **value** | (2) 可能夾帶路徑 | 只有 `os.path.isabs(val)` 才正規化(`:593-594`) | ① 平台相依;② 越出 root 的相對路徑(`../../…`)原樣落帳 |
| `inifilename` | (1) | 絕對 ⇒ 正規化;相對 ⇒ 只換反斜線(`:574-582`) | ① 平台相依;② 越出 root 的相對路徑原樣落帳;③ 相對路徑沒有依 `invocation_params.dir` 解析 |
| `inipath` | (1) | `config.inipath` 一律是絕對路徑(`_pytest/config/findpaths.py:182, 307`)⇒ 走絕對分支 | 平台相依(同上;實務上 inipath 與 `_ROOT` 同平台,風險低) |
| `config_blobs` 的鍵 / 值 | (3)(常數鍵、hex) | — | — |
| `pytest_version` | (3) | — | — |
| (3e 新增)`optimize`、`runxfail`、`pythonwarnings` | (3) | — | `pythonwarnings` 的元素是 warning filter 字串(類別 / 模組 regex),不是檔案路徑 |

**通用規則(對「一類輸入」,不對特定字串)**:見 P3 的「S5d-F3 修正規則候選」。

---

## P3 合約候選(只列不選,待 Jeff 裁)

### 新增條件(「受支援執行環境」白名單的直譯器與 pass 有效性層)

| 編號 | 條件 | 擋住 P1 的 | 缺欄 |
|---|---|---|---|
| **(xiv)** | `sys.flags.optimize == 0`(int,不接受 bool) | I-1、I-2、I-3、I-4、A-3、A-5、A-6 | 缺欄 / 型別錯 ⇒ 不得為 `"true"` |
| **(xv)** | `config.option.runxfail is False` | O-1 | 缺欄 ⇒ 不得為 `"true"`(真實 pytest 只要 skipping plugin 在就一定有這個屬性;停用 skipping ⇒ (xii) 已擋) |
| **(xvi)** | `config.option.pythonwarnings` 為 None 或空 list | O-3 | 屬性必定存在(由 essential plugin `main` 註冊,`_pytest/main.py:122-127`;`_pytest/config/__init__.py:306-312`)⇒ None 即預設 |
| (xvii)(可選) | `config.option.trace is False` | O-14 | 同 (xv) |

### 四個組法

**甲:只加 (xiv)**
- 擋住全部 (A) 中讀得到的列。
- 擋不住 O-1、O-3(都會得 `"true"`)⇒ 殘餘必須明寫。

**乙:(xiv) + (xv) + (xvi)**
- 擋住全部 (A)(B) 中「讀得到、且會得 `"true"`」的列,O-14 除外。

**乙+:乙 + (xvii)**
- 連 O-14 也擋。

**丙:枚舉白名單**
- producer 落帳整份 `vars(config.option)`,consumer 要求每個鍵都等於「固定全套的基準值」,P1 判為 (D) 的報告類鍵除外。
- 優點:P1 沒列到的選項也 fail-closed。
- 缺點:
  - 基準值要隨 pytest 版本與 anyio 選項維護。
  - 好幾個選項值是路徑(`rootdir`、`basetemp`、`confcutdir`、`junitxml`、`log_file`…)⇒ S5d-F3 的正規化面跟著擴大。
  - IDE / CI 常帶的報告類旗標必須逐一列入例外。
  - 成本高。

### 對 P1 未列出、或 producer 讀不到的 (A)(B) 類輸入,預設權限是否 fail-closed

- **pytest 選項面**:
  - P1 已對 pytest 9.1.1 的**全部內建 CLI 選項**逐一分類(封閉集合,以 Grep `addoption(` 列舉)。
  - 新的內建選項只會隨 pytest 升版出現,而 (xiii) 已把版本鎖在 9.1.1 ⇒ 換版即 fail-closed。
  - plugin 新增的選項只可能來自白名單內的 plugin(anyio 4.15.0,(vii′))。**anyio 有沒有新增會改變 pass 語意的選項,本輪未查(P5)**。
  - 甲 / 乙在這一面是「已盤點 + 版本鎖」,不是執行期枚舉;丙才是執行期枚舉。
- **直譯器面**:
  - `sys.flags` 已逐欄分類,只有 `optimize` 屬 (A)。
  - 但 **Python 版本沒有鎖**。新版 Python 若新增會影響 assert 執行的旗標,本盤點不涵蓋 ⇒ **殘餘(不是 fail-closed)**。
  - 可選的補法是另加「Python 版本 ∈ 已盤點清單」(類比 (xiii)),代價是升級 Python 也要走票。本規劃不建議在 3e 加入,列在 P5。
- **讀不到的**:
  - I-7(刻意製作的最佳化 bytecode)。
  - O-14 在甲 / 乙之下(人為互動)。
  - P-1 的殘餘(S5c-F4、S5d-F2)。
  - 這些都要刻意或人為介入,**不是 fail-closed**,明寫為殘餘。

### 固定全套是否仍得 `"true"`

是。固定全套的事實是:
- `optimize == 0`:沒有 `-O`。前提是執行環境沒有設 `PYTHONOPTIMIZE`;有設就**永遠無法退紅**,這是刻意的。
- `runxfail` 為 False(`_pytest/skipping.py:35`)。
- `pythonwarnings` 為 None(`_pytest/main.py:122-127` 沒有 default)。
- `trace` 為 False。

### 成本

- **producer**:
  - 在模組層 `import sys`。
  - 讀 `sys.flags.optimize`,記為 `completeness["optimize"]`。
  - 把 `runxfail`、`pythonwarnings`(乙+ 另加 `trace`)加進 `COMPLETENESS_OPTIONS`(`<TARGET>:.claude/hooks/redlight.py:457-458`)。
  - `_plain` 會把 list 記成 `"<list>"`(`<TARGET>:tests/conftest.py:308-312`)。對判定足夠(非 None 即不成立);若要保留 filter 內容,4e 另行處理。filter 字串屬 (3)。
- **consumer**:`_completeness_problems` 加驗 `optimize`(`:639-675`);`_completeness_verdict` 加 2–4 條(`:696-733`)。
- **既有測試**:見 P4 末段「受影響的既有測試」。甲只影響 2 支;乙 / 乙+ 影響 14 支。

### S5d-F3 修正規則候選

**F3-甲(規則式;依欄位類別,不依特定字串)**
1. **路徑判定與平台無關**:一個值算「絕對路徑」,當且僅當 `posixpath.isabs(v) or ntpath.isabs(v)`,或以磁碟代號 `X:` 開頭。不再單用 `os.path.isabs`,否則同一個輸入在 Windows 與 Linux 上的落帳結果會不同。
2. **(1) 類欄位**(`inipath`、`inifilename`、`invocation.args`、`plugins[].name` 中的路徑型名稱):
   - 絕對 ⇒ root 相對 posix 路徑,或 `<outside>`。
   - 相對 ⇒ 先以 `invocation_params.dir` 為基準解析,再同上處理。
   - 越出 root ⇒ `<outside>`。
   - 永不落帳原樣的絕對路徑,或以 `..` 越界的相對路徑。
3. **名稱欄位**(`plugins[].name`、`blocked[]`)以**封閉集合**判定:
   - 是 conftest 註冊的路徑名 ⇒ 依 2。
   - 符合模組 / entry-point 名稱字元集 `[A-Za-z0-9_.-]+`(含數字 id)⇒ 原樣。
   - 其他(含 `/`、`\`、`:`、空白等,例如 `pytest_C:\…`)⇒ 固定記號 `<non-identifier>`。
   - 判定 kind 用的是原始名稱,正規化只作用於落帳的字串 ⇒ 判定結果不變。
4. **(2) 類欄位**(`override_ini`):
   - **key 一律原樣**。
   - **value** 只在「依規則 1 是絕對路徑」或「normpath 後第一段是 `..`(越出 root)」時套用規則 2。
   - 其他值一律原樣(例:`true`、`test_b`、`tests/test_*.py`)⇒ 不改寫證據本身。

**F3-乙(型別式)**
- override value 是否為路徑,改由 pytest 的 ini 型別表判定:`config._parser._inidict[key]` 的 type 為 `paths` / `pathlist`(`_pytest/config/argparsing.py:181-252`)。內建只有 `pythonpath`(`_pytest/config/__init__.py:1549-1551`)。
- 另外補上 9.1.1 已知的 string 型路徑 key(`cache_dir`、`log_file`…),作為封閉清單。
- 精確,但依賴私有 API 與清單維護。plugin 自訂的 key 若不在表內,仍需退回 F3-甲 的形狀判定。

**F3-丙(拒絕式)**
- 一旦出現無法正規化的路徑值,整份 `completeness` 記為 None。
- fail-closed,但證據消失,而且看不出是哪一欄造成的。不建議。

### 建議(待 Jeff 裁)

**合約採乙((xiv) + (xv) + (xvi)),S5d-F3 採 F3-甲。** 理由:

1. 〈三十三〉33.3 裁決 2 的最低要求是 (xiv)。P1 另外找到兩個讀得到、而且在 TARGET 上會得 `"true"` 的 (B) 輸入:O-1 `--runxfail`(命令式 xfail 被 no-op 化後走成 passed)與 O-3 pytest `-W`(優先於已提交的 error filter)。兩者的後果與 S5d-F1 同型(假通過 ⇒ 退紅)。固定全套都不帶它們,加上去的成本只有讀一個屬性。
2. 不採 (xvii):O-14 只在**有人在 debugger 裡改狀態**時才會翻盤,與 S5c-F4 / S5d-F2 同屬「行程內介入」;非互動時 `--trace` 會以 `outcomes.exit` 結束(D)。若 Jeff 偏好一併鎖住,成本與 (xv) 相同。
3. 不採丙:pytest 選項面已由「P1 全量盤點 + (xiii) 版本鎖」達到「換版即 fail-closed」;丙要付出路徑型選項的正規化面與報告旗標例外清單的維護成本,換來的只是執行期的重複檢查。
4. **不加** assertmode 條件(P2(b);補充裁決 2)。
5. F3-甲 以欄位類別與封閉字元集判定,不碰非路徑值,也不依賴私有 API。平台無關的絕對路徑判定同時補上 `invocation.args` 與 `inipath` 的同族缺口。

---

## P4 紅燈清單(草案;P3 裁定後定稿)

以下依**建議組法(乙 + F3-甲)**寫。若裁決為甲,刪去 #4、#5、#6、#18、#19;若為乙+,另加 `trace` 一組(結構同 #4 / #18)。

### driver 原則

- **沿用 3c-1b**:每次模擬執行載入全新的 conftest(`_isolated_conftest` / `_chain_conftest`)。全部寫在 tmp root;tmp root 是真的 git repo(沿用 3d 的 `_d_committed_root` / `_t_committed`)。
- **新 helper 一律接在檔尾,不改既有 helper**。既有 helper(`_d_option`、`_d_plugins`、`_d_drive`、`_DConfig`、`_t_option`、`_t_drive`、`_TConfig` 等)只呼叫。
- **optimize 的注入方式(本刀定稿的介面細節)**:
  - producer 以 conftest **模組層的 `sys`** 讀 `sys.flags.optimize`,讀取時點在 sessionfinish。
  - driver 以 `monkeypatch.setattr(c, "sys", _e_sys(optimize=N), raising=False)` 換掉**該 conftest 所見的** `sys`。
  - `_e_sys` 把其他屬性轉給真的 `sys`;`flags` 複製真實 `sys.flags` 的全部公開欄位,只改指定欄位,或刪掉 `optimize` 以表達缺欄。
  - **不改全域的 `sys.flags`**:import 機制以它決定 pyc 檔名(CPython `importlib._bootstrap_external:470-473`),全域替換會波及 driver 期間的任何 import。
  - TARGET 的 conftest 沒有模組層 `sys` ⇒ 注入無害,而 TARGET 照樣判 `"true"` ⇒ 紅的理由是對的。
- **runxfail / pythonwarnings**:經 `_d_option(runxfail=..., pythonwarnings=...)` 或 `_t_option(...)` 帶入(`_COption` / `_CompletenessOption` 以 `**overrides` 接受任意屬性:`<TARGET>:tests/test_redlight.py:781-786`;`<TARGET>:tests/test_status.py:1897-1902`)。
- **S5d-F3 的輸入以「一類」驅動**,參數化三種形狀(使用者名稱一律用合成的 `e3p-user`,不用本機真名):
  - `win-abs`:`C:\Users\e3p-user\…`
  - `posix-abs`:`/home/e3p-user/…`
  - `rel-escape`:`../../e3p-user/…`
  - 斷言:持久化的那一行(`.dev/test-sessions.jsonl` 的原文)不含 `e3p-user`。不比對 JSON 跳脫後的整串,以免被跳脫形式騙過。
- **單點測試**一律在同一支測試內放對照組:不破壞 ⇒ `"true"`;只破壞一條、其他全部成立 ⇒ `!= "true"`(沿用 3d D3i 的寫法)。

### test_redlight.py(檔尾;新類別 `TestPassValidityCoverage`、`TestProducerPathNormalization`)

| # | 預定 nodeid(`tests/test_redlight.py::`…) | 情境 | 預期 | 分類 | TARGET 上失敗的原因 |
|---|---|---|---|---|---|
| 1 | `TestPassValidityCoverage::test_e3o_an_optimized_interpreter_is_not_full_coverage[1]` | 對照組 `optimize=0` ⇒ `"true"`;破壞組 `optimize=1`,其他事實同固定全套 | 對照 `== "true"`;破壞 `!= "true"` | behavior-red | `<TARGET>:tests/conftest.py:335-355` 不記 optimize;`<TARGET>:.claude/hooks/redlight.py:696-733` 沒有對應條件 ⇒ `:733` 回 `"true"` |
| 2 | `TestPassValidityCoverage::test_e3o_an_optimized_interpreter_is_not_full_coverage[2]` | 同上,`optimize=2`(`-OO`) | 同上 | behavior-red | 同 #1 |
| 3 | `TestPassValidityCoverage::test_e3o_a_missing_optimize_fact_is_not_full_coverage` | `_e_sys` 的 `flags` 沒有 `optimize` 欄位 | `!= "true"` | behavior-red | 同 #1 |
| 4 | `TestPassValidityCoverage::test_e3x_runxfail_alone_is_not_full_coverage` | 對照 `runxfail=False`;破壞 `runxfail=True` | 對照 `== "true"`;破壞 `!= "true"` | behavior-red | `COMPLETENESS_OPTIONS`(`:457-458`)沒有 runxfail ⇒ `:733` |
| 5 | `TestPassValidityCoverage::test_e3w_a_pytest_warning_filter_alone_is_not_full_coverage` | 對照 `pythonwarnings=None`;破壞 `pythonwarnings=["ignore::UserWarning"]` | 同上 | behavior-red | 同 #4 |
| 6 | `TestPassValidityCoverage::test_e3o_the_producer_records_the_interpreter_optimize_flag` | producer 側:注入 `optimize=1` ⇒ 持久化的 `completeness["optimize"] == 1`;不注入 ⇒ 等於真實的 `sys.flags.optimize` | 斷言成立 | behavior-red | TARGET 的 completeness 沒有 `optimize` 鍵(`<TARGET>:tests/conftest.py:340-355`) |
| 7 | `TestPassValidityCoverage::test_e3x_the_producer_records_runxfail_and_pythonwarnings` | producer 側:`runxfail=True`、`pythonwarnings=["ignore::UserWarning"]` ⇒ 持久化的 `options` 含兩鍵且非預設值 | 斷言成立 | behavior-red | `options` 只含 `COMPLETENESS_OPTIONS` 的 8 鍵(`<TARGET>:tests/conftest.py:341-342`) |
| 8 | `TestPassValidityCoverage::test_e3d_the_fixed_command_with_a_plain_interpreter_is_full_coverage` | 固定全套事實 + `optimize=0`、`runxfail=False`、`pythonwarnings=None` | `== "true"` | regression-lock | — |
| 9 | `TestPassValidityCoverage::test_e3a_plain_assert_mode_on_a_plain_interpreter_is_still_full_coverage` | 同 #8,另加 `assertmode="plain"`(P2(b):(D),不得被鎖) | `== "true"` | regression-lock | — |
| 10 | `TestProducerPathNormalization::test_e3p_blocked_plugin_names_never_persist_a_path[win-abs]` | `list_name_plugin()` 含 `(X, None)` 與 `("pytest_"+X, None)`(照 `_pytest/config/__init__.py:855-857` 的成對表示),X = `C:\Users\e3p-user\x.py` | 持久化行不含 `e3p-user` | behavior-red | `blocked` 原樣落帳(`<TARGET>:.claude/hooks/redlight.py:568-571`);`pytest_`+X 在 `plugins[].name` 也原樣(`:549-550`) |
| 11 | 同上 `[posix-abs]` | X = `/home/e3p-user/x.py` | 同上 | behavior-red | 同 #10 |
| 12 | 同上 `[rel-escape]` | X = `../../e3p-user/x.py` | 同上 | behavior-red | 同 #10 |
| 13 | `TestProducerPathNormalization::test_e3p_a_config_file_option_never_persists_a_path[rel-escape]` | `inifilename = ../../e3p-user/alt.toml` | 持久化行不含 `e3p-user` | behavior-red | 相對路徑原樣落帳(`:582`) |
| 14 | 同上 `[win-abs]` | `C:\Users\e3p-user\alt.toml` | 同上 | regression-lock(**本機 Windows**) | —(Windows 上 `os.path.isabs` 為真 ⇒ `:580-581` 正規化)。**在 POSIX(CI 為 ubuntu,`<TARGET>:.github/workflows/tests.yml:20`)上會紅** |
| 15 | 同上 `[posix-abs]` | `/home/e3p-user/alt.toml` | 同上 | regression-lock(**本機 Windows**) | —(Windows 上 `/home/…` 視為有根路徑,`relpath` 跨磁碟 ⇒ `<outside>`,`:524-526`) |
| 16 | `TestProducerPathNormalization::test_e3p_an_override_value_never_persists_a_path[rel-escape]` | `override_ini = ["strict_markers=true", "cache_dir=../../e3p-user/c"]` | 持久化行不含 `e3p-user` | behavior-red | 只有絕對路徑才正規化(`:593-594`) |
| 17a | 同上 `[win-abs]` | `cache_dir=C:\Users\e3p-user\c` | 同上 | regression-lock(**本機 Windows**) | —(POSIX 上會紅,理由同 #14) |
| 17b | 同上 `[posix-abs]` | `cache_dir=/home/e3p-user/c` | 同上 | regression-lock(**本機 Windows**) | — |
| 18 | `TestProducerPathNormalization::test_e3p_non_path_override_values_are_persisted_verbatim` | `override_ini = ["strict_markers=true", "python_functions=test_b", "python_files=tests/test_*.py"]` | 持久化值**逐字相等** | regression-lock | —(補充裁決 3:非路徑值不得被改寫) |
| 19 | `TestProducerPathNormalization::test_e3p_non_path_plugin_names_are_persisted_verbatim` | `blocked` 含 `cacheprovider` / `pytest_cacheprovider`;`plugins` 含 `main`、數字 id、`anyio` | 持久化名稱逐字相等 | regression-lock | — |
| 20 | `TestProducerPathNormalization::test_e3p_a_root_relative_config_file_option_is_persisted_as_given` | `inifilename = alt.toml`(root 內相對) | 持久化值 `alt.toml` | regression-lock | — |

### test_status.py(檔尾;新類別 `TestPassValidityChain`、`TestPassValidityLocks`)

| # | 預定 nodeid(`tests/test_status.py::`…) | 情境 | 預期 | 分類 | TARGET 上失敗的原因 |
|---|---|---|---|---|---|
| 21 | `TestPassValidityChain::test_e3o_optimized_pass_does_not_retire_a_known_red` | R1 固定全套:test_a failed(exit 1)⇒ 已知紅;R2 `optimize=1`,test_a passed(exit 0)。每次全新 conftest。情境斷言:R1 為 B;R2 `validate_session == []` 且為 A | `tests/test_x.py` 在 red、不在 green | behavior-red | R2 在 `<TARGET>:.claude/hooks/redlight.py:733` 判 `"true"` ⇒ `<TARGET>:.claude/portable/status.py:474` 退紅;`:475` green |
| 22 | `TestPassValidityChain::test_e3o_optimized_run_does_not_make_a_clean_file_green` | 先前沒有紅;一次 `optimize=1` 的全 passed run | 不在 green | behavior-red | 同 #21(`:475`) |
| 23 | `TestPassValidityChain::test_e3x_runxfail_pass_does_not_retire_a_known_red` | 同 #21,R2 改為 `runxfail=True`(`optimize=0`) | 在 red、不在 green | behavior-red | 同 #21 |
| 24 | `TestPassValidityChain::test_e3w_warning_filter_pass_does_not_retire_a_known_red` | 同 #21,R2 改為 `pythonwarnings=["ignore::UserWarning"]` | 在 red、不在 green | behavior-red | 同 #21 |
| 25 | `TestPassValidityLocks::test_e3d_the_fixed_command_full_run_still_retires_the_red` | 已知紅 CHAIN_X;一次固定全套(`optimize=0` 明確注入、`runxfail=False`、`pythonwarnings=None`,其他事實同 4d) | 退紅、在 green | regression-lock | — |

**S5d-F1 / S5d-X1 的對應**:#21 是串接情境;#1–#3 是單點;#6 是 producer 側(確認 producer 真的讀 `sys.flags.optimize`,而不是讓 consumer 收到預先做好的 dict)。S5d-X1(輔助模組在 rewrite 模式下)與 S5d-F1(plain 模式)落在 producer 的**同一個事實**上(P2(b)),所以不另立測試。

### 預期集合(以本機 Windows 為準)

**預期紅集合(behavior-red,16 支)**:

- `tests/test_redlight.py::TestPassValidityCoverage::test_e3o_an_optimized_interpreter_is_not_full_coverage[1]`
- `tests/test_redlight.py::TestPassValidityCoverage::test_e3o_an_optimized_interpreter_is_not_full_coverage[2]`
- `tests/test_redlight.py::TestPassValidityCoverage::test_e3o_a_missing_optimize_fact_is_not_full_coverage`
- `tests/test_redlight.py::TestPassValidityCoverage::test_e3x_runxfail_alone_is_not_full_coverage`
- `tests/test_redlight.py::TestPassValidityCoverage::test_e3w_a_pytest_warning_filter_alone_is_not_full_coverage`
- `tests/test_redlight.py::TestPassValidityCoverage::test_e3o_the_producer_records_the_interpreter_optimize_flag`
- `tests/test_redlight.py::TestPassValidityCoverage::test_e3x_the_producer_records_runxfail_and_pythonwarnings`
- `tests/test_redlight.py::TestProducerPathNormalization::test_e3p_blocked_plugin_names_never_persist_a_path[win-abs]`
- `tests/test_redlight.py::TestProducerPathNormalization::test_e3p_blocked_plugin_names_never_persist_a_path[posix-abs]`
- `tests/test_redlight.py::TestProducerPathNormalization::test_e3p_blocked_plugin_names_never_persist_a_path[rel-escape]`
- `tests/test_redlight.py::TestProducerPathNormalization::test_e3p_a_config_file_option_never_persists_a_path[rel-escape]`
- `tests/test_redlight.py::TestProducerPathNormalization::test_e3p_an_override_value_never_persists_a_path[rel-escape]`
- `tests/test_status.py::TestPassValidityChain::test_e3o_optimized_pass_does_not_retire_a_known_red`
- `tests/test_status.py::TestPassValidityChain::test_e3o_optimized_run_does_not_make_a_clean_file_green`
- `tests/test_status.py::TestPassValidityChain::test_e3x_runxfail_pass_does_not_retire_a_known_red`
- `tests/test_status.py::TestPassValidityChain::test_e3w_warning_filter_pass_does_not_retire_a_known_red`

**預期綠集合(regression-lock,10 支)**:

- `tests/test_redlight.py::TestPassValidityCoverage::test_e3d_the_fixed_command_with_a_plain_interpreter_is_full_coverage`
- `tests/test_redlight.py::TestPassValidityCoverage::test_e3a_plain_assert_mode_on_a_plain_interpreter_is_still_full_coverage`
- `tests/test_redlight.py::TestProducerPathNormalization::test_e3p_a_config_file_option_never_persists_a_path[win-abs]`
- `tests/test_redlight.py::TestProducerPathNormalization::test_e3p_a_config_file_option_never_persists_a_path[posix-abs]`
- `tests/test_redlight.py::TestProducerPathNormalization::test_e3p_an_override_value_never_persists_a_path[win-abs]`
- `tests/test_redlight.py::TestProducerPathNormalization::test_e3p_an_override_value_never_persists_a_path[posix-abs]`
- `tests/test_redlight.py::TestProducerPathNormalization::test_e3p_non_path_override_values_are_persisted_verbatim`
- `tests/test_redlight.py::TestProducerPathNormalization::test_e3p_non_path_plugin_names_are_persisted_verbatim`
- `tests/test_redlight.py::TestProducerPathNormalization::test_e3p_a_root_relative_config_file_option_is_persisted_as_given`
- `tests/test_status.py::TestPassValidityLocks::test_e3d_the_fixed_command_full_run_still_retires_the_red`

**平台附註**:上面 4 支 `[win-abs]` / `[posix-abs]` 的綠,是 TARGET 用 `os.path.isabs` 在 Windows 上剛好正規化的結果。在 POSIX(CI)上,`[win-abs]` 那兩支會紅。這正是 S5d-F3 的跨平台缺口(P2(d))。3e 的驗收以本機為準;4e 依 F3-甲 修好之後,兩個平台都必須綠。

### 4e 後會受新合約影響的既有測試與所需授權

下列既有測試斷言 `"true"`、green 或 orphan。在新合約下,它們的 fake / fixture 缺新事實 ⇒ 4e 後會失敗(以 TARGET 上的正向斷言為準)。

**經 producer、以 `_COption` / `_CompletenessOption` 為 option 的(乙 / 乙+ 時受影響:`runxfail` 缺 ⇒ `getattr` 得 None ⇒ (xv) 不成立)**:

| nodeid | 依賴(TARGET 行號) |
|---|---|
| `tests/test_redlight.py::TestFileCoverage::test_b1c_a_file_argument_without_deselection_is_full_coverage` | `== "true"`(`:540`) |
| `tests/test_redlight.py::TestFileCoverage::test_b1d_a_parent_directory_argument_is_full_coverage` | `== "true"`(`:558`) |
| `tests/test_redlight.py::TestFixedCommandCoverage::test_b10_the_fixed_command_without_positional_args_is_full_coverage` | `== "true"`(`:660`) |
| `tests/test_redlight.py::TestCompletenessCoverage::test_c3d_the_fixed_command_with_everything_off_is_full_coverage` | `== "true"`(`:1070`) |
| `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3i_lf_alone_is_not_full_coverage` | 對照 `== "true"`(`:1432`) |
| `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3i_maxfail_alone_is_not_full_coverage` | 對照 `== "true"`(`:1444`) |
| `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3i_shouldfail_alone_is_not_full_coverage` | 對照 `== "true"`(`:1456`) |
| `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3d_the_fixed_command_with_the_committed_config_is_full_coverage` | `== "true"`(`:1485`) |
| `tests/test_status.py::TestChainRegressionLocks::test_l3_a_full_directory_run_retires_the_red` | green(`:1740`) |
| `tests/test_status.py::TestCompletenessLocks::test_c3d_the_fixed_command_full_run_still_retires_the_red` | green(`:2220`) |
| `tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_builtin_root_conftest_and_known_dist_as_not_other` | `== "true"`(`:2320`) |
| `tests/test_status.py::TestCollectionDefinitionLocks::test_d3d_the_fixed_command_full_run_still_retires_the_red` | green(`:2564`) |

**直接以 `record_session` 寫入 completeness dict 的(甲 / 乙 / 乙+ 都受影響:缺 `optimize`;乙另缺 `options.runxfail` / `options.pythonwarnings`)**:

| nodeid | 依賴(TARGET 行號) |
|---|---|
| `tests/test_status.py::TestTestsUnderTicketUsesTheLatestRecordPerFile::test_a_file_that_went_red_then_green_counts_as_green` | green(`:600`;dict 在 `:583-594`) |
| `tests/test_status.py::TestOrphans::test_a_renamed_red_test_is_orphaned_not_green` | orphan(`:1371`;dict 在 `:1352-1367`) |

**合計**:乙 / 乙+ 共 **14 支**;甲只有後 **2 支**。經 producer 的 12 支在甲之下不受影響,因為 producer 讀的是真實的 `sys.flags.optimize`,而固定全套為 0。

**需要的授權(比照〈十七〉裁決 5、〈二十三〉5、〈二十九〉4)**:assertion、docstring、test identity 一律不改。可選兩種補法:
- **授權 A(建議)**:只在兩個共用預設 dict 各加一個鍵 `"runxfail": False`(`<TARGET>:tests/test_redlight.py:766-772` 的 `_C_OPTION_DEFAULTS`、`<TARGET>:tests/test_status.py:1885-1891` 的 `_S_OPTION_DEFAULTS`);並在 2 支直接寫 dict 的測試補上 `optimize: 0` 與(乙時)兩個 option 鍵。
  - 代價:改到既有 helper,而 3c / 3d 的規則是「既有 helper 只呼叫、不修改」,需要明文例外。
  - 效果:這是真實 pytest 的預設值(`_pytest/skipping.py:35`),使用這兩個 dict 的其他測試只會多一個與實況一致的屬性。
- **授權 B**:逐支在 12 支測試的呼叫處帶 `runxfail=False`。不改 helper,但要動 12 處呼叫。

**不受影響、但通過理由可能改變的**:3c / 3d 中斷言 `!= "true"` 的測試在 4e 後仍會通過,但可能多了「缺新事實」這個理由。4e 報告應逐支說明主因沒有改變(延續 S5c-F2 的關切)。

---

## P5 尚未證明 / 本輪未做

1. **全部結論都是讀原始碼推得的,沒有實測**。包括:
   - O-1(`--runxfail` 使命令式 xfail 走成 passed)
   - O-3(pytest `-W` 蓋過 ini error filter)
   - A-4(被改寫的 assert 在 `-O` 下仍執行)
   - P4 各支在 TARGET 上的紅綠預測
   〈三十三〉33.2 的外部重現只證明了 A-3、A-5(與 A-4 的「1 failed」)。
2. **CPython 的 C 層沒有逐行引用**:`sys.flags` 的建立、`-E` 對 `PYTHONOPTIMIZE` 的影響、`assert` 在最佳化下被移除、`__debug__` 不可賦值、Python 3.11 的 `sys.flags` 欄位清單。這些都依 CPython 文件,本機沒有 C 原始碼可引。
3. **pytest 選項的列舉方式**:以 Grep `addoption(` 加 `add_option_ini` 找出,沒有用 pytest 本身列出(那需要執行 pytest)。可能漏掉以非常規寫法註冊的選項。
4. **anyio 4.15.0 的 pytest plugin 是否新增會改變 pass 語意的選項或 hook**:本輪沒有讀 anyio 原始碼。
5. **Python 版本沒有鎖**:`sys.flags` 的盤點只對 3.11 成立。是否另加「Python 版本 ∈ 已盤點清單」,未建議、未評估成本。
6. I-7(刻意製作的最佳化 bytecode)、O-14(人為互動)、P-1 的殘餘(S5c-F4、S5d-F2):producer 讀不到或屬行程內介入,本輪不處理。
7. F3-甲 的字元集 `[A-Za-z0-9_.-]+` 是否涵蓋所有合法的 plugin 註冊名(例:entry-point 名稱允許的字元),沒有查 packaging 規格。
8. `invocation.args` 在 POSIX 上遇到 `C:\…` 參數的落帳形式,是推演,沒有實測;pytest 遇到不存在的路徑會以 usage error 結束(D),但那一筆 session 仍會落帳。
9. CLEAN / REAL 層不在本輪範圍。
