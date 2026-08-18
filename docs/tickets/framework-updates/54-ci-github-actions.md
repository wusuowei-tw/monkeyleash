# 54 — 裝 CI(GitHub Actions)

**狀態**:**收尾(2026-08-16)—— CI 第二次執行綠勾,證據見文末**
**立案**:唯讀偵察後裁決(票 46 之外的獨立票)
**產出**:`.github/workflows/tests.yml`、`tests/test_ci_workflow.py`、
`.agents/legacy-no-redlight.txt` 進版控、`.github/` 標 `skip`

---

## 頭條:CI 涵蓋落差表

**「有 CI」與「CI 涵蓋這一塊」是兩件事,而綠燈只說得出前者。**

這張表存在的理由:CI 上的排除項若只寫成 YAML 註解,
**下一個看到綠燈的人不會知道綠燈的範圍變小了**。

| 面向 | 本機 | CI | 差在哪一條 |
|---|---|---|---|
| **R6 正對照** | **5 條** | **5 條** | **無差** —— 五條全過(見下方逐條) |
| **R6 清單完整性** | 有 | **無** | `test_gate.py::TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce` |
| **leak_scan 個人 pattern 層** | 4 個測試函式 / **12 個參數化案例** | **0** | `tests/test_known_items_regression.py` **整檔** |
| **leak_scan 通用 pattern 層** | 有 | **有** | 無差(`load_patterns()` 對個人清單缺席只警告,不 fail-closed) |
| **symlink 路徑** | **0**(3 條 skip:Windows 建不了) | **3 條** | **CI 多於本機** —— 這三條在桌機從未執行過。**2026-08-16 第二次 CI 已實證通過**,見文末收尾節 |
| **淨室(安裝後形態)** | **這台機器上直接跑會中斷** —— 主控台是 cp950,`verify_gates.py:211` 印 `✓` 時丟 `UnicodeEncodeError`;**要 `python -X utf8` 才跑得完** | **有**(每次 CI,Linux 主控台是 UTF-8) | **票 56 加入;本機那一格由票 58 D4 更正。** CI 綠燈涵蓋 **13 / 93 面**的真實形態,**不是全部** —— 見下方註 |
| **`.githooks/` 的 hook 在 Linux 上真的被 git 執行** | **0** —— Windows 的 git 不看執行位元,測不出來 | **0** —— **CI 從不 commit** | **兩邊都是零。** 票 58 加入,見下方專節 |
| R1–R5、R7、R8、G1 | — | — | 無差 |

### ⚠ 兩邊都是零的那一列(票 58,2026-08-18)

**`.githooks/pre-commit` 的 index mode 已在 `e195adc` 改成 `100755`。
但「Linux 上 git 真的會執行它」這件事,推上去之後仍然是零證據。**

#### 兩層原因,各自獨立

| # | 原因 |
|---|---|
| **①** | **三道檢查驗的是 index mode,而 git 執行 hook 看的是檔案系統的位元。** 兩者在 Linux 上由 `checkout` 綁在一起 —— **而那個耦合本身沒被任何東西驗過。** 我們驗了 A、假設 A ⇒ B,而沒有驗過 B |
| **②** | **CI 從不 commit。** 唯一會真的 commit 的是 `verify_gates`,而它在 **target** 上做 —— 走的是 `install` 寫的 `.git/hooks/`(`core.hooksPath` 未設,那是甲的 C),**不是 `.githooks/`** |

> **mode 修好讓它「很可能會動」,而「很可能」不是證據。**
> 這一列存在的理由就是把那個差別寫出來 —— 綠燈現在說的是
> 「mode 對了」,不是「hook 會跑」。

#### 補法(**登記,不在票 58 做**)

**`verify_gates` 加一個情境:在 target 上跑一次 `bootstrap.sh`,然後真的 commit 一次。**
那條路徑會同時打到 ① 與 ②:走 `core.hooksPath` → `.githooks/pre-commit` →
**由 git 自己決定要不要執行它**,而那正是唯一能證明那個耦合的方式。

不在票 58 做的理由:它動的是 `verify_gates.py`,而那支是 **CI 紅綠燈的一部分**
(同丁那件的理由)——把它併進一張已經在收尾的票,等於在紅綠燈上多開一個未驗的面。

