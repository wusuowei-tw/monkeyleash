# 獨立審查包 —— agent-gates 票 145（M1-a）Station 5 程式碼審查

## 給審查者的說明（請先讀）

你是**獨立審查者**。你沒有、也不需要這個專案先前的討論紀錄。請只根據本文件提供的材料判斷。

**審查對象**：一個 Python 測試框架的「測試執行證據」機制修正。
- 修正前的問題：測試紀錄只記「某個測試檔 + green/red」，不記「這次執行涵蓋了什麼」。所以一次只選幾條測試、而且全部 skip 的窄選執行，會被記成 green，並在儀表板上蓋掉同一檔較早的 red（假綠）。
- 修正方式：新增「一次執行（run / session）」層級的事實，並讓儀表板依規則判斷某檔的 red 能不能退成 green。

**材料**：
1. 需求合約（票 145 的 REQUIREMENT 與裁決，逐字摘錄）
2. 實作改動（4 個檔）
3. 紅燈測試（實作前寫好、實作前全部失敗的 14 支測試，實作時不得修改）
4. 執行證據（固定指令全套結果、儀表板輸出、一筆 session 紀錄樣本）

**請你做的事**：逐項檢查實作是否符合合約，找出缺陷。特別注意：
- **fail-open**：任何「證據不足、讀取失敗、格式不符」時，系統是否可能錯誤地判成 green / 成功。
- **測試是否真的在測合約**：14 支紅燈測試有沒有可能被一個錯誤的實作也通過（測得太寬）。
- **與合約不符或合約沒涵蓋**的行為。

**請不要**：建議重寫架構、擴大範圍到合約〈八、Out of scope〉列出的項目。

**輸出格式**：
1. 總結論：PASS / PASS（附非阻擋意見）/ FAIL
2. 發現清單，依嚴重度排序（阻擋 / 應修 / 建議）。每一項必須：
   - 指出檔名與行號或函式名
   - 引用相關程式碼原文
   - 說明在什麼輸入或情境下會出錯（具體情境）
   - 對應到哪一條合約（A–F、I1–I7、BC 1–4、ODC-1/2/3、AC）
3. 合約逐條對照表：每條 REQUIREMENT 標「符合 / 不符 / 無法從材料判斷」，附依據
4. 你不確定的地方標「未證明」，不要猜

---

## 一、需求合約（票 145 摘錄，逐字）

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


### 補充事實（不是合約，是實作端的設計決定）
- run 層級事實寫在**另一本帳** `.dev/test-sessions.jsonl`；原本的 `.dev/test-runs.jsonl`（每檔一筆、8 個欄位）格式不變、舊紀錄不改寫。
- 固定驗收指令：`python -X utf8 -m pytest -q`（全套，不加任何選擇或排除）。

---

## 二、實作改動

### 2.1 `.claude/hooks/redlight.py`（紀錄的寫入與讀取；本次只新增、無刪除）

```diff
--- a/.claude/hooks/redlight.py
+++ b/.claude/hooks/redlight.py
@@ -141,3 +141,127 @@
     except Exception:
         pass
     return rec
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# 票 145(M1-a)—— run 事實:一次 test run 跑了什麼、結果是什麼
+#
+# 上面的 `record_run()` 一筆 = (一個測試檔 × 一次結果),**帳本裡沒有「一次執行」**
+# 這個實體 ⇒ 窄選、全部 skip、0 collected、根本沒跑,在帳本上長得一樣(票 139)。
+# 本段補上那個實體。
+#
+# **另一本帳**(`.dev/test-sessions.jsonl`),不寫進 `test-runs.jsonl`:
+#   - `gate.redlight_missing()`(R3,權威層)逐行讀 `test-runs.jsonl`,
+#     `test_file` 命中而缺 `impl_exists` 就擋 —— 同檔混放會讓 R3 的解析面跟著變;
+#   - 既有 8 欄紀錄**一筆都不改、不補欄位**(票 145〈三〉Backward compatibility 1–4)。
+# 落點由 `root` 參數推出,不由模組常數推出 —— status 依 root 載入本檔讀取,
+# 測試以 tmp root 寫入,三方對同一個 root 說的是同一本帳。
+# ─────────────────────────────────────────────────────────────────────────────
+
+SESSION_LOG_NAME = "test-sessions.jsonl"
+
+COLLECTION_ERROR = "<collection error>"
+
+
+def session_log(root):
+    """`<root>/.dev/test-sessions.jsonl`。"""
+    return os.path.join(os.fspath(root), ".dev", SESSION_LOG_NAME)
+
+
+def _ticket_of(root):
+    """`<root>/.dev/pipeline.json` 的 `ticket_id`。讀不到回 None —— 不猜(同 `current_ticket`)。"""
+    try:
+        with io.open(os.path.join(os.fspath(root), ".dev", "pipeline.json"),
+                     encoding="utf-8") as f:
+            return json.load(f).get("ticket_id")
+    except Exception:
+        return None
+
+
+def record_session(root, run_id=None, time=None, ticket_id=None, exit_code=None,
+                   collected=(), deselected=(), outcomes=None):
+    """追加一筆 run 事實到 `<root>` 的 session 帳本。回傳寫入的內容。
+
+    - `collected`:本次收集到的身分(含被 deselect 的;收集錯誤以
+      `<檔>::<collection error>` 標記)
+    - `deselected`:被排除的身分;`selected` = collected − deselected
+    - `outcomes`:`{身分: "passed" | "failed" | "skipped" | "other"}`,只含 selected
+    - `exit_code`:runner 的原始退出碼;取不到為 None
+
+    `run_id` / `time` / `ticket_id` 為 None 時自取(測試可指定以求決定性)。
+    寫入失敗不拋例外 —— 紀錄器不得弄死執行器(`TestTheRecorderCannotKillTheRunner`)。
+    """
+    import uuid
+    rec = {
+        "kind": "session",
+        "run_id": run_id or uuid.uuid4().hex,
+        "time": time or datetime.now(timezone.utc).isoformat(),
+        "ticket_id": ticket_id if ticket_id is not None else _ticket_of(root),
+        "exit_code": None if exit_code is None else int(exit_code),
+        "collected": [str(n).replace("\\", "/") for n in (collected or ())],
+        "deselected": [str(n).replace("\\", "/") for n in (deselected or ())],
+        "outcomes": {str(k).replace("\\", "/"): v for k, v in (outcomes or {}).items()},
+    }
+    path = session_log(root)
+    try:
+        os.makedirs(os.path.dirname(path), exist_ok=True)
+        with io.open(path, "a", encoding="utf-8") as f:
+            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
+    except Exception:
+        pass
+    return rec
+
+
+def load_runs(root):
+    """`<root>` 的 run 事實,依寫入順序。無帳本回 `[]`。
+
+    **任何一行讀不動就整本回 `[]`** —— 讀到一半的帳本會讓「較晚的 run」
+    看起來不存在,而那正是退紅判定最依賴的東西。回 `[]` 的效果是
+    「無 run 證據 / 不可判定」:沒有任何紅可以因此退掉(fail-closed 的方向)。
+    """
+    path = session_log(root)
+    if not os.path.exists(path):
+        return []
+    out = []
+    try:
+        with io.open(path, encoding="utf-8") as f:
+            for line in f:
+                line = line.strip()
+                if not line:
+                    continue
+                rec = json.loads(line)
+                if not isinstance(rec, dict) or not rec.get("run_id"):
+                    return []
+                out.append(rec)
+    except Exception:
+        return []
+    return out
+
+
+def run_state(run):
+    """一個 run 事實的狀態 `"A"`–`"F"`(票 145〈三〉A)。**依序判定,先命中者為準。**
+
+    | 條件 | 狀態 |
+    |---|---|
+    | exit code 不在 {0, 1, 5}(中斷 / 內部錯誤 / 用法錯誤 / 取不到),或有收集錯誤 | D |
+    | 任一身分 failed | B |
+    | 0 collected | C |
+    | 沒有任何身分 passed(全 skip、全 deselect、或混合) | F |
+    | 其餘(≥1 passed、0 failed) | A |
+
+    **不只看 exit code**:全部 deselected 時 pytest 回 5,但有收集到 ⇒ F,不是 C。
+    E(根本沒跑)沒有 run 事實可以輸入,不在本函式值域內。
+    """
+    ec = run.get("exit_code")
+    collected = run.get("collected") or []
+    outcomes = run.get("outcomes") or {}
+    values = list(outcomes.values())
+    if ec not in (0, 1, 5) or any(str(n).endswith("::" + COLLECTION_ERROR) for n in collected):
+        return "D"
+    if "failed" in values:
+        return "B"
+    if not collected:
+        return "C"
+    if "passed" not in values:
+        return "F"
+    return "A"
```

