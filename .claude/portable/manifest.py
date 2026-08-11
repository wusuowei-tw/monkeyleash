# -*- coding: utf-8 -*-
"""標記表 —— 哪些檔案是框架的,搬過去該怎麼處理。

目錄判定做不到:`.agents/` 底下同時有通用的(站別定義)與這個 repo 專屬的
(豁免清單、它的 go-live sha)。所以逐檔標記。

**代價不對稱,整份檔案的每個判斷都往同一邊倒:**
多帶一個檔案是**吵鬧的** —— 到了新專案馬上發現不對;
少帶一個是**靜默的** —— 沒人知道少了一條規則。
因此不確定時一律「帶」,但要**出聲**讓人確認。沒標記不等於不帶 —— 那又是白名單。

放在 `.claude/portable/` 而不是 `scripts/`:後者在非原始碼清單裡,
把判定邏輯放進去等於讓安裝器自己繞過閘門(CLAUDE.md 的常駐檢查項)。
"""

import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MANIFEST = os.path.join(ROOT, ".agents", "portable-manifest.txt")

# 三種標記。每一個都要寫理由 —— 清單一長判準就會漂移,理由欄是讓漂移看得見的東西。
MARKS = {
    "copy": "框架的一部分,內容與專案無關,照抄",
    "generate": "內容綁這個 repo(sha、路徑清單),必須在目標 repo 重新產生,照抄會靜默壞掉",
    "ask": "內容混著框架與專案兩種東西,要人決定帶哪些",
    "skip": "專案自己的東西,只是剛好住在框架根目錄底下(例如 tests/ 裡的專案測試)",
}

DEFAULT_MARK = "copy"


def _table():
    """讀標記表。回傳 {相對路徑: 標記}。

    檔案不存在 -> 空表 -> 全部視為未標記 -> 全部 copy 且全部被列出來。
    這裡的 fail 方向是**吵鬧**,不是「什麼都不帶」:少帶才是危險的那一邊。
    """
    out = {}
    if not os.path.exists(MANIFEST):
        return out
    for lineno, raw in enumerate(io.open(MANIFEST, encoding="utf-8"), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        # 由右邊切:路徑可以含空白,標記永遠是最後一個詞
        parts = line.rsplit(None, 1)
        if len(parts) != 2:
            raise ValueError(
                "%s:%d 這一行沒有標記:%r\n"
                "     格式是「路徑<空白>標記」,標記為 %s 之一。"
                % (rel(MANIFEST), lineno, line, "/".join(sorted(MARKS))))
        path, mark = parts[0].strip().replace("\\", "/"), parts[1]
        if mark not in MARKS:
            # 打錯字不得退化成預設。把一個該 generate 的檔案照抄進新專案
            # 看起來一切正常,實際上 R6 會拿別的 repo 的路徑去驗 —— 正是靜默壞掉。
            raise ValueError(
                "%s:%d 不認得的標記 %r(路徑 %s)。\n"
                "     只能是 %s。打錯字不會被當成未標記 —— 那會靜默退化成 copy。"
                % (rel(MANIFEST), lineno, mark, path, "/".join(sorted(MARKS))))
        if path in out:
            # 同一路徑標兩次,行為就取決於讀取順序,而那是隱形的
            raise ValueError(
                "%s:%d 重複標記:%s 已經標過 %r。\n"
                "     同一路徑標兩次的話,結果取決於讀取順序 —— 那是隱形的,先刪掉一筆。"
                % (rel(MANIFEST), lineno, path, out[path]))
        out[path] = mark
    return out


def rel(path):
    try:
        return os.path.relpath(os.path.abspath(path), ROOT).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _best_entry(rel_path, table):
    """最長前綴者勝。回傳 (前綴, 標記),沒有任何前綴命中回 (None, None)。

    用最長前綴而不是讀取順序:順序決定的話,同一份標記表換個排法就換個行為,
    那是隱形的。以 `/` 結尾的項目是目錄,其餘要完全相等才算命中 ——
    否則 `tests/x.py` 會被 `tests/x` 誤命中。
    """
    r = rel_path.replace("\\", "/")
    best = (None, None)
    for prefix, mark in table.items():
        hit = r == prefix or (prefix.endswith("/") and r.startswith(prefix))
        if hit and (best[0] is None or len(prefix) > len(best[0])):
            best = (prefix, mark)
    return best


def in_scope(rel_path):
    """這個路徑是不是框架的一部分。

    範圍必須用根目錄圈起來:少了這道,「未標記 → copy」會把整個專案的原始碼
    一起搬進新專案。那條預設只在框架範圍**之內**成立。
    """
    return _best_entry(rel_path, _table())[0] is not None


def mark_for(rel_path):
    """這個檔案該怎麼處理。在範圍內但沒有更具體的標記時回 copy。"""
    return _best_entry(rel_path, _table())[1] or DEFAULT_MARK


def uncovered_neighbours(paths):
    """跟框架檔住在同一個目錄、卻沒被任何根目錄涵蓋的檔案 —— 安裝時要出聲。

    範圍改用前綴之後,「在範圍內但沒標記」由構造為空,原本那條確認清單成了廢話。
    真正會漏帶的是這一群:`tests/` 底下同時住著框架的閘門測試與專案自己的測試,
    漏一個框架測試不會有任何人發現(少帶是靜默的)。

    完全無關的目錄不列 —— 那會把整個專案印出來,吵到沒人會讀,等於沒印。
    """
    norm = [p.replace("\\", "/") for p in paths]
    covered_dirs = {os.path.dirname(p) for p in norm if in_scope(p)}
    return [p for p in norm
            if not in_scope(p) and os.path.dirname(p) in covered_dirs]


def unmarked(paths):
    """哪些檔案是靠預設過關的 —— 安裝時要把它們印出來讓人確認。

    套了預設就要出聲。靜默套用等於沒有標記表:少帶的那一天沒有人會知道。
    """
    table = _table()
    return [p for p in paths if p.replace("\\", "/") not in table]