#### 這一格是 `F-101` 那個「找法」的第一次應用

照那四步跑:

| 步 | 本件 |
|---|---|
| 1 列觀測點 | CI、`verify_gates` |
| 2 問**它刻意不看什麼** | CI:**刻意不 commit**(`tests.yml:13-16`「只跑測試,不發布、不部署、不留言」);`verify_gates`:**刻意在 target 上用 `.git/hooks/`**(甲的 C,install 不設 config) |
| 3 疊起來取交集 | **「走 `core.hooksPath` 的真 commit」** |
| 4 問「壞了誰會叫」 | **沒有人** |

> **兩個盲區各自都有正當理由,而它們的交集正好是這一格。**
> **這一次不是回頭發現的,是照著步驟走出來的** —— 而那是 F-101 那條找法
> 第一次證明自己能用在**還沒出事**的東西上。

### ⚠ 「淨室」本機那一格的更正(票 58 D4,2026-08-18)

**舊文(照 F-036 留著)**:`有,但**手動、不強制**`。

**那比現實樂觀了一階。** 「不強制」的意思是**你可以選擇不跑**;
實際是**你照著跑會中斷**。實測(2026-08-18,推 `e24548c` 之前):

```
UnicodeEncodeError: 'cp950' codec can't encode character '✓'
  File "…\.claude\portable\verify_gates.py", line 211, in main
    print("    pre-commit 已接 leak_scan ✓")
```

**而它炸的位置讓這件事更難被發現**:斷點在 R1–R8 逐條實測**之後**、
安裝器預設值檢查那一段 —— 前半段全是綠勾,看起來像「跑到一半才壞」,
而不是「這台機器上它根本跑不完」。

**只更正描述,不動 `verify_gates.py`。** 它現在是 CI 紅綠燈的一部分
(`.github/workflows/tests.yml:86-87`),不該為了本機的主控台編碼順手改它 ——
那會讓一次文件更正變成一次動到紅綠燈的改動。

> **落差表比現實樂觀,是落差表最不該有的失效方向。**
>
> 這張表存在的**唯一**理由,就是說出綠燈涵蓋不到哪裡
> (見本節開頭:「下一個看到綠燈的人不會知道綠燈的範圍變小了」)。
> **一份高估自己涵蓋範圍的落差表,等於在它唯一該出聲的地方沉默。**
>
> 已落成 **F-099 的第五列**(載體:落差表)—— 那一族的判準是
> 「一段專門用來防止誤讀的文字,自己被誤讀的成本高於一般段落」,
> 而落差表是其中最尖銳的形態:**它的全部職責就是防止一個特定的誤讀
> (「綠燈 = 全部涵蓋」),所以它出錯的方向只有一個,而那個方向正是它自己。**

> **「淨室」那一列的綠燈,涵蓋範圍要照這段讀(票 56 加入)。**
>
> 涵蓋的 13 面(以「能獨立判錯的判定點」切,全庫 93 面):
> R1–R8 各 1 面(每條規則各擋一次)+ 權威層 3 面(hook 刪掉 / 別人的 hook 佔位 /
> 裝回去)+ 安裝器預設值 2 項(pre-commit 有接 leak_scan、`.gitignore` 有守 `.env`)。
>
> **沒被這一步涵蓋的重點**:R3 的 **8 面豁免全部零覆蓋**(legacy 清單、research 範圍、
> bare package marker、票宣告、logged exemption、upstream provenance、upstream 指標、
> 宣告解析)—— 而**覆蓋最差的一族,正好是最容易 fail-open 的一族**。
> 另有 R5 的位置判定與 to-spec 兩面、R7 的 8 面、R2 的 7 面。
>
> **代價:`verify_gates.py` 自己沒有測試守它。** 它列在
> `.agents/legacy-no-redlight.txt`、宣告 Untested by decision(接縫 S4),
> 接進 CI 等於讓一支無測試的腳本成為紅綠燈的一部分。
> **這一半已由實測補上**:把情境換成「什麼都不做」與「寫一個無害檔」兩種突變,
> 兩次都紅(`SystemExit: 1 條規則沒擋到`)—— 情境失效的方向是 fail-closed,
> 不會靜默變綠。**另一半沒補**:那是實測,不是機制,沒有東西保證它會被重跑。

