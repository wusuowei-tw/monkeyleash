# 10 — 同步需要一個「綁內容不綁站別」的 R2 豁免分支(ticket 01 的第二半)

## 事實

同步要寫 `.claude/portable/*.py`、`.claude/hooks/*.py`,而那些在目標 repo 是**原始碼**。
R2 因此會擋:影音現在 `stage=review`,量化在影子期,兩邊都不是可寫站。

**這不是假設。** 2026-08-11 那次手動同步就是這樣被擋的。

## 這一輪的處置(紙上流程,不是機器規則)—— **已由機制取代(2026-09-07)**

> **以下這一節記的是 2026-09-07 之前的作法,保留為紀錄,不再是現行流程。**
> 取代它的是 `gate.py` 的 `upstream_identical_staged()`(權威層,`reason=upstream-identical`),
> 見 `docs/adr/F-0016-r2-content-bound-exemption.md` 與下方「§落地」。
> **窗口從此是零** —— 不是「窗口變短」,是沒有窗口這個東西了。


由**人**在同步期間手動把該 repo 的 `current_stage` 改成 `implement`,
同步 + verify-gates + live 探針做完再改回去。

那是人的裁決放行,不是 agent 自我服務 —— agent 不碰 `pipeline.json`。
但它有紙上流程的所有毛病:靠記得改回去、靠記得只在同步期間開、
沒有任何東西驗證「改 stage 的那段時間裡只發生了同步」。
**窗口期間 R2 對整個 repo 都是開的**,不只對同步的那些檔案。

## 正解:R2 的 hash 豁免分支

批准過的設計,從未實作:**豁免綁內容,不綁站別。**

> 只放行「與上游來源逐位元組相同」的檔案寫入。

性質:

- **無法自我服務。** 豁免條件是「這個位元組序列等於上游那份」,
  agent 造不出一個上游沒有的內容來通過它 —— 要偽造得先改上游。
  這與 legacy 清單「必須在上線 commit 的樹裡」、票宣告式豁免
  「宣告在前」是同一個原則的第四次出現。
- **爆炸半徑是零。** 站別豁免會把整個 repo 的 R2 打開一段時間;
  內容豁免只放行那些「反正就是上游那份」的寫入,
  任何一個位元組不同就回到 R2 正常判定。
- **不需要記得關。** 沒有窗口,就沒有忘記關窗的失效模式。

## 難點(不要跳過)

- **上游是誰、怎麼信任它。** 目標 repo 要能指出來源並取得那份內容的雜湊。
  來源指標本身可不可信?(ticket 01 已列的同一個問題)
- **雜湊比對要用正規化過的**(行尾),否則 autocrlf 不同的機器上永遠不相等 ——
  ADR F-0013 踩過同一個坑。
- **豁免要記帳**,而且要與 gate-self 分開(`reason` 欄不同),
  否則對帳時兩種豁免混在一起,又變成一個解釋不了的數字(票 08)。
- **只豁免 R2。** R3 不豁免 —— 理由與 ADR 0004 相同:
  寫測試不需要先解鎖任何東西,而同步搬過去的檔案本來就帶著它們的測試。

## 實測窗口時長(影音側產出,裁決者代送 2026-08-13)

`docs/tickets/` 標 `skip`,所以下游的票不會流回上游,這些數字由裁決者代送。

| 輪次 | 開窗 | 關窗 | 時長 |
|---|---|---|---|
| 首輪 | `b6a9a75` 08:25:05 | `2e544e6` 09:22:43 | **57 分 38 秒** |
| 次輪 | `d2ce660` | 見影音 git log 最新一筆 | 累計逾 **1 小時 08 分** |

**這就是紙上流程的代價,已經量到了。** 票裡原本寫「窗口期間 R2 對整個 repo
都是開的」是個推論;現在它是一個小時以上的實際數字,而且是**兩次**。
內容豁免沒有窗口,所以這個數字在正解底下會是零。

## 開窗/關窗必撞髒樹的死結(同日再現)

