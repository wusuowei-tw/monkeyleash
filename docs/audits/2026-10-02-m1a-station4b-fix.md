# M1-a Station 4b —— 修正實作(讓 3b 含補件的 17 支紅燈轉綠)

**這份檔案的身分**:Station 4b 的正式報告,**進版控**
(位置依據:`docs/agents/handover.md:34`「**回報檔一律進版控**(`docs/audits/`)」)。
路徑一律寫 repo 相對路徑;session scratchpad 寫 `<session scratch>`。

| | |
|---|---|
| **撰寫時點** | 2026-10-02T17:07:24Z(寫入當下) |
| **起點 HEAD** | `af839c613e20eb750d80b0ce141305a7c7d1cfd8`(`0 14`,未推) |
| **S4b-1(實作)** | `333e5853bf1a1712bde2aea2d2b488299e3752f6` |
| **S4b-2(證據)** | 本報告所在的 commit;SHA 無法寫進自己 —— 見該 commit |

---

## 【給裁決者】

1. 修正完成:一次 run 對某個測試檔是否「整檔涵蓋」改由 producer 記下的實際參數判定(`true` / `false` / `unknown`,不知道就不算完整);D 狀態的 run 不能退紅;格式不合格的 run 不影響紅綠,但在 status 上會被看到。
2. 固定全套只跑一次:**exit 0,`1946 passed, 3 skipped, 3 xfailed`** —— 3b 的 17 支紅燈全部轉綠,L1–L3、Station 3 的 14 支、其他既有測試全過。
3. 實際 status:票 145 底下 `red 0`、`orphaned 0`、`schema 不合格 run 0`,最近一次 run 為 `A`。這次 run 的真實紀錄也印證了 B10 的推導:固定指令的參數確實是 `["tests"]`、來源 `TESTPATHS`。
4. 要你決定:①進 Station 5b 審查;②〈十〉的現況句仍寫「Station 4b 未開始」,與第 3 行矛盾 —— 本刀授權只改 Station 3b / 4b 兩項,**未動**,要不要下一刀一併改。
5. 不決定的話:十六個 commit 停在本機不推;Station 5b 不開始。

### 最低必要內容

| # | 項目 | 值 |
|---|---|---|
| 1 | coverage 判定依據 | 該檔有 deselected ⇒ `false`;位置參數是該檔或其上層目錄(不含 `::`)⇒ `true`;只以 nodeid 指名 ⇒ `false`;沒有 invocation 事實、pyargs、參數無法判讀、或 schema 不合格 ⇒ `unknown`。**固定指令判為 `"true"`,走通用的「上層目錄」規則,無特殊分支**(`config.args == ["tests"]`) |
| 2 | schema 不合格 run 的表示 | Evidence `test-runs` 行的 `schema 不合格 run N`;最近一次若不合格 ⇒ `最近一次 run:INVALID(schema 不合格:<問題清單>)`;不合格 run 不加紅、不退紅、不 orphan、不 green |
| 3 | 四檔改動 | `.claude/hooks/redlight.py` +163 / −1;`.claude/portable/status.py` +81 / −41;`tests/conftest.py` +29 / −2;`tests/test_status.py` +4 / −2。`tests/test_redlight.py`:**未修改**(`git diff af839c6 --stat -- tests/test_redlight.py` 無輸出);3b / Station 3 測試的 assertion 未修改 |
| 4 | fixture 補件 | 570 / 571 與 ODC-2 的 `record_session(...)` 各加 `invocation={u"args": [u"tests"]}`(= full_file_coverage 為 true 的事實);749 不需補;**assertion 一字未改** |
| 5 | commit 前兩本帳 | **未被寫入**(兩本帳 SHA-256 / bytes / lines 在 commit 前後皆 = H0 / L0) |
| 6 | 固定全套 | exit code **0**;`1946 passed, 3 skipped, 3 xfailed in 147.38s (0:02:27)`;3b 的 17 支**全部轉綠**;L1–L3、Station 3 的 14 支**全部通過** |
| 7 | 兩本帳只追加 | **是**:兩本帳 after 的前段 SHA-256 皆 = H0;test-runs +46(全 green)、test-sessions +1 |
| 8 | status.py | `tests red under ticket 145: (無)`;`tests orphaned under ticket 145: (無)`;`最近一次 run:A(exit 0;collected 1952 / deselected 0 / passed 1946 / failed 0 / skipped 3)` |
| 9 | SHA / rev-list / 樹 | S4b-1 `333e585`;S4b-2 與 `0 16`、樹狀態只在視窗回報 |
| 10 | push / 改 gate.py / 改合約測試 / 改 pipeline / pytest 次數 | **NO / NO / NO / NO / 1** |

