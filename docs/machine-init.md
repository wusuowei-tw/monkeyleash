# 機器初始化清單

三個月後、換一台機器(或另一個國家的新機器)從零重建時,照這份做完就好,不靠回憶。

**這份只管使用者層 `~/.claude/`** —— 那些「跟人走、不進任何 repo」的檔案。
**每個 repo 自己的安裝**(前哨 + 權威層 + 站別狀態)由 `install.py` 處理,見 README 與本檔第三節。
兩者分開的理由:repo 內的東西 clone 就有;`~/.claude/` 的東西不在任何 repo 裡,換機器就得重放一次。

> **紅線**:本檔所有範例都是佔位符。實際路徑、帳號、保護清單內容**不寫進這裡**——
> 那些是敏感資料,而這個 repo 要公開。佔位符:`<使用者家目錄>`、`<資料目錄>`、
> `<備份資料夾>`、`<你的使用者名稱>`、`<券商或雇主名>`、`<ISO 日期>`。

---

## 零、先決條件 —— 這台機器要先有的東西

**這一節原本不存在,而下面每一節的驗收都踩在它上面。** 2026-08-14 的換機器演練
在第一綠就撞停:`machine-init.md` 與 `README.md` 全文 `pip install` 出現 **0 次**。

### 0-1. Python 相依

`pyproject.toml` 要求 `>=3.10`。兩個套件缺一不可,而**缺席後果不同**:

| 套件 | 缺席時 |
|---|---|
| `pyyaml` | **`gate.py` 的硬相依。** `load_stage_defs()` 的 `import yaml` 失敗 → `stages` 空 + `err` → R2 fail-closed **擋掉所有原始碼寫入**。`pyproject.toml` 自己的註解寫得最準:「少了它閘門不是壞掉,是**把人鎖在外面**」。方向是對的、會出聲,但那個 repo 在裝好之前寫不了任何碼。 |
| `pytest` | 第二之一節的金絲雀與第三節的 `verify_gates` 全部跑不起來(`No module named pytest`)。 |

```
python -m pip install "pyyaml>=6.0" "pytest>=8.0,<10"
```

> **上限 `<10` 是刻意的(票 34)。** 沒有上限時新機器會拿到當下最新版
> (演練那台拿到 9.1.1、桌機是 9.0.3),兩台機器跑的不是同一個測試執行器。
> 上限的位置 = **實測證據的邊界**:9.x 兩台全綠,10.x 沒有證據。
>
> 上限自己會過期,而過期的上限不會出聲,所以它配了一個到期日
> (`pyproject.toml` 的 `pytest-ceiling-review`)。到期那天
> `tests/test_dependency_ceiling.py` 會轉紅並印出複審程序 ——
> **那條紅燈不是壞掉**,照著它做完再往上推上限。

### 0-2. ⚠ 要裝進 **hook 實際呼叫的那支** python,而那不一定是你以為的那支

掛載寫的是 `python "…/g1_guard.py"` —— **由 PATH 解析**。Windows 上
`where.exe python` 常常回兩支以上(第二支多半是 Microsoft Store 的轉接殼)。
裝錯直譯器的話,檔案都在、`pip list` 也對,而 hook 依然吃不到套件。

**別用推論,用一條零副作用的探針**(`gate.check()` 是純判定,不寫任何檔案,
所以擋下時磁碟上不會留下東西):

1. 裝之前,對一個源碼路徑用 **Write / Edit** 試寫一次,看 hook 回報的**原因**:
   ```
   [R2/fail-closed] …:站別定義不可用,原始碼寫入一律擋下。
        原因:無法載入 yaml 套件(No module named 'yaml')
   ```
2. `python -m pip install …`(用 `python -m pip`,保證裝進 `python` 解析到的那支)。
3. **同一條探針再試一次。** 訊息應翻成:
   ```
        原因:讀不到流程狀態(.dev/pipeline.json)
   ```

**訊息翻面 = 證明 hook 吃的就是你剛裝的那支。** 中間只變動了一件事,
所以這是觀測不是推論 —— 與第二節開頭「複製檔案不算裝好」同一句話,
套在直譯器上。

### 0-3. git identity

```
git config user.email "<你的提交信箱>"
git config user.name  "<你的提交名稱>"
```

**GCM 登入解決的是推送憑證,不是提交身分。兩件事。**

> **缺席時會製造假綠,這是本節最貴的一條。** 沒設 identity 時 `git commit`
> 回 **128**,而**洩漏偵測一個字都沒說** —— 它根本沒跑到。
> 第二節探針四的期望是「commit 被擋下」,如果只看「退出碼非 0」就打勾,
> 你會把一次**完全沒有發生的洩漏偵測**記成綠燈。
> 演練實際踩過這一次。判準見 `docs/adr/0009` 第 4 步:
> **一次觀測只能放一個受測項**;退出碼不是觀測,訊息才是。

