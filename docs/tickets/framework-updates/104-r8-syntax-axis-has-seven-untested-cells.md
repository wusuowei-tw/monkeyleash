# 104 — R8 的語法軸有七個空格,而封閉集合本來就枚舉得完

**狀態**:**完成**(2026-09-04)—— 三刀已落,**七輪有界突變預測 17/17 全中**,`gate.py` 三個獨立口徑各驗一次回到原樣。本票產出 `F-158`。~~立案、未實作~~(`F-036`:舊狀態不刪)
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

## 三之二、輪 ④–⑦ 的預測(**2026-09-04 裁決全部採用,共七輪;本節寫在動手之前**)

裁決:候選 ④⑤⑥⑦ 全部採用。以下四輪的預測**與輪①②③同一套紀律** ——
寫在跑之前,跑完不修改,不合就停。

### 輪 ④ — `:901` `for alias in node.names:` → 只看第一個

```python
-        if isinstance(node, ast.Import):
-            for alias in node.names:
-                if alias.name.split(".")[0] == RESEARCH_ROOT:
-                    return True
+        if isinstance(node, ast.Import):
+            alias = node.names[0]
+            if alias.name.split(".")[0] == RESEARCH_ROOT:
+                return True
```

**預測紅 1 條(新 1 + 既有 0):**

| | 逐字名稱 | 為什麼 |
|---|---|---|
| 新 | `test_research_among_several_names_on_one_line_is_caught`(格 5) | 語料 `import os, research\n` 的 `node.names` = `[('os', None), ('research', None)]`(**實測**);只看第一個 → `os` → False,而斷言要 True |

**預測綠(逐條):**
- 格 1/2/3/4 —— 語料都只有**一個** name,`names[0]` 就是它,行為不變。
- 格 6/7/8/9/10/11 —— 走 `ast.ImportFrom`,本輪不動。
- 四條邊界反控 —— `import research_utils` / `import researched` 各只有一個 name,仍 False。
- `check()` 版三條 —— 語料各只有一個 name。
- `test_edit_result.py` 全部 —— `:241`/`:247`/`:310` 語料各只有一個 name。

### 輪 ⑤ — `:902` 前加 `alias.asname is None and`

```python
-                if alias.name.split(".")[0] == RESEARCH_ROOT:
+                if alias.asname is None and alias.name.split(".")[0] == RESEARCH_ROOT:
```

**預測紅 2 條(新 2 + 既有 0):**

| | 逐字名稱 | 為什麼 |
|---|---|---|
| 新 | `test_an_aliased_import_is_still_a_research_import`(格 3) | `import research as r` 的 `names` = `[('research', 'r')]`(**實測**),`asname='r'` → 被跳過 → False |
| 新 | `test_an_aliased_dotted_import_is_still_a_research_import`(格 4) | `import research.explore as e` → `[('research.explore', 'e')]` → 同理 |

**預測綠(逐條):**
- 格 1/2/5 —— `asname` 皆為 `None`(實測),條件不變。
- 格 6–11、四條邊界反控、`check()` 版三條 —— 見輪④同理。

### 輪 ⑥ — `:906` 前加 `node.level == 0 and`

```python
-            if node.module and node.module.split(".")[0] == RESEARCH_ROOT:
+            if node.level == 0 and node.module and node.module.split(".")[0] == RESEARCH_ROOT:
```

**預測紅 1 條(新 1 + 既有 0):**

| | 逐字名稱 | 為什麼 |
|---|---|---|
| 新 | `test_a_relative_import_whose_module_is_research_is_caught`(格 11) | `from .research import x` 的 `level=1`(**實測**) → 被排除 → False,而斷言要 True |

**預測綠(逐條):**
- 格 6/7/8 —— `level=0`(實測),條件不變。
- 格 9/10 —— `level` 是 1/2,但 `module` 是 `None`,**本來就 False**,方向一致。
- 既有 `[from research import explore\n]`、`[from research.explore import thing\n]`、
  `:106`、`:241` —— 全部 `level=0`,不變。
- 四條邊界反控 —— `from research_helpers import x` / `from my_research import x` 皆 `level=0` 且不匹配。

> ### **⚠ 輪⑥就是候選一的【修法方向 A】。**
> 它紅的那一條(格 11)**正是本票用來釘現行行為的那一條** ——
> 所以這一輪的紅**不代表 A 是錯的**,它代表「格 11 的測試真的在守現行行為」。
> **要不要改成 A 由候選一裁,本票不裁。**

