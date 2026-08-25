# -*- coding: utf-8 -*-
"""G1 —— 保護清單的帶邊界前綴比對。

這份是 repo 內的版本,正式檔在 `~/.claude/hooks/g1_guard.py`,
**只有人能覆蓋過去**(ADR 0009)。repo 內的版本受 R 系列管
(條列見 `gate.py` 的 `rule_codes()`,不寫死範圍):
有測試、要在 implement 站寫、要用檔案工具寫。
放在 `~/.claude/` 底下的話這些一條都不適用 ——
**防護機制的修改反而是整個系統裡管得最鬆的地方**,那個方向是錯的。

比對方式的取捨:

  子字串(現行)  子目錄自動涵蓋 ✅  但 `D:\\notes1` 會誤中 `D:\\notes123` ❌
  帶邊界前綴      子目錄自動涵蓋 ✅  相鄰名稱不誤中 ✅

誤擋累積起來的後果是規則被關掉,而關掉的涵蓋率是零(F-031)。
"""

import ast
import importlib.util
import io
import pathlib
import warnings

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


SRC = ROOT / ".claude" / "portable" / "g1_guard.py"


def _load():
    spec = importlib.util.spec_from_file_location("g1_under_test", SRC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_the_guard_body_still_compiles_when_warnings_are_errors():
    """**這一支未來還編不編得動。** framework-updates/69。

    由來:量化 `TSI-037` —— 本檔的 docstring 含 `\\<` 而它不是 raw string,
    CI 的 log 出現 `DeprecationWarning: invalid escape sequence`。
    今天只是警告,而 Python 3.12 起這一族已轉 `SyntaxWarning`,
    更晚的版本規劃改成 `SyntaxError` —— **屆時本檔直接 import 失敗,
    而它是 G1 的守衛本體**:防護不會報錯,它會不在。

    **測剖析不測 import**:import 有副作用(讀家目錄的清單),
    而要問的是「編譯器還收不收這份原始碼」,那由 `ast.parse` 回答。

    範圍限本檔 —— **R3 要的紅燈必須在配對的測試檔裡**,而那是這一份。
    同一個判準對 `.claude/` 底下**全部** `.py` 的枚舉在
    `tests/test_source_hygiene.py::test_claude_python_parses_clean_with_warnings_as_errors`
    (封閉集合,枚舉不比對)。兩條不是重複:
    **這一條是這個檔案的紅燈,那一條是這一族的偵測器。**
    """
    src = io.open(SRC, encoding="utf-8").read()
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        warnings.simplefilter("error", SyntaxWarning)
        ast.parse(src, filename=str(SRC))


g1 = _load()

# **合成路徑,不是任何人的實際清單。** 這裡驗的是比對的性質(前綴、邊界、
# CJK、自我保護),那些性質與路徑內容無關 —— 而實際清單留在
# ~/.claude/g1-protected.txt,不進版控。`保管庫` 保留一個 CJK 條目以驗
# 非 ASCII 路徑;`fake_user` 佔位使用者名稱。
PROTECTED = [
    r"C:\Users\fake_user\Backups\vault",
    r"C:\db_backups",
    r"D:\datastore",
    r"D:\保管庫",
    r"D:\notes1",
]


class TestDriveRootEntriesAreRejectedLoudly:
    """票 25 — 磁碟根目錄條目(`D:\\`)是**假保護陷阱**,必須大聲拒絕。

    寫一條 `D:\\` 看起來是「整顆磁碟都保護」。實際上 `variants()` 只產出
    `['d:']` 一個變體,因為 `rstrip("\\\\/")` 把它削成 `D:`,
    而 git bash 分支的正則 `^([A-Za-z]):[\\\\/](.*)$` 要求磁碟代號後面有分隔符。

    後果是**兩個方向同時錯,而且方向相反**:

      太寬  `d:` 會命中該磁碟上的任何路徑 —— 一條進去整顆磁碟全擋
      又漏  `/d/...`(git bash 形態)不在變體裡 —— 而那正是本專案 Bash 工具用的形態

    誤擋不會有人抱怨(整顆磁碟本來就少碰),漏擋不會有人發現(沒有訊號),
    兩者剛好互相掩護。**而 `g1_verify` 對它給假綠**:探針
    `touch "D:\\g1_verify_probe.txt"` 剛好走 `d:` 那個唯一生效的變體。

    選型:**大聲拒絕**,不是「正確支援」。理由 ——
    守衛不得接受一種**自己守不住**的條目寫法;而整顆磁碟保護的真實需求
    先前已裁決不採(憑證改用逐檔條目,收攏另議)。
    支援它等於維護一個沒有使用者的語意,而那個語意的每一種寫法都要再驗一次。
    """

    def test_variants_of_a_drive_root_lose_the_git_bash_form(self):
        """**這條是拒絕的理由,不是願望。** 釘住現行行為:磁碟根條目產不出 `/d/`。

        修法不改 `variants()`(見 class docstring),所以這條在修完之後**仍然綠** ——
        它存在的目的是讓「為什麼要拒絕」有機器可讀的證據,
        而不是留在票裡當一句宣稱。
        """
        got = g1.variants("D:\\")
        assert not any(v.startswith("/d/") for v in got), (
            "如果哪天 variants 真的支援了磁碟根,拒絕的理由就該重新檢討:%s" % got)
        assert "d:" in got, got

    def test_a_drive_root_entry_is_detected(self):
        """`D:\\` / `D:/` / `d:` / `/d/` 都是磁碟根,四種寫法都要認得。"""
        for raw in ("D:\\", "D:/", "d:", "/d/", "C:\\", "  E:\\  "):
            assert g1.is_drive_root(raw), "沒認出磁碟根條目:%r" % raw

    def test_a_normal_entry_is_not_mistaken_for_a_drive_root(self):
        """**反控。** 少了它,「一律拒絕」的實作也會讓上一條過 ——
        而那會把整份清單擋掉,誤擋成本從近乎零變成全部。"""
        for raw in (r"D:\datastore", r"C:\db_backups", r"D:\保管庫",
                    "/d/datastore", r"C:\Users\fake_user\Backups\vault"):
            assert not g1.is_drive_root(raw), "正常條目被當成磁碟根:%r" % raw

    def test_a_list_containing_a_drive_root_fails_closed(self, tmp_path,
                                                         monkeypatch, capsys):
        """讀到磁碟根條目 -> **回 None(fail-closed)**,而且訊息**點名那一行**。

        點名是票 13 的判準:訊息要說出是哪一個前提沒滿足。
        只說「清單有問題」的話,人得自己逐行找 —— 而清單可能有三十幾行。
        """
        lst = tmp_path / "g1-protected.txt"
        lst.write_text("# 註解\n%s\nD:\\\n%s\n" % (r"C:\db_backups", r"D:\datastore"),
                       encoding="utf-8")
        monkeypatch.setattr(g1, "PROTECTED_LIST", str(lst))
        entries, reason = g1.protected_entries()
        assert entries is None, (
            "清單含磁碟根條目卻照常回傳 —— 那條目守不住 /d/ 形態,"
            "而使用者以為整顆磁碟都保護了")
        assert "3" in reason, "訊息沒點出是第幾行:%r" % reason
        assert "D:\\" in reason or "d:" in reason.lower(), \
            "訊息沒點名那一行的內容:%r" % reason

    def test_the_rejection_message_does_not_also_claim_the_list_is_unreadable(
            self, tmp_path, monkeypatch, capsys):
        """**票 25 收尾。** 擋下時只能說出**真正**沒滿足的那個前提。

        實測(live 探針)印了兩段:第一段點名第 55 行的寫法(對的),
        第二段說「讀不到保護清單」(**假的** —— 讀得到、解析得動,
        只是那一行不被接受)。人會照第二段去查權限與編碼,而答案在第一段。

        與票 26 的 `--no-verify`「會留下紀錄」、票 13 的「請改用 Write / Edit」
        同一族:**訊息描述了一個不成立的狀況**,而人會照著它去做。
        """
        import io as _io
        lst = tmp_path / "g1-protected.txt"
        lst.write_text("%s\nD:\\\n" % r"C:\db_backups", encoding="utf-8")
        monkeypatch.setattr(g1, "PROTECTED_LIST", str(lst))

        class _Stdin(object):
            buffer = _io.BytesIO(
                b'{"tool_name":"Bash","tool_input":{"command":"echo probe"}}')

        monkeypatch.setattr(g1.sys, "stdin", _Stdin())
        rc = g1.main()
        err = capsys.readouterr().err

        assert rc == 2, "磁碟根條目沒有 fail-closed"
        assert "磁碟根目錄條目" in err, "沒說出真正的原因:%r" % err
        assert "讀不到保護清單" not in err, (
            "同時宣稱『讀不到保護清單』—— 那是假的,清單讀得到、"
            "解析得動,只是那一行不被接受:%r" % err)

    def test_a_clean_list_still_loads(self, tmp_path, monkeypatch):
        """**反控。** 正常清單照常讀得到,而且筆數不變。"""
        lst = tmp_path / "g1-protected.txt"
        lst.write_text("# 註解\n%s\n%s\n" % (r"C:\db_backups", r"D:\datastore"),
                       encoding="utf-8")
        monkeypatch.setattr(g1, "PROTECTED_LIST", str(lst))
        entries, reason = g1.protected_entries()
        assert entries == [r"C:\db_backups", r"D:\datastore"]
        assert reason is None, "成功卻帶著理由:%r" % reason


class TestPrefixMatchingCoversSubdirectories:
    @pytest.mark.parametrize("cmd,expect", [
        (r'touch "D:\保管庫\probe.txt"', r"D:\保管庫"),
        (r'touch "D:/保管庫/2023/深層/x.jpg"', r"D:\保管庫"),      # 深層子目錄
        (r'rm /d/保管庫', r"D:\保管庫"),                           # git bash 形態
        (r'ls d:\保管庫', r"D:\保管庫"),                           # 小寫磁碟機
        (r'cp x C:/db_backups/y', r"C:\db_backups"),
    ])
    def test_a_protected_path_and_everything_under_it_is_blocked(self, cmd, expect):
        assert g1.level1_hit(cmd, PROTECTED) == expect, cmd


class TestAdjacentNamesAreNotFalselyBlocked:
    """`D:\\notes1` 不得讓 `D:\\notes123` 一起被擋。

    這是本票的實質:子字串比對在這裡誤擋,而誤擋累積起來規則會被關掉。
    """

    @pytest.mark.parametrize("cmd", [
        r'touch D:\notes123\x.txt',
        r'rm -rf D:/notes1_old/',
        r'ls D:/datastore_scratch/',
        r'touch C:/db_backups_tmp/x',
    ])
    def test_a_neighbouring_name_is_not_a_hit(self, cmd):
        assert g1.level1_hit(cmd, PROTECTED) is None, "誤擋:%s" % cmd


class TestTheListItselfStaysProtected:
    def test_the_list_and_the_guard_are_still_hits(self):
        entries = PROTECTED + [
            r"C:\Users\fake_user\.claude\g1-protected.txt",
            r"C:\Users\fake_user\.claude\hooks\g1_guard.py",
        ]
        assert g1.level1_hit(
            r'echo x >> C:/Users/fake_user/.claude/g1-protected.txt', entries)
        assert g1.level1_hit(
            r'rm C:\Users\fake_user\.claude\hooks\g1_guard.py', entries)


class TestFailClosedIsPreserved:
    def test_an_unreadable_list_returns_none_so_the_caller_blocks(
            self, tmp_path, monkeypatch):
        """讀不到 -> entries 為 None,而且**理由說的就是讀不到**。

        票 25 收尾把回傳改成 `(entries, reason)`:失敗要帶著理由走,
        呼叫端才不會用一句通用的話蓋掉真正的原因。
        """
        monkeypatch.setattr(g1, "PROTECTED_LIST", str(tmp_path / "gone.txt"))
        entries, reason = g1.protected_entries()
        assert entries is None
        assert "讀不到" in reason, "理由沒說出是讀不到:%r" % reason

    def test_a_readable_list_is_parsed_without_comments(self, tmp_path, monkeypatch):
        p = tmp_path / "list.txt"
        io.open(p, "w", encoding="utf-8", newline="\n").write(
            "# 註解\n\nD:\\保管庫\nD:\\封存   # 行尾註解\n")
        monkeypatch.setattr(g1, "PROTECTED_LIST", str(p))
        entries, reason = g1.protected_entries()
        assert entries == ["D:\\保管庫", "D:\\封存"]
        assert reason is None

    def test_an_empty_list_is_not_a_pass(self, tmp_path, monkeypatch):
        """只有註解的清單 = 涵蓋範圍是零,而它不會出聲 —— 與沒有清單一樣危險。

        原本 `return out or None` 把這個情況混進「讀不到」裡,
        訊息因此會說「讀不到保護清單」,而檔案好端端在那裡(票 25 收尾)。
        """
        p = tmp_path / "list.txt"
        io.open(p, "w", encoding="utf-8", newline="\n").write("# 全是註解\n\n")
        monkeypatch.setattr(g1, "PROTECTED_LIST", str(p))
        entries, reason = g1.protected_entries()
        assert entries is None
        assert "沒有任何有效條目" in reason, "把空清單說成讀不到:%r" % reason


class TestAbsPathExtraction:
    """`ABS_PATH` 是**共用比對基礎**,不是 `_is_scratch` 私有的。

    邊界符放的位置決定它是**收邊界**還是**砍長度**:
    放在擷取處會讓 `/etc-backup/x` 整條不被擷取 —— 第二級看不見它,
    於是從「擋下」變成「放行」。回歸集當場抓到六條。
    **擷取要吃完整個 token,邊界屬於豁免判定。**
    """

    @pytest.mark.parametrize("cmd,expect", [
        # 帶點
        ("rm -rf /home/u/data.tar.gz", "/home/u/data.tar.gz"),
        ("rm -rf /usr.old/x", "/usr.old/x"),
        # 帶連字號
        ("rm -rf /etc-backup/x", "/etc-backup/x"),
        ("rm -rf /home/u/my-file-name.txt", "/home/u/my-file-name.txt"),
        # 結尾接引號
        ('rm -rf "/home/u/data.tar.gz"', "/home/u/data.tar.gz"),
        # 結尾接 &&
        ("rm -rf /home/u/x && echo done", "/home/u/x"),
        # Windows 形態同樣要吃完
        (r"rm -rf C:/Users/u/my-dir.v2/x", "C:/Users/u/my-dir.v2/x"),
    ])
    def test_the_whole_token_is_captured(self, cmd, expect):
        got = g1.ABS_PATH.findall(cmd)
        assert expect in got, "擷取不完整:%r -> %r" % (cmd, got)

    def test_a_relative_path_is_still_not_captured(self):
        """守住上面那條不是「什麼都抓」:`rm .cache/x.json` 裡的 `/x.json`
        不得被當成絕對路徑 —— 那是第一次驗收就抓到的誤擋。"""
        assert g1.ABS_PATH.findall("rm -rf build/ && rm .cache/x.json") == []


class TestLevelTwoIsUnchanged:
    """第二級不在本票範圍 —— 但它不能因為改了第一級而壞掉。"""

    def test_in_project_deletion_still_passes(self):
        assert g1.level2_hit(r"rm -rf build/ && rm .cache/x.json",
                             r"c:\proj") is None

    def test_out_of_project_destructive_still_blocks(self):
        hit = g1.level2_hit(r"rm -rf C:/Users/someone/Documents/x", r"c:\proj")
        assert hit and hit[0].lower() == "rm"

    @pytest.mark.parametrize("path", [
        r"C:/Users/someone/AppData/Local/Temp/../../../../Windows/System32",
        r"C:/Users/someone/AppData/Local/Temp/../../../../../D:/x",
        "/tmp/../etc/passwd",
        "/var/tmp/../../root",
    ])
    def test_traversal_out_of_a_scratch_area_is_not_exempt(self, path):
        """**`in` 比對 + 未解 `..` = traversal 洞。**

        `C:/…/Temp/../../../../<目標>` 命中 marker → 豁免 → 第二級放行,
        而實際碰到的是完全不同的地方。

        這與「許可前綴不能替後面那段背書」是同一條判準(F-051)——
        `cd` 進了 R7 的許可清單時才剛寫過,換個位置又出現一次。
        **任何用子字串或前綴放行的地方都適用。**
        """
        assert g1.level2_hit("rm -rf %s" % path, r"c:\proj") is not None, path

    @pytest.mark.parametrize("path", [
        "/tmpdata/x",
        "/tmp_backup/x",
        "/var/tmpfoo/x",
        "/procedures/x",
        "/tmpfile",
    ])
    def test_a_name_that_merely_starts_with_a_scratch_prefix_is_not_exempt(self, path):
        """`startswith("/tmp")` 沒有邊界符 —— 會命中 `/tmpdata`、`/tmp_backup`。

        與 `.gitignore` 的 `skills/` 缺前導斜線同一族:
        **前綴比對沒帶邊界,就會吃掉開頭相同的別的名字。**

        直接測述詞:這一條問的是「豁免會不會誤收」,
        而「level2 會不會擋」還取決於 ABS_PATH 認不認得那個路徑 ——
        那是另一個缺口,見下一條。
        """
        assert g1._is_scratch(path) is False, path

    @pytest.mark.parametrize("path", [
        "/var/tmpfoo/x",
    ])
    def test_a_neighbouring_name_under_a_known_root_still_blocks(self, path):
        """端到端:頂層目錄在 ABS_PATH 認得的清單裡時,鄰居名稱會被完整捕捉並擋下。"""
        assert g1.level2_hit("rm -rf %s" % path, r"c:\proj") is not None, path

    @pytest.mark.xfail(
        strict=True,
        reason="monkeyleash framework-updates/04:ABS_PATH 的 POSIX 分支是頂層目錄"
               "白名單,未列名的根目錄第二級看不見。**變綠的條件**:那張票把它"
               "改成通用比對(或補上這些根)。"
               "屆時本測試會 XPASS,而 strict=True 讓 XPASS 算失敗 —— "
               "強迫有人回來刪掉這個 marker,而不是讓一條長期紅的測試變成噪音。")
    @pytest.mark.parametrize("path", ["/srv/x", "/data/x", "/backup/x"])
    def test_an_unlisted_root_should_be_visible_to_level_two(self, path):
        """**斷言的是期望行為,不是現況。**

        ABS_PATH 的 POSIX 分支是白名單(`home|tmp|var|etc|usr|opt|mnt|root`),
        `/srv`、`/data`、`/backup` 這些不在名單上的根本不被視為絕對路徑 ——
        第二級看不到它們。**那不是豁免放行,是沒進視野**:
        豁免是「看到了但決定放行」(可逐條檢視),沒進視野是「判斷根本沒發生」。

        改成通用 `/…` 會不會誤擋(URL、指令旗標)未評估過,不在本輪動。
        """
        assert g1.level2_hit("rm -rf %s" % path, r"c:\proj") is not None, path

    @pytest.mark.parametrize("path", [
        "/tmp/x",
        "/tmp",
        "/var/tmp/x",
        "/var/tmp",
        "/dev/null",
        "/proc/self/fd",
        r"C:/Users/somebody/AppData/Local/Temp/claude/session/scratchpad/x",
        r"C:\Users\other\AppData\Local\Temp\claude\y",
    ])
    def test_system_scratch_areas_are_exempt(self, path):
        """試營運誤擋 #1:在暫存區刪東西是日常,不是災難。

        POSIX 的 `/tmp` 本來就豁免,Windows 的對應物沒有 —— 那不是判準不同,
        是清單沒補齊。用**路徑片段**比對而不是完整前綴:Windows 暫存路徑帶
        使用者名稱,寫死前綴就綁死一個人的機器,而 G1 是跟著人走的。
        """
        assert g1.level2_hit("rm -rf %s" % path, r"c:\proj") is None, path

    def test_a_path_that_merely_mentions_temp_is_not_exempt(self):
        """`D:/my_temp_photos` 不是暫存區 —— 片段比對帶著路徑分隔符,不是裸字串。"""
        hit = g1.level2_hit(r"rm -rf D:/my_temp_photos", r"c:\proj")
        assert hit is not None, "只是名字裡有 temp 就被當成暫存區"

    def test_the_precondition_fails_towards_blocking(self):
        """`_is_scratch` 要求傳入已小寫、已正規化的路徑。違約時**往安全方向倒**。

        違約 -> 比對不到 -> 回 False -> 第二級命中 -> **擋下**。
        表現成誤擋,看得見、會被抱怨、會被修 —— 不是靜默放行。

        **只講契約不講方向是不夠的**:方向決定緊急程度(F-042 的教訓)。
        這條測試釘住的是方向,不是契約本身。
        """
        assert g1._is_scratch(r"C:\Users\X\AppData\Local\Temp\y") is False
        assert g1._is_scratch("/TMP/x") is False


class TestMsysAndWslFormsOfTheProjectAreProjectInternal:
    """framework-updates/79 缺陷①:MSYS / WSL 形態的專案路徑要判**專案內**。

    修前:`ABS_PATH` 擷取得到 `/c/…`(它的註解自己寫「git bash 形態」),
    但包含性判定只正規化反斜線與大小寫 —— `/c/users/...` 永遠比不上
    `c:/users/...`,於是**擷取得到卻比不上,被判專案外而擋**。
    比「擷取不到」更糟:擷取不到只是沒進視野,這裡是判斷發生了而且判錯。

    而 `variants()` 早就會做 `C:\\x → /c/x` 的互轉,只給第一級用 ——
    TSI-035 形狀:一組本該一起的知識只在一邊。修法是兩側共用同一個
    `_canon()`,一份知識一個住處。

    **每一筆負對照都來自 2026-08-25 對部署版的實證誤擋**(F-050:
    不憑推測加案例),探針編號見 framework-updates/79 票面。
    """

    PROJ = r"c:\Users\u\proj"

    @pytest.mark.parametrize("cmd", [
        "rm -rf /c/Users/u/proj/build",                # 探針 A1
        "cd /c/Users/u/proj && rm -rf build/",         # 探針 A4:cd 的路徑被判外
        "rm -rf /C/Users/u/proj/build",                # 探針 A5:大寫磁碟代號
        "rm -rf /mnt/c/Users/u/proj/build",            # 探針 B1:WSL 形態
    ])
    def test_a_posix_spelling_of_the_project_passes(self, cmd):
        assert g1.level2_hit(cmd, self.PROJ) is None, cmd

    def test_a_msys_project_dir_also_canonicalizes(self):
        """proj 那一側也要過同一個函式 —— 兩側共用才是 TSI-035 的解。"""
        assert g1.level2_hit("rm -rf C:/Users/u/proj/build",
                             "/c/Users/u/proj") is None

    @pytest.mark.parametrize("cmd", [
        "rm -rf /d/somewhere/x",       # 既有回歸集同款:真外部 MSYS
        "rm -rf /mnt/d/x",             # WSL 真外部
    ])
    def test_a_genuinely_external_posix_drive_still_blocks(self, cmd):
        """方向 B:正規化只把**專案自己**的別種寫法收進來,外部照擋。"""
        assert g1.level2_hit(cmd, self.PROJ) is not None, cmd

    def test_a_real_mnt_directory_is_not_mistaken_for_a_drive(self):
        """`/mnt/data/x` 是真的 mnt 路徑,不是磁碟形態 —— 不得被轉壞。"""
        assert g1.level2_hit("rm -rf /mnt/data/x", self.PROJ) is not None


class TestQuotedProseDoesNotPairAVerb:
    """framework-updates/79 缺陷②:引號裡的**動詞**不配對,引號裡的**路徑**照算。

    修前:動詞與路徑各自全文搜尋、無引號約束 ——
    `git commit -m "上次 rm -rf /home/x 被擋"` 的散文自己配對成擋。
    G1 擋住了「描述 G1 擋了什麼」,而 friction log 正是寫閘門行為的文件,
    這個假陽性會系統性打在它身上(量化 2026-08-25 實證,成本 = 要人開終端機)。

    收窄的只有動詞面,方向是「該放的沒放」= 維持誤擋,不會多放真操作。
    已知殘留:heredoc 內文的動詞 + 路徑仍會誤擋 —— 守備宣告在 guard docstring。
    """

    PROJ = r"c:\proj"

    @pytest.mark.parametrize("cmd", [
        'git commit -m "上次 rm -rf /home/x 被擋"',        # 探針 C2
        "git commit -m '先跑了 rm -rf /home/x 才發現'",     # 單引號同款
        'echo "rm -rf /etc/passwd 這種要擋" && git push',
    ])
    def test_a_verb_inside_quotes_is_prose_not_a_command(self, cmd):
        assert g1.level2_hit(cmd, self.PROJ) is None, cmd

    def test_a_quoted_path_after_an_unquoted_verb_still_blocks(self):
        """裁決條件 b 的關鍵反控:`rm -rf "/home/x"` 是真操作,引號路徑照算。"""
        assert g1.level2_hit('rm -rf "/home/x"', self.PROJ) is not None

    def test_unbalanced_quotes_fall_back_to_blocking(self):
        """裁決條件 a:引號掃描失敗(未閉合)→ 退回現行為,往擋的方向倒。

        掃不動就當作沒有引號 —— 誤差方向是維持誤擋(看得見、會被抱怨),
        不是靜默放行。與 `_is_scratch` 契約違約的方向同一條。
        """
        assert g1.level2_hit('echo "oops && rm -rf /home/x',
                             self.PROJ) is not None

    def test_an_escaped_quote_inside_double_quotes_does_not_end_the_span(self):
        r"""`"…\"…rm…"` —— 跳脫的雙引號不結束區間,動詞仍在散文裡。"""
        assert g1.level2_hit(
            'git commit -m "他說 \\"rm -rf /home/x\\" 被擋"',
            self.PROJ) is None
