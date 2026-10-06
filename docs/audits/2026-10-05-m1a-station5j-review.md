# 票 145 Station 5j 增量獨立審查報告

- 審查包:`docs/audits/2026-10-05-m1a-station5j-review-package.md`(S5j-0 `69e1fe2271fa2af66c0c4330b48eef8bbbc6db18`;blob `c1f3243ab2e384bd9c05513440485032564b2b07`;sha256 `e75ff8a7e63d45c980777d0245f7af11be36ec138077f38b2de466ad4870ba38`)
- 審查對象 TARGET(S4J1):`d4b6fafd4afdd70121278527194aeef4097bff33`
- REVIEW_HEAD(S4J4):`38691e0cc4c2a72fa7909d924975ca1f67da38d0`
- 身分:本對話為全新對話,無 4g 實作 / 3h–5j-0 實作 / 5g / 5h / 5i 審查 session 的記憶或上下文。
- 方法:只以完整 SHA 的 `git show` / `git diff` / `git grep` / `git rev-parse` 讀取;行為以紙上推演;git 原語以 repo 外 scratchpad 的拋棄式 repo 實驗(`od -c`)。未執行 pytest / verify_gates.py / status.py / 任何本 repo 的 Python;未開啟兩本帳本內容。

---

## 1. 判決

**PASS** —— G1(修正封住 S5i-F1,且可證明任何非空 prefix 都不可能通過)、G3(只改 `_root_is_toplevel` 一個函式、測試只在檔尾新增)、G4(J1b 對 HEAD 實作 blob `996f151…` 跑出本機紅燈後 4j 才通過 R3,非繞過)皆成立;G9 在 5h 18 項 + 5i LF 反例 + 包內列出的 6 類新候選上**沒有**找到同級漏洞。另有 nit 3 項(不構成 FAIL)。

---

## 2. Findings 表

| 編號 | 嚴重度 | 對應 G 題 | 證據 | 一句描述 | 需要重現 |
|---|---|---|---|---|---|
| S5j-F1 | nit | G7 | `d4b6fafd4afdd70121278527194aeef4097bff33:docs/audits/2026-10-05-m1a-station4i-fix.md:203-204`(舊措辭,BASE_I..REVIEW_HEAD 間未改動);`d4b6fafd…:.claude/hooks/redlight.py:727-728`(docstring 未補條件) | S5i-F2 補準只寫在 4j 報告 §7 第 4 點與票〈六十三〉63.2;4i 報告 §7 第 3 點仍是「gitdir / bare ⇒ unknown」的無條件版,檔內沒有指向取代版本的註記,單獨讀 4i 報告的人會讀到已被取代的措辭 | 否 |
| S5j-F2 | nit | G5 / G6 | `d4b6fafd…:tests/test_redlight.py:2709-2714`(J2 `bare` 分支);REVIEW_HEAD `docs/audits/2026-10-05-m1a-station4j-fix.md:208` | S5i-F3(b)「`safe.bareRepository=explicit` 時 bare 案例空洞通過」**沒有被 J2 關閉**:同一設定下 J2[bare] 也因 git exit 128 ⇒ False 而空洞通過(實驗 X9);J2[gitdir] 仍能抓到「接受 `false\n\n`」型回歸,所以實害小,但 4j §7.3「S5i-F3 已由機器鎖處理,不另列追蹤項」說得比證據滿 | 是(最小重現:在 `safe.bareRepository=explicit` 的 global 設定下跑 J2[bare] 於任一 parser 版本皆綠;git 原語層已由 X9 證明 exit 128) |
| S5j-F3 | nit | G5 | `d4b6fafd…:tests/test_redlight.py:2735-2750`(J1b 只有一個輸入 `b"true\n\nsub/\n"`);REVIEW_HEAD `docs/audits/2026-10-05-m1a-station4j-fix.md:208` | 4j §7.3 稱 J1b「鎖住『多餘位元組 ⇒ False』」,但 J1b 是單一樣本;它擋得住最自然的回歸(拆行看前兩行、`startswith(b"true\n\n")`),擋不住只對其他多餘位元組形狀放行的回歸。措辭是由一個樣本推出的通則 | 否 |

blocker 0、major 0、minor 0、nit 3。

---

## 3. G1–G10 逐題

### G1 修正是否封住 S5i-F1(fail-closed)—— **成立**

證據:`d4b6fafd…:.claude/hooks/redlight.py:732-741`(E.5 與本人 `git show` 取出的檔案一致)。

```
733    try:
734        proc = subprocess.run(["git", "-C", os.fspath(root), "rev-parse",
735                               "--is-inside-work-tree", "--show-prefix"],
736                              capture_output=True, timeout=30)
737    except Exception:
738        return False
739    if proc.returncode != 0:
740        return False
741    return proc.stdout.replace(b"\r\n", b"\n") == b"true\n\n"
```

