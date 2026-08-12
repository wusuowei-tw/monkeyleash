# agent-gates —— 六站流程閘門

<!-- FRAMEWORK:BEGIN -->

## 開發流程

**站別與順序的唯一定義:`.agents/pipeline-stages.yaml`(唯讀,不被任何流程寫入)。**
本檔不複製站名清單——要知道流程順序、每站對應哪個 skill、哪站可寫原始碼,一律讀該檔。

進入點都是顯式 slash command,流程細節在各 skill 內。
`/implement` 內部走 `/tdd`;`/improve-codebase-architecture` 為累積性檢查,非每票執行。

執行期狀態:`.dev/pipeline.json` 的 `current_stage`(+ `feature` / `ticket_id`)。
換新對話先讀它。合法值域由 `pipeline-stages.yaml` 的 `stages[].id` 決定。

## gate.py 強制契約

單一邏輯 `.claude/hooks/gate.py`,兩層呼叫:

- **pre-commit 為唯一權威判定** — `.git/hooks/pre-commit` → `gate.py --pre-commit`,擋 commit。
  **在已安裝的副本上**綁得住所有人(含非 Claude 的 agent 與人工 commit)。
  **未安裝的副本上這句不成立**:`.git/hooks/` 不進版控,clone 不會帶走它,
  而且完全靜默 —— 前哨照跑、測試照綠,沒有東西會說權威層不在。這是已知缺陷,不是留白。
- **agent hook 為前哨** — `.claude/settings.json` PreToolUse → `gate.py`,早點紅比 commit 才紅好。
  「繞過前哨仍會在 commit 被擋」**只在權威層已安裝時成立**;沒裝時前哨會直接說出這件事,
  並指出它自己涵蓋不到誰(clone 下來直接手動 commit 的人)。

四條規則:

| 規則 | 判定 |
|---|---|
| R1 | `docs/specs/**` 內容含 ``` / `def` / `import` / `function` → 擋 |
| R2 | `current_stage` 不是宣告 `allows_src_write` 的站時寫入原始碼目錄 → 擋 |
| R3 | 寫 `<name>.py` 但 `tests/test_<name>.py` 不存在 → 擋 |
| R4 | `.claude/skills/` 或 `skills/` 的 SKILL.md 與正典 `.agents/skills/` 不一致 → 擋 |
| R5 | 正典 `code-review` 缺第三軸掛載點(patch 未重套)→ 擋 |

被擋時不要繞過(改路徑、換工具、改 pipeline.json)。跳過流程由使用者自行修改 `.dev/pipeline.json` 的 `current_stage`。

## skills 更新

**唯一入口:`bash scripts/skills-update.sh`。不准直接跑 `npx skills update`** —— 它會靜默覆蓋正典裡的本地 patch。
wrapper 三步:更新 → 冪等重套 patch → gate.py 全規則驗證。R5 是這條規矩的機器保證。
正典為 `.agents/skills/`;`.claude/skills/` 與 `skills/` 是鏡像,已 gitignore。
**鏡像的實體形態由上游工具與檔案系統決定,不是本專案選的** —— 本機實測為檔案層硬連結
(目錄各自獨立、檔案是同一個實體檔),先前觀察過 symlink 佈局。R4 不得假設任一形態。
已知缺口:硬連結佈局下內容由構造保證相同,**R4 的內容比對不會觸發**,
它實際只守得住「檔案在不在」。見 `.scratch/portability/grill.md`。

閘門一律**黑名單、fail-closed**:列出不管的東西,其餘全管,新東西預設被守。
誤擋的處置是**把該目錄加進例外清單**(擋下訊息會直接給檔名與行號),
**不得退回白名單** —— 三次 fail-open 缺陷都源自白名單思維。見 `docs/adr/0003`。

**常駐檢查項:任何要進非原始碼清單的目錄,先問「它會不會裝著判定邏輯」。**
已經三次撞在同一個位置:`.claude` 整個在非原始碼清單、`find_implementation`
跳過點開頭目錄、`scripts/` 在非原始碼清單。共同根因是
**「基礎設施 = 特殊處理」這個習慣** —— 它在多數情境是對的(跳過 `.git` 省時間),
所以會被無意識套用;而閘門、hook、安裝器恰好全住在那些位置。
同理適用於任何「跳過某類路徑」的邏輯:先問它會不會跳過閘門自己。

## G1(檔案系統災難防護)

獨立於六站流程,不進 R 系列編號 —— R 系列是流程規則,**性質上**各自獨立、可分開裝;
災難防護則任何專案都該開。
**注意這是性質描述,不是功能宣告:目前沒有 per-repo 開關,R1–R7 全部無條件生效。**
掛在使用者層 `~/.claude/settings.json`,邏輯在 `~/.claude/hooks/g1_guard.py`,
保護清單是獨立純文字檔 `~/.claude/g1-protected.txt`。

**G1 把自己與保護清單都列在保護清單裡,所以 agent 改不動它。**
要改它:草稿放專案內、跑完 18 條驗收、附 diff,**覆蓋那一步只有人能做**。
完整流程見 `docs/adr/0009`。不得寫腳本代勞那一步 —— 那會讓保護消失。

## Code review 的分流判準

發現問題時要問的不是「要不要改」,而是「**不改會不會讓別的規則失效**」。
前者可以擱置,後者擱置就是把已偵測到的洞留在原地。見 `docs/adr/0003`。

## 重構歸屬

- **跨越本票宣告接縫(seam)的重構** → 不在紅綠燈迴圈內做,留給 `/code-review` 與 `/improve-codebase-architecture`
- **不跨接縫的重構**(改名、抽本地 helper、消除剛製造的重複)→ 留在紅綠燈迴圈內

## Agent skills

### Issue tracker

Local markdown under `.scratch/<feature>/`. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context — `CONTEXT.md` + `docs/adr/` at repo root. See `docs/agents/domain.md`.

### Friction log 發號

`docs/agents/friction-log.md` 在 portable-manifest 裡標 `copy`,**整份跟著裝進每個 repo**,
所以編號不是本地的事。`F-` 屬於框架(agent-gates 發號);
**每個安裝的 repo 用自己的三字母前綴,且前綴進號碼本身**(`TSA-001`,不是「F-001(影音)」)。
專案發現的框架層事實回 agent-gates 開票,落地才給 `F-` 號;專案那則不刪不改號,原地加一行指過去。
判準:**這一則搬到另一個專案還成立嗎?** 成立就是框架層。完整規則寫在 friction-log.md 開頭。

<!-- FRAMEWORK:END -->

## 這個專案自己的規範

(還沒有。寫在這一段裡的東西**不會**被帶進別的專案 ——
框架規範寫在上面那對 FRAMEWORK 界線之間,只有那一段會跟著走。)
