# -*- coding: utf-8 -*-
r"""G1 —— agent 檔案系統災難防護。使用者層,涵蓋所有專案。

**本 docstring 是 raw string,而那個 `r` 不是風格。** 底下第一級那一段舉的例子
含反斜線;不加 `r` 的話它是一個無效跳脫序列,今天只發 DeprecationWarning,
而 Python 3.12 起這一族已轉 SyntaxWarning、更晚的版本規劃改成 SyntaxError ——
**屆時本檔直接 import 失敗,而它是 G1 的守衛本體。**
守著這件事的是 `tests/test_g1_guard.py` 的
`test_the_guard_body_still_compiles_when_warnings_are_errors`(量化 TSI-037)。

**與 R 系列相反的設計。** R 系列是流程規則:**性質上**各自獨立、可分開裝,
每個專案自己決定要不要。G1 是災難防護:任何專案都該開,
所以住在 ~/.claude/ 而不是某個 repo 裡。

**上面那句是性質描述,不是功能宣告** —— 目前沒有 per-repo 開關,
R 系列在裝了閘門的 repo 裡全部無條件生效。

**刻意不寫成閉區間。** 寫死一個結尾編號會讓讀的人認定它後面那一條不存在,
而那一條存在:R8(生產程式碼不得 import `research/`)在下游擋過人。
規則代號的權威來源是 `gate.py` 的 `rule_codes()` —— 它從規則自己的擋下訊息
掃出來,加一條規則就自動涵蓋,不必有人記得回來改一份對照表。

也不用 R 系列的做法列舉危險指令 —— rm / del / Remove-Item / rmtree /
git clean / 某支會刪檔的腳本…那個清單列不完,而列不完的清單就是 fail-open。

## 兩級,成本不同所以判準不同

**第一級 —— 保護清單:出現即擋,無豁免,不解析指令。**
純文字比對。指令字串裡出現保護路徑就擋,不管它是讀是寫。
看似粗暴,但誤擋成本近乎零:日常工作不會碰 `D:\<你的備份目錄>`。
而「解析指令判斷是讀是寫」會引入解析失敗的可能,那才是真的洞。

**第二級 —— 其他專案外路徑:只有破壞性動詞才擋。**
這一級**必須寬鬆**。原本想做「專案外一律擋 + 解析不出來就擋」,
在使用者層會每天擋幾十次,然後它會被關掉 ——
**被煩到的規則會被關掉,而關掉的規則涵蓋率是零。**
吵鬧的訊號訓練人忽略訊號,那不是理論,是這個 repo 的 friction log 裡的實錄。

## 保護清單自己在保護清單裡

否則 agent 可以先改清單再刪東西。與「豁免來源不可自我服務」同一個遞迴,
終點一樣是人的審查:要改清單,人自己開編輯器改。
"""

import io
import json
import os
import posixpath
import re
import sys

# **從使用者家目錄解析,不從 `__file__` 推導。**
# 從檔案位置推導的話,專案內的草稿會去找專案裡的清單、正式檔會去找家目錄裡的,
# 兩者指向不同的資源 —— 於是草稿的驗收測到的是「清單讀不到」而不是比對邏輯,
# 而它會全部 fail-closed 通過,看起來像綠燈。G1 依設計是使用者層的,
# 家目錄才是它的定位點(ADR 0009)。
HOME = os.path.join(os.path.expanduser("~"), ".claude")
PROTECTED_LIST = os.path.join(HOME, "g1-protected.txt")

# 第二級的破壞性動詞。這是黑名單,列不完 —— 所以它只是第二級。
# 真正的保證在第一級,那一級不靠列舉。
DESTRUCTIVE = re.compile(
    r"(?:^|[\s;&|(`])"
    r"(rm|rmdir|rd|del|erase|unlink|shred|srm|truncate|dd|mkfs|format"
    r"|Remove-Item|ri|Clear-Content|Clear-Item|Move-Item|mv"
    r"|rsync\s+[^|;]*--delete)"
    r"(?:[\s]|$)", re.IGNORECASE)