---

## 零之一、**控制檔清單 —— 決定閘門行為、卻不進版控的那幾處**

> **這份清單 2026-08-26 從 `docs/audits/2026-08-16-rule-inventory.md` 搬過來。**
> 理由:**稽核紀錄是某個時點的快照,操作清單要跟著世界更新**,
> 兩者的更新頻率不同 —— 而它已經在被當成備份清單的底本用。
> 判準是「**它會長,而且會被當成現況查**」,而本檔正是換機器時逐項對照的那一份。
> 原處留了指標,舊路徑不變成死路。

**判準:決定閘門行為、卻不進版控。** 由 `F-083` 半徑掃描產出(不只裁決者列的六處,
是把守衛程式讀的**所有**路徑常數都撈出來對版控狀態)。

| # | 檔案 | 決定什麼 | 版控狀態 |
|---|---|---|---|
| 1 | `.agents/legacy-no-redlight.txt` | **R6 的 go-live 錨 + 豁免名單本身** | **已進版控**(票 54 前置 `20859ce`)—— **不需手動複製** |
| 2 | `.dev/pipeline.json` | **R2 的站別、R3 的票號** | gitignored |
| 3 | `.dev/shadow.json` | 影子模式開沒開 | gitignored · **🔴 本項刻意不存在,見下** |
| 4 | `.dev/test-runs.jsonl` | **R3 的紅燈紀錄** | gitignored |
| 5 | `.cache/mount-check.json` | R4 的掛載快取 | gitignored |
| 6 | `~/.claude/shadow-clamp.txt` | 影子安全閥 | **使用者層,不在任何 repo** |
| 7 | `~/.claude/g1-protected.txt` | **G1 第一級的保護清單** | 同上 |
| 8 | `~/.claude/leak-patterns.local.txt` | **leak_scan 一半的涵蓋** | 同上 |
| 9 | `~/.claude/upstream-roots.txt` | **R3 provenance 的上游指標** | 同上 |
| **10** | **`.dev/intercepts-*.jsonl`** | **R7 enforce 側的攔截紀錄**(票 49) | 裁定不進版控 |

**第 10 是一族檔案,不是一個檔**(2026-08-28 第一階段落地時定名)。
按月分檔,加一個不刪的摘要檔:

```
.dev/intercepts-YYYY-MM.jsonl   ← 原始紀錄。**只保留當月 + 前一月**,更舊的自動滾掉
.dev/intercepts-summary.jsonl   ← 滾掉的月份,一月一行(約 100 bytes),**不刪**
```

**換機器時複製整族**(`.dev/intercepts-*.jsonl`,一個萬用字元就夠)。
選按月分檔的理由與本清單的用途直接相關:備份是**按次**發生的,
而「複製最近幾個月」是人做得出來的操作,「複製最近 5000 筆」不是 ——
**要先算的備份步驟會被跳過**。月檔名還自然排序,`ls` 就看得出有沒有斷月。

⚠ **滾動會丟掉個別紀錄的 `message` 全文與 `cmd_sha256`。**
要拿來分析的月份,**必須在它被滾掉之前處理** —— 這是真的損失,不是無痛壓縮。

**第 4、5、9 是 `F-083` 掃出來的,不在原本那六處裡** ——
第 9 那格尤其值得記:**整條 provenance 豁免建立在一個住在使用者層、
不在任何 repo 的檔案上**,而沒有人主動想得到它。

### 🔴 第 1 項:**已進版控,但那一列不刪**(2026-08-28)

`20859ce`(票 54 前置)起 `.agents/legacy-no-redlight.txt` 就進版控了,
本清單一直記著 gitignored —— **`F-036` 的形狀:清單引用的事實已經被改掉。**

**改成「已進版控 · 不需手動複製」,而那一列保留。**
直接刪掉會讓清單**從 9 變 8 而沒有人知道為什麼** ——
`F-137` 逐字:**一份清單不會帶著它自己的長度**;
少掉的那一項在剩下的清單裡**不佔位置**,與「本來就只有八項」長得一樣。

> **「不需複製」與「不在清單上」是兩件事。**
> 前者是一個**答案**,後者是一個**空白** —— 而空白會被重新問一次。

### 🔴 第 3 項:**本項刻意不存在 —— 這是一個狀態,不是一個空白**

實查(2026-08-28):`.dev/shadow.json` **不存在**。**這是對的,要保持。**

> **它存在 → `shadow_active()` 為真 → 上游從 enforce 退回「只記不擋」。**
> **到新機器上不得憑空建立。**

