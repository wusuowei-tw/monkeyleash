# 票 146 第五站獨立審查(S5-146-1)

| 欄 | 值 |
|---|---|
| 日期 | 2026-10-07 |
| 審查者 | 本視窗(Claude Code session);**未參與票 146 任何前站**,只依 repo 內證據判斷 |
| HEAD | `eb3a3dbc5482e9475d62418a6c4911ab264dba4b`(`git rev-parse HEAD` 實測相符;`git status --porcelain` 執行前、pytest 後、寫檔前三次皆無輸出) |
| 與審查包標的的差 | 審查包寫的標的是 `c84af10`;`eb3a3db` 只多了審查包本身(`git show --stat`:1 file, 307 insertions)。審查包的行號在本 HEAD 逐一抽對皆相符 |
| 寫入 | 只有本檔(不 commit)與 `.dev/reports/2026-10-07T154152Z-ticket146-s5-1-independent-review.md`;探測程式與殘留目錄只在 session scratchpad |
| 結論 | **PASS-with-notes**(阻擋項 0;後補 / 待裁項見 §結論) |

---

## 第一段【給裁決者】

1. 146 的六個 production 檔與五個測試檔都讀完了;正式 pytest 跑一次:`2309 passed, 12 skipped, 3 xfailed`、0 failed,帳本只追加(前綴指紋相符)。
2. 審查包七題 (a)–(g) 有五題成立、兩題附條件成立:(d) 在「HEAD 還沒有某份 policy」時,用 `git mv` 把別的檔改名成 policy 可以讓混合 commit 走進 policy-only 通道(實測);(c)(f) 在 Windows 上把隔離 `.claude` 換成 junction(Windows 的目錄捷徑)就能讓清理碰到隔離外(實測型別,未實際刪除)。
3. 兩者都要「已經不正常的前置狀態」才走得到,判為不阻擋;**要你決定**:(d) 那一個旗標(`--no-renames`)是第六站前修(A)還是列後補(B)。
4. 另有一個**不屬 146 的既有洞**被本次實測坐實:權威層與 leak scan 的 staged 清單看不到改名的檔(票 140 A-1 當時標「未實測」)。建議另立票,優先級高於 146 的所有後補項。
5. PASS-with-notes 不是推送授權。

---

## 第二段【給裁決助手】

### 1. 讀過的檔案

- 審查包:`docs/audits/2026-10-07-146-station5-review-package.md`(全文)
- 票:`docs/tickets/framework-updates/146-claude-code-enforcement-integrity.md` :245–937(設計 v0 起到補件五,全部契約與裁決)
- 審計:`docs/audits/2026-10-07-146-station4b-implementation.md`(全文)、`docs/audits/2026-10-07-146-station3g-redlight.md`(全文);為 (j) 另查 `2026-10-06-146-station3e-redlight.md` :70、:117 與 `2026-10-06-146-station3f-redlight.md` :104、:130、:134
- `CLAUDE.md` 規則表(R10 列)
- production:
  - `.claude/hooks/redlight.py` :1015–1718(146 全段)
  - `.claude/hooks/gate.py` :1325–1378(`rule_codes` / `rule_sources`)、:2083–2102(`_redlight`)、:3996–4037(`staged_paths`)、:4040–4209(R10 接線與 `mode_pre_commit`)、`expanduser` 全部命中(:2364、:3132)
  - `.claude/portable/status.py` :1–57(docstring)、:671–740
  - `.claude/portable/verify_gates.py` :114–132、:229–411、:620–795
  - `.claude/portable/install.py` :110–225、:405–704
  - `.claude/portable/scanner.py` :485–514、`.claude/portable/leak_scan.py` :315–344(為 (k) O-1)
  - `.agents/portable-manifest.txt`(`settings`、`.dev` 命中)
- 測試(146 類別全部):
  - `tests/test_redlight.py` :2804–2943、:3380–4130(`TestTicket146ExtensionIntegrity` 3e/3f/3f-2 段、`TestTicket146IndexPolicy`)
  - `tests/test_gate.py` :6584–7187(`TestTicket146Integration`、`TestTicket146SyncedGovernance`、`TestTicket146PolicyOnlyLane`)、:3975–4027
  - `tests/test_status.py` :3203–3324(`TestTicket146StatusLines`)
  - `tests/test_install.py` :480–508(`g3_installed_repo`)、:700–945(`TestTicket146InstallPolicy` 與 helper)
  - `tests/test_verify_gates.py` :300–649(`TestTicket146Cleanroom`)
- diff:`git diff 8e7b293 982a661 -- tests/test_gate.py tests/test_status.py tests/test_r5_mounts.py tests/test_stage_defs_source.py`(准改第 1–18 項的測試側)
- 為 (k) O-1:`docs/tickets/framework-updates/140-sixth-station-2026-09-13-inventory.md` :38–51

