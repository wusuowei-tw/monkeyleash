# 111 — R7 邊界族第四次:repo 內 `tmp/` / `scratchpad/` 被當成系統暫存(併 A-3 票號前綴)

**狀態**:**done**(2026-09-07)—— 紅燈 5 紅 / 14 綠 → 全綠 19;全套 **1439 passed, 3 skipped, 3 xfailed**。
~~**candidate**(立案,不動工)~~(`F-036` 保留舊文)
**立案**:2026-09-07,第六站(arch)第二次診斷 → A 桶 A-1 + A-3
**來源**:`docs/audits/2026-09-07-arch-round-2.md`(A-1 / A-3);同族:F-051 邊界家族、F-117
**站別**:立案時 `arch`;動工前由裁決者改 `current_stage` 與 `ticket_id`

> ## ⚠ 併票宣告:**A-3 就是票 77**
>
> A-3(票號前綴無邊界)在 2026-08-24 已經開過 **票 77**,狀態 candidate、未動工。
> 本票**吸收**它,不是重開一張新的 —— 票 77 原地不刪、不改號,加一行指到這裡。
>
> **為什麼併**:兩者是同一個家族(比對缺邊界)、同一支檔案(`gate.py`)、
> 同一種修法(把「以某字串開頭」換成「帶邊界的比對」)、同一批對照組風險
> (改嚴之後會不會擋到本來該放的)。分開修的話,第二張票會在第一張改完之後
> 面對一份已經動過的 `gate.py`,而兩張票的驗收會互相污染。
>
> **反對意見先寫下來**:併票會讓兩件事共用一次裁決,而 A-3 的爆炸半徑
> (R3 豁免看錯票)與 A-1(R7 放行 repo 內寫入)不同。
> 若裁決者要分開,拆回兩張的成本是**低的** —— 本票的兩節本來就分開寫。

---

## 一、A-1 —— `_target_allowed` 把相對路徑當成絕對路徑

### 現象

```
.claude/hooks/gate.py:399    "/tmp/": "系統暫存,在 repo 之外",
.claude/hooks/gate.py:400    "scratchpad": "工作階段暫存目錄,在 repo 之外",
.claude/hooks/gate.py:549    haystack = "/" + tok.lstrip("/")
.claude/hooks/gate.py:551        needle = "/" + t.strip("/") + "/"
```

`tok = "tmp/evil.py"` → `haystack = "/tmp/evil.py"` → `needle = "/tmp/"` 命中 → **放行**。
`scratchpad` 同理,而且是**任意深度**:`a/b/scratchpad/x.py` 也命中。

### 為什麼是缺口不是設計

那兩行註解**逐字寫著「在 repo 之外」**,而比對完全不驗這件事 ——
它只問「路徑成分裡有沒有這個名字」。

票 76 A3 把子字串改成成分比對時,補的是**成分邊界**,**沒有補根錨定**。
而正典形狀寫得很清楚:

```
.claude/portable/scanner.py:455-458
    **兩種錨定,不要合成一種**(票 39 / P2 第五件):
      skip_roots 根錨定 —— 鏡像的位置是構造決定的,不會浮動
      skip_parts 任何深度,但**兩側帶 `/` 邊界**
```

`_target_allowed` 的 docstring **引用了那一段**,而實作只做了其中一種。
**引用一份正典不會讓你實作它** —— 這是 F-086 的形狀
(判準寫在別的地方,而註解不是機制),差別在於這次判準被抄進了同一支 docstring。

### 爆炸半徑

`tmp/` 與 `scratchpad/` 都不在 `NON_SOURCE_DIRS`(`gate.py:124-139`),
所以那裡寫進去的是**原始碼**。R7 的職責是把寫入收回檔案工具、讓 R1–R6 在**寫入當下**適用;
這一格漏掉之後,那條路徑上的寫入在寫入時完全沒有規則。
**提交時仍會被 R2/R3 看到**(pre-commit 掃 staged 檔案),所以不是整條穿透 ——
但那正是 ADR 0008 說的「只剩一道」。

### 探針形狀(零寫入,純函式)

```python
# 洞成立的證據
gate.bash_write_violation("tee tmp/evil.py")               # 期望 None(放行)
gate.bash_write_violation("tee a/b/scratchpad/x.py")       # 期望 None(放行)
gate.bash_write_violation("rm -rf tmp/")                    # 期望 None(放行)← 最貴的一格
```

不碰檔案系統、不碰 git、不碰 `pipeline.json`。

### 驗收(正控 + 反控,反控是硬條件)

