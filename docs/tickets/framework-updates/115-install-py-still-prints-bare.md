# 115 — `install.py` 的 21 筆裸 `print`(票 62 家族的第四支)

**狀態**:**candidate**(立案,不動工)
**立案**:2026-09-07,第六站(arch)第二次診斷 → **B 桶 B-5**
**來源**:`docs/audits/2026-09-07-arch-round-2.md` 的 **B-5**;家族:票 62
**站別**:立案時 `idle`;動工前由裁決者改 `current_stage` 與 `ticket_id`
**估工**:**小** · **裝新下游前**:**要**

---

## 事實(實測,2026-09-07)

`.claude/portable/` 的裸 `print` 逐檔清點(單位:筆):

```
install.py       21
其餘 14 支        0
```

**21 筆全部在 `install.py`**,而票 62 登記的數字**今天仍然對得上** —— 那張票還開著。

**受害符號**:`install.py` 的 `print(...)`(**安裝完成報告那一整段**:
「裝好了」「複製 N 個檔案」「權威層」「可攜層」「go-live」「閘門實測」…)。

> ⚠ **計數方法的坑,順手記**:`grep -c "print("` 對 `gate.py` 回 3,
> 三筆全是 `cmd_fingerprint(` 的子字串 —— **量測工具自己踩了邊界族的判準**。
> 正確的計數是 `grep -c "^\s*print("`。

## 為什麼是缺口不是設計

票 62 的測試檔 `tests/test_portable_output_encoding.py` **自己寫下了這一格**:

> **所以** `print` 都改走 `_out` —— **那是另一個範圍,不在本票。**

**那句話是一張沒有主詞的祈使句**(`F-110` 的形狀):它正確地指出了下一步,
而**沒有任何東西會因為它沒被做而叫**。本票就是那個主詞。

技術上的後果與票 62 一字不差:
`print` 走文字層(Windows 主控台是 cp950),`_out` 走二進位層(utf-8)——
**同一份輸出裡兩種編碼**;而 `install.py` 的輸出**恰好是下游第一次見到這個框架的畫面**。

## 修法

照票 62 的形狀,不發明新的:

- `install.py` 加一支 `_out`(四支既有實作可抄:`g1_verify` / `shadow_review` /
  `user_layer` / `verify_gates` 各有一份 —— **⚠ 這四份本身就是 B-4 那個「多份實作」的形狀**,
  但本票**不合併它們**,那是票 114 的判準延伸,不夾帶)。
- 21 筆 `print` 逐筆改走 `_out`。
- **不動互動提示**:`shadow_review` 那張票已裁過 `input()` 的提示字串不改
  (改了會讓提示與輸入游標換行分開,那是動互動行為不是動編碼)。
  `install.py` 若有同型的東西,照同一條裁決。

## 紅燈形狀(一句)

> 把 `install.py` 加進 `tests/test_portable_output_encoding.py::TestNoBarePrintRemainsInTheThreeTools`
> 的掃描範圍(該 class 名字屆時要改,**它現在寫死了「三支」**),
> 它會報「`install.py` 還有 21 個裸 print(行號 …)」而紅;逐筆改完轉綠。

> ⚠ **順帶的判準**:那個 class 名字裡的「Three」是**寫死的計數** ——
> 與票 94「六站是名字不是計數」同一族。改的時候一起處理,不要留一個
> 叫「三支」而掃四支的測試。

---

## ⚠ 動工前置(2026-09-08 落地,來源:票 114 各輪報告的候選清單)

> **這兩項原本只活在 `.dev/reports/` 裡,而 `.dev/` 不進版控** ——
> 也就是說**它們原本會隨機器消失**。落到票面上是為了讓它們跨得過下一台機器。
> (票 114 已收,那些報告不再有票在指著它們。)

### (c) ⛔ 票面「四支」這個數字**已過期**,動工前要先定掃描範圍

上面〈修法〉寫「四支既有實作可抄:`g1_verify` / `shadow_review` / `user_layer` / `verify_gates`」。
**那是照 `def _out` 數出來的,而家族比它大。**

實測(票 114 刀一,2026-09-08):

```
$ grep -rn "def _out" .claude/portable/ .claude/hooks/ --include=*.py
.claude/portable/g1_verify.py:44:def _out(text):
.claude/portable/shadow_review.py:101:def _out(text):
.claude/portable/user_layer.py:470:def _out(msg):
.claude/portable/verify_gates.py:38:def _out(text):
```

**但同一個寫法還有 inline 的 5 處**,`grep "def _out"` 撈不到:

```
.claude/portable/sync.py:702 / :709 / :720 / :746   (4 處,無函式包裝)
.claude/portable/ledger_verify.py:162               (1 處,無函式包裝)
```

**⇒ stdout utf-8 輸出家族 = `def` 4 份 + inline 5 處,共 6 個檔案。**

**動工前要裁的是**:本票的「抄一份 `_out`」要抄哪一種、
以及那個測試 class 的掃描範圍寫 **4** 還是 **6**。
**寫 4 的話,`sync.py` 與 `ledger_verify.py` 那 5 處永遠不在任何測試的視野裡。**

> **這一格是 `F-109` 的形狀**:票面寫下一個會變的數字而沒有標基準。
> 「四支」在寫下的當時是對的(它量的是 `def _out`),
> 而讀的人會以為它量的是「這個家族有幾份」。

### (b) `_out` 家族的四份**方向不一致**,合併前要先裁哪一個對

`tests/test_portable_output_encoding.py` 的 docstring **自述只涵蓋三支**,逐字:

> `verify_gates.py` / `g1_verify.py` / `shadow_review.py` 都是**「證明別的東西是對的」那一類工具**

⇒ **`user_layer.py` / `ledger_verify.py` / `sync.py` 三支不在那份測試的視野裡。**

而 `user_layer._write`(`:455-467`)與另外三份**方向相反**:

```python
    try:
        stream.buffer.write(msg.encode("utf-8"))
        stream.buffer.flush()
    except Exception:
        stream.write(msg)          # ← fail-soft:退回會炸的那條路
```

三個具體差異(票 114 刀一實測):
1. **不補 `"\n"`**(類 A 是 `(text + "\n")`)。
2. **沒有前置 `sys.stdout.flush()`** —— 類 A 那一行是為了避免文字層/二進位層交錯。
3. **有 `try/except` 退回 `stream.write(msg)`** —— **類 A 是 fail-loud,這一份是 fail-soft。**

**⇒ 本票若把 `install.py` 也加進來,要先裁「哪一個方向是對的」** ——
抄錯一份就是把 fail-soft 散播到第五個檔案,
而 fail-soft 在這一族的後果正是票 62 要消掉的東西(炸掉時看不出來)。

**本票不強制合併那四份**(上面〈修法〉已寫「不夾帶」),
但**必須明說抄的是哪一份、為什麼**。

## 裝新下游前要不要

**要,而且是這一批裡最直接的一件。**
`install.py` 的輸出是**下游第一次跑安裝時看到的畫面**;
在 cp950 主控台上那 21 行會是亂碼,而**看不懂的第一印象比看不懂的擋下訊息更貴** ——
後者至少還有 pre-commit 擋著,前者只會讓人以為裝壞了。
