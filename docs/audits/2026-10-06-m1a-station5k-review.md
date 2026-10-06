# 票 145 Station 5k 增量獨立審查報告

- 審查包:`docs/audits/2026-10-06-m1a-station5k-review-package.md`(S5k-0 `264e629c1899a04760f212362940f2e4a3526007`;blob `6ecd9b1f6406a45254703d0822ba3b0be067271a`;sha256 `43a3f34a39d37a07871e119ac6c7737e844286483f96c774205ea03c4b9ccdb1`)
- TARGET(S4K1B):`c1eebd97ed197d7f653fbc1c680a0feca1837c6a`(含 S4K1 `492b5de438ef9a306b112ac1fbc402729e219879`)
- REVIEW_HEAD(S4K4):`95cd4490f181537e530be516d7ef61c5f7c3e587`
- 審查者身分:第六個全新對話;無 4g / 3h–5k-0 實作 session、5g–5j 審查 session、S6-2 提交視窗的任何記憶或上下文。
- 日期:2026-10-06

---

## 1. 判決

**PASS** —— G9 在列出的全部路徑上都找不到讓「邊界外 dist」或「邊界內 dist + 未接受它的宿主 policy」得到 `file_coverage == "true"` 的路徑;G1 / G3 / G4 皆成立。其餘發現(G5 / G7 / G8)都不到 FAIL 門檻,列為 finding 與追蹤項。

---

## 2. Findings

| 編號 | 嚴重度 | G 題 | 證據 | 描述 | 需要重現 |
|---|---|---|---|---|---|
| S5k-F1 | Low | G8 | `c1eebd97ed197d7f653fbc1c680a0feca1837c6a:.claude/hooks/redlight.py:486-488`;anyio 原始碼 `anyio/pytest_plugin.py:16`、`:224`、`:305`;`anyio/__init__.py:5`、`:21`;`anyio/_lazyimport.py:33-56`(本機 4.15.0) | 納入 4.15.1 的「檔案逐位元組相同」只涵蓋 `pytest_plugin.py` 與 `entry_points.txt`;但 plugin 在 import 期就經 `from . import get_available_backends` 走 `anyio/__init__.py` → `_lazyimport.__getattr__`,而這**正是 4.15.1 唯二變動的兩個檔**,且 `get_available_backends()` 在收集期決定 anyio 測試的參數化。兩檔差異的**內容**不在任何證據裡;正二淨室證明的是「能退紅」(活性),不是「plugin 行為與已盤點的 4.15.0 等價」。 | **是**(見 G8 最小重現) |
| S5k-F2 | Nit | G7 | `c1eebd97ed197d7f653fbc1c680a0feca1837c6a:.claude/portable/verify_gates.py:335`、`:363`、`:366` | 票〈六十五〉65.3「機制」一句把 CI 淨室 FAIL 歸因於 `KNOWN_DISTS` **與** `.agents/evidence-policy.json` 的 `dists`;但淨室正二的 policy 是 `_ev_matching_policy` 依 `rl.KNOWN_DISTS ∩ 當下環境` 重新產生、覆寫到目標 repo 的 `POLICY_FILE`,宿主 policy 不參與淨室判定。淨室 FAIL 的機制只有 `KNOWN_DISTS`;S4K1B 的作用面是本 repo 自己的 run 與 status,不是 CI 淨室。程式行為無誤,只是措辭把兩個作用面併在一起。 | 否 |
| S5k-F3 | Nit | G7 | `c1eebd97ed197d7f653fbc1c680a0feca1837c6a:.claude/hooks/redlight.py:487` | 程式註解「真實 4.15.1 環境的淨室正二由 4k POSIX 驗收證明」在 S4K1 提交時,POSIX 驗收還沒發生(S4K4 才記錄),且證據是外部、非本 repo 帳本。以 REVIEW_HEAD 而言內容已成立(67.3),但它是一句寫在產品碼裡、指向不可機器重驗之來源的完成式宣稱。 | 否 |
| S5k-F4 | Info | G5 | `c1eebd97ed197d7f653fbc1c680a0feca1837c6a:.claude/hooks/redlight.py:1110`、`:1112`;`c1eebd97ed197d7f653fbc1c680a0feca1837c6a:tests/test_redlight.py:2775-2779` | K-c 在 S3K1 上是經 `:644` 判成 `other` → `:1110` 得 unknown;在 TARGET 上是 `known_dist` → `:1112` 的 `_known_dists_accepted` 得 unknown。斷言相同(`== "unknown"`),走的路徑不同 —— 「B ∩ H 拒絕邊界內但未被宿主接受的版本」這一層,在本輪沒有一個先紅後綠的示範。負控的性質本來就如此,不構成缺陷,記錄以供日後判讀。 | 否 |

