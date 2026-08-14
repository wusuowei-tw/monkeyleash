# 27 — 權威層沒有接上 git:agent-gates 自己不執行六站閘門

**排程**:票 26 之後。守衛設計變更,走完整流程,**自己的紅燈**。
**這是病本體;票 26 是它的症狀之一。**

## 一句話教訓

> **手動呼叫一支檢查,不等於那支檢查在通行路上。**

票 26 的調查過程本身就是標本:我手動跑 `python .claude/hooks/gate.py --pre-commit`,
看到它擋下,於是回報「pre-commit 現在擋掉所有 commit」。**那句話是錯的** ——
git 從來不會執行那一支。檢查存在、檢查會擋、檢查被我看到擋了,
三件事都成立,而**它仍然不在通行路上**。

## 現況(全部已驗證)

| 檢查 | 值 |
|---|---|
| `core.hooksPath` | **未設定** → git 用 `.git/hooks/pre-commit` |
| `.git/hooks/pre-commit` 含 `gate.py` 的次數 | **0** |
| `.githooks/pre-commit` 含 `gate.py` 的次數 | **0** |
| 兩支實際執行的內容 | 只有 `leak_scan.py --staged` |

唯一會寫出三層掛載(leak_scan **加** `gate.py --pre-commit`)的是
[install.py:39-41](../../../.claude/portable/install.py),而它**從未對 agent-gates 執行過**。

**後果:六站閘門在自己的來源 repo 裡只有前哨,沒有權威層。**
40 個 commit 一路過來,R1–R7 在 commit 時一次都沒有判定過。

## 這是 CLAUDE.md 已經寫下的那個缺陷,live

`CLAUDE.md` 的 gate.py 強制契約一節:

> **未安裝的副本上這句不成立**:`.git/hooks/` 不進版控,clone 不會帶走它,
> 而且**完全靜默** —— 前哨照跑、測試照綠,沒有東西會說權威層不在。
> **這是已知缺陷,不是留白。**

**agent-gates 自己就處在那個狀態。** 文件寫得完全正確,而寫下它的 repo
正是那句話的受害者 —— 因為「已知」不等於「有東西會說」。

唯一的訊號是 `tests/test_gate.py` 的 4 條紅(票 26),而那 4 條紅
混在既有的 3 skipped / 3 xfailed 裡,**沒有任何東西指出它們代表
「權威層對本 repo 是壞的」**。訊號存在但不可讀,等於沒有訊號。

## 附帶發現:bootstrap.sh 宣稱的機制不是實際生效的機制

`bootstrap.sh` 說它靠 `git config core.hooksPath .githooks` 啟用版控裡的 hook
(ADR 0007 的理由:`.git/hooks/` 不進版控,clone 不會帶走)。
但實測 **`core.hooksPath` 未設定**,實際生效的是 `.git/hooks/pre-commit`
—— 一支 08/11 13:58 直接安裝的副本,**早於** `.githooks/pre-commit` 的建立時間(14:35)。

兩支內容都只有 leak_scan,所以**效果相同**、洩漏偵測確實有效。
但「文件寫的機制」與「實際生效的機制」不是同一個,而 Phase 3 換機器時
照 machine-init 重建的是**文件寫的那個**。

## 修法(三項,b 是核心交付)

### a. 權威層接上 git

對 agent-gates 執行 `install.py` 的 hook 安裝段,或等價接線。
`core.hooksPath` 的語意一併釐清:**到底以哪一支為準**,以及
「`.githooks/` 版控 + config 指過去」與「直接寫 `.git/hooks/`」兩條路
在 clone 情境下各自的行為。**兩條路並存而沒有人說哪條為準,是這次混淆的一半。**

### b. 金絲雀:權威層未接上 → **大聲失敗**(核心交付)

**缺席必須出聲。** 新增一條檢查,驗**git 實際會執行的那一支 hook**
的內容含 `gate.py --pre-commit`。

判準,一條一條都是這次撞出來的:

- **驗的是 git 實際執行的那一支**,不是「某個路徑上有一支長得對的檔案」。
  `core.hooksPath` 決定是哪一支 —— 檢查必須先問 git,不能假設 `.git/hooks/`。
