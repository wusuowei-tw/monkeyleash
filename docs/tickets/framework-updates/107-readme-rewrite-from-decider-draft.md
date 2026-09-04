# 107 — README 改版:裁決端底稿與現行 README 的逐項對帳

**狀態**:**完成**(2026-09-04)—— 兩份 README 併稿完成,三個 `⟨VS 對帳⟩` 標記清零,三個錯誤數字全部換成重量值。~~立案、未實作~~(`F-036`:舊狀態不刪)
**時鐘**:**無外部時鐘。** 底稿已由裁決端起草、GPT / Gemini 審過,而**它不是定稿** ——
本票的工作是把它與 repo 的實際狀態對帳,把三個 `⟨VS 對帳⟩` 標記換成查證過的內容,
把數字換成重量過的實測值
**站別**:`idle`(立案時);刀二開工前由 Jeff 切成 `implement`,`ticket_id = 107`
**前置**:票 74(skills 無 lock 檔)、票 54(`TestLegacyNoRedlightList` 的已知缺口)、
票 106(CI 差額)、`F-137`(一份清單不會帶著它自己的長度)、`F-159`(答錯問題的欄位)

> **票號取得時點:2026-09-04,動手當下重查兩個位置,合併後最大號 **106**,加一。**
> `ls | grep "^107"` 零命中。**不提前占號**(`F-118`)。

**底稿位置**(唯讀,本票不動它):裁決端桌面的
`README.draft.md`(8164 bytes)與 `README.zh-TW.draft.md`(7840 bytes),
兩份 mtime 皆 `Sep 4 21:06`。

> ⚠ **路徑刻意寫成 `<裁決端桌面>` 而不是絕對路徑。**
> 第一次 commit 這張票時 **`leak_scan` 擋下了**,命中「個人 pattern #1」——
> 絕對路徑裡含使用者名稱。**擋得對**,而處置是改寫不是繞過(`F-116`)。
> 本票因此**不記那兩份底稿的絕對路徑**;它們不在 repo 裡,也不需要在。

---

## 一、現行 README 逐段對帳(①)

`README.md` 共 153 行、`README.zh-TW.md` 為其中譯。逐段:

| # | 現行段落 | 判定 | 理由 |
|---|---|---|---|
| 1 | 標題 + `**No monkeypatch, no fake greens.**` | **草稿未涵蓋,建議保留** | 那是這個專案的**名字由來**(monkeypatch → monkeyleash)。草稿完全沒有提到名字怎麼來的 |
| 2 | `Machine-enforced gates for a six-stage…Formerly agent-gates.` | **草稿已涵蓋**(改寫得更好) | 但 **`Formerly agent-gates` 建議保留** —— 舊名還在外部連結與下游 repo 裡 |
| 3 | `Core premise: prompts are suggestions; files and hooks are law.` | **草稿未涵蓋,建議保留** | 草稿的「評分者不是考生」是**另一句話**,不是它。這一句是整個設計的前提 |
| 4 | CI badge | **草稿未涵蓋,建議保留** | badge 是外部可驗證的即時證據,與本 repo「證據優先」一致 |
| 5 | `[繁體中文](README.zh-TW.md)` 語言互連 | **草稿未涵蓋,必須保留** | 兩份 README 互指,少了它中文版等於沒有入口 |
| 6 | `## What this is` 前兩段 | **草稿已涵蓋** | 草稿的開場更好 |
| 7 | **G1 那一段**(`It also ships G1…not a sandbox`) | 🔴 **草稿未涵蓋,建議保留** | **草稿完全沒有提 G1。** 而 G1 是使用者層的獨立防護,且那句「**this is a denylist hook, not a sandbox**」是一句**主動收窄宣稱**的話 —— 正是本 repo 的風格 |
| 8 | **歸屬句**(見下,原文照貼) | **草稿部分涵蓋** | 草稿把它挪到「Where it comes from」並加了 `⟨VS 對帳⟩` |
| 9 | `## Prerequisites` 三點 | **草稿部分涵蓋** | 第三點 Git Bash 那句(原文見下)**比草稿精確**,見第四節 |
| 10 | `## Quickstart` 的 5 行 + `pip install` 那段警告 | **草稿已涵蓋但數字錯**,見第三節 | 草稿的順序不同(先 `pip install` 後 `bootstrap.sh`),而那個順序**改變了首跑的結果** |
| 11 | `Install into another repository:` + `install.py` + 兩支 verify | 🔴 **草稿未涵蓋,建議保留** | **草稿完全沒有提「裝進別的 repo」** —— 而那是這個專案的主要用途之一 |
| 12 | `## No coding background? Let your AI install it` 整段 | 🔴 **草稿未涵蓋,建議保留** | 那一段是**給目標讀者(不讀程式碼的人)的唯一操作入口**,且內含「不要繞過、不要改路徑、不要改狀態檔」三條紀律 |
| 13 | `## Two enforcement layers` 表 + 三點 | **草稿已涵蓋**(壓縮成一列表格) | ⚠ 草稿少了「**不是 Claude Code 的 agent 只拿得到權威層**」那一句 |
| 14 | `## Rules` 表(R1–R8 + G1)+ `rule_codes()` 那句 | **草稿部分涵蓋** | 🔴 草稿寫「9 rules (R1–R9)」而**現行表只列到 R8 + G1**,見第三節 |
| 15 | `There is no per-repo switch…(docs/adr/0010)` | **草稿未涵蓋,建議保留** | |
| 16 | `## Known limitations` 四點 | **草稿已涵蓋**(改寫成 `What it does not claim`) | ⚠ 現行第 2 點(個人 leak pattern 兩側掃的 pattern 集不同)**草稿沒有** |
| 17 | `## Where to read next` 五項 | **草稿已涵蓋**(縮成四項) | ⚠ 草稿少了 `docs/tickets/`、`docs/audits/`、`CLAUDE.md` |
| 18 | `## License` 段 | **草稿部分涵蓋**(只剩 `License: see LICENSE.`) | 🔴 **現行那段含第三方歸屬與 `THIRD_PARTY_NOTICES.md` 指標,不能只縮成一行** —— 見第二節 |

