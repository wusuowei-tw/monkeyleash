# 156 — 閘門執行環境的 Python 隔離（P0 基礎設施）

**狀態**：~~**立案（設計封版）；R0／R1 偵察完成；紅燈未開始。**~~ **已結案（2026-10-20，限定範圍：上游；下游推廣等移入後續票，見驗收最終狀態與範圍調整紀錄）。**
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
- **S3b 裁決（D-1～D-11）**：依 S3a 紅燈設計審查，裁定如下。（Jeff 2026-10-19 約 20:01（美東），裁決助手記錄，非逐字原話）
  - D-1：納入本票（不改會讓 R3／redlight 誤判，屬必要相容修正）。`.venv-gates` 加進所有實際參與掃描的跳過／忽略集合：`gate.NON_SOURCE_DIRS`、`redlight._SEARCH_SKIP`、`test_source_hygiene._H2_SKIP_DIRS`，`test_non_source_list_parity.IN_BOTH` 同步；先要有紅燈證明「沒有排除時真的會掃進 venv」。
  - D-2：HOOK v2 加一行註解（全文見 `tests/fixtures/hooks/hook-v2-gatepy.sh`）。
  - D-3：不新增 `gatepy --whoami` 子命令；正式寫法是 `gatepy .claude/portable/runtime_identity.py --whoami …`，gatepy 只選定 `.venv-gates` 直譯器並轉交參數。
  - D-4（暫定）：runtime-bootstrap 例外候選 `pip==24.0`、`setuptools==65.5.0`，以名稱＋精確版本登記；實作站建出真的 `.venv-gates` 後觀測確認，**觀測不同就停，不得為了轉綠擴大例外清單**。
  - D-5：新測試檔分類照 S3a 6-7；`tests/test_gatepy.py` 標 skip、載入 `test_bootstrap.find_sh`；找不到 sh 就 fail，不 skip。
  - D-6：既有 installer 測試以 fixture／monkeypatch 讓事前檢查通過；「寫入前就失敗」只由 RT9、RT10 驗。
  - D-7：平台 marker 以 `packaging.markers` 評估。
  - D-8：允許清單遷移狀態不寫成常駐測試，改在各站核對。
  - D-9：bootstrap 只驗兩件事：`.venv-gates` 的直譯器存在、`--whoami` 退出碼為 0。
  - D-10：`install.py` 的驗證（`verify()` 與事前檢查）不經 gatepy、不依賴 sh：明確取 `<target>/.venv-gates/…/python`，用它執行**上游**的 `runtime_identity.py`（`--repo <target> --profile downstream`）；不得用裸 `python`、不得用 installer 自己的 `sys.executable`、不得退回 PATH。
  - D-11（兩層）：
    1. **核心**（verify_gates 與 RT 測試）：用 fixture、tmp repo、monkeypatch 或假的安裝步驟，**沒有網路也必須能完整驗證控制流程與 fail-closed 行為**；一般 `verify_gates` 必須能離線、可重現地綠燈，PyPI／網路是否可用不得是它綠燈的必要條件。
    2. **真實 bootstrap 整合**：照帶 hash 的鎖定檔真的建出 `.venv-gates`。CI 可在**明確允許網路**的整合步驟／job 執行；本機執行須 Jeff 明確授權；至少成功一次才算滿足驗收 9。CI 已有合適 job 就用它，沒有就設計最小的一條，不趁機重構 CI。
- **S4a 裁決（D-S4-1～D-S4-8）**：實作分八站 S4b → S4c → S4c′（金絲雀）→ S4d → S4e-1 → S4e-2 → S4f → S4g，D-S4-1～8 全照 S4a 建議，其中三條加邊界。（Jeff 2026-10-19 約 21:15（美東），裁決助手記錄，非逐字原話）
  - D-S4-1：身分檢查只在「正式直接執行 `gate.py`」時啟動（接在 `__main__`），`import gate` 本身不得觸發；同意在 S4e-2 修改真的會啟動 gate.py 子行程的 3 條既有測試（T146-59／60／60b 的 `_t146_pre_commit`）改用 target 的 `.venv-gates`，但只能讓測試符合新契約，不得 monkeypatch 掉、繞過或放寬正式身分檢查。
  - D-S4-4：S4b～S4g 每站一筆本機提交（錨點 A1～A7）；push 延到全部本機驗證完成後，push 前仍須核對遠端基線、提交範圍與最終 diff，不得盲推。
  - D-S4-7：不預先修改 R7；以 `.venv-gates` 的 Python 跑測試若被 R7 擋，立即停、保留原始拒絕訊息，回來裁決。
  - 其餘照建議：D-S4-2（S4e 拆兩段，中間重開 session）、D-S4-3（加 S4c′）、D-S4-5（鎖定檔照 P3 六步）、D-S4-6（`PyYAML==6.0.3`）、D-S4-8（D-4 觀測不符即停，不擴大清單）。
