> **本檔為正本**;`.dev/reports/2026-09-08T233524Z-laptop-align-verify.md` 下同名內容是產出當下的本機副本,不維護。
> **產出機器**:hostname=`14X`(筆電),對齊後 HEAD=`74464ca`。
> **本地時間** `Wed Sep  9 07:45:56     2026` / **UTC** `Tue Sep  8 23:45:56 UTC 2026`。
> **機器身分以 hostname 記錄。** 使用者名稱是受守的個人識別(個人 pattern),刻意不寫入版控 —— 不是漏寫;2026-09-09 本檔第一次 commit 即因此被權威層擋下。

# 筆電對齊 + 權威層 + 全套測試 驗證回報

- 機器:hostname=`14X`
- Repo:`C:/projects/agent-gates`
- 對齊後 HEAD:`74464ca`
- 產檔時間(UTC):`2026-09-08T233524Z`(取自 `date -u +%Y-%m-%dT%H%M%SZ`)
- 執行環境:Claude Code 的 Bash 工具,本機為 Git Bash(POSIX sh),非 PowerShell

**檔名說明:** 執行時 `.dev/reports/` 不存在(`ls: cannot access '.dev/reports/': No such file or directory`),
且全樹 `find . -path ./.git -prune -o -name '*Z-*.md' -print` 回 0 筆 —— **沒有既有格式可照抄**。
本檔採用指令中給定的字面格式 `YYYY-MM-DDTHHMMSSZ-laptop-align-verify.md`。

**轉錄聲明(適用全檔):** 底下每一段都是從工具回傳的主控台輸出**轉錄**進來的,
不是由指令直接重導向寫入(重導向被 R7 擋下,見文末附錄)。
因此「這些位元組與 stdout 的位元組完全相同」是**未證明**;
可證明的是「與我讀到的主控台呈現相同」。這個差別在下面亂碼那幾行特別要緊。

---

## 步驟一:對齊

### `git pull --ff-only origin master`

