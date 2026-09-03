# 票 101:唯讀 MCP v0 —— 把 `status` / `ticket` / `friction` 接到 Claude Desktop

**狀態**:**done**(2026-09-03 收票;實機驗收通過,見九之一)
~~**狀態**:**implement**(2026-09-03 核定,六裁逐字入票見第五節;擬稿降級保留於五之一)~~
~~**狀態**:**candidate**(2026-09-03 立案)~~(F-036 體例:舊行不刪)

**立案**:票 100 收票後的唯讀偵察(2026-09-03)。動機不是「缺一個功能」,是
**證據目前只有一個出口**:`status.py` 要在 PowerShell 裡跑,而做判斷的人不在終端機裡。
v0 只做**唯讀投影**,不做任何寫入 —— 寫入類工具是架構級的「永不做」,見第八節。

**來源票根**:本 repo `3523500`(偵察時的 HEAD,工作樹乾淨,`git status --porcelain | wc -l` = 0)

---

## 一、範圍

**宿主**:Claude Desktop + **本機 stdio**(不是遠端、不是 HTTP)。

**三支工具,就這三支:**

| 工具 | 輸入 | 回傳 |
|---|---|---|
| `status_all` | 無 | **原樣回傳** `status.py` 的 stdout,一個位元組都不加工 |
| `ticket(n)` | 票號 | 該票 markdown 全文 |
| `friction(F-n)` | friction 號 | 該則 friction log 全文 |

**v0 上游專用** —— 只裝在 monkeyleash 這個 repo,不進 portable manifest 的 `copy` 桶。

**不在範圍**:resources、prompts、任何寫入、任何下游 repo。

---

## 二、偵察實測(2026-09-03,原始數字)

### 二之一、SDK 現況

```
pip show mcp        → Version: 1.27.0    Required-by: mcp-server-duckdb
pip index versions  → INSTALLED: 1.27.0  LATEST: 2.1.1
python --version    → Python 3.11.9
```

**三格要分開讀。** 第三格 `Required-by: mcp-server-duckdb` 是升版決策的成本欄 ——
升 2.x 動到的不只本專案。

### 二之二、`status.py` 的可呼叫面

```
676:def render(root)          → unicode 多行字串,結尾帶 \n
786:def render_all(roots)     → unicode;roots 長度 >=2 時多接一段 Sync Health
806:def find_root(start=None) → 絕對路徑 str,找不到回 None
818:def main(argv=None)       → int 退出碼(0 / 2)
```

`main` 的 argv 處理:`argparse`,唯一參數 `--root`(`action="append"`,可重複);
`roots` 空 → 寫 stderr 回 `2`;`len(roots) > 1` → `render_all`,否則 `render`;
寫 `sys.stdout` 回 `0`。

**`render` 的 docstring 逐字**:

```
def render(root):
    """算一次現況,回傳多行字串。**不寫任何檔案**(判準 1)。"""
```

### 二之三、票號解析

`gate.py:1136`:

```
TICKET_DIRS = (".scratch/%s/issues", "docs/tickets/%s")
```

`status.py:567-576`(`_find_ticket_file` 全文):

```
def _find_ticket_file(root, gate, feature, ticket):
    """票檔在哪。**所有存在的票目錄都找**,不是取第一個。"""
    if not feature or not ticket:
        return None
    for d in _ticket_dirs(root, gate, feature):
        for name in sorted(os.listdir(d)):
            if name.startswith(str(ticket)) and name.endswith(".md"):
                return os.path.join(d, name)
    return None
```

`gate.py:1265-1271` 是**同一式**(`startswith`,不是 `^<n>-`):

```
    for tmpl in TICKET_DIRS:
        d = tmpl % feature
        abs_d = os.path.join(ROOT, d.replace("/", os.sep))
        if not os.path.isdir(abs_d):
            continue
        for name in sorted(os.listdir(abs_d)):
            if not name.startswith(str(ticket_id)):
                continue
```

⇒ **兩處都是前綴比對,兩處都沒有邊界。** 這是 `CLAUDE.md` 那條
「前綴要帶邊界…… 與 `skills/` 缺前導斜線同一族」在第三個位置的實例。

### 二之四、friction 號解析

`.claude/portable/friction_heading.py` **沒有任何 `def` 或 `class`**
（`grep -n '^def \|^class '` → 0 命中,而檔案存在,2195 bytes）。
它對外只出一個常數:

```
HEADING = re.compile(r"^##\s+([A-Za-z]+-\d+)(?:\s|$|[^\w-])")
```

⇒ 「不另寫第二份」的具體作法是 **`from friction_heading import HEADING`**,不是呼叫某個函式。
而該檔 docstring 同時規定:**不得改成 import `gate.py` 的 `_FRICTION_HEADING`** ——
那是票 42 刻意保留的第二份,理由是「權威層要依賴最少的東西」。**負控就守這一條。**

### 二之五、manifest 落桶

```
64:.claude/portable/               copy
331:.claude/portable/__pycache__/ skip
```

第 64 行是**目錄前綴規則** ⇒ 新增的 `.claude/portable/<任何>.py` **預設落 `copy`**,
跟著裝進每個下游 repo。第 331 行證明更長的前綴可以覆寫。

---

## 三、⚠ 官方文件與已裝 SDK **對不上** —— 這一格決定裁 C

官方 python quickstart(https://modelcontextprotocol.io/docs/develop/build-server,
2026-09-03 抓)逐字寫:

```python
from typing import Any

import httpx2
from mcp.server import MCPServer

# Initialize MCPServer
mcp = MCPServer("weather")
```

**這在已裝的 1.27.0 上 import 不起來。** 實測:

```
mcp/server/__init__.py:5
__all__ = ["Server", "FastMCP", "NotificationOptions", "InitializationOptions"]
```

`MCPServer` 這個名字在 1.27.0 裡只以**內部別名**存在,不從 `mcp.server` 匯出:

```
mcp/server/fastmcp/server.py:59:from mcp.server.lowlevel.server import Server as MCPServer
mcp/server/streamable_http_manager.py:18:from mcp.server.lowlevel.server import Server as MCPServer
```

文件同時寫 `import httpx2`,而 1.27.0 的相依是 `httpx`(見 `pip show mcp` 的 `Requires:`)。
⇒ **那份 quickstart 是為 2.x 寫的。**

**1.27.0 上的正確寫法**(從已裝套件讀出來,不是從文件抄的):

```
mcp/server/fastmcp/__init__.py
from .server import Context, FastMCP
__all__ = ["FastMCP", "Context", "Image", "Audio", "Icon"]

mcp/server/fastmcp/server.py:446
    def tool(
        self,
        name: str | None = None,
        title: str | None = None,
        description: str | None = None,
        annotations: ToolAnnotations | None = None,
        icons: list[Icon] | None = None,
        meta: dict[str, Any] | None = None,
        structured_output: bool | None = None,
    ) -> Callable[[AnyFunction], AnyFunction]:

mcp/server/fastmcp/server.py:279
    def run(
        self,
        transport: Literal["stdio", "sse", "streamable-http"] = "stdio",
        mount_path: str | None = None,
    ) -> None:
```

⇒ v0 用 `from mcp.server.fastmcp import FastMCP` / `@mcp.tool()` / `mcp.run(transport="stdio")`。

**這一格為什麼寫進票面**:下一個人會去看官方文件,而官方文件會**成功地騙過他** ——
`MCPServer` 這個名字讀起來完全合理,`httpx2` 讀起來像個筆誤。
**兩個都不是筆誤,是版本差。** 不寫下來的話,這次的量測下次要重做。