- **S4b 裁決（甲案兩處、帳本 append-only）**：（Jeff 2026-10-20 約 08:21（美東）裁決，裁決助手記錄，非逐字原話）
  - 甲案兩處：`tests/test_install.py:79-81` 的 framework 清單期望值加入 `.venv-gates/`（Jeff 2026-10-19 約 21:29（美東）裁）；`tests/test_verify_gates.py` 的 `test_t146_52b` 假安裝程式改為 `os.makedirs(…, exist_ok=True)`（Jeff 2026-10-20 約 08:21（美東）裁）。理由：兩處都是讓舊測試對齊 D-11／G4 的新契約（target 在 install 前先備好），不是放寬檢查；授權只限這兩處，再出現就停下等裁決。
  - 帳本 append-only 驗收：`gate.py` 合法自我修改時 `.dev/gate-exemptions.jsonl` 會自動追加紀錄，屬既有機制的正常證據。驗收改為嚴格 append-only：原始基線 319 行（sha256 `2a72d6976e1812e536a08d68ea25dedec8897e98092b86a4dc9f3505964e870e`）位元組完全不變；只允許在 EOF 之後追加、且只能是票 156 本次 `gate.py` 自我修改產生的紀錄，逐欄核對；提交時既有機制最多再追加一筆，同樣逐欄核對；不得有刪除、改寫、插入或任何不相關的額外紀錄；筆數或內容異常立即停下，不得解釋成正常自動紀錄；帳本永遠不 stage、不 commit、不 restore。
  - `setup_gates_env.main(argv, install_step=None)`：多出的注入參數預設就是真正的安裝步驟（`_install_lock`）；用途是讓 verify_gates 的核心模式傳入離線假步驟，而不必在正式程式裡改模組屬性。
  - `gatepy` 判斷候選直譯器只用 `-f`、不用 `-x`：Windows 沒有執行位元；就算命中一個不可執行的檔，`exec` 也會失敗，結果仍是擋下，不會放行。
  - **留給 S4f 的待裁**：核心模式下暫存 target 的 `.venv-gates` 是空的，install 的事前檢查（downstream profile 需要 pyyaml、pytest）預期會失敗；核心模式要怎麼通過這一關，已由 S4f-甲 裁定（見下方「S4f 裁決」）。
- **S4b′ 裁決（bootstrap profile 慣例、gatepy LF 持久化）**：（Jeff 2026-10-20 約 09:02（美東）裁決，裁決助手記錄，非逐字原話）
  - `bootstrap.sh` 以「`.claude/portable/gates-lock-upstream-tests.txt` 是否存在」選 profile（存在 ⇒ upstream，否則 downstream）：這只是 **profile selection convention**，**不是安全邊界**。真正的安全邊界是 runtime identity／profile 的精確比對 fail-closed；兩種誤判方向（上游被當下游、下游被當上游）都會因預期集合不符而擋下。
  - S4b′：gatepy 的 LF 寫成**持久化政策**（`.gitattributes` 新增 `.claude/bin/gatepy text eol=lf`）。理由：S4e-1 之後所有 active hook 都只經 `sh → gatepy → .venv-gates` 啟動，gatepy 是唯一的正式入口，被 checkout 成 CRLF 就會把閘門鎖死；而 gatepy 沒有副檔名，`*.sh text eol=lf` 涵蓋不到它。證據：A1 的 `git add .claude/bin/gatepy` 印出 `LF will be replaced by CRLF the next time Git touches it`（本機開著 autocrlf）；新增規則前 `git check-attr` 為 `text: auto`／`eol: unspecified`。紅燈測試問的是 Git 實際套用的屬性（`git check-attr`），不綁規則字面。
  - 下游判定：**B（待裁）**。installer 以 `shutil.copy2` 逐位元組照抄 gatepy，但 `.gitattributes` 在 manifest 標 **skip**（不隨安裝出貨），installer 對 `.gitattributes` 也沒有任何合併處理 ⇒ 下游拿不到這條規則；下游若開著 autocrlf，日後 checkout 可能把 gatepy 轉成 CRLF。本站不改 installer、manifest 或下游 `.gitattributes`。
  - **待裁：下游 gatepy 的 LF 保護**（要在下游切換 hook 之前決定）。
- **S4c 裁決與實測（帶 hash 的鎖定檔、上游 `.venv-gates`）**：（S4c 實測，裁決助手記錄，非逐字原話）
  - **S2a 個案裁決**（Jeff 2026-10-20 約 09:44（美東））：cryptography 50.0.2 的 `Requires-Dist: typing-extensions>=4.13.2 ; python_full_version < '3.11'` 用到禁用變數 `python_full_version`。**正式理由只有一個**：比較邊界在 `3.11`，依 PEP 440，所有 3.11.x 都 ≥ 3.11，這條 marker 在每一個 3.11 patch 版本上都恆為 False（稽核另以 `python_full_version=3.11.0` 評估，結果為 False）。「另有 8 條路徑帶入 typing-extensions」只列為旁證。本案**不建立泛化判例**，S2a 通則字面不改；下一次遇到 `python_full_version`／`implementation_version` 的 marker，照樣停下送裁決。「多條路徑」一項只適用於需要合成 marker 的 Windows-only 子套件；union 裡有 11 個多父套件，但兩平台都需要、父集合相同，不觸發。
  - **鎖定檔編碼約束**（Jeff 甲′，2026-10-20 約 09:57（美東））：pip 24.0 依 locale 解碼需求檔（`auto_decode` 遇到無 BOM 的檔案會改用 locale 編碼）。S4c 實測：檔頭含 UTF-8 中文時，cp950 在**解析需求檔**階段就失敗（`UnicodeDecodeError: 'cp950' codec can't decode byte 0xa8 in position 4`），還沒走到下載或 hash 驗證。因此兩份鎖定檔一律純 ASCII，由 `tests/test_runtime_identity_upstream.py::test_s4c_the_locks_are_pure_ascii` 鎖住（先紅後綠）。乙（pip 子行程設 `PYTHONUTF8=1`）、丙（BOM）不採用。
  - 第一次失敗留下的半成品 `.venv-gates`（裡面只有 ensurepip 預裝的 pip／setuptools），經 Jeff 核准後由 Jeff 手動移除（agent 的 `rm -rf` 被 R7 前哨擋下），之後重建。
  - **產生方式**（依證據模型）：
    - Windows：本機 CPython 3.11 上由 pip 24.0 **原生 resolver** 解析（`pip download --only-binary=:all:`，不加 `--platform`），core 7 個、union 37 個。
    - Linux cp311 manylinux x86_64：依據是 **wheel 可用性 probe**（`--no-deps --platform manylinux_2_17_x86_64 / manylinux2014_x86_64 / manylinux_2_28_x86_64`，36 筆全中、版本一致）**加上 METADATA marker 稽核**，**不是 Linux resolver**（pip issue #12466、#13442：`--platform` 不會切換 marker 的評估環境）。
    - hash：對每個釘住的版本讀 PyPI JSON API，收下支援範圍內的**全部** wheel（Windows 是 cp311／abi3／py3-none-any 的 `win_amd64` 相容 tag；Linux 是三個核准平台相容 tag 的聯集），sdist 一律不收。交叉核對：實際下載的 80 個檔，sha256 都等於 API 值，而且都在鎖定檔內；另以 `pip hash` 抽查 4 個，全部吻合。
  - **套件數**：`gates-lock.txt` 7 個；`gates-lock-upstream-tests.txt` 30 個（union 37 減 core 7；共用套件只列在核心那一份）。
  - **平台限定的套件**（相依邊表摘要）：只有兩個 Windows-only 套件，各自只有一條進入邊，marker 直接用原文：colorama（`sys_platform == "win32"`，來源：pytest 9.1.1）、pywin32（`sys_platform == 'win32' and python_version < '3.14'`，來源：mcp 1.29.1）。沒有 Linux-only 的邊或套件；稽核 FLAGS 為 0；extras 只有 `mcp -> pyjwt[crypto]`。
  - **下載量實測**（scratchpad 下載目錄，單位 bytes）：Windows core 7 檔 1,985,371；Windows union 37 檔 17,382,517；Linux probe 36 檔 12,160,099。`setup_gates_env` 的安裝另外以 `--no-cache-dir` 從 PyPI 下載了 37 個 Windows wheel，這一筆的總量沒有另外量。
  - **D-4 實測**：上游 `.venv-gates`（profile upstream）實際有 39 個 distribution，等於 upstream 有效集合 37 個加上 `pip==24.0`、`setuptools==65.5.0`，**與暫定相同**，例外清單不擴大。`--whoami --profile upstream` 退出碼 0（`identity: ok`）；`--profile downstream` 對照照預期 fail-closed（30 筆「額外套件」，正好是上游測試鎖定檔那 30 個）。
  - **全套結果**（兩種直譯器相同）：全域 python 與 `.venv-gates` 直譯器都是 `12 failed, 2825 passed, 10 skipped, 3 xfailed`。紅的 12 條就是 A1 那 15 條扣掉 S4c 轉綠的 3 條（RT5(a)、RT5(b)、D-11(c)），沒有收集期錯誤。以 `.venv-gates` 直譯器跑 pytest 沒有被 R7 擋下。
