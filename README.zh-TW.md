# monkeyleash

**No monkeypatch, no fake greens.**

六站、測試先行開發流程的**機器強制層**,加上給 coding agent 用的檔案系統破壞性指令防護。
原名 `agent-gates`。

核心前提:**Prompt 是建議,檔案和 hook 才是法律。**

[![tests](https://github.com/wusuowei-tw/monkeyleash/actions/workflows/tests.yml/badge.svg)](https://github.com/wusuowei-tw/monkeyleash/actions/workflows/tests.yml)

[English](README.md)

## 這是什麼

**白話說**:AI 寫程式又快又猛,但會亂來。這套東西是一組裝在專案門口的關卡——
AI(或任何人)想跳步、想亂改、想把祕密塞進提交,門口直接擋下。
你不用會寫程式也能用:見下方「讓 AI 幫你裝」。

一組 git hook 與 Claude Code hook,不讓 coding agent(或人)跳步:
實作站以外不准寫原始碼、寫 `x.py` 就得有 `tests/test_x.py`、秘密不准進 commit、
規格書不准含程式碼。每條規則強制兩次 —— 先由 agent 側的 hook 早點擋,
再由 `pre-commit` 權威判定 —— 而且每條規則都是 **fail-closed**:
閘門自己壞掉時,它擋,不放行。

另附 **G1**:使用者層的防護,對一份 agent 改不動的保護清單
擋下破壞性的檔案系統指令(`rm -rf`、`Remove-Item -Recurse`……)。
這是黑名單式的 hook,不是沙箱 —— 真正的隔離要靠容器或作業系統權限。

六站流程建立在 Matt Pocock 的開源 skills 之上
(grill-with-docs → to-spec → to-tickets → implement → code-review →
improve-codebase-architecture);強制層 —— 閘門本身、帳本、
與 friction log —— 是本 repo 原創。

## 前提

- Python ≥ 3.10、git
- Claude Code(`PreToolUse` 那一層是為它寫的;`pre-commit` 那一層任何 git 客戶端都適用)
- **Windows 請在 Git Bash 裡跑 `bootstrap.sh` 那一行**(裝 git 時會一起裝)——
  PowerShell 沒有 `sh` 這個指令。其餘指令任何殼都跑得動。

## 快速開始

    git clone https://github.com/wusuowei-tw/monkeyleash
    cd monkeyleash
    sh bootstrap.sh          # 用 core.hooksPath 接上 .githooks/(每個 clone 一次)
    python -m pip install -e ".[dev]"   # 測試相依,缺它 pytest 連 collect 都過不了
    python -m pytest -q      # 跑框架自己的測試

**`pip install -e ".[dev]"` 那一行在乾淨機器上不是可選的。**
2026-09-04 筆電實測:少了它,`pytest` 會在 **collection 階段整套中斷**
(不是某一條紅,是整套沒跑)——
`ModuleNotFoundError: No module named 'mcp'`、`1 error during collection`。
**中斷的 collection 回報的是「零條測試」,而那看起來不像缺相依,看起來像什麼都沒發生。**

最後那行跑完會剩一條紅(`TestLegacyNoRedlightList`)—— 那是**已知的缺口,
不是你裝壞了**。雲端那邊把這一條跳過了,原因見票 54。

裝進另一個 repo:

    python .claude/portable/install.py <目標 repo 路徑>

安裝**一律建立 commit**,並在最後**強制驗證** ——
**裝好的定義是驗證通過,不是檔案複製完。** 事後驗證:

    python .claude/portable/verify_gates.py <暫存目錄>   # 全規則,含淨室安裝
    python .claude/portable/g1_verify.py                 # G1 保護清單

## 不會寫程式?讓 AI 幫你裝

在你要保護的專案裡,把下面這段貼給你的 coding agent(Claude Code 或同類工具):

```
請照 monkeyleash(https://github.com/wusuowei-tw/monkeyleash)README 的
「快速開始」一節,把它裝進這個專案。

這次任務的規則:
1. 每個指令執行前,先用白話解釋它做什麼、為什麼要做,再執行。
2. 裝完之後,跑 README 裡的驗證指令,把完整輸出原樣貼給我。
3. 任何步驟失敗或被擋下,把原始錯誤訊息一字不改回報給我。
   不得繞過、不得改路徑、不得改閘門的狀態檔 —— 停下來問我。
```

## 兩層強制

| 層 | 掛載 | 涵蓋 |
|---|---|---|
| 前哨(Outpost) | `.claude/settings.json` 的 `PreToolUse` | 隨 repo 走,只涵蓋 agent 路徑 |
| 權威(Authority) | `.git/hooks/pre-commit`(經 `.githooks/`) | 綁得住所有人 —— **但每個 clone 要接一次**(`docs/adr/0007`) |

加起來的實際涵蓋:

- 前哨層綁的是 **Claude Code 的工具掛鉤**。換一個 agent 來開這個 repo,這一層就不存在。
- 權威層是 git 的 `pre-commit`,**與哪個 agent 無關**(人工 commit 也綁得住);
  但它住在 `.git/hooks/`,而 clone 不會帶走那裡的東西 ——
  跑過一次 `bootstrap.sh` 之後它才存在。
- 所以:**不跑 `bootstrap.sh` 的人得到的強制是「無」,不用 Claude Code 的 agent
  得到的是「僅權威層」。這是設計的邊界,不是缺陷。**

## 規則

權威來源是 `.claude/hooks/gate.py` 的 `rule_codes()` ——
它從規則自己的擋下訊息掃出來,所以本表只保證「列出的每一條都對」,不宣稱「列完了」。

| | 判定 |
|---|---|
| R1 | `docs/specs/` 底下的規格書含程式碼 → 擋 |
| R2 | 站別不允許時寫入原始碼 → 擋(`docs/adr/0005`) |
| R3 | 寫 `x.py` 但沒有 `tests/test_x.py`、或沒有先寫一個會紅的測試 → 擋 |
| R4 | skill 鏡像與正典 `.agents/skills/` 不一致 → 擋 |
| R5 | 正典 `code-review` 缺第三軸掛載點 → 擋 |
| R6 | 紅燈豁免清單多出不在 go-live 樹裡的項目 → 擋 |
| R7 | Bash 寫入 repo → 擋,請改用 Write/Edit(前哨限定,`docs/adr/0008`) |
| R8 | 生產程式碼 import `research/` → 擋 |
| G1 | 碰到保護清單裡的路徑 → 擋(使用者層,獨立於六站) |

**目前沒有 per-repo 開關,裝了就全部無條件生效**(`docs/adr/0010`)。

## 已知限制

- 權威層住在 `.git/hooks/`,git 永遠不版控它。
  新 clone 在跑 `bootstrap.sh` 之前**完全靜默**,沒有東西會說權威層不在。
- 個人洩漏 pattern(`~/.claude/leak-patterns.local.txt`)依設計留在作者的
  機器上,CI 只用通用 pattern 掃。兩邊因此用著不同的 pattern 集合 ——
  不一致的時候,先查是哪一組在跑,再修錯的那一邊。
- 閘門訊息目前是繁體中文。
- `.claude/skills/` 的鏡像依平台是硬連結或 symlink;R4 不得假設任一形態。

## 接下來讀什麼

- `docs/agents/friction-log.md` —— 編號 `F-` 的每一則都是實際踩過的坑,
  不是設計時想到的原則。這是整套東西**最可攜的資產**。
- `docs/adr/` —— 決策與理由。
- `docs/tickets/` —— 工作紀錄,一票一檔。
- `docs/audits/` —— 定點審計(規則清冊、轉公開攻擊面)。
- `CLAUDE.md` —— agent 被要求遵守的常駐檢查項。

## 授權

MIT,見 `LICENSE`。`.agents/skills/` 底下的 skills 衍生自
[mattpocock/skills](https://github.com/mattpocock/skills)(MIT),
並經 `.claude/patches/` 修改;見 `THIRD_PARTY_NOTICES.md`。
