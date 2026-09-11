# 票 132 —— `leak_scan --staged` 讀工作樹,不讀 index:洩漏偵測可被 add-then-revert 繞過

**狀態**:立案 → 紅燈 → 實作 → 收工(同一輪走完)。
**嚴重性**:**最高**。直接關係到框架的核心賣點 —— 洩漏偵測不能被繞過,
而這一條**在權威層**(`.githooks/pre-commit` 第一段),繞過之後**沒有第二道**。
**發現於**:2026-09-11,上游桌機,HEAD `7ed86c7`。
**來源**:**總指揮端第三輪 arch 診斷,GPT 唯讀審查 + 記憶體探針驗證**
(GPT 在一個**丟棄式臨時 clone** 上跑完攻擊路徑;本窗未重跑那次手動實驗 —— 見「獨立性」)。
**修法裁決**:**A 案**(Jeff 已核准)—— pre-commit 這條掃描路徑改讀 staging 區內容,
用 `git show :<路徑>` 或等效 plumbing 拿 staged blob,不再讀工作目錄。
**時鐘**:**已經到期**。這不是「什麼時候會咬人」,是「**現在任何一個 commit 都可以帶秘密進歷史**」——
而 `.claude/portable/` 在 portable-manifest 標 `copy`,所以**每一個安裝過的下游都帶著同一個洞**。
秘密一旦進歷史就只能改寫歷史清洗(見 `docs/adr/F-0015`),成本與時間成正比。

---

## 現象

`leak_scan --staged`(pre-commit 的第一段)**檔名來自 index,內容來自工作樹**。
兩份對象不同,而**不同的那一刻沒有任何東西會說話**。

攻擊路徑(三步,不需要任何特殊權限、不需要 `--no-verify`):

| 步 | 動作 | 此刻 index | 此刻工作樹 |
|---|---|---|---|
| 1 | `git add <含機敏內容的檔>` | **機敏版** | 機敏版 |
| 2 | 把工作樹那個檔改回乾淨版本(**不重新 `add`**) | **機敏版** | 乾淨版 |
| 3 | `git commit` | **機敏版進歷史** | 乾淨版 |

第 3 步的 pre-commit:
`staged_paths()` 回報「這個檔要掃」(對),
`read_text()` 打開**工作樹**那一份、看到乾淨版、沒命中,
`scan()` 回 `0`,`|| exit 1` 不觸發 → **放行,且零告警**。

而 `git commit` 寫進歷史的是 index 那一份 —— **機敏版**。

---

## 證據(行號,本窗從本機檔案讀出)

### 一、檔名來自 index —— 對的那一半

```
.claude/portable/leak_scan.py:304     rels = scanner.staged_paths(cwd=ROOT, gitlinks=gitlinks)
.claude/portable/scanner.py:409       out = subprocess.run(["git", "diff", "--cached", "-z", "--name-only",
.claude/portable/scanner.py:410                             "--diff-filter=ACM"], capture_output=True, cwd=cwd)
```

### 二、內容來自工作樹 —— 錯的那一半

```
.claude/portable/leak_scan.py:310     paths = [os.path.join(ROOT, p.replace("/", os.sep)) for p in rels]
                                      ^^^ index 的相對路徑被接成【工作樹的絕對路徑】
.claude/portable/leak_scan.py:225     hits = certs + scanner.scan_paths(rest, groups, root=ROOT,
.claude/portable/scanner.py:493           text, why = read_text(p)
.claude/portable/scanner.py:280           with io.open(path, "rb") as f:
                                          ^^^ 檔案系統。index 在這一行完全不存在
```

`:310` 是接縫。它把一個**index 的座標**轉成一個**檔案系統的座標**,
而轉換本身合法(路徑字串是對的)—— 錯的是**轉換之後再也沒有人記得那個座標原本指的是 index**。

### 三、⚠ 這條判準**本 repo 已經寫下來了**,逐字,而且就在權威層的另一支檔案裡

`.claude/hooks/gate.py:1957-1975`:

```python
def staged_blob(rel_path):
    """index 裡的那些位元組(`git show :<path>`)。取不到回 `None`。

    **為什麼不是工作樹**:commit 要判的是**要進 commit 的那一份**。
    工作樹與 index 可以不同(`git add` 之後又改了一次),而讀錯對象的失敗方式是
    **靜默的** —— 兩者多數時候一樣,所以日常與測試都不會發現,只有在
    「先 add 一份乾淨的、再把工作樹改壞」時才漏,而那正是要防的形狀
    (票 07 / F-046 那條「判定對象」的判準換到提交時點)。

    **取不到一律 `None`,呼叫端不得退回工作樹** —— 退回去就是判錯對象,
    而且是往 fail-open 的方向錯。
    """
```

**那段 docstring 是本票的完整內容,包含攻擊步驟(「先 add 一份乾淨的、再把工作樹改壞」)。**
它寫在 `staged_blob` 上,而 `staged_blob` 目前**只有一個消費者**:
`upstream_identical_staged()`(R2 的內容豁免,票 10)。

```
$ grep -n "staged_blob" .claude/hooks/gate.py
1957:def staged_blob(rel_path):
2002:    raw = staged_blob(rel_path)
```

⇒ **一個消費者。** R1、R8、R9、R6、R5、以及 `leak_scan` 整條,全部還在讀工作樹。

> 這是 `CLAUDE.md` 逐字那一條的第 n 次:
> **「同一份判準寫在 A 模組的註解裡,不會讓 B 模組變安全 —— 註解不是機制。」**
> 而它比 `F-086` 更難察覺一階:F-086 的判準寫在「隔壁模組」,
> 本則的判準寫在**同一支檔案、同一層、上下相隔三百行**,
> 且**已經被正確實作過一次** —— 所以搜「有沒有人想過這件事」會搜到,
> 而**搜到的那一個正是唯一被守住的那一格**。

### 四、獨立性(照 `CLAUDE.md`「材料從哪來」那條逐格交代)

| 輸入 | 來源 | 獨立嗎 |
|---|---|---|
| **命題**(讀工作樹不讀 index) | GPT 唯讀審查 + 記憶體探針,丟棄式臨時 clone | 外部 |
| **行號**(`leak_scan.py:304`、`scanner.py:280`、`:493`) | **本窗**從本機檔案 `sed -n` 讀出,與 GPT 給的數字**各自產生後相符** | ✅ 兩個來源 |
| **`git show :<path>` 語法可用** | **本窗**對本機真 git 跑 `git rev-parse :0:CLAUDE.md` → `0b157bcc…`;`git cat-file blob :0:.agents/pipeline-stages.yaml` → 真內容;`:0:no-such-file.txt` → `rc=128` | ✅ 產生端 |
| **攻擊路徑會放行** | ⚠ **本輪由紅燈測試量**(見下),不是引用 GPT 那次 | ✅ 本機、自己的工具 |
| **判準本身** | `gate.py:1957` 的 docstring,**本 repo 自己寫的** | ⚠ 同一個 repo,但它是**產生端**(那支函式就是照它寫的) |

**本窗沒有重跑 GPT 那次手動實驗**(Jeff 明示不必踩雷)。
取代它的不是「相信」,是**把同一個實驗寫成一支會自己跑的紅燈測試** ——
所以「會放行」這件事在本票裡有**本機的、可重跑的**量測,不是轉述。

---

## 為什麼要緊

**一、它在權威層,而權威層沒有下一道。**
`CLAUDE.md`:「pre-commit 為唯一權威判定」。
前哨(`gate.py` PreToolUse)看的是**工具呼叫**,而這個繞過**不需要任何被守的工具呼叫** ——
`git add` 與編輯檔案都是日常動作,前哨沒有理由擋。
所以這不是「繞過前哨仍會在 commit 被擋」那個形狀,**它在 commit 那一刻也不會被擋**。

**二、失敗方向是靜默 fail-open,而本檔案的整份 docstring 都在防這件事。**
`scanner.py:18-20` 逐字:「掃描器失效的方向是**靜默放行**,所以本檔一切『不確定』往擋的方向倒」。
這次不是「不確定」—— 是**確定地量錯了對象**,而量錯對象比量不到更難發現:
它會回一個**看起來完全正常的乾淨結果**。

**三、不需要惡意。** 最容易的觸發不是攻擊,是**日常**:
`git add` 之後想起要把 token 換成佔位符、改完忘了重新 `add`。
此時人以為「我已經清掉了而且 pre-commit 也綠了」——
**兩個信號都在說沒事,而秘密已經在 index 裡等著進歷史。**
(反過來的那一半更毒:`git add` 乾淨版 → 貼回真 token 測一下 → commit,
index 是乾淨的、歷史也乾淨,**於是這個洞在這個方向上完全無害** ——
它只在一個方向錯,所以日常不會撞到它。)

