# 票 145 —— M1-a:一次 test run 的證據要如實表達它「跑了什麼、結果是什麼」

**狀態**:動工 —— Station 3b(含補件)紅燈已寫(待 Jeff 驗收);Station 4b 未開始。
**時鐘**:2026-10-02 —— 自此時點起,任何依 status aggregate 判斷「沒有未解紅燈」的行為,都暴露於已證明的 partial-selection false-green failure mode。此日期為 Jeff 於 2026-10-02 的排程裁決,不是由證據唯一推出;痛點最早的證據為票 139(2026-09-13)。
**立案**:2026-10-02(寫入當下的事實時間)。
**性質**:M1-a 的正式 implementation ticket。**票 139 保留為原始 finding / evidence source**,
本票承接其後的工作;票 139 的現象、證據與未查邊界**不改寫**。

> **舊票頭值(F-036,保留不刪)** —— 以下是 **superseded historical values,不是 current machine state**;
> 原行分別以 `**狀態**` 與 `**時鐘**` 欄名開頭,此處只保存其值:
>
> - 狀態(舊):~~`**candidate。** 票已正式建立(M1-a Station 2);缺 issue-tracker 要求的日期型時鐘 ⇒ 停在 candidate,不排進任何順序。`~~
> - 時鐘(舊):~~`未定 —— 待 Jeff 裁定日期;Station 3 開工前必須裁`~~
>
> 2026-10-02 由第 3、4 行取代。
>
> - 狀態(舊,第二代):~~`立案(時鐘已定 2026-10-02);未動工 —— Station 2 DONE、Station 3 NOT STARTED。`~~
>   —— 2026-10-02 Station 3 baseline 量測後由第 3 行取代(見〈十二〉)。
>
> - 狀態(舊,第三代):~~`動工 —— Station 3 進行中(baseline 已量,紅燈未寫);Station 4 未開始。`~~
>   —— 2026-10-02 紅燈寫完並取得證據後由第 3 行取代(見〈十四〉)。
>
> - 狀態(舊,第四代):~~`動工 —— Station 3 紅燈已寫(待 Jeff 驗收);Station 4 未開始。`~~
>   —— 2026-10-02 Jeff 驗收 Station 3、redlight.py 豁免 drain 後由第 3 行取代(見〈十五〉)。
>
> - 狀態(舊,第五代):~~`動工 —— Station 3 PASS(Jeff 驗收 2026-10-02);redlight.py 豁免已 drain;待 Jeff 切 implement;Station 4 未開始。`~~
>   —— 2026-10-02 Station 4 實作完成、固定全套 exit 0 後由第 3 行取代(見〈十六〉)。
>
> - 狀態(舊,第六代):~~`動工 —— Station 4 實作完成(固定全套 exit 0);待 Station 5 審查。`~~
>   —— 2026-10-02 Station 5 獨立審查 FAIL 後由第 3 行取代(見〈十七〉)。
>
> - 狀態(舊,第七代):~~`動工 —— Station 5 FAIL;回 Station 3b(補紅燈);Station 4b 未開始。`~~
>   —— 2026-10-02 Station 3b 紅燈寫完並取得證據後由第 3 行取代(見〈十八〉)。
>
> - 狀態(舊,第八代):~~`動工 —— Station 3b 紅燈已寫(待 Jeff 驗收);Station 4b 未開始。`~~
>   —— 2026-10-02 Station 3b 補件(B10、B11)開始時由第 3 行取代(見〈十七〉末段)。
>
> - 狀態(舊,第九代):~~`動工 —— Station 3b 補件(B10、B11)進行中;Station 4b 未開始。`~~
>   —— 2026-10-02 補件紅燈寫完並取得證據後由第 3 行取代(見〈十八之一〉)。
> 『立案』取自 repo 慣例（票 124 狀態行），docs/agents/issue-tracker.md 未定義有時鐘後的狀態用語；字面由 Jeff 於 2026-10-02 裁定。

---

## 一、來源

| 來源 | 性質 |
|---|---|
| **票 139**(`139-a-narrow-test-selection-overwrites-the-full-suite-result.md`) | 原始 finding / evidence source。**本票不改寫其證據。** |
| `M1-A-RUN-EVIDENCE-SPEC.md` | M1-a 最小規格(Station 1)。**該檔不進版控;本票已摘錄本工作所需 REQUIREMENT。** |
| `RECON-NONPYTHON-SIX-STATION-M1.md` | 偵察報告,狀態 CLOSED FOR IMPLEMENTATION PLANNING。**該檔不進版控;本票已摘錄本工作所需 REQUIREMENT。** |

**讀本票不需要上面兩份 repo 外文件** —— 要求、禁止事項與驗收條件全部摘錄在下方。

---

## 二、問題

### 2.1 現行證據紀錄的主體

`.dev/test-runs.jsonl` 每一筆的主體是 **(一個測試檔 × 一次結果)**,
8 個欄位:`test_file, time, result, failed_tests, impl_file, impl_exists, impl_hash, ticket_id`。
`result` 值域只有 `green` / `red`。

### 2.2 為何它無法完整表示「一次 test run」

**缺的不是 `result` 的第三個值,而是「run 這個實體」。** 帳本裡沒有任何一筆代表「一次執行」,
因此記不下:這次執行有沒有發生、涵蓋了什麼(選擇範圍、collected / skipped / deselected 數)、
退出碼、由哪個 runner 產生。三條獨立證據:

1. `status.py:608` 的格式字串自己寫著 `全套結果:%s(帳本不記全套)`,該 `%s` 永遠填 `UNRECORDED`。
2. 票 139 列出的那一筆紀錄 8 個欄位中,沒有 skipped、沒有 deselected、沒有任何選擇範圍欄位。
3. `tests/conftest.py:168` 的 `pytest_sessionfinish(session, exitstatus)` 收到 `exitstatus`,
   函式本體(`:169-172`)從未引用它。

### 2.3 collapse 發生的位置

| Collapse | 位置 | 混在一起的狀態 |
|---|---|---|
| ① | `tests/conftest.py:171-172`(`_outcomes` 為空時迴圈跑 0 次,不寫任何紀錄;`exitstatus` 丟棄) | 0 collected、全部 deselected、runner 錯誤未形成 outcomes、根本沒跑 —— 全部「帳本無變化」 |
| ② | `gate.py:2166` | 同上四者走同一條「沒有任何執行紀錄」訊息 |
| ③ | `status.py:595-602` | 同上四者都是 `red 0 / green 0`(或 `未記錄`) |
| ④ | `tests/conftest.py` 的 `setdefault`(無條件建鍵;本輪重核在 `:163`,見〈六〉)+ `:172`(`passed=not rec["failed"]`) | **「全部 skip、零失敗」與「全部通過」寫出逐字相同的 `result="green"`、`failed_tests=[]`** |

`passed=not rec["failed"]` 的真正語意是「這次沒有任何失敗」,不是「這次有測試通過」。

aggregate 層:`status.py` 的 `_latest_per_file`(`:312-334`)取**每檔最新一筆**。
一次窄選擇 run 寫出的新紀錄會成為該檔的「最新一筆」 —— 這是票 139 那次遮蔽的發生位置。

### 2.4 票 139 已證明的 false-green aggregate(逐字引用原案)

全套執行仍有 1 failed —— 票 139 逐字:

> 它在 2026-09-13 的全套執行裡仍是紅的(`1 failed, 1823 passed, 3 skipped, 3 xfailed`)。

同檔以 `-k "symlink"` 窄選 —— 票 139 逐字:

```
$ python -X utf8 -m pytest tests/test_gate.py -k "symlink" -q --no-header
sss                                                                      [100%]
SKIPPED [1] tests\test_gate.py:451: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:459: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:473: 此環境無法建立 symlink
3 skipped, 645 deselected in 5.48s
```

> ⇒ **`3 skipped, 645 deselected`、零失敗 ⇒ 記成 `green`,`failed_tests: []`。**
> 同一天稍早的全套執行(`1 failed`)被這一筆蓋過。

該筆紀錄 8 個欄位中無任何 skipped / deselected / 選擇範圍欄位 —— 票 139 逐字:

> ⇒ **沒有 `skipped`、沒有 `deselected`、沒有任何「這次選了哪些測試」的欄位。**

aggregate 的結果 —— 票 139 逐字:

> **儀表板顯示 `red 0 / green 45`,而票 137 那條紅仍然存在。**

### 2.5 ⚠ 未證明(票 139 的證據邊界,本票照抄,不擴張)

票 139 逐字:

> **只記錄量到的東西,沒有做診斷、沒有提修法。**
> 沒寫的就是沒查:呈現層與寫入層各自的職責、是否還有別的檔受影響、
> 歷史上發生過幾次 —— 四件全部未查。

| 項目 | 狀態 |
|---|---|
| 呈現層的職責 | **未證明** |
| 寫入層的職責 | **未證明** |
| 是否還有其他測試檔受同樣影響 | **未證明** |
| 歷史上發生過幾次 | **未證明** |

**本票成立不改變上表任何一格。**

### 2.6 本票的成立理由

**upstream 現存 run-evidence correctness gap。** 直接觀測的實例是票 139 那一次,
語料為本 repo 自己的 `tests/test_gate.py`(純 Python);Collapse ④ 位於 pytest 專屬的 producer,
與副檔名無關。共用此版本 evidence / status 機制的 repo 均暴露於此 failure mode ——
**但不得寫成其他 repo 都已實際發生假綠**(未查證)。

**範圍**:只處理本 repo 的 evidence 是否如實表達一次 test run。不擴大成一般測試平台問題。

---

## 三、REQUIREMENT

### A. Machine states