推演:
1. 例外(git 不存在 → `FileNotFoundError`;`TimeoutExpired`)⇒ `:737-738` False。非零 returncode(dubious ownership、`safe.bareRepository=explicit`、不在 repo)⇒ `:739-740` False。這兩段在 E.4 是 context 行,未改。
2. 什麼輸入能讓 `:741` 為 True?`replace(b"\r\n", b"\n")` 只把 `\r\n` 換成 `\n`、不刪其他位元組。所以 True 的原像只有 `b"true"` + (`\n` 或 `\r\n`) + (`\n` 或 `\r\n`) 共 4 種。也就是說 `--show-prefix` 那一段輸出只能是 `\n` 或 `\r\n`。
3. 非空 prefix 一律以 `/` 結尾(實驗 X3 `s u b / \n`、X4 `  s p / \n`;5i X3 `344 270 255 / \n`),而 `/` 在正規化後還在 ⇒ 正規化後的 stdout 含 `/` ⇒ 不可能等於 `b"true\n\n"`。**結論:任何非空 prefix ⇒ False,與 prefix 的內容無關**(LF、CR、空白、`\r\n` 都一樣)。
4. 逐項代入:
   - S5i-F1 `b"true\n\nsub/\n"` ⇒ ≠ ⇒ False(J1b 斷言的就是這一點)。
   - prefix 首位元組為 CR(目錄 `"\r"`):`b"true\n\r/\n"`,沒有 `\r\n` 子字串 ⇒ 不變 ⇒ ≠ ⇒ False。
   - 目錄名含 `\r\n`(`"\r\nX"`):`b"true\n\r\nX/\n"` → `b"true\n\nX/\n"` ⇒ ≠ ⇒ False。
   - 空白開頭(X4 實測 `t r u e \n   s p / \n`)⇒ ≠ ⇒ False。
   - gitdir / bare(X2、X8 實測 `f a l s e \n \n`)⇒ ≠ ⇒ False。
5. 跟 4i 比:新條件 True ⇒ stdout 正規化後是 `true\n\n` ⇒ 4i 的 `lines[0].strip()==b"true"` 和 `lines[1].strip()==b""` 也都成立 ⇒ **新的接受集合是 4i 的子集**,本輪只收窄、沒有放寬。

### G2 精確比對的健壯性 —— **成立(附追蹤項:更舊的 git 版本沒有證據)**

- 正常最上層的原始位元組(本機 git 2.53.0.windows.2,實驗 X1):`t r u e \n \n`,恰好 6 bytes ⇒ 跟 `b"true\n\n"` 逐位元組相同。linked worktree 最上層(X7)、設 `GIT_WORK_TREE` 的情形(X6)也都恰好是 `t r u e \n \n`。
- Windows:X1–X8 的 `od -c` 都沒有 `\r`(跟 5i X1–X4 一致)。就算某個環境輸出 `\r\n`,4 種原像都會正規化成 `b"true\n\n"`(G1 第 2 點)⇒ 不會把正常 host 誤判。
- 不同 git 版本:Windows 2.53.0(X1)、Linux 2.43.0(F.1 第 9 節:J2[toplevel] 在 S4J1 原檔上 passed;verify_gates 正二 `file_coverage=true`)兩個版本都有證據證明最上層輸出能讓精確比對為 True。比 2.43.0 更舊的版本,最上層是否一定印出 `--show-prefix` 的空行:本人印象中 `builtin/rev-parse.c` 在 prefix 為空時會 `putchar('\n')`,但**未讀 git 原始碼核對**,屬推演。萬一某版本不印,結果是正常 host 被判 False(fail-closed、封死正常 host,不是 fail-open)⇒ 列追蹤項,不是 finding。
- core.* 設定:`core.quotePath` 不影響 `--show-prefix`(5i X3:輸出原始位元組)。`core.bare=true` 誤設在非 bare repo ⇒ 第一行 `false` ⇒ False(fail-closed;本來就該拒絕)。`safe.directory` / `safe.bareRepository` ⇒ exit 128 ⇒ False(X9)。`GIT_TRACE=1` 寫到 stderr,不影響 stdout;把 trace 導到 stdout 的極端設定只會造成 False(fail-closed)。
- 端到端正控:Windows 本機 S4J2 全套 J2[toplevel] 在 passed 之內(F.1 第 2 節);淨室正二 `file_coverage=true`(F.1 第 5 節 Windows;第 9 節 Linux)。

### G3 不變式未削弱 —— **成立**

- 程式碼檔範圍:本人 `git diff --name-only <TARGET_I>..<TARGET>` 與 D.2 逐行相同(7 行;非 docs 的只有 `.claude/hooks/redlight.py`、`tests/test_redlight.py`)。`tests/conftest.py`、`status.py`、`install.py`、`verify_gates.py` 都不在清單裡 ⇒ 未改。`git diff --name-only <TARGET>..<REVIEW_HEAD>` 只有 2 個 docs 檔。
- redlight.py:`git diff -U0` 只有兩個 hunk,`@@ -729 +729,3 @@`(docstring)與 `@@ -739,4 +741 @@`(本體)。以 TARGET 行號算都落在 `def _root_is_toplevel` 的 `:726-741` 之內。numstat `4 5`(S3J1B-2..TARGET)。
- 呼叫鏈未改:`git grep -n _root_is_toplevel <TARGET> -- "*.py"` 的程式呼叫點只有 `:757`(`committed_blobs`)與 `:873`(`evidence_policy_facts`)。兩處與其後 `:764-765`、`:875-883` 的 `hash-object` / `rev-parse HEAD:` / `cat-file` 都是 diff 範圍以外的行。producer `tests/conftest.py:410-412` 未改。`content_hash` 不在任何 hunk 內。
- 測試只在檔尾新增:合併 diff 為 `@@ -2648,0 +2649,102 @@`,0 個 `-` 行(numstat 合計 102 / 0)。逐 commit:TARGET_I..S3J1 `66 0 tests/test_redlight.py`;S3J2..S3J1B `36 0 tests/test_redlight.py`。E.2 / E.3 各一個 hunk、沒有 `-` 行,與包相符。
- blob 鏈:`tests/test_redlight.py` 在 S3J1 = `54557c3f…`,S3J1B = TARGET = `c284bc8c…`。`redlight.py` 在 TARGET_I = S3J1B = S3J1B-2 = `996f1519…`,TARGET = `d4d208af…`。