---

## 四、⚠ 指定的紅燈第⑤條**在真實資料上是綠的** —— 實測後改形狀

裁決者給的第⑤條原話:

> `_find_ticket_file`:目錄含 `10-a.md` 與 `100-b.md` 時 ticket `"10"` 回 `10-a.md`

**實測:這個 case 現行程式碼就已經通過。** 真實目錄裡兩個檔都在:

```
$ ls docs/tickets/framework-updates/ | grep -E '^10'
10-sync-needs-an-r2-exemption-bound-to-content.md
100-status-lies-when-idle-and-sync-waterline.md
```

用 `_find_ticket_file` 的**同一段邏輯**(`sorted` + `startswith`)掃真實目錄
(腳本在 scratchpad,不進 repo):

```
檔案數(.md): 99
解析得到的票號數: 99(最小 01 / 最大 100)
撞號(要 t 卻拿到別號)筆數: 0
0 筆 —— 真實資料上不發生
```

**成因是字典序意外救了它**:`"10-"` 與 `"100"` 比到第三個字元,`-`(0x2D)< `0`(0x30),
所以 `10-sync….md` 排在 `100-status….md` **前面**,`startswith("10")` 先命中對的那個。
⇒ **這條紅燈會一出生就是綠的,而一出生就綠的測試證明不了任何事。**

**真正的缺陷在反例側**(同一次量測):

```
--- 反例:目錄裡不存在的號,是否誤命中 ---
不存在的號卻誤命中一個檔的筆數: 9
  ticket 1   (無此票) -> 10-sync-needs-an-r2-exemption-bound-to-content.md
  ticket 2   (無此票) -> 20-provenance-exempts-both-halves-of-r3.md
  ticket 3   (無此票) -> 30-import-side-is-incomplete.md
  ticket 4   (無此票) -> 40-skills-inventory-readonly.md
  ticket 5   (無此票) -> 50-identity-gate-mechanism-then-distribution.md
  ticket 6   (無此票) -> 60-r2-does-not-cover-writes-made-by-tools.md
  ticket 7   (無此票) -> 70-sync-heading-guard-granularity.md
  ticket 8   (無此票) -> 80-g1-level2-cygdrive-unc-not-extracted.md
  ticket 9   (無此票) -> 90-dead-sha-citations-after-the-identity-rewrite.md
```

本 repo 的票號**補零到兩位**(`01`–`09`),所以字串 `"1"` 不對應任何票 ——
而 MCP 的呼叫者會打 `1`,**然後拿到票 10 的全文,沒有任何東西會說那不是票 1**。

**⇒ 第⑤條改成守這一格(見第七節)。原話那一格保留為負控** ——
它現在是綠的,而本票的修法**不得把它弄紅**。

**這一段是「⚠ 一則已作廢的證據,明寫」的同體例**(票 100 第七節):
裁決者指定的形狀被實測推翻,**原話不刪不改,改的理由與量測擺在旁邊**。

---

## 五、裁決(裁決者 2026-09-03 核定)

**以下六條是裁決者本人 2026-09-03 給的原文,逐字入票。** 上一版的 A–F 是 agent 擬稿,
**不刪不改**,降級保留在本節後半(F-036 體例)。

> **為什麼原文與擬稿都留**:兩者**不是同一份東西的兩個版本** ——
> 擬稿是「agent 從指令推出來的」,原文是「裁決者說的」。
> 只留原文的話,下一個人看不出**當初推錯了哪裡**;
> 只留擬稿的話,票面會拿一份沒人核准的東西當裁決用。
> 而**擬稿與原文長得很像**,正是要並排才看得出差異的理由。

### 裁 1 —— SDK **不升**,照 1.27.0 寫;升版**登記候選**

> SDK 不升,照 1.27.0 寫;升版登記候選(`mcp-server-duckdb` 相依)

**代價**:v0 綁在會被上游淘汰的 `FastMCP` 面上;官方 quickstart(2.x)不能當參考,
**要照第三節那格自己讀已裝套件**。到期訊號見第十節。

### 裁 2 —— server 放 `.claude/portable/mcp_server.py`,manifest 加 `skip` + **一行註解**

> server 放 `.claude/portable/mcp_server.py`,manifest 加 skip + 一行註解,照三則先例;v0 上游專用

「三則先例」= manifest 第 127 / 133 / 156 行(`ledger_verify.py` / `g1_verify.py` /
`shadow_review.py` 各留一行註解說明它落在 `copy` 前綴底下)。

**代價**:下游要用 MCP 得另外開票。

### 裁 3 —— 呼叫 `status` **走子程序**,argv 前綴寫死,**不 import `render_all`**

> 呼叫 status 走子程序 `[sys.executable, status.py, "--root", …]` argv 前綴寫死,
> 不 import `render_all`;gate 模組層副作用與 `_git` 動詞**留在子程序**

**⚠ 這一條把第六節第三層的問題從「未證明」變成「不在本行程」。**
不是把它證明掉,是**把它隔到另一個行程去** ——
`load_gate()` 的 `exec_module` 與 `_git()` 的 subprocess **都發生在子程序裡**,
MCP server 這個行程從頭到尾沒有 import 過 `gate`,也沒有自己開過 git。

**代價**:每次 `status_all` 多一次 python 啟動(慢),而且**拿不到結構化資料,只有一串 stdout**。
裁 B(原樣回傳)本來就不要結構化資料,所以這個代價與裁 B 同向。

### 裁 4 —— 票號比對改「**號碼後接 `-`**」;MCP 側先驗格式,**兩式都試**

> `_find_ticket_file` 比對改「號碼後接 `-`」;MCP `ticket(n)` 先驗 `^\d{1,4}$`,
> 試 `n` 與 `n.zfill(2)` **皆須邊界命中**,無則回「未記錄(無此票)」**不回檔**;
> `gate.py:1265` 同族**另開候選票**(權威層)

**⚠ 與擬稿的裁 F 不同的地方**:擬稿只說「不合法回錯」,原文多了
**`n` 與 `n.zfill(2)` 兩式都試** —— 這一格直接解掉第四節量到的那九筆
(`ticket("1")` 會先試 `1-`(不中)再試 `01-`(中),回到票 01,而不是票 10)。
**擬稿沒想到補零這一式,只想到擋掉它。** 兩者的差別是「能用」與「不會錯」。

**代價**:`gate.py:1265` 的同一個洞**這一票不修**(權威層,另開候選)——
所以豁免判定那一側在本票落地後**仍然是無邊界的**,明寫在第八節。

### 裁 5 —— `friction` 用 `friction_heading.HEADING`,**不碰 `gate` 那份**

> `friction(F-n)` 用 `from friction_heading import HEADING`,
> 取該標題到下一個 `^##` 之間原文;不碰 gate 那份(票 42)

**代價**:friction log 若出現非 `##` 層級的分隔,切出來的段落會偏長。
**照票 42 的裁決,這個代價不能用「合併兩份判準」來換。**

### 裁 6 —— 三個 root 由 `claude_desktop_config.json` 的 `args` 傳入;**repo 內不存路徑**

> 三個 root 由 `claude_desktop_config.json` 的 args 傳入;server 只認 `--root`;repo 內不存路徑

**⚠ 這一條同時是洩漏防線。** 票 100 收票那次,下游絕對路徑進了 commit 訊息被洩漏偵測擋下
(18 筆 = 6 行 × 3 pattern)。**路徑不進 repo,那個入口就不存在** ——
是構造,不是紀律。