改 `current_stage` 要寫 `.dev/pipeline.json`,而那是進版控的檔案 ——
於是**開窗這個動作本身就把工作樹弄髒**,而 sync 的第一道檢查是
「目標工作樹不乾淨就拒絕」。順序因此是死的:

```
改 stage(髒了) -> 必須先提交 -> 才能跑 sync -> 做完 -> 改回 stage(又髒了) -> 再提交
```

一次同步因此至少多兩筆 commit,而且兩筆都**只為了流程狀態**、不含任何產出。
今日兩筆(開窗、關窗)均由裁決者手動提交。

這條與上面的窗口時長是同一個根因的兩個面向:**把「誰可以寫」綁在一個
會被寫進版控的狀態上**。內容豁免不碰 `pipeline.json`,所以兩者一起消失。

## 怎樣算做完

- 目標 repo 停在任何站別,同步都寫得進去,而**不必改 `pipeline.json`**
- 內容差一個位元組 -> 回到 R2 正常判定(要實際製造一次)
- 豁免逐筆記帳,`reason` 可與 gate-self 分辨
- 這張票關掉之前,同步一律走人改 stage 的紙上流程,而且每次都要在
  回報裡寫明那個窗口開了多久
- **開窗/關窗不再需要額外的 commit** —— 死結消失,不是靠紀律繞開

### 逐條對應的測試(刀二,2026-09-07)

全部在 `tests/test_gate.py::TestR2AcceptsAnUpstreamIdenticalStagedFile`。

| 「怎樣算做完」 | 測試 | 說明 |
|---|---|---|
| 停在任何站別都寫得進去,不必改 `pipeline.json` | `test_a_staged_file_identical_to_the_upstream_object_passes_r2` + `test_the_exemption_never_writes_pipeline_json` | 後者跑遍**三個前置站**(`grill` / `spec` / `tickets`)都豁免。**範圍要說清楚**:`review` / `arch` / `idle` 在提交時本來就放行(ADR 0005),所以「任何站別」在**權威層**成立;**前哨仍以站別判**(本刀不動它),而同步工具不經前哨 |
| 差一個位元組 -> 回到 R2 正常判定 | `test_one_byte_of_drift_falls_back_to_normal_r2`(反控)+ `test_the_judgement_is_on_the_staged_bytes_not_the_worktree` 方向二 | 「實際製造一次」由前者的 `UP_SRC + " "` 完成 |
| 豁免逐筆記帳,`reason` 分得開 | `test_the_exemption_is_recorded_with_its_own_reason` | `reason=upstream-identical`;**是第四個值**,與 `ticket-declared` / `gate-self-modification` / `upstream-provenance` 都不同。欄位集合逐鍵斷言 ⇒ 票 49 的讀法不變 |
| 關票前走紙上流程、回報窗口時長 | —— | **已由機制取代**,見上方該節的標註 |
| 開窗/關窗不再需要額外的 commit | `test_the_exemption_never_writes_pipeline_json` | 位元組與 `mtime` 都不動 ⇒ 沒有髒樹 ⇒ 沒有那兩筆只為流程狀態的 commit |

另外兩條不在上表、但在 §設計 (g) 裡的:
`test_only_the_line_endings_differ`(③ 正規化)、
`test_a_missing_upstream_pointer_is_named` / `test_a_file_without_provenance_is_named` /
`test_an_unreachable_upstream_repo_is_named`(④ 缺件點名)。

## §落地(刀二,2026-09-07)

- 實作:`gate.py` 的 `staged_blob()` + `upstream_identical_staged()`,掛在
  `check()` 的 `at_commit` 前置站分支;`upstream_backed()` 加一個 `raw=` 參數
  (預設 `None` = 讀工作樹,**R3 那一側行為不變**)。
- 正規化重用 `redlight.content_hash()`(F-0013 那一次的函式),不新寫。
- 上游位置走 `read_upstream_root()`;釘的 commit 取自 `.dev/provenance.jsonl`
  該 path 最後一筆的 `upstream_commit`(= waterline,票 100)。
