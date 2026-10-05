# 票 145 —— M1-a:一次 test run 的證據要如實表達它「跑了什麼、結果是什麼」

**狀態**:動工 —— Station 4i PASS / COMPLETED（Windows 本機 + POSIX 外部 clean-room）；待 Station 5i 獨立審查。
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
>
> - 狀態(舊,第十代):~~`動工 —— Station 3b(含補件)紅燈已寫(待 Jeff 驗收);Station 4b 未開始。`~~
>   —— 2026-10-02 Station 4b 修正完成、固定全套 exit 0 後由第 3 行取代(見〈十九〉)。
>
> - 狀態(舊,第十一代):~~`動工 —— Station 4b 修正完成(固定全套 exit 0);待 Station 5b 審查。`~~
>   —— 2026-10-02 Station 5b 審查包建立後由第 3 行取代(見〈二十〉)。
>
> - 狀態(舊,第十二代):~~`動工 —— Station 5b 審查包已建立;待獨立審查。`~~
>   —— 2026-10-02 Station 5b 獨立審查 FAIL 後由第 3 行取代(見〈二十一〉)。
>
> - 狀態(舊,第十三代):~~`動工 —— Station 5b FAIL(S5b-F1 阻擋);回 Station 3c 補紅燈。`~~
>   —— 2026-10-02 Station 3c 紅燈規劃寫完後由第 3 行取代(見〈二十二〉)。
>
> - 狀態(舊,第十四代):~~`動工 —— Station 3c 紅燈規劃已寫(待 Jeff 裁 P3);未寫測試。`~~
>   —— 2026-10-02 Station 3c 紅燈寫完後由第 3 行取代(見〈二十三〉)。
>
> - 狀態(舊,第十五代):~~`動工 —— Station 3c 紅燈已寫(待 Jeff 驗收);Station 4c 未開始。`~~
>   —— 2026-10-02 Station 4c 修正完成、固定全套 exit 0 後由第 3 行取代(見〈二十五〉)。
>
> - 狀態(舊,第十六代):~~`動工 —— Station 4c 修正完成(固定全套 exit 0);待 Station 5c 審查。`~~
>   —— 2026-10-02 Station 5c 審查包建立後由第 3 行取代(見〈二十六〉)。
>
> - 狀態(舊,第十七代):~~`動工 —— Station 5c 審查包已建立;待獨立審查。`~~
>   —— 2026-10-02 Station 5c 獨立審查 FAIL 後由第 3 行取代(見〈二十七〉)。
>
> - 狀態(舊,第十八代):~~`動工 —— Station 5c FAIL(S5c-F1 阻擋);回 Station 3d 補紅燈。`~~
>   —— 2026-10-02 Station 3d 紅燈規劃寫完後由第 3 行取代(見〈二十八〉)。
>
> - 狀態(舊,第十九代):~~`動工 —— Station 3d 紅燈規劃已寫(待 Jeff 裁 P3);未寫測試。`~~
>   —— 2026-10-02 Station 3d 紅燈寫完後由第 3 行取代(見〈二十九〉)。
>
> - 狀態(舊,第二十代):~~`動工 —— Station 3d 紅燈已寫(待 Jeff 驗收);Station 4d 未開始。`~~
>   —— 2026-10-02 Station 4d 修正完成、固定全套 exit 0 後由第 3 行取代(見〈三十一〉)。
>
> - 狀態(舊,第二十一代):~~`動工 —— Station 4d 修正完成(固定全套 exit 0);待 Station 5d 審查。`~~
>   —— 2026-10-02 Station 5d 審查包建立後由第 3 行取代(見〈三十二〉)。
>
> - 狀態(舊,第二十二代):~~`動工 —— Station 5d 審查包已建立;待獨立審查。`~~
>   —— 2026-10-02 Station 5d 獨立審查 FAIL 後由第 3 行取代(見〈三十三〉)。
>
> - 狀態(舊,第二十三代):~~`動工 —— Station 5d FAIL(S5d-F1 阻擋);回 Station 3e 規劃與補紅燈。`~~
>   —— 2026-10-03 Station 3e 紅燈規劃寫完後由第 3 行取代(見〈三十四〉)。
>
> - 狀態(舊,第二十四代):~~`動工 —— Station 3e 紅燈規劃已寫(待 Jeff 裁 P3);未寫測試。`~~
>   —— 2026-10-03 Station 3e 紅燈寫完後由第 3 行取代(見〈三十五〉)。
>
> - 狀態(舊,第二十五代):~~`動工 —— Station 3e 紅燈已寫(待 Jeff 驗收);Station 4e 未開始。`~~
>   —— 2026-10-03 Station 4e 實作提交後由第 3 行取代(見〈三十七〉)。
>
> - 狀態(舊,第二十六代):~~`動工 —— Station 4e 實作已提交;待固定全套驗收。`~~
>   —— 2026-10-03 Station 4e 固定全套 exit 0 後由第 3 行取代(見〈三十七〉37.2)。
>
> - 狀態(舊,第二十七代):~~`動工 —— Station 4e 修正完成(固定全套 exit 0);待 Station 5e 審查。`~~
>   —— 2026-10-03 Station 5e 審查包建立後由第 3 行取代(見〈三十八〉)。
>
> - 狀態(舊,第二十八代):~~`動工 —— Station 5e 審查包已建立;待獨立審查。`~~
>   —— 2026-10-03 Station 5e 獨立審查結果與 Jeff 裁決記錄後由第 3 行取代(見〈三十九〉)。
>
> - 狀態(舊,第二十九代):~~`動工 —— Station 5e 依 Jeff 裁決 FAIL(S5e-F1;審查者原判 PASS);待 Station 3f 紅燈規劃。`~~
>   —— 2026-10-03 Station 3f 紅燈規劃寫完後由第 3 行取代(見〈四十〉)。
>
> - 狀態(舊,第三十代):~~`動工 —— Station 3f 紅燈規劃已寫(待 Jeff 裁);未寫測試。`~~
>   —— 2026-10-03 Station 3f 紅燈提交後由第 3 行取代(見〈四十一〉)。
>
> - 狀態(舊,第三十一代):~~`動工 —— Station 3f 紅燈已提交;待固定全套驗證。`~~
>   —— 2026-10-03 Station 3f 固定全套驗證成立後由第 3 行取代(見〈四十二〉)。
>
> - 狀態(舊,第三十二代):~~`動工 —— Station 3f 紅燈已寫(待 Jeff 驗收);Station 4f 未開始。`~~
>   —— 2026-10-03 Station 4f 實作提交後由第 3 行取代(見〈四十三〉)。
>
> - 狀態(舊,第三十三代):~~`動工 —— Station 4f 實作已提交;待固定全套驗收。`~~
>   —— 2026-10-03 Station 4f 本機固定全套驗收通過後由第 3 行取代(見〈四十三〉43.2)。
>
> - 狀態(舊,第三十四代):~~`動工 —— Station 4f 本機固定全套驗收通過;待 POSIX 跨平台驗收。`~~
>   —— 2026-10-03 POSIX 外部驗證通過後由第 3 行取代(見〈四十三〉43.3)。
>
> - 狀態(舊,第三十五代):~~`動工 —— Station 4f 修正完成(Windows 固定全套 exit 0 + POSIX 外部驗證通過);待 Station 5f 審查。`~~
>   —— 2026-10-03 Station 5f 審查包建立後由第 3 行取代(見〈四十四〉)。
>
> - 狀態(舊,第三十六代):~~`動工 —— Station 5f 審查包已建立;待獨立審查。`~~
>   —— 2026-10-03 Station 5f 獨立審查 PASS(依 Jeff 裁決)後由第 3 行取代(見〈四十五〉)。
>
> - 狀態(舊,第三十七代):~~`動工 —— Station 5f 獨立審查 PASS;待 push 與 CI 確認(Station 6)。`~~
>   —— 2026-10-03 Station 6 CI 淨室驗證 FAIL(依 Jeff 裁決)後由第 3 行取代(見〈四十六〉)。
>
> - 狀態(舊,第三十八代):~~`動工 —— Station 6 FAIL(淨室驗證);待 Station 3g 紅燈規劃。`~~
>   —— 2026-10-03 Station 3g 紅燈規劃寫完後由第 3 行取代(見〈四十七〉)。
>
> - 狀態(舊,第三十九代):~~`動工 —— Station 3g 紅燈規劃已寫(待 Jeff 裁);未寫測試。`~~
>   —— 2026-10-03 Station 3g 紅燈提交後由第 3 行取代(見〈四十八〉)。
>
> - 狀態(舊,第四十代):~~`動工 —— Station 3g 紅燈已提交;待固定全套驗證。`~~
>   —— 2026-10-03 Station 3g 固定全套驗證成立後由第 3 行取代(見〈四十九〉)。
>
> - 狀態(舊,第四十一代):~~`動工 —— Station 3g 紅燈已寫(待 Jeff 驗收);Station 4g 未開始。`~~
>   —— 2026-10-04 Station 3g-1b 紅燈提交後由第 3 行取代(見〈五十〉)。
>
> - 狀態(舊,第四十二代):~~`動工 —— Station 3g-1b 紅燈已提交;待固定全套驗證。`~~
>   —— 2026-10-04 Station 3g-1b 固定全套驗證(乾淨工作樹重跑)成立後由第 3 行取代(見〈五十〉50.4)。
>
> - 狀態(舊,第四十三代):~~`動工 —— Station 3g-1b 紅燈完成;待 Station 4g 實作。`~~
>   —— 2026-10-04 Station 4g 本機固定全套與 clean-room 驗收通過後由第 3 行取代(見〈五十一〉)。
>
> - 狀態(舊,第四十四代):~~`動工 —— Station 4g 本機固定全套與 clean-room 驗收通過;待 POSIX 外部驗收。`~~
>   —— 2026-10-04 POSIX 外部 clean-room 驗收通過、Jeff 裁決 Station 4g = PASS / COMPLETED 後由第 3 行取代(見〈五十一〉51.3)。
>
> - 狀態(舊,第四十五代):~~`動工 —— Station 4g PASS / COMPLETED（Windows 本機 + POSIX 外部 clean-room）；待 Station 5g 獨立審查。`~~
>   —— 2026-10-04 Station 5g 審查包建立後由第 3 行取代(見〈五十二〉)。
>
> - 狀態(舊,第四十六代):~~`動工 —— Station 5g 審查包已建立；待獨立審查。`~~
>   —— 2026-10-04 Station 5g 獨立審查完成(審查者 PASS)、Jeff 裁決 FAIL(S5g-F2)後由第 3 行取代(見〈五十三〉)。
>
> - 狀態(舊,第四十七代):~~`動工 —— Station 5g 獨立審查（審查者 PASS；依 Jeff 裁決 FAIL：S5g-F2）；待 Station 3h 紅燈。`~~
>   —— 2026-10-04 Station 3h 紅燈全套驗證成立後由第 3 行取代(見〈五十四〉)。
>
> - 狀態(舊,第四十八代):~~`動工 —— Station 3h 紅燈完成；待 Station 4h 實作。`~~
>   —— 2026-10-05 Station 4h 本機固定全套與 clean-room 驗收通過後由第 3 行取代(見〈五十五〉)。
>
> - 狀態(舊,第四十九代):~~`動工 —— Station 4h 本機固定全套與 clean-room 驗收通過；待 POSIX 外部驗收。`~~
>   —— 2026-10-05 POSIX 外部 clean-room 驗收通過、Jeff 裁決 Station 4h = PASS / COMPLETED 後由第 3 行取代(見〈五十五〉55.3)。
>
> - 狀態(舊,第五十代):~~`動工 —— Station 4h PASS / COMPLETED（Windows 本機 + POSIX 外部 clean-room）；待 Station 5h 獨立審查。`~~
>   —— 2026-10-05 Station 5h 審查包建立後由第 3 行取代(見〈五十六〉)。
>
> - 狀態(舊,第五十一代):~~`動工 —— Station 5h 審查包已建立；待獨立審查。`~~
>   —— 2026-10-05 Station 5h 獨立審查 FAIL(S5h-F1 major)後由第 3 行取代(見〈五十七〉)。
>
> - 狀態(舊,第五十二代):~~`動工 —— Station 5h 獨立審查 FAIL（S5h-F1 major）；待 Station 3i 紅燈。`~~
>   —— 2026-10-05 Station 3i 紅燈全套驗證成立後由第 3 行取代(見〈五十八〉)。
>
> - 狀態(舊,第五十三代):~~`動工 —— Station 3i 紅燈完成；待 Station 4i 實作。`~~
>   —— 2026-10-05 Station 4i 本機固定全套與 clean-room 驗收通過後由第 3 行取代(見〈五十九〉)。
>
> - 狀態(舊,第五十四代):~~`動工 —— Station 4i 本機固定全套與 clean-room 驗收通過；待 POSIX 外部驗收。`~~
>   —— 2026-10-05 POSIX 外部 clean-room 驗收通過、Jeff 裁決 Station 4i = PASS / COMPLETED 後由第 3 行取代(見〈五十九〉59.3)。
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
| Station 3b — Red-light(補,含補件) | PASS / ACCEPTED |
| Station 4b — Implementation(修正) | PASS / ACCEPTED |
| Station 5b — Review | FAIL |
| Station 3c — Red-light(補) | PASS / ACCEPTED |
| Station 4c — Implementation(修正) | PASS / COMPLETED（待 5c 審查） |
| Station 5c — Review | FAIL |
| Station 3d — Red-light(補) | PASS / ACCEPTED |
| Station 4d — Implementation(修正) | PASS / COMPLETED（待 5d 審查） |
| Station 5d — Review | FAIL |
| Station 3e — Red-light(補) | PASS / ACCEPTED |
| Station 4e — Implementation(修正) | PASS / COMPLETED（待 5e 審查） |
| Station 5e — Review | FAIL(依 Jeff 裁決;審查者原判 PASS) |
| Station 3f — Red-light(補) | PASS / ACCEPTED |
| Station 4f — Implementation(修正) | PASS / COMPLETED（待 5f 審查） |
| Station 5f — Review | PASS |
| Station 6 — Acceptance | FAIL(淨室驗證;依 Jeff 裁決) |
| Station 3g — Red-light(補) | PASS / ACCEPTED(26 behavior-red + 7 regression-lock;S3G2) |
| Station 3g-1b — Red-light(補) | PASS / ACCEPTED(9 behavior-red;S3G1B-2) |
| Station 4g — Implementation(修正) | PASS / COMPLETED（Windows/local acceptance PASS；POSIX clean-room PASS） |
| Station 5g — Review | 審查者 PASS；依 Jeff 裁決 FAIL（S5g-F2） |
| Station 3h — Red-light(補) | PASS / ACCEPTED（H1 behavior-red + H2 regression-lock；S3H2） |
| Station 4h — Implementation(修正) | PASS / COMPLETED（Windows/local acceptance PASS；POSIX clean-room PASS） |
| Station 5h — Review | FAIL（S5h-F1 major；S5h-F2 minor；F3/F4 nit） |
| Station 3i — Red-light(補) | PASS / ACCEPTED（I1 / I2 behavior-red + I3 regression-lock；S3I2） |
| Station 4i — Implementation(修正) | PASS / COMPLETED（Windows/local acceptance PASS；POSIX clean-room PASS） |

Transition：redlight.py 豁免已 drain

Station 3b 補件：PASS / ACCEPTED

Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 4i PASS / COMPLETED（Windows 本機 + POSIX 外部 clean-room）；待 Station 5i 獨立審查(與票頭第 3 行一致)。
(舊的 candidate 語意由票頭的 F-036 區塊保存;本節不是第二份 current status。)

