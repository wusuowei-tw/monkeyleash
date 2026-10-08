本檔為 .dev/reports/2026-10-08T002223Z-ticket148-s5-1-independent-review.md 的遮罩複本；遮罩差異見票 148〈第五站獨立審查〉。
# 票 148 第五站獨立審查(S5-148-1)

- 報告時間(UTC):2026-10-08T002223Z
- 審查對象 HEAD:`acf5523690203482cce3760a6943965d1ae548c3`
- 審查者身分:全新視窗;本 session 未參與票 148 的 R0～S5-0 任何一輪
- 授權:Jeff 裁決(2026-10-07 19:56 美東,逐字):「進第五站。先產審查包，再由全新視窗獨立審查；站別只改 `current_stage` 為 `review`，保留 ticket 148 與其他欄位。審查包須分清正式 pytest 對應的 code commit、後續 docs commit，以及外部 Linux 預演。重點核對 rename 目的檔確實進入 R2／leak scan、純刪除處置不變、#5 未改的限制。目前仍不 push。」
- 遮罩:絕對路徑 → `<path>` / `<scratchpad>`;使用者名 → `<使用者>`;帳號 / 信箱 → `<id>`

---

## 第一段【給裁決者】

1. **結論:PASS-with-notes。阻擋項 0。** 正式全套在 `acf5523` 重跑:2340 passed、10 skipped、3 xfailed、0 failed。兩本帳本只有追加。
2. **最重要的發現**:突變探針(故意把修正拿掉,看測試會不會轉紅)兩次都**精準命中**。拿掉 gate 側的修正,只有 gate 那 4 個 node 轉紅;拿掉 scanner 側的修正,只有 scanner／leak scan 那 4 個轉紅。也就是說,rename 目的檔進 R2、進 leak scan,兩件事各有測試獨立守著。
3. 純刪除與 rename 來源的處理和修正前一樣;#5(e2e 腳本)沒改。目前 e2e 沒有 rename 情境,所以沒有現成的誤判,但哪天新增 rename 案例,它的證據清單會是空的。
4. 附帶的行為變化(讀碼推論):原本「單純改名」完全不受檢,現在會照新增檔完整檢查(R3 要求有對應測試檔、leak scan 掃全檔),下游可能因此出現新的擋下。這符合裁決「按新增檔進入檢查」,但沒有測試鎖住,也還沒對外說明。
5. **要你決定**:#5 與第 4 點要不要另外開票(建議:開一張低優先票,兩件一起記)。不決定的話,兩件只留在本報告裡(ignored,不進版控)。本結論不等於推送授權。

---

## 第二段【給裁決助手】

### §0 步驟 0(唯讀)

```
$ pwd
<path>
$ git rev-parse HEAD
acf5523690203482cce3760a6943965d1ae548c3
$ git status --porcelain
(無輸出)
$ cat .dev/pipeline.json
{
  "current_stage": "review",
  "feature": "framework-updates",
  "ticket_id": "148",
  "updated": "2026-10-07"
}
$ wc -c .dev/test-runs.jsonl .dev/test-sessions.jsonl
 1210891 .dev/test-runs.jsonl
37662732 .dev/test-sessions.jsonl
38873623 total
$ sha256sum .dev/test-runs.jsonl .dev/test-sessions.jsonl
6a0a01a45df181e56c5752f52159c0e339b536a68457d5d2c3cfa8a55879b962 *.dev/test-runs.jsonl
0d38e3d86ddb1c2773ff4c69839476b87857c43211d82617a2a562878c05b71f *.dev/test-sessions.jsonl
```

- 五項全部符合預期。
- LC:runs 1210891 bytes,sessions 37662732 bytes。
- 這兩個值也和 S4 審計 §7 的「現長 / 現整檔 sha256」逐字相同,所以帳本鏈從 S3 → S4 → 本輪是連續的(S3 結尾 `6f10bda5…` = S4 起點)。

### §1 讀過的契約與實作

