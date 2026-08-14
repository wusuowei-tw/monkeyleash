# -*- coding: utf-8 -*-
"""G1 —— agent 檔案系統災難防護。使用者層,涵蓋所有專案。

**與 R 系列相反的設計。** R 系列是流程規則:**性質上**各自獨立、可分開裝,
每個專案自己決定要不要。G1 是災難防護:任何專案都該開,
所以住在 ~/.claude/ 而不是某個 repo 裡。

**上面那句是性質描述,不是功能宣告** —— 目前沒有 per-repo 開關,
R1–R7 在裝了閘門的 repo 裡全部無條件生效。

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
    r"|/(?:home|tmp|var|etc|usr|opt|mnt|root)[^\s'\"<>|;]*)")

# 保護項後面允許出現的字元 —— 用來把「前綴」與「剛好開頭相同的別的名字」分開。
# 少了這個邊界,`D:\notes1` 會擋掉 `D:\notes123`,而誤擋累積起來規則會被關掉(F-031)。
_BOUNDARY = set("/\\\"' \t;&|)>,")


def variants(path):
    """一個 Windows 路徑會被寫成的各種樣子,全部要比對得到。

    `D:\\data` / `D:/data` / `d:\\data` / `/d/data`(git bash)
    —— 只比對其中一種等於留下三個洞。
    """
    p = path.strip().rstrip("\\/")
    if not p:
        return []
    out = {p.replace("\\", "/"), p.replace("/", "\\")}
    m = re.match(r"^([A-Za-z]):[\\/](.*)$", p)
    if m:
        drive, rest = m.group(1), m.group(2).replace("\\", "/")
        out.add("/%s/%s" % (drive.lower(), rest))
        out.add("/%s/%s" % (drive.upper(), rest))
    return [v.lower() for v in out if v]


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
        for n, line in enumerate(io.open(PROTECTED_LIST, encoding="utf-8"), 1):
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
    """破壞性動詞 + 專案外的絕對路徑。回傳 (動詞, 路徑) 或 None。"""
    m = DESTRUCTIVE.search(text)
    if not m:
        return None
    proj = (project_dir or "").replace("\\", "/").rstrip("/").lower()
    for raw in ABS_PATH.findall(text):
        p = raw.replace("\\", "/").rstrip("/").lower()
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
