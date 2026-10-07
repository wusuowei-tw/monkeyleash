# 票 146 第三站 3g —— 淨室家目錄隔離、安裝器最小 policy、R10 情境原因斷言、policy-only index 通道 紅燈審計

| 欄 | 值 |
|---|---|
| 日期 | 2026-10-07 |
| 進入基準 | G-0 `2b7c9f8d3a28aaa2595b609ca44568f3fd44f535`;`git status --porcelain` 無輸出;pipeline `implement / framework-updates / 146` |
| 本 commit | S3g-146-1(紅燈 + 票 + 本審計，同一 commit) |
| 實作 | 無(不寫 production、不碰真實使用者層) |

---

## 第一段【給裁決者】

1. 新增測試 88 個(parametrize 展開後):紅 85、綠 1(T146-59,正控)、Windows 跳過 2(symlink 案)。
2. 既有測試只改准改清單兩項：`g3_installed_repo` 改成會在安裝前隔離家目錄、並隔離到整個 module 結束;T146-36 / 44 的鍵集合加 `"policy_source"`。`-` 行共 4 行。
3. 預期全套:failed 194(既有 109 + 新 85)、passed 2115、skipped 12、xfailed 3,collected 2324。實測結果在本次的 `.dev/reports` 報告。
4. 步驟 0 盤點與預判一致，唯一差異是 recording wrapper 的編號(在 T146-28,不是預判的 T146-30)。已裁定不構成停止條件。

---

## 第二段【給裁決助手】

### 1. 步驟 0 盤點(唯讀)

**(i) 對 `extension_report` 回傳鍵集合做精確斷言的 node**(Grep `set\(rep\) ==|set\(report\) ==|len\(rep\) ==|len\(report\) ==|...`):

```
tests\test_redlight.py:3538:        assert set(rep) == {"facts", "surfaces", "state", "category", "reason", "lines",
tests\test_redlight.py:3540:                            "authority", "observation", "inventory", "synced"}, sorted(rep)
tests\test_redlight.py:3845:                "claude_root", "claude_root_source", "authority", "observation", "inventory", "synced"}
tests\test_redlight.py:3857:        assert set(rep) == keys, sorted(rep)
```

⇒ 只有 T146-36(`:3538-3540`)與 T146-44(`:3844-3846` 定義、`:3857` 斷言),與預判一致。

**(ii) 替換 `extension_report` / `extension_allowlist_facts` / `extension_inventory_facts` 的 wrapper**(Grep `setattr\([^)]*"(extension_report|extension_allowlist_facts|extension_inventory_facts)"`):

| 位置 | node | 形狀 | 對 `policy_source` 關鍵字 |
|---|---|---|---|
| `tests/test_gate.py:6710-6711` | T146-37 | `lambda repo_root, claude_root=None, **k: orig(repo_root, claude_root, walk=fake)` | `**k` 吸收、不轉交(非 policy-only 情境，預設 head)—— 不改 |
| `tests/test_gate.py:6921-6922` | T146-23h | 同上，只轉交 `read_bytes=` | 同上 —— 不改 |
| `tests/test_status.py:3268-3272` | **T146-28** | `recording(*a, **k)`:`orig(*a, **k)` | 原樣轉交 —— 不改 |

替換兩個 facts 函式的 wrapper:0 處。

**與預判的差異**:預判把 recording wrapper 寫成 T146-30,實際在 T146-28(T146-30 沒有 wrapper)。依 Jeff 裁決(補件二附註，2026-10-07):「T146-28／30 是預判編號錯誤，wrapper 行為一致、修改範圍不變，不構成停止條件；審計步驟 0 記明即可。」

### 2. 既有測試的 `-` 行(全部 4 行，逐行)

| 檔 / hunk | 位置 | `-` 行 | 准改依據 |
|---|---|---|---|
| test_install `@@ -488 +488,5 @@` | `g3_installed_repo` docstring | `-    """`install.main(<tmp>/repo)` 裝好的新 repo(真安裝)。回傳 repo 路徑(pathlib.Path)。"""` | 「g3_installed_repo 改 yield fixture + 家目錄隔離」 |
| test_install `@@ -500 +508,0 @@` | `g3_installed_repo` | `-    return target` | 同上(改成 `yield target`,`mp.undo()` 移到 yield 之後) |
| test_redlight `@@ -3540 +3540 @@` | T146-36 | `-                            "authority", "observation", "inventory", "synced"}, sorted(rep)` | 「T146-36、T146-44 鍵集合加 "policy_source"」 |
| test_redlight `@@ -3845 +3845,2 @@` | T146-44 | `-                "claude_root", "claude_root_source", "authority", "observation", "inventory", "synced"}` | 同上 |

