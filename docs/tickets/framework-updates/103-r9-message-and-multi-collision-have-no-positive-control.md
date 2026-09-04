# 103 — R9 的訊息內容與多重撞號沒有正對照:規則會擋,而「擋下時說了什麼」沒有被問過

**狀態**:**立案、未實作**(2026-09-04)
**時鐘**:**無外部時鐘。** 本票的理由是 R9 的三個判定路徑在今天仍無斷言,而它們在 `gate.py` 裡已經存在很久 —— 不是新引入的風險,是一直沒有被問過的一格
**站別**:`idle`(立案時);刀二開工前由 Jeff 切成 `implement`,`ticket_id = 103`
**前置**:票 83(R9 立案)、票 98(兩份標題判準對帳)、**票 102(本票照它的三刀形狀做)**

> **票號取得時點:2026-09-04,動手當下重查兩個位置** ——
> `docs/tickets/framework-updates/` 與 `.scratch/framework-updates/issues/`
> (後者是空目錄,`F-155` 的形狀:只查第一個存在的位置會得到「0 張票」),
> 合併後最大號 **102**,加一。`ls | grep "^103"` 零命中。**不提前占號**(`F-118`)。

---

## 一、問題

**R9 的存在性沒有問題** —— 它有 11 條測試,涵蓋正控、四條反控、fail-closed、
接線、以及對真實 log 的正對照。**票 102 那種「語料在、斷言不在」的洞,R9 沒有。**

> ### **缺的是另一種:規則會擋這件事被問過了,而【擋下時說了什麼】沒有。**

R9 的擋下訊息有兩個資訊欄位(`gate.py:1372`,逐字):

```python
            "[R9] %s 裡的 %s 發了兩次以上(%s)。\n"
```

三個 `%s` 依序是:log 路徑、**撞到的號**、**撞在哪幾行**。
現有測試問過第二個,**沒有問過第三個**。

### 缺口一:訊息裡的行號,沒有任何斷言問過

票 83 的驗收條件逐字(`docs/tickets/framework-updates/83-friction-numbers-have-no-uniqueness-check.md:86`):

```
- **方向 A**:人工造一份含兩個 `## F-999` 的 log → 擋,且訊息**點名是哪個號、哪兩行**
```

**「哪個號」有測試,「哪兩行」沒有。**

現行兩條訊息斷言(`tests/test_gate.py`)逐字:

```python
:2629        assert v and "F-007" in v[0], v
:2668        assert v and "TSI-001" in v[0], v
```

兩條問的都是**號**。產生行號的那三行程式碼 ——
`enumerate(lines, 1)`(`gate.py:1359`)、
`dupes.setdefault(num, [seen[num]]).append(lineno)`(`:1365`)、
`"、".join("第 %d 行" % n for n in dupes[num])`(`:1370`)
—— **沒有一條斷言碰過它們的輸出**。

> **這與 `F-105` 是同一格**(訊息類斷言有兩種,而只有一種抓得到判定壞掉):
> `"F-007" in v[0]` 在 `at` 整個算錯時**仍然會綠**。

### 缺口二:同一個號出現三次以上,沒有測試

`gate.py:1365` 的 `.append(lineno)` 在第三次撞號時才會被走第二遍。
現有 10 份 tmp log **每一份最多兩次**,所以那條路徑從來沒有被走到。

要問的兩件事都沒有被問:
① 三次撞號是**一筆**發現還是三筆(現行實作是一筆);
② 三個行號**全部**都在訊息裡嗎。

### 缺口三:兩個不同的號各自重複,沒有測試

`gate.py:1369` 的 `for num in sorted(dupes)` 是一個迴圈,而
**現有測試每一份 log 都只有一個撞號** —— 迴圈永遠只跑一圈。
沒有被問過的兩件事:
① 兩個撞號會產出**兩則**訊息嗎;
② `sorted()` 那個排序有沒有生效(順序是決定性的還是 dict 順序)。

### 為什麼這三格容易被讀成「已經有涵蓋」

**因為 R9 的測試數看起來很多**(11 + 11 + 10 = 32 個案例),而
**數量分佈在「會不會擋」那一軸上** —— 四條反控、一條 fail-closed、一條接線、
一條真實資料正對照,全部問的是同一個問題的不同輸入。

> **一條規則的測試數,不會告訴你它們問的是幾個問題。**
> (`F-137` 的同一句話換到測試上:一份清單不會帶著它自己的長度。)

---

## 二、範圍:9 條正控

**口徑**:每一條都必須斷言**擋下訊息的具體內容**或**發現的筆數**,
不得只斷言 `assert v`(truthy)—— 那一層既有測試已經有了,再加一條是重複而不是涵蓋。

全部加在 `tests/test_gate.py::TestFrictionNumbersAreUnique`(現 `:2588-2687`)。

| # | 名稱(暫定) | 語料 | 斷言 | 補的缺口 |
|---|---|---|---|---|
| 1 | `test_the_message_names_both_line_numbers` | 兩個 `## F-007`,分別在第 1、5 行 | 訊息同時含 `第 1 行` 與 `第 5 行` | 一 |
| 2 | `test_the_message_lists_every_line_when_a_number_repeats_three_times` | 三個 `## F-007` | 三個行號**全部**在訊息裡 | 一 + 二 |
| 3 | `test_three_occurrences_are_one_finding_not_two` | 同上 | `len(v) == 1` | 二 |
| 4 | `test_two_distinct_collisions_produce_two_findings` | `F-001` ×2 與 `F-002` ×2 | `len(v) == 2` | 三 |
| 5 | `test_the_findings_are_ordered_by_number` | `F-002` 先撞、`F-001` 後撞 | `v[0]` 含 `F-001`、`v[1]` 含 `F-002` | 三 |
| 6 | `test_a_third_level_heading_is_not_an_issuing_line` | 兩個 `### F-001` | `== []` | **判定矩陣(gate 側)** |
| 7 | `test_a_heading_without_a_letter_prefix_is_not_an_issuing_line` | 兩個 `## 118 甲` | `== []` | 同上 |
| 8 | `test_a_longer_token_is_not_swallowed` | `## F-118x` 與 `## F-118` | `== []` | 同上(邊界) |
| 9 | `test_a_hash_without_a_space_is_not_an_issuing_line` | 兩個 `##F-001`(無空白) | `== []` | 同上 |

