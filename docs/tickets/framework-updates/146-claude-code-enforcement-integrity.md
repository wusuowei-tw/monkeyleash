# 票 146 —— Claude Code Enforcement Integrity

**狀態**:立案 —— 第三站紅燈補完中(3b-146);尚未實作
~~**狀態**:第三站紅燈已提交(S3-146-1);待第四站實作~~(F-036 體例:舊行不刪)—— 2026-10-06 契約增補 3b 入票時更新:4-146 暫緩,第三站契約漏掃 ~/.claude/skills 與 ~/.claude/commands,先補紅燈(裁決 (a))。
~~**狀態**:立案 —— 設計 v0 + Q1–Q6 已裁;進入第三站紅燈~~(F-036 體例:舊行不刪)—— 2026-10-06 第三站紅燈提交時更新:S3-146-1 已提交、已證紅。
~~**狀態**:立案 —— 設計 v0 已產出(2026-10-06T144009Z-ticket146-design-v0.md);待審~~(F-036 體例:舊行不刪)—— 2026-10-06 Q1–Q6 裁決入票時更新:設計 v0 已審、Q1–Q6 已裁。
~~**狀態**:立案 —— 第一步唯讀盤點已完成(2026-10-04 報告 2026-10-04T124314Z-ticket146-step1-inventory.md / 2026-10-04T130149Z-ticket146-step1-closeout.md,於 Claude Code 2.1.289 執行;門檻 ≥ 2.1.287 已滿足);可進入設計。~~(F-036 體例:舊行不刪)—— 2026-10-06 設計 v0 產出時更新:已進入設計。
~~**狀態**:**candidate。只登記。** 第一步**必須等升級之後才做**(見〈第一步〉)。~~(F-036 體例:舊行不刪)—— 2026-10-06 立案 commit 時更新:升級前提已於 10/4 滿足。
**優先度**:**未定。**
**發現於**:2026-10-04,monkeyleash-mod V0 唯讀偵察(裁決:V0 = NO-GO)。
**來源**:`F-166`。
**報告**:`.dev/reports/2026-10-04T110800Z-mods-v0-recon.md`
(⚠ `.dev/` 不進版控,只在本機 ⇒ 判定依據的官方原文抄在 `F-166`)。

---

## 目標

**任何 Claude Code 擴充機制都不能靜默削弱 agent-gates。**

「靜默」是這個目標的重點:削弱本身未必擋得住
(使用者有權裝 mod、有權開 `--safe-mode`),**但它不准不出聲。**

---

## 範圍 —— **寫死成已知機制清單**

| # | 機制 | 為什麼在清單上 |
|---|---|---|
| 1 | **hooks**(settings hooks:user / project / local / managed、plugin 的 `hooks/hooks.json`) | gate.py 前哨本身就是其中一個;其他 hook 和它跑在同一條鏈上 |
| 2 | **mods**(含官方內建 `cc-plugin-*`) | `F-166`:可以跳過或推翻 `PreToolUse` |
| 3 | **plugins** | mods 的載體;也能帶 hooks、MCP servers |
| 4 | **MCP servers** | 帶工具進 session;工具呼叫一樣走 `tool.call` / `PreToolUse` |

**擴充規則:新機制出現時,在上表加一行。**
**不做泛用的「未知偵測」** —— 那是開放集合上的比對,漏洞是未知的;
在已知清單上做枚舉,漏洞是不存在的(CLAUDE.md〈封閉集合〉那條)。
清單會過期,但**過期的時候會被看到**(上游文件出現新名詞,而表上沒有)——
泛用偵測過期的時候不會被看到。

---

## 第一步(**升級之後才做,唯讀**)

**前提**:`claude --version` 必須 **≥ 2.1.287**(Mods 的最低版本,overview.md:
"Mods require Claude Code v2.1.287 or later, and they're on by default.")。

**⚠ 在 2.1.282 下做的觀察一律不算數。** 2026-10-04 偵察時,
VS Code 視窗跑的是 **2.1.282**(`CLAUDE_CODE_EXECPATH` 指向
`anthropic.claude-code-2.1.282-win32-x64`),而 2.1.287 只是已經下載、尚未啟用。
在不支援 mods 的版本上量到「0 個 mod」,**證明不了任何事**。

要做的事:

