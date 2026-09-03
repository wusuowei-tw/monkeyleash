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
import subprocess
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
        """守判準 5:權威層在不在**由帳本說**;沒有帳本就是「未記錄」,不是「沒裝」。

        ⚠ Day 3 標籤從 `authority` 改成 `authority ledger` —— 因為同一段裡
        現在有兩個 authority 來源(帳本 / `core.hooksPath`),而
        `authority:` 這個裸標籤讀起來像「權威層的狀態」,那正是判準 5 不准印的東西。
        """
        out = render(_make_root(tmp_path, with_exemptions=None))
        assert _value_of(out, u"authority ledger") == UNRECORDED

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
        val = _value_of(out, u"authority ledger")
        assert val != UNRECORDED, out
        assert ts in val, (
            u"權威層那一行要指得出**哪一筆**紀錄 —— 只說「有」等於一個無從反駁的摘要\n%s" % out)


# ═══════════════════════════════════════════════════════════════════════════
# Day 3 —— 四補(generated / 標籤 / outpost 帳本 / intercepts 兩行 /
#          每檔最新一筆)+ `--all` + Sync Health
#
# 🔴 本區塊寫下的當下,`render_all` 與 `now_iso` 都不存在,而 v1 的欄位名
#    仍是 `authority` / 單行 `intercepts` —— 這是票 99 Day 3 的紅燈。
# ═══════════════════════════════════════════════════════════════════════════

# 假 gate:**刻意沒有 `stage_allows_src_write`**。
# 下游裝的是舊版框架,而「舊版沒有這個函式」正是 `--all` 一定會遇到的情形 ——
# 那時的正確行為是印「未記錄」,不是整份輸出崩掉。
FAKE_GATE = u'''# -*- coding: utf-8 -*-
import os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PIPELINE = os.path.join(ROOT, ".dev", "pipeline.json")
EXEMPTION_LOG = os.path.join(ROOT, ".dev", "gate-exemptions.jsonl")
RUN_LOG = os.path.join(ROOT, ".dev", "test-runs.jsonl")
PROVENANCE = os.path.join(ROOT, ".dev", "provenance.jsonl")
SHADOW_STATE = os.path.join(ROOT, ".dev", "shadow.json")
TICKET_DIRS = ("docs/tickets/%s",)
INTERCEPT_LOG = os.path.join(ROOT, ".dev", "intercepts.jsonl")


def load_stage():
    return ("__STAGE__", "__TICKET__")


def load_feature():
    return "__FEATURE__"


def intercept_path(month):
    stem, ext = os.path.splitext(INTERCEPT_LOG)
    return "%s-%s%s" % (stem, month, ext)


def shadow_active(today=None):
    return False


def skill_mirror_violations(canon, mirrors):
    return []


def rule_codes(source_path=None):
    return set()
'''


def _make_fake_root(tmp_path, name, stage, ticket, feature=u"fake"):
    """造一個只有**假 gate** 的 root。用來證明各 root 走各自的 gate。"""
    root = tmp_path / name
    (root / ".dev").mkdir(parents=True)
    (root / ".claude" / "hooks").mkdir(parents=True)
    with io.open(str(root / ".dev" / "pipeline.json"), "w", encoding="utf-8") as f:
        json.dump({"current_stage": stage, "feature": feature,
                   "ticket_id": ticket}, f)
    body = (FAKE_GATE.replace(u"__STAGE__", stage)
                     .replace(u"__TICKET__", ticket)
                     .replace(u"__FEATURE__", feature))
    with io.open(str(root / ".claude" / "hooks" / "gate.py"), "w", encoding="utf-8") as f:
        f.write(body)
    return str(root)


def _git(root, *args):
    return subprocess.run(["git"] + list(args), cwd=root, capture_output=True)


def _make_git_root(tmp_path, name, files):
    """造一個**真的 git repo**(Sync Health 要算 commit 距離,假不了)。"""
    root = _make_root_dir(tmp_path, name, files)
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@example.invalid")
    _git(root, "config", "user.name", "t")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "one")
    return root


def _make_root_dir(tmp_path, name, files):
    root = tmp_path / name
    root.mkdir(parents=True)
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        with io.open(str(p), "w", encoding="utf-8") as f:
            f.write(text)
    return str(root)


