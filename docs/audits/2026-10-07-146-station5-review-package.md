# 票 146 第五站審查包(S5-146-0)

- 日期:2026-10-07
- 讀者：沒看過本票過程的獨立審查者。
- 審查標的:HEAD `c84af106799f26c4a4c682f4b32aa95338bca20a`。實作在 `982a661d438783902247a1da7e4a023bc7961a9d`。
- 票：`docs/tickets/framework-updates/146-claude-code-enforcement-integrity.md`(下稱「票」;行號以 `c84af10` 為準)。
- 4b 審計：`docs/audits/2026-10-07-146-station4b-implementation.md`(下稱「4b 審計」)。
- 本包只整理、指路，不下判定;第 8 節的題目由審查者作答。

## 0. 一段話說明 146 在做什麼

Claude Code 會從幾個「靜態入口」載入擴充:`~/.claude/dev-mods`、`~/.claude/skills`、`~/.claude/commands`、`~/.claude/{skills,plugins}/synced`、專案 `.claude/settings*.json` 的 hook、`.mcp.json`。146 新增規則 **R10**:pre-commit 以 HEAD 已提交的兩份 policy 為唯一 authority,逐一核對這些入口。

- `.agents/extension-allowlist.json`:檔案型入口以 (path, sha256) 授權。
- `.agents/extension-inventory.json`:synced 以匿名邏輯路徑 + sha256 納管。

處置分兩類:

- 未登記 ⇒ 擋(走一般 violations,受影子規則)。
- 觀測失敗、authority 缺失、synced 未納管或驗證不過 ⇒ fail-closed 硬擋，不受影子豁免。

只改兩份 policy 的 commit 走 policy-only 通道，以 index 中的候選 policy 判定(H-6)。

不變式(票 :262-264):只證明「已知靜態入口符合 committed policy」;runtime 實際載入集合恆為 UNPROVEN。

## 1. 範圍:commit 清單(`git log --oneline 02a3265..HEAD`,新到舊，共 36 個)