```
From https://github.com/wusuowei-tw/monkeyleash
 * branch            master     -> FETCH_HEAD
Updating d2a1c67..74464ca
Fast-forward
 .agents/portable-manifest.txt                      |  61 ++
 .claude/hooks/gate.py                              | 357 ++++++++++-
 .claude/hooks/redlight.py                          |  11 +
 .claude/portable/g1_verify.py                      | 105 +--
 .claude/portable/install.py                        |  19 +-
 .claude/portable/ledger_verify.py                  | 213 ++++++-
 .claude/portable/mcp_server.py                     |  26 +-
 .claude/portable/scanner.py                        | 178 +++++-
 .claude/portable/shadow_review.py                  | 108 ++--
 .claude/portable/status.py                         |  72 ++-
 .claude/portable/ticket_lookup.py                  |  89 +++
 .claude/portable/verify_gates.py                   | 131 +++-
 .dev/gate-exemptions.jsonl                         |  28 +
 .dev/known-chain-breaks.txt                        |  59 ++
 .github/workflows/tests.yml                        |  24 +
 .gitignore                                         |   6 +
 CLAUDE.md                                          |  10 +
 README.md                                          |   6 +
 README.zh-TW.md                                    |   6 +
 docs/adr/F-0016-r2-content-bound-exemption.md      |  96 +++
 docs/agents/friction-log.md                        | 249 ++++++++
 docs/audits/2026-09-07-arch-round-2.md             | 280 ++++++++
 docs/handover/2026-09-11.md                        | 104 ++-
 docs/machine-init.md                               |  25 +-
 ...-sync-needs-an-r2-exemption-bound-to-content.md | 247 ++++++-
 .../109-scanner-is-blind-to-utf16.md               | 334 ++++++++++
 .../110-scanner-is-blind-to-utf32.md               | 341 ++++++++++
 ...ily-fourth-hit-repo-local-tmp-and-scratchpad.md | 336 ++++++++++
 .../112-r7-inline-interpreter-is-undecidable.md    | 317 +++++++++
 .../113-boundary-family-needs-a-machine.md         |  73 +++
 .../114-three-things-with-two-sources.md           | 323 ++++++++++
 .../115-install-py-still-prints-bare.md            | 139 ++++
 .../116-the-ledger-and-its-readers-disagree.md     | 583 +++++++++++++++++
 .../117-pipeline-json-has-no-format-check.md       |  79 +++
 ...m-skips-have-no-reason-and-no-expected-count.md | 101 +++
 ...119-r3-has-no-path-for-a-comment-only-change.md |  97 +++
 ...-name-is-not-importable-for-hyphenated-files.md |  87 +++
 .../121-splitlines-eats-cr-across-the-repo.md      |  98 +++
 ...emption-recon-premise-holds-for-zero-records.md | 144 +++++
 .../15-unclassified-must-not-default-to-copy.md    |  32 +-
 .../17-sync-guards-judge-the-wrong-object.md       |  19 +
 .../framework-updates/22-machine-recovery-drill.md |   4 +-
 .../23-cert-ext-misses-pkcs8-and-pkcs7.md          |  34 +-
 .../framework-updates/54-ci-github-actions.md      |  23 +-
 ...6-misdiagnoses-a-missing-tree-as-a-violation.md | 104 ++-
 ...produces-githooks-and-bootstrap-fails-closed.md |  67 ++
 ...e-tools-print-non-ascii-through-a-bare-print.md | 345 +++++++++-
 .../77-ticket-prefix-matches-without-boundary.md   |  11 +-
 .../78-gitignore-dedup-by-substring.md             | 111 +++-
 .../79-g1-level2-msys-canon-and-quoted-prose.md    |   7 +
 ...urce-path-does-not-normalise-before-matching.md |   2 +-
 .../85-local-vs-ci-collection-differs.md           | 279 +++++++-
 ...nel-absent-when-session-root-is-not-the-repo.md |   2 +-
 .../87-backup-has-no-staleness-trigger.md          | 199 +++++-
 .../88-g1-level1-does-not-expand-tilde.md          |   2 +-
 .../89-first-three-prose-rules-get-machines.md     |   4 +-
 ...ead-sha-citations-after-the-identity-rewrite.md |   2 +-
 ...l-pattern-lists-diverged-across-two-machines.md |  29 +-
 ...2-g1-reads-the-protection-list-as-plain-utf8.md |   2 +-
 .../94-six-stages-is-a-name-nobody-guards.md       | 126 +++-
 ...positive-controls-skip-outside-a-posix-shell.md | 135 +++-
 ...97-bash-allowlists-match-without-normalising.md |   2 +-
 ...ync-and-gate-read-different-heading-criteria.md |   2 +-
 tests/test_adr_numbers_resolve_upstream.py         | 122 ++++
 tests/test_bash_write.py                           |  37 +-
 tests/test_bootstrap.py                            | 302 ++++++++-
 tests/test_ci_workflow.py                          | 140 ++++
 tests/test_declared_in_is_an_identity.py           | 260 ++++++++
 tests/test_gate.py                                 | 709 +++++++++++++++++++++
 tests/test_install.py                              |  98 +++
 tests/test_leak_scan.py                            | 249 ++++++++
 tests/test_ledger_verify.py                        | 292 ++++++++-
 tests/test_line_ending_parity.py                   | 247 +++++++
 tests/test_mcp_server.py                           |  64 ++
 tests/test_non_source_list_parity.py               | 276 ++++++++
 tests/test_portable_output_encoding.py             | 341 ++++++++++
 tests/test_scanner.py                              | 197 ++++++
 tests/test_shadow_review.py                        |  95 +++
 tests/test_stage_naming.py                         | 241 +++++++
 tests/test_status.py                               | 141 ++++
 tests/test_sync.py                                 |  51 +-
 tests/test_ticket_dirs_are_md_only.py              | 350 ++++++++++
 tests/test_ticket_lookup.py                        | 242 +++++++
 tests/test_ticket_path_parity.py                   | 199 ++++++
 tests/test_verify_gates.py                         |  60 ++
 85 files changed, 11580 insertions(+), 238 deletions(-)
 create mode 100644 .claude/portable/ticket_lookup.py
 create mode 100644 .dev/known-chain-breaks.txt
 create mode 100644 docs/adr/F-0016-r2-content-bound-exemption.md
 create mode 100644 docs/audits/2026-09-07-arch-round-2.md
 create mode 100644 docs/tickets/framework-updates/109-scanner-is-blind-to-utf16.md
 create mode 100644 docs/tickets/framework-updates/110-scanner-is-blind-to-utf32.md
 create mode 100644 docs/tickets/framework-updates/111-r7-boundary-family-fourth-hit-repo-local-tmp-and-scratchpad.md
 create mode 100644 docs/tickets/framework-updates/112-r7-inline-interpreter-is-undecidable.md
 create mode 100644 docs/tickets/framework-updates/113-boundary-family-needs-a-machine.md
 create mode 100644 docs/tickets/framework-updates/114-three-things-with-two-sources.md
 create mode 100644 docs/tickets/framework-updates/115-install-py-still-prints-bare.md
 create mode 100644 docs/tickets/framework-updates/116-the-ledger-and-its-readers-disagree.md
 create mode 100644 docs/tickets/framework-updates/117-pipeline-json-has-no-format-check.md
 create mode 100644 docs/tickets/framework-updates/118-cleanroom-skips-have-no-reason-and-no-expected-count.md
 create mode 100644 docs/tickets/framework-updates/119-r3-has-no-path-for-a-comment-only-change.md
 create mode 100644 docs/tickets/framework-updates/120-r3-pair-name-is-not-importable-for-hyphenated-files.md
 create mode 100644 docs/tickets/framework-updates/121-splitlines-eats-cr-across-the-repo.md
 create mode 100644 docs/tickets/framework-updates/122-code-review-exemption-recon-premise-holds-for-zero-records.md
 create mode 100644 tests/test_adr_numbers_resolve_upstream.py
 create mode 100644 tests/test_declared_in_is_an_identity.py
 create mode 100644 tests/test_line_ending_parity.py
 create mode 100644 tests/test_non_source_list_parity.py
 create mode 100644 tests/test_portable_output_encoding.py
 create mode 100644 tests/test_stage_naming.py
 create mode 100644 tests/test_ticket_dirs_are_md_only.py
 create mode 100644 tests/test_ticket_lookup.py
 create mode 100644 tests/test_ticket_path_parity.py
```