| 狀態 | 定義 | 成功語意 |
|---|---|---|
| **A** | runner 已執行;至少一項適用測試**實際通過**;無失敗 | 是(僅就**該次涵蓋範圍**而言) |
| **B** | runner 已執行;至少一項失敗 | 否 |
| **C** | runner 已執行;**0 項**適用測試被收集 | 否 |
| **F** | runner 已執行;**有**收集到測試,但沒有任何一項實際通過或失敗(全部 skipped、全部 deselected、或兩者混合) | 否 |
| **D** | runner invocation 錯誤 / collection failure / **執行被中斷** | 否 |
| **E** | 本次根本沒有執行 runner | 否(且不是「一次 run」) |

- **「實際通過」**指該測試的本體有被執行且結果為通過;skipped 與 deselected **都不算**。
- **F 不得與 A 同義。** 票 139 原案(`3 skipped, 645 deselected`、0 passed、0 failed)屬 F。
- **F 與 C 分開,不合併。** 理由:I7 要求涵蓋範圍可觀察,F 與 C 的涵蓋範圍本來就是不同事實;
  票 139 把「645 deselected / 3 skipped 沒有進紀錄」列為兩件事之一;
  現行實作把兩者落在不同的 collapse(全 skip → ④ 寫成 green;0 collected / 全 deselect → ① 不寫)。
- **A 不等於「完整測試通過」。** 一次 `-k` 窄選、全部實際通過的 run 是 A,但不是全套通過;
  「是否涵蓋全套」是 I7 的涵蓋範圍事實,不是 A–F 的一個值。
- **本票不要求**:xfail / xpass 的歸類(偵察未量測現行 producer 如何記錄它們;
  在後續裁定前不宣稱它們屬於 A–F 任一);D 內部再細分;A 內部再細分;
  runner unsupported / unavailable 單獨成態(歸入 E)。
- **不預先指定**:新增 `result` 第三值、新增某個 JSON 欄位、另開檔案。
  **本票定義 semantics,implementation 決定 storage representation。**
  (偵察已記:必須新增一個現在不存在的 run-level 事實;既有 8 欄不必改;落點不裁。)

### B. Invariants

- **I1.** 「沒有 failure record」不得自動等價於「本次完整測試通過」。
- **I2.** 0 applicable tests(C)、全部 skipped、全部 deselected(F)不得與 full pass 具有相同 machine meaning。
- **I3.** runner error / collection failure / **中斷**(D)不得被表示為 green。
- **I4.** 一次 partial-selection run 不得使較早仍未被**有效解決**的 red 僅因 aggregate overwrite 而消失。
- **I5.** status aggregate 的 green / red 必須可追溯到足以證明其語意的 evidence。
- **I6.** 舊的 per-test green / red evidence 若仍保留,不得被新的 run-level semantics 錯誤解讀為完整 run 結果。
- **I7.** 一次 run 的涵蓋範圍 —— 選了哪些、跳過幾條、未選幾條 —— 必須是 machine 事後可觀察的事實。只定此語意,不指定欄位或格式。

### C. I4 前提 —— 「一條 red 何時算被有效解決」

測試 X 的一條 red,**只有在**較晚的某一次 run **同時**滿足下列三項時,才算被有效解決:

1. 該 run **選到了 X**(X 在該次的選擇範圍內);
2. X 在該 run 中**被實際執行**(不是 skipped、不是 deselected);
3. X 在該 run 中的結果為**通過**。

下列情形**都不能**解決 X 的 red:

- 一次**沒有選到 X** 的 run(無論它選到的其他測試結果如何,含全部實際通過);
- 一次選到 X 但 **X 被 skip** 的 run;
- 一次處於 **C / D / E / F** 狀態的 run;
- 該測試檔「最新一筆」紀錄為 green 這件事本身,當那一筆**不帶**上列 1–3 的證據時。

「X 的身分」以什麼為鍵不在本票裁定(見〈七〉Q7)。X 被刪除或改名後的退場:見 ODC-2。

### D. Backward compatibility

帳本已有歷史紀錄(偵察量測時 1997 筆,全部 8 欄、全部 `.py` 測試檔;以該次量測為底)。

1. **歷史紀錄不得被重新宣稱含有當時沒有記錄的 run-level facts。**
2. 舊紀錄缺少新 run-level fact 時,machine **不得憑空推論** full pass、zero tests、runner error、full-suite execution —— 四者任一皆不得。缺少即為「未知」,並且**可被看出是未知**。
3. **Migration**:只定 acceptance expectation —— 遷移後(若有遷移),1、2 仍須成立,且 AC-6 成立。要不要遷移、怎麼遷移,不在本票的 REQUIREMENT 內。
4. **不得竄改歷史 evidence** 來讓新模型看起來完整(含:不得改寫舊紀錄的 8 欄、不得為舊紀錄補寫推測出來的涵蓋範圍)。

### E. Acceptance criteria —— 下列全部成立才能 PASS

| AC | 條件 |
|---|---|
| **AC-1** | A / B / C / D / E / F 各 run state 在 machine semantics 上可區分;**F 與 C 分開**。ODC-3 所列殘餘情形須有明列的處置 |
| **AC-2** | zero tests / 全部 skipped / 全部 deselected **不能**產生與 full pass 相同的成功語意 |
| **AC-3** | runner error / collection error / 中斷 **不能**產生 green |
| **AC-4** | partial selection 不得以缺乏完整 run 證據的方式遮蔽仍有效的 earlier red —— **依 C 節的解決條件判斷** |
| **AC-5** | status consumer 不得把「缺 run-level evidence」默認成 successful full run |
| **AC-6** | 現有 per-test evidence 的歷史 provenance 保留(含 D 節 1–4) |
| **AC-7** | 至少有對應的 red-light tests 能在修正前失敗、修正後通過;**RL-6 必須是 red-light cases 之一** |
| **AC-8** | 現有 upstream regression suite 不得因 M1-a 被無關破壞(與 M1-a 相關的語意改動見 ODC-1 與〈五〉) |

### F. Red-light cases(本票只定案例,不建立 test)

「successful run」指具有 A 的成功語意;「green aggregate」指 status aggregate 把該檔 / 該測試計為綠。

| 案例 | precondition | action | expected machine-observable result | forbidden result |
|---|---|---|---|---|
| **RL-1** Full pass | 有適用測試 | 執行 runner,至少一項實際通過、無失敗 | state 明確為 A(successful run);涵蓋範圍可觀察(I7) | 被記成 C / D / E / F;涵蓋範圍不可觀察 |
| **RL-2** One failure | 有適用測試,至少一項會失敗 | 執行 runner | state 為 B;失敗的測試可被識別 | green aggregate;與 A 同義 |
| **RL-3** Zero tests collected | 選擇條件使 0 項適用測試被收集 | 執行 runner | state 為 C,且**可觀察到**這次 run 發生過 | 與 A 同義;與 E 同義(「帳本無變化」);green aggregate |
| **RL-4** Collection / runner error / 中斷 | 三子案各一:(a) 收集失敗、(b) runner invocation 錯誤、(c) 執行被中斷 | 執行 runner | state 為 D;不產生 green(子案 (b) 中 producer 自己未載入者見 ODC-3,至少須不為 green) | green;與 A 同義 |
| **RL-5** No invocation | 本次未執行 runner | 無(只檢查 machine state) | E;與 C、A 可區分 | 與 RL-3(C)混同;與 RL-1(A)混同;被推論出任何 run 事實 |
| **RL-6** 票 139 原案重現 | 同一測試檔的全套 run 有 **1 failed**(該失敗測試記為 X) | 同檔以 `-k` 窄選,得 **N skipped、M deselected、0 passed、0 failed**(N ≥ 1,M ≥ 1) | 該窄選 run 的 state 為 **F**;N 與 M 事後可觀察(I7);X 的 red 在 aggregate 中**仍存在** | 記成與 RL-1 同義的 green;前置那條 red 在 aggregate 中消失;N / M 事後不可觀察 |
| **RL-6b** Partial selection 全綠但未涵蓋 earlier red | 某條測試 X 為 red(未依 C 節解決) | 同檔窄選,選到的測試全部實際通過,但**未選到 X** | 該 run 的 state 為 A(僅就其涵蓋範圍);X 的 red **仍存在**;「未選到 X」事後可觀察 | 無證據地消除 X 的 red;該 run 被解讀為全套通過 |
| **RL-7** Historical evidence | 帳本中有舊格式紀錄(僅 8 欄,缺 run-level fact),其中至少一筆 `result="green"` | status consumer 讀取該帳本 | 該紀錄的 run-level 事實為「未知」且可被看出是未知;舊紀錄內容原樣保留 | 被 retroactively 解讀成 full pass、zero tests、runner error 或 full-suite execution;舊紀錄被改寫或補寫 |

案例總數:8(RL-1 ~ RL-7,加 RL-6b)。

---

## 四、OPEN DESIGN CONSTRAINT

> **Station 3 實際開始前,ODC 必須有可執行裁決;不得讓 Implementation 自己偷偷選答案。**

**ODC-1|I4 與現行 latest-per-file / red→green 假設的衝突**

- 證據:`status.py` `_latest_per_file`(`:312-334`)以**每檔最新一筆**決定該檔紅綠;
  `tests/test_status.py` 有斷言「紅轉綠算綠」(逐條見〈五〉)。
- 張力:I4 的解決條件是**測試層級**(X 是否被選到、被執行、通過);
  現行 aggregate 的選擇規則是**檔案層級的最新一筆**,且帳本沒有涵蓋範圍可供判斷。
  在現行架構下,I4 無法只靠改 consumer 達成。
- I4 **不刪**。調和方法未裁。