### 2.2 `tests/conftest.py`（測試執行時的紀錄產生端；本次新增 68 行、無刪除。全檔附上）

```python
"""Shared pytest fixtures that prevent CI hangs when API keys are absent."""

import os
from unittest.mock import MagicMock, patch

import pytest


def pytest_configure(config):
    for marker in ("unit", "integration", "smoke"):
        config.addinivalue_line("markers", f"{marker}: {marker}-level tests")


_API_KEY_ENV_VARS = (
    "OPENAI_API_KEY",
    "GOOGLE_API_KEY",
    "ANTHROPIC_API_KEY",
    "XAI_API_KEY",
    "DEEPSEEK_API_KEY",
    "DASHSCOPE_API_KEY",
    "DASHSCOPE_CN_API_KEY",
    "ZHIPU_API_KEY",
    "ZHIPU_CN_API_KEY",
    "MINIMAX_API_KEY",
    "MINIMAX_CN_API_KEY",
    "OPENROUTER_API_KEY",
    "AZURE_OPENAI_API_KEY",
    "ALPHA_VANTAGE_API_KEY",
)


@pytest.fixture(autouse=True)
def _dummy_api_keys(monkeypatch):
    for env_var in _API_KEY_ENV_VARS:
        monkeypatch.setenv(env_var, os.environ.get(env_var, "placeholder"))


@pytest.fixture(autouse=True)
def _isolate_live_gate_state(tmp_path, monkeypatch):
    """把**每一個**已載入的 gate 模組的證據路徑指到 tmp。

    由來(量化實測):框架測試把合成的 fixture 條目寫進宿主真實的
    `shadow-log`(4 筆變 13 筆)。證據檔是**閘門的判定依據** ——
    shadow-log 決定影子要不要晉升,test-runs.jsonl 決定 R3 的紅燈半。
    往裡面寫測試造的假紀錄,等於讓測試去改變閘門之後的判斷。

    **不靠「每條測試記得 monkeypatch」**:那是紀律,而紀律會漏 ——
    上游的 test_shadow.py 兩處都有 patch,漏掉的是**間接**走到
    `log_shadow()` 的那些(影子開著時,任何 check 被擋都會寫一筆)。
    所以改成機制:autouse,而且走訪 `sys.modules` ——
    各測試檔用 `spec_from_file_location` 各載一份 gate,只改一個沒有用。

    **同時修掉「測試假設影子是關的」**:`SHADOW_STATE` 指到 tmp 的不存在路徑,
    影子在測試中因此恆為關、可決定。影子開的那個方向由**成對的**測試
    自己開(見 tests/test_shadow.py),不再靠宿主 repo 碰巧是什麼狀態。

    `test-runs.jsonl` **不在這裡改**:紅燈紀錄是由 conftest 的紀錄器在
    每次真實執行後追加的,那是機制的正常產出,不是污染。
    """
    fields = {
        "SHADOW_LOG": tmp_path / "shadow-log.jsonl",
        "SHADOW_STATE": tmp_path / "shadow.json",
        "EXEMPTION_LOG": tmp_path / "gate-exemptions.jsonl",
        "PROVENANCE": tmp_path / "provenance.jsonl",
        # 票 49:攔截帳本。`INTERCEPT_LOG` 是**基底檔名**,月檔由
        # `intercept_path()` 從它推出來 —— 蓋住基底就蓋住整族,
        # 隔離不必知道輪替怎麼命名(新增一種月檔不必回來改這裡)。
        "INTERCEPT_LOG": tmp_path / "intercepts.jsonl",
        "INTERCEPT_SUMMARY": tmp_path / "intercepts-summary.jsonl",
    }
    for mod in _loaded_gate_modules():
        for name, path in fields.items():
            if hasattr(mod, name):
                monkeypatch.setattr(mod, name, str(path))


def _loaded_gate_modules():
    """找出所有已載入的 gate 模組實例。

    **不能只走訪 `sys.modules`**:各測試檔用
    `importlib.util.module_from_spec()` + `exec_module()` 載入,
    那條路徑**不會把模組註冊進 `sys.modules`** ——
    第一版的隔離 fixture 因此是空轉的,而且完全無聲。
    (抓到它的是本檔配套的接線測試,不是我。)

    改成從**測試模組的屬性**去找:每個測試檔都把載進來的 gate 綁在模組層變數上
    (`gate = _load()`),所以走訪 tests/ 底下的模組、看它們持有什麼就找得到。
    新增的測試檔不必做任何事就會被涵蓋 —— 這是機制,不是紀律。

    限制(誠實寫出來):在**測試函式內部**才載入的那份蓋不到,
    因為 fixture 在 setup 時就跑完了。所以測試檔要在模組層載 gate。
    """
    import sys as _sys
    out, seen = [], set()
    for mod in list(_sys.modules.values()):
        f = (getattr(mod, "__file__", None) or "").replace("\\", "/")
        if "/tests/" not in f:
            continue
        for attr in vars(mod).values():
            gf = (getattr(attr, "__file__", None) or "").replace("\\", "/")
            if gf.endswith(".claude/hooks/gate.py") and id(attr) not in seen:
                seen.add(id(attr))
                out.append(attr)
    return out


@pytest.fixture()
def mock_llm_client():
    client = MagicMock()
    client.get_llm.return_value = MagicMock()
    with patch(
        "tradingagents.llm_clients.factory.create_llm_client",
        return_value=client,
    ):
        yield client


# ─────────────────────────────────────────────────────────────────────────────
# 紅燈紀錄外掛 —— R3 的另一半(F-012 的規格掉件)。
#
# 綁在**執行測試這個動作本身**上,不是綁在「記得用某個指令」上:
# 用 IDE 跑、用 python -m pytest 跑、CI 跑,都會被記錄。
# 這也是靜默替換失敗的解藥:替換沒中 → 行為沒變 → 測試不會從紅轉綠 → 機制當場抓到。
# ─────────────────────────────────────────────────────────────────────────────

import importlib.util as _ilu
import pathlib as _pl

_ROOT = _pl.Path(__file__).resolve().parents[1]
_spec = _ilu.spec_from_file_location("_redlight", _ROOT / ".claude" / "hooks" / "redlight.py")
_redlight = _ilu.module_from_spec(_spec)
try:
    _spec.loader.exec_module(_redlight)
except Exception:
    _redlight = None

_outcomes = {}

# 票 145(M1-a):run 層級的事實 —— 這一次 session 收集了什麼、排除了什麼、
# 每個身分的結果、退出碼。上面的 `_outcomes` 是逐檔的(餵 `record_run`,R3 用),
# 這裡是逐身分的(餵 `record_session`,status 的退紅判定用)。兩份**並存**,
# 不互相推導:逐檔那份的語意(「這個檔這次有沒有失敗」)一個字都不改。
_run = {"selected": None, "deselected": [], "collect_errors": [], "outcomes": {}}


def _nodeid(obj):
    return str(getattr(obj, "nodeid", "") or "").replace("\\", "/")


def pytest_collectreport(report):
    """收集錯誤也算紅燈。

    **新模組的第一次紅燈幾乎都是這種** —— 實作還不存在,import 就掛了。
    只吃 when=="call" 的話這種紅燈完全不產生紀錄,於是 R3 的後半對每一個新模組
    都不可能誠實滿足,規則只剩繞過一條路。實際撞到過(可攜化票 01)。
    """
    if _redlight is None or not getattr(report, "failed", False):
        return
    f = str(getattr(report, "nodeid", "")).split("::", 1)[0].replace("\\", "/")
    if f.endswith(".py"):
        _outcomes.setdefault(f, {"failed": []})["failed"].append("<collection error>")
    # 票 145:收集錯誤也是 run 事實(狀態 D 的來源之一)。不限 .py ——
    # conftest 或目錄層級的收集錯誤一樣讓這次 run 不可信。
    _run["collect_errors"].append("%s::<collection error>" % (f or "<session>"))


def pytest_deselected(items):
    """票 145:被 `-k` / `-m` / `--deselect` 排除的身分。

    **deselect 不產生任何 report**(RECON 二.2 B2)—— 不在這裡記,
    事後就看不出那一次的涵蓋範圍有多窄(票 139 的 645 deselected)。
    """
    if _redlight is None:
        return
    _run["deselected"].extend(_nodeid(i) for i in items)


def pytest_collection_finish(session):
    """票 145:deselect 之後真正要跑的身分(= selected)。"""
    if _redlight is None:
        return
    _run["selected"] = [_nodeid(i) for i in getattr(session, "items", None) or []]


def _run_outcome(report):
    """一份 report 對「這個身分的結果」的貢獻。回 None 表示這份 report 不改變結果。

    **屬性一律帶預設值讀** —— 既有測試的假 report 只有 `when` / `failed` /
    `nodeid` / `fspath`;直接讀 `report.skipped` 會讓它們 AttributeError
    (紅燈規劃書一、B-1 約束 4)。
    """
    if getattr(report, "failed", False):
        return "failed"
    xfail = getattr(report, "wasxfail", None) is not None
    when = getattr(report, "when", None)
    if getattr(report, "skipped", False):
        return "other" if xfail else "skipped"
    if when == "call" and getattr(report, "passed", False):
        return "other" if xfail else "passed"
    return None


def pytest_runtest_logreport(report):
    # setup/teardown 失敗同樣算數:fixture 拋例外只產生 setup 報告,
    # 只認 call 的話「一次不綠的執行」會被記成綠。
    if report.when not in ("call", "setup", "teardown") or _redlight is None:
        return
    # 取自 nodeid,不是 fspath。nodeid 本來就帶著相對 rootdir 的路徑;
    # fspath 在會 chdir 的測試底下 resolve 到別處,relative_to 直接 ValueError,
    # 整個 session INTERNALERROR 中止 —— 紀錄器把它要觀測的東西弄死了。
    f = report.nodeid.split("::", 1)[0].replace("\\", "/")
    rec = _outcomes.setdefault(f, {"failed": []})
    if report.failed:
        rec["failed"].append(report.nodeid.split("::", 1)[-1])
    # 票 145:逐身分的結果。`failed` 一旦記下就不被後來的 report 蓋掉
    # (teardown 失敗之前的 call 可能是 passed)。
    got = _run_outcome(report)
    if got is not None and _run["outcomes"].get(_nodeid(report)) != "failed":
        _run["outcomes"][_nodeid(report)] = got


def pytest_sessionfinish(session, exitstatus):
    if _redlight is None:
        return
    for f, rec in _outcomes.items():
        _redlight.record_run(f, passed=not rec["failed"], failed_tests=rec["failed"])
    # 票 145:**每個 session 恰好一筆 run 事實**,寫在逐檔紀錄**之後** ——
    # 0 collected、全部 deselected、invocation 錯誤時上面的迴圈一筆都不寫
    # (RECON Collapse ①),這一筆是那些情形唯一留下的痕跡。
    # 舊版 redlight.py(下游未同步)沒有 record_session ⇒ 照舊只寫逐檔紀錄。
    if not hasattr(_redlight, "record_session"):
        return
    selected = _run["selected"] if _run["selected"] is not None else list(_run["outcomes"])
    _redlight.record_session(
        _ROOT,
        exit_code=exitstatus,
        collected=list(selected) + list(_run["deselected"]) + list(_run["collect_errors"]),
        deselected=list(_run["deselected"]),
        outcomes=dict(_run["outcomes"]),
    )
```

