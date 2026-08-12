# -*- coding: utf-8 -*-
"""洩漏偵測:掃檔案有沒有個人身分/機密。pre-commit 用,也可手動掃。

判定邏輯住在 `scanner.py`(與下游的 cookie 護欄共用同一副骨架);本檔只負責
**這一種掃描的組態**:pattern 從哪來、哪些檔案是自己、命中之後怎麼講。

用法:
  python .claude/portable/leak_scan.py --staged      掃 git staged 檔案(pre-commit)
  python .claude/portable/leak_scan.py <檔案...>      掃指定檔案

**fail-closed**:pattern 檔讀不到 → 擋;檔案讀不動 → 計為違規;
staged 清單問不到 → 機制錯誤。讀不到就放行的話,刪掉 pattern 檔就等於關掉偵測。

**散文不豁免。** 下游的 cookie 護欄對 `.md` 免掃(規則的說明本身必須寫得出來),
那個理由對**選項名**成立,對**金鑰**完全不成立 —— `.md` 裡的金鑰就是外洩的金鑰。
豁免綁在規則組上,所以合一沒有把這個差異壓平。

退出碼:0 = 乾淨,1 = 有命中(擋 commit),2 = 機制自身錯誤。
"""

import io
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scanner                                              # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

# 通用形狀,進版控,可公開。
PATTERNS_FILE = os.path.join(HERE, "leak-patterns.txt")
# 個人 token(使用者名稱、資料夾名、券商),**不進版控**,與 g1-protected.txt 同層。
# 兩份聯集 —— 機制/個人資料分離,與 G1 同構。缺這份不是錯(別台機器就沒有);
# 缺通用那份才是 fail-closed。
LOCAL_PATTERNS_FILE = os.path.join(os.path.expanduser("~"), ".claude",
                                   "leak-patterns.local.txt")

# 掃描器不掃自己:pattern 檔本來就寫著要偵測的字樣,本檔也提到它們。
#
# **綁 repo 相對路徑,不綁檔名。** 綁檔名的話豁免的鑰匙就握在要規避的人手上:
# 任何目錄放一個叫 leak_scan.py 的檔就免掃,而那個檔名誰都造得出來。
# 形式照 gate.py 的 GATE_SELF —— 那裡一開始就是路徑。
SELF_PATHS = (".claude/portable/leak_scan.py",
              ".claude/portable/leak-patterns.txt")

# **這是另一種豁免,不要跟 SELF_PATHS 混為一談。**
# SELF_PATHS 是**身分**豁免(只有那一個具體檔案);這裡是**內容類別**豁免
# —— 任何 .gitignore 的工作都是列出秘密檔的形狀(*.pfx 之類),掃它必然假陽性
# (F-062 實測:安裝器產的秘密檔區塊被自己擋下)。類別豁免綁檔名是對的,
# 因為它對每一個同類檔案都成立;身分豁免綁檔名就是開後門。
SKIP_BASENAMES = (".gitignore",)

# 憑證/金鑰檔:**依副檔名擋,不掃內容**。二進位憑證(.pfx/.p12/.jks/...)
# 任何編碼都解不開,掃內容永遠漏,而檔名是確定的。
# F-062 紅燈:260-byte 二進位 .pfx 進 staged,舊版回 0(沒擋)。
CERT_EXT = (".pfx", ".p12", ".pem", ".key", ".jks", ".keystore")


def _err(msg):
    """stderr 明確走 utf-8 —— pre-commit 環境常是 cp950,直接 write 中文會炸,
    而炸掉的 hook 會用一個看不懂的錯誤擋 commit(F-042)。"""
    try:
        sys.stderr.buffer.write(msg.encode("utf-8"))
        sys.stderr.buffer.flush()
    except Exception:
        sys.stderr.write(msg)


def _read_patterns(path, required):
    """讀一個 pattern 檔。required 且讀不到 → 丟例外(fail-closed);
    非 required 且不存在 → 回空(別台機器沒有個人清單很正常)。

    **用 utf-8-sig。** PowerShell 的 `Set-Content -Encoding utf8` 寫的是帶 BOM 的
    UTF-8,用 `utf-8` 讀的話 BOM 會變成第一條 pattern 的一部分 ——
    那條規則從此永遠不命中,少了一條規則而且完全無聲。
    """
    if not required and not os.path.exists(path):
        return []
    out = []
    for line in io.open(path, encoding="utf-8-sig"):
        line = line.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        out.append(line)
    return out


