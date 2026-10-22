# 160 — 找不到實作被記成「實作不存在」，R3 Python 路徑因此略過 HEAD 雜湊比對

**狀態**：候選，待裁；不在本站處理。
**來源**：票 159 獨立審查 N1（2026-10-22）；Jeff 2026-10-22 約 07:58（美東）決定另開票登記，之後再修，連同 K3 一起看（裁決助手記錄，非逐字原話）。
**相關**：K3（`find_implementation` 取第一個同名檔）、`F-167`、票 159。

---

## 一、現象

`redlight.record_run` 拿到 `find_implementation` 回的 None 時，寫出 `impl_file: null, impl_exists: false, impl_hash: null`；`gate.redlight_missing` 的 Python 路徑看到 `impl_exists` 為 False 就直接放行，不走 HEAD 雜湊比對。於是「找不到實作」與「實作不存在（新檔）」混成同一種紀錄。

## 二、影響

票 159 讓 None 變多，這個混同的影響面跟著變大。

## 三、可能方向（未裁）

- `impl=None` 時 `impl_exists` 記為 null；
- 或 R3 那側改用實作檔是否存在於 HEAD 來判定。

兩者都要動 gate.py（權威層），需裁決。

## 四、修正紀錄

- 2026-10-22（美東）：立案（候選）。