### 2. pytest 與帳本前綴證明

執行(恰好一次):`python -X utf8 -m pytest -q -rs > <scratchpad>/s5-review-pytest.txt 2>&1`,背景執行,exit code 0。

尾段原文:

```
SKIPPED [1] tests\test_gate.py:451: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:459: 此環境無法建立 symlink
SKIPPED [1] tests\test_gate.py:473: 此環境無法建立 symlink
SKIPPED [1] tests\test_redlight.py:2673: Windows 檔名不得含 LF;本案例由 POSIX 驗收證明(〈六十一〉61.3 裁決 2)
SKIPPED [1] tests\test_redlight.py:3074: Windows 建 symlink 需要額外權限;POSIX 才產得出來
SKIPPED [1] tests\test_redlight.py:3505: chmod 000 在 Windows 不會讓目錄不可列舉;POSIX 才產得出來
SKIPPED [3] tests\test_redlight.py:3702: Windows 建 symlink 需要額外權限;POSIX 才產得出來
SKIPPED [1] tests\test_redlight.py:3752: Windows 建 symlink 需要額外權限;POSIX 才產得出來
SKIPPED [1] tests\test_verify_gates.py:383: Windows 建 symlink 需要額外權限;POSIX 才產得出來
SKIPPED [1] tests\test_verify_gates.py:461: Windows 建 symlink 需要額外權限;POSIX 才產得出來
2309 passed, 12 skipped, 3 xfailed in 250.45s (0:04:10)
```

與 4b 審計 §3.5 在 `982a661` 的數字(`2309 passed, 12 skipped, 3 xfailed`)相同;12 個 skip 的位置與原因與 4b 審計 §3.1 列表逐項相同。

帳本(單位:bytes;雜湊為 sha256):

| 檔 | 執行前大小 | 執行前整檔 | 執行後大小 | 執行後整檔 | `head -c <執行前大小>` |
|---|---|---|---|---|---|
| `.dev/test-runs.jsonl` | 1125678 | `00ba3d7116b6483737013b65627a1de6bdcfa796e8cc1197ffce8e100b22a3ad` | 1137197 | `5bc5e6a6b84b3934a52260d8ec0e268e44b3cbe35e4633d328950e186cf607d8` | `00ba3d7116b6483737013b65627a1de6bdcfa796e8cc1197ffce8e100b22a3ad` |
| `.dev/test-sessions.jsonl` | 30400720 | `32c6fc0508536cf7aabcfcdecfaa0edd883f8253ece9111a02314f3c8cdc0f64` | 31205293 | `6f4701153e33c049efe60155aca5be508794f4abdf778c31757265a67ce9a4a3` | `32c6fc0508536cf7aabcfcdecfaa0edd883f8253ece9111a02314f3c8cdc0f64` |

⇒ 兩檔的前綴與執行前整檔相同,只追加(test-runs +11519 bytes、test-sessions +804573 bytes)。
附帶核對:執行前的大小與整檔雜湊,和 4b 審計 §3.5 記的「現長 1125678 / `00ba3d71…`」「現長 30400720 / `32c6fc05…`」逐字相同 —— 4b 正式跑之後到本次之間,兩本帳沒有任何寫入。

### 3. 探測(全部在 scratchpad;以 `python -X utf8 -I` 執行)

| 程式 | 量什麼 | 結果(原文) |
|---|---|---|
| `probe_rename.py` | `_staged_names_all` 同款指令與 `staged_paths` 同款指令在 `git mv` 下列出什麼(git 2.53.0.windows.2;本 repo 沒有 `diff.renames` 設定,`git config --get-all diff.renames` exit 1) | 見 (d) 與 (k) O-1 |
| `probe_junction.py` | Windows junction 在 `verify_gates._lkind` 與 realpath 下的型別 | 見 (c) |
| `probe_allowlist_shadow.py` | HEAD 模式下 allowlist 非 ok 與 inventory 非 ok 各走哪條路 | 見 (g) 與 (k) N-2;結束時清理 scratchpad 失敗(git 物件唯讀,`PermissionError: [WinError 5]`),殘留只在 scratchpad |
| `probe_mutant_43.py` | T146-43[iv-content] 的斷言能否分辨「有比 sha256」與「只比存在」 | 見 (j) |

真實 `~/.claude`:**未讀、未列舉**。production 的 `check_extension_integrity` 會雜湊使用者層內容,超出本輪「只可列舉目錄名與檔案數」的許可,所以審查包 §4.3 的本機一致性結果**未獨立重現**,只引用 4b 審計 §3.3。

---