# 只認絕對路徑。相對路徑一律視為專案內 —— 第二級刻意寬鬆,
# 「可能是外面的」不算證據,不然又回到每天擋幾十次。
#
# 前面那個 (?<![\w.\-/]) 是必要的,不是防禦性寫法:少了它,
# `rm .cache/x.json` 裡的 `/x.json` 會被當成絕對路徑,於是**每天擋你幾十次**
# 專案內的正常刪除。第一次驗收就抓到這個誤擋。
# 第二級誤擋的代價不是不方便,是整個 hook 會被關掉,而關掉的涵蓋率是零。
ABS_PATH = re.compile(
    r"(?<![\w.\-/])"
    r"(?:[A-Za-z]:[\\/][^\s'\"<>|;]*"     # C:\x 或 C:/x
    r"|/[a-zA-Z]/[^\s'\"<>|;]*"           # /c/x(git bash 形態)
    # **擷取要吃完整個 token,邊界屬於豁免判定,不屬於擷取。**
    # 曾經在這裡加 `(?![\w.\-])` 想收邊界,結果是**砍長度**:
    # `/etc-backup/x` 整條不再被擷取 -> 第二級看不見 -> 從「擋下」變「放行」。
    # 回歸集當場抓到六條(帶 `-`、帶 `.`、暫存區鄰居)。
    # 舊的 `(?:/…)?` 也不對:它把 `/tmpdata/x` 截成 `/tmp`,而 `/tmp` 在豁免裡。
    # 正解是擷取到 token 邊界為止,讓 `_is_scratch` 拿完整路徑去判。
    # `cygdrive` 是票 80 裁 A 補的第三側(2026-08-25)。**這張白名單不由
    # `_POSIX_DRIVE_MOUNTS` 生成 —— 那是刻意的,不是遺漏。** 生成要改的是
    # 這條正則的組裝方式,而這條正則的失敗方向是**砍長度 → 從擋下變放行**
    # (見上面六行那段回歸紀錄),裁 A 明訂「加一格 ≠ 改通用,本刀不改路線」。
    # 代價是表與本清單要靠人同步,而**人上一次沒同步**(cygdrive 進表之後
    # 這裡沒跟上,直到探針量出 `findall -> []`)。所以同步這件事交給紅燈:
    # `TestCygdriveIsExtractedAndBlocked::test_every_mount_in_the_table_is_extractable`
    # —— 下一個掛載點只要進表,那條就紅。**註解不是機制,紅燈才是。**
    r"|/(?:home|tmp|var|etc|usr|opt|mnt|cygdrive|root)[^\s'\"<>|;]*)")

# 保護項後面允許出現的字元 —— 用來把「前綴」與「剛好開頭相同的別的名字」分開。
# 少了這個邊界,`D:\notes1` 會擋掉 `D:\notes123`,而誤擋累積起來規則會被關掉(F-031)。
_BOUNDARY = set("/\\\"' \t;&|)>,")

# 磁碟形態的 POSIX 掛載點 —— **展開(variants)與收斂(_canon)共用這一張表**。
# 加一個掛載點,**這兩側**同時獲得;兩側同表是增量 review F-a 之後的**構造**,
# 一致性另有雙向耦合測試釘著。
#
# ⚠ **「兩側」是字面意思,不含第三側。** 擷取(`ABS_PATH` 的頂層目錄白名單)
# **不由本表生成**,要另外加一格。本註解的前一版寫「加一個掛載點(如日後
# cygdrive 有實例)兩側同時獲得」,而票 80 立案時**把它讀成了整條路徑都涵蓋** ——
# 於是票面把成本估成「共表加一格,近零成本」,實測是 `ABS_PATH.findall` 回 `[]`,
# 兩處都要加。**寫得準確的註解仍然會被讀成它沒說的那件事**,
# 因為讀的人要的是結論,而「兩側」在當下讀起來就像「兩邊都好了」。
# 現在同步由 `test_every_mount_in_the_table_is_extractable` 釘著。
_POSIX_DRIVE_MOUNTS = ("mnt", "cygdrive")

