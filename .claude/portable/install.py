# -*- coding: utf-8 -*-
"""把六站閘門裝進另一個 repo。

用法:python .claude/portable/install.py <目標目錄>

**單一路徑,零分支。** 全新專案不是另一種情境,它只是「既有原始碼數為零」的特例:
同一條路徑跑完會產出一份空的豁免清單。為空 repo 開第二條分支的話,
較少被走到的那條就是下一個 F-009(規則存在但沒被走過)。

安裝**一律建立 commit**:go-live sha 必須指向一個真的存在的 commit,
而安裝框架本來就是一次變更 —— 既有專案也該有那個 commit,空 repo 只是它的第一個。

裝 skill 是**安裝的一部分**,不是前置條件。當前置條件的話,漏做時 R4/R5
靜默不可驗 —— 跟權威層那個缺口同型。

本檔在票 01 宣告為 Untested by decision(接縫 S5):
它由空 repo 的端到端實測完整涵蓋,不另寫單元測試。
"""

import io
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import claude_md  # noqa: E402
import manifest  # noqa: E402  (同目錄,安裝器與標記表是一組的)

HOOK = ("#!/bin/sh\n"
        "# 六站閘門 — 權威判定。邏輯不在這裡,只呼叫共用的 gate.py。\n"
        'exec python "$(git rev-parse --show-toplevel)/.claude/hooks/gate.py" --pre-commit\n')


def run(args, cwd, check=True):
    p = subprocess.run(args, cwd=cwd, capture_output=True)
    out = (p.stdout + p.stderr).decode("utf-8", "replace")
    if check and p.returncode != 0:
        raise SystemExit("指令失敗(%s):%s\n%s" % (p.returncode, " ".join(args), out))
    return p.returncode, out


def source_files():
    """來源檔案集合 —— **含未追蹤但沒被 ignore 的檔案**。

    只取 `git ls-files` 的話,還沒 commit 的框架檔會**靜默漏帶**:
    安裝照樣成功、閘門照樣擋、輸出全綠,而裝出來的框架少了安裝器本身。
    實際發生過(第一次端到端就中):manifest.py / install.py / test_manifest.py
    三個都還沒進版控,於是新 repo 拿到一套裝不動下一個專案的框架。

    往「帶」的方向倒:多帶進來的暫存檔是吵鬧的(看得見、刪得掉),
    漏帶是靜默的。未追蹤的會在安裝輸出裡單獨列出來。
    """
    _, tracked = run(["git", "ls-files"], SRC_ROOT)
    _, untracked = run(["git", "ls-files", "--others", "--exclude-standard"], SRC_ROOT)
    t = [l.strip() for l in tracked.splitlines() if l.strip()]
    u = [l.strip() for l in untracked.splitlines() if l.strip()]
    return t + u, u


def classify(paths):
    """逐檔分類。回傳 (要複製的, 各標記的清單, 靠預設過關的)。"""
    buckets = {m: [] for m in manifest.MARKS}
    for p in paths:
        if manifest.in_scope(p):
            buckets[manifest.mark_for(p)].append(p)
    # 「在範圍內但沒標記」在前綴範圍下由構造為空 —— 真正會漏帶的是鄰居那一群
    return buckets, manifest.uncovered_neighbours(paths)


def copy_into(target, paths):
    for p in paths:
        dst = os.path.join(target, p.replace("/", os.sep))
        os.makedirs(os.path.dirname(dst) or target, exist_ok=True)
        shutil.copy2(os.path.join(SRC_ROOT, p.replace("/", os.sep)), dst)


def build_mirrors(target):
    """鏡像目錄。形態由環境決定(symlink / 硬連結 / 實體複製都出現過),
    這裡用實體複製 —— 它在任何檔案系統上都成立,而 R4 的實體目錄分支吃得下。"""
    canon = os.path.join(target, ".agents", "skills")
    if not os.path.isdir(canon):
        return []
    made = []
    for m in (os.path.join(target, ".claude", "skills"), os.path.join(target, "skills")):
        if os.path.exists(m):
            shutil.rmtree(m)
        shutil.copytree(canon, m)
        made.append(os.path.relpath(m, target).replace("\\", "/"))
    return made


