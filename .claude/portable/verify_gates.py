# -*- coding: utf-8 -*-
"""在一個空 repo 裡把框架真的裝一次,然後讓**每一條規則各擋一次**。

用法:python .claude/portable/verify_gates.py <暫存目錄>

**規則清單來自 gate.rule_codes(),不是這裡的對照表。** 兩者的差集由測試守住:
新增一條規則而沒有對應情境時,`tests/test_gate.py` 會紅。寫死條數的驗收條件
下次加規則時不會有人記得改,而漏掉的那條不會有任何東西出聲。

**跑的是真實安裝**,不是簡化版:真的 git init、真的複製、真的建 commit、
真的裝 hook、真的用 `git commit` 觸發權威層。一旦這裡出現「安裝的簡化版」,
S5「安裝流程不另測」的涵蓋就是假的 —— 那是 F-018 的形狀:
偵測用的東西自己繞過了被偵測的路徑。

本檔在票 02 宣告為 Untested by decision(接縫 S4):它的失效是**吵鬧的** ——
跑不起來立刻知道,跑完會印出每條規則各擋一次,少一條看得見。
與紅燈紀錄器那種靜默失效不同(F-027)。失敗訊息指出**是哪條規則**沒擋到,
那句話就是它保持吵鬧的機制。
"""

import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import install  # noqa: E402


def sh(args, cwd, check=True):
    p = subprocess.run(args, cwd=cwd, capture_output=True)
    out = (p.stdout + p.stderr).decode("utf-8", "replace")
    if check and p.returncode != 0:
        raise SystemExit("指令失敗:%s\n%s" % (" ".join(args), out))
    return p.returncode, out


def set_stage(target, stage):
    p = os.path.join(target, ".dev", "pipeline.json")
    io.open(p, "w", encoding="utf-8", newline="\n").write(
        json.dumps({"current_stage": stage, "feature": "verify",
                    "ticket_id": None, "updated": ""}, ensure_ascii=False, indent=2) + "\n")


def write(target, rel_path, text):
    dst = os.path.join(target, rel_path.replace("/", os.sep))
    os.makedirs(os.path.dirname(dst) or target, exist_ok=True)
    io.open(dst, "w", encoding="utf-8", newline="\n").write(text)


# ── 情境:每個都把 repo 佈置成「這條規則應該要擋」的狀態 ──────────────────

def scenario_r1(target):
    """規格書夾程式碼。"""
    set_stage(target, "spec")
    write(target, ".scratch/verify/spec.md",
          "## 問題\n\n```python\nprint(1)\n```\n")


def scenario_r2(target):
    """停在前置站卻要提交原始碼。"""
    set_stage(target, "spec")
    write(target, "verify_probe.py", "x = 1\n")


def scenario_r3(target):
    """在可寫站寫原始碼,但沒有對應測試檔。"""
    set_stage(target, "implement")
    write(target, "verify_probe.py", "x = 1\n")


def scenario_r4(target):
    """鏡像與正典不一致 —— 從鏡像刪掉一個檔案。"""
    set_stage(target, "implement")
    victim = os.path.join(target, ".claude", "skills", "tdd", "SKILL.md")
    if os.path.exists(victim):
        os.remove(victim)
    write(target, "docs/adr/verify-trigger.md", "觸發一次 commit 用\n")


def scenario_r5(target):
    """正典 code-review 缺第三軸掛載點 —— patch 沒重套的樣子。"""
    set_stage(target, "implement")
    canon = os.path.join(target, ".agents", "skills", "code-review", "SKILL.md")
    body = io.open(canon, encoding="utf-8").read()
    io.open(canon, "w", encoding="utf-8", newline="\n").write(
        body.replace("Data Integrity", "資料完整性"))
    write(target, "docs/adr/verify-trigger.md", "觸發一次 commit 用\n")


def scenario_r6(target):
    """往豁免清單裡塞一筆不在 go-live 樹裡的路徑。"""
    set_stage(target, "implement")
    lst = os.path.join(target, ".agents", "legacy-no-redlight.txt")
    with io.open(lst, "a", encoding="utf-8", newline="\n") as f:
        f.write("not/in/the/tree.py\n")


def scenario_r8(target):
    """生產程式碼 import research/ —— R8 擋(在 implement 站,避免被 R2 範圍先擋)。

    R8 在 R3 之前判,所以即使沒有測試檔也是 R8 先觸發,不會被 R3 搶走。
    """
    set_stage(target, "implement")
    write(target, "prod_module.py", "from research import explore\nx = 1\n")