### 現行歸屬句(原文照貼)

`README.md:29-32`:

```
The six-stage pipeline builds on Matt Pocock's open-source skills
(grill-with-docs → to-spec → to-tickets → implement → code-review →
improve-codebase-architecture); the enforcement layer — the gates
themselves, the ledger, and the friction log — is original to this repo.
```

`README.md:151-153`(License 段):

```
MIT — see `LICENSE`. The skills under `.agents/skills/` are derived from
[mattpocock/skills](https://github.com/mattpocock/skills) (MIT) and modified
by `.claude/patches/`; see `THIRD_PARTY_NOTICES.md`.
```

`README.zh-TW.md` 對應段(原文照貼):

```
六站流程建立在 Matt Pocock 的開源 skills 之上
(grill-with-docs → to-spec → to-tickets → implement → code-review →
improve-codebase-architecture);強制層 —— 閘門本身、帳本、
與 friction log —— 是本 repo 原創。
```

### 現行 Git Bash 那句(原文照貼)

`README.md:39-40`:

```
- **On Windows, run the `bootstrap.sh` line in Git Bash** (bundled with Git for
  Windows) — PowerShell has no `sh`. Everything else runs in any shell.
```

`README.zh-TW.md:39-40`:

```
- **Windows 請在 Git Bash 裡跑 `bootstrap.sh` 那一行**(裝 git 時會一起裝)——
  PowerShell 沒有 `sh` 這個指令。其餘指令任何殼都跑得動。
```

> ### 🔴 **現行這句比草稿精確,建議沿用現行的寫法。**
> 草稿寫「run the **last three lines** in Git Bash / **最後三行**要在 Git Bash 裡跑」,
> 而草稿的程式碼區塊裡最後三行是
> `python -m pytest -q` / `sh bootstrap.sh` / `python -m pytest -q` ——
> **其中兩行是 `python`,在 PowerShell 裡跑得動。**
> 只有 `sh bootstrap.sh` 需要 Git Bash,而現行那句**正好只點名它**。

---

## 二、三個 `⟨VS 對帳⟩` 標記的查實(②)

### 標記一:`pyproject.toml requires-python`

```
pyproject.toml:9:requires-python = ">=3.10"
```

⇒ 換成 **`>= 3.10`**。草稿中文版寫「需要 Python ⟨…⟩ **以上**與 git」——
`>=3.10` 已含「以上」,兩者疊加會變成「3.10 以上以上」。**中文版要調整句式。**

