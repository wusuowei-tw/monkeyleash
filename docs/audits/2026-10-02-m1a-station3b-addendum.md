# M1-a Station 3b 補件 —— B10、B11(三刀:落票 → 紅燈 → 紅燈證據)

**這份檔案的身分**:Station 3b 補件的正式報告,**進版控**
(位置依據:`docs/agents/handover.md:34`「**回報檔一律進版控**(`docs/audits/`)」)。
路徑一律寫 repo 相對路徑;session scratchpad 寫 `<session scratch>`;pytest 安裝位置寫 `<site-packages>`。

| | |
|---|---|
| **撰寫時點** | 2026-10-02T16:47:41Z(寫入當下) |
| **起點 HEAD** | `acc1b36d5c9bb404a49f7303052c0a324dd76fed`(`0 11`,未推) |
| **刀 A①** | `8c18157b8b5ddba50557118d99d36b0bd8ba9622` |
| **刀 A②** | `628c060f6f5fda886ff5feba6241272e76b06cc5` |
| **刀 A③** | 本報告所在的 commit;SHA 無法寫進自己 —— 見該 commit |

---

## 【給裁決者】

1. 補了兩支紅燈:B10(固定指令沒有位置參數時,也必須算「整檔涵蓋」)、B11(格式不合格的 session 不得被悄悄丟掉,也不得被當成正常 run)。
2. B10 的假 session 不是憑記憶寫的:讀了本機 pytest 9.1.1 的原始碼與本 repo 的 `pyproject.toml`,推導出無參數時 `config.args == ["tests"]`、來源為 `TESTPATHS`(**靜態推導,未實際執行觀察**)。
3. 固定全套只跑一次:`17 failed, 1929 passed, 3 skipped, 3 xfailed` —— **紅的恰好是 3b 的 15 支加 B10、B11,L1–L3 全過,既有測試 0 失敗**。B11 的失敗訊息直接顯示現行實作把不合格 session 當成正常的 A,而且把 `deselected` 字串當成 23 個字元在算。
4. 要你決定:**驗收 Station 3b(含補件)紅燈**(之後才切 implement 進 Station 4b)。
5. 不決定的話:十四個 commit 停在本機不推(紅燈推上去 CI 會紅),Station 4b 不開始。

### 最低必要內容

| # | 項目 | 值 |
|---|---|---|
| 1 | pytest / 推導 | 9.1.1,`<site-packages>`;無位置參數且 invocation dir == rootpath ⇒ `_decide_args()` 走 `TESTPATHS` 分支(`_pytest/config/__init__.py:1415-1422`),依 `pyproject.toml:71` `testpaths = ["tests"]` ⇒ `config.args == ["tests"]`、`args_source == TESTPATHS`(**靜態推導**);B10 的 fake 以 `config.args = ["tests"]`、`args_source = pytest.Config.ArgsSource.TESTPATHS` 建構 |
| 2 | 三刀 SHA / numstat | A① `8c18157`:票 145 `10 1`;A② `628c060`:`tests/test_redlight.py` `55 0`、`tests/test_status.py` `51 0`;A③ 見視窗 |
| 3 | 新增 / 消失集合 | 新增**恰為 B10、B11**;消失集合**空** |
| 4 | 全套 | exit code **1**;`17 failed, 1929 passed, 3 skipped, 3 xfailed in 135.89s (0:02:15)`;實際失敗集合**恰為 17 支**;L1–L3 **皆未失敗** |
| 5 | B10 / B11 失敗原因 | B10:`AttributeError: module 'redlight_under_test' has no attribute 'file_coverage'`;B11:`AssertionError: 不合格的 session 被當成正常狀態 A` |
| 6 | 帳本防污染 | test-runs +46 行(= 測試檔數)、前段逐位元組不變;test-sessions +1 行(本次全套)、前段逐位元組不變;假身分 0 筆 |
| 7 | push / 改 conftest.py / 改非測試 .py / 改既有測試 / 改 pipeline / pytest 啟動次數 | **NO / NO / NO / NO / NO / 5**(collect-only 4 次 + 全套 1 次) |

---

## 【給裁決助手】證據

### 前置

