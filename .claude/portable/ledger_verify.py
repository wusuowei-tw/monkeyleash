# -*- coding: utf-8 -*-
"""帳本鏈驗證 —— 逐段驗接續,不是只比端點。

用法:
  python .claude/portable/ledger_verify.py            驗整份 .dev/gate-exemptions.jsonl
  python .claude/portable/ledger_verify.py --diff     只驗相對 HEAD 新增的那幾筆
  python .claude/portable/ledger_verify.py <路徑>     驗指定檔案

## 這條鏈是什麼

`.dev/gate-exemptions.jsonl` 的每一筆帶 `content_hash`(編輯前)與
`result_hash`(編輯後)。連續的編輯因此串成一條鏈,而它可以
**獨立於任何人的宣稱**證明「這個檔案出去又回來了」——
票 58 與票 47 的三次有界突變都靠它收尾。

## v1 -> v2 的判準(這支存在的理由)

**第一版問錯了問題。** v1 的檢查是:

    第一筆的 content_hash == 最後一筆的 result_hash

那條斷言在**鏈中間斷過一次、又走回同一個雜湊**時**照樣通過**。
票 47 批 3 的鏈正是那個形狀:

    5  fa29d055 -> 795dff63     M4
    6  54dabea0 -> adcc5fb1     M5    <- 第 5 筆結束於 795dff63,這裡卻從 54dabea0 開始

斷點來自那一次還原走了 `git checkout`(Bash 在 `gate.py:2028-2043` 早退,
不經前哨,依設計不記帳)。**v1 說「回到原點」,而它只看了兩端。**

> **首尾相等不蘊含逐段接續 —— 兩者要分開報。**

所以本檔把它拆成**兩個獨立的述詞**,而不是一個布林:
型別上就看得見它們可以同時給出不同答案。

## 斷點不等於缺陷

`chain_breaks()` **只回報,不判對錯**。斷點的意思是
**「有一次改動發生在前哨看不見的地方」** —— 可能是 `git checkout`、
可能是外部編輯器、也可能是真的有人繞過。分辨它們要讀上下文,
**那是人的判斷**(同 `sync.refuse_if_duplicate_headings` 的理由:
護欄讓它現形,不替人決定)。

因此本檔**永遠回 0**,不用退出碼表達「有沒有斷點」——
把「需要人看一眼」講成「失敗」,會讓它被當成紅燈去消除,
而消除的方法多半是不再跑它(F-031)。

## 為什麼住在 `.claude/portable/` 而不是 `scripts/`

`scripts/` 在非原始碼清單裡,放進去等於讓它不受 R2/R3 管 ——
而**這支是判定邏輯**(它決定一條鏈算不算連續)。
CLAUDE.md 的常駐檢查項就是這條,那個位置已經撞過三次。
形式抄 `g1_verify.py` / `verify_gates.py`:驗收工具與被驗的東西同層。

**票 49 的前向輸入**:本檔讀的欄位(`content_hash` / `result_hash`)
就是票 49 要設計的「判定紀錄」裡已經存在的那一半。
票 49 若改動帳本格式,這支是第一個會紅的東西 —— 那是刻意的。
"""
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LEDGER = os.path.join(ROOT, ".dev", "gate-exemptions.jsonl")

# 已知斷點白名單(票 116 B-6)。**per-repo**:`.dev/` 標 `generate`,不隨安裝出貨,
# 而每個 repo 的帳本有自己的歷史。檔案不存在 = 空白名單(fail-closed)。
KNOWN_BREAKS = os.path.join(ROOT, ".dev", "known-chain-breaks.txt")

