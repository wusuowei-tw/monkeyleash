# 108 — 通用洩漏規則補 Google 新格式 `AQ.`,並補一條「通用組逐條正對照」的元測試

**狀態**:**完成**(2026-09-05)—— 四刀 `11eaa3a` / `c2bf47f` / `7491ecd` / 刀四本 commit,**未推**。三層全過:**UNIT 1326**(紅燈 5 條 → 全綠)、**CLEAN 1213**(1210 passed + 3 skipped)、**REAL** 權威層真的擋下一次 `git commit`。四個計數的預測與實測全中(差 0)。~~立案、未實作~~(`F-036`:舊狀態不刪)
**時鐘**:**有外部時鐘** —— Google 自 2026-06 起發的 Gemini API 金鑰改成 `AQ.` 開頭的 Auth key。新鑰**已經在本機 `.env` 裡**(桌機 9/5 實測可用),而現行通用規則只認 `\bAIza…`,**新鑰穿過**。下游 repo 收不到本機個人黑名單那一行形狀,所以每晚一天,下游就多一天沒有這條規則。
**站別**:待裁(見第七節 —— 兩個目標檔在 `gate.py` 眼中**都不是原始碼**,R2 不管,所以站別是流程紀律問題不是閘門問題)
**前置**:偵察回報 `.dev/reports/2026-09-05T060441Z-aq-key-rule-recon.md`;票 102(R1 零正對照,同一族的前例)、票 47(R5 零正對照)、票 45(規則清冊)

> **票號取得時點:2026-09-05,開檔當下重查 `docs/tickets/framework-updates/`,
> 最大號 107(`107-readme-rewrite-from-decider-draft.md`),加一。
> `.scratch/framework-updates/issues/` 無數字開頭檔案,不存在跨目錄撞號。**
> 不提前占號(`F-118`)。

---

## 一、問題

**兩件事,同一票**,因為第二件是第一件的**落點**:不先有元測試,新規則會落在一個沒有機制的位置上,跟現有那 4 條一樣。

### 1-1 `AQ.` 新格式穿過通用規則

`.claude/portable/leak-patterns.txt:23` 逐字:

```
\bAIza[A-Za-z0-9_\-]{30,}
```

**它只認舊格式。** 新格式是 `AQ.` 開頭、桌機實測長 53 的 Auth key,`AIza` 那條打不到。桌機 9/5 實測:含新鑰的 `.env` 餵給 `leak_scan`,**回 exit 0**(沒擋)。目前唯一擋著它的是 `~/.claude/leak-patterns.local.txt` 裡一行形狀 —— 那個檔**不進版控**(`leak_scan.py:56-58`),所以**下游 repo 完全沒有這條規則**。

### 1-2 通用組沒有逐條正對照,而且沒有機制要求有

10 條通用 pattern 裡:

| 狀態 | 條數 | 是哪些 |
|---|---|---|
| 有直接正對照 | 4 | 憑證副檔名 pfx 與 pem 那兩條、`-----BEGIN … PRIVATE KEY-----`、`\bghp_…` |
| 只是別的測試順帶打到 | 1 | `\bAIza…`(兩處都在測遮罩與 CJK 檔名,不是在測這條規則) |
| **完全沒有** | **4** | 憑證副檔名 p12 那條、`\bsk-…`、`\bgithub_pat_…`、`\bxox[baprs]-…` |
| 只對**臨時 RuleGroup** 測過,不經出貨檔 | 1 | `\bAKIA…`(`tests/test_scanner.py:616`) |

> **合計 10 條(以 `973ddc2` 的 `leak-patterns.txt` 為底,`load_patterns()` 實測 `len == 10`)。本票 +1 → 11 條。**

**沒有任何測試遍歷 `load_patterns()`。** 也就是說:今天往那個檔加一行,**不會有任何東西要求它配一條斷言** —— 加完之後測試全綠,而那條規則從沒被驗證過會命中。這正是票 102 記過的形狀:**輸入存在不等於斷言存在**。

---

## 二、偵察摘要(引 `.dev/reports/2026-09-05T060441Z-aq-key-rule-recon.md`,不重抄整份)

