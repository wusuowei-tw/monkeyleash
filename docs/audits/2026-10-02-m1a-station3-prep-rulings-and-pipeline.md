# M1-a Station 3 前置 —— 裁決落票 145 + pipeline.json 唯讀查詢

**這份檔案的身分**:Station 3 前置輪的正式報告,**進版控**
(位置依據同上一輪:`docs/agents/handover.md:34`「**回報檔一律進版控**(`docs/audits/`)」)。
本檔路徑一律寫 repo 相對路徑。

| | |
|---|---|
| **撰寫時點** | 2026-10-02T13:00:58Z(寫入當下) |
| **baseline HEAD** | `e55ce061a57477282578f19edd3434564b428b34` |
| **baseline origin/master** | 同上(`rev-list` = `0 0`) |
| **本輪 commit** | 本報告所在的 commit;SHA 無法寫進自己 —— 見該 commit |

---

## 【給裁決者】

1. 票 145 已寫入你的五項裁決:新第 3、4 行(下方原文),舊票頭值依 F-036 保存;新增〈十一〉放 ODC-1/2/3 與 baseline 流程原文;三個 ODC 末尾各加「→ 已裁,見〈十一〉」。
2. pipeline.json 查完了:`feature` 維持 `framework-updates`、`ticket_id` 應為**字串** `"145"`、`updated` 由你改檔當下填 —— **只有 `current_stage` 要你裁**:站別定義裡**沒有** Red-light 這一站。
3. 卡住的地方:Station 3 對應哪個 `current_stage`,證據推不出唯一答案(見下方選項)。
4. 要你決定:**A `implement`** 還是 **B `tickets`**(差別見下表)。
5. 不決定的話:pipeline.json 仍是 `idle` / `ticket_id: null`,baseline 量出來的紀錄不會歸到票 145,Station 3 不能開始。

**票 145 新第 3、4 行原文:**

```
**狀態**:立案(時鐘已定 2026-10-02);未動工 —— Station 2 DONE、Station 3 NOT STARTED。
**時鐘**:2026-10-02 —— 自此時點起,任何依 status aggregate 判斷「沒有未解紅燈」的行為,都暴露於已證明的 partial-selection false-green failure mode。此日期為 Jeff 於 2026-10-02 的排程裁決,不是由證據唯一推出;痛點最早的證據為票 139(2026-09-13)。
```

**要你裁的:Station 3 期間的 `current_stage`**

| 選項 | 寫 `tests/` | 寫原始碼(`.claude/hooks/*.py` 等) | 代價 |
|---|---|---|---|
| **A `implement`**(建議) | 放行(`tests` 在 `NON_SOURCE_DIRS`,任何站都放行) | **放行**(寫入時;R3 仍要求先有對應測試與票 145 的紅燈紀錄) | Station 3 期間 R2 不再擋原始碼寫入 —— 「只寫紅燈」靠紀律,不靠 R2;但 Station 4 不必再改一次 pipeline |
| **B `tickets`** | 放行(同上) | **擋**(寫入時 R2;提交時屬前置站也擋) | R2 在 Station 3 期間仍守住原始碼;Station 4 開工前要再手動改一次 pipeline.json 為 `implement` |

建議 A 的理由:`CLAUDE.md`「`/implement` 內部走 `/tdd`」、站別定義 `implement` 的 `zh` 為「TDD 實作」—— 紅燈在現行流程裡屬於 implement 站。
**但這是推論,不是定義檔寫明的對應**;選 B 的理由(R2 多守一段時間)同樣成立。

**一律不變的事**:A / B 兩者下,`ticket_id` 都必須是 `"145"`,否則 baseline 與紅燈紀錄不會掛在票 145 底下。

### 最低必要內容

| # | 項目 | 值 |
|---|---|---|
| 1 | 票 145 新第 3、4 行 | 見上 |
| 2 | A-6 a–c | a **PASS**、b **PASS**、c **PASS**(證據段);最終 numstat / check 只印在視窗(不進本檔,避免記錄自身 diff) |
| 3 | commit / `0 1` / 樹乾淨 | 發生在本檔 commit 之後,只在視窗回報 |
| 4 | 建議 pipeline.json | 見證據段 B-7 |
| 5 | 該 stage 放行 / 阻擋 | 見上表與證據段 B-5 |
| 6 | test-runs 指紋前後相同 | 開始時已記錄(證據段);最終比對在 commit 後,只在視窗回報 |
| 7 | push / pytest / pipeline.json 修改 | **NO / NO / NO** |

