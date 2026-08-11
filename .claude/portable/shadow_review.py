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


def load_log(path):
    rows = []
    try:
        for line in io.open(path, encoding="utf-8"):
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    except Exception:
        pass
    return rows


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
    per = promotion_status(path)
    if not per:
        print("還沒有任何已分類的影子日誌。先跑一輪互動分類。")
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
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print()
    print_status(path)


def main(argv):
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    log = os.path.join(root, ".dev", "shadow-log.jsonl")
    if "--status" in argv:
        print_status(log)
    else:
        review(log)


if __name__ == "__main__":
    main(sys.argv[1:])