### 2.3 `.claude/portable/status.py`（儀表板；本次 +223 / −19）

```diff
--- a/.claude/portable/status.py
+++ b/.claude/portable/status.py
@@ -334,6 +334,200 @@
     return out
 
 
+# ─────────────────────────────────────────────────────────────────────────
+# 票 145(M1-a)—— 依 run 事實判定紅綠
+#
+# 上面的 `_latest_per_file()` **保持原語意不動**(「每檔最新一筆」),只是
+# `_evidence` / `_derived` 不再拿它決定紅綠:最新一筆是一次 `-k` 窄選、全部 skip 的
+# 綠時,它會把較早的紅蓋掉(票 139)。紅綠改由 `ticket_test_state()` 依
+# 票 145〈十三〉修訂後的 ODC-1 判定。
+#
+# run 事實由 `<root>/.claude/hooks/redlight.py` 的 `load_runs()` 讀 ——
+# **per-root 載入,與 `load_gate()` 同一手法**(〈十三〉裁決 1);本檔不另寫解析。
+# ─────────────────────────────────────────────────────────────────────────
+
+_REDLIGHT_CACHE = {}
+
+WHOLE_FILE = u"*"          # 身分不明的紅:視同該檔全部 applicable tests 都是先前紅的
+NO_RUN = u"無 run 證據 / 不可判定"
+
+
+def load_redlight(root):
+    """載入 `<root>/.claude/hooks/redlight.py`。不存在或載不起來回 None。
+
+    **None 不進快取** —— 同一個 root 之後才放進 redlight.py 時要讀得到。
+    """
+    real = os.path.realpath(root)
+    if real in _REDLIGHT_CACHE:
+        return _REDLIGHT_CACHE[real]
+    path = os.path.join(real, ".claude", "hooks", "redlight.py")
+    if not os.path.exists(path):
+        return None
+    try:
+        name = "redlight_for_%s" % abs(hash(real))
+        spec = importlib.util.spec_from_file_location(name, path)
+        mod = importlib.util.module_from_spec(spec)
+        spec.loader.exec_module(mod)
+    except Exception:
+        return None
+    _REDLIGHT_CACHE[real] = mod
+    return mod
+
+
+def _run_facts(root):
+    """(run 事實 list, redlight 模組)。redlight 不在 / 無 `load_runs` / 讀失敗 ⇒ (None, None)。"""
+    rl = load_redlight(root)
+    if rl is None or not hasattr(rl, "load_runs"):
+        return None, None
+    try:
+        return rl.load_runs(root), rl
+    except Exception:
+        return None, None
+
+
+def _identity_file(ident):
+    return str(ident).split("::", 1)[0]
+
+
+def _whole(f):
+    return u"%s::%s" % (f, WHOLE_FILE)
+
+
+def _red_identities_of_row(rec):
+    """一筆舊格式 red 紀錄指名的身分。`failed_tests` 缺欄、為空、或含收集錯誤 ⇒ 身分不明。"""
+    f = rec.get("test_file")
+    names = rec.get("failed_tests")
+    if (not isinstance(names, list) or not names
+            or any(n == u"<collection error>" for n in names)):
+        return {_whole(f)}
+    return {u"%s::%s" % (f, n) for n in names}
+
+
+def _apply_run(run, red, orphan, green_now):
+    """一個 run 事實對每個檔的影響(就地更新三個 dict)。
+
+    退紅(〈十三〉修訂後 ODC-1,file-scoped)—— 三項同時成立才退:
+      1. 該檔的測試集合全部被選到(該檔沒有任何 deselected);
+      2. 已知的紅身分本次實際執行且 passed;身分不明時,該檔全部 collected 身分都要 passed;
+      3. 該檔本次沒有任何 failure。
+    另加 I3:exit code 不在 {0, 1}(中斷、內部錯誤、用法錯誤、取不到)的 run 沒有退紅權。
+
+    孤兒(ODC-2):全選的 run 收集不到某個已知紅身分 ⇒ 移到 orphan,**不退紅**;
+    之後若同名身分再被收集到,移回紅,照常判定。改名不視為延續。
+    """
+    collected = [str(n) for n in (run.get("collected") or [])]
+    deselected = set(str(n) for n in (run.get("deselected") or []))
+    outcomes = run.get("outcomes") or {}
+    exit_ok = run.get("exit_code") in (0, 1)
+    by_file = {}
+    for n in collected:
+        by_file.setdefault(_identity_file(n), []).append(n)
+    for f, idents in by_file.items():
+        errored = any(n.endswith(u"::<collection error>") for n in idents)
+        selected = [n for n in idents if n not in deselected]
+        if not selected and not errored:
+            continue                    # 整檔被排除:這次 run 沒有碰它,證據不變
+        results = [outcomes.get(n) for n in selected]
+        if errored or u"failed" in results:
+            mine = red.setdefault(f, set())
+            mine.update(n for n in selected if outcomes.get(n) == u"failed")
+            if errored:
+                mine.add(_whole(f))
+            green_now[f] = False
+            continue
+        if not any(n in deselected for n in idents):
+            present = set(idents)
+            back = set(n for n in orphan.get(f, ()) if n in present)
+            if back:
+                red.setdefault(f, set()).update(back)
+                orphan[f] -= back
+            gone = set(n for n in red.get(f, ())
+                       if not n.endswith(u"::" + WHOLE_FILE) and n not in present)
+            if gone:
+                red[f] -= gone
+                orphan.setdefault(f, set()).update(gone)
+            if exit_ok and red.get(f):
+                if any(n.endswith(u"::" + WHOLE_FILE) for n in red[f]):
+                    if all(outcomes.get(n) == u"passed" for n in idents):
+                        red[f] = set()
+                else:
+                    red[f] = set(n for n in red[f] if outcomes.get(n) != u"passed")
+        green_now[f] = exit_ok and u"passed" in results
+
+
+def ticket_test_state(records, runs, ticket):
+    """這張票底下每個測試檔的狀態。**純函式,不讀檔。**
+
+    回傳 `{test_file: {"state": "red" | "green" | "unknown" | "orphaned",
+                       "unresolved": [身分...], "orphaned": [身分...]}}`。
+
+    - `records`:`test-runs.jsonl` 的 8 欄紀錄;`runs`:`load_runs()` 的 run 事實。
+    - 兩者依 `time` 排序後依序套用;同一時點 run 事實排在紀錄**之後**
+      (producer 在同一個 session 先寫逐檔紀錄、最後寫 run 事實)。
+    - **8 欄紀錄沒有 run 事實 ⇒ coverage 未知**:red 紀錄加紅,green 紀錄**不退任何紅**,
+      且不能讓該檔變成 green(只到 `unknown`)—— Backward compatibility 2。
+    - `green` 只來自最新一次碰到該檔的 run:exit code ∈ {0, 1}、該檔 ≥1 passed、0 failed。
+    """
+    if not ticket:
+        return {}
+    events = []
+    for i, rec in enumerate(records or []):
+        if (not isinstance(rec, dict) or rec.get("ticket_id") != ticket
+                or not rec.get("test_file")):
+            continue
+        events.append((str(rec.get("time") or u""), 0, i, rec, None))
+    for i, run in enumerate(runs or []):
+        if not isinstance(run, dict) or run.get("ticket_id") != ticket:
+            continue
+        events.append((str(run.get("time") or u""), 1, i, None, run))
+    events.sort(key=lambda e: e[:3])
+
+    red, orphan, green_now = {}, {}, {}
+    for _t, _o, _i, rec, run in events:
+        if rec is not None:
+            f = rec["test_file"]
+            if rec.get("result") == u"red":
+                red.setdefault(f, set()).update(_red_identities_of_row(rec))
+            green_now[f] = False
+            continue
+        _apply_run(run, red, orphan, green_now)
+
+    out = {}
+    for f in set(red) | set(orphan) | set(green_now):
+        r = sorted(red.get(f, ()))
+        o = sorted(orphan.get(f, ()))
+        if r:
+            state = u"red"
+        elif o:
+            state = u"orphaned"
+        elif green_now.get(f):
+            state = u"green"
+        else:
+            state = u"unknown"
+        out[f] = {u"state": state, u"unresolved": r, u"orphaned": o}
+    return out
+
+
+def _last_run_text(facts, rl, ticket):
+    """本票最近一次 run 的一句話。找不到 ⇒ `無 run 證據 / 不可判定`。"""
+    mine = [r for r in (facts or []) if isinstance(r, dict) and r.get("ticket_id") == ticket]
+    if not mine or rl is None or not hasattr(rl, "run_state"):
+        return NO_RUN
+    r = mine[-1]
+    outs = list((r.get("outcomes") or {}).values())
+    return u"%s(exit %s;collected %d / deselected %d / passed %d / failed %d / skipped %d)" % (
+        rl.run_state(r), r.get("exit_code"), len(r.get("collected") or []),
+        len(r.get("deselected") or []), outs.count(u"passed"), outs.count(u"failed"),
+        outs.count(u"skipped"))
+
+
+def _run_source(root, run_log, rl):
+    left = _rel(root, run_log) if run_log else NO_FUNC
+    right = (_rel(root, rl.session_log(root)) if rl is not None and hasattr(rl, "session_log")
+             else u"%s(redlight.py 無 run 事實讀取)" % UNRECORDED)
+    return u"%s + %s" % (left, right)
+
+
 def _waterline_commits(recs):
     """provenance 的**水位線**:每個 `path` 最新一筆憑證的 commit,去重(票 100)。
 
@@ -592,23 +786,26 @@
     # 同一個問題在同一支檔案裡有兩種答案時,讀的人會以為那是刻意的區別。
     # 無票時**不得**印帶「本票」字樣的數字 —— 那不是缺值,是一個錯的宣稱,
     # 而帶著票面語氣的數字,讀的人會直接引用。
-    if runs is None:
+    # 票 145:紅綠改由 `ticket_test_state()` 判定(ODC-1);尾段由「全套結果:未記錄
+    # (帳本不記全套)」改為本票最近一次 run 的事實。**兩本帳都沒有 ⇒ 照舊整行未記錄。**
+    facts, rl = _run_facts(root)
+    if runs is None and not facts:
         val = UNRECORDED
     elif not ticket:
         val = u"%s(無當前票)" % UNRECORDED
     else:
-        latest = _latest_per_file(runs, ticket)
-        red = len([r for r in latest.values() if r.get("result") == "red"])
-        green = len([r for r in latest.values() if r.get("result") == "green"])
+        st = ticket_test_state(runs or [], facts or [], ticket)
+        n = {k: len([1 for s in st.values() if s[u"state"] == k])
+             for k in (u"red", u"green", u"unknown", u"orphaned")}
         last = runs[-1] if runs else None
         tail = (u"最後一筆 %s=%s @ %s" % (_field(last, "test_file"),
                                           _field(last, "result"),
                                           _field(last, "time"))
-                if last else UNRECORDED)
-        val = u"本票(每檔最新一筆)red %d / green %d;%s;全套結果:%s(帳本不記全套)" % (
-            red, green, tail, UNRECORDED)
-    out.append(_line(u"test-runs", val,
-                     _rel(root, run_log) if run_log else NO_FUNC))
+                if last else u"最後一筆 %s" % UNRECORDED)
+        val = u"本票 red %d / green %d / run 事實未知 %d / orphaned %d;%s;最近一次 run:%s" % (
+            n[u"red"], n[u"green"], n[u"unknown"], n[u"orphaned"], tail,
+            _last_run_text(facts, rl, ticket))
+    out.append(_line(u"test-runs", val, _run_source(root, run_log, rl)))
 
     # ── intercepts 印**兩行**,不是一行 ────────────────────────────────
     # 合成一行的話,「這個月還沒有人被擋」與「這個 repo 從來沒有攔截紀錄」
@@ -793,17 +990,24 @@
 
     run_log = _p(gate, "RUN_LOG")
     runs = _read_jsonl(run_log) if run_log else None
-    if runs is None or not ticket:
-        red = green = UNRECORDED
-    else:
-        latest = _latest_per_file(runs, ticket)
-        reds = sorted(f for f, r in latest.items() if r.get("result") == "red")
-        greens = sorted(f for f, r in latest.items() if r.get("result") == "green")
-        red = u" / ".join(reds) if reds else u"(無)"
-        green = u" / ".join(greens) if greens else u"(無)"
-    src = (u"%s 每檔最新一筆" % _rel(root, run_log)) if run_log else NO_FUNC
-    out.append(_line(u"tests red under ticket %s" % (ticket or UNRECORDED), red, src))
-    out.append(_line(u"tests green under ticket %s" % (ticket or UNRECORDED), green, src))
+    facts, rl = _run_facts(root)
+    labels = ((u"red", u"tests red under ticket %s"),
+              (u"green", u"tests green under ticket %s"),
+              (u"unknown", u"tests green (run 事實未知) under ticket %s"),
+              (u"orphaned", u"tests orphaned under ticket %s"))
+    vals = {}
+    if (runs is None and not facts) or not ticket:
+        vals = dict((k, UNRECORDED) for k, _l in labels)
+    else:
+        st = ticket_test_state(runs or [], facts or [], ticket)
+        for k, _l in labels:
+            files = sorted(f for f, s in st.items() if s[u"state"] == k)
+            if k == u"orphaned":
+                files = [u"%s(%s)" % (f, u", ".join(st[f][u"orphaned"])) for f in files]
+            vals[k] = u" / ".join(files) if files else u"(無)"
+    src = u"%s(票 145 ODC-1)" % _run_source(root, run_log, rl)
+    for k, label in labels:
+        out.append(_line(label % (ticket or UNRECORDED), vals[k], src))
 
     if not _has(gate, "rule_codes"):
         rules = NO_FUNC
```

