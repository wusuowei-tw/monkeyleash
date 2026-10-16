# tests/fixtures/redlight_run —— 合成樣本

**本目錄每一個檔案都是合成樣本**（票 152 批二，規格 v3 §6 階段 2：自製樣本標「合成樣本」）。
不是任何真實 Dart／Flutter／Gradle 執行的輸出；本票沒有執行任何真實工具鏈。
真實輸出形狀由階段 3（另票，需 Q-ENV 授權）確認；屆時若與本目錄不同，
**先同步修改規格與測試**，不得由實作自行更換。

JSON 不能放註解，所以逐檔列在這裡：

| 檔案 | 合成樣本 | 形狀依據 | 用在 |
|---|---|---|---|
| `dart_failure.jsonl` | 合成樣本 | 〔D-json〕JSON reporter 事件，每行一個：`start`、`allSuites`、`suite`（`path`）、載入虛擬測試（`testDone.hidden: true`）、一個 `failure`、`done` | AC-B25、B22、B22b、B23、B30、B31、B33、F3、E1-a |
| `dart_load_error.jsonl` | 合成樣本 | 〔D-json〕載入虛擬測試（`hidden: true`）`result: error`。**真實載入失敗的事件長相待階段 3**（規格 AC-B26、AC-B43） | AC-B26 |
| `dart_other_suite.jsonl` | 合成樣本 | 只有 `test/bar_test.dart` 的 suite —— 被指定的 `test/foo_test.dart` 不在輸出中 | AC-B24 |
| `dart_all_skipped.jsonl` | 合成樣本 | 唯一的非隱藏測試 `skipped: true` | AC-B33 |
| `dart_unknown_result.jsonl` | 合成樣本 | `testDone.result` 為協定外的值 `timeout` | AC-B34 |
| `kotlin_compile_red.json` | 合成樣本 | 暫定協定（見下）：產品編譯本次執行成功、測試編譯本次執行失敗、`compile_errors` 含測試檔路徑 | AC-B27、B28 |
| `kotlin_test_red.json` | 合成樣本 | 暫定協定：測試任務本次執行、一個測試 `failure` | AC-B33、B34 |
| `kotlin_green.json` | 合成樣本 | 暫定協定：全部本次執行、測試 `success` | AC-B33、E1-b |
| `kotlin_class_mismatch.json` | 合成樣本 | 暫定協定：結果類別 `y.FooTest`，轉回的路徑對不上 `x/FooTest.kt` | AC-B29 |

- Kotlin 樣本裡的 `{ROOT}` 是佔位符，測試在寫進本次輸出目錄前換成暫存 repo 根（posix）。
- 測試裡另有幾格是**在本目錄樣本上做的變形**（例：拿掉 `done`、改 `outcome`、截斷），
  一樣是合成樣本，變形寫在各測試的 docstring 與程式碼裡。

## Kotlin 暫定協定（初始化腳本 → 包裝器）

**不是 Gradle 原生格式。** 這是批二的初始化腳本（產出端，`.claude/hooks/redlight_gradle_init.gradle`）
與包裝器（讀取端，`.claude/hooks/redlight_run.py`）之間的協定，兩端都必須遵守。
權威全文在 `tests/test_redlight_run.py` 的模組 docstring；本段是同一份的摘要，兩者不一致時以測試檔為準。
