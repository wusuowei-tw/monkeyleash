# 票 145(M1-a)Station 3d-0 紅燈規劃 —— 收集定義完整性

- 依據:票 145〈二十七〉27.3 裁決 1–4。
- 程式碼錨點:`<TARGET>` = `02a5e28adf5aee11a43d5a1063504f01beb1d67f`(Station 4c 實作,Station 5c 判 FAIL)。
- 本規劃建立時的 HEAD:`da8e4e79ef1fa678949a171198232c96ba2305a8`(S5c-1;與 TARGET 之間只差 `docs/`)。
- pytest 9.1.1、pluggy 1.6.0(`python -m pip show`)。
- **本輪沒有執行任何 pytest,也沒有寫任何 Python probe。** 下文所有 pytest / pluggy 行為都是讀原始碼推得的。引用格式為 `_pytest/<檔>:<行>` / `pluggy/<檔>:<行>`。
- **repo baseline 一律綁 TARGET**:`git ls-tree -r --name-only <TARGET>` 裡和 pytest 設定有關的檔只有 `pyproject.toml` 與 `tests/conftest.py`。TARGET 沒有 `pytest.ini`、`tox.ini`、`setup.cfg`,也沒有 `pytest.toml`。
  - `<TARGET>:pyproject.toml` 的 `[tool.pytest.ini_options]`:`testpaths = ["tests"]`、`addopts = "-ra --strict-markers"`、`markers = [unit, integration, smoke]`、`filterwarnings = ["ignore::DeprecationWarning"]`。**沒有** `python_files` / `python_classes` / `python_functions` / `norecursedirs` / `collect_imported_tests`,所以這幾項取 pytest 預設值(見 P1)。
  - `<TARGET>:tests/conftest.py` 沒有 `collect_ignore` / `collect_ignore_glob`。

---

## P1 收集定義輸入盤點表

先講清楚基準點。TARGET 的縮小前快照取在 conftest 的 `pytest_make_collect_report` trylast wrapper 的 yield **之後**(`<TARGET>:tests/conftest.py:294-305`),也就是 `collector.collect()` 已經跑完、只剩外層 wrapper(例如 `LFPluginCollWrapper`)還沒動手的那一刻。所以:
- **「早於快照」**:縮小發生在 `collect()` 之內或更早。快照和 collected 會一樣少,(v) 抓不到。
- **「整檔 / 整路徑縮小」**:該檔在本次 run 完全沒有身分,`<TARGET>:.claude/hooks/redlight.py:416-417` 判 `unknown`,不會得 `"true"`。

欄位說明:
- (1) 對「哪些東西算測試」的效果
- (2) 縮小發生的階段 / 函式,以及是否早於快照
- (3) producer 在 sessionfinish 時能正向讀到什麼
- (4) 在 TARGET 上的後果(會不會得 `"true"`)