---

## 【給裁決助手】證據

### 0. preflight 與 test-runs 起點

```
$ git fetch origin                                   → (無輸出)
$ git rev-list --left-right --count origin/master...HEAD
0	0
$ git rev-parse HEAD
e55ce061a57477282578f19edd3434564b428b34
$ sha256sum .dev/test-runs.jsonl
d6c0da4d173388dc7d58ba30023c67620309059cd2bd1bc854faa45dc766f4ae *.dev/test-runs.jsonl
$ wc -c -l .dev/test-runs.jsonl
  1997 540862 .dev/test-runs.jsonl
```

### A. 票 145 改動摘要

| 項 | 位置 | 改動 |
|---|---|---|
| A-1 | 第 3、4 行 | 逐字替換為裁決字面;第 5–7 行(立案、性質)不動 |
| A-2 | 性質欄之後、第一條 `---` 之前 | F-036 provenance block:各行以 `>` 開頭;保存舊狀態值與舊時鐘值;明寫 superseded historical values;加「『立案』取自 repo 慣例(票 124 狀態行)…」一行 |
| A-3 | 新增〈十一、Station 3 前置裁決(2026-10-02,Jeff)〉 | ODC-1(2B 修正版)、ODC-2(3A 收緊)、ODC-3(4A)、Baseline 流程 —— 逐字(含全形標點) |
| A-4 | 〈四〉三個 ODC 各自末尾 | 各加一行「→ 已裁,見〈十一〉」;ODC 原文不改 |
| A-5 | 〈十〉 | Station 3 仍 NOT STARTED;lifecycle 描述改為與第 3 行一致;註明舊 candidate 語意由票頭 F-036 區塊保存、本節不是第二份 current status;「待裁事項:時鐘」改為「已裁:時鐘 2026-10-02」 |

A-2「票 124 狀態行」的引用已核:

```
$ grep -n ^\*\*狀態\*\* docs/tickets/framework-updates/124-redlight-evidence-is-per-machine.md
3:**狀態**:立案。**本票今日只立案,未動工。**
```

⚠ 過程紀錄:〈十一〉與 A-2 那一行第一次寫入時,全形標點(`（）`、`，`、`：`、`；`)被換成了半形;
發現後在 stage 之前改回裁決原文的全形字元。第 3、4 行的裁決字面原本就是半形,照抄。

### A-6 第一階段檢查

**a.**

```
$ grep -n ^\*\*狀態\*\* docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
3:**狀態**:立案(時鐘已定 2026-10-02);未動工 —— Station 2 DONE、Station 3 NOT STARTED。
$ grep -n ^\*\*時鐘\*\* docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
4:**時鐘**:2026-10-02 —— 自此時點起,任何依 status aggregate 判斷「沒有未解紅燈」的行為,都暴露於已證明的 partial-selection false-green failure mode。此日期為 Jeff 於 2026-10-02 的排程裁決,不是由證據唯一推出;痛點最早的證據為票 139(2026-09-13)。
```

⇒ current `**狀態**` 恰好 1 行(第 3 行);current `**時鐘**` 恰好 1 行(第 4 行)。**PASS**

**b.**

```
$ grep -c -F <磁碟代號>: docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
0
```

(**上列指令經遮罩**:實際搜尋字串是磁碟代號 C 加冒號;寫成原樣會讓本報告自己的磁碟代號計數不為 0。
這一行**不是逐字原文**,輸出 `0` 未改動。)

PRIVATE-CONTEXT CHECK:人工審查本輪新增文字 —— 全部來自裁決原文與本 repo 唯讀量測;
日期只有 2026-10-02(裁決 / 寫入)與 2026-09-13(票 139 既有證據)。**PASS**

**c.**

```
$ git add docs/tickets/framework-updates/145-m1a-run-level-evidence-correctness.md
$ git diff --cached --check
(無輸出)
```

**PASS**

### B. pipeline.json 唯讀查詢

#### B-1 `.dev/pipeline.json` 現有內容

```
$ cat -A .dev/pipeline.json
{$
  "current_stage": "idle",$
  "feature": "framework-updates",$
  "ticket_id": null,$
  "updated": "2026-09-24"$
}
```

