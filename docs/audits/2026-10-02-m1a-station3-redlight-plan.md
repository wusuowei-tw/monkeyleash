# M1-a Station 3 —— 紅燈規劃書(只規劃,不寫測試)

**這份檔案的身分**:Station 3 紅燈規劃,交裁決者裁決。**進版控**
(位置依據:`docs/agents/handover.md:34`「**回報檔一律進版控**(`docs/audits/`)」)。
路徑一律寫 repo 相對路徑。

| | |
|---|---|
| **撰寫時點** | 2026-10-02T13:48:16Z(寫入當下) |
| **規劃基準 HEAD** | `84014bae237a4741dae8ad18c6c041a3c3ef97b0` |
| **本輪 commit** | 本規劃書所在的 commit;SHA 無法寫進自己 —— 見該 commit |
| **本輪未做** | 未寫任何測試、未改票 145、未改任何 `.py`(含 `tests/conftest.py`)、未跑 pytest、未改 pipeline.json、未推 |

---

## 【給裁決者】

1. 規劃完成:觀察契約(一、A)共 7 項;紅燈 13 條規格、14 支測試(RL-6b 拆兩支);其中 **3 支是「行為紅」**(RL-6 歷史重現、RL-6b 舊寫入版、RL-7),其餘 11 支是「介面紅」。
2. RL-6 用真實帳本第 940 行(9/13 那條紅)+ 票 139 `:39` 原文(= 帳本第 970 行),**不用任何合成資料**,在現行 HEAD 會判成 green —— 是行為紅(由原始碼推得,未執行;第 3 站全套跑時驗證)。
3. 新發現:`redlight.py` 與 `gate.py` 都在 R3 豁免清單(`.agents/legacy-no-redlight.txt`)裡 ⇒ 第 4 站改紅燈產生器時,**閘門不要求先有紅燈**;只有 `status.py` 受 R3 約束。這與 conftest.py 缺口同性質,一併登記。
4. 要你裁 6 件(見下方「需要裁的事項」),其中 **2 件不裁就寫不出紅燈**:①status 從哪裡讀 run 事實;②570/571 的 fixture 補件怎麼做。
5. 不裁的話:第 3 站停在 baseline;RL-6 歷史重現那條可以先寫(不依賴任何未裁事項)。

### 最低必要內容

| # | 項目 | 摘要 |
|---|---|---|
| 1 | 一、A 各項 | 見下表「A 契約一句話摘要」;一、B **不能全部延後** —— 2 項須先裁(見一、B-2) |
| 2 | 新增觀察介面 | `redlight.record_session()`、`redlight.load_runs()`、`redlight.run_state()`、`status.ticket_test_state()`;`status.render()` 新增 2 行輸出、改寫 1 行的尾段 |
| 3 | 逐條 RL | 見下表「逐條紅燈」 |
| 4 | RL-6 | (1) 真實帳本第 940 行;(2) 票 139 `:39` 原文(逐字等於帳本第 970 行);無 synthetic;**行為紅** |
| 5 | 既有測試影響 | **2 條斷言**(570、571)結果會變;**749 不變**(`_latest_per_file` 保持原語意);可只靠補 fixture 處理,**但補件方式須裁**(見第 2 件) |
| 6 | conftest.py 缺口 | 建議 **(b) 另開框架票**;理由:修法是改 `NON_SOURCE_DIRS` 的分類,屬閘門邊界,不屬 run-evidence 語意 |
| 7 | 需裁事項 | 6 件,見下方 |
| 8 | commit / `0 1` / 樹 | 只在視窗回報(發生在本檔 commit 之後) |
| 9 | push / 寫測試 / 改 conftest.py / pytest | **NO / NO / NO / NO** |

**A 契約一句話摘要**

| # | 契約項 | 一句話 |
|---|---|---|
| A-1 | run identity | 每次 pytest session 產生恰好一個 run,帶唯一 `run_id` |
| A-2 | test identity(Q7) | 以正規化 nodeid(`tests/x.py::Class::test`,斜線一律 `/`)為鍵;舊紀錄的身分 = `test_file` + `::` + `failed_tests` 的一項 |
| A-3 | 每個 run 的事實 | collected、deselected(身分清單)、每個身分的 outcome(passed / failed / skipped / other) |
| A-4 | invocation outcome | 記原始 exit code;狀態 A–F 由 `redlight.run_state()` 依固定對照表推出(對照表見一、A-4) |
| A-5 | coverage 已知 / 未知 | 沒有對應 run 的紀錄(含全部既有 8 欄紀錄)一律判為「run 事實未知」,不推論 |
| A-6 | 與 per-test 紀錄的關聯(Q3) | 讀取端以 `ticket_id` + 時間序把 run 與紀錄對齊;既有紀錄不補任何欄位 |
| A-7 | status 判定 | 依〈十一〉ODC-1 三條件退紅;ODC-2 孤兒獨立一行;ODC-3 / E 印「無 run 證據 / 不可判定」 |

**逐條紅燈**

| RL | 放哪個檔 | 行為紅 / 介面紅 |
|---|---|---|
| RL-1 Full pass | `tests/test_redlight.py` | 介面紅 |
| RL-2 One failure | `tests/test_redlight.py` | 介面紅 |
| RL-3 Zero collected | `tests/test_redlight.py` | 介面紅 |
| RL-4(a) 收集錯誤 | `tests/test_redlight.py` | 介面紅 |
| RL-4(b) invocation 錯誤 | `tests/test_redlight.py` | 介面紅 |
| RL-4(c) 中斷 | `tests/test_redlight.py` | 介面紅 |
| RL-5 No invocation | `tests/test_status.py` | 介面紅 |
| **RL-6 票 139 歷史重現** | `tests/test_status.py` | **行為紅** |
| RL-6' 票 139 現場重現(producer) | `tests/test_redlight.py` | 介面紅 |
| **RL-6b 窄選未涵蓋 X(舊寫入版)** | `tests/test_status.py` | **行為紅** |
| RL-6b 窄選未涵蓋 X(run 事實版) | `tests/test_status.py` | 介面紅 |
| **RL-7 歷史紀錄** | `tests/test_status.py` | **行為紅**(依 I5 判讀,見三) |
| ODC-2 孤兒 | `tests/test_status.py` | 介面紅 |
| ODC-3 producer 未載入 | `tests/test_status.py` | 介面紅 |