- 票 148 全文(224 行),含〈Jeff 裁決〉16:37 / 16:50、〈第四站實作〉19:27
- S3 審計、S4 審計、審查包全文
- R0 報告 `2026-10-07T203056Z-ticket148-r0-inventory.md` 全文
- `git show 9efca02d1508d828862cb4cb8afe699e4b60601a` 全文
- `gate.py`:`staged_paths` :3996-4041、`mode_pre_commit` :4148-4200、`check()` R2/commit :2855-2900
- `scanner.py` `staged_paths` :469-525;`leak_scan.py` :300-350(`--staged`)、:33-34(`sys.path.insert` + `import scanner`)
- 測試:`tests/test_gate.py` :7308-7495(T148 全部)、:6584-6662(`TestTicket146Integration` 的 `_root` / `_load` / `_wire` / `_run`);`tests/test_scanner.py` :1054-1107;`tests/test_leak_scan.py` :1128-1214;`tests/conftest.py` :130(`_ROOT = Path(__file__).resolve().parents[1]`)
- `.githooks/pre-commit` 全文:`leak_scan.py --staged || exit 1`,接著 `exec python gate.py --pre-commit`

**各測試的隔離方式(讀碼)**

- 三檔的 T148 helper 都用 `monkeypatch.setenv` 設:`GIT_CONFIG_GLOBAL`(指向 tmp 空檔)、`GIT_CONFIG_NOSYSTEM=1`、`HOME`、`USERPROFILE`(都指向 tmp)。
  - 位置:`_t148_env` test_gate :7320、`_t148_mv_repo` test_scanner :1067、`_t148_repo` test_leak_scan :1154。
- `diff.renames` 只寫在 tmp repo 的 local config。
- T148-7 / 7c 的 `_run`(:7461)不呼叫 `_wire`,自己停掉 R10 以外的鄰居。名單:`upstream_shadow_violation`、`check_third_axis_mount`、`check_to_spec_override`、`check_legacy_list`、`check_friction_numbers`、`check_skill_copies`、`shadow_active`。
  - **沒有停 `staged_paths`**。對照:`_wire` 在 :6636 會把它換成 `[]`。
  - 另外斷言 `expanduser("~")` 等於 tmp home,且 `_extension_claude_root()` 是 None。

**指紋與 diff(實測)**

```
$ sha256sum tests/test_gate.py tests/test_scanner.py tests/test_leak_scan.py
1df7320a9c9a8acee177572cf215d3dee9bb3a35474044b56346e4730b2f7614 *tests/test_gate.py
c41833b4795ad0389c716a0856a1a84d388dab10fdf376fd99ebe6098f7926e7 *tests/test_scanner.py
a665916bf87c09c8da054351e5198516add3261d049c8e7246723bc3b8daa985 *tests/test_leak_scan.py
```

- 與 S3 審計 §9 的 T0 指紋逐字相同。

```
$ git diff --stat aeb4d51 acf5523 -- tests .claude scripts .agents .githooks
 .claude/hooks/gate.py       | 6 +++++-
 .claude/portable/scanner.py | 6 +++++-
 2 files changed, 10 insertions(+), 2 deletions(-)

$ git diff --stat 96fc8b9 9efca02
 .claude/hooks/gate.py                              |  6 ++-
 .claude/portable/scanner.py                        |  6 ++-
 .dev/gate-exemptions.jsonl                         |  2 +
 .../148-staged-list-misses-renames.md              | 48 +++++++++++++++++++++-
 4 files changed, 59 insertions(+), 3 deletions(-)

$ git diff --stat 9efca02 acf5523
 .dev/gate-exemptions.jsonl                         |   1 +
 .../2026-10-07-148-station4-implementation.md      | 216 +++++++++++++++++++++
 .../2026-10-07-148-station5-review-package.md      | 213 ++++++++++++++++++++
 .../148-staged-list-misses-renames.md              |   2 +-
 .../149-synced-plugin-metadata-hash-drift.md       |   8 +-
 5 files changed, 437 insertions(+), 3 deletions(-)

$ git diff --stat 6d80427 aeb4d51
 .agents/extension-inventory.json                   |   8 +-
 docs/audits/2026-10-07-148-station3-redlight.md    | 164 ++++++++++++++++++
 .../148-staged-list-misses-renames.md              | 126 +++++++++++++-
 tests/test_gate.py                                 | 190 +++++++++++++++++++++
 tests/test_leak_scan.py                            |  89 ++++++++++
 tests/test_scanner.py                              |  56 ++++++
 6 files changed, 628 insertions(+), 5 deletions(-)
```

- `6d80427..aeb4d51` 的 `.agents/extension-inventory.json` 來自背景 commit `c91db49`(Jeff policy-only)。

**git 版本與設定(實測)**

