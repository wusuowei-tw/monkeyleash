# 票 145 Station 4g —— host evidence policy 修正與本機驗收

- 日期:2026-10-04
- 對象:
  - S4G1 `f4fa0418aa037f95ef7d1f59c6fe6a812a80414c`:實作;
  - S4G1B `f581a02a5b7a65c8eaf150bf7231acc464f99072`:補紅燈 T1 / T2;
  - S4G1C `8e7775526e462d984abb0992ed74c1e1aa3648dd`:producer 修正(修法 B)。
  - 上一個 commit 是 S3G1B-2 `3eb112b1cafb399f2757274264281436729e7e42`。
- 合約:
  - 票 145〈四十八〉48.1 裁決 1–7、〈五十〉50.1;
  - 4g 續作裁決:R3 擋下後的還原與編輯規矩、第 7 鍵 `committed_addopts` 與 `addopts_overrides` 輸入合約、修法 B 與 T1 / T2;
  - 規劃檔 `docs/audits/2026-10-03-m1a-station3g-redlight-plan.md` P3 / P4 / P5 / P6。
- 範圍:**本機(Windows)驗收**。POSIX 外部 clean-room 驗收尚未執行(第 9 節)。**本報告不宣稱 4g 完成。**

## 【給裁決者】

1. 「哪些測試結果能當退紅證據」原本寫死成 agent-gates 自己的設定。現在改成每個 repo 自己提交一份 policy,框架只檢查它有沒有超出框架驗證過的範圍。
2. 本機全套 2094 passed、0 failed。原本的 35 支紅加上補的 1 支紅全部轉綠。status 顯示 policy 有效,票 145 底下沒有紅。
3. 淨室(全新安裝的乾淨 repo)第一次驗收時「正二」失敗:沒有 `-o` 類旗標的 repo 退不了紅。依裁決改在記錄端分清「沒有」與「取不到」之後,同一次淨室執行裡兩正三負全部成立。
4. 本 repo 的測試帳本只往後加,淨室驗收前後完全沒動。
5. 下一步是 POSIX 外部淨室驗收(由裁決助手執行)。通過後才升級狀態。

## 【給裁決助手】

### 1. 實作摘要(行號以 S4G1 為準;`tests/conftest.py` 以 S4G1C 為準)

**`.claude/hooks/redlight.py`**(S4G1 之後未再修改)

| 位置 | 內容 |
|---|---|
| `:493` `FRAMEWORK_CONFIG_FILES = ("pyproject.toml",)` | B 常數;取代 `CONFIG_FILE` |
| `:497` `BLOB_FILES` | producer 記 blob 的檔 = `FRAMEWORK_CONFIG_FILES + (ROOT_CONFTEST,)`;取代 `COMMITTED_FILES` |
| `:506`–`:507` `POLICY_FILE` / `POLICY_SCHEMAS` | I-1 / I-2 |
| `:512` `EVIDENCE_POLICY_KEYS` | 7 鍵(續作裁決 3) |
| `:524` `OVERRIDE_FLAGS` | 推導規則的旗標表(pytest 9.1.1) |
| `:715` `_git_bytes` | git 原始 stdout |
| `:726` `committed_blobs` | 逐路徑各一次 git(缺一檔不連坐) |
| `:749` `addopts_overrides(value)` | 只接受 `str` / `list[str]`;不讀 git / 檔案;推導不了 ⇒ None |
| `:791` `_committed_addopts` | `git cat-file blob HEAD:<config_file>` → `tomllib` → `[tool.pytest.ini_options].addopts` 原值。`""` = 段落在、沒有 addopts;None = 取得或解析失敗 |
| `:825` `evidence_policy_facts` | I-3 六步,只擷取事實,回傳 7 鍵 |
| `:874` `policy_document_problems` | (格式, 邊界);schema 不認得就不往下看;界外 ⇒ 整份不合格 |
| `:912` `policy_state` | status 行的六種狀態 |
| `:932` `policy_template` | 範本 = B 常數完整列舉;`committed_overrides: []` |
| `:945` `_effective_policy` | identity、格式、邊界、schema / version 一致、`committed_overrides == addopts_overrides(committed_addopts)`(`committed_addopts` 為 None ⇒ unknown) |
| `:972` / `:977` | `_effective`(B ∩ policy)、`_known_dists_accepted` |
| `:987` `_completeness_problems` | config_blobs 改驗 `ROOT_CONFTEST` 必在;`:1026` 新增 evidence_policy 7 鍵型別檢查 |
| `:1043` `_completeness_verdict` | `:1074` `policy = _effective_policy(...)`;(vii′)(xiii)(viii)(x)(xi)(xviii) 改為對 effective 判定;唯一的 `return "true"` 仍在 `:1127` |

