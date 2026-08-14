# -*- coding: utf-8 -*-
"""票 22 Phase 2 —— 使用者層(`~/.claude/`)的單向匯出/匯入。

**本票的驗收語言:主要輸出是「未帶走清單」。**

R4 定死了兩個 G1 檔腳本不碰(人工複製 + sha 核對),所以**匯出在設計上就是
不完整的**。而一個不完整卻看起來完整的匯出,正是這個 repo 一路在打的形狀 ——
票 27 的靜默缺席、票 26 的假綠、票 25 的假保護。
所以「沒帶走什麼」不是附註,是主要輸出。

不用 symlink:那會讓 dotfiles repo 的工作樹變成第二條可寫路徑
(自助豁免的標準形狀)。正本留在 `~/.claude/`,腳本單向搬。

分桶語意:
  export  腳本帶走
  age     加密後才帶走(唯一一項:個人 leak pattern)
  human   **腳本不碰**,人工 + sha(R4)
  never   永不匯出 —— **不走這條門,不等於不備份**

**預設值刻意沒有。** `portable-manifest.txt` 的預設是 `copy`,理由寫在它表頭:
「多帶是吵鬧的、少帶是靜默的」。**在這個 payload 上那個不對稱是反過來的** ——
多帶是把憑證推上雲端(靜默且不可逆),少帶是換機器當場發現(吵鬧)。
同一個預設值搬到相反的不對稱上就變成缺陷,所以這裡選「沒有預設」
(票 15 已經把預設從查詢裡拿掉,呼叫端自己選)。
"""

import importlib.util
import io
import os
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "user_layer_under_test", ROOT / ".claude" / "portable" / "user_layer.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ul = _load()


# 合成的表,不是實際的那份 —— 測的是分桶機制的性質,與內容無關。
TABLE = """\
upstream-roots.txt      export
settings.json           export
commands/               export
leak-patterns.local.txt age
g1-protected.txt        human
shadow-clamp.txt        human
.credentials.json       never
projects/               never
"""


@pytest.fixture
def home(tmp_path):
    """一個假的 `~/.claude/`,每個桶各放一個可觀測的樣本。"""
    h = tmp_path / "fake_home" / ".claude"
    (h / "commands").mkdir(parents=True)
    (h / "upstream-roots.txt").write_text("UPSTREAM_ROOT=/x\n", encoding="utf-8")
    (h / "settings.json").write_text('{"hooks":{}}\n', encoding="utf-8")
    (h / "commands" / "thing.md").write_text("# 指令\n", encoding="utf-8")
    (h / "leak-patterns.local.txt").write_text("SECRET_TOKEN_SHAPE\n", encoding="utf-8")
    (h / "g1-protected.txt").write_text("# 不該被讀\n", encoding="utf-8")
    (h / "shadow-clamp.txt").write_text("SHADOW_MAX=2099-01-01\n", encoding="utf-8")
    (h / ".credentials.json").write_text('{"token":"x"}\n', encoding="utf-8")
    (h / "projects").mkdir()
    (h / "projects" / "a.jsonl").write_text("{}\n", encoding="utf-8")
    return h


@pytest.fixture
def table(tmp_path):
    p = tmp_path / "user-layer-manifest.txt"
    p.write_text(TABLE, encoding="utf-8")
    return ul.load_marks(str(p))


