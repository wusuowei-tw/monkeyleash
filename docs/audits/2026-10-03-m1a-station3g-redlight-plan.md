# 票 145 Station 3g-0 —— 紅燈規劃:框架 self-test 錯置 + downstream evidence-policy 可移植性

- 日期:2026-10-03
- BASELINE:`faf7cb47823e33b65c2a21ffd85db3dd416adea1`(S6-1;相對 S5f-1 `de36ebcbab284ef11064a9943b5191750482dd93` 只改了票 145)。
  下文 `<BASELINE>:<路徑>:<行號>` 都指這個 commit 的樹。
- 依據:票 145〈四十六〉46.4 的 Jeff 裁決第 1–6 點(以下稱「裁決 n」)。
- 範圍:**只規劃**。沒有寫測試、沒有改 .py、沒有跑 pytest,也沒有執行 `verify_gates.py`。
  本檔所有「預測紅 / 綠」都是**靜態推論**,沒有實測。

---

## P1 宿主特定假設盤點

三類定義依裁決 3:
- **I**:Framework invariant,所有安裝都必須一致。
- **B**:Framework capability boundary,框架實際盤點、驗證到哪裡。
- **H**:Host evidence policy,宿主在 B 之內自己選擇接受哪些已提交設定。

「淨室行為」欄依兩個來源:`.claude/portable/install.py` 的安裝流程(下游有什麼、沒有什麼),以及〈四十六〉46.3 的外部重現。

| # | 常數 / 判定 | 位置 | 現行值 | 分類 | 淨室安裝 repo 的現行行為 |
|---|---|---|---|---|---|
| 1 | `COMMITTED_ADDOPTS_OVERRIDES` | `<BASELINE>:.claude/hooks/redlight.py:491-493`;判定 `:795-796` | `("strict_markers=true",)` | **H**:它是 agent-gates 自己 `pyproject.toml:72` `addopts = "-ra --strict-markers"` 的推導結果。「addopts → override 清單」的**推導規則**屬 B(pytest 9.1.1 的盤點) | 淨室 repo 沒有 `pyproject.toml`(manifest `<BASELINE>:.agents/portable-manifest.txt:69` 標 `skip`)⇒ `override_ini` 為 None(46.3)⇒ `None != ["strict_markers=true"]` ⇒ **unknown**。下游即使自備 pyproject,只要 addopts 不同也永遠 unknown |
| 2 | `CONFIG_FILE` / `inipath == "pyproject.toml"` | `redlight.py:495-496`;判定 `:799-800` | `"pyproject.toml"` | 拆成兩半:「可接受哪些設定檔**型態**」屬 **B**(P1 的盤點只做過 pyproject 的 `[tool.pytest.ini_options]`);「這個宿主用哪一個」屬 **H** | 淨室 `inipath` 為 None(46.3)⇒ `None != "pyproject.toml"` ⇒ **unknown** |
| 3 | `COMMITTED_FILES` / `config_blobs` 路徑清單 | `redlight.py:497`;取值 `:686-703`;判定 `:801-804` | `("pyproject.toml", "tests/conftest.py")` | 拆成兩半:`tests/conftest.py` 這一項屬 **I**(producer 本身,manifest `:119` 標 `copy`,每個安裝都有);`pyproject.toml` 這一項屬 **H**(宿主的設定檔) | 兩檔 worktree / head 皆為 None(46.3)。**靜態推論**:`committed_blobs` 用**同一次** `git hash-object` 處理全部路徑(`:696`),所以缺一個檔,整次呼叫失敗、所有路徑都是 None ⇒ conftest 的 blob 也一起遺失 ⇒ **unknown** |
| 4 | `KNOWN_DISTS` | `redlight.py:485-486`;使用 `:613` | `(("anyio", "4.15.0"),)` | **B**:框架盤點過的第三方 plugin。宿主只能再收窄(H) | 下游若沒有裝 anyio ⇒ 沒有 dist 配對,不影響判定;若裝了其他 plugin ⇒ `other` ⇒ unknown。這是**正確的** fail-closed |
| 5 | `KNOWN_PYTHON_VERSIONS` | `redlight.py:476-477`;判定 `:808-809` | `("3.11",)` | **B** | 淨室在 CI 上是 3.11(`<BASELINE>:.github/workflows/tests.yml:47`),這一條成立;下游若用其他版本 ⇒ unknown(正確) |
| 6 | `KNOWN_PYTEST_VERSIONS` | `redlight.py:488-489`;判定 `:793-794` | `("9.1.1",)` | **B** | 淨室是 9.1.1(46.3),這一條成立;其他版本 ⇒ unknown(正確) |
| 7 | `COMPLETENESS_OPTIONS` 與 (ii)–(vi)、(xiv)–(xix) | `redlight.py:462-467`;判定 `:810-832` | — | **B**:pytest 9.1.1 的 CLI 盤點 | 與宿主無關,淨室行為與 agent-gates 相同 |
| 8 | `ROOT_CONFTEST = "tests/conftest.py"`、`SUPPORTED_PLUGIN_KINDS`、`BUILTIN_MODULE`、`EXECUTED_OUTCOMES` | `redlight.py:469-472`、`:501` | — | **I** | 安裝器照抄 `tests/conftest.py`(manifest `:119`),所以淨室成立 |
| 9 | `_ROOT`(producer 的 repo 根) | `<BASELINE>:tests/conftest.py:130`(`parents[1]`);redlight 端 `redlight.py:42-43`(`ROOT` 由 `__file__` 推出,帳本在 `<ROOT>/.dev/`) | — | **I**:框架佈局,即 `tests/conftest.py` 與 `.claude/hooks/redlight.py` 的相對位置 | 淨室成立;帳本寫在淨室 repo 自己的 `.dev/` |
| 10 | 固定指令 / testpaths 的假設 | 判定 `redlight.py:412-414`、`:431-447`(**通用**的位置參數規則,沒有寫死 `tests`);測試註解 `<BASELINE>:tests/test_redlight.py:603-610` 引 `pyproject.toml:71` `testpaths = ["tests"]` | — | 分三部分:判定本身屬 **I**,沒有宿主假設。`testpaths` 的值屬 **H**,已被 #3 的 blob 一致性涵蓋。「固定指令 `python -X utf8 -m pytest -q`」不是判定的輸入,只是程序約定 | 判定與宿主無關。但若下游的測試不在 `tests/` 底下,`tests/conftest.py` 不會被載入 ⇒ 不產生 session ⇒ 沒有證據。這屬 I 的佈局前提,本票不處理(列 P7) |
| 11 | `status.py` 對 redlight 的依賴 | `<BASELINE>:.claude/portable/status.py:355-374`(依 root 載入 `<root>/.claude/hooks/redlight.py`);`:456`(只在 `file_coverage == "true"` 時退紅) | — | **I** | status 本身沒有宿主常數;淨室的 unknown 全部來自 redlight 的 #1–#3 |
| 12 | `SYNC_WATCHED` | `status.py:76-80` | 三個框架檔 | **I** | 與本題無關,列出只是為了盤點完整 |

