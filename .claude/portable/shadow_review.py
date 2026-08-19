# -*- coding: utf-8 -*-
"""影子日誌逐筆分類 + per-rule 晉升狀態。

用法:
  python .claude/portable/shadow_review.py                     互動:逐筆分類未分類的
  python .claude/portable/shadow_review.py --status            只印各規則的晉升狀態
  python .claude/portable/shadow_review.py --card <卡片>       批次:dry-run,不寫
  python .claude/portable/shadow_review.py --card <卡片> --apply   批次:實際套用

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

import datetime
import hashlib
import io
import json
import os
import sys

MIN_CLASSIFIED = 10
MAX_FALSE_POSITIVE_RATE = 0.05

# 六類:一真陽、四種假陽(各對應一種修法)、一種**刻意成本**。
CLASSES = {
    "1": "真陽",
    "2": "假陽/範圍",     # 路徑判定錯(非原始碼當成原始碼)-> 修非原始碼清單
    "3": "假陽/時點",     # 時點語意錯 -> 修規則
    "4": "假陽/既有",     # 早於閘門的既有碼 -> legacy 清單 / R3 豁免
    "5": "假陽/解析",     # 規則誤解輸入 -> 修規則
    # 票 65:fail-closed 保守觸發 —— **規則照設計動作**(「切不出目標就擋」)。
    # 成本是真的、要算進分母,但它**不是誤判**:把它算成假陽,
    # 等於要求一條 fail-closed 規則證明自己從不 fail-closed(上游票 21 裁決)。
    "6": "刻意 refuse",
    # 票 67:**判定不能,不是判定結果。** 日誌沒有記指令(票 68),
    # 所以有一整群 R7 從紀錄本身判不出真陽/誤報。
    # 它**既不進假陽率的分子,也不進分母** ——
    # 進分母會稀釋假陽率,進分子會誣賴規則。
    "7": "無法判定",
}

# **顯式集合,不是字串前綴。**
#
# 原本是 `classification.startswith("假陽")` —— 分類語意藏在中文字串的
# **前兩個字**裡。任何人把「假陽/範圍」改名成「範圍誤判」,
# 假陽率會**當場歸零而且全綠**。
#
# 分類集合是**封閉且可窮舉**的,而封閉集合**枚舉勝過比對** ——
# 比對的漏是未知的,枚舉的漏是不存在的(CLAUDE.md 常駐檢查項)。
# 加第六類只是觸發物,這個才是缺陷。
FALSE_POSITIVE_CLASSES = frozenset([
    CLASSES["2"], CLASSES["3"], CLASSES["4"], CLASSES["5"],
])

# 三分類(ADR 0012 §2):真實觸發 / 刻意 refuse(不計分子)/ 誤報。
DELIBERATE_CLASS = CLASSES["6"]
TRUE_POSITIVE_CLASS = CLASSES["1"]
UNDECIDABLE_CLASS = CLASSES["7"]                                     # 票 67

# 可判定率門檻(票 67)。**線畫在實測證據的邊界上**,同票 34 的先例:
#
#   畫在哪:2026-08-19 量化 R7 的實況 —— 202 筆裡 130 筆機械上判得出來,
#           72 筆判不出來(可判定率 64%)。**那是「明顯不夠」的一側**,
#           而 100% 是「顯然足夠」的另一側;90% 是在兩者之間、
#           容得下一成雜訊而不容得下一整群系統性盲區的位置。
#
#   ⚠ 這個數字**沒有**跨規則的實證支撐 —— 目前只有 R7 一條有夠多的樣本。
#     它是一條**保守的預設**,不是量出來的最適值。
#
#   什麼條件重畫:當有第二條規則累積到 ≥100 筆且完成分類時,
#   拿兩條的可判定率分佈回來重評 —— **而不是等到有人覺得 90% 太嚴**。
#   重畫的依據是分佈,不是誰被擋住了。
MIN_DECIDABLE_RATE = 0.90

KNOWN_CLASSES = frozenset(CLASSES.values())


def _is_false_positive(classification):
    return classification in FALSE_POSITIVE_CLASSES


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


# ── 票 64:批次分類(套用卡)────────────────────────────────────────────

ID_PREFIX = 16


def _canonical(rec):
    """身分用的正規化形式。**排除 `classification`。**

    身分必須在**套用前後不變** —— 否則卡片套完之後就再也指不到它動過的東西,
    而「留檔」會變成留一份指不回去的紙。
    """
    d = dict((k, v) for k, v in rec.items() if k != "classification")
    return json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def record_id(rec):
    """一筆紀錄的身分 —— **整筆內容的雜湊,不是時間戳。**

    `ts` 在生產資料上**已經撞號**:量化 222 筆裡 `ts` 只有 221 個相異值,
    `ts` + `rule` 也一樣。用時間戳當鍵的批次工具今天就會把兩筆不同的判定
    當成同一筆。

    **也不用 `ts`+`rule`+`message` 三元組**:它今天唯一,但那是**這份資料**的
    性質,不是這個結構的性質。欄位集合是封閉且可窮舉的,而
    **封閉集合用枚舉勝過比對** —— 整筆雜湊就是枚舉,挑三個欄位是比對,
    而比對的漏是未知的(CLAUDE.md 常駐檢查項)。
    """
    return hashlib.sha256(_canonical(rec).encode("utf-8")).hexdigest()


class CardPlan(object):
    """套用卡的計畫。`applied` 在 dry-run 一律為 0 —— **不是「打算套幾筆」**,
    是「**真的寫進去幾筆**」。兩者用同一個欄位表達的話,dry-run 的輸出會
    讀起來像已經做過了。"""

    __slots__ = ("card", "applied", "by_class")

    def __init__(self, card):
        self.card = card
        self.applied = 0
        self.by_class = {}

    def __repr__(self):
        return "CardPlan(applied=%d, by_class=%r)" % (self.applied, self.by_class)


def load_card(path):
    """回 [(行號, dict), …]。壞行一律出聲(同 `load_log`)。"""
    out = []
    for lineno, line in enumerate(_read_lines(path), 1):
        line = line.strip()
        if not line:
            continue
        try:
            out.append((lineno, json.loads(line)))
        except ValueError as e:
            raise ShadowLogError(
                "套用卡第 %d 行不是合法 JSON:%s\n     檔案:%s" % (lineno, e, path))
    return out


def _card_ledger_path(log_path):
    return os.path.join(os.path.dirname(os.path.abspath(log_path)),
                        "shadow-cards.jsonl")


def apply_card(log_path, card_path, apply=False):
    """把一張套用卡套到影子日誌上。**全有全無。**

    預設 dry-run(`apply=False`)。**dry-run 也要擋** —— 一份把不合法的卡
    列成「將套用」的清單本身就是錯的答案(同 `sync.refuse_if_unclassified`)。

    工具**不產生判斷**:它只套用人寫在卡片上的分類。ADR 0012 的
    「逐筆判,不算總數」要的是每一筆都有一個判斷,不是每一筆都要按一次鍵 ——
    **批次模式換的是介面,不是判準。**
    """
    rows = load_log(log_path)

    # 日誌自己撞號 -> 卡片指過去會指到兩筆,而「套哪一筆」不是工具能決定的
    by_id = {}
    for i, r in enumerate(rows):
        by_id.setdefault(record_id(r), []).append(i)
    dup = dict((k, v) for k, v in by_id.items() if len(v) > 1)
    if dup:
        raise ShadowLogError(
            "影子日誌裡有內容完全相同的紀錄(%d 組重複),整批拒絕。\n"
            "     %s\n"
            "     缺的前提是**身分唯一**:卡片指過去會同時對到多筆,\n"
            "     而「該套哪一筆」是人的判斷,不是工具能決定的。"
            % (len(dup), "\n     ".join(
                "%s… 出現在第 %s 筆" % (k[:ID_PREFIX],
                                     "、".join(str(x + 1) for x in v))
                for k, v in sorted(dup.items()))))

    entries = load_card(card_path)

    # 卡片自己撞號 —— 同一件事的反方向
    seen = {}
    for lineno, e in entries:
        seen.setdefault((e.get("id") or "").strip(), []).append(lineno)
    cdup = dict((k, v) for k, v in seen.items() if len(v) > 1)
    if cdup:
        raise ShadowLogError(
            "套用卡裡有重複的 id(%d 組),整批拒絕。\n"
            "     %s\n"
            "     同一筆紀錄被指定兩次,而兩次的分類可能不同 —— 那要人決定。"
            % (len(cdup), "\n     ".join(
                "%s 出現在第 %s 行" % (k, "、".join(str(x) for x in v))
                for k, v in sorted(cdup.items()))))

    problems = []
    targets = []
    by_class = {}
    for lineno, e in entries:
        cid = (e.get("id") or "").strip()
        klass = e.get("class")
        why = (e.get("why") or "").strip()
        if not why:
            problems.append(
                "第 %d 行缺 `why` —— 一張沒有理由的批次卡,事後沒有人分得出"
                "它是判斷還是手滑。" % lineno)
        if klass not in CLASSES:
            problems.append(
                "第 %d 行的 class=%r 不是合法分類(合法值:%s)。"
                % (lineno, klass, "、".join(sorted(CLASSES))))
        matches = [i for i, r in enumerate(rows)
                   if cid and record_id(r).startswith(cid)]
        if not matches:
            problems.append(
                "第 %d 行的 id %s 在日誌裡對不到任何一筆 —— 卡片與日誌不同步。"
                % (lineno, cid or "(空)"))
        elif len(matches) > 1:
            problems.append(
                "第 %d 行的 id %s 對到 %d 筆 —— 前綴不夠長,加長它。"
                % (lineno, cid, len(matches)))
        elif rows[matches[0]].get("classification"):
            problems.append(
                "第 %d 行的目標**已經有分類**(%s)—— 覆蓋別人的判斷要是一個"
                "顯式動作,不是批次的副作用。"
                % (lineno, rows[matches[0]]["classification"]))
        elif klass in CLASSES:
            targets.append((matches[0], klass))
            by_class[klass] = by_class.get(klass, 0) + 1

    if problems:
        raise ShadowLogError(
            "套用卡有 %d 個問題,**整批拒絕,一個字都沒寫**:\n     %s\n"
            "     卡片:%s\n"
            "     全有全無不是嚴格,是可還原性:部分套用之後,\n"
            "     沒有人分得出哪些是這張卡做的、哪些本來就在。"
            % (len(problems), "\n     ".join(problems), card_path))

    plan = CardPlan(card_path)
    plan.by_class = by_class
    if not apply:
        return plan

    for i, klass in targets:
        rows[i]["classification"] = CLASSES[klass]

    on_disk = _nonblank_line_count(log_path)
    if len(rows) != on_disk:
        raise ShadowLogError(
            "拒絕重寫影子日誌:手上有 %d 筆,檔案裡有 %d 筆非空白行。"
            % (len(rows), on_disk))

    with io.open(log_path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    plan.applied = len(targets)

    # 留檔在**寫入並通過筆數守恆之後**才做 —— 驗證沒過就不該有憑證,
    # 否則帳面上會出現一張替沒發生的套用背書的紀錄(同 sync 的 provenance)。
    rec = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "card": card_path,
        # **指紋要能被獨立查證**:事後有人可以拿卡片重算一次。
        # 一份只能自我背書的紀錄,證明不了任何事。
        "card_sha256": hashlib.sha256(
            io.open(card_path, "rb").read()).hexdigest(),
        "applied": plan.applied,
        "by_class": by_class,
    }
    with io.open(_card_ledger_path(log_path), "a",
                 encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return plan


def promotion_status(path):
    """回傳每條規則的計數與晉升判定。

    ## 三個分母,不是一個(票 67)

        total       這條規則的**全部**紀錄(含還沒判的)
        classified  有 classification 欄的
        decidable   真陽 + 誤報 + 刻意 refuse —— **假陽率的分母**

    「無法判定」進 `classified`、進 `total`,**不進 `decidable`** ——
    它是**判定不能**,不是判定結果:進分母會稀釋假陽率,進分子會誣賴規則。

    ## 轉正要同時滿足三條

        classified >= MIN_CLASSIFIED
        fp_rate     <  MAX_FALSE_POSITIVE_RATE
        decidable / total >= MIN_DECIDABLE_RATE          <- 票 67 新增

    第三條要防的東西,2026-08-19 在量化實測過:R7 202 筆,先判掉機械上
    判得出來的 130 筆(全部是刻意 refuse),於是
    `已分類 130 >= 10` 且 `假陽率 0.0% < 5%` —— **印出「可轉正」**,
    而誤報全部在還沒判的 72 筆裡。

    > **一條規則可以靠「只判對自己有利的那一群」把自己判成可轉正。**
    > **36% 判不出來的規則,它的 0% 假陽率不代表它準,
    > 只代表我們只看了它願意讓我們看的那部分。**

    原本的 `MIN_CLASSIFIED` 問的是**絕對數**(樣本夠不夠),
    擋不住這件事 —— 擋得住的是**涵蓋率**,所以第三條問的是比例。
    """
    rows = load_log(path)
    per = {}
    # **`total` 要數全部紀錄,不能只數已分類的** —— 可判定率的分母是它,
    # 而「還沒判的有多少」正是這一輪要讓它看得見的東西。
    totals = {}
    for r in rows:
        totals[r.get("rule", "?")] = totals.get(r.get("rule", "?"), 0) + 1
    for lineno, r in enumerate(rows, 1):
        c = r.get("classification")
        if not c:
            continue
        if c not in KNOWN_CLASSES:
            # **不靜默歸桶。** 前綴實作會把「假陽/沒登記過的」算成假陽(高估),
            # 枚舉實作會把它算成不是假陽(低估)—— 而**兩種靜默都印得出一個
            # 看起來權威的百分比**。所以出聲。
            raise ShadowLogError(
                "第 %d 筆的 classification 是 %r,不是任何一個已知分類。\n"
                "     已知分類:%s\n"
                "     檔案:%s\n"
                "     **不猜它屬於哪一桶** —— 猜高會誇大假陽率、猜低會掩蓋它,\n"
                "     而兩種猜法都會印出一個看起來權威的數字。\n"
                "     修法:把那一筆改成已知分類,或先確認這份日誌是不是\n"
                "     由別的版本寫的。"
                % (lineno, c, "、".join(sorted(KNOWN_CLASSES)), path))
        rule = r.get("rule", "?")
        d = per.setdefault(rule, {"classified": 0, "false_positives": 0,
                                  "true_positives": 0, "deliberate": 0,
                                  "undecidable": 0})
        d["classified"] += 1
        if _is_false_positive(c):
            d["false_positives"] += 1
        elif c == DELIBERATE_CLASS:
            # **算進分母,不算進分子**(ADR 0012 §2)。
            # 不算分母的話,一條規則只要大量 fail-closed 就能稀釋掉自己的假陽率。
            d["deliberate"] += 1
        elif c == UNDECIDABLE_CLASS:
            # **兩個分母都不進**(票 67)。與刻意 refuse 的差別就在這裡:
            # 刻意 refuse 是「規則做了對的事,而它有成本」——成本要算;
            # 無法判定是「我們不知道規則做得對不對」——那不是成本,是空白。
            d["undecidable"] += 1
        elif c == TRUE_POSITIVE_CLASS:
            d["true_positives"] += 1
    for rule, d in per.items():
        d["total"] = totals.get(rule, d["classified"])
        d["unclassified"] = d["total"] - d["classified"]
        d["decidable"] = (d["true_positives"] + d["false_positives"]
                          + d["deliberate"])
        d["fp_rate"] = ((d["false_positives"] / d["decidable"])
                        if d["decidable"] else 0.0)
        d["decidable_rate"] = ((d["decidable"] / d["total"])
                               if d["total"] else 0.0)
        d["promotable"] = (d["classified"] >= MIN_CLASSIFIED
                           and d["fp_rate"] < MAX_FALSE_POSITIVE_RATE
                           and d["decidable_rate"] >= MIN_DECIDABLE_RATE)
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
    print("每規則晉升狀態(三條同時滿足才可轉正:"
          "已分類 ≥%d、假陽率 <%.0f%%、可判定率 ≥%.0f%%):"
          % (MIN_CLASSIFIED, MAX_FALSE_POSITIVE_RATE * 100,
             MIN_DECIDABLE_RATE * 100))
    # **三分類的三個數都印**(票 65 / ADR 0012 §2)。只印一個 FP 的話,
    # 讀者無從判斷分母裡有多少是刻意成本 —— 而那正是同一批資料
    # 曾經算得出兩個相反 FP 的原因。
    print("  (假陽率的分母 = 真陽+誤報+刻意 refuse;無法判定兩個分母都不進)")
    print("  (可判定率 = 那個分母 ÷ 總筆數 —— **未判定的餘量看得見**,票 67)")
    for rule in sorted(per):
        d = per[rule]
        print("  %-4s 總 %3d  已分類 %3d  未判定 %3d"
              "  真陽 %3d  刻意 refuse %3d  誤報 %3d  無法判定 %3d"
              % (rule, d["total"], d["classified"], d["unclassified"],
                 d["true_positives"], d["deliberate"], d["false_positives"],
                 d["undecidable"]))
        print("       假陽率 %5.1f%%  可判定率 %5.1f%%  -> %s"
              % (d["fp_rate"] * 100, d["decidable_rate"] * 100,
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
        # 範圍字串從 `CLASSES` 導出,不寫死 —— 寫死的話,加一類而忘了改這裡,
        # 使用者會看到一個**不含新鍵的提示**,然後永遠不會按它。
        ans = input("  分類 [%s-%s/s/q]: "
                    % (min(CLASSES), max(CLASSES))).strip()
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
    card = None
    for i, a in enumerate(argv):
        if a == "--card" and i + 1 < len(argv):
            card = argv[i + 1]
    try:
        if card:
            apply = "--apply" in argv
            plan = apply_card(log, card, apply=apply)
            total = sum(plan.by_class.values())
            print("套用卡:%s" % card)
            print("將套用 %d 筆:%s"
                  % (total, "、".join("%s×%d(%s)" % (k, plan.by_class[k], CLASSES[k])
                                      for k in sorted(plan.by_class))))
            if apply:
                print("已寫入 %d 筆,留檔於 %s" % (plan.applied, _card_ledger_path(log)))
                print()
                print_status(log)
            else:
                # **dry-run 的收尾句要說出「什麼都沒發生」。** 少了它,
                # 上面那份清單讀起來像是已經做完的報告(F-104 的形狀:
                # 「我做了什麼」與「現在的狀態是什麼」)。
                print("(dry-run,日誌一個位元組都沒動;要實際套用加 --apply)")
        elif "--status" in argv:
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
