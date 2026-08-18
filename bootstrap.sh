#!/bin/sh
# 權威層接線 —— **每個 clone 跑一次**。
#
#     sh bootstrap.sh
#
# ── 為什麼需要這一步 ─────────────────────────────────────────────────────
# `.git/hooks/` 依 git 設計不進版控,clone 不會帶走它 —— 新 clone 上權威層
# 預設就是不在的,而且缺席**幾乎無聲**:前哨照跑、測試照綠。
# agent-gates 自己就這樣過了 40 個 commit,一次權威判定都沒發生過(ADR 0007)。
#
# ── 為什麼不能自動 ───────────────────────────────────────────────────────
# `core.hooksPath` 是 local config,不隨 clone 走。它把「複製一個檔案」換成
# 「跑一行 config」,**沒有消除那一步,只是縮短**。零接觸不可能:
# git 刻意不讓 clone 自動執行任何東西,那是安全設計不是缺陷(ADR 0007)。
#
# ── 為什麼會拒絕動手(三道 fail-closed)─────────────────────────────────
# **設了 core.hooksPath 之後,`.git/hooks/` 被 git 整個忽略。**
# 那一行 config 因此是本 repo 唯一「跑下去就可能靜默關掉閘門」的動作:
#
#   缺 hook 檔      指過去的目錄是空的 -> 權威層當場消失(F-065)
#   hook 不在 index 沒進版控就不隨 clone 走 -> 下一個 clone 又回到起點
#   mode 不是 755   git 不執行沒有執行位元的 hook,**而且不出聲**
#
# 三者的共同點:**出事之後前哨照跑、測試照綠,沒有任何東西會說話。**
# 所以檢查放在設定之前,而不是設定之後才驗。
#
# **約束寫在提交順序裡會過期,寫在腳本裡不會。** 批次切分只擋得住我們這一次;
# 任何人在別的機器上單獨拿這支去跑,危險原樣存在。
#
# ── 本 repo 的兩條歷史(票 27 / 票 51 ⑥,不刪)─────────────────────────
# 兩條掛載路徑**以 core.hooksPath 為準**:有設 -> git 只跑那個目錄裡的 hook,
# `.git/hooks/` 整個被忽略;沒設 -> git 跑 `.git/hooks/`。
# 兩支現在**兩段都接**(leak_scan + gate.py --pre-commit),所以走哪條都不掉權威層。
# (那個數字原寫「三層」—— 只有兩個階段,票 51 ⑥ 更正。)
# 在此之前 `.githooks/` 只有 leak_scan,而 core.hooksPath 從未設定 ——
# 於是「文件寫的機制」與「實際生效的機制」不是同一個,兩年份的 commit
# 沒有經過權威層判定,而且完全靜默(票 27)。
#
# ── 這三道從哪裡來(票 58)───────────────────────────────────────────────
# **下游先做出更好的版本,上游吸收回來。** 三道 fail-closed 出自量化那一份,
# 上游這一份更早卻沒有。判斷順序與措辭原樣帶走,只換兩處本 repo 專屬的東西。
# **上游這份必須是下游那份的超集** —— D3 之後安裝器會開始產 bootstrap.sh,
# 而 bootstrap.sh 標 skip、兩份永遠不會自動對齊:上游若少一道,
# 量化將來重跑 install 就會被**降級**,丟掉它自己那三道。
set -e

root="$(git rev-parse --show-toplevel)"
cd "$root"

hook=".githooks/pre-commit"

if [ ! -f "$hook" ]; then
    echo "[bootstrap/fail-closed] 找不到 $hook —— 拒絕設定 core.hooksPath。" >&2
    echo "     設下去會讓 .git/hooks/ 被整個忽略,而指過去的目錄是空的:" >&2
    echo "     六站權威層當場消失,而且不會有任何訊息。" >&2
    exit 1
fi

# **看 index 不看檔案系統。** Windows 的檔案系統根本不帶執行位元,
# 在本機問「這支有沒有執行權限」永遠得到錯的答案;git 的 index 才是跨平台的權威。
mode="$(git ls-files -s -- "$hook" | cut -d' ' -f1)"

if [ -z "$mode" ]; then
    echo "[bootstrap/fail-closed] $hook 不在 git index 裡 —— 拒絕設定 core.hooksPath。" >&2
    echo "     沒進版控的 hook 不隨 clone 走,而那正是 core.hooksPath 要解的問題:" >&2
    echo "     設下去只會讓這台機器看起來接上了,下一個 clone 仍然沒有。" >&2
    exit 1
fi

if [ "$mode" != "100755" ]; then
    echo "[bootstrap/fail-closed] $hook 的 index mode 是 $mode,不是 100755 —— 拒絕設定。" >&2
    echo "     git 不執行沒有執行位元的 hook,**而且不會出聲** ——" >&2
    echo "     Windows 上本機測不出這件事,CI(Linux)才會踩到。" >&2
    echo "     修法:git update-index --chmod=+x $hook" >&2
    exit 1
fi

git config core.hooksPath .githooks

echo "[bootstrap] core.hooksPath -> .githooks"
echo "     驗收(問的是行為,不是檔案在不在):"
echo "     python -m pytest tests/test_gate.py::TestAuthorityLayerIsWired tests/test_bootstrap.py"