| 欄位 | 型別 | 現值 |
|---|---|---|
| `current_stage` | string | `idle` |
| `feature` | string | `framework-updates` |
| `ticket_id` | null | `null` |
| `updated` | string(日期) | `2026-09-24` |

行尾為 LF(無 `^M`);最後一行 `}` 後沒有換行字元。

#### B-2 站別定義裡 Station 3(Red-light)對應的 stage

`.agents/pipeline-stages.yaml` 全部 8 個 `id`:`idle`(:14)、`grill`(:19)、`spec`(:24)、`tickets`(:29)、
`research`(:38)、`implement`(:47)、`review`(:52)、`arch`(:57)。

```
47	  - id: implement
48	    skill: implement
49	    zh: TDD 實作
50	    allows_src_write: true
```

⇒ **沒有名為 Red-light 的 stage。** 六站流程(Spec → Ticket → Red-light → Implementation → Review → Acceptance)
與定義檔的 `id` **不是一對一**。最接近的是 `implement`(`zh: TDD 實作`;`CLAUDE.md`「`/implement` 內部走 `/tdd`」)——
**這是推論,未證明唯一。**

#### B-3 實際讀取 `.dev/pipeline.json` 的 reader

以 `Grep pipeline\.json|PIPELINE|current_stage`(`.claude/**/*.py`)找出,逐一讀檔確認:

| 檔案:行 | 函式 | 讀什麼 | 誰用 |
|---|---|---|---|
| `.claude/hooks/gate.py:33` | `PIPELINE` 常數 | `os.path.join(ROOT, ".dev", "pipeline.json")` | 下兩列 |
| `.claude/hooks/gate.py:1522-1535` | **`load_stage()`** | `d.get("current_stage", "idle"), d.get("ticket_id")`;讀不到或解析失敗回 `UNREADABLE_STAGE, None`(**不回 idle**) | `check()` `:2757`(R2/R3 判定)、`log_exemptions()` `:2641`、`status._stage_of()` `status.py:255` |
| `.claude/hooks/gate.py:1538-1543` | **`load_feature()`** | `.get("feature")`;失敗回 `None` | `ticket_untested_modules(load_feature(), ticket)` `:2990`、`status._feature_of()` `status.py:265` |
| `.claude/hooks/redlight.py:41` / `:65-75` | **`current_ticket()`** | `.get("ticket_id")`;讀不到回 `None`(「不猜」) | 紅燈紀錄的 `ticket_id` 欄由此而來 |
| `.claude/portable/status.py:406-414` | `_repository()` 內 | `_field(json.load(f), "updated")` | 只顯示 `pipeline updated` 一行 |
| `.claude/portable/mcp_server.py:153-159` | `_feature_of(root)` | 讀不到回 None | MCP 唯讀工具 |

`load_stage()` 原文(`gate.py:1522-1535`):

```
def load_stage():
    """讀執行期狀態。current_stage 為權威欄位。

    讀不到時回 UNREADABLE_STAGE,**不回 "idle"**。
    回 idle 的話:寫入時 idle 不可寫 → 擋下(看起來沒問題),
    但**提交時 idle 是刻意放行的**(ADR 0005),於是 pipeline.json 壞掉或被刪,
    R2 在提交時就無條件通過。「不知道停在哪一站」不等於「停在 idle」。
    """
    try:
        with io.open(PIPELINE, encoding="utf-8") as f:
            d = json.load(f)
        return d.get("current_stage", "idle"), d.get("ticket_id")
    except Exception:
        return UNREADABLE_STAGE, None
```

`redlight.current_ticket()` 原文(`redlight.py:65-75`):

```
def current_ticket():
    """紅燈發生當下的票號。讀不到回 None。

    **讀不到就是 None,不猜。** 猜一個票號的話,猜中的那次會靜默解鎖
    一個根本沒有紅燈的修改 —— 而那正是這個欄位要防的事。
    """
    try:
        with io.open(PIPELINE, encoding="utf-8") as f:
            return json.load(f).get("ticket_id")
    except Exception:
        return None
```

寫入端(不是 reader,僅供對照格式):`install.py:190-192` / `:451-453`、`verify_gates.py:119-122` 以
`json.dumps(..., ensure_ascii=False, indent=2) + "\n"`、`newline="\n"` 寫出。