class TestGeneratedComesFromTheClock:

    def test_generated_line_comes_from_the_clock(self, tmp_path, monkeypatch):
        """守判準 1(projection 不存):時間來自時鐘,不來自任何被存下來的檔。

        一個從檔案讀出來的時間戳,會在檔案沒更新時**看起來像剛剛算的**,
        而那正是「存起來的現況」最危險的地方。
        """
        root = _make_root(tmp_path)
        monkeypatch.setattr(status, "now_iso", lambda: u"2999-01-01T00:00:00+00:00")
        out = render(root)
        assert _value_of(out, u"generated") == u"2999-01-01T00:00:00+00:00", out


class TestTheBareAuthorityLabelIsGone:

    def test_the_bare_authority_label_is_gone(self, tmp_path):
        """守判準 5:`authority:` 這個裸標籤讀起來像「權威層的狀態」。

        同一段裡現在有兩個 authority 來源(帳本 / `core.hooksPath`),
        而**它們回答的不是同一個問題** —— 一個是「跑過沒」,一個是「設定指向哪」。
        共用一個標籤會讓讀的人以為那是一個結論。
        """
        out = render(_make_root(tmp_path))
        bare = [ln for ln in _lines(out) if ln.strip().startswith(u"authority:")]
        assert bare == [], u"裸標籤 authority: 還在:%s" % bare
        assert _value_of(out, u"authority ledger") is not None, out
        assert _value_of(out, u"authority config") is not None, out


class TestOutpostHasALedgerLineToo:

    def test_outpost_ledger_is_unrecorded_without_a_ledger(self, tmp_path):
        """守判準 4:沒有帳本就是未記錄。"""
        out = render(_make_root(tmp_path, with_exemptions=None))
        assert _value_of(out, u"outpost ledger") == UNRECORDED

    def test_outpost_ledger_cites_the_last_agent_time_record(self, tmp_path):
        """守判準 5:前哨**跑過沒**由帳本說 —— `at_commit=false` 那些是它的痕跡。

        設定那一行仍然是 `mounted: 未證明`(裁 D):
        **設定解得到什麼,與 hook 跑的是不是它,是兩件事。**
        兩行並存不矛盾 —— 它們回答不同的問題,而各自帶自己的來源。
        """
        agent_ts = u"2026-09-02T00:44:52.652814+00:00"
        recs = [
            {"ts": agent_ts, "tool": "Edit", "at_commit": False, "outcome": "granted"},
            {"ts": u"2026-09-02T00:45:39.047247+00:00", "tool": "pre-commit",
             "at_commit": True, "outcome": "granted"},
        ]
        out = render(_make_root(tmp_path, with_exemptions=recs))
        assert agent_ts in _value_of(out, u"outpost ledger"), out
        assert u"mounted: 未證明" in _value_of(out, u"outpost"), out


