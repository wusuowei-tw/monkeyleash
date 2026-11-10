# 票 171：installer 把上游已核准的 synced contract 帶到下游候選

狀態：實作完成；本輪提交（2026-11-10）；未 push。

## 背景

**缺口甲**（L2 偵察，報告 `20261110T024035Z-l2-synced-policy-recon.md`）：上游名冊為 version 2、有 3 條
contract 項目；installer 的 `inventory_candidate()` 只產 `{path, sha256, note}`、version 固定 1 ⇒
新下游拿不到 contract。

**E2 結論**（E 查證，報告 `20261110T130654Z-l2e-manifest-probe.md`）：synced `manifest.json` 沒有逐檔
locator＋content hash，不能取代逐檔 SHA-256。

## 裁決（Jeff 2026-11-10，L2 收斂）

- 題 1＝B：installer 把上游「已提交、已核准」的 contract 項目正確帶到下游候選。
- 題 2＝A：真正的內容檔（SKILL.md 等）維持逐檔 SHA-256＋Jeff 人工核准；不放寬 R10、不新增 contract 名稱、不做 manifest 綁定。
- 名冊政策用語：版本由 Jeff 親自核准的 candidate hash 綁定，內容未逐項審閱（不得寫成「內容已審閱」）。

## 設計（本輪定案）

- **D1 來源**：只讀上游 **HEAD 已提交** 的 `.agents/extension-inventory.json`（不讀工作樹版本）；必須通過上游
  redlight 的 `_extension_inventory_ok`。讀不到／解析失敗／驗證不過 ⇒ SystemExit，下游零寫入。為了測試可注入，
  `inventory_candidate` 可加一個預設 None 的參數（`upstream_inventory`），None ⇒ 讀 HEAD；比照既有 `upstream_head` 參數的寫法。
- **D2 範圍**：只承接 entries 中帶 contract 的項目，且 `contract.name` 必須在上游 redlight 的 `EXT_CONTRACT_PATHS`、
  path 必須等於該名稱寫死的路徑；path／contract（name 與 pins）逐字照抄；note 一律用 installer 自己的固定字串
  （新增常數，內容標明票 171 承接上游契約），不抄上游 note。
- **D3 逐項處理**：上游每條 contract 的 path——
  (a) 該 path 在本次觀測的 synced_files 裡 ⇒ 先用上游 redlight 的 `synced_contract_check` 對實際檔案（經
  `_synced_contract_real_path` 解析）驗證：通過 ⇒ 以 contract 項目取代該 path 的 sha256 項目；不通過或實際路徑解析不了
  ⇒ SystemExit（只印類別/欄位代碼，不印檔案內容），下游零寫入。
  (b) 不在 synced_files ⇒ 不承接（避免下游 R10 判「缺少」），也不報錯。
  claude_root 為 None 時，實際路徑解析與 extension_report 採相同的使用者層根（不得另寫一套解析）。
- **D4 版本**：承接 ≥1 條 ⇒ inventory version＝上游 redlight 的 `EXT_INVENTORY_VERSION_CONTRACT`；承接 0 條 ⇒
  與現行行為逐位元相同（version 1、全 sha256、note 不變）。
- **D5**：最終 inventory 仍須通過 `_extension_inventory_ok`（沿用既有檢查）；candidate hash 照舊對整份 canonical bytes
  計算，所以 contract 的 name／pins 也被綁進 hash。
- **D6 輸出**：候選待核准時多印一行「承接上游 contract N 筆（名稱：…）」；只印名稱與筆數，不印 pins 值。

## AC

- **AC-1** 上游 HEAD 名冊有 contract、且對應 synced 檔在本機存在並通過契約 ⇒ 候選 inventory 為 version 2，該 path 為
  contract 項目（name／pins 與上游相同），其餘仍為 sha256。
