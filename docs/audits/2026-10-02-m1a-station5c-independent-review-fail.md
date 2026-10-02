# 票 145(M1-a)Station 5c 獨立審查報告

- 審查對象(TARGET):`02a5e28adf5aee11a43d5a1063504f01beb1d67f`
- 審查包:`587c1ed63a07d90dc33f3e247f4d1ebed01c91bf:docs/audits/2026-10-02-m1a-station5c-review-package.md`
- 審查方式:只讀 Git 物件(全部綁完整 SHA)與本機已安裝的 pytest 9.1.1 / pluggy 原始碼;**未執行任何 pytest**。
- 以下 `<TARGET>` 一律代表 `02a5e28adf5aee11a43d5a1063504f01beb1d67f`。

---

## 1. 判決

**FAIL**

- 阻擋發現:1(S5c-F1)
- 非阻擋發現:3(S5c-F2、S5c-F3、S5c-F4)

S5c-F1 一句話:pytest 在 `Module.collect()` / `Class.collect()` **之內**依 `python_functions` / `python_classes` 篩選身分,而這兩個值可以每次執行用 `-o` 改掉。producer 的縮小前快照(`pre_narrowing`)取在 collect report **之後**,所以看不到這種縮小。completeness 也沒有記 `override_ini`。結果是〈二十三〉7 的 (i)–(vii) 全部成立、`file_coverage == "true"`,於是只跑了部分身分的 run 被拿來退掉身分不明的整檔紅,後果與 S5b-F1 相同。

---

## 2. 身分核對結果(原始輸出)

```
$ git rev-parse 587c1ed63a07d90dc33f3e247f4d1ebed01c91bf:docs/audits/2026-10-02-m1a-station5c-review-package.md
d37e0538798ae763d86716542becf3430d7a73c5
exit=0
```
等於指定值 `d37e0538798ae763d86716542becf3430d7a73c5` ✓

```
$ git diff --name-only 02a5e28adf5aee11a43d5a1063504f01beb1d67f..587c1ed63a07d90dc33f3e247f4d1ebed01c91bf
docs/audits/2026-10-02-m1a-station4c-fix.md
docs/audits/2026-10-02-m1a-station5c-review-package.md
docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
exit=0
```
只有 `docs/` 底下 3 個檔(4c 報告、5c 審查包、票 145)✓

---

## 3. G1–G12 逐題回答

### G1. S5b-F1(`--lf` 收集期靜默縮小)是否已修好? —— **成立(已修好)**

依 pytest 9.1.1 hook 順序推演〈二十一〉21.2 的三步情境(`tests/test_x.py` 含模組層 `test_a`、`test_b`):

1. **R1(全套,實作不存在)**:收集錯誤。`<TARGET>:tests/conftest.py:157-164` 記 8 欄 red(`<collection error>`)和 `collect_errors`。`<TARGET>:.claude/portable/status.py:396-403` 把它解讀成整檔紅 `tests/test_x.py::*`。run_state 判 D(`<TARGET>:.claude/hooks/redlight.py:379-380`)。
2. **R2(全套)**:test_a passed、test_b failed ⇒ B。`<TARGET>:.claude/portable/status.py:449-455` 加紅 test_b,並保留整檔紅。
3. **R3(`python -X utf8 -m pytest -q --lf`)**:
   - 只有 `lf` 為真時 `LFPlugin` 才註冊 `LFPluginCollWrapper`(`_pytest/cacheprovider.py:326-330`)。它是**普通優先序**的 new-style wrapper(`_pytest/cacheprovider.py:248`),在 File 層**就地**縮小 `res.result`(`_pytest/cacheprovider.py:267-290`)。
   - conftest 的 wrapper 標 `trylast`(`<TARGET>:tests/conftest.py:294`)。pluggy 把 trylast wrapper 插在 wrapper 區段最前面(`pluggy/_hooks.py:459-465`),呼叫時反向走(`pluggy/_callers.py:93`),所以 conftest 的 wrapper 是**最內層**。yield 之後的段落也反向執行(`pluggy/_callers.py:135`),所以 conftest 會**先於** LF wrapper 拿到完整結果。它在當下複製 nodeid(`<TARGET>:tests/conftest.py:299-302`)⇒ `pre_narrowing["tests/test_x.py"] = [test_a, test_b]`。
   - 縮小後 `session.items = [test_b]` ⇒ `collected = [test_b]`、`deselected = []`;`options.lf = True`、`cacheprovider_blocked = False`。
   - `file_coverage`:位置參數 `tests` 涵蓋 ⇒ 進入 `_completeness_verdict`(`<TARGET>:.claude/hooks/redlight.py:436-439`)。接著在 `<TARGET>:.claude/hooks/redlight.py:579-582` 判 `"false"`。就算這一條不存在,`<TARGET>:.claude/hooks/redlight.py:590-592` 也會因 {test_a, test_b} ≠ {test_b} 判 `"false"`。
   - `_apply_run`:`<TARGET>:.claude/portable/status.py:456-458` ⇒ `green_now = False`,不退紅、不 orphan。
4. **結果**:`tests/test_x.py` 仍在 red(整檔紅 + test_b),不在 green ✓。21.2 附註 2(先前沒有紅的檔)走同一條路判 `"false"` ⇒ 不 green ✓。
5. 對應測試:`<TARGET>:tests/test_status.py:2156-2183`(C3e-1,每次執行用新的 conftest);`<TARGET>:tests/test_status.py:2045-2071`(C3a-2 / C3a-3)。

**但**:「靜默縮小 ⇒ 不得為 true」這一族**沒有**完全關閉,見 S5c-F1(另一個機制,後果相同)。

