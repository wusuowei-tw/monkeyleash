# -*- coding: utf-8 -*-
"""票 58 D2 —— `bootstrap.sh` 的三道 fail-closed。

## 為什麼這支腳本需要守衛,而別的腳本不需要

`git config core.hooksPath .githooks` 是本 repo **唯一**「跑下去就可能靜默
關掉閘門」的動作:設下去之後 `.git/hooks/` 被 git **整個忽略**,
於是指過去的那個目錄若是空的、內容不對、或沒有執行位元,
**六站權威層當場消失,而前哨照跑、測試照綠,沒有任何東西會說話。**

## 檢查必須在設定**之前**(TSI-030)

> **一個跑在危險動作之後的 fail-closed 檢查,不是 fail-closed。**

`core.hooksPath` 是**持久狀態** —— 報錯不會把它收回去。所以
「設完再驗、發現不對就喊」等於已經把閘門關掉之後才喊,
而喊完那個 config 還在。本檔的 `test_every_check_runs_before_the_config_line`
釘的就是這件事,**它是結構斷言,不靠執行**。

## 三道各有正對照

「正對照」= **造一個真的違規,證明它真的擋**。票 47 記過反面:
`monkeypatch` 成 `lambda: []` 是**停用它**、餵假違規是測快取、
只驗代號被列舉是驗**規則存在** —— 三種都不證明規則會動。

所以下面三條各自**真的建一個 repo、真的把它弄成違規狀態、真的跑腳本**,
並且**額外斷言 `core.hooksPath` 沒有被設下去** —— 那一半才是 TSI-030 的重點:
擋下訊息印對了但 config 已經設了,等於沒擋。

## 三道從哪裡來

**下游先做出更好的版本,上游吸收回來**(票 58 卷首)。
判斷順序與措辭出自量化那一份;上游這份必須是它的**超集**,
否則量化將來重跑 install 會被降級。
"""
import io
import os
import pathlib
import shutil
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "bootstrap.sh"

WIRED_HOOK = (
    '#!/bin/sh\n'
    'root="$(git rev-parse --show-toplevel)"\n'
    'python "$root/.claude/portable/leak_scan.py" --staged || exit 1\n'
    'exec python "$root/.claude/hooks/gate.py" --pre-commit\n'
)


def _text():
    return io.open(BOOTSTRAP, encoding="utf-8").read()


def _lines():
    return _text().splitlines()


def _index_of(pred):
    """第一個滿足 pred 的**可執行行**的索引。**註解不算。**

    失效方向要寫對(本 docstring 的第一版寫反了,D3 當天發現):
    把註解算進來**不會讓順序斷言變成假的,會讓它變成假地成立**。

    具體:若有人把「這一道檢查」寫進 `git config` **上方的註解**,而真正的
    檢查搬到了 `git config` **下方**,含註解的比對會在上方先命中 ->
    `check_index < config_index` 成立 -> **測試綠,而腳本已經是假 fail-closed**。

    > **一個結構斷言若能被「那件事的說明」滿足,它就不是在驗那件事。**

    這與 F-086「註解不是機制」是同一句話作用在**測試**上:
    註解不是機制,而**一條會被註解滿足的斷言,也不是機制**。
    """
    for i, line in enumerate(_lines()):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if pred(s):
            return i
    return -1


# ─────────────────────────────────────────────────────────────────────────────
# 結構斷言 —— 不執行腳本,任何平台都跑得到
# ─────────────────────────────────────────────────────────────────────────────

