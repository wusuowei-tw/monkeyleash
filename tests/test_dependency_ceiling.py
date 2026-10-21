# -*- coding: utf-8 -*-
"""票 34 —— pytest 版本上限,以及讓上限過期時**會出聲**的機制。

裁決選 A(設上限)。A 的代價票面寫得很清楚:

    上限會過期。而過期的上限**不會出聲** —— 它只是安靜地擋住升級,
    直到有人去查為什麼裝不上新版。

所以「設上限」不是一行相依宣告就結束的事:光設上限只是**把靜默換個地方** ——
從「兩台機器版本不同」換成「新版裝不上而沒人知道為什麼」。
這一檔就是那個「會出聲」的部分。

三條各守一件事:

1. 上限**還在**(有人把它刪掉會紅)
2. **實際裝的**那一版落在宣告的區間裡(繞過宣告硬裝會紅)
3. 複審日**還沒過**(到期會紅,並給出複審程序)

刻意不用 `tomllib`:`requires-python` 是 `>=3.10`,而 `tomllib` 是 3.11 才進標準庫。
在 3.10 上 `skip` 掉等於這一檔在最舊的支援版本上靜靜消失 —— 那正是本檔在防的東西。
兩個要讀的值都是單行、格式由本 repo 自己定,直接讀原文比引入版本分歧安全。
"""
from __future__ import annotations

import datetime as _dt
import re
import sys
import types
from pathlib import Path

import pytest

PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"

# ─────────────────────────────────────────────────────────────────────────────
# 有上限的相依 —— **一份清單,三條測試各自 parametrize 過來**(票 101 加 mcp)
#
# **為什麼是表不是複製一份**:票 101 加 `mcp` 時的第一個念頭是把下面三條
# 各複製一份改字串。那會得到兩組**語意相同的實作**,而
# **同缺陷的兩份實作必然漂開**(`F-058` 家族)—— 改了 pytest 那組的訊息、
# 忘了 mcp 那組,而兩組都還是綠的。
#
# ⚠ **代價明寫**:parametrize 之後這三條的 test id 從
# `test_x` 變成 `test_x[pytest]` / `test_x[mcp]`。
# 舊 id 出現在 `.dev/test-runs.jsonl` 的歷史 `failed_tests` 裡,**那些不會回頭改**
# —— 查舊紀錄的人會找不到現在的名字。本檔在 manifest 標 `skip`,
# 所以影響只在上游,不會傳到下游。
CAPPED = ("pytest", "mcp")

# 宣告形如:"pytest>=8.0,<10" / "mcp>=1.27,<2"
def _spec_re(name: str) -> re.Pattern:
    return re.compile(
        r'"%s>=(?P<low>[0-9][0-9.]*),<(?P<high>[0-9][0-9.]*)"' % re.escape(name)
    )


def _review_re(name: str) -> re.Pattern:
    return re.compile(
        r'^%s-ceiling-review\s*=\s*"(?P<date>\d{4}-\d{2}-\d{2})"' % re.escape(name),
        re.M,
    )


def _howto(name: str) -> str:
    return (
        "複審程序(票 156 的鎖定檔流程;票 157 起不再直接升級套件):\n"
        "  1. 改 .claude/portable/gates-lock*.txt 裡 %s 的版本與 hash(要連網,先取得 Jeff 授權)\n"
        "  2. 經 Jeff 同意後重建環境:setup_gates_env.py <repo> --profile upstream\n"
        "  3. runtime_identity.py --whoami --repo <repo> --profile upstream,確認 identity: ok\n"
        "  4. 用 .venv-gates 的 python 跑全套 `-m pytest`\n"
        "  5. 全綠 -> 最後才把 pyproject.toml 的上限與複審日**一起**往上推\n"
        "     有紅 -> 上限留著,把紅的成因寫進那張票,複審日往後推並註明理由\n"
        "不要只改日期不做 1-4 步 —— 那會把這條測試變成一個沒有內容的儀式。" % name
    )


# 相容名:舊寫法只有 pytest 一個,留著讓既有引用不斷。
SPEC_RE = _spec_re("pytest")
REVIEW_RE = _review_re("pytest")
_HOWTO = _howto("pytest")