- 刪除:`COMMITTED_ADDOPTS_OVERRIDES`、`CONFIG_FILE`、`COMMITTED_FILES`。
- `content_hash` 及其呼叫的函式未修改。

**`tests/conftest.py`**
- `:346` `_MISSING`、`:349` `_override_ini_of`(S4G1C;修法 B):先判屬性是否存在,再解讀值,只讀一次。
- `:406` `override_ini` 改經 `_override_ini_of`。
- `:411` `completeness["evidence_policy"]`(S4G1):舊版 redlight 沒有該函式 ⇒ None。

**`.claude/portable/status.py`**:`:560` `POLICY_SOURCE`、`:563` `_policy_line`、`:867` Evidence 區在 test-runs 行之後輸出 `evidence policy: <狀態>  (source: .agents/evidence-policy.json)`。

**`.claude/portable/install.py`**:
- `:386` `POLICY_TEMPLATE`、`:389` `_target_redlight`;
- `:399` `write_policy_template`:由目標 repo 的 `redlight.policy_template()` 產生,不另放範本來源檔;
- `:415` `write_decisions_pending(..., policy_file=None)`:一律加「evidence policy 未初始化」待決項,含 canonical 路徑;
- `:555` / `:572` 接線。

**`.claude/portable/verify_gates.py`**:
- `:286`–`:476` 新增:探針、正二的 policy(= 當下環境 ∩ B)、`_ev_red_then_green`、五個情境函式、`EVIDENCE_SCENARIOS`(`:446`)、`_ev_restore`、`run_evidence_scenarios`;
- `:613` 接在「框架測試在新 repo 跑一次」之後;每個情境各印一行,失敗訊息點名情境。

**`.agents/evidence-policy.json`**:= 規劃檔 P3 甲案範例(`config_file` `pyproject.toml`、`committed_overrides` `["strict_markers=true"]`、`python_versions` `["3.11"]`、`pytest_versions` `["9.1.1"]`、`dists` `[["anyio","4.15.0"]]`)。本 repo `HEAD:pyproject.toml` 的 `addopts = "-ra --strict-markers"` 推導值相同,步驟 F 的停手條件不成立。

**`.agents/portable-manifest.txt`**:`:106` `.agents/evidence-policy.json skip`、`:124` `.agents/evidence-policy.template.json generate`。

### 2. 授權改動對照(assertion / docstring / test identity 一律不改)

| 授權 | 位置(S4G1) | 內容 |
|---|---|---|
| G1 | `tests/test_redlight.py` `_D_POLICY_FILE` / `_D_BASELINE_POLICY`、`_d_committed_root`;`tests/test_status.py` `_T_POLICY_FILE` / `_T_BASELINE_POLICY` / `_T_BASELINE_ADDOPTS`、`_t_committed` | 寫入並提交與 baseline 相符的 policy |
| G2 | `tests/test_status.py` 兩支 completeness dict(`TestTestsUnderTicketUsesTheLatestRecordPerFile::test_a_file_that_went_red_then_green_counts_as_green`、`TestOrphans::test_a_renamed_red_test_is_orphaned_not_green`)+ helper `_t_policy_facts` | 只補 `evidence_policy`(含第 7 鍵) |
| G3 | `tests/test_redlight.py` `_isolated_conftest`;`tests/test_status.py` `_chain_conftest` | 固定 conftest 所見的 `sys.version_info` 為 3.11、`pytest.__version__` 為 9.1.1。測試在呼叫 driver 前自己設過 pytest 版本時不覆蓋(以模組載入時的真實版本判斷) |
| G4 | `tests/test_redlight.py` | 刪除 `TestCollectionDefinitionCoverage::test_d4_the_committed_addopts_override_constant_matches_pyproject` |
| G5 | `.agents/portable-manifest.txt` | 見第 1 節;`tests/test_host_evidence_policy.py skip` 已在 S3G1 加過,未重複 |

