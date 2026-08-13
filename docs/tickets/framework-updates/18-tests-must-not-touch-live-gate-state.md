# 18 — 測試不得碰宿主的活體閘門狀態;安裝器的列舉縫

量化盤點揭出四件。**紅燈全部來自量化實測,不必製造。**

## 一、框架測試寫進宿主的真實證據檔

量化的 `shadow-log` 從 4 筆變 13 筆,**含合成的 fixture 條目**。

證據檔是閘門的判定依據:`shadow-log` 決定影子模式要不要晉升,
`test-runs.jsonl` 決定 R3 的紅燈半。往裡面寫測試造的假紀錄,
等於**讓測試去改變閘門之後的判斷**。

上游實測(2026-08-13)對照:

```
gate-exemptions.jsonl  跑完全套件逐位元組不變(票 08 已修)
test-runs.jsonl        +17 行 —— 那是紅燈紀錄機制的正常產出,不是污染
```

上游沒開影子,所以那條路徑從沒被走到 —— **缺陷在下游才現形**。

### 修法

不靠「每條測試記得 monkeypatch」:那是紀律,而紀律會漏。
`conftest.py` 加一條 autouse fixture,把**每一個**已載入的 gate 模組實例的
證據路徑(`SHADOW_LOG` / `SHADOW_STATE` / `EXEMPTION_LOG` / `PROVENANCE`)
指到 tmp。各測試檔用 `spec_from_file_location` 各載一份,所以要走訪
`sys.modules`,不能只改一個。

負控:跑完全套件,宿主 `.dev/*.jsonl` 除了紅燈紀錄的正常追加以外逐位元組不變。

## 二、測試假設影子模式是關的

兩條在影子開啟的 repo **永久紅**。而永久紅是萬能鑰匙(F-071):
它會讓 R3 的紅燈半對那個檔案永久滿足,同時訓練人忽略訊號(F-031)。

根因與第一件相同:**測試的行為取決於宿主 repo 的活體閘門狀態**。
第一件的隔離會讓影子在測試中恆為關 —— 那修掉了「永久紅」,
但也代表影子那條路徑**在測試裡從沒被走過**。

所以兩件都要:隔離讓結果可決定,另加**成對**的 shadow-aware 測試 ——
影子開:斷言 `rc == 0` 且 shadow-log 記了一筆 `would-block`;
影子關:斷言真的擋。

## 三、`install.py` 的列舉縫:補了 untracked,沒補 ignored

```python
t = git_paths(["ls-files"], SRC_ROOT)
u = git_paths(["ls-files", "--others", "--exclude-standard"], SRC_ROOT)
```

docstring **描述了同一個病**(「只取 `git ls-files` 的話,還沒 commit 的框架檔
會靜默漏帶:安裝照樣成功、閘門照樣擋、輸出全綠」)並修好了 untracked 那半,
但 `--exclude-standard` 仍然把 **ignored** 排除在外。**差一步。**

量化的 `.claude/` 被 gitignore → 框架檔完全不進列舉 → 裝出**沒有閘門的 repo**
→ `verify_gates` 崩潰。而安裝過程本身是成功的、安靜的。

### 修法

列舉再加一道 `--others --ignored --exclude-standard`,取其中
`manifest.in_scope()` 為真的那些(被 gitignore 蓋住的框架檔),
帶進來並**顯式列出**。

安全性:鏡像(`.claude/skills/`、`skills/`)不在任何框架前綴底下,
`in_scope` 為假,不會被撈進來;`__pycache__` 在 `.claude/hooks/` 底下但標 `skip`,
標記表擋住。

「被 gitignore 蓋住的框架檔」本身是個怪狀態,所以不只帶,還要**出聲**。

## 四、R7 的 `WRITE_CONSTRUCT` 對輸出字串裡的 `->` 誤報(先記不修)

`(?<![0-9])>>?(?!&)` 會命中中文技術文字裡的箭頭 `->`,
而那在說明「A -> B」的句子裡極常見。本 session 撞到兩次。
F-058 家族(資料內容誤觸 R7)。**先記錄,不修** ——
修它要動 R7 的樣式,而那是守衛設計變更,不為順手方便改。

## 怎樣算做完

- 跑完全套件,宿主 `.dev/shadow-log.jsonl` 與 `gate-exemptions.jsonl` 逐位元組不變
- 影子開的 repo 跑全套件不會有永久紅
- 影子開/關兩個方向各有測試,而且是同一組行為的兩面
- 來源 `.claude/` 被 gitignore 時,安裝**帶得到框架檔**且說出這件事
