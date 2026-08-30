# 72 — 開源準備:LICENSE、第三方聲明、README 改版

**狀態**:**修復批 C1–C4 已落地**(2026-08-23);README 另有兩次後續改動(8/25,見末段「開源前最後的 README 改動」)。
**未完**:⑤ GitHub UI 三保護 + Actions 兩開關,公開日由 Jeff 在網頁執行。
(本行原寫「立案,修復批待開工」,自 C1 落地起就過期,2026-08-26 回填 —— 八張 stale status 的第八張。)
**立案**:2026-08-23,開源前置偵察(唯讀輪)四裁之後
**來源**:本日唯讀偵察回報(全史個資掃描 + 五項清點)
**授權**:MIT(裁決)

---

## 偵察結論(摘要,數字帶單位;原始輸出已依裁決 3 刪除)

| 面 | 結果 |
|---|---|
| 全史 blob | 677 blob / 194 則 commit 訊息,個人 pattern 17 條 + 通用 10 條,**不豁免 SELF_PATHS**。命中 58 筆全是掃描器自身(`leak_scan.py` 55 + `leak-patterns.txt` 3),其餘 **0** |
| 裸字樣反控(不靠偵測器) | 家目錄真值 0、機器名 0;`friction-log.md` 30 個歷史版本殘留 `C:\\Users\\<user>\\OneDrive\<工作區>`,使用者名是通用英文字、工作區已是佔位符 |
| 身分欄位(枚舉) | 388 筆全是 `<舊帳號> <…@users.noreply.github.com>` |
| 下游真名 | `台股資訊收集` 現樹 15 檔 23 行 / 歷史 89 blob;`台股分析師影音` 現樹 5 檔 7 行 / 歷史 58 blob;commit 訊息 5 則 |

## 四裁(2026-08-23)

1. **真值洩漏 0 → 歷史帶。** 方法照准(不豁免 SELF_PATHS + 裸字樣雙向反控)。
2. **下游資料夾名視為可公開的專案名**,歷史照帶、現樹不動。
   理由:公開敘事本來就要說「我有台股量化與分析師影音系統」,名字只說了故事已經要說的事,
   不含位置 / 帳號 / 金鑰;另一邊的代價是推翻票 39 單刀承諾 + 全部 sha 再變一次,
   換到的隱私增益 ≈ 0。「量化 / 影音」暱稱與結構描述同理照帶。
3. scratchpad 的 677 blob dump 與兩個 .out 原文檔**已刪**(刪前 871 檔 23 MB;刪後只剩 4 支腳本)。
4. `.gitignore` 類別豁免從未被內容掃描 = 真缺口 → **候選票 73**,不在本票修。

---

## 修復批(寫入輪)

### ① `LICENSE`
MIT,版權行 `Copyright (c) 2026 <舊帳號>`。標準 MIT 全文,不改字。

### ② `THIRD_PARTY_NOTICES.md`
- `.agents/skills/` **39 檔 / 13 目錄**來自 `github.com/mattpocock/skills`(MIT,上游有 LICENSE 檔):
  code-review、codebase-design、diagnosing-bugs、domain-modeling、grill-with-docs、grilling、handoff、
  implement、improve-codebase-architecture、setup-matt-pocock-skills、tdd、to-spec、to-tickets
- 必須寫明:**經 `.claude/patches/apply_patches.py` 修改後散布**(第三軸掛載點等)
- 誠實一行:**無 `skills-lock.json`,上游版本 / commit 不可考** → **候選票 74**(補 lock)
- 內容:上游 copyright 行 + MIT 全文 + 檔案清單 + 上述兩句