- **S4c′ 金絲雀取證（U-a）**：（Jeff 2026-10-20，裁決助手記錄，非逐字原話）
  - 在 `<canary>` 以 Claude Code 真正的 PreToolUse hook 做了兩次 Write，P1～P5 全部通過。hook 在 Git for Windows 的 MINGW64 bash 下，經 `sh → gatepy` 執行，用的是金絲雀自己的 `.venv-gates`（Python 3.11.9）。結果檔每一行都指向該 venv，沒有其他直譯器混入。**U-a 已證明。**
  - 瑕疵：第 1 次檔名 `canary-2026` 可預測，改用 B 方案重做一次補強；第 2 次 `canary-55663344` 長度合格，但只有數字而且有規律，Jeff 裁定不重做。
  - 金絲雀 `<canary>` 尚未刪除（K5）。
- **S4d 允許清單擴張（錨點 A3）**：（Jeff 2026-10-20，裁決助手記錄，非逐字原話）
  - A3 是 policy-only commit；允許清單新舊兩條指令並存；pre-commit 印出 `DECLARED_OK`。
  - 原 D2 的三方比對前提有誤：`install.py` 不寫死 settings 指令（它照抄上游 settings，再由 `_settings_hook_commands` 推出允許清單），票面也沒有新指令全文。這是裁決助手的錯誤。改為 fixed-string 比對（`grep -F`）加語義比對（json 解碼後做子字串比對）；`tests/test_install.py`、S3a 報告、允許清單三者一致。
- **S4e-1 正式 hook 改走 `sh → gatepy`（錨點 A4）**：（Jeff 2026-10-20，裁決助手記錄，非逐字原話）
  - `.claude/settings.json` 的 command 改為 `sh "$CLAUDE_PROJECT_DIR/.claude/bin/gatepy" "$CLAUDE_PROJECT_DIR/.claude/hooks/gate.py"`；`.githooks/pre-commit` 的兩行指令改為經 gatepy。
  - S4e-1 原指令要求整份換成範本，與 S3a 3-4 衝突（裁決助手錯誤），改依 S3a 3-4：保留上游 `:1-16` 歷史註解，只換指令行；上游 hook 因此不等於 hook-v2 範本。範本仍是新安裝／`--rehook` 的標準 v2 hook；上游不走 `--rehook`（票面 `:363`）。
  - S4e-1 探針（重開 session 後）：本 session 的 PreToolUse 前綴是 `sh "$CLAUDE_PROJECT_DIR/.claude/bin/gatepy" "$CLAUDE_PROJECT_DIR/.claude/hooks/gate.py"`；`touch .venv-gates/s4e1-probe` 被 R7 正常擋下、檔案未建立；沒有 `[gatepy]` 錯誤；`core.hooksPath` 為 `.githooks`；帳本只在檔尾追加。程序偏離：兩條唯讀 grep 同時送出，已接受，視為輕微。
- **S4e-2 gate-B 便宜身分檢查接上 `__main__`、T146 三條改用 target `.venv-gates`（錨點 A5）**：（Jeff 2026-10-20，裁決助手記錄，非逐字原話）
  - `gate.py` 新增 `gate_runtime_problem(root, prefix, base_prefix, version_info)`，只做第三節第 4 條的前兩項（在 `<root>/.venv-gates` 這個 venv 裡、Python 3.11.x；路徑判法與 `runtime_identity.evaluate` 相同，realpath＋normcase）；不合法時 stderr 印出含 `.venv-gates` 的訊息並以前哨的擋下碼 2 結束。只接在 `if __name__ == "__main__":`，`import gate` 不觸發（D-S4-1）。
  - `tests/test_install.py` 的 `_t146_pre_commit` 改用 target 的 `.venv-gates` 直譯器（`Scripts/python.exe`，其次 `bin/python`，順序照 gatepy）。venv 沿用 `g3_installed_repo` 的 `_g3_bootstrap_like_setup` 既有建法（真的 venv），沒有另外準備；未 monkeypatch、未繞過身分檢查。紅燈證據：改之前 T146-59／60／60b 被 `gate_runtime_problem` 擋下（`sys.prefix == sys.base_prefix`，`assert 2 == 0`）。
  - **本站之後，前哨與 pre-commit 都不能再靠全域 Python 救援**：改回 `settings.json` 也沒用，因為全域 Python 會被 gate-B 擋下。萬一閘門把自己鎖死，救援方式是由 Jeff 在編輯器裡親手刪掉 `__main__` 裡呼叫 `gate_runtime_problem` 的那 4 行，agent 不得自行繞過。