**stage 欄位如何解析**:`load_stage()` 回傳原字串;`check()` 拿它比對 `writable_stage_ids(stages)`
(定義檔裡 `allows_src_write: true` 的站)與 `src_write_scope`。`stage_allows_src_write()`(`gate.py:1487-1505`)
對**不在定義裡的站名一律 False**(fail-closed)。

**`ticket_id` 期望型別**:**字串**。依據:

- `redlight_missing()`(`gate.py:2090-2160`)以 `rec.get("ticket_id") != ticket` 直接比對,**沒有型別轉換**:

```
            if ticket is not None and rec.get("ticket_id") != ticket:
                saw_ticket_mismatch = True
                continue
```

- `status._latest_per_file()` 以 `rec.get("ticket_id") != ticket` 直接比對(`status.py:329`)。
- `ticket_lookup.find()` 以 `str(ticket) + "-"` 找票檔(`ticket_lookup.py:78`)—— 字串或整數都找得到,**但上兩處不轉型**。

⇒ pipeline 若寫整數 `145`,新紀錄會寫成整數,而**既有紀錄全是字串或 null**(B-4)—— 型別不一致會讓比對靜默不相等。

**`feature` 如何使用**:`gate.TICKET_DIRS = (".scratch/%s/issues", "docs/tickets/%s")`(`gate.py:1551`)以 `% feature` 展開 ——
`framework-updates` 展開成 `docs/tickets/framework-updates`,即票 145 所在目錄。

#### B-4 既有紀錄裡 `ticket_id` 的實際寫法

```
$ grep -c -E \"ticket_id\":\ \" .dev/test-runs.jsonl
1565
$ grep -c -E \"ticket_id\":\ [0-9] .dev/test-runs.jsonl
0
$ grep -c -E \"ticket_id\":\ null .dev/test-runs.jsonl
432
```

⇒ 1565 筆字串 + 432 筆 null = 1997 筆,**0 筆整數**。例:票 139 引用的那一筆為 `"ticket_id": "133"`。
`docs/agents/friction-log.md`(F-127)亦記:「`ticket_id = '83'`、`updated` 是 `2026-08-27`」。

#### B-5 該 stage 下各閘門放行 / 阻擋什麼(只列,不測)

| 寫入對象 | `idle`(現況) | `tickets` | `implement` |
|---|---|---|---|
| `tests/**`、`docs/**`、`.dev/**` 等 `NON_SOURCE_DIRS`(`gate.py:272-287`) | 放行(`is_source_path` 為 False,R2/R3 不管) | 放行 | 放行 |
| 原始碼(其餘路徑,含 `.claude/hooks/*.py`、`.scratch/<非 prototype>/*.py`) —— **寫入時** | **擋**(R2:不在 writable 集合) | **擋**(R2) | **放行**;`.py` 另受 R3:須有 `tests/test_<base>.py`,且有一筆**紅燈、屬於當前票、且(實作當時不存在或 impl_hash = HEAD)**的紀錄 |
| 原始碼 —— **提交時** | 放行 R2(ADR 0005:idle 刻意放行);R3 照驗 | **擋** R2(前置站 = 第一個可寫站之前、扣掉 idle;`tickets` 在 `research` 之前),除非內容與上游 provenance 逐位元組相同 | R2 放行;R3 照驗 |
| `research/**` | 擋 | 擋 | 放行 |

其他與 stage 無關、照常生效:R1、R4–R6、R7(前哨)、R8、R9、G1。

本輪第二次被擋即為一例:`.scratch/m1a-station2/probe_status.py` 在 `idle` 被 R2 擋(上一輪報告已收錄原文)——
`.scratch/` 不在 `NON_SOURCE_DIRS`,且路徑不符 `PROTOTYPE_RE = ^\.scratch/[^/]+/prototype/`(`gate.py:289`)。

#### B-6 `updated` 欄位寫法的規矩

**查無明文規矩。** 以 `Grep updated` 搜尋 `.agents/skills/**/SKILL.md`、`docs/agents/*.md`、`docs/adr/*.md`、
`CLAUDE.md`、`.claude/hooks/*.py`、`.claude/portable/*.py`,命中只有:

```
docs\agents\friction-log.md:4576:`json.load` 解析成功、`ticket_id = '83'`、`updated` 是 `2026-08-27`。
.claude\portable\verify_gates.py:122:                    "ticket_id": None, "updated": ""}, ensure_ascii=False, indent=2) + "\n")
.claude\portable\install.py:192:                    "ticket_id": None, "updated": ""}, ensure_ascii=False, indent=2) + "\n")
.claude\portable\install.py:453:                    "ticket_id": None, "updated": ""}, ensure_ascii=False, indent=2) + "\n")
.claude\portable\status.py:407:    updated = UNRECORDED
.claude\portable\status.py:411:                updated = _field(json.load(f), "updated")
.claude\portable\status.py:413:            updated = UNRECORDED
.claude\portable\status.py:414:    out.append(_line(u"pipeline updated", updated,
```

既有慣例只有值本身:`2026-09-24`(現值)、`2026-08-27`(F-127)—— `YYYY-MM-DD`。**沒有任何程式讀它做判定**(只顯示)。

另:`.agents/skills/` 底下**沒有任何 SKILL.md 提到 `pipeline.json`**(`grep -rln pipeline.json .agents/skills` 無輸出),
而 `.agents/pipeline-stages.yaml:5` 寫「狀態(.dev/pipeline.json)  執行期由 skill 寫入 current_stage」。只記錄,不處理。

#### B-7 建議 Jeff 手動貼進 `.dev/pipeline.json` 的完整內容

```
{
  "current_stage": "<A: implement | B: tickets —— 待 Jeff 裁>",
  "feature": "framework-updates",
  "ticket_id": "145",
  "updated": "<Jeff 改檔當下的日期,YYYY-MM-DD>"
}
```

| 欄位 | 值 | 來源 | 狀態 |
|---|---|---|---|
| `current_stage` | `implement` 或 `tickets` | B-2(定義檔無 Red-light 站)、B-5(兩者放行 / 阻擋差異) | **未證明唯一 —— 待裁** |
| `feature` | `framework-updates` | B-1 現值;B-3 `TICKET_DIRS % feature` 展開到票 145 所在目錄 | 已證明 |
| `ticket_id` | `"145"`(**字串**) | B-3 三處直接比對不轉型;B-4 既有 1565 筆字串、0 筆整數 | 已證明 |
| `updated` | 改檔當下日期 | B-6:無明文規矩,既有值為 `YYYY-MM-DD`,不參與判定 | 寫入時點 —— 不代填 |

格式:UTF-8、LF、兩格縮排(與 `install.py:190-192` 的寫法一致)。行尾若變 CRLF,`json.load` 仍可解析;
`cat -A` 可確認(F-127 的同一個檢查)。

**改完之後的確認**(Baseline 流程第 4 步「確認 machine reader 讀到票 145 與正確 stage」)——
`status.py` 的 `_repository()` 會印三行,來源欄分別標 `gate.load_stage()` / `gate.load_feature()`(`status.py:402-404`):
`stage`、`ticket_id`、`feature`。⚠ **本輪未執行該確認**(pipeline 未改、且本輪不得改)。

---

## 尚未證明 / 本輪未做

1. **Station 3 對應的 `current_stage`**:定義檔沒有 Red-light 站;`implement` 是推論,未證明唯一 —— 待裁。
2. **pipeline.json 改後 machine reader 讀到的值**:本輪未改 pipeline,未驗。
3. **B-5 放行 / 阻擋表**:由原始碼閱讀得出,**未實測**(本輪不得跑測試、不得寫原始碼)。
4. **上一輪的 residual 仍在**:`_ticket()` direct probe 未執行(R2 擋)—— 本輪未處理。
5. **Full baseline 尚未量測**:依裁決排在 Jeff 改 pipeline.json、確認 reader 之後。
6. **`pipeline-stages.yaml:5`「由 skill 寫入」與 skills 實況(0 個 SKILL.md 提到 pipeline.json)不一致**:只記錄,不處理、不開票。

---

## 六站狀態

| 站 | 狀態 |
|---|---|
| Station 1 — Spec | PASS / CLOSED |
| Station 2 — Ticket | DONE |
| Station 3 — Red-light | NOT STARTED |
| Station 4 — Implementation | NOT STARTED |
| Station 5 — Review | NOT STARTED |
| Station 6 — Acceptance | NOT STARTED |
