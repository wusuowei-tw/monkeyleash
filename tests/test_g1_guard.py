# -*- coding: utf-8 -*-
"""G1 —— 保護清單的帶邊界前綴比對。

這份是 repo 內的版本,正式檔在 `~/.claude/hooks/g1_guard.py`,
**只有人能覆蓋過去**(ADR 0009)。repo 內的版本受 R1–R7 管:
有測試、要在 implement 站寫、要用檔案工具寫。
放在 `~/.claude/` 底下的話這些一條都不適用 ——
**防護機制的修改反而是整個系統裡管得最鬆的地方**,那個方向是錯的。

比對方式的取捨:

  子字串(現行)  子目錄自動涵蓋 ✅  但 `D:\\notes1` 會誤中 `D:\\notes123` ❌
  帶邊界前綴      子目錄自動涵蓋 ✅  相鄰名稱不誤中 ✅

誤擋累積起來的後果是規則被關掉,而關掉的涵蓋率是零(F-031)。
"""

import importlib.util
import io
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "g1_under_test", ROOT / ".claude" / "portable" / "g1_guard.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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
        monkeypatch.setattr(g1, "PROTECTED_LIST", str(tmp_path / "gone.txt"))
        assert g1.protected_entries() is None

    def test_a_readable_list_is_parsed_without_comments(self, tmp_path, monkeypatch):
        p = tmp_path / "list.txt"
        io.open(p, "w", encoding="utf-8", newline="\n").write(
            "# 註解\n\nD:\\保管庫\nD:\\封存   # 行尾註解\n")
        monkeypatch.setattr(g1, "PROTECTED_LIST", str(p))
        assert g1.protected_entries() == ["D:\\保管庫", "D:\\封存"]


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
        reason="票 04:ABS_PATH 的 POSIX 分支是頂層目錄白名單,未列名的根目錄"
               "第二級看不見。**變綠的條件**:票 04 把它改成通用比對(或補上這些根)。"
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