**代價**:換機器要重打三條絕對路徑,而 repo 裡沒有任何東西可以抄。
處置在 `docs/machine-init.md` 的 `## 四、MCP 註冊`(第十節)。

---

## 五之一、⚠ 核定前的 agent 擬稿(F-036:舊行不刪)

**以下 A–F 是 agent 2026-09-03 從立票指令推出來的擬稿,已被上面六條取代。**
**保留的用途是對照,不是備援 —— 任何時候以上面的裁 1–6 為準。**

已知推錯的兩處,明寫:

| 擬稿 | 原文 | 差在哪 |
|---|---|---|
| 裁 F「不合法回錯」 | 裁 4「`n` 與 `n.zfill(2)` 兩式都試」 | 擬稿只想到**擋掉**補零問題,沒想到**解掉**它 |
| 裁 D「第三層只能寫『量到 0 筆』」 | 裁 3「留在子程序」 | 擬稿在**證明**那一層,原文**把它隔開** —— 隔開不需要證明 |

#### (擬稿)裁 A —— 範圍鎖死在「Claude Desktop + 本機 stdio + 三支唯讀工具」

**理由**:v0 的目的是把已經算得出來的證據換一個出口,不是長出新的判定邏輯。
範圍每寬一格,「MCP server 自己會不會說謊」就多一個要守的面。

**代價**:手機 / 網頁上的 Claude 用不到;要用就得等遠端傳輸那一票,而那是另一個安全模型。

#### (擬稿)裁 B —— `status_all` **原樣回傳** `status.py` 的 stdout

**理由**:`status.py` 的每一行都自帶 `(source: …)`,那是判準 3 的產物。
MCP 只要動一個字,**來源欄就開始說謊而沒有東西會叫** ——
它會是一個「看起來有來源」的欄位,那比沒有來源糟。

**代價**:輸出對聊天視窗來說偏長、不好讀。**這是刻意付的** ——
可讀性由讀的人自己挑行,可驗證性一旦丟掉就回不來。

#### (擬稿)裁 C —— SDK **停在已裝的 1.27.0**,不升 2.x

**理由**:兩件事各自成立。(1) 本機 `mcp-server-duckdb` 相依它,升版的爆炸半徑超出本票。
(2) 更要緊的是第三節那格 —— 官方 quickstart 已經改寫成 2.x 的 `MCPServer` / `httpx2`,
**而我們手上的是 1.27.0**,照文件寫會 import 不起來。停在 1.27.0 讓
「文件與現實對不上」變成一個**寫在票面上的已知事實**,而不是一個 debug 時才發現的驚喜。

**代價**:v0 綁在一個會被上游淘汰的 API 面上(`FastMCP`)。升 2.x 是**候選票**,不是本票。
到期訊號寫在第十節。

#### (擬稿)裁 D —— 零寫入的宣告**分三層寫**,不寫成一句

**理由**:三層各自由不同的東西守,而**把它們寫成一句會讓最弱的那一層繼承最強那一層的可信度**。
逐層見第六節。

**代價**:票面變長,而且第三層目前只能寫「量到 0 筆」不能寫「保證沒有」。
**那個難看正是它誠實的地方。**

#### (擬稿)裁 E —— manifest 加一行 `skip`,v0 **不進下游**

**理由**:`.claude/portable/` 整個前綴標 `copy`(manifest:64),不加 `skip` 的話
每個下游 repo 都會多一支**沒人註冊、沒人跑、沒人維護**的 server 檔。
那不只是浪費 —— 它是一支**看起來已經裝好了**的檔案。

**代價**:下游要用 MCP 的話得另外開票。**這正是想要的** ——
下游要不要有 MCP 是一個決策,不該由一條 `copy` 前綴替他們決定。

#### (擬稿)裁 F —— `ticket` / `friction` 的輸入**先驗格式,不合法回錯不回檔**

**理由**:見第四節的九筆實測。`startswith` 沒有邊界,而**回錯一份票比回不出來糟得多**:
回不出來的人會再查,拿到一份**看起來對**的票的人不會。

**代價**:合法但沒補零的輸入(`1`)會被擋。處置是**回一則說得出原因的錯**
(「票號 1 無對應檔;本 repo 票號補零到兩位,你要找的可能是 01」),不是靜默回最近的一個。

---

## 六、零寫入的宣告 —— **三層,各自的守衛不同**

| 層 | 宣稱 | **誰在守** | 現況 |
|---|---|---|---|
| **一、server 自身** | `mcp_server.py` 不寫任何檔案 | **本票的紅燈②**(AST 掃自己) | 待落地 |
| **二、`status.py`** | `render` / `render_all` 不寫檔(判準 1) | **它自己的測試**(`tests/test_status.py`) | 已存在 |
| **三、`gate.py` 模組層** | import 它不產生寫入副作用 | **沒有東西在守** | 見下 |

**第一層**由本票證明,證法寫在紅燈②。

**第二層**不是本票的功勞 —— `render` 的 docstring 自己寫著「**不寫任何檔案**(判準 1)」,
而守它的是 `status.py` 既有的測試。本票**引用**這個保證,不重新證明它。
輔證(本次 grep):`status.py` 全檔四處 `io.open` **全部無 mode 參數** = 讀取模式;
兩處 `.write(` 都在 `main()` 內、寫的是 stderr / stdout,不是檔案。

**第三層是本票唯一寫「未證明 → 已量到 0」的一格,而且要看清楚它量的是什麼。**

`render()` → `load_gate(root)` → `spec.loader.exec_module(mod)`,
**會執行目標 repo `gate.py` 的模組層**。本次用 scratchpad AST 腳本量測
(排除 `FunctionDef` / `AsyncFunctionDef` / `ClassDef` / `Lambda` 主體,
所以 `if` / `try` / `for` / `with` 底下的模組層陳述句**有**被涵蓋):

```
--- .claude/hooks/gate.py ---
模組層 Call 總數: 37
其中名稱屬於 ['Popen','makedirs','mkdir','open','remove','rename','run','system','unlink'] 的: 0 筆
0 筆
模組層出現過的所有 Call 名稱(供人自己看):
  ['abspath','compile','dirname','exit','expanduser','frozenset','join','lower',
   'mode_hook','mode_pre_commit','split']

--- .claude/portable/status.py ---
模組層 Call 總數: 2
其中名稱屬於 [...] 的: 0 筆
0 筆
模組層出現過的所有 Call 名稱(供人自己看): ['exit','main']
```

**⚠ 這是「量到 0 筆」,不是「保證 0」。三個已知限制,逐條寫:**

1. **黑名單,不是枚舉。** 判準是九個**名字**;`shutil.copy`、`pathlib.Path.write_text`、
   `os.replace`、`io.FileIO` 都不在那九個裡。
   依 `CLAUDE.md`「封閉集合用枚舉,開放集合才用 pattern」—— 「所有寫入方式」是**開放集合**,
   所以這裡選 pattern 是對的工具,但**它的漏是未知的**。
2. **只看名字,不看 binding。** `run` 這個名字沒出現,不代表沒有別名指過去。
3. **`gate.py` 模組層有兩個呼叫叫 `mode_hook` / `mode_pre_commit`** ——
   名字不在黑名單裡,而**它們是 gate.py 自己的函式**。本次沒有往下追它們的函式體。
   （追不追是取捨:`gate.py` 被 `if __name__` 護著時模組層不會呼叫到它們,
   但**本次沒有量那個 `if`**,所以這裡寫「沒追」而不是「不會執行」。）