**為什麼要把「沒有」明寫成一項**:備份清單逐項對照時,一個不存在的檔案
與一個**忘記複製的**檔案,在清單上長得一模一樣 ——
而這一項的兩種錯法方向相反:
漏複製只是少一份;**憑空建一份會把整個上游的閘門從「擋」變成「記」**,
而且**沒有任何東西會叫**(它不是錯誤狀態,它是影子模式的正常狀態)。

這一格同時寫進 `docs/handover/2026-09-11.md`,因為換機器的人讀的是那一份。

### 兩件要分清楚的事

**一、第 10 與 1–9 性質不同。** 1–9 是**控制項**(決定行為),
第 10 是**證據**(記錄行為)。放進同一張清單是因為**備份需求相同**
(不進版控 + 機器換掉就沒了),**不是性質相同**。
票 22 R5 的原則仍適用:**證據檔可接受竄改風險、控制檔不可** ——
所以第 10 的備份不需要與 1–9 同等級的完整性保證。

**二、`~/.claude/` 那四項(6–9)本檔第一節逐項有說明**(含 sha 核對指令);
`.dev/` 與 `.cache/` 那些(1–5、10)是**per-repo** 的,
每個裝了框架的 repo 各有一份。**換機器時前者只有一份、後者有 N 份。**

### ⚠ 這一節本身沒有機制

沒有任何東西會在**新增第 11 處控制檔**時出聲。
`F-083` 那次是一輪主動掃描的產物,而**掃描不是常設的**。
下一次有人在守衛程式裡加一個讀路徑的常數,這張表不會自己長。
**登記,不處置** —— 要做的話,判準是「守衛程式裡所有路徑常數 ∩ 不進版控」,
而那是可枚舉的(封閉集合)。

## 一、`~/.claude/` 底下框架需要的每一份檔案

先確保 `~/.claude/hooks/` 這個目錄存在。然後逐項備齊下表。

### 1. G1 hook 本體 `g1_guard.py`

| | |
|---|---|
| **路徑** | `<使用者家目錄>/.claude/hooks/g1_guard.py` |
| **格式** | Python 腳本,不是資料。原封不動。 |
| **誰提供** | **你從 repo 複製**:`.claude/portable/g1_guard.py` → 上面那個路徑。 |
| **缺席時** | **靜默失效(危險)**。掛載指令會去執行這支檔;檔不在 → 指令執行失敗 → 依 harness 對「hook 無法執行」的處置而定,**不能假設它會 fail-closed**。實務上等於 G1 整層不在,而且**沒有東西會說它不在**。所以這一項要跟第 5 項(掛載)一起驗活體探針,別只確認檔案存在。 |
| **過期時** | **靜默分歧(同樣危險,而且更容易發生)**。repo 副本每改一次,這一份就落後一次 —— 它**不會**自己跟上,`git pull` 也碰不到它(它不在 repo 裡)。而**兩邊都跑得起來、測試都綠**:repo 的測試驗的是 repo 那份,`~/.claude/` 這份沒有任何東西在驗。見下方「repo 改了之後」。 |

#### repo 改了之後:這一份要人工重蓋(ADR 0009)

**判準:`.claude/portable/g1_guard.py` 一有變動,這台機器上的副本就過期了。**
覆蓋只有人能做(agent 碰不到保護目錄,而且**不得寫腳本代勞** —— 那會讓保護消失)。

**⚠ 凍結過的機器解凍時,`git pull` 之後的下一個動作就是這一步。**
`git pull` 只更新 repo 副本;使用者層那份還停在凍結當時的版本,而**沒有任何訊號會說它舊了**。

```powershell
# 1. 兩個路徑 + 備份現行版
$src = "<repo 根目錄>\.claude\portable\g1_guard.py"
$dst = "$env:USERPROFILE\.claude\hooks\g1_guard.py"
Copy-Item $dst "$dst.working"

# 2. 覆蓋。**用 Copy-Item(位元組複製)**
#    不要用 Get-Content | Set-Content —— 它會重新編碼,可能加 BOM 或把 LF 換成 CRLF,
#    兩者都會讓 hash 對不上(BOM 這一族在本專案已經咬過三次)。
Copy-Item $src $dst -Force

# 3. 確認蓋對了 —— 三個確認點,缺一不可
Get-FileHash $dst -Algorithm SHA256 | Select-Object -ExpandProperty Hash
Get-Item $dst | Select-Object Length
cd "<repo 根目錄>"; git status --porcelain     # 必須**沒有輸出**
```

**期望的 sha256 從 repo 那份現算**,不要抄一個寫死的值(它每次修都會變):

