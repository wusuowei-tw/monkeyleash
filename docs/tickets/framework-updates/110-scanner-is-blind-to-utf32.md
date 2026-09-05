# 110 — 掃描器對 UTF-32 檔案讀不動:BOM 嗅探只認 2 位元組,而 `FF FE` 是 `FF FE 00 00` 的前綴

**狀態**:**完成**(2026-09-05)—— 四刀 `ebe38ee`(開票)/ `917c62c`(紅燈)/ `7447008`(轉綠)/ 本 commit(CLEAN+REAL+收票),**未推**。
三層全過:**UNIT 1375 collected**(紅燈 13 條 → 全綠,新增 20 條)、**CLEAN 1251 passed + 3 skipped + 3 xfailed**、**REAL** 權威層擋下含 UTF-32 金鑰的 `git commit`,遮罩 **20 字**(字元數,不是 80 位元組)。
UNIT 兩格預測全中(差 0);**CLEAN 有一格差 3,而那 3 不是本票造成的** —— 見「七、結果」。
~~立案~~(`F-036`:舊狀態不刪)
**時鐘**:**無外部時鐘。** 票 109 有一個真實檔案在量化 repo 裡當外部時鐘;
本票**沒有** —— 目前沒有任何實際的 UTF-32 檔案被觀測到。
**這一格刻意寫出來,因為它決定了本票的優先序**,而
「姊妹票」這個說法會讓人以為兩張票的急迫性相同。
**站別**:`implement`,`ticket_id = 110`(裁決者於開工前切,實測 `.dev/pipeline.json` 已是 `implement`/`110`)
**前置**:票 109(`.dev/reports/2026-09-05T075209Z-recon-utf16-blind-spot.md` 與收票回報)
—— 本票掛在票 109 做好的 BOM 嗅探點上,那個點在 `scanner.py:241` 的 ①

> **票號取得時點:2026-09-05,開檔當下重查 `docs/tickets/framework-updates/`,
> 最大號 109,加一。`.scratch/framework-updates/issues/` 是空目錄,不撞號。**
> 不提前占號(`F-118`)。

---

## 零、⚠ **先把命題與嚴重度分開寫**(`F-149`)

**命題**:`scanner.read_text()` **解不開 UTF-32**,四種形態(LE/BE × 有/無 BOM)
× 兩種內容(純 ASCII / 含 CJK)**共八格全部走到 fail-closed 出口**。

**嚴重度:比票 109 低一階,而且是**質**的低一階。**

| | 票 109(UTF-16) | **本票(UTF-32)** |
|---|---|---|
| `read_text` | **成功**,解出夾 NUL 的亂碼 | **fail-closed** |
| `leak_scan.scan()` | **回 0** —— 靜默放行 | **回 1** —— 擋下 |
| 報告裡看得到嗎 | **看不到**(報告全綠) | **看得到**(列為 `<讀不到內容>`) |
| 缺陷形狀 | **靜默漏放** | **擋下但沒有診斷** |

⇒ **本票不是「又一個洞」,是「一個已經擋住、但擋錯理由的格子」。**
現行行為在安全性上是對的(fail-closed 的方向對);錯的是**診斷**:
它說「可能是二進位或未知編碼」,而那個檔其實是一個標準編碼的文字檔,
**裡面有一把可以被讀出來的金鑰**。

> **這一格為什麼要寫在最前面**:派工單把本票叫「票 109 姊妹票」,
> 而姊妹這個詞會把 109 的嚴重度一起帶過來。
> **兩張票的機制相鄰,後果不相鄰。**

---

## 一、實測(2026-09-05,現行碼,commit `8a1c47b`)

探針腳本在 scratchpad,產物留在 `.scratch/ticket110-utf32-probes/`(見第六節)。
樣本 `AKIA` + 16 個 `Z`,**組裝而成**(本票自己也會被掃)。

```
scanner   : C:\projects\agent-gates\.claude\portable\scanner.py
UTF16_BOMS: (b'\xff\xfe', b'\xfe\xff')
NUL_TRIGGER=0.1  UNREADABLE_MAX=0.02
DECODINGS=('utf-8-sig', 'utf-8', 'cp950', 'cp1252', 'latin-1')
```