class TestTheChecksAreThereAndComeFirst:

    def test_all_three_checks_exist(self):
        """三道各自的判準要在腳本裡,而且是**可執行行**不是註解。"""
        body = _text()
        assert '[ ! -f "$hook" ]' in body, "缺第一道:hook 檔存不存在"
        assert '[ -z "$mode" ]' in body, "缺第二道:hook 在不在 index"
        assert '[ "$mode" != "100755" ]' in body, "缺第三道:index mode 是不是 100755"

    def test_the_mode_is_read_from_the_index_not_the_filesystem(self):
        """**看 index 不看檔案系統。**

        Windows 的檔案系統不帶執行位元,`test -x` 在本機永遠給錯的答案。
        `git ls-files -s` 問的是 index,那是跨平台的權威 ——
        而這一條正是本輪 D0 量到 `100644` 卻在桌機上完全無感的原因。
        """
        body = _text()
        assert "git ls-files -s" in body, "沒有從 index 讀 mode"
        assert "-x " not in body.replace("--chmod=+x", ""), (
            "用了檔案系統的執行位元判定(test -x)—— 那在 Windows 上永遠是錯的")

    def test_every_check_runs_before_the_config_line(self):
        """**TSI-030 的核心紅燈。**

        `core.hooksPath` 是持久狀態,報錯不會把它收回去。任何一道檢查若排在
        `git config` 之後,它就**不是 fail-closed** —— 它是一句在閘門關掉之後
        才喊出來的話。
        """
        cfg = _index_of(lambda s: s.startswith("git config core.hooksPath"))
        assert cfg >= 0, "找不到 `git config core.hooksPath` 那一行"
        for needle, name in (('[ ! -f "$hook" ]', "缺 hook 檔"),
                             ('[ -z "$mode" ]', "不在 index"),
                             ('[ "$mode" != "100755" ]', "mode 不對")):
            i = _index_of(lambda s, n=needle: n in s)
            assert 0 <= i < cfg, (
                "第「%s」道排在 `git config` 之後(第 %d 行 vs 第 %d 行)—— "
                "跑在危險動作之後的 fail-closed 不是 fail-closed" % (name, i + 1, cfg + 1))

    def test_each_refusal_names_the_fix_or_the_consequence(self):
        """票 13 的判準:**fail-closed 的訊息必須說出是哪一個前提沒滿足。**

        三道的訊息各自要說出後果或修法,否則被擋的人只知道「不給設」。
        """
        body = _text()
        assert "權威層當場消失" in body, "第一道沒說出後果"
        assert "下一個 clone 仍然沒有" in body, "第二道沒說出後果"
        assert "git update-index --chmod=+x" in body, "第三道沒給修法"


# ─────────────────────────────────────────────────────────────────────────────
# 行為正對照 —— 真的建 repo、真的弄成違規、真的跑腳本
# ─────────────────────────────────────────────────────────────────────────────

# **這段字串一個字都沒改**(票 96 驗收第三條)。抽成常數只是為了讓
# 「它沒被改」可以被一條測試釘住(`test_the_skip_message_is_unchanged`)。
SKIP_REASON = ("這台機器上找不到 sh —— **三道 fail-closed 的行為正對照整組沒有執行**。"
               "結構斷言仍然跑得到,但「它真的會擋」這件事在本機沒有被證明過"
               "(monkeyleash framework-updates/16)。")

# Git for Windows 的標準安裝位置(票 96 裁決方向 3)。
#
# **寫死絕對路徑是刻意的,不是偷懶。** 裝在別處的人,他的殼裡本來就有
# `sh` 或 `bash` 在 PATH 上(Git Bash 就是那樣跑起來的)—— 第一輪就命中了。
# 這兩條救的是**另一種人**:在 **PowerShell** 裡跑 pytest。
# 那個殼的 PATH 沒有 `sh` 也沒有 `bash`,而 Git for Windows 就在預設位置。
#
# ⚠ **已知不涵蓋**:裝在非預設磁碟/目錄、又剛好在一個 PATH 上沒有 sh 的殼裡跑。
# 那種情形仍然 skip,**而 skip 訊息會照實說**(它本來就在說實話)。
GIT_FOR_WINDOWS = (
    r"C:\Program Files\Git\usr\bin\sh.exe",
    r"C:\Program Files\Git\bin\bash.exe",
)

# Git for Windows 自己的 coreutils(`cut` / `sed` / `grep` …)住的地方。
GIT_USR_BIN = r"C:\Program Files\Git\usr\bin"

# **Windows PATH 的分隔符,寫死成 `;` —— 不是 `os.pathsep`。**
#
# 🔴 這一行是 CI 紅了一次換來的(`34101592862`,`headSha 8601a351`)。
# `sh_env()` 動 PATH 的那個分支,依構造**只在 Windows 上執行**
# (條件是 `sh in GIT_FOR_WINDOWS`,兩條寫死的 Windows 路徑)——
# 所以它接的是**一個 Windows PATH**,分隔符是 `;`,
# **與跑這支測試的主機是什麼作業系統無關**。
#
# 用 `os.pathsep` 的話,在 Linux 上會拿 `:` 去接一個 Windows PATH,
# 而 `C:\...` 本身就含 `:` —— 接出來的字串沒有任何一邊解得對。
# **一個 Windows 專屬的分支,不該去問主機的平台常數。**
GIT_PATH_SEP = ";"


