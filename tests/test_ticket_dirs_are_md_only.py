# -*- coding: utf-8 -*-
"""票目錄裡不得有 `<數字>-` 開頭的**非 `.md`** 檔(票 114 刀三,步驟 5)。

## 這條守的是步驟 4 那句規範的**另一半**

票 114 刀三給 `gate.ticket_untested_modules` 加了 `.md` 過濾,理由是
**那一層是判定**(發 R3 豁免),範圍不得寬於 `status` / `mcp` 那兩份。

**但「gate 只看 `.md`」自己會製造一個新的靜默**:
從此一個 `<號>-x.txt` 放在票目錄裡,**gate 看不到、status 看不到、mcp 看不到** ——
它變成一個**沒有人看的東西**,而放它進去的人不會知道。

所以規範有兩半,缺一不可:

    (前半)判定只認 `.md`             —— 由 `gate.py` 的過濾 + 對帳測試守
    (後半)票目錄裡就不該有非 `.md`   —— **由本檔守**

**只做前半的話,fail-open 換成了 fail-silent** —— 前者會發錯豁免,
後者會讓一份寫好的東西無聲消失。兩種都不行,而後者更難發現。

## ⚠ 判準只管 `<數字>-` 開頭的檔

票目錄裡放 `README.md`、`.gitkeep`、`NOTES.txt` 這類**不長得像票**的東西不歸本條管 ——
它們不會被任何一份找檔實作命中(三份都要求 `<號>-` 前綴),
所以它們不是「沒有人看的東西」,是「本來就不是票」。

**本條只抓那個危險的交集**:長得像票(`<數字>-` 開頭)、
而三份實作都看不到(非 `.md`)。

## 目錄從哪裡來

從 `gate.TICKET_DIRS` 展開,**不重述那份清單** —— 重述就會漂
(`status._ticket_dirs` 的 docstring 記過同一句)。
`feature` 從 `.dev/pipeline.json` 讀;讀不到就把兩個模板對**所有**現存的
一層子目錄展開,不因為讀不到就跳過(**跳過會讓本條在最需要它的時候靜音**)。
"""

import importlib.util
import io
import json
import os
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

NUM_PREFIX = re.compile(r"^\d+-")


