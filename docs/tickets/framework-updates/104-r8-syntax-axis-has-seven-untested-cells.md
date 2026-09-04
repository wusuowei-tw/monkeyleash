# 104 — R8 的語法軸有七個空格,而封閉集合本來就枚舉得完

**狀態**:**立案、未實作**(2026-09-04)
**時鐘**:**無外部時鐘。** 理由是 R8 的語法軸是**封閉集合**(`ast.Import` / `ast.ImportFrom` 兩個節點型別窮舉得完),而現有 8 個案例只覆蓋其中 4 格
**站別**:`idle`(立案時);刀二開工前由 Jeff 切成 `implement`,`ticket_id = 104`
**前置**:票 102(R1,三刀 + 三輪突變的原型)、**票 103(R9,同一套形狀的第二次)**、`F-051`(R8 的邊界問題)

> **票號取得時點:2026-09-04,動手當下重查兩個位置**
> (`docs/tickets/framework-updates/` 與 `.scratch/framework-updates/issues/`,後者為空目錄),
> 合併後最大號 **103**,加一。`ls | grep "^104"` 零命中。**不提前占號**(`F-118`)。

---

## 一、問題

R8 的判定住在 `imports_research()`(`gate.py:885-908`),它**只認兩個 AST 節點型別**:

```python
899	    for node in ast.walk(tree):
900	        if isinstance(node, ast.Import):
901	            for alias in node.names:
902	                if alias.name.split(".")[0] == RESEARCH_ROOT:
903	                    return True
904	        elif isinstance(node, ast.ImportFrom):
905	            # from research / from research.x import ...；相對 import(module=None)不算
906	            if node.module and node.module.split(".")[0] == RESEARCH_ROOT:
907	                return True
908	    return False
```

> ### **兩個節點型別是一個【封閉集合】,而封閉集合該用枚舉,不是用樣本。**
> `CLAUDE.md` 逐字:「封閉且可窮舉時,**枚舉勝過比對** —— 因為
> **比對的漏是未知的,枚舉的漏是不存在的**」。
> 現有 8 個案例是**樣本**,不是枚舉。

### 現況:11 格裡只有 4 格有案例

**下表的 `node` / `module` / `level` / `imports_research()` 四欄全部是 2026-09-04 實測**
(探針載入 repo 裡那一份 `gate.py`,不自己複製判定邏輯 —— `F-152`:
自己抄一份判定去驗判定,證明的只是我抄對了):

```
RESEARCH_ROOT = 'research'

case                             | node           | module             | level | imports_research()
---------------------------------------------------------------------------------------------------
1  import research               | ast.Import     | None               | None  | True
2  import research.explore       | ast.Import     | None               | None  | True
3  import research as r          | ast.Import     | None               | None  | True
4  import research.explore as e  | ast.Import     | None               | None  | True
5  import os, research           | ast.Import     | None               | None  | True
6  from research import explore  | ast.ImportFrom | 'research'         | 0     | True
7  from research.explore import t| ast.ImportFrom | 'research.explore' | 0     | True
8  from research import *        | ast.ImportFrom | 'research'         | 0     | True
9  from . import research        | ast.ImportFrom | None               | 1     | False
10 from .. import research       | ast.ImportFrom | None               | 2     | False
11 from .research import x       | ast.ImportFrom | 'research'         | 1     | True
-- import research_utils         | ast.Import     | None               | None  | False
-- from research_helpers import x| ast.ImportFrom | 'research_helpers' | 0     | False
-- import researched             | ast.Import     | None               | None  | False
-- from my_research import x     | ast.ImportFrom | 'my_research'      | 0     | False
```

| 格 | 現有案例 | 位置 |
|---|---|---|
| 1、2 | ✅ | `tests/test_research_stage.py:83-84` |
| 6、7 | ✅ | `tests/test_research_stage.py:85-86` |
| **3、4、5、8、9、10、11** | 🔴 **空** | —— |