```powershell
Get-FileHash $src -Algorithm SHA256 | Select-Object -ExpandProperty Hash
```

第 3 步的 `git status` 是 ADR 0009 票 25 加的查核項:**確認剛才是複製不是搬移**。
若出現 ` D .claude/portable/g1_guard.py`,立刻 `git checkout -- .claude/portable/g1_guard.py` 還原,再重做。

**覆蓋完必跑四項**,缺一不算裝好:

1. 兩檔 sha256 相同
2. `python -W error::DeprecationWarning` 匯入乾淨(`~/.claude/hooks/` 那一支)
3. `PYTHONIOENCODING=utf-8 python .claude/portable/g1_verify.py`(**不帶參數 = 驗正式檔**)全綠
4. **活體探針一次** —— 對一條含保護路徑的唯讀指令試一次,要看到 `[G1/保護清單]`

> **第 4 項不能被第 3 項取代。** `g1_verify` 自己 `subprocess` 起 guard,**不經 `settings.json` 的掛載** ——
> 它證明的是「如果被呼叫,它會擋」,證明不了「它會被呼叫」。這與本檔第 1、5 項「檔案都在也可能沒生效」是同一句話。
>
> `PYTHONIOENCODING=utf-8` 不是可選的:`g1_verify.py` 有一行 `print("  無 ✓")`,
> 在 cp950 主控台會 `UnicodeEncodeError` 崩掉(票 62,已立案未修)——
> 你會看到一個編碼錯誤,而不是驗收結果。

### 2. G1 保護清單 `g1-protected.txt`

| | |
|---|---|
| **路徑** | `<使用者家目錄>/.claude/g1-protected.txt` |
| **格式** | 純文字,**每行一個絕對路徑**;`#` 起首為註解,空行忽略。範例(兩三行示意):<br>`<資料目錄>/<備份資料夾>`<br>`<使用者家目錄>/.claude/g1-protected.txt`  ← 清單把自己列進去,否則 agent 能先改清單再刪東西<br>`<使用者家目錄>/.claude/shadow-clamp.txt`  ← 安全閥也受它保護 |
| **誰提供** | **你手動**,而且**照該機器實際存在的路徑寫**(見本檔第二節末的警告)。 |
| **缺席時** | **fail-closed(而且很吵)**。`g1_guard` 讀不到清單 → 一律回擋 → 所有 `Bash/PowerShell/Write/Edit` 全被 `[G1/fail-closed]` 擋下。你會**立刻**發現,不是靜默。這是刻意的:讀不到就放行的話,刪掉清單等於關掉整個防護。 |

### 3. 影子安全閥 `shadow-clamp.txt`

| | |
|---|---|
| **路徑** | `<使用者家目錄>/.claude/shadow-clamp.txt` |
| **格式** | **恰好一行** `SHADOW_MAX=<ISO 日期>`;`#` 註解、空行可有。多行 `SHADOW_MAX` 或不認得的行 → 視為壞掉 → 無效。範例:<br>`# 影子模式硬上限,過了這天影子物理上開不了`<br>`SHADOW_MAX=<ISO 日期>` |
| **誰提供** | **你手動**。而且**要手動加進第 2 項的保護清單**(gate.py 只讀它、改不了它)。用 utf-8 存檔即可(帶不帶 BOM 都吃,gate.py 用 `utf-8-sig` 讀)。 |
| **缺席時** | **fail-closed 方向,但不吵**。缺席/壞掉 → 影子**不生效**、閘門**照常擋**(往「閘門開著」倒,不往「影子開著」倒)。不影響正式閘門運作;只是**影子模式開不起來**。裝進大型既有 repo 想開影子卻發現一直在硬擋,先查這一項。 |

### 4. 個人洩漏 pattern `leak-patterns.local.txt`

| | |
|---|---|
| **路徑** | `<使用者家目錄>/.claude/leak-patterns.local.txt` |
| **格式** | 純文字,**每行一條 regex**;`#` 註解。放「會揭露我是誰」的具體形狀。範例:<br>`(?i)<你的使用者名稱>`<br>`<券商或雇主名>`<br>`<資料目錄>/<備份資料夾>` |
| **誰提供** | **你手動**。通用形狀在 repo 的 `.claude/portable/leak-patterns.txt`(公開);個人 token 住這份(不進版控),`leak_scan.py` 掃時把兩份聯集。 |
| **缺席時** | **不 fail-closed**(個人 pattern 本來跟人走,別台機器沒有很正常)。`leak_scan` 會**顯式警告**(stderr `[洩漏偵測/警告] 找不到個人 pattern 清單…`)後只用通用 pattern 繼續 —— 涵蓋比你以為的小,但不擋。**對比**:通用那份(repo 內)缺 → **fail-closed**、直接擋。 |