def _load_gate():
    spec = importlib.util.spec_from_file_location(
        "gate_for_ticket_dirs", ROOT / ".claude" / "hooks" / "gate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gate = _load_gate()


def _features():
    """要檢查哪些 feature。

    先讀 `.dev/pipeline.json`;讀不到**不跳過** —— 改成把模板的 `%s` 位置
    當成萬用,列出該層底下**所有**現存目錄。
    `.dev/` 被 gitignore,CI 上那個檔是 `install.py` 產的,
    所以「讀不到」在別的環境是常態,而**跳過會讓本條在那裡恆綠**
    (「一個從來不會紅的綠燈是空的」,票 58 判準)。
    """
    feats = set()
    try:
        with io.open(str(ROOT / ".dev" / "pipeline.json"), encoding="utf-8") as f:
            f_ = json.load(f).get("feature")
        if f_:
            feats.add(f_)
    except Exception:
        pass

    for tmpl in gate.TICKET_DIRS:
        head = tmpl.split("%s")[0]
        base = ROOT / head.replace("/", os.sep) if head else ROOT
        try:
            for name in os.listdir(str(base)):
                if os.path.isdir(os.path.join(str(base), name)):
                    feats.add(name)
        except OSError:
            continue
    return sorted(feats)


def _ticket_dirs():
    """`gate.TICKET_DIRS` 展開後**存在**的目錄。回 [(相對路徑, 絕對路徑), ...]。"""
    out = []
    for feature in _features():
        for tmpl in gate.TICKET_DIRS:
            rel = tmpl % feature
            d = ROOT / rel.replace("/", os.sep)
            if d.is_dir():
                out.append((rel, str(d)))
    return out


# ── 適用性判斷 —— **獨立於上面那個掃描器** ──────────────────────────────────
#
# 這段的存在理由,以及它為什麼不能用 `_ticket_dirs()` 的回傳值,
# 寫在 `_a_ticket_directory_exists_on_disk` 的 docstring 裡。**先讀那一段再改這裡。**

# 直接寫死的磁碟位置。**刻意與 `gate.TICKET_DIRS` 重複** —— 買的就是獨立性。
# 漂掉的話由 `test_the_independent_condition_still_matches_the_templates` 出聲,
# 那是**吵的**;共用一份的話漂掉是**靜默的**。
_TICKET_DIR_SHAPES = (
    ("docs/tickets", None),        # docs/tickets/<feature>/
    (".scratch", "issues"),        # .scratch/<feature>/issues/
)


def _a_ticket_directory_exists_on_disk():
    """這個 repo 到底有沒有票目錄。**直接看磁碟,不問掃描器。**

    ## 為什麼不能用 `_ticket_dirs()` 的回傳值來決定

    **那等於讓被測對象決定要不要測它。** 掃描器壞掉時會回 0 個目錄,
    而用它當跳過條件的話,結果會是 **skip 而不是紅** ——
    正是這條反控本來要防的事(掃描器壞了,而沒有東西說話)。

    「這個判斷要獨立於被它決定的那個東西」與 `CLAUDE.md` 的
    **「這次量測的輸入,有沒有一部分是從被量的東西身上拿的?」** 是同一條:
    材料來自被量的對象 ⇒ 只證明得了自洽。

    ## 為什麼形狀要寫死到 `<feature>/issues` 這一層

    `.scratch/` 這一層**在淨室裡是存在的** —— `verify_gates.py:136` 會在目標 repo
    寫 `.scratch/verify/spec.md`。所以「`.scratch/` 在不在」分不出「有沒有票目錄」,
    要問的是 `.scratch/<feature>/issues/` 在不在。
    (這一格是實測撞出來的,不是設計出來的:第一版差點寫成只看 `.scratch/`。)
    """
    for head, tail in _TICKET_DIR_SHAPES:
        base = ROOT / head
        if not base.is_dir():
            continue
        try:
            names = os.listdir(str(base))
        except OSError:
            continue
        for name in names:
            d = base / name if tail is None else base / name / tail
            if d.is_dir():
                return True
    return False


WHY_NOT_APPLICABLE = (
    u"此 repo 沒有票目錄(`docs/tickets/` 在 portable-manifest 標 skip,"
    u"不隨安裝出貨;`.scratch/<feature>/issues/` 也不由安裝器建立)—— "
    u"本檢查不適用。**這是「不適用」不是「壞掉」**:"
    u"票目錄的存在是這個 repo 的**資料**,不是框架的性質,"
    u"而框架測試只能斷言框架的性質(淨室 verify_gates 的收尾判準)。"
)


def _skip_unless_this_repo_has_tickets():
    """兩條(衛生 + 反控)**共用同一個獨立條件**,不各判各的。

    各判各的話,兩條的適用範圍會漂開,而漂開時**兩條都還是綠的**。
    """
    if not _a_ticket_directory_exists_on_disk():
        pytest.skip(WHY_NOT_APPLICABLE)


def test_the_scan_actually_looks_at_something():
    """**反控:先證明底下那條真的掃到了目錄。**

    掃到 0 個目錄時底下那條會**恆綠**,而恆綠的斷言與有效的斷言
    在測試輸出上長得一模一樣。

    ⚠ **本條只在「這個 repo 有票目錄」時適用。**
    在剛裝好的 repo 裡沒有票目錄是**正常的**(它還沒開過票),
    而原本這裡寫的是無條件斷言 —— 於是它在淨室裡紅了
    (票 114,run `34178844263`)。**那條紅是對的,錯的是斷言**:
    它斷言的是「這個 repo 有票」= **資料**,而框架測試只能斷言**框架的性質**。
    """
    _skip_unless_this_repo_has_tickets()
    dirs = _ticket_dirs()
    assert dirs, (
        "磁碟上有票目錄,而掃描器一個都沒展開出來 —— **掃描器壞了**。"
        "(適用性由 `_a_ticket_directory_exists_on_disk()` 獨立判定,"
        "所以這裡不會因為掃描器回 0 而變成 skip。)"
        "TICKET_DIRS=%r,features=%r" % (gate.TICKET_DIRS, _features()))


class TestTheSkipConditionIsIndependentOfTheScanner:
    """**釘住那個關鍵條件:跳不跳過,不得由掃描器決定。**

    弄錯的話這次的修等於白修:掃描器壞掉回 0 ⇒ 變成 skip 而不是紅,
    而**一條 skip 掉的測試與一條沒寫的測試,在輸出上長得一模一樣**。
    """

    def test_a_broken_scanner_is_red_not_skipped(self, monkeypatch):
        """磁碟有票目錄、而掃描器回 0 ⇒ **必須紅**,不得 skip、不得綠。

        造法:磁碟不動,把 `gate.TICKET_DIRS` 清空(行程內注入,
        monkeypatch 自動還原)—— 掃描器因此回 0,而獨立條件仍然為真。

        ⚠ **本條自己也要走同一個適用性條件。** 它的前提是「這個 repo 有票目錄」,
        而那是**資料**不是框架性質 —— 與它守護的那條犯的是同一個錯。
        (實測:第一版沒加,淨室當場再紅一次。**修好一個守衛之後,
        要回頭問它自己的守衛有沒有同一個病** —— `F-085` 的同檔同類那一圈。)
        """
        _skip_unless_this_repo_has_tickets()
        assert _a_ticket_directory_exists_on_disk(), (
            "前提不成立:這個 repo 現在沒有票目錄,本條無從證明任何事")
        monkeypatch.setattr(gate, "TICKET_DIRS", ())
        assert _ticket_dirs() == [], "注入沒生效,掃描器仍回得出目錄"

        try:
            test_the_scan_actually_looks_at_something()
        except AssertionError:
            return                                    # 正確:紅
        except BaseException as e:                    # pytest.skip 也走這裡
            pytest.fail(
                u"掃描器壞掉時應該**紅**,實得 %s:%s —— "
                u"跳過條件八成又用了掃描器的回傳值" % (type(e).__name__, e))
        pytest.fail(u"掃描器壞掉時應該**紅**,實得:通過")

    def test_a_scanner_based_condition_would_have_been_caught(self, monkeypatch):
        """**反控的反控**:證明上一條真的分得出兩種寫法。

        少了它,上一條可能因為別的理由通過。這裡把「錯的寫法」
        (拿掃描器的回傳值當適用性條件)就地寫出來,證明在同一個注入下
        它與獨立條件**給出相反的答案**。

        ⚠ 同上:本條的前提也是「這個 repo 有票目錄」,所以走同一個適用性條件。
        """
        _skip_unless_this_repo_has_tickets()
        monkeypatch.setattr(gate, "TICKET_DIRS", ())
        wrong = bool(_ticket_dirs())                  # 錯的寫法:問掃描器
        right = _a_ticket_directory_exists_on_disk()  # 對的寫法:問磁碟
        assert wrong is False and right is True, (
            u"這個注入分不出兩種寫法,上一條因此沒有資訊量:"
            u"掃描器說 %r,磁碟說 %r" % (wrong, right))

    def test_the_independent_condition_still_matches_the_templates(self):
        """寫死的形狀與 `gate.TICKET_DIRS` **漂開時要出聲**。

        `_TICKET_DIR_SHAPES` 刻意重複了模板的知識(買的是獨立性),
        而重複必然漂(`F-058` 家族)。這條把漂變成吵的。
        """
        shapes = set()
        for head, tail in _TICKET_DIR_SHAPES:
            shapes.add("%s/%%s" % head if tail is None else "%s/%%s/%s" % (head, tail))
        assert shapes == set(gate.TICKET_DIRS), (
            u"獨立條件的形狀與 gate.TICKET_DIRS 漂開了:"
            u"本檔 %r,gate %r —— 兩邊都要改" % (sorted(shapes), sorted(gate.TICKET_DIRS)))

    def test_a_repo_without_ticket_dirs_skips_instead_of_failing(
            self, tmp_path, monkeypatch):
        """**這一格就是淨室紅掉的那一格**(票 114,run `34178844263`)。

        剛裝好的 repo 沒有票目錄(`docs/tickets/` 標 skip 不出貨),
        而修法之前這裡是無條件斷言,於是它在那裡**紅**——
        「那些紅與新專案無關,會訓練人忽略訊號」(淨室收尾判準)。

        造法:把 `ROOT` 指到一個空的 tmp,磁碟上因此沒有任何票目錄。
        """
        import sys as _sys
        monkeypatch.setattr(_sys.modules[__name__], "ROOT", tmp_path)
        assert not _a_ticket_directory_exists_on_disk()

        try:
            test_the_scan_actually_looks_at_something()
        except AssertionError as e:
            pytest.fail(u"沒有票目錄時應該 **skip**,實得紅:%s" % e)
        except BaseException as e:
            assert type(e).__name__ == "Skipped", (
                u"應該 skip,實得 %s:%s" % (type(e).__name__, e))
            return
        pytest.fail(u"沒有票目錄時應該 **skip**,實得:通過(那是靜默的空綠)")

    def test_the_skip_message_says_which_and_why(self):
        """skip 訊息要讓人分得出「不適用」與「壞掉」。

        只寫「skipped」的話,一個真的壞掉的環境看起來與一個正常的新 repo 一樣。
        """
        for needle in (u"沒有票目錄", u"不適用", u"skip", u"資料", u"框架的性質"):
            assert needle in WHY_NOT_APPLICABLE, needle


def test_no_ticket_shaped_file_is_invisible_to_every_implementation():
    """`<數字>-` 開頭但不是 `.md` 的檔案 = 沒有人看得到的東西。

    三份找檔實作(`gate.ticket_untested_modules` /
    `status._find_ticket_file` / `mcp_server._ticket_path`)現在都要求
    `<號>-` 前綴**且** `.md` 結尾。所以這種檔案:

      - 對 gate 不存在  -> 它裡面的 `Untested by decision` 宣告不會發豁免
      - 對 status 不存在 -> 不會出現在 `ticket file` 那一行
      - 對 mcp 不存在    -> `ticket(n)` 讀不到它

    **而放它進去的人不會知道。** 這條就是那個會說話的東西。

    ⚠ **與上面那條反控共用同一個適用性條件**(`_skip_unless_this_repo_has_tickets`)。
    各判各的話兩條的適用範圍會漂開,**而漂開時兩條都還是綠的**。
    """
    _skip_unless_this_repo_has_tickets()
    bad = []
    for rel, d in _ticket_dirs():
        for name in sorted(os.listdir(d)):
            if not os.path.isfile(os.path.join(d, name)):
                continue
            if NUM_PREFIX.match(name) and not name.endswith(".md"):
                bad.append("%s/%s" % (rel, name))
    assert not bad, (
        "這些檔案長得像票(`<數字>-` 開頭)但**不是 `.md`**,"
        "三份找檔實作一份都看不到它們(%d 個):\n  %s\n"
        "出口:改成 `.md`,或改名讓它不要以 `<數字>-` 開頭。"
        % (len(bad), "\n  ".join(bad)))


class TestTheCriterionItselfIsRight:
    """釘住判準本身,不只釘住現況為空。

    現況是 0 個違規(2026-09-08 實測),所以上面那條**現在恆綠** ——
    它要到有人放進一個 `<號>-x.txt` 才會第一次咬。
    在那之前,守著「判準沒被改鬆」的是這一組。
    """

    @pytest.mark.parametrize("name,expected", [
        (u"114-a.txt", True),        # 危險的交集
        (u"01-x.rst", True),
        (u"7-notes.TXT", True),
        (u"114-c.md", False),        # 正常的票
        (u"README.md", False),       # 不長得像票
        (u"NOTES.txt", False),       # 不長得像票 -> 不歸本條管
        (u".gitkeep", False),
        (u"x114-e.md", False),       # 號碼不在開頭
    ])
    def test_which_names_count_as_a_violation(self, name, expected):
        got = bool(NUM_PREFIX.match(name)) and not name.endswith(".md")
        assert got is expected, name

    def test_a_plain_txt_without_the_number_prefix_is_deliberately_allowed(self):
        """**這一格是刻意的,寫出來免得被當成漏洞。**

        `NOTES.txt` 不會被任何一份找檔實作命中(三份都要 `<號>-` 前綴),
        所以它不是「沒有人看的東西」,是「本來就不是票」。
        把它也擋掉會讓本條變成一條目錄潔癖規則,而那會擋到做對事的人。
        """
        assert not NUM_PREFIX.match(u"NOTES.txt")