→ 已裁,見〈十一〉

**ODC-2|測試被刪除 / 改名後,舊 red 如何退休**

- 張力:C 節要求 X 在後續 run 中被實際執行且通過;X 若已不存在,這個條件永遠無法滿足。
- 偵察未涵蓋此情形。下限:**無論採何種退場方式,X 的 red 不得因 X 不再出現就靜默消失;
  退場本身必須是 machine 可觀察的事實。**

→ 已裁,見〈十一〉

**ODC-3|producer 本身未載入時,D 與 E 的可觀察性**

- 證據:偵察記錄「若 rootdir 不對,conftest 可能**連載入都沒有**」⇒ 帳本無變化。
- 張力:若 run-level 事實由 runner 內部(如 `conftest.py`)產生,
  讓 producer 自己沒被載入的 D 情形,在 machine 上與 E **必然相同**。
- D / E 的區分**不刪**。下限:**這類情形不得被表示為 green**(I3),也不得被推論為 C。

→ 已裁,見〈十一〉

---

## 五、既有安全網保護條款

現有 test_status.py 中與 red→green 語意相關的既有 assertion,不得由 Implementation 自行刪除、弱化或改寫預期來使新實作通過。若確實需要改變其語意,必須先列出 exact assertion、原語意、新語意、與 M1-a Spec 的衝突點,交由裁決者明確批准後才能修改。

### 5.1 現有符合「red → green」語意的 assertion(立案時 HEAD `8ff4c6e`,唯讀查得,未執行測試)

| nodeid | 檔案 | 行號 | assertion 原文 | 現行語意 |
|---|---|---|---|---|
| `tests/test_status.py::TestTestsUnderTicketUsesTheLatestRecordPerFile::test_a_file_that_went_red_then_green_counts_as_green` | `tests/test_status.py` | 570 | `assert u"tests/test_a.py" not in red, red` | 同一檔先 red 後 green ⇒ 最新一筆為 green 時,該檔**不在**紅名單 |
| 同上 | `tests/test_status.py` | 571 | `assert u"tests/test_a.py" in green, green` | 同一檔先 red 後 green ⇒ 該檔被計入綠名單 |
| `tests/test_status.py::TestLatestPerFileIsFailClosedWithoutTicket::test_with_ticket_still_filters` | `tests/test_status.py` | 749 | `assert got["tests/test_a.py"]["result"] == "green", got["tests/test_a.py"]` | 以 `TICKET_100_RUNS`(test_a 紅轉綠)為資料,`_latest_per_file` 回傳 test_a 的最新一筆為 green |

**共 3 條 assertion,分屬 2 個 nodeid。**

查詢方式與原始輸出:

```
$ grep -n -E "紅轉綠|red.{0,6}green|_latest_per_file|最新一筆|latest" tests/test_status.py
262:#          每檔最新一筆)+ `--all` + Sync Health
519:    def test_latest_existing_month_names_the_file_and_the_last_record(self, tmp_path):
524:    def test_latest_existing_month_changes_when_the_file_goes_away(self, tmp_path):
546:    def test_a_file_that_went_red_then_green_counts_as_green(self, tmp_path):
548:        「這張票底下還有什麼是紅的」問的是**每個檔的最新一筆**,不是有沒有紅過。
688:# 甲-2 用的固定資料:兩張票、三個檔,其中 test_a 紅轉綠。
713:    `_latest_per_file` 的過濾寫成 `if ticket and ...`,票號 falsy 時整個
728:        # 「未記錄;本票 red 0 / green 0」的實作會過關 —— 而那仍然是個謊。
741:        assert status._latest_per_file(TICKET_100_RUNS, None) == {}
748:        got = status._latest_per_file(TICKET_100_RUNS, u"99")
993:    def test_the_line_names_the_latest_file(self, tmp_path):
1003:        """與 `latest_report` 同一條(裁五「三種空同 ④」)。
```

⚠ 本查詢**不直接命中** 570 / 571 / 749 三行(斷言本體不含查詢字串);
三條是由命中的 546 與 748 **讀檔往下**找到的。

逐一讀檔後的排除理由:519 / 524 / 993 / 1003 為不同物件(intercepts 月檔、`latest_report`);
262 / 548 / 688 / 713 / 728 為註解或 docstring;741 / 748 不含紅轉綠語意
(741 斷言無票回空 dict;748 斷言篩出的檔名集合);
572(`assert u"tests/test_b.py" in red, red`)屬同一測試但不是紅轉綠斷言。

---

## 六、行號重核(以立案時 HEAD `8ff4c6e` 為底)

上方引用的原始碼行號源自偵察報告;本票立案時逐一重核如下。

| Spec 所寫行號 | 當下 HEAD 行號 | 是否相符 | 當下原文 |
|---|---|---|---|
| `tests/conftest.py:158`(`setdefault` 無條件) | `:163` | **STALE LINE REFERENCE** | `    rec = _outcomes.setdefault(f, {"failed": []})`(`:158` 當下為 `        return`) |
| `tests/conftest.py:168` | `:168` | 相符 | `def pytest_sessionfinish(session, exitstatus):` |
| `tests/conftest.py:169-172` | `:169-172` | 相符 | `    if _redlight is None:` / `        return` / `    for f, rec in _outcomes.items():` / `        _redlight.record_run(f, passed=not rec["failed"], failed_tests=rec["failed"])` |
| `tests/conftest.py:171-172` | `:171-172` | 相符 | `    for f, rec in _outcomes.items():` / `        _redlight.record_run(f, passed=not rec["failed"], failed_tests=rec["failed"])` |
| `tests/conftest.py:172` | `:172` | 相符 | `        _redlight.record_run(f, passed=not rec["failed"], failed_tests=rec["failed"])` |
| `.claude/portable/status.py:312-334` | `:312-334` | 相符 | `:312` `def _latest_per_file(runs, ticket):` …… `:334` `    return out` |
| `.claude/portable/status.py:595-602` | `:595-602` | 相符 | `:595` `    if runs is None:` …… `:601` `        red = len([r for r in latest.values() if r.get("result") == "red"])` / `:602` `        green = len([r for r in latest.values() if r.get("result") == "green"])` |
| `.claude/portable/status.py:608` | `:608` | 相符 | `        val = u"本票(每檔最新一筆)red %d / green %d;%s;全套結果:%s(帳本不記全套)" % (` |
| `.claude/hooks/gate.py:2166` | `:2166` | 相符 | `    return ("%s 沒有任何執行紀錄 —— 無法證明它曾經紅過。" % want)` |

**相符 8 處,STALE 1 處。** 只記錄,不改 Spec、不改原始碼。

---

## 七、Open design questions

全部是 DESIGN OPTION 層的問題;任何答案都必須滿足〈三〉的 REQUIREMENT。**沒有任何一個候選答案是 requirement。**

| # | 問題 | 狀態 |
|---|---|---|
| Q1 | run-level fact 放同一帳本,或獨立帳本? | 未裁 |
| Q2 | 是否新增 record type? | 未裁 |
| Q3 | per-test 與 per-run 如何關聯? | 未裁 |
| Q4 | aggregate 如何選 current authoritative run?(與 ODC-1 相關) | 未裁 |
| Q5 | historical records 如何呈現「未知」? | 未裁 |
| Q6 | Station 2 是升級票 139,或另開新票? | **已裁:NEW TICKET(本票 145)** |
| Q7 | I4 所稱「測試 X 的身分」以什麼為鍵? | 未裁 |

---

## 八、Out of scope

本票**不處理**:

- 票 137 那條紅本身(`TestLegacyNoRedlightList`)及票 137 的其他問題
- 票 93 的 CI `--deselect` 及票 93 的其他問題
- `.kt` / `.dart` 的 R3 / R8 fail-open(non-Python R3/R8)
- non-Python adapter
- Kotlin / Gradle
- Flutter / Dart
- Android
- `tests/test_<base>.py` mapping
- `impl_file` consumer
- `install.py` / G-08
- hook / project-root
- legacy-no-redlight
- nested `app/build` exclusion(nested build exclusion)
- CI 擴充(CI expansion)
- product-security
- Supply-chain Gate
- App implementation
- xfail / xpass 的狀態歸類

上述屬 M1-b、既有票或後續 milestone。**不得以「順手可以修」納入。**
**M1-b 另立 Spec / Ticket,不得與本票共票。**

---

## 九、測試三層

本票未來會動到 run evidence producer 與 status consumer / aggregation semantics。

| 層 | 狀態 |
|---|---|
| **UNIT** | 未證明 |
| **CLEAN** | 未證明 |
| **REAL** | 未證明 |

> Full baseline 尚未量測。
> 依 Station 2 裁決,baseline 排至 Station 3 開始前,
> 避免在純 ticket 階段寫入新的 test-run evidence。

---

## 十、六站狀態

| 站 | 狀態 |
|---|---|
| Station 1 — Spec | PASS / CLOSED |
| Station 2 — Ticket | DONE |
| Station 3 — Red-light | PASS / ACCEPTED |
| Station 4 — Implementation | 實作嘗試完成,Station 5 FAIL |
| Station 5 — Review | FAIL |
| Station 3b — Red-light(補) | 紅燈已寫,待驗收 |
| Station 6 — Acceptance | NOT STARTED |

Transition：redlight.py 豁免已 drain

Station 3b 補件：紅燈已寫，待驗收

Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 5 FAIL,回 Station 3b 補紅燈,Station 4b 未開始(與票頭第 3 行一致)。
(舊的 candidate 語意由票頭的 F-036 區塊保存;本節不是第二份 current status。)