# ── 四桶(票 116 B-6)────────────────────────────────────────────────────────
#
# 原本 `chain_breaks` 回一個扁平清單,而那個清單裡混著**三種完全不同**的東西,
# 外加一個**根本沒被報出來**的第四種。實測(2026-09-08,本 repo 帳本 223 筆):
#
#     設計上的斷    29 對   pre-commit 算不出結果內容,記 None —— 是設計
#     格式交界       1 對   票 08 之前的 5 鍵舊格式與之後的交界 —— 是歷史
#     真的對不上     4 對   要人讀上下文的那些
#     無從驗證      39 對   **舊實作一個都沒報** ⇒ fail-open
#
# 前三種一起報 34 個而其中 30 個是設計或歷史 ⇒ 噪音訓練人忽略訊號(`F-031`)。
BUCKET_BY_DESIGN = "by_design"
BUCKET_FORMAT_SEAM = "format_seam"
BUCKET_MISMATCH = "mismatch"
BUCKET_UNVERIFIABLE = "unverifiable"
BUCKET_LINKED = "linked"                 # 不是斷點,但要能對帳「每一對都有家」

BUCKET_ORDER = (BUCKET_BY_DESIGN, BUCKET_FORMAT_SEAM,
                BUCKET_MISMATCH, BUCKET_UNVERIFIABLE)

BUCKET_LABELS = {
    BUCKET_BY_DESIGN: u"設計上的斷(pre-commit 算不出結果內容)",
    BUCKET_FORMAT_SEAM: u"格式交界(有無雜湊欄位的兩種格式相接)",
    BUCKET_MISMATCH: u"真的對不上(兩邊都是雜湊而不相等)",
    BUCKET_UNVERIFIABLE: u"無從驗證(缺雜湊,查不了)",
    BUCKET_LINKED: u"接得上",
}


def _has_hash_keys(rec):
    """這一筆帶不帶雜湊欄位。**問鍵在不在,不問值。**

    票 08 之前的 5 鍵舊格式**連鍵都沒有**;而 pre-commit 那一半鍵在、值是 `None`
    (`gate.exemption_record` 逐字:「**None 不是 False**」)。
    兩者是不同的東西,分桶要分得開,所以這裡只問鍵。
    """
    return ("content_hash" in rec) or ("result_hash" in rec)


def parse_records(text):
    """JSON Lines -> 紀錄串列。**壞行丟 `ValueError`,不跳過。**

    跳過等於「那一段改動不存在」,而鏈會因此**看起來是連續的** ——
    一個因為漏看而變乾淨的結論,比看得見的斷點危險(fail-closed 的同一條)。
    """
    out = []
    for lineno, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception as e:
            raise ValueError("帳本第 %d 行解析不了:%s" % (lineno, e))
    return out


def chain_breaks(records):
    """**四桶**(票 116 B-6)。回 `{桶名: [(前序號, 後序號, ended, started), …]}`。

    序號從 1 起算,對得上人讀的清單。0 或 1 筆沒有「段」可以斷,五個桶都空 ——
    帳本第一次被寫時就是 1 筆,那不是異常狀態。

    ## 為什麼從扁平清單改成四桶

    舊版只問 `ended != started`,於是把**三種完全不同**的東西報成同一種:
    設計上的斷(pre-commit 記 `None`)、格式交界(舊格式沒有雜湊欄位)、
    真的對不上。而**第四種根本沒被報出來** ——
    相鄰兩筆都沒有雜湊欄位時,兩邊 `.get()` 都是 `None`,`None != None` 為假
    ⇒ **不算斷**。那 40 筆無從驗證的紀錄因此與「驗過而且接得上」長得一模一樣。

    **那是 fail-open。** `parse_records` 的 docstring 已寫過同一條的另一半
    (壞行不能跳過,否則鏈會**看起來是連續的**)—— 它管的是壞行,
    **沒管到「解析得了但沒有雜湊欄位的行」,而後果相同**。

    ## 分類是**窮舉**的

    每一對相鄰恰好落進一個桶(含 `BUCKET_LINKED`)——
    `tests/test_ledger_verify.py::test_the_four_buckets_partition_every_adjacent_pair`
    釘住這件事。少了那條,分類裡多一個沒人注意的 `else` 就會靜靜吃掉一群東西,
    **而被吃掉的與不存在的在輸出上長得一樣**。

    ## ⚠ 回傳形狀變了

    舊版回 list。唯一的生產消費端是本檔的 `report()`,測試側是
    `tests/test_ledger_verify.py` —— 兩者都在本刀內一起更新。
    形狀不對時 `report()` 會當場丟例外(**吵**,不是靜默),而它與本函式同檔。
    """
    out = dict((k, []) for k in BUCKET_ORDER)
    out[BUCKET_LINKED] = []
    for i in range(len(records) - 1):
        a, b = records[i], records[i + 1]
        ended = a.get("result_hash")
        started = b.get("content_hash")
        pair = (i + 1, i + 2, ended, started)
        a_keys, b_keys = _has_hash_keys(a), _has_hash_keys(b)

        if not a_keys and not b_keys:
            out[BUCKET_UNVERIFIABLE].append(pair)
        elif not a_keys or not b_keys:
            out[BUCKET_FORMAT_SEAM].append(pair)
        elif ended is None and a.get("at_commit") is True:
            out[BUCKET_BY_DESIGN].append(pair)
        elif ended == started:
            out[BUCKET_LINKED].append(pair)
        elif ended is not None and started is not None:
            out[BUCKET_MISMATCH].append(pair)
        else:
            # 鍵在而值是 `None`,且不是 pre-commit 那一半 —— 一樣查不了。
            # 本 repo 實測 0 對(2026-09-08),但**分類必須窮舉**:
            # 留一個沒有家的分支,就等於留一個靜默吃掉東西的地方。
            out[BUCKET_UNVERIFIABLE].append(pair)
    return out