def find_sh(which=None, exists=None):
    """依序找一個跑得動 `bootstrap.sh` 的殼:`sh` → `bash` → Git for Windows。

    ## 為什麼要有這個(票 96)

    原本是一句 `shutil.which("sh")`。在 **PowerShell** 裡跑 pytest 時,
    那個殼的 PATH 上沒有 `sh` —— **即使**這台機器已經用 Git Bash 跑過
    `bootstrap.sh`、**即使** Git for Windows 就裝在預設位置。
    於是三道 fail-closed 的**行為正對照整組不執行**,而結構斷言照跑照綠。

    > ### **skip 訊息自己說了「它真的會擋在本機沒被證明過」——
    > ### 問題是它出聲之後,沒有人接。**(票 96 的正題,逐字。)

    實測基準(2026-09-07,本機 PowerShell,改動前):**4 passed, 5 skipped**。

    ## 找不到仍然 skip,訊息一個字沒改

    **skip 這條路沒有被拿掉。** 票 96 驗收第三條逐字:
    「**不得把 skip 訊息刪掉或弱化 —— 它現在說的是實話**」。
    本票改的只有「什麼時候需要走那條路」。

    ## 兩個參數是為了可測,不是為了彈性

    `which` / `exists` 注射進來,測試才模擬得出
    「PATH 上什麼都沒有,而 Git for Windows 在」。
    **否則這組測試會變成在問「跑測試那台機器裝了什麼」** ——
    而那個答案在 CI(Linux,有 `sh`)與本機(PowerShell,沒有)不同,
    於是同一條測試在兩邊問的是兩件事。
    """
    which = shutil.which if which is None else which
    exists = os.path.exists if exists is None else exists
    # **PATH 優先。** 使用者的殼裡有什麼就用什麼 ——
    # 拿寫死的路徑去蓋過它,等於在一台刻意裝了別版 sh 的機器上偷換受測的殼。
    for name in ("sh", "bash"):
        found = which(name)
        if found:
            return found
    for path in GIT_FOR_WINDOWS:
        if exists(path):
            return path
    return None


def sh_env(sh=None, environ=None):
    """跑 `bootstrap.sh` 的環境。**走 Git for Windows 的殼時要把它的工具鏈帶上。**

    ## 這是方向 3 自己帶出來的第二個缺口(實測撞到的)

    接上 `sh.exe` 之後那 5 條真的開始跑了,而其中 3 條當場紅:

        bootstrap.sh: line 61: cut: command not found

    成因不在 `bootstrap.sh`:**PowerShell 的 PATH 上沒有 coreutils**,
    子行程繼承的就是那個 PATH。
    **一個叫得動 `sh.exe` 卻沒有 `cut` 的環境,不是「跑得動 bootstrap.sh 的殼」。**

    > ### **只挑殼、不帶它的工具鏈,換來的是一個【紅得不是地方】的結果 ——
    > ### 它看起來像 `bootstrap.sh` 壞了,而三道檢查其實一道都還沒跑到。**
    > **那比 skip 更糟**:skip 至少誠實說「沒有被證明過」,
    > 而這種紅會讓人去修一個沒有壞的東西。

    **只有走寫死路徑那條才動 PATH**(前置,不覆蓋)。PATH 上就有 `sh` 的機器
    (Git Bash、Linux CI)本來就帶著自己的工具鏈,
    再前置一個 Windows 專屬目錄等於**在 CI 上憑空插一個不存在的路徑**。
    """
    sh = SH if sh is None else sh
    environ = os.environ if environ is None else environ
    env = dict(environ)
    if sh and sh in GIT_FOR_WINDOWS:
        # **`GIT_PATH_SEP` 不是 `os.pathsep`** —— 這個分支依構造只在 Windows 上
        # 執行,接的是一個 Windows PATH。理由與那次 CI 紅寫在常數旁邊。
        env["PATH"] = GIT_USR_BIN + GIT_PATH_SEP + env.get("PATH", "")
    return env


