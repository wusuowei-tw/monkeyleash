# 票 128 —— `endpoints_match()` 在零證據時回 `True`,而 `report()` 正在印它

**狀態**:立案。**本票今日只立案,未動工。**
**發現於**:2026-09-09,上游桌機(hostname `DESKTOP-T2I45T1`),上游 HEAD `3a37399`。
**排期**:筆電期(2026-09-10 – 2026-09-28)。
**來源**:第六站(GPT 視窗)在 HEAD `3a37399` 上量到,交由本窗立案。

> **⚠ 材料出處分兩層,本票逐節標明。**
> 標「**第六站**」的:材料來自第六站(GPT 視窗),**本窗未重跑**。
> 標「**本窗**」的:2026-09-09 由本窗從本機檔案直接讀出。

---

## 現象

`endpoints_match()` 比的是「第一筆的 `content_hash`」與「最後一筆的 `result_hash`」。
兩端都用 `.get()` 取值,**兩端都取不到時各回 `None`,而 `None == None` 為真**
⇒ 一條**兩端都沒有雜湊證據**的帳本,會被判成「首尾相等」。

它處理了空鏈(`if not records: return False`),**沒有處理「有紀錄但沒有端點證據」**。
而**同一支模組的 docstring 逐字寫著這條判準**:

> 空鏈回 `False`:沒有端點可比,而**「沒有證據」不得回報成「證明了」**。

**它把自己寫下的那條判準,在隔壁那一行違反了。**

---

## 證據

### 一、函式原文(**本窗**從 `.claude/portable/ledger_verify.py:240-252` 讀出)

```python
def endpoints_match(records):
    """第一筆的 `content_hash` 是不是等於最後一筆的 `result_hash`。

    **這只回答「有沒有走回起點」,不回答「路上有沒有斷」** —— 後者問 `chain_breaks()`。
    兩個述詞分開存在,是因為它們可以同時給出不同答案(v1 的整個缺陷)。

    空鏈回 `False`:沒有端點可比,而**「沒有證據」不得回報成「證明了」**。
    """
    if not records:
        return False
    return records[0].get("content_hash") == records[-1].get("result_hash")
```

判準那句在 `:248`,失效那行在 `:252` —— **相隔四行。**

### 二、帳本首尾兩筆的原始行(**本窗**從 `.dev/gate-exemptions.jsonl` 讀出)

```
$ head -1 .dev/gate-exemptions.jsonl
{"file": ".claude/hooks/gate.py", "module": "gate", "ticket": null, "declared_in": "docs/adr/0004-gate-self-modification.md", "reason": "gate-self-modification"}

$ tail -1 .dev/gate-exemptions.jsonl
{"ts": "2026-09-08T05:39:36.831024+00:00", "file": ".claude/hooks/gate.py", "module": "gate", "ticket": "116", "stage": "implement", "declared_in": "0004", "reason": "gate-self-modification", "tool": "pre-commit", "outcome": "granted", "blocked_by": null, "at_commit": true, "content_hash": "771d0a9ea3dbc0ec9a2b5bc8117ddde586d2e96c54a52d2ca3bd288535d89d5f", "result_hash": null, "changes_bytes": null}
```

**第一筆完全沒有 `content_hash` 這個鍵**(整行只有五個欄位)⇒ `.get()` 回 `None`。
**最後一筆有 `result_hash`,值是 `null`** ⇒ 取出來也是 `None`。
⇒ `None == None` ⇒ **`True`**。

### 三、第六站量到的判定結果(**材料來自第六站(GPT 視窗),本窗未重跑**)

```
first = {at_commit: <MISSING>, content_hash: <MISSING>, result_hash: <MISSING>}
last  = {at_commit: true,      content_hash: "771d0a…",  result_hash: null}
endpoints_match = True
```

> **⚠ 這一格是本票唯一的獨立性檢查,寫出來讓人自己看得出來:**
> 第六站描述的 `first` 缺三個鍵、`last` 的 `result_hash` 是 `null` ——
> 而**本窗用不同的工具(`head`/`tail`)、在不同的視窗、從同一份檔案**讀出的原始行
> **與那個描述吻合**。
> **吻合的是輸入,不是結論** —— `endpoints_match = True` 這個**實際執行結果**
> 本窗**沒有跑**(本輪禁止跑 `.py`),它仍然只有第六站一個來源。
> 本窗能說的是:**由上面兩行原始資料推出來的值就是 `True`**,而那是推論不是量測。

### 四、消費端 —— **本窗量到了**(更正裁決那一格)

> **⚠ 裁決原文寫著「本輪未量,標未證明」。本窗量了,所以這一格不標未證明。**
> 記下這個更正是因為:一格標成「未證明」而其實量得到,
> 下一個讀票的人不會回來重量 —— 它會一直是未證明。