class TestInterceptsPrintsTwoLines:

    def _root_with_month(self, tmp_path, month):
        root = _make_root(tmp_path)
        rec = {"ts": u"2026-08-28T00:12:55+00:00", "rule": "R7",
               "at_commit": False, "cmd_verb": "printf"}
        with io.open(str(pathlib.Path(root) / ".dev" / ("intercepts-%s.jsonl" % month)),
                     "w", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return root

    def test_two_lines_not_one(self, tmp_path):
        """守判準 3/4:**「當月」與「最新存在月」是兩個問題,不得合成一格。**

        合成一格的話,一個從未被攔截過的月份會印「檔不存在」,
        而那與「這個 repo 從來沒有攔截紀錄」**逐字相同** ——
        兩件事差很多:前者是正常,後者是前哨可能沒在跑。
        """
        out = render(self._root_with_month(tmp_path, u"2026-08"))
        assert _value_of(out, u"intercepts (當月)") is not None, out
        assert _value_of(out, u"intercepts (最新存在月)") is not None, out

    def test_latest_existing_month_names_the_file_and_the_last_record(self, tmp_path):
        out = render(self._root_with_month(tmp_path, u"2026-08"))
        val = _value_of(out, u"intercepts (最新存在月)")
        assert u"2026-08" in val and u"R7" in val, val

    def test_latest_existing_month_changes_when_the_file_goes_away(self, tmp_path):
        """**變異控制** —— 檔案消失,那一行必須跟著變。

        少了這一格,一支永遠印同一句話的實作會讓上面兩條全綠
        (票 99 Day 2 的負控就是這樣空轉的:移走的檔案根本不在讀取路徑上)。
        """
        root = self._root_with_month(tmp_path, u"2026-08")
        before = _value_of(render(root), u"intercepts (最新存在月)")
        os.remove(str(pathlib.Path(root) / ".dev" / "intercepts-2026-08.jsonl"))
        after = _value_of(render(root), u"intercepts (最新存在月)")
        assert before != after, (
            u"檔案移走之後那一行沒有變 —— 它讀的不是這個檔\nbefore=%s\nafter=%s"
            % (before, after))
        assert after == UNRECORDED, after

    def test_no_month_file_at_all_is_unrecorded(self, tmp_path):
        out = render(_make_root(tmp_path))
        assert _value_of(out, u"intercepts (最新存在月)") == UNRECORDED


class TestTestsUnderTicketUsesTheLatestRecordPerFile:

    def test_a_file_that_went_red_then_green_counts_as_green(self, tmp_path):
        """守判準 5:帳本是追加式,**同一個檔會有很多筆** ——
        「這張票底下還有什麼是紅的」問的是**每個檔的最新一筆**,不是有沒有紅過。

        用「有沒有紅過」的話,任何轉綠的檔都會永遠留在紅名單裡,
        而一份永遠不會變空的紅名單,讀的人三天後就不看了。
        """
        root = _make_root(tmp_path)
        recs = [
            {"test_file": "tests/test_a.py", "time": "2026-09-02T01:00:00+00:00",
             "result": "red", "ticket_id": "99"},
            {"test_file": "tests/test_a.py", "time": "2026-09-02T02:00:00+00:00",
             "result": "green", "ticket_id": "99"},
            {"test_file": "tests/test_b.py", "time": "2026-09-02T03:00:00+00:00",
             "result": "red", "ticket_id": "99"},
        ]
        with io.open(str(pathlib.Path(root) / ".dev" / "test-runs.jsonl"),
                     "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

        out = render(root)
        red = _value_of(out, u"tests red under ticket 99")
        green = _value_of(out, u"tests green under ticket 99")
        assert u"tests/test_a.py" not in red, red
        assert u"tests/test_a.py" in green, green
        assert u"tests/test_b.py" in red, red


class TestRenderAll:

    def test_every_line_still_carries_a_source(self, tmp_path):
        """守判準 3 —— `--all` 不是放寬來源規矩的理由。"""
        roots = [_make_fake_root(tmp_path, "r1", u"grill", u"11"),
                 _make_fake_root(tmp_path, "r2", u"implement", u"22")]
        out = status.render_all(roots)
        offenders = [ln for ln in _lines(out)
                     if not ln.strip().startswith(u"===") and u"(source:" not in ln]
        assert offenders == [], u"\n".join(offenders)

    def test_each_root_gets_its_own_section(self, tmp_path):
        roots = [_make_fake_root(tmp_path, "r1", u"grill", u"11"),
                 _make_fake_root(tmp_path, "r2", u"implement", u"22")]
        out = status.render_all(roots)
        for r in roots:
            assert r in out, u"節頭沒有印出 root %s\n%s" % (r, out)

    def test_each_root_answers_through_its_own_gate(self, tmp_path):
        """守裁 C:**各 repo 的 gate 自己答。**

        兩個 root 的假 gate 回不同的 `load_stage()`。輸出兩節的值若相同,
        代表第二個 root 拿到的是第一個 root 的模組 —— 而那個錯**完全無聲**
        (規則還在、還被呼叫、永遠回同一個答案)。
        """
        roots = [_make_fake_root(tmp_path, "r1", u"grill", u"11"),
                 _make_fake_root(tmp_path, "r2", u"implement", u"22")]
        out = status.render_all(roots)
        assert u"stage: grill" in out, out
        assert u"stage: implement" in out, out

    def test_a_gate_without_the_new_function_does_not_crash(self, tmp_path):
        """守判準 4:下游裝的是舊版框架 —— **缺函式是常態,不是例外狀況。**

        崩掉的話,一個 root 的舊 gate 會讓**整份** `--all` 沒有輸出,
        而讀的人看到的是一個 traceback,不是「那一格算不出來」。
        """
        roots = [_make_fake_root(tmp_path, "r1", u"grill", u"11"),
                 _make_fake_root(tmp_path, "r2", u"implement", u"22")]
        out = status.render_all(roots)
        assert u"未記錄(該 repo 的 gate 無此函式)" in out, out


class TestSyncHealth:

    def _pair(self, tmp_path, sha=None):
        up = _make_git_root(tmp_path, "up", {
            ".claude/hooks/gate.py": u"# upstream gate\n",
            ".claude/portable/g1_guard.py": u"# guard\n",
            "tests/test_g1_guard.py": u"# guard test\n",
        })
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=up,
                              capture_output=True).stdout.decode().strip()
        down = _make_root_dir(tmp_path, "down", {
            ".claude/hooks/gate.py": u"# upstream gate\n",
            ".claude/portable/g1_guard.py": u"# guard drifted\n",
            "tests/test_g1_guard.py": u"# guard test\n",
            ".dev/provenance.jsonl": json.dumps(
                {"path": "x", "upstream_path": "x",
                 "upstream_commit": sha or head, "content_hash": "z"}) + "\n",
        })
        return up, down, head

    def test_not_printed_for_a_single_root(self, tmp_path):
        """守判準 7:單 repo 印不出 Sync Health —— **它答不出「跟誰比」。**"""
        out = render(_make_fake_root(tmp_path, "solo", u"idle", u"1"))
        assert u"Sync Health" not in out, out

    def test_printed_for_two_or_more_roots(self, tmp_path):
        up, down, _head = self._pair(tmp_path)
        out = status.render_all([up, down])
        assert u"Sync Health" in out, out

    def test_it_names_the_upstream_commit_from_provenance(self, tmp_path):
        up, down, head = self._pair(tmp_path)
        out = status.render_all([up, down])
        assert head[:8] in out, out

    def test_no_provenance_is_unrecorded(self, tmp_path):
        up = _make_git_root(tmp_path, "up", {".claude/hooks/gate.py": u"# g\n"})
        down = _make_root_dir(tmp_path, "down", {".claude/hooks/gate.py": u"# g\n"})
        out = status.render_all([up, down])
        line = [ln for ln in _lines(out) if u"upstream commit" in ln]
        assert line and UNRECORDED in line[0], out

    def test_a_sha_outside_upstream_history_is_not_converted(self, tmp_path):
        """**不做換算。** 那個 sha 可能是票 84 改寫身分之前的,
        而換算需要 commit-map —— 猜一個距離出來,比印「未記錄」糟得多。
        """
        dead = "0" * 40
        up, down, _head = self._pair(tmp_path, sha=dead)
        out = status.render_all([up, down])
        assert u"未記錄(sha 不在上游歷史,可能為票 84 改寫前)" in out, out

    def test_three_files_are_hashed_on_both_sides(self, tmp_path):
        """守判準 3:**兩邊都印**,不只印一個 same/drift 的結論。

        只印結論的話,讀的人無法自己核對 —— 而「兩邊都印」正是
        `same` 這個字唯一能被反駁的方式。
        """
        up, down, _head = self._pair(tmp_path)
        out = status.render_all([up, down])
        for rel in (u".claude/hooks/gate.py", u".claude/portable/g1_guard.py",
                    u"tests/test_g1_guard.py"):
            assert rel in out, u"%s 沒有出現\n%s" % (rel, out)
        assert u"same" in out and u"drift" in out, (
            u"三檔裡兩檔相同、一檔不同,兩種結論都該出現\n%s" % out)


# ─────────────────────────────────────────────────────────────────────────
# 票 100 —— 兩件都不是「算不出來」,是**算出了一個東西然後貼上配不上的標籤**
# ─────────────────────────────────────────────────────────────────────────

# 甲-2 用的固定資料:兩張票、三個檔,其中 test_a 紅轉綠。
# **放模組層而不是 fixture**:這組資料要被正控與負控**共用**,
# 兩支拿到不同的資料的話,「有票那條路沒被改壞」就證不出來。
TICKET_100_RUNS = [
    {"test_file": "tests/test_a.py", "time": "2026-09-02T01:00:00+00:00",
     "result": "red", "ticket_id": "99"},
    {"test_file": "tests/test_a.py", "time": "2026-09-02T02:00:00+00:00",
     "result": "green", "ticket_id": "99"},
    {"test_file": "tests/test_b.py", "time": "2026-09-02T03:00:00+00:00",
     "result": "red", "ticket_id": "99"},
    {"test_file": "tests/test_c.py", "time": "2026-09-02T04:00:00+00:00",
     "result": "green", "ticket_id": "98"},
]


def _write_runs(root, recs):
    with io.open(str(pathlib.Path(root) / ".dev" / "test-runs.jsonl"),
                 "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


class TestIdleTestRunsLineIsUnrecorded:
    """票 100 甲-1 —— **沒有當前票時,`test-runs` 行不得帶票面語氣。**

    `_latest_per_file` 的過濾寫成 `if ticket and ...`,票號 falsy 時整個
    `continue` 分支不執行,於是「這張票底下」變成「全部」——
    而值仍然標著「本票」。**那不是缺值,是一個錯的宣稱**,
    而帶著票面語氣的數字讀的人會直接引用。
    """

    def test_idle_prints_unrecorded_not_this_ticket(self, tmp_path):
        root = _make_root(tmp_path, stage=u"idle", ticket=None)
        _write_runs(root, TICKET_100_RUNS)

        out = render(root)
        val = _value_of(out, u"test-runs")
        assert val is not None, out
        assert val.startswith(UNRECORDED), val
        # **兩個斷言缺一不可。** 只斷言開頭的話,一個印成
        # 「未記錄;本票 red 0 / green 0」的實作會過關 —— 而那仍然是個謊。
        assert u"本票" not in val, val


class TestLatestPerFileIsFailClosedWithoutTicket:
    """票 100 甲-2 —— 守在**函式自己**,不是守在呼叫端。

    `_derived` 已經用 `or not ticket` 擋住了,而 `_evidence` 沒有。
    修呼叫端救不了下一個呼叫者:函式的名字與 docstring 都在跟他保證篩過了。
    """

    def test_no_ticket_returns_empty(self):
        assert TICKET_100_RUNS, u"資料是空的話這支測試證不了任何事"
        assert status._latest_per_file(TICKET_100_RUNS, None) == {}

    def test_with_ticket_still_filters(self):
        """**負控** —— 防止修法把有票那條路一起關掉。

        一支「永遠回 `{}`」的實作會讓上面那支綠,而它把整行變成裝飾。
        """
        got = status._latest_per_file(TICKET_100_RUNS, u"99")
        assert sorted(got) == ["tests/test_a.py", "tests/test_b.py"], sorted(got)
        assert got["tests/test_a.py"]["result"] == "green", got["tests/test_a.py"]


class TestSyncWaterline:
    """票 100 乙 —— **末筆是位置,不是水位線。**

    憑證逐檔發、追加不覆蓋、四個欄位裡沒有時間戳,所以 `recs[-1]` 只代表
    「最後一個被寫進去的 path」。由它推導出來的 `behind`,是一個由單一 path
    決定的距離,卻被印成整個下游的落後量。

    **自己造 fixture,不改 `TestSyncHealth._pair`** —— 那支單筆 fixture 被六支
    現有測試共用,而改一個共用 fixture 影響的不只是你正在看的那一支(票 99 十一之四)。
    """

    FILES = {
        ".claude/hooks/gate.py": u"# upstream gate\n",
        ".claude/portable/g1_guard.py": u"# guard\n",
        "tests/test_g1_guard.py": u"# guard test\n",
    }

    def _up_two_commits(self, tmp_path, name=u"upw"):
        """上游造**兩刀**,兩個 sha 都真實存在 —— 否則測到的是 DEAD_SHA 那條路。"""
        up = _make_git_root(tmp_path, name, dict(self.FILES))
        first = _git(up, "rev-parse", "HEAD").stdout.decode().strip()
        with io.open(str(pathlib.Path(up) / "note.txt"), "w", encoding="utf-8") as f:
            f.write(u"second\n")
        _git(up, "add", "-A")
        _git(up, "commit", "-q", "-m", "two")
        second = _git(up, "rev-parse", "HEAD").stdout.decode().strip()
        assert first != second
        return up, first, second

    def _down(self, tmp_path, recs, name=u"downw"):
        files = dict(self.FILES)
        files[".dev/provenance.jsonl"] = u"".join(
            json.dumps(r, ensure_ascii=False) + u"\n" for r in recs)
        return _make_root_dir(tmp_path, name, files)

    @staticmethod
    def _rec(path, commit):
        return {"path": path, "upstream_path": path,
                "upstream_commit": commit, "content_hash": "z"}

    def test_two_commits_print_count_and_unrecorded_behind(self, tmp_path):
        """乙-1:兩個 path 帶兩個不同 commit ⇒ **說出「未收齊」,不挑一個。**

        挑哪一個都是猜,而猜出來的距離長得跟量出來的一模一樣。
        """
        up, first, second = self._up_two_commits(tmp_path)
        down = self._down(tmp_path, [self._rec("a", first),
                                     self._rec("b", second)])
        out = status.render_all([up, down])

        wl = _value_of(out, u"[2] waterline")
        assert wl is not None, out
        assert u"2 個" in wl, wl

        behind = _value_of(out, u"[2] behind")
        assert behind.startswith(UNRECORDED), behind
        assert u"未收齊" in behind, behind

        # **末筆那一行一字不改。** 它是一個誠實的觀測(來源欄自己寫著「末筆」),
        # 刪掉一個觀測換一個新的,會讓「本來印什麼」在事後查不到。
        assert _value_of(out, u"[2] upstream commit") == second, out

    def test_one_commit_prints_sha_and_behind(self, tmp_path):
        """乙-2 **負控** —— 兩個 path 同一個 commit ⇒ 照樣算得出刀數。

        沒有這一支的話,一個「永遠印未收齊」的實作會讓乙-1 綠,
        而它把 Sync Health 整段變成裝飾。
        """
        up, first, _second = self._up_two_commits(tmp_path)
        down = self._down(tmp_path, [self._rec("a", first),
                                     self._rec("b", first)])
        out = status.render_all([up, down])

        wl = _value_of(out, u"[2] waterline")
        assert wl is not None, out
        assert first[:12] in wl, wl
        assert u"個不同 commit" not in wl, wl

        assert _value_of(out, u"[2] behind") == u"1 刀", out


class TestFindTicketFileHasABoundary:
    """framework-updates/101 裁 4 前半:票號比對要帶邊界(號碼後接 `-`)。

    **為什麼測試放在這裡而不是只放 MCP 那一側**:修的是 `status.py` 的函式,
    而**下一個呼叫者不會經過 MCP** —— CLI 的 Ticket 區段現在就在用它。
    測試要放在被修的東西旁邊。

    ⚠ 三格裡只有中間那格是紅的。另外兩格是**負控**:
    現行行為就是綠的,修法**不得把它們弄紅**。
    只寫紅的那一格的話,一個「一律回 None」的實作會通過。

    ⚠ 補零(`1` -> `01`)**不在這一層**。`_find_ticket_file("1")` 回 `None`
    是**正確行為** —— 底層只答「這個字串有沒有邊界命中」,
    補零是呼叫者對本 repo 命名慣例的知識(下游 repo 不見得補零)。
    """

    def _dir_with(self, tmp_path, feature=u"testfeat"):
        root = tmp_path / "repo"
        d = root / "docs" / "tickets" / feature
        d.mkdir(parents=True)
        for name in (u"10-a.md", u"100-b.md"):
            with io.open(str(d / name), "w", encoding="utf-8") as f:
                f.write(u"# %s\n" % name)
        # `_ticket_dirs` 走 `gate.TICKET_DIRS`,所以要一份真 gate。
        (root / ".claude" / "hooks").mkdir(parents=True)
        shutil.copy2(str(REAL_GATE), str(root / ".claude" / "hooks" / "gate.py"))
        return str(root), status.load_gate(str(root)), feature

    def test_ten_still_finds_ten(self, tmp_path):
        """負控 —— 現行就綠,修法不得弄紅。

        字典序意外讓這一格現在就對(`-` 0x2D < `0` 0x30,
        所以 `10-a.md` 排在 `100-b.md` 前面)。**綠的原因不是程式碼守住了它**,
        所以它留在這裡:邊界改成 `+"-"` 之後,綠的原因才變成正確的那個。
        """
        root, gate, feature = self._dir_with(tmp_path)
        got = status._find_ticket_file(root, gate, feature, u"10")
        assert got is not None and os.path.basename(got) == u"10-a.md", got

    def test_one_finds_nothing(self, tmp_path):
        """**紅的那一條** —— 現行回 `10-a.md`。

        真實資料上這一族有九筆(票 101 第四節實測):
        `1` -> 票 10、`2` -> 票 20、…、`9` -> 票 90。
        回錯一份票比回不出來糟得多:回不出來的人會再查,
        拿到一份**看起來對**的票的人不會。
        """
        root, gate, feature = self._dir_with(tmp_path)
        got = status._find_ticket_file(root, gate, feature, u"1")
        assert got is None, u"票號 1 不該命中 %r" % (got,)

    def test_hundred_still_finds_hundred(self, tmp_path):
        """負控 —— 邊界改成 `+"-"` 之後,長號仍要中。

        沒有這一支的話,一個把邊界寫成「號碼後接 `-` **且長度相等**」
        之類的實作會讓上面兩格都綠,而把 `100` 弄丟。
        """
        root, gate, feature = self._dir_with(tmp_path)
        got = status._find_ticket_file(root, gate, feature, u"100")
        assert got is not None and os.path.basename(got) == u"100-b.md", got