# MSYS(`/c/…`)與掛載形態(`/mnt/c/…`)的磁碟形態。單一字母 + 邊界才算 ——
# `/mnt/data` 是真的 mnt 路徑,不是磁碟。
_DRIVE_FORM = re.compile(r"^/(?:(?:%s)/)?([a-z])(?=/|$)"
                         % "|".join(re.escape(m) for m in _POSIX_DRIVE_MOUNTS))


def _canon(p):
    """第二級**包含性判定**用的正規化:斜線、小寫,加上把 MSYS `/c/…` 與
    WSL `/mnt/c/…` 轉成 `c:/…`。**proj 與擷取路徑兩側都必須過同一個函式。**

    修的是 framework-updates/79 缺陷①:`ABS_PATH` 擷取得到 `/c/…`
    (它的註解自己寫「git bash 形態」),而舊比對只正規化反斜線 ——
    `/c/users/…` 永遠比不上 `c:/users/…`,**擷取得到卻比不上,判專案外而擋**。
    session 內每條 Bash 指令都以 `cd /c/…` 開頭,等於全面誤擋(量化 2026-08-25)。

    同一份「一個路徑會被寫成哪些樣子」的知識:認定住 `_DRIVE_FORM`(由
    `_POSIX_DRIVE_MOUNTS` 生成),展開側 `variants()` **先過本函式收斂、
    再從同一張表展開** —— 這才是構造共用(增量 review F-a/F-b 之後)。
    本 docstring 第一版宣稱「認定收在一處」而 `variants()` 其實自帶正則,
    code-review 照出那是願望不是構造;第二版改成「靠測試釘」,增量 review
    再照出那條測試只釘單向。現在:構造共表 + **雙向**耦合測試
    (`TestVariantsAndCanonCoverTheSameForms`)並存。

    **先解 `..` 再比對**(framework-updates/88 那一刀補,`F-051`):
    少了這一步,`<專案>/../../<目標>` 收斂後仍以 `<專案>/` 開頭 ——
    第二級的專案目錄豁免收下它,**而它實際碰到的是專案外**。
    這不是新機制:同一支檔案的 `_is_scratch()` 早就這樣做,
    它的 docstring 逐字寫著「先解 `..` 再比對」。
    **同檔、隔四十行、只解了一個**(2026-08-31 由 framework-updates/82 的
    `F-051` 半徑掃描掃出)。

    **展開前導 `~`**(framework-updates/88 本題):`~/.claude/x` 與
    `C:/Users/<你>/.claude/x` 是同一個地方的兩種寫法,而第一級**不解析指令**
    —— 所以認定側要認得它,展開側(`variants()`)要產出它。**兩側同一份知識。**
    """
    p = os.path.expanduser(p) if p[:1] == "~" else p
    p = p.replace("\\", "/").rstrip("/").lower()
    if p:
        p = posixpath.normpath(p)
    m = _DRIVE_FORM.match(p)
    if m:
        p = m.group(1) + ":" + p[m.end():]
    return p


