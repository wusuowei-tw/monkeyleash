# M1-a Station 5b 獨立審查包(票 145)

**審查對象(TARGET)**:`851cbd75b359a6b2a34452265e8a70992fa56996`

本包只是材料,不含任何審查結論。所有逐字段落皆以 `<!-- 逐字開始 -->` / `<!-- 逐字結束 -->` 標出邊界,
邊界之間的文字與標示的出處逐位元組相同(換行一律 LF)。

---

## A. 身分與規則

### A.1 審查對象

- **實作審查對象**:`851cbd75b359a6b2a34452265e8a70992fa56996`(以下記作 `<TARGET>`;凡出現 `<TARGET>` 之處一律代入這一個完整 SHA)。
- 本包所在的 commit(S5b-0)是 `<TARGET>` **之後**的一個 docs-only commit,只改兩個檔:
  `docs/audits/2026-10-02-m1a-station5b-review-package.md`(本包)與
  `docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md`(票 145 的狀態同步)。
  審查者可自行核對:

  ```
  git diff --name-only 851cbd75b359a6b2a34452265e8a70992fa56996..<S5b-0 SHA>
  ```

  應只列出上面兩個路徑。S5b-0 的 SHA 不寫在本包內(本包是 S5b-0 的一部分,寫不進自己的 SHA),由裁決者交付審查時另附。
- S5b-0 **不是**審查對象;審查結論只針對 `<TARGET>` 的程式碼與測試。

### A.2 查詢一律綁定 TARGET

審查者的所有 Git 查詢都以完整 SHA 為錨點,不以分支名或工作樹當下狀態為錨點。範例:

```
git diff origin/master..851cbd75b359a6b2a34452265e8a70992fa56996 -- <路徑>
git diff af839c6..851cbd75b359a6b2a34452265e8a70992fa56996 -- <路徑>
git show 851cbd75b359a6b2a34452265e8a70992fa56996:<路徑>
```

- `origin/master` = 本票所有 commit 之前的上游狀態(〈D〉列出兩者之間的 16 個 commit)。
- `af839c6` = Station 3b 補件紅燈證據入票(Station 4b 修正之前的最後一個 commit)。

### A.3 審查者規則

1. **唯讀**:不改任何檔案、不 commit、不推、不改 `.dev/pipeline.json`。
2. **不跑 pytest**(含 `--collect-only`、`--version`)。帳本(`.dev/test-runs.jsonl`、`.dev/test-sessions.jsonl`)會被任何 pytest 執行追加,審查不得污染證據。
3. 審查報告**只寫到** `.scratch/m1a-s5b/review-report.md`,不寫其他位置。
4. **結論只能是 `PASS` 或 `FAIL`**,不得有第三種。
5. 每一項發現須標**「阻擋」或「非阻擋」**,並附 `<TARGET>:<路徑>:<行號>` 形式的證據
   (例:`851cbd75b359a6b2a34452265e8a70992fa56996:.claude/hooks/redlight.py:263`)。
   沒有行號證據的發現不計入判定。
6. 〈G〉的 G1–G11 每一題都必須回答;不能回答的,寫明「無法判定」與原因,不得略過。

### A.4 審查範圍內的檔案

| 路徑 | 角色 |
|---|---|
| `.claude/hooks/redlight.py` | run 事實的寫入 / 讀取 / 判定(`record_session`、`load_runs`、`validate_session`、`run_state`、`file_coverage`) |
| `.claude/portable/status.py` | 依 run 事實判定紅綠(`ticket_test_state`、`_apply_run`)與顯示(Evidence / Derived) |
| `tests/conftest.py` | producer(pytest hooks → `record_session`) |
| `tests/test_redlight.py` | Station 3 / 3b / 3b 補件的 producer 側紅燈 |
| `tests/test_status.py` | Station 3 / 3b / 3b 補件的 status 側與串接紅燈;Station 4b 的 fixture 補件 |

---

## B. 合約原文(票 145,逐字)

### B.1 〈十三〉ODC-1(修訂後全文)

行號來源:851cbd75b359a6b2a34452265e8a70992fa56996:docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md 第 540–545 行

<!-- 逐字開始 -->
ODC-1（修訂後全文，取代〈十一〉同條的第 2、3 項）
一個 run 只有在同時滿足下列三項時，才有資格使某 test file 內既有的 red 變為 green：
1. 該 file 的測試集合全部被選到（沒有任何 deselected）；
2. 已知先前為 red 的 test identity，本次確實執行並通過；若歷史 red 無法知道是哪一條 test，則該 file 內所有 applicable tests 都必須實際執行並通過；
3. 該 file 本次沒有任何 failure。
其他 file 的 failure 不影響本 file 的退紅資格；與既有 red 無關的 skip 亦不影響。
<!-- 逐字結束 -->

### B.2 〈十七〉Station 5 獨立審查(FAIL)與 Station 3b 裁決(全段)

行號來源:851cbd75b359a6b2a34452265e8a70992fa56996:docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md 第 778–808 行

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

(〈十七〉裁決 7 原文中的「HEAD」是當時的裁決文字,不是本包的查詢錨點;本包的錨點一律是 `<TARGET>`。)

### B.3 〈十八之一〉B10 推導(18-1.1)

行號來源:851cbd75b359a6b2a34452265e8a70992fa56996:docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md 第 881–899 行

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

### B.4 〈十九〉Station 4b 修正(全段)

行號來源:851cbd75b359a6b2a34452265e8a70992fa56996:docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md 第 942–1049 行

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

