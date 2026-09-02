# 票 99:`status` 是 repo 證據的 projection —— 算出來,不存起來

**狀態**:**implement**(2026-09-02 立案即動工)

**時鐘**:**三個工作天**。

| Day | 日期 | 內容 |
|---|---|---|
| **Day 1** | 2026-09-02 | 開票(本檔)+ **紅燈先行**(兩筆,見第八節) |
| **Day 2** | — | **單 repo v1**:五段輸出骨架跑得出來 |
| **Day 3** | — | `--all` 跨三 repo + 驗收(第九節) |

**MCP 不在本票。** 本票只做到「設計介面」那一步(判準九),**不實作**。

---

## 一、缺陷 / 動機

**一個沒看過這個 repo 的總指揮,無法只靠貼上來的東西正確說出現況。**

現況散在至少七個位置:`.dev/pipeline.json`(停在哪一站)、`git status` / `rev-list`(樹況與遠端差距)、
`.dev/` 底下三本帳(豁免、測試紅綠、攔截)、`.claude/settings.json`(前哨設定)、
`~/.claude/`(G1 與上游錨)、票檔的狀態行、`docs/agents/friction-log.md`(最大號)。
**沒有任何一個東西把它們合起來算一次。**

於是要問「現在什麼狀況」,只能靠人**逐個貼**;而貼的人決定貼什麼,
**沒貼的那一格看起來跟沒問題一樣**。

### 兩個標本 —— 兩件都是「沒有東西在算現況」

| | 事實 | 為什麼沒人知道 |
|---|---|---|
| **一** | 9/1 那次 `sync` 從 **8/29 壞到 9/1**(鬆的發號標題判準把散文標題當號碼,票 98) | `sync` 是**要跑才會叫**的東西。三天之內沒有人跑它,而**沒跑跟跑過沒事長得一樣** |
| **二** | `.dev/gate-exemptions.jsonl` 末筆 `"ticket": "82"`、`"ts": "2026-08-31T09:43:19"` —— **蓋在 82 的章,而 8/31 在做的是 98** | 帳本記的是「當時 `pipeline.json` 寫什麼」。票號沒切,章就蓋錯,而**帳本不會覺得奇怪** |

第二件的形狀要記清楚:**那不是帳本壞了,是帳本忠實記下了一個沒有人在看的欄位。**
加一條「票號必須正確」的規則救不了它 —— 救它的是**有東西會把那個號印出來給人看**。

**本票不修這兩件。** 本票做的是那個「會把現況印出來」的東西。

---

## 二、九條設計判準(來源:**2026-09-01 三方收斂**)

逐條抄,不改寫:

1. **projection 不存。** `status` 每次都從 repo 現場重算,**不產生 state 檔、不快取**。
   存起來的現況會過期,而**過期的現況看起來跟現況一模一樣**。
2. **只呼叫 `gate.py`,不重述它。** 判準的權威在 `gate.py`;`status` 是 consumer。
   任何「`status` 自己也算一次」的東西都會與權威層漂開(`F-058` 家族)。
3. **每一行帶來源。** 格式 `<欄>: <值>  (source: <檔或指令>)`。
   沒有來源的行不得印 —— 讀的人要能自己回去查那一格。
4. **算不出來就寫「未記錄」,不寫 PASS。** 缺檔、缺欄、讀失敗一律「未記錄」。
   **把「我沒看到」印成「沒問題」是 fail-open,而且是最難察覺的那一種。**
5. **規則不做靜態 PASS。** `status` **不重跑**任何規則來宣告它綠;
   它只印**帳本裡有什麼**與**從帳本推導得出什麼**。
   一個沒有被觸發過的規則,`status` 對它的正確答案是「本期無紀錄」,不是「通過」。
6. **Enforcement Health** 四行:**Authority(pre-commit)/ Outpost(agent hook)/ G1 / Skill mirror**,
   **各自帶來源**。
7. **Sync Health 進 `--all`**(單 repo 模式不印 —— 單 repo 答不出「跟誰比」)。
8. **`--all` 跨三 repo。**
9. **MCP 不做,只設計介面。**

---

## 三、Day 1 偵察結果與**六裁**

Day 1 為**零寫入唯讀偵察**(結果原文見第十節附錄)。六項裁決逐字如下:

### 裁 A —— 「當前 stage 允許寫 src 嗎」要有一支具名函式

在 `gate.py` 抽一支具名函式(從 `check()` 的 `:1870` / `:1891` inline 抽出,
`check()` 改呼叫它);**`status` 只呼叫**。
**紅燈 = 函式不存在。** 既有 R2 測試守行為不變。

> 現況(Day 1 量到):`gate.py` **沒有** `allows_src_write` 這支函式 ——
> 它是 `pipeline-stages.yaml` 的欄位,判定邏輯 inline 在 `check()` 內:
> `:1870  writable = {s["id"] for s in stages if s.get("allows_src_write")}`
> `:1891  first_writable = next((i for i, s in enumerate(stages) if s.get("allows_src_write")), len(ids))`
> 要問「這一站允許什麼」,目前只能拿候選路徑一條一條餵 `check()` ——
> 那等於讓 `status` 自己組一份判定,**違反判準 2**。

### 裁 B —— 票面狀態行**不分類**

只印**當前票那一行原文** + 來源(檔:行),與 **「有狀態行 N / 無 M(未分類)」** 兩個數。

> 實測(Day 1):`grep -rh "^\*\*狀態\*\*"` 得 **57 行**,而票檔 **97 個** ——
> 差 40。值域 **≥ 21 種寫法**(`done` / `已落地` / `完成` / `candidate` / `立案` /
> `收尾` / `implement` / `部分落地` / `放行動工` …,中英混用、粗體位置不一),
> 且 **2 行是跨行截斷的**(`第一階段完成(已推,commit a6473a2 為止);` 與
> `done(2026-08-25 收窗;第四次 cp + 對帳落地後二度收窗,`)—— 單行 grep 抓不完整。
>
> **在這個值域上做分類器,產出的是一個誰都驗不了的東西。**
> 統一值域**登記 candidate,不在本票**。

### 裁 C —— 住處與 `--all` 的機制

住 `.claude/portable/status.py`(manifest 標 **`copy`**)+ `tests/test_status.py`(**`copy`**)。
per-root:把 `<root>/.claude/hooks` 插進 `sys.path` 再 `import gate`;
`--all` 用 **subprocess 逐 root 跑同一支**,**各 repo 的 `gate.py` 自己答**。

> 理由:`gate.py` 的 `ROOT` 是從 `__file__` 往上三層推出來的模組層常數。
> 在 A repo 裡 import B repo 的 gate,`ROOT` 會指到 A —— **而那個錯是靜默的**。
> subprocess 讓每個 repo 的 gate 在自己的樹裡回答自己的問題。

### 裁 D —— Outpost 與 G1 兩行**同形**

兩行都寫 **`config resolves from <根> / mounted: 未證明`**。

**`$CLAUDE_PROJECT_DIR` 在 shell 未設定不是證據**(hook 由 harness 起,環境不必然是我這個 shell)。

> Day 1 實測:`.claude/settings.json` 的 PreToolUse 指令是
> `python "$CLAUDE_PROJECT_DIR/.claude/hooks/gate.py"`,
> 而 `printenv CLAUDE_PROJECT_DIR` **exit=1**(未設定)、PowerShell `$env:CLAUDE_PROJECT_DIR` 空。
> 檔案在根底下**存在**(`ls` 到 155138 bytes),但那只證明「檔案在」,
> **不證明 hook 執行時那個變數解到這個根**。
>
> 所以這兩格的正確輸出是**未證明**,不是 `MOUNTED`,也不是 `NOT MOUNTED`。
> **「我這裡看不到」與「它不在」是兩件事,而前者印成後者會讓人去修一個沒壞的東西。**

### 裁 E —— Sync Health 的「落後幾刀」怎麼算

**下游 `provenance.jsonl` 末筆的上游 commit → `rev-list` 到上游 HEAD。**
**無 `provenance` 印「未記錄」。**

> Day 1 量到:`sync.py` **沒有**任何算 commit 距離的函式
> (`head_commit` / `_sha_at` / `in_commit` 判的是「是不是同一個物件」,不是差幾刀);
> 上游錨在 `gate.read_upstream_root()`(`gate.py:1561`,讀 `~/.claude/` 的 `UPSTREAM_ROOT=`)。
> 而**本 repo(上游)`.dev/provenance.jsonl` 不存在** —— 上游本來就不該有,
> 所以這一格在單 repo 模式必然是「未記錄」,那是**正確**不是缺陷(呼應判準 7)。