### 輪 ⑦ — `:904-907` ImportFrom 支改為也看 `node.names`

```python
         elif isinstance(node, ast.ImportFrom):
             if node.module and node.module.split(".")[0] == RESEARCH_ROOT:
                 return True
+            for alias in node.names:
+                if alias.name.split(".")[0] == RESEARCH_ROOT:
+                    return True
```

**預測紅 2 條(新 2 + 既有 0):**

| | 逐字名稱 | 為什麼 |
|---|---|---|
| 新 | `test_a_relative_import_of_the_package_name_is_not_caught`(格 9) | `from . import research` 的 `names` = `[('research', None)]`(**實測**) → 新分支命中 → True,而斷言要 False |
| 新 | `test_a_two_level_relative_import_is_not_caught`(格 10) | `from .. import research` → 同理 |

**預測綠(逐條):**
- 格 6/7/11 —— `names` 分別是 `explore` / `thing` / `x`,**都不是** `research`;而它們本來就經第一個條件回 True,結果不變。
- 格 8 `from research import *` —— `names` = `[('*', None)]`,新分支不命中;第一個條件仍回 True。
- 四條邊界反控 —— `from research_helpers import x`、`from my_research import x` 的 `names` 是 `x`,不命中 ⇒ 仍 False。
- 格 1–5、`check()` 版三條 —— 走 `ast.Import`,本輪不動。

### 七輪合計的涵蓋

| 新測試 | 由哪一輪取得紅燈 |
|---|---|
| 格 3 `import research as r` | **輪⑤** |
| 格 4 `import research.explore as e` | **輪⑤** |
| 格 5 `import os, research` | **輪④** |
| 格 8 `from research import *` | **輪②** |
| 格 9 `from . import research` | **輪⑦** |
| 格 10 `from .. import research` | **輪⑦** |
| 格 11 `from .research import x` | **輪②、輪⑥**(兩輪) |
| `check()` 8 `import research` | 🔴 **無** |
| `check()` 9 `import research.explore` | 🔴 **無** |
| `check()` 10 `from research.explore import thing` | **輪②** |

**⇒ 10 條裡 8 條取得紅燈來源,2 條沒有。**
`check()` 版第 8、9 條**標為「本方法論下無紅燈來源」,不硬做**(裁決)——
理由見上一節:要讓它們紅得動 `check()` 的前置,那超出有界突變的邊界。

> **這兩條留白的意義**:它們仍然證明「這條路徑今天會擋」,
> 但**證明不了「這條斷言會咬」**。兩件事分開寫,而不是把它們算進涵蓋數。
> (與票 102 那 72 筆「無法判定」同一條:**留白比蓋章誠實**。)

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

**⇒ 那句話已落地為 `F-158`**(2026-09-04,動筆當下重查最大號 `F-157` 加一,
全庫 `grep -rn "F-158"` 零命中)。兩句判準逐字:
**枚舉補的是斷言,突變補的是紅燈**;
**沒有分支的行為,只能由「模擬未來的弄窄」提供紅燈。**

---

# 落地紀錄(2026-09-04)

## 三刀

| 刀 | sha | 內容 |
|---|---|---|
| 一(立案) | `7111009` | 票面(11 格實測表、10 條軸表、三輪定稿、3/10 那張表) |
| 二(正控 + 七輪突變) | `23b7c76` | `tests/test_research_stage.py` 10 條 + 票面輪④–⑦預測 |
| 三(帳本) | `11a5098` | `.dev/gate-exemptions.jsonl` 追加 14 筆 |
| 收票 | (本刀) | 狀態行 + 本節 + `F-158` |

## 全綠不是通過

10 條寫完當下**全部是綠的** —— 判定邏輯本來就在,這是**特徵化測試**。
紅燈由七輪有界突變提供。

## 七輪有界突變 —— **預測 17/17 全中**

