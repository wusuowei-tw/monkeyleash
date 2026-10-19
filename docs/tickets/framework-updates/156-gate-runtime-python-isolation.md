# 156 — 閘門執行環境的 Python 隔離（P0 基礎設施）

**狀態**：**立案（設計封版）；R0／R1 偵察完成；紅燈未開始。**
**時鐘**：未記錄（待 Jeff 指定）。
**優先度**：P0（Jeff 2026-10-19 約 14:40，美東，裁決助手記錄，非逐字原話）。插入本票期間，「AI 正式執行管道」暫停。
**立案**：2026-10-19（美東）。票號 156 由 Jeff 2026-10-19 約 16:45（美東）指定（原定 155，見第二節 D6）；建檔前確認 `docs/tickets/framework-updates/` 內無 156 開頭的檔案。
**性質**：基礎設施票 —— 閘門（hook、pre-commit、安裝器驗證、CI）執行時所用 Python 的隔離。
**規格**：無獨立規格檔。本票第三節即設計契約；依據為〔R0〕、〔R1〕兩份偵察報告。本票不重述偵察內容，以「R0 §x」「R1 Kx／Qx」引用。
**路徑代稱**：`<agent-gates>`＝上游 repo；`<canary>`＝金絲雀 repo；`<desktop>`＝Jeff 的桌機；`<laptop>`＝本機；`<path>`＝其他本機路徑；下游直接寫 repo 名稱（`meetingbridge`、`serenity-research`）。實際路徑詳見本機紀錄。
**交叉引用**：〔R0〕`.dev/reports/2026-10-19T190532Z-ticket155-r0-recon.md`、〔R1〕`.dev/reports/2026-10-19T193157Z-ticket155-r1-recon.md`（兩份當時暫用票號 155，檔名維持原樣）；〔F0 停止〕`.dev/reports/2026-10-19T203914Z-ticket155-f0-draft.md`。

---

## 一｜問題

### 1-1 現在每個入口怎麼找到 python

| 入口 | 位置 | 怎麼找到 python | 依據 |
|---|---|---|---|
| Claude Code 前哨 hook | `.claude/settings.json:9` | 指令 `python "$CLAUDE_PROJECT_DIR/.claude/hooks/gate.py"` ⇒ PATH 上的第一個 `python` | R0 §A2、§F1 |
| pre-commit（進版控那一份） | `.githooks/pre-commit:18-19` | `python …leak_scan.py`、`exec python …gate.py --pre-commit` ⇒ PATH | R0 §F1 |
| pre-commit（安裝器範本，寫進 `.git/hooks/` 與下游 `.githooks/`） | `.claude/portable/install.py:63-70`（`HOOK`） | 同上 ⇒ PATH | R0 §D3、§F1 |
| 安裝器驗證 | `.claude/portable/install.py:552`（`verify()`） | `run(["python", …gate.py, "--pre-commit"])` ⇒ PATH | R0 §F1 |
| CI | `.github/workflows/tests.yml:50`、`:74`、`:97`、`:113` | `actions/setup-python` 3.11 之後用 `python` ⇒ runner 的 PATH；`:50` 為 `pip install -e ".[dev]"` | R0 §F1；R1 K4-6 |
| `verify_gates`／`mcp_server`／`g1_verify` 的子程序 | `verify_gates.py:501`、`:515`、`:842`；`mcp_server.py:203`；`g1_verify.py:175` | `sys.executable` ⇒ 沿用**呼叫者**的直譯器 | R0 §F2 |

- `<laptop>` 上 PATH 的解析結果（觀測，R0 §B1～B3）：`where.exe python` 依序是全域安裝的 3.11 與 WindowsApps 的 `python.exe`；`py -0p` 只列出一支 3.11；`python --version` → `Python 3.11.9`。
- hook 由哪個 shell 執行：**高度支持 bash，但未證明**（R0 §A4，U-a）。`settings.json` 沒有 `"shell"` 鍵；指令用的是 POSIX 變數寫法 `$CLAUDE_PROJECT_DIR`。

### 1-2 根因（R0 已觀測）

- 會實際執行的入口裡，用裸 `python` 的有：
  - `.claude/settings.json:9`（hook）
  - `.githooks/pre-commit:18-19`
  - `install.py:69-70`（`HOOK`）、`:552`（`verify()`）