### `git rev-parse --short HEAD`

```
74464ca
```

### `git status --porcelain`

```
(Bash completed with no output)
```

**停止條件 1 未觸發**:對齊後 HEAD = `74464ca`,等於對齊前量到的 `origin/master`
(`git rev-parse --short origin/master` → `74464ca`);工作區乾淨(零輸出)。

> 上面那次 `git status --porcelain` 是在寫入本檔**之前**跑的。
> 本檔落到 `.dev/reports/` 之後,狀態會多出一筆未追蹤項 —— 那是預期,不是污染。

### 對齊前的基準(同一 session,步驟一之前量的)

```
$ git log --oneline -1
d2a1c67 票 108 刀四:F-161 進 friction log,規矩搬到 leak-patterns.txt 檔頭,收票

$ git status --porcelain
(Bash completed with no output)

$ git fetch origin
From https://github.com/wusuowei-tw/monkeyleash
   d2a1c67..74464ca  master     -> origin/master

$ git rev-list --left-right --count origin/master...HEAD
51	0

$ git rev-parse --short origin/master
74464ca

$ python --version
Python 3.11.9
```

左欄 51 = `origin/master` 獨有,右欄 0 = `HEAD` 獨有 ⇒ 落後 51、領先 0,純快轉。

---

## 步驟二:權威層在不在

### `ls -l --numeric-uid-gid .githooks/`

```
total 4
-rwxr-xr-x 1 197609 197609 1308 Sep  4 08:12 pre-commit
```

> **這一段是 2026-09-09 07:49 前後重跑的第二次量測**,不是與本報告其餘部分同一時點那一次。
> 原因:第一次用的是 `ls -l`,輸出帶使用者名稱而那是受守的個人識別。
> **不是把欄位手改掉的** —— 手改會讓一段「關於資料的說明」長得像資料(`F-151`);
> 這裡換的是**指令**,拿到的仍是原始輸出。

### `git config core.hooksPath`

```
.githooks
```

### 對齊後 CLAUDE.md 裡權威層那段

`grep -n "githooks\|\.git/hooks" CLAUDE.md`:

```
30:- **pre-commit 為唯一權威判定** — `.git/hooks/pre-commit` → `gate.py --pre-commit`,擋 commit。
32:  **未安裝的副本上這句不成立**:`.git/hooks/` 不進版控,clone 不會帶走它,
```

`sed -n '25,40p' CLAUDE.md`:

```
## gate.py 強制契約

單一邏輯 `.claude/hooks/gate.py`,兩層呼叫:

- **pre-commit 為唯一權威判定** — `.git/hooks/pre-commit` → `gate.py --pre-commit`,擋 commit。
  **在已安裝的副本上**綁得住所有人(含非 Claude 的 agent 與人工 commit)。
  **未安裝的副本上這句不成立**:`.git/hooks/` 不進版控,clone 不會帶走它,
  而且完全靜默 —— 前哨照跑、測試照綠,沒有東西會說權威層不在。這是已知缺陷,不是留白。
- **agent hook 為前哨** — `.claude/settings.json` PreToolUse → `gate.py`,早點紅比 commit 才紅好。
  「繞過前哨仍會在 commit 被擋」**只在權威層已安裝時成立**;沒裝時前哨會直接說出這件事,
  並指出它自己涵蓋不到誰(clone 下來直接手動 commit 的人)。

規則(**本表不寫共幾條,也不寫成閉區間**。權威來源是 `gate.py` 的 `rule_codes()` ——
它從規則自己的擋下訊息掃出來,加一條規則就自動涵蓋。
寫死條數或結尾編號的話,下次加規則時不會有人記得回來改這裡,
```

### 附帶量測:`.git/hooks/` 底下有什麼

`ls -la --numeric-uid-gid .git/hooks/`(同上,2026-09-09 07:49 前後重跑,未過濾):

