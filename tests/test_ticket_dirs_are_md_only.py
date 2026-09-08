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


def test_the_scan_actually_looks_at_something():
    """**反控:先證明這條測試真的掃到了目錄。**

    掃到 0 個目錄時上面那條會**恆綠**,而恆綠的斷言與有效的斷言
    在測試輸出上長得一模一樣。本 repo 一定至少有一個票目錄
    (`docs/tickets/<feature>/`,票就住在那裡)。
    """
    dirs = _ticket_dirs()
    assert dirs, (
        "一個票目錄都沒掃到 —— `gate.TICKET_DIRS` 展開後全部不存在?"
        "那底下那條測試是空的。TICKET_DIRS=%r,features=%r"
        % (gate.TICKET_DIRS, _features()))


def test_no_ticket_shaped_file_is_invisible_to_every_implementation():
    """`<數字>-` 開頭但不是 `.md` 的檔案 = 沒有人看得到的東西。

    三份找檔實作(`gate.ticket_untested_modules` /
    `status._find_ticket_file` / `mcp_server._ticket_path`)現在都要求
    `<號>-` 前綴**且** `.md` 結尾。所以這種檔案:

      - 對 gate 不存在  -> 它裡面的 `Untested by decision` 宣告不會發豁免
      - 對 status 不存在 -> 不會出現在 `ticket file` 那一行
      - 對 mcp 不存在    -> `ticket(n)` 讀不到它

    **而放它進去的人不會知道。** 這條就是那個會說話的東西。
    """
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
