# -*- coding: utf-8 -*-
"""掃描器共骨架 —— 掃 staged 檔案、比對 pattern、擋下 commit。

`leak_scan.py`(金鑰/個人身分)與下游的 `cookie_ban.py`(下載層零認證)
原本是兩份各自演化的實作,同一件事在兩邊寫了兩次,而且**失效方向已經分岔**:
一邊讀不動就 fail-closed,另一邊 `except: continue` 靜默跳過。
一個事實兩個來源(F-058 家族),再繞一圈。

合一的核心約束:**豁免綁在規則組上,不是綁在掃描器上。**

  `.md` 裡的 cookie 選項名 -> 放行(規則的說明本身必須寫得出來)
  `.md` 裡的金鑰           -> 擋  (散文裡的金鑰就是外洩的金鑰)

同一個副檔名,兩個相反的正確答案。一套豁免套用全部 pattern 的話,合一本身
就會把這個差異壓平 —— 而壓平的方向是 **fail-open**(取寬的那一邊)。
所以 `RuleGroup` 自帶適用範圍,不是共用一份全域豁免。

失效方向:掃描器失效的方向是**靜默放行**,所以本檔一切「不確定」往擋的方向倒:
讀不到位元組、任何編碼都解不開、取不到 staged 清單 —— 全部計為違規或例外,
不得翻譯成「這個檔案沒問題」。
"""

import io
import os
import re
import subprocess
import unicodedata


# 解碼順序。**latin-1 永不失敗**,所以最後一關保證有東西可掃:要找的 pattern
# 全是 ASCII,亂碼不影響它們的可見性。寧可拿到亂碼也要掃。
#
# 只用 utf-8 的後果不是假想:zh-TW Windows 上 cp950 是預設編碼,
# 一個 cp950 的 .ps1 裡寫著金鑰,UnicodeDecodeError 被吞掉之後**整個檔案靜默跳過**。
DECODINGS = ("utf-8-sig", "utf-8", "cp950", "cp1252", "latin-1")

# 不掃這些:二進位、鏡像、快取。判準是「內容不是文字,掃了只會有雜訊」。
SKIP_SUFFIX = (".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".gz",
               ".pyc", ".otf", ".ttf", ".woff", ".woff2", ".parquet", ".duckdb")
# ── 跳過清單分成兩類,因為它們的**錨定方式不同**(票 39 / P2 第五件)──
#
# 舊版是單一 tuple + **子字串**比對,於是一條裸的 `skills/`
# 把正典 `.agents/skills/` 一起吞掉 —— 39 個進版控、會跟著公開走的檔案
# **從來沒有被內容掃描過**,而報告一路全綠。
#
# 這一族在本 repo 早就被命名過:`g1_guard.py` 的 docstring 寫著
# 「前綴要帶邊界…… 與 `.gitignore` 的 `skills/` 缺前導斜線同一族」。
# **教訓學在一個地方,隔壁的資料從來沒有回頭重掃**(F-082 的形狀)。
# 正確形狀 repo 裡也有現成的:`gate.py:is_source_path` 取 `r.split("/")[0]`。
#
# 分類判準:**這個東西是「某個固定位置的目錄」還是「任何深度都算」?**
#   - 鏡像有固定位置(都在 repo 根),所以根錨定
#   - 快取與巢狀 repo 到處都有,所以任何深度 —— 但**要帶分段邊界**

# 根錨定:只有 repo 根底下的這些才算(鏡像的位置是構造決定的,不會浮動)
SKIP_ROOTS = ("skills/", ".claude/skills/")

# 任何深度,但**兩側都要帶 `/` 邊界** ——
# `foo.git/` 不是 `.git/`,`my.cache/` 不是 `.cache/`,`myskills/` 不是 `skills/`。
SKIP_PARTS = (".git/", "__pycache__/", ".pytest_cache/", ".cache/")

UNREADABLE = "<讀不到內容>"


class StagedListingFailed(Exception):
    """取不到 staged 清單。**不能當成「沒有檔案要掃」** —— 那是 fail-open。"""