### R6 的五條正對照(逐條,CI 上全過)

| # | 測試 | 斷言 |
|---|---|---|
| 1 | `test_an_entry_absent_from_the_go_live_tree_is_a_violation` | `assert len(v) == 1 and "not/in/the/tree.py" in v[0]` |
| 2 | `test_a_path_absent_from_that_tree_is_still_named` | `assert len(v) == 1 and "never/existed.py" in v[0]` |
| 3 | `test_a_list_without_a_sha_is_a_violation_not_a_pass` | `assert v and "go-live" in v[0]` |
| 4 | `test_an_unreadable_list_is_not_silently_clean` | `assert gate.check_legacy_list() != []` |
| 5 | `test_the_rule_is_actually_invoked_at_the_authoritative_layer` | `assert gate.mode_pre_commit() == 1` |

> **⚠ 裁決當時說「R6 少 1 條正對照(5→4)」,實測是 `5→5`。**
> 被排除的 `test_the_list_is_what_the_generator_would_produce` 斷言的是
> `entries <= expected` 與 `not undrained` —— 它守的是**清單完整性**
> (防手加一筆、防沒生成完整),**不是「R6 會擋」**。
> 落差表記的是那個**性質**,不是一個少掉的計數 ——
> 而「少 1 條」與「少了哪一種保護」在表上長得一樣,前者還比較好寫。

---

## 乾淨機器上的 17 條紅(實測,不是推論)

方法:`git clone` 到 scratchpad,`HOME`/`USERPROFILE` 指到空目錄。

| 條件 | 結果 |
|---|---|
| 乾淨 clone + **真實**家目錄 | `5 failed, 776 passed, 3 skipped, 3 xfailed` |
| 乾淨 clone + **空**家目錄 | **`17 failed, 764 passed, 3 skipped, 3 xfailed`** ← CI 等於這一種 |

> 我先用靜態檢查(搜 `tests/` 裡有沒有 `expanduser` / `HOME`)斷定「零依賴家目錄」,
> **測試檔裡確實一個都沒有** —— 讀取點在**被測模組**裡(`leak_scan.py:38–39`)。
> **量尺架在錯的那一層。**
>
> **要證明「不依賴 X」,唯一可靠的方法是把 X 拿走**;
> 搜尋 X 的名字只能證明「我搜的那一層沒提到它」。
> (突變測試的同一招,只是拿掉的是**環境**不是程式碼。)

### 三種處置

| 族 | 條數 | 處置 |
|---|---|---|
| **(甲)** legacy 清單不進版控 | 4 | **清單進版控**(下節)—— 修好 3 條;第 4 條見 (甲-2) |
| **(甲-2)** 排水證據不進版控 | 1 | **CI 跳過**,等票 49 定案後回來重評 |
| **(乙)** 權威層未接上 | 1 | CI 在 pytest 前跑 `sh bootstrap.sh` |
| **(丙)** 個人 pattern 不進版控 | 12 | **CI 跳過**,代價見落差表 |
| **(丁)** symlink | 3 | **不預先處理,讓它跑** —— 從沒看過它們跑 |

#### (甲-2) 為什麼跳過而不是就地解決

第 4 條是 `test_the_list_is_what_the_generator_would_produce`,原始訊息:

```
E       AssertionError: 這些在上線 commit 的樹裡卻不在清單上,也沒有合格紅燈紀錄可以解釋 ——清單沒生成完整:['.claude/portable/g1_guard.py']
```

`.claude/portable/g1_guard.py` 是 2026-08-14 排水的那一筆。清單第 15–17 行記著理由,
而**能證成那個理由的紅燈紀錄住在 `.dev/test-runs.jsonl`(2923 行,不進版控)**。

> **排水的理由進了版控,排水的證據沒有。**
> 那三行讀起來像已經證成的事,而**能證成它的東西一離開這台機器就不在了。**

**理由是時機不是優劣**:證據該不該進版控、用什麼格式,**正是票 49 的題目**
(判定紀錄機制:被擋時產生一筆帶「設定指紋 + 被拒的輸入 + 擋下的理由」)。
現在臨時設計一個,票 49 開工時很可能推翻重來,**還會多出一個沒人記得的舊格式**。