```
$ git --version
git version 2.53.0.windows.2
$ git config --show-origin --get-all diff.renames
Exit code 1(無輸出)
```

### §2 正式結果(原 repo,HEAD acf5523;沒有整套改 HOME)

```
$ pwd
<path>
$ python -X utf8 -m pytest -q -rs > <scratchpad>/rv148-full.txt 2>&1    (exit 0)
--- 尾段 ---
SKIPPED [1] tests\test_gate.py:451: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:459: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:473: 此環境無法建立 symlink
SKIPPED [1] tests\test_redlight.py:2673: Windows 檔名不得含 LF;本案例由 POSIX 驗收證明(〈六十一〉61.3 裁決 2)
SKIPPED [1] tests\test_redlight.py:3074: Windows 建 symlink 需要額外權限;POSIX 才產得出來
SKIPPED [1] tests\test_redlight.py:3505: chmod 000 在 Windows 不會讓目錄不可列舉;POSIX 才產得出來
SKIPPED [3] tests\test_redlight.py:3702: Windows 建 symlink 需要額外權限;POSIX 才產得出來
SKIPPED [1] tests\test_redlight.py:3752: Windows 建 symlink 需要額外權限;POSIX 才產得出來
2340 passed, 10 skipped, 3 xfailed in 257.99s (0:04:17)
```

- 結果與預期相同。10 行 skip 的位置和 S3 / S4 記錄的一致。

**帳本前綴證明**

```
$ head -c 1210891 .dev/test-runs.jsonl > <scratchpad>/rv148-runs-prefix.bin
$ head -c 37662732 .dev/test-sessions.jsonl > <scratchpad>/rv148-sessions-prefix.bin
$ sha256sum <兩個 prefix 檔>
6a0a01a45df181e56c5752f52159c0e339b536a68457d5d2c3cfa8a55879b962 *<scratchpad>/rv148-runs-prefix.bin
0d38e3d86ddb1c2773ff4c69839476b87857c43211d82617a2a562878c05b71f *<scratchpad>/rv148-sessions-prefix.bin
$ wc -c .dev/test-runs.jsonl .dev/test-sessions.jsonl
 1222410 .dev/test-runs.jsonl
38477559 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl .dev/test-sessions.jsonl
f8c6b84185b1187f4481166b2b4b088596bcdaf3e4acd482d5e7fc9e6744c64d *.dev/test-runs.jsonl
702483771a1cbda9fc516748311dcb1d9d24c16dfdb99249df8f3dc5f571a32f *.dev/test-sessions.jsonl
```

- 前綴 sha256 等於步驟 0 的值 ⇒ 既有條目沒有被改。
- LC2:runs 1222410 bytes(+11519 bytes),sessions 38477559 bytes(+814827 bytes)。
- H2:`f8c6b841…`、`70248377…`。

### §3 獨立複本與基線

```
$ git clone --no-hardlinks <path> <scratchpad>/r148-copy
Cloning into '<scratchpad>/r148-copy'...
done.
$ git -C <scratchpad>/r148-copy rev-parse HEAD
acf5523690203482cce3760a6943965d1ae548c3
$ git -C <scratchpad>/r148-copy status --porcelain
(無輸出)
Glob <scratchpad>/r148-copy/.dev/* ⇒ gate-exemptions.jsonl、known-chain-breaks.txt(只有這兩個)
Write <scratchpad>/rv148-home/.keep
$ sha256sum <copy>/.claude/hooks/gate.py <copy>/.claude/portable/scanner.py
6fe33699193b246ec90e1e9c8f3ccd04449c0e121f6b1589fdc593a9e17057b6   (G0)
98e5f43c7f50a5d3ad73fb7aeb72281605f99323e43ebd44baed32f35a349a33   (S0)
```

- G0 / S0 與原 repo 工作樹同檔的 sha256 相同。
- G0 也等於豁免帳本票 148 那筆 Edit 紀錄的 `result_hash`(`6fe33699…`)。帳本是 S4 編輯當時寫下的,G0 是從 git 取出的,兩個來源互相獨立。

**⚠ 執行方式偏離(見 F-1)**

- 照指令單獨一行 `cd <scratchpad>/r148-copy` 之後,工具回 `Shell cwd was reset to <path>`;下一行 `pwd` 是 `<path>`。也就是 cwd 無法停在 scratchpad。
- 改用的做法:cwd 留在原 repo,用參數把 pytest 指到複本。

  ```
  env HOME=<scratchpad>/rv148-home USERPROFILE=<scratchpad>/rv148-home python -X utf8 -P -m pytest -q -rA -k t148 --rootdir=<scratchpad>/r148-copy <scratchpad>/r148-copy/tests
  ```