```
$ git fetch origin
(無輸出)
$ git rev-list --left-right --count origin/master...HEAD
0	11
$ git rev-parse HEAD
acc1b36d5c9bb404a49f7303052c0a324dd76fed
$ git status --porcelain
(無輸出)
$ cat .dev/pipeline.json
{
  "current_stage": "tickets",
  "feature": "framework-updates",
  "ticket_id": "145",
  "updated": "2026-10-02"
}
```

### 刀 A①|落票

票 145:〈十七〉末尾逐字追加「3b 補件」(B10、B11);第 3 行改為 `**狀態**:動工 —— Station 3b 補件(B10、B11)進行中;Station 4b 未開始。`(舊行併入 F-036 block 第八代);〈十〉新增一行「Station 3b 補件：進行中」。

```
$ git diff --cached --numstat
10	1	docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
$ git diff --cached --check
(無輸出)
$ git commit -F .scratch/m1a-s3b-add/a1-msg.txt
[master 8c18157] docs(145): Station 3b 補件(B10、B11)裁決落票
 1 file changed, 10 insertions(+), 1 deletion(-)
```

(`--check` 與 commit 分兩步依序執行 —— 3b 刀③ 曾因兩者同批平行送出而在 `--check` 有輸出時 commit,本輪不再如此。)

### 刀 A② 步驟 0|推導 pytest 無參數行為(未啟動 pytest)

```
$ python -m pip show pytest
Name: pytest
Version: 9.1.1
Summary: pytest: simple powerful testing with Python
Location: <site-packages>
Requires: colorama, iniconfig, packaging, pluggy, pygments
```

(節錄:`Home-page` / `Author` / `License` / `Required-by` 四行未列;`Location` 的絕對路徑以 `<site-packages>` 代替 —— **本區塊不是逐字原文**。)

**唯讀讀取的原始碼**(`<site-packages>/_pytest/config/__init__.py`):

```
1093	        #: Command line arguments.
1094	        ARGS = enum.auto()
1095	        #: Invocation directory.
1096	        INVOCATION_DIR = enum.auto()
1097	        INCOVATION_DIR = INVOCATION_DIR  # backwards compatibility alias
1098	        #: 'testpaths' configuration value.
1099	        TESTPATHS = enum.auto()
```

```
1411	        if args:
1412	            source = Config.ArgsSource.ARGS
1413	            result = args
1414	        else:
1415	            if invocation_dir == rootpath:
1416	                source = Config.ArgsSource.TESTPATHS
1417	                if pyargs:
1418	                    result = testpaths
1419	                else:
1420	                    result = []
1421	                    for path in testpaths:
1422	                        result.extend(sorted(glob.iglob(path, recursive=True)))
```

```
1433	            else:
1434	                result = []
1435	            if not result:
1436	                source = Config.ArgsSource.INVOCATION_DIR
1437	                result = [str(invocation_dir)]
1438	        return result, source
```

```
1624	        self.args, self.args_source = self._decide_args(
1625	            args=getattr(self.option, FILE_OR_DIR),
1626	            pyargs=self.option.pyargs,
1627	            testpaths=self.getini("testpaths"),
1628	            invocation_dir=self.invocation_params.dir,
1629	            rootpath=self.rootpath,
1630	            warn=True,
1631	        )
```

`<site-packages>/_pytest/config/findpaths.py`:

```
312	    else:
313	        ancestor = get_common_ancestor(invocation_dir, dirs)
314	        rootdir, inipath, inicfg, ignored_config_files = locate_config(
315	            invocation_dir, [ancestor]
```

本 repo 設定(`Grep testpaths|\[tool\.pytest|rootdir|addopts` 於 `pytest.ini` / `pyproject.toml` / `setup.cfg` / `tox.ini`):

```
pyproject.toml:70:[tool.pytest.ini_options]
pyproject.toml:71:testpaths = ["tests"]
pyproject.toml:72:addopts = "-ra --strict-markers"
```

(另一個命中 `pyproject.toml:19` 是註解,與設定無關。)

**推導結論(靜態推導,未實際執行觀察)**:固定指令從 repo 根執行,無使用者位置參數 ⇒ `args` 為空;
rootdir 由 repo 根的 `pyproject.toml` 決定 ⇒ invocation dir == rootpath ⇒ `source = TESTPATHS`;
非 pyargs ⇒ `result = sorted(glob.iglob("tests", recursive=True))` = `["tests"]` ⇒
**`config.args == ["tests"]`、`config.args_source == Config.ArgsSource.TESTPATHS`**。

