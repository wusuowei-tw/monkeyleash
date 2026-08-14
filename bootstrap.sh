#!/bin/sh
# clone 之後跑一次,啟用進版控的 git hooks(洩漏偵測 + 六站閘門權威層)。
#
# 為什麼需要這一步:git hooks 住在 .git/hooks/,而 .git/ 不進版控 ——
# clone 不會帶走它。把 hook 放在版控的 .githooks/ 再用 core.hooksPath 指過來,
# 就跟著 clone 走了;但「指過來」這行 config 是 local 的,每個 clone 要跑一次。
# 零接觸不可能(git 刻意不讓 clone 自動執行任何東西),這一行是最小接觸。
#
# **兩條掛載路徑,以 core.hooksPath 為準**(票 27 釐清):
#   core.hooksPath 有設 -> git 只跑那個目錄裡的 hook,.git/hooks/ 整個被忽略
#   沒設             -> git 跑 .git/hooks/
# 兩支現在都是三層(leak_scan + gate.py --pre-commit),所以走哪條都不掉權威層。
# 在此之前 .githooks/ 只有 leak_scan,而 core.hooksPath 從未設定 ——
# 於是「文件寫的機制」與「實際生效的機制」不是同一個,兩年份的 commit
# 沒有經過權威層判定,而且完全靜默(票 27)。
set -e
cd "$(git rev-parse --show-toplevel)"
git config core.hooksPath .githooks
echo "已啟用 .githooks(洩漏偵測 + 權威層 pre-commit)。"
echo
echo "驗收 —— **裝好的定義是驗證通過,不是 config 設完**:"
echo "  1. 洩漏:對含 C:\\Users\\<真實帳號> 之類的檔案試 commit,應被擋。"
echo "  2. 權威層:python -m pytest tests/test_gate.py::TestAuthorityLayerIsWired"
echo "     那條金絲雀問的是「git 實際會執行的那一支有沒有接上」——"
echo "     檔案在、可讀、內容對,是三件事。"