### 標記二:`.agents/pipeline-stages.yaml` 的站名與順序

原文(`grep -nE "^  - id:|^    skill:|^    zh:"`):

```
14:  - id: idle          15:    skill: null                              16:    zh: 待命
19:  - id: grill         20:    skill: grill-with-docs                   21:    zh: 拷問共識
24:  - id: spec          25:    skill: to-spec                           26:    zh: 寫規格
29:  - id: tickets       30:    skill: to-tickets                        31:    zh: 拆票
38:  - id: research      39:    skill: research                          40:    zh: 探索研究
47:  - id: implement     48:    skill: implement                         49:    zh: TDD 實作
52:  - id: review        53:    skill: code-review                       54:    zh: 代碼審查
57:  - id: arch          58:    skill: improve-codebase-architecture     59:    zh: 架構掃除
```

> ### 🔴 **檔案裡有【八個】站,不是六個。**

| | |
|---|---|
| 現行 README 的歸屬句列的六個 | `grill-with-docs → to-spec → to-tickets → implement → code-review → improve-codebase-architecture` —— **那是六個 skill 名**,不是站名 |
| `pipeline-stages.yaml` 的八個 `id` | `idle` / `grill` / `spec` / `tickets` / **`research`** / `implement` / `review` / `arch` |
| 差在哪 | 多了 **`idle`**(待命,`skill: null`)與 **`research`**(探索研究) |

**⇒ 「六站」這個說法要處理,而處理方式是裁決不是實作:**

| 選項 | 內容 | 代價 |
|---|---|---|
| **甲** | 維持「六站」,並加一句「另有 `idle`(待命)與 `research`(探索區)兩個站,不在主線上」 | 沿用既有說法(`CLAUDE.md`、票面、skill 名全用六站),**但 README 會與 yaml 的 `id` 數對不上** |
| **乙** | 改成「八站」 | 準確,**但要動 `CLAUDE.md` 與大量既有引用**,遠超本票範圍 |
| **丙** | 不說數字,只說「流程由 `.agents/pipeline-stages.yaml` 定義」並列出 `id` | 不會過期,**但少了一個好記的名字** |

**本票不自行決定,列出等裁。** ⚠ 這正是 `F-137` 的形狀:
**一份清單不會帶著它自己的長度**,而「六」是一個寫在別處、會與清單漂開的數字。

### 標記三:mattpocock 歸屬(**照實寫,不是「若為 MIT」**)

| 項 | 查證結果 | 出處 |
|---|---|---|
| **確切 repo 名** | `mattpocock/skills` | `THIRD_PARTY_NOTICES.md`、`README.md:152` |
| **上游 repo URL** | `https://github.com/mattpocock/skills` | `THIRD_PARTY_NOTICES.md` `- Source:` 那行 |
| **上游 LICENSE** | **MIT**,`Copyright (c) Matt Pocock` | `THIRD_PARTY_NOTICES.md` 的 `### License text (MIT)` 區塊**收錄了全文** |
| **參考 commit SHA** | 🔴 **不存在,而且是明文記載的** | 見下 |
| 涵蓋檔案 | `.agents/skills/` 底下 **39 個檔、13 個 skill 目錄**(逐一列在 `THIRD_PARTY_NOTICES.md`) | 同上 |
| 本地修改 | **3 個檔**經 `.claude/patches/apply_patches.py` 修改後再散布 | 同上 |
| 本 repo LICENSE | **MIT**,`Copyright (c) 2026 wusuowei-tw` | `LICENSE:1-3` |

#### 🔴 參考 commit SHA:**查無,而那不是「我沒找到」**

`THIRD_PARTY_NOTICES.md` 的 `### Provenance caveat` 逐字:

```
This repository has **no `skills-lock.json`**, so the exact upstream
commit or version the files were taken from is not recorded. Tracked as
ticket `docs/tickets/framework-updates/74`.
```

實查佐證:

```
ls skills-lock.json .agents/skills-lock.json   →  兩者皆 No such file or directory
ls .dev/provenance.jsonl                       →  No such file or directory
ls docs/tickets/framework-updates/ | grep ^74  →  74-skills-have-no-lock-file.md
```