**→ 登記:等票 49 決定證據格式後回來重評。票 49 有反向指標指回本票。**

#### (乙) 的機制與我先前的說法不同

`bootstrap.sh` **不複製 hook**,它設 `core.hooksPath = .githooks`,
而 `.githooks/pre-commit` **進版控**。所以權威層是靠 **per-clone 的一次 config** 接上的,
不是靠一個不進版控的檔案。

實測:clone 後 `git config --local --get core.hooksPath` → `.githooks`。

---

## B 階段:legacy 清單進版控

刪 `.gitignore` 那一行,**manifest 標記不動,仍是 `generate`**。

### 兩個軸

| 軸 | 由誰管 |
|---|---|
| **可攜**(下游會不會拿到) | `.agents/portable-manifest.txt` 的 `generate` 標記。`install.py:396` 只搬 `copy` 桶;`generate` 桶靠 `generate_legacy_list()` 在目標 repo 重新產生 |
| **版控**(上游自己留不留紀錄) | `.gitignore` |

`.gitignore` 原註解講的全部是**可攜性**(「跟著發布來源走」「下游拿到」),而它管的是**版控**。

> **原理由成立,但它證成的是「不該標 `copy`」—— 而 `generate` 標記已經在做那件事。
> 一個正確的理由貼在錯的機制上。**(票 51 同族)

原文保留,更正寫在下方(F-036)。

### 進版控換來的第二件事(裁決者指出,比第一件重要)

**只減不增從此看得見。**

R6 守的正是只減不增,而那件事原本**只在執行時被檢查、不留痕**。
進版控後每次排水都是一筆 diff;有人想加回去,**R6 會擋**(新檔不在 go-live 樹裡)、
**diff 會顯示** —— 兩層都在。

同款先例就在 `.gitignore` 上面兩行:`gate-exemptions.jsonl` 與 `provenance.jsonl`
同樣是 per-repo 狀態、同樣進版控,理由同樣是「它是證據」。

### 前置驗證(進版控前)

| 檢查 | 結果 |
|---|---|
| 大小 / 行數 | 1178 bytes / 21 行 |
| 絕對路徑 / 家目錄 / 使用者名 | `grep` **無輸出** |
| `leak_scan` | **rc=0** |
| `45a8d16` 存活 | `commit`;`--is-ancestor ... HEAD` → **rc=0**;乾淨 clone 裡樹含 **20 個 `.py`** |

### 順帶修掉的死參照

清單 `:7` 原寫 `git ls-tree 5180678`,而 `5180678` 是票 39 改寫歷史前的根 commit,
`git cat-file -t` 回 `fatal: Not a valid object name`。

改成 `<go-live>` **佔位**,不填第二份 `45a8d16` ——
**同一個事實只留一個可寫的位置**,否則下次改寫歷史漏掉的仍會是第二份。

**已另立 `F-095`**(參照對齊做了 90%,而系統預測過這件事會發生)。

---

## `.github/` 標 `skip`

**標記先於任何 `.github/` 檔案進版控**,而且**分開提交** ——
順序本身就是防護,合成一次提交會讓那個順序在歷史上看不出來。

| 路徑 | 查詢函式 | 未分類時 |
|---|---|---|
| 更新(`sync`) | `mark_for` → `explicit_mark`(回 `None`) | `refuse_if_unclassified` 拒絕並點名 |
| **安裝器** | `mark_in` → `explicit_mark(...) or DEFAULT_MARK` | **`copy`,而且靜默** |

標 `skip` 的理由與 `README.md` / `pyproject.toml` / `.gitignore` 同一條:
**每個 repo 都有一份,而內容是那個 repo 的事實** ——
相依、測試數、要不要跑 `bootstrap.sh`、哪些測試依賴不進版控的檔案,三個 repo 各不相同。

---

## 四條安全驗收條件

寫成 `tests/test_ci_workflow.py`,**不寫成規矩** —— **註解不是機制**(F-086)。
下一個改 workflow 的人不會讀票面,他會讀 CI 紅不紅。