(RL-6b 兩版算一條規格、兩支測試;上表 14 列 = 13 條規格 + RL-6b 拆兩支。)

**需要裁的事項**

| # | 事項 | 選項 | 建議 |
|---|---|---|---|
| 1 | **status 從哪裡讀 run 事實**(不裁寫不出 status 側紅燈) | (i) status 依 root 載入 `<root>/.claude/hooks/redlight.py` 的 `load_runs()`(與既有 `load_gate()` 同一手法);(ii) gate.py 露出路徑常數,status 自己解析;(iii) 讀取函式放進 gate.py | **(i)**:不碰權威層 gate.py、只有一份解析碼;代價見第 2 件 |
| 2 | **570/571 的 fixture 補件怎麼做**(不裁寫不出) | A 補件以 `hasattr(redlight, "record_session")` 守住 —— HEAD 下不執行(仍綠),第 4 站後生效;B 直接手寫 run 事實的 JSON —— 等於現在就裁 Q1/Q2;C 補件延到第 4 站與實作同一個 commit | **A**;另需授權 `_make_root()` 多複製一個檔(`redlight.py`)—— 那是測試基礎設施,**不是** run-level facts,超出〈十一〉「只准補 run-level facts」的字面 |
| 3 | 紅燈紀錄的身分不明時怎麼退紅(`failed_tests` 缺欄、為空、或為 `["<collection error>"]`) | 視同「該檔全部身分都是先前紅的」—— 退紅須該檔每個 collected 身分都實際執行且通過 | 照建議。570/571 的 fixture 紅燈列正是缺 `failed_tests` 的情形 |
| 4 | ODC-1 第 3 條「本次 run 沒有任何 failure」的範圍 | 全 run(跨檔) / 只限該檔 | **全 run**(照裁決字面) |
| 5 | conftest.py 缺口 | (a) 本票處理 / (b) 另開框架票 | **(b)**,理由見五 |
| 6 | redlight.py 的 R3 豁免 | (甲) 接受為 residual,第 4 站只靠 staged diff 與票面守;(乙) 第 3 站紅燈跑完後,依清單既有排水格式把 `.claude/hooks/redlight.py` **移出**豁免清單(排水方向不需批准新增,但改的是本輪 allowlist 外的檔) | **(乙)**:紅燈全套跑會留下一筆對著 HEAD 內容的 `tests/test_redlight.py` 紅燈,正好滿足 R3 後半;移出後第 4 站改 redlight.py 會被 R3 真的檢查 |

---

## 【給裁決助手】規劃書本文

### 前置

```
$ git fetch origin
(無輸出)
$ git rev-list --left-right --count origin/master...HEAD
0	0
$ git rev-parse HEAD
84014bae237a4741dae8ad18c6c041a3c3ef97b0
$ git status --porcelain
(無輸出)
```

讀過的檔(唯讀):票 145、票 139、`tests/conftest.py`(全檔 173 行)、`.claude/hooks/redlight.py`(全檔 144 行)、
`.claude/portable/status.py`(`_latest_per_file` `:312-334`、`_evidence` `:586-662`、`_ticket` `:742-776`、`_derived` `:779-816`、`render` `:823-837`)、
`tests/test_redlight.py`(全檔 229 行)、`tests/test_status.py`(`:1-140`、`:155-180`、`:255-300`、`:530-580`、`:680-800`)、
`tests/test_evidence_isolation.py`(`:20-110`)、`.agents/legacy-no-redlight.txt`(全檔)。

---

## 一、表示法提案

### 一、A —— Station 3 必須裁的 observable contract(紅燈測試會依賴)

以下只定**語意、函式簽名、輸出字樣**,不寫實作。

#### A-1 run identity

- 每次 pytest session(一次 runner invocation)產生**恰好一個 run 事實**,帶 `run_id`(字串,在同一個帳本內唯一;產生方式屬 B)。
- runner 沒有被呼叫、或 producer 沒有被載入 ⇒ **沒有 run 事實**(E 與 ODC-3 在此不可區分,依〈十一〉ODC-3 接受為 residual)。
- 滿足:狀態 A–F(每個 run 有一個可判讀的狀態)、I7、AC-1。

#### A-2 test identity(Q7)

- 身分 = 正規化 nodeid:相對 rootdir、分隔符一律 `/`,例:`tests/test_gate.py::TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce`。
- **既有紀錄的身分**:`test_file` + `::` + `failed_tests` 的一項。這不是補寫事實 —— 兩個欄位當時就寫在同一筆裡(`conftest.py:165` 取 nodeid 的 `::` 之後那段),只是把它們讀在一起。
- 參數化測試:身分含參數段(`[...]`),每個參數化案例是獨立身分。
- 身分不明的紅燈(`failed_tests` 缺欄、為空、或為 `["<collection error>"]`):見需裁事項第 3 件。
- 滿足:I4 前提(「測試 X」必須可識別)、〈十一〉ODC-1 條件 2、ODC-2。

#### A-3 每個 run 的事實

| 事實 | 語意 |
|---|---|
| `collected` | 本次收集到的身分清單(收集錯誤的檔以 `<collection error>` 標記) |
| `deselected` | 被 `-k` / `-m` / `--deselect` 排除的身分清單 |
| `selected` | 推得:`collected − deselected` |
| `outcomes` | `{身分: "passed" \| "failed" \| "skipped" \| "other"}`,只含 selected 的身分 |
| `executed` | 推得:outcome 為 `passed` 或 `failed` 的身分(**skipped 不算執行**) |
| `exit_code` | runner 回傳的原始退出碼;取不到為 `None` |
| `ticket_id` | 與既有紀錄同源(`redlight.current_ticket()`),**字串** |
| `time` | 寫入時點(UTC ISO 8601) |