- 3g / 3g-1b 的 35 支與 `tests/test_host_evidence_policy.py` 一字未改。
- S4G1 的 `git diff --cached -- tests/` 全文可由 `git show f4fa041 -- tests/` 重現。

### 3. 第一次淨室驗收(S4G1)—— 正二不成立

`python .claude/portable/verify_gates.py <session scratch>/verify-gates`,exit 1。情境段原文:

```
=== 框架自己的測試,在這個新 repo 裡跑一次 ===
    1942 passed, 7 skipped, 3 xfailed in 399.28s (0:06:39)

=== evidence policy 淨室情境(兩正三負;每個情境各一行)===
    正一 未初始化                  成立 ✓  35 個框架測試檔皆 unknown=True;evidence policy: 未初始化
    正二 已初始化且相符               不成立 ✗  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 有效;1 passed in 26.91s
    負一 policy / 環境不符         成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 有效;1 passed in 0.34s
    負二 HEAD 有、工作樹不同          成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 工作樹與 HEAD 不同;1 passed in 0.30s
    負三 工作樹有、HEAD 沒有          成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 未提交;1 passed in 0.23s
```

- 同一輪的本機全套(S4G1):`2092 passed, 3 skipped, 3 xfailed in 392.31s (0:06:32)`。
- 本次負一到負三的「成立」**不作為證據**:成因相同,機制正確與否它們都會是 unknown。
- 細節見 `.dev/reports/2026-10-04T213043Z-ticket145-station4g-s4g1-local-pass-cleanroom-pos2-fail.md`。

**成因**:
- pytest 9.1.1 的 `-o` 是 `action="append"`,沒有 default(`_pytest/helpconfig.py:112-119`)。沒給任何 `-o` / OverrideIniAction 旗標時,`config.option.override_ini` 為 **None**。
- S4G1 的 producer 把 None 原樣交給 `normalize_overrides`,落帳 `null`。
- consumer (viii) 比 `None != []` ⇒ unknown。
- 本 repo 與 3g / 3g-1b 的正控都帶 `--strict-markers`,沒有一支走到這條路徑。

**裁決(Jeff)**:
- 修法 B = APPROVED:producer 先判欄位是否存在,再解讀值。
- A = REJECTED:在 consumer 把 None 當 [],等於丟掉 None 的來源資訊,會把「事實取不到」當成「確定沒有 override」⇒ fail-open。
- C = REJECTED:只是繞過缺陷。
- 授權新增 T1 + T2。負一到負三須在正二修好後的同一次淨室執行中重新驗證。

**裁決助手外部驗證**(Linux,Python 3.11 + pytest 9.1.1;隔離環境;**來源:Jeff 的 4g 續作指令;非本 repo 帳本證據、非獨立審查 finding**):
- pytest 9.1.1 不帶 `-o` 時 `config.option.override_ini` 為 None、屬性存在;帶 `-o xfail_strict=true` 時為 `['xfail_strict=true']`。
- 以 S4G1 的樹跑 verify_gates.py:正二不成立(`file_coverage=unknown`),與 Windows 一致。
- 套用 B 後跑 verify_gates.py:兩正三負全部成立,正二 `file_coverage=true`;test_redlight / test_status / test_install / test_verify_gates / test_host_evidence_policy 共 275 支全過。
- 原型測試:T1 在 S4G1 失敗、在 B 通過;T2 在 S4G1 與 B 都通過、在 A 失敗。