def known_breaks(path=None):
    """已知斷點白名單。回 `{(ended, started): 理由}`。檔案不存在回 `{}`。

    ## 這張清單的由來

    第六站 2026-08-24 首跑就寫下「帳本鏈已知斷點非缺陷;若帳本鏈驗證常態化,
    需『已知斷點附理由』白名單」,**而它從未落地**(`F-110`:規矩寫下來了,
    而沒有東西會因為它沒被做而叫)。票 116 B-6 是那句話的主詞。
    **當時 1 處,落地時 4 處** —— 集合長大了而沒有人回頭看。

    ## 定位鍵是**雜湊對**,不是索引

    索引會隨帳本增長而漂(帳本每天都在長)。**引身分,不引位置** ——
    與「引符號名不引行號」(票 114)、「記 ADR 編號不記路徑」(票 116 B-8)同一條。

    ## 格式:`<ended> <started> <理由>`,**理由欄硬性**

    只有兩個雜湊而沒有理由 ⇒ `ValueError`,不是靜默接受。
    理由欄是讓「這一處為什麼是對的」看得見的東西;少了它,
    白名單會退化成一張「把紅燈消掉」的清單,**而那正是它要防的**。

    `#` 開頭與空行是註解。
    """
    p = path or KNOWN_BREAKS
    out = {}
    if not os.path.exists(p):
        return out
    for lineno, line in enumerate(io.open(p, encoding="utf-8-sig")
                                  .read().splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 2)
        if len(parts) < 3 or not parts[2].strip():
            raise ValueError(
                "%s 第 %d 行少了理由欄:%r\n"
                "     格式是 `<前一筆 result_hash> <後一筆 content_hash> <為什麼這一處是對的>`。\n"
                "     沒有理由的白名單就是一張把紅燈消掉的清單。" % (p, lineno, line))
        out[(parts[0], parts[1])] = parts[2].strip()
    return out


def unregistered_mismatches(records, path=None):
    """「真的對不上」裡**沒有登記在白名單**的那些。

    白名單**只作用在這一桶** —— 另外三桶不是給人登記的:
    設計上的斷與格式交界是構造決定的,無從驗證是缺資料,
    登記它們等於把「查不了」講成「查過了」。
    """
    known = known_breaks(path)
    return [p for p in chain_breaks(records)[BUCKET_MISMATCH]
            if (p[2], p[3]) not in known]


def endpoints_match(records):
    """第一筆的 `content_hash` 是不是等於最後一筆的 `result_hash`。

    **這只回答「有沒有走回起點」,不回答「路上有沒有斷」** —— 後者問 `chain_breaks()`。
    兩個述詞分開存在,是因為它們可以同時給出不同答案(v1 的整個缺陷)。

    空鏈回 `False`:沒有端點可比,而**「沒有證據」不得回報成「證明了」**。
    """
    if not records:
        return False
    return records[0].get("content_hash") == records[-1].get("result_hash")


