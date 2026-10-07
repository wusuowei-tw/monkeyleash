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

import contextlib
import importlib.util
import io
import re
import json
import os
import shutil
import stat
import subprocess
import sys
import types
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import install  # noqa: E402
import friction_heading  # noqa: E402  (發號標題判準,與 sync 同一份)


def _out(text):
    """輸出走 **utf-8 位元組**,不走 `print`(票 62)。

    `print` 用主控台的編碼。Windows 的 cp950 編不出 `✓` / `✗` / `≥` / `⚠`,
    而那不是亂碼 —— 是 `UnicodeEncodeError` 未捕捉、**行程當場死掉**。
    這支工具是淨室驗證,**本機唯一涵蓋「安裝後形態」的東西**;
    它死掉時壞的不是功能,是**證據的產生能力**,而那種壞法不會讓任何測試變紅。
    (實測:重導向到管線也一樣炸 —— Python 對管線用的仍是 locale 編碼,
    所以「跑得完」與「跑得完且看得到」在這裡是同一件事,兩邊都不成立。)

    **寫法與 `sync.py` / `ledger_verify.py` 現有的一致**,不是新發明的。

    `sys.stdout.flush()` 不是裝飾:本檔仍有大量 cp950 安全的 `print`,
    它們走文字層的緩衝,而這裡直接寫二進位層 —— 不先 flush 的話
    **兩層的輸出會交錯**,而一份順序錯亂的驗收報告比沒有報告更難讀。
    """
    sys.stdout.flush()
    sys.stdout.buffer.write((text + "\n").encode("utf-8"))
    sys.stdout.buffer.flush()


# 底下三個 `_report_*` **只排版,不判定** —— 傳進來的布林值都是算好的。
# 抽出來的唯一理由是**可測**:原本它們長在 `main()` 裡,而 `main()` 會真的
# 裝一個 repo 再跑一次巢狀 pytest,不可能在單元測試裡呼叫。
# 判定留在 `main()`,本票一行都沒動。

def gitignore_gaps(body):
    """安裝出來的 `.gitignore` **少了哪幾條**(票 78 裁決 B)。

    **枚舉,不抽查。** `GITIGNORE_FRAMEWORK` 與 `GITIGNORE_SECRETS` 是
    **封閉且可窮舉**的集合,而 `CLAUDE.md` 常駐檢查項逐字:
    **封閉且可窮舉時,枚舉勝過比對 —— 比對的漏是未知的,枚舉的漏是不存在的。**

    舊斷言只問 `.env` **一項**,而且只在安裝當下跑一次;其餘十幾條零護欄。

    **行精確**(strip 後整行相等),與 `install.py` 的查重同一個判準 ——
    子字串會讓一個「只有註解、沒有防護」的 `.gitignore` 報全過,
    而那正是本票要修的安裝器缺陷的**驗收側版本**。
    **兩邊同時瞎掉的話,缺陷不會有任何訊號。**

    ## 這條驗的是【產物 vs 規格】,不是恆真檢查

    比的是**安裝出來的檔案** vs **安裝器自己的常數**。常數是規格、檔案是產物,
    而本票的缺陷正是「產物沒跟上規格」。
    **但它驗不到「規格本身縮水了」** —— 那一面由 `tests/test_install.py` 的
    `test_gitignore_secrets_cover_common_shapes` 與 `test_framework_ignores_unchanged`
    釘著。兩面分工,寫在這裡免得下一個人以為這一條涵蓋了全部。
    """
    lines = set(l.strip() for l in body.splitlines())
    return [p for p in list(install.GITIGNORE_FRAMEWORK) + list(install.GITIGNORE_SECRETS)
            if p not in lines]


def _report_installer_defaults(n_ignore):
    _out("    pre-commit 已接 leak_scan ✓")
    # 印出**條數**而不只是一句「已守」—— 一個「已守 ✓」在清單縮到剩一條時
    # 看起來完全一樣,而那正是本票在修的那種靜默。
    _out("    .gitignore 兩組清單逐條都在(%d 條)✓" % n_ignore)


def _report_rule_result(code, blocked):
    _out("    %-4s %s" % (code, "擋下 ✓" if blocked else "沒擋到 ✗"))


def _report_authority_probe(gone, detail, squatted, squat_detail, back):
    _out("    hook 刪掉        -> %s(%s)"
         % ("偵測到沒裝 ✓" if not gone else "沒偵測到 ✗", detail))
    _out("    別人的 hook 佔位 -> %s(%s)"
         % ("偵測到沒裝 ✓" if not squatted else "沒偵測到 ✗", squat_detail))
    _out("    裝回去           -> %s" % ("偵測到已裝 ✓" if back else "仍說沒裝 ✗"))


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