- ADR:`docs/adr/F-0016-r2-content-bound-exemption.md`(即帳本的 `declared_in`)。
- 裁決(2026-09-07):比對對象選 **A**(釘 provenance 那個 commit,不是上游 HEAD);
  指標檔的 G1 保護選 **乙**(原地登記,指向票 89 §三,本票不擴大)。

### 本刀與票面 §設計 的兩處差異(照實記)

1. **紅燈 ① 的站別由 `review` 改成 `spec`。** `at_commit` 的 R2 只擋前置站,
   `review` 在提交時本來就放行 —— 拿 `review` 當正控的話那條測試**從第一天就是綠的**,
   證明不了任何東西。
2. **⑥ 的「不讀 `pipeline.json`」沒有斷言,只斷言「不寫」+「判定不隨站別改變」。**
   `load_stage()` 每一次判定都要讀它才知道停在哪一站,那是構造;
   硬要斷言「沒讀」等於要求閘門不知道自己在哪一站。
   票面要的性質(「不必改 `pipeline.json`」)由「不寫 + 三個前置站都豁免」涵蓋。

---

## §設計(2026-09-07,刀一定稿)

**本節只寫設計,不動任何 `.py`。** 每一句事實都附程式位置,讓核准的人判的是判準本身,
不是一個他無從驗證的結論。

### 零、偵察結果(五項,先擺事實)

#### 一、R2 現在在哪判、判什麼

| | 前哨 | 權威 |
|---|---|---|
| 入口 | `mode_hook()` `gate.py:2598` | `mode_pre_commit()` `gate.py:3009` |
| 呼叫 | `check(path, content, exemptions=used)` `gate.py:2681` | `check(f, None, at_commit=True, exemptions=used)` `gate.py:3032` |
| 拿到的是 | **編輯後整檔內容**(`content_after_edit()`,票 07 / F-046) | **`None`** —— 一律退回磁碟 |
| R2 擋的站別 | 除 `research` / `implement` 外**全部**(含 `review`、`arch`、`idle`) | 只擋 pre-implement = `{grill, spec, tickets}`(`gate.py:1961-1968`) |

R2 判定體:`gate.py:1903-1979`。站別集合由 `.agents/pipeline-stages.yaml` 決定
(該檔 `^  - id:` **實數 8 筆**,不寫死在這裡)。

**staged 內容目前沒有任何地方取得。** 全庫 `git show` 只有一處
(`gate.py:1724`,取**上游 commit** 的物件),`git cat-file` 三處
(`:1168` HEAD、`:1228` submodule HEAD、`:1434` go-live 存在性)——
**沒有一處讀 index(`:<path>`)**。所以現況是:**pre-commit 判的是工作樹的位元組,
不是要進 commit 的那些位元組。**

#### 二、下游怎麼知道「上游是誰、同步到哪」

- **沒有 waterline 檔。** waterline 是**讀取側的推導值**:`status.py:296 _waterline_commits(recs)`
  —— 對 `.dev/provenance.jsonl` 每個 `path` 取最後一筆 `upstream_commit`,再去重(票 100)。
- 唯一的紀錄檔是 `.dev/provenance.jsonl`,由 `sync.py:556 write_provenance()` **追加**。
  欄位四個:`path` / `upstream_path` / `upstream_commit` / `content_hash`。
  **刻意不寫 `upstream_root`**(`sync.py:574`:去識別化 + 不可自助)。
- 位置指標:`~/.claude/upstream-roots.txt`,讀法 `gate.read_upstream_root()` `gate.py:1633`。
  格式恰好一行 `UPSTREAM_ROOT=<絕對路徑>`;`utf-8-sig`;多行 / 少行 / 認不得的行 → `None`。
- 既有消費者:`upstream_backed()` `gate.py:1661`(R3 的 upstream-provenance 分支)
  與票 89 A 錨 `upstream_shadow_violation()` `gate.py:2200`。
