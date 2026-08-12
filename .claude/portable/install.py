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
        "# 六站閘門 — 洩漏偵測 + 權威判定。邏輯不在這裡,只呼叫共用腳本。\n"
        "# 洩漏偵測在前:秘密一旦進了歷史,擋下 commit 是唯一便宜的時點。\n"
        "# 之前只接 gate.py —— 裝出來的 repo 對真 key 的 commit 完全放行(負控實測),\n"
        "# 而 F-055 說的就是洩漏 hook 不會自己跟過去。接線是安裝器的責任。\n"
        'root="$(git rev-parse --show-toplevel)"\n'
        'python "$root/.claude/portable/leak_scan.py" --staged || exit 1\n'
        'exec python "$root/.claude/hooks/gate.py" --pre-commit\n')

# 安裝出的 repo 的 .gitignore 必帶兩組:框架垃圾 + 秘密檔。
# 秘密那組是預設值問題:框架裝好的新專案,第一個放進去的秘密(.env)
# 原本不被任何規則守著 —— 不是使用者疏忽,是安裝器沒給預設。
GITIGNORE_FRAMEWORK = ("__pycache__/", ".cache/", "/.claude/skills/", "/skills/")
# 憑證副檔名用組裝而不寫死 —— 寫死的話 leak_scan 的通用 pattern 會擋住
# 本檔自己的 commit(防禦清單長得像洩漏)。與 tests/test_leak_scan.py 同一手法。
GITIGNORE_SECRETS = ((".env", ".env.*", "!.env.example", "credentials.json",
                      "service-account*.json")
                     + tuple("*." + ext for ext in ("pem", "pfx", "p12", "key")))


def run(args, cwd, check=True):
    p = subprocess.run(args, cwd=cwd, capture_output=True)
    out = (p.stdout + p.stderr).decode("utf-8", "replace")
    if check and p.returncode != 0:
        raise SystemExit("指令失敗(%s):%s\n%s" % (p.returncode, " ".join(args), out))
    return p.returncode, out


def git_paths(args, cwd, check=True):
    """凡是**拿 git 輸出當路徑**的地方都走這裡。`-z`(NUL 分隔),不是 splitlines。

    git 對非 ASCII 檔名預設回傳 C-quoted 路徑(`"\\345\\217\\260….py"`)。
    在這支的後果是**靜默漏帶**:中文檔名的檔案列不出來 → 不被複製到目標 repo,
    而少帶正是 F-030/F-031 那一族最難發現的失效。ls-tree 那邊還會把壞路徑寫進
    legacy 清單,R6 事後拿它去 `git cat-file` 查證必然失敗。

    不用 `core.quotePath=false`:它只解引號,檔名含換行或引號仍有歧義。
    另外走 stdout,不併 stderr —— 併起來的話警告訊息會被當成路徑。
    """
    p = subprocess.run(["git"] + args + ["-z"], cwd=cwd, capture_output=True)
    if check and p.returncode != 0:
        raise SystemExit("指令失敗(%s):git %s\n%s"
                         % (p.returncode, " ".join(args),
                            (p.stdout + p.stderr).decode("utf-8", "replace")))
    return [x for x in p.stdout.decode("utf-8", "replace").split("\0") if x.strip()]


def source_files():
    """來源檔案集合 —— **含未追蹤但沒被 ignore 的檔案**。

    只取 `git ls-files` 的話,還沒 commit 的框架檔會**靜默漏帶**:
    安裝照樣成功、閘門照樣擋、輸出全綠,而裝出來的框架少了安裝器本身。
    實際發生過(第一次端到端就中):manifest.py / install.py / test_manifest.py
    三個都還沒進版控,於是新 repo 拿到一套裝不動下一個專案的框架。

    往「帶」的方向倒:多帶進來的暫存檔是吵鬧的(看得見、刪得掉),
    漏帶是靜默的。未追蹤的會在安裝輸出裡單獨列出來。
    """
    t = git_paths(["ls-files"], SRC_ROOT)
    u = git_paths(["ls-files", "--others", "--exclude-standard"], SRC_ROOT)
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
    add = [p for p in GITIGNORE_FRAMEWORK if p not in have]
    if add:
        with io.open(ignore, "a", encoding="utf-8", newline="\n") as f:
            f.write(("\n" if have and not have.endswith("\n") else "")
                    + "# 六站閘門會產生的東西(鏡像目錄由 skills 工具重建)\n"
                    + "\n".join(add) + "\n")
        have = io.open(ignore, encoding="utf-8").read()
    secrets = [p for p in GITIGNORE_SECRETS if p not in have]
    if secrets:
        with io.open(ignore, "a", encoding="utf-8", newline="\n") as f:
            f.write(("\n" if have and not have.endswith("\n") else "")
                    + "# 秘密與憑證 —— 永不進版控(安裝器預設,見 F-062)\n"
                    + "\n".join(secrets) + "\n")


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

    files = sorted(p for p in git_paths(["ls-tree", "-r", "--name-only", go_live], target)
                   if p.endswith(".py") and g.is_source_path(p))
    dst = os.path.join(target, ".agents", "legacy-no-redlight.txt")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with io.open(dst, "w", encoding="utf-8", newline="\n") as f:
        f.write("# go-live: %s\n" % go_live)
        f.write("# 機制上線前就存在的 .py —— 豁免 R3 **整條**(兩半:紅燈紀錄 + 測試檔存在)。\n")
        f.write("# 生成的,不是手寫的。只減不增(R6 驗每一筆都在上面那個 commit 的樹裡)。\n")
        for p in files:
            f.write(p + "\n")
    return files