### 4. S4G1B 補紅燈

```
$ python -X utf8 -m py_compile tests/test_redlight.py
(無輸出)
$ git diff --cached --name-only
tests/test_redlight.py
$ git diff --cached --check
(無輸出)
$ git diff --cached -U0 -- tests/test_redlight.py   → 恰一個 hunk,只有 + 行
@@ -2492,0 +2493,42 @@ class TestAddoptsDerivation:
$ git commit -F .scratch/m1a-s4g/s4g-1b-msg.txt
[master f581a02] test(145): M1-a Station 4g-1b —— 「沒有任何 override」正控與「override 事實取不到」鎖(2 支)
 1 file changed, 42 insertions(+)
$ git rev-parse HEAD
f581a02a5b7a65c8eaf150bf7231acc464f99072
$ git status --porcelain
(無輸出)
```

- `TestEvidencePolicyNoOverride::test_g3_no_override_anywhere_is_full_coverage`(T1,behavior-red):addopts `-ra`、policy `committed_overrides: []`、`override_ini=None` ⇒ 必須 `"true"`。
- `TestEvidencePolicyNoOverride::test_g3_a_missing_override_fact_is_not_full_coverage`(T2,regression-lock):`override_ini` 屬性不存在 ⇒ 不得為 `"true"`。

**紅燈全套(S4G1B 上只跑一次)**:`python -X utf8 -m pytest -q > <session scratch>/s4g1b-run.txt 2>&1`,exit 1;之後 `git status --porcelain` 無輸出。照錄時第三行 `E` 的行尾空白已去除。

```
E       AssertionError: unknown
E       assert 'unknown' == 'true'
E
E         - true
E         + unknown

tests\test_redlight.py:2520: AssertionError
FAILED tests/test_redlight.py::TestEvidencePolicyNoOverride::test_g3_no_override_anywhere_is_full_coverage
1 failed, 2093 passed, 3 skipped, 3 xfailed in 342.54s (0:05:42)
```

- collected 2100。唯一的 FAILED 是 T1;T2 在 2093 passed 之內。

帳本(各自單獨執行):

```
$ head -c 787812 .dev/test-runs.jsonl > <session scratch>/r13.bin
$ head -c 10696010 .dev/test-sessions.jsonl > <session scratch>/s13.bin
$ sha256sum <session scratch>/r13.bin
d2cb491719cb9ec3c694b9ead332d08b41c8b5676603baebf42d126e627dc9f2 *<session scratch>/r13.bin
$ sha256sum <session scratch>/s13.bin
e593a945fc4dce41a7f4c0ae77d919e0c37c22da1f0c94cc3ed0561de4e6fa11 *<session scratch>/s13.bin
$ wc -l .dev/test-runs.jsonl
2968 .dev/test-runs.jsonl
$ wc -l .dev/test-sessions.jsonl
26 .dev/test-sessions.jsonl
$ wc -c .dev/test-runs.jsonl
799406 .dev/test-runs.jsonl
$ wc -c .dev/test-sessions.jsonl
11433570 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl
ab5070782e058c19090a82f139a717853f6fb1d07104e13cc7ff2a73c1d71bba *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
14fbbfb3ded7af07da0eac68c0b41a481c39ffd3f6d20c405658e12860de339d *.dev/test-sessions.jsonl
```

- 前段 sha256 = B13 ⇒ 只追加。
- test-runs 2921 → 2968(+47 行)、test-sessions 25 → 26(+1 行)。
- 跑後全檔記為 B14(799406 / 11433570;`ab507078…` / `14fbbfb3…`)。

### 5. S4G1C 修正

```
$ python -X utf8 -m py_compile tests/conftest.py
(無輸出)
$ git diff --cached --name-only
tests/conftest.py
$ git diff --cached --check
(無輸出)
$ git commit -F .scratch/m1a-s4g/s4g-1c-msg.txt
[master 8e77755] fix(145): M1-a Station 4g-1c —— producer 區分「沒有 -o」與「override 事實取不到」(修法 B)
 1 file changed, 22 insertions(+), 2 deletions(-)
$ git rev-parse HEAD
8e7775526e462d984abb0992ed74c1e1aa3648dd
$ git status --porcelain
(無輸出)
```