1. 記下 `claude --version` 的原始輸出,以及**本 session 實際在跑的執行檔路徑**
   (`CLAUDE_CODE_EXECPATH`)。兩者都要記,因為兩者可以不同(10/4 那次就不同)。
2. 列出**實際載入**的項目,按上表四類各列一份:
   - mods:**含官方內建**(`/plugin` → Installed → Built-in;另有 `mods active` 那一行,但它**不列內建**)
   - hooks:每個 settings 來源各自列
   - plugins
   - MCP servers
3. 存成證據**附回本票**(原始輸出逐字抄進來,不只放 `.dev/`)。

**「實際載入」與「設定檔裡寫了」是兩件事。** 要量的是前者;
後者只能當成交叉比對的材料。

---

## 之後才設計(**第一步做完之前不動**)

- **白名單**:哪些擴充可以出現在安裝了 agent-gates 的 session 裡。
- **接進 `status` 的 Enforcement Health**:一段專門回答
  「這個 session 有沒有東西排在 gate.py 前面或後面」。
- **紅燈測試**:**出現未授權的擴充 → FAIL。**
  (形狀先記在這裡:在 fixture 裡放一個登記了 `tool.call` 或 `tool.check` 的假 mod,
  斷言 Enforcement Health 判 FAIL,而且訊息會點名它。)

---

## ⛔ 禁止的對策

**不得以 `disableAllHooks` 當作對策。**

schema(2.1.287 `claude-code-settings.schema.json:815-817`)的描述是:
> "Disable all hooks and statusLine execution: the hooks defined in settings files and by installed plugins."

⇒ **疑會連帶關掉 gate.py 前哨本身**(gate.py 就是 settings 裡定義的 hook)。
**未實測證實之前,一律視為危險。** 同理也適用 `--safe-mode`、`--bare`
(help 文字都寫明會停用 hooks)。

---

## 與既有票 / 條目的關係

| 號 | 關係 |
|---|---|
| `F-166` | 本票的來源 |
| 票 147 | **不同生命週期**(Stop),分開處理;本票不涵蓋收工檢查 |
| ADR 0008 | R7 只活在前哨的那份裁決 —— 本票要保護的就是它所依賴的前提 |

---

## 第一步證據(2026-10-04T124314Z,VS Code 擴充套件 session,唯讀)

### 版本前提 —— **成立**

```
EXECPATH=C:\Users\<使用者>\.vscode\extensions\anthropic.claude-code-2.1.289-win32-x64\resources\native-binary\claude.exe
SDK=0.3.289
ENTRY=claude-vscode
SAFE= SIMPLE=
2.1.289 (Claude Code)
EXIT=0
```

⇒ **執行中的**執行檔就是 2.1.289(≥ 2.1.287)。`CLAUDE_CODE_SAFE_MODE`、`CLAUDE_CODE_SIMPLE` 都沒有設。

### 四類盤點

| # | 機制 | 觀測 | 來源 | 判定 |
|---|---|---|---|---|
| 1 | hooks:user | `PreToolUse`,matcher `Bash\|PowerShell\|Write\|Edit\|MultiEdit\|NotebookEdit` → `python "C:/Users/<使用者>/.claude/hooks/g1_guard.py"` | `~/.claude/settings.json:3-15` | 設定檔裡有登記(G1) |
| 1 | hooks:project | `PreToolUse`,matcher `Write\|Edit\|MultiEdit\|NotebookEdit\|Bash\|PowerShell` → `python "$CLAUDE_PROJECT_DIR/.claude/hooks/gate.py"` | `.claude/settings.json:2-14` | 設定檔裡有登記(gate.py 前哨) |
| 1 | hooks:local | 沒有 `.claude/settings.local.json` | Glob `.claude/settings*.json` → 只有 `.claude\settings.json` | 無 |
| 1 | hooks:managed | `C:\ProgramData\ClaudeCode` False;`C:\Program Files\ClaudeCode` False;`HKLM:\SOFTWARE\Policies\ClaudeCode` ItemNotFoundException;`HKCU:\SOFTWARE\Policies\ClaudeCode` ItemNotFoundException | PowerShell `Test-Path` / `Get-ItemProperty` | 這台機器**沒有 managed settings** |
| 2 | mods:使用者安裝 | `claude plugin list --json` → `[]`;文字版 → `No plugins installed. Use \`claude plugin install\` to install a plugin.` | 2.1.289 CLI,EXIT=0 | 0 |
| 2 | mods:官方內建 | 見下方〈內建 mod〉 | — | **部分 UNKNOWN** |
| 3 | plugins | 同第 2 列(`plugin list` 回 `[]`) | 同上 | 0 個已安裝 |
| 4 | MCP:Claude Code 設定 | `~/.claude.json:1423` `"c:/projects/agent-gates": {` → `:1426` `"mcpServers": {},`;全檔 `mcpServers` 只有這一處;repo 根目錄沒有 `.mcp.json` | Grep | 沒有設定任何 server |
| 4 | MCP:本 session 實際連線 | `claude.ai Claude Docs`(claude.ai connector)、`claude-vscode`(IDE 整合,工具 `getDiagnostics`) | 本 session 的系統提示 / 工具清單 | **實際載入 2 個**,兩個都不是設定檔登記的 |

