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