class Hit(object):
    """一筆命中。`context` 已遮罩,可以安全印出來。"""

    __slots__ = ("path", "line", "group", "pattern", "context")

    def __init__(self, path, line, group, pattern, context):
        self.path = path
        self.line = line
        self.group = group
        self.pattern = pattern
        self.context = context

    def __repr__(self):
        return "Hit(%s:%s, %s, %s)" % (self.path, self.line, self.group,
                                       self.pattern)


class RuleGroup(object):
    """一組 pattern **加上它自己的適用範圍**。

    `skip_suffix` / `skip_basenames` / `exempt` 都是**這一組**的豁免,
    不影響別組。合一的核心約束就是這件事:同一個檔案可以對一組免掃、
    對另一組照掃,而那正是 `.md` 上金鑰與 cookie 選項名的差別。

    `show_pattern=False` 用於個人 pattern —— 它們本身往往就是秘密
    (使用者名稱、往來對象),印出來等於在報告裡再洩一次(F-067)。
    """

    def __init__(self, name, patterns, skip_suffix=(), skip_basenames=(),
                 exempt=None, flags=0, show_pattern=True):
        self.name = name
        self.patterns = [(p, re.compile(p, flags)) for p in patterns]
        # 大小寫不敏感的**第二份**編譯(票 39 / P2,裁決 3)。
        # **另編一份而不是改原本那份**:原本那份的大小寫敏感性是某些 pattern
        # 的判定依據(`\bAKIA[A-Z0-9]{16}` 靠大寫縮小誤判),直接加
        # IGNORECASE 會讓那類 pattern 變寬。兩份都跑、取聯集,涵蓋只增不減。
        self.patterns_ci = [(p, re.compile(p, flags | re.IGNORECASE))
                            for p in patterns]
        self.skip_suffix = tuple(s.lower() for s in skip_suffix)
        self.skip_basenames = tuple(b.lower() for b in skip_basenames)
        self.exempt = exempt
        self.show_pattern = show_pattern

    def applies_to(self, rel):
        r = rel.lower()
        if self.skip_suffix and r.endswith(self.skip_suffix):
            return False
        if os.path.basename(r) in self.skip_basenames:
            return False
        if self.exempt is not None and self.exempt(rel):
            return False
        return True

    def label(self, raw, index):
        return raw if self.show_pattern else (
            "%s pattern #%d(不顯示內容)" % (self.name, index))


# 零寬字元:插在秘密中間就讓比對整條失效,而**肉眼完全看不出來**。
# 最惡劣的地方不是它難擋,是**貼上去的人自己也看不見** ——
# 從剪貼簿帶進來的零寬字元不需要任何惡意就能讓一條規則消失。
ZERO_WIDTH = "​‌‍⁠﻿"


def normalize_for_match(s):
    """比對用的正規化形式(票 39 / P2,裁決 3)。

    **只做兩件事**:NFKC 相容性正規化 + 濾除零寬字元。
    大小寫由 `RuleGroup.patterns_ci` 那一份負責,不在這裡折 ——
    折在這裡的話會連**報告要印的原文**一起折掉。

    **NFKC 折不動同形字。** 西里爾 `С`(U+0421)、希臘 `Ϲ`(U+03F9)
    在 NFKC 之後仍然不是拉丁 `C`:NFKC 處理的是**相容性**差異
    (全形、連字、上下標),不是**視覺相似**。同形字要另一套映射
    (Unicode TR39 的 confusables / skeleton),**本輪不做,歸妥協聲明** ——
    把它算進「已處理」就是製造一格假涵蓋(票 39)。
    """
    return "".join(c for c in unicodedata.normalize("NFKC", s)
                   if c not in ZERO_WIDTH)


# ── UTF-16 與可讀性(票 109)────────────────────────────────────────────────
#
# **問題不是「階梯裡沒有 utf-16」,是「階梯裡有好幾格會【成功】解開 UTF-16」。**
# 解出來的東西夾著 NUL,任何要求連續字元的 pattern 都打不到 ⇒ 那個檔
# 不是「掃過乾淨」,是**解成亂碼之後沒命中**,而兩者的回傳值一模一樣。
#
# 哪一格接走它**取決於內容**(票 109 實測):
#   含 CJK           -> latin-1(第 5 格)
#   純 ASCII 無 BOM  -> **utf-8-sig(第 1 格)** —— ASCII 與 NUL 都是合法 UTF-8
#   純 ASCII 有 BOM  -> **cp1252(第 4 格)** —— FF FE 是合法 cp1252
# 真實的 `.env` 幾乎都是純 ASCII,所以**最可能發生的案例走的是第 1 格**。
# ⇒ 判定不能只掛在 latin-1 後面。
#
# **`latin-1` 對全部 256 個位元組值都成功**(枚舉實測,測試釘住)⇒ 舊版
# `return None, "任何已知編碼都解不開"` 是**死碼**,從來沒被執行過。
# 那一行看起來是這支函式的 fail-closed 出口,而**保底編碼把它消掉了** ——
# 兩段程式各自都對,是它們的組合出的問題。