| 完整 SHA | 用途 |
|---|---|
| `c84af106799f26c4a4c682f4b32aa95338bca20a` | S4b-146-2:4b 審計、票狀態列、豁免帳本隨行 |
| `982a661d438783902247a1da7e4a023bc7961a9d` | S4b-146-1:R10 接線(六個 production 檔 + 准改測試 + 票) |
| `8e7b2937c2bdfab8c926aa834c02cf7df36fb37e` | S3g-146-1:3g 紅燈(淨室隔離、安裝器最小 policy、R10 情境原因斷言、policy-only 通道) |
| `2b7c9f8d3a28aaa2595b609ca44568f3fd44f535` | G-0:manifest 把兩份 canonical policy 分類為 skip |
| `4cb59eb5da307511140b2cb0f418d009e18a0f2a` | Jeff 核准並提交兩份 policy(本機觀測快照) |
| `54a79b253079ae7f0e1f13a8e07dff4ea98e0dc4` | 3f-2 驗收、D-1～D-3 裁決、4b 允許修改清單 |
| `3cbf89b0aebdb46f1bd81163f2290795dbca5d95` | 3f-2 紅燈審計 |
| `b5eb69d0c32b75b95251d65facec4edf3895cae6` | 3f-2 紅燈(synced_dirs 成對、空根、無效 / 重複根名、部分根走訪) |
| `09a3dc57469239eb4696e76c0ffaef87c21fff69` | 3f-2 裁決 C-1～C-6 入票 |
| `31877271441c1050255b027611ac3cd1ae681e8d` | 3f 紅燈審計 |
| `0a8a494237db7d50aedefc9f4056bc39c7f421cd` | 3f 紅燈(inventory、邏輯路徑、逐檔驗證、硬擋) |
| `8e1c286391666ee5da62eb032f1421c9375ea682` | 3f 裁決 + v2 synced 契約入票 |
| `41c8d9bd3c5fd160a464abec4cefe870ed27b8c1` | 3f-0 synced 納管偵查 |
| `05e752ca3b67ad01da8ed4679529c82336a1a56e` | 3e 紅燈審計 |
| `f625c19c10b60c0df5e0818dbc9b0e3b7d84951b` | 3e 紅燈(category、extension_report、claude_root、R10、fail-closed、status 兩行) |
| `ea2366e769b124ea8fb000b67e1061f93ab7b027` | 3e 裁決 + v1 接線契約入票 |
| `d5e890d353e42836fc0441271aa09b729f39a955` | 3e-0 接線設計偵查 |
| `624dfc35e0df94d83196977bec1beefd156bf72a` | 4a 核心實作審計 |
| `6d45a7adb7453ff87a76b44255d7448036bbf483` | 4a 修正:rule_codes 掃 gate + redlight;allowlist 違規優先於 surfaces 不完整 |
| `ff7f2bbf74dc4a51c17a5247e626c07765dc5024` | 4a-2 紅燈(優先序) |
| `44e9c87c9f4db56cfc9b838d9e2d832332a4a6fc` | 4a 核心:path+sha256 allowlist、surfaces、四態、R4 樹比對下沉 redlight |
| `2bb757ce55074bffcf99674ce87008df3e0d322d` | 3d 紅燈審計 |
| `449a2e67c6e95f783a46216c64f166f667d0111e` | 3d 紅燈(同欄位 path 重複 ⇒ malformed) |
| `ba86638e9444047410bebf937786f05caf511956` | 3d 裁決(path 唯一、symlink 走訪、原因優先序) |
| `bef44c8f2d45216d7581655fcccf2a6fd44a6b79` | 3c 紅燈審計 |
| `e79c393d800c7c68fbf7afe6f5d9082afbaa6a03` | 3c 紅燈(T146-9/13 修正、path+sha256 綁定、canonical path) |
| `ea41d5a08f4720cc7da3e686d001a346599870cf` | 3c 停點裁決 |
| `f6cd57a755a9501bb0811d5527c2f18607e7c56f` | 3c 裁決(紅燈來源、path+sha256、canonical path) |
| `db34bb9fa8aa388fab1eefe936924f75eec490d8` | 3b 紅燈審計 |
| `8727882f9643f3aa386b546fd2bac0b99438972c` | 3b 紅燈(user skills / commands、依賴方向、完整性) |
| `dc81b19e5195c666051f9a508f8dd0953db8df85` | 3b 裁決(方向 B) |
| `ad8bf70c29bbb89294b168e82fe3c7973222b202` | 第三站紅燈審計 |
| `0993d217a27bce8119587bf1553df49a3521e79e` | 第三站紅燈(v0 契約) |
| `441c2b44f36a64cd8a194d37d1a62776b6d6a76a` | 第三站停點裁決 C(測試併入 test_redlight.py) |
| `22e9624fefa94afcb9964f1c3f396007d9f894c5` | Q1–Q6 裁決、四態機、v0 介面契約入票 |
| `db134904ebb79dc5dea8adf43e64e4ce4fcf6581` | 設計 v0 / 紅燈規格(D-146-0) |

## 2. 契約索引(票內節標題與行號)