---

## 3. G1–G10 逐題

### G1 邊界擴張是否正確且不 fail-open —— **成立**

證據:E.5.0 的 7 個使用點(以 TARGET 實檔核對,`git grep` 結果與包一致),逐一推演:

1. `TARGET:.claude/hooks/redlight.py:488` 定義 `KNOWN_DISTS = (("anyio", "4.15.0"), ("anyio", "4.15.1"))`:tuple of tuple,成員比較為逐元素相等,同名兩版是**兩個不同的元素**,不存在以名稱為鍵的折疊。
2. `:644` `all(pair in KNOWN_DISTS for pair in paired)`:`paired` 是同一個 plugin 物件配對到的所有 `(dist 名稱, 版本)`(`:642`,以 `p is plugin` 配對)。
   - 只配對到一個 dist(正常情況):語意與一元組時相同 —— 該版在清單內 ⇒ `known_dist`,否則 `other`。
   - 同一 plugin 物件配對到兩個 dist(例:site-packages 殘留兩份 anyio dist-info):`all` 要求**每一筆**都在清單內;任一筆是邊界外版本或版本缺失(`_dist_version` 回 None,`:545-552`)⇒ `other`。兩筆都在邊界內 ⇒ `known_dist`,並把兩筆都記進 `entry["dists"]`(`:653-654`),之後由 `:1112` 的 `_known_dists_accepted` 要求**兩筆都**在宿主接受集內(`:1012` 的 `all`)。沒有「其中一筆合格就放行」的 `any` 語意。
   - `paired` 為空時走 `elif`,不進 `all`(空集合 `all` 為真的陷阱被 `if paired:` 擋住)。
3. `:939` policy 邊界檢查 `set(tuple(d) for d in policy["dists"]) <= set(KNOWN_DISTS)`:子集合語意,兩版並存時 policy 可列任意子集合;列出邊界外任一筆 ⇒ `bnd` 非空 ⇒ `_effective_policy` 回 None(`:990-992`)⇒ unknown。
4. `:974` 安裝範本 `[list(d) for d in KNOWN_DISTS]`:範本變成兩筆。它由 `install.py:399-411` 寫到**非 canonical 路徑**(docstring 原文「安裝器寫到非 canonical 路徑的範本內容」),不自動生效;宿主要複製它才會接受兩版,而兩版皆在 B 內。`tests/test_install.py:654` 以常數推導比對,不寫死。
5. `:1109` `accepted_dists = KNOWN_DISTS ∩ policy["dists"]`(`_effective`,`:1004-1006`,保留 policy 的子集):兩版並存時只有「宿主列出 且 框架認得」的版本被接受。
6. `verify_gates.py:335` `_ev_matching_policy`:對每個 `(name, version)` 比對 `metadata.version(name) == version`。`metadata.version("anyio")` 只回一個值,所以同名兩版最多命中一筆 ⇒ 淨室 policy 的 `dists` 恰為「實裝版本(若在邊界內)」,否則為空。空 `dists` 在環境有 anyio 時 ⇒ plugin 為 `other` 或 `known_dist` 但不被接受 ⇒ unknown(正二不成立,與 docstring `:325-326` 的設計一致)。負一 / 二 / 三(`:429-442`)不依賴 `dists`。
7. status 顯示:`status.py:565-572` 只呼叫 `rl.policy_state(root)`;`policy_state`(`redlight.py:944-961`)經 `policy_document_problems` 判「有效 / 超出框架能力邊界」,語意不變。`tests/test_host_evidence_policy.py:91` 以 `⊆ redlight.KNOWN_DISTS` 推導,不寫死。

「policy 列 4.15.0、環境 4.15.1」:`:644` ⇒ `known_dist`、`dists=[["anyio","4.15.1"]]`;`accepted={("anyio","4.15.0")}`;`:1112` ⇒ unknown。
反向「policy 列 4.15.1、環境 4.15.0」:對稱,`:1112` ⇒ unknown。
兩者都不得 true。

### G2 宿主 policy —— **成立**

證據:`TARGET:.agents/evidence-policy.json:8`;E.4 / 本審查重跑的 `git diff d4b6faf…c1eebd9 -- .agents/evidence-policy.json` 只有 `@@ -5,5 +5,5 @@` 一個 hunk,`-1 / +1`,改的就是 `dists` 一行。