- `other`:xfail、xpass(非 strict)等。**本規劃不宣稱它們屬於 A–F 的任何一個**(票 145〈三〉A 節:本 M1-a 不要求);在計數上不算 passed、也不算 failed。strict xpass 由 pytest 報成 failed,照 failed 記。
- 滿足:I7(選了哪些、跳過幾條、未選幾條皆可觀察)、I2、AC-1、AC-2。

#### A-4 invocation outcome —— `redlight.run_state(run) -> str`

純函式,輸入一個 run 事實,回傳 `"A"`–`"F"` 之一。**依序判定,先命中者為準**:

| 順序 | 條件 | 狀態 |
|---|---|---|
| 1 | `exit_code` ∈ {2, 3, 4},或 `exit_code` 為 `None`,或 collected 含 `<collection error>` | **D** |
| 2 | 任一 outcome 為 `failed` | **B** |
| 3 | `collected` 為空 | **C** |
| 4 | 沒有任何 outcome 為 `passed`(含全部 skipped、全部 deselected、混合) | **F** |
| 5 | 其餘(≥1 passed、0 failed) | **A** |

- **判定不只看 exit code**:全部 deselected 時 pytest 回 5,但 collected 非空 ⇒ 落在第 4 列 **F**,不是 C(票 145〈三〉A:F 包含「全部 deselected」)。
- E 沒有 run 事實可輸入,不在本函式值域內;由讀取端以「找不到 run」表示(A-7)。
- 滿足:A–F 的可區分(AC-1)、F ≠ A、F 與 C 分開、I3(中斷 / 錯誤 ⇒ D,不會是 A)。

#### A-5 coverage 已知 / 未知

- 一筆 per-test 紀錄**有對應的 run 事實** ⇒ coverage 已知;**沒有** ⇒「run 事實未知」。
- 全部既有 8 欄紀錄(帳本現有 2043 行,以 HEAD `84014ba` 時點為底)沒有對應 run ⇒ **一律判為 run 事實未知**。
  不得推論為 full pass、zero tests、runner error、full-suite execution(Backward compatibility 2)。
- 讀取端**不改寫、不補寫**任何既有紀錄(Backward compatibility 1、4)。
- 滿足:I1、I6、Backward compatibility 1–4、RL-7、AC-5、AC-6。

#### A-6 run 事實與既有 per-test 紀錄的關聯(Q3)

- 讀取端把每個 run 事實視為「該 run 涵蓋的所有檔」的權威來源;per-test 紀錄(8 欄)照舊存在,供 R3 與既有 consumer 使用。
- 一筆 per-test 紀錄是否「屬於」某個 run:由讀取函式回答(`load_runs()` 回傳的 run 內帶它涵蓋的檔與身分;8 欄紀錄**本身不加欄位**)。
- 實際用什麼鍵把兩者接起來(時間窗、共同 `run_id`、或 run 事實自帶逐檔結果)屬 B(Q1/Q2)。**紅燈測試只透過 `load_runs()` 與 `status` 的輸出觀察,不讀實體格式。**
- 滿足:I6、Backward compatibility 1、AC-6。

#### A-7 status 的判定與呈現

**判定函式**:`status.ticket_test_state(records, runs, ticket) -> dict`(純函式,不讀檔)。

- 輸入:`records` = 8 欄紀錄 list、`runs` = `load_runs()` 的結果、`ticket` = 票號字串。
- 回傳:`{test_file: {"state": "red" | "green" | "unknown" | "orphaned", "unresolved": [身分...]}}`。
- **退紅規則**(〈十一〉ODC-1,逐字三條件):某檔內一個先前為 red 的身分,只有在**較晚**的某個 run 同時滿足下列三項時才退紅:
  1. 該檔的測試集合全部被選到(該檔 `deselected` 為空);
  2. 先前為 red 的那些身分在該 run 中 `executed` 且 `passed`;
  3. 該 run 沒有任何 `failed`(範圍見需裁事項第 4 件)。
  該檔其他測試 skipped 不影響。partial selection、deselection、zero tests、coverage 未知的 run **一律沒有退紅權**。
- **檔的狀態**:
  - `red` —— 有 ≥1 個未退紅的身分(**含**:紅燈之後只有 coverage 未知的 green 紀錄);
  - `green` —— 沒有未退紅的身分,且最新證據有對應 run(coverage 已知);
  - `unknown` —— 沒有未退紅的身分,但最新證據 coverage 未知(全部既有 8 欄 green 紀錄落在這裡);
  - `orphaned` —— 有先前為 red 的身分,而較晚的 run 已**收集不到**它(刪除或改名;〈十一〉ODC-2)。改名不視為延續。

**`status.render()` 的輸出字樣**(既有欄名保留,新增兩行;每行照既有規矩帶 `(source: …)`):

| 行 | 狀態 | 值 |
|---|---|---|
| `tests red under ticket N:` | 既有,**語意改** | `state == "red"` 的檔(依上述退紅規則) |
| `tests green under ticket N:` | 既有,**語意改** | `state == "green"` 的檔(coverage 已知) |
| `tests green (run 事實未知) under ticket N:` | **新增** | `state == "unknown"` 的檔 |
| `tests orphaned under ticket N:` | **新增** | `state == "orphaned"` 的檔,後附孤兒身分 |
| `test-runs:` 的尾段 | 既有,**尾段改寫** | 原 `全套結果:未記錄(帳本不記全套)` 改為 `最近一次 run:<狀態>(exit <code>;collected <n> / deselected <n> / passed <n> / failed <n> / skipped <n>)`;找不到本票任何 run 時為 `最近一次 run:無 run 證據 / 不可判定` |

- 無帳本時整行照舊印 `未記錄`;無當前票時照舊以 `未記錄` 開頭、不含「本票」(票 100 的兩條既有斷言)。
- gate 或 redlight 缺新函式(舊版下游)時,新行印 `未記錄`,**不得**整份輸出崩掉(既有 `FAKE_GATE` 測試的同一條規矩)。
- 輸出不得含 `PASS` / `OK` 等靜態裁決字樣(既有 `VERDICT_TOKENS` 斷言)。
- 滿足:I4、I5、ODC-1、ODC-2、ODC-3、AC-4、AC-5、RL-6、RL-6b、RL-7。