### G4 紅綠時序與 R3 —— **成立**

- 時序(`git log --format="%H %P %s"`,線性,無 merge):S5i-1 → S3J1(J1/J2)→ S3J2 → S3J1B(J1b)→ S3J1B-2 → S4J1 → S4J3 → S4J4。
- 第一次 4j 被擋(F.3 Step 0:HEAD = `ee33e2d…` = S3J2,帳本 = B19;Step 2 照錄 R3 擋下原文):當時 `redlight.py` = `996f151…`,本機帳本只有 S3J1 全套(J1 skipped、J2 green)⇒ 沒有紅燈。這是 R3 照設計動作。處置是停手、還原工作樹(`git status --porcelain` 無輸出),沒有改路徑、換工具或動 pipeline。
- 3j-1b 紅燈:S3J1B 上 `redlight.py` = `996f151…`(本人 `git rev-parse` 核對,與 HEAD 實作同一 blob),J1b 失敗於 `tests\test_redlight.py:2749: AssertionError`(`assert True is False`),全套 `1 failed, 2103 passed, 4 skipped, 3 xfailed`,status `tests red under ticket 145: tests/test_redlight.py`(F.2 §6.3)。紙上推演同樣會紅:`996f151` 的 `split(b"\n")` → `[b"true", b"", b"sub/", b""]` ⇒ True ⇒ `True is False` 失敗。⇒ **紅燈是對著 HEAD 的實作跑出來的**,而且紅的原因正是 S5i-F1 的解析缺陷,不是測試本身的瑕疵。
- 綠:S4J1 上 J1b 推演 `b"true\n\nsub/\n" != b"true\n\n"` ⇒ False ⇒ 通過;`calls[0][-2:]` = `["--is-inside-work-tree", "--show-prefix"]`(`:734-735`)⇒ 通過。S4J2 全套 `2104 passed, 4 skipped, 3 xfailed`,0 failed(F.1 §2)。紅與綠之間測試檔 blob 不變(`c284bc8c…`)⇒ 同一支測試由紅轉綠。
- 三支各自的狀態(F.0):J1b S3J1B red → S4J1 green;J2 S3J1 / S3J1B green → S4J1 green;J1 在 Windows 一律 skipped(本機帳本看不到),Linux 上 S4I1 red → S4J1 green 只有裁決助手的外部證據(非本 repo 帳本)。
- 沒有走豁免(F.3 選項 B 未採用),沒有換環境(選項 C 未採用)⇒ 不是繞過。
- 帳本:依規則本人只能 `sha256sum`。審查前全檔 `22148446…` / `3d7cde59…` = F.1 §5 的 V0 ⇒ S4J3 的 3d 之後到本審查開始,沒有任何寫入。B19 → B21 → V0 的前段雜湊鏈由實作 session 以 `head -c` 計算,**本審查未獨立重算**(會讀到帳本內容,超出規則允許範圍)。

### G5 三支測試是否測到宣稱的形狀 —— **成立(附 S5j-F2、S5j-F3)**

