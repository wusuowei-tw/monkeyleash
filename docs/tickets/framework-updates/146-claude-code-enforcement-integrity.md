# 票 146 —— Claude Code Enforcement Integrity

**狀態**:立案 —— 第一步唯讀盤點已完成(2026-10-04 報告 2026-10-04T124314Z-ticket146-step1-inventory.md / 2026-10-04T130149Z-ticket146-step1-closeout.md,於 Claude Code 2.1.289 執行;門檻 ≥ 2.1.287 已滿足);可進入設計。
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
