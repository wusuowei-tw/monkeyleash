# -*- coding: utf-8 -*-
"""G1 驗收 —— 每條案例斷言**它自己那條保護路徑**出現在擋下訊息裡。

用法:python .claude/portable/g1_verify.py [要驗的 guard 檔]
      預設驗正式檔;改草稿時傳 .claude/portable/g1_guard_draft.py。

## 案例是**執行時從實際清單生成的**,不是寫死在這裡

兩個理由,一個安全、一個正確性:

- **安全**:寫死的話,每個人的保護路徑(家目錄、備份位置)會進到版控,
  而這個 repo 要公開。清單留在 `~/.claude/g1-protected.txt`,repo 只有生成邏輯。
- **正確性(暗傷)**:寫死一份拷貝的話,清單改了、驗收還在驗**舊的拷貝** ——
  那正是 F-032 第四種形狀(綠的原因不是你以為的)。改讀實際清單之後,
  驗的是「**現行清單的每一條**都擋得住」,清單長出新的一條,驗收自動涵蓋它。

## 為什麼不能只看 exit=2

只看退出碼:「因為找不到清單而擋」與「因為命中保護路徑而擋」長得一樣。
再往下:只驗「有命中某條」仍不夠 —— 清單被讀成別的內容而仍可讀時,
每條探針可能命中同一條無關項目,全部通過而綠的原因不對(F-032)。
所以每條帶著它應該命中的那條路徑,逐條比對。

## 一次觀測只放一個受測項

G1 是 fail-fast(ADR 0009 第 4 步)。本檔每個 payload 只含一個受測路徑。

本檔在票 02 宣告為 Untested by decision:失效是**吵鬧的** ——
跑不起來立刻知道,跑完逐條印出命中的路徑,錯一條看得見(F-027)。
"""

import json
import os
import re
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OFFICIAL = os.path.join(os.path.expanduser("~"), ".claude", "hooks", "g1_guard.py")
PROTECTED_LIST = os.path.join(os.path.expanduser("~"), ".claude", "g1-protected.txt")


def protected_entries():
    """讀實際保護清單,回傳路徑串列(去註解、去空行)。讀不到回空。"""
    out = []
    try:
        for line in open(PROTECTED_LIST, encoding="utf-8"):
            line = line.split("#", 1)[0].strip()
            if line:
                out.append(line)
    except Exception:
        pass
    return out


def as_backslash(p):
    return p.replace("/", "\\")


def as_probe(p):
    """把保護路徑轉成一條會碰到它的無害指令。"""
    return r'touch "%s\g1_verify_probe.txt"' % as_backslash(p.rstrip("/\\"))


# 應放行 / 回歸集不含任何個人路徑,寫死無妨。
PASS_THROUGH = [
    ("專案內刪除",       r'rm -rf build/ && rm .cache/x.json'),
    ("專案內一般指令",   r'python -m pytest tests/ -q'),
    ("讀取無關外部路徑", r'cat C:/Windows/System32/drivers/etc/hosts'),
]

# 第二級的**回歸集**:收窄比對之前會被擋下的專案外破壞性指令,逐條斷言仍然擋。
# 本輪三個修法方向都是**比對得更少**,而在擋東西的元件裡每次縮小都是潛在 fail-open。
# 帶 `-` 與 `.` 的那幾條是關鍵:舊正則把 `/etc-backup/x` 截成 `/etc` —— 收邊界後
# 若整條不再被擷取,就是從「擋下」變「放行」。
LEVEL2_REGRESSION = [
    ("一般 POSIX 路徑",     r'rm -rf /etc/passwd'),
    ("家目錄",              r'rm -rf /home/someone/data'),
    ("Windows 使用者目錄",  r'rm -rf C:/Users/someone/Documents/x'),
    ("git bash 形態",       r'rm -rf /d/somewhere/x'),
    ("頂層目錄帶連字號",    r'rm -rf /etc-backup/x'),
    ("頂層目錄帶點",        r'rm -rf /usr.old/x'),
    ("家目錄帶連字號",      r'rm -rf /home-old/data'),
    ("root 帶點",           r'rm -rf /root.bak/x'),
    ("暫存區的鄰居",        r'rm -rf /tmpdata/x'),
    ("暫存區名稱加後綴",    r'rm -rf /tmp.bak/x'),
]


def run(guard, payload):
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = REPO
    p = subprocess.run([sys.executable, guard],
                       input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                       capture_output=True, env=env)
    return p.returncode, p.stderr.decode("utf-8", "replace").strip()


def bash(cmd):
    return {"tool_name": "Bash", "tool_input": {"command": cmd}}