**`status._latest_per_file()` 不改** —— 它保持「每檔最新一筆」的原語意,只是 `_evidence` / `_derived` 不再拿它決定紅綠。
這使 `tests/test_status.py:749` 的斷言結果不變(見四)。

### 一、B —— Station 4 才裁的 physical persistence(紅燈測試不得依賴)

#### B-1 可延後到第 4 站

| 項目 | 說明 |
|---|---|
| Q1 | run 事實放在 `.dev/test-runs.jsonl` 內,或另一個帳本 |
| Q2 | 是否新增 record type、欄位名、序列化格式 |
| `run_id` 的產生方式 | |
| producer 內部結構 | conftest 用哪些 pytest hook 收集 deselected / collected(`pytest_deselected`、`pytest_collection_finish`、`session.items` 等) |
| A-6 的接合鍵 | 時間窗、共同 `run_id`、或 run 事實自帶逐檔結果 |

**原則**:紅燈測試的假資料一律透過寫入函式 `redlight.record_session()` 產生,不手寫 JSON。**唯一例外**:RL-6 / RL-6b(舊寫入版)/ RL-7 用的歷史原始紀錄 —— 它們本來就是 8 欄格式,逐字取用。

**第 4 站裁 Q1/Q2 時必須守住的約束**(由本輪讀碼得出,只列不裁):

1. **R3 解析**:`gate.redlight_missing()` 對 `test_file` 命中的每一筆,缺 `impl_exists` 欄就**擋**(`gate.py:2143-2144`)。若 run 事實與 8 欄紀錄同檔,且帶 `test_file` 鍵,會讓 R3 fail-closed 擋下做對事的人。
2. **既有 consumer 的值域**:`status.py:601-602` 與 `_derived` 以 `result == "red"` / `== "green"` 計數;新紀錄若帶 `result` 第三值或 `test_file` 鍵,會被既有 consumer 誤收或靜默漏數(RECON 已記錄的同一族)。
3. **證據隔離測試**:`tests/test_evidence_isolation.py:28` 的 `EXPECTED_TO_GROW = {"test-runs.jsonl"}` 只豁免這一檔。另開帳本時,若它在 session **中途**被寫入,該測試會紅;只在 `pytest_sessionfinish` 寫則不受影響(該測試只比對單一測試函式前後)。
4. **既有 fake report**:`tests/test_redlight.py:184-190` 的 `_Report` 只有 `when` / `failed` / `nodeid` / `fspath`。producer 若讀 `report.skipped` / `report.outcome` 而不帶預設值,既有 3 條 `TestTheRecorderCannotKillTheRunner` 會以 `AttributeError` 紅 —— 那不是補 fixture 能處理的(屬改測試),所以 **producer 必須以 `getattr(..., 預設)` 讀這些屬性**。

#### B-2 **不可延後**的項目(逐條,交裁決者)

| # | 項目 | 為何不能延後 |
|---|---|---|
| B-2-1 | **status 從哪裡讀 run 事實**(需裁事項第 1 件) | status 側的紅燈要在 `tmp_path` 造的最小 repo 上跑 `render()`。`_make_root()`(`test_status.py:70-113`)只複製 `gate.py` 與 `pipeline-stages.yaml`。status 若經 `<root>/.claude/hooks/redlight.py` 讀,測試的 root 就得多複製該檔;若經 gate 讀,gate.py 要改。**不先定入口,測試不知道要造什麼 root。**這只決定「從哪個模組呼叫」,不決定 Q1/Q2。 |
| B-2-2 | **570/571 補件的形式**(需裁事項第 2 件) | 指令要求補件內容逐字列出、且補完在現行 HEAD 仍為綠。補件透過 `record_session()` ⇒ HEAD 下該函式不存在 ⇒ 不加守衛就紅。手寫 JSON ⇒ 等於現在就裁 Q1/Q2。兩條路都要裁決者選。 |

---

## 二、觀察介面

紅燈測試只在下列輸出上斷言。**全部屬於一、A 的範圍**;沒有任何一條讀實體帳本格式(歷史原始紀錄是輸入,不是觀察對象)。

### 既有介面

| 介面 | 用途 |
|---|---|
| `status.render(root) -> str` 的 `tests red under ticket N:` / `tests green under ticket N:` / `test-runs:` 三行 | RL-6、RL-6b(舊寫入版)、RL-7 的行為紅 |
| `tests/conftest.py` 的 `pytest_collectreport(report)`、`pytest_runtest_logreport(report)`、`pytest_sessionfinish(session, exitstatus)` | producer 側紅燈的驅動入口(沿用 `test_redlight.py:176-182` 載入 conftest 的手法) |
| `redlight.record_run(test_file, passed, failed_tests)` | RL-6b(舊寫入版)以既有寫入函式造舊格式紀錄 |
| `status._latest_per_file(runs, ticket)` | 不改;749 的觀察點 |

### 新增介面(名稱與簽名)

| 介面 | 簽名 | 回傳 |
|---|---|---|
| 寫入 | `redlight.record_session(root, *, run_id=None, time=None, ticket_id=None, exit_code, collected, deselected, outcomes)` | 寫入的 run 事實(dict)。`root` 決定寫到哪個 repo 的帳本;`run_id` / `time` / `ticket_id` 為 `None` 時由函式自取(測試可指定以求決定性) |
| 讀取 | `redlight.load_runs(root)` | run 事實 list(時間序);無資料回 `[]`;讀不動不拋例外(回 `[]` 並由 status 印「不可判定」) |
| 狀態 | `redlight.run_state(run)` | `"A"`–`"F"`(對照表見一、A-4) |
| 判定 | `status.ticket_test_state(records, runs, ticket)` | 見一、A-7 |
| 輸出 | `status.render()` 新增 `tests green (run 事實未知) under ticket N:`、`tests orphaned under ticket N:` 兩行;`test-runs:` 尾段改寫 | 見一、A-7 |