### G2. 〈二十三〉7 (i)–(vii) 的強制行 —— **七條都有強制行;沒有找到任何繞過某一條而得 `"true"` 的輸入。但七條合起來不足以排除 S5c-F1**

`file_coverage` 唯一的 `"true"` 出口是 `<TARGET>:.claude/hooks/redlight.py:597`,只能經由 `<TARGET>:.claude/hooks/redlight.py:438-439` 到達。舊的 `return "true"` 已移除(`git diff 851cbd75b359a6b2a34452265e8a70992fa56996..02a5e28adf5aee11a43d5a1063504f01beb1d67f -- .claude/hooks/redlight.py` 的刪除行只有簽名、docstring、`OUTCOME_VALUES` 和 `return "true"`)。

| 條 | 強制行 | 說明 |
|---|---|---|
| (i) | `<TARGET>:.claude/hooks/redlight.py:574-575`;`:539-559` | 缺欄或型別錯 ⇒ unknown。`validate_session` 只要求 completeness 是 dict(`:352-354`),細項由 `_completeness_problems` 驗 |
| (ii) | `<TARGET>:.claude/hooks/redlight.py:579-582` | `lf` / `stepwise` / `stepwise_skip` 必須 `is False`,除非 `cacheprovider_blocked is True` |
| (iii) | `<TARGET>:.claude/hooks/redlight.py:583-587` | maxfail 必須是 None 或 int 0;collectonly / setuponly / setupplan 必須 `is False` |
| (iv) | `<TARGET>:.claude/hooks/redlight.py:588-589` | shouldstop / shouldfail 必須 `is False` |
| (v) | `<TARGET>:.claude/hooks/redlight.py:590-592` | `set(pre) != set(idents)` ⇒ false |
| (vi) | `<TARGET>:.claude/hooks/redlight.py:593-596`;`:469` | selected 身分的 outcome 必須屬於 `EXECUTED_OUTCOMES`(不含 `other`) |
| (vii) | `<TARGET>:.claude/hooks/redlight.py:576-577` | 任一 kind 不在 `SUPPORTED_PLUGIN_KINDS` ⇒ unknown |

- (ii) 可以被跳過但沒有造成假綠:見 S5c-F3(非阻擋)。
- S5c-F1 不是繞過某一條,而是 (i)–(vii) 都**沒涵蓋**的縮小機制。

### G3. 執行完整性 —— **成立**

- `pytest.exit(returncode=0)`:`Exit` 屬於 reraise 清單(`_pytest/runner.py:262-267`),在 `pytest_runtest_makereport` 之前就丟出(`_pytest/runner.py:249-256`)⇒ 中斷的那一個 phase 沒有 report。call 中斷 ⇒ 只有 setup passed,`_run_outcome` 回 None(`<TARGET>:tests/conftest.py:198-203`)⇒ 沒有 outcome ⇒ `<TARGET>:.claude/hooks/redlight.py:595` 判 unknown。之後沒跑到的身分也沒有 outcome,同樣判 unknown。對應測試:`<TARGET>:tests/test_status.py:2124-2137`。
- `--setup-only`:不呼叫 call(`_pytest/runner.py:134-139`)⇒ setup / teardown passed 都回 None ⇒ (vi) 判 unknown。另外 `<TARGET>:.claude/hooks/redlight.py:586-587` 也擋。
- 只有 setup 沒有 call:同上,(vi) 判 unknown。
- xfail:skipped + `wasxfail` ⇒ `"xfail"`(`<TARGET>:tests/conftest.py:197-200`)。non-strict xpass:call passed + `wasxfail` ⇒ `"xpass"`(`:201-202`)。strict xpass:report failed ⇒ `"failed"`(`:192-193`)。
- 籠統的 `other`:新 producer 不再產生(`<TARGET>:tests/conftest.py:192-203` 沒有任何 `"other"` 回傳)。`EXECUTED_OUTCOMES` 不含 `other`(`<TARGET>:.claude/hooks/redlight.py:469`)⇒ 舊 session 的 `other` 一律判 unknown。**`other` 拿不到 completeness。**

### G4. plugin 邊界 —— **成立;另有一個非阻擋的冒充路徑(S5c-F4)**

- **來源**:分類直接吃 `pm.list_name_plugin()` 和 `pm.list_plugin_distinfo()` 的原始回傳(`<TARGET>:tests/conftest.py:337-338` → `<TARGET>:.claude/hooks/redlight.py:504-532`)✓
- **known_dist 以物件同一性判定**:`[dn for p, dn in dists if p is plugin]`(`<TARGET>:.claude/hooks/redlight.py:521`)✓
  - 用 `-p` 載入一個名叫 `anyio` 的自訂模組:pytest 會先找 entry point(`_pytest/config/__init__.py:906-909`)。找得到 ⇒ 載入的是真的 dist,合法。找不到 ⇒ 改 import 模組並以 `register(mod, modname)` 註冊(`_pytest/config/__init__.py:911-927`),該物件不在 distinfo 配對裡 ⇒ 走 builtin 判定,`__name__ == "anyio"` ⇒ `other`(`<TARGET>:.claude/hooks/redlight.py:526-530`)✓
- **builtin 前綴冒充**:判定式是 `mod == "_pytest" or mod.startswith("_pytest.")`(`<TARGET>:.claude/hooks/redlight.py:528-529`),有點號邊界 ⇒ `_pytest_evil` **不會**被判 builtin ✓。
  - 但模組在 import 時自己把 `__name__` 改成 `_pytest.x`,就會被判 builtin:見 S5c-F4(非阻擋;實作照合約字面「模組物件看 `__name__`」)。