- **S4f 裁決（S4f-甲／乙／丙）與 R-3 判讀**：依 S4f-0 唯讀偵察（裁決助手已以原始碼核對）裁定如下。（Jeff 2026-10-20 約 13:53（美東），裁決助手記錄，非逐字原話）
  - **S4f-甲**：核心模式採 (d)。`verify_gates` 核心模式的假安裝步驟改為「離線複製」：從上游 repo 根目錄下**已安裝**的 `.venv-gates`，把 downstream profile 有效集合（`gates-lock.txt`、目前平台的 marker）的套件 payload 與 `*.dist-info` 複製進暫存 target 的 `.venv-gates`。複製前來源要先通過 `runtime_identity --profile upstream`；來源缺失或不合法 ⇒ `SystemExit`（含 `[verify_gates/核心]`），target 不寫入套件。完成後以 target 的直譯器執行上游的 `runtime_identity.py --whoami --repo <target> --profile downstream`，必須是 `identity: ok`（D-10）。宣告成功之前，除身分檢查外還要驗 payload 完整性或可用性。不採 (a)（CI 端查不到離線 wheel 的實際來源）、(b)（涵蓋面大幅縮小）、(c)（端到端改依賴網路）。
    - **證明的性質**：核心證明是**自洽**的 —— 上游 venv 的子集能通過 downstream 身分檢查；鎖定檔「真的裝得起來」由 CI 整合步驟（`id: gates-bootstrap-integration`）證明。
    - 紅燈：`TestS4fCoreCopiesFromUpstreamVenv` 六條（`test_s4f_d_*`；錨點 A6-紅），實作在 S4f-2。原本寫在 `tests/test_verify_gates.py`，S4f-丁 搬到 `tests/test_verify_gates_core_copy.py`。
  - **S4f-乙**：CI 的 `python-version` 釘成 `'3.11.9'`，與桌機一致。理由：`runtime_identity` 的 runtime-bootstrap 例外是精確版本（pip／setuptools 取自 3.11.9 的 ensurepip），只寫 `'3.11'` 時 runner 可能拿到別的修補版。改 `tests.yml` 在 S4f-2。
  - **S4f-丙**：`machine-init.md` 依 S4f-0 第 5 點的表一併改：0-1、0-2、`:667`、`:721`／`:746`、`:923-924`、`:1019`、`:1057-1062`；`:985` 不動（`import gate` 不觸發 gate-B）。在 S4f-2 改。
  - **R-3（裁決助手判讀）**：RT7 要求 CI 上所有 pytest 與 verify_gates 都在 `.venv-gates` 裡跑，所以**在 CI 上**，核心步驟以整合步驟先成功為前提。D-11「網路不得為核心綠燈的必要條件」的意思是：在已有合法 `.venv-gates` 的機器上，核心 `verify_gates` 不連網也能綠。(d) 符合這個解讀。
  - **待辦**：(d) 的自洽性 —— 核心證明的是上游 venv 子集能通過 downstream 身分檢查；鎖定檔可安裝性由整合步驟證明。
- **S4f-丁**：(d) 的紅燈六條（含專用 helper 與常數）原樣搬到新檔 `tests/test_verify_gates_core_copy.py`，manifest 標 `skip`（不出貨、上游專屬），比照 `tests/test_runtime_identity_upstream.py`。理由：這組讀上游 repo 自己已安裝的 `.venv-gates`，在下游與淨室 target 裡沒有意義。（Jeff 2026-10-20 約 15:31（美東），裁決助手記錄，非逐字原話）
  - **S4f-1 程序偏離的裁定**（裁決助手）：負控對 `packaging` 完整複製 —— 接受（符合「光靠 `identity: ok` 不夠」的用意）；用空 venv 當壞來源 —— 接受；規格 1 把來源檢查寫成子行程約束 —— 接受（同 D-10）；三個 Edit 並行送出 —— 記為違規。
- **S4f-丁之二（淨室 4 紅的處理）**：S4f-2 實作後，淨室第一次端到端走到「框架測試在新 repo 裡重跑」，`tests/test_verify_gates.py` 紅了 4 條（T146-52、T146-52b、D-11 (b)、D-11 (c)）。處理方式：T146-52／52b 比照 D-11 (a) 以 monkeypatch 把 `vg.prepare_target_env` 換成什麼都不做的函式（它們驗的是「隔離先於安裝」，不是準備環境；原斷言不變）；D-11 (b)、(c) 原樣搬到 `tests/test_verify_gates_core_copy.py`（本質上依賴上游已安裝的 `.venv-gates`／上游測試鎖定檔）；D-11 (a) 留在原檔。（Jeff 2026-10-20 約 16:06（美東），裁決助手記錄，非逐字原話）
- **S4f-2 完成（錨點 A6）**：`verify_gates.py` 的核心模式改為離線複製（`_core_source_venv`、共用的檔案選取 `_core_payload`、路徑元件語義的 `_within`、目的地 fail-closed 的 `_core_dest`、複製前的來源 upstream 身分檢查、seam 之外先完整性後 downstream 身分的 `_core_verify_target`）。結果：
  - `tests/test_verify_gates_core_copy.py` 8 passed；`tests/test_verify_gates.py` 47 passed；
  - **淨室首次端到端 exit 0**（`.venv-gates` 直譯器、離線）：R1～R10 各擋一次、權威層偵測正常、框架測試在新 repo 全綠（2652 passed, 14 skipped, 3 xfailed）、evidence policy 兩正三負成立；
  - 全套（`.venv-gates`）：4 failed（`tests/test_ci_workflow.py` 的 RT7／D-11 四條，留給 S4f-3）、2839 passed。