> **舊句(F-036,保留不刪,第四十五代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 4i 本機固定全套與 clean-room 驗收通過；待 POSIX 外部驗收(與票頭第 3 行一致)。~~
> 2026-10-05 POSIX 外部 clean-room 驗收通過、Station 4i = PASS / COMPLETED 後隨第 3 行同步更新(見〈五十九〉59.3)。
> Station 4i 列舊值(F-036,保留不刪):~~`Windows/local acceptance PASS；POSIX clean-room pending`~~;2026-10-05 依〈五十九〉59.3 更新。
>
> **舊句(F-036,保留不刪,第四十四代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 3i 紅燈完成；待 Station 4i 實作(與票頭第 3 行一致)。~~
> 2026-10-05 Station 4i 本機固定全套與 clean-room 驗收通過後隨第 3 行同步更新(見〈五十九〉)。
> Station 3i 列舊值(F-036,保留不刪):~~`紅燈完成（I1 / I2 behavior-red + I3 regression-lock），待 Station 4i`~~;2026-10-05 依 Jeff 裁決(3i = PASS / ACCEPTED)更新。
> Station 4i 列為新增列,沒有舊值(2026-10-05,S4I3)。
>
> **舊句(F-036,保留不刪,第四十三代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 5h 獨立審查 FAIL（S5h-F1 major）；待 Station 3i 紅燈(與票頭第 3 行一致)。~~
> 2026-10-05 Station 3i 紅燈全套驗證成立後隨第 3 行同步更新(見〈五十八〉)。
> Station 3i 列舊值(F-036,保留不刪):~~`NOT STARTED`~~;2026-10-05 依〈五十八〉更新。
>
> **舊句(F-036,保留不刪,第四十二代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 5h 審查包已建立；待獨立審查(與票頭第 3 行一致)。~~
> 2026-10-05 Station 5h 獨立審查 FAIL(S5h-F1 major)後隨第 3 行同步更新(見〈五十七〉)。
> Station 5h 列舊值(F-036,保留不刪):~~`審查包已建立，待審`~~;2026-10-05 依〈五十七〉更新。
> Station 3i 列為新增列,沒有舊值(2026-10-05,S5h-1)。
>
> **舊句(F-036,保留不刪,第四十一代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 4h PASS / COMPLETED（Windows 本機 + POSIX 外部 clean-room）；待 Station 5h 獨立審查(與票頭第 3 行一致)。~~
> 2026-10-05 Station 5h 審查包建立後隨第 3 行同步更新(見〈五十六〉)。
> Station 5h 列為新增列,沒有舊值(2026-10-05,S5h-0)。
>
> **舊句(F-036,保留不刪,第四十代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 4h 本機固定全套與 clean-room 驗收通過；待 POSIX 外部驗收(與票頭第 3 行一致)。~~
> 2026-10-05 POSIX 外部 clean-room 驗收通過、Station 4h = PASS / COMPLETED 後隨第 3 行同步更新(見〈五十五〉55.3)。
> Station 3h 列舊值(F-036,保留不刪):~~`紅燈完成（H1 behavior-red + H2 regression-lock），待 Station 4h`~~;2026-10-05 依 Jeff 前裁(選 A)更新。
> Station 4h 列舊值(F-036,保留不刪):~~`Windows/local acceptance PASS；POSIX clean-room pending`~~;2026-10-05 依〈五十五〉55.3 更新。
>
> **舊句(F-036,保留不刪,第三十九代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 3h 紅燈完成；待 Station 4h 實作(與票頭第 3 行一致)。~~
> 2026-10-05 Station 4h 本機固定全套與 clean-room 驗收通過後隨第 3 行同步更新(見〈五十五〉)。
> Station 4h 列為新增列,沒有舊值(2026-10-05,S4H3)。
>
> **舊句(F-036,保留不刪,第三十八代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 5g 獨立審查（審查者 PASS；依 Jeff 裁決 FAIL：S5g-F2）；待 Station 3h 紅燈(與票頭第 3 行一致)。~~
> 2026-10-04 Station 3h 紅燈全套驗證成立後隨第 3 行同步更新(見〈五十四〉)。
> Station 3h 列舊值(F-036,保留不刪):~~`NOT STARTED`~~;2026-10-04 依〈五十四〉更新。
>
> **舊句(F-036,保留不刪,第三十七代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 5g 審查包已建立；待獨立審查(與票頭第 3 行一致)。~~
> 2026-10-04 Station 5g 獨立審查完成、Jeff 裁決 FAIL(S5g-F2)後隨第 3 行同步更新(見〈五十三〉)。
> Station 5g 列舊值(F-036,保留不刪):~~`審查包已建立，待審`~~;2026-10-04 依〈五十三〉更新。
> Station 3h 列為新增列,沒有舊值(2026-10-04,S5g-1)。
>
> **舊句(F-036,保留不刪,第三十六代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 4g PASS / COMPLETED（Windows 本機 + POSIX 外部 clean-room）；待 Station 5g 獨立審查(與票頭第 3 行一致)。~~
> 2026-10-04 Station 5g 審查包建立後隨第 3 行同步更新(見〈五十二〉)。
> Station 5g 列為新增列,沒有舊值(2026-10-04,S5g-0)。
>
> **舊句(F-036,保留不刪,第三十五代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 4g 本機固定全套與 clean-room 驗收通過;待 POSIX 外部驗收(與票頭第 3 行一致)。~~
> 2026-10-04 POSIX 外部 clean-room 驗收通過、Station 4g = PASS / COMPLETED 後隨第 3 行同步更新(見〈五十一〉51.3)。
>
> **〈十〉表格舊值(F-036)**:Station 4g 列 ~~`Windows/local acceptance PASS;POSIX clean-room pending`~~ → `PASS / COMPLETED（Windows/local acceptance PASS；POSIX clean-room PASS）`(2026-10-04,S4G4)。
> Station 3g-1b 列改為 `PASS / ACCEPTED`(S4G3)經 Jeff 追認(2026-10-04,S4G4 指令)。
>
> **舊句(F-036,保留不刪,第三十四代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 3g-1b 紅燈完成;待 Station 4g 實作(與票頭第 3 行一致)。~~
> 2026-10-04 Station 4g 本機固定全套與 clean-room 驗收通過後隨第 3 行同步更新(見〈五十一〉)。
>
> **〈十〉表格舊值(F-036)**:Station 3g-1b 列 ~~`紅燈完成,待 Station 4g 實作`~~ → `PASS / ACCEPTED(9 behavior-red;S3G1B-2)`(2026-10-04,依〈五十一〉51.1 第 1 點)。
> Station 4g 列為新增列,沒有舊值(2026-10-04,S4G3)。
>
> **舊句(F-036,保留不刪,第三十三代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 3g-1b 紅燈已提交;待固定全套驗證(與票頭第 3 行一致)。~~
> 2026-10-04 Station 3g-1b 固定全套驗證(乾淨工作樹重跑)成立後隨第 3 行同步更新(見〈五十〉50.4)。
>
> **〈十〉表格舊值(F-036)**:Station 3g-1b 列 ~~`紅燈已提交,待固定全套驗證`~~ → `紅燈完成,待 Station 4g 實作`(2026-10-04,S3G1B-2)。
>
> **舊句(F-036,保留不刪,第三十二代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 3g 紅燈已寫(待 Jeff 驗收);Station 4g 未開始(與票頭第 3 行一致)。~~
> 2026-10-04 Station 3g-1b 紅燈提交後隨第 3 行同步更新(見〈五十〉)。
>
> **〈十〉表格舊值(F-036)**:Station 3g 列 ~~`紅燈已寫,待 Jeff 驗收`~~ → `PASS / ACCEPTED(26 behavior-red + 7 regression-lock;S3G2)`(2026-10-04,依〈五十〉50.1 第 1 點)。
> Station 3g-1b 列為新增列,沒有舊值(2026-10-04,S3g-1b)。
>
> **舊句(F-036,保留不刪,第三十一代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 3g 紅燈已提交;待固定全套驗證(與票頭第 3 行一致)。~~
> 2026-10-03 Station 3g 固定全套驗證成立後隨第 3 行同步更新(見〈四十九〉)。
>
> **〈十〉表格舊值(F-036)**:Station 3g 列 ~~`紅燈已提交,待固定全套驗證`~~ → `紅燈已寫,待 Jeff 驗收`(2026-10-03,S3g-2)。
>
> **舊句(F-036,保留不刪,第三十代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 3g 紅燈規劃已寫(待 Jeff 裁);未寫測試(與票頭第 3 行一致)。~~
> 2026-10-03 Station 3g 紅燈提交後隨第 3 行同步更新(見〈四十八〉)。
>
> **〈十〉表格舊值(F-036)**:Station 3g 列 ~~`規劃已寫(待 Jeff 裁),未寫測試`~~ → `紅燈已提交,待固定全套驗證`(2026-10-03,S3g-1)。
>
> **舊句(F-036,保留不刪,第二十九代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 6 FAIL(淨室驗證);待 Station 3g 紅燈規劃(與票頭第 3 行一致)。~~
> 2026-10-03 Station 3g 紅燈規劃寫完後隨第 3 行同步更新(見〈四十七〉)。
>
> **〈十〉表格舊值(F-036)**:Station 3g 列 ~~`待紅燈規劃`~~ → `規劃已寫(待 Jeff 裁),未寫測試`(2026-10-03,S3g-0)。
>
> **舊句(F-036,保留不刪,第二十八代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 5f 獨立審查 PASS;待 push 與 CI 確認(Station 6)(與票頭第 3 行一致)。~~
> 2026-10-03 Station 6 FAIL 後隨第 3 行同步更新(見〈四十六〉)。
>
> **〈十〉表格舊值(F-036)**:Station 6 列 ~~`NOT STARTED`~~ → `FAIL(淨室驗證;依 Jeff 裁決)`(2026-10-03,S6-1)。
> Station 3g 列為新增列,沒有舊值(2026-10-03,S6-1)。
>
> **舊句(F-036,保留不刪,第二十七代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 5f 審查包已建立;待獨立審查(與票頭第 3 行一致)。~~
> 2026-10-03 Station 5f 獨立審查 PASS 後隨第 3 行同步更新(見〈四十五〉)。
>
> **〈十〉表格舊值(F-036)**:Station 5f 列 ~~`審查包已建立，待審`~~ → `PASS`(2026-10-03,S5f-1)。

> **舊句(F-036,保留不刪,第二十六代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 4f 修正完成(Windows 固定全套 exit 0 + POSIX 外部驗證通過);待 Station 5f 審查(與票頭第 3 行一致)。~~
> 2026-10-03 Station 5f 審查包建立後隨第 3 行同步更新(見〈四十四〉)。
>
> **〈十〉表格新增(F-036)**:Station 5f 列為新增列,沒有舊值(2026-10-03,S5f-0)。

> **舊句(F-036,保留不刪,第二十五代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 4f 本機固定全套驗收通過;待 POSIX 跨平台驗收(與票頭第 3 行一致)。~~
> 2026-10-03 POSIX 外部驗證通過後隨第 3 行同步更新(見〈四十三〉43.3)。
>
> **〈十〉表格舊值(F-036)**:Station 4f 列 ~~`Windows acceptance PASS；POSIX pending`~~ → `PASS / COMPLETED（待 5f 審查）`(2026-10-03,S4f-3)。

> **舊句(F-036,保留不刪,第二十四代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 4f 實作已提交;待固定全套驗收(與票頭第 3 行一致)。~~
> 2026-10-03 Station 4f 本機固定全套驗收通過後隨第 3 行同步更新(見〈四十三〉43.2)。
>
> **〈十〉表格舊值(F-036)**:Station 4f 列 ~~`實作已提交，待驗收`~~ → `Windows acceptance PASS；POSIX pending`(2026-10-03,S4f-2)。

> **舊句(F-036,保留不刪,第二十三代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 3f 紅燈已寫(待 Jeff 驗收);Station 4f 未開始(與票頭第 3 行一致)。~~
> 2026-10-03 Station 4f 實作提交後隨第 3 行同步更新(見〈四十三〉)。
>
> **〈十〉表格舊值(F-036)**:Station 3f 列 ~~`紅燈已寫,待 Jeff 驗收`~~ → `PASS / ACCEPTED`(2026-10-03,S4f-1;依 Jeff 的 3f 裁決)。
> Station 4f 列為新增列,沒有舊值(2026-10-03,S4f-1)。

> **舊句(F-036,保留不刪,第二十二代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 3f 紅燈已提交;待固定全套驗證(與票頭第 3 行一致)。~~
> 2026-10-03 Station 3f 固定全套驗證成立後隨第 3 行同步更新(見〈四十二〉)。
>
> **〈十〉表格舊值(F-036)**:Station 3f 列 ~~`紅燈已提交,待固定全套驗證`~~ → `紅燈已寫,待 Jeff 驗收`(2026-10-03,S3f-2)。

> **舊句(F-036,保留不刪,第二十一代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 3f 紅燈規劃已寫(待 Jeff 裁);未寫測試(與票頭第 3 行一致)。~~
> 2026-10-03 Station 3f 紅燈提交後隨第 3 行同步更新(見〈四十一〉)。
>
> **〈十〉表格舊值(F-036)**:Station 3f 列 ~~`規劃已寫(待 Jeff 裁),未寫測試`~~ → `紅燈已提交,待固定全套驗證`(2026-10-03,S3f-1)。

> **舊句(F-036,保留不刪,第二十代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 5e 依 Jeff 裁決 FAIL(S5e-F1;審查者原判 PASS);待 Station 3f 紅燈規劃(與票頭第 3 行一致)。~~
> 2026-10-03 Station 3f 紅燈規劃寫完後隨第 3 行同步更新(見〈四十〉)。
>
> **〈十〉表格新增(F-036)**:Station 3f 列為新增列,沒有舊值(2026-10-03,S3f-0)。

> **舊句(F-036,保留不刪,第十九代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 5e 審查包已建立;待獨立審查(與票頭第 3 行一致)。~~
> 2026-10-03 Station 5e 獨立審查結果與 Jeff 裁決記錄後隨第 3 行同步更新(見〈三十九〉)。
>
> **〈十〉表格舊值(F-036)**:Station 5e 列 ~~`審查包已建立，待審`~~ → `FAIL(依 Jeff 裁決;審查者原判 PASS)`(2026-10-03,S5e-1)。

> **舊句(F-036,保留不刪,第十八代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 4e 修正完成(固定全套 exit 0);待 Station 5e 審查(與票頭第 3 行一致)。~~
> 2026-10-03 Station 5e 審查包建立後隨第 3 行同步更新(見〈三十八〉)。
>
> **〈十〉表格舊值(F-036)**:Station 5e 列 ~~`NOT STARTED`~~ → `審查包已建立，待審`(2026-10-03,S5e-0)。

> **舊句(F-036,保留不刪,第十七代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 4e 實作已提交;待固定全套驗收(與票頭第 3 行一致)。~~
> 2026-10-03 Station 4e 固定全套 exit 0 後隨第 3 行同步更新(見〈三十七〉37.2)。
>
> **〈十〉表格舊值(F-036)**:Station 4e 列 ~~`實作已提交，待驗收`~~ → `PASS / COMPLETED（待 5e 審查）`(2026-10-03,S4e-2)。

> **舊句(F-036,保留不刪,第十六代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 3e 紅燈已寫(待 Jeff 驗收);Station 4e 未開始(與票頭第 3 行一致)。~~
> 2026-10-03 Station 4e 實作提交後隨第 3 行同步更新(見〈三十七〉)。

> **舊句(F-036,保留不刪,第十五代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 3e 紅燈規劃已寫(待 Jeff 裁 P3);未寫測試(與票頭第 3 行一致)。~~
> 2026-10-03 Station 3e 紅燈寫完後隨第 3 行同步更新(見〈三十五〉)。

> **舊句(F-036,保留不刪,第十四代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 5d FAIL(S5d-F1 阻擋);回 Station 3e 規劃與補紅燈(與票頭第 3 行一致)。~~
> 2026-10-03 Station 3e 紅燈規劃寫完後隨第 3 行同步更新(見〈三十四〉)。

> **舊句(F-036,保留不刪,第十三代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 5d 審查包已建立;待獨立審查(與票頭第 3 行一致)。~~
> 2026-10-02 Station 5d 獨立審查 FAIL 後隨第 3 行同步更新(見〈三十三〉)。

> **舊句(F-036,保留不刪,第十二代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 4d 修正完成(固定全套 exit 0);待 Station 5d 審查(與票頭第 3 行一致)。~~
> 2026-10-02 Station 5d 審查包建立後隨第 3 行同步更新(見〈三十二〉)。

> **舊句(F-036,保留不刪,第十一代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 3d 紅燈已寫(待 Jeff 驗收);Station 4d 未開始(與票頭第 3 行一致)。~~
> 2026-10-02 Station 4d 修正完成後隨第 3 行同步更新(見〈三十一〉)。

> **舊句(F-036,保留不刪,第十代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 3d 紅燈規劃已寫(待 Jeff 裁 P3);未寫測試(與票頭第 3 行一致)。~~
> 2026-10-02 Station 3d 紅燈寫完後隨第 3 行同步更新(見〈二十九〉)。

> **舊句(F-036,保留不刪,第九代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 5c FAIL(S5c-F1 阻擋);回 Station 3d 補紅燈(與票頭第 3 行一致)。~~
> 2026-10-02 Station 3d 紅燈規劃寫完後隨第 3 行同步更新(見〈二十八〉)。

> **舊句(F-036,保留不刪,第八代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 5c 審查包已建立;待獨立審查(與票頭第 3 行一致)。~~
> 2026-10-02 Station 5c 獨立審查 FAIL 後隨第 3 行同步更新(見〈二十七〉)。

> **舊句(F-036,保留不刪,第七代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 4c 修正完成(固定全套 exit 0);待 Station 5c 審查(與票頭第 3 行一致)。~~
> 2026-10-02 Station 5c 審查包建立後隨第 3 行同步更新(見〈二十六〉)。

> **舊句(F-036,保留不刪,第六代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 3c 紅燈已寫(待 Jeff 驗收);Station 4c 未開始(與票頭第 3 行一致)。~~
> 2026-10-02 Station 4c 修正完成後隨第 3 行同步更新(見〈二十五〉)。

> **舊句(F-036,保留不刪,第五代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 3c 紅燈規劃已寫(待 Jeff 裁 P3);未寫測試(與票頭第 3 行一致)。~~
> 2026-10-02 Station 3c 紅燈寫完後隨第 3 行同步更新(見〈二十三〉)。

> **舊句(F-036,保留不刪,第四代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 5b FAIL(S5b-F1 阻擋);回 Station 3c 補紅燈(與票頭第 3 行一致)。~~
> 2026-10-02 Station 3c 紅燈規劃寫完後隨第 3 行同步更新(見〈二十二〉)。

> **舊句(F-036,保留不刪,第三代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 4b 修正完成，Station 5b 審查包已建立，待獨立審查(與票頭第 3 行一致)。~~
> 2026-10-02 Station 5b 獨立審查 FAIL 後隨第 3 行同步更新(見〈二十一〉)。

> **舊句(F-036,保留不刪,第二代)**:~~Station 2 = DONE 只表示票已正確建立;票 145 lifecycle = 動工 —— Station 5 FAIL,回 Station 3b 補紅燈,Station 4b 未開始(與票頭第 3 行一致)。~~
> Station 4b 落票時第 3 行已更新而本句未同步(Station 4b 報告「尚未證明」第 4 項);2026-10-02 Station 5b-0 修正。

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

## 十九、Station 4b 修正

### 19.1 coverage 判定依據(`redlight.file_coverage(run, test_file)`)

依序判定,先命中者為準:

| 條件 | 結果 |
|---|---|
| run schema 不合格 | `unknown` |
| 本 run 沒有收集到該檔的任何身分,或該檔有收集錯誤 | `unknown` |
| 該檔有任何 deselected 身分(`-k` / `-m` / `--deselect` / `--lf` 等) | `false` |
| 沒有 invocation 事實、`pyargs` 為真、或 `args` 不是非空 list | `unknown` |
| 某個位置參數是**該檔本身或其上層目錄**(含 `.`)、且不含 `::` | `true` |
| 位置參數只以 nodeid(含 `::`)指名該檔 | `false` |
| 其餘(參數無法判讀 —— 如落在 root 之外 —— 或都與該檔無關) | `unknown` |

**固定指令判為 `"true"`,走通用規則、無特殊分支**:pytest 未給位置參數時以 testpaths 補上 `config.args == ["tests"]`
(〈十八之一〉推導),與「位置參數為上層目錄 `tests`」同一條規則。
本站固定全套留下的真實 session 印證了這個推導:`"invocation": {"args": ["tests"], "args_source": "TESTPATHS", "pyargs": false}`。

位置參數的正規化(`redlight._normalize_arg`):反斜線換成 `/`;相對路徑以 `invocation_params.dir`(無則 root)為基準解析,
再轉成 **root 相對 posix 路徑**;落在 root 之外或跨磁碟 ⇒ `null`(無法判讀)。**絕對路徑與 invocation dir 不落帳。**

### 19.2 D 狀態與 schema fail-closed

- **`redlight.validate_session(run)`** 回傳問題清單(空 = 合格):`run_id` / `time` 為非空字串;`ticket_id`、`exit_code` 欄位存在
  (`exit_code` 為 int 或 null);`collected` / `deselected` 為字串 list 且 `deselected ⊆ collected`;
  `outcomes` 為 `{字串: passed | failed | skipped | other}` 且鍵 ⊆ selected;`invocation` 若存在須為 dict(`args` 為 list 或 null)。
- **`redlight.run_state(run)`**:不合格 ⇒ `"INVALID"`(不是 A–F 任何一個);其餘照原表。
- **`status._apply_run()`**:不合格 run **不產生任何效果**(不加紅、不退紅、不 orphan、不 green);
  `run_state == "D"` ⇒ 整個 run **沒有退紅權、不得使任何檔成為 green**;
  退紅 / orphan / green **只在 `file_coverage == "true"` 時進行**。
- **不合格 run 在 status 上的表示形式**(Evidence 區塊 `test-runs` 行):
  - 計數:`… / orphaned N / schema 不合格 run N;…`
  - 最近一次 run 若不合格:`最近一次 run:INVALID(schema 不合格:<問題清單>)`(不從它計算任何計數)

### 19.3 四個檔的改動(`git diff af839c6 --stat`)

```
 .claude/hooks/redlight.py  | 164 ++++++++++++++++++++++++++++++++++++++++++++-
 .claude/portable/status.py | 122 +++++++++++++++++++++------------
 tests/conftest.py          |  31 ++++++++-
 tests/test_status.py       |   6 +-
 4 files changed, 277 insertions(+), 46 deletions(-)
```

- `.claude/hooks/redlight.py`(+163 / −1):新增 `_normalize_arg`、`_normalize_invocation`、`OUTCOME_VALUES`、`validate_session`、`file_coverage`;
  `record_session` 新增 `invocation` 參數並落帳正規化後的 `invocation`;`run_state` 對不合格 run 回 `INVALID`。
- `.claude/portable/status.py`(+81 / −41):新增 `_RL_FUNCS`、`_rl_ready`、`_invalid_count`;`_apply_run` 依 19.2 重寫並接受 `rl`;
  `ticket_test_state(records, runs, ticket, rl=None)`(`rl` 為 None ⇒ 涵蓋一律未知);`_last_run_text` 顯示 INVALID;
  `_evidence` / `_derived` 傳入 `rl`,`test-runs` 行加 `schema 不合格 run N`。
- `tests/conftest.py`(+29 / −2),逐段:
  1. `pytest_sessionfinish` 尾段:原本直接呼叫 `record_session(_ROOT, …)`,改為先組 `kwargs`(內容不變),
     若 `record_session` 的簽名有 `invocation` 參數(`inspect.signature`)才加上 `invocation=_invocation_of(session)`,再呼叫。舊版 redlight 照舊不傳。
  2. 新增 `_invocation_of(session)`:讀 `session.config` 的 `args`、`args_source.name`、`invocation_params.dir`、`option.pyargs`(屬性一律帶預設值);沒有 config ⇒ None。
  3. 既有 `_outcomes` / `_run` 的蒐集邏輯與其他 hook **未動**。
- `tests/test_status.py`(+4 / −2):見 19.4。

**未修改**:`tests/test_redlight.py`(`git diff af839c6 --stat -- tests/test_redlight.py` 無輸出)、`.claude/hooks/gate.py`、`.agents/`、`pipeline.json`。
Station 3 的 14 支與 3b 的 20 支測試的 assertion、docstring、test identity 未動;僅 19.4 的兩處授權補件。

### 19.4 fixture 補件(〈十七〉裁決 5;assertion 一字未改)

`git diff -U0 tests/test_status.py` 原文:

```
@@ -577 +577,2 @@ class TestTestsUnderTicketUsesTheLatestRecordPerFile:
-            deselected=[], outcomes={u"tests/test_a.py::test_one": u"passed"})
+            deselected=[], outcomes={u"tests/test_a.py::test_one": u"passed"},
+            invocation={u"args": [u"tests"]})
@@ -1329 +1330,2 @@ class TestOrphans:
-                                deselected=[], outcomes={new: u"passed", keep: u"passed"})
+                                deselected=[], outcomes={new: u"passed", keep: u"passed"},
+                                invocation={u"args": [u"tests"]})
```

- 570 / 571:該測試 Station 4 補上的 run 加 `invocation={u"args": [u"tests"]}` ⇒ 該 run 對 `tests/test_a.py` 為整檔涵蓋。
- ODC-2(`test_a_renamed_red_test_is_orphaned_not_green`):run2 加同一參數 ⇒ 整檔涵蓋 ⇒ 有 orphan 判定權。
- 749:直接呼叫未改的 `_latest_per_file()` ⇒ 不需補。
- 兩處改動只在 `record_session(...)` 呼叫的參數列尾端加一個參數(原行的 `)` 移到新行),**無任何 assertion 被改動**。

### 19.5 證據鏈

| 步驟 | 證據 |
|---|---|
| 前置 H0 / L0 | test-runs `b555ded4e2986f819c711c4ef16168c9df25f54cce12fd8064141e9cc7bc2ada` / 613185 / 2273;test-sessions `d97b7631d55ba0b8359803a6b2ffa9c6330de02b8363dc0c769afea6eb38e12e` / 1413031 / 11 |
| S4b-1 commit 前未執行 pytest | commit 前與 commit 後重量兩本帳,SHA-256 / bytes / lines **皆與 H0 / L0 相同** |
| S4b-1 commit | `333e5853bf1a1712bde2aea2d2b488299e3752f6`(`163 1` / `81 41` / `29 2` / `4 2`);pre-commit 未擋 |
| 固定全套(只跑一次,在 `333e585` 上) | exit code **0**;`1946 passed, 3 skipped, 3 xfailed in 147.38s (0:02:27)`;**failed 0** |
| 3b 的 17 支 / L1–L3 / Station 3 的 14 支 | **全部通過**(失敗集合為空;1946 = 1929 + 17) |
| 帳本只追加 | test-runs after 前 613185 bytes 的 SHA-256 = H0;test-sessions after 前 1413031 bytes 的 SHA-256 = H0 |
| 帳本 after | test-runs `73737b7d…a8a93` / 624488 / 2319(+46 = 測試檔數,全 green);test-sessions `42bdc38e…7e35` / 1873333 / 12(+1) |

**status.py**(節錄):

```
test-runs: 本票 red 0 / green 46 / run 事實未知 0 / orphaned 0 / schema 不合格 run 0;最後一筆 tests/test_verify_gates.py=green @ 2026-10-02T17:05:51.724830+00:00;最近一次 run:A(exit 0;collected 1952 / deselected 0 / passed 1946 / failed 0 / skipped 3)
tests red under ticket 145: (無)
tests orphaned under ticket 145: (無)
```

### 19.6 測試三層

| 層 | 狀態 |
|---|---|
| **UNIT** | 固定全套 exit 0,`1946 passed, 3 skipped, 3 xfailed` |
| **CLEAN** | 未證明 |
| **REAL** | 留待 Jeff 端 status_all 確認(本站不宣稱) |

---

## 二十、Station 5b 審查包

| 項 | 值 |
|---|---|
| 審查對象(TARGET) | `851cbd75b359a6b2a34452265e8a70992fa56996` |
| 審查包 | `docs/audits/2026-10-02-m1a-station5b-review-package.md` |
| bytes / 行數(工作複本,LF) | 151293 / 2971 |
| SHA-256(工作複本) | `86a1c73429f4655fdc268c1544bcf0af054df57eb2a36e2f546f38087ba404bf` |
| staged blob ID | `94bd4b6dced526b0433a61ba7423cf58ed792f33` |
| S5b-0 commit | `5c637fd0ac1e7c1f6b89a2061fdb6fcf66207461` |

- 審查包的 A–H 段:身分與規則(審查對象一律寫成 TARGET 完整 SHA)、票 145 合約原文、前次 FAIL 原文(F1–F4)、
  `origin/master..TARGET` commit 清單、兩份完整 diff、Station 4b 證據、必答問題 G1–G11、已知例外與未證明事項。
- 審查包的 `git diff --cached --check` 有 31 行 trailing whitespace,全部是〈E〉內嵌 diff 的空白 context 行(單一空格),屬 diff 原樣,刻意保留。

裁決(2026-10-02,Jeff):
1. **Station 3b 刀③ 的程序違規**(`git diff --check` 有輸出時仍 commit)列為**已知例外**;不改寫歷史。
2. **Station 4b:PASS / ACCEPTED**。

---

## 二十一、Station 5b 獨立審查（FAIL）與 Station 3c 裁決（2026-10-02，Jeff）

### 21.1 審查報告

- 路徑 docs/audits/2026-10-02-m1a-station5b-independent-review-fail.md
- 原始證據：.scratch/m1a-s5b/review-report.md（不進版控），LF，30155 bytes，
  sha256 05951ee66f810e308954f2baa301d8fafb88f431fc9c0f54c9ac166c4c1917fc
- repo 副本：docs/audits/2026-10-02-m1a-station5b-independent-review-fail.md，30156 bytes，
  sha256 bc7d9b67ac0f7d030ed4b0cda78013bbf372f504c3f489874fbcb5a6ed0c1e3f，Git blob 見下一行
- 兩者唯一差異：第 329 行本機使用者資料夾名稱以 `<user>` 遮罩（pre-commit 洩漏偵測擋下，依 F-116 遮罩版不再稱為原始）。
  其餘逐位元組相同。
- Git blob：5caacedbd123e3aa47eb39d8819ef66fedac9e11
- 審查對象 851cbd75b359a6b2a34452265e8a70992fa56996；判決 FAIL；阻擋 1（S5b-F1），非阻擋 5（S5b-F2–F6）

### 21.2 裁決助手外部重現（隔離環境；不是本 repo 的帳本證據；未寫入本 repo 任何檔案）

- 環境：pytest 9.1.1；redlight.py、status.py、tests/conftest.py 取自 TARGET；testpaths = ["tests"]；
  一個測試檔含模組層 test_a、test_b。
- R1 全套（實作不存在）⇒ 收集錯誤 ⇒ 整檔紅。
- R2 全套（test_a 過、test_b 敗）⇒ red = {整檔, test_b}；lastfailed = {test_b}。
- R3 `pytest -q --lf`（test_b 已修、test_a 被改壞）⇒ 只收集並執行 test_b，passed；deselected = []；
  invocation args = ["tests"] ⇒ file_coverage = "true"，run_state = A ⇒ ticket_test_state = green。
- 實際：單獨執行 test_a ⇒ 1 failed。⇒ S5b-F1 在真實執行上成立。
- 附註 1：審查報告推演的 R2（只跑 nodeid）在真實執行中 lastfailed 仍保留整檔鍵、R3 會跑全檔，該條路徑不重現；
  但上面「全套 → --lf」的路徑重現，結論不變。
- 附註 2：即使檔案先前沒有紅，--lf 也會讓「只跑了部分身分」的檔被判 green。問題在 coverage 判定本身，不限整檔紅。
- 附註 3：審查報告 G5 推演 -x / --maxfail 在 TARGET 上未造成假綠（停止點所在檔必有 failure；之後的檔沒有 outcome，不退紅、不 green）。
  下面裁決 2 仍把提前停止納入合約，作為正向事實的一部分；它在 3c 的紅燈屬於 behavior-red 還是 regression-lock，於規劃時逐支判定。

### 21.3 裁決

1. Station 5b FAIL 成立；S5b-F1 為阻擋。依流程回 Station 3c（補紅燈）→ 4c（修正）→ 5c（新的獨立審查）。不推、不回滾、不改寫歷史。
2. 修正方向（合約）—— coverage authority 的正向事實必須涵蓋「選擇完整性 + 執行完整性」：
   full_file_coverage == "true" 除既有條件外，producer 必須正向記錄足以證明本次沒有任何
   「會縮小實際執行集合」或「會提前終止執行」的機制生效。至少盤點並分類：
   - selection / collection narrowing：--lf / --last-failed 等（收集期就過濾、不發 deselected 通知）
   - execution early-stop：-x / --exitfirst、--maxfail、--sw / --stepwise（含 --sw-skip）等
   具體清單、每個機制在 pytest 9.1.1 的實際行為（是否走 pytest_deselected、是否提前停止）與原始碼出處，
   於 Station 3c 規劃時逐項確認並列表。
   任一必要事實缺欄、型別不明、或機制生效 ⇒ 不得給 "true"；依語意給 "false" 或 "unknown"，兩者都沒有退紅權與 orphan 權。
   不得以「沒有 deselected」推論選擇完整或執行完整。
3. Station 3c 紅燈至少要含：
   (a) --lf silent narrowing：收集結果少了身分、沒有 deselected 通知 ⇒ 不退紅、不 green；
   (b) 選擇／執行完整性事實缺欄 ⇒ 不得為 "true"；
   (c) -x / --maxfail 或 --sw：完整收集但部分未執行 ⇒ 不得因 coverage authority 被當成 green 或 orphan-safe；
   (d) regression lock：固定全套指令（narrowing / early-stop 全關）仍判 "true"；
   (e) 21.2 的三步情境（全套 → --lf → status 假綠）以 driver 表達（不在真實帳本執行）。
   3c 規劃時必須逐支標明 behavior-red（現在應該失敗）或 regression-lock（現在就應該通過），
   驗收照舊：預期紅集合 = 實際失敗集合。
4. S5b-F2–F6：非阻擋，本票不修，登記到 M1-a 結案後的追蹤票。
   S5b-F3（固定 skip/xfail 讓整檔紅永遠退不了）需要另裁合約對 applicable 的解讀，在追蹤票處理。
5. 程序事件：審查者曾嘗試寫入 scratchpad，被 R7 擋下；停手詢問後，Jeff 選擇只讀繼續。
   審查前後 HEAD、樹狀態、兩本帳皆未變（裁決助手以 status_all 核對）。照實記錄，不影響審查效力。
6. 結案後追蹤票清單更新為：conftest 不受 R2/R3 管的缺口；session 帳本增長；S5b-F2–F6；上游票 139 少一空行。
7. 洩漏事件：審查報告照錄 R7 擋下訊息時，帶入了本機使用者資料夾名稱（F-082 型）。
   pre-commit 洩漏偵測（權威層）在 S5b-1 commit 時擋下，未進入歷史。
   處置：裁 A，repo 副本遮罩、原檔不動、不豁免偵測。
   Station 5c 審查者提示新增一條：照錄系統訊息前，先遮罩本機路徑中的使用者名稱。

---

## 二十二、Station 3c 紅燈規劃

- 規劃檔:`docs/audits/2026-10-02-m1a-station3c-redlight-plan.md`(只規劃;未寫測試、未執行 pytest;pytest 行為全部由讀 pytest 9.1.1 / pluggy 1.6.0 原始碼推得)。
- P2(d) 結論:對內建 `--lf`,有一個可觀察縮小前全集的時點(conftest 的 trylast `pytest_make_collect_report` wrapper,未實測);對未知第三方 plugin 沒有 ⇒ **無法由 selected / outcomes 單獨證明 selection completeness**,正向證據只能靠 provenance。
- P3 三案(待 Jeff 裁):
  - A 選項清單法 —— 記下會影響完整性的 pytest 選項,任一開著或缺欄 ⇒ 不是 `"true"`;擋不住 `pytest.exit(returncode=0)` 與未知 plugin。
  - B 執行事實法 —— 記下 shouldstop / shouldfail、每個 selected 身分是否都有終局 outcome,可加縮小前全集快照;selection completeness 對未知 plugin 仍須回到 provenance。
  - C A + B 合用,可再加「plugin dist 不在已知清單 ⇒ 不是 `"true"`」;規劃檔的建議是 C。
- 另待裁:六支既有測試(預期 `"true"` / green / orphan)的 fixture 補件授權,見規劃檔 P4。

---

## 二十三、Station 3c 裁決與完整性事實合約（2026-10-02，Jeff）

### 23.1 裁決(照錄)

1. P3 採 C：selection completeness 與 execution completeness 都要有 producer 的正向事實。
2. 裁決助手隔離環境實測（pytest 9.1.1；不是本 repo 帳本證據）：
   (a) conftest 的 hookimpl(wrapper=True, trylast=True) pytest_make_collect_report 在 --lf 時看得到縮小前全集（4 支），session.items 只剩 1 支；
   (b) 測試內 pytest.exit(returncode=0)：exit 0、4 支只跑 2 支、shouldstop 與 shouldfail 皆為 False；
   (c) --sw 停下 exit 2；
   (d) -p no:cacheprovider 時 config.option 沒有 lf、stepwise；
   (e) --lf 真的過濾時 lfplugin-collskip 會註冊；
   (f) 預設 config.option.maxfail 為 None；
   (g) config.pluginmanager.list_name_plugin() 在 sessionfinish 時列出全部已註冊 plugin：
       -p 載入、PYTEST_PLUGINS 載入、任何層級的 conftest 都看得到；
       非頂層 conftest 定義 pytest_plugins 在 pytest 9 是收集錯誤（run 判 D）。
       名稱為數字（id）的項目來自 _pytest 內部物件；conftest 的名稱是絕對路徑。
3. 受支援範圍（supported execution boundary）：full_file_coverage == "true" 只在本次註冊的每一個 plugin 都屬於白名單類別時宣稱：
   (1) builtin：定義模組為 _pytest 或 _pytest.*（模組物件看 __name__；其他物件看其類別或物件的 __module__）；
   (2) root_conftest：root 相對路徑恰為 tests/conftest.py 的 conftest；
   (3) known_dist：該 plugin 物件出現在 pluginmanager.list_plugin_distinfo() 的配對中，且 dist 名稱屬於已知清單 {"anyio"}。
       只看名稱相同不算（名稱可被冒用）。
   其他任何來源（-p、PYTEST_PLUGINS、其他 conftest、未知 dist、無法分類）⇒ kind = "other" ⇒ 不是 "true"（"unknown"）。
   tests/conftest.py 本身是 producer，屬於受審查程式碼，視為信任邊界內；此點明文記錄，不是未知來源。
   白名單定義在 redlight.py，變更須走票。
4. -p no:cacheprovider：pluginmanager.is_blocked("cacheprovider") 為 True，視為 lf / stepwise 不可能作用的正向事實。
5. 授權 4c 只在規劃檔 P4「受影響的既有測試」那六支的 fake / fixture 補上「全部關閉、白名單內」的完整性事實；
   assertion、docstring、test identity 一律不改。
6. anyio 擴增（P1 #20）：Station 4b 固定全套的真實 session 合格（run_state A），目前 repo 沒有觸發它的測試；列入追蹤票。
7. 完整性事實合約（3c 依此寫測試，4c 依此實作；欄位名稱可在本刀定稿，語意不得改）：
   session 新增欄位 completeness（dict），至少含：
   - options：lf、last_failed_no_failures、stepwise、stepwise_skip、maxfail、collectonly、setuponly、setupplan
     （照 config.option 原樣；屬性不存在記為 null）
   - cacheprovider_blocked：bool
   - shouldstop、shouldfail：bool（session 結束時的值）
   - pre_narrowing：{測試檔: [縮小前完整 nodeid 清單]}（trylast wrapper 當下立刻複製）
   - plugins：[{"name": 正規化名稱, "kind": "builtin" | "root_conftest" | "known_dist" | "other"}]
     由 producer 從 list_name_plugin() 與 list_plugin_distinfo() 的原始事實分類產生；
     路徑型名稱只能記 root 相對路徑，root 以外記 "<outside>"；帳本中不得出現任何絕對路徑。
   file_coverage(run, f) == "true" 的新增必要條件（全部成立才行）：
   (i)    completeness 存在且型別正確；缺欄或型別錯 ⇒ "unknown"
   (ii)   lf 與 stepwise 都為 False，或 cacheprovider_blocked 為 True
   (iii)  maxfail 為 None 或 0；collectonly、setuponly、setupplan 皆為 False
   (iv)   shouldstop、shouldfail 皆為 False
   (v)    pre_narrowing 有 f，且它的集合 == 本 run 中 f 的 collected 身分集合（selected + deselected）；不相等 ⇒ "false"
   (vi)   f 的每一個 selected 身分都達到「執行完成」終態：
          只承認 call phase 的 passed / failed、skip（任何 phase）、明確辨識的 xfail / xpass。
          沒有 call、只有 setup、被中止、無法辨識、或籠統的 other ⇒ 不算執行完成 ⇒ 不是 "true"。
          4c 須讓 outcome 能區分 xfail / xpass，不得讓 other 自動取得 completeness。
   (vii)  plugins 每一項的 kind 都不是 "other"
   不得以「沒有 deselected」推論完整；不得以「有一筆 report」推論已執行；不得以「名稱相同」推論 known_dist。
8. 鏈條要求：完整性事實的每一段（raw pytest 事實 → producer 分類與記錄 → 持久化 session → file_coverage → 退紅 / green / orphan）
   都要有測試鎖住；不得只測 consumer 收到預先分類好的資料。

### 23.2 預期集合(照錄;完整 nodeid)

預期紅集合(behavior-red,16 支,在 d122df4 上必須失敗):

- tests/test_redlight.py::TestCompletenessCoverage::test_c3a_lf_silent_narrowing_is_not_full_coverage
- tests/test_status.py::TestSilentNarrowingChain::test_c3a_lf_narrowing_does_not_retire_an_unidentified_red
- tests/test_status.py::TestSilentNarrowingChain::test_c3a_lf_narrowing_does_not_make_a_clean_file_green
- tests/test_redlight.py::TestCompletenessCoverage::test_c3b_a_session_without_completeness_facts_is_not_full_coverage
- tests/test_redlight.py::TestCompletenessCoverage::test_c3b_a_malformed_completeness_fact_is_not_full_coverage
- tests/test_redlight.py::TestCompletenessCoverage::test_c3c_an_exitfirst_run_is_not_full_coverage
- tests/test_status.py::TestEarlyStopChain::test_c3c_exitfirst_does_not_orphan_a_known_red
- tests/test_status.py::TestEarlyStopChain::test_c3c_pytest_exit_zero_partial_file_is_not_green
- tests/test_status.py::TestLfFalseGreenChain::test_c3e_full_then_lf_does_not_produce_a_false_green
- tests/test_redlight.py::TestCompletenessCoverage::test_c3p_an_unknown_plugin_dist_means_not_full_coverage
- tests/test_redlight.py::TestCompletenessCoverage::test_c3p_a_plugin_loaded_by_name_means_not_full_coverage
- tests/test_redlight.py::TestCompletenessCoverage::test_c3p_an_extra_conftest_means_not_full_coverage
- tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_an_unknown_dist_plugin_as_other
- tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_a_plugin_loaded_by_name_as_other
- tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_an_extra_conftest_as_other_and_the_root_conftest_as_root_conftest
- tests/test_status.py::TestPluginProducerChain::test_c3p_producer_classifies_builtin_root_conftest_and_known_dist_as_not_other

預期綠集合(regression-lock,5 支,在 d122df4 上必須通過):

- tests/test_status.py::TestEarlyStopChain::test_c3c_exitfirst_does_not_make_unrun_files_green
- tests/test_status.py::TestEarlyStopChain::test_c3c_stepwise_stop_is_d_and_retires_nothing
- tests/test_redlight.py::TestCompletenessCoverage::test_c3d_the_fixed_command_with_everything_off_is_full_coverage
- tests/test_status.py::TestCompletenessLocks::test_c3d_the_fixed_command_full_run_still_retires_the_red
- tests/test_status.py::TestEarlyStopChain::test_setup_only_run_is_not_green

### 23.3 本刀定稿的介面細節(不是裁決原文;語意依 23.1 第 7 點)

- `completeness` 的鍵名照 23.1 第 7 點原樣定稿:`options`、`cacheprovider_blocked`、`shouldstop`、`shouldfail`、`pre_narrowing`、`plugins`;
  `options` 內的鍵名與 `config.option` 屬性同名;`plugins` 每項為 `{"name", "kind"}`,路徑型名稱記 root 相對 posix 路徑(例:`tests/sub/conftest.py`)。
- 3c 的 driver 以 new-style 協定(`wrapper=True`,23.1 第 2 點 (a))呼叫 conftest 的 `pytest_make_collect_report`:
  先送出完整結果,wrapper 返回後才**就地**縮小 `report.result`;假 item / collector 是 `pytest.Item` / `pytest.File` 的子類。
  4c 的 producer 須在 wrapper 當下複製 nodeid,並以 `pytest.Item` 判斷 item(或等價方式)。
- 明確辨識的 xfail 在 driver 中表達為:call report `outcome == "skipped"` 且帶 `wasxfail`。

---

## 二十四、Station 3c 紅燈證據

- 報告:`docs/audits/2026-10-02-m1a-station3c-redlight.md`。
- S3c-1 `175da887f404fe0e1029de8bb2e438ab62f4aebb`:兩個測試檔各恰好一個檔尾 hunk(`@@ -632,0 +633,409 @@`、`@@ -1755,0 +1756,514 @@`),沒有刪除行。
- 第一次驗收(S3c-1 上):`15 failed, 1952 passed, 3 skipped, 3 xfailed`。偏差:C3e-1 意外通過,依程序停手。
- **3c-1b 裁決(Jeff)**:判定為 test-driver defect,不是產品碼問題。C3e-1 以同一個 conftest 模組連續驅動 R1–R3,狀態殘留使 R3 的 session 判 INVALID ⇒ 不退紅 ⇒ 因錯誤的理由通過。
  只修這一支:R1 / R2 / R3 各自用新的 `_chain_conftest()`,加情境斷言 R1 = D、R2 = B、R3 = A 且 schema 合格;red / green 斷言不變。授權在修正後的乾淨 HEAD 上再跑一次。
- S3c-1b `49bcde20adc276632fa5bab456e8c7a80839fc0b`:三個 hunk 都在該函式範圍內(修改前 2137–2154 / 修改後 2137–2164)。
- 第二次驗收(S3c-1b 上):16 支 behavior-red 全部失敗,5 支 regression-lock 與其他既有測試全部通過。
  **摘要行原文因 tool 輸出截斷而遺失**(裁決:照寫並標明)。失敗集合由 pytest 的 `lastfailed` 快取與帳本兩個獨立來源證明;status.py 為 `最近一次 run:B(exit 1;collected 1973 / deselected 0 / passed 1951 / failed 16 / skipped 3)`,red 只有 `tests/test_redlight.py`、`tests/test_status.py`。
- 帳本 H0 → H1 → H2:test-runs 624488 → 637099 → 649789 bytes(2319 → 2365 → 2411 行),test-sessions 1873333 → 2338347 → 2803361 bytes(12 → 13 → 14 行);兩段前段 sha256 都與前一點相同 ⇒ 只追加。
  H0 為 VS 當時記錄,H0 / H1 都與裁決助手獨立量測相同。

---

## 二十五、Station 4c 修正與裁決

- 報告:`docs/audits/2026-10-02-m1a-station4c-fix.md`。
- S4c-1 `02a5e28adf5aee11a43d5a1063504f01beb1d67f`;固定全套(只跑一次)`1967 passed, 3 skipped, 3 xfailed`,exit 0。

裁決(2026-10-02,Jeff;照錄):

1. 完成條件 (c)「不得有絕對路徑」的適用範圍，依欄位性質分三類：
   (1) producer 為了自身正規化、分類而產生的 path-valued metadata（例如 completeness.plugins[].name）：
       不得產生或洩漏絕對路徑。
   (2) pytest 提供、作為 identity 必須逐字保存的 opaque facts（nodeid；collected、outcomes、pre_narrowing 中的身分）：
       不因本條改寫；pre_narrowing 與 collected 的比對需要逐字相等。
   (3) invocation.args：依〈十九〉Station 4b 已驗收的正規化規則處理（root 相對路徑；root 以外不落帳），
       屬既定且可重現的正規化，不屬本條，也不是任意改寫。
   若 (2) 類原始事實本身帶有本機敏感路徑，屬另一個 privacy / provenance 問題，列入 M1-a 結案後追蹤票。
   裁決助手獨立核對真實 session（第 15 行）：類似絕對路徑的字串只出現在 collected、outcomes 的鍵、
   completeness.pre_narrowing 三處，共 29 個身分，且 pre_narrowing 中的這些身分全部也在 collected 中；
   plugins 與 invocation 不含；整行不含本機使用者名稱。本次固定指令的 invocation.args 為相對的 tests。
   ⇒ (c) 判定成立。〈二十三〉7 plugins 條目末句「帳本中不得出現任何絕對路徑」以本條澄清範圍（原文依 F-036 不改）。
2. 接受實作偏離：pre_narrowing 記錄每個 collector report 中的 pytest.Item（File 的直接子項，以及 Class 等子 collector 的子項），
   以測試檔為 key、完整身分集合為 value。理由：class 內的測試不在 File 的 report 裡；--lf 只在 File 層過濾
   （_pytest/cacheprovider.py:282-290），子 collector 不受影響。真實固定全套 46 檔全部以同一套一般規則判 "true" 為佐證。
   Station 5c 必答題（審查包須列入）：多層 collector 累積是否會因重複、巢狀 class、parametrize、hook 順序而漏記或錯記；
   --lf 的 File 層縮小是否確實發生在本 snapshot 之後，沒有形成新的 false-positive coverage 路徑。
3. 裁決助手獨立核對：帳本 H2 前段雜湊相符（36bf61df… / 0ef187e0…）；真實 session 的 46 檔 file_coverage 全為 "true"；
   plugins 43 項（builtin 41、known_dist 1、root_conftest 1），無 other。
4. Station 4c implementation = PASS / COMPLETED，待 Station 5c 獨立審查。四項完成判定：(a)(b)(c)(d) 皆成立。

---

## 二十六、Station 5c 審查包

| 項 | 值 |
|---|---|
| 審查對象(Implementation TARGET) | `02a5e28adf5aee11a43d5a1063504f01beb1d67f` |
| S4c-2 docs commit | `a88b7f9664189f9b3f3124aa39eb3a95eaca51b1` |
| S3c-1b | `49bcde20adc276632fa5bab456e8c7a80839fc0b` |
| 審查包 | `docs/audits/2026-10-02-m1a-station5c-review-package.md` |
| bytes / 行數(工作複本,LF) | 298249 / 5623 |
| SHA-256(工作複本) | `1212a03951779967449bd637549860fee7acf22be9de40421e652817164a3db3` |
| staged blob ID | `d37e0538798ae763d86716542becf3430d7a73c5` |
| S5c-0 commit | `587c1ed63a07d90dc33f3e247f4d1ebed01c91bf` |

- 審查包的 A–H 段:身分與規則(所有查詢錨點一律為完整 SHA)、票 145 規格原文(〈十三〉ODC-1、〈十七〉、〈十八之一〉18-1.1、〈十九〉、〈二十一〉、〈二十三〉、〈二十五〉)、
  Station 5(F1–F4)與 Station 5b(S5b-F1–F6)的發現原文、`origin/master..TARGET` commit 清單、三份完整 diff、3c / 4c 實測證據、必答題 G1–G12、已知例外與未證明事項。
- 〈E〉三份 diff 與全部 14 段逐字段落,都已在建包時以 `cmp` 與原始輸出 / 出處檔案逐位元組比對相同。
- 審查包的 `git diff --cached --check` 有 39 行 trailing whitespace,全部是〈E〉內嵌 diff 的空白 context 行(單一空格),屬 diff 原樣,刻意保留。

---

## 二十七、Station 5c 獨立審查（FAIL）與 Station 3d 裁決（2026-10-02，Jeff）

### 27.1 審查報告

- 路徑 docs/audits/2026-10-02-m1a-station5c-independent-review-fail.md；raw = normalized（LF），sha256 33f8ef6006b672eab3019a426bfc4a787e90d2b92ae1530ae18a6be9e788eccc
- 審查對象 02a5e28adf5aee11a43d5a1063504f01beb1d67f；判決 FAIL（valid independent review）；阻擋 1（S5c-F1），非阻擋 3（S5c-F2–F4）
- 報告內的本機路徑已由審查者遮罩為 <user>。

### 27.2 裁決助手外部重現（隔離環境；不是本 repo 的帳本證據；未寫入本 repo 任何檔案）

- 環境：pytest 9.1.1；redlight.py、status.py、tests/conftest.py 取自 TARGET 02a5e28；testpaths = ["tests"]；未安裝第三方 pytest 外掛。
- R1 全套（實作不存在）⇒ D，整檔紅。R2 全套（test_a 過、test_b 敗）⇒ B，coverage "true"。
- R3 `pytest -q -o python_functions=test_b`（test_b 已修、test_a 被改壞）⇒ 只收集 test_b，passed；
  pre_narrowing 只有 test_b；run_state A；file_coverage "true" ⇒ ticket_test_state = green。
- 實際：完整執行該檔 ⇒ 1 failed, 1 passed。⇒ S5c-F1 在真實執行上成立。
- 附帶觀察（裁決助手，非審查者發現，記為 S5c-X1）：`-p no:<name>` 會在 list_name_plugin() 留下該名稱（物件為 None），
  被分類為 other ⇒ coverage "unknown"。因此〈二十三〉裁決 4（cacheprovider_blocked 視為正向事實）實際上不會生效；
  方向為 fail-closed，不危險。同理 `-p no:unittest` 已被擋。

### 27.3 裁決

1. Station 5c FAIL 成立；S5c-F1 為阻擋。審查報告的反方論點（設定定義測試集合）不採納，理由：
   M1-a 的 coverage authority 已選定「repo 所提交的 collection definition」為完整性的基準。
   單次 invocation 透過 -o / --override-ini 等管道改變 python_functions 等 discovery 規則，等於改變本次的 execution universe，
   卻沒有留下 deselection evidence，因此不能沿用 repo baseline 的 whole-file authority。
   （這不是主張 -o 與 -k 是同一種機制；兩者發生在 pytest 不同層次，只是對 completeness 的效果相同。）
   依流程回 Station 3d（規劃 + 紅燈）→ 4d（修正）→ 5d（新的獨立審查）。不推、不回滾、不改寫歷史。
2. 修正方向（合約）：completeness 必須正向證明「本次 effective collection definition = repo 所提交的 collection definition」。
   Station 3d-0 規劃時先查清楚，再定合約，不預設修法：
   - pytest 9.1.1 能否告訴 producer 哪些 ini key 被 -o 覆寫；effective ini 值能否與 repo baseline 可靠比較；
   - PYTEST_ADDOPTS 注入的覆寫能否被同一機制看到；CLI、環境、ini 的合併順序；
   - 若只看得到最後值、看不到來源，能否仍證明「等於 repo 定義」；
   - -c / --config-file：指向 repo 內已提交的權威設定時是否仍可接受，或一律 fail-closed（若 provenance 成本不值得，可選後者）；
   - 其他會改變「哪些東西算測試」的輸入（python_files、python_classes、python_functions、norecursedirs、collect_ignore、
     --rootdir、--confcutdir、--import-mode、--doctest-modules 等）逐項盤點行為與出處，分類為「會縮小」「只會擴增」「不影響」。
   據此決定 4d 是「禁止所有覆寫管道」還是「比較 effective collection definition」。缺欄或無法判定 ⇒ 不得為 "true"。
3. S5c-F2（三條條件沒有單獨的測試鎖住）：納入 Station 3d，以 regression-lock 補上逐條隔離測試。
4. S5c-X1：納入 Station 3d 的合約整理。傾向把合約簡化為「任何明確的 plugin 停用（-p no:<name>）⇒ 不取得 full coverage authority」，
   取代〈二十三〉裁決 4 的 cacheprovider_blocked 特判；正式裁定前，先由 3d-0 查清 pytest 9.1.1 對被停用 plugin 的實際表示方式。
5. S5c-F3、S5c-F4：非阻擋，登記到 M1-a 結案後的追蹤票。
6. 程序事件：審查者兩次被 R7 擋下，停手詢問後 Jeff 選擇只讀繼續；一次以短 SHA 查規劃 commit、一次讀到工作樹 pyproject.toml，
   事後皆以 TARGET 完整 SHA 重讀，報告引用重讀結果。照實記錄，不影響審查效力。
7. 結案後追蹤票清單更新為：conftest 不受 R2/R3 管的缺口；session 帳本增長；S5b-F2–F6；S5c-F3、S5c-F4；
   測試身分 parametrize ID 帶本機 repo 路徑；上游票 139 少一空行。

---

## 二十八、Station 3d 紅燈規劃

- 規劃檔:`docs/audits/2026-10-02-m1a-station3d-redlight-plan.md`(依〈二十七〉27.3 裁決 1–4;只讀原始碼推得,未執行 pytest)。
- **P2(a)**:CLI、PYTEST_ADDOPTS、ini addopts 帶入的 `-o` 全部落在同一個 `config.option.override_ini`;`invocation_params.args` 不含後兩者。已提交的 `--strict-markers` 本身就會產生 `strict_markers=true` ⇒ 固定全套的 `override_ini` 不是空的。
- **P2(b)**:`config.getini` 回傳的是工作樹設定加上 override 的有效值;執行層唯一能正向證明「設定內容 = 已提交版本」的,是「`inipath` 為 `pyproject.toml`,且其 blob 雜湊 = `HEAD:pyproject.toml`」。整棵工作樹乾淨的要求不可行(紅綠燈迴圈本來就在 commit 前跑測試)。
- **P2(d)**:`-p no:<name>` 在 `list_name_plugin()` 留下 `(name, None)`;TARGET 把它判為 other,而且 (vii) 在 `cacheprovider_blocked` 之前判定 ⇒〈二十三〉裁決 4 的特判在得 `"true"` 的路徑上走不到(S5c-X1 成立;S5c-F3 的路徑也因此被擋)。
- **P3 三案**(待 Jeff 裁):
  - **A 禁止覆寫管道**:必須比對「已提交 addopts 推得的 override 清單」,照字面寫成「非空 ⇒ 不是 true」會讓固定全套永遠拿不到 true;不加雜湊就擋不住工作樹改過的 pyproject。對管道清單以外的輸入**不是 fail-closed**(殘餘)。
  - **B 比較有效值**:對清單內的 key 有效;清單外的 key **不是 fail-closed**(殘餘)。
  - **C(A + 設定檔雜湊)**:ini 設定那一面 fail-closed;非 ini 的 CLI 選項那一面仍是否定清單(殘餘)。
  - 規劃建議 C,另建議以「任何 `-p no:` ⇒ 不是 true」取代 `cacheprovider_blocked` 特判。

---

## 二十九、Station 3d 裁決與收集定義合約（2026-10-02，Jeff）

### 29.1 裁決(照錄)

1. 裁決助手在隔離環境以 pytest 9.1.1 實測（不是本 repo 帳本證據），規劃檔 P2 的五項推論全部成立：
   (a) 固定全套（pyproject addopts = "-ra --strict-markers"）的 config.option.override_ini == ["strict_markers=true"]；
   (b) CLI 的 -o 與 PYTEST_ADDOPTS 帶入的 -o 都附加到 config.option.override_ini；
   (c) config.invocation_params.args 不含 PYTEST_ADDOPTS 的內容；
   (d) -p no:cacheprovider 時 list_name_plugin() 出現 cacheprovider、pytest_cacheprovider、stepwise、pytest_stepwise 四筆值為 None 的項目；
   (e) repo 根多一份 pytest.ini 時，沒有任何 -o，config.inipath 改指向 pytest.ini，python_functions 跟著改變。
2. P3 採 C（管道檢查 + 設定檔雜湊比對）。full_file_coverage == "true" 的新增必要條件（全部成立才行）：
   (vii′)  修訂〈二十三〉3 (3)：known_dist 改為「plugin 物件出現在 list_plugin_distinfo() 的配對中，且 (dist 名稱, 精確版本) 屬於已盤點清單」。
           已盤點清單以常數定義在 redlight.py，目前為 {("anyio", "4.15.0")}；變更須走票。
           版本缺失、讀不到、或名稱相同但版本不同 ⇒ kind = "other" ⇒ 不得為 "true"。
   (viii)  config.option.override_ini 恰等於「已提交 addopts 帶來的 override 清單」；
           該清單以常數定義在 redlight.py（目前為 ["strict_markers=true"]），並由一支鎖步測試對照已提交的 pyproject.toml addopts；變更須走票。
   (ix)    config.option.inifilename 為 None（-c / --config-file 一律 fail-closed，即使指向已提交的權威檔）。
   (x)     config.inipath 的 root 相對路徑 == "pyproject.toml"。
   (xi)    pyproject.toml 工作樹內容（套用 .gitattributes 的 eol 正規化）的 blob 雜湊 == HEAD:pyproject.toml 的 blob；
           tests/conftest.py 同樣比對（root conftest 是 producer 本身，工作樹被改即不給 "true"）。
           git 不可用、出錯或任何一項取不到 ⇒ 缺欄 ⇒ 不得為 "true"。
   (xii)   list_name_plugin() 中沒有任何值為 None 的項目（任何 -p no:<name> ⇒ 不得為 "true"）。
           取代〈二十三〉裁決 4：cacheprovider_blocked 不再具有任何判定權（欄位可保留為紀錄）。
   (xiii)  pytest 版本屬於已盤點清單，目前為 {"9.1.1"}，以常數定義在 redlight.py；版本不在清單 ⇒ 不得為 "true"。
           理由：P1 的盤點只對 pytest 9.1.1 成立；非 ini 的 CLI 選項是否會做檔內縮小，換版後必須重新盤點。
           這把「未知或不可觀察的 discovery 輸入」的預設權限定為 fail-closed。升級 pytest 須走票重做盤點。
   版本邊界總表：pytest 內建 ⇒ 鎖 pytest 版本；root producer ⇒ 鎖 tests/conftest.py 已提交 blob；
   repo 收集設定 ⇒ 鎖 pyproject.toml 已提交 blob；已知第三方 plugin ⇒ 鎖 dist 名稱 + 精確版本；未知 plugin ⇒ fail-closed。
   producer 讀 config.option.* 的解析後值，不得掃 argv 字串。
   隱私：新落帳的事實不得含絕對路徑；inipath 記 root 相對路徑；override_ini 只記解析後清單，若含路徑值須依〈十九〉規則正規化或只記 key。
3. 已知殘餘（照實記錄）：
   - TOCTOU：執行中途改設定再改回，雜湊比對看不到。
   - 雜湊比對以 HEAD 為準：已 stage 未 commit 的設定改動也判不等（fail-closed）；只改註解也判不等（fail-closed 的代價）。
   - 改了 pyproject.toml 或 tests/conftest.py 而尚未提交的期間，沒有任何 run 能退紅。
   - 升級 pytest 或 anyio 後，在走票更新清單之前，沒有任何 run 能退紅。
   - known plugin contract 鎖 anyio 4.15.0、pytest 版本清單為 9.1.1，但目前 dependency resolution 是否結構性鎖定這兩個版本
     尚未保證（證據：`02a5e28adf5aee11a43d5a1063504f01beb1d67f:pyproject.toml:34` 為 `"pytest>=8.0,<10"`(範圍,非精確);
     anyio 在 pyproject.toml 中完全沒有宣告(間接相依);
     `02a5e28adf5aee11a43d5a1063504f01beb1d67f:.github/workflows/tests.yml:50` 以 `python -m pip install -e ".[dev]"` 在執行當下解析;
     TARGET 樹中沒有 requirements*.txt、*.lock、constraints*.txt);CI 或新環境若取得其他版本，coverage 會 fail-closed（不會假綠，但無法退紅）。
     4d / 5d 前須決定是否另行 pin。(本條依 3d-1 補充裁決,由第 0 步只讀查證的結果填入。)
4. 授權 4d 只在規劃檔 P4「4d 後會受新合約影響的既有測試」那 9 支的 fake / fixture 補上「已提交設定、沒有額外 override、沒有 -c、
   沒有 -p no:、pytest 9.1.1、anyio 4.15.0」的事實（含在 tmp root 建 git repo 並提交 pyproject.toml 與 tests/conftest.py）；
   assertion、docstring、test identity 一律不改。C3p-6 的隱私斷言不屬可授權修改範圍。
5. 鏈條要求（延續〈二十三〉8 與 3c 的教訓）：本輪所有 behavior-red 情境，都必須經由真實的 tests/conftest.py producer 產生事實，
   再到 file_coverage / status；不得直接把預先做好的 completeness dict 餵給 consumer。
   涉及設定檔內容雜湊的情境，必須在 tmp root 建立真的 git repo 並提交檔案；不得以假雜湊值代替。
   fake pluginmanager 的 list_name_plugin() 必須照 pluggy 實際表示方式包含 (name, None) 項目，且與 is_blocked() 一致；
   list_plugin_distinfo() 的 dist 物件必須帶名稱與版本。
   每次模擬執行用全新的 conftest（沿用 3c-1b）。

### 29.2 預期集合(完整 nodeid)

預期紅集合(behavior-red,13 支,在 9d1446a 上必須失敗):

- tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3a_an_override_ini_narrowing_is_not_full_coverage
- tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3b_an_override_from_pytest_addopts_is_not_full_coverage
- tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3c_a_config_file_option_is_not_full_coverage
- tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3c_a_config_file_option_naming_the_committed_config
- tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3w_an_unexpected_config_file_is_not_full_coverage
- tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3w_an_uncommitted_config_change_is_not_full_coverage
- tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3w_a_non_collection_edit_to_the_config_file
- tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3w_an_uncommitted_root_conftest_change_is_not_full_coverage
- tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3v_an_unrecognized_pytest_version_is_not_full_coverage
- tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3v_a_known_plugin_with_unrecognized_version_is_not_full_coverage
- tests/test_status.py::TestOverrideIniChain::test_d3a_full_then_override_ini_does_not_produce_a_false_green
- tests/test_status.py::TestOverrideIniChain::test_d3a_override_ini_does_not_orphan_a_known_red
- tests/test_status.py::TestOverrideIniChain::test_d3a_override_ini_does_not_make_a_clean_file_green

預期綠集合(regression-lock,6 支,在 9d1446a 上必須通過):

- tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3i_lf_alone_is_not_full_coverage
- tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3i_maxfail_alone_is_not_full_coverage
- tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3i_shouldfail_alone_is_not_full_coverage
- tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3x_a_blocked_plugin_is_not_full_coverage
- tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d3d_the_fixed_command_with_the_committed_config_is_full_coverage
- tests/test_status.py::TestCollectionDefinitionLocks::test_d3d_the_fixed_command_full_run_still_retires_the_red

### 29.3 本刀定稿的介面細節(不是裁決原文;語意依 29.1 第 2 點)

- pytest 版本事實取自 conftest 所 import 的 `pytest` 模組的 `__version__`(D3v-1 以 monkeypatch 改它)。
- 設定檔雜湊以 producer 的 `_ROOT` 為 repo 根(測試中為 tmp root,tmp root 是真的 git repo)。
- 被 `collect()` 之內縮掉的身分,在 driver 中表達為「從一開始就不在 collect report 裡」(不經收集後移除)。

---

## 三十、Station 3d 紅燈證據

- 報告:`docs/audits/2026-10-02-m1a-station3d-redlight.md`。
- S3d-1 `33b8bb4ba6e5601c011d6a50eda9504610c69665`:兩個測試檔各一個接在檔尾的 hunk(`@@ -1063,0 +1064,415 @@`、`@@ -2298,0 +2299,245 @@`),沒有刪除行;commit 前只跑 py_compile。
- 固定全套(只跑一次,在 S3d-1 上):`13 failed, 1973 passed, 3 skipped, 3 xfailed in 147.44s (0:02:27)`,exit 1;失敗集合恰為〈二十九〉29.2 的 13 支;6 支 regression-lock 與 P4 那 9 支既有測試全部通過。
- 帳本 H3 → H4 只追加:test-runs 661092 → 673590 bytes(2457 → 2503 行,+46)、test-sessions 3494564 → 4192482 bytes(15 → 16 行,+1);兩本前段 sha256 等於 H3(`352e7d26…` / `b48ee090…`)。
- status:red 只有 tests/test_redlight.py、tests/test_status.py;最近一次 run 為 B(collected 1992)。
- 版本固定查證:pytest 只有範圍(`pyproject.toml:34`),anyio 沒有宣告,CI 在執行當下解析(`.github/workflows/tests.yml:50`)⇒ 已記入〈二十九〉第 3 點的已知殘餘。

---

## 三十一、Station 4d 修正與裁決

裁決(2026-10-02,Jeff;照錄):

1. Station 3d 紅燈 = PASS / ACCEPTED（以 Jeff 切換 pipeline 為驗收）。
2. pytest / anyio 版本不在本票 pin：agent-gates 為公開 repo，修改 dependency 會影響所有安裝者；anyio 為間接相依，精確 pin 易與上游衝突。
   維持 fail-closed（換環境只會無法退紅，不會假綠），列入 M1-a 結案後追蹤票（supply / dependency policy）。
3. 例外授權：〈二十九〉2 (viii) 要求的「override 常數 vs 已提交 pyproject.toml addopts」鎖步測試，在 3d 時常數尚不存在而無法撰寫；
   授權 4d 新增恰好這一支（接在 tests/test_redlight.py 檔尾），名稱：
   tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d4_the_committed_addopts_override_constant_matches_pyproject
   規格（不得變更）：
   - 讀取來源固定為 agent-gates repo 的已提交版本：以 git show HEAD:pyproject.toml（在 repo 根執行，唯讀）取得內容；
     不得讀工作樹檔案，不得以測試自造的 tmp repo 或寫死的 addopts 字串代替。
     理由：這支測試要鎖的是「redlight.py 常數 ↔ repo 真正提交的設定」；用自造設定只會驗到測試自己，失去鎖步作用。
   - 從該內容的 [tool.pytest.ini_options] addopts 推導應有的 override 清單，與 redlight.py 的常數比較。
     推導方式須在報告中說明（例如明列 addopts 旗標 → override 項目的對應），並附 pytest 9.1.1 出處。
   - git 不可用或讀取失敗 ⇒ 測試失敗（不得 skip、不得靜默通過）。
   - 唯讀：不得寫入任何檔案、不得改動 repo 狀態。

適用位置已由〈四十八〉48.1 第 4 點修訂(語意不變)。

- 報告:`docs/audits/2026-10-02-m1a-station4d-fix.md`。
- S4d-1 `889fbd8f666ea522ff6af172979a8d020e50b86b`;固定全套(只跑一次)`1987 passed, 3 skipped, 3 xfailed in 149.54s (0:02:29)`,exit 0(collected 1993 = 1992 + 1 支鎖步測試)。
- 四項完成判定:
  - (a) 固定全套 exit 0、failed 0 —— **成立**。
  - (b) 3d 的 13 支全部轉綠 —— **成立**(失敗清單為空;status red (無))。
  - (c) 真實 session(`.dev/test-sessions.jsonl` 第 17 行)新事實全部合格 —— **成立**:
    `override_ini == ["strict_markers=true"]`、`inifilename` null、`inipath` "pyproject.toml"、
    pyproject.toml / tests/conftest.py 的 worktree blob = head blob、`pytest_version` "9.1.1"、
    anyio 4.15.0 為 known_dist、None 項目 0、other 0;producer 自行產生的欄位無絕對路徑;全帳本本機使用者名稱 0 筆。
  - (d) 帳本 H4 → H5 只追加 —— **成立**(兩本前段 sha256 = H4)。

---

## 三十二、Station 5d 審查包

| 項 | 值 |
|---|---|
| 審查對象(Implementation TARGET) | `889fbd8f666ea522ff6af172979a8d020e50b86b` |
| S4d-2 docs commit(S4D2) | `6bc15df88d54bbb6761310de5b8e86c400c4b2a7` |
| Station 3d 最後 commit(S3D2) | `5262828ab7f8fb89bb6bb85a6f63e24fdf852532` |
| 審查包 | `docs/audits/2026-10-02-m1a-station5d-review-package.md` |
| bytes / 行數(工作複本,LF) | 382481 / 6821 |
| SHA-256(工作複本) | `c3f0a6070265b17e7b626fc894bbfb470ef0d66e5a5ee1837c5ee1584ec0d575` |
| staged blob ID | `8ea2d705057abcae7c7f5932837e92b991d42c99` |
| S5d-0 commit | `5ffae457f8c97d47f5cb649c107e584ca5219dd6` |

---

## 三十三、Station 5d 獨立審查（FAIL）與 Station 3e 裁決（2026-10-02，Jeff）

### 33.1 審查報告

- 路徑 docs/audits/2026-10-02-m1a-station5d-independent-review-fail.md；raw = normalized（LF），sha256 35a385d859056528f22a1bb369bea92901c3e0e0f4de22e085e8796a79e863cf
- 審查對象 889fbd8f666ea522ff6af172979a8d020e50b86b；判決 FAIL（valid independent review，於全新對話執行）；阻擋 1（S5d-F1），非阻擋 5（S5d-F2–F6）
- 報告內的本機路徑已由審查者遮罩為 <user>。

### 33.2 裁決助手外部重現（隔離環境；不是本 repo 的帳本證據；未寫入本 repo 任何檔案）

- 環境：pytest 9.1.1。測試 `def test_a(): assert 1 == 2`。
- 正常執行 ⇒ 1 failed。PYTHONOPTIMIZE=1 ⇒ 1 failed（測試模組的 assert 經 rewrite 仍執行）。
- PYTHONOPTIMIZE=1 + PYTEST_ADDOPTS=--assert=plain ⇒ 1 passed；pytest 只發出 PytestConfigWarning
  「ASSERTIONS ARE NOT EXECUTED and FAILING TESTS WILL PASS」。⇒ S5d-F1 在真實執行上成立。
- 附加發現（裁決助手，非審查者發現，記為 S5d-X1）：assert 寫在非測試的輔助模組（不被 rewrite）時，
  只要 PYTHONOPTIMIZE=1（預設 rewrite 模式、不加 --assert=plain）⇒ 1 passed。
  ⇒ 審查報告「本發現只成立於 plain 模式」的範圍過窄；根因是直譯器的最佳化旗標，不是 assert 模式。

### 33.3 裁決

1. Station 5d FAIL 成立；S5d-F1 為阻擋，納入 M1-a（審查報告的選項 A）。
   理由：後果與 S5b-F1、S5c-F1 同為假綠；兩個環境變數即可觸發，屬一般使用而非對抗；
   依 ODC-1 第 2 項「確實執行並通過」，assert 不執行的 run 不得取得退紅權。
   依流程回 Station 3e（規劃 + 紅燈）→ 4e（修正）→ 5e（新的獨立審查）。不推、不回滾、不改寫歷史。
2. 方向（合約）：從「列舉會出問題的管道」改為「定義合格的執行環境」（受支援執行邊界）。
   pytest 版本、plugin、收集設定已是白名單；本輪補上「直譯器與 pass 有效性」這一層。
   最低要求：producer 正向記錄 sys.flags.optimize，非 0 或缺欄 ⇒ 不得為 "true"。
   Station 3e-0 規劃時一次盤點：哪些直譯器旗標、pytest 選項或環境輸入會讓「passed」不再代表斷言確實執行並通過
   （至少涵蓋 -O / -OO / PYTHONOPTIMIZE、--assert 模式、會改變 pass / fail 語意的其他內建選項），
   逐項附 pytest 9.1.1 / CPython 出處、分類（會造成假通過／只會更嚴／不影響）、producer 能否正向讀到，再定白名單合約。
3. S5d-F3（刻意構造的輸入使 producer 寫入未正規化路徑）：納入 4e 修正（違反〈二十五〉裁決 1 (1) 的字面，修正成本低）；
   3e 規劃須列出對應的紅燈。
4. S5d-F2（plugin 自行 unregister）：非阻擋，併入 S5c-F4 的追蹤票（行程內程式碼使事實失真）。
   S5d-F4（Windows 上 subprocess 逾時不保證有上界）、S5d-F5（鎖步測試推導的寫法缺口）、S5d-F6（resolve 與 absolutepath 形式不同）：
   非阻擋，皆只會 fail-closed / fail-loud，登記到結案後追蹤票。
5. 程序事件：審查者一次誤用 pipe（git grep 正規表示式中的 | 被 shell 解讀；後段未執行、無寫入），事後以 git show 全檔 + Grep 重做；
   工具環境自動把超長輸出存到 repo 外的 tool-results 目錄。審查前後 HEAD、樹狀態、兩本帳、閘門攔截數皆未變
   （裁決助手以 status_all 核對）。照實記錄，不影響審查效力。
   另記：本輪曾誤把審查提示貼到實作 session，該 session 拒絕自審並停手；正式審查改在全新對話執行。
6. 結案後追蹤票清單更新為：conftest 不受 R2/R3 管的缺口；session 帳本增長；S5b-F2–F6；S5c-F3；
   S5c-F4 + S5d-F2（行程內程式碼使事實失真）；S5d-F4、S5d-F5、S5d-F6；
   pytest / anyio 版本未在 dependency 精確 pin；測試身分 parametrize ID 帶本機 repo 路徑；上游票 139 少一空行。

---

## 三十四、Station 3e 紅燈規劃

- 規劃檔:`docs/audits/2026-10-03-m1a-station3e-redlight-plan.md`(依〈三十三〉33.3 裁決 1–3 與 Jeff 併入 3e-0 指令的補充裁決 1–3;只讀原始碼推得,未執行 pytest)。
- **authority scope**:受 agent-gates 管控的 pytest 主執行環境中,`passed` 沒有因 interpreter / pytest execution mode 而失去通常的 pass 語意;測試自行啟動的子行程、外部工具屬 scope 外。
- **P1**:69 列;(A) 8、(B) 10、(C) 9、(D) 6、(E) 33、scope 外 3。pytest 9.1.1 的內建 CLI 選項以 Grep `addoption(` 全數列舉;`sys.flags` 逐欄分類。
- **P2(a)**:`-O` / `-OO` / `PYTHONOPTIMIZE` 都反映在 `sys.flags.optimize`(唯讀,行程內無公開途徑可改);讀取點放在 `_completeness_of`(`<TARGET>:tests/conftest.py:335-357`),在 sessionfinish 當下經模組層 `sys` 讀取。
- **P2(b)**:被 pytest 改寫的 assert 在 `-O` 下仍執行,未改寫的輔助模組不執行(S5d-X1);`optimize == 0` 時 `--assert=plain` 只失去訊息 ⇒ 歸 (D),合約不需要 assertmode,只鎖 `optimize == 0`。
- **P2(c)**:(xii)「任何 `(name, None)` ⇒ 不得為 `"true"`」不需調整;它同時擋住 `-p no:skipping` / `no:warnings` / `no:unraisableexception` / `no:threadexception` 這些會改變 outcome 解讀的停用。
- **P2(d)**:producer 寫入的欄位逐欄歸入三類;缺口在 `blocked`(完全不正規化)、`plugins[].name` 的 `pytest_<路徑>`、`inifilename` 與 `override_ini` value 的越界相對路徑,以及全部依賴平台相依的 `os.path.isabs`。
- **P3 摘要**(待 Jeff 裁):
  - 新增條件候選:(xiv) `sys.flags.optimize == 0`;(xv) `runxfail is False`;(xvi) `pythonwarnings` 為 None / 空;(xvii,可選) `trace is False`。
  - 組法:甲 (xiv);乙 (xiv)+(xv)+(xvi);乙+ 再加 (xvii);丙 option 全鍵枚舉。
  - S5d-F3:F3-甲(規則式、平台無關的路徑判定 + 名稱封閉字元集 + override 只動路徑值)、F3-乙(ini 型別表)、F3-丙(拒絕)。
  - 規劃建議:**乙 + F3-甲**。
- **P4 草案**(依建議組法):預期紅 16 支、預期綠 10 支(以本機 Windows 為準;4 支 `[win-abs]` / `[posix-abs]` 的綠在 POSIX 上會變紅,即 S5d-F3 的跨平台缺口);4e 後受影響的既有測試:乙 14 支、甲 2 支,授權方式 A / B 待裁。

---

## 三十五、Station 3e 裁決與 pass 有效性合約（2026-10-03，Jeff）

### 35.1 裁決(照錄)

1. 裁決助手在隔離環境以 pytest 9.1.1 實測（不是本 repo 帳本證據），規劃檔 P1 三項推論成立：
   (a) 測試本體呼叫 pytest.xfail(...) 後無其他斷言：正常 ⇒ XFAIL；加 --runxfail ⇒ PASSED。
   (b) 已提交 filterwarnings = ["error::UserWarning"]，測試發出 UserWarning：正常 ⇒ FAILED；加 -W ignore::UserWarning ⇒ PASSED。
   (c) 未開最佳化時 --assert=plain：失敗的 assert 仍 FAILED（只失去 introspection 訊息）⇒ 歸 (D)，不列入合約。
   (d) 直譯器層的警告設定不會蓋過已提交的 filterwarnings：已提交 filterwarnings = ["error::UserWarning"]、測試發出 UserWarning，
       PYTHONWARNINGS=ignore::UserWarning、PYTHONWARNINGS=default、python -W ignore::UserWarning 三種情形皆仍為 FAILED；
       只有 pytest 的 -W ignore::UserWarning 會變成 PASSED（已由 (xvi) 擋下）。
       ⇒ 與規劃檔 P1 I-8 的推論一致（pytest 每個測試把 ini filterwarnings 疊在直譯器層 filter 之後，後者優先序最低）。
       sys.warnoptions 不列為合約條件；依賴環境預設 filter 的斷言屬 scope 外 S-3。
2. authority scope（沿用 3e-0 補充裁決 1）：受 agent-gates 管控的 pytest 主執行環境中，passed 未因 interpreter / pytest execution mode 失去通常的 pass 語意；
   不涵蓋測試自行啟動的子行程或外部 runtime。
3. 合約新增條件（受支援執行環境白名單的直譯器與 pass 有效性層）；full_file_coverage == "true" 須全部成立：
   (xiv)   sys.flags.optimize == 0（int，不接受 bool）；producer 在 sessionfinish 當下經 conftest 模組層的 sys 讀取；缺欄或型別錯 ⇒ 不得為 "true"。
   (xv)    config.option.runxfail is False；缺欄 ⇒ 不得為 "true"。
   (xvi)   config.option.pythonwarnings 為 None 或空 list。
   (xvii)  config.option.trace is False；缺欄 ⇒ 不得為 "true"（除錯模式下人可在中途改變狀態，不作為證據執行）。
   (xviii) Python 版本（major.minor）屬於已盤點清單，目前為 {"3.11"}，以常數定義在 redlight.py；不在清單 ⇒ 不得為 "true"。
           理由：P1 對 sys.flags 的盤點只對 3.11 成立；升級 Python 須走票重做盤點（與 (xiii) 鎖 pytest 版本同理）。
           鎖 major.minor 而非 micro：P1 對 sys.flags 與 assert 移除的依據是 Python 3.11 的文件化語意，不是特定 patch 版的實作細節；
           patch 升級不改這些語意，鎖到 micro 只會讓安全更新也須走票。
   不新增 assertmode 條件（--assert=plain 在 optimize == 0 時屬 reporting）。
4. S5d-F3 採規劃檔 P3 的 F3-甲（規則式，依欄位類別，不依特定字串）：
   - 絕對路徑判定與平台無關：posixpath.isabs(v) or ntpath.isabs(v)，或以磁碟代號開頭。
   - (1) 類欄位（inipath、inifilename、invocation.args、plugins[].name 中的路徑型名稱）：絕對 ⇒ root 相對 posix 路徑或 <outside>；
     相對 ⇒ 先以 invocation_params.dir 解析再同上；越出 root ⇒ <outside>。
   - 名稱欄位（plugins[].name、blocked[]）：conftest 註冊的路徑名依上一條；符合 [A-Za-z0-9_.-]+（含數字 id）者原樣；其他記 <non-identifier>；
     kind 判定用原始名稱，正規化只作用於落帳字串。
   - (2) 類欄位（override_ini）：key 一律原樣；value 只在依上述規則為絕對路徑、或 normpath 後越出 root 時正規化；其他值一律原樣。
5. 授權（明文例外）：4e 可在兩個共用預設 dict（tests/test_redlight.py 的 _C_OPTION_DEFAULTS、tests/test_status.py 的 _S_OPTION_DEFAULTS）
   只新增三個鍵 "runxfail": False、"pythonwarnings": None、"trace": False（皆為真實 pytest 預設值），其他 helper 內容一律不改；
   並在規劃檔 P4「直接以 record_session 寫入 completeness dict」的 2 支測試補上 optimize: 0、python 版本、三個 option 鍵。
   assertion、docstring、test identity 一律不改。
6. 殘餘（照實記錄）：I-7（刻意製作的最佳化 bytecode）；P-1 殘餘（S5c-F4、S5d-F2）；scope 外 S-1–S-3。

### 35.2 anyio 4.15.0 唯讀查證(Station 3e-1 第 0 步)

以 Grep 搜尋已安裝 anyio 的 `pytest_plugin.py`:

| 搜尋項 | 結果 | 用途 |
|---|---|---|
| `addoption` | 有:`anyio/pytest_plugin.py:94-103`(`--anyio-mode`,dest `anyio_mode`);另有 ini `anyio_mode`(`:89-93`,預設 `strict`) | `auto` 時所有 async 測試由 anyio 執行(`:106-109, 192-207`) |
| `pytest_runtest_makereport` | 無 | — |
| `pytest_pyfunc_call` | 有:`anyio/pytest_plugin.py:268-302`(tryfirst) | 只處理帶 `anyio_backend` 的協程測試,在 runner 中執行本體;例外(含 ExceptionGroup 內的 Exit / KeyboardInterrupt / SystemExit)一律重拋(`:291-298`),成功才回 True |
| `pytest_collection_modifyitems` | 無 | — |
| 其他 hook(附帶) | `pytest_configure`(`:112-128`,註冊 `anyio` marker)、`pytest_fixture_setup` hookwrapper(`:131-189`,只包 async fixture)、`pytest_pycollect_makeitem`(`:192-207`,只加 `usefixtures("anyio_backend")`)、`pytest_collection_finish`(`:210-265`,把未帶 backend 的 anyio 協程測試換成依 backend 參數化的項目) | 不改 outcome |

判斷:**沒有找到會把失敗轉成通過的機制。**
- `--anyio-mode=auto` 只會讓原本因 pytest 不支援 async 而 `fail` 的測試(`_pytest/python.py:147-169`)**真的執行**。執行後的斷言照常評估,失敗照常重拋 ⇒ passed 仍代表本體執行並通過。
- `pytest_collection_finish` 的項目替換屬 selection 面:producer 記下的 selected 與 outcome 身分若對不上,會由 `validate_session` 判為不合格(方向為 fail-closed)。本 repo 的 `tests/` 沒有 async 測試。

### 35.3 預期集合(Station 3e-1;完整 nodeid)

預期紅集合(behavior-red,18 支,在 2258490 上必須失敗):

- tests/test_redlight.py::TestPassValidityCoverage::test_e3o_an_optimized_interpreter_is_not_full_coverage[1]
- tests/test_redlight.py::TestPassValidityCoverage::test_e3o_an_optimized_interpreter_is_not_full_coverage[2]
- tests/test_redlight.py::TestPassValidityCoverage::test_e3o_a_missing_optimize_fact_is_not_full_coverage
- tests/test_redlight.py::TestPassValidityCoverage::test_e3x_runxfail_alone_is_not_full_coverage
- tests/test_redlight.py::TestPassValidityCoverage::test_e3w_a_pytest_warning_filter_alone_is_not_full_coverage
- tests/test_redlight.py::TestPassValidityCoverage::test_e3t_trace_alone_is_not_full_coverage
- tests/test_redlight.py::TestPassValidityCoverage::test_e3v_an_unrecognized_python_version_is_not_full_coverage
- tests/test_redlight.py::TestPassValidityCoverage::test_e3o_the_producer_records_the_interpreter_optimize_flag
- tests/test_redlight.py::TestPassValidityCoverage::test_e3x_the_producer_records_runxfail_and_pythonwarnings
- tests/test_redlight.py::TestProducerPathNormalization::test_e3p_blocked_plugin_names_never_persist_a_path[win-abs]
- tests/test_redlight.py::TestProducerPathNormalization::test_e3p_blocked_plugin_names_never_persist_a_path[posix-abs]
- tests/test_redlight.py::TestProducerPathNormalization::test_e3p_blocked_plugin_names_never_persist_a_path[rel-escape]
- tests/test_redlight.py::TestProducerPathNormalization::test_e3p_a_config_file_option_never_persists_a_path[rel-escape]
- tests/test_redlight.py::TestProducerPathNormalization::test_e3p_an_override_value_never_persists_a_path[rel-escape]
- tests/test_status.py::TestPassValidityChain::test_e3o_optimized_pass_does_not_retire_a_known_red
- tests/test_status.py::TestPassValidityChain::test_e3o_optimized_run_does_not_make_a_clean_file_green
- tests/test_status.py::TestPassValidityChain::test_e3x_runxfail_pass_does_not_retire_a_known_red
- tests/test_status.py::TestPassValidityChain::test_e3w_warning_filter_pass_does_not_retire_a_known_red

預期綠集合(regression-lock,10 支,在 2258490 上必須通過;以本機 Windows 為準):

- tests/test_redlight.py::TestPassValidityCoverage::test_e3d_the_fixed_command_with_a_plain_interpreter_is_full_coverage
- tests/test_redlight.py::TestPassValidityCoverage::test_e3a_plain_assert_mode_on_a_plain_interpreter_is_still_full_coverage
- tests/test_redlight.py::TestProducerPathNormalization::test_e3p_a_config_file_option_never_persists_a_path[win-abs]
- tests/test_redlight.py::TestProducerPathNormalization::test_e3p_a_config_file_option_never_persists_a_path[posix-abs]
- tests/test_redlight.py::TestProducerPathNormalization::test_e3p_an_override_value_never_persists_a_path[win-abs]
- tests/test_redlight.py::TestProducerPathNormalization::test_e3p_an_override_value_never_persists_a_path[posix-abs]
- tests/test_redlight.py::TestProducerPathNormalization::test_e3p_non_path_override_values_are_persisted_verbatim
- tests/test_redlight.py::TestProducerPathNormalization::test_e3p_non_path_plugin_names_are_persisted_verbatim
- tests/test_redlight.py::TestProducerPathNormalization::test_e3p_a_root_relative_config_file_option_is_persisted_as_given
- tests/test_status.py::TestPassValidityLocks::test_e3d_the_fixed_command_full_run_still_retires_the_red

---

## 三十六、Station 3e 紅燈證據

- 報告:`docs/audits/2026-10-03-m1a-station3e-redlight.md`。
- S3e-1 `7ebbb815fbba96124d971fe0066c096c3f1db8e8`:兩個測試檔各一個接在檔尾的 hunk(`@@ -1532,0 +1533,317 @@`、`@@ -2565,0 +2566,160 @@`),沒有刪除行;commit 前只跑 py_compile。
- 固定全套(只跑一次,在 S3e-1 上):exit 1。失敗集合恰為〈三十五〉35.3 的 18 支;10 支 regression-lock 與其他全部既有測試通過。
  - 計數(由帳本第 18 行與 status 重建):collected 2021 / passed 1997 / failed 18 / skipped 3 / xfail 3。
  - **pytest 摘要行原文缺失**:工具輸出被截斷,依規定未重跑;詳見報告第 4 節。
- 帳本 H5 → H6 只追加:
  - test-runs 684893 → 697745 bytes(2549 → 2595 行,+46)。
  - test-sessions 4891233 → 5599744 bytes(17 → 18 行,+1)。
  - 兩本前段 sha256 等於 H5(`23f397d4…` / `7463a452…`)。
- status:red 只有 tests/test_redlight.py、tests/test_status.py;最近一次 run 為 B(collected 2021)。
- anyio 4.15.0 唯讀查證:沒有會把失敗轉成通過的機制(〈三十五〉35.2)。
- commit(回填):S3e-1 `7ebbb815fbba96124d971fe0066c096c3f1db8e8`;S3e-2(證據)`1c771c400c620a03135971063c37b89d4d237c74`。

---

## 三十七、Station 4e 修正

裁決(2026-10-03,Jeff;照錄):

- Station 3e = PASS / ACCEPTED,選 A(以帳本第 18 行 producer 紀錄代替缺失的 pytest 摘要行,不重跑 3e;
  裁決助手已在隔離環境以 pytest 9.1.1 獨立重現 18 支的失敗原因皆正確 —— 非本 repo 帳本證據)。以 Jeff 切換 pipeline 為 implement 為驗收。

裁決助手外部觀察(**隔離環境、非帳本證據**):

- 在 Linux 上,S3e-1 的 3e 28 支為 20 failed / 8 passed。
- 多出的 2 支 = `test_e3p_a_config_file_option_never_persists_a_path[win-abs]`、`test_e3p_an_override_value_never_persists_a_path[win-abs]`(POSIX 上認不出 Windows 絕對路徑 = S5d-F3 跨平台缺口)。
- 4e 的 F3-甲 必須讓這 6 個參數化案例在兩種平台都綠;此點列為 5e 審查題。

### 37.1 實作內容(S4e-1)

**`.claude/hooks/redlight.py`**:
- 依〈三十五〉35.1 第 3 點新增五個事實與條件:
  - `COMPLETENESS_OPTIONS` 加 `runxfail`、`pythonwarnings`、`trace`。
  - 新常數 `KNOWN_PYTHON_VERSIONS = ("3.11",)`。
  - `_completeness_problems` 加驗:`optimize`(int,不含 bool)、`python_version`(字串)、`options.runxfail` / `options.trace`(bool)、`options.pythonwarnings`(None 或字串 list)。缺欄或型別錯 ⇒ 不合格 ⇒ unknown。
  - `_completeness_verdict` 加:`optimize != 0`、版本不在清單、`runxfail` / `trace` 不是 False、`pythonwarnings` 不是 None / 空 ⇒ unknown。
  - 唯一 `"true"` 出口不變;不新增 assertmode 條件;不帶入 `sys.warnoptions`。
- F3-甲(〈三十五〉35.1 第 4 點):
  - 平台無關的絕對路徑判定 `_is_abs_path`(`posixpath.isabs` 或 `ntpath.isabs` 或磁碟代號開頭)。
  - (1) 類路徑 `_root_relative`:相對路徑先以 base 解析,越出 root 或他平台絕對路徑 ⇒ `<outside>`。
  - 名稱欄位 `_plugin_name`:路徑名 ⇒ (1);`[A-Za-z0-9_.-]+` 原樣;其他 `<non-identifier>`。
  - `classify_plugins` 以原始名稱判 kind,落帳字串正規化。
  - `blocked_plugins(name_plugins, root)` 正規化落帳字串。
  - `normalize_config_path(value, root, base)` 一律走 (1)。
  - `normalize_overrides(values, root, base)`:key 原樣;value 只在絕對或越出 root 時正規化。
  - `_normalize_arg`(invocation.args)對他平台的絕對路徑回 None。
- `validate_session` 未改。

**`tests/conftest.py`(producer)**:
- 模組層 `import sys`。
- `_optimize_flag()` / `_python_version()` 在 sessionfinish 當下經模組層 `sys` 讀 `sys.flags.optimize`、`sys.version_info`(不在 import 時快取)。
- completeness 新增 `optimize`、`python_version` 兩鍵。
- `_plain` 把字串 list 原樣記成 list(`-W` 的 filter)。
- `blocked` / `override_ini` / `inifilename` 傳入 root 與 `invocation_params.dir`。

**授權補件(〈三十五〉35.1 第 5 點)**:
- `_C_OPTION_DEFAULTS`、`_S_OPTION_DEFAULTS` 各加三個鍵。
- 兩支直接寫 dict 的測試補 `optimize: 0`、`python_version: "3.11"` 與三個 option 鍵。

**未改**:`.claude/portable/status.py`。

### 37.2 驗收結果

- 報告:`docs/audits/2026-10-03-m1a-station4e-fix.md`。
- S4e-1 `0139a7e803fc2d41eb354f1196a6206cfe304701`(`5 files changed, 222 insertions(+), 37 deletions(-)`)。
- 固定全套(只跑一次,在 S4e-1 上):`2015 passed, 3 skipped, 3 xfailed in 159.82s (0:02:39)`,exit 0(collected 2021)。輸出經 shell 導入 session scratch 檔保存,pytest 指令本身未加參數。
- 四項判定:
  - (a) 3e 的 18 支全部轉綠,10 支 regression-lock 仍綠 —— **成立**(帳本第 19 行 28 支皆 `passed`)。
  - (b) 第 19 行新事實合格 —— **成立**:
    - `optimize` 0、`python_version` "3.11"、`runxfail` false、`pythonwarnings` null、`trace` false。
    - 舊事實不變:`override_ini == ["strict_markers=true"]`、`inifilename` null、`inipath` "pyproject.toml"、兩個 blob worktree = head、`pytest_version` "9.1.1"、anyio 4.15.0 known_dist、other 0、None 項目 0。
    - producer 欄位無絕對路徑;全帳本本機使用者名稱 0 筆。
  - (c) 帳本 H6 → H7 只追加 —— **成立**:兩本前段 sha256 = H6;test-runs +46 行、test-sessions +1 行。
  - (d) status:red(無)、green 46、最近一次 run A —— **成立**。
- 3c / 3d 中斷言 `!= "true"` 的既有測試:沒有任何一支是因 4e 新條件才通過(報告第 4e 節逐支列出主因條件與行號)。
- 程序記錄:〈十〉Station 3e 列已在 S4e-1 依 3e 裁決同步為 PASS / ACCEPTED(舊值「紅燈已寫,待驗收」)。

---

## 三十八、Station 5e 審查包

| 名稱 | 值 |
|---|---|
| BASE | `84014bae237a4741dae8ad18c6c041a3c3ef97b0` |
| TARGET(唯一審查對象,S4e-1) | `0139a7e803fc2d41eb354f1196a6206cfe304701` |
| S4E2(4e 證據) | `f9d67d8e83778741cd5dcaf8ad13f11602d9b0b5` |
| S3E2(3e 證據) | `1c771c400c620a03135971063c37b89d4d237c74` |
| 審查包 | `docs/audits/2026-10-03-m1a-station5e-review-package.md` |
| 審查包大小 | 394851 bytes / 6994 行 |
| 審查包 SHA-256 | `754721dc20305e127dfd5de0c4ddccc001f040abe5fd6c06c7ced033615fb302` |
| 審查包 staged blob | `ec6f6c68e88a78bff8aedaa93263157548080a93` |
| S5e-0(本 commit) | `4f839d2399c36cf1c8bca36b91a27d4932c6e5e2`(2026-10-03 於 S5e-1 回填;原值「記錄 5e 結果時回填」) |

- 審查報告只寫到 `.scratch/m1a-s5e/review-report.md`;審查者規則見審查包 A.3。
- 審查包內的逐字段落皆以 cmp 對出處核對過(詳見 S5e-0 的回報)。

---

## 三十九、Station 5e 獨立審查（審查者 PASS;依 Jeff 裁決 FAIL）與 Station 3f 裁決（2026-10-03，Jeff）

### 39.1 審查報告

- 路徑 `docs/audits/2026-10-03-m1a-station5e-independent-review.md`;raw = repo 副本(與審查者原檔 `.scratch/m1a-s5e/review-report.md` 以 `cmp` 逐位元組相同,無任何改動);
  sha256 `c8ed7d0ba20dcaa39258532bd0f7dda1329f638490bd5dcbb8acf80a4ea8259d`;40861 bytes。
- 審查對象 TARGET `0139a7e803fc2d41eb354f1196a6206cfe304701`;審查包所在 commit S5e-0 `4f839d2399c36cf1c8bca36b91a27d4932c6e5e2`。
- **審查者原始判決:PASS**(阻擋 0、非阻擋 6)。報告第 1 節的附帶聲明原文:

  > **附帶聲明**:S5e-F1(`--pdb` 不在白名單合約內)我判為非阻擋,但它的理由與 (xvii) 收 `--trace` 的理由相同。若裁決者認定它屬於 M1-a 範圍(F1 的選項 A),本判決應改為 FAIL。判斷依據寫在 S5e-F1 的「為什麼判非阻擋」。

- 審查過程曾被 R7(`python -c`)擋下一次;審查者停手回報,Jeff 裁定停手正確、不算違規,並指定只用 `python -m pip show` 取得 pytest / pluggy 安裝位置。經過記於報告第 5 節。
- 發現清單(報告第 3 節標題原文):
  - S5e-F1【非阻擋(請裁決)】`--pdb`:失敗後進入 post-mortem,人可以改行程內狀態再 `continue`,讓**其他檔**的已知紅被退掉。白名單合約沒有涵蓋它
  - S5e-F2【非阻擋】invocation dir 在 root 之外時,`override_ini` 的非路徑值 `true` 被改寫成 `<outside>`;固定指令從上層目錄執行時永遠是 unknown(相較 889fbd8 是可用性退步,方向為 fail-closed)
  - S5e-F3【非阻擋】POSIX 上,以反斜線分隔、會越出 root 的相對值,在值類欄位不被認為越界,原字串照樣落帳(可帶本機使用者名稱;與 Windows 結果不同)
  - S5e-F4【非阻擋】`_IDENTIFIER` 用 `re.match` 配 `$`,接受結尾帶換行的名稱,與合約字元集 `[A-Za-z0-9_.-]+` 的字面不符
  - S5e-F5【非阻擋】4e 報告 4e 表把 c3 生產端測試的第一個擋下條件寫成 (viii) `:784-785`,實際是 (vii′) `:778-779`
  - S5e-F6【非阻擋】依合約原樣落帳、但可以帶路徑的兩個欄位:override 的 key、`pythonwarnings`

### 39.2 裁決助手外部重現(隔離環境;非獨立審查 finding;非本 repo 帳本證據)

來源:Jeff 的 Station 5e-1 指令第 4 點,照錄。

- Linux + Python 3.11 + pytest 9.1.1 + TARGET 的 redlight.py / conftest.py:
  R1 固定全套 test_x 失敗(已知紅);R2 加 --pdb,另一檔 test_a 失敗進 pdb,輸入 `!import impl; impl.f = lambda: 2` 後 `c`,
  test_x 通過;R2 run_state B、file_coverage(run, "tests/test_x.py") == "true" ⇒ 會退紅。S5e-F1 成立。
- normalize_overrides(["strict_markers=true"], root, root 的上一層) ⇒ ["strict_markers=<outside>"];實際從上一層執行,
  落帳 override_ini 為 ["strict_markers=<outside>"]、file_coverage 為 "unknown"。S5e-F2 成立。
- POSIX 上 normalize_overrides(["cache_dir=a\..\..\..\home\x\c"], root, root) 原樣保留。S5e-F3 成立。
- _plugin_name("abc\n", root) 回 "abc\n"。S5e-F4 成立。
- pytest 9.1.1 讀碼:--pdbcls 的 dest 為 usepdb_cls(_pytest/debugging.py:51);其模組只在 debugger 被叫出時才 import
  (_pytest/debugging.py:117-139)。此點僅供 3f-0 參考,不構成裁定。

### 39.3 裁決(照錄)

1. 獨立審查者原始判決:PASS(阻擋 0、非阻擋 6),附帶聲明 S5e-F1 若屬 M1-a 範圍則判決改為 FAIL。原始判決照錄,不得改寫為「審查者判 FAIL」。
   Jeff 裁定:S5e-F1 屬 M1-a 範圍,視為阻擋 ⇒ Station 5e 最終結果 = FAIL(依 Jeff 裁決;審查本身為有效獨立審查)。
2. 理由:〈三十五〉合約要求受支援的 pytest 主執行環境中,passed 不因 execution mode 失去正常證據語意;
   (xvii) 收 --trace 的理由「除錯模式下人可在中途改變狀態,不作為證據執行」對 --pdb 同樣成立;只收其一,合約內部不一致。
   且裁決助手已實際重現 false green(見第 4 點)。
3. Station 3f 範圍(由 3f-0 規劃細化,本步不寫測試):
   - 必做:S5e-F1 —— 新增 (xix):config.option.usepdb is False;缺欄或型別錯 ⇒ 不得為 "true"。
   - 待證明項(3f-0 依 pytest 9.1.1 原始碼裁定,本步不得預先決定):usepdb_cls(--pdbcls 的 dest;注意名稱含底線)
     在 usepdb=False、trace=False 時能否單獨啟動或改變 debugger / execution semantics。
     若不能:新增 regression-lock,證明非 None 的 usepdb_cls 本身不降低 authority,避免不必要的 fail-closed;
     若能:才把 usepdb_cls 加入 (xix)。
   - 防「錯欄位測試」:3f 紅燈須至少一支經真實 pytest 參數解析(真實 conftest producer)證明 producer 讀到的是 pytest 真正的
     config.option.usepdb(及 3f-0 若裁定需要的 usepdb_cls);不得只以人工 dict 塞同名欄位給 consumer 來證明。
   - 一併修:S5e-F2(override 非路徑值在 invocation dir 位於 root 外時被改寫成 <outside>)、
     S5e-F3(POSIX 反斜線越界未被認出,原字串落帳)、S5e-F4(_IDENTIFIER 以 match + $ 接受結尾換行)。
   - S5e-F5:4e 表行號更正,寫在 3f 報告的 correction 段,不回寫 4e 報告。
   - S5e-F6:非阻擋,列入 privacy / provenance 追蹤票,不在本票修。

(39.3 第 2 點的「見第 4 點」指 Jeff 指令的第 4 點,即本節 39.2。)

---

## 四十、Station 3f 紅燈規劃

- 規劃檔:`docs/audits/2026-10-03-m1a-station3f-redlight-plan.md`(只規劃,未寫測試、未改 .py、未跑 pytest)。
- BASELINE:`e0459be46bfa5d3f7514526e57cf1f05127bb841`(S5e-1;產品碼與 TARGET `0139a7e803fc2d41eb354f1196a6206cfe304701` 相同)。
- 規劃結論摘要:
  - P2:`usepdb_cls` 在 `usepdb=False` 且 `trace=False` 時不能單獨改變執行 ⇒ 結論 (a)(唯一讀點 `_pytest/debugging.py:117` 只在 debugger 被建立時執行;剩下的進入點只有被執行的程式碼自己呼叫,歸 P-1)。
  - P3:複查 3e-0 判為「不影響」的列,另找到 I-9 / I-6 族(執行的程式碼不是工作樹那一份),列為待裁;O-16(`-s` 下讀 stdin)歸 P-1。
  - P7:新增 35 支(behavior-red 12、regression-lock 23);預期固定全套 collected 2056(以 S4e-1 的 2021 為底)、failed 12(本機 Windows)。
- P10 待 Jeff 裁(各項選項、建議與理由見規劃檔 P10):
  1. `usepdb_cls` 是否加入 (xix) —— 建議 A:不加,只寫 regression-lock。
  2. 防錯欄位測試的取得方式 —— 建議 A:`pytestconfig._parser.parse_known_args(...)`。
  3. S5e-F2 修法 —— 建議乙:override value 以 root 為基準判越界(需確認〈三十五〉35.1 4 (2) 類以 root 為基準的合約澄清)。
  4. S5e-F3 本機紅燈 —— 建議 A:以 proxy 替換 redlight 模組所見的 `os` 模擬兩種平台,另加真實平台測試。
  5. I-9 / I-6 族 —— 建議 A:列殘餘、另開追蹤票,本票不處理。
  6. 測試授權文字 —— 建議 A:兩個共用 dict 各加 `"usepdb": False`,2 支直接寫 dict 的測試補 `u"usepdb": False`。

---

## 四十一、Station 3f 裁決與紅燈集合（2026-10-03，Jeff）

### 41.1 裁決(照錄;針對 S3f-0 8bdc4f2072a6b4300deb011a7b5a0d574254fc9c 規劃檔 P10)

1. usepdb_cls:A —— 不加入 (xix);只寫 regression-lock R5。
2. 防錯欄位:A —— pytestconfig._parser.parse_known_args(...)(本次 session 的完整 parser)。
3. S5e-F2:乙 —— override value 以 root 為基準判越界。合約澄清:〈三十五〉35.1 第 4 點 (2) 類「越出 root」的基準為 root。
   (1) 類(inifilename、invocation.args)維持以 invocation_params.dir 解析。
4. S5e-F3 紅燈:A —— 以 proxy 替換 redlight 模組所見的 os(posixpath / ntpath 兩種語意,R9–R12),另加真實平台 producer 測試 R13。
5. 「執行的程式碼不是工作樹那一份」(I-9 / I-6 族):A —— 列殘餘,另開追蹤票(受測物件身分 / provenance),本票不處理。
6. 授權:A —— 照規劃檔 7.4 原文(4f 可在 _C_OPTION_DEFAULTS、_S_OPTION_DEFAULTS 各只新增 "usepdb": False;
   2 支直接寫 completeness dict 的測試在 options 補 u"usepdb": False;assertion、docstring、test identity 一律不改)。
7. 補正(裁決助手):R2 改為參數化兩案,覆蓋裁決的「缺欄或型別錯」:
   tests/test_redlight.py::TestDebuggerModeCoverage::test_f3p_a_missing_or_malformed_usepdb_fact_is_not_full_coverage[missing]
   tests/test_redlight.py::TestDebuggerModeCoverage::test_f3p_a_missing_or_malformed_usepdb_fact_is_not_full_coverage[str]
   ([str] 的破壞組:option.usepdb = "False"(字串);兩案皆含對照組 usepdb=False ⇒ "true")。
   ⇒ 新增 36 支(behavior-red 13、regression-lock 23);預期 collected 2057;本機預期 failed 13、passed 2038、skipped 3、xfailed 3;
     POSIX 上 R13 另紅(14)。其餘 nodeid、情境、分類照規劃檔 7.3。

### 41.2 裁決助手外部驗證(隔離環境;非帳本證據)

來源:Jeff 的 Station 3f-1 指令第 8 點,照錄。

- pytest 9.1.1 中 pytestconfig._parser.parse_known_args(["--strict-markers","--pdb"])
  得 usepdb True、usepdb_cls None、override_ini ["strict_markers=true"];["--strict-markers","--pdbcls=pdb:Pdb"] 得 usepdb False、
  usepdb_cls ("pdb","Pdb");以 -p no:cacheprovider 執行時 namespace 無 lf 屬性(大聲失敗)。_pytest/cacheprovider.py:141 以 config.rootpath 解析 cache_dir。

### 41.3 預期集合(36 支,完整 nodeid)

預期紅集合(behavior-red,13 支,在 S3f-1 上必須失敗):

- tests/test_redlight.py::TestDebuggerModeCoverage::test_f3p_pdb_alone_is_not_full_coverage
- tests/test_redlight.py::TestDebuggerModeCoverage::test_f3p_a_missing_or_malformed_usepdb_fact_is_not_full_coverage[missing]
- tests/test_redlight.py::TestDebuggerModeCoverage::test_f3p_a_missing_or_malformed_usepdb_fact_is_not_full_coverage[str]
- tests/test_redlight.py::TestDebuggerModeCoverage::test_f3p_the_producer_records_usepdb_from_the_pytest_parser
- tests/test_redlight.py::TestDebuggerModeCoverage::test_f3p_pdb_parsed_by_pytest_is_not_full_coverage
- tests/test_redlight.py::TestOverrideBaseCoverage::test_f3o_an_invocation_dir_outside_the_root_keeps_non_path_override_values
- tests/test_redlight.py::TestOverrideBaseCoverage::test_f3o_the_fixed_command_from_the_parent_dir_is_full_coverage
- tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_a_backslash_escape_is_outside_under_posix_semantics[override]
- tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_a_backslash_escape_is_outside_under_posix_semantics[config-file]
- tests/test_redlight.py::TestIdentifierFullMatch::test_f3i_a_plugin_name_with_a_trailing_newline_is_not_persisted_verbatim
- tests/test_status.py::TestDebuggerModeChain::test_f3p_pdb_pass_does_not_retire_a_known_red
- tests/test_status.py::TestDebuggerModeChain::test_f3p_pdb_parsed_by_pytest_does_not_retire_a_known_red
- tests/test_status.py::TestOverrideBaseChain::test_f3o_the_fixed_command_from_the_parent_dir_retires_the_red

預期綠集合(regression-lock,23 支,在 S3f-1 上必須通過;以本機 Windows 為準):

- tests/test_redlight.py::TestDebuggerModeCoverage::test_f3c_pdbcls_alone_does_not_lower_authority
- tests/test_redlight.py::TestOverrideBaseCoverage::test_f3o_an_escaping_relative_override_is_outside_from_the_parent_dir
- tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_g3_inputs_under_posix_semantics[win-drive-backslash]
- tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_g3_inputs_under_posix_semantics[win-drive-slash]
- tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_g3_inputs_under_posix_semantics[drive-relative]
- tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_g3_inputs_under_posix_semantics[unc]
- tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_g3_inputs_under_posix_semantics[device]
- tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_g3_inputs_under_posix_semantics[posix-abs]
- tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_g3_inputs_under_posix_semantics[rel-escape]
- tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_g3_inputs_under_posix_semantics[rel-inside]
- tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_g3_inputs_under_posix_semantics[mixed-inside]
- tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_g3_inputs_under_windows_semantics[win-drive-backslash]
- tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_g3_inputs_under_windows_semantics[win-drive-slash]
- tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_g3_inputs_under_windows_semantics[drive-relative]
- tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_g3_inputs_under_windows_semantics[unc]
- tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_g3_inputs_under_windows_semantics[device]
- tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_g3_inputs_under_windows_semantics[posix-abs]
- tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_g3_inputs_under_windows_semantics[rel-escape]
- tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_g3_inputs_under_windows_semantics[rel-inside]
- tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_g3_inputs_under_windows_semantics[mixed-inside]
- tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_g3_inputs_under_windows_semantics[cross-drive]
- tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_a_backslash_escape_override_never_persists_a_path
- tests/test_status.py::TestDebuggerModeLocks::test_f3d_the_fixed_command_full_run_still_retires_the_red

**平台附註**:`test_f3s_a_backslash_escape_override_never_persists_a_path`(R13)在**本機 Windows 為綠、POSIX 為紅**(Windows 的 `ntpath.normpath` 本來就收合反斜線的 `..`);
POSIX 上 failed 預期為 14。

---

## 四十二、Station 3f 紅燈證據

- 報告:`docs/audits/2026-10-03-m1a-station3f-redlight.md`。
- S3f-1 `229b5e762f087193e138c7c8d0f0d0b0f3e5cbb5`:只在兩個測試檔的檔尾新增(`-U0` 各恰一個 hunk:`@@ -1850,0 +1851,293 @@`、`@@ -2731,0 +2732,125 @@`;沒有刪除行),另改票 145。
- 固定全套(在 S3f-1 上只跑一次):exit 1;摘要行原文 `13 failed, 2038 passed, 3 skipped, 3 xfailed in 169.02s (0:02:49)`(collected 2057)。
- 失敗集合恰為〈四十一〉41.3 的 13 支 behavior-red;23 支 regression-lock 與全部既有測試通過(帳本第 20 行逐支相符)。
- 帳本 H7 → H8 只追加:兩本前段 sha256 = H7;test-runs +46 行、test-sessions +1 行。
  H8:test-runs 721553 bytes / 2687 行 / `f7a025c6de2ad0d97ef38eac1725ea0e8d566fb0a0d453d3a5e530b84018a379`;
  test-sessions 7030070 bytes / 20 行 / `4ceb819ea08f78e3c9aa5849bf89e3ab2a54ca42619427fb0dfeab36e4f576fc`。
- status:red 只有 `tests/test_redlight.py`、`tests/test_status.py`;最近一次 run B(collected 2057)。
- R13 在本機 Windows 為綠、POSIX 為紅(未實測)。
- commit(回填):S3f-1 `229b5e762f087193e138c7c8d0f0d0b0f3e5cbb5`;S3f-2(證據)`2f6743fff2f13170b27c52c3390a69cc361dfe26`。

---

## 四十三、Station 4f 修正

裁決(2026-10-03,Jeff;照錄):Station 3f 紅燈 = PASS / ACCEPTED(以 Jeff 切換 pipeline 為 implement 為驗收)。

裁決助手外部驗證(**隔離環境;非本 repo 帳本證據**;來源:Jeff 的 Station 4f 指令,照錄):

- Linux + Python 3.11 + pytest 9.1.1,以 S3F1 229b5e762f087193e138c7c8d0f0d0b0f3e5cbb5 的 redlight.py / conftest.py / 兩個測試檔:
  3f 的 36 支為 14 failed / 22 passed —— 即 41.3 的 13 支 behavior-red 加 R13
  (tests/test_redlight.py::TestPlatformIndependentNormalization::test_f3s_a_backslash_escape_override_never_persists_a_path);
  R13 的失敗為持久化行含 "cache_dir=a\\..\\..\\..\\e3p-user\\c"。其餘 test_redlight + test_status(Sync 類除外)皆通過。
- 帳本第 20 行 failed 集合恰為 41.3 的 13 支;intercepts 的 2 筆新增為 5e-0 的 mkdir(14:14:26Z)與 5e 審查的 python -c(18:48:00Z),不屬 3f-1。

跨平台驗收(Jeff 裁定):
- R9–R13 必須在 Windows 語意與 POSIX 語意都轉綠;R13 在真實 POSIX producer 上必須綠。
- 本機只驗 Windows。4f 分三段:
  1. S4F1 實作;
  2. S4F2 本機 Windows 驗收;
  3. 裁決助手 POSIX 外部驗證通過後,S4F3(docs-only)升級為 PASS / COMPLETED。

### 43.1 實作內容(S4F1)

**`.claude/hooks/redlight.py`**:
- (xix)(〈三十九〉39.3 第 3 點):
  - `COMPLETENESS_OPTIONS` 加 `"usepdb"`。
  - `_completeness_problems`:`options.usepdb` 須為 bool(缺欄、None、字串、int ⇒ problems ⇒ unknown)。
  - `_completeness_verdict`:`usepdb is not False` ⇒ unknown;docstring 補 (xix)。
  - 唯一 `"true"` 出口不變;不加 `usepdb_cls`(〈四十一〉41.1 第 1 點)。
- S5e-F2(乙;〈四十一〉41.1 第 3 點):`normalize_overrides` 的非絕對 value 以 **root** 為基準判越界(`_root_relative(val, root)`)。key 原樣;絕對路徑分支不變。(1) 類(`inifilename`、`invocation.args`)維持以 `invocation_params.dir` 解析。
- S5e-F3:`_root_relative` 先以原字串判「他平台絕對」(順序不變),之後把 `\` 換成 `/` 再 join / normpath;relpath 之後的處理不變。
- S5e-F4:`_IDENTIFIER` 改為 `[A-Za-z0-9_.\-]+`,以 `fullmatch` 整串比對。

**`tests/conftest.py`**:未改(F2 在 redlight 端以 root 為基準;producer 仍傳 `inv_dir`,只有絕對路徑分支會用到它,而絕對路徑的結果與 base 無關)。

**授權補件(〈四十一〉41.1 第 6 點,照規劃檔 7.4)**:
- `_C_OPTION_DEFAULTS`、`_S_OPTION_DEFAULTS` 各只新增 `"usepdb": False`。
- 2 支直接寫 completeness dict 的測試在 `options` 補 `u"usepdb": False`。

**未改**:`.claude/portable/status.py`。

### 43.2 驗收結果(本機 Windows;S4F2)

- 報告:`docs/audits/2026-10-03-m1a-station4f-fix.md`。
- S4F1 `ad14418d903b26212dc9e98754f44aaa894375c8`(`4 files changed, 85 insertions(+), 13 deletions(-)`);conftest 未改。
- 固定全套(只跑一次,在 S4F1 上):`2051 passed, 3 skipped, 3 xfailed in 166.17s (0:02:46)`,exit 0(collected 2057)。
- 判定:
  - (a) 3f 的 13 支 behavior-red 全部轉綠,23 支 regression-lock 仍綠;規劃檔 7.4 的 24 支既有測試全部通過 —— **成立**(帳本第 21 行)。
  - (b) 第 21 行 `options.usepdb` false;既有事實不變;other 0;producer 欄位無絕對路徑;全帳本本機使用者名稱 0 筆 —— **成立**。
  - (c) 帳本 H8 → H9 只追加 —— **成立**:
    - 兩本前段 sha256 等於 H8;test-runs 2733 行(+46)、test-sessions 21 行(+1)。
    - H9:test-runs 732856 bytes / `ec6bc011…`;test-sessions 7751802 bytes / `33b920e9…`。
  - (d) status:red(無)、green 46、最近一次 run A —— **成立**。
  - (e) S5e-F5 更正已照錄進 4f 報告的 correction 段(3f 規劃檔 P8;未回寫 4e 報告)。
  - (f) (xix) 不是任何 3c / 3d / 3e `!= "true"` 測試通過的唯一理由(靜態推理,見報告 5f)。
- **未證明:R9–R13 的 POSIX 實測尚未完成,待裁決助手外部驗證。** 4f 在 S4F3 之前不標 PASS / COMPLETED。
- commit(回填):S4F1 `ad14418d903b26212dc9e98754f44aaa894375c8`;S4F2(本機驗收紀錄)`a761d2276a1a6d2dbdcd4a74cea4d401c75513db`。

### 43.3 POSIX 外部驗證(裁決助手)

**隔離環境;非獨立審查 finding;非本 repo 帳本證據。** 來源:Jeff 的 Station 4f S4F3 指令,照錄如下。

- 環境:Linux + Python 3.11 + pytest 9.1.1 + anyio 4.15.0;檔案取自 S4F2 工作樹(redlight.py、conftest.py、status.py、兩個測試檔,
  產品碼與 S4F1 ad14418d903b26212dc9e98754f44aaa894375c8 相同),放進新建 git repo 後執行。
- R9–R13(TestPlatformIndependentNormalization 全部 22 個案例,含 R13 test_f3s_a_backslash_escape_override_never_persists_a_path
  在真實 POSIX producer 上):22 passed。3f 時 R13 在同環境為 failed(〈四十三〉已記)⇒ 先紅後綠成立。
- 3f 新增的 36 支:36 passed。test_redlight + test_status(Sync 類除外,隔離環境未放 sync.py):195 passed。
- 真實 --pdb 重現(同 39.2 手法):R2 加 --pdb、於 pdb 內 `!import impl; impl.f = lambda: 2` 後 `c`,test_x passed;
  該 run file_coverage(run, "tests/test_x.py") == "unknown" ⇒ 不退紅。單獨 --pdbcls=pdb:Pdb 的 run 仍為 "true"(R5 語意)。
- normalize_overrides(["strict_markers=true", "python_files=tests/test_*.py", "cache_dir=../x", "cache_dir=a\..\..\..\home\z\c"],
  root, root 的上一層) ⇒ ["strict_markers=true", "python_files=tests/test_*.py", "cache_dir=<outside>", "cache_dir=<outside>"]。
- _plugin_name("abc\n", root) ⇒ "<non-identifier>"。
- 帳本 H8 → H9 前段 sha256 = H8r / H8s;test-runs 2687 → 2733、test-sessions 20 → 21;第 21 行 options.usepdb = false、other 0。

裁決(2026-10-03,Jeff;照錄):裁決助手 POSIX 外部驗證通過 ⇒ Station 4f = PASS / COMPLETED(待 5f 審查)。

- 4f 報告(`docs/audits/2026-10-03-m1a-station4f-fix.md`)不改。其第 7 節「未證明」第 1 點(R9–R13 的 POSIX 實測)由本節結案。
- S4F2 `a761d2276a1a6d2dbdcd4a74cea4d401c75513db`。

---

## 四十四、Station 5f 審查包

| 名稱 | 值 |
|---|---|
| BASE | `84014bae237a4741dae8ad18c6c041a3c3ef97b0` |
| TARGET(唯一審查對象,S4F1) | `ad14418d903b26212dc9e98754f44aaa894375c8` |
| S4F2(本機 Windows 驗收證據) | `a761d2276a1a6d2dbdcd4a74cea4d401c75513db` |
| S4F3(POSIX 外部驗證紀錄) | `bd57e617d3529b20d88d75b99da0f660f1b3685d` |
| S3F2 | `2f6743fff2f13170b27c52c3390a69cc361dfe26` |
| S3F1 | `229b5e762f087193e138c7c8d0f0d0b0f3e5cbb5` |
| 5E_TARGET(前一次審查對象) | `0139a7e803fc2d41eb354f1196a6206cfe304701` |
| 審查包 | `docs/audits/2026-10-03-m1a-station5f-review-package.md` |
| 審查包大小 | 413243 bytes / 7100 行 |
| 審查包 SHA-256 | `f254a9d7278e1cbdfb50d67443ac1014bdaa5094d0db000e2d5e9b2eb6e5c385` |
| 審查包 staged blob | `a5821b099b8b8d0c6c626297348ecc8682255150` |
| S5f-0(本 commit) | `695909f2f22ec17f97d4609f3fd28a5d146f252d`(回填) |

- 審查報告只寫到 `.scratch/m1a-s5f/review-report.md`;審查者規則見審查包 A.3(含第 10 條:不得用 python -c / heredoc;pytest / pluggy 安裝位置只准用 `python -m pip show`)。
- 審查包內的逐字段落皆以 cmp 對出處核對過(詳見 S5f-0 的回報)。

---

## 四十五、Station 5f 獨立審查（PASS）與裁決（2026-10-03，Jeff）

### 45.1 審查報告

- 路徑 `docs/audits/2026-10-03-m1a-station5f-independent-review.md`;raw = repo 副本(與審查者原檔 `.scratch/m1a-s5f/review-report.md` 以 `cmp` 逐位元組相同,無任何改動);
  sha256 `2fe5758e63ca0b7845552ffa5f651aed4ba4879ad574e9c6eb9fb5b92ed91e2c`;45652 bytes。
- 審查對象 TARGET `ad14418d903b26212dc9e98754f44aaa894375c8`;審查包所在 commit S5f-0 `695909f2f22ec17f97d4609f3fd28a5d146f252d`。
- **審查者原始判決:PASS**(阻擋 0、非阻擋 3)。報告第 1 節的附帶聲明原文:

  > **附帶聲明**:S5f-F1(logging 擷取選項 `--log-level` / `--log-disable` 等不在合約內)我判為非阻擋,理由是 TARGET 目前已提交的設定下,它能翻盤的情形全部落在已裁決的 scope 外 S-3。**但它與 (xvi) pytest `-W` 的納入理由同形**(3e-0 的 O-3 以「已提交設定若有 `error::X`,CLI 會蓋過它」納入合約,即使本 repo 當時實際能翻的也只有 S-3 類)。若裁決者以 O-3 / (xvi) 的同一標準看待它(與 S5e-F1 以 (xvii) 標準看待 `--pdb` 同型),本判決應改為 **FAIL**。判斷依據寫在 S5f-F1 的「為什麼判非阻擋」。

- 發現清單(報告第 3 節標題原文):
  - S5f-F1【非阻擋(請裁決)】logging 擷取選項(`--log-level` / `--log-disable` / `--log-cli-level` / `--log-file-level`)能讓失敗的斷言變成 passed,TARGET 仍判 `"true"`;歸 S-3 的前提沒有機制守住,且與 (xvi) 的納入標準不一致
  - S5f-F2【非阻擋】POSIX 上 root 路徑本身含 `\` 時,固定全套永遠 unknown(4f 引入;與 4f 報告第 7 節第 3 點「判定不受影響」的敘述不符)
  - S5f-F3【非阻擋】`normalize_overrides` 的 docstring 對 pytest 的敘述過度概括:「pytest 解析 ini 的路徑值也不用 invocation dir」

### 45.2 裁決助手外部重現(隔離環境;非獨立審查 finding;非本 repo 帳本證據)

來源:Jeff 的 Station 5f-1 指令裁決第 4 點,照錄。

Linux + Python 3.11 + pytest 9.1.1 + TARGET 的 redlight.py / conftest.py:測試 test_quiet(caplog) 呼叫會發 WARNING 的 impl.run() 並斷言 caplog.records == [];
固定指令 ⇒ failed、run_state B;加 --log-level=ERROR ⇒ passed、run_state A、file_coverage == "true" ⇒ 會退紅。S5f-F1 情境一成立(屬 S-3)。

### 45.3 裁決(照錄)

1. 獨立審查者原始判決:PASS(阻擋 0、非阻擋 3),附帶聲明 S5f-F1 若以 (xvi) 標準看待則改為 FAIL。原始判決照錄。
   Jeff 裁定:S5f-F1 維持〈三十五〉35.1 第 6 點的 S-3 scope 邊界,不是目前 TARGET 的阻擋項 ⇒ Station 5f 最終結果 = PASS;不進 3g。
2. 理由:(xvi) 納入 authority,是因為 repo 有已提交的 filterwarnings 政策,CLI -W 可覆蓋該已提交的證據環境。
   TARGET 的 pyproject.toml 沒有提交 log_level / log_cli_level / log_file_level;--log-level 等能翻轉的,是依賴 pytest 預設 logging 擷取層級的測試,屬已裁定的 S-3。
   若未來 repo 提交 logging level 政策,CLI 覆蓋它即與 -W 同形,屆時必須重新納入 authority 合約。
   S5e-F1(--pdb)不依賴測試本身的環境相依性,與本項不同。
3. 登記追蹤項(寫在票 145「相關」段;本步不建立新票檔,稱「追蹤項」):
   - logging 鎖步絆線待辦(目前尚未 machine-enforced):後續追蹤項須新增測試,讀取已提交的 pyproject.toml(git show HEAD:pyproject.toml),
     斷言 [tool.pytest.ini_options] 尚未出現 log_level / log_cli_level / log_file_level(做法同 D4)。
     在該機器絆線實作並通過前,新增上述已提交 logging 政策的變更,不得視為已被 M1-a authority 覆蓋。此為程序約束,目前尚非機器 enforcement。
   - 一般化研究:以「實際生效的 option namespace 等於固定指令的解析結果」取代逐項列舉(可收斂 (xv)–(xix) 與 logging 族);獨立設計,不在 M1-a 處理。
   - S5f-F2:POSIX 上 root 路徑本身含 \ 時固定全套永遠 unknown(fail-closed 的可用性問題);並更正 4f 報告第 7 節第 3 點的敘述(在新紀錄更正,不回寫)。
   - S5f-F3:normalize_overrides docstring 對 pytest 解析基準的敘述過度概括(log_file 以 cwd 解析);屬文件準確度,不改 authority 語意。

---

## 四十六、Station 6 push 與 CI(FAIL)及 Station 3g 裁決（2026-10-03，Jeff）

### 46.1 push 紀錄

- 指令 `git push origin master`(無 force、無 `--no-verify`);輸出原文:

  ```
  To https://github.com/wusuowei-tw/monkeyleash
     84014ba..de36ebc  master -> master
  ```

- BASE `84014bae237a4741dae8ad18c6c041a3c3ef97b0` → `de36ebcbab284ef11064a9943b5191750482dd93`(S5f-1)。
- push 前 `git rev-list --left-right --count origin/master...HEAD` = `0 48`(原輸出以 tab 分隔);push 後 = `0 0`;工作樹兩次皆乾淨。

### 46.2 CI 失敗原文

來源:Jeff 自 GitHub Actions 貼回(淨室驗證步驟),照錄:

```
=== 框架自己的測試,在這個新 repo 裡跑一次 ===
框架測試在新 repo 裡不是全綠 —— 那些紅與新專案無關,會訓練人忽略訊號。框架測試只能斷言框架的性質。
    1 failed, 1904 passed, 4 skipped, 3 xfailed in 23.57s
    在新 repo 裡紅的:
      FAILED tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d4_the_committed_addopts_override_constant_matches_pyproject - AssertionError: b"fatal: path 'pyproject.toml' does not exist in 'HEAD'
Error: Process completed with exit code 1.
```

### 46.3 裁決助手外部重現

**隔離環境;非獨立審查 finding;非本 repo 帳本證據。** 來源:Jeff 的 Station 6-1 / 3g-0 指令(修正第二版),照錄:

- git clone 公開 repo(HEAD de36ebcbab284ef11064a9943b5191750482dd93),Linux + Python 3.11 + pytest 9.1.1,執行
  python .claude/portable/verify_gates.py <暫存目錄>:R1–R9 各擋下一次、權威層偵測正常;框架測試 1 failed, 1904 passed,
  失敗即上述 test_d4(與 CI 相同)。
- 淨室安裝出的 repo:沒有 pyproject.toml;其帳本最後一筆 session:run_state B、_completeness_problems 為空、
  override_ini None、inipath None、inifilename None、config_blobs 兩檔 worktree / head 皆 None;
  抽查 tests/test_apply_patches.py 等檔 file_coverage 皆 "unknown"。⇒ 第二層成立。

### 46.4 裁決(照錄)

1. Station 6 = FAIL。公開的紅 CI 保留,不撤回、不 force rewrite;後續以正常 commit 修好再 push。
2. 票 145 回 Station 3g-0;3g 同時處理兩層:
   (第一層)框架 self-test 錯置:tests/test_redlight.py::TestCollectionDefinitionCoverage::test_d4_the_committed_addopts_override_constant_matches_pyproject
     斷言宿主 repo(agent-gates)已提交的 pyproject.toml,違反「框架測試只能斷言框架的性質」;在淨室安裝的 repo 必紅。
   (第二層)downstream evidence-policy 可移植性:全新安裝的 repo 跑固定指令,所有檔案 file_coverage 永遠 unknown,既有紅永遠無法合法退休。
     這直接碰到 M1-a 的核心交付(框架裝到 downstream 後,可信的 pass 能否取得 true authority),屬票 145,不是之後再改善的可用性問題。
3. 設計原則(3g-0 須遵守):
   - 三類拆分:(a) Framework invariant —— 所有安裝都必須一致;框架 self-test 不得要求宿主 repo 剛好有 agent-gates 的 pyproject.toml。
     (b) Framework capability boundary —— 框架實際驗證 / 支援到哪裡(例:Python major.minor、pytest audited versions、known plugin / dist)。
     (c) Host evidence policy —— 宿主 repo 在 (b) 之內,自己選擇接受哪些已提交設定;必須來自宿主已提交、可審計的 policy / config,不得在執行當下自動猜測。
   - 最終可取得 authority 的集合 = Framework capability boundary ∩ Host 已提交 policy。host policy 只能收窄,不能擴張框架未驗證的能力。
   - 不得把「缺少 host policy」解讀成可信。狀態模型:新 repo 尚未建立 / 提交 evidence policy ⇒ unknown ⇒ 不得退紅(正確的 fail-closed);
     經框架初始化流程,宿主提交自己的 policy ⇒ 實際有效環境 == 宿主已提交 policy(且在 capability boundary 內)⇒ 才可能 true。
   - 不得修成「新 repo 沒有 pyproject.toml 也直接給 true」。
4. 驗收須包含 clean-room 兩正三負:
   - (正一)Uninitialized clean repo:框架測試本身全綠;host evidence authority 為 unknown(預期結果)。
   - (正二)Initialized + matching policy:提交合法 policy → 製造 red → 正常固定指令 → true → red 合法退休(端到端證據)。
   - (負一)Initialized + policy / environment mismatch(例:policy 認可某 override,實際不同)⇒ unknown,不能退休。
   - (負二)HEAD 有 policy,但 worktree 與 HEAD 不同(本地改了未 commit)⇒ unknown,不能退休。
   - (負三)worktree 有 policy,但 HEAD 根本沒有 policy(從未提交)⇒ unknown,不能退休。
5. 流程教訓:Station 6 push 前,clean-room verification(.claude/portable/verify_gates.py)成為固定 pre-push acceptance 項,不得只靠 GitHub CI 第一次發現。
6. Policy bootstrap trust root:policy 的 canonical location、schema bootstrap 與 policy 自身的 HEAD / worktree integrity 屬 framework invariant,
   不得由 policy 內容自行指定或自我授權。缺檔、未提交、worktree ≠ HEAD、schema / version 未知 ⇒ 只能 unknown。
   policy authority 內容必須由 HEAD committed blob 解析;worktree 僅用來做 HEAD / worktree identity check,不作為 authority policy 的內容來源
   (不得在比對相等後再把 worktree 檔案當 authority source)。

---

## 四十七、Station 3g 紅燈規劃

- 規劃檔:`docs/audits/2026-10-03-m1a-station3g-redlight-plan.md`。只規劃:未寫測試、未改 .py、未跑 pytest、未執行 verify_gates.py。
- BASELINE:`faf7cb47823e33b65c2a21ffd85db3dd416adea1`(S6-1)。
- 規劃結論摘要:
  - P1:淨室的 unknown 有三個各自獨立的來源 —— (viii) `COMMITTED_ADDOPTS_OVERRIDES`、(x) `CONFIG_FILE`、(xi) `COMMITTED_FILES` 的 pyproject 那一半。三者都是 agent-gates 的宿主事實(Host evidence policy),被寫成了框架常數。
    `KNOWN_PYTHON_VERSIONS` / `KNOWN_PYTEST_VERSIONS` / `KNOWN_DISTS` 屬能力邊界;`tests/conftest.py`、`_ROOT` 屬框架不變式。
  - P2:test_d4 錯在**位置**,不在語意(出貨檔讀宿主 HEAD)。另發現 P2-B:斷言 "true" 的正控依賴真實 Python 3.11 + pytest 9.1.1,在其他環境的下游會出現與下游無關的紅。
  - P3:canonical path 與 schema 屬框架常數;bootstrap 依 HEAD 存在 → HEAD blob → worktree identity → 由 HEAD blob 解析 → 與 runtime 比對;effective = 能力邊界 ∩ policy。
  - P6:新增 33 支(behavior-red 26、regression-lock 7);預期 collected 2090(以 S4F1 的 2057 為底,未實測)、本機 failed 26。
    負二、負三分別為 `test_g3_an_uncommitted_policy_state_is_not_full_coverage[worktree-differs]` / `[worktree-only]`(另有 test_status 鏈條版)。
- P8 待 Jeff 裁(各項選項、建議與理由見規劃檔 P8):
  1. policy 載體 —— 建議甲:獨立檔 `.agents/evidence-policy.json`。
  2. 誰解析 policy —— 建議 A:producer 從 HEAD blob 解析並記入 session。
  3. policy 列出能力邊界外的值 —— 建議 A:整份不合格 ⇒ unknown。
  4. test_d4 處置 —— 建議 C:框架推導測試 + verdict 時機器鎖步 + 宿主專用檔保留 agent-gates 自身鎖步(〈三十一〉裁決 3 只改適用位置)。
  5. 環境相依正控 —— 建議 A:在共用 driver 固定版本事實。
  6. 初始化 —— 建議 A:安裝器只寫非 canonical 範本 + decisions-pending + status 顯示 policy 狀態。

---

## 四十八、Station 3g 裁決與紅燈集合（2026-10-03，Jeff）

### 48.1 裁決(照錄;針對 S3g-0 560f618560ddac1a34e0e835b99a1e3a5cc7eda5 規劃檔 P8)

1. policy 載體:甲 —— 獨立檔 .agents/evidence-policy.json(JSON,schema "monkeyleash.evidence-policy" v1)。
2. 誰解析:A —— producer 依 I-3 從 HEAD committed blob 解析並記入 session 的 evidence_policy 欄;consumer 驗型別、identity、schema / version 後判定。
3. 界外值:A —— policy 任一欄位超出 framework capability boundary ⇒ 整份不合格 ⇒ unknown(不取交集、不靜默忽略)。
4. test_d4:C —— 框架推導規則以 fixture 測(TestAddoptsDerivation)+ verdict 時機器鎖步;agent-gates 自身「policy ↔ pyproject」鎖步移到宿主專用檔
   tests/test_host_evidence_policy.py(manifest 標 skip)。
   〈三十一〉裁決 3 修訂(Jeff 明文):語意不變(git show HEAD、不得以 tmp repo / 寫死字串代替、讀取失敗 ⇒ 失敗、不得 skip、唯讀),
   適用位置由「出貨的 tests/test_redlight.py」改為「宿主專用、不出貨的 tests/test_host_evidence_policy.py」。原 test_d4 於 4g 刪除。
5. 環境相依正控(P2-B):A —— 3g / 4g 一併在共用 driver 固定版本事實(授權於 4g)。
6. 初始化:A —— 安裝器只在非 canonical 路徑 .agents/evidence-policy.template.json 寫範本(內容 = B 常數)+ decisions-pending + status 顯示 policy 狀態;
   不做從本機觀察值產草稿的指令。
7. 補充(裁決助手):
   - 4g 驗收須在本機實跑一次 python .claude/portable/verify_gates.py <session scratchpad>/verify-gates,照錄五情境(正一、正二、負一、負二、負三)各一行結果,
     並證明本 repo .dev/ 兩本帳本前後 bytes 與 sha256 不變。規劃檔 #33 只證明情境有接線,不證明情境結果。
   - 3g-1 須把 tests/test_host_evidence_policy.py 登記進 .agents/portable-manifest.txt(skip),否則 test_upstream_manifest 會多紅一支、紅燈集合不準。
   - 其餘未裁事項照規劃檔「不需裁、已依原則定案」段。

### 48.2 預期集合(33 支,完整 nodeid)

預期紅集合(behavior-red,26 支,在 S3G1 上必須失敗):

- tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_a_repo_without_a_policy_is_not_full_coverage
- tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_uncommitted_policy_state_is_not_full_coverage[worktree-only]
- tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_uncommitted_policy_state_is_not_full_coverage[worktree-differs]
- tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_uncommitted_policy_state_is_not_full_coverage[staged-only]
- tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_uncommitted_policy_state_is_not_full_coverage[deleted-in-worktree]
- tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[malformed-json]
- tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[unknown-schema]
- tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[unknown-version]
- tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[unknown-key]
- tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_an_unknown_policy_document_is_not_full_coverage[missing-field]
- tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_a_policy_outside_the_canonical_path_is_not_full_coverage
- tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_the_producer_records_the_policy_identity
- tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_environment_mismatch_is_not_full_coverage[override]
- tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_environment_mismatch_is_not_full_coverage[narrowed-dist]
- tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[strict-markers]
- tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[strict-config]
- tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[o-flag]
- tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[override-ini-eq]
- tests/test_redlight.py::TestAddoptsDerivation::test_g3_overrides_are_derived_from_committed_addopts[no-addopts]
- tests/test_redlight.py::TestAddoptsDerivation::test_g3_a_policy_disagreeing_with_the_committed_addopts_is_not_full_coverage
- tests/test_host_evidence_policy.py::test_the_committed_policy_matches_the_committed_pyproject
- tests/test_status.py::TestEvidencePolicyChain::test_g3_no_policy_does_not_retire_a_known_red
- tests/test_status.py::TestEvidencePolicyChain::test_g3_an_uncommitted_policy_does_not_retire_a_known_red[worktree-only]
- tests/test_status.py::TestEvidencePolicyChain::test_g3_an_uncommitted_policy_does_not_retire_a_known_red[worktree-differs]
- tests/test_status.py::TestEvidencePolicyChain::test_g3_a_policy_environment_mismatch_does_not_retire_a_known_red
- tests/test_verify_gates.py::test_every_evidence_policy_scenario_is_wired

預期綠集合(regression-lock,7 支,在 S3G1 上必須通過):

- tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_policy_content_is_not_read_from_the_worktree
- tests/test_redlight.py::TestEvidencePolicyBootstrap::test_g3_a_matching_committed_policy_is_full_coverage
- tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_cannot_widen_the_capability_boundary[python]
- tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_cannot_widen_the_capability_boundary[pytest]
- tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_cannot_widen_the_capability_boundary[dist]
- tests/test_redlight.py::TestEvidencePolicyBoundary::test_g3_a_policy_cannot_widen_the_capability_boundary[config-file]
- tests/test_status.py::TestEvidencePolicyChain::test_g3_a_matching_committed_policy_retires_the_red

- 預期固定全套:collected 2090(以 S4F1 實測的 collected 2057 為底;S5f-0 到 S3G0 都沒有改測試)。
- 本機 Windows 預期:26 failed、2058 passed、3 skipped、3 xfailed。

---

## 四十九、Station 3g 紅燈證據

- 報告:`docs/audits/2026-10-03-m1a-station3g-redlight.md`。
- S3G1 `2737e02c64b88f4d0a39bdafbea2f3776993cf2b`:三個測試檔各只在檔尾新增一個 hunk(`-U0` 標頭 `@@ -2144,0 +2145,363 @@`、`@@ -2858,0 +2859,159 @@`、`@@ -291,0 +292,24 @@`;沒有刪除行);
  新檔 `tests/test_host_evidence_policy.py`;`.agents/portable-manifest.txt` 恰新增一行 `tests/test_host_evidence_policy.py skip`;另改票 145。commit 前只跑 py_compile。
- 固定全套(在 S3G1 上只跑一次):exit 1;摘要行原文 `26 failed, 2058 passed, 3 skipped, 3 xfailed in 243.99s (0:04:03)`(collected 2090)。
- 失敗集合恰為〈四十八〉48.2 的 26 支 behavior-red。7 支 regression-lock 與全部既有測試都通過(帳本第 22 行逐支相符)。
  每支都失敗在破壞組 / 主斷言,對照組與情境斷言皆通過(報告第 4 節逐支表)。
- 帳本 H9 → H10 只追加:兩本前段 sha256 = H9r / H9s;test-runs 2733 → 2780 行(+47 = 46 + 新檔 1)、test-sessions 21 → 22 行(+1)。
- status:red 恰為 `tests/test_host_evidence_policy.py`、`tests/test_redlight.py`、`tests/test_status.py`、`tests/test_verify_gates.py`;最近一次 run B(collected 2090)。
- commit(回填):S3G1 `2737e02c64b88f4d0a39bdafbea2f3776993cf2b`;S3G2(證據)`7a15ea081da1bf23cc79e04aef76065438f65219`。

---

## 五十、Station 3g-1b 補紅燈

### 50.1 裁決(照錄)

1. Station 3g 現有 26 behavior-red + 7 regression-lock(S3G2 7a15ea081da1bf23cc79e04aef76065438f65219)= PASS / ACCEPTED。
   〈四十八〉48.1 第 6 點的兩項設計(安裝範本、status policy 狀態行)沒有對應紅燈;缺口處理選 A:先補 3g-1b,再進 4g。
2. 裁決助手外部驗證(隔離環境;非本 repo 帳本證據;寫進票並標明來源):
   - Linux + Python 3.11 + pytest 9.1.1,以 S3G1 2737e02c64b88f4d0a39bdafbea2f3776993cf2b 的測試檔:3g 新增 33 支為 26 failed / 7 passed,失敗集合同〈四十八〉48.2。
   - 以 S3G1 的樹跑 verify_gates.py:淨室安裝的 repo 不含 tests/test_host_evidence_policy.py;淨室框架測試 26 failed(25 支出貨的 3g 紅燈 + 原 test_d4)、1911 passed;
     7 支 regression-lock 在淨室為綠。
   - 既有事實:install.main 既有流程即以 git add -A + commit 提交安裝結果(.claude/portable/install.py 約 :516–:520);本輪紅燈不得把「範本已提交」列為要求。
3. 本輪新增紅燈(全部 behavior-red;在 S3G2 上必須失敗):
   tests/test_install.py(檔尾新增 class TestEvidencePolicyTemplate):
     I1 test_g3_install_writes_the_template_outside_the_canonical_path:install.main(<tmp 新 repo>) 後,
        .agents/evidence-policy.template.json 存在;.agents/evidence-policy.json 不存在。
        並以真實 producer / consumer 驗證:該 repo(安裝後、未建立 canonical policy)的固定全套 session,其 file_coverage 不得為 "true"
        —— 範本位於非 canonical path,無論是否 tracked / committed,都不得成為 evidence authority。
        (不得斷言範本「已提交」或「未提交」;那不是本票裁決的需求。)
     I2 test_g3_the_template_lists_exactly_the_capability_boundary:範本為 schema "monkeyleash.evidence-policy" v1;python_versions / pytest_versions / dists
        分別等於 redlight 的框架能力邊界常數;config_file 屬 FRAMEWORK_CONFIG_FILES。(常數名稱以 4g 實作為準,測試以 getattr 取得;取不到 ⇒ 失敗。)
     I3 test_g3_decisions_pending_asks_to_initialize_the_policy:docs/decisions-pending.md 含 evidence policy 初始化的待決項(含 canonical 路徑 .agents/evidence-policy.json)。
   tests/test_status.py(檔尾新增 class TestEvidencePolicyStatusLine;參數化 6 案;經真 git tmp repo):
     test_g3_status_shows_the_policy_state[<state>],state ∈ uninitialized / uncommitted / worktree-differs / unknown-schema / outside-boundary / valid;
     status 輸出須有一行以 "evidence policy: " 開頭,其後依序為:未初始化 / 未提交 / 工作樹與 HEAD 不同 / 格式不明 / 超出框架能力邊界 / 有效,
     且該行帶 (source: .agents/evidence-policy.json)。
     [unknown-schema] 必須在同一支測試內依序涵蓋四種已提交文件:JSON malformed、schema 名稱不認得、version 不支援、必要欄位缺失 / 型別錯誤;
     每一種都須顯示「格式不明」(逐一斷言,不得只測一種)。
   ⇒ 新增 9 支;預期固定全套:collected 2099;failed 35(既有 26 + 新 9);passed 2058;skipped 3;xfailed 3。

### 50.2 外部驗證(來源)

50.1 第 2 點為裁決助手在隔離環境的外部驗證,來源是 Jeff 的 Station 3g-1b 指令(修正版),照錄於上。
**非獨立審查 finding;非本 repo 帳本證據。**

### 50.3 新增 9 支(完整 nodeid;全部 behavior-red,在 S3G1B 上必須失敗)

- tests/test_install.py::TestEvidencePolicyTemplate::test_g3_install_writes_the_template_outside_the_canonical_path
- tests/test_install.py::TestEvidencePolicyTemplate::test_g3_the_template_lists_exactly_the_capability_boundary
- tests/test_install.py::TestEvidencePolicyTemplate::test_g3_decisions_pending_asks_to_initialize_the_policy
- tests/test_status.py::TestEvidencePolicyStatusLine::test_g3_status_shows_the_policy_state[uninitialized]
- tests/test_status.py::TestEvidencePolicyStatusLine::test_g3_status_shows_the_policy_state[uncommitted]
- tests/test_status.py::TestEvidencePolicyStatusLine::test_g3_status_shows_the_policy_state[worktree-differs]
- tests/test_status.py::TestEvidencePolicyStatusLine::test_g3_status_shows_the_policy_state[unknown-schema]
- tests/test_status.py::TestEvidencePolicyStatusLine::test_g3_status_shows_the_policy_state[outside-boundary]
- tests/test_status.py::TestEvidencePolicyStatusLine::test_g3_status_shows_the_policy_state[valid]

附註:
- `[unknown-schema]` 逐一涵蓋五份已提交文件。「必要欄位缺失 / 型別錯誤」那一類兩種都測:缺 `dists`、`python_versions` 為字串。
- I1 為了讓「範本不得成為 authority」不被其他 unknown 原因遮蔽,在安裝出的 repo 另提交一份 `pyproject.toml`(以 `--no-verify` 提交,同 install.main 自己的 commit),再驅動真實 producer。

### 50.4 紅燈證據

- 報告:`docs/audits/2026-10-04-m1a-station3g-1b-redlight.md`。
- S3G1B `83258dd9ab415a793eaf2b140a9e34c5b91069f2`:`tests/test_install.py`、`tests/test_status.py` 各只在檔尾新增一個 hunk(`-U0` 標頭 `@@ -463,0 +464,205 @@`、`@@ -3017,0 +3018,117 @@`;沒有刪除行);另改票 145。commit 前只跑 py_compile。
- 固定全套在 S3G1B 上跑了兩次:
  - (a) 第一次:工作樹含 3 個外來 docs 變更(` M docs/agents/friction-log.md`、`?? …/146-…`、`?? …/147-…`)⇒ **不作為正式證據**。
    摘要行原文 `35 failed, 2058 passed, 3 skipped, 3 xfailed in 351.04s (0:05:51)`;停手報告 `.dev/reports/2026-10-04T112500Z-ticket145-station3g-1b-stop.md`。
  - (b) 依 Jeff 裁決 B,外來 3 檔以 `git stash push -u -m jeff-mods-recon-20261004` 收起後重跑一次 ⇒ **正式證據**。
    跑前、跑後 `git status --porcelain` 皆無輸出。exit 1;摘要行原文 `35 failed, 2058 passed, 3 skipped, 3 xfailed in 351.00s (0:05:50)`(collected 2099)。
- 失敗集合恰為〈四十八〉48.2 的 26 支 + 50.3 的 9 支,沒有多、也沒有少;與第一次執行逐條相同。其餘 2058 支(含 3g 的 7 支 regression-lock)通過。
- 新 9 支的失敗點:I1 / I2 在 `test_install.py:617` / `:648`(範本不存在);I3 在 `:667`(decisions-pending 沒有 evidence policy);
  status 6 案都在 `test_status.py:3071`(`evidence policy:` 行 0 行);`[unknown-schema]` 在第一份文件 `malformed-json` 就失敗。
- 帳本 H11 → H12 只追加:兩本前段 sha256 = H11r / H11s;test-runs 2827 → 2874 行(+47)、test-sessions 23 → 24 行(+1)。
- commit(回填):S3G1B `83258dd9ab415a793eaf2b140a9e34c5b91069f2`;S3G1B-2(證據)`3eb112b1cafb399f2757274264281436729e7e42`。
  (F-036:本行原文為「S3G1B-2(證據)於下一次提交回填」;2026-10-04 於 S4G3 回填。)

---

## 五十一、Station 4g 修正

### 51.1 裁決(照錄要點;Jeff,2026-10-04)

1. Station 3g-1b = PASS / ACCEPTED(證據 S3G1B-2 `3eb112b1cafb399f2757274264281436729e7e42`)。4g plan = APPROVED WITH 2 FIXES。
   4g 期間外來 3 檔 stash,票 146 / 147 視窗暫停。三段式:S4G1 實作 → S4G2 本機驗收 → S4G3 docs-only;POSIX 外部 clean-room 由裁決助手執行,通過後另以 S4G4 升級。
2. R3 擋下後續作:
   - R3 擋下屬預期的 fail-closed 行為(非產品缺陷);允許 `git restore` 丟棄 redlight.py 半成品。
   - 編輯規矩:漸進遷移或一次 Write;每次寫入 redlight.py 後以 status.py 為 import 探針;不得修改 `content_hash` 及其呼叫的函式。
   - 第 7 鍵 `committed_addopts` = APPROVED:`evidence_policy` 為 7 鍵。`committed_addopts` 的語意:None = 取得或解析失敗;`""` = config 合法但沒有 addopts;`str` / `list[str]` = 原值。
   - `addopts_overrides(value)` 只接受 `str` / `list[str]`,不讀 git / 檔案。
3. 淨室正二不成立後續作:
   - 修法 B = APPROVED:producer 先判欄位是否存在、再解讀值。
   - A = REJECTED:在 consumer 把 None 當 [],會把「事實取不到」當成「確定沒有 override」⇒ fail-open。
   - C = REJECTED:只是繞過缺陷。
   - 授權新增 T1 + T2;負一到負三須在正二修好後的同一次淨室執行中重新驗證。

### 51.2 證據

- 報告:`docs/audits/2026-10-04-m1a-station4g-fix.md`。
- commit:
  - S4G1 `f4fa0418aa037f95ef7d1f59c6fe6a812a80414c`(實作);
  - S4G1B `f581a02a5b7a65c8eaf150bf7231acc464f99072`(T1 / T2;`tests/test_redlight.py` 檔尾一個 hunk `@@ -2492,0 +2493,42 @@`,只有 + 行);
  - S4G1C `8e7775526e462d984abb0992ed74c1e1aa3648dd`(`tests/conftest.py` 的 producer 修正);
  - S4G3(證據提交)`2fe52d0ea7ec2d465768b5e907d64726bb1d9256`。
    (F-036:本行原文為「S4G3(本次證據提交)於下一次提交回填。」;2026-10-04 於 S4G4 回填。)
  - S4G4(POSIX 驗收記錄與狀態升級)於下一次提交回填。
- 第一次淨室(S4G1):正二不成立(`file_coverage=unknown`)。成因:pytest 9.1.1 沒給 `-o` 時 `override_ini` 為 None,producer 原樣落帳,consumer (viii) 比 `None != []`。該次負一到負三不作為證據。
- 裁決助手外部驗證(Linux,Python 3.11 + pytest 9.1.1;隔離環境;**非本 repo 帳本證據**),照錄於報告第 3 節。
- S4G1B 紅燈全套(只跑一次):`1 failed, 2093 passed, 3 skipped, 3 xfailed in 342.54s (0:05:42)`(collected 2100)。唯一的 FAILED 為 T1,失敗行為 `assert 'unknown' == 'true'`。
- S4G1C 本機全套(只跑一次):`2094 passed, 3 skipped, 3 xfailed in 341.79s (0:05:41)`(collected 2100、0 failed)。
- status:`evidence policy: 有效`;`tests red under ticket 145: (無)`;run 事實未知 0;原本的 5 個紅檔都在 green。
  - 「有效」只代表 policy 文件本身有效,不代表 runtime 一定取得 true authority(報告第 8 節第 2 點)。
- 第二次淨室(S4G1C;同一次執行):兩正三負全部成立。正二 `file_coverage=true`、`green=tests/test_evidence_probe.py`;淨室框架測試 `1944 passed, 7 skipped, 3 xfailed`。
- 帳本只追加:
  - B13 → B14:test-runs 2921 → 2968、test-sessions 25 → 26;
  - B14 → 本次:test-runs 2968 → 3015、test-sessions 26 → 27;
  - 兩次前段 sha256 都等於基準。
  - 淨室驗收前後,本 repo 兩本帳本的 bytes 與 sha256 都不變。
- 殘餘與未證明:見報告第 8 節。其中 status 行不檢查 addopts 鎖步、淨室負情境不斷言成因、logging 鎖步絆線,**目前尚未 machine-enforced**。

### 51.3 POSIX 外部 clean-room 驗收

> **舊文字(F-036,保留不刪)**:本節原文為 ~~`待執行(裁決助手)。`~~;2026-10-04 S4G4 依 Jeff 裁決改為下方照錄段落。
> Jeff 裁決(2026-10-04):Station 4g 本機驗收(S4G2,見 S4G3 `2fe52d0ea7ec2d465768b5e907d64726bb1d9256`)與裁決助手 POSIX 外部驗收皆 PASS ⇒ Station 4g = PASS / COMPLETED;下一站 5g 獨立審查。

POSIX 外部 clean-room 驗收（裁決助手；隔離環境；非本 repo 帳本證據）——2026-10-04 約 18:50 ET
- 環境：Linux，Python 3.11.16，pytest 9.1.1，anyio 4.15.0。
- 受測樹：以公開 repo de36ebcbab284ef11064a9943b5191750482dd93 的 clone 為底，覆蓋 Windows 工作樹於 S4G3 時點的 12 個程式 / 測試 / 設定檔（.claude/hooks/redlight.py、.claude/portable/install.py、.claude/portable/status.py、.claude/portable/verify_gates.py、tests/conftest.py、tests/test_redlight.py、tests/test_status.py、tests/test_install.py、tests/test_verify_gates.py、tests/test_host_evidence_policy.py、.agents/portable-manifest.txt、.agents/evidence-policy.json；CRLF→LF）。docs 未同步（不影響程式行為）。
- verify_gates.py：R1–R9 各擋下一次；權威層偵測三項成立；淨室框架測試 1945 passed、4 skipped、3 xfailed、0 failed；evidence policy 兩正三負全部成立：
    正一 未初始化 成立（35 個框架測試檔皆 unknown；evidence policy: 未初始化）
    正二 已初始化且相符 成立（rc 1→0；file_coverage=true；green=tests/test_evidence_probe.py；evidence policy: 有效）
    負一 policy / 環境不符 成立（file_coverage=unknown；紅仍在）
    負二 HEAD 有、工作樹不同 成立（file_coverage=unknown；evidence policy: 工作樹與 HEAD 不同）
    負三 工作樹有、HEAD 沒有 成立（file_coverage=unknown；evidence policy: 未提交）
- 宿主固定全套（Linux）：collected 2100；2084 passed、13 failed、3 xfailed。13 支為 tests/test_gate.py::TestAuthorityLayerIsWired::test_this_repo_itself_is_wired 與 tests/test_known_items_regression.py 的 12 支；同一沙盒在 4g 之前的已推送版本 de36ebc 上同樣恰為這 13 支失敗 ⇒ 屬沙盒環境因素（推測：clone 未設 hooksPath、缺本機私有資料），與 4g 無關。evidence 相關 5 檔（test_redlight / test_status / test_install / test_verify_gates / test_host_evidence_policy）全過。
- 先前的 S4G1 Linux 重現（正二不成立、成因 override_ini 為 None）與修法 B 原型驗證，見〈五十一〉51.1 / 證據報告。
- 結論：POSIX 外部 clean-room 驗收 PASS。

---

## 五十二、Station 5g 審查包

- Jeff 裁決(2026-10-04):Station 4g = PASS / COMPLETED(S4G4、S4G5 已提交);S4G5 = review baseline;Station 5g-0 = APPROVED TO BUILD REVIEW PACKAGE。
- 審查包:`docs/audits/2026-10-04-m1a-station5g-review-package.md`。
  - 347652 bytes / 5820 行;SHA-256 `c88ddd71af4fd4f3038d0363c5372a51951c6f256aea9ac8bfcd75c00cfbcfb5`;
  - staged blob `26141bdc40a83a0f2f85da97eefb64ace226cb4d`。
- 身分(13 個完整 SHA):

| 代號 | 完整 SHA |
|---|---|
| BASE(已推送、5f 審過的最後狀態 S5f-1) | `de36ebcbab284ef11064a9943b5191750482dd93` |
| S6-1 | `faf7cb47823e33b65c2a21ffd85db3dd416adea1` |
| S3g-0 | `560f618560ddac1a34e0e835b99a1e3a5cc7eda5` |
| S3G1(3g 主紅燈基線:33 支 = 26 + 7) | `2737e02c64b88f4d0a39bdafbea2f3776993cf2b` |
| S3G2 | `7a15ea081da1bf23cc79e04aef76065438f65219` |
| S3G1B(3g-1b 補紅燈基線:+9 behavior-red) | `83258dd9ab415a793eaf2b140a9e34c5b91069f2` |
| S3G1B-2 | `3eb112b1cafb399f2757274264281436729e7e42` |
| S4G1 | `f4fa0418aa037f95ef7d1f59c6fe6a812a80414c` |
| S4G1B(T1/T2) | `f581a02a5b7a65c8eaf150bf7231acc464f99072` |
| TARGET(S4G1C;最後一個程式 commit) | `8e7775526e462d984abb0992ed74c1e1aa3648dd` |
| S4G3 | `2fe52d0ea7ec2d465768b5e907d64726bb1d9256` |
| S4G4 | `b127ae016ce6a7a7d096742e5771f1e6d328f52a` |
| REVIEW_HEAD(S4G5) | `b5db3734f6795d8a371e4f58b172e0a8ffb066eb` |

- 數量用語(審查包與審查報告一律照此):
  - 3g(S3G1)新增 33 支 = 26 behavior-red + 7 regression-lock;
  - 3g-1b(S3G1B)再新增 9 支 behavior-red;
  - 3g / 3g-1b 合計 42 支 = 35 behavior-red + 7 regression-lock;這 42 支在 4g 都不得被改動;
  - 4g 另合法新增 T1(behavior-red)+ T2(regression-lock)於 S4G1B。
- S5g-0(審查包 commit)`5e096acb899b3370f16018199627784af71b788e`。
  (F-036:本行原文為「S5g-0(審查包 commit):記錄 5g 結果時回填。」;2026-10-04 於 S5g-1 回填。)

---

## 五十三、Station 5g 獨立審查（審查者 PASS；依 Jeff 裁決 FAIL）與 Station 3h 裁決（2026-10-04，Jeff）

### 53.1 審查報告

- 路徑 `docs/audits/2026-10-04-m1a-station5g-review.md`;raw = repo 副本(與審查者原檔 `.scratch/m1a-s5g/review-report.md` 以 `cmp` 逐位元組相同,無任何改動);
  sha256 `8399be264fafa82d62bb3294762d17835b4429850aca68c57c545883adfd0a49`;28223 bytes。
- 審查對象 TARGET `8e7775526e462d984abb0992ed74c1e1aa3648dd`;審查包所在 commit S5g-0 `5e096acb899b3370f16018199627784af71b788e`。
- **審查者原始判決:PASS**(blocker 0、major 0、minor 2、nit 3)。
- Findings(報告第 2 節;一行摘要,不改寫結論):
  - S5g-F1【minor;G7(+G8)】`policy_state` 不查 addopts 鎖步;框架 pyproject 範本(addopts 帶 `--strict-markers`)+ policy 範本(`committed_overrides: []`)原樣採用 ⇒ status 顯示「有效」但每次固定全套都是 unknown,紅燈永遠不退且無訊號(fail-closed)。
  - S5g-F2【minor;G13 / G1 / G6;需要重現】`_ROOT` 不是 git toplevel 時,`rev-parse HEAD:<path>` 以 tree 根為基準、`hash-object <path>` 以 cwd 為基準;toplevel 已提交同內容 policy、子目錄放未提交副本 ⇒ 可得 `"true"`(內容等於某個已提交 blob;完整性成立,位置不成立)。
  - S5g-F3【nit;G3】pytest 9 原生 `[tool.pytest]`(無 `ini_options`)⇒ `_committed_addopts` 回 None ⇒ 永遠 unknown;status 仍顯示「有效」;fail-closed,H 段殘餘清單未列。
  - S5g-F4【nit;G12;需要重現】`.gitattributes` 的 clean filter 可讓 `pyproject.toml` / `tests/conftest.py` 工作樹 ≠ HEAD 但 `hash-object` 相等 ⇒ (xi) 誤判一致;policy 本身不受影響;BASE 已存在。
  - S5g-F5【nit;G9】正二不成立時負一~負三仍印「成立 ✓」;負情境的判別力完全來自同次執行中正二成立的差分,程式沒有把這個耦合寫進輸出。

### 53.2 裁決助手外部重現(隔離 Linux 環境;Python 3.11 + pytest 9.1.1;非獨立審查 finding;非本 repo 帳本證據)

來源:Jeff 的 Station 5g-1 指令,照錄。

- 事實層：建 git repo R，於 R 最上層提交合法 policy、pyproject.toml、tests/conftest.py；於 R/sub 放三份位元組相同、從未提交的副本（git ls-files 在 sub 下為空）。以 TARGET 的 redlight 讀 R/sub：evidence_policy_facts 的 head == worktree 成立、committed_addopts 取得、committed_blobs 兩檔 head == worktree、policy_state 顯示「有效」。
- 端到端：以 tests/test_redlight.py 的既有 helper（_g_default_root、_g_coverage）在 TARGET 上模擬固定全套，root = parent/sub ⇒ file_coverage == "true"（原型測試失敗於 assert got != "true"）。S5g-F2 為真，且可取得 true authority。
- 修法原型：redlight 新增「root 必須是 git 最上層」檢查（git -C <root> rev-parse --show-prefix 為空；不是 ⇒ evidence_policy_facts 與 committed_blobs 全記 None）。套用後上述原型轉為非 true；「root 為最上層、policy 正常提交」原型仍為 true；evidence 相關 5 檔共 279 支全過。

### 53.3 裁決(照錄)

1. Station 5g：獨立審查者判決 PASS（blocker 0、major 0、minor 2、nit 3）；Jeff acceptance = FAIL。理由：S5g-F2 違反〈四十六〉46.4 第 6 點與 I-3 —— canonical policy 必須是宿主 evidence root 對應路徑上、已提交的 HEAD blob；未提交 ⇒ unknown。現行 git rev-parse HEAD:<path> 以 git 最上層為基準、git hash-object <path> 以 root 為基準；root 不是 git 最上層時，被驗證的 HEAD 物件與實際使用的工作樹物件不是同一個邏輯路徑（identity 錯位），內容相同即可取得 true。
2. 修法方向：evidence root 必須就是 git 最上層（git -C <root> rev-parse --show-prefix 為空；與「resolved root == git rev-parse --show-toplevel」等價，但不需比對路徑字串）；不是 ⇒ policy 事實與 (xi) 的 blob 事實皆記 None ⇒ unknown ⇒ 不得退紅。框架目前明確只支援「一個 host evidence root = 一個 Git 最上層」；monorepo 子專案作為 evidence root 屬另案設計，不在本票。
3. Station 3h 紅燈至少兩支（皆經真實 conftest producer、真 git repo）：
   H1 behavior-red：git 最上層已提交合法 policy、pyproject.toml、tests/conftest.py；root = <最上層>/sub，三份位元組相同的副本只在工作樹、從未提交 ⇒ file_coverage 不得為 "true"。
   H2 regression-lock：root 本身就是 git 最上層，policy 正常提交、worktree = HEAD ⇒ 仍為 "true"。
   巢狀獨立 repo 的情境不在本輪。
4. S5g-F1、S5g-F3、S5g-F4、S5g-F5 列追蹤項（目前尚未 machine-enforced），不阻擋本輪；S5g-F1 列下一張票優先，須以機制處理 status 訊號（例：status 多一狀態，重用 verdict 的鎖步），不只改文字。
5. 流程：5g-1 記錄 → Jeff 切 tickets → 3h 紅燈 → Jeff 切 implement → 4h 最小修正（含 Windows 全套、本機 clean-room、裁決助手 POSIX）→ 5h 獨立審查（只審 3h/4h 增量）→ Station 6。

### 53.4 commit

- S5g-1(本節與審查報告入庫)`3a9200c03bb8493ab5a789d4c4157a7b38392e79`。
  (F-036:本行原文為「S5g-1(本節與審查報告入庫)於下一次提交回填。」;2026-10-04 於 S3H2 回填。)

---

## 五十四、Station 3h 紅燈證據

- Jeff 裁決(2026-10-04):S5g-1 = accepted;Station 3h plan = APPROVED。
- 報告:`docs/audits/2026-10-04-m1a-station3h-redlight.md`。
- S3H1 `7621e3ce8604ab72ab2f3fb3257cb1181b8a126e`:`tests/test_redlight.py` 檔尾一個 hunk `@@ -2534,0 +2535,42 @@`,只有 + 行;新增 `class TestEvidenceRootIsGitToplevel`,既有 helper 只呼叫、不修改。commit 前只跑 py_compile。
- 新增 2 支(完整 nodeid):
  - H1 behavior-red(在 S5g-1 上必須失敗):`tests/test_redlight.py::TestEvidenceRootIsGitToplevel::test_h3_a_parent_committed_policy_does_not_authorize_a_subdirectory_root`
  - H2 regression-lock(在 S5g-1 上必須通過):`tests/test_redlight.py::TestEvidenceRootIsGitToplevel::test_h3_a_git_toplevel_root_with_a_committed_policy_is_full_coverage`
- 紅燈全套(在 S3H1 上只跑一次;外來 3 檔已 stash,跑前跑後 `git status --porcelain` 皆無輸出):exit 1;
  摘要行原文 `1 failed, 2095 passed, 3 skipped, 3 xfailed in 409.36s (0:06:49)`(collected 2102)。
  唯一的 FAILED 為 H1,失敗行 `tests\test_redlight.py:2567: AssertionError`(`assert 'true' != 'true'`);H2 在 2095 passed 之內。
- 帳本只追加:兩本前段 sha256 = Step 0 基準(`9fa98cc7…` / `27cccd2c…`);test-runs 3015 → 3062 行(+47)、test-sessions 27 → 28 行(+1)。
  跑後全檔記為 B15:test-runs 822547 bytes、`49fc32bc88ad7eb93840e070154953980fa40122388c2fce49645b411a254789`;
  test-sessions 12909484 bytes、`0539883a5548a9032ed0877aab4614bdde6fd748103a3db2524de99e9c589674`。
- 程序紀錄(Jeff 程序註記,照錄要點):S5g-1 由 5g 審查 session 執行(審查報告在 S5g-1 前已完成,RR = `8399be264fafa82d62bb3294762d17835b4429850aca68c57c545883adfd0a49`),
  不影響已凍結的 5g 審查結果,但該 session 不得擔任 5h 審查者;S5g-1 回報檔名的時間戳與實際提交時間不符,之後 `.dev/reports/` 檔名一律用實際 UTC 時間。
  本輪 3h 亦由同一 session 執行。
- commit:S3H1 `7621e3ce8604ab72ab2f3fb3257cb1181b8a126e`;S3H2(本節與證據報告)`66140896d03f32c4df73be01b2aaeb48353e0510`。
  (F-036:本行原文為「S3H2(本節與證據報告)於下一次提交回填。」;2026-10-05 於 S4H3 回填。)

---

## 五十五、Station 4h 修正

### 55.1 裁決(照錄要點;Jeff,2026-10-05)

- Station 3h = PASS / ACCEPTED;Station 4h plan = APPROVED;H1 / H2 不准修改;最小修正只動 redlight.py。
- 三段式:S4H1 實作 → S4H2 本機驗收 → S4H3 docs-only(只能宣稱本機驗收通過;待 POSIX 外部驗收)。POSIX 由裁決助手執行,通過後另以 S4H4 升級。

### 55.2 證據

- 報告:`docs/audits/2026-10-05-m1a-station4h-fix.md`。
- S4H1 `ea6aba6452668982fee56f7a2f0faf2cd720ca6d`:只改 `.claude/hooks/redlight.py`(+25 行,0 刪除)。
  - `:726` 新增 `_root_is_toplevel(root)`(`git -C <root> rev-parse --show-prefix` 為空才 True;失敗 ⇒ False);
  - `:752` / `:755` `committed_blobs`:不是最上層 ⇒ 每個路徑記 `{"worktree": None, "head": None}`;
  - `:868` `evidence_policy_facts`:不是最上層 ⇒ 全 None;
  - 兩個函式 docstring 補 I-3 位置不變式。
  - 未改 consumer、`policy_state` 判定字串、conftest、status / install / verify_gates、任何測試;`content_hash` 未動。
  - 兩刀,每刀後 status.py 探針;皆無「redlight.py 無 run 事實讀取」。
- S4H2 本機固定全套(S4H1 上只跑一次;外來 3 檔已 stash):exit 0;`2096 passed, 3 skipped, 3 xfailed in 380.00s (0:06:19)`(collected 2102、0 failed)。H1 由紅轉綠,H2 維持綠。
- 帳本只追加:前段 sha256 = B15;test-runs 3062 → 3109(+47)、test-sessions 28 → 29(+1)。
- status:`evidence policy: 有效`;`tests red under ticket 145: (無)`;run 事實未知 0;`tests/test_redlight.py` 在 green。
- 淨室(verify_gates;同一次執行):R1–R9 各擋下一次、權威層偵測三項成立、淨室框架測試 `1946 passed, 7 skipped, 3 xfailed`;兩正三負全部成立,正二 `file_coverage=true`、`green=tests/test_evidence_probe.py`。
  本 repo 兩本帳本前後 bytes 與 sha256 都等於 V0(test-runs 834066 / `5f0ffa92…`;test-sessions 13647838 / `74757aa6…`)。
- 裁決助手 Linux 預演(來源:Jeff 的 Station 4h 指令;隔離環境;非本 repo 帳本證據):H1 紅轉綠、H2 維持綠;evidence 相關 5 檔共 279 支全過;verify_gates 兩正三負全部成立、正二 file_coverage=true。
- 殘餘與未證明(目前尚未 machine-enforced):沿用 4g 證據報告第 8 節 + S5g-F1 / F3 / F4 / F5 追蹤項;本輪新增(照錄):
  「本輪檢查的語意是 git rev-parse --show-prefix 為空，即 root 必須是 Git 認定的該 repository 最上層。monorepo 中、非 Git 最上層的普通子專案，本輪明確不支援作為 evidence root（H1 鎖住）。巢狀獨立 Git repo / submodule 若自身被 Git 視為最上層，--show-prefix 同樣為空、會被接受；其行為本輪未納入 acceptance，屬未證明範圍，不得宣稱已拒絕或已支援。」
- commit:S4H1 `ea6aba6452668982fee56f7a2f0faf2cd720ca6d`;S4H3(本節與證據報告)`569b57d2dd048d3317d51970757f3b41a7f28891`。
  (F-036:本行原文為「S4H3(本節與證據報告)於下一次提交回填。」;2026-10-05 於 S4H4 回填。)
  - S4H4(POSIX 驗收記錄與狀態升級)`2f496b9d0a71d88995b2338c6b4440d693c9a879`。
    (F-036:本行原文為「S4H4(POSIX 驗收記錄與狀態升級)於下一次提交回填。」;2026-10-05 於 S5h-0 回填。)

### 55.3 POSIX 外部 clean-room 驗收

> **舊文字(F-036,保留不刪)**:本節原文為 ~~`待執行(裁決助手)。`~~;2026-10-05 S4H4 依 Jeff 裁決改為下方照錄段落。
> Jeff 裁決(2026-10-05):Station 4h 本機驗收(S4H2,見 S4H3 `569b57d2dd048d3317d51970757f3b41a7f28891`)與裁決助手 POSIX 外部驗收皆 PASS ⇒ Station 4h = PASS / COMPLETED;〈十〉3h 列依前裁改為 PASS / ACCEPTED(選 A);下一站 5h 獨立審查(只審 3h/4h 增量;須開全新對話)。

POSIX 外部 clean-room 驗收（裁決助手；隔離環境；非本 repo 帳本證據）——2026-10-05 約 09:45 ET
- 環境：Linux，Python 3.11.16，pytest 9.1.1，anyio 4.15.0。
- 受測樹：4g POSIX 驗收所用的樹（BASE de36ebcbab284ef11064a9943b5191750482dd93 + S4G3 時點 12 檔）再覆蓋 S3H1 的 tests/test_redlight.py 與 S4H1 ea6aba6452668982fee56f7a2f0faf2cd720ca6d 的 .claude/hooks/redlight.py 原檔（CRLF→LF）。
- 修正前（S3H1 tests + 4g 程式）：H1 失敗於 got == "true"、H2 通過，與 Windows 3h 一致。
- 修正後：verify_gates.py R1–R9 各擋下一次；權威層偵測三項成立；淨室框架測試 0 failed；evidence policy 兩正三負全部成立：
    正一 未初始化 成立（35 個框架測試檔皆 unknown；evidence policy: 未初始化）
    正二 已初始化且相符 成立（rc 1→0；file_coverage=true；green=tests/test_evidence_probe.py；evidence policy: 有效）
    負一 policy / 環境不符 成立（file_coverage=unknown；紅仍在）
    負二 HEAD 有、工作樹不同 成立（file_coverage=unknown；evidence policy: 工作樹與 HEAD 不同）
    負三 工作樹有、HEAD 沒有 成立（file_coverage=unknown；evidence policy: 未提交）
- 宿主固定全套（Linux）：collected 2102；2086 passed、13 failed、3 xfailed。13 支與 4g POSIX 驗收及 de36ebc 基準在同一沙盒的失敗集合完全相同（tests/test_gate.py::TestAuthorityLayerIsWired::test_this_repo_itself_is_wired 與 tests/test_known_items_regression.py 的 12 支）⇒ 沙盒環境因素（推測：clone 未設 hooksPath、缺本機私有資料），與 3h/4h 無關。evidence 相關 5 檔全過。
- 結論：POSIX 外部 clean-room 驗收 PASS。

---

## 五十六、Station 5h 審查包

- Jeff 裁決(2026-10-05):S4H4 = accepted;Station 4h = PASS / COMPLETED(S4H4 `2f496b9d0a71d88995b2338c6b4440d693c9a879`);Station 5h-0 = APPROVED TO BUILD REVIEW PACKAGE;
  5h 獨立審查須在全新對話進行,5g 審查 session 不得擔任 5h 審查者。
- 審查包:`docs/audits/2026-10-05-m1a-station5h-review-package.md`(只審 3h / 4h 增量)。
  - 69609 bytes / 1085 行;SHA-256 `f37743fb9e358ba33b07cb2ebe08f33e42092fb0a1525032de0089d4d13093cb`;
  - staged blob `d0260d087ccfac00376c4ac624c36b261eeb8fde`。
- 身分(9 個完整 SHA):

| 代號 | 完整 SHA |
|---|---|
| BASE_G(5g 審查 HEAD;S4G5) | `b5db3734f6795d8a371e4f58b172e0a8ffb066eb` |
| TARGET_G(5g 審過的最後程式 commit;S4G1C) | `8e7775526e462d984abb0992ed74c1e1aa3648dd` |
| S5g-0 | `5e096acb899b3370f16018199627784af71b788e` |
| S5g-1 | `3a9200c03bb8493ab5a789d4c4157a7b38392e79` |
| S3H1(H1/H2 紅燈) | `7621e3ce8604ab72ab2f3fb3257cb1181b8a126e` |
| S3H2 | `66140896d03f32c4df73be01b2aaeb48353e0510` |
| TARGET(S4H1;本輪最後程式 commit) | `ea6aba6452668982fee56f7a2f0faf2cd720ca6d` |
| S4H3 | `569b57d2dd048d3317d51970757f3b41a7f28891` |
| REVIEW_HEAD(S4H4) | `2f496b9d0a71d88995b2338c6b4440d693c9a879` |

- CODE_FILES(TARGET_G..TARGET 的非 docs 檔):`.claude/hooks/redlight.py`、`tests/test_redlight.py`。
- 審查包 `git diff --cached --check` 的 4 行行尾空白全部來自 E.1 / E.3 原樣 diff 的單空格 context 行(包內第 323、324、495、496 行),未修改。
- S5h-0(審查包 commit)`300b42a520b0a62fec0931d895200ea8817e47aa`。
  (F-036:本行原文為「S5h-0(審查包 commit):記錄 5h 結果時回填。」;2026-10-05 於 S5h-1 回填。)

---

## 五十七、Station 5h 獨立審查（FAIL）與 Station 3i 裁決（2026-10-05，Jeff）

### 57.1 審查報告

- 路徑 `docs/audits/2026-10-05-m1a-station5h-review.md`;raw = repo 副本(與審查者原檔 `.scratch/m1a-s5h/review-report.md` 以 `cmp` 逐位元組相同,無任何改動);
  sha256 `7dac1d2a145ac576ab8958d0c9fd9eb1275333ab79f70f07639c6f32e02ed8d0`;33480 bytes。
- 審查對象 TARGET `ea6aba6452668982fee56f7a2f0faf2cd720ca6d`;審查包所在 commit S5h-0 `300b42a520b0a62fec0931d895200ea8817e47aa`。
- **審查者判決:FAIL**(blocker 0、major 1、minor 1、nit 2)。
- Findings(報告第 2 節;一行摘要,不改寫結論):
  - S5h-F1【major;G9 / G1 / G7;需要重現(端到端)】`_root_is_toplevel` 只看 `--show-prefix` 為空;root 位於 gitdir 內(bare repo 目錄、bare 底下子目錄、非 bare 的 `.git/`)時 `--show-prefix` 同樣 exit 0 輸出空行,`HEAD:<path>` 取 tree 根的已提交 blob、`hash-object <path>` 讀 root 底下 Git 不對應任何 tree 路徑的副本 ⇒ head == worktree ⇒ 預期 `file_coverage == "true"`;同一 root 的 `--show-toplevel` exit 128,53.3 裁決 2 的等價式不成立。
  - S5h-F2【minor;G2 / G5;需要重現(突變測試)】刪掉 `committed_blobs` 的非最上層分支(`:755-757`)H1 仍會綠 —— `evidence_policy_facts` 已先回全 None;全樹沒有測試直接呼叫 `committed_blobs` 或 `_root_is_toplevel`,「不得留 (xi) 半套」只由程式碼保證、沒有測試鎖住。
  - S5h-F3【nit;G7】殘餘措辭漏列「被接受但不是獨立 repo」的佈局(`sub/.git` 檔指向上層 gitdir、只設 `GIT_DIR`、`core.worktree` 指向 sub):Git 把 sub 解析成同一 repository 的工作樹最上層;依 G9 判準不構成 F2,只是措辭涵蓋面不足。
  - S5h-F4【nit;G3 / G7】非最上層 root 沒有專屬 status 狀態字:monorepo 子專案的 policy 已提交於上層 repo 時 status 顯示「未提交」,照字面再提交也不會變;fail-closed,與 S5g-F1 同型;非本輪引入。
- 5g 結論:報告第 5 節逐條判定 5g 的 G1–G13 與 S5g-F1 / F3 / F4 / F5 仍成立(G1 / G6 / G13 的「例外形狀」更新為:普通子目錄已封住,gitdir / bare 內仍存在 = S5h-F1)。

### 57.2 裁決助手外部重現(隔離 Linux 環境;git 2.43.0;Python 3.11 + pytest 9.1.1;非獨立審查 finding;非本 repo 帳本證據)

來源:Jeff 的 Station 5h-1 指令,照錄。

- 端到端：以 S4H1 ea6aba6452668982fee56f7a2f0faf2cd720ca6d 的 redlight.py 與 tests/test_redlight.py 既有 helper（_g_default_root、_g_coverage），分別把 root 設為 <parent>/.git（parent 為已提交合法 policy 的最上層）與 <bare.git>/proj（bare clone 底下子目錄），三份未提交副本放在 root 下 ⇒ 兩者皆得 file_coverage == "true"。S5h-F1 由「需要重現」升為已確認。
- 修法原型：_root_is_toplevel 改為一次 git rev-parse --is-inside-work-tree --show-prefix，須第一行為 true 且第二行為空；指令失敗 / 非零 / 任一條件不符 ⇒ False。套用後上述兩個原型轉為非 true；H1 / H2 維持綠；evidence 相關 5 檔共 281 支全過。
- I3 原型：直接呼叫 redlight.committed_blobs(<parent>/sub)（不經 evidence_policy_facts），要求 BLOB_FILES 每一路徑都為 {"worktree": None, "head": None}，且 committed_blobs(<parent>) 每一路徑 worktree 非空且 == head；在 S4H1 與修法原型上皆通過（regression-lock）。

### 57.3 裁決(照錄)

1. Station 5h 獨立審查 = FAIL；S5h-F1 = major / confirmed end-to-end。4h 的 _root_is_toplevel 以 rev-parse --show-prefix 為空當作「root 是工作樹最上層」，但 .git/ 內部或 bare repository 內同樣滿足此條件，而該處並非工作樹 ⇒ HEAD 證明的是 repository 內某個 path、工作樹實際讀的是另一個 filesystem root ⇒ identity mismatch ⇒ 仍可能 file_coverage == "true"。與 S5g-F2 同一條 I-3 位置不變式，不得列追蹤項。〈五十三〉53.3 裁決 2 所稱「與 resolved root == git rev-parse --show-toplevel 等價」實測不成立，於此更正。
2. 回 Station 3i，紅燈三支（皆經真實 conftest producer 或直接呼叫 producer helper，真 git repo）：
   I1 behavior-red：root = <最上層>/.git，三份副本只在 root 下、未提交 ⇒ 不得為 "true"。
   I2 behavior-red：root = <bare clone>/proj，同上 ⇒ 不得為 "true"。
   I3 regression-lock：直接呼叫 committed_blobs 對非法 root（<最上層>/sub）：BLOB_FILES 每一路徑皆 {"worktree": None, "head": None}；對照組 committed_blobs(<最上層>) 每一路徑 worktree 非空且 == head。目的：獨立證明 committed_blobs 那一半 fail-closed，不被 evidence_policy_facts 的 guard 間接遮蔽（S5h-F2）。
3. Station 4i 最小修正方向：_root_is_toplevel 須同時滿足 rev-parse --show-prefix 為空 且 rev-parse --is-inside-work-tree 為 true；任一查詢失敗、非零、或條件不符 ⇒ False ⇒ policy facts / committed_blobs facts 全 None ⇒ unknown ⇒ 不得退紅。對應的 invariant：root 必須是 Git 工作樹的最上層，不只是 Git repository context 中 prefix 恰為空的位置。
4. S5h-F3（殘餘措辭漏列「被接受但非獨立 repo」的重新對應佈局）於 4i 文件補準；S5h-F4（非最上層 root 的 status 無專屬狀態字）併入 S5g-F1 類的 operator / status 追蹤項。兩者不阻擋本輪，目前尚未 machine-enforced。
5. 流程：5h-1 記錄 → Jeff 切 tickets → 3i 紅燈 → Jeff 切 implement → 4i（含 Windows 全套、本機 clean-room、裁決助手 POSIX）→ 5i 增量審查（全新對話；4g 實作 session、5g 與 5h 審查 session 皆不得擔任）→ Station 6。

### 57.4 commit

- S5h-1(本節與審查報告入庫)`b62346136cd5ce3bcb0e8dfbc78e3c827f7da849`。
  (F-036:本行原文為「S5h-1(本節與審查報告入庫)於下一次提交回填。」;2026-10-05 於 S3I2 回填。)

---

## 五十八、Station 3i 紅燈證據

- Jeff 裁決(2026-10-05):S5h-1 = accepted。**身分更正**:本 session 自 3h 起為事實上的實作 session(3h、4h、5h-0、5h-1 皆由本 session 執行);3i / 4i 繼續由本 session 執行;5i 審查須開全新對話,5g / 5h 審查 session 與本 session 皆不得擔任。
- 報告:`docs/audits/2026-10-05-m1a-station3i-redlight.md`。
- S3I1 `260ede30628c7d205b30ac12c94be73a75cd2812`:`tests/test_redlight.py` 檔尾一個 hunk `@@ -2576,0 +2577,72 @@`,只有 + 行;新增 `class TestEvidenceRootIsInsideWorkTree`,既有 helper 只呼叫、不修改。commit 前只跑 py_compile。
- 新增 3 支(完整 nodeid):
  - I1 behavior-red(在 S5h-1 上必須失敗):`tests/test_redlight.py::TestEvidenceRootIsInsideWorkTree::test_i3_a_root_inside_the_gitdir_is_not_full_coverage`
  - I2 behavior-red(在 S5h-1 上必須失敗):`tests/test_redlight.py::TestEvidenceRootIsInsideWorkTree::test_i3_a_root_inside_a_bare_repository_is_not_full_coverage`
  - I3 regression-lock(在 S5h-1 上必須通過;不經 `evidence_policy_facts`,直接呼叫 `committed_blobs`):`tests/test_redlight.py::TestEvidenceRootIsInsideWorkTree::test_i3_committed_blobs_alone_is_fail_closed_for_a_subdirectory_root`
- 紅燈全套(在 S3I1 上只跑一次;外來 3 檔已 stash,跑前跑後 `git status --porcelain` 皆無輸出):exit 1;
  摘要行原文 `2 failed, 2097 passed, 3 skipped, 3 xfailed in 256.98s (0:04:16)`(collected 2105)。
  FAILED 恰為 I1、I2:失敗行 `tests\test_redlight.py:2613: AssertionError` 與 `tests\test_redlight.py:2629: AssertionError`(皆 `assert 'true' != 'true'`);I3、H1、H2 在 2097 passed 之內。
  ⇒ S5h-F1 在本樹(Windows)端到端重現。
- 帳本只追加:兩本前段 sha256 = Step 0 基準(`5f0ffa92…` / `74757aa6…`);test-runs 3109 → 3156 行(+47)、test-sessions 29 → 30 行(+1)。
  跑後全檔記為 B17:test-runs 845770 bytes、`5c91ea58af19e13d181af2c8ae471738d313d61b60a47fde20f40dfdbde10098`;
  test-sessions 14387323 bytes、`52ef61774703e5b9feff6de02462b878c22ce47b1cface87511b74d14e45ff1a`。
- 裁決助手 Linux 預演(來源:Jeff 的 Station 3i 指令;隔離環境;非本 repo 帳本證據):以 S4H1 的 redlight.py,I1 / I2 原型皆失敗於 got == "true"、I3 原型通過;套用 4i 修法原型後 I1 / I2 / I3 / H1 / H2 全綠,evidence 相關 5 檔 281 支全過。
- commit:S3I1 `260ede30628c7d205b30ac12c94be73a75cd2812`;S3I2(本節與證據報告)`b11dc9eb49912d1a639534aca14aed31b24a9dec`。
  (F-036:本行原文為「S3I2(本節與證據報告)於下一次提交回填。」;2026-10-05 於 S4I3 回填。)

---

## 五十九、Station 4i 修正

### 59.1 裁決(照錄要點;Jeff,2026-10-05)

- Station 3i = PASS / ACCEPTED(I1 / I2 behavior-red、I3 regression-lock 成立);Station 4i plan = APPROVED;只改 `_root_is_toplevel()`,I1–I3 / H1 / H2 不准修改。
- 三段式:S4I1 實作 → S4I2 本機驗收 → S4I3 docs-only(只能宣稱本機驗收通過;待 POSIX 外部驗收)。POSIX 由裁決助手執行,通過後另以 S4I4 升級。

### 59.2 證據

- 報告:`docs/audits/2026-10-05-m1a-station4i-fix.md`。
- S4I1 `8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8`:只改 `.claude/hooks/redlight.py` 的 `_root_is_toplevel()`(+9 / −3,一個 hunk `@@ -724,16 +724,22 @@`)。
  - 一次呼叫 `git -C <root> rev-parse --is-inside-work-tree --show-prefix`;須第一行 strip 後為 `b"true"` 且第二行 strip 後為空才 True;任何例外 / returncode ≠ 0 / `len(lines) < 2` / 條件不符 ⇒ False。
  - 未改 `committed_blobs` / `evidence_policy_facts` 的呼叫處、consumer、`policy_state`、conftest、status / install / verify_gates、任何測試;`content_hash` 未動。
  - 一次 Edit,寫入後 status.py 探針無「redlight.py 無 run 事實讀取」。
- S4I2 本機固定全套(S4I1 上只跑一次;外來 3 檔已 stash):exit 0;`2099 passed, 3 skipped, 3 xfailed in 241.02s (0:04:01)`(collected 2105、0 failed)。I1 / I2 由紅轉綠,I3 / H1 / H2 維持綠。
- 帳本只追加:前段 sha256 = B17;test-runs 3156 → 3203(+47)、test-sessions 30 → 31(+1)。
- status:`evidence policy: 有效`;`tests red under ticket 145: (無)`;run 事實未知 0;`tests/test_redlight.py` 在 green。
- 淨室(verify_gates;同一次執行):R1–R9 各擋下一次、權威層偵測三項成立、淨室框架測試 `1949 passed, 7 skipped, 3 xfailed`;兩正三負全部成立,正二 `file_coverage=true`、`green=tests/test_evidence_probe.py`。
  本 repo 兩本帳本前後 bytes 與 sha256 都等於 V0(test-runs 857289 / `9e909520…`;test-sessions 15126808 / `440406f6…`)。
- 裁決助手 Linux 預演(來源:Jeff 的 Station 4i 指令;隔離環境;非本 repo 帳本證據):以 S3I1 的 tests 與 S4H1 的程式,I1 / I2 失敗於 got == "true"、I3 通過;套用本修正形狀後 I1 / I2 / I3 / H1 / H2 全綠,evidence 相關 5 檔 282 支全過。
- 殘餘與未證明(目前尚未 machine-enforced):沿用 4h 證據報告第 7 節 + S5g-F1 / F3 / F4 / F5、S5h-F3 / F4 追蹤項;本輪依 S5h-F3 補準措辭(照錄於報告第 7 節第 3 點):
  「本輪檢查的語意是 git rev-parse --is-inside-work-tree 為 true 且 --show-prefix 為空，即 root 必須是 Git 對該 root 解析出的工作樹的最上層。明確不支援（⇒ unknown）：monorepo 中非最上層的普通子目錄（H1）、位於 gitdir 或 bare repository 內的 root（I1 / I2）。會被接受但本輪未納入 acceptance、屬未證明：巢狀獨立 Git repo、submodule、linked worktree（git worktree add）、.git 為檔案且 gitdir 指向他處、GIT_DIR / GIT_WORK_TREE / core.worktree 等重新對應佈局。上述佈局若 Git 對該 root 實際回報 --is-inside-work-tree=true 且 --show-prefix 為空，即會被本檢查接受；其 HEAD 與工作樹是否符合既定 identity invariant，本輪未完整 acceptance，不得宣稱已拒絕或已支援。」
- commit:S4I1 `8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8`;S4I3(本節與證據報告)`64da2ec2b78b64b6eb23822c7a0e018b82e2500a`。
  (F-036:本行原文為「S4I3(本節與證據報告)於下一次提交回填。」;2026-10-05 於 S4I4 回填。)
  - S4I4(POSIX 驗收記錄與狀態升級)於下一次提交回填。

### 59.3 POSIX 外部 clean-room 驗收

> **舊文字(F-036,保留不刪)**:本節原文為 ~~`待執行(裁決助手)。`~~;2026-10-05 S4I4 依 Jeff 裁決改為下方照錄段落。
> Jeff 裁決(2026-10-05):Station 4i 本機驗收(S4I2,見 S4I3 `64da2ec2b78b64b6eb23822c7a0e018b82e2500a`)與裁決助手 POSIX 外部驗收皆 PASS ⇒ Station 4i = PASS / COMPLETED;下一站 5i 增量獨立審查(只審 3i/4i 增量;須開全新對話;4g 實作 session、本實作 session、5g 與 5h 審查 session 皆不得擔任)。

POSIX 外部 clean-room 驗收（裁決助手；隔離環境；非本 repo 帳本證據）——2026-10-05 約 13:20 ET
- 環境：Linux，Python 3.11.16，pytest 9.1.1，anyio 4.15.0，git 2.43.0。
- 受測樹：4h POSIX 驗收所用的樹再覆蓋 S3I1 的 tests/test_redlight.py 與 S4I1 8154a1acb9ccd4dac87bbbd37aa2aca8b0348fe8 的 .claude/hooks/redlight.py 原檔（CRLF→LF）。
- 修正前（S3I1 tests + S4H1 程式）：I1 / I2 失敗於 got == "true"、I3 通過，與 Windows 3i 一致。
- 修正後：verify_gates.py R1–R9 各擋下一次；權威層偵測三項成立；淨室框架測試 0 failed；evidence policy 兩正三負全部成立：
    正一 未初始化 成立（35 個框架測試檔皆 unknown；evidence policy: 未初始化）
    正二 已初始化且相符 成立（rc 1→0；file_coverage=true；green=tests/test_evidence_probe.py；evidence policy: 有效）
    負一 policy / 環境不符 成立（file_coverage=unknown；紅仍在）
    負二 HEAD 有、工作樹不同 成立（file_coverage=unknown；evidence policy: 工作樹與 HEAD 不同）
    負三 工作樹有、HEAD 沒有 成立（file_coverage=unknown；evidence policy: 未提交）
- 宿主固定全套（Linux）：collected 2105；2089 passed、13 failed、3 xfailed。13 支與 4g / 4h POSIX 驗收及 de36ebc 基準在同一沙盒的失敗集合完全相同（tests/test_gate.py::TestAuthorityLayerIsWired::test_this_repo_itself_is_wired 與 tests/test_known_items_regression.py 的 12 支）⇒ 沙盒環境因素（推測：clone 未設 hooksPath、缺本機私有資料），與 3i/4i 無關。evidence 相關 5 檔（含 I1–I3 / H1–H2）全過。
- 結論：POSIX 外部 clean-room 驗收 PASS。

---

## 相關

- **票 139** —— 原始 finding。本票承接;其證據與未查邊界不改寫。
- **票 137** —— 被票 139 那次窄選遮蔽的那條紅。**本票不處理它。**
- **票 93** —— CI 的 `--deselect`。**本票不處理它。**
- **追蹤票(待建,2026-10-03 登記)受測物件身分 / provenance(I-9 / I-6 族)** —— 執行的程式碼不是工作樹那一份
  (`PYTHONPATH`、site-packages 的另一份、`-P`;同秒同大小的改寫快取)。依〈四十一〉41.1 第 5 點列殘餘,**本票不處理**。
  分析見 `docs/audits/2026-10-03-m1a-station3f-redlight-plan.md` P3。
- **追蹤票(待建,2026-10-03 登記)S5e-F6** —— override 的 key 與 `pythonwarnings` 原樣落帳(可帶路徑)。
  依〈三十九〉39.3 列入 privacy / provenance 追蹤票,**本票不修**。
- **追蹤項(2026-10-03 登記,〈四十五〉45.3 第 3 點)logging 鎖步絆線待辦(目前尚未 machine-enforced)** ——
  後續追蹤項須新增測試,讀取已提交的 pyproject.toml(`git show HEAD:pyproject.toml`),斷言 `[tool.pytest.ini_options]`
  尚未出現 `log_level` / `log_cli_level` / `log_file_level`(做法同 D4)。在該機器絆線實作並通過前,
  新增上述已提交 logging 政策的變更,**不得視為已被 M1-a authority 覆蓋**。此為程序約束,目前尚非機器 enforcement。
- **追蹤項(2026-10-03 登記,〈四十五〉45.3 第 3 點)一般化研究** —— 以「實際生效的 option namespace 等於固定指令的解析結果」
  取代逐項列舉(可收斂 (xv)–(xix) 與 logging 族);獨立設計,**不在 M1-a 處理**。
- **追蹤項(2026-10-03 登記,〈四十五〉45.3 第 3 點)S5f-F2** —— POSIX 上 root 路徑本身含 `\` 時固定全套永遠 unknown
  (fail-closed 的可用性問題)。
  4f 報告第 7 節第 3 點的敘述更正(在本紀錄更正,不回寫 4f 報告):該點只涵蓋「值」含 `\` 的情形;
  **root 路徑本身含 `\` 時,受影響的是固定全套本身**((vii)、(x) 判 unknown),不是只有 `-c` / override。
- **追蹤項(2026-10-03 登記,〈四十五〉45.3 第 3 點)S5f-F3** —— `normalize_overrides` docstring 對 pytest 解析基準的敘述過度概括
  (`log_file` 以 cwd 解析);屬文件準確度,不改 authority 語意。
- **追蹤項(2026-10-04 登記,〈五十三〉53.3 第 4 點;下一張票優先)S5g-F1(目前尚未 machine-enforced)** ——
  `policy_state` 不查 addopts 鎖步;框架 pyproject 範本 + policy 範本原樣採用時 status 顯示「有效」,但每次固定全套都是 unknown,
  紅燈永遠不退且無訊號。須以機制處理 status 訊號(例:status 多一狀態,重用 verdict 的鎖步),不只改文字。
- **追蹤項(2026-10-04 登記,〈五十三〉53.3 第 4 點)S5g-F3(目前尚未 machine-enforced)** ——
  pytest 9 原生 `[tool.pytest]`(無 `ini_options`)⇒ `_committed_addopts` 回 None ⇒ 永遠 unknown;status 仍顯示「有效」(fail-closed)。
- **追蹤項(2026-10-04 登記,〈五十三〉53.3 第 4 點)S5g-F4(目前尚未 machine-enforced)** ——
  `.gitattributes` 的 clean filter 可讓設定檔 / conftest 工作樹 ≠ HEAD 但 `hash-object` 相等 ⇒ (xi) 誤判一致;policy 本身不受影響;BASE 已存在。
- **追蹤項(2026-10-04 登記,〈五十三〉53.3 第 4 點)S5g-F5(目前尚未 machine-enforced)** ——
  verify_gates 在正二不成立時,負一~負三仍印「成立 ✓」;負情境的判別力來自同次執行中正二成立的差分,程式沒有把這個耦合寫進輸出。
- **追蹤項(2026-10-05 登記,〈五十七〉57.3 第 4 點)S5h-F3(目前尚未 machine-enforced)** ——
  殘餘措辭漏列「被接受但不是獨立 repo」的重新對應佈局(`sub/.git` 檔指向上層 gitdir、只設 `GIT_DIR`、`core.worktree` 指向 sub):
  Git 把 sub 解析成同一 repository 的工作樹最上層;依判準不構成 F2,只是措辭涵蓋面不足。於 4i 文件補準。
- **追蹤項(2026-10-05 登記,〈五十七〉57.3 第 4 點)S5h-F4(目前尚未 machine-enforced;與 S5g-F1 同類的 operator / status 訊號)** ——
  非最上層 root 沒有專屬 status 狀態字:monorepo 子專案的 policy 已提交於上層 repo 時 status 顯示「未提交」,照字面再提交也不會變、紅燈也不退(fail-closed)。
