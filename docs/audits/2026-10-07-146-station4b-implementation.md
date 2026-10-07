# 票 146 第四站 4b 實作審計(S4b-146-1)

- 日期:2026-10-07
- 實作 commit(commit 1):`982a661d438783902247a1da7e4a023bc7961a9d`
- 基準 HEAD:`8e7b2937c2bdfab8c926aa834c02cf7df36fb37e`(S3g-146-1)
- 契約來源：票 146 v1 / v2 / 3f-2 / 4b 允許修改清單(累積)/ G-0 / 3g;S4b 指令;補件三、四、五。
- 本審計是 4b 的落地紀錄，不是第五站的獨立審查。

## 1. production(六檔)

| 檔 | 內容 |
|---|---|
| `.claude/hooks/redlight.py` | v1 / v2 / 3g 契約全部名稱:EXT_* 常數、`_walk_regular`、`_policy_facts`(head / index)、`extension_allowlist_facts` / `extension_inventory_facts(policy_source)`、`_synced_root`、`extension_surface_facts`、`synced_verification`、`_extension_first_reason`(九步)、`_extension_render_lines`、兩參數相容 wrapper、`extension_report`(十四鍵) |
| `.claude/hooks/gate.py` | `rule_sources`、`EXT_POLICY_PATHS`(純字串常數)、`_extension_claude_root`、`_staged_names_all`、`extension_policy_only_commit`、`check_extension_integrity`(0→5 步)、`mode_pre_commit` 呼叫點(staged 之後、逐檔 check / 影子 / R4 之前;取不到 staged 全集 ⇒ 硬擋) |
| `.claude/portable/status.py` | R10 兩行(`extension integrity (R10)` / `runtime loaded set`,runtime 值去掉固定前綴);redlight 缺失 ⇒ 一行「未記錄(146 判定器不在)」;docstring :16 / :19 / :36 以 F-036 方式修訂 |
| `.claude/portable/verify_gates.py` | 3g:`isolated_home` 等隔離名稱、`scenario_r10` / `precontrol_r10`、`EXPECTED_MARKER` / `EXPECTED_REASON` / `PRECONTROL`、`run_scenario(target, code, iso=None)`、`main` 包在 `isolated_home` 內 |
| `.claude/portable/install.py` | `write_extension_policy`(呼叫點在 `write_policy_template` 之後、第一個 `git add -A` 之前);`write_decisions_pending(..., extension_policy=)` 增段;`verify` 在 `[R10/fail-closed] claude_root_invalid` 時加 G-4 前提句 |
| `CLAUDE.md` | R9 之後加 R10 一列(文字依 S4b 指令逐字) |

### 1.1 詮釋點(契約未寫死、由實作取定)

- (i1) `extension_report` fallback 時,「`~` 沒展開」以 `expanduser("~")` 結果 `startswith("~")` 判定。
- (i2) claude_root 以 lstat 判斷：必須是非 symlink 的目錄;symlink 判為 `claude_root_invalid`。
- (i3) `install._settings_hook_commands`:目標 `.claude/settings.json` 讀不到或不是 JSON ⇒ SystemExit(fail-closed;在寫入任何 policy 之前)。
- (v1) `verify_gates.main` 的隔離範圍：從 `install.main` 一路到 evidence 五情境結束(含權威層偵測與巢狀框架測試)。契約「到最後一條情境」取最寬讀法。
- (v2) `run_scenario` 對 R1–R10 都傳 iso;`restore_user_layer` 依契約「iso 非 None ⇒」無條件執行。
- (v3) R10 擋下時，報表多印「正控放行」一行，以及含 `[R10/fail-closed]` 的原始行。
- (v4) workdir 下已有非空 `home/` ⇒ SystemExit(契約行為),所以同一個 workdir 不能重跑。
- (v5) 正控 commit 會留在目標歷史;情境 commit 時 staged 為空，仍由 R10 硬擋 —— 見 §4 實測。
  - staged 為空時 gate 仍跑 R10,是已裁的全局入口檢查行為(補件三)。

