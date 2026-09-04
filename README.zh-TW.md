# monkeyleash

**No monkeypatch, no fake greens.**

**給無法逐行檢查 AI 工作的人,用來治理 AI coding agent 的流程。** 原名 `agent-gates`。

核心前提:**Prompt 是建議,檔案和 hook 才是法律。**

*目前實證範圍:1 位使用者・1 個 agent(Claude Code)・1 個 OS(Windows)・
第一個外部專案待驗證。*

[![tests](https://github.com/wusuowei-tw/monkeyleash/actions/workflows/tests.yml/badge.svg)](https://github.com/wusuowei-tw/monkeyleash/actions/workflows/tests.yml)

[English](README.md)

---

你問 AI「檢查有跑嗎?」它說有。你怎麼知道?

monkeyleash 是我發現自己專案門口那六道關卡,在四十幾次改動裡一次都沒真的動過
之後做出來的東西。AI 沒有騙我 —— 根本沒有任何東西在查。這個 repo 就是現在負責
查的那套機器,加上它到目前為止每一次失手的紀錄。

> 這套東西是為一個人(我,一個不讀 Python 的量化交易員)、一個 agent
> (Claude Code)、一個作業系統(Windows)做的。下面每一個數字都是在那個環境量
> 出來的。沒在別處證明過的,README 直接寫「未證明」,不假裝。

## 一張圖

```
 你(裁決、放行)                        ← 唯一寫下意圖的人
        │  貼指令
        ▼
 執行者(Claude Code)                   ← 寫程式,不決定範圍
        │
   ┌────┴────────────────────┐
   ▼                         ▼
 前哨 hook                  權威 hook
 (每次工具呼叫都判,        (每次 commit 都判,
   可被繞過)                  結構性)
   └────┬────────────────────┘
        ▼
 磁碟上的證據:帳本、攔截紀錄、測試紀錄、回報檔
        ▼
 status 投影  →  唯讀 MCP  →  總指揮(Claude Desktop)
                                    │ 讀證據、裁決、寫下一段指令
                                    ▼
                                   你
```

兩件事是刻意的:

- **去程是授權,回程是證據。** 總指揮 AI 永遠碰不到 repo;執行者 AI 永遠不決定
  下一步做什麼。人站在兩者之間唯一那條線上。
- **評分者不是考生。** 每一句「通過了」都來自 agent 改不到的檔案,由 agent 在
  commit 時關不掉的機制產生。

## 裡面有什麼

| 東西 | 是什麼 |
|---|---|
| **九條規則(R1–R9)** | 機器強制的限制:agent 可以寫什麼、寫到哪、什麼時候寫。規格書裡不准放程式碼、不准寫到當前階段範圍外、生產檔要有測試、生產碼不准 `import research/`、鏡像要一致、friction 號不准重複……等。權威清單是 `.claude/hooks/gate.py` 的 `rule_codes()`,它從規則自己的擋下訊息掃出來。 |
| **G1** | **使用者層**的獨立防護,不走六站流程:擋下破壞性檔案系統指令(`rm -rf`、`Remove-Item -Recurse`…),對照一份 agent 改不動的保護清單。**這是一個 denylist hook,不是沙箱** —— 真正的隔離要靠容器或作業系統權限。 |
| **兩層強制** | **前哨**(`PreToolUse` hook,每一次 Bash / Edit / Write 執行前先判)與**權威**(`pre-commit`,`core.hooksPath`,agent 在正常 commit 路徑上繞不過的那層)。每條規則宣告自己住在哪一層。 |
| **六站流程** | `grill-with-docs → to-spec → to-tickets → implement → code-review → improve-codebase-architecture`。另有兩個站不在主線上:`idle`(待命)與 `research`(探索區,不准寫生產碼)。目前在哪一站是一個由人編輯的檔案;agent 讀得到、改不了。只有允許寫程式的站才能寫程式。 |
| **帳本** | 每一次豁免、每一次攔截、每一次測試,都追加到 `.dev/*.jsonl`,雜湊逐筆相接。用 `git checkout` 還原會在鏈上留下看得見的缺口,而不是一個乾淨的謊。 |
| **`status`** | 一個指令印出 repo 的真實狀態 —— HEAD、階段、票號、哪些 hook 證明得了在場、哪些只是「宣稱」—— 每一行都帶 `(source: …)` 來源欄。證明不了的行印「未證明」,不印綠勾。 |
| **唯讀 MCP server** | 給 Claude Desktop 的四支工具:`status_all`、`ticket(n)`、`friction(code)`、`latest_report`(最近一輪執行者回報)。零寫入路徑,由一條 AST 測試守著 —— 出現任何寫入呼叫就紅。 |
| **Friction log** | 148 則(編號至 `F-159`;缺號是設計上允許的)。每一則是系統或作者被騙過的一種方式,寫在現在負責擋它的那一行程式旁邊。每一則都是實際撞過的失敗模式,不是假想的威脅清單。**這是這個 repo 最重要的資產。** |
| **正對照** | 一條測試只有在「故意把守衛弄壞、它真的紅了」之後才算可信。九條規則做完這道的有四條;另外五條列為「尚未證明」,不列為通過。 |

## 它**不**主張什麼

- 它不會讓 agent 寫出正確的程式。它讓「檢查跑過了」變成一句可以驗證的話。
- 除了作者,還沒有任何人跑過它。第一個外部專案已排定;在那之前,「別人也能用」
  是未證明的。
- 規則 R4(鏡像一致)目前在 Windows 上做不了突變測試 —— symlink 相關測試在
  Windows 會跳過。這件事有記錄,沒有藏。
- 前哨那一層可以被 agent 的宿主關掉,只有權威層是結構性的。繞過前哨會被記錄;
  繞過 `pre-commit` 只能靠 `--no-verify`,而帳本會顯示出那個缺口。
- `status` 能告訴你某個 hook **設定了**,不能告訴你它在上一次 commit **跑了**。
  那一行印「未證明」是故意的。
- 個人洩漏 pattern(`~/.claude/leak-patterns.local.txt`)照設計留在作者機器上;
  CI 只用通用 pattern 掃。所以兩邊掃的 pattern 集不同 —— 兩邊結果對不上時,
  先弄清楚用的是哪一份,再修錯的那一側。
- 閘門訊息目前是繁體中文。

## 十分鐘上手

需要 Python `>= 3.10` 與 git。

```bash
git clone https://github.com/wusuowei-tw/monkeyleash.git
cd monkeyleash
pip install -e ".[dev]"
python -m pytest -q      # 乾淨 clone 上:2 failed
sh bootstrap.sh          # 用 core.hooksPath 接上 .githooks/(每個 clone 一次)
python -m pytest -q      # 現在:1 failed
```

**Windows 請在 Git Bash 裡跑 `bootstrap.sh` 那一行**(裝 git 時會一起裝)——
PowerShell 沒有 `sh` 這個指令。其餘指令任何殼都跑得動。

**`pip install -e ".[dev]"` 那一行在乾淨機器上不是可選的。**
2026-09-04 筆電實測:少了它,`pytest` 會在 **collection 階段整套中斷**
(不是某一條紅,是整套沒跑)——
`ModuleNotFoundError: No module named 'mcp'`、`1 error during collection`。
**中斷的 collection 回報的是「零條測試」,而那看起來不像缺相依,看起來像什麼都沒發生。**

**第一次跑的那兩條紅正是重點**,而它們**不是同一種紅**
(2026-09-04 在乾淨 clone 上實測):

| 測試 | `bootstrap.sh` 之後 | 為什麼 |
|---|---|---|
| `TestAuthorityLayerIsWired::test_this_repo_itself_is_wired` | **轉綠** | 它就是那條說「權威層沒裝」的測試。在裝好之前本來就該是紅的。 |
| `TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce` | **仍然紅** | 它要 `.dev/test-runs.jsonl` 裡的排水證據,而那個檔 gitignored,clone 永遠不會有。這是**已知的缺口,不是你裝壞了**;CI 把這一條跳過,原因見票 54。 |

然後看 repo 的狀態:

```bash
python .claude/portable/status.py
```

每一行都有來源。印「未證明」的行,是這支工具拒絕猜的東西。

裝進另一個 repo:

```bash
python .claude/portable/install.py <目標 repo 路徑>
```

安裝**一律建立 commit**,並在最後**強制驗證** ——
**裝好的定義是驗證通過,不是檔案複製完。** 事後驗證:

```bash
python .claude/portable/verify_gates.py <暫存目錄>   # 全規則,含淨室安裝
python .claude/portable/g1_verify.py                 # G1 保護清單
```

## 不會寫程式?讓 AI 幫你裝

在你想保護的專案裡,把下面這段貼給你的 coding agent(Claude Code 或類似的):

```
請照 monkeyleash(https://github.com/wusuowei-tw/monkeyleash)README 的
「Quickstart」章節,把它裝進這個專案。

這件事的規矩:
1. 每執行一個指令之前,先用白話說明它會做什麼、為什麼 —— 然後才執行。
2. 裝完之後,跑 README 裡的驗證指令,把完整輸出原樣貼回給我。
3. 任何一步失敗或被擋下,把原始錯誤訊息逐字回報。不要繞過、不要改路徑、
   不要動閘門的狀態檔 —— 停下來問我。
```

## 兩層強制

| 層 | 掛載 | 涵蓋 |
|---|---|---|
| 前哨 | `.claude/settings.json` → `PreToolUse` | 跟著 repo 走;只涵蓋 agent 那條路徑 |
| 權威 | `.git/hooks/pre-commit`(經 `.githooks/`) | 綁得住所有人 —— **但每個 clone 要接一次**(`docs/adr/0007`) |

合起來是這樣:

- 前哨掛在 **Claude Code 的工具層**。換一個 agent 來開這個 repo,這一層根本不在。
- 權威層是 git 的 `pre-commit` hook,所以它不在乎是哪個 agent(或人)在 commit
  —— 但它住在 `.git/hooks/`,而 clone 不會帶走那裡。**跑過一次
  `bootstrap.sh` 之後它才存在。**
- 所以:**不跑 `bootstrap.sh` 的人得到的強制是「無」,不用 Claude Code 的 agent
  得到的是「只有權威層」。** 那是設計的邊界,不是缺陷。

沒有 per-repo 開關:裝好之後每一條規則都無條件生效(`docs/adr/0010`)。

## 跟其他 agent 治理工具的差別

有好幾個專案在做 AI coding agent 的政策強制(hooks、沙箱、把政策編譯成 git
hooks 與 CI)。monkeyleash 在「強制」這件事上跟它們重疊,在多 agent 支援與可攜性
上落後於其中幾個。它不是要取代它們。它多出來的是強制之外的那套操作模型 ——
而且底下的強制機制換掉,這套模型仍然成立:

- 一個不需要讀程式碼的人,站在授權線上;
- 證據住在 repo 裡,由 agent 改不到的東西產生;
- 一個分得清「設定了」與「證明了」的 status;
- 以及一本把每一次被騙都當成正式產出的 friction log。

如果你的團隊讀得懂程式碼、同時跑五個 agent,其他工具大概更適合你。如果你是一個
人監督一個 agent,做的是你沒辦法逐行檢查的工作,這是我在用的那套。

## 它從哪裡來

六站工作流程與 `.agents/skills/` 底下的 skills 改編自
[mattpocock/skills](https://github.com/mattpocock/skills)(MIT)。
**取自上游的確切 commit 沒有被記錄** —— 這個 repo 沒有 `skills-lock.json`
(登記為票 74)。檔案清單、取回之後被修改的那三個檔、以及上游的授權條款全文,
都在 `THIRD_PARTY_NOTICES.md`。我把 skills 翻成繁體中文,並在 provenance 規則
要求的地方保留原檔逐位元組相同。

這個 repo 原創的是上游沒有的那一層:強制(閘門、兩層 hook、agent 不准改的階段
檔)、證據(帳本、攔截紀錄、測試紀錄、回報檔)、`status` 投影、唯讀 MCP server,
以及 friction log。

## 延伸閱讀

- 那四十幾次靜默跳過的故事:https://vocus.cc/article/6a950f34fd8978000170e285
- `docs/agents/friction-log.md` —— 編號的 `F-` 條目:每一則都是真的發生過的
  bug,不是設計時想像出來的原則。這是這個 repo 裡最可攜的資產。
- `docs/adr/` —— 架構決策,包括為什麼強制是 deny-by-default、為什麼 agent 不准
  改自己的階段。
- `docs/tickets/` —— 工作紀錄,一票一檔。
- `docs/audits/` —— 時點稽核(規則清冊、公開前的檢查面)。
- `docs/machine-init.md` —— 從零裝第二台機器,含文件與現實對不上的地方。
- `CLAUDE.md` —— agent 被要求遵守的常駐檢查項。

## 狀態

持續開發中,一個維護者。下面的數字截至 2026-09-04:

| | |
|---|---|
| 測試,本機 | **1313** 條通過(3 skipped、3 xfailed) |
| 測試,CI | **1303** 條通過(差額逐項列在票 106) |
| 規則 | **9** 條(R1–R9),另有使用者層的 G1 |
| Friction log | **148** 則,編號至 `F-159` |
| 票 | **105** 張,編號至 106 |

> 「幾則」與「編號到幾」在這裡是兩件事:friction 號與票號都可能有缺號
> (改號會留下空洞,而 R9 刻意不查連號)。上表兩個都給。

## 授權

MIT —— 見 `LICENSE`。`.agents/skills/` 底下的 skills 衍生自
[mattpocock/skills](https://github.com/mattpocock/skills)(MIT),
並由 `.claude/patches/` 修改;見 `THIRD_PARTY_NOTICES.md`。
