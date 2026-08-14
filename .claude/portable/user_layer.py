# -*- coding: utf-8 -*-
"""使用者層(`~/.claude/`)的單向匯出/匯入 —— 票 22 Phase 2。

**主要輸出是「未帶走清單」。** R4 定死了兩個 G1 檔腳本不碰
(人工複製 + sha 核對),所以**匯出在設計上就是不完整的**;
而一個不完整卻看起來完整的匯出,正是這個 repo 一路在打的形狀
(票 27 的靜默缺席、票 26 的假綠、票 25 的假保護)。
所以「沒帶走什麼」不是附註,是報告的主體。

**不用 symlink。** 正本留在 `~/.claude/`,本腳本單向搬。
symlink 會讓 dotfiles repo 的工作樹變成第二條可寫路徑 —— 自助豁免的標準形狀。

## 預設值:刻意沒有

`portable-manifest.txt` 的預設是 `copy`,理由寫在它自己的表頭:
「多帶是吵鬧的(到了新專案馬上發現不對),少帶是靜默的」。

**在這個 payload 上那個不對稱是反過來的:**

    多帶 -> 把憑證推上雲端,**靜默而且不可逆**
    少帶 -> 換機器當場發現少東西,吵鬧

**同一個預設值,搬到相反的不對稱上就變成缺陷。** 這是本檔對重用的具名原則:
重用時要問的不只是「這段程式碼做的事對不對」,還有
**「它的預設是為哪一種代價結構挑的」**。

票 15 已經把預設從查詢裡拿掉(`explicit_mark` 未命中回 None,
「要不要有預設,由各呼叫端明確選」),所以這裡只要選「沒有預設」,
不必改任何既有碼,分岔的可能性為零。
"""

import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import manifest                                              # noqa: E402
import sync                                                  # noqa: E402

Refused = sync.Refused          # 拒絕是一種型別,不是回傳值(重用 sync 的定義)
file_hash = sync.file_hash      # sha 定義只有一份 —— 人工核對要算得出同一個值

EXPORT, AGE, HUMAN, NEVER = "export", "age", "human", "never"
BUCKETS = (EXPORT, AGE, HUMAN, NEVER)

# **這一組不看分類表。** 表是可寫的檔案,而這些東西一旦外洩就收不回來 ——
# 「改一行表」不得構成一條完整的外洩路徑(那是自助豁免的形狀)。
# 與 G1 把保護清單列進保護清單同一個遞迴:**豁免來源不可自我服務。**
NEVER_ALWAYS = (".credentials.json", ".claude.json")
NEVER_ALWAYS_PREFIX = ("backups/",)


BUCKET_REASONS = {
    EXPORT: "腳本帶走",
    AGE: "加密後才帶走(裸的祕密永遠不上雲端、不進 repo)",
    HUMAN: "腳本不碰,人工複製 + sha 核對(R4)",
    NEVER: "永不匯出 —— **不走這條門,不等於不備份**",
}


def load_marks(path):
    """讀分類表。**共用 `manifest.load_table` 的解析器,只換詞彙。**

    複製一份 parser 出去會違反那支函式自己寫下的理由
    (「同一件事只留一個實作,連『格式錯誤要吵』這件事也一起繼承」)。
    換掉的只有標記詞彙,**「打錯字照樣吵」那條原封不動繼承**。
    """
    return manifest.load_table(path, allowed=BUCKET_REASONS)


def _forced_never(rel):
    r = rel.replace("\\", "/")
    return (os.path.basename(r) in NEVER_ALWAYS
            or any(r.startswith(p) for p in NEVER_ALWAYS_PREFIX))


class ExportPlan(object):
    """算出來的匯出計畫。**先算後寫** —— dry-run 是預設(形狀取自 `sync.update`)。"""

    def __init__(self):
        self.take = []           # [(rel, mark)]
        self.left_behind = []    # [(rel, mark, 為什麼沒帶走)]

    @property
    def age_items(self):
        return [rel for rel, mark in self.take if mark == AGE]


LEFT_REASON = {
    HUMAN: "R4:腳本不碰,由人工複製 + sha 核對(見 machine-init.md)",
    NEVER: "不走這條門 —— **不等於不備份**,見分類表的交叉引用",
}


def _walk(home):
    """走訪 `~/.claude/`,回傳相對路徑。**只看路徑,不開任何檔案。**

    這一點是硬需求不是最佳化:`human` 桶的兩個檔在真機器上受 G1 保護,
    讀它們會被第一級擋下 —— 腳本必須**本來就不去讀**,
    而不是讀了以後決定不用。
    """
    out = []
    for dirpath, dirnames, filenames in os.walk(home):
        dirnames.sort()
        for fn in sorted(filenames):
            full = os.path.join(dirpath, fn)
            out.append(os.path.relpath(full, home).replace("\\", "/"))
    return out