---

## C. 前一次審查的 FAIL 原文(F1–F4)

出處:`851cbd75b359a6b2a34452265e8a70992fa56996:docs/audits/2026-10-02-m1a-station5-independent-review-fail.md` 第 11–197 行;
該檔在 `<TARGET>` 的 blob ID:`ae885228549f9100618d8f97effecf2bca4e82a6`。

(前次審查報告的編號是「1.」–「4.」;票 145〈十七〉把它們記為 F1–F4,對應為 1 → F1、2 → F2、3 → F3、4 → F4。)

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

---

## D. 本票 commit 清單

產生指令:`git log --oneline origin/master..851cbd75b359a6b2a34452265e8a70992fa56996`(完整輸出,16 行)

```
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

---

## E. 完整 diff

兩份 diff 皆為完整輸出、未截斷。diff 內空白的 context 行(單一空格)是 `git diff` 的原樣輸出,
`git diff --check` 會把它們報成 trailing whitespace —— 那是本段的已知形狀,不是編輯錯誤。

### E.1 `git diff origin/master..851cbd75b359a6b2a34452265e8a70992fa56996 -- .claude/hooks/redlight.py .claude/portable/status.py tests/conftest.py tests/test_redlight.py tests/test_status.py`

本票全部程式碼與測試改動(上游 → TARGET)。

```diff
diff --git a/.claude/hooks/redlight.py b/.claude/hooks/redlight.py
index 01eec85..0f1633b 100644
--- a/.claude/hooks/redlight.py
+++ b/.claude/hooks/redlight.py
@@ -141,3 +141,289 @@ def record_run(test_file, passed, failed_tests):
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
+                   collected=(), deselected=(), outcomes=None, invocation=None):
+    """追加一筆 run 事實到 `<root>` 的 session 帳本。回傳寫入的內容。
+
+    - `collected`:本次收集到的身分(含被 deselect 的;收集錯誤以
+      `<檔>::<collection error>` 標記)
+    - `deselected`:被排除的身分;`selected` = collected − deselected
+    - `outcomes`:`{身分: "passed" | "failed" | "skipped" | "other"}`,只含 selected
+    - `exit_code`:runner 的原始退出碼;取不到為 None
+    - `invocation`:producer 觀察到的呼叫事實 `{"args", "args_source", "invocation_dir",
+      "pyargs"}`(票 145〈十七〉裁決 1 的判定依據);None ⇒ 涵蓋範圍未知
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
+OUTCOME_VALUES = ("passed", "failed", "skipped", "other")
+
+
+def validate_session(run):
+    """一筆 run 事實的 schema 問題清單。**空 list = 合格。**(票 145〈十七〉裁決 3)
+
+    合格的條件(缺一即不合格,**不得**以「缺欄 ⇒ 空集合」或「錯型別照常迭代」處理):
+      - `run_id`、`time` 為非空字串;`ticket_id` 欄位存在(字串或 null)
+      - `exit_code` 欄位存在,為 int(非 bool)或 null
+      - `collected`、`deselected` 為字串 list;`deselected ⊆ collected`
+      - `outcomes` 為 `{字串: passed | failed | skipped | other}`;其鍵 ⊆ selected
+      - `invocation` 若存在且非 null:為 dict,`args` 為 list(元素為字串或 null)或 null
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
+
+    **沒有為固定指令另寫分支**:pytest 未給位置參數時以 testpaths 補上
+    `config.args == ["tests"]`,與「位置參數為上層目錄 tests」走同一條規則。
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
+        return "true"
+    if narrowed:
+        return "false"
+    return "unknown"
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
index 7c163e7..7f6fe5e 100644
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
@@ -149,6 +159,45 @@ def pytest_collectreport(report):
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
+    xfail = getattr(report, "wasxfail", None) is not None
+    when = getattr(report, "when", None)
+    if getattr(report, "skipped", False):
+        return "other" if xfail else "skipped"
+    if when == "call" and getattr(report, "passed", False):
+        return "other" if xfail else "passed"
+    return None
 
 
 def pytest_runtest_logreport(report):
@@ -163,6 +212,11 @@ def pytest_runtest_logreport(report):
     rec = _outcomes.setdefault(f, {"failed": []})
     if report.failed:
         rec["failed"].append(report.nodeid.split("::", 1)[-1])
+    # 票 145:逐身分的結果。`failed` 一旦記下就不被後來的 report 蓋掉
+    # (teardown 失敗之前的 call 可能是 passed)。
+    got = _run_outcome(report)
+    if got is not None and _run["outcomes"].get(_nodeid(report)) != "failed":
+        _run["outcomes"][_nodeid(report)] = got
 
 
 def pytest_sessionfinish(session, exitstatus):
