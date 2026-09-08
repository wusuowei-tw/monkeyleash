# 120 — R3 的配對名對含連字號的檔名不可 import

**狀態**:**candidate**(立案,不動工)
**立案**:2026-09-08,票 114 刀二 B-3 量測時撞到
**來源**:票 114 各輪報告的候選清單 **(a)**
(`.dev/reports/2026-09-07T234821Z-ticket-114-b4-recon.md` 的 Q6)
**站別**:立案時 `implement`/票 114;動工前由裁決者改 `current_stage` 與 `ticket_id`
**估工**:**小** · **裝新下游前**:**待裁**

> **⚠ 出處與它為什麼現在才落到票面上**:這一項原本只活在 `.dev/reports/` 裡,
> 而 `.dev/` **不進版控** ⇒ **它原本會隨機器消失**。
> 票 114 已收,那些報告不再有票在指著它們,所以本輪把它落成票。

---

## 事實(實測,2026-09-07 / 複驗 2026-09-08)

`scripts/` 底下的 `.py`,以及 R3 會去找的配對測試名:

```
Q5 scripts/**/*.py count = 1 支
  scripts/ticket84-old-sha-probe.py

Q6 pairing (tests/test_<name>.py):
  scripts/ticket84-old-sha-probe.py -> tests/test_ticket84-old-sha-probe.py  exists=False
Q6 paired = 0 支 / 1 支
```

R3 的規則是「寫 `<name>.py` 但 `tests/test_<name>.py` 不存在 → 擋」。
對這個檔案,`<name>` = `ticket84-old-sha-probe`,配對名 = `tests/test_ticket84-old-sha-probe.py`。

**⚠ 那個檔名含連字號,不是合法的 Python 模組名 ——
所以即使有人建了它,`import` 不了、pytest 收集得到但無法被 `-k` 之外的方式引用。**

## 為什麼今天沒有咬

`scripts/` 在 `gate.NON_SOURCE_DIRS` 裡(理由欄逐字:
「維運腳本,不進產品線;變更由人直接驗證」),
所以 `is_source_path("scripts/x.py")` 回 **False**,R3 根本不管它。

**⇒ 這是一個「規則的邊界剛好蓋住了它」而不是「規則處理得了它」的狀態。**

實測(票 114 刀二):

```
  is_source_path('scripts/x.py'                  ) = False
```

## 為什麼仍然值得一張票

**因為那個保護來自一份會變的清單,不是來自 R3 本身。**

- `scripts/` 只在 `gate.NON_SOURCE_DIRS` 裡,**不在** `redlight._SEARCH_SKIP` 裡
  (票 114 刀二實測,那是兩份**刻意不同**的清單)。
  所以 `redlight.find_implementation` **會**走進 `scripts/`。
- 票 114 刀二的差集理由表對 `scripts` 那一筆寫下了**觸發條件**,逐字:

  > **觸發條件**:哪天 `scripts/` 長出 `tests/test_<name>.py` 配對,這條差異要重新裁。

- 而更一般的形狀是:**任何被 R3 管的目錄裡,只要有人建一個含連字號的 `.py`,
  R3 就會要求一個不可 import 的配對名。** 那時 R3 的訊息會叫人去建一個
  **建了也用不了**的檔案 —— 擋下訊息指向一條走不通的路。

## 待裁的方向(**不在立案時定死**)

| 方向 | 做什麼 | 代價 |
|---|---|---|
| 甲 | **R3 的配對名做標準化**(連字號 → 底線),兩種都接受 | 要決定「兩種都接受」還是「只接受標準化後的」;後者會讓既有的配對突然失效 |
| 乙 | **加一條規則:被 R3 管的 `.py` 檔名必須是合法模組名** | fail-closed 而且零判斷(檔名是封閉集合,`str.isidentifier()` 就答得出來)—— 符合「進權威層的門檻是零誤報 + 零判斷 + 便宜」 |
| 丙 | **只改擋下訊息**:配對名不可 import 時,訊息要說出來,不要叫人去建一個沒用的檔 | 最省,不改判定。但那條路仍然走不通,只是訊息誠實了 |
| 丁 | 不修,登記為已知 | 目前實際上就是這樣;但那個「不咬」依賴 `NON_SOURCE_DIRS` 的內容 |

**我的初步傾向是乙**(不是裁決):它把問題從「R3 要怎麼處理壞名字」
變成「壞名字進不來」,而後者**是封閉集合、可枚舉**
(`CLAUDE.md`:封閉且可窮舉時,枚舉勝過比對)。

## 順帶:那個檔本身要不要留

`scripts/ticket84-old-sha-probe.py` 是票 84 的一次性探針。
**本票不裁它的去留** —— 但動工時若決定刪掉它,這張票的實例就沒有了,
**而形狀還在**(下一個含連字號的檔案會再撞一次)。
**不要用「刪掉那個檔」當成修法。**

## 交叉引用

- 票 114 刀二的差集理由表(`tests/test_non_source_list_parity.py` 的 `ONLY_IN_GATE`)
- `.dev/reports/2026-09-07T234821Z-ticket-114-b4-recon.md` 的 Q5 / Q6
