# 117 — `pipeline.json` 沒有格式驗證,壞掉時票號靜默變 `null`

**狀態**:**candidate**(立案,不動工)
**立案**:2026-09-08,票 114 刀一 B-4 步驟 0 的**活標本**(不是巡檢挖出來的)
**來源**:`.dev/reports/2026-09-08T000653Z-ticket-114-b4-cut.md` 的候選 (e)
**站別**:立案時由票 114 佔用;動工前由裁決者改 `current_stage` 與 `ticket_id`
**估工**:**小** · **裝新下游前**:**待裁**

---

## 形狀:兩層,一層擋住了,另一層沒有

`.dev/pipeline.json` 是執行期狀態,**由人用編輯器手改**(`CLAUDE.md` 明文:
「跳過流程由使用者自行修改 `.dev/pipeline.json` 的 `current_stage`」),
而它壞掉時兩個讀它的東西行為**相反**:

| 讀的人 | 壞掉時 | 性質 |
|---|---|---|
| `gate.load_stage()`(`.claude/hooks/gate.py:1282-1295`) | 回 `UNREADABLE_STAGE`(`:1228`),R2 在**兩個時點**都擋(`:2166`),訊息說「修好 pipeline.json 再繼續」(`:2177-2182`) | **fail-closed,而且出聲** |
| `redlight.current_ticket()`(`.claude/hooks/redlight.py:60-70`) | 回 `None`,**紅燈照記**,`ticket_id` 寫成 `null` | **fail-silent** |

**⇒ 缺陷不在任何一層自己**:`load_stage` 的 fail-closed 是對的,
`current_ticket` 回 `None` 也完全照它自己的 docstring 走
(「**讀不到就是 None,不猜。** 猜一個票號的話,猜中的那次會靜默解鎖
一個根本沒有紅燈的修改」)。

**缺陷在兩層的交界:R2 擋住了寫入,而紅燈的記錄路徑沒有被擋** ——
於是 `.dev/test-runs.jsonl` 會長出 `"ticket_id": null` 的紀錄,
**而那份紀錄看起來是完整的**(欄位齊、格式對、時間對)。
R3 後續要靠票號把紅燈與實作對起來,對不起來的那些**不會有東西說話**。

這是 `CLAUDE.md` 那條「識別風險的品質越高,它偽裝成處置的能力越強」的機器版:
`current_ticket` 的 docstring 把風險寫得很準確,**而除了那段文字之外沒有東西在管它**。

## 活標本(不是假想案例)

2026-09-08 早上,裁決者手動編輯 `.dev/pipeline.json` 時第 4 行漏一個冒號:

```
  "ticket_id""114",
```

實測(票 114 步驟 0,原始輸出):

```
bytes = 116
b'{\n  "current_stage": "implement",\n  "feature": "framework-updates",\n  "ticket_id""114",\n  "updated": "2026-09-08"\n}\n'
json.loads -> FAILED: JSONDecodeError: Expecting ':' delimiter: line 4 column 14 (char 81)
redlight.current_ticket() = None
```

**那一次沒有造成損害**,因為 R2 先擋住了原始碼寫入,而當時還沒跑到會記紅燈的步驟。
**「這次沒事」與「這個形狀不會出事」是兩句話** —— 本票立的是後者。

## 待裁的設計問題(**立案時刻意不定死**)

驗格式的機器該掛在哪一層,三個位置各有代價:

| 位置 | 做法 | 代價 / 疑慮 |
|---|---|---|
| **寫入端** | —— | **沒有寫入端。** 這個檔是人用編輯器改的,`install.py:161/422` 只在安裝時產一次。「加在寫入端」在這裡等於「沒有加」 |
| **讀取端** | `current_ticket()` 讀不到時**出聲**(而不是靜默回 `None`) | 它是在 hook 裡被呼叫的,出聲要出到哪裡?寫進紀錄?那會讓紀錄多一個狀態。而**不得改成猜票號** —— 那條 docstring 的理由仍然成立 |
| **常駐測試** | 一條測試斷言 `.dev/pipeline.json` 可解析且 `current_stage` 在 `pipeline-stages.yaml` 的值域內 | `.dev/` 被 gitignore,CI 上那個檔是 `install.py` 產的,**測試在 CI 上恆綠** —— 「一個從來不會紅的綠燈是空的」(票 58 判準)。要真的咬,得在本機跑 |

**附加疑慮(要一起裁)**:`current_stage` 現在只有「讀得到 / 讀不到」兩態,
**沒有人驗它的值在不在 `pipeline-stages.yaml` 的 `stages[].id` 裡** ——
`CLAUDE.md` 寫著「合法值域由 `pipeline-stages.yaml` 的 `stages[].id` 決定」,
而那是一句散文,不是機制。打錯一個站名(`implment`)會走到哪條分支,本票要一併量。

## 為什麼是 candidate 不是直接做

三個位置的取捨會決定這條規則**擋誰**,而擋錯人的規則最後會被整條關掉(F-031 家族)。
先裁位置再動工。

## 交叉引用

- friction:`F-163`(pipeline.json 手動編輯無格式驗證)
- 票 114 刀一 B-4 的步驟 0 報告:`.dev/reports/2026-09-08T000653Z-ticket-114-b4-cut.md`
- `docs/adr/0005`(idle 在提交時放行 —— `load_stage` 不回 `idle` 的理由)