```
total 57
drwxr-xr-x 1 197609 197609    0 Sep  4 08:12 .
drwxr-xr-x 1 197609 197609    0 Sep  9 07:49 ..
-rwxr-xr-x 1 197609 197609  478 Sep  4 08:12 applypatch-msg.sample
-rwxr-xr-x 1 197609 197609  896 Sep  4 08:12 commit-msg.sample
-rwxr-xr-x 1 197609 197609 4726 Sep  4 08:12 fsmonitor-watchman.sample
-rwxr-xr-x 1 197609 197609  189 Sep  4 08:12 post-update.sample
-rwxr-xr-x 1 197609 197609  424 Sep  4 08:12 pre-applypatch.sample
-rwxr-xr-x 1 197609 197609 1649 Sep  4 08:12 pre-commit.sample
-rwxr-xr-x 1 197609 197609  416 Sep  4 08:12 pre-merge-commit.sample
-rwxr-xr-x 1 197609 197609 1374 Sep  4 08:12 pre-push.sample
-rwxr-xr-x 1 197609 197609 4898 Sep  4 08:12 pre-rebase.sample
-rwxr-xr-x 1 197609 197609  544 Sep  4 08:12 pre-receive.sample
-rwxr-xr-x 1 197609 197609 1492 Sep  4 08:12 prepare-commit-msg.sample
-rwxr-xr-x 1 197609 197609 2783 Sep  4 08:12 push-to-checkout.sample
-rwxr-xr-x 1 197609 197609 2308 Sep  4 08:12 sendemail-validate.sample
-rwxr-xr-x 1 197609 197609 3650 Sep  4 08:12 update.sample
```

→ 除了 `.sample` 之外**沒有任何檔案**。第一次量測有 `| grep -v '\.sample'` 過濾,
這一次沒有 —— **這一份比前一份強**:過濾過的清單證明的是「篩掉之後沒有東西」,
未過濾的清單直接把整個目錄攤開,讀的人不必相信篩選條件寫對了。
`..` 的 mtime 兩次不同(`Sep  9 07:30` → `Sep  9 07:49`),那是 repo 期間有寫入所致,不是同一次量測。

### 判定:文件與機器不一致(**已記錄,未修改任何檔案**)

- 機器側:`core.hooksPath` = `.githooks`;`.githooks/pre-commit` 存在、可執行
  (mode `-rwxr-xr-x`,1308 bytes,mtime `Sep  4 08:12`)。
- 文件側:**對齊後**(HEAD `74464ca`)的 `CLAUDE.md` 第 30、32 行仍寫 `.git/hooks/`。
- 後果不是「權威層不在」,是**指路指錯**:照第 30 行去 `.git/hooks/` 找,
  在這台機器上會找不到,而它實際上在 `.githooks/`。
- 第 32 行「`.git/hooks/` 不進版控,clone 不會帶走它」那段推論在 `.githooks` 設計下
  已不是原本那個形狀 —— `.githooks/pre-commit` 進版控,clone 會帶走**檔案**,
  少的只是 per-clone 的 `core.hooksPath` config(由 `bootstrap.sh` 設,
  見 `.github/workflows/tests.yml` 的「接上權威層」步驟註解)。
  「靜默」那一半是否仍成立,本次**未證明** —— 沒去讀 `bootstrap.sh`,
  也沒去看有沒有東西會在 config 沒設時出聲。
- **本次未做**:沒有實際發起一次 commit 去驗權威層真的會擋(裁決明令不得 commit)。
  「這個 pre-commit 會擋下違規」在本機**未證明**;
  本次證明的只是「檔案存在、可執行、且 git 指向該目錄」。

---

## 步驟三:全套測試

### 讀到的 CI 指令原文

來源:`.github/workflows/tests.yml`,job `pytest`,step `跑測試`:

```yaml
      - name: 跑測試
        run: |
          python -m pytest -q \
            --ignore=tests/test_known_items_regression.py \
            --deselect "tests/test_gate.py::TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce"
```

### 本機實際執行(照抄,未加任何截斷旗標)

```
python -m pytest -q \
  --ignore=tests/test_known_items_regression.py \
  --deselect "tests/test_gate.py::TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce"
```

### 完整輸出

```
........................................................................ [  4%]
........................................................................ [  9%]
........................................................................ [ 13%]
........................................................................ [ 18%]
..............................................xxx....................... [ 22%]
........................................................................ [ 27%]
........................................................................ [ 31%]
........................................................................ [ 36%]
............sss......................................................... [ 41%]
........................................................................ [ 45%]
........................................................................ [ 50%]
........................................................................ [ 54%]
........................................................................ [ 59%]
........................................................................ [ 63%]
........................................................................ [ 68%]
........................................................................ [ 73%]
........................................................................ [ 77%]
........................................................................ [ 82%]
........................................................................ [ 86%]
........................................................................ [ 91%]
........................................................................ [ 95%]
................................................................         [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_gate.py:451: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:459: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:473: 此環境無法建立 symlink
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/srv/x] - <此行原因字串在主控台為亂碼,見下方說明>
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/data/x] - <此行原因字串在主控台為亂碼,見下方說明>
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/backup/x] - <此行原因字串在主控台為亂碼,見下方說明>
1570 passed, 3 skipped, 1 deselected, 3 xfailed in 228.28s (0:03:48)
```

