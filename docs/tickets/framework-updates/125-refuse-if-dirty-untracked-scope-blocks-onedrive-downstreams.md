# 票 125 —— `refuse_if_dirty` 的 untracked 口徑對 OneDrive 型下游是實質障礙

**狀態**:立案。**本票今日只立案,未動工。**
**發現於**:2026-09-09,筆電(hostname `14X`),上游 HEAD `63cd0fa`。
**受影響 repo**:工作區位於 OneDrive 底下的下游。今日實測的是影音下游
(`analyst-tracker`,HEAD `562e4ef`)。

## 現象

`sync.py` 的 `refuse_if_dirty()` 用 git 的**預設 untracked 口徑**問工作樹狀態,
而那個口徑在 OneDrive 底下的工作區上**跑不完**(120 秒逾時、零輸出)。
同一條指令加上 `--untracked-files=no` 立即回覆。

## 證據(今日原始輸出)

### 一、函式本體(`sync.py:289-301`)

```python
def refuse_if_dirty(target):
    """外層樹必須乾淨。**內嵌 repo 的內部狀態不算**(見 `gitlink_unsettled`)。"""
    out = subprocess.run(["git", "status", "--porcelain",
                          "--ignore-submodules=all"],
                         cwd=target, capture_output=True)
    if out.returncode != 0:
        raise Refused("問不到 %s 的工作樹狀態" % target)
    dirty = [l for l in out.stdout.decode("utf-8", "replace").splitlines()
             if l.strip()]
    dirty += gitlink_unsettled(target)
    if dirty:
        raise Refused(
            "目標**外層**工作樹不乾淨(%d 項),先清乾淨再更新 —— "
```

**沒有 `-uno` / `--untracked-files=no`** ⇒ 走 git 預設 `--untracked-files=normal`
⇒ 會掃未追蹤檔。

### 二、兩個呼叫端

```
448:    refuse_if_dirty(target)        ← regenerate_canon(),無條件
606:        refuse_if_dirty(target)    ← update(),在 `if apply:` 底下
```

| 路徑 | 會踩到嗎 |
|---|---|
| `sync.py <目標>`(不帶旗標) | **不會** —— `update()` 只在 `if apply:` 底下呼叫 |
| `sync.py <目標> --apply` | **會** |
| `sync.py <目標> --regenerate-canon` | **會**(448 行無條件) |

### 三、同口徑指令在該下游逾時

```
$ git -C "<影音>" status --porcelain
Command timed out after 2m 0s（exit 143,零輸出)
```

加上 `-uno` 之後立即回覆:

```
$ git -C "<影音>" status --porcelain --untracked-files=no
 D .agents/skills/code-review/SKILL.md
 M .dev/intercepts-2026-09.jsonl
 M .dev/pipeline.json
```

**單一變因、前後對照** ⇒ 時間全部花在未追蹤檔那一段。

### 四、排除「repo 太大」

```
$ git -C "<影音>" ls-files | wc -l
215

$ git -C "<影音>" count-objects -vH
count: 1702
size: 8.51 MiB
in-pack: 0
packs: 0
size-pack: 0 bytes
prune-packable: 0
garbage: 0
size-garbage: 0 bytes
```

215 個追蹤檔 / 8.51 MiB。單一追蹤檔讀取:

```
$ git -C "<影音>" ls-files | head -1
.agents/alias-table.txt

$ time cat "<影音>/.agents/alias-table.txt" > /dev/null
real	0m0.054s
user	0m0.000s
sys	0m0.015s
```

54ms ⇒ 那個檔確實在本機,不是待下載的雲端佔位。

## 為什麼要緊

今日對影音下游跑 dry-run(不帶旗標)時,拒絕訊息**建議的出口是 `--regenerate-canon`**:

```
$ python .claude/portable/sync.py "<影音>"
[更新/拒絕] 目標的正典段與來源不同(1 個條目)—— 那一段各 repo 應當完全相同:
  CLAUDE.md(FRAMEWORK 界線之間)
     出口:`python .claude/portable/sync.py <目標> --regenerate-canon`
     ...
```

而 `--regenerate-canon` 在 448 行**無條件**呼叫 `refuse_if_dirty` ⇒
那條出口在這台會**先撞慢掃描**,通過的話**再撞髒樹**(上面那 3 筆)。

**照拒絕訊息給的出口走,目前走不通。**
這不是訊息寫錯 —— **訊息不知道執行它的機器長什麼樣**。

`refuse_if_dirty` 擋的是對的東西(在未提交的變更上覆寫,出事分不出是誰改的);
**問題在它問問題的方式**,不在它的判準。

## 未證明

- **`--apply` / `--regenerate-canon` 在這台實跑會不會逾時。**
  **沒有實跑**(今日裁決禁止帶那兩個旗標)。上面是從「同一個口徑的指令逾時過」
  推得的 —— 依 `F-113`,那是一個合理的預測,不是量到的事實。
- **具體是哪個目錄拖慢的。** 該 repo 根目錄下有 `.backups` / `.cache` /
  `.pytest_cache` / `.scratch` / `skills` 等典型「大量小檔且常被 gitignore」的目錄,
  **但我沒有數過任何一個的檔案數或大小** —— 那正是會觸發慢路徑的動作。
  **「是 `.backups` 拖慢的」沒有證據。**
- **為什麼掃未追蹤檔在 OneDrive 上特別慢。** 只證明了「慢在那一段」,
  **沒有證明「為什麼那一段慢」**。
- **其他下游是否同樣受影響。** 量化下游今天被更前面的守衛擋下,沒測到這一格。

## 本票不預設解法

改成 `-uno` 是**放寬判準**(未追蹤檔就不算髒了),那會動到
`refuse_if_dirty` 存在的理由,不是一個純效能改動。
其他方向(例如只在需要時才問、或讓口徑可設定)各有代價。**本票不選。**