- **S4f-3 完成（錨點 A7）：S4f-乙、S4f-丙 已實作**：
  - `.github/workflows/tests.yml`：
    - `python-version` 釘 `'3.11.9'`（S4f-乙；註解寫明理由：bootstrap 例外是精確版本）；
    - 刪除 `pip install -e ".[dev]"`；
    - 在 `sh bootstrap.sh` 之前新增整合步驟 `id: gates-bootstrap-integration`（`setup_gates_env.py . --profile upstream`，再以 `.venv-gates/bin/python` 跑 `runtime_identity --whoami --profile upstream`；會連網）；
    - 跑測試、收集清單、淨室驗證三步改用 `.venv-gates/bin/python`。
    - `tests/test_ci_workflow.py` 14 passed（4 紅轉綠，既有 10 條仍綠）。
  - `docs/machine-init.md`（S4f-丙）：改了 0-1、0-2、前哨掛載指令兩處、③ 負控、二之一的 `bootstrap.sh` 前提與驗收直譯器、二之二 `-rs` 那行的直譯器、第三節新下游流程；`:985` 與 0-2 的使用者層 G1 那一行不動；舊文照 F-036 保留。
  - **出貨檔的裁定**：`docs/machine-init.md` 在 manifest 標 `copy`（會出貨），與原指示「改到出貨檔就停」衝突，S4f-3 因此在修改前停下。裁定：它是 S4f-丙 授權修改的檔，照改，改完必須重跑淨室；除此之外改到其他出貨檔仍要停。原指示互相衝突屬裁決助手的指示錯誤。（裁決助手 2026-10-20 約 16:52（美東），非 Jeff 逐字原話）
  - **淨室重跑**（改完 `machine-init.md` 之後，`.venv-gates` 直譯器、離線）：exit 0；框架測試在新 repo 2652 passed, 14 skipped, 3 xfailed；evidence policy 兩正三負成立。
  - 全套（`.venv-gates`）：**0 failed**、2843 passed。
  - **尚待 push 之後才能驗**：驗收 6「CI 綠燈（Jeff 目視）」，以及驗收 9 的「整合層（CI 網路 job）至少成功一次」。本站沒有連網、沒有 push。
- **S4f-4 push 與 CI**：
  - 10 筆提交 `f5815d3..e7604f4` 已推上 `origin/master`（一般 push；Jeff 2026-10-20 約 18:40（美東）授權，裁決助手記錄，非逐字原話）。
  - 推之前的守衛：fetch 後遠端仍是 `f5815d3`、ancestry 成立；10 筆 × Author／Committer 共 20 組，全是同一個公開身分（與 `origin/master` 那筆相同）；整段歷史只有 A／M（沒有 D／R），沒有 `.dev/`、`.venv-gates`、scratchpad、`*.whl`、快取或 log 等本機產物；`leak_scan.py`、`leak-patterns.txt`、`scanner.py` 在這段範圍內都沒有變動；最終 34 檔以既有的 `leak_scan.py <檔案…>` 補掃，exit 0、沒有命中（補掃依 Jeff 2026-10-20 約 18:51（美東）裁決，裁決助手記錄，非逐字原話）。
  - **CI 綠燈**：commit `e7604f4` 的那次執行，由 Jeff 2026-10-20 約 19:18（美東）目視確認（裁決助手記錄，非逐字原話）。本機沒有 `gh`，所以 CI 結果沒有在 session 內取得。
- **S4g-0 唯讀偵察（R10 資料來源）**：〔讀碼結論，見 `.dev/reports/2026-10-20-ticket156-s4g0.md` 1-4／1-5〕前哨不跑 R10（只在 `mode_pre_commit` 呼叫）；一般提交的 policy 讀 HEAD blob，工作樹與 HEAD 不同就 `worktree_differs` 硬擋；policy-only 提交（staged 全屬兩個 policy 檔）讀 index；`settings.json` 一律讀工作樹。所以縮回必須單獨一筆 policy-only 提交，而且它之前不得有其他提交與允許清單的未提交修改交錯。
- **S4g（錨點 A8）上游允許清單縮回完成**：`.agents/extension-allowlist.json` 的 `project_settings_hook_commands` 刪除裸 python 舊指令，只剩 gatepy 新指令（policy-only 提交）。
  - pre-commit 的 R10 訊息：`[R10/policy-only] policy-only commit（policy_source=index）：staged 候選 policy 對現場成立（DECLARED_OK；runtime 仍 UNPROVEN）。這是候選驗證，不是 HEAD 已生效的 policy。`
  - 核對方式（依 D-8「改在各站核對」，**不寫紅燈測試**，裁決助手判定）：對工作樹 `git grep -n -F 'python \"$CLAUDE_PROJECT_DIR/.claude/hooks/gate.py\"' -- .agents/extension-allowlist.json` 沒有輸出；同一 pattern 對縮回前的 `HEAD` 命中第 14 行（證明 pattern 有鑑別力）；Grep `^\s*"python ` 為 0；diff 只有 1 行刪除、0 行新增；`json.tool` 驗證通過。
  - 縮回後全套（`.venv-gates`）：0 failed、2843 passed。
- **S4g 裁決**（Jeff 2026-10-20 約 19:33（美東），裁決助手記錄，非逐字原話）：
  - **S4g-甲**：驗收 7（下游推廣）**移出本票，另開後續票**。後續票的範圍：兩個下游各自的 D10 七步、桌機唯讀偵察、驗收 3 的下游部分。以下三項也一併移入後續票：下游 gatepy 的 LF 保護（S4b′ 判定 B；S4g-0 報告第 3 節的 A／B／C 三案）、鎖定檔與允許清單的 `eol=lf`、金絲雀刪除。
  - **S4g-乙**：金絲雀 `<canary>` 先留著，不刪。
  - **S4g-丙**：`eol=lf` 照 `:168` 留給後續，本票不做。