**小結(第二層的成因)**:淨室 repo 的 unknown 有三個**各自獨立**的來源 —— #1 (viii)、#2 (x)、#3 (xi)。
三個都是把 agent-gates 的宿主事實(H)寫成了框架常數。只修其中一個,固定全套仍然是 unknown。

---

## P2 框架 self-test 錯置盤點

**方法**:
- Grep `tests/`,關鍵字為 `HEAD:`、`git -C str(ROOT)`、`cwd=str(ROOT)`、`pyproject.toml`、`test-runs.jsonl` / `test-sessions.jsonl`、`__version__` / `version_info`。
- 只分類**出貨**(manifest 標 `copy`)的測試檔。標 `skip` 的檔不會到下游。
- 已知事實:淨室 CI 只有 1 支紅(46.2)。⇒ 其餘命中**在 CI 的淨室環境**(Linux + 3.11 + pytest 9.1.1)都是綠的。

### P2-A 讀宿主 repo 事實的測試

| 測試 | 位置 | 讀什麼 | 分類 |
|---|---|---|---|
| `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d4_the_committed_addopts_override_constant_matches_pyproject` | `<BASELINE>:tests/test_redlight.py:1489-1534`(`git -C ROOT show HEAD:pyproject.toml` 在 `:1511-1513`) | 宿主已提交的 `pyproject.toml` | **錯置**:應改為斷言框架性質(以 fixture 驗證),另把宿主鎖步移為 host-policy 檢查。見下方「test_d4 與〈三十一〉裁決 3」 |
| `tests/test_gate.py::…::test_cache_dir_is_ignored_by_version_control` | `<BASELINE>:tests/test_gate.py:714-723` | 宿主的 `git check-ignore` | **無問題**:斷言的是安裝器寫進 `.gitignore` 的結果,即安裝後的框架不變式(I) |
| `tests/test_gate.py::…::test_every_entry_existed_in_the_go_live_commit` | `tests/test_gate.py:860-871` | 宿主的豁免清單與 go-live 樹 | **無問題**:清單由安裝器 `generate`(manifest `:115`),是框架不變式 |
| `tests/test_gate.py::…::test_the_real_list_is_the_generator_output_minus_drained` | `tests/test_gate.py:6511-6533` | 同上 | **無問題**(同上) |
| `tests/test_leak_scan.py` 的發布來源掃描(`git ls-files` 掃整棵宿主樹) | `<BASELINE>:tests/test_leak_scan.py:300-316` | 宿主樹的全部追蹤檔 | **刻意斷言宿主狀態**(host-policy 性質的檢查),而且是出貨的。不屬本票的 evidence policy,本票不處理(列 P7) |
| `tests/test_evidence_isolation.py::test_a_blocked_judgement_does_not_touch_host_evidence` | `<BASELINE>:tests/test_evidence_isolation.py:99-111`(`:107` 要求宿主 `.dev/*.jsonl` 存在) | 宿主 `.dev/` 證據檔 | **無問題**:`.dev/` 由安裝器 `generate`(manifest `:116`),淨室 CI 也是綠 |
| 其他 `HEAD:` / `pyproject.toml` 命中(`test_redlight.py`、`test_status.py`、`test_gate.py`) | 例:`test_redlight.py:1143-1154` `_d_committed_root`、`test_status.py:2370-2382` `_t_committed`、`test_gate.py:1511-1524`、`:3338-3350` | 全部是 **tmp 目錄裡自建的 git repo** | **無問題**。唯一的例外是 `_d_committed_root` / `_t_committed` 會讀 `ROOT/tests/conftest.py`(`test_redlight.py:1148`、`test_status.py:2376`),而那是框架 copy 檔(I) |

**連帶影響**:〈四十五〉45.3 第 3 點的「logging 鎖步絆線待辦」原文寫「做法同 D4」,也就是讀 `git show HEAD:pyproject.toml`。
它若照原文寫進出貨的測試檔,在淨室**同樣必紅**。⇒ 實作時必須放進宿主專用、manifest 標 `skip` 的檔(與 P8-4 同一個處置)。

### P2-B 執行環境相依的正控(新發現,不是讀宿主 repo,而是讀**執行它的環境**)