@@ -170,3 +224,44 @@ def pytest_sessionfinish(session, exitstatus):
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
+    if "invocation" in _inspect.signature(_redlight.record_session).parameters:
+        kwargs["invocation"] = _invocation_of(session)
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
diff --git a/tests/test_redlight.py b/tests/test_redlight.py
index 63a68a8..f1b010f 100644
--- a/tests/test_redlight.py
+++ b/tests/test_redlight.py
@@ -226,3 +226,407 @@ class TestTheRecorderCannotKillTheRunner:
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
+        got = self._coverage_after(tmp_path, monkeypatch, ["tests/test_x.py"], [X_A, X_B])
+        assert got == "true", got
+
+    def test_b1d_a_parent_directory_argument_is_full_coverage(self, tmp_path, monkeypatch):
+        """B1d(F3 producer)。分類:interface-red(`redlight.file_coverage` 不存在)。
+
+        位置參數 `tests`(上層目錄)、無 deselected ⇒ 整檔涵蓋。
+        """
+        got = self._coverage_after(tmp_path, monkeypatch, ["tests"], [X_A, X_B])
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
+        _drive_with_session(c, session, selected=[X_A, X_B],
+                            outcomes={X_A: "passed", X_B: "passed"}, exitstatus=0)
+        runs = redlight.load_runs(str(tmp_path))
+        assert len(runs) == 1, runs
+        got = redlight.file_coverage(runs[0], "tests/test_x.py")
+        assert got == "true", got
diff --git a/tests/test_status.py b/tests/test_status.py
index b2ae5d9..196b304 100644
--- a/tests/test_status.py
+++ b/tests/test_status.py
@@ -563,6 +563,19 @@ class TestTestsUnderTicketUsesTheLatestRecordPerFile:
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
+            invocation={u"args": [u"tests"]})
 
         out = render(root)
         red = _value_of(out, u"tests red under ticket 99")
@@ -1119,3 +1132,624 @@ class TestReportLineSaysHowStaleTheReportIs:
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
+                                invocation={u"args": [u"tests"]})
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
+        _chain_drive(c, root, ["tests"], selected=[CHAIN_X, CHAIN_Y],
+                     outcomes={CHAIN_X: "passed", CHAIN_Y: "passed"}, exitstatus=0)
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
```

### E.2 `git diff af839c6..851cbd75b359a6b2a34452265e8a70992fa56996 -- .claude/hooks/redlight.py .claude/portable/status.py tests/conftest.py tests/test_status.py`

Station 4b 的修正(3b 補件紅燈證據入票之後 → TARGET)。`tests/test_redlight.py` 不在指令內:同一區間它沒有改動(見 G10(a))。

```diff
diff --git a/.claude/hooks/redlight.py b/.claude/hooks/redlight.py
index 1e2f0ae..0f1633b 100644
--- a/.claude/hooks/redlight.py
+++ b/.claude/hooks/redlight.py
@@ -178,8 +178,47 @@ def _ticket_of(root):
         return None
 
 
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
 def record_session(root, run_id=None, time=None, ticket_id=None, exit_code=None,
-                   collected=(), deselected=(), outcomes=None):
+                   collected=(), deselected=(), outcomes=None, invocation=None):
     """追加一筆 run 事實到 `<root>` 的 session 帳本。回傳寫入的內容。
 
     - `collected`:本次收集到的身分(含被 deselect 的;收集錯誤以
@@ -187,6 +226,8 @@ def record_session(root, run_id=None, time=None, ticket_id=None, exit_code=None,
     - `deselected`:被排除的身分;`selected` = collected − deselected
     - `outcomes`:`{身分: "passed" | "failed" | "skipped" | "other"}`,只含 selected
     - `exit_code`:runner 的原始退出碼;取不到為 None
+    - `invocation`:producer 觀察到的呼叫事實 `{"args", "args_source", "invocation_dir",
+      "pyargs"}`(票 145〈十七〉裁決 1 的判定依據);None ⇒ 涵蓋範圍未知
 
     `run_id` / `time` / `ticket_id` 為 None 時自取(測試可指定以求決定性)。
     寫入失敗不拋例外 —— 紀錄器不得弄死執行器(`TestTheRecorderCannotKillTheRunner`)。
@@ -201,6 +242,7 @@ def record_session(root, run_id=None, time=None, ticket_id=None, exit_code=None,
         "collected": [str(n).replace("\\", "/") for n in (collected or ())],
         "deselected": [str(n).replace("\\", "/") for n in (deselected or ())],
         "outcomes": {str(k).replace("\\", "/"): v for k, v in (outcomes or {}).items()},
+        "invocation": _normalize_invocation(root, invocation),
     }
     path = session_log(root)
     try:
@@ -238,11 +280,76 @@ def load_runs(root):
     return out
 
 
+OUTCOME_VALUES = ("passed", "failed", "skipped", "other")
+
+
+def validate_session(run):
+    """一筆 run 事實的 schema 問題清單。**空 list = 合格。**(票 145〈十七〉裁決 3)
+
+    合格的條件(缺一即不合格,**不得**以「缺欄 ⇒ 空集合」或「錯型別照常迭代」處理):
+      - `run_id`、`time` 為非空字串;`ticket_id` 欄位存在(字串或 null)
+      - `exit_code` 欄位存在,為 int(非 bool)或 null
+      - `collected`、`deselected` 為字串 list;`deselected ⊆ collected`
+      - `outcomes` 為 `{字串: passed | failed | skipped | other}`;其鍵 ⊆ selected
+      - `invocation` 若存在且非 null:為 dict,`args` 為 list(元素為字串或 null)或 null
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
+    return problems
+
+
 def run_state(run):
     """一個 run 事實的狀態 `"A"`–`"F"`(票 145〈三〉A)。**依序判定,先命中者為準。**
 
     | 條件 | 狀態 |
     |---|---|
+    | schema 不合格(`validate_session()` 非空) | INVALID —— 不是 A–F 任何一個 |
     | exit code 不在 {0, 1, 5}(中斷 / 內部錯誤 / 用法錯誤 / 取不到),或有收集錯誤 | D |
     | 任一身分 failed | B |
     | 0 collected | C |
@@ -252,6 +359,8 @@ def run_state(run):
     **不只看 exit code**:全部 deselected 時 pytest 回 5,但有收集到 ⇒ F,不是 C。
     E(根本沒跑)沒有 run 事實可以輸入,不在本函式值域內。
     """