### 5. `settings.json` 的 G1 掛載設定

| | |
|---|---|
| **路徑** | `<使用者家目錄>/.claude/settings.json`(既有檔,合併進去,別覆蓋你其他設定) |
| **格式** | 在 `hooks.PreToolUse` 放一個掛載:<br>`{"matcher": "Bash\|PowerShell\|Write\|Edit\|MultiEdit\|NotebookEdit",`<br>`  "hooks": [{"type":"command",`<br>`    "command": "python \"<使用者家目錄>/.claude/hooks/g1_guard.py\""}]}`<br>matcher **必須含 Write/Edit**,不能只掛 Bash —— 否則 Write 直接覆寫保護目錄不會有人擋。 |
| **誰提供** | **你手動**(把上面那塊併進既有 `settings.json`)。 |
| **缺席時** | **靜默失效(危險)**。沒有掛載 → `g1_guard` 永遠不被呼叫 → 防護整層不在、**無訊號**。與第 1 項同一類坑:檔案都在也可能沒生效。 |

> **一句話記住缺席行為**:**清單/pattern 缺 → 讀取端 fail-closed(擋、看得見);
> hook 本體或掛載缺 → 根本沒被呼叫(靜默、看不見)。** 所以驗收不能只 `ls`,要跑活體探針。

---

## 二、換機器的驗收(複製檔案不算裝好)

「檔案都在」證明不了「防護會生效」——第 1、5 項缺席時檔案在也沒用。換機器後**必跑**下列活體探針,每條都要看到**擋**與**訊息內容**,不是只看退出碼。

| 探針 | 怎麼觸發 | 期望 |
|---|---|---|
| **G1 第一級:擋保護路徑、訊息指名** | 對一條含保護路徑的指令(任何 `Bash`,連讀取都算)試一次 | `[G1/保護清單]` 擋下,**訊息裡指名**那條保護路徑 |
| **G1 第二級:擋專案外破壞** | 對專案目錄以外的絕對路徑下破壞性動詞(如 `rm <資料目錄>/x`) | `[G1/專案外破壞性動作]` 擋下,指名動詞與路徑 |
| **clamp 缺席 → fail-closed** | 把 `shadow-clamp.txt` 暫時改名,對一個開了影子的 repo 觸發一條本該擋的規則 | **照常擋**(影子不生效),不寫影子日誌。驗完把 clamp 改回來 |
| **leak hook 擋假 token** | 在一個跑過 `bootstrap.sh` 的 repo 裡,把一個**假造**的、命中某條 pattern 的字串寫進檔案並試 `commit` | pre-commit 洩漏偵測擋下 commit |

自動化替代:
- `python .claude/portable/g1_verify.py` —— 從**當前實際清單**生成案例,斷言每一條保護路徑被命中時訊息都指名它自己(涵蓋第一級探針,且清單長新條目時自動涵蓋)。
- `python .claude/portable/verify_gates.py <暫存目錄>` —— 六站規則全跑 + 淨室安裝一次。

> **關鍵警告 —— 新機器的路徑不一樣,保護清單要照該機器實際存在的路徑寫,不是照桌機抄。**
> 清單是**文字比對**:寫了一條桌機才有的路徑,在新機器上它**指向不存在的地方,等於白列**。
> 更陰的是:`g1_verify` 只證明「清單裡每一條被命中時擋得住」,它**不會**告訴你「這些條目在這台機器上保護的是不是真的東西」——
> 驗收全綠 ≠ 保護對了地方。備清單時逐條問:**這台機器上,這個路徑真的存在、真的是我要保護的嗎?**

---

## 一之一、用匯出/匯入腳本搬 `~/.claude/`(票 22 Phase 2)

`.claude/portable/user_layer.py` —— **單向**,正本永遠是 `~/.claude/`。
不用 symlink:那會讓 dotfiles repo 的工作樹變成第二條可寫路徑。

分類表:`.agents/user-layer-manifest.txt`。**沒有預設** —— 未分類會拒絕整次匯出。

```
# 舊機器 —— 先看會發生什麼(dry-run,不寫任何東西)
python .claude/portable/user_layer.py export <匯出目錄>

# 確認報告沒問題,再真的寫
python .claude/portable/user_layer.py export <匯出目錄> --apply

# 新機器 —— 先看會發生什麼
python .claude/portable/user_layer.py import <匯出目錄>

# 真的寫(`age` 桶有東西時必須給私鑰)
python .claude/portable/user_layer.py import <匯出目錄> --apply --identity <私鑰檔>
```

### 排除物的慣例:**放匯出目錄之外,名稱帶日期**