### ③ README 改版
- `README.md` 英文為主 + `README.zh-TW.md`,開頭互連
- 一句話定位與前提:Claude Code hooks、Python ≥ 3.10、git
- quickstart(clone → bootstrap → 裝進專案 → 驗證)
- 規則表補 **R8**;**條數不寫死**(照票 51 D3:指向 `gate.py` 的 `rule_codes()`)
- 「46 則判準」→ 不寫數字,寫「編號至 `F-` 最後一則見檔內」(現為 106 則 / 最後 F-116,**此數只在本票,不進 README**)
- 已知限制節:權威層不進版控 / 個人 pattern 不上 CI / 無 per-repo 開關 / 閘門訊息目前中文
- 授權段、CI badge、`docs/` 導覽(adr / tickets / audits / agents 的分工)
- `.agents/portable-manifest.txt`:`README.md` 已標 `skip`;**新檔 `README.zh-TW.md`、`LICENSE`、`THIRD_PARTY_NOTICES.md` 要補標**,否則 `tests/test_upstream_manifest.py` 紅(每一檔都要有歸屬)

### ④ 更名影響清點(唯讀,本輪已做)
`git grep "agent-gates"`:**115 行 / 49 檔**。分層:

| 層 | 處 | 影響 |
|---|---|---|
| 識別字面(改了會壞) | `pyproject.toml:6` name、`pyproject.toml:36` `[tool.agent-gates]`、`.claude/portable/templates/pyproject.toml.template:6` | 套件名 + 設定段名;`[tool.*]` 段名若有讀取方要一起改 |
| 測試 reason / 註解前綴 | `tests/test_g1_guard.py:352` xfail reason、`tests/test_bootstrap.py:150`、`tests/test_source_hygiene.py:165`(H3 規則本身舉 `agent-gates framework-updates/04` 為例) | H3 守「reason 帶 feature 名」,前綴是慣例不是斷言;改名要連 H3 的例子一起改 |
| 框架文件(`copy` 桶,隨 install 出貨) | `CLAUDE.md` 3 行、`docs/agents/friction-log.md` 14 行、`.agents/portable-manifest.txt:53`、`.agents/legacy-no-redlight.txt:5`、`gate.py:1038` 註解、`bootstrap.sh:9` 註解 | 改了會觸發下游 sync 的差異,屬散文 |
| 票 / ADR / 審計散文 | 其餘約 80 行 | 歷史紀錄,**不改**(票面是當時的事實) |

結論:rename 的硬成本是 **3 處識別字面 + 3 處測試字串**;其餘是散文。GitHub 端 rename 會自動轉址舊 URL。**動作等名字定案另裁。**

### ⑤ GitHub 公開日(由 Jeff 在 UI 點,屆時給逐步)

**★ 2026-08-30:五項【逐項標明它防的是什麼】,不再用一句集體理由涵蓋。**
理由:2026-08-30 用一句集體理由讀這五項,推出了一個錯的結論
(「③ 整組都是外洩類」→ 差點據此升方案)。**分類是這次踩到的坑的正解。**

| # | 設定 | 類 | 失效需要什麼 | 現況(2026-08-30 實讀) | 排在 |
|---|---|---|---|---|---|
| 1 | Actions → General → Workflow permissions = Read repository contents | **外洩** | 不需要任何人動作 | ✅ `read`(GET 回值) | 已完成 |
| 2 | Actions → General → Fork PR workflows = Require approval for all outside collaborators | **外洩** | **不需要任何人動作** —— 外面的人自己就能發起 PR | 🔴 私有下此設定**不存在**(422) | **票 84 第 3 步** |
| 3 | Branches / Rulesets(`master`):Require PR | 寫入 | 要有**寫入權限的主體**動作 | 403,待公開 | 票 84 第 4 步 |
| 4 | Branches / Rulesets(`master`):Require status checks(`tests`) | 寫入 | 同上 | 403,待公開 | 票 84 第 4 步 |
| 5 | Branches / Rulesets(`master`):Block force-push & deletion | 寫入 | 同上 | 403,待公開 | 票 84 第 4 步 |

**第 2 項排在寫入類三項之前**,因為它是唯一不需要窗口內有人動作就會失效的。

**窗口期(翻公開 → 三保護設完)的殘餘曝險,2026-08-30 實測封頂**:
`0 secret / 0 variable / 0 environment`;唯一的 workflow `tests.yml` 用的是
`pull_request`**不是** `pull_request_target`;檔面 `permissions: contents: read`。

