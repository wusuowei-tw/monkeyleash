# 95 — quickstart 沒有告訴 Windows 讀者要用哪個殼

**狀態**:**README 兩份已修(2026-08-31);`docs/machine-init.md` 已補。剩:文章那一句(不進版控,由 Jeff 改)。**
**時鐘**:**上線之後**
**站別**:立案時 `implement`;動工前重設 `ticket_id`
**前置**:票 27(權威層沒接上 git)、票 58(bootstrap 三道 fail-closed)

> **票號取得時點:2026-08-31,重查最大號 94 加一,全庫確認未使用 95。**

---

## 一、事實(2026-08-31,Jeff 在自己的機器上實跑)

| 殼 | 結果 |
|---|---|
| **PowerShell** | `sh bootstrap.sh` → **無法辨識 'sh' 詞彙** |
| **Git Bash** | 正常:`core.hooksPath -> .githooks`;第二次 `pytest` = `1 failed / 1107 passed / 3 skipped / 3 xfailed`,`TestAuthorityLayerIsWired` **轉綠** |

那一條剩下的紅是 `TestLegacyNoRedlightList` —— **已知,登記在 `K5`**,不是本票的事。

## 二、🔴 缺在哪:**說明文件沒講殼**

`sh bootstrap.sh` 出現在**兩份 README 的 quickstart 第三行**:

```
README.md:44        sh bootstrap.sh          # wires .githooks/ via core.hooksPath (once per clone)
README.zh-TW.md:44  sh bootstrap.sh          # 用 core.hooksPath 接上 .githooks/(每個 clone 一次)
```

而**前提節**兩份都只寫:

```
README.md:36        - Python ≥ 3.10, git
README.zh-TW.md:37  - Python ≥ 3.10、git
```

**全庫查證(2026-08-31)**:`README.md` / `README.zh-TW.md` **完全沒有**
`bash` / `shell` / `Windows` / `PowerShell` / `Git Bash` 任何一個字
(唯一的 `Bash` 命中是規則表裡的 R7,與此無關)。

> ### **一個 Windows 訪客照 README 第三行做,拿到的是「無法辨識 'sh'」。**
> **而那是 GitHub 訪客的第一眼** —— 比文章更前面。

## 三、★ 修的是說明文件,**不是 `bootstrap.sh`**(寫死)

> ### **不要為了 Windows 去改一支已經正確的腳本。**

`bootstrap.sh` 是 POSIX sh 腳本,`.gitattributes` 明寫 `*.sh text eol=lf`,
CI 也用 `sh bootstrap.sh` 跑得好好的。**它沒有壞。**
壞的是**沒有人告訴讀者他需要一個 POSIX 殼**,而 Windows 上那個殼叫 Git Bash
(**隨 Git for Windows 一起裝,所以前提節寫的 `git` 其實已經隱含了它** ——
只是沒有人把那句話說出來)。

**候選修法(擇一,另裁)**:

1. 前提節補一行:Windows 用 Git Bash(隨 Git for Windows 附帶)
2. quickstart 那一行加註解:`# Windows: run this in Git Bash, not PowerShell`
3. 兩者都做

**不做的**:改 `bootstrap.sh`、加一支 `.ps1`、在腳本裡偵測殼。
**那些都是把一個文件問題變成一個要維護兩份的問題。**

## 四、驗收

- [x] **兩份 README 同步(英 / 繁,內容對等)** —— 2026-08-31 落地,補在**前提節**,
      不是指令方塊後面(**讀者是先看前提才照著打**)
- [x] **補的那句話不寫死條數、不寫死平台清單** —— 只點名 Windows 這一個實測過的情況
- [x] **`docs/machine-init.md:604` 同步**(優先序在兩份 README 之後,同輪一起做)
- [ ] ⚠ **文章那一句**(**文章不進版控,由 Jeff 改,不在本票範圍**)

### 落地內容(逐字)

```
README.md(前提節)
- **On Windows, run the `bootstrap.sh` line in Git Bash** (bundled with Git for
  Windows) — PowerShell has no `sh`. Everything else runs in any shell.

README.zh-TW.md(前提節)
- **Windows 請在 Git Bash 裡跑 `bootstrap.sh` 那一行**(裝 git 時會一起裝)——
  PowerShell 沒有 `sh` 這個指令。其餘指令任何殼都跑得動。
```

**`bootstrap.sh` 一個位元組都沒有動**,也沒有加 `.ps1`、沒有在腳本裡偵測殼 ——
照本票第三節寫死的那條。