---

## 【給裁決助手】證據

### 前置

```
$ git fetch origin
(無輸出)
$ git rev-list --left-right --count origin/master...HEAD
0	14
$ git rev-parse HEAD
af839c613e20eb750d80b0ce141305a7c7d1cfd8
$ git status --porcelain
(無輸出)
$ cat .dev/pipeline.json
{
  "current_stage": "implement",
  "feature": "framework-updates",
  "ticket_id": "145",
  "updated": "2026-10-02"
}
$ sha256sum .dev/test-runs.jsonl .dev/test-sessions.jsonl
b555ded4e2986f819c711c4ef16168c9df25f54cce12fd8064141e9cc7bc2ada *.dev/test-runs.jsonl
d97b7631d55ba0b8359803a6b2ffa9c6330de02b8363dc0c769afea6eb38e12e *.dev/test-sessions.jsonl
$ wc -c -l .dev/test-runs.jsonl .dev/test-sessions.jsonl
   2273  613185 .dev/test-runs.jsonl
     11 1413031 .dev/test-sessions.jsonl
```

(`wc` 的 `total` 行省略。)

### 實作摘要

完整的判定依據、表示形式、四檔改動、conftest 逐段與 fixture 補件原文見票 145〈十九〉。重點:

- `.claude/hooks/redlight.py`:`validate_session()`、`file_coverage()`、`_normalize_arg()` / `_normalize_invocation()`;
  `record_session(..., invocation=None)` 落帳正規化後的 `invocation`(root 相對路徑;絕對路徑不落帳);
  `run_state()` 對不合格 run 回 `INVALID`。
- `tests/conftest.py`:`pytest_sessionfinish` 尾段以 `_invocation_of(session)` 收集 `config.args` / `args_source.name` /
  `invocation_params.dir` / `option.pyargs`,僅在 `record_session` 簽名有 `invocation` 時傳入;既有蒐集邏輯未動。
- `.claude/portable/status.py`:`_apply_run(run, red, orphan, green_now, rl)` —— 不合格 run 不產生效果;D 無退紅權、不 green;
  退紅 / orphan / green 只在 `file_coverage == "true"`;`ticket_test_state(..., rl=None)`;Evidence 顯示 `schema 不合格 run N` 與 `INVALID(…)`。
- `tests/test_status.py`:兩處授權補件(`invocation={u"args": [u"tests"]}`)。

### S4b-1 commit 前

```
$ python -X utf8 -m py_compile .claude/hooks/redlight.py
(無輸出)
$ python -X utf8 -m py_compile .claude/portable/status.py
(無輸出)
$ python -X utf8 -m py_compile tests/conftest.py
(無輸出)
$ python -X utf8 -m py_compile tests/test_status.py
(無輸出)
$ git diff --name-only
.claude/hooks/redlight.py
.claude/portable/status.py
tests/conftest.py
tests/test_status.py
$ wc -c -l .dev/test-runs.jsonl .dev/test-sessions.jsonl
   2273  613185 .dev/test-runs.jsonl
     11 1413031 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl .dev/test-sessions.jsonl
b555ded4e2986f819c711c4ef16168c9df25f54cce12fd8064141e9cc7bc2ada *.dev/test-runs.jsonl
d97b7631d55ba0b8359803a6b2ffa9c6330de02b8363dc0c769afea6eb38e12e *.dev/test-sessions.jsonl
$ git check-ignore -v .scratch/m1a-s4b/s4b-1-msg.txt
.gitignore:67:/.scratch/	.scratch/m1a-s4b/s4b-1-msg.txt
$ git diff --cached --numstat
163	1	.claude/hooks/redlight.py
81	41	.claude/portable/status.py
29	2	tests/conftest.py
4	2	tests/test_status.py
$ git diff --cached --check
(無輸出)
$ git diff --cached --stat -- tests/test_redlight.py
(無輸出)
$ git commit -F .scratch/m1a-s4b/s4b-1-msg.txt
[master 333e585] fix(145): M1-a Station 4b —— coverage authority / D 無退紅權 / schema fail-closed
 4 files changed, 277 insertions(+), 46 deletions(-)
$ git status --porcelain
(無輸出)
```

