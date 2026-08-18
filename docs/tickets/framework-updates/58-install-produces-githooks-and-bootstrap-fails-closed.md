# 58 — 執行 `F-065:1115`:install 產 `.githooks/`,bootstrap 三道 fail-closed

**狀態**:**完成**(2026-08-18)—— 本機 824 passed、淨室 R1–R8 各擋一次、巢狀 790 passed。
**唯一未驗的一格是 CI 的「接上權威層」步驟,推上去才驗得到,所以驗收清單留白不勾。**
**落地**:`69854e9` D4(票 54 落差表 + F-099 第五列)→ `7020057` D1 立案
→ `e195adc` D2(三道 + mode)→ `af8752a` D3(install 產出 + `--chmod=+x`)→ 本筆收尾
**立案**:2026-08-18,批一(票 57)收乾淨、CI 綠之後
**批次**:本輪第二批。**批一是票 57**,它的卷首是本票的前提 —— **引用,不重述。**
**來源**:`docs/agents/friction-log.md` 的 **F-065:1115–1118**(標「未做,待裁決」)

> **本票不寫新的待辦,它執行一條已經寫下、標著「待裁決」的待辦。**
> 票面引用 `F-065` 原文,不改寫、不重述 —— 重述會製造第二個版本,
> 而兩個版本不一致時沒有人知道哪一個是真的。

---

## 卷首:兩件,而第二件是罕見的方向

### 一、一段專門防止某個誤讀的文字,住在一支正在犯那個誤讀的程式裡

`bootstrap.sh` 現有全文可執行的只有三行:

```sh
set -e
cd "$(git rev-parse --show-toplevel)"
git config core.hooksPath .githooks
```

**無條件設 config。** 不查 `.githooks/pre-commit` 在不在、不查它在不在 index、
不查它的 mode。**fail-closed:零。**

而同一支腳本的第 22 行印出:

```sh
echo "驗收 —— **裝好的定義是驗證通過,不是 config 設完**:"
```

> **它印出「裝好 ≠ config 設完」,然後做的正是「設完 config 就宣告裝好」。**
> 底下那兩條驗收是**印給人看的待辦**,腳本自己一條都沒跑。

**這是 F-099 最尖銳的形態:一段專門用來防止某個誤讀的文字,
住在一支正在犯那個誤讀的程式裡。**

### 二、下游先做出更好的版本,上游吸收回來

量化今天早上替它的 `bootstrap.sh` 加了三道 fail-closed(**上游那支更早,沒有**):

| # | 檢查 | 不擋的話會怎樣 |
|---|---|---|
| ① | 缺 `.githooks/pre-commit` → 拒絕設 config | 指過去的目錄是空的,**權威層當場消失** |
| ② | hook 不在 index → 拒絕 | 沒進版控就不隨 clone 走 —— **這台機器看起來接上了,下一個 clone 又回到起點** |
| ③ | mode 非 `100755` → 拒絕 | **git 不執行沒有執行位元的 hook,而且不出聲** |

**每一道都額外斷言 `core.hooksPath` 沒有被設下去**,理由是 **TSI-030**:

> **一個跑在危險動作之後的 fail-closed 檢查,不是 fail-closed。**
> config 是**持久狀態**,報錯不會把它收回去。

三道各有正對照。

> **那三道把上面那句 echo 從「提醒」變成「機制」。**
> **這是罕見的方向:下游先做出更好的版本,而上游要吸收它。**
> 本票**以量化那一版為起點,不重寫一版** —— 重寫會丟掉它已經踩過的坑,
> 而那些坑不會在票面上,只會在它的判斷順序裡。

---

## ⚠ 範圍聲明:本票**不關掉** ADR 0007 那個缺口

**不寫這一節,「執行了 F-065:1115」會被讀成「缺口關掉了」。**

`ADR 0007:33` 逐字:

> **三者都碰不到:clone 下來直接手動 `git commit` 的人。**

`ADR 0007:19-22` 逐字:

> `core.hooksPath` 是 **local config,不隨 clone 走**。它把「複製一個檔案」
> 換成「跑一行 config」,**沒有消除那一步**,只是縮短。
> 零接觸不可能:**git 刻意不讓 clone 自動執行任何東西。**

**本票買到的是**:hook 檔跟著 clone 走,所以 `bootstrap.sh` 從
「**你還得先弄到 hook**」變成「**一行 config**」。

**本票買不到的是**:那一步本身。**沒有做法關得掉** —— 那是 git 的安全設計,不是缺陷。

### ⚠ 順帶:`F-065:1117` 的措辭比現實樂觀,而且**點錯了受益者**

F-065 原文(**照 F-036 不改寫,更正記在這裡**):

```
  那會**部分關掉 ADR 0007 說的那個缺口**(clone 下來直接手動 commit 的人)。
```

**兩處都不對:**

| 原文 | 事實 |
|---|---|
| 「**部分關掉**」 | **一點都沒關。** 那個人仍然不會跑 `bootstrap.sh`,而不跑就沒有權威層 |
| 「(**clone 下來直接手動 commit 的人**)」 | **那正是 ADR 0007:33 說三者都碰不到的人。** 本票對他一點影響都沒有 |

**真正的受益者是另一個人:會跑 `bootstrap.sh` 的人。**
在他身上,本票讓 `ADR 0007:20` 那句「換成跑一行 config」**第一次成為真的** ——
在此之前,裝出來的 repo **根本沒有 `.githooks/`**,那一步實際是
「先手工造一個 hook,再跑一行 config」。

> **本票不縮小缺口,它讓一個已經寫在 ADR 裡的機制真的存在。**
> 這兩件事在票面上長得很像,而只有後者是真的。

**這一則歸 F-099 那一族**(一段解釋性文字比現實樂觀),
與丁那件(票 54 落差表)同一天撿到兩個。

---

## 現況證據

### 一、`install.py` 的產出面:三格,只有一格真的缺

| 需求 | 現況 | 要不要改 |
|---|---|---|
| hook 檔進得了 index | **已滿足** —— `install.py:402` 的 `git add -A` 就跟在 `install_hook()`(`:400`)後面 | **不用** |
| hook 檔有執行位元 | **不滿足** —— `install.py:205-208` 用 `os.chmod(path, 0o755)` | **要,而且只有這一格** |
| 產 `.githooks/` | **不滿足** —— `install_hook()` 只寫 `.git/hooks/pre-commit` | 要 |

`os.chmod` 為什麼不夠,兩層:

| 層 | 事實 |
|---|---|
| **檔案系統** | Windows 沒有 POSIX 執行位元,`os.chmod(0o755)` 實質是 no-op |
| **git index** | `filemode=false` 時 git 一律把新檔記成 `100644`,**不看檔案系統** |

**唯一的解是明確指定 index 的 mode**:`git update-index --add --chmod=+x <path>`
(或 `git add --chmod=+x`)。它寫的是 **index 的位元**,不經過檔案系統,
所以在 Windows 上一樣成立。

### 二、D0 量測:上游自己的 hook 就是 `100644`

```
$ git ls-files -s .githooks/ bootstrap.sh scripts/ .github/
100644 bfb69618a8830a3ad8984569182c9ae0cc8ea175 0	.githooks/pre-commit
100644 4d3be1b85530c662295e70fcff481d22ce2a3850 0	.github/workflows/tests.yml
100644 7cfd127c657996a8608466f0c76fa223a32cb61d 0	bootstrap.sh
100644 093aa00fd8134581ad5879de2fd6137b5ff5f9fd 0	scripts/skills-update.sh
```

> **檢查③ 抓到的第一個受害者,會是寫出檢查③ 的那個框架自己。**

因果鏈四段,每段都有既有證據:

| # | 事實 | 證據 |
|---|---|---|
| 1 | 本 repo 的 `core.filemode` 是 `false` | `.git/config` `[core] filemode = false` |
| 2 | `filemode=false` 時 git 一律記 `100644` | 上面四個檔全是 100644 |
| 3 | Linux 上 git **只執行有執行位元的 hook**,沒有就**靜默跳過** | git 對非 Windows 走 `access(path, X_OK)`,失敗即當作沒有 hook |
| 4 | `authoritative_layer()` **只讀內容,不看 mode** | `gate.py:239-258` —— 查 `exists`、讀 `body`、比對 `"gate.py"` 與 `"--pre-commit"`,**沒有一行問 mode** |

**1 → 2 → 3 造成缺陷,4 讓它靜默。**

#### ⚠ 嚴重度校準:**潛伏缺陷,不是現行故障**

**今天沒有活的受害者。** 四個理由各自獨立:

| | 為什麼今天沒事 |
|---|---|
| agent-gates 桌機 | Windows 開發,**git for Windows 不看執行位元**(靠 shebang 判) |
| agent-gates 本機 | `core.hooksPath` **未設定** → 走的是 `.git/hooks/`(不進版控,mode 無關) |
| agent-gates CI | Linux,但 **CI 從不 commit** —— 沒有任何一次 commit 會觸發那支 hook |
| 下游 | 量化那份是 **100755**;影音**沒有 `.githooks/`** |

**但它正是「綠燈說已安裝,而它不會執行」那一類。** 寫成潛伏而不是火警,
是因為**把潛伏講成火警會讓下一個真的火警沒有人信**。

#### 同類入口查過了,而且結論是「**不是同一族**」

| 檔案 | index mode | 誰執行它 | 需要執行位元? | 是缺陷? |
|---|---|---|---|---|
| `.githooks/pre-commit` | 100644 | **git 直接執行** | **是** | **是** |
| `bootstrap.sh` | 100644 | 人跑 `sh bootstrap.sh`(CI 也是 `run: sh bootstrap.sh`) | 否 | 否 |
| `scripts/skills-update.sh` | 100644 | 人跑 `bash scripts/skills-update.sh` | 否 | 否 |
| `.github/workflows/tests.yml` | 100644 | GitHub Actions 讀它,不執行 | 否 | 否 |

> **三個檔共用同一個 mode,只有一個共用那個缺陷。**
>
> **「同類」的判準是機制不是外觀 —— 誰執行它,以及那個執行者看不看那個位元。**
> (這是 **F-083** 那條「回頭問同類入口在哪」的精修:同類要問**機制**,不是問長得像不像。)

**所以本票只改一個檔的 mode。** 把另外兩支一起改成 100755 會是
**沒有缺陷在後面的改動** —— **它讓 diff 看起來一致,而一致不是理由。**

---

## 設計裁決(2026-08-18)

### 甲:產 `.githooks/` 之後的三個開關 → 選 **C**

`gate.py:229-241` 的 `authoritative_layer()` **跟著 `core.hooksPath` 走**:
沒設就查 `.git/hooks/pre-commit`。四格全列:

| # | 產 `.githooks/` | 設 config | 續寫 `.git/hooks/` | 驗證查哪裡 | `install.py:328` | 後果 |
|---|---|---|---|---|---|---|
| A | ✓ | ✓ | ✓ | `.githooks/` | **過** | 兩支並存,`.git/hooks/` 那支永遠空轉 —— **「裝上去但空轉」第五個實例** |
| B | ✓ | ✓ | ✗ | `.githooks/` | **過** | 端狀態最乾淨,但**沒有備援**:config 被清掉就靜默消失 |
| **C** | ✓ | ✗ | ✓ | `.git/hooks/` | **過** | **選這個** |
| D | ✓ | ✗ | ✗ | `.git/hooks/`(不存在) | **失敗** | — |

**選 C 的三個理由:**

1. **install 不該設 config,因為 config 不是 repo 的內容。** `core.hooksPath` 是
   local config,不隨 clone 走(ADR 0007:19)。設了它,等於把**這台機器的狀態**
   混進安裝產物,而下一個 clone 拿不到 —— 「裝好了」在兩台機器上意思不同。
2. **兩支並存是票 27 已裁過的正解**,agent-gates 自己現在就是這個狀態。
3. **A 會製造第五個「裝上去但空轉」**,而那正是票 57 卷首在講的病。