def _text() -> str:
    return PYPROJECT.read_text(encoding="utf-8")


def _version_tuple(v: str) -> tuple[int, ...]:
    return tuple(int(p) for p in v.split(".") if p.isdigit())


def _installed(name: str) -> str:
    """**問套件中繼資料,不問模組的 `__version__`。**

    `pytest.__version__` 只對 pytest 管用,而這一族要對每個相依都問得出來。
    更要緊的是:`__version__` 是**模組自己說的**,中繼資料是**安裝器寫的** ——
    這條測試守的正是「宣告」與「實際裝的」對不對得上,
    所以要問**安裝器那一側**,不能問被裝的東西自己(`F-153`:材料不能從被量的對象身上拿)。
    """
    from importlib.metadata import version

    return version(name)


@pytest.mark.parametrize("name", CAPPED)
def test_dependency_declares_an_upper_bound(name: str) -> None:
    """上限被刪掉時要紅。

    這是三條裡唯一守「決定本身」的:另外兩條都預設上限存在。
    """
    m = _spec_re(name).search(_text())
    assert m is not None, (
        "pyproject.toml 的 dev 相依讀不到 `%s>=X,<Y` 形狀的宣告。\n"
        "要嘛上限被拿掉了,要嘛格式改了而這條測試沒跟著改。\n"
        "兩種都不能靜靜過去 —— 上限沒了,兩台機器就會再次跑不同的大版本(票 34)。"
        % name
    )


@pytest.mark.parametrize("name", CAPPED)
def test_installed_version_is_inside_the_declared_range(name: str) -> None:
    """實際裝的那一版必須落在宣告的區間裡。

    宣告只在**透過宣告安裝**時有效。手動 `pip install -U <pkg>` 繞得過去,
    而繞過去之後一切照跑 —— 這條就是那個情況唯一的聲音。

    ⚠ **`mcp` 那一格還多守一件 pytest 那格不需要守的事**:
    `mcp` 有沒有**裝**。沒裝的話 `importlib.metadata.version` 直接丟
    `PackageNotFoundError` —— 而票 101 的 CI 紅正是「沒裝」
    (`ModuleNotFoundError: No module named 'mcp'`,run 33720175725)。
    """
    m = _spec_re(name).search(_text())
    assert m is not None, "先看 test_dependency_declares_an_upper_bound[%s]" % name
    low, high = _version_tuple(m["low"]), _version_tuple(m["high"])
    got = _installed(name)
    installed = _version_tuple(got)

    assert low <= installed < high, (
        "實際安裝的 %s %s 落在宣告區間 [>=%s, <%s) 之外。\n"
        "宣告只約束「照宣告安裝」的路徑,手動升級繞得過去 —— 這條是那個情況的聲音。\n"
        "如果是刻意要試新大版本,那就是一次複審:\n%s"
        % (name, got, m["low"], m["high"], _howto(name))
    )


@pytest.mark.parametrize("name", CAPPED)
def test_ceiling_review_date_has_not_passed(name: str) -> None:
    """複審日到了就紅 —— 這是「上限過期會出聲」的那個機制本身。

    一條會在某天自己轉紅的測試是刻意的:上限的危害正是**它不會自己出聲**,
    而唯一不依賴外部網路、不依賴有人想起來的辦法,就是讓時間本身當觸發器。
    """
    m = _review_re(name).search(_text())
    assert m is not None, (
        "pyproject.toml 讀不到 `%s-ceiling-review = \"YYYY-MM-DD\"`。\n"
        "沒有複審日的上限就是一個不會出聲的上限(票 34 的整個代價都在這裡)。"
        % name
    )
    review = _dt.date.fromisoformat(m["date"])
    today = _dt.date.today()

    assert today <= review, (
        "%s 上限的複審日 %s 已經過了(今天 %s)。\n"
        "這條紅燈不是壞掉,是它在做它被寫出來要做的事。\n%s"
        % (name, review, today, _howto(name))
    )