### 2.4 `tests/test_status.py` 對既有測試 fixture 的補件（只新增，既有斷言未改）

```diff
--- a/tests/test_status.py
+++ b/tests/test_status.py
@@ -563,6 +563,18 @@
                      "w", encoding="utf-8") as f:
             for r in recs:
                 f.write(json.dumps(r, ensure_ascii=False) + "\n")
+        # 票 145〈十三〉裁決 2(C):Station 4 補 run-level facts。
+        # 上面 test_a 的綠紀錄是 8 欄格式、沒有 run 事實 ⇒ 依 ODC-1 沒有退紅權;
+        # 補一次「test_a 全檔被選到、唯一一條實際執行且通過、該檔無 failure」的 run,
+        # 時點與那筆綠相同。紅紀錄沒有 failed_tests(身分不明)⇒ 依〈十三〉裁決 3,
+        # 該檔全部 collected 身分都要 passed —— 這個 run 滿足它。
+        # 第一行讓 fake repo 有 redlight.py:status 依 root 載入它讀 run 事實(裁決 1)。
+        shutil.copy2(str(REAL_REDLIGHT),
+                     str(pathlib.Path(root) / ".claude" / "hooks" / "redlight.py"))
+        redlight.record_session(
+            root, run_id=u"fixture-570-571", time=u"2026-09-02T02:00:00+00:00",
+            ticket_id=u"99", exit_code=0, collected=[u"tests/test_a.py::test_one"],
+            deselected=[], outcomes={u"tests/test_a.py::test_one": u"passed"})
 
         out = render(root)
         red = _value_of(out, u"tests red under ticket 99")
```