- 政策登記面：`.agents/extension-allowlist.json:14` 目前登記、認可的也是裸 `python` 指令。**它不是執行入口**，但換 hook 時必須同步修改（R0 §D3：sync 會把上游 `settings.json` 帶到下游，而下游的允許清單是 skip，不會跟著改 ⇒ 〔讀碼推論〕R10 會擋）。
- `verify_gates` 正二的政策＝全域環境 ∩ 能力邊界（`verify_gates.py:533-549`）。
- 全域 Python 由多個 repo 共用：它的套件集合（例如 mcp 帶進來的 anyio，R0 §B6、§B8）決定了閘門實際看到的環境，而這個集合不受任何一個 repo 管控。

### 1-3 不在本票範圍

- 全域 Python。
- `taishi-shared`。
- quant 與影片 repo。
- redlight 的宿主測試執行環境（redlight 在宿主 pytest 裡跑的那條路，見第二節約束 2）。

---

## 二｜裁決紀錄

依時間排序。

- **P0 插入**：插入 P0 基礎設施票：閘門 Python 執行環境隔離。「AI 正式執行管道」暫停，等 P0 收掉再回去。（Jeff 2026-10-19 約 14:40（美東），裁決助手記錄，非逐字原話）
- **D1**：每個 repo 各有一個專用的 `.venv-gates/`，不和專案自己的 `.venv` 混用。（Jeff 2026-10-19 約 14:52（美東），裁決助手記錄，非逐字原話）
- **D2**：`.venv-gates` 不裝下游的業務相依。（Jeff 2026-10-19 約 14:52（美東），裁決助手記錄，非逐字原話）
- **D3**：鎖定檔要加 hash（`--require-hashes`）。（Jeff 2026-10-19 約 14:52（美東），裁決助手記錄，非逐字原話）
- **D4**：各 repo 各自做 R10 政策提交，不用萬用字元。（Jeff 2026-10-19 約 14:52（美東），裁決助手記錄，非逐字原話）
- **D5**：`g1_guard`（使用者層）另開票；本票只記為 KNOWN FOLLOW-UP。（Jeff 2026-10-19 約 14:52（美東），裁決助手記錄，非逐字原話）
- **D6**：票號 156（原定 155；155 已在 10/16 給了 Flutter 候選票，16:45 更正）。（Jeff 2026-10-19 約 14:52 定號、約 16:45（美東）更正，裁決助手記錄，非逐字原話）
- **約束 1**：啟動器只認 `.venv-gates`，絕不退回 `.venv` 或 PATH 上的 python。（Jeff 2026-10-19 約 14:52（美東），裁決助手記錄，非逐字原話）
- **約束 2**：本票只處理閘門執行環境；redlight 在宿主 pytest 裡跑的那條路不重構，維持能力邊界 fail-closed。（Jeff 2026-10-19 約 14:52（美東），裁決助手記錄，非逐字原話）
- **D7**：anyio 鎖 4.15.0；4.15.1 仍留在能力邊界內。（Jeff 2026-10-19 約 15:26（美東），裁決助手記錄，非逐字原話）
- **D8**：啟動器用 sh；先在一次性的金絲雀 repo 直接取證，取證成功之前不切換正式 hook。（Jeff 2026-10-19 約 15:26（美東），裁決助手記錄，非逐字原話）
- **D9**：mcp 拆出去，另成「上游測試專用」鎖定檔；下游的 `.venv-gates` 不裝 mcp，也不裝 anyio。（Jeff 2026-10-19 約 15:26（美東），裁決助手記錄，非逐字原話）
- **D10**：換 hook 採「先擴、後縮」。（Jeff 2026-10-19 約 15:26（美東），裁決助手記錄，非逐字原話）
- **K1**：`meetingbridge`、`serenity-research` 的位置：R0 §E 在 repo 內的紀錄裡判為 UNPROVEN；不猜、不掃磁碟。（Jeff 2026-10-19 約 15:26（美東），裁決助手記錄，非逐字原話）其後補充：兩個下游 repo 在 `<desktop>`，不在 `<laptop>`。（Jeff 2026-10-19 約 15:31（美東），裁決助手記錄，非逐字原話）
- **K3**：本票的完成標準是「可重現、涵蓋目前支援的平台、能用 `--require-hashes` 成功建立 `.venv-gates`」；鎖定檔的再產生工具另外排後續。（Jeff 2026-10-19 約 15:26（美東），裁決助手記錄，非逐字原話）
- **K5**：金絲雀 repo 放在 `<canary>`；只做取證，取證完可以刪。（Jeff 2026-10-19 約 15:26（美東），16:45 隨票號改名，裁決助手記錄，非逐字原話）
- **D11**：新增 `--rehook`，內容見第三節第 7 條。（Jeff 2026-10-19 約 15:40（美東），裁決助手記錄，非逐字原話）
- **D12**：「重跑 `install.py` 不安全」另開後續票，不放進本票；本票明文禁止對已安裝的下游重跑完整的 `install.py`。（Jeff 2026-10-19 約 15:40（美東），裁決助手記錄，非逐字原話）
- **F0 核准附四項修正**：(1) 根因用語：允許清單是政策登記面，不是執行入口；(2) `runtime_identity` 分上游、下游兩種 profile，不在預期清單裡的額外套件一律 fail-closed；(3) `--rehook` 的所有權判斷寫死，兩支檔分別判定；(4) RT5 與驗收依 profile 修正。（Jeff 2026-10-19 約 16:25（美東），裁決助手記錄，非逐字原話）
- **F0 最終核准補兩項**（只把既有契約寫精確，不擴大範圍）：(5) `--rehook` 改成交易式全有或全無，失敗要回滾；(6) 預期套件集合依平台 marker 評估。另建議（不擋 F0）：已知 HOOK 範本以 sha256 加版本 ID 登記。本票不再增加功能。（Jeff 2026-10-19 約 16:32（美東），裁決助手記錄，非逐字原話）
- **F0 APPROVED**：來源紀錄改成依時間排序；RT8(i) 補驗 mtime。（Jeff 2026-10-19 約 16:36（美東），裁決助手記錄，非逐字原話）
- **票號更正**：上一版 F0 在步驟 0 停下（〔F0 停止〕），原因是票號 155 已於 10/16 給了 Flutter 候選票；D6 給號時裁決助手用的是過時的檔案副本。Jeff 選甲案：P0 改用票號 156；金絲雀 repo 隨之改名；R0、R1 報告檔名維持原樣（`ticket155-…`），票面引用時註明「當時暫用 155」。（Jeff 2026-10-19 約 16:45（美東），裁決助手記錄，非逐字原話）
- **G1（manifest 逐檔分類）**：所有新的 portable 檔、鎖定檔、啟動器，都必須在 `.agents/portable-manifest.txt` 明確標上 copy 或 skip，不得靠目錄前綴推斷。逐檔分類：`.claude/portable/gates-lock.txt` → copy；`.claude/portable/runtime_identity.py` → copy；`.claude/portable/setup_gates_env.py` → copy；`.claude/bin/gatepy` → copy；`.claude/portable/gates-lock-upstream-tests.txt` → skip（只給上游用）；本票新增的測試檔在紅燈站逐檔分類，只給上游用的標 skip。（Jeff 2026-10-19 約 16:55（美東），裁決助手記錄，非逐字原話）
- **G2（所有權比對的正規化）**：判斷 hook 是不是我們的之前，只允許做一種正規化：CRLF → LF。已知範本的 sha256 一律對「LF 標準形」計算；`--rehook` 寫出的檔案一律用 LF；比對時用 LF 標準形的位元組來比。除了換行符號，其他一律要完全相同：不刪頭尾空白、不改編碼、不做 Unicode 正規化、不忽略行尾空白。（Jeff 2026-10-19 約 16:55（美東），裁決助手記錄，非逐字原話）
- **G3（RT2 範圍與允許清單遷移狀態）**：RT2 只檢查真正會執行的入口（`settings.json`、`.githooks/pre-commit`、`install.HOOK`、`install.verify()`）。允許清單改用「遷移狀態」另外驗收：擴張階段允許清單**恰好**允許舊指令＋新指令；縮回階段**只剩**新指令；收票時裸 python 的舊指令必須已經不存在。（Jeff 2026-10-19 約 16:55（美東），裁決助手記錄，非逐字原話）
- **G4（先建環境、再安裝）**：對**還沒安裝 agent-gates 的新 target repo**，`setup_gates_env.py` 必須從**一份已經存在的上游 agent-gates checkout** 執行：target 路徑以明確參數傳入；使用上游已提交的 `gates-lock.txt`；**只准**在 target 建立 `.venv-gates/` 與 `.git/info/exclude` 裡必要的登記；不得要求 target 事先有任何 agent-gates 的檔案。新下游流程為六步（見第三節第 8 條）。`install.py` 在**做任何寫入之前**，都必須先確認 `.venv-gates` 存在、身分檢查與 core profile 都合法；不合法就結束執行，而且 target 除了 bootstrap 建立的 `.venv-gates/` 和 `.git/info/exclude` 之外，不得留下任何變更。新增一條紅燈：在沒有 `.venv-gates` 的乾淨新 target 上執行 install，必須在**第一次寫入專案之前**就失敗。（Jeff 2026-10-19 約 16:55（美東），裁決助手記錄，非逐字原話）
- **設計契約封版**：G1～G4 補完後不再擴充內容。（Jeff 2026-10-19 約 16:55（美東），裁決助手記錄，非逐字原話）
- **RT11 前置定稿**：RT11 的 target 必須是乾淨、已 `git init`、還沒裝 agent-gates 的 repo；這不是擴大範圍。（Jeff 2026-10-19 約 16:56（美東），裁決助手記錄，非逐字原話）
- **F0c 補精確（a）（b）（c）**：(a) CRLF 版新版 hook 經 CRLF→LF 正規化後等於新版範本 ⇒ 視為已是最新、--rehook no-op，不重寫、不改 mtime；CRLF 能否在 Windows／Git Bash 執行留待桌機偵察與金絲雀觀測，不與所有權判定混在一起。(b) install.py 驗 target 時必須明確使用 target 自己 .venv-gates 的直譯器執行上游同一支 runtime_identity.py，並明確指定 target repo 與 downstream profile；不得以自身 sys.executable 代替，不得另寫第二套驗證邏輯。(c) 封版條目依時間移到 16:56 之前。三點皆為把既有契約寫精確，不重開設計。（Jeff 2026-10-19 約 18:54（美東），裁決助手記錄，非逐字原話）

