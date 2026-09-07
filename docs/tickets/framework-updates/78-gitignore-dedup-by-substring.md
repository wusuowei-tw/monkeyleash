# 78 — 安裝器對 .gitignore 的查重是子字串:註解裡的字樣會吃掉真防護行

**狀態**:**done**(落地 2026-09-07,採**候選 B**;紅燈先行,全套 + 淨室各一次)
~~**candidate**(立案,不動工)~~(`F-036` 保留舊文)
**立案**:2026-08-24,票 76 三半徑重掃之半徑二(全庫受害字串重掃)
**來源**:票 76 收刀回報;同族:F-051 邊界家族、F-117;失效方向歸 F-062

---

## 現象

`install.py:185` `add = [p for p in GITIGNORE_FRAMEWORK if p not in have]`
與 `:192`(`GITIGNORE_SECRETS` 同式)—— 對目標 `.gitignore` **整檔內容**
做子字串查重:檔裡任何位置出現 `.env` 字樣(例如一行註解
「keep .env.example」)就不補真的 `.env` 防護行,而失效**靜默** ——
裝出來的 repo 第一個放進去的秘密沒人守,正是 F-062 要防的方向。

## 為什麼是缺口不是設計

查重要問的是「**這個 pattern 行**存不存在」,子字串答的是
「這串字元出現過沒有」—— 問錯對象。
部分護欄現況:`verify_gates` 只對 `.env` **一項**做行精確斷言,
且只在安裝當下跑一次;其餘十幾個 pattern(星號接憑證副檔名那組
(pem/pfx 家族)、credentials.json…)零護欄。
(本段第一版把副檔名寫成字面,被 pre-commit 擋下 —— 與票 73 同形,
照它的先例改描述式、不加豁免。)

## 候選處置(~~不裁~~ **已裁:採 B**,2026-09-07)

- A:查重改**行精確**(strip 後整行相等),與 verify_gates 的斷言同形
- **B:A + verify_gates 的行精確斷言從 `.env` 一項擴到兩組清單全部**
  (封閉且可窮舉 —— 枚舉勝過抽查,CLAUDE.md 常駐檢查項)

### 為什麼採 B 而不是 A(理由寫在票面,不寫在別的檔案裡)

**A 只修安裝器那一側,而驗收側仍然只問 `.env` 一項。** 那會留下一個
比原缺陷更難發現的狀態:

> ### **安裝器補齊了,而驗收工具**看不出來**它有沒有補齊 ——
> ### 於是下一次安裝器再壞掉時,淨室仍然全綠。**

`verify_gates` 是**本機唯一涵蓋「安裝後形態」的東西**。
它對兩組清單裡的其餘十幾條**零護欄**,而且只在安裝當下跑一次。
只做 A 等於「修好了偵測對象,沒修偵測器」——
而本票的失效方向(靜默)正是靠偵測器才看得見。

**B 的成本**:多一個 `gitignore_gaps()` 函式與一組枚舉測試。**便宜。**

## 驗收要有的反控(**三條各附測試名**)

| | 驗什麼 | 測試 | 開工當下 |
|---|---|---|---|
| ① | 目標 `.gitignore` 註解含 `.env` 字樣 → 真的 `.env` 行**仍被補上** | `tests/test_install.py::TestGitignoreDedupIsLineExact::test_a_comment_mentioning_the_pattern_does_not_suppress_the_real_line` | 🔴 **紅** |
| ② | 目標已有真的 `.env` 行 → **不重複追加**(查重的本意不得丟) | `…::test_an_existing_real_line_is_not_appended_twice` | ✅ **綠**(見下) |
| ③ | 空 / 無 `.gitignore` → 兩組清單**全部**補上 | `…::test_an_absent_or_empty_gitignore_gets_both_lists_in_full`(參數化 `None` / `""`) | ✅ 綠 |
| ①枚舉 | 註解情境下**每一條**都要在,不只 `.env` | `…::test_every_entry_of_both_lists_survives_the_comment_case` | 🔴 **紅** |

