# 37 — 回報改成兩段式:人先看懂,證據不打折

**狀態**:**done**(2026-08-25 回填)—— 落地 commit `52557eb`。
~~已寫入 `CLAUDE.md` 框架段(`## 回報格式`),待 commit。~~
(舊文保留照 F-036。**這一行從 2026-08-15 起就過期了** ——
`52557eb` 當天就 commit 了,而狀態行停在「待 commit」十天,
盤點時得靠 git log 才判得出來。詳見文末〈回填〉。)

**來源**:裁決者反覆「事後才知道發生什麼」。現行回報密度是為裁決助手
(web Claude,會逐字核對)寫的,而做判斷的人不寫程式、只靠讀證據決定下一步。

## 問題

**一種密度服務不了兩種讀者。**

為逐字核對者寫的密度,對做判斷的人是不可讀的 —— 而不可讀的後果不是「他慢一點懂」,
是**他在事情做完之後才懂**,那時代價已經付了。

反過來,把密度降下來服務前者,會讓後者失去核對依據 ——
而**證據被壓縮之後看起來跟沒壓縮一樣**,直到有人要回去查。

所以不是「選一種密度」,是**兩段**。

## 規格(已落地)

1. 兩段式,順序固定:【給裁決者】白話 → 【給裁決助手】原始證據
2. 白話段**硬上限 5 行**,四件事:做了什麼 / 卡在哪 / 要你決定什麼 / 不決定會怎樣。
   超過就刪到 5 行,**不得靠搬證據段內容上來重講**
3. 術語第一次出現時括號內用生活化比喻解釋一次,之後不重複
4. 證據段密度不減:raw stdout、雜湊、退出碼、行號、原始擋下訊息
5. 要裁決的事寫成「A 還是 B、差別是什麼」;三個以上選項照列並標建議與代價,
   **不得為湊二選一而藏選項**
6. 白話段不得出現證據段沒有的東西 —— 摘要,不是新宣稱
7. 不可切換的核心(被擋即停 / 附原始擋下訊息 / 不用宣稱句)完全不變

## 落點裁決:為什麼是 CLAUDE.md 框架段,不是 output style 檔

盤點過五個落點(CLAUDE.md 框架段、專案 `.claude/output-styles/`、SessionStart hook、
skill SKILL.md、使用者層 `~/.claude/`)。裁決選 CLAUDE.md 框架段。

**否決 output style 檔的兩個理由,都是靜默失敗:**

1. **取代而非附加。** output style 的 frontmatter 若漏寫
   `keep-coding-instructions: true`,它會**取代**內建的工程指令而不是加上去。
   漏寫不報錯,只會讓 agent 悄悄變笨 —— 壞了看起來正常。
2. **機制兩半分住兩張表。** `.claude/settings.json` 在 portable-manifest 標 `copy`
   (會散佈),而 `.claude/output-styles/` 不在該表的任何前綴內
   → `in_scope()` 為 False → sync 不帶;且 `uncovered_neighbours()` 只列
   dirname 落在 covered_dirs 裡的檔案,這個目錄連**提醒都不會出現**。
   結果:下游拿到一個**指向不存在樣式**的設定。

**否決 SessionStart hook**:官方 plugin README 自述其效果「roughly equivalent to
CLAUDE.md」,對本專案無淨收益,卻多一層掛不上時會靜默無指示的機制。

**否決 skill SKILL.md**:只在該 skill 被叫起時生效,涵蓋不到一般對話回報。不符規格。

**否決使用者層**:生效範圍最廣但繞過版控與流程 —— 改了沒有 commit、沒有 review,
其他 repo 的回報格式會在沒人知道的情況下改變。另外 `~/.claude/output-styles/`
未在 `user-layer-manifest.txt` 分類,`plan_export()` 會 `Refused` 整次使用者層匯出。

**散佈到下游是目的,不是代價。** CLAUDE.md 標 `generate`,只有框架界線之間那段跟著走 ——
所以規格寫成 repo 無關的通則,不提任何專案特有的事物。

## 流程

`.md` 在 `gate.py` 的 `NON_SOURCE_EXT` 裡 → R2 不擋、R3 不擋、redlight 不要求紅燈。
R1 只管 `docs/specs/**`。`CLAUDE.md` 已在 portable-manifest(標 `generate`),
`test_upstream_manifest` 不會紅。

驗證:`pytest tests/test_claude_md.py tests/test_upstream_manifest.py`

**內文不得出現框架界線標記字串本身**(`claude_md.py:22-24`:出現的話產生的檔案
會有兩組界線,下一次抽取會因「取哪一組取決於實作」而拒絕)。已避開,round-trip 測試覆蓋。

## 怎樣算做完

- [x] `CLAUDE.md` 框架界線之間新增 `## 回報格式`
- [x] 內文無框架界線標記字串
- [ ] `pytest tests/test_claude_md.py tests/test_upstream_manifest.py` 綠
- [ ] commit(等裁決者把 `.dev/pipeline.json` 的 `ticket_id` 改成 37)

## 後續

票 38「白話段詳略做成可切換展示層」為排隊票,條件未成立前不動工。