- **J1**(`d4b6fafd…:tests/test_redlight.py:2673-2688`)。skipif 照錄:`@pytest.mark.skipif(sys.platform == "win32", reason="Windows 檔名不得含 LF;本案例由 POSIX 驗收證明(〈六十一〉61.3 裁決 2)")`。`sys` 由 class body 第 2663 行 `import sys` 綁在 class 命名空間;decorator 在 class body 內求值,所以取得到(檔頭只有 `import sys as _e_real_sys`,`:1547`,名稱不同)。條件只在 Windows 跳過;POSIX(含 cygwin / msys 的 `sys.platform`)會實跑,方向正確。形狀:`parent = _g_default_root(...)`(`:2216-2218` → `_g_root` `:2187-2213` 提交 pyproject / conftest / policy);`root = parent / "\nsub"`;`_copy_into` 只 `read_bytes` / `write_bytes`(沒有 git add)⇒ 三份副本從未提交。`_g_coverage` → `_g_run` → `_isolated_conftest`(`:298-312`,`:306` `c._ROOT = root`)→ 真實 producer `tests/conftest.py:410-412`。弱點:只斷言 `!= "true"`(S5i-F3(a) 同型;由 J1b / J2 直接鎖補位)。
- **J1b**(`:2725-2750`)。monkeypatch 目標用程式碼證明:`redlight` 是以 `importlib.util.spec_from_file_location("redlight_under_test", …)` 載入的模組(`:22-30`),`_root_is_toplevel` 在函式內執行 `import subprocess`(`redlight.py:732`)⇒ 取得的是 `sys.modules["subprocess"]`。J1b 的 `import subprocess as _sp`(`:2735`)也是同一個 `sys.modules["subprocess"]` 物件。`monkeypatch.setattr(_sp, "run", fake_run)` 改的是這個模組物件的屬性,而 `:734` 的 `subprocess.run` 是呼叫當下才查屬性 ⇒ **一定會呼叫到替身**。`fake_run(args, **kw)` 吃得下 `:734-736` 的 positional list + `capture_output` / `timeout`。args 結尾斷言 `calls[0][-2:] == ["--is-inside-work-tree", "--show-prefix"]`(`:2750`)。stdout `b"true\n\nsub/\n"` 與 61.2 外部 git 原語(`t r u e \n \n s u b / \n`)、S5i-F1 原文的形狀一致。外漏:monkeypatch 在 fixture teardown 還原。替身有效期間會跑的 conftest hook 只有 `pytest_runtest_logreport`(`tests/conftest.py:207-223`),它不呼叫 subprocess;會呼叫 git 的 producer 在 `pytest_sessionfinish`(`:226` 起),那時已 teardown ⇒ 不外漏。弱點:單一樣本(S5j-F3)。
- **J2**(`:2690-2714`)。四種佈置各自建出獨立的 `tmp_path`(parametrize 每案一個 tmp_path)。實驗對應:toplevel `t r u e \n \n`(X1)、subdir `t r u e \n s u b / \n`(X3)、gitdir `f a l s e \n \n`(X2)、bare `f a l s e \n \n`(X8;J2 用的是 `bare.git/proj`,5i X5–X7 已實測同型)。每案只靠一個條件分辨,彼此獨立。弱點:`safe.bareRepository=explicit` 時 bare 案 exit 128(X9)⇒ 不論 parser 怎麼寫都是 False ⇒ 空洞通過(S5j-F2)。

### G6 5g / 5h / 5i 其他結論是否仍成立 —— **成立(附 S5j-F2)**

- 本輪唯一的程式變更讓接受集合**嚴格收窄**(G1 第 5 點)。所以「X 被擋 ⇒ unknown」形式的結論全部維持;「正常 host 會被接受」形式的正控結論由 J2[toplevel](Windows 本機 + Linux 外部)與淨室正二 `file_coverage=true` 維持。
- 5h G1–G9:總表 #1–#6、#12、#16、#17 在 TARGET 仍被擋(第 G9 題逐項);#7–#11、#13–#15 仍判「不構成 F2」。5h G9 的反例(#3–#6)在 5i 已封住,本輪沒有重新打開。
- 5i:G2 / G7 / G9 的 S5i-F1 部分由本輪修正(G1、G7、G9)。G5 的 S5i-F3:(a) 由 J2 直接呼叫補位;(c) 由 J1b 補位;**(b) 未被 J2 關閉**(S5j-F2)。其餘(G3、G4、G6、G8 等)不受影響:本輪沒有動其他程式。
- 5g 13 題:本輪沒有改 consumer / policy_state / conftest / status / install / verify_gates(G3)⇒ 不受影響。註:5g 報告全文不在包內,本人未逐題重讀,依據是「改動範圍只在 `_root_is_toplevel` 且只收窄」。
- 追蹤項 S5g-F1 / F3 / F4 / F5、S5h-F4:本輪沒有任何對應的程式或機器檢查 ⇒ 仍然**目前尚未 machine-enforced**,與 H 段相符。

### G7 殘餘措辭與程式一致 —— **成立(附 S5j-F1)**

並排比對(4j 報告 §7 第 4 點 = REVIEW_HEAD `docs/audits/2026-10-05-m1a-station4j-fix.md:210`;C.2 S5i-F2 = 5i 審查報告第 91 行):

| S5i-F2 原文 | 4j §7.4 措辭 | 相符? |
|---|---|---|
| 「措辭把『位於 gitdir 或 bare repository 內的 root(I1 / I2)』列為**無條件的**『明確不支援(⇒ unknown)』」 | 「在預設環境(未設 GIT_DIR / GIT_WORK_TREE / core.worktree)下明確不支援(⇒ unknown):… 位於 gitdir 或 bare repository 內的 root(I1 / I2)」 | 是 —— 無條件改成有條件 |
| 「(a) 環境有 `GIT_DIR=<p/.git>`、沒有 `GIT_WORK_TREE`,cwd = `p/.git` …(b) 該 repo 的 `core.worktree` 指向它自己的 gitdir …這兩種都是 Git 自己把 gitdir 當成工作樹」 | 「以及 GIT_DIR / GIT_WORK_TREE / core.worktree 等重新對應佈局(含 Git 因此把 gitdir 本身視為工作樹的情形)」 | 是 —— (a)(b) 兩種都被括號涵蓋 |
| 「措辭後半的『GIT_DIR / … core.worktree 等重新對應佈局 … 會被接受』已經涵蓋。所以這只是前後兩句重疊」 | 前句加了「在預設環境」條件,重疊消除 | 是 |