**四、`.claude/portable/` 標 `copy` ⇒ 每一個下游都有。**
`.agents/portable-manifest.txt` 把 `scanner.py` / `leak_scan.py` 標 `copy`,
⇒ 這不是「上游的一個缺陷」,是**已經出貨的缺陷**。

---

## 修法(A 案,已核准)

**位置:換位元組的來源,不換判定。**

`read_text()` 目前做兩件事:① 拿位元組 ② 依序解碼(票 109/110 的 BOM 嗅探、
UTF-16/32、可讀性檢查、fail-closed 出口)。**只有 ① 錯**。
所以把 ② 抽成 `decode_bytes(raw)`,①' 加一支 `staged_blob()`;
`read_text()` 的**公開簽名與行為一個字不動**。

```
read_text(path)          = 工作樹位元組 + decode_bytes      ← 一個字不動
read_staged_text(rel)    = index 位元組  + decode_bytes      ← 新增
```

**共用 `decode_bytes` 是必要條件,不是整潔。** 另寫一套解碼 =
票 109 / 110 修的 UTF-16 / UTF-32 盲區在**新那條路上原地復活**,
而那條路正是唯一會在 commit 跑的那條。**兩份實作會分岔,而分岔的方向沒有人會發現。**

**`scan_paths` 加一個「來源」參數,不分岔成兩支函式。**
分岔的話 `scan_paths` 裡那整段遮罩邏輯(票 32 / F-066 / F-067 的四種比對面聯集、
整行遮罩、`unmappable` 判定)就有兩份 —— 同上,分岔會靜默。
參數是 `reader`(一個 `(abs_path, rel) -> (text, why)` 的可呼叫物),預設 `None` = 工作樹。

### ⚠ `--review` 不受影響 —— 這一格是動手前被要求先查證的那一格

**查證結果:`read_text` / `scan_paths` 確實被 `--review` 共用,
但「來源」要綁的不是 `--review`,是 `--staged`。**

| 入口 | 路徑從哪來 | 內容該從哪來 | 誰決定 |
|---|---|---|---|
| `--staged`(pre-commit) | index | **index** | **本票改這一格** |
| `<檔案...>`(手動掃) | 命令列 | 工作樹 | 不動 |
| `--review <檔案...>`(公開稽核) | 命令列 | 工作樹 | 不動 |

理由:`--review` 的**設計目的是廣泛稽核目前工作樹狀態**,概念上沒有「暫存區」可比 ——
`.claude/portable/leak_scan.py:280` 的 docstring 與 `docs/adr/F-0015-…:527`
(「本 repo `HEAD` 當時的版本 / 審查模式 `--review`」)、
`docs/tickets/…/107-…:345`(`leak_scan.py --review README.md README.zh-TW.md`)
都顯示它一律**帶明確路徑**呼叫。
⇒ `--review` 是**副檔名政策 + 報告格式**的旗標,**從來不是來源旗標**,本票不讓它變成來源旗標。

**`--staged --review` 這個組合**(程式上合法)在本票之後的語意是:
來源 = index(因為 `--staged`),副檔名政策 = 白名單(因為 `--review`)。
兩個旗標各管一件事,**正交**。這是刻意的:把來源綁到 `--review` 上的話,
`--staged --review` 會變成「稽核 index」而 `--staged` 單獨用是「稽核工作樹」,
**同一個旗標在兩種組合下指不同的對象** —— 那正是本票要修的病的形狀。

### fail-closed(方向不變)

`git show :<path>` 取不到 → **不退回工作樹**,回 `(None, 理由)` →
`scan_paths` 既有那條路把它記成 `UNREADABLE` 命中 → **擋**。
`gate.py:1966` 的 docstring 逐字要求這件事:「**取不到一律 `None`,呼叫端不得退回工作樹**
—— 退回去就是判錯對象,而且是往 fail-open 的方向錯。」

### 附帶的語意改善(不是本票目標,但要記下來)

改讀 blob 之後,「staged 之後在工作樹被刪掉」的檔案**變得掃得到**
(現在會回報「讀不到檔案:…」並擋下,而那是誤擋 —— 那個檔的內容明明在 index 裡)。
方向是**涵蓋變大 + 誤擋變少**,兩邊都對。

