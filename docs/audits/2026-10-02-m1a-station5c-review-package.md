# M1-a Station 5c 獨立審查包(票 145)

**審查對象(TARGET)**:`02a5e28adf5aee11a43d5a1063504f01beb1d67f`

本包只是材料,不含任何審查結論。所有逐字段落皆以 `<!-- 逐字開始 -->` / `<!-- 逐字結束 -->` 標出邊界,
邊界之間的文字與標示的出處逐位元組相同(換行一律 LF)。

---

## A. 身分與規則

### A.1 永久記錄的身分

| 名稱 | 完整 SHA | 說明 |
|---|---|---|
| **Implementation TARGET** | `02a5e28adf5aee11a43d5a1063504f01beb1d67f` | Station 4c 實作 commit —— **唯一審查對象** |
| S4c-2 docs commit | `a88b7f9664189f9b3f3124aa39eb3a95eaca51b1` | Station 4c 修正證據與〈二十五〉裁決(只改 docs/) |
| S3c-1b | `49bcde20adc276632fa5bab456e8c7a80839fc0b` | Station 3c-1b(C3e-1 driver 修正)—— `git diff <S3c-1b>..<TARGET>` 的測試改動即 4c 授權補件 |
| Station 5b target | `851cbd75b359a6b2a34452265e8a70992fa56996` | 前一次獨立審查(FAIL)的對象 |

- 本包所在的 commit(S5c-0)是 S4c-2 **之後**才建立的 docs-only commit;本包寫不進自己的 SHA,由裁決者交付審查時另附。S5c-0 **不屬於審查對象**。
- `git diff --name-only 02a5e28adf5aee11a43d5a1063504f01beb1d67f..a88b7f9664189f9b3f3124aa39eb3a95eaca51b1` 只列出 `docs/audits/2026-10-02-m1a-station4c-fix.md` 與 `docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md`(本包建立時核對)。

### A.2 查詢一律綁定完整 SHA

所有可重跑的 Git 查詢都以上表的完整 SHA 為錨點,不以分支名、`HEAD` 或工作樹當下狀態為錨點。範例:

```
git show 02a5e28adf5aee11a43d5a1063504f01beb1d67f:<路徑>
git diff 851cbd75b359a6b2a34452265e8a70992fa56996..02a5e28adf5aee11a43d5a1063504f01beb1d67f -- <路徑>
git diff 49bcde20adc276632fa5bab456e8c7a80839fc0b..02a5e28adf5aee11a43d5a1063504f01beb1d67f -- tests/test_redlight.py tests/test_status.py
git show a88b7f9664189f9b3f3124aa39eb3a95eaca51b1:docs/audits/2026-10-02-m1a-station4c-fix.md
```

`origin/master` = 本票所有 commit 之前的上游狀態(〈D〉列出 `origin/master..TARGET` 的全部 commit)。

### A.3 審查者規則

1. **唯讀**:不改任何檔案、不 commit、不推、不改 `.dev/pipeline.json`。
2. **禁止 pytest**(含 `--collect-only`、`--version`)。帳本(`.dev/test-runs.jsonl`、`.dev/test-sessions.jsonl`)會被任何 pytest 執行追加,審查不得污染證據。需要驗證行為時,讀程式碼做紙上推演。
3. 審查報告**只寫到** `.scratch/m1a-s5c/review-report.md`,不寫其他位置(含 scratchpad、暫存檔)。
4. **照錄任何系統訊息、錯誤訊息或路徑前,先把本機使用者名稱遮成 `<user>`。** Station 5b 的審查報告曾因照錄含本機使用者資料夾名稱的系統訊息而觸發 pre-commit 洩漏偵測(票 145〈二十一〉21.3 第 7 點)。
5. 被任何閘門(R1–R9、pre-commit、洩漏偵測)擋下:停手回報,不換工具、不繞過。
6. **結論只能是 `PASS` 或 `FAIL`**。只要有任何一項「阻擋」發現,就是 `FAIL`。
7. 每一項發現須標**「阻擋」或「非阻擋」**,並附 `<TARGET>:<路徑>:<行號>` 形式的證據(例:`02a5e28adf5aee11a43d5a1063504f01beb1d67f:.claude/hooks/redlight.py:562`)。沒有行號證據的發現不計入判定。
8. 〈G〉的 G1–G12 每一題都必須回答(「無問題」也要附證據);不能回答的,寫明「無法判定」與原因,不得略過。

### A.4 審查範圍內的檔案

| 路徑 | 角色 |
|---|---|
| `.claude/hooks/redlight.py` | run 事實的寫入 / 讀取 / 判定(`record_session`、`load_runs`、`validate_session`、`run_state`、`file_coverage`、`classify_plugins`、`_completeness_problems`、`_completeness_verdict`) |
| `.claude/portable/status.py` | 依 run 事實判定紅綠(`ticket_test_state`、`_apply_run`)與顯示;**Station 4c 未改** |
| `tests/conftest.py` | producer(pytest hooks → `record_session`;`pytest_make_collect_report` trylast wrapper;`_completeness_of`) |
| `tests/test_redlight.py` | Station 3 / 3b / 3c 的 producer / consumer 側紅燈;4c 授權補件(b1c / b1d / b10) |
| `tests/test_status.py` | Station 3 / 3b / 3c 的 status 側與串接紅燈;4c 授權補件(546 / ODC-2 / L3) |

---

## B. 規格依據(逐字)

### B.1 〈十三〉ODC-1(修訂後全文)

行號來源:02a5e28adf5aee11a43d5a1063504f01beb1d67f:docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md 第 568–573 行(該檔在 TARGET 的 blob ID:`800bb542b8b0af3b61a559a987bb9f5be4b555c7`)

<!-- 逐字開始 -->
ODC-1（修訂後全文，取代〈十一〉同條的第 2、3 項）
一個 run 只有在同時滿足下列三項時，才有資格使某 test file 內既有的 red 變為 green：
1. 該 file 的測試集合全部被選到（沒有任何 deselected）；
2. 已知先前為 red 的 test identity，本次確實執行並通過；若歷史 red 無法知道是哪一條 test，則該 file 內所有 applicable tests 都必須實際執行並通過；
3. 該 file 本次沒有任何 failure。
其他 file 的 failure 不影響本 file 的退紅資格；與既有 red 無關的 skip 亦不影響。
<!-- 逐字結束 -->

### B.2 〈十七〉Station 5 獨立審查(FAIL)與 Station 3b 裁決

行號來源:02a5e28adf5aee11a43d5a1063504f01beb1d67f:docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md 第 806–836 行

<!-- 逐字開始 -->
## 十七、Station 5 獨立審查（FAIL）與 Station 3b 裁決（2026-10-02，Jeff）

Station 5 結果：FAIL（獨立、無記憶審查者）。審查包與審查結果原文存於 docs/audits/2026-10-02-m1a-station5-review-package.md 與 docs/audits/2026-10-02-m1a-station5-independent-review-fail.md。Station 4 實作保留，作為 3b 紅燈要打紅的 baseline，不回滾。

審查檔保存模型：.scratch/m1a-s5-review/ 保留原始審查證據（未修改）；docs/audits/ 為 repo-normalized archival copy。
- 審查包：原始與 repo copy 的 SHA-256 皆為 892db3f7b8a59884dba01590becff2406fa089e841b0bec40e6479e8c3bab165。
- 審查結果（FAIL）：原始檔為 CRLF、無檔尾換行，SHA-256 99f617c8a273db431b7691b3cd48090f9e061959c69d2dd2e3f575e1853ea7a0；repo copy 依 text normalization 保存為 LF 並補檔尾換行，SHA-256 b9b559f6124e0f2fb6b6ae554b45bdef14dda341ae86e8043664f3dfd477ca3f。文字內容未改，差異僅限 CRLF→LF 與檔尾換行。
- 依 .gitattributes 的 * text=auto，進版控的 blob 本即為 LF；不以「進 Git 後與原始位元組相同」作為要求。
- 審查包含 7 處 trailing whitespace（第 652、653、850、884、888、920、946 行），為內嵌 unified diff 的空白 context 行，屬原始審查證據，刻意保留未修改；本 commit 的 git diff --check 以此 7 筆為已知例外。

確認的缺陷：
- F1：session 缺必要欄位（如 deselected、collected）或欄位型別不符時，被當成空集合或錯誤型別並進入正常判定，可退紅、可誤判 C。
- F2：run_state 判為 D 的 run（例：exit 1 + 他檔收集錯誤），其他檔仍可退紅並產生 green。
- F3：「沒有 deselected」被當成「整檔被選到」；以 nodeid 指名執行（如 pytest tests/test_x.py::test_a）時，未收集的身分不產生 deselected ⇒ 身分不明的舊紅被錯誤退紅；已知紅身分被錯誤判為 orphaned。
- F4：紅燈測試分別驗 producer 與 consumer，沒有串接驗證，F1–F3 因此漏網。

Invariant（新增）：Absence is not coverage —— 一個 test identity 沒出現在某 run 中，不得僅因此推論它已刪除、改名、不存在或已被完整涵蓋。

裁決：
1. Coverage authority（F3）：每個 run、每個 test file 有一個 machine-readable 事實 full_file_coverage ∈ {true, false, unknown}。只有 producer 能正向證明該次對該檔為整檔涵蓋時才為 true（例：該檔或其上層目錄以不含 :: 的位置參數進入收集、該檔沒有任何 deselected、沒有其他使涵蓋範圍未知的情形）；nodeid 指名等明確窄選為 false；其餘一律 unknown。只有 true 才有 ODC-1 退紅權與 ODC-2 orphan 判定權；false / unknown 兩者皆無。不知道，就不是完整。
2. D 狀態（F2）：run_state(run) == D 時，整個 run 沒有任何退紅權，也不得使任何檔成為 green。
3. Schema fail-closed（F1）：session 缺必要欄位、型別不符、或 outcome 身分不屬於本次 selected 時，該 run 不得進入正常語意；不得以「缺欄 ⇒ 空集合」或「錯型別照常迭代」處理；不得產生退紅、orphan 或 green；須可被觀察到。
4. 串接驗證（F4）：須有 producer → 持久化 run 事實 → status 的串接測試。
5. 4b 測試補件授權：Station 3 原 14 支測試與 570 / 571 / 749 的 assertion、預期語意、test identity 一律不改；4b 只授權在 ODC-2 孤兒測試（test_a_renamed_red_test_is_orphaned_not_green）與 570 / 571 / 749 的 fixture 補上 full_file_coverage = true 的事實。若只補事實仍無法維持原 assertion：立即停手回裁。
6. 3b 新增測試分兩類：behavior-red（現行實作必須失敗）與 regression-lock（現行已正確，必須通過）；驗收以預先標定的 exact nodeid 集合為準，不以數量為準。
7. 證據原則：任何 pytest（含 --collect-only）只能在乾淨、已 commit 的 HEAD 上執行。
8. Debt（不擋 M1-a）：.dev/test-sessions.jsonl 每次全套約增長 450 KB，reader 為全檔讀取；M1-a 結案時另開票（rotation / index / compaction），本票不得順手最佳化。

3b 補件（2026-10-02，Jeff）：4b 指令明文要求的兩項行為先補紅燈 ——
- B10：pytest 無使用者位置參數的正常全套執行（即固定指令 python -X utf8 -m pytest -q），該檔被正常收集、無 deselected ⇒ full_file_coverage 必須為 "true"。fake session 依本機 pytest 原始碼與本 repo 設定推導出的無位置參數 config.args 值／語意建構；此為靜態推導，不宣稱為實際執行觀察值。
- B11：schema 不合格的 session 不得被靜默丟棄，也不得被當成正常 run。在同一個 root 中加入該 session 前後，status 輸出的 Evidence 與 Derived 區塊必須可區分（表示位置與文字由 4b 決定）；加入後不得顯示為正常狀態 A / B / C / F；不得 green、不得 orphan。
<!-- 逐字結束 -->

(〈十七〉裁決 7 原文中的「HEAD」是當時的裁決文字,不是本包的查詢錨點。)

### B.3 〈十八之一〉B10 推導(18-1.1)

行號來源:02a5e28adf5aee11a43d5a1063504f01beb1d67f:docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md 第 909–927 行

<!-- 逐字開始 -->
### 18-1.1 pytest 無位置參數時的 `config.args`(**靜態推導,未實際執行觀察**)

`python -m pip show pytest`:`Version: 9.1.1`;`Location:` 使用者層 Python 3.11 的 `site-packages`(絕對路徑不入票)。

| 來源 | 行號 | 原文 / 內容 |
|---|---|---|
| `_pytest/config/__init__.py` | 1087–1099 | `class ArgsSource(enum.Enum)`:`ARGS`、`INVOCATION_DIR`、`TESTPATHS` |
| 同上 | 1411–1413 | `if args:` ⇒ `source = Config.ArgsSource.ARGS`;`result = args` |
| 同上 | 1415–1422 | `if invocation_dir == rootpath:` ⇒ `source = Config.ArgsSource.TESTPATHS`;非 pyargs 時 `result.extend(sorted(glob.iglob(path, recursive=True)))` 逐一展開 testpaths |
| 同上 | 1435–1437 | `if not result:` ⇒ `source = Config.ArgsSource.INVOCATION_DIR`;`result = [str(invocation_dir)]` |
| 同上 | 1624–1631 | `self.args, self.args_source = self._decide_args(args=getattr(self.option, FILE_OR_DIR), …, testpaths=self.getini("testpaths"), invocation_dir=self.invocation_params.dir, rootpath=self.rootpath, …)` |
| `_pytest/config/findpaths.py` | 312–315 | 未指定 inifile 時,由 invocation dir 往上 `locate_config()` 找設定檔,rootdir = 找到的設定檔所在目錄 |
| `pyproject.toml`(本 repo) | 70–72 | `[tool.pytest.ini_options]`;`testpaths = ["tests"]`;`addopts = "-ra --strict-markers"` |

**推導**:固定指令從 repo 根執行、無使用者位置參數 ⇒ rootdir = repo 根 = invocation dir ⇒ 走 `TESTPATHS` 分支 ⇒
`config.args == ["tests"]`、`config.args_source == Config.ArgsSource.TESTPATHS`。

**B10 的 fake 依此建構**:`_SessionWithConfig([...], ["tests"], tmp_path)`(`rootpath` 與 `invocation_params.dir` 皆為 root),
另設 `session.config.args_source = pytest.Config.ArgsSource.TESTPATHS`(`pytest/__init__.py:107` 公開匯出 `Config`)。
<!-- 逐字結束 -->

### B.4 〈十九〉Station 4b 修正

行號來源:02a5e28adf5aee11a43d5a1063504f01beb1d67f:docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md 第 970–1077 行

<!-- 逐字開始 -->
## 十九、Station 4b 修正

### 19.1 coverage 判定依據(`redlight.file_coverage(run, test_file)`)

依序判定,先命中者為準:

| 條件 | 結果 |
|---|---|
| run schema 不合格 | `unknown` |
| 本 run 沒有收集到該檔的任何身分,或該檔有收集錯誤 | `unknown` |
| 該檔有任何 deselected 身分(`-k` / `-m` / `--deselect` / `--lf` 等) | `false` |
| 沒有 invocation 事實、`pyargs` 為真、或 `args` 不是非空 list | `unknown` |
| 某個位置參數是**該檔本身或其上層目錄**(含 `.`)、且不含 `::` | `true` |
| 位置參數只以 nodeid(含 `::`)指名該檔 | `false` |
| 其餘(參數無法判讀 —— 如落在 root 之外 —— 或都與該檔無關) | `unknown` |

**固定指令判為 `"true"`,走通用規則、無特殊分支**:pytest 未給位置參數時以 testpaths 補上 `config.args == ["tests"]`
(〈十八之一〉推導),與「位置參數為上層目錄 `tests`」同一條規則。
本站固定全套留下的真實 session 印證了這個推導:`"invocation": {"args": ["tests"], "args_source": "TESTPATHS", "pyargs": false}`。

位置參數的正規化(`redlight._normalize_arg`):反斜線換成 `/`;相對路徑以 `invocation_params.dir`(無則 root)為基準解析,
再轉成 **root 相對 posix 路徑**;落在 root 之外或跨磁碟 ⇒ `null`(無法判讀)。**絕對路徑與 invocation dir 不落帳。**

### 19.2 D 狀態與 schema fail-closed

- **`redlight.validate_session(run)`** 回傳問題清單(空 = 合格):`run_id` / `time` 為非空字串;`ticket_id`、`exit_code` 欄位存在
  (`exit_code` 為 int 或 null);`collected` / `deselected` 為字串 list 且 `deselected ⊆ collected`;
  `outcomes` 為 `{字串: passed | failed | skipped | other}` 且鍵 ⊆ selected;`invocation` 若存在須為 dict(`args` 為 list 或 null)。
- **`redlight.run_state(run)`**:不合格 ⇒ `"INVALID"`(不是 A–F 任何一個);其餘照原表。
- **`status._apply_run()`**:不合格 run **不產生任何效果**(不加紅、不退紅、不 orphan、不 green);
  `run_state == "D"` ⇒ 整個 run **沒有退紅權、不得使任何檔成為 green**;
  退紅 / orphan / green **只在 `file_coverage == "true"` 時進行**。
- **不合格 run 在 status 上的表示形式**(Evidence 區塊 `test-runs` 行):
  - 計數:`… / orphaned N / schema 不合格 run N;…`
  - 最近一次 run 若不合格:`最近一次 run:INVALID(schema 不合格:<問題清單>)`(不從它計算任何計數)

### 19.3 四個檔的改動(`git diff af839c6 --stat`)

```
 .claude/hooks/redlight.py  | 164 ++++++++++++++++++++++++++++++++++++++++++++-
 .claude/portable/status.py | 122 +++++++++++++++++++++------------
 tests/conftest.py          |  31 ++++++++-
 tests/test_status.py       |   6 +-
 4 files changed, 277 insertions(+), 46 deletions(-)
```

- `.claude/hooks/redlight.py`(+163 / −1):新增 `_normalize_arg`、`_normalize_invocation`、`OUTCOME_VALUES`、`validate_session`、`file_coverage`;
  `record_session` 新增 `invocation` 參數並落帳正規化後的 `invocation`;`run_state` 對不合格 run 回 `INVALID`。
- `.claude/portable/status.py`(+81 / −41):新增 `_RL_FUNCS`、`_rl_ready`、`_invalid_count`;`_apply_run` 依 19.2 重寫並接受 `rl`;
  `ticket_test_state(records, runs, ticket, rl=None)`(`rl` 為 None ⇒ 涵蓋一律未知);`_last_run_text` 顯示 INVALID;
  `_evidence` / `_derived` 傳入 `rl`,`test-runs` 行加 `schema 不合格 run N`。
- `tests/conftest.py`(+29 / −2),逐段:
  1. `pytest_sessionfinish` 尾段:原本直接呼叫 `record_session(_ROOT, …)`,改為先組 `kwargs`(內容不變),
     若 `record_session` 的簽名有 `invocation` 參數(`inspect.signature`)才加上 `invocation=_invocation_of(session)`,再呼叫。舊版 redlight 照舊不傳。
  2. 新增 `_invocation_of(session)`:讀 `session.config` 的 `args`、`args_source.name`、`invocation_params.dir`、`option.pyargs`(屬性一律帶預設值);沒有 config ⇒ None。
  3. 既有 `_outcomes` / `_run` 的蒐集邏輯與其他 hook **未動**。
- `tests/test_status.py`(+4 / −2):見 19.4。

**未修改**:`tests/test_redlight.py`(`git diff af839c6 --stat -- tests/test_redlight.py` 無輸出)、`.claude/hooks/gate.py`、`.agents/`、`pipeline.json`。
Station 3 的 14 支與 3b 的 20 支測試的 assertion、docstring、test identity 未動;僅 19.4 的兩處授權補件。

### 19.4 fixture 補件(〈十七〉裁決 5;assertion 一字未改)

`git diff -U0 tests/test_status.py` 原文:

```
@@ -577 +577,2 @@ class TestTestsUnderTicketUsesTheLatestRecordPerFile:
-            deselected=[], outcomes={u"tests/test_a.py::test_one": u"passed"})
+            deselected=[], outcomes={u"tests/test_a.py::test_one": u"passed"},
+            invocation={u"args": [u"tests"]})
@@ -1329 +1330,2 @@ class TestOrphans:
-                                deselected=[], outcomes={new: u"passed", keep: u"passed"})
+                                deselected=[], outcomes={new: u"passed", keep: u"passed"},
+                                invocation={u"args": [u"tests"]})
```

- 570 / 571:該測試 Station 4 補上的 run 加 `invocation={u"args": [u"tests"]}` ⇒ 該 run 對 `tests/test_a.py` 為整檔涵蓋。
- ODC-2(`test_a_renamed_red_test_is_orphaned_not_green`):run2 加同一參數 ⇒ 整檔涵蓋 ⇒ 有 orphan 判定權。
- 749:直接呼叫未改的 `_latest_per_file()` ⇒ 不需補。
- 兩處改動只在 `record_session(...)` 呼叫的參數列尾端加一個參數(原行的 `)` 移到新行),**無任何 assertion 被改動**。

### 19.5 證據鏈

| 步驟 | 證據 |
|---|---|
| 前置 H0 / L0 | test-runs `b555ded4e2986f819c711c4ef16168c9df25f54cce12fd8064141e9cc7bc2ada` / 613185 / 2273;test-sessions `d97b7631d55ba0b8359803a6b2ffa9c6330de02b8363dc0c769afea6eb38e12e` / 1413031 / 11 |
| S4b-1 commit 前未執行 pytest | commit 前與 commit 後重量兩本帳,SHA-256 / bytes / lines **皆與 H0 / L0 相同** |
| S4b-1 commit | `333e5853bf1a1712bde2aea2d2b488299e3752f6`(`163 1` / `81 41` / `29 2` / `4 2`);pre-commit 未擋 |
| 固定全套(只跑一次,在 `333e585` 上) | exit code **0**;`1946 passed, 3 skipped, 3 xfailed in 147.38s (0:02:27)`;**failed 0** |
| 3b 的 17 支 / L1–L3 / Station 3 的 14 支 | **全部通過**(失敗集合為空;1946 = 1929 + 17) |
| 帳本只追加 | test-runs after 前 613185 bytes 的 SHA-256 = H0;test-sessions after 前 1413031 bytes 的 SHA-256 = H0 |
| 帳本 after | test-runs `73737b7d…a8a93` / 624488 / 2319(+46 = 測試檔數,全 green);test-sessions `42bdc38e…7e35` / 1873333 / 12(+1) |

**status.py**(節錄):

```
test-runs: 本票 red 0 / green 46 / run 事實未知 0 / orphaned 0 / schema 不合格 run 0;最後一筆 tests/test_verify_gates.py=green @ 2026-10-02T17:05:51.724830+00:00;最近一次 run:A(exit 0;collected 1952 / deselected 0 / passed 1946 / failed 0 / skipped 3)
tests red under ticket 145: (無)
tests orphaned under ticket 145: (無)
```

### 19.6 測試三層

| 層 | 狀態 |
|---|---|
| **UNIT** | 固定全套 exit 0,`1946 passed, 3 skipped, 3 xfailed` |
| **CLEAN** | 未證明 |
| **REAL** | 留待 Jeff 端 status_all 確認(本站不宣稱) |
<!-- 逐字結束 -->

### B.5 〈二十一〉Station 5b 獨立審查(FAIL)與 Station 3c 裁決

行號來源:02a5e28adf5aee11a43d5a1063504f01beb1d67f:docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md 第 1102–1159 行

<!-- 逐字開始 -->
## 二十一、Station 5b 獨立審查（FAIL）與 Station 3c 裁決（2026-10-02，Jeff）

### 21.1 審查報告

- 路徑 docs/audits/2026-10-02-m1a-station5b-independent-review-fail.md
- 原始證據：.scratch/m1a-s5b/review-report.md（不進版控），LF，30155 bytes，
  sha256 05951ee66f810e308954f2baa301d8fafb88f431fc9c0f54c9ac166c4c1917fc
- repo 副本：docs/audits/2026-10-02-m1a-station5b-independent-review-fail.md，30156 bytes，
  sha256 bc7d9b67ac0f7d030ed4b0cda78013bbf372f504c3f489874fbcb5a6ed0c1e3f，Git blob 見下一行
- 兩者唯一差異：第 329 行本機使用者資料夾名稱以 `<user>` 遮罩（pre-commit 洩漏偵測擋下，依 F-116 遮罩版不再稱為原始）。
  其餘逐位元組相同。
- Git blob：5caacedbd123e3aa47eb39d8819ef66fedac9e11
- 審查對象 851cbd75b359a6b2a34452265e8a70992fa56996；判決 FAIL；阻擋 1（S5b-F1），非阻擋 5（S5b-F2–F6）

### 21.2 裁決助手外部重現（隔離環境；不是本 repo 的帳本證據；未寫入本 repo 任何檔案）

- 環境：pytest 9.1.1；redlight.py、status.py、tests/conftest.py 取自 TARGET；testpaths = ["tests"]；
  一個測試檔含模組層 test_a、test_b。
- R1 全套（實作不存在）⇒ 收集錯誤 ⇒ 整檔紅。
- R2 全套（test_a 過、test_b 敗）⇒ red = {整檔, test_b}；lastfailed = {test_b}。
- R3 `pytest -q --lf`（test_b 已修、test_a 被改壞）⇒ 只收集並執行 test_b，passed；deselected = []；
  invocation args = ["tests"] ⇒ file_coverage = "true"，run_state = A ⇒ ticket_test_state = green。
- 實際：單獨執行 test_a ⇒ 1 failed。⇒ S5b-F1 在真實執行上成立。
- 附註 1：審查報告推演的 R2（只跑 nodeid）在真實執行中 lastfailed 仍保留整檔鍵、R3 會跑全檔，該條路徑不重現；
  但上面「全套 → --lf」的路徑重現，結論不變。
- 附註 2：即使檔案先前沒有紅，--lf 也會讓「只跑了部分身分」的檔被判 green。問題在 coverage 判定本身，不限整檔紅。
- 附註 3：審查報告 G5 推演 -x / --maxfail 在 TARGET 上未造成假綠（停止點所在檔必有 failure；之後的檔沒有 outcome，不退紅、不 green）。
  下面裁決 2 仍把提前停止納入合約，作為正向事實的一部分；它在 3c 的紅燈屬於 behavior-red 還是 regression-lock，於規劃時逐支判定。

### 21.3 裁決

1. Station 5b FAIL 成立；S5b-F1 為阻擋。依流程回 Station 3c（補紅燈）→ 4c（修正）→ 5c（新的獨立審查）。不推、不回滾、不改寫歷史。
2. 修正方向（合約）—— coverage authority 的正向事實必須涵蓋「選擇完整性 + 執行完整性」：
   full_file_coverage == "true" 除既有條件外，producer 必須正向記錄足以證明本次沒有任何
   「會縮小實際執行集合」或「會提前終止執行」的機制生效。至少盤點並分類：
   - selection / collection narrowing：--lf / --last-failed 等（收集期就過濾、不發 deselected 通知）
   - execution early-stop：-x / --exitfirst、--maxfail、--sw / --stepwise（含 --sw-skip）等
   具體清單、每個機制在 pytest 9.1.1 的實際行為（是否走 pytest_deselected、是否提前停止）與原始碼出處，
   於 Station 3c 規劃時逐項確認並列表。
   任一必要事實缺欄、型別不明、或機制生效 ⇒ 不得給 "true"；依語意給 "false" 或 "unknown"，兩者都沒有退紅權與 orphan 權。
   不得以「沒有 deselected」推論選擇完整或執行完整。
3. Station 3c 紅燈至少要含：
   (a) --lf silent narrowing：收集結果少了身分、沒有 deselected 通知 ⇒ 不退紅、不 green；
   (b) 選擇／執行完整性事實缺欄 ⇒ 不得為 "true"；
   (c) -x / --maxfail 或 --sw：完整收集但部分未執行 ⇒ 不得因 coverage authority 被當成 green 或 orphan-safe；
   (d) regression lock：固定全套指令（narrowing / early-stop 全關）仍判 "true"；
   (e) 21.2 的三步情境（全套 → --lf → status 假綠）以 driver 表達（不在真實帳本執行）。
   3c 規劃時必須逐支標明 behavior-red（現在應該失敗）或 regression-lock（現在就應該通過），
   驗收照舊：預期紅集合 = 實際失敗集合。
4. S5b-F2–F6：非阻擋，本票不修，登記到 M1-a 結案後的追蹤票。
   S5b-F3（固定 skip/xfail 讓整檔紅永遠退不了）需要另裁合約對 applicable 的解讀，在追蹤票處理。
5. 程序事件：審查者曾嘗試寫入 scratchpad，被 R7 擋下；停手詢問後，Jeff 選擇只讀繼續。
   審查前後 HEAD、樹狀態、兩本帳皆未變（裁決助手以 status_all 核對）。照實記錄，不影響審查效力。
6. 結案後追蹤票清單更新為：conftest 不受 R2/R3 管的缺口；session 帳本增長；S5b-F2–F6；上游票 139 少一空行。
7. 洩漏事件：審查報告照錄 R7 擋下訊息時，帶入了本機使用者資料夾名稱（F-082 型）。
   pre-commit 洩漏偵測（權威層）在 S5b-1 commit 時擋下，未進入歷史。
   處置：裁 A，repo 副本遮罩、原檔不動、不豁免偵測。
   Station 5c 審查者提示新增一條：照錄系統訊息前，先遮罩本機路徑中的使用者名稱。
<!-- 逐字結束 -->

### B.6 〈二十三〉Station 3c 裁決與完整性事實合約

行號來源:02a5e28adf5aee11a43d5a1063504f01beb1d67f:docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md 第 1175–1264 行

<!-- 逐字開始 -->
## 二十三、Station 3c 裁決與完整性事實合約（2026-10-02，Jeff）

### 23.1 裁決(照錄)

1. P3 採 C：selection completeness 與 execution completeness 都要有 producer 的正向事實。
2. 裁決助手隔離環境實測（pytest 9.1.1；不是本 repo 帳本證據）：
   (a) conftest 的 hookimpl(wrapper=True, trylast=True) pytest_make_collect_report 在 --lf 時看得到縮小前全集（4 支），session.items 只剩 1 支；
   (b) 測試內 pytest.exit(returncode=0)：exit 0、4 支只跑 2 支、shouldstop 與 shouldfail 皆為 False；
   (c) --sw 停下 exit 2；
   (d) -p no:cacheprovider 時 config.option 沒有 lf、stepwise；
   (e) --lf 真的過濾時 lfplugin-collskip 會註冊；
   (f) 預設 config.option.maxfail 為 None；
   (g) config.pluginmanager.list_name_plugin() 在 sessionfinish 時列出全部已註冊 plugin：
       -p 載入、PYTEST_PLUGINS 載入、任何層級的 conftest 都看得到；
       非頂層 conftest 定義 pytest_plugins 在 pytest 9 是收集錯誤（run 判 D）。
       名稱為數字（id）的項目來自 _pytest 內部物件；conftest 的名稱是絕對路徑。
3. 受支援範圍（supported execution boundary）：full_file_coverage == "true" 只在本次註冊的每一個 plugin 都屬於白名單類別時宣稱：
   (1) builtin：定義模組為 _pytest 或 _pytest.*（模組物件看 __name__；其他物件看其類別或物件的 __module__）；
   (2) root_conftest：root 相對路徑恰為 tests/conftest.py 的 conftest；
   (3) known_dist：該 plugin 物件出現在 pluginmanager.list_plugin_distinfo() 的配對中，且 dist 名稱屬於已知清單 {"anyio"}。
       只看名稱相同不算（名稱可被冒用）。
   其他任何來源（-p、PYTEST_PLUGINS、其他 conftest、未知 dist、無法分類）⇒ kind = "other" ⇒ 不是 "true"（"unknown"）。
   tests/conftest.py 本身是 producer，屬於受審查程式碼，視為信任邊界內；此點明文記錄，不是未知來源。
   白名單定義在 redlight.py，變更須走票。
4. -p no:cacheprovider：pluginmanager.is_blocked("cacheprovider") 為 True，視為 lf / stepwise 不可能作用的正向事實。
5. 授權 4c 只在規劃檔 P4「受影響的既有測試」那六支的 fake / fixture 補上「全部關閉、白名單內」的完整性事實；
   assertion、docstring、test identity 一律不改。
6. anyio 擴增（P1 #20）：Station 4b 固定全套的真實 session 合格（run_state A），目前 repo 沒有觸發它的測試；列入追蹤票。
7. 完整性事實合約（3c 依此寫測試，4c 依此實作；欄位名稱可在本刀定稿，語意不得改）：
   session 新增欄位 completeness（dict），至少含：
   - options：lf、last_failed_no_failures、stepwise、stepwise_skip、maxfail、collectonly、setuponly、setupplan
     （照 config.option 原樣；屬性不存在記為 null）
   - cacheprovider_blocked：bool
   - shouldstop、shouldfail：bool（session 結束時的值）
   - pre_narrowing：{測試檔: [縮小前完整 nodeid 清單]}（trylast wrapper 當下立刻複製）
   - plugins：[{"name": 正規化名稱, "kind": "builtin" | "root_conftest" | "known_dist" | "other"}]
     由 producer 從 list_name_plugin() 與 list_plugin_distinfo() 的原始事實分類產生；
     路徑型名稱只能記 root 相對路徑，root 以外記 "<outside>"；帳本中不得出現任何絕對路徑。
   file_coverage(run, f) == "true" 的新增必要條件（全部成立才行）：
   (i)    completeness 存在且型別正確；缺欄或型別錯 ⇒ "unknown"
   (ii)   lf 與 stepwise 都為 False，或 cacheprovider_blocked 為 True
   (iii)  maxfail 為 None 或 0；collectonly、setuponly、setupplan 皆為 False
   (iv)   shouldstop、shouldfail 皆為 False
   (v)    pre_narrowing 有 f，且它的集合 == 本 run 中 f 的 collected 身分集合（selected + deselected）；不相等 ⇒ "false"
   (vi)   f 的每一個 selected 身分都達到「執行完成」終態：
          只承認 call phase 的 passed / failed、skip（任何 phase）、明確辨識的 xfail / xpass。
          沒有 call、只有 setup、被中止、無法辨識、或籠統的 other ⇒ 不算執行完成 ⇒ 不是 "true"。
          4c 須讓 outcome 能區分 xfail / xpass，不得讓 other 自動取得 completeness。
   (vii)  plugins 每一項的 kind 都不是 "other"
   不得以「沒有 deselected」推論完整；不得以「有一筆 report」推論已執行；不得以「名稱相同」推論 known_dist。
8. 鏈條要求：完整性事實的每一段（raw pytest 事實 → producer 分類與記錄 → 持久化 session → file_coverage → 退紅 / green / orphan）
   都要有測試鎖住；不得只測 consumer 收到預先分類好的資料。

### 23.2 預期集合(照錄;完整 nodeid)

預期紅集合(behavior-red,16 支,在 d122df4 上必須失敗):

- tests/test_redlight.py::TestCompletenessCoverage::test_c3a_lf_silent_narrowing_is_not_full_coverage
- tests/test_status.py::TestSilentNarrowingChain::test_c3a_lf_narrowing_does_not_retire_an_unidentified_red
- tests/test_status.py::TestSilentNarrowingChain::test_c3a_lf_narrowing_does_not_make_a_clean_file_green
- tests/test_redlight.py::TestCompletenessCoverage::test_c3b_a_session_without_completeness_facts_is_not_full_coverage
- tests/test_redlight.py::TestCompletenessCoverage::test_c3b_a_malformed_completeness_fact_is_not_full_coverage
- tests/test_redlight.py::TestCompletenessCoverage::test_c3c_an_exitfirst_run_is_not_full_coverage
- tests/test_status.py::TestEarlyStopChain::test_c3c_exitfirst_does_not_orphan_a_known_red
- tests/test_status.py::TestEarlyStopChain::test_c3c_pytest_exit_zero_partial_file_is_not_green
- tests/test_status.py::TestLfFalseGreenChain::test_c3e_full_then_lf_does_not_produce_a_false_green
- tests/test_redlight.py::TestCompletenessCoverage::test_c3p_an_unknown_plugin_dist_means_not_full_coverage
- tests/test_redlight.py::TestCompletenessCoverage::test_c3p_a_plugin_loaded_by_name_means_not_full_coverage
- tests/test_redlight.py::TestCompletenessCoverage::test_c3p_an_extra_conftest_means_not_full_coverage
- tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_an_unknown_dist_plugin_as_other
- tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_a_plugin_loaded_by_name_as_other
- tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_an_extra_conftest_as_other_and_the_root_conftest_as_root_conftest
- tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_builtin_root_conftest_and_known_dist_as_not_other

預期綠集合(regression-lock,5 支,在 d122df4 上必須通過):

- tests/test_status.py::TestEarlyStopChain::test_c3c_exitfirst_does_not_make_unrun_files_green
- tests/test_status.py::TestEarlyStopChain::test_c3c_stepwise_stop_is_d_and_retires_nothing
- tests/test_redlight.py::TestCompletenessCoverage::test_c3d_the_fixed_command_with_everything_off_is_full_coverage
- tests/test_status.py::TestCompletenessLocks::test_c3d_the_fixed_command_full_run_still_retires_the_red
- tests/test_status.py::TestEarlyStopChain::test_setup_only_run_is_not_green

### 23.3 本刀定稿的介面細節(不是裁決原文;語意依 23.1 第 7 點)

- `completeness` 的鍵名照 23.1 第 7 點原樣定稿:`options`、`cacheprovider_blocked`、`shouldstop`、`shouldfail`、`pre_narrowing`、`plugins`;
  `options` 內的鍵名與 `config.option` 屬性同名;`plugins` 每項為 `{"name", "kind"}`,路徑型名稱記 root 相對 posix 路徑(例:`tests/sub/conftest.py`)。
- 3c 的 driver 以 new-style 協定(`wrapper=True`,23.1 第 2 點 (a))呼叫 conftest 的 `pytest_make_collect_report`:
  先送出完整結果,wrapper 返回後才**就地**縮小 `report.result`;假 item / collector 是 `pytest.Item` / `pytest.File` 的子類。
  4c 的 producer 須在 wrapper 當下複製 nodeid,並以 `pytest.Item` 判斷 item(或等價方式)。
- 明確辨識的 xfail 在 driver 中表達為:call report `outcome == "skipped"` 且帶 `wasxfail`。
<!-- 逐字結束 -->

### B.7 〈二十五〉Station 4c 修正與裁決

行號來源:a88b7f9664189f9b3f3124aa39eb3a95eaca51b1:docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md 第 1289–1315 行(該檔在 S4c-2 的 blob ID:`7714312cbd0ddee8f88ec52654f7b7f6f6922df4`)

<!-- 逐字開始 -->
## 二十五、Station 4c 修正與裁決

- 報告:`docs/audits/2026-10-02-m1a-station4c-fix.md`。
- S4c-1 `02a5e28adf5aee11a43d5a1063504f01beb1d67f`;固定全套(只跑一次)`1967 passed, 3 skipped, 3 xfailed`,exit 0。

裁決(2026-10-02,Jeff;照錄):

1. 完成條件 (c)「不得有絕對路徑」的適用範圍，依欄位性質分三類：
   (1) producer 為了自身正規化、分類而產生的 path-valued metadata（例如 completeness.plugins[].name）：
       不得產生或洩漏絕對路徑。
   (2) pytest 提供、作為 identity 必須逐字保存的 opaque facts（nodeid；collected、outcomes、pre_narrowing 中的身分）：
       不因本條改寫；pre_narrowing 與 collected 的比對需要逐字相等。
   (3) invocation.args：依〈十九〉Station 4b 已驗收的正規化規則處理（root 相對路徑；root 以外不落帳），
       屬既定且可重現的正規化，不屬本條，也不是任意改寫。
   若 (2) 類原始事實本身帶有本機敏感路徑，屬另一個 privacy / provenance 問題，列入 M1-a 結案後追蹤票。
   裁決助手獨立核對真實 session（第 15 行）：類似絕對路徑的字串只出現在 collected、outcomes 的鍵、
   completeness.pre_narrowing 三處，共 29 個身分，且 pre_narrowing 中的這些身分全部也在 collected 中；
   plugins 與 invocation 不含；整行不含本機使用者名稱。本次固定指令的 invocation.args 為相對的 tests。
   ⇒ (c) 判定成立。〈二十三〉7 plugins 條目末句「帳本中不得出現任何絕對路徑」以本條澄清範圍（原文依 F-036 不改）。
2. 接受實作偏離：pre_narrowing 記錄每個 collector report 中的 pytest.Item（File 的直接子項，以及 Class 等子 collector 的子項），
   以測試檔為 key、完整身分集合為 value。理由：class 內的測試不在 File 的 report 裡；--lf 只在 File 層過濾
   （_pytest/cacheprovider.py:282-290），子 collector 不受影響。真實固定全套 46 檔全部以同一套一般規則判 "true" 為佐證。
   Station 5c 必答題（審查包須列入）：多層 collector 累積是否會因重複、巢狀 class、parametrize、hook 順序而漏記或錯記；
   --lf 的 File 層縮小是否確實發生在本 snapshot 之後，沒有形成新的 false-positive coverage 路徑。
3. 裁決助手獨立核對：帳本 H2 前段雜湊相符（36bf61df… / 0ef187e0…）；真實 session 的 46 檔 file_coverage 全為 "true"；
   plugins 43 項（builtin 41、known_dist 1、root_conftest 1），無 other。
4. Station 4c implementation = PASS / COMPLETED，待 Station 5c 獨立審查。四項完成判定：(a)(b)(c)(d) 皆成立。
<!-- 逐字結束 -->

---

## C. 歷次 FAIL 的發現原文

### C.1 Station 5(F1–F4)

出處:`02a5e28adf5aee11a43d5a1063504f01beb1d67f:docs/audits/2026-10-02-m1a-station5-independent-review-fail.md` 第 11–197 行;
該檔在 TARGET 的 blob ID:`ae885228549f9100618d8f97effecf2bca4e82a6`。
(原報告的編號是「1.」–「4.」;票 145〈十七〉記為 F1–F4,對應 1 → F1、2 → F2、3 → F3、4 → F4。)

<!-- 逐字開始 -->
### 1.【阻擋】缺少必要欄位的 session 仍能消除既有 red

**位置：** `.claude/hooks/redlight.py::load_runs`、`run_state`；`.claude/portable/status.py::_apply_run`

**程式碼原文：**

```python
if not isinstance(rec, dict) or not rec.get("run_id"):
    return []
out.append(rec)
```

```python
deselected = set(str(n) for n in (run.get("deselected") or []))
```

```python
if not any(n in deselected for n in idents):
```

```python
red[f] = set(n for n in red[f] if outcomes.get(n) != u"passed")
```

**具體情境：**

既有 `tests/test_x.py::test_x` 為 red，較晚收到以下 session：

```json
{
  "run_id": "r2",
  "time": "2",
  "ticket_id": "99",
  "exit_code": 0,
  "collected": ["tests/test_x.py::test_x"],
  "outcomes": {"tests/test_x.py::test_x": "passed"}
}
```

紀錄**沒有 `deselected`**，因此無法知道選取範圍是否完整。`load_runs()` 仍接受它，`_apply_run()` 將缺欄解讀成空集合，進入退紅分支。

直接執行附件函式可得到：

```python
{"state": "green", "unresolved": [], "orphaned": []}
```

同一問題也影響狀態分類：`run_state()` 把缺少 `collected` 當成零收集，可能將不完整證據宣稱為 C；它也沒有驗證 passed 身分是否屬於 selected。

**對應合約：** I5、I7、C 節、ODC-1 第 1 項及 coverage 未知不得退紅、AC-1、AC-4、AC-5。

---

### 2.【阻擋】有 collection error 的 D run，仍可能讓其他檔退紅成 green

**位置：** `.claude/hooks/redlight.py::run_state`；`.claude/portable/status.py::_apply_run`

**程式碼原文：**

```python
if ec not in (0, 1, 5) or any(str(n).endswith("::" + COLLECTION_ERROR) for n in collected):
    return "D"
```

```python
exit_ok = run.get("exit_code") in (0, 1)
```

```python
errored = any(n.endswith(u"::<collection error>") for n in idents)
```

```python
green_now[f] = exit_ok and u"passed" in results
```

**具體情境：**

既有 `tests/test_x.py::test_x` 為 red。較晚 session 的內容為：

```python
exit_code = 1
collected = [
    "tests/test_x.py::test_x",
    "tests/broken.py::<collection error>",
]
deselected = []
outcomes = {"tests/test_x.py::test_x": "passed"}
```

`run_state()` 明確回傳 **D**。但 `_apply_run()` 只檢查 exit code 及當前檔案的 collection error，因此把 `tests/test_x.py` 的 red 清除並列為 **green**。已用附件函式重現。

〈十三〉允許其他檔案的測試 failure 不影響本檔退紅；它沒有撤銷 C 節「D 狀態不能解決 red」及 I3 的限制。

**對應合約：** A 節 D、I3、I5、C 節禁止 D 退紅、AC-3、RL-4。

---

### 3.【阻擋】「沒有 deselected」不足以證明全檔選取，身分不明的歷史 red 可被局部結果清除

**位置：** `tests/conftest.py::pytest_collection_finish`、`pytest_sessionfinish`；`.claude/portable/status.py::_apply_run`

**程式碼原文：**

```python
_run["selected"] = [_nodeid(i) for i in getattr(session, "items", None) or []]
```

```python
collected=list(selected) + list(_run["deselected"]) + list(_run["collect_errors"]),
```

```python
if not any(n in deselected for n in idents):
```

```python
if any(n.endswith(u"::" + WHOLE_FILE) for n in red[f]):
    if all(outcomes.get(n) == u"passed" for n in idents):
        red[f] = set()
```

**具體情境：**

檔案實際有 X、Y，歷史 red 的 `failed_tests=[]`，依裁決應視為全檔測試均是先前紅。

若本次選取範圍只讓 X 進入 `session.items`，沒有提供 Y 的 deselection 通知，producer 寫出的事實就是：

```python
collected = [X]
deselected = []
outcomes = {X: "passed"}
```

consumer 無從區分「檔案只有 X」與「此次只收集 X」，卻將兩者都當作全檔選取，清除 `WHOLE_FILE` red。以此輸入執行附件函式，結果確實是 green。

這與發現 1 不同：此處所有欄位都齊全，缺少的是**足以證明全檔涵蓋的事實**。附件沒有提供選取限制或完整集合證據來排除此情境。

**對應合約：** I5、I7、ODC-1 第 1、2 項、〈十三〉裁決 3、AC-4、AC-5。

---

### 4.【應修】紅燈測試將 producer 與 aggregate 分開驗證，錯誤 consumer 仍可能全部通過

**位置：**

- `tests/test_redlight.py::TestRunFacts`
- `tests/test_status.py::TestTicket139::test_a_narrow_all_skip_record_does_not_retire_the_earlier_red`

**程式碼原文：**

RL-4(c)：

```python
assert len(runs) == 1, runs
assert redlight.run_state(runs[0]) == "D", runs[0]
```

RL-6 producer：

```python
assert redlight.run_state(run) == "F", run
assert len(run["deselected"]) == 645, len(run["deselected"])
assert [v for v in run["outcomes"].values()].count("skipped") == 3, run["outcomes"]
assert "passed" not in run["outcomes"].values(), run["outcomes"]
```

RL-6 consumer：

```python
_write_raw_lines(root, [LEDGER_940, LEDGER_970])
out = render(root)
```

**具體情境：**

RL-4 只檢查 `run_state()`，未驗證同一紀錄交給 status 後不得退紅或產生 green，因此未涵蓋發現 2。

RL-6 的 consumer 測試只有兩筆歷史八欄紀錄，沒有加入 producer 產生的 F session。假設錯誤 consumer 在遇到 F session 時清除 red：

- producer 測試仍可正確判出 F；
- 歷史紀錄測試因沒有 F session，仍保留 red；
- 兩者都通過，實際串接後卻違反 RL-6。

應補上「既有 red → 本次 session → status aggregate」的連續驗證，以及上述證據不完整情況。

**對應合約：** F 節 RL-4、RL-6、RL-6b；AC-7 的驗收充分性。此發現不否認附件所報告的修前失敗、修後通過結果。
<!-- 逐字結束 -->

### C.2 Station 5b(S5b-F1–F6)

出處:`02a5e28adf5aee11a43d5a1063504f01beb1d67f:docs/audits/2026-10-02-m1a-station5b-independent-review-fail.md` 第 243–311 行;
該檔在 TARGET 的 blob ID:`5caacedbd123e3aa47eb39d8819ef66fedac9e11`(repo 副本;與原始證據唯一差異在第 329 行,不在本段範圍內)。
原報告中的 `<T>` 代表 Station 5b 的審查對象 `851cbd75b359a6b2a34452265e8a70992fa56996`,**不是**本次的 TARGET。

<!-- 逐字開始 -->
### S5b-F1【阻擋】`--lf` 在收集期濾掉的身分不產生 deselected,`file_coverage` 誤判 `"true"`,身分不明的整檔紅會被局部 run 退成 green

**證據行**
- `<T>:.claude/hooks/redlight.py:405-406` —— 只用「有沒有 deselected」判斷檔內選取是否縮窄。
- `<T>:.claude/hooks/redlight.py:423-426` —— 位置參數是上層目錄 ⇒ `"true"`。
- `<T>:tests/conftest.py:167-175`(只有 `pytest_deselected` 會記排除)、`<T>:tests/conftest.py:178-182`(selected = `session.items`)、`<T>:tests/conftest.py:233-236`(collected = selected + deselected + 收集錯誤 —— 收集期就被濾掉的身分三者都不在)。
- `<T>:tests/conftest.py:249-267` —— invocation 只記 args / args_source / dir / pyargs,沒有記 `--lf` 之類會縮窄收集的選項。
- `<T>:.claude/portable/status.py:470-472` —— 整檔紅只要求「本 run 收集到的身分」全部 passed。
- 佐證(本機 pytest 9.1.1 原始碼,不在 TARGET 內):`_pytest/cacheprovider.py:267-290`(File 收集報告就地過濾,沒有呼叫 deselected hook)、`:354-359`(模組收集成功時,模組鍵換成全部子身分)、`:348-350`(passed 從 lastfailed 移除)、`:389-391`(只有 modifyitems 層才走 `pytest_deselected`);`_pytest/main.py:726-729`、`:842-846`(initpath 不含父目錄比對)。

**具體情境(紙上推演)**

`tests/test_x.py` 有兩個模組層測試函式 `test_a`、`test_b`(本 repo 有 19 個測試檔含模組層 `def test_`,`git grep -c "^def test_" <T> -- tests/`)。

1. R1(票 145):實作還不存在 ⇒ 收集錯誤。conftest.py:161 ⇒ 8 欄 red,`failed_tests=["<collection error>"]` ⇒ status.py:400-402 視為整檔紅 `tests/test_x.py::*`。
   pytest cache 的 lastfailed = `{"tests/test_x.py": true}`。
2. 實作寫好。R2:`python -X utf8 -m pytest -q tests/test_x.py::test_a`,test_a passed。
   cache:模組收集成功 ⇒ 模組鍵換成 `{test_a, test_b}`(cacheprovider:357-359),test_a passed 被移除(348-350)⇒ lastfailed = `{tests/test_x.py::test_b}`。
   帳本:args `["tests/test_x.py::test_a"]` ⇒ `"false"` ⇒ 不退紅(正確),整檔紅還在。
3. 開發者為了讓 test_b 通過改了實作,**改壞了 test_a**。R3:`python -X utf8 -m pytest -q --lf`(repo 根、無位置參數)。
   - `config.args = ["tests"]`(TESTPATHS,與 B.3 推導相同)。
   - File collector `test_x.py` 在 `_last_failed_paths` 裡;結果 `[test_a, test_b]` 裡有 test_b 在 lastfailed ⇒ 第 282-290 行只留 test_b。test_a 不在 lastfailed,`isinitpath(tests/test_x.py)` 為假 ⇒ **test_a 被丟掉,沒有任何 hook 通知**。
   - modifyitems:previously_failed = `[test_b]`、previously_passed = `[]` ⇒ `pytest_deselected(items=[])`。
   - test_b passed,exit 0。
4. producer 寫出:`collected=["tests/test_x.py::test_b"]`、`deselected=[]`、`outcomes={"tests/test_x.py::test_b":"passed"}`、`invocation={"args":["tests"],"args_source":"TESTPATHS","pyargs":false}`。
5. `file_coverage`:合格;idents = `[test_b]`;沒有收集錯誤;沒有 deselected;args `tests` ⇒ 423 行命中 ⇒ **`"true"`**。`run_state` = A。
6. `_apply_run`:沒有 failure ⇒ 456 行通過 ⇒ gone 為空 ⇒ 整檔紅,`all(passed for idents=[test_b])` 為真 ⇒ `red[f] = set()`(472)⇒ `green_now = True`(475)。

**錯誤輸出**:`tests green under ticket 145` 列出 `tests/test_x.py`,`tests red` 不含它。
可是 test_a 在 R3 沒有執行,而且實際上是紅的。

**應有輸出**:依 ODC-1 第 1 項(該檔測試集合全部被選到)、第 2 項(身分不明時,所有 applicable tests 都必須在本次實際執行並通過)、〈十七〉裁決 1(不知道,就不是完整),coverage 應該是 `"false"` 或 `"unknown"`,`tests/test_x.py` 應該仍紅。

**影響**
- 重現了前次 F3(阻擋)的核心:「沒有 deselected」被當成「整檔被選到」,於是身分不明的歷史紅被局部結果清除。
- 「新模組第一次紅燈幾乎都是收集錯誤」(conftest.py:153-155)⇒ 整檔紅正是本流程最常見的紅;「修完先跑單一 nodeid,再 `--lf`」是常見的工作流程。
- 已知身分的紅不受影響(474 行逐身分檢查)。受影響的只有整檔紅。用 class 組織的測試在這條路徑上剛好不受影響:第 274 行只看直接子節點的 nodeid,而 Class collector 保留在第 289 行。
- 3b / 4b 的測試沒有接住:`_chain_drive`(test_status.py:1473-1500)與 `_drive_with_args` 都由 `selected` 推出收集結果,表達不了「從來沒進入收集」。

### S5b-F2【非阻擋】一行讀不動(缺 `run_id`、非 dict、JSON 壞、半行)會讓整本 session 帳消失,而且不顯示成 INVALID

- 證據:`<T>:.claude/hooks/redlight.py:275-279`;`<T>:.claude/portable/status.py:540-543`、`:551-557`(只有 `load_runs` 成功回傳的紀錄才會被 validate / 計數)。
- 情境:手寫一筆 `{"kind":"session","time":"…","ticket_id":"145",…}`(沒有 `run_id`),或寫入時磁碟滿留下半行(見 G11(c))
  ⇒ `load_runs` 回 `[]` ⇒ Evidence 顯示 `schema 不合格 run 0`、`最近一次 run:無 run 證據 / 不可判定`;先前由 session 退掉的紅,從 8 欄 red 紀錄全部重新出現。
- 影響:fail-closed(只會多紅、不會多綠),所以不擋。但〈十七〉裁決 3 要求的「須可被觀察到」在這一型只做到「輸出有變」,沒做到「指出是哪一筆、什麼問題」。半行之後的追加會接在壞行後面,不手動修帳本就永遠不會恢復。

### S5b-F3【非阻擋】整檔紅要求「全部收集到的身分 passed」,會把固定 skip / xfail 的檔鎖成永遠退不了紅

- 證據:`<T>:.claude/portable/status.py:470-472`;`<T>:tests/conftest.py:194-199`(skip ⇒ `skipped`,xfail ⇒ `other`)。
- 情境:這台機器上 `tests/test_gate.py` 有 3 個固定 skip(審查包 F.1:「此環境無法建立 symlink」)。如果它曾因收集錯誤得到整檔紅,之後在這台機器上的任何 run 都滿足不了 471 行 ⇒ 永遠紅。`tests/test_g1_guard.py` 的 3 個 xfail 同理。
- 影響:fail-closed 的可用性問題。ODC-1 寫的是「applicable tests」與「與既有 red 無關的 skip 亦不影響」,被 skip 的測試算不算 applicable 是合約解讀問題,建議裁決者明定。不擋。

### S5b-F4【非阻擋】非 `.py` 的收集錯誤鍵(`<session>`、目錄、`conftest.py`)會產生沒有任何 run 能退掉的紅

- 證據:`<T>:tests/conftest.py:164`(`"%s::<collection error>" % (f or "<session>")`,不限 `.py`);`<T>:.claude/portable/status.py:441-453`(依 `::` 前段分檔,errored ⇒ 加 `<f>::*`)。
- 情境:`tests/conftest.py` import 失敗 ⇒ 錯誤掛在目錄或 conftest 節點上 ⇒ 檔鍵 `tests` 或 `tests/conftest.py` 得到整檔紅。之後的全套 run 永遠不會收集到 `tests::…` 這種身分 ⇒ 456 行之後的退紅永遠進不去 ⇒ 這張票的 status 永遠列一個紅。
- 影響:fail-closed 的可用性問題(Station 4 引入,在 E.1 範圍內)。不擋。

### S5b-F5【非阻擋】producer 有兩段在 try 之外,docstring 的「紀錄器不得弄死執行器」只涵蓋寫入那一段

- 證據:`<T>:.claude/hooks/redlight.py:233`(docstring)vs `:236-246`(組 rec,含 `_normalize_invocation`,在 try 外)與 `:248-253`(try);`<T>:tests/conftest.py:243-246`;pytest `main.py:364-371`。
- 情境:見 G11(a)(b)。用 conftest 實際交進來的型別,我找不到會觸發的輸入。
- 影響:目前是理論風險;下游改了 `_invocation_of` 或 redlight 的介面時會變成真的。不擋。

### S5b-F6【非阻擋】`validate_session` 的 docstring 說 `ticket_id`「字串或 null」,程式只檢查欄位存在;型別錯的 ticket_id 會讓不合格 session 不被計數

- 證據:`<T>:.claude/hooks/redlight.py:290`(docstring)vs `:303-304`(只檢查 `in`);`<T>:.claude/portable/status.py:503`、`:555-556`(以 `== ticket` 篩選)。
- 情境:一筆 `ticket_id: 145`(int)的 session ⇒ 不屬於本票 ⇒ 不產生效果(正確),但也不出現在 `schema 不合格 run N`。
- 影響:審查包 19.2 只要求「欄位存在」,所以程式符合合約,但 docstring 宣稱得比實作多。不擋。
<!-- 逐字結束 -->

---

## D. 本票 commit 清單

產生指令:`git log --oneline origin/master..02a5e28adf5aee11a43d5a1063504f01beb1d67f`(完整輸出,23 行)

```
02a5e28 fix(145): M1-a Station 4c —— 選擇/執行完整性事實與 plugin 邊界(coverage authority)
4ff0310 docs(145): M1-a Station 3c 紅燈證據(含 3c-1b)
49bcde2 test(145): M1-a Station 3c-1b —— C3e-1 每次執行改用全新 conftest(修 driver 狀態殘留)
175da88 test(145): M1-a Station 3c 紅燈 —— 選擇/執行完整性與 plugin 邊界(16 behavior-red + 5 regression-lock)
d122df4 docs(145): M1-a Station 3c-0 —— 紅燈規劃(選擇/執行完整性機制盤點)
353ca18 docs(145): M1-a Station 5b FAIL(S5b-F1)與 Station 3c 裁決(選擇/執行完整性)
5c637fd docs(145): M1-a Station 5b-0 —— 獨立審查包(target 851cbd7);〈十〉現況句同步
851cbd7 docs(145): Station 4b 證據入票 —— 固定全套 exit 0,3b 的 17 支紅燈全部轉綠
333e585 fix(145): M1-a Station 4b —— coverage authority / D 無退紅權 / schema fail-closed
af839c6 docs(145): Station 3b 補件紅燈證據入票 —— 17 failed 恰為預期,L1–L3 全過
628c060 test(145): Station 3b 補件紅燈 —— B10(固定指令整檔涵蓋)、B11(不合格 session 可觀察)
8c18157 docs(145): Station 3b 補件(B10、B11)裁決落票
acc1b36 docs(145): Station 3b 紅燈證據入票 —— 15 failed 恰為預期紅集合,L1–L3 全過
a9d885a test(145): Station 3b 紅燈 —— coverage authority / D 狀態 / schema fail-closed / 串接
280a551 docs(145): Station 5 獨立審查 FAIL 存檔 + Station 3b 裁決落票(〈十七〉)
3df2613 docs(145): Station 4 證據入票 —— 固定全套 exit 0,14 支紅燈全部轉綠
db01283 feat(145): M1-a Station 4 —— run 事實(producer / 帳本 / status 退紅判定)
f50b285 docs(145): Station 3→4 轉場落票 —— Station 3 PASS、redlight.py 豁免已 drain
b27ca30 chore(145): drain .claude/hooks/redlight.py 的 R3 豁免(9 -> 8)
09e1e91 docs(145): Station 3 紅燈證據入票 —— 14 failed 恰為預期集合,既有 0 失敗
5188f49 test(145): Station 3 紅燈 —— 13 條規格 / 14 支測試(依紅燈規劃書三)
d681329 docs(145): Station 3 紅燈規劃裁決落票(〈十三〉)
ad35008 docs(145): Station 3 紅燈規劃書(只規劃,不寫測試)
```

(這是 `git log --oneline` 的原樣輸出,commit 以 7 碼短 SHA 顯示;它們是清單內容,不是查詢錨點。)

---

## E. 完整 diff

三份 diff 皆為完整輸出、未截斷。diff 內空白的 context 行(單一空格)是 `git diff` 的原樣輸出,
`git diff --check` 會把它們報成 trailing whitespace —— 那是本段的已知形狀,不是編輯錯誤。

### E.1 `git diff origin/master..02a5e28adf5aee11a43d5a1063504f01beb1d67f -- .claude/hooks/redlight.py .claude/portable/status.py tests/conftest.py tests/test_redlight.py tests/test_status.py`

```diff
diff --git a/.claude/hooks/redlight.py b/.claude/hooks/redlight.py
index 01eec85..f4bee43 100644
--- a/.claude/hooks/redlight.py
+++ b/.claude/hooks/redlight.py
@@ -141,3 +141,457 @@ def record_run(test_file, passed, failed_tests):
     except Exception:
         pass
     return rec
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# 票 145(M1-a)—— run 事實:一次 test run 跑了什麼、結果是什麼
+#
+# 上面的 `record_run()` 一筆 = (一個測試檔 × 一次結果),**帳本裡沒有「一次執行」**
+# 這個實體 ⇒ 窄選、全部 skip、0 collected、根本沒跑,在帳本上長得一樣(票 139)。
+# 本段補上那個實體。
+#
+# **另一本帳**(`.dev/test-sessions.jsonl`),不寫進 `test-runs.jsonl`:
+#   - `gate.redlight_missing()`(R3,權威層)逐行讀 `test-runs.jsonl`,
+#     `test_file` 命中而缺 `impl_exists` 就擋 —— 同檔混放會讓 R3 的解析面跟著變;
+#   - 既有 8 欄紀錄**一筆都不改、不補欄位**(票 145〈三〉Backward compatibility 1–4)。
+# 落點由 `root` 參數推出,不由模組常數推出 —— status 依 root 載入本檔讀取,
+# 測試以 tmp root 寫入,三方對同一個 root 說的是同一本帳。
+# ─────────────────────────────────────────────────────────────────────────────
+
+SESSION_LOG_NAME = "test-sessions.jsonl"
+
+COLLECTION_ERROR = "<collection error>"
+
+
+def session_log(root):
+    """`<root>/.dev/test-sessions.jsonl`。"""
+    return os.path.join(os.fspath(root), ".dev", SESSION_LOG_NAME)
+
+
+def _ticket_of(root):
+    """`<root>/.dev/pipeline.json` 的 `ticket_id`。讀不到回 None —— 不猜(同 `current_ticket`)。"""
+    try:
+        with io.open(os.path.join(os.fspath(root), ".dev", "pipeline.json"),
+                     encoding="utf-8") as f:
+            return json.load(f).get("ticket_id")
+    except Exception:
+        return None
+
+
+def _normalize_arg(arg, root, invocation_dir):
+    """一個 pytest 位置參數 → root 相對的 posix 路徑(保留 `::` 之後那段)。
+
+    無法判讀(空字串、落在 root 之外、跨磁碟)⇒ None。**絕對路徑不落帳** ——
+    帳本只存 root 相對路徑,`invocation_dir` 只用來解析,不寫進紀錄。
+    """
+    s = str(arg).replace("\\", "/")
+    path, sep, rest = s.partition("::")
+    if not path:
+        return None
+    base = os.fspath(invocation_dir) if invocation_dir else os.fspath(root)
+    full = path if os.path.isabs(path) else os.path.join(base, path)
+    try:
+        rel = os.path.relpath(os.path.normpath(full), os.path.normpath(os.fspath(root)))
+    except ValueError:
+        return None
+    rel = rel.replace("\\", "/")
+    if rel == ".." or rel.startswith("../"):
+        return None
+    return rel + (sep + rest if sep else "")
+
+
+def _normalize_invocation(root, invocation):
+    """producer 交來的 invocation 事實 → 落帳形狀。不是 dict ⇒ None(涵蓋範圍未知)。"""
+    if not isinstance(invocation, dict):
+        return None
+    args = invocation.get("args")
+    if isinstance(args, (list, tuple)):
+        norm = [_normalize_arg(a, root, invocation.get("invocation_dir")) for a in args]
+    else:
+        norm = None
+    src = invocation.get("args_source")
+    return {
+        "args": norm,
+        "args_source": src if isinstance(src, str) else None,
+        "pyargs": bool(invocation.get("pyargs")),
+    }
+
+
+def record_session(root, run_id=None, time=None, ticket_id=None, exit_code=None,
+                   collected=(), deselected=(), outcomes=None, invocation=None,
+                   completeness=None):
+    """追加一筆 run 事實到 `<root>` 的 session 帳本。回傳寫入的內容。
+
+    - `collected`:本次收集到的身分(含被 deselect 的;收集錯誤以
+      `<檔>::<collection error>` 標記)
+    - `deselected`:被排除的身分;`selected` = collected − deselected
+    - `outcomes`:`{身分: OUTCOME_VALUES 之一}`,只含 selected
+    - `exit_code`:runner 的原始退出碼;取不到為 None
+    - `invocation`:producer 觀察到的呼叫事實 `{"args", "args_source", "invocation_dir",
+      "pyargs"}`(票 145〈十七〉裁決 1 的判定依據);None ⇒ 涵蓋範圍未知
+    - `completeness`:選擇 / 執行完整性事實(票 145〈二十三〉7);不是 dict ⇒ 記 None
+      (涵蓋範圍未知)。producer 負責只放 root 相對路徑與 JSON 原生型別
+
+    `run_id` / `time` / `ticket_id` 為 None 時自取(測試可指定以求決定性)。
+    寫入失敗不拋例外 —— 紀錄器不得弄死執行器(`TestTheRecorderCannotKillTheRunner`)。
+    """
+    import uuid
+    rec = {
+        "kind": "session",
+        "run_id": run_id or uuid.uuid4().hex,
+        "time": time or datetime.now(timezone.utc).isoformat(),
+        "ticket_id": ticket_id if ticket_id is not None else _ticket_of(root),
+        "exit_code": None if exit_code is None else int(exit_code),
+        "collected": [str(n).replace("\\", "/") for n in (collected or ())],
+        "deselected": [str(n).replace("\\", "/") for n in (deselected or ())],
+        "outcomes": {str(k).replace("\\", "/"): v for k, v in (outcomes or {}).items()},
+        "invocation": _normalize_invocation(root, invocation),
+        "completeness": completeness if isinstance(completeness, dict) else None,
+    }
+    path = session_log(root)
+    try:
+        os.makedirs(os.path.dirname(path), exist_ok=True)
+        with io.open(path, "a", encoding="utf-8") as f:
+            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
+    except Exception:
+        pass
+    return rec
+
+
+def load_runs(root):
+    """`<root>` 的 run 事實,依寫入順序。無帳本回 `[]`。
+
+    **任何一行讀不動就整本回 `[]`** —— 讀到一半的帳本會讓「較晚的 run」
+    看起來不存在,而那正是退紅判定最依賴的東西。回 `[]` 的效果是
+    「無 run 證據 / 不可判定」:沒有任何紅可以因此退掉(fail-closed 的方向)。
+    """
+    path = session_log(root)
+    if not os.path.exists(path):
+        return []
+    out = []
+    try:
+        with io.open(path, encoding="utf-8") as f:
+            for line in f:
+                line = line.strip()
+                if not line:
+                    continue
+                rec = json.loads(line)
+                if not isinstance(rec, dict) or not rec.get("run_id"):
+                    return []
+                out.append(rec)
+    except Exception:
+        return []
+    return out
+
+
+# "other" 只為讀得動 Station 4c 之前的 session(當時 xfail / xpass 都記成 other);
+# 4c 之後的 producer 寫 "xfail" / "xpass"。"other" 不算「執行完成」(〈二十三〉7 (vi))。
+OUTCOME_VALUES = ("passed", "failed", "skipped", "xfail", "xpass", "other")
+
+
+def validate_session(run):
+    """一筆 run 事實的 schema 問題清單。**空 list = 合格。**(票 145〈十七〉裁決 3)
+
+    合格的條件(缺一即不合格,**不得**以「缺欄 ⇒ 空集合」或「錯型別照常迭代」處理):
+      - `run_id`、`time` 為非空字串;`ticket_id` 欄位存在(字串或 null)
+      - `exit_code` 欄位存在,為 int(非 bool)或 null
+      - `collected`、`deselected` 為字串 list;`deselected ⊆ collected`
+      - `outcomes` 為 `{字串: OUTCOME_VALUES 之一}`;其鍵 ⊆ selected
+      - `invocation` 若存在且非 null:為 dict,`args` 為 list(元素為字串或 null)或 null
+      - `completeness` 若存在且非 null:為 dict(內部欄位由 `file_coverage` 逐項驗;
+        不合格 ⇒ 涵蓋 `"unknown"`,不讓整筆 run 失去加紅的效果)。沒有這個欄位的舊 session 仍合格
+    """
+    if not isinstance(run, dict):
+        return ["不是物件"]
+    problems = []
+    for key in ("run_id", "time"):
+        v = run.get(key)
+        if not isinstance(v, str) or not v:
+            problems.append("%s 缺欄或非字串" % key)
+    if "ticket_id" not in run:
+        problems.append("ticket_id 缺欄")
+    if "exit_code" not in run:
+        problems.append("exit_code 缺欄")
+    else:
+        ec = run["exit_code"]
+        if ec is not None and (isinstance(ec, bool) or not isinstance(ec, int)):
+            problems.append("exit_code 型別不符")
+    lists = {}
+    for key in ("collected", "deselected"):
+        if key not in run:
+            problems.append("%s 缺欄" % key)
+        elif not isinstance(run[key], list) or not all(isinstance(n, str) for n in run[key]):
+            problems.append("%s 型別不符" % key)
+        else:
+            lists[key] = run[key]
+    outcomes = run.get("outcomes", None)
+    if "outcomes" not in run:
+        problems.append("outcomes 缺欄")
+    elif not isinstance(outcomes, dict) or not all(
+            isinstance(k, str) and v in OUTCOME_VALUES for k, v in outcomes.items()):
+        problems.append("outcomes 型別不符")
+        outcomes = None
+    if "collected" in lists and "deselected" in lists:
+        collected = set(lists["collected"])
+        deselected = set(lists["deselected"])
+        if not deselected <= collected:
+            problems.append("deselected 不屬於 collected")
+        if isinstance(outcomes, dict):
+            stray = sorted(set(outcomes) - (collected - deselected))
+            if stray:
+                problems.append("outcome 身分不屬於 selected:%s" % ", ".join(stray))
+    inv = run.get("invocation")
+    if inv is not None:
+        if not isinstance(inv, dict):
+            problems.append("invocation 型別不符")
+        else:
+            args = inv.get("args")
+            if args is not None and (not isinstance(args, list) or not all(
+                    a is None or isinstance(a, str) for a in args)):
+                problems.append("invocation.args 型別不符")
+    comp = run.get("completeness")
+    if comp is not None and not isinstance(comp, dict):
+        problems.append("completeness 型別不符")
+    return problems
+
+
+def run_state(run):
+    """一個 run 事實的狀態 `"A"`–`"F"`(票 145〈三〉A)。**依序判定,先命中者為準。**
+
+    | 條件 | 狀態 |
+    |---|---|
+    | schema 不合格(`validate_session()` 非空) | INVALID —— 不是 A–F 任何一個 |
+    | exit code 不在 {0, 1, 5}(中斷 / 內部錯誤 / 用法錯誤 / 取不到),或有收集錯誤 | D |
+    | 任一身分 failed | B |
+    | 0 collected | C |
+    | 沒有任何身分 passed(全 skip、全 deselect、或混合) | F |
+    | 其餘(≥1 passed、0 failed) | A |
+
+    **不只看 exit code**:全部 deselected 時 pytest 回 5,但有收集到 ⇒ F,不是 C。
+    E(根本沒跑)沒有 run 事實可以輸入,不在本函式值域內。
+    """
+    if validate_session(run):
+        return "INVALID"
+    ec = run.get("exit_code")
+    collected = run.get("collected") or []
+    outcomes = run.get("outcomes") or {}
+    values = list(outcomes.values())
+    if ec not in (0, 1, 5) or any(str(n).endswith("::" + COLLECTION_ERROR) for n in collected):
+        return "D"
+    if "failed" in values:
+        return "B"
+    if not collected:
+        return "C"
+    if "passed" not in values:
+        return "F"
+    return "A"
+
+
+def file_coverage(run, test_file):
+    """這個 run 對 `test_file` 是否整檔涵蓋:`"true"` / `"false"` / `"unknown"`。
+
+    票 145〈十七〉裁決 1:**只有 producer 能正向證明整檔涵蓋時才為 true;不知道,就不是完整。**
+    依序判定(先命中者為準):
+
+    | 條件 | 結果 |
+    |---|---|
+    | run schema 不合格 | unknown |
+    | 本 run 沒有收集到該檔的任何身分,或該檔有收集錯誤 | unknown |
+    | 該檔有任何 deselected 身分(`-k` / `-m` / `--deselect` / `--lf` 等) | false |
+    | 沒有 invocation 事實、`pyargs`、或 `args` 不是非空 list | unknown |
+    | 某個位置參數是**該檔本身或其上層目錄**、且不含 `::` | true |
+    | 位置參數只以 nodeid(含 `::`)指名該檔 | false |
+    | 其餘(參數無法判讀、或都與該檔無關) | unknown |
+    | 位置參數涵蓋該檔之後:完整性事實(〈二十三〉7)不全部成立 | 見 `_completeness_verdict` |
+
+    **沒有為固定指令另寫分支**:pytest 未給位置參數時以 testpaths 補上
+    `config.args == ["tests"]`,與「位置參數為上層目錄 tests」走同一條規則;
+    完整性事實也一樣 —— 固定全套只是「每一條都剛好成立」的那一種 run。
+    """
+    if validate_session(run):
+        return "unknown"
+    tf = str(test_file).replace("\\", "/")
+    deselected = set(run["deselected"])
+    idents = [n for n in run["collected"] if n.split("::", 1)[0] == tf]
+    if not idents or any(n.endswith("::" + COLLECTION_ERROR) for n in idents):
+        return "unknown"
+    if any(n in deselected for n in idents):
+        return "false"
+    inv = run.get("invocation")
+    if not isinstance(inv, dict) or inv.get("pyargs"):
+        return "unknown"
+    args = inv.get("args")
+    if not isinstance(args, list) or not args:
+        return "unknown"
+    covering = narrowed = False
+    for a in args:
+        if not isinstance(a, str):
+            continue                        # 無法判讀的參數:不證明任何事
+        path, sep, _rest = a.partition("::")
+        if path == tf:
+            if sep:
+                narrowed = True
+            else:
+                covering = True
+        elif not sep and (path == "." or tf.startswith(path.rstrip("/") + "/")):
+            covering = True
+    if covering:
+        return _completeness_verdict(run, tf, idents)
+    if narrowed:
+        return "false"
+    return "unknown"
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# 票 145 Station 4c —— 選擇 / 執行完整性(〈二十三〉)
+#
+# 「沒有 deselected」證明不了選擇完整(`--lf` 在收集期就悄悄移除身分),
+# 「有一筆 report」證明不了已執行(`pytest.exit(returncode=0)` 只留 setup report)。
+# 所以 `"true"` 另外要 producer 的正向事實:選項全部關閉、沒有提前停止、
+# 縮小前全集 == 收集結果、每個 selected 身分都到了執行完成的終態、
+# 本次註冊的每個 plugin 都在受支援範圍(白名單)內。**任一缺欄或型別錯 ⇒ unknown。**
+#
+# 白名單變更須走票(〈二十三〉3)。
+# ─────────────────────────────────────────────────────────────────────────────
+
+COMPLETENESS_OPTIONS = ("lf", "last_failed_no_failures", "stepwise", "stepwise_skip",
+                        "maxfail", "collectonly", "setuponly", "setupplan")
+
+PLUGIN_KINDS = ("builtin", "root_conftest", "known_dist", "other")
+SUPPORTED_PLUGIN_KINDS = ("builtin", "root_conftest", "known_dist")
+BUILTIN_MODULE = "_pytest"
+ROOT_CONFTEST = "tests/conftest.py"
+KNOWN_DISTS = ("anyio",)
+OUTSIDE = "<outside>"
+
+# 「執行完成」的終態:call 的 passed / failed、任何 phase 的 skip、明確辨識的 xfail / xpass。
+# 籠統的 "other"(4c 之前的 xfail 記法)不算 —— 不得讓 other 自動取得 completeness。
+EXECUTED_OUTCOMES = ("passed", "failed", "skipped", "xfail", "xpass")
+
+
+def _dist_name(dist):
+    name = getattr(dist, "project_name", None)
+    if not isinstance(name, str):
+        try:
+            name = dist.metadata["name"]
+        except Exception:
+            name = None
+    return name.strip().lower().replace("_", "-") if isinstance(name, str) else None
+
+
+def _defining_module(plugin):
+    """模組物件看 `__name__`;類別看自己的 `__module__`;其他物件看其類別的 `__module__`。"""
+    import types
+    if isinstance(plugin, types.ModuleType):
+        return getattr(plugin, "__name__", None)
+    if isinstance(plugin, type):
+        return getattr(plugin, "__module__", None)
+    return getattr(type(plugin), "__module__", None)
+
+
+def _plugin_path_name(name, root):
+    """路徑型名稱 → root 相對 posix 路徑;root 以外(含跨磁碟)⇒ `<outside>`。"""
+    try:
+        rel = os.path.relpath(os.path.normpath(name), os.path.normpath(os.fspath(root)))
+    except ValueError:
+        return OUTSIDE
+    rel = rel.replace("\\", "/")
+    if rel == ".." or rel.startswith("../") or os.path.isabs(rel):
+        return OUTSIDE
+    return rel
+
+
+def classify_plugins(root, name_plugins, distinfo):
+    """`list_name_plugin()` 與 `list_plugin_distinfo()` 的原始事實 → `[{"name", "kind"}]`。
+
+    依序判定(〈二十三〉3):
+      1. plugin **物件**出現在 distinfo 配對中 ⇒ dist 名稱在 `KNOWN_DISTS` 為 known_dist,否則 other
+         (只看名稱相同不算 —— 名稱可被冒用)
+      2. 名稱是絕對路徑(conftest 的註冊名稱)⇒ root 相對路徑恰為 `ROOT_CONFTEST` 為 root_conftest,否則 other
+      3. 定義模組為 `_pytest` 或 `_pytest.*` ⇒ builtin
+      4. 其他 ⇒ other
+    帳本只記正規化名稱:路徑型一律轉 root 相對路徑(root 以外記 `<outside>`),不記絕對路徑。
+    """
+    dists = [(p, _dist_name(d)) for p, d in (distinfo or [])]
+    out = []
+    for name, plugin in name_plugins or []:
+        name = str(name)
+        is_path = os.path.isabs(name)
+        shown = _plugin_path_name(name, root) if is_path else name
+        paired = [dn for p, dn in dists if p is plugin]
+        if paired:
+            kind = "known_dist" if all(dn in KNOWN_DISTS for dn in paired) else "other"
+        elif is_path:
+            kind = "root_conftest" if shown == ROOT_CONFTEST else "other"
+        else:
+            mod = _defining_module(plugin)
+            builtin = isinstance(mod, str) and (
+                mod == BUILTIN_MODULE or mod.startswith(BUILTIN_MODULE + "."))
+            kind = "builtin" if builtin else "other"
+        out.append({"name": shown, "kind": kind})
+    return out
+
+
+def _is_str_list(v):
+    return isinstance(v, list) and all(isinstance(n, str) for n in v)
+
+
+def _completeness_problems(comp):
+    """completeness 的型別問題清單(空 = 型別正確)。〈二十三〉7 (i)。"""
+    if not isinstance(comp, dict):
+        return ["completeness 缺欄或型別不符"]
+    problems = []
+    options = comp.get("options")
+    if not isinstance(options, dict) or any(k not in options for k in COMPLETENESS_OPTIONS):
+        problems.append("options 缺欄或型別不符")
+    for key in ("cacheprovider_blocked", "shouldstop", "shouldfail"):
+        if not isinstance(comp.get(key), bool):
+            problems.append("%s 缺欄或型別不符" % key)
+    pre = comp.get("pre_narrowing")
+    if not isinstance(pre, dict) or not all(
+            isinstance(k, str) and _is_str_list(v) for k, v in pre.items()):
+        problems.append("pre_narrowing 缺欄或型別不符")
+    plugins = comp.get("plugins")
+    if not isinstance(plugins, list) or not plugins or not all(
+            isinstance(p, dict) and isinstance(p.get("name"), str)
+            and p.get("kind") in PLUGIN_KINDS for p in plugins):
+        problems.append("plugins 缺欄或型別不符")
+    return problems
+
+
+def _completeness_verdict(run, tf, idents):
+    """位置參數已涵蓋 `tf` 之後,依〈二十三〉7 (i)–(vii) 判 `"true"` / `"false"` / `"unknown"`。
+
+    - (i) 缺欄 / 型別錯 ⇒ unknown
+    - (vii) 有 plugin 不在受支援範圍 ⇒ unknown(在支援邊界之外,不知道)
+    - (ii) `lf` / `stepwise` 生效(除非 cacheprovider 被封鎖)⇒ false(縮小機制作用中)
+    - (iii) maxfail / collectonly / setuponly / setupplan ⇒ unknown
+    - (iv) shouldstop / shouldfail ⇒ unknown
+    - (v) 縮小前全集 != 本 run 該檔的 collected ⇒ false
+    - (vi) 有 selected 身分沒到執行完成的終態 ⇒ unknown
+    """
+    comp = run.get("completeness")
+    if _completeness_problems(comp):
+        return "unknown"
+    if any(p["kind"] not in SUPPORTED_PLUGIN_KINDS for p in comp["plugins"]):
+        return "unknown"
+    options = comp["options"]
+    if comp["cacheprovider_blocked"] is not True:
+        if not (options["lf"] is False and options["stepwise"] is False
+                and options["stepwise_skip"] is False):
+            return "false"
+    maxfail = options["maxfail"]
+    if not (maxfail is None or (type(maxfail) is int and maxfail == 0)):
+        return "unknown"
+    if not all(options[k] is False for k in ("collectonly", "setuponly", "setupplan")):
+        return "unknown"
+    if comp["shouldstop"] is not False or comp["shouldfail"] is not False:
+        return "unknown"
+    pre = comp["pre_narrowing"].get(tf)
+    if pre is None or set(pre) != set(idents):
+        return "false"
+    deselected = set(run["deselected"])
+    outcomes = run["outcomes"]
+    if any(outcomes.get(n) not in EXECUTED_OUTCOMES for n in idents if n not in deselected):
+        return "unknown"
+    return "true"
diff --git a/.claude/portable/status.py b/.claude/portable/status.py
index 5d4ebd1..55e7fcc 100644
--- a/.claude/portable/status.py
+++ b/.claude/portable/status.py
@@ -334,6 +334,236 @@ def _latest_per_file(runs, ticket):
     return out
 
 
+# ─────────────────────────────────────────────────────────────────────────
+# 票 145(M1-a)—— 依 run 事實判定紅綠
+#
+# 上面的 `_latest_per_file()` **保持原語意不動**(「每檔最新一筆」),只是
+# `_evidence` / `_derived` 不再拿它決定紅綠:最新一筆是一次 `-k` 窄選、全部 skip 的
+# 綠時,它會把較早的紅蓋掉(票 139)。紅綠改由 `ticket_test_state()` 依
+# 票 145〈十三〉修訂後的 ODC-1 判定。
+#
+# run 事實由 `<root>/.claude/hooks/redlight.py` 的 `load_runs()` 讀 ——
+# **per-root 載入,與 `load_gate()` 同一手法**(〈十三〉裁決 1);本檔不另寫解析。
+# ─────────────────────────────────────────────────────────────────────────
+
+_REDLIGHT_CACHE = {}
+
+WHOLE_FILE = u"*"          # 身分不明的紅:視同該檔全部 applicable tests 都是先前紅的
+NO_RUN = u"無 run 證據 / 不可判定"
+
+
+def load_redlight(root):
+    """載入 `<root>/.claude/hooks/redlight.py`。不存在或載不起來回 None。
+
+    **None 不進快取** —— 同一個 root 之後才放進 redlight.py 時要讀得到。
+    """
+    real = os.path.realpath(root)
+    if real in _REDLIGHT_CACHE:
+        return _REDLIGHT_CACHE[real]
+    path = os.path.join(real, ".claude", "hooks", "redlight.py")
+    if not os.path.exists(path):
+        return None
+    try:
+        name = "redlight_for_%s" % abs(hash(real))
+        spec = importlib.util.spec_from_file_location(name, path)
+        mod = importlib.util.module_from_spec(spec)
+        spec.loader.exec_module(mod)
+    except Exception:
+        return None
+    _REDLIGHT_CACHE[real] = mod
+    return mod
+
+
+def _run_facts(root):
+    """(run 事實 list, redlight 模組)。redlight 不在 / 無 `load_runs` / 讀失敗 ⇒ (None, None)。"""
+    rl = load_redlight(root)
+    if rl is None or not hasattr(rl, "load_runs"):
+        return None, None
+    try:
+        return rl.load_runs(root), rl
+    except Exception:
+        return None, None
+
+
+def _identity_file(ident):
+    return str(ident).split("::", 1)[0]
+
+
+def _whole(f):
+    return u"%s::%s" % (f, WHOLE_FILE)
+
+
+def _red_identities_of_row(rec):
+    """一筆舊格式 red 紀錄指名的身分。`failed_tests` 缺欄、為空、或含收集錯誤 ⇒ 身分不明。"""
+    f = rec.get("test_file")
+    names = rec.get("failed_tests")
+    if (not isinstance(names, list) or not names
+            or any(n == u"<collection error>" for n in names)):
+        return {_whole(f)}
+    return {u"%s::%s" % (f, n) for n in names}
+
+
+_RL_FUNCS = ("validate_session", "run_state", "file_coverage")
+
+
+def _rl_ready(rl):
+    """這份 redlight 有沒有判定所需的三個函式(舊版下游沒有 ⇒ 一律當涵蓋未知)。"""
+    return rl is not None and all(hasattr(rl, n) for n in _RL_FUNCS)
+
+
+def _apply_run(run, red, orphan, green_now, rl=None):
+    """一個 run 事實對每個檔的影響(就地更新三個 dict)。
+
+    **schema 不合格的 run 不產生任何效果**(〈十七〉裁決 3)—— 不加紅、不退紅、
+    不 orphan、不 green;它的存在由 `_evidence` 另行顯示(不靜默丟棄)。
+
+    合格的 run:
+      - 該檔有 failure 或收集錯誤 ⇒ 加紅(收集錯誤 ⇒ 身分不明的整檔紅),不 green。
+      - `run_state == "D"` ⇒ **整個 run 沒有退紅權、不得使任何檔成為 green**(裁決 2)。
+      - 退紅 / orphan / green **只在 `file_coverage(run, f) == "true"` 時進行**(裁決 1):
+        退紅(〈十三〉ODC-1)—— 已知紅身分本次 passed;身分不明時該檔全部 collected 身分 passed;
+        孤兒(ODC-2)—— 整檔涵蓋的 run 收集不到某已知紅身分 ⇒ 移到 orphan,不退紅;
+        同名身分再被收集到 ⇒ 移回紅。改名不視為延續。
+      - `rl` 為 None 或缺函式 ⇒ 無法判定涵蓋 ⇒ 只加紅,不退紅、不 orphan、不 green。
+    """
+    ready = _rl_ready(rl)
+    if ready and rl.validate_session(run):
+        return
+    collected = run.get("collected")
+    deselected = run.get("deselected")
+    outcomes = run.get("outcomes")
+    if (not isinstance(collected, list) or not isinstance(deselected, list)
+            or not isinstance(outcomes, dict)):
+        return
+    deselected = set(str(n) for n in deselected)
+    state = rl.run_state(run) if ready else None
+    by_file = {}
+    for n in collected:
+        by_file.setdefault(_identity_file(n), []).append(str(n))
+    for f, idents in by_file.items():
+        errored = any(n.endswith(u"::<collection error>") for n in idents)
+        selected = [n for n in idents if n not in deselected]
+        if not selected and not errored:
+            continue                    # 整檔被排除:這次 run 沒有碰它,證據不變
+        results = [outcomes.get(n) for n in selected]
+        if errored or u"failed" in results:
+            mine = red.setdefault(f, set())
+            mine.update(n for n in selected if outcomes.get(n) == u"failed")
+            if errored:
+                mine.add(_whole(f))
+            green_now[f] = False
+            continue
+        if not ready or state == u"D" or rl.file_coverage(run, f) != u"true":
+            green_now[f] = False
+            continue
+        present = set(idents)
+        back = set(n for n in orphan.get(f, ()) if n in present)
+        if back:
+            red.setdefault(f, set()).update(back)
+            orphan[f] -= back
+        gone = set(n for n in red.get(f, ())
+                   if not n.endswith(u"::" + WHOLE_FILE) and n not in present)
+        if gone:
+            red[f] -= gone
+            orphan.setdefault(f, set()).update(gone)
+        if red.get(f):
+            if any(n.endswith(u"::" + WHOLE_FILE) for n in red[f]):
+                if all(outcomes.get(n) == u"passed" for n in idents):
+                    red[f] = set()
+            else:
+                red[f] = set(n for n in red[f] if outcomes.get(n) != u"passed")
+        green_now[f] = u"passed" in results
+
+
+def ticket_test_state(records, runs, ticket, rl=None):
+    """這張票底下每個測試檔的狀態。**純函式,不讀檔。**
+
+    回傳 `{test_file: {"state": "red" | "green" | "unknown" | "orphaned",
+                       "unresolved": [身分...], "orphaned": [身分...]}}`。
+
+    - `records`:`test-runs.jsonl` 的 8 欄紀錄;`runs`:`load_runs()` 的 run 事實。
+    - 兩者依 `time` 排序後依序套用;同一時點 run 事實排在紀錄**之後**
+      (producer 在同一個 session 先寫逐檔紀錄、最後寫 run 事實)。
+    - **8 欄紀錄沒有 run 事實 ⇒ coverage 未知**:red 紀錄加紅,green 紀錄**不退任何紅**,
+      且不能讓該檔變成 green(只到 `unknown`)—— Backward compatibility 2。
+    - `green` 只來自最新一次碰到該檔的 run:schema 合格、非 D、對該檔整檔涵蓋(`"true"`)、
+      該檔 ≥1 passed、0 failed。
+    - `rl`:該 root 的 redlight 模組(提供 `validate_session` / `run_state` / `file_coverage`);
+      None ⇒ 涵蓋一律未知(只加紅、不退紅)。
+    """
+    if not ticket:
+        return {}
+    events = []
+    for i, rec in enumerate(records or []):
+        if (not isinstance(rec, dict) or rec.get("ticket_id") != ticket
+                or not rec.get("test_file")):
+            continue
+        events.append((str(rec.get("time") or u""), 0, i, rec, None))
+    for i, run in enumerate(runs or []):
+        if not isinstance(run, dict) or run.get("ticket_id") != ticket:
+            continue
+        events.append((str(run.get("time") or u""), 1, i, None, run))
+    events.sort(key=lambda e: e[:3])
+
+    red, orphan, green_now = {}, {}, {}
+    for _t, _o, _i, rec, run in events:
+        if rec is not None:
+            f = rec["test_file"]
+            if rec.get("result") == u"red":
+                red.setdefault(f, set()).update(_red_identities_of_row(rec))
+            green_now[f] = False
+            continue
+        _apply_run(run, red, orphan, green_now, rl)
+
+    out = {}
+    for f in set(red) | set(orphan) | set(green_now):
+        r = sorted(red.get(f, ()))
+        o = sorted(orphan.get(f, ()))
+        if r:
+            state = u"red"
+        elif o:
+            state = u"orphaned"
+        elif green_now.get(f):
+            state = u"green"
+        else:
+            state = u"unknown"
+        out[f] = {u"state": state, u"unresolved": r, u"orphaned": o}
+    return out
+
+
+def _last_run_text(facts, rl, ticket):
+    """本票最近一次 run 的一句話。找不到 ⇒ `無 run 證據 / 不可判定`。"""
+    mine = [r for r in (facts or []) if isinstance(r, dict) and r.get("ticket_id") == ticket]
+    if not mine or rl is None or not hasattr(rl, "run_state"):
+        return NO_RUN
+    r = mine[-1]
+    problems = rl.validate_session(r) if hasattr(rl, "validate_session") else []
+    if problems:
+        # 不合格的 run:不顯示成 A–F 任何一個,也不從它算計數(錯型別不得照常迭代)
+        return u"INVALID(schema 不合格:%s)" % u";".join(problems)
+    outs = list((r.get("outcomes") or {}).values())
+    return u"%s(exit %s;collected %d / deselected %d / passed %d / failed %d / skipped %d)" % (
+        rl.run_state(r), r.get("exit_code"), len(r.get("collected") or []),
+        len(r.get("deselected") or []), outs.count(u"passed"), outs.count(u"failed"),
+        outs.count(u"skipped"))
+
+
+def _invalid_count(facts, rl, ticket):
+    """本票 schema 不合格的 run 筆數。無法驗證(舊版 redlight)⇒ 0。"""
+    if rl is None or not hasattr(rl, "validate_session"):
+        return 0
+    return len([r for r in (facts or [])
+                if isinstance(r, dict) and r.get("ticket_id") == ticket
+                and rl.validate_session(r)])
+
+
+def _run_source(root, run_log, rl):
+    left = _rel(root, run_log) if run_log else NO_FUNC
+    right = (_rel(root, rl.session_log(root)) if rl is not None and hasattr(rl, "session_log")
+             else u"%s(redlight.py 無 run 事實讀取)" % UNRECORDED)
+    return u"%s + %s" % (left, right)
+
+
 def _waterline_commits(recs):
     """provenance 的**水位線**:每個 `path` 最新一筆憑證的 commit,去重(票 100)。
 
@@ -592,23 +822,30 @@ def _evidence(root, gate, ticket):
     # 同一個問題在同一支檔案裡有兩種答案時,讀的人會以為那是刻意的區別。
     # 無票時**不得**印帶「本票」字樣的數字 —— 那不是缺值,是一個錯的宣稱,
     # 而帶著票面語氣的數字,讀的人會直接引用。
-    if runs is None:
+    # 票 145:紅綠改由 `ticket_test_state()` 判定(ODC-1);尾段由「全套結果:未記錄
+    # (帳本不記全套)」改為本票最近一次 run 的事實。**兩本帳都沒有 ⇒ 照舊整行未記錄。**
+    facts, rl = _run_facts(root)
+    if runs is None and not facts:
         val = UNRECORDED
     elif not ticket:
         val = u"%s(無當前票)" % UNRECORDED
     else:
-        latest = _latest_per_file(runs, ticket)
-        red = len([r for r in latest.values() if r.get("result") == "red"])
-        green = len([r for r in latest.values() if r.get("result") == "green"])
+        st = ticket_test_state(runs or [], facts or [], ticket, rl)
+        n = {k: len([1 for s in st.values() if s[u"state"] == k])
+             for k in (u"red", u"green", u"unknown", u"orphaned")}
         last = runs[-1] if runs else None
         tail = (u"最後一筆 %s=%s @ %s" % (_field(last, "test_file"),
                                           _field(last, "result"),
                                           _field(last, "time"))
-                if last else UNRECORDED)
-        val = u"本票(每檔最新一筆)red %d / green %d;%s;全套結果:%s(帳本不記全套)" % (
-            red, green, tail, UNRECORDED)
-    out.append(_line(u"test-runs", val,
-                     _rel(root, run_log) if run_log else NO_FUNC))
+                if last else u"最後一筆 %s" % UNRECORDED)
+        # 票 145 Station 4b:schema 不合格的 run 不進正常語意,但**不靜默丟棄** ——
+        # 筆數留在這一行,最近一次若不合格則尾段顯示 INVALID(…)(〈十七〉裁決 3)。
+        val = (u"本票 red %d / green %d / run 事實未知 %d / orphaned %d / schema 不合格 run %d;"
+               u"%s;最近一次 run:%s") % (
+            n[u"red"], n[u"green"], n[u"unknown"], n[u"orphaned"],
+            _invalid_count(facts, rl, ticket), tail,
+            _last_run_text(facts, rl, ticket))
+    out.append(_line(u"test-runs", val, _run_source(root, run_log, rl)))
 
     # ── intercepts 印**兩行**,不是一行 ────────────────────────────────
     # 合成一行的話,「這個月還沒有人被擋」與「這個 repo 從來沒有攔截紀錄」
@@ -793,17 +1030,24 @@ def _derived(root, gate, stage, ticket):
 
     run_log = _p(gate, "RUN_LOG")
     runs = _read_jsonl(run_log) if run_log else None
-    if runs is None or not ticket:
-        red = green = UNRECORDED
+    facts, rl = _run_facts(root)
+    labels = ((u"red", u"tests red under ticket %s"),
+              (u"green", u"tests green under ticket %s"),
+              (u"unknown", u"tests green (run 事實未知) under ticket %s"),
+              (u"orphaned", u"tests orphaned under ticket %s"))
+    vals = {}
+    if (runs is None and not facts) or not ticket:
+        vals = dict((k, UNRECORDED) for k, _l in labels)
     else:
-        latest = _latest_per_file(runs, ticket)
-        reds = sorted(f for f, r in latest.items() if r.get("result") == "red")
-        greens = sorted(f for f, r in latest.items() if r.get("result") == "green")
-        red = u" / ".join(reds) if reds else u"(無)"
-        green = u" / ".join(greens) if greens else u"(無)"
-    src = (u"%s 每檔最新一筆" % _rel(root, run_log)) if run_log else NO_FUNC
-    out.append(_line(u"tests red under ticket %s" % (ticket or UNRECORDED), red, src))
-    out.append(_line(u"tests green under ticket %s" % (ticket or UNRECORDED), green, src))
+        st = ticket_test_state(runs or [], facts or [], ticket, rl)
+        for k, _l in labels:
+            files = sorted(f for f, s in st.items() if s[u"state"] == k)
+            if k == u"orphaned":
+                files = [u"%s(%s)" % (f, u", ".join(st[f][u"orphaned"])) for f in files]
+            vals[k] = u" / ".join(files) if files else u"(無)"
+    src = u"%s(票 145 ODC-1)" % _run_source(root, run_log, rl)
+    for k, label in labels:
+        out.append(_line(label % (ticket or UNRECORDED), vals[k], src))
 
     if not _has(gate, "rule_codes"):
         rules = NO_FUNC
diff --git a/tests/conftest.py b/tests/conftest.py
index 7c163e7..bb8e498 100644
--- a/tests/conftest.py
+++ b/tests/conftest.py
@@ -136,6 +136,16 @@ except Exception:
 
 _outcomes = {}
 
+# 票 145(M1-a):run 層級的事實 —— 這一次 session 收集了什麼、排除了什麼、
+# 每個身分的結果、退出碼。上面的 `_outcomes` 是逐檔的(餵 `record_run`,R3 用),
+# 這裡是逐身分的(餵 `record_session`,status 的退紅判定用)。兩份**並存**,
+# 不互相推導:逐檔那份的語意(「這個檔這次有沒有失敗」)一個字都不改。
+_run = {"selected": None, "deselected": [], "collect_errors": [], "outcomes": {}}
+
+
+def _nodeid(obj):
+    return str(getattr(obj, "nodeid", "") or "").replace("\\", "/")
+
 
 def pytest_collectreport(report):
     """收集錯誤也算紅燈。
@@ -149,6 +159,48 @@ def pytest_collectreport(report):
     f = str(getattr(report, "nodeid", "")).split("::", 1)[0].replace("\\", "/")
     if f.endswith(".py"):
         _outcomes.setdefault(f, {"failed": []})["failed"].append("<collection error>")
+    # 票 145:收集錯誤也是 run 事實(狀態 D 的來源之一)。不限 .py ——
+    # conftest 或目錄層級的收集錯誤一樣讓這次 run 不可信。
+    _run["collect_errors"].append("%s::<collection error>" % (f or "<session>"))
+
+
+def pytest_deselected(items):
+    """票 145:被 `-k` / `-m` / `--deselect` 排除的身分。
+
+    **deselect 不產生任何 report**(RECON 二.2 B2)—— 不在這裡記,
+    事後就看不出那一次的涵蓋範圍有多窄(票 139 的 645 deselected)。
+    """
+    if _redlight is None:
+        return
+    _run["deselected"].extend(_nodeid(i) for i in items)
+
+
+def pytest_collection_finish(session):
+    """票 145:deselect 之後真正要跑的身分(= selected)。"""
+    if _redlight is None:
+        return
+    _run["selected"] = [_nodeid(i) for i in getattr(session, "items", None) or []]
+
+
+def _run_outcome(report):
+    """一份 report 對「這個身分的結果」的貢獻。回 None 表示這份 report 不改變結果。
+
+    **屬性一律帶預設值讀** —— 既有測試的假 report 只有 `when` / `failed` /
+    `nodeid` / `fspath`;直接讀 `report.skipped` 會讓它們 AttributeError
+    (紅燈規劃書一、B-1 約束 4)。
+    """
+    if getattr(report, "failed", False):
+        return "failed"
+    # 票 145 Station 4c:xfail / xpass 明確辨識(〈二十三〉7 (vi)),不再籠統記成 other ——
+    # other 不算「執行完成」,而 xfail(skipped + wasxfail)與 non-strict xpass(call passed +
+    # wasxfail)都是測試確實跑完的終態。strict xpass 是 failed,上面已處理。
+    xfail = getattr(report, "wasxfail", None) is not None
+    when = getattr(report, "when", None)
+    if getattr(report, "skipped", False):
+        return "xfail" if xfail else "skipped"
+    if when == "call" and getattr(report, "passed", False):
+        return "xpass" if xfail else "passed"
+    return None
 
 
 def pytest_runtest_logreport(report):
@@ -163,6 +215,11 @@ def pytest_runtest_logreport(report):
     rec = _outcomes.setdefault(f, {"failed": []})
     if report.failed:
         rec["failed"].append(report.nodeid.split("::", 1)[-1])
+    # 票 145:逐身分的結果。`failed` 一旦記下就不被後來的 report 蓋掉
+    # (teardown 失敗之前的 call 可能是 passed)。
+    got = _run_outcome(report)
+    if got is not None and _run["outcomes"].get(_nodeid(report)) != "failed":
+        _run["outcomes"][_nodeid(report)] = got
 
 
 def pytest_sessionfinish(session, exitstatus):
@@ -170,3 +227,115 @@ def pytest_sessionfinish(session, exitstatus):
         return
     for f, rec in _outcomes.items():
         _redlight.record_run(f, passed=not rec["failed"], failed_tests=rec["failed"])
+    # 票 145:**每個 session 恰好一筆 run 事實**,寫在逐檔紀錄**之後** ——
+    # 0 collected、全部 deselected、invocation 錯誤時上面的迴圈一筆都不寫
+    # (RECON Collapse ①),這一筆是那些情形唯一留下的痕跡。
+    # 舊版 redlight.py(下游未同步)沒有 record_session ⇒ 照舊只寫逐檔紀錄。
+    if not hasattr(_redlight, "record_session"):
+        return
+    selected = _run["selected"] if _run["selected"] is not None else list(_run["outcomes"])
+    kwargs = dict(
+        exit_code=exitstatus,
+        collected=list(selected) + list(_run["deselected"]) + list(_run["collect_errors"]),
+        deselected=list(_run["deselected"]),
+        outcomes=dict(_run["outcomes"]),
+    )
+    # 票 145 Station 4b:涵蓋範圍的判定依據(〈十七〉裁決 1)—— pytest 實際收到的
+    # 位置參數與它們的來源。沒有 config ⇒ None ⇒ 涵蓋範圍未知(不知道,就不是完整)。
+    # 舊版 redlight.py 的 record_session 沒有 `invocation` 參數 ⇒ 照舊不傳。
+    import inspect as _inspect
+    params = _inspect.signature(_redlight.record_session).parameters
+    if "invocation" in params:
+        kwargs["invocation"] = _invocation_of(session)
+    # 票 145 Station 4c:選擇 / 執行完整性事實(〈二十三〉7)。收集失敗 ⇒ None ⇒ 涵蓋未知。
+    if "completeness" in params:
+        kwargs["completeness"] = _completeness_of(session)
+    _redlight.record_session(_ROOT, **kwargs)
+
+
+def _invocation_of(session):
+    """session 的呼叫事實:`config.args`、`args_source`、`invocation_params.dir`、`option.pyargs`。
+
+    屬性一律帶預設值讀;沒有 config ⇒ None。
+    """
+    cfg = getattr(session, "config", None)
+    if cfg is None:
+        return None
+    args = getattr(cfg, "args", None)
+    src = getattr(cfg, "args_source", None)
+    params = getattr(cfg, "invocation_params", None)
+    inv_dir = getattr(params, "dir", None) if params is not None else None
+    option = getattr(cfg, "option", None)
+    return {
+        "args": list(args) if isinstance(args, (list, tuple)) else None,
+        "args_source": getattr(src, "name", None) if src is not None else None,
+        "invocation_dir": os.fspath(inv_dir) if inv_dir is not None else None,
+        "pyargs": bool(getattr(option, "pyargs", False)),
+    }
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# 票 145 Station 4c:選擇 / 執行完整性事實(〈二十三〉7)
+#
+# **縮小前全集**:`--lf` 在外層 wrapper(`LFPluginCollWrapper`)裡就地改寫 collector 的
+# `report.result`,不發 deselected 通知。本 wrapper 標 trylast ⇒ 在 wrapper 鏈的最內層,
+# `yield` 之後最先拿到 report,當下**複製** nodeid(之後的就地改寫碰不到這份)。
+# 記的是 report 裡的 `pytest.Item`:File collector 的直接子項,以及 Class 之類子 collector 的子項 ——
+# class 內的測試不在 File 的 report 裡,只記 File 的話 class 型測試檔的全集永遠對不上。
+#
+# 存在 `_run` 之外:既有的測試 driver 會在驅動前清空 `_run` 的每個值。
+# 收集出錯 ⇒ `_pre_narrowing_broken` ⇒ 本次 completeness 不寫(涵蓋未知)。
+# ─────────────────────────────────────────────────────────────────────────────
+
+_pre_narrowing = {}
+_pre_narrowing_broken = []
+
+
+@pytest.hookimpl(wrapper=True, trylast=True)
+def pytest_make_collect_report(collector):
+    report = yield
+    try:
+        if _redlight is not None:
+            for node in list(getattr(report, "result", None) or []):
+                if isinstance(node, pytest.Item):
+                    nodeid = _nodeid(node)
+                    _pre_narrowing.setdefault(nodeid.split("::", 1)[0], []).append(nodeid)
+    except Exception:
+        _pre_narrowing_broken.append(True)
+    return report
+
+
+def _plain(value):
+    """config.option 的值照原樣記;不是 JSON 原生型別的,記型別名(寫不出來就整筆 session 遺失)。"""
+    if value is None or isinstance(value, (bool, int, float, str)):
+        return value
+    return "<%s>" % type(value).__name__
+
+
+def _flag(session, name):
+    """session 結束時的 shouldstop / shouldfail → bool;屬性不存在 ⇒ None(缺欄 ⇒ 涵蓋未知)。"""
+    if not hasattr(session, name):
+        return None
+    return bool(getattr(session, name))
+
+
+def _completeness_of(session):
+    """本次 session 的完整性事實。任何一步出錯 ⇒ None(寧可多紅,不讓 pytest 失敗)。"""
+    try:
+        if _pre_narrowing_broken:
+            return None
+        cfg = session.config
+        option = cfg.option
+        pm = cfg.pluginmanager
+        return {
+            "options": dict((k, _plain(getattr(option, k, None)))
+                            for k in _redlight.COMPLETENESS_OPTIONS),
+            "cacheprovider_blocked": bool(pm.is_blocked("cacheprovider")),
+            "shouldstop": _flag(session, "shouldstop"),
+            "shouldfail": _flag(session, "shouldfail"),
+            "pre_narrowing": dict((f, list(ids)) for f, ids in _pre_narrowing.items()),
+            "plugins": _redlight.classify_plugins(_ROOT, pm.list_name_plugin(),
+                                                  pm.list_plugin_distinfo()),
+        }
+    except Exception:
+        return None
diff --git a/tests/test_redlight.py b/tests/test_redlight.py
index 63a68a8..efb3600 100644
--- a/tests/test_redlight.py
+++ b/tests/test_redlight.py
@@ -226,3 +226,838 @@ class TestTheRecorderCannotKillTheRunner:
         c.pytest_runtest_logreport(r)
         assert c._outcomes.get("tests/test_thing.py", {}).get("failed"), \
             "setup 失敗沒被記成紅燈"
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# 票 145(M1-a)Station 3 紅燈 —— run 事實(producer 側)
+#
+# 觀察契約:docs/audits/2026-10-02-m1a-station3-redlight-plan.md 一、A,
+# 經票 145〈十三〉裁決修正。
+#
+# **新介面(`load_runs` / `run_state`)只在測試函式內部取用**,不在模組層 ——
+# 它們不存在時只有這幾支失敗,不會讓整個檔收集錯誤、拖垮上面既有的測試。
+#
+# **隔離**:conftest 模組載入時會自己載一份 redlight.py,而那一份的 RUN_LOG
+# 指向真實帳本(`tests/conftest.py:129-133`)。驅動前一律把 conftest 的
+# `_redlight` 換成本檔這一份、並把路徑指到 tmp —— 少一個,假紀錄就會寫進真實帳本。
+# ─────────────────────────────────────────────────────────────────────────────
+
+
+class _Item:
+    def __init__(self, nodeid):
+        self.nodeid = nodeid
+
+
+class _CollectRep:
+    def __init__(self, nodeid, failed=False):
+        self.nodeid = nodeid
+        self.failed = failed
+        self.passed = not failed
+        self.outcome = "failed" if failed else "passed"
+
+
+class _RunRep:
+    def __init__(self, nodeid, when, outcome):
+        self.nodeid = nodeid
+        self.fspath = nodeid.split("::", 1)[0]
+        self.when = when
+        self.outcome = outcome
+        self.passed = outcome == "passed"
+        self.failed = outcome == "failed"
+        self.skipped = outcome == "skipped"
+
+
+def _reports_for(nodeid, outcome):
+    """一條測試在 pytest 裡實際產生的 report 序列。
+
+    passed / failed:setup → call → teardown;skipped:setup(skipped)→ teardown,
+    **沒有 call**(skip 在 setup 階段就決定了)。
+    """
+    if outcome == "skipped":
+        return [_RunRep(nodeid, "setup", "skipped"),
+                _RunRep(nodeid, "teardown", "passed")]
+    return [_RunRep(nodeid, "setup", "passed"),
+            _RunRep(nodeid, "call", outcome),
+            _RunRep(nodeid, "teardown", "passed")]
+
+
+class _Session:
+    def __init__(self, items):
+        self.items = list(items)
+        self.testscollected = len(self.items)
+
+
+def _isolated_conftest(monkeypatch, tmp_path):
+    c = TestTheRecorderCannotKillTheRunner._conftest()
+    monkeypatch.setattr(redlight, "ROOT", str(tmp_path))
+    monkeypatch.setattr(redlight, "RUN_LOG",
+                        str(tmp_path / ".dev" / "test-runs.jsonl"))
+    monkeypatch.setattr(redlight, "PIPELINE",
+                        str(tmp_path / ".dev" / "pipeline.json"))
+    monkeypatch.setattr(c, "_redlight", redlight)
+    monkeypatch.setattr(c, "_ROOT", tmp_path)
+    c._outcomes.clear()
+    return c
+
+
+def _drive_session(c, collect_files=(), collect_errors=(), selected=(),
+                   deselected=(), outcomes=None, exitstatus=0):
+    """依 pytest 的實際呼叫順序,對 conftest 呼叫**標準 hook 名稱**。
+
+    conftest 沒實作的 hook 以 no-op 跳過 —— 測試不依賴 producer 用了哪幾個 hook
+    (那是 Station 4 的實體決定)。
+    """
+    def hook(name):
+        return getattr(c, name, None) or (lambda *a, **k: None)
+
+    for f in collect_files:
+        hook("pytest_collectreport")(_CollectRep(f))
+    for f in collect_errors:
+        hook("pytest_collectreport")(_CollectRep(f, failed=True))
+    items = [_Item(n) for n in selected]
+    gone = [_Item(n) for n in deselected]
+    if gone:
+        hook("pytest_deselected")(gone)
+    session = _Session(items)
+    hook("pytest_collection_finish")(session)
+    for nodeid, outcome in (outcomes or {}).items():
+        for rep in _reports_for(nodeid, outcome):
+            hook("pytest_runtest_logreport")(rep)
+    hook("pytest_sessionfinish")(session, exitstatus)
+
+
+class TestRunFacts:
+
+    def test_a_full_pass_is_state_a_with_coverage_visible(self, tmp_path, monkeypatch):
+        """RL-1 Full pass。現行 HEAD:**介面紅**(`redlight.load_runs` 不存在)。"""
+        c = _isolated_conftest(monkeypatch, tmp_path)
+        ids = ["tests/test_thing.py::test_a", "tests/test_thing.py::test_b"]
+        _drive_session(c, collect_files=["tests/test_thing.py"], selected=ids,
+                       outcomes={ids[0]: "passed", ids[1]: "passed"}, exitstatus=0)
+        runs = redlight.load_runs(str(tmp_path))
+        assert len(runs) == 1, runs
+        assert redlight.run_state(runs[0]) == "A", runs[0]
+        assert sorted(runs[0]["collected"]) == sorted(ids), runs[0]
+        assert list(runs[0]["deselected"]) == [], runs[0]
+
+    def test_one_failure_is_state_b_and_names_the_test(self, tmp_path, monkeypatch):
+        """RL-2 One failure。現行 HEAD:**介面紅**(`redlight.load_runs` 不存在)。"""
+        c = _isolated_conftest(monkeypatch, tmp_path)
+        ids = ["tests/test_thing.py::test_a", "tests/test_thing.py::test_b"]
+        _drive_session(c, collect_files=["tests/test_thing.py"], selected=ids,
+                       outcomes={ids[0]: "passed", ids[1]: "failed"}, exitstatus=1)
+        runs = redlight.load_runs(str(tmp_path))
+        assert len(runs) == 1, runs
+        assert redlight.run_state(runs[0]) == "B", runs[0]
+        assert runs[0]["outcomes"][ids[1]] == "failed", runs[0]
+
+    def test_zero_collected_is_state_c_and_the_run_is_visible(self, tmp_path, monkeypatch):
+        """RL-3 Zero tests collected。現行 HEAD:**介面紅**(`redlight.load_runs` 不存在)。
+
+        底層行為缺口:HEAD 對此情形一筆都不寫(`conftest.py:171-172` 迴圈 0 次),
+        與「根本沒跑」不可分 —— 修後必須留下一筆 run 事實。
+        """
+        c = _isolated_conftest(monkeypatch, tmp_path)
+        _drive_session(c, exitstatus=5)
+        runs = redlight.load_runs(str(tmp_path))
+        assert len(runs) == 1, u"0 collected 的 run 沒有留下事實,與 E 不可分:%r" % runs
+        assert redlight.run_state(runs[0]) == "C", runs[0]
+
+    def test_a_collection_error_is_state_d(self, tmp_path, monkeypatch):
+        """RL-4(a) Collection failure。現行 HEAD:**介面紅**(`redlight.load_runs` 不存在)。"""
+        c = _isolated_conftest(monkeypatch, tmp_path)
+        _drive_session(c, collect_errors=["tests/test_broken.py"], exitstatus=2)
+        runs = redlight.load_runs(str(tmp_path))
+        assert len(runs) == 1, runs
+        assert redlight.run_state(runs[0]) == "D", runs[0]
+
+    def test_a_usage_error_is_state_d_not_green(self, tmp_path, monkeypatch):
+        """RL-4(b) Runner invocation error。現行 HEAD:**介面紅**(`redlight.load_runs` 不存在)。
+
+        producer 本身沒被載入的子情形不在這裡 —— 那是 ODC-3(見 tests/test_status.py)。
+        """
+        c = _isolated_conftest(monkeypatch, tmp_path)
+        _drive_session(c, exitstatus=4)
+        runs = redlight.load_runs(str(tmp_path))
+        assert len(runs) == 1, runs
+        assert redlight.run_state(runs[0]) == "D", runs[0]
+
+    def test_an_interrupted_run_is_state_d_even_with_passes(self, tmp_path, monkeypatch):
+        """RL-4(c) 執行被中斷。現行 HEAD:**介面紅**(`redlight.load_runs` 不存在)。
+
+        中斷前已有一條通過 —— 那不得讓這個 run 變成 A。
+        """
+        c = _isolated_conftest(monkeypatch, tmp_path)
+        ids = ["tests/test_thing.py::test_a", "tests/test_thing.py::test_b"]
+        _drive_session(c, collect_files=["tests/test_thing.py"], selected=ids,
+                       outcomes={ids[0]: "passed"}, exitstatus=2)
+        runs = redlight.load_runs(str(tmp_path))
+        assert len(runs) == 1, runs
+        assert redlight.run_state(runs[0]) == "D", runs[0]
+
+    def test_three_skipped_645_deselected_is_state_f_with_counts(self, tmp_path, monkeypatch):
+        """RL-6' 票 139 現場重現(producer 側)。現行 HEAD:**介面紅**(`redlight.load_runs` 不存在)。
+
+        `-k "symlink"` 的形狀:選到 3 條、全部 skip,645 條 deselected,0 passed、0 failed。
+        """
+        c = _isolated_conftest(monkeypatch, tmp_path)
+        chosen = ["tests/test_gate.py::test_symlink_%d" % i for i in range(3)]
+        gone = ["tests/test_gate.py::test_other_%d" % i for i in range(645)]
+        _drive_session(c, collect_files=["tests/test_gate.py"], selected=chosen,
+                       deselected=gone,
+                       outcomes={n: "skipped" for n in chosen}, exitstatus=0)
+        runs = redlight.load_runs(str(tmp_path))
+        assert len(runs) == 1, runs
+        run = runs[0]
+        assert redlight.run_state(run) == "F", run
+        assert len(run["deselected"]) == 645, len(run["deselected"])
+        assert [v for v in run["outcomes"].values()].count("skipped") == 3, run["outcomes"]
+        assert "passed" not in run["outcomes"].values(), run["outcomes"]
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# 票 145 Station 3b 紅燈 —— coverage authority(F3)與 session schema(F1)
+#
+# 依據:票 145〈十七〉裁決 1(full_file_coverage ∈ {true, false, unknown},
+# 只有 producer 能正向證明整檔涵蓋時才為 true)、裁決 3(schema fail-closed)。
+#
+# **新介面 `redlight.file_coverage(run, test_file)` 只在測試函式內部取用。**
+# producer 以 pytest 實際的位置參數(`session.config.args`)判斷窄選;
+# 這裡以帶 `config` 的假 session 模擬 —— 屬性照真實 pytest 的名字給
+# (`args`、`rootpath`、`invocation_params.dir`、`option.pyargs`、`getoption`)。
+# ─────────────────────────────────────────────────────────────────────────────
+
+
+class _InvocationParams:
+    def __init__(self, d):
+        self.dir = d
+
+
+class _Option:
+    pyargs = False
+
+
+class _Config:
+    def __init__(self, args, root):
+        self.args = list(args)
+        self.rootpath = root
+        self.invocation_params = _InvocationParams(root)
+        self.option = _Option()
+
+    def getoption(self, name, default=None):
+        return getattr(self.option, name, default)
+
+
+class _SessionWithConfig(_Session):
+    def __init__(self, items, args, root, with_config=True):
+        _Session.__init__(self, items)
+        if with_config:
+            self.config = _Config(args, root)
+
+
+def _reset_conftest_state(c):
+    """每次驅動前把 conftest 模組的累積狀態歸零(避免案例互相污染)。"""
+    c._outcomes.clear()
+    run = getattr(c, "_run", None)
+    if isinstance(run, dict):
+        for k, v in list(run.items()):
+            if hasattr(v, "clear"):
+                v.clear()
+            else:
+                run[k] = None
+
+
+def _drive_with_args(c, root, args, selected=(), deselected=(), outcomes=None,
+                     exitstatus=0, with_config=True):
+    """同 `_drive_session`,但 session 帶 `config.args`(pytest 實際收到的位置參數)。"""
+    def hook(name):
+        return getattr(c, name, None) or (lambda *a, **k: None)
+
+    _reset_conftest_state(c)
+    files = sorted(set(n.split("::", 1)[0] for n in list(selected) + list(deselected)))
+    for f in files:
+        hook("pytest_collectreport")(_CollectRep(f))
+    gone = [_Item(n) for n in deselected]
+    if gone:
+        hook("pytest_deselected")(gone)
+    session = _SessionWithConfig([_Item(n) for n in selected], args, root,
+                                 with_config=with_config)
+    hook("pytest_collection_finish")(session)
+    for nodeid, outcome in (outcomes or {}).items():
+        for rep in _reports_for(nodeid, outcome):
+            hook("pytest_runtest_logreport")(rep)
+    hook("pytest_sessionfinish")(session, exitstatus)
+
+
+X_A = "tests/test_x.py::test_a"
+X_B = "tests/test_x.py::test_b"
+
+
+class TestFileCoverage:
+
+    def _coverage_after(self, tmp_path, monkeypatch, args, selected, deselected=(),
+                        with_config=True):
+        c = _isolated_conftest(monkeypatch, tmp_path)
+        _drive_with_args(c, tmp_path, args, selected=selected, deselected=deselected,
+                         outcomes={n: "passed" for n in selected}, exitstatus=0,
+                         with_config=with_config)
+        runs = redlight.load_runs(str(tmp_path))
+        assert len(runs) == 1, runs
+        return redlight.file_coverage(runs[0], "tests/test_x.py")
+
+    def test_b1a_a_nodeid_argument_is_not_full_coverage(self, tmp_path, monkeypatch):
+        """B1a(F3 producer)。分類:interface-red(`redlight.file_coverage` 不存在)。
+
+        位置參數 `tests/test_x.py::test_a` —— 以 nodeid 指名,未收集的身分不產生 deselected。
+        """
+        got = self._coverage_after(tmp_path, monkeypatch, [X_A], [X_A])
+        assert got == "false", got
+
+    def test_b1b_a_backslash_nodeid_argument_is_not_full_coverage(self, tmp_path, monkeypatch):
+        """B1b(F3 producer)。分類:interface-red(`redlight.file_coverage` 不存在)。
+
+        位置參數 `tests\\test_x.py::test_a`(Windows 反斜線)—— 仍是 nodeid 指名。
+        """
+        got = self._coverage_after(tmp_path, monkeypatch, ["tests\\test_x.py::test_a"], [X_A])
+        assert got == "false", got
+
+    def test_b1c_a_file_argument_without_deselection_is_full_coverage(self, tmp_path, monkeypatch):
+        """B1c(F3 producer)。分類:interface-red(`redlight.file_coverage` 不存在)。
+
+        位置參數 `tests/test_x.py`(不含 `::`)、無 deselected ⇒ 整檔涵蓋。
+        """
+        c = _isolated_conftest(monkeypatch, tmp_path)
+        _c_call_collect_wrapper(c, _c_file(tmp_path, "tests/test_x.py"),
+                                _CCollectReport("tests/test_x.py", [_c_item(X_A), _c_item(X_B)]))
+        session = _CompletenessSession([_c_item(X_A), _c_item(X_B)],
+                                       _CConfig(tmp_path, _COption(), _c_plugins(c, tmp_path),
+                                                args=["tests/test_x.py"]))
+        _drive_with_session(c, session, selected=[X_A, X_B],
+                            outcomes={X_A: "passed", X_B: "passed"}, exitstatus=0)
+        got = redlight.file_coverage(redlight.load_runs(str(tmp_path))[0], "tests/test_x.py")
+        assert got == "true", got
+
+    def test_b1d_a_parent_directory_argument_is_full_coverage(self, tmp_path, monkeypatch):
+        """B1d(F3 producer)。分類:interface-red(`redlight.file_coverage` 不存在)。
+
+        位置參數 `tests`(上層目錄)、無 deselected ⇒ 整檔涵蓋。
+        """
+        c = _isolated_conftest(monkeypatch, tmp_path)
+        _c_call_collect_wrapper(c, _c_file(tmp_path, "tests/test_x.py"),
+                                _CCollectReport("tests/test_x.py", [_c_item(X_A), _c_item(X_B)]))
+        session = _CompletenessSession([_c_item(X_A), _c_item(X_B)],
+                                       _CConfig(tmp_path, _COption(), _c_plugins(c, tmp_path),
+                                                args=["tests"]))
+        _drive_with_session(c, session, selected=[X_A, X_B],
+                            outcomes={X_A: "passed", X_B: "passed"}, exitstatus=0)
+        got = redlight.file_coverage(redlight.load_runs(str(tmp_path))[0], "tests/test_x.py")
+        assert got == "true", got
+
+    def test_b1e_a_file_argument_with_deselection_is_not_full_coverage(self, tmp_path, monkeypatch):
+        """B1e(F3 producer)。分類:interface-red(`redlight.file_coverage` 不存在)。
+
+        位置參數 `tests/test_x.py`,但該檔有 deselected(`-k` 之類)⇒ 不是整檔涵蓋。
+        """
+        got = self._coverage_after(tmp_path, monkeypatch, ["tests/test_x.py"], [X_A],
+                                   deselected=[X_B])
+        assert got == "false", got
+
+    def test_b1f_no_config_means_unknown(self, tmp_path, monkeypatch):
+        """B1f(F3 producer)。分類:interface-red(`redlight.file_coverage` 不存在)。
+
+        假 session 沒有 config / args ⇒ 證明不了整檔涵蓋 ⇒ unknown(不知道,就不是完整)。
+        """
+        got = self._coverage_after(tmp_path, monkeypatch, [], [X_A, X_B], with_config=False)
+        assert got == "unknown", got
+
+    def test_b1g_an_argument_outside_the_root_means_unknown(self, tmp_path, monkeypatch):
+        """B1g(F3 producer)。分類:interface-red(`redlight.file_coverage` 不存在)。
+
+        位置參數是 root 之外的絕對路徑 —— 無法判讀它與 `tests/test_x.py` 的關係 ⇒ unknown。
+        """
+        outside = str(tmp_path.parent / "elsewhere" / "test_x.py")
+        got = self._coverage_after(tmp_path, monkeypatch, [outside], [X_A, X_B])
+        assert got == "unknown", got
+
+
+class TestRunStateSchema:
+
+    def test_b6_a_session_without_collected_is_not_state_c(self):
+        """B6(F1 缺欄)。分類:behavior-red。
+
+        session 缺 `collected` 欄位 —— 那不是「0 collected」,是證據不完整;
+        不得被判成 C(〈十七〉裁決 3:不得以「缺欄 ⇒ 空集合」處理)。
+        """
+        run = {"kind": "session", "run_id": "b6", "time": "2999-01-01T00:00:00+00:00",
+               "ticket_id": "99", "exit_code": 0, "deselected": [], "outcomes": {}}
+        assert redlight.run_state(run) != "C", run
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# 票 145 Station 3b 補件 —— B10:固定指令(無使用者位置參數)的整檔涵蓋
+#
+# 假 session 的 `config` 依本機 pytest 9.1.1 原始碼與本 repo 設定**靜態推導**:
+#   - `_pytest/config/__init__.py:1411-1438` `_decide_args()`:未給位置參數、且
+#     invocation dir == rootpath ⇒ `source = ArgsSource.TESTPATHS`,
+#     `result` = testpaths 各項經 `glob.iglob(path, recursive=True)` 展開後排序;
+#   - `pyproject.toml:71` `testpaths = ["tests"]` ⇒ `config.args == ["tests"]`;
+#   - rootdir 由 repo 根的 `pyproject.toml`(含 `[tool.pytest.ini_options]`)決定
+#     (`_pytest/config/findpaths.py:313-315`)⇒ 從 repo 根執行時 invocation dir == rootpath。
+# 這是推導,不是實際執行時觀察到的值。
+# ─────────────────────────────────────────────────────────────────────────────
+
+
+def _drive_with_session(c, session, selected=(), deselected=(), outcomes=None, exitstatus=0):
+    """同 `_drive_with_args`,但 session 由呼叫端建構(以便帶 `args_source`)。"""
+    def hook(name):
+        return getattr(c, name, None) or (lambda *a, **k: None)
+
+    _reset_conftest_state(c)
+    files = sorted(set(n.split("::", 1)[0] for n in list(selected) + list(deselected)))
+    for f in files:
+        hook("pytest_collectreport")(_CollectRep(f))
+    gone = [_Item(n) for n in deselected]
+    if gone:
+        hook("pytest_deselected")(gone)
+    hook("pytest_collection_finish")(session)
+    for nodeid, outcome in (outcomes or {}).items():
+        for rep in _reports_for(nodeid, outcome):
+            hook("pytest_runtest_logreport")(rep)
+    hook("pytest_sessionfinish")(session, exitstatus)
+
+
+class TestFixedCommandCoverage:
+
+    def test_b10_the_fixed_command_without_positional_args_is_full_coverage(
+            self, tmp_path, monkeypatch):
+        """B10(F3;〈十七〉3b 補件)。分類:interface-red(`redlight.file_coverage` 不存在)。
+
+        固定指令 `python -X utf8 -m pytest -q` 沒有使用者位置參數 —— pytest 以 testpaths
+        補上 `config.args == ["tests"]`、`args_source == TESTPATHS`(靜態推導,見上方註解)。
+        tests/test_x.py 被正常收集、無 deselected ⇒ full_file_coverage 必須為 "true";
+        否則固定全套永遠無法退紅。
+        """
+        c = _isolated_conftest(monkeypatch, tmp_path)
+        session = _SessionWithConfig([_Item(X_A), _Item(X_B)], ["tests"], tmp_path)
+        session.config.args_source = pytest.Config.ArgsSource.TESTPATHS
+        session.config.option = _COption()
+        session.config.pluginmanager = _c_plugins(c, tmp_path)
+        session.shouldstop = False
+        session.shouldfail = False
+        _c_call_collect_wrapper(c, _c_file(tmp_path, "tests/test_x.py"),
+                                _CCollectReport("tests/test_x.py", [_c_item(X_A), _c_item(X_B)]))
+        _drive_with_session(c, session, selected=[X_A, X_B],
+                            outcomes={X_A: "passed", X_B: "passed"}, exitstatus=0)
+        runs = redlight.load_runs(str(tmp_path))
+        assert len(runs) == 1, runs
+        got = redlight.file_coverage(runs[0], "tests/test_x.py")
+        assert got == "true", got
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# 票 145 Station 3c 紅燈 —— 選擇 / 執行完整性與 plugin 邊界(〈二十三〉)
+#
+# 合約:票 145〈二十三〉7 —— session 新增 `completeness`(options / cacheprovider_blocked /
+# shouldstop / shouldfail / pre_narrowing / plugins),`file_coverage == "true"` 多七條必要條件。
+# 規劃:docs/audits/2026-10-02-m1a-station3c-redlight-plan.md P4。
+#
+# **假物件盡量是 pytest 的真型別**:item 是 `pytest.Item` 子類、collector 是 `pytest.File`
+# 子類(以 `object.__new__` 建立、不經 `from_parent`),producer 用 isinstance 判斷時也成立。
+# **driver 依 pytest 9.1.1 的呼叫順序**:每個檔先對 conftest 的
+# `pytest_make_collect_report`(new-style `wrapper=True`;〈二十三〉2(a))送出**完整**結果,
+# wrapper 返回後才**就地**縮小 `report.result`(模擬外層 `LFPluginCollWrapper`,
+# `_pytest/cacheprovider.py:282`)—— producer 若沒有當下複製 nodeid,會看到縮小後的內容。
+# 之後才是 `pytest_collectreport`(縮小後)、`pytest_deselected`、`pytest_collection_finish`、
+# 逐身分的 runtest report、session 結束時的 `shouldstop` / `shouldfail`、`pytest_sessionfinish`。
+# 全部寫在 tmp root,不碰真實帳本(`_isolated_conftest`)。
+# ─────────────────────────────────────────────────────────────────────────────
+
+import inspect as _c_inspect
+import os as _c_os
+import types as _c_types
+
+
+class _CItem(pytest.Item):
+    """真的 `pytest.Item` 子類;只帶 nodeid。"""
+
+    def runtest(self):
+        pass
+
+
+class _CFile(pytest.File):
+    """真的 `pytest.File` 子類;只帶 nodeid / path。"""
+
+    def collect(self):
+        return []
+
+
+def _c_item(nodeid):
+    it = object.__new__(_CItem)
+    it._nodeid = nodeid
+    it.name = nodeid.split("::")[-1]
+    return it
+
+
+def _c_file(root, path):
+    f = object.__new__(_CFile)
+    f._nodeid = path
+    f.name = path.split("/")[-1]
+    f.path = pathlib.Path(str(root)) / path
+    return f
+
+
+class _CCollectReport:
+    def __init__(self, nodeid, result, failed=False):
+        self.nodeid = nodeid
+        self.result = list(result)
+        self.failed = failed
+        self.passed = not failed
+        self.skipped = False
+        self.outcome = "failed" if failed else "passed"
+
+
+class _CRunReport:
+    def __init__(self, nodeid, when, outcome, wasxfail=None):
+        self.nodeid = nodeid
+        self.fspath = nodeid.split("::", 1)[0]
+        self.when = when
+        self.outcome = outcome
+        self.passed = outcome == "passed"
+        self.failed = outcome == "failed"
+        self.skipped = outcome == "skipped"
+        if wasxfail is not None:
+            self.wasxfail = wasxfail
+
+
+def _c_reports(nodeid, kind):
+    """一個身分在 pytest 裡實際產生的 report 序列。
+
+    - passed / failed:setup → call → teardown
+    - skipped:setup(skipped)→ teardown,沒有 call
+    - xfail:setup → call(skipped,帶 `wasxfail`)→ teardown —— 明確辨識的 xfail
+    - setup_only:只有 setup(例:call 中 `pytest.exit()`,`_pytest/runner.py:262-267` 重拋,沒有 call / teardown report)
+    - setup_teardown:setup → teardown,沒有 call(`--setup-only`,`_pytest/runner.py:134-139`)
+    """
+    if kind in ("passed", "failed"):
+        return [_CRunReport(nodeid, "setup", "passed"),
+                _CRunReport(nodeid, "call", kind),
+                _CRunReport(nodeid, "teardown", "passed")]
+    if kind == "skipped":
+        return [_CRunReport(nodeid, "setup", "skipped"),
+                _CRunReport(nodeid, "teardown", "passed")]
+    if kind == "xfail":
+        return [_CRunReport(nodeid, "setup", "passed"),
+                _CRunReport(nodeid, "call", "skipped", wasxfail="reason"),
+                _CRunReport(nodeid, "teardown", "passed")]
+    if kind == "setup_only":
+        return [_CRunReport(nodeid, "setup", "passed")]
+    if kind == "setup_teardown":
+        return [_CRunReport(nodeid, "setup", "passed"),
+                _CRunReport(nodeid, "teardown", "passed")]
+    raise ValueError(kind)
+
+
+_C_OPTION_DEFAULTS = {
+    "pyargs": False, "lf": False, "last_failed_no_failures": "all",
+    "failedfirst": False, "newfirst": False, "stepwise": False, "stepwise_skip": False,
+    "stepwise_reset": False, "maxfail": None, "collectonly": False, "setuponly": False,
+    "setupplan": False, "setupshow": False, "keyword": "", "markexpr": "",
+    "deselect": None, "ignore": None, "ignore_glob": None,
+}
+
+
+class _COption:
+    """`config.option`:預設值為「全部關閉」(`maxfail` 預設 None,〈二十三〉2(f))。
+
+    `missing` 中的屬性不存在(例:`-p no:cacheprovider` 時沒有 `lf` / `stepwise`,〈二十三〉2(d))。
+    """
+
+    def __init__(self, missing=(), **overrides):
+        values = dict(_C_OPTION_DEFAULTS)
+        values.update(overrides)
+        for k in missing:
+            values.pop(k, None)
+        self.__dict__.update(values)
+
+
+class _CDist:
+    def __init__(self, name):
+        self.project_name = name
+        self.version = "0"
+        self.metadata = {"name": name}
+
+
+class _FakePluginManager:
+    """`config.pluginmanager` 的四個讀取點(`pluggy/_manager.py:235, 312, 422-429`)。"""
+
+    def __init__(self, name_plugins, distinfo=(), blocked=()):
+        self._name_plugins = list(name_plugins)
+        self._distinfo = list(distinfo)
+        self._blocked = set(blocked)
+
+    def list_name_plugin(self):
+        return list(self._name_plugins)
+
+    def list_plugin_distinfo(self):
+        return list(self._distinfo)
+
+    def is_blocked(self, name):
+        return name in self._blocked
+
+    def get_plugin(self, name):
+        return dict(self._name_plugins).get(name)
+
+    def has_plugin(self, name):
+        return self.get_plugin(name) is not None
+
+
+def _c_internal(module, label):
+    """類別定義在 `module` 的物件(模擬 `_pytest` 內部物件)。"""
+    return type(label, (), {"__module__": module})()
+
+
+def _c_plugins(c, root, extra=(), extra_dist=()):
+    """白名單內的 plugin 集合 + `extra`。
+
+    builtin:模組 `_pytest.main`、一個數字名稱(`str(id(...))`)而類別定義在 `_pytest.config` 的物件;
+    root_conftest:`<root>/tests/conftest.py`(絕對路徑,與 pytest 的 conftest 註冊名稱同形)—— 就是 producer 本身;
+    known_dist:`anyio.pytest_plugin`,在 `list_plugin_distinfo()` 中與 dist `anyio` 配對。
+    """
+    builtin_mod = _c_types.ModuleType("_pytest.main")
+    internal = _c_internal("_pytest.config", "_InternalHelper")
+    anyio_mod = _c_types.ModuleType("anyio.pytest_plugin")
+    names = [("main", builtin_mod),
+             (str(id(internal)), internal),
+             (_c_os.path.join(str(root), "tests", "conftest.py"), c),
+             ("anyio", anyio_mod)] + list(extra)
+    dist = [(anyio_mod, _CDist("anyio"))] + list(extra_dist)
+    return _FakePluginManager(names, dist)
+
+
+class _CInvocationParams:
+    def __init__(self, d):
+        self.dir = d
+
+
+class _CConfig:
+    def __init__(self, root, option, pluginmanager, args=("tests",)):
+        self.args = list(args)
+        self.args_source = pytest.Config.ArgsSource.TESTPATHS
+        self.rootpath = pathlib.Path(str(root))
+        self.invocation_params = _CInvocationParams(pathlib.Path(str(root)))
+        self.option = option
+        self.pluginmanager = pluginmanager
+
+    def getoption(self, name, default=None, skip=False):
+        return getattr(self.option, name, default)
+
+
+class _CompletenessSession:
+    def __init__(self, items, config):
+        self.items = list(items)
+        self.testscollected = len(self.items)
+        self.config = config
+        self.shouldstop = False
+        self.shouldfail = False
+
+
+def _c_call_collect_wrapper(c, collector, report):
+    """依 new-style wrapper 協定呼叫 conftest 的 `pytest_make_collect_report`(沒有就跳過)。"""
+    fn = getattr(c, "pytest_make_collect_report", None)
+    if fn is None:
+        return
+    gen = fn(collector)
+    if not _c_inspect.isgenerator(gen):
+        return
+    next(gen)
+    try:
+        gen.send(report)
+    except StopIteration:
+        pass
+
+
+def _c_drive(c, root, files, selected, outcomes=None, deselected=(), filtered_out=(),
+             collect_errors=(), exitstatus=0, option=None, pm=None,
+             shouldstop=False, shouldfail=False):
+    """依 pytest 9.1.1 的呼叫順序驅動 conftest(見本段開頭註解)。
+
+    `files`:{測試檔: 縮小前的完整 nodeid 清單};`filtered_out`:收集期被悄悄移除的身分
+    (不發 deselected 通知)。
+    """
+    def hook(name):
+        return getattr(c, name, None) or (lambda *a, **k: None)
+
+    dropped = set(filtered_out)
+    for path in sorted(files):
+        report = _CCollectReport(path, [_c_item(n) for n in files[path]])
+        _c_call_collect_wrapper(c, _c_file(root, path), report)
+        report.result[:] = [x for x in report.result if x.nodeid not in dropped]
+        hook("pytest_collectreport")(report)
+    for path in collect_errors:
+        hook("pytest_collectreport")(_CCollectReport(path, [], failed=True))
+    gone = [_c_item(n) for n in deselected]
+    if gone:
+        hook("pytest_deselected")(gone)
+    session = _CompletenessSession([_c_item(n) for n in selected],
+                                   _CConfig(root, option or _COption(), pm))
+    hook("pytest_collection_finish")(session)
+    for nodeid, kind in (outcomes or {}).items():
+        for rep in _c_reports(nodeid, kind):
+            hook("pytest_runtest_logreport")(rep)
+    session.shouldstop = shouldstop
+    session.shouldfail = shouldfail
+    hook("pytest_sessionfinish")(session, exitstatus)
+
+
+_C_MISSING = object()
+
+X_XF = "tests/test_x.py::test_xf"
+W_A = "tests/test_w.py::test_w_a"
+
+
+def _c_all_off(plugins=None):
+    """一份「全部關閉、白名單內」的完整性事實(consumer 側用;欄位名稱依〈二十三〉7)。"""
+    return {
+        "options": {"lf": False, "last_failed_no_failures": "all", "stepwise": False,
+                    "stepwise_skip": False, "maxfail": None, "collectonly": False,
+                    "setuponly": False, "setupplan": False},
+        "cacheprovider_blocked": False,
+        "shouldstop": False,
+        "shouldfail": False,
+        "pre_narrowing": {"tests/test_x.py": [X_A, X_B]},
+        "plugins": plugins if plugins is not None else [
+            {"name": "main", "kind": "builtin"},
+            {"name": "tests/conftest.py", "kind": "root_conftest"},
+            {"name": "anyio", "kind": "known_dist"},
+        ],
+    }
+
+
+def _c_raw_coverage(tmp_path, completeness=_C_MISSING):
+    """手寫一筆 session(全收集、全 passed、args `tests`)到 tmp root,讀回後判 `tests/test_x.py`。
+
+    除 `completeness` 外,形狀與 d122df4 的 producer 實際寫出的相同。
+    """
+    rec = {"kind": "session", "run_id": "c3-raw", "time": "2999-01-01T00:00:00+00:00",
+           "ticket_id": "99", "exit_code": 0, "collected": [X_A, X_B], "deselected": [],
+           "outcomes": {X_A: "passed", X_B: "passed"},
+           "invocation": {"args": ["tests"], "args_source": "TESTPATHS", "pyargs": False}}
+    if completeness is not _C_MISSING:
+        rec["completeness"] = completeness
+    path = redlight.session_log(str(tmp_path))
+    _c_os.makedirs(_c_os.path.dirname(path), exist_ok=True)
+    with io.open(path, "a", encoding="utf-8", newline="\n") as f:
+        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
+    runs = redlight.load_runs(str(tmp_path))
+    assert len(runs) == 1, runs
+    return redlight.file_coverage(runs[0], "tests/test_x.py")
+
+
+class TestCompletenessCoverage:
+
+    def test_c3a_lf_silent_narrowing_is_not_full_coverage(self, tmp_path, monkeypatch):
+        """C3a-1(〈二十三〉7 (ii)(v))。分類:behavior-red。
+
+        `--lf`:縮小前全集 [X_A, X_B],收集期悄悄移除 X_A(沒有 deselected 通知),
+        `session.items` 只剩 X_B 且 passed;`lfplugin-collskip` 已註冊(〈二十三〉2(e))。
+        d122df4 上失敗的原因:`.claude/hooks/redlight.py:405-406` 只看 deselected,
+        `:423-426` 位置參數 `tests` 為上層目錄 ⇒ `"true"`。
+        """
+        c = _isolated_conftest(monkeypatch, tmp_path)
+        skip_marker = _c_internal("_pytest.cacheprovider", "LFPluginCollSkipfiles")
+        wrapper = _c_internal("_pytest.cacheprovider", "LFPluginCollWrapper")
+        pm = _c_plugins(c, tmp_path, extra=[("lfplugin-collwrapper", wrapper),
+                                            ("lfplugin-collskip", skip_marker)])
+        _c_drive(c, tmp_path, {"tests/test_x.py": [X_A, X_B]}, selected=[X_B],
+                 outcomes={X_B: "passed"}, filtered_out=[X_A],
+                 option=_COption(lf=True), pm=pm, exitstatus=0)
+        runs = redlight.load_runs(str(tmp_path))
+        assert len(runs) == 1, runs
+        got = redlight.file_coverage(runs[0], "tests/test_x.py")
+        assert got != "true", got
+
+    def test_c3b_a_session_without_completeness_facts_is_not_full_coverage(self, tmp_path):
+        """C3b-1(〈二十三〉7 (i))。分類:behavior-red。
+
+        session 正好是 d122df4 的 producer 寫出的形狀,沒有 `completeness` ⇒ 不得為 `"true"`。
+        d122df4 上失敗的原因:`.claude/hooks/redlight.py:407-426` 不讀任何完整性事實 ⇒ `"true"`。
+        """
+        got = _c_raw_coverage(tmp_path)
+        assert got != "true", got
+
+    def test_c3b_a_malformed_completeness_fact_is_not_full_coverage(self, tmp_path):
+        """C3b-2(〈二十三〉7 (i))。分類:behavior-red。
+
+        `completeness` 存在,其餘全部關閉,但 `shouldstop` 是字串 `"False"`(型別錯)⇒ 不得為 `"true"`。
+        d122df4 上失敗的原因:`.claude/hooks/redlight.py:335-343` 不驗新欄位、`:407-426` 不讀它 ⇒ `"true"`。
+        """
+        comp = _c_all_off()
+        comp["shouldstop"] = "False"
+        got = _c_raw_coverage(tmp_path, comp)
+        assert got != "true", got
+
+    def test_c3c_an_exitfirst_run_is_not_full_coverage(self, tmp_path, monkeypatch):
+        """C3c-1(〈二十三〉7 (iii)(iv)(vi))。分類:behavior-red。
+
+        `-x`:`maxfail = 1`;W_A failed 後 `shouldfail` 設定、exit 1;X 全收集但沒有執行。
+        d122df4 上失敗的原因:`.claude/hooks/redlight.py:423-426` 不讀 maxfail / shouldfail ⇒ X 為 `"true"`。
+        """
+        c = _isolated_conftest(monkeypatch, tmp_path)
+        _c_drive(c, tmp_path, {"tests/test_w.py": [W_A], "tests/test_x.py": [X_A, X_B]},
+                 selected=[W_A, X_A, X_B], outcomes={W_A: "failed"},
+                 option=_COption(maxfail=1), pm=_c_plugins(c, tmp_path),
+                 shouldfail="stopping after 1 failures", exitstatus=1)
+        runs = redlight.load_runs(str(tmp_path))
+        assert len(runs) == 1, runs
+        got = redlight.file_coverage(runs[0], "tests/test_x.py")
+        assert got != "true", got
+
+    def test_c3p_an_unknown_plugin_dist_means_not_full_coverage(self, tmp_path):
+        """C3p-1 consumer(〈二十三〉3、7 (vii))。分類:behavior-red。
+
+        完整性事實全部關閉,`plugins` 多一項 `{"name": "evilplug", "kind": "other"}`(未知 dist)。
+        d122df4 上失敗的原因:`.claude/hooks/redlight.py:407-426` 不讀 plugins ⇒ `"true"`。
+        """
+        comp = _c_all_off()
+        comp["plugins"].append({"name": "evilplug", "kind": "other"})
+        got = _c_raw_coverage(tmp_path, comp)
+        assert got != "true", got
+
+    def test_c3p_a_plugin_loaded_by_name_means_not_full_coverage(self, tmp_path):
+        """C3p-2 consumer(〈二十三〉3、7 (vii))。分類:behavior-red。
+
+        完整性事實全部關閉,`plugins` 多一項 `{"name": "myplug", "kind": "other"}`(`-p myplug` 之類)。
+        d122df4 上失敗的原因:同 C3p-1。
+        """
+        comp = _c_all_off()
+        comp["plugins"].append({"name": "myplug", "kind": "other"})
+        got = _c_raw_coverage(tmp_path, comp)
+        assert got != "true", got
+
+    def test_c3p_an_extra_conftest_means_not_full_coverage(self, tmp_path):
+        """C3p-3 consumer(〈二十三〉3、7 (vii))。分類:behavior-red。
+
+        完整性事實全部關閉,`plugins` 多一項 `{"name": "tests/sub/conftest.py", "kind": "other"}`。
+        d122df4 上失敗的原因:同 C3p-1。
+        """
+        comp = _c_all_off()
+        comp["plugins"].append({"name": "tests/sub/conftest.py", "kind": "other"})
+        got = _c_raw_coverage(tmp_path, comp)
+        assert got != "true", got
+
+    def test_c3d_the_fixed_command_with_everything_off_is_full_coverage(self, tmp_path, monkeypatch):
+        """C3d-1(〈二十三〉7 全部條件成立)。分類:regression-lock。
+
+        固定全套:args `tests` / TESTPATHS、選項全部關閉、沒有 shouldstop / shouldfail、
+        縮小前全集 = 收集結果、plugin 全在白名單;X_A、X_B passed,X_XF 為明確辨識的 xfail
+        (call 為 skipped 且帶 `wasxfail`)⇒ `"true"`。
+        """
+        c = _isolated_conftest(monkeypatch, tmp_path)
+        _c_drive(c, tmp_path, {"tests/test_x.py": [X_A, X_B, X_XF]},
+                 selected=[X_A, X_B, X_XF],
+                 outcomes={X_A: "passed", X_B: "passed", X_XF: "xfail"},
+                 option=_COption(), pm=_c_plugins(c, tmp_path), exitstatus=0)
+        runs = redlight.load_runs(str(tmp_path))
+        assert len(runs) == 1, runs
+        got = redlight.file_coverage(runs[0], "tests/test_x.py")
+        assert got == "true", got
diff --git a/tests/test_status.py b/tests/test_status.py
index b2ae5d9..f87511d 100644
--- a/tests/test_status.py
+++ b/tests/test_status.py
@@ -563,6 +563,27 @@ class TestTestsUnderTicketUsesTheLatestRecordPerFile:
                      "w", encoding="utf-8") as f:
             for r in recs:
                 f.write(json.dumps(r, ensure_ascii=False) + "\n")
+        # 票 145〈十三〉裁決 2(C):Station 4 補 run-level facts。
+        # 上面 test_a 的綠紀錄是 8 欄格式、沒有 run 事實 ⇒ 依 ODC-1 沒有退紅權;
+        # 補一次「test_a 全檔被選到、唯一一條實際執行且通過、該檔無 failure」的 run,
+        # 時點與那筆綠相同。紅紀錄沒有 failed_tests(身分不明)⇒ 依〈十三〉裁決 3,
+        # 該檔全部 collected 身分都要 passed —— 這個 run 滿足它。
+        # 第一行讓 fake repo 有 redlight.py:status 依 root 載入它讀 run 事實(裁決 1)。
+        shutil.copy2(str(REAL_REDLIGHT),
+                     str(pathlib.Path(root) / ".claude" / "hooks" / "redlight.py"))
+        redlight.record_session(
+            root, run_id=u"fixture-570-571", time=u"2026-09-02T02:00:00+00:00",
+            ticket_id=u"99", exit_code=0, collected=[u"tests/test_a.py::test_one"],
+            deselected=[], outcomes={u"tests/test_a.py::test_one": u"passed"},
+            invocation={u"args": [u"tests"]},
+            completeness={
+                u"options": {u"lf": False, u"last_failed_no_failures": u"all", u"stepwise": False,
+                             u"stepwise_skip": False, u"maxfail": None, u"collectonly": False,
+                             u"setuponly": False, u"setupplan": False},
+                u"cacheprovider_blocked": False, u"shouldstop": False, u"shouldfail": False,
+                u"pre_narrowing": {u"tests/test_a.py": [u"tests/test_a.py::test_one"]},
+                u"plugins": [{u"name": u"main", u"kind": u"builtin"},
+                             {u"name": u"tests/conftest.py", u"kind": u"root_conftest"}]})
 
         out = render(root)
         red = _value_of(out, u"tests red under ticket 99")
@@ -1119,3 +1140,1159 @@ class TestReportLineSaysHowStaleTheReportIs:
         val = status._report_value(str(root))
         assert u"回報後 0 筆" in val, val
         assert u"樹共" not in val, u"仍在印樹的總數:%r" % val
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 票 145(M1-a)Station 3 紅燈 —— status 依 run 事實判定紅綠
+#
+# 觀察契約:docs/audits/2026-10-02-m1a-station3-redlight-plan.md 一、A,
+# 經票 145〈十三〉裁決修正(status 依 root 載入 redlight.py 的讀取函式;
+# ODC-1 第 2、3 項 file-scoped)。
+#
+# **新介面(`record_session` / `load_runs` / `ticket_test_state`)只在測試函式內部取用**
+# —— 它們不存在時只有這幾支失敗,不會讓整個檔收集錯誤。
+#
+# **既有的 `_make_root()` 一字不改**;要 redlight.py 的 fake repo 走下面的
+# `_root_with_redlight()`(〈十三〉裁決 2 允許的 fake repo 基礎設施)。
+# ═══════════════════════════════════════════════════════════════════════════
+
+REAL_REDLIGHT = ROOT / ".claude" / "hooks" / "redlight.py"
+
+
+def _load_redlight():
+    """載入 repo 的 redlight.py(既有模組;新函式在測試內才取用)。"""
+    import importlib.util
+    spec = importlib.util.spec_from_file_location(
+        "redlight_for_status_test", str(REAL_REDLIGHT))
+    mod = importlib.util.module_from_spec(spec)
+    spec.loader.exec_module(mod)
+    return mod
+
+
+redlight = _load_redlight()
+
+
+def _root_with_redlight(base, **kw):
+    """`_make_root()` 造出的最小 repo,再放一份 redlight.py 真檔複本。"""
+    root = _make_root(base, **kw)
+    shutil.copy2(str(REAL_REDLIGHT),
+                 str(pathlib.Path(root) / ".claude" / "hooks" / "redlight.py"))
+    return root
+
+
+def _write_raw_lines(root, lines):
+    """歷史原始紀錄**逐字**寫入 —— 不經 json 往返,一個位元組都不動。"""
+    with io.open(str(pathlib.Path(root) / ".dev" / "test-runs.jsonl"),
+                 "w", encoding="utf-8", newline="\n") as f:
+        for ln in lines:
+            f.write(ln + u"\n")
+
+
+def _rows_of(root):
+    p = pathlib.Path(root) / ".dev" / "test-runs.jsonl"
+    if not p.exists():
+        return []
+    return [json.loads(l) for l in io.open(str(p), encoding="utf-8") if l.strip()]
+
+
+# `.dev/test-runs.jsonl` 第 940 行與第 970 行原文(後者 = 票 139 `:39`)。
+LEDGER_940 = (u'{"test_file": "tests/test_gate.py", "time": "2026-09-13T07:28:31.037700+00:00", '
+              u'"result": "red", "failed_tests": ["TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce"], '
+              u'"impl_file": ".claude/hooks/gate.py", "impl_exists": true, '
+              u'"impl_hash": "2215f109bb73277248f78a6110a90bf51ec8a5f215251cf6089b86ebbe215170", '
+              u'"ticket_id": "133"}')
+LEDGER_970 = (u'{"test_file": "tests/test_gate.py", "time": "2026-09-13T12:26:18.644697+00:00", '
+              u'"result": "green", "failed_tests": [], '
+              u'"impl_file": ".claude/hooks/gate.py", "impl_exists": true, '
+              u'"impl_hash": "446b2ef6f49fa0608d347d9969b49a0f3fa682d11cfe47b622feaa80cdbb7dc2", '
+              u'"ticket_id": "133"}')
+
+# `.dev/test-runs.jsonl` 第 2036 行原文(Station 3 baseline 寫入)。
+LEDGER_2036 = (u'{"test_file": "tests/test_status.py", "time": "2026-10-02T13:27:56.450055+00:00", '
+               u'"result": "green", "failed_tests": [], '
+               u'"impl_file": ".claude/portable/status.py", "impl_exists": true, '
+               u'"impl_hash": "bdc3a089a33d179dc72eb937401520c5ec257ba11037fb42083420a9560fadf0", '
+               u'"ticket_id": "145"}')
+
+NO_RUN = u"最近一次 run:無 run 證據 / 不可判定"
+
+
+@pytest.fixture
+def redlight_guard(tmp_path, monkeypatch):
+    """本檔那一份 redlight 的路徑一律指到 tmp 的**另一個**位置。
+
+    `record_session(root, ...)` 應該寫到 `root`;若實作忽略 `root` 而寫到模組常數,
+    這裡讓它落在 guard 目錄 —— 測試會因為 status 讀不到而紅(出聲),
+    **而不是把假紀錄寫進真實帳本**。
+    """
+    guard = tmp_path / u"guard"
+    monkeypatch.setattr(redlight, "ROOT", str(guard))
+    monkeypatch.setattr(redlight, "RUN_LOG", str(guard / ".dev" / "test-runs.jsonl"))
+    monkeypatch.setattr(redlight, "PIPELINE", str(guard / ".dev" / "pipeline.json"))
+    return guard
+
+
+class TestTicket139:
+
+    def test_a_narrow_all_skip_record_does_not_retire_the_earlier_red(self, tmp_path):
+        """RL-6 票 139 歷史重現。現行 HEAD:**行為紅**。
+
+        帳本只有兩筆、逐字取自真實帳本(第 940 行 red、第 970 行 = 票 139 `:39` green),
+        沒有任何 synthetic 欄位。第 970 行沒有 run 事實 ⇒ coverage 未知 ⇒ 無退紅權
+        (〈十一〉/〈十三〉ODC-1)⇒ 第 940 行那條紅不得因為「每檔最新一筆」而消失。
+        現行 HEAD 取最新一筆 ⇒ 判成 green —— 那就是票 139 的 false green。
+        """
+        root = _root_with_redlight(tmp_path, ticket=u"133")
+        _write_raw_lines(root, [LEDGER_940, LEDGER_970])
+        out = render(root)
+        red = _value_of(out, u"tests red under ticket 133")
+        green = _value_of(out, u"tests green under ticket 133")
+        assert u"tests/test_gate.py" not in green, (
+            u"窄選、全部 skip 的那一筆把較早的紅蓋成綠了(票 139)\nred=%s\ngreen=%s"
+            % (red, green))
+        assert u"tests/test_gate.py" in red, red
+
+
+class TestNarrowSelection:
+
+    def test_a_later_green_without_run_facts_does_not_retire_x(self, tmp_path, monkeypatch):
+        """RL-6b(舊寫入版)。現行 HEAD:**行為紅**。
+
+        只用既有的 `redlight.record_run()` 寫:X 紅 → 同檔綠。那筆綠沒有 run 事實,
+        看不出它有沒有選到 X ⇒ 不得退紅。現行 HEAD 取最新一筆 ⇒ 判成 green。
+        """
+        root = _root_with_redlight(tmp_path)
+        monkeypatch.setattr(redlight, "ROOT", root)
+        monkeypatch.setattr(redlight, "RUN_LOG",
+                            str(pathlib.Path(root) / ".dev" / "test-runs.jsonl"))
+        monkeypatch.setattr(redlight, "PIPELINE",
+                            str(pathlib.Path(root) / ".dev" / "pipeline.json"))
+        redlight.record_run("tests/test_x.py", passed=False, failed_tests=["test_target"])
+        redlight.record_run("tests/test_x.py", passed=True, failed_tests=[])
+        out = render(root)
+        red = _value_of(out, u"tests red under ticket 99")
+        green = _value_of(out, u"tests green under ticket 99")
+        assert u"tests/test_x.py" not in green, (
+            u"沒有 run 事實的綠把較早的紅蓋掉了\nred=%s\ngreen=%s" % (red, green))
+        assert u"tests/test_x.py" in red, red
+
+    def test_a_narrow_run_that_did_not_select_x_does_not_retire_x(self, tmp_path, redlight_guard):
+        """RL-6b(run 事實版)。現行 HEAD:**介面紅**(`redlight.record_session` 不存在)。
+
+        run1:X 失敗。run2:同檔窄選,選到的 Y 通過,**X 在 deselected** ⇒
+        ODC-1 第 1 項不成立 ⇒ X 不退紅;run2 的 deselected 數事後可見(I7)。
+        """
+        root = _root_with_redlight(tmp_path)
+        x = u"tests/test_x.py::test_target"
+        y = u"tests/test_x.py::test_other"
+        redlight.record_session(root, run_id=u"rl6b-1", time=u"2026-09-02T01:00:00+00:00",
+                                ticket_id=u"99", exit_code=1, collected=[x, y],
+                                deselected=[], outcomes={x: u"failed", y: u"passed"})
+        redlight.record_session(root, run_id=u"rl6b-2", time=u"2026-09-02T02:00:00+00:00",
+                                ticket_id=u"99", exit_code=0, collected=[x, y],
+                                deselected=[x], outcomes={y: u"passed"})
+        out = render(root)
+        red = _value_of(out, u"tests red under ticket 99")
+        assert u"tests/test_x.py" in red, red
+        state = status.ticket_test_state(_rows_of(root), redlight.load_runs(root), u"99")
+        assert x in state[u"tests/test_x.py"][u"unresolved"], state
+        assert u"deselected 1" in _value_of(out, u"test-runs"), _value_of(out, u"test-runs")
+
+
+class TestHistoricalRecords:
+
+    def test_old_green_rows_are_shown_as_run_unknown_not_green(self, tmp_path):
+        """RL-7 Historical evidence。現行 HEAD:**行為紅**(依 I5 判讀)。
+
+        帳本第 2036 行原文 —— 一筆**真實**、來自一次確實全套通過的執行的 green;
+        而帳本仍證明不了這件事。舊格式紀錄缺 run 事實 ⇒ 只能是「run 事實未知」,
+        不得印在 green(Backward compatibility 2:不得推論 full pass)。
+        """
+        root = _root_with_redlight(tmp_path, ticket=u"145")
+        _write_raw_lines(root, [LEDGER_2036])
+        out = render(root)
+        green = _value_of(out, u"tests green under ticket 145")
+        assert u"tests/test_status.py" not in green, (
+            u"沒有 run 事實的舊紀錄被印成 green:%s" % green)
+        unknown = _value_of(out, u"tests green (run 事實未知) under ticket 145")
+        assert unknown is not None and u"tests/test_status.py" in unknown, out
+
+
+class TestOrphans:
+
+    def test_a_renamed_red_test_is_orphaned_not_green(self, tmp_path, redlight_guard):
+        """ODC-2 被刪除 / 改名的紅。現行 HEAD:**介面紅**(`redlight.record_session` 不存在)。
+
+        run1:test_old 失敗。run2:同檔全選、全部通過,但收集不到 test_old(改名成 test_new)
+        ⇒ 改名不視為延續 ⇒ 舊紅不得自動變綠,保留為可觀察的 orphaned。
+        """
+        root = _root_with_redlight(tmp_path)
+        old = u"tests/test_x.py::test_old"
+        new = u"tests/test_x.py::test_new"
+        keep = u"tests/test_x.py::test_keep"
+        redlight.record_session(root, run_id=u"odc2-1", time=u"2026-09-02T01:00:00+00:00",
+                                ticket_id=u"99", exit_code=1, collected=[old, keep],
+                                deselected=[], outcomes={old: u"failed", keep: u"passed"})
+        redlight.record_session(root, run_id=u"odc2-2", time=u"2026-09-02T02:00:00+00:00",
+                                ticket_id=u"99", exit_code=0, collected=[new, keep],
+                                deselected=[], outcomes={new: u"passed", keep: u"passed"},
+                                invocation={u"args": [u"tests"]},
+                                completeness={
+                                    u"options": {u"lf": False, u"last_failed_no_failures": u"all",
+                                                 u"stepwise": False, u"stepwise_skip": False,
+                                                 u"maxfail": None, u"collectonly": False,
+                                                 u"setuponly": False, u"setupplan": False},
+                                    u"cacheprovider_blocked": False, u"shouldstop": False,
+                                    u"shouldfail": False,
+                                    u"pre_narrowing": {u"tests/test_x.py": [new, keep]},
+                                    u"plugins": [{u"name": u"main", u"kind": u"builtin"},
+                                                 {u"name": u"tests/conftest.py",
+                                                  u"kind": u"root_conftest"}]})
+        out = render(root)
+        orphaned = _value_of(out, u"tests orphaned under ticket 99")
+        green = _value_of(out, u"tests green under ticket 99")
+        assert orphaned is not None and u"tests/test_x.py" in orphaned, out
+        assert u"test_old" in orphaned, orphaned
+        assert u"tests/test_x.py" not in green, green
+
+
+class TestRunEvidence:
+
+    def test_no_run_at_all_is_not_zero_tests_and_not_a_pass(self, tmp_path, redlight_guard):
+        """RL-5 No invocation。現行 HEAD:**介面紅**(`redlight.record_session` 不存在)。
+
+        兩個 root:B 有一次 0 collected 的 run(狀態 C),A 完全沒有 run 事實(E)。
+        兩者在輸出上必須分得開,且 A 不得被推論成任何 run 事實。
+        """
+        root_b = _root_with_redlight(tmp_path / u"b")
+        redlight.record_session(root_b, run_id=u"rl5-c", time=u"2026-09-02T01:00:00+00:00",
+                                ticket_id=u"99", exit_code=5, collected=[],
+                                deselected=[], outcomes={})
+        root_a = _root_with_redlight(tmp_path / u"a", with_runs=True)
+        assert redlight.load_runs(root_a) == [], u"沒有 run 卻讀出了 run 事實"
+        val_a = _value_of(render(root_a), u"test-runs")
+        val_b = _value_of(render(root_b), u"test-runs")
+        assert NO_RUN in val_a, val_a
+        assert u"最近一次 run:C" in val_b, val_b
+        assert val_a != val_b
+
+    def test_no_producer_means_undecidable_not_green_not_c(self, tmp_path, redlight_guard):
+        """ODC-3 producer 未載入。現行 HEAD:**介面紅**(`redlight.load_runs` 不存在)。
+
+        帳本有舊格式紀錄、沒有任何 run 事實(producer 沒被載入時就是這樣)⇒
+        記為「無證據 / 不可判定」;不得表示為 green,也不得推論為 C。
+        """
+        root = _root_with_redlight(tmp_path, ticket=u"145")
+        _write_raw_lines(root, [LEDGER_2036])
+        assert redlight.load_runs(root) == [], u"沒有 run 卻讀出了 run 事實"
+        out = render(root)
+        val = _value_of(out, u"test-runs")
+        assert NO_RUN in val, val
+        assert u"最近一次 run:C" not in val, val
+        assert u"tests/test_status.py" not in _value_of(out, u"tests green under ticket 145")
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 票 145 Station 3b 紅燈 —— producer → 持久化 run 事實 → status 的串接(F4)
+#
+# 依據:票 145〈十七〉F1–F4、裁決 1–4、Invariant「Absence is not coverage」。
+#
+# **串接的做法**:載入 `tests/conftest.py`,把它的 `_redlight` 換成本檔那一份、
+# `_ROOT` 指到 tmp root;本檔那一份 redlight 的 ROOT / RUN_LOG / PIPELINE 也指到
+# 同一個 tmp root。於是 producer 寫的逐檔紀錄與 run 事實都落在 tmp root,
+# status 再依 root 載入 redlight.py 讀回 —— 三段走的是真的程式碼,只有 pytest 本身是假的。
+#
+# **手寫 JSON 只在 B5 / B9**:缺欄與錯型別是寫入函式寫不出來的形狀(它們的重點正是
+# 「不是正常 producer 產生的紀錄」)。其餘一律透過 `record_run` / `record_session` /
+# conftest hooks 產生。
+# ═══════════════════════════════════════════════════════════════════════════
+
+CHAIN_X = u"tests/test_x.py::test_target"
+CHAIN_Y = u"tests/test_x.py::test_other"
+FAR_FUTURE = u"2999-01-01T00:00:00+00:00"
+
+
+class _ChainItem:
+    def __init__(self, nodeid):
+        self.nodeid = nodeid
+
+
+class _ChainCollectRep:
+    def __init__(self, nodeid, failed=False):
+        self.nodeid = nodeid
+        self.failed = failed
+        self.passed = not failed
+        self.outcome = "failed" if failed else "passed"
+
+
+class _ChainRunRep:
+    def __init__(self, nodeid, when, outcome):
+        self.nodeid = nodeid
+        self.fspath = nodeid.split("::", 1)[0]
+        self.when = when
+        self.outcome = outcome
+        self.passed = outcome == "passed"
+        self.failed = outcome == "failed"
+        self.skipped = outcome == "skipped"
+
+
+def _chain_reports(nodeid, outcome):
+    if outcome == "skipped":
+        return [_ChainRunRep(nodeid, "setup", "skipped"),
+                _ChainRunRep(nodeid, "teardown", "passed")]
+    return [_ChainRunRep(nodeid, "setup", "passed"),
+            _ChainRunRep(nodeid, "call", outcome),
+            _ChainRunRep(nodeid, "teardown", "passed")]
+
+
+class _ChainInvocationParams:
+    def __init__(self, d):
+        self.dir = d
+
+
+class _ChainOption:
+    pyargs = False
+
+
+class _ChainConfig:
+    def __init__(self, args, root):
+        self.args = list(args)
+        self.rootpath = root
+        self.invocation_params = _ChainInvocationParams(root)
+        self.option = _ChainOption()
+
+    def getoption(self, name, default=None):
+        return getattr(self.option, name, default)
+
+
+class _ChainSession:
+    def __init__(self, items, args, root):
+        self.items = list(items)
+        self.testscollected = len(self.items)
+        self.config = _ChainConfig(args, root)
+
+
+def _chain_conftest(root, monkeypatch):
+    """載入 tests/conftest.py,並把它與本檔那一份 redlight 的所有寫入都導到 `root`。"""
+    import importlib.util
+    spec = importlib.util.spec_from_file_location(
+        "conftest_for_status_chain", str(ROOT / "tests" / "conftest.py"))
+    c = importlib.util.module_from_spec(spec)
+    spec.loader.exec_module(c)
+    monkeypatch.setattr(redlight, "ROOT", root)
+    monkeypatch.setattr(redlight, "RUN_LOG",
+                        str(pathlib.Path(root) / ".dev" / "test-runs.jsonl"))
+    monkeypatch.setattr(redlight, "PIPELINE",
+                        str(pathlib.Path(root) / ".dev" / "pipeline.json"))
+    monkeypatch.setattr(c, "_redlight", redlight)
+    monkeypatch.setattr(c, "_ROOT", pathlib.Path(root))
+    return c
+
+
+def _chain_drive(c, root, args, selected=(), deselected=(), outcomes=None,
+                 collect_errors=(), exitstatus=0):
+    """依 pytest 的呼叫順序驅動 conftest hooks;session 帶 `config.args`。驅動前重置累積狀態。"""
+    def hook(name):
+        return getattr(c, name, None) or (lambda *a, **k: None)
+
+    c._outcomes.clear()
+    run = getattr(c, "_run", None)
+    if isinstance(run, dict):
+        for k, v in list(run.items()):
+            if hasattr(v, "clear"):
+                v.clear()
+            else:
+                run[k] = None
+    files = sorted(set(n.split("::", 1)[0] for n in list(selected) + list(deselected)))
+    for f in files:
+        hook("pytest_collectreport")(_ChainCollectRep(f))
+    for f in collect_errors:
+        hook("pytest_collectreport")(_ChainCollectRep(f, failed=True))
+    gone = [_ChainItem(n) for n in deselected]
+    if gone:
+        hook("pytest_deselected")(gone)
+    session = _ChainSession([_ChainItem(n) for n in selected], args, pathlib.Path(root))
+    hook("pytest_collection_finish")(session)
+    for nodeid, outcome in (outcomes or {}).items():
+        for rep in _chain_reports(nodeid, outcome):
+            hook("pytest_runtest_logreport")(rep)
+    hook("pytest_sessionfinish")(session, exitstatus)
+
+
+def _seed_red(failed_tests):
+    """以既有的 `record_run()` 寫一筆 tests/test_x.py 的 red(本檔 redlight 已導到 root)。"""
+    redlight.record_run("tests/test_x.py", passed=False, failed_tests=failed_tests)
+
+
+def _append_raw_session(root, rec):
+    """手寫一筆 session(只給 B5 / B9 用:寫入函式寫不出缺欄 / 錯型別的形狀)。"""
+    path = redlight.session_log(root)
+    os.makedirs(os.path.dirname(path), exist_ok=True)
+    with io.open(path, "a", encoding="utf-8", newline="\n") as f:
+        f.write(json.dumps(rec, ensure_ascii=False) + u"\n")
+
+
+def _lines_of(root):
+    out = render(root)
+    return {k: _value_of(out, u"tests %s under ticket 99" % k)
+            for k in (u"red", u"green", u"orphaned")}
+
+
+class TestCoverageChain:
+
+    def test_b2_a_nodeid_run_does_not_retire_an_unidentified_red(self, tmp_path, monkeypatch):
+        """B2(F3 串接)。分類:behavior-red。
+
+        舊紅的 `failed_tests` 為空(身分不明 ⇒ 視同全檔皆紅)。之後經 producer 以 nodeid
+        指名只跑 test_a 且 passed —— 沒收集到的身分不產生 deselected,但那不是整檔涵蓋。
+        ⇒ 該檔仍在 red、不在 green。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        _seed_red([])
+        a = u"tests/test_x.py::test_a"
+        _chain_drive(c, root, [a], selected=[a], outcomes={a: "passed"}, exitstatus=0)
+        got = _lines_of(root)
+        assert u"tests/test_x.py" not in got[u"green"], got
+        assert u"tests/test_x.py" in got[u"red"], got
+
+    def test_b3_a_nodeid_run_does_not_orphan_a_known_red(self, tmp_path, monkeypatch):
+        """B3(F3 串接)。分類:behavior-red。
+
+        已知紅身分 test_b。之後經 producer 以 nodeid 指名只跑 test_a 且 passed ——
+        test_b 沒被收集,只是因為沒被指名(Absence is not coverage)。
+        ⇒ test_b 仍在 red、不在 orphaned。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        _seed_red(["test_b"])
+        a = u"tests/test_x.py::test_a"
+        _chain_drive(c, root, [a], selected=[a], outcomes={a: "passed"}, exitstatus=0)
+        got = _lines_of(root)
+        assert u"tests/test_x.py" not in got[u"orphaned"], got
+        assert u"tests/test_x.py" in got[u"red"], got
+
+
+class TestDStateRetiresNothing:
+
+    def test_b4_a_d_run_with_a_collection_error_elsewhere_retires_nothing(
+            self, tmp_path, monkeypatch):
+        """B4(F2)。分類:behavior-red。
+
+        tests/test_x.py 的 X 為紅。之後一個 run:exit 1、另一檔 tests/test_y.py 收集錯誤、
+        X passed —— `run_state` 為 D ⇒ 整個 run 沒有退紅權、不得使任何檔成為 green。
+        ⇒ test_x.py 仍紅、不在 green。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        _seed_red(["test_target"])
+        _chain_drive(c, root, ["tests"], selected=[CHAIN_X], outcomes={CHAIN_X: "passed"},
+                     collect_errors=["tests/test_y.py"], exitstatus=1)
+        got = _lines_of(root)
+        assert u"tests/test_x.py" not in got[u"green"], got
+        assert u"tests/test_x.py" in got[u"red"], got
+
+
+class TestSessionSchemaFailClosed:
+
+    def test_b5_a_session_without_deselected_retires_nothing(self, tmp_path, monkeypatch):
+        """B5(F1 缺欄)。分類:behavior-red。
+
+        X 為紅。之後一筆 session **缺 `deselected` 欄位**、X passed(手寫:寫入函式寫不出缺欄)。
+        缺欄不得被當成「沒有 deselected」⇒ X 仍紅、不在 green。
+        """
+        root = _root_with_redlight(tmp_path)
+        _chain_conftest(root, monkeypatch)
+        _seed_red(["test_target"])
+        _append_raw_session(root, {"kind": "session", "run_id": "b5", "time": FAR_FUTURE,
+                                   "ticket_id": "99", "exit_code": 0,
+                                   "collected": [CHAIN_X],
+                                   "outcomes": {CHAIN_X: "passed"}})
+        got = _lines_of(root)
+        assert u"tests/test_x.py" not in got[u"green"], got
+        assert u"tests/test_x.py" in got[u"red"], got
+
+    def test_b7_an_outcome_outside_collected_retires_nothing(self, tmp_path, monkeypatch):
+        """B7(F1 身分不一致)。分類:behavior-red。
+
+        X 為紅。之後一筆 session 的 outcomes 含一個**不在 collected 裡**的身分(passed),
+        X 也 passed —— outcome 身分不屬於本次 selected ⇒ 該 run 不得進入正常語意。
+        ⇒ X 仍紅、不在 green。
+        """
+        root = _root_with_redlight(tmp_path)
+        _chain_conftest(root, monkeypatch)
+        _seed_red(["test_target"])
+        ghost = u"tests/test_x.py::test_ghost"
+        redlight.record_session(root, run_id=u"b7", time=FAR_FUTURE, ticket_id=u"99",
+                                exit_code=0, collected=[CHAIN_X], deselected=[],
+                                outcomes={CHAIN_X: u"passed", ghost: u"passed"})
+        got = _lines_of(root)
+        assert u"tests/test_x.py" not in got[u"green"], got
+        assert u"tests/test_x.py" in got[u"red"], got
+
+    def test_b9_a_string_deselected_retires_nothing_and_orphans_nothing(
+            self, tmp_path, monkeypatch):
+        """B9(F1 型別不符)。分類:behavior-red。
+
+        X 為紅。之後一筆 session 欄位都在,但 `deselected` 是**字串**而不是 list
+        (手寫:寫入函式會把它拆成字元 list,寫不出這個形狀)、X passed。
+        錯型別不得照常迭代 ⇒ 不退 X 的紅、該檔不為 green、不產生 orphan。
+        """
+        root = _root_with_redlight(tmp_path)
+        _chain_conftest(root, monkeypatch)
+        _seed_red(["test_target"])
+        _append_raw_session(root, {"kind": "session", "run_id": "b9", "time": FAR_FUTURE,
+                                   "ticket_id": "99", "exit_code": 0,
+                                   "collected": [CHAIN_X, CHAIN_Y],
+                                   "deselected": "tests/test_x.py::test_y",
+                                   "outcomes": {CHAIN_X: "passed", CHAIN_Y: "passed"}})
+        got = _lines_of(root)
+        assert u"tests/test_x.py" not in got[u"green"], got
+        assert u"tests/test_x.py" in got[u"red"], got
+        assert u"tests/test_x.py" not in got[u"orphaned"], got
+
+
+class TestAbsenceIsNotCoverage:
+
+    def test_b8_a_run_without_coverage_facts_does_not_orphan(self, tmp_path, monkeypatch):
+        """B8(Absence is not coverage)。分類:behavior-red。
+
+        已知紅身分 test_old。之後一筆**沒有 full_file_coverage 事實**的 session
+        (直接以 `record_session` 寫、不帶任何涵蓋資訊)收集不到 test_old ——
+        沒出現不代表已刪除或改名 ⇒ 不在 orphaned,且仍在 red。
+        """
+        root = _root_with_redlight(tmp_path)
+        _chain_conftest(root, monkeypatch)
+        _seed_red(["test_old"])
+        new = u"tests/test_x.py::test_new"
+        keep = u"tests/test_x.py::test_keep"
+        redlight.record_session(root, run_id=u"b8", time=FAR_FUTURE, ticket_id=u"99",
+                                exit_code=0, collected=[new, keep], deselected=[],
+                                outcomes={new: u"passed", keep: u"passed"})
+        got = _lines_of(root)
+        assert u"tests/test_x.py" not in got[u"orphaned"], got
+        assert u"tests/test_x.py" in got[u"red"], got
+
+
+class TestChainRegressionLocks:
+
+    def test_l1_three_skipped_645_deselected_keeps_the_red(self, tmp_path, monkeypatch):
+        """L1(RL-6 串接;F4)。分類:regression-lock(現行實作必須通過)。
+
+        X 為紅。之後經 producer 產生「3 skipped、645 deselected、0 passed」的 run
+        (X 在 deselected 裡)⇒ 仍紅。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        _seed_red(["test_target"])
+        chosen = [u"tests/test_x.py::test_symlink_%d" % i for i in range(3)]
+        gone = [CHAIN_X] + [u"tests/test_x.py::test_other_%d" % i for i in range(644)]
+        _chain_drive(c, root, ["tests/test_x.py"], selected=chosen, deselected=gone,
+                     outcomes={n: "skipped" for n in chosen}, exitstatus=0)
+        got = _lines_of(root)
+        assert u"tests/test_x.py" in got[u"red"], got
+        assert u"tests/test_x.py" not in got[u"green"], got
+
+    def test_l2_an_interrupted_run_keeps_the_red(self, tmp_path, monkeypatch):
+        """L2(RL-4 串接;F4)。分類:regression-lock(現行實作必須通過)。
+
+        X 為紅。之後經 producer 產生 exit 2(中斷)且 X passed 的 run ⇒ 仍紅。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        _seed_red(["test_target"])
+        _chain_drive(c, root, ["tests"], selected=[CHAIN_X], outcomes={CHAIN_X: "passed"},
+                     exitstatus=2)
+        got = _lines_of(root)
+        assert u"tests/test_x.py" in got[u"red"], got
+        assert u"tests/test_x.py" not in got[u"green"], got
+
+    def test_l3_a_full_directory_run_retires_the_red(self, tmp_path, monkeypatch):
+        """L3(正向對照;F4)。分類:regression-lock(現行實作必須通過;4b 後仍必須通過)。
+
+        X 為紅。之後經 producer 以位置參數 `tests`(整個目錄)跑、該檔全選、X passed、
+        無 failure、exit 0 ⇒ X 退紅、該檔在 green。防止修正過頭變成「永遠退不了紅」。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        _seed_red(["test_target"])
+        _s_drive(c, root, {u"tests/test_x.py": [CHAIN_X, CHAIN_Y]}, selected=[CHAIN_X, CHAIN_Y],
+                 outcomes={CHAIN_X: "passed", CHAIN_Y: "passed"}, exitstatus=0)
+        got = _lines_of(root)
+        assert u"tests/test_x.py" in got[u"green"], got
+        assert u"tests/test_x.py" not in got[u"red"], got
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 票 145 Station 3b 補件 —— B11:schema 不合格的 session 必須可被觀察到
+# ═══════════════════════════════════════════════════════════════════════════
+
+
+def _evidence_and_derived(out):
+    """render 輸出中 `=== Evidence ===` 與 `=== Derived ===` 兩個區塊的全文。
+
+    Repository 區塊(含 `generated` 時鐘行)不納入 —— 它兩次 render 之間本來就會變。
+    """
+    blocks = out.split(u"\n\n")
+    keep = [b for b in blocks
+            if b.startswith(u"=== Evidence ===") or b.startswith(u"=== Derived ===")]
+    return u"\n\n".join(keep)
+
+
+class TestMalformedSessionIsVisible:
+
+    def test_b11_a_malformed_session_is_neither_dropped_silently_nor_read_as_normal(
+            self, tmp_path, monkeypatch):
+        """B11(F1;〈十七〉3b 補件)。分類:behavior-red。
+
+        同一個 root 的前後比較:先只有 X 的紅(無任何 session),render 一次;
+        再追加一筆 schema 不合格的 session(`deselected` 為字串、X passed;手寫 ——
+        寫入函式寫不出這個形狀),其餘資料不動,再 render 一次。
+        ⇒ Evidence / Derived 必須與前次不同(不得靜默丟棄;表示位置與文字由 4b 決定);
+          不得顯示為正常狀態 A / B / C / F;X 所在檔仍紅、不 green、不 orphan。
+        """
+        root = _root_with_redlight(tmp_path)
+        _chain_conftest(root, monkeypatch)
+        _seed_red(["test_target"])
+        before = _evidence_and_derived(render(root))
+        _append_raw_session(root, {"kind": "session", "run_id": "b11", "time": FAR_FUTURE,
+                                   "ticket_id": "99", "exit_code": 0,
+                                   "collected": [CHAIN_X],
+                                   "deselected": "tests/test_x.py::test_y",
+                                   "outcomes": {CHAIN_X: "passed"}})
+        out = render(root)
+        after = _evidence_and_derived(out)
+        assert after != before, u"不合格的 session 被靜默丟棄:前後輸出相同\n%s" % after
+        for state in (u"A", u"B", u"C", u"F"):
+            assert u"最近一次 run:%s" % state not in after, (
+                u"不合格的 session 被當成正常狀態 %s\n%s" % (state, after))
+        red = _value_of(out, u"tests red under ticket 99")
+        green = _value_of(out, u"tests green under ticket 99")
+        orphaned = _value_of(out, u"tests orphaned under ticket 99")
+        assert u"tests/test_x.py" in red, after
+        assert u"tests/test_x.py" not in green, after
+        assert u"tests/test_x.py" not in orphaned, after
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 票 145 Station 3c 紅燈 —— 選擇 / 執行完整性與 plugin 邊界(串接;〈二十三〉)
+#
+# 合約:票 145〈二十三〉7、8。每一支都經**真實 tests/conftest.py** 的 hook(`_chain_conftest`)
+# 寫入 tmp root 的帳本,再由 status / `file_coverage` 讀回判定 —— 不直接餵分類好的資料。
+# 規劃:docs/audits/2026-10-02-m1a-station3c-redlight-plan.md P4。
+#
+# driver(`_s_drive`)的呼叫順序與 tests/test_redlight.py 的 `_c_drive` 相同:
+# 每個檔先對 conftest 的 `pytest_make_collect_report`(new-style wrapper)送出**完整**結果,
+# wrapper 返回後才**就地**縮小 `report.result`(模擬外層 `LFPluginCollWrapper`,
+# `_pytest/cacheprovider.py:282`);縮小掉的身分**不**送 `pytest_deselected`。
+# 假 item / collector 是 `pytest.Item` / `pytest.File` 的子類(`object.__new__`,不經 `from_parent`)。
+# 本段 helper 全部新寫;既有 helper(`_chain_conftest` / `_seed_red` / `_lines_of`)只呼叫、不修改。
+# ═══════════════════════════════════════════════════════════════════════════
+
+import inspect as _s_inspect
+import types as _s_types
+
+
+class _SItem(pytest.Item):
+    def runtest(self):
+        pass
+
+
+class _SFile(pytest.File):
+    def collect(self):
+        return []
+
+
+def _s_item(nodeid):
+    it = object.__new__(_SItem)
+    it._nodeid = nodeid
+    it.name = nodeid.split(u"::")[-1]
+    return it
+
+
+def _s_file(root, path):
+    f = object.__new__(_SFile)
+    f._nodeid = path
+    f.name = path.split(u"/")[-1]
+    f.path = pathlib.Path(str(root)) / path
+    return f
+
+
+class _SCollectReport:
+    def __init__(self, nodeid, result, failed=False):
+        self.nodeid = nodeid
+        self.result = list(result)
+        self.failed = failed
+        self.passed = not failed
+        self.skipped = False
+        self.outcome = "failed" if failed else "passed"
+
+
+class _SRunReport:
+    def __init__(self, nodeid, when, outcome, wasxfail=None):
+        self.nodeid = nodeid
+        self.fspath = nodeid.split(u"::", 1)[0]
+        self.when = when
+        self.outcome = outcome
+        self.passed = outcome == "passed"
+        self.failed = outcome == "failed"
+        self.skipped = outcome == "skipped"
+        if wasxfail is not None:
+            self.wasxfail = wasxfail
+
+
+def _s_reports(nodeid, kind):
+    """passed / failed:setup → call → teardown;skipped:setup(skipped)→ teardown;
+    xfail:call 為 skipped 且帶 `wasxfail`;setup_only:只有 setup(call 中 `pytest.exit()`);
+    setup_teardown:沒有 call(`--setup-only`)。"""
+    if kind in ("passed", "failed"):
+        return [_SRunReport(nodeid, "setup", "passed"),
+                _SRunReport(nodeid, "call", kind),
+                _SRunReport(nodeid, "teardown", "passed")]
+    if kind == "skipped":
+        return [_SRunReport(nodeid, "setup", "skipped"),
+                _SRunReport(nodeid, "teardown", "passed")]
+    if kind == "xfail":
+        return [_SRunReport(nodeid, "setup", "passed"),
+                _SRunReport(nodeid, "call", "skipped", wasxfail="reason"),
+                _SRunReport(nodeid, "teardown", "passed")]
+    if kind == "setup_only":
+        return [_SRunReport(nodeid, "setup", "passed")]
+    if kind == "setup_teardown":
+        return [_SRunReport(nodeid, "setup", "passed"),
+                _SRunReport(nodeid, "teardown", "passed")]
+    raise ValueError(kind)
+
+
+_S_OPTION_DEFAULTS = {
+    "pyargs": False, "lf": False, "last_failed_no_failures": "all",
+    "failedfirst": False, "newfirst": False, "stepwise": False, "stepwise_skip": False,
+    "stepwise_reset": False, "maxfail": None, "collectonly": False, "setuponly": False,
+    "setupplan": False, "setupshow": False, "keyword": "", "markexpr": "",
+    "deselect": None, "ignore": None, "ignore_glob": None,
+}
+
+
+class _CompletenessOption:
+    """`config.option`,預設「全部關閉」;`missing` 中的屬性不存在。"""
+
+    def __init__(self, missing=(), **overrides):
+        values = dict(_S_OPTION_DEFAULTS)
+        values.update(overrides)
+        for k in missing:
+            values.pop(k, None)
+        self.__dict__.update(values)
+
+
+class _SDist:
+    def __init__(self, name):
+        self.project_name = name
+        self.version = "0"
+        self.metadata = {"name": name}
+
+
+class _SFakePluginManager:
+    """`config.pluginmanager`:list_name_plugin / list_plugin_distinfo / is_blocked / get_plugin。"""
+
+    def __init__(self, name_plugins, distinfo=(), blocked=()):
+        self._name_plugins = list(name_plugins)
+        self._distinfo = list(distinfo)
+        self._blocked = set(blocked)
+
+    def list_name_plugin(self):
+        return list(self._name_plugins)
+
+    def list_plugin_distinfo(self):
+        return list(self._distinfo)
+
+    def is_blocked(self, name):
+        return name in self._blocked
+
+    def get_plugin(self, name):
+        return dict(self._name_plugins).get(name)
+
+    def has_plugin(self, name):
+        return self.get_plugin(name) is not None
+
+
+def _s_internal(module, label):
+    return type(label, (), {"__module__": module})()
+
+
+def _s_plugins(c, root, extra=(), extra_dist=()):
+    """白名單內的 plugin 集合(builtin / root_conftest / known_dist)+ `extra`。
+
+    builtin:模組 `_pytest.main`,以及數字名稱(`str(id(...))`)、類別定義在 `_pytest.config` 的物件;
+    root_conftest:`<root>/tests/conftest.py` 的絕對路徑 → producer 本身;
+    known_dist:`anyio.pytest_plugin`,在 `list_plugin_distinfo()` 中與 dist `anyio` 配對。
+    """
+    builtin_mod = _s_types.ModuleType("_pytest.main")
+    internal = _s_internal("_pytest.config", "_InternalHelper")
+    anyio_mod = _s_types.ModuleType("anyio.pytest_plugin")
+    names = [(u"main", builtin_mod),
+             (str(id(internal)), internal),
+             (os.path.join(str(root), u"tests", u"conftest.py"), c),
+             (u"anyio", anyio_mod)] + list(extra)
+    dist = [(anyio_mod, _SDist("anyio"))] + list(extra_dist)
+    return _SFakePluginManager(names, dist)
+
+
+class _SInvocationParams:
+    def __init__(self, d):
+        self.dir = d
+
+
+class _SConfig:
+    def __init__(self, root, option, pluginmanager, args=(u"tests",)):
+        self.args = list(args)
+        self.args_source = pytest.Config.ArgsSource.TESTPATHS
+        self.rootpath = pathlib.Path(str(root))
+        self.invocation_params = _SInvocationParams(pathlib.Path(str(root)))
+        self.option = option
+        self.pluginmanager = pluginmanager
+
+    def getoption(self, name, default=None, skip=False):
+        return getattr(self.option, name, default)
+
+
+class _CompletenessSession:
+    def __init__(self, items, config):
+        self.items = list(items)
+        self.testscollected = len(self.items)
+        self.config = config
+        self.shouldstop = False
+        self.shouldfail = False
+
+
+def _s_call_collect_wrapper(c, collector, report):
+    fn = getattr(c, "pytest_make_collect_report", None)
+    if fn is None:
+        return
+    gen = fn(collector)
+    if not _s_inspect.isgenerator(gen):
+        return
+    next(gen)
+    try:
+        gen.send(report)
+    except StopIteration:
+        pass
+
+
+def _s_drive(c, root, files, selected, outcomes=None, deselected=(), filtered_out=(),
+             collect_errors=(), exitstatus=0, option=None, pm=None,
+             shouldstop=False, shouldfail=False):
+    """依 pytest 9.1.1 的呼叫順序驅動真實 conftest;`files` = {檔: 縮小前完整 nodeid 清單}。"""
+    def hook(name):
+        return getattr(c, name, None) or (lambda *a, **k: None)
+
+    if pm is None:
+        pm = _s_plugins(c, root)
+    dropped = set(filtered_out)
+    for path in sorted(files):
+        report = _SCollectReport(path, [_s_item(n) for n in files[path]])
+        _s_call_collect_wrapper(c, _s_file(root, path), report)
+        report.result[:] = [x for x in report.result if x.nodeid not in dropped]
+        hook("pytest_collectreport")(report)
+    for path in collect_errors:
+        hook("pytest_collectreport")(_SCollectReport(path, [], failed=True))
+    gone = [_s_item(n) for n in deselected]
+    if gone:
+        hook("pytest_deselected")(gone)
+    session = _CompletenessSession([_s_item(n) for n in selected],
+                                   _SConfig(root, option or _CompletenessOption(), pm))
+    hook("pytest_collection_finish")(session)
+    for nodeid, kind in (outcomes or {}).items():
+        for rep in _s_reports(nodeid, kind):
+            hook("pytest_runtest_logreport")(rep)
+    session.shouldstop = shouldstop
+    session.shouldfail = shouldfail
+    hook("pytest_sessionfinish")(session, exitstatus)
+
+
+S_A = u"tests/test_x.py::test_a"
+S_B = u"tests/test_x.py::test_b"
+S_C = u"tests/test_x.py::test_c"
+S_XF = u"tests/test_x.py::test_xf"
+S_NEW = u"tests/test_x.py::test_new"
+S_KEEP = u"tests/test_x.py::test_keep"
+S_W = u"tests/test_w.py::test_w_a"
+
+
+def _s_lf_pm(c, root):
+    """`--lf` 真的過濾時的 plugin 集合:多了 `lfplugin-collwrapper` 與 `lfplugin-collskip`(皆為 builtin)。"""
+    return _s_plugins(c, root, extra=[
+        (u"lfplugin-collwrapper", _s_internal("_pytest.cacheprovider", "LFPluginCollWrapper")),
+        (u"lfplugin-collskip", _s_internal("_pytest.cacheprovider", "LFPluginCollSkipfiles"))])
+
+
+def _s_drive_lf(c, root):
+    """`--lf`:縮小前全集 [S_A, S_B],S_A 在收集期被悄悄移除,只跑 S_B 且 passed,exit 0。"""
+    _s_drive(c, root, {u"tests/test_x.py": [S_A, S_B]}, selected=[S_B],
+             outcomes={S_B: "passed"}, filtered_out=[S_A],
+             option=_CompletenessOption(lf=True), pm=_s_lf_pm(c, root), exitstatus=0)
+
+
+def _s_drive_exitfirst(c, root, x_ids):
+    """`-x`:S_W failed ⇒ `shouldfail`、exit 1;X 全收集(`x_ids`)但沒有執行。"""
+    _s_drive(c, root, {u"tests/test_w.py": [S_W], u"tests/test_x.py": list(x_ids)},
+             selected=[S_W] + list(x_ids), outcomes={S_W: "failed"},
+             option=_CompletenessOption(maxfail=1),
+             shouldfail=u"stopping after 1 failures", exitstatus=1)
+
+
+class TestSilentNarrowingChain:
+
+    def test_c3a_lf_narrowing_does_not_retire_an_unidentified_red(self, tmp_path, monkeypatch):
+        """C3a-2(〈二十三〉7 (ii)(v))。分類:behavior-red。
+
+        test_x.py 有身分不明的整檔紅;之後一次 `--lf` 只跑了 S_B(S_A 被悄悄移除)⇒ 仍紅、不 green。
+        d122df4 上失敗的原因:`.claude/hooks/redlight.py:423-426` 判 `"true"` ⇒
+        `.claude/portable/status.py:470-472` 整檔紅只看本 run 收集到的身分 ⇒ 退紅;`:475` green。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        _seed_red([])
+        _s_drive_lf(c, root)
+        got = _lines_of(root)
+        assert u"tests/test_x.py" in got[u"red"], got
+        assert u"tests/test_x.py" not in got[u"green"], got
+
+    def test_c3a_lf_narrowing_does_not_make_a_clean_file_green(self, tmp_path, monkeypatch):
+        """C3a-3(〈二十一〉21.2 附註 2;〈二十三〉7 (ii)(v))。分類:behavior-red。
+
+        test_x.py 先前沒有紅;一次 `--lf` 只跑了 S_B ⇒ 不得 green。
+        d122df4 上失敗的原因:`.claude/hooks/redlight.py:423-426` 判 `"true"` ⇒
+        `.claude/portable/status.py:475` `green_now = True`。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        _s_drive_lf(c, root)
+        got = _lines_of(root)
+        assert u"tests/test_x.py" not in got[u"green"], got
+
+
+class TestEarlyStopChain:
+
+    def test_c3c_exitfirst_does_not_orphan_a_known_red(self, tmp_path, monkeypatch):
+        """C3c-2(〈二十三〉7 (iii)(iv)(vi))。分類:behavior-red。
+
+        X 有已知紅 test_old;之後一次 `-x` 在 W 停下,X 收集到 [test_new, test_keep] 但沒執行
+        ⇒ X 仍紅、不 orphan(提前停止的 run 沒有 orphan 權)。
+        d122df4 上失敗的原因:`.claude/hooks/redlight.py:423-426` 判 `"true"` ⇒
+        `.claude/portable/status.py:464-468` 把 test_old 移入 orphan。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        _seed_red(["test_old"])
+        _s_drive_exitfirst(c, root, [S_NEW, S_KEEP])
+        got = _lines_of(root)
+        assert u"tests/test_x.py" not in got[u"orphaned"], got
+        assert u"tests/test_x.py" in got[u"red"], got
+
+    def test_c3c_exitfirst_does_not_make_unrun_files_green(self, tmp_path, monkeypatch):
+        """C3c-3。分類:regression-lock。
+
+        一次 `-x` 在 W 停下,X 全收集但沒有任何 outcome ⇒ X 不 green
+        (d122df4:`.claude/portable/status.py:475` 沒有 passed ⇒ 不 green)。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        _s_drive_exitfirst(c, root, [S_A, S_B])
+        got = _lines_of(root)
+        assert u"tests/test_x.py" not in got[u"green"], got
+
+    def test_c3c_stepwise_stop_is_d_and_retires_nothing(self, tmp_path, monkeypatch):
+        """C3c-4。分類:regression-lock。
+
+        `--sw`:S_W failed ⇒ `shouldstop` ⇒ `Interrupted` ⇒ exit 2(`_pytest/stepwise.py:183-188`、
+        `_pytest/main.py:411-412`)。X 的已知紅 CHAIN_X 本次 passed ⇒ D 沒有退紅權:仍紅、不 green、不 orphan
+        (d122df4:`.claude/portable/status.py:456-458`)。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        _seed_red(["test_target"])
+        _s_drive(c, root, {u"tests/test_w.py": [S_W], u"tests/test_x.py": [CHAIN_X, CHAIN_Y]},
+                 selected=[CHAIN_X, CHAIN_Y, S_W],
+                 outcomes={CHAIN_X: "passed", CHAIN_Y: "passed", S_W: "failed"},
+                 option=_CompletenessOption(stepwise=True),
+                 shouldstop=u"Test failed, continuing from this test next run.", exitstatus=2)
+        got = _lines_of(root)
+        assert u"tests/test_x.py" in got[u"red"], got
+        assert u"tests/test_x.py" not in got[u"green"], got
+        assert u"tests/test_x.py" not in got[u"orphaned"], got
+
+    def test_c3c_pytest_exit_zero_partial_file_is_not_green(self, tmp_path, monkeypatch):
+        """C3c-5(〈二十三〉2(b)、7 (vi))。分類:behavior-red。
+
+        測試內 `pytest.exit(returncode=0)`:S_A passed;S_B 只有 setup report、沒有 call;
+        S_C 沒有任何 report;exit 0;`shouldstop` / `shouldfail` 皆為 False ⇒ X 不得 green。
+        d122df4 上失敗的原因:`.claude/hooks/redlight.py:423-426` 判 `"true"` ⇒
+        `.claude/portable/status.py:475` `"passed" in results` ⇒ green。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        _s_drive(c, root, {u"tests/test_x.py": [S_A, S_B, S_C]}, selected=[S_A, S_B, S_C],
+                 outcomes={S_A: "passed", S_B: "setup_only"}, exitstatus=0)
+        got = _lines_of(root)
+        assert u"tests/test_x.py" not in got[u"green"], got
+
+    def test_setup_only_run_is_not_green(self, tmp_path, monkeypatch):
+        """C3x-1(規劃檔 P2(a))。分類:regression-lock。
+
+        `--setup-only`:每個身分只有 setup / teardown passed、沒有 call;exit 0 ⇒ 不 green
+        (d122df4:`tests/conftest.py:198-199` 只從 call 取 passed)。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        _s_drive(c, root, {u"tests/test_x.py": [S_A, S_B]}, selected=[S_A, S_B],
+                 outcomes={S_A: "setup_teardown", S_B: "setup_teardown"},
+                 option=_CompletenessOption(setuponly=True), exitstatus=0)
+        got = _lines_of(root)
+        assert u"tests/test_x.py" not in got[u"green"], got
+
+
+class TestLfFalseGreenChain:
+
+    def test_c3e_full_then_lf_does_not_produce_a_false_green(self, tmp_path, monkeypatch):
+        """C3e-1(〈二十一〉21.2 三步情境)。分類:behavior-red。
+
+        R1:test_x.py 收集錯誤(exit 2)⇒ 整檔紅。R2:全套,S_A passed、S_B failed(exit 1)⇒
+        red = {整檔, S_B}。R3:`--lf`,縮小前全集 [S_A, S_B],S_A 被悄悄移除,S_B passed(exit 0)
+        ⇒ 仍紅、不 green。
+        每次執行各自載入新的 conftest,模擬獨立的 pytest 程序(3c-1b 修正)。
+        情境斷言:R1 的 session 判 D、R2 判 B、R3 判 A 且 schema 合格。
+        d122df4 上失敗的原因:R3 在 `.claude/hooks/redlight.py:423-426` 判 `"true"` ⇒
+        `.claude/portable/status.py:470-474` 退掉整檔紅與 S_B ⇒ `:475` green。
+        """
+        root = _root_with_redlight(tmp_path)
+        c1 = _chain_conftest(root, monkeypatch)
+        _s_drive(c1, root, {}, selected=[], collect_errors=[u"tests/test_x.py"], exitstatus=2)
+        c2 = _chain_conftest(root, monkeypatch)
+        _s_drive(c2, root, {u"tests/test_x.py": [S_A, S_B]}, selected=[S_A, S_B],
+                 outcomes={S_A: "passed", S_B: "failed"}, exitstatus=1)
+        c3 = _chain_conftest(root, monkeypatch)
+        _s_drive_lf(c3, root)
+        runs = redlight.load_runs(root)
+        assert len(runs) == 3, runs
+        assert redlight.run_state(runs[0]) == u"D", runs[0]
+        assert redlight.run_state(runs[1]) == u"B", runs[1]
+        assert redlight.validate_session(runs[2]) == [], runs[2]
+        assert redlight.run_state(runs[2]) == u"A", runs[2]
+        got = _lines_of(root)
+        assert u"tests/test_x.py" in got[u"red"], got
+        assert u"tests/test_x.py" not in got[u"green"], got
+
+
+class TestCompletenessLocks:
+
+    def test_c3d_the_fixed_command_full_run_still_retires_the_red(self, tmp_path, monkeypatch):
+        """C3d-2(〈二十三〉7 全部條件成立)。分類:regression-lock。
+
+        X 的已知紅 CHAIN_X;之後一次固定全套(選項全部關閉、plugin 全在白名單、縮小前全集 = 收集結果),
+        CHAIN_X / CHAIN_Y passed,S_XF 為明確辨識的 xfail ⇒ X 退紅、在 green。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        _seed_red(["test_target"])
+        _s_drive(c, root, {u"tests/test_x.py": [CHAIN_X, CHAIN_Y, S_XF]},
+                 selected=[CHAIN_X, CHAIN_Y, S_XF],
+                 outcomes={CHAIN_X: "passed", CHAIN_Y: "passed", S_XF: "xfail"}, exitstatus=0)
+        got = _lines_of(root)
+        assert u"tests/test_x.py" in got[u"green"], got
+        assert u"tests/test_x.py" not in got[u"red"], got
+
+
+def _s_full_run_session(c, root, pm):
+    """test_x.py 全收集、全 passed、其餘完整性事實全部關閉;回傳讀回的最後一筆 session。"""
+    _s_drive(c, root, {u"tests/test_x.py": [S_A, S_B]}, selected=[S_A, S_B],
+             outcomes={S_A: "passed", S_B: "passed"}, pm=pm, exitstatus=0)
+    runs = redlight.load_runs(root)
+    assert runs, runs
+    return runs[-1]
+
+
+def _s_plugin_kinds(run):
+    """持久化 session 的 `completeness.plugins` → {正規化名稱: kind}。缺欄即失敗(不推論)。"""
+    comp = run.get("completeness")
+    assert isinstance(comp, dict), u"session 沒有 completeness:%r" % (run,)
+    plugins = comp.get("plugins")
+    assert isinstance(plugins, list), u"completeness 沒有 plugins:%r" % (comp,)
+    return dict((p.get("name"), p.get("kind")) for p in plugins)
+
+
+class TestPluginProducerChain:
+
+    def test_c3p_producer_classifies_an_unknown_dist_plugin_as_other(self, tmp_path, monkeypatch):
+        """C3p-4(〈二十三〉3 (3)、7 plugins / (vii))。分類:behavior-red。
+
+        多一個 plugin 物件(模組 `evilplug.plugin`),在 `list_plugin_distinfo()` 中配對到 dist `evil-dist`
+        ⇒ 持久化的 plugins 有一項 kind == "other",且 `file_coverage != "true"`。
+        d122df4 上失敗的原因:`tests/conftest.py:222-246` 不記 completeness ⇒ session 沒有 `completeness`。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        evil = _s_types.ModuleType("evilplug.plugin")
+        pm = _s_plugins(c, root, extra=[(u"evilplug", evil)], extra_dist=[(evil, _SDist("evil-dist"))])
+        run = _s_full_run_session(c, root, pm)
+        kinds = _s_plugin_kinds(run)
+        assert kinds.get(u"evilplug") == u"other", kinds
+        got = redlight.file_coverage(run, u"tests/test_x.py")
+        assert got != u"true", got
+
+    def test_c3p_producer_classifies_a_plugin_loaded_by_name_as_other(self, tmp_path, monkeypatch):
+        """C3p-5(〈二十三〉3、7 plugins / (vii))。分類:behavior-red。
+
+        多一個以名稱 `myplug` 註冊的模組 `myplug`(模擬 `-p myplug`),不在 `list_plugin_distinfo()`
+        ⇒ kind == "other",且 `file_coverage != "true"`。
+        d122df4 上失敗的原因:同 C3p-4。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        pm = _s_plugins(c, root, extra=[(u"myplug", _s_types.ModuleType("myplug"))])
+        run = _s_full_run_session(c, root, pm)
+        kinds = _s_plugin_kinds(run)
+        assert kinds.get(u"myplug") == u"other", kinds
+        got = redlight.file_coverage(run, u"tests/test_x.py")
+        assert got != u"true", got
+
+    def test_c3p_producer_classifies_an_extra_conftest_as_other_and_the_root_conftest_as_root_conftest(
+            self, tmp_path, monkeypatch):
+        """C3p-6(〈二十三〉3 (2)、7 plugins / (vii))。分類:behavior-red。
+
+        除 `<root>/tests/conftest.py` 外,多一個名稱為 `<root>/tests/sub/conftest.py` 絕對路徑的 conftest
+        ⇒ 前者 kind == "root_conftest"、後者 kind == "other"(名稱記 root 相對路徑),`file_coverage != "true"`;
+        持久化的 session 那一行文字不得包含 tmp root 的絕對路徑。
+        d122df4 上失敗的原因:同 C3p-4。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        sub = os.path.join(str(root), u"tests", u"sub", u"conftest.py")
+        pm = _s_plugins(c, root, extra=[(sub, _s_types.ModuleType("conftest"))])
+        run = _s_full_run_session(c, root, pm)
+        kinds = _s_plugin_kinds(run)
+        assert kinds.get(u"tests/sub/conftest.py") == u"other", kinds
+        assert kinds.get(u"tests/conftest.py") == u"root_conftest", kinds
+        got = redlight.file_coverage(run, u"tests/test_x.py")
+        assert got != u"true", got
+        with io.open(redlight.session_log(root), encoding="utf-8") as f:
+            text = f.read()
+        for form in set([str(root), str(root).replace(u"\\", u"/"), json.dumps(str(root))[1:-1]]):
+            assert form not in text, u"帳本出現絕對路徑:%s" % form
+
+    def test_c3p_producer_classifies_builtin_root_conftest_and_known_dist_as_not_other(
+            self, tmp_path, monkeypatch):
+        """C3p-7(〈二十三〉3 (1)(2)(3)、7 全部條件)。分類:behavior-red。
+
+        只有 `_pytest` 內建物件(含一個數字名稱、類別定義在 `_pytest.config` 的物件)、root `tests/conftest.py`、
+        以及在 `list_plugin_distinfo()` 中配對到 dist `anyio` 的 `anyio.pytest_plugin`
+        ⇒ 每一項 kind 都不是 "other",且 `file_coverage == "true"`。
+        d122df4 上失敗的原因:同 C3p-4(session 沒有 `completeness`)。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        run = _s_full_run_session(c, root, _s_plugins(c, root))
+        kinds = _s_plugin_kinds(run)
+        assert kinds, kinds
+        assert all(k != u"other" for k in kinds.values()), kinds
+        got = redlight.file_coverage(run, u"tests/test_x.py")
+        assert got == u"true", got
```

### E.2 `git diff 851cbd75b359a6b2a34452265e8a70992fa56996..02a5e28adf5aee11a43d5a1063504f01beb1d67f -- .claude/hooks/redlight.py .claude/portable/status.py tests/conftest.py tests/test_redlight.py tests/test_status.py`

```diff
diff --git a/.claude/hooks/redlight.py b/.claude/hooks/redlight.py
index 0f1633b..f4bee43 100644
--- a/.claude/hooks/redlight.py
+++ b/.claude/hooks/redlight.py
@@ -218,16 +218,19 @@ def _normalize_invocation(root, invocation):
 
 
 def record_session(root, run_id=None, time=None, ticket_id=None, exit_code=None,
-                   collected=(), deselected=(), outcomes=None, invocation=None):
+                   collected=(), deselected=(), outcomes=None, invocation=None,
+                   completeness=None):
     """追加一筆 run 事實到 `<root>` 的 session 帳本。回傳寫入的內容。
 
     - `collected`:本次收集到的身分(含被 deselect 的;收集錯誤以
       `<檔>::<collection error>` 標記)
     - `deselected`:被排除的身分;`selected` = collected − deselected
-    - `outcomes`:`{身分: "passed" | "failed" | "skipped" | "other"}`,只含 selected
+    - `outcomes`:`{身分: OUTCOME_VALUES 之一}`,只含 selected
     - `exit_code`:runner 的原始退出碼;取不到為 None
     - `invocation`:producer 觀察到的呼叫事實 `{"args", "args_source", "invocation_dir",
       "pyargs"}`(票 145〈十七〉裁決 1 的判定依據);None ⇒ 涵蓋範圍未知
+    - `completeness`:選擇 / 執行完整性事實(票 145〈二十三〉7);不是 dict ⇒ 記 None
+      (涵蓋範圍未知)。producer 負責只放 root 相對路徑與 JSON 原生型別
 
     `run_id` / `time` / `ticket_id` 為 None 時自取(測試可指定以求決定性)。
     寫入失敗不拋例外 —— 紀錄器不得弄死執行器(`TestTheRecorderCannotKillTheRunner`)。
@@ -243,6 +246,7 @@ def record_session(root, run_id=None, time=None, ticket_id=None, exit_code=None,
         "deselected": [str(n).replace("\\", "/") for n in (deselected or ())],
         "outcomes": {str(k).replace("\\", "/"): v for k, v in (outcomes or {}).items()},
         "invocation": _normalize_invocation(root, invocation),
+        "completeness": completeness if isinstance(completeness, dict) else None,
     }
     path = session_log(root)
     try:
@@ -280,7 +284,9 @@ def load_runs(root):
     return out
 
 
-OUTCOME_VALUES = ("passed", "failed", "skipped", "other")
+# "other" 只為讀得動 Station 4c 之前的 session(當時 xfail / xpass 都記成 other);
+# 4c 之後的 producer 寫 "xfail" / "xpass"。"other" 不算「執行完成」(〈二十三〉7 (vi))。
+OUTCOME_VALUES = ("passed", "failed", "skipped", "xfail", "xpass", "other")
 
 
 def validate_session(run):
@@ -290,8 +296,10 @@ def validate_session(run):
       - `run_id`、`time` 為非空字串;`ticket_id` 欄位存在(字串或 null)
       - `exit_code` 欄位存在,為 int(非 bool)或 null
       - `collected`、`deselected` 為字串 list;`deselected ⊆ collected`
-      - `outcomes` 為 `{字串: passed | failed | skipped | other}`;其鍵 ⊆ selected
+      - `outcomes` 為 `{字串: OUTCOME_VALUES 之一}`;其鍵 ⊆ selected
       - `invocation` 若存在且非 null:為 dict,`args` 為 list(元素為字串或 null)或 null
+      - `completeness` 若存在且非 null:為 dict(內部欄位由 `file_coverage` 逐項驗;
+        不合格 ⇒ 涵蓋 `"unknown"`,不讓整筆 run 失去加紅的效果)。沒有這個欄位的舊 session 仍合格
     """
     if not isinstance(run, dict):
         return ["不是物件"]
@@ -341,6 +349,9 @@ def validate_session(run):
             if args is not None and (not isinstance(args, list) or not all(
                     a is None or isinstance(a, str) for a in args)):
                 problems.append("invocation.args 型別不符")
+    comp = run.get("completeness")
+    if comp is not None and not isinstance(comp, dict):
+        problems.append("completeness 型別不符")
     return problems
 
 
@@ -391,9 +402,11 @@ def file_coverage(run, test_file):
     | 某個位置參數是**該檔本身或其上層目錄**、且不含 `::` | true |
     | 位置參數只以 nodeid(含 `::`)指名該檔 | false |
     | 其餘(參數無法判讀、或都與該檔無關) | unknown |
+    | 位置參數涵蓋該檔之後:完整性事實(〈二十三〉7)不全部成立 | 見 `_completeness_verdict` |
 
     **沒有為固定指令另寫分支**:pytest 未給位置參數時以 testpaths 補上
-    `config.args == ["tests"]`,與「位置參數為上層目錄 tests」走同一條規則。
+    `config.args == ["tests"]`,與「位置參數為上層目錄 tests」走同一條規則;
+    完整性事實也一樣 —— 固定全套只是「每一條都剛好成立」的那一種 run。
     """
     if validate_session(run):
         return "unknown"
@@ -423,7 +436,162 @@ def file_coverage(run, test_file):
         elif not sep and (path == "." or tf.startswith(path.rstrip("/") + "/")):
             covering = True
     if covering:
-        return "true"
+        return _completeness_verdict(run, tf, idents)
     if narrowed:
         return "false"
     return "unknown"
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# 票 145 Station 4c —— 選擇 / 執行完整性(〈二十三〉)
+#
+# 「沒有 deselected」證明不了選擇完整(`--lf` 在收集期就悄悄移除身分),
+# 「有一筆 report」證明不了已執行(`pytest.exit(returncode=0)` 只留 setup report)。
+# 所以 `"true"` 另外要 producer 的正向事實:選項全部關閉、沒有提前停止、
+# 縮小前全集 == 收集結果、每個 selected 身分都到了執行完成的終態、
+# 本次註冊的每個 plugin 都在受支援範圍(白名單)內。**任一缺欄或型別錯 ⇒ unknown。**
+#
+# 白名單變更須走票(〈二十三〉3)。
+# ─────────────────────────────────────────────────────────────────────────────
+
+COMPLETENESS_OPTIONS = ("lf", "last_failed_no_failures", "stepwise", "stepwise_skip",
+                        "maxfail", "collectonly", "setuponly", "setupplan")
+
+PLUGIN_KINDS = ("builtin", "root_conftest", "known_dist", "other")
+SUPPORTED_PLUGIN_KINDS = ("builtin", "root_conftest", "known_dist")
+BUILTIN_MODULE = "_pytest"
+ROOT_CONFTEST = "tests/conftest.py"
+KNOWN_DISTS = ("anyio",)
+OUTSIDE = "<outside>"
+
+# 「執行完成」的終態:call 的 passed / failed、任何 phase 的 skip、明確辨識的 xfail / xpass。
+# 籠統的 "other"(4c 之前的 xfail 記法)不算 —— 不得讓 other 自動取得 completeness。
+EXECUTED_OUTCOMES = ("passed", "failed", "skipped", "xfail", "xpass")
+
+
+def _dist_name(dist):
+    name = getattr(dist, "project_name", None)
+    if not isinstance(name, str):
+        try:
+            name = dist.metadata["name"]
+        except Exception:
+            name = None
+    return name.strip().lower().replace("_", "-") if isinstance(name, str) else None
+
+
+def _defining_module(plugin):
+    """模組物件看 `__name__`;類別看自己的 `__module__`;其他物件看其類別的 `__module__`。"""
+    import types
+    if isinstance(plugin, types.ModuleType):
+        return getattr(plugin, "__name__", None)
+    if isinstance(plugin, type):
+        return getattr(plugin, "__module__", None)
+    return getattr(type(plugin), "__module__", None)
+
+
+def _plugin_path_name(name, root):
+    """路徑型名稱 → root 相對 posix 路徑;root 以外(含跨磁碟)⇒ `<outside>`。"""
+    try:
+        rel = os.path.relpath(os.path.normpath(name), os.path.normpath(os.fspath(root)))
+    except ValueError:
+        return OUTSIDE
+    rel = rel.replace("\\", "/")
+    if rel == ".." or rel.startswith("../") or os.path.isabs(rel):
+        return OUTSIDE
+    return rel
+
+
+def classify_plugins(root, name_plugins, distinfo):
+    """`list_name_plugin()` 與 `list_plugin_distinfo()` 的原始事實 → `[{"name", "kind"}]`。
+
+    依序判定(〈二十三〉3):
+      1. plugin **物件**出現在 distinfo 配對中 ⇒ dist 名稱在 `KNOWN_DISTS` 為 known_dist,否則 other
+         (只看名稱相同不算 —— 名稱可被冒用)
+      2. 名稱是絕對路徑(conftest 的註冊名稱)⇒ root 相對路徑恰為 `ROOT_CONFTEST` 為 root_conftest,否則 other
+      3. 定義模組為 `_pytest` 或 `_pytest.*` ⇒ builtin
+      4. 其他 ⇒ other
+    帳本只記正規化名稱:路徑型一律轉 root 相對路徑(root 以外記 `<outside>`),不記絕對路徑。
+    """
+    dists = [(p, _dist_name(d)) for p, d in (distinfo or [])]
+    out = []
+    for name, plugin in name_plugins or []:
+        name = str(name)
+        is_path = os.path.isabs(name)
+        shown = _plugin_path_name(name, root) if is_path else name
+        paired = [dn for p, dn in dists if p is plugin]
+        if paired:
+            kind = "known_dist" if all(dn in KNOWN_DISTS for dn in paired) else "other"
+        elif is_path:
+            kind = "root_conftest" if shown == ROOT_CONFTEST else "other"
+        else:
+            mod = _defining_module(plugin)
+            builtin = isinstance(mod, str) and (
+                mod == BUILTIN_MODULE or mod.startswith(BUILTIN_MODULE + "."))
+            kind = "builtin" if builtin else "other"
+        out.append({"name": shown, "kind": kind})
+    return out
+
+
+def _is_str_list(v):
+    return isinstance(v, list) and all(isinstance(n, str) for n in v)
+
+
+def _completeness_problems(comp):
+    """completeness 的型別問題清單(空 = 型別正確)。〈二十三〉7 (i)。"""
+    if not isinstance(comp, dict):
+        return ["completeness 缺欄或型別不符"]
+    problems = []
+    options = comp.get("options")
+    if not isinstance(options, dict) or any(k not in options for k in COMPLETENESS_OPTIONS):
+        problems.append("options 缺欄或型別不符")
+    for key in ("cacheprovider_blocked", "shouldstop", "shouldfail"):
+        if not isinstance(comp.get(key), bool):
+            problems.append("%s 缺欄或型別不符" % key)
+    pre = comp.get("pre_narrowing")
+    if not isinstance(pre, dict) or not all(
+            isinstance(k, str) and _is_str_list(v) for k, v in pre.items()):
+        problems.append("pre_narrowing 缺欄或型別不符")
+    plugins = comp.get("plugins")
+    if not isinstance(plugins, list) or not plugins or not all(
+            isinstance(p, dict) and isinstance(p.get("name"), str)
+            and p.get("kind") in PLUGIN_KINDS for p in plugins):
+        problems.append("plugins 缺欄或型別不符")
+    return problems
+
+
+def _completeness_verdict(run, tf, idents):
+    """位置參數已涵蓋 `tf` 之後,依〈二十三〉7 (i)–(vii) 判 `"true"` / `"false"` / `"unknown"`。
+
+    - (i) 缺欄 / 型別錯 ⇒ unknown
+    - (vii) 有 plugin 不在受支援範圍 ⇒ unknown(在支援邊界之外,不知道)
+    - (ii) `lf` / `stepwise` 生效(除非 cacheprovider 被封鎖)⇒ false(縮小機制作用中)
+    - (iii) maxfail / collectonly / setuponly / setupplan ⇒ unknown
+    - (iv) shouldstop / shouldfail ⇒ unknown
+    - (v) 縮小前全集 != 本 run 該檔的 collected ⇒ false
+    - (vi) 有 selected 身分沒到執行完成的終態 ⇒ unknown
+    """
+    comp = run.get("completeness")
+    if _completeness_problems(comp):
+        return "unknown"
+    if any(p["kind"] not in SUPPORTED_PLUGIN_KINDS for p in comp["plugins"]):
+        return "unknown"
+    options = comp["options"]
+    if comp["cacheprovider_blocked"] is not True:
+        if not (options["lf"] is False and options["stepwise"] is False
+                and options["stepwise_skip"] is False):
+            return "false"
+    maxfail = options["maxfail"]
+    if not (maxfail is None or (type(maxfail) is int and maxfail == 0)):
+        return "unknown"
+    if not all(options[k] is False for k in ("collectonly", "setuponly", "setupplan")):
+        return "unknown"
+    if comp["shouldstop"] is not False or comp["shouldfail"] is not False:
+        return "unknown"
+    pre = comp["pre_narrowing"].get(tf)
+    if pre is None or set(pre) != set(idents):
+        return "false"
+    deselected = set(run["deselected"])
+    outcomes = run["outcomes"]
+    if any(outcomes.get(n) not in EXECUTED_OUTCOMES for n in idents if n not in deselected):
+        return "unknown"
+    return "true"
diff --git a/tests/conftest.py b/tests/conftest.py
index 7f6fe5e..bb8e498 100644
--- a/tests/conftest.py
+++ b/tests/conftest.py
@@ -191,12 +191,15 @@ def _run_outcome(report):
     """
     if getattr(report, "failed", False):
         return "failed"
+    # 票 145 Station 4c:xfail / xpass 明確辨識(〈二十三〉7 (vi)),不再籠統記成 other ——
+    # other 不算「執行完成」,而 xfail(skipped + wasxfail)與 non-strict xpass(call passed +
+    # wasxfail)都是測試確實跑完的終態。strict xpass 是 failed,上面已處理。
     xfail = getattr(report, "wasxfail", None) is not None
     when = getattr(report, "when", None)
     if getattr(report, "skipped", False):
-        return "other" if xfail else "skipped"
+        return "xfail" if xfail else "skipped"
     if when == "call" and getattr(report, "passed", False):
-        return "other" if xfail else "passed"
+        return "xpass" if xfail else "passed"
     return None
 
 
@@ -241,8 +244,12 @@ def pytest_sessionfinish(session, exitstatus):
     # 位置參數與它們的來源。沒有 config ⇒ None ⇒ 涵蓋範圍未知(不知道,就不是完整)。
     # 舊版 redlight.py 的 record_session 沒有 `invocation` 參數 ⇒ 照舊不傳。
     import inspect as _inspect
-    if "invocation" in _inspect.signature(_redlight.record_session).parameters:
+    params = _inspect.signature(_redlight.record_session).parameters
+    if "invocation" in params:
         kwargs["invocation"] = _invocation_of(session)
+    # 票 145 Station 4c:選擇 / 執行完整性事實(〈二十三〉7)。收集失敗 ⇒ None ⇒ 涵蓋未知。
+    if "completeness" in params:
+        kwargs["completeness"] = _completeness_of(session)
     _redlight.record_session(_ROOT, **kwargs)
 
 
@@ -265,3 +272,70 @@ def _invocation_of(session):
         "invocation_dir": os.fspath(inv_dir) if inv_dir is not None else None,
         "pyargs": bool(getattr(option, "pyargs", False)),
     }
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# 票 145 Station 4c:選擇 / 執行完整性事實(〈二十三〉7)
+#
+# **縮小前全集**:`--lf` 在外層 wrapper(`LFPluginCollWrapper`)裡就地改寫 collector 的
+# `report.result`,不發 deselected 通知。本 wrapper 標 trylast ⇒ 在 wrapper 鏈的最內層,
+# `yield` 之後最先拿到 report,當下**複製** nodeid(之後的就地改寫碰不到這份)。
+# 記的是 report 裡的 `pytest.Item`:File collector 的直接子項,以及 Class 之類子 collector 的子項 ——
+# class 內的測試不在 File 的 report 裡,只記 File 的話 class 型測試檔的全集永遠對不上。
+#
+# 存在 `_run` 之外:既有的測試 driver 會在驅動前清空 `_run` 的每個值。
+# 收集出錯 ⇒ `_pre_narrowing_broken` ⇒ 本次 completeness 不寫(涵蓋未知)。
+# ─────────────────────────────────────────────────────────────────────────────
+
+_pre_narrowing = {}
+_pre_narrowing_broken = []
+
+
+@pytest.hookimpl(wrapper=True, trylast=True)
+def pytest_make_collect_report(collector):
+    report = yield
+    try:
+        if _redlight is not None:
+            for node in list(getattr(report, "result", None) or []):
+                if isinstance(node, pytest.Item):
+                    nodeid = _nodeid(node)
+                    _pre_narrowing.setdefault(nodeid.split("::", 1)[0], []).append(nodeid)
+    except Exception:
+        _pre_narrowing_broken.append(True)
+    return report
+
+
+def _plain(value):
+    """config.option 的值照原樣記;不是 JSON 原生型別的,記型別名(寫不出來就整筆 session 遺失)。"""
+    if value is None or isinstance(value, (bool, int, float, str)):
+        return value
+    return "<%s>" % type(value).__name__
+
+
+def _flag(session, name):
+    """session 結束時的 shouldstop / shouldfail → bool;屬性不存在 ⇒ None(缺欄 ⇒ 涵蓋未知)。"""
+    if not hasattr(session, name):
+        return None
+    return bool(getattr(session, name))
+
+
+def _completeness_of(session):
+    """本次 session 的完整性事實。任何一步出錯 ⇒ None(寧可多紅,不讓 pytest 失敗)。"""
+    try:
+        if _pre_narrowing_broken:
+            return None
+        cfg = session.config
+        option = cfg.option
+        pm = cfg.pluginmanager
+        return {
+            "options": dict((k, _plain(getattr(option, k, None)))
+                            for k in _redlight.COMPLETENESS_OPTIONS),
+            "cacheprovider_blocked": bool(pm.is_blocked("cacheprovider")),
+            "shouldstop": _flag(session, "shouldstop"),
+            "shouldfail": _flag(session, "shouldfail"),
+            "pre_narrowing": dict((f, list(ids)) for f, ids in _pre_narrowing.items()),
+            "plugins": _redlight.classify_plugins(_ROOT, pm.list_name_plugin(),
+                                                  pm.list_plugin_distinfo()),
+        }
+    except Exception:
+        return None
diff --git a/tests/test_redlight.py b/tests/test_redlight.py
index f1b010f..efb3600 100644
--- a/tests/test_redlight.py
+++ b/tests/test_redlight.py
@@ -526,7 +526,15 @@ class TestFileCoverage:
 
         位置參數 `tests/test_x.py`(不含 `::`)、無 deselected ⇒ 整檔涵蓋。
         """
-        got = self._coverage_after(tmp_path, monkeypatch, ["tests/test_x.py"], [X_A, X_B])
+        c = _isolated_conftest(monkeypatch, tmp_path)
+        _c_call_collect_wrapper(c, _c_file(tmp_path, "tests/test_x.py"),
+                                _CCollectReport("tests/test_x.py", [_c_item(X_A), _c_item(X_B)]))
+        session = _CompletenessSession([_c_item(X_A), _c_item(X_B)],
+                                       _CConfig(tmp_path, _COption(), _c_plugins(c, tmp_path),
+                                                args=["tests/test_x.py"]))
+        _drive_with_session(c, session, selected=[X_A, X_B],
+                            outcomes={X_A: "passed", X_B: "passed"}, exitstatus=0)
+        got = redlight.file_coverage(redlight.load_runs(str(tmp_path))[0], "tests/test_x.py")
         assert got == "true", got
 
     def test_b1d_a_parent_directory_argument_is_full_coverage(self, tmp_path, monkeypatch):
@@ -534,7 +542,15 @@ class TestFileCoverage:
 
         位置參數 `tests`(上層目錄)、無 deselected ⇒ 整檔涵蓋。
         """
-        got = self._coverage_after(tmp_path, monkeypatch, ["tests"], [X_A, X_B])
+        c = _isolated_conftest(monkeypatch, tmp_path)
+        _c_call_collect_wrapper(c, _c_file(tmp_path, "tests/test_x.py"),
+                                _CCollectReport("tests/test_x.py", [_c_item(X_A), _c_item(X_B)]))
+        session = _CompletenessSession([_c_item(X_A), _c_item(X_B)],
+                                       _CConfig(tmp_path, _COption(), _c_plugins(c, tmp_path),
+                                                args=["tests"]))
+        _drive_with_session(c, session, selected=[X_A, X_B],
+                            outcomes={X_A: "passed", X_B: "passed"}, exitstatus=0)
+        got = redlight.file_coverage(redlight.load_runs(str(tmp_path))[0], "tests/test_x.py")
         assert got == "true", got
 
     def test_b1e_a_file_argument_with_deselection_is_not_full_coverage(self, tmp_path, monkeypatch):
@@ -624,9 +640,424 @@ class TestFixedCommandCoverage:
         c = _isolated_conftest(monkeypatch, tmp_path)
         session = _SessionWithConfig([_Item(X_A), _Item(X_B)], ["tests"], tmp_path)
         session.config.args_source = pytest.Config.ArgsSource.TESTPATHS
+        session.config.option = _COption()
+        session.config.pluginmanager = _c_plugins(c, tmp_path)
+        session.shouldstop = False
+        session.shouldfail = False
+        _c_call_collect_wrapper(c, _c_file(tmp_path, "tests/test_x.py"),
+                                _CCollectReport("tests/test_x.py", [_c_item(X_A), _c_item(X_B)]))
         _drive_with_session(c, session, selected=[X_A, X_B],
                             outcomes={X_A: "passed", X_B: "passed"}, exitstatus=0)
         runs = redlight.load_runs(str(tmp_path))
         assert len(runs) == 1, runs
         got = redlight.file_coverage(runs[0], "tests/test_x.py")
         assert got == "true", got
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# 票 145 Station 3c 紅燈 —— 選擇 / 執行完整性與 plugin 邊界(〈二十三〉)
+#
+# 合約:票 145〈二十三〉7 —— session 新增 `completeness`(options / cacheprovider_blocked /
+# shouldstop / shouldfail / pre_narrowing / plugins),`file_coverage == "true"` 多七條必要條件。
+# 規劃:docs/audits/2026-10-02-m1a-station3c-redlight-plan.md P4。
+#
+# **假物件盡量是 pytest 的真型別**:item 是 `pytest.Item` 子類、collector 是 `pytest.File`
+# 子類(以 `object.__new__` 建立、不經 `from_parent`),producer 用 isinstance 判斷時也成立。
+# **driver 依 pytest 9.1.1 的呼叫順序**:每個檔先對 conftest 的
+# `pytest_make_collect_report`(new-style `wrapper=True`;〈二十三〉2(a))送出**完整**結果,
+# wrapper 返回後才**就地**縮小 `report.result`(模擬外層 `LFPluginCollWrapper`,
+# `_pytest/cacheprovider.py:282`)—— producer 若沒有當下複製 nodeid,會看到縮小後的內容。
+# 之後才是 `pytest_collectreport`(縮小後)、`pytest_deselected`、`pytest_collection_finish`、
+# 逐身分的 runtest report、session 結束時的 `shouldstop` / `shouldfail`、`pytest_sessionfinish`。
+# 全部寫在 tmp root,不碰真實帳本(`_isolated_conftest`)。
+# ─────────────────────────────────────────────────────────────────────────────
+
+import inspect as _c_inspect
+import os as _c_os
+import types as _c_types
+
+
+class _CItem(pytest.Item):
+    """真的 `pytest.Item` 子類;只帶 nodeid。"""
+
+    def runtest(self):
+        pass
+
+
+class _CFile(pytest.File):
+    """真的 `pytest.File` 子類;只帶 nodeid / path。"""
+
+    def collect(self):
+        return []
+
+
+def _c_item(nodeid):
+    it = object.__new__(_CItem)
+    it._nodeid = nodeid
+    it.name = nodeid.split("::")[-1]
+    return it
+
+
+def _c_file(root, path):
+    f = object.__new__(_CFile)
+    f._nodeid = path
+    f.name = path.split("/")[-1]
+    f.path = pathlib.Path(str(root)) / path
+    return f
+
+
+class _CCollectReport:
+    def __init__(self, nodeid, result, failed=False):
+        self.nodeid = nodeid
+        self.result = list(result)
+        self.failed = failed
+        self.passed = not failed
+        self.skipped = False
+        self.outcome = "failed" if failed else "passed"
+
+
+class _CRunReport:
+    def __init__(self, nodeid, when, outcome, wasxfail=None):
+        self.nodeid = nodeid
+        self.fspath = nodeid.split("::", 1)[0]
+        self.when = when
+        self.outcome = outcome
+        self.passed = outcome == "passed"
+        self.failed = outcome == "failed"
+        self.skipped = outcome == "skipped"
+        if wasxfail is not None:
+            self.wasxfail = wasxfail
+
+
+def _c_reports(nodeid, kind):
+    """一個身分在 pytest 裡實際產生的 report 序列。
+
+    - passed / failed:setup → call → teardown
+    - skipped:setup(skipped)→ teardown,沒有 call
+    - xfail:setup → call(skipped,帶 `wasxfail`)→ teardown —— 明確辨識的 xfail
+    - setup_only:只有 setup(例:call 中 `pytest.exit()`,`_pytest/runner.py:262-267` 重拋,沒有 call / teardown report)
+    - setup_teardown:setup → teardown,沒有 call(`--setup-only`,`_pytest/runner.py:134-139`)
+    """
+    if kind in ("passed", "failed"):
+        return [_CRunReport(nodeid, "setup", "passed"),
+                _CRunReport(nodeid, "call", kind),
+                _CRunReport(nodeid, "teardown", "passed")]
+    if kind == "skipped":
+        return [_CRunReport(nodeid, "setup", "skipped"),
+                _CRunReport(nodeid, "teardown", "passed")]
+    if kind == "xfail":
+        return [_CRunReport(nodeid, "setup", "passed"),
+                _CRunReport(nodeid, "call", "skipped", wasxfail="reason"),
+                _CRunReport(nodeid, "teardown", "passed")]
+    if kind == "setup_only":
+        return [_CRunReport(nodeid, "setup", "passed")]
+    if kind == "setup_teardown":
+        return [_CRunReport(nodeid, "setup", "passed"),
+                _CRunReport(nodeid, "teardown", "passed")]
+    raise ValueError(kind)
+
+
+_C_OPTION_DEFAULTS = {
+    "pyargs": False, "lf": False, "last_failed_no_failures": "all",
+    "failedfirst": False, "newfirst": False, "stepwise": False, "stepwise_skip": False,
+    "stepwise_reset": False, "maxfail": None, "collectonly": False, "setuponly": False,
+    "setupplan": False, "setupshow": False, "keyword": "", "markexpr": "",
+    "deselect": None, "ignore": None, "ignore_glob": None,
+}
+
+
+class _COption:
+    """`config.option`:預設值為「全部關閉」(`maxfail` 預設 None,〈二十三〉2(f))。
+
+    `missing` 中的屬性不存在(例:`-p no:cacheprovider` 時沒有 `lf` / `stepwise`,〈二十三〉2(d))。
+    """
+
+    def __init__(self, missing=(), **overrides):
+        values = dict(_C_OPTION_DEFAULTS)
+        values.update(overrides)
+        for k in missing:
+            values.pop(k, None)
+        self.__dict__.update(values)
+
+
+class _CDist:
+    def __init__(self, name):
+        self.project_name = name
+        self.version = "0"
+        self.metadata = {"name": name}
+
+
+class _FakePluginManager:
+    """`config.pluginmanager` 的四個讀取點(`pluggy/_manager.py:235, 312, 422-429`)。"""
+
+    def __init__(self, name_plugins, distinfo=(), blocked=()):
+        self._name_plugins = list(name_plugins)
+        self._distinfo = list(distinfo)
+        self._blocked = set(blocked)
+
+    def list_name_plugin(self):
+        return list(self._name_plugins)
+
+    def list_plugin_distinfo(self):
+        return list(self._distinfo)
+
+    def is_blocked(self, name):
+        return name in self._blocked
+
+    def get_plugin(self, name):
+        return dict(self._name_plugins).get(name)
+
+    def has_plugin(self, name):
+        return self.get_plugin(name) is not None
+
+
+def _c_internal(module, label):
+    """類別定義在 `module` 的物件(模擬 `_pytest` 內部物件)。"""
+    return type(label, (), {"__module__": module})()
+
+
+def _c_plugins(c, root, extra=(), extra_dist=()):
+    """白名單內的 plugin 集合 + `extra`。
+
+    builtin:模組 `_pytest.main`、一個數字名稱(`str(id(...))`)而類別定義在 `_pytest.config` 的物件;
+    root_conftest:`<root>/tests/conftest.py`(絕對路徑,與 pytest 的 conftest 註冊名稱同形)—— 就是 producer 本身;
+    known_dist:`anyio.pytest_plugin`,在 `list_plugin_distinfo()` 中與 dist `anyio` 配對。
+    """
+    builtin_mod = _c_types.ModuleType("_pytest.main")
+    internal = _c_internal("_pytest.config", "_InternalHelper")
+    anyio_mod = _c_types.ModuleType("anyio.pytest_plugin")
+    names = [("main", builtin_mod),
+             (str(id(internal)), internal),
+             (_c_os.path.join(str(root), "tests", "conftest.py"), c),
+             ("anyio", anyio_mod)] + list(extra)
+    dist = [(anyio_mod, _CDist("anyio"))] + list(extra_dist)
+    return _FakePluginManager(names, dist)
+
+
+class _CInvocationParams:
+    def __init__(self, d):
+        self.dir = d
+
+
+class _CConfig:
+    def __init__(self, root, option, pluginmanager, args=("tests",)):
+        self.args = list(args)
+        self.args_source = pytest.Config.ArgsSource.TESTPATHS
+        self.rootpath = pathlib.Path(str(root))
+        self.invocation_params = _CInvocationParams(pathlib.Path(str(root)))
+        self.option = option
+        self.pluginmanager = pluginmanager
+
+    def getoption(self, name, default=None, skip=False):
+        return getattr(self.option, name, default)
+
+
+class _CompletenessSession:
+    def __init__(self, items, config):
+        self.items = list(items)
+        self.testscollected = len(self.items)
+        self.config = config
+        self.shouldstop = False
+        self.shouldfail = False
+
+
+def _c_call_collect_wrapper(c, collector, report):
+    """依 new-style wrapper 協定呼叫 conftest 的 `pytest_make_collect_report`(沒有就跳過)。"""
+    fn = getattr(c, "pytest_make_collect_report", None)
+    if fn is None:
+        return
+    gen = fn(collector)
+    if not _c_inspect.isgenerator(gen):
+        return
+    next(gen)
+    try:
+        gen.send(report)
+    except StopIteration:
+        pass
+
+
+def _c_drive(c, root, files, selected, outcomes=None, deselected=(), filtered_out=(),
+             collect_errors=(), exitstatus=0, option=None, pm=None,
+             shouldstop=False, shouldfail=False):
+    """依 pytest 9.1.1 的呼叫順序驅動 conftest(見本段開頭註解)。
+
+    `files`:{測試檔: 縮小前的完整 nodeid 清單};`filtered_out`:收集期被悄悄移除的身分
+    (不發 deselected 通知)。
+    """
+    def hook(name):
+        return getattr(c, name, None) or (lambda *a, **k: None)
+
+    dropped = set(filtered_out)
+    for path in sorted(files):
+        report = _CCollectReport(path, [_c_item(n) for n in files[path]])
+        _c_call_collect_wrapper(c, _c_file(root, path), report)
+        report.result[:] = [x for x in report.result if x.nodeid not in dropped]
+        hook("pytest_collectreport")(report)
+    for path in collect_errors:
+        hook("pytest_collectreport")(_CCollectReport(path, [], failed=True))
+    gone = [_c_item(n) for n in deselected]
+    if gone:
+        hook("pytest_deselected")(gone)
+    session = _CompletenessSession([_c_item(n) for n in selected],
+                                   _CConfig(root, option or _COption(), pm))
+    hook("pytest_collection_finish")(session)
+    for nodeid, kind in (outcomes or {}).items():
+        for rep in _c_reports(nodeid, kind):
+            hook("pytest_runtest_logreport")(rep)
+    session.shouldstop = shouldstop
+    session.shouldfail = shouldfail
+    hook("pytest_sessionfinish")(session, exitstatus)
+
+
+_C_MISSING = object()
+
+X_XF = "tests/test_x.py::test_xf"
+W_A = "tests/test_w.py::test_w_a"
+
+
+def _c_all_off(plugins=None):
+    """一份「全部關閉、白名單內」的完整性事實(consumer 側用;欄位名稱依〈二十三〉7)。"""
+    return {
+        "options": {"lf": False, "last_failed_no_failures": "all", "stepwise": False,
+                    "stepwise_skip": False, "maxfail": None, "collectonly": False,
+                    "setuponly": False, "setupplan": False},
+        "cacheprovider_blocked": False,
+        "shouldstop": False,
+        "shouldfail": False,
+        "pre_narrowing": {"tests/test_x.py": [X_A, X_B]},
+        "plugins": plugins if plugins is not None else [
+            {"name": "main", "kind": "builtin"},
+            {"name": "tests/conftest.py", "kind": "root_conftest"},
+            {"name": "anyio", "kind": "known_dist"},
+        ],
+    }
+
+
+def _c_raw_coverage(tmp_path, completeness=_C_MISSING):
+    """手寫一筆 session(全收集、全 passed、args `tests`)到 tmp root,讀回後判 `tests/test_x.py`。
+
+    除 `completeness` 外,形狀與 d122df4 的 producer 實際寫出的相同。
+    """
+    rec = {"kind": "session", "run_id": "c3-raw", "time": "2999-01-01T00:00:00+00:00",
+           "ticket_id": "99", "exit_code": 0, "collected": [X_A, X_B], "deselected": [],
+           "outcomes": {X_A: "passed", X_B: "passed"},
+           "invocation": {"args": ["tests"], "args_source": "TESTPATHS", "pyargs": False}}
+    if completeness is not _C_MISSING:
+        rec["completeness"] = completeness
+    path = redlight.session_log(str(tmp_path))
+    _c_os.makedirs(_c_os.path.dirname(path), exist_ok=True)
+    with io.open(path, "a", encoding="utf-8", newline="\n") as f:
+        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
+    runs = redlight.load_runs(str(tmp_path))
+    assert len(runs) == 1, runs
+    return redlight.file_coverage(runs[0], "tests/test_x.py")
+
+
+class TestCompletenessCoverage:
+
+    def test_c3a_lf_silent_narrowing_is_not_full_coverage(self, tmp_path, monkeypatch):
+        """C3a-1(〈二十三〉7 (ii)(v))。分類:behavior-red。
+
+        `--lf`:縮小前全集 [X_A, X_B],收集期悄悄移除 X_A(沒有 deselected 通知),
+        `session.items` 只剩 X_B 且 passed;`lfplugin-collskip` 已註冊(〈二十三〉2(e))。
+        d122df4 上失敗的原因:`.claude/hooks/redlight.py:405-406` 只看 deselected,
+        `:423-426` 位置參數 `tests` 為上層目錄 ⇒ `"true"`。
+        """
+        c = _isolated_conftest(monkeypatch, tmp_path)
+        skip_marker = _c_internal("_pytest.cacheprovider", "LFPluginCollSkipfiles")
+        wrapper = _c_internal("_pytest.cacheprovider", "LFPluginCollWrapper")
+        pm = _c_plugins(c, tmp_path, extra=[("lfplugin-collwrapper", wrapper),
+                                            ("lfplugin-collskip", skip_marker)])
+        _c_drive(c, tmp_path, {"tests/test_x.py": [X_A, X_B]}, selected=[X_B],
+                 outcomes={X_B: "passed"}, filtered_out=[X_A],
+                 option=_COption(lf=True), pm=pm, exitstatus=0)
+        runs = redlight.load_runs(str(tmp_path))
+        assert len(runs) == 1, runs
+        got = redlight.file_coverage(runs[0], "tests/test_x.py")
+        assert got != "true", got
+
+    def test_c3b_a_session_without_completeness_facts_is_not_full_coverage(self, tmp_path):
+        """C3b-1(〈二十三〉7 (i))。分類:behavior-red。
+
+        session 正好是 d122df4 的 producer 寫出的形狀,沒有 `completeness` ⇒ 不得為 `"true"`。
+        d122df4 上失敗的原因:`.claude/hooks/redlight.py:407-426` 不讀任何完整性事實 ⇒ `"true"`。
+        """
+        got = _c_raw_coverage(tmp_path)
+        assert got != "true", got
+
+    def test_c3b_a_malformed_completeness_fact_is_not_full_coverage(self, tmp_path):
+        """C3b-2(〈二十三〉7 (i))。分類:behavior-red。
+
+        `completeness` 存在,其餘全部關閉,但 `shouldstop` 是字串 `"False"`(型別錯)⇒ 不得為 `"true"`。
+        d122df4 上失敗的原因:`.claude/hooks/redlight.py:335-343` 不驗新欄位、`:407-426` 不讀它 ⇒ `"true"`。
+        """
+        comp = _c_all_off()
+        comp["shouldstop"] = "False"
+        got = _c_raw_coverage(tmp_path, comp)
+        assert got != "true", got
+
+    def test_c3c_an_exitfirst_run_is_not_full_coverage(self, tmp_path, monkeypatch):
+        """C3c-1(〈二十三〉7 (iii)(iv)(vi))。分類:behavior-red。
+
+        `-x`:`maxfail = 1`;W_A failed 後 `shouldfail` 設定、exit 1;X 全收集但沒有執行。
+        d122df4 上失敗的原因:`.claude/hooks/redlight.py:423-426` 不讀 maxfail / shouldfail ⇒ X 為 `"true"`。
+        """
+        c = _isolated_conftest(monkeypatch, tmp_path)
+        _c_drive(c, tmp_path, {"tests/test_w.py": [W_A], "tests/test_x.py": [X_A, X_B]},
+                 selected=[W_A, X_A, X_B], outcomes={W_A: "failed"},
+                 option=_COption(maxfail=1), pm=_c_plugins(c, tmp_path),
+                 shouldfail="stopping after 1 failures", exitstatus=1)
+        runs = redlight.load_runs(str(tmp_path))
+        assert len(runs) == 1, runs
+        got = redlight.file_coverage(runs[0], "tests/test_x.py")
+        assert got != "true", got
+
+    def test_c3p_an_unknown_plugin_dist_means_not_full_coverage(self, tmp_path):
+        """C3p-1 consumer(〈二十三〉3、7 (vii))。分類:behavior-red。
+
+        完整性事實全部關閉,`plugins` 多一項 `{"name": "evilplug", "kind": "other"}`(未知 dist)。
+        d122df4 上失敗的原因:`.claude/hooks/redlight.py:407-426` 不讀 plugins ⇒ `"true"`。
+        """
+        comp = _c_all_off()
+        comp["plugins"].append({"name": "evilplug", "kind": "other"})
+        got = _c_raw_coverage(tmp_path, comp)
+        assert got != "true", got
+
+    def test_c3p_a_plugin_loaded_by_name_means_not_full_coverage(self, tmp_path):
+        """C3p-2 consumer(〈二十三〉3、7 (vii))。分類:behavior-red。
+
+        完整性事實全部關閉,`plugins` 多一項 `{"name": "myplug", "kind": "other"}`(`-p myplug` 之類)。
+        d122df4 上失敗的原因:同 C3p-1。
+        """
+        comp = _c_all_off()
+        comp["plugins"].append({"name": "myplug", "kind": "other"})
+        got = _c_raw_coverage(tmp_path, comp)
+        assert got != "true", got
+
+    def test_c3p_an_extra_conftest_means_not_full_coverage(self, tmp_path):
+        """C3p-3 consumer(〈二十三〉3、7 (vii))。分類:behavior-red。
+
+        完整性事實全部關閉,`plugins` 多一項 `{"name": "tests/sub/conftest.py", "kind": "other"}`。
+        d122df4 上失敗的原因:同 C3p-1。
+        """
+        comp = _c_all_off()
+        comp["plugins"].append({"name": "tests/sub/conftest.py", "kind": "other"})
+        got = _c_raw_coverage(tmp_path, comp)
+        assert got != "true", got
+
+    def test_c3d_the_fixed_command_with_everything_off_is_full_coverage(self, tmp_path, monkeypatch):
+        """C3d-1(〈二十三〉7 全部條件成立)。分類:regression-lock。
+
+        固定全套:args `tests` / TESTPATHS、選項全部關閉、沒有 shouldstop / shouldfail、
+        縮小前全集 = 收集結果、plugin 全在白名單;X_A、X_B passed,X_XF 為明確辨識的 xfail
+        (call 為 skipped 且帶 `wasxfail`)⇒ `"true"`。
+        """
+        c = _isolated_conftest(monkeypatch, tmp_path)
+        _c_drive(c, tmp_path, {"tests/test_x.py": [X_A, X_B, X_XF]},
+                 selected=[X_A, X_B, X_XF],
+                 outcomes={X_A: "passed", X_B: "passed", X_XF: "xfail"},
+                 option=_COption(), pm=_c_plugins(c, tmp_path), exitstatus=0)
+        runs = redlight.load_runs(str(tmp_path))
+        assert len(runs) == 1, runs
+        got = redlight.file_coverage(runs[0], "tests/test_x.py")
+        assert got == "true", got
diff --git a/tests/test_status.py b/tests/test_status.py
index 196b304..f87511d 100644
--- a/tests/test_status.py
+++ b/tests/test_status.py
@@ -575,7 +575,15 @@ class TestTestsUnderTicketUsesTheLatestRecordPerFile:
             root, run_id=u"fixture-570-571", time=u"2026-09-02T02:00:00+00:00",
             ticket_id=u"99", exit_code=0, collected=[u"tests/test_a.py::test_one"],
             deselected=[], outcomes={u"tests/test_a.py::test_one": u"passed"},
-            invocation={u"args": [u"tests"]})
+            invocation={u"args": [u"tests"]},
+            completeness={
+                u"options": {u"lf": False, u"last_failed_no_failures": u"all", u"stepwise": False,
+                             u"stepwise_skip": False, u"maxfail": None, u"collectonly": False,
+                             u"setuponly": False, u"setupplan": False},
+                u"cacheprovider_blocked": False, u"shouldstop": False, u"shouldfail": False,
+                u"pre_narrowing": {u"tests/test_a.py": [u"tests/test_a.py::test_one"]},
+                u"plugins": [{u"name": u"main", u"kind": u"builtin"},
+                             {u"name": u"tests/conftest.py", u"kind": u"root_conftest"}]})
 
         out = render(root)
         red = _value_of(out, u"tests red under ticket 99")
@@ -1328,7 +1336,18 @@ class TestOrphans:
         redlight.record_session(root, run_id=u"odc2-2", time=u"2026-09-02T02:00:00+00:00",
                                 ticket_id=u"99", exit_code=0, collected=[new, keep],
                                 deselected=[], outcomes={new: u"passed", keep: u"passed"},
-                                invocation={u"args": [u"tests"]})
+                                invocation={u"args": [u"tests"]},
+                                completeness={
+                                    u"options": {u"lf": False, u"last_failed_no_failures": u"all",
+                                                 u"stepwise": False, u"stepwise_skip": False,
+                                                 u"maxfail": None, u"collectonly": False,
+                                                 u"setuponly": False, u"setupplan": False},
+                                    u"cacheprovider_blocked": False, u"shouldstop": False,
+                                    u"shouldfail": False,
+                                    u"pre_narrowing": {u"tests/test_x.py": [new, keep]},
+                                    u"plugins": [{u"name": u"main", u"kind": u"builtin"},
+                                                 {u"name": u"tests/conftest.py",
+                                                  u"kind": u"root_conftest"}]})
         out = render(root)
         orphaned = _value_of(out, u"tests orphaned under ticket 99")
         green = _value_of(out, u"tests green under ticket 99")
@@ -1697,8 +1716,8 @@ class TestChainRegressionLocks:
         root = _root_with_redlight(tmp_path)
         c = _chain_conftest(root, monkeypatch)
         _seed_red(["test_target"])
-        _chain_drive(c, root, ["tests"], selected=[CHAIN_X, CHAIN_Y],
-                     outcomes={CHAIN_X: "passed", CHAIN_Y: "passed"}, exitstatus=0)
+        _s_drive(c, root, {u"tests/test_x.py": [CHAIN_X, CHAIN_Y]}, selected=[CHAIN_X, CHAIN_Y],
+                 outcomes={CHAIN_X: "passed", CHAIN_Y: "passed"}, exitstatus=0)
         got = _lines_of(root)
         assert u"tests/test_x.py" in got[u"green"], got
         assert u"tests/test_x.py" not in got[u"red"], got
@@ -1753,3 +1772,527 @@ class TestMalformedSessionIsVisible:
         assert u"tests/test_x.py" in red, after
         assert u"tests/test_x.py" not in green, after
         assert u"tests/test_x.py" not in orphaned, after
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 票 145 Station 3c 紅燈 —— 選擇 / 執行完整性與 plugin 邊界(串接;〈二十三〉)
+#
+# 合約:票 145〈二十三〉7、8。每一支都經**真實 tests/conftest.py** 的 hook(`_chain_conftest`)
+# 寫入 tmp root 的帳本,再由 status / `file_coverage` 讀回判定 —— 不直接餵分類好的資料。
+# 規劃:docs/audits/2026-10-02-m1a-station3c-redlight-plan.md P4。
+#
+# driver(`_s_drive`)的呼叫順序與 tests/test_redlight.py 的 `_c_drive` 相同:
+# 每個檔先對 conftest 的 `pytest_make_collect_report`(new-style wrapper)送出**完整**結果,
+# wrapper 返回後才**就地**縮小 `report.result`(模擬外層 `LFPluginCollWrapper`,
+# `_pytest/cacheprovider.py:282`);縮小掉的身分**不**送 `pytest_deselected`。
+# 假 item / collector 是 `pytest.Item` / `pytest.File` 的子類(`object.__new__`,不經 `from_parent`)。
+# 本段 helper 全部新寫;既有 helper(`_chain_conftest` / `_seed_red` / `_lines_of`)只呼叫、不修改。
+# ═══════════════════════════════════════════════════════════════════════════
+
+import inspect as _s_inspect
+import types as _s_types
+
+
+class _SItem(pytest.Item):
+    def runtest(self):
+        pass
+
+
+class _SFile(pytest.File):
+    def collect(self):
+        return []
+
+
+def _s_item(nodeid):
+    it = object.__new__(_SItem)
+    it._nodeid = nodeid
+    it.name = nodeid.split(u"::")[-1]
+    return it
+
+
+def _s_file(root, path):
+    f = object.__new__(_SFile)
+    f._nodeid = path
+    f.name = path.split(u"/")[-1]
+    f.path = pathlib.Path(str(root)) / path
+    return f
+
+
+class _SCollectReport:
+    def __init__(self, nodeid, result, failed=False):
+        self.nodeid = nodeid
+        self.result = list(result)
+        self.failed = failed
+        self.passed = not failed
+        self.skipped = False
+        self.outcome = "failed" if failed else "passed"
+
+
+class _SRunReport:
+    def __init__(self, nodeid, when, outcome, wasxfail=None):
+        self.nodeid = nodeid
+        self.fspath = nodeid.split(u"::", 1)[0]
+        self.when = when
+        self.outcome = outcome
+        self.passed = outcome == "passed"
+        self.failed = outcome == "failed"
+        self.skipped = outcome == "skipped"
+        if wasxfail is not None:
+            self.wasxfail = wasxfail
+
+
+def _s_reports(nodeid, kind):
+    """passed / failed:setup → call → teardown;skipped:setup(skipped)→ teardown;
+    xfail:call 為 skipped 且帶 `wasxfail`;setup_only:只有 setup(call 中 `pytest.exit()`);
+    setup_teardown:沒有 call(`--setup-only`)。"""
+    if kind in ("passed", "failed"):
+        return [_SRunReport(nodeid, "setup", "passed"),
+                _SRunReport(nodeid, "call", kind),
+                _SRunReport(nodeid, "teardown", "passed")]
+    if kind == "skipped":
+        return [_SRunReport(nodeid, "setup", "skipped"),
+                _SRunReport(nodeid, "teardown", "passed")]
+    if kind == "xfail":
+        return [_SRunReport(nodeid, "setup", "passed"),
+                _SRunReport(nodeid, "call", "skipped", wasxfail="reason"),
+                _SRunReport(nodeid, "teardown", "passed")]
+    if kind == "setup_only":
+        return [_SRunReport(nodeid, "setup", "passed")]
+    if kind == "setup_teardown":
+        return [_SRunReport(nodeid, "setup", "passed"),
+                _SRunReport(nodeid, "teardown", "passed")]
+    raise ValueError(kind)
+
+
+_S_OPTION_DEFAULTS = {
+    "pyargs": False, "lf": False, "last_failed_no_failures": "all",
+    "failedfirst": False, "newfirst": False, "stepwise": False, "stepwise_skip": False,
+    "stepwise_reset": False, "maxfail": None, "collectonly": False, "setuponly": False,
+    "setupplan": False, "setupshow": False, "keyword": "", "markexpr": "",
+    "deselect": None, "ignore": None, "ignore_glob": None,
+}
+
+
+class _CompletenessOption:
+    """`config.option`,預設「全部關閉」;`missing` 中的屬性不存在。"""
+
+    def __init__(self, missing=(), **overrides):
+        values = dict(_S_OPTION_DEFAULTS)
+        values.update(overrides)
+        for k in missing:
+            values.pop(k, None)
+        self.__dict__.update(values)
+
+
+class _SDist:
+    def __init__(self, name):
+        self.project_name = name
+        self.version = "0"
+        self.metadata = {"name": name}
+
+
+class _SFakePluginManager:
+    """`config.pluginmanager`:list_name_plugin / list_plugin_distinfo / is_blocked / get_plugin。"""
+
+    def __init__(self, name_plugins, distinfo=(), blocked=()):
+        self._name_plugins = list(name_plugins)
+        self._distinfo = list(distinfo)
+        self._blocked = set(blocked)
+
+    def list_name_plugin(self):
+        return list(self._name_plugins)
+
+    def list_plugin_distinfo(self):
+        return list(self._distinfo)
+
+    def is_blocked(self, name):
+        return name in self._blocked
+
+    def get_plugin(self, name):
+        return dict(self._name_plugins).get(name)
+
+    def has_plugin(self, name):
+        return self.get_plugin(name) is not None
+
+
+def _s_internal(module, label):
+    return type(label, (), {"__module__": module})()
+
+
+def _s_plugins(c, root, extra=(), extra_dist=()):
+    """白名單內的 plugin 集合(builtin / root_conftest / known_dist)+ `extra`。
+
+    builtin:模組 `_pytest.main`,以及數字名稱(`str(id(...))`)、類別定義在 `_pytest.config` 的物件;
+    root_conftest:`<root>/tests/conftest.py` 的絕對路徑 → producer 本身;
+    known_dist:`anyio.pytest_plugin`,在 `list_plugin_distinfo()` 中與 dist `anyio` 配對。
+    """
+    builtin_mod = _s_types.ModuleType("_pytest.main")
+    internal = _s_internal("_pytest.config", "_InternalHelper")
+    anyio_mod = _s_types.ModuleType("anyio.pytest_plugin")
+    names = [(u"main", builtin_mod),
+             (str(id(internal)), internal),
+             (os.path.join(str(root), u"tests", u"conftest.py"), c),
+             (u"anyio", anyio_mod)] + list(extra)
+    dist = [(anyio_mod, _SDist("anyio"))] + list(extra_dist)
+    return _SFakePluginManager(names, dist)
+
+
+class _SInvocationParams:
+    def __init__(self, d):
+        self.dir = d
+
+
+class _SConfig:
+    def __init__(self, root, option, pluginmanager, args=(u"tests",)):
+        self.args = list(args)
+        self.args_source = pytest.Config.ArgsSource.TESTPATHS
+        self.rootpath = pathlib.Path(str(root))
+        self.invocation_params = _SInvocationParams(pathlib.Path(str(root)))
+        self.option = option
+        self.pluginmanager = pluginmanager
+
+    def getoption(self, name, default=None, skip=False):
+        return getattr(self.option, name, default)
+
+
+class _CompletenessSession:
+    def __init__(self, items, config):
+        self.items = list(items)
+        self.testscollected = len(self.items)
+        self.config = config
+        self.shouldstop = False
+        self.shouldfail = False
+
+
+def _s_call_collect_wrapper(c, collector, report):
+    fn = getattr(c, "pytest_make_collect_report", None)
+    if fn is None:
+        return
+    gen = fn(collector)
+    if not _s_inspect.isgenerator(gen):
+        return
+    next(gen)
+    try:
+        gen.send(report)
+    except StopIteration:
+        pass
+
+
+def _s_drive(c, root, files, selected, outcomes=None, deselected=(), filtered_out=(),
+             collect_errors=(), exitstatus=0, option=None, pm=None,
+             shouldstop=False, shouldfail=False):
+    """依 pytest 9.1.1 的呼叫順序驅動真實 conftest;`files` = {檔: 縮小前完整 nodeid 清單}。"""
+    def hook(name):
+        return getattr(c, name, None) or (lambda *a, **k: None)
+
+    if pm is None:
+        pm = _s_plugins(c, root)
+    dropped = set(filtered_out)
+    for path in sorted(files):
+        report = _SCollectReport(path, [_s_item(n) for n in files[path]])
+        _s_call_collect_wrapper(c, _s_file(root, path), report)
+        report.result[:] = [x for x in report.result if x.nodeid not in dropped]
+        hook("pytest_collectreport")(report)
+    for path in collect_errors:
+        hook("pytest_collectreport")(_SCollectReport(path, [], failed=True))
+    gone = [_s_item(n) for n in deselected]
+    if gone:
+        hook("pytest_deselected")(gone)
+    session = _CompletenessSession([_s_item(n) for n in selected],
+                                   _SConfig(root, option or _CompletenessOption(), pm))
+    hook("pytest_collection_finish")(session)
+    for nodeid, kind in (outcomes or {}).items():
+        for rep in _s_reports(nodeid, kind):
+            hook("pytest_runtest_logreport")(rep)
+    session.shouldstop = shouldstop
+    session.shouldfail = shouldfail
+    hook("pytest_sessionfinish")(session, exitstatus)
+
+
+S_A = u"tests/test_x.py::test_a"
+S_B = u"tests/test_x.py::test_b"
+S_C = u"tests/test_x.py::test_c"
+S_XF = u"tests/test_x.py::test_xf"
+S_NEW = u"tests/test_x.py::test_new"
+S_KEEP = u"tests/test_x.py::test_keep"
+S_W = u"tests/test_w.py::test_w_a"
+
+
+def _s_lf_pm(c, root):
+    """`--lf` 真的過濾時的 plugin 集合:多了 `lfplugin-collwrapper` 與 `lfplugin-collskip`(皆為 builtin)。"""
+    return _s_plugins(c, root, extra=[
+        (u"lfplugin-collwrapper", _s_internal("_pytest.cacheprovider", "LFPluginCollWrapper")),
+        (u"lfplugin-collskip", _s_internal("_pytest.cacheprovider", "LFPluginCollSkipfiles"))])
+
+
+def _s_drive_lf(c, root):
+    """`--lf`:縮小前全集 [S_A, S_B],S_A 在收集期被悄悄移除,只跑 S_B 且 passed,exit 0。"""
+    _s_drive(c, root, {u"tests/test_x.py": [S_A, S_B]}, selected=[S_B],
+             outcomes={S_B: "passed"}, filtered_out=[S_A],
+             option=_CompletenessOption(lf=True), pm=_s_lf_pm(c, root), exitstatus=0)
+
+
+def _s_drive_exitfirst(c, root, x_ids):
+    """`-x`:S_W failed ⇒ `shouldfail`、exit 1;X 全收集(`x_ids`)但沒有執行。"""
+    _s_drive(c, root, {u"tests/test_w.py": [S_W], u"tests/test_x.py": list(x_ids)},
+             selected=[S_W] + list(x_ids), outcomes={S_W: "failed"},
+             option=_CompletenessOption(maxfail=1),
+             shouldfail=u"stopping after 1 failures", exitstatus=1)
+
+
+class TestSilentNarrowingChain:
+
+    def test_c3a_lf_narrowing_does_not_retire_an_unidentified_red(self, tmp_path, monkeypatch):
+        """C3a-2(〈二十三〉7 (ii)(v))。分類:behavior-red。
+
+        test_x.py 有身分不明的整檔紅;之後一次 `--lf` 只跑了 S_B(S_A 被悄悄移除)⇒ 仍紅、不 green。
+        d122df4 上失敗的原因:`.claude/hooks/redlight.py:423-426` 判 `"true"` ⇒
+        `.claude/portable/status.py:470-472` 整檔紅只看本 run 收集到的身分 ⇒ 退紅;`:475` green。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        _seed_red([])
+        _s_drive_lf(c, root)
+        got = _lines_of(root)
+        assert u"tests/test_x.py" in got[u"red"], got
+        assert u"tests/test_x.py" not in got[u"green"], got
+
+    def test_c3a_lf_narrowing_does_not_make_a_clean_file_green(self, tmp_path, monkeypatch):
+        """C3a-3(〈二十一〉21.2 附註 2;〈二十三〉7 (ii)(v))。分類:behavior-red。
+
+        test_x.py 先前沒有紅;一次 `--lf` 只跑了 S_B ⇒ 不得 green。
+        d122df4 上失敗的原因:`.claude/hooks/redlight.py:423-426` 判 `"true"` ⇒
+        `.claude/portable/status.py:475` `green_now = True`。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        _s_drive_lf(c, root)
+        got = _lines_of(root)
+        assert u"tests/test_x.py" not in got[u"green"], got
+
+
+class TestEarlyStopChain:
+
+    def test_c3c_exitfirst_does_not_orphan_a_known_red(self, tmp_path, monkeypatch):
+        """C3c-2(〈二十三〉7 (iii)(iv)(vi))。分類:behavior-red。
+
+        X 有已知紅 test_old;之後一次 `-x` 在 W 停下,X 收集到 [test_new, test_keep] 但沒執行
+        ⇒ X 仍紅、不 orphan(提前停止的 run 沒有 orphan 權)。
+        d122df4 上失敗的原因:`.claude/hooks/redlight.py:423-426` 判 `"true"` ⇒
+        `.claude/portable/status.py:464-468` 把 test_old 移入 orphan。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        _seed_red(["test_old"])
+        _s_drive_exitfirst(c, root, [S_NEW, S_KEEP])
+        got = _lines_of(root)
+        assert u"tests/test_x.py" not in got[u"orphaned"], got
+        assert u"tests/test_x.py" in got[u"red"], got
+
+    def test_c3c_exitfirst_does_not_make_unrun_files_green(self, tmp_path, monkeypatch):
+        """C3c-3。分類:regression-lock。
+
+        一次 `-x` 在 W 停下,X 全收集但沒有任何 outcome ⇒ X 不 green
+        (d122df4:`.claude/portable/status.py:475` 沒有 passed ⇒ 不 green)。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        _s_drive_exitfirst(c, root, [S_A, S_B])
+        got = _lines_of(root)
+        assert u"tests/test_x.py" not in got[u"green"], got
+
+    def test_c3c_stepwise_stop_is_d_and_retires_nothing(self, tmp_path, monkeypatch):
+        """C3c-4。分類:regression-lock。
+
+        `--sw`:S_W failed ⇒ `shouldstop` ⇒ `Interrupted` ⇒ exit 2(`_pytest/stepwise.py:183-188`、
+        `_pytest/main.py:411-412`)。X 的已知紅 CHAIN_X 本次 passed ⇒ D 沒有退紅權:仍紅、不 green、不 orphan
+        (d122df4:`.claude/portable/status.py:456-458`)。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        _seed_red(["test_target"])
+        _s_drive(c, root, {u"tests/test_w.py": [S_W], u"tests/test_x.py": [CHAIN_X, CHAIN_Y]},
+                 selected=[CHAIN_X, CHAIN_Y, S_W],
+                 outcomes={CHAIN_X: "passed", CHAIN_Y: "passed", S_W: "failed"},
+                 option=_CompletenessOption(stepwise=True),
+                 shouldstop=u"Test failed, continuing from this test next run.", exitstatus=2)
+        got = _lines_of(root)
+        assert u"tests/test_x.py" in got[u"red"], got
+        assert u"tests/test_x.py" not in got[u"green"], got
+        assert u"tests/test_x.py" not in got[u"orphaned"], got
+
+    def test_c3c_pytest_exit_zero_partial_file_is_not_green(self, tmp_path, monkeypatch):
+        """C3c-5(〈二十三〉2(b)、7 (vi))。分類:behavior-red。
+
+        測試內 `pytest.exit(returncode=0)`:S_A passed;S_B 只有 setup report、沒有 call;
+        S_C 沒有任何 report;exit 0;`shouldstop` / `shouldfail` 皆為 False ⇒ X 不得 green。
+        d122df4 上失敗的原因:`.claude/hooks/redlight.py:423-426` 判 `"true"` ⇒
+        `.claude/portable/status.py:475` `"passed" in results` ⇒ green。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        _s_drive(c, root, {u"tests/test_x.py": [S_A, S_B, S_C]}, selected=[S_A, S_B, S_C],
+                 outcomes={S_A: "passed", S_B: "setup_only"}, exitstatus=0)
+        got = _lines_of(root)
+        assert u"tests/test_x.py" not in got[u"green"], got
+
+    def test_setup_only_run_is_not_green(self, tmp_path, monkeypatch):
+        """C3x-1(規劃檔 P2(a))。分類:regression-lock。
+
+        `--setup-only`:每個身分只有 setup / teardown passed、沒有 call;exit 0 ⇒ 不 green
+        (d122df4:`tests/conftest.py:198-199` 只從 call 取 passed)。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        _s_drive(c, root, {u"tests/test_x.py": [S_A, S_B]}, selected=[S_A, S_B],
+                 outcomes={S_A: "setup_teardown", S_B: "setup_teardown"},
+                 option=_CompletenessOption(setuponly=True), exitstatus=0)
+        got = _lines_of(root)
+        assert u"tests/test_x.py" not in got[u"green"], got
+
+
+class TestLfFalseGreenChain:
+
+    def test_c3e_full_then_lf_does_not_produce_a_false_green(self, tmp_path, monkeypatch):
+        """C3e-1(〈二十一〉21.2 三步情境)。分類:behavior-red。
+
+        R1:test_x.py 收集錯誤(exit 2)⇒ 整檔紅。R2:全套,S_A passed、S_B failed(exit 1)⇒
+        red = {整檔, S_B}。R3:`--lf`,縮小前全集 [S_A, S_B],S_A 被悄悄移除,S_B passed(exit 0)
+        ⇒ 仍紅、不 green。
+        每次執行各自載入新的 conftest,模擬獨立的 pytest 程序(3c-1b 修正)。
+        情境斷言:R1 的 session 判 D、R2 判 B、R3 判 A 且 schema 合格。
+        d122df4 上失敗的原因:R3 在 `.claude/hooks/redlight.py:423-426` 判 `"true"` ⇒
+        `.claude/portable/status.py:470-474` 退掉整檔紅與 S_B ⇒ `:475` green。
+        """
+        root = _root_with_redlight(tmp_path)
+        c1 = _chain_conftest(root, monkeypatch)
+        _s_drive(c1, root, {}, selected=[], collect_errors=[u"tests/test_x.py"], exitstatus=2)
+        c2 = _chain_conftest(root, monkeypatch)
+        _s_drive(c2, root, {u"tests/test_x.py": [S_A, S_B]}, selected=[S_A, S_B],
+                 outcomes={S_A: "passed", S_B: "failed"}, exitstatus=1)
+        c3 = _chain_conftest(root, monkeypatch)
+        _s_drive_lf(c3, root)
+        runs = redlight.load_runs(root)
+        assert len(runs) == 3, runs
+        assert redlight.run_state(runs[0]) == u"D", runs[0]
+        assert redlight.run_state(runs[1]) == u"B", runs[1]
+        assert redlight.validate_session(runs[2]) == [], runs[2]
+        assert redlight.run_state(runs[2]) == u"A", runs[2]
+        got = _lines_of(root)
+        assert u"tests/test_x.py" in got[u"red"], got
+        assert u"tests/test_x.py" not in got[u"green"], got
+
+
+class TestCompletenessLocks:
+
+    def test_c3d_the_fixed_command_full_run_still_retires_the_red(self, tmp_path, monkeypatch):
+        """C3d-2(〈二十三〉7 全部條件成立)。分類:regression-lock。
+
+        X 的已知紅 CHAIN_X;之後一次固定全套(選項全部關閉、plugin 全在白名單、縮小前全集 = 收集結果),
+        CHAIN_X / CHAIN_Y passed,S_XF 為明確辨識的 xfail ⇒ X 退紅、在 green。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        _seed_red(["test_target"])
+        _s_drive(c, root, {u"tests/test_x.py": [CHAIN_X, CHAIN_Y, S_XF]},
+                 selected=[CHAIN_X, CHAIN_Y, S_XF],
+                 outcomes={CHAIN_X: "passed", CHAIN_Y: "passed", S_XF: "xfail"}, exitstatus=0)
+        got = _lines_of(root)
+        assert u"tests/test_x.py" in got[u"green"], got
+        assert u"tests/test_x.py" not in got[u"red"], got
+
+
+def _s_full_run_session(c, root, pm):
+    """test_x.py 全收集、全 passed、其餘完整性事實全部關閉;回傳讀回的最後一筆 session。"""
+    _s_drive(c, root, {u"tests/test_x.py": [S_A, S_B]}, selected=[S_A, S_B],
+             outcomes={S_A: "passed", S_B: "passed"}, pm=pm, exitstatus=0)
+    runs = redlight.load_runs(root)
+    assert runs, runs
+    return runs[-1]
+
+
+def _s_plugin_kinds(run):
+    """持久化 session 的 `completeness.plugins` → {正規化名稱: kind}。缺欄即失敗(不推論)。"""
+    comp = run.get("completeness")
+    assert isinstance(comp, dict), u"session 沒有 completeness:%r" % (run,)
+    plugins = comp.get("plugins")
+    assert isinstance(plugins, list), u"completeness 沒有 plugins:%r" % (comp,)
+    return dict((p.get("name"), p.get("kind")) for p in plugins)
+
+
+class TestPluginProducerChain:
+
+    def test_c3p_producer_classifies_an_unknown_dist_plugin_as_other(self, tmp_path, monkeypatch):
+        """C3p-4(〈二十三〉3 (3)、7 plugins / (vii))。分類:behavior-red。
+
+        多一個 plugin 物件(模組 `evilplug.plugin`),在 `list_plugin_distinfo()` 中配對到 dist `evil-dist`
+        ⇒ 持久化的 plugins 有一項 kind == "other",且 `file_coverage != "true"`。
+        d122df4 上失敗的原因:`tests/conftest.py:222-246` 不記 completeness ⇒ session 沒有 `completeness`。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        evil = _s_types.ModuleType("evilplug.plugin")
+        pm = _s_plugins(c, root, extra=[(u"evilplug", evil)], extra_dist=[(evil, _SDist("evil-dist"))])
+        run = _s_full_run_session(c, root, pm)
+        kinds = _s_plugin_kinds(run)
+        assert kinds.get(u"evilplug") == u"other", kinds
+        got = redlight.file_coverage(run, u"tests/test_x.py")
+        assert got != u"true", got
+
+    def test_c3p_producer_classifies_a_plugin_loaded_by_name_as_other(self, tmp_path, monkeypatch):
+        """C3p-5(〈二十三〉3、7 plugins / (vii))。分類:behavior-red。
+
+        多一個以名稱 `myplug` 註冊的模組 `myplug`(模擬 `-p myplug`),不在 `list_plugin_distinfo()`
+        ⇒ kind == "other",且 `file_coverage != "true"`。
+        d122df4 上失敗的原因:同 C3p-4。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        pm = _s_plugins(c, root, extra=[(u"myplug", _s_types.ModuleType("myplug"))])
+        run = _s_full_run_session(c, root, pm)
+        kinds = _s_plugin_kinds(run)
+        assert kinds.get(u"myplug") == u"other", kinds
+        got = redlight.file_coverage(run, u"tests/test_x.py")
+        assert got != u"true", got
+
+    def test_c3p_producer_classifies_an_extra_conftest_as_other_and_the_root_conftest_as_root_conftest(
+            self, tmp_path, monkeypatch):
+        """C3p-6(〈二十三〉3 (2)、7 plugins / (vii))。分類:behavior-red。
+
+        除 `<root>/tests/conftest.py` 外,多一個名稱為 `<root>/tests/sub/conftest.py` 絕對路徑的 conftest
+        ⇒ 前者 kind == "root_conftest"、後者 kind == "other"(名稱記 root 相對路徑),`file_coverage != "true"`;
+        持久化的 session 那一行文字不得包含 tmp root 的絕對路徑。
+        d122df4 上失敗的原因:同 C3p-4。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        sub = os.path.join(str(root), u"tests", u"sub", u"conftest.py")
+        pm = _s_plugins(c, root, extra=[(sub, _s_types.ModuleType("conftest"))])
+        run = _s_full_run_session(c, root, pm)
+        kinds = _s_plugin_kinds(run)
+        assert kinds.get(u"tests/sub/conftest.py") == u"other", kinds
+        assert kinds.get(u"tests/conftest.py") == u"root_conftest", kinds
+        got = redlight.file_coverage(run, u"tests/test_x.py")
+        assert got != u"true", got
+        with io.open(redlight.session_log(root), encoding="utf-8") as f:
+            text = f.read()
+        for form in set([str(root), str(root).replace(u"\\", u"/"), json.dumps(str(root))[1:-1]]):
+            assert form not in text, u"帳本出現絕對路徑:%s" % form
+
+    def test_c3p_producer_classifies_builtin_root_conftest_and_known_dist_as_not_other(
+            self, tmp_path, monkeypatch):
+        """C3p-7(〈二十三〉3 (1)(2)(3)、7 全部條件)。分類:behavior-red。
+
+        只有 `_pytest` 內建物件(含一個數字名稱、類別定義在 `_pytest.config` 的物件)、root `tests/conftest.py`、
+        以及在 `list_plugin_distinfo()` 中配對到 dist `anyio` 的 `anyio.pytest_plugin`
+        ⇒ 每一項 kind 都不是 "other",且 `file_coverage == "true"`。
+        d122df4 上失敗的原因:同 C3p-4(session 沒有 `completeness`)。
+        """
+        root = _root_with_redlight(tmp_path)
+        c = _chain_conftest(root, monkeypatch)
+        run = _s_full_run_session(c, root, _s_plugins(c, root))
+        kinds = _s_plugin_kinds(run)
+        assert kinds, kinds
+        assert all(k != u"other" for k in kinds.values()), kinds
+        got = redlight.file_coverage(run, u"tests/test_x.py")
+        assert got == u"true", got
```

### E.3 `git diff 49bcde20adc276632fa5bab456e8c7a80839fc0b..02a5e28adf5aee11a43d5a1063504f01beb1d67f -- tests/test_redlight.py tests/test_status.py`

(3c-1b 之後的測試改動 = Station 4c 授權補件。)

```diff
diff --git a/tests/test_redlight.py b/tests/test_redlight.py
index 2b0ef34..efb3600 100644
--- a/tests/test_redlight.py
+++ b/tests/test_redlight.py
@@ -526,7 +526,15 @@ class TestFileCoverage:
 
         位置參數 `tests/test_x.py`(不含 `::`)、無 deselected ⇒ 整檔涵蓋。
         """
-        got = self._coverage_after(tmp_path, monkeypatch, ["tests/test_x.py"], [X_A, X_B])
+        c = _isolated_conftest(monkeypatch, tmp_path)
+        _c_call_collect_wrapper(c, _c_file(tmp_path, "tests/test_x.py"),
+                                _CCollectReport("tests/test_x.py", [_c_item(X_A), _c_item(X_B)]))
+        session = _CompletenessSession([_c_item(X_A), _c_item(X_B)],
+                                       _CConfig(tmp_path, _COption(), _c_plugins(c, tmp_path),
+                                                args=["tests/test_x.py"]))
+        _drive_with_session(c, session, selected=[X_A, X_B],
+                            outcomes={X_A: "passed", X_B: "passed"}, exitstatus=0)
+        got = redlight.file_coverage(redlight.load_runs(str(tmp_path))[0], "tests/test_x.py")
         assert got == "true", got
 
     def test_b1d_a_parent_directory_argument_is_full_coverage(self, tmp_path, monkeypatch):
@@ -534,7 +542,15 @@ class TestFileCoverage:
 
         位置參數 `tests`(上層目錄)、無 deselected ⇒ 整檔涵蓋。
         """
-        got = self._coverage_after(tmp_path, monkeypatch, ["tests"], [X_A, X_B])
+        c = _isolated_conftest(monkeypatch, tmp_path)
+        _c_call_collect_wrapper(c, _c_file(tmp_path, "tests/test_x.py"),
+                                _CCollectReport("tests/test_x.py", [_c_item(X_A), _c_item(X_B)]))
+        session = _CompletenessSession([_c_item(X_A), _c_item(X_B)],
+                                       _CConfig(tmp_path, _COption(), _c_plugins(c, tmp_path),
+                                                args=["tests"]))
+        _drive_with_session(c, session, selected=[X_A, X_B],
+                            outcomes={X_A: "passed", X_B: "passed"}, exitstatus=0)
+        got = redlight.file_coverage(redlight.load_runs(str(tmp_path))[0], "tests/test_x.py")
         assert got == "true", got
 
     def test_b1e_a_file_argument_with_deselection_is_not_full_coverage(self, tmp_path, monkeypatch):
@@ -624,6 +640,12 @@ class TestFixedCommandCoverage:
         c = _isolated_conftest(monkeypatch, tmp_path)
         session = _SessionWithConfig([_Item(X_A), _Item(X_B)], ["tests"], tmp_path)
         session.config.args_source = pytest.Config.ArgsSource.TESTPATHS
+        session.config.option = _COption()
+        session.config.pluginmanager = _c_plugins(c, tmp_path)
+        session.shouldstop = False
+        session.shouldfail = False
+        _c_call_collect_wrapper(c, _c_file(tmp_path, "tests/test_x.py"),
+                                _CCollectReport("tests/test_x.py", [_c_item(X_A), _c_item(X_B)]))
         _drive_with_session(c, session, selected=[X_A, X_B],
                             outcomes={X_A: "passed", X_B: "passed"}, exitstatus=0)
         runs = redlight.load_runs(str(tmp_path))
diff --git a/tests/test_status.py b/tests/test_status.py
index 36f0fae..f87511d 100644
--- a/tests/test_status.py
+++ b/tests/test_status.py
@@ -575,7 +575,15 @@ class TestTestsUnderTicketUsesTheLatestRecordPerFile:
             root, run_id=u"fixture-570-571", time=u"2026-09-02T02:00:00+00:00",
             ticket_id=u"99", exit_code=0, collected=[u"tests/test_a.py::test_one"],
             deselected=[], outcomes={u"tests/test_a.py::test_one": u"passed"},
-            invocation={u"args": [u"tests"]})
+            invocation={u"args": [u"tests"]},
+            completeness={
+                u"options": {u"lf": False, u"last_failed_no_failures": u"all", u"stepwise": False,
+                             u"stepwise_skip": False, u"maxfail": None, u"collectonly": False,
+                             u"setuponly": False, u"setupplan": False},
+                u"cacheprovider_blocked": False, u"shouldstop": False, u"shouldfail": False,
+                u"pre_narrowing": {u"tests/test_a.py": [u"tests/test_a.py::test_one"]},
+                u"plugins": [{u"name": u"main", u"kind": u"builtin"},
+                             {u"name": u"tests/conftest.py", u"kind": u"root_conftest"}]})
 
         out = render(root)
         red = _value_of(out, u"tests red under ticket 99")
@@ -1328,7 +1336,18 @@ class TestOrphans:
         redlight.record_session(root, run_id=u"odc2-2", time=u"2026-09-02T02:00:00+00:00",
                                 ticket_id=u"99", exit_code=0, collected=[new, keep],
                                 deselected=[], outcomes={new: u"passed", keep: u"passed"},
-                                invocation={u"args": [u"tests"]})
+                                invocation={u"args": [u"tests"]},
+                                completeness={
+                                    u"options": {u"lf": False, u"last_failed_no_failures": u"all",
+                                                 u"stepwise": False, u"stepwise_skip": False,
+                                                 u"maxfail": None, u"collectonly": False,
+                                                 u"setuponly": False, u"setupplan": False},
+                                    u"cacheprovider_blocked": False, u"shouldstop": False,
+                                    u"shouldfail": False,
+                                    u"pre_narrowing": {u"tests/test_x.py": [new, keep]},
+                                    u"plugins": [{u"name": u"main", u"kind": u"builtin"},
+                                                 {u"name": u"tests/conftest.py",
+                                                  u"kind": u"root_conftest"}]})
         out = render(root)
         orphaned = _value_of(out, u"tests orphaned under ticket 99")
         green = _value_of(out, u"tests green under ticket 99")
@@ -1697,8 +1716,8 @@ class TestChainRegressionLocks:
         root = _root_with_redlight(tmp_path)
         c = _chain_conftest(root, monkeypatch)
         _seed_red(["test_target"])
-        _chain_drive(c, root, ["tests"], selected=[CHAIN_X, CHAIN_Y],
-                     outcomes={CHAIN_X: "passed", CHAIN_Y: "passed"}, exitstatus=0)
+        _s_drive(c, root, {u"tests/test_x.py": [CHAIN_X, CHAIN_Y]}, selected=[CHAIN_X, CHAIN_Y],
+                 outcomes={CHAIN_X: "passed", CHAIN_Y: "passed"}, exitstatus=0)
         got = _lines_of(root)
         assert u"tests/test_x.py" in got[u"green"], got
         assert u"tests/test_x.py" not in got[u"red"], got
```

---

## F. 實測證據(逐字)

### F.1 Station 3c 紅燈證據 —— 兩次驗收與帳本 H0 → H1 → H2

出處:`02a5e28adf5aee11a43d5a1063504f01beb1d67f:docs/audits/2026-10-02-m1a-station3c-redlight.md`;該檔在 TARGET 的 blob ID:`1053342b0d103392a5a313ae490f5027c33db4e5`。
以下三段逐字照錄;原報告中已就地註明的截斷 / 遮罩說明一併保留(那些行本身不是 pytest 原始輸出)。

行號來源:同檔第 59–93 行

<!-- 逐字開始 -->
## 3. 第一次驗收(在 S3c-1 上,只跑一次)

```
$ date -u +%Y-%m-%dT%H:%M:%SZ
2026-10-02T18:56:51Z
$ python -X utf8 -m pytest -q
...
FAILED tests/test_redlight.py::TestCompletenessCoverage::test_c3a_lf_silent_narrowing_is_not_full_coverage
FAILED tests/test_redlight.py::TestCompletenessCoverage::test_c3b_a_session_without_completeness_facts_is_not_full_coverage
FAILED tests/test_redlight.py::TestCompletenessCoverage::test_c3b_a_malformed_completeness_fact_is_not_full_coverage
FAILED tests/test_redlight.py::TestCompletenessCoverage::test_c3c_an_exitfirst_run_is_not_full_coverage
FAILED tests/test_redlight.py::TestCompletenessCoverage::test_c3p_an_unknown_plugin_dist_means_not_full_coverage
FAILED tests/test_redlight.py::TestCompletenessCoverage::test_c3p_a_plugin_loaded_by_name_means_not_full_coverage
FAILED tests/test_redlight.py::TestCompletenessCoverage::test_c3p_an_extra_conftest_means_not_full_coverage
FAILED tests/test_status.py::TestSilentNarrowingChain::test_c3a_lf_narrowing_does_not_retire_an_unidentified_red
FAILED tests/test_status.py::TestSilentNarrowingChain::test_c3a_lf_narrowing_does_not_make_a_clean_file_green
FAILED tests/test_status.py::TestEarlyStopChain::test_c3c_exitfirst_does_not_orphan_a_known_red
FAILED tests/test_status.py::TestEarlyStopChain::test_c3c_pytest_exit_zero_partial_file_is_not_green
FAILED tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_an_unknown_dist_plugin_as_other
FAILED tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_a_plugin_loaded_by_name_as_other
FAILED tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_an_extra_conftest_as_other_and_the_root_conftest_as_root_conftest
FAILED tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_builtin_root_conftest_and_known_dist_as_not_other
15 failed, 1952 passed, 3 skipped, 3 xfailed in 151.15s (0:02:31)
```

(exit code 1。tool 輸出中段截斷約 16790 字元;摘要行與 short test summary 完整。)

**偏差**:`tests/test_status.py::TestLfFalseGreenChain::test_c3e_full_then_lf_does_not_produce_a_false_green` 通過(預期失敗)。依程序不修、不重跑,停手回報。

**原因**(裁決助手在隔離環境以 d122df4 的 conftest / redlight / status 重現):
- C3e-1 用同一個 conftest 模組連續驅動 R1、R2、R3,中間沒有重置模組狀態(`tests/conftest.py:137` 的 `_outcomes`、`:143` 的 `_run`,`pytest_sessionfinish` 不會清掉它們)。
- R1 的收集錯誤殘留,R2 的 session 因此判 D。
- R2 的 outcome(S_A)殘留到 R3,而 R3 的 selected 只有 S_B ⇒ outcome 身分不屬於 selected ⇒ R3 判 **INVALID**(`.claude/hooks/redlight.py:331-334`)⇒ 不退紅 ⇒ 測試因錯誤的理由通過。
- 每次執行都是全新狀態時,R3 判 A、該檔判 green(即 S5b-F1),測試會如預期失敗。
- 更正:VS 第一次回報時把 R3 寫成「判 D」,依據不完整(只考慮了收集錯誤殘留,沒有考慮 outcome 殘留)。裁決助手的重現結果是 R3 為 INVALID,本報告以此為準。
<!-- 逐字結束 -->

行號來源:同檔第 115–175 行

<!-- 逐字開始 -->
## 5. 第二次驗收(在 S3c-1b 上,只跑一次)

```
$ date -u +%Y-%m-%dT%H:%M:%SZ
2026-10-02T19:06:34Z
$ python -X utf8 -m pytest -q
```

exit code 1。**tool 輸出在結尾被截斷**:摘要行原文與 short test summary 的後半沒有顯示。以下是保留下來的部分原文:

```
........................................FFFFFFF......................... [ 76%]
...
..........FFF..F.F.FFFF................................................. [ 94%]
...
FAILED tests/test_redlight.py::TestCompletenessCoverage::test_c3a_lf_silent_narrowing_is_not_full_coverage
FAILED tests/test_redlight.py::TestCompletenessCoverage::test_c3b_a_session_without_completeness_facts_is_not_full_coverage
FAILED tests/test_redlight.py::TestCompletenessCoverage::test_c3b_a_malformed_completeness_fact_is_not_full_coverage
FAILED tests/test_redlight.py::TestCompletenessCoverage::test_c3c_an_exitfirst_run_is_not_full_coverage
FAILED tests/test_redlight.py::TestCompletenessCoverage::test_c3p_an_unknown_plugin_dist_means_not_full_coverage
FAILED tests/test_redlight.py::TestCompletenessCoverage::test_c3p_a_plugin_loaded_by_name_means_not_
```

(進度列上的 `F` 共 7 + 9 = 16 個。)**依裁決不重跑**,失敗集合與計數改由下列來源證明:

**來源 A —— pytest 自己寫的 `.pytest_cache/v/cache/lastfailed`(pytest 原始資料)**:

```
{
  "tests/test_gate.py::TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce": true,
  "tests/test_stage_defs_source.py::TestTheWorktreePathDerivesFromRoot::test_patching_root_moves_the_worktree_definition": true,
  "tests/test_redlight.py::TestCompletenessCoverage::test_c3a_lf_silent_narrowing_is_not_full_coverage": true,
  "tests/test_redlight.py::TestCompletenessCoverage::test_c3b_a_session_without_completeness_facts_is_not_full_coverage": true,
  "tests/test_redlight.py::TestCompletenessCoverage::test_c3b_a_malformed_completeness_fact_is_not_full_coverage": true,
  "tests/test_redlight.py::TestCompletenessCoverage::test_c3c_an_exitfirst_run_is_not_full_coverage": true,
  "tests/test_redlight.py::TestCompletenessCoverage::test_c3p_an_unknown_plugin_dist_means_not_full_coverage": true,
  "tests/test_redlight.py::TestCompletenessCoverage::test_c3p_a_plugin_loaded_by_name_means_not_full_coverage": true,
  "tests/test_redlight.py::TestCompletenessCoverage::test_c3p_an_extra_conftest_means_not_full_coverage": true,
  "tests/test_status.py::TestSilentNarrowingChain::test_c3a_lf_narrowing_does_not_retire_an_unidentified_red": true,
  "tests/test_status.py::TestSilentNarrowingChain::test_c3a_lf_narrowing_does_not_make_a_clean_file_green": true,
  "tests/test_status.py::TestEarlyStopChain::test_c3c_exitfirst_does_not_orphan_a_known_red": true,
  "tests/test_status.py::TestEarlyStopChain::test_c3c_pytest_exit_zero_partial_file_is_not_green": true,
  "tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_an_unknown_dist_plugin_as_other": true,
  "tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_a_plugin_loaded_by_name_as_other": true,
  "tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_an_extra_conftest_as_other_and_the_root_conftest_as_root_conftest": true,
  "tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_builtin_root_conftest_and_known_dist_as_not_other": true,
  "tests/test_status.py::TestLfFalseGreenChain::test_c3e_full_then_lf_does_not_produce_a_false_green": true
}
```

- 第 3–19 行恰好是預期的 16 支。
- 前兩筆是**身分已不存在的舊紀錄**:pytest 只在本次有收集、而且通過時才移除 lastfailed 項目(`_pytest/cacheprovider.py:348-350, 354-359`)。
  Grep 證明:`tests/test_stage_defs_source.py` 沒有 `TestTheWorktreePathDerivesFromRoot` 類別;`tests/test_gate.py:834` 的 `TestLegacyNoRedlightList` 類別還在,但其中已經沒有 `test_the_list_is_what_the_generator_would_produce` 方法。

**來源 B —— 帳本 `.dev/test-runs.jsonl` 本次新增的 46 行(第 2366–2411 行)**:
- 第 2396 行 `tests/test_redlight.py` red,`failed_tests` 7 項(上表 test_redlight 的 7 支);
- 第 2404 行 `tests/test_status.py` red,`failed_tests` 9 項(上表 test_status 的 9 支,含 C3e-1);
- 其餘 44 行全部 `"result": "green"`。

**來源 C —— `status.py`(受測系統的 producer 紀錄,不是 pytest 原文)**:`最近一次 run:B(exit 1;collected 1973 / deselected 0 / passed 1951 / failed 16 / skipped 3)`。
collected 1973 = 1951 + 16 + 3 + 3(xfail 記為 other)。
<!-- 逐字結束 -->

行號來源:同檔第 205–224 行

<!-- 逐字開始 -->
## 7. 帳本只追加證據鏈

| 點 | test-runs | test-sessions | 值的來源 |
|---|---|---|---|
| H0(第一次驗收前) | 624488 bytes / 2319 行 / `73737b7ddc353b2049d3bf8a61e831c9e2ab57e44b634ba91349447d1d0a8a93` | 1873333 bytes / 12 行 / `42bdc38e99695014d384f501cbf8517ca6a72d5bde690f090fcfc190d6c27e35` | VS 當時記錄(S3c-1 第 0 步);與裁決助手獨立量測相同 |
| H1(第一次驗收後) | 637099 bytes / 2365 行 / `95cee485cf98c1e9fb45e4a77641a59d9798756f268f10fd591fd79719aa2ad3` | 2338347 bytes / 13 行 / `5dbe56fea2e22747058b826269ce8023974dc45b561bcb82d94a42ccf73c9863` | VS 量測(3c-1b 第 0 步);與裁決助手獨立量測相同 |
| H2(第二次驗收後) | 649789 bytes / 2411 行 / `36bf61df9c2a4b68d109f419d2020184e101edbd8de8131723c085b86f8f2544` | 2803361 bytes / 14 行 / `0ef187e02160759dba4912650d7baa0d3642a3b1902e91add71a20f97e477c45` | VS 量測(3c-1b 第 3 步) |

prefix 驗證(`head -c <前一點的 bytes>` 寫到 session scratch,再取 sha256;scratch 路徑以 `<session scratch>` 代替):

| 段 | 檔 | 前段 bytes | 前段 sha256 | 等於 |
|---|---|---|---|---|
| H0 → H1 | test-runs | 624488 | `73737b7ddc353b2049d3bf8a61e831c9e2ab57e44b634ba91349447d1d0a8a93` | H0r ✓ |
| H0 → H1 | test-sessions | 1873333 | `42bdc38e99695014d384f501cbf8517ca6a72d5bde690f090fcfc190d6c27e35` | H0s ✓ |
| H1 → H2 | test-runs | 637099 | `95cee485cf98c1e9fb45e4a77641a59d9798756f268f10fd591fd79719aa2ad3` | H1r ✓ |
| H1 → H2 | test-sessions | 2338347 | `5dbe56fea2e22747058b826269ce8023974dc45b561bcb82d94a42ccf73c9863` | H1s ✓ |

- 每段 test-runs 增加 46 行(= 測試檔數),test-sessions 增加 1 行。
- H0 → H1 的驗證是在 3c-1b 第 0 步做的(在第二次驗收之前)。
- 兩次驗收之後,`git status --porcelain` 都沒有輸出。
<!-- 逐字結束 -->

### F.2 Station 4c 修正證據 —— 驗收、帳本 H2 → H3、真實 session、status、四項完成判定

出處:`a88b7f9664189f9b3f3124aa39eb3a95eaca51b1:docs/audits/2026-10-02-m1a-station4c-fix.md`;該檔在 S4c-2 的 blob ID:`5b95de9fe03d6de863a7e2caa21430e3f8874916`。

行號來源:同檔第 102–200 行

<!-- 逐字開始 -->
## 5. 驗收(在 S4c-1 上,只跑一次)

```
$ date -u +%Y-%m-%dT%H:%M:%SZ
2026-10-02T20:55:13Z
$ python -X utf8 -m pytest -q
...
=========================== short test summary info ===========================
SKIPPED [1] tests\test_gate.py:451: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:459: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:473: 此環境無法建立 symlink
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/srv/x] - …
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/data/x] - …
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/backup/x] - …
1967 passed, 3 skipped, 3 xfailed in 150.21s (0:02:30)
```

(XFAIL 三行的說明文字以 `…` 截斷 —— 本區塊不是逐字全文;SKIPPED 與摘要行逐字。exit code 0;輸出沒有任何 FAILED / ERROR 行;tool 輸出沒有截斷。)

失敗清單:無。3c 的 16 支、5 支 regression-lock、六支授權測試、其他全部既有測試都通過(1967 = 1951 + 16)。

## 6. 帳本 H2 → H3 只追加

| 點 | test-runs | test-sessions |
|---|---|---|
| H2(驗收前) | 649789 bytes / 2411 行 / `36bf61df9c2a4b68d109f419d2020184e101edbd8de8131723c085b86f8f2544` | 2803361 bytes / 14 行 / `0ef187e02160759dba4912650d7baa0d3642a3b1902e91add71a20f97e477c45` |
| H3(驗收後) | 661092 bytes / 2457 行 / `352e7d2653301e11d16494c100d67231e47efcabe2a7a047a297402046972172` | 3494564 bytes / 15 行 / `b48ee090beb214f264476c2efc827b6d244cb6b70cf0d669adffd6d3ce871870` |

```
$ head -c 649789 .dev/test-runs.jsonl > <session scratch>/r.bin
$ sha256sum <session scratch>/r.bin
36bf61df9c2a4b68d109f419d2020184e101edbd8de8131723c085b86f8f2544 *<session scratch>/r.bin
$ head -c 2803361 .dev/test-sessions.jsonl > <session scratch>/s.bin
$ sha256sum <session scratch>/s.bin
0ef187e02160759dba4912650d7baa0d3642a3b1902e91add71a20f97e477c45 *<session scratch>/s.bin
```

(scratch 絕對路徑以 `<session scratch>` 代替 —— 這四行經遮罩,不是逐字原文。)
⇒ 兩本前段都等於 H2;test-runs +46 行(= 測試檔數)、test-sessions +1 行。跑完 `git status --porcelain` 無輸出。

## 7. 真實 session(`.dev/test-sessions.jsonl` 第 15 行)的 completeness

該行約 691 KB,以 Grep `-o` 取片段(不是整行 Read):

```
15:"options": {"lf": false, "last_failed_no_failures": "all", "stepwise": false, "stepwise_skip": false, "maxfail": null, "collectonly": false, "setuponly": false, "setupplan": false}
15:"cacheprovider_blocked": false
15:"shouldstop": false
15:"shouldfail": false
```

- `pre_narrowing`:46 個檔(Grep `"tests/[^":]+\.py": \[` 命中 46 個,全部在第 15 行)。
- `plugins`:43 項,builtin 41、known_dist 1、root_conftest 1;全帳本 Grep `"kind": "other"`:0 筆。

| kind | name |
|---|---|
| builtin | `2082416878800`(數字名稱)、pytestconfig、mark、main、runner、fixtures、helpconfig、python、terminal、debugging、unittest、capture、skipping、legacypath、tmpdir、monkeypatch、recwarn、pastebin、assertion、junitxml、doctest、cacheprovider、setuponly、setupplan、stepwise、unraisableexception、threadexception、warnings、logging、reports、faulthandler、subtests、capturemanager、session、lfplugin、nfplugin、legacypath-tmpdir、terminalreporter、terminalprogress、logging-plugin、funcmanage |
| known_dist | anyio |
| root_conftest | tests/conftest.py |

## 8. 絕對路徑檢查與裁決 1(三類欄位)

- Grep `[A-Za-z]:(\\\\|/)|Users`:命中第 1、6、11–14、15 行;第 1、6、11–14 行每行 2 組、第 15 行 3 組,每組 53 個片段。
  片段全部位於測試身分的 parametrize ID(例:`…test_no_secrets_are_referenced[C://projects//agent-gates//.github//workflo…`、`…[rm C://Users//fake//thing.py-…`)。
  第 15 行多出的一組位於 `completeness.pre_narrowing`(由組數推得;plugins 片段已確認不含路徑)。
- 全帳本 Grep 本機使用者名稱:0 筆。
- 裁決助手獨立核對:類似絕對路徑的字串只出現在 collected、outcomes 的鍵、completeness.pre_narrowing 三處,共 29 個身分;pre_narrowing 中的這些身分全部也在 collected 中;plugins 與 invocation 不含;本次 invocation.args 為相對的 `tests`。
- **裁決 1**:(1) producer 自身產生的 path-valued metadata(如 `completeness.plugins[].name`)不得有絕對路徑 —— 成立;(2) pytest 提供、作為 identity 逐字保存的 nodeid 不因本條改寫;(3) invocation.args 依〈十九〉的正規化 —— 不屬本條。⇒ **(c) 成立**。(2) 類原始事實本身帶本機敏感路徑的問題列入 M1-a 結案後追蹤票。

## 9. status.py(驗收後)

`python .claude/portable/status.py --root .` 的 Evidence 與 Derived 兩段(逐字):

```
=== Evidence ===
test-runs: 本票 red 0 / green 46 / run 事實未知 0 / orphaned 0 / schema 不合格 run 0;最後一筆 tests/test_verify_gates.py=green @ 2026-10-02T20:57:42.829998+00:00;最近一次 run:A(exit 0;collected 1973 / deselected 0 / passed 1967 / failed 0 / skipped 3)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl)
intercepts (當月): 2 筆  (source: .dev/intercepts-2026-10.jsonl)
intercepts (最新存在月): 2026-10 2 筆;末筆 R7@2026-10-02T18:03:07.370596+00:00  (source: .dev/intercepts-2026-10.jsonl)
exemptions: 總 281 筆;granted 240 筆;blocked 1 筆;未記錄(無此欄)40 筆;最後一筆 2026-09-24T08:17:49.073745+00:00  (source: .dev/gate-exemptions.jsonl)
provenance: 未記錄(上游無此檔屬正常)  (source: .dev/provenance.jsonl)
report: 2026-10-02T174245Z-ticket145-station5b-0.md;HEAD 2026-10-02T16:55:06-04:00;回報後 6 筆  (source: .dev/reports/)

=== Derived ===
src write allowed in implement: yes  (source: gate.stage_allows_src_write() <- .agents/pipeline-stages.yaml)
tests red under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests green under ticket 145: tests/test_adr_numbering.py / tests/test_adr_numbers_resolve_upstream.py / tests/test_apply_patches.py / tests/test_bash_write.py / tests/test_bootstrap.py / tests/test_canon_section.py / tests/test_ci_workflow.py / tests/test_cjk_git_paths.py / tests/test_claude_md.py / tests/test_declared_in_is_an_identity.py / tests/test_dependency_ceiling.py / tests/test_edit_result.py / tests/test_evidence_isolation.py / tests/test_friction_heading.py / tests/test_g1_guard.py / tests/test_g1_verify.py / tests/test_gate.py / tests/test_gate_boundaries.py / tests/test_gitlink_downstream_cycle.py / tests/test_install.py / tests/test_intercepts.py / tests/test_known_items_regression.py / tests/test_leak_scan.py / tests/test_ledger_verify.py / tests/test_line_ending_parity.py / tests/test_manifest.py / tests/test_mcp_server.py / tests/test_non_source_list_parity.py / tests/test_portable_output_encoding.py / tests/test_r5_mounts.py / tests/test_redlight.py / tests/test_research_stage.py / tests/test_scanner.py / tests/test_shadow.py / tests/test_shadow_review.py / tests/test_source_hygiene.py / tests/test_stage_defs_source.py / tests/test_stage_naming.py / tests/test_status.py / tests/test_sync.py / tests/test_ticket_dirs_are_md_only.py / tests/test_ticket_lookup.py / tests/test_ticket_path_parity.py / tests/test_upstream_manifest.py / tests/test_user_layer.py / tests/test_verify_gates.py  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests green (run 事實未知) under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests orphaned under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
rules defined: R1 R2 R3 R4 R5 R6 R7 R8 R9  (source: gate.rule_codes())
```

## 10. 四項完成判定

| 項 | 判定 | 依據 |
|---|---|---|
| (a) 固定全套 exit 0、failed 0 | **成立** | 第 5 節摘要行原文 |
| (b) 3c 的 16 支全部轉綠 | **成立** | 失敗集合為空;status red 0 |
| (c) completeness 合格、plugins 無 other、無絕對路徑 | **成立** | 第 7、8 節;依裁決 1 的欄位邊界 |
| (d) 帳本 H2 → H3 只追加 | **成立** | 第 6 節前段雜湊相符 |
<!-- 逐字結束 -->

---

## G. 必答問題(G1–G12)

每題回答「成立 / 不成立 / 無法判定」(或題目要求的具體推演結果),並附 `<TARGET>:<路徑>:<行號>` 證據。
「無問題」也要附證據;「不成立」須給出具體輸入與錯誤輸出(紙上推演,**不得執行 pytest**)。
`<TARGET>` 一律代入 `02a5e28adf5aee11a43d5a1063504f01beb1d67f`。

**G1. S5b-F1(`--lf` 收集期靜默縮小)是否已修好?**
沿 pytest 9.1.1 的實際 hook 順序逐步推演:全套 → `--lf` 的三步情境(〈二十一〉21.2)在 TARGET 上會得到什麼?

**G2. 〈二十三〉7 (i)–(vii) 每一條在 `file_coverage` 中由哪幾行強制?**
是否有任何一條可被繞過而仍得 `"true"`?

**G3. 執行完整性**
`pytest.exit(returncode=0)`、`--setup-only`、只有 setup 沒有 call、xfail / xpass 的辨識;籠統的 `other` 是否仍可能取得 completeness?

**G4. plugin 邊界**
分類是否確實由 `list_name_plugin()` 與 `list_plugin_distinfo()` 的原始事實產生?
known_dist 是否以「物件出現在 distinfo 配對」判定,而非只比名稱(例如以 `-p` 載入一個名叫 `anyio` 的模組)?
builtin 的判定能否被一個自訂模組冒充(例如模組名以 `_pytest` 開頭)?
路徑型名稱是否只記 root 相對路徑?

**G5. pre_narrowing 多層 collector 累積(Jeff 裁決指定必答;〈二十五〉裁決 2)**
是否會因重複、巢狀 class、parametrize、unittest TestCase、hook 順序而漏記或錯記?
`--lf` 的 File 層縮小是否確實發生在本 snapshot 之後?是否形成新的 false-positive coverage 路徑?

**G6. producer 失敗安全**
新增的事實收集出錯時是否不讓 pytest 失敗、completeness 缺失 ⇒ `"unknown"`?既有 8 欄紀錄是否不受影響?
S5b-F5 指出的「try 之外」區段現況如何?

**G7. 提前停止**
`-x` / `--maxfail` / `--sw` / KeyboardInterrupt 下,是否都沒有退紅、orphan、green 權?

**G8. 向下相容**
沒有 completeness 的舊 session ⇒ `"unknown"`?只有 8 欄 ⇒ 不退紅?
舊版 redlight 配新 status、新 conftest 配舊 redlight,是否不拋例外、只會多紅?

**G9. 測試沒有被放寬**
以 `git diff 49bcde20adc276632fa5bab456e8c7a80839fc0b..02a5e28adf5aee11a43d5a1063504f01beb1d67f -- tests/test_redlight.py tests/test_status.py`(〈E.3〉)逐一核對 ——
3c 新增的 21 支未改;授權補件只動六支既有測試的 fake / fixture,assertion、docstring、identity 不變。

**G10. 測試 driver 是否忠實模擬 pytest?**
是否有任何新測試可能「為了錯的理由通過」(參照 3c 的 C3e-1 狀態殘留事件,〈F.1〉第一次驗收;
例如模組狀態跨模擬 session 殘留、fake wrapper 協定與 pluggy 不符)?

**G11. 隱私與欄位邊界**
producer 自行產生的 path-valued metadata 是否沒有絕對路徑;測試身分是否逐字保存;
invocation.args 是否依〈十九〉正規化(依〈二十五〉裁決 1 的三類)。

**G12. 既往修正未退步**
Station 5 的 F1–F4、Station 5b 審查已確認的項目,在 TARGET 上是否仍成立?

---

## H. 已知例外與未證明事項(照實列出,不評論)

### H.1 Station 4c 報告的「尚未證明」(逐字)

行號來源:a88b7f9664189f9b3f3124aa39eb3a95eaca51b1:docs/audits/2026-10-02-m1a-station4c-fix.md 第 204–208 行

<!-- 逐字開始 -->
1. plugin completeness 以 producer 在 sessionfinish 時觀察到的已註冊 plugin 集合為依據;**某 plugin 在 session 中途自行 unregister、且已改過 collection** 這類非標準生命週期未證明。標準的 `-p`、`PYTEST_PLUGINS`、conftest、entry-point dist 已由〈二十三〉合約與 3c 測試涵蓋。
2. 未被 Git 追蹤或被 ignore 的 conftest 不在第 0 步盤點內;若真實執行載入它,會被分類為 other ⇒ 驗收 fail-closed。
3. `_pre_narrowing` 是模組層狀態,同一程序內多次 `pytest.main()` 會累積(集合只會多不會少 ⇒ 與 collected 不等 ⇒ false),屬 fail-closed 方向,未另驗。
4. 多層 collector 累積的正確性(裁決 2 的 Station 5c 必答題:重複、巢狀 class、parametrize、hook 順序;`--lf` 的 File 層縮小是否確實發生在本 snapshot 之後)只由真實固定全套佐證,未逐案證明。
5. CLEAN / REAL 層未證明。
<!-- 逐字結束 -->

### H.2 已裁定的例外與債務

| 項 | 處置 | 是否擋 Station 5c |
|---|---|---|
| S5b-F2–F6 | **非阻擋**;已登記到 M1-a 結案後的追蹤票(〈二十一〉21.3 第 4 點) | 否 |
| 測試身分的 parametrize ID 帶本機 repo 路徑(例:`tests/test_ci_workflow.py` 的參數) | **已登記追蹤票**(〈二十五〉裁決 1:屬 privacy / provenance 問題,不屬 (c)) | 否 |
| `.dev/test-sessions.jsonl` 增長(每次全套約增長 450–690 KB,全檔讀取) | **債務**(〈十七〉裁決 8);M1-a 結案時另開票 | 否(非阻擋) |
| Station 3b 刀③ 的程序違規(`git diff --check` 有輸出時仍 commit) | **已知例外**;不改寫歷史 | 否 |
| 本包〈E〉內嵌 diff 的空白 context 行 | `git diff --check` 會報 trailing whitespace;是 diff 原樣,不是編輯錯誤 | 否 |

審查者若認為上列任一項應改為阻擋,須以「阻擋」發現提出並附證據;否則不重複列為發現。