def _quote_spans(text):
    """單/雙引號區間的 [(start, end)] 清單;**掃描失敗(未閉合)回 None**。

    修的是 framework-updates/79 缺陷②:動詞與路徑各自全文搜尋、無引號約束,
    `git commit -m "上次 rm -rf /home/x 被擋"` 的**散文**自己配對成擋 ——
    G1 擋住了「描述 G1 擋了什麼」,而 friction log 正是寫閘門行為的文件。

    語意照 shell:雙引號內 `\\` 跳脫下一個字元;單引號內無跳脫。
    這是一個刻意極小的 lexer,**只用來收窄動詞面**(見 level2_hit):
    誤差方向必須是「該放的沒放」= 維持誤擋(看得見、會被抱怨)。
    回 None 時呼叫端把整條當成沒有引號 —— 往擋的方向倒,
    與 `_is_scratch` 契約違約的方向同一條。

    **含 `$(` 或成對反引號的雙引號區間不算散文**(code-review F1)。
    bash 與 PowerShell 的雙引號都替換 `$()` —— `"$(rm -rf …)"` 是
    **會執行的真操作**,本函式第一版把它當散文放行,是 fail-open 回歸。
    反引號**要求成對**(增量 review F-c):bash 的反引號替換必然成對,
    而 PS 雙引號裡的單個反引號是跳脫字元(`` `n ``、`` `t ``)不替換 ——
    第一版見一個反引號就取消散文身分,PS 散文寫個 `` `n `` 就整段誤擋。
    單引號兩種 shell 都不替換,維持散文。
    殘留代價(方向都往擋倒):散文裡寫 `$(`、或 PS 散文帶**兩個以上**
    跳脫反引號,維持誤擋。
    """
    spans = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch not in "'\"":
            i += 1
            continue
        j = i + 1
        closed = False
        while j < n:
            if ch == '"' and text[j] == "\\":
                j += 2
                continue
            if text[j] == ch:
                closed = True
                break
            j += 1
        if not closed:
            return None              # 未閉合 —— 掃描失敗,呼叫端退回現行為
        body = text[i + 1:j]
        if not (ch == '"' and ("$(" in body or body.count("`") >= 2)):
            spans.append((i, j + 1))
        i = j + 1
    return spans


def variants(path):
    """一個 Windows 路徑會被寫成的各種樣子,全部要比對得到。

    `D:\\data` / `D:/data` / `d:\\data` / `/d/data`(git bash)
    —— 只比對其中一種等於留下三個洞。
    """
    p = path.strip().rstrip("\\/")
    if not p:
        return []
    # **先收斂再展開**(增量 review F-b):條目本身寫成 `/mnt/d/…` 或 `/d/…`
    # 也要得到全形態涵蓋 —— 修前那種條目只展開出自己,`del D:\…` 與
    # `/d/…` 都穿過無豁免的第一級(「遮一半比完全沒遮更容易過關」)。
    # 收斂用的就是第二級那顆 `_canon` —— 磁碟形態的知識只住 `_DRIVE_FORM` 一處。
    c = _canon(p)
    out = {c, c.replace("/", "\\")}
    m = re.match(r"^([a-z]):/(.*)$", c)
    if m:
        drive, rest = m.group(1), m.group(2)
        # 展開面從共用表推導(WSL 形態是 framework-updates/79 code-review F2 補的)。
        # 全小寫即可:level1_hit 比對前把兩邊都折小寫,upper 形態是
        # 熱迴圈裡的重複白掃(增量 review F-d)。
        out.add("/%s/%s" % (drive, rest))
        for mount in _POSIX_DRIVE_MOUNTS:
            out.add("/%s/%s/%s" % (mount, drive, rest))
    # framework-updates/88:家目錄底下的條目再補 `~/…` 與 `~\\…` 兩種寫法。
    # 展開的責任在**條目這一側**,不是在比對時去解析指令字串 ——
    # 第一級的判定不解析指令(解析會失敗,而失敗的解析就是洞)。
    home = _canon(os.path.expanduser("~"))
    if home and (c == home or c.startswith(home + "/")):
        rest = c[len(home):].lstrip("/")
        out.add(("~/" + rest) if rest else "~")
        out.add(("~\\" + rest.replace("/", "\\")) if rest else "~")
    return [v for v in out if v]