| 探針 | 前 8 位元組 | `read_text` | `leak_scan.scan()` |
|---|---|---|---|
| `utf32-le-bom-ascii` | `ff fe 00 00 61 00 00 00` | **FAIL-CLOSED** | 1(`<讀不到內容>`) |
| `utf32-be-bom-ascii` | `00 00 fe ff 00 00 00 61` | **FAIL-CLOSED** | 1(`<讀不到內容>`) |
| `utf32-le-nobom-ascii` | `61 00 00 00 77 00 00 00` | **FAIL-CLOSED** | 1(`<讀不到內容>`) |
| `utf32-be-nobom-ascii` | `00 00 00 61 00 00 00 77` | **FAIL-CLOSED** | 1(`<讀不到內容>`) |
| `utf32-le-bom-cjk` | `ff fe 00 00 23 00 00 00` | **FAIL-CLOSED** | 1(`<讀不到內容>`) |
| `utf32-be-bom-cjk` | `00 00 fe ff 00 00 00 23` | **FAIL-CLOSED** | 1(`<讀不到內容>`) |
| `utf32-le-nobom-cjk` | `23 00 00 00 20 00 00 00` | **FAIL-CLOSED** | 1(`<讀不到內容>`) |
| `utf32-be-nobom-cjk` | `00 00 00 23 00 00 00 20` | **FAIL-CLOSED** | 1(`<讀不到內容>`) |

fail-closed 的理由字串八格相同:
`解不出可讀文字(控制字元佔比過高,可能是二進位或未知編碼)`

### 1-1 🔴 **裁決裡有一個前提,實測不成立**

裁決寫:

> 無 BOM 的 UTF-32 由票 109 的 NUL 佔比路徑涵蓋(每 4 位元組 3 個 NUL),
> **若現行門檻已涵蓋就只補正對照不改碼**。

**門檻確實被觸發了,而它接到的那隻手接不住。** 逐步實測:

無 BOM 的 UTF-32 LE(純 ASCII)在階梯**第一格** `utf-8-sig` 就解成功
(ASCII 與 NUL 都是合法 UTF-8),`_nul_ratio` = 0.75 ≥ `NUL_TRIGGER` 0.10,
⇒ 快路徑觸發 ⇒ 呼叫 `_decode_utf16(raw)` ——

```
=== _decode_utf16 對 UTF-32 位元組的實際回傳 ===
    utf32-le-bom-ascii       -> None
    utf32-be-bom-ascii       -> None
    utf32-le-nobom-ascii     -> None
    utf32-be-nobom-ascii     -> None
```

**四格全 `None`。** 因為 `_decode_utf16` 只試 `utf-16-le` / `utf-16-be`,
而 UTF-32 的位元組用 UTF-16 解出來一半是 NUL,`looks_readable` 判不可讀。

⇒ **「NUL 佔比路徑涵蓋」只在「擋下」這個意義上成立,在「讀得出金鑰」這個
意義上不成立。** 而票 109 那條路徑的用途是後者 —— 它是為了讓金鑰**被讀出來**,
不是為了讓檔案**被擋住**(擋住那件事 fail-closed 出口本來就會做)。

> **一個被觸發了的門檻,與一個接得住的門檻,是兩件事。**
> 前者留下的痕跡(快路徑真的跑了)看起來像後者。
> ⇒ **「若現行門檻已涵蓋就只補正對照不改碼」這個分支不成立,要改碼。**

---

## 二、順序陷阱 —— **先試 4 位元組 BOM**

**這是本票唯一真正需要小心的一格,寫在票面而不是只寫在程式註解裡。**

```
UTF-32 LE BOM   FF FE 00 00
UTF-16 LE BOM   FF FE
                ^^^^^ 前綴重疊
```

**`FF FE` 是 `FF FE 00 00` 的前綴。** 現行 `scanner.py:243` 寫的是

```python
if raw[:2] in UTF16_BOMS:
    t = raw.decode("utf-16")          # 由 BOM 自己決定 LE/BE
```

—— 所以一個 UTF-32 LE + BOM 的檔**會先命中 UTF-16 那一格**,
被 `raw.decode("utf-16")` 解成夾 NUL 的東西。
今天它之所以沒出事,是因為後面還有 `looks_readable` 擋著,結果掉進 fail-closed;
**但如果先加 UTF-32 的分支卻加在 UTF-16 之後,那個檔會被 UTF-16 那格搶走**,
而搶走之後的行為與今天一模一樣(fail-closed),
**看起來就像「UTF-32 的修法沒生效」,而不是「順序寫錯了」。**

⇒ **判準寫死:BOM 嗅探一律【長的先試】。**
理由不是 UTF-32 比較重要,是**短 BOM 是長 BOM 的前綴,先試短的必然截走長的**。

**另一邊沒有重疊,但要一起寫**:
`UTF-32 BE BOM = 00 00 FE FF`,而 `UTF-16 BE BOM = FE FF` ——
`00 00 FE FF` **不以** `FE FF` 開頭,所以這一側沒有前綴問題。
**寫出來是因為「兩側對稱」是一個假設,而它在這裡只有一半成立** ——
不寫的話,下一個讀的人會以為兩側同構。