- 兩筆 `["anyio","4.15.0"]`、`["anyio","4.15.1"]` ⊆ TARGET 的 `KNOWN_DISTS`(`:488`)⇒ `:939` 不入 `bnd`。
- `schema` / `version` / `config_file` / `committed_overrides` / `python_versions` / `pytest_versions` 都在 diff 的 context 行,未變。
- 同名兩筆是否合法:`policy_document_problems`(`:906-941`)只驗 `_is_pair_list` 與子集合,沒有「同名唯一」的約束;`_known_dists_accepted` 以完整 `(名稱, 版本)` 比對。所以 B ∩ H = H = 兩版,4k 文件「effective = B ∩ H 兩版皆接受」(F.1 第 52 行)成立。
- 4k 本機 status `evidence policy: 有效`(F.1 第 128 行)與此推演一致。

### G3 不變式未削弱 —— **成立**

證據(本審查以完整 SHA 重跑):

- `git diff --stat d4b6faf…c1eebd9`:非 docs 的只有 `.agents/evidence-policy.json | 2 +-`、`.claude/hooks/redlight.py | 4 +-`、`tests/test_redlight.py | 42 +`。與 D.2 一致;conftest / status.py / install.py / verify_gates.py 不在清單內。
- 逐 commit:S3K1 只動 `tests/test_redlight.py`(42 insertions);S4K1 只動 `.claude/hooks/redlight.py`(3+ / 1−);S4K1B 只動 `.agents/evidence-policy.json`(1+ / 1−)。
- redlight.py:唯一 hunk `@@ -483,7 +483,9 @@`,`-` 行只有舊的 `KNOWN_DISTS = (("anyio", "4.15.0"),)`,`+` 行為兩行註解 + 新定義(`TARGET:.claude/hooks/redlight.py:486-488`)。
- test_redlight.py:E.2(`0904cdb..b084979`)唯一 hunk `@@ -2748,3 +2748,45 @@`,無 `-` 行;-U0 形式為 `@@ -2750,0 +2751,42 @@`(F.2 第 32 行),兩者一致(第 2750 行之後插入 42 行 = 2751–2792)。既有 helper `_g_policy`(`:2161`)/ `_g_policy_text`(`:2176`)/ `_g_root`(`:2187`)/ `_g_coverage`(`:2240`)/ `_d_plugins`(`:1216`)不在 hunk 內。
- blob 鏈:redlight.py 在 S6-2 / S3K1 / S3K2 皆 `d4d208af…`,TARGET / REVIEW_HEAD 皆 `0fe2f7ab…`;test_redlight.py 在 S6-2 `c284bc8c…`,S3K1 之後皆 `e9f4c82e…`;policy 在 S4K1B 前 `6e9aca1f…`,之後 `82669a8c…`。與 F.1 第 9 節所列受測物 blob 相同。
- TARGET → REVIEW_HEAD(S4K3、S4K4)只改 `docs/`(本審查 `git show --stat` 核對)。

### G4 紅綠時序 —— **成立**

證據:F.0 表;F.2 第 59–62 行(FAILED 四行)、第 63 行(`4 failed, 2106 passed, 4 skipped, 3 xfailed`);F.1 第 81 行(`2110 passed, 4 skipped, 3 xfailed`)。本審查以 `git grep -n` 在 REVIEW_HEAD 抽驗 F.1 第 36、81、129、197 行與 F.2 第 132 行,行號與內容皆符合。