### 內建 mod

| 名稱 | 載入了嗎 | 依據 |
|---|---|---|
| `cc-plugin-plugin-authoring` | **是(有觀測)** | 升級後的 session 出現 skill `plugin-authoring`("Make a mod … Load before writing or debugging a hooks module.");2.1.282 下的 session 沒有這個 skill |
| `cc-plugin-agents-md` | UNKNOWN | 文件寫「Every session, apart from the ones that can't read `AGENTS.md`」,但**沒有觀測** |
| `cc-plugin-diff` | UNKNOWN | 文件寫「Interactive terminal sessions」;本 session 是 VS Code 面板 |
| `cc-plugin-telemetry` | UNKNOWN | 文件寫「Wherever Claude Code's own analytics are on」 |
| `cc-plugin-sec-default` | UNKNOWN | 載入條件是「有 managed settings,**或**以 Team/Enterprise 方案登入」;前者確定沒有,後者**未查** |
| `cc-plugin-you-should-know` | UNKNOWN | 文件寫「Disabled by default」 |

### 沒有做 / 做不到的(照列)

- **`claude mcp list` 沒有跑**:help 寫 "approved servers are health-checked",也就是會把 server 啟動起來,不算唯讀。
- **沒有 debug log**:`~/.claude/debug` 不存在(本 session 沒開 debug)。
- **「實際載入的內建 mod」從 agent 這一側量不到**:官方的觀測入口是 `/plugin` → **Installed** → **Built-in**,是互動式畫面。
  ⇒ 剩下 5 個 UNKNOWN,需要**人**在 `/plugin` 看一次,把畫面原文貼回來。
- **hooks 那幾列是「設定檔裡有登記」,不是「實際有執行」**:本輪沒有觸發 gate.py / g1_guard.py 去證明它們真的會跑。

### 這份證據對設計的直接含意(**只記,不設計**)

- **使用者安裝的 mod 目前是 0 個** ⇒ `F-166` 那條路徑**現在是空的**,但 v2.1.287 起 mods 預設開啟,**入口是開的**。
- **沒有 managed settings** ⇒ 依 permissions.md,deny rules 擋不擋得住 mod 取決於帳號方案:
  "on a machine with managed settings, or when you're signed in with a Team or Enterprise plan, deny rules hold over the mod by default … **Anywhere else, the mod can approve a call that a deny rule refuses.**"
  ⇒ 方案要查,而且要記進白名單設計的前提。
- **MCP 實際連上 2 個,設定檔裡卻是 0 個** ⇒ 「看設定檔」量不到 MCP。
  Enforcement Health 若要涵蓋 MCP,**資料來源不能只靠設定檔** —— 這正是第一步要求「實際載入」而不是「設定檔寫了」的理由,而且它這一次真的發生了。

---

## 第一步收尾(2026-10-04T130149Z,裁決 A)

### 一、VS Code surface 的矛盾 —— 記錄,不追查

| 來源 | 說法 |
|---|---|
| 型別檔 `bundled-skills/2.1.289/…/plugin-authoring/types/claude-code.d.ts`(第 1 行 `// Written by Claude Code 2.1.289.`) | `:9837` `export type RenderSurface = 'terminal' \| 'desktop' \| 'mobile' \| 'vscode';`;`:9829-9832` "`vscode` Claude Code for VS Code. A remote surface … draws the tree where it has a slot for it." |
| 官方文件 overview.md〈Where mods run〉 | "The VS Code extension's chat panel \| Hooks run: Yes \| What the mod draws appears: No" |
| 官方文件 reference.md(開頭 "as of v2.1.289") | render sites 表的「Rendered on」欄只有 Terminal / Desktop |