SH = find_sh()

needs_sh = pytest.mark.skipif(SH is None, reason=SKIP_REASON)


def _repo(tmp_path, name):
    repo = tmp_path / name
    repo.mkdir()
    for c in ("init -q", "config user.email t@t", "config user.name t"):
        subprocess.run(["git"] + c.split(), cwd=str(repo), capture_output=True)
    shutil.copy2(str(BOOTSTRAP), str(repo / "bootstrap.sh"))
    return repo


def _write_hook(repo, body=WIRED_HOOK):
    d = repo / ".githooks"
    d.mkdir(exist_ok=True)
    io.open(str(d / "pre-commit"), "w", encoding="utf-8", newline="\n").write(body)


def _run(repo):
    p = subprocess.run([SH, "bootstrap.sh"], cwd=str(repo), capture_output=True,
                       env=sh_env())
    out = (p.stdout + p.stderr).decode("utf-8", "replace")
    return p.returncode, out


def _hookspath(repo):
    p = subprocess.run(["git", "config", "--local", "--get", "core.hooksPath"],
                       cwd=str(repo), capture_output=True)
    return p.stdout.decode("utf-8", "replace").strip()


@needs_sh
class TestEachCheckActuallyRefuses:
    """三道正對照。**每一條都斷言兩件事**:擋下了,而且 config 沒被設。

    只斷言退出碼的話,一支「先設 config 再喊」的腳本會全部通過 ——
    而那正是 TSI-030 說的那種假 fail-closed。
    """

    def test_a_missing_hook_file_is_refused(self, tmp_path):
        repo = _repo(tmp_path, "nohook")          # 不建 .githooks/
        rc, out = _run(repo)
        assert rc != 0, "缺 hook 檔卻放行了:%s" % out
        assert "找不到" in out, out
        assert _hookspath(repo) == "", (
            "拒絕了,但 core.hooksPath 已經被設下去 —— 報錯不會把它收回來")

    def test_a_hook_not_in_the_index_is_refused(self, tmp_path):
        """檔案在磁碟上,但**沒有 git add**。

        這一格最容易被漏掉:`ls` 看得到、`test -f` 過得了,
        而它不隨 clone 走 —— 下一個 clone 回到起點,且完全無聲。
        """
        repo = _repo(tmp_path, "notinindex")
        _write_hook(repo)                          # 只寫檔,不 add
        rc, out = _run(repo)
        assert rc != 0, "hook 不在 index 卻放行了:%s" % out
        assert "index" in out, out
        assert _hookspath(repo) == "", "拒絕了,但 config 已被設"

    def test_a_hook_with_mode_100644_is_refused(self, tmp_path):
        """**D0 在上游自己身上量到的就是這一格。**

        `git ls-files -s .githooks/pre-commit` -> `100644`。
        Linux 上 git 不執行它,而且不出聲。
        """
        repo = _repo(tmp_path, "badmode")
        _write_hook(repo)
        subprocess.run(["git", "add", ".githooks/pre-commit"],
                       cwd=str(repo), capture_output=True)
        subprocess.run(["git", "update-index", "--chmod=-x", ".githooks/pre-commit"],
                       cwd=str(repo), capture_output=True)
        rc, out = _run(repo)
        assert rc != 0, "mode 100644 卻放行了:%s" % out
        assert "100755" in out, out
        assert "--chmod=+x" in out, "沒給修法:%s" % out
        assert _hookspath(repo) == "", "拒絕了,但 config 已被設"


@needs_sh
class TestItStillWiresUpWhenEverythingIsRight:
    """**反控。** 三道不是「一律拒絕」——條件滿足時它必須真的把 config 設下去。

    少了這一條,把腳本改成 `exit 1` 第一行也會讓上面三條全綠,
    而那是「擋得對」與「什麼都擋」分不開的狀態。
    """

    def test_a_correctly_staged_hook_gets_the_config_set(self, tmp_path):
        repo = _repo(tmp_path, "good")
        _write_hook(repo)
        subprocess.run(["git", "add", ".githooks/pre-commit"],
                       cwd=str(repo), capture_output=True)
        subprocess.run(["git", "update-index", "--chmod=+x", ".githooks/pre-commit"],
                       cwd=str(repo), capture_output=True)
        rc, out = _run(repo)
        assert rc == 0, "條件都滿足卻被擋:%s" % out
        assert _hookspath(repo) == ".githooks", (
            "沒被擋,但 config 也沒設 —— 腳本什麼都沒做:%s" % out)