- S3K1:K-a / K-b / K-e[4.15.0] / K-e[4.15.1] failed,失敗行 `:2767`、`:2773`、`:2792`、`:2792`;以 TARGET 的 test_redlight.py 核對,這三個行號恰為三支測試的 `assert` 行。K-c / K-d 在 passed 之內。紙上推演(S3K1 時 `KNOWN_DISTS` 只有 4.15.0):K-a 不在;K-b policy 含 4.15.1 ⇒ `:939` 越界 ⇒ unknown;K-e 兩案 policy 含 4.15.1 ⇒ 越界 ⇒ unknown;K-c 4.15.1 plugin ⇒ `other` ⇒ unknown;K-d 9.9.9 ⇒ 越界 ⇒ unknown。與實測一致。
- S4K1B:0 failed;K 測試沒有 xfail 標記,而 4 支 skipped 已逐行列出(F.1 第 77–80 行,即輸出檔第 32–35 行,無 K 測試),所以 6 個 nodeid 必為 passed —— F.1 第 95 行(§2 表下註)的推論成立。
- 帳本:V0 → V1(F.2 §3:前段 `head -c 891928` / `head -c 17351316` 的 sha256 = V0)、V1 → V2(F.1 §3:前段 = V1)。本審查 Step 0 與收尾的全檔 sha256 = V2(`3637077a…` / `6d18a5c6…`),`wc -l` = 3438 / 36,`wc -c` = 915335 / 18838751,與 F.1 §3 一字不差 ⇒ S4K2 之後本 repo 沒有再追加任何 run。
- R3:S4K1 寫 redlight.py 時所依賴的紅燈是 S3K1 上那一次 run(status `tests red under ticket 145: tests/test_redlight.py`,F.2 第 132 行;F.1 第 36 行)。該 run 讀到的 redlight.py 是 `d4d208af…`,而 S3K2 上 redlight.py 同為 `d4d208af…`(S3K2 只改 docs)⇒ 那個紅燈正是對著 S3K2 時的 redlight.py 跑出來的。

### G5 測試是否測到宣稱形狀 —— **成立**(附 S5k-F4 Info)

證據:`TARGET:tests/test_redlight.py:2763-2792`;helper `:2161-2241`、`:1216-1226`。

- K-b(`:2771`):`_g_policy(dists=[["anyio","4.15.1"]])` —— `policy.update` 整欄覆寫,所以 policy **只列** 4.15.1;`_g_root` 預設 `commit_policy=True`(`:2187`)⇒ 已提交。`anyio_version="4.15.1"` 經 `_g_run` → `_d_plugins` → `_DDist("anyio", anyio_version)` 與 `anyio.pytest_plugin` 模組物件配對(`:1226`),是真的走 `:642` 的配對路徑。
- K-c(`:2779`)`assert got == "unknown", got`;K-d(`:2785`)同為 `== "unknown"`,不是 `!= "true"`。K-d 用 `9.9.9`(`:2783-2784`)。
- K-e(`:2787-2792`):`@pytest.mark.parametrize("version", ["4.15.0", "4.15.1"])`;每案各自取得 pytest 的 `tmp_path` 與 `monkeypatch`,並在案內建立自己的 root ⇒ 兩案獨立,不共用 repo 或帳本。
- helper 未改:見 G3。
- S5k-F4:K-c 修前修後同綠,但走的判定行不同(`:1110` vs `:1112`),見 Findings。

### G6 5g–5j 結論是否仍成立 —— **成立**

證據:G3 的範圍核對(TARGET_J..TARGET 只動 `KNOWN_DISTS` 一行、policy 一行、測試檔尾);C.1。

- 5g–5j 審過的 `_root_is_toplevel`、`evidence_policy_facts`(`:855-898`)、`_effective_policy`(`:977-1001`)、`_completeness_verdict`(`:1075-`)、producer / conftest 都沒被增量碰到 ⇒ 結論的前提不變。
- C.1 七項追蹤項:增量沒有處理也沒有惡化任何一項,狀態皆維持「目前尚未 machine-enforced」。
- S5j-F2(J2[bare] 在 `safe.bareRepository=explicit` 下空洞通過):相關測試與 `_root_is_toplevel` 不在增量內,不受影響,也未被修補。
- 註:TARGET_J..TARGET 的 docs 變動(4i-fix、4j-fix、5j 包、5j 報告、票)屬 TARGET_J..BASE_J 的 5j 產出(本審查 `git diff --name-only d4b6faf..774e735` 核對),不屬本輪增量。

### G7 措辭與程式一致 —— **部分成立**(S5k-F2、S5k-F3 皆 Nit)

證據:B.1 65.2 / 65.3、B.3 67.2 / 67.3、H(4k §7)、D.1 commit 訊息。

- 65.3 通篇使用「推定」,並兩次寫明「CI 實際安裝版本尚未取得 log 直接核驗」;65.2 寫「完整 log 需登入,未取得」。與 F.3(本機 CI 查詢停手、狀態「未知」)一致。S6-2 commit 訊息亦寫「推定」。
- 67.3 對 test_gate 1 支、known_items_regression 12 支、淺層 clone 4 支的環境性成因,皆標「推定 / 尚未獨立核驗」。
- 4k §7 第 2 點「相依漂移」與 TARGET 的程式相符:`KNOWN_DISTS` 仍為精確版本 pin(`:488`)。
- **全包與兩份報告沒有任何一處宣稱 CI 已綠**;67.3 最後一點明寫「CI 是否轉綠仍須 Station 6 第三次 push 後由 CI 本身證明」,F.1 第 9 節同句。
- 不一致之處兩則(都不改變判決):S5k-F2(65.3 機制句把宿主 policy 也算進 CI 淨室的成因)、S5k-F3(程式註解的完成式宣稱寫在證據產生之前)。

