# 票 172：installer 不帶位元碼、「已強制帶過去」清單只列真的複製的檔

狀態：實作完成；本輪提交（2026-11-10）；未 push。

## 背景

依據唯讀偵察報告 `20261110T143823Z-installer-ignored-recon.md`。

**甲（位元碼被帶到下游）**
- manifest 只替 `.claude/hooks/`、`.claude/portable/` 寫了直接子層的 `__pycache__/ skip`。
- `.agents/skills/`、`.claude/patches/`、`tests/fixtures/hooks/`、`tests/fixtures/redlight_run/` 沒有對應的 skip。
- 已補的兩個也封不住更深一層：`.claude/hooks/sub/__pycache__/…` 判 copy。
- 結果：位元碼會進 copy 桶被帶到下游。實測 `.claude/patches/__pycache__/apply_patches.cpython-311.pyc` 判 copy。

**乙（清單失真）**
- `ignored_framework_files()` 只排除 mark＝skip。
- 「已強制帶過去」清單列出 670 筆（以 c96425a 當下工作樹為底），其中 1 筆 mark＝copy、會被複製，669 筆是 `.dev/` 下的 generate、不會被複製。
- 這就是票 170 S1。

甲乙經過同一函式，但根因不同，各自修、各一條 AC。

## 裁決（Jeff 2026-11-10）

- 1B：程式層全域規則排除位元碼。
- 2A：清單只列真的會被複製的 ignored 框架檔。
- 3B：另開新票，把票 170 S1 移過來。
- 附帶題不加：`.pytest_cache/`、`*.egg-info/` 等其他執行期產物本票不處理。
- 兩條核心 AC（Jeff 原意）：
  - AC-1：任意深度的 `__pycache__`、`.pyc`、`.pyo` 都不得進 source-copy。
  - AC-2：「已強制帶過去」清單只列實際 mark＝copy、且真的會被 copy 的 ignored framework files。

## 設計（本輪定案）

- **D1 位元碼判定**（一個函式，一處定義）：路徑以 `/` 切段後任一段恰為 `__pycache__`，或檔名副檔名為 `.pyc`／`.pyo`（比對副檔名不分大小寫）⇒ 位元碼。不用 glob／regex 掃路徑；不靠 manifest 標記。
- **D2 套用位置**：
  - `classify()` 先排除位元碼，使其不進任何桶；因此不進 copy 桶、不進 journal、不被 `copy_into`。
  - `ignored_framework_files()` 也排除位元碼。
  - manifest 既有的兩行 `__pycache__/ skip` 保留不動（多一層防護，不衝突）。
- **D3 清單（AC-2）**：
  - main 的「已強制帶過去」清單改為「ignored 框架檔 ∩ 本次實際傳給 `copy_into` 的 `buckets["copy"]`」。
  - 直接用 main 手上那一份 `buckets["copy"]` 求交集，不得另外再算一次標記（避免兩份判定漂移）。
  - 交集為空 ⇒ 不印標題行與清單。
  - 措辭「已強制帶過去」保留（交集後為真）。
- **D4 manifest 註解**：在「# 位元碼快取」註解處補一兩行，寫明「位元碼另由 install.py 的程式層規則全域排除（票 172），本表兩行只是多一層防護」。
- **D5**：既有 `test_mirrors_and_bytecode_are_not_dragged_in` 的 docstring 若仍把「`__pycache__` …標 `skip`」寫成通則 ⇒ 改成如實描述（只此一測試、只改 docstring）。

## AC 與測試對應

| AC | 內容 | 測試 |
|---|---|---|
| AC-1 | 任意深度的 `__pycache__`、`.pyc`、`.pyo` 都不得進 source-copy | `test_t172_bytecode_never_in_copy_bucket`：tracked／untracked／ignored 三種來源、多個 copy 目錄與深度、大寫副檔名 |
| AC-1 | 同上（端到端） | `test_t172_bytecode_not_copied_by_main`：main 實際交給 `copy_into` 的路徑 |
| AC-2 | 「已強制帶過去」清單只列實際 mark＝copy、且真的會被 copy 的 ignored framework files | `test_t172_forced_list_only_actually_copied` |
| AC-2 | 同上（無可列項目時不印） | `test_t172_no_forced_list_when_nothing_copied` |