**判讀**:**規格允許 ≠ 面板已經有 slot。** VS Code 面板實際會顯示什麼 = **UNKNOWN,不追查。**

**V0 = NO-GO 維持。** 這個結論由**理由二**(Mods 沒有獨有的執行前控制:`tool.call {deny}` 與既有 PreToolUse→gate.py 是同一種能力)**單獨成立**,不依賴理由一。

### 二、更正上一份報告

`.dev/reports/2026-10-04T125500Z-vscode-surface-premise-check.md` 第一段第 5 點寫
「NO-GO 的前提一是建立在一份比型別檔還舊的文件上」—— **不成立**。
reference.md 開頭標的就是 "as of v2.1.289",它的 render sites 表也不列 VS Code;它與型別檔**標的是同一個版本**。
(精確地說:「面板不顯示」這句原文出自 overview.md,而 overview.md 沒有標版本;
但同一份文件集裡標了 2.1.289 的 reference.md 與它一致。)
那份報告的第二段其實引用過 reference.md 的 "as of v2.1.289",**第一段卻沒有和第二段對齊** ——
這是第一段寫出了第二段不支持的話。

### 三、人工查證(Jeff,2026-10-04)

| 入口 | 結果 |
|---|---|
| VS Code 面板輸入 `/plugin` | 被自動補成 `/plugin-authoring`,**打不開 Installed 清單**(上一輪的 `/plugin-authoring` 就是這樣被叫出來的) |
| Claude Desktop「Settings → Plugins」 | 顯示「Add your first plugins」(沒有已安裝的外掛);In this project 沒有選資料夾;**這一頁不列 Built-in 段** |

**結論**:
- 使用者安裝的 plugin = 0,**多了一份獨立證據**(與 `claude plugin list --json` → `[]` 的來源不同:一個是 CLI,一個是 Desktop UI,加上人的眼睛)。
- 內建 mod 清單:**兩個人工入口都列不出來。**

### 四、帳號方案

**非 Team / Enterprise 的個人方案。** 本機也沒有 managed settings(見第一步證據)。

⇒ 依 reference.md / overview.md,`sec-default@builtin` 只在「有 managed settings,或以 Team/Enterprise 方案登入」時載入 ⇒ **官方的 `sec-default` 守衛不會優先載入。**
⇒ 依 permissions.md,"Anywhere else, the mod can approve a call that a deny rule refuses." ⇒ **F-166 在本機是真實風險;目前只是因為使用者安裝的 mod = 0,還沒有被利用。**

### 五、內建 mod 狀態更新

第一步證據表裡 5 個 UNKNOWN(`cc-plugin-agents-md`、`cc-plugin-diff`、`cc-plugin-telemetry`、`cc-plugin-sec-default`、`cc-plugin-you-should-know`)
**改標為「待補(VS Code 面板與 Desktop 都列不出來)」**。原表不動,以本節為準。
`cc-plugin-sec-default` 依第四點,**推定不載入**(條件不符),但仍屬推定、沒有觀測。

**這不阻擋進入設計。** 但設計必須:
- 把「**內建 mod 清單不完整**」列為**已知限制**;
- 要求檢查器**自己**列出實際載入的內建 mod(**若 API 做得到**),不依賴人去看畫面。能不能做到,是設計階段第一個要查證的問題。

### 六、設計要求(新增)

**檢查器以「實際載入 / 實際連線」為準,不得只讀設定檔。**
依據:本票第一步實測,MCP 在 Claude Code 設定檔裡是 **0 個**(`~/.claude.json:1426` `"mcpServers": {},`;沒有 `.mcp.json`),
實際連線的卻是 **2 個**(`claude.ai Claude Docs`、`claude-vscode`)。

設計要求（新增，2026-10-06 補 10/4 第 4 項）：監看 ~/.claude/dev-mods/。符合 Claude Code dev-mod 載入條件、卻不在 allowlist 上的項目 → FAIL。若目前無法可靠判斷哪些項目可載入，第一版採 fail-closed：目錄非空 → FAIL，並明確標記為暫時的保守策略。依據：/plugin-authoring 說明「The first file written there makes the engine ask the person… On Enable for this session the folder joins the session's plugin folders」（存檔即 hot reload）；2.1.289 已建立 ~/.claude/dev-mods/<id>/（10/4 觀察為空目錄）。