+    if validate_session(run):
+        return "INVALID"
     ec = run.get("exit_code")
     collected = run.get("collected") or []
     outcomes = run.get("outcomes") or {}
@@ -265,3 +374,56 @@ def run_state(run):
     if "passed" not in values:
         return "F"
     return "A"
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
+
+    **沒有為固定指令另寫分支**:pytest 未給位置參數時以 testpaths 補上
+    `config.args == ["tests"]`,與「位置參數為上層目錄 tests」走同一條規則。
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
+        return "true"
+    if narrowed:
+        return "false"
+    return "unknown"
diff --git a/.claude/portable/status.py b/.claude/portable/status.py
index fd83f73..55e7fcc 100644
--- a/.claude/portable/status.py
+++ b/.claude/portable/status.py
@@ -403,25 +403,43 @@ def _red_identities_of_row(rec):
     return {u"%s::%s" % (f, n) for n in names}
 
 
-def _apply_run(run, red, orphan, green_now):
-    """一個 run 事實對每個檔的影響(就地更新三個 dict)。
+_RL_FUNCS = ("validate_session", "run_state", "file_coverage")
+
+
+def _rl_ready(rl):
+    """這份 redlight 有沒有判定所需的三個函式(舊版下游沒有 ⇒ 一律當涵蓋未知)。"""
+    return rl is not None and all(hasattr(rl, n) for n in _RL_FUNCS)
 
-    退紅(〈十三〉修訂後 ODC-1,file-scoped)—— 三項同時成立才退:
-      1. 該檔的測試集合全部被選到(該檔沒有任何 deselected);
-      2. 已知的紅身分本次實際執行且 passed;身分不明時,該檔全部 collected 身分都要 passed;
-      3. 該檔本次沒有任何 failure。
-    另加 I3:exit code 不在 {0, 1}(中斷、內部錯誤、用法錯誤、取不到)的 run 沒有退紅權。
 
-    孤兒(ODC-2):全選的 run 收集不到某個已知紅身分 ⇒ 移到 orphan,**不退紅**;
-    之後若同名身分再被收集到,移回紅,照常判定。改名不視為延續。
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
     """
-    collected = [str(n) for n in (run.get("collected") or [])]
-    deselected = set(str(n) for n in (run.get("deselected") or []))
-    outcomes = run.get("outcomes") or {}
-    exit_ok = run.get("exit_code") in (0, 1)
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
     by_file = {}
     for n in collected:
-        by_file.setdefault(_identity_file(n), []).append(n)
+        by_file.setdefault(_identity_file(n), []).append(str(n))
     for f, idents in by_file.items():
         errored = any(n.endswith(u"::<collection error>") for n in idents)
         selected = [n for n in idents if n not in deselected]
@@ -435,27 +453,29 @@ def _apply_run(run, red, orphan, green_now):
                 mine.add(_whole(f))
             green_now[f] = False
             continue
-        if not any(n in deselected for n in idents):
-            present = set(idents)
-            back = set(n for n in orphan.get(f, ()) if n in present)
-            if back:
-                red.setdefault(f, set()).update(back)
-                orphan[f] -= back
-            gone = set(n for n in red.get(f, ())
-                       if not n.endswith(u"::" + WHOLE_FILE) and n not in present)
-            if gone:
-                red[f] -= gone
-                orphan.setdefault(f, set()).update(gone)
-            if exit_ok and red.get(f):
-                if any(n.endswith(u"::" + WHOLE_FILE) for n in red[f]):
-                    if all(outcomes.get(n) == u"passed" for n in idents):
-                        red[f] = set()
-                else:
-                    red[f] = set(n for n in red[f] if outcomes.get(n) != u"passed")
-        green_now[f] = exit_ok and u"passed" in results
-
-
-def ticket_test_state(records, runs, ticket):
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
     """這張票底下每個測試檔的狀態。**純函式,不讀檔。**
 
     回傳 `{test_file: {"state": "red" | "green" | "unknown" | "orphaned",
@@ -466,7 +486,10 @@ def ticket_test_state(records, runs, ticket):
       (producer 在同一個 session 先寫逐檔紀錄、最後寫 run 事實)。
     - **8 欄紀錄沒有 run 事實 ⇒ coverage 未知**:red 紀錄加紅,green 紀錄**不退任何紅**,
       且不能讓該檔變成 green(只到 `unknown`)—— Backward compatibility 2。
-    - `green` 只來自最新一次碰到該檔的 run:exit code ∈ {0, 1}、該檔 ≥1 passed、0 failed。
+    - `green` 只來自最新一次碰到該檔的 run:schema 合格、非 D、對該檔整檔涵蓋(`"true"`)、
+      該檔 ≥1 passed、0 failed。
+    - `rl`:該 root 的 redlight 模組(提供 `validate_session` / `run_state` / `file_coverage`);
+      None ⇒ 涵蓋一律未知(只加紅、不退紅)。
     """
     if not ticket:
         return {}
@@ -490,7 +513,7 @@ def ticket_test_state(records, runs, ticket):
                 red.setdefault(f, set()).update(_red_identities_of_row(rec))
             green_now[f] = False
             continue
-        _apply_run(run, red, orphan, green_now)
+        _apply_run(run, red, orphan, green_now, rl)
 
     out = {}
     for f in set(red) | set(orphan) | set(green_now):
