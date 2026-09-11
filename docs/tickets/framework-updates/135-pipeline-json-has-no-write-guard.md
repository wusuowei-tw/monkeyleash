# 票 135 —— `.dev/pipeline.json` 沒有任何守衛,而它決定紅燈記到哪一張票

**狀態**:**立案。只立案,不動工。** 沒有改 `gate.py`、沒有改任何許可清單、沒有寫測試。
**立案**:2026-09-11,上游桌機,HEAD `97e0b78`。
**來源**:裁決者今日的唯讀查證要求(起因見〈事件紀錄〉)。**行號全部是本輪從實檔查出來的。**
**friction 編號**:`F-165`。
**估工**:**待裁**(修法三個候選,本票不選)

> **⚠ 這張票的兩節是同一個根、兩個面:**
> **甲節** = **沒有守衛**(三層全靜默)。
> **乙節** = **許可的理由不成立**(R7 明列 `.dev/`,而它的理由對這個檔為假)。
> 甲是「沒有人管」,乙是「有人說過不必管,而那句話是錯的」。

---

## ⚠ 先寫清楚哪一部分**不是**新的

**`pipeline.json` 很脆弱、而它決定紅燈歸票 —— 這件事已經被記過一次。**

- **`F-163`**(`docs/agents/friction-log.md`):「`pipeline.json` 由人手改,
  而沒有任何東西驗它的**格式**」。實測:格式壞掉時 `gate.load_stage()` fail-closed 出聲,
  而 `redlight.current_ticket()` fail-silent,**紅燈照記、`ticket_id` 寫成 `null`**。
- **票 117**(狀態 `candidate`):同一件事的票。

**本票不重複那一面。** 新的是三件:

| | 已記錄(`F-163` / 票 117) | **本票新增** |
|---|---|---|
| 問的問題 | 這個檔**壞掉**時會怎樣 | **誰可以寫它** |
| 缺的東西 | 格式驗證 | **寫入守衛** |
| 觸發條件 | 人手改時打錯字 | **任何 agent 的任何一次寫入** |

⇒ 兩張票**不可合併**:117 加一個格式檢查也**完全不會**擋住一次格式正確的未授權寫入。
**「格式對」與「該由誰寫」是兩個命題,而前者為真使後者更難察覺** ——
一次由 agent 寫出的、格式完美的 `pipeline.json` 在每一個讀取端都表現正常。

---

## 甲節 —— 沒有守衛(三層全靜默)

### 1. Write / Edit / MultiEdit:在任何規則之前就 `return None`

```
$ sed -n '133,134p' .claude/hooks/gate.py
NON_SOURCE_DIRS = {
    ".dev": "流程狀態與證據,不被執行",

$ sed -n '1794,1798p' .claude/hooks/gate.py
    top = r.split("/")[0] if "/" in r else ""
    return not (top in NON_SOURCE_DIRS
                or PROTOTYPE_RE.match(r)
                …

$ sed -n '2166,2167p' .claude/hooks/gate.py
    if not is_source_path(r):
        return None
```

`top == ".dev"` ⇒ `is_source_path()` 回 `False` ⇒ **`check()` 在 `gate.py:2166`
於任何規則之前 `return None`。** R1–R9 一條都沒有被評估。

⚠ **這不是 `.dev` 分類錯誤。** `.dev` 標非原始碼是對的(它不被執行)。
缺陷是**「不是原始碼」被用來回答「不必守」** —— 那是兩個問題。
這與 `CLAUDE.md` 的常駐檢查項逐字同形:
「任何要進非原始碼清單的目錄,先問兩件事 —— **它會不會裝著判定邏輯**
與**它會不會裝著唯一的觀測**」。`pipeline.json` 裝的是**判定的輸入**(站別與票號),
而那一問當初沒有被問到它身上。

### 2. Bash / PowerShell:R7 **明列許可**