@needs_sh
class TestThisRepoItselfPassesItsOwnChecks:
    """**活體金絲雀。** 上游自己的 `.githooks/pre-commit` 要過得了這三道。

    這一條刻意違反「只驗未安裝路徑」那條原則(接縫 S3),理由與
    `test_this_repo_itself_is_wired` 相同:**它問的不是框架性質,是部署事實。**

    D0 量到上游自己是 `100644` —— 也就是說**在同一筆 commit 修好之前,
    這一條會紅**。那個紅是要它紅:三道檢查抓到的第一個違規者,
    正是寫出這三道的框架自己。
    """

    def test_the_upstream_hook_is_staged_executable(self):
        p = subprocess.run(["git", "ls-files", "-s", "--", ".githooks/pre-commit"],
                           cwd=str(ROOT), capture_output=True)
        rec = p.stdout.decode("utf-8", "replace").strip()
        assert rec, ".githooks/pre-commit 不在 index 裡"
        mode = rec.split()[0]
        assert mode == "100755", (
            ".githooks/pre-commit 的 index mode 是 %s,不是 100755 —— "
            "Linux 上 git 不會執行它,而且不出聲。\n"
            "     修法:git update-index --chmod=+x .githooks/pre-commit" % mode)


# ─────────────────────────────────────────────────────────────────────────────
# 票 96 —— 找 sh 的方式(方向 3:PATH 沒有就去試 Git for Windows 的標準路徑)
# ─────────────────────────────────────────────────────────────────────────────

# ⚠ **這是本檔 skip 訊息的逐字副本,用來釘住「一個字都不改」。**
# 票 96 驗收第三條逐字:「不得把 skip 訊息刪掉或弱化 —— 它現在說的是實話」。
# 兩份字串必須相同;不同就是有人動了訊息,而那正是這條反控要抓的事。
EXPECTED_SKIP_REASON = (
    "這台機器上找不到 sh —— **三道 fail-closed 的行為正對照整組沒有執行**。"
    "結構斷言仍然跑得到,但「它真的會擋」這件事在本機沒有被證明過"
    "(monkeyleash framework-updates/16)。")