### 4. 必答題

#### (a) z1:判定一次、顯示消費同一結果 —— **成立**

- `redlight.extension_report` 在觀測有效時恰好呼叫一次 `_extension_first_reason`(`redlight.py:1714`),`lines` 由同一個 `(state, category, reason)` 渲染(`:1716`);前置觀測失敗時在 `:1695-1699` 先 return,呼叫 0 次。
- gate:`check_extension_integrity` 呼叫一次 `extension_report`(`gate.py:4092`),之後只讀 `report` 的欄位(`:4098-4131`),不另判定。
- status:`_extension_lines` 呼叫一次 `extension_report`(`status.py:690`),只取 `report["lines"][0]` / `[1]`(`:691`)。
- production 不經相容 wrapper:`extension_status_lines` / `extension_state` / `EXT_INVENTORY_UNCHECKED` 在 `.claude/` 下只出現在 redlight 自己的定義(Grep 命中 `redlight.py:1062/1065/1599/1629/1649/1651/1654/1656`,gate / status 零命中)。
- node:T146-31(計數 == 1 / 無效 0)、T146-44(計數 == 1 且收到 `report["inventory"]`)、T146-28(status 呼叫次數 == 1,與 gate 消費的 report 同 state、同第一行)。三者本輪皆綠。
- 附註(不構成不成立):`synced_verification` 在同一次 report 裡最多被呼叫兩次 —— `_extension_first_reason` 第 8 步內一次(`:1633`)、`report["synced"]` 一次(`:1717`)。兩次的輸入是同一個 `inventory` 與同一個 `surfaces` 物件、函式無副作用,結果必然相同;gate 的 (d) 讀的是後者。它不是第二次「判定」,但「判定一次」的字面若要嚴格到函式層級,這是唯一的例外。

#### (b) (a)(b)(c)(d) 與 policy-only (e)(f) 不受影子豁免 —— **成立**

- 所有硬擋都在 `mode_pre_commit` 的影子分支之前 return 1:`gate.py:4160-4163`(R10 硬擋)vs `:4182-4189`(影子分支)。`_staged_names_all()` 失敗也在之前硬擋(`:4155-4159`)。
- 對應:(a) `:4098-4100`;(b)(c)(d) `:4112-4128`;(e)(f) `:4101-4111`。
- node(影子開):T146-22(a)、T146-23 / T146-38(d)、T146-37(c)、T146-23c~23i(d 的各型)、T146-70(policy-only (e) + `mode_pre_commit`)、T146-26(判定器缺失)。
- 對照:未登記走 `violations`(`:4129-4130`),受影子規則 —— T146-38c 實證影子開 ⇒ rc 0 且 shadow-log 有 R10。
- 缺口(不阻擋):(b) 的「UNKNOWN 且無其他原因」分支(`:4122-4123`)沒有 node,production 走不到(見 (h) 第 3 項);(f) 沒有「影子開」的 node,但與 (e) 同一個 return(`:4111`)。

#### (c) `_require_isolation` 可否被偽造 —— **成立(身分不可偽造);附 Windows junction 缺口,不阻擋**

- 身分:`iso is _ACTIVE_ISOLATION`(`verify_gates.py:310`),偽造的 `SimpleNamespace` 被拒(T146-51b[iii-forged-namespace]);context 結束後被拒(T146-51b[iv]);marker 刪除 / 改內容被拒(T146-51b[i][ii],`:319-323`);環境被移走被拒(T146-51b[v],`:324-325`)。
- 路徑:只有 `realpath(iso.home)` 被要求位於 `realpath(workdir)` 之下(`:312-315`);`iso.claude_root` 只用 `_lkind` 判「非 symlink 的目錄」(`:316-318`),**沒有 realpath 檢查**。這與 3g 契約字面一致(契約只寫 `realpath(iso.home)`)。
- 實測(`probe_junction.py`):

  ```
  mklink /J rc=0
  _lkind(home/.claude junction) = dir
  os.path.islink = False
  realpath(home/.claude) = <scratchpad>\probe-junction\outside\claude
  realpath 在 wd 之下 = False
  listdir(home/.claude) = ['sentinel.txt']
  sentinel 仍在 = True
  ```

  ⇒ 在 Windows 上,若有人在 context 期間把 `<wd>/home/.claude` 換成指向隔離外的 junction,`_require_isolation` 的每一道檢查都會過(`_lkind` 回 `dir`),而 `restore_user_layer`(`:331-336`)會清空 junction 目標的內容。**本探測沒有呼叫 `restore_user_layer`,「會清空」是讀碼推論**;型別與 realpath 是實測。