**BOM 是封閉集合**,所以照 `F-087` 用枚舉不用 pattern:
四個位元組序列,列完就是列完,漏是不存在的。

---

## 三、要做什麼

1. `scanner.py` 加 UTF-32 BOM 枚舉,**排在 UTF-16 BOM 之前**。
2. 加一個與 `_decode_utf16` 同形狀的 UTF-32 解碼嘗試(附 `looks_readable` 檢查),
   並掛在**兩個**位置:NUL 快路徑、以及階梯全不可讀之後的第 ③ 步。
   **兩個位置都要**,理由與票 109 相同:快路徑讓意圖看得見,
   保證掛在不依賴門檻的那一步上。
3. `test_scanner.py` / `test_leak_scan.py` 各加正對照,審查模式二擇一一條。

**範圍就這三句。** 不改 `DECODINGS` 階梯、不動 `UNREADABLE_MAX` / `NUL_TRIGGER`
兩個門檻(它們是票 109 用實測值訂的,動它要重跑那一批實測)。

### 3-1 正對照要斷言什麼 —— **不能只斷言 `scan() == 1`**

⚠ **現行碼在八格上 `scan()` 就已經回 1 了**(fail-closed 也算命中)。
所以一條寫成 `assert ls.scan([f]) == 1` 的「正對照」**今天就是綠的**,
而它證明的是「這個檔被擋下」,不是「這個檔裡的金鑰被讀出來」。

> **`F-155` 同族:那個 `1` 回答的不是它欄名問的問題。**
> 票 109 那一批遇到的是「`0` 替沒讀過的檔作保」;
> 本票遇到的是它的鏡像 —— **一個因為讀不到而給出的 `1`,
> 被讀成「偵測有效」。**

⇒ 判準寫死:leak_scan 側的正對照**必須斷言報告裡不含 `<讀不到內容>`**,
且**含真正的 pattern 命中**。scanner 側的正對照斷言
`why is None` 且 `_AWS in text` —— 那一側沒有這個歧義。

---

## 四、驗收

- [ ] `read_text` 對四種形態 × 兩種內容(八格)全部 `why is None` 且樣本在文字裡
- [ ] `leak_scan` 側正對照:**不含 `<讀不到內容>`**,且是真正的 pattern 命中
- [ ] 審查模式二擇一一條(命中 **或** 列進未內容掃描清單,不得兩者皆無)
- [ ] 反控:UTF-8 / cp950 / 含少量 NUL 的 UTF-8 / **UTF-16 四態** 全部不變
      —— **UTF-16 那一組是本票專屬的反控**,票 109 剛修好,
      而本票動的正是它那條路徑的入口
- [ ] 全套末行與 collected 差額**先算後比**(`F-109`:基準與數字一起寫)
- [ ] CLEAN:`verify_gates` 基準 **1234** + 本票新增
- [ ] REAL:UTF-32 LE + BOM 的 `.env` 被權威層擋下,**且遮罩字元數正確**
      (字元數,不是位元組數 —— 票 109 踩過這一格)

## 五、不做的事

- **不動兩個門檻**(`UNREADABLE_MAX` / `NUL_TRIGGER`)。
- **不加 UTF-7、UTF-1、SCSU 等其他編碼。** 它們不是封閉集合的一部分,
  各自要自己的實測。**「順手多加幾個」會讓反控面失控**,
  而反控面失控的方向是**涵蓋變小**,那個方向沒有測試會抱怨。
- **不改 `DECODINGS` 階梯本身。**
- **不修「診斷訊息說『可能是二進位』」這句話的其他情境** —— 本票只讓 UTF-32
  不再走到那裡,不重寫那句話。

## 六、探針(留在 `.scratch/`,裁決者明早以檔案總管刪)

`.scratch/` 是 gitignored,以下八個檔**不進版控**:

```
.scratch/ticket110-utf32-probes/utf32-le-bom-ascii.env      168 位元組
.scratch/ticket110-utf32-probes/utf32-be-bom-ascii.env      168 位元組
.scratch/ticket110-utf32-probes/utf32-le-nobom-ascii.env    164 位元組
.scratch/ticket110-utf32-probes/utf32-be-nobom-ascii.env    164 位元組
.scratch/ticket110-utf32-probes/utf32-le-bom-cjk.env        196 位元組
.scratch/ticket110-utf32-probes/utf32-be-bom-cjk.env        196 位元組
.scratch/ticket110-utf32-probes/utf32-le-nobom-cjk.env      192 位元組
.scratch/ticket110-utf32-probes/utf32-be-nobom-cjk.env      192 位元組
```