# BOM 是**封閉集合**(兩個位元組序列),所以用枚舉不用 pattern(`F-087` 同款)。
UTF16_BOMS = (b"\xff\xfe", b"\xfe\xff")

# 「這串解出來的東西還算文字嗎」的門檻:控制字元(含 NUL)佔比。
# 實測(票 109):正常文字 ~0%;含少量 NUL 的 UTF-8 檔 0.8%;
# UTF-16 被單位元組編碼解開 4.3%(全 CJK)~ 50%(純 ASCII);隨機位元組 ~12.9%。
# 2% 落在「含少量 NUL 的真文字」與「最低的 UTF-16」之間,**兩側都有實測值**。
UNREADABLE_MAX = 0.02

# 裁決 B 的 NUL 佔比:**這是快路徑,不是唯一的保證**。
# 它讓「解出來一半是 NUL」在階梯中途就被認出來,不必等走完;
# 真正保證涵蓋的是底下第 ③ 步(階梯全不可讀 -> 再試一次 utf-16),
# 而**那一步不依賴任何門檻**。兩者都留:快路徑讓意圖看得見,
# 保證掛在不會因為門檻訂錯而消失的那一步上。
NUL_TRIGGER = 0.10


def _control_ratio(s):
    """控制字元(含 NUL)佔比。`\\t` `\\n` `\\r` 是正常文字的一部分,不算。"""
    if not s:
        return 0.0
    bad = sum(1 for c in s
              if (ord(c) < 32 and c not in "\t\n\r") or ord(c) == 127)
    return float(bad) / len(s)


def _nul_ratio(s):
    return (float(s.count(u"\x00")) / len(s)) if s else 0.0


def looks_readable(s):
    """這串東西還算文字嗎。**空字串算可讀**(空檔案不是壞檔案)。"""
    return _control_ratio(s) <= UNREADABLE_MAX


def _decode_utf16(raw):
    """試 LE / BE 兩種 UTF-16,回**第一個可讀的**結果;都不可讀回 None。

    **可讀性檢查是必要的一半。** 少了它,任何偶數長度的位元組流都能被
    utf-16 解出「某個東西」,於是這條路自己變成新的靜默漏放。
    """
    for enc in ("utf-16-le", "utf-16-be"):
        try:
            t = raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
        if looks_readable(t):
            return t
    return None


def read_text(path):
    """讀檔並解碼。回 `(text, None)` 或 `(None, 理由)` —— 理由非空即 fail-closed。

    **先拿位元組再依序解碼。** 讀不到位元組(權限、路徑壞掉)不是「沒問題」,
    是「這個問題沒有答案」,呼叫端一律計為違規。

    票 109 之後的順序:① BOM 嗅探 → ② 原本的階梯(每一格的結果都要過
    可讀性檢查)→ ③ 階梯全不可讀時再試一次 utf-16 → ④ 都不可讀就 fail-closed。

    **`latin-1` 不再是保底。** 它仍在階梯裡,但它的結果與別格一樣要過檢查 ——
    這正是把那條死掉的 fail-closed 出口叫醒的那一步。
    """
    try:
        with io.open(path, "rb") as f:
            raw = f.read()
    except Exception as e:                                   # noqa: BLE001
        return None, "讀不到檔案:%s" % e

    # 空檔案是合法的文字檔,不是壞檔案 —— 這一格要在所有檢查之前。
    if not raw:
        return u"", None

    # ① BOM 嗅探。**BOM 說了算**:它是產生端寫下的宣告,不是讀的人的猜測
    #    (與「判『遮過沒』的權威在產生端」同一條)。
    if raw[:2] in UTF16_BOMS:
        try:
            t = raw.decode("utf-16")          # 由 BOM 自己決定 LE/BE
            if looks_readable(t):
                return t, None
        except (UnicodeDecodeError, LookupError):
            pass

    # ② 原本的階梯。差別是:**解得開不等於可以用。**
    for enc in DECODINGS:
        try:
            t = raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
        # 裁決 B 的快路徑:一半是 NUL 的「文字」多半是被單位元組編碼
        # 讀進來的 UTF-16 —— 當場改試,不必等走完階梯。
        if _nul_ratio(t) >= NUL_TRIGGER:
            u16 = _decode_utf16(raw)
            if u16 is not None:
                return u16, None
        if looks_readable(t):
            return t, None
        # 解得開但不可讀 -> 這一格不算數,繼續試下一格。

    # ③ 階梯裡沒有一格給出可讀的東西。**無 BOM 又含 CJK 的 UTF-16 走到這裡** ——
    #    它的 NUL 佔比低到 4.3%,快路徑接不住,而這一步不依賴門檻。
    u16 = _decode_utf16(raw)
    if u16 is not None:
        return u16, None

    # ④ 真正的 fail-closed 出口 —— 票 109 之前這裡是死碼。
    return None, "解不出可讀文字(控制字元佔比過高,可能是二進位或未知編碼)"