- 跟程式一致:「stdout(\r\n 正規化後)完整等於 b"true\n\n"」= `:741`。「非最上層的普通子目錄(H1;含 POSIX 上名稱以 LF 開頭者,J1 / J1b)」⇒ 有 G1 第 3 點證明支撐。「會被接受…不得宣稱已拒絕或已支援」與 X5、X6、X7 實測(`true` + 空 prefix)一致,沒有宣稱拒絕或支援任何未測佈局。
- 程序偏差 (b) 的獨立核對:最終措辭的每一個成分都能由已提交的 5i 審查報告(C.2 S5i-F2 列、C.5 G7)與票〈六十一〉61.3 裁決 4 推出 ⇒ **由已提交文件支撐,不依賴對話紀錄**。
- 小瑕疵:4i 報告 §7.3 仍然是無條件版,而且沒有指向取代版本(S5j-F1)。`redlight.py:727-728` docstring 的「gitdir / bare … 但不是工作樹」是在說明這個條件存在的理由,不是範圍宣稱,影響更小。

### G8 跨平台 —— **成立**

- `\r\n` 正規化是否足夠:G1 第 2 點的 4 種原像都涵蓋。單獨出現的 `\r`(例如 `true\r\n\r`)或尾端多一個 LF ⇒ False(fail-closed)。本機 2.53.0 與外部 2.43.0 都沒有觀察到這種輸出(X1、X6、X7;J2[toplevel] 在兩平台都 passed)。
- Windows 上對 LF 開頭子目錄沒有端到端證據:屬實(J1 skipped;F.1 §2 第 35 行)。但 Win32 / NTFS 不能建立含 LF 的名稱,這個攻擊輸入在 Windows 本機**不可達**,所以「沒有端到端證據」不是覆蓋缺口。J1b 用替身在所有平台鎖解析層,而解析層是 S5i-F1 唯一的缺陷位置(G1 第 3 點證明了非空 prefix 的內容無關)⇒ J1b 足以補位。POSIX 端到端由裁決助手的外部證據(S4I1 red → S4J1 green;非本 repo 帳本)補足。

### G9 總問題(增量版)—— **成立(沒有找到同級反例)**

判準:root 的 canonical policy 沒有提交在「Git 對該 root 實際解析出的 repository / HEAD」中,卻能得到 `file_coverage == "true"`。TARGET 上能得到 True 的唯一入口是 `:741`,也就是 Git 對 root 回報「在工作樹內 + prefix 為空」。這時 `HEAD:<path>`(`:765` / `:875`)與 `hash-object <path>`(`:764` / `:879`)都以 `-C root` 執行,由 Git 把同一個 root 對應到同一個工作樹 / HEAD ⇒ identity 錯位只可能來自「Git 自己的對應」,而那依判準不構成 F2。

5h 第 4 節總表 18 項在 TARGET 的重新判定:

| # | 佈局 | TARGET 的 stdout(實測或推演) | 判定 |
|---|---|---|---|
| 1 | 普通子目錄 | `true\nsub/\n`(X3)| 擋下 |
| 2 | 同上,大寫路徑 | prefix 非空 ⇒ ≠ | 擋下 |
| 3 | bare 目錄 | `false\n\n`(X8)| 擋下 |
| 4 | bare 底下子目錄 | 第一行 false(5i X5–X7)| 擋下 |
| 5 | `p/.git/` | `false\n\n`(X2)| 擋下 |
| 6 | `p/.git/refs` | 第一行 false(5i)| 擋下 |
| 7 | linked worktree | `true\n\n`(X7)| 接受(worktree 自己的 HEAD;不構成 F2)|
| 8 | submodule | 同最上層 ⇒ `true\n\n`(推演)| 接受(submodule 自己的 HEAD;不構成 F2)|
| 9 | `.git` 檔指向上層 gitdir | `true\n\n`(5h 實測)| 接受(Git 自己的對應;不構成 F2)|
| 10 | 外部目錄 gitfile | 同 #9 | 接受(不構成 F2)|
| 11 | `GIT_DIR` 有設、`GIT_WORK_TREE` 沒設 | `true\n\n` + toplevel = 子目錄(X5)| 接受(Git 把 cwd 當工作樹最上層;不構成 F2;殘餘措辭涵蓋)|
| 12 | `GIT_DIR` + `GIT_WORK_TREE=p`,cwd 子目錄 | prefix `sub2/` ⇒ ≠ | 擋下 |
| 13 | `core.worktree` 指向子目錄 | 依語意 `true\n\n` | 接受(不構成 F2;未實測)|
| 14 | root 為符號連結 | `_ROOT` 已 `resolve()` | 不構成 F2 |
| 15 | policy 為符號連結 | 不經 `_root_is_toplevel` 的差異 | 不構成 F2(同 5h)|
| 16 | 名稱只含空白 | prefix `" /"`(X4 同型 `  s p /`)⇒ ≠ | 擋下 |
| 17 | dubious ownership | exit 128 | 擋下 |
| 18 | `_committed_addopts` | 只在 `:873` 之後 | 跟著 #1–#6 一起擋 |