---

## 紅燈先行

三支測試,**兩支正控一支反控**,假秘密字串一律取**現有測試語料庫已在用的組裝樣本**
(`_AWS = "AKIA" + ("Z" * 16)`,`tests/test_leak_scan.py:768` / `tests/test_scanner.py:751` 已在用,
`SAMPLES` 表的 `\bAKIA[0-9A-Z]{16}\b` 那一格對著它,`test_every_generic_pattern_has_a_positive_control`
每次跑都在證明它真的命中一條**已配置的**規則)。
**不憑空發明新字串** —— 新字串命中的可能是巧合,而巧合的紅燈修好之後沒有人守得住它。

| # | 測試 | 檔案 | 主張 |
|---|---|---|---|
| 1 | `test_the_staged_blob_is_what_gets_scanned` | `tests/test_leak_scan.py` | **正控/端到端**:機敏版進 index、乾淨版留工作樹 → `main(["--staged"])` 必須回 `1` |
| 2 | `test_read_staged_text_reads_the_index_not_the_worktree` | `tests/test_scanner.py` | **正控/單元**:同一個 index-vs-工作樹分岔,問的是 `read_staged_text` 回哪一份位元組 |
| 3 | `test_a_file_whose_index_and_worktree_agree_is_unaffected` | `tests/test_leak_scan.py` | **反控**:index 與工作樹一致(乾淨)→ 仍回 `0`。少了它,「一律擋」也會讓 1、2 過,而那是把 pre-commit 變成永遠紅 |

反控的必要性照 `tests/test_leak_scan.py:269-277` 的既有形狀
(「**負控**:掃描面不得被這次過濾弄小。少了它,『staged 一律回空』也會讓上面兩條過」)。

---

## 同類入口(**收工前追查的那一節 —— 要 Jeff 裁**)

GPT 原話「多項內容檢查仍讀工作樹」是**複數**,查證結果:**它說得對,而且不只一處。**
以下是 `.githooks/pre-commit` 第二段(`gate.py --pre-commit`)裡**每一個讀檔內容做判斷**的點,
逐一標明對象。

**判準**(先寫判準再看表,照 `CLAUDE.md` 批次核准那條):
一個檢查**可被 add-then-revert 繞過**,當且僅當
① 它的判定吃檔案內容,且 ② 那份內容來自工作樹,且 ③ 那個檔可以出現在一次 commit 裡。
三個都成立才算同族;少任何一個都不算(列出來讓人自己看得出來)。

| 規則 / 檢查 | 讀內容的那一行 | 對象 | ① | ② | ③ | 同族? |
|---|---|---|---|---|---|---|
| **`leak_scan --staged`** | `scanner.py:280` | 工作樹 | ✅ | ✅ | ✅ | **本票本體** |
| **R1**(規格書禁含程式碼) | `gate.py:2154` | 工作樹 | ✅ | ✅ | ✅ | **是** |
| **R8**(生產碼不得 import `research/`) | `gate.py:2293` | 工作樹 | ✅ | ✅ | ✅ | **是** |
| **R9**(friction log 撞號) | `gate.py:1559` | 工作樹 | ✅ | ✅ | ✅ | **是** |
| **R6**(紅燈豁免清單) | `gate.py:1815`(清單)、`gate.py:76`(go-live sha) | 工作樹 | ✅ | ✅ | ✅ | **是**(⚠ 見下,這一格最毒) |
| **R5**(`to-spec` 覆寫掛載點) | `gate.py:3159` | 工作樹 | ✅ | ✅ | ✅ | **是** |
| **R5**(`code-review` 第三軸掛載點) | `gate.py:3184` | 工作樹 | ✅ | ✅ | ✅ | **是** |
| **R4**(skill 鏡像一致) | `gate.py:3068-3069` | 工作樹兩邊 | ✅ | ✅ | ⚠ 鏡像已 gitignore | **半個**(正典側成立,鏡像側不進 commit) |
| **R2**(站別) | 無(純路徑判定) | 路徑來自 index | ❌ | — | — | 否 |
| **R2 內容豁免**(票 10) | `gate.py:2002` → `staged_blob` | **index** | ✅ | ❌ | ✅ | **否 —— 唯一已經修對的那一格** |
| R3 前半(測試檔存在) | `os.path.exists` | 工作樹 | ❌(不吃內容) | — | — | 否(另一個形狀,見下) |
| R3 後半(紅燈紀錄) | `gate.py:1738`(`.dev/`)+ `head_blob`(HEAD) | `.dev/` 不進版控 / HEAD | ✅ | ⚠ | ❌ | 否 |

