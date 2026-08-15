# 40 — `.agents/skills/` 39 檔體檢(**唯讀盤點**)

**性質**:唯讀。**不改任何檔案。** 只量、只列表,**不做結論**,等裁。
**日期**:2026-08-15
**相關**:票 39 P2 第五件(正典 39 檔在此之前從未被內容掃描過)

---

## 1. 每檔行數

| 行數 | 檔案 |
|---|---|
| 140 | `diagnosing-bugs/SKILL.md` |
| 123 | `improve-codebase-architecture/HTML-REPORT.md` |
| 116 | `setup-matt-pocock-skills/SKILL.md` |
| 114 | `codebase-design/SKILL.md` |
| 113 | `code-review/SKILL.md` |
| 105 | `to-tickets/SKILL.md` |
| 82 | `to-spec/SKILL.md` |
| 77 | `tdd/tests.md` |
| 74 | `domain-modeling/SKILL.md` |
| 71 | `improve-codebase-architecture/SKILL.md` |
| 60 | `domain-modeling/CONTEXT-FORMAT.md` |
| 59 | `tdd/mocking.md` |
| 51 | `setup-matt-pocock-skills/domain.md` |
| 47 | `domain-modeling/ADR-FORMAT.md` |
| 46 | `setup-matt-pocock-skills/issue-tracker-gitlab.md` |
| 45 | `setup-matt-pocock-skills/issue-tracker-github.md` |
| 44 | `diagnosing-bugs/scripts/hitl-loop.template.sh` |
| 44 | `codebase-design/DESIGN-IT-TWICE.md` |
| 38 | `tdd/SKILL.md` |
| 37 | `codebase-design/DEEPENING.md` |
| 30 | `setup-matt-pocock-skills/issue-tracker-local.md` |
| 22 | `grilling/SKILL.md` |
| 20 | `grill-with-docs/SKILL.md` |
| 16 | `handoff/SKILL.md` |
| 15 | `setup-matt-pocock-skills/triage-labels.md` |
| 15 | `implement/SKILL.md` |
| 5 ×7 | `agents/openai.yaml`(to-tickets / to-spec / setup-matt-pocock-skills / improve-codebase-architecture / implement / handoff / grill-with-docs) |
| 3 ×6 | `agents/openai.yaml`(tdd / grilling / domain-modeling / diagnosing-bugs / codebase-design / code-review) |

| 統計 | |
|---|---|
| 檔數 | **39** |
| 總行數 | **1,657** |
| **中位數** | **37.0** |
| **最長** | **140**(`diagnosing-bugs/SKILL.md`) |
| 最短 | 3(`code-review/agents/openai.yaml`) |
| **超過 300 行** | **0 隻** |

---

## 2. `description` 欄:「這是什麼」 vs 「什麼時候該用」

**判準(明寫,免得數字不知道在數什麼)**:`description` 內含觸發語
(`use when` / `when the user` / `mentions` / `after` / `before` / `invoke` / `trigger`)
→ 判為有「什麼時候該用」。13 個 `SKILL.md` 全部有 frontmatter 與 `description`。

| skill | 判定 | 字元數 |
|---|---|---|
| `code-review` | **時機語 ✔** | 418 |
| `codebase-design` | **時機語 ✔** | 265 |
| `diagnosing-bugs` | **時機語 ✔** | 156 |
| `domain-modeling` | **時機語 ✔** | 216 |
| `grilling` | **時機語 ✔** | 152 |
| `setup-matt-pocock-skills` | **時機語 ✔** | 181 |
| `tdd` | **時機語 ✔** | 149 |
| `grill-with-docs` | 只有「是什麼」 ✘ | 106 |
| `handoff` | 只有「是什麼」 ✘ | 86 |
| `implement` | 只有「是什麼」 ✘ | 62 |
| `improve-codebase-architecture` | 只有「是什麼」 ✘ | 125 |
| `to-spec` | 只有「是什麼」 ✘ | 150 |
| `to-tickets` | 只有「是什麼」 ✘ | 247 |

**7 有 / 6 無。**

只有「是什麼」的六條原文:

- `grill-with-docs`:A relentless interview to sharpen a plan or design, which also creates docs (ADR's and glossary) as we go.
- `handoff`:Compact the current conversation into a handoff document for another agent to pick up.
- `implement`:"Implement a piece of work based on a spec or set of tickets."
- `improve-codebase-architecture`:Scan a codebase for deepening opportunities, present them as a visual HTML report, then grill through whichever one you pick.
- `to-spec`:Turn the current conversation into a spec and publish it to the project issue tracker — no interview, just synthesis of what you've already discussed.
- `to-tickets`:Break a plan, spec, or the current conversation into a set of tracer-bullet tickets, each declaring its blocking edges, published to the configured tracker.

---

## 3. 可執行腳本 / 仍停在散文

| skill | 腳本檔 | md 內指令碼區塊 |
|---|---|---|
| `diagnosing-bugs` | **1**(`scripts/hitl-loop.template.sh`,44 行) | 0 |
| 其餘 12 個 skill | **0** | **0** |

**全 13 個 skill 裡只有 1 個附腳本。**

「能封進程式而還停在散文」這一項**量不出來**:掃 `.md` 內的
` ```bash ` / ` ```sh ` / ` ```powershell ` 等指令碼區塊,**全部 13 個 skill 都是 0**。
也就是說散文裡**連指令碼區塊都沒有**,所以「有具體指令但沒封成腳本」這個
可機械偵測的訊號**一次都沒出現**。要判定「本來可以封成程式」需要讀語意,
不在本票的量測範圍內 —— **列為量不到,不臆測。**

---

## 4. `CLAUDE.md` 常駐檢查項

| | |
|---|---|
| `CLAUDE.md` 總行數 | **190** |
| 常駐檢查項**條數** | **3** |
| 常駐檢查項**總行數** | **43**(佔全檔 **23%**) |

| # | 位置 | 行數 | 標題 |
|---|---|---|---|
| 1 | 行 54–60 | 7 | 任何要進非原始碼清單的目錄,先問「它會不會裝著判定邏輯」 |
| 2 | 行 61–88 | **28** | 修好一個偵測器之後,回頭重掃既有資料 |
| 3 | 行 89–96 | 8 | 收了一個入口,就回頭問它的同類入口在哪 |

### 各條最後一次被**實際引用**

**「實際引用」的操作定義**:在 **`CLAUDE.md` 以外**出現該條識別詞
(票 / ADR / friction log / commit 訊息)。**`CLAUDE.md` 自己不算** ——
那是條文所在地,不是引用。

| # | 最後一次進 commit 訊息 | 最後一次被加進檔案 | 現樹引用檔數 |
|---|---|---|---|
| 1 | **2026-08-13** `b712016` | 2026-08-13 `b712016` | **9** |
| 2 | **2026-08-15** `b23598f` | 2026-08-15 `5b58e85` | **9** |
| 3 | **2026-08-15** `e9f2d13` | 2026-08-15 `e9f2d13` | **8** |

現樹引用處逐檔:

**[1] 非原始碼清單 / 判定邏輯**(9 檔)
`docs/agents/friction-log.md` ×7、`docs/tickets/framework-updates/09-the-update-path.md` ×3、
`.claude/hooks/gate.py` ×2、`docs/adr/0004-gate-self-modification.md` ×2、
`tests/test_gate.py` ×2、`.claude/portable/manifest.py` ×1、
`.claude/portable/shadow_review.py` ×1、`.claude/portable/sync.py` ×1、
`tests/test_bash_write.py` ×1

**[2] 回頭重掃 / F-082**(9 檔)
`docs/agents/friction-log.md` ×21、`docs/adr/F-0015-…` ×6、
`票 36` ×4、`票 39` ×4、`票 33` ×3、`.claude/portable/scanner.py` ×2、
`tests/test_scanner.py` ×2、`docs/audits/2026-08-15-…` ×1、
`docs/going-public-known-items.md` ×1

**[3] 同類入口 / F-083**(8 檔)
`docs/agents/friction-log.md` ×13、`票 29` ×6、`tests/test_bash_write.py` ×3、
`.claude/hooks/gate.py` ×2、`票 31` ×2、`票 32` ×2、
`docs/going-public-known-items.md` ×1、`票 36` ×1

---

---

## 落地紀錄(裁決 2026-08-15)—— **關票,不動任何 skill 檔**

量測收下。**不改任何 skill 檔**,理由不是「不重要」,是**改動的代價已知且具體**:

> 這 39 檔是**上游原檔**。改動即與上游位元不同 →
> **R3 provenance 豁免失效**,而且**每次上游更新都要手動合併**。

第二層理由是判準:**「該翻沒翻」目前零實例。**
依「痛點出現才加機制」,等實例再議 —— 沒有實例的改動,
付的是確定的成本、換的是假設的收益。

### 觀察名單:6 個缺觸發語的 `description`

**只登記,不改。** 出現「該翻沒翻」的實例時回到這張清單。

| skill | `description`(原文) |
|---|---|
| `grill-with-docs` | A relentless interview to sharpen a plan or design, which also creates docs (ADR's and glossary) as we go. |
| `handoff` | Compact the current conversation into a handoff document for another agent to pick up. |
| `implement` | "Implement a piece of work based on a spec or set of tickets." |
| `improve-codebase-architecture` | Scan a codebase for deepening opportunities, present them as a visual HTML report, then grill through whichever one you pick. |
| `to-spec` | Turn the current conversation into a spec and publish it to the project issue tracker — no interview, just synthesis of what you've already discussed. |
| `to-tickets` | Break a plan, spec, or the current conversation into a set of tracer-bullet tickets, each declaring its blocking edges, published to the configured tracker. |

**觀察指標**(出現任一即回來):
某次該用其中一個 skill 而沒被想起來、或用錯了另一個。
**要記的是實例本身(哪一次、該用哪個、實際用了什麼)**,不是「感覺不夠清楚」。

### 腳本項同理不動

13 個 skill 只有 1 支腳本,而 `.md` 內**指令碼區塊 0 個** ——
**零可見缺口**。沒有「有具體指令卻沒封成腳本」的實例可指,
所以沒有可據以改動的東西。

**票 40 關票。**

---

## 本票不做的事

- **不做結論**、不排優先序、不建議改法
- **不改任何檔案**(本票自己除外)
- 第 3 題的「本來可以封成程式」需要讀語意,**列為量不到**,不臆測
