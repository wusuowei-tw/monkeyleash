# -*- coding: utf-8 -*-
"""`.claude/portable/status.py` —— repo 證據的 projection。

**本檔是票 99 的第一筆紅燈。** 寫下它的時候 `status.py` 還不存在,
所以整份**收集錯誤**(`ModuleNotFoundError: status`)—— 那就是紅燈本身,
先例:票 98 的 `8c2d555`。

## 受測介面(本檔釘住的形狀)

    status.render(root) -> str        多行輸出,每行 `<欄>: <值>  (source: <來源>)`
    status.load_gate(root)            回傳那個 root 的 gate 模組

`load_gate` 是**刻意露出來的接縫**,不是實作細節外洩:
判準 2 說「只呼叫 `gate.py`,不重述它」,而**「有沒有真的去呼叫」從輸出看不出來** ——
一個自己偷讀 `pipeline.json` 的實作會印出一模一樣的字。
把載入那一步收成一個具名函式,測試才能換掉它、看輸出跟著變
(`test_stage_is_read_through_gate`)。**沒有這個接縫,判準 2 就只是一句話。**

## 為什麼 root 是參數而不是模組常數

裁 C:`gate.py` 的 `ROOT` 是從 `__file__` 往上三層推的模組層常數。
在 A repo 裡 import B repo 的 gate,`ROOT` 會指到 A,**而那個錯是靜默的**。
所以 `render` 吃 root、per-root 把 `<root>/.claude/hooks` 插進 `sys.path` 再載 gate;
`--all` 用 subprocess 逐 root 跑同一支,**各 repo 的 gate 自己答**。

## tmp repo 的造法(本檔選的方式)

每個測試用 `tmp_path` 造一個**最小 repo**:
`.dev/pipeline.json` + `.claude/settings.json` + `.claude/hooks/gate.py`(**真檔複本**)
+ `.agents/pipeline-stages.yaml`(真檔複本)。

**用複本而不是 sys.path 注入**,理由是這一檔要驗的正是「每個 root 拿到自己的 gate」——
注入宿主 repo 的 gate 會讓 `ROOT` 指回宿主,**測試會綠,而綠的原因是它沒在測那件事**。

framework-updates/99。
"""

import io
import json
import os
import pathlib
import shutil
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PORTABLE = ROOT / ".claude" / "portable"
REAL_GATE = ROOT / ".claude" / "hooks" / "gate.py"
REAL_STAGES = ROOT / ".agents" / "pipeline-stages.yaml"

if str(PORTABLE) not in sys.path:
    sys.path.insert(0, str(PORTABLE))

import status                      # noqa: E402  ← 尚不存在,本檔的紅燈在這裡
from status import render          # noqa: E402


# 分類詞 —— 裁 B:票面狀態行**不分類**,只印原文。
CLASSIFIER_WORDS = (u"done", u"open", u"candidate")

# 裁決式字樣 —— 判準 4 / 判準 5:不得有靜態 PASS。
VERDICT_TOKENS = (u"PASS", u"NOT MOUNTED", u"MOUNTED", u"ACTIVE", u": OK")

UNRECORDED = u"未記錄"