**⚠ R6 那一格為什麼最毒**:R6 的整個存在理由是「**無法自我服務**」——
`gate.py:1801-1812` 逐字:「凍結清單則進不去:每一項都必須在 `LEGACY_GO_LIVE` 的樹裡找得到,
**偽造需要改寫歷史**」。而 add-then-revert **不需要改寫歷史**:
`git add` 一份加了條目的清單 → 工作樹改回原樣 → R6 讀工作樹、看到原樣、綠 →
commit 進去的是**加了條目的那一份**。
⇒ **那句「偽造需要改寫歷史」在今天不成立。** 這一格不是「還有一個洞」,
是**一條規則的唯一正當性被同一個機制抽掉了**。

**要裁的事**(A 還是 B,差別寫在下面):

- **A —— 本票只修 `leak_scan`,其餘七格另開一張票(建議)**
  - 代價:R1 / R6 / R8 / R9 / R5 在這張票收工之後**仍然可被繞過**,而且**已經被寫下來了**
    (寫下來的風險偽裝成處置 —— `CLAUDE.md` 那一條;本票的存在不會讓它們變安全)。
  - 好處:本票的紅燈/綠燈邊界乾淨(一個接縫、三支測試);
    `gate.py` 是權威層本體 + 有 R2 自我修改豁免,動它的爆炸半徑與 `portable/` 不同,
    值得一張自己的票與自己的紅燈。
  - **附帶條件**:那張票要**現在就開**、帶時鐘,不是「記得去開」——
    祈使句沒有主詞(`F-110`)。
- **B —— 一票全修**
  - 代價:一次動 `scanner.py` + `leak_scan.py` + `gate.py` 三支,其中 `gate.py` 有 8 個判定點;
    紅燈要一次寫 ~9 支,而**任一支寫錯會把權威層擋死**(fail-closed 的方向是對的,
    擋住的卻是做對事的人 —— 那種規則最後會被整條關掉)。
  - 好處:洞一次關完,沒有「中間狀態」。

**本窗建議 A**,理由是爆炸半徑:`gate.py` 擋死 = 沒有人能 commit,包含修它的那一次。
但 **A 的代價必須被明確接受,不是默認** —— 接受 A 就等於接受
「R6 的『偽造需要改寫歷史』這句話在下一張票收工之前是假的」。

---

## 未證明 / 已知邊界

- **本窗沒有手動重跑 GPT 那次 add-then-revert 實驗**(Jeff 明示不必)。
  ⇒ 「會放行」在本票裡的證據是**紅燈測試**(本機、可重跑),不是那次手動實驗。
- **沒有量下游。** `scanner.py` / `leak_scan.py` 標 `copy` ⇒ 推定每個下游都有同一個洞,
  **但那是推論,沒有去兩個下游身上跑**。修好之後要走同步路徑,而同步本身是票 01 的範圍。
- **沒有量 `git show :<path>` 在非 ASCII 檔名上的行為。**
  `staged_paths` 用 `-z` 拿到的是解碼後的 UTF-8 路徑(F-064),再接成 `:<path>` 交給 git ——
  這條路徑**本票未測**。`tests/test_cjk_git_paths.py` 守的是清單那一半,不是內容那一半。
  ⚠ **這一格在收工時被補上了測試**,見下方「收工」。
- **沒有量 `core.autocrlf` 開啟時 blob 與工作樹行尾不同對 pattern 的影響。**
  推定無影響(要找的 pattern 全是 ASCII 且不跨行),**未量**。
- **R4 那個「半個」沒有量。** 鏡像目錄已 gitignore ⇒ 推定進不了 commit;
  正典側(`.agents/skills/`)進版控,所以 R4 的正典側**應該**同族 ——
  `gate.py:3068-3069` 兩邊都讀工作樹,但判定是「兩邊一不一致」,
  add-then-revert 能造出什麼結果**沒有推完**。

---

## 交叉引用