---

## 三、紅燈測試（實作前寫好、實作前 14 支全部失敗、實作時未修改）

### 3.1 `tests/test_redlight.py`（第 240 行起）

```python
# **隔離**:conftest 模組載入時會自己載一份 redlight.py,而那一份的 RUN_LOG
# 指向真實帳本(`tests/conftest.py:129-133`)。驅動前一律把 conftest 的
# `_redlight` 換成本檔這一份、並把路徑指到 tmp —— 少一個,假紀錄就會寫進真實帳本。
# ─────────────────────────────────────────────────────────────────────────────


class _Item:
    def __init__(self, nodeid):
        self.nodeid = nodeid


class _CollectRep:
    def __init__(self, nodeid, failed=False):
        self.nodeid = nodeid
        self.failed = failed
        self.passed = not failed
        self.outcome = "failed" if failed else "passed"


class _RunRep:
    def __init__(self, nodeid, when, outcome):
        self.nodeid = nodeid
        self.fspath = nodeid.split("::", 1)[0]
        self.when = when
        self.outcome = outcome
        self.passed = outcome == "passed"
        self.failed = outcome == "failed"
        self.skipped = outcome == "skipped"


def _reports_for(nodeid, outcome):
    """一條測試在 pytest 裡實際產生的 report 序列。

    passed / failed:setup → call → teardown;skipped:setup(skipped)→ teardown,
    **沒有 call**(skip 在 setup 階段就決定了)。
    """
    if outcome == "skipped":
        return [_RunRep(nodeid, "setup", "skipped"),
                _RunRep(nodeid, "teardown", "passed")]
    return [_RunRep(nodeid, "setup", "passed"),
            _RunRep(nodeid, "call", outcome),
            _RunRep(nodeid, "teardown", "passed")]


class _Session:
    def __init__(self, items):
        self.items = list(items)
        self.testscollected = len(self.items)


def _isolated_conftest(monkeypatch, tmp_path):
    c = TestTheRecorderCannotKillTheRunner._conftest()
    monkeypatch.setattr(redlight, "ROOT", str(tmp_path))
    monkeypatch.setattr(redlight, "RUN_LOG",
                        str(tmp_path / ".dev" / "test-runs.jsonl"))
    monkeypatch.setattr(redlight, "PIPELINE",
                        str(tmp_path / ".dev" / "pipeline.json"))
    monkeypatch.setattr(c, "_redlight", redlight)
    monkeypatch.setattr(c, "_ROOT", tmp_path)
    c._outcomes.clear()
    return c


def _drive_session(c, collect_files=(), collect_errors=(), selected=(),
                   deselected=(), outcomes=None, exitstatus=0):
    """依 pytest 的實際呼叫順序,對 conftest 呼叫**標準 hook 名稱**。

    conftest 沒實作的 hook 以 no-op 跳過 —— 測試不依賴 producer 用了哪幾個 hook
    (那是 Station 4 的實體決定)。
    """
    def hook(name):
        return getattr(c, name, None) or (lambda *a, **k: None)

    for f in collect_files:
        hook("pytest_collectreport")(_CollectRep(f))
    for f in collect_errors:
        hook("pytest_collectreport")(_CollectRep(f, failed=True))
    items = [_Item(n) for n in selected]
    gone = [_Item(n) for n in deselected]
    if gone:
        hook("pytest_deselected")(gone)
    session = _Session(items)
    hook("pytest_collection_finish")(session)
    for nodeid, outcome in (outcomes or {}).items():
        for rep in _reports_for(nodeid, outcome):
            hook("pytest_runtest_logreport")(rep)
    hook("pytest_sessionfinish")(session, exitstatus)


class TestRunFacts:

    def test_a_full_pass_is_state_a_with_coverage_visible(self, tmp_path, monkeypatch):
        """RL-1 Full pass。現行 HEAD:**介面紅**(`redlight.load_runs` 不存在)。"""
        c = _isolated_conftest(monkeypatch, tmp_path)
        ids = ["tests/test_thing.py::test_a", "tests/test_thing.py::test_b"]
        _drive_session(c, collect_files=["tests/test_thing.py"], selected=ids,
                       outcomes={ids[0]: "passed", ids[1]: "passed"}, exitstatus=0)
        runs = redlight.load_runs(str(tmp_path))
        assert len(runs) == 1, runs
        assert redlight.run_state(runs[0]) == "A", runs[0]
        assert sorted(runs[0]["collected"]) == sorted(ids), runs[0]
        assert list(runs[0]["deselected"]) == [], runs[0]

    def test_one_failure_is_state_b_and_names_the_test(self, tmp_path, monkeypatch):
        """RL-2 One failure。現行 HEAD:**介面紅**(`redlight.load_runs` 不存在)。"""
        c = _isolated_conftest(monkeypatch, tmp_path)
        ids = ["tests/test_thing.py::test_a", "tests/test_thing.py::test_b"]
        _drive_session(c, collect_files=["tests/test_thing.py"], selected=ids,
                       outcomes={ids[0]: "passed", ids[1]: "failed"}, exitstatus=1)
        runs = redlight.load_runs(str(tmp_path))
        assert len(runs) == 1, runs
        assert redlight.run_state(runs[0]) == "B", runs[0]
        assert runs[0]["outcomes"][ids[1]] == "failed", runs[0]

    def test_zero_collected_is_state_c_and_the_run_is_visible(self, tmp_path, monkeypatch):
        """RL-3 Zero tests collected。現行 HEAD:**介面紅**(`redlight.load_runs` 不存在)。

        底層行為缺口:HEAD 對此情形一筆都不寫(`conftest.py:171-172` 迴圈 0 次),
        與「根本沒跑」不可分 —— 修後必須留下一筆 run 事實。
        """
        c = _isolated_conftest(monkeypatch, tmp_path)
        _drive_session(c, exitstatus=5)
        runs = redlight.load_runs(str(tmp_path))
        assert len(runs) == 1, u"0 collected 的 run 沒有留下事實,與 E 不可分:%r" % runs
        assert redlight.run_state(runs[0]) == "C", runs[0]

    def test_a_collection_error_is_state_d(self, tmp_path, monkeypatch):
        """RL-4(a) Collection failure。現行 HEAD:**介面紅**(`redlight.load_runs` 不存在)。"""
        c = _isolated_conftest(monkeypatch, tmp_path)
        _drive_session(c, collect_errors=["tests/test_broken.py"], exitstatus=2)
        runs = redlight.load_runs(str(tmp_path))
        assert len(runs) == 1, runs
        assert redlight.run_state(runs[0]) == "D", runs[0]

    def test_a_usage_error_is_state_d_not_green(self, tmp_path, monkeypatch):
        """RL-4(b) Runner invocation error。現行 HEAD:**介面紅**(`redlight.load_runs` 不存在)。

        producer 本身沒被載入的子情形不在這裡 —— 那是 ODC-3(見 tests/test_status.py)。
        """
        c = _isolated_conftest(monkeypatch, tmp_path)
        _drive_session(c, exitstatus=4)
        runs = redlight.load_runs(str(tmp_path))
        assert len(runs) == 1, runs
        assert redlight.run_state(runs[0]) == "D", runs[0]

    def test_an_interrupted_run_is_state_d_even_with_passes(self, tmp_path, monkeypatch):
        """RL-4(c) 執行被中斷。現行 HEAD:**介面紅**(`redlight.load_runs` 不存在)。

        中斷前已有一條通過 —— 那不得讓這個 run 變成 A。
        """
        c = _isolated_conftest(monkeypatch, tmp_path)
        ids = ["tests/test_thing.py::test_a", "tests/test_thing.py::test_b"]
        _drive_session(c, collect_files=["tests/test_thing.py"], selected=ids,
                       outcomes={ids[0]: "passed"}, exitstatus=2)
        runs = redlight.load_runs(str(tmp_path))
        assert len(runs) == 1, runs
        assert redlight.run_state(runs[0]) == "D", runs[0]

    def test_three_skipped_645_deselected_is_state_f_with_counts(self, tmp_path, monkeypatch):
        """RL-6' 票 139 現場重現(producer 側)。現行 HEAD:**介面紅**(`redlight.load_runs` 不存在)。

        `-k "symlink"` 的形狀:選到 3 條、全部 skip,645 條 deselected,0 passed、0 failed。
        """
        c = _isolated_conftest(monkeypatch, tmp_path)
        chosen = ["tests/test_gate.py::test_symlink_%d" % i for i in range(3)]
        gone = ["tests/test_gate.py::test_other_%d" % i for i in range(645)]
        _drive_session(c, collect_files=["tests/test_gate.py"], selected=chosen,
                       deselected=gone,
                       outcomes={n: "skipped" for n in chosen}, exitstatus=0)
        runs = redlight.load_runs(str(tmp_path))
        assert len(runs) == 1, runs
        run = runs[0]
        assert redlight.run_state(run) == "F", run
        assert len(run["deselected"]) == 645, len(run["deselected"])
        assert [v for v in run["outcomes"].values()].count("skipped") == 3, run["outcomes"]
        assert "passed" not in run["outcomes"].values(), run["outcomes"]
```