class TestTheDocumentedCommandActuallyRuns:
    """票 22 Phase 3 前置 —— **文件承諾的指令必須跑得起來。**

    `machine-init.md` 寫著 `python .claude/portable/user_layer.py export <目錄>`,
    而模組**沒有 `__main__`** —— 執行它什麼都不會發生,而且**退出碼是 0**。
    照文件做的人會看到「成功」然後得到一個空目錄。

    這是今天記了一整天的那一族:**文件/訊息宣稱一個不存在的東西**。
    同族:`bootstrap.sh` 宣稱 `core.hooksPath` 而它沒設定(票 27)、
    R7 叫人「改用 Write / Edit」而那兩個工具不能刪檔(票 13)、
    `--no-verify`「會留下紀錄」而 git 不記(票 26)。
    **這一則是我自己寫的** —— 模組與那一節文件都出自同一次工作,
    寫完文件沒有回頭驗指令跑不跑得起來。

    所以斷言的是**輸出**,不是退出碼:沒有 `__main__` 的模組退出碼正好是 0,
    只驗退出碼會是假綠。
    """

    MODULE = str(ROOT / ".claude" / "portable" / "user_layer.py")

    def _run(self, args, cwd):
        import subprocess
        p = subprocess.run([sys.executable, self.MODULE] + args,
                           cwd=str(cwd), capture_output=True)
        return (p.returncode,
                p.stdout.decode("utf-8", "replace"),
                p.stderr.decode("utf-8", "replace"))

    def test_export_dry_run_prints_the_report(self, home, tmp_path):
        """文件寫的那條指令要真的印出報告 —— 包含**未帶走清單**。"""
        tbl = tmp_path / "marks.txt"
        tbl.write_text(TABLE, encoding="utf-8")
        rc, out, err = self._run(
            ["export", str(tmp_path / "out"), "--home", str(home),
             "--marks", str(tbl)], tmp_path)
        assert rc == 0, "文件承諾的指令跑不起來:rc=%s\n%s" % (rc, err)
        assert "未帶走" in out, (
            "指令跑完卻沒印報告 —— 沒有 __main__ 的模組退出碼正好是 0,"
            "只驗退出碼會是假綠:\n%r" % out)

    def test_an_unknown_subcommand_fails_loudly(self, home, tmp_path):
        """打錯子命令不得靜默成功。"""
        rc, out, err = self._run(["frobnicate"], tmp_path)
        assert rc != 0, "不認得的子命令卻回 0"
        assert "frobnicate" in (out + err), "訊息沒點名打錯的是什麼"

    def test_apply_without_a_recipient_refuses_and_says_how_to_fix(
            self, home, tmp_path):
        """`age` 桶非空而沒有 recipient → 拒絕,而且訊息要說怎麼修。

        「拒絕」單獨不夠 —— 票 13 的判準是訊息要說出哪一個前提沒滿足,
        而這裡人能做的動作有兩個(裝 age、給 recipient),訊息要分得開。
        """
        tbl = tmp_path / "marks.txt"
        tbl.write_text(TABLE, encoding="utf-8")
        rc, out, err = self._run(
            ["export", str(tmp_path / "out2"), "--home", str(home),
             "--marks", str(tbl), "--apply"], tmp_path)
        assert rc != 0, "沒有 recipient 卻寫出去了"
        blob = out + err
        assert "leak-patterns.local.txt" in blob, "沒點名是哪一項要加密"
        assert "recipient" in blob.lower(), "沒說出缺的是 recipient"


def test_an_unclassified_item_refuses_the_whole_export(home, table, tmp_path):
    """**紅燈 1。** 未分類 → 拒絕整次匯出,而且點名是哪一項。

    沿用票 15 的判準:未分類不得當成照抄。而這裡連「當成跳過」也不行 ——
    跳過是靜默的,而靜默正是這個 payload 最貴的失敗。
    """
    (home / "mystery-new-file.txt").write_text("?\n", encoding="utf-8")
    with pytest.raises(ul.Refused) as e:
        ul.plan_export(str(home), table)
    assert "mystery-new-file.txt" in str(e.value), (
        "拒絕了但沒說是哪一項 —— 清單長的時候人得自己逐行找:%s" % e.value)


def test_the_human_bucket_files_are_never_even_opened(home, table, monkeypatch):
    """**紅燈 2,本票最尖的一條。**

    R4:兩個 G1 檔腳本不碰。**斷言「輸出裡沒有它」是不夠的** ——
    那只證明沒帶走,不證明沒讀。而在真機器上 G1 第一級會擋讀取,
    腳本若去讀就會整個炸掉;它必須**本來就不去讀**。

    `io.open` 與 `builtins.open` **兩條都攔** —— 只攔一條會是假綠
    (`g1_guard.py` 用的是 `io.open`,而一般碼常用 `open`)。
    """
    opened = []

    real_io_open, real_builtin_open = io.open, open

    def _spy_io(path, *a, **k):
        opened.append(str(path))
        return real_io_open(path, *a, **k)

    def _spy_builtin(path, *a, **k):
        opened.append(str(path))
        return real_builtin_open(path, *a, **k)

    monkeypatch.setattr(io, "open", _spy_io)
    monkeypatch.setattr("builtins.open", _spy_builtin)
    ul.plan_export(str(home), table)
    monkeypatch.undo()

    for forbidden in ("g1-protected.txt", "shadow-clamp.txt"):
        touched = [p for p in opened if p.replace("\\", "/").endswith(forbidden)]
        assert not touched, (
            "%s 被讀取了 —— R4 說腳本不碰,而在真機器上 G1 會擋這個讀取:%s"
            % (forbidden, touched))