- **`gate.py:1957` `staged_blob()` / 票 10**(R2 內容豁免綁 staged 位元組)—— 判準的出處,唯一修對的那一格
- **票 07 / `F-046`**(R8 判編輯片段不判結果)—— 同一條「判定對象錯了」的判準,在寫入時點
- **票 109 / 110**(scanner 對 UTF-16 / UTF-32 盲)—— 本票必須共用 `decode_bytes` 的理由
- **票 106**(`leak_scan` 沒掃到任何東西卻回 0)—— 同一支檔案的上一個靜默 fail-open
- **票 42**(gitlink)—— `staged_paths` 兩份實作、不共用碼的理由
- **`docs/adr/F-0015`**(公開前要審歷史)—— 秘密進了歷史之後的成本
- **`F-082` / `F-085` / `F-086`**(修好一個偵測器要回頭重掃、判準寫在別處不算機制)
- **`F-110`**(祈使句沒有主詞)—— 上面「另開一張票」那一格為什麼要現在開

---

## 收工(2026-09-11,同一輪)

### 一、紅燈 —— **量到了,不是引用**

```
$ python -m pytest tests/test_leak_scan.py::TestTheStagedBlobIsWhatGetsScanned \
    tests/test_scanner.py::TestStagedBytesComeFromTheIndex -p no:randomly -q
...
FAILED tests/test_leak_scan.py::TestTheStagedBlobIsWhatGetsScanned::test_the_staged_blob_is_what_gets_scanned
FAILED tests/test_leak_scan.py::TestTheStagedBlobIsWhatGetsScanned::test_a_secret_only_in_the_worktree_is_not_blocked
FAILED tests/test_scanner.py::TestStagedBytesComeFromTheIndex::test_read_staged_text_reads_the_index_not_the_worktree
FAILED tests/test_scanner.py::TestStagedBytesComeFromTheIndex::test_a_cjk_path_survives_the_blob_lookup
FAILED tests/test_scanner.py::TestStagedBytesComeFromTheIndex::test_a_utf16_blob_is_decoded_by_the_same_ladder
FAILED tests/test_scanner.py::TestStagedBytesComeFromTheIndex::test_a_path_not_in_the_index_fails_closed
6 failed, 3 passed in 4.26s
```

**6 紅 3 綠,而哪三綠正是預測的那三綠** —— 三個反控
(`test_an_agreeing_clean_file_still_passes`、`test_an_agreeing_dirty_file_is_still_caught`、
`test_the_worktree_reader_is_unchanged`)修法之前本來就該是綠的。
**如果反控當時也是紅的,那代表紅燈語料本身壞了**,而不是缺陷存在。

本體那一格的原始斷言輸出:

```
$ python -X utf8 -m pytest "tests/test_leak_scan.py::TestTheStagedBlobIsWhatGetsScanned::test_the_staged_blob_is_what_gets_scanned" -p no:randomly -q
E       AssertionError: index 裡是機敏版、工作樹是乾淨版,`--staged` 回了 0 ——
E             掃的是工作樹,而進歷史的是 index 那一份。秘密偷渡成功,零告警。
E             stderr:[洩漏偵測/警告] 找不到個人 pattern 清單 …\none.local.txt —— 只用通用形狀掃…
E
E       assert 0 == 1

tests\test_leak_scan.py:1073: AssertionError
```

**`assert 0 == 1`** —— `0` 是放行,而 stderr 裡唯一的字是一句與本缺陷無關的
個人清單警告。**零告警**這件事是量到的,不是形容詞。

紅燈紀錄(`.dev/test-runs.jsonl`,**兩支實作檔各一筆**,票號吻合):

```
{"test_file": "tests/test_leak_scan.py", "time": "2026-09-11T08:04:24.870379+00:00", "result": "red",
 "failed_tests": ["TestTheStagedBlobIsWhatGetsScanned::test_the_staged_blob_is_what_gets_scanned",
                  "TestTheStagedBlobIsWhatGetsScanned::test_a_secret_only_in_the_worktree_is_not_blocked"],
 "impl_file": ".claude/portable/leak_scan.py", "impl_exists": true,
 "impl_hash": "b1310c9c50e6a0b96c006cf6cf65341940d38761a8c173a4ac43968893b3d32e", "ticket_id": "132"}
{"test_file": "tests/test_scanner.py", "time": "2026-09-11T08:04:24.870379+00:00", "result": "red",
 "failed_tests": ["TestStagedBytesComeFromTheIndex::test_read_staged_text_reads_the_index_not_the_worktree",
                  "TestStagedBytesComeFromTheIndex::test_a_cjk_path_survives_the_blob_lookup",
                  "TestStagedBytesComeFromTheIndex::test_a_utf16_blob_is_decoded_by_the_same_ladder",
                  "TestStagedBytesComeFromTheIndex::test_a_path_not_in_the_index_fails_closed"],
 "impl_file": ".claude/portable/scanner.py", "impl_exists": true,
 "impl_hash": "2736433a18be7e5e76210771bb7bfc732088b6dc778780edbbd357284da16460", "ticket_id": "132"}
```