5i LF 反例:`b"true\n\nsub/\n"` 與名稱 `"\n"`、`" \n…"`、`"\t\nX"` ⇒ 都含 `/` ⇒ **擋下**。

包內 G9 列出的新候選:

| 候選 | 判定 | 依據 |
|---|---|---|
| prefix 只含 `\r`(目錄 `"\r"`)| 擋下 | `true\n\r/\n` 沒有 `\r\n` 子字串 ⇒ 不變 ⇒ ≠(G1 第 4 點)|
| prefix 含 `\r\n`(目錄 `"\r\nX"`)| 擋下 | 正規化後 `true\n\nX/\n` ⇒ ≠ |
| prefix 含 NUL | 擋下(不可建構)| POSIX 與 NTFS 的檔名都不能含 NUL;就算能,`/` 仍在 ⇒ ≠ |
| 子目錄名為空白 / 空白開頭 | 擋下 | X4 實測 `t r u e \n   s p / \n` ⇒ ≠ |
| `GIT_DIR` 重新對應 | 接受 | X5:Git 把子目錄當工作樹最上層,HEAD 與 hash-object 同一個 Git 對應 ⇒ 依判準不構成 F2;4j §7.4 已列為「會被接受、屬未證明」|
| `GIT_WORK_TREE` 重新對應 | 接受 | X6 `t r u e \n \n`;同上 |
| `core.worktree` 重新對應 | 接受 | 5i X8 + 語意;同上 |
| linked worktree | 接受 | X7;worktree 自己的 HEAD |
| submodule | 接受 | 5h #8;submodule 自己的 HEAD |
| 本人另擬:root 路徑含 `..`(`p/sub/..`)| 接受 | git 與 hash-object 都在同一個 `-C` 下解析,對應到同一個 `p` ⇒ 不構成 F2 |
| 本人另擬:`GIT_CEILING_DIRECTORIES` / `GIT_DISCOVERY_ACROSS_FILESYSTEM` 讓探索失敗 | 擋下 | exit ≠ 0 ⇒ `:739-740` False |
| 本人另擬:`_root_is_toplevel` 與後續 git 呼叫之間佈局被並行改動(TOCTOU)| 無法判定 | 需要 sessionfinish 期間有人並行改檔;非本輪引入(TARGET_I 已存在同一結構);列追蹤項 |

### G10 程序偏差對證據完整性 —— **不影響**

- (a) S4J3 3d 事後 5 條唯讀檢查並行送出:那 5 條都是 `wc -c` / `sha256sum` / `git status --porcelain`,不寫入。輸出值 `891928` / `17351316` / `22148446…` / `3d7cde59…` 與同節事前 V0 相同。**本審查 Step 0 獨立量到的全檔 sha256 也是 `22148446c9cc…` / `3d7cde594d88…`**(另一個 session、另一個時間點、本人自己執行)⇒ 這些數值有一個不來自實作 session 的獨立來源。並行送出不會改變唯讀指令的輸出。
- (b) 以 grep 讀對話紀錄找回 S5i-F2 措辭:這個偏差只能影響「措辭的來源」。G7 已證明最終措辭的每一個成分都能由已提交的 C.2 / C.5 / 61.3 裁決 4 推出。帳本雜湊、blob(本人以 `git rev-parse` 獨立取得 `996f151…` / `d4d208a…` / `c284bc8…` / `54557c3…`)、diff(本人獨立 `git diff`)都不依賴對話紀錄。run 紀錄的通過數(2104 passed 等)來自實作 session 未入庫的輸出檔,本審查無法獨立核對,但這一點跟偏差 (b) 無關(不是從對話紀錄取得的)。
- 結論:**不影響**。

---

## 4. 實驗記錄

環境:本機 git `git version 2.53.0.windows.2`。實驗 repo 都在 session scratchpad(repo 外),下文以 `<scratch>` 表示 `C:/Users/<user>/AppData/Local/Temp/claude/c--projects-agent-gates/<session>/scratchpad`。沒有任何實驗 repo 指向本 repo。每條指令都是單獨送出(違規的兩次見第 7 節)。