---

## 三｜設計要點

### 1. `.venv-gates/`

- 每個 repo 一個，要加進 gitignore（〔讀碼推論〕R0 §F3：本 repo 的 `.gitignore` 目前沒有任何 `venv` 條目）。
- 底座是 3.11。依目前的觀測（R0 §B2～B3），`<laptop>` 上只有一支 3.11.9；不改全域 Python。
- bootstrap 方式（G4）：
  - 由上游 checkout 對 target 執行 `setup_gates_env.py <target>`；
  - 只建 `.venv-gates/` 和 `.git/info/exclude` 裡 `.venv-gates/` 的登記；
  - 正式安裝時，再由 `install.py` 把 `.venv-gates/` 永久寫進它產生的 `.gitignore`。

### 2. 兩份鎖定檔（都要帶 hash）

- `.claude/portable/gates-lock.txt`（核心，所有 repo 共用；manifest 標 copy，G1）：
  - `pyyaml`
  - `pytest==9.1.1`
  - pytest 的遞移相依
  - 涵蓋平台：Windows cp311 win_amd64 與 Linux cp311 manylinux（CI 用）
- `.claude/portable/gates-lock-upstream-tests.txt`（只用於上游；manifest 標 skip，G1）：
  - `mcp==1.29.1`
  - `anyio==4.15.0`
  - mcp 的整串相依