### G8 證據邊界 —— **部分成立**(S5k-F1,需要重現)

**KNOWN_DISTS 的定義與用途**(從程式而非註解推):

- `:479-485` 的註解區塊:四組「已盤點」清單,「已知第三方 plugin ⇒ 鎖 dist 名稱 + 精確版本;未知 plugin ⇒ fail-closed」;`(vii′)`「只看名稱不算(名稱可被冒用),版本不同也不算」。
- 用途:`:644` 決定 plugin 是否屬於 `SUPPORTED_PLUGIN_KINDS`(`:470`),亦即「這個 plugin 不會悄悄改變收集 / 執行完整性」這個前提是否被盤點過;`:939` / `:1109` 再把它當能力邊界 B。
- 所以「納入某版」要滿足的是:**該版作為 pytest plugin 的行為,與已盤點的那一版相同(或已另行盤點)**。`(xiii)` 屬 `KNOWN_PYTEST_VERSIONS`,本題不套用。

**本輪依據是否足夠**:

- 外部證據一(wheel 比對):`pytest_plugin.py` 與 `entry_points.txt` 逐位元組相同;差異「僅」`anyio/__init__.py`、`anyio/_lazyimport.py`。
- 本機 4.15.0 原始碼唯讀對照(不得實跑):
  - `anyio/pytest_plugin.py:16` `from . import get_available_backends` —— 在 plugin 模組 import 時就經過 `anyio/__init__.py`。
  - `anyio/__init__.py:5` 從 `._lazyimport` 匯入;`:21` 以 `TYPE_CHECKING` 區塊宣告 `get_available_backends` 來自 `._core._eventloop`。
  - `anyio/_lazyimport.py:33-56` 的模組層 `__getattr__` 依 `lazy_map` 解析名稱並 `import_module`。
  - `get_available_backends()` 用在 `anyio/pytest_plugin.py:224`(`pytest_collection_finish` 內的參數化)與 `:305`(`anyio_backend` fixture 的 `params`)—— **影響收集出哪些身分**。
  - 同檔另有 `pytest_pycollect_makeitem`(`:192-193`,tryfirst)、`pytest_pyfunc_call`(`:268-269`,tryfirst)等收集 / 執行 hook。
- 結論:兩個變動檔**就在 plugin 的 import 與名稱解析路徑上**。「plugin 檔相同」是必要條件,不是充分條件 —— 包自己也寫「檔案相同不等於行為等價」。補上的外部證據二(真裝 4.15.1 淨室正二成立)證明的是**活性**(該環境能得到 true),不是盤點等價;正二的探針 `tests/test_evidence_probe.py` 並不使用 anyio。
- 兩檔差異的**內容**(改了什麼、是否改變 `lazy_map` 或 `get_available_backends` 的解析)不在任何一份證據裡。依據對「納入」這個決定大致足夠(方向保守、兩檔看名稱屬匯出機制),但未達到 `(vii′)` 定義所要求的「已盤點」強度。
- 本機只有 4.15.0(`pip show` 原文見第 4 節),無法對照 4.15.1。

**需要重現(最小重現)**:

1. 取得兩個 wheel,核對 sha256 = `7ecd9937…acb99`(4.15.0)/ `6152fdbb…ed101`(4.15.1)。
2. 解包後 `diff` `anyio/__init__.py` 與 `anyio/_lazyimport.py`,照錄全文差異。
3. 判讀:`get_available_backends`、以及 `pytest_plugin.py:17-23` 自 `._core._eventloop` / `._core._exceptions` 直接匯入的名稱,在兩版是否解析到同一個定義;`_lazyimport` 的變動是否會在 plugin import 期改變行為(例:新增 deprecated alias 警告 —— 與 `pythonwarnings` / `-W error` 的互動)。
4. (選做)在兩個各裝一版的全新 venv 中,對一個含 `@pytest.mark.anyio` 測試的最小 repo 跑 `pytest --collect-only -q`,比對 nodeid 清單相同。

### G9 總問題(增量版)—— **找不到同級漏洞**

逐一檢查過的路徑(全部以 TARGET 的程式紙上推演):