# git 的檔案模式是**封閉集合**,所以判定用枚舉、不用 pattern:
# 040000 目錄 / 100644 一般檔 / 100755 可執行檔 / 120000 symlink / 160000 gitlink。
# 「比對的漏是未知的,枚舉的漏是不存在的」(F-087)。
GITLINK_MODE = "160000"


def index_modes(cwd=None):
    """index 裡每條路徑的 mode。問不到 -> 丟 `StagedListingFailed`(fail-closed)。

    **判定依據是 index,不是檔案系統。** 用 `os.path.isdir()` 判「這是不是
    submodule」的話,問題就跑到磁碟上去了 —— 而磁碟上的樣子隨時會變
    (目錄被搬走、submodule 沒 init、有人放了一個同名檔),
    **index 的 mode 才是 git 對「這一格是什麼」的答案**。

    fail-closed 的方向:問不到 mode = 這個問題**沒有答案**,不是「都不是 gitlink」。
    往「一律當檔案」倒的話 gitlink 又回到 open() 那條路;往「一律跳過」倒更糟 ——
    那會把整份 staged 清單靜默清空。兩種都不對,所以丟例外。
    """
    out = subprocess.run(["git", "ls-files", "--stage", "-z"],
                         capture_output=True, cwd=cwd)
    if out.returncode != 0:
        raise StagedListingFailed(
            "git ls-files --stage 失敗(退出碼 %s):%s"
            % (out.returncode, (out.stderr or b"").decode("utf-8", "replace")[:200]))
    modes = {}
    for rec in out.stdout.decode("utf-8", "replace").split("\0"):
        if not rec.strip():
            continue
        meta, _, path = rec.partition("\t")     # `<mode> <sha> <stage>\t<path>`
        fields = meta.split()
        if path and fields:
            modes[path] = fields[0]
    return modes