- 判定:要「隔離目錄在執行中被別人改掉」才走得到,而那個人本來就能直接動真實使用者層 ⇒ 不阻擋,列後補 N-3。
- POSIX symlink 版本(T146-50b[home-is-symlink]、T146-51b[vi-home-symlink])在 Windows skip,本輪沒有 POSIX 實跑;junction 在 Windows 不需額外權限,這兩個 node 可以改用 junction 在 Windows 實跑(後補)。

#### (d) policy-only 通道可否被混合 commit 繞過 —— **不成立(邊界情境);不阻擋,但列為 146 範圍內最嚴重的一項,交裁決 A/B**

- 一般混合(policy + 其他檔)正確走 HEAD:`extension_policy_only_commit`(`gate.py:4062-4065`)要求 `set(names) ⊆ EXT_POLICY_PATHS`;T146-61[both-plus-x / docs-plus-allowlist]、T146-67、T146-68 皆綠。刪除有被列入(T146-62)。
- 但 `_staged_names_all` 用 `git diff --cached -z --name-only`(`gate.py:4058`),**沒有 `--no-renames`**。實測(`probe_rename.py`,case A:HEAD 沒有 allowlist、`git mv docs/draft-allowlist.json .agents/extension-allowlist.json`):

  ```
  _staged_names_all 同款指令(無旗標)        names=['.agents/extension-allowlist.json']  policy_only=True
  加 --no-renames                     names=['.agents/extension-allowlist.json', 'docs/draft-allowlist.json']  policy_only=False
  name-status: 'R100\tdocs/draft-allowlist.json\t.agents/extension-allowlist.json'
  ```

  ⇒ 改名的**來源檔刪除**不在清單裡,這個混合 commit 被判成 policy-only。違反 H-6 定案「混入任何其他檔仍用 HEAD」(票 :742)。
- 可達範圍(讀碼推論):rename 的目的路徑必須是**新增**的(HEAD 已有的路徑只會顯示為 M,不會配成 R),所以只在 HEAD 缺那份 policy 時發生 —— 例如尚未提交 policy 的 repo。安裝器(G-2)會在第一個安裝 commit 就把兩份 policy 放進 HEAD;之後單獨刪 policy 走通道會 `index_missing` 硬擋(T146-66)。因此穩態下走不到;但「刪 policy + 其他檔」的混合 commit 在 HEAD 模式是 `identity_mismatch` ⇒ VIOLATION ⇒ 受影子規則(見 N-2),影子開時這條鏈可以接上。
- 後果:被藏起來的只有「一個與 policy 內容相似度 ≥ 50% 的檔被刪除」;候選 policy 仍須合法且對現場 DECLARED_OK。
- 最小修正方向:`_staged_names_all` 不做 rename 配對(`--no-renames`),並補一個 `git mv <x> <policy>` 的 node。
- **要裁的事**:A 第六站前修(一個旗標 + 一個 node,改動在 4b 准改範圍之外,需新准改)/ B 列後補、第六站照進。建議 A:代價小,而 H-6 是 Jeff 逐字定的邊界。

#### (e) 安裝器最小 policy 是否登記了任何觀察值 —— **成立(沒有登記)**

- `install.write_extension_policy`(`install.py:440-485`):inventory `entries: []`(`:475`);allowlist 七欄先全設 `[]`(`:470-471`),只覆寫 schema / version / `project_settings_hook_commands`(`:472-474`)。
- hook 清單來源是目標 `.claude/settings.json`(`:415-437`);該檔在 manifest 標 `copy`(`.agents/portable-manifest.txt:89`),由 `copy_into`(`:164-168`)以上游版本覆寫 ⇒ 讀到的是安裝器寫入的 command,不是目標原有的觀察值。`settings.local.json` 不登記(使用者層 / 本機 hook 仍會被 R10 判未登記)。
- 既有兩份合法 policy ⇒ 保留不覆寫(`:452-464`);只有一份或不合法 ⇒ SystemExit 且之前不寫(`:458-467`)。
- node:T146-56(四個 list 欄位 `== []`、hook == settings 的 command == `[_T146_HOOK]`)、T146-58[a~e]、T146-57(decisions-pending 寫明「未登記任何使用者擴充」)。

#### (f) production 路徑是否會寫入真實 `~/.claude` —— **成立(不會);附 (c) 的 junction 條件**