- **不得只驗檔案存在**。存在、可讀、內容對,是三件事(machine-init 第二節的同一句話)。
- **失敗訊息要說出是哪一個前提沒滿足**(票 13 判準):
  是沒有 hook、是 hook 沒接 gate、還是 `core.hooksPath` 指到別處。
- **這條檢查自己不能只活在前哨** —— 否則又是一個「不在通行路上的檢查」,
  同一個遞迴。它要能在 CI / 測試 / 安裝驗證三處之一被強制跑到。

> 反面教材就在手邊:`check_legacy_list` 是一條正確、fail-closed、
> 有測試涵蓋的檢查,而它兩天沒擋住任何東西,因為沒接上。
> **本票如果只寫出檢查而沒接上,就是把票 27 再犯一次。**

### c. bootstrap.sh 與 machine-init 對齊

修正宣稱機制與實際生效機制的落差,`machine-init.md` 同步,
**標註 Phase 3 必驗**(票 22)。換機器是這種落差唯一會現形的時刻。

## 過渡措施(即刻生效至本票落地)

**每次 commit 前手動執行 `python .claude/hooks/gate.py --pre-commit` 並回報結果;紅 → 停。**

這是繃帶不是修法 —— 它靠紀律,而本票存在的理由正是紀律靠不住。
記在這裡是為了讓它有結束的日期。

## 落地紀錄(2026-08-14)

**紅燈先行**:`tests/test_gate.py::TestAuthorityLayerIsWired`,**7 紅**,
`ticket_id 27`、`impl_hash` 為改動前的 `gate.py`。

實作 `gate.authority_hook_missing()` 之後 **6 綠 1 紅** —— 剩下那條紅是
**活體金絲雀**(`test_this_repo_itself_is_wired`),它紅得對:當時權威層真的沒接上。
訊息點名了 git 實際會跑的那一支的完整路徑。接線之後 **7 綠**。

三支檔案的處置:

| 檔案 | 動作 | 理由 |
|---|---|---|
| `.git/hooks/pre-commit` | 接上三層 | git 現在實際執行的那一支(`core.hooksPath` 未設定) |
| `.githooks/pre-commit` | 接上三層 | **進版控**,跟著 clone 走。原本只有 leak_scan —— 而 `manifest.py` 自己就記載過這個形狀是缺陷:「降成只剩 leak_scan,**權威層靜默消失**,而整個過程看起來像一次成功的更新」。agent-gates 自己就在那個降級狀態 |
| `bootstrap.sh` | 釐清語意 + 驗收改成兩條 | 宣稱機制與實際生效機制對齊(c) |

`core.hooksPath` 語意寫進 `bootstrap.sh`:**有設就只跑那個目錄,`.git/hooks/` 整個被忽略;沒設才跑 `.git/hooks/`。**
兩支現在都是三層,所以走哪條都不掉權威層 —— 這是「兩條路徑並存」的正解:
不是選一條廢一條,是**讓兩條都不會靜默降級**,再把「哪條為準」寫下來。

### 為什麼金絲雀不掛在 `mode_pre_commit` 裡

掛在那裡的話,**權威層沒接上時它根本不會被呼叫** —— 而那正是它要偵測的情況。
同一個遞迴。所以它住在測試裡:那是這個 repo 目前唯一**會被強制跑到**的路徑。
本票開頭那句一句話教訓,對它自己也適用。

### 未完(留在本票)

- 金絲雀目前只接在 pytest 上。**安裝驗證(`verify_gates.py`)也該叫它** ——
  裝完一個新 repo 時,「權威層接上了嗎」正是該當場回答的問題。
- `machine-init.md` 同步 + 標 Phase 3 必驗(票 22)。

## 怎樣算做完

- git **實際執行**的 pre-commit 含 `gate.py --pre-commit`(實測,不是宣稱)
- 金絲雀檢查在權威層被拔掉時**大聲失敗**,訊息說得出是哪一個前提沒滿足
- 金絲雀自己接在一條會被強制跑到的路徑上(不是只有前哨)
- `core.hooksPath` 的語意寫進文件,兩條掛載路徑明確擇一
- `bootstrap.sh` 宣稱 == 實際生效;`machine-init.md` 同步並標 Phase 3 必驗
- 過渡措施撤除,票 22 Phase 3 的演練會驗到這一條