# 磁碟根目錄條目 —— `D:\` / `D:/` / `d:` / `/d/`。**一律拒絕,不是支援。**
#
# 寫一條 `D:\` 看起來是「整顆磁碟都保護」,實際上 variants() 只產出 `['d:']`:
# rstrip("\\/") 把它削成 `D:`,而 git bash 分支的正則要求磁碟代號後面有分隔符。
# 於是**兩個方向同時錯,而且方向相反**:
#   太寬  `d:` 命中該磁碟上的任何路徑 —— 一條進去整顆磁碟全擋
#   又漏  `/d/...`(git bash 形態、本專案 Bash 工具實際用的形態)放行
# 誤擋不會有人抱怨(整顆磁碟本來就少碰),漏擋不會有人發現(沒有訊號)——
# 兩者互相掩護,而 g1_verify 對它給假綠(探針恰好踩中唯一生效的那個變體)。
#
# **為什麼拒絕而不是修好 variants():守衛不得接受一種自己守不住的寫法。**
# 整顆磁碟保護的真實需求已裁決不採(憑證改用逐檔條目),
# 支援它等於維護一個沒有使用者的語意,而那個語意的每一種寫法都要再驗一次。
_DRIVE_ROOT_RE = re.compile(r"^(?:[A-Za-z]:[\\/]?|/[A-Za-z]/?)$")


def is_drive_root(raw):
    """這一行是不是磁碟根目錄條目。四種寫法都要認得。"""
    return bool(_DRIVE_ROOT_RE.match((raw or "").strip()))


def protected_entries():
    """讀保護清單。回傳 **(entries, reason)**;失敗時 entries 為 None。

    **fail-closed**:讀不到、或有不支援的條目,呼叫端一律擋。
    讀不到時放行的話,刪掉清單就等於關掉整個防護 —— 那是最廉價的繞法。

    **理由跟著失敗一起回傳,不在這裡印**(票 25 收尾)。
    原本的寫法是「這裡印specific 訊息、回 None,呼叫端再印一句通用的」,
    實測(live 探針)的結果是兩段訊息同時出現,而第二段
    **「讀不到保護清單」是假的** —— 清單讀得到、解析得動,只是某一行不被接受。
    人會照那句去查權限與編碼,而答案在第一段。

    與票 26 的 `--no-verify`「會留下紀錄」、票 13 的「請改用 Write / Edit」同一族:
    **訊息描述了一個不成立的狀況**,而人會照著它去做。
    修法不是「少印一句」,是讓**知道原因的地方**負責把原因說出來 ——
    一個失敗,一段訊息,說出真正沒滿足的那個前提(票 13)。
    """
    try:
        out = []
        # framework-updates/92:**`utf-8-sig`,不是 `utf-8`。** 同族的另外三個
        # 使用者層讀取端(`read_shadow_clamp` / `_read_patterns` / `read_upstream_root`)
        # 早就這樣做,理由逐字是「fail-closed 系統的故障是隱形的,輸入端的坑要在
        # 進門前排掉」。沒跟上的是 G1 自己,而它讀的正是保護清單:BOM 黏在第一行
        # 就讓**第一條路徑靜默失去保護** —— 清單上有那一行、行數正確、
        # `g1_verify` 照樣全綠。`g1-protected.txt` 是新機器上第一次建檔的四份之一,
        # 而 PowerShell 最自然的兩種寫法都寫 BOM(`F-146` 實測)。
        for n, line in enumerate(io.open(PROTECTED_LIST, encoding="utf-8-sig"), 1):
            raw = line.split("#", 1)[0].strip()
            if not raw:
                continue
            if is_drive_root(raw):
                return None, (
                    "[G1/fail-closed] 保護清單第 %d 行是磁碟根目錄條目:%s\n"
                    "     這種寫法**守不住**:它只產出一個變體,\n"
                    "     git bash 形態(/x/...)會直接放行,而整顆磁碟會被誤擋 ——\n"
                    "     看起來保護最多,實際上有洞。守衛不接受自己守不住的寫法。\n"
                    "     改法:把要保護的東西逐條列出來(目錄或檔案都可以)。\n"
                    "     清單:%s\n" % (n, raw, PROTECTED_LIST))
            out.append(raw)
        if not out:
            return None, (
                "[G1/fail-closed] 保護清單 %s 沒有任何有效條目 —— 一律擋下。\n"
                "     空清單與沒有清單一樣危險:防護的涵蓋範圍是零,而它不會出聲。\n"
                % PROTECTED_LIST)
        return out, None
    except Exception as e:
        return None, (
            "[G1/fail-closed] 讀不到保護清單 %s(%s)—— 一律擋下。\n"
            "     讀不到就放行的話,刪掉清單就等於關掉整個防護。\n"
            % (PROTECTED_LIST, e))


