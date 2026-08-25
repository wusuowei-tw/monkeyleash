# ADR 0012 — 影子模式:裝進既有 repo 的 rollout 工具

日期:2026-08-11
狀態:已採納

## 問題

把閘門裝進一個**既有、無測試**的 repo,R1–R8 會立刻擋掉大量既有工作
(量化 repo 實測 121 個 .py、0 個測試)。需要一個「先不擋、只量測」的階段:
裝上去、記錄每一筆「本該擋」、量誤擋率,達標了才真的開始擋。

## 機制

- 本 repo 宣告:`.dev/shadow.json` = `{"until": "YYYY-MM-DD"}`。
- 安全閥:`~/.claude/shadow-clamp.txt` 一行 `SHADOW_MAX=<ISO 日期>`,**硬上限**。
- 影子生效 iff:兩個檔都在 且 `今天 <= min(shadow.json.until, SHADOW_MAX)`。
- 生效時,每個「本該擋」改為寫進 `.dev/shadow-log.jsonl`(ts/rule/at_commit/message),
  然後放行。**決策放在進入點**(mode_hook / mode_pre_commit),check() 保持純判定。
- **G1 不進影子** —— 它是檔案系統破壞性指令防護,不是流程規則,永遠擋。

## 安全閥防篡改(乙案)

SHADOW_MAX 住在 **G1 保護的** `~/.claude/shadow-clamp.txt`,gate.py **唯讀**。
agent 改不了它(要改得走 ADR 0009 的人覆蓋流程)。

**為什麼安全閥要防篡改,而 shadow-log 不用(F-057)**:
證據可以接受竄改風險,控制項不可。shadow-log 是事後證據,竄改後果是晉升判斷失準,
而逐筆分類會撞到不一致(看得見);SHADOW_MAX 是安全閥,竄改後果是閘門形同關閉
且**沒有人會發現**(看不見)。③ 接受的「不防篡改」適用範圍到證據為止。

## fail-closed 方向

安全閥缺席 / 讀不到 / 格式壞掉 / 日期無效 → 影子**不生效、照常擋**。
**往「閘門開著」倒,不往「影子開著」倒** —— 安全閥的故障不能變成閘門的關閉。
有測試釘這個方向(`TestShadowActiveFailsClosed`),淨室有 live 探針。

BOM 之坑:clamp 用 `utf-8-sig` 讀。PowerShell 的 `Set-Content -Encoding utf8`
寫的是帶 BOM 的 UTF-8;用 utf-8 讀、BOM 黏上鍵名 → 解析失敗 → fail-closed →
影子永遠開不了,而所有訊息都說「照常擋,正常」。fail-closed 系統的故障是隱形的,
輸入端的坑要在進門前排掉。

## 晉升:per-rule,不全局

每條規則**自己** ≥10 筆已分類 且 假陽率 <5% 才可轉正;不足 10 筆留影子。
全局比率會讓一條規則的真陽稀釋另一條的假陽(「R2 很準」被誤讀成「R3 也能開」)。

**逐筆判,不算總數**:五類分類(一真陽、四種假陽:範圍/時點/既有/解析),
每類對應一種修法。晉升率從分類算,不能靠「總共擋幾次」。工具:`shadow_review.py`。

## 兩個殘留缺口(誠實寫下,不修)

1. **乙防「順手改設定」,防不了「改 gate.py 讓它不讀 clamp」。**
   設定會被隨手調,讀設定的碼較不會被隨手改 —— 好意犯錯模型下這個差距就是乙的價值。
   完整解是甲(enforcement 檔全走人覆蓋,ADR 0009 擴到 gate.py)。
   **立票,搬家後再議**(docs/tickets/framework-updates/06)。
2. **晉升後、SHADOW_MAX 前,agent 可自我重開影子(夾到 9/15)。**
   接受,因為**自癒**:9/15 之後 SHADOW_MAX 過期,影子物理上不可能存在,
   不管 agent 怎麼寫 shadow.json。缺口有底,終點是寫死的日期。

## 參數

`SHADOW_MAX = 2026-09-15`(避開使用者八到十月搬家,影子不能搬家途中過期)、
窗 14 天、每規則 ≥10 筆已分類、假陽率 <5%。