#### C 的代價,寫在票面上

**裝出來的 repo 上,`.githooks/pre-commit` 在 `bootstrap.sh` 跑之前是死的。**
只看目錄結構的人會以為權威層走 `.githooks/`,而實際走 `.git/hooks/`。

> **這是票 27 那個誤讀的鏡像版本。** 要在安裝輸出或 `decisions-pending.md` 裡明說 ——
> 不說的話,它就是本票自己製造的下一則 F-099。

### 設計張力:`install` 產的檔會被它自己的檢查②③ 拒絕 → **只補 `--chmod=+x`**

原本的三選一是「install 也要 `git add` + `--chmod=+x`」/「bootstrap 分兩種形態」/「兩者都要」。
**查完之後範圍比三個都窄:**

- **`git add` 不用補** —— `install.py:402` 早就有(**這一格是沒查就先設計**)
- **`--chmod=+x` 要補** —— 唯一真的缺的
- **「bootstrap 分兩種形態」否決**

#### 否決「分兩種形態」的三個理由

1. **它要先回答「我現在是剛安裝還是已 clone」,而那沒有可靠的問法。**
   能想到的代理指標(有沒有 commit、是不是空 repo、有沒有 remote)全部會錯,
   **而且錯的方向是放行**。這是**票 48**「repo 身分是推導來的,不是問出來的」同一族。
2. **它讓 fail-closed 認得一個例外,而 TSI-030 的整個理由就是不留例外。**
   一旦有「但這次是剛安裝」這條路,那條路就是會被走到的那條 —— 而它跳過的正是三道檢查。
3. **兩個判準只有一個會被日常走到,另一個會腐爛而沒有東西出聲。**
   「已 clone」那條每天走,「剛安裝」那條一年走幾次。

---

## 明確不做:`install.py:102` 的假警報

**這一項本票不做,而「不做」是裁決不是遺漏。**(登記在票 56:116–147)

`ignored_framework_files()` 的契約(`install.py:105`)寫「**本來會帶、卻被 gitignore
藏起來的**」,而過濾是 `in_scope(p) and mark_for(p) != "skip"` ——
**`generate` 桶不在「會帶」之列**(`install.py:396` `copy_into(target, buckets["copy"])`
只搬 `copy` 桶),卻照樣進了公告清單。

### 新資訊(票 56 只記了一次觀察)

> **它每次都印,不是量化特有。** 本輪 CI 又印了一次(`.dev/test-runs.jsonl`)。

**那把它的代價從「一次噪音」變成「每次安裝、每次 CI 的固定噪音」——
F-031 的累積曲線因此比票 56 記的陡。**

### 不做的三個理由

| | 理由 |
|---|---|
| 1 | **接縫不同。** 本票動 install 的**產出面**;它動 install 的**公告面**。同一個檔案,不同接縫 —— 票 56 自己寫過:「混進本票會讓一組紅綠燈同時服務兩個缺陷」 |
| 2 | **正解要設計。** 天真修法(排除 `generate`)不對 —— 「一個 `generate` 檔被 gitignore 蓋住」仍可能值得知道,正解多半是**分兩段講**,而分成哪兩段是一次獨立設計 |
| 3 | **它不讓任何規則失效。** 照 code-review 的分流判準(`docs/adr/0003`):「不改會不會讓別的規則失效?」→ **不會** |

### 若將來要做,先知道代價

**它會改變 `tests/test_install.py` 既有兩條測試的前提**
(`test_ignored_framework_files_are_enumerated`、`test_mirrors_and_bytecode_are_not_dragged_in`)——
那兩條現在釘的正是 `in_scope` + `!= "skip"` 這組過濾。

> **不是加一條測試,是重新定義那組測試在測什麼。**

---

## 批次與順序

