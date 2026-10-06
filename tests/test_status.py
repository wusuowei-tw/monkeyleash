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
import re
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


class TestTheExemptionsLineGivesEveryRecordAHome:
    """票 116 B-7 —— `exemptions` 那一行要**逐桶**,而留白要有自己的桶。

    ## 修之前是什麼樣子

    `status.py:613` 只問一件事:`r.get("outcome") == "blocked"`。
    於是輸出是「總 N 筆;outcome=blocked M 筆」——
    **而「沒有 `outcome` 這個鍵」的那些既不在 blocked 也不在 granted**,
    報表上**沒有它們的位置**。

    實測(2026-09-08,上游帳本 223 筆):`granted` 182 / `blocked` 1 /
    **沒有這個鍵 40**。那 40 筆是票 08 之前的 5 鍵舊格式。

    `.get()` 讓「**沒有這個鍵**」與「**值不是 blocked**」在輸出上長得一模一樣。

    > **留白要有自己的桶,不能併進蓋章。**(票 67 那 72 筆的同一句)

    ## ⚠ 這一行在本票之前**一個測試都沒有**

    2026-09-08 全庫查過:沒有任何測試引用 `exemptions` 這個 label。
    所以本組是它的第一份覆蓋 —— **而那也是它能默默錯這麼久的原因**。
    """

    GRANTED = {"ts": u"2026-09-01T00:00:00+00:00", "file": "a.py",
               "at_commit": False, "outcome": "granted", "ticket": "01"}
    BLOCKED = {"ts": u"2026-09-01T00:01:00+00:00", "file": "b.py",
               "at_commit": False, "outcome": "blocked", "ticket": "01"}
    NO_KEY = {"file": "c.py", "module": "c", "ticket": "01",
              "declared_in": "0004", "reason": "gate-self-modification"}

    def _val(self, tmp_path, recs):
        return _value_of(render(_make_root(tmp_path, with_exemptions=recs)),
                         u"exemptions")

    def test_the_buckets_add_up_to_the_total(self, tmp_path):
        """**紅燈甲**:各桶相加 == 總筆數。

        相加對不上就代表有一群紀錄無家可歸,**而它們會靜靜消失在某個 `else` 裡**。
        """
        val = self._val(tmp_path, [self.GRANTED, self.GRANTED,
                                   self.BLOCKED, self.NO_KEY])
        nums = [int(x) for x in re.findall(r"(\d+) 筆", val)]
        assert nums, u"那一行印不出任何筆數:%r" % val
        total = nums[0]
        assert total == 4, u"總筆數報錯:%r" % val
        assert sum(nums[1:]) == total, (
            u"各桶相加 %d != 總筆數 %d —— 有紀錄無家可歸:%r"
            % (sum(nums[1:]), total, val))

    def test_a_record_without_the_outcome_key_has_its_own_bucket(self, tmp_path):
        """**紅燈甲後半**:沒有 `outcome` 鍵的那些**不是** granted 也**不是** blocked。

        修之前它們被 `.get()` 靜默併進「不是 blocked」那一邊。
        """
        val = self._val(tmp_path, [self.GRANTED, self.NO_KEY])
        assert u"未記錄" in val, (
            u"沒有 outcome 鍵的紀錄沒有自己的桶 —— 留白被併進蓋章了:%r" % val)
        m = re.search(r"granted (\d+) 筆", val)
        assert m and int(m.group(1)) == 1, (
            u"granted 把沒有 outcome 鍵的那一筆也算進去了:%r" % val)

    def test_an_out_of_range_outcome_is_not_silently_bucketed(self, tmp_path):
        """**紅燈乙(反控,`F-087`)**:值域外的值不得被靜默歸進任何一桶。

        `outcome` 的值域從產生端看是**封閉**的 ——
        `gate.py:2079` 是唯一的寫入點,而它是一個三元式:

            "outcome": "blocked" if verdict else "granted",

        ⇒ 只有兩種值。**而封閉是今天的性質,不是永遠的保證。**
        這一條釘住「哪天它不再封閉時會有東西說話」:
        多一種值就要多一個桶,而不是讓它靜靜落進既有的某一格。
        """
        weird = dict(self.GRANTED)
        weird["outcome"] = "surprise"
        val = self._val(tmp_path, [self.GRANTED, weird])
        nums = [int(x) for x in re.findall(r"(\d+) 筆", val)]
        assert sum(nums[1:]) == nums[0], (
            u"值域外的 outcome 讓各桶相加對不上總數 —— 它被靜默丟掉了:%r" % val)
        assert u"其他" in val, (
            u"值域外的 outcome 沒有落進「其他」桶 —— 那一天沒有東西會說話:%r" % val)

    def test_a_missing_ledger_is_still_unrecorded(self, tmp_path):
        """**負控**:帳本不存在時仍然是「未記錄」,不是「0 筆」。

        少了它,一支「一律印 0 筆」的實作會讓上面幾條過 ——
        而**「沒有帳本」與「帳本是空的」是兩件事**。
        """
        assert self._val(tmp_path, None) == UNRECORDED


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
        # 票 145〈十三〉裁決 2(C):Station 4 補 run-level facts。
        # 上面 test_a 的綠紀錄是 8 欄格式、沒有 run 事實 ⇒ 依 ODC-1 沒有退紅權;
        # 補一次「test_a 全檔被選到、唯一一條實際執行且通過、該檔無 failure」的 run,
        # 時點與那筆綠相同。紅紀錄沒有 failed_tests(身分不明)⇒ 依〈十三〉裁決 3,
        # 該檔全部 collected 身分都要 passed —— 這個 run 滿足它。
        # 第一行讓 fake repo 有 redlight.py:status 依 root 載入它讀 run 事實(裁決 1)。
        shutil.copy2(str(REAL_REDLIGHT),
                     str(pathlib.Path(root) / ".claude" / "hooks" / "redlight.py"))
        _t_committed(root)
        blobs = dict((p, {u"worktree": _t_git(root, "hash-object", p).stdout.decode().strip(),
                          u"head": _t_git(root, "rev-parse", "HEAD:" + p).stdout.decode().strip()})
                     for p in (u"pyproject.toml", u"tests/conftest.py"))
        redlight.record_session(
            root, run_id=u"fixture-570-571", time=u"2026-09-02T02:00:00+00:00",
            ticket_id=u"99", exit_code=0, collected=[u"tests/test_a.py::test_one"],
            deselected=[], outcomes={u"tests/test_a.py::test_one": u"passed"},
            invocation={u"args": [u"tests"]},
            completeness={
                u"options": {u"lf": False, u"last_failed_no_failures": u"all", u"stepwise": False,
                             u"stepwise_skip": False, u"maxfail": None, u"collectonly": False,
                             u"setuponly": False, u"setupplan": False,
                             u"runxfail": False, u"pythonwarnings": None, u"trace": False,
                             u"usepdb": False},
                u"cacheprovider_blocked": False, u"shouldstop": False, u"shouldfail": False,
                u"pre_narrowing": {u"tests/test_a.py": [u"tests/test_a.py::test_one"]},
                u"plugins": [{u"name": u"main", u"kind": u"builtin"},
                             {u"name": u"tests/conftest.py", u"kind": u"root_conftest"},
                             {u"name": u"anyio", u"kind": u"known_dist",
                              u"dists": [[u"anyio", u"4.15.0"]]}],
                u"blocked": [], u"override_ini": list(_T_FIXED_OVERRIDES), u"inifilename": None,
                u"inipath": u"pyproject.toml", u"config_blobs": blobs, u"pytest_version": u"9.1.1",
                u"optimize": 0, u"python_version": u"3.11",
                u"evidence_policy": _t_policy_facts(root)})

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

    # ── 票 114 刀三:判準收成一份 ────────────────────────────────────────────
    #
    # 在此之前 `_find_ticket_file` 與 `mcp_server._ticket_path` 是**兩份逐字
    # 幾乎相同**的實作;2026-09-08 實測對八組輸入答案全同,**而那是巧合不是保證**
    # (`F-058` 家族)。本票收進 `.claude/portable/ticket_lookup.find`。

    def test_it_delegates_to_the_shared_lookup_module(self):
        """**判準只有一份** —— 本檔不得自己再寫一次邊界與副檔名。

        測「有沒有真的委派」而不是「答案對不對」:一個自己重寫一份的實作
        會給出**一模一樣的答案**,而它會在下一次只改一邊的時候漂開,
        **那時沒有東西會說話**。
        """
        assert getattr(status, "ticket_lookup", None) is not None, (
            "status 沒有用 ticket_lookup 的判定 —— 它自己有一份")

    def test_swapping_the_shared_lookup_changes_the_answer(self, tmp_path, monkeypatch):
        """**反控**:上一條只證明那個名字在,不證明它被呼叫。

        少了這一條,`import ticket_lookup` 放著不用也會讓上一條綠 ——
        而**恆真的斷言與有效的斷言在測試輸出上長得一模一樣**。
        做法:把共用模組的 `find` 換掉,答案必須跟著變。
        """
        root, gate, feature = self._dir_with(tmp_path)
        monkeypatch.setattr(status.ticket_lookup, "find",
                            lambda dirs, ticket: u"SENTINEL")
        assert status._find_ticket_file(root, gate, feature, u"10") == u"SENTINEL"

    def test_the_directory_expansion_stays_in_this_layer(self, tmp_path, monkeypatch):
        """**目錄清單由本層展開後傳進去**,共用模組不讀 `gate.TICKET_DIRS`。

        裁決(票 114):來源留在各自的呼叫端 —— `status` 從它已載入的 gate 取,
        `mcp_server` 用自己的常數。共用模組若自己去讀,那個來源就被綁死了。
        """
        root, gate, feature = self._dir_with(tmp_path)
        seen = {}

        def _spy(dirs, ticket):
            seen["dirs"] = list(dirs)
            seen["ticket"] = ticket
            return None

        monkeypatch.setattr(status.ticket_lookup, "find", _spy)
        status._find_ticket_file(root, gate, feature, u"10")
        assert seen["ticket"] == u"10"
        assert seen["dirs"] and all(os.path.isabs(d) for d in seen["dirs"]), seen
        assert any(d.replace(os.sep, "/").endswith(u"docs/tickets/%s" % feature)
                   for d in seen["dirs"]), seen


# ─────────────────────────────────────────────────────────────────────────────
# 票 105 乙段:Evidence 的 `report:` 行
#
# **它只印一行,不擋任何東西** —— 票面第六節逐字:
# 「一個沒有人看的 `status` 輸出,與沒有這一行,效果相同。」
# 選它的理由是便宜且零誤報,不是它解決了問題。
# ─────────────────────────────────────────────────────────────────────────────

def _reports(root, files):
    """在 root 底下造 `.dev/reports/`。`files=None` = 目錄不存在。"""
    d = os.path.join(root, ".dev", "reports")
    if files is None:
        return d
    os.makedirs(d)
    for name, body in files.items():
        with io.open(os.path.join(d, name), "w", encoding="utf-8") as f:
            f.write(body)
    return d


def _report_line(blob):
    """從 status 輸出取 `report:` 那一行。沒有回 None。

    **錨在行首**,不用 `in` —— 「輸出裡有 report 這個字」與
    「有一行叫 report:」是兩件事,而票面內文本來就會提到 report。
    """
    for ln in blob.splitlines():
        if ln.startswith(u"report:"):
            return ln
    return None


class TestEvidenceHasAReportLine:
    """票 105 乙:Evidence 區段要有 `report:` 一行,三種空各說不同的話。"""

    def test_there_is_a_report_line_at_all(self, tmp_path):
        root = _make_root(tmp_path)
        _reports(root, {u"2026-09-04T120000Z-ticket-105.md": u"## 第一段【給裁決者】\nx\n"})
        line = _report_line(render(root))
        assert line is not None, u"status 輸出裡沒有 report: 開頭的行"

    def test_the_line_carries_a_source(self, tmp_path):
        """`_line()` 的 `source` 是必填參數(判準 3)—— 這一行也不例外。"""
        root = _make_root(tmp_path)
        _reports(root, {u"2026-09-04T120000Z-ticket-105.md": u"x"})
        line = _report_line(render(root))
        assert line is not None and u"(source:" in line, line

    def test_the_line_names_the_latest_file(self, tmp_path):
        root = _make_root(tmp_path)
        _reports(root, {
            u"2026-01-01T000000Z-a.md": u"舊",
            u"2026-12-31T235959Z-b.md": u"新",
        })
        line = _report_line(render(root))
        assert line is not None and u"2026-12-31T235959Z-b.md" in line, line

    def test_the_three_empties_say_different_things(self, tmp_path):
        """與 `latest_report` 同一條(裁五「三種空同 ④」)。

        三句話兩兩不同 —— 否則「沒目錄」與「目錄空」在 status 上同形,
        而那兩者的處置不同:一個要去建,一個要去問這輪為什麼沒寫。
        """
        r1 = _make_root(tmp_path / u"none")
        _reports(r1, None)
        a = _report_line(render(r1))

        r2 = _make_root(tmp_path / u"empty")
        _reports(r2, {})
        b = _report_line(render(r2))

        assert a is not None and b is not None, (a, b)
        assert a != b, u"沒目錄與空目錄印了相同的一行:%r" % a


def _git_here(root, *args):
    """在 root 底下跑一條 git。測試自己用,不經 status 的 `_git`。

    **不共用被測模組的 helper** —— 用它來造材料的話,
    `_git` 壞掉時這一組會**一起壞掉而看起來像通過**(材料與量測同源,`F-152`)。
    """
    out = subprocess.run(["git"] + list(args), cwd=str(root),
                         capture_output=True)
    assert out.returncode == 0, (args, out.stderr.decode("utf-8", "replace"))
    return out.stdout.decode("utf-8", "replace").strip()


def _commit_at(root, msg, when):
    """在 root 造一筆 commit,**author/committer date 都釘在 `when`**。

    只釘 author date 的話 `--since` 讀的是 committer date,那筆會落在錯的一側 ——
    而錯的方向是「看起來沒過期」,剛好是最不會被發現的那一種。
    """
    p = root / (msg + u".txt")
    with io.open(str(p), "w", encoding="utf-8") as f:
        f.write(msg)
    _git_here(root, "add", "-A")
    env_args = ["-c", "user.name=t", "-c", "user.email=t@t",
                "-c", "commit.gpgsign=false"]
    out = subprocess.run(
        ["git"] + env_args + ["commit", "-m", msg, "--date", when],
        cwd=str(root), capture_output=True,
        env=dict(os.environ, GIT_COMMITTER_DATE=when,
                 GIT_AUTHOR_DATE=when))
    assert out.returncode == 0, out.stderr.decode("utf-8", "replace")


class TestReportLineSaysHowStaleTheReportIs:
    """票 105 收票追加:`report:` 的第三欄要答「**回報之後 HEAD 多了幾筆**」。

    🔴 **第一版做成 `git rev-list --count HEAD`(樹的總 commit 數)** ——
    那個數字回答的是「這棵樹有多大」,**對「這份回報過期沒有」一個字都沒說**,
    而它每一輪都會變大,所以**看起來像在動、像有意義**。

    判準:**這個欄位的值,能不能回答它旁邊那個欄名問的問題?**
    「report(回報)」問的是**新不新**,不是**樹多大**。

    ⚠ 而它之所以撐過了 25 條測試與三層驗收,是因為
    **一個每輪都會變大的數字,看起來像在動、像有意義** ——
    抓到它的是裁決者在 Desktop 上看一眼,不是任何一條斷言。
    """

    def _repo_with_report(self, tmp_path, report_stamp, commits):
        """造一個真 git repo,`.dev/reports/` 放一份檔,再依 `commits` 造 commit。

        `report_stamp` 是檔名裡的那個 UTC 戳(`YYYY-MM-DDTHHMMSSZ`)。
        """
        root = tmp_path / u"gitrepo"
        root.mkdir()
        _git_here(root, "init", "-q")
        _git_here(root, "config", "user.name", "t")
        _git_here(root, "config", "user.email", "t@t")

        d = root / ".dev" / "reports"
        d.mkdir(parents=True)
        with io.open(str(d / (report_stamp + u"-ticket-105.md")), "w",
                     encoding="utf-8") as f:
            f.write(u"## 第一段【給裁決者】\nx\n")

        for i, when in enumerate(commits):
            _commit_at(root, u"c%d" % i, when)
        return root

    def test_a_report_newer_than_head_counts_zero(self, tmp_path):
        """回報比 HEAD 新 → **0 筆**。"""
        root = self._repo_with_report(
            tmp_path, u"2026-09-04T083627Z",
            [u"2026-09-04T08:00:00+00:00"])          # commit 在回報之前
        val = status._report_value(str(root))
        assert u"回報後 0 筆" in val, val

    def test_commits_after_the_report_are_counted(self, tmp_path):
        """HEAD 有回報之後的 commit → **N 筆**。"""
        root = self._repo_with_report(
            tmp_path, u"2026-09-04T083627Z",
            [u"2026-09-04T08:00:00+00:00",          # 之前,不算
             u"2026-09-04T09:00:00+00:00",          # 之後,算
             u"2026-09-04T10:00:00+00:00"])         # 之後,算
        val = status._report_value(str(root))
        assert u"回報後 2 筆" in val, val

    def test_the_field_is_not_the_total_commit_count(self, tmp_path):
        """**負控:不得是樹的總 commit 數。**

        少了這一條,一個回 `rev-list --count HEAD` 的實作在「有 2 筆」那格
        會印 3(總數),而 `"回報後 2 筆" in val` 為假 —— 上面那條抓得到。
        但**「0 筆」那格抓不到**:一個 commit 的樹,總數 1、回報後 0,
        兩個數字不同所以碰巧會紅;**而兩筆 commit 且都在回報之前時,
        總數 2、回報後 0** —— 這一格才是真的分得開。
        """
        root = self._repo_with_report(
            tmp_path, u"2026-09-04T083627Z",
            [u"2026-09-04T07:00:00+00:00",
             u"2026-09-04T08:00:00+00:00"])         # 兩筆都在回報之前
        val = status._report_value(str(root))
        assert u"回報後 0 筆" in val, val
        assert u"樹共" not in val, u"仍在印樹的總數:%r" % val


