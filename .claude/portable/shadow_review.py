# -*- coding: utf-8 -*-
"""影子日誌逐筆分類 + per-rule 晉升狀態。

用法:
  python .claude/portable/shadow_review.py            互動:逐筆分類未分類的
  python .claude/portable/shadow_review.py --status   只印各規則的晉升狀態

**晉升 per-rule 不全局**:每條規則自己 ≥10 筆已分類 且 假陽率 <5% 才可轉正。
全局比率會讓一條規則的真陽稀釋另一條的假陽 —— 那會把「R2 很準」誤讀成
「R3 也可以開了」。所以逐條算,不足 10 筆的留影子。

**逐筆判,不算總數**:每筆給一個分類,晉升率從分類算。你不能靠「總共擋幾次」
晉升,必須逐筆判真陽/假陽 —— 只有這樣才知道假陽集中在哪條規則、哪一類。

## 讀取一律出聲失敗(票 63)

原本 `load_log` 是 `except Exception: pass` 回 `[]`,於是
**「日誌是空的」與「日誌讀不動」壓成同一個輸出**,而 `print_status`
把後者播報成前者:量化 222 筆的日誌被說成「還沒有任何已分類的」。

觸發它的是 **UTF-8 BOM**:`encoding="utf-8"` 讓第一行變 `﻿{...}`,
`json.loads` 丟例外 —— 而 ADR 0012:37-40 **已經寫過同一個坑**
(「輸入端的坑要在進門前排掉」),只是那段排的是 clamp,隔 11 行就點名本檔。
**同一份判準寫在 A 的註解裡,不會讓 B 變安全。**

所以這裡兩件事一起做,而它們守的東西不同:

    utf-8-sig       讓 BOM 不再是壞行
    ShadowLogError  讓**任何**讀不動都出聲,不只 BOM

第二件才是重點:BOM 是這次的觸發物,**不是這一類故障的全集**。
只改編碼的話,下一種壞法會走同一條靜默路徑回來。
"""

import io
import json
import os
import sys

MIN_CLASSIFIED = 10
MAX_FALSE_POSITIVE_RATE = 0.05

# 五類:一真陽,四種假陽(各對應一種修法)
CLASSES = {
    "1": "真陽",
    "2": "假陽/範圍",     # 路徑判定錯(非原始碼當成原始碼)-> 修非原始碼清單
    "3": "假陽/時點",     # 時點語意錯 -> 修規則
    "4": "假陽/既有",     # 早於閘門的既有碼 -> legacy 清單 / R3 豁免
    "5": "假陽/解析",     # 規則誤解輸入 -> 修規則
}


def _is_false_positive(classification):
    return classification and classification.startswith("假陽")


class ShadowLogError(Exception):
    """影子日誌讀不動或內容壞掉。

    **自己的型別,不是 `Exception`。** 呼叫端要分得出「日誌壞了」與別的錯;
    要求呼叫端寫 `except Exception` 等於把本票在修的那個坑往外挪一層。
    """


def _read_lines(path):
    """逐行讀,**`utf-8-sig` 不是 `utf-8`**。

    `utf-8-sig` 對**沒有** BOM 的檔案行為與 `utf-8` 相同,所以這不是取捨 ——
    它嚴格涵蓋舊行為。有測試釘住沒有 BOM 的情況(`test_a_log_without_a_bom_still_works`),
    否則「修好 BOM」會有機會偷偷換成「只認 BOM」。
    """
    try:
        with io.open(path, encoding="utf-8-sig") as f:
            return f.readlines()
    except IOError as e:
        raise ShadowLogError(
            "讀不到影子日誌:%s\n"
            "     %s\n"
            "     **這不等於「日誌是空的」** —— 一個讀不到的檔案與一個沒有內容的\n"
            "     檔案,對晉升判定是兩件完全不同的事。前者要修,後者要跑分類。"
            % (path, e))