def staged_paths(cwd=None, gitlinks=None):
    """staged **檔案**清單。**-z(NUL 分隔),而且要看退出碼。**

    git 對非 ASCII 檔名回傳 C-quoted 路徑;直接 splitlines 拿到的是壞路徑,
    開不了檔 -> 被當成讀不動 -> 靜默不掃(F-064)。

    **退出碼要看。** 不看的話,git 因為任何理由失敗 -> stdout 空 -> 清單空 ->
    呼叫端回 0 -> pre-commit 放行。權威層沒有 fail-open 的餘地。

    **gitlink(mode 160000)不是檔案,不進清單**(票 42)。
    `--name-only` 對 submodule 條目回傳**目錄路徑**,而 index 裡它的值是一個
    commit sha —— **沒有 blob 內容可掃**。掃描器拿它去 `open()`,Windows 得
    `PermissionError`、POSIX 得 `IsADirectoryError`,兩者都落進「讀不到內容」的
    fail-closed 分支,於是擋下 commit。

    「讀不到不等於乾淨」這條規則的正當性,對**應該是檔案**的東西成立;
    對 gitlink 它把「**沒有內容這回事**」判成「內容讀不到」,產生一個
    **永遠無法滿足的條件** —— 使用者沒有任何合法動作能讓它變乾淨,
    因為沒有東西可以洗。實測:下游因此連 bump 都做不出來。

    `gitlinks`:呼叫端傳入的收集串列,被跳過的那幾格會 append 進去,
    **讓跳過看得見**(票 39:未內容掃描的清單一律進報告)。
    外層對 gitlink 的正確語意是「**這一格由內層 repo 自己守**」——
    內層有自己的 pre-commit,寫清楚比靜默跳過重要。

    **回傳型別不變(仍是路徑串列)。** 不改成 `(paths, skipped)`:
    票 13 C 的教訓是簽名一改,忘了解包的呼叫端會靜默拿到錯的東西 ——
    `(False, "…")` 在 `if` 裡是真的,fail-closed 整條翻成 fail-open 而測試全綠。
    走收集串列就沒有那個失敗模式(形狀同 `gate.check(..., exemptions=[])`)。
    """
    out = subprocess.run(["git", "diff", "--cached", "-z", "--name-only",
                          "--diff-filter=ACM"], capture_output=True, cwd=cwd)
    if out.returncode != 0:
        raise StagedListingFailed(
            "git diff --cached 失敗(退出碼 %s):%s"
            % (out.returncode, (out.stderr or b"").decode("utf-8", "replace")[:200]))
    paths = [p for p in out.stdout.decode("utf-8", "replace").split("\0")
             if p.strip()]
    if not paths:
        return []
    modes = index_modes(cwd)
    kept = []
    for p in paths:
        if modes.get(p) == GITLINK_MODE:
            if gitlinks is not None:
                gitlinks.append(p)
            continue
        kept.append(p)
    return kept


def rel_path(root, path):
    """轉成 repo 相對路徑(正斜線)。repo 外的維持原樣。"""
    r = os.path.abspath(path).replace("\\", "/")
    base = os.path.abspath(root).replace("\\", "/").rstrip("/") + "/"
    return r[len(base):] if r.startswith(base) else path.replace("\\", "/")


def redact(text, matched):
    """把命中的那一段換掉再輸出。

    **掃描器的輸出本身是外流面。** 擋下 commit 的那一刻,原本要防的東西會被
    原樣印進終端機、CI log、agent 對話紀錄 —— 剛好是最多眼睛在看的時候。
    保留行號與前後文足夠定位;完整值使用者本來就知道(F-066/F-067)。
    """
    if not matched:
        return text
    return text.replace(matched, "***已遮罩 %d 字***" % len(matched))


def _globally_skipped(rel, self_paths, skip_suffix, skip_parts,
                      skip_roots=SKIP_ROOTS):
    """所有規則組共通的跳過:二進位、鏡像/快取目錄、掃描器自己。

    self-skip **綁 repo 相對路徑,不綁檔名** —— 綁檔名的話豁免的鑰匙就握在
    要規避的人手上:任何目錄放一個同名檔就免掃,而那個檔名誰都造得出來。

    **兩種錨定,不要合成一種**(票 39 / P2 第五件):
      `skip_roots` 根錨定 —— 鏡像的位置是構造決定的,不會浮動
      `skip_parts` 任何深度,但**兩側帶 `/` 邊界** ——
                   `foo.git/` 不是 `.git/`,`myskills/` 不是 `skills/`

    合成一種的代價已經量過:裸的 `skills/` 做子字串比對,
    把正典 `.agents/skills/` 的 39 個檔一起吞掉,而報告全綠。
    """
    if rel in self_paths:
        return True
    if rel.lower().endswith(tuple(s.lower() for s in skip_suffix)):
        return True
    if any(rel == r.rstrip("/") or rel.startswith(r) for r in skip_roots):
        return True
    # 兩側都補 `/`,讓「片段在開頭 / 中間 / 結尾」用同一個式子判,
    # 而且**片段兩側必然是分隔符** —— 這就是「帶邊界」的具體形式。
    padded = "/" + rel + "/"
    return any(("/" + p) in padded for p in skip_parts)