### 刀 A② 步驟 1–4

**BEFORE-COLLECT**(A① commit 後、乾淨 HEAD):`tests/test_redlight.py` 29 支、`tests/test_status.py` 67 支,無 collection error。

**實作期間未執行任何 pytest**:

```
$ python -X utf8 -m py_compile tests/test_redlight.py
(無輸出)
$ python -X utf8 -m py_compile tests/test_status.py
(無輸出)
$ git diff --name-only
tests/test_redlight.py
tests/test_status.py
$ git diff --cached --numstat
55	0	tests/test_redlight.py
51	0	tests/test_status.py
$ git diff --cached --check
(無輸出)
$ git commit -F .scratch/m1a-s3b-add/a2-msg.txt
[master 628c060] test(145): Station 3b 補件紅燈 —— B10(固定指令整檔涵蓋)、B11(不合格 session 可觀察)
 2 files changed, 106 insertions(+)
```

兩檔皆只有新增、0 刪除 ⇒ 既有測試(Station 3 的 14 支、3b 的 18 支)與既有輔助函式一字未改。
新增輔助:`_drive_with_session()`(test_redlight,讓呼叫端傳入帶 `args_source` 的 session)、`_evidence_and_derived()`(test_status,擷取兩個區塊)。

**AFTER-COLLECT**(A② commit 後、乾淨 HEAD):`tests/test_redlight.py` 30 支、`tests/test_status.py` 68 支,無 collection error;前 29 / 67 支與 BEFORE 逐行同名同序。新增的兩行原文:

```
tests/test_redlight.py::TestFixedCommandCoverage::test_b10_the_fixed_command_without_positional_args_is_full_coverage
tests/test_status.py::TestMalformedSessionIsVisible::test_b11_a_malformed_session_is_neither_dropped_silently_nor_read_as_normal
```

⇒ 新增集合**恰為 B10、B11**;消失集合**空**。

### collect-only 與帳本(collection-only observation)

| 時點 | test-runs(bytes / lines) | test-sessions(bytes / lines) |
|---|---|---|
| BEFORE-COLLECT 之前 | 600499 / 2227 | 933154 / 6 |
| BEFORE-COLLECT 之後 | 600499 / 2227 | 942855 / 8 |
| AFTER-COLLECT 之後(= 全套 before) | 600499 / 2227(`30a3513e1a56f7c753acdc0ecff315888bb9dbd80d098923d7f158e044a5fc17`) | 952809 / 10(`f3a48d453dacbdb0ee304cb95dfb2241de1d653c3304d52831972e1c1ee89bf4`) |

四次 `--collect-only` 各寫一筆 session —— **collection-only observation,非紅燈驗收證據**;test-runs 未被寫入。

### 刀 A③|固定全套(在 `628c060` 上,只跑一次)

```
$ python -X utf8 -m pytest -q
...
FAILED tests/test_redlight.py::TestFileCoverage::test_b1a_a_nodeid_argument_is_not_full_coverage
FAILED tests/test_redlight.py::TestFileCoverage::test_b1b_a_backslash_nodeid_argument_is_not_full_coverage
FAILED tests/test_redlight.py::TestFileCoverage::test_b1c_a_file_argument_without_deselection_is_full_coverage
FAILED tests/test_redlight.py::TestFileCoverage::test_b1d_a_parent_directory_argument_is_full_coverage
FAILED tests/test_redlight.py::TestFileCoverage::test_b1e_a_file_argument_with_deselection_is_not_full_coverage
FAILED tests/test_redlight.py::TestFileCoverage::test_b1f_no_config_means_unknown
FAILED tests/test_redlight.py::TestFileCoverage::test_b1g_an_argument_outside_the_root_means_unknown
FAILED tests/test_redlight.py::TestRunStateSchema::test_b6_a_session_without_collected_is_not_state_c
FAILED tests/test_redlight.py::TestFixedCommandCoverage::test_b10_the_fixed_command_without_positional_args_is_full_coverage
FAILED tests/test_status.py::TestCoverageChain::test_b2_a_nodeid_run_does_not_retire_an_unidentified_red
FAILED tests/test_status.py::TestCoverageChain::test_b3_a_nodeid_run_does_not_orphan_a_known_red
FAILED tests/test_status.py::TestDStateRetiresNothing::test_b4_a_d_run_with_a_collection_error_elsewhere_retires_nothing
FAILED tests/test_status.py::TestSessionSchemaFailClosed::test_b5_a_session_without_deselected_retires_nothing
FAILED tests/test_status.py::TestSessionSchemaFailClosed::test_b7_an_outcome_outside_collected_retires_nothing
FAILED tests/test_status.py::TestSessionSchemaFailClosed::test_b9_a_string_deselected_retires_nothing_and_orphans_nothing
FAILED tests/test_status.py::TestAbsenceIsNotCoverage::test_b8_a_run_without_coverage_facts_does_not_orphan
FAILED tests/test_status.py::TestMalformedSessionIsVisible::test_b11_a_malformed_session_is_neither_dropped_silently_nor_read_as_normal
17 failed, 1929 passed, 3 skipped, 3 xfailed in 135.89s (0:02:15)

[exit code 1]
```

