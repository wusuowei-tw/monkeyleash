# -*- coding: utf-8 -*-
"""洩漏偵測:掃檔案有沒有個人身分/機密。pre-commit 用,也可手動掃。

用法:
  python .claude/portable/leak_scan.py --staged      掃 git staged 檔案(pre-commit)
  python .claude/portable/leak_scan.py <檔案...>      掃指定檔案

**fail-closed**:pattern 檔讀不到 → 當作有問題 → 擋。
讀不到就放行的話,刪掉 pattern 檔就等於關掉洩漏偵測 —— 那是最廉價的繞法。

退出碼:0 = 乾淨,1 = 有命中(擋 commit),2 = 機制自身錯誤(pattern 讀不到等)。
"""

import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# 通用形狀,進版控,可公開。
PATTERNS_FILE = os.path.join(HERE, "leak-patterns.txt")
# 個人 token(使用者名稱、資料夾名、券商),**不進版控**,與 g1-protected.txt 同層。
# 兩份聯集 —— 機制/個人資料分離,與 G1 同構。缺這份不是錯(別台機器就沒有);
# 缺通用那份才是 fail-closed。
LOCAL_PATTERNS_FILE = os.path.join(os.path.expanduser("~"), ".claude",
                                   "leak-patterns.local.txt")


def _err(msg):
    """stderr 明確走 utf-8 —— pre-commit 環境常是 cp950,直接 write 中文會炸,
    而炸掉的 hook 會用一個看不懂的錯誤擋 commit(F-042)。"""
    try:
        sys.stderr.buffer.write(msg.encode("utf-8"))
        sys.stderr.buffer.flush()
    except Exception:
        sys.stderr.write(msg)

# 不掃這些:二進位、鏡像、快取、pattern 檔自己(它本來就含要偵測的字樣)。
# .gitignore 同一類:它的工作就是列出秘密檔的形狀(*.pfx 之類),
# 內容掃它必然假陽性 —— 安裝器產的秘密檔區塊實測就被自己擋過(F-062)。
SKIP_SUFFIX = (".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".gz",
               ".pyc", ".otf", ".ttf", ".woff", ".woff2", ".parquet", ".duckdb")
SKIP_PARTS = (".git/", ".claude/skills/", "skills/", "__pycache__/",
              ".pytest_cache/", ".cache/", ".dev/")
SELF = {"leak-patterns.txt", "leak_scan.py", ".gitignore"}

# 憑證/金鑰檔:**依副檔名擋,不掃內容**。二進位憑證(.pfx/.p12/.jks/...)
# utf-8 解不開會被 scan() 的 except 跳過 —— 掃內容永遠漏,而檔名是確定的。
# F-062 紅燈:260-byte 二進位 .pfx 進 staged,leak_scan 舊版回 0(沒擋)。
# 這一層與 leak-patterns.txt 的 \.pfx\b 內容 pattern 互補:那條擋文字檔裡
# 提到憑證路徑,這條擋憑證檔本身進 commit。
CERT_EXT = (".pfx", ".p12", ".pem", ".key", ".jks", ".keystore")


def _read_patterns(path, required):
    """讀一個 pattern 檔。required 且讀不到 → 丟例外(fail-closed);
    非 required 且不存在 → 回空(別台機器沒有個人清單很正常)。"""
    if not required and not os.path.exists(path):
        return []
    out = []
    for line in io.open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        out.append((line, re.compile(line)))
    return out


def load_patterns():
    """通用(必需)+ 個人(選用)兩份的聯集。

    通用那份讀不到 → fail-closed(呼叫端擋)。
    個人那份缺 → **不 fail-closed**(個人 pattern 本來跟人走,別台機器沒有很正常),
    但**顯式警告,不無痕** —— 缺了個人清單,掃描只剩通用形狀,涵蓋比你以為的小,
    而那件事必須看得見。個人 token 靠掃描擋的部分這時沒有守。
    """
    out = _read_patterns(PATTERNS_FILE, required=True)
    if os.path.exists(LOCAL_PATTERNS_FILE):
        out += _read_patterns(LOCAL_PATTERNS_FILE, required=False)
    else:
        _err("[洩漏偵測/警告] 找不到個人 pattern 清單 %s —— "
             "只用通用形狀掃,個人 token(使用者名稱/資料夾名/往來對象)這輪沒有守。\n"
             "     這不是錯(個人清單跟人走),但缺了要看得見。\n"
             % LOCAL_PATTERNS_FILE)
    if not out:
        raise ValueError("pattern 檔沒有任何有效 pattern")
    return out


def staged_files(cwd=None):
    """staged 檔案清單。**-z(NUL 分隔),不是 --name-only + splitlines。**

    這裡的失效方向是 **fail-open,比閘門那邊更危險**:git 對非 ASCII 檔名回傳
    C-quoted 路徑,壞掉的路徑 `io.open` 開不起來,而 scan() 對開不動的檔案
    `except: continue`(「讀不動的不是洩漏」)—— 於是**中文檔名檔案裡的金鑰
    完全不會被掃到,而且一聲不吭**。同一個編碼假設,在閘門是誤擋(看得見),
    在這裡是靜默放行。見 F-042 家族。
    """
    out = subprocess.run(["git", "diff", "--cached", "-z", "--name-only",
                          "--diff-filter=ACM"], capture_output=True, cwd=cwd)
    return [p for p in out.stdout.decode("utf-8", "replace").split("\0") if p.strip()]


def should_skip(rel):
    r = rel.replace("\\", "/")
    if os.path.basename(r) in SELF:
        return True
    if r.endswith(SKIP_SUFFIX):
        return True
    return any(p in ("/" + r + "/") for p in SKIP_PARTS) or \
        any(r.startswith(p) for p in SKIP_PARTS)


def scan(paths):
    try:
        patterns = load_patterns()
    except Exception as e:
        _err("[洩漏偵測/fail-closed] 讀不到 pattern(%s):%s —— 一律擋。\n"
                         % (PATTERNS_FILE, e))
        return 2
    hits = []
    for p in paths:
        if should_skip(p):
            continue
        if p.replace("\\", "/").lower().endswith(CERT_EXT):
            # 副檔名即判定,不讀內容 —— 二進位憑證檔的唯一可靠攔截點。
            hits.append((p, 0, "<憑證副檔名>", "(依副檔名擋,不掃內容)"))
            continue
        try:
            text = io.open(p, encoding="utf-8").read()
        except Exception:
            continue  # 讀不動(二進位等)不是洩漏
        for i, line in enumerate(text.split("\n"), 1):
            for raw, rx in patterns:
                if rx.search(line):
                    hits.append((p, i, raw, line.strip()[:100]))
    if hits:
        _err("\n[洩漏偵測] 這些檔案含個人身分或機密,擋下 commit:\n\n")
        for f, i, raw, ctx in hits:
            _err("  %s:%d\n     命中 pattern:%s\n     內容:%s\n"
                             % (f, i, raw, ctx))
        _err("\n乾淨的歷史要在這條規則底下誕生 —— 先把上面的洗掉再 commit。\n")
        return 1
    return 0


def main(argv):
    if "--staged" in argv:
        paths = staged_files()
    else:
        paths = [a for a in argv if not a.startswith("--")]
    if not paths:
        return 0
    return scan(paths)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
