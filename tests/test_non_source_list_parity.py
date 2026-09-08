# -*- coding: utf-8 -*-
"""票 114 刀二 B-3 —— 兩份「目錄清單」的**差集**對帳。

## ⚠ 這條測試對的不是相等,是**刻意的差集**

`gate.NON_SOURCE_DIRS` 與 `redlight._SEARCH_SKIP` 看起來像同一份清單的兩份副本,
**它們不是**。兩份服務的判準各自寫在自己的檔案裡:

  `gate.py:119`      「判準只有一句:**會不會被執行,或被建置工具當成邏輯消費**」
                     ⇒ 消費點 `is_source_path()`,對象是 **R2/R3 要不要管這個檔**
  `redlight.py:77`   「測試檔名對應到實作檔名的**搜尋範圍**」
                     ⇒ 消費點 `find_implementation()`,對象是 **反查實作時 os.walk 要不要進去**

**讓它們相等會製造 fail-open。** 實測(2026-09-08,票 114 步驟 C-2-c):
把 `_SEARCH_SKIP` 併進 `NON_SOURCE_DIRS`,`is_source_path('.scratch/f/x.py')`
由 `True` 翻成 `False` ⇒ **`.scratch/` 底下的碼從此不受站別限制**,
而 **R7 的擋下訊息正是叫人把腳本寫到那裡**(`gate.py:986-987`)——
合併之後,那條官方出口會變成一個繞過 R2 的通道,而且是閘門自己指的路。
逐項見票面 `docs/tickets/framework-updates/114-three-things-with-two-sources.md`
的 B-3 段 F-036 更正塊。

**所以本檔釘的是「差集就是這三筆,不多不少」,不是「兩份一樣」。**

## ⚠ 順帶守住 `PROTOTYPE_RE` 不會靜默變死碼

`gate.py:145` 的 `PROTOTYPE_RE = re.compile(r"^\\.scratch/[^/]+/prototype/")`
挖掉的是 `.scratch` 的一個**子集** —— **只有在 `.scratch` 本身是原始碼時才有意義**。
`.scratch` 一旦被加進 `NON_SOURCE_DIRS`,那條正則就變成恆為冗餘,
**而它變成死碼不會有任何東西說話**。

本檔的差集斷言就是那個「會說話的東西」:`.scratch` 進了 `NON_SOURCE_DIRS`
⇒ `_SEARCH_SKIP - NON_SOURCE_DIRS` 少一筆 ⇒ **本測試紅**。

## 為什麼不抽共用常數

13 筆重疊**不是「同一個判斷的兩份副本」**,是**兩個獨立判斷碰巧同答案**
(票 114 裁決,2026-09-08:C 案不採)。抽成共用常數會把那個巧合寫成前提,
而下一次只有一邊該變的時候,共用常數會讓兩邊一起變 —— 那是更難發現的漂移。
"""

import contextlib
import importlib.util
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load(name, *parts):
    """兩側都用路徑載入(寫法抄 `tests/test_gate.py:336-343`)。"""
    spec = importlib.util.spec_from_file_location(name, ROOT.joinpath(*parts))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gate = _load("gate_for_dirs", ".claude", "hooks", "gate.py")
redlight = _load("redlight_for_dirs", ".claude", "hooks", "redlight.py")


# ── 三筆刻意的差異,與各自的理由(票 114 裁決,2026-09-08)────────────────────
#
# 形狀比照 `tests/test_gate.py::TestNonSourceListsAreWellFormed::
# test_every_entry_carries_a_reason` —— **理由欄是讓判準漂移看得見的東西**。
# 差集也一樣:一筆沒有理由的差異,與一筆漏掉的差異,在測試輸出上長得一模一樣。

ONLY_IN_GATE = {
    "scripts":
        "**未證明**是刻意還是漏的 —— `redlight.py` 全檔沒有任何註解提到 `scripts`。"
        "實測影響 0:`scripts/` 底下 1 支 .py、0 支配對測試、"
        "`.dev/test-runs.jsonl` 裡 0 筆 impl_file 落在 scripts/。保留現況不改行為。"
        "**觸發條件**:哪天 scripts/ 長出 tests/test_<name>.py 配對,這條差異要重新裁。",
}

ONLY_IN_REDLIGHT = {
    ".cache":
        "兩邊各自正確。gate 把 `.cache/x.py` 當原始碼管是**嚴格的那一側**"
        "(fail-closed);redlight 跳過它是因為**反查實作不該走進快取目錄**。"
        "兩個方向都不是 fail-open。",
    ".scratch":
        "gate 缺席是**刻意**,四處設計依賴:"
        "`gate.py:144-145` 的 PROTOTYPE_RE(挖的是 .scratch 的**子集**,"
        "只有在 .scratch 本身是原始碼時才有意義)、"
        "`gate.py:2123` R1 認 `.scratch/<f>/spec.md` 為規格書、"
        "`gate.py:1310` TICKET_DIRS 含 `.scratch/%s/issues`、"
        "`gate.py:986-987` R7 的官方出口指向 `.scratch/<feature>/`。"
        "redlight 跳過它是因為反查實作不該走進暫存區。",
}