- **裁決助手判定**（2026-10-20，非 Jeff 逐字原話）：
  - 縮回不寫紅燈測試，依 D-8（`:90`）改在各站核對（核對方式見上方 S4g）。
  - 驗收 3 的上游部分判為成立：CI 的「接上權威層」通過，而 `bootstrap.sh:100` 是經 gatepy 執行 `runtime_identity --whoami`（profile 依上游測試鎖定檔存在而為 upstream）；加上 S4e-1 探針 `identity: ok`（套件清單沒有 `taishi-shared`）。下游部分移入後續票。
  - 驗收 5 判為成立（等價形式）：S4e-1 探針證明前哨換成新前綴 `sh … gatepy …`、R7 照常擋、沒有 `[gatepy]` 錯誤；S4e-2 的 gate-B 證明全域 python 會被擋。`machine-init` 0-2「建 venv 前後翻面」的原形式不另做，因為那要刪掉上游的 `.venv-gates`。
  - 錨點：縮回為 A8；收票前紀錄為 C1。
- **觀察（留給後續，不在本票處理）**：
  - 鎖定檔與 `.agents/extension-allowlist.json` 會受 autocrlf 影響，`git add` 時提示 checkout 後會轉成 CRLF。〔讀碼推論〕pip、`runtime_identity`、R10 的 json 解析都不受影響。之後在合適的站點，比照 gatepy 一起釘成 `eol=lf`。
  - 已安裝的下游，允許清單在 manifest 標 skip，不會跟著更新。下游仍須逐 repo 照 D10「先擴後縮」處理。
  - 下游 gatepy 的 LF 保護（S4b′ 判定 B）仍待裁。

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
- **runtime-bootstrap 例外（D-4，暫定）**：`pip==24.0`、`setuptools==65.5.0`，以名稱＋精確版本登記（`setuptools 66.0` 不是例外）。來源是底座 3.11.9 的 `Lib/ensurepip/_bundled/` 檔名（〔讀碼推論〕，S3a 第 5 節）；實作站建出真的 `.venv-gates` 後觀測確認，觀測不同就停，不得擴大清單。
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
- `install.HOOK` 改用啟動器；`verify()` 與事前檢查依 D-10 直接用 target 的 `.venv-gates` 直譯器，不經 sh 或 gatepy
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
   - 已知範本要用**固定的 sha256** 來識別（每一版有自己的版本 ID）。程式和票面都要登記這張「版本 ID → sha256」對照表，不能只寫「舊裸 python 版」「本票新版」這種名稱。實際的 sha256 值在紅燈站產生範本後填入（見第七節）。S3b 已填入（LF 標準形、UTF-8、無 BOM，`sha256sum` 量得；fixture 在 `tests/fixtures/hooks/`）：

     | 版本 ID | sha256 | 內容 |
     |---|---|---|
     | `hook-v1-bare-python` | `eb6ee62cfb31803c26c3547822ba76b8104d111f759a960774d425a6b1f1c807` | 立案提交 `f5815d3` 的 `install.HOOK`（裸 python） |
     | `hook-v2-gatepy` | `091c0290f0e9c43441678f3c33391a31d8260c84764c9c86270e688fa1ccd83d` | 本票新版（經 gatepy，D-2 註解一行） |

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

### 10. 非原始碼目錄清單（D-1）

`.venv-gates` 裝的是第三方套件與直譯器（裡面就有與本 repo 同名的 `install.py`、`status.py`）。它要進三份實際參與掃描的跳過／忽略集合：

- `gate.NON_SOURCE_DIRS`（`is_source_path` 判 R2／R3 要不要管）
- `redlight._SEARCH_SKIP`（`find_implementation` 反查實作時 `os.walk` 要不要進去；不排除的話，紅燈紀錄的 `impl_hash` 會靜默記到 venv 裡的同名檔）
- `tests/test_source_hygiene.py` 的 `_H2_SKIP_DIRS`

`tests/test_non_source_list_parity.py` 的 `IN_BOTH` 同步加入（兩邊各自的判準都答「是」）。CLAUDE.md 常駐檢查項的兩問：會不會裝著判定邏輯 —— 不會；會不會裝著唯一的觀測 —— 不會。

---

## 四｜紅燈測試（先寫，並且要看到它們失敗）

- **RT1**：沒有 `.venv-gates` 時呼叫啟動器 → exit 2。PATH 上放一支假 `python`，存在的 `.venv` 也放假直譯器，兩者被呼叫都會留下記號檔；斷言兩個記號檔都**不存在**。
- **RT2**（G3、D-10）：只檢查四個會實際執行的入口。`settings.json`、`.githooks/pre-commit`、`install.HOOK` 沒有任何指令開頭是裸 `python`；`install.verify()` 執行 gate 的直譯器是 `<target>/.venv-gates` 那一支（不是 `"python"`、不是 `sys.executable`），而且**不經 sh 或 gatepy**。允許清單不在 RT2 範圍內，改由第五節的遷移狀態驗收。
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
- **S3b 補入的對應紅燈**（實際測試名稱）：
  - D-1：
    - `tests/test_redlight.py::TestT156FindImplementationSkipsVenvGates::test_a_venv_only_match_is_not_an_implementation`（E2 負案例：tmp root 只有 `.venv-gates/Lib/site-packages/x/install.py` ⇒ 必須回 None；現況回 venv 那一份）
    - `tests/test_redlight.py::TestT156FindImplementationSkipsVenvGates::test_venv_gates_is_in_the_search_skip_set`
    - `tests/test_gate.py::TestT156VenvGatesIsNotSource::test_venv_gates_is_listed`、`::test_a_file_under_venv_gates_is_not_source`
    - `tests/test_non_source_list_parity.py::TestTheDifferenceIsExactlyWhatWasDecided::test_the_overlap_is_exactly_the_listed_thirteen`、`::test_the_whole_partition_agrees_at_once`（`IN_BOTH` 加入 `.venv-gates` 後轉紅）
    - 對照（現況即綠，不作紅燈證據）：`tests/test_redlight.py::TestT156FindImplementationSkipsVenvGates::test_the_project_file_wins_over_a_venv_copy`
  - D-9：`tests/test_bootstrap.py::TestT156D9BootstrapVerifiesTheGatesEnvironment::test_d9_a_missing_venv_gates_interpreter_is_refused`、`::test_d9_a_failing_whoami_is_refused`
  - D-11（離線核心）：`tests/test_verify_gates.py::TestT156D11OfflineCore::test_d11_a_setup_runs_before_install`、`tests/test_verify_gates_core_copy.py::TestT156D11OfflineCoreUpstream::test_d11_b_the_core_mode_never_runs_the_real_install_or_touches_the_network`、`::test_d11_c_the_pos2_policy_uses_the_upstream_profile_set`（(b)、(c) 原在 `tests/test_verify_gates.py::TestT156D11OfflineCore`，S4f-丁之二搬到不出貨的新檔）
  - D-11（整合層）：`tests/test_ci_workflow.py::test_d11_a_labelled_integration_step_really_bootstraps_from_the_locks`、`::test_d11_the_integration_step_is_separate_from_core_verify_gates`（步驟 `id: gates-bootstrap-integration`）

