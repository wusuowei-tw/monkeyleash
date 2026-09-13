# 票 139 —— 一次窄選擇的測試執行,會蓋掉全套的真實結果

**狀態**:candidate。只登記,本輪不查、不修。
**優先度**:未定 —— 見〈時鐘〉欄。
**發現於**:2026-09-13,票 133 ⑦ R4 收尾時比對儀表板與實際測試狀態。
**來源**:裁決者指出儀表板與事實不符。**本票只登記,不處理。**

---

## ⚠ 本票的證據邊界

**只記錄量到的東西,沒有做診斷、沒有提修法。**
沒寫的就是沒查:呈現層與寫入層各自的職責、是否還有別的檔受影響、
歷史上發生過幾次 —— 四件全部未查。

---

## 現象

**儀表板顯示 `red 0 / green 45`,而票 137 那條紅仍然存在。**

票 137 的那條紅:

```
tests/test_gate.py::TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce
```

它在 2026-09-13 的全套執行裡仍是紅的(`1 failed, 1823 passed, 3 skipped, 3 xfailed`)。

## 成因(裁決者給的,本輪附上佐證)

**最新一筆 `tests/test_gate.py` 的紀錄,來自一次「只選 symlink、結果全部 skip」的執行** ——
那次執行**沒有任何失敗**,於是被記成 `green`,**覆蓋了原本的失敗狀態**。

`.dev/test-runs.jsonl` 最後一筆 `tests/test_gate.py` 的紀錄 —— **完整一行,未截斷**
(`.dev/test-runs.jsonl:970`):

```
{"test_file": "tests/test_gate.py", "time": "2026-09-13T12:26:18.644697+00:00", "result": "green", "failed_tests": [], "impl_file": ".claude/hooks/gate.py", "impl_exists": true, "impl_hash": "446b2ef6f49fa0608d347d9969b49a0f3fa682d11cfe47b622feaa80cdbb7dc2", "ticket_id": "133"}
```

**⚠ 完整放進來,是因為本票的結論就靠「它裡面沒有什麼」** ——
截斷過的證據支撐不了一個「缺某個欄位」的命題。

**這一筆的全部欄位共 8 個**,逐一列出:

| 欄位 | 值 |
|---|---|
| `test_file` | `tests/test_gate.py` |
| `time` | `2026-09-13T12:26:18.644697+00:00` |
| `result` | `green` |
| `failed_tests` | `[]` |
| `impl_file` | `.claude/hooks/gate.py` |
| `impl_exists` | `true` |
| `impl_hash` | `446b2ef6f49fa0608d347d9969b49a0f3fa682d11cfe47b622feaa80cdbb7dc2` |
| `ticket_id` | `133` |

⇒ **沒有 `skipped`、沒有 `deselected`、沒有任何「這次選了哪些測試」的欄位。**

**那一筆 `12:26:18` 對應的執行是**:

```
$ python -X utf8 -m pytest tests/test_gate.py -k "symlink" -q --no-header
sss                                                                      [100%]
SKIPPED [1] tests\test_gate.py:451: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:459: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:473: 此環境無法建立 symlink
3 skipped, 645 deselected in 5.48s
```

⇒ **`3 skipped, 645 deselected`、零失敗 ⇒ 記成 `green`,`failed_tests: []`。**
同一天稍早的全套執行(`1 failed`)被這一筆蓋過。

## 命題

> **測試紀錄的呈現,會讓一次【窄選擇】的執行蓋掉全套的真實結果。**

**兩件要分開看**(本票不裁哪一件才是問題所在):

- 一次 `-k` 選擇的執行,與一次全套執行,**在紀錄裡長得一樣**
  —— 都是「某個測試檔 + green/red」。
- **645 deselected / 3 skipped 這兩個數字沒有進紀錄**,
  所以事後看不出那一筆的涵蓋範圍有多窄。

⚠ **不主張**「應該只記全套」或「應該拒絕記窄選擇」——那是修法,本票不提。

## 為什麼值得一張票

**它不會自己出聲。** 儀表板顯示 `red 0` 的那一刻,看起來與「真的都綠了」完全一樣;
而**最近一次本機全套仍失敗**。

⚠ **CI 的狀況不同,不得混為一談**:**現行 CI 排除此測試**
(`.github/workflows/` 兩處各有一行
`--deselect "tests/test_gate.py::TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce"`)。
⇒ **CI 綠不是因為它被修好了,是因為它沒被跑。**
**本票不處理那個 deselect**(它自己有票:`93-ci-deselect-needs-reevaluating-after-ticket-49`)。

> 與本專案反覆記過的同一族:**假綠與真綠在輸出上完全一樣。**
> 這一次的特別之處是 —— **假綠是由一次【正確而無害】的窄執行造成的**,
> 不是由錯誤造成的。我跑 `-k "symlink"` 是為了查證票 102 那兩件,那一步沒有做錯。

## 時鐘

**有觸發條件,沒有日期。**

> **下一次有人拿儀表板判斷「測試是不是都綠了」的時候。**

照 `docs/agents/issue-tracker.md` 的時鐘欄規矩,沒有日期 ⇒ 停在 `candidate`,
不排進任何順序。

---

## 相關

- **票 137** —— 被蓋掉的那條紅。**本票不處理它。**
- **票 133 ⑦** —— 發現時的上下文(收尾核對)。