| 輪 | 突變 | 預測紅 | 實測紅 | passed | 命中的是誰 |
|---|---|---|---|---|---|
| **①** | `:902` `split(".")[0] ==` → `startswith` | **3**(新 0 + 既有 3) | **3** | 1277 | `[import research_utils\n]`、`[import researched\n]`、`test_research_utils_is_still_not_a_research_import` |
| **②** | 刪 `:904-907` ImportFrom 支 | **7**(新 3 + 既有 4) | **7** | 1273 | 新:格8、格11、`check()`版第10條;既有:`[from research import explore\n]`、`[from research.explore import thing\n]`、`:106`、`test_a_whole_file_write_importing_research_is_still_blocked` |
| **③** | `:897-898` `except: return True` → `return False` | **1**(新 0 + 既有 1) | **1** | 1279 | `test_malformed_python_fails_closed` |
| **④** | `:901` `for alias in node.names` → 只看 `names[0]` | **1**(新 1 + 既有 0) | **1** | 1279 | 格5 `test_research_among_several_names_on_one_line_is_caught` |
| **⑤** | `:902` 前加 `alias.asname is None and` | **2**(新 2 + 既有 0) | **2** | 1278 | 格3、格4 兩條 alias |
| **⑥** | `:906` 前加 `node.level == 0 and` | **1**(新 1 + 既有 0) | **1** | 1279 | 格11 `test_a_relative_import_whose_module_is_research_is_caught` |
| **⑦** | ImportFrom 支加看 `node.names` | **2**(新 2 + 既有 0) | **2** | 1278 | 格9、格10 |

**七輪的紅燈條數與逐字名單全部相符,零筆落空、零筆意外。**

### 輪⑥ 單記:**它就是候選一的修法方向 A**

輪⑥ 加的 `node.level == 0` 正是候選一的方向 A(只認絕對 import),
而它紅的是**格 11 那條釘現行行為的測試**。

> **這一輪的紅【不代表 A 是錯的】** —— 它代表格 11 的測試真的在守現行行為。
> 改判成 A 的那一天,這條測試會紅,而**那正是它的工作**:
> 讓改判成為一個**看得見的動作**,不是一次沒有人注意到的行為漂移。

### 反控在七輪裡全綠

四條既有邊界反控(`import research_utils` / `from research_helpers import x` /
`import researched` / `from my_research import x`)——
**除了輪①刻意咬到的那兩條之外,七輪零紅**。
輪①咬到它們是**預測之內**(那一輪的方向就是放寬邊界),不是反控寫錯。

## 🔴 紅燈來源表(第三節那張,實測後兌現;**驗收條件第 6 條:不得因全綠拿掉**)

| 新測試 | 預定來源 | 實測 |
|---|---|---|
| 格3 `import research as r` | 輪⑤ | ✅ |
| 格4 `import research.explore as e` | 輪⑤ | ✅ |
| 格5 `import os, research` | 輪④ | ✅ |
| 格8 `from research import *` | 輪② | ✅ |
| 格9 `from . import research` | 輪⑦ | ✅ |
| 格10 `from .. import research` | 輪⑦ | ✅ |
| 格11 `from .research import x` | 輪②、輪⑥ | ✅ **兩輪都紅** |
| **`check()` 8 `import research`** | 🔴 **無** | **未取得** |
| **`check()` 9 `import research.explore`** | 🔴 **無** | **未取得** |
| `check()` 10 `from research.explore import thing` | 輪② | ✅ |

**8/10 取得紅燈來源。兩條無來源,逐條明列如上,標「本方法論下無紅燈來源」,不硬做**(裁決)。

**那兩條為什麼救不了**:它們與述詞測試 `:83` / `:84` 的差別只在**走不走 `check()`**,
要讓它們紅得動 `check()` 的前置(`is_source_path:1863` / R2 站別 `:1936` /
`_under_research:1956`)—— **那超出「有界突變」的邊界**,動的不再是 R8 自己。

> **它們仍然證明「這條路徑今天會擋」,但證明不了「這條斷言會咬」。**
> 兩件事分開寫,**不算進涵蓋數**。與票 102 那 72 筆「無法判定」同一條:
> **留白比蓋章誠實。**

## 全套數字(逐名對帳)

