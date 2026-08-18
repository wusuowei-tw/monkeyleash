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

SH = shutil.which("sh")

needs_sh = pytest.mark.skipif(
    SH is None,
    reason="這台機器上找不到 sh —— **三道 fail-closed 的行為正對照整組沒有執行**。"
           "結構斷言仍然跑得到,但「它真的會擋」這件事在本機沒有被證明過(票 16)。")


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
    p = subprocess.run([SH, "bootstrap.sh"], cwd=str(repo), capture_output=True)
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