def load_log(path):
    """回傳全部紀錄,或丟 `ShadowLogError`。**不回部分。**

    回部分是最糟的選項,因為 `review()` 會拿回傳值**整份重寫檔案** ——
    壞行在第 50 筆時,靜默回 49 筆會讓後面 173 筆在下一次分類時消失。
    """
    rows = []
    for lineno, line in enumerate(_read_lines(path), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except ValueError as e:
            raise ShadowLogError(
                "影子日誌第 %d 行不是合法 JSON:%s\n"
                "     檔案:%s\n"
                "     **不跳過這一行,也不回傳前 %d 筆** —— `review()` 會拿\n"
                "     回傳值整份重寫檔案,回部分等於靜默刪掉後面每一筆。\n"
                "     修法:把那一行修好或刪掉,再跑一次。"
                % (lineno, e, path, len(rows)))
    return rows


def _nonblank_line_count(path):
    """檔案裡有幾行非空白。**筆數守恆那一道的右邊。**"""
    return sum(1 for line in _read_lines(path) if line.strip())


def promotion_status(path):
    """回傳 {rule: {classified, false_positives, fp_rate, promotable}}。

    只算**已分類**的筆數(有 classification 欄)。未分類的不進分母 ——
    否則「還沒判」會被當成分母灌水,永遠達不到門檻或反而虛高。
    """
    rows = load_log(path)
    per = {}
    for r in rows:
        c = r.get("classification")
        if not c:
            continue
        rule = r.get("rule", "?")
        d = per.setdefault(rule, {"classified": 0, "false_positives": 0})
        d["classified"] += 1
        if _is_false_positive(c):
            d["false_positives"] += 1
    for rule, d in per.items():
        n = d["classified"]
        d["fp_rate"] = (d["false_positives"] / n) if n else 0.0
        d["promotable"] = (n >= MIN_CLASSIFIED
                           and d["fp_rate"] < MAX_FALSE_POSITIVE_RATE)
    return per


def print_status(path):
    """**先報讀到幾筆,再報分類情形。**(票 63,同一個病的上一層。)

    `load_log` 那一層分開了「讀不到」與「日誌是空的」;而在這一層,
    「讀到 222 筆但一筆都還沒分類」與「檔案裡什麼都沒有」原本壓成同一句話
    ——「還沒有任何已分類的影子日誌」。修好讀取之後那句話變成**真的**,
    但它仍然**分不出來**,而分不出來就代表**修好與沒修好在輸出上一樣**。

    讀到的筆數是這支工具唯一能證明「我真的看到資料了」的東西,所以它先印。
    """
    rows = load_log(path)
    per = promotion_status(path)
    total = len(rows)
    classified = sum(d["classified"] for d in per.values())
    print("影子日誌:讀到 %d 筆,其中 %d 筆已分類。" % (total, classified))
    if not per:
        if total:
            print("尚無任何分類 —— 跑一輪互動分類(不加 --status)即可開始。")
        else:
            print("日誌本身是空的 —— 影子模式還沒有記錄過任何判定。")
        return
    print("每規則晉升狀態(≥%d 筆已分類 且 假陽率 <%.0f%% 才可轉正):"
          % (MIN_CLASSIFIED, MAX_FALSE_POSITIVE_RATE * 100))
    for rule in sorted(per):
        d = per[rule]
        print("  %-4s 已分類 %3d  假陽 %3d  假陽率 %5.1f%%  -> %s"
              % (rule, d["classified"], d["false_positives"],
                 d["fp_rate"] * 100,
                 "可轉正" if d["promotable"] else "留影子"))


def review(path):
    """逐筆分類未分類的項目,原地更新(重寫整份,把 classification 填進去)。"""
    rows = load_log(path)
    unclassified = [i for i, r in enumerate(rows) if not r.get("classification")]
    if not unclassified:
        print("沒有未分類的項目。")
        print_status(path)
        return
    print("共 %d 筆未分類。分類選項:" % len(unclassified))
    for k, v in CLASSES.items():
        print("  %s = %s" % (k, v))
    print("  s = 跳過(留待下次)  q = 存檔離開\n")
    for i in unclassified:
        r = rows[i]
        print("── %s  [%s]  %s" % (r.get("ts", "")[:19], r.get("rule", "?"),
                                    r.get("message", "")[:90]))
        ans = input("  分類 [1-5/s/q]: ").strip()
        if ans == "q":
            break
        if ans == "s" or ans not in CLASSES:
            continue
        rows[i]["classification"] = CLASSES[ans]

    # ── 筆數守恆(票 63 的第二道)────────────────────────────────────
    # **這一行是整支工具唯一會刪掉資料的地方**,所以釘子釘在它旁邊,
    # 不釘在 `load_log` 裡 —— 位置就是它的理由。
    #
    # 修好之後 `load_log` 要嘛回全部、要嘛丟例外,所以這道檢查在**當下**
    # 走不到。留著是因為那個等價是**目前實作**的性質,不是這條路徑的性質:
    # 下一個人若為了別的理由讓 `load_log` 再度容忍部分失敗,
    # 第一道會消失,而下面那行 `open(path, "w")` 不會知道。
    #
    # 有負控釘住它(`test_review_refuses_to_rewrite_when_records_went_missing`
    # 把 `load_log` 換成回截斷清單),否則這是一個從未被走到的 fail-closed 分支 ——
    # 那種分支會在它前面那個分支被拿掉的當天才現形(票 42)。
    on_disk = _nonblank_line_count(path)
    if len(rows) != on_disk:
        raise ShadowLogError(
            "拒絕重寫影子日誌:手上有 %d 筆,檔案裡有 %d 筆非空白行。\n"
            "     檔案:%s\n"
            "     **少掉的 %d 筆會在重寫時消失,而消失不會有任何訊息。**\n"
            "     缺的前提是**筆數守恆**:重寫是全量覆蓋,所以寫出去的必須\n"
            "     與讀進來的一樣多。對不上代表讀取那一層吞了東西 —— 先修那裡。"
            % (len(rows), on_disk, path, on_disk - len(rows)))

    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print()
    print_status(path)


def main(argv):
    """回退出碼。**讀不動的日誌不得以 0 收場** —— 一個永遠回 0 的工具
    接進任何自動化時等於沒接(同 `ledger_verify` 那道張力,票 61 第 5 題,
    差別在**這裡的非 0 表示「壞了」,不是「需要人看一眼」**)。
    """
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    log = os.path.join(root, ".dev", "shadow-log.jsonl")
    try:
        if "--status" in argv:
            print_status(log)
        else:
            review(log)
    except ShadowLogError as e:
        # **新增的輸出走 buffer,不走 `print`。** 本檔既有的 `print()` 屬票 62
        # (cp950 家族)的範圍,本票不順手改它們;但**新寫的東西不該再製造一個**
        # —— 在 cp950 主控台上,一個用 `print` 印中文的錯誤訊息會自己炸掉,
        # 而那正好發生在使用者最需要讀到它的時候。
        sys.stderr.buffer.write((u"[影子日誌/拒絕] %s\n" % e).encode("utf-8"))
        return 1
    return 0


if __name__ == "__main__":
    # **`sys.exit(main(...))`,不是 `main(...)`。** 舊版丟掉了回傳值,
    # 所以就算 `main` 回 1,行程仍以 0 結束 —— 出聲失敗只做一半:
    # 訊息印出來了,而任何看退出碼的東西照樣當它成功。
    sys.exit(main(sys.argv[1:]))