def _prefix_in(haystack, needle):
    """needle 是否以**路徑前綴**的形式出現在 haystack 裡。

    前綴比對而不是子字串比對:
      `D:/保管庫`  命中 `D:/保管庫`、`D:/保管庫/2023/x.jpg`   ← 子目錄自動涵蓋
      `D:/notes1` **不**命中 `D:/notes123/x`             ← 相鄰名稱不誤中

    命中條件:needle 之後是路徑分隔符、引號、空白、指令分隔符,或字串結尾;
    且 needle 之前不是識別字元(避免 `xD:/保管庫` 這種黏在一起的誤中)。
    """
    start = 0
    n = len(needle)
    while True:
        i = haystack.find(needle, start)
        if i < 0:
            return False
        before_ok = i == 0 or not (haystack[i - 1].isalnum() or haystack[i - 1] == "_")
        j = i + n
        after_ok = j >= len(haystack) or haystack[j] in _BOUNDARY
        if before_ok and after_ok:
            return True
        start = i + 1


def level1_hit(text, entries):
    """保護路徑出現在指令字串裡 —— 回傳觸發的那一條,沒有回 None。"""
    low = text.replace("\\", "/").lower()
    low_bs = text.lower()
    for entry in entries:
        for v in variants(entry):
            if _prefix_in(low, v) or _prefix_in(low_bs, v):
                return entry
    return None