背景執行,完成通知回報 `exit code 1`。

**判定**

| 條件 | 結果 |
|---|---|
| exit code = 1 | **成立** |
| 實際失敗集合 = 3b 預期紅集合(15)∪ {B10, B11} | **成立**(17 = 17;兩方向差集皆空) |
| L1–L3 不在失敗集合 | **成立**(1929 passed 與 3b 時相同) |
| 既有測試 0 失敗 | **成立** |
| B10 為 `AttributeError` 類 | **成立** |
| B11 為 `AssertionError` | **成立** |

**B10、B11 失敗原因原文**(輸出檔中的對應行,逐字):

```
E       AttributeError: module 'redlight_under_test' has no attribute 'file_coverage'
```

```
E           AssertionError: 不合格的 session 被當成正常狀態 A
E             === Evidence ===
E             test-runs: 本票 red 0 / green 1 / run 事實未知 0 / orphaned 0;最後一筆 tests/test_x.py=red @ 2026-10-02T16:45:45.825659+00:00;最近一次 run:A(exit 0;collected 1 / deselected 23 / passed 1 / failed 0 / skipped 0)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl)
```

(B11 的訊息後續還有完整的 Evidence / Derived 區塊,其中 `tests green under ticket 99: tests/test_x.py`;此處只節錄前三行。
`deselected 23` 是字串 `tests/test_x.py::test_y` 的字元數 —— 錯型別被照常迭代,正是 F1。)

B11 在第一條斷言(前後輸出不同)**通過**,在第二組斷言(不得顯示為正常狀態)以 `A` 失敗 —— 現行實作沒有靜默丟棄,而是把它當成正常 run。

### 帳本防污染

```
$ wc -c -l .dev/test-runs.jsonl .dev/test-sessions.jsonl
   2273  613185 .dev/test-runs.jsonl
     11 1413031 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl .dev/test-sessions.jsonl
b555ded4e2986f819c711c4ef16168c9df25f54cce12fd8064141e9cc7bc2ada *.dev/test-runs.jsonl
d97b7631d55ba0b8359803a6b2ffa9c6330de02b8363dc0c769afea6eb38e12e *.dev/test-sessions.jsonl
$ head -c 600499 .dev/test-runs.jsonl > <session scratch>/runs-prefix-3badd.bin
$ head -c 952809 .dev/test-sessions.jsonl > <session scratch>/sessions-prefix-3badd.bin
$ sha256sum <session scratch>/runs-prefix-3badd.bin <session scratch>/sessions-prefix-3badd.bin
30a3513e1a56f7c753acdc0ecff315888bb9dbd80d098923d7f158e044a5fc17 *<session scratch>/runs-prefix-3badd.bin
f3a48d453dacbdb0ee304cb95dfb2241de1d653c3304d52831972e1c1ee89bf4 *<session scratch>/sessions-prefix-3badd.bin
```

(scratchpad 絕對路徑以 `<session scratch>` 代替 —— **這三條指令與輸出經遮罩,不是逐字原文**;`wc` 的 `total` 行省略。)

- test-runs:2273 − 2227 = **46** 行(= 本次測試檔數);前 600499 bytes = before ⇒ **前段逐位元組不變**。
- test-sessions:11 − 10 = **1** 行;前 952809 bytes = before ⇒ **前段逐位元組不變**。新增那一行的欄位頭:

```
"kind": "session", "run_id": "328fbc7c826e47238465eabff225dd6d", "time": "2026-10-02T16:46:21.647219+00:00", "ticket_id": "145", "exit_code": 1
```