| 批 | 內容 | 狀態 |
|---|---|---|
| 批 | 內容 | commit |
|---|---|---|
| **D0** | 量 `.githooks/pre-commit` 的 index mode → **100644** | (唯讀,無 commit) |
| **D4** | 票 54 落差表「淨室」那一列更正 + `F-099` 第五列(載體:落差表) | `69854e9` |
| **D1** | 本票立案(卷首、範圍聲明、現況證據、設計裁決、明確不做項) | `7020057` |
| **D2** | `bootstrap.sh` 三道 fail-closed + **`.githooks/pre-commit` 的 mode 改 100755** + `tests/test_bootstrap.py`(9 條) | `e195adc` |
| **D3** | `install.py` 產 `.githooks/pre-commit` 與 `bootstrap.sh`,以 `--chmod=+x` 進 index + `tests/test_install.py`(7 條) | `af8752a` |
| **D5** | 收尾 + `F-101` / `F-102` / `F-103` + `F-099` 增補 + 票 51 的行號 | **本筆** |

### 三個順序約束

1. **D2 必須在 D3 之前。** D3 讓 install 產出 `.githooks/pre-commit`,而 D2 的三道檢查
   是它的驗收標準。反過來的話,D3 的中間狀態是「產了一個沒有人檢查的檔案」。
2. **mode 修正不得與 D2 分開。** `.github/workflows/tests.yml:56-57` 每次 CI 都跑
   `sh bootstrap.sh`;三道檢查一落地而 mode 還是 100644 → **CI 當場紅**,
   而那筆紅**不是設計的紅燈,是排序失誤**。
3. **`F-101` 必須在 D3 之後**(所以掛 D5):它要寫「**修好這一個檔的 mode 是修實例,
   讓 `authoritative_layer` 看 mode 才是修機制**」,而「實例已修」要
   **D2(上游那份)與 D3(安裝器產出的那份)都做完才完整**。
   順帶符合票 57 的先例:**friction 排在它引用的東西之後。**

### D2 的訊息要保留這一句

> **mode 修正獨立於三道檢查成立 —— 就算三道都不做,那個 mode 也是錯的。**

不寫的話,日後讀 diff 的人會把**一個真缺陷的修復**讀成**一次為了配合測試的調整**。

---

## 怎樣算做完

- [x] `bootstrap.sh` 以量化那一版為起點(不重寫),三道 fail-closed 各有正對照
- [x] 三道都**在設 config 之前**跑,且各自額外斷言 `core.hooksPath` 沒被設下去(TSI-030)
- [x] `.githooks/pre-commit` 的 index mode 是 `100755`,而且該筆 commit 的訊息說出它獨立成立
- [x] `install.py` 產 `.githooks/pre-commit` + `bootstrap.sh`,前者以 `--chmod=+x` 進 index
- [x] `install.py` **不設** `core.hooksPath`、**繼續寫** `.git/hooks/pre-commit`(甲的 C)
- [x] C 的代價(`.githooks/` 在 bootstrap 跑之前是死的)出現在安裝輸出
- [x] 淨室 `verify_gates` 全綠(它跑真安裝,是本票的端到端驗收)
- [ ] **CI 的「接上權威層」步驟綠** —— **推上去才驗得到,本機驗不了,所以留白不勾**
- [x] 範圍聲明(不關掉 ADR 0007)在票面上,且 `F-065:1117` 的措辭更正已記
- [x] `F-101` 落地(D5),外加 `F-102` / `F-103` / `F-099` 增補

---

## 落地紀錄(2026-08-18)

### 端到端:那一步從此真的只剩一行

**在拋棄式 target 上驗**(`verify_gates` 產的淨室 repo),照 **F-102** 不碰本尊:

```
$ git -C <target> ls-files -s .githooks/pre-commit bootstrap.sh
100755 12be7ba08a7ad36a62bd361eb8f66152cd2cd22e 0	.githooks/pre-commit
100644 8f6da5bf78ca238526b8eca0284337f1019f90c5 0	bootstrap.sh

$ git -C <target> config --local --get core.hooksPath
(空)

$ cd <target> && sh bootstrap.sh
[bootstrap] core.hooksPath -> .githooks
rc=0

$ git -C <target> config --local --get core.hooksPath
.githooks
```