引該份**第二段之 4)「誤殺量測」**與**之 6)「長度下限」**兩節。要點:

- **誤殺實測 0**:候選 pattern `\bAQ\.[A-Za-z0-9_\-]{40,}` 對 `git ls-files` 全樹,命中 **0 檔 0 處**。涵蓋 **248 檔內容掃描 / 251 檔 tracked**(3 檔為掃描器自己與 `.gitignore`)。
- **量測走的是同一顆引擎**(`scanner.scan_paths` + `RuleGroup`),含它的四種比對面聯集(原文/正規化 × 大小寫敏感/不敏感,`scanner.py:336-357`)⇒ 那個 0 **已經涵蓋** `aq.` / `Aq.` 等大小寫變體。
- **harness 自證會叫**:正對照(`AQ.`+50 字)exit 1、遮罩長度回報 53 字;負對照(`AQ.`+39 字)exit 0。
- **現行兩條規則的形式自相矛盾**:`AKIA` 用封閉 `{16}` + 前後 `\b`(`:21`),`AIza` 用開放 `{30,}` 且**無收尾 `\b`**(`:23`),而 `AIza` 鑰其實也是封閉的 39 字規格。**兩條都沒有行內註解**,`git log -S` 顯示同在初始 commit `91335c8` 引入,無說明 commit。
- **`scanner.py:103` 那句「`\bAKIA[A-Z0-9]{16}` 靠大寫縮小誤判」在今天已不成立** —— 同一個 `__init__` 緊接著編了 `patterns_ci`(`:105-106`)、`scan_paths:348` 兩份都跑取聯集。⇒ **大小寫不再是收窄手段,長度是目前唯一還有效的收窄旋鈕。**

---

## 三、裁決(2026-09-05,逐字)

```
裁決:pattern 取 \bAQ\.[A-Za-z0-9_\-]{40,}(開放下限,依檔頭「寧可寬」+ 本輪誤殺 0;
「53 為規格固定」列未證明,附註裁決端網搜結果「新格式 53 字/舊 39 字」未經機器驗證);
票內加一條表驅動元測試:遍歷 load_patterns() 通用組,每條對應一個組裝正樣本,
缺樣本或不命中即紅(現有 4 條無正對照者會一起紅,轉綠時一起補);
範圍超過一小時切回只補 AQ. 一條並回報。
```

**切回條件是本票的一部分,不是備案的口頭承諾** —— 超過一小時就只留 `AQ.` 那一條並回報,元測試另開票。

---

## 四、三層測試表(UNIT / CLEAN / REAL)

**三層不是「由粗到細」,是三個不同的命題** —— 跳過任何一層,那一層的命題就沒有人回答(票 105 `:165` 逐字紀律)。

| 層 | 要證的命題 | 怎麼證 | 為什麼別層證不了 |
|---|---|---|---|
| **UNIT**(pytest,本機) | ① `AQ.`+50 的組裝樣本經**出貨的** `leak-patterns.txt` → `load_patterns()` → `ls.scan()` 回 1;② 元測試遍歷通用組,**11 條**各有組裝正樣本且各自命中;③ 缺樣本即紅(不是靜默跳過);④ 反控:`AQ.`+39 不命中(釘住下限就在 40) | `tests/test_leak_scan.py` 加測試,樣板照 `test_a_github_token_shape_is_caught`(`:45-47`) | 快、可枚舉。**但它 import 的是這棵樹裡的檔案** —— 證不了「這條規則會不會跟著安裝走到下游」 |
| **CLEAN**(淨室,`verify_gates.py <tmp>`) | 新規則與新測試**真的被複製到全新安裝的 repo**,而且在那裡跑得起來、綠 | `python -X utf8 .claude/portable/verify_gates.py <暫存目錄>` —— 它 `install.main(target)` 進乾淨目錄再 `pytest tests/ -q`(`verify_gates.py:225,301`) | manifest 標記是**宣告**,不是證據。標記對而安裝腳本沒搬過去,UNIT 一樣全綠。⚠ 淨室測試數會因本票 +N,**基準要跟數字一起寫**(`F-109`):以 `973ddc2` 的筆電淨室 `1197 passed, 3 skipped` 為底 |
| **REAL**(真的 `git commit`) | **權威層**(`.githooks/pre-commit` 的 leak_scan 那一段)對含 `AQ.` 形狀的檔案**真的擋得下 commit** | 活體負控:暫存一個含組裝假鑰的檔,`git commit` 一次,要看到 `[洩漏偵測]` 擋下訊息與非 0 退出碼,然後 `git reset` | UNIT 是 in-process 叫 `ls.scan()`,**證不了 hook 有沒有被呼叫**。`docs/machine-init.md:567` 逐字:「hook 本體或掛載缺 → 根本沒被呼叫(靜默、看不見)。所以驗收不能只 `ls`,要跑活體探針」。同一條路徑在 `973ddc2` 已經跑過一次(commit 訊息:「權威層第一段活體負控通過(leak hook 擋假 token)」),本票是**換一個 pattern 再跑一次** |

