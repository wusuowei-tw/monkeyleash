# 票 146 第三站 3h 紅燈審計(S3h-146-1)—— N-1～N-4

- 日期:2026-10-07
- 基準 HEAD:`df83a05d60ef4c9e6ea69fc9ab8c1dbfcdc4abcf`(status 乾淨;pipeline implement / framework-updates / 146)
- 契約與裁決：票 146〈3h 契約與紅燈(N-1～N-4)〉
- 範圍：只寫測試、票、審計;production 未動。
- 本審計寫在證紅之前;C0 是讀碼預期，實際結果記在本輪報告，並由下一輪核對入票。

## 1. 新 node(依 parametrize 展開實算:15 個)

### `tests/test_gate.py` 檔尾 `TestTicket146RenameAndAllowlistBlock`(6 個)

| node | BASELINE 預期 | 紅因(讀碼推論) |
|---|---|---|
| `test_t146_80_rename_into_policy_path_is_not_policy_only` | 紅 | `_staged_names_all` 沒有 `--no-renames`;Git 把相同內容的 `git mv` 配成 R100,清單只有目的 `.agents/extension-allowlist.json`,第一個斷言(含來源)失敗 |
| `test_t146_80b_plain_rename_lists_both_names` | 紅 | 同上;佈置以 name-status 含 `R100` 為前提(不成立 ⇒ 以「佈置未形成 rename」fail) |
| `test_t146_81_…[uninitialized]` | 紅 | allowlist 非 ok 走 violations,影子開 ⇒ `mode_pre_commit()` 回 0;`hard_block` 為 None |
| `test_t146_81_…[worktree_differs]` | 紅 | 同上 |
| `test_t146_81_…[malformed]` | 紅 | 同上 |
| `test_t146_81d_shadow_still_exempts_plain_unregistered` | **綠**(正控) | 未登記 dev-mod 走 violations、受影子規則 ⇒ rc 0(與 T146-38c 同理) |

### `tests/test_verify_gates.py` 檔尾 `TestTicket146IsolationReparse`(9 個)

| node | BASELINE 預期(Windows) | 紅因(讀碼推論) |
|---|---|---|
| `test_t146_82_restore_refuses_claude_root_link` | 紅 | junction 被 `_lkind` 判 dir;`_require_isolation` 不驗 claude_root 的 realpath ⇒ 清理照做、刪到 outside,沒有 SystemExit |
| `test_t146_82b_restore_refuses_direct_child_link` | 紅 | 先刪 `plain.txt`,再對 junction 子項 `shutil.rmtree`(例外，非 SystemExit) |
| `test_t146_82c_restore_refuses_nested_link_without_enumerating_outside` | 紅 | 沒有預檢;`restore_user_layer` 照刪 ⇒ 沒有 SystemExit(`assert raised` 失敗) |
| `test_t146_82d_scenario_r10_refuses_claude_root_link` | 紅 | 同 82;`scenario_r10` 寫入 junction 目標 |
| `test_t146_82e_require_isolation_checks_claude_root_realpath` | 紅 | 不驗 claude_root 的解析位置 |
| `test_t146_83_scenario_trigger_differs_and_stages_nonempty` | 紅 | `SCENARIO_TRIGGER_R10` 不存在(AttributeError) |
| `test_t146_83b_run_scenario_fails_when_staged_empty` | 紅 | 沒有 staged 檢查;情境照樣 commit(2 次)、判擋下 |
| `test_t146_83c_run_scenario_fails_when_gate_returns_zero` | **綠**(見 §4 待裁一) | 現行判定 `rc != 0 and …`:gate 回 0 ⇒ False;commit 2 次 —— 斷言在現行實作下已成立 |
| `test_t146_83d_r4_generic_with_staged_check` | 紅 | 空 staged 也照樣 commit 並判擋下(第二段斷言失敗) |

- 新 node 合計:15(紅 13、綠 2)。
- 在 POSIX 上,82 / 82d 的 symlink 已被現行 `_lkind` 拒絕，可能為綠;本輪只在 Windows 證紅。

## 2. 既有 node(准改;逐行)