# ═══════════════════════════════════════════════════════════════════════════
# 票 145(M1-a)Station 3 紅燈 —— status 依 run 事實判定紅綠
#
# 觀察契約:docs/audits/2026-10-02-m1a-station3-redlight-plan.md 一、A,
# 經票 145〈十三〉裁決修正(status 依 root 載入 redlight.py 的讀取函式;
# ODC-1 第 2、3 項 file-scoped)。
#
# **新介面(`record_session` / `load_runs` / `ticket_test_state`)只在測試函式內部取用**
# —— 它們不存在時只有這幾支失敗,不會讓整個檔收集錯誤。
#
# **既有的 `_make_root()` 一字不改**;要 redlight.py 的 fake repo 走下面的
# `_root_with_redlight()`(〈十三〉裁決 2 允許的 fake repo 基礎設施)。
# ═══════════════════════════════════════════════════════════════════════════

REAL_REDLIGHT = ROOT / ".claude" / "hooks" / "redlight.py"


def _load_redlight():
    """載入 repo 的 redlight.py(既有模組;新函式在測試內才取用)。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "redlight_for_status_test", str(REAL_REDLIGHT))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


redlight = _load_redlight()


def _root_with_redlight(base, **kw):
    """`_make_root()` 造出的最小 repo,再放一份 redlight.py 真檔複本。"""
    root = _make_root(base, **kw)
    shutil.copy2(str(REAL_REDLIGHT),
                 str(pathlib.Path(root) / ".claude" / "hooks" / "redlight.py"))
    return root


def _write_raw_lines(root, lines):
    """歷史原始紀錄**逐字**寫入 —— 不經 json 往返,一個位元組都不動。"""
    with io.open(str(pathlib.Path(root) / ".dev" / "test-runs.jsonl"),
                 "w", encoding="utf-8", newline="\n") as f:
        for ln in lines:
            f.write(ln + u"\n")


def _rows_of(root):
    p = pathlib.Path(root) / ".dev" / "test-runs.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in io.open(str(p), encoding="utf-8") if l.strip()]


# `.dev/test-runs.jsonl` 第 940 行與第 970 行原文(後者 = 票 139 `:39`)。
LEDGER_940 = (u'{"test_file": "tests/test_gate.py", "time": "2026-09-13T07:28:31.037700+00:00", '
              u'"result": "red", "failed_tests": ["TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce"], '
              u'"impl_file": ".claude/hooks/gate.py", "impl_exists": true, '
              u'"impl_hash": "2215f109bb73277248f78a6110a90bf51ec8a5f215251cf6089b86ebbe215170", '
              u'"ticket_id": "133"}')
LEDGER_970 = (u'{"test_file": "tests/test_gate.py", "time": "2026-09-13T12:26:18.644697+00:00", '
              u'"result": "green", "failed_tests": [], '
              u'"impl_file": ".claude/hooks/gate.py", "impl_exists": true, '
              u'"impl_hash": "446b2ef6f49fa0608d347d9969b49a0f3fa682d11cfe47b622feaa80cdbb7dc2", '
              u'"ticket_id": "133"}')

# `.dev/test-runs.jsonl` 第 2036 行原文(Station 3 baseline 寫入)。
LEDGER_2036 = (u'{"test_file": "tests/test_status.py", "time": "2026-10-02T13:27:56.450055+00:00", '
               u'"result": "green", "failed_tests": [], '
               u'"impl_file": ".claude/portable/status.py", "impl_exists": true, '
               u'"impl_hash": "bdc3a089a33d179dc72eb937401520c5ec257ba11037fb42083420a9560fadf0", '
               u'"ticket_id": "145"}')

NO_RUN = u"最近一次 run:無 run 證據 / 不可判定"


@pytest.fixture
def redlight_guard(tmp_path, monkeypatch):
    """本檔那一份 redlight 的路徑一律指到 tmp 的**另一個**位置。

    `record_session(root, ...)` 應該寫到 `root`;若實作忽略 `root` 而寫到模組常數,
    這裡讓它落在 guard 目錄 —— 測試會因為 status 讀不到而紅(出聲),
    **而不是把假紀錄寫進真實帳本**。
    """
    guard = tmp_path / u"guard"
    monkeypatch.setattr(redlight, "ROOT", str(guard))
    monkeypatch.setattr(redlight, "RUN_LOG", str(guard / ".dev" / "test-runs.jsonl"))
    monkeypatch.setattr(redlight, "PIPELINE", str(guard / ".dev" / "pipeline.json"))
    return guard


class TestTicket139:

    def test_a_narrow_all_skip_record_does_not_retire_the_earlier_red(self, tmp_path):
        """RL-6 票 139 歷史重現。現行 HEAD:**行為紅**。

        帳本只有兩筆、逐字取自真實帳本(第 940 行 red、第 970 行 = 票 139 `:39` green),
        沒有任何 synthetic 欄位。第 970 行沒有 run 事實 ⇒ coverage 未知 ⇒ 無退紅權
        (〈十一〉/〈十三〉ODC-1)⇒ 第 940 行那條紅不得因為「每檔最新一筆」而消失。
        現行 HEAD 取最新一筆 ⇒ 判成 green —— 那就是票 139 的 false green。
        """
        root = _root_with_redlight(tmp_path, ticket=u"133")
        _write_raw_lines(root, [LEDGER_940, LEDGER_970])
        out = render(root)
        red = _value_of(out, u"tests red under ticket 133")
        green = _value_of(out, u"tests green under ticket 133")
        assert u"tests/test_gate.py" not in green, (
            u"窄選、全部 skip 的那一筆把較早的紅蓋成綠了(票 139)\nred=%s\ngreen=%s"
            % (red, green))
        assert u"tests/test_gate.py" in red, red


class TestNarrowSelection:

    def test_a_later_green_without_run_facts_does_not_retire_x(self, tmp_path, monkeypatch):
        """RL-6b(舊寫入版)。現行 HEAD:**行為紅**。

        只用既有的 `redlight.record_run()` 寫:X 紅 → 同檔綠。那筆綠沒有 run 事實,
        看不出它有沒有選到 X ⇒ 不得退紅。現行 HEAD 取最新一筆 ⇒ 判成 green。
        """
        root = _root_with_redlight(tmp_path)
        monkeypatch.setattr(redlight, "ROOT", root)
        monkeypatch.setattr(redlight, "RUN_LOG",
                            str(pathlib.Path(root) / ".dev" / "test-runs.jsonl"))
        monkeypatch.setattr(redlight, "PIPELINE",
                            str(pathlib.Path(root) / ".dev" / "pipeline.json"))
        redlight.record_run("tests/test_x.py", passed=False, failed_tests=["test_target"])
        redlight.record_run("tests/test_x.py", passed=True, failed_tests=[])
        out = render(root)
        red = _value_of(out, u"tests red under ticket 99")
        green = _value_of(out, u"tests green under ticket 99")
        assert u"tests/test_x.py" not in green, (
            u"沒有 run 事實的綠把較早的紅蓋掉了\nred=%s\ngreen=%s" % (red, green))
        assert u"tests/test_x.py" in red, red

    def test_a_narrow_run_that_did_not_select_x_does_not_retire_x(self, tmp_path, redlight_guard):
        """RL-6b(run 事實版)。現行 HEAD:**介面紅**(`redlight.record_session` 不存在)。

        run1:X 失敗。run2:同檔窄選,選到的 Y 通過,**X 在 deselected** ⇒
        ODC-1 第 1 項不成立 ⇒ X 不退紅;run2 的 deselected 數事後可見(I7)。
        """
        root = _root_with_redlight(tmp_path)
        x = u"tests/test_x.py::test_target"
        y = u"tests/test_x.py::test_other"
        redlight.record_session(root, run_id=u"rl6b-1", time=u"2026-09-02T01:00:00+00:00",
                                ticket_id=u"99", exit_code=1, collected=[x, y],
                                deselected=[], outcomes={x: u"failed", y: u"passed"})
        redlight.record_session(root, run_id=u"rl6b-2", time=u"2026-09-02T02:00:00+00:00",
                                ticket_id=u"99", exit_code=0, collected=[x, y],
                                deselected=[x], outcomes={y: u"passed"})
        out = render(root)
        red = _value_of(out, u"tests red under ticket 99")
        assert u"tests/test_x.py" in red, red
        state = status.ticket_test_state(_rows_of(root), redlight.load_runs(root), u"99")
        assert x in state[u"tests/test_x.py"][u"unresolved"], state
        assert u"deselected 1" in _value_of(out, u"test-runs"), _value_of(out, u"test-runs")


class TestHistoricalRecords:

    def test_old_green_rows_are_shown_as_run_unknown_not_green(self, tmp_path):
        """RL-7 Historical evidence。現行 HEAD:**行為紅**(依 I5 判讀)。

        帳本第 2036 行原文 —— 一筆**真實**、來自一次確實全套通過的執行的 green;
        而帳本仍證明不了這件事。舊格式紀錄缺 run 事實 ⇒ 只能是「run 事實未知」,
        不得印在 green(Backward compatibility 2:不得推論 full pass)。
        """
        root = _root_with_redlight(tmp_path, ticket=u"145")
        _write_raw_lines(root, [LEDGER_2036])
        out = render(root)
        green = _value_of(out, u"tests green under ticket 145")
        assert u"tests/test_status.py" not in green, (
            u"沒有 run 事實的舊紀錄被印成 green:%s" % green)
        unknown = _value_of(out, u"tests green (run 事實未知) under ticket 145")
        assert unknown is not None and u"tests/test_status.py" in unknown, out


class TestOrphans:

    def test_a_renamed_red_test_is_orphaned_not_green(self, tmp_path, redlight_guard):
        """ODC-2 被刪除 / 改名的紅。現行 HEAD:**介面紅**(`redlight.record_session` 不存在)。

        run1:test_old 失敗。run2:同檔全選、全部通過,但收集不到 test_old(改名成 test_new)
        ⇒ 改名不視為延續 ⇒ 舊紅不得自動變綠,保留為可觀察的 orphaned。
        """
        root = _root_with_redlight(tmp_path)
        old = u"tests/test_x.py::test_old"
        new = u"tests/test_x.py::test_new"
        keep = u"tests/test_x.py::test_keep"
        redlight.record_session(root, run_id=u"odc2-1", time=u"2026-09-02T01:00:00+00:00",
                                ticket_id=u"99", exit_code=1, collected=[old, keep],
                                deselected=[], outcomes={old: u"failed", keep: u"passed"})
        _t_committed(root)
        blobs = dict((p, {u"worktree": _t_git(root, "hash-object", p).stdout.decode().strip(),
                          u"head": _t_git(root, "rev-parse", "HEAD:" + p).stdout.decode().strip()})
                     for p in (u"pyproject.toml", u"tests/conftest.py"))
        redlight.record_session(root, run_id=u"odc2-2", time=u"2026-09-02T02:00:00+00:00",
                                ticket_id=u"99", exit_code=0, collected=[new, keep],
                                deselected=[], outcomes={new: u"passed", keep: u"passed"},
                                invocation={u"args": [u"tests"]},
                                completeness={
                                    u"options": {u"lf": False, u"last_failed_no_failures": u"all",
                                                 u"stepwise": False, u"stepwise_skip": False,
                                                 u"maxfail": None, u"collectonly": False,
                                                 u"setuponly": False, u"setupplan": False,
                                                 u"runxfail": False, u"pythonwarnings": None,
                                                 u"trace": False, u"usepdb": False},
                                    u"cacheprovider_blocked": False, u"shouldstop": False,
                                    u"shouldfail": False,
                                    u"pre_narrowing": {u"tests/test_x.py": [new, keep]},
                                    u"plugins": [{u"name": u"main", u"kind": u"builtin"},
                                                 {u"name": u"tests/conftest.py",
                                                  u"kind": u"root_conftest"},
                                                 {u"name": u"anyio", u"kind": u"known_dist",
                                                  u"dists": [[u"anyio", u"4.15.0"]]}],
                                    u"blocked": [], u"override_ini": list(_T_FIXED_OVERRIDES),
                                    u"inifilename": None, u"inipath": u"pyproject.toml",
                                    u"config_blobs": blobs, u"pytest_version": u"9.1.1",
                                    u"optimize": 0, u"python_version": u"3.11",
                                    u"evidence_policy": _t_policy_facts(root)})
        out = render(root)
        orphaned = _value_of(out, u"tests orphaned under ticket 99")
        green = _value_of(out, u"tests green under ticket 99")
        assert orphaned is not None and u"tests/test_x.py" in orphaned, out
        assert u"test_old" in orphaned, orphaned
        assert u"tests/test_x.py" not in green, green


class TestRunEvidence:

    def test_no_run_at_all_is_not_zero_tests_and_not_a_pass(self, tmp_path, redlight_guard):
        """RL-5 No invocation。現行 HEAD:**介面紅**(`redlight.record_session` 不存在)。

        兩個 root:B 有一次 0 collected 的 run(狀態 C),A 完全沒有 run 事實(E)。
        兩者在輸出上必須分得開,且 A 不得被推論成任何 run 事實。
        """
        root_b = _root_with_redlight(tmp_path / u"b")
        redlight.record_session(root_b, run_id=u"rl5-c", time=u"2026-09-02T01:00:00+00:00",
                                ticket_id=u"99", exit_code=5, collected=[],
                                deselected=[], outcomes={})
        root_a = _root_with_redlight(tmp_path / u"a", with_runs=True)
        assert redlight.load_runs(root_a) == [], u"沒有 run 卻讀出了 run 事實"
        val_a = _value_of(render(root_a), u"test-runs")
        val_b = _value_of(render(root_b), u"test-runs")
        assert NO_RUN in val_a, val_a
        assert u"最近一次 run:C" in val_b, val_b
        assert val_a != val_b

    def test_no_producer_means_undecidable_not_green_not_c(self, tmp_path, redlight_guard):
        """ODC-3 producer 未載入。現行 HEAD:**介面紅**(`redlight.load_runs` 不存在)。

        帳本有舊格式紀錄、沒有任何 run 事實(producer 沒被載入時就是這樣)⇒
        記為「無證據 / 不可判定」;不得表示為 green,也不得推論為 C。
        """
        root = _root_with_redlight(tmp_path, ticket=u"145")
        _write_raw_lines(root, [LEDGER_2036])
        assert redlight.load_runs(root) == [], u"沒有 run 卻讀出了 run 事實"
        out = render(root)
        val = _value_of(out, u"test-runs")
        assert NO_RUN in val, val
        assert u"最近一次 run:C" not in val, val
        assert u"tests/test_status.py" not in _value_of(out, u"tests green under ticket 145")


# ═══════════════════════════════════════════════════════════════════════════
# 票 145 Station 3b 紅燈 —— producer → 持久化 run 事實 → status 的串接(F4)
#
# 依據:票 145〈十七〉F1–F4、裁決 1–4、Invariant「Absence is not coverage」。
#
# **串接的做法**:載入 `tests/conftest.py`,把它的 `_redlight` 換成本檔那一份、
# `_ROOT` 指到 tmp root;本檔那一份 redlight 的 ROOT / RUN_LOG / PIPELINE 也指到
# 同一個 tmp root。於是 producer 寫的逐檔紀錄與 run 事實都落在 tmp root,
# status 再依 root 載入 redlight.py 讀回 —— 三段走的是真的程式碼,只有 pytest 本身是假的。
#
# **手寫 JSON 只在 B5 / B9**:缺欄與錯型別是寫入函式寫不出來的形狀(它們的重點正是
# 「不是正常 producer 產生的紀錄」)。其餘一律透過 `record_run` / `record_session` /
# conftest hooks 產生。
# ═══════════════════════════════════════════════════════════════════════════

CHAIN_X = u"tests/test_x.py::test_target"
CHAIN_Y = u"tests/test_x.py::test_other"
FAR_FUTURE = u"2999-01-01T00:00:00+00:00"


class _ChainItem:
    def __init__(self, nodeid):
        self.nodeid = nodeid


class _ChainCollectRep:
    def __init__(self, nodeid, failed=False):
        self.nodeid = nodeid
        self.failed = failed
        self.passed = not failed
        self.outcome = "failed" if failed else "passed"


class _ChainRunRep:
    def __init__(self, nodeid, when, outcome):
        self.nodeid = nodeid
        self.fspath = nodeid.split("::", 1)[0]
        self.when = when
        self.outcome = outcome
        self.passed = outcome == "passed"
        self.failed = outcome == "failed"
        self.skipped = outcome == "skipped"


def _chain_reports(nodeid, outcome):
    if outcome == "skipped":
        return [_ChainRunRep(nodeid, "setup", "skipped"),
                _ChainRunRep(nodeid, "teardown", "passed")]
    return [_ChainRunRep(nodeid, "setup", "passed"),
            _ChainRunRep(nodeid, "call", outcome),
            _ChainRunRep(nodeid, "teardown", "passed")]


class _ChainInvocationParams:
    def __init__(self, d):
        self.dir = d


class _ChainOption:
    pyargs = False


class _ChainConfig:
    def __init__(self, args, root):
        self.args = list(args)
        self.rootpath = root
        self.invocation_params = _ChainInvocationParams(root)
        self.option = _ChainOption()

    def getoption(self, name, default=None):
        return getattr(self.option, name, default)


class _ChainSession:
    def __init__(self, items, args, root):
        self.items = list(items)
        self.testscollected = len(self.items)
        self.config = _ChainConfig(args, root)


# 票 145 Station 4g 授權 G3(〈四十八〉48.1 第 5 點;規劃檔 S3g-0 P2-B):driver 把 conftest 所見的版本事實
# 固定在能力邊界內,正控不再依賴執行它的直譯器 / pytest 版本。模組載入當下的真實版本記在這裡 ——
# 測試在呼叫 driver **之前**自己設過 `pytest.__version__` 時不覆蓋它(與 tests/test_redlight.py 同式)。
_REAL_PYTEST_VERSION = pytest.__version__
_PINNED_PYTEST_VERSION = u"9.1.1"
_PINNED_PYTHON = (3, 11, 0, u"final", 0)


def _chain_conftest(root, monkeypatch):
    """載入 tests/conftest.py,並把它與本檔那一份 redlight 的所有寫入都導到 `root`。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "conftest_for_status_chain", str(ROOT / "tests" / "conftest.py"))
    c = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(c)
    monkeypatch.setattr(redlight, "ROOT", root)
    monkeypatch.setattr(redlight, "RUN_LOG",
                        str(pathlib.Path(root) / ".dev" / "test-runs.jsonl"))
    monkeypatch.setattr(redlight, "PIPELINE",
                        str(pathlib.Path(root) / ".dev" / "pipeline.json"))
    monkeypatch.setattr(c, "_redlight", redlight)
    monkeypatch.setattr(c, "_ROOT", pathlib.Path(root))
    monkeypatch.setattr(c, "sys", _e_sys(optimize=sys.flags.optimize,
                                         version_info=_EVersion(*_PINNED_PYTHON)), raising=False)
    if pytest.__version__ == _REAL_PYTEST_VERSION:
        monkeypatch.setattr(pytest, "__version__", _PINNED_PYTEST_VERSION)
    return c