producer 側的驅動輔助(只在測試檔內,不是產品介面):`_drive_session(c, collected, deselected, reports, exitstatus)` —— 依 pytest 的實際呼叫順序,對 conftest 模組呼叫標準 hook 名稱;conftest 沒實作的 hook 以 no-op 跳過。**測試不依賴 conftest 用了哪幾個 hook**(那是 B)。

---

## 三、逐條紅燈設計

### 共同手法與安全規矩

- **producer 側**(`tests/test_redlight.py`):沿用 `TestTheRecorderCannotKillTheRunner._conftest()` 載入 conftest。
  ⚠ **conftest 模組在載入時自己載一份 `redlight.py`,其 `RUN_LOG` 指向真實帳本**(`conftest.py:129-133`)。
  每條 producer 紅燈**必須**先 `monkeypatch.setattr(c, "_redlight", redlight)`(本測試檔那一份)、`monkeypatch.setattr(c, "_ROOT", tmp_path)`、並照既有 `log` fixture 把 `redlight.RUN_LOG` / `redlight.ROOT` 指到 `tmp_path`。
  少了任何一個,紅燈測試會把**假紀錄寫進真實帳本** —— 那正是證據隔離要防的事。
- **status 側**(`tests/test_status.py`):沿用 `_make_root()` 造最小 repo;run 事實一律透過 `record_session(root, ...)` 寫入;歷史原始紀錄照 `_write_runs()` 手法寫入(唯一例外)。
- **不另起子行程跑 pytest**;不用 pytester(它會在同一行程內再跑一次 pytest,而本 repo 的 conftest 紀錄器在模組層綁定真實帳本,風險同上)。

### 逐條

| RL | 測試檔 | 測試名稱(擬) | 模擬方式 | 現行 HEAD 下為何失敗 | 分類 |
|---|---|---|---|---|---|
| **RL-1** Full pass | `tests/test_redlight.py` | `TestRunFacts::test_a_full_pass_is_state_a_with_coverage_visible` | `_drive_session`:collected 2 身分、0 deselected、2 個 passed report、exit 0 → `load_runs(tmp)` | `redlight.load_runs` 不存在(`AttributeError`) | 介面紅 |
| **RL-2** One failure | 同上 | `test_one_failure_is_state_b_and_names_the_test` | collected 2、1 passed + 1 failed、exit 1;斷言 `run_state == "B"`、`outcomes` 指名失敗身分 | 同上 | 介面紅 |
| **RL-3** Zero collected | 同上 | `test_zero_collected_is_state_c_and_the_run_is_visible` | collected 0、exit 5;斷言有一筆 run、`run_state == "C"` | 同上。**底層行為缺口**:HEAD 對此情形一筆都不寫(`conftest.py:171-172` 迴圈 0 次),與 E 不可分 | 介面紅 |
| **RL-4(a)** 收集錯誤 | 同上 | `test_a_collection_error_is_state_d` | `pytest_collectreport`(failed)+ exit 2;斷言 `run_state == "D"` | 同上 | 介面紅 |
| **RL-4(b)** invocation 錯誤 | 同上 | `test_a_usage_error_is_state_d_not_green` | 無任何 report、exit 4;斷言 `run_state == "D"`。producer 本身未載入的子情形 → 見 ODC-3 | 同上 | 介面紅 |
| **RL-4(c)** 中斷 | 同上 | `test_an_interrupted_run_is_state_d_even_with_passes` | 1 個 passed report、exit 2;斷言 `run_state == "D"`(有 passed 也不得為 A) | 同上 | 介面紅 |
| **RL-5** No invocation | `tests/test_status.py` | `TestRunEvidence::test_no_run_at_all_is_not_zero_tests_and_not_a_pass` | `_make_root()`,不寫任何 run 事實;另造一個寫入 C 狀態 run 的 root;比對兩者 `test-runs:` 尾段 | 尾段字樣 `最近一次 run:` 不存在;HEAD 兩者都印 `全套結果:未記錄` | 介面紅 |
| **RL-6** 票 139 歷史重現 | `tests/test_status.py` | `TestTicket139::test_a_narrow_all_skip_record_does_not_retire_the_earlier_red` | `_make_root(ticket=u"133")`;以 `_write_runs()` 逐字寫入**帳本第 940 行與第 970 行**(見下);`render()` | HEAD:`_latest_per_file` 取第 970 行(green)⇒ `tests green under ticket 133` 含 `tests/test_gate.py`、`tests red` 為 `(無)` | **行為紅** |
| **RL-6'** 票 139 現場重現 | `tests/test_redlight.py` | `TestRunFacts::test_three_skipped_645_deselected_is_state_f_with_counts` | collected 648 身分(645 deselected + 3 selected)、3 個 skipped report、exit 0;斷言 `run_state == "F"`、deselected 數 645、skipped 數 3 | `load_runs` 不存在 | 介面紅 |
| **RL-6b** 舊寫入版 | `tests/test_status.py` | `TestNarrowSelection::test_a_later_green_without_run_facts_does_not_retire_x` | 以既有 `redlight.record_run()`(`RUN_LOG` 指到 tmp root)寫 X red → 同檔 green;`render()` | HEAD:最新一筆 green ⇒ 該檔在 green、不在 red | **行為紅** |
| **RL-6b** run 事實版 | 同上 | `test_a_narrow_run_that_did_not_select_x_does_not_retire_x` | `record_session` 寫 run1(X failed)→ run2(同檔選 Y、X 在 deselected、Y passed、exit 0);斷言該檔在 red、`unresolved` 含 X、run2 的 deselected 可見 | `record_session` 不存在 | 介面紅 |
| **RL-7** 歷史紀錄 | 同上 | `TestHistoricalRecords::test_old_green_rows_are_shown_as_run_unknown_not_green` | 以 `_write_runs()` 寫入 1 筆既有格式 green 紀錄(取帳本第 2036 行原文,`tests/test_status.py` 的 baseline 紀錄);`ticket=u"145"`;`render()` | HEAD:該檔印在 `tests green under ticket 145`,沒有任何「未知」標記 | **行為紅**(依 I5 判讀:aggregate 的 green 必須可追溯到足以證明其語意的 evidence,而舊紀錄沒有 run 事實) |
| **ODC-2** 孤兒 | 同上 | `TestOrphans::test_a_renamed_red_test_is_orphaned_not_green` | run1:X failed;run2:同檔全選、collected 不含 X(改名為 X2)、X2 passed、exit 0;斷言該檔在 `tests orphaned`、不在 green | `record_session` 不存在 | 介面紅 |
| **ODC-3** producer 未載入 | 同上 | `TestRunEvidence::test_no_producer_means_undecidable_not_green_not_c` | `_make_root()` 有 8 欄紀錄、沒有任何 run 事實;斷言尾段為 `無 run 證據 / 不可判定`、不含狀態字母 `C`、該檔不在 `tests green` | 尾段字樣不存在;HEAD 該檔在 green | 介面紅(尾段)+ 行為成分(green);**歸介面紅**,因為失敗的第一個斷言是字樣 |