### 第 6–9 條為什麼算新增,而不是重複

**這四個判定條件今天只在 `.claude/portable/` 那一側有測試**
(`tests/test_friction_heading.py:39-74`),而那支測的是
`.claude/portable/friction_heading.py` 的 `HEADING`,**不是 `gate.py` 的 `_FRICTION_HEADING`**。

兩份是**各自獨立的字面**,不是同一個物件:

```
.claude/portable/friction_heading.py:47   HEADING = re.compile(r"^##\s+([A-Za-z]+-\d+)(?:\s|$|[^\w-])")
.claude/hooks/gate.py:1319         _FRICTION_HEADING = re.compile(r"^##\s+([A-Za-z]+-\d+)(?:\s|$|[^\w-])")
```

`tests/test_gate.py::TestBothHeadingCriteriaAgree` 做的是**對帳**(兩邊給同樣答案),
而對帳綠有兩種來源:**兩邊都對**,以及**兩邊一起錯**。
那個 class 自己的 docstring 逐字寫過這件事(`:350`):

```
        """**先釘住 R9 那一份自己是對的** —— 否則「兩邊一致」也可能是一起錯。"""
```

⇒ 而它「釘住」的方式是拿 5 筆 CORPUS 比對,**那 5 筆裡沒有 `###`、沒有無空白、沒有邊界案例**。
第 6–9 條補的正是這四格。

---

## 三、反控:不新增

既有四條反控(缺號、併記段、內文引用、跨前綴)方向已經對,
且票 102 的經驗是**反控在突變輪裡應該全綠** —— 三輪突變都是把判定弄窄或弄鬆,
而反控問的是「有沒有擋過頭」。

> 有反控跟著紅的話,意思不是規則壞了,是**反控寫錯了**(票 102 `:200` 逐字)。

**本票不新增反控**,但三輪突變**都要記錄反控的顏色**。

---

## 四、三輪有界突變 —— 預測寫在這裡,跑之前

> **紀律(票 102 `:180` 逐字)**:
> 「一條從來沒有紅過的測試,與一條永遠不會紅的測試,在報告上長得一樣。」
>
> **本節的每一個數字都在動手之前寫下。** 跑完之後**不修改本節**,
> 差異寫進落地紀錄 —— 事後改預測等於沒有預測(`F-132`)。

### ⚠ 一處與裁決指令的偏離,寫在這裡等裁

裁決逐字寫的是「**改 `gate.py:1319`**」(即 `_FRICTION_HEADING` 那一行)。
**輪三做不到** —— 缺口一與二的輸出來自**去重迴圈**(`gate.py:1357-1377`),
不是正則。**動 `:1319` 不可能讓「訊息含行號」的斷言變紅。**