def scan_paths(paths, groups, root=".", self_paths=(),
               skip_suffix=SKIP_SUFFIX, skip_parts=SKIP_PARTS):
    """掃一批檔案,回傳 `Hit` 串列(空 = 乾淨)。

    只回結果不印、不決定退出碼 —— 呈現與退出碼屬於各掃描器的入口,
    這裡只負責判定。這樣兩支掃描器共用的是**判定**,而它們各自的訊息
    (被擋時該怎麼辦)本來就不一樣,不該被合一硬壓成同一句。
    """
    self_paths = tuple(p.replace("\\", "/") for p in self_paths)
    hits = []
    for p in paths:
        rel = rel_path(root, p)
        if _globally_skipped(rel, self_paths, skip_suffix, skip_parts):
            continue
        active = [g for g in groups if g.applies_to(rel)]
        if not active:
            continue

        text, why = read_text(p)
        if why is not None:
            # **讀不動 ≠ 沒問題。** 已知的二進位副檔名在上面就濾掉了;
            # 走到這裡還讀不動的是意料外的東西,而意料外的東西一律擋。
            hits.append(Hit(rel, 0, UNREADABLE, UNREADABLE, why))
            continue

        for i, line in enumerate(text.split("\n"), 1):
            # **先收齊這一行的所有命中,再決定怎麼遮**(票 32)。
            #
            # 原本是逐命中各自產生一個 Hit、各自只遮**自己那一段**,
            # 於是同一行的兩份報告**各自洩漏對方遮掉的那一半** ——
            # 每一行單獨看都合格,而讀報告的人拿到的是全部。
            #
            # **防護的單位(一次命中)小於洩漏的單位(一整行)。**
            # F-067 解的是「一次命中」,這裡補的是它的多命中形式。
            #
            # **比對面有三種形式**(票 39 / P2,裁決 3),取聯集:
            #   原文 × 大小寫敏感   -> 原本就有的那一輪,一個字沒動
            #   原文 × 大小寫不敏感 -> 大寫/混寫形式
            #   正規化 × 兩者       -> 全形、零寬
            # **聯集不是取代**:正規化會折掉大小寫與相容字,而折掉的東西
            # 有可能正是某條 pattern 要的。取代的話涵蓋會變小,而**變小的
            # 方向沒有任何測試會抱怨** —— 除了本檔那條反控。
            norm = normalize_for_match(line)
            variants = [line] if norm == line else [line, norm]

            line_hits, seen = [], set()
            for g in active:
                for compiled in (g.patterns, g.patterns_ci):
                    for n, (raw, rx) in enumerate(compiled, 1):
                        if (id(g), n) in seen:
                            continue
                        for v in variants:
                            m = rx.search(v)
                            if m:
                                seen.add((id(g), n))
                                line_hits.append((g, raw, n, m))
                                break
            if not line_hits:
                continue
            snippet = line.strip()[:100]

            # **遮罩安全性**:命中那一段必須在**原文裡真的存在**,
            # 否則 `redact()` 的 `replace` 什麼都換不到 —— 於是原始那一行
            # **原樣印出來**,在擋下的那一刻把秘密印進終端機。
            # 對不回去就不猜,整行遮(與票 32 同一個判準)。
            unmappable = [h for h in line_hits if h[3].group(0) not in line]

            if len(line_hits) == 1 and not unmappable:
                # 單一命中維持 F-067 的形狀:遮命中那一段,**前後文留得住**
                #(「遮罩過頭 —— 前後文要留得住,否則定位不了」)。
                g, raw, n, m = line_hits[0]
                hits.append(Hit(rel, i, g.name, g.label(raw, n),
                                redact(snippet, m.group(0))))
            elif unmappable:
                masked = ("***整行已遮罩(命中只在正規化後可見,"
                          "無法安全對回原文)***")
                for g, raw, n, _m in line_hits:
                    hits.append(Hit(rel, i, g.name, g.label(raw, n), masked))
            else:
                # 多命中 -> **整行遮**。前後文在這一行上不可能安全保留:
                # 任何留下來的片段都是別份報告遮掉的那一半。
                # 定位改靠**路徑 + 行號**,那兩個本來就在 Hit 裡。
                masked = "***整行已遮罩(同一行 %d 條命中,分段遮罩可拼回)***" \
                    % len(line_hits)
                for g, raw, n, _m in line_hits:
                    hits.append(Hit(rel, i, g.name, g.label(raw, n), masked))
    return hits
