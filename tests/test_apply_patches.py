# -*- coding: utf-8 -*-
"""票 06 — 本地 patch 的重套。

patch 的價值全在**冪等**與**可回復**:`npx skills update` 會把正典整份還原,
wrapper 的第二步就是重跑這支。它若不冪等,重跑會疊出兩份;
它若在被蓋掉後套不回來,那段內容就靜默消失了(F-002)。

錨點消失時**丟例外要人來看,不猜** —— 猜錯的話 patch 會插在錯的位置,
字串全在、檢查全綠、內容卻掛在錯的地方(F-002 補記的那個真缺口)。
"""

import importlib.util
import io
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "apply_patches_under_test", ROOT / ".claude" / "patches" / "apply_patches.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ap = _load()

UPSTREAM_GRILL = ("---\nname: grill-with-docs\n---\n\n"
                  "Run a `/grilling` session.\n")


@pytest.fixture
def grill(tmp_path, monkeypatch):
    p = tmp_path / "SKILL.md"
    p.write_text(UPSTREAM_GRILL, encoding="utf-8")
    monkeypatch.setattr(ap, "TARGET_GRILL", str(p))
    return p


def _count(p):
    return io.open(p, encoding="utf-8").read().count("LOCAL OVERRIDE (question triage)")


def test_the_patch_is_applied_to_a_pristine_upstream_file(grill):
    ap.patch_grill_question_triage()
    assert _count(grill) == 1
    assert "先查清" in io.open(grill, encoding="utf-8").read()


def test_the_upstream_content_survives(grill):
    """插入不得吃掉上游的內容 —— 那會讓 skill 本身失效,而且沒有東西會說。"""
    ap.patch_grill_question_triage()
    assert "Run a `/grilling` session." in io.open(grill, encoding="utf-8").read()


def test_running_twice_does_not_stack(grill):
    """wrapper 每次 update 後都會重跑 —— 不冪等的話會疊出兩份。"""
    ap.patch_grill_question_triage()
    ap.patch_grill_question_triage()
    ap.patch_grill_question_triage()
    assert _count(grill) == 1


def test_it_comes_back_after_upstream_overwrites_it(grill):
    """`npx skills update` 把正典整份還原 —— 重套要拿得回來,這是整支腳本的存在理由。"""
    ap.patch_grill_question_triage()
    grill.write_text(UPSTREAM_GRILL, encoding="utf-8")   # 模擬上游覆蓋
    assert _count(grill) == 0
    ap.patch_grill_question_triage()
    assert _count(grill) == 1


def test_a_missing_target_fails_loudly_instead_of_silently_skipping(tmp_path, monkeypatch):
    """檔案不在就出聲。靜默跳過的話,wrapper 全綠而 patch 根本沒套上。"""
    monkeypatch.setattr(ap, "TARGET_GRILL", str(tmp_path / "nope.md"))
    with pytest.raises(SystemExit):
        ap.patch_grill_question_triage()