- **信任邊界(實測,與程式裡的註解不一致)**:`gate.py:1625` 寫
  「放進 G1 保護清單之後 agent 改不動它」,而 `gate.py:2222` 寫
  「`~/.claude/upstream-roots.txt` 目前沒有 G1 保護」。
  實查 `~/.claude/g1-protected.txt`(**65 行**),`grep upstream` → **不在清單裡**。
  → 後者為真,`:1625` 那句是**已經失效的宣稱**。本票的豁免會**原樣繼承**這個邊界。
- 下游那份 `gate.py` 是 `copy` 桶(`portable-manifest.txt:63 .claude/hooks/ copy`),
  **執行的是下游自己那一份** —— 本設計落地後要靠一次 sync 才會到下游。

#### 三、帳本

- `.dev/gate-exemptions.jsonl`:**199 行**,`reason` 唯一值 `gate-self-modification`(199/199)。
  **首行是票 08 之前的舊格式**(5 欄,無 `ts` / `outcome`);之後是 14 欄。
- 欄位定義 `exemption_record()` `gate.py:1782`:
  `ts` `file` `module` `ticket` `stage` `declared_in` `reason` `tool` `outcome`
  `blocked_by` `at_commit` `content_hash` `result_hash` `changes_bytes`。
- 唯一寫入者 `log_exemptions()` `gate.py:1820`,兩個強制點各呼叫一次;
  記不下來 → `SystemExit(2)`(fail-closed)。
- **程式裡已有三個 `reason` 值**,不是一個:
  `ticket-declared`(`:1758` 預設)、`gate-self-modification`(`:1913`)、
  `upstream-provenance`(`:2090`,R3 用)。
  → 票面原句「要與 gate-self 分開」**不夠**:新值要與這三個都分得開。
- 票 49 讀 `reason` 的方式:逐條清冊對「哪一條規則有帳、`outcome` 是什麼」
  (`49-a-record-when-something-is-blocked.md:42` 那張表)。

#### 四、正規化

F-0013 的行尾坑修在 **`redlight.content_hash()`** `redlight.py:44-57`:
`\r\n` → `\n`、`\r` → `\n`,再 `sha256`。
`gate` 已有轉接 `_hash_bytes()` `gate.py:1773`,而 `upstream_backed` 就是用它比
(`gate.py:1737`)。**可原樣重用,本票不新寫正規化。**

理由不只是省事:`.gitattributes` 在 manifest 裡標 `skip`(`portable-manifest.txt:48`),
下游**不保證**有 `*.py text eol=lf` —— 不正規化的話,這條規則在 autocrlf 機器上永遠不成立,
而失敗方向是「擋住做對事的人」。

### 一、設計(逐條回答)

#### (a) 兩層都做

理由二:

1. **站別涵蓋互補。** 只做權威層 → 停在 `review` 的下游在**前哨**就被擋(票面記的影音正是
   `stage=review`);只做前哨 → 停在 `spec` / `tickets` / `grill` 的下游在 **commit** 被擋。
   而「怎樣算做完」要的是**任何站別**都寫得進去。
2. **既有判準**:`logged_exemption_backed` docstring `gate.py:1285`——
   「豁免的兩個時點要綁同一個條件,否則**鬆的那一邊定義了整條規則**」。

**但兩層判的對象不同,必須分開寫:**

- **前哨判 `content`(編輯後整檔)。`content is None` ⇒ 不豁免(fail-closed)。**
  退回磁碟等於判**寫入前**的位元組 —— 而「寫入前那份與上游相同」正是同步情境的常態,
  於是一個「把上游檔改壞」的寫入會拿到豁免。這是 F-046 / 票 07 的同一個坑。
- **權威判 staged blob(`git show :<path>`),不是工作樹。** 同一句話換一個時點:
  commit 要判的是**要進 commit 的那些位元組**。這需要新增一個 `staged_blob()` helper
  —— 現況全庫沒有讀 index 的地方(見上「零、一」)。

