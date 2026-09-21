# 票 142 —— 站別定義檔的修改限制:**已檢查的閘門路徑未涵蓋**

**狀態**:**candidate。只登記,本輪不修、不選保護方案。**
**優先度**:**未定** —— 見〈時鐘〉欄。
**發現於**:2026-09-16,做票 133 批二 #8/#9 的來源分流量測時(B3 補量輪)。
**來源**:票 133 批二 #8/#9 的隔離量測(A / B2 / B3 三變體)。
**報告**:`.dev/reports/2026-09-16T0929Z-ticket133-cell8-cell9-b3-measured.md`
(⚠ `.dev/` 不進版控 —— 報告只在**本機**,所以原始輸出**逐字抄進本票**)。

---

## ⚠ 本票的證據邊界(先寫)

- 本票的量測**只涵蓋 R2 / R3 這條路徑**(`is_source_path` → `check()`)。
- **未查**:G1 保護清單、`.githooks/` 的其他掛載、`skills-update.sh`、
  CI、檔案系統權限、以及任何本票沒有點名的機制。
- ⇒ **本票不主張「沒有任何機器在守」。** 它主張的是一句**範圍受限**的話,
  逐字寫在〈命題〉裡。
- 本票**不指定保護方案**,〈修法選項〉一欄**刻意留空**。

---

## 命題(**逐字,照 2026-09-16 裁決的措辭,不得改寫**)

> **已檢查的 R2/R3 路徑不把 `pipeline-stages.yaml` 當原始碼;
> 本輪尚未確認是否存在其他修改限制或授權驗證機制。**

---

## 為什麼這件事值得登記

`CLAUDE.md` 對這個檔案有**唯讀要求**,而且是用最強的措辭下的:

> **站別與順序的唯一定義:`.agents/pipeline-stages.yaml`(唯讀,不被任何流程寫入)。**

檔案自己的檔頭也再說一次:

```
# 開發流程站別 —— 唯一定義來源(唯讀)
#
# 只被讀的是定義,會被寫的是狀態,兩者不同居:
#   定義(本檔)          純規格,不被任何流程寫入
#   狀態(.dev/pipeline.json)  執行期由 skill 寫入 current_stage
```

**而「唯讀」這兩個字在本輪檢查的路徑上是一句祈使句。**
這正是 `CLAUDE.md` 那條常駐檢查項的形狀:

> **「要留存」是祈使句,而祈使句沒有主詞。**
> 每寫下一句「X 要留存 / 要記得 / 不能當成一次性的」,立刻問
> **「不做會有什麼東西叫?」**

本票就是把那個問句對「唯讀」問一次的結果 —— 而**在 R2/R3 這條路徑上,答案是沒有東西叫**。
(⚠ 其他路徑**未查**,見〈證據邊界〉。)

**另一半的份量**:這個檔案不是普通設定檔。R2 用它決定**哪一站可以寫原始碼**,
R3 用它決定**哪一站可以跳過測試**(`exempts_r3_in_scope`)。
`check()` 裡 `stage` 與 `stages` 交會的那一行是**唯一**的對應鍵,
而**沒有任何一方驗證對方**:

```python
    stage_def = next((s for s in stages if s.get("id") == stage), None)
```

(`.claude/hooks/gate.py:2605`)

---

## 檔案與符號依據

| 項目 | 值 |
|---|---|
| 對象 | `.agents/pipeline-stages.yaml` |
| 分類函式 | `gate.is_source_path()` |
| 命中的非原始碼**目錄**清單 | `gate.NON_SOURCE_DIRS` 含 `.agents` |
| 命中的非原始碼**副檔名**清單 | `gate.NON_SOURCE_EXT` 含 `.yaml` |
| 常數定義 | `gate.py:34` `STAGES_DEF = os.path.join(ROOT, ".agents", "pipeline-stages.yaml")  # 定義(唯讀)` |
| 讀取函式 | `gate.load_stage_defs()`(`gate.py:1295`) |
| 消費點(R2) | `gate.py:2599` `writable_stage_ids(stages)`、`gate.py:2605-2606` `stage_def` / `scope` |
| 消費點(R3) | `gate.py:2767` `if (stage_def and stage_def.get("exempts_r3_in_scope") and _under_research(r)):` |
| 另一個讀取端 | `gate.stage_allows_src_write()`(`gate.py:1343`),由 `.claude/portable/status.py:788` 消費 |
| `GATE_SELF` 是否含它 | **否** |

### 原始輸出(逐字,`import` 正式 repo 的 `gate.py`,只讀不寫)

