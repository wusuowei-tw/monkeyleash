#!/bin/sh
# 六站閘門 — 洩漏偵測 + 權威判定。邏輯不在這裡,只呼叫共用腳本。
# 洩漏偵測在前:秘密一旦進了歷史,擋下 commit 是唯一便宜的時點。
# 之前只接 gate.py —— 裝出來的 repo 對真 key 的 commit 完全放行(負控實測),
# 而 F-055 說的就是洩漏 hook 不會自己跟過去。接線是安裝器的責任。
# 直譯器只經 .claude/bin/gatepy 取 .venv-gates(票 156);不退回 .venv 或 PATH 上的 python。
root="$(git rev-parse --show-toplevel)"
sh "$root/.claude/bin/gatepy" "$root/.claude/portable/leak_scan.py" --staged || exit 1
exec sh "$root/.claude/bin/gatepy" "$root/.claude/hooks/gate.py" --pre-commit