### 元測試的設計約束(要寫進實作,不是建議)

1. **表以 pattern 原字串為 key。** 改了一條 pattern,key 就對不上 → 紅 → 有人得回來看。這是本票唯一那個「規則變動會叫」的機制。
2. **樣本一律組裝,不得寫死字面。** `tests/test_leak_scan.py:6-8` 逐字:「這個測試檔自己也被 shipped-tree-is-clean 掃描,所以它不含任何實際敏感字面:所有偵測樣本都是組裝的,或用注入的 pattern。」
3. **憑證副檔名那三條(pfx / p12 / pem)的樣本要放在【內容】裡,不是檔名。** `leak_scan.scan()` 先用 `CERT_EXT` 對**路徑**短路(`:221`),把樣本放成檔名會走到副檔名那條路,**測不到 regex**。

> ⚠ **本節這三行原本把那三條的 pattern 寫成字面,刀三 commit 被權威層擋下**(訊息點名本檔 `:35` `:37` `:86`)。**同一個陷阱在本票裡連中三次**:元測試的註解一次、票面兩次。⇒ 判準是「**任何進版控的檔案**都不得含那三條的字面」,不只測試檔。已改寫為敘述形式。
4. **缺樣本要紅,不能 skip。** skip 的話這條元測試就變成「有樣本的都過」,而那正是它要修的病。

---

## 五、未證明格:`53` 是不是封閉規格

| 命題 | 狀態 |
|---|---|
| 新格式金鑰**在本機這一把**是 `AQ.` + 50 = 53 字 | **已證明**(桌機 9/5 實測 `.env` 值長 53、前綴 `AQ.`;本輪偵察的遮罩回報 `***已遮罩 53 字***`) |
| **所有**新格式金鑰都是 53 字(長度為規格固定) | **未證明** |

**依據只有一個樣本。** 依 CLAUDE.md「一個從單一樣本挑出來的指標,涵蓋率等於那一個樣本」,現在**沒有資格宣稱它封閉**,所以本票不用 `{50}`。

**裁決端附註(逐字轉錄,標明來源與強度)**:裁決端網搜得到「新格式 53 字 / 舊 39 字」的說法,**未經機器驗證**,不作為本票的判定依據,只記錄在此。

**到期條件**:拿到**第二個獨立來源**(官方文件、或第二把來源不同的鑰)之後,重新裁「要不要收成 `\bAQ\.[A-Za-z0-9_\-]{50}\b`」。在那之前開放下限是**已知的、寫下來的**寬,不是疏忽。

---

## 六、manifest 查證結果

查法:`manifest.py` 本人解析,不是我讀表推的。

```
.claude/portable/leak-patterns.txt     mark=copy      best_entry=('.claude/portable/', 'copy')    explicit=copy
tests/test_leak_scan.py                mark=copy      best_entry=('tests/test_leak_scan.py', 'copy') explicit=copy
.claude/portable/leak_scan.py          mark=copy      best_entry=('.claude/portable/', 'copy')    explicit=copy
```

| 檔案 | 標記 | 來源行 | 形式 |
|---|---|---|---|
| `.claude/portable/leak-patterns.txt` | **copy** | `.agents/portable-manifest.txt:64` `.claude/portable/               copy` | **繼承目錄前綴**,無自己的明列行 |
| `tests/test_leak_scan.py` | **copy** | `.agents/portable-manifest.txt:108` `tests/test_leak_scan.py         copy` | **明列** |

