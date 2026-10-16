# 票 155 —— M1-b 階段 3（Flutter）：候選

**狀態**：**候選（未排程）。**
**時鐘**：無。依 `docs/agents/issue-tracker.md:34-36`，說不出時鐘的票停在 `candidate`。可能的觸發事件：LifeApp 框架改選 Flutter 時。
**優先度**：未定。
**立案**：2026-10-16（美東）。Jeff 2026-10-16 同意另開 Flutter 候選票，並確認票號 155；建檔前已確認 `docs/tickets/framework-updates/` 內沒有 155 開頭的檔案。
**交叉引用**：票 154（M1-b 階段 3，Kotlin）；〔R0〕`.dev/reports/2026-10-16T153620Z-ticket-stage3-r0-recon.md`；規格 `<path>\M1-B-NONPYTHON-ADAPTER-SPEC-v3.md`（sha256 `af735dbd679b59618b451fc65fdf804408da04fe1555f7cd44edc4b03259cf3f`）。

---

## 為何另開

- 〔讀碼推論〕包裝器只呼叫 `dart`，不呼叫 `flutter`（`.claude/hooks/redlight_run.py:436-438` `_dart_argv` 回 `["dart", "test", "--file-reporter", …]`；R0 3-3 推論 2）。
- 依賴 `flutter_test` 的 Flutter 專案能不能用 `dart test` 跑：UNKNOWN。
- ⇒ Dart 的階段 3 即使通過，也不能據此宣稱 Flutter 專案可用。

## 規格依據

- 規格 :43（M1-b 目標句）與 :158（E1「Dart／Flutter：`--file-reporter json:<本次目錄>/report.json`」）提到 Flutter／Dart。
- 規格 §5（:213-228）與 AC-B40～B45（:305-310）只說「各語言」「Dart」。
- Flutter 是否需要獨立的階段 3：**規格未定義**。

## 範圍

待立案時定。

---

## 修正紀錄

- 建檔（2026-10-16，裁決助手記錄，非逐字原話）：Jeff 2026-10-16 約 12:50（美東）裁決「Flutter 另開候選票，先不排程」。~~票號 155 為候選號，未經 Jeff 核准。~~ Jeff 2026-10-16 約 13:05 確認票號 155。