| 時點 | passed | skipped | xfailed | failed | passed+failed |
|---|---|---|---|---|---|
| **動工前基線**(票 103 收刀) | **1270** | 3 | 3 | 0 | — |
| **10 條加完(突變前)** | **1280** | 3 | 3 | 0 | **1280** |
| 突變 ① | 1277 | 3 | 3 | **3** | **1280** |
| 突變 ② | 1273 | 3 | 3 | **7** | **1280** |
| 突變 ③ | 1279 | 3 | 3 | **1** | **1280** |
| 突變 ④ | 1279 | 3 | 3 | **1** | **1280** |
| 突變 ⑤ | 1278 | 3 | 3 | **2** | **1280** |
| 突變 ⑥ | 1279 | 3 | 3 | **1** | **1280** |
| 突變 ⑦ | 1278 | 3 | 3 | **2** | **1280** |
| **收刀** | **1280** | 3 | 3 | 0 | **1280** |

**1270 + 10 = 1280**,而**九次量測**的 `passed + failed` 全部等於 1280。
**skipped / xfailed 全程 3 / 3,零新增 skip。**

> ⚠ **基線 1270 沒有重算,理由**(`F-109`):基線量在票 103 收刀(`d2312ea`),
> 而中間只隔本票刀一(`7111009`,一個 `.md`)。**沒有任何 `.py` 進出。**
> 日後對帳不是 1270 時,**先查那一筆 commit**,不要直接歸因到本票。

### 10 條逐名

| # | 名稱 | 格 | 紅燈來源 |
|---|---|---|---|
| 1 | `test_an_aliased_import_is_still_a_research_import` | 3 | 輪⑤ |
| 2 | `test_an_aliased_dotted_import_is_still_a_research_import` | 4 | 輪⑤ |
| 3 | `test_research_among_several_names_on_one_line_is_caught` | 5 | 輪④ |
| 4 | `test_a_star_import_is_still_a_research_import` | 8 | 輪② |
| 5 | `test_a_relative_import_of_the_package_name_is_not_caught` | 9 | 輪⑦ |
| 6 | `test_a_two_level_relative_import_is_not_caught` | 10 | 輪⑦ |
| 7 | `test_a_relative_import_whose_module_is_research_is_caught` | 11 | 輪②、⑥ |
| 8 | `test_a_plain_import_is_blocked_through_check` | check() | 🔴 無 |
| 9 | `test_a_dotted_import_is_blocked_through_check` | check() | 🔴 無 |
| 10 | `test_a_dotted_from_import_is_blocked_through_check` | check() | 輪② |

前 7 條在 `TestTheSyntaxAxisIsEnumeratedNotSampled`,後 3 條在
`TestR8BlocksThroughCheckNotJustThePredicate`,**皆在 `tests/test_research_stage.py`,零個新檔案**。

## `gate.py` 回到動工前 —— **三個獨立口徑**

| 口徑 | 做法 | 結果 |
|---|---|---|
| ① 對工作樹 | 每輪還原後 `git diff --stat .claude/hooks/gate.py` | **七次都無輸出** |
| ② 對動工前 commit | `git diff 7111009 --stat -- .claude/hooks/gate.py` | **無輸出** |
| ③ **帳本鏈**(獨立於 git) | `python .claude/portable/ledger_verify.py --diff` | **筆數 14 / 首尾相等:是 / 逐段接續:是** |

### 帳本比 `git diff` 多說的那一件事

七個突變雜湊**互不相同**:

```
c04ff9a094f5  dec5864053c7  98ad486e5893  0a428687c1dc
f108866aebf0  75e5f6d72ca0  9bd3d7c81bf0
```

⇒ **七輪真的各改到了不同的東西**,不是同一個編輯做了七次。
**`git diff --stat` 只能說「現在是原樣」,說不出中間去過哪裡。**

## 帳本(刀三)

| | |
|---|---|
| 追加 | **14 筆**,`git diff --numstat` = `14  0` —— **純追加零刪除** |
| 總數 | 181 → **195** |
| 欄位 | 全部 `ticket=104`、`tool=Edit`、`reason=gate-self-modification` |
| 首尾接續 | 第 181 筆(票 103 末筆)`result_hash` = `b6b06c082b53…becced`,第 182 筆 `content_hash` **逐字相同** ⇒ 接縫成立 |
| 歷史斷點 | 全檔仍是 **27 處**(與票 103 收票時**同一個數字**)⇒ **本輪零新增斷點**;`grep "第 1[89][0-9] 筆結束於"` 無命中 |

## CI(run `33851709370`,`success`,`pytest in 46s`)

四刀(`7111009` / `23b7c76` / `11a5098` / `325c375`)於 2026-09-04 推上
`d2312ea..325c375`,**未用 force**。CI 原文:

```
跑測試                             1270 passed, 1 deselected, 3 xfailed in 12.36s
淨室驗證(每條規則各擋一次 + 安裝後形態)  1188 passed, 3 xfailed in 10.10s
                                   全部 9 條規則各擋下一次,權威層偵測正常,框架測試在新 repo 全綠。
```

### CI 與本機的差額 —— **逐項算得出來,不是「環境不同」**

| 項 | 數 | 來源(可各自驗證,不是靠總和收尾) |
|---|---|---|
| 本機 passed | **1280** | 收刀那一跑 |
| − 個人 pattern 那一檔 | **−12** | `tests.yml:71` 的 `--ignore=tests/test_known_items_regression.py`;**12 是本輪重量的**:`python -m pytest tests/test_known_items_regression.py --collect-only -q` → `12 tests collected in 0.02s`。**未從票 103 抄** |
| ＋ Windows 才 skip 的 symlink 三條 | **+3** | 本機 `3 skipped`(`test_gate.py:451/459/473`);ubuntu 上它們會跑而且過,所以進了 CI 的 passed |
| − deselect 一條 | **−1** | `tests.yml:72` 的 `--deselect "tests/test_gate.py::TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce"`;CI 另欄報 `1 deselected` |
| **= CI passed** | **1270** | **與實測相符** |

`xfailed` 兩邊都是 **3**,一條不差。`deselected` 預測 1、實測 1。

> **`1280 − 12 + 3 − 1 = 1270` 是四個各自有指名來源的數字相加,不是先看到 1270 再湊出來的。**
> **這個 1270 寫在拿到 CI 實測之前**(見刀四推送前的回報)。
> 票 102 §CI 逐字警告過:「閉合是算術,不是歸因」。
>
> **`−12` 每一輪都重量,不抄上一張票**:票 102 對票 85 做過、票 103 對票 102 做過、
> 本票對票 103 做過。**一條「上次是 12」的記憶,與一次「這次量到 12」的測量,
> 在報告上長得一樣** —— 而只有後者會在那一檔增減測試時出聲。

### 淨室那 1188 —— **不與上表對帳,但它與票 103 的淨室可比**

照票 102 的處置:淨室跑的是**另一棵樹**(安裝後的新 repo),與「本機 passed」
**沒有可比的基準**,所以**不併進上表**。**明寫「沒對」,不是「對得上」。**

**但它與【票 103 的淨室】可比**(同一種樹、同一支指令):

| | 淨室 passed |
|---|---|
| 票 102 收刀(run `33751941469`) | 1169 |
| 票 103 收刀(run `33847385546`) | **1178** |
| 本票(run `33851709370`) | **1188** |

**`1178 + 10 = 1188`,而 10 正是本票新增的條數** ——
中間沒有任何其他 `.py` 進出(刀一是一個 `.md`)。
**這個 +10 也是預測寫在實測之前的**(見刀四推送前的回報第四節末)。

## ⚠ 這 10 條證明了什麼、沒證明什麼

**證明了**:R8 的語法軸 11 格**全部有斷言**(先前只有 4 格),
而其中 8 條由七輪突變證明**咬得到**。

**沒證明**:R8 的**設計**是對的。
格 11(`from .research import x` → 擋)是**現行行為**,不是理想行為 ——
測試裡逐字寫著「未裁是否正確」,要不要改是候選一。

**也沒證明**:那 11 格就是全部。
枚舉的依據是 `ast.Import` / `ast.ImportFrom` 兩個型別,
**而「R8 只需要管這兩個型別」本身是一個判斷** ——
`F-060` 逐字記過同一個洞:「R8 只看 AST 的 Import/ImportFrom:**字串型動態 import 全放行**」。
**本票沒有碰那一面。**

---

# 本票產出的 friction

**`F-158` 枚舉補得完測試,補不完紅燈 —— 沒有分支的行為造不出反例**
(`docs/agents/friction-log.md`)。

由來:本票第三節那張 3/10 的表。兩句判準逐字:

> **枚舉補的是斷言,突變補的是紅燈。**
> **沒有分支的行為,只能由「模擬未來的弄窄」提供紅燈。**

`F-158` 反過來引本票作為落地出處,並收錄「`check()` 版兩條連這個修法都救不了」那一格。