| 條件 | 測試 | 判準 |
|---|---|---|
| 1 密鑰 | `test_no_secrets_are_referenced` | `secrets.` 一次都不該出現 —— **需求為零時,任何一次出現都是需求變了** |
| 1+3 使用者層 | `test_nothing_reaches_for_the_user_layer` | 封的是**位置**(封閉集合),不是逐個檔名 —— `settings.json` / `cache/` 在 CI 有正當用途,全列會製造假警報,而**假警報訓練人忽略這條測試** |
| 1 通用形狀 | `test_leak_scan_is_clean_on_the_workflow` | 列舉抓我想得到的,通用抓我沒想到的 |
| 2 最小權限 | `test_permissions_are_least_privilege` | 要求**恰好** `{contents: read}`。**沒寫不等於安全** —— 沒寫用的是 repo 預設,而預設不在這個檔案裡、改了不會有 diff |
| 4 釘 sha | `test_every_third_party_action_is_pinned_to_a_sha` | 40 位十六進位。遞迴走訪所有 `uses:`,不寫死 `jobs→steps` 的巢狀深度 |

### 紅燈先行(原始輸出)

YAML 存在之前:

```
1 failed, 5 skipped in 0.11s
FAILED tests/test_ci_workflow.py::test_there_is_at_least_one_workflow
E       assert []
E        +  where [] = workflow_files()
```

YAML 之後:`6 passed in 0.07s`。

### 反控:五條斷言對違規樣本全部會紅

**一條沒紅過的守衛等於沒被驗過**(票 45 的 (b)/(c) 就是這個分別)。
餵一份違反全部四條件的合成 workflow:

```
  擋下  條件1 secrets            bad-workflow.yml 引用了 secrets(本 repo 的 CI 不需要任何密鑰):
  擋下  條件1+3 使用者層             bad-workflow.yml 指向使用者層:['$HOME/.claude', 'leak-patterns.local.txt']
  擋下  條件1 leak_scan          leak_scan 對 bad-workflow.yml 回 1(0=乾淨 / 1=有命中 / 2=機制錯誤)
  擋下  條件2 最小權限               bad-workflow.yml 的 permissions 是 {'contents': 'write', 'packages': 'write'},要求恰好是 {'contents': 'read'}
  擋下  條件4 釘 sha              bad-workflow.yml 有沒釘 sha 的 action:['actions/checkout@v4']

五條斷言中,對違規樣本紅的有 5 條 / 共 5 條
```

> **第三條第一次跑時沒紅,而那是樣本的錯不是守衛的錯** ——
> 我第一版的違規樣本用 `${{ secrets.MY_TOKEN }}` 當「密鑰」,那是佔位符不是金鑰形狀。
> 換成合成的 `AKIA` + 16 位大寫英數(對應 `\bAKIA[0-9A-Z]{16}\b`)就命中。
> **「守衛沒動」與「樣本沒踩到」在輸出上長得一樣,而只有一種需要修程式。**

### 這五條測試自己抓到的第一個違規:我寫的 YAML 註解

`test_nothing_reaches_for_the_user_layer` 第一次跑就紅 ——
因為我在 YAML 註解裡寫了個人 pattern 清單的**字面路徑**。

**與票 39 那條「commit 訊息裡一律用描述式,不寫字面例子」同一形狀。**
註解已改成描述式。

---

## 釘住的 action(sha ↔ 版本標籤)

| action | sha | 標籤 | 型別確認 |
|---|---|---|---|
| `actions/checkout` | `fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09` | **v5.1.0** | `object.type = "commit"` |
| `actions/setup-python` | `ece7cb06caefa5fff74198d8649806c4678c61a1` | **v6.3.0** | `object.type = "commit"` |

**型別要確認**:`refs/tags/<t>` 對 annotated tag 指向的是 **tag 物件**不是 commit,
而 `uses:` 只吃 commit sha。兩個都逐一查過 `object.type`。

---

## CI 設定要點

| 項 | 值 | 理由 |
|---|---|---|
| Python | **3.11** | 與桌機相同。**一次只變一個變數** —— CI 的價值是換一台乾淨機器,不是順便換直譯器版本 |
| 相依 | `pip install -e ".[dev]"` | 無 `requirements.txt`;`pyyaml>=6.0` + `pytest>=8.0,<10` |
| 權威層 | `sh bootstrap.sh` | 設 `core.hooksPath`,per-clone |

### CI 模擬實測(全新 clone + 空家目錄 + 兩項排除)