四條邊界反控(`:92-95`)覆蓋的是「不該擋的」那一側,不填上面任何一格。

### 🔴 第 11 格:`gate.py` 完全不讀 `node.level`

```
grep -n "node.level\|\.level" .claude/hooks/gate.py   ->  零命中
```

而 `:905` 的註解只講了 `module=None` 那一種相對 import:

```python
            # from research / from research.x import ...；相對 import(module=None)不算
```

**它沒說 `module` 非 None 的相對 import 算什麼**,而讀的人會把那句讀成「相對 import 都不算」。
實測:`from .research import x` 的 `module='research'`、`level=1` ⇒ **現行判定 True**。

> **`from .research import x` import 的是【同層一個叫 research 的模組】,不是頂層 `research/` 套件。**
> 現行行為把它擋下來。**本票不裁那是對是錯** —— 見第三節。

---

## 二、範圍:10 條

**口徑**:全部是**特徵化測試**(釘現行行為),寫完當下應為全綠。

### 語法軸空格 7 條

| # | 名稱(暫定) | 語料 | 斷言 |
|---|---|---|---|
| 1 | `test_an_aliased_import_is_still_a_research_import` | `import research as r\n` | `is True` |
| 2 | `test_an_aliased_dotted_import_is_still_a_research_import` | `import research.explore as e\n` | `is True` |
| 3 | `test_research_among_several_names_on_one_line_is_caught` | `import os, research\n` | `is True` |
| 4 | `test_a_star_import_is_still_a_research_import` | `from research import *\n` | `is True` |
| 5 | `test_a_relative_import_of_the_package_name_is_not_caught` | `from . import research\n` | `is False` |
| 6 | `test_a_two_level_relative_import_is_not_caught` | `from .. import research\n` | `is False` |
| 7 | `test_a_relative_import_whose_module_is_research_is_caught` | `from .research import x\n` | `is True` |

**第 5、6 條釘的是 `:905` 註解逐字宣告的行為**(「相對 import(module=None)不算」)——
今天有註解、沒有斷言。

**第 7 條的測試裡要逐字寫明**(裁決要求):

```
現行行為,未裁是否正確。`from .research import x` 的 module='research'、level=1,
而 gate.py 不讀 level(全庫 grep "node.level" 零命中)。
這一條釘的是「今天會擋」,不是「應該擋」—— 要不要改由候選一決定。
```

### `check()` 版 3 條

**為什麼要有這一組**:現有 8 個案例裡有 8 個斷言的是 **`gate.imports_research()` 這個述詞**,
走 `check()` 並斷言 `"R8" in msg` 的**只有一條**(`:106`)。
**述詞對 ≠ 規則會擋** —— 中間隔著 `is_source_path`、R2 的站別、`.py` 副檔名、`_under_research`
四個前置。

`check()` 走到 R8 的前置(逐條實查,附行號):

| # | 前置 | 出處 | 不滿足會怎樣 |
|---|---|---|---|
| 1 | 不是「規格書含程式碼」 | R1,`:1847` 起 | R1 先擋(`.py` 天然滿足) |
| 2 | `is_source_path(r)` 為真 | `:1863` `if not is_source_path(r): return None` | **直接放行,R8 永遠走不到** |
| 3 | stage 在 `writable` | `:1936` | R2 擋 |
| 4 | stage 若有 `src_write_scope`,路徑要在範圍內 | `:1913-1919` | `[R2/範圍]` 擋 ⇒ **不能用 `research` 站配生產路徑** |
| 5 | `r.endswith(".py")` | `:1948` | R3/R8 整段不進 |
| 6 | `not _under_research(r)` | `:1956` | R8 分支跳過(反方向放行) |
| 7 | `parses_as_python(body)` | `:1976` | 走 `[R8/fail-closed]`,不是 `[R8]` |

**最小可通過模板**:

```python
    def test_<name>(self, monkeypatch):
        monkeypatch.setattr(gate, "load_stage", lambda: ("implement", "01"))
        msg = gate.check("macro_audit/model.py", <content>)
        assert msg and "R8" in msg, <理由>
```

`implement` 滿足前置 3 且**沒有 `src_write_scope`**(只有 `research` 站有)⇒ 滿足 4。
`macro_audit/model.py` 滿足 2、5、6(`is_source_path` 是純字串判定,**目錄不必存在**)。

| # | 語料 | 對應述詞測試 |
|---|---|---|
| 8 | `import research\n` | `:83` |
| 9 | `import research.explore\n` | `:84` |
| 10 | `from research.explore import thing\n` | `:86` |

🔴 **第四條(`from research import explore`)刻意不寫** —— 既有
`test_a_production_file_importing_research_is_blocked_by_r8`(`:106`)用的正是它。
**裁決:不重複、不重構那一條。**

### 不含

- **`[R8/fail-closed]` 子類**(裁決剔出)。查證結果是它**本來就有涵蓋**,不是缺口:

| 出口 | `gate.py` | 測試 | 斷言 |
|---|---|---|---|
| 讀不到內容 | `:1971` | `test_edit_result.py:225` | `:232` `"R8" in msg` **+ `:233` `"fail-closed" in msg`** |
| 非合法 Python | `:1977` | `test_edit_result.py:208` | `:219` `"fail-closed" in msg` + `:220` `"不得 import research/" not in msg` + `:221` `"不是合法 Python" in msg` |

- **`gate.py` 的任何行為改動。** 本票只加測試 + 有界突變 + 還原。

---

## 三、🔴 三輪突變定稿 —— **而定稿本身揭露了一個要裁的問題**

> **紀律(票 102 `:180`)**:「一條從來沒有紅過的測試,與一條永遠不會紅的測試,
> 在報告上長得一樣。」**突變的目的是證明新測試會咬。**

### 驗收①:全庫 R8 語料逐條的 AST 型別(動手前讀完)

`tests/test_research_stage.py`:

| 行 | 語料 | AST | 判定 |
|---|---|---|---|
| :83 | `import research\n` | **ast.Import** | True |
| :84 | `import research.explore\n` | **ast.Import** | True |
| :85 | `from research import explore\n` | **ast.ImportFrom** mod=`research` lvl=0 | True |
| :86 | `from research.explore import thing\n` | **ast.ImportFrom** mod=`research.explore` lvl=0 | True |
| :92 | `import research_utils\n` | **ast.Import** | False |
| :93 | `from research_helpers import x\n` | **ast.ImportFrom** | False |
| :94 | `import researched\n` | **ast.Import** | False |
| :95 | `from my_research import x\n` | **ast.ImportFrom** | False |
| :102 | path `research/explore.py` | `_under_research` 為真 → R8 分支跳過 | check() → None |
| :109 | `from research import explore\n` | **ast.ImportFrom** | check() → R8 |
| :117 | `import research\nthis is not python(` | **解析失敗** | True(fail-closed) |

`tests/test_edit_result.py`(**含裁決點名補讀的 `:241` / `:310`**):

| 行 | 語料 | AST | 備註 |
|---|---|---|---|
| :167 / :175 | 片段無 import,結果 = `EXISTING` 改一行 | 無 research | 免疫 |
| :188 | `import research\n` | **ast.Import** | — |
| :199 | 移除 import 後 | — | 免疫 |
| :206 / :219 | 壞語法 | 走 `parses_as_python`(`:870`)**另一個函式** | 免疫 |
| :232 | `content=None` 讀不到 | — | 免疫 |
| **:241** | `from research import explore\n` | 🔴 **ast.ImportFrom** | **輪②會咬** |
| :247 | `import research_utils\n` | **ast.Import** | 輪①會咬 |
| :255 | path `research/explore.py` | `_under_research` → 跳過 | 免疫 |
| :301 | `EXISTING` 改一行 | fixture 是 `import sqlite3` + `from analyst_tracker import schema`(`:40-48`),**無 research** | 免疫 |
| **:310** | `import research\n\ndef f():\n    return 1\n` | 🔴 **ast.Import** | **輪②不咬**(Import 支);輪①不咬(`research` 完全相等) |