### 3.2 `tests/test_status.py`（第 1140 行起；其中 570/571 補件已列在 2.4）

```python
# 經票 145〈十三〉裁決修正(status 依 root 載入 redlight.py 的讀取函式;
# ODC-1 第 2、3 項 file-scoped)。
#
# **新介面(`record_session` / `load_runs` / `ticket_test_state`)只在測試函式內部取用**
# —— 它們不存在時只有這幾支失敗,不會讓整個檔收集錯誤。
#
# **既有的 `_make_root()` 一字不改**;要 redlight.py 的 fake repo 走下面的
# `_root_with_redlight()`(〈十三〉裁決 2 允許的 fake repo 基礎設施)。
# ═══════════════════════════════════════════════════════════════════════════

REAL_REDLIGHT = ROOT / ".claude" / "hooks" / "redlight.py"


def _load_redlight():
    """載入 repo 的 redlight.py(既有模組;新函式在測試內才取用)。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "redlight_for_status_test", str(REAL_REDLIGHT))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


redlight = _load_redlight()


def _root_with_redlight(base, **kw):
    """`_make_root()` 造出的最小 repo,再放一份 redlight.py 真檔複本。"""
    root = _make_root(base, **kw)
    shutil.copy2(str(REAL_REDLIGHT),
                 str(pathlib.Path(root) / ".claude" / "hooks" / "redlight.py"))
    return root


def _write_raw_lines(root, lines):
    """歷史原始紀錄**逐字**寫入 —— 不經 json 往返,一個位元組都不動。"""
    with io.open(str(pathlib.Path(root) / ".dev" / "test-runs.jsonl"),
                 "w", encoding="utf-8", newline="\n") as f:
        for ln in lines:
            f.write(ln + u"\n")


def _rows_of(root):
    p = pathlib.Path(root) / ".dev" / "test-runs.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in io.open(str(p), encoding="utf-8") if l.strip()]


# `.dev/test-runs.jsonl` 第 940 行與第 970 行原文(後者 = 票 139 `:39`)。
LEDGER_940 = (u'{"test_file": "tests/test_gate.py", "time": "2026-09-13T07:28:31.037700+00:00", '
              u'"result": "red", "failed_tests": ["TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce"], '
              u'"impl_file": ".claude/hooks/gate.py", "impl_exists": true, '
              u'"impl_hash": "2215f109bb73277248f78a6110a90bf51ec8a5f215251cf6089b86ebbe215170", '
              u'"ticket_id": "133"}')
LEDGER_970 = (u'{"test_file": "tests/test_gate.py", "time": "2026-09-13T12:26:18.644697+00:00", '
              u'"result": "green", "failed_tests": [], '
              u'"impl_file": ".claude/hooks/gate.py", "impl_exists": true, '
              u'"impl_hash": "446b2ef6f49fa0608d347d9969b49a0f3fa682d11cfe47b622feaa80cdbb7dc2", '
              u'"ticket_id": "133"}')

# `.dev/test-runs.jsonl` 第 2036 行原文(Station 3 baseline 寫入)。
LEDGER_2036 = (u'{"test_file": "tests/test_status.py", "time": "2026-10-02T13:27:56.450055+00:00", '
               u'"result": "green", "failed_tests": [], '
               u'"impl_file": ".claude/portable/status.py", "impl_exists": true, '
               u'"impl_hash": "bdc3a089a33d179dc72eb937401520c5ec257ba11037fb42083420a9560fadf0", '
               u'"ticket_id": "145"}')

NO_RUN = u"最近一次 run:無 run 證據 / 不可判定"


@pytest.fixture
def redlight_guard(tmp_path, monkeypatch):
    """本檔那一份 redlight 的路徑一律指到 tmp 的**另一個**位置。

    `record_session(root, ...)` 應該寫到 `root`;若實作忽略 `root` 而寫到模組常數,
    這裡讓它落在 guard 目錄 —— 測試會因為 status 讀不到而紅(出聲),
    **而不是把假紀錄寫進真實帳本**。
    """
    guard = tmp_path / u"guard"
    monkeypatch.setattr(redlight, "ROOT", str(guard))
    monkeypatch.setattr(redlight, "RUN_LOG", str(guard / ".dev" / "test-runs.jsonl"))
    monkeypatch.setattr(redlight, "PIPELINE", str(guard / ".dev" / "pipeline.json"))
    return guard


class TestTicket139:

    def test_a_narrow_all_skip_record_does_not_retire_the_earlier_red(self, tmp_path):
        """RL-6 票 139 歷史重現。現行 HEAD:**行為紅**。

        帳本只有兩筆、逐字取自真實帳本(第 940 行 red、第 970 行 = 票 139 `:39` green),
        沒有任何 synthetic 欄位。第 970 行沒有 run 事實 ⇒ coverage 未知 ⇒ 無退紅權
        (〈十一〉/〈十三〉ODC-1)⇒ 第 940 行那條紅不得因為「每檔最新一筆」而消失。
        現行 HEAD 取最新一筆 ⇒ 判成 green —— 那就是票 139 的 false green。
        """
        root = _root_with_redlight(tmp_path, ticket=u"133")
        _write_raw_lines(root, [LEDGER_940, LEDGER_970])
        out = render(root)
        red = _value_of(out, u"tests red under ticket 133")
        green = _value_of(out, u"tests green under ticket 133")
        assert u"tests/test_gate.py" not in green, (
            u"窄選、全部 skip 的那一筆把較早的紅蓋成綠了(票 139)\nred=%s\ngreen=%s"
            % (red, green))
        assert u"tests/test_gate.py" in red, red


class TestNarrowSelection:

    def test_a_later_green_without_run_facts_does_not_retire_x(self, tmp_path, monkeypatch):
        """RL-6b(舊寫入版)。現行 HEAD:**行為紅**。

        只用既有的 `redlight.record_run()` 寫:X 紅 → 同檔綠。那筆綠沒有 run 事實,
        看不出它有沒有選到 X ⇒ 不得退紅。現行 HEAD 取最新一筆 ⇒ 判成 green。
        """
        root = _root_with_redlight(tmp_path)
        monkeypatch.setattr(redlight, "ROOT", root)
        monkeypatch.setattr(redlight, "RUN_LOG",
                            str(pathlib.Path(root) / ".dev" / "test-runs.jsonl"))
        monkeypatch.setattr(redlight, "PIPELINE",
                            str(pathlib.Path(root) / ".dev" / "pipeline.json"))
        redlight.record_run("tests/test_x.py", passed=False, failed_tests=["test_target"])
        redlight.record_run("tests/test_x.py", passed=True, failed_tests=[])
        out = render(root)
        red = _value_of(out, u"tests red under ticket 99")
        green = _value_of(out, u"tests green under ticket 99")
        assert u"tests/test_x.py" not in green, (
            u"沒有 run 事實的綠把較早的紅蓋掉了\nred=%s\ngreen=%s" % (red, green))
        assert u"tests/test_x.py" in red, red

    def test_a_narrow_run_that_did_not_select_x_does_not_retire_x(self, tmp_path, redlight_guard):
        """RL-6b(run 事實版)。現行 HEAD:**介面紅**(`redlight.record_session` 不存在)。

        run1:X 失敗。run2:同檔窄選,選到的 Y 通過,**X 在 deselected** ⇒
        ODC-1 第 1 項不成立 ⇒ X 不退紅;run2 的 deselected 數事後可見(I7)。
        """
        root = _root_with_redlight(tmp_path)
        x = u"tests/test_x.py::test_target"
        y = u"tests/test_x.py::test_other"
        redlight.record_session(root, run_id=u"rl6b-1", time=u"2026-09-02T01:00:00+00:00",
                                ticket_id=u"99", exit_code=1, collected=[x, y],
                                deselected=[], outcomes={x: u"failed", y: u"passed"})
        redlight.record_session(root, run_id=u"rl6b-2", time=u"2026-09-02T02:00:00+00:00",
                                ticket_id=u"99", exit_code=0, collected=[x, y],
                                deselected=[x], outcomes={y: u"passed"})
        out = render(root)
        red = _value_of(out, u"tests red under ticket 99")
        assert u"tests/test_x.py" in red, red
        state = status.ticket_test_state(_rows_of(root), redlight.load_runs(root), u"99")
        assert x in state[u"tests/test_x.py"][u"unresolved"], state
        assert u"deselected 1" in _value_of(out, u"test-runs"), _value_of(out, u"test-runs")


class TestHistoricalRecords:

    def test_old_green_rows_are_shown_as_run_unknown_not_green(self, tmp_path):
        """RL-7 Historical evidence。現行 HEAD:**行為紅**(依 I5 判讀)。

        帳本第 2036 行原文 —— 一筆**真實**、來自一次確實全套通過的執行的 green;
        而帳本仍證明不了這件事。舊格式紀錄缺 run 事實 ⇒ 只能是「run 事實未知」,
        不得印在 green(Backward compatibility 2:不得推論 full pass)。
        """
        root = _root_with_redlight(tmp_path, ticket=u"145")
        _write_raw_lines(root, [LEDGER_2036])
        out = render(root)
        green = _value_of(out, u"tests green under ticket 145")
        assert u"tests/test_status.py" not in green, (
            u"沒有 run 事實的舊紀錄被印成 green:%s" % green)
        unknown = _value_of(out, u"tests green (run 事實未知) under ticket 145")
        assert unknown is not None and u"tests/test_status.py" in unknown, out


class TestOrphans:

    def test_a_renamed_red_test_is_orphaned_not_green(self, tmp_path, redlight_guard):
        """ODC-2 被刪除 / 改名的紅。現行 HEAD:**介面紅**(`redlight.record_session` 不存在)。

        run1:test_old 失敗。run2:同檔全選、全部通過,但收集不到 test_old(改名成 test_new)
        ⇒ 改名不視為延續 ⇒ 舊紅不得自動變綠,保留為可觀察的 orphaned。
        """
        root = _root_with_redlight(tmp_path)
        old = u"tests/test_x.py::test_old"
        new = u"tests/test_x.py::test_new"
        keep = u"tests/test_x.py::test_keep"
        redlight.record_session(root, run_id=u"odc2-1", time=u"2026-09-02T01:00:00+00:00",
                                ticket_id=u"99", exit_code=1, collected=[old, keep],
                                deselected=[], outcomes={old: u"failed", keep: u"passed"})
        redlight.record_session(root, run_id=u"odc2-2", time=u"2026-09-02T02:00:00+00:00",
                                ticket_id=u"99", exit_code=0, collected=[new, keep],
                                deselected=[], outcomes={new: u"passed", keep: u"passed"})
        out = render(root)
        orphaned = _value_of(out, u"tests orphaned under ticket 99")
        green = _value_of(out, u"tests green under ticket 99")
        assert orphaned is not None and u"tests/test_x.py" in orphaned, out
        assert u"test_old" in orphaned, orphaned
        assert u"tests/test_x.py" not in green, green


class TestRunEvidence:

    def test_no_run_at_all_is_not_zero_tests_and_not_a_pass(self, tmp_path, redlight_guard):
        """RL-5 No invocation。現行 HEAD:**介面紅**(`redlight.record_session` 不存在)。

        兩個 root:B 有一次 0 collected 的 run(狀態 C),A 完全沒有 run 事實(E)。
        兩者在輸出上必須分得開,且 A 不得被推論成任何 run 事實。
        """
        root_b = _root_with_redlight(tmp_path / u"b")
        redlight.record_session(root_b, run_id=u"rl5-c", time=u"2026-09-02T01:00:00+00:00",
                                ticket_id=u"99", exit_code=5, collected=[],
                                deselected=[], outcomes={})
        root_a = _root_with_redlight(tmp_path / u"a", with_runs=True)
        assert redlight.load_runs(root_a) == [], u"沒有 run 卻讀出了 run 事實"
        val_a = _value_of(render(root_a), u"test-runs")
        val_b = _value_of(render(root_b), u"test-runs")
        assert NO_RUN in val_a, val_a
        assert u"最近一次 run:C" in val_b, val_b
        assert val_a != val_b

    def test_no_producer_means_undecidable_not_green_not_c(self, tmp_path, redlight_guard):
        """ODC-3 producer 未載入。現行 HEAD:**介面紅**(`redlight.load_runs` 不存在)。

        帳本有舊格式紀錄、沒有任何 run 事實(producer 沒被載入時就是這樣)⇒
        記為「無證據 / 不可判定」;不得表示為 green,也不得推論為 C。
        """
        root = _root_with_redlight(tmp_path, ticket=u"145")
        _write_raw_lines(root, [LEDGER_2036])
        assert redlight.load_runs(root) == [], u"沒有 run 卻讀出了 run 事實"
        out = render(root)
        val = _value_of(out, u"test-runs")
        assert NO_RUN in val, val
        assert u"最近一次 run:C" not in val, val
        assert u"tests/test_status.py" not in _value_of(out, u"tests green under ticket 145")
```