> **第 2 項設為最嚴檔,是為了讓兩個【公開前不可量】的行為問題變成不必回答,
> 而不是為了回答它們。**

⚠ **原「兩開關 2026-08-27 已設」為誤記** —— repo 自 2026-08-27 建立起即為 private,
第 2 項在寫下那一刻不可能為真。逐步與失敗處置見**票 84 順序區塊與 §4-12**,本處不複寫(`F-122`)。

本機 `.github/workflows/tests.yml` 已是 `contents: read` + action 釘 40 位 sha(由 `tests/test_ci_workflow.py` 守)。

---

## 切分提案(照「中間狀態不自相矛盾」切)

| commit | 內容 | 為什麼是一刀 |
|---|---|---|
| C1 | 本票 72 + 候選票 73、74 | 立案先於修復;純 docs |
| C2 | `LICENSE` + `THIRD_PARTY_NOTICES.md` + `pyproject.toml` 補 `license` 欄 + manifest 標兩個新檔 | 授權是一個整體:只有自家 MIT 而沒有第三方聲明,是一個「看起來合規」的中間狀態 |
| C3 | `README.md`(en)+ `README.zh-TW.md` + manifest 標新檔 | README 引用 LICENSE / NOTICES,所以在 C2 之後;兩語版互連,分開會有一邊連到不存在的檔 |

C2、C3 各自跑 `python .claude/hooks/gate.py --pre-commit` 與 `pytest tests/test_upstream_manifest.py`。

---

## README.md 英文初稿 v1(待 Jeff 審;審過才搬)

> 以下是草稿,中文版照此翻回。數字一律不寫死。

> ⚠ **這是 2026-08-23 的 v1 草稿,已被續裁與後續 commit 取代;
> 現行內容見 `README.md`,不要拿這份比對現況。**(標注不同步,不更新內容 —— F-036)