- 加了兩個旗標:
  - `-P`:不把 cwd(原 repo)放進 `sys.path`。
  - `--rootdir`:把 rootdir 固定在複本。
- 先讀碼確認寫入位置:
  - conftest 的帳本根是 `Path(__file__).parents[1]`,也就是複本。
  - 三個被測模組都用 `spec_from_file_location` 從測試檔所在的 ROOT 載入。
  - `leak_scan.py` 用 `sys.path.insert(0, 自身目錄)` 載入 scanner。
- 事後以原 repo 帳本仍等於 H2、複本 `.dev/` 新長出兩本帳本來佐證(實測,見下)。

**基線結果**(`<scratchpad>/rv148-copy-base.txt`)

```
PASSED tests/test_gate.py::TestTicket148RenameDestinationIsListed::test_t148_1_gate_staged_paths_lists_rename_destination[unset]
PASSED …::test_t148_1_gate_staged_paths_lists_rename_destination[true]
PASSED …::test_t148_1_gate_staged_paths_lists_rename_destination[copies]
PASSED …::test_t148_1_gate_staged_paths_lists_rename_destination[false]
PASSED tests/test_gate.py::TestTicket148RenameDestinationIsListed::test_t148_3_rename_source_stays_out_of_both_listings
PASSED tests/test_gate.py::TestTicket148RenameDestinationIsListed::test_t148_4_pure_deletion_stays_out_of_both_listings
PASSED tests/test_gate.py::TestTicket148AuthorityLayerJudgesRenamedSource::test_t148_7c_new_source_file_is_blocked_by_r2
PASSED tests/test_gate.py::TestTicket148AuthorityLayerJudgesRenamedSource::test_t148_7_renamed_into_source_is_blocked_by_r2
PASSED tests/test_leak_scan.py::TestTicket148RenamedFileIsScanned::test_t148_5_secret_in_a_new_file_is_caught
PASSED tests/test_leak_scan.py::TestTicket148RenamedFileIsScanned::test_t148_6_secret_added_during_rename_is_caught
PASSED tests/test_scanner.py::test_t148_2_scanner_staged_paths_lists_rename_destination[unset]
PASSED …::test_t148_2_scanner_staged_paths_lists_rename_destination[true]
PASSED …::test_t148_2_scanner_staged_paths_lists_rename_destination[copies]
PASSED …::test_t148_2_scanner_staged_paths_lists_rename_destination[false]
14 passed, 2339 deselected in 6.86s
```

- 原始輸出裡每行的路徑前綴是 `..\..\<path>\scratchpad\r148-copy\tests\…`,上面已省略。
- 14 個名稱與參數 id 都和審查包 §1 表相符。failed / error / skipped 皆 0。

**基線之後的帳本與狀態**

- 複本 `.dev/` 新生成 `test-runs.jsonl`(859 bytes)與 `test-sessions.jsonl`(793348 bytes),都是 ignored。
- `git -C <copy> status --porcelain` 無輸出。
- 原 repo 帳本 sha256 = `f8c6b841…` / `70248377…`,也就是 H2,沒有變。

**環境差異(複本 vs 原 repo)**

| 項目 | 原 repo | 複本 |
|---|---|---|
| HOME / USERPROFILE | 不改(使用者真實家目錄) | `<scratchpad>/rv148-home`(只有 `.keep`) |
| `.dev/pipeline.json` | 存在(review / 148) | 不存在 |
| 測試帳本 | 存在 | 起初不存在;跑完基線後生成 |
| cwd | 原 repo | 原 repo(cd 無法持久,見 F-1);以 `-P` + `--rootdir` + 路徑參數指向複本 |

**隔離實測(c 題用)**

```
$ env GIT_CONFIG_GLOBAL=<scratchpad>/rv148-empty-gitconfig GIT_CONFIG_NOSYSTEM=1 git -C <scratchpad>/rv148-home config --show-origin --show-scope --list
(無輸出)
```

### §4 突變探針(只在複本)

**探針 A:拿掉 gate 側的 `--no-renames`**