⇒ **第三層的正式措辭是:「以九個名字為判準,模組層 Call 命中 0 筆;
黑名單外與別名的情形未涵蓋,`mode_hook` / `mode_pre_commit` 未往下追。」**
**不寫成「gate.py 匯入無副作用」** —— 那句話比量測強。

> **這一節在對付的是 `CLAUDE.md` 那條:「識別風險的品質越高,它偽裝成處置的能力越強。」**
> 上面三個限制寫得再清楚,**除了這段文字之外沒有任何東西在管第三層**。
> 要有機制的話,那是另一張票(把 AST 檢查釘進 `tests/`),本票**不假裝已經做了**。

---

## 七、紅燈形狀

**五條全部在 `tests/test_mcp_server.py`**;第⑤條動 `status.py`,故 `tests/test_status.py` **也加一條**。

### ① 工具清單**恰好**是那三支

`FastMCP` 註冊完之後列出工具名,斷言 `== {"status_all", "ticket", "friction"}`。
**用相等,不用包含** —— 包含擋不住「多長出第四支」,而多出來的那支正是要擋的東西。

### ② AST:`mcp_server.py` 無寫入呼叫,且 subprocess **只有一處**

兩個斷言,缺一不可:

- **全檔**(不只模組層)沒有名為
  `open` / `makedirs` / `mkdir` / `remove` / `unlink` / `rename` / `system` / `Popen` 的 Call。
- `subprocess.run` **恰好出現一次**,且該次的第一個位置引數是一個 list,
  前三個元素為 `[sys.executable, <status.py 絕對路徑>, "--root"]`。

**釘 argv 前綴而不只是「有沒有 subprocess」的理由**:`_git()` 那個先例已經示範過
——「這次傳的是唯讀指令」與「這支只跑唯讀指令」是兩句話。釘前綴把後者變成構造。

⚠ **本條與第六節第一層是同一件事的兩面**,而它繼承第六節列的三個限制
(黑名單、只看名字、不追別名)。**測試通過不等於零寫入,等於「這九個名字沒出現」。**

### ③ 輸入格式

- `ticket` 只收 `^\d{1,4}$`
- `friction` 只收 `^[A-Za-z]+-\d+$`（與 `friction_heading.HEADING` 的號碼部分同式)
- 不合法 → **回錯,不回檔**。斷言回傳裡不含任何檔案內容。

### ④ `status_all` 逐位元組相同

對一個 tmp repo,比較兩者:

- `status_all()` 的回傳
- 直接 `subprocess.run([sys.executable, status.py, "--root", tmp])` 的 stdout

**斷言 `bytes` 相等,不是 `str` 相等,也不是 `strip()` 之後相等。**
裁 B 說的「一個位元組都不加工」要由這一條變成構造 ——
`strip()` 一下就把「結尾那個 `\n`」這種差異放過去了,而那正是加工。

### ⑤ 票號邊界（**形狀依第四節的實測改過,原話保留為負控**)

**依裁 4 定案的三格**(全部在 `tests/test_status.py`,對同一個 tmp 目錄
`10-a.md` + `100-b.md`):

| 呼叫 | 期望 | 性質 |
|---|---|---|
| `_find_ticket_file(…, "10")` | `10-a.md` | **負控** —— 現行就綠,修法不得把它弄紅 |
| `_find_ticket_file(…, "1")` | **`None`** | **紅的那一條** —— 現行回 `10-a.md` |
| `_find_ticket_file(…, "100")` | `100-b.md` | **負控** —— 邊界改成 `+"-"` 之後仍要中 |

**修法(裁 4 前半)**:`name.startswith(str(ticket))` → `name.startswith(str(ticket) + "-")`。

**⚠ 補零那一式在 MCP 那一層,不在 `_find_ticket_file` 裡**(裁 4 後半)——
`_find_ticket_file("1")` 回 `None` 是**正確行為**,由 `mcp_server.ticket()`
再試一次 `"01"`。**兩層分工要寫清楚**:底層只回答「這個字串有沒有邊界命中」,
補零是**呼叫者對本 repo 命名慣例的知識**,不該埋進通用查找函式裡
(下游 repo 不見得補零)。

**負控 2(架構)**:`mcp_server` **不 import `gate`**。
斷言 import `mcp_server` 之後 `sys.modules` 裡沒有本 repo 的 `gate` 模組。
理由在 `friction_heading.py` 的 docstring 逐字寫著(票 42 裁決):
「權威層要依賴最少的東西 —— 讓它 import `portable/` 會多一個失效點,
而閘門起不來的樣子跟沒裝一模一樣」。**方向反過來也一樣要守。**

**`tests/test_status.py` 加的那一條**:`_find_ticket_file` 的同一個邊界 case ——
因為修的是 `status.py` 裡的函式,而**測試要放在被修的東西旁邊**,
不能只靠 MCP 那一側的測試守它(下一個呼叫者不會經過 MCP)。

---

## 八、**不做**

| 不做 | 性質 | 理由 |
|---|---|---|
| **SDK 升 2.x** | **候選票** | 見裁 1。升版的爆炸半徑含 `mcp-server-duckdb`;且 v0 要先能動 |
| **下游 repo 用 MCP** | **候選票** | 見裁 2。下游要不要有 MCP 是一個決策,不該由 `copy` 前綴代決 |
| **`gate.py:1265` 票號比對無邊界** | **候選票(權威層)** | 見下 |
| **任何寫入類工具** | **架構級原則,永不做** | 見下 |
| **劇本第 26 步** | **等筆電日** | 見第十節 |

### 🔴 `gate.py:1265` 的同族洞 —— 本票**不修**,另開候選票

裁 4 只修 `status.py` 的 `_find_ticket_file`。**`gate.py:1265` 有語意相同的一份,本票不動它**:

```
        for name in sorted(os.listdir(abs_d)):
            if not name.startswith(str(ticket_id)):
                continue
```

**為什麼分開**:那一份在**權威層**(R2 豁免判定),而 `CLAUDE.md` 寫著
「權威層要依賴最少的東西」、「錯在權威層等於擋住做對事的人」。
改權威層的判定要單獨一票、單獨的紅燈、單獨的驗收 ——
**搭本票的便車會讓那個改動沒有自己的證據**。

**所以本票落地之後,兩份會暫時不一致**:`status.py` 有邊界,`gate.py` 沒有。
**這句話要留在票面上** —— `CLAUDE.md` 說「同缺陷的兩份實作必然漂開」,
而這一次是**知情地、有期限地**讓它漂開,不是忘了。

⚠ **影響面明寫**:`gate.py` 那一份決定 R2 的**豁免**。無邊界的後果是
`ticket_id = "1"` 時可能撈到票 10 的宣告 —— 方向是**多給豁免**,也就是 **fail-open**。
本票落地不會讓它變好,也不會讓它變壞。**候選票的時鐘:下一次有人用個位數票號時。**

### 「寫入類工具永不做」是架構級原則,不是 v0 的範圍取捨

**出處**:2026-09-01 GPT 第四版 + 2026-09-02 裁決。

**理由**:MCP server 跑在 Claude Desktop 底下,而 **Desktop 那一側沒有六站閘門**——
`gate.py` 的前哨掛在 `.claude/settings.json` 的 PreToolUse,那是 Claude Code 的掛載點。
一支能寫檔的 MCP server 等於**在閘門旁邊開一個它看不到的入口**,
而依 `CLAUDE.md`「R7 只活在前哨」那句,權威層(pre-commit)看得到檔案內容、
**看不到你用什麼工具寫的**。

