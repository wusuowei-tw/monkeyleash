# 票 148 第三站紅燈審計(S3-148-1)—— rename 目的檔須進入 staged 檢查

- 日期:2026-10-07
- 測試基準 HEAD:`6d80427b0bfd79d4c0477a8b93b2f8f65c44de09`
- 證據性質:**工作樹證紅**(測試基準 HEAD + 未提交測試)。不是提交後 HEAD 的正式結果。
- 准改範圍:
  - 只追加:`tests/test_gate.py`、`tests/test_scanner.py`、`tests/test_leak_scan.py`
  - 只用 Edit,依 F-036:`docs/tickets/framework-updates/148-staged-list-misses-renames.md`
  - 新增:本審計
  - production、policy、`.dev/pipeline.json` 都沒有改動。

## 1. 契約(Jeff 裁決原文)

16:37 美東,逐字:

> 「裁 A，#5 本輪不改，但記入票 148 待辦。
> #1 與 #3 加 `--no-renames`，保留既有 `--diff-filter=ACM`，讓 rename 目的檔按新增檔進入檢查；刪除處置不變。
> 第三站紅燈須鎖住：
> * 未設定／true／false／copies 四種 `diff.renames` 下，目的檔都被列入；false 可列基線正控。
> * leak scan：新檔秘密被擋的正控，以及「rename＋少量修改＋秘密」仍被擋的負控；先確認佈置確實形成 rename。
> * 權威層另做實際規則驗證，不能只驗清單；目前其繞過仍是推論。
> * 純刪除維持既有處置。
> 沙盒結果記為外部 Linux 實測，不升格成本 repo 的 Windows 帳本證據。「秘密完全不被察覺」也限縮為「該佈置下 leak scan 回 rc 0」，避免泛化。」

16:50 美東,逐字:

> 「裁 A。允許將 `-k "T148 or t148"` 改為 `-k t148`，沿用原 C0 與停止條件，不改測試內容。
> 選取驗證須核對 14 個 node 的完整名稱與參數案都符合預定清單，不能只看 passed＋failed＝14；ERROR／skip／xfail 均應為 0。
> R7 的擋下訊息記為實測，`split()` 是否為觸發原因維持讀碼推論。另把「還沒存檔」改為「已寫入工作樹、尚未 commit」。
> 其餘接續安排接受，不 push。」

## 2. node 表、C0 與工作樹證紅結果

| node(完整名稱) | C0 | 結果 | 紅 node 失敗訊息首行 |
|---|---|---|---|
| `tests/test_gate.py::TestTicket148RenameDestinationIsListed::test_t148_1_gate_staged_paths_lists_rename_destination[unset]` | 紅 | 紅 | `AssertionError: rename 目的檔不在 gate.staged_paths(diff.renames=unset):[]` |
| `…test_t148_1_gate_staged_paths_lists_rename_destination[true]` | 紅 | 紅 | `AssertionError: rename 目的檔不在 gate.staged_paths(diff.renames=true):[]` |
| `…test_t148_1_gate_staged_paths_lists_rename_destination[copies]` | 紅 | 紅 | `AssertionError: rename 目的檔不在 gate.staged_paths(diff.renames=copies):[]` |
| `…test_t148_1_gate_staged_paths_lists_rename_destination[false]` | 綠 | 綠 | — |
| `tests/test_gate.py::TestTicket148RenameDestinationIsListed::test_t148_3_rename_source_stays_out_of_both_listings` | 綠 | 綠 | — |
| `tests/test_gate.py::TestTicket148RenameDestinationIsListed::test_t148_4_pure_deletion_stays_out_of_both_listings` | 綠 | 綠 | — |
| `tests/test_gate.py::TestTicket148AuthorityLayerJudgesRenamedSource::test_t148_7c_new_source_file_is_blocked_by_r2` | 綠 | 綠 | — |
| `tests/test_gate.py::TestTicket148AuthorityLayerJudgesRenamedSource::test_t148_7_renamed_into_source_is_blocked_by_r2` | 紅 | 紅 | `AssertionError: rename 進原始碼目錄沒被權威層擋下:rc=0` |
| `tests/test_scanner.py::test_t148_2_scanner_staged_paths_lists_rename_destination[unset]` | 紅 | 紅 | `AssertionError: rename 目的檔不在 scanner.staged_paths(diff.renames=unset):[]` |
| `…test_t148_2_scanner_staged_paths_lists_rename_destination[true]` | 紅 | 紅 | `AssertionError: rename 目的檔不在 scanner.staged_paths(diff.renames=true):[]` |
| `…test_t148_2_scanner_staged_paths_lists_rename_destination[copies]` | 紅 | 紅 | `AssertionError: rename 目的檔不在 scanner.staged_paths(diff.renames=copies):[]` |
| `…test_t148_2_scanner_staged_paths_lists_rename_destination[false]` | 綠 | 綠 | — |
| `tests/test_leak_scan.py::TestTicket148RenamedFileIsScanned::test_t148_5_secret_in_a_new_file_is_caught` | 綠 | 綠 | — |
| `tests/test_leak_scan.py::TestTicket148RenamedFileIsScanned::test_t148_6_secret_added_during_rename_is_caught` | 紅 | 紅 | `AssertionError: leak scan 回 0(notes/b.txt 未被擋):` |