**甲的 C 三格全中**:`.githooks/pre-commit` 是 `100755`、config 未設、
`.git/hooks/pre-commit` 仍在。`bootstrap.sh` 是 `100644` —— **對的**,
它被 `sh` 呼叫,不需要執行位元(F-101:同類的判準是機制不是外觀)。

> **在此之前,一個裝出來的 repo 上跑 `bootstrap.sh` 會撞到第一道 fail-closed
> (`找不到 .githooks/pre-commit`),因為安裝器根本不產它。**
> `F-065:1118` 逐字:「現在是人工補的,**下一個安裝的人不會知道要補**。」

### 測試

| | 本機 | 巢狀(淨室) |
|---|---|---|
| D2 前 | 808 | 783 |
| D2 後 | 817(+9,`tests/test_bootstrap.py`) | — |
| D3 後 | **824**(+7,`tests/test_install.py`) | **790**(+7) |

**巢狀 +7 而不是 +16**:`tests/test_install.py` 標 `copy` 會跟著走,
`tests/test_bootstrap.py` 標 `skip` 不走(見標記表裡的釘子)。
**+7 是真的 +7** —— 那七條在巢狀 repo 裡讀的是巢狀自己的
`SRC_ROOT/bootstrap.sh`,而那個檔是它自己剛被產出來的。

紅燈先行,兩批都走:D2 先跑 **1 failed**(活體金絲雀抓到上游自己 `100644`)、
D3 先跑 **7 failed**(整個新 class)。

### 本輪產出的 friction

| | 主題 |
|---|---|
| **F-101** | **觀測點的數量不等於覆蓋 —— 盲區會重疊。** 執行位元是實例,盲區重疊才是教訓 |
| **F-102** | 一個已經在拋棄式環境被證明的東西,不要在本尊上再證一次 |
| **F-103** | 一個斷言可以因為**錯的理由**而通過(兩個實例) |
| **F-099 增補** | 第四面(**行號**)、處置欄的**構造解:釘子** |

### ⚠ 兩處我自己寫錯、在下一個批次被自己抓到

**兩處都留著不刪**,理由見 F-099 的處置欄:
**釘子的價值不是「條件會對」,是「條件被寫下來所以可以被查」。**

| 寫在 | 錯的 | 什麼時候抓到 |
|---|---|---|
| 標記表的釘子(D2) | 到期條件寫「**D3 之後**」 | **D3 當天** —— 正確條件是「目標 repo 有 `bootstrap.sh`」,而 D3 之前裝好的下游要**重跑 install** 才會有。現在標 `copy` 會讓 sync 送一條註定紅的測試過去 |
| `_index_of()` 的 docstring(D2) | 失效方向寫成「讓順序斷言變成**假的**」 | **D3 當天** —— 實際是讓它**假地成立**。已落成 **F-103 實例一**,而那一處是 `TSI-029` × `F-099` 的交集:**程式碼本來就是對的,錯的是它的說明,而錯的說明與正確的程式碼同向 —— 所以沒有任何東西會揭穿它** |

> **兩處都是「寫下來所以被查到」。** 沒寫的話那兩個假設一樣是錯的,
> 只是沒有人會發現 —— 而其中一個會在某天讓 `sync` 把一條註定紅的測試送到下游。

### ⚠ 提交過程中的一次自我修正(留紀錄)

E1 第一次提交時**多帶了 `.githooks/pre-commit` 的 mode 變更** ——
那一格早在 D2 就被 `git update-index --chmod=+x` **直接寫進 index**,
於是 `git add <兩個 docs 檔>` 之後它仍然在暫存區,被一起收進 E1。

未推送,`git reset --soft HEAD~1` + `git restore --staged` 退掉重做。

> **`update-index` 不經過工作樹,所以 `git status` 的第一欄早就是 `M`** ——
> 而按檔名逐一 `git add` 的習慣**看不到那一格**:它不在我要加的清單裡,
> 它已經在裡面了。**「我只加了這兩個檔」與「這一筆只有這兩個檔」是兩件事。**