- 〔讀碼推論〕hook 本身只用到 pyyaml（R1 意外發現 6：`gate.py:1472 import yaml`；`leak_scan.py` 只有標準庫加 `scanner`）。pytest 會放進核心，是因為 `verify_gates` 要用 `sys.executable -m pytest`（`verify_gates.py:501`、`:842`）。
- 本專案本身**不安裝**（R1 K4 結論 (a)）。

### 3. 啟動器 `.claude/bin/gatepy`（sh）

- 只認 `<repo>/.venv-gates/Scripts/python.exe` 或 `<repo>/.venv-gates/bin/python`。
- 找不到 → exit 2，並印出原因。
- 絕不退回 `.venv` 或 PATH 上的 python（約束 1）。

### 4. 身分自檢 `runtime_identity`

- 驗 `sys.prefix != sys.base_prefix`，而且 `sys.prefix` 的實際路徑等於 `<repo>/.venv-gates`。
- 驗 Python 是 3.11.x。
- **分成兩種 profile**（Jeff 2026-10-19 約 16:25（美東），裁決助手記錄，非逐字原話）：
  - downstream profile：預期套件集合＝`gates-lock.txt`
  - upstream profile：預期套件集合＝`gates-lock.txt` ∪ `gates-lock-upstream-tests.txt`
- **預期集合的定義**（Jeff 2026-10-19 約 16:32（美東），裁決助手記錄，非逐字原話）：拿目前這台機器的 Python 版本、作業系統、架構，去評估鎖定檔裡的平台條件（environment markers），算出來的**有效集合**才是預期集合。不是把鎖定檔裡出現的每一個名字都當成必裝。
  - 同一份帶 hash 的鎖定檔可以收多個平台的 artifact hash；但身分比對時，比的是「這個平台實際應該安裝的套件集合」。
  - 例子：只在 Windows 才裝的相依（例如 colorama），在 Linux CI 上不存在，不算錯。
  - `--whoami`、RT5、`verify_gates` 一律用**同一套** marker 與 profile 評估規則。
  - 若最後決定讓全部相依都在每個平台無條件安裝，必須在票面明寫，不能留給實作者自行決定。
