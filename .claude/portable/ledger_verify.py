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
    """回傳斷點 `[(前一筆序號, 後一筆序號, 前一筆的 result_hash, 後一筆的 content_hash), …]`。

    序號從 1 起算,對得上人讀的清單。沒有斷點回 `[]`。
    0 或 1 筆沒有「段」可以斷,回 `[]` —— 帳本第一次被寫時就是 1 筆,
    那不是異常狀態。
    """
    breaks = []
    for i in range(len(records) - 1):
        ended = records[i].get("result_hash")
        started = records[i + 1].get("content_hash")
        if ended != started:
            breaks.append((i + 1, i + 2, ended, started))
    return breaks


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
    breaks = chain_breaks(records)
    out.append("")
    out.append("筆數                : %d" % len(records))
    out.append("首尾相等            : %s" % ("是" if endpoints_match(records) else "否"))
    out.append("逐段接續(全部相連): %s"
               % ("是" if not breaks else "否 —— %d 處斷點" % len(breaks)))
    for a, b, ended, started in breaks:
        out.append("    斷點:第 %d 筆結束於 %s,第 %d 筆卻從 %s 開始"
                   % (a, (ended or "")[:12], b, (started or "")[:12]))
    if breaks:
        out.append("")
        out.append("**斷點不等於缺陷。** 它的意思是「有一次改動發生在前哨看不見的地方」")
        out.append("(`git checkout`、外部編輯器、或真的有人繞過)—— 要讀上下文才分得出來。")
    out.append("")
    out.append("**首尾相等不蘊含逐段接續** —— 兩者是分開的兩個問題。")
    return "\n".join(out)


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