### 驗收②:輪③ 的 `:151` 定案 —— **綠**

`test_edit_result.py:151` 的 `got` 是 **`gate.content_after_edit(...)` 的回傳值**
(`:148-149`),它測的是**編輯結果解析**,**完全不碰 `imports_research`**。
⇒ 輪③(改 `imports_research` 的 except 分支)**不影響它**。

### 輪 ① — `:902` `split(".")[0] ==` → `startswith`(放寬)

**只影響 `ast.Import` 那一支** —— `ImportFrom` 的同一句在 `:906`,是另一行。

**預測紅 3 條(新 0 + 既有 3):**

| | 逐字名稱 | 為什麼 |
|---|---|---|
| 既有 | `test_research_stage.py::TestR8ProductionMustNotImportResearch::test_a_boundary_neighbour_is_not_a_research_import[import research_utils\n]` | `ast.Import`,`"research_utils".startswith("research")` → True,斷言要 False |
| 既有 | 同上 `[import researched\n]` | 同理 |
| 既有 | `test_edit_result.py::TestTheOldGuaranteesDoNotRegress::test_research_utils_is_still_not_a_research_import` | 走真入口,content `import research_utils` → `ast.Import` |

**預測綠(逐條寫):**
- `[from research_helpers import x\n]`、`[from my_research import x\n]` —— **走 `:906`,本輪不動**。
- 4 條正控(格 1/2/6/7)—— 放寬只讓 True 更 True。
- **新 10 條全部** —— 見下面的問題。
- `test_the_scope_is_boundary_matched_not_prefix`(`:50`)—— 測 `_under_research`(`:863`),不是 `imports_research`。
- R9 那兩條脆弱測試(`test_gate.py:2059`、`test_r5_mounts.py:609`)—— `staged_paths` 皆 patch 為 `[]`,R8 走不到。

### 輪 ② — 刪掉 `:904-907` 整個 `elif ast.ImportFrom` 分支(收窄)

**預測紅 7 條(新 3 + 既有 4):**

| | 逐字名稱 | 為什麼 |
|---|---|---|
| 新 | `test_a_star_import_is_still_a_research_import`(格 8) | ImportFrom 支沒了 → False |
| 新 | `test_a_relative_import_whose_module_is_research_is_caught`(格 11) | 同上 |
| 新 | `check()` 版 `from research.explore import thing`(第 10 條) | 同上 |
| 既有 | `test_production_importing_research_is_blocked[from research import explore\n]` | 同上 |
| 既有 | 同上 `[from research.explore import thing\n]` | 同上 |
| 既有 | `test_a_production_file_importing_research_is_blocked_by_r8`(`:106`) | 語料是 ImportFrom |
| 既有 | 🔴 `test_edit_result.py::TestTheOldGuaranteesDoNotRegress::test_a_whole_file_write_importing_research_is_still_blocked`(`:238`,語料在 `:240`) | **補讀 `:241` 才發現的第 4 條既有紅** |

**預測綠**:格 1/2/3/4/5(全走 `ast.Import`)、格 9/10(本來就 False)、
`check()` 版第 8/9 條(Import)、`:310`(Import)、四條邊界反控。

### 輪 ③ — `:897-898` `except: return True` → `return False`(收窄)

**預測紅 1 條(新 0 + 既有 1):**

| | 逐字名稱 | 為什麼 |
|---|---|---|
| 既有 | `test_research_stage.py::TestR8ProductionMustNotImportResearch::test_malformed_python_fails_closed`(`:114`) | 直接呼叫 `imports_research("import research\nthis is not python(")`,斷言 True |

