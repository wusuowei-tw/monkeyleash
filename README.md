# agent-gates

六站開發流程的**機器強制層**,加上 agent 檔案系統災難防護。

核心前提:**Prompt 是建議,檔案和 hook 才是法律。**

## clone 之後先跑一次

```
sh bootstrap.sh
```

啟用進版控的洩漏偵測 pre-commit(擋個人身分/機密進版控)。
git hooks 住在 `.git/hooks/` 而 `.git/` 不進版控 —— 所以 hook 放在版控的
`.githooks/`,`bootstrap.sh` 用 `core.hooksPath` 指過來。這一行 config 是
每個 clone 要跑一次的(零接觸不可能,git 刻意如此,見 `docs/adr/0007`)。

## 裝進一個專案

```
python .claude/portable/install.py <目標 repo 路徑>
```

安裝**一律建立 commit**(go-live sha 要指向真的存在的 commit),
並在最後**強制驗證**。**裝好的定義是驗證通過,不是檔案複製完。**

驗證:

```
python .claude/portable/verify_gates.py <暫存目錄>   # 全規則,含淨室安裝
python .claude/portable/g1_verify.py                 # G1 保護清單
```

## 兩層強制

| 層 | 掛載 | 涵蓋 |
|---|---|---|
| 前哨 | `.claude/settings.json` 的 PreToolUse | 隨 repo 走,只涵蓋 AI 路徑 |
| 權威 | `.git/hooks/pre-commit` | 綁得住所有人 —— **但不進版控**,見 `docs/adr/0007` |

## 規則

| | 判定 |
|---|---|
| R1 | 規格書含程式碼 → 擋 |
| R2 | 站別不允許時寫入原始碼 → 擋(寫入與提交問的問題不同,`docs/adr/0005`) |
| R3 | 寫 `x.py` 但沒有 `tests/test_x.py`、或沒有紅燈紀錄 → 擋 |
| R4 | skill 鏡像與正典不一致 → 擋 |
| R5 | 正典 code-review 缺第三軸掛載點 → 擋 |
| R6 | 紅燈豁免清單裡有不在 go-live 樹裡的項目 → 擋 |
| R7 | Bash 寫入 repo → 擋,請改用 Write/Edit(前哨限定,`docs/adr/0008`) |
| G1 | 碰到保護清單裡的路徑 → 擋(使用者層,獨立於六站) |

**目前沒有 per-repo 開關,裝了就全部無條件生效**(`docs/adr/0010`)。

## 最該先讀的東西

`docs/agents/friction-log.md` —— 46 則判準,是這套東西**最可攜的資產**,
比任何一支程式碼都通用。裡面每一條都是實際踩過的坑,而不是設計時想到的原則。

幾個反覆出現的:

- **fail-closed**:閘門壞掉時只能更嚴,不能更鬆。`except: return 0` 在任何閘門裡都是禁忌
- **黑名單,不是白名單**:列出不管的東西,其餘全管,新東西預設被守
- **豁免條件必須無法自我服務**:「檔案已存在」agent 造得出來,「在凍結清單裡」造不出來
- **驗邏輯證明「如果被呼叫它會擋」,證明不了「它會被呼叫」**:掛載完要用真實呼叫收尾
- **擋不住就明說擋不住**:假裝擋得住比擋不住危險,你會停止注意它
