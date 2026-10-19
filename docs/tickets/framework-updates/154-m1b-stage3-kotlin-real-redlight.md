# 票 154 —— M1-b 階段 3（Kotlin）：受控環境真實工具鏈紅燈驗收

**狀態**：**範例 repo 實測完成（限定範圍，見下）；待收票裁決。**（範圍見第四節之一「範圍聲明」；結果見第四節之一，上游候選見第四節之二。）
**時鐘**：LifeApp 以 Kotlin 開發之前 —— 依規格 :244（R-DEP 第 3 條），某語言的階段 3 通過前，不得在 App 以該語言開發。（事件型時鐘；Jeff 2026-10-16 確認採用）
**優先度**：高（Jeff 2026-10-16）。
**立案**：2026-10-16（美東）。票號 154 由 Jeff 2026-10-16 指定（立案前確認 `docs/tickets/framework-updates/` 內無 154 開頭的檔案）。
**性質**：甲路線 M1-b 階段 3（真實工具鏈）的 Kotlin 份。
**規格**：`<path>\M1-B-NONPYTHON-ADAPTER-SPEC-v3.md`（sha256 `af735dbd679b59618b451fc65fdf804408da04fe1555f7cd44edc4b03259cf3f`）。⚠ 該檔第 1 行標題仍寫「實作規格草稿 v1」，第 5 行性質欄寫 v3（標題未隨版本更新；R0 2-1）。本票不重述規格；以「規格 :行號／§x／AC-Bxx」引用。
**路徑代稱**：`<sandbox>`＝本票受控範例 repo；`<tools>`＝repo 外的工具資料夾；`<path>`＝其他本機路徑。實際路徑詳見本機紀錄。
**交叉引用**：〔R0〕`.dev/reports/2026-10-16T153620Z-ticket-stage3-r0-recon.md`；票 152 §7 第 203 行「階段 3 票：受控環境真實『紅 → 實作 → 綠』（規格 §5、AC-B40～B45），需 Q-ENV 授權。」；候選票 155（Flutter）。

---

## 一｜範圍（只限 Kotlin：JVM 外掛＋Gradle）

**本票包含**：規格 §5 步驟 1～6 的 Kotlin 份（要可重現），以及 AC-B40、B41、B42、B44、B45 的 Kotlin 份。

規格原文（逐字）：

> :217 每個語言各做一次，全部步驟要可重現並留紀錄：
> :219 1. 在 implement 站寫測試檔（D3：不受 R2／R3）。
> :220 2. 嘗試寫實作 → **被 R3 擋**（沒有紅燈）。
> :221 3. 用包裝器跑該測試（實作不存在）→ 帳內出現一筆合格紅燈（Kotlin 走 E2 的編譯失敗判準）。
> :222 4. 再寫實作 → **R3 放行**。
> :223 5. 用包裝器再跑 → 綠燈。
> :224 6. 反向檢查：
> :225    - 沒有紅燈、也沒有任何豁免，就先寫實作 → 擋。
> :226    - 實作寫好後再跑「紅燈」→ 快照顯示實作存在且不等於 HEAD → 不合格。
> :227    - 執行期間修改實作 → 不寫紀錄。
> :228    - 把上一次的輸出目錄拿來重用 → 包裝器拒絕（目錄已存在）。

> :305 | AC-B40 | 第 5 節步驟 1～5 在受控環境真實完成，各語言各一次，可重現 |
> :306 | AC-B41 | 第 5 節步驟 6 的四個反向檢查全部成立 |
> :307 | AC-B42 | Kotlin：E2 的①～④在真實 Gradle 上都量得到；量不到依 E2 回報 |
> :309 | AC-B44 | 初始化腳本與包裝器執行前後，受控 repo 的建置檔沒有任何變更 |
> :310 | AC-B45 | 在真實工具上製造「沿用快取／不需重跑／跳過／中斷」各一次（能製造的才做），包裝器都**不寫合格紅燈**；製造不出來的情形記錄原因，並據此定案 AC-B33 的辨識方式 |

**本票不包含**：

- **Dart 階段 3**：另議，未開票。
- **Flutter**：見候選票 155。
- **Android 專案結構**（`compileDebugKotlin`、`androidTest` 等）：初始化腳本 `.claude/hooks/redlight_gradle_init.gradle:12-15` 寫明未對應（「Android 變體(compileDebugKotlin 等)沒有對應 —— 待階段 3。」）。
- **Gradle configuration cache 開啟**的情況。
- **Linux／macOS**。
- **CI**（不改 `.github/workflows/`）。
- **下游部署**（規格 R-DEP :243-244，另議）。