**上面那個區塊有兩處不是逐位元組原文,必須點名:**

1. 三行 `SKIPPED` 的原因字串,主控台實際呈現為亂碼。
   上面填的「此環境無法建立 symlink」是**我從亂碼推回去的**,**不是機器輸出** ——
   依 `F-151` 的判準,那一行是「關於資料的說明」,不是資料。**原文未證明。**
2. 三行 `XFAIL` 的原因字串同樣是亂碼,且長度可觀。
   我不轉錄那串亂碼:亂碼經過「主控台解碼 → 我轉錄 → 寫檔再編碼」三道,
   任何一道都會改動位元組,而**轉錄出來的東西會長得像原文**。
   要拿到原文,正確做法是重跑一次並讓輸出直接落到檔案(本次因 R7 未做)。

**唯一未受亂碼影響、可逐字採信的是結尾統計行**(純 ASCII)。

### 統計(**全部抄自結尾統計行,未自行計算**)

| 項 | 筆數 |
|---|---|
| passed | 1570 |
| failed | 0(結尾統計行**沒有** failed 欄位) |
| skipped | 3 |
| deselected | 1 |
| xfailed | 3 |
| 耗時 | 228.28s (0:03:48) |

- **總收集數:未證明。** `-q` 的結尾統計不印 collected 總數,本次沒有另跑 `--collect-only`。
  把上表相加得 1577 是**推算**,不是機器輸出,不得當成量測值引用。
- **退出碼:未證明。** 本次未取用 `$?`;判斷「全綠」的依據是結尾統計行沒有 failed / error 欄位。

### 與 CI 的口徑差異(**本次刻意未跑的步驟**)

`tests.yml` 的 job 共五個 step,本次只跑第四個(`跑測試`)。未跑的四個與理由:

1. `python -m pip install -e ".[dev]"` —— 裁決明令不得裝任何套件。
   測試跑得起來表示相依已在本機,但**版本是否與 CI 相同,未證明**。
2. `sh bootstrap.sh` —— 它會寫 git config(`core.hooksPath`)。
   本機該值已是 `.githooks`,且裁決要求不改設定,故未跑。
3. `收集清單(票 85)` 的 `--collect-only` —— 不屬於「跑全套測試」那一條。
   **附帶後果**:票 85 要的本機 ↔ CI 收集清單差集,本次沒有素材。
4. `淨室驗證` `python .claude/portable/verify_gates.py "${{ runner.temp }}/verify-gates"` ——
   同上,且它會在暫存目錄做一次真實安裝。
   **因此「安裝後形態」在本機是未證明** —— 本次綠燈只涵蓋原始碼形態(這個 repo 的樹)。

---

## 附錄:R7 在寫本檔時擋了一次(**未繞過**)

第一次嘗試是 `mkdir -p .dev/reports && cat > '<本檔>' <<'REPORT_EOF' … REPORT_EOF`,被前哨擋下。
原始擋下訊息(節錄自開頭與結尾,中段列舉的被切段落過長故省略,省略處已標明):

```
PreToolUse:Bash hook error: [python "$CLAUDE_PROJECT_DIR/.claude/hooks/gate.py"]: [六站閘門/前哨] [R7][enforce] 這個 Bash 指令會寫到沒有被許可的位置(FETCH_HEAD、(引號或跳脫使目標無法可靠切分)、本檔本身寫入、上面那次量測是在寫入本檔**之前**跑的。)。
     **許可是逐段比對的**(`&&` / `;` / `||` 各算一段)。
     這幾段不在清單裡:`mkdir -p .dev/reports`、`cat > '.dev/reports/2026-09-08T233524Z-laptop-align-verify.m…`、
     〔中略:約一百段,全部是 heredoc 內文被切出來的片段〕
     其餘各段本來就許可 —— 把它們拿掉就過得了。
     **切分不認引號,也不認 heredoc 內文**:`<<'EOF'` 到 `EOF` 之間、
     以及引號裡的每一個 `;` / `&&` / `||`,一樣會被切成一段。
     所以「整條以 `git` 開頭」不代表安全 —— 訊息或腳本內文裡的一個分號,
     就會切出一段不以許可前綴開頭的段落。
     出口:**內文用 Write 寫成檔案**,再 `git commit -F <路徑>`
     或 `python <路徑>` 餵進去 —— 內文完全不進指令字串,
     就沒有東西可以被切。
     理由不是風格:從指令字串解析『寫到哪』解不完,而半套的解析器
     比零涵蓋更危險 —— 零涵蓋你知道它是零。所以入口收成一個,
     走檔案工具的話 R1–R6 全部適用。
     例外(附理由)在 gate.py 的 BASH_ALLOWED_CMDS / BASH_ALLOWED_TARGETS。
     指令裡出現 /dev/null **不會**讓其他寫入一起免檢。
(R7 只活在前哨:commit 看得到檔案內容,看不到你用什麼工具寫的。
 繞過前哨就沒有第二道了 —— 見 docs/adr/0008)
