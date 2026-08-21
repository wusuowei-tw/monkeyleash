# -*- coding: utf-8 -*-
"""票 04 — CLAUDE.md 的框架段與專案段。

**查證後的事實**:目前這份 CLAUDE.md 裡**沒有任何專案專屬內容**,
七個小節全是框架規範。票裡原本寫「它同時裝著框架規範與台股專屬規範」——
那是我沒查證就寫下的前提,不成立。

所以本票的實質不是拆內容,是**建立那道界線**:
標記出框架段,讓將來加進去的專案規範有一個**明確不會被帶走**的位置。
沒有這道界線的話,某天有人在 CLAUDE.md 裡寫下「台股的收盤時間是 13:30」,
它會靜默跟著裝進別的專案,而 agent 會照那條規矩工作 —— **那不會報錯**。
"""

import importlib.util
import io
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "claude_md_under_test", ROOT / ".claude" / "portable" / "claude_md.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


claude_md = _load()

SAMPLE = (
    "# 專案開發規範\n\n"
    "<!-- FRAMEWORK:BEGIN -->\n"
    "## 開發流程\n框架規矩。\n"
    "<!-- FRAMEWORK:END -->\n\n"
    "## 這個專案自己的\n收盤 13:30。\n"
)


def test_the_framework_section_is_what_lies_between_the_markers():
    out = claude_md.framework_section(SAMPLE)
    assert "框架規矩" in out
    assert "收盤 13:30" not in out, "專案段漏進框架段 —— 那會被裝進別的專案"


def test_missing_markers_is_an_error_not_the_whole_file():
    """讀不到界線時**不得整份帶過去**。

    退化成「整份都算框架」的話,專案規範會靜默搬家 —— 而那正是這道界線要擋的。
    這裡的 fail 方向與標記表相反:標記表往「多帶」倒(多帶是吵鬧的),
    這裡往「不帶」倒,因為帶錯的內容不會報錯,只會讓 agent 照錯的規矩工作。
    """
    with pytest.raises(ValueError):
        claude_md.framework_section("# 沒有任何標記\n內容\n")


def test_duplicate_markers_are_an_error():
    """兩組標記時取哪一組取決於實作,那是隱形的。"""
    doubled = SAMPLE + "<!-- FRAMEWORK:BEGIN -->\n又一段\n<!-- FRAMEWORK:END -->\n"
    with pytest.raises(ValueError):
        claude_md.framework_section(doubled)


def test_end_before_begin_is_an_error():
    with pytest.raises(ValueError):
        claude_md.framework_section("<!-- FRAMEWORK:END -->\nx\n<!-- FRAMEWORK:BEGIN -->\n")


def test_the_rendered_file_round_trips():
    """裝出去的 CLAUDE.md 自己也要帶著界線 —— 否則下一次安裝就找不到框架段。"""
    rendered = claude_md.render_for_new_repo(SAMPLE)
    assert claude_md.framework_section(rendered) == claude_md.framework_section(SAMPLE)


def test_the_rendered_file_leaves_a_labelled_place_for_project_rules():
    rendered = claude_md.render_for_new_repo(SAMPLE)
    assert "收盤 13:30" not in rendered, "來源的專案段被帶進新專案了"
    assert "專案" in rendered.split("FRAMEWORK:END")[-1], \
        "沒有替專案規範留下一個標明位置,人只好寫進框架段"


def test_the_shipped_claude_md_carries_the_markers():
    text = io.open(ROOT / "CLAUDE.md", encoding="utf-8").read()
    assert claude_md.framework_section(text).strip(), "本 repo 的 CLAUDE.md 沒有框架段標記"


# ─────────────────────────────────────────────────────────────────────────────
# 票 53 偵測器 I —— 正典段的可機器對照宣稱(方向二)
# ─────────────────────────────────────────────────────────────────────────────
#
# 上面七條驗的是**抽取邏輯與界線**;這一批驗的是**界線圈出來的那段內容**。
# 票 53 逐字:「抽取邏輯有測試、界線有測試,而界線圈出來的那段內容沒有。」
#
# **本檔標 `copy`,所以這一批會到下游跑。** 每一條因此都必須與
# 「這個 repo 的檔案樹」無關 —— 下游那棵樹不是上游那棵。
# 樹相依的兩條(ADR 引用、路徑分類)住在 `tests/test_canon_section.py`,
# 那支標 `skip`,不出貨。
#
# 放這裡而不是新開一支的理由:正典段的界線由 `framework_section()` 定義,
# 而那個函式的測試就在本檔 —— **判定與它的界線同居**,
# 才不會有人改了界線而忘了這一批。
#
# **枚舉,不比對。** 三條守的面都是封閉且可窮舉的(規則代號、`F-` 條目、
# 行號引用的字面形狀),所以逐一列舉:比對的漏是未知的,枚舉的漏是不存在的。

RULE_IN_TEXT = re.compile(r"\bR\d+\b")
FRICTION_ENTRY = re.compile(r"^## (F-\d+)", re.M)
# 行號引用 = 反引號裡以「冒號 + 數字」結尾的東西。**只收反引號內** ——
# 散文裡的「第 3 步」不是引用,收進來會把整批變成噪音。
LINE_REF = re.compile(r"`[^`\n]*?:\d{1,4}(?:[-–]\d{1,4})?`")