- redlight 的 facts / surfaces 只有 `lstat` / `os.walk` / `listdir` / 讀檔(`redlight.py:1099-1157`、`:1431-1558`),沒有寫入。
- gate R10:只讀 `report`(`gate.py:4068-4131`)。
- `verify_gates`:`scenario_r10` 先 `_require_isolation`(`:342`)才寫 `iso.claude_root`;`restore_user_layer` 先 `_require_isolation`(`:330`)才刪;`main` 從 `install.main` 起都在 `isolated_home` 內(`:671-672`)。node:T146-53[no-marker / marker-without-context](沒有 context 時假家目錄位元組不變)、T146-51b、T146-52 / 52b。
- install:`write_extension_policy` 只寫目標 repo(`:449-450`、`:481-484`);`verify` 跑目標 gate 的 pre-commit(唯讀)。
- 例外條件同 (c):隔離 `.claude` 被換成 junction 時,`restore_user_layer` 的刪除目標會在隔離之外(讀碼推論 + 型別實測)。

#### (g) index / 列舉失敗是否可讀地 fail-closed,不被舊 wrapper 或例外洗成通過 —— **成立;附三個註記**

- index 六態(`redlight.py:1337-1375`):無輸出 ⇒ `index_missing`;任一 stage ≠ 0 ⇒ `index_conflict`;mode 非 100644/100755 ⇒ `index_nonregular`;`ls-files` / `cat-file` 失敗或任何例外 ⇒ `index_unreadable`(初值 `:1338`,`except` 吞成該態 `:1373-1374`);JSON / validator 不過 ⇒ `malformed`。任一非 ok ⇒ gate (e) 硬擋(`gate.py:4105-4107`)。node:T146-71(facts 層 16 案)、T146-64(malformed)、T146-66[allowlist/inventory](missing)、T146-66b(conflict)、T146-70(影子開)。**`index_unreadable` 沒有 node**(T146-71 的 case 清單 a~h 沒有它)⇒ 後補。
- 目錄列舉失敗:`_walk_regular` 以 `onerror` 收集(`:1122-1125`),子目錄 lstat 失敗也進 errors(`:1133-1136`)⇒ `surfaces["errors"]` ⇒ gate (c) 硬擋。node:T146-32a~d、T146-37;T146-32e 在 Windows skip。
- 舊 wrapper:兩參數 wrapper 傳 `EXT_INVENTORY_UNCHECKED`(`:1649-1657`),synced 非空 ⇒ UNKNOWN「未評估」(T146-45);production 不經 wrapper(見 (a))。
- 例外路徑:判定器載入失敗 ⇒ 硬擋(`gate.py:4083-4090`,T146-26);`extension_report` 執行期例外 ⇒ 硬擋(`:4091-4096`,無 node,見 (h) 第 2 項)。
- 註記一(N-2,實測,契約內但不對稱):HEAD 模式下 **allowlist** 非 ok 是 VIOLATION 走 `violations`(受影子規則),**inventory** 非 ok 則經 (d) 硬擋。`probe_allowlist_shadow.py` 原文:

  ```
  [allowlist-dirty] state=VIOLATION category=allowlist_state
      allowlist=worktree_differs inventory=ok synced.verified=True
      hard_block=None
      violations=['[R10] allowlist 工作樹與 HEAD 不同；只採用 HEAD，本次無法判定']
  [inventory-dirty] state=UNKNOWN category=unmanaged_entry
      allowlist=ok inventory=worktree_differs synced.verified=False
      hard_block='[R10/fail-closed] unmanaged_entry：未受管入口：synced（synced 未納管：inventory worktree_differs）'
      violations=[]
  ```

  v1 契約的硬擋只列 (a)(b)(c)(d),allowlist 非 ok 走 VIOLATION 是照契約;但影子開時,allowlist 缺失 / 不合法 / 工作樹不同的 commit 會放行(寫進 shadow-log),而且第 1 步提早 return,使用者層三個檔案型入口在那一次**完全沒有被比對**。這是否屬 z2「authority 缺失走獨立硬擋」的範圍,票內字面沒有定論 ⇒ 交裁決。
- 註記二(N-5):R4 的樹比對丟掉 `_walk_regular` 的 errors —— `skill_mirror_violations` 只取 `[0]`(`redlight.py:1213`、`:1215`)。鏡像裡一個正典沒有、又列舉不到的子目錄,其中的多餘檔不會被報、也不會留下觀測失敗。常見情況(正典與鏡像同一個子目錄讀不到)仍會以「鏡像缺少」報出,所以不是全面失效;與 z3「列舉失敗不得洗成空集合」的精神不一致。
- 註記三:使用者層檔案 lstat 失敗記 `(relp, None)`(`:1146-1149`)⇒ 未登記 VIOLATION(可被影子豁免),synced 內同型則經 (d) 硬擋。這是裁決 8「surface 個別讀取失敗：維持 VIOLATION」的字面結果,記錄即可。

#### (h) 審查包 §3.7 的 9 處無 node 程式

