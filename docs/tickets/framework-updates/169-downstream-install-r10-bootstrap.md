# 票 169 —— 新下游安裝必死於 R10 空名冊 —— installer 先 commit 後驗證，留下半套

**狀態**：~~**立案（2026-11-04）。只立案與記錄調查結果；實作未開始。**~~ ~~**AC 與設計已定案（2026-11-04）；紅燈測試已寫（輪一）；實作未開始。**~~ ~~**實作完成、綠燈與全套已跑（輪三，2026-11-04）；未 commit。**~~ ~~**實作完成（含 commit 前重驗與自動復原）、綠燈與全套已跑（輪四，2026-11-04）；未 commit。**~~ **結案（2026-11-09）：AC-1～AC-3 全部通過；後續可用性問題移至票 170。**
**優先度**：LifeApp 接線的前提（裁決者 2026-11-04）。
**立案**：2026-11-04。票號 169 於立案當下重查 `docs/tickets/framework-updates/` 取得（當時最大號 168；寫檔前 `Test-Path` 確認無此檔、Glob 確認無 169 開頭的檔案）。
**性質**：缺陷票（第一層）＋設計待答題（第二層）。
**交叉引用**：LifeApp 規格目錄下的報告 `20261104T150548Z-lifeapp-install-rehearsal.md`（非本 repo）；本 repo 立案時 HEAD `45ac49d046ea3c3c99000aeb583bebf323faeb2e`。

---

## 一｜背景

### 1.1 事實（來源：上述 LifeApp 彩排報告；本票立案時未在本 repo 重跑安裝）

1. installer 先複製並以 `--no-verify` 建 2 個 commit（共 142 檔），之後才跑安裝末段 verify。
2. 名冊（`.agents/extension-inventory.json`）預設空白。
3. 安裝末段 verify 以空名冊比對本機使用者層 `~/.claude`：R10 判 synced 額外 231，另 user-commands 未登記 1（`finmind.md`）。
4. 安裝停在 verify，留下半套：探針、decisions-pending、bootstrap 的 hooksPath、verify_gates 皆未執行。
5. 主線（裁決者 2026-11-04）：LifeApp 接線暫停 → 本 repo 開票修新下游安裝／R10 bootstrap → 拋棄式 repo 驗證完整安裝 → 回 LifeApp 補 §25 → 正式接線。

### 1.2 本 repo 唯讀調查（2026-11-04，HEAD 同上；只讀原始碼，未執行任何程式）

- **installer 順序**（`.claude/portable/install.py` `main`，`:882`）：`precheck`（`:884`）→ 複製／鏡像／狀態／hook（`:895-900`）→ `write_extension_policy`（`:903`）→ `git add -A` ＋ `commit --no-verify`（`:905-909`，go-live）→ legacy 清單 ＋ 第二個 `commit --no-verify`（`:913-916`）→ **`verify`（`:918`）** → `write_decisions_pending`（`:919`）→ 輸出摘要與探針結果（`:923-962`）。`verify`（`:696`）跑 `gate.py --pre-commit`，rc≠0 即 `SystemExit`（`:710-717`），所以後面全部不執行。
- **空名冊是刻意設計**：`write_extension_policy`（`:453-460`）docstring：「這是安裝預設，不是核准過的觀測快照：不登記任何使用者擴充（dev-mods / skills / commands / synced / .mcp.json）」。
- **R10 對 synced 的判定不分 profile**：`gate.py` `check_extension_integrity`（`:5177-5247`）沒有任何 upstream／downstream 分流；`synced` 不 `verified` ⇒ `[R10/fail-closed]` 硬擋（`:5234-5243`），不受影子豁免。`runtime_identity.py` 的 `PROFILES`（`:34`）只管套件集合，與 R10 無關。
- **能依本機現況產生名冊候選的既有工具**：`.claude/portable/inventory_evidence.py`（票 165）有 S2「候選名冊」步驟，但 manifest 標 `skip`（`.agents/portable-manifest.txt:98`，不出貨到下游），且 repo 識別值寫死本 repo（`:55-57`）。對新下游不可用。
- **既有下游名冊**（唯讀，只數數字）：本機只找到 1 個非本 repo 的名冊，資料夾 `t154-kotlin-sandbox`：含 `"path"` 鍵的行 230 行，其中以 `skills/` 或 `plugins/` 開頭 230 行。該資料夾是否算正式下游、名冊怎麼來的：**未查**。