- 已安裝的每個套件，版本都要等於有效集合裡的版本。
- 除了 Python 與 pip 本身，以及票面明確列為 runtime-bootstrap 例外的項目之外，`.venv-gates` 裡只要出現**不在對應預期集合**的額外套件，就 fail-closed。（例外清單由紅燈站實測後列出，不在這裡猜；見第七節。）
- 一律用 `importlib.metadata` 讀版本，不用 `pip show`（原因：R0 §B6 的 cp950 問題）。
- `--whoami` 要印出：profile、直譯器路徑、`sys.prefix`、Python 版本、實際安裝的全部套件與版本。
- `gate.py` 只做便宜的前兩項；`verify_gates` 做完整檢查。

### 5. `setup_gates_env.py`

- 用指定的底座建立 venv，再用 `--require-hashes` 安裝。
- 需要連網，所以要 Jeff 授權。
- `bootstrap.sh` 只負責驗證，不負責安裝。
- 位置：`.claude/portable/setup_gates_env.py`（manifest 標 copy，G1）。
- 參數與限制（G4）：
  - 從一份已經存在的上游 agent-gates checkout 執行；target 路徑以明確參數傳入（`setup_gates_env.py <target>`）；
  - 使用上游已提交的 `.claude/portable/gates-lock.txt`；
  - **只准**在 target 建立兩樣東西：`.venv-gates/`，以及 `.git/info/exclude` 裡 `.venv-gates/` 的登記；
  - 不得要求 target 事先有任何 agent-gates 的檔案。

### 6. 改用啟動器的地方

- `settings.json` 的 hook
- `.githooks/pre-commit`
- `install.py` 的 `HOOK` 與 `verify()`
- 允許清單
- CI：改成照鎖定檔安裝，不再用 `pip install -e`
- `machine-init.md` 0-1、0-2 節
- `.agents/portable-manifest.txt`：照 G1 逐檔分類（見第二節 G1）
- `install.py` 的事前檢查（G4）：做任何寫入之前，先確認 `.venv-gates` 存在、身分檢查與 core profile 都合法；不合法就結束，target 除了 bootstrap 建立的兩樣東西之外不留任何變更。另外，`install.py` 要把 `.venv-gates/` 寫進它產生的 `.gitignore`。驗證 target 時，必須明確啟動 `<target>/.venv-gates` 的直譯器，去執行上游同一支 `runtime_identity.py`，並明確傳入 target repo 與 downstream profile；不得用 `install.py` 自己的 `sys.executable` 代替，不得另寫第二套驗證邏輯（F0c (b)）。
- 新的 HOOK 文字仍然要包含 `gate.py`、`--pre-commit`、`leak_scan`，讓 `authoritative_layer`（`gate.py:393-418`）照常判定為已安裝（R1 Q4：它只比對這三個子字串）。

### 7. `--rehook`（D11），共六條

