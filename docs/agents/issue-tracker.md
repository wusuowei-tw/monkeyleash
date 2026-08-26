# Issue tracker: Local Markdown

Issues and specs for this repo live as markdown files in `.scratch/`.

## Conventions

- One feature per directory: `.scratch/<feature-slug>/`
- The spec is `.scratch/<feature-slug>/spec.md`
- Implementation issues are one file per ticket at `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01` — never a single combined tickets file
- Triage state is recorded as a `Status:` line near the top of each issue file (see `triage-labels.md` for the role strings)
- Comments and conversation history append to the bottom of the file under a `## Comments` heading

## When a skill says "publish to the issue tracker"

Create a new file under `.scratch/<feature-slug>/` (creating the directory if needed).

## When a skill says "fetch the relevant ticket"

Read the file at the referenced path. The user will normally pass the path or the issue number directly.

## Wayfinding operations

Used by `/wayfinder`. The **map** is a file with one **child** file per ticket.

- **Map**: `.scratch/<effort>/map.md` — the Notes / Decisions-so-far / Fog body.
- **Child ticket**: `.scratch/<effort>/issues/NN-<slug>.md`, numbered from `01`, with the question in the body. A `Type:` line records the ticket type (`research`/`prototype`/`grilling`/`task`); a `Status:` line records `claimed`/`resolved`.
- **Blocking**: a `Blocked by: NN, NN` line near the top. A ticket is unblocked when every file it lists is `resolved`.
- **Frontier**: scan `.scratch/<effort>/issues/` for files that are open, unblocked, and unclaimed; first by number wins.
- **Claim**: set `Status: claimed` and save before any work.
- **Resolve**: append the answer under an `## Answer` heading, set `Status: resolved`, then append a context pointer (gist + link) to the map's Decisions-so-far in `map.md`.

## 時鐘欄(2026-08-25 裁決,即刻生效)

**每一張新票的票面必須有一欄「時鐘」:寫明什麼時候不做會痛。**

**說不出時鐘的,一律停在 `candidate`,不排進任何順序。**
說不出來不是失格 —— 很多票確實還不知道什麼時候會咬人。
規矩要的不是每張票都有期限,是**每張票都被問過這個問題**,
而問過與沒問過要在票面上分得出來。

寫法:一句話,帶一個可以到期的東西(日期、事件、外部里程碑)。

| 好的時鐘 | 為什麼 |
|---|---|
| `8/28 開源 —— 之後這個判定點在別人的機器上跑` | 有日期,且說出到期時**性質會變** |
| `9/15 影子晉升評估 —— 之前判不出來就得帶著假綠燈過關` | 綁在一個已排定的事件 |
| `下一個掛載點進表時 —— 屆時擷取側會靜默不跟` | 沒有日期,但有**可觀察的觸發條件** |

| 不是時鐘 | 為什麼 |
|---|---|
| `盡快` / `高優先` / `重要` | 沒有東西會到期;它描述的是感受,不是世界 |
| `等有空` | 那是排序的結果,不是排序的輸入 |
| `以後會變成技術債` | 「以後」不能到期。**什麼時候**變成債? |

### 為什麼要這一條(理由寫在規矩旁邊,不寫在別的檔案裡)

2026-08-25 的存量盤點量到 31 張未完成票。

> **成因不是開得太多,是開的時候沒有人問「這件事什麼時候會咬人」。**
>
> 沒有時鐘的待辦會變成背景噪音,而**背景噪音不會被清掉,
> 只會讓有時鐘的那幾張更難被看見**。

所以本條不是為了少開票 —— 開票仍然便宜,而且應該便宜。
它是為了讓**排序有輸入**:凍結政策解除後改成「看哪個優先處理的先處理」,
而「優先」需要一個可比較的東西,`高優先` 三個字比不出高下。

### ⚠ 時鐘欄目前**沒有機制**,只有紀律

本節是散文。**沒有任何東西會在一張沒有時鐘的票被開出來時出聲。**

寫下這句是因為 CLAUDE.md 的常駐檢查項逐字:
**「要留存」是祈使句,而祈使句沒有主詞** ——
每寫下一句規矩,立刻問「不做會有什麼東西叫?」答案現在是「沒有」。

**機制版的候選**(未裁,未開票):`gate.py` 已經有 `TICKET_DIRS`
(2 項)這個既有的錨點,知道票住在哪裡。一條檢查可以是:
新增的票檔沒有時鐘欄 → 擋,或(較溫和)→ 要求 status 必須是 `candidate`。
**後者更貼近本條的語意** —— 它不禁止你開沒有時鐘的票,
它禁止你把沒有時鐘的票排進順序。

## 判準要先在自己的語料上跑過(2026-08-26 裁決,即刻生效)

> **一個要交給人核准的判準,必須先在自己的反例集上跑一次,並貼出逐筆對照。**
>
> 沒跑過的判準,**它證明的只是提出者想得到的那些情況**。

適用範圍是**任何要人點頭的判準** —— 分類規則、遷移條件、豁免條件、
lint 規則、驗收條件。不只票務。

**要交的是三樣,缺一不算**:

1. **判準本身**(規則,不是結論 —— 見 CLAUDE.md 的批次核准那條)
2. **語料**,含**反例**(全是正例的語料任何判準都會過)
3. **兩者相乘的逐筆對照表**,含**判錯的那幾筆**

### 標本

2026-08-26 的一次:提案者在同一頁上給了**四筆帶標籤的語料**,也給了**判準**,
**而沒有把兩者對起來**。對起來就會看到第 2 筆被判錯,
且錯的方向是**把真陽壓成附帶損害** —— 假陽率會被灌水。

> **兩份材料都已經在同一頁上,缺的那一步是把它們相乘。**
> 這不是懶,是**「我有語料」與「我驗過」感覺起來很像** ——
> 語料放在那裡會產生一種它已經發揮作用的錯覺。

### 對照表要連**判對的**一起貼

只貼判錯的,讀的人無從知道涵蓋率;只貼判對的,那是選擇性呈現。
**還要貼但書** —— 語料幾筆、有幾筆是為了測試刻意造的、標籤是誰標的。
一張沒有但書的對照表會被當成外推依據,而**小語料上的涵蓋率不能外推**。

### ⚠ 這一條也沒有機制,但它比時鐘那條容易自查

同樣是散文,同樣沒有東西會出聲。**差別在於它的違反有痕跡**:
一份沒有對照表的判準提案,**表不在那裡**就是證據 ——
而一張沒有時鐘的票,少的那一欄要有人記得去找。

所以自查問法是固定的一句:**「對照表呢?」**
問不出東西就是還沒跑。核准者可以只憑這一句擋下,不必讀判準內容。