下列測試斷言 `file_coverage == "true"` 或「退紅成立」,而且都透過**真實的** `tests/conftest.py` producer 產生事實。

producer 在呼叫當下讀兩個值:
- 真實的 `pytest.__version__`:`<BASELINE>:tests/conftest.py:366`
- 真實的 `sys.version_info`:`:329-335`

既有 driver **沒有**釘住這兩個值:
- `test_redlight.py:1598`、`test_status.py:2617`:`version_info` 為 None 時沿用真實版本。
- 只有破壞組會 monkeypatch,例如 `test_redlight.py:1409`、`:1714`。

⇒ 這些正控**只在 Python 3.11 + pytest 9.1.1 的環境才綠**。下游若用 3.12 或其他 pytest 版本,框架測試會出現與下游無關的紅,與裁決 3 (a) 及 `verify_gates.py:376-379` 的註解原意衝突。
CI 的淨室剛好是 3.11 + 9.1.1,所以沒有現形。

Grep 命中(`assert … == "true"` 與 `retires_the_red` 類):

| 檔 | 命中 |
|---|---|
| `tests/test_redlight.py` | 22 個斷言行:`:540`、`:558`、`:660`、`:1072`、`:1434`、`:1446`、`:1458`、`:1487`、`:1650`、`:1662`、`:1675`、`:1688`、`:1700`、`:1715`、`:1757`、`:1768`、`:1939`、`:1957`、`:1988`、`:2001`、`:2035`、`:2036` |
| `tests/test_status.py` | 6 個測試定義(`:1733`、`:2214`、`:2558`、`:2718`、`:2816`、`:2843`)+ 1 個斷言行(`:2328`) |

**每一行是否都經真實 producer 讀版本,未逐支驗證**(列 P7)。

分類:**應改為斷言框架性質**,在共用 driver 以 fixture 固定版本事實。是否在 3g 一併處理,列 P8-5。

### test_d4 與〈三十一〉裁決 3 的關係

〈三十一〉裁決 3(`<BASELINE>:docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md:1672-1682`)規定:
- 讀取來源固定為「agent-gates repo 的已提交版本」(`git show HEAD:pyproject.toml`)。
- 不得以 tmp repo 或寫死的字串代替。
- **git 讀取失敗 ⇒ 失敗、不得 skip**。

**這三條本身沒有錯**。它們要鎖的是「redlight 常數 ↔ 這個 repo 真正提交的設定」,用自造設定確實只會驗到測試自己。
錯在**位置**:這支測試放在出貨的 `tests/test_redlight.py`(manifest `:127` 標 `copy`)。下游執行時,`HEAD` 是下游的 HEAD,
「agent-gates repo 的已提交版本」這個前提在那裡不存在。於是「不得 skip」把一個與下游無關的前提變成了必紅。
這是 manifest 檔頭與 `:267-271` 已記錄過的「帶走測試卻不帶走它讀的檔案 = 到站即紅」同一個形狀。

**建議處置**(P8-4 建議 C):
1. 把 `COMMITTED_ADDOPTS_OVERRIDES` 從框架常數移進宿主 policy(P3)。
2. 「addopts → override 清單」的推導,改寫成框架函式,並在 verdict 時拿它對照**已提交設定 blob**做機器檢查。
   這樣鎖步由機制執行,不再依賴一支測試。
   框架這一側以 fixture 測推導函式本身(P6 的 TestAddoptsDerivation)。〈三十一〉裁決 3 禁用 tmp repo 的理由不適用於此:
   這裡驗的是**推導規則**,不是「常數 ↔ 宿主設定」。
3. agent-gates 自己的「policy ↔ pyproject」鎖步,搬到宿主專用檔 `tests/test_host_evidence_policy.py`(manifest 標 `skip`),
   **原樣保留**〈三十一〉裁決 3 的「git show HEAD、不得 skip、唯讀」。
4. 原 test_d4 在 4g 刪除。這需要 Jeff 明文修訂〈三十一〉裁決 3 的**適用位置**(只改位置,不改語意)。
   **絕不能改成「找不到就 skip」**:票 16 指出,測試從 pass 轉成 skip 不會有任何東西出聲。

---

## P3 Host evidence policy 設計

### 共同不變式(兩案皆同;屬 I,寫在 redlight.py,不可由 policy 指定)

**I-1 canonical location**:`POLICY_FILE` 是框架常數(兩案各自的值見下)。policy 內容**不得**含任何指定位置、路徑、include 或 extends 的鍵。

**I-2 schema bootstrap**:框架常數列出認得的 `(schema id, version)` 組合。不在清單內 ⇒ unknown。policy 不能宣告自己用哪一套解析規則。

**I-3 bootstrap 順序**(producer 在 sessionfinish 執行;任一步失敗 ⇒ 記 None,consumer 判 unknown):
1. 固定 canonical path(`POLICY_FILE`)。
2. 用 `git rev-parse HEAD:<POLICY_FILE>` 確認檔案存在於 HEAD。否 ⇒ unknown(狀態「未初始化」)。
3. 取得 HEAD committed blob sha(同上一步的輸出)。
4. 用 `git hash-object <POLICY_FILE>`(套用 .gitattributes 正規化,與 `committed_blobs` 同一手法)取得 worktree blob,確認與 HEAD blob 相等。
   不相等、worktree 缺檔 ⇒ unknown。
   - worktree 被改:對應負二。
   - worktree 被刪:同屬負二家族。
   - 只 staged:第 2 步已失敗。
   - 只在 worktree:第 2 步已失敗,對應負三。
5. 用 `git cat-file blob <HEAD blob sha>` 取得內容,解析 schema、version 與 policy 內容。未知、格式錯、多鍵或缺鍵 ⇒ unknown。
   **內容只從這個 blob 來**;第 4 步的 worktree 檔**只用於 identity 比對,之後不再讀取**。