| # | 位置 | fail-closed 關鍵路徑? | 判定 |
|---|---|---|---|
| 1 | `mode_pre_commit` 的 `_staged_names_all()` 失敗 ⇒ 硬擋(`gate.py:4155-4159`) | 是,但退化方向安全:若改成吞例外給 `[]`,`check_extension_integrity([])` 走 HEAD 路徑仍會判定 | 後補 |
| 2 | `extension_report` 丟例外 ⇒ 硬擋(`:4091-4096`) | 是。即使此 `except` 消失,例外會讓 `gate.py --pre-commit` 以非零碼結束,commit 仍被擋(讀碼推論;hook 腳本本輪未讀),損失的是「可讀」 | 後補(優先) |
| 3 | (b) 的「UNKNOWN 且無其他原因」(`:4122-4123`) | 防禦分支;production 的 UNKNOWN 只來自第 7 步(errors ⇒ 已有 (c) 訊息)與第 8 步(synced ⇒ 已有 (d) 訊息),第 2 步在固定八鍵下走不到 | 後補 |
| 4 | `staged_names=None` 且 git 失敗 ⇒ HEAD(`:4076-4080`) | 否;退回較嚴路徑,production 的 `mode_pre_commit` 一律傳 list | 後補 |
| 5 | `install._settings_hook_commands` 讀不到 ⇒ SystemExit(`install.py:415-422`) | 安裝期,在任何寫入之前;非權威層 | 後補 |
| 6 | `install.verify` 的 G-4 說明句(`:556-558`) | 否;只是訊息 | 後補 |
| 7 | `~` 未展開以 `startswith("~")` 判(`redlight.py:1675`) | 縱深防禦:未展開時 `"~/.claude"` 是相對路徑,通常 lstat ⇒ `FileNotFoundError` ⇒ 仍是 `claude_root_invalid`;只有 cwd 下真有 `~/.claude` 目錄才會誤用 | 後補(T146-27 已會 monkeypatch `expanduser`,加一案成本極低) |
| 8 | `verify_gates` 多印兩行、隔離範圍延伸 | 否;淨室工具 | 後補 |
| 9 | gate / status 的 `_extension_claude_root` production 回 None | **審查包的描述不完整**:T146-59 / 60 / 60b 以子程序跑安裝目標的真 `gate.py --pre-commit`(`tests/test_install.py:746-751`),沒有注入 `_extension_claude_root`,家目錄由 `g3_installed_repo` 的 USERPROFILE / HOME 隔離(`:497-500`、`:700-707`)⇒ **gate 側的 production fallback 有 node**。status 側沒有:autouse `_t146_isolated_claude_root` 一律注入(`tests/test_status.py:61-69`) | gate 側已覆蓋;status 側後補 |

**沒有任何一項會讓我拒絕驗收。** 理由:9 項中沒有一項的缺測會讓「該擋而沒擋」不被任何 node 發現 —— 第 2 項的最壞退化仍是非零結束碼,第 9 項的 gate 側已由真子程序覆蓋。後補優先序:2 → 7 → 9(status 側)→ 其餘。

#### (i) 准改第 14–18 項(未經獨立紅燈)—— **沒有一項改變既有斷言語意或弱化驗收**

逐項依 `git diff 8e7b293 982a661`:

- 第 14 項(T146-20 加 `rt[0].count(u"runtime loaded set: ") == 1`):純新增斷言。`rt` 是以 `runtime loaded set: ` 開頭的 status 行(`tests/test_status.py:3243`),計數 == 1 等於鎖住「值裡沒有再帶一次前綴」(裁決 (ee))。加嚴。
- 第 15 項(autouse `_t146_isolated_claude_root`):只換 `status._extension_claude_root`,不改任何斷言。效果是全檔 status 測試不再 fallback 到真實使用者層。代價:status 側的 production fallback 從此沒有 node(見 (h) 第 9 項)。在每個用 `tmp_path` 的測試裡多建一個空目錄 `_t146_isolated_claude_root`;本輪全綠,未見影響。不弱化。
- 第 16 項(R9 接線 node:spy + R10 替身 + `len(calls) >= 1`):原斷言 `rc == 1` 保留;替身移除「rc 1 可能來自 R10」的假綠來源,spy 加上「真的被呼叫」。加嚴。
- 第 17 項(`test_the_rule_stays_inside_r7`):移除 `"R10" not in codes`。原句的本意寫在它自己的訊息裡:「多了一個規則代號,淨室會要求它的情境」——它鎖的是「代號集合不得增長」,不是 R7 的性質,R10 合法加入後必然要動。替換成 `msg and "[R7/" in msg`(`python -c "print(1)"` 的擋下掛在 R7 名下),保留 `"R7" in codes`。這是**改了斷言的對象**(從全集合改成 R7 本身),但新斷言比舊句更直接地守「內嵌直譯器留在 R7」;舊句守的「不得多出代號」已無正當性。不弱化。補件四的 `"[R7]"` 與實測不符、補件五改 `"[R7/"`,4b 審計 §5 已記。
- 第 18 項(T146-67):期待原因由「額外 2」改為 `inventory worktree_differs`,加 `"[R10/fail-closed]"` 與結構化斷言 `res["report"]["inventory"]["state"] == "worktree_differs"`,保留 `policy_source == "head"`。依 v2 契約,HEAD 模式下工作樹 inventory ≠ HEAD 必判 `worktree_differs`(`redlight.py:1389-1391`),原期待在契約上不可能成立。新斷言**對通道判定更有鑑別力**:`worktree_differs` 只有 HEAD 模式產得出來(index 模式不做 worktree 比對,`:1329-1331`)。原期待隱含的另一件事 ——「HEAD 的空 inventory 被拿來比對」—— 由 T146-23(工作樹乾淨、HEAD 空 inventory ⇒ 額外 2)覆蓋。不弱化。