- **路徑型名稱**:`os.path.isabs(name)` ⇒ `_plugin_path_name` 轉成 root 相對 posix 路徑,root 以外或跨磁碟記 `<outside>`(`<TARGET>:.claude/hooks/redlight.py:492-501, 519-520`)✓。測試 `<TARGET>:tests/test_status.py:2277-2280` 斷言帳本不含 tmp root 的三種寫法。

### G5. pre_narrowing 多層 collector 累積 —— **累積本身:成立(未找到漏記或錯記);但這張快照取的位置有一個假陽性路徑,見 S5c-F1**

- **每個 collector 都經過 conftest 的 wrapper**:`Session.genitems` 對 `rep.result` 裡的每個子 collector 遞迴呼叫 `_collect_one_node` → `collect_one_node` → `collector.ihook.pytest_make_collect_report`(`_pytest/main.py:1023-1037`、`:886-897`;`_pytest/runner.py:586-589`)。子 collector(Class)是在 LF 過濾之後,從 `rep.result` 走到的,而 LF 過濾**保留所有子 collector**(`_pytest/cacheprovider.py:288-289`)。
- **重複**:`handle_dupes = not isinstance(node, File)`(`_pytest/main.py:1031`),同一個 File 可能被收集兩次 ⇒ list 裡出現重複的 nodeid。比對用 `set(pre) != set(idents)`(`<TARGET>:.claude/hooks/redlight.py:591`),不受重複影響 ✓
- **巢狀 class**:外層 Class 的 report 裡,內層是 Class(collector),`isinstance(node, pytest.Item)` 為假,所以不記(`<TARGET>:tests/conftest.py:300`)。內層 Class 自己的 report 裡有它的 Function,會被記到。key 取 nodeid 的 `::` 前段(`:302`)⇒ 全部歸到同一個測試檔 ✓
- **parametrize**:每個參數一個 Function item,出現在 Module 或 Class 的 report 裡 ✓
- **unittest TestCase**:TestCase 的 collector 是 Class 的子類,它的 report 裡是 TestCaseFunction item,同一條路徑。本 repo 在 TARGET 沒有 TestCase 測試(`git grep -n -E "unittest\.TestCase|\(TestCase\)" <TARGET> -- tests/`:0 筆)。
- **hook 順序 / `--lf` 的縮小是否發生在快照之後**:是。LF wrapper 是普通優先序(`_pytest/cacheprovider.py:248`),conftest 是 trylast(`<TARGET>:tests/conftest.py:294`)⇒ conftest 在最內層,yield 之後最先執行(推演見 G1)✓
- **`LFPluginCollSkipfiles`**:對不在 lastfailed 路徑裡的 File,它直接回一份 `result=[]` 的 report(`_pytest/cacheprovider.py:299-309`)⇒ 這個檔沒有 pre 項目,也沒有 collected 身分 ⇒ `<TARGET>:.claude/hooks/redlight.py:416-417` 判 unknown ✓
- **新的假陽性路徑**:有。快照取在「collect report 之後」,所以在 `collect()` **之內**就被移除的身分,不會出現在快照、也不會出現在 collected,兩邊同樣少 ⇒ (v) 成立。pytest 內建的 `python_functions` / `python_classes` 篩選正是這種縮小,而且可以每次執行用 `-o` 改掉 ⇒ **S5c-F1**。
- 只有真實固定全套佐證、沒有 driver 測試覆蓋 Class 子 collector 的累積:這是 H.1 第 4 項的已知事項,不重複列為發現。

### G6. producer 失敗安全 —— **新增的部分成立;S5b-F5 指出的區段原樣不變**

- wrapper 的 yield 之後整段包在 try 裡;出錯 ⇒ `_pre_narrowing_broken`(`<TARGET>:tests/conftest.py:297-304`)⇒ `_completeness_of` 回 None(`:325-326`)⇒ (i) 判 unknown。yield 本身不在 try 裡,所以內層丟出的例外照常往外傳,不會被吞掉 ✓。最後 `return report`(`:305`)✓
- `_completeness_of` 整段包在 try 裡,任何例外 ⇒ None(`<TARGET>:tests/conftest.py:324-341`)✓。`_flag` 遇到缺屬性回 None ⇒ 型別錯 ⇒ unknown(`:315-319`)✓。選項值經 `_plain` 轉成 JSON 原生型別(`:308-312`)⇒ 寫入時的 `json.dumps` 不會因 completeness 失敗。
- 8 欄紀錄不受影響:`record_run` 的迴圈原樣不動(`<TARGET>:tests/conftest.py:228-229`);逐檔的 `_outcomes` 原樣(`:214-217`)✓
- S5b-F5 的「try 之外」區段**照舊**:`<TARGET>:tests/conftest.py:246-249`(`inspect.signature`、`_invocation_of` 不在 try 裡);`<TARGET>:.claude/hooks/redlight.py:239-250`(組 rec 不在 try 裡)。4c 在 rec 裡加的是 `completeness if isinstance(completeness, dict) else None`(`:249`),不會丟例外。S5b-F5 是已知的非阻擋項(H.2),不重複列。

### G7. 提前停止 —— **成立**