```

處置:**照擋下訊息本身指定的出口走** —— 改用 Write 工具寫本檔,內文完全不進指令字串。
沒有改路徑、沒有換到不受管的位置、沒有動 `.dev/pipeline.json`。

**一項值得記下的觀察(未開票,交裁決者):**
擋下訊息把 heredoc 內文切出約一百段當成「寫入目標」列舉,
其中包含 `項`、`筆數`、`---`、`1570`、`3` 這種明顯不是路徑的東西,
訊息開頭的目標清單也出現「本檔本身寫入」「上面那次量測是在寫入本檔**之前**跑的。」這類散文句。
**擋得對**(fail-closed,方向正確),但**診斷是噪音** ——
它報的「寫入目標」多數是內文的中文句子。
這與 `docs/tickets/framework-updates/112-r7-inline-interpreter-is-undecidable.md` 的題目是否同一件,
本次**未去讀那張票確認,未證明**。

---

## 補錄:權威層活體證據(2026-09-09 追加)

上方步驟二結尾寫著「這個 pre-commit 會擋得住,在本機未證明」。
**那一格在本檔第一次 commit 時被補上了** —— 補它的不是一次刻意的演練,是一次真的違規。

### 已證明

2026-09-09 本檔第一次 `git commit` 被 `.githooks/pre-commit` 擋下,exit code 1,
訊息開頭是 `[洩漏偵測] 這些檔案含個人身分或機密,擋下 commit:`,
命中 5 行,全部是本檔當時寫著的使用者名稱。

判定它走的是**權威層而非前哨**,依據是**訊息沒有 `PreToolUse:Bash hook error:` 前綴** ——
對照同一 session 稍早那次 R7 攔截,該次**有**前綴且由前哨發出;
這次則是 `git commit` 本身以 exit 1 吐出。

所以這台機器的權威層**不只是「檔案存在 + 可執行 + git 指向它」,它真的會擋**。
這三件事在步驟二只能各自證明一半;**只有真的擋過一次,才是行為證據**
(`bootstrap.sh` 收尾那句也是這個意思:「驗收(問的是行為,不是檔案在不在)」)。

### 未證明(一)

**沒有逐行核對 `.githooks/pre-commit` 如何呼叫洩漏偵測。**
上面那句「走的是權威層」是從「有無 PreToolUse 前綴 + exit 1 的來源」**推得的,是推論不是核對**。
要補齊只需讀那支 1308 bytes 的 hook,本次未做。

依 `F-111` 的判準:一整條每一步都成立的推論,可以從一個沒人檢查過的前提出發。
這裡沒被檢查的前提是「前哨一定會加前綴、權威層一定不會」。

### 未證明(二)

**這次擋的是洩漏偵測,不是 R1–R9 任何一條。**
所以「**R 系列在這台的權威層會擋**」仍然沒有活體證據 —— 本次證明的是洩漏段接上了,
不是六站段接上了。`gate.py` 的 `authoritative_layer()` 判定要求 hook 同時含
`gate.py`、`--pre-commit`、`leak_scan` **三者**;本次只驗到 `leak_scan` 那一段真的會動。

---

## 補錄:三筆旁證(本檔升為正本時追加,2026-09-09)

以上是筆電這一側的原始回報,一個字未改。以下三筆是**追加**,不是原報告的一部分。

**每一筆先標材料來源** —— 依 `F-151` 下半(「這次量測的輸入,有沒有一部分是從被量的東西身上拿的」),
以及「材料若來自被量的對象,只能證明自洽」。

### 旁證一:雲端 CI 第 103 次執行

- **內容**:conclusion=`success`,啟動於 push 後約 4 分鐘。
- **材料來源**:**裁決者提供,本 session 未自行量測。** 筆電這一側沒有跑過 `gh run list` / `gh run view`。
- **「該次即 `74464ca`」標未證明** —— sha 字串未逐字核對。
  第 103 次執行對應哪一個 commit,目前是**由時間相鄰推出來的**,不是比對出來的。
  要補齊只需一次 `gh run view 103 --json headSha`,本次未做。

### 旁證二:與票 112 收票時的全套數字對照

| | passed | skipped | xfailed |
|---|---|---|---|
| 票 112 收票時 | 1466 | 3 | 3 |
| 本次(筆電,HEAD `74464ca`) | 1570 | 3 | 3 |

- **材料來源**:上排(1466)**裁決者提供,本 session 未自行量測**;
  下排(1570)是本檔步驟三的機器輸出。**兩排來源不同,不是同一次量測的兩半。**
- 可讀出的:**skipped 與 xfail 同數**(各 3 / 3),passed 差 +104。
- **不可讀出的**:兩次的口徑是否相同(同樣的 `--ignore` / `--deselect`、同一台機器、同一個 Python)
  在本檔內**未證明**;沒有基準就談差異,正是 `F-109` 那一族。
  「+104 條測試」是**在口徑相同的前提下**才成立的說法,而那個前提沒被驗。

### 旁證三:CLAUDE.md 第 30 / 32 行與機器不一致

- **材料來源**:本 session 自行量測(見上方步驟二,三條指令的原始輸出都在)。
- 第 30 行指 `.git/hooks/`,而實體在 `.githooks/`;本機 `.git/hooks/` 底下無非 `.sample` 檔。
- 第 32 行「不進版控、clone 不會帶走」在票 58 之後失效 —— `.githooks/` 進版控。
- **裁決:記錄,不修。** 本次未改 `CLAUDE.md` 一個字。
  (**後續**:2026-09-09 稍晚另有一輪動了第 30–33 行,那**不在本檔記錄的範圍內**,
  且在寫下這一行時仍是未 commit 的工作區改動。上面那句「本次未改」講的是產出本報告的那一次。)

---

## 補錄:跨機器測試數對帳(2026-09-09)

問的是:**筆電這台跑出來的數,跟桌機回報的數,對不對得起來。**
不是再驗一次測試 —— 是驗**兩台機器量的是不是同一批東西**。

### 四列一式

| | 數(單位:測試函式) | 材料來源 |
|---|---|---|
| 筆電實跑 passed | 1570 | **本機量測**(本檔步驟三的結尾統計行) |
| `+` `--ignore=tests/test_known_items_regression.py` 的收集數 | 12 | **本機量測**,`python -m pytest --collect-only -q tests/test_known_items_regression.py` → `12 tests collected in 0.03s`,於 HEAD `81a1e81`;9/5 於 `3fe882c` 同值(該次由裁決者提供) |
| `+` `--deselect` | 1 | **本機量測**(本檔步驟三結尾統計行的 `1 deselected`) |
| `=` | **1583** | 相加 |
| 桌機回報檔 `2026-09-08T121546Z-restore-test-pass.md` 在 `74464ca` 上寫的「全套」 | 1583 | **裁決者提供,非本機量測** |

**兩邊都是 1583。**

### 三個未證明(一個都不能省)

1. **桌機那個 1583 是不是 passed 口徑,本次未查證。**
   我沒有讀過 `2026-09-08T121546Z-restore-test-pass.md`;它寫的「全套 1583」可能是
   passed、可能是 collected、可能是別的。**左式是 passed + ignore + deselect,
   右式的口徑不明** —— 兩個數字相等而口徑不同的話,這次對帳是巧合不是咬合。

2. **那 12 格是否全過,未量。**
   `--collect-only` 只證明**收集得到 12 個**,不證明它們會過。
   把它當成「本來會 passed 的 12」是**假設**。

3. **那 1 格 deselect 掉的是否會過,未量。**
   同上,而且它有前科:同一支 `TestLegacyNoRedlightList::
   test_the_list_is_what_the_generator_would_produce` 在 2026-09-09 稍晚不帶 deselect
   跑時**是紅的**(`assert not ['.claude/portable/g1_guard.py']`)。
   **所以第三格幾乎可以確定不是 passed** —— 這一列進得了「收集數」,進不了「passed 數」。

### 結論

**四數互相咬合 ⇒ 未見跨機器落差。**

但這句話的效力**完全建立在上面三個前提上**,而其中第三個**已經有反證**。
`1570 + 12 + 1 = 1583` 成立的是**算術**;它成立不代表**兩台機器量的是同一批**。
**三前提任一不成立則需重算** —— 而重算之前,不得把這一節當成「跨機器一致」的證明。

依 `F-151` 下半:這次對帳的三格材料裡,兩格是本機量的,一格(右式的 1583)
**來自被對的那一側**。那一格沒有獨立來源,所以這次對帳**證明得了自洽,證明不了一致**。

### 2026-09-09 更正

**上面那個結論錯了。追加更正,原文不改寫**(`F-036`)——
被推翻的推論留在原地才看得出它是怎麼錯的;把它改掉會讓這一頁讀起來像從來沒錯過。

#### 錯在哪

原結論把「**收集數**對得上」讀成「**通過數**對得上」。
`1570 + 12 + 1 = 1583` 這個算式裡,後兩項是**收集數**,第一項是**通過數** ——
三個加數不同單位,而**相加不會報錯**。
右式那個 1583 若是 passed 口徑,左式就不是同一件東西,等號成立只是巧合。

#### 新事實

桌機在 `74464ca` 上**不帶 `--ignore` / `--deselect`** 跑出 **1583 passed / 0 failed**。
**材料由裁決者從桌機回報檔 `2026-09-08T121546Z-restore-test-pass.md` 第 4-1 節讀出,
本機未讀過該檔。**

#### 三個未證明的現況

| 原未證明 | 現況 |
|---|---|
| ① 桌機那個 1583 是不是 passed 口徑 | **已有答案:是 passed 口徑。** |
| ② 那 12 格是否全過 | **仍未證明**,見下。 |
| ③ 那 1 格 deselect 掉的是否會過 | **已有答案,而且是「不會過」**——見下。 |

①有了答案之後,原算式**當場垮掉**:桌機那 1583 是**不帶任何排除**跑出來的 passed,
而左式是「筆電排除掉兩批之後的 passed」加上「那兩批的收集數」。
**兩邊算的不是同一個量。**

#### 真正的結論:存在跨機器落差(`F-142`)

`TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce`
在**桌機綠、筆電紅**。同一個 commit、同一條測試、兩台結果相反 ⇒ **跨機器落差**。

**今天只查因,不修。**

#### 查因:兩種排序都紅 ⇒ 不是排序污染

```
$ python -m pytest -q -p no:randomly tests/test_gate.py::TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce
F                                                                        [100%]
...
E       AssertionError: 〔原因字串主控台亂碼〕:['.claude/portable/g1_guard.py']
E       assert not ['.claude/portable/g1_guard.py']

