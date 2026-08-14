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


# 解碼順序。**latin-1 永不失敗**,所以最後一關保證有東西可掃:要找的 pattern
# 全是 ASCII,亂碼不影響它們的可見性。寧可拿到亂碼也要掃。
#
# 只用 utf-8 的後果不是假想:zh-TW Windows 上 cp950 是預設編碼,
# 一個 cp950 的 .ps1 裡寫著金鑰,UnicodeDecodeError 被吞掉之後**整個檔案靜默跳過**。
DECODINGS = ("utf-8-sig", "utf-8", "cp950", "cp1252", "latin-1")

# 不掃這些:二進位、鏡像、快取。判準是「內容不是文字,掃了只會有雜訊」。
SKIP_SUFFIX = (".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".gz",
               ".pyc", ".otf", ".ttf", ".woff", ".woff2", ".parquet", ".duckdb")
SKIP_PARTS = (".git/", ".claude/skills/", "skills/", "__pycache__/",
              ".pytest_cache/", ".cache/")

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


def read_text(path):
    """讀檔並解碼。回 `(text, None)` 或 `(None, 理由)` —— 理由非空即 fail-closed。

    **先拿位元組再依序解碼。** 讀不到位元組(權限、路徑壞掉)不是「沒問題」,
    是「這個問題沒有答案」,呼叫端一律計為違規。
    """
    try:
        with io.open(path, "rb") as f:
            raw = f.read()
    except Exception as e:                                   # noqa: BLE001
        return None, "讀不到檔案:%s" % e
    for enc in DECODINGS:
        try:
            return raw.decode(enc), None
        except (UnicodeDecodeError, LookupError):
            continue
    return None, "任何已知編碼都解不開"


def staged_paths(cwd=None):
    """staged 檔案清單。**-z(NUL 分隔),而且要看退出碼。**

    git 對非 ASCII 檔名回傳 C-quoted 路徑;直接 splitlines 拿到的是壞路徑,
    開不了檔 -> 被當成讀不動 -> 靜默不掃(F-064)。

    **退出碼要看。** 不看的話,git 因為任何理由失敗 -> stdout 空 -> 清單空 ->
    呼叫端回 0 -> pre-commit 放行。權威層沒有 fail-open 的餘地。
    """
    out = subprocess.run(["git", "diff", "--cached", "-z", "--name-only",
                          "--diff-filter=ACM"], capture_output=True, cwd=cwd)
    if out.returncode != 0:
        raise StagedListingFailed(
            "git diff --cached 失敗(退出碼 %s):%s"
            % (out.returncode, (out.stderr or b"").decode("utf-8", "replace")[:200]))
    return [p for p in out.stdout.decode("utf-8", "replace").split("\0")
            if p.strip()]


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


def _globally_skipped(rel, self_paths, skip_suffix, skip_parts):
    """所有規則組共通的跳過:二進位、鏡像/快取目錄、掃描器自己。

    self-skip **綁 repo 相對路徑,不綁檔名** —— 綁檔名的話豁免的鑰匙就握在
    要規避的人手上:任何目錄放一個同名檔就免掃,而那個檔名誰都造得出來。
    """
    if rel in self_paths:
        return True
    if rel.lower().endswith(tuple(s.lower() for s in skip_suffix)):
        return True
    padded = "/" + rel + "/"
    return any(p in padded for p in skip_parts) or \
        any(rel.startswith(p) for p in skip_parts)


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
            line_hits = []
            for g in active:
                for n, (raw, rx) in enumerate(g.patterns, 1):
                    m = rx.search(line)
                    if m:
                        line_hits.append((g, raw, n, m))
            if not line_hits:
                continue
            snippet = line.strip()[:100]
            if len(line_hits) == 1:
                # 單一命中維持 F-067 的形狀:遮命中那一段,**前後文留得住**
                #(「遮罩過頭 —— 前後文要留得住,否則定位不了」)。
                g, raw, n, m = line_hits[0]
                hits.append(Hit(rel, i, g.name, g.label(raw, n),
                                redact(snippet, m.group(0))))
            else:
                # 多命中 -> **整行遮**。前後文在這一行上不可能安全保留:
                # 任何留下來的片段都是別份報告遮掉的那一半。
                # 定位改靠**路徑 + 行號**,那兩個本來就在 Hit 裡。
                masked = "***整行已遮罩(同一行 %d 條命中,分段遮罩可拼回)***" \
                    % len(line_hits)
                for g, raw, n, _m in line_hits:
                    hits.append(Hit(rel, i, g.name, g.label(raw, n), masked))
    return hits
