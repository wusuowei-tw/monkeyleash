# 票 148 —— staged 清單在 rename 時漏列(權威層／leak scan 側)

**狀態**:**立案(未排程)。**
**優先度**:**未定。**(審查建議見下;排程由 Jeff 另裁。)
**發現於**:2026-10-07,票 146 第五站獨立審查 (k) O-1。
**來源**:`docs/audits/2026-10-07-146-station5-independent-review.md`(§4 (k) O-1、(d))。
**交叉引用**:票 140 A-1(`docs/tickets/framework-updates/140-sixth-station-2026-09-13-inventory.md` :38–51)。本票是該格「仍待確認：未實測 rename 是否真能繞過」的實測補件。

---

## 命題

staged 清單遇到 rename 時會漏列。漏法有兩種，不能統稱「只漏來源」:

### 1. 「來源被隱藏」—— 已由票 146 N-1 修正，不屬本票

- 位置:`gate.py` `_staged_names_all`。這個呼叫點沒有 diff-filter,原本也沒有 `--no-renames`。
- 審查 `probe_rename.py` case A(`git mv docs/draft-allowlist.json .agents/extension-allowlist.json`):只列出目的，沒有列出來源的刪除。【實測】
- 票 146 N-1 已加上 `--no-renames` 修正(`98099bae297b68e5c6cd4787ea8474d3f400ccc0`)。**這一項不屬本票**,列出只是為了和第 2 項區分。

### 2. 「rename 整筆被排除」—— 本票對象

- 位置:權威層與 leak scan 的 staged 清單使用 `--diff-filter=ACM`。審查當時的行號是 `gate.py:4024`、`scanner.py:499-500`;`leak_scan.py:321` 經由 `scanner.staged_paths` 取得清單。
- 機制:git 預設會做 rename 配對，配成的狀態是 `R`,而 `R` 不在 `ACM` 之內。
- 審查 `probe_rename.py` case B(`git mv src/a.py src/b.py`)原文:

  ```
    staged_paths 同款(--diff-filter=ACM): []
    加 --no-renames:                       ['src/b.py']
  ```

  ⇒ 來源與目的**都不在**清單裡。【實測】

### 3. 後果

- 改名的檔不會進入 R1 / R2 / R3 / R8 的逐檔判定(依審查原文，讀碼推論)。【推論】
- 改名的檔也不會進入 leak scan 的掃描清單;leak scan 對空清單回 0(`leak_scan.py:344`)。
- 「改名時夾帶秘密不會被掃」是從「清單為空」推出來的;審查沒有實際放入秘密去跑。【推論】

## 環境註記

- 審查實測環境:git 2.53.0.windows.2;repo 沒有 `diff.renames` 設定(`git config --get-all diff.renames` exit 1)。
- 行號是審查當時的版本，立票時沒有重新核對。

## 審查建議(非 Jeff 裁決)

審查者認為本票的嚴重度高於票 146 所有後補項，建議優先處理。**排程由 Jeff 另裁。**

## 範圍

- 立案本身不含任何修法。
- 下一步：唯讀盤點所有使用 `--diff-filter` 或會做 rename 配對的 staged 清單呼叫點。
- 本票只引用審查檔與票 140 既有的文字，沒有新增未經實測的主張。