### RL-6 的因果序列(逐字)

**(1) 造成 unresolved red 的先前紀錄** —— 真實帳本 `.dev/test-runs.jsonl` **第 940 行**(唯讀取得,原文):

```
{"test_file": "tests/test_gate.py", "time": "2026-09-13T07:28:31.037700+00:00", "result": "red", "failed_tests": ["TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce"], "impl_file": ".claude/hooks/gate.py", "impl_exists": true, "impl_hash": "2215f109bb73277248f78a6110a90bf51ec8a5f215251cf6089b86ebbe215170", "ticket_id": "133"}
```

**(2) 造成 false-green aggregate 的窄選紀錄** —— 票 139 `:39` 原文,逐字不改;與真實帳本 **第 970 行**逐字相同:

```
{"test_file": "tests/test_gate.py", "time": "2026-09-13T12:26:18.644697+00:00", "result": "green", "failed_tests": [], "impl_file": ".claude/hooks/gate.py", "impl_exists": true, "impl_hash": "446b2ef6f49fa0608d347d9969b49a0f3fa682d11cfe47b622feaa80cdbb7dc2", "ticket_id": "133"}
```

查找方式(唯讀,`Grep` 工具,pattern `"test_file": "tests/test_gate.py", "time": "2026-09-13`)原始輸出:

```
920:{"test_file": "tests/test_gate.py", "time": "2026-09-13T07:24:49.179969+00:00", "result": "red", "failed_tests": ["TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce"], "impl_file": ".claude/hooks/gate.py", "impl_exists": true, "impl_hash": "2215f109bb73277248f78a6110a90bf51ec8a5f215251cf6089b86ebbe215170", "ticket_id": "133"}
922:{"test_file": "tests/test_gate.py", "time": "2026-09-13T07:26:01.174004+00:00", "result": "red", "failed_tests": ["TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce"], "impl_file": ".claude/hooks/gate.py", "impl_exists": true, "impl_hash": "2215f109bb73277248f78a6110a90bf51ec8a5f215251cf6089b86ebbe215170", "ticket_id": "133"}
940:{"test_file": "tests/test_gate.py", "time": "2026-09-13T07:28:31.037700+00:00", "result": "red", "failed_tests": ["TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce"], "impl_file": ".claude/hooks/gate.py", "impl_exists": true, "impl_hash": "2215f109bb73277248f78a6110a90bf51ec8a5f215251cf6089b86ebbe215170", "ticket_id": "133"}
970:{"test_file": "tests/test_gate.py", "time": "2026-09-13T12:26:18.644697+00:00", "result": "green", "failed_tests": [], "impl_file": ".claude/hooks/gate.py", "impl_exists": true, "impl_hash": "446b2ef6f49fa0608d347d9969b49a0f3fa682d11cfe47b622feaa80cdbb7dc2", "ticket_id": "133"}
```

- **選第 940 行的理由**:它是第 970 行之前、同一 `test_file` 的最後一筆 red;最小序列只需兩筆。
- ⚠ **哪一筆來自票 139 所說的「全套執行(`1 failed`)」,帳本本身判不出來** —— 920 / 922 / 940 三筆欄位結構相同,沒有任何涵蓋範圍欄位(這正是本票要修的缺口)。本規劃**不宣稱** 940 就是那次全套執行;它只需要是「第 970 行之前仍未退紅的那條 red」,而這一點由帳本順序直接成立。
- **無 synthetic 資料**;**未改寫任何歷史 row**。
- **為何是行為紅**(由原始碼推得,**未執行**):`render()` → `_derived()`(`status.py:779-816`)→ `_latest_per_file(runs, "133")`(`:312-334`)以 `out[f] = rec` 逐筆覆蓋,`tests/test_gate.py` 最後留下第 970 行(`result: "green"`)⇒ `greens` 含它、`reds` 為空 ⇒ 輸出 `tests red under ticket 133: (無)`。測試斷言 `tests/test_gate.py` **不在** green、**在** red ⇒ HEAD 下第一個斷言即失敗,而且**不經過任何新介面**。第 3 站全套跑時以實際輸出驗證此推論。
- 修後預期:第 970 行沒有對應 run(A-5)⇒ coverage 未知 ⇒ 無退紅權(ODC-1)⇒ 第 940 行那個身分未退紅 ⇒ `tests/test_gate.py` 為 `red`。

### RL-7 用的歷史紀錄(逐字)

帳本**第 2036 行**(Station 3 baseline 寫入,原文):

```
{"test_file": "tests/test_status.py", "time": "2026-10-02T13:27:56.450055+00:00", "result": "green", "failed_tests": [], "impl_file": ".claude/portable/status.py", "impl_exists": true, "impl_hash": "bdc3a089a33d179dc72eb937401520c5ec257ba11037fb42083420a9560fadf0", "ticket_id": "145"}
```