def _chain_drive(c, root, args, selected=(), deselected=(), outcomes=None,
                 collect_errors=(), exitstatus=0):
    """依 pytest 的呼叫順序驅動 conftest hooks;session 帶 `config.args`。驅動前重置累積狀態。"""
    def hook(name):
        return getattr(c, name, None) or (lambda *a, **k: None)

    c._outcomes.clear()
    run = getattr(c, "_run", None)
    if isinstance(run, dict):
        for k, v in list(run.items()):
            if hasattr(v, "clear"):
                v.clear()
            else:
                run[k] = None
    files = sorted(set(n.split("::", 1)[0] for n in list(selected) + list(deselected)))
    for f in files:
        hook("pytest_collectreport")(_ChainCollectRep(f))
    for f in collect_errors:
        hook("pytest_collectreport")(_ChainCollectRep(f, failed=True))
    gone = [_ChainItem(n) for n in deselected]
    if gone:
        hook("pytest_deselected")(gone)
    session = _ChainSession([_ChainItem(n) for n in selected], args, pathlib.Path(root))
    hook("pytest_collection_finish")(session)
    for nodeid, outcome in (outcomes or {}).items():
        for rep in _chain_reports(nodeid, outcome):
            hook("pytest_runtest_logreport")(rep)
    hook("pytest_sessionfinish")(session, exitstatus)


def _seed_red(failed_tests):
    """以既有的 `record_run()` 寫一筆 tests/test_x.py 的 red(本檔 redlight 已導到 root)。"""
    redlight.record_run("tests/test_x.py", passed=False, failed_tests=failed_tests)


def _append_raw_session(root, rec):
    """手寫一筆 session(只給 B5 / B9 用:寫入函式寫不出缺欄 / 錯型別的形狀)。"""
    path = redlight.session_log(root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + u"\n")


def _lines_of(root):
    out = render(root)
    return {k: _value_of(out, u"tests %s under ticket 99" % k)
            for k in (u"red", u"green", u"orphaned")}


class TestCoverageChain:

    def test_b2_a_nodeid_run_does_not_retire_an_unidentified_red(self, tmp_path, monkeypatch):
        """B2(F3 串接)。分類:behavior-red。

        舊紅的 `failed_tests` 為空(身分不明 ⇒ 視同全檔皆紅)。之後經 producer 以 nodeid
        指名只跑 test_a 且 passed —— 沒收集到的身分不產生 deselected,但那不是整檔涵蓋。
        ⇒ 該檔仍在 red、不在 green。
        """
        root = _root_with_redlight(tmp_path)
        c = _chain_conftest(root, monkeypatch)
        _seed_red([])
        a = u"tests/test_x.py::test_a"
        _chain_drive(c, root, [a], selected=[a], outcomes={a: "passed"}, exitstatus=0)
        got = _lines_of(root)
        assert u"tests/test_x.py" not in got[u"green"], got
        assert u"tests/test_x.py" in got[u"red"], got

    def test_b3_a_nodeid_run_does_not_orphan_a_known_red(self, tmp_path, monkeypatch):
        """B3(F3 串接)。分類:behavior-red。

        已知紅身分 test_b。之後經 producer 以 nodeid 指名只跑 test_a 且 passed ——
        test_b 沒被收集,只是因為沒被指名(Absence is not coverage)。
        ⇒ test_b 仍在 red、不在 orphaned。
        """
        root = _root_with_redlight(tmp_path)
        c = _chain_conftest(root, monkeypatch)
        _seed_red(["test_b"])
        a = u"tests/test_x.py::test_a"
        _chain_drive(c, root, [a], selected=[a], outcomes={a: "passed"}, exitstatus=0)
        got = _lines_of(root)
        assert u"tests/test_x.py" not in got[u"orphaned"], got
        assert u"tests/test_x.py" in got[u"red"], got


class TestDStateRetiresNothing:

    def test_b4_a_d_run_with_a_collection_error_elsewhere_retires_nothing(
            self, tmp_path, monkeypatch):
        """B4(F2)。分類:behavior-red。

        tests/test_x.py 的 X 為紅。之後一個 run:exit 1、另一檔 tests/test_y.py 收集錯誤、
        X passed —— `run_state` 為 D ⇒ 整個 run 沒有退紅權、不得使任何檔成為 green。
        ⇒ test_x.py 仍紅、不在 green。
        """
        root = _root_with_redlight(tmp_path)
        c = _chain_conftest(root, monkeypatch)
        _seed_red(["test_target"])
        _chain_drive(c, root, ["tests"], selected=[CHAIN_X], outcomes={CHAIN_X: "passed"},
                     collect_errors=["tests/test_y.py"], exitstatus=1)
        got = _lines_of(root)
        assert u"tests/test_x.py" not in got[u"green"], got
        assert u"tests/test_x.py" in got[u"red"], got


class TestSessionSchemaFailClosed:

    def test_b5_a_session_without_deselected_retires_nothing(self, tmp_path, monkeypatch):
        """B5(F1 缺欄)。分類:behavior-red。

        X 為紅。之後一筆 session **缺 `deselected` 欄位**、X passed(手寫:寫入函式寫不出缺欄)。
        缺欄不得被當成「沒有 deselected」⇒ X 仍紅、不在 green。
        """
        root = _root_with_redlight(tmp_path)
        _chain_conftest(root, monkeypatch)
        _seed_red(["test_target"])
        _append_raw_session(root, {"kind": "session", "run_id": "b5", "time": FAR_FUTURE,
                                   "ticket_id": "99", "exit_code": 0,
                                   "collected": [CHAIN_X],
                                   "outcomes": {CHAIN_X: "passed"}})
        got = _lines_of(root)
        assert u"tests/test_x.py" not in got[u"green"], got
        assert u"tests/test_x.py" in got[u"red"], got

    def test_b7_an_outcome_outside_collected_retires_nothing(self, tmp_path, monkeypatch):
        """B7(F1 身分不一致)。分類:behavior-red。

        X 為紅。之後一筆 session 的 outcomes 含一個**不在 collected 裡**的身分(passed),
        X 也 passed —— outcome 身分不屬於本次 selected ⇒ 該 run 不得進入正常語意。
        ⇒ X 仍紅、不在 green。
        """
        root = _root_with_redlight(tmp_path)
        _chain_conftest(root, monkeypatch)
        _seed_red(["test_target"])
        ghost = u"tests/test_x.py::test_ghost"
        redlight.record_session(root, run_id=u"b7", time=FAR_FUTURE, ticket_id=u"99",
                                exit_code=0, collected=[CHAIN_X], deselected=[],
                                outcomes={CHAIN_X: u"passed", ghost: u"passed"})
        got = _lines_of(root)
        assert u"tests/test_x.py" not in got[u"green"], got
        assert u"tests/test_x.py" in got[u"red"], got

    def test_b9_a_string_deselected_retires_nothing_and_orphans_nothing(
            self, tmp_path, monkeypatch):
        """B9(F1 型別不符)。分類:behavior-red。

        X 為紅。之後一筆 session 欄位都在,但 `deselected` 是**字串**而不是 list
        (手寫:寫入函式會把它拆成字元 list,寫不出這個形狀)、X passed。
        錯型別不得照常迭代 ⇒ 不退 X 的紅、該檔不為 green、不產生 orphan。
        """
        root = _root_with_redlight(tmp_path)
        _chain_conftest(root, monkeypatch)
        _seed_red(["test_target"])
        _append_raw_session(root, {"kind": "session", "run_id": "b9", "time": FAR_FUTURE,
                                   "ticket_id": "99", "exit_code": 0,
                                   "collected": [CHAIN_X, CHAIN_Y],
                                   "deselected": "tests/test_x.py::test_y",
                                   "outcomes": {CHAIN_X: "passed", CHAIN_Y: "passed"}})
        got = _lines_of(root)
        assert u"tests/test_x.py" not in got[u"green"], got
        assert u"tests/test_x.py" in got[u"red"], got
        assert u"tests/test_x.py" not in got[u"orphaned"], got


class TestAbsenceIsNotCoverage:

    def test_b8_a_run_without_coverage_facts_does_not_orphan(self, tmp_path, monkeypatch):
        """B8(Absence is not coverage)。分類:behavior-red。

        已知紅身分 test_old。之後一筆**沒有 full_file_coverage 事實**的 session
        (直接以 `record_session` 寫、不帶任何涵蓋資訊)收集不到 test_old ——
        沒出現不代表已刪除或改名 ⇒ 不在 orphaned,且仍在 red。
        """
        root = _root_with_redlight(tmp_path)
        _chain_conftest(root, monkeypatch)
        _seed_red(["test_old"])
        new = u"tests/test_x.py::test_new"
        keep = u"tests/test_x.py::test_keep"
        redlight.record_session(root, run_id=u"b8", time=FAR_FUTURE, ticket_id=u"99",
                                exit_code=0, collected=[new, keep], deselected=[],
                                outcomes={new: u"passed", keep: u"passed"})
        got = _lines_of(root)
        assert u"tests/test_x.py" not in got[u"orphaned"], got
        assert u"tests/test_x.py" in got[u"red"], got


class TestChainRegressionLocks:

    def test_l1_three_skipped_645_deselected_keeps_the_red(self, tmp_path, monkeypatch):
        """L1(RL-6 串接;F4)。分類:regression-lock(現行實作必須通過)。

        X 為紅。之後經 producer 產生「3 skipped、645 deselected、0 passed」的 run
        (X 在 deselected 裡)⇒ 仍紅。
        """
        root = _root_with_redlight(tmp_path)
        c = _chain_conftest(root, monkeypatch)
        _seed_red(["test_target"])
        chosen = [u"tests/test_x.py::test_symlink_%d" % i for i in range(3)]
        gone = [CHAIN_X] + [u"tests/test_x.py::test_other_%d" % i for i in range(644)]
        _chain_drive(c, root, ["tests/test_x.py"], selected=chosen, deselected=gone,
                     outcomes={n: "skipped" for n in chosen}, exitstatus=0)
        got = _lines_of(root)
        assert u"tests/test_x.py" in got[u"red"], got
        assert u"tests/test_x.py" not in got[u"green"], got

    def test_l2_an_interrupted_run_keeps_the_red(self, tmp_path, monkeypatch):
        """L2(RL-4 串接;F4)。分類:regression-lock(現行實作必須通過)。

        X 為紅。之後經 producer 產生 exit 2(中斷)且 X passed 的 run ⇒ 仍紅。
        """
        root = _root_with_redlight(tmp_path)
        c = _chain_conftest(root, monkeypatch)
        _seed_red(["test_target"])
        _chain_drive(c, root, ["tests"], selected=[CHAIN_X], outcomes={CHAIN_X: "passed"},
                     exitstatus=2)
        got = _lines_of(root)
        assert u"tests/test_x.py" in got[u"red"], got
        assert u"tests/test_x.py" not in got[u"green"], got

    def test_l3_a_full_directory_run_retires_the_red(self, tmp_path, monkeypatch):
        """L3(正向對照;F4)。分類:regression-lock(現行實作必須通過;4b 後仍必須通過)。

        X 為紅。之後經 producer 以位置參數 `tests`(整個目錄)跑、該檔全選、X passed、
        無 failure、exit 0 ⇒ X 退紅、該檔在 green。防止修正過頭變成「永遠退不了紅」。
        """
        root = _root_with_redlight(tmp_path)
        c = _chain_conftest(root, monkeypatch)
        _seed_red(["test_target"])
        _t_committed(root)
        _t_drive(c, root, {u"tests/test_x.py": [CHAIN_X, CHAIN_Y]}, [CHAIN_X, CHAIN_Y],
                 {CHAIN_X: "passed", CHAIN_Y: "passed"}, exitstatus=0)
        got = _lines_of(root)
        assert u"tests/test_x.py" in got[u"green"], got
        assert u"tests/test_x.py" not in got[u"red"], got


# ═══════════════════════════════════════════════════════════════════════════
# 票 145 Station 3b 補件 —— B11:schema 不合格的 session 必須可被觀察到
# ═══════════════════════════════════════════════════════════════════════════


def _evidence_and_derived(out):
    """render 輸出中 `=== Evidence ===` 與 `=== Derived ===` 兩個區塊的全文。

    Repository 區塊(含 `generated` 時鐘行)不納入 —— 它兩次 render 之間本來就會變。
    """
    blocks = out.split(u"\n\n")
    keep = [b for b in blocks
            if b.startswith(u"=== Evidence ===") or b.startswith(u"=== Derived ===")]
    return u"\n\n".join(keep)