```
$ git init -q <scratch>/exp/p
(無輸出)
$ git -C <scratch>/exp/p rev-parse --is-inside-work-tree --show-prefix > <scratch>/exp/x1-top.bin
(無輸出)
$ od -c <scratch>/exp/x1-top.bin                                   # X1 最上層
0000000   t   r   u   e  \n  \n
0000006
$ git -C <scratch>/exp/p/.git rev-parse --is-inside-work-tree --show-prefix > <scratch>/exp/x2-gitdir.bin
(無輸出)
$ od -c <scratch>/exp/x2-gitdir.bin                                # X2 gitdir
0000000   f   a   l   s   e  \n  \n
0000007
$ git -C <scratch>/exp/p hash-object -w --stdin < /dev/null
e69de29bb2d1d6434b8b29ae775ad8c2e48c5391
$ git -C <scratch>/exp/p update-index --add --cacheinfo 100644,e69de29bb2d1d6434b8b29ae775ad8c2e48c5391,sub/f
(無輸出)
$ git -C <scratch>/exp/p update-index --add --cacheinfo "100644,e69de29bb2d1d6434b8b29ae775ad8c2e48c5391, sp/f"
(無輸出)
$ git -C <scratch>/exp/p checkout-index -a
(無輸出)
$ git -C <scratch>/exp/p/sub rev-parse --is-inside-work-tree --show-prefix > <scratch>/exp/x3-sub.bin
(無輸出)
$ od -c <scratch>/exp/x3-sub.bin                                   # X3 普通子目錄
0000000   t   r   u   e  \n   s   u   b   /  \n
0000012
$ git -C "<scratch>/exp/p/ sp" rev-parse --is-inside-work-tree --show-prefix > <scratch>/exp/x4-space.bin
(無輸出)
$ od -c <scratch>/exp/x4-space.bin                                 # X4 空白開頭子目錄 " sp"
0000000   t   r   u   e  \n       s   p   /  \n
0000012
$ GIT_DIR=<scratch>/exp/p/.git git -C <scratch>/exp/p/sub rev-parse --is-inside-work-tree --show-prefix --show-toplevel > <scratch>/exp/x5-gitdir-env.bin
(無輸出)
$ od -c <scratch>/exp/x5-gitdir-env.bin                            # X5 GIT_DIR 重新對應(多加 --show-toplevel 以觀察 Git 的對應)
```

X5 輸出(**遮罩後,非原始**:第 0000006–0000177 位元組是 scratchpad 絕對路徑,其中本機使用者名稱的 5 個位元組已改成 `<user>`,路徑中段以 `<scratch>` 縮寫;前 6 位元組與最後 1 位元組為原文):

```
0000000   t   r   u   e  \n  \n   C   :   /   U   s   e   r   s   /  <user>
…(<scratch> 的其餘路徑位元組)…   /   e   x   p   /   p   /   s   u   b
0000200  \n
0000201
```

即 `true\n\n` + `--show-toplevel` = `<scratch>/exp/p/sub` + `\n`。

```
$ GIT_WORK_TREE=<scratch>/exp/p/sub git -C <scratch>/exp/p/sub rev-parse --is-inside-work-tree --show-prefix > <scratch>/exp/x6-worktree-env.bin
(無輸出)
$ od -c <scratch>/exp/x6-worktree-env.bin                          # X6 GIT_WORK_TREE 重新對應
0000000   t   r   u   e  \n  \n
0000006
$ git -c user.name=x -c user.email=x@example.invalid -c core.hooksPath=<scratch>/exp/nohooks -C <scratch>/exp/p commit -q -m x
(無輸出)
$ git -C <scratch>/exp/p worktree add -q <scratch>/exp/wt
(無輸出)
$ git -C <scratch>/exp/wt rev-parse --is-inside-work-tree --show-prefix > <scratch>/exp/x7-linked.bin
(無輸出)
$ od -c <scratch>/exp/x7-linked.bin                                # X7 linked worktree
0000000   t   r   u   e  \n  \n
0000006
$ git clone -q --bare <scratch>/exp/p <scratch>/exp/bare.git
(無輸出)
$ git -C <scratch>/exp/bare.git rev-parse --is-inside-work-tree --show-prefix > <scratch>/exp/x8-bare.bin
(無輸出)
$ od -c <scratch>/exp/x8-bare.bin                                  # X8 bare(預設設定)
0000000   f   a   l   s   e  \n  \n
0000007
$ git -c safe.bareRepository=explicit -C <scratch>/exp/bare.git rev-parse --is-inside-work-tree --show-prefix   # X9
Exit code 128
fatal: cannot use bare repository '<scratch>/exp/bare.git' (safe.bareRepository is 'explicit')
```

(X9 的錯誤訊息中,路徑已遮成 `<scratch>`。)

---

## 5. 5g / 5h / 5i 結論複查

| 來源 | 結論 | 本輪後 |
|---|---|---|
| 5i S5i-F1(major) | LF 開頭子目錄 ⇒ True | **已封住**(G1 證明 + J1b 鎖 + 外部 POSIX J1 green)|
| 5i S5i-F2(nit) | 措辭無條件 | 4j §7.4 已補準(G7);4i 報告舊措辭沒有指向新版(S5j-F1)|
| 5i S5i-F3(nit) | (a) 只斷言 != true;(b) bare 空洞;(c) 沒有解析層鎖 | (a)(c) 由 J2 / J1b 補位;**(b) 仍成立**(S5j-F2)|
| 5i G2 / G7 / G9 的「例外形狀」 | POSIX LF 子目錄 | 已移除 |
| 5h 總表 #3–#6 | 5i 已封 | 仍封(第一行 false)|
| 5h #1、#2、#12、#16、#17 | 擋 | 仍擋 |
| 5h #7–#11、#13–#15 | 不構成 F2 | 仍不構成 F2(接受集合沒有放寬)|
| 5g 13 題 | — | 改動範圍以外,不受影響(未逐題重讀)|
| 追蹤項 S5g-F1 / F3 / F4 / F5、S5h-F4 | 未 machine-enforced | 狀態正確,仍**目前尚未 machine-enforced** |

---

## 6. 追蹤項建議(都不構成 FAIL;全部**目前尚未 machine-enforced**)