```
# agent-gates

Machine-enforced gates for a six-stage, test-first development pipeline —
plus a filesystem disaster guard for coding agents.

Core premise: **prompts are suggestions; files and hooks are law.**

[繁體中文](README.zh-TW.md)

## What this is

A set of git hooks and Claude Code hooks that refuse to let a coding agent
(or a human) skip steps: no source writes outside the implementation stage,
no `x.py` without `tests/test_x.py`, no secrets in commits, no spec files
that contain code. The rules are enforced twice — early by an agent-side
hook, and authoritatively by `pre-commit` — and every rule fails *closed*:
when the gate itself breaks, it blocks rather than passes.

It also ships **G1**, a user-level guard that blocks destructive filesystem
commands (`rm -rf`, `Remove-Item -Recurse`, …) against a protected list that
the agent cannot edit.

## Prerequisites

- Python ≥ 3.10, git
- Claude Code (the `PreToolUse` hook layer targets it; the `pre-commit`
  layer works with any git client)

## Quickstart

    git clone https://github.com/<舊帳號>/agent-gates
    cd agent-gates
    sh bootstrap.sh          # wires .githooks/ via core.hooksPath (once per clone)
    python -m pytest -q      # run the framework's own tests

> **★ 2026-08-27 加註(票 84;原文不改,照 F-036)**:上面那個 clone URL 裡的帳號
> 已遮蔽,而**那個 repo 本身也已經不存在** —— `agent-gates` 於 2026-08-27 刪除
> (票 84 硬條件二:force-push **不會**清掉舊物件,舊 commit 仍可用 sha 開啟,
> 實測 11 / 11 解得開、其中 8 筆 author 仍是舊名)。**現行位置見 README。**
> 這一行留著是因為它是當時的事實;加這一句是因為讀的人會照著去試。

Install into another repository:

    python .claude/portable/install.py <path-to-target-repo>

Install always creates a commit and ends with a full verification —
*installed* means *verified*, not *copied*. Verify later with:

    python .claude/portable/verify_gates.py <scratch-dir>   # every rule, clean-room
    python .claude/portable/g1_verify.py                    # G1 protected list

## Two enforcement layers

| Layer | Mount | Reach |
|---|---|---|
| Outpost | `.claude/settings.json` → `PreToolUse` | Travels with the repo; covers only the agent path |
| Authority | `.git/hooks/pre-commit` (via `.githooks/`) | Binds everyone — **but must be wired once per clone** (`docs/adr/0007`) |

## Rules

The authoritative list is `rule_codes()` in `.claude/hooks/gate.py` — it is
derived from the rules' own block messages, so this table claims only that
each row is correct, not that it is complete.

| | Blocks when |
|---|---|
| R1 | a spec under `docs/specs/` contains code |
| R2 | source is written outside a stage that allows it (`docs/adr/0005`) |
| R3 | `x.py` is written without `tests/test_x.py`, or without a recorded red test |
| R4 | a skill mirror drifts from the canonical `.agents/skills/` |
| R5 | the canonical `code-review` skill lost its third-axis mount point |
| R6 | the red-light exemption list gains an entry not in the go-live tree |
| R7 | Bash writes into the repo — use Write/Edit instead (outpost only, `docs/adr/0008`) |
| R8 | production code imports from `research/` |
| G1 | a path on the protected list is touched (user level, independent of the pipeline) |

There is no per-repo switch: once installed, every rule is active (`docs/adr/0010`).

## Known limitations

- The authority layer lives in `.git/hooks/`, which git never versions.
  A fresh clone is **silent** about it until `bootstrap.sh` runs.
- Personal leak patterns (`~/.claude/leak-patterns.local.txt`) stay on the
  author's machine by design; CI scans with the generic patterns only.
- Gate messages are currently in Traditional Chinese.
- Skill mirrors under `.claude/skills/` are hard links or symlinks depending
  on the platform; R4 cannot assume either (`.scratch/portability/grill.md`).

## Where to read next

- `docs/agents/friction-log.md` — the numbered `F-` entries: every one is a
  bug that actually happened, not a principle imagined at design time.
  This is the most portable asset in the repo.
- `docs/adr/` — decisions and their reasons.
- `docs/tickets/` — the work log, one file per ticket.
- `docs/audits/` — point-in-time audits (rule inventory, going-public surface).
- `CLAUDE.md` — the standing checks the agent is held to.

## License

MIT — see `LICENSE`. The skills under `.agents/skills/` are derived from
[mattpocock/skills](https://github.com/mattpocock/skills) (MIT) and modified
by `.claude/patches/`; see `THIRD_PARTY_NOTICES.md`.
```

**審稿要點給 Jeff**:(a) "Outpost / Authority" 這對譯名要不要;(b) Known limitations 第四條要不要公開提 `.scratch/`(它 gitignored,陌生人看不到 —— 建議刪掉括號);(c) R3 那行的「red test」措辭。

---

## 續裁(2026-08-23,README 審過 + 順序調整)

審稿三問:(a) Outpost / Authority **留**;(b) `.scratch/` 括號**刪**;(c) "red test" → **"a failing test written first"**。

**更名 `monkeyleash` 提前**:C4 排在 C3 之前,README 直接以新名出生。README 加:
標題 `# monkeyleash`、tagline `No monkeypatch, no fake greens.`、一行 `formerly agent-gates`;
clone URL 用 `github.com/<舊帳號>/monkeyleash`(GitHub 端 rename 公開日由 Jeff 在 UI 做,舊 URL 自動轉址)。

> **★ 2026-08-27 更正(票 84;原文不改,照 F-036)**:上面那句「**舊 URL 自動轉址**」
> **已於 2026-08-27 經實測推翻**。實際情形是:GitHub 改名後**個人檔案頁不轉址,直接 404**;
> **只有儲存庫路徑會轉址,而且只到舊名被他人認領為止**。
> 而本案更早一步失效 —— 該 repo 已被刪除,連儲存庫路徑的轉址也不存在。
> **當時為什麼會這樣寫**:那是把「GitHub 對 repo 改名的轉址」推廣成「對帳號改名也一樣」,
> 一個沒有查證就外推的說法。**遮蔽解決曝光,加註解決錯誤 —— 兩件事不合成一件。**
> 連帶:9/1 **不再有 rename 這一步**(新 repo 直接叫 `monkeyleash`)。
"What this is" 節尾加掛名一行:skills 建於 Matt Pocock 的開源 skills,閘門本體為本 repo 原創。中文版同義照翻。