> **舊句(F-036,保留不刪)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 3 進行中,Station 4 未開始(與票頭第 3 行一致)。~~
> 第 3 行之後數次更新(紅燈驗收、Station 4 完成)時本句未同步而與第 3 行矛盾;2026-10-02 Station 3b 落票時修正。

> **舊句(F-036,保留不刪)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 立案、時鐘已定(2026-10-02)、未動工 —— 與票頭第 3 行一致,不代表 Station 3 已開工。~~
> 2026-10-02 baseline 入票時第 3 行已改為「動工」,本句未同步而與第 3 行矛盾;2026-10-02 修正。

**已裁**:時鐘 2026-10-02。

---

## 十一、Station 3 前置裁決（2026-10-02，Jeff）

ODC-1（2B 修正版）
一個 run 只有在同時滿足下列三項時，才有資格使某 test file 內既有的 red 變為 green：
1. 該 file 的測試集合全部被選到（沒有任何 deselected）；
2. 先前為 red 的那些 test identity，在本次 run 中確實被執行且通過；
3. 本次 run 沒有任何 failure。
與既有 red 無關的其他測試在本次 run 中被 skip，不影響退紅資格。
partial selection、deselection、zero tests、coverage 未知的 run，一律沒有退紅權。
本規則比 I4 對單一測試 X 的最低條件更嚴格，不違反 I4。
既有 3 條 test_status.py assertion（570 / 571 / 749）原文不改；fixture 只准補新的 run-level facts，且所補內容須在本票列出。若發現任一 assertion 語意必須改變，回裁決者單獨裁，Implementation 不得自行改。
→ 第 2、3 項已於 2026-10-02 修訂，見〈十三〉

ODC-2（3A 收緊）
test 被刪除或改名後，舊 red 不得自動變 green；沒有證據證明 identity 延續時，保留為 orphaned / absent 類可觀察狀態。改名不得自動視為原 test 的延續。M1-a 不提供人工 retirement workflow，因此此狀態可能持續存在 —— 這是已接受的 residual，不得偷偷歸綠。

ODC-3（4A）
producer 未載入時，記為「無證據 / 不可判定」；不得表示為 green，也不得推論為 C。D / E 在此路徑不可區分，作為 ODC-3 明示 residual 接受。依據：Spec ODC-3 原文「是否接受此殘餘、或改由 runner 外部產生事實，不在本 Spec 裁定」與 AC-1「ODC-3 所列殘餘情形須在 Station 2 票面明列其處置」。

Baseline 流程
裁決落票 → 唯讀查 pipeline 應填內容 → Jeff 手動改 pipeline.json → 確認 machine reader 讀到票 145 與正確 stage → 以固定指令量 baseline → 之後 Red-light 與修後 Acceptance 必須使用同一指令口徑，除非票面明文裁定變更。

---

## 十二、Station 3 baseline(固定指令)

**固定指令(逐字,從 repo 根目錄)**:

```
python -X utf8 -m pytest -q
```

Red-light 與修後 Acceptance 必須使用同一指令，除非票面明文裁定變更。

### 12.1 結果

| 項 | 值 |
|---|---|
| exit code | **0** |
| 摘要行原文 | `1912 passed, 3 skipped, 3 xfailed in 146.72s (0:02:26)` |
| 耗時 | 146.72s(pytest 自報);指令於 2026-10-02T13:25:31Z 之後啟動 |
| Python | `Python 3.11.9` |
| pytest | `pytest 9.1.1` |
| 執行機器 | `<執行機器>` |
| HEAD | `4be8eeb01ce2a695d1170576432adc7b5f6dd3b2` |
| pipeline.json | `current_stage: tickets`、`feature: framework-updates`、`ticket_id: "145"` |
| 判定分支 | exit code == 0 ⇒ baseline 全過 |

### 12.2 `.dev/test-runs.jsonl`

| 時點 | SHA-256 | bytes | lines |
|---|---|---|---|
| before | `d6c0da4d173388dc7d58ba30023c67620309059cd2bd1bc854faa45dc766f4ae` | 540862 | 1997 |
| after | `460f714f02c527081d8242520021f611ad0a62c52e3ae592977ae7fc7be7684c` | 552165 | 2043 |

新增 **46** 行(第 1998–2043 行),逐筆:

| 計數 | 筆數 |
|---|---|
| `ticket_id == "145"` | 46 |
| `ticket_id != "145"` | 0 |
| `result == "red"` | 0 |
| `result == "green"` | 46 |
| 其他 / 缺欄 | 0 |

⚠ 46 是**測試檔數**,不是測試數(每檔一筆;本次 1912 passed / 3 skipped / 3 xfailed 不進帳本)。
`status.py` 同一時點的 Evidence 行原文:`全套結果:未記錄(帳本不記全套)` —— 本票〈二〉所述缺口,本次 baseline 亦適用。

### 12.3 兩個 operational 檔的追蹤狀態

| 檔 | `git ls-files` | `git check-ignore -v` | 判定 |
|---|---|---|---|
| `.dev/pipeline.json` | (無輸出) | `.gitignore:30:/.dev/*` | 未追蹤、被 ignore |
| `.dev/test-runs.jsonl` | (無輸出) | `.gitignore:30:/.dev/*` | 未追蹤、被 ignore |

⇒ baseline 新增的 46 筆紀錄**只存在本機帳本**;進版控的是本節的指紋與計數。

### 12.4 與 CI 指令的差異(只列,不評價、不修改)

CI(`.github/workflows/tests.yml:73-75`,步驟「跑測試」):

```
python -m pytest -q \
  --ignore=tests/test_known_items_regression.py
```

| 項 | 本次 baseline | CI |
|---|---|---|
| 直譯器旗標 | `-X utf8` | 無 |
| 排除項 | 無 | `--ignore=tests/test_known_items_regression.py` |
| `--deselect` | 無 | 無 |
| 環境變數 | 未設定額外變數 | workflow 無 `env:` 區塊 |
| 作業系統 | Windows(`<執行機器>`) | `ubuntu-latest`(`tests.yml:20`) |
| Python | 3.11.9 | `python-version: '3.11'`(`tests.yml:47`) |
| 前置步驟 | 無 | `python -m pip install -e ".[dev]"`(`:50`)、`sh bootstrap.sh`(`:57`) |
| 收集清單步驟 | 無 | `python -m pytest --collect-only -q --ignore=tests/test_known_items_regression.py`(`:96-98`) |

本次 baseline 有收集並執行 `tests/test_known_items_regression.py`(帳本第 2019 行,green)。

---

## 十三、Station 3 紅燈規劃裁決（2026-10-02，Jeff）

觀察契約採 docs/audits/2026-10-02-m1a-station3-redlight-plan.md 一、A（A-1 ~ A-7），並經以下裁決修正：
1. status 讀取 run 事實：(i) status 依 root 載入 redlight.py 的讀取函式；status 不另寫解析。
2. 570 / 571 / 749 的 fixture：C —— 原 assertion 不動；舊 fixture 所需的 run-level facts，於 Station 4 在同一個 implementation commit 補上。若屆時無法只靠補 facts 恢復而須改 assertion 語意：立即停，回裁決者。Station 3 允許補新紅燈測試所需的 fixture / fake repo 基礎設施（含讓 fake repo 有 redlight.py），條件是既有測試結果不變。
3. 身分不明的舊紅（failed_tests 缺欄、為空、或為 ["<collection error>"]）：視同該檔全部 applicable tests 都是先前紅的。
4. ODC-1 第 3 條修訂為 file-scoped（見下）。
5. tests/conftest.py 不受 R2 / R3 管轄之缺口：(b) M1-a 結案後另開框架票；本票先登記為 residual。
6. redlight.py 的 R3 豁免：乙 —— 但 drain 獨立成「Red-light 經 Jeff 驗收後、Station 4 前」的 transition commit，不與紅燈 commit 混合；transition 以既有 gate 測試或唯讀方式驗證豁免已消失，不得為了測門禁而修改 redlight.py。

ODC-1（修訂後全文，取代〈十一〉同條的第 2、3 項）
一個 run 只有在同時滿足下列三項時，才有資格使某 test file 內既有的 red 變為 green：
1. 該 file 的測試集合全部被選到（沒有任何 deselected）；
2. 已知先前為 red 的 test identity，本次確實執行並通過；若歷史 red 無法知道是哪一條 test，則該 file 內所有 applicable tests 都必須實際執行並通過；
3. 該 file 本次沒有任何 failure。
其他 file 的 failure 不影響本 file 的退紅資格；與既有 red 無關的 skip 亦不影響。

Enforcement residual（登記）
- tests/conftest.py 是 M1-a 的 evidence producer，但被 NON_SOURCE_DIRS 排除，R2 / R3 無法結構性阻止它在錯誤 station 被修改；目前只靠 tracked allowlist + final staged diff 守住。M1-a 結案後另開框架票。
- .claude/hooks/redlight.py 列在 .agents/legacy-no-redlight.txt，R3 對它整條豁免；依裁決 6 於 transition commit drain。

---

## 十四、Station 3 紅燈證據

### 14.1 執行

| 項 | 值 |
|---|---|
| 紅燈 commit(刀②) | `5188f49de0f2e258ae490cab935fd9b666e8345b` |
| 固定指令 | `python -X utf8 -m pytest -q`(〈十二〉) |
| exit code | **1** |
| 摘要行原文 | `14 failed, 1912 passed, 3 skipped, 3 xfailed in 127.31s (0:02:07)` |
| 既有測試 | 1912 passed —— 與 baseline(`1912 passed, 3 skipped, 3 xfailed`)相同;**既有測試 0 失敗** |

### 14.2 三層集合對照(規劃 case = 新增 nodeid = 實際紅燈 nodeid)