| # | 種類 | 指令 | 修好之後 |
|---|---|---|---|
| 1 | 正控 | `tee tmp/evil.py` | **擋** |
| 2 | 正控 | `rm -rf tmp/`(repo 內) | **擋** |
| 3 | 正控 | `tee a/b/scratchpad/x.py` | **擋** |
| 4 | **反控** | `tee /tmp/x.py`(POSIX 絕對路徑) | **放行**(設計許可,不得變) |
| 5 | **反控** | 真正的系統暫存:`tee %TEMP%\x.py` / `tee $env:TEMP\x.py` / `tee /var/folders/...`(macOS) | **放行** |
| 6 | **反控** | `tee .dev/notes.jsonl`、`tee build/out.tmp` | **放行**(票 76 對照組,不得變) |

> **第 5 格是本票最容易做錯的一格。** 「repo 內的 `tmp/`」與「這台機器的系統暫存」
> 在字串上長得很像,而**把根錨定寫成「必須以 `/tmp/` 開頭」會擋掉 Windows 與 macOS 的
> 真實暫存目錄** —— 那是誤擋方向,而誤擋的規則最後會被整條關掉(F-031)。
>
> **⚠ 這一格的判準要在動工前先裁**:「在 repo 之外」到底怎麼判 ——
> (a) 路徑絕對且不在 `ROOT` 底下(要 `os.path.abspath` + `commonpath`,而**字串裡的相對路徑
> 沒有 cwd 這個資訊**);(b) 維持字串判定但要求絕對前綴 + 平台暫存變數白名單。
> **兩案的失敗方向相反**,不要在寫碼時順手決定。

## 二、A-3 —— 票號前綴無邊界(原票 77)

### 現象

```
.claude/hooks/gate.py:1279            if not name.startswith(str(ticket_id)):
```

`ticket_id="1"` 命中 `10-*.md`;`"0"` 命中 `01-*.md`。
命中後 `committed_declaration()` 讀的是**那張票**的 `**Untested by decision:**`,
於是**別張票裁過的模組**豁免掉當前票的 R3。

### 三個實作,兩個修了一個沒修

```
.claude/portable/status.py:649-661     已修(prefix = str(ticket) + "-"),且逐字寫著
                                       「gate.py 有語意相同的一份(:1265),**本票不修它**」
.claude/portable/mcp_server.py:220-231 已修(prefix = str(num) + u"-")
.claude/hooks/gate.py:1279             **沒修**,而它在權威層
```

**這是 F-085 的形狀(修好一個命中之後沒找同類),而且是知情版** ——
不修的那一份被寫進了另一份的 docstring 裡。**寫下來不等於做掉。**

### 探針形狀(零寫入,純函式)

```python
mods, rel = gate.ticket_untested_modules("framework-updates", "1")
# 期望 rel == "docs/tickets/framework-updates/10-sync-needs-an-r2-exemption-bound-to-content.md"
# 回到別張票 ⇒ 洞成立。宣告集合是不是空的無關緊要 —— 錯的是它看了哪一張票。
```

### 驗收

| # | 種類 | 情境 | 修好之後 |
|---|---|---|---|
| 1 | 正控 | `ticket_id="1"`,樹裡有 `10-*.md` | 回 `(set(), None)` —— **不命中別張票** |
| 2 | 正控 | `ticket_id="0"`,樹裡有 `01-*.md` | 同上 |
| 3 | **反控** | `ticket_id="10"`,樹裡有 `10-*.md` | **命中那一張**(不得變) |
| 4 | **反控** | 兩個票目錄都存在(`.scratch/<f>/issues` 與 `docs/tickets/<f>`) | 兩處都找,行為不變(`TICKET_DIRS` 的語意,票 24) |

> ⚠ **補零不在這一層**(照 `status.py:655-658` 的同一條判準):
> `"1"` 回 `None` 是**正確行為**,不是要靠補零去救。
> 下游 repo 不見得補零到兩位,把命名慣例埋進判定會在別的 repo 出錯。

## 三、估工

| 刀 | 內容 | 估 |
|---|---|---|
| 一 | 「在 repo 之外」判準裁決(A-1 的 (a)/(b) 兩案)+ 探針實跑三條 | 0.5–1.0 h |
| 二 | 紅燈:A-1 六條 + A-3 四條,先跑紅(其中 4 條反控現行就綠) | 1.0–1.5 h |
| 三 | 實作:`_target_allowed` 根錨定 + `ticket_untested_modules` 邊界 | 1.0–1.5 h |
| 四 | 全套 + 淨室驗證 + 票 77 收尾(狀態改 done 並指回本票) | 0.5–1.0 h |

合計 **3.0–5.0 h**。**基準**:與票 10(實測 5.5–7.5 h)相比少一刀,
因為本票不新增判定函式、不動帳本格式、不碰兩層時點語意。