### 裁 F —— 讀帳本要容錯

讀帳本容錯,**缺欄印「未記錄」**;
欄位清單**取自各帳末行**,**全檔是否同欄未驗(登記)**。

> Day 1 的欄位清單來自 `tail -n 1`,**不是全掃**。舊行可能少欄或多欄。
> 這一句寫進票面是為了讓它有主詞 —— **不寫的話它會變成一句沒有人負責的「之後再驗」。**

---

## 四、五段輸出骨架(v1)

每行格式:`<欄>: <值>  (source: <檔或指令>)`

```
=== Repository ===
root:            <路徑>                      (source: git rev-parse --show-toplevel)
branch:          <名>                        (source: git rev-parse --abbrev-ref HEAD)
head:            <sha>                       (source: git rev-parse --short HEAD)
tree:            clean | <N> 筆              (source: git status --porcelain)
ahead/behind:    <A>/<B>                     (source: git rev-list --left-right --count)

=== Enforcement Health ===
authority:        <最後一筆 at_commit=true 的 ts | 未記錄>
                                             (source: .dev/gate-exemptions.jsonl)
authority config: core.hooksPath=<值>; pre-commit 存在=<是|否>; installed: 未證明
                                             (source: git config core.hooksPath)
outpost:         config resolves from <根> / mounted: 未證明
                                             (source: .claude/settings.json)
g1:              config resolves from <根> / mounted: 未證明
                                             (source: ~/.claude/settings.json)
skill mirror:    <值 | 未記錄>               (source: gate.mount_violations_cached())

=== Evidence ===
exemptions:      <N> 筆, 末筆 ts=<...> ticket=<...>
                                             (source: .dev/gate-exemptions.jsonl)
test-runs:       <N> 筆, 末筆 <file>=<result> ticket=<...>
                                             (source: .dev/test-runs.jsonl)
intercepts:      <月>=<N> 筆 | 本月無紀錄     (source: gate.intercept_path(<月>))
provenance:      未記錄                      (source: .dev/provenance.jsonl)
shadow:          未記錄                      (source: .dev/shadow.json)

=== Ticket ===
stage:           <stage>                     (source: gate.load_stage())
feature:         <feature>                   (source: gate.load_feature())
ticket_id:       <id | null>                 (source: gate.load_stage())
status line:     <當前票那一行原文>          (source: docs/tickets/<f>/<n>-*.md:<行>)
status coverage: 有 <N> / 無 <M>(未分類)    (source: grep -c "^\*\*狀態\*\*")

=== Derived ===
src writable:    <bool>                      (source: gate.<裁 A 那支函式>())
max ticket:      <N>                         (source: ls docs/tickets/<feature>)
max friction:    <F-NNN>                     (source: docs/agents/friction-log.md)
rules defined:   <排序後的 R 代號>           (source: gate.rule_codes())
```

**`--all` 追加一段**(判準 7):

```
=== Sync Health (--all) ===
<repo>: 落後 <N> 刀(自 <上游 commit>)      (source: <repo>/.dev/provenance.jsonl 末筆 + rev-list)
<repo>: 未記錄                              (source: <repo>/.dev/provenance.jsonl 不存在)
```

---

## 五、**不做**

1. **MCP** —— 只設計介面,不實作。
2. **狀態行值域統一** —— 登記 candidate(裁 B)。
3. **多 agent** —— 本票是一支可跑的程式,不是編排。
4. **`state.json`** —— 違反判準 1,明確不做。
5. **`Skill mirror` 以外的新判準** —— `status` 不新增任何規則。

---

## 六、紅燈紀律

**本票的紅燈必須記在本票號(99)下。**
動工前 `pipeline.json` 由 **Jeff** 切到 `implement` / `99` ——
**agent 不動那個檔**(第一節標本二正是「號沒切,章蓋錯」)。

紅燈**兩筆**:

| # | 紅燈 | 形狀 |
|---|---|---|
| **1** | `tests/test_status.py` **collection red** | 檔在、`import status` 失敗(模組不存在)。**先例:票 98 的 `8c2d555`** |
| **2** | `tests/test_gate.py` 對裁 A 那支具名函式 **AttributeError red** | `getattr(gate, "<名>")` 不存在 → red。函式抽出後轉綠 |