`impl_hash` 是**改動前**的內容 ⇒ R3 後半(「紅燈對著改動前的碼發生」)成立,
不是事後補跑。

### 二、落地的檔案與行號

| 位置 | 做了什麼 |
|---|---|
| `.claude/portable/scanner.py:267` | **新** `decode_bytes(raw)` —— 票 109/110 那整套解碼階梯原封不動搬進來,一個位元組沒改 |
| `.claude/portable/scanner.py:346` | `read_text(path)` = 工作樹位元組 + `decode_bytes`。**公開簽名與行為未變**;docstring 加了「誰該用我、誰該用另一支」 |
| `.claude/portable/scanner.py:368` | **新** `staged_blob(rel, cwd=None)` → `(raw, None)` / `(None, 理由)`,`git cat-file blob :0:<path>` |
| `.claude/portable/scanner.py:421` | **新** `read_staged_text(rel, cwd=None)` = index 位元組 + **同一個** `decode_bytes` |
| `.claude/portable/scanner.py:567` | `scan_paths(..., reader=None)` —— 新增來源參數 |
| `.claude/portable/scanner.py:595` | `text, why = read(p, rel)`(原本是 `read_text(p)`)。**這一行就是接縫** |
| `.claude/portable/leak_scan.py:195` | **新** `staged_reader(abs_path, rel)` → `scanner.read_staged_text(rel, cwd=ROOT)` |
| `.claude/portable/leak_scan.py:205` | `scan(paths, review=False, staged=False)` —— 兩個旗標**正交** |
| `.claude/portable/leak_scan.py:243` | `reader=staged_reader if staged else None` |
| `.claude/portable/leak_scan.py:344` | `--staged` 那條路傳 `staged=True` |
| `tests/test_leak_scan.py` | `TestTheStagedBlobIsWhatGetsScanned`(2×2 真值表,4 條) |
| `tests/test_scanner.py` | `TestStagedBytesComeFromTheIndex`(5 條:index / 工作樹反控 / CJK 路徑 / UTF-16 共用解碼 / fail-closed) |

**指令形式與 `gate.py:1957` 那份刻意不同**(這裡 `git cat-file blob :0:<path>`,
那裡 `git show :<path>`),理由寫進 `staged_blob` 的 docstring:
plumbing 的輸出契約穩定、不吃 pager / textconv,`:0:` 明寫 stage 0 使衝突中的 index
fail-closed。**兩份不共用程式碼是票 42 的既有裁決**,但**字面不同這件事必須寫出來**,
否則下一個讀的人會以為其中一份是筆誤。

### 三、綠燈

```
$ python -X utf8 -m pytest tests/test_leak_scan.py::TestTheStagedBlobIsWhatGetsScanned \
    tests/test_scanner.py::TestStagedBytesComeFromTheIndex -p no:randomly -q
.........                                                                [100%]
9 passed in 17.12s
```

6 紅 → 0 紅,3 綠反控**保持綠**(反控從綠變紅的話,修法就是把偵測面弄小了)。

### 四、全套回歸

```
$ python -X utf8 -m pytest -q
2 failed, 1596 passed, 3 skipped, 3 xfailed in 315.49s (0:05:15)
```

**兩紅都不是本票造成的**,逐一交代(判準:那條測試的**輸入集合**裡有沒有本票改動的檔案):