- 8 個紅 node 全部是**斷言失敗**:
  - 都不是 ImportError、fixture 錯誤或前提斷言失敗(前提斷言用 `pytest.fail`,會顯示為 `Failed:`,本輪輸出中不存在)。
  - T148-6 的前提斷言(R、非 R100)與 T148-7 的前提斷言(R)都在 rc 斷言之前通過,紅因落在 rc。
- 新 node:`python -X utf8 -m pytest -q -rA -k t148`
  - 結果:`8 failed, 6 passed, 2339 deselected in 5.23s`
  - `-rA` 摘要列出的 14 個名稱與參數 id 逐一相符(實測)
  - ERROR / skipped / xfailed / xpassed 皆 0
- 全套:`python -X utf8 -m pytest -q -rs`
  - 結果:`8 failed, 2332 passed, 10 skipped, 3 xfailed in 252.90s (0:04:12)`
  - 失敗區塊標頭恰為上表 8 個紅 node
  - 10 個 skip 的位置與原因與 4c 審計 §3.1 列表相同:`test_gate.py:451/459/473`、`test_redlight.py:2673/3074/3505/3702×3/3752`
- 2332 = 前次 2326 passed + 6 綠。

## 3. 步驟 0 第 8 項:路徑規則核對(讀碼,測試基準 HEAD)

- `gate.py:272-287` `NON_SOURCE_DIRS` 含 `tests`、`docs`。
- `:2204-2230` `is_source_path`:top 在 `NON_SOURCE_DIRS` ⇒ 非原始碼。
- `check()` `:2786`:非原始碼直接 return None ⇒ R2 / R3 / R8 都不進入。
- R1 只管 `docs/specs/**` 與 `.scratch/<f>/spec.md`(`:2737`)。
- ⇒ 三個測試檔、票、本審計都不屬原始碼,tickets 站寫入不會被 R2 / R3 擋。
- `.agents/pipeline-stages.yaml:29-32`:`tickets` 的 `allows_src_write: false`。

## 4. 所選路徑與分類依據

| 路徑 | 分類 | 依據 |
|---|---|---|
| `src/a.py` → `src/b.py` | 只用於清單層測試(T148-1~4),不經規則判定 | — |
| `pkg/fresh.py`(T148-7c)、`pkg/tool.py`(T148-7 目的) | 原始碼 | top `pkg` 不在 `NON_SOURCE_DIRS`;`.py` 不在 `NON_SOURCE_EXT` |
| `docs/tool.py`(T148-7 來源) | 非原始碼 | top `docs` 在 `NON_SOURCE_DIRS` |
| `notes/fresh.txt`、`notes/a.txt` → `notes/b.txt`(T148-5/6) | leak scan 對象 | 非 `.gitignore`,非 `CERT_EXT` |

T148-7 / 7c 的站別:tmp repo 的 `.dev/pipeline.json` 寫 `current_stage: tickets`。

- R2 提交時點(`gate.py:2862-2894`)的 `pre_implement = {grill, spec, tickets}`,所以會進 `[R2/commit]` 分支。
- 該分支 return 早於 R3。

## 5. git 設定與使用者層隔離

- 每個 T148 測試都在 tmp 建獨立 git repo,並用 `monkeypatch.setenv` 設定:
  - `GIT_CONFIG_GLOBAL` → tmp 內空檔
  - `GIT_CONFIG_NOSYSTEM=1`
  - `HOME` 與 `USERPROFILE` → tmp 家目錄
- 被測程式的 git 子行程繼承這份環境。
- `diff.renames` 只寫在 tmp repo 的 local config;`unset` 格完全不寫。
- 前提斷言用同一隔離環境下的 `git diff --cached --name-status`(依該 repo 的設定做 rename 偵測):
  - unset / true / copies:要有恰一列 `R…\t來源\t目的`。
  - false:要恰為 `D\t來源` + `A\t目的`。
  - 不成立 ⇒ `pytest.fail`,不 skip。
- `staged_paths` 一律呼叫真實函式,沒有替身。

## 6. R10 隔離:採 (a)

- tmp 家目錄下建空的 `.claude`。
- tmp repo 提交合法空白 allowlist / inventory,內容同 `TestTicket146Integration._ALLOWLIST` 與空 `entries` 的 inventory,佈置方式同 `TestTicket146Integration._root`。另外提交 `.agents/pipeline-stages.yaml` 副本與 `docs/tool.py`。
- **不注入** `_extension_claude_root`(斷言它回 None),R10 走 production fallback `expanduser("~")/.claude`。
- 執行前斷言 `expanduser("~")` 等於 tmp 家目錄,沒有讀到真實使用者層。
- R10 以外的鄰居照 `TestTicket146Integration._wire`(`tests/test_gate.py:6630-6642`)的同一份名單停掉:
  - `upstream_shadow_violation`、`check_third_axis_mount`、`check_to_spec_override`、`check_legacy_list`、`check_friction_numbers`、`check_skill_copies`、`shadow_active`
  - **不停 `staged_paths`**。