## 2. 測試准改(逐行)

- 第 1 項 `tests/test_r5_mounts.py` `_wire_pre_commit`:加 `check_extension_integrity` 替身(回 `{"hard_block": None, "violations": [], "report": None, "policy_source": "head"}`)。
- 第 2 項 `tests/test_gate.py` `_d_silence_the_neighbours`:同款替身。
- 第 3 項 `tests/test_stage_defs_source.py` `_PRE_COMMIT_STUBS`:加 `"check_extension_integrity"` 同款替身(`*a, **k`)。
- 第 4 項 `tests/test_gate.py` R6 `test_the_rule_is_actually_invoked_at_the_authoritative_layer`:同款替身。
- 第 5 項 `tests/test_gate.py` `_blocked_stderr`:同款替身。
- 第 6 項 `tests/test_status.py` `_make_root`:不改;維持只複製 gate.py ⇒ status 走「redlight 缺失」分支。
- 第 7 項 `tests/test_gate.py` T146-23 / T146-38:
  - synced 佈置由 `manifest.json` 改為合法 bucket(`b1/SKILL.md` + `.bucket-b1`);
  - 保留原硬擋斷言，加 `額外 2 in err and 結構錯誤 not in err`;
  - T146-38 保留未登記 dev-mod 與 shadow=True。
- 第 8 項 `tests/test_gate.py` T146-24b:刪除重複寫入並提交 inventory 的五行，保留 `rc == 0`。
- 第 9 項 `tests/test_gate.py` `TestTicket146Integration._root`:docstring 移除緊湊 JSON 說明;inventory 改回 indent=2。
- 第 10 項 docstring:T146-23 / 38 隨第 7 項修訂。
- 第 11 項 `CLAUDE.md` R10 列(連動 `tests/test_claude_md.py` I-1b)。
- 第 12 項 `verify_gates.SCENARIOS["R10"]`。
- 第 13 項 `status.py` :16 / :19 / :36 字句。
- 第 14 項 `tests/test_status.py` T146-20:加 `assert rt[0].count(u"runtime loaded set: ") == 1, rt` —— **此斷言未經獨立紅燈，屬准改**。
- 第 15 項(補件三)`tests/test_status.py`:模組層 autouse、function scope 的 `_t146_isolated_claude_root`,只換 `status._extension_claude_root` 為 `tmp_path / "_t146_isolated_claude_root"`(空目錄);不改 HOME / USERPROFILE;T146-20 / 28 / 30 的 `_inject` 以各自注入為準;`:572` 的 fixture 由它覆蓋。
- 第 16 項(補件三)`tests/test_gate.py` `TestFrictionNumbersAreUnique::test_the_rule_is_actually_invoked_at_the_authoritative_layer`:spy 包住 `check_friction_numbers`,加同款替身，新增 `assert len(calls) >= 1`,保留 `rc == 1` —— **未經獨立紅燈，屬准改**。
- 第 17 項(補件四、五)`tests/test_gate.py` `TestInlineInterpretersAreUndecidable::test_the_rule_stays_inside_r7`:移除 `"R10" not in codes`,保留 `"R7" in codes`,加 `msg = gate.bash_write_violation('python -c "print(1)"')`、`assert msg and "[R7/" in msg, msg` —— **未經獨立紅燈，屬准改**。
- 第 18 項(補件四)`tests/test_gate.py` T146-67:
  - 期待原因由「額外 2」改為 `"inventory worktree_differs"`;
  - 加 `"[R10/fail-closed]" in hb` 與 `res["report"]["inventory"]["state"] == "worktree_differs"`;
  - 保留 `policy_source == "head"`;
  - docstring 補「混合 commit 走 HEAD 路徑：工作樹 inventory ≠ HEAD ⇒ identity 先判 worktree_differs」。