- **AC-2** 上游沒有 contract（或全部不在本機）⇒ 候選與票 171 之前逐位元相同。
- **AC-3** 本機契約檔驗證失敗 ⇒ 停止、下游零寫入、也不寫出候選檔（檢查發生在候選落地之前）。
- **AC-4** 經核准安裝後，下游用自己的 redlight 判 synced ⇒ verified（R10 不因 contract 項目擋）。
- **AC-5** 來源只取 HEAD：工作樹名冊與 HEAD 不同時，以 HEAD 為準。

## 不在本票

- LifeApp 名冊 v1→v2 切換（另輪，需 Jeff 核准）。
- 票 170（`.pyc`／「已強制帶過去」訊息）。
- redlight 任何改動。
- 票 165。

## 關聯

- 票 169（新下游安裝先核准名冊；本票擴充其候選內容）。
- 票 170（安裝流程可用性問題；不在本票）。
- 票 151（skills 根 `.last-complete-round` 契約 `synced-skills-last-round-v1`）。
- 票 149（名冊 version 2 與 contract 項目、`synced_contract_check`）。
- 票 165（不在本票）。

## 設計對位（2026-11-10 讀到的行號，以 HEAD `b258fb1` 為底）

- `install.py`：`inventory_candidate` 在 988；sha256 entries 由內部 `entries()` 於 1005–1012 產生；inv 於 1027–1028 組裝
  （version 取 `rl.EXT_INVENTORY_VERSION`）；policy 驗證在 1029；候選待核准輸出在 `_approve_inventory` 1154–1160。
- `redlight.py`：`EXT_INVENTORY_VERSION_CONTRACT = 2`（1105）；`EXT_CONTRACT_PATHS`（1110–1112，三個名稱各綁一條
  含 `<bucket>` 的邏輯路徑）；`synced_contract_check(name, path, pins, lstat=None, fstat=None)`（1728，放行回 None、
  擋回 `{"category","field"}`）；`_synced_contract_real_path(claude_root, logical)`（2007，解析不了回 None，claude_root
  為 None 亦回 None）；`extension_report` 於 2168–2170 決定使用者層根，並以 `report["claude_root"]` 回傳實際採用值。
- synced_files 的 path 即含 `<bucket>` 的邏輯路徑：`_synced_root` 於 1926–1928 產生。
- 因此 D3 的「與 extension_report 相同的根」直接取 `report["claude_root"]`，不另寫解析。

## 驗證

引自報告 `20261110T135021Z-ticket171-contracts.md`（只引尾行，不重跑）：

- P0：`T171_BASELINE_SHA256 5db65a840674f317ef205bb66e73fc5d79e887bd0d1ae8ec4e828c28c8095a5d`；`1 failed, 116 deselected in 0.83s`（原因：`TypeError: inventory_candidate() got an unexpected keyword argument 'upstream_inventory'`）
- P1：`7 failed, 110 deselected in 1.98s`
- P2：`7 passed, 110 deselected in 15.94s`
- P2b：`T171_BASELINE_SHA256 5db65a840674f317ef205bb66e73fc5d79e887bd0d1ae8ec4e828c28c8095a5d`；`1 passed, 116 deselected in 0.94s`
- P3：`117 passed in 99.75s (0:01:39)`
- P4：`3531 passed, 39 skipped, 3 xfailed in 1207.98s (0:20:07)`

P0 與 P2b 的基準 SHA-256 一致；基準對 target.path／target.head 兩欄做固定字樣正規化，其餘逐位元照原樣（上一輪報告已說明）。

## 小裁決（2026-11-10）

- D6：承接 0 條時不印「承接上游 contract」那一行（A）。
- D1：上游 HEAD 名冊不合格一律 SystemExit（A）。

裁決助手依 D1／D4 字面裁定，Jeff 未推翻。

## 名冊

本票 commit 的前一筆為名冊 policy-only commit（2 筆，Jeff 2026-11-10 核准，內容未審閱）。