| # | 輸入 | (1) 效果 | (2) 階段 / 出處 / 是否早於快照 | (3) producer 讀得到什麼 | (4) TARGET 後果 |
|---|---|---|---|---|---|
| 1 | `-o` / `--override-ini KEY=VAL` | 依 KEY 而定:`python_functions` / `python_classes` / `collect_imported_tests` ⇒ **檔內縮小**;`python_files` / `norecursedirs` ⇒ 整檔 / 整目錄;`testpaths` ⇒ 只影響位置參數;其他 key 視其語意 | 設定期。CLI 與環境帶入的部分在 `determine_setup` 寫進 inicfg(`_pytest/config/findpaths.py:338-339`;呼叫點 `_pytest/config/__init__.py:1532-1539`);ini addopts 帶入的部分在 `_pytest/config/__init__.py:1567-1572` 再套一次。生效點在 `collect()` 內(`_pytest/python.py:354-355, 366-367, 385-398, 420-441`)⇒ **早於快照** | **值**:`config.option.override_ini`(`dest="override_ini"`、`action="append"`,`_pytest/helpconfig.py:113-116`),是三個來源合併後的完整清單(見 P2(a))。**來源**:從 option 本身分不出 CLI / 環境 / ini。私有 API `config._inicfg[key].origin` 只分得出 `"file"` / `"override"`(`_pytest/config/findpaths.py:22-40, 271`) | **`"true"`**(S5c-F1;27.2 已實測重現) |
| 2 | `PYTEST_ADDOPTS` | 本身只是**載具**;效果等於它帶進來的選項 | 設定期,放在 CLI args 之前(`_pytest/config/__init__.py:1522-1528`) | 帶進來的選項全部落在 `config.option.*`。**不在** `config.invocation_params.args` 裡(`_pytest/config/__init__.py:1063-1064` docstring;`:359-363` 在合併前就把 args 凍結成 tuple)。原始字串可在 sessionfinish 讀 `os.environ["PYTEST_ADDOPTS"]`,但那是「現在的環境」,不保證是當初啟動時的值 | 帶 `-o python_functions=…` ⇒ 同 #1,**`"true"`** |
| 3 | ini 檔裡的 `addopts` | 載具;TARGET 的已提交值 `-ra --strict-markers` **本身會產生一筆 override**(見 P2(a)) | 設定期,放在最前面(`_pytest/config/__init__.py:1559-1562`) | `config.getini("addopts")`(有效值;但它自己也能被 `-o addopts=…` 改掉);帶進來的選項落在 `config.option.*` | 已提交值:不縮小。工作樹改過的 addopts 帶 `-o python_functions=…` ⇒ 同 #1 |
| 4 | `-c` / `--config-file FILE` | 整份設定來源被換掉 ⇒ 任何 key 都可能變(可縮小、可擴增);rootdir 也跟著變成 FILE 的父目錄(除非另給 `--rootdir`) | 設定期(`_pytest/config/findpaths.py:306-311`;選項定義 `_pytest/main.py:262-270`)⇒ 早於一切 | `config.option.inifilename`(值);`config.inipath`(實際採用的檔) | FILE 與 repo 同一層、內容設 `python_functions = test_b` ⇒ 同 #1,**`"true"`** |
| 5 | `--rootdir` | 不改變測試集合;改變 **nodeid 的基準**(`config.rootpath`) | 設定期(`_pytest/config/findpaths.py:331-336`) | `config.option.rootdir`、`config.rootpath` | nodeid 換基準 ⇒ 身分鍵與帳本既有的鍵不相交 ⇒ 既有的紅不會被這次 run 碰到。**本輪未逐案推演**它與 `testpaths` / 位置參數正規化(`<TARGET>:.claude/hooks/redlight.py:203-217` 以 conftest 的 `_ROOT` 為基準)的交互 |
| 6 | `--confcutdir` | 不直接改集合;**決定哪些 conftest 會被載入** | 設定期(`_pytest/config/__init__.py:669-681`;預設值 `:1598-1603`) | `config.option.confcutdir` | 若 confcutdir 落在 `tests/` 之下 ⇒ `tests/conftest.py` 不載入 ⇒ **producer 不存在**,8 欄紀錄與 session 都不寫 ⇒ 沒有任何退紅 |
| 7 | `--noconftest` | 不載入任何 conftest | `_pytest/config/__init__.py:692-693` | (producer 不存在) | 同 #6:不寫紀錄 ⇒ 沒有效果 |
| 8 | `--import-mode` | 不影響集合;只影響 import 機制。import 失敗會變成收集錯誤 | `_pytest/main.py:217-224` | `config.option.importmode` | 收集錯誤 ⇒ D;不會得 `"true"` |
| 9 | `python_files`(ini) | **整檔**縮小或擴增;初始路徑例外(`isinitpath`) | `pytest_collect_file`(`_pytest/python.py:195-207`)⇒ 早於快照,但以整檔為單位 | `config.getini("python_files")`(有效值,預設 `["test_*.py", "*_test.py"]`,`_pytest/python.py:87-93`) | 該檔沒有身分 ⇒ `unknown`(安全) |
| 10 | `python_classes`(ini) | **檔內縮小**(整個 class 不收集) | `_pytest/python.py:366-367, 378-383` ⇒ 早於快照 | `config.getini("python_classes")`(預設 `["Test"]`,`:94-99`) | **`"true"`**(與 S5c-F1 同型) |
| 11 | `python_functions`(ini) | **檔內縮小** | `_pytest/python.py:354-355, 369-376` ⇒ 早於快照 | `config.getini("python_functions")`(預設 `["test"]`,`:100-105`) | **`"true"`**(S5c-F1) |
| 12 | `norecursedirs`(ini) | **整目錄**縮小 | `pytest_ignore_collect`(`_pytest/main.py:467-470`;預設清單 `:225-240`) | `config.getini("norecursedirs")` | 該目錄下的檔沒有身分 ⇒ `unknown`(安全) |
| 13 | `testpaths`(ini) | 只在**沒有位置參數**時決定起點 | `_decide_args`(`_pytest/config/__init__.py:1415-1422`) | `config.getini("testpaths")`;結果已落在 `invocation.args`(`<TARGET>:tests/conftest.py:256-274`) | 起點以外的檔沒有身分 ⇒ `unknown`;起點以內的檔照一般規則判。**不構成檔內縮小** |
| 14 | conftest 的 `collect_ignore` / `collect_ignore_glob` | **整路徑**縮小 | `pytest_ignore_collect`(`_pytest/main.py:441-461`) | `config._getconftest_pathlist`(私有) | TARGET 的 root conftest 沒有這兩個變數。其他 conftest 會被分類為 other(〈二十三〉3)。被排除的檔沒有身分 ⇒ `unknown`。root conftest 在工作樹被改,屬於 producer 本身被改(信任邊界問題,見 P5) |
| 15 | `--doctest-modules` / `--doctest-glob` | **只會擴增**(多出 DoctestModule / DoctestTextfile) | `_pytest/doctest.py:126-135` | `config.option.doctestmodules`、`config.option.doctestglob` | 擴增的身分同時出現在快照和 collected ⇒ 兩邊一致。不縮小 |
| 16 | `--pyargs` | 位置參數改以 Python 套件解讀 | `_pytest/main.py:157-161` | `config.option.pyargs`(已落帳) | `<TARGET>:.claude/hooks/redlight.py:421-422` ⇒ `unknown` |
| 17 | `-p no:python` | 不收集任何 Python 模組 ⇒ 整體縮小 | `consider_pluginarg`(`_pytest/config/__init__.py:837-857`) | 停用的名稱在 `list_name_plugin()` 裡是 `(name, None)`(P2(d)) | 沒有身分 ⇒ `unknown`;而且 `("python", None)` 被判 other ⇒ `unknown` |
| 18 | `-p no:unittest` | **檔內縮小**:TestCase 改由 python plugin 收集;因為有 `__init__`,只發警告、回空 | `_pytest/python.py:757-768`(Class.collect) | 同 #17 | `("unittest", None)` 被判 other ⇒ `unknown`。TARGET 的 `tests/` 沒有 TestCase(5c 報告 G5) |
| 19 | `-p no:cacheprovider` | `--lf` / `--sw` 不可用;stepwise 一併封鎖 | `_pytest/config/__init__.py:850-857` | 同 #17;另有 `is_blocked("cacheprovider")` | `("cacheprovider", None)` 等 4 筆被判 other ⇒ `unknown`(〈二十三〉裁決 4 的特判因此走不到,見 P2(d)) |
| 20 | `--ignore` / `--ignore-glob` | **整路徑**縮小 | `_pytest/main.py:445-461` | `config.option.ignore` / `ignore_glob` | 沒有身分 ⇒ `unknown`(3c 規劃 P1 #4、#5 已確認;本輪重讀,結論相同) |
| 21 | `collect_imported_tests`(ini) | 設為 false ⇒ 從別的模組 import 進來的函式 / class 不收集 ⇒ **檔內縮小** | `_pytest/python.py:427-431`;ini 定義 `_pytest/main.py:248-253` | `config.getini("collect_imported_tests")` | 經 `-o` 或改設定帶入 ⇒ 同 #1,**`"true"`** |
| 22 | **未追蹤 / 未提交的設定檔**(`pytest.toml`、`.pytest.toml`、`pytest.ini`、`.pytest.ini` 的搜尋順位都在 `pyproject.toml` 之前;`tox.ini`、`setup.cfg` 在之後) | 整份設定來源被換掉 ⇒ 同 #4,但**不需要任何 CLI 參數** | `locate_config`(`_pytest/config/findpaths.py:166-174, 181-199`)⇒ 早於一切 | `config.inipath`(實際採用的檔) | 在 repo 根放一份 `pytest.ini`,`[pytest]` 寫 `python_functions = test_b` ⇒ **`"true"`**。**沒有 `-o`、沒有 `-c`** |
| 23 | **工作樹的 `pyproject.toml` 被改過、還沒提交** | 任何 key 都可能變 | 同 #22(pytest 讀的是工作樹檔案,`_pytest/config/findpaths.py:102`) | `config.inipath` 不變。要看出內容不同,只能比對檔案與已提交 blob(P2(b)) | 改 `python_functions` ⇒ **`"true"`** |
| 24 | `@檔案` 參數(`fromfile_prefix_chars="@"`) | 載具;效果等於檔案裡的選項 | `_pytest/config/argparsing.py:395-396` | 選項落在 `config.option.*`;`invocation_params.args` 裡只有 `@檔案` 這一個字串 | 同它帶進來的選項 |
| 25 | `--keep-duplicates`、`--collect-in-virtualenv` | 只會擴增 | `_pytest/main.py:195-209` | `config.option.keepduplicates` / `collect_in_virtualenv` | 不縮小 |
| 26 | `--continue-on-collection-errors` | 收集錯誤之後仍繼續執行 | `_pytest/main.py:210-216` | `config.option.continue_on_collection_errors` | 收集錯誤照樣記成 `collect_errors` ⇒ D;不得 green |
| 27 | `PYTEST_DISABLE_PLUGIN_AUTOLOAD` / `--disable-plugin-autoload` | entry-point plugin 不載入;**不會**在 `list_name_plugin()` 留下 `None` 項目 | `_pytest/config/__init__.py:1577-1586` | 讀不到「被跳過」這件事,只看得到 plugin 不在 | 本 repo 的 entry-point plugin 只有 anyio,它不縮小集合(3c 規劃 P1 #20)。少了它,async 測試會失敗 ⇒ 紅(fail-closed)。**不構成檔內縮小**,但這是 producer 看不見的輸入 |

**表中會讓 TARGET 得 `"true"` 的列**:#1、#2(帶 `-o`)、#3(工作樹 addopts 帶 `-o`)、#4、#10、#11、#21、#22、#23、#24(帶 `-o`)。它們的共同點是:**縮小發生在 `collect()` 之內,而 TARGET 沒有任何事實能證明「本次的收集定義 = repo 已提交的定義」。**

---

## P2 特別查證

### (a) `-o` 的三個來源是否都落在 `config.option.override_ini`?合併順序?`invocation_params.args` 含不含 PYTEST_ADDOPTS?

- **都會落在同一個事實上。** `parse()` 先把 PYTEST_ADDOPTS 放到 CLI args 前面(`_pytest/config/__init__.py:1522-1528`),再把 ini 的 `addopts` 放到最前面(`:1559-1562`)。最後 `self._parser.parse(args, namespace=self.option)`(`:1620`)用的是合併後的整串;`-o` 是 `action="append"`(`_pytest/helpconfig.py:113-116`)⇒ 三個來源的 `-o` 全部依序附加到 `config.option.override_ini`。
- **`OverrideIniAction` 也會附加**:`--strict-markers` 這類旗標會把 `"strict_markers=true"` 附加進 `override_ini`(`_pytest/config/argparsing.py:491-503`;旗標定義 `_pytest/main.py:76-96`)。⇒ **固定全套的 `override_ini` 不是空的**:TARGET 已提交的 `addopts = "-ra --strict-markers"` 會讓它至少含 `["strict_markers=true"]`。這是推得的,未實測。
- **合併順序**(串接順序 = ini addopts → PYTEST_ADDOPTS → CLI;同一個 key 後者勝,`_pytest/config/findpaths.py:261-271`):
  1. `determine_setup` 先套 PYTEST_ADDOPTS + CLI 的 `-o`(`_pytest/config/__init__.py:1532-1539` → `_pytest/config/findpaths.py:338-339`);
  2. 讀 `getini("addopts")`(這時已經是被第 1 步覆寫過的值)並放到最前面;
  3. 以 ini addopts + PYTEST_ADDOPTS + CLI 的完整 `override_ini` 再套一次(`_pytest/config/__init__.py:1567-1572`;註解寫明只做一層)。
- **`config.invocation_params.args` 不含 PYTEST_ADDOPTS,也不含 ini addopts**:docstring 明寫(`_pytest/config/__init__.py:1061-1064`)。args 在 `get_config` 時就被凍結成 tuple(`:359-363`),之後 `args[:] = …` 改的是另一個 list。固定指令 `python -X utf8 -m pytest -q` 的 `invocation_params.args` 是 `("-q",)`(`:211` 取 `sys.argv[1:]`)。
- **結論**:producer 應讀 `config.option.override_ini`(合併後、parse 過的權威值),**不應掃 argv 字串**。掃 argv 會漏掉 PYTEST_ADDOPTS、ini addopts 與 `@檔案`(#24),也要自己處理 `-ovalue`、短選項合併等 argparse 寫法(雖然 `allow_abbrev=False`,`_pytest/config/argparsing.py:395`)。代價是看不到來源;要分來源只能靠私有的 `_inicfg[...].origin`,而它也只分得出 file / override 兩類。

### (b) effective ini 值能否與「repo 所提交的設定」可靠比較

**規劃層(baseline,以 `git show <TARGET>:pyproject.toml` 取得)**

| key | TARGET 已提交值 | 有效值(推得) |
|---|---|---|
| `testpaths` | `["tests"]` | `["tests"]` |
| `addopts` | `"-ra --strict-markers"` | `["-ra", "--strict-markers"]`;`override_ini` 因此含 `strict_markers=true` |
| `python_files` | (未設) | 預設 `["test_*.py", "*_test.py"]`(`_pytest/python.py:87-93`) |
| `python_classes` | (未設) | 預設 `["Test"]`(`:94-99`) |
| `python_functions` | (未設) | 預設 `["test"]`(`:100-105`) |
| `norecursedirs` | (未設) | 預設清單(`_pytest/main.py:229-239`) |
| `collect_imported_tests` | (未設) | 預設 `True`(`_pytest/main.py:248-253`) |
| 設定檔 | `pyproject.toml`(TARGET 沒有其他候選檔) | `config.inipath` 應為 `<root>/pyproject.toml` |

**執行層(producer 在 pytest 執行當下,用什麼正向事實證明「pytest 實際讀到的設定內容 = 已提交版本」)**

先講前提:pytest 讀的是**工作樹**上的設定檔(`_pytest/config/findpaths.py:102` `read_text`;`:53` iniconfig),`config.getini()` 回的是工作樹內容加上 override 的有效值。所以**光看 `getini` 證明不了「= 已提交」**。

| 候選 | 做法 | 工作樹 ≠ 已提交時會不會誤判為相等 | 可行性 / 成本 |
|---|---|---|---|
| 1. 要求整棵工作樹乾淨 | sessionfinish 跑 `git status --porcelain` | 不會 | **不可行**:紅綠燈迴圈(Station 4)本來就在 commit 前跑測試,工作樹必然是髒的 ⇒ 固定全套永遠拿不到 `"true"`,退紅機制失去意義 |
| 2. **設定檔對已提交 blob 比雜湊** | 要求 `config.inipath == <root>/pyproject.toml`,且 `git hash-object <inipath>`(套用 `.gitattributes` 的 eol 正規化)== `git rev-parse HEAD:pyproject.toml` | **不會**:內容有任何差異,雜湊就不同。未追蹤的 `pytest.ini`(#22)會讓 `inipath` 不同,同樣抓得到 | **可行**。成本:producer 在 sessionfinish 多跑 2 次 git 子程序;git 不可用或出錯 ⇒ 缺欄 ⇒ 不得 `"true"`。殘餘:TOCTOU(執行中途改設定再改回去)。比的是 HEAD:已 stage 但未 commit 的修改也算不等(fail-closed)。只改註解也會判不等 —— 與候選 3 的行為差異,見 P4 條件項 |
| 3. 有效值對 HEAD blob 解析後的值 | `git show HEAD:pyproject.toml` → tomllib → `[tool.pytest.ini_options]` → 依 pytest 的型別轉換(args / linelist / paths)換算 → 與 `getini` 逐 key 比 | 對比較清單內的 key 不會;**清單外的 key 看不見** | 成本高:要複製 pytest 的型別轉換與預設值規則(`_pytest/config/__init__.py:1722-1900`),pytest 升版就可能失準 |
| 4. 有效值對寫死在 redlight 的常數 | redlight 定義 `BASELINE = {"python_functions": ["test"], …}` | 對清單內的 key 不會;**清單外的 key 看不見**;常數本身不是從已提交設定推出來的 | 成本中等:常數要與 pyproject 同步,需要一支鎖步測試(讀 TARGET / HEAD 的 pyproject 比對常數)。pyproject 改設定時要一起走票 |
| 5. 私有 `config._inicfg[key].origin` | 區分值來自檔案還是 override | 分得出「被 override」,**分不出「檔案內容 ≠ 已提交」** | 私有 API(`_pytest/config/findpaths.py:22-40`),pytest 升版可能消失;而且只解一半的問題 |

**結論**:執行層唯一能**正向證明**「pytest 讀到的設定內容 = 已提交版本」的,是**候選 2**(inipath + 對 HEAD blob 比雜湊)。其他候選都只證得出「清單內的 key 的有效值 = 某個 baseline」。**若不採候選 2,就要明寫:執行層無法正向證明設定檔內容 = 已提交版本。**

### (c) `-c` / `--config-file` 指向 repo 內權威設定時,producer 能否證明它就是權威設定?

- producer 讀得到 `config.option.inifilename`(使用者給的字串)與 `config.inipath`(`absolutepath(inifile)`,`_pytest/config/findpaths.py:306-311`)。
- `-c pyproject.toml`(從 repo 根執行)⇒ `inipath` 與隱式搜尋的結果相同,rootdir 也相同(`:310-311`)。這時用 P2(b) 候選 2 可以證明內容 = 已提交 ⇒ **證明得了**,成本與隱式情況相同。
- `-c` 指向其他檔 ⇒ `inipath` ≠ `<root>/pyproject.toml` ⇒ 用同一條規則就會被擋。副檔名不被支援時,設定會變成空的(`:309` `or {}`),testpaths 等全部回到預設 ⇒ 收集範圍整個改變。
- **風險**:`-c` 帶來的唯一好處是「明確指定同一份檔」,而代價是多一條要證明的路徑。建議:**`inifilename` 不是 None ⇒ 不是 `"true"`**,不去證明它指向哪裡。這是 fail-closed;成本只是讀一個欄位。若 Jeff 偏好容許 `-c <權威檔>`,那是候選 2 的直接延伸(inipath + 雜湊),不需要額外機制。

### (d) S5c-X1:被 `-p no:<name>` 停用的 plugin 怎麼表示;TARGET 的分類器怎麼處理

- **表示方式**:`set_blocked(name)` 先 unregister,再設 `self._name2plugin[name] = None`(`pluggy/_manager.py:230-233`);`list_name_plugin()` 原樣回傳 `list(self._name2plugin.items())`(`pluggy/_manager.py:427-429`)⇒ 被停用的名稱以 **`(name, None)`** 出現。
- **is_blocked 的語意**:`name in _name2plugin and _name2plugin[name] is None`(`pluggy/_manager.py:235-237`)。`-p <name>` 會 `unblock`,把那一項刪掉(`_pytest/config/__init__.py:858-864`;`pluggy/_manager.py:239-247`)。
- **一個 `-p no:` 會產生幾筆**:`-p no:X` ⇒ `X`、`pytest_X` 兩筆;`-p no:cacheprovider` 另外加上 `stepwise`、`pytest_stepwise` ⇒ 共 4 筆(`_pytest/config/__init__.py:850-857`)。來源不限 CLI:PYTEST_ADDOPTS 與 ini addopts 帶進來的 `-p no:` 也一樣處理(`:1576` 用的是合併後的 args);`get_config` 也會先處理一次 CLI 的 `-p no:`(`:366-368`)。
- **pytest 預設不會停用任何東西**:`_pytest/` 裡呼叫 `set_blocked` 的只有 `consider_pluginarg`(`_pytest/config/__init__.py:852-857`)⇒ 固定全套不會有 `None` 項目(與 4c 真實 session 的 43 項、無 other 一致)。
- **TARGET 怎麼處理 `(name, None)`**:
  1. 不是絕對路徑。
  2. `None` 不會出現在 distinfo 配對裡(`<TARGET>:.claude/hooks/redlight.py:521`)。
  3. `_defining_module(None)` 回 `type(None).__module__ == "builtins"`(`:489`),不是 `_pytest` ⇒ **`kind = "other"`**(`:526-530`)。
  4. `_completeness_verdict` 先檢查 (vii)(`:576-577`),後檢查 `cacheprovider_blocked`(`:579`)⇒ **只要有任何 `-p no:`,就在 (vii) 判 `unknown`**。
  - 〈二十三〉裁決 4 的 `cacheprovider_blocked is True` 分支,在得 `"true"` 的路徑上**永遠走不到**。
  - S5c-F3 的 `-p no:cacheprovider -p _pytest.cacheprovider`:後者只 unblock `_pytest.cacheprovider` 這個名稱,`("cacheprovider", None)` 還在 ⇒ 同樣判 `unknown`。**S5c-F3 在 TARGET 上其實已經被這條路徑擋住**(5c 報告寫 (ii) 被跳過、由 (v) 補位;實際上更早就被 (vii) 擋下)。
- 現行 3c 測試的 `_FakePluginManager` 把 `blocked` 放在另一個 set 裡,`list_name_plugin()` **不含** `None` 項目(`<TARGET>:tests/test_redlight.py:790-811`)⇒ **與 pluggy 實際表示方式不符**。目前沒有任何 3c 測試傳入 `blocked`,所以這個落差沒有造成「為了錯的理由通過」;但 3d 的 driver 必須照實表達(P4)。

### (e) S5c-F2:(ii)、(iii) maxfail、(iv) 為何沒有單獨被鎖住

| 現有測試 | 觸發 (ii) | 觸發 (iii) maxfail | 觸發 (iv) | 其他同時成立的擋法 |
|---|---|---|---|---|
| C3a-1 `<TARGET>:tests/test_redlight.py:958-977` | ✓ lf | | | (v):`filtered_out` 讓快照 ≠ collected |
| C3a-2 / C3a-3 `<TARGET>:tests/test_status.py:2045-2071` | ✓ lf | | | (v) |
| C3e-1 `<TARGET>:tests/test_status.py:2156-2183` | ✓ lf | | | (v) |
| C3c-1 `<TARGET>:tests/test_redlight.py:999-1013` | | ✓ maxfail=1 | ✓ shouldfail | (vi):X 沒有 outcome |
| C3c-2 / C3c-3 `<TARGET>:tests/test_status.py:2076-2102` | | ✓ | ✓ | (vi) |
| C3c-4 `<TARGET>:tests/test_status.py:2104-2122` | ✓ stepwise | | ✓ shouldstop | run_state D(exit 2) |

每一支都同時觸發兩個以上的擋法,所以刪掉 `<TARGET>:.claude/hooks/redlight.py:579-582`、`:583-585` 或 `:588-589` 其中任何一段,全部測試仍會通過(5c 報告 S5c-F2 的紙上推演)。修法:每支測試只破壞一條,其他條件全部成立(包含快照 = collected、每個身分都有 outcome、exit 0),並在**同一支測試裡**放一個「不破壞 ⇒ `"true"`」的對照組,鎖住「這一條單獨生效」。

---

## P3 修法方向候選(只列不選,待 Jeff 裁)

共同前提(三案都適用):
- producer 讀 `config.option.*` 的**解析後**值,不掃 argv(P2(a))。
- **隱私**:新落帳的事實不得含絕對路徑。`inipath` 記 root 相對路徑;`override_ini` 的值可能含路徑(例如 `-o cache_dir=…`),建議**只記 key**,或依〈十九〉的規則正規化;`invocation_params.args` 不落帳。這延續〈二十五〉裁決 1 (1) 類。
- 缺欄或型別錯 ⇒ 不得為 `"true"`(〈二十三〉7 (i) 的延伸)。

### A. 禁止覆寫管道

- **條件**(任一成立 ⇒ 不是 `"true"`):`override_ini` ≠ 已提交 addopts 推得的 override 清單;`inifilename` 不是 None;有任何 `(name, None)`(`-p no:`);`inipath` ≠ `<root>/pyproject.toml`。
- **⚠ 照字面寫成「`override_ini` 非空 ⇒ 不是 `"true"`」會讓固定全套永遠拿不到 `"true"`**,因為已提交的 `--strict-markers` 本身就產生 `strict_markers=true`(P2(a))。所以 A 必須比對一份明確的「已提交 addopts 帶來的 override」清單(TARGET 為 `["strict_markers=true"]`)。這份清單要嘛寫死在 redlight(配一支鎖步測試),要嘛在執行時從已提交的 addopts 推算(需要 pytest 的私有 parser)。
- **擋得住**:#1、#2、#3(帶 `-o` 或 `-p no:` 時)、#4、#10、#11、#21(經 `-o` 時)、#22(inipath)、#24。
- **擋不住**:#23(工作樹改了 `pyproject.toml` 的 `python_functions` 等值,`inipath` 不變、沒有 `-o`)⇒ **除非另加 P2(b) 候選 2 的雜湊比對**。#3 的工作樹 addopts 若只加 `--ignore` 之類,是整檔縮小,本來就安全。
- **未知 / 不可觀察的輸入的預設權限**:A 是**對管道的否定清單**。P1 以外的輸入,或 producer 讀不到的輸入(例如 #27 這種「看不見的跳過」、日後 pytest 新增的會改變 discovery 的 CLI 選項、plugin 自己加的 ini key 被寫進工作樹設定檔)**不在清單上就不會被擋** ⇒ **不是 fail-closed;這是同型漏洞的殘餘。**
  - 理由:`config.option` 的鍵本身是可枚舉的集合,理論上可以改成「每個選項的值都等於預設值或允許清單內的值」,那才是 fail-closed;但這需要知道每個選項的預設值(pytest 的 parser 是私有 API),本輪沒有查證可行性(P5)。
- **固定全套**:採用比對清單的版本 ⇒ 仍得 `"true"`;採照字面「非空」的版本 ⇒ **永遠不是 `"true"`**。
- **成本**:低到中。新欄位 4–5 個;一份 baseline override 常數加一支鎖步測試;3c 的 fake 要補欄位。

### B. 比較 effective collection definition

- **條件**:記下固定 key 集合的有效值(`python_files`、`python_classes`、`python_functions`、`norecursedirs`、`testpaths`、`collect_imported_tests`,以及 `inipath`),與 baseline 比較;不相等或取不到 baseline ⇒ 不是 `"true"`。baseline 可取 P2(b) 候選 3(執行時解析 HEAD blob)或候選 4(寫死常數)。
- **擋得住**:清單內 key 的所有變更,不論管道(#1、#2、#3、#4、#10、#11、#21、#22、#23、#24 中涉及這些 key 的情形)。
- **擋不住**:清單外的 key;以及不是 ini key 的 discovery 輸入(`-p no:unittest` 由 (vii) 另行擋下;`--rootdir` 不比較)。
- **未知 / 不可觀察的輸入的預設權限**:對 key 集合是比對、不是枚舉 ⇒ 清單外的 key **不會被擋** ⇒ **不是 fail-closed;這是同型漏洞的殘餘**(pytest 新增 discovery key、plugin 註冊的 ini key)。
- **固定全套**:有效值 = baseline ⇒ 仍得 `"true"`。
- **成本**:候選 4 中等(常數 + 型別正規化 + 鎖步測試);候選 3 高(git + tomllib + 複製 pytest 的型別轉換規則)。

### C. A 與 B 合用(建議的組法:A 的管道檢查 + P2(b) 候選 2 的雜湊比對)

- **條件**:`override_ini` = 已提交 addopts 推得的清單;`inifilename` 為 None;沒有 `-p no:`;`inipath == <root>/pyproject.toml`;inipath 的內容(套用 eol 正規化)的 blob 雜湊 == `HEAD:pyproject.toml`。
  - 有了雜湊,B 的「逐 key 比有效值」就變得多餘:設定檔內容 = 已提交,且沒有任何 override(除了已提交 addopts 自己帶的)⇒ 有效值必然等於已提交定義。所以 C 實際上是「A + 雜湊」,不需要 B 的 key 清單。
- **擋得住**:P1 中所有會得 `"true"` 的列(#1、#2、#3、#4、#10、#11、#21、#22、#23、#24)。
- **擋不住**:P1 以外、而且**不是**經由 ini 設定或已列管道進來的 discovery 輸入(例如日後 pytest 新增、預設不啟用、會在 `collect()` 內縮小的 CLI 選項)。
- **未知 / 不可觀察的輸入的預設權限**:對「ini 設定」這一面是 **fail-closed**(內容由雜湊鎖住,override 必須等於明確清單,任何其他 `-o` key 都擋);對「非 ini 的 CLI 選項」這一面仍是否定清單 ⇒ **殘餘**,理由同 A。依 P1,TARGET 時點的 pytest 9.1.1 沒有找到這一類會做檔內縮小的 CLI 選項,但這是盤點結果,不是構造保證。
- **固定全套**:工作樹的 `pyproject.toml` 與 HEAD 相同時 ⇒ 仍得 `"true"`。紅綠燈迴圈通常不改 pyproject,所以不受影響;**改了 pyproject 而還沒提交的那段期間,沒有任何 run 能退紅**(fail-closed 的代價)。
- **成本**:中。A 的成本,加上 producer 的 2 次 git 子程序(必須包在 try 內;失敗 ⇒ 缺欄);測試要在 tmp root 建 git repo 並提交 pyproject。

### 建議(待 Jeff 裁)

**建議 C(A 的管道檢查 + 設定檔對 HEAD blob 的雜湊比對),並明寫「非 ini 的 CLI 選項」這一面仍是否定清單的殘餘。** 理由:
1. 27.3 裁決 2 要的是「effective collection definition = repo 所提交的」的**正向證明**。三案中只有雜湊比對能在執行層給出這個證明(P2(b));A 單獨用擋不住 #23,B 單獨用擋不住清單外的 key。
2. 有了雜湊,就不需要複製 pytest 的型別轉換規則(B 的高成本部分),也不需要維護 key 清單。
3. 照字面的 A(「override_ini 非空」)會讓固定全套永遠失去退紅權,不可行。不論選哪一案,都必須以「已提交 addopts 推得的 override 清單」為比較基準。
4. 殘餘那一面的可能補法:改成「`config.option` 的每一個鍵都等於預設值或明確允許的值」的枚舉檢查。這需要先查證 pytest 是否提供公開方式取得選項預設值。建議列入 3d-1 規劃前的追加查證或結案後追蹤票,**不在本輪宣稱可行**。

### S5c-X1 的合約整理建議

**建議採用「本次有任何 `-p no:<name>`(`list_name_plugin()` 中任何值為 None 的項目)⇒ 不是 `"true"`」,作為一條獨立、明文的條件,取代〈二十三〉裁決 4 的 `cacheprovider_blocked` 特判。** 理由:
1. TARGET 的實際行為已經是這樣(P2(d)):(vii) 先於 `cacheprovider_blocked` 判定,所以特判在得 `"true"` 的路徑上走不到。合約與實作的說法應該一致。
2. 現在這個行為是 `_defining_module(None)` 的**副作用**,不是明文規則;將來若有人「修正」分類器,讓 None 被跳過,就會靜默失效。改成明文條件,並由 P4 的測試鎖住,才是機制。
3. 這條規則同時關掉 S5c-F3 的路徑(`("cacheprovider", None)` 會一直留著)。
4. `cacheprovider_blocked` 欄位可以保留為紀錄,但不再具有任何判定權;或在 4d 一併移除。由 Jeff 決定。

---

## P4 紅燈清單(草案;P3 裁定後定稿)

**driver 原則**
- 沿用 3c 的 `pytest.Item` / `pytest.File` 子類與 new-style wrapper 協定。每次模擬執行都載入全新的 conftest(沿用 3c-1b)。全部寫在 tmp root,不碰真實帳本。
- **新 helper 一律接在檔尾**,不改既有 helper。
- **pytest 層級的假物件要與真實 pytest 一致**:
  - `config.option` 帶 `override_ini`、`inifilename`;
  - `config.inipath` 為 `<tmp root>/pyproject.toml` 或測試指定的檔;
  - `config.getini(key)` 回傳與上面一致的有效值;
  - `config.invocation_params.args` 照真實 argv 給(不含 PYTEST_ADDOPTS);
  - fake pluginmanager 的 `list_name_plugin()` **必須包含** `(name, None)` 項目,並與 `is_blocked()` 一致(P2(d))。
- **「test_a 從一開始就不在 collect report 裡」的表達**:R3 的 `files` 參數直接是 `{"tests/test_x.py": [S_B]}`(縮小前清單本身就只有 S_B),**不使用** `filtered_out`。檔案原本有 test_a 這件事,由 R2 的 `{"tests/test_x.py": [S_A, S_B]}` 與情境斷言表達。
- **override 事實的表達**:`option.override_ini = ["strict_markers=true", "python_functions=test_b"]`、`getini("python_functions") == ["test_b"]`;CLI 情境的 `invocation_params.args = ("-q", "-o", "python_functions=test_b")`。
- 若 P3 採雜湊比對:driver 要在 tmp root 執行 `git init`、提交 `pyproject.toml`(沿用 test_status 既有的 git helper 寫法)。工作樹與已提交版本不同的情境,在提交之後再改檔。

### 確定項

| # | 預定 nodeid | 情境 | 預期 | 分類 | TARGET 上失敗的原因 |
|---|---|---|---|---|---|
| 1 | `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3a_an_override_ini_narrowing_is_not_full_coverage` | CLI `-o python_functions=test_b`;快照與 collected 都只有 X_B;其他條件全部成立 | `file_coverage != "true"` | behavior-red | `<TARGET>:.claude/hooks/redlight.py:590-592`({X_B} == {X_B})、`:457-458` 與 `<TARGET>:tests/conftest.py:322-341` 沒有任何 override 事實 ⇒ `:597` `"true"` |
| 2 | `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3b_an_override_from_pytest_addopts_is_not_full_coverage` | 同 #1,但 `invocation_params.args == ("-q",)`(argv 裡沒有 `-o`),override 只出現在 `config.option.override_ini`(模擬 PYTEST_ADDOPTS) | `!= "true"` | behavior-red | 同 #1 |
| 3 | `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3c_a_config_file_option_is_not_full_coverage` | `-c alt.toml`(`inifilename="alt.toml"`、`inipath=<root>/alt.toml`,內容設 `python_functions = test_b`);沒有 `-o` | `!= "true"` | behavior-red | 同 #1;TARGET 不讀 `inifilename` / `inipath` |
| 4 | `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3w_an_unexpected_config_file_is_not_full_coverage` | repo 根有一份未追蹤的 `pytest.ini`(`inipath=<root>/pytest.ini`,`python_functions = test_b`);沒有 `-o`、沒有 `-c` | `!= "true"` | behavior-red | 同 #3 |
| 5 | `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3w_an_uncommitted_config_change_is_not_full_coverage` | tmp git repo 提交了 baseline `pyproject.toml`,之後在工作樹加上 `python_functions = ["test_b"]`;`inipath=<root>/pyproject.toml`;沒有 `-o` | `!= "true"` | behavior-red | 同 #1;TARGET 沒有任何設定檔內容的事實 |
| 6 | `tests/test_status.py::TestOverrideIniChain::test_d3a_full_then_override_ini_does_not_produce_a_false_green` | R1 收集錯誤(exit 2)⇒ 整檔紅;R2 全套 S_A passed、S_B failed(exit 1);R3 `-o python_functions=test_b`,S_B passed(exit 0)。**每次執行都用新的 conftest**。情境斷言:R1 為 D、R2 為 B、R3 schema 合格且為 A | `tests/test_x.py` 在 red、不在 green | behavior-red | `<TARGET>:.claude/portable/status.py:470-472` 退掉整檔紅;`:475` green(經 `<TARGET>:.claude/hooks/redlight.py:597`) |
| 7 | `tests/test_status.py::TestOverrideIniChain::test_d3a_override_ini_does_not_orphan_a_known_red` | 已知紅 test_a;R `-o python_functions=test_b` 只收集到 S_B,passed | 不在 orphaned;仍在 red | behavior-red | `<TARGET>:.claude/portable/status.py:464-468` 把 test_a 移到 orphan |
| 8 | `tests/test_status.py::TestOverrideIniChain::test_d3a_override_ini_does_not_make_a_clean_file_green` | 先前沒有紅;R `-o python_functions=test_b` | 不在 green | behavior-red | `<TARGET>:.claude/portable/status.py:475` |
| 9 | `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3i_lf_alone_is_not_full_coverage` | 只破壞 (ii):`lf=True`,但快照 = collected、每個身分都有 outcome、exit 0。同一支測試內附對照組(`lf=False` ⇒ `"true"`) | 對照 `== "true"`;破壞後 `!= "true"` | regression-lock | (TARGET 上通過:`:579-582` ⇒ `"false"`) |
| 10 | `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3i_maxfail_alone_is_not_full_coverage` | 只破壞 (iii):`maxfail=1`,但 shouldfail 為 False、全部執行完成;附對照組 | 同上 | regression-lock | (TARGET:`:583-585` ⇒ `unknown`) |
| 11 | `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3i_shouldfail_alone_is_not_full_coverage` | 只破壞 (iv):`shouldfail=True`,maxfail 為 None、全部執行完成;附對照組 | 同上 | regression-lock | (TARGET:`:588-589` ⇒ `unknown`) |
| 12 | `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3x_a_blocked_plugin_is_not_full_coverage` | `-p no:cacheprovider`:`list_name_plugin()` 含 `cacheprovider` / `pytest_cacheprovider` / `stepwise` / `pytest_stepwise` 四筆 `None`,`is_blocked` 一致,`option` 沒有 `lf` / `stepwise` 屬性;其他條件全部成立 | `!= "true"` | **regression-lock**(TARGET 經 `<TARGET>:.claude/hooks/redlight.py:489, 526-530` 判 other ⇒ `:576-577` 判 `unknown`) | — |
| 13 | `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3d_the_fixed_command_with_the_committed_config_is_full_coverage` | 固定全套:`invocation_params.args == ("-q",)`、`override_ini == ["strict_markers=true"]`、`inifilename` 為 None、`inipath=<root>/pyproject.toml`(若採雜湊,內容 = 已提交)、沒有 `None` 項目 | `== "true"` | regression-lock | —(TARGET 忽略新事實,照樣判 `"true"`)。**這支專門擋「override_ini 非空 ⇒ 不是 true」那種照字面的實作** |
| 14 | `tests/test_status.py::TestCollectionDefinitionLocks::test_d3d_the_fixed_command_full_run_still_retires_the_red` | 已知紅 CHAIN_X;以 #13 的事實跑一次全套,全部 passed | 退紅、在 green | regression-lock | — |

- **#1 與 #2 不合併成參數化**:兩者在 producer 讀 `config.option.override_ini` 時是同一個事實(P2(a)),但 #2 的 argv 裡**沒有** `-o`。這一支專門讓「掃 argv」的實作失敗。只有 #1 的話,掃 argv 的實作也會通過。
- ini addopts 帶入的 `-o`(P1 #3)與 `@檔案`(P1 #24)落在同一個事實上,和 #2 的差別只在 argv 的內容。不另立測試,由 #2 涵蓋。

### 條件項(依 P3 決定分類)

| # | 預定 nodeid | 情境 | 若 P3 採… | 分類 |
|---|---|---|---|---|
| 15 | `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3c_a_config_file_option_naming_the_committed_config` | `-c pyproject.toml`(就是已提交的那一份),其他同固定全套 | 「`-c` 一律 fail-closed」(P2(c) 建議)⇒ 預期 `!= "true"` | behavior-red(TARGET 判 `"true"`) |
|  |  |  | 「容許指向權威檔」⇒ 預期 `== "true"` | regression-lock |
| 16 | `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3w_a_non_collection_edit_to_the_config_file` | 工作樹的 `pyproject.toml` 只改了註解(已提交 vs 工作樹不同,收集相關的 key 全部相同) | 雜湊比對(C)⇒ 預期 `!= "true"` | behavior-red |
|  |  |  | 逐 key 比較(B)⇒ 預期 `== "true"` | regression-lock |

### 預期集合(確定項;條件項 #15、#16 待 P3 裁定後再加入其中一個集合)

**預期紅集合(behavior-red,8 支)**:

- `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3a_an_override_ini_narrowing_is_not_full_coverage`
- `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3b_an_override_from_pytest_addopts_is_not_full_coverage`
- `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3c_a_config_file_option_is_not_full_coverage`
- `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3w_an_unexpected_config_file_is_not_full_coverage`
- `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3w_an_uncommitted_config_change_is_not_full_coverage`
- `tests/test_status.py::TestOverrideIniChain::test_d3a_full_then_override_ini_does_not_produce_a_false_green`
- `tests/test_status.py::TestOverrideIniChain::test_d3a_override_ini_does_not_orphan_a_known_red`
- `tests/test_status.py::TestOverrideIniChain::test_d3a_override_ini_does_not_make_a_clean_file_green`

**預期綠集合(regression-lock,6 支)**:

- `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3i_lf_alone_is_not_full_coverage`
- `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3i_maxfail_alone_is_not_full_coverage`
- `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3i_shouldfail_alone_is_not_full_coverage`
- `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3x_a_blocked_plugin_is_not_full_coverage`
- `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3d_the_fixed_command_with_the_committed_config_is_full_coverage`
- `tests/test_status.py::TestCollectionDefinitionLocks::test_d3d_the_fixed_command_full_run_still_retires_the_red`

- #4、#5 列為確定項的理由:27.3 裁決 2 要求正向證明「= repo 所提交的定義」。任何符合合約的實作,都必須把「工作樹多一份設定檔」與「工作樹改過設定檔」判為不是 `"true"`。若 P3 選了照字面、不含 inipath / 雜湊的 A,這兩支會一直紅 —— 那正是它們要揭露的殘餘。
- S5c-F2 的對照組(#9–#11 的「不破壞 ⇒ `"true"`」)在 4d 之後需要 driver 帶齊新事實才會成立。所以 3d 的 driver 從一開始就要帶齊固定全套的 pytest 層級事實(#13 那一組)。

### 4d 後會受新合約影響的既有測試

新合約下,缺新事實 ⇒ 不得為 `"true"`。下列既有測試的 fake / fixture **沒有**新事實,但斷言「`"true"`」、green、退紅或 orphan,4d 後會失敗(以 `git grep` 在 TARGET 上找出的正向斷言為準):

| nodeid | 依賴(TARGET 行號) |
|---|---|
| `tests/test_redlight.py::TestFileCoverage::test_b1c_a_file_argument_without_deselection_is_full_coverage` | `== "true"`(`:538`) |
| `tests/test_redlight.py::TestFileCoverage::test_b1d_a_parent_directory_argument_is_full_coverage` | `== "true"`(`:554`) |
| `tests/test_redlight.py::TestFixedCommandCoverage::test_b10_the_fixed_command_without_positional_args_is_full_coverage` | `== "true"`(`:654`) |
| `tests/test_redlight.py::TestCompletenessCoverage::test_c3d_the_fixed_command_with_everything_off_is_full_coverage` | `== "true"`(`:1063`) |
| `tests/test_status.py::TestTestsUnderTicketUsesTheLatestRecordPerFile::test_a_file_that_went_red_then_green_counts_as_green` | green(`:592`;直接以 `record_session` 寫 completeness dict) |
| `tests/test_status.py::TestOrphans::test_a_renamed_red_test_is_orphaned_not_green` | orphan(`:1336-1356` 一帶;同上) |
| `tests/test_status.py::TestChainRegressionLocks::test_l3_a_full_directory_run_retires_the_red` | green(`:1722`) |
| `tests/test_status.py::TestCompletenessLocks::test_c3d_the_fixed_command_full_run_still_retires_the_red` | green(`:2201`) |
| `tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_builtin_root_conftest_and_known_dist_as_not_other` | `== "true"`(`:2298`) |

- 共 9 支:〈二十三〉5 授權過的 6 支,加上 3c 新增、斷言 `"true"` / green 的 3 支(C3d-1、C3d-2、C3p-7)。
- **需要的授權**(比照〈十七〉裁決 5、〈二十三〉5):4d 只在這 9 支的 fake / fixture 補上「已提交設定、沒有額外 override、沒有 `-c`、沒有 `-p no:`」的事實(若採雜湊,另外在 tmp root 建 git repo 並提交 pyproject);assertion、docstring、test identity 一律不改。
- 3c 中斷言 `!= "true"` / 不 green 的測試,4d 後仍會通過,但通過的理由可能多了「缺新事實」。這不需要授權,但 4d 報告應逐支說明主因沒有改變(延續 S5c-F2 的關切)。
- C3p-6(`<TARGET>:tests/test_status.py:2258-2280`)斷言帳本不含 tmp root 的絕對路徑:新事實若記 `inipath` 的絕對路徑,會讓它失敗。**這是隱私約束,不是可授權的修改**(見 P3 共同前提)。

---

## P5 尚未證明 / 本輪未做

1. **全部 pytest / pluggy 行為都是讀原始碼推得的,未實測。** 包括:`override_ini` 的合併內容(特別是固定全套含 `strict_markers=true`)、`(name, None)` 的實際出現、`invocation_params.args == ("-q",)`。27.2 的外部重現只證明了 S5c-F1 本身。
2. P1 #5(`--rootdir`)與位置參數正規化、`testpaths` 的交互沒有逐案推演。
3. P2(b) 候選 2 的 `git hash-object` 是否在所有 `.gitattributes` / `core.autocrlf` 組合下都與 HEAD blob 一致,沒有驗;TOCTOU 只做了定性描述。
4. P3 A 的「從已提交 addopts 推算 override 清單」需要 pytest 的私有 parser,可行性未查;寫死常數 + 鎖步測試的方式可行性較高,但也未寫。
5. P3 建議第 4 點的「`config.option` 全鍵枚舉」:pytest 是否提供公開方式取得每個選項的預設值,未查。
6. root conftest(`tests/conftest.py`)在工作樹被改(例如加入 `collect_ignore` 或會靜默移除身分的 hook):〈二十三〉3 把它當作信任邊界內的 producer。雜湊比對可以延伸到這個檔,但是否納入,本輪未評估,建議 Jeff 一併裁定是否列入 3d。
7. P1 列了 27 項,是 pytest 9.1.1 內建選項與 ini key 中「看起來和收集有關」的部分,**不是**對全部選項的窮舉。
8. CLEAN / REAL 層不在本輪範圍。