- `-x` / `--maxfail=N`:`maxfail` 不是 None 也不是 0 ⇒ unknown(`<TARGET>:.claude/hooks/redlight.py:583-585`);停下時 shouldfail ⇒ unknown(`:588-589`);沒跑到的身分沒有 outcome ⇒ unknown(`:595`)。這種 run 是 exit 1 ⇒ B,所以靠 `<TARGET>:.claude/portable/status.py:456-458` 的 coverage 判定擋下。對應測試:`<TARGET>:tests/test_status.py:2076-2102`。
- `--sw`:`stepwise` 為真 ⇒ `"false"`(`<TARGET>:.claude/hooks/redlight.py:579-582`)。失敗時設 shouldstop(`_pytest/stepwise.py:187`)⇒ Interrupted ⇒ exit 2 ⇒ D ⇒ `<TARGET>:.claude/portable/status.py:456`。對應測試:`<TARGET>:tests/test_status.py:2104-2122`。
- KeyboardInterrupt:屬於 reraise 清單(`_pytest/runner.py:264-266`)⇒ exit 2 ⇒ D ⇒ 不退紅、不 orphan、不 green。orphan 和 green 的段落都在 `<TARGET>:.claude/portable/status.py:456-458` 之後(`:459-475`)。加了 `--pdb` 時 KeyboardInterrupt 不重拋、會變成 failed report ⇒ 加紅,這個方向是 fail-closed。

### G8. 向下相容 —— **成立**

- 沒有 completeness 的舊 session:`validate_session` 照樣判合格(`<TARGET>:.claude/hooks/redlight.py:352-354`)⇒ `file_coverage` 在 `:574-575` 判 unknown ⇒ 能加紅,不能退紅、不能 green ✓
- 只有 8 欄紀錄:red 只加不退,green 只會變 `unknown`(`<TARGET>:.claude/portable/status.py:510-515`)✓
- 新 status 配舊 redlight:`_rl_ready` 檢查三個函式在不在(`<TARGET>:.claude/portable/status.py:406-411`);缺函式 ⇒ `:456` 不退紅。status.py 在 4c 沒改(`git diff --stat 851cbd75…..02a5e28a…` 只列出 redlight.py 和 conftest.py)。
- 新 conftest 配舊(4b)redlight:舊版 `record_session` 沒有 `completeness` 參數 ⇒ conftest 不傳(`<TARGET>:tests/conftest.py:251-252`)。但新 conftest 會寫 `"xfail"` / `"xpass"`,而 4b 的 `OUTCOME_VALUES = ("passed", "failed", "skipped", "other")`(`851cbd75b359a6b2a34452265e8a70992fa56996:.claude/hooks/redlight.py:283`)⇒ 有 xfail 的 run 整筆判 INVALID ⇒ 不產生效果,會計入「schema 不合格 run」。不會丟例外,方向是 fail-closed ✓。沒有 xfail 的 run 會走 4b 的舊判定(S5b-F1 的舊行為)—— 那是舊版本身的問題,不是 4c 的退步。

### G9. 測試沒有被放寬 —— **成立**

- `git diff 49bcde20adc276632fa5bab456e8c7a80839fc0b..02a5e28adf5aee11a43d5a1063504f01beb1d67f -- tests/test_redlight.py tests/test_status.py` 一共 6 個 hunk,分屬 6 支測試:b1c、b1d(`<TARGET>:tests/test_redlight.py:524-554`)、b10(`:631-654`)、570/571(`<TARGET>:tests/test_status.py:575-586`)、ODC-2(`:1336-1350`)、L3(`:1716-1720` 一帶)。
- 這 6 支與 3c 規劃檔「受影響的既有測試」一一相符(`<TARGET>:docs/audits/2026-10-02-m1a-station3c-redlight-plan.md:231-238`)✓
- 每個 hunk 都只動 driver / fake / fixture 那幾行。`assert` 行、docstring、函式名稱一行都沒動 ✓
- 3c 新增的 21 支(`<TARGET>:tests/test_redlight.py:958-1063`;`<TARGET>:tests/test_status.py:2043-2298`)不在 diff 裡 ✓
- 附記(不列發現):b1c / b1d 把原本的 `self._coverage_after(...)` 換成明確的 wrapper + session 建構,L3 把 `_chain_drive` 換成 `_s_drive`。這是**整段換掉 driver**,不只是「補上事實」;不過換上去的都是「全部關閉、白名單內」的事實,斷言與預期值都沒變,所以仍在〈二十三〉5 授權的範圍內。

### G10. 測試 driver 是否忠實模擬 pytest —— **大致成立;有一個非阻擋的覆蓋缺口(S5c-F2)**

- **模組狀態殘留**:`_conftest()` 每次都 `exec_module` 一個新模組(`<TARGET>:tests/test_redlight.py:177-182`);`_chain_conftest` 也一樣(`<TARGET>:tests/test_status.py:1475-1481`)⇒ 每支測試各自拿到全新的 `_pre_narrowing`。`_reset_conftest_state` 不清 `_pre_narrowing`(`<TARGET>:tests/test_redlight.py:458-467`),但同一支測試裡驅動多次的只有 C3e-1,而它每次都用新的 conftest(`<TARGET>:tests/test_status.py:2168-2174`)✓。沒有找到 C3e-1 那一型的殘留。
- **wrapper 協定**:`next(gen)` → `gen.send(report)` → 接 StopIteration(`<TARGET>:tests/test_redlight.py:864-876`;`<TARGET>:tests/test_status.py:1967-1978`),與 pluggy 的 `teardown.send(result)` 一致(`pluggy/_callers.py:135-152`)✓
- **縮小時點**:wrapper 返回後才就地縮小(`<TARGET>:tests/test_redlight.py:894`;`<TARGET>:tests/test_status.py:1994`),與 G1 推得的真實順序一致 ✓
- **假物件型別**:item / file 是 `pytest.Item` / `pytest.File` 的子類,所以 `isinstance` 判斷成立(`<TARGET>:tests/test_redlight.py:680-706`)✓
- **可能「為了錯的理由通過」**:斷言 `!= "true"` 的測試,每一支都**同時**觸發兩個以上的條件,所以 (ii)、(iii) 的 maxfail、(iv) 三條都**沒有單獨被鎖住**:刪掉其中任何一條,全部測試仍會通過。見 S5c-F2。
- driver 沒有驅動 Class 子 collector 的 report(H.1 第 4 項,已知事項)。