@@ -514,6 +537,10 @@ def _last_run_text(facts, rl, ticket):
     if not mine or rl is None or not hasattr(rl, "run_state"):
         return NO_RUN
     r = mine[-1]
+    problems = rl.validate_session(r) if hasattr(rl, "validate_session") else []
+    if problems:
+        # 不合格的 run:不顯示成 A–F 任何一個,也不從它算計數(錯型別不得照常迭代)
+        return u"INVALID(schema 不合格:%s)" % u";".join(problems)
     outs = list((r.get("outcomes") or {}).values())
     return u"%s(exit %s;collected %d / deselected %d / passed %d / failed %d / skipped %d)" % (
         rl.run_state(r), r.get("exit_code"), len(r.get("collected") or []),
@@ -521,6 +548,15 @@ def _last_run_text(facts, rl, ticket):
         outs.count(u"skipped"))
 
 
+def _invalid_count(facts, rl, ticket):
+    """本票 schema 不合格的 run 筆數。無法驗證(舊版 redlight)⇒ 0。"""
+    if rl is None or not hasattr(rl, "validate_session"):
+        return 0
+    return len([r for r in (facts or [])
+                if isinstance(r, dict) and r.get("ticket_id") == ticket
+                and rl.validate_session(r)])
+
+
 def _run_source(root, run_log, rl):
     left = _rel(root, run_log) if run_log else NO_FUNC
     right = (_rel(root, rl.session_log(root)) if rl is not None and hasattr(rl, "session_log")
@@ -794,7 +830,7 @@ def _evidence(root, gate, ticket):
     elif not ticket:
         val = u"%s(無當前票)" % UNRECORDED
     else:
-        st = ticket_test_state(runs or [], facts or [], ticket)
+        st = ticket_test_state(runs or [], facts or [], ticket, rl)
         n = {k: len([1 for s in st.values() if s[u"state"] == k])
              for k in (u"red", u"green", u"unknown", u"orphaned")}
         last = runs[-1] if runs else None
@@ -802,8 +838,12 @@ def _evidence(root, gate, ticket):
                                           _field(last, "result"),
                                           _field(last, "time"))
                 if last else u"最後一筆 %s" % UNRECORDED)
-        val = u"本票 red %d / green %d / run 事實未知 %d / orphaned %d;%s;最近一次 run:%s" % (
-            n[u"red"], n[u"green"], n[u"unknown"], n[u"orphaned"], tail,
+        # 票 145 Station 4b:schema 不合格的 run 不進正常語意,但**不靜默丟棄** ——
+        # 筆數留在這一行,最近一次若不合格則尾段顯示 INVALID(…)(〈十七〉裁決 3)。
+        val = (u"本票 red %d / green %d / run 事實未知 %d / orphaned %d / schema 不合格 run %d;"
+               u"%s;最近一次 run:%s") % (
+            n[u"red"], n[u"green"], n[u"unknown"], n[u"orphaned"],
+            _invalid_count(facts, rl, ticket), tail,
             _last_run_text(facts, rl, ticket))
     out.append(_line(u"test-runs", val, _run_source(root, run_log, rl)))
 
@@ -999,7 +1039,7 @@ def _derived(root, gate, stage, ticket):
     if (runs is None and not facts) or not ticket:
         vals = dict((k, UNRECORDED) for k, _l in labels)
     else:
-        st = ticket_test_state(runs or [], facts or [], ticket)
+        st = ticket_test_state(runs or [], facts or [], ticket, rl)
         for k, _l in labels:
             files = sorted(f for f, s in st.items() if s[u"state"] == k)
             if k == u"orphaned":
diff --git a/tests/conftest.py b/tests/conftest.py
index dd0735e..7f6fe5e 100644
--- a/tests/conftest.py
+++ b/tests/conftest.py
@@ -231,10 +231,37 @@ def pytest_sessionfinish(session, exitstatus):
     if not hasattr(_redlight, "record_session"):
         return
     selected = _run["selected"] if _run["selected"] is not None else list(_run["outcomes"])
-    _redlight.record_session(
-        _ROOT,
+    kwargs = dict(
         exit_code=exitstatus,
         collected=list(selected) + list(_run["deselected"]) + list(_run["collect_errors"]),
         deselected=list(_run["deselected"]),
         outcomes=dict(_run["outcomes"]),
     )
+    # 票 145 Station 4b:涵蓋範圍的判定依據(〈十七〉裁決 1)—— pytest 實際收到的
+    # 位置參數與它們的來源。沒有 config ⇒ None ⇒ 涵蓋範圍未知(不知道,就不是完整)。
+    # 舊版 redlight.py 的 record_session 沒有 `invocation` 參數 ⇒ 照舊不傳。
+    import inspect as _inspect
+    if "invocation" in _inspect.signature(_redlight.record_session).parameters:
+        kwargs["invocation"] = _invocation_of(session)
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
diff --git a/tests/test_status.py b/tests/test_status.py
index 99c3c25..196b304 100644
--- a/tests/test_status.py
+++ b/tests/test_status.py
@@ -574,7 +574,8 @@ class TestTestsUnderTicketUsesTheLatestRecordPerFile:
         redlight.record_session(
             root, run_id=u"fixture-570-571", time=u"2026-09-02T02:00:00+00:00",
             ticket_id=u"99", exit_code=0, collected=[u"tests/test_a.py::test_one"],
-            deselected=[], outcomes={u"tests/test_a.py::test_one": u"passed"})
+            deselected=[], outcomes={u"tests/test_a.py::test_one": u"passed"},
+            invocation={u"args": [u"tests"]})
 
         out = render(root)
         red = _value_of(out, u"tests red under ticket 99")
@@ -1326,7 +1327,8 @@ class TestOrphans:
                                 deselected=[], outcomes={old: u"failed", keep: u"passed"})
         redlight.record_session(root, run_id=u"odc2-2", time=u"2026-09-02T02:00:00+00:00",
                                 ticket_id=u"99", exit_code=0, collected=[new, keep],
-                                deselected=[], outcomes={new: u"passed", keep: u"passed"})
+                                deselected=[], outcomes={new: u"passed", keep: u"passed"},
+                                invocation={u"args": [u"tests"]})
         out = render(root)
         orphaned = _value_of(out, u"tests orphaned under ticket 99")
         green = _value_of(out, u"tests green under ticket 99")