```
gate.__file__          = C:\projects\agent-gates\.claude\hooks\gate.py
gate.ROOT              = C:\projects\agent-gates

is_source_path('.agents/pipeline-stages.yaml') = False
'.agents' in NON_SOURCE_DIRS = True
'.yaml'   in NON_SOURCE_EXT  = True

check(.agents/pipeline-stages.yaml, at_commit=False) -> None   trace=[]
check(.agents/pipeline-stages.yaml, at_commit=True) -> None   trace=[]

GATE_SELF 含它嗎 = False
NON_SOURCE_DIRS = ['.agents', '.dev', '.git', '.venv', '__pycache__', 'assets', 'build', 'docs', 'logs', 'node_modules', 'scripts', 'skills', 'tests', 'tradingagents.egg-info']
NON_SOURCE_EXT  = ['.adoc', '.cfg', '.csv', '.db', '.duckdb', '.example', '.gif', '.gz', '.ico', '.ini', '.jpeg', '.jpg', '.json', '.lock', '.log', '.md', '.ods', '.parquet', '.pdf', '.png', '.properties', '.pyc', '.pyo', '.rst', '.sample', '.sqlite', '.svg', '.template', '.toml', '.tsv', '.txt', '.xls', '.xlsx', '.xml', '.yaml', '.yml', '.zip']
```

**`trace` 兩個時點都是空的** —— 不是「R2/R3 判過了然後放行」,是
**R2/R3 的職責範圍根本沒有被進入**(`trace` 的語意見 `gate.py:2765` 附近的註解:
「這條規則的職責範圍被進入」)。

⚠ **分類本身不是缺陷。** 它是黑名單設計的**正確結果** ——
`.yaml` 不會被執行,把它當原始碼擋下是誤擋。
**本票登記的是「所以這條路徑不涵蓋它」這個事實,不是主張分類判錯。**

---

## 與這條判準的關係

`CLAUDE.md` 的常駐檢查項:

> **任何要進非原始碼清單的目錄,先問兩件事 ——
> 「它會不會裝著判定邏輯」與「它會不會裝著唯一的觀測」。**

`.agents/` 在非原始碼清單裡,而 `pipeline-stages.yaml` **裝著判定邏輯的輸入** ——
R2 的可寫站集合、R3 的豁免開關,都從它長出來。
⇒ **本票是 `F-011` / `F-021` 那一脈的同一個形狀**,換到定義檔這一格。
(⚠ 是否要**併入**那一脈、還是獨立成族,**本票不裁。**)

---

## 查重(**沿用 2026-09-16 前輪的查重結果,本輪不擴大調查**)

前輪對 `docs/tickets/framework-updates/*.md` 全文 `grep "pipeline-stages"`,13 檔命中,逐一判讀:

| 票 | 是不是這件事 |
|---|---|
| **135**(`.dev/pipeline.json` 沒有任何守衛) | ❌ 對象是**執行狀態檔**,不是定義檔 |
| **117**(`pipeline.json` 沒有格式檢查) | ❌ 同上;它提到「值域由 `pipeline-stages.yaml` 決定」,但守的是 json |
| **94**(六站是名字沒人守) | ❌ 它逐字寫「**不動 `pipeline-stages.yaml`** —— 它是權威來源,本票只是指向它」 |
| **51 ⑧** | ❌ 講的是 research 站的 `skill` 指向不存在的目錄 |
| **133**(來源票) | 部分 —— #8/#9 講的是**來源**(該讀工作樹還是 index),不是**修改權限** |

**編號可用性**:`docs/tickets/framework-updates/` 現有最大號 **141**;
全庫 `grep "票 142"` / `"ticket 142"` / `"^142-"` **零命中** ⇒ **142 未被占用**。

---

## 與其他票的關係

| 票 | 關係 |
|---|---|
| **133**(批二 #8/#9) | **本票的來源。** 133 問「#8/#9 該讀哪一版定義」;**「誰可以改那份定義」在本票** |
| **141** | **同一個形狀,不同對象**:141 是 legacy 清單第一行的 go-live sha「身分沒人驗」,本票是站別定義檔「修改限制未查」。兩者都是**判定的前提本身可被改** |
| **135 / 117** | **相鄰但不同**:那兩票守 `.dev/pipeline.json`(狀態),本票的對象是 `.agents/pipeline-stages.yaml`(定義) |
| **94** | 引用關係:94 明著把本檔當成**權威來源**而不動它 ⇒ 本票登記的正是那個「被當成權威」的東西的守備範圍 |
| **24** | 同族(**不可自助**的豁免):`exempts_r3_in_scope` 是一個豁免開關,而它住在本檔裡 |

---

## 修法選項

**刻意留空。** 本輪不指定保護方案 ——
要先有〈證據邊界〉列的那些未查項目的答案,才知道這一格缺的是什麼。

⚠ **不得把本票讀成「應該把 `.agents/` 移出非原始碼清單」** ——
那是一個**具體方案**,而本票沒有裁它。

---

## 時鐘

**說不出來 —— 因此停在 `candidate`,不排進順序。**

已知的**觸發條件候選**(未裁,不當成時鐘):

> **下一次有人主張「站別定義是唯讀的、改不動」的時候** ——
> 那句話在本票未解之前,**在 R2/R3 這條路徑上沒有機器支撐**,
> 而說的人不會知道自己引的是一句祈使句還是一個機制。

⚠ 照 `issue-tracker.md` 的規矩:規矩要的不是每張票都有期限,
是**每張票都被問過這個問題**。本票問過了,答不出日期。