**⚠ 兩筆都是「結構紅」,不是「行為紅」。** 票 98 票面已記過同一件事:
結構紅只證明**東西還沒有**,不證明**它做對了**。行為紅要等 Day 2 有第一個真值可比。

---

## 七、驗收(Day 3)

**找一個乾淨視窗當受試者**,只貼 `status` 輸出(**不貼別的、不解釋**),問它五題:

1. 現在停在哪一站?
2. 當前票是哪一張?
3. 樹況?
4. 上游落後幾刀?
5. 前哨在不在?

記**答對幾格**。

> **答錯的格是 `status` 的缺陷,不是受試者的。**
> 這一句是本節的全部重點:驗收物件是輸出,不是人。
> 受試者說不出來 = 那一格沒印、印得不清楚、或印了一個他無從判斷的值。
>
> 第 4、5 題預期會是「未記錄 / 未證明」(裁 D、裁 E)——
> **受試者答「未記錄」算對**;答「沒問題」算錯,答「壞了」也算錯。

---

## 八、Day 1 偵察附錄(關鍵原文)

零寫入唯讀偵察,2026-09-02 08:15–08:26。以下為原始 stdout 節錄。

### ⓪ 根

```
$ pwd
/c/projects/agent-gates
$ echo $CLAUDE_PROJECT_DIR
(no output)
$ printenv CLAUDE_PROJECT_DIR
(Exit code 1)
$ git rev-parse --show-toplevel
C:/projects/agent-gates
```

### ① `load_stage` / `load_feature` 回值

```
$ python -c "...; import gate; print(gate.PIPELINE); print(gate.load_stage())"
C:\projects\agent-gates\.dev\pipeline.json
('idle', None)
$ ... print(gate.load_feature())
framework-updates
$ python -c "print(list(open('.../pipeline.json','rb').read()[:4]))"
[123, 10, 32, 32]        # = "{\n  " → 無 BOM
$ git status --short
(empty)
$ git rev-list --left-right --count origin/master...HEAD
0	0
$ git rev-parse --short origin/master
fa1c34a
```

`load_stage()` 回 `(stage, ticket_id)` tuple;讀不到回 `(UNREADABLE_STAGE, None)`,**不回 `"idle"`**。

### ② `settings.json` 那一行

```
"command": "python \"$CLAUDE_PROJECT_DIR/.claude/hooks/gate.py\""
matcher:   "Write|Edit|MultiEdit|NotebookEdit|Bash|PowerShell"

$ ls -la "C:/projects/agent-gates/.claude/hooks/gate.py"
-rw-r--r-- 1 user 197121 155138 Aug 31 17:40 .../gate.py
```

### ④ `.dev` 三本帳的行數 + **缺席的五個檔**

```
$ wc -l .dev/gate-exemptions.jsonl     → 163 行
$ wc -l .dev/test-runs.jsonl           → 7877 行
$ wc -l .dev/intercepts-2026-08.jsonl  → 1 行
$ ls .dev/intercepts-2026-09.jsonl     → No such file (尚無 9 月攔截,非錯誤)
```

**磁碟上不存在、但 `gate.py` 有常數的五個**:
`provenance.jsonl`、`shadow.json`、`shadow-log.jsonl`、`intercepts.jsonl`(基底)、`intercepts-summary.jsonl`。

欄位名(**取自各帳末行,全檔未驗** —— 裁 F 登記):

| 檔 | keys |
|---|---|
| `gate-exemptions.jsonl` | `ts, file, module, ticket, stage, declared_in, reason, tool, outcome, blocked_by, at_commit, content_hash, result_hash, changes_bytes` |
| `test-runs.jsonl` | `test_file, time, result, failed_tests, impl_file, impl_exists, impl_hash, ticket_id` |
| `intercepts-2026-08.jsonl` | `ts, rule, at_commit, cmd_sha256, cmd_verb, cmd_len, message` |

**標本二的原文**(第一節):

```
$ tail -n 1 .dev/gate-exemptions.jsonl
{"ts": "2026-08-31T09:43:19.318024+00:00", "file": ".claude/hooks/gate.py",
 "module": "gate", "ticket": "82", "stage": "implement", ...}
```