def generate_state(target):
    """.dev/ 是這個 repo 的狀態與證據,不照抄。空證據是誠實的起點。"""
    dev = os.path.join(target, ".dev")
    os.makedirs(dev, exist_ok=True)
    io.open(os.path.join(dev, "pipeline.json"), "w", encoding="utf-8", newline="\n").write(
        json.dumps({"current_stage": "idle", "feature": None,
                    "ticket_id": None, "updated": ""}, ensure_ascii=False, indent=2) + "\n")
    for name in ("test-runs.jsonl", "gate-exemptions.jsonl"):
        io.open(os.path.join(dev, name), "w", encoding="utf-8", newline="\n").write("")

    # 框架自己會產生的垃圾。不寫這個的話,安裝當下跑驗證產生的 __pycache__
    # 會被第一個 commit 收進去 —— 不是複製過去的,是裝好之後自己長出來的。
    # 用附加不覆寫:目標可能已經有自己的 .gitignore。
    # CLAUDE.md 只帶框架段。專案段留在原地 —— 把某個專案的規矩裝進另一個專案,
    # agent 會照錯的規矩工作,而**那不會報錯**。汙染方向比乾淨要緊。
    src = os.path.join(SRC_ROOT, "CLAUDE.md")
    if os.path.exists(src):
        io.open(os.path.join(target, "CLAUDE.md"), "w",
                encoding="utf-8", newline="\n").write(
            claude_md.render_for_new_repo(io.open(src, encoding="utf-8").read()))

    ignore = os.path.join(target, ".gitignore")
    have = io.open(ignore, encoding="utf-8").read() if os.path.exists(ignore) else ""
    # **前導斜線是必要的,不是風格。** 寫成 `skills/` 的話 gitignore 會在
    # **任何深度**比對同名目錄 —— 於是 `.agents/skills/`(正典)也被排除,
    # 而 git 對 ignored 檔案依定義是靜默的。後果不是少幾個檔案:
    # 正典沒進版控 → 下一次從這個 repo 安裝時帶不走 skills → R5 在目標 repo 失敗。
    # 淨室測試抓到的,而且要「安裝出來的 repo 再安裝一次」才會現形。
    add = [p for p in ("__pycache__/", ".cache/", "/.claude/skills/", "/skills/")
           if p not in have]
    if add:
        with io.open(ignore, "a", encoding="utf-8", newline="\n") as f:
            f.write(("\n" if have and not have.endswith("\n") else "")
                    + "# 六站閘門會產生的東西(鏡像目錄由 skills 工具重建)\n"
                    + "\n".join(add) + "\n")


def install_hook(target):
    hooks = os.path.join(target, ".git", "hooks")
    os.makedirs(hooks, exist_ok=True)
    path = os.path.join(hooks, "pre-commit")
    io.open(path, "w", encoding="utf-8", newline="\n").write(HOOK)
    try:
        os.chmod(path, 0o755)
    except Exception:
        pass
    return path


def generate_legacy_list(target, go_live):
    """既有 .py 的紅燈豁免清單 —— 在目標 repo 重新產生,絕不照抄。

    照抄的話清單裡是**來源 repo 的路徑**,拿目標 repo 的 sha 去驗每一筆都不在樹裡,
    R6 全數判違規 —— 而且是在安裝之後才炸,看起來像框架壞了。
    """
    sys.path.insert(0, os.path.join(target, ".claude", "hooks"))
    for mod in ("gate",):
        sys.modules.pop(mod, None)
    spec_path = os.path.join(target, ".claude", "hooks", "gate.py")
    import importlib.util
    spec = importlib.util.spec_from_file_location("target_gate", spec_path)
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)

    _, out = run(["git", "ls-tree", "-r", "--name-only", go_live], target)
    files = sorted(p.strip() for p in out.splitlines()
                   if p.strip().endswith(".py") and g.is_source_path(p.strip()))
    dst = os.path.join(target, ".agents", "legacy-no-redlight.txt")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with io.open(dst, "w", encoding="utf-8", newline="\n") as f:
        f.write("# go-live: %s\n" % go_live)
        f.write("# 機制上線前就存在的 .py —— 只豁免 R3 的後半(紅燈紀錄),前半照常適用。\n")
        f.write("# 生成的,不是手寫的。只減不增(R6 驗每一筆都在上面那個 commit 的樹裡)。\n")
        for p in files:
            f.write(p + "\n")
    return files