**兩檔都是 `copy` ⇒ 下游收得到,不需要先改 manifest,本票不停。**

⚠ **一個要記下來但本票不動的事**:`leak-patterns.txt` 的 `copy` 是**繼承**來的。同一個目錄底下已經有兩筆更具體的 `skip`(`:339` `__pycache__/`、`:356` `mcp_server.py`)—— 也就是說「最長前綴者勝」這條規則**已經在這個目錄裡被用來翻案過兩次**。今天沒問題;**哪天有人為別的理由給 `.claude/portable/` 底下某個 `.txt` 加一筆 skip,這條洩漏規則會靜默地不出貨**,而 manifest 標記本身不會叫。要不要給它一行明列的 `copy`(讓它不依賴繼承),是另一件事,**本票不裁**。

---

## 七、站別(引 `.agents/pipeline-stages.yaml`,只報站名,不改 `pipeline.json`)

`gate.stage_allows_src_write()` 實測(讀的就是那份 yaml):

```
idle       allows_src_write=False
grill      allows_src_write=False
spec       allows_src_write=False
tickets    allows_src_write=False
research   allows_src_write=True     (src_write_scope: research/)
implement  allows_src_write=True
review     allows_src_write=False
arch       allows_src_write=False
```

⇒ **寫生產原始碼的站只有 `implement`**(`research` 綁 `research/` 路徑,與本票無關)。

### 但這兩個檔在 `gate.py` 眼中都不是原始碼

`gate.is_source_path()` 實測:

```
.claude/portable/leak-patterns.txt       is_source_path=False
tests/test_leak_scan.py                  is_source_path=False
.claude/portable/leak_scan.py            is_source_path=True
```

原因逐一對得上黑名單:

- `tests/test_leak_scan.py` → 第一段 `tests` 在 `NON_SOURCE_DIRS`(實測含 `tests`)
- `.claude/portable/leak-patterns.txt` → 副檔名 `.txt` 在 `NON_SOURCE_EXT`

**所以 R2 對這兩個檔都不生效 —— 任何站(含 `idle`)都寫得進去。**

| 要寫什麼 | R2 管不管 | 站別 |
|---|---|---|
| `tests/test_leak_scan.py`(紅燈) | **不管** | 閘門無要求;流程紀律上紅燈屬 `implement`(`skill: implement` → 內部走 `/tdd`) |
| `.claude/portable/leak-patterns.txt`(實作) | **不管** | 同上 |
| 若本票最後動到 `.claude/portable/leak_scan.py` | **管**(`is_source_path=True`) | **必須 `implement`** |

**建議:整票都在 `implement` 做**,理由不是閘門逼的,是紅燈/綠燈的順序要有人守,而那個順序住在 `implement` 的 skill 裡。**此處只報站名,`pipeline.json` 未動,切站由裁決者。**

### ⚠ 順帶發現(本票不修,只記)

**`leak-patterns.txt` 裝的是判定邏輯本身(規則清單),而它靠 `.txt` 這個副檔名落在 R2 的非原始碼清單外。** 這正是 CLAUDE.md 那條常駐檢查項的形狀:「任何要進非原始碼清單的目錄,先問……它會不會裝著判定邏輯」(`F-011` / `F-021` 一脈)。

差別在於這次不是**目錄**而是**副檔名**,而副檔名清單當初的判準大概是「文件不是碼」—— 對 `.md` 成立,對一個**每一行都是 regex 的 `.txt`** 不成立。

**本票不動它**,因為改 `NON_SOURCE_EXT` 的爆炸半徑遠大於本票(所有 `.txt`),而且**現在動它會讓本票自己寫不進那個檔**。記在這裡是為了它有一個位置,不是為了處理掉它 —— 依 CLAUDE.md:「除了這段文字之外,還有什麼在管它?」**答案目前是:沒有。** 要處理就得開票。

---

## 八、範圍與切回

**刀次(預計)**:

| 刀 | 內容 | 產物 |
|---|---|---|
| 一 | 本票面立案 | 本檔 |
| 二 | **紅燈**:元測試 + `AQ.` 正控 + 反控,**先紅**(現有 4 條無正對照者會一起紅) | `tests/test_leak_scan.py` |
| 三 | **綠燈**:`leak-patterns.txt` 加 `AQ.` 那條,並補齊那 4 條的正樣本 | `.claude/portable/leak-patterns.txt` + 測試表 |
| 四 | 三層驗收(UNIT / CLEAN / REAL)+ 帳本 | `.dev/` |

**切回條件(裁決逐字)**:**範圍超過一小時 → 切回只補 `AQ.` 一條並回報**,元測試另開票。

**本段(刀一)只建票面,未動 `src`、未動 `tests`、未 commit。**

---

## 九、落地紀錄(2026-09-05)

> **刀次與第八節的規劃對不上,這裡照實記。** 第八節把「票面立案」算成刀一;
> 實際執行的裁決把刀次重編為**紅燈 / 轉綠 / CLEAN+REAL 三刀**,票面立案併進刀三。
> 不改第八節(`F-036`:舊文不刪)。

| 刀 | sha | 內容 |
|---|---|---|
| 一 | `11eaa3a` | 紅燈:元測試 + AQ. 正反控,只動 `tests/test_leak_scan.py` |
| 二 | `c2bf47f` | 轉綠:`leak-patterns.txt` 加 AQ. 那條 + 補四條樣本 |
| 三 | `7491ecd` | CLEAN / REAL 落地紀錄(本節)+ 票面入版控 |
| 四 | 本 commit | `F-161` 進 friction log;`leak-patterns.txt` 檔頭加「加一條規則要配什麼」;狀態行收票 |

### 三層計數總表(預測 vs 實測,基準一併寫)

| 層 | 基準 | 預測 | 實測 | 差 |
|---|---|---|---|---|
| **UNIT** 全套 collected | `973ddc2` 的 1313 | 1313 + 13 = **1326** | **1326 passed, 3 skipped, 3 xfailed** | **0** |
| **UNIT** 單檔 `test_leak_scan.py` | 刀一收集 57 | 58 | **58 passed** | **0** |
| **CLEAN** 淨室 collected | `973ddc2` 筆電淨室 1197 passed + 3 skipped = 1200 | 1200 + 13 = **1213** | **1210 passed + 3 skipped = 1213** | **0** |
| `load_patterns()` 通用組長度 | `973ddc2` 的 10 | 11 | **11** | **0** |
| **REAL** | —— | 權威層擋下、HEAD 不動 | **擋下,HEAD 仍 `c2bf47f`** | —— |

新增 13 的拆法:元測試 `parametrize` **11 個參數** + AQ. 正控 **1** + AQ. 反控 **1**。

### 九之一、UNIT

刀一紅燈 **5 條**(預期即此):
```
FAILED tests/test_leak_scan.py::test_every_generic_pattern_has_a_positive_control[\\bsk-[A-Za-z0-9]{16,}]
FAILED tests/test_leak_scan.py::test_every_generic_pattern_has_a_positive_control[\\bgithub_pat_[A-Za-z0-9_]{20,}]
FAILED tests/test_leak_scan.py::test_every_generic_pattern_has_a_positive_control[\\bAKIA[0-9A-Z]{16}\\b]
FAILED tests/test_leak_scan.py::test_every_generic_pattern_has_a_positive_control[\\bxox[baprs]-[A-Za-z0-9-]{10,}]
FAILED tests/test_leak_scan.py::test_the_new_google_key_shape_is_caught
5 failed, 52 passed in 3.60s
```

刀二全綠:單檔 `58 passed`;全套 **1326 passed, 3 skipped, 3 xfailed**。

**計數(先算後比,`F-109`)**:預測 `1313 + 13 = 1326`(基準:`973ddc2` 的全套 1313;新增 13 = 元測試 11 個參數 + AQ. 正控 + AQ. 反控)⇒ **實測 1326,中**。
`load_patterns()` 通用組長度 **11**(以 `973ddc2` 的 10 為底,+1)。

### 九之二、CLEAN