6. 之後才與 runtime environment 比對:
   - 先算 `effective = boundary ∩ policy`;
   - 再要求每一項 runtime 事實都屬於 effective。

**I-4 收窄不擴張**:每個 policy 欄位都必須是 B 常數的子集。界外值怎麼處理見 P8-3:
- 建議:整份 policy 不合格 ⇒ unknown。
- 替代:取交集。

**I-5 缺 policy 不是可信**:沒有 policy、未提交、不一致、看不懂 ⇒ 一律 unknown。不得退回「沿用框架預設值」—— 那正是本票要拆掉的狀態。

### 甲案(建議):獨立 JSON 檔 `.agents/evidence-policy.json`

格式與欄位(schema v1;所有欄位必填;不得有多餘鍵):

```json
{
  "schema": "monkeyleash.evidence-policy",
  "version": 1,
  "config_file": "pyproject.toml",
  "committed_overrides": ["strict_markers=true"],
  "python_versions": ["3.11"],
  "pytest_versions": ["9.1.1"],
  "dists": [["anyio", "4.15.0"]]
}
```

| 欄位 | 語意 | 能力邊界(B 常數) | 與 runtime 比對 |
|---|---|---|---|
| `config_file` | 宿主採用的 pytest 設定檔(root 相對路徑) | `FRAMEWORK_CONFIG_FILES = ("pyproject.toml",)` | `inipath == config_file`;`inifilename is None`(ix 不變);該檔的 worktree blob == HEAD blob(xi 的宿主那一半) |
| `committed_overrides` | 宿主接受的、由已提交 addopts 帶來的 override 清單 | 推導規則(`addopts_overrides(text)`,pytest 9.1.1 盤點) | 兩項都要成立:(a) `== addopts_overrides(HEAD:<config_file> 的 [tool.pytest.ini_options].addopts)`,這是 policy 自洽的機器鎖步,取代 test_d4;(b) runtime `override_ini == committed_overrides`(viii) |
| `python_versions` | 宿主接受的 Python major.minor | ⊆ `KNOWN_PYTHON_VERSIONS` | runtime 屬於 effective(xviii) |
| `pytest_versions` | 宿主接受的 pytest 版本 | ⊆ `KNOWN_PYTEST_VERSIONS` | (xiii) |
| `dists` | 宿主接受的第三方 plugin(名稱與精確版本) | ⊆ `KNOWN_DISTS` | `known_dist` 改為「(名, 版本) ∈ effective」(vii′) |

- **為什麼用 JSON**:`json` 是標準庫,能力邊界外的 Python 版本也解析得了,producer 不必依賴 `tomllib`(3.11 起才有)。
- `config_file` 的 TOML 解析只在 (a) 用到,而能力邊界目前只有 3.11,屬 `tomllib` 可用的範圍;邊界外反正是 unknown。
- **為什麼放 `.agents/`**:它與 `pipeline-stages.yaml` 同一層,都是流程定義。manifest 要明列 `.agents/evidence-policy.json skip`:
  上游自己那一份描述的是 agent-gates,絕不能被抄到下游(P4)。

### 乙案:寫在設定檔裡,`pyproject.toml` 的 `[tool.monkeyleash.evidence-policy]`

- canonical location = 固定的 TOML table。policy 的 integrity 直接沿用 (xi) 的 pyproject blob 比對,不必另做一組 identity check。
- 優點:少一個檔。改設定與改 policy 一定在同一個 commit。
- 缺點:
  1. policy 與「被它管的設定檔」綁在同一份 blob,只要改 pyproject 的任何一行(包括非 pytest 段落),policy 的 identity 就跟著變。
  2. 宿主若選擇其他設定檔型態(將來 B 擴張到 `pytest.ini`),policy 會失去固定位置,違反 I-1。
  3. 解析要 `tomllib`。
  4. 「沒有 pyproject 的 repo」根本沒有地方放 policy。

### 兩案共同:producer / consumer 怎麼讀(P8-2)

- **建議 A**:producer(`tests/conftest.py` 的 `_completeness_of`)依 I-3 讀 policy,在 session 的 `completeness` 新增 `evidence_policy` 欄位:
  `{"path", "head", "worktree", "schema", "version", "policy"}`(`policy` 為從 HEAD blob 解析的內容)。
  consumer(`_completeness_problems` / `_completeness_verdict`)做三件事:驗型別、驗 `head == worktree` 且非 None、驗 schema 與 version;
  然後對 B 常數算交集並比對 runtime 事實。
  - 理由:與既有的 `config_blobs` 同一套「producer 記事實、consumer 判定」模式。
  - 歷史 run 依**當時**的 policy 判定,不會因為之後改 policy 就被重審。
- **B**:consumer 在 status 時依記錄的 blob sha 以 `git cat-file` 重新解析。
  - 好處:不信任 producer 的解析結果。
  - 代價:`file_coverage` 需要 root 與 git,判定變成依賴「status 執行當下的物件庫」。

### fail-closed 一覽

| 情形 | 結果 |
|---|---|
| 缺 policy(HEAD 沒有) | unknown(「未初始化」) |
| worktree 有、HEAD 沒有(負三) | unknown |
| HEAD 有、worktree 不同或缺(負二) | unknown |
| schema / version 未知、JSON 錯、缺鍵或多鍵 | unknown |
| 欄位值超出 B(P8-3) | 建議:unknown |
| policy 與 HEAD 設定檔的 addopts 推導不一致 | unknown |
| runtime 與 effective 不符(負一) | unknown |
| git 不可用 | unknown |