1. 只寫 `.git/hooks/pre-commit` 與 `.githooks/pre-commit`，其他檔一律不碰。
2. 目標沒有 `.venv-gates` → 拒絕。
3. 不自動提交；不准使用 `--no-verify`。
4. 目標從來沒裝過 agent-gates → 拒絕。
5. **冪等**：兩支檔已經是期望內容時，回報 no-op；重跑不得改變內容、時間戳，也不得有其他副作用。CRLF 版的新版 hook 經 G2 正規化後等於新版範本時，同樣視為已是最新 ⇒ no-op，不重寫、不改 mtime（F0c (a)）。
6. **執行前驗證身分與所有權**（寫死，Jeff 2026-10-19 約 16:25（美東），裁決助手記錄，非逐字原話）：
   - 「已安裝」：`.claude/hooks/gate.py` 與 `.agents/extension-allowlist.json` 兩者都必須存在。本票**不新增** provenance 制度（R1 已確認 install 不寫 provenance）。
   - `.git/hooks/pre-commit` 與 `.githooks/pre-commit` **分別判定**。檔案存在時，內容必須逐位元組等於本票明確登記的某一版已知 agent-gates `HOOK` 範本。已知範本清單寫在程式與票面裡：目前的裸 python 版，以及本票的新版。
   - **比對前的正規化**（G2，Jeff 2026-10-19 約 16:55（美東），裁決助手記錄，非逐字原話）：
     - 只允許一種正規化：CRLF → LF；
     - 已知範本的 sha256 一律對 LF 標準形計算；比對時用 LF 標準形的位元組來比；
     - `--rehook` 寫出的檔案一律用 LF；
     - 除了換行符號，其他一律要完全相同：不刪頭尾空白、不改編碼、不做 Unicode 正規化、不忽略行尾空白。
   - 只要有任何一支存在、但內容不認得（手工改過或自訂的）→ 整次 `--rehook` fail-closed，**兩支都不寫**。
   - 缺了其中一支怎麼辦，依現有安裝契約決定：〔讀碼推論，R1 K2-1〕現行的 `install.py` 一定會同時寫這兩支（`install_hook` 在 `:244-259`，`install_portable_layer` 在 `:266-303`）。所以「缺一支」不是現行安裝契約會產生的狀態 ⇒ fail-closed，不補建。這也涵蓋沒有 `.githooks/` 的舊下游（影音，票 58:169）。這條判定寫進 RT8(g)。
   - 所有權驗證全部通過之後，才開始更新兩支目標檔。更新必須是**交易式、全有或全無（all-or-nothing）並可回滾**（Jeff 2026-10-19 約 16:32（美東），裁決助手記錄，非逐字原話）：
     - 先把兩支的新內容完整準備好，並且驗證無誤；
     - 替換之前，先保存兩支的原始內容與 metadata（mode、mtime）；
     - 第二支或之後任何一步替換失敗時，必須把已經改掉的第一支復原；
     - 最終狀態只允許兩種：「兩支都是舊的」或「兩支都是新的」，不得留下一新一舊；
     - 本票**不**宣稱檔案系統能提供跨檔的真正原子交易 —— 上面是以保存與復原達成的全有或全無，不是檔案系統層的原子性。
   - 已知範本要用**固定的 sha256** 來識別（每一版有自己的版本 ID）。程式和票面都要登記這張「版本 ID → sha256」對照表，不能只寫「舊裸 python 版」「本票新版」這種名稱。實際的 sha256 值在紅燈站產生範本後填入（見第七節）。

### 8. 換 hook 的順序（D10，每個 repo 都照做）

1. 擴張階段（G3）：允許清單**恰好**允許舊指令＋新指令（R10 政策提交）
2. `.gitignore` 加上 `.venv-gates/`
3. 建立 `.venv-gates`
4. 用 `--whoami` 核對身分
5. 切換：上游直接提交；下游用 sync 帶入 `settings.json` 與啟動器，pre-commit 用 `--rehook`
6. 跑探針（`machine-init` 0-2 的「訊息翻面」法）
7. 縮回階段（G3）：允許清單**只剩**新指令（R10 政策提交）；收票時裸 python 的舊指令必須已經不存在

- **對已安裝的下游，禁止重跑完整的 `install.py`**（D12）。
- 下游的切換在 `<desktop>` 進行；開始之前先做一站桌機唯讀偵察。

**新下游（從來沒裝過 agent-gates）的流程**（G4）：

1. 從上游 checkout 執行 `setup_gates_env.py <target>`
2. 在 target 的 `.git/info/exclude` 登記忽略 `.venv-gates/`（由第 1 步的 setup 完成）
3. 驗證 `.venv-gates` 的身分
4. 執行正式的 `install.py`（它在任何寫入之前先做 G4 事前檢查）
5. `install.py` 把 `.venv-gates/` 永久寫進它自己產生的 `.gitignore`
6. installer 最後透過新的啟動器驗證

### 9. 金絲雀（D8，K5）

- 在 `<canary>` 建立最小的 repo、它自己的 `.venv-gates`，hook 指令的形狀與正式版相同，後面接一支只寫出 `sys.executable`／`sys.prefix` 的小腳本。
- Jeff 在該 repo 開 Claude Code，做一次 Write。
- 判讀：結果檔出現、而且指向 `.venv-gates`，才算 U-a 已證明。沒有出現 → 不切換，回頭設計 `.cmd` 或寫絕對路徑。

---

## 四｜紅燈測試（先寫，並且要看到它們失敗）