def load_patterns():
    """通用(必需)+ 個人(選用)。回傳兩個 `RuleGroup`。

    個人那份缺 → **不 fail-closed**(個人 pattern 跟人走,別台機器沒有很正常),
    但**顯式警告,不無痕** —— 缺了個人清單,涵蓋比你以為的小,而那件事必須看得見。

    兩組都**不豁免散文**:金鑰出現在 .md 裡就是外洩。
    """
    generic = _read_patterns(PATTERNS_FILE, required=True)
    personal = _read_patterns(LOCAL_PATTERNS_FILE, required=False) \
        if os.path.exists(LOCAL_PATTERNS_FILE) else []
    if not os.path.exists(LOCAL_PATTERNS_FILE):
        _err("[洩漏偵測/警告] 找不到個人 pattern 清單 %s —— "
             "只用通用形狀掃,個人 token(使用者名稱/資料夾名/往來對象)這輪沒有守。\n"
             "     這不是錯(個人清單跟人走),但缺了要看得見。\n"
             % LOCAL_PATTERNS_FILE)
    if not generic and not personal:
        raise ValueError("pattern 檔沒有任何有效 pattern")

    groups = [scanner.RuleGroup("通用", generic)]
    if personal:
        # 個人 pattern **不印原文** —— 它們本身往往就是秘密(使用者名稱、
        # 往來對象、甚至金鑰字面),印出來等於在報告裡再洩一次(F-067)。
        groups.append(scanner.RuleGroup("個人", personal, show_pattern=False))
    return groups


def should_skip(rel):
    """全域跳過:掃描器自己(路徑)、.gitignore(類別)、二進位、鏡像/快取。"""
    r = scanner.rel_path(ROOT, rel)
    if os.path.basename(r).lower() in SKIP_BASENAMES:
        return True
    return scanner._globally_skipped(r, SELF_PATHS, scanner.SKIP_SUFFIX,
                                     scanner.SKIP_PARTS)


def scan(paths):
    """回 0 乾淨 / 1 有命中 / 2 機制錯誤(pattern 讀不到)。"""
    try:
        groups = load_patterns()
    except Exception as e:
        _err("[洩漏偵測/fail-closed] 讀不到 pattern(%s):%s —— 一律擋。\n"
             % (PATTERNS_FILE, e))
        return 2

    certs, rest = [], []
    for p in paths:
        if should_skip(p):
            continue
        if p.replace("\\", "/").lower().endswith(CERT_EXT):
            # 副檔名即判定,不讀內容 —— 二進位憑證檔的唯一可靠攔截點。
            certs.append(scanner.Hit(scanner.rel_path(ROOT, p), 0, "憑證副檔名",
                                     "<憑證副檔名>", "(依副檔名擋,不掃內容)"))
        else:
            rest.append(p)

    hits = certs + scanner.scan_paths(rest, groups, root=ROOT,
                                      self_paths=SELF_PATHS)
    if not hits:
        return 0

    _err("\n[洩漏偵測] 這些檔案含個人身分或機密,擋下 commit:\n\n")
    for h in hits:
        _err("  %s:%d\n     命中 pattern:%s\n     內容:%s\n"
             % (h.path, h.line, h.pattern, h.context))
    _err("\n乾淨的歷史要在這條規則底下誕生 —— 先把上面的洗掉再 commit。\n")
    return 1


def main(argv):
    """`--staged` 取不到清單時回 2(機制錯誤),**不是 0**。

    回 0 的話,git 壞掉那一刻偵測就靜默消失,而 pre-commit 照樣放行 ——
    「沒有檔案要掃」與「問不到有哪些檔案」是兩件事。
    """
    if "--staged" in argv:
        try:
            rels = scanner.staged_paths(cwd=ROOT)
        except scanner.StagedListingFailed as e:
            _err("[洩漏偵測/fail-closed] %s —— 一律擋。\n" % e)
            return 2
        paths = [os.path.join(ROOT, p.replace("/", os.sep)) for p in rels]
    else:
        paths = [a for a in argv if not a.startswith("--")]
    return scan(paths) if paths else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