pre-commit(含 R3:status.py 不在豁免清單、redlight.py 已 drain)未擋。commit 後再量一次兩本帳:SHA-256 / bytes / lines 仍 = H0 / L0。

### 驗收|在 `333e585` 上跑固定全套(只跑一次)

```
$ date -u +%Y-%m-%dT%H:%M:%SZ
2026-10-02T17:03:26Z
$ python -X utf8 -m pytest -q
...
SKIPPED [1] tests\test_gate.py:451: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:459: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:473: 此環境無法建立 symlink
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/srv/x] - …
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/data/x] - …
XFAIL tests/test_g1_guard.py::TestLevelTwoIsUnchanged::test_an_unlisted_root_should_be_visible_to_level_two[/backup/x] - …
1946 passed, 3 skipped, 3 xfailed in 147.38s (0:02:27)

[exited with code 0]
```

(XFAIL 三行的說明文字以 `…` 截斷 —— 本區塊**不是逐字全文**;SKIPPED 與摘要行逐字。輸出中無任何 `FAILED` / `ERROR` 行。背景執行,完成通知回報 `exit code 0`。)

**判定**

| 條件 | 結果 |
|---|---|
| exit code = 0;failed = 0 | **成立** |
| 3b 的 17 支、L1–L3、Station 3 的 14 支不在失敗集合 | **成立**(失敗集合為空) |
| 摘要 1946 passed;skipped / xfailed 3 / 3 | **成立**(1946 = 1929 + 17;skip / xfail 為 baseline 同一批) |

### 帳本只追加

```
$ wc -c -l .dev/test-runs.jsonl .dev/test-sessions.jsonl
   2319  624488 .dev/test-runs.jsonl
     12 1873333 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl .dev/test-sessions.jsonl
73737b7ddc353b2049d3bf8a61e831c9e2ab57e44b634ba91349447d1d0a8a93 *.dev/test-runs.jsonl
42bdc38e99695014d384f501cbf8517ca6a72d5bde690f090fcfc190d6c27e35 *.dev/test-sessions.jsonl
$ head -c 613185 .dev/test-runs.jsonl > <session scratch>/runs-prefix-4b.bin
$ head -c 1413031 .dev/test-sessions.jsonl > <session scratch>/sessions-prefix-4b.bin
$ sha256sum <session scratch>/runs-prefix-4b.bin <session scratch>/sessions-prefix-4b.bin
b555ded4e2986f819c711c4ef16168c9df25f54cce12fd8064141e9cc7bc2ada *<session scratch>/runs-prefix-4b.bin
d97b7631d55ba0b8359803a6b2ffa9c6330de02b8363dc0c769afea6eb38e12e *<session scratch>/sessions-prefix-4b.bin
```

(scratchpad 絕對路徑以 `<session scratch>` 代替 —— **這三條指令與輸出經遮罩,不是逐字原文**;`wc` 的 `total` 行省略。)

- test-runs:2319 − 2273 = **46** 行(= 測試檔數);前 613185 bytes = H0 ⇒ **前段逐位元組不變**。
  以 `Grep "result": "red"` 列出全帳本 red 紀錄,最後一筆在第 2266 行(< 2274)⇒ 新增 46 筆 **0 red、全 green**。
- test-sessions:12 − 11 = **1** 行;前 1413031 bytes = H0 ⇒ **前段逐位元組不變**。新增那一行的欄位頭與 invocation:

```
"kind": "session", "run_id": "7ec16d4b97d1478b893e354681623a78", "time": "2026-10-02T17:05:51.724830+00:00", "ticket_id": "145", "exit_code": 0
"invocation": {"args": ["tests"], "args_source": "TESTPATHS", "pyargs": false}
```

  ⇒ **〈十八之一〉的靜態推導在真實執行中得到印證**(固定指令 `config.args == ["tests"]`、`args_source == TESTPATHS`)。
  全帳本只有這一筆帶 `invocation`(先前的 session 由舊版 producer 產生,沒有這個欄位 ⇒ 涵蓋範圍未知)。
- 測試的假身分 / 假檔名 / 假 run_id 在兩本真實帳本中皆 **0** 筆。

全套後工作樹:`git status --porcelain` 無輸出。

### status.py 的 Evidence 與 Derived

`python .claude/portable/status.py --root .`(一處遮罩:`report:` 行的 HEAD 時間含本地時區偏移,以 `<本地時間>` 代替;`tests green under ticket 145` 的 46 檔清單以「(46 檔)」代替;其餘逐字):