### ④之二 狀態行 **57 / 排程行 23**

```
$ grep -rh "^\*\*狀態\*\*" docs/tickets/framework-updates   → 57 行
$ grep -rh "^\*\*排程\*\*" docs/tickets/framework-updates   → 23 行
```
票檔 97 個 → **40 張沒有行首狀態行**(或狀態行不在行首)。

### ⑤ **票 89 不是 stale-status 檢查**(前提不成立)

票 89 = 「三條散文規矩上機器」:`.dev/shadow.json` 在上游必須不存在(權威層)/
`KNOWN_GAPS` 每項要有票號(測試層)/ `0013` 起 ADR 要用 `F-` 前綴(測試層)。
**沒有一條讀票面狀態行。**

```
$ grep -rn "docs/tickets" --include=*.py .claude tests scripts
.claude/hooks/gate.py:1100:TICKET_DIRS = (".scratch/%s/issues", "docs/tickets/%s")
(其餘皆為註解或測試 fixture)
```

唯一讀票檔的生產程式碼是 `ticket_untested_modules()`(`gate.py:1213`)+
`declared_untested()`(`:1105`),它們只認 `**Untested by decision:**` 前綴 ——
**借不到**。可複用的是**紀律**(`TICKET_DIRS` 兩個位置都算、綁 HEAD 不綁磁碟),不是函式。

### ⑥ 最大號

```
最大票號:98    (票檔 97 個,編號 01–98,缺 12)
最大 F- 號:F-154 (docs/agents/friction-log.md:6184;共 154 個發號標題,號碼不重複)
```

`docs/friction-log.md` **不存在** —— 正典路徑是 `docs/agents/friction-log.md`,
與 `gate.py:1274` 的 `FRICTION_LOG` 常數一致。

---

## 九、待辦登記(**不在本票**)

| # | 內容 | 出處 |
|---|---|---|
| 1 | 票面狀態行值域統一 | 裁 B |
| 2 | 帳本欄位「全檔是否同欄」全掃驗證 | 裁 F |
| 3 | MCP 介面實作 | 判準 9 |

**這三條寫在這裡是為了讓它們有出處,不是為了讓它們被記得。**
要被記得得開票 —— 而本票**不代開**。

---

## 十、Day 2 落地(2026-09-02)

兩刀:`4094439`(gate 抽函式)+ 第二刀(`status.py` v1)。

### 十之一、⚠ 前面幾節裡被 Day 2 推翻或更正的東西

**`F-036` 體例:舊文不刪,錯在哪寫在旁邊。**

| 位置 | 舊文 | 實際 | 為什麼要記 |
|---|---|---|---|
| 第四節骨架 | ~~`authority: <installed \| 未記錄>  (source: .git/hooks/pre-commit)`~~ | 拆成 `authority`(帳本 ts)+ `authority config`(`core.hooksPath`) | `.git/hooks/` **不進版控、clone 不帶走**,拿它當唯一來源在每個下游都印同一個答案。**能證明權威層跑過的是帳本**,不是設定檔 |
| 第八節 | 「紅燈兩筆」的條數寫 **7 + 4** | **9 + 5** | 我數錯了。`status` 9 條(c、g 各拆正控/負控),`gate` 5 條(甲拆兩條)。**commit 訊息 `a20bfca` 裡的 7+4 已進歷史,不 amend** |
| 第三節裁 C | 「住 `.claude/portable/status.py`(manifest 標 `copy`)」 | **不需要加行** | `.agents/portable-manifest.txt:64` 的 `.claude/portable/  copy` 是目錄級標記,最長前綴者勝。實測 `manifest.mark_for('.claude/portable/status.py')` → `'copy'`、`explicit_mark(...)` → `'copy'`(非 DEFAULT 落底)。**加一行冗餘標記等於製造第二個要維護的位置** |
| 第十節之外 | 「manifest 在 `.claude/portable/portable-manifest.txt`」(Day 2 指令) | **`.agents/portable-manifest.txt`** | 前者不存在 |

### 十之二、Day 2 加的設計決定(票面原本沒有)