```
$ git -C <copy> diff --stat
 .claude/hooks/gate.py | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
$ git -C <copy> diff
-        ["git", "diff", "--cached", "-z", "--name-only", "--diff-filter=ACM", "--no-renames"],
+        ["git", "diff", "--cached", "-z", "--name-only", "--diff-filter=ACM"],
```

結果(`<scratchpad>/rv148-mut-gate.txt`,exit 1):

```
E       AssertionError: rename 目的檔不在 gate.staged_paths(diff.renames=unset):[]
E       AssertionError: rename 目的檔不在 gate.staged_paths(diff.renames=true):[]
E       AssertionError: rename 目的檔不在 gate.staged_paths(diff.renames=copies):[]
E       AssertionError: rename 進原始碼目錄沒被權威層擋下:rc=0
FAILED …test_t148_1_gate_staged_paths_lists_rename_destination[unset]
FAILED …test_t148_1_gate_staged_paths_lists_rename_destination[true]
FAILED …test_t148_1_gate_staged_paths_lists_rename_destination[copies]
FAILED …TestTicket148AuthorityLayerJudgesRenamedSource::test_t148_7_renamed_into_source_is_blocked_by_r2
4 failed, 10 passed, 2339 deselected in 15.39s
```

- PASSED 的 10 個:`t148_1[false]`、`t148_3`、`t148_4`、`t148_7c`、`t148_5`、`t148_6`、`t148_2[unset/true/copies/false]`。
- **與預期完全相同**。
- 4 個紅都是斷言失敗;沒有 `Failed:`(前提斷言失敗)。

還原證明:

```
$ sha256sum <copy>/gate.py <copy>/scanner.py
6fe33699193b246ec90e1e9c8f3ccd04449c0e121f6b1589fdc593a9e17057b6   (= G0)
98e5f43c7f50a5d3ad73fb7aeb72281605f99323e43ebd44baed32f35a349a33   (= S0)
$ git -C <copy> status --porcelain
(無輸出)
$ sha256sum .dev/test-runs.jsonl .dev/test-sessions.jsonl   (原 repo)
f8c6b841… / 70248377…   (= H2)
```

**探針 B:拿掉 scanner 側的 `--no-renames`**

```
$ git -C <copy> diff --stat
 .claude/portable/scanner.py | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
```

結果(`<scratchpad>/rv148-mut-scanner.txt`,exit 1):

```
E       AssertionError: leak scan 回 0(notes/b.txt 未被擋):
E       AssertionError: rename 目的檔不在 scanner.staged_paths(diff.renames=unset):[]
E       AssertionError: rename 目的檔不在 scanner.staged_paths(diff.renames=true):[]
E       AssertionError: rename 目的檔不在 scanner.staged_paths(diff.renames=copies):[]
FAILED …TestTicket148RenamedFileIsScanned::test_t148_6_secret_added_during_rename_is_caught
FAILED …test_t148_2_scanner_staged_paths_lists_rename_destination[unset]
FAILED …test_t148_2_scanner_staged_paths_lists_rename_destination[true]
FAILED …test_t148_2_scanner_staged_paths_lists_rename_destination[copies]
4 failed, 10 passed, 2339 deselected in 16.58s
```

- `grep -c "^PASSED"` 回 10。
- **與預期完全相同**。

還原證明:

```
$ sha256sum <copy>/gate.py <copy>/scanner.py
6fe33699193b246ec90e1e9c8f3ccd04449c0e121f6b1589fdc593a9e17057b6   (= G0)
98e5f43c7f50a5d3ad73fb7aeb72281605f99323e43ebd44baed32f35a349a33 (= S0)
$ git -C <copy> diff --stat
(無輸出)
$ sha256sum .dev/test-runs.jsonl .dev/test-sessions.jsonl   (原 repo)
f8c6b84185b1187f4481166b2b4b088596bcdaf3e4acd482d5e7fc9e6744c64d
702483771a1cbda9fc516748311dcb1d9d24c16dfdb99249df8f3dc5f571a32f   (= H2)
```

**兩次探針合看(實測)**

- 兩側互不串線:
  - 拿掉 gate 側,T148-6(leak scan)維持綠。
  - 拿掉 scanner 側,T148-7(權威層 R2)維持綠。
- ⇒ 兩個呼叫點各由自己的測試獨立鑑別,沒有一支測試同時依賴兩側。
- T148-3 / T148-4 在兩次探針下都是綠。它們是回歸鎖,不是鑑別器(見 F-5)。