def level2_hit(text, project_dir):
    """破壞性動詞 + 專案外的絕對路徑。回傳 (動詞, 路徑) 或 None。

    ## 守備範圍宣告(framework-updates/79;綠燈要說得出驗的是哪一面。
    三態不二態 —— 已實測涵蓋 / 已實測未涵蓋(分方向)/ 未取樣;
    窮盡與否不再是一個要宣稱的東西)

    - **動詞**:引號區間內的不算(散文,見 `_quote_spans`);
      引號掃描失敗 → 全文都算(往擋倒)。
    - **路徑**:**引號內外都算** —— `rm -rf "/home/x"` 是真操作,
      收窄的只有動詞面,路徑面一寸不縮。包含性判定兩側都過 `_canon()`。

    ### 已實測涵蓋(2026-08-25:本輪 16 案探針 + 量化 live probe 對帳)

    MSYS 路徑、WSL 路徑、引號散文、PowerShell 磁碟形態
    (`Remove-Item D:\\x -Recurse` → 擋)、PS 停止解析符(`--%` 之後的
    刪令 → 擋)。後兩格更正自量化 8/25 對帳 —— 該份誤列為未涵蓋,
    以 live probe 實測為準。

    **cygdrive(`/cygdrive/d/x`)自 2026-08-25 起在此格**(票 80 裁 A 落地)。
    補的是**兩處**:`_POSIX_DRIVE_MOUNTS` 加一格(收斂/展開兩側自動獲得)
    **與** `ABS_PATH` 的頂層目錄白名單加一格(擷取側,不由該表生成)。
    票面原估「共表加一格,近零成本」,依據是該表旁註解的「兩側同時獲得」——
    **那句話是對的,而它沒說擷取是第三側**;動工前的唯讀探針量到
    `ABS_PATH.findall("rm -rf /cygdrive/d/x") -> []` 才現形。
    兩處的同步現由 `test_every_mount_in_the_table_is_extractable` 釘著。

    ### 已實測未涵蓋 —— 分兩欄標方向:讀的人對誤擋與漏擋的容忍度不同,
    並列在同一張表會誤判嚴重度

    **誤擋方向(看得見、會被抱怨;撞到時的出口與其他誤擋相同:
    人自己開終端機)**

    - **殘留一(裁決登記)**:heredoc 內文的動詞 + 路徑**仍會誤擋** ——
      heredoc 沒有引號可認,而解析 heredoc 邊界就是半套 shell parser,
      比零涵蓋更危險(R7 同一句)。2026-08-25 量化 live probe 實測確認
      仍成立(C 案:heredoc 散文 + 真外部路徑 → 擋)。
    - **殘留二(code-review F4)**:PowerShell 的反斜線是
      路徑字元不是跳脫,散文結尾是 `…\\"` 時 lexer 會誤判未閉合 → 退回
      全文比對 → 維持誤擋。分不同 shell 的語意要知道 tool_name,本層拿不到。
    - **殘留三(code-review F6/F7)**:動詞與路徑的配對仍
      跨引號邊界 —— 未引號的良性動詞(`rm old.txt`)可與引號散文裡的
      外部路徑配對成擋,且訊息報的是散文那個路徑。收窄路徑面會違反
      裁決條件 b(引號路徑照算),留待有實例再裁。

    **漏擋方向(不出聲、真操作穿過 —— 比誤擋重)**

    - bash 寫法的 UNC(`//server/share/x`):`ABS_PATH` 擷取不到 =
      不在本判定的視野裡,2026-08-25 量化 live probe 實測放行。
      **票 80 裁 A 明訂不動**:`//` 與 `https://` 的 `//` 撞形是設計題,
      而設計題不該卡住同票裡一個近零成本的洞。**仍 open。**
      F-050 的「等實際誤擋實例」門檻不適用 —— 那條講的是誤擋面;
      漏擋不產生抱怨,等不到實例。票:framework-updates/80。

    ### 未取樣(無樣本,不做宣稱)

    PowerShell 寫法的 UNC(`\\\\server\\share`)、路徑含空白且未引號、
    tool_name 為 PowerShell 時的反斜線散文(殘留二那格的 PS 實測側)。
    """
    if not DESTRUCTIVE.search(text):
        return None                  # 常態路徑零成本(code-review F5):
                                     # 沒有動詞就不必掃引號
    spans = _quote_spans(text)
    m = None
    for cand in DESTRUCTIVE.finditer(text):
        if spans is not None and any(s <= cand.start(1) < e for s, e in spans):
            continue                 # 動詞在引號裡 —— 是散文,不是指令
        m = cand
        break
    if not m:
        return None
    proj = _canon(project_dir or "")
    for raw in ABS_PATH.findall(text):
        p = _canon(raw)
        if proj and (p == proj or p.startswith(proj + "/")):
            continue
        if _is_scratch(p):
            continue
        return m.group(1), raw
    return None


# 系統暫存區 —— 在這裡刪東西是日常,不是災難。
# 試營運誤擋 #1:agent 的工作階段暫存目錄在專案外,於是每一次
# `rm -rf <scratchpad>/x` 都被第二級擋下。POSIX 的 /tmp 本來就豁免了,
# Windows 的對應物沒有 —— 那不是判準不同,是清單沒補齊。
#
# **每一筆都必須來自一次實際觀察到的誤擋**(F-050)。憑推測加進來再補測試,
# 等於把猜測認證成事實 —— 曾經加過 `/windows/temp/`,沒有任何誤擋當證據,已移除。
_SCRATCH_PREFIXES = ("/tmp", "/var/tmp", "/dev/null", "/proc")
_SCRATCH_MARKERS = ("/appdata/local/temp",)