| 紅 | 原因 | 歸屬 |
|---|---|---|
| `test_gate.py::TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce` | `assert not ['.claude/portable/g1_guard.py']` —— 本機 `.dev/test-runs.jsonl` 最早一筆是 `2026-09-04`,而 g1_guard 的排水發生在 `2026-08-14`,**那筆紅燈證據不在這台機器上** | **票 124 / `F-142`**,CI 已 `--deselect` |
| `test_upstream_manifest.py::test_every_tracked_file_is_classified` | `docs/agents/commander.md`、`docs/agents/handover.md` 沒有 manifest 標記 | **commit `992297a` 帶進來的**(建交班兩份)。`docs/agents/` 是逐檔列舉、不是目錄規則,所以新檔要各自標一筆 |

**不歸屬的證明是構造式的,不是感覺**:那兩條測試的輸入分別是
`.agents/legacy-no-redlight.txt` + `git ls-tree <go-live>` + `.dev/test-runs.jsonl`,
以及 `.agents/portable-manifest.txt` + `git ls-files`。
本票改動的檔案是這五個(`git status --porcelain`):

```
 M .claude/portable/leak_scan.py
 M .claude/portable/scanner.py
 M tests/test_leak_scan.py
 M tests/test_scanner.py
?? docs/tickets/framework-updates/132-leak-scan-reads-the-worktree-not-the-index.md
```

**兩個集合的交集是空的。**

> **⚠ 附帶發現,不在本票範圍,登記在此以免遺失(票 124 的材料)。**
> 票 124 的命題是「**桌機綠、筆電紅**」。**今天桌機也紅了。**
> 而 `docs/audits/2026-09-09-laptop-align-verify.md:528` 逐字寫著
> 「桌機那個 1583 是不是 passed 口徑,**本次未查證**」——
> 「桌機綠」這個前提**從頭到尾沒有被量過**,它來自一份裁決者提供、
> 且該審計自己標明未讀過的回報檔(`:522`)。
> ⇒ 今天這一次不是「桌機退化了」,更可能是**那個前提本來就不成立**。
> 兩種可能在結果上長得一樣,而**要分開它們需要那份回報檔**,本窗手上沒有。
> 這是 `F-111` 的形狀:**推論鏈的品質保證不了前提,而前提越自然,越不會被驗。**

### 五、兩層閘門在真實 staged 集合上的實跑

```
$ git add -A
$ python -X utf8 .claude/portable/leak_scan.py --staged    -> leak_scan-rc=0
$ python -X utf8 .claude/hooks/gate.py --pre-commit        -> gate-rc=0
```

**`rc=0` 在這裡不是「沒掃」**,推論寫出來讓人自己看:
5 個 staged 檔裡 `.claude/portable/leak_scan.py` 在 `SELF_PATHS` 被跳過,
**其餘 4 個都走了 `staged_reader`**;若 `staged_blob` 對它們失敗,
每一個都會變成 `UNREADABLE` 命中 ⇒ `rc` 會是 `1`。
**得到 0 ⇒ 那 4 個的 index blob 都真的被讀出來並掃過了。**
(這是推論;會放行/會擋的**量測**在第一、三節的 2×2 真值表裡。)

### 六、未證明(收工版,與立案版的差異已標出)

- ✅ **CJK 路徑往返** —— 立案時標未證明,**已補測試**
  (`test_a_cjk_path_survives_the_blob_lookup`,`docs/計畫/台股筆記.txt`)。
- ⚠ **symlink(mode 120000)的語意變了,未測。**
  舊路徑 `io.open()` 會**跟著連結**讀到目標檔的內容;
  新路徑 `cat-file blob` 拿到的是**連結目標字串本身**。
  新語意才是對的(進歷史的就是那個字串),但**沒有測**,
  而本機建不了 symlink(`tests/test_gate.py:451` 等三條 skip 的同一個理由)。
- ⚠ **`core.autocrlf` 的影響仍未量。** 本機系統層 `core.autocrlf=true`
  (`file:C:/Program Files/Git/etc/gitconfig`),所以 blob 是 LF、工作樹可能是 CRLF。
  推定無影響(pattern 全是 ASCII 且不跨行),**推定,沒量**。
- ⚠ **下游沒有量。** `copy` ⇒ 推定每個下游都有同一個洞、修好之後也都要收到,
  但沒去下游身上跑。同步走票 01 的路徑。
- ⚠ **`gate.py` 那七格沒有修**(見「同類入口」的 A/B 裁決)。
  **接受 A 就等於接受「R6 的『偽造需要改寫歷史』這句話在下一張票收工之前是假的」。**