⚠ **這八個檔含 `AKIA` 開頭的樣本字串**(組裝的假金鑰,尾巴 16 個 `Z`)。
**刀三之後它們的行為變了**:改碼前 `leak_scan` 對它們回 1 是因為**讀不到**;
現在回 1 是因為**真的命中**。⚠ 兩者都擋得下 commit,所以「不會意外進版控」
這句話前後都成立 —— **但它成立的理由換了一個**,而
**理由換了而結論沒換,是最不容易被發現的那種變化**。
它們現在**擋得下 commit**(`leak_scan` 對每一個都回 1,實測)——
所以它們不會意外進版控。但**`.scratch/` 上一次是被整個清空的**(2026-09-05),
那次事故刪掉了兩張票的語料;**本節寫的是路徑,不是「去看那些檔」** ——
上面第一節的表已經把量到的東西抄下來了。

**REAL 那一個探針不在這個清單裡** —— 它是 `real-utf32-probe.env`(repo 根),
用完當場 `git reset` + `git clean -f` 移除,**工作樹已回到乾淨**(實測 `git status --porcelain` 空)。
它不能留:它在 repo 根、不是 gitignored,留著就是一個等著被誤 add 的檔。

---

## 七、結果(2026-09-05,收票)

### 改了什麼

`.claude/portable/scanner.py` 三處(全樹只有這一份,`find` 實測無鏡像):

1. `UTF32_BOMS = (b"\xff\xfe\x00\x00", b"\x00\x00\xfe\xff")` —— 枚舉(`F-087`)。
2. `_decode_utf32()`(與 `_decode_utf16` 同形狀,含 `looks_readable` 檢查)
   與 `_decode_wide() = _decode_utf32(raw) or _decode_utf16(raw)`。
3. `read_text` 的 ① 嗅探:`raw[:4] in UTF32_BOMS` 排在 `raw[:2] in UTF16_BOMS` **之前**;
   **兩個無 BOM 的位置一起換成 `_decode_wide`**(NUL 快路徑 + 階梯全不可讀後的 ③)。

**兩個門檻一個字沒動**(`UNREADABLE_MAX` 0.02 / `NUL_TRIGGER` 0.10),照第五節。

### 順序陷阱:**中途那一次實測,把它變成了證據而不是預言**

刀二是**分兩步**做的,而中間那一步的數字正好證明了第二節那條規矩:

| 做到哪 | 實測 |
|---|---|
| 只加了 BOM 那一層(`raw[:4]` 排在 `raw[:2]` 前) | `6 failed, 136 passed` —— **BOM 四格轉綠,無 BOM 四格仍紅** |
| 接上 `_decode_wide` 的兩個呼叫點 | `142 passed in 6.05s` |

⇒ **BOM 那一層與無 BOM 那一層是兩個獨立的失效點**,
只修一個會得到一個「看起來修好了一半」的狀態 ——
而那一半正是最像真實世界的那一半(`.env` 另存成 Unicode 通常帶 BOM)。

### 三層計數 —— **先算後比**

| 層 | 基準 | 算 | 實測 | 差 |
|---|---|---|---|---|
| **UNIT** collected | `8a1c47b` 的 **1355**(= 1349 passed + 3 skipped + 3 xfailed) | 1355 + 20 = **1375** | 1369 passed + 3 skipped + 3 xfailed = **1375** | **0** |
| **UNIT** passed | 同上的 **1349** | 1349 + 20 = **1369** | **1369** | **0** |
| **CLEAN** passed | 票 109 記的 **1231** | 1231 + 20 = **1251** | **1251** | **0** |
| **CLEAN** collected | 票 109 記的 **1234** | 1234 + 20 = **1254** | 1251 + 3 skipped + 3 xfailed = **1257** | **+3** |

#### 🔴 那個 `+3` 不是本票造成的 —— 是票 109 的 `1234` 這個**標籤**有問題

票 109 第 263 行那一列的欄名是「**CLEAN 淨室 collected**」,右欄寫
`1231 passed + 3 skipped = 1234`。**那個加法沒有把 `xfailed` 算進去。**
本輪同一支腳本實測回的是 `1251 passed, 3 skipped, 3 xfailed` ——
**xfailed 也是被 collect 到的**,所以 collected 是 **1257**,不是 1254。

- **passed 那一格差 0** ⇒ 本票的 +20 完全落地,沒有多也沒有少。
- **collected 那一格差 +3** ⇒ 差的正是那 3 條 `xfailed`,
  而它們來自 `test_g1_guard.py`(票 04 的 `xfail(strict)`),**本票一個字沒動**。