tests\test_gate.py:870: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_gate.py::TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce
1 failed in 0.40s
```

```
$ python -m pytest -q tests/test_gate.py::TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce
F                                                                        [100%]
...
E       AssertionError: 〔原因字串主控台亂碼〕:['.claude/portable/g1_guard.py']
E       assert not ['.claude/portable/g1_guard.py']

tests\test_gate.py:870: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_gate.py::TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce
1 failed in 13.78s
```

**兩種都紅**(`-p no:randomly` 加了也一樣)⇒ **不是排序或污染,是真的機器差異。**
兩次的差別只有耗時(0.40s / 13.78s),那是隨機化外掛的收集成本,與判定無關。

環境對照:

```
$ git log --oneline -1 -- .claude/portable/g1_guard.py
2dc3419 票 92 落地:protected_entries() 改用 utf-8-sig —— BOM 不再吃掉第一條保護路徑

$ python -VV
Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
```

#### 落差的機制(**已證明的那一半**)

判定走 `gate.redlight_missing()`,而它讀的紀錄檔是:

```
.claude/hooks/gate.py:61:RUN_LOG = os.path.join(ROOT, ".dev", "test-runs.jsonl")               # 證據
```

那個檔**不進版控**:

```
$ git check-ignore -v .dev/test-runs.jsonl
.gitignore:30:/.dev/*	.dev/test-runs.jsonl
```

⇒ **紅燈證據是 per-machine 的,不隨 clone 走。**

筆電這台的 8 筆紀錄**全部是 green,一筆紅燈都沒有**:

```
$ grep -c "test_g1_guard.py" .dev/test-runs.jsonl
8

$ grep "test_g1_guard.py" .dev/test-runs.jsonl
{"test_file": "tests/test_g1_guard.py", "time": "2026-09-04T00:29:05.079605+00:00", "result": "green", ...}
{"test_file": "tests/test_g1_guard.py", "time": "2026-09-05T00:06:40.409272+00:00", "result": "green", ...}
{"test_file": "tests/test_g1_guard.py", "time": "2026-09-05T00:09:56.792459+00:00", "result": "green", ...}
{"test_file": "tests/test_g1_guard.py", "time": "2026-09-05T00:51:03.274473+00:00", "result": "green", ...}
{"test_file": "tests/test_g1_guard.py", "time": "2026-09-05T00:55:29.235119+00:00", "result": "green", ...}
{"test_file": "tests/test_g1_guard.py", "time": "2026-09-05T00:59:17.074295+00:00", "result": "green", ...}
{"test_file": "tests/test_g1_guard.py", "time": "2026-09-05T01:53:40.518791+00:00", "result": "green", ...}
{"test_file": "tests/test_g1_guard.py", "time": "2026-09-08T23:35:11.052305+00:00", "result": "green", ...}
```

(八筆的 `impl_hash` 皆為 `33ca8e52…`,內容穩定;`ticket_id` 皆 `null`。)

`redlight_missing()` 只在找到 `result == "red"` 的紀錄時回 `None`(= 合格);
這台一筆都沒有 ⇒ 它回訊息 ⇒ `undrained` 非空 ⇒ 紅。**這一段是構造,不是機率。**

#### 這一段裡哪一半是推論

**已證明**:筆電這台沒有紅燈紀錄,所以這條測試在這台**必紅**。
**未證明**:桌機那台有紅燈紀錄。我沒有看過桌機的 `.dev/test-runs.jsonl` ——
「桌機綠是因為它的帳本裡有一筆 red」是**最合理的解釋,不是量到的事實**。
依 `F-113`:一個候選解釋提出來之後要問「它預測的東西在這一次真的出現了嗎」,
而這一格**在桌機那一側沒有被觀測**。

#### 仍未證明

**那 12 格在兩台各自的通過狀況,兩台都未逐格量。**
本機只跑過 `--collect-only`(得 12),桌機那 1583 是總數不是分項。
