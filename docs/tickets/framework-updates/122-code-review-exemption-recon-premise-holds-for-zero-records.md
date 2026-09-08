# 122 — code-review 的豁免對帳散文,前提對 0/329 筆成立

**狀態**:**candidate**(立案,不動工)
**立案**:2026-09-08,票 116 B-8 動工前驗裁決前提時撞到
**來源**:`.dev/reports/2026-09-08T035917Z-116-b8-cut.md`
**站別**:立案時 `implement`/票 116;動工前由裁決者改 `current_stage` 與 `ticket_id`
**估工**:**小~中** · **裝新下游前**:**待裁**

> **由來**:票 116 B-8 的裁決寫「散文那一端**本來就撲空**,改記編號不會讓它更糟」,
> 並附「若你量到不是這樣,停手回報」。**量出來不是撲空,是 100% 假陽性。**
> 裁決者當場更正,並裁「散文那一端另開一張票,不併進 B-8」。本票即那一張。

---

## 事實(實測,2026-09-08,三個 repo 逐筆)

那段散文住在 `.agents/skills/code-review/SKILL.md:75-82`
(源頭:`.claude/patches/apply_patches.py:81` 的 `BLOCK_EXEMPTION_RECON`,
由 `patch_exemption_recon()` 注入)。逐字:

```
- **Exemption reconciliation (local addition).** Read `.dev/gate-exemptions.jsonl` if it exists.
  Every line records a case where gate R3 waived the "must have a test file" rule because a ticket
  declared that module untested. For each line, open the ticket named in `declared_in` and confirm
  the module really is listed under `**Untested by decision:**`. Report any line whose ticket does
  not back it — that is a test-skip that was granted without a prior decision, which is the exact
  backdoor the exemption mechanism exists to prevent. Also report tickets whose declared-untested
  list has grown since the ticket was written, if the git history shows it.
```

**它有兩句,要分開驗:**

| | 句子 | 性質 |
|---|---|---|
| ① | 「Every line records a case where gate **R3** waived…because a **ticket** declared that module untested」 | **前提** |
| ② | 「**Report any line whose ticket does not back it**」 | **動作** |

### ① 前提:符合的紀錄 = **0 / 329 筆**

| repo | 帳本 | `reason` 分布 | 符合前提(`ticket-declared`) |
|---|---|---|---|
| 上游 monkeyleash | **219** 筆 | `gate-self-modification` 219 | **0 筆** |
| 下游①(影音) | **64** 筆 | `gate-self-modification` 54 / `upstream-provenance` 10 | **0 筆** |
| 下游②(台股資訊) | **46** 筆 | `gate-self-modification` 7 / `upstream-provenance` 39 | **0 筆** |
| **合計** | **329** 筆 | | **0 筆** |

**散文開頭那句描述的東西,一次都沒發生過。**

### ② 動作:觸發的紀錄 = **329 / 329 筆**

「open the ticket named in `declared_in`」—— 那些 ADR 檔**打得開**(都在),
**但都不含 `Untested by decision`**(三個 ADR 逐檔驗過,全部 `False`)。
所以「whose ticket does not back it」**對每一筆都成立**。

> **⇒ 不是撲空,是全中,而且方向相反。**
> 照它做的 agent 會報:「這 329 筆全部是**未經決定就發出的 test-skip 後門**」——
> **而它們一筆都不是 test-skip**(219 筆是 R2 閘門自我修改,49 筆是 R3 provenance)。
> **100% 假陽性。**

## 出貨狀態:已經在兩個下游身上

```
  上游 monkeyleash         SKILL.md 存在;含 Exemption reconciliation 段 = True
  下游①(影音)             SKILL.md 存在;含 Exemption reconciliation 段 = True
  下游②(台股資訊)         SKILL.md 存在;含 Exemption reconciliation 段 = True
```

`.agents/skills/` 在 portable-manifest 標 **`copy`** ⇒ **一定帶下去**。
**這不是上游的內部問題。**

## 為什麼「假陽性」比「撲空」貴得多

`F-031` 逐字:**壞掉的訊號訓練人忽略訊號。**