選它的理由:它是一筆**真實**、**最新**、**來自一次確實全套通過的執行**的 green —— 而帳本仍無法證明這件事(`status.py` 當時印「全套結果:未記錄(帳本不記全套)」)。修後它必須落在 `run 事實未知`,**即使它事實上來自全套通過**:Backward compatibility 2 禁止推論。

---

## 四、既有測試的影響清單

依一、A 契約實作後,結果會改變的既有斷言:

| nodeid | 行號 | 原文 | 改變原因 |
|---|---|---|---|
| `tests/test_status.py::TestTestsUnderTicketUsesTheLatestRecordPerFile::test_a_file_that_went_red_then_green_counts_as_green` | 570 | `assert u"tests/test_a.py" not in red, red` | fixture(`:554-561`)的 test_a 綠燈列沒有對應 run ⇒ coverage 未知 ⇒ 無退紅權 ⇒ test_a 仍為 red ⇒ 斷言失敗 |
| 同上 | 571 | `assert u"tests/test_a.py" in green, green` | 同上;test_a 不在 green(會落在 red) |

**不受影響**(已逐條檢查):

| nodeid | 行號 | 原文 | 不變的理由 |
|---|---|---|---|
| 同上 | 572 | `assert u"tests/test_b.py" in red, red` | test_b 只有一筆 red,新規則下仍 red |
| `tests/test_status.py::TestLatestPerFileIsFailClosedWithoutTicket::test_with_ticket_still_filters` | 749 | `assert got["tests/test_a.py"]["result"] == "green", got["tests/test_a.py"]` | 直接呼叫 `_latest_per_file`,而一、A-7 定為**不改**該函式 |
| `…::TestLatestPerFileIsFailClosedWithoutTicket::test_no_ticket_returns_empty` | 741 | `assert status._latest_per_file(TICKET_100_RUNS, None) == {}` | 同上 |
| `…::TestMissingEvidencePrintsUnrecorded::test_missing_ledger_prints_unrecorded` | 165 | `assert _value_of(out, u"test-runs") == UNRECORDED` | 一、A-7:無帳本時整行照舊 `未記錄` |
| `…::TestMissingEvidencePrintsUnrecorded::test_present_ledger_is_not_unrecorded` | 171 | `assert _value_of(out, u"test-runs") != UNRECORDED` | 有帳本時不印 `未記錄` |
| `…::TestIdleTestRunsLineIsUnrecorded::test_idle_prints_unrecorded_not_this_ticket` | 725 / 728 | `assert val.startswith(UNRECORDED), val` / `assert u"本票" not in val, val` | 一、A-7:無當前票時照舊 |
| `tests/test_redlight.py::TestTheRecorderCannotKillTheRunner` 三條 | 197-199 / 216-218 / 226-228 | (見檔案) | 前提:producer 以 `getattr` 預設值讀 report 屬性(一、B-1 約束 4) |
| `tests/test_gate.py` 中讀 `RUN_LOG` 的 R3 測試(17 處引用) | —— | —— | 前提:第 4 站的 Q1/Q2 守住一、B-1 約束 1(R3 解析) |

### 570 / 571 的 fixture 補件(逐字,依需裁事項第 2 件的選項 A)

補在 `test_a_file_that_went_red_then_green_counts_as_green` 寫完 `recs` 之後、`render(root)` 之前:

```
    if hasattr(redlight, "record_session"):
        redlight.record_session(
            root,
            run_id=u"fixture-570-571",
            time=u"2026-09-02T02:00:00+00:00",
            ticket_id=u"99",
            exit_code=0,
            collected=[u"tests/test_a.py::test_one"],
            deselected=[],
            outcomes={u"tests/test_a.py::test_one": u"passed"},
        )
```

另需兩處測試基礎設施(**不是** run-level facts,故列為需裁):

1. `tests/test_status.py` 模組層載入 `redlight`(照 `tests/test_redlight.py:22-30` 的 `_load()` 手法)。
2. 若需裁事項第 1 件選 (i):`_make_root()` 多一行 `shutil.copy2(str(ROOT / ".claude" / "hooks" / "redlight.py"), str(root / ".claude" / "hooks" / "redlight.py"))`。

**這份補件的語意**:test_a 的紅燈列沒有 `failed_tests`(身分不明)⇒ 依需裁事項第 3 件,退紅須該檔每個 collected 身分都執行且通過 ⇒ 補一個「test_a 全檔只有 `test_one`、它通過、無 deselected、run 無 failure、exit 0」的 run,時間與原 green 列相同。補完後 test_a 退紅 ⇒ 570、571 恢復成立;572 不受影響。

**補完後在現行 HEAD 下仍為綠嗎**:是,但理由要寫清楚 —— HEAD 沒有 `record_session`,`hasattr` 為假,**補件不執行**,斷言照舊依 `_latest_per_file` 成立。⚠ 這只證明「補件不會讓 HEAD 變紅」,**不證明補件內容正確**;補件的效力要到第 4 站實作後才被這兩條斷言實際檢驗。
若補件在第 4 站因函式改名而靜默不執行:新規則會讓 test_a 為 red ⇒ 570 / 571 失敗 ⇒ **會出聲**,不會靜默綠。

**是否有任何一條必須改斷言語意**:**沒有**。全部可只靠補 fixture 處理 —— 前提是需裁事項第 1、2、3 件照建議裁定。

---

## 五、第 4 站會動到的檔案與 enforcement residual

### 逐檔

判準原文:`gate.is_source_path()`(`gate.py:2188-2195`)—— `top in NON_SOURCE_DIRS` 等四條任一成立即**不是**原始碼;`NON_SOURCE_DIRS`(`gate.py:272-287`)含 `"tests": "測試自身,受測試執行器消費但不是產品原始碼(R3 的對象是被測物)"`,**不含** `.claude`。
R3 豁免清單:`.agents/legacy-no-redlight.txt`(9 筆,全檔已讀)。