---

## 四、執行證據

### 4.1 實作前（紅燈階段）
固定指令全套：`14 failed, 1912 passed, 3 skipped, 3 xfailed`，失敗的恰好是上面 14 支新測試。

### 4.2 實作後
固定指令全套：exit code 0；`1926 passed, 3 skipped, 3 xfailed`。

### 4.3 實作後儀表板輸出（相關行）
```
test-runs: 本票 red 0 / green 46 / run 事實未知 0 / orphaned 0;最近一次 run:A(exit 0;collected 1932 / deselected 0 / passed 1926 / failed 0 / skipped 3)
tests red under ticket 145: (無)
tests green (run 事實未知) under ticket 145: (無)
tests orphaned under ticket 145: (無)
```

### 4.4 `.dev/test-sessions.jsonl` 的一筆 session 紀錄（截斷樣本）
```json
{
  "kind": "session",
  "run_id": "66de864e63fc45c9978331601f3e5d91",
  "time": "2026-10-02T14:51:04.809936+00:00",
  "ticket_id": "145",
  "exit_code": 0,
  "collected": [
    "tests/test_adr_numbering.py::TestAdrNumbersCarryTheirPrefix::test_the_adr_directory_is_not_empty",
    "tests/test_adr_numbering.py::TestAdrNumbersCarryTheirPrefix::test_no_bare_number_after_the_switch_point",
    "tests/test_adr_numbering.py::TestAdrNumbersCarryTheirPrefix::test_nothing_is_unclassified",
    "…(共 1932 筆)"
  ],
  "deselected": [],
  "outcomes": {
    "tests/test_adr_numbering.py::TestAdrNumbersCarryTheirPrefix::test_the_adr_directory_is_not_empty": "passed",
    "tests/test_adr_numbering.py::TestAdrNumbersCarryTheirPrefix::test_no_bare_number_after_the_switch_point": "passed",
    "tests/test_adr_numbering.py::TestAdrNumbersCarryTheirPrefix::test_nothing_is_unclassified": "passed",
    "…": "(共 1932 筆)"
  }
}

```
outcomes 值的分布：{'passed': 1926, 'other': 3, 'skipped': 3}
該筆紀錄單行大小約 455874 bytes。

### 4.5 帳本
- `.dev/test-runs.jsonl` 實作前的 576,717 bytes 在實作後逐位元組不變（只追加）。