- `tests/test_verify_gates.py` T146-50b parametrize:`"home-nonempty", "home-is-file", "claude-is-file", "marker-preexists",` + `pytest.param("home-is-symlink", marks=_T146_SKIP_SYMLINK)])` → `"home-nonempty", "home-is-file", "claude-is-file", "marker-preexists", "home-is-symlink"])`(不再 skip)。
- T146-50b 佈置:`os.symlink(str(real), str(home))` → `_t146_link_dir(real, home)`(Windows junction / POSIX symlink)。
- T146-51b parametrize:`"v-env-moved", pytest.param("vi-home-symlink", marks=_T146_SKIP_SYMLINK)])` → `"v-env-moved", "vi-home-symlink"])`。
- T146-51b 佈置:`os.symlink(moved, str(iso.home))` → `_t146_link_dir(moved, iso.home)`。
- T146-53b:`assert (target / "docs" / "adr" / "verify-trigger.md").is_file()` → `assert (target / getattr(vg, "SCENARIO_TRIGGER_R10")).is_file()`(加一行註解)。
  - 准改清單字面寫 `_api(...)`;本檔沒有 `_api`,依指令規則「_api/getattr 取物件」用 `getattr(vg, …)`,與本檔既有慣例一致。
- T146-55 `fake_sh`:加兩行 —— `args[1:4] == ["diff", "--cached", "--name-only"]` ⇒ 回 `(0, "docs/adr/verify-trigger-r10.md\n")`;六案斷言不動。
- `_t146_link_dir` 定義在檔尾新區塊(3h 新增 helper),兩支准改 node 在執行期引用它。
- `_T146_SKIP_SYMLINK` 常數保留未刪，現已無引用。

| 既有 node | BASELINE 預期 | 理由 |
|---|---|---|
| T146-50b[home-is-symlink] | skip → **紅** | junction 被 `_lkind` 判 dir,空 junction 目標 ⇒ `isolated_home` 照常進入、不 SystemExit |
| T146-51b[vi-home-symlink] | skip → **紅** | `realpath(home)` 解析到 `wd/home-moved`(仍在 workdir 下)、`_lkind` 判 dir ⇒ 每道檢查都過、照常清理 |
| T146-53b | 綠 → **紅** | `SCENARIO_TRIGGER_R10` 不存在(AttributeError,在既有斷言之後) |
| T146-55 六案 | 綠 → 綠 | 現行 `run_scenario` 不呼叫 staged 查詢,替身的新分支不被走到 |
| 其餘既有 node | 綠 | 未動 |

## 3. C0 總表(基準:4b 正式結果與獨立審查 `2309 passed, 12 skipped, 3 xfailed`,collected 2324)

| 項 | 計算 | 預期 |
|---|---|---|
| collected | 2324 + 15 | **2339** |
| failed | 新 13 + 50b / 51b 兩案 + 53b | **16** |
| passed | 2309 − 1(53b)+ 2(81d、83c) | **2310** |
| skipped | 12 − 2(50b / 51b 轉為實跑) | **10** |
| xfailed | 不變 | **3** |
| ERROR | — | **0** |

## 4. 待裁 / 偏離

- **待裁一(T146-83c 在 BASELINE 為綠)**:依補充裁決 2 的規格(情境 commit 回 0 ⇒ False、commit 2 次),現行 `run_scenario` 的 `rc != 0 and …` 已讓它成立。這與補充裁決 3「T146-81d 是唯一 BASELINE 綠」的表述不一致。本輪照規格寫、不自行加斷言，列為綠(回歸鎖)。若要它在 BASELINE 為紅，需要新增可鑑別的斷言(例如 staged 查詢被呼叫)——待裁。
- **待裁二(4c 後 T146-50b[home-is-symlink] 預期仍紅)**:N-3 契約只把 reparse 檢查加在 `_require_isolation` / `restore_user_layer`;`isolated_home` 的進入檢查仍用 `_lkind`(junction ⇒ dir)。依現行契約實作後，該 node 仍不會 SystemExit【推論】。若要它轉綠，契約須補「`isolated_home` 進入時 home / `.claude` / marker 任一 `_is_reparse` ⇒ SystemExit」—— 待裁。
- 偏離:T146-53b 用 `getattr` 而非 `_api`(理由見 §2)。
- 「新 node 一律追加檔尾」:兩檔都只在檔尾新增;`_t146_link_dir` 也在檔尾。
