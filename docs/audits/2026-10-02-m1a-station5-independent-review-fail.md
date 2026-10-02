## 1. 總結論

**FAIL**

附件中的實作仍有證據不足時退紅，以及 D 狀態產生 green aggregate 的路徑。`1926 passed` 證明提供的測試通過，但不足以證明合約全部成立。

以下僅依附件判斷；另直接抽取附件中的判定函式，以小型輸入重現結果，未使用附件以外的專案程式碼。

## 2. 發現清單

### 1.【阻擋】缺少必要欄位的 session 仍能消除既有 red

**位置：** `.claude/hooks/redlight.py::load_runs`、`run_state`；`.claude/portable/status.py::_apply_run`

**程式碼原文：**

```python
if not isinstance(rec, dict) or not rec.get("run_id"):
    return []
out.append(rec)
```

```python
deselected = set(str(n) for n in (run.get("deselected") or []))
```

```python
if not any(n in deselected for n in idents):
```

```python
red[f] = set(n for n in red[f] if outcomes.get(n) != u"passed")
```

**具體情境：**

既有 `tests/test_x.py::test_x` 為 red，較晚收到以下 session：

```json
{
  "run_id": "r2",
  "time": "2",
  "ticket_id": "99",
  "exit_code": 0,
  "collected": ["tests/test_x.py::test_x"],
  "outcomes": {"tests/test_x.py::test_x": "passed"}
}
```

紀錄**沒有 `deselected`**，因此無法知道選取範圍是否完整。`load_runs()` 仍接受它，`_apply_run()` 將缺欄解讀成空集合，進入退紅分支。

直接執行附件函式可得到：

```python
{"state": "green", "unresolved": [], "orphaned": []}
```

同一問題也影響狀態分類：`run_state()` 把缺少 `collected` 當成零收集，可能將不完整證據宣稱為 C；它也沒有驗證 passed 身分是否屬於 selected。

**對應合約：** I5、I7、C 節、ODC-1 第 1 項及 coverage 未知不得退紅、AC-1、AC-4、AC-5。

---

### 2.【阻擋】有 collection error 的 D run，仍可能讓其他檔退紅成 green

**位置：** `.claude/hooks/redlight.py::run_state`；`.claude/portable/status.py::_apply_run`

**程式碼原文：**

```python
if ec not in (0, 1, 5) or any(str(n).endswith("::" + COLLECTION_ERROR) for n in collected):
    return "D"
```

```python
exit_ok = run.get("exit_code") in (0, 1)
```

```python
errored = any(n.endswith(u"::<collection error>") for n in idents)
```

```python
green_now[f] = exit_ok and u"passed" in results
```

**具體情境：**

既有 `tests/test_x.py::test_x` 為 red。較晚 session 的內容為：

```python
exit_code = 1
collected = [
    "tests/test_x.py::test_x",
    "tests/broken.py::<collection error>",
]
deselected = []
outcomes = {"tests/test_x.py::test_x": "passed"}
```

`run_state()` 明確回傳 **D**。但 `_apply_run()` 只檢查 exit code 及當前檔案的 collection error，因此把 `tests/test_x.py` 的 red 清除並列為 **green**。已用附件函式重現。

〈十三〉允許其他檔案的測試 failure 不影響本檔退紅；它沒有撤銷 C 節「D 狀態不能解決 red」及 I3 的限制。

**對應合約：** A 節 D、I3、I5、C 節禁止 D 退紅、AC-3、RL-4。

---

### 3.【阻擋】「沒有 deselected」不足以證明全檔選取，身分不明的歷史 red 可被局部結果清除

**位置：** `tests/conftest.py::pytest_collection_finish`、`pytest_sessionfinish`；`.claude/portable/status.py::_apply_run`

**程式碼原文：**

```python
_run["selected"] = [_nodeid(i) for i in getattr(session, "items", None) or []]
```

```python
collected=list(selected) + list(_run["deselected"]) + list(_run["collect_errors"]),
```

```python
if not any(n in deselected for n in idents):
```

```python
if any(n.endswith(u"::" + WHOLE_FILE) for n in red[f]):
    if all(outcomes.get(n) == u"passed" for n in idents):
        red[f] = set()
```

**具體情境：**

檔案實際有 X、Y，歷史 red 的 `failed_tests=[]`，依裁決應視為全檔測試均是先前紅。

若本次選取範圍只讓 X 進入 `session.items`，沒有提供 Y 的 deselection 通知，producer 寫出的事實就是：