### G11. 隱私與欄位邊界 —— **成立**

- (1) producer 自己產生的 path-valued metadata:`plugins[].name` 只有 root 相對路徑或 `<outside>`(`<TARGET>:.claude/hooks/redlight.py:492-501, 519-520`)。`options` 的值都是 bool / int / None / 固定字串,經 `_plain` 處理(`<TARGET>:tests/conftest.py:308-312`)。`invocation_dir` 不落帳(`<TARGET>:.claude/hooks/redlight.py:213-217`)✓
- (2) 測試身分:`pre_narrowing` 和 `collected` 都經過同一個 `_nodeid`(`<TARGET>:tests/conftest.py:146-147, 182, 301`),所以兩邊逐字相等、可以比對。`\`→`/` 的替換是 Station 4 就有的既有行為(`<TARGET>:.claude/hooks/redlight.py:245-247`),不是 4c 新加的改寫 ✓
- (3) `invocation.args`:`_normalize_invocation` / `_normalize_arg` 在 4c 沒改(E.2 的刪除行不含它們)✓

### G12. 既往修正未退步 —— **成立**

- F1(缺欄的 session):`validate_session` 原有的檢查都在(`<TARGET>:.claude/hooks/redlight.py:304-351`),4c 只加了 `xfail`/`xpass` 兩個值和 completeness 的型別檢查;status 的 `<TARGET>:.claude/portable/status.py:429-437` 沒動 ✓
- F2(D 狀態的 run):`<TARGET>:.claude/portable/status.py:456` ✓
- F3(以 nodeid 指名):`<TARGET>:.claude/hooks/redlight.py:431-433, 440-441` 判 `"false"`;(v) 也會判 false ✓
- F4(沒有串接驗證):串接測試都在(`<TARGET>:tests/test_status.py:1541` 起的 `TestCoverageChain`,以及 3c 的 `:2043-2298`)✓
- S5b-F1:見 G1 ✓。S5b-F2–F6 原樣不變(已知非阻擋,H.2)。
- `git diff 851cbd75b359a6b2a34452265e8a70992fa56996..02a5e28adf5aee11a43d5a1063504f01beb1d67f` 在 conftest.py 只刪了 3 行(兩行 `"other"` 回傳,換成 xfail/xpass;一行簽名判斷,改寫成 `params`),在 redlight.py 只刪了簽名、docstring、`OUTCOME_VALUES` 和 `return "true"` ⇒ 既有的判定邏輯沒有被移除。

---

## 4. 發現清單

### S5c-F1【阻擋】`-o python_functions` / `python_classes` 在 `collect()` 之內靜默縮小,completeness 沒有記,`file_coverage` 判 `"true"` ⇒ 整檔紅被局部 run 退成 green

**證據行**
- `<TARGET>:.claude/hooks/redlight.py:457-458` —— `COMPLETENESS_OPTIONS` 只有 lf / last_failed_no_failures / stepwise / stepwise_skip / maxfail / collectonly / setuponly / setupplan,沒有 `override_ini`,也沒有其他能看出收集規則被改過的事實。
- `<TARGET>:tests/conftest.py:294-302` —— 快照取的是 collect report 的 `result`(collect **之後**)。
- `<TARGET>:.claude/hooks/redlight.py:590-592` —— (v) 比的是「快照」和「collected」;這兩者都在 collect 之後才產生,所以 collect 之內的縮小兩邊一樣少。
- `<TARGET>:.claude/hooks/redlight.py:593-597` —— (vi) 只看 selected 身分,被縮掉的身分不在 selected 裡。
- `<TARGET>:.claude/portable/status.py:469-475` —— 整檔紅只要求「本 run 收集到的身分」全部 passed。
- 佐證(本機 pytest 9.1.1 原始碼,不在 TARGET 內):
  - `_pytest/helpconfig.py:113-116`:`-o` / `--override-ini`,`dest="override_ini"`、`action="append"`。
  - `_pytest/config/findpaths.py:338-339`:`ini_overrides = parse_override_ini(override_ini)`;`inicfg.update(ini_overrides)`。
  - `_pytest/config/__init__.py:1532-1539`:`determine_setup(..., override_ini=ns.override_ini, ...)`。
  - `_pytest/python.py:354-355, 366-367, 385-398`:`funcnamefilter` / `classnamefilter` 讀 `getini("python_functions")` / `getini("python_classes")`,做前綴或 glob 比對。
  - `_pytest/python.py:420-441`:不符合的名稱在 `collect()` 裡被丟掉,不產生 item,也不發任何通知。
- 本 repo 的 `[tool.pytest.ini_options]` 沒有設定 `python_functions`(`<TARGET>:pyproject.toml:70-72` 之後只有 markers),所以預設值是前綴 `test`。

**具體情境(紙上推演)**

`tests/test_x.py` 有模組層的 `test_a`、`test_b`。

1. R1(全套):實作還不存在 ⇒ 收集錯誤 ⇒ 整檔紅 `tests/test_x.py::*`(同 G1 第 1 步)。
2. 實作寫好了,但 `test_a` 其實是紅的。R2:從 repo 根執行 `python -X utf8 -m pytest -q -o python_functions=test_b`(或用 `PYTEST_ADDOPTS="-o python_functions=test_b"`)。
   - `config.args == ["tests"]`、`args_source == TESTPATHS`(B.3 的推導)。
   - `Module.collect()` 時,`"test_a".startswith("test_b")` 為假 ⇒ 不產生 item ⇒ report `result = [Function test_b]`。
   - conftest 的 wrapper 記到 `pre_narrowing["tests/test_x.py"] = ["tests/test_x.py::test_b"]`。
   - 沒有 deselected。`session.items` 裡 test_x.py 只有 test_b。test_b passed,exit 0。
   - completeness:options 全部 False / None;`cacheprovider_blocked = False`;shouldstop / shouldfail 為 False;plugins 都是 builtin / root_conftest / known_dist。
3. `file_coverage(run, "tests/test_x.py")`:schema 合格 → idents `[test_b]` → 沒有 deselected → args `tests` 涵蓋 → (i) 型別正確 → (vii) 沒有 other → (ii) lf / stepwise 皆 False → (iii) maxfail None、其他 False → (iv) False → (v) {test_b} == {test_b} → (vi) passed ⇒ **`"true"`**。`run_state` = A。
4. `_apply_run`:沒有 failure;ready、非 D、coverage true;整檔紅 ⇒ `all(passed for idents=[test_b])` 為真 ⇒ `red[f] = set()`;`green_now = True`(`<TARGET>:.claude/portable/status.py:470-475`)。

**錯誤輸出**:`tests green under ticket <N>` 列出 `tests/test_x.py`,`tests red` 不含它。但 test_a 從未被收集或執行,而且實際上是紅的。

**應有輸出**:依 ODC-1 第 1、2 項、〈十七〉裁決 1(不知道,就不是完整)、〈二十一〉21.3 裁決 2(producer 必須**正向記錄**足以證明沒有任何「會縮小實際執行集合」的機制生效)⇒ 應判 `"false"` 或 `"unknown"`,`tests/test_x.py` 應該仍紅。

**同一路徑的其他後果**
- **已知身分的紅**:test_a 是已知紅,R2 照上面跑 ⇒ coverage `"true"`、test_a 不在 present 裡 ⇒ 被移到 **orphan**(`<TARGET>:.claude/portable/status.py:464-468`),違反「不得 orphan」。
- **乾淨的檔**:只跑了部分身分,卻判 green(21.2 附註 2 的同型)。
- **class 型測試也受影響**:`python_functions` 同樣作用在 class 的方法上,`python_classes` 會整個 class 不收集。所以不像 S5b-F1 那樣只影響模組層測試。

**為什麼判「阻擋」**
- 後果與 S5b-F1(上一輪的阻擋)完全相同:身分不明的整檔紅被局部 run 退成 green。
- 〈二十一〉21.3 裁決 2 的要求是「正向記錄足以證明沒有任何縮小機制生效」,並且「不得以『沒有 deselected』推論選擇完整」。現在的事實集合證明不了這一個機制沒有生效。
- 3c 的機制盤點(`<TARGET>:docs/audits/2026-10-02-m1a-station3c-redlight-plan.md` P1 表,第 45-67 行)沒有這一項。該表第 67 行只把「收集期在 collect report 之前的移除」歸給**未知第三方 plugin**,而 plugin 白名單管得到第三方 plugin;這裡的移除是由**白名單內**的 builtin `python` plugin 依每次可改的設定執行的,白名單管不到。

**可能的反方論點(照實列出,由裁決者判斷)**:有人會說「這個檔的測試集合」本來就由設定決定,`python_functions` 改了,集合的定義也跟著改。但 `-o` / `PYTEST_ADDOPTS` 是每次執行都能改的覆寫,與 `-k` 同屬「這一次只跑一部分」,只是不發 deselected 通知,與 `--lf` 同型。

**同族、未逐一推演**(只列名,不計入本發現的證據):`-c` / `--config-file` 指向另一份設定檔、`PYTEST_ADDOPTS`(它只是載具);`-p no:unittest` 讓 TestCase 類別在 collect 時消失(本 repo 在 TARGET 沒有 TestCase,未讀 unittest 那一段原始碼)。

### S5c-F2【非阻擋】(ii)、(iii) 的 maxfail、(iv) 三條都沒有單獨被測試鎖住 —— 刪掉任何一條,全部測試仍會通過

- **證據**:
  - `<TARGET>:tests/test_redlight.py:958-977`(C3a-1);`<TARGET>:tests/test_status.py:2028-2032, 2045-2071, 2156-2183`(C3a-2 / C3a-3 / C3e-1):都同時有 `lf=True` **和** `filtered_out`。
  - `<TARGET>:tests/test_redlight.py:999-1013`(C3c-1);`<TARGET>:tests/test_status.py:2035-2040, 2076-2102`(C3c-2 / C3c-3):都同時有 `maxfail=1`、`shouldfail` **和**「X 沒有 outcome」。
  - `<TARGET>:tests/test_status.py:2104-2122`(C3c-4):`stepwise=True`、`shouldstop`、exit 2(D)。
- **紙上推演**:
  - 刪掉 `<TARGET>:.claude/hooks/redlight.py:579-582`((ii))⇒ C3a 系列由 `:590-592`((v))判 false,仍通過。
  - 刪掉 `:583-585`(maxfail)⇒ C3c-1 / C3c-2 由 `:588-589` 或 `:595` 判 unknown,仍通過。
  - 刪掉 `:588-589`((iv))⇒ C3c 系列由 `:583-585` 判 unknown;C3c-4 由 D 擋下,仍通過。
- **影響**:合約一條一條列出必要條件,但測試只鎖住「結果不是 true」,沒有鎖住「每一條各自生效」。以後任何一條被誤刪或改壞,測試都不會紅。目前的程式碼是對的,所以判非阻擋。

### S5c-F3【非阻擋】(ii) 可以被跳過:`-p no:cacheprovider -p _pytest.cacheprovider` 讓 `cacheprovider_blocked` 為真,但 LF 仍然作用;目前由 (v) 補位,沒有造成假綠

- **證據**:
  - `<TARGET>:.claude/hooks/redlight.py:579`:`cacheprovider_blocked is True` 時整條 (ii) 跳過。
  - `<TARGET>:tests/conftest.py:333`:只問 `is_blocked("cacheprovider")`。
  - `_pytest/config/__init__.py:851-857` 只封鎖名稱 `cacheprovider`、`pytest_cacheprovider`、`stepwise`、`pytest_stepwise`。
  - `:900-903, 911-927`:`-p _pytest.cacheprovider` 的名稱沒有被封鎖 ⇒ import 後以 `register(mod, "_pytest.cacheprovider")` 註冊。
  - `<TARGET>:.claude/hooks/redlight.py:526-530`:模組 `__name__` 是 `_pytest.cacheprovider` ⇒ 判 builtin,沒有 other 可以擋。
- **情境**:`pytest -p no:cacheprovider -p _pytest.cacheprovider --lf` ⇒ `options.lf = True`、`cacheprovider_blocked = True` ⇒ (ii) 跳過。但 File 層的縮小仍發生在快照之後 ⇒ (v) 判 `"false"`。stepwise 的類比情形:stepwise 走 `pytest_deselected`(`_pytest/stepwise.py:172`)⇒ `<TARGET>:.claude/hooks/redlight.py:418-419` 判 false;停下時設 shouldstop(`_pytest/stepwise.py:187`)⇒ (iv) 也會擋。
- **影響**:目前沒有找到假綠;只是防線少了一層。〈二十三〉4 把 `is_blocked("cacheprovider")` 當成「lf / stepwise 不可能作用」的正向事實,這個前提在上面的情境下不成立。

### S5c-F4【非阻擋】builtin 判定可以被冒充:模組在 import 時把自己的 `__name__` 改成 `_pytest.*`,就會被判 builtin

- **證據**:`<TARGET>:.claude/hooks/redlight.py:485-486`(模組物件看 `__name__`);`:526-530`(只比字串)。註冊名稱(`-p` 給的名字)不參與判定。
- **情境**:`-p myplug`,`myplug.py` 第一行寫 `__name__ = "_pytest.myplug"` ⇒ `register(mod, "myplug")` ⇒ 不在 distinfo 配對裡,也不是路徑 ⇒ `_defining_module` 回 `"_pytest.myplug"` ⇒ `kind = "builtin"` ⇒ (vii) 通過。這個 plugin 接著可以實作 `pytest_pycollect_makeitem` 之類的 hook,做 collect 之內的縮小(與 S5c-F1 同一個盲點)。
- **影響**:要**刻意**才做得到,實作也照合約〈二十三〉3 (1) 的字面寫。本票防的是誤用,不是對抗,所以判非阻擋。若要收緊,可以改用 `sys.modules` 裡的模組物件或 `__file__` 是否位於 `_pytest` 套件目錄之下來判定。

---

## 5. 沒有查、或無法判定的部分

1. **實際執行行為**:依規則沒有執行任何 pytest。所有結論都是讀原始碼的紙上推演。S5c-F1 的情境沒有實測。
2. **CLEAN / REAL 層**:未驗(H.1 第 5 項)。
3. **S5c-F1 的同族機制**:`-c` / `--config-file`、`--rootdir`、`--confcutdir`、`-p no:unittest`、`-p no:<其他 builtin>` 都沒有逐一推演;unittest 那一段原始碼沒讀。
4. **H.1 第 1 項**:plugin 在 session 中途 unregister 的情形沒查。
5. **pytest-xdist 之類的分散執行**:沒查(它們會以 other plugin 出現,依 (vii) 判 unknown,但沒驗)。
6. **真實帳本**:`.dev/test-runs.jsonl`、`.dev/test-sessions.jsonl` 都沒讀;F.2 的 46 檔 `"true"` 照審查包轉述,沒有獨立核對。
7. **status 的顯示文字**:status.py 在 4c 沒改,所以沒重新核對 Evidence / Derived 的輸出格式。
8. **pytest 9.1.1 以外的版本**:沒查。`LFPluginCollWrapper` 的優先序(本版是普通優先序)在其他版本可能不同。
9. 〈二十三〉2 裁決助手的隔離環境實測(a)–(g):只把它當背景,沒有重現。

---

## 6. 程序事件(使用者名稱已遮成 `<user>`;下列訊息本身不含使用者名稱)

### 事件 1:R7/內嵌直譯器 擋下 `python -c`

- 當時要做的事:找出本機 pytest 和 pluggy 的安裝位置(只 import、印出路徑,不執行 pytest)。
- 指令(Bash):`cd /c/projects/agent-gates && python -c "import _pytest,pluggy,pytest;print(_pytest.__file__);print(pluggy.__file__);print(pytest.__version__, pluggy.__version__)" 2>&1 | sed -E '...'`
- 原始擋下訊息:

```
PreToolUse:Bash hook error: [python "$CLAUDE_PROJECT_DIR/.claude/hooks/gate.py"]: [六站閘門/前哨] [R7/內嵌直譯器][enforce] `python -c` 後面是一段程式,而**那段程式會不會寫檔,從指令字串判不出來**。
     不可判定就擋,這是 R7 既有的姿態往前一步:
     R7 問『寫到哪』,抽不出來就 refuse;這一格連『有沒有在寫』都答不出來。
     **本規則不解析引號裡的程式** —— 那是資料不是 shell 語法,
     要判它得寫一個直譯器語意的分析器,而半套的解析器比零涵蓋更危險。
     出口:用 Write 把那段程式寫成 `.scratch/<feature>/<名字>.py`,
     再 `python .scratch/<feature>/<名字>.py` 跑它 ——
     內文不進指令字串,就沒有東西需要被判定,而且 R1–R6 全部適用。
     (唯讀診斷也一樣要走這條:判準是『判不判得出來』,不是『有沒有在寫』。)