### 七、本票狀態

第一步**完成**(帶已知限制:5 個內建 mod 待補)。**可以進入設計**(白名單 → Enforcement Health → 紅燈測試「未授權擴充 → FAIL」)。
設計時沿用的禁令不變:**不得以 `disableAllHooks` 當作對策。**

---

## 設計 v0(2026-10-06,D-146-0)

**狀態:設計 v0 已產出,待 Jeff/GPT 審;尚未進第三站。**

**設計報告**:`.dev/reports/2026-10-06T144009Z-ticket146-design-v0.md`(本機證據,**不在 git 內**)。

### 裁決(Jeff,2026-10-06 10:32 美東;逐字)

1 加：新發現的 5 條管道 —— ~/.claude/skills、專案 .claude/skills、CLAUDE_CODE_PLUGIN_DIRS、synced/、~/.claude/commands —— 全部納入 mechanism inventory；各自標 Declared / Discoverable / Loaded UNKNOWN / Trustworthy UNKNOWN 的實際能力邊界。
2 停在可證明的靜態 enforcement boundary；runtime observer 另開票、登記不排程。狀態至少分 VIOLATION、DECLARED_OK / RUNTIME_UNKNOWN、VERIFIED（目前不可達）。靜態乾淨不得顯示單獨的 PASS、有效 或 runtime verified。
3 否：不採 mod 監看 mod；正式記為 capability limitation。
4 repo allowlist：沿用 145 的 authority 模式 —— policy 只認 HEAD committed blob；worktree 只做 identity check；missing / uncommitted / dirty / identity mismatch ⇒ UNKNOWN / fail-closed；agent 修改工作樹 allowlist 不得立即把自己洗白。
5 dev-mods：空目錄／只有目錄 ⇒ OK；candidate file 的判準依官方 loader contract；不自行寫死 .js/.ts/.mjs；loader 可接受格式若無法完整證明，第一版保守把任何 regular file 視為 candidate，須符合 allowlist。
6 .claude/skills：列入，但擴充既有 R4（gate.py skill_mirror_violations），不另造第二套。symlink mirror 延續既有「不得斷鏈、不得指向 canonical 外」；實體 mirror directory 由目前只比 SKILL.md 升級成 canonical 與 mirror 的遞迴 tree parity / content identity；canonical 有的合法輔助檔可以存在但內容必須對得上；mirror 多出 canonical 沒有的 regular file ⇒ VIOLATION；mirror 缺 canonical 必要檔、內容 hash 不同 ⇒ VIOLATION；不採「凡非 SKILL.md 一律違規」。
+ UI/status：known static surfaces clean 與 runtime loaded set UNKNOWN 必須分欄呈現，不准用一個「有效」把兩者混在一起。

### Invariant(逐字)

146 可以證明「所有已知靜態載入入口符合 committed policy」，但在沒有獨立 runtime authority source 前，不得把這件事升格成「本 session 實際載入集合已驗證」。

---

## 設計決策 Q1–Q6(2026-10-06)

### 裁決(Jeff,2026-10-06;逐字)

Q1：共享 read-only facts layer，由 gate/status 共用；不靠 gate 產出的殘留摘要。若需碰 ~/.claude/，正式修訂 capability boundary（status.py:36），不偷繞。
Q2：synced/ 不直接判 VIOLATION，但在未有 committed policy 前屬 unmanaged/UNKNOWN，不能算 static clean。
Q3：IDE lock 只顯示，不判定。
Q4：前哨只警告；pre-commit fail-closed；status 必須顯示。
Q5：agent 可算 hash/產 diff，但 policy 生效 commit 必須 Jeff 明確核准；目前是 procedural invariant，尚未 machine-enforced；另票候選「policy-approval provenance」。
Q6：保留 fingerprint 模型；v0 讓 dev_mod_files=[]，所以任何 regular file 都因未登記而 VIOLATION，而不是另寫一條永久「非空即違規」語意。
附：T146-7 的禁詞掃描必須限定 146 的 status 區段，不得因 145 的 POLICY_VALID="有效" 誤殺；mcp__ 前綴不可作 provenance 證據 —— 列為 known limitation，不做成測試（v0 沒有 provenance API，不硬生一個）。

### 狀態機(依 Q2,四態)