def scenario_r9(target):
    """在 friction log 末尾追加一個**已經存在的號**(票 83)。

    取「已存在的號」而不是寫死 `F-001`:每個安裝的 repo 用自己的前綴
    (`TSI-`、`TSA-`…),寫死上游的前綴會讓這個情境在下游**永遠觸發不了**,
    而它仍然會印「擋下 OK」—— 那是最糟的一種綠(F-023 家族)。
    取不到號就明說取不到,不假裝驗過。
    """
    log = os.path.join(target, "docs", "agents", "friction-log.md")
    existing = None
    with io.open(log, encoding="utf-8") as f:
        for line in f:
            # framework-updates/98:本行原本自帶一份與 `gate.py:1283` **逐字相同**
            # 的正則 —— portable 這一側因此有兩份字面(另一份在 sync.py)。
            # 改用共用的那一份,portable 側 2 -> 1。
            m = friction_heading.HEADING.match(line)
            if m:
                existing = m.group(1)
                break
    if not existing:
        raise SystemExit(
            "\n[R9 情境] %s 裡找不到任何發號標題 —— 造不出撞號情境。\n"
            "這不是通過,是**驗不到**:沒有號可以複製,就沒有東西可以撞。" % log)
    with io.open(log, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n## %s 情境造出來的撞號(verify_gates)\n" % existing)


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


# ── 票 146 3g:淨室家目錄隔離(G-1)與 R10 情境(G-3)────────────────────────
#
# 安裝、情境子程序、直接載入的目標 gate 一律用同一個隔離家目錄;真實使用者層不讀不寫。
# Windows 的 expanduser 只看 USERPROFILE,POSIX 看 HOME —— 兩個都設。
# 清理與寫入都要求**本輪 context 註冊的那一個 iso**:marker 檔單獨存在不足以授權(3g 五處閉合第 3 點)。

ISOLATED_HOME_DIRNAME = "home"
ISOLATION_MARKER = ".verify-gates-isolated"
SCENARIO_TRIGGER_R10 = "docs/adr/verify-trigger-r10.md"
_ACTIVE_ISOLATION = None
_HOME_VARS = ("USERPROFILE", "HOME")


def current_isolation():
    return _ACTIVE_ISOLATION


def _lkind(path):
    """lstat 的型別:"absent" / "symlink" / "dir" / "file" / "other";lstat 失敗(非不存在)⇒ SystemExit。"""
    try:
        mode = os.lstat(path).st_mode
    except FileNotFoundError:
        return "absent"
    except OSError as e:
        raise SystemExit("隔離家目錄:lstat 失敗(%s):%s" % (type(e).__name__, path))
    if stat.S_ISLNK(mode):
        return "symlink"
    if stat.S_ISDIR(mode):
        return "dir"
    if stat.S_ISREG(mode):
        return "file"
    return "other"


_FILE_ATTRIBUTE_REPARSE_POINT = 0x400


def _is_reparse(path):
    """路徑本身是不是連結 / reparse point(3h N-3)。POSIX:`os.path.islink`;Windows:另看 lstat 的
    `st_file_attributes` 是否含 FILE_ATTRIBUTE_REPARSE_POINT —— junction 的 lstat 型別是目錄、`islink` 為假,
    只看 `_lkind` 會把它當成一般目錄。不存在 ⇒ False;其他 lstat 失敗照常拋出(呼叫端視為失敗)。"""
    if os.path.islink(path):
        return True
    if os.name == "nt":
        try:
            st = os.lstat(path)
        except FileNotFoundError:
            return False
        return bool(getattr(st, "st_file_attributes", 0) & _FILE_ATTRIBUTE_REPARSE_POINT)
    return False


def _reparse_or_exit(path, what):
    try:
        bad = _is_reparse(path)
    except OSError as e:
        raise SystemExit("%s:lstat 失敗(%s):%s" % (what, type(e).__name__, path))
    if bad:
        raise SystemExit("%s 是連結或 reparse point(junction 等)—— 拒絕:%s" % (what, path))


@contextlib.contextmanager
def isolated_home(workdir):
    """把 USERPROFILE / HOME 指到 `<workdir>/home`(含空的 `.claude` 與本輪 marker),離開時精確還原。

    進入前任何一項預置物不對(home 是 symlink / 不是目錄 / 非空;`.claude` 同;marker 已存在)⇒ SystemExit,
    **什麼都不建**。不准巢狀。"""
    global _ACTIVE_ISOLATION
    if _ACTIVE_ISOLATION is not None:
        raise SystemExit("隔離家目錄不准巢狀進入(已有一個作用中的隔離)")
    workdir = os.path.abspath(workdir)
    home = os.path.join(workdir, ISOLATED_HOME_DIRNAME)
    claude_root = os.path.join(home, ".claude")
    marker = os.path.join(home, ISOLATION_MARKER)
    # N-3′:任何建立 / 寫入 / 改環境之前,已存在的 home、home/.claude、marker 是連結或 reparse point ⇒ 拒絕。
    k = _lkind(home)
    if k not in ("absent", "dir"):
        raise SystemExit("隔離家目錄的位置已有東西且不是目錄(%s):%s" % (k, home))
    if k != "absent":
        _reparse_or_exit(home, "隔離家目錄")
    if k == "dir" and os.listdir(home):
        raise SystemExit("隔離家目錄已存在且非空 —— 不清空既有內容:%s" % home)
    k = _lkind(claude_root)
    if k not in ("absent", "dir"):
        raise SystemExit("隔離 .claude 的位置已有東西且不是目錄(%s):%s" % (k, claude_root))
    if k != "absent":
        _reparse_or_exit(claude_root, "隔離 .claude")
    if k == "dir" and os.listdir(claude_root):
        raise SystemExit("隔離 .claude 已存在且非空:%s" % claude_root)
    if _lkind(marker) != "absent":
        raise SystemExit("隔離 marker 已存在 —— 不是本輪建立的家目錄:%s" % marker)
    os.makedirs(claude_root, exist_ok=True)
    token = uuid.uuid4().hex
    with io.open(marker, "w", encoding="utf-8", newline="\n") as f:
        f.write(token)
    saved = dict((v, (v in os.environ, os.environ.get(v))) for v in _HOME_VARS)
    try:
        for v in _HOME_VARS:
            os.environ[v] = home
        iso = types.SimpleNamespace(workdir=workdir, home=home, claude_root=claude_root,
                                    marker=marker, token=token)
        _ACTIVE_ISOLATION = iso
        yield iso
    finally:
        for v, (present, value) in saved.items():
            if present:
                os.environ[v] = value
            else:
                os.environ.pop(v, None)
        _ACTIVE_ISOLATION = None


def _require_isolation(iso):
    """iso 必須是本輪作用中的那一個,且家目錄 / marker / 環境都還是進入時的樣子;任一不成立 ⇒ SystemExit。"""
    if iso is None or iso is not _ACTIVE_ISOLATION:
        raise SystemExit("沒有作用中的隔離家目錄(或不是本輪 context 建立的)—— 拒絕碰家目錄")
    root = os.path.normcase(os.path.realpath(iso.workdir))
    real_home = os.path.normcase(os.path.realpath(iso.home))
    if not real_home.startswith(root.rstrip(os.sep) + os.sep):
        raise SystemExit("隔離家目錄解析後不在 workdir 之下:%s" % iso.home)
    # N-3:claude_root 的解析位置必須正是 realpath(home)/.claude;三者任一是連結 / reparse point ⇒ 拒絕。
    if os.path.normcase(os.path.realpath(iso.claude_root)) != os.path.normcase(
            os.path.join(os.path.realpath(iso.home), ".claude")):
        raise SystemExit("隔離 .claude 解析後不是 <home>/.claude:%s" % iso.claude_root)
    for p, what in ((iso.home, "隔離家目錄"), (iso.claude_root, "隔離 .claude"), (iso.marker, "隔離 marker")):
        _reparse_or_exit(p, what)
    for p in (iso.home, iso.claude_root):
        if _lkind(p) != "dir":
            raise SystemExit("隔離路徑不是非 symlink 的目錄:%s" % p)
    if _lkind(iso.marker) != "file":
        raise SystemExit("隔離 marker 不是非 symlink 的一般檔:%s" % iso.marker)
    with io.open(iso.marker, encoding="utf-8") as f:
        if f.read() != iso.token:
            raise SystemExit("隔離 marker 內容不是本輪 token:%s" % iso.marker)
    if os.path.normcase(os.path.abspath(os.path.expanduser("~"))) != os.path.normcase(os.path.abspath(iso.home)):
        raise SystemExit("expanduser(\"~\") 不是隔離家目錄 —— 環境被改過")


def restore_user_layer(iso):
    """清空隔離 `.claude` 的內容(保留空目錄)。先驗隔離,再全樹預檢;任一不過就停,什麼都不刪。

    預檢(3h N-3):topdown、不追連結地走訪;每一層先對 dirnames 與 filenames 每個項目 lstat(失敗 ⇒ 停),
    任一項目是連結 / reparse point ⇒ 停;進下一層之前原地剪掉不得走訪的 dirnames,使走訪不進入它們。
    列舉失敗(onerror)收集後立即視為失敗。預檢全過才刪。"""
    _require_isolation(iso)
    errors = []
    for dirpath, dirnames, filenames in os.walk(iso.claude_root, topdown=True, followlinks=False,
                                                onerror=errors.append):
        if errors:
            break
        keep = []
        for name in list(dirnames) + list(filenames):
            p = os.path.join(dirpath, name)
            try:
                st = os.lstat(p)
            except OSError as e:
                raise SystemExit("隔離清理預檢:lstat 失敗(%s):%s —— 未刪除任何內容" % (type(e).__name__, p))
            try:
                bad = _is_reparse(p)
            except OSError as e:
                raise SystemExit("隔離清理預檢:lstat 失敗(%s):%s —— 未刪除任何內容" % (type(e).__name__, p))
            if bad:
                raise SystemExit("隔離清理預檢:%s 是連結或 reparse point —— 未刪除任何內容" % p)
            if name in dirnames and stat.S_ISDIR(st.st_mode):
                keep.append(name)
        dirnames[:] = keep
    if errors:
        raise SystemExit("隔離清理預檢:列舉失敗(%s)—— 未刪除任何內容" % type(errors[0]).__name__)
    for name in os.listdir(iso.claude_root):
        p = os.path.join(iso.claude_root, name)
        if _lkind(p) == "dir":
            shutil.rmtree(p)
        else:
            os.remove(p)


def scenario_r10(target):
    """隔離 `.claude/skills/synced` 放一個合法 bucket + marker(兩筆),安裝器的空 inventory 沒有登記 ⇒ 額外 2。"""
    iso = current_isolation()
    _require_isolation(iso)
    synced = os.path.join(iso.claude_root, "skills", "synced")
    os.makedirs(os.path.join(synced, "vgbucket"))
    with io.open(os.path.join(synced, "vgbucket", "SKILL.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# verify_gates r10\n")
    with io.open(os.path.join(synced, ".bucket-vgbucket"), "w", encoding="utf-8", newline="\n") as f:
        f.write("vgbucket\n")
    set_stage(target, "implement")
    # N-4:情境 trigger 與正控不同 ⇒ 正控提交之後,情境 commit 的 staged 仍非空。
    write(target, SCENARIO_TRIGGER_R10, "觸發一次 R10 情境 commit 用(與正控 trigger 不同)\n")


def precontrol_r10(target):
    """R10 的乾淨正控:同一佈置、家目錄不放任何東西 ⇒ 必須放行。"""
    set_stage(target, "implement")
    write(target, "docs/adr/verify-trigger.md", "觸發一次 commit 用\n")


SCENARIOS = {
    "R1": scenario_r1,
    "R2": scenario_r2,
    "R3": scenario_r3,
    "R4": scenario_r4,
    "R5": scenario_r5,
    "R6": scenario_r6,
    "R7": scenario_r7,
    "R8": scenario_r8,
    "R9": scenario_r9,
    "R10": scenario_r10,
}

# 有指定擋下路徑的規則:代號標記與原因**同時**出現才算擋到(G-3;補件裁決)。
# 不在這兩張表的規則沿用 `[code]` / `[code/` 判定。
EXPECTED_MARKER = {"R10": "[R10/fail-closed]"}
EXPECTED_REASON = {"R10": u"未受管入口：synced（額外 2"}
# 情境前先跑的正控:同一佈置在放入情境物之前必須放行,否則情境的擋下證明不了什麼。
PRECONTROL = {"R10": precontrol_r10}


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


# ── 票 145 Station 4g —— evidence policy 的淨室兩正三負(〈四十六〉46.4 第 4 點;規劃檔 S3g-0 P5)
#
# 接在「框架測試在新 repo 跑一次」之後。正一直接讀那一次留下的帳本;其餘四個各自從同一個
# 基準 commit(安裝 + 規則情境之後的 HEAD)出發,做完 `_ev_restore` 回到基準 ——
# 目標 repo 的 `.dev/` 是被追蹤的(安裝器不 ignore 它),不回到基準的話上一個情境的帳本與 commit
# 會留給下一個。
#
# 探針只收一支測試檔:已提交的 pyproject 以 `python_files` 把收集範圍定成探針那一支
# (那是宿主自己的已提交設定,不是窄選 —— consumer 鎖 `inipath` 與 blob,不看 `python_files` 的值)。
# 否則每個情境的固定指令都要把整套框架測試再跑兩次。
#
# 佈置用的 commit 以 `--no-verify` 提交,同 `install.main` 自己的兩個 commit(`install.py` 的 main):
# 這裡驗的是證據鏈,不是閘門;閘門由上面的規則情境各擋一次。

EV_PROBE = "tests/test_evidence_probe.py"
EV_RED = "def test_probe():\n    assert False\n"
EV_GREEN = "def test_probe():\n    assert True\n"
EV_PYPROJECT = ('[tool.pytest.ini_options]\n'
                'testpaths = ["tests"]\n'
                'python_files = ["test_evidence_probe.py"]\n')
FIXED_COMMAND = [sys.executable, "-X", "utf8", "-m", "pytest", "-q"]


def load_target_redlight(target):
    """每次重新載入(帳本是讀檔,模組本身不快取 run 事實;重新載入只是避免沿用上一個情境的模組狀態)。"""
    spec = importlib.util.spec_from_file_location(
        "target_redlight", os.path.join(target, ".claude", "hooks", "redlight.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _ev_status(target):
    """在子行程跑目標 repo 自己的 status.py,回傳 `{欄位: 值}`(值去掉 `(source: …)`)。"""
    _rc, out = sh([sys.executable, "-X", "utf8",
                   os.path.join(target, ".claude", "portable", "status.py"), "--root", target],
                  target, check=False)
    fields = {}
    for line in out.splitlines():
        key, sep, rest = line.partition(": ")
        if sep:
            fields[key.strip()] = rest.split("  (source:")[0].strip()
    return fields


def _ev_set_ticket(target, ticket):
    p = os.path.join(target, ".dev", "pipeline.json")
    io.open(p, "w", encoding="utf-8", newline="\n").write(
        json.dumps({"current_stage": "implement", "feature": "verify",
                    "ticket_id": ticket, "updated": ""}, ensure_ascii=False, indent=2) + "\n")


def _ev_matching_policy(target):
    """正二的 policy:值 = 當下環境 ∩ 框架能力邊界(規劃檔 P5)。不在邊界內的環境 ⇒ 對應欄位為空,
    正二會因此不成立 —— 那是正確的(那個環境本來就退不了紅),而失敗訊息會點名正二。"""
    from importlib import metadata
    rl = load_target_redlight(target)
    here = "%d.%d" % tuple(sys.version_info[:2])
    try:
        pytest_version = metadata.version("pytest")
    except Exception:
        pytest_version = None
    dists = []
    for name, version in rl.KNOWN_DISTS:
        try:
            if metadata.version(name) == version:
                dists.append([name, version])
        except Exception:
            pass
    return {"schema": rl.POLICY_SCHEMAS[0][0], "version": rl.POLICY_SCHEMAS[0][1],
            "config_file": rl.FRAMEWORK_CONFIG_FILES[0],
            "committed_overrides": [],
            "python_versions": [v for v in rl.KNOWN_PYTHON_VERSIONS if v == here],
            "pytest_versions": [v for v in rl.KNOWN_PYTEST_VERSIONS if v == pytest_version],
            "dists": dists}


def _ev_fixed_run(target, extra_env=None):
    env = dict(os.environ)
    env.pop("PYTEST_ADDOPTS", None)
    env.update(extra_env or {})
    p = subprocess.run(FIXED_COMMAND, cwd=target, capture_output=True, env=env)
    return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")


def _ev_red_then_green(target, ticket, commit_policy=True, dirty_policy=False, extra_env=None):
    """佈置 pyproject + 失敗的探針(+ policy)並提交 → 固定指令(紅)→ 修好探針、提交
    →(負二:policy 工作樹多一行)→ 固定指令(依 `extra_env`)。
    回傳 `(第一次 rc, 第二次 rc, 第二次的 file_coverage, status 欄位, 第二次輸出尾行)`。"""
    _ev_set_ticket(target, ticket)
    rl = load_target_redlight(target)
    policy_text = json.dumps(_ev_matching_policy(target), ensure_ascii=False, indent=2) + "\n"
    write(target, "pyproject.toml", EV_PYPROJECT)
    write(target, EV_PROBE, EV_RED)
    write(target, rl.POLICY_FILE, policy_text)
    tracked = ["pyproject.toml", EV_PROBE] + ([rl.POLICY_FILE] if commit_policy else [])
    sh(["git", "add"] + tracked, target)
    sh(["git", "commit", "-q", "--no-verify", "-m", "evidence %s: red probe" % ticket], target)
    rc1, _out1 = _ev_fixed_run(target)
    write(target, EV_PROBE, EV_GREEN)
    sh(["git", "add", EV_PROBE], target)
    sh(["git", "commit", "-q", "--no-verify", "-m", "evidence %s: fix probe" % ticket], target)
    if dirty_policy:
        write(target, rl.POLICY_FILE, policy_text + "\n")
    rc2, out2 = _ev_fixed_run(target, extra_env)
    runs = load_target_redlight(target).load_runs(target)
    cov = rl.file_coverage(runs[-1], EV_PROBE) if runs else "(沒有 run 事實)"
    tail = [l for l in out2.strip().splitlines() if l.strip()][-1:]
    return rc1, rc2, cov, _ev_status(target), (tail[0] if tail else "(沒有輸出)")


def _ev_verdict_line(fields, ticket, kind):
    return fields.get("tests %s under ticket %s" % (kind, ticket), "")


def ev_pos1_uninitialized(target, _base=None):
    """正一:安裝後不動 —— 框架測試全綠(由 main 的上一步保證);那一次 run 對框架測試檔的
    `file_coverage` 必須是 unknown,status 的 policy 行為「未初始化」。"""
    rl = load_target_redlight(target)
    runs = rl.load_runs(target)
    if not runs:
        return False, "淨室帳本沒有 run 事實 —— 框架測試那一次沒有留下 session"
    last = runs[-1]
    files = sorted(set(n.split("::", 1)[0] for n in last.get("collected") or []))
    if not files:
        return False, "最後一筆 session 沒有收集到任何檔"
    covs = dict((f, rl.file_coverage(last, f)) for f in files)
    not_unknown = sorted(f for f, c in covs.items() if c != "unknown")
    state = _ev_status(target).get("evidence policy")
    ok = not not_unknown and state == rl.POLICY_UNINITIALIZED
    return ok, "%d 個框架測試檔皆 unknown=%s;evidence policy: %s%s" % (
        len(files), not not_unknown, state,
        (";非 unknown 的檔:%s" % ", ".join(not_unknown)) if not_unknown else "")


def ev_pos2_initialized(target, _base=None):
    """正二:已提交且與環境相符的 policy ⇒ 紅 → 固定全套 → true → 合法退休(status 端到端)。"""
    ticket = "ev-pos2"
    rc1, rc2, cov, fields, tail = _ev_red_then_green(target, ticket)
    green = _ev_verdict_line(fields, ticket, "green")
    red = _ev_verdict_line(fields, ticket, "red")
    ok = (rc1 == 1 and rc2 == 0 and cov == "true"
          and EV_PROBE in green and EV_PROBE not in red
          and fields.get("evidence policy") == load_target_redlight(target).POLICY_VALID)
    return ok, "rc %s→%s;file_coverage=%s;red=%s;green=%s;evidence policy: %s;%s" % (
        rc1, rc2, cov, red, green, fields.get("evidence policy"), tail)


def _ev_negative(target, ticket, **kw):
    rc1, rc2, cov, fields, tail = _ev_red_then_green(target, ticket, **kw)
    red = _ev_verdict_line(fields, ticket, "red")
    green = _ev_verdict_line(fields, ticket, "green")
    ok = rc1 == 1 and rc2 == 0 and cov == "unknown" and EV_PROBE in red and EV_PROBE not in green
    return ok, "rc %s→%s;file_coverage=%s;red=%s;green=%s;evidence policy: %s;%s" % (
        rc1, rc2, cov, red, green, fields.get("evidence policy"), tail)


def ev_neg1_mismatch(target, _base=None):
    """負一:policy 與環境不符 —— 修好後那一次多一個 policy 未列的 override ⇒ unknown,紅仍在。"""
    return _ev_negative(target, "ev-neg1",
                        extra_env={"PYTEST_ADDOPTS": "-o python_functions=test"})


def ev_neg2_worktree_differs(target, _base=None):
    """負二:HEAD 有 policy、工作樹多一行(未 commit)⇒ unknown,紅仍在。"""
    return _ev_negative(target, "ev-neg2", dirty_policy=True)


def ev_neg3_worktree_only(target, _base=None):
    """負三:policy 只在工作樹、從未 commit ⇒ unknown,紅仍在。"""
    return _ev_negative(target, "ev-neg3", commit_policy=False)


# 鍵 ↔ 情境,比照 `SCENARIOS`。`tests/test_verify_gates.py` 斷言五個鍵都在。
EVIDENCE_SCENARIOS = {
    "pos1-uninitialized": ev_pos1_uninitialized,
    "pos2-initialized": ev_pos2_initialized,
    "neg1-mismatch": ev_neg1_mismatch,
    "neg2-worktree-differs": ev_neg2_worktree_differs,
    "neg3-worktree-only": ev_neg3_worktree_only,
}

EVIDENCE_LABELS = {
    "pos1-uninitialized": "正一 未初始化",
    "pos2-initialized": "正二 已初始化且相符",
    "neg1-mismatch": "負一 policy / 環境不符",
    "neg2-worktree-differs": "負二 HEAD 有、工作樹不同",
    "neg3-worktree-only": "負三 工作樹有、HEAD 沒有",
}


def _ev_restore(target, base):
    """回到證據情境的基準 commit(兩半,同 `restore`:追蹤側由 git、鏡像重建)。"""
    sh(["git", "reset", "-q", "--hard", base], target)
    sh(["git", "clean", "-qfd"], target)
    install.build_mirrors(target)


def run_evidence_scenarios(target):
    """依序跑五個情境;每個各印一行(不合併)。回傳失敗的 `[(鍵, 細節)]`。"""
    _rc, base = sh(["git", "rev-parse", "HEAD"], target)
    base = base.strip()
    failures = []
    for key in ("pos1-uninitialized", "pos2-initialized", "neg1-mismatch",
                "neg2-worktree-differs", "neg3-worktree-only"):
        try:
            ok, detail = EVIDENCE_SCENARIOS[key](target, base)
        except SystemExit as e:
            ok, detail = False, "情境執行失敗:%s" % e
        finally:
            if key != "pos1-uninitialized":
                _ev_restore(target, base)
        _out("    %-24s %s  %s" % (EVIDENCE_LABELS[key], "成立 ✓" if ok else "不成立 ✗", detail))
        if not ok:
            failures.append((key, detail))
    return failures


def run_scenario(target, code, iso=None):
    if code in PRECONTROL:
        PRECONTROL[code](target)
        sh(["git", "add", "-A"], target)
        rc, out = sh(["git", "commit", "-m", "verify %s precontrol" % code], target, check=False)
        if rc != 0:
            restore(target)
            return False, u"正控未放行：" + out
        restore(target)
    marker = SCENARIOS[code](target)
    if marker == "predicate":
        # 前哨規則:直接問述詞。走 commit 驗不到它 —— 它管的是工具呼叫。
        gate = load_target_gate(target)
        msg = gate.bash_write_violation("echo x > 偷偷寫進去.txt")
        return bool(msg and "[%s]" % code in msg), (msg or "(述詞放行了)")
    sh(["git", "add", "-A"], target)
    # N-4:staged 為空時 `git commit` 會以 nothing-to-commit 非零結束 —— 那個 rc 不是閘門給的,不得算擋下。
    # 這一步只排除那個假象;R10 是否擋下仍由 rc + marker + reason 三者共同判定(判定句不變)。
    _rc, staged = sh(["git", "diff", "--cached", "--name-only"], target)
    if not staged.strip():
        restore(target)
        if iso is not None:
            restore_user_layer(iso)
        return False, u"情境 staged 為空：" + code
    rc, out = sh(["git", "commit", "-m", "verify %s" % code], target, check=False)
    restore(target)
    if iso is not None:
        restore_user_layer(iso)
    if code in EXPECTED_MARKER:
        blocked = rc != 0 and EXPECTED_MARKER[code] in out and EXPECTED_REASON[code] in out
    else:
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

    # 票 146 G-1:安裝、規則情境、目標 gate 的載入、框架測試與 evidence 情境全在同一個隔離家目錄內 ——
    # 真實 `~/.claude` 不讀不寫,目標 gate / leak scanner 的模組層常數也不會先綁到真實家目錄。
    with isolated_home(workdir) as iso:
        _main_isolated(target, iso)


def _main_isolated(target, iso):
    _out("=== 真實安裝(不是簡化版)===")
    _out("    隔離家目錄:%s" % iso.home)
    # ⚠ `install.main()` 自己還有 21 個裸 `print` —— **不在票 62 範圍內**
    # (票面掃描的對象是這三支「證明別的東西是對的」的工具)。
    # 實測那 21 個沒有一個含 cp950 編不出的字,所以它不會炸;
    # 但它的輸出仍走文字層,**於是淨室的輸出在這一段仍是 locale 編碼**。
    # 登記在票 62 第二刀的票面上,不在這裡順手擴大範圍。
    install.main(target)

    # 安裝器預設值(F-062):這兩項少任何一個,新 repo 的第一個秘密就沒人守。
    # 負控實測過:HOOK 沒接 leak_scan 時,含真 key 的 commit 直接成功。
    hook_body = io.open(os.path.join(target, ".git", "hooks", "pre-commit"),
                        encoding="utf-8").read()
    ignore_body = io.open(os.path.join(target, ".gitignore"), encoding="utf-8").read()
    defaults_bad = []
    if "leak_scan.py" not in hook_body:
        defaults_bad.append("pre-commit 沒接 leak_scan(洩漏 commit 會直接成功)")
    # 票 78 裁決 B:~~只問 `.env` 一項~~ → **兩組清單逐條枚舉**。
    # 訊息列出**缺的是哪幾條** —— 一句「.gitignore 沒守」讓人得自己去比對兩份清單,
    # 而票 13 的判準是「說得出是哪一個前提沒滿足」。
    gaps = gitignore_gaps(ignore_body)
    if gaps:
        defaults_bad.append(".gitignore 少了 %d 條(逐條枚舉,不是抽查):%s"
                            % (len(gaps), "、".join(gaps)))
    if defaults_bad:
        raise SystemExit("\n=== 安裝器預設值缺陷 ===\n"
                         + "".join("    %s\n" % b for b in defaults_bad))
    _out("\n=== 安裝器預設值(F-062)===")
    _report_installer_defaults(
        len(install.GITIGNORE_FRAMEWORK) + len(install.GITIGNORE_SECRETS))

    gate = load_target_gate(target)
    codes = sorted(gate.rule_codes(), key=lambda c: int(c[1:]))
    _out("\n=== 規則清單(從 gate.py 的定義列舉,不是對照表)===")
    _out("    %s" % " ".join(codes))

    missing = [c for c in codes if c not in SCENARIOS]
    if missing:
        raise SystemExit(
            "\n這些規則沒有任何實測情境:%s\n"
            "規則存在但沒被證明擋得住,跟沒有規則的差別只在讀碼的人心裡。" % missing)

    _out("\n=== 逐條實測(每條各擋一次)===")
    failures = []
    for code in codes:
        blocked, out = run_scenario(target, code, iso=iso)
        _report_rule_result(code, blocked)
        if blocked and code in PRECONTROL:
            # 擋下的證明要連正控一起看:正控沒放行時 run_scenario 回 False,走不到這裡。
            _out(u"         正控放行 ✓(同一佈置、家目錄未放情境物)")
            for line in out.splitlines():
                if EXPECTED_MARKER[code] in line:
                    _out("         %s" % line.strip())
        if not blocked:
            failures.append((code, out))

    if failures:
        _out("\n=== 沒擋到的規則 ===")
        for code, out in failures:
            _out("\n  %s —— 這條規則存在於定義裡,實測卻沒有擋下它的情境:" % code)
            for line in (out.strip().splitlines() or ["(沒有任何輸出)"]):
                _out("      %s" % line)
        raise SystemExit("\n%d 條規則沒擋到:%s"
                         % (len(failures), " ".join(c for c, _ in failures)))

    _out("\n=== 權威層偵測(只驗未安裝路徑)===")
    hook = os.path.join(target, ".git", "hooks", "pre-commit")
    body = io.open(hook, encoding="utf-8").read()

    os.remove(hook)
    gone, detail = gate.authoritative_layer(target)

    io.open(hook, "w", encoding="utf-8", newline="\n").write("#!/bin/sh\nnpm run lint\n")
    squatted, squat_detail = gate.authoritative_layer(target)

    io.open(hook, "w", encoding="utf-8", newline="\n").write(body)
    back, _ = gate.authoritative_layer(target)

    _report_authority_probe(gone, detail, squatted, squat_detail, back)
    if gone or squatted or not back:
        raise SystemExit("權威層偵測不準 —— 沒裝的時候不會叫,那一層就是靜默缺席的。")

    _out("\n    未安裝時會說的話:")
    for line in gate.not_installed_notice(detail).splitlines():
        _out("      %s" % line)

    _out("\n=== 框架自己的測試,在這個新 repo 裡跑一次 ===")
    # 「在宿主 repo 全綠」證明不了什麼 —— 它本來就綠。要驗的是**換個環境也綠**:
    # 那是一個獨立的涵蓋維度(F-031)。框架測試若把宿主的特徵寫進斷言,
    # 新專案第一次跑就看到與自己無關的紅,人學到的是「這套測試本來就紅」,
    # 之後真的紅也不會被當一回事 —— 壞掉的訊號比沒有訊號糟。
    rc, out = sh([sys.executable, "-m", "pytest", "tests/", "-q"], target, check=False)
    tail = [l for l in out.strip().splitlines() if l.strip()][-1:]
    _out("    %s" % (tail[0] if tail else "(沒有輸出)"))
    if rc != 0:
        _out("\n    在新 repo 裡紅的:")
        for line in out.splitlines():
            if line.startswith("FAILED") or line.startswith("ERROR"):
                _out("      %s" % line)
        raise SystemExit(
            "框架測試在新 repo 裡不是全綠 —— 那些紅與新專案無關,"
            "會訓練人忽略訊號。框架測試只能斷言框架的性質。")

    # 票 145 Station 4g:evidence policy 的兩正三負。正一讀的就是上面那一次框架測試的帳本,
    # 所以必須緊接在它之後、任何 reset 之前。
    _out("\n=== evidence policy 淨室情境(兩正三負;每個情境各一行)===")
    ev_failures = run_evidence_scenarios(target)
    if ev_failures:
        raise SystemExit("\n%d 個 evidence policy 情境沒有成立:%s"
                         % (len(ev_failures), " ".join(EVIDENCE_LABELS[k] for k, _ in ev_failures)))

    _out("\n全部 %d 條規則各擋下一次,權威層偵測正常,框架測試在新 repo 全綠,"
         "evidence policy 兩正三負成立。"
         "\n安裝位置:%s" % (len(codes), target))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("用法:python .claude/portable/verify_gates.py <暫存目錄>")
    main(sys.argv[1])