清單外未改任何測試。

## 3. 驗證

### 3.1 前檢證據(工作樹;不是正式結果)

| 次 | 指令 | 結果 |
|---|---|---|
| 1 | `python -m pytest -q -rs`(漏 `-X utf8`) | `2 failed, 2307 passed, 12 skipped, 3 xfailed in 274.40s` —— `test_the_rule_stays_inside_r7`(清單外)與 T146-67,停下 ⇒ 補件四 |
| — | `s4b-wt-pytest-2.txt` | 沒有產生：補件四的 `"[R7]"` 與實測矛盾，重跑前停下 ⇒ 補件五 |
| 3 | `python -X utf8 -m pytest -q -rs` | `2309 passed, 12 skipped, 3 xfailed in 249.98s`;ERROR 0 |

12 skipped 全為 Windows 平台限制，每項原因印在輸出中:
- `tests/test_gate.py:451 / :459 / :473`:此環境無法建立 symlink。
- `tests/test_redlight.py:2673`:Windows 檔名不得含 LF。
- `tests/test_redlight.py:3074`、`:3702` ×3、`:3752`:Windows 建 symlink 需要額外權限。
- `tests/test_redlight.py:3505`:chmod 000 在 Windows 不會讓目錄不可列舉。
- `tests/test_verify_gates.py:383 / :461`:Windows 建 symlink 需要額外權限(3g 新增)。

### 3.2 淨室(`python .claude/portable/verify_gates.py <scratchpad>/vg-4b`;rc 0)

- 規則清單 `R1 R2 R3 R4 R5 R6 R7 R8 R9 R10`,十條各「擋下 ✓」。
- R10 段 raw:

  ```
      R10  擋下 ✓
           正控放行 ✓(同一佈置、家目錄未放情境物)
           [R10/fail-closed] unmanaged_entry：未受管入口：synced（額外 2 / 缺少 0 / 內容不符 0）
  ```

- 框架測試在新 repo:`2159 passed, 16 skipped, 3 xfailed in 235.04s`。
- evidence 五情境皆「成立 ✓」。
- 結束後 `vg-4b/home/` 只有 `.claude/`(空)與 `.verify-gates-isolated`(32 bytes);輸出中的隔離家目錄行為 `…\scratchpad\vg-4b\home`。

### 3.3 report / status 一致性(scratchpad 唯讀探測;production 唯讀觀測真實使用者層，准於本步)

- `check_extension_integrity([])` 的結果:
  - `hard_block: None`、`violations: []`、`policy_source: 'head'`;
  - `report.state: 'DECLARED_OK'`、`claude_root_source: 'fallback'`、`surfaces.errors: []`;
  - `facts` blob `40dec504c85cfca3910d2d85fc446cc9af791510`,`inventory` blob `c474b8351e4a2171a02485480e2088413ef059fb`,兩者皆 `ok`;
  - `synced: {'verified': True, 'reason': None, 'missing': 0, 'extra': 0, 'mismatch': 0, 'structure_errors': 0}`。
- status 兩行各 1 行:
  - 第一行值 == `lines[0]`、runtime 值 == `lines[1]` 去前綴，皆 True;
  - `runtime loaded set: ` 在該行出現 1 次;
  - 兩行來源皆含 `redlight.extension_report`。

### 3.4 pre-commit 乾跑與 commit 1

- `git diff --cached --name-only`:與 L1 一致(六個 production 檔 + 四個測試檔 + 票 + `.dev/gate-exemptions.jsonl`,共 12 檔)。
- `python .claude/hooks/gate.py --pre-commit`:rc 0,輸出只有一筆 `[R2/自我修改豁免] .claude/hooks/gate.py`;沒有 `[R10`。
- 乾跑新增 1 筆豁免紀錄，已一併 add(290 → 291 行)。
- `git diff --cached --check`:無輸出。
- commit 1 經 hook 提交(沒有 `--no-verify`):`982a661…`,12 files changed。
- commit 1 自己的 pre-commit 追加 1 筆(291 → 292 行),依裁決 (s) 隨 commit 2 進版。