演練時難免會人工把某幾項先挪開。**挪去哪裡、叫什麼名字,要有慣例**:

```
匯出目錄     <雲端>\dotfiles-export\
排除物       <雲端>\dotfiles-export-excluded-<ISO 日期>\      ← 目錄之外,帶日期
```

**理由**:「刻意移走」與「意外消失」在檔案系統上**長得一模一樣** ——
留下的檔案 mtime 沒變、目錄 mtime 變了,兩種情況產生的痕跡完全相同。
唯一能區分它們的是**命名與位置的慣例,不是記性**(F-084 實際耗過一輪查證)。

放在匯出目錄**裡面**更糟:匯入端會把未分類的東西一起搬過去,
而那正是卡點 #4 的形狀。

### 解密的執行方式:**`age -o` 直寫,不走管線**

若要手動解密(不經腳本):

```
age -d -i <私鑰檔> -o leak-patterns.local.txt leak-patterns.local.txt.age
```

> **不要用管線接 `Set-Content`。** PowerShell 5.1 的管線會弄壞 UTF-8 中文
> (F-042 第五次現身),而這個檔案裡就是中文形狀。`-o` 直寫繞開整條管線。

**順序:先驗貨,再燒鑰匙。**
確認解密出來的內容是對的**之前**,不要銷毀任何一份來源 ——
這是備份總方針「備份先於手術」在單檔層級的同一句話。

### 私鑰只在這一步出現,而且只在這一步

| | |
|---|---|
| **公鑰** | 有預設檔案 `~/.claude/age-recipient.txt`,腳本自動讀,跟著匯出走 |
| **私鑰** | **每次用 `--identity` 明給**;腳本**不會**去任何預設位置找它 |

**兩者的處置刻意不對稱。** 讓私鑰有一個預設檔案位置,就等於把金鑰放回自動流程裡 ——
而「密碼管理器 + 紙本各一份」那條裁決會變成一句空話:
金鑰會安靜地住在磁碟上,**而加密的價值等於私鑰的保密程度**。

> **`export` 預設是 dry-run。** 先算、先報告,加 `--apply` 才寫 ——
> 而報告的主體是**「未帶走」那一段**。
> 匯出**依設計就是不完整的**(下一節那兩個檔腳本不碰),
> 所以「沒帶走什麼」比「帶走什麼」重要。
> 匯入在人工步驟完成前**不會回報成功**(退出碼 1),那是刻意的。

執行前提沒滿足時(例如缺 age 公鑰),**dry-run 照樣把計畫算給你看**,
只在報告末尾多一段「執行前提未滿足」;`--apply` 才會拒絕。
**「計畫算不出來」與「計畫現在還不能執行」是兩件事。**

### 一之二、裝 age(`age` 桶要用)

`leak-patterns.local.txt` 內容本身就是祕密(使用者名稱、往來機構、資料夾名),
明文進任何 repo 或雲端等於把「要防的東西」列成一張清單。所以它加密後才走。

```
winget install --id FiloSottile.age
age --version          # 裝完必驗 —— 「裝了」與「叫得到」是兩件事
```

> **若 `age --version` 說找不到指令:關閉並重開終端機,再驗一次。**
> 安裝會更新 PATH,但**已經開著的視窗吃的是舊環境** —— 新視窗才生效。
> 桌機實測過這一次:`winget list` 顯示 `age 1.3.1` 已裝,而兩個 shell 都叫不到。
> 重開之後仍然找不到,才是真的沒裝好
>(可查 `%LOCALAPPDATA%\Microsoft\WinGet\Packages\FiloSottile.age_*\age\age.exe`)。

**公鑰(recipient)給法兩種,擇一:**

```
python ... export <目錄> --apply --recipient age1xxxxxxxx…
# 或在 <使用者家目錄>/.claude/age-recipient.txt 放一行公鑰
```

| | |
|---|---|
| **公鑰** | **不是祕密**。可以進版控、可以跟著匯出走(分類表標 `export`)——新機器要加密自己的匯出時需要它。 |
| **私鑰** | **不經本腳本、不經任何自動流程。** 密碼管理器 + 紙本各一份,與 age 金鑰的既有裁決一致。 |

> 沒有 age 或沒有公鑰時,`--apply` **整批拒絕、不寫半套** ——
> 不會退化成「那一項跳過、其餘照寫」。跳過是靜默的。

### 這兩個檔只能人工複製 + sha 核對(R4,腳本永遠不碰)