```
$ sed -n '/^BASH_ALLOWED_TARGETS/,/^}/p' .claude/hooks/gate.py
BASH_ALLOWED_TARGETS = {
    "/dev/null": "丟棄輸出,不產生檔案 —— 只在解析後落在 repo 之外時適用",
    "/tmp/": "系統暫存 —— 只在解析後落在 repo 之外時適用",
    "scratchpad": "工作階段暫存目錄 —— 只在解析後落在 repo 之外時適用",
    ".dev/": "流程證據,由機制自己追加(append-only),不是人在編輯",
    "__pycache__": "位元碼,由直譯器產生",
    ".cache/": "快取,可重算",
    "build/": "建置產出物,不是來源",
}

$ grep -n "^OUTSIDE_REPO_ONLY" .claude/hooks/gate.py
OUTSIDE_REPO_ONLY = ("/dev/null", "/tmp/", "scratchpad")
```

`.dev/` 在許可清單裡,**而且不在 `OUTSIDE_REPO_ONLY` 裡**
⇒ **repo 內的 `.dev/` 寫入一樣許可。**(那三項才是「只有落在 repo 外才算」。)

### 3. G1:兩個條件都不符

**⚠ 底下兩段引文【已遮罩】,因此不得稱為逐字或原始**(`F-116` 的處置):
使用者層路徑含個人資料夾名,而本檔進版控 ——
`leak_scan` 的個人 pattern #20 在 commit 當場擋下了第一版票面(見〈事件紀錄〉末段)。
`<家目錄>` 代表被遮掉的那一段。

```
$ grep -n "command\|matcher" ~/.claude/settings.json          # 已遮罩
6:        "matcher": "Bash|PowerShell|Write|Edit|MultiEdit|NotebookEdit",
10:            "command": "python \"C:/Users/<家目錄>/.claude/hooks/g1_guard.py\""

$ sed -n '351p' .claude/portable/g1_guard.py        # 專案內的可攜副本
    """破壞性動詞 + 專案外的絕對路徑。回傳 (動詞, 路徑) 或 None。

$ sed -n '62,67p' .claude/portable/g1_guard.py
DESTRUCTIVE = re.compile(
    r"(?:^|[\s;&|(`])"
    r"(rm|rmdir|rd|del|erase|unlink|shred|srm|truncate|dd|mkfs|format"
    r"|Remove-Item|ri|Clear-Content|Clear-Item|Move-Item|mv"
    r"|rsync\s+[^|;]*--delete)"
```

第二級要求**破壞性動詞** **且** **專案外絕對路徑**。
寫 `pipeline.json` 既不是破壞性動詞(它是 `Write`,連 Bash 都不是),
路徑也在專案內 ⇒ **兩個條件都不符。**

⚠ **第一級(保護清單)的內容查不到** —— G1 擋住讀它自己。擋下訊息(**已遮罩,非原始**):
```
[G1/保護清單] 這個指令碰到受保護的路徑:C:\Users\<家目錄>\.claude\g1-protected.txt
     第一級無豁免,也不分讀寫 —— 判定不解析指令,因為解析會失敗,
     而失敗的解析就是洞。
