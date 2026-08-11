# 06 — enforcement 檔全走人覆蓋(甲案),搬家後再議

## 由來

影子模式的安全閥 SHADOW_MAX 用乙案保護:住在 G1 保護的 `shadow-clamp.txt`,
gate.py 唯讀。乙**防「順手改設定」,防不了「改 gate.py 讓它不讀 clamp」**。

好意犯錯模型下這個差距是可接受的(設定會被隨手調,讀設定的碼較不會被隨手改),
但它是真缺口(ADR 0012 殘留 1)。

## 完整解:甲案

enforcement 檔(gate.py / redlight.py / g1_guard.py / leak_scan.py)的改動,
全走 ADR 0009 的人覆蓋流程:草稿放非權威位置、跑驗收、附 diff、**人**覆蓋。
agent 寫不了正式檔。

現況(查證於 2026-08-11):這些檔在 agent-gates 裡 agent 全改得動,
gate.py 還是 R2 豁免(明確允許編輯)。

## 為什麼搬家後再議

代價高:框架自身開發每次改 gate.py 都要人手動覆蓋。搬家期間(八到十月)
不適合引入這種摩擦。等影子模式量測完、搬家結束再評估甲值不值得。

## 怎樣算做完

- enforcement 檔的改動無法由 agent 直接寫入正式位置
- 但框架開發流程仍可運作(草稿→驗收→人覆蓋,不是卡死)
- SHADOW_MAX 的「寫死」名副其實(agent 連 gate.py 都改不了讓它不讀)