| # | 情境 | 推演 | 結果 |
|---|---|---|---|
| 1 | policy 列兩版 + 環境第三版(例 4.15.2) | `:644` `("anyio","4.15.2") ∉ KNOWN_DISTS` ⇒ `other` ⇒ `:1110` | unknown |
| 2 | policy 只列 4.15.1 + 環境 4.15.0 | policy 合格;plugin `known_dist`、`dists=[4.15.0]`;`accepted={4.15.1}` ⇒ `:1112` | unknown |
| 3 | policy 只列 4.15.0 + 環境 4.15.1(K-c) | 對稱於 #2 | unknown |
| 4 | 同一 plugin 物件配對到 4.15.0 與 4.15.1 兩個 dist,policy 只列其一 | `:644` 兩筆皆在 ⇒ `known_dist`;`_known_dists_accepted` 的 `all`(`:1012`)要求兩筆皆被接受 ⇒ 缺一 | unknown |
| 5 | 同 #4,配對中一筆邊界外(例 4.15.0 + 9.9.9) | `:644` 的 `all` 失敗 ⇒ `other` | unknown |
| 6 | 同 #4,policy 列兩版 | `known_dist` 且兩筆皆被接受 ⇒ 可為 true。兩筆都在 B 且都被 H 接受,不屬「邊界外」也不屬「未被接受」 | true(不屬漏洞) |
| 7 | 版本字串缺失 / 帶空白 / 後綴(`None`、`" 4.15.1 "`、`4.15.1.post0`) | `_dist_version` 去空白後比對(`:552`);None 或後綴 ∉ ⇒ `other` | 前者等同 4.15.1;其餘 unknown |
| 8 | 名稱大小寫 / 底線(`Anyio`、`any_io`) | `_dist_name` 正規化 lower 與 `_`→`-`(`:542`);policy 端不正規化,`["Anyio",…]` ⇒ `:939` 越界 ⇒ unknown | 無放寬 |
| 9 | policy `dists` 含邊界外一筆 + 邊界內一筆 | `:939` 整份不合格(不取交集)⇒ `_effective_policy` None | unknown |
| 10 | policy `dists=[]` + 環境有 anyio(任一邊界內版本) | `accepted=∅` ⇒ `:1112` | unknown |
| 11 | 4k 之前留下的帳本紀錄(4.15.1 的 plugin 當時被記為 `other`) | consumer 不重新分類;`other` ⇒ `:1110` | unknown(維持 fail-closed) |
| 12 | 只套 S4K1、未套 S4K1B 的中間態(B 兩版、H 一版)+ 環境 4.15.1 | 等同 #3 | unknown |
| 13 | 只套 S4K1B、未套 S4K1(H 含 B 外版本) | `:939` 越界 | unknown |
| 14 | verify_gates 淨室,環境為邊界外版本 | `_ev_matching_policy` 的 `dists=[]`(`:334-340`)⇒ 等同 #10 | unknown(正二不成立) |

`all(pair in KNOWN_DISTS for pair in paired)` 在同名兩版下的語意:`pair` 是完整的 `(名稱, 版本)` 元組,`in` 對 tuple of tuple 做逐元素相等比較,同名不同版是不同元素;`all` 的量詞是「這個 plugin 配對到的每一個 dist」,不是「KNOWN_DISTS 的每一個成員」。所以清單變長不會讓任何一個原本 `other` 的配對變成 `known_dist`,唯一的例外是 `("anyio","4.15.1")` 本身 —— 而那正是本輪的意圖,且仍須通過 H。

### G10 程序 —— **不影響**

依據:

- S6-2 `0904cdbc…` 只改票 145 一個檔(`git show --stat`:61+ / 3−)。3 行 `-` 全是狀態行(票頭第 3 行、lifecycle 句、`S5j-1 …於下一次提交回填`),每一處都以 F-036 形式保留舊文;沒有刪改任何既有證據段、雜湊或 run 紀錄。
- S6-2 不含任何程式、測試、policy 或帳本變動;S6-2 的 redlight.py / policy blob 與 BASE_J 之後到 S3K2 相同(`d4d208af…` / `6e9aca1f…`)。紅綠的依據(S3K1 的 run、S4K2 的 run)都由原實作視窗產生,F.2 / F.1 各自有前段 sha256 鏈(V0 → V1 → V2)。
- 3k 指令誤貼 5j 視窗並停手:若該視窗曾跑 pytest,帳本會多出行數;V0 → V1 與 V1 → V2 都恰為 +47 / +1(一次全套的形狀),而目前全檔 = V2(本審查前後兩次 sha256、`wc -l`、`wc -c` 皆符)。誤貼若發生在 V0 量取之前,會落在 V0 前段而與本輪紅綠無關。
- F.3 本機報告 sha256 本審查重算 = `969f6729…02aa`,與包所記相同。
- 審查者身分隔離:S6-2 提交視窗與 5k 不同(本對話為全新)。