- **RT1**：沒有 `.venv-gates` 時呼叫啟動器 → exit 2。PATH 上放一支假 `python`，存在的 `.venv` 也放假直譯器，兩者被呼叫都會留下記號檔；斷言兩個記號檔都**不存在**。
- **RT2**（G3）：只檢查四個會實際執行的入口 —— `settings.json`、`.githooks/pre-commit`、`install.HOOK`、`install.verify()` —— 沒有任何指令開頭是裸 `python`。允許清單不在 RT2 範圍內，改由第五節的遷移狀態驗收。
- **RT3**：身分自檢遇到不在 venv 裡，或 `sys.prefix` 不是 `<repo>/.venv-gates` → fail-closed。
- **RT4**：身分自檢遇到版本跟鎖定檔不符 → fail-closed，訊息要指名是哪一個套件。
- **RT5**（依 profile 判定）：
  - 核心鎖定檔不得包含 `mcp` 或 `anyio`。
  - 只有上游測試鎖定檔可以包含 `mcp==1.29.1`、`anyio==4.15.0`。
  - 能力邊界的檢查只看**實際出現**的項目：出現了就必須落在 `redlight.py` 的邊界內。不得要求 downstream profile 一定裝有 anyio。
  - 上游完整環境的預期集合＝兩份鎖定檔的聯集，並依目前平台評估 marker 之後的有效集合。
  - 平台案例：同一份鎖定檔，分別以 Windows 與 Linux 的 marker 環境評估，兩邊各自得到正確的有效集合。只存在於某一平台的相依，在另一平台缺席時不得判紅。
  - 出現不在對應預期集合裡的額外套件 → fail-closed，只有已登記的例外可以放行。
- **RT6**：`install.py` 裝到乾淨的目標之後，兩支 pre-commit 都走啟動器，`verify()` 也走啟動器。
- **RT7**：CI workflow 照鎖定檔安裝，並在 `.venv-gates` 裡執行（由 `test_ci_workflow` 守著）。
- **RT8**（`--rehook`，D11）：
  - (a) 沒有 `.venv-gates` → 拒絕；
  - (b) 沒裝過 → 拒絕；
  - (c) hook 內容不是已知範本 → 拒絕，而且檔案不變；
  - (d) 執行後，除了兩支 pre-commit 之外，所有受追蹤的檔、`.dev/pipeline.json`、兩本帳本、允許清單、CLAUDE.md、provenance 都**逐位元組不變**；
  - (e) 已經是期望內容時重跑 → 回報 no-op，內容與 mtime 都不變；
  - (f) 不建立任何 commit；
  - (g) 兩支 pre-commit 缺了其中一支 → fail-closed，另一支也不寫；
  - (h) 兩支都存在，一支是已知範本、另一支不認得（自訂內容）→ fail-closed，兩支都不變；
  - (i) 模擬第二支替換失敗（第一支已經換掉）→ 第一支被回滾；兩支的內容、mode、mtime 都回到原狀；不留一新一舊；
  - (j)（G2）CRLF 版的已知範本 → 判為「已知」；只差行尾空白、或只差 BOM 的內容 → 判為「不認得」，fail-closed；
  - (k)（F0c (a)）hook 是 CRLF 版的新版範本 → 回報 no-op，內容與 mtime 都不變。
- **RT9**（G4）：在沒有 `.venv-gates` 的乾淨新 target 上跑 install → 在第一次寫入專案之前失敗。斷言 target 的工作區、index、`.git/hooks/` 都沒有被寫入（只有 bootstrap 該建的東西可以存在；這個案例裡兩者都不存在）。
- **RT10**（G4）：`.venv-gates` 存在、但身分不合法（例如 profile 不符）→ install 一樣在第一次寫入之前失敗。`install.py` 本身是在合法的上游 `.venv-gates` 裡執行時，結果也必須相同；並斷言用來驗證的直譯器是 `<target>/.venv-gates` 的那一支，不是 `install.py` 自己的 `sys.executable`（F0c (b)）。
- **RT11**（G4，Jeff 2026-10-19 約 16:56（美東）定稿，裁決助手記錄，非逐字原話）：
  - 前置：target 必須是**乾淨、已經 `git init`、還沒裝 agent-gates** 的 repo。不能用一般的空資料夾，因為 setup 要修改 `.git/info/exclude`。
  - 從上游對這個 target 執行 `setup_gates_env.py <target>`。
  - 本測試不連網：用假的套件來源，或用 monkeypatch 把安裝動作隔離開；用哪一種由紅燈站決定。
  - setup 成功之後，target 只允許有兩項變化：
    1. 新增 `.venv-gates/`；
    2. `.git/info/exclude` 新增 `.venv-gates/` 的登記，而且只新增這一筆。
  - 除了上面兩項，其他都不能變：已追蹤、未追蹤的專案檔案都不變；index 不變；hooks 不變；不產生任何其他 agent-gates 檔案。
- **RT12**（G1）：每一個新檔在 manifest 裡都有明確的 copy 或 skip，而且分類必須跟第二節 G1 的表格一致。

---

## 五｜驗收

