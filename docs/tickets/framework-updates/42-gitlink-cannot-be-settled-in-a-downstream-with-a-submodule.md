# 42 — 含 submodule 的下游無法落定 gitlink:leak_scan 與 sync 各判錯一次對象

**排程**:立即。station-④ TDD,紅燈先行。
**來源**:下游(台股資訊收集)實測回報,錨點 `3c0e6ed`。
**嚴重度**:任何含 submodule 的下游,gitlink bump 做不出來,**且因此無法再同步框架**。

**兩部分必須在同一張票落地。** 只修 (a):下游能 bump 了,但要先跑 `sync` 才拿得到
修好的 `leak_scan`,而 `sync` 因 gitlink 未落定被拒 → 循環未解。
只修 (b):`sync` 過得去、拿得到新框架,但 bump 仍被 `leak_scan` 擋 → 循環未解。

下游**目前沒有合法出口**:`--no-verify` 等於關掉洩漏偵測、改本地框架檔等於失去
provenance 豁免、手動複製上游檔案繞過 `sync` 同理。已停手等修。

---

## (a) `staged_paths()` 把 gitlink 當檔案讀

### 現象(下游原始輸出)

```
=== staged 清單 ===
.dev/gate-exemptions.jsonl
.dev/test-runs.jsonl
data_collector

=== leak_scan --staged 完整輸出 ===
[洩漏偵測] 這些檔案含個人身分或機密,擋下 commit:

  data_collector:0
     命中 pattern:<讀不到內容>
     內容:讀不到檔案:[Errno 13] Permission denied: '<下游 repo 的絕對路徑>/data_collector'

乾淨的歷史要在這條規則底下誕生 —— 先把上面的洗掉再 commit。
```

`data_collector` 是目錄,`open()` 在 Windows 上得 `PermissionError`
(POSIX 上會是 `IsADirectoryError`),落進「讀不到內容」的 fail-closed 分支。

### 根因([scanner.py:169-185](.claude/portable/scanner.py#L169-L185))

`git diff --cached --name-only` 對 submodule 條目回傳**目錄路徑**;
index 裡它的 mode 是 `160000`(gitlink),值是一個 commit sha,**沒有 blob 內容可掃**。
回傳前無任何項目型別過濾。

```
$ git ls-tree HEAD data_collector
160000 commit 928e1a2ca55285b6b26f5e7880218d989f178a2b	data_collector
```

### 為什麼「讀不到就擋」在這裡是錯的答案

該規則的正當性是「**讀不到不等於乾淨**」—— 對一個**應該是檔案**的東西成立。
gitlink 不是讀不到,是**根本沒有內容這回事**。把「沒有內容」判成「內容讀不到」,
產生一個**永遠無法滿足的條件**:使用者沒有任何合法動作能讓它變乾淨,因為沒有東西可以洗。

同一個形狀在本框架已經是第二次(票 41:R3 把「gitlink 沒有 blob」判成
「HEAD 讀不到」,於是 submodule 底下的既有檔案永遠拿不到合格紅燈)。
**兩次都是:一個為「檔案」設計的判定,碰到 mode 160000 時把「不適用」讀成「不合格」。**

### 修(裁決者已核可的切法,**不得自行放寬**)

依 **index 的 mode** 過濾掉 `160000`,而且是**看得見的跳過**:

- 取型別用 `git ls-files --stage -z` 的 mode 欄比對(或 `git diff --cached -z --raw`
  的 dst mode)。**不得改用 `os.path.isdir()`** —— 判定依據會跑到檔案系統去,
  而 **index 的 mode 才是權威**
- 跳過的 gitlink **必須進報告**,理由同票 39 的「未內容掃描清單一律進報告」
- 外層對 gitlink 的正確語意是「**這一格由別人守**」(內層有自己的 pre-commit 跑
  `leak_scan`,下游實測),**寫清楚比靜默跳過重要**

**介面形狀**:`staged_paths()` 的回傳型別**不變**(仍是路徑串列),
跳過的 gitlink 由呼叫端傳入的收集串列帶出來 ——
形狀抄 `gate.check(..., exemptions=[])`。理由是票 13 C:
`(bool, reason)` 那次簽名改動,忘了解包的呼叫端**每一個都拿到豁免**,
fail-closed 整條翻成 fail-open 而測試全綠。**簽名不變就沒有那個失敗模式。**