---

## 4. 紙上推演與唯讀查詢記錄

### 4.1 pip show anyio(照錄;本機使用者名稱已遮)

```
Name: anyio
Version: 4.15.0
Summary: High-level concurrency and networking framework on top of asyncio or Trio
Home-page: 
Author: 
--- Logging error ---
Traceback (most recent call last):
  File "C:\Users\<user>\AppData\Local\Programs\Python\Python311\Lib\site-packages\pip\_internal\utils\logging.py", line 177, in emit
...
UnicodeEncodeError: 'cp950' codec can't encode character '\xf6' in position 21: illegal multibyte sequence
...
Message: 'Author-email: %s'
```

(其後 `License` / `Location` / `Requires` / `Required-by` 各一段相同形狀的 cp950 logging 錯誤,屬終端編碼問題;`Requires` 參數為 `idna, typing_extensions`,`Required-by` 參數為 `httpx, mcp, sse-starlette, starlette`。本題只需 Version 行。)

**本機 anyio = 4.15.0,未實跑任何東西。**

### 4.2 讀過的本機 anyio 4.15.0 原始碼(唯讀,相對路徑)

- `anyio-4.15.0.dist-info/entry_points.txt:1-2`:`[pytest11]` / `anyio = anyio.pytest_plugin`
- `anyio/pytest_plugin.py:16`、`:17-23`、`:87`、`:112`、`:131-132`、`:192-193`、`:210`、`:224`、`:268-269`、`:305`
- `anyio/__init__.py:5`、`:21`
- `anyio/_lazyimport.py:18-56`

### 4.3 git 查詢(全部以完整 SHA 為錨點,各自單獨送出)

- `git diff --stat d4b6fafd…..c1eebd97…`
- `git diff d4b6fafd…..c1eebd97… -- .claude/hooks/redlight.py tests/test_redlight.py .agents/evidence-policy.json`(與 E.1 逐字相同)
- `git log --format=%H%x20%s 774e7351…..95cd4490…`(7 筆,與 A.1 / D.1 對應)
- `git show --stat` × S3K1 / S4K1 / S4K1B / S6-2 / S3K2 / S4K3 / S4K4
- `git diff --name-only` × `774e735..b084979`、`d4b6faf..774e735`、`b084979..492b5de`
- `git ls-tree` × S6-2 / S3K1 / S3K2 / TARGET / REVIEW_HEAD(三個程式檔的 blob)
- `git show c1eebd97…:{.claude/hooks/redlight.py, .claude/portable/verify_gates.py, tests/test_redlight.py}` → scratchpad 扁平檔,以 Read / Grep 閱讀
- `git grep -n -E "dists|policy_template|policy_state|policy_document_problems" c1eebd97… -- status.py install.py tests/conftest.py redlight.py`
- `git grep -n …  95cd4490… -- 4k-fix.md 3k-redlight.md`(抽驗 F.0 行號)
- `git show -U0 0904cdbc… -- 票 145`(S6-2 的刪除行)

### 4.4 紙上推演

見 G1(7 個使用點)、G4(S3K1 上 6 支的預期結果)、G5(helper 路徑)、G9(14 個情境)。

---

## 5. 5g–5j 結論複查