`g3_installed_repo` 的 `+` 行:

- 建 `home = tmp_path_factory.mktemp("g3-home")` 與 `home/.claude`;
- `mp.setenv("USERPROFILE", str(home))`、`mp.setenv("HOME", str(home))`,都在 `mod.main` 之前;
- `yield target` 在 try 內，`mp.undo()` 在 finally(涵蓋整個 module 的使用期)。

三支既有 node(`TestEvidencePolicyTemplate`)的斷言沒動。

### 3. diff 摘要

```
 .../146-claude-code-enforcement-integrity.md       | 140 ++++++++-
 tests/test_gate.py                                 | 204 +++++++++++++
 tests/test_install.py                              | 281 ++++++++++++++++-
 tests/test_redlight.py                             | 149 ++++++++-
 tests/test_verify_gates.py                         | 334 +++++++++++++++++++++
 5 files changed, 1103 insertions(+), 5 deletions(-)
```

(本審計檔是新檔，未列在上表;票的 1 個 `-` 是 (cc) 那一句的 F-036 劃線改寫。)

新增 class:

- `tests/test_verify_gates.py::TestTicket146Cleanroom`
- `tests/test_install.py::TestTicket146InstallPolicy`
- `tests/test_redlight.py::TestTicket146IndexPolicy`
- `tests/test_gate.py::TestTicket146PolicyOnlyLane`

### 4. C0 預期表(parametrize 展開後的 node 數;BASELINE = 本 commit,未實作)

**test_verify_gates.py(28 個)**

| node | 數 | 預期 | 紅因 |
|---|---|---|---|
| T146-50[both-set / both-absent] | 2 | 紅 | `vg.isolated_home` 不存在(AttributeError) |
| T146-50b[home-nonempty / home-is-file / claude-is-file / marker-preexists] | 4 | 紅 | 同上 |
| T146-50b[home-is-symlink] | 1 | Windows skip | `os.name == 'nt'` |
| T146-50c | 1 | 紅 | 同上 |
| T146-50d | 1 | 紅 | 同上 |
| T146-51 | 1 | 紅 | 同上 |
| T146-51b[i / ii / iii / iv / v] | 5 | 紅 | 同上 |
| T146-51b[vi-home-symlink] | 1 | Windows skip | `os.name == 'nt'` |
| T146-52 | 1 | 紅 | main 沒有隔離：假 install.main 記到的是真實家目錄 ⇒ `assert` 失敗(不寫任何東西) |
| T146-52b | 1 | 紅 | 同上(假 load_target_gate 記到真實家目錄) |
| T146-53[no-marker / marker-without-context] | 2 | 紅 | `vg.scenario_r10` 不存在 |
| T146-53b | 1 | 紅 | 同上 |
| T146-54 | 1 | 紅 | 同上 |
| T146-55[a / b / c / d / e / f] | 6 | 紅 | `monkeypatch.setattr(vg, "restore_user_layer", …)` 時 AttributeError(在呼叫 `run_scenario` 之前) |

**test_install.py(10 個)**

| node | 數 | 預期 | 紅因 |
|---|---|---|---|
| T146-56 | 1 | 紅 | 安裝器不寫兩份 policy(`is_file` 失敗) |
| T146-57 | 1 | 紅 | decisions-pending 沒有那一段 |
| T146-58[a / b / c / d / e] | 5 | 紅 | `install.write_extension_policy` 不存在(AttributeError) |
| T146-59 | 1 | **綠**(正控) | R10 未接線;隔離家目錄為空時，安裝目標的 pre-commit 放行、輸出不含 `[R10` |
| T146-60 | 1 | 紅 | R10 未接線 ⇒ pre-commit rc 0(預期 1) |
| T146-60b | 1 | 紅 | 沒有 policy-only 通道 ⇒ 輸出不含 `policy_source=index` |

**test_redlight.py(31 個)**