- **撲空** = 沒有輸出 = 沒有人被訓練。登記起來以後再說是合理的。
- **100% 假陽性** = 每一次 code-review 都吐出一整份「後門清單」 ⇒
  **讀的人會學會跳過整個 Exemption reconciliation 段** ——
  而那是這段散文**唯一**的執行者(**沒有任何程式在跑它**)。

**⇒ 它不是睡著的缺陷,是正在消耗信號預算的缺陷。**

## 家族

**`F-031`**(壞掉的訊號訓練人忽略訊號)——上面那段。

**`F-110`**(規矩寫下來了但沒變成機器)——**而本則是它更難察覺的一型**:
規矩不只沒變成機器,**它本身寫錯了,而且沒有東西在驗它的前提**。

> 那段散文對帳本做了一個**斷言**(「every line 是 R3 ticket-declared」),
> 而 `.agents/skills/` 底下沒有任何測試在驗那個斷言。
> **R5 只驗那段文字在不在**(`tests/test_r5_mounts.py` 把
> `Exemption reconciliation (local addition)` 當成掛載點標記),
> **不驗它說的話對不對。**
>
> ⇒ **「有掛載點」被當成了「內容正確」。**

## 待裁的設計方向(**立案不定死**)

**核心問題不是 `declared_in` 的格式,是散文的前提** ——
它假設帳本只有一種 reason,而實際有四種(票 116 B-8 實測)。
**票 116 把 `declared_in` 改成編號之後,那個前提還是錯的。**

初步方向(**不是裁決**):**對帳要依 `reason` 分支**。

| `reason` | 依據應該是什麼 |
|---|---|
| `ticket-declared` | **現在那條**:開 `declared_in` 指的票,確認模組列在 `**Untested by decision:**` 底下 |
| `gate-self-modification` | ADR `0004` 存在 + `file` 真的在 `GATE_SELF` 裡 —— **不是**找宣告 |
| `upstream-provenance` | ADR `F-0014` 存在 + 有對應的 provenance 紀錄 |
| `upstream-identical` | ADR `F-0016` 存在 + staged 內容與上游物件相同 |

**要一起裁的三件:**

1. **下游打不開那份 ADR 時怎麼辦?**(`docs/adr/` 標 `ask` 不出貨,
   而票 116 B-8 明寫「只讓帳本誠實,不讓 ADR 可達」)——
   報告「引用了一份我這裡沒有的 ADR」,還是靜靜跳過?**現在的散文沒有這一格。**
2. **這段散文要不要有測試?** 它現在只被 R5 驗「在不在」。
   驗「說得對不對」需要一份語料 + 一個能跑它的東西,而**執行者是 agent 不是程式** ——
   這一格與票 118(淨室 skip 沒有預期值)是同一族:**沒有機器在管的東西**。
3. **改散文要走 `bash scripts/skills-update.sh`**(更新 → 冪等重套 patch → gate 全規則驗證),
   而 R5 是那條規矩的機器保證。**動工時不得直接改 `.agents/skills/`**。

## ⚠ 一個**未證明**

> **「這段對帳大概從未被執行過」是推論,不是量測。**
> 論據是:若跑過,329 筆警報不可能沒有人提。**但那是關於人的推論,不是證據。**

本輪查過的地方(都沒有執行紀錄):

- `.dev/` 底下的帳本(`gate-exemptions.jsonl` / `test-runs.jsonl` / `intercepts-*.jsonl`)
  —— 只有 `test-runs.jsonl` 兩筆提到那個字串,而那是
  `tests/test_r5_mounts.py` 把它當**掛載點標記**在測,不是對帳被執行。
- `.dev/reports/` —— 7 份提到 `code-review`,**沒有一份含對帳輸出**;
  唯二提到 `Exemption reconciliation` 的是本輪自己產的兩份報告。

**⇒ 沒有找到執行紀錄。但 code-review 的執行在本 repo 本來就沒有留下帳本,
所以「找不到」不等於「沒跑過」。標為未證明,不編。**

## 交叉引用

- 票 116 B-8(`declared_in` 記編號)—— 本票是它裁決過程中量出來的副產物
- 票 118(淨室 skip 沒有理由也沒有預期值)—— 同族:沒有機器在管
- `F-031` / `F-110`
- `CLAUDE.md` 的 skills 更新規矩(唯一入口 `bash scripts/skills-update.sh`,R5 是機器保證)