---

## 二｜受控環境

- 拋棄式範例 repo，放在**本機、agent-gates 之外**。
- **不得**放在規格資料夾 `<path>`（該處沒有 `.git`，有 G-08 風險），也**不得**放在任何現有 repo 內。
- 確切路徑：`<sandbox>`（Jeff 2026-10-16 同意）。
- 範例 repo 裝含 M1-b 的上游版本（`install.py`）；**票面記錄所裝上游的 commit sha**：`70f732f02eea1b3c891b9ce45426b49b4f8b8d31`（安裝時 agent-gates 工作樹僅帳本一行未提交，帳本不隨安裝帶出（E3 讀碼））。

---

## 三｜Q-ENV 環境工作包（已核准；JDK、Gradle 已就位，相依套件已於實測時下載（見第四節之一）；見第三節之二）

**整包由 Jeff 一次授權**；之後只有**超出工作包範圍**的動作才再問。超出的例子：不同版本、其他下載來源、包外指令、改動範例 repo 以外的位置。

Jeff 2026-10-16 約 13:20（美東）核准下列工作包（見修正紀錄）。

| 項目 | 版本 | 下載來源 | 大小 | 安裝位置 |
|---|---|---|---|---|
| JDK | Eclipse Temurin 21 LTS，Windows x64 **zip**，取下載當下官方最新 GA 修補版。確切版本：`Temurin 21.0.12.1+1`，檔名 `OpenJDK21U-jdk_x64_windows_hotspot_21.0.12.1_1.zip`，sha256 `f9d6e191ab098c0d416e7d588a24420a8621cd2f4720dab2459b8b7b2d2d8b4e`，size `205073461` | adoptium.net 官方，經 `api.adoptium.net` 取得連結與 checksum；實際檔案在 GitHub `adoptium` 官方 release | 約 200 MB | `<tools>\jdk-21\` |
| Gradle（安裝版） | **9.7.0**，`gradle-9.7.0-bin.zip`，sha256 `84fbba45c7f4c64abc77460e1c00f541e9f960e3c7ed2538f1ede19eacd873ae` | `https://services.gradle.org/distributions/`（同目錄的 `.sha256`） | 約 130～150 MB | `<tools>\gradle-9.7.0\` |
| Kotlin Gradle 外掛／kotlin-stdlib／JUnit 相依 | Kotlin Gradle 外掛與 stdlib **2.4.21**；JUnit 5 版本於紅燈站設計時定 | Gradle Plugin Portal、Maven Central，由 Gradle 首次建置時自動取得 | 約 100～300 MB | `GRADLE_USER_HOME=<tools>\gradle-home` |