```

---

## F. Station 4b 證據(逐字)

出處:`851cbd75b359a6b2a34452265e8a70992fa56996:docs/audits/2026-10-02-m1a-station4b-fix.md`;
該檔在 `<TARGET>` 的 blob ID:`28da58e8ee263dc5233e5f0abccb2cecef47e00d`。
以下三段逐字照錄,**其中原有的遮罩與遮罩說明一併保留**(遮罩過的行不是原始輸出,原報告已就地註明)。

### F.1 「驗收」段

行號來源:851cbd75b359a6b2a34452265e8a70992fa56996:docs/audits/2026-10-02-m1a-station4b-fix.md 第 126–152 行

<!-- 逐字開始 -->
### 驗收|在 `333e585` 上跑固定全套(只跑一次)

```
$ date -u +%Y-%m-%dT%H:%M:%SZ
2026-10-02T17:03:26Z
$ python -X utf8 -m pytest -q
...
SKIPPED [1] tests\test_gate.py:451: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:459: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:473: 此環境無法建立 symlink
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/srv/x] - …
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/data/x] - …
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/backup/x] - …
1946 passed, 3 skipped, 3 xfailed in 147.38s (0:02:27)

[exited with code 0]
```

(XFAIL 三行的說明文字以 `…` 截斷 —— 本區塊**不是逐字全文**;SKIPPED 與摘要行逐字。輸出中無任何 `FAILED` / `ERROR` 行。背景執行,完成通知回報 `exit code 0`。)

**判定**

| 條件 | 結果 |
|---|---|
| exit code = 0;failed = 0 | **成立** |
| 3b 的 17 支、L1–L3、Station 3 的 14 支不在失敗集合 | **成立**(失敗集合為空) |
| 摘要 1946 passed;skipped / xfailed 3 / 3 | **成立**(1946 = 1929 + 17;skip / xfail 為 baseline 同一批) |
<!-- 逐字結束 -->

### F.2 「帳本只追加」段

行號來源:851cbd75b359a6b2a34452265e8a70992fa56996:docs/audits/2026-10-02-m1a-station4b-fix.md 第 154–185 行

<!-- 逐字開始 -->
### 帳本只追加

```
$ wc -c -l .dev/test-runs.jsonl .dev/test-sessions.jsonl
   2319  624488 .dev/test-runs.jsonl
     12 1873333 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl .dev/test-sessions.jsonl
73737b7ddc353b2049d3bf8a61e831c9e2ab57e44b634ba91349447d1d0a8a93 *.dev/test-runs.jsonl
42bdc38e99695014d384f501cbf8517ca6a72d5bde690f090fcfc190d6c27e35 *.dev/test-sessions.jsonl
$ head -c 613185 .dev/test-runs.jsonl > <session scratch>/runs-prefix-4b.bin
$ head -c 1413031 .dev/test-sessions.jsonl > <session scratch>/sessions-prefix-4b.bin
$ sha256sum <session scratch>/runs-prefix-4b.bin <session scratch>/sessions-prefix-4b.bin
b555ded4e2986f819c711c4ef16168c9df25f54cce12fd8064141e9cc7bc2ada *<session scratch>/runs-prefix-4b.bin
d97b7631d55ba0b8359803a6b2ffa9c6330de02b8363dc0c769afea6eb38e12e *<session scratch>/sessions-prefix-4b.bin
```

(scratchpad 絕對路徑以 `<session scratch>` 代替 —— **這三條指令與輸出經遮罩,不是逐字原文**;`wc` 的 `total` 行省略。)

- test-runs:2319 − 2273 = **46** 行(= 測試檔數);前 613185 bytes = H0 ⇒ **前段逐位元組不變**。
  以 `Grep "result": "red"` 列出全帳本 red 紀錄,最後一筆在第 2266 行(< 2274)⇒ 新增 46 筆 **0 red、全 green**。
- test-sessions:12 − 11 = **1** 行;前 1413031 bytes = H0 ⇒ **前段逐位元組不變**。新增那一行的欄位頭與 invocation:

```
"kind": "session", "run_id": "7ec16d4b97d1478b893e354681623a78", "time": "2026-10-02T17:05:51.724830+00:00", "ticket_id": "145", "exit_code": 0
"invocation": {"args": ["tests"], "args_source": "TESTPATHS", "pyargs": false}
```

  ⇒ **〈十八之一〉的靜態推導在真實執行中得到印證**(固定指令 `config.args == ["tests"]`、`args_source == TESTPATHS`)。
  全帳本只有這一筆帶 `invocation`(先前的 session 由舊版 producer 產生,沒有這個欄位 ⇒ 涵蓋範圍未知)。
- 測試的假身分 / 假檔名 / 假 run_id 在兩本真實帳本中皆 **0** 筆。

全套後工作樹:`git status --porcelain` 無輸出。
<!-- 逐字結束 -->

### F.3 「status.py 的 Evidence 與 Derived」段

行號來源:851cbd75b359a6b2a34452265e8a70992fa56996:docs/audits/2026-10-02-m1a-station4b-fix.md 第 187–209 行

<!-- 逐字開始 -->
### status.py 的 Evidence 與 Derived

`python .claude/portable/status.py --root .`(一處遮罩:`report:` 行的 HEAD 時間含本地時區偏移,以 `<本地時間>` 代替;`tests green under ticket 145` 的 46 檔清單以「(46 檔)」代替;其餘逐字):

```
=== Evidence ===
test-runs: 本票 red 0 / green 46 / run 事實未知 0 / orphaned 0 / schema 不合格 run 0;最後一筆 tests/test_verify_gates.py=green @ 2026-10-02T17:05:51.724830+00:00;最近一次 run:A(exit 0;collected 1952 / deselected 0 / passed 1946 / failed 0 / skipped 3)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl)
intercepts (當月): 1 筆  (source: .dev/intercepts-2026-10.jsonl)
intercepts (最新存在月): 2026-10 1 筆;末筆 R7@2026-10-02T12:12:16.405577+00:00  (source: .dev/intercepts-2026-10.jsonl)
exemptions: 總 281 筆;granted 240 筆;blocked 1 筆;未記錄(無此欄)40 筆;最後一筆 2026-09-24T08:17:49.073745+00:00  (source: .dev/gate-exemptions.jsonl)
provenance: 未記錄(上游無此檔屬正常)  (source: .dev/provenance.jsonl)
report: 2026-09-24T084909Z-ticket137-status-line.md;HEAD <本地時間>;回報後 18 筆  (source: .dev/reports/)

