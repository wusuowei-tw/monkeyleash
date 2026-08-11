# ADR 0011 — research 站:探索區,寫入綁路徑,生產不得依賴它

日期:2026-08-11
狀態:已採納

## 問題

需要一個「探索/研究」的模式:可以快速寫程式試東西,不必先寫測試、不必走完六站。
但探索碼不能污染生產 —— 試出來的東西要進生產,必須經過正規流程。

## 裁決

### 1. research 是**階段**,不是規則開關

放進 `pipeline-stages.yaml`(唯讀凍結來源)。**不做 per-rule 開關**:
那是 ADR 0010 的 C 案,卡在「凍結來源不存在」(規則代號沒有 git 樹那種
不可自我服務的背書)。而階段定義**已經是**凍結來源,R2 本來就是階段範圍豁免 ——
research 站直接沿用這套,不需要新機制。

### 2. `allows_src_write` 綁**路徑**,不綁階段

research 站宣告 `src_write_scope: research/`。R2 據此:research 站只能寫
`research/` 底下,寫範圍外(`src/`、`macro_audit/`…)**一律擋,不分寫入或提交時點**。

**為什麼綁路徑**:agent 能自己寫 `pipeline.json` 宣告 `current_stage: research`。
如果 research 綁階段(整站可寫),agent 宣告 research 就寫得了生產碼 —— 豁免爆炸。
綁路徑把爆炸半徑縮到零:**不管誰宣告 research,都寫不了生產碼**。
主測試就是這條:`test_declaring_research_still_cannot_write_src`。

### 3. R8:生產程式碼不得 `import research/`

機器可判(AST,不是字串比對 —— 字串分不開 `research` 與 `research_utils`)。掛權威層。

**反方向放行**:`research/` 底下的碼可以 `import` 生產資料層。
方向是刻意的:研究依賴生產資料是正常的;生產依賴研究則危險 ——
research/ 可以被丟棄,生產碼一旦 import 它,研究一被殺生產就壞。

邊界比對(F-051):研究套件是 `research`,`research_utils` / `researched` /
`my_research` 都不是。用 AST 取頂層套件名精確比對。

### 4. 出口只有兩個:殺掉、或移出 research/ 走六站

**沒有第三條出口。** 把檔案移出 `research/` = 它成為生產碼 = R3 要求測試、
R2 要求 implement 站、R8 要求沒有人 import 它 —— 六站的閘門自然全數適用。
「移出」因此是一個**必須走六站的事件**,不是「複製過去就好」。
R8 額外保證:在移出之前,生產碼不能靠 import 偷用研究成果繞過這條。

### 5. 資料完整性(DI)軸**不隨 research 放寬**

research/ 底下豁免 **R3**(探索不必先寫測試),但 DI 是 code-review 的第三軸,
不是閘門規則(R 系列)。研究碼要進生產必得走六站、過 code-review,
DI 那時照樣管。**這裡刻意不加任何「research 豁免 DI」的路徑** ——
探索可以沒有測試,但不能把「沒驗證資料完整性」的東西送進生產。

### 6. 套用今天學到的

- **R8 的比對套 F-051**:`imports_research` 用 AST 取頂層套件,
  `research_utils` 不會被當成 `research/`。有測試釘住
  (`test_a_boundary_neighbour_is_not_a_research_import`)。
- **R8 有自己的紅燈證據**:TDD 先寫 17 條會紅的測試,實作後轉綠;
  淨室驗收再跑一次真實 commit 被 R8 擋(照 leak_scan 的先例:規則要先紅過才算存在)。
- **R8 fail-closed**:AST 解析不了(語法壞掉)當作**可能 import 了** ——
  「看不懂這段碼」不能翻譯成「它沒 import research」。
