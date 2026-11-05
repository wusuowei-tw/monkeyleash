# 票 168 —— test-runs.jsonl 缺測試檔版本綁定 —— 軸二永遠證不了

**狀態**：**立案（2026-11-03）。AC 為草案，待裁決者定案；實作未開始。**
**優先度**：非 LifeApp 接線 blocker（裁決者 2026-11-03）。
**立案**：2026-11-03。票號 168 於立案當下重查 `docs/tickets/framework-updates/` 取得（當時最大號 166，同輪票 A 取 167；寫檔前確認無 168 開頭的檔案）。
**性質**：證據 provenance 缺口。
**交叉引用**：LifeApp 規格目錄下的報告 `20261103T184416Z-lifeapp-gates-coverage-recon.md`（非本 repo）第 5 題；票 167（豁免帳本 malformed record，同輪立案）。

---

## 一｜背景

事實來源：上述 LifeApp 報告（查證時 HEAD `4bc2025ed7f150111c56b126b565693c9ee354e4`）。本票立案時**未**在本 repo 重新查證欄位。

- `.dev/test-runs.jsonl` 現行欄位含 `impl_file`／`impl_hash`。
- `impl_hash` 綁的是**實作**內容雜湊，**不綁測試檔**：沒有任何欄位綁測試檔版本。
- 沒有 commit SHA 欄位。
- 因此「某測試在現行版本跑過」依甲類標準無法成立（依上述 LifeApp 報告第 5 題的分類登記）。

---

## 二｜裁決

- **Q4**（裁決者 2026-11-03）：本問題另開獨立票（即本票），與票 167 同輪立案，不作為 LifeApp 接線 blocker。
- 其餘（AC 定案）：**待裁**。

---

## 三｜AC 草案（**草案，待裁決者定案**）

- **AC-B1**：寫入端每筆加三欄：
  - `test_file`：測試檔 repo 相對路徑；
  - `test_hash`：測試檔內容雜湊，CRLF→LF 後 sha256，與 `impl_hash` 同法；
  - `head_sha`：寫入當下的 HEAD。
- **AC-B2**：讀取端（`status.py`、`ledger_verify.py`，及票 167 偵察第 2 題 (4) 找到的讀取端）對缺新欄位的舊記錄照舊處理，不報錯。
  ⚠ 票 167 偵察第 2 題 (4) 查的是**豁免帳本**的讀取端；哪些讀取端實際讀 `test-runs.jsonl`，本票立案時**未查**，輪到本票時先列清單。
- **AC-B3**：有測試證明新記錄含三欄且值正確。

---

## 四｜優先序

非 LifeApp 接線 blocker（裁決者 2026-11-03）。

## 五｜不在本票範圍

- 豁免帳本（見票 167）。

---
## 補充佐證（2026-11-04，裁決者裁 B：記入本票，不另開票）
票 167 commit 45ac49d 時，R3 對 .claude/portable/ledger_verify.py 與 .claude/portable/status.py 提示「沒有屬於本票的紅燈紀錄」；
但票 167 的紅燈測試寫在 tests/test_exemption_ledger_malformed.py（首跑 21 failed，含 status 5 條、ledger_verify 3 條）。
R3 以同名配對（status.py ↔ tests/test_status.py）找紅燈，看不到跨檔測試。此案與本票「帳本說不清跑的是哪個測試檔」相關，列為佐證；兩者是否同一根因，未證明。
