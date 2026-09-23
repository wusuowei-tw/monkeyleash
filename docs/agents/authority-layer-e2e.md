# 權威層端對端驗證 —— 操作說明

**這份文件存在的理由**:票 138 的命題逐字是
「權威層端對端驗證**需要人工步驟,而該步驟沒有被寫下來**」。
**寫一支腳本不等於寫下來** —— 下一個人要知道的是**為什麼**這樣做,
否則他會在正式 repo 裡直接試,然後撞上一串看不懂的紅燈。

> **位置為什麼在 `docs/agents/` 而不是 `docs/adr/`**
> `docs/adr/` 記的是**決策**(為什麼選 A 不選 B,以及當時的取捨);
> 本文是**操作程序**(要做哪些動作、怎麼判讀結果)。
> `docs/agents/` 已經住著同性質的 `issue-tracker.md` 與 `domain.md`。
> 裁決本身(六格全做、B 輪不做、#12 只標接線)留在**票 133 / 138 的票面**,
> 本文只引用,不重新裁決。

> **可攜性**:`.agents/portable-manifest.txt` 把本文標 **`skip`**。
> 理由:它依賴 `scripts/e2e_authority_layer.py`(同樣標 `skip`),
> 而且引用了下游沒有的票號。**一份指向下游不存在的東西的說明,比沒有說明更糟。**
> 實跑並驗收之後再評估要不要改 `copy`。

---

## 一、為什麼要 clone,為什麼不能在正式 repo 跑

### 1.1 為什麼不能在正式 repo 跑

這個驗證的內容就是**「造一個違規,真的下 `git commit`,看它被不被擋」**。

| 在正式 repo 做會怎樣 | |
|---|---|
| **違規語料要進 index** | 一旦某個案例**意外提交成功**,違規內容就**進了正式歷史** —— 而那正是這個驗證想找出來的情況。**最不該發生的事,恰好是它最可能發生的地方。** |
| **控制檔要被改** | 案例要改 `.agents/pipeline-stages.yaml`(index 版)、`.agents/legacy-no-redlight.txt`(工作樹版)、`.dev/pipeline.json`。在正式 repo 改這些,等於在驗證期間**把正式閘門的判準換掉**。 |
| **`.dev/gate-exemptions.jsonl` 會被寫** | 它**有追蹤**。hook 每跑一次就往裡面追加,正式帳本會混進一批「不是真的在做事」的紀錄,而**帳本的用途就是逐筆對帳**。 |
| **工作樹乾淨是好幾條紀律的前提** | 票根要記 `git status --porcelain` 為 0、推送前三條件都看它。驗證途中它不可能是乾淨的。 |

### 1.2 為什麼**每個案例**一個 clone,而不是 reset

直覺的做法是「跑完一個案例就 `git reset --hard` + `git clean -fd`」。**那不夠。**

**`clean -fd` 預設不碰 ignored 檔案**,而本驗證的控制輸入**幾乎全是 ignored 的**:

| 控制輸入 | 狀態 | reset/clean 清得掉嗎 |
|---|---|---|
| `.dev/pipeline.json` | ignored | ❌ |
| `.dev/provenance.jsonl` | ignored(**本 repo 根本沒有這個檔**) | ❌ |
| `.dev/shadow.json` | ignored | ❌ |
| `.claude/skills/`、`/skills/` | ignored | ❌ |
| `.dev/gate-exemptions.jsonl` | **有追蹤** | ✅(所以 hook 寫進去的行會被還原) |

⇒ **只靠那兩條命令宣稱「已完全重置」是假的**,而殘留的控制檔會讓**下一個案例
用到上一個案例的前提**,結果看起來正常。
所以腳本**直接換一個 clone**:每個 clone 的可變狀態由 `prepare_clone()`
**逐項建立**,清單寫在該函式的註解裡。

⚠ 附帶但重要:`.dev/gate-exemptions.jsonl` **有追蹤** ⇒
**hook 追加的那幾行要在丟掉 clone 之前讀出來**,事後撈不到。腳本就是這樣做的。

### 1.3 為什麼 clone 完立刻移除 origin

```
git clone --no-hardlinks <official> <work>/clone
git -C <work>/clone remote remove origin
```

**「不向任何遠端推送」不該靠紀律,要靠構造。** 移掉 origin 之後,
`git push` 沒有預設目標;要推得先自己加回一個 remote,那是一個
**看得見的動作**,不是一個手滑。

`--no-hardlinks` 同理:預設的本地 clone 會**硬連結物件檔**,
clone 裡的操作理論上碰得到正式 repo 的物件。加這個旗標讓兩邊實體分離。

---

## 二、Jeff 的步驟

### 步驟 0 —— 先看上游錨(**只有人能做**)

```powershell
type $env:USERPROFILE\.claude\upstream-roots.txt
```

**為什麼要人做**:`~/.claude/` 在 G1 保護清單裡,**第一級不分讀寫**,
agent 讀它會被當場擋下(實測)。

**看什麼**:它應該是**恰好一行** `UPSTREAM_ROOT=<絕對路徑>`(`#` 註解與空行不算)。

⚠ **看到那一行只是格式初查。** **路徑名稱結尾不是 repo 身分證明** ——
一個叫 `...\agent-gates` 的目錄不保證是 git repo,也不保證有你要的那個 commit。
真正的確認由腳本在你的機器上做:它會問 `git rev-parse --git-dir`、
再問 `git show <SHA>:<path>` 讀不讀得到,**並且只印布林值與一個遮蔽過的識別碼,
不把完整路徑印出來、也不需要你貼到對話裡**。

⚠ **不修改真實上游設定。** 格式不合或物件讀不到 ⇒ #13 的三個案例標
**「前置條件未完成」並停止**,不是去改那個檔。

#### 「恰好一行」到底在算什麼(**已核對程式,2026-09-23**)

裁決者本人以 UTF-8 看過該檔,回報為**三行**:兩行 `#` 註解
(第一行註解自述規格為「恰好一行 `UPSTREAM_ROOT=<絕對路徑>`,正斜線,
由人手維護(machine-init 第 6 項)」;第二行記 2026-09-04 筆電原檔
遭誤覆蓋後重建)+ 一行 `UPSTREAM_ROOT=C:/projects/agent-gates`。

**這會不會被判成「多行」?不會。** `gate.py` 的 `read_upstream_root()`:

```python
for line in lines:
    line = line.split("#", 1)[0].strip()
    if not line:
        continue                       # ← 整行註解在這裡就被丟掉
    if line.startswith("UPSTREAM_ROOT="):
        ...
        vals.append(v)                 # ← 只有【賦值行】進 vals
    else:
        return None
return vals[0] if len(vals) == 1 else None   # ← 算的是 len(vals)
```

| 問 | 答 | 依據 |
|---|---|---|
| 註解行會被略過嗎? | **會** —— `split("#",1)[0].strip()` 把整行註解變成空字串,`continue` 掉 | 上面第 2–4 行 |
| 「恰好一行」算賦值行還是整檔行數? | **賦值行**(`len(vals) == 1`) | 上面最後一行 |
| 程式與檔內註解自述一致嗎? | **一致**。docstring 也逐字寫「`#` 註解與空行忽略」 | `read_upstream_root` docstring |

**合成核對**(⚠ **沒有讀真實檔案** —— 餵的是依上述描述重建的內容,
打進 `gate.py` 的**真函式**):

| 輸入 | 結果 |
|---|---|
| 2 行註解 + 1 行賦值(裁決者描述的形狀) | `'C:/projects/agent-gates'` ✅ |
| 只有賦值行 / 註解 + 空行 + 賦值 / 行尾註解 / 帶 BOM | 各自取到值 ✅ |
| **兩行賦值** / **零行賦值** / **認不得的行** | `None`(fail-closed)✅ |

⇒ **那個檔解析得出 `C:/projects/agent-gates`,#13 的上游前置在這一層成立。**
(**是不是 git repo、`commit:path` 讀不讀得到**,仍由腳本實問 —— 見上面那段。)

⚠ **邊界(不影響本案,但寫下來)**:截斷用的是**整行第一個 `#`**,
所以**路徑本身若含 `#` 會被截掉**。目前的值沒有 `#`。

⚠ **已知的重複位置**:`scripts/e2e_authority_layer.py` 裡有一份
`read_upstream_root()` 的**副本**(腳本不 import `gate.py`)。
本輪逐案比對過,兩份**每一格都一致**;但這是
**「同一個事實有兩個可寫的位置」**那個形狀 ——
`gate.py` 的解析哪天改了,副本不會跟著改,而且**不會有東西出聲**。
**本輪不動它**(改成 import 會把 `gate.py` 的 import 期副作用帶進腳本,
那是另一個決定),原地登記於此。

### 步驟 1 —— 跑腳本

見本輪回報附的那一行(固定 SHA、報告位置都在裡面)。

### 步驟 2 —— 讀摘要表

腳本最後印一張表:**格 / 案例 / 預期 / 實際 / 判定 / 證明力**。
完整證據寫進 `.dev/reports/<時戳>-authority-layer-e2e-roundA.md`。

---

## 三、判讀表 —— **哪些失敗「不算」規則擋下**

**這是本文最容易被跳過、而最會害人的一節。**
一個非零退出碼看起來都一樣;下面這些**全部不算**預期拒絕成功。

| 失敗樣態 | 判別字串 | 真正的意思 |
|---|---|---|
| 身分未設 | `Please tell me who you are` / `unable to auto-detect email` | git 不知道 commit 作者是誰 |
| 簽章失敗 | `gpg failed to sign` | 簽章設定問題 |
| 缺依賴 | `無法載入 yaml 套件` | PyYAML 不在那個 Python 裡 |
| 流程狀態讀不到 | `讀不到流程狀態` | `.dev/pipeline.json` 沒寫好 |
| 站別定義壞掉 | `站別定義不可用` | 構造把 YAML 寫成非法的了 |
| **影子模式開著** | `[六站閘門/影子]` | **整輪作廢** —— 閘門退成「只記不擋」 |
| 權威層沒接上 | `[權威層未安裝]` | `core.hooksPath` 沒設好 |
| 別的規則先擋 | 訊息裡的規則代號不是預期的那一條 | 構造撞到別的規則(例:#13 撞 R8) |

**處置一律相同:記為【未完成】,不記為通過也不記為失敗;停,保留輸出。**
腳本會自動判這幾條並標成「未完成」。

### 3.1 為什麼「非零 + HEAD 不變」不夠

**非零退出碼與 HEAD 不變,本身不證明是 hook 擋下的。**
上表每一條都會產生同樣的外觀。所以每個預期拒絕要**同時**滿足:

1. 非零退出碼;
2. `HEAD` 逐字不變(比 40 碼);
3. 訊息含 `[六站閘門/pre-commit] commit 已擋下`;
4. **`git trace2` 事件裡看得到 git 啟動 `pre-commit`**;
5. 訊息含該案例預期的規則代號與目標路徑;
6. 訊息**不含**該案例明列的禁止代號;
7. 暫存內容仍在 index(commit 被中止,不是被吃掉)。

### 3.2 追蹤證得到什麼、證不到什麼

腳本用 `GIT_TRACE2_EVENT`(git 自己的追蹤,**不修改受測程式**)記錄
`child_start` 事件,從中找 `pre-commit`。

| 這一層 | 誰證 |
|---|---|
| **git 真的啟動了那個 hook** | ✅ trace2 事件 |
| **跑的是哪一份 hook / gate.py / leak_scan** | ✅ 腳本記下三個檔的 `sha256` 與解析後的 hook 路徑 |
| **hook 內部走了哪一條規則** | ❌ trace2 證不到 —— 由**訊息內容**與**帳本新增行**承擔 |

⚠ **追蹤看不到就記 `False`,不補一個替代訊號。**

### 3.3 合法對照不要求帳本或警告

**不可要求每個合法案例都新增豁免帳本行或印個人清單警告** ——
正常執行**可能兩者皆無**(沒有用到豁免就不寫帳本;個人清單存在就不警告)。
合法對照的判準是:**rc=0 + HEAD 前進 + trace2 看到 hook**,三者。

---

## 四、意外提交成功的處置

**預期拒絕卻 `exit 0`** ⇒ **記為驗證失敗,而且是最重要的那一種。**

1. **不清理那個 clone。** 腳本偵測到就跳過清理,並印出絕對路徑。
2. **記下新 HEAD 的 40 碼 SHA** 與 `git show --stat`。
3. **不推送**(origin 已移除,構造上也推不了)。
4. **不重跑到綠為止。** 要再試就**另開一個案例編號**,兩次結果都留。

> 把它解釋成「大概是構造沒做對」然後重跑,是這一類驗證最常見的死法 ——
> 那等於用重試把一個真的訊號洗掉。

---

## 五、兩個格子的限制(**原文,不得改寫**)

### 5.1 #12 —— **只有【接線】,沒有【差異】**

#12 修的是「**讀端用哪一個常數取得帳本路徑**」:
舊碼 `os.path.join(ROOT, ".dev", "gate-exemptions.jsonl")`,新碼 `EXEMPTION_LOG`。
而 `EXEMPTION_LOG` 的定義(`gate.py:74`)**就是**
`os.path.join(ROOT, ".dev", "gate-exemptions.jsonl")`。

⇒ **正式配置下兩者逐字相同,真 hook 在任何構造下都給出一樣的答案。**
那個修法的價值在**測試隔離**(patch `EXEMPTION_LOG` 才擋得住讀端),
而**測試隔離依定義不在真 hook 的可觀測範圍內**。

⇒ **不替它捏「舊碼必放、新碼必擋」的案例。**
捏一個出來就得改受測程式或改 `ROOT`,兩者都被禁。
#12 的三個案例證明的是:**帳本索引 → 回頭驗 HEAD 裡的票**那條鏈
在真 commit 下真的被走到,且判準正確。**就只有這樣,不得寫成更多。**

### 5.2 #11② —— **真 hook 不可構造**

`staged_paths()` 用 `git diff --cached -z --name-only --diff-filter=ACM`,
**不在 index 的檔案根本不會進 `check()` 的清單**。

⇒ 「index 讀不到 ⇒ 不豁免、不提前返回」那一支,**在真 commit 路徑上造不出來**。
腳本用一個**靜態案例**記下它,限定措辭是:

> **靜態構造一個未暫存目標時,正常 `staged_paths` 不會選到它。**

⚠ **不概括成「真實流程永遠不可能發生 index 讀取失敗」** ——
`staged_blob` 回 `None` 有兩種可能(不在 index、**或 git 本身執行失敗**),
後者本節完全沒有涵蓋。該支的既有證據**維持在隔離層**,不由本驗證取代。

### 5.3 #8/#9 —— 黑箱結果的邊界

兩格的案例**可以驗證來源行為**(提交時點用的是 index 那一份定義)。
⚠ **不能單靠兩個案例宣稱「#8 與 #9 共用同一次讀取」** ——
那是**構造性質**,由 `check()` 裡只有一次 `load_stage_defs()` 呼叫
這件事本身、以及既有測試支撐,不是黑箱結果推得出來的。

---

## 六、合法對照為什麼長這樣(**別把它簡化掉**)

最容易犯的錯:合法對照建一個 `pkg/thing.py` 加一個**空的** `tests/test_thing.py`,
以為這樣就過 R3。**不會過。**

R3 有兩半,而它們**互相接手**:

| 情況 | 擋下的是哪一半 |
|---|---|
| 測試檔**不存在** | 前半 —— `找不到對應測試` |
| 測試檔**存在** | 後半 —— `redlight_missing` 要求一筆合格紅燈紀錄,而紀錄檔 `.dev/test-runs.jsonl` **是 ignored、clone 不帶** ⇒ `找不到紅燈紀錄檔` |

⇒ **一個全新的 `.py` 在 clone 裡沒有任何辦法自己通過 R3。**

所以每一格的合法對照都**走該格自己的豁免**,這也正是它該驗的東西:

| 格 | 合法對照用什麼 | 靠哪個豁免過 R3 |
|---|---|---|
| #8 / #10 | `.claude/hooks/redlight.py` 的無害改動 | **legacy 豁免**(它在清單裡,且確在 go-live 樹裡)⇒ R3 整條不適用,R2 照常 |
| #9 | `research/probe.py`,站別 `research` | **#9 的 `exempts_r3_in_scope`** |
| #11 | `pkg/__init__.py`,index 版是空的 | **#11 純套件標記** |
| #12 | `pkg/thing.py` + 帳本紀錄 + **已 commit 且列了該模組的票** | **#12 已記錄的票宣告** |
| #13 | `pkg/thing.py`,index 位元組 = 上游物件 | **#13 上游成品** |

### 6.1 #12 的票面格式(**照解析器,不是照函式名**)

解析器找的是**以這個字串開頭的那一行**:

```
**Untested by decision:** thing
```

常數是 `gate.py` 的 `_UNTESTED_PREFIX`。
⚠ **`declared_untested` 是函式名,不是票面欄位** —— 票裡不要寫那五個字。

而帳本那一筆的 **`declared_in` 是「票檔的 repo 相對路徑」**,不是票號:

```json
{"file": "pkg/thing.py", "module": "thing",
 "declared_in": "docs/tickets/framework-updates/900-e2e-probe.md", ...}
```

`logged_exemption_backed` 拿它去 `committed_declaration(rel_path)` →
`head_blob(rel_path)` ⇒ **那張票必須已經在 HEAD 裡**,工作樹有不算。

### 6.2 #8 的違規構造為什麼是「把可寫站往後搬」

提交時點的 R2 走的是**前置站**那一支:

```python
if gate_self:      pass
elif at_commit:    ...  # 只問「你是不是還停在前置站」
elif stage not in writable:  return "[R2] ..."   # ← at_commit 為真時**不會被評估**
```

⇒ 光把 `implement` 的 `allows_src_write` 拿掉**不會擋**。
必須讓 `implement` 落在**第一個可寫站之前**,所以構造是
**把 `allows_src_write` 從 `research`/`implement` 移到 `review`**。

### 6.3 #10 的違規構造為什麼不能 `git add` 那份清單

- `check()` 的 #10 明確傳 `path=LEGACY_LIST` ⇒ **讀工作樹**。
- R6 的 `check_legacy_list()` **不傳 path** ⇒ **讀 index**。

⇒ **只改工作樹、不 `git add`**,R6 看到的是乾淨的清單(不出聲),
而 #10 看得到那一筆假條目。**這是唯一能把 #10 與 R6 分開的構造** ——
一旦把清單也 `git add`,R6 會一起紅,案例作廢。

---

## 七、防誤用檢查(**不是安全證明**)

腳本把**所有** git 呼叫收進一個函式,它檢查**實際 argv 與 env**:

- 拒絕 `--no-verify`,以及 `git commit -n`(那個 `-n` 就是 `--no-verify`);
- 拒絕在指令層覆寫 `core.hooksPath`(`-c core.hooksPath=…`、`--config-env=…`);
- 拒絕 env 挾帶 `GIT_CONFIG*` / `GIT_DIR` / `GIT_WORK_TREE` / `GIT_INDEX_FILE`;
- 腳本**自己永遠不設** `core.hooksPath` —— 那一步只由 `sh bootstrap.sh` 做;
- 每次 commit **之前**再確認一次 `core.hooksPath` 仍是 `.githooks`。

⚠ **早一版的想法是「搜尋原始碼裡有沒有 `--no-verify` 字串」。那種自檢是假的** ——
它會命中檢查程式自己與這份說明文字。**要檢查的是那一次真的交給 git 的參數。**

⚠ **這是防誤用檢查,不宣稱能證明整支腳本安全。**
它涵蓋的只有經過那個函式的 git 呼叫;`sh bootstrap.sh` 那一步不在涵蓋內
(那一步由 bootstrap 自己的三道 fail-closed 負責)。

---

## 八、清理與「正式 repo 沒被動到」的正確措辭

### 8.1 刪除前的三道斷言

暫存目錄由 `tempfile.mkdtemp(prefix="mk-e2e-")` **安全建立**(唯一、由本輪建立),
根目錄放一個帶 uuid 的標記檔。刪除前三道**全過**才刪:

1. **標記檔存在且內容等於本輪的 uuid**(⇒ 這個目錄是本輪建的);
2. 位於系統暫存目錄底下,且 basename 以 `mk-e2e-` 起頭;
3. **與正式 repo 互不包含** —— **比路徑元件,不用 `startswith`**
   (`startswith` 會把 `…/agent-gates2` 判成 `…/agent-gates` 的子路徑)。

任一不成立 ⇒ **不刪,印出路徑**。清理本身失敗 ⇒ **保留並回報,不吞不重試**。
**不刪使用者預先存在的目錄。**

### 8.2 措辭

> **正式 repo 的受追蹤檔案、index、HEAD 與設定不變;
> `.dev/reports/` 有預期新增。**

⚠ **不再宣稱「正式 repo 全程沒有任何寫入」** ——
報告就寫在正式 repo 的 `.dev/reports/` 底下(該目錄不進版控),
那是**允許的唯一執行期寫入**。把它說成「沒有任何寫入」就是一句假話。

---

## 九、執行安排與它**不**代表什麼

本輪由**裁決者本人**在普通終端機執行。

⚠ **repo 內找不到一份載明「REAL 層材料須來自本人或 CI」的協定文件。**
已查到的只有兩處,**都沒有寫來源規則**:

- `docs/agents/friction-log.md` —— 一處「**三層驗收**(UNIT / CLEAN / REAL)」;
- `docs/tickets/framework-updates/22-machine-recovery-drill.md:531,535` ——
  記了一次「MCP 註冊:**REAL 層通過**」。

⇒ 那條來源規則是**本輪的口頭裁決**,**不是可引用的條文**。
要把它變成條文,得另外寫下來(**本輪不做**)。

⚠ **人工按下按鈕不自動代表獨立設計或獨立驗收。**
本腳本由 agent 設計與撰寫、由人執行 —— **兩者不互相背書**。
「誰跑的」解決的是材料來源,**不解決「設計對不對」與「結果誰驗收」**。

---

## 十、結案範圍

- **票 138 不因腳本存在而結案。** 它的命題是「人工步驟沒有被寫下來」,
  本文是那一半的候選答案;**夠不夠由裁決者判**。
- **票 133 不因本項而結案。** 本項只是〈本票不是「只剩端對端」〉九項盤點的**第 1 項**;
  其餘八項(#12 乙、#12/#11/#13 的候選記錄、受測分支可達性、票 141 / 143、
  `prov_why` 未被讀)**一個字都沒動**。
- **B 輪(舊版 gate.py 對照)本版未實作**,`--round B` 一律拒絕。
  【差異】證據由**隔離層既有測試**提供(票 133 的 #10 / #11 / #13);
  本項缺的是真 hook 的**【接線】**證據。
  **B 輪不列入票 133 的結案條件。**

---

## 相關

- **票 138** —— 本文的來源(人工步驟沒有被寫下來)。
- **票 133** —— 六格的修復與〈待辦:真正掛 hook 的違規 `git commit` 端對端驗證〉。
- **`docs/adr/0007`** —— `core.hooksPath` 是 per-clone local config,clone 帶不走。
- **`bootstrap.sh`** —— 接線那一步,自帶三道 fail-closed。
- **`docs/adr/0009`** —— 另一個「只有人能做」的步驟(`g1_verify.py` 的覆蓋)。
  **本行只記兩者都存在人工步驟,不主張同類、也不主張該照搬。**