---

## 二｜兩層範圍

### 第一層（確定要修）

- **L1-1**：新下游第一次安裝時，R10 的初始名冊如何合法建立；不得「先空白、再讓驗證自己撞死」。
- **L1-2**：installer 不得先留下 `--no-verify` commit 才發現前提不成立。要嘛 preflight 先確認／建立合法 R10 基準，要嘛讓安裝保持可恢復、可完成的明確狀態。二擇一或其他方案，待設計輪裁。
  - 裁決：(a)（2026-11-04）。
- **L1-3**：修完後，以新的拋棄式 repo 從乾淨狀態重跑完整官方安裝，證明一路完成，不靠人工補登記才能脫困。

### 第二層（待證據再裁）

- **L2-1**：分清兩類外部內容：
  - 使用者自己控制的內容（例：`~/.claude/commands` 下的自訂指令）：仍適合精確指紋鎖定。
  - Claude app 自動同步、使用者不控制版本的官方 synced 技能：是否還值得逐檔 SHA 鎖定，重新裁。
- **L2-2**：contract 只是候選方案，未裁。要先回答三件事：R10 原本防什麼、現有 contract 能不能涵蓋 app-managed 內容、會不會漏掉真正危險的變更（見〈三〉）。

---

## 三｜第二層的調查底稿（唯讀；結論未裁）

- **R10 想防什麼**：票 146〈目標〉（`:40-43`）：「任何 Claude Code 擴充機制都不能靜默削弱 agent-gates。」「靜默」是重點：削弱本身未必擋得住，「但它不准不出聲」。同票 `:471`：synced 是「已知存在的未受管靜態入口」，裁決是擋，並明記「這台機器在 synced 納管前無法 commit 是已知成本」。
- **synced 與 user-commands 的現行判定**（`.claude/hooks/redlight.py`）：
  - user-commands：allowlist 的 `(path, sha256)` 精確比對，不在集合內或 sha 為 None ⇒ VIOLATION／unregistered（`:2106-2111`）。
  - synced：名冊的 `{path: sha256}` 對磁碟，額外（`:2057`）、缺少（`:2058`）、內容不符（`:2059-2060`）；contract 項目改呼叫 `synced_contract_check`，失敗也計入內容不符（`:2071-2073`）；理由字串在 `:2076`。gate 端一律硬擋（見 1.2）。
- **contract 現有語義**：只有 3 個名稱，各自寫死唯一合法路徑（`:1110-1112`；名稱與路徑不合 ⇒ `contract.path`，`:1474-1475`）。pins：`synced-marketplaces-v1` 恰為 `{"id_sha256"}`，兩個 last-round 恰為 `{}`（`:1410-1415`）。鎖住的內容：
  - `.marketplaces.json`：鍵集合、`parserVersion == 1002`、單列 rows 結構，以及 id 對 pins 的雜湊（`:1605-1671`）。
  - 兩個 `.last-complete-round`：只驗格式（小寫 UUIDv4 ＋ 空格；skills 版另驗尾段字元集），不鎖值（`:1675-1725`）。
- **若官方 synced 技能檔改用 contract**（**推論，未執行**）：現行程式沒有能掛在技能檔路徑上的 contract 名稱，名冊直接判 `inventory_schema`。若照 last-round 的方式新增「只驗格式」的 contract：
  - 仍會擋：檔案增減（額外／缺少的算法不變）、讀檔層的結構與連結檢查。
  - 會漏：技能檔內文的任何改寫（例：加入要求 agent 繞過閘門的指示），因為格式不變就放行。這正是 R10 要防的「靜默削弱」。

### 待答問題（第二層不寫 AC）

1. app-managed 內容裡，哪些變更算「削弱閘門」？能不能只用結構判定，不比內文？
2. 官方同步的版本有沒有獨立的 authority（簽章、版本清單）可以取代逐檔 SHA？沒有的話，contract 能鎖的上限是什麼？
3. 每次重新登記的成本（見〈四〉）與漏掉內文變更的風險，誰來承擔、怎麼量？