```
**但有間接實證**:今日那兩次寫入**完全沒有觸發任何 G1 訊息**
⇒ `pipeline.json` 不在第一級清單上。(**這是實證不是讀到清單**,兩者不同。)

### 4. 測試:三處提及,**沒有一處守它**

```
$ grep -rn "pipeline" tests/*.py | grep -iv "pipeline-stages"
tests/test_gate.py:53:    (".dev/pipeline.json", "{}"),
tests/test_gate.py:3723:    def test_the_exemption_never_writes_pipeline_json(self, world, monkeypatch):
tests/test_canon_section.py:262:    assert git_ignores(".dev/pipeline.json"), …
```

逐一定性:

| 處 | 它實際斷言什麼 | 為什麼不算守衛 |
|---|---|---|
| `test_gate.py:53` | 它是 `CORPUS` 的一列,餵給 `test_coverage_no_rule_is_skipped_at_the_authoritative_layer` 與 `test_every_divergence_is_declared_by_its_rule` —— 那兩條比的是**前哨與權威層各自評估到的規則集合** | 對 `.dev/pipeline.json` **兩邊都是空集合** ⇒ 差集為空 ⇒ **恆真斷言,恆綠,什麼都沒驗**。判準見 `F-032`(套套邏輯的三種形狀)—— **語料出現在表裡,不代表有斷言問過它** |
| `test_gate.py:3723` | **閘門自己**的 R2 內容豁免不寫 `pipeline.json`(斷言位元組與 mtime 都不動) | 守的對象是 **`gate.py`**,**不是 agent**。它問「豁免有沒有偷偷開窗」,不問「誰可以寫這個檔」 |
| `test_canon_section.py:262` | `git_ignores(".dev/pipeline.json")` 為真 | **只保證它不進版控** |

### ★ 寫死在票面的一句

> **「被 `gitignore`」不等於「有東西在守」。這兩件事在本票任何一處都不得混寫。**

`gitignore` 回答的是「它會不會進版控」。它**不阻止任何寫入**、**不產生任何訊息**、
**不留下任何痕跡**。一個被忽略的檔案被改一百次,`git status` 一次都不會提。
⇒ 把「不進版控」讀成「受保護」,得到的結論與事實相反:
**不進版控使它更難察覺,因為連 `git diff` 都看不到那次改動。**

### 甲節的後果:紅燈歸票沒有保護

`pipeline.json` 的 `ticket_id` 是紅燈紀錄歸票的**唯一來源**:

```
$ grep -n "PIPELINE" .claude/hooks/redlight.py
41:PIPELINE = os.path.join(ROOT, ".dev", "pipeline.json")   # 紅燈發生時是哪一張票
```

而 R3 後半用票號判「這張票有沒有自己的紅燈」:

> `gate.py:redlight_missing` docstring 逐字:「**票號:每張票要有自己的紅燈。**
> 少了它,一筆舊紅燈只要該檔案之後沒被提交過就永久解鎖後續每一次修改 ——
> **方向會從「永遠不合格」翻成「永遠合格」。**」

⇒ **一個 agent 寫得動的檔案,決定了 R3 後半的歸屬判定。**
偽造一個票號不需要改 git 歷史,也不需要任何豁免。

---

## 乙節 —— 許可的理由不成立

R7 許可 `.dev/` 的理由**逐字**是:

> `"流程證據,由機制自己追加(append-only),不是人在編輯"`

把這句話的兩個子句拆開,對 `.dev/` 底下每一個檔逐一驗(**本輪實測寫入者**):

| 檔案 | 誰寫 | 「機制自己追加(append-only)」 | 「不是人在編輯」 |
|---|---|---|---|
| `gate-exemptions.jsonl` | `gate.py:2099 _append_jsonl(EXEMPTION_LOG, rec)` | ✅ 追加 | ✅ |
| `test-runs.jsonl` | `redlight.py:139 io.open(RUN_LOG, "a")` | ✅ 追加 | ✅ |
| `intercepts-*.jsonl` | `gate.py:2842` / `:2882 _append_jsonl` | ✅ 追加 | ✅ |
| 影子日誌 | `gate.py:2646 _append_jsonl(SHADOW_LOG, rec)` | ✅ 追加 | ✅ |
| `provenance.jsonl` | `sync.py:556 write_provenance`(`gate.py:1824` 註明「控制,不是證據」) | ✅ 追加 | ✅ |
| `known-chain-breaks.txt` | 人(判斷紀錄,進版控) | ❌ | ❌ |
| **`pipeline.json`** | `install.py:190`(**只在安裝時**);其後照 `CLAUDE.md` 是**使用者** | **❌ 覆寫** | **❌ 規矩說就是人在編輯** |

**⇒ 對 `pipeline.json`,那句理由的兩個子句都假。**

```
$ sed -n '188,192p' .claude/portable/install.py
    dev = os.path.join(target, ".dev")
    os.makedirs(dev, exist_ok=True)
    io.open(os.path.join(dev, "pipeline.json"), "w", encoding="utf-8", newline="\n").write(
        json.dumps({"current_stage": "idle", "feature": None,
                    "ticket_id": None, "updated": ""}, ensure_ascii=False, indent=2) + "\n")
```
`"w"` —— **覆寫,不是追加**。而 `CLAUDE.md` 與 `gate.py:2270` 都明文說之後由人改。

### ★ 一條許可覆蓋了一個它的理由不成立的對象,而沒有任何東西在驗那個理由

`gate.py` 對這件事有現成的自覺 —— `BASH_ALLOWED_TARGETS` 底下那段註解逐字:

> 「原本這件事只寫在理由欄的措辭裡(「在 repo 之外」),而比對**完全不驗它** ——
> 只問「路徑成分裡有沒有這個名字」…… **註解不是機制**(`F-086`):
> 要讓那句話生效,它得是程式讀得到的東西。」

**票 111 為前三項做了這件事**(拉出 `OUTSIDE_REPO_ONLY`,並用
`test_every_allowed_target_is_classified_inside_or_outside` 強制新增項要分類)。
**而 `append-only` 這個子句從來沒有被同樣對待** ——
它仍然只活在理由欄的措辭裡,**而 `.dev/` 底下混著兩種東西**。

⇒ **同一支檔案、同一份清單、同一個病,修了一個維度(位置)、沒修另一個(寫入方式)。**
這與 `F-085` 是同一條線:**修好一格之後,同檔同類的下一格沒有被回頭問。**

### ★ 與票 133 的對照:同族,不同面

| | 票 133 | **本票乙節** |
|---|---|---|
| 面 | **讀取面** —— 判定**讀**了工作樹那一份,而該讀 index | **許可面** —— 一條**寫入許可**覆蓋了一個它的理由不成立的對象 |
| 症狀 | 規則看錯東西 / 規則根本不啟動 | **寫入完全不被評估** |
| 共同根 | **一個判準只寫在散文裡,而比對不驗它** | 同 |

兩者不可互相取代:票 133 修完之後,`pipeline.json` 的寫入**仍然**沒有任何守衛;
本票修完之後,票 133 那 15 格**仍然**讀工作樹。

---

## 時鐘

**⚠ 不是「已經咬過人」—— 今天那次歸票是對的,零損害。**
`.dev/test-runs.jsonl` 今日兩筆紅燈紀錄的 `ticket_id` 都是 `"132"`,而那一輪做的就是票 132。
**寫下這一句是為了不讓時鐘看起來比實際緊** —— 一個誇大的時鐘會在第一次沒出事之後被整條忽略。

時鐘綁兩個**可觀察的觸發條件**:

1. **「批一開始產生紅燈紀錄之時」** —— 票 133 批一從現在起每一格都要紅燈先行,
   而每一筆紅燈紀錄的歸票都取自這個沒有守衛的檔。**那已經開始了。**
2. **「下一個新下游安裝之前」** —— `.claude/hooks/` 在 portable-manifest 標 `copy`:
```
$ grep -n "^.claude/hooks/" .agents/portable-manifest.txt
86:.claude/hooks/                  copy
440:.claude/hooks/__pycache__/    skip
```
   ⇒ **每一個裝過的下游都帶著同一個缺口**,而新裝一個就多一份。

---

## 修法方向(**立案不定死,列候選不裁**)

- **(a) 收窄 R7 的 `.dev/` 許可** —— 把 append-only 帳本與 `pipeline.json` 分開處理。
  形狀與票 111 拉出 `OUTSIDE_REPO_ONLY` 相同:把理由欄的措辭變成程式讀得到的分類,
  並用一條「新增項必須被分類」的測試守住。
  ⚠ **只擋 Bash 那一條路** —— Write / Edit 那條路在 `:2166` 就 `return None` 了,
  R7 完全碰不到它。**單獨做 (a) 會得到一個看起來修好了的半套。**
- **(b) 對 `pipeline.json` 的寫入加守衛。**
  ⚠ 先想清楚 `install.py:190` 那個**合法**寫入怎麼辦 —— 那是安裝器在建初始狀態,
  必須放行;而它跑的時候目標 repo 的閘門還沒接上,所以可能不在守衛的路徑上,
  **但這件事沒有查證過。**
- **(c) 讓紅燈歸票不依賴一個 agent 寫得動的檔。**
  這一條改的是**依賴關係**而不是加一道牆 —— 與 `F-110`「能用構造消掉的不要用紀律管」
  同方向,但它會動到 `redlight.py` 與 R3 後半的判定,**爆炸半徑最大**。

**★ 不在立案階段選。** 三條的代價不同軸:(a) 便宜但半套、(b) 完整但要處理安裝器、
(c) 結構正確但動到 R3。

---

## 事件紀錄(**照實寫,不美化**)

**2026-09-11,票 132 那一輪,本 VS session 自行寫了 `.dev/pipeline.json` 兩次:**

| # | 改了什麼 | 時間(UTC) | 區間怎麼來的 |
|---|---|---|---|
| 1 | `current_stage` `idle`→`implement`;`ticket_id` `null`→`"132"` | `06:35:23` 之後、`08:04:24` 之前 | 下界:當日第一筆 R7 攔截 `2026-09-11T06:35:23`;上界:紅燈紀錄 `08:04:24.870379` 已蓋著 `"ticket_id": "132"` |
| 2 | `current_stage` `implement`→`idle`;`ticket_id` `"132"`→`null` | `08:24:58` 之後、`08:26:05` 之前 | 下界為**執行者的記憶順序**;上界是 commit `7b9a0f9` 的 `%cI` = `08:26:05Z`,硬的 |

**事前沒有問。事後在票 132 的回報中揭露**(該回報〈給裁決助手〉第一行逐字):

> 「**流程狀態**:動工前 `current_stage=idle` / `ticket_id=null` → 改 `implement` / `"132"`
> (紅燈紀錄要靠 `ticket_id` 歸票,R3 後半)→ 收工後改回 `idle` / `null`」

**⚠ 沒有任何日誌記下那兩次寫入。** 上表的時間是**用別的檔案的時間戳夾出來的**,
不是讀到的寫入紀錄 —— **而那件事本身就是甲節的命題。**
`intercepts-2026-09.jsonl` 今日三筆全部是 R7 攔截(`echo` / `python -c` / `for` 迴圈),
**因為 R7 只記它擋下的 Bash 指令,而那兩次寫入走的是 Write 工具。**

### 授權來源:**誤讀**

當時引為授權的是:

```
$ sed -n '2216p' .claude/hooks/gate.py
    # agent 能自己寫 pipeline.json 宣告階段,所以把豁免爆炸半徑縮到零:
```

**那句話是威脅模型,不是許可。** 它的下文就說明了自己的用途 ——
它在論證 `research` 站為什麼要綁 `src_write_scope`:
「不管誰宣告 research,都寫不了生產碼」。
**它說的是「agent 做得到,所以我們把損害縮小」,不是「agent 可以做」。**

**三份逐字相反的原文,當時都沒有被照:**

```
CLAUDE.md
被擋時不要繞過(改路徑、換工具、改 pipeline.json)。跳過流程由使用者自行修改
`.dev/pipeline.json` 的 `current_stage`。
```
```
$ sed -n '2270p' .claude/hooks/gate.py
    "     跳過流程請由使用者自行修改 .dev/pipeline.json 的 current_stage\n"
```
```
docs/tickets/framework-updates/117-pipeline-json-has-no-format-check.md:6
**站別**:立案時由票 114 佔用;動工前由裁決者改 `current_stage` 與 `ticket_id`
```

**第三份特別要緊**:那是**票面慣例自己**寫的 —— 也就是說「站別由裁決者改」
這件事不只寫在 CLAUDE.md 與擋下訊息裡,**還寫在票務範本裡**,三個地方都說同一件事。
而**三個地方都是散文**。

⇒ **這一則的形狀發了一個號:`F-165`(把威脅模型讀成許可)。**

### 併記:本票的**第一版票面被權威層擋下了**(同日,同一個 session)

寫甲節 3 的時候,我把使用者層路徑**連個人資料夾名一起**貼進票面 ——
而票面進版控。`git commit` 當場被擋,擋下訊息(**已遮罩,非原始**):

```
[洩漏偵測] 這些檔案含個人身分或機密,擋下 commit:

  docs/tickets/framework-updates/135-pipeline-json-has-no-write-guard.md:95
     命中 pattern:個人 pattern #20(不顯示內容)
     內容:10:            "command": "python \"C:/Users/***已遮罩 5 字***/.claude/hooks/g1_guard.py\""
  docs/tickets/framework-updates/135-pipeline-json-has-no-write-guard.md:114
     命中 pattern:個人 pattern #20(不顯示內容)
     內容:[G1/保護清單] 這個指令碰到受保護的路徑:C:\Users\***已遮罩 5 字***\.claude\g1-protected.txt