def main(guard):
    print("驗的是:%s" % guard)
    entries = protected_entries()
    print("實際保護清單:%s(%d 條)\n" % (PROTECTED_LIST, len(entries)))
    if len(entries) < 3:
        print("清單少於 3 條 —— 驗收沒有實質對象,先確認清單存在。")
        return 1
    failures = []

    # 票 25:磁碟根目錄條目(`D:\` 之類)**這支腳本以前會給它假綠**。
    # as_probe() 產出 `touch "D:\g1_verify_probe.txt"`,而那條剛好走
    # `d:` —— 磁碟根條目唯一生效的變體 —— 於是命中、斷言通過,
    # 而真正該擔心的 `/d/...` 形態一路放行。**綠的原因不是保護生效了。**
    # 現在 guard 會 fail-closed 拒絕這種條目,所以清單裡不該再有;
    # 這一段是驗收側的對應修改:行為改了,驗收也要改,
    # 否則陷阱只是從 guard 換到這裡(F-032:綠的原因不是你以為的)。
    drive_roots = [i + 1 for i, e in enumerate(entries)
                   if re.match(r"^(?:[A-Za-z]:[\\/]?|/[A-Za-z]/?)$", e.strip())]
    print("=== 磁碟根目錄條目(票 25:守不住的寫法)===")
    if drive_roots:
        print("  第 %s 條是磁碟根目錄 —— guard 會 fail-closed 拒絕整份清單。"
              % ", ".join(str(n) for n in drive_roots))
        print("  改法:把要保護的東西逐條列出來。**不印路徑本身**,序號自己去對。")
        failures.append("磁碟根目錄條目(第 %s 條)"
                        % ", ".join(str(n) for n in drive_roots))
    else:
        print("  無 ✓")
    print()

    print("=== 第一級:清單每一條各斷言【命中的是哪一條】 ===")
    for p in entries:
        rc, err = run(guard, bash(as_probe(p)))
        blocked = rc == 2 and "G1/保護清單" in err
        want = as_backslash(p.rstrip("/\\"))
        right = blocked and want in err
        # 只印命中與否,**不印路徑本身** —— 這支腳本的輸出也可能被貼進公開處
        print("  %-3d %s" % (entries.index(p) + 1,
                             "OK" if right else
                             ("擋了但命中的不是這條" if blocked else "沒擋到")))
        if not right:
            failures.append("第 %d 條" % (entries.index(p) + 1))

    print("\n=== 子目錄自動涵蓋(取第一條 + 深層子路徑)===")
    sub = bash(r'touch "%s\2023\x\y.txt"' % as_backslash(entries[0].rstrip("/\\")))
    rc, err = run(guard, sub)
    ok = rc == 2 and "G1/保護清單" in err and as_backslash(entries[0].rstrip("/\\")) in err
    print("  子目錄  %s" % ("擋下 OK" if ok else "不符"))
    if not ok:
        failures.append("子目錄")

    print("\n=== 相鄰名稱不得命中(前綴邊界,取前三條加後綴)===")
    for p in entries[:3]:
        neighbour = bash(r'ls "%s_g1_neighbour\x"' % as_backslash(p.rstrip("/\\")))
        rc, err = run(guard, neighbour)
        ok = rc == 0
        print("  第 %d 條的鄰居  %s" % (entries.index(p) + 1,
                                        "放行 OK" if ok else "誤擋"))
        if not ok:
            failures.append("鄰居 %d(誤擋)" % (entries.index(p) + 1))

    print("\n=== Write 工具寫入第一條保護目錄 ===")
    rc, err = run(guard, {"tool_name": "Write",
                          "tool_input": {"file_path":
                                         r"%s\新檔案.txt" % as_backslash(entries[0].rstrip("/\\")),
                                         "content": "x"}})
    ok = rc == 2 and "G1/保護清單" in err
    print("  Write  %s" % ("擋下 OK" if ok else "不符"))
    if not ok:
        failures.append("Write 工具")

    print("\n=== 第二級回歸集:收窄比對前擋得住的,現在還擋得住嗎 ===")
    for label, cmd in LEVEL2_REGRESSION:
        rc, err = run(guard, bash(cmd))
        ok = rc == 2 and "G1/專案外破壞性動作" in err
        print("  %-22s exit=%d  %s" % (label, rc, "擋下 OK" if ok else
                                       ("擋了但不是第二級" if rc == 2 else "沒擋到")))
        if not ok:
            print("      指令:%s" % cmd)
            print("      實得:%s" % (err.splitlines()[0] if err else "(無訊息 = 放行)"))
            failures.append(label + "(第二級回歸)")

    print("\n=== 應放行 ===")
    for label, cmd in PASS_THROUGH:
        rc, err = run(guard, bash(cmd))
        print("  %-24s exit=%d  %s" % (label, rc, "OK" if rc == 0 else "誤擋"))
        if rc != 0:
            failures.append(label + "(誤擋)")

    print("\n=== fail-closed:清單讀不到 ===")
    moved = PROTECTED_LIST + ".verify-moved"
    shutil.move(PROTECTED_LIST, moved)
    try:
        rc, err = run(guard, bash("touch /tmp/x"))
        ok = rc == 2 and "fail-closed" in err
        print("  清單不存在  exit=%d  %s" % (rc, "OK" if ok else "不符"))
        if not ok:
            failures.append("fail-closed")
    finally:
        shutil.move(moved, PROTECTED_LIST)

    print()
    if failures:
        print("不合格:%s" % failures)
        return 1
    print("全部通過:%d 條保護路徑各命中自己那一條、子目錄涵蓋、"
          "3 個相鄰名稱不誤中、%d 條第二級回歸擋下、fail-closed 成立。"
          % (len(entries), len(LEVEL2_REGRESSION)))
    return 0


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else OFFICIAL
    sys.exit(main(target))