> **附帶發現(本票不修,登記為候選票)**:R3 現有的 `upstream_backed` 讀的是**工作樹**
> (`gate.py:1735`),而測試 `test_a_file_matching_the_upstream_object_needs_no_local_redlight`
> (`tests/test_gate.py:1737`)傳進去的 `content` 與磁碟**不同**、仍取得豁免 ——
> 即 R3 那一半判的是磁碟,不是編輯後結果。
> **本票不改 R3**(見 (f)),但新寫的 R2 分支不得照抄這個形狀。

#### (b) 比對對象 = 上游**那個 commit 的同路徑 blob**,不是上游工作樹

工作樹未提交、可變;`write_provenance()` docstring 已寫死
「provenance 的效力全部來自『查得到那個 git 物件』」。

**哪一個 commit —— 三個選項,請裁決:**

| | 判準 | 好處 | 代價 |
|---|---|---|---|
| **A(建議)** | 該 path 在 `.dev/provenance.jsonl` **最後一筆**的 `upstream_commit`(= 該 path 的 waterline) | 整段 `upstream_backed` 連**五個** fail-closed 分支一起重用,**零新信任面** | 沒有紀錄的檔案不豁免;而紀錄由 sync 在**寫完內容之後**才發(`sync.py:676-681`)→ **手動逐檔同步**一個上游更新過的檔案時,紀錄還釘在舊 commit,仍被擋 |
| B | 上游 `HEAD` | 手動同步能過,不依賴紀錄順序 | 判準綁在一個**會動的 ref** 上;且「碰巧等於上游 HEAD」的本地檔也拿得到豁免 —— 它從來沒被同步過 |
| C | A 為主,A 不成立時退到 B | 涵蓋最廣 | 是兩個判準的**聯集**,所以擋不住 B 的代價;且訊息與帳本要說得出「這次是哪一個判準放行的」,否則對帳又是一個解釋不了的數字 |

**建議 A 的理由**:票面性質段第一句是「agent 造不出一個上游沒有的內容」。
A 額外要求「這個檔案曾經被登記為同步成品」,是**更窄**的門。
窄的一邊出錯 = 擋住做對事的人(而且有出口:`sync.py --certify` 補證,`sync.py:536`);
寬的一邊出錯 = 放行一個從未被同步過的檔案。

**A 的代價不是理論**:sync 工具路徑不受影響(它用 python io 直接寫,不經前哨;
pre-commit 時紀錄已在),受影響的是**手動逐檔同步** —— 也就是 2026-08-11 那一次的作法。
選 A 等於宣告「手動逐檔同步不是支援路徑,同步走 `sync.py`」。

#### (c) 正規化

重用 `redlight.content_hash()`(經 `gate._hash_bytes()`):`\r\n` / `\r` → `\n` 再 sha256,
**兩邊都算過再比**。不新寫。理由見「零、四」。

#### (d) 缺件一律不豁免,訊息點名缺哪一個(fail-closed)

五個分支各自的話術**不共用一句話**(票 13 C:修法不同就不能共用):

| 缺什麼 | 訊息要說 | 現成位置 |
|---|---|---|
| 指標檔不可用 | 點名 `~/.claude/upstream-roots.txt` 與格式 | `gate.py:1714` |
| 沒有 provenance 紀錄 | 「它不是同步進來的成品」 | `gate.py:1701` |
| 缺 `upstream_commit` | 是 sync 產出的紀錄有問題,不是指標檔 | `gate.py:1718` |
| 上游 repo / 物件問不到 | 印 `commit[:12]:path` 與上游根 | `gate.py:1726` |
| 內容漂移 | 判準就是「相同」,改一個位元組就回到本地 | `gate.py:1741` |

**這五句已經寫好了**,R2 分支直接轉述其 `why`,不另外造話術。

#### (e) `reason = "upstream-identical"`

與 `gate-self-modification` / `upstream-provenance` / `ticket-declared` **三個**都不同。
同一次 `check()` 對同一個檔案可能同時進 R2 與 R3 兩筆(`reason` 不同)——
那是對的,票 49 要**逐規則**算。