---

## 四｜已知成本證據

- 上游名冊一週內第 5 次因官方同步重新登記（最近一次 commit `6b49a53`）。

---

## 五｜AC（定案，2026-11-04）

（舊版 AC 草案由本節取代；裁決者 2026-11-04 定案。）

- **AC-1**：新下游安裝時，必須在第一個 repo commit 之前產生 extension inventory 並完成核准；核准綁定具體的內容版本；未核准的內容不得進第一個 commit。
- **AC-2**：採 (a)。~~前置核准未完成，或執行時的內容與核准版本不一致 ⇒ installer 在第一個 commit 之前停止。~~
  **語義訂正（Jeff 2026-11-04）**：「不一致時，在第一個 commit 前停止；停止後，下游 repo 必須精確恢復到 installer 開始前的狀態，不得留下安裝副作用。安裝過程中允許暫時寫入，但失敗必須具備 transaction-like rollback。」
  「原樣」定義：以 installer 開始前的下游 repo 狀態為準，repo 內的 tracked／untracked 檔、git config、index、commit 都不得留下安裝副作用；repo 外（上游 `.dev/install-candidates/`）的候選檔不算污染。
- **AC-3**：以新的拋棄式乾淨 repo 驗證完整官方安裝能一路完成，包括探針、decisions-pending、bootstrap、verify_gates；除了 AC-1 定義的核准點，不需要人工修改 inventory 才能脫困。`g1_verify` 明確不列入（涉及使用者層）。

---

## 五之一｜設計（定案，2026-11-04）

- **D1 候選檔位置**：`<agent-gates>/.dev/install-candidates/<target-id>/<candidate-hash>.json`；不覆寫既有檔，舊候選保留作證據。
  若 `<candidate-hash>.json` 已存在：不得拿它當核准判定的來源，但必須驗證它的 canonical bytes 的 SHA-256 恰好等於檔名，也等於依現況重算的 hash。相同 ⇒ 保留、不覆寫；不同 ⇒ 視為候選證據毀損（candidate evidence corruption）：停止、下游零寫入、不得覆寫原檔，並明確回報。
- **D2 候選內容**（canonical JSON 一起 hash）：schema 與 version、agent-gates 完整 HEAD SHA、target 識別（canonical 路徑＋target 當下 HEAD SHA）、完整 candidate inventory 內容，以及讓 R10 放行所需的其他登記內容（見下方對位 (3)）。candidate-hash＝SHA-256(canonical JSON bytes)。
- **D3 `--approve-inventory <hash>`**：執行時一律依當下現況重新產生候選並重算 hash，不得讀既有候選檔代替；完全一致才繼續寫入下游。不一致 ⇒ 寫出新候選、印新 hash、下游零寫入並停止。
- **D4 AI 權限**：`--approve-inventory` 屬裁決輸入，值必須逐字來自 Jeff 在對話中的明示核准；Claude／VS／其他 agent 不得從候選檔、console 輸出、報告或先前的 hash 自行推導、複製或代填。產生候選 ≠ 核准候選。installer 不得提供任何「自動核准最新候選」的選項。
- **與票 165 的關係**：165 是上游自身的名冊更新流程（暫停中）；169 是新下游首次安裝。兩者不合併。

### 對位結論（輪一唯讀；行號以 HEAD `45ac49d` 計）

1. **preflight 插入點**：`install.py` `main` 的 `precheck(target)`（`:884`）之後、`os.makedirs(target, exist_ok=True)`（`:885`，第一個寫入目標的呼叫，見 `precheck` docstring `:589`）之前。`refuse_if_dirty`（`:886`）唯讀，但排在 `:885` 之後；之後的 `git init`（`:887-890`）、`copy_into`（`:895`）都是寫入。
   ⚠ 未裁：D2 要用 target 當下的 HEAD SHA，但沒有任何 commit 的 repo（unborn HEAD）沒有這個值，`:887` 的 `git init` 分支也一樣。