**預測綠**:
- `test_edit_result.py:206` / `:219`(結果解析不了)—— 走 **`parses_as_python()`(`:870`)**,是另一個函式,輪③不動它。
- `test_edit_result.py:151` —— 見驗收②。
- **所有走 `check()` 的測試** —— `check()` 在 `:1976` **先**問 `parses_as_python`,
  壞語法**永遠到不了** `imports_research` ⇒ 輪③在 `check()` 這條路上完全不可觀測。

### 🔴🔴 定稿揭露的問題:**10 條新測試裡有 7 條,三輪都不會紅**

| 新測試 | 輪① | 輪② | 輪③ | 三輪內會不會紅 |
|---|---|---|---|---|
| 格 3 `import research as r` | 綠 | 綠 | 綠 | 🔴 **不會** |
| 格 4 `import research.explore as e` | 綠 | 綠 | 綠 | 🔴 **不會** |
| 格 5 `import os, research` | 綠 | 綠 | 綠 | 🔴 **不會** |
| 格 8 `from research import *` | 綠 | **紅** | 綠 | ✅ 會 |
| 格 9 `from . import research` | 綠 | 綠 | 綠 | 🔴 **不會** |
| 格 10 `from .. import research` | 綠 | 綠 | 綠 | 🔴 **不會** |
| 格 11 `from .research import x` | 綠 | **紅** | 綠 | ✅ 會 |
| `check()` 8 `import research` | 綠 | 綠 | 綠 | 🔴 **不會** |
| `check()` 9 `import research.explore` | 綠 | 綠 | 綠 | 🔴 **不會** |
| `check()` 10 `from research.explore import thing` | 綠 | **紅** | 綠 | ✅ 會 |

> ### **三輪突變只咬得到 3/10。另外 7 條在本票裡【從來沒有紅過】。**
>
> 而票 102 那句話正是為這種情況寫的:
> **「一條從來沒有紅過的測試,與一條永遠不會紅的測試,在報告上長得一樣。」**
>
> **成因不是突變選錯,是【突變的軸與測試的軸不同】**:
> 三輪動的是「頂層名比對」「ImportFrom 分支」「except 分支」,
> 而 7 條新測試釘的是 **alias、多名、相對層級** —— 那三件事在現行實作裡
> **根本沒有對應的判定分支**(`alias.asname` 沒被讀、`node.names` 只被迭代、`node.level` 零命中)。
> **沒有分支,就沒有可以弄壞的地方。**

**⇒ 這一格是本票要 Jeff 裁的事,寫在票面而不是留在對話裡**(`F-112`:
承諾沒有主詞也沒有機制,寫進來才跨得過 session)。候選突變見下,**本票未採用任何一個**。

| 候選突變 | 位置 | 會咬到 |
|---|---|---|
| ④ `for alias in node.names:` → `alias = node.names[0]`(只看第一個) | `:901` | 格 5 |
| ⑤ `:902` 前加 `alias.asname is None and` | `:902` | 格 3、格 4 |
| ⑥ `:906` 前加 `node.level == 0 and` | `:906` | 格 11(而這正是候選一的**修法方向**) |
| ⑦ ImportFrom 支改看 `node.names`(把 `from . import research` 也算) | `:904-907` | 格 9、格 10 |

**⚠ 未被任何候選涵蓋的:`check()` 版第 8、9 條**(`import research` / `import research.explore`)。
它們與述詞測試 `:83` / `:84` 的差別只在**走不走 `check()`** ——
要讓它們紅,得動 `check()` 的前置(`is_source_path` / R2 / `_under_research`),
而那**超出「有界突變」的邊界**(動的不再是 R8 自己)。
**⇒ 這兩條在本票的方法論下無法取得紅燈,只能誠實標註。**

---

## 四、驗收條件