`declared_in` 填**新開的 ADR**(刀二寫,暫名 `docs/adr/F-00NN-r2-content-bound-exemption.md`),
不填票號路徑:`docs/tickets/` 標 `skip`(`portable-manifest.txt:324`),
填一個下游不會有的檔案就是 `F-122` 那個形狀。

#### (f) 只豁免 R2,R3 不豁免

R3 已有自己的 `upstream-provenance` 分支(`gate.py:2086`),理由與 ADR 0004 相同:
**寫測試不需要先解鎖任何東西。**
實作落點在 `gate.py:1903-1979` 之間,且**不得 `return None`** ——
要像 `gate_self`(`:1958`)那樣**落到下方的 R3**。

#### (g) 紅燈清單(七條)

票面列的六條,加第七條 —— 它是 ② 的另一個入口,漏掉它 ② 就只守住一半。

| # | 種類 | 內容 | 現行 |
|---|---|---|---|
| ① | 正控 | 停在 `review`、待寫內容與上游 waterline blob **逐位元組同** → `check()` 回傳不含 `[R2` | **必紅** |
| ② | **反控** | 同 ①,但差一個位元組(結尾多一個空白)→ **仍含 `[R2`** | **現行綠,落地後必須維持綠** |
| ③ | 正控 | 只差行尾(上游 LF / 本地 CRLF)→ 豁免成立 | **必紅** |
| ④ | 正控 | `read_upstream_root()` 回 `None` → 不豁免,**且訊息含 `upstream-roots.txt`** | **必紅**(現行連豁免都沒有,訊息是純站別訊息) |
| ⑤ | 正控 | `exemptions` bucket 收到一筆 `reason == "upstream-identical"`,且不取代同 bucket 的 `gate-self-modification` | **必紅** |
| ⑥ | **反控** | 整條走完,`.dev/pipeline.json` 的 mtime 與位元組**皆不變** | **現行綠,必須維持** |
| ⑦ | **反控** | 前哨 `content is None` → **不豁免** | **現行綠,必須維持** |

②⑥⑦ 是反控:它們現在就綠。**綠不是通過,是基準線** ——
它們要擋的是實作把 fail-closed 翻成 fail-open 而正控全綠。

### 二、工時估(以本刀實際用量為基準)

| 刀 | 內容 | 估 |
|---|---|---|
| 一 | 唯讀偵察 + 本節定稿(**已完成**) | ~1.0 h |
| 二 | 七支紅燈測試 + ADR 骨架(先紅,不實作) | 1.5–2.0 h |
| 三 | 實作:`upstream_identical(rel, raw)` + `staged_blob()` + R2 分支 + 記帳 | 1.5–2.0 h |
| 四 | 全套 pytest + `gate.py` 全規則驗證 + `CLAUDE.md` R2 行 / ADR 定稿 | 1.0–1.5 h |
| 五(可選) | 下游實測一次真同步,量窗口 = 0 | 0.5–1.0 h |

合計 **5.5–7.5 h**,不含裁決等待。
**基準**:刀一的 1.0 h 是實際值;二至五是從它外推,外推的獨立性是零 ——
刀二做完要回頭對一次。

### 三、要裁決的兩件事

1. **(b) 選 A / B / C。** 建議 A。選 A 等於宣告「手動逐檔同步不是支援路徑」。
2. **指標檔要不要進 G1 保護清單。** 本票的「無法自我服務」原樣繼承票 89 A 錨的邊界,
   而該邊界**現在是開的**(實測不在 65 行的清單裡)。
   選項:(甲)本票內把 `upstream-roots.txt` 加進 `~/.claude/g1-protected.txt`
   —— **那一步只有人能做**(ADR 0009),agent 只能備草稿與驗收;
   (乙)不動,原地登記缺口並指向票 89 第二階段(git 背書的錨)。
   **建議乙**:甲會讓本票夾帶一個需要人手操作的使用者層改動,而票 89 已經有出口。
   但無論選哪個,`gate.py:1625` 那句失效的註解要在刀四順手改掉。