### agent-gates 自身的遷移

1. 提交 `.agents/evidence-policy.json`,內容即上方範例,等於現有常數的值。
2. redlight.py 刪除 `COMMITTED_ADDOPTS_OVERRIDES`。`CONFIG_FILE` 改為 B 常數 `FRAMEWORK_CONFIG_FILES`。
   `KNOWN_*` 三組維持為 B 常數。`COMMITTED_FILES` 拆成兩組:I 的 `ROOT_CONFTEST`,以及由 policy 指定的 `config_file`。
3. `committed_blobs` 改為**逐路徑**呼叫 git,避免 P1 #3 那種「缺一個、全部 None」的連坐。
4. 新增宿主專用測試 `tests/test_host_evidence_policy.py`(skip),繼承 test_d4 的鎖步。

### 版本演進

- 新增 schema 版本時,框架常數列出可接受的 `(schema, version)`。舊版本是否繼續接受,依票裁決。
- 變更 policy 的語意(新增欄位、改比對規則)必須升 version,不得在同一個 version 內改語意。
- 擴張 B(新的 Python、pytest、dist 或設定檔型態)仍須走票重做盤點(沿用〈二十九〉的規則)。
  宿主 policy 只能在 B 擴張**之後**才收得進新值。

---

## P4 初始化流程

**原則**:不得自動信任首次觀察值;**只有**人把檔案放到 canonical path 並 commit,policy 才生效。

- **A(建議)**:
  - 安裝器(`<BASELINE>:.claude/portable/install.py:497-530`)新增一步,把範本寫到**非 canonical** 路徑 `.agents/evidence-policy.template.json`。
    範本內容是**框架 B 常數的完整列舉**,不是觀察值。安裝器 `:516`、`:520` 的 `git add -A` 與 commit 會把範本一起提交,
    但因為它不在 canonical path,**永遠不會被當成 authority**。
  - 同時在 `docs/decisions-pending.md`(`install.py:386-422`)加一項:「evidence policy 未初始化:審閱範本 → 依需要收窄 → 存成 `.agents/evidence-policy.json` → commit」。
  - status 新增一行顯示 policy 狀態(未初始化 / 未提交 / worktree ≠ HEAD / schema 不明 / 有效)。
    沒有這一行的話,第二層「永遠 unknown」對下游仍然是靜默的。
  - 範本與 status 行都由框架產生;**「放進 canonical path 並 commit」只有人做**。
- **B**:另做 `python .claude/portable/evidence_policy.py draft`,從**本機觀察值**產一份草稿到 scratch(不 commit)。
  - 好處:方便。
  - 風險:人很容易不審就照抄,實質上等於信任首次觀察值。

**manifest**:
- `.agents/evidence-policy.json`:標 `skip`(各 repo 自己的檔)。
- `.agents/evidence-policy.template.json`:標 `generate`(由安裝器在目標 repo 產生)。
- 範本來源:放在 `.claude/portable/templates/`(標 `copy`)。

**既有 downstream(已 sync 的 repo)的影響**:
- sync 帶入新 redlight 之後,在下游提交 policy 之前,所有 run 都是 unknown,無法退紅。
- 原本若有剛好吻合的下游(例如 pyproject 照舊範本 `<BASELINE>:.claude/portable/templates/pyproject.toml.template:27`,addopts 與 agent-gates 相同),
  在升級後會從「可能 true」降為 unknown。
- 這是 fail-closed 方向的行為改變,不會假綠,但**會讓已有的退紅能力暫時消失**。
- 遷移步驟:sync 的 dry-run 列出「需建立 evidence policy」→ 人在下游審範本、commit → 之後才恢復。
- sync 端是否要加這一項提示,列 P7(本票先只做 status 行)。

---

## P5 clean-room acceptance 設計

### verify_gates.py 新增的五個情境(裁決 4)

每個情境都在淨室 repo 內進行(`<BASELINE>:.claude/portable/verify_gates.py:287` `target = <workdir>/verify-gates-repo`)。
每個情境用 `run_scenario` 同一套「佈置 → 執行 → `restore`(`:246-269`)」。

| 情境 | 佈置 | 執行 | 驗收 |
|---|---|---|---|
| **正一** Uninitialized | 安裝後不動 | 在淨室 repo 跑框架測試(既有 `:380`) | 框架測試全綠(既有 `:383-390`);**另外**讀淨室帳本最後一筆 session,對一個框架測試檔算 `file_coverage`,必須是 `"unknown"`;status 的 policy 行為「未初始化」 |
| **正二** Initialized + matching | 建立 pyproject(與 `FRAMEWORK_CONFIG_FILES` 相容)+ policy(值 = 當下環境 ∩ B),commit;再提交一支故意失敗的測試檔 | 固定指令跑一次(紅)→ 修好那支測試、commit → 固定指令再跑一次 | 第二次 `file_coverage == "true"`;status 顯示該紅已退休(**端到端**) |
| **負一** policy / environment mismatch | 同正二,但 runtime 多一個 override(`PYTEST_ADDOPTS="-o python_functions=test"`,或任何 policy 未列的值) | 修好後的那一次改在這個環境跑 | `file_coverage == "unknown"`;紅**仍在** |
| **負二** HEAD 有、worktree 不同 | 同正二,但 policy 的 worktree 多一行(未 commit) | 修好後的那一次 | unknown;紅仍在 |
| **負三** worktree 有、HEAD 沒有 | 同正二,但 policy 從未 commit(只在 worktree) | 修好後的那一次 | unknown;紅仍在 |