#### (j) 三個 node 的紅因可信度

| 站 | node | BASELINE 紅因(出處) | 現在的綠 | 綠在錯的理由上的可能 |
|---|---|---|---|---|
| 3e | T146-31 | `AssertionError: v0 contract not implemented: extension_report`(3e 審計 :70)—— 撞在第一行 `_api`,計數斷言在基線上從未執行 | 計數 wrapper 換掉模組全域的 `_extension_first_reason`(`tests/test_redlight.py:3426`);`extension_report` 在呼叫時才解析全域(`redlight.py:1714`),所以計到的是真實呼叫;`lines` 與 `render(state, …)` 逐字比對 | 低(讀碼推論)。呼叫兩次 ⇒ 計數 2;另行判定不經該函式 ⇒ 計數 0;lines 改由別處產生 ⇒ 比對不等。三種錯誤實作都會紅 |
| 3f | T146-43[iv-content] | `AssertionError: v0 contract not implemented: EXT_CAT_UNMANAGED`(3f 審計 :104、:134)—— 同樣撞在第一個 `_api` | `mismatch == 1`、reason 含「內容不符」、`(state, category) == (UNKNOWN, unmanaged_entry)` | **實測排除**最可疑的一型:`probe_mutant_43.py` 把 mismatch 條件改成只看 None(不比 sha256),原樣 ⇒「斷言 通過」,變異 ⇒ `synced={'verified': True, … 'mismatch': 0 …} state=DECLARED_OK` ⇒「斷言 失敗」。綠因可信 |
| 3g | T146-67 | `_wire` 的斷言:`gate._extension_claude_root` 不存在(3g 審計 §4 test_gate 表);現行斷言是 4b 第 18 項改寫的,**從未在任何基線上紅過** | `policy_source == "head"` + `worktree_differs` | 低。`worktree_differs` 只有 HEAD 模式產得出來,所以它本身就是「走 HEAD」的證據,不依賴訊息措辭。但本 node 只用「多一個 .py」造混合;rename 型混合(見 (d))不在任何 node 裡,綠不代表那一型也走 HEAD |

#### (k) 審查包沒列的問題

**146 範圍內**