```
768 passed, 3 skipped, 1 deselected, 3 xfailed in 62.48s
```

對帳:**768 passed + 1 deselected + 12 ignored = 781**,與本機總數相符。

---

## 登記(不在本票處置)

| # | 登記項 |
|---|---|
| 一 | **(甲-2) 等票 49** —— 排水證據的格式定案後回來重評那 1 條。票 49 加反向指標 |
| 二 | **Python 只有下限沒有上限** —— `requires-python = ">=3.10"`。對照 pytest 有上限 `<10` **且附到期日**(`pytest-ceiling-review`)與一條會轉紅的測試。同一個 repo 裡兩種紀律 |
| 三 | ~~**條件 2 的另查未完成**~~ **← 已結案,見下方「條件 2 結案」** |
| 四 | **`5180678` 在歷史紀錄裡還有 9 處** —— 票 26(4 處)、`F-0013`(3 處)、`F-0015:444`、`going-public-known-items.md:76`。**那些不該改**(F-036:歷史紀錄記的是當時的事實)。作業中的檔案只有清單 `:7` 那一處,已修 |

---

## 條件 2 結案(2026-08-16)

**兩半都成立:**

| 半 | 值 | 誰量的 |
|---|---|---|
| repo 預設權限 | **Read repository contents and packages permissions**(唯讀,不需要收) | **裁決者在 GitHub 網頁上看的**(Settings → Actions → General → Workflow permissions)。`gh` 未安裝,該端點需 admin token,**我量不到** |
| workflow 檔內 | `permissions: contents: read` | `test_permissions_are_least_privilege` |

> 記下是誰量的,因為這一格**沒有本機證據** —— 下次有人要複驗,得知道去哪裡看,
> 而不是以為跑一次測試就能得到它。

---

## 第一次 CI 執行:`3 failed / 774 passed`(2026-08-16)

### 成因:`actions/checkout` 預設是淺層 clone

三條紅同一個成因,而且**不是清單有問題** —— 本機用同一份清單、同一個 sha 全綠。

**本機重現(`--depth 1`,唯讀):**

```
git rev-parse --is-shallow-repository  -> true
git log --oneline | wc -l              -> 1
git cat-file -t 45a8d16                -> fatal: Not a valid object name 45a8d16
git cat-file -e 45a8d16:.claude/hooks/gate.py  -> fatal: invalid object name '45a8d16'. rc=128
```

**完整 CI 條件下的淺層 clone:**

```
FAILED tests/test_gate.py::TestLegacyNoRedlightList::test_every_entry_existed_in_the_go_live_commit
FAILED tests/test_gate.py::TestTheListItselfIsGuarded::test_an_entry_absent_from_the_go_live_tree_is_a_violation
FAILED tests/test_gate.py::TestTheListItselfIsGuarded::test_the_shipped_list_is_clean
3 failed, 771 passed, 3 skipped, 1 deselected, 3 xfailed in 59.91s
```

**數字對帳:**`771 + 3 skipped = 774`,與 CI 的 `774 passed` 相符 ——
差的正是 Linux 會執行、Windows 會 skip 的那三條 symlink。**成因確認,不是推測。**

### 修法:`fetch-depth: 0`,並寫成測試

`test_checkout_fetches_the_whole_history`。紅燈先行:

```
E       AssertionError: tests.yml 的 checkout 沒有 fetch-depth: 0(取到 [None])。
E              預設是淺層(只抓最新一筆),而 R6 要查 go-live 那棵舊樹。
1 failed, 6 passed
```

修好後 `7 passed`。

> 守它的必須是**對設定檔的斷言**,不能是對行為的斷言 ——
> **本機永遠測不出這個,本機的 clone 一直是完整的。**

### ⚠ 登記:R6 的訊息把環境問題誤報成違規(本票不修)

真正的發現不是修法。`gate.py:1160–1168` 把 `git cat-file -e` 的**任何非零 rc**
都歸成「路徑不在那棵樹裡」:

| | 意思 | R6 現在說什麼 |
|---|---|---|
| ① 路徑不在那棵樹裡 | **真違規** | 「不在…的樹裡…**新檔案要走紅燈,不是往豁免名單裡加**」✅ |
| ② 那個 commit 不在這個 repo 裡 | **環境問題** | **同一句話** ❌ |