```python
collected = [X]
deselected = []
outcomes = {X: "passed"}
```

consumer 無從區分「檔案只有 X」與「此次只收集 X」，卻將兩者都當作全檔選取，清除 `WHOLE_FILE` red。以此輸入執行附件函式，結果確實是 green。

這與發現 1 不同：此處所有欄位都齊全，缺少的是**足以證明全檔涵蓋的事實**。附件沒有提供選取限制或完整集合證據來排除此情境。

**對應合約：** I5、I7、ODC-1 第 1、2 項、〈十三〉裁決 3、AC-4、AC-5。

---

### 4.【應修】紅燈測試將 producer 與 aggregate 分開驗證，錯誤 consumer 仍可能全部通過

**位置：**

- `tests/test_redlight.py::TestRunFacts`
- `tests/test_status.py::TestTicket139::test_a_narrow_all_skip_record_does_not_retire_the_earlier_red`

**程式碼原文：**

RL-4(c)：

```python
assert len(runs) == 1, runs
assert redlight.run_state(runs[0]) == "D", runs[0]
```

RL-6 producer：

```python
assert redlight.run_state(run) == "F", run
assert len(run["deselected"]) == 645, len(run["deselected"])
assert [v for v in run["outcomes"].values()].count("skipped") == 3, run["outcomes"]
assert "passed" not in run["outcomes"].values(), run["outcomes"]
```

RL-6 consumer：

```python
_write_raw_lines(root, [LEDGER_940, LEDGER_970])
out = render(root)
```

**具體情境：**

RL-4 只檢查 `run_state()`，未驗證同一紀錄交給 status 後不得退紅或產生 green，因此未涵蓋發現 2。

RL-6 的 consumer 測試只有兩筆歷史八欄紀錄，沒有加入 producer 產生的 F session。假設錯誤 consumer 在遇到 F session 時清除 red：

- producer 測試仍可正確判出 F；
- 歷史紀錄測試因沒有 F session，仍保留 red；
- 兩者都通過，實際串接後卻違反 RL-6。

應補上「既有 red → 本次 session → status aggregate」的連續驗證，以及上述證據不完整情況。

**對應合約：** F 節 RL-4、RL-6、RL-6b；AC-7 的驗收充分性。此發現不否認附件所報告的修前失敗、修後通過結果。

## 3. 合約逐條對照表

「符合」限於附件可支持的範圍；測試通過不等於所有輸入都已驗證。