EXT_VIOLATION：policy authority 任一步失敗、或監看路徑有未登記項目、或 R4 非空。
EXT_UNKNOWN：policy 與受管路徑都乾淨，但存在未受管的已知載入入口（v0：synced/ 任一目錄含 regular file）。
EXT_DECLARED_OK：policy 四步通過、受管路徑全符合、R4 為空、synced/ 無 regular file。runtime 欄仍固定「未證明」。
EXT_VERIFIED：常數存在，無任何回傳路徑（v0 以行為測試 + 結構性 regression lock 鎖住，不宣稱形式證明）。
優先序：VIOLATION > UNKNOWN > DECLARED_OK。

### v0 介面契約(第四站只能實作,不能改名;要改名須回本票記一筆)

放在 .claude/hooks/redlight.py：
  EXT_ALLOWLIST_FILE = ".agents/extension-allowlist.json"
  EXT_ALLOWLIST_SCHEMA = "monkeyleash.extension-allowlist"，版本 1
  EXT_ALLOWLIST_FIELDS = ("schema","version","dev_mod_files","user_skill_plugins","user_commands","project_settings_hook_commands","mcp_json_servers")
  EXT_VIOLATION、EXT_UNKNOWN、EXT_DECLARED_OK、EXT_VERIFIED 四個字串常數，值 "VIOLATION"、"UNKNOWN"、"DECLARED_OK"、"VERIFIED"
  extension_allowlist_facts(root) → dict，至少含 "state"（"uninitialized" / "uncommitted" / "worktree_differs" / "identity_mismatch" / "malformed" / "ok"）、"blob"、"policy"。流程與 145 的 evidence_policy_facts 相同：只認 HEAD blob，工作樹只做一次 hash-object 比對。
  extension_state(facts, surfaces) → 四常數之一。
  extension_status_lines(facts, surfaces) → list，恰好兩個字串，第一個以 "static surfaces: " 開頭，第二個以 "runtime loaded set: " 開頭且含「未證明」。
放在「共用唯讀 facts 模組」：
  extension_surface_facts(dev_mods_dir, synced_dirs, canon_dir, mirror_dirs, project_settings_paths, mcp_json_path) → surfaces dict：{"dev_mod_files": [(relpath, sha256 或 None), ...], "synced_files": [relpath, ...], "r4_violations": [str, ...], "project_hook_commands": [str, ...], "mcp_json_servers": [str, ...]}。純讀、無副作用、所有路徑由參數注入；symlink 以 (relpath, None) 標為不可信。
  要求：gate.py 與 status.py 都能直接 import 該模組取得這個函式，呼叫時現場計算，不讀任何 cache 或前一次 pre-commit 的產物。
gate.py：skill_mirror_violations 簽名不變，實體副本分支改為遞迴 tree parity。

**「共用唯讀 facts 模組」的落點 = `.claude/hooks/redlight.py`**(第三站步驟 0d 判定)。依據:
3b:方向 B,R4 primitive 下沉 redlight.py,見〈契約增補 3b〉
- `gate.py` → `redlight.py`:`gate.py:2051-2065` `_redlight()` 以 `spec_from_file_location` 依路徑載入同目錄的 `redlight.py`(呼叫點 `:2085`、`:2437`、`:2592`)。
- `status.py` → `redlight.py`:`status.py:355-370` `load_redlight(root)` 依路徑載入 `<root>/.claude/hooks/redlight.py`。
- `status.py` → `gate.py`:`status.py:98-111` `load_gate(root)`。
- `redlight.py` → `gate.py`:**無**。`redlight.py` 的 import 只有標準庫(`:33-40`,以及函式內的 `uuid` / `types` / `subprocess` / `shlex` / `tomllib`);提到 `gate` 的地方(`:18`、`:27`、`:86`、`:89`、`:157`)都是註解。
- `verify_gates.py` → 兩者:`.claude/portable/verify_gates.py:238` `load_target_gate`、`:295` `load_target_redlight`。
⇒ 兩邊都已經引用 `redlight.py`,而且沒有循環 ⇒ 不新建模組,facts 模組本身不需要新的 manifest 登記。
~~(⚠ 這句只講模組。**新的測試檔另計**:`tests/test_manifest.py:196-219` 要求 `tests/` 下每個檔都在 `.agents/portable-manifest.txt` 標 copy / skip。)~~(F-036 體例:舊行不刪)—— 2026-10-06:選 C,測試併入 tests/test_redlight.py,無新檔。

