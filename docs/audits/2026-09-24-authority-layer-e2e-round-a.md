# 權威層端對端驗證 A 輪 —— REAL 層證據(持久化)

**這份檔案的身分**:`.dev/reports/` **不進版控**,所以只在票面引用檔名
**不足以長期保存證據**。本檔是那份報告的**可公開內容**,存進版控供票 133 / 138 引用。

| | |
|---|---|
| **來源報告** | `.dev/reports/2026-09-24T042056Z-authority-layer-e2e-roundA.md` |
| **來源 sha256** | `2db5eb62f58eb6213197f39cf1e5a3c67299db6b9097617727755ea0ed40e1c3` |
| **來源行數** | 527 |
| **受測版本**(`--sha`) | `9726ab4c0954933048e26791c2f8040b3ca5ee85` |
| **腳本版本**(`scripts/e2e_authority_layer.py` 的 sha256) | `cc07ee05fe5a0a5f859d065c8f77b438034a7d5d2e15c9db23feacd4ad85ad0b` |
| **執行者** | **Jeff 本人**,普通 PowerShell ——**由裁決端確認**,不是腳本自述 |

> ⚠ **腳本版本 ≠ 受測版本。** `--sha` 釘的是 clone 出來受檢的那個 commit;
> 腳本是從正式 repo 的工作樹跑的,兩者可以不同步。

## ⚠ 這不是逐字原文 —— 遮罩清單

下面的內容**經過遮罩**,因此**不得稱為逐字原文**。實際替換:

- **含使用者名稱的暫存目錄絕對路徑** —— 替換 **1** 處,代以 `<TEMP>\mk-e2e-<本輪隨機後綴>`

**遮罩以外的內容未改動**(未刪節、未重排)。
遮罩後殘留的 `C:\Users\…` 片段數:**0**。

**核對方式**:對來源檔套用上表那一條規則,結果應與本檔〈報告內容〉一節相同;
兩邊的 sha256 **依定義不同**(遮罩改了位元組),所以核對的是**規則**而不是雜湊相等。

## 執行者確認的來源

**裁決端確認**(2026-09-24):本輪由 **Jeff 本人**在普通 PowerShell 執行。
⚠ 報告本文那一段寫的是腳本的中性措辭
(「正式驗收模式;執行者身分由本次人工執行紀錄確認」)——
**腳本無法驗證身分**,所以身分這一格的權威在裁決端,不在報告本文。

**條文位置**:`docs/agents/commander.md` §六〈只有 Jeff 能做的〉
〈REAL 層材料的來源限制〉。來源逐字:
**本輪裁決確認;裁決者轉述此要求源於 2026-09-03,本次未取得該日原始裁決文件。**

## 數量與證明力(**照實寫**)

- **17 項 = 16 項真正 `git commit` 案例 + 1 項靜態觀察**(`11b-static`,不下 commit)。
  ⚠ **不得寫成「17 次提交都有 hook 執行紀錄」。**
- 16 項 commit 案例**全部**有 `git trace2` 的 `pre-commit` hook 啟動紀錄
  (9 項 rc=0 放行 + 7 項 rc=1 擋下)。
- 本輪除了真 hook **【接線】**,也驗證了所列案例的**現行行為**,
  含部分 **index / 工作樹分歧的正反對照**。