⚠ **這一格我沒有回去重跑 `d2a1c67`**,所以「票 109 當時也有那 3 條 xfailed」是**推論**
(依據:本票沒有新增任何 xfail,而那 3 條的來源檔本票沒碰)。
**推論與量測不同,標明在這裡** —— 要坐實得 checkout 那個 commit 再跑一次淨室。

> **這是 CLAUDE.md 那句「報告裡的每一個數字都要帶單位」的實例:
> `1231 passed + 3 skipped` 是對的,把它叫做 `collected` 是錯的。
> 算術錯會被看出來,單位錯不會** —— 而它已經被本票引用了一次,
> 差一點就變成「本票多出 3 條」。

**本票不改票 109 的字面**(它已收,`F-036`)—— 原地登記在這裡。

### REAL —— 權威層實擋(原始輸出)

```
$ python <scratchpad>/make_real_probe.py real-utf32-probe.env
前 8 位元組   : b'\xff\xfe\x00\x00a\x00\x00\x00'
總位元組數    : 168
樣本字元數    : 20   <- 遮罩應該報這個
樣本 UTF-32 位元組數 : 80   <- 不是這個

$ git add real-utf32-probe.env
$ git commit -m REAL-probe-should-be-blocked

[洩漏偵測] 這些檔案含個人身分或機密,擋下 commit:

  real-utf32-probe.env:1
     命中 pattern:\bAKIA[0-9A-Z]{16}\b
     內容:aws_access_key_id = ***已遮罩 20 字***

乾淨的歷史要在這條規則底下誕生 —— 先把上面的洗掉再 commit。
COMMIT_RC=1
```

**三件事各自成立,要分開讀**:

| | 證據 | 為什麼要分開 |
|---|---|---|
| 擋下了 | `COMMIT_RC=1`,commit 沒有產生 | **改碼前也會擋** —— 這一格單獨看證明不了本票 |
| **是真的命中,不是讀不到** | `命中 pattern:\bAKIA[0-9A-Z]{16}\b`、**行號 `:1`** | 改碼前是 `命中 pattern:<讀不到內容>`、行號 `:0` |
| **遮罩是字元數** | `***已遮罩 20 字***` | 20 = 字元數;UTF-32 位元組數是 **80**。票 109 在這一格踩過 |

### 驗收對照

- [x] `read_text` 四態 × 兩內容(八格)全部 `why is None` 且樣本在文字裡
      —— `TestReadTextUnderstandsUtf32`,刀一全紅 → 刀二全綠
- [x] `leak_scan` 側正對照**不含 `<讀不到內容>`** 且是真正的 pattern 命中
      —— `TestUtf32IsNotReportedAsUnreadable` 五條
- [x] 審查模式二擇一一條 —— `TestReviewModeDoesNotVouchForAnUnreadUtf32File`
      ⚠ **這一條刀一時就是綠的**:fail-closed 的 `Hit` 也會把檔名列進報告,
      所以「二擇一」當時是由**錯的那一支**滿足的。刀二之後改由**命中**那一支滿足,
      **而這條測試分不出來** —— 已知限制,不是它壞掉。
- [x] 反控:UTF-16 三態 + 純 ASCII UTF-8 —— `TestUtf32DecodingDoesNotOverreach` 四條,
      刀一刀二皆綠,涵蓋沒有變小
- [x] 全套末行與 collected 差額先算後比 —— 上表,UNIT 兩格差 0
- [x] CLEAN:`verify_gates` —— 9 條規則各擋一次、權威層三態偵測正常、
      框架測試在新 repo `1251 passed, 3 skipped, 3 xfailed`
- [x] REAL:UTF-32 LE + BOM 的 `.env` 被擋且遮罩字元數正確(20 字)

### 本票沒做的事

- **沒有動兩個門檻**(第五節)。
- **沒有加 UTF-7 / UTF-1 / SCSU**(第五節)。
- **沒有重寫「可能是二進位或未知編碼」那句診斷** —— 只讓 UTF-32 不再走到那裡。
- **沒有回去重跑票 109 的 `d2a1c67` 淨室**,所以上面那個 `+3` 的歸因是推論。
- **沒有改票 109 的字面**(已收,`F-036`)。
- **沒有推**(裁決:每刀 commit,不推)。
- **friction 未發新號** —— CLEAN 那個 `+3` 是 `F-109` / CLAUDE.md「數字要帶單位」
  的既有形狀,不是新族。要不要在 `F-109` 原地加一個實例,留給裁決者。