(R7 只活在前哨:commit 看得到檔案內容,看不到你用什麼工具寫的。
 繞過前哨就沒有第二道了 —— 見 docs/adr/0008)
```

- 處置:停手,沒有照訊息的建議去寫 .py 檔(審查規則禁止寫暫存檔),改用 AskUserQuestion 詢問使用者。
- 使用者選擇:「只讀繼續(Glob 找原始碼)」。之後用 Glob 在 `C:\Users\<user>\AppData` 底下找到 `...\Python311\Lib\site-packages\_pytest\cacheprovider.py`,再以 Read / Grep / `cat -n | sed -n` 讀 `_pytest/`、`pluggy/` 的原始碼。整個審查沒有再執行任何 python 指令。

### 事件 2:R7 擋下含 awk 的唯讀指令

- 當時要做的事:讀 3c 規劃檔的 P4 段。
- 指令(Bash):`cd /c/projects/agent-gates && git show 02a5e28adf5aee11a43d5a1063504f01beb1d67f:docs/audits/2026-10-02-m1a-station3c-redlight-plan.md | grep -n "P4" | head; git show 02a5e28adf5aee11a43d5a1063504f01beb1d67f:docs/audits/2026-10-02-m1a-station3c-redlight-plan.md | awk '/受影響的既有測試/{f=1} f{print NR": "$0; c++} c>30{exit}'`
- 原始擋下訊息:

```
PreToolUse:Bash hook error: [python "$CLAUDE_PROJECT_DIR/.claude/hooks/gate.py"]: [六站閘門/前哨] [R7][enforce] 這個 Bash 指令會寫到沒有被許可的位置((引號或跳脫使目標無法可靠切分)、30{exit})。
     **許可是逐段比對的**(`&&` / `;` / `||` 各算一段)。
     這幾段不在清單裡:`grep -n "P4"`、`head`、`awk '/受影響的既有測試/{f=1} f{print NR": "$0`、`c++} c>30{exit}'`
     其餘各段本來就許可 —— 把它們拿掉就過得了。
     **切分不認引號,也不認 heredoc 內文**:`<<'EOF'` 到 `EOF` 之間、
     以及引號裡的每一個 `;` / `&&` / `||`,一樣會被切成一段。
     所以「整條以 `git` 開頭」不代表安全 —— 訊息或腳本內文裡的一個分號,
     就會切出一段不以許可前綴開頭的段落。
     出口:**內文用 Write 寫成檔案**,再 `git commit -F <路徑>`
     或 `python <路徑>` 餵進去 —— 內文完全不進指令字串,
     就沒有東西可以被切。
     理由不是風格:從指令字串解析『寫到哪』解不完,而半套的解析器
     比零涵蓋更危險 —— 零涵蓋你知道它是零。所以入口收成一個,
     走檔案工具的話 R1–R6 全部適用。
     例外(附理由)在 gate.py 的 BASH_ALLOWED_CMDS / BASH_ALLOWED_TARGETS。
     指令裡出現 /dev/null **不會**讓其他寫入一起免檢。