def _make_root(tmp_path, stage=u"implement", ticket=u"99", feature=u"testfeat",
               with_runs=False, with_exemptions=None, ticket_status=None):
    """造一個最小 repo。回傳 root 路徑(str)。

    `with_exemptions` 傳 list of dict 就寫成 jsonl;傳 None 代表**檔案不存在**
    (不是空檔 —— 空檔與不存在是兩件事,而本檔的負控要分得出來)。
    """
    root = tmp_path / "repo"
    (root / ".dev").mkdir(parents=True)
    (root / ".claude" / "hooks").mkdir(parents=True)
    (root / ".agents").mkdir(parents=True)

    with io.open(str(root / ".dev" / "pipeline.json"), "w", encoding="utf-8") as f:
        json.dump({"current_stage": stage, "feature": feature,
                   "ticket_id": ticket, "updated": "2026-09-02"}, f)

    with io.open(str(root / ".claude" / "settings.json"), "w", encoding="utf-8") as f:
        json.dump({"hooks": {"PreToolUse": [{"matcher": "Write|Edit|Bash", "hooks": [
            {"type": "command",
             "command": 'python "$CLAUDE_PROJECT_DIR/.claude/hooks/gate.py"'}]}]}}, f)

    shutil.copy2(str(REAL_GATE), str(root / ".claude" / "hooks" / "gate.py"))
    shutil.copy2(str(REAL_STAGES), str(root / ".agents" / "pipeline-stages.yaml"))

    if with_runs:
        rec = {"test_file": "tests/test_x.py", "time": "2026-09-02T00:00:00+00:00",
               "result": "red", "failed_tests": ["<collection error>"],
               "impl_file": None, "impl_exists": False, "impl_hash": None,
               "ticket_id": ticket}
        with io.open(str(root / ".dev" / "test-runs.jsonl"), "w", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    if with_exemptions is not None:
        with io.open(str(root / ".dev" / "gate-exemptions.jsonl"), "w", encoding="utf-8") as f:
            for rec in with_exemptions:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    if ticket_status is not None:
        d = root / "docs" / "tickets" / feature
        d.mkdir(parents=True)
        with io.open(str(d / ("%s-x.md" % ticket)), "w", encoding="utf-8") as f:
            f.write(u"# 票 %s\n\n%s\n\n內文\n" % (ticket, ticket_status))

    return str(root)


def _lines(out):
    return [ln for ln in out.splitlines() if ln.strip()]


def _value_of(out, field):
    """取 `<欄>:` 那一行的值(去掉 `(source: …)` 那一段)。找不到回 None。"""
    for ln in _lines(out):
        if ln.strip().startswith(field + u":"):
            v = ln.split(u":", 1)[1]
            return v.split(u"(source:")[0].strip()
    return None


class TestEveryLineIsTraceable:

    def test_every_line_carries_a_source(self, tmp_path):
        """守判準 3:每一行帶來源 —— 沒有來源的行不得印。"""
        out = render(_make_root(tmp_path))
        offenders = [ln for ln in _lines(out)
                     if not ln.strip().startswith(u"===") and u"(source:" not in ln]
        assert offenders == [], (
            u"這些行沒有來源,讀的人無法自己回去查:\n%s" % u"\n".join(offenders))


class TestOutpostIsNeverAVerdict:

    def test_outpost_line_is_never_a_verdict(self, tmp_path, monkeypatch):
        """守裁 D:前哨那一行永遠是 `mounted: 未證明`,而且不隨 shell 環境改變。"""
        root = _make_root(tmp_path)

        monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
        unset = _value_of(render(root), u"outpost")

        monkeypatch.setenv("CLAUDE_PROJECT_DIR", root)
        been_set = _value_of(render(root), u"outpost")

        assert unset is not None, u"outpost 那一行不見了"
        assert u"mounted: 未證明" in unset, unset
        assert unset == been_set, (
            u"`$CLAUDE_PROJECT_DIR` 在 shell 有沒有設定**不是證據** —— "
            u"hook 由 harness 起,環境不必然是這個 shell(裁 D)。\n"
            u"未設定:%s\n已設定:%s" % (unset, been_set))


class TestMissingEvidencePrintsUnrecorded:

    def test_missing_ledger_prints_unrecorded(self, tmp_path):
        """守判準 4:算不出來寫「未記錄」,不寫 PASS。"""
        out = render(_make_root(tmp_path, with_runs=False))
        assert _value_of(out, u"test-runs") == UNRECORDED

    def test_present_ledger_is_not_unrecorded(self, tmp_path):
        """負控:帳本在的時候那一行**不得**還是「未記錄」——
        少了這一格,一支永遠印「未記錄」的實作會讓上一條全綠。"""
        out = render(_make_root(tmp_path, with_runs=True))
        assert _value_of(out, u"test-runs") != UNRECORDED


class TestNoStaticVerdicts:

    def test_no_bare_verdict_tokens(self, tmp_path):
        """守判準 5:規則不做靜態 PASS —— 只印帳本與推導。"""
        out = render(_make_root(tmp_path))
        hits = [t for t in VERDICT_TOKENS if t in out]
        assert hits == [], (
            u"輸出裡出現裁決式字樣 %s —— `status` 不重跑規則,"
            u"它對一個沒被觸發過的規則的正確答案是「本期無紀錄」" % hits)


class TestStageComesFromGate:

    def test_stage_is_read_through_gate(self, tmp_path, monkeypatch):
        """守判準 2:只呼叫 `gate.py`,不重述它(換掉 gate,輸出要跟著變)。"""
        root = _make_root(tmp_path, stage=u"implement", ticket=u"99")

        real = status.load_gate(root)

        class _Stub(object):
            def __getattr__(self, name):
                return getattr(real, name)

            def load_stage(self):
                return (u"grill", u"77")

        monkeypatch.setattr(status, "load_gate", lambda _root: _Stub())
        out = render(root)

        assert _value_of(out, u"stage") == u"grill", out
        assert _value_of(out, u"ticket_id") == u"77", (
            u"stage 與 ticket_id 是 `load_stage()` 同一個回傳值的兩半,"
            u"只有一半跟著變的話,另一半是自己讀檔讀來的\n%s" % out)


class TestTicketStatusLineIsVerbatim:

    def test_ticket_status_line_is_verbatim(self, tmp_path):
        """守裁 B:票面狀態行只印原文,**不分類**(值域 ≥21 種寫法,分類器驗不了)。"""
        weird = u"**狀態**:**半熟(測試用)**"
        out = render(_make_root(tmp_path, ticket_status=weird))

        assert weird in out, (
            u"狀態行沒有原文出現 —— 摘要過的狀態行讀的人無法回去核對\n%s" % out)

        line = None
        for ln in _lines(out):
            if weird in ln:
                line = ln
                break
        low = line.lower()
        hits = [w for w in CLASSIFIER_WORDS if w in low]
        assert hits == [], (
            u"狀態行被分類成 %s —— 裁 B:不分類。"
            u"實測值域 ≥21 種寫法、2 行跨行截斷,分類器的產出沒有人驗得了\n%s"
            % (hits, line))


class TestAuthorityIsALedgerNotAVerdict:

    def test_authority_line_is_unrecorded_without_a_ledger(self, tmp_path):
        """守判準 5:權威層在不在**由帳本說**;沒有帳本就是「未記錄」,不是「沒裝」。"""
        out = render(_make_root(tmp_path, with_exemptions=None))
        assert _value_of(out, u"authority") == UNRECORDED

    def test_authority_line_cites_the_commit_time_record(self, tmp_path):
        """負控:帳本裡有 `at_commit=true` 的一筆時,那一行要帶得出它的 `ts`。"""
        ts = u"2026-08-31T09:43:19.318024+00:00"
        recs = [
            {"ts": u"2026-08-30T00:00:00+00:00", "file": "a.py", "at_commit": False,
             "outcome": "granted", "ticket": "98"},
            {"ts": ts, "file": ".claude/hooks/gate.py", "at_commit": True,
             "outcome": "granted", "ticket": "82"},
        ]
        out = render(_make_root(tmp_path, with_exemptions=recs))
        val = _value_of(out, u"authority")
        assert val != UNRECORDED, out
        assert ts in val, (
            u"權威層那一行要指得出**哪一筆**紀錄 —— 只說「有」等於一個無從反駁的摘要\n%s" % out)