def _is_scratch(lowered_path):
    """這個路徑是不是系統暫存區。傳入的必須是已轉小寫、斜線正規化的路徑。

    **契約違約時往安全方向倒**:比對不到 → 回 False → 第二級命中 → 擋下。
    表現成誤擋,看得見、會被抱怨、會被修 —— 不是靜默放行。

    用**路徑片段**比對 Windows 的暫存區:那個路徑帶使用者名稱
    (`C:/Users/<誰>/AppData/Local/Temp/...`),寫死完整前綴就綁死一台機器,
    而 G1 是要跟著人走的使用者層防護。

    **先解 `..` 再比對。** 少了這一步,
    `C:/…/AppData/Local/Temp/../../../../<目標>` 會命中片段 → 豁免 → 放行,
    而它實際碰到的是完全不同的地方。這與「許可前綴不能替後面那段背書」
    是同一條判準(F-051):**任何用子字串或前綴放行的地方都適用。**

    **前綴要帶邊界。** `startswith("/tmp")` 會命中 `/tmpdata`、`/tmp_backup` ——
    與 `.gitignore` 的 `skills/` 缺前導斜線同一族。
    """
    p = posixpath.normpath(lowered_path)
    if any(p == pre or p.startswith(pre + "/") for pre in _SCRATCH_PREFIXES):
        return True
    # 尾端補一個 `/`,讓「片段剛好在結尾」與「片段在中間」用同一個式子判,
    # 而且片段兩側都帶分隔符 —— `/appdata/local/temp` 不會命中 `/appdata/local/temporary`。
    padded = p + "/"
    return any((mark + "/") in padded for mark in _SCRATCH_MARKERS)


def payload_text(payload):
    """從 PreToolUse payload 取出要檢查的字串。

    Bash / PowerShell 看指令;Write / Edit 看目標路徑。
    **兩者都要**:只掛 Bash 的話,Write 直接覆寫保護目錄裡的檔案不會有人擋。
    """
    ti = payload.get("tool_input") or {}
    parts = [ti.get("command"), ti.get("file_path"), ti.get("notebook_path"),
             ti.get("path")]
    return "\n".join(p for p in parts if isinstance(p, str) and p)


def _err(msg):
    try:
        sys.stderr.buffer.write(msg.encode("utf-8"))
        sys.stderr.buffer.flush()
    except Exception:
        sys.stderr.write(msg)


def main():
    # **以位元組讀取,明確用 utf-8 解碼。**
    # `sys.stdin.read()` 在 Windows 上會用主控台編碼(cp950)去解,payload 裡的
    # 中文路徑與反斜線會被解成別的東西,json 隨即報 Invalid \escape ——
    # 而原本的 `except: return 0` 把那個失敗吞掉,變成靜默 fail-open。
    data = sys.stdin.buffer.read()
    try:
        payload = json.loads(data.decode("utf-8"))
    except Exception as e:
        # **fail-closed**:讀不懂輸入不代表沒事。原本這裡 return 0,
        # 於是任何 payload 形狀的變化都會靜默關掉整個防護。
        _err("[G1/fail-closed] 讀不懂 PreToolUse 輸入(%s)—— 一律擋下。\n" % e)
        return 2
    text = payload_text(payload)
    if not text.strip():
        return 0

    entries, reason = protected_entries()
    if entries is None:
        _err(reason)                     # 一個失敗,一段訊息(票 25 收尾)
        return 2

    hit = level1_hit(text, entries)
    if hit:
        _err(
            "[G1/保護清單] 這個指令碰到受保護的路徑:%s\n"
            "     清單:%s\n"
            "     第一級無豁免,也不分讀寫 —— 判定不解析指令,因為解析會失敗,\n"
            "     而失敗的解析就是洞。要動這個目錄,請自己開終端機做。\n"
            % (hit, PROTECTED_LIST))
        return 2

    l2 = level2_hit(text, os.environ.get("CLAUDE_PROJECT_DIR"))
    if l2:
        verb, path = l2
        _err(
            "[G1/專案外破壞性動作] `%s` 指向專案目錄以外的路徑:%s\n"
            "     專案目錄:%s\n"
            "     這一級只擋破壞性動詞;讀取與一般寫入不受影響。\n"
            "     確定要做的話請自己開終端機 —— 不要改路徑繞過去。\n"
            % (verb, path, os.environ.get("CLAUDE_PROJECT_DIR") or "(未設定)"))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