| 路徑 | 是否原始碼 | R2 | R3 | R3 需要的紅燈紀錄 |
|---|---|---|---|---|
| `.claude/portable/status.py` | 是(`.claude` 不在 `NON_SOURCE_DIRS`) | 管(須 `implement`) | **管**(不在豁免清單) | `tests/test_status.py` 的一筆 red,`ticket_id == "145"`,且 `impl_hash` == status.py 在 HEAD 的內容雜湊 —— 第 3 站全套紅燈跑會產生 |
| `.claude/hooks/redlight.py` | 是 | 管 | **整條豁免**(清單第 2 筆:`.claude/hooks/redlight.py`) | 不需要 —— **R3 不檢查** |
| `tests/conftest.py` | **否**(`tests` 在 `NON_SOURCE_DIRS`) | **不管** | **不管** | —— |
| `tests/test_redlight.py`、`tests/test_status.py` | 否 | 不管 | 不管 | —— |
| `.claude/hooks/gate.py` | 是 | `GATE_SELF`(`gate.py:227`)R2 豁免並記帳 | **整條豁免**(清單第 1 筆) | 不需要 —— **R3 不檢查**。只有在需裁事項第 1 件選 (iii),或 Q1 選同檔而需讓 R3 跳過新紀錄時,才會動到 |

### enforcement residual(正式登記)

> tests/conftest.py 是 M1-a 的 evidence producer,但被 NON_SOURCE_DIRS 排除,R2 / R3 無法結構性阻止它在錯誤 station 被修改。Station 3 目前只靠 tracked allowlist + final staged diff 守住,這不是結構保證。

**同性質的第二筆**(本輪讀碼新發現):

> `.claude/hooks/redlight.py` 是 M1-a evidence 的寫入函式所在,但列在 `.agents/legacy-no-redlight.txt`,R3 對它整條豁免 —— 第 4 站修改它時,閘門**不要求**先有紅燈紀錄。R2 仍管(須 `implement`)。

⇒ M1-a 的兩個 producer 檔,**沒有一個受 R3 的「紅燈先行」結構約束**;受約束的只有 consumer(`status.py`)。

### conftest.py 缺口:(a) 本票處理,還是 (b) 另開框架票?

**建議 (b) 另開框架票。**

1. **修法不屬於 run-evidence 語意**:要讓 conftest.py 受 R2 / R3 管,得改 `NON_SOURCE_DIRS` 的分類或加例外 —— 那是閘門邊界,屬 `CLAUDE.md`「任何要進非原始碼清單的目錄,先問它會不會裝著判定邏輯 / 唯一的觀測」那一族,不是本票〈三〉的任何一條 REQUIREMENT。
2. **它對所有下游都成立**:每個安裝的 repo 都有同一支 conftest 紀錄器住在 `tests/`;用「這一則搬到另一個專案還成立嗎」判準 ⇒ 成立 ⇒ 框架層。
3. **在本票內改會讓本票的閘門條件在途中變動**:第 3、4 站正依賴現行 R2 / R3 行為;中途改分類,本票自己的紅燈與實作會在兩套規則下各走一半。
4. 本票內的補償控制(不是結構保證):第 3 站紅燈 commit 的 staged diff 只准出現 `tests/test_redlight.py`、`tests/test_status.py` 與報告;`tests/conftest.py` 出現即停。

redlight.py 的豁免則有本票內可用的低成本處置 —— 見需裁事項第 6 件(乙)。

---

## 六、證明方式與推送政策

### 證明方式

- 紅燈證明**一律**用票 145〈十二〉的固定指令,從 repo 根目錄全套跑:

```
python -X utf8 -m pytest -q
```

- 不得以 `-k`、檔案參數、`--deselect` 或其他指令證明(那正是本票要修的 false-green 形狀)。

### 預期全套結果(第 3 站紅燈 commit 之後、第 4 站之前)

| 類別 | 預期 |
|---|---|
| exit code | **1**(有測試失敗) |
| 新測試 | 上表 14 支**全部失敗**(行為紅 3 支、介面紅 11 支) |
| 既有測試 | **全部通過**,含 570 / 571 / 572 / 741 / 749(570/571 的補件在 HEAD 下不執行) |
| baseline 對照 | baseline 為 `1912 passed, 3 skipped, 3 xfailed`;紅燈 commit 後應為 `1912 passed, 3 skipped, 3 xfailed` 加上 14 failed(若既有測試的計數有任何變動 ⇒ 停手回報) |
| 帳本 | 新增列數 = 本次執行的測試檔數;`tests/test_redlight.py` 與 `tests/test_status.py` 兩筆為 `red`、`ticket_id == "145"`;**不得出現任何假檔名**(如 `tests/test_thing.py`)—— 出現代表 producer 紅燈的隔離漏了,假紀錄寫進了真實帳本 |

### 推送政策

**紅燈 commit 不推,直到第 4 站全套全綠。** 理由:CI 會跑同一批測試(`tests.yml:73-75`),紅燈 commit 推上去會讓 CI 紅;而 CI 紅與「真的壞了」在輸出上一樣。

---

## 尚未證明 / 本輪未做

1. **RL-6 / RL-6b(舊寫入版)/ RL-7 是行為紅**:由原始碼推得,**未執行**;第 3 站全套跑時以實際輸出驗證。
2. **RL-6 的第 940 行是否就是票 139 所說的那次全套執行**:帳本判不出來,本規劃不宣稱。
3. **producer 側的 fake 驅動與真實 pytest 的一致性**:`_drive_session` 依 pytest 的 hook 呼叫順序模擬;fake 物件缺少 producer 實際會讀的屬性時,測試可能因錯的理由紅或綠。第 4 站實作後,以固定指令全套跑一次、看真實帳本長出的 run 事實,作為端對端補驗。
4. **需裁事項 6 件**未裁。
5. `_ticket()` direct probe 的 residual(Station 2)仍在,本輪未處理。

---

## 六站狀態

| 站 | 狀態 |
|---|---|
| Station 1 — Spec | PASS / CLOSED |
| Station 2 — Ticket | DONE |
| Station 3 — Red-light | IN PROGRESS(baseline 已量;紅燈規劃完成,待裁;紅燈未寫) |
| Station 4 — Implementation | NOT STARTED |
| Station 5 — Review | NOT STARTED |
| Station 6 — Acceptance | NOT STARTED |