| node | 數 | 預期 | 紅因 |
|---|---|---|---|
| T146-71[allowlist-*] × 8 | 8 | 紅 | `extension_allowlist_facts` 沒有 `policy_source` 參數(TypeError;h 案的 TypeError 也不是預期的 ValueError) |
| T146-71[inventory-*] × 8 | 8 | 紅 | `extension_inventory_facts` 不存在(AttributeError) |
| T146-72 | 1 | 紅 | `extension_report` 不存在 |
| T146-73 × 13 | 13 | 紅 | `_extension_inventory_ok` 不存在 |
| T146-74 | 1 | 紅 | `gate.EXT_POLICY_PATHS` 不存在 |

**test_gate.py(19 個)**

| node | 數 | 預期 | 紅因 |
|---|---|---|---|
| T146-61 × 7 | 7 | 紅 | `gate.extension_policy_only_commit` 不存在 |
| T146-62 | 1 | 紅 | `_staged_names_all` 不存在 |
| T146-63、64、65、66b、66c、67、68、69、70 | 9 | 紅 | `_wire` 的斷言:`gate._extension_claude_root` 不存在 |
| T146-66[allowlist / inventory] | 2 | 紅 | 同上 |

**合計**:新增 88 = 紅 85 + 綠 1 + Windows skip 2。

**被改的既有 node**:

| node | 改前 | 改後預期 | 說明 |
|---|---|---|---|
| T146-36、T146-44 | 紅 | 紅 | **第一個失敗點不變**:仍先撞到 `extension_report` 不存在(`_api`);改的是更後面的鍵集合斷言，基線上執行不到。指令預期「紅因改變」,實際紅因字面不會變，見偏離 1 |
| `TestEvidencePolicyTemplate` 三支(I1 / I2 / I3,共用 `g3_installed_repo`) | 綠 | 綠 | 隔離只改環境變數;安裝在新 repo 設本地 git user,不依賴家目錄的 git 設定 |

**全套預期**:

| 欄 | 基準(G-0 實測) | 預期 |
|---|---|---|
| failed | 109 | 194(109 + 85) |
| passed | 2114 | 2115(2114 + 1) |
| skipped | 10 | 12(10 + 2) |
| xfailed | 3 | 3 |
| collected | 2236 | 2324(2236 + 88) |
| ERROR | 0 | 0 |
| 既有 109 個 failed | —— | 全部仍在 |

### 5. 測試設計上的選擇(規格沒寫死的地方)

1. **marker 位置以 `<home>/<ISOLATION_MARKER>` 佈置**(T146-50b marker-preexists、T146-53 marker-without-context)。契約寫「建 home、home/.claude、marker」,沒有寫 marker 的父目錄;這兩個 node 鎖成在 home 底下。
2. **T146-55 一律以 `iso=` 關鍵字呼叫 `run_scenario`**,並 monkeypatch `PRECONTROL["R10"]` / `SCENARIOS[code]` 為假函式，不碰真實 target。
3. **T146-56–60b 寫家目錄前先驗隔離。** 以 `_t146_isolated_claude_root()` 確認 USERPROFILE == HOME == expanduser 且 basename 以 `g3-home` 開頭，否則拒絕。會改目標狀態的 node,finally 都會 `git reset --hard <SHA>`,並清掉自己放的檔。
4. **T146-66 多斷言了 `"policy_source=index"`。** 依「任何失敗均包含 `policy-only`、`policy_source=index` 與具體原因」(五處閉合裁決第 2 點)。
5. **T146-66c 用 indent=4 改寫 allowlist 位元組。** 不改的話 `git add` 沒有變更;改後斷言 staged 集合恰為 allowlist。
6. **T146-67 / 68 的 staged 集合由 `git diff --cached --name-only` 實際取得**後傳入,不是寫死的清單。

### 6. 偏離與說明

1. **T146-36 / 44「紅因改變」不成立。** 指令預期兩者紅因改變，但第一個失敗點仍是 `extension_report` 不存在，與改前相同。改動的是更後面的鍵集合斷言。
2. **票的狀態列沒有更新。** 本次指令沒有要求，仍是「3f-2 紅燈已驗收；待 policy 草稿與 Jeff 核准」。policy 已由 Jeff 在 `4cb59eb` 提交，狀態列實際已過期，待指示。
3. **`g3_installed_repo` 的 `mp.undo()` 移到 yield 之後**(依指令)。`sys.path` / `sys.modules["gate"]` 的還原也跟著延後到 module 結束。三支既有 node 只以路徑載入模組，預期不受影響;以實測為準。