- 增量只動 `KNOWN_DISTS` 一行(+2 行註解)、宿主 policy `dists` 一行、測試檔尾 42 行;5g–5j 審查對象中的判定函式、producer、conftest、status / install / verify_gates 皆未改(G3)。
- 5j 的 PASS 與 S5j-F1 / F2 / F3 結論:前提未變,**仍成立**。
- 5j 第 6 節追蹤項 1–7:皆未處理、皆未惡化,狀態不變。
- 唯一可能交會處:4j / 5j 曾以「anyio 4.15.0」作為固定全套的已盤點 plugin 事實;本輪把邊界擴成兩版,並未使任何既有 `true` 判定失效(G9 #11)。

---

## 6. 追蹤項建議(全部**目前尚未 machine-enforced**)

1. **S5k-F1 的重現**:兩個 anyio wheel 的 `__init__.py` / `_lazyimport.py` 差異照錄並判讀(G8 最小重現 1–3);結果附到 4k 報告第 9 節之後。
2. **相依漂移的機制化**(沿用〈六十五〉65.4 / 4k §7 第 2 點):本輪再次確認 `KNOWN_DISTS` 仍是精確版本 pin;候選機制(CI 在淨室前印出實裝版本並與 `KNOWN_DISTS` 比對、或 constraints 檔)維持未實作。
3. **納入新版本的判準落成文字**:本輪的「plugin 檔逐位元組相同 + 真裝淨室正二」組合,建議在 `(vii′)` 旁寫明「還須核對 plugin import 路徑上的變動檔」,避免下一次只比對 `pytest_plugin.py`。
4. **S5k-F2 措辭**:65.3 機制句可補一句「淨室的 policy 由 `_ev_matching_policy` 重新產生,宿主 `dists` 不參與;S4K1B 的作用面是本 repo 自己的 run」。
5. **S5k-F3**:`redlight.py:487` 的註解可改為指向文件(例「見票 145〈六十七〉67.3」),不在產品碼裡寫完成式宣稱。
6. **既有過期行號(非本輪引入)**:`TARGET:tests/test_redlight.py:2440` 的 docstring 寫「`:613` 的 `KNOWN_DISTS` 含 anyio 4.15.0 ⇒ `:833` 回 `"true"`」;TARGET 上 `KNOWN_DISTS` 在 `:488`。內容仍真,行號已過期(引名不引行號的同一類)。

---

## 7. 程序紀錄

### 7.1 Step 0 原文(各自單獨送出)

```
$ cat .dev/pipeline.json
{
  "current_stage": "review",
  "feature": "framework-updates",
  "ticket_id": "145",
  "updated": "2026-10-05"
}
$ git rev-parse HEAD
264e629c1899a04760f212362940f2e4a3526007
$ git ls-tree 264e629c1899a04760f212362940f2e4a3526007 docs/audits/2026-10-06-m1a-station5k-review-package.md
100644 blob 6ecd9b1f6406a45254703d0822ba3b0be067271a	docs/audits/2026-10-06-m1a-station5k-review-package.md
$ git status --porcelain
 M docs/agents/friction-log.md
?? docs/tickets/framework-updates/146-claude-code-enforcement-integrity.md
?? docs/tickets/framework-updates/147-turn-end-check-via-settings-stop-hook.md
$ sha256sum .dev/test-runs.jsonl
3637077aea4d2bdaa3138bf9b2aa28b5306ab9e9bc317d04df78ddfee3382778 *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
6d18a5c6567054da5f2d09d7655b8aa29129c34cbf948be69e8a9c58d09dddcd *.dev/test-sessions.jsonl
$ python -m pip show anyio
Version: 4.15.0   (其餘見 4.1)
```

全部符合預期。

### 7.2 包檔 sha256 核對

```
$ git show 264e629c1899a04760f212362940f2e4a3526007:docs/audits/2026-10-06-m1a-station5k-review-package.md > <session scratchpad>/m1a-s5k-package.md
(無輸出)
$ sha256sum <session scratchpad>/m1a-s5k-package.md
43a3f34a39d37a07871e119ac6c7737e844286483f96c774205ea03c4b9ccdb1 *<session scratchpad>/m1a-s5k-package.md
```

= 預期值。

### 7.3 其他

- 閘門攔截:**無**。
- 寫入:只有本報告 `.scratch/m1a-s5k/review-report.md`(Write);scratchpad 內的扁平暫存檔 `m1a-s5k-package.md`、`m1a-s5k-redlight.py.txt`、`m1a-s5k-verify_gates.py.txt`、`m1a-s5k-test_redlight.py.txt`。未改任何 repo 檔、未 commit / push / fetch / stash、未改 `.dev/pipeline.json`。
- 未執行 pytest、verify_gates.py、status.py 或任何本 repo 的 Python;未用 `python -c` / heredoc。
- 未讀取 AI 對話紀錄檔;兩本帳本只做 `sha256sum` / `wc -l` / `wc -c`。
- 讀了 `.dev/reports/2026-10-06T002652Z-ticket145-station6b-push-ci.md` 的 sha256(只算雜湊,未開啟內容):`969f6729e99d91ef24f6f6b8142109efc9ff681e6ede3bb26960aa04f28d02aa`。
- 兩本帳本 sha256:審查前 `3637077a…2778` / `6d18a5c6…dcd`;`wc -l` 3438 / 36;`wc -c` 915335 / 18838751。審查後見 Step 4(回報於對話)。
