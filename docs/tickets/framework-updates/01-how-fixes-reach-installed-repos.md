# 01 — 框架更新怎麼流到已安裝的 repo

## 問題

`agent-gates` 是框架,`TradingAgents-main` 是實例。修正應該**從框架流向實例**,
而**那條路徑不存在**。

`scripts/skills-update.sh` 管的是上游 Matt 的 skills(`npx skills update` +
重套本地 patch),**不管框架自己**。所以框架改了一行,已安裝的 repo 不會知道。

## 這不是假設,已經發生

`install.py` 產生的 `.gitignore` 缺前導斜線那個 bug:

1. 淨室測試在 agent-gates 抓到
2. 在 agent-gates 修好
3. **TradingAgents-main 完全不知道**,要人手動同步過去

那是第一個實例。**之後每一次框架改動都會遇到同一件事**,
而且每次都會有一段「兩邊不一致而沒有人知道」的時間。

## 難點(不要跳過)

- **不能整份覆蓋**:目標 repo 的 `.agents/legacy-no-redlight.txt`、`.dev/`、
  `CLAUDE.md` 的專案段都是它自己的(標記表已經分好 `generate` / `ask`)。
  更新只能碰 `copy` 那一桶。
- **本地 patch 怎麼辦**:目標 repo 可能對框架檔做過本地修改。
  上游 skills 的做法是「錨點插入 + 冪等重套」(`apply_patches.py`),
  框架自己需不需要同一套?還是宣告「框架檔不得本地修改」?
- **版本怎麼比**:目標 repo 怎麼知道自己裝的是哪一版?
  現在沒有任何版本標記 —— `install.py` 不寫版本,目標 repo 也不記來源 commit。
- **更新完要重驗**:安裝的定義是「verify-gates 通過」,更新也該一樣。
  而更新後的驗證必須跑到**第二代**(裝出來的東西還能再裝)。

## 一個要先決的問題

**更新是 push 還是 pull?**

- push(框架主動改實例):需要框架知道有哪些實例,而它不知道
- pull(實例主動拉框架):需要實例記得框架在哪、以及自己是哪一版

pull 比較可行,但那要求目標 repo 存一個「來源 + 版本」的指標,
而那個指標本身要能被信任(不可自我服務?還是只是方便性資訊?)。

## 怎樣算做完

- 一條可重複的更新路徑,跑完之後目標 repo 的 `copy` 檔案與框架一致
- 更新不動 `generate` / `ask` 桶的任何東西(要實際製造一次:
  目標 repo 的 legacy 清單與 CLAUDE.md 專案段在更新後原封不動)
- 更新後自動跑 verify-gates,不通過就不算更新完成
- **驗到第二代**:更新過的 repo 還能當來源再裝一次