`git diff --cached` 全文(照錄時去除了行尾空白,以通過 `git diff --cached --check`:diff 的空白 context 行原為單一空格。原文可由 `git show 8e77755` 重現):

```
diff --git a/tests/conftest.py b/tests/conftest.py
index 64d5dd0..565deb3 100644
--- a/tests/conftest.py
+++ b/tests/conftest.py
@@ -342,6 +342,25 @@ def _flag(session, name):
     return bool(getattr(session, name))


+# 「屬性不存在」的 sentinel(票 145 Station 4g 修法 B):與「屬性存在、值為 None」分開。
+_MISSING = object()
+
+
+def _override_ini_of(option):
+    """交給 `normalize_overrides` 的 `override_ini` 原值。**先判欄位是否存在,再解讀值;只讀一次。**
+
+    pytest 9.1.1 的 `-o` 為 `action="append"`、沒有 default(`_pytest/helpconfig.py:112-119`),
+    未給任何 `-o` / OverrideIniAction 旗標時值為 None —— 語意是「沒有 override」,與「屬性取不到」不同:
+      - 屬性不存在 ⇒ None(事實取不到;consumer 判 unknown);
+      - 值為 None ⇒ 以 `[]` 交給 `normalize_overrides`,落帳 `[]`(事實取得成功:pytest 明確表示沒有 -o);
+      - 其他 ⇒ `normalize_overrides` 照舊(非 list ⇒ None)。
+    """
+    raw = getattr(option, "override_ini", _MISSING)
+    if raw is _MISSING:
+        return None
+    return raw if raw is not None else []
+
+
 def _completeness_of(session):
     """本次 session 的完整性事實。任何一步出錯 ⇒ None(寧可多紅,不讓 pytest 失敗)。

@@ -351,6 +370,8 @@ def _completeness_of(session):
     pyproject.toml 與本檔的工作樹 blob vs HEAD blob(git 子程序,失敗 ⇒ None);`pytest_version`
     取自本檔 import 的 `pytest`;`blocked` 是 `list_name_plugin()` 中值為 None 的名稱(`-p no:`)。
     路徑型事實一律轉成 root 相對路徑,不落帳絕對路徑。
+    `override_ini` 先判屬性是否存在(`_override_ini_of`):pytest 9.1.1 的 -o 為 action="append" 無 default,
+    未給時為 None,語意是「沒有 override」(落帳 `[]`),與「屬性取不到」(落帳 None ⇒ unknown)不同。

     票 145 Station 4e(〈三十五〉3 (xiv)–(xviii)、4)另記 pass 有效性的事實:`optimize` 與 `python_version`
     在此刻經模組層 `sys` 讀;`runxfail` / `pythonwarnings` / `trace` 隨 `COMPLETENESS_OPTIONS` 記在 `options`。
@@ -382,8 +403,7 @@ def _completeness_of(session):
             "plugins": _redlight.classify_plugins(_ROOT, name_plugins,
                                                   pm.list_plugin_distinfo()),
             "blocked": _redlight.blocked_plugins(name_plugins, _ROOT),
-            "override_ini": _redlight.normalize_overrides(getattr(option, "override_ini", None),
-                                                          _ROOT, inv_dir),
+            "override_ini": _redlight.normalize_overrides(_override_ini_of(option), _ROOT, inv_dir),
             "inifilename": _redlight.normalize_config_path(getattr(option, "inifilename", None),
                                                            _ROOT, inv_dir),
             "inipath": _redlight.normalize_config_path(getattr(cfg, "inipath", None), _ROOT),
```

- `redlight.py` 未改:consumer (viii) 維持 None ⇒ unknown。`normalize_overrides` 未改。
- 既有 option 替身(`_C_OPTION_DEFAULTS`、`_S_OPTION_DEFAULTS`)都沒有明寫 `override_ini=None`。缺屬性時仍落帳 None,行為不變。