class TestMalformedSessionIsVisible:

    def test_b11_a_malformed_session_is_neither_dropped_silently_nor_read_as_normal(
            self, tmp_path, monkeypatch):
        """B11(F1;〈十七〉3b 補件)。分類:behavior-red。

        同一個 root 的前後比較:先只有 X 的紅(無任何 session),render 一次;
        再追加一筆 schema 不合格的 session(`deselected` 為字串、X passed;手寫 ——
        寫入函式寫不出這個形狀),其餘資料不動,再 render 一次。
        ⇒ Evidence / Derived 必須與前次不同(不得靜默丟棄;表示位置與文字由 4b 決定);
          不得顯示為正常狀態 A / B / C / F;X 所在檔仍紅、不 green、不 orphan。
        """
        root = _root_with_redlight(tmp_path)
        _chain_conftest(root, monkeypatch)
        _seed_red(["test_target"])
        before = _evidence_and_derived(render(root))
        _append_raw_session(root, {"kind": "session", "run_id": "b11", "time": FAR_FUTURE,
                                   "ticket_id": "99", "exit_code": 0,
                                   "collected": [CHAIN_X],
                                   "deselected": "tests/test_x.py::test_y",
                                   "outcomes": {CHAIN_X: "passed"}})
        out = render(root)
        after = _evidence_and_derived(out)
        assert after != before, u"不合格的 session 被靜默丟棄:前後輸出相同\n%s" % after
        for state in (u"A", u"B", u"C", u"F"):
            assert u"最近一次 run:%s" % state not in after, (
                u"不合格的 session 被當成正常狀態 %s\n%s" % (state, after))
        red = _value_of(out, u"tests red under ticket 99")
        green = _value_of(out, u"tests green under ticket 99")
        orphaned = _value_of(out, u"tests orphaned under ticket 99")
        assert u"tests/test_x.py" in red, after
        assert u"tests/test_x.py" not in green, after
        assert u"tests/test_x.py" not in orphaned, after


# ═══════════════════════════════════════════════════════════════════════════
# 票 145 Station 3c 紅燈 —— 選擇 / 執行完整性與 plugin 邊界(串接;〈二十三〉)
#
# 合約:票 145〈二十三〉7、8。每一支都經**真實 tests/conftest.py** 的 hook(`_chain_conftest`)
# 寫入 tmp root 的帳本,再由 status / `file_coverage` 讀回判定 —— 不直接餵分類好的資料。
# 規劃:docs/audits/2026-10-02-m1a-station3c-redlight-plan.md P4。
#
# driver(`_s_drive`)的呼叫順序與 tests/test_redlight.py 的 `_c_drive` 相同:
# 每個檔先對 conftest 的 `pytest_make_collect_report`(new-style wrapper)送出**完整**結果,
# wrapper 返回後才**就地**縮小 `report.result`(模擬外層 `LFPluginCollWrapper`,
# `_pytest/cacheprovider.py:282`);縮小掉的身分**不**送 `pytest_deselected`。
# 假 item / collector 是 `pytest.Item` / `pytest.File` 的子類(`object.__new__`,不經 `from_parent`)。
# 本段 helper 全部新寫;既有 helper(`_chain_conftest` / `_seed_red` / `_lines_of`)只呼叫、不修改。
# ═══════════════════════════════════════════════════════════════════════════

import inspect as _s_inspect
import types as _s_types


class _SItem(pytest.Item):
    def runtest(self):
        pass


class _SFile(pytest.File):
    def collect(self):
        return []


def _s_item(nodeid):
    it = object.__new__(_SItem)
    it._nodeid = nodeid
    it.name = nodeid.split(u"::")[-1]
    return it


def _s_file(root, path):
    f = object.__new__(_SFile)
    f._nodeid = path
    f.name = path.split(u"/")[-1]
    f.path = pathlib.Path(str(root)) / path
    return f


class _SCollectReport:
    def __init__(self, nodeid, result, failed=False):
        self.nodeid = nodeid
        self.result = list(result)
        self.failed = failed
        self.passed = not failed
        self.skipped = False
        self.outcome = "failed" if failed else "passed"


class _SRunReport:
    def __init__(self, nodeid, when, outcome, wasxfail=None):
        self.nodeid = nodeid
        self.fspath = nodeid.split(u"::", 1)[0]
        self.when = when
        self.outcome = outcome
        self.passed = outcome == "passed"
        self.failed = outcome == "failed"
        self.skipped = outcome == "skipped"
        if wasxfail is not None:
            self.wasxfail = wasxfail


def _s_reports(nodeid, kind):
    """passed / failed:setup → call → teardown;skipped:setup(skipped)→ teardown;
    xfail:call 為 skipped 且帶 `wasxfail`;setup_only:只有 setup(call 中 `pytest.exit()`);
    setup_teardown:沒有 call(`--setup-only`)。"""
    if kind in ("passed", "failed"):
        return [_SRunReport(nodeid, "setup", "passed"),
                _SRunReport(nodeid, "call", kind),
                _SRunReport(nodeid, "teardown", "passed")]
    if kind == "skipped":
        return [_SRunReport(nodeid, "setup", "skipped"),
                _SRunReport(nodeid, "teardown", "passed")]
    if kind == "xfail":
        return [_SRunReport(nodeid, "setup", "passed"),
                _SRunReport(nodeid, "call", "skipped", wasxfail="reason"),
                _SRunReport(nodeid, "teardown", "passed")]
    if kind == "setup_only":
        return [_SRunReport(nodeid, "setup", "passed")]
    if kind == "setup_teardown":
        return [_SRunReport(nodeid, "setup", "passed"),
                _SRunReport(nodeid, "teardown", "passed")]
    raise ValueError(kind)


_S_OPTION_DEFAULTS = {
    "pyargs": False, "lf": False, "last_failed_no_failures": "all",
    "failedfirst": False, "newfirst": False, "stepwise": False, "stepwise_skip": False,
    "stepwise_reset": False, "maxfail": None, "collectonly": False, "setuponly": False,
    "setupplan": False, "setupshow": False, "keyword": "", "markexpr": "",
    "deselect": None, "ignore": None, "ignore_glob": None,
    "runxfail": False, "pythonwarnings": None, "trace": False,
    "usepdb": False,
}


class _CompletenessOption:
    """`config.option`,預設「全部關閉」;`missing` 中的屬性不存在。"""

    def __init__(self, missing=(), **overrides):
        values = dict(_S_OPTION_DEFAULTS)
        values.update(overrides)
        for k in missing:
            values.pop(k, None)
        self.__dict__.update(values)


class _SDist:
    def __init__(self, name):
        self.project_name = name
        self.version = "0"
        self.metadata = {"name": name}


class _SFakePluginManager:
    """`config.pluginmanager`:list_name_plugin / list_plugin_distinfo / is_blocked / get_plugin。"""

    def __init__(self, name_plugins, distinfo=(), blocked=()):
        self._name_plugins = list(name_plugins)
        self._distinfo = list(distinfo)
        self._blocked = set(blocked)

    def list_name_plugin(self):
        return list(self._name_plugins)

    def list_plugin_distinfo(self):
        return list(self._distinfo)

    def is_blocked(self, name):
        return name in self._blocked

    def get_plugin(self, name):
        return dict(self._name_plugins).get(name)

    def has_plugin(self, name):
        return self.get_plugin(name) is not None


def _s_internal(module, label):
    return type(label, (), {"__module__": module})()


def _s_plugins(c, root, extra=(), extra_dist=()):
    """白名單內的 plugin 集合(builtin / root_conftest / known_dist)+ `extra`。

    builtin:模組 `_pytest.main`,以及數字名稱(`str(id(...))`)、類別定義在 `_pytest.config` 的物件;
    root_conftest:`<root>/tests/conftest.py` 的絕對路徑 → producer 本身;
    known_dist:`anyio.pytest_plugin`,在 `list_plugin_distinfo()` 中與 dist `anyio` 配對。
    """
    builtin_mod = _s_types.ModuleType("_pytest.main")
    internal = _s_internal("_pytest.config", "_InternalHelper")
    anyio_mod = _s_types.ModuleType("anyio.pytest_plugin")
    names = [(u"main", builtin_mod),
             (str(id(internal)), internal),
             (os.path.join(str(root), u"tests", u"conftest.py"), c),
             (u"anyio", anyio_mod)] + list(extra)
    dist = [(anyio_mod, _SDist("anyio"))] + list(extra_dist)
    return _SFakePluginManager(names, dist)


class _SInvocationParams:
    def __init__(self, d):
        self.dir = d


class _SConfig:
    def __init__(self, root, option, pluginmanager, args=(u"tests",)):
        self.args = list(args)
        self.args_source = pytest.Config.ArgsSource.TESTPATHS
        self.rootpath = pathlib.Path(str(root))
        self.invocation_params = _SInvocationParams(pathlib.Path(str(root)))
        self.option = option
        self.pluginmanager = pluginmanager

    def getoption(self, name, default=None, skip=False):
        return getattr(self.option, name, default)


class _CompletenessSession:
    def __init__(self, items, config):
        self.items = list(items)
        self.testscollected = len(self.items)
        self.config = config
        self.shouldstop = False
        self.shouldfail = False


def _s_call_collect_wrapper(c, collector, report):
    fn = getattr(c, "pytest_make_collect_report", None)
    if fn is None:
        return
    gen = fn(collector)
    if not _s_inspect.isgenerator(gen):
        return
    next(gen)
    try:
        gen.send(report)
    except StopIteration:
        pass


def _s_drive(c, root, files, selected, outcomes=None, deselected=(), filtered_out=(),
             collect_errors=(), exitstatus=0, option=None, pm=None,
             shouldstop=False, shouldfail=False):
    """依 pytest 9.1.1 的呼叫順序驅動真實 conftest;`files` = {檔: 縮小前完整 nodeid 清單}。"""
    def hook(name):
        return getattr(c, name, None) or (lambda *a, **k: None)

    if pm is None:
        pm = _s_plugins(c, root)
    dropped = set(filtered_out)
    for path in sorted(files):
        report = _SCollectReport(path, [_s_item(n) for n in files[path]])
        _s_call_collect_wrapper(c, _s_file(root, path), report)
        report.result[:] = [x for x in report.result if x.nodeid not in dropped]
        hook("pytest_collectreport")(report)
    for path in collect_errors:
        hook("pytest_collectreport")(_SCollectReport(path, [], failed=True))
    gone = [_s_item(n) for n in deselected]
    if gone:
        hook("pytest_deselected")(gone)
    session = _CompletenessSession([_s_item(n) for n in selected],
                                   _SConfig(root, option or _CompletenessOption(), pm))
    hook("pytest_collection_finish")(session)
    for nodeid, kind in (outcomes or {}).items():
        for rep in _s_reports(nodeid, kind):
            hook("pytest_runtest_logreport")(rep)
    session.shouldstop = shouldstop
    session.shouldfail = shouldfail
    hook("pytest_sessionfinish")(session, exitstatus)


S_A = u"tests/test_x.py::test_a"
S_B = u"tests/test_x.py::test_b"
S_C = u"tests/test_x.py::test_c"
S_XF = u"tests/test_x.py::test_xf"
S_NEW = u"tests/test_x.py::test_new"
S_KEEP = u"tests/test_x.py::test_keep"
S_W = u"tests/test_w.py::test_w_a"


def _s_lf_pm(c, root):
    """`--lf` 真的過濾時的 plugin 集合:多了 `lfplugin-collwrapper` 與 `lfplugin-collskip`(皆為 builtin)。"""
    return _s_plugins(c, root, extra=[
        (u"lfplugin-collwrapper", _s_internal("_pytest.cacheprovider", "LFPluginCollWrapper")),
        (u"lfplugin-collskip", _s_internal("_pytest.cacheprovider", "LFPluginCollSkipfiles"))])


def _s_drive_lf(c, root):
    """`--lf`:縮小前全集 [S_A, S_B],S_A 在收集期被悄悄移除,只跑 S_B 且 passed,exit 0。"""
    _s_drive(c, root, {u"tests/test_x.py": [S_A, S_B]}, selected=[S_B],
             outcomes={S_B: "passed"}, filtered_out=[S_A],
             option=_CompletenessOption(lf=True), pm=_s_lf_pm(c, root), exitstatus=0)


def _s_drive_exitfirst(c, root, x_ids):
    """`-x`:S_W failed ⇒ `shouldfail`、exit 1;X 全收集(`x_ids`)但沒有執行。"""
    _s_drive(c, root, {u"tests/test_w.py": [S_W], u"tests/test_x.py": list(x_ids)},
             selected=[S_W] + list(x_ids), outcomes={S_W: "failed"},
             option=_CompletenessOption(maxfail=1),
             shouldfail=u"stopping after 1 failures", exitstatus=1)


class TestSilentNarrowingChain:

    def test_c3a_lf_narrowing_does_not_retire_an_unidentified_red(self, tmp_path, monkeypatch):
        """C3a-2(〈二十三〉7 (ii)(v))。分類:behavior-red。

        test_x.py 有身分不明的整檔紅;之後一次 `--lf` 只跑了 S_B(S_A 被悄悄移除)⇒ 仍紅、不 green。
        d122df4 上失敗的原因:`.claude/hooks/redlight.py:423-426` 判 `"true"` ⇒
        `.claude/portable/status.py:470-472` 整檔紅只看本 run 收集到的身分 ⇒ 退紅;`:475` green。
        """
        root = _root_with_redlight(tmp_path)
        c = _chain_conftest(root, monkeypatch)
        _seed_red([])
        _s_drive_lf(c, root)
        got = _lines_of(root)
        assert u"tests/test_x.py" in got[u"red"], got
        assert u"tests/test_x.py" not in got[u"green"], got

    def test_c3a_lf_narrowing_does_not_make_a_clean_file_green(self, tmp_path, monkeypatch):
        """C3a-3(〈二十一〉21.2 附註 2;〈二十三〉7 (ii)(v))。分類:behavior-red。

        test_x.py 先前沒有紅;一次 `--lf` 只跑了 S_B ⇒ 不得 green。
        d122df4 上失敗的原因:`.claude/hooks/redlight.py:423-426` 判 `"true"` ⇒
        `.claude/portable/status.py:475` `green_now = True`。
        """
        root = _root_with_redlight(tmp_path)
        c = _chain_conftest(root, monkeypatch)
        _s_drive_lf(c, root)
        got = _lines_of(root)
        assert u"tests/test_x.py" not in got[u"green"], got