def plan_export(home, marks):
    """算出計畫。**不開任何檔案、不寫任何東西。**

    未分類 -> `Refused`,並點名是哪一項(票 15:未分類不得當成照抄;
    這裡連「當成跳過」也不行 —— 跳過是靜默的,而靜默是這個 payload 最貴的失敗)。
    """
    plan = ExportPlan()
    unclassified = []
    for rel in _walk(home):
        mark = manifest.explicit_mark(rel, marks)   # **沒有預設的查詢**
        if _forced_never(rel):
            if mark in (EXPORT, AGE):
                raise Refused(
                    "分類表把 %s 標成 %s,但它在**不看表的 never 清單**裡。\n"
                    "     表是可寫的檔案,而這種東西外洩就收不回來 ——\n"
                    "     『改一行表』不得構成一條完整的外洩路徑。" % (rel, mark))
            plan.left_behind.append((rel, NEVER, LEFT_REASON[NEVER]))
            continue
        if mark is None:
            unclassified.append(rel)
            continue
        if mark not in BUCKETS:
            raise Refused("%s 的標記 %r 不是四個桶之一。" % (rel, mark))
        if mark in (HUMAN, NEVER):
            plan.left_behind.append((rel, mark, LEFT_REASON[mark]))
        else:
            plan.take.append((rel, mark))
    if unclassified:
        raise Refused(
            "這些項目沒有分類,拒絕整次匯出:%s\n"
            "     未分類不得當成照抄,也不得當成跳過 —— 跳過是靜默的。\n"
            "     處置:在分類表裡給它一個桶(%s)。"
            % (", ".join(sorted(unclassified)), "/".join(BUCKETS)))
    return plan


def report(plan):
    """匯出報告。**「未帶走」那一段是主體,不是附註。**"""
    lines = ["=== 帶走(%d 項)===" % len(plan.take)]
    for rel, mark in plan.take:
        lines.append("    %-34s %s" % (rel, mark))
    lines.append("")
    lines.append("=== **未帶走**(%d 項)—— 這一段才是重點 ==="
                 % len(plan.left_behind))
    lines.append("    匯出依設計就是不完整的:R4 把兩個 G1 檔留給人工。")
    lines.append("    **檔案都到位 ≠ 這台機器可以工作**(machine-init.md 第二節)。")
    for rel, mark, why in plan.left_behind:
        lines.append("    %-34s %-6s %s" % (rel, mark, why))
    return "\n".join(lines) + "\n"


def export(home, dest, marks, apply=False, encrypt=None):
    """匯出。**先算後寫**:任何一項不合格就整批拒絕,不會寫出半套。

    `encrypt` 是 age 加密器(吃 bytes 回 bytes)。`age` 桶有東西而它是 None
    -> 拒絕。**裸的祕密永遠不上任何雲端、不進任何 repo。**
    """
    plan = plan_export(home, marks)
    if plan.age_items and encrypt is None:
        raise Refused(
            "這些項目要加密才能帶走,但沒有給加密器:%s\n"
            "     裸的祕密永遠不上任何雲端、不進任何 repo。"
            % ", ".join(plan.age_items))
    if not apply:
        return plan
    for rel, mark in plan.take:
        raw = io.open(os.path.join(home, rel.replace("/", os.sep)), "rb").read()
        if mark == AGE:
            raw = encrypt(raw)
        out = os.path.join(dest, rel.replace("/", os.sep))
        d = os.path.dirname(out)
        if d and not os.path.isdir(d):
            os.makedirs(d)
        io.open(out, "wb").write(raw)
    return plan


class ImportResult(object):
    """匯入結果。**`complete` 與「檔案有沒有寫成功」是兩件事。**"""

    def __init__(self):
        self.written = []
        self.pending = []

    @property
    def complete(self):
        """人工步驟還有待辦 -> **不算完成**。

        `machine-init.md` 第二節開頭那句「複製檔案不算裝好」,這裡用機器實現。
        回 True 的條件是「這台機器可以工作了」,不是「我寫完了我負責的部分」。
        """
        return not self.pending


def import_(src, home, marks, apply=False):
    """把匯出的內容放進新機器的 `~/.claude/`,並列出還差的人工步驟。"""
    result = ImportResult()
    for rel, mark in sorted(_marks_items(marks)):
        if mark == HUMAN:
            target = os.path.join(home, rel.replace("/", os.sep))
            if not os.path.exists(target):
                result.pending.append(
                    "%s —— 人工複製 + sha 核對(R4:腳本不碰)" % rel)
    for rel in _walk(src) if os.path.isdir(src) else []:
        if not apply:
            result.written.append(rel)
            continue
        raw = io.open(os.path.join(src, rel.replace("/", os.sep)), "rb").read()
        out = os.path.join(home, rel.replace("/", os.sep))
        d = os.path.dirname(out)
        if d and not os.path.isdir(d):
            os.makedirs(d)
        io.open(out, "wb").write(raw)
        result.written.append(rel)
    return result


def _marks_items(marks):
    """把標記表攤成 (路徑, 標記)。表的內部形狀由 manifest 決定,這裡只取用。"""
    if isinstance(marks, dict):
        return list(marks.items())
    return list(marks)