### 6. S4G2 本機驗收(S4G1C 上)

**5a 固定全套(只跑一次)**:`python -X utf8 -m pytest -q > <session scratch>/s4g-run2.txt 2>&1`,exit 0;之後 `git status --porcelain` 無輸出。

```
2094 passed, 3 skipped, 3 xfailed in 341.79s (0:05:41)
```

- collected 2100(2094 + 3 + 3)。0 failed。輸出沒有任何 `FAILED` / `ERROR` 行。

**5b 帳本(以 B14 為前段基準;各自單獨執行)**

```
$ head -c 799406 .dev/test-runs.jsonl > <session scratch>/r14.bin
$ head -c 11433570 .dev/test-sessions.jsonl > <session scratch>/s14.bin
$ sha256sum <session scratch>/r14.bin
ab5070782e058c19090a82f139a717853f6fb1d07104e13cc7ff2a73c1d71bba *<session scratch>/r14.bin
$ sha256sum <session scratch>/s14.bin
14fbbfb3ded7af07da0eac68c0b41a481c39ffd3f6d20c405658e12860de339d *<session scratch>/s14.bin
$ wc -l .dev/test-runs.jsonl
3015 .dev/test-runs.jsonl
$ wc -l .dev/test-sessions.jsonl
27 .dev/test-sessions.jsonl
```

- 前段 sha256 = B14 ⇒ 只追加。
- test-runs 2968 → 3015(+47 行;47 個測試檔各一行)、test-sessions 26 → 27(+1 行)。

**5c status(節錄原文)**

```
test-runs: 本票 red 0 / green 47 / run 事實未知 0 / orphaned 0 / schema 不合格 run 0;最後一筆 tests/test_verify_gates.py=green @ 2026-10-04T22:04:53.003363+00:00;最近一次 run:A(exit 0;collected 2100 / deselected 0 / passed 2094 / failed 0 / skipped 3)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl)
evidence policy: 有效  (source: .agents/evidence-policy.json)
tests red under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests green (run 事實未知) under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
tests orphaned under ticket 145: (無)  (source: .dev/test-runs.jsonl + .dev/test-sessions.jsonl(票 145 ODC-1))
```

- 原本的 5 個紅檔都在 green:`tests/test_host_evidence_policy.py`、`tests/test_install.py`、`tests/test_redlight.py`、`tests/test_status.py`、`tests/test_verify_gates.py`。

**5d 淨室**

V0(各自單獨執行):

```
$ wc -c .dev/test-runs.jsonl
810925 .dev/test-runs.jsonl
$ wc -c .dev/test-sessions.jsonl
12171130 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl
9fa98cc71426865862deebbfcefcd78c49503251e6f20aca928656bb3ac93426 *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
27cccd2c1a1506f96d2628c608487ccd394af1da2280ebdc983aa02c6645198b *.dev/test-sessions.jsonl
```

`python .claude/portable/verify_gates.py <session scratch>/verify-gates2 > <session scratch>/s4g-verify2.txt 2>&1`,exit 0。末段原文:

```
=== 逐條實測(每條各擋一次)===
    R1   擋下 ✓
    R2   擋下 ✓
    R3   擋下 ✓
    R4   擋下 ✓
    R5   擋下 ✓
    R6   擋下 ✓
    R7   擋下 ✓
    R8   擋下 ✓
    R9   擋下 ✓

=== 權威層偵測(只驗未安裝路徑)===
    hook 刪掉        -> 偵測到沒裝 ✓(找不到 pre-commit(查過 .git/hooks/pre-commit))
    別人的 hook 佔位 -> 偵測到沒裝 ✓(.git/hooks/pre-commit 存在,但它不呼叫 gate.py —— 那是別人的 hook 佔著位子,不是本框架的權威層。)
    裝回去           -> 偵測到已裝 ✓

=== 框架自己的測試,在這個新 repo 裡跑一次 ===
    1944 passed, 7 skipped, 3 xfailed in 327.25s (0:05:27)

=== evidence policy 淨室情境(兩正三負;每個情境各一行)===
    正一 未初始化                  成立 ✓  35 個框架測試檔皆 unknown=True;evidence policy: 未初始化
    正二 已初始化且相符               成立 ✓  rc 1→0;file_coverage=true;red=(無);green=tests/test_evidence_probe.py;evidence policy: 有效;1 passed in 17.36s
    負一 policy / 環境不符         成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 有效;1 passed in 0.32s
    負二 HEAD 有、工作樹不同          成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 工作樹與 HEAD 不同;1 passed in 0.24s
    負三 工作樹有、HEAD 沒有          成立 ✓  rc 1→0;file_coverage=unknown;red=tests/test_evidence_probe.py;green=(無);evidence policy: 未提交;1 passed in 0.21s

全部 9 條規則各擋下一次,權威層偵測正常,框架測試在新 repo 全綠,evidence policy 兩正三負成立。
安裝位置:<session scratch>/verify-gates2/verify-gates-repo
```

- 五情境在**同一次**淨室執行中全部成立。
- 正二含 `file_coverage=true` 與 `green=tests/test_evidence_probe.py`。
- 負一到負三是在正二成立的同一次執行中得到的。

事後(各自單獨執行):

```
$ wc -c .dev/test-runs.jsonl
810925 .dev/test-runs.jsonl
$ wc -c .dev/test-sessions.jsonl
12171130 .dev/test-sessions.jsonl
$ sha256sum .dev/test-runs.jsonl
9fa98cc71426865862deebbfcefcd78c49503251e6f20aca928656bb3ac93426 *.dev/test-runs.jsonl
$ sha256sum .dev/test-sessions.jsonl
27cccd2c1a1506f96d2628c608487ccd394af1da2280ebdc983aa02c6645198b *.dev/test-sessions.jsonl
$ git status --porcelain
(無輸出)
```

⇒ 本 repo 兩本帳本前後 bytes 與 sha256 都等於 V0。

### 7. 程序紀錄

- R3 擋下與還原:S4G1 之前,第一次嘗試在 redlight.py 半改狀態被前哨 R3 擋下(`.dev/reports/2026-10-04T205524Z-ticket145-station4g-blocked-r3-self-import.md`)。依裁決以 `git restore` 丟棄半成品後重做。
- 重做採漸進遷移:新增 → 改引用 → 刪舊,每刀後以 `python .claude/portable/status.py --root .` 為 import 探針。
  - **違規**:3a–3c 三次寫入後沒有立刻探針。裁決已記錄並接受,本輪(S4G1B / S4G1C)沒有再寫 redlight.py。
- 淨室 `.dev/` 在目標 repo 是被追蹤的。證據情境之間以 `git reset --hard <基準>` 還原,所以單一情境的 session 不留存。結果只以每個情境當場印出的那一行為準。

### 8. 殘餘與未證明(依規劃檔 P7 與 4g 續作裁決;不擴張)

1. **閘門依賴 redlight.py 可 import**:`gate.head_content_hash` 經 `_redlight()` 載入工作樹的 redlight.py。半改狀態載不起來時,全部 R3 判定都會被擋。屬 fail-closed、照設計,不在本票修。
2. **status 的 `evidence policy: 有效` 只代表 policy 文件本身有效**:已提交、工作樹 = HEAD、schema / version 認得、在能力邊界內。它不代表本次 runtime 一定能取得 true authority。`committed_overrides` 與 HEAD addopts 推導是否一致,只在 verdict 時判定,status 行不檢查。屬追蹤項,**目前尚未 machine-enforced**。
3. **淨室負一到負三只斷言 unknown,不斷言 unknown 的成因**(追蹤項)。
4. **verify_gates 的 `SystemExit` 訊息**在 cp950 主控台重導向時為亂碼(既有行為)。
5. 規劃檔 P7 照舊、本票不處理:
   - 下游測試不在 `tests/` 底下時 producer 不載入;
   - 「無設定檔」不在能力邊界內;
   - 「人審」無法機器驗證;
   - sync 端沒有「需建立 evidence policy」提示;
   - logging 鎖步絆線(〈四十五〉45.3)**目前尚未 machine-enforced**,實作時須放進宿主專用檔;
   - `tests/test_leak_scan.py` 的宿主樹掃描在下游的意義;
   - 機器化 pre-push;
   - TOCTOU 與未 pin 版本;policy 改了但未 commit 的期間無法退紅。
