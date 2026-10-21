# 157 — mcp 依賴上限複審（2026-10-31 到期前處理）

**狀態**：~~**立案；未開工。** **紅燈與修補完成（本機）；待 push 與 CI。**~~ **已結案（2026-10-20，美東）。**
**時鐘**：`2026-10-31`（美東）。11/1 起 `test_ceiling_review_date_has_not_passed[mcp]` 會依日期自動轉紅。
**優先度**：要在 2026-10-31 之前收掉，排在「AI 正式執行管道」（票 158）之前（Jeff 2026-10-20 約 20:30，美東，裁決助手記錄，非逐字原話）。
**立案**：2026-10-20（美東）。票號 157 由 Jeff 2026-10-20 約 20:30（美東）指定（裁決助手記錄，非逐字原話）；建檔前確認 `docs/tickets/framework-updates/` 內無 157 開頭的檔案。
**性質**：小票 —— 依賴上限的定期複審，以及複審程序與票 156 鎖定檔制度的對齊。
**交叉引用**：〔AIP-R0〕`.dev/reports/2026-10-21T002449Z-aip-r0.md` 步驟 4（本機報告，不進版控）。

---

## 一、背景

以下各點的出處都是〔AIP-R0〕步驟 4。

1. `pyproject.toml:56` 宣告 `"mcp>=1.27,<2"`；`:63-68` 是複審日的理由註解，以及 `mcp-ceiling-review = "2026-10-31"`。
2. `tests/test_dependency_ceiling.py`：
   - `:46` `CAPPED = ("pytest", "mcp")`；
   - `:62-70` `_howto(name)` 的複審程序，第 1 步是「`python -m pip install -U %s` 裝下一個大版本」；
   - `:141-161` `test_ceiling_review_date_has_not_passed`，`:155` `today = _dt.date.today()`，`:157` `assert today <= review`。
3. `.claude/portable/gates-lock-upstream-tests.txt:44` 釘 `mcp==1.29.1`，落在 `>=1.27,<2` 之內。到期規則只比日期，和釘的版本無關〔讀碼推論〕。
4. CI 只在 push／PR 時觸發（`.github/workflows/tests.yml:7-11`），沒有排程。因此 11/1 之後，CI 要到下一次 push 或 PR 才會轉紅〔讀碼推論〕。
5. 〔讀碼推論〕`_howto` 的 `pip install -U` 會和 `.venv-gates` 的鎖定制度（票 156）衝突。在 `.venv-gates` 裡照做，已安裝版本就會偏離鎖定檔，`.claude/portable/runtime_identity.py` 的 `evaluate`（`:176-177`）會判「版本 … 與鎖定檔 … 不符」，結果是 `identity: FAIL`。票 156 票面沒有提到這個複審日（〔AIP-R0〕：Grep `10-31|10/31|ceiling|複審日` @ 票 156，`No matches found`）。

## 二、已裁

Jeff 2026-10-20 約 20:30（美東）的裁定，由裁決助手記錄，非逐字原話：

1. mcp 複審先開小票處理，要在 2026-10-31 之前收掉，排在「AI 正式執行管道」之前。
2. 處理方向：
   - 維持 `mcp>=1.27,<2`，不升 2.x；
   - 把複審日延後，並寫明理由；
   - 把 `_howto`（`tests/test_dependency_ceiling.py:62-70`）的複審步驟，改成符合票 156 鎖定檔制度的寫法。
3. 票號：157 = mcp 上限複審；158 = AI 正式執行管道（待立案）。

外部事實（裁決助手 2026-10-20 **網路查證，未在 repo 內驗證**）：PyPI 上已有 `mcp` 2.0.0 與 2.0.1。所以維持 `<2` 是一個真的選擇，不是「沒有新版可升」。升 2.x 另案評估，不在本票。

## 三、範圍

1. 決定新的複審日與理由，寫進 `pyproject.toml:63-68`。新日期**待裁**（見第六節），立案時不填。
2. 改 `_howto` 的複審步驟：照票 156 的流程（改鎖定檔、重建 `.venv-gates`、驗 `identity: ok`），不再寫 `pip install -U`。實際的指令寫法由紅燈站對照票 156 設計。
3. 紅燈先行：先寫一條測試，斷言 `_howto` 的文字**不再建議** `pip install -U`，而且會指向鎖定檔流程。這條測試要先紅，再實作轉綠。
4. 檢查 `docs/tickets/framework-updates/101-*.md:1017`、`:1025` 的文件提醒要不要同步。

## 四、不在範圍

- 升級 mcp 到 2.x（另案評估）。
- 改鎖定檔裡的 mcp 版本。
- pytest 的複審日（`pyproject.toml:62`，`2027-02-15`）。

## 五、驗收

1. 本機全套 0 failed。
2. 證明在新複審日之下，即使把「今天」假設成 2026-11-01，測試仍綠。做法由紅燈站設計（例如 monkeypatch `date.today`），**不改系統時間**。
3. push 後 CI 綠燈，由 Jeff 目視。

## 六、待裁

- ~~新的複審日，例如再延 3 個月或 6 個月。~~ 已裁：**2027-01-31**（延後 3 個月；Jeff 2026-10-20 約 20:42，美東，裁決助手記錄，非逐字原話）。

## 七、相關

- 票 158「AI 正式執行管道」（待立案）。Jeff 選「A＋B 都要」：A 是 U3 的正式執行通道，B 是減少逐步放行。本票不展開。
- 票 156（閘門執行環境的 Python 隔離；鎖定檔制度）。