### 已知盲區 / known limitation

1. `--plugin-dir`:只是啟動旗標,沒有落地檔 ⇒ 沒有靜態入口。
2. claude.ai connector:沒有本機登記點。
3. `mcp__` 前綴不證明來源(2.1.289 reference.md:178:mod 註冊的工具也列成 `mcp__<plugin>__<name>`)。**不做成測試**:v0 沒有 provenance API。
4. EXT_VERIFIED 不可達,只有 regression lock(行為鎖 + 結構鎖),**不是形式證明**。

第三站停點報告:.dev/reports/2026-10-06T145908Z-ticket146-s3-halted-before-B.md;三選一裁 C。

---

## 第三站紅燈(S3-146-1)

- 審計:`docs/audits/2026-10-06-146-station3a-redlight.md`
- 紅燈:`tests/test_redlight.py::TestTicket146ExtensionIntegrity`,14 個(T146-0a、1、2、2b、2c、3、3b、4、4b、5、6、7、8、9)。
- 證紅(S3-146-1 `0993d217a27bce8119587bf1553df49a3521e79e`,乾淨工作樹,Windows):**13 failed**(全部屬於本 class),T146-9 依規格 skip;其餘 2110 passed,沒有 collection / setup / teardown ERROR。
- 待第四站:實作 `redlight.py` 的契約名稱與 `gate.py` R4 的遞迴 tree parity;改名必須回本票記一筆。

---

## 契約增補 3b(2026-10-06)

### 裁決(Jeff,2026-10-06;逐字)

(a) 4-146 暫緩：第三站契約漏掃 ~/.claude/skills 與 ~/.claude/commands，先補紅燈再實作。
(b) 共用 facts 層不得反向載入 gate.py。架構方向 = B：R4 樹比對純函式下沉到 redlight.py；gate.skill_mirror_violations 改為薄包裝，簽名、訊息、呼叫點不變；依賴方向 gate → redlight、status → redlight，redlight 不依賴任何專案模組。
(c) 第四站未接 status / pre-commit 前，票面狀態只能寫「核心判定已提交；146 尚未生效」，不得寫「待第五站審查」。
(d) extension_surface_facts 契約增補兩個參數與兩個回傳鍵：user_skills_dir → "user_skill_plugins"、user_commands_dir → "user_commands"。排除規則：只排除 user_skills_dir 的直接子目錄 synced（即 <user_skills_dir>/synced）及其整棵 subtree；其他層級恰好名為 synced 的目錄不得因此被排除。
(e) 兩種資料形狀分開鎖：
    policy（allowlist 檔）裡的 dev_mod_files / user_skill_plugins / user_commands，每項恰為物件 {"sha256": 64 碼小寫十六進位, "note": 字串}，鍵集合恰好這兩個。
    surfaces（extension_surface_facts 回傳）裡的同名三鍵，每項恰為 tuple (relpath, sha256 或 None)。
(f) extension_state 的完整性前提：surfaces 鍵集合必須恰好等於 {"dev_mod_files","synced_files","r4_violations","project_hook_commands","mcp_json_servers","user_skill_plugins","user_commands"}；少任何一鍵或多任何一鍵 ⇒ 不得回 EXT_DECLARED_OK（回 EXT_UNKNOWN，fail-closed）。
(g) 已知後果：~/.claude/commands/ 現有的 .md（R-146-1 看到一個）在 allowlist 空時會判 VIOLATION；這是設計內的，要由 Jeff 核准指紋後才合法。

### 增補後的契約

- `extension_surface_facts` 完整簽名:`(dev_mods_dir, synced_dirs, canon_dir, mirror_dirs, project_settings_paths, mcp_json_path, user_skills_dir, user_commands_dir)`。
- surfaces 七鍵:`"dev_mod_files"`、`"synced_files"`、`"r4_violations"`、`"project_hook_commands"`、`"mcp_json_servers"`、`"user_skill_plugins"`、`"user_commands"`。
- policy 形狀:allowlist 的 `dev_mod_files` / `user_skill_plugins` / `user_commands` 每項恰為 `{"sha256": <64 碼小寫十六進位>, "note": <字串>}`,鍵集合恰好這兩個。
- surfaces 形狀:回傳的 `dev_mod_files` / `user_skill_plugins` / `user_commands` 每項恰為 tuple `(relpath, sha256 或 None)`。