- 走真實 `mode_pre_commit`(`TestTicket146Integration._run`),並 `chdir` 到 tmp repo(理由見 `_d_silence_the_neighbours` docstring:`rel()` 以行程 cwd 為基準)。
- 7c 綠的意義:**rc 1、含 `[R2`、不含 `[R10`**,證明正控確實走到 R2,R10 判 DECLARED_OK 沒有搶走 rc。

不採 (b) 的理由:

- `_wire` 會把 `staged_paths` 換成 `[]`(`:6636`),違反「不得以替身換掉 staged_paths」。
- `_d_silence_the_neighbours`(`:6214-6240`)綁模組層 `gate`,它的 ROOT / PIPELINE 不指向 tmp repo。

## 7. 合成秘密

- 執行時由 `_t148_secret_block()` 組合,分三段:
  1. 私鑰標頭:以 `"-----BEGIN "`、`"RSA "`、`"PRIVATE "`、`"KEY-----"` 相接
  2. 假 base64 本體:兩個四字元片段重複 8 次
  3. 私鑰結尾:同法相接
- 不使用任何真實 key / token。
- 規則斷言用 `_t148_rule()`,同樣執行時組合出 `leak-patterns.txt` 私鑰標頭那條的原文。斷言輸出含「命中 pattern:<該規則>」與 `<檔名>:`,不只看 rc。
- 本審計不貼完整字串。

## 8. 帳本前綴證明

| 檔 | LC(執行前,bytes) | `head -c LC` 的 sha256 | 執行前整檔 sha256 | 執行後長度(bytes) | 執行後整檔 sha256 |
|---|---|---|---|---|---|
| `.dev/test-runs.jsonl` | 1173222 | `d9d3ffd5ceee0168c16c06d2a068eed99c2b4ea497ee32a280d5cbd311b21a24` | `d9d3ffd5…` | 1186991 | `6f10bda5995fa68795195a5999fa1000fb52b2f5c3424c39b42ad25a060bd1da` |
| `.dev/test-sessions.jsonl` | 33635395 | `6d6ec88ca7a3c5606ec29a5079a54b167cbf8eecd8aaf779ded3b4ee3fe7e23c` | `6d6ec88c…` | 35241650 | `20ce69ff16b80f5a52fb7565dcca5052dcadfaea4c1ad2d546a10152ba8a6fa9` |

- 前綴雜湊與執行前整檔雜湊逐字相同 ⇒ 兩本帳只追加:
  - test-runs +13769 bytes
  - test-sessions +1606255 bytes
- 追加來自兩次 pytest(新 node 一次、全套一次)。

## 9. T0 指紋(寫完測試、執行前)

```
1df7320a9c9a8acee177572cf215d3dee9bb3a35474044b56346e4730b2f7614 *tests/test_gate.py
c41833b4795ad0389c716a0856a1a84d388dab10fdf376fd99ebe6098f7926e7 *tests/test_scanner.py
a665916bf87c09c8da054351e5198516add3261d049c8e7246723bc3b8daa985 *tests/test_leak_scan.py
```

## 10. 偏離與詮釋

1. **步驟 3-2 指令改寫**(依 Jeff 16:50 裁決)。
   - 原指令 `-k "T148 or t148"` 被 R7 前哨以「(引號或跳脫使目標無法可靠切分)」整行擋下。擋下訊息是實測,原文見停止報告 `.dev/reports/2026-10-07T204645Z-ticket148-s3-redlight.md` §3。
   - 觸發點是否為 `_quoting_is_ambiguous` 以 `split()` 切 token,維持讀碼推論。
   - 改為 `-k t148`,另加 `-rA` 用來點名。14 個 node 名稱逐一相符是實測。
2. **測試內各檔自帶 `_t148_*` helper**,三份內容同形。准改範圍只到三個測試檔,沒有共用模組可放。
3. **T148-6「少量修改」的形狀**:
   - 40 行檔改第 1 行,檔尾加 3 行合成秘密。
   - 前提額外要求 R 的相似度不是 100(排除「沒改到」),實測形成 R。本輪沒有記錄確切相似度數字。
4. **T148-7 / 7c 停掉的鄰居**沿用 `_wire` 名單。這些不是 R10 替身;R10 本身走真實判定。

## 11. 未驗 / 待辦

- POSIX、CI 未跑。
- 外部證據(裁決者 Linux 沙盒)見票 148〈外部證據〉,不屬本 repo 帳本。
- 第四站:#1、#3 加 `--no-renames`(裁 A);#5 不改。