# 兩份都有的那些。**明列,不用長度** —— 長度相等而內容不同時,
# 一個「len == 13」的斷言會綠,而那正是漂移的樣子。
IN_BOTH = {
    ".agents", ".dev", ".git", ".venv", "__pycache__", "assets", "build",
    "docs", "logs", "node_modules", "skills", "tests", "tradingagents.egg-info",
}


def _partition():
    """(只在 gate 那份, 只在 redlight 那份, 兩份都有)。**每次重讀模組屬性。**

    不快取:反控靠注入真的屬性來證明這條會咬,而快取會讓注入看不見。
    """
    g = set(gate.NON_SOURCE_DIRS)
    r = set(redlight._SEARCH_SKIP)
    return g - r, r - g, g & r


def _parity_violations():
    """差集與宣告的理由表不符的地方。回 [(哪一格, 實得, 預期), ...]。

    **回清單不回布林**:紅燈要說得出是哪一格、多了什麼少了什麼,
    否則訊息只說「差集不對」,而人要自己重算一遍才知道往哪裡看。
    """
    only_g, only_r, both = _partition()
    out = []
    if only_g != set(ONLY_IN_GATE):
        out.append(("只在 gate 那份", only_g, set(ONLY_IN_GATE)))
    if only_r != set(ONLY_IN_REDLIGHT):
        out.append(("只在 redlight 那份", only_r, set(ONLY_IN_REDLIGHT)))
    if both != IN_BOTH:
        out.append(("兩份都有", both, IN_BOTH))
    return out


@contextlib.contextmanager
def _injected(where, name):
    """把一個目錄注入其中一份,離開時還原。**動的是真的模組屬性。**

    用真的屬性而不是傳一份副本進去,是為了讓反控也能抓到
    「兩邊其實比到同一個物件」—— 那種寫法下,注入會讓**兩側同時**改變,
    差集不動,而斷言恆真。傳副本的話這個缺陷測不出來。
    """
    if where == "gate":
        table = gate.NON_SOURCE_DIRS
        assert name not in table, "語料選錯:%r 本來就在 gate 那份裡" % name
        table[name] = "(反控注入)"
        try:
            yield
        finally:
            del table[name]
    elif where == "redlight":
        table = redlight._SEARCH_SKIP
        assert name not in table, "語料選錯:%r 本來就在 redlight 那份裡" % name
        table.add(name)
        try:
            yield
        finally:
            table.discard(name)
    else:
        raise ValueError(where)


class TestTheParityCheckItselfCatchesAnInjectedDirectory:
    """**反控:先證明這個差集對帳真的會咬,兩個方向各驗一次。**

    形狀抄 `tests/test_portable_output_encoding.py::TestTheHarnessItselfRejectsTheMark`
    那一層(引 `F-103`)。少了它,底下的差集斷言可能因為**任何**理由恆真:
    差集算錯方向(`G - R` 寫成 `R - G`)、兩邊比到同一個物件、
    或斷言寫成一個永遠成立的形狀 ——
    **而恆真的斷言與有效的斷言在測試輸出上長得一模一樣。**
    """

    def test_injecting_into_the_gate_list_is_caught(self):
        with _injected("gate", "zzz_injected_dir"):
            bad = _parity_violations()
        assert bad, (
            "往 gate 那份注入一個目錄,差集對帳竟然沒抓到 —— "
            "斷言可能是恆真的,或差集算錯了方向")

    def test_injecting_into_the_redlight_list_is_caught(self):
        with _injected("redlight", "zzz_injected_dir"):
            bad = _parity_violations()
        assert bad, (
            "往 redlight 那份注入一個目錄,差集對帳竟然沒抓到 —— "
            "斷言可能是恆真的,或差集算錯了方向")

    def test_the_two_lists_are_not_the_same_object(self):
        """**兩份必須真的是兩個物件。**

        是同一個的話,上面兩條的注入會讓兩側同時改變,差集不動,反控自己也失效。
        """
        assert gate.NON_SOURCE_DIRS is not redlight._SEARCH_SKIP
        assert set(gate.NON_SOURCE_DIRS) != set(redlight._SEARCH_SKIP), (
            "兩份內容相等 —— 那正是本檔要防的 fail-open(見模組 docstring)")

    def test_the_injection_is_undone(self):
        """**反控的反控**:注入必須還原,否則後面的測試會踩到污染的狀態。"""
        before_g, before_r = dict(gate.NON_SOURCE_DIRS), set(redlight._SEARCH_SKIP)
        with _injected("gate", "zzz_undo_probe"):
            pass
        with _injected("redlight", "zzz_undo_probe"):
            pass
        assert dict(gate.NON_SOURCE_DIRS) == before_g
        assert set(redlight._SEARCH_SKIP) == before_r