```
=== 框架自己的測試,在這個新 repo 裡跑一次 ===
    1210 passed, 3 skipped, 3 xfailed in 78.03s (0:01:18)

全部 9 條規則各擋下一次,權威層偵測正常,框架測試在新 repo 全綠。
```

**預測 `1200 + 13 = 1213` collected(基準:`973ddc2` 筆電淨室 `1197 passed, 3 skipped`)⇒ 實測 `1210 passed + 3 skipped = 1213`,中。**

⇒ **兩個 `copy` 標記兌現了**:新規則與新測試**真的被複製進全新安裝的 repo**,而且在那裡跑得起來。標記是宣告,這一格才是證據。

### 九之三、REAL —— 權威層活體負控

做法:`.scratch/ticket-108-real/leak-probe.env` 放一行 `AQ.` 開頭 + 50 個 `A`(**不是真金鑰**),`git add -f` 後真的 `git commit` 一次。

**原始輸出(逐字)**:
```
[洩漏偵測] 這些檔案含個人身分或機密,擋下 commit:

  .scratch/ticket-108-real/leak-probe.env:4
     命中 pattern:\bAQ\.[A-Za-z0-9_\-]{40,}
     內容:***整行已遮罩(同一行 2 條命中,分段遮罩可拼回)***
  .scratch/ticket-108-real/leak-probe.env:4
     命中 pattern:個人 pattern #19(不顯示內容)
     內容:***整行已遮罩(同一行 2 條命中,分段遮罩可拼回)***

乾淨的歷史要在這條規則底下誕生 —— 先把上面的洗掉再 commit。
```

`git rev-parse --short HEAD` 在那之後仍是 `c2bf47f` ⇒ **commit 真的沒成立**,不是印了訊息還放行。已 `git reset` 退出 staging;探針檔留在 `.scratch/`(gitignored)給裁決者手清。

**三件事一次證到**:

1. 權威層(`.githooks/pre-commit` 的 leak_scan 那一段)**真的被呼叫**,而且擋得下。
2. 擋下訊息**點名新那條 pattern**,不是被別條順手接住 —— 這是「本票的規則在生產路徑上活著」的直接證據。
3. **順帶收到遮罩路徑的實測**:同一行同時打中通用新規則與個人 pattern #19(裁決者本機黑名單那一行形狀),於是引擎走**整行遮罩**分支(票 32 的「分段遮罩可拼回 ⇒ 對不回去就不猜」)。⇒ 個人清單那層**沒有因為通用規則補上而變成多餘**,兩層都在。

### 九之四、刀一實測收到的一條(已寫進測試檔註解)

元測試那段註解**原本把憑證那三條的 pattern 寫成字面當例子**,`test_the_shipped_tree_is_clean` **當場紅**,擋下訊息點名的就是**那幾行註解**本身。

> **連解釋這條陷阱的句子都會踩到它。**

已改寫為不含字面的敘述,該條轉綠。這是本檔頭那條紀律(「所有偵測樣本都是組裝的」)第一次在**註解**上被機器執行到 —— 紀律原本只被理解成管樣本。

### 九之五、⚠ 仍未關的缺口(本票範圍外,不是留白)

| 缺口 | 現況 |
|---|---|
| 元測試只驗**一個方向**(「pattern 都有樣本嗎」) | 反方向(刪掉 pattern 後表裡留下孤兒樣本)**沒有機器在管**。CLAUDE.md「驗兩個方向」的判準適用,但不在本票裁決範圍 —— 已寫進測試檔註解 |
| `53` 是不是封閉規格 | **仍未證明**(單一樣本)。見第五節的到期條件 |
| `leak-patterns.txt` 靠 `.txt` 落在 R2 非原始碼清單外 | **未動**。見第七節 |
| 「pattern 字面不得進版控」在**寫的當下**沒有機器會叫 | 刀四把規矩從測試檔檔頭搬到 `leak-patterns.txt` 檔頭(加規則的人一定會打開那個檔),但**守它的仍然只有 commit 時的擋下** —— 前哨與 UNIT 都走 `git ls-files`,看不到未追蹤的檔。⇒ **下次仍會是 `git commit` 才發現**(`F-161` 末節) |