- **未執行 B 輪** ⇒ **本輪不提供舊版／新版的端對端差異證據**。
  【差異】由**隔離層既有證據**提供(票 133 的 #10 / #11 / #13)。
- **#12 僅【接線】** —— 正式配置下 `EXEMPTION_LOG` 與舊碼自組的路徑逐字相同,
  真 hook 在任何構造下都給一樣的答案。
- **#11②** 限定為:**「靜態構造一個未暫存目標時,正常 `staged_paths` 不會選到它。」**
  ⚠ **不概括成真實提交流程永遠不可能遇到 index 讀取失敗** ——
  `staged_blob` 回 `None` 有兩種可能(不在 index、**或 git 本身執行失敗**),
  後者本輪完全沒有涵蓋。

## 限定

- **單機(本筆電)單次。** 沒有第二台機器、沒有 CI、沒有重複跑。
- **腳本由 agent 設計與撰寫、由人執行** —— **兩者不互相背書**。
  人工按下按鈕不自動代表獨立設計或獨立驗收。
- **未掃下游 repo。**
- `.dev/provenance.jsonl` 是**驗證者自建,非 `sync.py` 產物**。

---

## 報告內容(遮罩後)

# 權威層端對端驗證 —— A 輪(六格)

**時間**:2026-09-24T04:20:56.058546+00:00
**釘住的 SHA**:`9726ab4c0954933048e26791c2f8040b3ca5ee85`
**B 輪**:未實作(【差異】由隔離層既有測試提供)
**執行者**:見下方〈執行安排〉
**腳本版本**(這支 `.py` 的 sha256):`cc07ee05fe5a0a5f859d065c8f77b438034a7d5d2e15c9db23feacd4ad85ad0b`
⚠ **腳本版本與 `--sha` 指定的【受測版本】是兩件事** ——
`--sha` 釘的是 clone 出來受檢的那個 commit;腳本本身是從正式 repo 的工作樹跑的,兩者可以不同步。

## 正式 repo 進出

| | 進入 | 結束 |
|---|---|---|
| `HEAD` | `9726ab4c0954933048e26791c2f8040b3ca5ee85` | `9726ab4c0954933048e26791c2f8040b3ca5ee85` |
| `status --porcelain` | (空) | (空) |

⚠ 措辭:**受追蹤檔案、index、HEAD 與設定不變;`.dev/reports/` 有預期新增。**
**不宣稱正式 repo 全程沒有任何寫入。**

## #13 上游前置(不記完整路徑)

- 指標檔格式合法(恰好一行):`True`
- 是 git repo:`True`
- commit:path 可讀:`True`
- 上游位置識別(遮蔽):`sha256:1be43c353548838d`

⚠ `.dev/provenance.jsonl` 是**驗證者自建,非 `sync.py` 產物**。

## 摘要

| 格 | 案例 | 預期 | 實際 | 判定 | 證明力 |
|---|---|---|---|---|---|
| #8 | `8-legal` | exit 0;HEAD 前進 | rc=0;HEAD 前進;trace2 hook=True | **通過** | 【接線】 |
| #8 | `8-reject` | exit 1;[R2/commit];含 index 來源提示 | rc=1;HEAD 不變;trace2 hook=True | **通過** | 【接線】 |
| #8 | `8-reverse` | exit 0(現行版本判 index) | rc=0;HEAD 前進;trace2 hook=True | **通過** | 【接線】+ 現行版本判 index |
| #9 | `9-legal` | exit 0;HEAD 前進 | rc=0;HEAD 前進;trace2 hook=True | **通過** | 【接線】 |
| #9 | `9-reject` | exit 1;[R3] 找不到對應測試;含 index 來源提示 | rc=1;HEAD 不變;trace2 hook=True | **通過** | 【接線】 |
| #10 | `10-legal` | exit 0;HEAD 前進 | rc=0;HEAD 前進;trace2 hook=True | **通過** | 【接線】 |
| #10 | `10-reject` | exit 1;[R3];**不得出現 [R6]** | rc=1;HEAD 不變;trace2 hook=True | **通過** | 【接線】 |
| #11 | `11-legal` | exit 0;HEAD 前進 | rc=0;HEAD 前進;trace2 hook=True | **通過** | 【接線】 |
| #11 | `11-reject` | exit 1;[R3] 找不到對應測試 | rc=1;HEAD 不變;trace2 hook=True | **通過** | 【接線】 |
| #11 | `11-reverse` | exit 0(現行版本判 index) | rc=0;HEAD 前進;trace2 hook=True | **通過** | 【接線】+ 現行版本判 index |
| #11② | `11b-static` | `git diff --cached -z --name-only --diff-filter=ACM` 不含該檔 | staged=['.claude/hooks/redlight.py'] | **通過** | 【真 hook 不可構造】(限定:靜態構造一個未暫存目標時,正常 staged_paths 不會選到它) |
| #12 | `12-legal` | exit 0;HEAD 前進 | rc=0;HEAD 前進;trace2 hook=True | **通過** | 【接線】only(見說明:正式配置下新舊路徑相同,無【差異】可驗) |
| #12 | `12-reject-not-in-head` | exit 1;[R3] | rc=1;HEAD 不變;trace2 hook=True | **通過** | 【接線】only |
| #12 | `12-reject-wrong-module` | exit 1;[R3] | rc=1;HEAD 不變;trace2 hook=True | **通過** | 【接線】only |
| #13 | `13-legal` | exit 0;HEAD 前進;帳本出現 upstream-provenance | rc=0;HEAD 前進;trace2 hook=True | **通過** | 【接線】 |
| #13 | `13-reject` | exit 1;[R3];**不得出現 [R8** | rc=1;HEAD 不變;trace2 hook=True | **通過** | 【接線】 |
| #13 | `13-reverse` | exit 0(現行版本判 index) | rc=0;HEAD 前進;trace2 hook=True | **通過** | 【接線】+ 現行版本判 index |

## 逐案例證據

### `8-legal` —— 站別定義原版 + legacy 成員的無害改動

- **判定**:**通過**
- **構造前提**:`'成立(已比對 index 與工作樹的實際內容)'`
- **staged**:`['.claude/hooks/redlight.py']`
- **rc**:`0`
- **head_before**:`'9726ab4c0954933048e26791c2f8040b3ca5ee85'`
- **head_after**:`'91416836ef204c62ca354de4e860e9337d776dc6'`
- **head 不變**:`False`
- **git trace2 看到 pre-commit hook**:`True`
- **trace2 樣本**:`['.githooks/pre-commit pre-commit hook']`
- **帳本新增行**:`[]`
- **hook 身分**:`{'core.hooksPath': '.githooks', '解析後的 hook 路徑': '.githooks/pre-commit', 'hook sha256': '95408d29ee3ab03315d34595833e3941550f0fd62ece31757dec7102acf81a72', 'gate.py sha256': 'e69932bc32c79fd5a6d7b74f97d9be701fde5057948f6b2b0fc594f06790e8c4', 'leak_scan.py sha256': '4d21e808f1db5f669c8dd33d2423619305a60957080fe89a1d3b5fc3889cace2', 'bootstrap 用的殼': '<Git 安裝根>/usr/bin/sh.exe'}`

```
[detached HEAD 9141683] e2e: 8-legal
 1 file changed, 2 insertions(+)
```

### `8-reject` —— index 定義 = implement 非可寫站;工作樹定義 = 原版

- **判定**:**通過**
- **構造前提**:`'成立(已比對 index 與工作樹的實際內容)'`
- **staged**:`['.agents/pipeline-stages.yaml', '.claude/hooks/redlight.py']`
- **rc**:`1`
- **head_before**:`'9726ab4c0954933048e26791c2f8040b3ca5ee85'`
- **head_after**:`'9726ab4c0954933048e26791c2f8040b3ca5ee85'`
- **head 不變**:`True`
- **git trace2 看到 pre-commit hook**:`True`
- **trace2 樣本**:`['.githooks/pre-commit pre-commit hook']`
- **帳本新增行**:`[]`
- **hook 身分**:`{'core.hooksPath': '.githooks', '解析後的 hook 路徑': '.githooks/pre-commit', 'hook sha256': '95408d29ee3ab03315d34595833e3941550f0fd62ece31757dec7102acf81a72', 'gate.py sha256': 'e69932bc32c79fd5a6d7b74f97d9be701fde5057948f6b2b0fc594f06790e8c4', 'leak_scan.py sha256': '4d21e808f1db5f669c8dd33d2423619305a60957080fe89a1d3b5fc3889cace2', 'bootstrap 用的殼': '<Git 安裝根>/usr/bin/sh.exe'}`
- **逐條判準**:
  - 非零退出碼:`True`
  - HEAD 不變:`True`
  - 有閘門擋下訊息:`True`
  - git trace2 看到 hook:`True`
  - 暫存內容仍在 index:`True`
  - 訊息含 '[R2/commit]':`True`
  - 訊息含 '本次站別定義取自':`True`
  - 訊息含 '.claude/hooks/redlight.py':`True`
  - 訊息不含 '[R3]':`True`

```

[六站閘門/pre-commit] commit 已擋下,1 項違規:

  [R2/commit][enforce] .claude/hooks/redlight.py:current_stage='implement' 是前置站,卻要提交原始碼。
     代表這些碼寫在該寫之前。回頭把流程走完,或由使用者調整 current_stage。
     上游內容豁免不適用:.claude/hooks/redlight.py 沒有 provenance 紀錄 —— 它不是同步進來的成品,所以紅燈責任在本地。
     本次站別定義取自**暫存區(index)**;工作樹裡尚未暫存的定義修改,不影響本次提交。
     (這不表示兩版一定不同;暫存之後是否通過,仍取決於定義本身怎麼寫。)

上面每一項都指出了是哪一個前提沒滿足 —— 修掉它們再提交。
```

### `8-reverse` —— index 定義 = 原版;工作樹定義 = implement 非可寫站

- **判定**:**通過**
- **構造前提**:`'成立(已比對 index 與工作樹的實際內容)'`
- **staged**:`['.claude/hooks/redlight.py']`
- **rc**:`0`
- **head_before**:`'9726ab4c0954933048e26791c2f8040b3ca5ee85'`
- **head_after**:`'40f2e962b855148da03e2077aa7bada6f6053558'`
- **head 不變**:`False`
- **git trace2 看到 pre-commit hook**:`True`
- **trace2 樣本**:`['.githooks/pre-commit pre-commit hook']`
- **帳本新增行**:`[]`
- **hook 身分**:`{'core.hooksPath': '.githooks', '解析後的 hook 路徑': '.githooks/pre-commit', 'hook sha256': '95408d29ee3ab03315d34595833e3941550f0fd62ece31757dec7102acf81a72', 'gate.py sha256': 'e69932bc32c79fd5a6d7b74f97d9be701fde5057948f6b2b0fc594f06790e8c4', 'leak_scan.py sha256': '4d21e808f1db5f669c8dd33d2423619305a60957080fe89a1d3b5fc3889cace2', 'bootstrap 用的殼': '<Git 安裝根>/usr/bin/sh.exe'}`

```
[detached HEAD 40f2e96] e2e: 8-reverse
 1 file changed, 2 insertions(+)
```

### `9-legal` —— research 站 + research/ 底下新檔(無測試)⇒ #9 豁免 R3

- **判定**:**通過**
- **構造前提**:`'成立(已比對 index 與工作樹的實際內容)'`
- **staged**:`['research/probe.py']`
- **rc**:`0`
- **head_before**:`'9726ab4c0954933048e26791c2f8040b3ca5ee85'`
- **head_after**:`'89f5ba886ee0133519b7c17824410bf10a1f4156'`
- **head 不變**:`False`
- **git trace2 看到 pre-commit hook**:`True`
- **trace2 樣本**:`['.githooks/pre-commit pre-commit hook']`
- **帳本新增行**:`[]`
- **hook 身分**:`{'core.hooksPath': '.githooks', '解析後的 hook 路徑': '.githooks/pre-commit', 'hook sha256': '95408d29ee3ab03315d34595833e3941550f0fd62ece31757dec7102acf81a72', 'gate.py sha256': 'e69932bc32c79fd5a6d7b74f97d9be701fde5057948f6b2b0fc594f06790e8c4', 'leak_scan.py sha256': '4d21e808f1db5f669c8dd33d2423619305a60957080fe89a1d3b5fc3889cace2', 'bootstrap 用的殼': '<Git 安裝根>/usr/bin/sh.exe'}`

```
[detached HEAD 89f5ba8] e2e: 9-legal
 1 file changed, 1 insertion(+)
 create mode 100644 research/probe.py
```

### `9-reject` —— index 定義拿掉 exempts_r3_in_scope;工作樹保留

- **判定**:**通過**
- **構造前提**:`'成立(已比對 index 與工作樹的實際內容)'`
- **staged**:`['.agents/pipeline-stages.yaml', 'research/probe.py']`
- **rc**:`1`
- **head_before**:`'9726ab4c0954933048e26791c2f8040b3ca5ee85'`
- **head_after**:`'9726ab4c0954933048e26791c2f8040b3ca5ee85'`
- **head 不變**:`True`
- **git trace2 看到 pre-commit hook**:`True`
- **trace2 樣本**:`['.githooks/pre-commit pre-commit hook']`
- **帳本新增行**:`[]`
- **hook 身分**:`{'core.hooksPath': '.githooks', '解析後的 hook 路徑': '.githooks/pre-commit', 'hook sha256': '95408d29ee3ab03315d34595833e3941550f0fd62ece31757dec7102acf81a72', 'gate.py sha256': 'e69932bc32c79fd5a6d7b74f97d9be701fde5057948f6b2b0fc594f06790e8c4', 'leak_scan.py sha256': '4d21e808f1db5f669c8dd33d2423619305a60957080fe89a1d3b5fc3889cace2', 'bootstrap 用的殼': '<Git 安裝根>/usr/bin/sh.exe'}`
- **逐條判準**:
  - 非零退出碼:`True`
  - HEAD 不變:`True`
  - 有閘門擋下訊息:`True`
  - git trace2 看到 hook:`True`
  - 暫存內容仍在 index:`True`
  - 訊息含 '[R3]':`True`
  - 訊息含 'research/probe.py':`True`
  - 訊息含 '本次站別定義取自':`True`

```

[六站閘門/pre-commit] commit 已擋下,1 項違規:

  [R3][enforce] research/probe.py:找不到對應測試(tests/test_probe.py),不可先寫功能碼。
     請先寫測試、執行它、確認紅燈,再回來寫功能碼。票號:未設定
     若這不是原始碼(誤擋):把它的目錄加進 .claude/hooks/gate.py:233 的 NON_SOURCE_EXT 加一筆 '.py'(附理由:為什麼它不會被執行或被建置消費);
     **不得退回白名單**(docs/adr/0003)
     本次站別定義取自**暫存區(index)**;工作樹裡尚未暫存的定義修改,不影響本次提交。
     (這不表示兩版一定不同;暫存之後是否通過,仍取決於定義本身怎麼寫。)

上面每一項都指出了是哪一個前提沒滿足 —— 修掉它們再提交。
```

### `10-legal` —— legacy 清單既有成員(確在 go-live 樹裡)⇒ 豁免成立

- **判定**:**通過**
- **構造前提**:`'成立(已比對 index 與工作樹的實際內容)'`
- **staged**:`['.claude/hooks/redlight.py']`
- **rc**:`0`
- **head_before**:`'9726ab4c0954933048e26791c2f8040b3ca5ee85'`
- **head_after**:`'d7f9d0040057f8e73321f7c69c4b30b461f2ed53'`
- **head 不變**:`False`
- **git trace2 看到 pre-commit hook**:`True`
- **trace2 樣本**:`['.githooks/pre-commit pre-commit hook']`
- **帳本新增行**:`[]`
- **hook 身分**:`{'core.hooksPath': '.githooks', '解析後的 hook 路徑': '.githooks/pre-commit', 'hook sha256': '95408d29ee3ab03315d34595833e3941550f0fd62ece31757dec7102acf81a72', 'gate.py sha256': 'e69932bc32c79fd5a6d7b74f97d9be701fde5057948f6b2b0fc594f06790e8c4', 'leak_scan.py sha256': '4d21e808f1db5f669c8dd33d2423619305a60957080fe89a1d3b5fc3889cace2', 'bootstrap 用的殼': '<Git 安裝根>/usr/bin/sh.exe'}`

```
[detached HEAD d7f9d00] e2e: 10-legal
 1 file changed, 2 insertions(+)
```

### `10-reject` —— 工作樹清單加一筆不在 go-live 樹裡的條目(不 add)

- **判定**:**通過**
- **構造前提**:`'成立(已比對 index 與工作樹的實際內容)'`
- **staged**:`['pkg/thing.py']`
- **rc**:`1`
- **head_before**:`'9726ab4c0954933048e26791c2f8040b3ca5ee85'`
- **head_after**:`'9726ab4c0954933048e26791c2f8040b3ca5ee85'`
- **head 不變**:`True`
- **git trace2 看到 pre-commit hook**:`True`
- **trace2 樣本**:`['.githooks/pre-commit pre-commit hook']`
- **帳本新增行**:`[]`
- **hook 身分**:`{'core.hooksPath': '.githooks', '解析後的 hook 路徑': '.githooks/pre-commit', 'hook sha256': '95408d29ee3ab03315d34595833e3941550f0fd62ece31757dec7102acf81a72', 'gate.py sha256': 'e69932bc32c79fd5a6d7b74f97d9be701fde5057948f6b2b0fc594f06790e8c4', 'leak_scan.py sha256': '4d21e808f1db5f669c8dd33d2423619305a60957080fe89a1d3b5fc3889cace2', 'bootstrap 用的殼': '<Git 安裝根>/usr/bin/sh.exe'}`
- **逐條判準**:
  - 非零退出碼:`True`
  - HEAD 不變:`True`
  - 有閘門擋下訊息:`True`
  - git trace2 看到 hook:`True`
  - 暫存內容仍在 index:`True`
  - 訊息含 '[R3]':`True`
  - 訊息含 'pkg/thing.py':`True`
  - 訊息不含 '[R6]':`True`

```

[六站閘門/pre-commit] commit 已擋下,1 項違規:

  [R3][enforce] pkg/thing.py:找不到對應測試(tests/test_thing.py),不可先寫功能碼。
     請先寫測試、執行它、確認紅燈,再回來寫功能碼。票號:未設定
     若這不是原始碼(誤擋):把它的目錄加進 .claude/hooks/gate.py:233 的 NON_SOURCE_EXT 加一筆 '.py'(附理由:為什麼它不會被執行或被建置消費);
     **不得退回白名單**(docs/adr/0003)
     本次站別定義取自**暫存區(index)**;工作樹裡尚未暫存的定義修改,不影響本次提交。
     (這不表示兩版一定不同;暫存之後是否通過,仍取決於定義本身怎麼寫。)

上面每一項都指出了是哪一個前提沒滿足 —— 修掉它們再提交。
```

### `11-legal` —— index 的 __init__.py 是空的 ⇒ 純標記,豁免成立

- **判定**:**通過**
- **構造前提**:`'成立(已比對 index 與工作樹的實際內容)'`
- **staged**:`['pkg/__init__.py']`
- **rc**:`0`
- **head_before**:`'9726ab4c0954933048e26791c2f8040b3ca5ee85'`
- **head_after**:`'e7f70af5c0327b253e601646a58f19bef98679b3'`
- **head 不變**:`False`
- **git trace2 看到 pre-commit hook**:`True`
- **trace2 樣本**:`['.githooks/pre-commit pre-commit hook']`
- **帳本新增行**:`[]`
- **hook 身分**:`{'core.hooksPath': '.githooks', '解析後的 hook 路徑': '.githooks/pre-commit', 'hook sha256': '95408d29ee3ab03315d34595833e3941550f0fd62ece31757dec7102acf81a72', 'gate.py sha256': 'e69932bc32c79fd5a6d7b74f97d9be701fde5057948f6b2b0fc594f06790e8c4', 'leak_scan.py sha256': '4d21e808f1db5f669c8dd33d2423619305a60957080fe89a1d3b5fc3889cace2', 'bootstrap 用的殼': '<Git 安裝根>/usr/bin/sh.exe'}`

```
[detached HEAD e7f70af] e2e: 11-legal
 1 file changed, 0 insertions(+), 0 deletions(-)
 create mode 100644 pkg/__init__.py
```

### `11-reject` —— index 含 def;工作樹改成空的

- **判定**:**通過**
- **構造前提**:`'成立(已比對 index 與工作樹的實際內容)'`
- **staged**:`['pkg/__init__.py']`
- **rc**:`1`
- **head_before**:`'9726ab4c0954933048e26791c2f8040b3ca5ee85'`
- **head_after**:`'9726ab4c0954933048e26791c2f8040b3ca5ee85'`
- **head 不變**:`True`
- **git trace2 看到 pre-commit hook**:`True`
- **trace2 樣本**:`['.githooks/pre-commit pre-commit hook']`
- **帳本新增行**:`[]`
- **hook 身分**:`{'core.hooksPath': '.githooks', '解析後的 hook 路徑': '.githooks/pre-commit', 'hook sha256': '95408d29ee3ab03315d34595833e3941550f0fd62ece31757dec7102acf81a72', 'gate.py sha256': 'e69932bc32c79fd5a6d7b74f97d9be701fde5057948f6b2b0fc594f06790e8c4', 'leak_scan.py sha256': '4d21e808f1db5f669c8dd33d2423619305a60957080fe89a1d3b5fc3889cace2', 'bootstrap 用的殼': '<Git 安裝根>/usr/bin/sh.exe'}`
- **逐條判準**:
  - 非零退出碼:`True`
  - HEAD 不變:`True`
  - 有閘門擋下訊息:`True`
  - git trace2 看到 hook:`True`
  - 暫存內容仍在 index:`True`
  - 訊息含 '[R3]':`True`
  - 訊息含 'pkg/__init__.py':`True`

```

[六站閘門/pre-commit] commit 已擋下,1 項違規:

  [R3][enforce] pkg/__init__.py:找不到對應測試(tests/test___init__.py),不可先寫功能碼。
     請先寫測試、執行它、確認紅燈,再回來寫功能碼。票號:未設定
     若這不是原始碼(誤擋):把它的目錄加進 .claude/hooks/gate.py:233 的 NON_SOURCE_EXT 加一筆 '.py'(附理由:為什麼它不會被執行或被建置消費);
     **不得退回白名單**(docs/adr/0003)
     本次站別定義取自**暫存區(index)**;工作樹裡尚未暫存的定義修改,不影響本次提交。
     (這不表示兩版一定不同;暫存之後是否通過,仍取決於定義本身怎麼寫。)

上面每一項都指出了是哪一個前提沒滿足 —— 修掉它們再提交。
```

### `11-reverse` —— index 是空的;工作樹含 def

- **判定**:**通過**
- **構造前提**:`'成立(已比對 index 與工作樹的實際內容)'`
- **staged**:`['pkg/__init__.py']`
- **rc**:`0`
- **head_before**:`'9726ab4c0954933048e26791c2f8040b3ca5ee85'`
- **head_after**:`'9c8e143129eb89e6d0690f1154548bd9aa2b6cb4'`
- **head 不變**:`False`
- **git trace2 看到 pre-commit hook**:`True`
- **trace2 樣本**:`['.githooks/pre-commit pre-commit hook']`
- **帳本新增行**:`[]`
- **hook 身分**:`{'core.hooksPath': '.githooks', '解析後的 hook 路徑': '.githooks/pre-commit', 'hook sha256': '95408d29ee3ab03315d34595833e3941550f0fd62ece31757dec7102acf81a72', 'gate.py sha256': 'e69932bc32c79fd5a6d7b74f97d9be701fde5057948f6b2b0fc594f06790e8c4', 'leak_scan.py sha256': '4d21e808f1db5f669c8dd33d2423619305a60957080fe89a1d3b5fc3889cace2', 'bootstrap 用的殼': '<Git 安裝根>/usr/bin/sh.exe'}`

```
[detached HEAD 9c8e143] e2e: 11-reverse
 1 file changed, 0 insertions(+), 0 deletions(-)
 create mode 100644 pkg/__init__.py
```

### `11b-static` —— 未暫存的 pkg/__init__.py + 已暫存的別的檔

- **判定**:**通過** —— 未暫存的目標確實不在 staged 清單裡
- **構造前提**:`'成立(已比對 index 與工作樹的實際內容)'`
- **staged**:`['.claude/hooks/redlight.py']`
- **hook 身分**:`{'core.hooksPath': '.githooks', '解析後的 hook 路徑': '.githooks/pre-commit', 'hook sha256': '95408d29ee3ab03315d34595833e3941550f0fd62ece31757dec7102acf81a72', 'gate.py sha256': 'e69932bc32c79fd5a6d7b74f97d9be701fde5057948f6b2b0fc594f06790e8c4', 'leak_scan.py sha256': '4d21e808f1db5f669c8dd33d2423619305a60957080fe89a1d3b5fc3889cace2', 'bootstrap 用的殼': '<Git 安裝根>/usr/bin/sh.exe'}`

### `12-legal` —— 帳本紀錄 + 票已進 HEAD 且列了該模組;ticket_id 已清空

- **判定**:**通過**
- **構造前提**:`'成立(已比對 index 與工作樹的實際內容)'`
- **staged**:`['pkg/thing.py']`
- **rc**:`0`
- **head_before**:`'c3af653cb74a03396c46ce6f607bd30fe8b436f7'`
- **head_after**:`'b75fed3ec65ca788e7677f1729a9bf23b6cbc401'`
- **head 不變**:`False`
- **git trace2 看到 pre-commit hook**:`True`
- **trace2 樣本**:`['.githooks/pre-commit pre-commit hook']`
- **帳本新增行**:`['{"ts": "2026-09-24T04:22:19.339111+00:00", "file": "pkg/thing.py", "module": "thing", "ticket": "900", "stage": "implement", "declared_in": "docs/tickets/framework-updates/900-e2e-probe.md", "reason": "ticket-declared", "tool": "e2e-probe", "outcome": "granted", "blocked_by": null, "at_commit": false, "content_hash": null, "result_hash": null, "changes_bytes": null}']`
- **hook 身分**:`{'core.hooksPath': '.githooks', '解析後的 hook 路徑': '.githooks/pre-commit', 'hook sha256': '95408d29ee3ab03315d34595833e3941550f0fd62ece31757dec7102acf81a72', 'gate.py sha256': 'e69932bc32c79fd5a6d7b74f97d9be701fde5057948f6b2b0fc594f06790e8c4', 'leak_scan.py sha256': '4d21e808f1db5f669c8dd33d2423619305a60957080fe89a1d3b5fc3889cace2', 'bootstrap 用的殼': '<Git 安裝根>/usr/bin/sh.exe'}`

```
[detached HEAD b75fed3] e2e: 12-legal
 1 file changed, 2 insertions(+)
 create mode 100644 pkg/thing.py
```

### `12-reject-not-in-head` —— 帳本有紀錄,但票只在工作樹、不在 HEAD

- **判定**:**通過**
- **構造前提**:`'成立(已比對 index 與工作樹的實際內容)'`
- **staged**:`['pkg/thing.py']`
- **rc**:`1`
- **head_before**:`'9726ab4c0954933048e26791c2f8040b3ca5ee85'`
- **head_after**:`'9726ab4c0954933048e26791c2f8040b3ca5ee85'`
- **head 不變**:`True`
- **git trace2 看到 pre-commit hook**:`True`
- **trace2 樣本**:`['.githooks/pre-commit pre-commit hook']`
- **帳本新增行**:`['{"ts": "2026-09-24T04:22:27.203477+00:00", "file": "pkg/thing.py", "module": "thing", "ticket": "900", "stage": "implement", "declared_in": "docs/tickets/framework-updates/900-e2e-probe.md", "reason": "ticket-declared", "tool": "e2e-probe", "outcome": "granted", "blocked_by": null, "at_commit": false, "content_hash": null, "result_hash": null, "changes_bytes": null}']`
- **hook 身分**:`{'core.hooksPath': '.githooks', '解析後的 hook 路徑': '.githooks/pre-commit', 'hook sha256': '95408d29ee3ab03315d34595833e3941550f0fd62ece31757dec7102acf81a72', 'gate.py sha256': 'e69932bc32c79fd5a6d7b74f97d9be701fde5057948f6b2b0fc594f06790e8c4', 'leak_scan.py sha256': '4d21e808f1db5f669c8dd33d2423619305a60957080fe89a1d3b5fc3889cace2', 'bootstrap 用的殼': '<Git 安裝根>/usr/bin/sh.exe'}`
- **逐條判準**:
  - 非零退出碼:`True`
  - HEAD 不變:`True`
  - 有閘門擋下訊息:`True`
  - git trace2 看到 hook:`True`
  - 暫存內容仍在 index:`True`
  - 訊息含 '[R3]':`True`
  - 訊息含 'pkg/thing.py':`True`

```

[六站閘門/pre-commit] commit 已擋下,1 項違規:

  [R3][enforce] pkg/thing.py:找不到對應測試(tests/test_thing.py),不可先寫功能碼。
     請先寫測試、執行它、確認紅燈,再回來寫功能碼。票號:未設定
     若這不是原始碼(誤擋):把它的目錄加進 .claude/hooks/gate.py:233 的 NON_SOURCE_EXT 加一筆 '.py'(附理由:為什麼它不會被執行或被建置消費);
     **不得退回白名單**(docs/adr/0003)
     本次站別定義取自**暫存區(index)**;工作樹裡尚未暫存的定義修改,不影響本次提交。
     (這不表示兩版一定不同;暫存之後是否通過,仍取決於定義本身怎麼寫。)

上面每一項都指出了是哪一個前提沒滿足 —— 修掉它們再提交。
```

### `12-reject-wrong-module` —— 票在 HEAD,但它宣告的是別的模組

- **判定**:**通過**
- **構造前提**:`'成立(已比對 index 與工作樹的實際內容)'`
- **staged**:`['pkg/thing.py']`
- **rc**:`1`
- **head_before**:`'6db06eece05d2f9261d566277ffd80449157dd2b'`
- **head_after**:`'6db06eece05d2f9261d566277ffd80449157dd2b'`
- **head 不變**:`True`
- **git trace2 看到 pre-commit hook**:`True`
- **trace2 樣本**:`['.githooks/pre-commit pre-commit hook']`
- **帳本新增行**:`['{"ts": "2026-09-24T04:22:37.258997+00:00", "file": "pkg/thing.py", "module": "thing", "ticket": "900", "stage": "implement", "declared_in": "docs/tickets/framework-updates/900-e2e-probe.md", "reason": "ticket-declared", "tool": "e2e-probe", "outcome": "granted", "blocked_by": null, "at_commit": false, "content_hash": null, "result_hash": null, "changes_bytes": null}']`
- **hook 身分**:`{'core.hooksPath': '.githooks', '解析後的 hook 路徑': '.githooks/pre-commit', 'hook sha256': '95408d29ee3ab03315d34595833e3941550f0fd62ece31757dec7102acf81a72', 'gate.py sha256': 'e69932bc32c79fd5a6d7b74f97d9be701fde5057948f6b2b0fc594f06790e8c4', 'leak_scan.py sha256': '4d21e808f1db5f669c8dd33d2423619305a60957080fe89a1d3b5fc3889cace2', 'bootstrap 用的殼': '<Git 安裝根>/usr/bin/sh.exe'}`
- **逐條判準**:
  - 非零退出碼:`True`
  - HEAD 不變:`True`
  - 有閘門擋下訊息:`True`
  - git trace2 看到 hook:`True`
  - 暫存內容仍在 index:`True`
  - 訊息含 '[R3]':`True`
  - 訊息含 'pkg/thing.py':`True`

```

[六站閘門/pre-commit] commit 已擋下,1 項違規:

  [R3][enforce] pkg/thing.py:找不到對應測試(tests/test_thing.py),不可先寫功能碼。
     請先寫測試、執行它、確認紅燈,再回來寫功能碼。票號:未設定
     若這不是原始碼(誤擋):把它的目錄加進 .claude/hooks/gate.py:233 的 NON_SOURCE_EXT 加一筆 '.py'(附理由:為什麼它不會被執行或被建置消費);
     **不得退回白名單**(docs/adr/0003)
     本次站別定義取自**暫存區(index)**;工作樹裡尚未暫存的定義修改,不影響本次提交。
     (這不表示兩版一定不同;暫存之後是否通過,仍取決於定義本身怎麼寫。)

上面每一項都指出了是哪一個前提沒滿足 —— 修掉它們再提交。
```

### `13-legal` —— index 位元組 = 上游物件 ⇒ provenance 豁免成立

- **判定**:**通過**
- **構造前提**:`'成立(已比對 index 與工作樹的實際內容)'`
- **staged**:`['pkg/thing.py']`
- **rc**:`0`
- **head_before**:`'9726ab4c0954933048e26791c2f8040b3ca5ee85'`
- **head_after**:`'739e266cca92bac2e9702603222bce755b9b5a53'`
- **head 不變**:`False`
- **git trace2 看到 pre-commit hook**:`True`
- **trace2 樣本**:`['.githooks/pre-commit pre-commit hook']`
- **帳本新增行**:`['{"ts": "2026-09-24T04:22:48.658971+00:00", "file": "pkg/thing.py", "module": "thing", "ticket": null, "stage": "implement", "declared_in": "F-0014", "reason": "upstream-provenance", "tool": "pre-commit", "outcome": "granted", "blocked_by": null, "at_commit": true, "content_hash": "9cb9f6edb7e58f04d4c965a90133e09f39bb6c61ab5273ccebfa835e4ca9cdce", "result_hash": null, "changes_bytes": null}']`
- **hook 身分**:`{'core.hooksPath': '.githooks', '解析後的 hook 路徑': '.githooks/pre-commit', 'hook sha256': '95408d29ee3ab03315d34595833e3941550f0fd62ece31757dec7102acf81a72', 'gate.py sha256': 'e69932bc32c79fd5a6d7b74f97d9be701fde5057948f6b2b0fc594f06790e8c4', 'leak_scan.py sha256': '4d21e808f1db5f669c8dd33d2423619305a60957080fe89a1d3b5fc3889cace2', 'bootstrap 用的殼': '<Git 安裝根>/usr/bin/sh.exe'}`

```
[detached HEAD 739e266] e2e: 13-legal
 1 file changed, 178 insertions(+)
 create mode 100644 pkg/thing.py
```

### `13-reject` —— index 漂移(改內容字元,非行尾);工作樹 = 上游物件

- **判定**:**通過**
- **構造前提**:`'成立(已比對 index 與工作樹的實際內容)'`
- **staged**:`['pkg/thing.py']`
- **rc**:`1`
- **head_before**:`'9726ab4c0954933048e26791c2f8040b3ca5ee85'`
- **head_after**:`'9726ab4c0954933048e26791c2f8040b3ca5ee85'`
- **head 不變**:`True`
- **git trace2 看到 pre-commit hook**:`True`
- **trace2 樣本**:`['.githooks/pre-commit pre-commit hook']`
- **帳本新增行**:`[]`
- **hook 身分**:`{'core.hooksPath': '.githooks', '解析後的 hook 路徑': '.githooks/pre-commit', 'hook sha256': '95408d29ee3ab03315d34595833e3941550f0fd62ece31757dec7102acf81a72', 'gate.py sha256': 'e69932bc32c79fd5a6d7b74f97d9be701fde5057948f6b2b0fc594f06790e8c4', 'leak_scan.py sha256': '4d21e808f1db5f669c8dd33d2423619305a60957080fe89a1d3b5fc3889cace2', 'bootstrap 用的殼': '<Git 安裝根>/usr/bin/sh.exe'}`
- **逐條判準**:
  - 非零退出碼:`True`
  - HEAD 不變:`True`
  - 有閘門擋下訊息:`True`
  - git trace2 看到 hook:`True`
  - 暫存內容仍在 index:`True`
  - 訊息含 '[R3]':`True`
  - 訊息含 'pkg/thing.py':`True`
  - 訊息不含 '[R8':`True`

```

[六站閘門/pre-commit] commit 已擋下,1 項違規:

  [R3][enforce] pkg/thing.py:找不到對應測試(tests/test_thing.py),不可先寫功能碼。
     請先寫測試、執行它、確認紅燈,再回來寫功能碼。票號:未設定
     若這不是原始碼(誤擋):把它的目錄加進 .claude/hooks/gate.py:233 的 NON_SOURCE_EXT 加一筆 '.py'(附理由:為什麼它不會被執行或被建置消費);
     **不得退回白名單**(docs/adr/0003)
     本次站別定義取自**暫存區(index)**;工作樹裡尚未暫存的定義修改,不影響本次提交。
     (這不表示兩版一定不同;暫存之後是否通過,仍取決於定義本身怎麼寫。)

上面每一項都指出了是哪一個前提沒滿足 —— 修掉它們再提交。
```

### `13-reverse` —— index = 上游物件;工作樹漂移

- **判定**:**通過**
- **構造前提**:`'成立(已比對 index 與工作樹的實際內容)'`
- **staged**:`['pkg/thing.py']`
- **rc**:`0`
- **head_before**:`'9726ab4c0954933048e26791c2f8040b3ca5ee85'`
- **head_after**:`'34edca44b4c5dca45c533a7176faf60c9b5e8e4b'`
- **head 不變**:`False`
- **git trace2 看到 pre-commit hook**:`True`
- **trace2 樣本**:`['.githooks/pre-commit pre-commit hook']`
- **帳本新增行**:`['{"ts": "2026-09-24T04:23:05.449518+00:00", "file": "pkg/thing.py", "module": "thing", "ticket": null, "stage": "implement", "declared_in": "F-0014", "reason": "upstream-provenance", "tool": "pre-commit", "outcome": "granted", "blocked_by": null, "at_commit": true, "content_hash": "fafaf8b526623b38ac097be4da0a526786467b14a2914d25408c6e3e663cbf3f", "result_hash": null, "changes_bytes": null}']`
- **hook 身分**:`{'core.hooksPath': '.githooks', '解析後的 hook 路徑': '.githooks/pre-commit', 'hook sha256': '95408d29ee3ab03315d34595833e3941550f0fd62ece31757dec7102acf81a72', 'gate.py sha256': 'e69932bc32c79fd5a6d7b74f97d9be701fde5057948f6b2b0fc594f06790e8c4', 'leak_scan.py sha256': '4d21e808f1db5f669c8dd33d2423619305a60957080fe89a1d3b5fc3889cace2', 'bootstrap 用的殼': '<Git 安裝根>/usr/bin/sh.exe'}`

```
[detached HEAD 34edca4] e2e: 13-reverse
 1 file changed, 178 insertions(+)
 create mode 100644 pkg/thing.py
```

## 清理

- ① 標記檔存在且是本輪的:`True`
- ② 位於系統暫存目錄底下、且 basename 以 mk-e2e- 起頭:`True`
- ③ 與正式 repo 互不包含(比路徑元件,非 startswith):`True`
- **結果**:已刪除:<TEMP>\mk-e2e-<本輪隨機後綴>(存在=False)

## 證據限制(**不編造訊號**)

- **非零退出碼 + HEAD 不變,本身不證明是 hook 擋下的** —— 所以每個預期拒絕都要同時滿足〈逐條判準〉裡的每一條。
- **`git trace2` 證明的是「git 啟動了 pre-commit hook」** —— 它**不**證明 hook 內部走了哪一條規則;那一層由訊息內容與帳本新增行承擔。追蹤沒看到就記 `False`,**不補一個替代訊號**。
- **#12 只有【接線】**:正式配置下 `EXEMPTION_LOG` 與舊碼自組的路徑**逐字相同**,真 hook 在任何構造下都給一樣的答案 ⇒ **無【差異】可驗**。
- **#11② 限定為**:「靜態構造一個未暫存目標時,正常 `staged_paths` 不會選到它」。**不概括成真實流程永遠不可能發生 index 讀取失敗。**
- **#8/#9 的黑箱結果可驗證來源行為**,但**不能單靠兩個案例宣稱「共用同一次讀取」** —— 那個構造性質由程式與既有測試支撐。
- 合法對照**不要求**每一案例都新增豁免帳本行或印個人清單警告 —— 正常執行可能兩者皆無。

## 執行安排

**正式驗收模式;執行者身分由本次人工執行紀錄確認。**

> ⚠ **腳本未取得執行者身分** —— **不得僅憑「沒有帶 `--smoke`」就斷言是誰跑的**。
> 要把身分寫進報告,用 `--executor <名字>`(那仍然是自述)。

**REAL 層材料的來源限制**(條文位置:`docs/agents/commander.md` §六〈只有 Jeff 能做的〉)——
REAL 層材料必須由**裁決者本人**或 **CI** 產生,**agent 自跑不算**。
來源逐字:**本輪裁決確認;裁決者轉述此要求源於 2026-09-03,本次未取得該日原始裁決文件。**
⚠ 不得把它引述成一條已查證的歷史條文。(**2026-09-24 才發現 repo 查無此條** ——`docs/agents/friction-log.md` 一處「三層驗收(UNIT / CLEAN / REAL)」、`docs/tickets/framework-updates/22-machine-recovery-drill.md:531,535`一次「REAL 層通過」,**兩處都沒有寫來源規則**。)
⚠ **人工按下按鈕不自動代表獨立設計或獨立驗收** —— 本腳本由 agent 設計與撰寫;執行者與設計者不互相背書。

## 結案

**票 133 與票 138 均不因本報告預先結案。**
票 138 的命題是「人工步驟沒有被寫下來」—— 見 `docs/agents/authority-layer-e2e.md`;
是否足夠由裁決者判定。