(R7 只活在前哨:commit 看得到檔案內容,看不到你用什麼工具寫的。
 繞過前哨就沒有第二道了 —— 見 docs/adr/0008)
```

- 處置:停手,再用 AskUserQuestion 詢問(事件 1 的核准不延伸到這一次)。
- 使用者選擇:「只讀繼續(不含 awk/重導字元)」。之後改用 `git show <完整 SHA>:<路徑> | grep -n -A14 "..."` 讀取,沒有再被擋。

### 事件 3:兩次錨點偏離(照實記錄)

1. 為了找出 3c-0 規劃 commit 改了哪些檔,執行過 `git show --stat d122df4a 2>/dev/null | head -0`、`git log --format=%H -1 d122df4`、`git diff-tree ... $(git rev-parse d122df4)`。這裡用短 SHA 當**查詢錨點**,偏離了規則 3。查出完整 SHA `d122df42f1a90704961d6e07f98d5e6cd719f99e` 和檔名之後,規劃檔的內容一律以 `git show 02a5e28adf5aee11a43d5a1063504f01beb1d67f:docs/audits/2026-10-02-m1a-station3c-redlight-plan.md` 讀取。
2. 曾用 Grep 讀過一次**工作樹**的 `pyproject.toml`(沒有綁 SHA)。之後改以 `git show 02a5e28adf5aee11a43d5a1063504f01beb1d67f:pyproject.toml` 重讀;報告引用的是後者。

### 事件 4:寫入與副作用

- 改過的檔:只有本報告 `.scratch/m1a-s5c/review-report.md`。
- pytest 執行:0 次。commit:0。push:0。`.dev/pipeline.json` 沒有讀也沒有改。
- 我的工具輸出有兩次因為太大,被 harness 自動存到使用者層 `~/.claude/projects/...` 底下的 tool-results 檔(審查包全文、test_status.py 片段)。那是工具機制自動產生的,不是我用寫檔工具寫的,不在 repo 內。照實記錄。