| # | 決定 | 為什麼 |
|---|---|---|
| 1 | **`status.load_gate(root)` 是公開接縫** | 判準 2 說「只呼叫不重述」,而**「有沒有真的去呼叫」從輸出看不出來** —— 偷讀 `pipeline.json` 的實作印出的字一模一樣。`TestStageComesFromGate` 換掉它、看輸出跟著變 |
| 2 | **不讀 `~/.claude/`** | G1 掛使用者層,而使用者層不屬於任何 repo。讀了會讓同一份輸出在不同機器上意義不同,**而讀的人分不出來**。所以 `g1` 那行恆為未證明 |
| 3 | **`skill mirror` 走 `skill_mirror_violations()`,不走 `mount_violations_cached()`** | 後者會寫 `.cache/mount-check.json`(`gate.py:2791`),違反判準 1(projection 不存)。**一支「看一下現況」的工具不得留下檔案** |
| 4 | **讀票面時 `rstrip("\r\n")`** | 工作樹在 Windows 是 CRLF(`git add` 每次都警告)。不去掉的話輸出多一個看不見的字元,**而比對狀態行原文的人看不出那是行尾** |
| 5 | **`status coverage` 兩個票位置都算** | 見下 |

### 十之三、實跑抓到的一個缺陷(本輪修掉)

第一次實跑印:

```
status coverage: 有狀態行 0 檔 / 無 0 檔(未分類)  (source: .scratch/framework-updates/issues)
```

成因:`gate.TICKET_DIRS` 兩個位置,我取**第一個存在的**;而 `.scratch/framework-updates/issues`
存在但是**空的**,票在 `docs/tickets/`。

**要緊的不是數字錯,是錯的樣子。**「有 0 / 無 0」與「真的一張票都沒有」**逐字相同** ——
而 source 欄印出了那個空目錄的名字,是**唯一**露出破綻的地方。
**這正是判準 3 存在的理由:帶來源的那一格自己說出了它讀錯了地方。**

修法:兩個位置都算。修後 `有狀態行 58 檔 / 無 40 檔`,合計 98 檔 ——
與 Day 1 的「97 檔 / 57 行」對得上(本票 99 是第 98 檔、第 58 條狀態行)。

### 十之四、⚠ 負控空轉(誠實記下)

Day 2 指令的負控是「把 `.dev/intercepts-2026-08.jsonl` 移出 repo 再跑一次,
`intercepts` 行必須變成未記錄」。實跑結果:**輸出逐字未變**。

**它不是失敗,是空轉** —— `status` 讀的是**當月**(`2026-09`),
而 `.dev/intercepts-2026-09.jsonl` 本來就不存在,那一行在移動前後都是
「無當月攔截(檔不存在)」。**一個不可能失敗的控制證明不了任何事。**

sha256 前後相同(`0802c800bb78044e21299a3f213786a73bd7ca1319fffe42a384345105b6ab70`),無資料變動。

**真正能失敗的負控在 `tests/test_status.py`**:
`test_present_ledger_is_not_unrecorded`(帳本在 → 不得還是未記錄)與
`test_authority_line_cites_the_commit_time_record`(有 `at_commit=true` → 要指得出那一筆)。
兩條都跑在 `tmp_path` 造的 root 上,**檔案有無由測試自己控制**,所以它們會紅。

### 十之五、Day 2 量到的一件事:**前哨與權威層都在**

Day 1 那兩格是「未證明」,而 Day 2 的第一刀留下了痕跡:

```
$ grep "\"ticket\": \"99\"" .dev/gate-exemptions.jsonl   # 4 筆
tool=Edit       at_commit=false   × 3   ← 前哨(PreToolUse)在跑
tool=pre-commit at_commit=true    × 1   ← 權威層在跑
```

commit 當下 stdout 也印出了 `[R2/自我修改豁免] .claude/hooks/gate.py:…`。

**這不推翻裁 D。** 裁 D 管的是**設定**那一半(「設定解得到什麼」不等於「hook 跑的是它」),
而帳本管的是**動作**那一半。兩者都印,值不同,來源不同 ——
`mounted: 未證明` 與 `authority: <ts>` 同時成立,不矛盾。

**Day 3 待議**:`outpost` 要不要比照 `authority` 也加一行帳本證據
(`tool=Edit` 的豁免紀錄就是前哨跑過的痕跡)。**本輪不做** ——
`test_outpost_line_is_never_a_verdict` 釘的是設定那一行,加新行不影響它,
但那是新判準,要先裁。