### §5 逐題審查(審查包 §4)

**(a) rename 目的檔是否確實進入權威層 R2 —— 是。【實測】**

- 佈置有效:T148-7 的前提斷言 `_t148_assert_rename(docs/tool.py → pkg/tool.py)` 在 rc 斷言之前執行。探針 A 下的失敗是 `AssertionError … rc=0`,不是 `Failed:`,所以前提確實成立。【實測】
- R10 隔離有效:
  - 7c 斷言 rc 1、含 `[R2`、不含 `[R10`,在基線與探針 A 下都綠。【實測】
  - 不注入 `_extension_claude_root`,`expanduser("~")` 等於 tmp home。【讀碼:斷言在 :7469-7471,且隨測試通過】
- 7c 確實走到 R2:斷言包含 `"[R2" in err`。【實測】
  - tickets 站屬於 `pre_implement`,會進 `[R2/commit]`,而這個分支 return 早於 R3。【讀碼 :2862-2894】
- 撤回修正後 T148-7 轉紅(`rc=0`)。【實測,探針 A】

**(b) rename 目的檔是否確實進入 leak scan —— 是。【實測】**

- T148-5 / 6 共用 `_t148_secret_block()`(執行時組合)。【讀碼】
- `_t148_assert_hit` 同時斷言三件事:rc ≠ 0、含「`命中 pattern:` + 私鑰標頭規則原文」、含 `<檔名>:`。【讀碼】
- T148-6 的前提斷言:恰一列 R、來源 / 目的正確、狀態不是 `R100`。【讀碼 :1208-1212】
- 撤回 scanner 側修正後 T148-6 轉紅(rc 0)。【實測,探針 B】
- ⚠ 範圍只到「該佈置下」:私鑰標頭規則、文字檔、未設 `diff.renames`。符合裁決的限縮措辭。

**(c) 四種 `diff.renames` 設定 —— 隔離成立。【實測 + 讀碼推論】**

- 在隔離環境下,`git config --list --show-origin --show-scope` 沒有任何輸出。也就是 system、Git for Windows 的 ProgramData、global 三層都沒有被讀到。【實測,在 repo 外執行】
- 被測子行程:`staged_paths` 兩處都沒傳 `env=`,所以會繼承 `os.environ`;`monkeypatch.setenv` 改的正是 `os.environ`。【讀碼推論】
- 前提斷言也是同一環境下 git 的實際判定:unset / true / copies 都形成 R,false 形成 D + A。這只有在 local config 生效、且沒有被外層設定覆蓋時才會同時成立。【實測,隨 14 綠】

**(d) 純刪除與 rename 來源的處置維持不變 —— 是。【實測 + 讀碼推論】**

- T148-3(rename 來源不在兩份清單)、T148-4(純刪除不在兩份清單)在基線與兩次探針下都綠。【實測】
- 加了 `--no-renames` 之後,來源是 `D`,被 `ACM` 排除,和純刪除相同。【讀碼】
- 新的未覆蓋情形(只描述,不擴範圍):原始碼檔被改名移出原始碼目錄(例如 `pkg/x.py → docs/x.py`)時,來源 D 不受檢,目的是非原始碼。結果等同「刪除原始碼 + 新增文件」,沒有任何規則評估它。【讀碼推論】
  - 這和修正前的純刪除處置一致,**不是本票新造成的缺口**;修正前連目的也不受檢。

**(e) #5 未改的影響 —— 目前沒有實害,屬潛在問題。【讀碼推論】**

- `scripts/e2e_authority_layer.py:1046-1047` 仍是 `--diff-filter=ACM`,沒有 `--no-renames`。【實測 grep】
- 搜尋 `"mv"|git mv|rename|os.rename|shutil.move`,只命中 :132 的 `--rename-section`(git config 子命令字串),沒有任何 rename 情境。【實測 grep】
- ⇒ 現有案例不會誤判。【讀碼推論】
- 但如果日後加入 rename 案例,`res["evidence"]["staged"]` 會是空的,`premise(clone, staged)` 拿到的清單也會缺目的檔;static 案例的判定條件是 `not hit and staged`,會判成「失敗」。【讀碼推論】
- 建議另外排票,和 F-2 一起記。

**(f) 其他 staged 清單呼叫點 —— 沒發現未涵蓋、會做 rename 配對的逐檔呼叫點。【讀碼推論】**