**報告位置的邊界**:gitlink 進報告,但**在 pre-commit 模式下不得讓退出碼變 1** ——
現行 `not_scanned` 非空即回 1(見 [leak_scan.py:218-222](.claude/portable/leak_scan.py#L218-L222)),
把 gitlink 丟進那個桶會**擋掉每一次 bump**,也就是換一種方式重演本票的缺陷。
`--review` 模式照票 39 的規矩要人逐一定性(那裡回 1 是設計,不是誤擋)。

---

## (b) `gitlink_unsettled()` 也判錯對象

### 現象

即使 (a) 修好,下游仍解不開:bump 需要新版 `leak_scan`,而取得新版要跑 `sync`,
`sync` 又因 gitlink 未 bump 而拒絕。

[sync.py:208-224](.claude/portable/sync.py#L208-L224) 的 `refuse_if_dirty()` 呼叫
`gitlink_unsettled()`,後者把「內嵌 repo 已前進但外層未記錄」判為髒
([sync.py:202-204](.claude/portable/sync.py#L202-L204))。

### 為什麼這個對象是錯的

`refuse_if_dirty` 自陳的理由是「**在未提交的變更上覆寫,出事時分不出是誰改的**」,
而它自己也寫著:「內嵌 repo 的內部 modified / untracked 不算 ——
那在 sync 的寫入面之外,sync 從不寫它底下的東西。」

**gitlink 指標落沒落定,同樣不在 sync 的寫入面上。**
sync 不寫 submodule 底下任何東西,也不寫 gitlink 本身。
「內層前進、外層未記錄」不會讓 sync 的覆寫變得無法歸屬 —— 它跟 sync 要防的風險**沒有交集**。

用本專案自己的判準句:**這個檔案壞掉或消失時,正確行為是什麼**。
gitlink 指標落後,sync 覆寫框架檔的結果**完全不變**。

### 精確切三態(裁決者已核可)

| 情況 | 判定 | 理由 |
|---|---|---|
| HEAD sha ≠ index sha(已 stage 未提交的 bump) | **維持為髒** | 它會被下一次提交掃進去 —— 那才是真的未落定,**且落在寫入面上** |
| index sha ≠ 內層 HEAD(內層前進、外層未記錄) | **放寬** | 不在 sync 的寫入面上;且在 (a) 未修時,下游**無法**落定它 |
| 內嵌 repo 讀不到 | **維持為髒** | fail-closed,問不出來不等於乾淨 |

### 這會推翻兩條既有測試 —— 記名推翻,不靜默改掉

票 17 的裁決寫在這兩條裡,它們現在斷言的正是要放寬的那一格:

| 測試 | 位置 | 處置 |
|---|---|---|
| `test_an_unrecorded_gitlink_advance_still_blocks` | [test_sync.py:371](tests/test_sync.py#L371) | **反轉**:改斷言不再拒絕 |
| `test_gitlink_unsettled_reports_an_advanced_inner_repo` | [test_sync.py:419](tests/test_sync.py#L419) | **反轉**:改斷言不再回報 |

反轉時**在測試的 docstring 裡寫下推翻的理由與票號**,不是刪掉重寫 ——
照 F-036 的規矩:前一版裁決作廢要留痕,因為它在當時的理由下被引用過。
`test_a_staged_but_uncommitted_gitlink_bump_blocks`([test_sync.py:380](tests/test_sync.py#L380))
與 `test_an_unreadable_embedded_repo_fails_closed`([test_sync.py:427](tests/test_sync.py#L427))
**一個字都不動** —— 它們守的正是這次放寬**不得**碰到的兩格。

---

## 紅燈計畫

| # | 紅燈 | 對應 | 守什麼 |
|---|---|---|---|
| 1 | staged 清單含一格 gitlink 時,`leak_scan --staged` 回 **0**(不擋) | (a) | 本票主張 |
| 2 | 被跳過的 gitlink **出現在報告裡**,並說明「由內層 repo 自己守」 | (a) | 靜默跳過不算修好 |
| 3 | `staged_paths()` 回傳的清單**不含**那格 gitlink,且判定來自 **index 的 mode** | (a) | 判定依據不得跑到檔案系統 |
| 4 | `gitlink_unsettled`:index ≠ 內層 HEAD **不再**被判髒 | (b) | 放寬確實生效 |
| 5 | **負控**:HEAD ≠ index(已 staged 的 bump)**仍**被判髒 | (b) | 放寬不得擴大到寫入面上那一格 |
| 6 | **負控**:內嵌 repo 讀不到**仍**被判髒 | (b) | fail-closed |
| 7 | **負控**:一般檔案照掃、命中照擋(掃描面沒有被 (a) 弄小) | (a) | 少了它,「一律跳過」也會讓 1–3 全綠 |
| 8 | **整條循環**:含 gitlink 的下游能 `sync` **且**能 bump(兩步接著跑) | (a)+(b) | 單測任一半都證明不了循環解開 |

第 5 條是下游點名要求的:**沒有它,這次放寬會在下一次重構時被順手擴大成
「gitlink 一律不管」**,而那會讓一個已 staged、下次就會被提交的 bump
在 sync 覆寫時無法歸屬。

第 7、8 條是本票這邊補的:第 7 條防「(a) 的過濾寫寬了」——
`160000` 是**枚舉一個值**,不是「跳過看起來像目錄的東西」(F-087)。
第 8 條是因為兩部分**必須一起**才解得開循環,而兩個單測各自綠**不蘊含**循環解開。

---

## 同類入口:外層 `gate.py` 的 `staged_paths()` 有**同一個洞**(要裁決)

CLAUDE.md 常駐檢查項:**收了一個入口,就回頭問它的同類入口在哪。**
`staged_paths` 在本框架有**兩份**:`.claude/portable/scanner.py`(下游回報的那份)
與 [gate.py:2240-2254](.claude/hooks/gate.py#L2240-L2254)(權威層自己用的那份)。
下游沒撞到第二份,只是因為 hook 的順序是 `leak_scan || exit 1` 在前,**還沒走到 gate**。

本機唯讀實測(未寫任何檔案):

```
is_source_path('data_collector')      = True      ← 無副檔名、top 不在非原始碼清單 → 判成原始碼
check('data_collector', at_commit=True) 逐站:
  idle       -> None
  grill      -> [R2/commit] data_collector:current_stage='grill' 是前置站,卻要提交原始碼。
  spec       -> [R2/commit] …'spec' 是前置站,卻要提交原始碼。
  tickets    -> [R2/commit] …'tickets' 是前置站,卻要提交原始碼。
  research   -> [R2/範圍] data_collector:current_stage='research' 只能寫 research/ 底下的原始碼。
  implement  -> None
  review     -> None
```

也就是:**在四個站別上,一次純 gitlink bump 會被 R2 當成「提交原始碼」擋下**,
而使用者同樣沒有合法動作能讓它變乾淨 —— 那一格不是原始碼,是一個 commit 指標。
(`implement` / `review` 放行純屬巧合,不是因為判定認得 gitlink。)

**要裁決的是範圍,兩個選項:**

- **A(建議)——** 併進本票:`gate.py` 的 `staged_paths()` 同樣依 index mode 濾掉
  `160000`,並在 `--pre-commit` 的訊息裡明講「gitlink 由內層 repo 自己守」。
  **代價**:本票多動一支檔案(R3 要多一組紅燈),範圍從兩部分變三部分。
  **好處**:下游修好 (a)(b) 之後,不會在 `spec`/`tickets` 站再撞一次同一個形狀 ——
  而那一次會長得像新缺陷。
- **B ——** 另開一張票。**代價**:框架這邊會有一段時間「一半的入口修好了」,
  而下游若在前置站 bump 就會撞上;那次的擋下訊息說的是 R2,
  **完全不會提到 gitlink**,診斷成本比這次高。

**不自行決定**:裁決者已核可的切法只寫了 (a)(b),擴大範圍是裁決者的事,不是我的。
未裁決前**不動 `gate.py`**。

---

## 順帶觀察(**不在本票範圍**,不動)

`test_an_unreadable_embedded_repo_fails_closed`([test_sync.py:427](tests/test_sync.py#L427))
用 `shutil.rmtree(..., ignore_errors=True)` 砍內嵌 repo 的 `.git`。
本機實測(票 41):Windows 上 git 的**鬆散物件檔是唯讀的**,`rmtree` 會
`PermissionError: [WinError 5]` —— 帶了 `ignore_errors=True` 就變成**部分刪除**。
那條測試現在會綠,靠的是「`HEAD`/`config` 可寫、被刪掉了,所以 `rev-parse` 失敗」,
**不是靠 `.git` 真的消失**。結論沒錯,但它的成立理由比它宣稱的窄。
記在這裡,不在本票動它 —— 那是 `/code-review` 的事。

---

## 怎樣算做完

- 上表 8 條各有測試;1–4 先紅(5–7 是負控,修法前本來就綠,**要用一次故意寫錯的
  修法量過它們會咬**,否則是裝飾;8 修法前紅)
- `staged_paths()` 的**簽名不變**,gitlink 由收集串列帶出
- 兩條被推翻的測試**反轉並在 docstring 記名理由**,不刪
- 全套測試綠
- friction 記一則 `F-089`:同一個「mode 160000 被當成檔案」的形狀,
  在本框架的第二、第三個入口(票 41 是第一個)
- 備案(下游列出的內層 tag + 暫退 HEAD)**不啟用** —— 它讓內層一段時間處於
  「已完成的工作被從 HEAD 拿掉」的狀態,中途中斷就只靠 tag 可達。
  列在這裡只為了讓否決 (b) 的人知道代價

## 引入點(下游的定位,備查)

下游實測 `d500917`(2026-08-13 13:29)只 staged 一個 gitlink 並成功提交,
當時外層 hook(2026-08-12 09:52 安裝)已在呼叫 `leak_scan`。
最近一次同步(`e51c8e3` → `3c0e6ed`)的 `leak_scan.py` 與 `scanner.py` diff
均未觸及 staged 項目型別處理(下游已逐行確認)。
故推定引入點為 `ffb1fc7` → `f19a418`(2026-08-13 13:53,補 `-z` 並改寫 `staged_paths`)。
下游無法直接驗證該版本:當時 `.claude/` 尚未納管,
`git show d500917:.claude/portable/leak_scan.py` 回 `exists on disk, but not in 'd500917'`。