def test_the_report_must_list_what_was_left_behind(home, table):
    """**紅燈 3。** 匯出報告**必須**列出未帶走的項目。

    這是本票的驗收語言。少了這一段,匯出讀起來像完整的 ——
    而它依設計就不完整(R4 把兩個檔留給人工)。
    """
    plan = ul.plan_export(str(home), table)
    text = ul.report(plan)
    for expect in ("g1-protected.txt", "shadow-clamp.txt", ".credentials.json"):
        assert expect in text, "報告沒說出未帶走的 %s:\n%s" % (expect, text)
    assert "未帶走" in text or "沒帶走" in text, "報告沒有『未帶走』那一段:\n%s" % text


def test_a_never_item_is_refused_even_if_the_table_says_export(home, tmp_path):
    """**紅燈 4。** 分類表本身是可寫的 —— 秘密不能只靠它守。

    把 `.credentials.json` 標成 `export`,腳本仍然必須拒絕。
    否則「改一行表」就是一條完整的外洩路徑,而那是自助豁免的形狀。
    """
    p = tmp_path / "bad-table.txt"
    p.write_text(TABLE.replace(".credentials.json       never",
                               ".credentials.json       export"), encoding="utf-8")
    bad = ul.load_marks(str(p))
    with pytest.raises(ul.Refused) as e:
        ul.plan_export(str(home), bad)
    assert "credentials" in str(e.value).lower(), e.value


def test_an_age_item_is_not_written_in_the_clear(home, table, tmp_path):
    """**紅燈 5。** `age` 桶的項目未加密就不得寫出。

    裸的祕密永遠不上任何雲端、不進任何 repo(備份總方針)。
    這裡不驗 age 本身,驗的是「沒有加密器就拒絕」——
    有加密器卻沒被呼叫的情況由下一條的位元比對蓋住。
    """
    dest = tmp_path / "dotfiles"
    with pytest.raises(ul.Refused) as e:
        ul.export(str(home), str(dest), table, apply=True, encrypt=None)
    assert "leak-patterns.local.txt" in str(e.value), e.value
    assert not (dest / "leak-patterns.local.txt").exists(), "明文寫出去了"


def test_import_does_not_report_success_while_human_steps_are_pending(
        home, table, tmp_path):
    """**紅燈 6。** 「檔案到位」與「這台機器可以工作了」是兩件事。

    `machine-init.md` 第二節開頭那句「複製檔案不算裝好」,這裡用機器實現:
    人工步驟(兩個 G1 檔 + sha 核對)沒完成之前,匯入不得回報成功。
    """
    dest = tmp_path / "dotfiles"
    ul.export(str(home), str(dest), table, apply=True, encrypt=lambda b: b"AGE" + b)
    fresh = tmp_path / "new_machine" / ".claude"
    result = ul.import_(str(dest), str(fresh), table, apply=True)
    assert result.complete is False, "人工步驟還沒做,卻回報安裝完成"
    assert result.pending, "沒說出還差什麼"
    joined = " ".join(result.pending)
    for f in ("g1-protected.txt", "shadow-clamp.txt"):
        assert f in joined, "待辦沒點名 %s:%s" % (f, result.pending)


def test_legitimate_items_are_actually_taken_byte_for_byte(home, table, tmp_path):
    """**紅燈 7,反控。**

    少了它,「一律拒絕」的實作會讓上面六條全綠 —— 而那是把功能拿掉,不是做出來。
    """
    dest = tmp_path / "dotfiles"
    ul.export(str(home), str(dest), table, apply=True, encrypt=lambda b: b"AGE" + b)
    for rel in ("upstream-roots.txt", "settings.json", "commands/thing.md"):
        src_p = home / rel.replace("/", os.sep)
        dst_p = dest / rel.replace("/", os.sep)
        assert dst_p.exists(), "%s 沒被帶走" % rel
        assert dst_p.read_bytes() == src_p.read_bytes(), "%s 內容不同" % rel
    for rel in ("g1-protected.txt", "shadow-clamp.txt", ".credentials.json",
                "projects/a.jsonl"):
        assert not (dest / rel.replace("/", os.sep)).exists(), "%s 不該被帶走" % rel
    enc = dest / "leak-patterns.local.txt"
    assert enc.exists() and enc.read_bytes().startswith(b"AGE"), "age 項沒被加密"