2. **重用的現況算法**：`redlight.extension_report(repo_root, claude_root=None, walk=None, lstat=None, read_bytes=None, policy_source="head")`（`redlight.py:2157`）。不論 allowlist 狀態都會計算 surfaces（`:2198-2210`）。surfaces 八鍵（`:1079-1080`）：檔案型三鍵 `dev_mod_files`／`user_skill_plugins`／`user_commands`＝`[(相對路徑, sha256 或 None)]`；`synced_files`＝`[(匿名邏輯路徑, sha256 或 None)]`；另有 `project_hook_commands`、`mcp_json_servers`、`r4_violations`、`errors`。
   ⚠ preflight 時目標還沒有 redlight（`_target_redlight`，`:402-409`，讀的是複製後的那一份），只能載入上游 `SRC_ROOT` 的同一份檔案。
3. **R10 放行所需的登記**（依 `_extension_first_reason` `:2106-2132` 與 `synced_verification` `:2053-2085`）：
   - inventory `entries`（synced 兩根）：由 `synced_files` 自動產生；v1 名冊每筆用 `sha256`，含三個 metadata 檔（`_extension_inventory_v1_ok` `:1370`）。**contract 項目不是必要的**，它的 pins 也不需要人工填。
   - allowlist `dev_mod_files`／`user_skill_plugins`／`user_commands`：由 surfaces 的 `(path, sha256)` 自動產生。
   - allowlist `project_settings_hook_commands`：由將被複製的 `.claude/settings.json` 自動產生（manifest `:89` 標 `copy`；現行做法見 `install.py:481`）。preflight 時要讀來源那一份。
   - allowlist `mcp_json_servers`：`.mcp.json` 不在 manifest，由目標現況自動產生。
   - `r4_violations`、`errors`：不是登記項，必須為空。任一 surface 的 sha 為 None（symlink／讀不到）⇒ 無法登記，preflight 應停止。
   - 結論：沒有「不能自動產生、R10 卻必驗」的類別。

### 紅燈測試釘住的介面（輪一；實作站照此實作）

- `install.main(target, approve_inventory=None)`；CLI 為 `install.py <target> [--approve-inventory <64 碼 hex>]`。
- `install.inventory_candidate(target, claude_root=..., upstream_head=...)` ⇒ `(canonical_bytes, hash)`。
- 候選文件鍵：`schema`、`version`、`agent_gates_head`、`target`（含 `path`、`head`）、`inventory`、`allowlist`。
- `install.CANDIDATES_DIR`（模組屬性，預設為上游 `.dev/install-candidates`，呼叫時才讀；測試會換成 tmp）。
- `install.EXIT_INVENTORY_PENDING`（非 0 的 int）：未核准停止時的結束碼。
- 候選證據毀損時，輸出必須含 `候選證據毀損` 或 `candidate evidence corruption`。
- 測試位置：`tests/test_install.py` 檔尾，名稱以 `test_candidate_` 開頭。

### UNBORN 裁決（Jeff 2026-11-04）

1. `target_head` 是 schema 的正式欄位值。repo 已有 HEAD ⇒ 寫完整 40 碼 commit SHA；repo 為 unborn branch、尚無 commit ⇒ 寫固定 sentinel `"UNBORN"`（全大寫、逐字）。
2. `"UNBORN"` 必須納入 candidate canonical JSON 與 hash。
3. 之後一旦產生第一個 commit，`target_head` 由 `"UNBORN"` 變為 SHA，舊 approval hash 自動失效。
4. 不得要求使用者先做「未受治理的初始 commit」。

### 非 git 目錄裁決（Jeff 2026-11-04）

目標路徑不存在或不是 git repo ⇒ preflight 零寫入拒絕安裝，印明確訊息（請先 git init）；installer 不得再自行 git init 或 makedirs 目標。若此行為使任何本票以外的既有測試轉紅 ⇒ 停手回報，不改既有測試、不自行改成支援。

- 輪二紅燈：`TestTicket169UnbornAndNonRepo`（`test_candidate_unborn_target_head_sentinel`、`test_candidate_non_repo_target_stops`）。

### D4 例外（Jeff 2026-11-04）