| 節(行號) | 它鎖什麼 |
|---|---|
| 設計 v0 裁決 :252 / Invariant :262 | 納入五條管道;停在可證明的靜態邊界;VERIFIED 不可達;policy 只認 HEAD blob;R4 擴為遞迴樹比對;靜態與 runtime 分欄 |
| Q1–Q6 裁決 :270 | 共用唯讀 facts 層(gate / status 共用);synced 未納管 ⇒ UNKNOWN;IDE lock 只顯示;前哨只警告、pre-commit fail-closed、status 必顯示;policy 生效須 Jeff 核准(procedural);指紋模型 |
| 狀態機 :280 | VIOLATION > UNKNOWN > DECLARED_OK;VERIFIED 無回傳路徑 |
| v0 介面契約 :288 | redlight.py 的 EXT_* 常數、`extension_allowlist_facts`、`extension_state`、`extension_status_lines`、`extension_surface_facts` 名稱與形狀;facts 模組落點 = redlight.py |
| 已知盲區 :313 | `--plugin-dir`、claude.ai connector、`mcp__` 前綴不證明來源、VERIFIED 只有 regression lock |
| 3b 裁決 :335 / 增補後 :348 | 補 user skills / commands 兩入口;依賴方向 B(redlight 不載入 gate);surfaces 完整性前提 |
| 3c 裁決 :369 / 例子表 :379 | 授權比對是 (path, sha256) 對;canonical path 規則;T146-13 改 AST 掃描;紅燈 blob provenance |
| 3d 裁決 :409 | 同欄位 path 唯一;symlink 目錄記 (relpath, None) 不追;status 原因與 state 共用第一原因函式 |
| 4a 裁決 :429 | rule_codes 掃兩檔聯集;allowlist 違規優先於完整性 UNKNOWN;豁免帳本不得刪改並隨 commit 進版(裁決 (s));四個實作判斷入契約 |
| 3e 裁決 :463 | category 兩類 UNKNOWN、observation_missing 與 unmanaged_entry 擋 pre-commit、新代號 R10、home 來源只有參數或 `~/.claude`、判定一次(z1)、authority 缺失獨立硬擋(z2)、列舉失敗不洗成空(z3)、補鎖 1–6 |
| v1 接線契約 :486 | `_walk_regular`、八鍵 surfaces、`_extension_first_reason` 九步、`extension_report`(含前置觀測)、gate 的 `rule_sources` / `_extension_claude_root` / `check_extension_integrity` 硬擋 (a)(b)(c)(d)、`mode_pre_commit` 呼叫點、status 兩行 |
| 3f 裁決 :547 / v2 synced 契約 :565 | inventory 檔與匿名邏輯路徑四種;bucket 結構規則;`synced_verification` 六鍵;第 8 步改依納管結果;(d) 改為 synced 驗證不過即硬擋 |
| 3f-2 裁決 :603 / 契約修訂 :613 | `synced_dirs` 為 (root_name, path) 對;空根 ⇒ 空集合;結構錯誤 ⇒ 該根不走訪、另一根照常 |
| 3f-2 驗收 / D-1～D-3 :642 / 4b 允許修改清單 :651 | 4b 准改第 1–13 項;policy 草稿規矩 |
| G-0 :681 / Jeff 裁決 :697 | manifest 分類;G-1 淨室隔離家目錄、G-2 安裝器最小 policy、G-3 R10 情境原因斷言 + 乾淨正控、G-4 root 不存在即 invalid(安裝器只說明前提) |
| 3g 裁決補件 :734(含 H-6 定案 :736) | policy-only 通道條件與硬擋順序;隔離契約四點;`run_scenario` 對 R10 要求 marker + 原因;安裝器完整驗 inventory |
| 3g 契約 :811 | verify_gates / install / redlight / gate 的 3g 名稱與流程(4b 只能實作) |
| 第四站 4b 實作 :870 起 | 4b 範圍、補件三～五(准改第 14–18 項) |

## 3. 實作對照表

行號以 `c84af10` 為準。「契約」欄引票內節名。

### 3.1 `.claude/hooks/redlight.py`

| 函式 / 常數(行) | 契約 | node |
|---|---|---|
| EXT_ALLOWLIST_* / 四態常數(:1024 起) | v0 :288 | T146-0a |
| EXT_CAT_* / EXT_CATEGORIES / EXT_RUNTIME_UNPROVEN / EXT_SURFACE_KEYS | v1 :486 | T146-34 |
| EXT_INVENTORY_* / EXT_SYNCED_ROOTS / EXT_BUCKET_TOKEN | v2 :565 | T146-40 |
| EXT_POLICY_SOURCES | 3g :811 | T146-71、72 |
| `EXT_INVENTORY_UNCHECKED`(:1065) | v2 :565 | T146-45 |
| `_error_text`(:1093) | v1(errors 的 error_text) | T146-32c |
| `_walk_regular`(:1099) | v1、v2(read_bytes) | T146-32a/b/c/d/e、3、11、12 |
| `skill_mirror_violations`(:1160;gate 同名為薄包裝 :3721) | v0、3b 方向 B | T146-5、6、9、13 |
| `_canonical_relpath_ok`(:1238)/ `_extension_allowlist_ok`(:1253) | 3c (k)、3d (m) | T146-2c、15c、16 |
| `_logical_path_ok`(:1280)/ `_extension_inventory_ok`(:1295) | v2、3g(完整驗證) | T146-40、73、58[e] |
| `_policy_facts`(:1323)/ `extension_allowlist_facts`(:1409)/ `extension_inventory_facts`(:1414) | v0、v2、3g(index 模式) | T146-1、2、2b、2c、40、71 |
| `_hook_commands`(:1419) | v0(project_hook_commands) | T146-24、23b(DECLARED_OK 佈置) |
| `_synced_root`(:1431) | v2、3f-2 | T146-41、42、42b、46、47 |
| `extension_surface_facts`(:1487) | v0、3b、v1、3f-2 | T146-9、11、11c、14、41、46 |
| `synced_verification`(:1561) | v2 | T146-43、42b |
| `_extension_first_reason`(:1594) | v1 九步、3d (o)、4a (r)、v2 第 8 步 | T146-17、35、31、44 |
| `_extension_render_lines`(:1639) | v1 | T146-7、24 |
| `extension_state`(:1649)/ `extension_status_lines`(:1654) | v0、v2(相容 wrapper) | T146-4、4b、7、8、45 |
| `extension_report`(:1660) | v1、v2、3g | T146-24、27、31、36、44、72 |