```
=== Evidence ===
test-runs: 本票 red 0 / green 46 / run 事實未知 0 / orphaned 0 / schema 不合格 run 0;最後一筆 tests/test_verify_gates.py=green @ 2026-10-02T17:05:51.724830+00:00;最近一次 run:A(exit 0;collected 1952 / deselected 0 / passed 1946 / failed 0 / skipped 3)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl)
intercepts (當月): 1 筆  (source: .dev/intercepts-2026-10.jsonl)
intercepts (最新存在月): 2026-10 1 筆;末筆 R7@2026-10-02T12:12:16.405577+00:00  (source: .dev/intercepts-2026-10.jsonl)
exemptions: 總 281 筆;granted 240 筆;blocked 1 筆;未記錄(無此欄)40 筆;最後一筆 2026-09-24T08:17:49.073745+00:00  (source: .dev/gate-exemptions.jsonl)
provenance: 未記錄(上游無此檔屬正常)  (source: .dev/provenance.jsonl)
report: 2026-09-24T084909Z-ticket137-status-line.md;HEAD <本地時間>;回報後 18 筆  (source: .dev/reports/)

=== Derived ===
src write allowed in implement: yes  (source: gate.stage_allows_src_write() <- .agents/pipeline-stages.yaml)
tests red under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests green under ticket 145: (46 檔)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests green (run 事實未知) under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests orphaned under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
rules defined: R1 R2 R3 R4 R5 R6 R7 R8 R9  (source: gate.rule_codes())
```

`collected 1952` = 1946 passed + 3 skipped + 3 xfail(記為 `other`)。

### `git diff af839c6 --stat`

```
 .claude/hooks/redlight.py  | 164 ++++++++++++++++++++++++++++++++++++++++++++-
 .claude/portable/status.py | 122 +++++++++++++++++++++------------
 tests/conftest.py          |  31 ++++++++-
 tests/test_status.py       |   6 +-
 4 files changed, 277 insertions(+), 46 deletions(-)
$ git diff af839c6 --stat -- tests/test_redlight.py
(無輸出)
```

### 票 145 的 S4b-2 改動

第 3 行改為 `**狀態**:動工 —— Station 4b 修正完成(固定全套 exit 0);待 Station 5b 審查。`(舊行併入 F-036 block 第十代);
新增〈十九、Station 4b 修正〉;〈十〉Station 3b(含補件)改為 PASS / ACCEPTED、新增 Station 4b「修正完成，待審查」、「Station 3b 補件」行改為 PASS / ACCEPTED。

PRIVATE-CONTEXT CHECK:**PASS** —— 本輪新增文字只來自程式碼 diff、測試輸出、帳本與 status 輸出;本地時區偏移與 scratchpad 絕對路徑已遮罩;帳本只落帳 root 相對路徑。

---

## 尚未證明 / 本輪未做

1. **CLEAN 層**未證明;**REAL 層**留待 Jeff 端 status_all 確認。
2. **窄選(nodeid / `-k`)與中斷的真實 pytest 情形**未在真實執行上觀察過 —— 只由 3b 紅燈的 fake 驅動與串接測試證明。
3. **`--collect-only` 也會寫一筆 session**:在新規則下,它對碰到的檔可能為 `true` 涵蓋但沒有 passed ⇒ 不退紅、不 green(那些檔的最新證據會變成「run 事實未知」直到下一次全套)。本輪未另驗。
4. **〈十〉現況句**仍寫「Station 5 FAIL,回 Station 3b 補紅燈,Station 4b 未開始(與票頭第 3 行一致)」—— 與新第 3 行不一致;本刀授權外,未改,待裁。
5. **3b 刀③ 的程序違規**(`--check` 有輸出時 commit 的 6 筆)仍待裁。
6. `.dev/test-sessions.jsonl` 已達 1.87 MB(〈十七〉裁決 8 的 debt)。
7. 十六個 commit 均未推。

---

## 六站狀態

| 站 | 狀態 |
|---|---|
| Station 1 — Spec | PASS / CLOSED |
| Station 2 — Ticket | DONE |
| Station 3 — Red-light | PASS / ACCEPTED |
| Station 4 — Implementation | 實作嘗試完成,Station 5 FAIL |
| Station 5 — Review | FAIL |
| Station 3b — Red-light(補,含補件) | PASS / ACCEPTED |
| Station 4b — Implementation(修正) | 修正完成,待審查 |
| Station 5b — Review | NOT STARTED |
| Station 6 — Acceptance | NOT STARTED |