**代價**:MCP 這一側永遠只能看不能動,要改東西還是得回 Claude Code。
**這個代價是刻意付的,而且不隨版本重新評估** —— 寫成「永不做」而不是「v0 不做」,
正是為了讓下一個人不會把它讀成一個排程問題。

> ⚠ **這一格自己就是「祈使句沒有主詞」的候選**:目前守著它的是這段文字,
> 加上紅燈①(工具清單恰三支)。①擋得住「多長出第四支」,
> **擋不住「把 `ticket` 改成能寫」** —— 那一面現在沒有機制。明寫在這裡。

---

## 九、驗收

**驗收的材料要從別的地方來**(票 100 收票的同一條紀律)——
所以驗收**不是** agent 自己跑一次 server 說它通了。

1. **Jeff 本人**手改 `claude_desktop_config.json`(位置見下,**不寫死**),
   `args` 帶**三個 `--root` 絕對路徑**(上游 + 兩個下游)。
2. **重啟 Claude Desktop**（改設定不重啟不生效)。
3. 在 Desktop 裡叫 `status_all`。
4. **同時**在 PowerShell 跑 `status --all`。
5. **兩份逐字比**,`generated` 時間戳除外。

### 🔴 設定檔位置:**從 App 裡取得,不寫死**

**取得方式**:Claude Desktop → **Settings → Developer → Edit Config**。
那個按鈕會開啟**這台機器上實際生效的那一份**,不存在就順手建一份。

**為什麼不寫死路徑**:Windows 有**兩種安裝形態**,設定檔住不同地方 ——

| 安裝形態 | 設定檔在哪 |
|---|---|
| 一般(MSI / exe)安裝 | `%APPDATA%\Claude\` |
| **Microsoft Store 版** | `Packages` 底下該 App 的 **`LocalCache\Roaming\Claude\`** |

Store 版的路徑含**套件容器目錄**,**本票不寫帳號名、不寫完整路徑** ——
依裁 6,絕對路徑不進 repo。

⚠ **這一格取代了上一版票面「Windows: `%APPDATA%\Claude\claude_desktop_config.json`」那句。**
那句是官方文件的逐字,**而官方文件只講了一般安裝那一種** ——
**它沒有寫錯,是它沒有寫全**,而讀的人分不出這兩者。
舊句不刪,降級為下方「官方文件原文」一格(F-036)。

**官方文件原文(2026-09-03,https://modelcontextprotocol.io/docs/develop/connect-local-servers)**:

> * **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
> * **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

**`"command"` 用 `python.exe` 的絕對路徑,不用 `uv`** ——
官方 quickstart 的 `"command": "uv"` 是為 2.x + `uv` 專案佈局寫的(見第三節),
本專案沒有 `uv` 佈局。絕對路徑用 `where python` 查,**查到什麼寫什麼**,
不假設 PATH 在 Desktop 的執行環境裡與 PowerShell 相同 ——
**那正是官方 Warning 說的那件事**(「You may need to put the full path to the `uv` executable」)。

**日誌**:與設定檔**同一個資料夾底下的 `logs\`**,檔名 `mcp-server-<name>.log`
(官方文件逐字:「Files named `mcp-server-SERVERNAME.log` will contain the stderr output
from the named server. Stdio servers may use stderr for all their logging,
so these files are not limited to errors.」)。
`mcp.log` 存連線層的失敗。**寫成「與設定檔同一個資料夾」而不是 `%APPDATA%\Claude\logs`,
理由與上面那格一樣** —— Store 版兩者一起搬。

**⚠ 一則官方已知坑,先記著**:若日誌裡出現路徑含 `${APPDATA}` 的錯誤,
要在 `claude_desktop_config.json` 的 `env` 鍵補上 `%APPDATA%` 的展開值。

**⚠ 這一節的形狀本身要被檢查**(`CLAUDE.md`「驗收清單天生偏向意圖」):
上面五步驗的是**方向 A**(「MCP 那邊拿得到嗎」)。
**方向 B 是「PowerShell 那條路還在嗎」** —— 本票不動 `status.py` 的 CLI 外殼,
但第⑤條會動 `_find_ticket_file`,而那支**同時**被 CLI 的 Ticket 區段用著。
所以驗收要多一格:**修完之後 `status --all` 的 Ticket 區段仍指得到當前票**。

---

## 九之一、🟢 實機驗收結果(2026-09-03,**Jeff 本人**)

**材料來源**:Claude Desktop 起的 server(**不是** agent 起的),
與 PowerShell 直跑,兩份由裁決者本人取得。

| | 時間(UTC) | 取得方式 |
|---|---|---|
| Desktop 叫 `status_all` | `05:31:11Z` | Desktop 自己起 server |
| PowerShell 直跑 `status.py` | `05:32:18Z` | 同一組三個 root |

**逐行比對:139 行,差異只有兩類 ——**

| 差異 | 行數 | 判定 |
|---|---|---|
| `generated` 時間戳 | **3 行** | 預期內(兩次跑相隔 67 秒;第九節本來就寫明除外) |
| `root` / `upstream` / `outpost` 行的**磁碟機字母大小寫** | 見下 | **非缺陷** |

**其餘逐字相同。** 交叉核對的欄位全部一致:

```
head        8533249
ahead       6
waterline   兩個下游各 2 個 commit(未收齊)
drift       三檔
綠燈        36
```

### 磁碟機字母那一格 —— **非缺陷,但要說出它為什麼會不同**

`c:` 與 `C:` 的差別**來自 argv,不來自程式**:

- Desktop 那一份走 `claude_desktop_config.json` 的 `args`,那裡寫的是**小寫** `c:\projects\...`
- PowerShell 那一份是人手打的,**大寫** `C:\projects\...`

`status.py` 的 `root` 欄位是 `os.path.abspath(argv --root)` 的**原樣回傳**,
而 Windows 的 `abspath` **不正規化磁碟機字母大小寫**。
⇒ 兩份不同**正是「原樣回傳」在做它該做的事**(裁 B),
**如果兩份一樣,反而表示中間有人正規化過。**

**登記(建議,非缺陷)**:設定檔的磁碟機字母**改成大寫**,
與 PowerShell 慣用寫法一致 —— 這樣下次逐行比只剩 `generated` 三行,
**而「只剩三行」比「三行加幾行大小寫」更容易一眼掃完**。
不改也完全正確。

⚠ **兩份原文不貼進票面**:它們含兩個下游 repo 的絕對路徑(`OneDrive` 底下)。
依裁 6「repo 內不存路徑」與票 100 的先例(遮成 `<影音根>` / `<量化根>`),
原文留在裁決對話裡,票面只留可核對的欄位。

### 方向 B 也過了

第九節那一格(「PowerShell 那條路還在嗎」)由上表的 PowerShell 那一份直接證到:
`status --all` 跑得起來、139 行、Ticket 區段正常。

---

## 九之二、落地六刀

| 刀 | sha | 內容 |
|---|---|---|
| 1 立案 | `012087c` | 票檔 538 行 |
| 2 核定 | `83531f8` | 六裁逐字入票;擬稿降級 |
| 3 紅燈一 | `3adeb44` | `mcp_server` 收集錯誤 + `_find_ticket_file` 邊界(1 failed / 2 passed) |
| 4 落地 | `c6d07be` | server + 邊界修 + manifest skip + machine-init 第四節 |
| 5 紅燈二 | `23eccf0` | stdin/timeout 釘 kwargs + 真起 stdio server(2 failed / 2 passed) |
| 6 修復 | `8533249` | `stdin=DEVNULL` + `timeout=60`;第十二節 |

**全套最終:1236 passed / 3 skipped / 3 xfailed。**

⚠ **六刀裡有兩組紅綠燈,不是一組。** 第二組(5、6)不是補做 ——
它是**第一組全綠之後在真實環境失敗**才長出來的,成因與代價寫在第十二節。
把六刀讀成「一次順利的落地加一點收尾」會漏掉本票最貴的那一課。

---

## 十、時鐘

**兩個日期,不是一個:**

- **9/11 桌機打包前落地** —— 到期時性質會變:打包之後這支 server 的開發環境
  (已裝的 1.27.0、已驗過的路徑)不在手邊了,要重建。
- **筆電 9/9 驗收** —— 驗收要**另一台機器**,而筆電日是那台機器唯一排定的時點。
  錯過就沒有獨立的驗證來源,只剩「在寫它的那台機器上它能跑」。

**連帶**:`docs/machine-init.md` 加 `## 四、MCP 註冊`。