消失集合(修改前收集有、修改後沒有)= **空**。新增集合 = 實際失敗集合 = 下表 14 支,**不多不少**。

| 規劃 case | nodeid | 分類 | 實際失敗原因 |
|---|---|---|---|
| RL-1 | `tests/test_redlight.py::TestRunFacts::test_a_full_pass_is_state_a_with_coverage_visible` | 介面紅 | `AttributeError: … has no attribute 'load_runs'` |
| RL-2 | `tests/test_redlight.py::TestRunFacts::test_one_failure_is_state_b_and_names_the_test` | 介面紅 | `AttributeError: … 'load_runs'` |
| RL-3 | `tests/test_redlight.py::TestRunFacts::test_zero_collected_is_state_c_and_the_run_is_visible` | 介面紅 | `AttributeError: … 'load_runs'` |
| RL-4(a) | `tests/test_redlight.py::TestRunFacts::test_a_collection_error_is_state_d` | 介面紅 | `AttributeError: … 'load_runs'` |
| RL-4(b) | `tests/test_redlight.py::TestRunFacts::test_a_usage_error_is_state_d_not_green` | 介面紅 | `AttributeError: … 'load_runs'` |
| RL-4(c) | `tests/test_redlight.py::TestRunFacts::test_an_interrupted_run_is_state_d_even_with_passes` | 介面紅 | `AttributeError: … 'load_runs'` |
| RL-6' | `tests/test_redlight.py::TestRunFacts::test_three_skipped_645_deselected_is_state_f_with_counts` | 介面紅 | `AttributeError: … 'load_runs'` |
| **RL-6** | `tests/test_status.py::TestTicket139::test_a_narrow_all_skip_record_does_not_retire_the_earlier_red` | **行為紅** | `AssertionError`:`red=(無)`、`green=tests/test_gate.py` |
| **RL-6b(舊寫入版)** | `tests/test_status.py::TestNarrowSelection::test_a_later_green_without_run_facts_does_not_retire_x` | **行為紅** | `AssertionError`:`red=(無)`、`green=tests/test_x.py` |
| RL-6b(run 事實版) | `tests/test_status.py::TestNarrowSelection::test_a_narrow_run_that_did_not_select_x_does_not_retire_x` | 介面紅 | `AttributeError: … 'record_session'` |
| **RL-7** | `tests/test_status.py::TestHistoricalRecords::test_old_green_rows_are_shown_as_run_unknown_not_green` | **行為紅** | `AssertionError`:舊紀錄被印成 green |
| ODC-2 | `tests/test_status.py::TestOrphans::test_a_renamed_red_test_is_orphaned_not_green` | 介面紅 | `AttributeError: … 'record_session'` |
| RL-5 | `tests/test_status.py::TestRunEvidence::test_no_run_at_all_is_not_zero_tests_and_not_a_pass` | 介面紅 | `AttributeError: … 'record_session'` |
| ODC-3 | `tests/test_status.py::TestRunEvidence::test_no_producer_means_undecidable_not_green_not_c` | 介面紅 | `AttributeError: … 'load_runs'` |

### 14.3 帳本

| 時點 | SHA-256 | bytes | lines |
|---|---|---|---|
| before(所有 `--collect-only` 之後重取) | `460f714f02c527081d8242520021f611ad0a62c52e3ae592977ae7fc7be7684c` | 552165 | 2043 |
| after | `05c819a047bd83bf88bfb3aba040c4d55a6e63eddd3de5a396bca03a2457d632` | 564441 | 2089 |

新增 **46** 行(第 2044–2089 行):`ticket_id == "145"` 46 筆、`!= "145"` 0 筆;
`red` **2** 筆(`tests/test_redlight.py`、`tests/test_status.py`)、`green` **44** 筆、其他 / 缺欄 **0** 筆。
測試造的假檔名(`tests/test_thing.py`、`tests/test_x.py`、`tests/test_broken.py`)在真實帳本中各 **0** 筆 —— producer 紅燈的隔離有效。

`tests/test_status.py` 那一筆紅燈的 `impl_hash` 為 `bdc3a089…fadf0`,即 `.claude/portable/status.py` 在本 HEAD 的內容 —— Station 4 修改 status.py 時 R3 要求的「屬於票 145、對著改動前內容發生的紅燈」由這一筆滿足。
(`redlight.py` 仍在 R3 豁免清單;依〈十三〉裁決 6,drain 為 Station 4 前的獨立 transition commit。)

---

## 十五、Station 3→4 轉場

### 15.1 Jeff 驗收

Station 3 Red-light = **PASS / ACCEPTED**(Jeff,2026-10-02)。依〈十三〉裁決 6,本轉場只 drain `.claude/hooks/redlight.py` 的 R3 豁免並驗證;不改 redlight.py 本體、不改 tests/、不改 pipeline.json。

### 15.2 drain 前提驗證(唯讀)

```
$ git ls-files --eol .claude/hooks/redlight.py
i/lf    w/lf    attr/text eol=lf      	.claude/hooks/redlight.py
$ sha256sum .claude/hooks/redlight.py
0dadc80d19a7f1d11246d0fdeb2d75ca3f5c170511ec14b142fba394512f0ed7 *.claude/hooks/redlight.py
```

`.dev/test-runs.jsonl` 第 2074 行(Station 3 紅燈跑,`2026-10-02T14:08:27.690782+00:00`)的 `tests/test_redlight.py` red 紀錄:

| 欄位 | 值 | 判定 |
|---|---|---|
| `impl_file` | `.claude/hooks/redlight.py` | 相符 |
| `ticket_id` | `"145"` | 相符 |
| `impl_hash` | `0dadc80d19a7f1d11246d0fdeb2d75ca3f5c170511ec14b142fba394512f0ed7` | **與 sha256sum 逐字相同**(工作樹與 index 皆 lf ⇒ sha256sum 即 `content_hash`) |

排水格式依據:票 137 `:152-167`(節標題「排水紀錄格式(本票的權威定義)」在 `:152`;格式行 `# drained: <path> <YYYY-MM-DD> <ticket>` 在 `:155`;規矩表 `:158-165`;契約 `drained_from_lines()` 在 `:167`)。

### 15.3 active entries 前後對照(條目行 = 非註解、非空行)

| drain 前(9 筆,清單第 25–33 行) | drain 後(8 筆,清單第 29–36 行) |
|---|---|
| `.claude/hooks/gate.py` | `.claude/hooks/gate.py` |
| `.claude/hooks/redlight.py` | **(移除)** |
| `.claude/patches/apply_patches.py` | `.claude/patches/apply_patches.py` |
| `.claude/portable/claude_md.py` | `.claude/portable/claude_md.py` |
| `.claude/portable/g1_verify.py` | `.claude/portable/g1_verify.py` |
| `.claude/portable/install.py` | `.claude/portable/install.py` |
| `.claude/portable/leak_scan.py` | `.claude/portable/leak_scan.py` |
| `.claude/portable/manifest.py` | `.claude/portable/manifest.py` |
| `.claude/portable/verify_gates.py` | `.claude/portable/verify_gates.py` |

被移除者恰為 `.claude/hooks/redlight.py`;其餘 8 筆逐字不變;`.claude/hooks/redlight.py` 不在 drain 後的 active entries;
`# drained: .claude/hooks/redlight.py 2026-10-02 145` 存在(清單第 28 行)。

### 15.4 T1 commit

`b27ca301b058c60c3972eb247e2b701f4c38c3d4` —— `.agents/legacy-no-redlight.txt` 一檔,`4 1`:

- 刪除條目行 `.claude/hooks/redlight.py`
- 新增 `# drained: .claude/hooks/redlight.py 2026-10-02 145`(既有排水行的下一行)
- 散文排水紀錄末尾追加 2026-10-02 一筆(三行)

⚠ 清單第 26 行既有註解「既有 9 筆豁免條目一筆未增未減」是票 137 當時的陳述,drain 後已不精確;依本轉場「其餘行一字不改」未動。

### 15.5 驗證全套(在 `b27ca30` 上,只跑一次)

| 項 | 值 |
|---|---|
| 固定指令 | `python -X utf8 -m pytest -q` |
| exit code | **1** |
| 摘要行 | `14 failed, 1912 passed, 3 skipped, 3 xfailed in 141.67s (0:02:21)` |
| 失敗集合 | **等於** Station 3 預期 Red-light 集合(〈十四〉14.2 的 14 支),不多不少 |
| 既有測試失敗 | **0** |
| `tests/test_gate.py::TestT137TheRealListUnderTheNewRule::test_the_real_list_is_the_generator_output_minus_drained` | **未失敗;exact PASS 未由本次固定指令直接觀察。** 佐證:`addopts = "-ra"` 會逐條列出所有非通過結果,本次 3 筆 SKIPPED 皆為 `tests\test_gate.py:451 / 459 / 473`(symlink),3 筆 XFAIL 皆為 `tests/test_g1_guard.py`,該測試不在其中 |

### 15.6 帳本

| 時點 | SHA-256 | bytes | lines |
|---|---|---|---|
| before | `05c819a047bd83bf88bfb3aba040c4d55a6e63eddd3de5a396bca03a2457d632` | 564441 | 2089 |
| after | `6069453b9c0624ad42b898afded146bf01dd906cbd8be44f9c4fafa5655d9bd2` | 576717 | 2135 |

新增 **46** 行:全部 `ticket_id == "145"`(全帳本 `"145"` 由 92 → 138);red **2**(`tests/test_redlight.py`、`tests/test_status.py`)、green **44**、其他 **0**。

---

## 十六、Station 4 實作

### 16.1 physical persistence 的決定(規劃書一、B)

