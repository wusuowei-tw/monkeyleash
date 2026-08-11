#!/bin/sh
# clone 之後跑一次,啟用進版控的 git hooks(目前是洩漏偵測 pre-commit)。
#
# 為什麼需要這一步:git hooks 住在 .git/hooks/,而 .git/ 不進版控 ——
# clone 不會帶走它。把 hook 放在版控的 .githooks/ 再用 core.hooksPath 指過來,
# 就跟著 clone 走了;但「指過來」這行 config 是 local 的,每個 clone 要跑一次。
# 零接觸不可能(git 刻意不讓 clone 自動執行任何東西),這一行是最小接觸。
set -e
cd "$(git rev-parse --show-toplevel)"
git config core.hooksPath .githooks
echo "已啟用 .githooks(洩漏偵測 pre-commit)。"
echo "驗一次:對含 C:\\Users\\<真實帳號> 之類的檔案試 commit,應被擋。"