原始訊息(淺層 clone 上,九條之一):

```
[R6] .claude/hooks/gate.py 不在機制上線 commit 45a8d16 的樹裡,不得列入紅燈豁免清單。
     清單只減不增:新檔案要走紅燈,不是往豁免名單裡加。
```

**「是後來手加的」是推論,不是量到的事實。**
在任何淺層 clone 上,R6 會擋下每一次 commit 並對九個條目逐一給出錯誤的理由。

> **fail-closed 保證的是「擋不擋」,不是「為什麼擋」。而人會照理由行動** ——
> 讀到「是後來手加的」,合理的下一步是去刪清單條目,
> 那會**把一份正確的清單改壞**,而且改完 R6 仍然紅(樹還是不在)。
> **一個方向正確而理由錯誤的擋下,比不擋更耗人:它把人推向錯的修法。**

**已立 `F-096`。修復需另開票**(要動權威層規則的判定路徑,不在裝 CI 的範圍)。
最小修法的形狀已知:進迴圈前先驗 `git cat-file -e <go-live>^{commit}`,
不成立時給另一句訊息 —— **一行就能把兩種原因分開**。

---

## 收尾:CI 第二次執行綠勾(2026-08-16)

```
778 passed, 1 deselected, 3 xfailed
```

**這是本機無法產生的證據。** 本機跑出來的是 `788 passed, 3 skipped, 3 xfailed` ——
兩個數字都對,而它們**量的不是同一個集合**。

### 對帳(兩條獨立路徑,都到 778)

| 路徑 | 算式 |
|---|---|
| **由本機總量往下扣** | `788 + 3 skipped + 3 xfailed = 794` 收集 → `− 12`(個人 pattern,4 個測試函式的參數化案例)`= 782` → `− 1 deselected = 781` 執行 → `− 3 xfailed = 778`;Linux 上 3 條 symlink 由 skip 轉 pass |
| **由第一次 CI 往上加** | `774`(第一次 CI 的 passed)`+ 3`(**修好的那三條 R6 測試**)`+ 1`(`test_checkout_fetches_the_whole_history`,第一次 CI 時它還不存在)`= 778` |

### ⚠ 對帳時抓到的一個標籤錯誤

第二條路徑的 `+3` 一度被寫成「symlink」。**數字對,標籤錯。**

第一次 CI 就跑在 `ubuntu-latest` 上,**那三條 symlink 當時已經執行而且通過** ——
它們本來就在 `774` 裡面。證據是 Windows 淺層重現的
`3 failed, 771 passed, 3 skipped`(`771 + 3 = 774`)。

所以 `+3` 是**修好的 R6 三條**,`+1` 才是新測試。

> **這比算錯更難抓:數字是對的,標籤是錯的。而對帳只驗數字 —— 標籤錯了照樣加得起來。**
> 與票 45 那次「判準掛錯規則」同形:**一個正確的東西貼在錯的對象上,不會讓任何檢查失敗。**

### 落差表的「CI 多於本機」那一列得到實證

**`3 skipped` 在 CI 上消失了。**

那三條(`tests/test_gate.py:286 / 294 / 308`)在 Windows 上因
「此環境無法建立 symlink」而跳過,**在 Linux 上真的跑了,而且過了**。

> **從寫出來到今天,它們第一次被實際執行。**

這一格單獨記,因為它是落差表裡**唯一一列 CI 涵蓋大於本機**的 ——
其餘四列都是 CI 較少。**而少的那幾列是已知代價,多的這一列是純得。**

它也是 F-096 那句話的第二個實例:**CI 餵進了本機餵不出來的輸入** ——
第一次是淺層歷史(照出 R6 誤診),第二次是**能建 symlink 的檔案系統**
(讓三條測試第一次離開 skip 狀態)。

### 落差表不改

**維持記種類不記數量。** CI 綠不改變任何一列 ——
綠證明的是「排除之後剩下的都過」,不是「排除的那些也沒問題」。

---

## 本票不做的事

- 不裝 `gh`
- 不改 repo 在 GitHub 上的預設權限設定(那是網頁動作,裁決者自己做)
- 不為了讓測試變綠而把使用者層的任何檔案上傳或重建到 CI