> ### **⇒ 草稿裡「版本/commit」那一格,正確的填法是【寫明它不存在】,不是留空也不是編一個。**
> 建議寫法:「取自 upstream 的**確切 commit 未記錄**(無 `skills-lock.json`,票 74),
> 檔案清單與修改逐項列在 `THIRD_PARTY_NOTICES.md`。」

⚠ **`.dev/provenance.jsonl` 也不存在** —— 那是**下游**才有的檔(上游對自己沒有 provenance),
`status` 的 provenance 欄逐字印「未記錄(上游無此檔屬正常)」。**不要拿它當 SHA 來源。**

---

## 三、草稿數字逐一重量(③)

**全部 2026-09-04 實測,HEAD `41cba6d`。**

| 草稿寫的 | 實測 | 判定 | 來源 |
|---|---|---|---|
| 首跑 `2 failed` | **2 failed** | ✅ **中** | **乾淨 clone 實跑**(見下),不是抄 8/31 |
| 「那兩條轉綠」 | 🔴 **只有一條轉綠** | ❌ **錯** | 見下 |
| 本機 `1313` | **1313 passed, 3 skipped, 3 xfailed** | ✅ | `python -m pytest -q` |
| CI `1303` | **1303 passed, 1 deselected, 3 xfailed** | ✅ | 票 106 CI run `33870292455` |
| `9 rules` | **R1–R9 共 9 個** | ✅ | `grep -oE "\[R[0-9]+" gate.py \| sort -u` → `R1…R9` |
| `159 friction entries` | 🔴 **148 則**(最大號 F-159) | ❌ **錯** | 見下 |
| `106 tickets` | 🔴 **105 張**(最大號 106) | ❌ **錯** | 見下 |

### 首跑實測 —— **乾淨 clone,不抄舊值**

```
git clone -q . <tmp>/mlclone            →  exit 0
git -C <tmp>/mlclone config core.hooksPath  →  exit 1(未設 —— 正是草稿說的狀態)

<clone> $ python -m pytest -q
FAILED tests/test_gate.py::TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce
FAILED tests/test_gate.py::TestAuthorityLayerIsWired::test_this_repo_itself_is_wired
2 failed, 1311 passed, 3 skipped, 3 xfailed in 102.59s

<clone> $ sh bootstrap.sh
[bootstrap] core.hooksPath -> .githooks

<clone> $ python -m pytest -q
FAILED tests/test_gate.py::TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce
1 failed, 1312 passed, 3 skipped, 3 xfailed in 99.70s
```

> ### 🔴 **`2 failed` 這個數字是對的,而「那兩條轉綠」是錯的 —— 只有一條轉綠。**

**兩條的性質完全不同:**

| 測試 | `bootstrap.sh` 之後 | 為什麼 |
|---|---|---|
| `TestAuthorityLayerIsWired::test_this_repo_itself_is_wired` | ✅ **轉綠** | 它就是在驗 `core.hooksPath` 有沒有接上 —— **草稿說的那個「應該紅到裝好為止」的測試,指的是這一條** |
| `TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce` | 🔴 **仍然紅** | 它要 `.dev/test-runs.jsonl` 裡的**排水證據**,而那個檔 **gitignored,clone 永遠不會有** |

**成因查證**(不是推論):該測試 `tests/test_gate.py:784-785` 呼叫
`gate.redlight_missing(...)`,而 CI 為此**明文 deselect**,`tests.yml:66-67` 逐字:

```
      #   --deselect 清單完整性那一條要 .dev/test-runs.jsonl 裡的排水證據,
      #              而證據格式是票 49 的題目。等票 49 定案後回來重評。
```

#### ⇒ **同一句話在四個環境有四個答案**

| 環境 | 結果 | 為什麼 |
|---|---|---|
| **乾淨 clone,首跑** | **2 failed** | 權威層未接 + 無排水證據 |
| **乾淨 clone,`bootstrap.sh` 之後** | **1 failed** | 排水證據仍然沒有 |
| **作者本機** | **0 failed**(1313 passed) | `.dev/test-runs.jsonl` 累積了數月的排水證據 |
| **CI** | **0 failed**(1303 passed, 1 deselected) | CI 明文 deselect 那一條 |