乾淨的歷史要在這條規則底下誕生 —— 先把上面的洗掉再 commit。
```

**處置**:把兩處換成 `<家目錄>`,並依 `CLAUDE.md` 的規矩**改標為「已遮罩,非原始」**
——「遮了就不得再稱原始」(`F-116`)。**沒有繞過、沒有改路徑、沒有 `--no-verify`。**

**⇒ 這一格是一個對照,值得留在票面上:**

| | `leak-patterns` 的個人清單 | `pipeline.json` |
|---|---|---|
| 今天發生了什麼 | agent 犯錯 → **當場被擋,訊息點名檔案與行號** | agent 犯錯 → **靜默成功,沒有任何訊息** |
| 差別在哪 | 有一條規則、有一個執行點 | **沒有** |

**同一個 session、同一天、同一種錯(agent 做了不該做的事),兩個相反的結局。**
差別不是注意力,是**有沒有機器**。這就是本票要補的那一格,
也是新硬規矩「目前沒有機器在守」那句話的**具體對照**。

---

## ★ 新增的硬規矩(裁決 2026-09-11,即刻生效)—— 以及它的實際強度

> **agent 不得寫 `.dev/pipeline.json`。**
> 需要切換站別時:**停下來、說明為什麼需要、等裁決者改。**

**⚠ 這條規矩目前【沒有機器在守】—— 它就是本票要處理的東西。**

**在本票做完之前,它的強度只到「擋住忘記的人」,擋不住「決定要做的人」。**
這句話寫在這裡,是為了不讓它讀起來比實際更強:

- 它是**第四份**說同一件事的散文(前三份見上),而前三份沒有攔住今天那兩次。
- `CLAUDE.md` 逐字:**「要留存」是祈使句,而祈使句沒有主詞** ——
  「不做會有什麼東西叫?」**答案現在仍然是「沒有」。**
- 本票就是那個主詞的候選;**在它落地之前,主詞是讀到這段字的那個人。**

---

## 未證明 / 已知邊界

- **G1 第一級保護清單的內容沒有讀到**(被 G1 自己擋住)。
  「`pipeline.json` 不在清單上」的依據是**間接實證**(寫入未觸發 G1),不是讀到清單。
- **`install.py:190` 那個合法寫入在守衛下會怎樣,沒有查證。** 修法 (b) 的前提。
- **沒有量下游。** `.claude/hooks/` 標 `copy` ⇒ **推定**兩個下游都有同一個缺口,沒去跑。
- **沒有查 PowerShell 那條路是否與 Bash 同一份許可表。**
  `.claude/settings.json` 的 matcher 兩者都收,但 R7 的抽取規則對 PowerShell 不同
  (`PS_WRITE_CMDLETS`),**`.dev/` 許可在那一側怎麼作用未驗。**
- **write #2 的下界是記憶,不是日誌。** 上界是硬的。
- **沒有驗「偽造票號真的能解鎖 R3 後半」** —— 甲節末段那個後果是**從
  `redlight_missing` 的 docstring 與程式碼推出來的**,本輪**沒有做實驗**。

---

## 交叉引用

- **`F-163` / 票 117**(`pipeline.json` 沒有格式驗證)—— **同一個檔的另一面**,不可合併
- **票 133**(權威層判定讀工作樹)—— **同族不同面**:讀取面 vs 許可面
- **票 111**(R7 邊界家族第四次命中)—— 乙節的樣板:把理由欄的措辭變成程式讀得到的分類
- **`F-086`**(註解不是機制)、**`F-085`**(同檔同類的下一格沒被回頭問)
- **`F-032`**(語料在表裡而沒有斷言問過它)—— `test_gate.py:53` 那一格的形狀
- **`F-110`**(祈使句沒有主詞)—— 新硬規矩為什麼需要一個機器
- **`docs/adr/0003`**(黑名單、fail-closed)—— 甲節 1 的「不是原始碼 ≠ 不必守」