| | |
|---|---|
| **哪兩個** | `<使用者家目錄>/.claude/g1-protected.txt`、`<使用者家目錄>/.claude/shadow-clamp.txt` |
| **為什麼腳本不碰** | 兩者都在 G1 保護清單裡,第一級**無豁免、不分讀寫** —— 腳本去讀就會被擋。它們必須**本來就不去讀**,而不是讀了以後決定不用。**G1 不開任何豁免。** |
| **怎麼搬** | 你自己開終端機複製。`cp`,**不是 `mv`**(ADR 0009 第 3 步踩過一次)。 |

**複製完兩邊各算一次 sha,肉眼比對:**

```
# 舊機器
certutil -hashfile "%USERPROFILE%\.claude\g1-protected.txt" SHA256
certutil -hashfile "%USERPROFILE%\.claude\shadow-clamp.txt" SHA256

# 新機器,同樣兩條,比對輸出
```

> **「複製過去了」與「兩邊內容相同」是兩件事**,而前者不蘊涵後者
> (編碼、行尾、同步軟體都可能插手)。這是第二節「複製檔案不算裝好」
> 套在檔案內容上的同一句話。

### ⚠ `g1-protected.txt` 是唯一**不該**照抄的一項

清單是**文字比對**,而且要照**該機器實際存在的路徑**寫。
新機器的磁碟結構不同 —— 照舊機器抄過去,那些條目**指向不存在的地方,等於白列**,
而且 `g1_verify` 會全綠(它只證明清單裡每條被命中時擋得住)。

所以這一項的正確動作是**帶過去當底稿,然後逐條覆核**:
「這台機器上,這個路徑真的存在、真的是我要保護的嗎?」
唯讀探針的**存在性檢查**(第五段)就是為這件事做的,Phase 3 必跑。

## 二之一、權威層接上了沒(票 27,**Phase 3 必驗**)

前一節驗的是 G1。**這一節驗的是六站閘門的權威層有沒有真的在 git 的通行路上。**

> **這一條是換機器最容易漏的。** `.git/hooks/` 依 git 設計不進版控,
> **clone 不會帶走它** —— 新機器上 clone 完,權威層預設就是不在的。
> 而缺席**幾乎無聲**:前哨照跑、測試照綠。
> agent-gates 自己就這樣過了 40 個 commit,一次權威判定都沒發生過。

| | |
|---|---|
| **啟用** | 在 repo 根目錄跑 `sh bootstrap.sh` —— 一行 `core.hooksPath` config,**每個 clone 一次**。零接觸不可能:git 刻意不讓 clone 自動執行任何東西。 |
| **驗收** | `python -m pytest tests/test_gate.py::TestAuthorityLayerIsWired` —— 其中 `test_this_repo_itself_is_wired` 問的是「**現在、這台機器上**接上了沒」,不是「框架的邏輯對不對」。 |
| **缺席時** | 紅燈,訊息直接給修法(`sh bootstrap.sh`)。**這是刻意讓它吵的** —— 靜默缺席正是票 27 的整件事。 |

**兩條掛載路徑,以 `core.hooksPath` 為準:**

- 有設 → git **只**跑那個目錄裡的 hook,`.git/hooks/` 整個被忽略
- 沒設 → git 跑 `.git/hooks/`

兩支都必須**兩段都接**(`leak_scan` + `gate.py --pre-commit`)。少了 `--pre-commit`
那支 hook 跑的是預設模式,**什麼都不擋** —— 而「檔案在、名字對、內容有 gate.py」
三件事都成立。驗收要看的是**行為**,不是這三件事。

> **本行原寫「三層」,2026-08-18(票 51:⑥)更正為「兩段」。**
> 那個 hook 只有兩個階段,全庫沒有任何一處說得出第三樣是什麼 ——
> **不是這裡缺一層,是那個數字從一開始就錯。** 完整查證見票 51:⑥。
> 歷史紀錄(票 01/15/27/44 與 friction 條目)照 F-036 不改寫。

> **驗收不能只 `ls`,也不能只讀 hook 的檔名** —— 與第二節開頭同一句話:
> 檔案都在證明不了防護會生效。

## 二之二、clone **框架自己**時還缺三樣(演練實測)

前面兩節管的是「裝進別的 repo」。**這一節管的是 clone `monkeyleash`(原 `agent-gates`)自己。**

第三節的 `install.py` 會替目標 repo 產生狀態與名冊,但**沒有任何東西替框架自己做這件事** ——
而它們全被 `.gitignore` 蓋住(per-repo 狀態,不是框架內容),所以 **clone 拿不到**。
症狀全是 fail-closed,會出聲,但訊息不會告訴你「這是新 clone 的通病」。