- 假身分 / 假檔名 / 假 run_id(`Grep` 精確比對):test-runs 中 `"test_file": "tests/test_(x|y|thing|broken).py"` **0** 筆;test-sessions 中 `"tests/test_(x|y|thing|broken).py::` 與 `"run_id": "b(5|6|7|8|9|11)"` **0** 筆。

全套後工作樹:`git status --porcelain` 無輸出。

### status.py 的 Evidence 與 Derived

`python .claude/portable/status.py --root .`(一處遮罩:`report:` 行的 HEAD 時間含本地時區偏移,以 `<本地時間>` 代替;`tests green under ticket 145` 那一行的 44 檔清單以「(44 檔,同 3b)」代替;其餘逐字):

```
=== Evidence ===
test-runs: 本票 red 2 / green 44 / run 事實未知 0 / orphaned 0;最後一筆 tests/test_verify_gates.py=green @ 2026-10-02T16:46:21.647219+00:00;最近一次 run:B(exit 1;collected 1952 / deselected 0 / passed 1929 / failed 17 / skipped 3)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl)
intercepts (當月): 1 筆  (source: .dev/intercepts-2026-10.jsonl)
intercepts (最新存在月): 2026-10 1 筆;末筆 R7@2026-10-02T12:12:16.405577+00:00  (source: .dev/intercepts-2026-10.jsonl)
exemptions: 總 281 筆;granted 240 筆;blocked 1 筆;未記錄(無此欄)40 筆;最後一筆 2026-09-24T08:17:49.073745+00:00  (source: .dev/gate-exemptions.jsonl)
provenance: 未記錄(上游無此檔屬正常)  (source: .dev/provenance.jsonl)
report: 2026-09-24T084909Z-ticket137-status-line.md;HEAD <本地時間>;回報後 16 筆  (source: .dev/reports/)

=== Derived ===
src write allowed in tickets: no  (source: gate.stage_allows_src_write() <- .agents/pipeline-stages.yaml)
tests red under ticket 145: tests/test_redlight.py / tests/test_status.py  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests green under ticket 145: (44 檔,同 3b)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests green (run 事實未知) under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests orphaned under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
rules defined: R1 R2 R3 R4 R5 R6 R7 R8 R9  (source: gate.rule_codes())
```

`collected 1952` = 1929 passed + 17 failed + 3 skipped + 3 xfail(記為 `other`)。

### 刀 A③ 的票 145 改動

第 3 行改為 `**狀態**:動工 —— Station 3b(含補件)紅燈已寫(待 Jeff 驗收);Station 4b 未開始。`(舊行併入 F-036 block 第九代);
新增〈十八之一、Station 3b 補件紅燈證據〉;〈十〉「Station 3b 補件」改為「紅燈已寫，待驗收」。

PRIVATE-CONTEXT CHECK:**PASS** —— 本輪新增文字只來自裁決、pytest 原始碼、repo 設定、測試碼、測試輸出、帳本與 status 輸出;
pytest 安裝位置、session scratchpad 絕對路徑與本地時區偏移皆已遮罩。

---

## 尚未證明 / 本輪未做

1. **Station 3b(含補件)紅燈未經 Jeff 驗收。**
2. **B10 的 `config.args` 是靜態推導**:未以真實 pytest 執行時觀察 `session.config.args` / `args_source` 的實際值。4b 後以固定全套與真實 session 帳本補驗。
3. **B11 不指定可觀察痕跡的位置與文字**:只要求前後不同、不得顯示為 A / B / C / F;4b 的呈現方式需另行檢視是否足以讓人看懂。
4. **3b 刀③ 的程序違規**(在 `--check` 有輸出時 commit)上一輪已回報;本輪未處理那 6 筆。
5. 十四個 commit 均未推。

---

## 六站狀態

| 站 | 狀態 |
|---|---|
| Station 1 — Spec | PASS / CLOSED |
| Station 2 — Ticket | DONE |
| Station 3 — Red-light | PASS / ACCEPTED |
| Station 4 — Implementation | 實作嘗試完成,Station 5 FAIL |
| Station 5 — Review | FAIL |
| Station 3b — Red-light(補) | 紅燈已寫,待驗收 |
| Station 3b 補件 | 紅燈已寫,待驗收 |
| Station 6 — Acceptance | NOT STARTED |