def verify(target):
    """安裝時**強制**跑一次。不通過就不算安裝完成。

    票 01 只驗 R2(最薄的端到端);全規則機器列舉的版本是票 02。
    """
    rc, out = run(["python", os.path.join(".claude", "hooks", "gate.py"), "--pre-commit"],
                  target, check=False)
    if rc != 0:
        raise SystemExit("安裝後的權威判定不乾淨,安裝不算完成:\n%s" % out)

    # 權威層裝了沒 —— 這一層不進版控,漏裝是完全靜默的。安裝時是唯一被機器強制的時點。
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "installed_gate", os.path.join(target, ".claude", "hooks", "gate.py"))
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    ok, detail = g.authoritative_layer(target)
    if not ok:
        raise SystemExit("權威層沒裝起來,安裝不算完成:%s" % detail)

    # 停在**前置站**才問得到 R2 在提交時的那個問題。
    # idle 在提交時是故意放行的:實作做完站別本來就會走回 review / idle,
    # 拿寫入時的問題去問提交會擋掉每一次合法提交(docs/adr/0005)。
    # 這一點是端到端真的跑一次才會撞到的 —— 讀碼推不出來。
    pipeline = os.path.join(target, ".dev", "pipeline.json")
    saved = io.open(pipeline, encoding="utf-8").read()
    io.open(pipeline, "w", encoding="utf-8", newline="\n").write(
        json.dumps({"current_stage": "spec", "feature": "install-probe",
                    "ticket_id": None, "updated": ""}, ensure_ascii=False, indent=2) + "\n")

    probe = os.path.join(target, "probe_gate_is_alive.py")
    io.open(probe, "w", encoding="utf-8", newline="\n").write("x = 1\n")
    run(["git", "add", "probe_gate_is_alive.py"], target)
    rc, out = run(["git", "commit", "-m", "probe"], target, check=False)
    run(["git", "reset", "-q", "HEAD", "--", "probe_gate_is_alive.py"], target, check=False)
    os.remove(probe)
    io.open(pipeline, "w", encoding="utf-8", newline="\n").write(saved)
    if rc == 0 or "[R2" not in out:
        raise SystemExit("R2 沒有擋下前置站的原始碼提交 —— 閘門沒在守:\n%s" % out)
    return out


def main(target):
    target = os.path.abspath(target)
    os.makedirs(target, exist_ok=True)
    if not os.path.isdir(os.path.join(target, ".git")):
        run(["git", "init", "-q"], target)
        run(["git", "config", "user.email", "gate@local"], target)
        run(["git", "config", "user.name", "gate"], target)

    all_files, untracked = source_files()
    buckets, unmarked = classify(all_files)
    carried_untracked = [p for p in untracked if manifest.in_scope(p)]
    copy_into(target, buckets["copy"])
    mirrors = build_mirrors(target)
    generate_state(target)
    hook = install_hook(target)

    run(["git", "add", "-A"], target)
    run(["git", "commit", "-q", "--no-verify", "-m", "裝上六站閘門(框架安裝)"], target)
    _, go_live = run(["git", "rev-parse", "HEAD"], target)
    go_live = go_live.strip()

    legacy = generate_legacy_list(target, go_live)
    run(["git", "add", "-A"], target)
    run(["git", "commit", "-q", "--no-verify", "-m",
         "凍結既有 .py 的紅燈豁免清單(go-live %s)" % go_live[:7]], target)

    blocked = verify(target)

    print("裝好了:%s" % target)
    print("  複製      %d 個檔案" % len(buckets["copy"]))
    print("  產生      .dev/(狀態與空證據)、.agents/legacy-no-redlight.txt(%d 筆)" % len(legacy))
    print("  鏡像      %s" % (", ".join(mirrors) or "(無 skills 可鏡像)"))
    print("  權威層    %s" % os.path.relpath(hook, target).replace("\\", "/"))
    print("  go-live   %s" % go_live)
    if carried_untracked:
        print("\n帶過去了但來源 repo 還沒把它們進版控 —— 確認不是暫存檔:")
        for p in carried_untracked:
            print("    %s" % p)
    if buckets["ask"]:
        print("\n要人決定的(沒有帶過去):")
        for p in buckets["ask"]:
            print("    %s" % p)
    if buckets["skip"]:
        print("\n明確不帶的:")
        for p in buckets["skip"]:
            print("    %s" % p)
    if unmarked:
        print("\n跟框架檔住在同一個目錄、卻沒被帶過去的 —— 確認不是漏的:")
        for p in unmarked:
            print("    %s" % p)
    else:
        print("\n框架檔的鄰居全部都有歸屬。")
    print("\n閘門實測(R2 在 idle 站擋下原始碼提交):")
    for line in blocked.strip().splitlines():
        print("    %s" % line)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("用法:python .claude/portable/install.py <目標目錄>")
    main(sys.argv[1])