class TestEarlyStopChain:

    def test_c3c_exitfirst_does_not_orphan_a_known_red(self, tmp_path, monkeypatch):
        """C3c-2(〈二十三〉7 (iii)(iv)(vi))。分類:behavior-red。

        X 有已知紅 test_old;之後一次 `-x` 在 W 停下,X 收集到 [test_new, test_keep] 但沒執行
        ⇒ X 仍紅、不 orphan(提前停止的 run 沒有 orphan 權)。
        d122df4 上失敗的原因:`.claude/hooks/redlight.py:423-426` 判 `"true"` ⇒
        `.claude/portable/status.py:464-468` 把 test_old 移入 orphan。
        """
        root = _root_with_redlight(tmp_path)
        c = _chain_conftest(root, monkeypatch)
        _seed_red(["test_old"])
        _s_drive_exitfirst(c, root, [S_NEW, S_KEEP])
        got = _lines_of(root)
        assert u"tests/test_x.py" not in got[u"orphaned"], got
        assert u"tests/test_x.py" in got[u"red"], got

    def test_c3c_exitfirst_does_not_make_unrun_files_green(self, tmp_path, monkeypatch):
        """C3c-3。分類:regression-lock。

        一次 `-x` 在 W 停下,X 全收集但沒有任何 outcome ⇒ X 不 green
        (d122df4:`.claude/portable/status.py:475` 沒有 passed ⇒ 不 green)。
        """
        root = _root_with_redlight(tmp_path)
        c = _chain_conftest(root, monkeypatch)
        _s_drive_exitfirst(c, root, [S_A, S_B])
        got = _lines_of(root)
        assert u"tests/test_x.py" not in got[u"green"], got

    def test_c3c_stepwise_stop_is_d_and_retires_nothing(self, tmp_path, monkeypatch):
        """C3c-4。分類:regression-lock。

        `--sw`:S_W failed ⇒ `shouldstop` ⇒ `Interrupted` ⇒ exit 2(`_pytest/stepwise.py:183-188`、
        `_pytest/main.py:411-412`)。X 的已知紅 CHAIN_X 本次 passed ⇒ D 沒有退紅權:仍紅、不 green、不 orphan
        (d122df4:`.claude/portable/status.py:456-458`)。
        """
        root = _root_with_redlight(tmp_path)
        c = _chain_conftest(root, monkeypatch)
        _seed_red(["test_target"])
        _s_drive(c, root, {u"tests/test_w.py": [S_W], u"tests/test_x.py": [CHAIN_X, CHAIN_Y]},
                 selected=[CHAIN_X, CHAIN_Y, S_W],
                 outcomes={CHAIN_X: "passed", CHAIN_Y: "passed", S_W: "failed"},
                 option=_CompletenessOption(stepwise=True),
                 shouldstop=u"Test failed, continuing from this test next run.", exitstatus=2)
        got = _lines_of(root)
        assert u"tests/test_x.py" in got[u"red"], got
        assert u"tests/test_x.py" not in got[u"green"], got
        assert u"tests/test_x.py" not in got[u"orphaned"], got

    def test_c3c_pytest_exit_zero_partial_file_is_not_green(self, tmp_path, monkeypatch):
        """C3c-5(〈二十三〉2(b)、7 (vi))。分類:behavior-red。

        測試內 `pytest.exit(returncode=0)`:S_A passed;S_B 只有 setup report、沒有 call;
        S_C 沒有任何 report;exit 0;`shouldstop` / `shouldfail` 皆為 False ⇒ X 不得 green。
        d122df4 上失敗的原因:`.claude/hooks/redlight.py:423-426` 判 `"true"` ⇒
        `.claude/portable/status.py:475` `"passed" in results` ⇒ green。
        """
        root = _root_with_redlight(tmp_path)
        c = _chain_conftest(root, monkeypatch)
        _s_drive(c, root, {u"tests/test_x.py": [S_A, S_B, S_C]}, selected=[S_A, S_B, S_C],
                 outcomes={S_A: "passed", S_B: "setup_only"}, exitstatus=0)
        got = _lines_of(root)
        assert u"tests/test_x.py" not in got[u"green"], got

    def test_setup_only_run_is_not_green(self, tmp_path, monkeypatch):
        """C3x-1(規劃檔 P2(a))。分類:regression-lock。

        `--setup-only`:每個身分只有 setup / teardown passed、沒有 call;exit 0 ⇒ 不 green
        (d122df4:`tests/conftest.py:198-199` 只從 call 取 passed)。
        """
        root = _root_with_redlight(tmp_path)
        c = _chain_conftest(root, monkeypatch)
        _s_drive(c, root, {u"tests/test_x.py": [S_A, S_B]}, selected=[S_A, S_B],
                 outcomes={S_A: "setup_teardown", S_B: "setup_teardown"},
                 option=_CompletenessOption(setuponly=True), exitstatus=0)
        got = _lines_of(root)
        assert u"tests/test_x.py" not in got[u"green"], got


class TestLfFalseGreenChain:

    def test_c3e_full_then_lf_does_not_produce_a_false_green(self, tmp_path, monkeypatch):
        """C3e-1(〈二十一〉21.2 三步情境)。分類:behavior-red。

        R1:test_x.py 收集錯誤(exit 2)⇒ 整檔紅。R2:全套,S_A passed、S_B failed(exit 1)⇒
        red = {整檔, S_B}。R3:`--lf`,縮小前全集 [S_A, S_B],S_A 被悄悄移除,S_B passed(exit 0)
        ⇒ 仍紅、不 green。
        每次執行各自載入新的 conftest,模擬獨立的 pytest 程序(3c-1b 修正)。
        情境斷言:R1 的 session 判 D、R2 判 B、R3 判 A 且 schema 合格。
        d122df4 上失敗的原因:R3 在 `.claude/hooks/redlight.py:423-426` 判 `"true"` ⇒
        `.claude/portable/status.py:470-474` 退掉整檔紅與 S_B ⇒ `:475` green。
        """
        root = _root_with_redlight(tmp_path)
        c1 = _chain_conftest(root, monkeypatch)
        _s_drive(c1, root, {}, selected=[], collect_errors=[u"tests/test_x.py"], exitstatus=2)
        c2 = _chain_conftest(root, monkeypatch)
        _s_drive(c2, root, {u"tests/test_x.py": [S_A, S_B]}, selected=[S_A, S_B],
                 outcomes={S_A: "passed", S_B: "failed"}, exitstatus=1)
        c3 = _chain_conftest(root, monkeypatch)
        _s_drive_lf(c3, root)
        runs = redlight.load_runs(root)
        assert len(runs) == 3, runs
        assert redlight.run_state(runs[0]) == u"D", runs[0]
        assert redlight.run_state(runs[1]) == u"B", runs[1]
        assert redlight.validate_session(runs[2]) == [], runs[2]
        assert redlight.run_state(runs[2]) == u"A", runs[2]
        got = _lines_of(root)
        assert u"tests/test_x.py" in got[u"red"], got
        assert u"tests/test_x.py" not in got[u"green"], got


class TestCompletenessLocks:

    def test_c3d_the_fixed_command_full_run_still_retires_the_red(self, tmp_path, monkeypatch):
        """C3d-2(〈二十三〉7 全部條件成立)。分類:regression-lock。

        X 的已知紅 CHAIN_X;之後一次固定全套(選項全部關閉、plugin 全在白名單、縮小前全集 = 收集結果),
        CHAIN_X / CHAIN_Y passed,S_XF 為明確辨識的 xfail ⇒ X 退紅、在 green。
        """
        root = _root_with_redlight(tmp_path)
        c = _chain_conftest(root, monkeypatch)
        _seed_red(["test_target"])
        _t_committed(root)
        _t_drive(c, root, {u"tests/test_x.py": [CHAIN_X, CHAIN_Y, S_XF]},
                 [CHAIN_X, CHAIN_Y, S_XF],
                 {CHAIN_X: "passed", CHAIN_Y: "passed", S_XF: "xfail"}, exitstatus=0)
        got = _lines_of(root)
        assert u"tests/test_x.py" in got[u"green"], got
        assert u"tests/test_x.py" not in got[u"red"], got


def _s_full_run_session(c, root, pm):
    """test_x.py 全收集、全 passed、其餘完整性事實全部關閉;回傳讀回的最後一筆 session。"""
    _s_drive(c, root, {u"tests/test_x.py": [S_A, S_B]}, selected=[S_A, S_B],
             outcomes={S_A: "passed", S_B: "passed"}, pm=pm, exitstatus=0)
    runs = redlight.load_runs(root)
    assert runs, runs
    return runs[-1]


def _s_plugin_kinds(run):
    """持久化 session 的 `completeness.plugins` → {正規化名稱: kind}。缺欄即失敗(不推論)。"""
    comp = run.get("completeness")
    assert isinstance(comp, dict), u"session 沒有 completeness:%r" % (run,)
    plugins = comp.get("plugins")
    assert isinstance(plugins, list), u"completeness 沒有 plugins:%r" % (comp,)
    return dict((p.get("name"), p.get("kind")) for p in plugins)


class TestPluginProducerChain:

    def test_c3p_producer_classifies_an_unknown_dist_plugin_as_other(self, tmp_path, monkeypatch):
        """C3p-4(〈二十三〉3 (3)、7 plugins / (vii))。分類:behavior-red。

        多一個 plugin 物件(模組 `evilplug.plugin`),在 `list_plugin_distinfo()` 中配對到 dist `evil-dist`
        ⇒ 持久化的 plugins 有一項 kind == "other",且 `file_coverage != "true"`。
        d122df4 上失敗的原因:`tests/conftest.py:222-246` 不記 completeness ⇒ session 沒有 `completeness`。
        """
        root = _root_with_redlight(tmp_path)
        c = _chain_conftest(root, monkeypatch)
        evil = _s_types.ModuleType("evilplug.plugin")
        pm = _s_plugins(c, root, extra=[(u"evilplug", evil)], extra_dist=[(evil, _SDist("evil-dist"))])
        run = _s_full_run_session(c, root, pm)
        kinds = _s_plugin_kinds(run)
        assert kinds.get(u"evilplug") == u"other", kinds
        got = redlight.file_coverage(run, u"tests/test_x.py")
        assert got != u"true", got

    def test_c3p_producer_classifies_a_plugin_loaded_by_name_as_other(self, tmp_path, monkeypatch):
        """C3p-5(〈二十三〉3、7 plugins / (vii))。分類:behavior-red。

        多一個以名稱 `myplug` 註冊的模組 `myplug`(模擬 `-p myplug`),不在 `list_plugin_distinfo()`
        ⇒ kind == "other",且 `file_coverage != "true"`。
        d122df4 上失敗的原因:同 C3p-4。
        """
        root = _root_with_redlight(tmp_path)
        c = _chain_conftest(root, monkeypatch)
        pm = _s_plugins(c, root, extra=[(u"myplug", _s_types.ModuleType("myplug"))])
        run = _s_full_run_session(c, root, pm)
        kinds = _s_plugin_kinds(run)
        assert kinds.get(u"myplug") == u"other", kinds
        got = redlight.file_coverage(run, u"tests/test_x.py")
        assert got != u"true", got

    def test_c3p_producer_classifies_an_extra_conftest_as_other_and_the_root_conftest_as_root_conftest(
            self, tmp_path, monkeypatch):
        """C3p-6(〈二十三〉3 (2)、7 plugins / (vii))。分類:behavior-red。

        除 `<root>/tests/conftest.py` 外,多一個名稱為 `<root>/tests/sub/conftest.py` 絕對路徑的 conftest
        ⇒ 前者 kind == "root_conftest"、後者 kind == "other"(名稱記 root 相對路徑),`file_coverage != "true"`;
        持久化的 session 那一行文字不得包含 tmp root 的絕對路徑。
        d122df4 上失敗的原因:同 C3p-4。
        """
        root = _root_with_redlight(tmp_path)
        c = _chain_conftest(root, monkeypatch)
        sub = os.path.join(str(root), u"tests", u"sub", u"conftest.py")
        pm = _s_plugins(c, root, extra=[(sub, _s_types.ModuleType("conftest"))])
        run = _s_full_run_session(c, root, pm)
        kinds = _s_plugin_kinds(run)
        assert kinds.get(u"tests/sub/conftest.py") == u"other", kinds
        assert kinds.get(u"tests/conftest.py") == u"root_conftest", kinds
        got = redlight.file_coverage(run, u"tests/test_x.py")
        assert got != u"true", got
        with io.open(redlight.session_log(root), encoding="utf-8") as f:
            text = f.read()
        for form in set([str(root), str(root).replace(u"\\", u"/"), json.dumps(str(root))[1:-1]]):
            assert form not in text, u"帳本出現絕對路徑:%s" % form

    def test_c3p_producer_classifies_builtin_root_conftest_and_known_dist_as_not_other(
            self, tmp_path, monkeypatch):
        """C3p-7(〈二十三〉3 (1)(2)(3)、7 全部條件)。分類:behavior-red。

        只有 `_pytest` 內建物件(含一個數字名稱、類別定義在 `_pytest.config` 的物件)、root `tests/conftest.py`、
        以及在 `list_plugin_distinfo()` 中配對到 dist `anyio` 的 `anyio.pytest_plugin`
        ⇒ 每一項 kind 都不是 "other",且 `file_coverage == "true"`。
        d122df4 上失敗的原因:同 C3p-4(session 沒有 `completeness`)。
        """
        root = _root_with_redlight(tmp_path)
        c = _chain_conftest(root, monkeypatch)
        _t_committed(root)
        _t_drive(c, root, {u"tests/test_x.py": [S_A, S_B]}, [S_A, S_B],
                 {S_A: "passed", S_B: "passed"}, exitstatus=0)
        run = redlight.load_runs(root)[-1]
        kinds = _s_plugin_kinds(run)
        assert kinds, kinds
        assert all(k != u"other" for k in kinds.values()), kinds
        got = redlight.file_coverage(run, u"tests/test_x.py")
        assert got == u"true", got


# ═══════════════════════════════════════════════════════════════════════════
# 票 145 Station 3d 紅燈 —— 收集定義完整性的串接(producer → 持久化 run 事實 → status)
#
# 合約:票 145〈二十九〉2、5。規劃:docs/audits/2026-10-02-m1a-station3d-redlight-plan.md P4。
# 下文 `<TARGET>` = 02a5e28adf5aee11a43d5a1063504f01beb1d67f(與 9d1446a 之間程式碼相同)。
#
# 每一次模擬執行都經**真實 tests/conftest.py**(`_chain_conftest` 每次載入全新模組,沿用 3c-1b)寫入
# tmp root 的帳本,再由 status 讀回判定。tmp root 是**真的 git repo**,已提交 `pyproject.toml` 與
# `tests/conftest.py`(真檔內容)。pytest 層級的假物件與 tests/test_redlight.py 的 3d 段同形:
# `override_ini` 為解析後清單(固定全套 = `["strict_markers=true"]`)、`invocation_params.args` 只有 argv、
# `inipath` / `getini()` 一致、`list_name_plugin()` 照 pluggy 表示方式、dist 帶名稱與版本。
# `-o python_functions=test_b` 的情境:test_a 從一開始就不在 collect report 裡。
# 本段 helper 全部新寫;既有 helper(`_root_with_redlight` / `_chain_conftest` / `_seed_red` / `_lines_of` /
# `_CompletenessOption` / `_CompletenessSession` / `_SCollectReport` / `_s_item` / `_s_file` /
# `_s_call_collect_wrapper` / `_s_reports` / `_s_internal`)只呼叫、不修改。
# ═══════════════════════════════════════════════════════════════════════════

_T_COMMITTED_PYPROJECT = (
    u'[tool.pytest.ini_options]\n'
    u'testpaths = ["tests"]\n'
    u'addopts = "-ra --strict-markers"\n')

_T_BASELINE_INI = {
    "testpaths": ["tests"],
    "addopts": ["-ra", "--strict-markers"],
    "python_files": ["test_*.py", "*_test.py"],
    "python_classes": ["Test"],
    "python_functions": ["test"],
    "norecursedirs": ["*.egg", ".*", "_darcs", "build", "CVS", "dist", "node_modules", "venv", "{arch}"],
    "collect_imported_tests": True,
}

_T_FIXED_OVERRIDES = [u"strict_markers=true"]

# 票 145 Station 4g 授權 G1(規劃檔 S3g-0 P6「需要的授權」1):與 baseline 相符的已提交 evidence policy ——
# 已提交 addopts `-ra --strict-markers` ⇒ `strict_markers=true`;版本與 dist 等於 driver 固定的事實(授權 3)。
_T_POLICY_FILE = u".agents/evidence-policy.json"
_T_BASELINE_POLICY = {
    u"schema": u"monkeyleash.evidence-policy",
    u"version": 1,
    u"config_file": u"pyproject.toml",
    u"committed_overrides": list(_T_FIXED_OVERRIDES),
    u"python_versions": [u"3.11"],
    u"pytest_versions": [u"9.1.1"],
    u"dists": [[u"anyio", u"4.15.0"]],
}
_T_BASELINE_ADDOPTS = u"-ra --strict-markers"


def _t_git(root, *args):
    return subprocess.run(["git"] + list(args), cwd=str(root), capture_output=True, check=True)