- **N-1**(= (d)):`_staged_names_all` 缺 `--no-renames`,rename 型混合 commit 可被判成 policy-only。實測。交裁決 A/B。
- **N-2**(= (g) 註記一):allowlist 非 ok 受影子豁免、inventory 非 ok 硬擋,兩份 policy 的處置不對稱;影子開時 allowlist 失效那一次使用者層三個檔案型入口不被比對。實測。契約內,交裁決是否擴大 z2。
- **N-3**(= (c)):`_require_isolation` 不檢查 `realpath(iso.claude_root)`;Windows junction 被 `_lkind` 判為 `dir`。型別實測、刪除後果為推論。後補方向:清理前要求 `realpath(claude_root) == realpath(home)/.claude`,並把 Windows skip 的兩個 symlink node 改用 junction 實跑。
- **N-4**:淨室 R10 情境的 `rc != 0` 沒有鑑別力。`precontrol_r10` 與 `scenario_r10` 寫入完全相同的 repo 側內容(`verify_gates.py:349-350` 與 `:355-356`;`set_stage` 內容固定,`:122-126`),正控 commit 後 `restore` 只回到 HEAD(`:409-411`),所以情境 commit 時 staged 為空(4b 審計 §4 也記錄了這一點)。若 gate 印出硬擋訊息卻回 0,git 會接著以「nothing to commit」非零結束 —— `run_scenario` 的 `rc != 0`(`:652-653`)照樣成立。`restore()` 自己的 docstring(`:399-401`)描述過同一個形狀(「`rc != 0` 一半由殘留白送」)。R10「對非空 commit 回 1」另由 T146-60(直接看 `gate.py --pre-commit` 的 rc)守住,所以不是未受檢。後補方向:情境的 trigger 內容與正控不同,讓 staged 非空。
- **N-5**(= (g) 註記二):R4 樹比對丟掉 `_walk_regular` 的 errors(`redlight.py:1213`、`:1215`)。
- **N-6**:`check_extension_integrity` 的一般路徑以「是 VIOLATION 才進 violations、其餘放行」結尾(`gate.py:4129-4131`)。state 若是 VIOLATION / UNKNOWN / DECLARED_OK 以外的值(例如 `EXT_VERIFIED` 或 None)會放行。目前 `_extension_first_reason` 回不出這些值,所以走不到;但 policy-only 那一支是寫成 `!= DECLARED_OK ⇒ 擋`(`:4108`)。CLAUDE.md 的黑名單 / fail-closed 原則下,一般路徑也應寫成「非 DECLARED_OK 且非 VIOLATION ⇒ 硬擋」。後補。
- **N-7**:Windows junction 在使用者層走訪中會被當成一般目錄並追進去(`_walk_regular` 的目錄 lstat 對 junction 回 `S_ISDIR`,同 (c) 實測的型別)。3d 裁決 (n)「symlink 不追」因此不涵蓋 junction。追進去的內容仍會被雜湊並要求登記,**不是 fail-open**,只是語意與 symlink 不一致;記錄即可。
- **N-8**(審查包內容更正):§3.7 第 9 點應改為「gate 側由 T146-59 / 60 / 60b 的真子程序覆蓋;status 側無 node」。§7「淨室安裝會把本機 `.dev/reports/*.md` 與兩本帳帶進目標 repo」:讀碼結果是**沒有複製** —— `.dev/` 在 manifest 標 `generate`(`.agents/portable-manifest.txt:126`),`copy_into` 只複製 copy 桶(`install.py:635`、`:164-168`),`generate_state` 重新產生 `.dev/`(`:186-194`);被列出只是因為 `ignored_framework_files` 收「標記不是 skip」的項目(`:148-151`),而輸出那句「已強制帶過去」(`:689-690`)對 `generate` 項目**字面不實**。這是讀碼推論,本輪沒有跑安裝(跑安裝會讓 `verify()` 讀真實使用者層)。建議:訊息改正可另立小票,不構成洩漏。

**146 範圍外(既有問題,本輪實測坐實)**

- **O-1**:權威層與 leak scan 的 staged 清單都用 `--diff-filter=ACM`(`gate.py:4024`、`scanner.py:499-500`;`leak_scan.py:321` 經 `scanner.staged_paths` 取清單),而 git 2.53 的 `git diff` 預設做 rename 配對、狀態 `R` 不在 ACM 裡。`probe_rename.py` case B(`git mv src/a.py src/b.py`)原文:

  ```
    staged_paths 同款(--diff-filter=ACM): []
    加 --no-renames:                       ['src/b.py']
  ```

  ⇒ 改名檔不進 R1/R2/R3/R8 的逐檔判定,也不進 leak scan 的掃描清單(leak scan 對空清單回 0,`leak_scan.py:344`)。「改名時順手加進秘密不會被掃」是由清單為空推得,本輪沒有實際放秘密去跑。這正是票 140 A-1(`140-sixth-station-2026-09-13-inventory.md:40-51`),當時「仍待確認:未實測 rename 是否真能繞過」;本次是那一格的實測。**不屬 146 的驗收**,但它的嚴重度高於 146 的所有後補項,建議另立票並優先處理。

---

### 5. 結論:**PASS-with-notes**(可進第六站;不是推送授權)

- 阻擋項:**0**。
- 交裁決:
  1. N-1:A 第六站前修 / B 後補(建議 A)。
  2. N-2:allowlist 非 ok 是否改為硬擋(擴大 z2)/ 維持現契約。
  3. O-1:是否另立票(建議立,並排在 146 後補之前)。
- 後補(依優先):(h) 第 2 項例外硬擋 node → N-6 → N-3 → (g) `index_unreadable` node → (h) 第 7、9(status 側)項 → N-4 → N-5 → (h) 其餘 → N-8 訊息更正。
- 未驗:POSIX(146 的 symlink / chmod skip node 共 8 個:`test_redlight.py:3074` ×1、`:3505` ×1、`:3702` ×3、`:3752` ×1、`test_verify_gates.py:383` ×1、`:461` ×1;全套 12 個 skip 的其餘 4 個不屬 146)、CI、真實使用者層上的 report / status 一致性(審查包 §4.3,只引用 4b 審計 §3.3)。

做完停下,等 Jeff。