---

## 五｜驗收

1. 上游全套測試在 `.venv-gates` 裡全綠。
2. `verify_gates` 綠燈，正二情境綠燈，而且政策裡的版本＝上游 profile 的預期集合。
3. 經 gatepy 執行 `runtime_identity.py --whoami`（D-3）：
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
9. 新下游的 bootstrap 流程（G4，第三節第 8 條的六步）至少走通一次。可以用金絲雀，或用測試裡的乾淨 target 證明。並且由整合層（CI 網路 job 或經 Jeff 授權的本機執行）至少成功一次（D-11）。

一般 `verify_gates` 必須能離線綠燈（D-11）。

### 驗收最終狀態（C1，2026-10-20；上方原條文不改）

| 驗收 | 狀態 | 依據 |
|---|---|---|
| 1 上游全套在 `.venv-gates` 全綠 | 成立 | S4f-3 全套 0 failed、2843 passed（A7）；S4g 縮回後同樣 0 failed、2843 passed；CI 綠燈 |
| 2 verify_gates 綠、正二綠、政策版本＝上游 profile | 成立 | S4f-2／S4f-3 淨室 exit 0，「正二 已初始化且相符 成立」；`test_d11_c_*` 上游綠 |
| 3 經 gatepy 的 `--whoami` | **部分成立／本票範圍完成** | 上游部分已成立（依據見上方「裁決助手判定」）；原下游部分依 S4g-甲 移入後續票，不再作為票 156 的收票阻塞條件 |
| 4 金絲雀取證成功 | 成立 | S4c′（`:126`）U-a 已證明 |
| 5 探針訊息翻面 | 成立（等價形式，裁決助手判定） | S4e-1 探針（前哨新前綴、R7 照常擋、沒有 `[gatepy]` 錯誤）與 S4e-2 gate-B；原形式要刪上游 `.venv-gates`，不另做 |
| 6 CI 綠燈（Jeff 目視） | 成立 | Jeff 2026-10-20 約 19:18（美東）目視確認 `e7604f4` 的那次執行 |
| 7 下游 | **移出本票，待後續票立案**（不是成立） | S4g-甲 |
| 8 允許清單遷移狀態 | 成立 | 擴張＝新加舊（A3）；縮回後只剩新、裸 python 舊指令不存在（A8） |
| 9 G4 bootstrap 走通一次＋整合層至少成功一次 | 成立 | 淨室的乾淨 target 走通 setup → install（S4f-2／S4f-3）；CI 綠燈 ⇒ 整合步驟 `gates-bootstrap-integration` 成功（裁決助手判定：job 的各 step 依序執行，任一步失敗整次就紅） |
| （附）一般 verify_gates 離線綠燈 | 成立 | S4f-2／S4f-3 淨室離線 exit 0 |

**移入後續票的事項**（S4g-甲；後續票待立案）：兩個下游（`meetingbridge`、`serenity-research`）各自的 D10 七步；桌機唯讀偵察；驗收 3 的下游部分；下游 gatepy 的 LF 保護（S4b′ 判定 B，A／B／C 三案）；鎖定檔與允許清單的 `eol=lf`；金絲雀刪除（S4g-乙：在此之前先留著）。

### 範圍調整紀錄

- 驗收 3 的下游部分、驗收 7 全項，依 **S4g-甲** 移出本票，另開後續票（Jeff 2026-10-20 約 19:33（美東），裁決助手記錄，非逐字原話）。上方驗收原條文保留原文，不刪不改；本票的收票判定以「驗收最終狀態」表為準。

### 收票裁決（C2，2026-10-20）

- **收票**：票 156 **限定範圍結案**（範圍：上游）。（Jeff 2026-10-20 約 19:51（美東），裁決助手記錄，非逐字原話）
- **收票順序：裁決 A（證據先於宣告）**：先 push A8＋C1，Jeff 目視那次 CI 綠燈之後，才形成收票提交 C2。（Jeff 2026-10-20 約 19:53（美東），裁決助手記錄，非逐字原話）
- **線上驗證**：
  - `e46d860`（含 A8 縮回）的 CI 綠燈：All checks have passed，耗時 3 分 4 秒。（Jeff 2026-10-20 約 20:01（美東）目視，裁決助手記錄，非逐字原話）
  - `e7604f4`（A7）的 CI 綠燈。（Jeff 2026-10-20 約 19:18（美東）目視，裁決助手記錄，非逐字原話）
  - 本機沒有 `gh`，CI 結果沒有在 session 內獨立取得。