=== Derived ===
src write allowed in implement: yes  (source: gate.stage_allows_src_write() <- .agents/pipeline-stages.yaml)
tests red under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests green under ticket 145: (46 檔)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests green (run 事實未知) under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests orphaned under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
rules defined: R1 R2 R3 R4 R5 R6 R7 R8 R9  (source: gate.rule_codes())
```

`collected 1952` = 1946 passed + 3 skipped + 3 xfail(記為 `other`)。
<!-- 逐字結束 -->

---

## G. 必答問題(G1–G11)

每題回答「成立 / 不成立 / 無法判定」,並附 `<TARGET>:<路徑>:<行號>` 證據。
「成立」須指出讓它成立的程式碼行;「不成立」須給出具體輸入與錯誤輸出(可用紙上推演,**不得執行 pytest**)。

**G1. F1–F4 是否逐條被修正?**
對〈C〉的每一條,指出 `<TARGET>` 中阻止該情境的程式碼行,並說明〈C〉所列的具體情境在 `<TARGET>` 上會得到什麼結果。
F4 另須指出串接測試(producer → 持久化 run 事實 → status)的 nodeid。

**G2. `file_coverage` 是否只在正向證明時為 `"true"`?固定指令是否經由通用規則得到 `"true"`?**
逐條檢查 `redlight.file_coverage` 的每一個 `return "true"` 路徑,確認每一條都需要「位置參數為該檔或其上層目錄、不含 `::`、該檔無 deselected、無收集錯誤、非 pyargs」。
確認沒有任何以固定指令、`args_source == "TESTPATHS"` 或特定字串為條件的特殊分支。

**G3. D run 是否沒有退紅權、不能產生 green?**
包括:D 的成因為他檔收集錯誤、exit code 不在 {0, 1, 5}、exit code 為 None。確認 `_apply_run` 在 D 時對**每一個檔**都不退紅、不 orphan、不 green。

**G4. schema 不合格的 session 是否 fail-closed 且可被觀察到?**
確認:不合格 run 不加紅、不退紅、不 orphan、不 green;`run_state` 回 `INVALID`;status 輸出不會把它顯示成 A / B / C / F;Evidence 有計數與 `INVALID(…)` 表示。
另檢查:`_last_run_text` 只看「本票最後一筆」—— 若最後一筆合格、較早一筆不合格,不合格那筆是否仍可被觀察到(計數)。

**G5. `-x` / `--maxfail` 提前停止的 run 怎麼被判定?是否與〈十七〉一致?**
提前停止時,未執行的身分既不在 deselected、也沒有 outcome;exit code 通常為 1(或中斷時為 2)。
請推演:(a) 某檔的已知紅身分排在停止點之後、從未執行;(b) 身分不明的整檔紅、該檔只有部分身分執行;(c) 停止點所在檔之外、完全沒被執行到的檔。
每一種情形下,`file_coverage`、退紅、green、orphan 的結果各是什麼?是否違反 ODC-1 第 2 項或「Absence is not coverage」?

**G6. `--collect-only` 的效果是什麼?**
`--collect-only` 也會經 conftest 寫一筆 session(outcomes 為空)。請推演:它的 `run_state`、對每檔的 `file_coverage`、對既有 red / green / orphan 的影響。
是否可能造成退紅、orphan,或把一個原為 green 的檔變成其他狀態?後者是否可接受(對照〈H〉第 3 項)?

**G7. 位置參數的正規化在下列情形下是否正確?**
逐一推演 `_normalize_arg` 與 `file_coverage` 的結果(假設 root = repo 根):
(a) 從子目錄執行(invocation dir ≠ root);(b) `./tests`;(c) `tests/`(尾端斜線);(d) 反斜線 `tests\test_x.py`;(e) root 內的絕對路徑;
(f) `.`;(g) root 之外的路徑;(h) `--rootdir` 指向別處(rootpath ≠ repo 根,而帳本 root 仍是 repo 根);(i) `--pyargs`。
特別檢查:前綴比對是否帶路徑邊界(`tests` 不得涵蓋 `tests_extra/test_x.py`);`..` 開頭但不是上層目錄的檔名(如 `..foo`)是否被誤判。

**G8. `-k` / `-m` / `--deselect` / `--lf` 是否一律得到 `"false"`?**
這四者都透過 `pytest_deselected` 回報被排除的身分嗎?若某一種**不**經過 `pytest_deselected`(例:`--lf` 在收集階段直接略過檔案或身分),它會落到哪一個結果?該結果是否仍不給退紅權?

**G9. 向後相容是否成立?**
(a) 沒有 `invocation` 欄位的舊 session(舊版 producer 寫的)⇒ 涵蓋是否為 `"unknown"`?
(b) 只有 8 欄紀錄、沒有任何 session ⇒ 是否永遠不退紅、不 green(只到 `run 事實未知`)?
(c) 下游 repo 的舊版 redlight.py(沒有 `validate_session` / `file_coverage`)搭配新版 status.py ⇒ 是否只加紅、不退紅?
(d) 新版 conftest 搭配舊版 redlight(`record_session` 沒有 `invocation` 參數)⇒ 是否不拋例外?

**G10. 測試是否沒有被放寬?**
(a) `git diff af839c6..851cbd75b359a6b2a34452265e8a70992fa56996 -- tests/test_redlight.py` 應無輸出。
(b) `tests/test_status.py` 自 `af839c6` 起只有兩處改動,且都只是在 `record_session(...)` 尾端加 `invocation={u"args": [u"tests"]}`(〈十七〉裁決 5 授權);沒有任何 assertion、docstring、test identity 被改。
(c) 這兩處補件是否只是「補上整檔涵蓋事實」,而沒有讓原本應失敗的情境變成通過?

**G11. producer 的錯誤能不能讓 pytest 失敗,或寫出半行?**
(a) `record_session` 內的例外(含 `_normalize_invocation` / `_normalize_arg` 的例外)是否都被吞掉、不讓 pytest 失敗?
`_normalize_invocation` 在 `try` 之外被呼叫 —— 若它拋例外,會發生什麼?
(b) `conftest._invocation_of` 與 `inspect.signature(...)` 若拋例外,`pytest_sessionfinish` 會怎樣?
(c) 寫入是否為單次 `write(json + "\n")`?在什麼情形下可能留下半行?留下半行時 `load_runs` 的行為(整本回 `[]`)對紅綠判定的方向是 fail-closed 還是 fail-open?

---

## H. 已知例外與未證明事項

### H.1 Station 4b 報告的「尚未證明 / 本輪未做」(逐字)

行號來源:851cbd75b359a6b2a34452265e8a70992fa56996:docs/audits/2026-10-02-m1a-station4b-fix.md 第 234–240 行

<!-- 逐字開始 -->
1. **CLEAN 層**未證明;**REAL 層**留待 Jeff 端 status_all 確認。
2. **窄選(nodeid / `-k`)與中斷的真實 pytest 情形**未在真實執行上觀察過 —— 只由 3b 紅燈的 fake 驅動與串接測試證明。
3. **`--collect-only` 也會寫一筆 session**:在新規則下,它對碰到的檔可能為 `true` 涵蓋但沒有 passed ⇒ 不退紅、不 green(那些檔的最新證據會變成「run 事實未知」直到下一次全套)。本輪未另驗。
4. **〈十〉現況句**仍寫「Station 5 FAIL,回 Station 3b 補紅燈,Station 4b 未開始(與票頭第 3 行一致)」—— 與新第 3 行不一致;本刀授權外,未改,待裁。
5. **3b 刀③ 的程序違規**(`--check` 有輸出時 commit 的 6 筆)仍待裁。
6. `.dev/test-sessions.jsonl` 已達 1.87 MB(〈十七〉裁決 8 的 debt)。
7. 十六個 commit 均未推。
<!-- 逐字結束 -->

(第 4 項已在 S5b-0 處理:票 145〈十〉現況句已同步。第 5 項見 H.2。這兩句是本包的說明,不屬於上面的逐字段落。)

### H.2 已裁定的例外與債務

| 項 | 處置 | 是否擋 Station 5b |
|---|---|---|
| Station 3b 刀③ 的程序違規(`git diff --check` 有 6 筆輸出時仍 commit) | **已知例外**;不改寫歷史 | 否 |
| 前一份審查包(`docs/audits/2026-10-02-m1a-station5-review-package.md`)的 7 處 trailing whitespace | **已接受的例外**(〈十七〉已記錄;內嵌 diff 的空白 context 行) | 否 |
| `.dev/test-sessions.jsonl` 增長(Station 4b 後約 1.87 MB,全檔讀取) | **債務**(〈十七〉裁決 8);M1-a 結案時另開票 | 否(非阻擋) |
| 本包〈E〉內嵌 diff 的空白 context 行 | `git diff --check` 會報 trailing whitespace;是 diff 原樣,不是編輯錯誤 | 否 |

審查者若認為上表任一項應改為阻擋,須以「阻擋」發現提出並附證據;否則不重複列為發現。