# ─────────────────────────────────────────────────────────────────────────────
# 票 157 —— mcp 複審(2026-10-20)
#
# (A) 複審程序必須走票 156 的鎖定檔流程。舊版第一步是 `pip install -U`,
#     在 `.venv-gates` 裡照做,已安裝版本就偏離鎖定檔,`runtime_identity` 判 FAIL ——
#     **照著紅燈訊息做,反而把閘門環境弄壞**。
# (B) 驗收 2:不改系統時間,只換掉本模組的日期來源 `_dt`,
#     證明新複審日之下 11/1 綠、複審日當天綠、隔天紅。

_PIP_UPGRADE_RE = re.compile(r"pip\s+install\b[^\n]*?(?:\s-U\b|--upgrade\b)", re.I)
_NEGATION = ("不要", "不得", "不再", "勿", "禁止", "別")


def test_t157_howto_walks_the_lock_file_flow_in_order() -> None:
    """改鎖定檔 → 重建 `.venv-gates` → 核對身分,三步要依序出現。

    判定用**第一次出現的位置**比先後:第一次提到鎖定檔必須早於第一次提到重建,
    第一次提到重建必須早於第一次提到身分核對。只檢查關鍵字有沒有出現,
    擋不住「三步都提了但順序顛倒」—— 先重建再改鎖定檔,重建出來的還是舊版。
    """
    text = _howto("mcp")
    lock = text.find("gates-lock")
    hits = [i for i in (text.find("setup_gates_env"), text.find(".venv-gates")) if i >= 0]
    rebuild = min(hits) if hits else -1
    whoami = text.find("runtime_identity")
    ok = text.find("identity: ok")

    assert lock >= 0, "複審程序沒有提到鎖定檔(gates-lock):\n%s" % text
    assert rebuild >= 0, "複審程序沒有提到重建環境(setup_gates_env / .venv-gates):\n%s" % text
    assert whoami >= 0 and ok >= 0, \
        "複審程序沒有提到身分核對(runtime_identity 與 identity: ok):\n%s" % text
    assert lock < rebuild < min(whoami, ok), (
        "三步的順序不對(位置:鎖定檔 %d、重建 %d、身分 %d/%d):\n%s"
        % (lock, rebuild, whoami, ok, text)
    )


def test_t157_howto_never_instructs_pip_install_upgrade() -> None:
    """沒有任何一步叫人直接 `pip install -U`。

    判定方式(**逐行的字面啟發式,不是語意判定**):含 `pip install … -U/--upgrade`
    的那一行,必須同時帶否定詞(`_NEGATION`)才算「引用或警告」;
    沒有否定詞就當成指示,判錯。所以「不要用 `pip install -U`」這種句子不會誤判;
    而把指示和否定詞硬塞在同一行,這條測試擋不住 —— 那要靠人讀。
    """
    text = _howto("mcp")
    offending = [line for line in text.splitlines()
                 if _PIP_UPGRADE_RE.search(line) and not any(n in line for n in _NEGATION)]
    assert not offending, (
        "複審程序仍有一行在指示 `pip install -U`(在 .venv-gates 裡照做會讓身分判 FAIL):\n%s"
        % "\n".join(offending)
    )


def _fixed_dt(day: _dt.date):
    """一個 `_dt` 替身:`date.today()` 固定回 `day`,其餘行為與 `datetime.date` 相同。"""
    class _FixedDate(_dt.date):
        @classmethod
        def today(cls):
            return day
    return types.SimpleNamespace(date=_FixedDate)


@pytest.mark.parametrize("today, should_pass", [
    ("2026-11-01", True),    # 舊複審日的隔天:票 157 要讓它仍綠
    ("2027-01-31", True),    # 新複審日當天(`today <= review`,含等號)
    ("2027-02-01", False),   # 新複審日隔天:機制必須仍會紅
])
def test_t157_mcp_review_date_acceptance(monkeypatch, today: str, should_pass: bool) -> None:
    """驗收 2:只替換本模組的 `_dt`,呼叫原本那條測試。

    第三格(會紅)同時證明替身真的生效 —— 真實的今天會讓它綠,
    所以它紅的唯一原因是 `today()` 被換掉了。
    """
    monkeypatch.setattr(sys.modules[__name__], "_dt", _fixed_dt(_dt.date.fromisoformat(today)))
    if should_pass:
        test_ceiling_review_date_has_not_passed("mcp")
    else:
        with pytest.raises(AssertionError):
            test_ceiling_review_date_has_not_passed("mcp")
