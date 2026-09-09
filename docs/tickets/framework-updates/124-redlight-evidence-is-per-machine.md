# 票 124 —— 紅燈證據是 per-machine 的,而 CI 用 `--deselect` 把它蓋住了

**狀態**:立案。**本票今日只立案,未動工。**
**發現於**:2026-09-09,筆電(hostname `14X`),上游 HEAD `63cd0fa`。
**friction 編號**:`F-142`。

## 現象

`tests/test_gate.py::TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce`
在**同一個 commit** 上,**桌機綠、筆電紅**。

紅的理由是 `.claude/portable/g1_guard.py` 「在上線 commit 樹裡卻不在豁免清單上,
也沒有出過紅燈可以豁免」。

## 證據(今日原始輸出)

### 一、兩種排序都紅 ⇒ 不是排序或污染

```
$ python -m pytest -q -p no:randomly tests/test_gate.py::TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce
F                                                                        [100%]
...
E       AssertionError: 〔原因字串在本機主控台為亂碼〕:['.claude/portable/g1_guard.py']
E       assert not ['.claude/portable/g1_guard.py']

tests\test_gate.py:870: AssertionError
FAILED tests/test_gate.py::TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce
1 failed in 0.40s
```

```
$ python -m pytest -q tests/test_gate.py::TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce
F                                                                        [100%]
...
E       assert not ['.claude/portable/g1_guard.py']
1 failed in 13.78s
```

環境:

```
$ git log --oneline -1 -- .claude/portable/g1_guard.py
2dc3419 票 92 落地:protected_entries() 改用 utf-8-sig —— BOM 不再吃掉第一條保護路徑

$ python -VV
Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
```

### 二、機制:證據檔不進版控

```
$ grep -n "^RUN_LOG\|RUN_LOG =" .claude/hooks/gate.py
61:RUN_LOG = os.path.join(ROOT, ".dev", "test-runs.jsonl")               # 證據

$ git check-ignore -v .dev/test-runs.jsonl
.gitignore:30:/.dev/*	.dev/test-runs.jsonl
```

### 三、本機該檔的內容:8 筆全 green,0 筆 red

```
$ grep -c "test_g1_guard.py" .dev/test-runs.jsonl
8

$ grep "test_g1_guard.py" .dev/test-runs.jsonl
{"test_file": "tests/test_g1_guard.py", "time": "2026-09-04T00:29:05.079605+00:00", "result": "green", "failed_tests": [], "impl_file": ".claude/portable/g1_guard.py", "impl_exists": true, "impl_hash": "33ca8e521932ab746fcc3403426a869b8220e855ab573daff72a0598d34701c8", "ticket_id": null}
{"test_file": "tests/test_g1_guard.py", "time": "2026-09-05T00:06:40.409272+00:00", "result": "green", ...}
{"test_file": "tests/test_g1_guard.py", "time": "2026-09-05T00:09:56.792459+00:00", "result": "green", ...}
{"test_file": "tests/test_g1_guard.py", "time": "2026-09-05T00:51:03.274473+00:00", "result": "green", ...}
{"test_file": "tests/test_g1_guard.py", "time": "2026-09-05T00:55:29.235119+00:00", "result": "green", ...}
{"test_file": "tests/test_g1_guard.py", "time": "2026-09-05T00:59:17.074295+00:00", "result": "green", ...}
{"test_file": "tests/test_g1_guard.py", "time": "2026-09-05T01:53:40.518791+00:00", "result": "green", ...}
{"test_file": "tests/test_g1_guard.py", "time": "2026-09-08T23:35:11.052305+00:00", "result": "green", ...}
```

(八筆的 `impl_hash` 皆為 `33ca8e52…`,`ticket_id` 皆 `null`。上面第二筆之後的
省略號是本票為了篇幅省的,欄位結構與第一筆相同。)

### 四、判定條文只認 red

`gate.py:1751-1756`:

```python
            if rec.get("result") != "red":
                continue
            if ticket is not None and rec.get("ticket_id") != ticket:
                saw_ticket_mismatch = True
                continue
            if rec["impl_exists"] is False:
                return None                 # 新檔案:紅燈時實作不存在
            if head is not None and rec.get("impl_hash") == head:
                return None                 # 既有檔案:紅燈對著改動前的碼發生
```

零筆 red ⇒ `redlight_missing()` 回訊息而非 `None` ⇒ `undrained` 非空 ⇒ 紅。
**這是構造,不是機率。**

### 五、桌機那一側

桌機在同一個 commit `74464ca` 上、**不帶 `--ignore` / `--deselect`**,
跑出 **1583 passed / 0 failed**。
(材料由裁決者從桌機回報檔 `2026-09-08T121546Z-restore-test-pass.md` 第 4-1 節讀出,
**本機未讀過該檔**。)

### 六、CI 把它蓋住了

`.github/workflows/tests.yml` 的「跑測試」步驟:

```yaml
          python -m pytest -q \
            --ignore=tests/test_known_items_regression.py \
            --deselect "tests/test_gate.py::TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce"
```

## 為什麼要緊

**任何全新 clone 都會紅** —— 紅燈證據住在一個 gitignored 的檔案裡,clone 不會帶走它,
所以新機器上那個檔是空的或不存在,而判定 fail-closed 於是全部判「沒證據」。

**而 CI 用 `--deselect` 把這一條蓋住了,所以沒有人看得見。**
這兩件事疊起來的形狀是:一個**在每一台新機器上都必然紅**的測試,
**被一個為了別的理由設的排除項擋在視線外**。
`--deselect` 的理由記在票 49(需要 `.dev/test-runs.jsonl` 的排水證據,
而證據格式是票 49 的題目)—— 理由本身成立,**但它順帶蓋掉了本票這件事**。

## 真正的題目

**紅燈證據該不該隨版控走?**

這不是「把 g1_guard 排掉」也不是「補一筆 red 進去」——
那兩個都是在資料側修一個機制側的問題。要決定的是:

- `.dev/test-runs.jsonl` 是**本機執行紀錄**(那它就該 per-machine,
  而依賴它的判定必須接受「新機器上沒有證據」是常態),
- 還是**專案的紅綠燈憑證**(那它就該進版控,而它會帶來別的問題:
  合併衝突、可偽造性、以及「誰的紅燈算數」)。

**兩條路都有代價,本票不預設答案。**

## 未證明

- **桌機那台是不是因為帳本裡有一筆 red 才綠。** **沒看過桌機的
  `.dev/test-runs.jsonl`。** 這是目前最合理的解釋,**不是量到的事實** ——
  依 `F-113`,一個候選解釋要問「它預測的東西這一次真的出現了嗎」,
  而這一格**在桌機那一側沒有被觀測**。
- **CI 那一側的行為。** CI 是全新 checkout,理應也沒有帳本,
  但它 `--deselect` 了這一條,所以**從來沒有機會顯示**。未查。
- **還有多少測試依賴這份 per-machine 證據。** 只看到這一條,沒有全面盤點。