- 呼叫點(對照 R0 表):
  - #2b `_staged_names_all`:有 `--no-renames`(:4065)。
  - #4 `verify_gates.py:717`、#6 `e2e:1128`:只判空與非空。
  - #5:見 (e)。
- R0 §3 的缺口補搜:`--staged` 只出現在 `leak_scan` 自己的旗標;`status --porcelain` 有 `install.py:610`、`status.py:633`、`sync.py:291`、`e2e:1303`,都是髒污檢查或前後比對,不逐檔判定;`--raw`、`find-copies` 都是 0 命中。【實測 grep;用途是讀碼推論】
- `.githooks/pre-commit` 只串接 #3 與 #1/#2b。
- `-C` / copies 的語意層、字串拼接、二進位與編碼:仍為 **UNKNOWN**(與 R0 §3 相同,本輪未擴查)。

**(g) 程式改動範圍 —— 只有兩處旗標與 docstring,敘述正確。【實測 + 讀碼推論】**

- 範圍:`git show 9efca02` 的 production diff 只有兩處參數各加 `"--no-renames"`,以及各 3 行 docstring。【實測】
- docstring 的敘述:「R 不在 ACM」「目的以 A 進清單」「來源是 D,照舊不進清單」三點,都與探針結果和 T148-3/4 一致。【實測】
- docstring 寫「R1/R2/R3/R8 都不評估它」:其中 R2 有實測(T148-7)。R1 / R3 / R8 對 rename 目的檔的評估沒有專屬測試,只能由「進入逐檔 `check()`」推得。【讀碼推論】

**(h) 證據分級 —— 沒有混用;只追加的證明成立。【實測】**

- (3) 正式結果綁 `9efca02`;(4) 明寫「未重跑」並以 diff 推論;(5) 標為外部、不屬本 repo 帳本,並列出兩項限制。分級清楚。
- 本輪在 `acf5523` 重跑全套,得到 2340 / 10 / 3。
  - `9efca02..acf5523` 的實測 diff 只有文件與豁免帳本。
  - ⇒ 這次重跑是對 `9efca02` 程式內容的**獨立第二次量測**。執行者與時點都不同,但機器相同。
- 帳本:步驟 0 的值和 S4 審計 §7 的「現整檔」相同;本輪前綴 sha256 等於步驟 0 值。⇒ 鏈連續,而且只追加。
- 審查包 §2 (5) 的外部 Linux 預演沒有本 repo 紀錄,本輪無法驗證。維持它原本的分級,不升格。

**(i) 豁免帳本 —— 符合裁決 (s)。【實測 + 讀碼推論】**

- 裁決 (s) 的原文在票 146 :437(審查包沒有給出處;見 F-6):
  > 「gate 自我修改豁免紀錄不得刪改。進入某次 code commit 前已存在的未提交紀錄，必須隨該次 code commit 進版；若該次 commit 的 pre-commit 執行期間新追加 at_commit: true 紀錄，因其產生於 index 建立之後，照實留在工作樹，隨下一個允許的 commit 進版…」
- 第 1 筆(23:31:25,Edit)、第 2 筆(23:42:09,乾跑的 pre-commit):都在 commit 前就已存在 ⇒ 隨 `9efca02`。【實測:git show 9efca02 的 diff 有 +2 行】
- 第 3 筆(23:42:19.69,at_commit true):隨 `4d35073`。【實測:`git diff 9efca02 acf5523 -- .dev/gate-exemptions.jsonl` 只有 +1 行,就是這一筆】
- 時間核對:`9efca02` 的 ad / cd 都是 `2026-10-07T19:42:18-04:00`(= 23:42:18Z),早於第 3 筆。
  - 這與「git 在跑 pre-commit 前就決定 ident 日期,且行程內快取」相容。【讀碼推論,依 git 內部行為的記憶,本輪未讀 git 原始碼】
- 所有既有行都沒有被改(diff 只有 `+`)。【實測】
- `acf5523` 沒有新增任何帳本行。【實測】

### §6 結尾核對(原 repo)

```
$ pwd
<path>
$ git rev-parse HEAD
acf5523690203482cce3760a6943965d1ae548c3
$ git status --porcelain
(無輸出)
$ sha256sum .dev/test-runs.jsonl .dev/test-sessions.jsonl
f8c6b84185b1187f4481166b2b4b088596bcdaf3e4acd482d5e7fc9e6744c64d *.dev/test-runs.jsonl
702483771a1cbda9fc516748311dcb1d9d24c16dfdb99249df8f3dc5f571a32f *.dev/test-sessions.jsonl
```