- **依據**：上方「驗收最終狀態」表（C1）；錨點 A1～A8 與 C1。
- **移入後續票的事項**：見上方「移入後續票的事項」與「範圍調整紀錄」（C1），這裡不重寫；後續票待立案。
- 「AI 正式執行管道」的恢復（`:5`），以及 `.dev/pipeline.json` 的處理，由 Jeff 處理。

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

- 例外清單暫定（D-4），實作站觀測確認；sha256 已填（第三節第 7 條第 6 點）。
- U-a（hook 的 shell）：~~目前「高度支持 bash，但未證明」，等金絲雀取證。~~ **已由 S4c′ 金絲雀證明**（`:126`；C1 更新）。
- 桌機的 Python 版本、桌機上 agent-gates 的副本位置、兩個下游目前的 hook 長什麼樣子：等桌機偵察。
- manifest 分類與換行正規化已由 G1、G2 裁定，見第二節。
- 下游在 Windows 上的工作區實際是不是 CRLF，仍然要在桌機偵察時觀測（G2 只解決了比對規則）。依據：上游的 `.githooks/pre-commit` 由上游的 `.gitattributes` 釘成 LF（觀測：`git ls-files --eol` → `i/lf w/lf attr/text eol=lf`），但 `.gitattributes` 在 manifest 標 skip（`:71`；`:60-61`），不隨安裝走；票 154 曾觀測到 `git restore` 之後工作區變 CRLF 的現象（票 154 第四節之三）。另外要觀測 CRLF 的 hook 能不能被 Git Bash 正常執行（F0c (a)：與所有權判定分開）。
- 上游自己的 `.githooks/pre-commit` 跟 `install.HOOK` 不一樣（上游多了 `:4-16` 的註解段；觀測）。這不影響 `--rehook`：上游直接提交新 hook（第三節第 8 條第 5 步），不走 `--rehook`；`--rehook` 的已知範本只需涵蓋安裝器產生的那幾版。

---

## 修正紀錄

- 立案草稿（2026-10-19，裁決助手記錄，非逐字原話）：依 R0／R1 偵察（當時暫用票號 155）與 Jeff 2026-10-19 14:40～16:45 的裁決起草。上一版 F0 因票號衝突在步驟 0 停下，見〔F0 停止〕。
- G1～G4 補入（2026-10-19，裁決助手記錄，非逐字原話）；設計契約封版。
- F0c (a)(b)(c) 補入；票面封版（2026-10-19，裁決助手記錄，非逐字原話）。
- S3b 紅燈與 D-1～D-11 補入（2026-10-19，裁決助手記錄，非逐字原話）。
- S4a 裁決（D-S4-1～8）與 S4b 裁決（甲案兩處、帳本 append-only、`install_step` 參數、gatepy 只用 `-f`、S4f 待裁）補入；S4b 離線實作（錨點 A1）（2026-10-20，裁決助手記錄，非逐字原話）。
- S4b′ 裁決（bootstrap profile 慣例非安全邊界、gatepy LF 持久化、下游判定 B 待裁）補入；`.gitattributes` 加 `.claude/bin/gatepy text eol=lf`（錨點 A1′）（2026-10-20，裁決助手記錄，非逐字原話）。
- S4c：S2a 個案裁決（cryptography `python_full_version` 邊）、鎖定檔純 ASCII 約束（甲′）與其測試、兩份帶 hash 的鎖定檔、上游 `.venv-gates` 建立與 D-4 實測補入（錨點 A2）（2026-10-20，裁決助手記錄，非逐字原話）。
- S4c′ U-a 取證結果、S4d（錨點 A3，policy-only）與 D2 改法、S4e-1 正式 hook 改走 gatepy（保留上游 hook 歷史註解）與後續觀察補入（錨點 A4）（2026-10-20，裁決助手記錄，非逐字原話）。
- S4e-1 探針結果、S4e-2 gate-B 便宜身分檢查接上 `__main__`、T146-59／60／60b 改用 target `.venv-gates`、全域 Python 不再能救援補入（錨點 A5）（Jeff 2026-10-20，裁決助手記錄，非逐字原話）。
- S4f 裁決（S4f-甲 方案 (d)、S4f-乙 CI 釘 3.11.9、S4f-丙 machine-init 範圍）與 R-3 判讀補入；`:106` 改指 S4f-甲；(d) 紅燈六條（錨點 A6-紅）（Jeff 2026-10-20 約 13:53（美東），裁決助手記錄，非逐字原話）。
- S4f-丁（紅燈移到不出貨的 `tests/test_verify_gates_core_copy.py`）、S4f-1 偏離裁定、S4f-丁之二（淨室 4 紅：T146-52／52b 換掉 `prepare_target_env`，D-11 (b)(c) 移檔）、S4f-2 (d) 實作與淨室首次端到端 exit 0 補入（錨點 A6）（Jeff 2026-10-20 約 15:31／16:06（美東），裁決助手記錄，非逐字原話）。
- S4f-3：CI 改走 `.venv-gates`（整合步驟 `gates-bootstrap-integration`、釘 3.11.9、移除 `pip install -e`）、`machine-init.md` 更新、出貨檔裁定（16:52）與淨室重跑結果補入；驗收 6、9 待 push 後驗（錨點 A7）（2026-10-20，裁決助手記錄，非逐字原話）。
- S4f-4 push 與 CI 綠燈、S4g-0 R10 資料來源結論、S4g 允許清單縮回（錨點 A8）、S4g-甲／乙／丙 裁決與裁決助手判定、驗收最終狀態表與範圍調整紀錄、未決 U-a 更新（錨點 C1）（Jeff 2026-10-20 約 18:40／18:51／19:18／19:33（美東），裁決助手記錄，非逐字原話）。
- 收票（錨點 C2）：狀態列改為「已結案（限定範圍：上游）」，舊狀態以刪除線保留；新增「收票裁決」一節（收票 19:51、順序裁決 A 19:53、`e46d860` CI 綠燈 20:01 目視）（Jeff 2026-10-20 約 19:51／19:53／20:01（美東），裁決助手記錄，非逐字原話）。