⚠ **而現行 README `:57-58` 說的是第二種**:

```
The last command ends with `1 failed` (`TestLegacyNoRedlightList`) — that is a
known gap, not a broken install. CI skips this one; see ticket 54 for why.
```

**那句話對 clone 的人是對的,對作者自己的 repo 是錯的。**
⇒ 新 README **要說清楚是哪一個環境**,否則照做的人拿到的數字對不上。

### `159 friction entries` 為什麼錯

**用產生端的判準量**(載入 `friction_heading.HEADING`,不自己寫正則 —— `F-152`):

```
friction 標題行總數(含任何前綴) : 148
其中 F- 開頭                     : 148
最大 F- 號                       : 159
最小 F- 號                       : 1
缺號個數                         : 11
缺號                             : [47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57]
重複號(R9 會擋)                  : []
```

> ### **148 則,最大號 F-159,中間缺 11 個號(F-047–F-057 連續一段)。**
> **「最大號」不是「條目數」** —— 而**缺號是合法的**:
> `gate.check_friction_numbers` 的 docstring 逐字寫著
> 「**不查連號** —— 缺號合法(後到者改號會留下空洞,見發號規則第 4 節)」。

⚠ 這是 `F-137`(一份清單不會帶著它自己的長度)的**又一個實例** ——
而這一次它出現在 **README 上**,是**對外**的數字。

### `106 tickets` 為什麼錯

```
票檔 .md 總數                    : 105
其中檔名帶號                     : 105
不帶號的檔                       : []
最大票號                         : 106
票號缺號個數                     : 1
票號缺號                         : [12]
```

**105 張,最大號 106,缺 12 號。** 同一個形狀。

### 建議寫法(兩處都要改口徑)

**不要寫「N 則 / N 張」然後填最大號。** 建議:

```
friction log:148 則(編號至 F-159;缺號合法,見 R9)
tickets:105 張(編號至 106)
```

**或**只寫最大號並說明它是編號:`編號已到 F-159 / 票 106`。
⚠ **兩者不可混用** —— 混用時讀的人分不出你講的是哪一個。

---

## 四、中英對齊(④)

**逐段比對兩份底稿,語意不一致處:**

| 段 | 英文 | 中文 | 判定 |
|---|---|---|---|
| 圖(`:18`) | `← the only writer of intent` | `← 唯一寫下意圖、決定是否放行的人` | ⚠ **中文多了「決定是否放行」** |
| 「裡面有什麼」(`:53`) | `This is the repo's most important asset.`(未粗體) | `**這是這個 repo 最重要的資產。**`(粗體) | ⚠ 格式不一致 |
| 十分鐘上手(`:66`) | `Requires Python ⟨…⟩ and git.` | `需要 Python ⟨…⟩ **以上**與 git。` | 🔴 **標記換成 `>=3.10` 後中文會變「3.10 以上以上」** |
| Windows(`:77`) | `run the last three lines in Git Bash` | `最後三行要在 Git Bash 裡跑` | 🔴 **兩份都不精確**(見第一節)—— 三行裡有兩行是 `python` |
| 狀態(`:115`) | `159 friction entries, 106 tickets` | `159 則 friction、106 張票` | 🔴 **兩份同錯**(見第三節) |

**其餘各段語意一致**,包括:開場問句、兩件刻意的事、九條規則表、不主張什麼五點、
差別那節四點、來源那節、延伸閱讀四項。

### 標點慣例 —— **底稿與現行 repo 不同,需要裁決**

```
現行 README.zh-TW.md:  全形逗號「，」出現 0 次;半形逗號「,」出現 49 次
底稿 README.zh-TW.draft.md:  全形「，：（）」通篇使用
```

裁決指示刀二用「繁中全形標點」⇒ **採底稿的全形**。
⚠ **但那與 `README.zh-TW.md` 現行、以及 `CLAUDE.md` / 票面 / friction log 的慣例相反**
(全庫中文散文用半形 `,` `:`)。
**本票只改兩份 README,不動別的檔** —— 而那會讓 repo 內出現**兩種標點慣例**。
**這一格請確認是刻意的。**

---

## 五、刀二要做的事(驗收條件)