def scenario_r7(target):
    """R7 是**前哨規則**,不是 commit 規則 —— 它擋的是工具呼叫,不是 staged 檔案。

    所以它的情境不走 git commit,而是直接問述詞。這是規則之間**合法的形狀差異**:
    有些規則管檔案內容(commit 時可驗),有些管工具呼叫(只有前哨看得到)。
    情境表因此不是「每條規則都用同一種方式觸發」,而是「每條規則都被觸發過一次」。
    """
    return "predicate"


SCENARIOS = {
    "R1": scenario_r1,
    "R2": scenario_r2,
    "R3": scenario_r3,
    "R4": scenario_r4,
    "R5": scenario_r5,
    "R6": scenario_r6,
    "R7": scenario_r7,
    "R8": scenario_r8,
}


def load_target_gate(target):
    spec = importlib.util.spec_from_file_location(
        "target_gate", os.path.join(target, ".claude", "hooks", "gate.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def restore(target):
    """回到安裝後的乾淨狀態。**兩半,因為這個 repo 有兩半。**

    追蹤側由 git 還原;**被 .gitignore 忽略的鏡像目錄 git 碰不到**,要重建。

    `git clean -fd` 不帶 -x 仍然是對的:帶了會把鏡像整個清掉。但**只靠它不夠** ——
    `scenario_r4` 刪的是鏡像**裡面**的一個檔,而 `git reset --hard` 與
    `git clean -fd` 都管不到被忽略的路徑,那個刪除因此永久留著(票 56)。
    舊註解只寫了「鏡像被整個清掉」那一種殘缺,漏掉「鏡像內被刪一個檔」那一種,
    而後者正是本檔自己的情境造的。

    後果不是抽象的:R4 之後每一條走 commit 的情境(R5 / R6 / R8)都在一個帶著
    R4 違規的 repo 上跑,於是 `run_scenario` 那個連言裡的 `rc != 0` 一半**由殘留
    白送**,真正在做事的只剩 `"[Rx]" in out`。讀起來在驗兩件事,實際只驗一件。

    **重建而不是 `-x`**:`-x` 刪掉鏡像之後不會再建回來,那是換一個更大的殘缺。
    `build_mirrors` 從正典 rmtree + copytree,兩個鏡像一起回來。

    **順序不能反**:先 `git reset` 讓正典回到 HEAD,再從正典重建鏡像 ——
    反過來的話,`scenario_r5` 改過的正典會被複製進鏡像,乾淨狀態就不乾淨了。
    """
    sh(["git", "reset", "-q", "--hard", "HEAD"], target)
    sh(["git", "clean", "-qfd"], target)
    install.build_mirrors(target)


def run_scenario(target, code):
    marker = SCENARIOS[code](target)
    if marker == "predicate":
        # 前哨規則:直接問述詞。走 commit 驗不到它 —— 它管的是工具呼叫。
        gate = load_target_gate(target)
        msg = gate.bash_write_violation("echo x > 偷偷寫進去.txt")
        return bool(msg and "[%s]" % code in msg), (msg or "(述詞放行了)")
    sh(["git", "add", "-A"], target)
    rc, out = sh(["git", "commit", "-m", "verify %s" % code], target, check=False)
    restore(target)
    blocked = rc != 0 and ("[%s]" % code in out or "[%s/" % code in out)
    return blocked, out


def main(workdir):
    target = os.path.abspath(os.path.join(workdir, "verify-gates-repo"))
    if os.path.exists(target):
        # Windows 的 git object 檔是唯讀的,直接 rmtree 會 PermissionError。
        # 清不掉舊的就會在上一輪的殘骸上跑,失敗原因會變成上一輪的狀態。
        def _force(func, path, _exc):
            os.chmod(path, 0o600)
            func(path)
        shutil.rmtree(target, onerror=_force)

    print("=== 真實安裝(不是簡化版)===")
    install.main(target)

    # 安裝器預設值(F-062):這兩項少任何一個,新 repo 的第一個秘密就沒人守。
    # 負控實測過:HOOK 沒接 leak_scan 時,含真 key 的 commit 直接成功。
    hook_body = io.open(os.path.join(target, ".git", "hooks", "pre-commit"),
                        encoding="utf-8").read()
    ignore_body = io.open(os.path.join(target, ".gitignore"), encoding="utf-8").read()
    defaults_bad = []
    if "leak_scan.py" not in hook_body:
        defaults_bad.append("pre-commit 沒接 leak_scan(洩漏 commit 會直接成功)")
    if ".env" not in ignore_body.splitlines():
        defaults_bad.append(".gitignore 沒守 .env")
    if defaults_bad:
        raise SystemExit("\n=== 安裝器預設值缺陷 ===\n"
                         + "".join("    %s\n" % b for b in defaults_bad))
    print("\n=== 安裝器預設值(F-062)===")
    print("    pre-commit 已接 leak_scan ✓")
    print("    .gitignore 已守 .env 家族與金鑰檔 ✓")

    gate = load_target_gate(target)
    codes = sorted(gate.rule_codes(), key=lambda c: int(c[1:]))
    print("\n=== 規則清單(從 gate.py 的定義列舉,不是對照表)===")
    print("    %s" % " ".join(codes))

    missing = [c for c in codes if c not in SCENARIOS]
    if missing:
        raise SystemExit(
            "\n這些規則沒有任何實測情境:%s\n"
            "規則存在但沒被證明擋得住,跟沒有規則的差別只在讀碼的人心裡。" % missing)

    print("\n=== 逐條實測(每條各擋一次)===")
    failures = []
    for code in codes:
        blocked, out = run_scenario(target, code)
        print("    %-4s %s" % (code, "擋下 ✓" if blocked else "沒擋到 ✗"))
        if not blocked:
            failures.append((code, out))

    if failures:
        print("\n=== 沒擋到的規則 ===")
        for code, out in failures:
            print("\n  %s —— 這條規則存在於定義裡,實測卻沒有擋下它的情境:" % code)
            for line in (out.strip().splitlines() or ["(沒有任何輸出)"]):
                print("      %s" % line)
        raise SystemExit("\n%d 條規則沒擋到:%s"
                         % (len(failures), " ".join(c for c, _ in failures)))

    print("\n=== 權威層偵測(只驗未安裝路徑)===")
    hook = os.path.join(target, ".git", "hooks", "pre-commit")
    body = io.open(hook, encoding="utf-8").read()

    os.remove(hook)
    gone, detail = gate.authoritative_layer(target)

    io.open(hook, "w", encoding="utf-8", newline="\n").write("#!/bin/sh\nnpm run lint\n")
    squatted, squat_detail = gate.authoritative_layer(target)

    io.open(hook, "w", encoding="utf-8", newline="\n").write(body)
    back, _ = gate.authoritative_layer(target)

    print("    hook 刪掉        -> %s(%s)" % ("偵測到沒裝 ✓" if not gone else "沒偵測到 ✗", detail))
    print("    別人的 hook 佔位 -> %s(%s)"
          % ("偵測到沒裝 ✓" if not squatted else "沒偵測到 ✗", squat_detail))
    print("    裝回去           -> %s" % ("偵測到已裝 ✓" if back else "仍說沒裝 ✗"))
    if gone or squatted or not back:
        raise SystemExit("權威層偵測不準 —— 沒裝的時候不會叫,那一層就是靜默缺席的。")

    print("\n    未安裝時會說的話:")
    for line in gate.not_installed_notice(detail).splitlines():
        print("      %s" % line)

    print("\n=== 框架自己的測試,在這個新 repo 裡跑一次 ===")
    # 「在宿主 repo 全綠」證明不了什麼 —— 它本來就綠。要驗的是**換個環境也綠**:
    # 那是一個獨立的涵蓋維度(F-031)。框架測試若把宿主的特徵寫進斷言,
    # 新專案第一次跑就看到與自己無關的紅,人學到的是「這套測試本來就紅」,
    # 之後真的紅也不會被當一回事 —— 壞掉的訊號比沒有訊號糟。
    rc, out = sh([sys.executable, "-m", "pytest", "tests/", "-q"], target, check=False)
    tail = [l for l in out.strip().splitlines() if l.strip()][-1:]
    print("    %s" % (tail[0] if tail else "(沒有輸出)"))
    if rc != 0:
        print("\n    在新 repo 裡紅的:")
        for line in out.splitlines():
            if line.startswith("FAILED") or line.startswith("ERROR"):
                print("      %s" % line)
        raise SystemExit(
            "框架測試在新 repo 裡不是全綠 —— 那些紅與新專案無關,"
            "會訓練人忽略訊號。框架測試只能斷言框架的性質。")

    print("\n全部 %d 條規則各擋下一次,權威層偵測正常,框架測試在新 repo 全綠。"
          "\n安裝位置:%s" % (len(codes), target))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("用法:python .claude/portable/verify_gates.py <暫存目錄>")
    main(sys.argv[1])