1. 上游全套測試在 `.venv-gates` 裡全綠。
2. `verify_gates` 綠燈，正二情境綠燈，而且政策裡的版本＝上游 profile 的預期集合。
3. `gatepy --whoami`：
   - 指向 `<repo>/.venv-gates`；
   - 印出的 profile 正確（上游是 upstream，下游是 downstream）；
   - 實際安裝的套件＝該 profile 的預期集合（加上已登記的例外）；
   - 沒有 `taishi-shared`；
   - 下游沒有 mcp／anyio。
4. 金絲雀取證成功。
5. 探針訊息翻面。
6. CI 綠燈（Jeff 目視）。
7. 下游（`<desktop>` 上的 `meetingbridge`、`serenity-research`）：
   - `--whoami` 核對通過；
   - pre-commit 經啟動器通過；
   - 各自的測試結果與切換前相同；
   - 最後縮回允許清單。
8. 允許清單的遷移狀態（G3）：
   - 擴張時**恰好**是新＋舊；
   - 收票時**只剩**新；
   - 裸 python 的舊指令一筆都不剩。
9. 新下游的 bootstrap 流程（G4，第三節第 8 條的六步）至少走通一次。可以用金絲雀，或用測試裡的乾淨 target 證明。

---

## 六｜已知後續（KNOWN FOLLOW-UP，本票不實作）

- `g1_guard`（使用者層）仍然用裸 python（D5）。
- **既有的 `install.py` 不適合拿來重裝或刷新 hook**。R1 讀碼推論它會：
  - 清空帳本（`:193-194`）
  - 把 pipeline 重設為 idle（`:190-192`）
  - 覆寫 CLAUDE.md 與 manifest
  - 用新的 go-live 重新產生、擴大豁免清單（`:358-383`）
  - 多兩筆 `--no-verify` 提交（`:649`、`:655`）
  - 本票對已安裝的下游**必須**使用 `--rehook`，**禁止**重跑完整的 `install.py`（D12）。另開一張票處理 installer 重裝的安全性與冪等性。
- 鎖定檔的再產生工具（K3）。
- `authoritative_layer` 只比對子字串，看不出 hook 是不是還在用裸 python（R1 Q4）。是否把這一項加進 status，另外再裁。
- `monkeyleash.egg-info/` 已經過期；全域 Python 裡留有 `pip install -e .` 的痕跡（R1 意外發現 4）。
- `templates/pyproject.toml.template` 可能是死檔（R1 意外發現 5）。
- 在 cp950 主控台下，`pip show` 會在非 ASCII 的 metadata 上崩潰（R0 §B6）。

---

## 七｜未決

- runtime-bootstrap 例外清單（第三節第 4 條）：要等紅燈站實際建出 venv 之後才能列出。
- 已知 HOOK 範本的「版本 ID → sha256」對照表：在紅燈站填入。
- U-a（hook 的 shell）：目前「高度支持 bash，但未證明」，等金絲雀取證。
- 桌機的 Python 版本、桌機上 agent-gates 的副本位置、兩個下游目前的 hook 長什麼樣子：等桌機偵察。
- manifest 分類與換行正規化已由 G1、G2 裁定，見第二節。
- 下游在 Windows 上的工作區實際是不是 CRLF，仍然要在桌機偵察時觀測（G2 只解決了比對規則）。依據：上游的 `.githooks/pre-commit` 由上游的 `.gitattributes` 釘成 LF（觀測：`git ls-files --eol` → `i/lf w/lf attr/text eol=lf`），但 `.gitattributes` 在 manifest 標 skip（`:71`；`:60-61`），不隨安裝走；票 154 曾觀測到 `git restore` 之後工作區變 CRLF 的現象（票 154 第四節之三）。另外要觀測 CRLF 的 hook 能不能被 Git Bash 正常執行（F0c (a)：與所有權判定分開）。
- 上游自己的 `.githooks/pre-commit` 跟 `install.HOOK` 不一樣（上游多了 `:4-16` 的註解段；觀測）。這不影響 `--rehook`：上游直接提交新 hook（第三節第 8 條第 5 步），不走 `--rehook`；`--rehook` 的已知範本只需涵蓋安裝器產生的那幾版。

---

## 修正紀錄

- 立案草稿（2026-10-19，裁決助手記錄，非逐字原話）：依 R0／R1 偵察（當時暫用票號 155）與 Jeff 2026-10-19 14:40～16:45 的裁決起草。上一版 F0 因票號衝突在步驟 0 停下，見〔F0 停止〕。
- G1～G4 補入（2026-10-19，裁決助手記錄，非逐字原話）；設計契約封版。
- F0c (a)(b)(c) 補入；票面封版（2026-10-19，裁決助手記錄，非逐字原話）。