| 項目 | 決定 | 理由 |
|---|---|---|
| Q1 存哪裡 | **另一本帳 `<root>/.dev/test-sessions.jsonl`**,不寫進 `test-runs.jsonl` | `gate.redlight_missing()`(R3,權威層)逐行讀 `test-runs.jsonl`,`test_file` 命中而缺 `impl_exists` 就擋(`gate.py:2143-2144`);同檔混放會讓 R3 的解析面跟著變。既有 8 欄紀錄因此**一筆不改、不補欄位**(Backward compatibility 1、4) |
| Q2 record type | 每筆 `{"kind": "session", "run_id", "time", "ticket_id", "exit_code", "collected", "deselected", "outcomes"}` | 規劃書一、A-3 的事實逐項落成欄位;`kind` 留給日後同帳其他類型 |
| 落點由誰決定 | **`root` 參數**(`redlight.session_log(root)`),不由模組常數 | status 依 root 載入 redlight.py 讀取、測試以 tmp root 寫入 —— 三方對同一個 root 指向同一本帳 |
| 寫入時機 | `pytest_sessionfinish`,**在逐檔紀錄之後**,每個 session 恰好一筆 | 0 collected、全部 deselected、invocation 錯誤時逐檔迴圈一筆都不寫(RECON Collapse ①),這一筆是唯一痕跡;寫在後面使同一時點 run 事實排在逐檔紀錄之後 |
| 讀取失敗 | 任何一行讀不動 ⇒ `load_runs()` 整本回 `[]` | 讀到一半會讓「較晚的 run」看起來不存在;回 `[]` ⇒ 「無 run 證據 / 不可判定」⇒ 沒有紅能因此退掉 |
| A-6 接合 | status 以 `ticket_id` + `time` 把 8 欄紀錄與 run 事實排成一條時間線;同一時點 run 事實在後 | 不需要在 8 欄紀錄加 `run_id` |
| `.gitignore` | 不改 —— `/.dev/*` 已涵蓋新帳 | |

### 16.2 四個檔的改動(`git diff f50b285 --stat`)

```
 .claude/hooks/redlight.py  | 124 +++++++++++++++++++++++
 .claude/portable/status.py | 242 +++++++++++++++++++++++++++++++++++++++++----
 tests/conftest.py          |  68 +++++++++++++
 tests/test_status.py       |  12 +++
 4 files changed, 427 insertions(+), 19 deletions(-)
```

- **`.claude/hooks/redlight.py`**(+124 / −0):**只在檔尾追加**(既有行號不動 —— `tests/test_line_ending_parity.py` 與 `tests/test_non_source_list_parity.py` 引用 `:56` / `:77`)。新增 `SESSION_LOG_NAME`、`COLLECTION_ERROR`、`session_log(root)`、`_ticket_of(root)`、`record_session(root, ...)`、`load_runs(root)`、`run_state(run)`。`run_state` 對照表:exit code ∉ {0, 1, 5} 或有收集錯誤 ⇒ D;任一 failed ⇒ B;0 collected ⇒ C;無任何 passed ⇒ F;其餘 ⇒ A。
- **`.claude/portable/status.py`**(+223 / −19):新增 `load_redlight(root)`(per-root 載入,與 `load_gate()` 同手法;None 不快取)、`_run_facts`、`ticket_test_state(records, runs, ticket)`、`_apply_run`、`_last_run_text`、`_run_source`。`_evidence` 的 `test-runs` 行改由 `ticket_test_state()` 計數,尾段由「全套結果:未記錄(帳本不記全套)」改為「最近一次 run:…」;`_derived` 由兩行改為四行(red / green / green (run 事實未知) / orphaned)。**`_latest_per_file()` 未動**。
- **`tests/conftest.py`**(+68 / −0):逐段見 16.3。
- **`tests/test_status.py`**(+12 / −0):只在 570 / 571 那一支測試補 run-level facts,見 16.4。

**未修改**:`tests/test_redlight.py`(`git diff f50b285 --stat -- tests/test_redlight.py` 無輸出)、Station 3 的 14 支紅燈測試、`.claude/hooks/gate.py`、`.agents/`、`pipeline.json`。

### 16.3 `tests/conftest.py` 逐段

| 段 | 內容 |
|---|---|
| ① 模組層 `_run` | `{"selected": None, "deselected": [], "collect_errors": [], "outcomes": {}}` —— 逐身分的 run 事實;既有逐檔 `_outcomes` 並存,不互相推導 |
| ② `_nodeid(obj)` | 取 `nodeid`,`\` 換 `/` |
| ③ `pytest_collectreport` 追加一行 | 收集失敗時 `_run["collect_errors"]` 加 `<檔>::<collection error>`(不限 `.py`);既有寫 `_outcomes` 的兩行未動 |
| ④ 新 hook `pytest_deselected(items)` | 記下被排除的身分(deselect 不產生任何 report) |
| ⑤ 新 hook `pytest_collection_finish(session)` | 記下 `session.items`(= selected) |
| ⑥ `_run_outcome(report)` | 一份 report 對身分結果的貢獻:failed ⇒ `failed`;skipped ⇒ `skipped`(xfail ⇒ `other`);call passed ⇒ `passed`(xpass ⇒ `other`);**屬性一律 `getattr` 帶預設值**(既有測試的假 report 只有四個屬性) |
| ⑦ `pytest_runtest_logreport` 追加三行 | 逐身分寫入 `_run["outcomes"]`;`failed` 一旦記下不被後來的 report 蓋掉。既有寫 `_outcomes` 的部分未動 |
| ⑧ `pytest_sessionfinish` 追加 | 既有逐檔迴圈之後,`record_session(_ROOT, exit_code=exitstatus, collected=selected + deselected + collect_errors, deselected=…, outcomes=…)`;舊版 redlight.py 無 `record_session` ⇒ 照舊只寫逐檔紀錄 |

### 16.4 570 / 571 / 749 的 fixture 補件

依〈十三〉裁決 2(C)。**斷言一字未改**(`git diff f50b285 -U0 -- tests/test_status.py` 只有一段 `@@ -565,0 +566,12 @@` 的純新增)。

補在 `test_a_file_that_went_red_then_green_counts_as_green` 寫完 8 欄紀錄之後、`render(root)` 之前,逐字:

```
        # 票 145〈十三〉裁決 2(C):Station 4 補 run-level facts。
        # 上面 test_a 的綠紀錄是 8 欄格式、沒有 run 事實 ⇒ 依 ODC-1 沒有退紅權;
        # 補一次「test_a 全檔被選到、唯一一條實際執行且通過、該檔無 failure」的 run,
        # 時點與那筆綠相同。紅紀錄沒有 failed_tests(身分不明)⇒ 依〈十三〉裁決 3,
        # 該檔全部 collected 身分都要 passed —— 這個 run 滿足它。
        # 第一行讓 fake repo 有 redlight.py:status 依 root 載入它讀 run 事實(裁決 1)。
        shutil.copy2(str(REAL_REDLIGHT),
                     str(pathlib.Path(root) / ".claude" / "hooks" / "redlight.py"))
        redlight.record_session(
            root, run_id=u"fixture-570-571", time=u"2026-09-02T02:00:00+00:00",
            ticket_id=u"99", exit_code=0, collected=[u"tests/test_a.py::test_one"],
            deselected=[], outcomes={u"tests/test_a.py::test_one": u"passed"})