1. 併稿寫入 `README.md` 與 `README.zh-TW.md`,**三個 `⟨VS 對帳⟩` 標記清零**。
2. **數字全換實測值**:首跑說明分環境、friction 148(編號至 F-159)、票 105(編號至 106)、
   本機 1313、CI 1303、規則 9。
3. **建議保留的段落併回**(第一節標「草稿未涵蓋建議保留」那六項:
   名字由來、`Formerly agent-gates`、核心前提、CI badge、語言互連、
   **G1 段**、**裝進別的 repo**、**讓 AI 幫你裝**、per-repo switch、
   個人 leak pattern 那點、`Where to read next` 的三項、**License 段的第三方歸屬**)。
4. 繁中全形標點(裁決;⚠ 見第四節末的慣例衝突)。
5. `python .claude/portable/leak_scan.py --review README.md README.zh-TW.md` → **exit 0 且有報告**。
   (基線實測:今天兩份現行 README 跑這條回 `[審查模式] 未內容掃描 的檔案(0): (無)`,exit 0。)
6. 全套逐名對帳。**基線 = 票 106 收票後的 1313 passed / 3 skipped / 3 xfailed**。
   ⚠ 動工時 HEAD 若不是 `41cba6d`,**先重算再談差異**(`F-109`)。
7. 票面狀態行改完成;CI 對帳四格留白待推後填。

### ⚠ 一件實測過的好消息

```
grep -rn 'ROOT / "README' tests/*.py .claude/portable/*.py   →  零命中
```

**沒有任何測試讀真實的 `README.md` 內容** ——
所有測試裡的 `README.md` 都是在 `tmp_path` 裡造的合成檔。
⇒ **改 README 不會讓任何既有測試變紅。**

⚠ 附帶查證(**查了才知道不是矛盾**):`tests/test_manifest.py:164-166` 斷言
`explicit_mark("README.md", …) is None` 且 `mark_for("README.md") == "copy"`,
而 `.agents/portable-manifest.txt:39` 寫 `README.md skip` ——
**看起來矛盾,實際上那條測試用的是 `_write(table, "pkg/  copy\n")` 造的【合成表】**,
不是真實 manifest。**不列為發現。**

---

## 六、本票不含 / 要裁的三件

**不含**:`CLAUDE.md`、票面、friction log 的標點或用詞;下游 sync;`THIRD_PARTY_NOTICES.md` 的內容。

| # | 要裁的 |
|---|---|
| 1 | **「六站」怎麼處理**(甲/乙/丙,見第二節標記二) |
| 2 | **繁中全形標點會讓 repo 出現兩種慣例** —— 確認是刻意的 |
| 3 | **首跑數字要以哪個環境為準**(clone 首跑 2 / clone bootstrap 後 1 / 作者本機 0 / CI 0) |

---

## 七、為什麼是現在

**因為底稿裡有三個數字是錯的,而它們是【對外】的數字。**

`159 則`、`106 張` 兩個錯法相同:**把最大號當成條目數**,
而 `缺號合法` 正是 R9 明文的設計(`不查連號`)。
`那兩條轉綠` 則是一個**沒有量過就寫下的期待** ——
實測只有一條轉綠,另一條在 clone 上**永遠**是紅的。

> **一份 README 是這個專案對外唯一的入口。**
> 裡面的數字錯了,讀的人照著做會拿到對不上的結果 ——
> 而**那正是這個 repo 存在的理由的反面**。

---

# 落地紀錄(2026-09-04)

## 三裁(2026-09-04,Jeff)

| # | 內容 |
|---|---|
| 一 | **六站走甲** —— 維持「六站」,加一句「另有 `idle` 待命與 `research` 探索區,不在主線上」 |
| 二 | **標點照 repo 慣例用半形**,不用全形(與底稿相反) |
| 三 | **首跑以乾淨 clone 為準**:首跑 2 紅、`bootstrap.sh` 後 1 紅,且沿用現行 README 那句已知缺口說明(票 54、CI deselect);**Git Bash 那句沿用現行,只點名 `bootstrap.sh`** |

## 刀

| 刀 | sha | 內容 |
|---|---|---|
| 一(唯讀對帳) | `7a5530c` | 票面四項對帳 |
| 二(併稿) | (本刀) | `README.md` + `README.zh-TW.md` + 本節 |

## 基線重算(裁決指示:HEAD 非 `41cba6d` 先重算)