落點已量:該檔 933 行,末節 `## 三、新專案安裝` 起於 915 行、
`### 要不要開影子?一條判準` 起於 927 行。
**新節接在 933 行之後另起 `## 四、`** —— 不放進 `## 一、`,
因為那一節的標題是「`~/.claude/` 底下框架需要的每一份檔案」,
而 Desktop 設定檔在 `%APPDATA%\Claude\`,**不在 `~/.claude/`**,放進去會讓那個節名開始說謊。

> ⚠ 裁決者立票時寫的是「劇本第 26 步」。**`docs/machine-init.md` 裡沒有第 25 步** ——
> 實測:全檔唯一的長編號序列是 `## 一、` 底下的 **1–6**(287/370/379/388/491/505 行),
> 另有兩處短清單(51-57 行的 1–3、354-357 行的 1–4),**都到不了 25**。
> 原話不刪;若「第 26 步」指的是別的檔,這一格要重定。

---

## 十一、紅燈紀律

- 紅燈與落地**都記在票 101 底下**(`.dev/test-runs.jsonl` 的 `ticket_id` = `"101"`)。
- `.dev/pipeline.json` 的 `current_stage` **由 Jeff 切**,agent 不動它。
  立案當下是 `idle` / `feature: framework-updates` / `ticket_id: null`。
- 紅燈先行:測試檔單獨一刀,`git show HEAD:<實作檔> | sha256sum` 與帳本 `impl_hash` 逐字相同,
  證明那一刀沒動實作。

---

## 十二、🔴 驗收失敗與修復(2026-09-03)

**`c6d07be` 落地、全套 1232 綠,而第一次實機驗收失敗。** 這一節記整件事。

### 十二之一、失敗現場(**材料來自 Jeff,不是 agent 自跑**)

| 觀測 | 值 |
|---|---|
| Claude Desktop 叫 `status_all` | **兩次 timed out** |
| 同一時間 PowerShell `Measure-Command` 直跑 `status.py` | **0.98s** |

**這兩格擺在一起才有意義**:同一份 `status.py`、同一組 root,
在終端機是 1 秒,在 Desktop 是叫不動。⇒ **不是 `status.py` 慢。**

### 十二之二、成因

`.claude/portable/mcp_server.py` 的 `subprocess.run(...)` **只帶了 `capture_output=True`**,
沒有 `stdin`。在 MCP stdio server 底下,**沒有重導向 stdin 的子程序會連帶繼承
server 與客戶端之間那對管線**,於是 `subprocess.run` 等不到結束。

### 十二之三、探針結論(逐項,scratchpad,未進 repo)

| 實驗 | 結果 | 排除了什麼 |
|---|---|---|
| `ticket` / `friction` 走協定 | **0.01s 正常** | 不是「server 起不來」,也不是「呼叫工具」壞了 |
| `initialize` + `list_tools` | **0.76s 成功,三支工具都在** | 握手與註冊都好 |
| 三個 root 直跑 `status.py` | **0.88s,rc=0** | `status.py` 本身沒問題;OneDrive 路徑也不慢 |
| 普通父行程下 stdin 三種寫法 | 都 **~1.05s** | ⚠ **單看這一格會得出「stdin 無關」的錯誤結論** |
| 客戶端過濾成 12 個環境變數 | **1.00s** | 環境變數無關 |
| 最小 FastMCP server,子程序只是 `print('hi')`,stdin 繼承 | **卡住** | **與 `status.py` 無關** |
| 同一支,`stdin=DEVNULL` | **1.03s** | 一行修法,已實測 |
| 客戶端逾時 20s / 40s | 子程序記到 **20.02s / 40.03s** | **是跟著拆線才回來 ⇒ 死鎖,不是慢** |

**最後一格是這一節最要緊的一格。** `60.03s` 那個數字第一次出現時,
它太接近我設的 60s 逾時 —— **不分清的話會把「永遠不回來」寫成「要跑 60 秒」**,
而那兩者的嚴重度差一個量級,處置也不同(調 timeout vs 找死鎖)。

⚠ **機制的部分是推的,不是量的**:Windows 上 `subprocess` 只要有任一標準流
未重導向就會用 `bInheritHandles=True` 交出可繼承 handle。
**行為是量出來的,`bInheritHandles` 那句是推的** —— 分開寫。

### 十二之四、⚠ 為什麼 1232 支全綠而現場是死的

**兩件事不衝突。** 既有測試**全部是在 pytest 的行程裡直接呼叫那個函式**,
而 pytest 的 stdin 不是 MCP 管線 ⇒ **那個死鎖在測試環境裡不會發生**。

紅燈④(逐位元組相同)是最貼近的一條,而**它也是 in-process 的**:
它證的是「這個函式回的字串對」,不是「這支 server 在協定上活著」。

紅燈②釘了 `argv` 前綴,**而現場死掉的原因不在 argv 裡,在 kwargs 裡** ——
`grep -n 'stdin' tests/test_mcp_server.py` 在修復前是 **0 命中**。

> **判準:測試造的行程環境,證不出真實行程環境裡的事。**
> 這與「材料要從別的地方來」是同一句話,只是換到行程模型這一面 ——
> 材料(行程環境)若由測試自己造,它只能證明自洽。

**這也是第六節那三層宣告漏掉的第四層**:第六節逐層問了「誰在守零寫入」,
**沒有人問「誰在守它跑得起來」**。零寫入守得再好,叫不動就是零。

### 十二之五、修法(`23eccf0` 紅 → 本刀綠)

- 紅燈②' `test_stdin_and_timeout_are_pinned` —— AST 釘 `stdin=subprocess.DEVNULL`
  與 `timeout=<int>` 兩個 kwarg。**兩件事分開釘,因為它們各自失效**:
  缺 `stdin` 是這一次的成因,缺 `timeout` 是它變成「永遠等」的原因。
- 紅燈⑥ `TestLiveStdioServer` —— **真的起一支 stdio server 走協定叫一次**。
  客戶端跑在子行程裡(不在 pytest 的事件迴圈),
  **理由不只是與 plugin 打架:客戶端與被測 server 同處一個行程,
  會讓「行程環境」這個變因回到測試手上,而那正是本節要避開的東西。**
  兩條負控(`ticket` / `friction` 走同一條線 1s 內回)**是把成因夾出來的那兩支** ——
  沒有它們,⑥ 的逾時會有兩種讀法,而處置不同。
