# 票 145(M1-a)Station 3c 紅燈規劃 —— 選擇 / 執行完整性

- 依據:票 145〈二十一〉21.3 裁決 2、3。
- 本檔只做規劃:**不寫測試、未執行任何 pytest**(含 `--collect-only` / `--version`),也沒有另寫 probe。
  本檔所有 pytest 行為都是讀原始碼推得的,不是實測觀察。
- 程式碼錨點:`<T>` = `851cbd75b359a6b2a34452265e8a70992fa56996`(Station 4b TARGET)。
  `.claude/hooks/redlight.py`、`.claude/portable/status.py`、`tests/conftest.py` 自 `<T>` 起到本檔撰寫時的 HEAD `353ca18` 都沒有改動
  (中間兩個 commit 只改 docs)。
- 版本:`python -m pip show pytest` ⇒ `Version: 9.1.1`;`python -m pip show pluggy` ⇒ `Version: 1.6.0`。
- 出處格式:`_pytest/<檔名>:<行號>`、`pluggy/<檔名>:<行號>`、`anyio/<檔名>:<行號>`(只讀原始碼)。

## P0 外掛觀察

**pytest-prefixed distributions 的觀察清單,非 exhaustive plugin inventory**(`python -m pip list` 中名稱以 `pytest` 開頭的):

| distribution | 版本 |
|---|---|
| pytest | 9.1.1 |

`[pytest11]` entry points(用 Grep 搜系統 site-packages 下 `*.dist-info/entry_points.txt`):

| dist-info | entry point |
|---|---|
| `anyio-4.15.0.dist-info` | `anyio = anyio.pytest_plugin` |

- `python -m site --user-site` 回報的使用者層 site-packages 目錄不存在,所以那一層沒有東西可搜。
- 沒有盤點:`-p <name>` 指名載入、`PYTEST_PLUGINS` 環境變數、conftest 的 `pytest_plugins` 變數、sys.path 上其他位置的套件。
  本 repo 的 `*.py / *.toml / *.ini / *.cfg / *.yml / *.yaml` 用 Grep 搜 `pytest_plugins|PYTEST_PLUGINS|PYTEST_ADDOPTS|-p no:`,0 筆。
  `pyproject.toml:70-72` 的 `addopts = "-ra --strict-markers"` 不載入外掛。
- **installed plugin inventory 未完整證明。**

## P1 機制盤點表(pytest 9.1.1)

欄位:
(1) 會不會呼叫 `pytest_deselected`;
(2) 會不會在收集期悄悄移除身分(不發通知),會的話是哪個 hook;
(3) 會不會提前停止執行;
(4) exit code,以及 `<T>` 的 `run_state` 會判成什麼(`<T>:.claude/hooks/redlight.py:362-376`:exit 不在 {0,1,5} 或有收集錯誤 ⇒ D;有 failed ⇒ B;0 collected ⇒ C;沒有 passed ⇒ F;其他 ⇒ A);
(5) conftest 在 run 結束時能從哪裡正向讀到它。

分類:**SN-silent** = selection narrowing(悄悄)/ **SN-notified** = selection narrowing(有通知)/ **ES** = execution early-stop / **NX** = no-execution / **RO** = only-reorder。