## 四、裝新下游前要不要

**要。** 兩條都要:

- A-1:下游的 repo 內**很可能真的有 `tmp/`**(建置暫存、測試輸出),
  而那正好是這一格會誤放行的地方。
- A-3:下游的票號慣例未必補零,`1` / `0` 這種短票號在下游更容易出現。

## 五、落地(2026-09-07)

### 實作(`gate.py`,三處 + 一處)

| 位置 | 改動 |
|---|---|
| `BASH_ALLOWED_TARGETS` 的三行理由 | 「在 repo 之外」改成程式真的驗的那句話:「**只在解析後落在 repo 之外時適用**」 |
| 新 `OUTSIDE_REPO_ONLY = ("/dev/null", "/tmp/", "scratchpad")` | 把「這一項是 repo 外才成立」從**理由欄的措辭**變成**程式讀得到的東西**(F-086:註解不是機制) |
| 新 `_resolves_inside_repo(tok)` | `realpath` 後 `normcase` 比對,**前綴帶 `os.sep` 邊界**;相對路徑以 repo 根為基準;例外一律回 `True`(= 更嚴) |
| `_target_allowed` | `if inside and t in OUTSIDE_REPO_ONLY: continue` —— **只加這一個方向**,repo 外的判定一個字都沒動 |
| `ticket_untested_modules` | `startswith(str(ticket_id) + "-")` |

### 實測(同一支唯讀探針,修前 / 修後)

```
                              修前     修後
rm -rf tmp/                   放行  ->  擋      ①
tee tmp/x.py                  放行  ->  擋
tee <repo>/scratchpad/x.py    放行  ->  擋      ②
tee a/b/scratchpad/x.py       放行  ->  擋
tee /tmp/x.py                 放行  ->  放行    ③ 反控
tee <系統暫存>/…/scratchpad/x  放行  ->  放行    ③ 反控
tee <repo 外>/…/tmp/x.py       放行  ->  放行    ④ 反控
tee .dev/notes.jsonl          放行  ->  放行    反控
tee build/out.tmp             放行  ->  放行    反控
tee pkg/evil.py               擋    ->  擋      反控

ticket_id="1"    -> docs/tickets/framework-updates/10-….md  ->  None      正控
ticket_id="0"    -> docs/tickets/framework-updates/01-….md  ->  None      正控
ticket_id="11"   -> 11-….md                                 ->  11-….md   反控
ticket_id="111"  -> 111-….md                                ->  111-….md  反控
```

### ⚠ 驗收第 5 格的**實測更正**(照實記)

票面原本把「真正的系統暫存(`tempfile.gettempdir()` 之下、`%TEMP%`、`/tmp`)→ 放行」
整格寫成**反控**。**實測不是這樣**:

| 目標 | 修前 | 修後 |
|---|---|---|
| `/tmp/x.py`(POSIX) | 放行 | 放行 |
| `<gettempdir()>/x.py`(Windows,`…\AppData\Local\Temp`) | **擋** | **擋** |
| `%TEMP%\x.py` / `$env:TEMP\x.py` | **擋** | **擋** |

Windows 的真實暫存目錄**在本票之前就已經被擋**(許可項是字面的 `/tmp/`,
而 `Temp` ≠ `tmp`,比對區分大小寫);環境變數則是「**答案不在字串裡**」,
R7 依設計不展開它。

**本票不改這一格,也沒有讓它變糟。** 要不要放行 Windows 的系統暫存是**另一個判準**
(需要一個「這個路徑是不是本機系統暫存」的判定,而那要引入 `tempfile.gettempdir()`
當作比對基準 —— 那是一個新的信任面)。**登記在此,不夾帶。**

> 這一格是「反控必須先量過才知道它是不是反控」的標本:
> 一條寫成「必須維持放行」的反控,如果它**現在根本不放行**,
> 那它就不是反控,是一條偷渡進來的新需求 —— 而它會在紅燈時被當成「本票的洞」。

### 測試

`tests/test_gate.py`:

- `TestUnallowedWriteTargets` 新增 **9 條**(①②③④ + 4 條 repo 內許可反控 + 1 條分類完整性)
- `TestTicketNumberMatchingCarriesABoundary` 新增 **5 條**(2 正控 + 3 反控),
  用自建的 tmp git repo(`01-a.md` / `10-b.md` / `11-c.md` / `111-d.md`),不依賴實際票樹

`test_every_allowed_target_is_classified_inside_or_outside` 是**機制那一條**:
許可表新增一項而忘了分類,它會紅 —— 否則 `OUTSIDE_REPO_ONLY` 就是第二份手工名單。