```

**靜態預期理由**(實作前寫下,不是觀察):實作後,test_a 那筆 8 欄綠紀錄沒有 run 事實,將不再具有退紅權 ⇒ 若不補,570 / 571 會因 test_a 仍為 red 而不成立 —— 故需補 facts。
⚠ **超出「純 run-level facts」的一項**:`shutil.copy2(...redlight.py)` 是 fake repo 基礎設施,不是 facts。理由:〈十三〉裁決 1 規定 status 依 root 載入 redlight.py 讀 run 事實,而該測試的 root 由既有 `_make_root()` 造、沒有 redlight.py —— 不補這一行,補上的 facts status 讀不到。這一行是純新增,未改任何既有行。

**749 未補**:它直接呼叫 `status._latest_per_file()`,而該函式未改(16.2)—— 依靜態分析不需要。

### 16.5 證據鏈

| 步驟 | 證據 |
|---|---|
| 前置 H0 / L0 | `6069453b9c0624ad42b898afded146bf01dd906cbd8be44f9c4fafa5655d9bd2` / 576717 bytes / 2135 行 |
| S4-1 commit 前未執行 pytest | commit 前重量帳本:SHA-256 / bytes / lines **與 H0 / L0 完全相同**;`.dev/test-sessions.jsonl` 不存在 |
| S4-1 commit | `db0128348a877c557684573a584a38797425ae5d`(四檔 `124 0` / `223 19` / `68 0` / `12 0`);pre-commit 未擋 |
| 固定全套(只跑一次,在 `db01283` 上) | `python -X utf8 -m pytest -q` ⇒ exit code **0**;`1926 passed, 3 skipped, 3 xfailed in 146.92s (0:02:26)`;**failed 0** |
| 14 支紅燈 | **全部轉綠**(1926 = 1912 + 14;skipped / xfailed 維持 3 / 3,皆為 baseline 那 6 支) |
| 帳本只追加 | after 前 576717 bytes 的 SHA-256 = `6069453b…d9bd2` = H0 ⇒ **前 L0 行逐位元組未變** |
| 帳本 after | `a81559a44f2689eb412eb663f35c3b434f197a466bfe9b15b2b256fd3e664062` / 588020 bytes / 2181 行;新增 46 行,全部 `"145"`、全部 green |
| run 事實帳本 | `.dev/test-sessions.jsonl` 1 行:`ticket_id` `"145"`、`exit_code` 0、`deselected` 空 |

**status.py 的 Evidence 與 Derived**(節錄兩行;全文見報告):

```
test-runs: 本票 red 0 / green 46 / run 事實未知 0 / orphaned 0;最後一筆 tests/test_verify_gates.py=green @ 2026-10-02T14:51:04.809936+00:00;最近一次 run:A(exit 0;collected 1932 / deselected 0 / passed 1926 / failed 0 / skipped 3)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl)
tests red under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
```

`tests/test_redlight.py` 與 `tests/test_status.py` 先前的紅身分,在這次 run 中皆被選到、實際執行且通過、該檔無 failure ⇒ 依 ODC-1 退紅。

### 16.6 測試三層

| 層 | 狀態 |
|---|---|
| **UNIT** | 固定全套 exit 0,`1926 passed, 3 skipped, 3 xfailed` |
| **CLEAN** | 未證明 |
| **REAL** | 留待 Jeff 端 status_all 確認(本站不宣稱) |

---

## 十七、Station 5 獨立審查（FAIL）與 Station 3b 裁決（2026-10-02，Jeff）

Station 5 結果：FAIL（獨立、無記憶審查者）。審查包與審查結果原文存於 docs/audits/2026-10-02-m1a-station5-review-package.md 與 docs/audits/2026-10-02-m1a-station5-independent-review-fail.md。Station 4 實作保留，作為 3b 紅燈要打紅的 baseline，不回滾。

審查檔保存模型：.scratch/m1a-s5-review/ 保留原始審查證據（未修改）；docs/audits/ 為 repo-normalized archival copy。
- 審查包：原始與 repo copy 的 SHA-256 皆為 892db3f7b8a59884dba01590becff2406fa089e841b0bec40e6479e8c3bab165。
- 審查結果（FAIL）：原始檔為 CRLF、無檔尾換行，SHA-256 99f617c8a273db431b7691b3cd48090f9e061959c69d2dd2e3f575e1853ea7a0；repo copy 依 text normalization 保存為 LF 並補檔尾換行，SHA-256 b9b559f6124e0f2fb6b6ae554b45bdef14dda341ae86e8043664f3dfd477ca3f。文字內容未改，差異僅限 CRLF→LF 與檔尾換行。
- 依 .gitattributes 的 * text=auto，進版控的 blob 本即為 LF；不以「進 Git 後與原始位元組相同」作為要求。
- 審查包含 7 處 trailing whitespace（第 652、653、850、884、888、920、946 行），為內嵌 unified diff 的空白 context 行，屬原始審查證據，刻意保留未修改；本 commit 的 git diff --check 以此 7 筆為已知例外。

確認的缺陷：
- F1：session 缺必要欄位（如 deselected、collected）或欄位型別不符時，被當成空集合或錯誤型別並進入正常判定，可退紅、可誤判 C。
- F2：run_state 判為 D 的 run（例：exit 1 + 他檔收集錯誤），其他檔仍可退紅並產生 green。
- F3：「沒有 deselected」被當成「整檔被選到」；以 nodeid 指名執行（如 pytest tests/test_x.py::test_a）時，未收集的身分不產生 deselected ⇒ 身分不明的舊紅被錯誤退紅；已知紅身分被錯誤判為 orphaned。
- F4：紅燈測試分別驗 producer 與 consumer，沒有串接驗證，F1–F3 因此漏網。

Invariant（新增）：Absence is not coverage —— 一個 test identity 沒出現在某 run 中，不得僅因此推論它已刪除、改名、不存在或已被完整涵蓋。

裁決：
1. Coverage authority（F3）：每個 run、每個 test file 有一個 machine-readable 事實 full_file_coverage ∈ {true, false, unknown}。只有 producer 能正向證明該次對該檔為整檔涵蓋時才為 true（例：該檔或其上層目錄以不含 :: 的位置參數進入收集、該檔沒有任何 deselected、沒有其他使涵蓋範圍未知的情形）；nodeid 指名等明確窄選為 false；其餘一律 unknown。只有 true 才有 ODC-1 退紅權與 ODC-2 orphan 判定權；false / unknown 兩者皆無。不知道，就不是完整。
2. D 狀態（F2）：run_state(run) == D 時，整個 run 沒有任何退紅權，也不得使任何檔成為 green。
3. Schema fail-closed（F1）：session 缺必要欄位、型別不符、或 outcome 身分不屬於本次 selected 時，該 run 不得進入正常語意；不得以「缺欄 ⇒ 空集合」或「錯型別照常迭代」處理；不得產生退紅、orphan 或 green；須可被觀察到。
4. 串接驗證（F4）：須有 producer → 持久化 run 事實 → status 的串接測試。
5. 4b 測試補件授權：Station 3 原 14 支測試與 570 / 571 / 749 的 assertion、預期語意、test identity 一律不改；4b 只授權在 ODC-2 孤兒測試（test_a_renamed_red_test_is_orphaned_not_green）與 570 / 571 / 749 的 fixture 補上 full_file_coverage = true 的事實。若只補事實仍無法維持原 assertion：立即停手回裁。
6. 3b 新增測試分兩類：behavior-red（現行實作必須失敗）與 regression-lock（現行已正確，必須通過）；驗收以預先標定的 exact nodeid 集合為準，不以數量為準。
7. 證據原則：任何 pytest（含 --collect-only）只能在乾淨、已 commit 的 HEAD 上執行。
8. Debt（不擋 M1-a）：.dev/test-sessions.jsonl 每次全套約增長 450 KB，reader 為全檔讀取；M1-a 結案時另開票（rotation / index / compaction），本票不得順手最佳化。

3b 補件（2026-10-02，Jeff）：4b 指令明文要求的兩項行為先補紅燈 ——
- B10：pytest 無使用者位置參數的正常全套執行（即固定指令 python -X utf8 -m pytest -q），該檔被正常收集、無 deselected ⇒ full_file_coverage 必須為 "true"。fake session 依本機 pytest 原始碼與本 repo 設定推導出的無位置參數 config.args 值／語意建構；此為靜態推導，不宣稱為實際執行觀察值。
- B11：schema 不合格的 session 不得被靜默丟棄，也不得被當成正常 run。在同一個 root 中加入該 session 前後，status 輸出的 Evidence 與 Derived 區塊必須可區分（表示位置與文字由 4b 決定）；加入後不得顯示為正常狀態 A / B / C / F；不得 green、不得 orphan。

---

## 十八、Station 3b 紅燈證據

### 18.1 commit 與執行

| 項 | 值 |
|---|---|
| 刀①(落票 + 審查存檔) | `280a551c64d088ad7960933b9761b656ffcb373b` |
| 刀②(紅燈 commit) | `a9d885a654d2f5e4846262f247a5974f4e174adc`(`tests/test_redlight.py` `162 0`、`tests/test_status.py` `331 0`) |
| 固定指令 | `python -X utf8 -m pytest -q`(〈十二〉),在 `a9d885a` 上只跑一次 |
| exit code | **1** |
| 摘要行 | `15 failed, 1929 passed, 3 skipped, 3 xfailed in 150.16s (0:02:30)` |
| 既有測試 | **0 失敗**(1929 = Station 4 的 1926 + L1–L3 三支) |

### 18.2 案例 → nodeid → 分類

消失集合(修改前收集有、修改後沒有)= **空**。新增 18 支,每個案例恰一支。

| 案例 | Finding | nodeid | 分類 | 實際 |
|---|---|---|---|---|
| B1a | F3 | `tests/test_redlight.py::TestFileCoverage::test_b1a_a_nodeid_argument_is_not_full_coverage` | interface-red | 失敗:`AttributeError … 'file_coverage'` |
| B1b | F3 | `tests/test_redlight.py::TestFileCoverage::test_b1b_a_backslash_nodeid_argument_is_not_full_coverage` | interface-red | 同上 |
| B1c | F3 | `tests/test_redlight.py::TestFileCoverage::test_b1c_a_file_argument_without_deselection_is_full_coverage` | interface-red | 同上 |
| B1d | F3 | `tests/test_redlight.py::TestFileCoverage::test_b1d_a_parent_directory_argument_is_full_coverage` | interface-red | 同上 |
| B1e | F3 | `tests/test_redlight.py::TestFileCoverage::test_b1e_a_file_argument_with_deselection_is_not_full_coverage` | interface-red | 同上 |
| B1f | F3 | `tests/test_redlight.py::TestFileCoverage::test_b1f_no_config_means_unknown` | interface-red | 同上 |
| B1g | F3 | `tests/test_redlight.py::TestFileCoverage::test_b1g_an_argument_outside_the_root_means_unknown` | interface-red | 同上 |
| B6 | F1 | `tests/test_redlight.py::TestRunStateSchema::test_b6_a_session_without_collected_is_not_state_c` | behavior-red | 失敗:`AssertionError`(判成 C) |
| B2 | F3 | `tests/test_status.py::TestCoverageChain::test_b2_a_nodeid_run_does_not_retire_an_unidentified_red` | behavior-red | 失敗:`AssertionError`,`green: tests/test_x.py` |
| B3 | F3 | `tests/test_status.py::TestCoverageChain::test_b3_a_nodeid_run_does_not_orphan_a_known_red` | behavior-red | 失敗:`AssertionError`,`orphaned: tests/test_x.py(…::test_b)` |
| B4 | F2 | `tests/test_status.py::TestDStateRetiresNothing::test_b4_a_d_run_with_a_collection_error_elsewhere_retires_nothing` | behavior-red | 失敗:`AssertionError`,`green: tests/test_x.py` |
| B5 | F1 | `tests/test_status.py::TestSessionSchemaFailClosed::test_b5_a_session_without_deselected_retires_nothing` | behavior-red | 失敗:`AssertionError`,`green: tests/test_x.py` |
| B7 | F1 | `tests/test_status.py::TestSessionSchemaFailClosed::test_b7_an_outcome_outside_collected_retires_nothing` | behavior-red | 失敗:`AssertionError`,`green: tests/test_x.py` |
| B9 | F1 | `tests/test_status.py::TestSessionSchemaFailClosed::test_b9_a_string_deselected_retires_nothing_and_orphans_nothing` | behavior-red | 失敗:`AssertionError`,`green: tests/test_x.py` |
| B8 | Absence is not coverage | `tests/test_status.py::TestAbsenceIsNotCoverage::test_b8_a_run_without_coverage_facts_does_not_orphan` | behavior-red | 失敗:`AssertionError`,`orphaned: tests/test_x.py(…::test_old)` |
| L1 | F4(RL-6 串接) | `tests/test_status.py::TestChainRegressionLocks::test_l1_three_skipped_645_deselected_keeps_the_red` | regression-lock | **通過** |
| L2 | F4(RL-4 串接) | `tests/test_status.py::TestChainRegressionLocks::test_l2_an_interrupted_run_keeps_the_red` | regression-lock | **通過** |
| L3 | F4(正向對照) | `tests/test_status.py::TestChainRegressionLocks::test_l3_a_full_directory_run_retires_the_red` | regression-lock | **通過** |

**預期紅集合**(B1a–B1g、B6、B2–B5、B7–B9,共 15 個 nodeid)**= 實際失敗集合**,不多不少;
**預期綠集合**(L1–L3)全部不在失敗集合。

### 18.3 collect-only 與帳本

| 時點 | test-runs(bytes / lines) | test-sessions(bytes / lines) | 說明 |
|---|---|---|---|
| BEFORE-COLLECT 之前 | 588020 / 2181 | 455876 / 1 | |
| BEFORE-COLLECT 之後 | 588020 / 2181 | 463757 / 3 | **collection-only observation,非紅燈驗收證據**(兩次 `--collect-only` 各寫一筆 session) |
| AFTER-COLLECT 之後(= 全套 before) | 588020 / 2181(`a81559a4…4062`) | 473458 / 5(`e2b0e460…8dff2`) | **collection-only observation,非紅燈驗收證據** |
| 全套 after | 600499 / 2227(`30a3513e…5fc17`) | 933154 / 6(`bacf0033…f334d`) | |

**防污染**:
- test-runs 新增 **46** 行(= 本次測試檔數);after 前 588020 bytes 的 SHA-256 = `a81559a4…4062`(before)⇒ 前段逐位元組不變。
- test-sessions 新增恰 **1** 行(第 6 行,`exit_code` 1,本次全套);after 前 473458 bytes 的 SHA-256 = `e2b0e460…8dff2`(before)⇒ 前段逐位元組不變。
- 測試造的假身分與假檔名(`tests/test_x.py`、`tests/test_y.py`、`tests/test_thing.py`、`tests/test_broken.py`、`run_id` b5 / b6 / b7 / b8 / b9)在兩本真實帳本中皆 **0** 筆。

### 18.4 status.py(本次全套後)

```
test-runs: 本票 red 2 / green 44 / run 事實未知 0 / orphaned 0;…;最近一次 run:B(exit 1;collected 1950 / deselected 0 / passed 1929 / failed 15 / skipped 3)
tests red under ticket 145: tests/test_redlight.py / tests/test_status.py
tests orphaned under ticket 145: (無)
```

(節錄;全文見 `docs/audits/2026-10-02-m1a-station3b-redlight.md`。)

---

## 十八之一、Station 3b 補件紅燈證據

### 18-1.1 pytest 無位置參數時的 `config.args`(**靜態推導,未實際執行觀察**)

`python -m pip show pytest`:`Version: 9.1.1`;`Location:` 使用者層 Python 3.11 的 `site-packages`(絕對路徑不入票)。

| 來源 | 行號 | 原文 / 內容 |
|---|---|---|
| `_pytest/config/__init__.py` | 1087–1099 | `class ArgsSource(enum.Enum)`:`ARGS`、`INVOCATION_DIR`、`TESTPATHS` |
| 同上 | 1411–1413 | `if args:` ⇒ `source = Config.ArgsSource.ARGS`;`result = args` |
| 同上 | 1415–1422 | `if invocation_dir == rootpath:` ⇒ `source = Config.ArgsSource.TESTPATHS`;非 pyargs 時 `result.extend(sorted(glob.iglob(path, recursive=True)))` 逐一展開 testpaths |
| 同上 | 1435–1437 | `if not result:` ⇒ `source = Config.ArgsSource.INVOCATION_DIR`;`result = [str(invocation_dir)]` |
| 同上 | 1624–1631 | `self.args, self.args_source = self._decide_args(args=getattr(self.option, FILE_OR_DIR), …, testpaths=self.getini("testpaths"), invocation_dir=self.invocation_params.dir, rootpath=self.rootpath, …)` |
| `_pytest/config/findpaths.py` | 312–315 | 未指定 inifile 時,由 invocation dir 往上 `locate_config()` 找設定檔,rootdir = 找到的設定檔所在目錄 |
| `pyproject.toml`(本 repo) | 70–72 | `[tool.pytest.ini_options]`;`testpaths = ["tests"]`;`addopts = "-ra --strict-markers"` |

**推導**:固定指令從 repo 根執行、無使用者位置參數 ⇒ rootdir = repo 根 = invocation dir ⇒ 走 `TESTPATHS` 分支 ⇒
`config.args == ["tests"]`、`config.args_source == Config.ArgsSource.TESTPATHS`。

**B10 的 fake 依此建構**:`_SessionWithConfig([...], ["tests"], tmp_path)`(`rootpath` 與 `invocation_params.dir` 皆為 root),
另設 `session.config.args_source = pytest.Config.ArgsSource.TESTPATHS`(`pytest/__init__.py:107` 公開匯出 `Config`)。

### 18-1.2 commit、collect 與集合

| 項 | 值 |
|---|---|
| 刀 A①(落票) | `8c18157b8b5ddba50557118d99d36b0bd8ba9622`(票 145 `10 1`) |
| 刀 A②(紅燈) | `628c060f6f5fda886ff5feba6241272e76b06cc5`(`tests/test_redlight.py` `55 0`、`tests/test_status.py` `51 0`) |
| BEFORE-COLLECT | `tests/test_redlight.py` 29 支、`tests/test_status.py` 67 支 |
| AFTER-COLLECT | 30 支、68 支 |
| 新增集合 | **恰為 B10、B11 兩支** |
| 消失集合 | **空** |

| 案例 | Finding | nodeid | 分類 | 實際 |
|---|---|---|---|---|
| B10 | F3(〈十七〉3b 補件) | `tests/test_redlight.py::TestFixedCommandCoverage::test_b10_the_fixed_command_without_positional_args_is_full_coverage` | interface-red | 失敗:`AttributeError: … has no attribute 'file_coverage'` |
| B11 | F1(〈十七〉3b 補件) | `tests/test_status.py::TestMalformedSessionIsVisible::test_b11_a_malformed_session_is_neither_dropped_silently_nor_read_as_normal` | behavior-red | 失敗:`AssertionError: 不合格的 session 被當成正常狀態 A`(前後輸出確有不同,但不合格 session 被顯示成 `最近一次 run:A(… deselected 23 …)` —— `23` 是字串的字元數 —— 並讓 test_x.py 變 green) |

### 18-1.3 固定全套(在 `628c060` 上,只跑一次)

| 項 | 值 |
|---|---|
| exit code | **1** |
| 摘要行 | `17 failed, 1929 passed, 3 skipped, 3 xfailed in 135.89s (0:02:15)` |
| 實際失敗集合 | **= 3b 既有預期紅集合(15 支,見〈十八〉18.2)∪ {B10, B11},共 17 支,不多不少** |
| L1–L3 | 皆**未失敗**(1929 passed 與 3b 時相同) |
| 既有測試 | **0 失敗** |

### 18-1.4 帳本防污染

| 帳本 | before(AFTER-COLLECT 後) | after | 新增 | 前段 |
|---|---|---|---|---|
| `.dev/test-runs.jsonl` | 600499 bytes / 2227 行(`30a3513e…5fc17`) | 613185 / 2273(`b555ded4…2ada`) | **46** 行(= 測試檔數) | 前 600499 bytes 的 SHA-256 = before ⇒ **逐位元組不變** |
| `.dev/test-sessions.jsonl` | 952809 / 10(`f3a48d45…89bf4`) | 1413031 / 11(`d97b7631…e12e`) | **1** 行(第 11 行,`exit_code` 1) | 前 952809 bytes 的 SHA-256 = before ⇒ **逐位元組不變** |

四次 `--collect-only` 讓 session 帳本 6 → 8 → 10 行 —— **collection-only observation,非紅燈驗收證據**;test-runs 未被 collect-only 寫入。
測試的假身分 / 假檔名 / 假 run_id(`tests/test_x.py`、`tests/test_y.py`、`b5`–`b11`)在兩本真實帳本中皆 **0** 筆。

**status.py**(節錄):`tests red under ticket 145: tests/test_redlight.py / tests/test_status.py`;`tests orphaned under ticket 145: (無)`;
`最近一次 run:B(exit 1;collected 1952 / deselected 0 / passed 1929 / failed 17 / skipped 3)`。

---

## 相關

- **票 139** —— 原始 finding。本票承接;其證據與未查邊界不改寫。
- **票 137** —— 被票 139 那次窄選遮蔽的那條紅。**本票不處理它。**
- **票 93** —— CI 的 `--deselect`。**本票不處理它。**