1. 10 條全部加進 `tests/test_research_stage.py::TestR8ProductionMustNotImportResearch`
   (`check()` 版可另開一個 class),寫完當下**全綠**。
2. 三輪有界突變**逐輪**:改 → 跑全套 → 對預測(**紅的條數與名單逐字比**)→ 還原 →
   `git diff --stat .claude/hooks/gate.py` 查空。
3. 預測與實測不合**停下回報**,**不調整預測去配結果**。
4. 全套數字逐名對帳。
   **基線 = 2026-09-04 票 103 收刀的 1270 passed / 3 skipped / 3 xfailed**
   (出處:票 103 落地紀錄)。⚠ **動工時 HEAD 若不是 `d2312ea`,先重算再談差異**(`F-109`)。
5. `gate.py` 三個獨立口徑各驗一次回到原樣(`git diff` 對工作樹、對動工前 commit、
   `ledger_verify --diff` 帳本鏈)。
6. **第三節那張 3/10 的表要留在票面**,收票時不得因為全綠而拿掉。
7. 票面狀態行改完成,附三刀 sha 與 CI run id。

---

## 五、本票不含 / 候選登記(**不占號**,`F-118`)

**候選一:`from .research import x` 的設計題。**

| | |
|---|---|
| 事實 | `gate.py` 全庫 `grep "node.level"` **零命中**;`:905` 註解只講了 `module=None` 那一種相對 import |
| 現行行為 | `from .research import x`(module=`research`、level=1,**實測**)→ **擋** |
| 問題 | 它 import 的是**同層一個叫 research 的模組**,不是頂層 `research/` 套件 |
| 兩個方向 | **A** 加 `node.level == 0`(只認絕對 import)⇒ 放行;**B** 維持現狀(寧可誤擋)⇒ 但要把註解補完 |
| 為什麼不在本票裁 | 本票的驗收是 `gate.py` 三輪後回到原樣;在同一輪改它會讓那道驗收失去意義 |

**候選二:`:106` 的 `mkdir` 註解與規則順序不符。**

```python
        # 生產檔有對應測試(避免被 R3 先擋),但 import 了 research -> R8 擋
        (ROOT / "tests").mkdir(exist_ok=True)
```

**而 R8 的判定在 `:1956-1985`,R3 的「對應測試檔須存在」在 `:1994` 之後** ——
**R8 先說話,R3 擋不到它。** ⇒ 那個 `mkdir` 與它的理由至少有一個是過期的。
⚠ **本票不動它**(裁決:不重構 `:106`),但**開票時要先實測**
「拿掉 `mkdir` 之後那條測試還綠不綠」,不要照著我這段推導改。

**候選三～七**(承票 103,原樣保留):R4 兩前置、`CLAUDE.md` 硬連結時態、
`gate.py:1283` 過期行號、helper 漏關一條而 `patch ROOT` 讓它看起來已隔離、
`FRICTION_LOG` import 時算好。

---

## 六、為什麼是現在

**因為 R8 的軸是封閉的,而封閉集合是本 repo 明文寫過該用枚舉的那一類。**

`CLAUDE.md` 逐字:

> **常駐檢查項:動手守一個面之前,先問這一面的集合是開放還是封閉。**
> 封閉且可窮舉時,**枚舉勝過比對** —— 因為**比對的漏是未知的,枚舉的漏是不存在的**。

R1(票 102)的 8 個樣式是寫死在 `gate.py` 裡的封閉集合;
R9(票 103)的判定條件是一條正則的三個條件;
**R8 的封閉集合來自 Python 自己的文法** —— 比前兩者更硬,因為它不是本專案定的。

> **而本票最有價值的產出可能不是那 10 條測試,是第三節那張 3/10 的表** ——
> 它說的是:**枚舉補得完測試,補不完紅燈。**
> 一個沒有判定分支的行為,枚舉得出它的案例,卻造不出它的反例。