def _load_gate():
    spec = importlib.util.spec_from_file_location(
        "gate_for_canon_checks", ROOT / ".claude" / "hooks" / "gate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def canon_text():
    """本 repo 的正典段。

    **抽不出來就丟例外,不回空字串** —— `framework_section()` 已經這樣設計,
    這裡只是不要把它接住。一個對空字串跑的檢查會全部通過,
    而「掃不到東西的綠燈不算綠燈」。
    """
    return claude_md.framework_section(
        io.open(ROOT / "CLAUDE.md", encoding="utf-8").read())


def rules_named_in(text):
    """這段文字提到了哪些規則代號。"""
    return set(RULE_IN_TEXT.findall(text))


def friction_refs_in(text):
    """這段文字引用了哪些 `F-` 號(保留順序,去重)。"""
    out = []
    for r in re.findall(r"F-\d+", text):
        if r not in out:
            out.append(r)
    return out


def line_refs_in(text):
    """這段文字裡的行號引用。"""
    return LINE_REF.findall(text)


def test_the_canon_section_is_extractable_and_not_empty():
    """I-7 —— 枚舉沒壞。

    門檻**刻意不寫成 `> N`**:那是數量,而數量在別的 repo 上是另一個數字
    (`> 50` 在一棵一萬個檔的樹上是恆真式,票 53 落地驗收第三項在修那一格)。
    這裡問的是**結構**:界線抽得出來、抽出來非空、而且它真的是正典段的內容。
    """
    body = canon_text()
    assert body.strip(), "正典段抽出來是空的 —— 枚舉本身壞了,不是通過"
    assert claude_md.BEGIN not in body and claude_md.END not in body, \
        "抽出來的內容含界線標記本身 —— 抽取範圍不對"


def test_the_canon_names_no_rule_that_does_not_exist():
    """I-1a —— 正典段提到的規則都必須真的存在。

    抓的是「**刪掉一條規則而正典段沒改**」。權威來源是 `rule_codes()`,
    它從規則自己的擋下訊息掃出來,不維護對照表。
    """
    authoritative = _load_gate().rule_codes()
    assert authoritative, "`rule_codes()` 回空 —— 權威來源讀不到,不是通過"
    ghost = sorted(rules_named_in(canon_text()) - authoritative)
    assert not ghost, (
        "正典段提到了不存在的規則:%s\n"
        "規則被刪掉時,正典段沒有跟著改 —— 而那一段會跟著每一次 install 出貨。"
        % ", ".join(ghost))


def test_i1a_catches_a_rule_that_does_not_exist():
    """I-1a 的正對照 —— 拿一段含假代號的文字,判定必須指出它。"""
    fake = "| R1 | 真的 |\n| R99 | 這一條不存在 |\n"
    assert rules_named_in(fake) - {"R1", "R2"} == {"R99"}


def test_every_friction_reference_in_the_canon_resolves():
    """I-2 —— 正典段引用的每個 `F-` 號都要在 friction-log 找得到。

    抓的是「引用一則不存在的 friction」與「號碼打錯」。
    兩者在畫面上長得一樣,而**讀的人會去找,找不到才發現** —— 那時已經很晚。
    """
    entries = set(FRICTION_ENTRY.findall(
        io.open(ROOT / "docs" / "agents" / "friction-log.md",
                encoding="utf-8").read()))
    assert entries, "friction-log 一則 `## F-` 都沒枚舉到 —— 枚舉本身壞了,不是通過"
    refs = friction_refs_in(canon_text())
    assert refs, "正典段一個 `F-` 引用都沒有 —— 枚舉本身壞了,不是通過"
    bad = [r for r in refs if r not in entries]
    assert not bad, (
        "正典段引用了 friction-log 裡沒有的條目:%s\n"
        "這一段跟著 install 出貨,下游會照它去找一則不存在的紀錄。"
        % ", ".join(bad))


def test_i2_catches_a_friction_reference_that_does_not_resolve():
    """I-2 的正對照。"""
    assert friction_refs_in("見 `F-001` 與 `F-999`,以及重複的 `F-001`") == \
        ["F-001", "F-999"]


def test_the_canon_carries_no_line_number_references():
    """I-4 —— 正典段不得出現行號引用。

    **這不是「將來會漂」,是「對下游從第一天就是錯的」**:
    下游那份 `CLAUDE.md` 的行號與上游不同(上游檔含自己的專案段與標題,
    下游那份由 `render_for_new_repo()` 重組),而正典段內容兩邊相同。
    所以一個在上游指得到的行號,在下游指到別的地方。

    今天命中 0 —— **這條的價值是把這個 0 釘住**,不是修什麼。
    """
    hits = line_refs_in(canon_text())
    assert not hits, (
        "正典段出現行號引用:%s\n"
        "改法:引名不引行號(節名 / 標記字串 / 逐字原文)。\n"
        "理由不是「會過期」,是**下游那份的行號從一開始就不一樣**。"
        % ", ".join(hits))


def test_i4_catches_a_line_number_reference():
    """I-4 的正對照 —— 含區間的形態也要收。"""
    found = line_refs_in("見 `gate.py:123` 與 `install.py:34-41`,而 `第 3 步` 不是引用")
    assert found == ["`gate.py:123`", "`install.py:34-41`"]
