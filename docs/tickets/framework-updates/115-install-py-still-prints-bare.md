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

## ✅ 落地(2026-09-09)—— 裁決「甲+」

### 動工前量到的三件(都與票面原本的預期不同)

| | 票面原本 | 實測 |
|---|---|---|
| 互動提示 | 「`install.py` 若有同型的東西,照同一條裁決」 | **`install.py` 沒有任何 `input()`** ⇒ 那一條**沒有對象**,不必處理 |
| 21 這個數字 | `grep "^\s*print("` 數的 | 用 `ast`(與 `_print_calls` 同一支判準)重數**也是 21** ⇒ 數字站得住,**但對的理由是這一支剛好沒有跨行 `print`,不是判準對** |
| 「四支既有實作可抄」 | `def _out` 數的 4 支 | 家族實為 **`def` 4 份 + inline 5 處 = 6 個檔案**(見上方〈動工前置〉(c)) |

### 裁一:抄類 A,**不抄 `user_layer._write`**

`install.py` 從零加一支 `_out`:補 `"\n"`、前置 `sys.stdout.flush()`、
`sys.stdout.buffer.write(...encode("utf-8"))`、`flush`。
**沒有 `try/except` 退回 `stream.write`。**

**三條理由**:

1. **「pytest 抓輸出會不會炸」不成立** —— `tests/test_portable_output_encoding.py`
   **自己造** cp950 主控台(`io.TextIOWrapper` 換掉整個 `sys.stdout`),
   被測程式拿到的 `.buffer` 就是底下那個 `BytesIO`。**`subprocess` / `capsys` / `capfd` 三者零命中。**
2. **`user_layer._write` 的 `except` 退回的是 `stream.write(msg)`** ——
   **在 cp950 上那條照樣會炸**。它沒有救到任何東西,只是把「為什麼炸」藏起來。
3. **票 62 要消掉的正是「炸掉時看不出來」。fail-soft 就是那個東西本身。**

這一條由 `TestInstallOutWritesUtf8Bytes::test_out_does_not_swallow_the_reason`
用 `ast` 釘住(**不是行為測試** —— fail-soft 的症狀是「沒有症狀」,行為看不見它)。

### 裁二:**列舉**,不做目錄全掃

`parametrize` 加入 `"install.py"`(四支);
class 更名 `TestNoBarePrintRemainsInTheThreeTools` → **`TestNoBarePrintRemainsInTheListedModules`**
(名字裡不再有任何數量詞,票 94)。

**為什麼不能全掃**(已寫進 class docstring,不留在對話裡):
其餘模組**刻意保留** cp950 編得動的 `print`(`_carries` 的 docstring 逐字:
「那是範圍,不是遺漏」)⇒ **全掃會把「刻意保留」報成「還沒改」,那是一條會誤擋的規則。**

**代價也寫進去了**:列舉會漏 —— 新增一支有裸 `print` 的工具時這條不會叫,
除非有人記得加進清單。另補一條 `test_the_listed_modules_are_the_ones_that_exist`
擋住「清單打錯名字」那個失敗方式。

### 裁三:不碰 `.agents/legacy-no-redlight.txt`

`install.py` 在該清單第 23 行 ⇒ **R3 整條豁免** ⇒ 紅燈只能來自測試那一側。
**動完之後該不該把它拿掉,本票不處理,不夾帶**(那會動到
`TestLegacyNoRedlightList`,而那是票 124 的題目)。

### ⚠ 撤回一個說法:**「端到端由 CI 淨室守著」在編碼這一格不成立**

`tests/test_install.py:339-341` 寫著「端到端由 CI 的淨室驗證守著」——
**那句話對它自己的題目(`core.hooksPath`)成立,對編碼這一格不成立**:

```
$ grep -n "runs-on" .github/workflows/tests.yml
20:    runs-on: ubuntu-latest
```

**CI 跑 Linux ⇒ locale 是 utf-8 ⇒ cp950 在那裡不會發生。**
淨室證得到「安裝跑得完」,**證不到「cp950 主控台上不會炸」**。

> **⇒ 票面不得把淨室算成這一格的覆蓋。**
> 唯一的覆蓋是 `TestInstallOutWritesUtf8Bytes`(它自己造 cp950 情境,
> 所以在 Linux 上一樣會紅)。
> `F-113` 的同一條反過來用:**不要拿一個不會發生的環境去宣稱覆蓋。**

### 紅燈先行(順序沒有顛倒)

先只加 `parametrize`、**還沒動 `install.py`** 時跑:

```
E       AssertionError: install.py 還有 21 個裸 print(行號 [503, 504, 505, 506, 507, 509, 514, 515, 516, 517, 518, 519, 540, 521, 529, 536, 537, 539, 542, 523, 532])—— 輸出要走 _out,否則同一份輸出裡會有兩種編碼:留著的 print 走 locale(Windows 上是 cp950),_out 走 utf-8。
FAILED tests/test_portable_output_encoding.py::TestNoBarePrintRemainsInTheThreeTools::test_the_module_has_no_bare_print[install.py]
1 failed, 15 passed in 0.16s
```

改完之後 `grep -c "print(" .claude/portable/install.py` = **0**。

### 驗收

```
$ python -m pytest -q tests/test_portable_output_encoding.py tests/test_install.py
44 passed in 1.55s

$ PYTHONIOENCODING=utf-8 python -m pytest -q -p no:randomly --tb=short
1589 passed, 3 skipped, 3 xfailed in 109.90s (0:01:49)
```

**1583 → 1589,+6,逐條指得出來**:

| 來源 | 條 |
|---|---|
| `parametrize` 多一個 `install.py` | **+1** |
| `test_the_listed_modules_are_the_ones_that_exist`(新) | **+1** |
| `TestInstallOutWritesUtf8Bytes`(新,四條) | **+4** |

### ⚠ 一個本票**沒有**處理的殘留

更名之後,`.claude/portable/shadow_review.py:651` 的註解裡仍寫著舊名
`TestNoBarePrintRemainsInTheThreeTools`。**沒有改,而那是刻意的**:

`shadow_review.py` **不在** `legacy-no-redlight` 上 ⇒ 改它(即使只是註解)
需要一筆屬於本票、記在 `tests/test_shadow_review.py` 上的紅燈 ——
**而純註解修改造不出那種紅燈**。那正是**票 119** 的題目。

**登記在這裡,不繞過。**(票 62 的票面 `:426` 也有一處舊名,同理未動 —— 那是歷史紀錄,`F-036`。)

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