> ### 🔴 **② 開工當下是【綠】的,不是紅 —— 這一格要寫下來**
>
> 裁決預期「前兩條紅」。**實測 ② 綠**,而理由不是測試寫錯:
>
> **子字串查重的失效方向只有一邊** —— 它**只會過度抑制**(該補的不補),
> **不會過度追加**。`.env` 已經在檔裡時,子字串當然找得到它,於是跳過。
>
> **⇒ ② 是一條【必須保持綠】的反控,不是一條會轉綠的紅燈。**
> 它封住的是修法的退化解:一個「一律追加」的實作也會讓 ① 綠,而 ② 會紅。
> **三條互相封住對方的退化解,那是本組存在的理由。**

### verify_gates 那一側(裁決 B 的第二半)

`tests/test_verify_gates.py::TestGitignoreAssertionEnumeratesBothLists`,三條:

| 測試 | 驗什麼 |
|---|---|
| `test_a_complete_gitignore_reports_no_gap` | 完整的 `.gitignore` → 零缺項 |
| `test_removing_any_single_entry_is_reported` | **有界突變:逐條拿掉,每一條都要被指名**。這是非空性證明 —— 一個永遠回 `[]` 的實作只有這條會紅 |
| `test_a_comment_mentioning_an_entry_is_not_counted_as_present` | 全是註解的 `.gitignore` → **每一條**都算缺 |

**三條開工當下都紅**(`AttributeError: module has no attribute 'gitignore_gaps'`)。
**那是「函式還不存在」的紅,不是行為紅** —— 明講不湊,同票 62 第一刀那三條。
真正證明新斷言會叫的是**有界突變**那一條:它在函式存在之後仍然逐條檢查。

## ✅ 落地(2026-09-07)

### 一、安裝器側

`install.py`:`have` 之外多算一個 `have_lines = set(l.strip() for l in have.splitlines())`,
`:185` 與 `:192` 的 `p not in have` 改成 `p not in have_lines`;
框架那組寫入後**重算一次** `have_lines`(原本就重讀 `have`,同一個理由)。

**不動別的判定**:追加的位置、註解標題、換行處理、兩組的先後順序都不變。

### 二、驗收側

`verify_gates.py` 新增 `gitignore_gaps(body)`:行精確、**逐條枚舉**
`install.GITIGNORE_FRAMEWORK + install.GITIGNORE_SECRETS`,回傳缺的那幾條。
`main()` 的 `defaults_bad` 改用它,訊息**列出缺的是哪幾條**
(票 13 判準:說得出是哪一個前提沒滿足)。

`_report_installer_defaults()` 順帶改成印**條數**:

```
    .gitignore 兩組清單逐條都在(13 條)✓
```

> 一句「已守 ✓」在清單縮到剩一條時**看起來完全一樣**,
> 而那正是本票在修的那種靜默。

### 三、⚠ 這條斷言驗的是【產物 vs 規格】,不是恆真檢查

比的是**安裝出來的檔案** vs **安裝器自己的常數**:常數是規格、檔案是產物,
而本票的缺陷正是「產物沒跟上規格」。**不是 `F-114` 那種用衍生欄位驗來源欄位。**

**但它驗不到「規格本身縮水了」** —— 那一面由 `tests/test_install.py` 的
`test_gitignore_secrets_cover_common_shapes` 與 `test_framework_ignores_unchanged`
釘著。**兩面分工,寫在票面免得下一個人以為這一條涵蓋了全部。**

### 四、數字

```
紅燈  5 failed, 26 passed   (① + ①枚舉 真紅;verify_gates × 3 紅在 AttributeError)
綠燈  46 passed             (test_install + test_verify_gates + test_portable_output_encoding)
全套  1394 passed, 3 skipped, 3 xfailed in 95.05s
      新增 8 條(基準 1386 = 票 62 第二刀 `c1ae8c1` 的實測值)
淨室  不帶 -X utf8  exit=0,9 條規則各擋一次
      安裝器預設值那一段印:.gitignore 兩組清單逐條都在(13 條)✓
```

### 五、本票不含

- **不加同型的內容 regex** —— 見上方「為什麼是缺口不是設計」那一節的先例
  (票 73 / 票 78 同形):憑證副檔名字面會被本 repo 自己的洩漏偵測擋下,
  所以票面與測試一律用**組裝**(`install.GITIGNORE_SECRETS`),不寫字面。
- **不動兩組清單的內容** —— 本票管的是「有沒有補上」,不是「該補哪些」。