| 合約條目 | 判定 | 依據 |
|---|---|---|
| A：A 狀態 | 不符 | 未驗證 passed 是否屬於 selected，不完整證據仍可能判 A。 |
| A：B 狀態 | 符合 | 有效一般紀錄含 failed 時回傳 B；D 優先。 |
| A：C 狀態 | 不符 | 缺 `collected` 與明確空集合被混同。 |
| A：D 狀態 | 不符 | 分類可為 D，但 aggregate 仍可 green，見發現 2。 |
| A：E 狀態 | 符合 | 無 session 時不合成 run；D/E 不可分依 ODC-3 處置。 |
| A：F 狀態 | 符合 | 有 collected、無 passed/failed 時回傳 F，與 C 分開。 |
| A：skipped／deselected 不算實際通過 | 不符 | 正常 producer 可區別，但 reader 未驗證 outcome 與選取集合一致。 |
| A：A 不等於全套通過 | 不符 | 局部集合被用於全檔退紅，見發現 3。 |
| A：xfail／xpass 等排除項 | 符合 | 未將其分類正確性納入本次缺陷判定。 |
| A：儲存形式由實作決定 | 符合 | 另建 session 帳本符合允許範圍。 |
| I1 | 不符 | 缺少 deselection／完整集合證據仍取得全檔退紅資格。 |
| I2 | 符合 | 完整有效輸入下，C、全 skip、全 deselect 不成 A。 |
| I3 | 不符 | 發現 2。 |
| I4 | 不符 | 不完整選取證據可消除歷史 red，見發現 1、3。 |
| I5 | 不符 | green 的證據驗證不足，見發現 1–3。 |
| I6 | 符合 | 單獨舊 green 只形成 unknown，不被當作完整 run。 |
| I7 | 不符 | 能記選取及 outcome，但無法充分證明全檔涵蓋，且缺欄不拒絕。 |
| C-1：選到 X | 不符 | 缺乏一致性驗證；可能接受未證明選取範圍的紀錄。 |
| C-2：X 實際執行 | 不符 | 未驗證 passed 身分與 selected 一致。 |
| C-3：X 通過 | 符合 | 已知身分退紅要求 `outcomes[n] == "passed"`。 |
| C：未選／skip／C–F／舊 green 的禁止退紅條件 | 不符 | D run 可退紅；其餘典型路徑有防護。 |
| BC-1 | 符合 | 不替歷史紀錄宣稱原本不存在的 run facts。 |
| BC-2 | 符合 | 舊 green 顯示 run 事實未知。 |
| BC-3 | 符合 | 附件方案未遷移舊紀錄，保留原帳。 |
| BC-4 | 符合 | diff 未改寫歷史紀錄；§4.5 報告舊位元組不變。 |
| AC-1 | 不符 | 格式不完整紀錄可被錯誤分類；ODC-3 residual 已明列。 |
| AC-2 | 符合 | 有效 C/F 輸入不產生本次成功判定。 |
| AC-3 | 不符 | 發現 2。 |
| AC-4 | 不符 | 發現 1、3。 |
| AC-5 | 不符 | 部分 run 證據缺失仍取得成功／全檔退紅語意。 |
| AC-6 | 符合 | 原八欄帳本保留；符合附件所示 BC 行為。 |
| AC-7 | 符合 | 附件報告 14 支修前失敗、修後通過，含 RL-6；充分性另見發現 4。 |
| AC-8 | 符合 | 固定指令結果無失敗；所示既有 assertion 未修改。 |
| RL-1 | 符合 | 完整正常輸入可得到 A，並保留集合。 |
| RL-2 | 符合 | 可得到 B 並保留 failed 身分；同檔失敗阻止 green。 |
| RL-3 | 符合 | 空集合、exit 5 仍寫 session，分類 C。 |
| RL-4 | 不符 | D 的分類與 aggregate 判定不一致。 |
| RL-5 | 符合 | 無 run 不捏造 C/A，採裁決允許的不可判定表示。 |
| RL-6 | 符合 | 所示完整輸入的 F 分類、計數及保紅分支正確；串接測試不足。 |
| RL-6b | 符合 | X 明列於 deselected 的案例保留 red；涵蓋證據缺口見發現 3。 |
| RL-7 | 符合 | 舊 green 顯示 unknown，未改寫原紀錄。 |
| ODC-1 | 不符 | 未證明全檔選取即可能退紅；D run 也有退紅路徑。 |
| ODC-2 | 符合 | 所示已知身分消失時轉 orphaned，阻止 green。 |
| ODC-3 | 符合 | 無 producer／無 run evidence 的所示路徑顯示不可判定。 |
| 〈五〉既有 assertion 保護 | 符合 | 所示改動僅補 fixture；`_latest_per_file` 保留原語意。 |
| 〈十三〉1：依 root 載入 reader | 符合 | `load_redlight(root)` 呼叫該 root 的 `load_runs()`。 |
| 〈十三〉2：fixture 與 commit 條件 | 無法從材料判斷 | 補件內容可見，同一 implementation commit 的歷史未提供。 |
| 〈十三〉3：身分不明視同全檔紅 | 不符 | 有 `WHOLE_FILE` 表示，但局部集合可清除它。 |
| 〈十三〉4：file-scoped failure | 符合 | 一般其他檔測試 failure 不阻止本檔退紅；D 例外未處理。 |
| 〈十三〉5：producer enforcement residual | 符合 | 已明文登記。 |
| 〈十三〉6：獨立 transition commit drain | 無法從材料判斷 | 未提供 transition diff、commit 或驗證結果。 |

## 4. 未證明事項

- **未證明：** 完整專案可重現附件報告的全套結果。本次只重現附件判定函式，未執行完整 upstream suite。
- **未證明：** 真實 runner 在何種命令下產生發現 2、3 的輸入。已證明 consumer 對這些輸入的行為；附件未提供 runner 版本、選取限制或排除這些輸入的保證。
- **未證明：** 所有格式不符、讀取失敗及寫入失敗路徑都 fail-closed；目前缺欄反例已足以否定全面成立。
- **未證明：** session 樣本全部 1932 個身分與 outcome 的一致性，因附件只提供截斷樣本。
- **未證明：** 歷史帳本位元組保持及 commit 流程已被獨立驗證；附件提供的是結果陳述，未附完整原始比對或歷史。
- **未證明：** 附件引用但未附全文的〈八、Out of scope〉與紅燈規劃 A-1～A-7；未據此推論額外義務。