```
git diff 41cba6d 7a5530c --stat
 .../107-readme-rewrite-from-decider-draft.md       | 392 +++++++++++++++++++++
 1 file changed, 392 insertions(+)

python -m pytest -q   ->  1313 passed, 3 skipped, 3 xfailed
```

**中間只有一個 `.md`,零 `.py` 進出 ⇒ 基線 1313 不變。**

## 三個 `⟨VS 對帳⟩` 標記清零

```
grep -n "VS 對帳\|⟨" README.md README.zh-TW.md   ->  grep_exit=1(零命中)
```

| 標記 | 換成什麼 |
|---|---|
| `requires-python` | **`>= 3.10`**;中文句式改為「需要 Python `>= 3.10` 與 git」,**不疊「以上」** |
| 站名與順序 | 六站列名 + 「另有兩個站不在主線上:`idle`(待命)與 `research`(探索區,不准寫生產碼)」(裁一,甲案) |
| mattpocock 歸屬 | `mattpocock/skills`(MIT)+ 連結 + **「取自上游的確切 commit 沒有被記錄 —— 這個 repo 沒有 `skills-lock.json`(登記為票 74)」** + 指向 `THIRD_PARTY_NOTICES.md` |

## 三個錯誤數字全部換成重量值

| 底稿 | 換成 | 來源 |
|---|---|---|
| `159 friction entries` | **148 則,編號至 `F-159`** | 載入 `friction_heading.HEADING` 量,缺 11 個號(F-047–F-057),零重複 |
| `106 tickets` | **105 張,編號至 106** | 檔名帶號者 105,缺 12 號 |
| `expect: the two go green` | **分兩列的表**:一條轉綠、一條**仍然紅**(要 `.dev/test-runs.jsonl` 的排水證據,clone 永遠沒有) | 乾淨 clone 兩次實跑 |

並在兩份「狀態」節末加一句**口徑說明**:

```
> 「幾則」與「編號到幾」在這裡是兩件事:friction 號與票號都可能有缺號
> (改號會留下空洞,而 R9 刻意不查連號)。上表兩個都給。
```

> **這一句是本票最該留下的東西** —— 它讓下一個改 README 的人**不會再犯同一個錯**,
> 而底稿犯的正是這個(`F-137`:一份清單不會帶著它自己的長度)。

## 12 段建議保留全部併回

名字由來(`No monkeypatch, no fake greens.`)、`Formerly agent-gates`、核心前提句、
CI badge、語言互連、**G1 整段**(含「denylist hook, not a sandbox」)、
**裝進別的 repo**(`install.py` + 兩支 verify)、**「讓 AI 幫你裝」整段**、
兩層強制的三點(含「不是 Claude Code 的 agent 只拿得到權威層」)、
per-repo switch 那句、個人 leak pattern 那點、`Where to read next` 的
`docs/tickets/` / `docs/audits/` / `CLAUDE.md` 三項、**License 段的第三方歸屬**。

## 標點(裁二)

```
grep -c "，" README.zh-TW.md  ->  0
grep -c "：" README.zh-TW.md  ->  0
```

**全形逗號與全形冒號皆 0**,與 `CLAUDE.md` / 票面 / friction log 同一套慣例。
⚠ **這與底稿相反**(底稿通篇全形),裁二明文選了 repo 慣例。

## 中英對齊(刀一 ④ 列的五處)

| 處 | 處置 |
|---|---|
| 圖那句「唯一寫下意圖的人」 | 中文**改回與英文同義**(拿掉「決定是否放行」) |
| `This is the repo's most important asset.` 粗體不一致 | 兩份都不粗體(英)/ 粗體(中)—— **保留中文粗體**,因為中文版該句在表格內,粗體是既有慣例 |
| Python 「以上」疊加 | 中文改為「需要 Python `>= 3.10` 與 git」 |
| Windows 那句 | **兩份都改用現行寫法,只點名 `bootstrap.sh`**(裁三) |
| 狀態段數字 | 兩份同步換成重量值 + 口徑說明 |

## 驗收

