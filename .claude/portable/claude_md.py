# -*- coding: utf-8 -*-
"""CLAUDE.md 的框架段 —— 哪一部分該跟著框架走。

**查證後的事實**:目前這份 CLAUDE.md 裡沒有任何專案專屬內容,七個小節全是框架規範。
票 04 原本寫「它同時裝著框架規範與台股專屬規範」是沒查證的前提,不成立。

所以本模組的用途不是今天拆掉什麼,是**建立那道界線**:
將來有人在 CLAUDE.md 裡寫下「台股的收盤時間是 13:30」時,它有一個
**明確不會被帶走**的位置。沒有界線的話那條規矩會靜默裝進別的專案,
而 agent 會照它工作 —— **那不會報錯**,這是汙染方向比乾淨更要緊的原因。

失敗方向與標記表**相反**:標記表往「多帶」倒(多帶是吵鬧的,馬上發現);
這裡往「不帶」倒,因為帶錯的規矩不會報錯,只會讓 agent 照錯的規矩工作。
"""

BEGIN = "<!-- FRAMEWORK:BEGIN -->"
END = "<!-- FRAMEWORK:END -->"

# 佔位文字裡**不得出現標記字串本身** —— 出現的話產生的檔案就有兩組界線,
# 下一次抽取會因「取哪一組取決於實作」而拒絕。這是測試抓到的:round-trip 那條。
PROJECT_PLACEHOLDER = """
## 這個專案自己的規範

(還沒有。寫在這一段裡的東西**不會**被帶進別的專案 ——
框架規範寫在上面那對 FRAMEWORK 界線之間,只有那一段會跟著走。)
"""


def framework_section(text):
    """取出框架段。找不到界線就丟例外,**不退化成整份**。

    退化成「整份都算框架」的話,專案規範會靜默搬家 —— 而那正是這道界線要擋的。
    """
    begins = text.count(BEGIN)
    ends = text.count(END)
    if begins == 0 or ends == 0:
        raise ValueError(
            "CLAUDE.md 找不到框架段界線(%s / %s)。\n"
            "     找不到界線時不會整份帶走 —— 那會把專案規範一起裝進別的專案。"
            % (BEGIN, END))
    if begins > 1 or ends > 1:
        raise ValueError(
            "CLAUDE.md 有 %d 組 BEGIN、%d 組 END —— 取哪一組取決於實作,那是隱形的。"
            % (begins, ends))
    i, j = text.index(BEGIN), text.index(END)
    if j < i:
        raise ValueError("CLAUDE.md 的 END 出現在 BEGIN 之前,界線是壞的。")
    return text[i + len(BEGIN):j]


def render_for_new_repo(text, title="# 專案開發規範"):
    """產生目標 repo 的 CLAUDE.md:框架段 + 一個標明位置的空專案段。

    界線本身也寫進去 —— 否則下一次從這個 repo 再往外裝時就找不到框架段了。
    """
    body = framework_section(text)
    return "%s\n\n%s%s%s\n%s" % (title, BEGIN, body, END, PROJECT_PLACEHOLDER)