### 3.2 `.claude/hooks/gate.py`

| 函式(行) | 契約 | node |
|---|---|---|
| `rule_codes`(:1329,改) | 4a (q) | T146-33 |
| `rule_sources`(:1357) | 3e 補鎖 4、v1 | T146-29 |
| `EXT_POLICY_PATHS`(:4048) | 3g、五處閉合第 1 點 | T146-74 |
| `_extension_claude_root`(:4051) | v1 | 只以注入使用(T146-21 等);production 回 None 的效果見 §4.3 本機探測 |
| `_staged_names_all`(:4056) | 3g | T146-62 |
| `extension_policy_only_commit`(:4062) | H-6、3g | T146-61 |
| `check_extension_integrity`(:4068) step 0 | v1、3g step 0 | T146-26 |
| 同上 (a) 前置觀測失敗 | v1 | T146-22、69 |
| 同上 (c) 列舉錯誤 | v1、補鎖 2 | T146-37 |
| 同上 (d) synced 驗證 | v2 | T146-23、23c～23i、38 |
| 同上 VIOLATION / DECLARED_OK | v1 | T146-21、38b、38c、24b |
| 同上 policy-only (e)(f) / 放行 | 3g step 4 | T146-63、64、65、66、66b、66c、68、70 |
| 同上 混合 commit 走 head | H-6 | T146-67 |
| `mode_pre_commit`(:4134,改) | v1、3g | T146-25、70、23b |

### 3.3 `.claude/portable/status.py`

| 函式(行) | 契約 | node |
|---|---|---|
| `_EXT_SOURCE` / `_EXT_RUNTIME_PREFIX`(:671) | v1 status | T146-30、20(第 14 項斷言) |
| `_extension_claude_root`(:675) | v1 | 注入使用(T146-20/28/30);第 15 項 autouse |
| `_extension_lines`(:680)、`_enforcement`(:700,改) | v1、Q4 | T146-20、20b、28、30 |
| docstring :16 / :19 / :36 | 3e 裁決 7 | 無行為 node(文件) |

### 3.4 `.claude/portable/verify_gates.py`

| 函式 / 常數(行) | 契約 | node |
|---|---|---|
| `ISOLATED_HOME_DIRNAME` / `ISOLATION_MARKER`(:235)、`current_isolation`(:241) | 3g | T146-50、50b |
| `_lkind`(:245) | 3g(lstat 型別判斷的實作細節) | T146-50b、51b |
| `isolated_home`(:263) | 3g | T146-50、50b、50c、50d |
| `_require_isolation`(:308)/ `restore_user_layer`(:328) | 3g、隔離契約第 1 點 | T146-51、51b |
| `scenario_r10`(:339)/ `precontrol_r10`(:353)/ `SCENARIOS["R10"]` | 3g、G-3 | T146-53、53b、54、33 |
| `EXPECTED_MARKER` / `EXPECTED_REASON` / `PRECONTROL`(:374) | 3g、補件裁決 | T146-54 |
| `run_scenario`(:632) | 3g | T146-55 |
| `main`(:659)/ `_main_isolated`(:675) | 3g、G-1 | T146-52、52b |

### 3.5 `.claude/portable/install.py`

