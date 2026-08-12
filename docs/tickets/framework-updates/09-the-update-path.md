# 09 — 框架更新流到已安裝 repo 的路徑(ticket 01 的實作)

## 觸發條件(2026-08-13,比預期更硬)

盤點發現量化 repo(台股資訊收集)的 `gate.py` **對不上任何框架版本**,
而且是落後:少了 `staged_paths` 的 `-z`(F-064)。後果是
**中文檔名的 staged 檔案靜默不掃** —— 而那個 repo 整個住在中文路徑底下。

手動同步已經證明會漏。兩個目標 repo 都是**版本拼盤**:
同一個 repo 裡 `install.py` 停在一個版本、`leak_scan.py` 另一個、
`test_gate_boundaries.py` 又另一個。ticket 01 說的
「每次都會有一段兩邊不一致而沒有人知道的時間」已經是現況,不是預測。

## 範圍(不擴大)

只做更新路徑本身:

- 只碰 `copy` 桶。`generate` / `ask` / `skip` 一律不動,**而且事後要驗它們沒被動到**
- 逐檔 hash 比對 → 只寫不同的 → 寫完重算 hash 確認等於來源
- `.agents/portable-manifest.txt` **一律跳過**(桶標未裁決,見票 10)
- `docs/agents/friction-log.md` 若目標含來源沒有的條目 → **拒絕覆蓋並列出來**
  (那代表 per-repo 條目還沒搬去 `friction-local.md`,見票 11)
- 預設 dry-run;實際寫入要顯式 `--apply`

不做:版本標記、pull 模式、本地 patch 的錨點重套。那些是 ticket 01 的其他難點,
各自另立。

## 為什麼判定邏輯不放 `scripts/`

`scripts/` 在非原始碼清單裡。這支工具**決定哪些檔案被覆蓋**,那是判定邏輯 ——
放進去等於讓它不受 R2/R3 管。CLAUDE.md 的常駐檢查項就是這條:
「任何要進非原始碼清單的目錄,先問它會不會裝著判定邏輯」,
而這個位置已經撞過三次。所以住 `.claude/portable/sync.py`。

## 怎樣算做完

- dry-run 列出會動到的檔案與 hash,不寫任何東西
- `--apply` 之後,`copy` 桶逐檔 hash 等於來源
- `generate` / `ask` / `skip` 桶的 hash 前後不變(實際比對,不是宣稱)
- 目標 repo 髒工作樹 → 拒絕(與 `install.py` 同規矩)
- friction-log 有未搬遷的本地條目 → 拒絕,並列出是哪幾則