## 八、修正紀錄

- 2026-10-20（美東）：立案。
- 2026-10-20（美東）：錨點 S1 —— 紅燈與修補完成（本機），見第九節。
- 2026-10-20（美東）：錨點 C1 —— 收票，見第十節。

## 九、S1 紀錄（紅燈＋修補＋全套，同一視窗連做；10/15 精簡流程規則②）

1. **新複審日**：`pyproject.toml` 的 `mcp-ceiling-review = "2027-01-31"`（Jeff 2026-10-20 約 20:42），理由註解補一句「2026-10-20 複審（票 157）：PyPI 已有 2.0.x；維持 `<2`……下次複審 2027-01-31」。`mcp>=1.27,<2` 與 pytest 兩行不動。
2. **改 `pyproject.toml` 不影響環境身分（讀碼依據）**：
   - Grep `pyproject` @ `.claude`：`runtime_identity.py`、`setup_gates_env.py`、`bin/gatepy`、`gate.py` 0 命中（四檔以 Glob 確認存在）。
   - 身分判定的輸入只有 `runtime_identity.py:128-184` `evaluate` 的 sys.prefix／base_prefix、Python 版本、已安裝 dists、兩份鎖定檔全文，再加上 marker 環境。
   - `redlight.py:747-770` 會記 `pyproject.toml` 的工作樹 blob 與 HEAD blob，但那是紅燈證據的完整性判定：工作樹 ≠ HEAD ⇒ `file_coverage` 為 `unknown`（`:2280-2284`），只影響 status 的退紅（`status.py:460`）。gate.py 不讀它；`tests` 列在非原始碼清單（`gate.py:277`）。
3. **紅燈**（修補前）：`-k t157` → `4 failed, 1 passed`，失敗原因都是 `AssertionError`。修補前就綠的是 `[2027-02-01-False]`，因為舊複審日 2026-10-31 早於 2027-02-01，「會失敗」這項本來就成立。
4. **修補**：
   - `_howto` 改成鎖定檔流程：改 `gates-lock*.txt`（連網需授權）→ 經同意重建（`setup_gates_env.py <repo> --profile upstream`）→ `runtime_identity.py --whoami` 確認 `identity: ok` → 全套 → 最後才改 `pyproject.toml`。全文不再出現 `pip install -U`。
   - 只改 `_howto` 之後：`2 failed, 3 passed`（兩支日期驗收項仍紅，符合預期）。
   - 再改 `pyproject.toml` 之後：整檔 `11 passed`。
5. **驗收 2**（`test_t157_mcp_review_date_acceptance`，只 monkeypatch 本模組的 `_dt`，不改系統時間、不改 `.claude/`）：
   - `[2026-11-01-True]` 通過；
   - `[2027-01-31-True]` 通過；
   - `[2027-02-01-False]` 通過（以 `pytest.raises(AssertionError)` 斷言原測試會紅）。
6. **其他新測試**：
   - `test_t157_howto_walks_the_lock_file_flow_in_order`：依第一次出現的位置判斷三步的先後。
   - `test_t157_howto_never_instructs_pip_install_upgrade`：逐行字面啟發式，帶否定詞的行視為引用，不是語意判定。
7. **票 101 兩處提醒**（`:1017`、`:1025`）：各補「已由票 157 延至 2027-01-31」，原文保留。
8. **全套**：`2848 passed, 10 skipped, 3 xfailed in 611.76s`，exit 0。passed = 2843 + 本票新增 5 項。
9. **已知副作用**：commit 前、`pyproject.toml` 工作樹 ≠ HEAD 時跑的 run，`file_coverage` 都是 `unknown`，status 不會替 `tests/test_dependency_ceiling.py` 退紅；要等 commit 後再跑一次完整 run。

## 十、收票紀錄（錨點 C1）

1. **線上驗證**：`bc7616a4a8e189af99c66f8afc3b1b3d5cb2db15` 的 push 事件 CI 綠燈（All checks have passed），Jeff 2026-10-20 約 21:23（美東）目視確認（裁決助手記錄，非逐字原話）。這次執行涵蓋了本票全部的實質修改。依票 156 裁決 A（證據先於宣告），收票在綠燈之後。
2. **依據**：
   - S1（`.dev/reports/2026-10-21T011222Z-ticket157-s1.md`）：全套 `2848 passed, 10 skipped, 3 xfailed`；驗收 2 三格（2026-11-01 綠、2027-01-31 綠、2027-02-01 紅）由 `test_t157_mcp_review_date_acceptance` 證明。
   - P1（`.dev/reports/2026-10-21T012142Z-ticket157-p1.md`）：push 前守衛全部通過，推送 `4e058d5..bc7616a`。
3. **「status 暫時紅」**：來源是 `.dev/test-sessions.jsonl` 裡該 run 的 `completeness.config_blobs`。`pyproject.toml` 工作樹 ≠ HEAD ⇒ `file_coverage` 判 `unknown` ⇒ status 不退紅。gate.py 不讀這本帳；R3 讀的是 `test-runs.jsonl`，欄位不含 pyproject blob ⇒ **不影響任何閘門判定**〔讀碼推論，見 P1 報告〕。
4. **收票裁定**：Jeff 2026-10-20 約 21:24（美東）裁定收票並授權 push（裁決助手記錄，非逐字原話）。
5. **後續**：`.dev/pipeline.json` 切回 idle 由 Jeff 處理。下一張是票 158「AI 正式執行管道」（待立案）。