| 項 | 結果 |
|---|---|
| 三個標記清零 | ✅ `grep` 零命中 |
| `leak_scan --review` 兩份 | ✅ `[審查模式] 未內容掃描 的檔案(0): (無)`,**exit 0 且有報告** |
| 全套 | ✅ **1313 passed, 3 skipped, 3 xfailed, 0 failed** |
| 測試數變動 | **0** —— 與刀一實測相符:**沒有任何測試讀真實 README 內容** |

## CI(run `33879746803`,`success`,`pytest in 54s`)

兩刀(`7a5530c` / `9a5d3df`)於 2026-09-04 推上 `41cba6d..9a5d3df`,**未用 force**。

```
跑測試                             1303 passed, 1 deselected, 3 xfailed in 19.18s
淨室驗證(每條規則各擋一次 + 安裝後形態)  1200 passed, 3 xfailed in 12.08s
                                   全部 9 條規則各擋下一次,權威層偵測正常,框架測試在新 repo 全綠。
```

### CI 與本機的差額 —— **逐項算得出來,不是「環境不同」**

| 項 | 數 | 來源(可各自驗證) |
|---|---|---|
| 本機 passed | **1313** | 刀二後那一跑 |
| − 個人 pattern 那一檔 | **−12** | `tests.yml:71` `--ignore=tests/test_known_items_regression.py`;**12 是本輪重量的**:`--collect-only -q` → `12 tests collected in 0.02s`。**未從票 106 抄** |
| ＋ Windows 才 skip 的 symlink 三條 | **+3** | 本機 `3 skipped`(`test_gate.py:451/459/473`) |
| − deselect 一條 | **−1** | `tests.yml:72`;CI 另欄報 `1 deselected` |
| **= CI passed** | **1303** | **與實測相符** |

`xfailed` 兩邊都是 **3**;`deselected` 預測 1、實測 1。
**`1313 − 12 + 3 − 1 = 1303` 寫在拿到 CI 實測之前。**

### 淨室 `1200` —— **預期增量 0,實測增量 0**

**這一格的預測在刀二就寫進本節了**(見上方原文的「待填」那格),所以它是**預測**,不是事後解釋。

算法仍是同一條(票 105 那次錯過之後定的):

```
淨室新增 = 新增測試中【manifest 標 copy】的那些檔的條數
```

本輪逐檔查證:

```
.agents/portable-manifest.txt:39:README.md                       skip
.agents/portable-manifest.txt:40:README.zh-TW.md                 skip
```

| 本輪動的檔 | manifest | 影響淨室嗎 |
|---|---|---|
| `README.md` | **`skip`**(`:39`) | ❌ 不出貨 |
| `README.zh-TW.md` | **`skip`**(`:40`) | ❌ 不出貨 |
| 測試檔 | **零異動** | ❌ |

**⇒ 那個集合是【空的】,預期 `1200 + 0 = 1200`,實測 `1200`。** ✅

> ⚠ **這一次的「增量 0」與票 106 的「增量 5」走的是同一條路徑。**
> 差別只在集合的內容,不在算法。
> **恰好為 0 時也要走同一條路徑得出** —— 否則下一次不為 0 時,
> 沿用的會是那個沒有走過查證的捷徑。

**淨室序列**:

| | 淨室 | 增量 | 動的檔在 manifest 標什麼 |
|---|---|---|---|
| 票 102 | 1169 | — | — |
| 票 103 | 1178 | +9 | `test_gate.py` copy |
| 票 104 | 1188 | +10 | `test_research_stage.py` copy |
| 票 105 | 1195 | +7 | `test_status.py` copy(7)+ `test_mcp_server.py` **skip**(21) |
| 票 106 | 1200 | +5 | `test_leak_scan.py` copy(5) |
| **票 107** | **1200** | **0** | 兩份 README 皆 **skip**,零測試檔異動 |

## ⚠ 這次改版證明了什麼、沒證明什麼

**證明了**:兩份 README 的三個標記已換成查證過的內容,三個數字已換成重量值,
12 段實質內容併回,兩份語意對齊,`leak_scan --review` 乾淨。

**沒證明**:**新 README 讀起來對不對**。
那是**人的判斷**,不是任何一條測試能回答的 —— 而本 repo**沒有任何測試讀真實 README**
(刀一實測,`grep 'ROOT / "README'` 零命中)。
⇒ **這份 README 從現在起只由人守著。** 寫出來,免得下一個人以為它有機器在守。
