#!/bin/sh
# 唯一允許的 skills 更新入口。
# 不准直接跑 `npx skills update` —— 它會靜默覆蓋正典裡的本地 patch。
# 三步:更新 -> 重套 patch(冪等) -> 全規則驗證。任一步失敗即中止。
set -e
cd "$(git rev-parse --show-toplevel)"

echo "[1/3] npx skills update"
npx --yes skills@latest update -y -p

echo "[2/3] 重套本地 patch"
python .claude/patches/apply_patches.py

echo "[3/3] 驗證(gate.py 全規則)"
python .claude/hooks/gate.py --pre-commit

echo "OK — skills 已更新且 patch 完整"