| 要補的 | 缺席時 |
|---|---|
| `.dev/pipeline.json` | `[R2/fail-closed] 讀不到流程狀態` —— **擋掉所有原始碼寫入** |
| `.dev/test-runs.jsonl`、`.dev/gate-exemptions.jsonl`(雙帳本) | R3 的紅燈紀錄那一半沒有依據;豁免記不下來即 fail-closed |
| `.agents/legacy-no-redlight.txt` | `[R6] 找不到豁免清單 —— 讀不到一律當違規` → **擋掉所有 commit** |

### 三樣怎麼補

**1. `.dev/pipeline.json`** —— 照 `install.py` 的 `generate_state()` 正典,不要自己編:

```json
{
  "current_stage": "idle",
  "feature": null,
  "ticket_id": null,
  "updated": ""
}
```

`idle` 是對的起點:它 `allows_src_write: false`,所以要開工得由**人**顯式改這個欄位;
而提交時 `idle` 是刻意放行的(ADR 0005),不會擋掉文件類 commit。

**2. 兩本空帳** —— `.dev/test-runs.jsonl`、`.dev/gate-exemptions.jsonl`,各建 **0 位元組**。
`install.py` 是一起建它們的。**空證據是誠實的起點**,不存在的證據不是。

**3. `.agents/legacy-no-redlight.txt`** —— **重新生成,絕不照抄**。
照抄的話清單裡是別的 repo 的路徑,R6 拿本地的 sha 去驗每一筆都不在樹裡,全數判違規。
生成邏輯就是 `install.py` 的 `generate_legacy_list()`:取 go-live commit 的樹、
篩 `.py`、再過 `gate.is_source_path()`。首行是 `# go-live: <完整 sha>`。

驗收(**寫了檔不等於過**):

```
python -c "import sys; sys.path.insert(0,'.claude/hooks'); import gate; print(len(gate.check_legacy_list()))"
```

回 `0` 才算數。

> ### ⚠ 兩個會讓你查錯方向的坑
>
> **編碼**:`gate.py` 讀 `pipeline.json` 用的是 `utf-8`,**不是 `utf-8-sig`** ——
> 有 BOM 的話 `json.load` 直接炸,而你看到的訊息與「檔案根本不存在」**一模一樣**。
> Notepad 存檔請選 `UTF-8`,不要選 `UTF-8 with BOM`;檔名記得加引號免得被偷加 `.txt`。
>
> **目錄名**:`.dev/` 被 `.gitignore` 忽略,所以**目錄名打錯時 `git status` 看不到** ——
> 演練那次打成字母對調的名字,而 `git status` 反而因為它「不是那個被忽略的名字」
> 才把它顯示成未追蹤。fail-closed 訊息只會說「讀不到流程狀態」,
> **它不會說「你建在隔壁」**。補完先用上面那條 `python -c` 之類的方式讀一次,
> 確認讀得到的是你剛建的那份。
>
> 另外:若目標目錄**已經存在**(例如你先跑過測試,機制自己建了 `.dev/` 並寫了證據),
> `Move-Item` 是**搬進去**而不是改名,會得到 `.dev/<打錯的名字>/`。
> 而那裡面的空帳本若平移上來,會**蓋掉已經有內容的證據檔** —— 證據不搬移、不還原。

---

## 三、新專案安裝

```
sh bootstrap.sh                                   # 啟用進版控的洩漏 pre-commit(每個 clone 一次)
python .claude/portable/install.py <目標 repo>     # 一律建 commit(go-live sha)、最後強制驗證
# → 讀 <目標 repo>/docs/decisions-pending.md,把裡面每一項問清楚、處理完刪掉
python .claude/portable/verify_gates.py <暫存目錄>  # 全規則 + 淨室
python .claude/portable/g1_verify.py               # G1 保護清單
```

**裝好的定義是驗證通過,不是檔案複製完。** `decisions-pending.md` 清空才算安裝的人工部分做完。

### 要不要開影子?一條判準

- **legacy 清單筆數大到會淹沒日常工作** → **先開影子**。裝進既有、大量無測試的 repo 時,R1–R8 會擋掉大批既有工作;影子讓「先不擋、只量測誤擋率」成為可能。
  開影子:在 repo 建 `.dev/shadow.json` = `{"until":"<ISO 日期>"}`,**且**第 3 項的 `shadow-clamp.txt` 要在(否則影子開不了、照常擋)。晉升 per-rule(每規則 ≥10 筆已分類、假陽率 <5%),工具 `shadow_review.py`。見 `docs/adr/0012`。
- **空 repo 或小 repo** → **不用開,直接正式上線**。沒有大批既有工作要豁免,影子只是多一層要收的狀態。

影子開著時,正式擋下的訊息帶 `[enforce]` 標示、影子只寫 `.dev/shadow-log.jsonl` 的 `would-block` —— 「現在是影子還是正式」從任一次攔截訊息就讀得出來。