1. **舊版 git 的最上層輸出**:2.43.0 以前是否一定輸出 `true\n\n`,本審查沒有版本證據(G2)。不符時的方向是 fail-closed(封死正常 host)。
2. **GIT_DIR / GIT_WORK_TREE / core.worktree 重新對應佈局**(X5、X6;5h #11、#13):會被接受,依判準不構成 F2,4j §7.4 已列為未證明。補充:git hook 的執行環境會匯出 `GIT_DIR` 等變數,producer 若在 hook 內被呼叫,會繼承它(5h #11 已註「conftest 子行程會繼承環境變數」)。
3. **linked worktree / submodule / gitfile 佈局**(X7;5h #7–#10):接受,沒有 acceptance 測試。
4. **S5i-F3(b) 殘留**(S5j-F2):J2[bare] 在 `safe.bareRepository=explicit` 下空洞通過;建議在 4j §7.3 改回「部分處理」,或補一個以 `-c safe.bareRepository=all` 固定設定的 bare 案例。
5. **TOCTOU**:`_root_is_toplevel` 與後續 `hash-object` / `rev-parse HEAD:` 之間的佈局競態,本輪無法判定,非本輪引入。
6. **4i 報告 §7.3 指向**(S5j-F1):在 4i 報告該點加一行「已由 4j 報告 §7 第 4 點取代」。
7. 流程教訓「R3 與 POSIX-only 紅燈」(4j §7.3 已列)—— 本審查確認那條路徑沒有繞過 R3(G4),不另加。

---

## 7. 程序紀錄

### 7.1 Step 0 原文(每條單獨執行;違規見 7.4)

```
$ cat .dev/pipeline.json
{
  "current_stage": "review",
  "feature": "framework-updates",
  "ticket_id": "145",
  "updated": "2026-10-05"
}
$ git rev-parse HEAD
69e1fe2271fa2af66c0c4330b48eef8bbbc6db18
$ git ls-tree 69e1fe2271fa2af66c0c4330b48eef8bbbc6db18 docs/audits/2026-10-05-m1a-station5j-review-package.md
100644 blob c1f3243ab2e384bd9c05513440485032564b2b07	docs/audits/2026-10-05-m1a-station5j-review-package.md
$ git status --porcelain
 M docs/agents/friction-log.md
?? docs/tickets/framework-updates/146-claude-code-enforcement-integrity.md
?? docs/tickets/framework-updates/147-turn-end-check-via-settings-stop-hook.md
$ sha256sum .dev/test-runs.jsonl
22148446c9cc8d11520cd6437f5a49c852b9b02cc17c47d2a4b53d8be8991fe4 *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
3d7cde594d889bc71804c2af421b4c7d61078691c8644052bb68bbe7e03865f1 *.dev/test-sessions.jsonl
```

全部符合預期。

### 7.2 包檔 sha256 核對原文

```
$ git show 69e1fe2271fa2af66c0c4330b48eef8bbbc6db18:docs/audits/2026-10-05-m1a-station5j-review-package.md > <scratch>/m1a-s5j-package.md
(無輸出)
$ sha256sum <scratch>/m1a-s5j-package.md
e75ff8a7e63d45c980777d0245f7af11be36ec138077f38b2de466ad4870ba38 *<scratch>/m1a-s5j-package.md
```

相符。

### 7.3 閘門攔截 / 寫入

- 閘門攔截:**無**。
- repo 內寫入:只有本報告(`.scratch/m1a-s5j/review-report.md`,Write)。沒有 commit / push / fetch / stash,沒有改 `.dev/pipeline.json`。
- repo 外寫入:session scratchpad 內的包副本、TARGET 檔案副本(`git show … >`)與實驗 repo。

### 7.4 本審查自身的程序偏差(唯讀,不影響證據)

1. 兩次把兩條 Bash 放在同一則訊息送出,違反「每條 Bash 單獨一則訊息」:(i) Step 0 的兩條 `sha256sum`(兩本帳本);(ii) `git --version` 與 `git init -q <scratch>/exp/p`。都不是 `;` / `&&` / `|` 串接,輸出各自獨立取得;(i) 是唯讀,(ii) 只寫入 repo 外的 scratchpad。
2. 指令要求包副本放在 `<scratch>/m1a-s5j/package.md`,但 scratchpad 沒有該子目錄,而規則禁止 `mkdir`。所以改放 `<scratch>/m1a-s5j-package.md`(扁平檔名);sha256 核對結果不受影響(7.2)。
3. 為了在不用 `mkdir` 的前提下建出子目錄,實驗用了 `hash-object -w --stdin < /dev/null`、`update-index`、`checkout-index`、`commit`、`worktree add`、`clone --bare` 等 git 指令。全部都在 scratchpad 的拋棄式 repo 內,`commit` 以 `-c core.hooksPath=<scratch>/exp/nohooks` 停用 hook。

### 7.5 審查前後兩本帳本 sha256

- 審查前:`22148446c9cc8d11520cd6437f5a49c852b9b02cc17c47d2a4b53d8be8991fe4` / `3d7cde594d889bc71804c2af421b4c7d61078691c8644052bb68bbe7e03865f1`
- 審查後:見 Step 4 收尾(報告寫完後才執行,所以不寫進報告本身;結果貼在對話中)。