class TestTheDifferenceIsExactlyWhatWasDecided:
    """**差集就是這三筆,不多不少。** 任何一邊新增目錄而另一邊沒跟上就紅。"""

    def test_only_in_gate_is_exactly_the_declared_set(self):
        only_g, _, _ = _partition()
        assert only_g == set(ONLY_IN_GATE), (
            "只在 gate 那份的目錄變了:實得 %s,宣告 %s。\n"
            "多出來的要嘛補進理由表(附為什麼 redlight 不需要它),"
            "要嘛是漏加到 redlight 那份。" % (sorted(only_g), sorted(ONLY_IN_GATE)))

    def test_only_in_redlight_is_exactly_the_declared_set(self):
        _, only_r, _ = _partition()
        assert only_r == set(ONLY_IN_REDLIGHT), (
            "只在 redlight 那份的目錄變了:實得 %s,宣告 %s。\n"
            "⚠ 少了 `.scratch` 的話,先查它是不是被加進 NON_SOURCE_DIRS —— "
            "那會讓 .scratch/ 底下的碼脫離站別限制,而 PROTOTYPE_RE 同時變死碼。"
            % (sorted(only_r), sorted(ONLY_IN_REDLIGHT)))

    def test_the_overlap_is_exactly_the_listed_thirteen(self):
        """**明列,不用長度。** 長度相等而內容不同時,一個 `len ==` 的斷言會綠。"""
        _, _, both = _partition()
        assert both == IN_BOTH, (
            "兩份共有的目錄變了:多了 %s,少了 %s"
            % (sorted(both - IN_BOTH), sorted(IN_BOTH - both)))

    def test_the_whole_partition_agrees_at_once(self):
        """三格一起看 —— 逐格的三條各自紅時,這一條給出完整的對照。"""
        bad = _parity_violations()
        assert not bad, "\n".join(
            "%s:實得 %s,宣告 %s" % (where, sorted(got), sorted(want))
            for where, got, want in bad)

    @pytest.mark.parametrize("table_name", ["ONLY_IN_GATE", "ONLY_IN_REDLIGHT"])
    def test_every_declared_difference_carries_a_reason(self, table_name):
        """形狀比照 `TestNonSourceListsAreWellFormed::test_every_entry_carries_a_reason`。

        **一筆沒有理由的差異,與一筆漏掉的差異,在測試輸出上長得一模一樣。**
        理由欄逼人在加一筆差異時回答「為什麼另一邊不需要它」。
        """
        table = globals()[table_name]
        assert isinstance(table, dict), "%s 必須是 {目錄: 理由}" % table_name
        for key, why in table.items():
            assert isinstance(why, str) and why.strip(), (
                "%s 的 %r 沒有理由" % (table_name, key))

    def test_the_three_declared_groups_do_not_overlap(self):
        """三張表互斥 —— 同一個目錄不得同時出現在兩張,否則理由表自己就矛盾。"""
        seen = {}
        for name in ("ONLY_IN_GATE", "ONLY_IN_REDLIGHT", "IN_BOTH"):
            for key in globals()[name]:
                assert key not in seen, "%r 同時在 %s 與 %s" % (key, seen[key], name)
                seen[key] = name


class TestPrototypeReStaysAlive:
    """`PROTOTYPE_RE` 不得靜默變成死碼。

    它挖掉的是 `.scratch` 的**子集**,只有在 `.scratch` 本身是原始碼時才有意義。
    上面的差集斷言是主要的守衛(`.scratch` 進了 `NON_SOURCE_DIRS` ⇒ 差集變 ⇒ 紅);
    這裡再直接釘一次那個前提,讓紅燈**說出原因**而不只是「差集不對」。
    """

    def test_scratch_is_still_source_so_the_regex_carves_something_out(self):
        assert gate.is_source_path(".scratch/f/x.py") is True, (
            ".scratch/ 底下的 .py 不再算原始碼 —— R2 不管它了,"
            "而 R7 的擋下訊息(gate.py:986-987)正是叫人把腳本寫到那裡")
        assert gate.is_source_path(".scratch/f/prototype/try.py") is False, (
            "PROTOTYPE_RE 沒有在挖東西了")

    def test_the_regex_is_the_only_thing_making_those_two_differ(self):
        """**歸因反控**:上一條的兩個答案不同,必須是 `PROTOTYPE_RE` 造成的。

        少了這一條,`.scratch/f/prototype/try.py` 哪天因為別的理由變成非原始碼
        (例如有人把 `prototype` 加進 `NON_SOURCE_DIRS`),上一條照樣綠。
        """
        assert gate.PROTOTYPE_RE.match(".scratch/f/prototype/try.py")
        assert not gate.PROTOTYPE_RE.match(".scratch/f/x.py")
        assert "prototype" not in gate.NON_SOURCE_DIRS
        assert ".scratch" not in gate.NON_SOURCE_DIRS