6. **G3 的殘餘**:driver 固定的是 `_isolated_conftest` / `_chain_conftest` 預設所見的版本。測試事後以 `_e_sys(version_info=None)` 換掉 `sys` 的那些(例:3e 的 optimize 對照組),仍讀真實 Python 版本。在 3.11 以外的直譯器上,它們的正控是否仍綠:**未證明**。
7. **`addopts_overrides` 推導不了的寫法**(合併短旗標 `-qo x`、長旗標縮寫):方向是 unknown(fail-closed),不是假綠。
8. **本機只驗 Windows**。POSIX 的淨室結果目前只有裁決助手的原型驗證(第 3 節),不是本樹的實測。

### 9. POSIX 外部 clean-room 驗收

> **舊文字(F-036,保留不刪)**:本節標題原為 ~~`### 9. POSIX 外部 clean-room 驗收:待執行(裁決助手)`~~,沒有內文。
> 2026-10-04 S4G4 依 Jeff 裁決改為下方照錄段落。

POSIX 外部 clean-room 驗收（裁決助手；隔離環境；非本 repo 帳本證據）——2026-10-04 約 18:50 ET
- 環境：Linux，Python 3.11.16，pytest 9.1.1，anyio 4.15.0。
- 受測樹：以公開 repo de36ebcbab284ef11064a9943b5191750482dd93 的 clone 為底，覆蓋 Windows 工作樹於 S4G3 時點的 12 個程式 / 測試 / 設定檔（.claude/hooks/redlight.py、.claude/portable/install.py、.claude/portable/status.py、.claude/portable/verify_gates.py、tests/conftest.py、tests/test_redlight.py、tests/test_status.py、tests/test_install.py、tests/test_verify_gates.py、tests/test_host_evidence_policy.py、.agents/portable-manifest.txt、.agents/evidence-policy.json；CRLF→LF）。docs 未同步（不影響程式行為）。
- verify_gates.py：R1–R9 各擋下一次；權威層偵測三項成立；淨室框架測試 1945 passed、4 skipped、3 xfailed、0 failed；evidence policy 兩正三負全部成立：
    正一 未初始化 成立（35 個框架測試檔皆 unknown；evidence policy: 未初始化）
    正二 已初始化且相符 成立（rc 1→0；file_coverage=true；green=tests/test_evidence_probe.py；evidence policy: 有效）
    負一 policy / 環境不符 成立（file_coverage=unknown；紅仍在）
    負二 HEAD 有、工作樹不同 成立（file_coverage=unknown；evidence policy: 工作樹與 HEAD 不同）
    負三 工作樹有、HEAD 沒有 成立（file_coverage=unknown；evidence policy: 未提交）
- 宿主固定全套（Linux）：collected 2100；2084 passed、13 failed、3 xfailed。13 支為 tests/test_gate.py::TestAuthorityLayerIsWired::test_this_repo_itself_is_wired 與 tests/test_known_items_regression.py 的 12 支；同一沙盒在 4g 之前的已推送版本 de36ebc 上同樣恰為這 13 支失敗 ⇒ 屬沙盒環境因素（推測：clone 未設 hooksPath、缺本機私有資料），與 4g 無關。evidence 相關 5 檔（test_redlight / test_status / test_install / test_verify_gates / test_host_evidence_policy）全過。
- 先前的 S4G1 Linux 重現（正二不成立、成因 override_ini 為 None）與修法 B 原型驗證，見〈五十一〉51.1 / 證據報告。
- 結論：POSIX 外部 clean-room 驗收 PASS。