def write_decisions_pending(target, buckets, carried_untracked, unmarked):
    """把需要人決定的項目**寫成檔案**,不只印終端機。

    印出來沒人看等於沒列(F-036 的同一個病:訊號不落地就等於沒有訊號)。
    寫成 docs/decisions-pending.md —— 人回頭找得到,也進得了版控、能被 review。
    沒有任何待決項目時回 None(不留空檔案佔位)。
    """
    sections = []
    if buckets.get("ask"):
        sections.append(("需要你決定帶不帶(標記為 ask,安裝時沒有帶過去)",
                         buckets["ask"],
                         "這些檔案混著框架與專案兩種東西。看過內容後,"
                         "要嘛手動複製過來、要嘛確認不需要。"))
    if carried_untracked:
        sections.append(("帶過去了但來源 repo 還沒進版控 —— 確認不是暫存檔",
                         carried_untracked,
                         "來源是未追蹤檔,可能是還沒 commit 的框架檔,也可能是暫存物。"))
    if unmarked:
        sections.append(("跟框架檔住在同一個目錄、卻沒被帶過去 —— 確認不是漏的",
                         unmarked,
                         "少帶是靜默的(F-030/F-031)。逐一確認這些是專案自己的、不是漏掉的框架檔。"))
    if not sections:
        return None

    path = os.path.join(target, "docs", "decisions-pending.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lines = ["# 安裝待決定項目\n",
             "由 install.py 產生。**這是這些決定的落地處,不是終端機。**",
             "處理完一項就把它從這裡刪掉;清空了就代表安裝的人工部分做完了。\n"]
    for title, items, note in sections:
        lines.append("## %s\n" % title)
        lines.append("%s\n" % note)
        for it in sorted(items):
            lines.append("- [ ] `%s`" % it)
        lines.append("")
    io.open(path, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    return path


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


def refuse_if_dirty(target):
    """既有 repo 的 working tree 不乾淨 → 拒絕安裝並列出變更。

    **「安裝器假設 repo 乾淨」是個沒寫出來的前置條件。**
    install 隨後會 `git add -A && git commit` 生成 go-live —— 在乾淨 repo 無害,
    在髒 repo 會把使用者未提交的工作**全部掃進**框架安裝 commit(難以復原,
    而且 submodule / WIP 都會被吞)。同一行程式碼的破壞性取決於落地環境(friction)。
    把這個前置條件從假設變成機器檢查:髒就停,讓機器擋而不是靠人擋。
    """
    if not os.path.isdir(os.path.join(target, ".git")):
        return  # 全新 / 非 git 目錄:沒有既有工作可吞
    # --ignore-submodules=dirty:submodule 的**內部**未提交變更(status 的 ` m`)
    # 住在 submodule 自己的 index,父 repo 的 `git add -A` 碰不到、吞不走 ——
    # 它不是這道檢查要防的危險。**指標移動**(` M`)才會被 add -A 提交進安裝 commit,
    # 那個仍會被抓到。把「髒」定義成「add -A 吞得走的東西」,而不是 status 的預設髒。
    # 這裡的路徑是**要給人看的**(「你的工作區有這些未提交變更」)——
    # C-quoted 的話使用者認不出自己的檔案,所以同樣走 -z。
    changes = git_paths(["status", "--porcelain", "--ignore-submodules=dirty"],
                        target, check=False)
    if changes:
        listed = "\n".join("    " + c for c in changes[:20])
        more = ("\n    …(還有 %d 個)" % (len(changes) - 20)) if len(changes) > 20 else ""
        raise SystemExit(
            "拒絕安裝:目標 repo 的 working tree 不乾淨(%d 個未提交變更)。\n"
            "install 會 git add -A && commit 生成 go-live —— 那會把下面這些\n"
            "未提交的工作全部掃進框架安裝 commit,難以復原。\n"
            "先 commit 或 stash 這些變更,再重跑安裝:\n%s%s"
            % (len(changes), listed, more))


def main(target):
    target = os.path.abspath(target)
    os.makedirs(target, exist_ok=True)
    refuse_if_dirty(target)
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
    pending = write_decisions_pending(target, buckets, carried_untracked, unmarked)

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
    # ask / 未涵蓋鄰居 / 未進版控 —— **落地成檔案**,不只印終端機。
    # 印出來沒人看等於沒列;寫成 decisions-pending.md,人回頭找得到,也進得了版控。
    if pending:
        print("\n要人決定的項目已寫進:%s" % os.path.relpath(pending, target).replace("\\", "/"))
        print("    (別只看終端機 —— 那份檔案是這些決定的落地處)")
    else:
        print("\n沒有待決定項目。")
    print("\n閘門實測(R2 在 idle 站擋下原始碼提交):")
    for line in blocked.strip().splitlines():
        print("    %s" % line)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("用法:python .claude/portable/install.py <目標目錄>")
    main(sys.argv[1])