| # | 機制 | 分類 | (1) deselected | (2) 收集期悄悄移除 | (3) 提前停止 | (4) exit / `<T>` run_state | (5) 正向讀取點 |
|---|---|---|---|---|---|---|---|
| 1 | `-k` | SN-notified | 是 —— `_pytest/mark/__init__.py:207-223` | 否 | 否 | 0 / 1;全部被排除 ⇒ `testscollected = len(items) = 0` ⇒ 5(`_pytest/main.py:388-389, 882`)/ A、B、F | `config.option.keyword`(`_pytest/mark/__init__.py:91-93`) |
| 2 | `-m` | SN-notified | 是 —— `_pytest/mark/__init__.py:255-269` | 否 | 否 | 同上 | `config.option.markexpr`(`_pytest/mark/__init__.py:111-113`) |
| 3 | `--deselect` | SN-notified | 是 —— `_pytest/main.py:481-496` | 否 | 否 | 同上 | `config.option.deselect`(`_pytest/main.py:174-179`) |
| 4 | `--ignore` | SN-silent(整個路徑) | 否 | 是,但以**整檔 / 整目錄**為單位 —— `pytest_ignore_collect`(`_pytest/main.py:437-450`)。被忽略的檔一個身分都不會被收集 ⇒ `<T>:.claude/hooks/redlight.py:402-404` 判 `"unknown"`(安全) | 否 | 0 / 1 / 5 / A、B、C | `config.option.ignore`(`_pytest/main.py:162-167`) |
| 5 | `--ignore-glob` | SN-silent(整個路徑) | 否 | 同上 —— `_pytest/main.py:452-461` | 否 | 同上 | `config.option.ignore_glob`(`_pytest/main.py:168-173`) |
| 6 | `--lf` / `--last-failed`(檔內過濾) | **SN-silent(檔內)** | 否 | **是** —— `LFPluginCollWrapper.pytest_make_collect_report`(`wrapper=True`)就地改寫 File collector 的 `res.result`(`_pytest/cacheprovider.py:248-292`,過濾在 282-290)。只在**已經收集到至少一個 lastfailed 身分之後**才過濾(273-279) | 否 | 0 / 1 / A、B | `config.option.lf`(`_pytest/cacheprovider.py:478-484`);`--lf` 時一定註冊 `lfplugin-collwrapper`(326-330);**真的發生過濾時**會註冊 `lfplugin-collskip`(276-278)⇒ `config.pluginmanager.get_plugin("lfplugin-collskip")`(`pluggy/_manager.py:312-314`)不是 None |
| 6' | `--lf`(整檔略過) | SN-silent(整檔) | 否 | 是 —— `LFPluginCollSkipfiles.pytest_make_collect_report` 回傳空結果(`_pytest/cacheprovider.py:299-310`)⇒ 該檔沒有身分 ⇒ `"unknown"`(安全) | 否 | 同上 | 同 #6 |
| 6'' | `--lf`(modifyitems 層) | SN-notified | 是 —— `_pytest/cacheprovider.py:389-391`(previously_passed) | 否 | 否 | 同上 | 同 #6 |
| 7 | `--lfnf` / `--last-failed-no-failures` | `none`:SN-notified;`all`(預設):無效果 | `none` 且沒有 lastfailed ⇒ 全部 deselect(`_pytest/cacheprovider.py:404-409`) | 否 | 否 | `none` ⇒ 全部被排除 ⇒ 5 / F | `config.option.last_failed_no_failures`(`_pytest/cacheprovider.py:522-534`) |
| 8 | `--ff` / `--failed-first` | RO | 否 | 否(`lfplugin-collwrapper` 只在 `lf` 時註冊,`_pytest/cacheprovider.py:326-330`)| 否 | 0 / 1 / A、B | `config.option.failedfirst`(485-492);只改順序(393) |
| 9 | `--nf` / `--new-first` | RO | 否 | 否 | 否 | 同上 | `config.option.newfirst`(494-501);只改順序(`_pytest/cacheprovider.py:439-451`) |
| 10 | `--sw` / `--stepwise` | SN-notified + **ES** | 是 —— 略過的前段(`_pytest/stepwise.py:170-172`) | 否 | **是** —— 失敗即設 `session.shouldstop`(`_pytest/stepwise.py:183-188`)⇒ `session.Interrupted`(`_pytest/main.py:411-412`;`Interrupted` 繼承 `KeyboardInterrupt`,514)⇒ exit 2 | 停下時 2 / **D**;沒有失敗 ⇒ 0 / A、F | `config.option.stepwise`(`_pytest/stepwise.py:25-31`);`stepwiseplugin` 註冊(57-58);`session.shouldstop`(`_pytest/main.py:643-658`) |
| 11 | `--sw-skip` | 同 #10 | 同 #10 | 否 | 第一次失敗不停(`_pytest/stepwise.py:176-182`),第二次失敗才停 | 停下時 2 / D;否則 1 / B | `config.option.stepwise_skip`(33-41;它會連帶把 `stepwise` 設成真,55-56) |
| 12 | `-x` / `--exitfirst` | **ES** | 否 | 否(但收集期若有收集錯誤,`pytest_collectstart` 會拋 `Failed` 中止收集,`_pytest/main.py:690-695`) | **是** —— `maxfail = 1`(`_pytest/main.py:59-66`);失敗計數到達即設 `shouldfail`(698-703)⇒ `session.Failed`(409-410)⇒ exit 1(334-335) | 1 / **B**(有收集錯誤時 D) | `config.option.maxfail == 1`;`session.shouldfail`(`_pytest/main.py:661-676`) |
| 13 | `--maxfail=N` | ES | 否 | 同 #12 | 是(同 #12) | 1 / B | `config.option.maxfail`(`_pytest/main.py:67-75`);`session.shouldfail` |
| 14 | `--collect-only` / `--co` | **NX** | 否 | 否 | 不執行 —— `pytest_runtestloop` 直接 return(`_pytest/main.py:403-404`) | 0;0 個身分 ⇒ 5;有收集錯誤 ⇒ `Interrupted`(398-401)⇒ 2 / F、C、D | `config.option.collectonly`(`_pytest/main.py:150-156`) |
| 15 | `--setup-only` | NX(只做 setup / teardown) | 否 | 否 | 不執行 call —— `_pytest/runner.py:134-139` | 0(setup 錯誤 ⇒ 1)/ F、B | `config.option.setuponly`(`_pytest/setuponly.py:17-22`) |
| 16 | `--setup-plan` | NX | 否 | 否 | 不執行 call;fixture 回傳假值(`_pytest/setupplan.py:22-31`),並連帶設 `setuponly`(34-38) | 0 / F | `config.option.setupplan`(`_pytest/setupplan.py:13-19`) |
| 17 | `-p no:cacheprovider` | 停用機制(使 #6–#11 不可用) | — | — | — | — | 同時封鎖 `stepwise`(`_pytest/config/__init__.py:850-855`);`config.pluginmanager.is_blocked("cacheprovider")`(`pluggy/_manager.py:235`)。此時 `config.option` 上**沒有** `lf` / `stepwise` 等屬性(那些選項由 cacheprovider / stepwise 的 `pytest_addoption` 加入) |
| 18 | KeyboardInterrupt | ES | 否 | 否 | 是 | `wrap_session` 接住 ⇒ 2(`_pytest/main.py:336-345`)/ **D** | `exitstatus == 2`;`pytest_keyboard_interrupt` hook(344) |
| 19 | 測試內 `pytest.exit()` | ES | 否 | 否 | 是 —— `Exit` 由 runner 重拋(`_pytest/runner.py:262-267`),在 call 階段拋出時**沒有 call / teardown report** | `returncode` 為 None ⇒ 2 / D;**`returncode=0` ⇒ 0**(`_pytest/main.py:339-341`;`_pytest/outcomes.py:65-72, 97-99`)/ **A 或 F** | `returncode=0` 時:`shouldstop` / `shouldfail` 都沒有設,exitstatus 是 0 ⇒ **從 config / session 讀不到**。只能從「有 selected 身分沒有任何終局 outcome」間接看出(P3-B) |
| 20 | anyio(P0 觀察到的 entry-point 外掛) | 不縮小;**會擴增** | 否 | 否。`pytest_pycollect_makeitem`(`anyio/pytest_plugin.py:192-207`)只加 marker | 否 | 不影響 | 外掛有沒有註冊:`config.pluginmanager.list_plugin_distinfo()`(`pluggy/_manager.py:422-425`)。⚠ 它的 `pytest_collection_finish`(`anyio/pytest_plugin.py:210-`)會**替換** `session.items` 裡帶 `anyio` marker、但沒有 `anyio_backend` 的 async 測試(擴成每個 backend 各一份)。conftest 註冊得比 entry-point 外掛晚,所以先被呼叫(`pluggy/_hooks.py:403-408`、`pluggy/_callers.py:93`)⇒ conftest 記到的 selected 是**擴增前**的身分,之後的 outcome 身分不在 selected ⇒ `<T>:.claude/hooks/redlight.py:331-334` 判 INVALID。這是讀原始碼推得的,本 repo 有沒有這種測試沒有查 |
| 21 | **未知第三方 plugin** | 可能任何一類 | 不一定 | 可以,而且有多個 hook 能做:`pytest_ignore_collect`(整路徑)、`pytest_collect_file`(換掉 Module)、`pytest_pycollect_makeitem`(在 Module.collect 內丟掉函式,比任何 collect report 都早)、`pytest_make_collect_report`(wrapper 或 firstresult)、`pytest_collection_modifyitems`(移除但不呼叫 deselected)、`pytest_collection_finish`(改 `session.items`)| 可以:`pytest_runtestloop` / `pytest_runtest_protocol` 都是 firstresult,可以只跑子集而**不產生任何 report**;也可以設 `shouldstop` / `shouldfail` | 任意 | producer 察覺得到的:執行期的跳過(selected 身分沒有 outcome,P3-B)、`shouldstop` / `shouldfail`、modifyitems 期的移除(視 hook 順序,P2(d))。**察覺不到的:收集期在 collect report 之前的移除**(P2(d)) |

P1 共 **24 列**(編號 1–21,其中 #6 拆成 6 / 6' / 6'' 三列)。

## P2 特別查證

### (a) conftest 的 outcome 從哪個 phase 取?`--setup-only` / `--setup-plan` 會不會產生假 passed?

- `<T>:tests/conftest.py:203-219` 收 `call` / `setup` / `teardown` 三個 phase 的 report。由 `_run_outcome`(`<T>:tests/conftest.py:185-200`)決定結果:
  - 任何 phase failed ⇒ `"failed"`(192-193),而且之後不會被覆蓋(218)。
  - skipped(通常在 setup)⇒ `"skipped"`,xfail ⇒ `"other"`(196-197)。
  - **`"passed"` 只來自 `when == "call"`**(198-199)。setup / teardown 的 passed 回傳 None,不寫入。
- `--setup-only` 下,`_pytest/runner.py:134-139` 不呼叫 call ⇒ 只有 setup passed + teardown passed ⇒ outcome 不寫入 ⇒ **不會產生假 passed**。`--setup-plan` 連帶設 `setuponly`(`_pytest/setupplan.py:34-38`),結論相同。
- `<T>` 對這種 run 的判定:collected 非空、沒有 passed、exit 0 ⇒ F;沒有 passed ⇒ 不退紅、不 green(`<T>:.claude/portable/status.py:471, 474-475`)。
  但 coverage 會是 `"true"` ⇒ 有 orphan 權(464-468)。21.3 裁決 2 之後,它屬於 NX,應該失去 orphan 權。
- 附帶(既有行為,不是本票範圍):逐檔的 `_outcomes` 在 setup / teardown passed 時也會建立條目(`<T>:tests/conftest.py:211-212`),`pytest_sessionfinish` 因此會替每個碰到的檔寫一筆 8 欄 **green** 紀錄(225-226)。`<T>` 的 status 不會因 8 欄 green 退紅(`<T>:.claude/portable/status.py:509-515`);R3 讀這些 green 紀錄的行為沒有查。
- **結論:不會產生假 passed;不是新發現。**

### (b) `-x` / `--maxfail`:審查報告 G5 的「不會假綠」在 `<T>` 上成立嗎?

逐步推演(檔 W 在檔 X 之前執行,args `["tests"]`,沒有收集錯誤):
1. W 某身分 failed ⇒ `testsfailed` 到達 maxfail ⇒ `shouldfail`(`_pytest/main.py:698-703`)⇒ 該 item 的 teardown 照常報告(`_pytest/runner.py:142-144`)⇒ `pytest_runtestloop` 拋 `Failed`(409-410)⇒ exit 1(334-335)⇒ `<T>` run_state B。
2. W 有 failed ⇒ `<T>:.claude/portable/status.py:449-455` 只加紅。
3. X 已收集、沒有 deselected ⇒ `file_coverage` = `"true"`。但 X 沒有任何 outcome ⇒ 已知紅不退(474);整檔紅不退(471);`green_now = "passed" in results` = False(475)⇒ **不會 green**。
4. **但 orphan 會發生**:X 有已知紅身分 `test_old`,而本次完整收集沒有它 ⇒ 進 orphan(464-468)。

⇒ G5 的「不會假綠」**成立**。可是 21.3 裁決 3(c) 要求「不得被當成 orphan-safe」,而 `<T>` 會讓提前停止的 run 行使 orphan 權 ⇒ 這一半在 `<T>` 上**會失敗**(見 P4 C3c-2)。

補充:會讓「部分執行、本檔沒有 failure」的檔變 green 的提前停止,是 `pytest.exit(returncode=0)`(P1 #19),不是 `-x`。
`-x` / `--maxfail` 停下時,所在檔一定有 failure(停止由該檔的 failed report 觸發);它之後的檔沒有 outcome。

### (c) `--sw`:哪一半走 `pytest_deselected`,哪一半是提前停止?

- **選擇那一半**:有快取的 `last_failed`,而且測試數沒變時,把它之前的 items 移除並呼叫 `pytest_deselected`(`_pytest/stepwise.py:151-172`)⇒ 有通知 ⇒ `<T>` 判 `"false"`。
- **停止那一半**:之後第一次 failed(`--sw-skip` 時是第二次)設 `session.shouldstop`(`_pytest/stepwise.py:174-189`)⇒ `pytest_runtestloop` 拋 `session.Interrupted`(`_pytest/main.py:411-412`)。這是 `KeyboardInterrupt` 的子類(514),所以 `wrap_session` 判 exit 2(336-345)⇒ `<T>` run_state **D** ⇒ 整個 run 沒有退紅權、不 green、不 orphan(`<T>:.claude/portable/status.py:456-458`)。
- 對照:`-x` / `--maxfail` 走 `shouldfail` ⇒ `Failed` ⇒ exit 1 ⇒ B。**兩者的停止路徑不同,exit code 也不同。**

### (d) hook 順序,以及「縮小前的完整身分全集」能不能被觀察(最重要)

**順序**(`_main`,`_pytest/main.py:380-390`):
1. `pytest_collection` ⇒ `Session.perform_collect`(393-394);`self.items = []`(816)。
2. `collect_one_node(self)`(849)。每個 collector 依序跑 `pytest_collectstart` ⇒ `pytest_make_collect_report`(`_pytest/runner.py:586-593`)。
   - **`--lf` 在這裡縮小**:`LFPluginCollWrapper` 是 `hookimpl(wrapper=True)`(沒有 tryfirst / trylast),在 `yield` 之後**就地**改寫 File collector 的 `res.result`(`result[:] = …`,`_pytest/cacheprovider.py:248-292`)。
   - `LFPluginCollSkipfiles` 是一般 firstresult 實作,直接回傳空結果(299-310)。
3. `genitems` 遞迴(`_pytest/main.py:1023-1037`):Item ⇒ `pytest_itemcollected`(1026);Collector ⇒ 子節點全部 yield 完**之後**才呼叫它的 `pytest_collectreport`(1037)。Session 自己的 collect report 在 850。
4. `self.items.extend(...)`(869)。
5. `pytest_collection_modifyitems`(872-874):`-k` / `-m`(`_pytest/mark/__init__.py:282`)、`--deselect`(`_pytest/main.py:481-496`)、`LFPlugin` 的 `wrapper=True, tryfirst=True`(`_pytest/cacheprovider.py:363-413`)、`NFPlugin`(435-455)、stepwise(`_pytest/stepwise.py:129-172`)。
6. `pytest_collection_finish`(`_pytest/main.py:879`,在 finally 裡,收集中途拋例外也會呼叫)。
7. `testscollected = len(items)`(882)。
8. `pytest_runtestloop`(397-413)。

**`<T>` 的 conftest 看到的是什麼**:
- `pytest_collectreport`(`<T>:tests/conftest.py:150-164`):只用 failed 的 report;而且它在步驟 3 才被呼叫,那時 `res.result` 已經被步驟 2 改掉 ⇒ **縮小後**。
- `pytest_deselected`(167-175):只看得到有通知的那幾類。
- `pytest_collection_finish`(178-182):步驟 6 的 `session.items` ⇒ **縮小後**,也是 modifyitems 之後。

**有沒有一個可靠的時點能看到縮小前的全集?**
- **對內建 `--lf`:有(讀原始碼推得,未實測)。** pluggy 呼叫 wrapper 的順序是 tryfirst wrapper、一般 wrapper、trylast wrapper(`pluggy/_hooks.py:403-408`;`pluggy/_callers.py:93` 反向迭代)。`yield` 之後的 teardown 再反向執行(`pluggy/_callers.py:135`)⇒ **trylast wrapper 最內層,它 `yield` 之後的程式碼最先執行**。
  所以在 `tests/conftest.py` 加一個 `hookimpl(wrapper=True, trylast=True)` 的 `pytest_make_collect_report`,能在 `LFPluginCollWrapper` 改寫之前看到 File collector 的完整 `res.result`。
  兩個條件:
  1. 必須**立刻複製 nodeid**。LF 是就地改同一個 list 物件(`_pytest/cacheprovider.py:282`),只存參考的話,事後會看到縮小後的內容。
  2. `LFPluginCollSkipfiles` 的整檔略過會讓那個檔的結果本來就是空的。那個檔反正沒有身分 ⇒ `"unknown"`(安全)。
- **對未知第三方 plugin:不成立。** 理由:
  1. `pytest_pycollect_makeitem` 在 `Module.collect` 內部就能丟掉函式,比任何 `pytest_make_collect_report` wrapper 看得到的結果都早。
  2. 第三方可以用**非 wrapper** 的 `pytest_make_collect_report`(firstresult)直接回傳已經縮小的 report。非 wrapper 實作在任何 wrapper 的 `yield` 之後程式碼之前就跑完(`pluggy/_hooks.py:403-408`),trylast wrapper 看到的就是縮小後的結果。
     wrapper 之間的順序也不保證:trylast 是插在 wrapper 區段的**最前面**(`pluggy/_hooks.py:464-465`),所以**越晚註冊的 trylast wrapper 越內層**。entry-point 外掛比 conftest 早註冊,它的 trylast wrapper 在 conftest 外層(conftest 先看到);但子目錄的 conftest、或收集期才動態註冊的 plugin 比 `tests/conftest.py` 晚,會在更內層,先改掉結果。
  3. `pytest_collect_file` 可以換掉整個 collector。
  4. modifyitems 階段:tryfirst 是插在 wrapper 區段的最後面(`pluggy/_hooks.py:466-467`),越晚註冊的越外層。conftest 的 `wrapper=True, tryfirst=True` 比 entry-point 外掛晚註冊,通常在最外層,可以在 `yield` 之前拍快照、之後比對(移除了卻沒呼叫 deselected ⇒ 看得出來)。但子目錄的 conftest 註冊得更晚,會在更外層,不保證。
- **結論:無法由 selected / outcomes 單獨證明 selection completeness。** 對內建 `--lf` 有一個可觀察縮小前全集的時點(未實測);對未知第三方 plugin 沒有。
  所以 selection completeness 的正向證據**只能靠 provenance**:沒有任何已知的 silent-narrowing 機制在作用,而且沒有未知 plugin。

## P3 修法方向候選(只列不選,待 Jeff 裁)

共同前提(21.3 裁決 2):任一必要事實缺欄、型別不明或機制生效 ⇒ 不是 `"true"`;`"false"` / `"unknown"` 都沒有退紅權與 orphan 權;不得以「沒有 deselected」推論完整。

### A. 選項清單法

producer 在 `pytest_sessionfinish` 記下 P1 中所有會影響完整性的選項值:
`lf`、`last_failed_no_failures`、`stepwise`、`stepwise_skip`、`maxfail`、`collectonly`、`setuponly`、`setupplan`、`keyword`、`markexpr`、`deselect`、`ignore`、`ignore_glob`、`failedfirst`、`newfirst`(後兩者只用來記錄,不影響判定)。
另外記 `pluginmanager.is_blocked("cacheprovider")`。任一 narrowing / early-stop / NX 選項開著,或缺欄 ⇒ 不是 `"true"`。

- **擋得住**:#1–#3(本來就有通知)、#4 / #5(本來就安全)、#6 / #6' / #6''、#7、#10 / #11、#12 / #13、#14–#16。
- **擋不住**:#19 `pytest.exit(returncode=0)`(沒有任何選項)、#21 未知 plugin 的縮小或跳過。#18 KeyboardInterrupt 本來就是 D。
- **未知 plugin**:A 本身完全看不到。
- **固定全套指令**:所有選項都是預設值 ⇒ 可以 `"true"`。
- **代價**:
  - `-p no:cacheprovider` 時 `lf` / `stepwise` 屬性不存在 ⇒ 依「缺欄 ⇒ 不是 true」會變成 unknown。要不要用 `is_blocked("cacheprovider")` 當作「這些機制不可能作用」的正向事實,待裁。
  - 選項清單要跟著 pytest 版本維護。

### B. 執行事實法

producer 記下執行當下的事實:
- `session.shouldfail` / `session.shouldstop`(`_pytest/main.py:643-676`)是否被設;
- exitstatus;
- **每一個 selected 身分是否都有終局 outcome**(passed / failed / skipped / other);
- (可選)P2(d) 的 trylast `pytest_make_collect_report` 快照:縮小前每個檔的身分全集。

- ⚠ **只要求「所有 selected 都有 call outcome」擋不住 `--lf`** —— `--lf` 在 producer 看到 selected 之前就移除了身分,這個條件仍然成立。
- **selection completeness 的正向證據從哪裡來**:
  - 內建 `--lf`:比對 trylast 快照的「縮小前全集」與 collected(selected + deselected)。快照裡有、collected 裡沒有 ⇒ silent narrowing ⇒ 不是 `"true"`。
  - 未知 plugin:P2(d) 已證明**不能**觀察縮小前全集 ⇒ B 只能依賴「沒有任何 silent-narrowing 機制 active」的正向 provenance,否則一律 `"unknown"`。
- **擋得住**:#6(靠快照)、#10–#13、#18(本來就是 D)、**#19**(靠「每個 selected 都有 outcome」)、#14–#16(靠同一條)、#21 中「執行期只跑子集」的那一類。
- **擋不住**:#21 中「收集期在 collect report 之前移除」的那一類;#7 的 `none`(本來就有通知)不受影響。
- **未知 plugin**:只能部分擋住。
- **固定全套指令**:完整收集、全部有 outcome、沒有 shouldstop / shouldfail ⇒ 可以 `"true"`。
- **代價**:快照時點依賴 pluggy 的 hook 順序,沒有實測;anyio 那種擴增會讓「selected 身分」與「outcome 身分」的對應更複雜(P1 #20)。

### C. A 與 B 合用(可再加 provenance 檢查)

- A 擋「已知選項」,B 擋「已知選項以外的執行期縮小 / 停止」。快照可以當第二道,但不單獨依賴。
- **未知 plugin 的 fail-closed 候選**:producer 記下本次實際註冊的 plugin 集合,只要有一個不在已知清單 ⇒ 不是 `"true"`。
  - **在 pytest 9.1.1 讀得到**:`config.pluginmanager.list_plugin_distinfo()` 回傳經 setuptools entry point 載入的 (plugin, dist) 對(`pluggy/_manager.py:422-425`);`list_name_plugin()` 回傳全部 (名稱, plugin)(427-429)。
  - **代價**:
    1. 沒有給名稱就註冊的 plugin,名稱是 `str(id(plugin))`(`pluggy/_manager.py:301-310`),每次都不同,不能直接拿名稱比對清單。要改成依類別:`_pytest` 內建(`_pytest/config/__init__.py:306-348` 的 `builtin_plugins`)、conftest、已知 dist。
    2. pytest 升版加了新的內部 plugin 名稱時,清單要跟著改,否則固定全套會變成 unknown(fail-closed,但會卡住退紅)。
    3. 本機有 anyio(P0),它必須在清單內,固定全套才拿得到 `"true"`。
    4. **conftest 本身也能縮小集合**,而 conftest 不是 dist,這個檢查看不到它(下游 repo 的殘餘風險,只能寫明)。
- **擋得住**:A 與 B 的聯集。
- **擋不住**:conftest 層級的收集期縮小;已知 dist 換了行為。
- **固定全套指令**:可以 `"true"`(前提是清單包含 anyio,以及固定全套時實際註冊的內建名稱)。

### 建議(**待 Jeff 裁**)

**C,provenance 用 `list_plugin_distinfo()` 的 dist 名稱比對已知清單。** 理由:
1. P2(d) 的結論是「無法由 selected / outcomes 單獨證明 selection completeness」。只用 B 的話,silent narrowing 的正向證據最後還是要回到「沒有已知機制 active」,也就是 A 那一份清單。
2. 只用 A 的話擋不住 #19:沒有任何選項,exit 0,卻只跑了部分身分。B 的「每個 selected 都有終局 outcome」正好擋住它。
3. dist 名稱是穩定的(不像 `str(id(...))`),本機目前只有 anyio 一個,維護成本最低。
4. trylast 快照建議當作**附加防線**,不當作判定的唯一依據,因為它的順序推論沒有實測。

## P4 紅燈清單(草案;P3 裁定後才定稿)

**driver 的共同設計**:沿用 `tests/test_status.py` 的 `_chain_conftest` / `_chain_drive` 形狀(`<T>:tests/test_status.py:1456-1500`),全部寫在 tmp root,**不碰真實帳本**。新增:
- fake `config.option`:帶齊 P3-A 的全部選項,預設值與 pytest 相同。
- fake `session.shouldfail` / `shouldstop`。
- fake `config.pluginmanager`:提供 `list_plugin_distinfo()` / `get_plugin()` / `is_blocked()`。
- 「每檔縮小前的完整身分」:用一個 fake File collector 驅動 conftest 的 `pytest_make_collect_report`(若 P3 採快照)。
- 只給 setup report、沒有 call 的身分(表達 #19)。

**表達「收集結果少了身分卻沒有 deselected 通知」的方法**:檔案的縮小前全集給 `[a, b]`(fake collect report 與 `config.option.lf = True`、`get_plugin("lfplugin-collskip")` 非 None),但 `session.items` 只給 `[b]`,而且**不呼叫** `pytest_deselected`。
這些額外事實 `<T>` 一律不讀,所以在 `<T>` 上的結果與現在相同。這也是 behavior-red 判定不依賴 P3 選哪一案的原因。

| ID | 裁決 3 | 預定測試(檔::類::名稱) | 情境(輸入事實) | 預期結果 | 分類 | `<T>` 上失敗的原因 |
|---|---|---|---|---|---|---|
| C3a-1 | (a) | `tests/test_redlight.py::TestCompletenessCoverage::test_c3a_lf_silent_narrowing_is_not_full_coverage` | args `["tests"]`;`option.lf = True`;縮小前全集 `[X_A, X_B]`;selected `[X_B]`;沒有 deselected;X_B passed | `file_coverage(run, "tests/test_x.py") != "true"` | behavior-red | `<T>:.claude/hooks/redlight.py:405-406`(只看 deselected)、`423-426`(上層目錄 ⇒ `"true"`) |
| C3a-2 | (a) | `tests/test_status.py::TestSilentNarrowingChain::test_c3a_lf_narrowing_does_not_retire_an_unidentified_red` | 既有整檔紅(`record_run` 的 `failed_tests=[]`);一次如 C3a-1 的 run | 仍紅、不在 green | behavior-red | 同上 + `<T>:.claude/portable/status.py:470-472`(整檔紅只看本 run 收集到的身分)、`475` |
| C3a-3 | (a)(21.2 附註 2) | `tests/test_status.py::TestSilentNarrowingChain::test_c3a_lf_narrowing_does_not_make_a_clean_file_green` | 該檔先前沒有紅;一次如 C3a-1 的 run | 不在 green | behavior-red | `<T>:.claude/portable/status.py:456`(coverage `"true"`)⇒ `475`(`green_now = True`) |
| C3b-1 | (b) | `tests/test_redlight.py::TestCompletenessCoverage::test_c3b_a_session_without_completeness_facts_is_not_full_coverage` | 直接 `record_session`,invocation 正好是 `<T>` 目前寫出的形狀 `{"args": ["tests"], "args_source": "TESTPATHS", "pyargs": false}`,**沒有任何完整性事實**;全收集、全 passed | `!= "true"` | behavior-red | `<T>:.claude/hooks/redlight.py:407-426`(不讀任何完整性事實) |
| C3b-2 | (b) | `tests/test_redlight.py::TestCompletenessCoverage::test_c3b_a_malformed_completeness_fact_is_not_full_coverage` | 同 C3b-1,但完整性事實存在、型別錯(例:字串而不是 bool / dict) | `!= "true"`(建議:schema 不合格 ⇒ `"unknown"`) | behavior-red | `<T>:.claude/hooks/redlight.py:335-343`(不驗新欄位)、`407-426` |
| C3c-1 | (c) | `tests/test_redlight.py::TestCompletenessCoverage::test_c3c_an_exitfirst_run_is_not_full_coverage` | `option.maxfail = 1`;`session.shouldfail` 已設;W 失敗、X 全收集、沒有 outcome;exit 1 | X 的 coverage `!= "true"` | behavior-red | `<T>:.claude/hooks/redlight.py:423-426`(不讀 maxfail / shouldfail) |
| C3c-2 | (c) | `tests/test_status.py::TestEarlyStopChain::test_c3c_exitfirst_does_not_orphan_a_known_red` | X 有已知紅 `test_old`;一次如 C3c-1 的 run,X 收集 `[test_new, test_keep]` | X 仍紅、不在 orphaned | behavior-red | `<T>:.claude/portable/status.py:456`(coverage `"true"`)⇒ `464-468`(移入 orphan) |
| C3c-3 | (c) | `tests/test_status.py::TestEarlyStopChain::test_c3c_exitfirst_does_not_make_unrun_files_green` | 如 C3c-1;X 先前 green 或沒有紀錄 | X 不在 green | regression-lock | —(`<T>:.claude/portable/status.py:475` 沒有 passed ⇒ 不 green) |
| C3c-4 | (c) | `tests/test_status.py::TestEarlyStopChain::test_c3c_stepwise_stop_is_d_and_retires_nothing` | `option.stepwise = True`;`session.shouldstop` 已設;exit 2;X 已知紅、本次 passed | 仍紅、不在 green、不在 orphaned | regression-lock | —(exit 2 ⇒ D,`<T>:.claude/portable/status.py:456-458`) |
| C3c-5 | (c) | `tests/test_status.py::TestEarlyStopChain::test_c3c_pytest_exit_zero_partial_file_is_not_green` | exit 0;X selected `[a, b, c]`;a passed、b 只有 setup passed(沒有 call)、c 沒有任何 report;沒有 shouldstop / shouldfail | X 不在 green | behavior-red | `<T>:.claude/portable/status.py:475`(`"passed" in results`)。⚠ **只有 P3-B 或 P3-C 擋得住**;若裁 A,這支在 4c 後仍會紅,要嘛拿掉,要嘛 A 不完整 |
| C3d-1 | (d) | `tests/test_redlight.py::TestCompletenessCoverage::test_c3d_the_fixed_command_with_everything_off_is_full_coverage` | args `["tests"]`、`args_source` TESTPATHS;所有選項為預設值;沒有 shouldstop / shouldfail;縮小前全集 = selected;全部有 outcome;plugin dist 只有已知清單 | `== "true"` | regression-lock | —(`<T>` 已判 `"true"`) |
| C3d-2 | (d) | `tests/test_status.py::TestCompletenessLocks::test_c3d_the_fixed_command_full_run_still_retires_the_red` | X 已知紅;一次如 C3d-1 的 run,X passed | X 退紅、在 green | regression-lock | — |
| C3e-1 | (e) | `tests/test_status.py::TestLfFalseGreenChain::test_c3e_full_then_lf_does_not_produce_a_false_green` | R1:X 收集錯誤(`collect_errors=["tests/test_x.py"]`)⇒ 整檔紅。R2:全套,a passed、b failed ⇒ red = {整檔, b}。R3:`option.lf = True`、縮小前全集 `[a, b]`、selected `[b]`、沒有 deselected、b passed、exit 0 | X 仍紅、不在 green | behavior-red | 同 C3a-2 |
| C3x-1 | P2(a) | `tests/test_status.py::TestEarlyStopChain::test_setup_only_run_is_not_green` | `option.setuponly = True`;每個身分只有 setup / teardown passed;exit 0 | 不在 green | regression-lock | —(不是新發現;`<T>:tests/conftest.py:198-199` 只從 call 取 passed) |
| C3p-1 | P3-C(**待裁**) | `tests/test_redlight.py::TestCompletenessCoverage::test_c3p_an_unknown_plugin_dist_means_not_full_coverage` | 如 C3d-1,但 `list_plugin_distinfo()` 多一個不在清單的 dist | `!= "true"` | behavior-red(**僅在 P3 採 provenance 時納入**) | `<T>:.claude/hooks/redlight.py:407-426`(不讀 plugin) |

### 受影響的既有測試(需要 Jeff 授權,比照〈十七〉裁決 5)

21.3 裁決 2 的「缺欄 ⇒ 不是 true」會讓下面這些**目前預期 `"true"`、green 或 orphan**的既有測試在 4c 後失敗。
原因是它們的 fake / fixture 沒有新的完整性事實(`_Option` 只有 `pyargs`,`<T>:tests/test_redlight.py:436-437`;`record_session` 直接寫的 invocation 只有 `args`):

| nodeid | 依賴 |
|---|---|
| `tests/test_redlight.py::TestFileCoverage::test_b1c_a_file_argument_without_deselection_is_full_coverage` | `== "true"`(`<T>:tests/test_redlight.py:530`) |
| `tests/test_redlight.py::TestFileCoverage::test_b1d_a_parent_directory_argument_is_full_coverage` | `== "true"`(538) |
| `tests/test_redlight.py::TestFixedCommandCoverage::test_b10_the_fixed_command_without_positional_args_is_full_coverage` | `== "true"`(632) |
| `tests/test_status.py::TestTestsUnderTicketUsesTheLatestRecordPerFile::test_a_file_that_went_red_then_green_counts_as_green` | green(`<T>:tests/test_status.py:574-584`) |
| `tests/test_status.py::TestOrphans::test_a_renamed_red_test_is_orphaned_not_green` | orphan(1328-1336) |
| `tests/test_status.py::TestChainRegressionLocks::test_l3_a_full_directory_run_retires_the_red` | green(1700-1703) |

待裁:是否授權 4c **只在這六支的 fake / fixture 補上「全部關閉」的完整性事實**,assertion、docstring、test identity 一律不改。
不授權的話,4c 只能讓它們變紅,或放寬「缺欄 ⇒ 不是 true」,而後者違反裁決 2。

### 預期集合(草案)

- **預期紅集合(behavior-red)**:C3a-1、C3a-2、C3a-3、C3b-1、C3b-2、C3c-1、C3c-2、C3c-5、C3e-1,共 **9** 支;C3p-1 視 P3 而定(納入則 **10** 支)。
- **預期綠集合(regression-lock)**:C3c-3、C3c-4、C3d-1、C3d-2、C3x-1,共 **5** 支。
- 上一節的六支既有測試在 3c 的紅燈 commit 上仍應該通過(3c 不改產品碼)。它們只在 4c 受影響。

## P5 尚未證明 / 本輪未做

1. **沒有執行任何 pytest**,也沒有寫 probe。P1 的 exit code、run_state、P2(b)(c)(d) 全部是讀 `_pytest` / `pluggy` / `anyio` 原始碼推得。
2. **P2(d)「trylast wrapper 能看到縮小前全集」未實測。** 它依賴三件事:pluggy 1.6.0 的排序(`pluggy/_hooks.py:403-408, 451-473`)、conftest 的 `pytest_make_collect_report` 會經 FSHookProxy 套用到 tests/ 底下的 File collector、LF wrapper 沒有 trylast。
   撰寫過程中,我一度把「同為 trylast 時誰在內層」寫反(先寫成第三方較內層)。讀 `pluggy/_hooks.py:464-465`(trylast 插在區段最前面)後更正,P2(d) 現在的寫法是更正後的版本;結論(未知 plugin 不成立)不受影響。
3. **plugin inventory 未完整證明**(P0):只搜了系統 site-packages 的 `[pytest11]`,沒有盤點 `-p`、`PYTEST_PLUGINS`、conftest `pytest_plugins` 以外的動態註冊;`list_plugin_distinfo()` 在本機實際回傳什麼沒有觀察。
4. anyio 的 `pytest_collection_finish` 擴增會不會讓 session 被判 INVALID(P1 #20)只是推論;本 repo 有沒有符合條件的 async 測試沒有查。
5. `-p no:cacheprovider` 時「缺欄」的處置(A 的代價)待裁。
6. 21.2 附註 1 指出審查報告的 R2(只跑 nodeid)路徑在真實執行中不重現;本規劃的 C3e-1 依 21.2 的「全套 → `--lf`」路徑設計,沒有使用那條路徑。
7. P4 的測試名稱、類別名、driver 介面都是草案,P3 裁定後才定稿;behavior-red / regression-lock 的分類是依 `<T>` 程式碼紙上推演,要等 3c 實際寫完、在乾淨 HEAD 上跑一次才驗收(預期紅集合 = 實際失敗集合)。
8. 8 欄紀錄在 `--setup-only` 下會寫 green(P2(a) 附帶)。R3 讀到它的行為沒有查。