- 兩本帳本仍等於 H2。前綴證明同 §2。
- 帳本 sha256 是探針 B 還原後最後一次量的,之後只有 `pwd` / `rev-parse` / `status` / `date`,沒有再跑 pytest。

### §7 發現清單

**F-1 | 非阻擋 | 實測 —— 執行方式偏離指令:cd 無法持久**

- 單獨一行 `cd <scratchpad>/r148-copy` 後,工具把 cwd 重設回原 repo(原文:`Shell cwd was reset to <path>`)。
- 改用的做法:`-P`、`--rootdir=<copy>`、複本 tests 路徑參數。
- 是否寫進原 repo:原 repo 帳本三次核對都等於 H2,複本 `.dev/` 生成兩本帳本 ⇒ 沒有寫進原 repo。【實測】
- 是否真的跑到複本的程式:探針 A / B 只改複本,而測試確實轉紅 ⇒ 被測程式來自複本。【實測】
- 這不是閘門擋下,沒有繞過任何規則;照實記錄。

**F-2 | 非阻擋 | 讀碼推論 —— 未記錄、未測的行為變化:單純改名現在會被完整檢查**

- 修正前,R(含 R100)整筆不受檢。修正後,目的檔以 A 進 R1 / R2 / R3 / R8 與 leak scan 全檔掃描。
- 可能出現的新擋下:
  - `implement` 站 `pkg/a.py → pkg/b.py`,但沒有 `tests/test_b.py` ⇒ R3。
  - 改名一個早已提交、內容命中 pattern 的檔 ⇒ leak scan 擋下。
- 這符合裁決「讓 rename 目的檔按新增檔進入檢查」,不是缺陷。但票面與 docstring 沒有點出「下游可能出現新的擋下」,R1 / R3 / R8 也沒有 rename 專屬測試(只有 R2)。
- 建議:另外開票記錄,或在下次發布說明中註明。

**F-3 | 非阻擋 | 讀碼推論 —— 原始碼改名移出原始碼目錄不受任何規則評估**

- 見 (d)。等同純刪除,修正前後一致;只描述,不擴範圍。

**F-4 | 非阻擋 | 讀碼推論 —— #5 是潛在問題**

- 見 (e)。目前沒有 rename 案例,所以沒有實害;一旦新增,證據清單會漏列。
- 建議另外排票(與 F-2 同票即可)。

**F-5 | 非阻擋 | 實測 —— T148-3 / T148-4 不是鑑別器**

- 在兩次探針下都綠。拿不拿掉修正,「來源不在清單」都成立,所以它們只鎖回歸,不證明修正。
- R0 §7 A 提過 `T148-both-listings-agree-on-rename`(兩份清單答案一致),實際沒有採用。T148-3 只部分涵蓋(兩份都不含來源)。
- 契約沒有要求這一項 ⇒ 只記錄。

**F-6 | 非阻擋 | 實測 —— 審查包文件小瑕疵**

- §4 (i) 引用「裁決 (s)」,但沒有給出處。實際在票 146 :437(另見 `docs/audits/2026-10-06-146-station4a-core-implementation.md:66`)。
- 審查包 §1 寫「製作時 HEAD `4d35073`」,而包本身在 `acf5523` 提交。行號仍以 `4d35073` 為準;`acf5523` 沒有改程式,所以行號仍有效。【實測 diff】

**F-7 | 非阻擋 | UNKNOWN —— 外部 Linux 預演無法在本 repo 核對**

- 審查包已自述這項限制。本輪不升格,也不否定。
- POSIX CI 未跑(未 push)。

**阻擋項:0。**

### §8 結論

- **PASS-with-notes**(阻擋 0,非阻擋 7)。
- 結論只供 Jeff 裁決;PASS-with-notes 不等於推送授權。

**scratchpad 輸出(平面檔名)**

- `rv148-full.txt`、`rv148-runs-prefix.bin`、`rv148-sessions-prefix.bin`
- `rv148-copy-base.txt`、`rv148-mut-gate.txt`、`rv148-mut-scanner.txt`
- `rv148-empty-gitconfig`
- 目錄:`rv148-home/`(`.keep`)、`r148-copy/`

除授權的測試帳本追加與新報告外,未修改原 repo;未 commit、未 push。