def _t_committed(root):
    """把 `root` 變成真的 git repo,提交 baseline `pyproject.toml` 與 root conftest(真檔內容)。"""
    with io.open(str(pathlib.Path(root) / "pyproject.toml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(_T_COMMITTED_PYPROJECT)
    conftest = pathlib.Path(root) / "tests" / "conftest.py"
    conftest.parent.mkdir(parents=True, exist_ok=True)
    conftest.write_bytes((ROOT / "tests" / "conftest.py").read_bytes())
    policy = pathlib.Path(root) / ".agents" / "evidence-policy.json"
    policy.parent.mkdir(parents=True, exist_ok=True)
    with io.open(str(policy), "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(_T_BASELINE_POLICY, ensure_ascii=False, indent=2) + u"\n")
    _t_git(root, "init", "-q")
    _t_git(root, "config", "user.email", "t@example.invalid")
    _t_git(root, "config", "user.name", "t")
    _t_git(root, "add", "pyproject.toml", "tests/conftest.py", _T_POLICY_FILE)
    _t_git(root, "commit", "-q", "-m", "baseline")
    return root


def _t_policy_facts(root):
    """`_t_committed(root)` 之後的 `completeness["evidence_policy"]` 事實(7 鍵;授權 G2 用):
    blob 由 git 實際取得,內容 = 已提交的 baseline policy,`committed_addopts` = 已提交的 addopts 原值。"""
    head = _t_git(root, "rev-parse", "HEAD:" + _T_POLICY_FILE).stdout.decode().strip()
    worktree = _t_git(root, "hash-object", _T_POLICY_FILE).stdout.decode().strip()
    return {u"path": _T_POLICY_FILE, u"head": head, u"worktree": worktree,
            u"schema": _T_BASELINE_POLICY[u"schema"], u"version": _T_BASELINE_POLICY[u"version"],
            u"policy": dict(_T_BASELINE_POLICY), u"committed_addopts": _T_BASELINE_ADDOPTS}


class _TDist:
    def __init__(self, name, version):
        self.project_name = name
        self.version = version
        self.metadata = {"name": name, "version": version}


class _TPluginManager:
    """`list_name_plugin()` 照 pluggy 實際表示方式(可含 `(name, None)`);`is_blocked()` 由同一份資料推出。"""

    def __init__(self, name_plugins, distinfo=()):
        self._name_plugins = list(name_plugins)
        self._distinfo = list(distinfo)

    def list_name_plugin(self):
        return list(self._name_plugins)

    def list_plugin_distinfo(self):
        return list(self._distinfo)

    def is_blocked(self, name):
        return any(n == name and p is None for n, p in self._name_plugins)

    def get_plugin(self, name):
        return dict(self._name_plugins).get(name)

    def has_plugin(self, name):
        return self.get_plugin(name) is not None


def _t_plugins(c, root, anyio_version="4.15.0"):
    builtin_mod = _s_types.ModuleType("_pytest.main")
    internal = _s_internal("_pytest.config", "_InternalHelper")
    anyio_mod = _s_types.ModuleType("anyio.pytest_plugin")
    names = [(u"main", builtin_mod),
             (str(id(internal)), internal),
             (os.path.join(str(root), u"tests", u"conftest.py"), c),
             (u"anyio", anyio_mod)]
    return _TPluginManager(names, [(anyio_mod, _TDist("anyio", anyio_version))])


class _TInvocationParams:
    def __init__(self, args, d):
        self.args = tuple(args)
        self.plugins = None
        self.dir = d


class _TConfig:
    def __init__(self, root, option, pluginmanager, argv=(u"-q",), inipath=u"pyproject.toml", ini=None):
        self.args = [u"tests"]
        self.args_source = pytest.Config.ArgsSource.TESTPATHS
        self.rootpath = pathlib.Path(str(root))
        self.invocation_params = _TInvocationParams(argv, self.rootpath)
        self.option = option
        self.pluginmanager = pluginmanager
        self.inipath = self.rootpath / inipath
        self._ini = dict(_T_BASELINE_INI)
        self._ini.update(ini or {})

    def getini(self, name):
        if name not in self._ini:
            raise ValueError("unknown configuration value: %r" % (name,))
        value = self._ini[name]
        return list(value) if isinstance(value, list) else value

    def getoption(self, name, default=None, skip=False):
        return getattr(self.option, name, default)


def _t_option(**overrides):
    values = {"override_ini": list(_T_FIXED_OVERRIDES), "inifilename": None}
    values.update(overrides)
    return _CompletenessOption(**values)


def _t_drive(c, root, files, selected, outcomes, collect_errors=(), exitstatus=0,
             option=None, argv=(u"-q",), ini=None):
    """依 pytest 9.1.1 的呼叫順序驅動真實 conftest(同 `_s_drive`),session 帶 `_TConfig`。
    `files` 的清單就是 collect report 的內容 —— 在 `collect()` 之內被縮掉的身分不在裡面。"""
    def hook(name):
        return getattr(c, name, None) or (lambda *a, **k: None)

    for path in sorted(files):
        report = _SCollectReport(path, [_s_item(n) for n in files[path]])
        _s_call_collect_wrapper(c, _s_file(root, path), report)
        hook("pytest_collectreport")(report)
    for path in collect_errors:
        hook("pytest_collectreport")(_SCollectReport(path, [], failed=True))
    config = _TConfig(root, option if option is not None else _t_option(), _t_plugins(c, root),
                      argv=argv, ini=ini)
    session = _CompletenessSession([_s_item(n) for n in selected], config)
    hook("pytest_collection_finish")(session)
    for nodeid, kind in outcomes.items():
        for rep in _s_reports(nodeid, kind):
            hook("pytest_runtest_logreport")(rep)
    hook("pytest_sessionfinish")(session, exitstatus)


def _t_drive_override(c, root):
    """`python -X utf8 -m pytest -q -o python_functions=test_b`:test_a 在 `collect()` 之內就不被收集;
    只跑 S_B、passed、exit 0;其餘事實同固定全套。"""
    _t_drive(c, root, {u"tests/test_x.py": [S_B]}, [S_B], {S_B: "passed"},
             option=_t_option(override_ini=_T_FIXED_OVERRIDES + [u"python_functions=test_b"]),
             argv=(u"-q", u"-o", u"python_functions=test_b"),
             ini={"python_functions": [u"test_b"]}, exitstatus=0)


class TestOverrideIniChain:

    def test_d3a_full_then_override_ini_does_not_produce_a_false_green(self, tmp_path, monkeypatch):
        """D3a-2(S5c-F1 三步情境;〈二十七〉27.2;〈二十九〉2 (viii))。分類:behavior-red。

        R1:test_x.py 收集錯誤(exit 2)⇒ 整檔紅。R2:全套,S_A passed、S_B failed(exit 1)。
        R3:`-o python_functions=test_b`,test_a 從一開始就不在 collect report 裡,S_B passed(exit 0)
        ⇒ 仍紅、不 green。每次執行各自載入新的 conftest。
        情境斷言:R1 的 session 判 D、R2 判 B、R3 schema 合格且判 A。
        9d1446a 上失敗的原因:R3 在 `<TARGET>:.claude/hooks/redlight.py:590-592, 597` 判 `"true"` ⇒
        `<TARGET>:.claude/portable/status.py:470-474` 退掉整檔紅與 S_B ⇒ `:475` green。
        """
        root = _root_with_redlight(tmp_path)
        _t_committed(root)
        c1 = _chain_conftest(root, monkeypatch)
        _t_drive(c1, root, {}, [], {}, collect_errors=[u"tests/test_x.py"], exitstatus=2)
        c2 = _chain_conftest(root, monkeypatch)
        _t_drive(c2, root, {u"tests/test_x.py": [S_A, S_B]}, [S_A, S_B],
                 {S_A: "passed", S_B: "failed"}, exitstatus=1)
        c3 = _chain_conftest(root, monkeypatch)
        _t_drive_override(c3, root)
        runs = redlight.load_runs(root)
        assert len(runs) == 3, runs
        assert redlight.run_state(runs[0]) == u"D", runs[0]
        assert redlight.run_state(runs[1]) == u"B", runs[1]
        assert redlight.validate_session(runs[2]) == [], runs[2]
        assert redlight.run_state(runs[2]) == u"A", runs[2]
        got = _lines_of(root)
        assert u"tests/test_x.py" in got[u"red"], got
        assert u"tests/test_x.py" not in got[u"green"], got

    def test_d3a_override_ini_does_not_orphan_a_known_red(self, tmp_path, monkeypatch):
        """D3a-3(〈二十九〉2 (viii);ODC-2 的 orphan 判定權)。分類:behavior-red。

        已知紅 test_a;之後一次 `-o python_functions=test_b` 只收集到 S_B 且 passed
        ⇒ test_a 不得被移到 orphan,仍紅。
        9d1446a 上失敗的原因:`<TARGET>:.claude/hooks/redlight.py:597` 判 `"true"` ⇒
        `<TARGET>:.claude/portable/status.py:464-468` 把 test_a 移入 orphan。
        """
        root = _root_with_redlight(tmp_path)
        _t_committed(root)
        c = _chain_conftest(root, monkeypatch)
        _seed_red(["test_a"])
        _t_drive_override(c, root)
        got = _lines_of(root)
        assert u"tests/test_x.py" not in got[u"orphaned"], got
        assert u"tests/test_x.py" in got[u"red"], got

    def test_d3a_override_ini_does_not_make_a_clean_file_green(self, tmp_path, monkeypatch):
        """D3a-4(〈二十一〉21.2 附註 2 的同型;〈二十九〉2 (viii))。分類:behavior-red。

        test_x.py 先前沒有紅;一次 `-o python_functions=test_b` 只跑了 S_B ⇒ 不得 green。
        9d1446a 上失敗的原因:`<TARGET>:.claude/hooks/redlight.py:597` 判 `"true"` ⇒
        `<TARGET>:.claude/portable/status.py:475` `green_now = True`。
        """
        root = _root_with_redlight(tmp_path)
        _t_committed(root)
        c = _chain_conftest(root, monkeypatch)
        _t_drive_override(c, root)
        got = _lines_of(root)
        assert u"tests/test_x.py" not in got[u"green"], got


class TestCollectionDefinitionLocks:

    def test_d3d_the_fixed_command_full_run_still_retires_the_red(self, tmp_path, monkeypatch):
        """D3d-2(〈二十九〉2 全部條件成立)。分類:regression-lock。

        X 的已知紅 CHAIN_X;之後一次固定全套(`override_ini == ["strict_markers=true"]`、沒有 `-c`、
        `inipath` 為 `pyproject.toml`、設定檔與 conftest = 已提交 blob、沒有 `(name, None)`、
        pytest 9.1.1、anyio 4.15.0;全收集、全 passed)⇒ X 退紅、在 green。
        """
        root = _root_with_redlight(tmp_path)
        _t_committed(root)
        c = _chain_conftest(root, monkeypatch)
        _seed_red(["test_target"])
        _t_drive(c, root, {u"tests/test_x.py": [CHAIN_X, CHAIN_Y]}, [CHAIN_X, CHAIN_Y],
                 {CHAIN_X: "passed", CHAIN_Y: "passed"}, exitstatus=0)
        got = _lines_of(root)
        assert u"tests/test_x.py" in got[u"green"], got
        assert u"tests/test_x.py" not in got[u"red"], got


# ═══════════════════════════════════════════════════════════════════════════
# 票 145 Station 3e 紅燈 —— pass 有效性的串接(producer → 持久化 run 事實 → status;〈三十五〉)
#
# 合約:票 145〈三十五〉3 (xiv)–(xvii)。規劃:docs/audits/2026-10-03-m1a-station3e-redlight-plan.md P4。
# 下文 `<TARGET>` = 889fbd8f666ea522ff6af172979a8d020e50b86b(與 2258490 之間程式碼相同)。
#
# 每一次模擬執行都經**真實 tests/conftest.py**(`_chain_conftest` 每次載入全新模組,沿用 3c-1b)寫入
# tmp root 的帳本,再由 status 讀回判定;tmp root 是真的 git repo(`_t_committed`)。
# 直譯器事實以 `monkeypatch.setattr(c, "sys", _e_sys(...), raising=False)` 注入**該 conftest 所見的** `sys`,
# 不改全域 `sys.flags`(與 tests/test_redlight.py 的 3e 段同一介面細節)。
# `runxfail` / `pythonwarnings` / `trace` 以 `_e_option(...)` 明確帶入真實 pytest 的預設值。
# 本段 helper 全部新寫;既有 helper(`_root_with_redlight` / `_chain_conftest` / `_seed_red` / `_lines_of` /
# `_t_committed` / `_t_option` / `_t_drive`)只呼叫、不修改。
# ═══════════════════════════════════════════════════════════════════════════

import collections as _e_collections

_E_FLAG_FIELDS = tuple(
    n for n in dir(sys.flags)
    if not n.startswith(("_", "n_")) and not callable(getattr(sys.flags, n)))

_EVersion = _e_collections.namedtuple("_EVersion", "major minor micro releaselevel serial")


class _ESys(object):
    """conftest 所見的 `sys` 替身:`flags` / `version_info` 由測試指定,其他屬性一律轉給真的 `sys`。"""

    def __init__(self, flags, version_info):
        self.flags = flags
        self.version_info = version_info

    def __getattr__(self, name):
        return getattr(sys, name)


def _e_sys(optimize=0, drop=(), version_info=None):
    """複製真實 `sys.flags` 的全部公開欄位,只把 `optimize` 換成指定值;`drop` 中的欄位不存在。"""
    values = dict((n, getattr(sys.flags, n)) for n in _E_FLAG_FIELDS)
    values["optimize"] = optimize
    for k in drop:
        values.pop(k, None)
    vi = version_info if version_info is not None else _EVersion(*tuple(sys.version_info))
    return _ESys(_s_types.SimpleNamespace(**values), vi)


def _e_option(**overrides):
    """固定全套的 `config.option`(`_t_option`)+ 三個 pass 有效性選項的真實預設值。"""
    values = {"runxfail": False, "pythonwarnings": None, "trace": False}
    values.update(overrides)
    return _t_option(**values)


def _e_drive(root, monkeypatch, outcomes, exitstatus, sys_=None, option=None):
    """一次模擬執行:全新 conftest;tests/test_x.py 的 S_A / S_B 全收集;其他事實同固定全套。
    `sys_` 為 None ⇒ 不注入(producer 看到真的 `sys`)。"""
    c = _chain_conftest(root, monkeypatch)
    if sys_ is not None:
        monkeypatch.setattr(c, "sys", sys_, raising=False)
    _t_drive(c, root, {u"tests/test_x.py": [S_A, S_B]}, [S_A, S_B], outcomes,
             exitstatus=exitstatus, option=option if option is not None else _e_option())


def _e_red_then(root, monkeypatch, sys_=None, option=None):
    """R1 固定全套:S_A failed、S_B passed(exit 1)⇒ S_A 為已知紅;R2 依 `sys_` / `option`:S_A、S_B 皆 passed(exit 0)。
    回傳兩筆 run 事實(各自用全新 conftest)。"""
    _e_drive(root, monkeypatch, {S_A: "failed", S_B: "passed"}, 1, sys_=_e_sys(optimize=0))
    _e_drive(root, monkeypatch, {S_A: "passed", S_B: "passed"}, 0, sys_=sys_, option=option)
    runs = redlight.load_runs(root)
    assert len(runs) == 2, runs
    return runs


class TestPassValidityChain:

    def test_e3o_optimized_pass_does_not_retire_a_known_red(self, tmp_path, monkeypatch):
        """E3o-4(S5d-F1 / S5d-X1 串接;〈三十五〉3 (xiv))。分類:behavior-red。

        R1 固定全套:test_a failed(exit 1)⇒ 已知紅。R2:conftest 所見的 `sys.flags.optimize = 1`,
        test_a passed(exit 0)⇒ 不得退紅、不得 green。情境斷言:R1 為 B;R2 schema 合格且為 A。
        TARGET 上失敗的原因:R2 在 `<TARGET>:.claude/hooks/redlight.py:733` 判 `"true"` ⇒
        `<TARGET>:.claude/portable/status.py:474` 退掉 test_a ⇒ `:475` green。
        """
        root = _root_with_redlight(tmp_path)
        _t_committed(root)
        runs = _e_red_then(root, monkeypatch, sys_=_e_sys(optimize=1))
        assert redlight.run_state(runs[0]) == u"B", runs[0]
        assert redlight.validate_session(runs[1]) == [], runs[1]
        assert redlight.run_state(runs[1]) == u"A", runs[1]
        got = _lines_of(root)
        assert u"tests/test_x.py" in got[u"red"], got
        assert u"tests/test_x.py" not in got[u"green"], got

    def test_e3o_optimized_run_does_not_make_a_clean_file_green(self, tmp_path, monkeypatch):
        """E3o-5(〈三十五〉3 (xiv))。分類:behavior-red。

        test_x.py 先前沒有紅;一次 `optimize = 1` 的全 passed run(exit 0)⇒ 不得 green。
        TARGET 上失敗的原因:`<TARGET>:.claude/hooks/redlight.py:733` 判 `"true"` ⇒
        `<TARGET>:.claude/portable/status.py:475` `green_now = True`。
        """
        root = _root_with_redlight(tmp_path)
        _t_committed(root)
        _e_drive(root, monkeypatch, {S_A: "passed", S_B: "passed"}, 0, sys_=_e_sys(optimize=1))
        runs = redlight.load_runs(root)
        assert len(runs) == 1 and redlight.validate_session(runs[0]) == [], runs
        got = _lines_of(root)
        assert u"tests/test_x.py" not in got[u"green"], got

    def test_e3x_runxfail_pass_does_not_retire_a_known_red(self, tmp_path, monkeypatch):
        """E3x-3(〈三十五〉3 (xv);〈三十五〉1 (a))。分類:behavior-red。

        同 E3o-4,R2 改為 `--runxfail`(`optimize` 為真實值)⇒ 不得退紅、不得 green。
        TARGET 上失敗的原因:同 E3o-4(`<TARGET>:.claude/hooks/redlight.py:733`;
        `<TARGET>:.claude/portable/status.py:474-475`)。
        """
        root = _root_with_redlight(tmp_path)
        _t_committed(root)
        runs = _e_red_then(root, monkeypatch, option=_e_option(runxfail=True))
        assert redlight.run_state(runs[0]) == u"B", runs[0]
        assert redlight.validate_session(runs[1]) == [], runs[1]
        got = _lines_of(root)
        assert u"tests/test_x.py" in got[u"red"], got
        assert u"tests/test_x.py" not in got[u"green"], got

    def test_e3w_warning_filter_pass_does_not_retire_a_known_red(self, tmp_path, monkeypatch):
        """E3w-2(〈三十五〉3 (xvi);〈三十五〉1 (b))。分類:behavior-red。

        同 E3o-4,R2 改為 pytest 的 `-W ignore::UserWarning` ⇒ 不得退紅、不得 green。
        TARGET 上失敗的原因:同 E3o-4(`<TARGET>:.claude/hooks/redlight.py:733`;
        `<TARGET>:.claude/portable/status.py:474-475`)。
        """
        root = _root_with_redlight(tmp_path)
        _t_committed(root)
        runs = _e_red_then(root, monkeypatch, option=_e_option(pythonwarnings=["ignore::UserWarning"]))
        assert redlight.run_state(runs[0]) == u"B", runs[0]
        assert redlight.validate_session(runs[1]) == [], runs[1]
        got = _lines_of(root)
        assert u"tests/test_x.py" in got[u"red"], got
        assert u"tests/test_x.py" not in got[u"green"], got


class TestPassValidityLocks:

    def test_e3d_the_fixed_command_full_run_still_retires_the_red(self, tmp_path, monkeypatch):
        """E3d-2(〈三十五〉3 全部條件成立)。分類:regression-lock。

        X 的已知紅 CHAIN_X;之後一次固定全套(`optimize=0` 明確注入、真實 Python 版本、`runxfail=False`、
        `pythonwarnings=None`、`trace=False`,其他事實同 4d 的 D3d-2;全收集、全 passed)⇒ X 退紅、在 green。
        """
        root = _root_with_redlight(tmp_path)
        _t_committed(root)
        c = _chain_conftest(root, monkeypatch)
        monkeypatch.setattr(c, "sys", _e_sys(optimize=0), raising=False)
        _seed_red(["test_target"])
        _t_drive(c, root, {u"tests/test_x.py": [CHAIN_X, CHAIN_Y]}, [CHAIN_X, CHAIN_Y],
                 {CHAIN_X: "passed", CHAIN_Y: "passed"}, exitstatus=0, option=_e_option())
        got = _lines_of(root)
        assert u"tests/test_x.py" in got[u"green"], got
        assert u"tests/test_x.py" not in got[u"red"], got


# ═══════════════════════════════════════════════════════════════════════════
# 票 145 Station 3f 紅燈 —— `--pdb`(xix)與 S5e-F2 的串接(producer → 持久化 run 事實 → status)
#
# 合約:票 145〈三十九〉39.3、〈四十一〉41.1。規劃:docs/audits/2026-10-03-m1a-station3f-redlight-plan.md P7。
# 下文 `<TARGET>` = 0139a7e803fc2d41eb354f1196a6206cfe304701。
#
# 每一次模擬執行都經**真實 tests/conftest.py**(`_chain_conftest` 每次載入全新模組)寫入 tmp root 的帳本,
# 再由 status 讀回判定;tmp root 是真的 git repo(`_t_committed`)。
# S2 的 R2 option 是本次 session 的 pytest parser(`pytestconfig._parser.parse_known_args(...)`)解析出的
# namespace(防錯欄位;〈四十一〉41.1 第 2 點)。
# 本段 helper 全部新寫;既有 helper(`_root_with_redlight` / `_chain_conftest` / `_seed_red` / `_lines_of` /
# `_t_committed` / `_t_plugins` / `_TConfig` / `_TInvocationParams` / `_e_red_then` / `_e_option` / `_e_sys`)只呼叫、不修改。
# ═══════════════════════════════════════════════════════════════════════════


def _f_drive_from_parent(c, root, files, selected, outcomes, option, exitstatus=0):
    """從 root 的上一層執行 `python -X utf8 -m pytest -q <root 目錄名>`(同 `_t_drive`,只改
    `config.args`、`args_source`、`invocation_params.dir`;rootdir / inipath 不變)。"""
    def hook(name):
        return getattr(c, name, None) or (lambda *a, **k: None)

    base = pathlib.Path(str(root))
    for path in sorted(files):
        report = _SCollectReport(path, [_s_item(n) for n in files[path]])
        _s_call_collect_wrapper(c, _s_file(root, path), report)
        hook("pytest_collectreport")(report)
    config = _TConfig(root, option, _t_plugins(c, root))
    config.args = [base.name]
    config.args_source = pytest.Config.ArgsSource.ARGS
    config.invocation_params = _TInvocationParams((u"-q", base.name), base.parent)
    session = _CompletenessSession([_s_item(n) for n in selected], config)
    hook("pytest_collection_finish")(session)
    for nodeid, kind in outcomes.items():
        for rep in _s_reports(nodeid, kind):
            hook("pytest_runtest_logreport")(rep)
    hook("pytest_sessionfinish")(session, exitstatus)


class TestDebuggerModeChain:

    def test_f3p_pdb_pass_does_not_retire_a_known_red(self, tmp_path, monkeypatch):
        """S1(S5e-F1 串接;〈三十九〉39.3 第 3 點 (xix))。分類:behavior-red。

        R1 固定全套:test_a failed(exit 1)⇒ 已知紅。R2:`--pdb`(`usepdb=True`),test_a passed(exit 0)
        ⇒ 不得退紅、不得 green。情境斷言:R1 為 B;R2 schema 合格且為 A。
        TARGET 上失敗的原因:R2 在 `<TARGET>:.claude/hooks/redlight.py:820` 判 `"true"` ⇒
        `<TARGET>:.claude/portable/status.py:474` 退掉 test_a ⇒ `:475` green。
        """
        root = _root_with_redlight(tmp_path)
        _t_committed(root)
        runs = _e_red_then(root, monkeypatch, option=_e_option(usepdb=True))
        assert redlight.run_state(runs[0]) == u"B", runs[0]
        assert redlight.validate_session(runs[1]) == [], runs[1]
        assert redlight.run_state(runs[1]) == u"A", runs[1]
        got = _lines_of(root)
        assert u"tests/test_x.py" in got[u"red"], got
        assert u"tests/test_x.py" not in got[u"green"], got

    def test_f3p_pdb_parsed_by_pytest_does_not_retire_a_known_red(self, tmp_path, monkeypatch, pytestconfig):
        """S2(防錯欄位的串接版;〈四十一〉41.1 第 2 點)。分類:behavior-red。

        同 S1,但 R2 的 option 由本次 session 的 pytest parser 解析 `["--strict-markers", "--pdb"]` 取得
        ⇒ 不得退紅、不得 green。情境斷言:namespace 的 `usepdb is True`;R1 為 B;R2 schema 合格且為 A。
        TARGET 上失敗的原因:同 S1(`<TARGET>:.claude/hooks/redlight.py:820`;`<TARGET>:.claude/portable/status.py:474-475`)。
        """
        option = pytestconfig._parser.parse_known_args([u"--strict-markers", u"--pdb"])
        assert option.usepdb is True, option
        root = _root_with_redlight(tmp_path)
        _t_committed(root)
        runs = _e_red_then(root, monkeypatch, option=option)
        assert redlight.run_state(runs[0]) == u"B", runs[0]
        assert redlight.validate_session(runs[1]) == [], runs[1]
        assert redlight.run_state(runs[1]) == u"A", runs[1]
        got = _lines_of(root)
        assert u"tests/test_x.py" in got[u"red"], got
        assert u"tests/test_x.py" not in got[u"green"], got


class TestOverrideBaseChain:

    def test_f3o_the_fixed_command_from_the_parent_dir_retires_the_red(self, tmp_path, monkeypatch):
        """S3(S5e-F2 串接;〈四十一〉41.1 第 3 點)。分類:behavior-red。

        X 的已知紅 CHAIN_X;之後從 root 的上一層執行一次固定全套(`pytest -q <root 目錄名>`;全收集、全 passed;
        `usepdb=False`,其他事實同固定全套)⇒ X 退紅、在 green。
        情境斷言:session 合格且為 A;`invocation.args == ["."]`;`override_ini` 未被改寫。
        TARGET 上失敗的原因:`<TARGET>:.claude/hooks/redlight.py:655-656` 以 invocation dir 判越界 ⇒
        `strict_markers=<outside>` ⇒ `:784` unknown ⇒ `<TARGET>:.claude/portable/status.py:456-458` 不退紅。
        """
        root = _root_with_redlight(tmp_path)
        _t_committed(root)
        c = _chain_conftest(root, monkeypatch)
        _seed_red(["test_target"])
        _f_drive_from_parent(c, root, {u"tests/test_x.py": [CHAIN_X, CHAIN_Y]}, [CHAIN_X, CHAIN_Y],
                             {CHAIN_X: "passed", CHAIN_Y: "passed"}, _e_option(usepdb=False))
        runs = redlight.load_runs(root)
        assert len(runs) == 1, runs
        assert redlight.run_state(runs[0]) == u"A", runs[0]
        assert runs[0]["invocation"]["args"] == [u"."], runs[0]["invocation"]
        assert runs[0]["completeness"]["override_ini"] == [u"strict_markers=true"], runs[0]["completeness"]
        got = _lines_of(root)
        assert u"tests/test_x.py" in got[u"green"], got
        assert u"tests/test_x.py" not in got[u"red"], got


class TestDebuggerModeLocks:

    def test_f3d_the_fixed_command_full_run_still_retires_the_red(self, tmp_path, monkeypatch):
        """S4((xix) 之下固定全套仍可退紅)。分類:regression-lock。

        X 的已知紅 CHAIN_X;之後一次固定全套(`usepdb=False`、`optimize=0` 明確注入,其他事實同 3e 的 E3d-2)
        ⇒ X 退紅、在 green。
        """
        root = _root_with_redlight(tmp_path)
        _t_committed(root)
        c = _chain_conftest(root, monkeypatch)
        monkeypatch.setattr(c, "sys", _e_sys(optimize=0), raising=False)
        _seed_red(["test_target"])
        _t_drive(c, root, {u"tests/test_x.py": [CHAIN_X, CHAIN_Y]}, [CHAIN_X, CHAIN_Y],
                 {CHAIN_X: "passed", CHAIN_Y: "passed"}, exitstatus=0, option=_e_option(usepdb=False))
        got = _lines_of(root)
        assert u"tests/test_x.py" in got[u"green"], got
        assert u"tests/test_x.py" not in got[u"red"], got


# ═══════════════════════════════════════════════════════════════════════════
# 票 145 Station 3g 紅燈 —— Host evidence policy 的串接(producer → 持久化 run 事實 → status)
#
# 合約:票 145〈四十八〉48.1。規劃:docs/audits/2026-10-03-m1a-station3g-redlight-plan.md P3、P6。
# 下文 `<BASELINE>` = 560f618560ddac1a34e0e835b99a1e3a5cc7eda5(S3G0)。
#
# 每一次模擬執行都經**真實 tests/conftest.py**(`_chain_conftest` 每次載入全新模組)寫入 tmp root 的帳本,
# 再由 status 讀回判定;tmp root 是真的 git repo,policy 檔**真的**提交 / 修改(canonical path
# `.agents/evidence-policy.json`;schema 與欄位同 tests/test_redlight.py 的 3g 段)。
# **版本事實一律固定**(〈四十八〉48.1 第 5 點):conftest 所見的 `sys.version_info` 為 3.11、`pytest.__version__` 為 9.1.1。
# 本段 helper 全部新寫;既有 helper(`_root_with_redlight` / `_chain_conftest` / `_lines_of` / `_t_option` /
# `_t_drive` / `_e_option` / `_e_sys` / `_EVersion`)只呼叫、不修改。
# ═══════════════════════════════════════════════════════════════════════════

_G_POLICY_FILE = u".agents/evidence-policy.json"


def _g_policy(**overrides):
    policy = {
        u"schema": u"monkeyleash.evidence-policy",
        u"version": 1,
        u"config_file": u"pyproject.toml",
        u"committed_overrides": [u"strict_markers=true"],
        u"python_versions": [u"3.11"],
        u"pytest_versions": [u"9.1.1"],
        u"dists": [[u"anyio", u"4.15.0"]],
    }
    policy.update(overrides)
    return policy


def _g_write(root, rel, text):
    p = pathlib.Path(str(root)) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    with io.open(str(p), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _g_committed(root, policy=None, commit_policy=True, addopts=u"-ra --strict-markers"):
    """把 `root` 變成真的 git repo:提交 `pyproject.toml`(addopts 由參數決定)與 root conftest(真檔內容);
    `policy` 不為 None ⇒ 寫到 canonical path,`commit_policy` 為真才一起提交。"""
    _g_write(root, u"pyproject.toml",
             u'[tool.pytest.ini_options]\ntestpaths = ["tests"]\naddopts = "%s"\n' % addopts)
    conftest = pathlib.Path(root) / "tests" / "conftest.py"
    conftest.parent.mkdir(parents=True, exist_ok=True)
    conftest.write_bytes((ROOT / "tests" / "conftest.py").read_bytes())
    tracked = [u"pyproject.toml", u"tests/conftest.py"]
    if policy is not None:
        _g_write(root, _G_POLICY_FILE, json.dumps(policy, ensure_ascii=False, indent=2) + u"\n")
        if commit_policy:
            tracked.append(_G_POLICY_FILE)
    _t_git(root, "init", "-q")
    _t_git(root, "config", "user.email", "t@example.invalid")
    _t_git(root, "config", "user.name", "t")
    _t_git(root, "add", *tracked)
    _t_git(root, "commit", "-q", "-m", "baseline")
    return root


def _g_drive(root, monkeypatch, outcomes, exitstatus, option=None):
    """一次模擬執行:全新 conftest;tests/test_x.py 的 S_A / S_B 全收集;版本事實固定為 3.11 / 9.1.1。"""
    c = _chain_conftest(root, monkeypatch)
    monkeypatch.setattr(c, "sys", _e_sys(optimize=0, version_info=_EVersion(3, 11, 0, "final", 0)), raising=False)
    monkeypatch.setattr(pytest, "__version__", "9.1.1")
    _t_drive(c, root, {u"tests/test_x.py": [S_A, S_B]}, [S_A, S_B], outcomes,
             exitstatus=exitstatus, option=option if option is not None else _e_option(usepdb=False))


def _g_red_then(root, monkeypatch, option=None):
    """R1 固定全套:S_A failed、S_B passed(exit 1)⇒ S_A 為已知紅;R2:S_A、S_B 皆 passed(exit 0,`option`)。
    回傳兩筆 run 事實(各自用全新 conftest)。"""
    _g_drive(root, monkeypatch, {S_A: "failed", S_B: "passed"}, 1)
    _g_drive(root, monkeypatch, {S_A: "passed", S_B: "passed"}, 0, option=option)
    runs = redlight.load_runs(root)
    assert len(runs) == 2, runs
    return runs


def _g_assert_scenario(runs):
    """情境斷言:R1 為 B;R2 schema 合格且為 A(紅留著,是因為 coverage 不是 "true",不是因為 run 本身不合格)。"""
    assert redlight.run_state(runs[0]) == u"B", runs[0]
    assert redlight.validate_session(runs[1]) == [], runs[1]
    assert redlight.run_state(runs[1]) == u"A", runs[1]


class TestEvidencePolicyChain:

    def test_g3_no_policy_does_not_retire_a_known_red(self, tmp_path, monkeypatch):
        """#28(〈四十六〉46.4 第 3 點、第 4 點 正一的鏈條面:未初始化 ⇒ unknown ⇒ 不得退紅)。分類:behavior-red。

        repo 已提交設定與 conftest,但從未有 policy。R1 固定全套:test_a failed ⇒ 已知紅。
        R2 固定全套:全 passed ⇒ 不得退紅、不得 green。
        BASELINE 上失敗的原因:R2 在 `<BASELINE>:.claude/hooks/redlight.py:833` 判 `"true"` ⇒
        `<BASELINE>:.claude/portable/status.py:456-474` 退掉 test_a ⇒ green。
        """
        root = _root_with_redlight(tmp_path)
        _g_committed(root)
        runs = _g_red_then(root, monkeypatch)
        _g_assert_scenario(runs)
        got = _lines_of(root)
        assert u"tests/test_x.py" in got[u"red"], got
        assert u"tests/test_x.py" not in got[u"green"], got

    @pytest.mark.parametrize("state", ["worktree-only", "worktree-differs"])
    def test_g3_an_uncommitted_policy_does_not_retire_a_known_red(self, tmp_path, monkeypatch, state):
        """#29–#30(〈四十六〉46.4 第 4 點 負三 / 負二 的鏈條版)。分類:behavior-red。

        `[worktree-only]`:合法 policy 只在工作樹,HEAD 從未有它(負三)。
        `[worktree-differs]`:HEAD 有合法 policy,工作樹內容不同、未 commit(負二)。
        R1 固定全套:test_a failed ⇒ 已知紅。R2 固定全套:全 passed ⇒ 不得退紅、不得 green。
        BASELINE 上失敗的原因:同 #28(`<BASELINE>:.claude/hooks/redlight.py:833`;`<BASELINE>:.claude/portable/status.py:456-474`)。
        """
        root = _root_with_redlight(tmp_path)
        if state == "worktree-only":
            _g_committed(root, policy=_g_policy(), commit_policy=False)
        else:
            _g_committed(root, policy=_g_policy())
            _g_write(root, _G_POLICY_FILE,
                     json.dumps(_g_policy(), ensure_ascii=False, indent=2) + u"\n\n")
        runs = _g_red_then(root, monkeypatch)
        _g_assert_scenario(runs)
        got = _lines_of(root)
        assert u"tests/test_x.py" in got[u"red"], got
        assert u"tests/test_x.py" not in got[u"green"], got

    def test_g3_a_policy_environment_mismatch_does_not_retire_a_known_red(self, tmp_path, monkeypatch):
        """#31(〈四十六〉46.4 第 4 點 負一的鏈條版)。分類:behavior-red。

        已提交 addopts `-ra`、policy `committed_overrides: []`(兩者自洽)並已提交。R1 固定全套:test_a failed ⇒ 已知紅。
        R2:經 `PYTEST_ADDOPTS` 帶入 `--strict-markers` ⇒ `override_ini == ["strict_markers=true"]`(policy 未列),
        全 passed ⇒ 不得退紅、不得 green。
        BASELINE 上失敗的原因:`<BASELINE>:.claude/hooks/redlight.py:795` 的比較對象是框架常數 ⇒ `:833` 判 `"true"` ⇒
        `<BASELINE>:.claude/portable/status.py:456-474` 退紅。
        """
        root = _root_with_redlight(tmp_path)
        _g_committed(root, policy=_g_policy(committed_overrides=[]), addopts=u"-ra")
        runs = _g_red_then(root, monkeypatch)
        _g_assert_scenario(runs)
        assert runs[1]["completeness"]["override_ini"] == [u"strict_markers=true"], runs[1]["completeness"]
        got = _lines_of(root)
        assert u"tests/test_x.py" in got[u"red"], got
        assert u"tests/test_x.py" not in got[u"green"], got

    def test_g3_a_matching_committed_policy_retires_the_red(self, tmp_path, monkeypatch):
        """#32(〈四十六〉46.4 第 4 點 正二的鏈條版:提交合法 policy → 製造 red → 固定全套 → true → red 合法退休)。
        分類:regression-lock。

        提交合法 policy(值 = 現行常數)、工作樹 = HEAD。R1 固定全套:test_a failed ⇒ 已知紅。
        R2 固定全套:全 passed ⇒ X 退紅、在 green。
        """
        root = _root_with_redlight(tmp_path)
        _g_committed(root, policy=_g_policy())
        runs = _g_red_then(root, monkeypatch)
        _g_assert_scenario(runs)
        got = _lines_of(root)
        assert u"tests/test_x.py" in got[u"green"], got
        assert u"tests/test_x.py" not in got[u"red"], got


# ═══════════════════════════════════════════════════════════════════════════
# 票 145 Station 3g-1b 紅燈 —— status 的 evidence policy 狀態行(〈四十八〉48.1 第 6 點;〈五十〉50.1)
#
# 合約:status 輸出恰有一行以 `evidence policy: ` 開頭,值依 policy 狀態為
# 未初始化 / 未提交 / 工作樹與 HEAD 不同 / 格式不明 / 超出框架能力邊界 / 有效,
# 並帶 `(source: .agents/evidence-policy.json)`。沒有這一行,「未初始化 ⇒ 永遠 unknown」對下游是靜默的。
# 下文 `<BASELINE>` = 7a15ea081da1bf23cc79e04aef76065438f65219(S3G2)。
#
# 每一案都在**真的** git tmp repo(`_g_committed`)上佈置 policy 狀態,再呼叫 `render(root)`。
# 本段 helper 全部新寫;既有 helper(`_root_with_redlight` / `_g_committed` / `_g_policy` / `_g_write` /
# `_t_git` / `_lines` / `render`)只呼叫、不修改。
# ═══════════════════════════════════════════════════════════════════════════

_G_STATUS_PREFIX = u"evidence policy: "
_G_STATUS_SOURCE = u"(source: .agents/evidence-policy.json)"

_G_STATUS_EXPECTED = {
    u"uninitialized": u"未初始化",
    u"uncommitted": u"未提交",
    u"worktree-differs": u"工作樹與 HEAD 不同",
    u"unknown-schema": u"格式不明",
    u"outside-boundary": u"超出框架能力邊界",
    u"valid": u"有效",
}


def _g_policy_json(policy):
    return json.dumps(policy, ensure_ascii=False, indent=2) + u"\n"


def _g_without_key(policy, key):
    out = dict(policy)
    out.pop(key)
    return out


# [unknown-schema] 依序涵蓋的已提交文件:JSON malformed、schema 名稱不認得、version 不支援、
# 必要欄位缺失、型別錯誤(後兩者同屬「必要欄位缺失 / 型別錯誤」一類,兩種都測)。
_G_UNKNOWN_DOCUMENTS = [
    (u"malformed-json", u"{not json\n"),
    (u"unknown-schema-name", _g_policy_json(_g_policy(schema=u"other.evidence-policy"))),
    (u"unsupported-version", _g_policy_json(_g_policy(version=2))),
    (u"missing-field", _g_policy_json(_g_without_key(_g_policy(), u"dists"))),
    (u"wrong-type", _g_policy_json(_g_policy(python_versions=u"3.11"))),
]


def _g_policy_status_line(root):
    """`render(root)` 裡以 `evidence policy: ` 開頭的行;必須恰有一行。"""
    out = render(root)
    hits = [ln.strip() for ln in _lines(out) if ln.strip().startswith(_G_STATUS_PREFIX)]
    assert len(hits) == 1, (hits, out)
    return hits[0]


def _g_assert_status(line, expected):
    value = line[len(_G_STATUS_PREFIX):].split(u"(source:")[0].strip()
    assert value.startswith(expected), (expected, line)
    assert _G_STATUS_SOURCE in line, line


def _g_status_root(base, state):
    """在 `base` 底下造一個帶 redlight 的 tmp repo,佈置成 `state`;回傳 root。"""
    root = _root_with_redlight(base)
    if state == u"uninitialized":
        _g_committed(root)
    elif state == u"uncommitted":
        _g_committed(root, policy=_g_policy(), commit_policy=False)
    elif state == u"worktree-differs":
        _g_committed(root, policy=_g_policy())
        _g_write(root, _G_POLICY_FILE, _g_policy_json(_g_policy()) + u"\n")
    elif state == u"outside-boundary":
        _g_committed(root, policy=_g_policy(python_versions=[u"3.11", u"3.12"]))
    elif state == u"valid":
        _g_committed(root, policy=_g_policy())
    else:
        raise ValueError(state)
    return root


def _g_committed_raw_policy(base, text):
    """已提交設定與 conftest 的 repo,再把 `text`(原樣)提交為 canonical policy。"""
    root = _root_with_redlight(base)
    _g_committed(root)
    _g_write(root, _G_POLICY_FILE, text)
    _t_git(root, "add", _G_POLICY_FILE)
    _t_git(root, "commit", "-q", "-m", "policy")
    return root


class TestEvidencePolicyStatusLine:

    @pytest.mark.parametrize("state", list(_G_STATUS_EXPECTED))
    def test_g3_status_shows_the_policy_state(self, tmp_path, state):
        """〈五十〉50.1 第 3 點(status 的 policy 狀態行)。分類:behavior-red。

        - `[uninitialized]`:repo 從未有 policy ⇒ `未初始化`;
        - `[uncommitted]`:合法 policy 只在工作樹 ⇒ `未提交`;
        - `[worktree-differs]`:HEAD 有合法 policy,工作樹內容不同 ⇒ `工作樹與 HEAD 不同`;
        - `[unknown-schema]`:依序五份**已提交**文件(JSON malformed、schema 名稱不認得、version 2、
          缺 `dists`、`python_versions` 為字串),**逐一**斷言 ⇒ 都是 `格式不明`;
        - `[outside-boundary]`:已提交 policy 的 `python_versions` 含 3.12(框架能力邊界外)⇒ `超出框架能力邊界`;
        - `[valid]`:已提交合法 policy、工作樹 = HEAD ⇒ `有效`。
        每一案的那一行都須帶 `(source: .agents/evidence-policy.json)`。
        BASELINE 上失敗的原因:`<BASELINE>:.claude/portable/status.py` 沒有 `evidence policy:` 這一行
        (`_g_policy_status_line` 的「恰有一行」斷言)。
        """
        expected = _G_STATUS_EXPECTED[state]
        if state == u"unknown-schema":
            for name, text in _G_UNKNOWN_DOCUMENTS:
                root = _g_committed_raw_policy(tmp_path / name, text)
                _g_assert_status(_g_policy_status_line(root), expected)
            return
        root = _g_status_root(tmp_path, state)
        _g_assert_status(_g_policy_status_line(root), expected)


# ─────────────────────────────────────────────────────────────────────────────
# 票 146 第三站 3e 紅燈(S3e-146-1)—— status 的 R10 兩行
#
# 臨時 root 自建(gate.py + redlight.py 真檔複本、已提交空白 allowlist);**不改 `_make_root`**。
# claude_root 一律以 tmp 注入 `status._extension_claude_root`,不碰真的 ~/.claude。缺 API ⇒ 測試內紅。
# ─────────────────────────────────────────────────────────────────────────────

_T146_REAL_REDLIGHT = ROOT / ".claude" / "hooks" / "redlight.py"
_T146_ALLOWLIST = {"schema": "monkeyleash.extension-allowlist", "version": 1,
                   "dev_mod_files": [], "user_skill_plugins": [], "user_commands": [],
                   "project_settings_hook_commands": [], "mcp_json_servers": []}


class TestTicket146StatusLines:
    """票 146 第三站 3e:status 顯示與 pre-commit 消費同一份 extension_report。全部在 S3e-146-1 預期各自失敗。"""

    @staticmethod
    def _git(root, *args):
        subprocess.run(["git"] + list(args), cwd=str(root), capture_output=True, check=True)

    def _root(self, tmp_path, with_redlight=True):
        root = tmp_path / "repo"
        (root / ".dev").mkdir(parents=True)
        (root / ".claude" / "hooks").mkdir(parents=True)
        (root / ".agents").mkdir(parents=True)
        with io.open(str(root / ".dev" / "pipeline.json"), "w", encoding="utf-8") as f:
            json.dump({"current_stage": "implement", "feature": "testfeat",
                       "ticket_id": "146", "updated": "2026-10-06"}, f)
        shutil.copy2(str(REAL_GATE), str(root / ".claude" / "hooks" / "gate.py"))
        shutil.copy2(str(REAL_STAGES), str(root / ".agents" / "pipeline-stages.yaml"))
        if with_redlight:
            shutil.copy2(str(_T146_REAL_REDLIGHT), str(root / ".claude" / "hooks" / "redlight.py"))
        with io.open(str(root / ".agents" / "extension-allowlist.json"), "w",
                     encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(_T146_ALLOWLIST, ensure_ascii=False, indent=2) + "\n")
        self._git(root, "init", "-q")
        self._git(root, "config", "user.email", "t@example.invalid")
        self._git(root, "config", "user.name", "t")
        self._git(root, "add", ".agents/extension-allowlist.json")
        self._git(root, "commit", "-q", "-m", "baseline")
        claude = tmp_path / "claude"
        claude.mkdir()
        return str(root), claude

    @staticmethod
    def _inject(monkeypatch, claude):
        assert hasattr(status, "_extension_claude_root"), \
            "v0 contract not implemented: status._extension_claude_root"
        monkeypatch.setattr(status, "_extension_claude_root", lambda: str(claude))

    @staticmethod
    def _two_lines(out):
        ext = [ln for ln in _lines(out) if ln.startswith(u"extension integrity (R10): ")]
        rt = [ln for ln in _lines(out) if ln.startswith(u"runtime loaded set: ")]
        return ext, rt

    def test_t146_20(self, tmp_path, monkeypatch):
        """T146-20:DECLARED_OK 佈置 ⇒ R10 兩行各恰好 1 行,第一行值 == extension_report(...)["lines"][0];對應 Q4、裁決 (w)。"""
        root, claude = self._root(tmp_path)
        self._inject(monkeypatch, claude)
        out = render(root)
        ext, rt = self._two_lines(out)
        assert len(ext) == 1 and len(rt) == 1, (ext, rt)
        rl = status.load_redlight(root)
        assert rl is not None and hasattr(rl, "extension_report"), \
            "v0 contract not implemented: redlight.extension_report"
        rep = rl.extension_report(root, str(claude))
        assert _value_of(out, u"extension integrity (R10)") == rep["lines"][0], (ext, rep["lines"])

    def test_t146_28(self, tmp_path, monkeypatch):
        """T146-28:status 實際消費的 report 與 gate.check_extension_integrity 消費的 report 同 state、同第一行;對應裁決 (w)。"""
        root, claude = self._root(tmp_path)
        self._inject(monkeypatch, claude)
        rl = status.load_redlight(root)
        assert rl is not None and hasattr(rl, "extension_report"), \
            "v0 contract not implemented: redlight.extension_report"
        orig = rl.extension_report
        seen = []

        def recording(*a, **k):
            r = orig(*a, **k)
            seen.append(r)
            return r
        monkeypatch.setattr(rl, "extension_report", recording)
        out = render(root)
        assert len(seen) == 1, u"status 呼叫 extension_report 的次數:%d" % len(seen)
        consumed = seen[0]
        assert _value_of(out, u"extension integrity (R10)") == consumed["lines"][0], (out, consumed["lines"])
        g = status.load_gate(root)
        assert hasattr(g, "_extension_claude_root") and hasattr(g, "check_extension_integrity"), \
            "v0 contract not implemented: gate._extension_claude_root / gate.check_extension_integrity"
        monkeypatch.setattr(g, "_extension_claude_root", lambda: str(claude))
        gate_report = g.check_extension_integrity()["report"]
        assert gate_report["state"] == consumed["state"], (gate_report["state"], consumed["state"])
        assert gate_report["lines"][0] == consumed["lines"][0], (gate_report["lines"], consumed["lines"])
        direct = orig(root, str(claude))
        assert direct["state"] == consumed["state"], (direct["state"], consumed["state"])

    def test_t146_30(self, tmp_path, monkeypatch):
        """T146-30:R10 兩行恰好找到,各帶 (source:,值不含 VERDICT_TOKENS;對應 Q4。"""
        root, claude = self._root(tmp_path)
        self._inject(monkeypatch, claude)
        out = render(root)
        ext, rt = self._two_lines(out)
        assert len(ext) == 1 and len(rt) == 1, (ext, rt)
        for ln in ext + rt:
            assert u"(source:" in ln, ln
            value = ln.split(u":", 1)[1].split(u"(source:")[0]
            hits = [t for t in VERDICT_TOKENS if t in value]
            assert hits == [], (hits, ln)

    def test_t146_20b(self, tmp_path, monkeypatch):
        """T146-20b:臨時 root 只有 gate.py ⇒「未記錄（146 判定器不在）」且不出現 static surfaces;對應裁決 (x)。"""
        root, claude = self._root(tmp_path, with_redlight=False)
        self._inject(monkeypatch, claude)
        out = render(root)
        assert u"未記錄（146 判定器不在）" in out, out
        assert u"static surfaces:" not in out, out