def added_records(path=None):
    """相對 HEAD **新增**的那幾筆 —— 驗一次實驗的鏈時要的是這個,不是整份。"""
    rel = os.path.relpath(path or LEDGER, ROOT).replace(os.sep, "/")
    out = subprocess.run(["git", "-C", ROOT, "diff", "-U0", "--", rel],
                         capture_output=True)
    if out.returncode != 0:
        raise ValueError("問不到 %s 的 diff(退出碼 %s)" % (rel, out.returncode))
    text = "\n".join(
        l[1:] for l in out.stdout.decode("utf-8", "replace").splitlines()
        if l.startswith("+") and not l.startswith("+++"))
    return parse_records(text)


def report(records):
    out = []
    for i, r in enumerate(records, 1):
        out.append("%3d  ticket=%-4s tool=%-10s %s -> %s"
                   % (i, r.get("ticket"), r.get("tool"),
                      (r.get("content_hash") or "")[:12],
                      (r.get("result_hash") or "")[:12]))
    buckets = chain_breaks(records)
    known = known_breaks()
    total_pairs = max(len(records) - 1, 0)
    flagged = sum(len(buckets[k]) for k in BUCKET_ORDER)

    out.append("")
    out.append("筆數                : %d" % len(records))
    out.append("相鄰對              : %d" % total_pairs)
    out.append("首尾相等            : %s" % ("是" if endpoints_match(records) else "否"))
    out.append("")
    out.append("=== 分桶(每一對相鄰恰好落進一個桶)===")
    for k in BUCKET_ORDER:
        out.append("  %-34s %4d 對" % (BUCKET_LABELS[k], len(buckets[k])))
    out.append("  %-34s %4d 對" % (BUCKET_LABELS[BUCKET_LINKED],
                                   len(buckets[BUCKET_LINKED])))
    out.append("  %-34s %4d 對  (= 相鄰對 %d,%s)"
               % ("合計", flagged + len(buckets[BUCKET_LINKED]), total_pairs,
                  "對得上" if flagged + len(buckets[BUCKET_LINKED]) == total_pairs
                  else "**對不上 —— 分類有洞**"))

    mism = buckets[BUCKET_MISMATCH]
    if mism:
        out.append("")
        out.append("=== 真的對不上(逐筆)===")
        for a, b, ended, started in mism:
            mark = "已登記" if (ended, started) in known else "**未登記**"
            out.append("  [%s] 第 %d 筆結束於 %s,第 %d 筆卻從 %s 開始"
                       % (mark, a, (ended or "")[:12], b, (started or "")[:12]))
            why = known.get((ended, started))
            if why:
                out.append("            理由:%s" % why)
        left = [p for p in mism if (p[2], p[3]) not in known]
        if left:
            out.append("")
            out.append("  ⚠ 有 %d 處**未登記** —— 要嘛查出它為什麼發生,"
                       "要嘛寫進 %s 並附理由。" % (len(left), rel_known()))

    out.append("")
    out.append("**斷點不等於缺陷。** 它的意思是「有一次改動發生在前哨看不見的地方」")
    out.append("(`git checkout`、外部編輯器、或真的有人繞過)—— 要讀上下文才分得出來。")
    out.append("**所以退出碼恆為 0** —— 把「需要人看一眼」講成「失敗」,")
    out.append("會讓它被當成紅燈去消除,而消除的方法多半是不再跑它(F-031)。")
    out.append("")
    out.append("**首尾相等不蘊含逐段接續** —— 兩者是分開的兩個問題。")
    return "\n".join(out)


def rel_known():
    """白名單檔給人看的相對路徑。"""
    try:
        return os.path.relpath(KNOWN_BREAKS, ROOT).replace(os.sep, "/")
    except ValueError:
        return KNOWN_BREAKS


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if "--diff" in argv:
        records = added_records(args[0] if args else None)
    else:
        path = args[0] if args else LEDGER
        records = parse_records(io.open(path, encoding="utf-8").read())
    sys.stdout.buffer.write((report(records) + "\n").encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