```
$ grep -rn "endpoints_match" --include=*.py .
./.claude/portable/ledger_verify.py:242:def endpoints_match(records):
./.claude/portable/ledger_verify.py:283:    out.append("首尾相等            : %s" % ("是" if endpoints_match(records) else "否"))
./tests/test_ledger_verify.py:357:    v1 只有 `endpoints_match` 那一半,而它在斷鏈上照樣回 True。
./tests/test_ledger_verify.py:364:        assert lv.endpoints_match(BROKEN) is True, "測試語料的首尾本來就該相等"
./tests/test_ledger_verify.py:371:        assert lv.endpoints_match(CONTINUOUS) is True
./tests/test_ledger_verify.py:381:        assert lv.endpoints_match(half) is False
./tests/test_ledger_verify.py:386:        assert lv.endpoints_match([]) is False
```

`report()` 的那一行(**本窗**讀出,`ledger_verify.py:280-283`):

```python
    out.append("")
    out.append("筆數                : %d" % len(records))
    out.append("相鄰對              : %d" % total_pairs)
    out.append("首尾相等            : %s" % ("是" if endpoints_match(records) else "否"))
```

**⇒ 裁決的兩個分支裡,成立的是第二個:`report()` 在印它。**
**⇒ 這支 CLI 在本機這份 223 筆的帳本上,印出來的是「首尾相等 : 是」,而那是一句假話。**

---

## 為什麼要緊

**一、它違反的是它自己寫下的判準,而判準就在四行之前。**
`:248` 的那句話不是外部規矩,是這支模組的作者為了這個函式寫的。
**判準寫在正確的地方、正確的時點,而它沒有變成機制**(`F-110` 的形狀)。

**二、它與票 116 B-6 修掉的那個 fail-open 是同一族,同一支檔案。**
B-6 修的是 `chain_breaks` 的 `.get()` → `None == None` → 判成「連得上」;
本則是 `endpoints_match` 的 `.get()` → `None == None` → 判成「首尾相等」。
**同一個機制、同一支檔案、隔幾十行。**

> **B-6 修完之後沒有回頭掃同一支檔案。**
> `CLAUDE.md` 逐字:「命中修復後,搜尋半徑至少是『同檔同類』」——
> 而理由也逐字寫在那裡:「**『我剛剛看過這個檔案』感覺像是查過了**」。
> `F-080` / `F-082` / `F-083` / `F-085` 是同一條線,**本則是它在本 repo 的第 n 個實例**
> (**刻意不寫 n** —— 計數住在 friction log,不住在票面)。

**三、有消費端 ⇒ 它不是睡著的缺陷。**
若沒有人消費,它只是一個不會被叫到的錯答案;
**而 `report()` 在印它,所以每一次跑這支 CLI 的人都會讀到一句被證實為假的話。**
`F-031`:壞掉的訊號訓練人忽略訊號 —— 這裡更糟一階,
因為它印的是**「是」**(看起來像好消息),不是一個會引人去查的警報。

---

## 方向(**立案不定死**)

初步(**不是裁決**):
零證據時應該回 `False`,理由與空鏈那格一樣(`:248` 那句)。
判「有沒有證據」的位置要想清楚是**鍵在不在**還是**值是不是 `None`** ——
票 116 B-8 已經把產生端釘成「兩個鍵必須在,值可以是 `None`」,
所以**新寫入的紀錄靠鍵存在分不出來**,得看值。
而第一筆那種**舊格式、連鍵都沒有**的紀錄,兩種判法都會落進同一邊。

**同時要問的**:`report()` 那一行印「是/否」兩值,
而現在有第三種狀態(**無從判定**)—— 這與 B-6 給 `chain_breaks` 加第四桶是同一個形狀。

---

## 未證明

- **本窗沒有跑過 `ledger_verify.py`**(本輪禁止跑 `.py`)⇒
  `endpoints_match = True` 與 `report()` 的實際輸出,**只有第六站一個來源**;
  本窗貼的是**輸入**(原始行)與**原始碼**,由它們推出結論。**推論不是量測。**
- **沒有量兩個下游的帳本**(本輪不碰下游)⇒
  下游① 64 筆 / 下游② 46 筆(數字出自票 122,**立案時的量**)首尾長什麼樣,未知。
  `.claude/portable/` 標 `copy` ⇒ **這支模組已經在下游身上**,而它們的帳本內容不同。
- **沒有量修法會不會打壞既有斷言。** `tests/test_ledger_verify.py:364` 逐字是
  `assert lv.endpoints_match(BROKEN) is True`(語料的首尾本來就相等,是合法案例),
  改行為之前要先確認那四條斷言各自釘的是什麼。**本輪未跑測試。**
- **沒有量這支 CLI 有沒有人在跑。** 有消費端 ≠ 有人消費;
  與票 122 的最後一格同形(「找不到執行紀錄」不等於「沒跑過」)。

---

## 交叉引用

- **票 116 B-6**(`chain_breaks` 分四桶 + 已知斷點白名單)—— 同檔同族,先修的那一半
- **票 122**(對帳散文的前提對 0 筆成立)—— 同一份帳本的另一個讀者
- **票 129**(反控驗副本不驗真接縫)—— 同日立案;本則若當初有一條反控,會被咬出來
- `F-031` / `F-080` / `F-082` / `F-083` / `F-085` / `F-110`