「D4 例外：測試夾具與 verify_gates.py 對其本次自行建立、使用後即丟棄的臨時 repo，可在同一受控流程內產生 candidate、取得其 hash 並作為該次臨時安裝的 approval。candidate root 必須同樣位於該臨時環境，不得寫入真實 <agent-gates>/.dev/install-candidates/。此能力不得透過 CLI、環境變數或設定暴露給正式安裝，也不得適用於任何既存／真實目標 repo。」

邊界（全部必須在程式與測試中成立）：

- **E1**：只限本次由該 fixture／verify_gates.py 自行建立、明確標記為 disposable 的臨時 repo；不得以「路徑看起來像 temp」判斷。判定依據必須是建立目錄當下、同一程序內產生的記憶體物件（例如建立函式回傳的 sandbox 物件，記錄它親手建立的路徑）；不得用磁碟上的標記檔、路徑樣式、環境變數或字串參數作為依據。不是該物件親手建立的目標 ⇒ 拒絕 self-approve、零寫入。
- **E2**：self-approve 只存在於內部函式呼叫；不得新增 CLI flag、環境變數、設定檔開關，或任何可由字串傳入的參數。正式 `install.py <target>` 路徑仍只接受 Jeff 明示提供的 `--approve-inventory <hash>`。
- **E3**：candidate root 必須在該臨時環境內；不得讀寫真實 <agent-gates>/.dev/install-candidates/。
- **E4**：installer 的核准判定本身不變：一律依現況重算 hash 並逐字比對（沙盒流程只是自己把剛算出的 hash 交回去）。
- **E5**：碰到既存／真實目標 repo（非 E1 物件建立者）一律拒絕。

實作對位（輪三）：`install.create_disposable_repo(path, candidates_dir)` 親手 `mkdir` 並在本程序記憶體登記（以物件身分 `id()` 與物件本身比對）；`install._registered_sandbox(obj)` 只查這份登記；`install.install_disposable(sandbox)` 只接受登記過的物件本身；`install.main(target)` 收到登記過的物件才會把剛算出的 hash 交回同一條比對路徑（E4）。verify_gates.py 的 `create_repo` 改經 `create_disposable_repo`，候選根目錄為 `<workdir>/install-candidates`；`tests/test_install.py` 的 `g3_installed_repo` 改為沙盒兩段式（斷言未改）。紅燈：`TestTicket169DisposableException`。

### 既有 policy 裁決（Jeff 2026-11-04）

目標已有 extension policy 檔 ⇒ 維持輪三行為：零寫入拒絕、不接手。理由：本票只處理新下游首次安裝；既有名冊是否可信、可否沿用核准屬新問題，不擴票。

### 第一個 commit 前重驗（Jeff 2026-11-04）

installer 在第一個 git add／commit 之前，依現況重新產生候選並重算 hash：一致 ⇒ 才進第一個 commit；不一致 ⇒ 停止、執行自動復原、寫出新 candidate 並印新 hash；舊 approval 失效。

### 自動復原（rollback）邊界（Jeff 2026-11-04）

- **R1**：開始寫入前先記錄足以驗證原狀的 snapshot：HEAD、index、tracked／untracked 集合、會被修改的既有檔內容（bytes）、repo-local git config、hooks 狀態；另須記錄目標 repo 開始前的完整檔案系統路徑存在快照（filesystem path existence snapshot），包含 tracked、untracked、ignored 路徑與目錄本身，至少覆蓋 installer 可能建立／修改／刪除的全部路徑。不得只以 Git 看得到的集合代替。
- **R2**：只能刪除同時滿足兩條件的路徑：(1) 在 R1 的開始前檔案系統快照中不存在；(2) 在本次 installer 的寫入／建立紀錄（write journal）中。開始前已存在的 ignored 路徑／目錄，即使本次被碰過，也只能依 R3 還原，不得因 Git 看不到就刪除。
- **R3**：開始前存在的檔案一律不得刪除；若本次修改過，只能恢復為開始前 bytes。
- **R4**：.gitignore、hooks、core.hooksPath 等都納入 rollback。
- **R5**：rollback 完成後，重新驗證 R1 各項與開始前完全一致。
- **R6**：rollback 自身失敗或驗證不一致 ⇒ hard fail、停止，不再嘗試其他修復，不得宣稱已恢復原狀（訊息需明說未恢復）。
- **R7**：rollback 只處理第一個 commit 前的失敗；不得被用作 commit 後的 reset／rollback 一般機制。