class TestFindingShFallsBackToGitForWindows:
    """票 96 —— 在沒有 `sh` 的殼下,三道 fail-closed 的行為正對照整組不執行。

    ## 病灶不是 skip 本身

    skip 訊息**寫得完全正確**,而且照票 16 主動出聲了。
    **問題是它出聲之後,沒有人接** —— 在 PowerShell 裡跑 pytest,
    即使這台機器已經用 Git Bash 跑過 `bootstrap.sh`、
    即使 Git for Windows 就裝在預設位置,那 5 條仍然 skip。

    實測基準(2026-09-07,本機 PowerShell,改動前):**4 passed, 5 skipped**。

    ## 為什麼注射 `which` / `exists`,不看本機真的有沒有 Git

    **否則這組測試會變成在問「跑測試那台機器裝了什麼」** ——
    而那個答案在 CI(Linux,有 `sh`)與本機(PowerShell,沒有)不同,
    於是同一條測試在兩邊問的是兩件事。注射之後,四個分支在任何平台都跑得到。

    ## 四條各自封住一個退化解

    | | 驗什麼 | 少了它 |
    |---|---|---|
    | ① | PATH 什麼都沒有、Git for Windows 在 → **回那條路徑** | 這是病灶本身 |
    | ② | PATH 有 `sh` → **回 PATH 那個**,不去碰寫死的路徑 | 一個「一律回寫死路徑」的實作也會讓 ① 綠 |
    | ③ | PATH 沒有 `sh` 但有 `bash` → 回 `bash` | 一個「只認 sh 就跳去看檔案」的實作也會讓 ①② 綠 |
    | ④ | 兩邊都沒有 → **回 `None`,而且 skip 訊息一個字沒改** | 一個「永遠找得到東西」的實作會讓 skip 這條路悄悄消失 |
    """

    def test_git_for_windows_is_used_when_path_has_neither(self):
        """① **病灶本身。** PATH 上沒有 `sh` 也沒有 `bash`,而 Git 裝在預設位置。"""
        seen = []

        def which(name):
            seen.append(name)
            return None

        found = find_sh(which=which, exists=lambda p: p in GIT_FOR_WINDOWS)
        assert found in GIT_FOR_WINDOWS, (
            "PATH 上沒有 sh/bash 而 Git for Windows 在,卻沒有用它:%r" % found)
        assert seen == ["sh", "bash"], (
            "PATH 那一輪沒有依序試過 sh 與 bash:%r" % seen)

    def test_the_shell_on_path_wins_over_the_hardcoded_paths(self):
        """② **反控:PATH 優先。**

        使用者的殼裡有什麼就用什麼 —— 拿寫死的路徑去蓋過它,
        等於在一台刻意裝了別版 `sh` 的機器上偷換掉受測的殼。
        """
        found = find_sh(which=lambda n: "/usr/bin/sh" if n == "sh" else None,
                        exists=lambda p: True)
        assert found == "/usr/bin/sh", found

    def test_bash_is_tried_when_sh_is_absent(self):
        """③ **`bash` 那一格。** 少了它,`sh` 缺席就直接跳去看檔案系統。"""
        found = find_sh(which=lambda n: "/usr/bin/bash" if n == "bash" else None,
                        exists=lambda p: True)
        assert found == "/usr/bin/bash", found

    def test_nothing_anywhere_still_skips_with_the_same_message(self):
        """④ **反控:skip 那條路沒有被拿掉,訊息一個字也沒改。**

        票 96 驗收第三條逐字:**不得把 skip 訊息刪掉或弱化** ——
        它說的是實話,而本票改的只有「什麼時候需要走那條路」。
        """
        assert find_sh(which=lambda n: None, exists=lambda p: False) is None

    def test_a_git_for_windows_shell_gets_its_own_toolchain_on_path(self):
        """🔴 **方向 3 自己帶出來的第二個缺口 —— 實測撞到的,不是想出來的。**

        接上 Git for Windows 的 `sh.exe` 之後,那 5 條**真的開始跑了**,
        而其中 3 條當場紅:

            bootstrap.sh: line 61: cut: command not found

        成因不在 `bootstrap.sh`:PowerShell 的 PATH 上沒有 coreutils,
        而子行程繼承的是那個 PATH。**一個叫得動 `sh.exe` 卻沒有 `cut` 的環境,
        不是「跑得動 `bootstrap.sh` 的殼」。**

        > ### **只挑殼、不帶它的工具鏈,換來的是一個【紅得不是地方】的結果 ——
        > ### 它看起來像 `bootstrap.sh` 壞了,而三道檢查其實一道都還沒跑到。**
        >
        > 那比 skip 更糟:skip 至少誠實說「沒有被證明過」,
        > 而這種紅會讓人去修一個沒有壞的東西。

        實測(2026-09-07,PowerShell):把 `C:\\Program Files\\Git\\usr\\bin`
        放進 PATH 之後,同一支檔 **14 passed**。
        """
        env = sh_env(sh=GIT_FOR_WINDOWS[0], environ={"PATH": "C:\\Windows"})
        # ⚠ **不切字串**(`split(os.pathsep)`)—— `C:\...` 本身就含 `:`,
        # 而 `os.pathsep` 在 Linux 正好是 `:`,於是切點落在磁碟代號後面。
        # 那次 CI 紅就是這麼來的;改成問「有沒有前置」,兩個平台同一個語意。
        assert env["PATH"].startswith(GIT_USR_BIN + GIT_PATH_SEP), (
            "走 Git for Windows 的殼,卻沒有把它的 coreutils 放到 PATH 最前面:%r"
            % env["PATH"])
        assert env["PATH"].endswith("C:\\Windows"), (
            "原本的 PATH 被蓋掉了,不是前置:%r" % env["PATH"])

    def test_the_same_input_holds_when_the_host_looks_like_linux(self, monkeypatch):
        """🔴 **反控:同一組輸入,在「假裝是 Linux」的主機上也要成立。**

        ## 這條在本機重現得出 CI 那個紅

        上一條的第一版斷言寫的是 `env["PATH"].split(os.pathsep)[0]`,
        而 **`os.pathsep` 在 Linux 是 `:`** —— 於是
        `'C:\\Program Files\\Git\\usr\\bin:C:\\Windows'` 會從 `C` 後面被切開,
        第一段變成 `'C'`。**本機(Windows,`;`)恆綠,CI(Linux)紅。**

        CI 原文(`34101592862`,`headSha 8601a351`):

            E  AssertionError: 走 Git for Windows 的殼,卻沒有把它的 coreutils
               放到 PATH 最前面:'C:\\Program Files\\Git\\usr\\bin:C:\\Windows'
            E  assert 'C' == 'C:\\Program ...Git\\usr\\bin'

        > ### **本條把那個平台條件搬進測試裡,所以它在【任何】平台上都問得出來。**
        > 少了它,這個缺陷**只有推上去才看得到** ——
        > 而票 54 落差表「本機看不到、只有 CI 看得到」那一格會再長一筆。

        ## 判準:Windows 的 PATH 用 `;`,而這個分支依構造只在 Windows 上執行

        `sh_env()` 只在 `sh in GIT_FOR_WINDOWS`(兩條寫死的 Windows 路徑)時
        才動 PATH,**那個條件在 Linux 上永遠不成立**。
        所以那一段接的是**一個 Windows PATH**,分隔符是 `;` ——
        **與跑這支測試的主機是什麼作業系統無關。**
        `GIT_PATH_SEP` 就是把這句話寫成一個常數。
        """
        # ⚠ **只換 `os.pathsep`,不換 `os.name`。**
        # 換 `os.name` 會讓 `pathlib` 整個改走 POSIX 分支,而 pytest 自己的
        # 錯誤報告也用 `pathlib` —— 實測結果是
        # `INTERNALERROR> NotImplementedError: cannot instantiate 'PosixPath' on your system`:
        # **測試沒有紅,是整個 pytest 死掉**,而那種死法連失敗訊息都印不出來。
        #
        # `os.pathsep` 才是這個缺陷依賴的那一個變數;換它就足以重現 CI 那個紅。
        # **模擬要換的是【被依賴的那一格】,不是【整個作業系統】** ——
        # 換得越多,壞掉的東西越可能不是受測的那個。
        monkeypatch.setattr(os, "pathsep", ":")
        env = sh_env(sh=GIT_FOR_WINDOWS[0], environ={"PATH": "C:\\Windows"})
        assert env["PATH"].startswith(GIT_USR_BIN + GIT_PATH_SEP), (
            "主機看起來像 Linux 時,前置用的分隔符跟著主機跑了 —— "
            "而接的是一個 Windows PATH:%r" % env["PATH"])
        assert env["PATH"].endswith("C:\\Windows"), (
            "原本的 PATH 被蓋掉了,不是前置:%r" % env["PATH"])

    def test_a_shell_from_path_does_not_get_its_path_rewritten(self):
        """**反控:只有走寫死路徑那條才動 PATH。**

        PATH 上就有 `sh` 的機器(Git Bash、Linux CI)本來就帶著自己的工具鏈,
        再前置一個 Windows 專屬目錄是**在 CI 上憑空插一個不存在的路徑**。
        少了這條,那個副作用不會有任何東西說。
        """
        env = sh_env(sh="/usr/bin/sh", environ={"PATH": "/usr/bin"})
        assert env["PATH"] == "/usr/bin", env["PATH"]

    def test_the_skip_message_is_unchanged(self):
        """④之二 —— **這一條在改動前後都該綠,而它是刻意分開的。**

        與上一條分開寫的理由:上一條在動工當下紅在 `NameError`
        (`find_sh` 還不存在),**如果訊息比對跟它綁在同一條測試裡,
        「訊息沒被改」這件事在動工當下就沒有被證明過** ——
        而那正是本票唯一不准動的東西。
        **分開之後,它從第一次跑就在守著。**
        """
        assert needs_sh.kwargs["reason"] == EXPECTED_SKIP_REASON, (
            "skip 訊息被改動了 —— 票 96 明訂不得刪除或弱化。\n"
            "  現況:%r" % needs_sh.kwargs["reason"])