| 項目 | 內容 |
|---|---|
| 範例 repo 位置 | `<sandbox>\`；本機 `git init`，不設 remote，不 push |

**允許的動作**：

| 動作 | 位置 |
|---|---|
| 下載上表的檔案；核對 sha256 | `<tools>\downloads\` |
| 用 PowerShell `Expand-Archive` 解壓 | `<tools>\` |
| `git init`／`add`／`commit`（只在本機） | 範例 repo |
| 用 agent-gates 的 `install.py` 安裝 | 目標：範例 repo |
| 執行 `redlight_run.py`、`gradle`、`java` | 範例 repo（`gradle --version` 版本確認在 `<tools>`） |
| `gradle.properties` 設 `org.gradle.daemon=false`、`org.gradle.configuration-cache=false` | 範例 repo 自己的 `gradle.properties` |

- **環境變數只在單一指令內設定**：每一次執行 Gradle（包括 `gradle --version`）都必須同時設定 `JAVA_HOME=<JDK 根>` 與 `GRADLE_USER_HOME=<tools>/gradle-home`，並在核准的工作目錄內執行。目的是讓 Gradle 使用隔離目錄，不用真實家目錄的 `.gradle`。
- `org.gradle.daemon=false` **不保證**完全不啟動背景 JVM；Gradle 仍可能為本次建置啟動一個專用 daemon，建置結束後停止。

**不做**：

- msi 或其他安裝程式；
- 改系統或使用者層的環境變數、登錄檔；
- Android SDK、IDE；
- 其他版本；
- push 範例 repo；
- 刪除任何東西（刪除要另問 Jeff）。

agent-gates 本身需要修改時：先回報，不動手。

---

## 三之二｜環境準備實際經過

> **〔更正，2026-10-19〕** 提交 `e1564b0`（本節、第三節之三與修正紀錄「環境準備完成」一條由該提交加入）：該提交標題中的『完成』過度宣告；實際當時只完成環境記錄，見本節。（原文不改。）

1. **E1／E1b**（`.dev/reports/2026-10-16T172711Z-ticket154-e1-env-setup.md`、`.dev/reports/2026-10-16T173748Z-ticket154-e1b-env-setup.md`）：A 段入票、推送 `70f732f`。B 段 AI 用指令在 repo 外建目錄，被 R7 擋下；R7 這次判斷的目標就是指令真正要寫的位置。
2. 裁決助手查了 `gate.py:530-564`、`:1143-1175`、ADR 0008、`CLAUDE.md`、`docs/adr/`：**沒有**「AI 在 repo 外準備環境、建立下游 repo、對外部目標執行安裝器」的正規入口或明確授權。換視窗屬於繞過，所以 E2 撤回、未執行。
3. 因此下載、核對、解壓、建立範例 repo、安裝、補登記冊、補驗證，**全部由 Jeff 人工執行**。AI 只做唯讀核對（`.dev/reports/2026-10-16T185419Z-ticket154-e3-verify.md`、`.dev/reports/2026-10-16T190652Z-ticket154-e4-install-diagnosis.md`）。
4. 安裝程式退出碼 1：`verify()` 第一項被 R10 hard_block。範例 repo 的登記冊是安裝程式產生的空清單；使用者層有 synced 230 筆、user-commands 1 筆未登記（E4，已證實）。`verify()` 的另外兩項檢查沒有執行。
5. Jeff 照抄 agent-gates 的兩份登記冊（範例 repo 與 agent-gates 兩份的 SHA256 相同），以只含兩份 policy 的提交 `41313ac` 通過 R10（紀錄中出現 `[R10/policy-only]`），再補跑 `install.verify()`，退出碼 0（紀錄中 `VERIFY-OK` 1 次）。
6. **安裝程式 `main()` 在 `verify()` 之後的步驟沒有執行**：`docs/decisions-pending.md` 不存在，完成報告沒有產生。`bootstrap.sh` 未跑（範例 repo `core.hooksPath` 未設）。目前在範例 repo 有檔案的是 `.git/hooks/pre-commit`。
   - **〔已過期，2026-10-19 更正〕** 本點「bootstrap 未跑／hooksPath 未設」已過期：10/16 Jeff 親手執行 bootstrap，exit 0，`core.hooksPath=.githooks`。（上游候選 U9；原文不改。）
7. 讀取範圍：Jeff 先接受「僅該次安裝」的驗證讀取；之後在「R10 會讀擴充檔內容計算指紋、核對格式，但不輸出名稱與內容」的正確說法下，接受「限票 154 範例 repo」的 R10 讀取。
8. 範例 repo 的提交身分是 local `gate@local`，不 push。

## 三之三｜本票期間的發現（候選，不在本票範圍）

1. **R7 運算元判讀**：`cp <來源> <目的>` 的擋下訊息把**來源**（只被讀取）列為寫入目標（E1 報告）。是否為判讀錯誤，待另查。
2. **安裝驗證與未登記擴充**：安裝程式產生空的登記冊（`install.py:440-485`）。本次觀測到的未登記擴充（synced 230 筆、user-commands 1 筆）使 `verify()`（`install.py:552-559`）被 R10 擋下；擋下時兩個安裝提交已經建立（`install.py:649`、`:655` 早於 `:658`；E4 報告）。是否所有環境都會如此：待確認。是否屬預期設計：UNKNOWN。
3. **安裝輸出編碼**：失敗訊息走 stderr，在 cmd 轉向下是 cp950；成功路徑 `_out()`（`install.py:58-60`）是 UTF-8（E4 讀碼推論）。
4. **MCP `latest_report` 排序**：`.dev/reports/` 有兩份檔名不含 `-` 的舊報告（`20261009T…`、`20261013T…`），以字典序會排在最後，工具因此回傳舊報告（裁決助手 2026-10-16 實際碰到）。

---

## 四｜完成條件

- 規格 §5 步驟 1～6 的 Kotlin 份在受控環境真實完成。
- AC-B42 的 E2 ①～④ 在真實 Gradle 上都量得到。

**失敗時先分類**，每類都要附證據：

| 類別 | 例子 | 處置 |
|---|---|---|
| 環境問題 | 工具版本、安裝 | 回報；超出工作包的修正另行授權 |
| 包裝器或初始化腳本缺陷 | 腳本 API 不相容、協定欄位對不上 | 在上游 agent-gates 修（見第五節） |
| 規格不可行 | 真實 Gradle 確實量不到 E2 的某一條 | 依規格 :202 回報 Jeff |

- 只有證據支持「規格不可行」時，才依規格 :202 回報。規格原文（逐字）：

  > :202 - **這是 M1-b 的核心可行性問題**：階段 3 必須在真實 Gradle 上證明①～④都量得到。量不到時，結論是「Kotlin 新檔目前無法誠實滿足 R3」，回報 Jeff；**不得用放寬 R3 的方式收場**。

- **初始化腳本第一次跑壞，不得據此判定語言不可行。**
- 任何情況都不得用放寬 R3 的方式收場。
- **允許的完成宣告**只限 R0 方案表 B 欄「做完能說」的範圍：Kotlin、JVM 外掛、本機 Windows、票面記錄的 Gradle／JDK 版本。不得延伸到 Dart、Flutter、Android、其他版本或其他作業系統。

---

## 四之一｜實測結果（2026-10-16～19）

**範圍聲明**：本次完成宣告**只限**：Windows、Kotlin JVM、Temurin JDK 21.0.12.1+1、Gradle 9.7.0（經 Wrapper，指向本機 zip）、Kotlin 外掛 2.4.21、JUnit 5.13.4。**不包含** Android、Flutter、純 Dart、其他作業系統或其他版本；各自後續歸屬依另案裁定。（票 155 只是 Flutter 候選票；純 Dart 的階段 3 仍為「另議、未開票」。）

- 實測地點：範例 repo `<sandbox>`；各站報告在該 repo 的 `.dev/reports/`。以下證據欄只寫報告檔名。
- 整票結果表引自 `2026-10-19T132037Z-ticket154-fin-closing.md`（以下稱 FIN）第 6 節；AC-B44 引自 FIN 第 2 節。日期為 UTC。
- 標「裁決助手核對」者：判定由裁決助手讀結果檔核對，FIN 視窗只引用其記錄，沒有自己讀 `.dev/runs/`（FIN 第 6 節〔註〕）。
- 範例 repo 收尾：HEAD `b0bcc21`；帳本 `.dev/test-runs.jsonl` 7 行，保留不提交；Wrapper 4 檔未進版控（見 U4）；站別已由 Jeff 切回 idle（`current_stage: "idle"`、`ticket_id: null`）。（裁決助手讀檔核對，記於本站指令。）

### §5 步驟 1～5（主流程，AC-B40／B42）

| 步驟 | 日期（UTC） | 判定 | 證據 |
|---|---|---|---|
| 1 寫測試（D3） | 2026-10-16／17 | 放行 | `2026-10-16T234111Z-ticket154-s1-first-run.md`（GreeterTest）、`2026-10-17T005351Z-ticket154-s2b-seed-test-first.md`（SeedTest） |
| 2 試寫實作 → R3 擋 | 2026-10-16／17 | 擋（`[R3/紅燈]`） | 同上兩份 |
| 3 包裝器紅燈 | 2026-10-17 | Seed：執行期紅燈（帳本第 1 行）；Greeter：編譯紅燈（帳本第 3 行） | `2026-10-17T011129Z-ticket154-s3-seed-impl.md`（Seed）、`2026-10-17T015600Z-ticket154-s4-greeter-impl.md`（Greeter）；執行結果由裁決助手核對，記於該站指令來源段 |
| 4 寫實作 → R3 放行 | 2026-10-17 | 放行（無 trace，放行依據為〔讀碼推論〕） | `2026-10-17T011129Z-ticket154-s3-seed-impl.md`、`2026-10-17T015600Z-ticket154-s4-greeter-impl.md` |
| 5 包裝器綠燈 | 2026-10-17 | Seed、Greeter 各綠（帳本第 2、4 行） | 範例 repo 無對應報告；記於 S4、RC1 指令來源段 |

E2 ①～④（AC-B42）：Greeter 帳本第 3 行為 `impl_exists:false`、`failed_tests:["<compile error>"]`；`compileKotlin up_to_date`、`compileTestKotlin failed/executed`、`compile_errors` 含測試檔路徑、單一 `--test`（依 S4 指令所記的裁決助手核對）。**限制**：只在產品來源集非空（已有 `Seed.kt`）時觀測到；空專案時被 `no_source` 拒絕（見 U2）。

### §5 步驟 6 反向①～④（AC-B41）

| 項目 | 日期（UTC） | 判定 | 證據 |
|---|---|---|---|
| 反向①：無紅燈、無豁免先寫實作 | 2026-10-17 | 擋下（`[R3]` 找不到對應測試），符合預測 | `2026-10-17T021046Z-ticket154-rc1-orphan.md` |
| 反向②：實作已存在才跑紅燈 | 2026-10-19 | 實驗組（紅燈對 H1）擋下、對照組（紅燈對 H0）放行 | `2026-10-19T124047Z-ticket154-rc2-impl-exists-red.md`（含 D 段） |
| 反向③：執行中改實作 | 2026-10-19 | 通過（`reasons`「執行前後實作狀態不同」、`records` 空；裁決助手核對） | `2026-10-19T122129Z-ticket154-rc3-modify-during-run.md`（還原證據）；判定記於 RC2 指令來源段 |
| 反向④：重用輸出目錄 | 2026-10-17 | 通過（退出碼 2、`aborted:true`、帳本不變；裁決助手核對） | 範例 repo 無對應報告；記於 B45S 指令來源段 |

- **反向② 結論**：H1 紅燈時擋下、H0 紅燈時放行，提供支持『版本綁定影響判定』的實測證據；不能單憑此證明唯一原因。
- 註：實驗組的擋下訊息與事實不符（印出「沒有一筆屬於當前票」，而本票其實有紅燈、只是不合格）；見 U7。

### AC-B45 四種

| 情形 | 日期（UTC） | 判定 | 證據 |
|---|---|---|---|
| 不需重跑 | 2026-10-17 | 通過（三任務 `up_to_date`、不寫紀錄；裁決助手核對） | 範例 repo 無對應報告；記於 B45S 指令來源段 |
| 沿用快取 | 2026-10-17 | 通過（`from_cache`、不寫紀錄；裁決助手核對）。前置綠燈為帳本第 5 行（真實執行） | 範例 repo 無對應報告；記於 B45S 指令來源段 |
| 跳過 | 2026-10-17 | 通過（`skipped`、`records` 空；裁決助手核對）；測試已還原 | `2026-10-17T024014Z-ticket154-b45-skip.md`（還原證據）；判定記於 B45I 指令來源段 |
| 中斷 | 2026-10-19 | 通過（沒有 `kotlin-result.json`、`records` 空；裁決助手核對） | `2026-10-19T120646Z-ticket154-b45-interrupt.md`（還原證據）；判定記於 RC3 指令來源段 |

- 「中斷」的兩點限定：
  1. 終止的是唯一確認身分的建置程序。
  2. 「測試工作程序存在」不能直接證明已進入 sleep。
- 「中斷」用的是硬殺（`buildFinished` 不執行）；Gradle 正常取消的情形未製造，見第四節之二 R-6。

### AC-B44（建置檔前後不變）

| 檔案 | `git hash-object` | S1 基準 | 判定 |
|---|---|---|---|
| `gradle.properties` | `6b18fd1b2e16b8e7527182aaf12c156e0b6afbfc` | `6b18fd1b2e16b8e7527182aaf12c156e0b6afbfc` | 相同 |
| `settings.gradle.kts` | `11a59628007edcd88b47cfe1382ccfe0a3635b4c` | `11a59628007edcd88b47cfe1382ccfe0a3635b4c` | 相同 |
| `app/build.gradle.kts` | `b6001e3081f77acfd41b8da37327ad5924edf1f6` | `b6001e3081f77acfd41b8da37327ad5924edf1f6` | 相同 |
| `.gitignore` | `d92a3501a263b91bdb73d8e08ba16c653e01dd99` | `d92a3501a263b91bdb73d8e08ba16c653e01dd99` | 相同 |

- 證據：`2026-10-19T132037Z-ticket154-fin-closing.md` 第 2 節（基準見 `2026-10-16T234111Z-ticket154-s1-first-run.md`）；`git diff --exit-code` 對這 4 檔退出碼 0。
- 限制（照 FIN）：這是「收尾時」與基準相同，不是每一次包裝器執行前後都量過；中間是否有變動又改回，FIN 無法排除。這 4 檔不含 Wrapper 檔（未進版控，沒有基準可比）。
- 初始化腳本 `redlight_gradle_init.gradle` 與包裝器 `redlight_run.py` 收尾時與範例 repo HEAD 相同（FIN 第 3 節）。

---

## 四之二｜上游候選

內容依 FIN 第 7 節；是否開上游票待裁（見第四節之四）。

| # | 內容 | 性質 | 來源報告 |
|---|---|---|---|
| U1 | `redlight_run.py` :442-443、:461：無 `gradlew.bat` 時以裸 `"gradle"` 呼叫，Windows 上 `FileNotFoundError`（R-1，Jeff 實測成立） | 包裝器缺陷 | `2026-10-16T230449Z-ticket154-r1-design.md`（預測）；實測記於 S2 指令來源段 |
| U2 | 產品來源集為空時 `main_compile='no_source'`，編譯失敗路徑不寫紅燈（R-2，Jeff 實測成立；範圍限空專案＋編譯失敗路徑） | 包裝器／規格待裁 | `2026-10-16T230449Z-ticket154-r1-design.md`（預測）；實測記於 S2 指令來源段 |
| U3 | R7 許可前綴不認 `VAR=value` 開頭的指令，`python .claude/` 包裝器在帶環境變數時只因「看不出寫入」而放行；ADR 0008 無明示管道、下游無登記位置 | 規則／程序 | `2026-10-16T234111Z-ticket154-s1-first-run.md` |
| U4 | `leak_scan` 把 `gradle-wrapper.jar` 判為「讀不到內容」擋下（`scanner.py` `SKIP_SUFFIX` 收 `.zip` 未收 `.jar`，裁決助手讀碼）；放行方式待裁 | 掃描器 | `2026-10-17T003922Z-ticket154-s2-wrapper-seed.md` |
| U5 | `exemption_hint` 對 Kotlin 實作檔建議「`NON_SOURCE_EXT` 加一筆 `'.kt'`」，照做會讓 R2／R3 對全部 `.kt` 失效 | 訊息 | `2026-10-17T021046Z-ticket154-rc1-orphan.md` |
| U6 | 硬中斷建置程序後，測試工作程序與 Kotlin daemon 成為孤兒、不自行退出 | 包裝器／環境 | 範例 repo 無對應報告；記於 RC3 指令來源段 |
| U7 | `redlight_missing` 訊息優先序：本票有紅燈但不合格、同時有舊票紅燈時，印出「沒有一筆屬於當前票」，與事實不符 | 訊息 | `2026-10-19T124047Z-ticket154-rc2-impl-exists-red.md` |
| U8 | Gradle 輸出「已棄用功能，與 Gradle 10 不相容」，來源 UNKNOWN（初始化腳本的 `buildFinished`／`afterTask`／執行期 `Task.project` 為候選，R1 R-4／R-5，未證實） | 初始化腳本（待查） | 記於 S3 指令來源段；`2026-10-16T230449Z-ticket154-r1-design.md` G 節 |
| U9 | 本票 §三之二第 6 點「`core.hooksPath` 未設」已過期（已於該點加更正註記） | 文件 | `2026-10-16T230449Z-ticket154-r1-design.md` A 節 |

- 未驗證風險 R-6：Gradle 正常取消時，是否可能輸出 `complete:true` 並被包裝器誤記；本票未實測。

---

## 四之三｜小觀察：換行現象

`git restore` 後 `pipeline.json` 與 `GreeterTest.kt` 在 `git status` 顯示 M；原始位元組不同（工作區為 CRLF），LF 正規化後與 HEAD 相同，`pipeline.json` 的 JSON 內容為 idle。這支持『沒有語意變更』；自動轉換的原因屬推論，不概括為所有情況都無害。

---

## 四之四｜後續

1. 收票裁決（Jeff）。
2. U1～U9 是否開上游票（Jeff）。
3. 「AI 正式執行管道」列為減少摩擦的第一優先（Jeff 10/17 決定順序）。

---

## 五｜已知風險

照抄 R0 3-3：

- 〔讀碼推論〕初始化腳本從未經真實 Gradle 執行（`redlight_gradle_init.gradle:3`：「**本檔未經真實 Gradle 執行;協定為暫定,改動需規格＋測試。**」）。
- 〔讀碼推論〕腳本自述用到的 API 可能已 deprecated（`redlight_gradle_init.gradle:29-30`：「本檔用到的 taskGraph.afterTask / buildFinished / addTestListener 在較新的 Gradle 版本可能已標為 deprecated 或與 configuration cache 不相容 —— 待階段 3 實測。」）。
- 〔讀碼推論〕Kotlin 的 Gradle 專案路徑由目錄推出（`app` → `:app`，`redlight_run.py:174-175`）；子專案名與目錄不同時會對不上（R0 3-3 推論 3）。

**若必須改初始化腳本或包裝器**：

- 照紅燈先行，在上游 agent-gates 修，不在範例 repo 改。
- 修改屬於本票範圍，但**先回報、再動手**。

---

## 六｜延後項目對照（自 R0 2-3 搬入）

分類只依規格原文。必做項只保留與 Kotlin 有關的；只屬 Dart 的必做項標「Dart 份，不在本票」；待裁項原樣列為待裁。

| 項目 | 票 152 原文要點（行號） | 與階段 3 的關聯 | 分類 | 規格依據 |
|---|---|---|---|---|
| §7 階段 3 票 | :203「受控環境真實『紅 → 實作 → 綠』（規格 §5、AC-B40～B45），需 Q-ENV 授權」 | 本體 | **必做**（Kotlin 份） | :213-228、:238、:305-310 |
| R-e（快取／跳過／未完成） | :189 引 P3 殘餘風險 | 規格明寫待階段 3 | **必做**（AC-B45 Kotlin 份） | :168、:310、:347 |
| AC-B26／Dart 載入失敗形狀 | （批二以合成樣本 `dart_load_error.jsonl` 處理） | 規格明寫待階段 3 | **Dart 份，不在本票**（AC-B43） | :291、:308 |
| E2 Kotlin ①～④ | — | 規格明寫 | **必做**（AC-B42） | :197、:202、:307 |
| 初始化腳本不改建置檔 | — | 規格明寫 | **必做**（AC-B44） | :159、:309、:353 |
| K1 | 規格 §11 | 階段 3 通過即解除（針對該語言） | 階段 3 的結果，非待處理項 | :54、:374 |
| K2 | 規格 §11 | 限「階段 1、2 期間」 | 規格未說階段 3 後如何 → **待裁** | :375、:249 |
| K3、K7、K8 | 規格 §11 | 規格 §10「不在 M1-b 範圍」 | **可保留** | :367、:370、:376、:380-381 |
| K4（R8 未檢查） | 規格 §11 | P2 已裁 | **可保留** | :321、:377 |
| K5／R-a～R-d、R-f、R-g | P3 | P3 已裁「接受」 | **可保留** | :322、:351、:378 |
| K6、K9、K10、K11 | 規格 §11 | Jeff 已裁記為已知限制 | **可保留** | :379、:382-384 |
| K12 | :190「前提『工具只跑 argv 指定的檔』……待階段 3 驗證。完整修法……放在階段 3」 | 票面自述延到階段 3 | **待裁**（v3 無 K12；v4 是否存在 UNKNOWN）。相關規格：E3 :206「相對於套件根時，補上套件根前綴」 | :206 |
| G3 | :191 junction／symlink 落點；「延後處理」 | 票面未說延到階段 3 | **待裁**（規格未定義） | — |
| H4 | :192「依階段 3 真實輸出再定」 | 票面自述 | **待裁**（規格未定義；AC-B43 只要求載入失敗形狀，不涉及路徑大小寫） | — |
| H6 | :193「修掉 H1 之後已無錯配路徑」 | 票面未連到階段 3 | 不屬延後項（規格未定義） | — |
| J2 | :194（資訊） | 無 | 不屬延後項（規格未定義） | — |
| J4 | :195 刻意接受的相容性代價 | 無 | 不屬延後項（規格未定義） | — |
| S5h3-K1 | :196 威脅模型外 | 無 | 不屬延後項（規格未定義） | — |
| S5h3-K2 | :197 Windows 別名 | 無明文 | 不屬延後項（規格未定義） | — |
| S5h3-K3 | :198 NUL → ValueError | 無 | 不屬延後項（規格未定義） | — |
| S5h3-K4 | :199「真實 Windows 上的行為未實測」 | 需真實環境，但票面未寫階段 3 | **待裁**（規格未定義） | — |
| D3 測試目錄不打包 | — | 規格標「待階段 3 實測確認」但無對應 AC | **待裁** | :104 |
| §7 下游部署 | :204「依 R-DEP，階段 3 通過後另議」 | 部署不是階段 3 | 不屬階段 3（規格 R-DEP 只寫前提） | :243-244 |

（「票 152 原文要點」欄的行號指票 152 檔案；「規格依據」欄的行號指規格 v3。K12、H4 兩列與 Dart 相關，在本票仍只列為待裁，不處理。）

---

## 七｜未決事項

- **真實輸出要不要收回 agent-gates 當 fixture**：等 Kotlin 份通過後再裁。R0 問題 4，VS（R0 所在的 VS Code 視窗）建議 (a)；**Jeff 尚未裁**。
- **規格 v4 是否存在**：UNKNOWN（票 152 §6 K12 提到「規格 v4 定案」）。
- 時鐘、優先度已由 Jeff 2026-10-16 確認（見修正紀錄）。

---

## 修正紀錄

- 立案（2026-10-16，裁決助手記錄，非逐字原話）：Jeff 2026-10-16 約 12:50（美東）裁決：
  1. 階段 3 先做 Kotlin（JVM＋Gradle）。理由：App 目前候選是「Kotlin 為主、Flutter 挑戰」；規格 :202 寫明 Kotlin 是 M1-b 的核心可行性問題；結果也能回饋 App 選型。
  2. 受控範例 repo 放在本機、agent-gates 之外；不放規格資料夾 `<path>`（該處沒有 `.git`，有 G-08 風險）；不動 CI。
  3. Flutter 另開候選票，先不排程（候選票 155）。
  4. 票號用 154，放在 `docs/tickets/framework-updates/`。
- 定稿（2026-10-16，裁決助手記錄，非逐字原話）：Jeff 2026-10-16 約 13:05（美東）確認：時鐘「LifeApp 以 Kotlin 開發之前」採用；優先度高；票號 155 確認；授權提交並 push（範圍只有票 154、155 兩個票檔，合成一個提交）。裁決助手要求：repo 公開，票面上的本機路徑一律遮成 `<path>`（比照票 152）。
- Q-ENV 核准（2026-10-16，裁決助手記錄，非逐字原話）：Jeff 2026-10-16 約 13:20（美東）核准第三節的環境工作包（一次授權），並同意範例 repo 位置 `<sandbox>`。`9398cc3` 的 CI 綠燈由 Jeff 目視確認（約 13:15，美東）。選版依據：kotlinlang.org 的 Kotlin Gradle 外掛相容表中，KGP 2.4.20–2.4.21 完整支援的 Gradle 範圍是 7.6.3–9.7.0；docs.gradle.org 的 compatibility 頁寫明 Gradle 9.x 需要 JVM 17–27。
- 環境準備完成（2026-10-16，裁決助手記錄，非逐字原話）：Jeff 2026-10-16（美東）約 14:25 選擇人工準備 JDK／Gradle；約 15:00 接受「僅該次安裝」的驗證讀取；約 15:12 選擇照抄 agent-gates 的兩份登記冊；約 15:15 在正確說法下接受「限票 154 範例 repo」的 R10 讀取；約 15:20 授權本次提交並 push。經過見第三節之二。
- 實測期間決定紀錄（2026-10-16～19，裁決助手記錄，非逐字原話）：
  1. 包裝器由 Jeff 親手執行（10/16 選乙）。
  2. Q7 原記錄「不製造 from_cache」有誤，已依 AC-B45 更正並實際製造（結果見第四節之一 AC-B45「沿用快取」）。
  3. Wrapper 因 U4 未提交。
  4. 反向② 加了對照組（紅燈對 H0）。
- 實測結果寫回（2026-10-19，裁決助手記錄，非逐字原話）：Jeff 2026-10-19 約 09:51（美東）決定一次寫回本票：實測結果、U1～U9、未驗證的 R-6、兩處更正、換行現象；不重跑工具鏈；push 前停下等 Jeff 確認。
- 路徑遮罩（2026-10-19，裁決助手記錄，非逐字原話）：依定稿「本機路徑一律遮成 <path>」，把票面本機路徑改為代稱 <sandbox>／<tools>（其中 1 處由 b098328 加入，係 REC 指令允許所致）；§三標題「相依套件尚未下載」已過期，一併更正。已 push 的舊版本留在歷史中，不改寫歷史。