⇒ 本票的三輪是 **`:1319` 兩輪 + `:1365` 一輪**。
**這一格請 Jeff 在切站前確認**;不同意的話輪三改成別的形狀,而缺口一與二會失去它們的紅燈來源。

### 🔴 反向枚舉:真實 `friction-log.md` 有幾個消費者(2026-09-04,輪①失準後補)

**第一版預測只數了明著讀它的那一個**(`test_the_shipped_log_is_clean`),
漏掉了**暗著讀它的那一個** —— `mode_pre_commit()` 會呼叫 `check_friction_numbers()`
(`gate.py:3006`),而

```
gate.py:1310   FRICTION_LOG = os.path.join(ROOT, "docs", "agents", "friction-log.md")
gate.py:  28   ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

**`FRICTION_LOG` 在 import 時就算好了** —— 之後 `monkeypatch.setattr(gate, "ROOT", tmp_path)`
**改不到它**。於是任何走 `mode_pre_commit()` 的測試,都在讀**本 repo 真實的** friction log。

**全庫枚舉**(`grep -rn "mode_pre_commit" tests/*.py`,逐一讀過斷言):

| # | 位置 | 斷言 | 有 patch R9? | 對「真實 log 多一個違規」 |
|---|---|---|---|---|
| 1 | `test_gate.py:987` | `rc == 1` | ❌ | 免疫(rc 本來就是 1) |
| 2 | `test_gate.py:2042` | `rc == 1` + `"--no-verify" not in err` | ❌ | 免疫 |
| 3 | `test_gate.py:2051` | `"會留下紀錄" not in err` | ❌ | 免疫 |
| **4** | **`test_gate.py:2059`** | **`"1 項" in err`** | ❌ | 🔴 **脆弱(斷言的是【項數】)** |
| 5 | `test_gate.py:2521` | 只讀原始碼字串,不呼叫 | — | 免疫 |
| 6 | `test_gate.py:2682` | `rc == 1`,**且自己 patch 掉 `check_friction_numbers`** | ✅ | 免疫 |
| 7 | `test_gate.py:2966` | `rc == 1` | ❌ | 免疫 |
| 8 | `test_gate.py:2996` | `rc == 1` | ❌ | 免疫 |
| 9 | `test_r5_mounts.py:578` | `rc == 1` + `[R5]` + 內容 | ❌ | 免疫 |
| 10 | `test_r5_mounts.py:595` | `rc == 1` + `[R5]` + 內容 | ❌ | 免疫 |
| **11** | **`test_r5_mounts.py:609`** | **`rc == 0`** | ❌ | 🔴 **脆弱(期望乾淨)** |
| 12 | `test_r5_mounts.py:625` | `rc == 1` + 兩則訊息 | ❌ | 免疫 |

**交叉驗證(獨立於上表)**:全庫只有這兩處做「數量/乾淨」斷言 ——

```
grep -rn "項\" in err"            -> tests/test_gate.py:2059   (唯一命中)
grep -rn "mode_pre_commit() == 0" -> tests/test_r5_mounts.py:609 (唯一命中)
```

> ### **⇒ 判準不是「這條測試提不提 R9」,是【它斷言的東西會不會被多一個違規改變】。**
> 斷言 `rc == 1` 的**全部免疫**(多一個違規,rc 還是 1);
> 斷言**項數**或 **`rc == 0`** 的**全部脆弱**。全庫恰好各一條。

### 輪 ① — 拿掉標題層級限制

**突變**:`gate.py:1319`,`^##\s+` → `^#+\s+`

~~**預測紅 2 條(新 1 + 既有 1):**~~
~~| 新 | `test_a_third_level_heading_is_not_an_issuing_line`(#6) |~~
~~| 既有 | `test_the_shipped_log_is_clean`(`:2684`) |~~
~~**預測綠**:`TestBothHeadingCriteriaAgree` 三條全綠。~~

> **第一版預測(2026-09-04,動手前)實測不中:預測 2,實測 4。**
> 原文加刪節線保留不刪(`F-036`)。**漏的兩條與成因見上一格的反向枚舉。**

#### **第二版預測(2026-09-04,重跑前寫)——紅 4 條(新 1 + 既有 3)**

| | 哪一條(逐字) | 為什麼 |
|---|---|---|
| 新 | `tests/test_gate.py::TestFrictionNumbersAreUnique::test_a_third_level_heading_is_not_an_issuing_line` | `### F-001` ×2 變成撞號 |
| 既有 | `tests/test_gate.py::TestFrictionNumbersAreUnique::test_the_shipped_log_is_clean` | 真實 log 有 `## F-058`(946 行)與 `### F-058 家族註記`(979 行);放寬層級後撞號。全檔 `^###` 像發號的行 = **1**,所以剛好一個撞號 |
| 既有 | `tests/test_gate.py::TestEnforcementDoesNotTeachItsOwnBypass::test_the_block_message_still_says_what_was_violated` | `_blocked_stderr`(`:2025-2037`)把 R4/R5/R6 都 patch 掉了,**唯獨沒 patch R9**;真實 log 多一項 → 訊息從「1 項」變「2 項」→ `:2059` 的斷言失敗 |
| 既有 | `tests/test_r5_mounts.py::TestR5IsActuallyInvokedAtTheAuthoritativeLayer::test_a_clean_repo_does_not_block` | `_wire_pre_commit`(`:534-555`)同樣沒 patch R9,而它 patch 的 `ROOT` **救不了 import 時定死的 `FRICTION_LOG`**;`rc` 從 0 變 1 → `:609` 失敗 |

**預測綠(逐條寫出來,不只寫「其餘全綠」):**
- `TestBothHeadingCriteriaAgree` 三條 —— 它的 5 筆 CORPUS **沒有 `###` 開頭的行**,gate 側答案不變。
- 上表第 1/2/3/6/7/8/9/10/12 號 —— 斷言 `rc == 1` 或字串不存在,多一個違規不改變它們。
- 四條既有反控 —— 突變方向是**放寬**,反控問的是有沒有擋過頭,不該被影響。

**預測 passed = 1270 − 4 = 1266。**

### 輪 ② — 拿掉尾端邊界

**突變**:`gate.py:1319`,刪去 `(?:\s|$|[^\w-])`

**預測紅 1 條(新 1 + 既有 0):**

| | 哪一條 | 為什麼 |
|---|---|---|
| 新 | `test_a_longer_token_is_not_swallowed`(#8) | `## F-118x` 會被讀成 `F-118`,與 `## F-118` 撞號 |
| **既有** | **無** | **實測依據**:真實 log 中 `^##\s+<字母>-<數字>` 之後緊接字母或底線的行 = **0**;緊接 `-` 的行 = **0**。所以 `test_the_shipped_log_is_clean` 不受影響 |

> ⚠ **這個 0 是重量過的。** 第一次探針寫成
> `^##[[:space:]]+[A-Za-z]+-[0-9]+[[:alnum:]_]`,回報 **146**(= 全部命中)——
> 因為 `[0-9]+` 會**回溯**,吃掉部分數字讓最後一位去配 `[[:alnum:]]`。
> 改用不含數字的字元類 `[A-Za-z_]` 之後才是 **0**。
> **那個 146 會跑、會給數字、看起來合理,而它量的不是這個問題**(`F-151` 家族)。

**預測綠**:`TestBothHeadingCriteriaAgree` 三條 —— 5 筆 CORPUS 裡
`## 併記於 F-118(…)` 仍然不匹配(`[A-Za-z]+` 配不上 `併`),gate 側答案全部不變。

#### **第二版預測(2026-09-04,反向枚舉後)——【枚舉後不變】,仍是紅 1 條**

理由要寫出來,不能只寫「不變」:
反向枚舉找出的兩條脆弱測試,**只有在真實 log 的判定結果改變時才會紅**。
而本輪突變是拿掉尾端邊界,對真實 log 的影響已量過:

```
號碼後緊接字母或底線的行 = 0
號碼後緊接 - 的行        = 0
```

⇒ **真實 log 在本輪突變下仍然乾淨**,`check_friction_numbers()` 仍回 `[]`,
`mode_pre_commit()` 的違規項數與 `rc` 都不變 ⇒ 那兩條**不會紅**。
**預測 passed = 1270 − 1 = 1269。**

### 輪 ③ — 丟掉第一次出現的行號

**突變**:`gate.py:1365`,
`dupes.setdefault(num, [seen[num]]).append(lineno)` → `dupes.setdefault(num, []).append(lineno)`

**預測紅 2 條(新 2 + 既有 0):**

| | 哪一條 | 為什麼 |
|---|---|---|
| 新 | `test_the_message_names_both_line_numbers`(#1) | 訊息只剩第二次的行號 |
| 新 | `test_the_message_lists_every_line_when_a_number_repeats_three_times`(#2) | 三個行號只剩兩個 |
| **既有** | **無** | `:2629` 與 `:2668` 斷言的是**號**不是行號;`test_a_duplicate_number_is_a_violation` 只斷言 truthy;`test_the_shipped_log_is_clean` 對乾淨 log 回 `[]`,不進迴圈 |

> **輪 ③ 的既有紅是 0,這件事本身就是缺口一的證據** ——
> 一個把行號整個算錯的突變,**現有 32 個案例一條都不會咬**。

#### **第二版預測(2026-09-04,反向枚舉後)——【枚舉後不變】,仍是紅 2 條**

理由:本輪突變動的是**去重迴圈**(`gate.py:1365`),而那段程式碼
**只有在已經偵測到撞號時才會執行**(`if num in seen:`)。
真實 log **沒有撞號**(`test_the_shipped_log_is_clean` 現在是綠的),
所以 `dupes` 恆為空、迴圈不進、`check_friction_numbers()` 仍回 `[]`。
⇒ 兩條脆弱測試看到的違規項數與 `rc` 都不變 ⇒ **不會紅**。
**預測 passed = 1270 − 2 = 1268。**

### 三輪共通的驗收

| | |
|---|---|
| **反控** | 三輪都必須**全綠**;有反控紅 ⇒ 反控寫錯,不是規則壞 |
| **還原** | 每輪突變後 `git diff --stat .claude/hooks/gate.py` **無輸出**。**查 diff 不是查記憶**(票 102 `:219` 逐字:「『我改回來了』與『它現在是原樣』是兩句話」) |
| **收刀後** | 對動工前的 commit 再查一次 `git diff <sha> --stat -- .claude/hooks/gate.py`,無輸出 |
| **原始輸出** | 三輪的 pytest stdout 逐字貼進落地紀錄,不摘要 |

---

## 五、驗收條件

1. 9 條正控全部加進 `tests/test_gate.py::TestFrictionNumbersAreUnique`,寫完當下**全綠**
   (與票 102 相同:這是**特徵化測試**,判定邏輯本來就在)。
2. 三輪有界突變**逐輪**:改 → 跑 → 對預測 → 還原 → `git diff --stat` 查空。
3. 三輪的**預測 vs 實測**逐格對照寫進落地紀錄;**不中的格子不得改預測,要寫為什麼不中**。
4. 全套數字逐名對帳,**基線 = 2026-09-03 的 1261 passed / 3 skipped / 3 xfailed**
   (出處:票 102 `:213`「收刀 1261」)。
   ⚠ **基準與被對的 commit 不同就先重算再談差異**(`F-109`)——
   本票動工時的 HEAD 是 `ba578e5`,**而 `ba578e5` 是純文件輪(4 個 `.md`,零個 `.py`),
   所以基線 1261 應該仍然成立;實測不等於 1261 時,先查那三筆文件 commit,不要直接歸因到本票**。
5. 票面狀態行改「完成」,附三刀 sha 與 CI run id。

---

## 六、本票不含

- **R4 的 102 形狀**。裁決:本輪不做。**兩個前置都不是寫測試能解決的**(登記如下)。
- **R8 的 102 形狀**。裁決順序是 R9 → R8 → R4,R8 另票。
- **`gate.py` 的任何行為改動。** 本票只加測試 + 有界突變 + 還原。
  三輪突變的目的是**證明新測試會咬**,不是修 R9。

### 候選登記(**不占票號** —— `F-118`:不提前占號)

**候選一:R4 走 102 形狀**。兩個前置,都要裁決不是實作:

| 前置 | 內容 |
|---|---|
| ① 鏡像要不要建起來 | 2026-09-04 實測:`.claude/skills/` 與 `skills/` **在本機都不存在**,而 `gate.py:2704-2706` 對不存在的鏡像 `continue`。⇒ `check_skill_copies()` 對真實 repo **由構造回空**,「對真實 repo 的正對照」那一格現在做不出來 |
| ② 突變輪跑哪台機器 | R4 六個訊息出口裡的兩個(symlink 斷裂、symlink 指向正典之外)在 Windows 上 **skip**;票 102 `:236` 逐字記過那 3 個 skip 就是 `test_gate.py:451/459/473`。⇒ 在本機做突變輪,預測的紅會落在被 skip 的測試上,而 **skip 不是紅** |

**候選二:`CLAUDE.md` 的硬連結那句要更正**。
現行逐字寫著「本機實測為檔案層硬連結(目錄各自獨立、檔案是同一個實體檔)」,
而 2026-09-04 實測**兩個鏡像目錄都不存在**。
⚠ **不下「這是缺陷」的結論** —— 鏡像已 gitignore、由 `scripts/skills-update.sh` 建,
沒跑過就不存在是合理的。要更正的是那句話的**時態與條件**,不是它的判斷。
裁決:**不在本輪改。**

**候選三(本票立案途中順帶發現,未列入裁決):兩處行號引用已過期。**
`gate.py` 的 `_FRICTION_HEADING` 現在在 **`:1319`**,而兩處引用仍寫 `gate.py:1283`:

```
.claude/portable/friction_heading.py:28   `.claude/hooks/gate.py:1283` 有一份語意相同的 `_FRICTION_HEADING`,
tests/test_gate.py:300                    R9(`gate.py:1283` 的 `_FRICTION_HEADING`)**嚴**:前綴必須是字母、
```

**這是 `CLAUDE.md`「引名不引行號」那一格的又一個實例**(行號是位置,標題是身分)。
**不在本票改** —— 本票只碰測試,改註解會讓突變輪的 `git diff --stat` 驗收混進無關異動。

**候選四(friction 候選,2026-09-04 輪①失準時發現):
測試 helper 逐條關規則時漏掉一條,而【`ROOT` 被換掉】讓它看起來已經隔離了。**

`tests/test_r5_mounts.py:534-555` 的 `_wire_pre_commit` docstring 逐字寫著
「把 `mode_pre_commit()` 的**鄰居全部停掉**」,並列出四條,每條附**不同的理由** ——
**那份清單本身寫得比多數地方都仔細,而它漏了 R9。**

真正讓人不會回頭查的是第一行:

```python
    monkeypatch.setattr(gate, "ROOT", str(root))
```

**`ROOT` 換掉了,讀起來像「整個 repo 已經被換成 tmp_path」** ——
於是「還有誰在讀真實 repo」這個問題不會被問第二次。
而 `FRICTION_LOG` 是 import 時就從 `ROOT` 算好的常數,**patch `ROOT` 對它無效**。

> **一份【逐條列出並各附理由】的關閉清單,比一份沒有理由的清單更難發現漏項** ——
> 理由欄讓讀的人相信每一條都被想過,而**沒被想到的那一條不會出現在清單上**。
> (`F-108` 的同一句話換到 monkeypatch 上:驗收清單天生偏向意圖,
> 而「我沒打算關的那條」不會出現在待辦清單裡。)

**候選五(票候選):`FRICTION_LOG` 在 import 時算好,`patch ROOT` 隔離不到。**

| | |
|---|---|
| 現況 | `gate.py:1310` `FRICTION_LOG = os.path.join(ROOT, ...)`,模組載入時定死 |
| 後果 | 任何 `monkeypatch.setattr(gate, "ROOT", tmp)` 都**隔離不掉 R9** —— 測試以為在打 tmp_path,實際在讀本 repo |
| 修法 A | **呼叫時算**:`check_friction_numbers()` 內用 `os.path.join(ROOT, ...)`,讓它跟著 patch 走 |
| 修法 B | **helper 明關 R9**:兩支 helper 各加一行 `monkeypatch.setattr(gate, "check_friction_numbers", lambda: [])` |
| 取捨 | A 修根因、涵蓋未來所有 helper,但**動的是 `gate.py`**(守衛本體);B 只動測試、風險低,但**下一個寫 helper 的人仍然會漏** |
| 範圍 | 同一個形狀可能不只 `FRICTION_LOG` —— **開票時要先枚舉 `gate.py` 裡所有 import 時就綁死 `ROOT` 的常數**,不要只修這一個 |

**不在本票修** —— 本票的驗收條件是 `gate.py` 三輪突變後回到原樣,
在同一輪改它會讓 `git diff --stat` 那道驗收失去意義。

---

## 七、為什麼是現在

不是因為 R9 有風險 —— **R9 是這三條裡最不可能壞的**(單一正則 + 一個 dict 迴圈,
`gate.py:1332-1340` 的 docstring 逐字說它「零誤報、零判斷、極便宜」)。

**是因為它最便宜,而票 102 的形狀需要先被走過第二遍。**

> 一個只做過一次的流程,與一個可重複的流程,**在紀錄上長得一樣**。
> R9 這一輪要證的不只是 R9,是**票 102 那套三刀 + 三輪突變換一條規則還跑不跑得動** ——
> 而那件事要在最便宜的規則上先問,不是在最貴的(R4)上問。