防退化基線（實作後必須仍綠）：
- `test_ignored_framework_files_are_enumerated`
- `test_it_says_so_when_framework_files_were_hidden`
- `test_mirrors_and_bytecode_are_not_dragged_in`

## 不在本票

- `.pytest_cache/` 等其他執行期產物。
- 票 170 S2／S3。
- `sync.py`（見〈同類入口〉，只查不改）。
- LifeApp 名冊 v1→v2。

## 同類入口（只查不改；修不修另裁）

`.claude/portable/sync.py` 也依 manifest 標記把來源檔複製到別的 repo：
- 來源只取 `tracked(src)`：:171–176，`git ls-files -z`。
- 逐檔依 `mark_for`（`manifest.explicit_mark`）判桶，mark＝copy 即進寫入計畫：:906–908。
- 全檔沒有任何排除位元碼的規則。

結論：
- untracked 與 ignored 的 `__pycache__`／`.pyc` 不會被 sync 帶走，因為來源只有 tracked。
- 但若來源 repo **曾把位元碼 commit 進版控**，而它落在 copy 目錄底下，sync 會照帶。
- 本輪未查來源 repo 是否實際追蹤任何位元碼。

## 關聯

- 票 170 S1：移入本票（Jeff 裁 3B）。
- 票 169：新下游安裝流程，本票改的是其中的 copy 與輸出段。
- 票 171：前一張 installer 票；本票的行號已含票 171 的偏移。

## 設計對位（2026-11-10 讀到的行號，以 HEAD `c96425a` 為底）

- `install.py`：
  - `ignored_framework_files()` 在 163，過濾式在 182–183（`in_scope and mark_for != "skip"`）。
  - `classify()` 在 186，依 `mark_for` 分桶（189–191）。
  - main：`source_files()` 在 1439、`classify` 在 1440、`_begin_journal(target, buckets["copy"], rl)` 在 1442、`copy_into(target, buckets["copy"])` 在 1444。
  - 「已強制帶過去」段在 1519–1527：`hidden = ignored_framework_files()` 重算一次，與 copy 桶無關。
- `buckets` 在 1440 定義，與 1522 同屬 `main` 作用域，可以直接取用。
- 既有測試中直接斷言 `ignored_framework_files()` 回傳值的有 2 條：`test_it_says_so_when_framework_files_were_hidden`（期望含 `.claude/hooks/gate.py`）、`test_mirrors_and_bytecode_are_not_dragged_in`（期望不含 `__pycache__`）。
- 本票只從回傳值中多排除位元碼，兩條的預期不受影響（預判）。

## 驗證

引自報告 `20261110T151944Z-ticket172-bytecode.md`（只引尾行，不重跑）：

- P1：`4 failed, 117 deselected in 19.93s`
- P2：`4 passed, 117 deselected in 19.91s`
- P3：`121 passed in 128.79s (0:02:08)`
- P4：`3535 passed, 39 skipped, 3 xfailed in 1214.15s (0:20:14)`

S0～S4 候選快照逐行一致（CAND_COUNT 2）。

## 已知限制／後續

- sync.py 與其他來源列舉路徑目前未套用票 172 的 bytecode 全域排除；本輪確認上游 tracked bytecode 為 0，且既有 ignore 規則已排除常見 bytecode，因此本票不擴充修正。日後若有實際案例再另案處理。（Jeff 2026-11-10 裁：只記錄，不另開票、不改程式；含 main 的「帶過去了但來源 repo 還沒把它們進版控」清單不排除位元碼一事。）
- 測試中臨時 target 的閘門實測輸出出現「鏡像缺少 .claude/skills/code-review/SKILL.md」：既有輸出，非票 172 回歸，本票不處理。