- 實作:`stdin=subprocess.DEVNULL, timeout=60`,`TimeoutExpired` 回
  「未記錄(status 逾時 60s)」—— **說得出上限,不是靜默地等**。

### 十二之六、候選票(**本票不做**)

**`status.py:133` 的 `_git()` 是同族**:也是 `subprocess.run(..., capture_output=True)`
無 `stdin`。**目前無害,因為裁 3 把它關在子程序裡** ——
而那是**別的決定順手保護的,不是它自己安全**。
任何人把 `status.render_all` 改成 in-process import 進 MCP server,同一個死鎖就搬過來。

**到期條件**:有人提「MCP 直接 import status 比較快」的那一刻。

### 十二之七、⚠ 日誌那一格改成「未證明」

`docs/machine-init.md` 的 4-3 原本寫「日誌在與設定檔同一資料夾的 `logs\`」。
**這台 Store 版機器上實測 `mcp*.log` 命中 0**,三種可能(Store 版寫別處 /
這版行為不同 / Desktop 沒真正拉起過 server)都沒排除。

**改成「未證明」而不是刪掉的理由**:原句**看起來完全可用**,
而照著它去找的人會找不到檔,然後懷疑自己路徑打錯。
**一句找不到對應物的指路,比沒有指路糟。**

---

## 十三、🔴 CI 紅:相依未宣告(2026-09-03,收票**之後**)

**收票刀 `fedae28` 推上去,CI 立刻紅。** 這一節記它。

### 十三之一、CI 原文(run 33720175725)

```
pytest	跑測試	##[group]Run python -m pytest -q \
pytest	跑測試	  --ignore=tests/test_known_items_regression.py \
pytest	跑測試	  --deselect "tests/test_gate.py::TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce"
pytest	跑測試	==================================== ERRORS ====================================
pytest	跑測試	__________________ ERROR collecting tests/test_mcp_server.py ___________________
pytest	跑測試	ImportError while importing test module '/home/runner/work/monkeyleash/monkeyleash/tests/test_mcp_server.py'.
pytest	跑測試	Traceback:
pytest	跑測試	tests/test_mcp_server.py:54: in <module>
pytest	跑測試	    import mcp_server  # noqa: E402
pytest	跑測試	.claude/portable/mcp_server.py:77: in <module>
pytest	跑測試	    from mcp.server.fastmcp import FastMCP
pytest	跑測試	E   ModuleNotFoundError: No module named 'mcp'
pytest	跑測試	=========================== short test summary info ============================
pytest	跑測試	ERROR tests/test_mcp_server.py
pytest	跑測試	!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
pytest	跑測試	1 deselected, 1 error in 1.24s
pytest	跑測試	##[error]Process completed with exit code 2.
```

`conclusion: failure`,`headSha: fedae2850c8aa9c854029231c62c274cc8c1ee39`。
**一支測試都沒跑到** ⇒ 那一輪的 `+37` 差額對帳**一個字都沒證到**。

### 十三之二、成因

`mcp` **沒有宣告在 `pyproject.toml`**,而 CI 裝的是 `python -m pip install -e ".[dev]"`
(`.github/workflows/*.yml:50`)。`dependencies` 只有 `pyyaml`,`dev` 只有 `pytest`。

**本機測不出來**:桌機早就裝了 `mcp` 1.27.0(`pip show mcp` 的
`Required-by: mcp-server-duckdb`),所以本機 1236 全綠。

### 十三之三、⚠ 最難看的部分:失效模式我自己寫過,只想到一半

`c6d07be` 的 manifest 註解裡逐字寫著:

```
# 而且更硬一層:本檔在 import 期就 `import mcp_server`,那支 `import mcp`(PyPI 套件),
# 下游的 `pyproject.toml` 沒有那條相依 —— **collection 就炸**,
# 而那個紅與「下游把 server 改壞了」長得一模一樣。
```

**預測完全正確,而我只把它套在下游身上。** 上游 CI 的執行環境與
「一個乾淨 clone 的下游」**是同一類** —— 都只裝 `pyproject.toml` 宣告的東西。

`CLAUDE.md`:「**收了一個入口,就回頭問它的同類入口在哪**……
問法是『這個東西還有哪些同類』,不是『我還想得到什麼』」——
**這一次只做了前半。** 而做前半的時候感覺**像是做完了**:
註解寫得很清楚、理由很完整、代價也明寫了,
唯一沒做的是**把同一句話再套一次在自己身上**。

### 十三之四、這是第十二節那條判準的**第二個實例**

> **測試造的環境,證不出別的環境裡的事。**

第十二節的「別的環境」是 **MCP 行程**(pytest 的 stdin 不是 MCP 管線)。
這一次的「別的環境」是 **CI**(桌機裝了 `mcp`,CI 沒有)。

**兩次的形狀一模一樣,中間只隔了幾個小時。** 而寫下那條判準的人
(就是我)**沒有在第二次發生時認出它** —— 這正是 `CLAUDE.md` 那句
「寫下一條判準,不會讓你在下一次認出它適用」的又一個標本。
**判準是索引,而『認出這次該查那個索引』本身沒有索引。**

### 十三之五、淨室驗證(**材料來自 Jeff,在 PowerShell 跑**)

`python -m venv` 造一個乾淨 venv,只裝 `pyproject.toml` 宣告的東西。
**agent 這一側跑不了這一步** —— R7 擋下用絕對路徑呼叫 venv 內 python.exe 的指令
(白名單比對的是指令名前綴 `python -m pip`,而 venv 一定走絕對路徑),
**已停手未繞過**,原始擋下訊息留在裁決對話。

**修前(Jeff)** —— ⚠ **一行遮過,見下方註記**:

```
======================================================= ERRORS ========================================================
______________________________________ ERROR collecting tests/test_mcp_server.py ______________________________________
ImportError while importing test module 'C:\projects\agent-gates\tests\test_mcp_server.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\<使用者目錄>\AppData\Local\Programs\Python\Python311\Lib\importlib\__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_mcp_server.py:54: in <module>
    import mcp_server  # noqa: E402
    ^^^^^^^^^^^^^^^^^
.claude\portable\mcp_server.py:77: in <module>
    from mcp.server.fastmcp import FastMCP
E   ModuleNotFoundError: No module named 'mcp'
=============================================== short test summary info ===============================================
ERROR tests/test_mcp_server.py
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
no tests collected, 1 error in 0.13s
```

> ⚠ **F-116:遮了就不得再自稱原始。** 上面第 6 行的 `C:\<使用者目錄>\` 原本是
> 本機的使用者路徑,**被洩漏偵測擋下**(`test_the_shipped_tree_is_clean`,
> 命中「個人 pattern #1」)。偵測是對的,不是誤報 ——
> 這份輸出**要跟著 repo 推到 GitHub**,而個人路徑不該在那裡。
> 除那一行之外一字未動;`no tests collected, 1 error in 0.13s` 與所有行號皆未動。

**與 CI 那份同一個失敗**(同一個 `tests/test_mcp_server.py:54` → `mcp_server.py:77` →
`ModuleNotFoundError: No module named 'mcp'`)⇒ **淨室重現了 CI**,
而它是在**本機**重現的 —— 這一格的價值就在這裡:
CI 的紅只證得出「CI 上會紅」,淨室的紅證得出「**任何只裝宣告相依的環境都會紅**」。

**修後(Jeff)** —— ⚠ **venv 路徑遮過,見下方註記**:

```
> python.exe -m pip install -e ".[dev]" -q
(無錯誤;只有 pip 自己的升級提示)

> python.exe -m pytest --collect-only -q tests\test_mcp_server.py
tests/test_mcp_server.py::TestToolInventory::test_exactly_three_tools
tests/test_mcp_server.py::TestToolInventory::test_a_missing_tool_would_be_caught
tests/test_mcp_server.py::TestNoWriteCalls::test_no_write_named_calls_anywhere_in_the_file
tests/test_mcp_server.py::TestNoWriteCalls::test_every_open_is_read_mode
tests/test_mcp_server.py::TestSubprocessIsPinned::test_exactly_one_subprocess_call
tests/test_mcp_server.py::TestSubprocessIsPinned::test_argv_prefix_is_pinned
tests/test_mcp_server.py::TestSubprocessIsPinned::test_status_path_constant_points_at_the_real_file
tests/test_mcp_server.py::TestSubprocessIsPinned::test_stdin_and_timeout_are_pinned
... (中略 22 支) ...
tests/test_mcp_server.py::TestLiveStdioServer::test_status_all_returns_over_the_wire
tests/test_mcp_server.py::TestLiveStdioServer::test_ticket_over_the_wire_is_the_negative_control
tests/test_mcp_server.py::TestLiveStdioServer::test_friction_over_the_wire_is_the_negative_control

34 tests collected in 0.45s

> python.exe -m pip show mcp
Name: mcp
Version: 1.29.1
Summary: Model Context Protocol SDK
Location: <淨室 venv>\Lib\site-packages
Required-by:

> python.exe -m pytest -q tests\test_mcp_server.py
..................................                                       [100%]
34 passed in 17.08s
```

> ⚠ **F-116:遮了就不得再自稱原始。** `Location:` 那一行與三條指令的
> 直譯器絕對路徑原本是 scratchpad 底下的完整路徑(含使用者名),已遮成
> `<淨室 venv>` / `python.exe`。**版本、條數、耗時、測試名一字未動**;
> 中略的 22 支是為了篇幅,`--collect-only` 的總數 `34` 就是完整清單的長度。

### 🟡 淨室裝到的是 **1.29.1**,不是 1.27.0 —— 這一格比預期的更有用

`pip` 照 `"mcp>=1.27,<2"` 自己解到區間內最新的合規版。

**所以現在區間裡有兩個版本各自實測過全綠**:

| 版本 | 環境 | 口徑 |
|---|---|---|
| `1.27.0` | 桌機 | **既有安裝**(`mcp-server-duckdb` 帶進來的) |
| `1.29.1` | 淨室 venv | **照這份宣告解出來的** |

**兩者的口徑不同,要分開記**:後者才證得出「**宣告本身可用**」,
前者只證得出「這台機器上剛好有的那一版可用」。
**票 101 全程用的是前者,而前者證不出 CI 會不會過** —— 這正是十三之二的成因。

**附帶效果**:1.29.1 已經很靠近區間右端,它全綠 ⇒ **`<2` 擋掉的是 2.x 那個
已知不同的 API,不是順手把還能用的版本一起關在外面**。
上限畫在哪裡這件事,本來只有「2.x 已知不同」這個反面理由,
**現在多了一個正面的**:右端附近是通的。

⚠ **裁 1 的措辭要跟著校正**:裁 1 說「**照 1.27.0 寫**」。
實作面仍然成立(`FastMCP` 面在 1.27–1.29 都在),
但「我們跑的是 1.27.0」這句話**從今天起只對桌機成立** ——
CI 與任何新淨室都會拿到 1.29.x。**票面不改裁 1 的原文**(F-036),
在這裡記一行:**執行版本是一個區間,不是一個點。**

### 十三之六、修法

`pyproject.toml` 的 `[project.optional-dependencies].dev` 加 `"mcp>=1.27,<2"`,
`[tool.monkeyleash]` 加 `mcp-ceiling-review = "2026-10-31"`。

**上限 `<2` 的理由與 pytest 那條方向相反**:

| | pytest `<10` | mcp `<2` |
|---|---|---|
| 上限守的是 | **已知好的邊界**(9.x 實測全綠,10.x 沒人跑過) | **已知壞的邊界** |
| 證據 | 兩台機器在 9.x 全綠 | 官方 quickstart 已改成 `MCPServer` + `httpx2`,而 1.27.0 的 `__all__` 裡**沒有** `MCPServer`(第三節實測)⇒ **API 已知不同,2.x 零證據** |
| 複審日 | `2027-02-15` | `2026-10-31` |

**複審日差這麼多是刻意的**:pytest 的上限在等「新大版本出來、有人去試」,
**而 mcp 的上限在等一張已經開好的候選票**(升 2.x),那張票有具體內容 ——
換 import 面、換 HTTP 客戶端。**一個等外界、一個等自己,後者不該給同樣長的繩子。**

`tests/test_dependency_ceiling.py` 照票 34 體例照顧新的一格,
但**不是複製一份**:三條測試改成 parametrize 過一張 `CAPPED` 清單。
理由是**同缺陷的兩份實作必然漂開**(`F-058` 家族)——
複製一份會得到兩組語意相同的實作,改了一組忘了另一組,而兩組都還是綠的。

⚠ **代價明寫**:parametrize 之後 test id 從 `test_x` 變成 `test_x[pytest]` /
`test_x[mcp]`,而**舊 id 出現在 `.dev/test-runs.jsonl` 的歷史 `failed_tests` 裡,
那些不會回頭改** —— 查舊紀錄的人會找不到現在的名字。
本檔在 manifest 標 `skip`,所以影響只在上游。

另外把版本查法從 `pytest.__version__` 換成 `importlib.metadata.version(name)`:
`__version__` 是**模組自己說的**,中繼資料是**安裝器寫的**,
而這條測試守的正是「宣告」與「實際裝的」對不對得上 ——
**要問安裝器那一側,不能問被裝的東西自己**(`F-153`)。

### 十三之七、⚠ 順帶照出的一格(**本票不修,另開候選**)

R7 的 `BASH_ALLOWED_CMDS` 有 `"pip"` 與 `"python -m pip"`,
理由欄寫著「套件管理器寫 `.venv`,不是本 repo 的來源」——
**意圖明確包含 venv,而實作恰好擋掉所有 venv 內的呼叫**:
比對是「這一段是否以指令名開頭」(`gate.py:434-440`),
而用 venv 一定要走絕對路徑 `<venv>/Scripts/python.exe`,對不上任何前綴。

**這與「前綴要帶邊界」是鄰居,但方向相反** ——
不是漏放行了危險的東西,是**擋掉了理由欄明說要放行的東西**。

**本票不修**:改 `gate.py` 白名單是動閘門,要單獨一票、單獨紅燈、單獨驗收。
**到期條件**:下一次有人要在 venv 裡跑淨室驗證的時候(**這一次已經發生過一次了**)。

---

## 附:立案時的計數(**帶單位,帶基準**)

- 票檔:`docs/tickets/framework-updates/` **99 個 `.md` 檔**,票號範圍 **01–100**,
  解析出 **99 個相異號** ⇒ **缺 1 個號**。實測缺的是 **12**
  (`ls | grep -E '^0*12'` → 0 命中)。**缺號合法**(`CLAUDE.md` R9 只查重複不查連號)。
- 本票號 **101** = 立案動手當下重查的最大號 100 加一。
- 基準 commit:`3523500`,工作樹乾淨(`git status --porcelain | wc -l` = 0)。
