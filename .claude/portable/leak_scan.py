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

退出碼:0 = **掃過了而且乾淨**(掃了零個檔不算,見 `main()`),
       1 = 有命中(擋 commit),
       2 = 機制自身錯誤(**含:不認得的旗標、沒有給任何路徑**)。

⚠ `2` 那一格的括號是票 106 加的:它的涵蓋從「git 問不到清單」擴到
「呼叫方式不對」是**一次語意擴張**。不寫出來的話,下一個讀的人會以為
`2` 只在 git 壞掉時出現 —— **而那正是票 106 要修的那個誤解的鏡像**。
"""

import io
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scanner                                              # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# 票 106。**旗標是封閉集合,所以用枚舉不用 pattern**(`F-158` 的同一條)。
# 少了它,`--stage`(打錯的 `--staged`)會被當成「某個旗標」濾掉,
# 而 `paths` 變空 → 回 0 → **整層偵測靜默消失**,`|| exit 1` 也不觸發。
KNOWN_FLAGS = ("--staged", "--review", "--help", "-h")

# 用法字串 —— 與檔頭 `用法:` 那三行同一份內容。
# 兩份會漂開,而漂開的那一天沒有東西會說
# (同 `friction_heading.HEADING` 與 `gate._FRICTION_HEADING` 那兩份正則的教訓)。
USAGE = (u"用法:\n"
         u"  python .claude/portable/leak_scan.py --staged      掃 git staged 檔案(pre-commit)\n"
         u"  python .claude/portable/leak_scan.py <檔案...>      掃指定檔案\n"
         u"  旗標:--staged / --review / --help\n")
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

# ── 審查模式的副檔名**白名單**(票 39 / P2,裁決 4)────────────────────
#
# pre-commit 那個情境用黑名單(`SKIP_SUFFIX`)是對的:跳過二進位省時間也省雜訊。
# **公開審查的問題不一樣** —— 那裡「沒掃」與「掃過沒事」不能混為一談,
# 而黑名單的預設是「沒列到的就掃」,反過來說**被列到的一律靜默消失**。
#
# 審查要的是相反的預設:**只掃得懂的才掃,掃不懂的一律浮上來要人看。**
# 陌生副檔名(`.env.backup`、`.pem.old`、沒有副檔名的檔)在黑名單底下
# 會被「照掃、沒命中、放行」—— 而那三步沒有一步證明它是乾淨的。
#
# **方向與 ADR 0003 一致,不是它的例外。** 0003 講的黑名單列的是
# 「不管的東西」;這裡的清單列的是「要跳過的東西」——
# 同一個東西列在相反的欄位裡,所以要換一邊才維持同一個 deny-by-default 方向。
REVIEW_ALLOWED_EXT = (
    ".py", ".pyi", ".sh", ".ps1", ".bat",
    ".md", ".rst", ".txt", ".adoc",
    ".json", ".jsonl", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".csv", ".tsv", ".sql", ".xml", ".html", ".css", ".js", ".ts",
    ".gitignore", ".gitattributes", ".template",
)

REVIEW_HEADER = "未內容掃描"

# 憑證/金鑰檔:**依副檔名擋,不掃內容**。二進位憑證(.pfx/.p12/.jks/...)
# 任何編碼都解不開,掃內容永遠漏,而檔名是確定的。
# F-062 紅燈:260-byte 二進位 .pfx 進 staged,舊版回 0(沒擋)。
#
# `.p8`(PKCS#8 私鑰)與 `.p7b`(PKCS#7 簽章包)是票 23 補的。
# 補之前它們**完全 fail-open**:兩者都不在 SKIP_SUFFIX 裡,於是走完內容比對 ——
# 而掃描器對那些位元組解得出東西、沒命中、放行。實測五種形狀(可解碼文字、
# DER 二進位、PEM 但無私鑰標頭、大寫副檔名)全部回 0。
#
# **不要改用「內容有沒有私鑰標頭」來判。** PEM 的那份剛好打得到通用 pattern,
# 但同一種副檔名可以是 DER(純二進位、無標頭)—— 判定不能取決於手上這份
# 剛好是哪種編碼。副檔名判定的價值就在於不必知道內容長什麼樣。
#
# 大小寫由下方比對點的 `.lower()` 負責(`client.P8` 靠它才命中),
# 所以這裡一律小寫。拿掉那個 `.lower()` 會讓大寫副檔名整批放行。
CERT_EXT = (".pfx", ".p12", ".pem", ".key", ".jks", ".keystore", ".p8", ".p7b")


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


def review_allowed(rel):
    """審查模式:這個檔案的副檔名在白名單裡嗎?

    **沒有副檔名一律回 False。** `LICENSE`、`pre-commit` 這種檔在審查模式下
    要人看一眼 —— 「我認得這個檔」是人的知識,不是掃描器的。
    """
    ext = os.path.splitext(os.path.basename(rel))[1].lower()
    if not ext:
        # `.gitignore` 這種「整個名字都是副檔名」的:splitext 回 ('.gitignore', '')
        base = os.path.basename(rel).lower()
        return base in tuple(e.lower() for e in REVIEW_ALLOWED_EXT)
    return ext in REVIEW_ALLOWED_EXT


def scan(paths, review=False):
    """回 0 乾淨 / 1 有命中 / 2 機制錯誤(pattern 讀不到)。

    `review=True` 是**公開審查模式**(票 39):副檔名改白名單
    (deny-by-default),而且**未內容掃描的清單一律進報告**——
    含清單是空的那一次(Q5:「印出來是空的」與「沒印」是兩件事)。
    """
    try:
        groups = load_patterns()
    except Exception as e:
        _err("[洩漏偵測/fail-closed] 讀不到 pattern(%s):%s —— 一律擋。\n"
             % (PATTERNS_FILE, e))
        return 2

    certs, rest, not_scanned = [], [], []
    for p in paths:
        rel = scanner.rel_path(ROOT, p)
        if should_skip(p):
            if review:
                not_scanned.append((rel, "跳過清單(掃描器自己 / 類別豁免 / 二進位)"))
            continue
        if p.replace("\\", "/").lower().endswith(CERT_EXT):
            # 副檔名即判定,不讀內容 —— 二進位憑證檔的唯一可靠攔截點。
            certs.append(scanner.Hit(scanner.rel_path(ROOT, p), 0, "憑證副檔名",
                                     "<憑證副檔名>", "(依副檔名擋,不掃內容)"))
        elif review and not review_allowed(rel):
            not_scanned.append((rel, "非白名單副檔名 —— 需人工放行"))
        else:
            rest.append(p)

    hits = certs + scanner.scan_paths(rest, groups, root=ROOT,
                                      self_paths=SELF_PATHS)

    if review:
        # **必要部分,不是選項。** 清單不在,「跳過」這件事就不存在於報告上,
        # 於是等同沒發生 —— 而那正是「沒掃」被讀成「掃過沒事」的那一步。
        _err("\n[審查模式] %s 的檔案(%d):\n" % (REVIEW_HEADER, len(not_scanned)))
        if not not_scanned:
            _err("  (無)\n")
        for rel, why in not_scanned:
            _err("  %s\n     %s\n" % (rel, why))

    if not hits and not not_scanned:
        return 0
    if not hits:
        _err("\n未內容掃描的檔案要逐一定性 —— 「沒掃」不是「乾淨」。\n")
        return 1

    _err("\n[洩漏偵測] 這些檔案含個人身分或機密,擋下 commit:\n\n")
    for h in hits:
        _err("  %s:%d\n     命中 pattern:%s\n     內容:%s\n"
             % (h.path, h.line, h.pattern, h.context))
    _err("\n乾淨的歷史要在這條規則底下誕生 —— 先把上面的洗掉再 commit。\n")
    return 1


def gitlink_note(paths):
    """被跳過的 gitlink 進報告。**跳過要看得見,而且要說出由誰守。**

    靜默跳過的話,讀報告的人分不出「掃過沒事」與「根本沒掃」——
    票 39 的「未內容掃描清單一律進報告」是同一條規矩。
    這裡刻意不寫成「已跳過」就結束:外層對 gitlink 的正確語意是
    **這一格由內層 repo 自己守**(內層有自己的 pre-commit 跑本掃描器),
    而不是「這一格沒事」。兩者的差別是責任在誰身上。

    **不影響退出碼。** gitlink 進 `not_scanned` 那個桶的話,
    非空即回 1(見 `scan`),於是每一次 bump 都被擋 ——
    那是換一種方式重演本票要修的缺陷。
    """
    out = ["\n[洩漏偵測] 跳過 %d 格 gitlink(mode 160000)—— 沒有 blob 內容可掃:\n"
           % len(paths)]
    for p in paths:
        out.append("  %s\n" % p)
    out.append("     這一格記的是一個 commit sha,**由內層 repo 自己守**"
               "(它有自己的 pre-commit)。\n"
               "     外層掃得到的東西裡不包含它的內容 —— 這不是「掃過沒事」。\n")
    return "".join(out)


def main(argv):
    """`--staged` 取不到清單時回 2(機制錯誤),**不是 0**。

    回 0 的話,git 壞掉那一刻偵測就靜默消失,而 pre-commit 照樣放行 ——
    「沒有檔案要掃」與「問不到有哪些檔案」是兩件事。

    `--review` 開公開審查模式(票 39):副檔名白名單 + 未掃清單進報告。
    **刻意不是預設** —— 把審查模式的嚴格度倒灌回 pre-commit,
    每天的 commit 會開始被陌生副檔名擋,而**被煩到的規則會被關掉**。
    """
    if "--help" in argv or "-h" in argv:
        # **裁四(甲案)**:印用法、回 0。
        # 本票的病是**靜默**,不是 exit 0 本身 —— 印了用法就不靜默了,
        # 而「查用法回機制錯誤」會讓人以為裝壞了。
        _err(USAGE)
        return 0

    unknown = [a for a in argv if a.startswith("-") and a not in KNOWN_FLAGS]
    if unknown:
        # **點名那個旗標**,不只說「用法不對」。
        # 一個只說用法不對的訊息,對 `--stage`(少一個 `d`)這種錯幫不上忙 ——
        # 人會盯著那一行看半天,而差別只有一個字元。
        _err("[洩漏偵測/機制錯誤] 不認得的旗標:%s\n%s"
             % (" ".join(unknown), USAGE))
        return 2

    review = "--review" in argv
    if "--staged" in argv:
        gitlinks = []
        try:
            rels = scanner.staged_paths(cwd=ROOT, gitlinks=gitlinks)
        except scanner.StagedListingFailed as e:
            _err("[洩漏偵測/fail-closed] %s —— 一律擋。\n" % e)
            return 2
        if gitlinks:
            _err(gitlink_note(gitlinks))
        paths = [os.path.join(ROOT, p.replace("/", os.sep)) for p in rels]
        # ⚠ **這裡【刻意】允許空清單回 0**(票 106 裁二)。
        # C 碰得到:`git commit --allow-empty`、**純刪除**(本函式用
        # `--diff-filter=ACM`,`D` 不在裡面)、mode-only 改動。
        # 把它判成 2,就是把「**沒有東西要掃這回事**」判成「掃描機制壞了」,
        # 造出一個**永遠無法滿足的條件** —— 使用者沒有任何合法動作
        # 能讓一個 `--allow-empty` 的 commit 變得「有檔案可掃」。
        # `scanner.py` 對 gitlink 逐字記過同一個教訓。
        #
        # **「問不到」早就回 2 了**(上面那個 `StagedListingFailed`),
        # 所以這裡回 0 是對的,不是漏網。
        # 負控:`tests/test_leak_scan.py::…::test_an_empty_staged_list_still_returns_zero`。
        return scan(paths, review=review) if paths else 0

    paths = [a for a in argv if not a.startswith("-")]
    if not paths:
        _err("[洩漏偵測/機制錯誤] 沒有給任何路徑,而且沒有 --staged。\n%s" % USAGE)
        return 2
    return scan(paths, review=review)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