新結束碼：`install.EXIT_REVERIFY_ROLLED_BACK = 6`（重驗不一致、已復原並驗證）；`install.EXIT_ROLLBACK_FAILED = 7`（復原失敗或復原後驗證不一致，未恢復）。既有 3／4／5 不變。

實作對位（輪四）：`_begin_journal`（R1，在 `copy_into` 之前）；`_reverify_before_commit`（第一個 `git add` 之前）；`_rollback`（R2／R3／R5／R6）。復原範圍從第一個寫入起，到第一個 commit 成功為止（含 add／commit 本身失敗）；journal 另登記 `.git/index`、`.git/objects/`、`.git/COMMIT_EDITMSG`、`.git/index.lock`，以及目標 redlight 載入時留下的 `.claude/hooks/__pycache__`。紅燈：`TestTicket169Rollback`。

### rollback 範圍裁決（Jeff 2026-11-04，新裁決 6）

rollback 有效到「第一次 commit 成功完成」為止（含 git add／commit 本身失敗）。理由：第一次 commit 尚未落進歷史前，安裝仍處在尚未建立不可逆治理基線的階段；此範圍仍符合 R7 原意，不構成 commit 後的通用 reset 機制。

### git worktree 型目標裁決（Jeff 2026-11-04，新裁決 7）

git worktree 型目標（.git 為檔案）暫時拒絕安裝，列為已知限制；目前無測試覆蓋，等有需求再開票。

已知限制：
- 第一個 commit 之後到安裝結束之間，若使用者層同步更新，末段 verify 仍可能擋下；R7 明定 rollback 不處理此段。
- git worktree 型目標拒絕安裝（新裁決 7）。

---

## 六｜不在本票範圍

- 改 R10 對使用者自訂指令的鎖定強度。
- LifeApp 的 §25 補訂。

## 六之一｜前輪偏差紀錄

- 輪一跑過一次未授權的純讀管線指令（Get-Content | Measure-Object）。
- 輪一遮罩掃描晚於寫入；事後 0 命中，但不得描述為符合原流程。
- Jeff 裁：記錄後繼續，不另開處置。
- 輪二寫入前遮罩先寫進 session scratchpad（指令未明文准許）；裁決助手依常設授權記錄後繼續，本輪起明文准許。
- 輪三寫入前遮罩漏跑兩處（install.py main 的 ext_note 說明文字、verify_gates.py :1016 註解）；寫入後整檔重掃 0 命中。
- 輪三曾把兩條檢索式合併成一條跑，隨即分開重跑皆 0。
- 以上兩條 Jeff 裁：記錄後繼續；不得描述為完全依流程執行。

## 七｜關聯

- 票 165：名冊更新流程。裁決者記為暫停中；票面狀態欄為「候選…未授權實作」。
- 票 167：同期修帳本。
- 票 146（R10 本體）、票 149／151（contract 的來源）。
- 票 170：安裝流程可用性與表述修正（AC-3 驗收發現，三個子項）。

---

## 七之一｜AC-3 驗收結果（2026-11-09）

