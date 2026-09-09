# 票 129 —— 反控驗的是自己抄的副本,不是它宣稱在守的那道接縫(家族票)

**狀態**:立案。**本票今日只立案,未動工。**
**發現於**:2026-09-09,上游桌機(hostname `DESKTOP-T2I45T1`),上游 HEAD `3a37399`。
**排期**:筆電期(2026-09-10 – 2026-09-28)。
**性質**:**家族票**。底下兩例是**入口**,不是題目本身。

---

## 現象

**反控**(counter-control)在本 repo 的用途是回答一句話:
「上面那組斷言真的會咬嗎,還是它恆綠?」——
因為 `CLAUDE.md` 那條:**恆真的斷言與有效的斷言,在測試輸出上長得一模一樣。**

而有一族反控,**驗的是它自己在函式體內抄的一份副本**,
或**驗了一個與票面指定的案例不同的案例** ——
副本綠了,**被守的那道真接縫一次都沒被走過**。

> **這一族的危險在於它讀起來比沒有反控更安全。**
> `CLAUDE.md` 逐字:「識別風險的品質越高,它偽裝成處置的能力越強」——
> 一條寫得很好、docstring 講清楚它在防什麼的反控,
> **正是最不會有人回去讀它函式體的那一條。**

---

## 證據(**本窗**從檔案讀出;兩例都是既有票的落地物)

### 例一 —— 票 114:反控重抄了一份 AST 列舉,沒有呼叫被守的那支 helper

被守的斷言(`tests/test_ticket_lookup.py:182-185`):

```python
    @pytest.mark.parametrize("name", FORBIDDEN)
    def test_the_module_does_not_import_the_forbidden_ones(self, name):
        assert name not in self._imported_names(), (
            "%s 被 %s import 了 —— 裁 3 的隔離就沒了(mcp_server 會 import 這支)"
            % (name, SRC.name))
```

被守的那支 helper(`:187-197`):

```python
    @staticmethod
    def _imported_names():
        import ast
        tree = ast.parse(io.open(str(SRC), encoding="utf-8").read())
        mods = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods.add(node.module.split(".")[0])
        return mods
```

反控本身(`:199-213`):

```python
    def test_the_ast_check_would_actually_catch_a_forbidden_import(self):
        """**反控**:證明上面那組枚舉真的會咬,而不是恆綠。

        少了它,`_imported_names()` 寫錯(例如回空集合)會讓每一條都綠 ——
        而**恆真的斷言與有效的斷言在測試輸出上長得一模一樣**。
        """
        import ast
        tree = ast.parse("import subprocess\nfrom gate import x\nimport os\n")
        mods = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods.add(node.module.split(".")[0])
        assert {"subprocess", "gate"} <= mods, mods
```

**`_imported_names` 在這條反控裡一次都沒有出現。**
它重抄了同一段 `ast.walk` 迴圈,然後驗那份副本會咬。

> **⇒ 把 `_imported_names()` 改成 `return set()`,`:182` 那組四條全綠,
> 而 `:199` 這條反控**照樣綠** —— 它走的是自己的副本。**
>
> **而那正是它的 docstring 逐字說它在防的事**:
> 「少了它,`_imported_names()` 寫錯(**例如回空集合**)會讓每一條都綠」。
> **它點名了它擋不住的那個案例。**

同族併記:`tests/test_ticket_lookup.py:215-223` 的 `test_prose_mentioning_the_forbidden_names_is_not_a_hit`
**有**呼叫 `self._imported_names()`(`:223`)—— **同一個類別裡,一條走真接縫、一條走副本。**
`F-058`:重複的實作一定會漂。

### 例二 —— 票 116:票面指定「拿掉其中一個鍵」,實作拿掉兩個

票面(`docs/tickets/framework-updates/116-the-ledger-and-its-readers-disagree.md:258`):

```
> 配一條反控:拿掉其中一個鍵的紀錄必須落進「無從驗證」桶,否則那條路徑又變回 fail-open。
```

實作(`tests/test_ledger_verify.py:309-322`):

```python
    def test_dropping_a_key_would_be_caught(self):
        """**反控**:證明上面兩條會咬,而不是恆綠。

        拿掉其中一個鍵的紀錄,必須被歸進「無從驗證」桶。
        """
        rec = gate.exemption_record(
            {"file": "pkg/thing.py", "module": "thing", "ticket": "01",
             "declared_in": "0004", "reason": "gate-self-modification"},
            None, False, "implement", "01", "x = 1\n")
        stripped = {k: v for k, v in rec.items()
                    if k not in ("content_hash", "result_hash")}
        b = lv.chain_breaks([stripped, dict(stripped)])
        assert len(b[lv.BUCKET_UNVERIFIABLE]) == 1, (
            "少了兩個雜湊鍵的紀錄沒有落進「無從驗證」桶 —— 那條路徑又變回 fail-open:%s" % b)
```

**`:319` 一次拿掉兩個鍵。** 函式名(`dropping_a_key`,單數)與 docstring(`:312`「其中一個鍵」)
說的是一個,**而失敗訊息 `:322` 自己寫「少了兩個雜湊鍵」** ——
**證據就在同一條測試的三個位置裡互相矛盾,而它是綠的。**

⇒ **票面指定的那個案例(只少一個鍵)從來沒有被驗過。**
「只少 `result_hash`」或「只少 `content_hash`」會落進哪個桶,**目前不知道**。