### 3.5 正式結果(committed HEAD `982a661…`)

- `python -X utf8 -m pytest -q -rs`:`2309 passed, 12 skipped, 3 xfailed in 257.78s`,與 3.1 第 3 次數字相同。
- 帳本只追加(`head -c` 取上一輪長度的前綴後 sha256):
  - `test-runs.jsonl` 前 1090986 bytes ⇒ `396acd9440ee5f4c48f0b52c9cebc3da4506db1034c0080ab969affd7f24cdc7`(與上一輪 LC 前綴 `396acd94…` 相符);現長 1125678 bytes,整檔 `00ba3d7116b6483737013b65627a1de6bdcfa796e8cc1197ffce8e100b22a3ad`。
  - `test-sessions.jsonl` 前 27987001 bytes ⇒ `17c414437d10630eeccd4acddbd6d5910a8c58f2268b120dba0d6782958120a8`(與 `17c41443…` 相符);現長 30400720 bytes,整檔 `32c6fc0508536cf7aabcfcdecfaa0edd883f8253ece9111a02314f3c8cdc0f64`。

## 4. (v5) 實測

淨室目標 repo `git log --oneline --name-status`:最上面是 `ea14bb1 verify R10 precontrol`(`M .dev/pipeline.json`、`A docs/adr/verify-trigger.md`),之下是安裝的兩個 commit。

- 情境 commit 時 repo 側內容與正控相同,synced 兩筆在隔離家目錄 ⇒ staged 為空。
- 輸出仍含 `[R10/fail-closed] … 額外 2`,情境 commit 沒有落地(HEAD 停在正控)。
- ⇒ git 在 staged 為空時仍執行 pre-commit hook,gate 也照跑 R10。

## 5. 待裁 / 偏離

- **3g 審計 C0 的預判漏項(T146-67)**:3g 紅燈把混合 commit 的原因預判為「額外 2」,與 v2 契約(head 模式 inventory 六態;`worktree_differs` ⇒「synced 未納管」)矛盾。
  - BASELINE 紅因(API 不存在)沒有驗到這一段斷言。
  - 4b 前檢實測轉紅後，依補件四第 18 項改寫;HEAD identity 契約不動。
- **前檢第一次漏 `-X utf8`**:用了 `python -m pytest -q -rs`,cp950 主控台重導向使中文成亂碼。之後一律 `python -X utf8 -m pytest -q -rs`。
- **補件四的 `"[R7]"` 是指令錯誤**:R7 內嵌直譯器的訊息實測為 `[R7/內嵌直譯器] …`(含 `[R7/`、不含 `[R7]`)。VS 以實測更正，補件五改為 `"[R7/"`;Jeff 先前核准的精確子字串同樣作廢。
- **補件三的成因**:接線後 status 對含 redlight 的 tmp root 以 `claude_root=None` fallback 到真實使用者層。清單外有 `_root_with_redlight` 51 個呼叫點、`:572` fixture、`test_gate.py:3702`,4b-2 在跑 pytest 之前停下 ⇒ 第 15、16 項。
- **口徑**:3.1 第 3 次與 3.5 皆 0 failed。T146-67 經第 18 項改寫後，在前檢與正式結果中皆通過。本審計不另行宣稱 146 紅燈的總數。
- **觀察(不在本票範圍)**:淨室安裝輸出列出「來源的 .gitignore 蓋住了這些框架檔，已強制帶過去」,其中包含本機 `.dev/reports/*.md` 與兩本測試帳本。目標在 scratchpad,這是既有安裝器行為,4b 沒有改動。

## 6. 狀態

146 已接線並正式驗證;待第五站獨立審查;尚未宣告生效。不 push。