- 負二、負三在 verify_gates 內可以共用一個參數化的 helper,但輸出必須**各印一行**,不得合併成一行。
- 「固定指令」在淨室內寫成 `[sys.executable, "-X", "utf8", "-m", "pytest", "-q"]`,在淨室 repo 根執行。
- 新增一個常數表 `EVIDENCE_SCENARIOS`(五個鍵),比照 `SCENARIOS`(`:225-235`)的「規則 ↔ 情境」對照。
  由 `tests/test_verify_gates.py` 斷言五個鍵都在(P6 #33)。

### CI 接線

- 沿用 `<BASELINE>:.github/workflows/tests.yml:112-113` 那一步,不另開步驟。五個情境在 `main()` 內接在「框架測試」(`:375-390`)之後。
- 失敗訊息照 `:345-352` 的格式,點名是**哪一個情境**沒有成立。
- `.github/` 標 `skip`(manifest `:83`),只動上游自己的 CI。

### 本機 Station 6 pre-push 的淨室驗證(裁決 5)

**它寫到哪裡**:
- `verify_gates.py:287`:全部產物在 `<workdir>/verify-gates-repo`。
- `:302` `install.main(target)`:只**讀**來源 repo(`install.py:506` `source_files()`),寫入的都是 target。
- `:380`:淨室內的 pytest 以淨室 repo 為 cwd。該 repo 的 `tests/conftest.py` 以自己的位置推出 `_ROOT`(`tests/conftest.py:130`),
  redlight 的 `ROOT` 也由自己的 `__file__` 推出(`redlight.py:42-43`)。
  ⇒ 帳本寫進 `<workdir>/verify-gates-repo/.dev/`,**不寫本 repo 的 `.dev/`**(靜態推論)。

**程序**(建議寫進 Station 6 的固定步驟):
1. `git status --porcelain` 必須無輸出。
   理由:安裝器讀的是**工作樹**(含未追蹤檔,`install.py:506-508`)。工作樹 ≠ HEAD 時,驗到的不是要 push 的那一版。
2. `<workdir>` 必須在 repo 之外,用 session scratchpad。放在 repo 內會讓本 repo 多一個巢狀 git repo、工作樹變髒。
3. 執行 `python .claude/portable/verify_gates.py <scratchpad>/verify-gates`,照錄最後的摘要行與情境結果。
4. 事後 `git status --porcelain` 仍然無輸出,本 repo `.dev/` 兩本帳本的 bytes 與 sha256 前後不變(作為「不污染」的實測證據)。

**是否另做機器化的 pre-push hook**(per-clone、會拖慢 push):本票不做,列 P7。

---

## P6 紅燈清單草案

**前提**:P8 全部採建議選項。BASELINE = S6-1。預測是**靜態推論**,本機 Windows + Python 3.11 + pytest 9.1.1。

- 分類 behavior-red:在 BASELINE 上必須失敗。
- 分類 regression-lock:在 BASELINE 上必須通過。

### `tests/test_redlight.py`(出貨)

`class TestEvidencePolicyBootstrap`:

| # | nodeid | 分類 | BASELINE 預測 |
|---|---|---|---|
| 1 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_a_repo_without_a_policy_is_not_full_coverage` | behavior-red | 紅(現在 "true") |
| 2 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_uncommitted_policy_state_is_not_full_coverage[worktree-only]` | behavior-red | 紅 —— **「worktree-only policy 未提交 ⇒ unknown」**(負三) |
| 3 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_uncommitted_policy_state_is_not_full_coverage[worktree-differs]` | behavior-red | 紅 —— **「HEAD 有 policy 但 worktree 不同 ⇒ unknown」**(負二) |
| 4 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_uncommitted_policy_state_is_not_full_coverage[staged-only]` | behavior-red | 紅 |
| 5 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_uncommitted_policy_state_is_not_full_coverage[deleted-in-worktree]` | behavior-red | 紅 |
| 6 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[malformed-json]` | behavior-red | 紅 |
| 7 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[unknown-schema]` | behavior-red | 紅 |
| 8 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[unknown-version]` | behavior-red | 紅 |
| 9 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[unknown-key]` | behavior-red | 紅(含自我指定位置的鍵,I-1) |
| 10 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[missing-field]` | behavior-red | 紅 |
| 11 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_a_policy_outside_the_canonical_path_is_not_full_coverage` | behavior-red | 紅 |
| 12 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_the_producer_records_the_policy_identity` | behavior-red | 紅(session 沒有 `evidence_policy` 欄) |
| 13 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_policy_content_is_not_read_from_the_worktree` | regression-lock | 綠(現在根本不讀 policy)。上線後鎖住 I-3 第 5 步:讓 Python 層 open canonical path 一律拋例外,仍須 "true" |
| 14 | `tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_a_matching_committed_policy_is_full_coverage` | regression-lock | 綠(正控) |

`class TestEvidencePolicyBoundary`:

| # | nodeid | 分類 | BASELINE 預測 |
|---|---|---|---|
| 15 | `tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_cannot_widen_the_capability_boundary[python]` | regression-lock | 綠(現在由常數擋下) |
| 16 | `tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_cannot_widen_the_capability_boundary[pytest]` | regression-lock | 綠 |
| 17 | `tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_cannot_widen_the_capability_boundary[dist]` | regression-lock | 綠 |
| 18 | `tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_cannot_widen_the_capability_boundary[config-file]` | regression-lock | 綠 |
| 19 | `tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_environment_mismatch_is_not_full_coverage[override]` | behavior-red | 紅:已提交 addopts 為 `-ra`、policy `committed_overrides: []`,runtime 經 `PYTEST_ADDOPTS` 得到 `["strict_markers=true"]`;現在與常數相等 ⇒ "true"(負一) |
| 20 | `tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_environment_mismatch_is_not_full_coverage[narrowed-dist]` | behavior-red | 紅:policy `dists: []`,runtime 有 anyio 4.15.0 |

`class TestAddoptsDerivation`(框架推導規則,以 fixture 文字驗;取代 test_d4 的框架那一半):

| # | nodeid | 分類 | BASELINE 預測 |
|---|---|---|---|
| 21 | `tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[strict-markers]` | behavior-red | 紅(函式不存在) |
| 22 | `tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[strict-config]` | behavior-red | 紅 |
| 23 | `tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[o-flag]` | behavior-red | 紅 |
| 24 | `tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[override-ini-eq]` | behavior-red | 紅 |
| 25 | `tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[no-addopts]` | behavior-red | 紅 |
| 26 | `tests/test_redlight.py::TestAddoptsDerivation::test_g3_a_policy_disagreeing_with_the_committed_addopts_is_not_full_coverage` | behavior-red | 紅:已提交 addopts `-ra`,policy 與 runtime 都是 `["strict_markers=true"]`;現在 "true" |

### `tests/test_host_evidence_policy.py`(新檔,宿主專用,manifest 標 `skip`)

| # | nodeid | 分類 | BASELINE 預測 |
|---|---|---|---|
| 27 | `tests/test_host_evidence_policy.py::test_the_committed_policy_matches_the_committed_pyproject` | behavior-red | 紅(`git show HEAD:.agents/evidence-policy.json` 失敗;依〈三十一〉裁決 3:失敗、不 skip) |

### `tests/test_status.py`(出貨)

`class TestEvidencePolicyChain`:

| # | nodeid | 分類 | BASELINE 預測 |
|---|---|---|---|
| 28 | `tests/test_status.py::TestEvidencePolicyChain::test_g3_no_policy_does_not_retire_a_known_red` | behavior-red | 紅(現在會退紅) |
| 29 | `tests/test_status.py::TestEvidencePolicyChain::test_g3_an_uncommitted_policy_does_not_retire_a_known_red[worktree-only]` | behavior-red | 紅 —— 負三的鏈條版 |
| 30 | `tests/test_status.py::TestEvidencePolicyChain::test_g3_an_uncommitted_policy_does_not_retire_a_known_red[worktree-differs]` | behavior-red | 紅 —— 負二的鏈條版 |
| 31 | `tests/test_status.py::TestEvidencePolicyChain::test_g3_a_policy_environment_mismatch_does_not_retire_a_known_red` | behavior-red | 紅 —— 負一的鏈條版 |
| 32 | `tests/test_status.py::TestEvidencePolicyChain::test_g3_a_matching_committed_policy_retires_the_red` | regression-lock | 綠 —— 正二的鏈條版 |

### `tests/test_verify_gates.py`(出貨)

| # | nodeid | 分類 | BASELINE 預測 |
|---|---|---|---|
| 33 | `tests/test_verify_gates.py::test_every_evidence_policy_scenario_is_wired` | behavior-red | 紅(`EVIDENCE_SCENARIOS` 不存在) |

### 計數

- 新增 33 支:behavior-red 26、regression-lock 7。
- 檔別:test_redlight 26、test_host_evidence_policy 1、test_status 5、test_verify_gates 1。
- 預期固定全套 collected 2090(以 S4F1 實測的 collected 2057 為底;S5f-0 到 S6-1 都沒有改測試;**未在 BASELINE 實測**)。
  本機預期 failed 26。
- 原 test_d4 在 3g 不動。它在 4g 刪除時,collected 再減 1,前提是 Jeff 裁 P8-4。

### 鏈條要求(延續〈二十九〉29.1 第 5 點)

- #1–#20、#26、#28–#32 必須經**真實** `tests/conftest.py` producer。
- 必須在 tmp root 建**真的** git repo,並提交或修改 policy 檔;不得以假雜湊值代替。
- 每次模擬執行都用全新的 conftest(`_isolated_conftest`,`<BASELINE>:tests/test_redlight.py:290`)。
- #1 需要一個**不提交 policy** 的新 helper(建議 `_g_root(policy=…)`)。它不得改用 `_d_committed_root`,因為後者在 4g 後會一併提交 policy。

### 需要的授權(4g 動既有測試或 helper;assertion、docstring 與 test identity 一律不改)

1. `tests/test_redlight.py:1143` `_d_committed_root`(46 個呼叫點)與 `tests/test_status.py:2370` `_t_committed`(19 個呼叫點):
   加入「寫入並提交與 baseline 相符的 `.agents/evidence-policy.json`」。
   否則上線後所有既有正控都會轉為 unknown —— 包括 P2-B 列出的 22 + 7 個命中,以及 `TestFixedCommandCoverage`、`TestCompletenessLocks`、`TestCollectionDefinitionLocks`、`TestPassValidityLocks`、`TestOverrideBaseChain`、`TestDebuggerModeLocks` 等。
2. `tests/test_status.py` 兩支直接寫 completeness dict 的測試:
   - `TestTestsUnderTicketUsesTheLatestRecordPerFile::test_a_file_that_went_red_then_green_counts_as_green`(`:583`)
   - `TestOrphans::test_a_renamed_red_test_is_orphaned_not_green`(`:1355`)
   兩支都在 `completeness` 補 `evidence_policy` 事實(同 3f 的 `usepdb` 授權形式)。Grep `completeness={` 只命中這兩處。
3. 若 P8-5 選 A:在 `_isolated_conftest`(`test_redlight.py:290`)與 test_status 的對應 driver,以 monkeypatch 把 `pytest.__version__` 與 conftest 所見的 `sys.version_info` 固定為能力邊界內的值。
   只改 driver,不改各測試。
4. `tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d4_the_committed_addopts_override_constant_matches_pyproject`:4g 刪除。需要 P8-4 與〈三十一〉裁決 3 的位置修訂。
5. `.agents/portable-manifest.txt`(`ask`):新增 `tests/test_host_evidence_policy.py skip`、`.agents/evidence-policy.json skip`、`.agents/evidence-policy.template.json generate`。
   否則 `tests/test_upstream_manifest.py` 會因未分類而紅。

**受影響的既有測試(預期 4g 後須經授權 1–3 才會維持原判)**:上列 helper 的全部呼叫者,以及授權 2 的兩支。

---

## P7 殘餘與未證明

1. **未實測**:P6 的紅綠預測、collected 2090、failed 26,以及 P1 #3「缺一檔、全部 None」的成因,都是靜態推論。
2. **未逐支驗證**:P2-B 的 22 + 7 個命中是否都經真實 producer 讀版本。另外,出貨測試之中是否還有其他依賴 3.11 / 9.1.1 的斷言。
3. **未驗證**:`verify_gates.py` 在本機執行時,本 repo `.dev/` 是否確實不變。只有靜態推論(P5);要等 Station 6 的步驟 4 實測。
   此外,session 的 PreToolUse 閘門在執行期間是否寫本 repo 的 intercepts 帳本,未查。
4. **宿主佈局前提**:測試不在 `tests/` 底下的下游,producer 不會載入(P1 #10)。本票不處理。
5. **「無設定檔」狀態不在能力邊界內**:沒有 pyproject 的下游必須先建立一份才能初始化。
   這是收窄(fail-closed),不是缺陷;要擴張須走票重做盤點。
6. **「人審」無法機器驗證**:機制只能要求「canonical path 上有一個已 commit 的檔」。是誰、有沒有審,框架看不到(同 CLAUDE.md「核准是一段文字,不帶身分」)。
7. **sync 端提示**:只規劃了 status 行,沒有規劃 sync 的 dry-run 列出「需建立 evidence policy」(P4)。
8. **logging 鎖步絆線**(〈四十五〉45.3):實作時必須放進宿主專用檔(P2-A 連帶影響);本票不實作。
9. **`tests/test_leak_scan.py` 的宿主樹掃描**(P2-A):它刻意斷言宿主狀態,而且出貨。它在下游的意義是否成立,本票不判定。
10. **機器化 pre-push**:裁決 5 的淨室驗證,本票規劃為程序步驟(P5),不做 hook。
11. 〈二十九〉29.1 第 3 點的殘餘照舊:TOCTOU、未 pin 版本。policy 的引入讓「改 policy 但未 commit」也進入同一類(該期間無法退紅)。

---

## P8 要 Jeff 裁的事

| # | 題目 | 選項 | 建議 | 理由 |
|---|---|---|---|---|
| 1 | policy 載體 | **甲** 獨立檔 `.agents/evidence-policy.json`(JSON,schema v1);**乙** `pyproject.toml` 的 `[tool.monkeyleash.evidence-policy]` | 甲 | 位置與設定檔型態脫鉤(I-1 不受將來擴張影響);沒有 pyproject 的 repo 也有地方放;解析不依賴 `tomllib`;identity 不被 pyproject 的無關改動牽動 |
| 2 | 誰解析 policy | **A** producer 依 I-3 從 HEAD blob 解析,記入 session,consumer 驗型別與 identity;**B** consumer 在 status 時依記錄的 blob sha 以 git 重解析 | A | 與既有 `config_blobs` 同一套模式;歷史 run 依當時的 policy 判定,不被事後重審;`file_coverage` 不必依賴 status 當下的 git |
| 3 | policy 列出能力邊界外的值 | **A** 整份 policy 不合格 ⇒ unknown;**B** 取交集,界外值靜默忽略 | A | 兩者都不會擴張(都滿足「只能收窄」),但 B 會把宿主的誤解藏起來,而且 status 會顯示「有效」;A 會出聲 |
| 4 | test_d4 處置 | **A** 只把 test_d4 原樣搬到宿主專用檔(skip);**B** 刪除,只換成框架推導測試 + verdict 時的機器鎖步;**C** = B + 宿主專用檔保留 agent-gates 自身的鎖步(原樣保留〈三十一〉裁決 3 的「git show HEAD、不得 skip」,只改適用位置) | C | A 留著常數,第二層修不好;B 會失去 agent-gates 自身「policy ↔ pyproject」的獨立檢查;C 兩層都顧到,且不違反票 16(不轉 skip) |
| 5 | 環境相依正控(P2-B) | **A** 3g / 4g 一併在共用 driver 固定版本事實;**B** 列殘餘,另開追蹤票 | A | 裁決 4 (正一) 要求框架測試在新 repo 全綠;下游若不是 3.11 + 9.1.1,B 會重演本次 CI 的形狀(紅與下游無關)。代價:授權 3 會動兩個 driver |
| 6 | 初始化 | **A** 安裝器只在非 canonical 路徑寫範本(內容 = B 常數)+ decisions-pending + status 顯示 policy 狀態;**B** 另做 `draft` 指令,從本機觀察值產草稿 | A | 不自動信任首次觀察值;status 行讓「未初始化 ⇒ 永遠 unknown」不再靜默。B 的方便正是風險所在 |

**不需裁、已依原則定案的設計**(有異議請指出):
- canonical path 與 schema 屬框架常數(裁決 6)。
- 缺 policy 與各種不一致一律 unknown(裁決 3、6)。
- `committed_blobs` 改為逐路徑呼叫(P3 遷移第 3 點)。
- 「無設定檔」不在能力邊界內(P7 #5)。