**C4 執行判準**:識別字面 6 處全改;`[tool.agent-gates]` 段名的讀者查過 ——
`tests/test_dependency_ceiling.py:36` 只用 regex 抓 `pytest-ceiling-review` 鍵,**不讀段名**,所以無讀者碼要同刀。
copy 桶散文逐處「活改史留」;歷史票面 14 處不動(F-036)。

**執行序**:C1 → C2 → C4 → C3。zh-TW 照英文翻回,連同 C3 給 Jeff 過目。

## 帳號改名善後(2026-08-23,GitHub username → `wusuowei-tw`)

- 四刀落地:C1 `cc59833`、C2 `3822aab`、C4 `ddce215`、C3 `3a7918e`;C3 起作者為新代號。
- README 全部 URL 換 `github.com/wusuowei-tw/monkeyleash`;本機 remote 改指 `wusuowei-tw/agent-gates.git`
  (GitHub 端 repo 名公開日才 rename),**本 repo 層級**的 `user.name` / `user.email` 改新代號。
- `LICENSE:3` 版權行裁改 `wusuowei-tw`,單獨一刀:版權行是傳播最遠的一行,每個轉散布者永遠攜帶;
  兩個代號同為筆名效力等同,取與品牌一致者。
- **登記,不動**:全域 git 身分與量化 / 影音兩個私有 repo 仍是舊代號 —— 私有無曝光面,留著無妨。
- 歷史 commit 的舊代號照裁不動。

## 開源前最後的 README 改動(2026-08-25,兩刀,登記於此)

**這兩刀是 Jeff 直接派工,沒有開票 —— 直接派工是合法路徑,不是繞過。**
登記在這裡的理由:**票 72 是「開源準備」那張,而它是要開源出去的** ——
開源前最後一次改 README 的理由若只活在對話裡,讀票的人會以為 8/23 那批就是全部。

| commit | 時間 | 改了什麼 | 為什麼 |
|---|---|---|---|
| `d651638` | 08-25 07:30 | 掛名句括號從四站補成六站(`grill-with-docs → … → improve-codebase-architecture`);原創物補列「帳本、friction log」 | 原括號只列四站,讀者會誤以為另兩站(拷問共識、架構掃除)是本 repo 自創。查證 `pipeline-stages.yaml` 六站對應的 skill 全部來自上游 |
| `aab7c10` | 08-25 17:22 | ① 副標 `filesystem disaster guard` → `user-level guard against destructive filesystem commands`;中文「檔案系統災難防護」→「檔案系統破壞性指令防護」;CLAUDE.md 節標題與 ADR 0010/0012 同詞對齊 ② 「兩層強制」補適用範圍三點 ③ G1 定位句後加「不是沙箱,真正的隔離要靠容器或作業系統權限」 | 副標會被單獨轉載,「災難防護」易被讀成沙箱等級的隔離;實作是使用者層 hook 的黑名單比對,**詞要停在它做的事** |

**未動並登記**(措辭對齊的漏網,皆在該刀紅線外):`g1_guard.py` docstring、
`pyproject.toml` 與其範本的 `description`、`docs/audits/2026-08-16-rule-inventory.md:223`
節標題 —— 前兩者是程式碼/設定,第三者是定點審計(史留)。要不要一併對齊,另裁。

## CI 對帳(2026-08-25,登記不開票)

`d651638` 預測 962 / 實際 975,差 13:預測所用的本機基準(959)取自票 76 的
13 條新測試落地**之前**,**基準過時而非改動造成** —— 純文件改動的對帳應以
「上一次 CI 實測數」為基準(此處即與前一筆 CI 同數 975),不以本機某次
歷史數字為基準(F-109 同型:基準與被對的 commit 不同,先重算再談差異)。