> **⚠ 票 116 已 `done`。依 `F-036`,本票不修改 116 的任何一個字,只從這裡指過去。**

---

## 真正的題目(**這才是本票**)

**這個 repo 還有多少反控,驗的是副本而不是真接縫?**

**動工的第一步是全庫盤點,不是修上面那兩條。**
先修兩條的話會得到「處理過了」的感覺,而母體從來沒被數過 ——
那正是 `CLAUDE.md`「修好一個偵測器之後回頭重掃既有資料」那條在講的:
**新規則的第一次全量掃描,問的不是「以後會不會再犯」,是「以前犯過幾次」。**

### 盤點的規模(**本窗量到,帶單位**)

| 量的東西 | 值 | 指令 |
|---|---|---|
| `tests/` 底下的 `.py` 檔 | **46 支** | `find tests -name "*.py" \| wc -l` |
| 其中含「反控」字串的 `.py` 檔 | **30 支** | `grep -rln --include="*.py" "反控" tests/ \| wc -l` |
| 「反控」出現的**行數**(`.py`) | **134 行** | `grep -rn --include="*.py" "反控" tests/ \| wc -l` |
| 全庫(排除 `__pycache__`)含「反控」的 `.py` 檔 | **33 支** | `grep -rln --include="*.py" "反控" . \| grep -v __pycache__ \| wc -l` |
| 函式名含 `would_actually` / `would_be_caught` / `actually_catch` 的測試 | **4 支** | `grep -rn "def test_.*\(would_actually\|would_be_caught\|actually_catch\|really_catch\)" tests/ \| wc -l` |

> **⚠ 這幾個都是【字串出現數】,不是【反控數】。**
> 一條反控可以佔好幾行「反控」,而一行「反控」也可能只是散文在提它。
> **盤點時要逐條看,不得拿這幾個數當母體。**(`F-109`:數字要帶單位與基準。)
> 反過來也成立:**不叫「反控」的反控不會被這幾個數抓到** ——
> 例如 `test_prose_mentioning_the_forbidden_names_is_not_a_hit`(它自稱「歸因反控」)。
> **這是比對,而比對的漏是未知的。**

### ⚠ 併記一格:量這張票的時候,我自己踩了一次同樣的形狀

第一次數「含反控的檔」得到 **60 支**,而其中 **30 支是 `tests/__pycache__/` 底下的 `.pyc`**
—— **我數到的是編譯後的副本,不是原始碼。**
排除之後才是 30 支 `.py`。

> **記在這裡當標本,因為它就是本票的形狀:量到了一個副本,而副本會給出合理的數字。**
> 沒有東西會說那是副本 —— `grep` 只看得到字元
> (`CLAUDE.md`「這一行是【資料】還是【關於資料的說明】」的同一句話,換到檔案層)。

### 盤點要問的兩個問題(逐條)

| | 問句 |
|---|---|
| ① | 這條反控,有沒有**呼叫**被守的那支函式 / 走被守的那條路徑?還是在函式體內重抄了一份? |
| ② | 這條反控驗的案例,與**票面 / docstring 指定的案例**是不是同一個? |

**② 抓得到 ① 抓不到的那一型**(例二就是),反之亦然 ——
**參照物不同,盲區就不同**(`CLAUDE.md`「驗兩個方向」那條)。

### 判準草案(**不是裁決**)

一條反控要能回答:「**把被守的那個東西打壞,這條會不會紅?**」
能回答的唯一方式是**它真的呼叫了那個東西**。
副本能證明的只有「這段邏輯抄對了」,**而那件事由構造成立**
(`CLAUDE.md`「材料若來自被量的對象,它證明的是這個對象跟它自己一致」)。

---

## 未證明

- **兩例都沒有實際失效過** —— 沒有量到它們曾經放過一個真缺陷。
  本票主張的是「它擋不住它宣稱擋的那件事」,**不是**「它已經害過人」。
  (`F-149`:命題與嚴重度分開寫。)
- **沒有把 `_imported_names()` 打樁成回空集合跑一次全套。** 本輪禁止跑測試 ⇒
  「四條會全綠、反控照樣綠」是**從原始碼推出來的**,不是量出來的。
  **這是本票最該補的一格,而且它便宜。**
- **沒有量例二「只拿掉一個鍵」時 `chain_breaks` 會落進哪個桶。** 同上,未跑。
- **盤點尚未做。** 目前是「已逐條看過 2 條 / 母體未知」——
  上表那幾個字串數**不是**母體,只是找母體的起點。
- **沒有看下游。** 本輪不碰下游。`tests/` 在 portable-manifest 是**逐檔標記**,
  哪幾條反控出貨到下游、哪幾條沒有,未量。

---

## 交叉引用

- **票 114**(ticket_lookup 那一刀)—— 例一的出處,已 `done`
- **票 116**(帳本與讀它的人不一致)—— 例二的出處,已 `done`;`F-036` ⇒ 不改它
- **票 128**(`endpoints_match` 零證據回 `True`)—— 同日立案;
  **那個缺陷若當初有一條走真接縫的反控,會被咬出來**
- **票 118**(淨室 skip 沒有理由也沒有預期值)—— 同族:**沒有機器在管的東西**
- `F-032`(綠燈綠錯原因)/ `F-058`(重複實作一定會漂)/ `F-109`(數字要帶單位)
- `CLAUDE.md`「識別風險的品質越高,它偽裝成處置的能力越強」
