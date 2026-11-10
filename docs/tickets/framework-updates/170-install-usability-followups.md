# 票 170 —— installer／bootstrap 安裝流程的可用性與表述修正（票 169 AC-3 驗收發現）

**狀態**：**立案（2026-11-09）。只立案；實作未開始。**
**優先度**：低；非 correctness blocker。若 S3 日後被裁為高風險治理問題，再拆獨立票。
**立案**：2026-11-09。票號 170 於立案當下重查 `docs/tickets/framework-updates/` 取得（當時最大號 169；寫檔前 `Test-Path` 確認無此檔、Glob 確認無 170 開頭的檔案）。
**性質**：可用性與表述修正（三個子項）；不改票 169 已定案的行為。
**交叉引用**：票 169〈七之一〉列出的 AC-3 驗收彩排報告（`.dev/reports/`，不進版控）；本 repo 立案時 HEAD `5528204`。

---

## 一｜背景

票 169 的 AC-3 驗收彩排（第一輪到第四輪）通過，但過程中看到三個與核准／重驗／復原無關的問題：一句可能與事實不符的安裝訊息、一個沒跟著改的待決清單標題，以及 bootstrap 在錯的目錄或錯的 shell 下執行的風險。三者都不阻擋安裝完成，所以不塞回票 169。

以下行號為立案當下以 Grep 讀到的位置（HEAD `5528204`）。

---

## 二｜子項

### S1｜「已強制帶過去」清單疑似與實際 copy scope 不一致

**已移至票 172（2026-11-10，Jeff 裁 3B）**；本段保留原文作紀錄，S1 不再在本票處理。

- installer 輸出「**來源的 .gitignore 蓋住了這些框架檔**,已強制帶過去」（`.claude/portable/install.py:1459`），並列出 648 個上游被忽略的檔，多數在 `.dev/reports/`。
- 清單來源 `ignored_framework_files()`（`install.py:160`）只排除 `skip`（`:180`）；而 `.dev/` 在 manifest 標 `generate`（`.agents/portable-manifest.txt:135`），不進 copy 桶。
- AC-3 第三輪-B 的全量 `git check-ignore` 證據：彩排中「上游 ignored 卻存在」的檔，全部落在 setup_venv／mirror／pycache／installer_state 四個已知類別，other＝0。verify_gates 的輸出也含同形清單。
- **未定性**：是否「只是顯示錯誤」，待本票調查。已知限制：未取得原始 648 路徑集合，不能逐條判定每一項是否被複製。

### S2｜decisions-pending 的 extension policy 段標題沒跟著改

- 標題仍是「extension policy 是安裝器產生的最小版 —— 不是核准過的觀測快照」（`install.py:549`）。
- 票 169 之後，名冊是依核准候選登記的內容；說明文字已依情況改寫（票 169 輪三的 `extension_note`），標題沒有。
- AC-3 第三輪-B 在彩排的 `docs/decisions-pending.md` 實際看到這個標題。

### S3｜bootstrap 依當下目錄定位 repo；Windows PowerShell 沒有 `sh`

- `bootstrap.sh:47-48`：`root="$(git rev-parse --show-toplevel)"`／`cd "$root"`。在其他 repo 的目錄執行，會把 `core.hooksPath` 設到那個 repo。
- Windows PowerShell 預設 PATH 找不到 `sh`：AC-3 第三輪-B 的 `Start-Process -FilePath sh` 因此無法啟動；第四輪改以 Git 安裝目錄的 `bin\sh.exe` 完整路徑＋WorkingDirectory 才完成。
- 現有文件：`docs/machine-init.md:958` 已寫「**⚠ Windows 請在 Git Bash 裡跑**（裝 git 時會一起裝）—— PowerShell 沒有 `sh` 這個指令」。所以缺的不是「完全沒寫」，而是 installer 結尾的提示（「要跑一次 `sh bootstrap.sh`」）沒有帶到這個前提；是否要在 bootstrap 或 installer 內處理，待本票裁。

---

## 三｜AC 草案（**草案，待裁決者定案**）

- **AC-S1**：installer 的「已強制帶過去」清單只列實際被複製進 target 的檔（或改成不宣稱已複製的措辭）；有測試證明：上游 ignored、標 `generate` 的路徑不會出現在該清單裡，或出現時措辭不宣稱已複製。
  - **AC-S1 已移至票 172（2026-11-10，Jeff 裁 3B）**；本條保留原文作紀錄，不再在本票驗收。
- **AC-S2**：名冊經核准登記了任何項目時，decisions-pending 的 extension policy 段標題不再宣稱「不是核准過的觀測快照」；名冊為空時維持原標題；兩種情況都有測試。
- **AC-S3**：從 target 以外的 git repo 目錄執行 bootstrap，不會改到任何 repo 的 `core.hooksPath`（明確拒絕，或改以腳本自身位置定位）；有測試證明。Windows 上的執行方式在 installer 結尾提示或 bootstrap 失敗訊息中寫明（是否需要測試，待裁）。

---

## 四｜不在本票範圍

- 票 169 已定案的核准／重驗／復原行為。
- R10 synced 長期政策（票 169 第二層 L2）。

## 五｜關聯

- 票 169（新下游安裝的 R10 名冊前置核准；AC-3 驗收彩排發現本票三項）。
