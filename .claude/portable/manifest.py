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
    """讀本 repo 的標記表。"""
    return load_table(MANIFEST)


def load_table(path, allowed=None):
    """讀**指定位置**的標記表。回傳 {相對路徑: 標記}。

    要能指定位置,是因為更新路徑(sync)讀的是**來源 repo** 的那一份,
    不是自己這一份。原本 sync 有一份自己的解析與優先序 —— 兩份實作會漂移,
    而漂移的那天不會有人發現:一個把檔案搬過去,一個以為沒搬(F-058)。
    同一件事只留一個實作,連「格式錯誤要吵」這件事也一起繼承。

    `allowed` 讓**別的標記詞彙**共用這個解析器(票 22:使用者層的四個桶是
    `export`/`age`/`human`/`never`)。預設 `None` = 用框架自己的 `MARKS`,
    既有呼叫端行為完全不變。
    **參數化的是詞彙,不是「要不要驗」** —— 打錯字照樣吵,那條不可協商。
    複製一份 parser 出去會違反上一段自己寫的理由。

    檔案不存在 -> 空表 -> 全部視為未標記。
    **未標記之後怎麼辦由呼叫端決定**:框架這邊是 copy 且全部被列出來
    (少帶才是危險的那一邊);使用者層那邊是拒絕(多帶才是危險的那一邊)。
    """
    vocab = MARKS if allowed is None else allowed
    out = {}
    if not os.path.exists(path):
        return out
    # 訊息指的是**這一次讀的那份表**,不是本 repo 的那份 —— 讀來源 repo 的表
    # 卻報自己的檔名,會把人指去改一個沒問題的檔案。
    where = rel(path)
    for lineno, raw in enumerate(io.open(path, encoding="utf-8-sig"), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        # 由右邊切:路徑可以含空白,標記永遠是最後一個詞
        parts = line.rsplit(None, 1)
        if len(parts) != 2:
            raise ValueError(
                "%s:%d 這一行沒有標記:%r\n"
                "     格式是「路徑<空白>標記」,標記為 %s 之一。"
                % (where, lineno, line, "/".join(sorted(vocab))))
        entry, mark = parts[0].strip().replace("\\", "/"), parts[1]
        if mark not in vocab:
            # 打錯字不得退化成預設。把一個該 generate 的檔案照抄進新專案
            # 看起來一切正常,實際上 R6 會拿別的 repo 的路徑去驗 —— 正是靜默壞掉。
            raise ValueError(
                "%s:%d 不認得的標記 %r(路徑 %s)。\n"
                "     只能是 %s。打錯字不會被當成未標記 —— 那會靜默退化成 copy。"
                % (where, lineno, mark, entry, "/".join(sorted(vocab))))
        if entry in out:
            # 同一路徑標兩次,行為就取決於讀取順序,而那是隱形的
            raise ValueError(
                "%s:%d 重複標記:%s 已經標過 %r。\n"
                "     同一路徑標兩次的話,結果取決於讀取順序 —— 那是隱形的,先刪掉一筆。"
                % (where, lineno, entry, out[entry]))
        out[entry] = mark
    return out


def explicit_mark(rel_path, table):
    """**沒有預設的查詢**:回傳標記,未命中任何前綴回 `None`。

    `mark_for` / `mark_in` 帶著 `DEFAULT_MARK`,那是**安裝器的**語意,
    而它在安裝器安全是因為有兩道護欄:`in_scope()` 先濾掉範圍外的檔案,
    未涵蓋的鄰居會被列出來讓人確認。

    更新路徑(`sync`)兩道都沒有,而它的寫入對象是**別人 repo 裡已經存在的
    檔案** —— 同一個預設在那裡的意思是「覆蓋」。實際後果(影音第三輪 dry-run):
    目標的 `.githooks/pre-commit` 會從**兩段都接**降成只剩 leak_scan,
    **權威層靜默消失**,而整個過程看起來像一次成功的更新。
    (本句原寫「三層掛載」—— 那個 hook 只有兩個階段,票 51:⑥ 更正。
    `.githooks/pre-commit:11-12` 逐字引用本句,兩處同一次改完。)

    所以預設不再藏在查詢裡:查詢只回答「有沒有標記、標的是什麼」,
    **要不要有預設,由各呼叫端明確選**(票 15)。
    """
    return _best_entry(rel_path, table)[1]


def mark_in(rel_path, table):
    """在**給定的表**裡查標記,未命中回 `DEFAULT_MARK`。

    帶預設的那一支 —— 安裝器用。更新路徑用 `explicit_mark`。
    """
    return explicit_mark(rel_path, table) or DEFAULT_MARK


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