| 函式(行) | 契約 | node |
|---|---|---|
| `_settings_hook_commands`(:415) | 3g(hook 清單來源) | T146-56、58[a] |
| `write_extension_policy`(:440)與呼叫點(:643) | 3g、G-2、隔離契約第 4 點 | T146-56、58 |
| `write_decisions_pending`(:488,增段) | 3g | T146-57 |
| `verify`(:547,G-4 提示句 :556) | G-4 | 見 §3.7 |

### 3.6 `CLAUDE.md`

R10 一列 ⇒ 契約為 4b 准改第 11 項;node 為 `tests/test_claude_md.py` I-1b(正典段要提到新代號)。

### 3.7 審查重點:無 node 的程式 / 無 node 或無實作的契約

**無 node 的程式**(都在 4b 寫入;行為為讀碼【推論】):

1. `gate.mode_pre_commit`:`_staged_names_all()` 失敗 ⇒ `[R10/fail-closed]` 硬擋(4b-1 新增，契約沒有明寫)。
2. `gate.check_extension_integrity` :4093:`extension_report` 丟例外 ⇒「146 判定器執行失敗」硬擋。契約只寫載入失敗那一支。
3. 同函式 :4122:(b) 的「state == UNKNOWN 且無其他原因」分支。production 的 surfaces 鍵集合固定，正常路徑走不到。
4. 同函式 :4076-4080:`staged_names=None` 且 git 失敗 ⇒ policy_only=False(退回較嚴的 head 路徑)。
5. `install._settings_hook_commands`:settings.json 讀不到或不是 JSON ⇒ SystemExit(4b 審計詮釋 i3)。
6. `install.verify` :556 的 G-4 前提句(契約 G-4 有，沒有 node)。
7. `redlight.extension_report`:「`~` 沒展開」以 `startswith("~")` 判定(v1 有此句;4b 審計 i1);沒有 node 直接注入未展開的家目錄。
8. `verify_gates`:R10 擋下時多印兩行(v3);`main` 的隔離範圍延伸到巢狀測試與 evidence 情境(v1)。T146-52 / 52b 只鎖「install 之前已進入」與「載入 gate 在隔離內」。
9. gate / status 的 `_extension_claude_root` production 回 None:單元 node 都改用注入，fallback 的效果只有本機唯讀探測(§4.3,`claude_root_source: 'fallback'`)與 redlight 側的 T146-27。

**無 node 或無實作的契約**:

1. Q3「IDE lock 只顯示，不判定」:146 的程式沒有任何 IDE lock 顯示或判定(Grep `ide.?lock` 只命中 gate.py:310 的副檔名表)。
2. Q4「前哨只警告」:v1 改為「mode_hook 不呼叫它」(T146-25 鎖住不在前哨)。前哨目前不對 R10 發任何警告，等於 Q4 的前半句被 v1 取代。審查者可判斷這算契約演進還是缺口。
3. v0 裁決 1 的 `CLAUDE_CODE_PLUGIN_DIRS`:列為盲區(3f 裁決 (nn)、票 :556),沒有觀測實作;v1 裁決 6 明定 home 來源不納環境變數。
4. POSIX 才跑得到的 node,在 Windows 都 skip,目前沒有 POSIX 實跑證據:
   - T146-50b[home-is-symlink]、T146-51b[vi-home-symlink]:隔離 symlink 拒絕、realpath 在 workdir 之下;
   - T146-42 的 symlink 案、T146-43[v-symlink];
   - T146-9;
   - T146-32e(chmod 000)。

## 4. 驗證證據(HEAD 口徑分明)

### 4.1 正式結果 —— `982a661d438783902247a1da7e4a023bc7961a9d`

`python -X utf8 -m pytest -q -rs` ⇒ `2309 passed, 12 skipped, 3 xfailed in 257.78s`(0 failed、ERROR 0)。12 skipped 全為 Windows 平台限制(4b 審計 §3.1 逐項)。

`c84af106799f26c4a4c682f4b32aa95338bca20a` 只提交審計 / 票 / 豁免帳本(3 檔:`.dev/gate-exemptions.jsonl`、`docs/audits/2026-10-07-146-station4b-implementation.md`、票),**沒有另跑正式 pytest**。

### 4.2 淨室(4b 審計 §3.2)

`python .claude/portable/verify_gates.py <scratchpad>/vg-4b`,rc 0。R10 段原文:

```
    R10  擋下 ✓
         正控放行 ✓(同一佈置、家目錄未放情境物)
         [R10/fail-closed] unmanaged_entry：未受管入口：synced（額外 2 / 缺少 0 / 內容不符 0）
```

- 十條規則各擋下一次。
- 新 repo 框架測試 `2159 passed, 16 skipped, 3 xfailed`;evidence 兩正三負成立。
- 結束後隔離 `home/.claude` 為空、marker 仍在。
- staged 為空時 R10 仍硬擋，實測見 4b 審計 §4。

### 4.3 本機 report / status 一致(4b 審計 §3.3)

`check_extension_integrity([])`(production 唯讀觀測真實使用者層):

- `hard_block None`、`violations []`、`policy_source 'head'`、`DECLARED_OK`;
- `synced.verified True`;
- status 兩行的值與 `report["lines"]` 一致,runtime 前綴只出現一次，來源皆含 `redlight.extension_report`。

### 4.4 pre-commit 乾跑與 commit(4b 審計 §3.4)

- 乾跑 rc 0,只有 `[R2/自我修改豁免] .claude/hooks/gate.py`,沒有 `[R10`。
- commit 1 與 commit 2 都經 hook 提交，沒有 `--no-verify`。

### 4.5 帳本(4b 審計 §3.5、§3.4)

- `test-runs.jsonl` / `test-sessions.jsonl`:上一輪長度的前綴 sha256 與上一輪 LC 相同(`396acd94…` / `17c41443…`),只追加。
- `gate-exemptions.jsonl`:290 → 291(乾跑)→ 292(commit 1 hook),隨 commit 2 進版;commit 2 的 hook 未追加。

## 5. 准改清單 1–18

★ = 未經獨立紅燈(斷言是 4b 時新加或改寫的)。

| 項 | 改了什麼 | 為何在清單內 |
|---|---|---|
| 1 | `tests/test_r5_mounts.py` `_wire_pre_commit` 加 R10 替身 | 3e-0 Q-F 隔離點;R10 會在臨時 repo 硬擋、搶走 rc |
| 2 | `tests/test_gate.py` `_d_silence_the_neighbours` 加替身 | 同上 |
| 3 | `tests/test_stage_defs_source.py` `_PRE_COMMIT_STUBS` 加替身 | 同上 |
| 4 | `tests/test_gate.py` R6 接線 node 加替身 | 同上 |
| 5 | `tests/test_gate.py` `_blocked_stderr` 加替身 | 同上 |
| 6 | `tests/test_status.py` `_make_root` 不改 | 裁決 (ee):維持「redlight 缺失」分支 |
| 7 | T146-23 / 38 佈置改合法 bucket + marker,加「額外 2、非結構錯誤」 | 裁決 (aaa) |
| 8 | T146-24b 刪五行 | 裁決 (bbb) |
| 9 | `_root` docstring、inventory 縮排 | 裁決 (bbb) |
| 10 | T146-23 / 38 docstring | 裁決 (zz) / 第 7 項 |
| 11 | `CLAUDE.md` R10 列 | I-1b 連動 |
| 12 | `verify_gates.SCENARIOS["R10"]` | T146-33 / test_gate :1317 連動 |
| 13 | status.py :16 / :19 / :36 | 3e 裁決 7 |
| 14 ★ | T146-20 加「`runtime loaded set: ` 恰出現 1 次」 | Jeff 新裁 |
| 15 ★ | `tests/test_status.py` 模組層 autouse `_t146_isolated_claude_root` | 補件三:51 個 `_root_with_redlight` 呼叫點與 :572 會讓 status 讀真實 `~/.claude` |
| 16 ★ | `test_gate.py` R9 接線 node:spy + R10 替身 + `len(calls) >= 1` | 補件三:避免 rc 1 來自 R10 的假綠 |
| 17 ★ | `test_the_rule_stays_inside_r7`:移除 `"R10" not in codes`,改驗 python -c 訊息含 `"[R7/"` | 補件四、五;補件四寫的 `"[R7]"` 與實測訊息格式不符，已更正 |
| 18 ★ | T146-67:期待原因改 `inventory worktree_differs`,加 `[R10/fail-closed]` 與 `inventory.state == "worktree_differs"` | 補件四;3g 預判與 v2 head 模式語意矛盾 |