- **彩排**：`<rehearsal>`（LifeApp 複本，origin 已移除）；上游 HEAD `5528204`。全程不連網；唯一的連網動作是第一輪 `setup_gates_env` 下載 7 個釘死版本與指紋的套件。
- **第一輪**：不帶核准 ⇒ 結束碼 3。安裝前後對彩排做完整檔案快照，digest 相同（entries 2806），下游零寫入；上游只多 1 個候選檔。候選內容：synced 231（skills 228、plugins 3）、user_commands 1、hook command 1，其餘 0。
- **核准**：Jeff 親手提供核准 hash（未經任何 agent 代填）。
- **第二輪**：帶核准安裝 ⇒ 結束碼 0；commit 前重驗一致；探針照設計擋下。安裝後上游快照比出量測帳本（`.dev/intercepts-2026-11.jsonl`）變動而停手。
- **第三輪（首跑）**：起點條件誤寫「彩排 status 必須無輸出」而停（指令錯誤，未執行任何動作）；之後更正為只允許 `?? docs/decisions-pending.md`。
- **第三輪（重跑）**：648 行清單閘口因 installer_state 2≠3 而停；上游面驗證通過。
- **第三輪-B**：
  - 上游 `ls-files` 證明三個狀態檔中只有 `.dev/gate-exemptions.jsonl` 在上游追蹤 ⇒ 2＋1＝3，閘口成立。
  - 彩排中「上游 ignored 卻存在」的檔全部落在 setup_venv／mirror／pycache／installer_state 四類，other＝0。未取得原始 648 路徑集合，所以不能逐條判定每一項；訊息是否只是顯示錯誤，留待票 170。
  - 安裝後檢查：2 個安裝 commit、名冊 231、user_commands 恰為 `finmind.md`、pre-commit hook 存在。
  - verify_gates 結束碼 0（4 條硬擋各擋一次、7 條降級各提示一次、新 repo 框架測試 3076 passed）。
  - bootstrap 因 PowerShell 找不到 `sh` 而未啟動。
- **第四輪**：以 Git 安裝目錄的 `bin\sh.exe` 完整路徑、WorkingDirectory＝彩排執行 bootstrap ⇒ 子程序 ExitCode 0、identity ok；彩排 `core.hooksPath`＝`.githooks`（config 只新增此鍵）；上游 config 逐字不變。
- **AC-3 對照表**：

  | 項目 | 狀態 |
  |---|---|
  | 安裝 | 完成（第二輪） |
  | 探針 | 完成（第二輪；第三輪-B verify_gates 內再次成立） |
  | decisions-pending | 完成（已產生，未處理） |
  | bootstrap（hooksPath） | 完成（第四輪） |
  | verify_gates | 完成（第三輪-B） |
  | 上游面驗證 | 完成（第三輪-B、第四輪） |

  ⇒ 六項全部完成，**AC-3 通過**。
- 「除 Jeff 的 hash 核准外，過程中沒有人工修改 inventory 或 allowlist」：成立。
- 各輪報告（`.dev/reports/`，不進版控）：
  - `20261105T010426Z-ac3-rehearsal-r1.md`（第一輪）
  - `20261105T014945Z-ac3-rehearsal-r2.md`（第二輪）
  - `20261105T021109Z-ac3-rehearsal-r3.md`（第三輪首跑）
  - `20261105T022038Z-ac3-rehearsal-r3.md`（第三輪重跑）
  - `20261109T133756Z-ac3-rehearsal-r3b.md`（第三輪-B）
  - `20261109T135947Z-ac3-rehearsal-r4.md`（第四輪）

## 七之二｜驗收過程中的裁決與例外（Jeff）

- 上游被 git 忽略的 `__pycache__/*.pyc` 為可接受副作用；第二輪起 installer／verify_gates 一律加直譯器選項 `-B`。
- `.dev/intercepts-2026-11.jsonl` 的 append-only 變化為治理系統自身副作用，條件 L1～L4：開始前記錄完整 bytes 基準；結束後基準逐 byte 不變（新檔＝基準＋尾段）；尾段依 gate.py 帳本寫入契約逐行對應本輪活動；例外只限該檔。
- bootstrap 以 Git 內建 `sh.exe` 的完整路徑、WorkingDirectory 指定為彩排執行（不開串接指令例外、不用 Bash 工具、不由人工代跑）。

## 七之三｜驗收過程偏差（照實保留）

- 第三輪首跑：指令錯誤（起點條件誤寫），未執行任何動作即停。
- 第三輪-B：呼叫紀錄起算前的兩次 Read（確認兩支腳本逐字相同）未列入呼叫紀錄。
- 第四輪：兩支腳本未重新 Read 比對，依據是前一輪已逐字確認、之後未曾寫入。
- 第一輪 installer 未加 `-B`，是否寫過上游 `__pycache__`：未查證。