逐行文字見 4b 審計 §2。

## 6. 已知限制與未做

- runtime 實際載入集合恆為 UNPROVEN;VERIFIED 不可達(只有行為鎖 + 結構鎖，不是形式證明)。
- 盲區:`CLAUDE_CODE_PLUGIN_DIRS`、`--plugin-dir`、claude.ai connector、`mcp__` 前綴不證明來源(票 :313、:556)。
- 下游機器只要有 synced 或其他未登記入口，接上 146 之後的第一個 commit 就會被擋，須由人審閱並以 policy-only commit 登記。
  - 安裝器只給「空 inventory + 自身 hook」的最小 policy(G-2)。
  - 「policy 由 Jeff 親自核准」仍是 procedural invariant,未 machine-enforced(Q5、H-6)。
- CI 尚未跑(尚未 push)。
- POSIX 未驗(symlink / chmod 案在 Windows skip,見 §3.7)。

## 7. 審查重點(待裁，不立項)

- 淨室安裝會把本機 `.dev/reports/*.md` 與 `.dev/test-runs.jsonl` / `.dev/test-sessions.jsonl` 帶進目標 repo:安裝輸出「來源的 .gitignore 蓋住了這些框架檔，已強制帶過去」。
  - 這是既有安裝器行為,4b 未改動(4b 審計 §5)。
  - 請審查者評估是否另立票。
- §3.7 列出的無 node 程式與無 node / 無實作契約。

## 8. 審查者必答題

每題附上「從哪裡看」,答案由審查者自行判定。

- **(a) z1:判定一次、顯示消費同一結果是否成立?**
  - 看 `redlight.extension_report` :1660(`_extension_first_reason` 呼叫次數)、`status._extension_lines` :680、`gate.check_extension_integrity` :4092。
  - node:T146-31、44、28。
- **(b) 四個硬擋條件 (a)(b)(c)(d) + policy-only (e)(f) 是否都不受影子豁免?**
  - 看 `gate.mode_pre_commit` :4134(hard_block 在影子分支之前 return 1)、`check_extension_integrity` :4098-4128。
  - node:T146-22、23、37、38(影子開)、70(policy-only + 影子)。
  - 對照：未登記走 violations、受影子規則(T146-38c)。
- **(c) 隔離家目錄的 `_require_isolation` 是否可被偽造?**
  - 看 `verify_gates` :263-337(身分比對 `iso is _ACTIVE_ISOLATION`、marker token、lstat、realpath、expanduser)。
  - node:T146-51b(偽造 SimpleNamespace、context 結束、env 移動、marker 改動);symlink 案在 Windows skip。
- **(d) policy-only 通道是否可被混合 commit 繞過?**
  - 看 `gate.extension_policy_only_commit` :4062(staged 非空且 ⊆ 兩路徑)、`mode_pre_commit` 傳入 `_staged_names_all()`(含刪除)。
  - node:T146-61、62、67、68;安裝層 T146-60b。
- **(e) 安裝器最小 policy 是否登記了任何觀察值?**
  - 看 `install.write_extension_policy` :440(inventory entries 為 [],三個檔案型欄位與 mcp 為 [],hook 清單取自目標 settings.json)。
  - node:T146-56、58。
- **(f) 任何 production 路徑是否會寫入真實 `~/.claude`?**
  - 看 redlight 的 facts / surfaces(唯讀走訪)、`verify_gates.restore_user_layer` / `scenario_r10`(只在 `_require_isolation` 通過後寫隔離根)、`install.write_extension_policy`(只寫目標 repo)。
  - node:T146-53、51b;淨室結束狀態見 §4.2。
- **(g) index 缺失 / 衝突 / 非 regular / 讀取失敗，以及目錄列舉失敗，是否都可讀地 fail-closed,而不會被舊 wrapper(`extension_state` / `extension_status_lines`)或例外路徑洗成通過?**
  - 看 `redlight._policy_facts` :1323(index 六態)、`_walk_regular` :1099(onerror)、相容 wrapper :1649-1658(傳 `EXT_INVENTORY_UNCHECKED`)、`gate.check_extension_integrity` :4091-4096(例外 ⇒ 硬擋)。
  - node:T146-71、66、66b、32a～32e、45;例外分支無 node(§3.7 第 2 點)。
