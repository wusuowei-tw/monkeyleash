# -*- coding: utf-8 -*-
"""票 01 — 兩層不變式,以及閘門自我修改的豁免。

不變式是單向的:**任何時點下,權威層的嚴格程度不得低於前哨。**
前哨擋而權威放行 = 缺陷;權威擋而前哨放行 = 合規(**R4** 只在提交時評估就是這種)。

**⚠ 更正(票 47 批 0,2026-08-18):舊文寫「R4/R5」,而 R5 不是這個例子。**
R5 **兩層都跑** —— 前哨走 `gate.py:2051` 的 `mount_violations_cached()`,
權威層走 `gate.py:2419-2420` 直接呼叫(不快取)。原句保留形狀、只拿掉 R5(F-036)。

這條測試存在的理由是 F-017:修 R2 的時點語意時,at_commit 分支被寫成提早返回,
把 R3 在提交時整個跳過,權威層反而比前哨鬆。當時沒有任何東西發現。
"""

import hashlib
import importlib.util
import io
import json
import os
import pathlib
import shutil
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load_gate():
    spec = importlib.util.spec_from_file_location(
        "gate_under_test", ROOT / ".claude" / "hooks" / "gate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gate = _load_gate()


# 語料:涵蓋 R1 / R2 / R3 的放行與擋下路徑。
# 內容刻意樸素 —— 這裡驗的是路徑與站別的判定,不是內容解析。
CORPUS = [
    ("docs/specs/x.md", "## 問題\n只有散文。"),
    ("docs/specs/x.md", "## 問題\n```python\nprint(1)\n```"),
    (".scratch/f/spec.md", "## 問題\n只有散文。"),
    (".scratch/f/spec.md", "## 問題\n```python\nprint(1)\n```"),
    (".scratch/f/issues/01-x.md", "票內容"),
    (".scratch/f/prototype/try.py", "print(1)"),
    ("macro_audit/classify.py", "x = 1"),
    ("macro_audit/no_such_module.py", "x = 1"),
    ("tests/test_classify.py", "def test_x(): pass"),
    ("docs/agents/friction-log.md", "import 這個字不是程式"),
    (".dev/pipeline.json", "{}"),
    ("README.md", "說明"),
]

STAGES = ["idle", "grill", "spec", "tickets", "implement", "review"]


@pytest.fixture
def fake_repo(tmp_path, monkeypatch):
    """一個測試自己造的最小 repo。回傳 (根目錄, 被測原始碼的絕對路徑)。

    **框架測試只能斷言框架的性質**(票 07)。借宿主 repo 現成的檔案
    (`macro_audit/classify.py`)當樣本,等於把「這個 repo 剛好有這個檔案」
    寫進斷言 —— 裝到新專案就紅,而那個紅與新專案無關,
    只會教人「這套測試本來就紅」,之後真的紅也不會被當一回事(F-031)。

    路徑用絕對的:`rel()` 走 `abspath`,相對路徑會以 cwd 為基準而不是 ROOT。
    """
    (tmp_path / "pkg").mkdir()
    (tmp_path / "tests").mkdir()
    probe = tmp_path / "pkg" / "thing.py"
    probe.write_text("x = 1", encoding="utf-8")
    (tmp_path / "tests" / "test_thing.py").write_text("def test_x(): pass", encoding="utf-8")
    monkeypatch.setattr(gate, "ROOT", str(tmp_path))
    monkeypatch.setattr(gate, "LEGACY_LIST", str(tmp_path / "legacy.txt"))
    monkeypatch.setattr(gate, "RUN_LOG", str(tmp_path / "no-such-log.jsonl"))
    monkeypatch.setattr(gate, "load_stage", lambda: ("implement", "01"))
    return tmp_path, str(probe)


def _rule_of(msg):
    """從擋下訊息取規則代號。`[R2/commit]` 與 `[R2/fail-closed]` 都歸 R2。"""
    return msg.split("]")[0].lstrip("[").split("/")[0] if msg else None


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("path,content", CORPUS)
def test_coverage_no_rule_is_skipped_at_the_authoritative_layer(
        monkeypatch, stage, path, content):
    """不變式一(結構):每條在前哨會評估的規則,權威層也必須評估到。

    用規則代號出現與否判定,不比較判決 —— 抓的是規則被刪除或跳過。
    F-017 就是這個形狀:at_commit 分支提早返回,R3 在提交時整個沒被評估。
    """
    monkeypatch.setattr(gate, "load_stage", lambda: (stage, "01"))
    sentinel, authoritative = [], []
    gate.check(path, content, at_commit=False, trace=sentinel)
    gate.check(path, content, at_commit=True, trace=authoritative)
    missing = set(sentinel) - set(authoritative)
    assert not missing, (
        "規則 %s 在前哨被評估,在權威層卻沒有:stage=%s path=%s —— "
        "繞過前哨的人就完全沒有東西守。" % (sorted(missing), stage, path))


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("path,content", CORPUS)
def test_every_divergence_is_declared_by_its_rule(monkeypatch, stage, path, content):
    """不變式二(行為):權威比前哨鬆的每一個案例,其負責規則必須帶有分時點宣告。

    抓的是規則還在、被評估、判決卻被放水 —— 涵蓋性單獨看不見的變體。
    宣告寫在規則自己的定義裡並指向 ADR,不在本測試維護豁免清單(那會退化成裝飾)。
    """
    monkeypatch.setattr(gate, "load_stage", lambda: (stage, "01"))
    s_msg = gate.check(path, content, at_commit=False)
    a_msg = gate.check(path, content, at_commit=True)
    if s_msg is None or a_msg is not None:
        return  # 沒有分歧
    rule = _rule_of(s_msg)
    decl = gate.RULE_DIVERGENCE.get(rule)
    assert decl, (
        "未宣告的分時點分歧:規則 %s 在前哨擋、權威放行(stage=%s path=%s)。"
        "刻意的話寫進 gate.RULE_DIVERGENCE 並附 ADR;不是的話就是缺陷。"
        % (rule, stage, path))
    adr = ROOT / decl["adr"]
    assert adr.exists(), "宣告指向的 ADR 不存在:%s" % decl["adr"]


@pytest.mark.parametrize("path,expected", [
    ("docs/specs/x.md", "R1"),
    (".scratch/f/spec.md", "R1"),
    ("macro_audit/anything.py", "R2"),
    ("macro_audit/anything.py", "R3"),
])
def test_the_detector_itself_records_each_rule(monkeypatch, path, expected):
    """守住涵蓋性測試自己:trace 若漏記某條規則,它就永遠偵測不到那條規則被跳過。

    這條的由來:R3 的 trace 記錄曾經整個沒被寫進去,而涵蓋性測試照樣全綠 ——
    偵測「X 沒發生」的機制自己被 X 略過了。
    任何這類機制都要問一次:它自己會不會被它要偵測的東西略過?
    """
    monkeypatch.setattr(gate, "load_stage", lambda: ("implement", "01"))
    t = []
    gate.check(path, "x = 1", at_commit=False, trace=t)
    assert expected in t, "trace 沒記到 %s(path=%s),涵蓋性測試對它是盲的" % (expected, path)


def test_the_invariants_do_not_assert_the_reverse(monkeypatch):
    """權威嚴於前哨是合規的,不是不對稱缺陷。

    **R4** 只在提交時評估就是這種情況;為了讓兩層對稱而把成本推進前哨是錯的方向。
    這裡以「存在一個權威嚴於前哨的案例、而測試不因此失敗」來表達單向性。

    **⚠ 更正(票 47 批 0,2026-08-18)**:舊文寫「R4/R5」,而 **R5 兩層都跑**,
    不是這個例子。**下面兩條斷言本來就只驗 R4,一個字都沒改。**
    """
    monkeypatch.setattr(gate, "load_stage", lambda: ("implement", "01"))
    # **R4** 只在 pre_commit 模式被呼叫,`check()` 本身不含它 —— 單向性由此成立:
    # 權威層額外跑的檢查不需要在前哨有對應。
    #
    # **R5 不在這個例子裡(票 47 批 0 更正)。** 它兩層都跑:
    #   前哨      gate.py:2051      mount_violations_cached()  ← 走快取
    #   權威層    gate.py:2419-2420 check_third_axis_mount()
    #                               check_to_spec_override()   ← 不走快取
    #
    # 舊註解寫「R4/R5 只在 pre_commit 模式被呼叫,check() 本身不含它們」——
    # **後半句(check() 不含它們)對兩者都成立,前半句對 R5 是假的**,
    # 而兩個子句支持同一個結論。F-103 那一族:錯的論據與正確結論同向,
    # 所以沒有任何東西會揭穿它。
    assert "check_skill_copies" not in gate.mode_hook.__code__.co_names
    assert "check_skill_copies" in gate.mode_pre_commit.__code__.co_names


class TestExtensionDenylist:
    """票 02 — 副檔名判定從白名單反轉為黑名單。

    白名單是 fail-open:任何新型態的檔案都不在名單上,一律放行。
    目錄那層已經反轉過(F-011),副檔名這層是同一個病的最後一處。
    反轉後被誤擋的檔案,正確處置是把副檔名加進非原始碼清單 ——
    那是一個看得見的決定,不是沉默的洞。
    """

    @pytest.mark.parametrize("path", [
        "macro_audit/Dockerfile",
        "macro_audit/Makefile",
        "macro_audit/run_daily",          # 無副檔名的腳本
        "macro_audit/deploy.tf",          # 還沒用過的工具的組態
        "macro_audit/schema.sql",
    ])
    def test_unknown_file_types_in_source_dirs_are_guarded(self, monkeypatch, path):
        """白名單時代這些全部放行。反轉後預設被守。"""
        monkeypatch.setattr(gate, "load_stage", lambda: ("spec", None))
        msg = gate.check(path, "anything", at_commit=False)
        assert msg is not None and "R2" in msg, "%s 未被守到" % path

    @pytest.mark.parametrize("path", [
        "macro_audit/README.md",
        "macro_audit/fixtures/us_macro_series.yaml",
        "macro_audit/data.csv",
        "macro_audit/notes.txt",
    ])
    def test_declared_non_source_extensions_pass(self, monkeypatch, path):
        """在非原始碼清單裡的副檔名照常放行。"""
        monkeypatch.setattr(gate, "load_stage", lambda: ("spec", None))
        assert gate.check(path, "anything", at_commit=False) is None, path

    def test_a_false_block_is_fixed_by_declaring_the_extension(self, monkeypatch):
        """誤擋的處置是把副檔名加進清單 —— 看得見的決定,不是沉默的洞。"""
        monkeypatch.setattr(gate, "load_stage", lambda: ("spec", None))
        p = "macro_audit/config.someformat"
        assert gate.check(p, "x", at_commit=False) is not None  # 未宣告 → 守
        # 清單是 {項目: 理由} —— 宣告一個新例外必須同時寫下理由,這是本票的設計,
        # 不是測試遷就實作:沒有理由欄的話判準會漂移而沒有東西攔得住。
        declared = dict(gate.NON_SOURCE_EXT)
        declared[".someformat"] = "示範用格式,不被執行也不被建置消費"
        monkeypatch.setattr(gate, "NON_SOURCE_EXT", declared)
        assert gate.check(p, "x", at_commit=False) is None      # 宣告後 → 放行

    @pytest.mark.parametrize("path,expected_list", [
        ("macro_audit/deploy.tf", "NON_SOURCE_EXT"),      # 有副檔名 → 指副檔名清單
        ("macro_audit/Makefile", "NON_SOURCE_NAMES"),     # 無副檔名 → 指檔名清單
    ])
    def test_block_message_points_at_the_right_list(self, monkeypatch, path, expected_list):
        """三個路徑全印出來的話,人要自己判斷該改哪一份 ——
        那正好是這個訊息本來要省掉的認知成本。"""
        monkeypatch.setattr(gate, "load_stage", lambda: ("spec", None))
        msg = gate.check(path, "x", at_commit=False)
        assert expected_list in msg and ".claude/hooks/gate.py:" in msg
        wrong = "NON_SOURCE_NAMES" if expected_list == "NON_SOURCE_EXT" else "NON_SOURCE_EXT"
        assert wrong not in msg, "同時指了兩份清單,認知成本沒省掉"


class TestIsSourcePathResolvesDotDotBeforeMatching:
    """framework-updates/82:`is_source_path` 取 `r.split("/")[0]` 當 top,
    **比對前不做 normpath**。

    `docs/../pkg/thing.py` 的 top 是 `docs` -> 判成非原始碼 -> **R2/R3 不管它**。
    方向是 fail-open:**該管的檔案不被管**。

    這與同一個 repo 裡 `g1_guard._is_scratch()` 的判準是同一條(`F-051`):
    **任何用子字串或前綴放行的地方,都要先解 `..`。**
    那句話寫在 `_is_scratch()` 的 docstring 裡 ——
    **同一份判準寫在 A 模組的註解裡,不會讓 B 模組變安全。註解不是機制。**
    """

    @pytest.mark.parametrize("rel_path", [
        "scripts/../pkg/thing.py",
        "docs/../pkg/thing.py",
        "tests/../pkg/thing.py",
        r"docs\..\pkg\thing.py",
    ])
    def test_a_path_that_climbs_back_out_is_still_source(self, rel_path):
        assert gate.is_source_path(rel_path) is True, (
            "**該被 R2/R3 管的檔案被判成非原始碼**:%s —— "
            "top 是 `..` 前面那一段,而 `..` 收斂之後它根本不在那個目錄底下"
            % rel_path)

    @pytest.mark.parametrize("rel_path,expect", [
        ("pkg/thing.py", True),          # 一般原始碼
        ("docs/x.py", False),            # 真的在 docs 底下
        ("docsx/thing.py", True),        # 邊界:相鄰名稱不誤中
        ("tests/test_gate.py", False),   # 真的在 tests 底下
        ("docs/a/../x.py", False),       # 收斂後仍在 docs 底下
    ])
    def test_the_ordinary_answers_do_not_change(self, rel_path, expect):
        """**反控。** 修法不得把判定往任何一個方向整體推。"""
        assert gate.is_source_path(rel_path) is expect, rel_path


class TestBothLayersNormalizeAndNeitherIsLoadBearingAlone:
    """**兩層都在,哪一層失效都還有另一層。**

    `is_source_path` 生產上只有一個呼叫點,而餵它的 `r` 來自 `rel()` ——
    `os.path.relpath(os.path.abspath(path), ROOT)`,**`abspath` 已經把 `..` 收掉了**。
    另一個消費端吃的是 `git diff --cached --name-only`,git 的輸出也是正規化的。

    **所以票 82 修的是函式契約的洞,不是活洞。** 而「呼叫端剛好也洗」這件事
    在修之前**沒有任何測試在守** —— 它只存在於讀過那兩處程式碼的人腦子裡。
    改一次 `rel()`(例如為了效能拿掉 `abspath`),第二層就沒了,
    **而那時沒有東西會說**。這一組測試就是那個「有東西會說」。
    """

    def test_rel_collapses_dotdot_before_the_matcher_ever_sees_it(self):
        r = gate.rel(os.path.join(gate.ROOT, "docs", "..", "pkg", "thing.py"))
        assert ".." not in r.split("/"), (
            "`rel()` 不再收斂 `..` —— 第二層沒了,而 `is_source_path` 是唯一剩下的:%s" % r)
        assert r == "pkg/thing.py", r

    def test_the_two_layers_agree_on_the_same_input(self):
        """兩層各自的答案要一致 —— 不一致代表有一層在做另一層以為它沒做的事。"""
        raw = os.path.join(gate.ROOT, "docs", "..", "pkg", "thing.py")
        assert gate.is_source_path(gate.rel(raw)) is True
        assert gate.is_source_path("docs/../pkg/thing.py") is True


class TestBothHeadingCriteriaAgree:
    """framework-updates/98:**`sync` 與 R9 讀的不是同一份「發號標題」判準。**

    R9(`gate.py:1283` 的 `_FRICTION_HEADING`)**嚴**:前綴必須是字母、
    號碼必須緊接 `## `。`sync.py:38` 的 `HEADING` **鬆**:`## ` 之後
    第一個非空白詞就算號碼。於是 `## 併記於 F-118(…)` 在 R9 眼裡是「提到」,
    在 sync 眼裡是一個叫 `併記於` 的號碼 —— 而 friction log 裡有**兩則**那樣的
    標題(`F-118` 與 `F-145`,兩個不同的號),**sync 因此拒絕了整次更新**
    (2026-08-31 實測,`exit=1`)。

    `gate.py:1283` 上面那段註解**逐字寫著**那個寫法是刻意的:
    「本檔自己就有一段 `## 併記於 F-118(…)`,它刻意寫成這樣正是為了不被本條誤判。」
    **⇒ sync 抓到的正是 R9 刻意排除的那一類。**

    ## 為什麼是「兩份」而不是「一份」

    `gate.py` 那份**刻意不與 portable 共用**(票 42,理由見
    `test_both_staged_listings_agree_on_a_gitlink` 的 docstring):
    權威層要依賴最少的東西,**讓它 import `portable/` 會多一個失效點,
    而閘門起不來的樣子跟沒裝一模一樣(全靜默)**。
    所以本條測的是**兩份的行為一致**,不是字面相同 —— 與那條 gitlink 對帳同族。

    ## ⚠ 為什麼比對的對象是 `sync.HEADING`,不是那個新模組

    要問的是「**sync 實際上用什麼判準**」。直接比對新模組的話,
    新模組自己一定與 `gate.py` 一致(它是照著寫的),而 `sync` 還在用舊字面時
    這條測試會**綠** —— 那正是本票要抓的缺陷,而它會從測試的視野裡消失。
    **判準要釘在使用端,不是釘在定義端。**
    """

    # (標題行, R9 是否判定它為「發號」)
    CORPUS = [
        (u"## F-118 甲", True),
        (u"## TSI-038 前哨在場的三段驗收", True),
        (u"## 併記於 F-118(2026-08-26):那次相撞真的發生了", False),
        (u"## 這份規則(附決策)", False),
        (u"見 F-005 與 F-005 的討論", False),
    ]

    def _sync_side(self):
        """載入 `sync.py`,回它實際使用的那個判準。"""
        import importlib.util
        path = ROOT / ".claude" / "portable" / "sync.py"
        spec = importlib.util.spec_from_file_location("sync_under_test", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.HEADING

    def _gate_says(self, line):
        return gate._FRICTION_HEADING.match(line) is not None

    @pytest.mark.parametrize("line,expected", CORPUS)
    def test_the_authoritative_side_matches_the_corpus(self, line, expected):
        """**先釘住 R9 那一份自己是對的** —— 否則「兩邊一致」也可能是一起錯。"""
        assert self._gate_says(line) is expected, line

    @pytest.mark.parametrize("line,expected", CORPUS)
    def test_both_sides_agree_on_the_same_line(self, line, expected):
        theirs = self._sync_side().match(line) is not None
        mine = self._gate_says(line)
        assert theirs is mine, (
            "兩份判準對同一行給出不同答案:%r —— R9=%s / sync=%s。"
            "同缺陷的兩份實作必然漂開(F-058 家族),而這一次漂的後果是:"
            "sync 把一個散文標題當成條目號碼,拒絕整次更新。"
            % (line, mine, theirs))

    def test_the_parity_check_itself_goes_red_when_one_side_drifts(self):
        """**釘住上面那條會咬。**

        沒有這條的話,`test_both_sides_agree_on_the_same_line` 只是一句
        「兩邊相等」的宣稱 —— 它可能因為**任何**理由恆真(兩邊都回 None、
        兩邊其實是同一個物件、斷言寫錯方向),而
        **恆真的斷言與有效的斷言在測試輸出上長得一模一樣。**

        做法:拿一份**刻意寫鬆**的正則當假的 sync 側,斷言對帳**必須**抓到它。
        """
        import re as _re
        drifted = _re.compile(r"^## (\S+)")
        caught = [line for line, _ in self.CORPUS
                  if (drifted.match(line) is not None) != self._gate_says(line)]
        assert caught, (
            "拿一份公認鬆的正則當對照,對帳竟然一個差異都沒抓到 —— "
            "那代表這組語料分辨不出鬆緊,對帳斷言是恆真的")


class TestNonSourceListsAreWellFormed:
    """三份清單的形狀 —— 清單一長,判準就會漂移。"""

    LISTS = ("NON_SOURCE_DIRS", "NON_SOURCE_EXT", "NON_SOURCE_NAMES")

    @pytest.mark.parametrize("name", LISTS)
    def test_every_entry_carries_a_reason(self, name):
        """理由欄是讓判準漂移看得見的東西。

        沒有理由欄的話,一年後有人往裡面加 entrypoint.sh,沒有東西攔得住 ——
        判準是「會不會被執行或被建置工具消費」,理由欄逼人每次都回答一次。
        """
        table = getattr(gate, name)
        assert isinstance(table, dict), "%s 必須是 {項目: 理由} 而非裸清單" % name
        for key, why in table.items():
            assert isinstance(why, str) and why.strip(), "%s 的 %r 沒有理由" % (name, key)

    def test_the_three_lists_are_mutually_exclusive(self):
        """同一個項目不得落在兩份裡,否則行為取決於檢查順序 —— 那是隱形的。"""
        seen = {}
        for name in self.LISTS:
            for key in getattr(gate, name):
                assert key not in seen, (
                    "%r 同時在 %s 與 %s,行為取決於檢查順序" % (key, seen[key], name))
                seen[key] = name

    def test_no_filename_is_also_matched_by_an_extension_rule(self):
        """檔名清單裡的項目不得同時被某條副檔名規則命中。

        `.env` 這種「長得像副檔名的檔名」是典型:放錯清單時兩邊都會中,
        誰先檢查誰決定行為。
        """
        exts = tuple(gate.NON_SOURCE_EXT)
        for name in gate.NON_SOURCE_NAMES:
            assert not name.endswith(exts), (
                "檔名 %r 同時被副檔名規則命中,兩份清單重疊" % name)


class TestSkillMirrorSingleRule:
    """票 03 — 鏡像檢查改成單一規則兩分支。

    原本守的是「三份實體副本可能各自 drift」。佈局改成 symlink 之後,
    一致性由構造保證 —— 那條規則全輪只觸發過一次,還是人工製造的負向測試。
    一條永遠不會在真實流程生效的規則,看起來像在守,實際上什麼都沒守。

    改法不是並排兩個檢查(那會讓其中一個在當下佈局永遠不跑,又是同一個處境),
    而是一條規則每次執行都必須回答「現在是哪種佈局」。
    """

    @staticmethod
    def _canon(tmp_path):
        canon = tmp_path / "canon" / "tdd"
        canon.mkdir(parents=True)
        (canon / "SKILL.md").write_text("原始內容", encoding="utf-8")
        return tmp_path / "canon"

    @staticmethod
    def _try_symlink(src, dst):
        try:
            dst.symlink_to(src, target_is_directory=True)
            return dst.is_symlink()
        except (OSError, NotImplementedError):
            return False

    def test_intact_symlink_passes(self, tmp_path):
        canon = self._canon(tmp_path)
        mirror = tmp_path / "mirror"
        mirror.mkdir()
        if not self._try_symlink(canon / "tdd", mirror / "tdd"):
            pytest.skip("此環境無法建立 symlink")
        assert gate.skill_mirror_violations(str(canon), [str(mirror)]) == []

    def test_broken_symlink_is_blocked(self, tmp_path):
        canon = self._canon(tmp_path)
        mirror = tmp_path / "mirror"
        mirror.mkdir()
        if not self._try_symlink(canon / "tdd", mirror / "tdd"):
            pytest.skip("此環境無法建立 symlink")
        import shutil
        shutil.rmtree(canon / "tdd")          # 弄斷:目標消失
        out = gate.skill_mirror_violations(str(canon), [str(mirror)])
        assert out and "R4" in out[0]

    def test_symlink_pointing_outside_canonical_is_blocked(self, tmp_path):
        canon = self._canon(tmp_path)
        elsewhere = tmp_path / "elsewhere" / "tdd"
        elsewhere.mkdir(parents=True)
        (elsewhere / "SKILL.md").write_text("原始內容", encoding="utf-8")
        mirror = tmp_path / "mirror"
        mirror.mkdir()
        if not self._try_symlink(elsewhere, mirror / "tdd"):
            pytest.skip("此環境無法建立 symlink")
        out = gate.skill_mirror_violations(str(canon), [str(mirror)])
        assert out and "R4" in out[0], "指向正典以外仍被放行 —— 內容一樣不代表來源正確"

    def test_physical_copy_with_same_content_passes(self, tmp_path):
        canon = self._canon(tmp_path)
        mirror = tmp_path / "mirror" / "tdd"
        mirror.mkdir(parents=True)
        (mirror / "SKILL.md").write_text("原始內容", encoding="utf-8")
        assert gate.skill_mirror_violations(str(canon), [str(tmp_path / "mirror")]) == []

    def test_physical_copy_that_drifted_is_blocked(self, tmp_path):
        canon = self._canon(tmp_path)
        mirror = tmp_path / "mirror" / "tdd"
        mirror.mkdir(parents=True)
        (mirror / "SKILL.md").write_text("被改過的內容", encoding="utf-8")
        out = gate.skill_mirror_violations(str(canon), [str(tmp_path / "mirror")])
        assert out and "R4" in out[0]

    def test_both_branches_are_reachable_by_the_tests(self, tmp_path):
        """守住這條規則自己:兩個分支都要有測試涵蓋。

        只測一個分支的話,另一個又會變成沒人知道它壞掉的死路徑 ——
        那正是這條規則被改寫的原因(維度 4:偵測機制自己會不會被略過)。
        """
        names = [n for n in dir(self) if n.startswith("test_")]
        assert any("symlink" in n for n in names)
        assert any("physical" in n for n in names)


class TestMountCheckCache:
    """票 04 — 掛載點檢查進前哨,以工作階段為單位快取。

    使用者要在**編輯當下**就知道 skill 被外部更新覆蓋了,不必等提交 ——
    在那之前他可能已經照著壞掉的指令工作了半天。
    但覆蓋只可能來自外部更新指令,是離散事件,不該讓每次編輯都付出讀多個檔案的成本。

    快取的 fail-open 形狀是「拿不準就用舊值」。因此失效判斷本身出錯時要**重算**。
    """

    def test_unchanged_mtime_reuses_the_cached_result(self, tmp_path, monkeypatch):
        monkeypatch.setattr(gate, "MOUNT_CACHE", str(tmp_path / "mount.json"))
        calls = []
        monkeypatch.setattr(gate, "_mount_violations_uncached",
                            lambda: calls.append(1) or [])
        monkeypatch.setattr(gate, "_skills_mtime", lambda: 1000.0)
        gate.mount_violations_cached()
        gate.mount_violations_cached()
        assert len(calls) == 1, "mtime 未變動卻重算了,前哨成本沒省下來"

    def test_changed_mtime_recomputes(self, tmp_path, monkeypatch):
        monkeypatch.setattr(gate, "MOUNT_CACHE", str(tmp_path / "mount.json"))
        calls = []
        monkeypatch.setattr(gate, "_mount_violations_uncached",
                            lambda: calls.append(1) or [])
        monkeypatch.setattr(gate, "_skills_mtime", lambda: 1000.0)
        gate.mount_violations_cached()
        monkeypatch.setattr(gate, "_skills_mtime", lambda: 2000.0)
        gate.mount_violations_cached()
        assert len(calls) == 2

    def test_unreadable_mtime_recomputes_rather_than_reusing(self, tmp_path, monkeypatch):
        """讀不到修改時間 → 重算。拿不準就用舊值是快取的 fail-open 形狀。"""
        monkeypatch.setattr(gate, "MOUNT_CACHE", str(tmp_path / "mount.json"))
        calls = []
        monkeypatch.setattr(gate, "_mount_violations_uncached",
                            lambda: calls.append(1) or [])
        monkeypatch.setattr(gate, "_skills_mtime", lambda: 1000.0)
        gate.mount_violations_cached()
        monkeypatch.setattr(gate, "_skills_mtime", lambda: None)
        gate.mount_violations_cached()
        assert len(calls) == 2

    def test_mtime_older_than_cache_recomputes(self, tmp_path, monkeypatch):
        """時鐘回撥、檔案被還原 —— 比快取還舊也要重算,不是沿用。"""
        monkeypatch.setattr(gate, "MOUNT_CACHE", str(tmp_path / "mount.json"))
        calls = []
        monkeypatch.setattr(gate, "_mount_violations_uncached",
                            lambda: calls.append(1) or [])
        monkeypatch.setattr(gate, "_skills_mtime", lambda: 2000.0)
        gate.mount_violations_cached()
        monkeypatch.setattr(gate, "_skills_mtime", lambda: 1000.0)
        gate.mount_violations_cached()
        assert len(calls) == 2

    def test_deleting_the_cache_still_works(self, tmp_path, monkeypatch):
        """快取是可重建的加速結構 —— 消失就重算,不影響判定。"""
        cache = tmp_path / "mount.json"
        monkeypatch.setattr(gate, "MOUNT_CACHE", str(cache))
        monkeypatch.setattr(gate, "_mount_violations_uncached", lambda: [])
        monkeypatch.setattr(gate, "_skills_mtime", lambda: 1000.0)
        gate.mount_violations_cached()
        cache.unlink()
        assert gate.mount_violations_cached() == []

    def test_broken_patch_is_caught_at_write_time(self, monkeypatch):
        """前哨要在編輯當下就擋,不必等提交。"""
        monkeypatch.setattr(gate, "mount_violations_cached",
                            lambda: ["[R5] 掛載點消失"])
        monkeypatch.setattr(gate, "load_stage", lambda: ("implement", "01"))
        assert gate.mode_hook_would_block_on_mounts() is True


class TestUnallowedWriteTargets:
    """R7 的目標抽取 —— gate.py 的公開判定,所以釘在 gate 自己的測試檔。

    行為層的正負控在 tests/test_bash_write.py;這裡驗的是**抽出來的東西對不對**。
    兩層都要:只驗行為的話,「碰巧擋對了」與「真的看懂了目標」分不開。
    """

    def test_it_lists_every_redirect_target(self):
        got = gate.unallowed_write_targets("python x.py > out.txt 2>/dev/null")
        assert got == ["out.txt"], got

    def test_dev_null_alone_yields_nothing(self):
        assert gate.unallowed_write_targets("ls >/dev/null 2>&1") == []

    def test_a_write_command_operand_counts_as_a_target(self):
        got = gate.unallowed_write_targets("rm -rf important_dir >/dev/null")
        assert "important_dir" in got, got

    def test_flags_are_not_mistaken_for_targets(self):
        got = gate.unallowed_write_targets("rm -rf important_dir")
        assert got == ["important_dir"], got

    def test_an_allowed_operand_is_not_listed(self):
        assert gate.unallowed_write_targets("rm -rf /tmp/scratch") == []

    # ── 票 111(A-1)—— 暫存許可止於 repo 邊界 ────────────────────────────
    #
    # `BASH_ALLOWED_TARGETS` 的 `/tmp/` 與 `scratchpad` 兩行,理由欄逐字寫著
    # 「**在 repo 之外**」,而比對只問「路徑成分裡有沒有這個名字」——
    # 於是 repo 內的 `tmp/` 與 `scratchpad/` 一起被當成系統暫存。
    #
    # 票 76 A3 補的是**成分邊界**,沒有補**根錨定**;而 `scanner.py` 的正典
    # 明寫「**兩種錨定,不要合成一種**」,`_target_allowed` 的 docstring
    # **引用了那一段**而只實作了其中一種 —— 引用一份正典不會讓你實作它(F-117)。

    def test_a_repo_local_tmp_is_not_the_system_temp(self):
        """① 正控:`rm -rf tmp/` 的目標解析後落在 repo 裡,**不是**系統暫存。

        這一格是本票最貴的一格:它刪的是 repo 內的一個目錄,
        而 R7 現行放行(2026-09-07 實測)。
        """
        assert gate.unallowed_write_targets("rm -rf tmp/") == ["tmp/"], \
            gate.unallowed_write_targets("rm -rf tmp/")
        msg = gate.bash_write_violation("rm -rf tmp/")
        assert msg and "R7" in msg, "repo 內的 tmp/ 被當成系統暫存放行了:%r" % msg

    def test_a_repo_local_scratchpad_is_not_the_session_scratchpad(self):
        """② 正控:絕對路徑指向 `<repo>/scratchpad/`,以及任意深度的 `scratchpad`。

        `scratchpad` 那一行沒有斜線,所以它是**任意深度**比對 ——
        repo 內任何一層叫 `scratchpad` 的目錄都吃得到那個許可。
        """
        abs_in_repo = str(pathlib.Path(gate.ROOT) / "scratchpad" / "x.py").replace("\\", "/")
        for cmd in ("tee %s" % abs_in_repo, "tee a/b/scratchpad/x.py"):
            msg = gate.bash_write_violation(cmd)
            assert msg and "R7" in msg, "repo 內的 scratchpad 被放行了:%r -> %r" % (cmd, msg)

    def test_the_real_outside_temp_is_still_allowed(self, tmp_path):
        """③ **反控** —— 真正在 repo 之外的暫存必須維持放行。

        誤擋的方向會讓規則被關掉(F-031),而這一格正是 agent 每天在用的那條路。

        ⚠ **兩條斷言都刻意與平台無關**:
        `tempfile.gettempdir()` 在 Linux 是 `/tmp`(放行)、在 Windows 是
        `…\\AppData\\Local\\Temp`(**現行就擋**,因為 `Temp` 不等於 `tmp`)——
        直接斷言它會在兩個平台得到相反的答案。
        **那個 Windows 現況不是本票造成的,本票也不改它**(要不要放行是另一個判準)。
        """
        outside_scratch = str(tmp_path / "claude" / "sess" / "scratchpad" / "x.py").replace("\\", "/")
        assert gate.bash_write_violation("tee /tmp/x.py") is None, "POSIX /tmp/ 被誤擋"
        assert gate.bash_write_violation("tee %s" % outside_scratch) is None, \
            "repo 外的 session scratchpad 被誤擋:%s" % outside_scratch

    def test_an_outside_repo_directory_named_tmp_keeps_its_old_verdict(self, tmp_path):
        """④ **反控**:repo 之外一個恰好叫 `tmp` 的目錄,**依原本 R7 規則判**。

        現行放行(任意深度命中 `/tmp/`),而本票**不動 repo 之外的判定** ——
        本票加的條件只有一個方向:「解析後在 repo 內 ⇒ 不算系統暫存」。
        """
        outside_tmp = str(tmp_path / "not-the-repo" / "tmp" / "x.py").replace("\\", "/")
        assert gate.bash_write_violation("tee %s" % outside_tmp) is None, \
            "repo 外的 tmp 判定被本票改到了:%s" % outside_tmp

    @pytest.mark.parametrize("cmd", [
        "tee .dev/notes.jsonl",
        "tee build/out.tmp",
        "tee __pycache__/x.pyc",
        "tee .cache/x.json",
    ])
    def test_the_in_repo_allowances_are_untouched(self, cmd):
        """**反控**:`BASH_ALLOWED_TARGETS` 裡本來就是**給 repo 內用**的那幾項不受影響。

        少了這一組,「在 repo 內 ⇒ 不許可」會被寫成一條把整份許可表關掉的規則,
        而正控會全綠。
        """
        assert gate.bash_write_violation(cmd) is None, "誤擋:%r" % cmd

    def test_every_allowed_target_is_classified_inside_or_outside(self):
        """**機制,不是紀律**(F-148):許可表新增一項而忘了分類 ⇒ 這條紅。

        分類是「這一項是給 repo 之外用的,還是 repo 之內」。沒有第三種:
        少了這條測試,`OUTSIDE_REPO_ONLY` 就是第二份手工維護的名單,
        而兩份手工名單必分岔(票 29 已經記過同型)。
        """
        keys = set(gate.BASH_ALLOWED_TARGETS)
        outside = set(gate.OUTSIDE_REPO_ONLY)
        assert outside <= keys, "OUTSIDE_REPO_ONLY 有不在許可表裡的項目:%s" % (outside - keys)
        assert gate.OUTSIDE_REPO_ONLY, "分類表是空的 —— 那等於這條規則沒有生效"


class TestStateFileClassification:
    """票 04 — 狀態檔分類。判準是**這個檔案壞掉或消失時,正確行為是什麼**。

    證據消失即失去判定依據,必須 fail-closed;快取消失就重算。
    目錄本身就是分類,不必靠記性維持。
    """

    def test_evidence_files_live_under_dev(self):
        """驗的是**正式**路徑,所以要拿一份沒被隔離 fixture 蓋過的 gate。

        conftest 的 autouse fixture 把證據路徑指到 tmp(票 18:測試不得寫進
        宿主的真實證據檔),它在 setup 時走訪已載入的模組 ——
        **在測試函式內部才載的這一份蓋不到**,正好是這裡要的。

        兩者不衝突,是同一個設計的兩面:平常一律隔離,
        要驗「正式路徑長什麼樣」時自己拿一份乾淨的。
        """
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "gate_unpatched_for_paths", ROOT / ".claude" / "hooks" / "gate.py")
        fresh = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fresh)
        for p in (fresh.PIPELINE, fresh.EXEMPTION_LOG):
            assert "/.dev/" in p.replace("\\", "/"), p

    def test_cache_files_live_under_cache_dir(self):
        assert "/.cache/" in gate.MOUNT_CACHE.replace("\\", "/"), gate.MOUNT_CACHE

    def test_cache_dir_is_ignored_by_version_control(self):
        """問 git,不比對 .gitignore 的字串。

        原本斷言 `"/.cache/" in text` —— 那綁死了**宿主 repo 的寫法**:
        安裝到新專案時 .gitignore 寫的是 `.cache/`(沒有前導斜線),同樣有效,
        測試卻紅。要驗的性質是「這個目錄被版控忽略」,而那件事只有 git 說了算(票 07)。
        """
        rc = subprocess.run(["git", "check-ignore", "-q", ".cache/probe"],
                            cwd=str(ROOT), capture_output=True).returncode
        assert rc == 0, "快取目錄未被版控忽略(git check-ignore 說沒有)"


class TestR3ReadsRedlight:
    """票 06 — R3 的完整斷言:測試檔存在 **且** 有一筆宣告當時實作不存在的紅燈紀錄。

    R3 的原始規格本來就是兩個條件,實作只做了前半,而且沒有東西發現它掉了(F-012)。
    只驗檔案存在的話,一個永遠跑不起來的測試檔也能過關。

    擋得住順手作弊(先寫實作再補測試),擋不住刻意作弊(直接改紀錄檔)——
    後者靠 code review,閘門不假裝能防它。
    """

    @staticmethod
    def _write_log(path, records):
        with io.open(path, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    def test_a_proper_red_then_green_sequence_passes(self, tmp_path, monkeypatch):
        log = tmp_path / "runs.jsonl"
        self._write_log(log, [{"test_file": "tests/test_widget.py", "result": "red",
                               "impl_exists": False, "impl_hash": None}])
        monkeypatch.setattr(gate, "RUN_LOG", str(log))
        assert gate.redlight_missing("widget") is None

    def test_implementation_written_before_the_test_is_blocked(self, tmp_path, monkeypatch):
        """紅燈時實作就已經在了 —— 那不是紅綠燈,是補測試。"""
        log = tmp_path / "runs.jsonl"
        self._write_log(log, [{"test_file": "tests/test_widget.py", "result": "red",
                               "impl_exists": True, "impl_hash": "abc"}])
        monkeypatch.setattr(gate, "RUN_LOG", str(log))
        msg = gate.redlight_missing("widget")
        assert msg and "實作" in msg

    def test_only_green_records_is_blocked(self, tmp_path, monkeypatch):
        log = tmp_path / "runs.jsonl"
        self._write_log(log, [{"test_file": "tests/test_widget.py", "result": "green",
                               "impl_exists": True, "impl_hash": "abc"}])
        monkeypatch.setattr(gate, "RUN_LOG", str(log))
        assert gate.redlight_missing("widget") is not None

    def test_missing_log_is_fail_closed(self, tmp_path, monkeypatch):
        """讀不到就擋,不是讀不到就放行 —— 這是 F-001 的同一個位置,在測試裡釘死。"""
        monkeypatch.setattr(gate, "RUN_LOG", str(tmp_path / "does-not-exist.jsonl"))
        assert gate.redlight_missing("widget") is not None

    def test_malformed_log_is_fail_closed(self, tmp_path, monkeypatch):
        log = tmp_path / "runs.jsonl"
        io.open(log, "w", encoding="utf-8").write("這不是 json\n{壞掉的\n")
        monkeypatch.setattr(gate, "RUN_LOG", str(log))
        assert gate.redlight_missing("widget") is not None

    def test_record_missing_the_impl_exists_field_is_fail_closed(self, tmp_path, monkeypatch):
        """欄位缺漏也算格式不對 —— 不能因為「看起來像紅燈」就放行。"""
        log = tmp_path / "runs.jsonl"
        self._write_log(log, [{"test_file": "tests/test_widget.py", "result": "red"}])
        monkeypatch.setattr(gate, "RUN_LOG", str(log))
        assert gate.redlight_missing("widget") is not None


class TestGateSelfModification:
    """閘門自己受不受閘門管。

    R2 有例外(死鎖):閘門把站別卡住時,修法需要改 gate.py,R2 管到它就把人鎖在外面。
    R3 沒有例外:寫測試不需要先解鎖任何東西,而爆炸半徑最大的程式更該有測試。
    """

    def test_gate_itself_is_exempt_from_stage_rule(self, monkeypatch, tmp_path):
        monkeypatch.setattr(gate, "load_stage", lambda: ("spec", None))
        msg = gate.check(".claude/hooks/gate.py", "x = 1", at_commit=False)
        assert msg is None or "R2" not in msg

    def test_gate_exemption_is_never_silent(self, monkeypatch):
        """靜默的洞比會叫的洞危險(F-011 的教訓)。"""
        monkeypatch.setattr(gate, "load_stage", lambda: ("spec", None))
        note = gate.self_modification_note(".claude/hooks/gate.py")
        assert note is not None
        assert "自我修改豁免" in note and "已記錄" in note

    def test_gate_exemption_is_recorded_with_its_reason(self, monkeypatch, tmp_path):
        """**記帳搬到強制點了,所以這條也跟著搬**(票 08)。

        原本是 `check()` 自己寫,那個副作用讓每一次評估(含跑測試)都記一筆。
        現在 `check()` 把用到的豁免交出來,由強制點寫 —— 保證沒有變弱,
        變的是誰負責寫,以及什麼時候寫。
        """
        log = tmp_path / "gate-exemptions.jsonl"
        monkeypatch.setattr(gate, "EXEMPTION_LOG", str(log))
        monkeypatch.setattr(gate, "load_stage", lambda: ("spec", None))
        used = []
        gate.check(".claude/hooks/gate.py", "x = 1", at_commit=False,
                   exemptions=used)
        gate.log_exemptions(used, verdict=None, at_commit=False, content="x = 1")
        records = [json.loads(l) for l in io.open(log, encoding="utf-8") if l.strip()]
        assert any(r.get("reason") == "gate-self-modification" for r in records), records

    def test_gate_is_still_subject_to_the_test_file_rule(self, monkeypatch):
        """R3 沒有例外。這裡用一個不存在對應測試的假閘門檔驗證。"""
        monkeypatch.setattr(gate, "load_stage", lambda: ("implement", "01"))
        msg = gate.check(".claude/hooks/no_such_gate_helper.py", "x = 1", at_commit=False)
        assert msg is not None and "R3" in msg

    def test_patch_script_gets_no_exemption(self, monkeypatch):
        """豁免對象是閘門自身這個具體清單,不是「.claude 底下的 .py」這個籠統類別。"""
        monkeypatch.setattr(gate, "load_stage", lambda: ("spec", None))
        msg = gate.check(".claude/patches/apply_patches.py", "x = 1", at_commit=False)
        assert msg is not None and "R2" in msg



class TestLegacyNoRedlightList:
    """既有 .py 的「紅燈紀錄」豁免 —— 豁免條件必須是【無法自我服務】的。

    被否決的作法:紅燈紀錄只在「檔案還不存在」時要求。那個豁免條件是
    **agent 隨時可以自己製造的狀態**:先建一個空檔,下一次寫入就成了「既有檔案」,
    自動進入豁免集合。規則等於自帶開關。

    採用的作法:豁免集合 = 一份以【機制上線 commit 的樹】為權威的凍結清單。
    要進去得改那份清單,而清單裡每一項都必須在上線 commit 裡找得到 ——
    這個條件偽造不了,除非改寫歷史。與票宣告式豁免同構:宣告在前,不得在被擋當下新增。

    這份清單只豁免 R3 的**後半**(紅燈紀錄)。前半(對應測試檔須存在)照常適用。
    """

    def test_the_list_is_what_the_generator_would_produce(self):
        """清單必須等於「上線 commit 的樹 ∩ 原始碼 .py」,扣掉已排水的。

        原本寫的是 `len(...) > 50` —— 那斷言的是**宿主 repo 有上百個既有 .py**
        這個事實,不是框架的性質。裝到新專案(五個框架檔)就紅,而那個紅
        與新專案無關,只會教人「這套測試本來就紅」(票 07、F-031)。

        換成這條之後,兩種環境都成立,而且比原本強:它抓得到「手加一筆」
        (超出生成集合)與「清單根本沒生成」(缺一大片且沒有排水證據)。
        """
        go_live = gate.read_go_live()
        out = subprocess.run(["git", "ls-tree", "-r", "--name-only", go_live],
                             cwd=str(ROOT), capture_output=True)
        tree = [l.strip() for l in out.stdout.decode("utf-8", "replace").splitlines()
                if l.strip()]
        expected = {p for p in tree if p.endswith(".py") and gate.is_source_path(p)}
        entries = gate.legacy_no_redlight()

        assert entries <= expected, (
            "清單裡有生成集合以外的項目(只減不增):%s" % sorted(entries - expected))
        undrained = [p for p in sorted(expected - entries)
                     if gate.redlight_missing(pathlib.Path(p).stem) is not None]
        assert not undrained, (
            "這些在上線 commit 的樹裡卻不在清單上,也沒有合格紅燈紀錄可以解釋 ——"
            "清單沒生成完整:%s" % undrained)

    def test_every_entry_existed_in_the_go_live_commit(self):
        """只減不增:新檔案永遠進不去,它不在那個 commit 的樹裡。

        用 git 物件庫判定,不用時間戳 —— 時間可以改,樹不行(除非改寫歷史)。
        """
        missing = [p for p in sorted(gate.legacy_no_redlight())
                   if subprocess.run(
                       ["git", "cat-file", "-e", "%s:%s" % (gate.read_go_live(), p)],
                       cwd=str(ROOT), capture_output=True).returncode != 0]
        assert not missing, (
            "這些項目不在機制上線 commit %s 的樹裡 —— 是後來手加的:\n%s"
            % (gate.read_go_live(), "\n".join(missing)))

    def test_every_entry_is_actually_subject_to_R3(self):
        """清單只能裝「本來會被 R3 要求紅燈」的檔案,裝別的等於偷渡擴大豁免範圍。"""
        stray = [p for p in sorted(gate.legacy_no_redlight())
                 if not (p.endswith(".py") and gate.is_source_path(p))]
        assert not stray, "這些不是 R3 的對象,不該出現在豁免清單:%s" % stray

    def test_no_entry_still_holds_a_qualifying_redlight_record(self):
        """**絆線,不是縮減機制。**

        原本寫成「要排水,債務隨時間縮減」。審查指出那條路徑走不通:
        合格紅燈要求紀錄當下實作不存在,而檔案還在就產不出那種紀錄 ——
        清單因此接近永久。實務上只有「刪掉重寫」會觸發。

        留著它是因為它仍會在**同名撞號**時響:別的模組的紅燈紀錄讓清單裡某一筆
        看起來有了排水資格,那代表 basename 鍵撞到了,需要有人看一眼(ADR 0006)。
        """
        stale = [p for p in sorted(gate.legacy_no_redlight())
                 if gate.redlight_missing(pathlib.Path(p).stem) is None]
        assert not stale, (
            "這些已經有合格紅燈紀錄,應從豁免清單移除(債務要隨時間縮減):%s" % stale)

    def test_a_listed_file_is_exempt_from_the_redlight_requirement(self, fake_repo):
        root, probe = fake_repo
        (root / "legacy.txt").write_text("pkg/thing.py\n", encoding="utf-8")
        assert gate.check(probe, "x = 2") is None

    def test_a_listed_file_is_exempt_from_R3_ENTIRELY_even_without_a_test(self, fake_repo):
        """**語意更新(ADR 0006)**:legacy 清單豁免 R3 **整條**,不只紅燈半。

        測試檔存在半也豁免 —— 否則 121 個檔案 0 個測試的既有 repo,
        每個既有檔案一被編輯就被 R3 第一半擋死,而 legacy 清單救不了。
        這裡刪掉測試檔:列冊的既有檔案**連測試都沒有**,仍該放行。
        """
        root, probe = fake_repo
        (root / "tests" / "test_thing.py").unlink()   # 連測試都沒有
        (root / "legacy.txt").write_text("pkg/thing.py\n", encoding="utf-8")
        assert gate.check(probe, "x = 2") is None, \
            "列冊的既有檔案(無測試)仍被 R3 第一半擋 —— 語意沒改到"

    def test_a_new_file_without_a_test_is_still_blocked(self, fake_repo):
        """新檔案不受影響:不在清單裡、沒有測試 → R3 照擋(整條豁免只給既有碼)。"""
        root, probe = fake_repo
        (root / "tests" / "test_thing.py").unlink()
        (root / "legacy.txt").write_text("# 空清單\n", encoding="utf-8")
        out = gate.check(probe, "x = 2")
        assert out and "R3" in out, "新檔案無測試竟放行(整條豁免漏到新檔):%r" % out

    def test_an_existing_but_unlisted_file_still_needs_a_redlight_record(self, fake_repo):
        """(a) 的洞:建一個空檔就進豁免集合。凍結清單擋住的正是這個。

        樣本是測試自己造的:`pkg/thing.py` 存在、`tests/test_thing.py` 也存在 ——
        舊判準(creating_new)會放行,新判準要求它在清單裡才放行。
        """
        root, probe = fake_repo
        (root / "legacy.txt").write_text("# 空清單\n", encoding="utf-8")
        out = gate.check(probe, "x = 2")
        assert out and "R3/紅燈" in out, \
            "既有但未列冊仍應要求紅燈紀錄,實得:%r" % out

    def test_an_unreadable_list_exempts_nothing(self, fake_repo, monkeypatch):
        """清單本身 fail-closed:讀不到是「沒有任何豁免」,不是「全部豁免」。"""
        root, probe = fake_repo
        monkeypatch.setattr(gate, "LEGACY_LIST", str(root / "gone.txt"))
        out = gate.check(probe, "x = 2")
        assert out and "R3/紅燈" in out, "豁免清單不存在時竟然放行(fail-open):%r" % out

    def test_comments_and_blank_lines_are_not_treated_as_paths(
            self, tmp_path, monkeypatch):
        lst = tmp_path / "legacy.txt"
        lst.write_text("# 產生指令:...\n\npkg/thing.py\n", encoding="utf-8")
        monkeypatch.setattr(gate, "LEGACY_LIST", str(lst))
        assert gate.legacy_no_redlight() == {"pkg/thing.py"}


class TestTheListItselfIsGuarded:
    """審查發現:凍結清單落在 .agents/(非原始碼),沒有任何規則守它 ——
    被 R3 擋下時只要在清單末尾加一行就豁免到手,**完全不必碰 git 歷史**。
    那讓「無法自我服務」這個選 (b) 的唯一理由當場失效,(b) 退化成 (a)。

    「有一條測試會抓到」不算守住:沒有任何機制強制那條測試被跑。
    判定必須跟 R4/R5 同構 —— 進權威層(pre-commit)。
    """

    @staticmethod
    def _a_path_actually_in(tree_sha, root):
        """**執行期查詢**一個真的在那棵樹裡的路徑。

        原本硬寫 `.claude/hooks/gate.py`,註解宣稱「它必然在任何裝了本框架的
        repo 的上線 commit 樹裡」。**那句話是假的**:量化 repo 的 go-live
        (`df8867a`)正是把 `.claude/` 寫進 `.gitignore` 的那個提交,
        所以 gate.py 不在它的樹裡,這條測試在那裡永久紅。

        判錯對象:要的是「一個**在樹裡**的路徑」,拿到的是
        「一個**我以為**在樹裡的路徑」。而「我以為」在別人的 repo 不成立。
        """
        out = subprocess.run(["git", "ls-tree", "-r", "--name-only", tree_sha],
                             cwd=str(root), capture_output=True)
        paths = [l.strip() for l in
                 out.stdout.decode("utf-8", "replace").splitlines() if l.strip()]
        return paths[0] if paths else None

    def test_an_entry_absent_from_the_go_live_tree_is_a_violation(
            self, tmp_path, monkeypatch):
        lst = tmp_path / "legacy.txt"
        # sha 取自本 repo 自己的清單,不寫死 —— 寫死的話換個 repo 就紅(票 07)
        go_live = gate.read_go_live()
        sample = self._a_path_actually_in(go_live, ROOT) if go_live else None
        # **意圖要明說。** 取不到樣本時 `sample` 是 None,寫進清單變成字串
        # "None",而 "None" 碰巧不在任何樹裡 —— 於是測試仍然會紅,
        # 但紅的理由是「湊巧」而不是「我們檢查了」。
        # 靠巧合成立的斷言,下次條件一變就靜默改變意義。
        assert sample, "go-live 樹裡取不到任何路徑 —— 沒有有效樣本,這條測不了"
        lst.write_text("# go-live: %s\n%s\nnot/in/the/tree.py\n"
                       % (go_live, sample), encoding="utf-8")
        monkeypatch.setattr(gate, "LEGACY_LIST", str(lst))
        v = gate.check_legacy_list()
        assert len(v) == 1 and "not/in/the/tree.py" in v[0], v

    def test_it_holds_when_the_gate_itself_is_absent_from_the_tree(
            self, tmp_path, monkeypatch):
        """**正控,直接構造量化的 repo 形狀**:go-live 那棵樹裡**沒有** gate.py。

        不靠宿主 repo 碰巧長什麼樣 —— 那正是原本那條測試壞掉的原因。
        """
        repo = tmp_path / "quantish"
        repo.mkdir()
        for c in ("init -q", "config user.email t@t", "config user.name t"):
            subprocess.run(["git"] + c.split(), cwd=str(repo), capture_output=True)
        (repo / "pkg").mkdir()
        io.open(repo / "pkg" / "thing.py", "w", encoding="utf-8").write("x = 1\n")
        io.open(repo / ".gitignore", "w", encoding="utf-8").write(".claude/\n")
        subprocess.run(["git", "add", "-A"], cwd=str(repo), capture_output=True)
        subprocess.run(["git", "commit", "-qm", "go-live(.claude 被 ignore)"],
                       cwd=str(repo), capture_output=True)
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo),
                             capture_output=True).stdout.decode().strip()
        assert subprocess.run(["git", "cat-file", "-e",
                               "%s:.claude/hooks/gate.py" % sha],
                              cwd=str(repo), capture_output=True).returncode != 0, \
            "測試的前提垮了:gate.py 竟然在這棵樹裡"

        lst = repo / "legacy.txt"
        sample = self._a_path_actually_in(sha, repo)
        assert sample, "構造出來的 go-live 樹是空的 —— 這條測不了"
        io.open(lst, "w", encoding="utf-8").write(
            "# go-live: %s\n%s\n" % (sha, sample))
        monkeypatch.setattr(gate, "LEGACY_LIST", str(lst))
        monkeypatch.setattr(gate, "ROOT", str(repo))
        assert gate.check_legacy_list() == [], "gate.py 不在樹裡的 repo 形狀下誤報"

    def test_a_path_absent_from_that_tree_is_still_named(
            self, tmp_path, monkeypatch):
        """**負控**:同一個 repo 形狀下,不在樹裡的路徑仍要被 R6 點名。

        少了它,「一律回空」也會讓上面那條正控過。
        """
        repo = tmp_path / "quantish2"
        repo.mkdir()
        for c in ("init -q", "config user.email t@t", "config user.name t"):
            subprocess.run(["git"] + c.split(), cwd=str(repo), capture_output=True)
        io.open(repo / "a.py", "w", encoding="utf-8").write("x = 1\n")
        subprocess.run(["git", "add", "-A"], cwd=str(repo), capture_output=True)
        subprocess.run(["git", "commit", "-qm", "base"], cwd=str(repo),
                       capture_output=True)
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo),
                             capture_output=True).stdout.decode().strip()
        lst = repo / "legacy.txt"
        io.open(lst, "w", encoding="utf-8").write(
            "# go-live: %s\na.py\nnever/existed.py\n" % sha)
        monkeypatch.setattr(gate, "LEGACY_LIST", str(lst))
        monkeypatch.setattr(gate, "ROOT", str(repo))
        v = gate.check_legacy_list()
        assert len(v) == 1 and "never/existed.py" in v[0], v

    def test_the_shipped_list_is_clean(self):
        assert gate.check_legacy_list() == []

    def test_the_rule_is_actually_invoked_at_the_authoritative_layer(self, monkeypatch):
        """規則存在但沒人呼叫,就是 F-017 的形狀 —— 在這裡釘死。"""
        monkeypatch.setattr(gate.subprocess, "check_output", lambda *a, **k: b"")
        monkeypatch.setattr(gate, "check_skill_copies", lambda: [])
        monkeypatch.setattr(gate, "check_third_axis_mount", lambda: [])
        monkeypatch.setattr(gate, "check_to_spec_override", lambda: [])
        monkeypatch.setattr(gate, "check_legacy_list", lambda: ["假違規"])
        assert gate.mode_pre_commit() == 1, "pre-commit 沒有呼叫 check_legacy_list"

    def test_an_unreadable_list_is_not_silently_clean(self, tmp_path, monkeypatch):
        monkeypatch.setattr(gate, "LEGACY_LIST", str(tmp_path / "gone.txt"))
        assert gate.check_legacy_list() != [], "清單消失時竟然回報乾淨(fail-open)"


class TestR6SeparatesAMissingCommitFromAMissingPath:
    """票 55 —— R6 把「那棵樹不在」誤報成「這是後來手加的」。

    ## 病灶

    `git cat-file -e <go-live>:<path>` 的**非零退出碼有兩種原因**,而程式折成一種:

    | | 意思 | 舊訊息 | 該說什麼 |
    |---|---|---|---|
    | ① 路徑不在那棵樹裡 | **真違規** | 「新檔案要走紅燈,不是往豁免名單裡加」 | 同左 ✅ |
    | ② 那個 commit **不在這個 repo** | **環境問題**(淺 clone / 歷史被改寫) | **同一句話** | 「go-live commit 不在這個 repo」 |

    ## 為什麼「理由錯」比「不擋」貴

    舊訊息會**主動把人推向刪清單條目** —— 那是讀完之後最合理的下一步。而:

    1. 刪掉之後,**一份本來正確的清單被改壞**
    2. 而 **R6 仍然紅**(樹還是不在)
    3. 於是人會繼續刪,直到清單空掉,**而它從頭到尾都是對的**

    > ### **`fail-closed` 保證的是「擋不擋」,不是「為什麼擋」——
    > ### 而人是照理由行動的,不是照擋不擋行動的。**

    ## 三條缺一不可

    ① 是病灶;② 釘住舊訊息**一字不改**(少了它,一個「一律回新訊息」的實作也會讓 ① 綠);
    ③ 釘住兩者都正常時**不擋**(少了它,一個「一律回違規」的實作會讓 ①② 都綠)。
    """

    def _repo(self, tmp_path, name, body="x = 1\n"):
        """建一個一 commit 的 repo,回 (路徑, sha)。

        ⚠ **`body` 這個參數不是裝飾。** 第一版兩個 repo 用同一份內容、同一個
        commit 訊息、同一個身分建 —— 而 git 是**內容定址**的:
        樹一樣、訊息一樣、時間戳落在同一秒,**兩個「互不相干的 repo」
        算出來的 commit sha 完全相同**。

        > ### **「另一個 repo」不等於「另一個 sha」。**

        於是「拿別的 repo 的 sha 來當找不到的物件」這個構造**當場失效** ——
        而它失效的樣子是**測試綠**(那個 sha 在這裡真的找得到)。
        本類的前提斷言(`cat-file -e` 必須非零)就是為了這個而寫的,
        **它在第一次跑就抓到了**。
        """
        repo = tmp_path / name
        repo.mkdir()
        for c in ("init -q", "config user.email t@t", "config user.name t"):
            subprocess.run(["git"] + c.split(), cwd=str(repo), capture_output=True)
        (repo / "pkg").mkdir()
        io.open(repo / "pkg" / "thing.py", "w", encoding="utf-8").write(body)
        subprocess.run(["git", "add", "-A"], cwd=str(repo), capture_output=True)
        subprocess.run(["git", "commit", "-qm", "go-live " + name],
                       cwd=str(repo), capture_output=True)
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo),
                             capture_output=True).stdout.decode().strip()
        return repo, sha

    def test_a_go_live_commit_absent_from_this_repo_says_so(
            self, tmp_path, monkeypatch):
        """① **病灶本身。**

        **怎麼造出「commit 不在這個 repo」**:建**兩個**互不相干的 repo,
        把 B 的 sha 寫進 A 的清單。那是淺 clone / 歷史改寫之後的真實形狀 ——
        sha 長得完全正常,而那個物件在這裡**不存在**。

        **不用 `"0" * 40`**:git 對全零 sha 有特殊語意(null sha),
        拿它當樣本的話,測到的可能是那個特例而不是本票的情境。
        """
        repo, _sha = self._repo(tmp_path, "here")
        # **內容要不一樣** —— 見 `_repo` 的 docstring:一樣的話兩個 repo 同 sha。
        _elsewhere, foreign = self._repo(tmp_path, "elsewhere", body="y = 2\n")

        assert subprocess.run(["git", "cat-file", "-e", foreign + "^{commit}"],
                              cwd=str(repo), capture_output=True).returncode != 0, \
            "測試的前提垮了:另一個 repo 的 commit 竟然在這裡找得到"

        lst = repo / "legacy.txt"
        io.open(lst, "w", encoding="utf-8").write(
            "# go-live: %s\npkg/thing.py\n" % foreign)
        monkeypatch.setattr(gate, "LEGACY_LIST", str(lst))
        monkeypatch.setattr(gate, "ROOT", str(repo))

        v = gate.check_legacy_list()
        assert v, "go-live commit 不在這個 repo,卻回報乾淨(fail-open)"
        joined = "\n".join(v)
        assert "不在這個 repo" in joined, joined
        assert "淺層 clone" in joined and "--unshallow" in joined, (
            "訊息沒說出修法 —— 票 13 的判準:說得出是哪一個前提沒滿足:%s" % joined)
        assert foreign in joined, "訊息沒帶那個 sha,人沒辦法拿它去 fetch:%s" % joined

        # 🔴 **這一句是本條的重點**:舊訊息會把人推向刪清單。
        assert "清單只減不增" not in joined, (
            "還在說「清單只減不增:新檔案要走紅燈」—— 那句話會讓人去刪一份"
            "本來正確的清單,而刪完之後 R6 仍然紅:%s" % joined)

    def test_a_path_absent_from_a_present_tree_keeps_the_original_message(
            self, tmp_path, monkeypatch):
        """② **反控:commit 在、路徑不在樹裡 → 原訊息一字不改。**

        少了這條,一個「一律回新訊息」的實作也會讓 ① 綠,
        而**真違規會被說成環境問題** —— 方向剛好相反,而且更貴:
        它會讓一個真的往豁免清單裡加東西的人,以為自己只是 clone 淺了。
        """
        repo, sha = self._repo(tmp_path, "here")
        lst = repo / "legacy.txt"
        io.open(lst, "w", encoding="utf-8").write(
            "# go-live: %s\npkg/thing.py\nnever/existed.py\n" % sha)
        monkeypatch.setattr(gate, "LEGACY_LIST", str(lst))
        monkeypatch.setattr(gate, "ROOT", str(repo))

        v = gate.check_legacy_list()
        assert len(v) == 1, v
        assert "never/existed.py" in v[0], v
        assert "不在機制上線 commit" in v[0], v
        assert "清單只減不增:新檔案要走紅燈,不是往豁免名單裡加。" in v[0], (
            "原訊息被改動了 —— 這一條路徑上它是對的,票 55 明訂一字不改:%s" % v[0])
        assert "不在這個 repo" not in v[0], (
            "真違規被說成環境問題 —— 方向反了:%s" % v[0])

    def test_both_present_does_not_block(self, tmp_path, monkeypatch):
        """③ **反控:兩者皆正常 → 不擋。**

        少了這條,一個「一律回違規」的實作會讓 ①② 都綠 ——
        而那會擋下每一個 repo 的每一次 commit,理由還輪流換。
        """
        repo, sha = self._repo(tmp_path, "here")
        lst = repo / "legacy.txt"
        io.open(lst, "w", encoding="utf-8").write(
            "# go-live: %s\npkg/thing.py\n" % sha)
        monkeypatch.setattr(gate, "LEGACY_LIST", str(lst))
        monkeypatch.setattr(gate, "ROOT", str(repo))
        assert gate.check_legacy_list() == [], "一切正常卻擋下"

    def test_the_two_messages_are_told_apart_by_more_than_wording(
            self, tmp_path, monkeypatch):
        """**非空性**:兩條路徑各自產生的訊息,不得只差幾個字。

        少了這條,「兩種原因都說得出來」可以靠**同一句話裡塞兩種可能**滿足
        ——「不在樹裡,或者 commit 不在這個 repo」。
        那種訊息**每一次都對**,而它**每一次都沒有指出是哪一個**,
        於是讀的人仍然得自己查。**一句永遠正確的訊息沒有資訊量。**
        """
        repo, sha = self._repo(tmp_path, "here")
        # **內容要不一樣** —— 見 `_repo` 的 docstring:一樣的話兩個 repo 同 sha。
        _elsewhere, foreign = self._repo(tmp_path, "elsewhere", body="y = 2\n")
        monkeypatch.setattr(gate, "ROOT", str(repo))

        lst = repo / "legacy.txt"
        io.open(lst, "w", encoding="utf-8").write(
            "# go-live: %s\nnever/existed.py\n" % sha)
        monkeypatch.setattr(gate, "LEGACY_LIST", str(lst))
        real_violation = "\n".join(gate.check_legacy_list())

        io.open(lst, "w", encoding="utf-8").write(
            "# go-live: %s\nnever/existed.py\n" % foreign)
        missing_commit = "\n".join(gate.check_legacy_list())

        assert real_violation and missing_commit
        assert real_violation != missing_commit
        # 各自**只**含自己那一半的關鍵字,不含對方的
        assert "清單只減不增" in real_violation and "清單只減不增" not in missing_commit
        assert "不在這個 repo" in missing_commit and "不在這個 repo" not in real_violation


class TestRedlightAcceptsTheSameTestLocationsAsR3:
    """R3 前半接受三個測試檔位置,後半只認 tests/test_X.py ——
    pkg/foo.py 配 pkg/test_foo.py 的佈局會被永久擋死,而且沒有合法解法。
    同一條規則的兩半必須問同一個問題(維度 2 的形狀,只是發生在單一時點內)。
    """

    def test_a_sibling_test_file_can_satisfy_the_redlight_half(
            self, tmp_path, monkeypatch):
        log = tmp_path / "runs.jsonl"
        log.write_text(json.dumps({"test_file": "pkg/test_foo.py", "result": "red",
                                   "impl_exists": False, "impl_hash": None}) + "\n",
                       encoding="utf-8")
        monkeypatch.setattr(gate, "RUN_LOG", str(log))
        assert gate.redlight_missing("foo", ("pkg/test_foo.py",)) is None


class TestGoLiveShaTravelsWithTheList:
    """go-live sha 必須跟它定義的清單住在一起,不能寫死在 gate.py 裡。

    gate.py 是要被照抄到新專案的框架檔;清單與 sha 則綁死這個 repo。
    sha 留在 gate.py 裡的話,照抄過去 `check_legacy_list()` 會拿一個
    **在目標 repo 不存在的 commit** 去驗每一筆,安裝的強制驗證當場失敗 ——
    而那是可攜化票 01 端到端跑一次才會撞到的東西。
    """

    def test_the_sha_is_read_from_the_list_file(self, tmp_path, monkeypatch):
        lst = tmp_path / "legacy.txt"
        lst.write_text("# go-live: deadbeefdeadbeefdeadbeefdeadbeefdeadbeef\n"
                       "macro_audit/classify.py\n", encoding="utf-8")
        monkeypatch.setattr(gate, "LEGACY_LIST", str(lst))
        assert gate.read_go_live() == "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"

    def test_the_sha_line_is_not_mistaken_for_a_path(self, tmp_path, monkeypatch):
        lst = tmp_path / "legacy.txt"
        lst.write_text("# go-live: deadbeef\nmacro_audit/classify.py\n", encoding="utf-8")
        monkeypatch.setattr(gate, "LEGACY_LIST", str(lst))
        assert gate.legacy_no_redlight() == {"macro_audit/classify.py"}

    def test_a_list_without_a_sha_is_a_violation_not_a_pass(self, tmp_path, monkeypatch):
        """讀不到基準點就無從驗證清單 —— fail-closed,不是「沒基準所以都算過」。"""
        lst = tmp_path / "legacy.txt"
        lst.write_text("macro_audit/classify.py\n", encoding="utf-8")
        monkeypatch.setattr(gate, "LEGACY_LIST", str(lst))
        v = gate.check_legacy_list()
        assert v and "go-live" in v[0], v

    def test_the_shipped_list_carries_its_own_sha(self):
        assert gate.read_go_live(), "正式清單沒有帶 go-live sha,照抄到新專案會壞"


class TestRulesAreEnumeratedFromTheDefinition:
    """驗收條件不得寫死條數。

    「五條規則各擋一次」在寫下的當下已經是六條 —— 任何寫死數量的驗收條件,
    下次加規則時不會有人記得改,而漏掉的那條不會有任何東西出聲。
    清單必須從規則定義本身列舉。
    """

    def test_a_new_rule_code_is_discovered_without_touching_any_list(self, tmp_path):
        """機制的真正斷言:餵一條**不存在的**規則進去,它必須被列出來。

        拿現有的 R1–R6 當斷言的話,一份硬編碼清單也會綠 ——
        那是套套邏輯的第三種形狀(斷言與現況重合,F-032)。
        """
        fake = tmp_path / "fake_gate.py"
        fake.write_text('msg = "[R99] 這是一條新規則"\n'
                        'other = "[R100/子類] 帶子類的也算"\n', encoding="utf-8")
        codes = gate.rule_codes(str(fake))
        assert codes == {"R99", "R100"}, codes

    def test_the_shipped_gate_enumerates_all_of_its_rules(self):
        codes = gate.rule_codes()
        assert {"R1", "R2", "R3", "R4", "R5", "R6"} <= codes, codes

    def test_every_rule_has_a_scenario_that_actually_triggers_it(self):
        """新增一條規則而沒有對應實測 —— 這裡會紅。

        這是「驗收條件會自己長大」的實作點:清單來自定義,對照表來自實測腳本,
        兩者的差集必須為空。差集不為空代表有規則從來沒被證明擋得住。
        """
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "verify_gates_under_test",
            ROOT / ".claude" / "portable" / "verify_gates.py")
        vg = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vg)
        missing = gate.rule_codes() - set(vg.SCENARIOS)
        assert not missing, (
            "這些規則沒有任何實測會觸發它們:%s —— "
            "規則存在但沒被證明擋得住,跟沒有規則的差別只在讀碼的人心裡。"
            % sorted(missing))


class TestMirrorMissingIsAViolation:
    """鏡像少了東西,是 R4 最典型的破法 —— 而它原本被靜默跳過。

    原碼:`if not os.path.exists(src) or not os.path.exists(m): continue`
    —— 兩邊有任何一邊缺檔就跳過。於是 R4 只驗得出「內容不同」,
    驗不出「東西不見了」;而在硬連結/symlink 佈局下內容根本不可能不同(票 10)。
    兩層疊起來,R4 在實務上是空的。

    由票 02 的機器列舉實測抓到:六條規則裡只有 R4 沒擋下自己的情境。
    """

    @staticmethod
    def _layout(tmp_path):
        canon = tmp_path / "canon"
        (canon / "tdd").mkdir(parents=True)
        (canon / "tdd" / "SKILL.md").write_text("內容", encoding="utf-8")
        mirror = tmp_path / "mirror"
        (mirror / "tdd").mkdir(parents=True)
        (mirror / "tdd" / "SKILL.md").write_text("內容", encoding="utf-8")
        return canon, mirror

    def test_identical_layout_is_clean(self, tmp_path):
        canon, mirror = self._layout(tmp_path)
        assert gate.skill_mirror_violations(str(canon), [str(mirror)]) == []

    def test_a_missing_file_in_the_mirror_is_a_violation(self, tmp_path):
        canon, mirror = self._layout(tmp_path)
        (mirror / "tdd" / "SKILL.md").unlink()
        v = gate.skill_mirror_violations(str(canon), [str(mirror)])
        assert v and "R4" in v[0], "鏡像少了 SKILL.md 卻沒被判違規:%s" % v

    def test_a_missing_directory_in_the_mirror_is_a_violation(self, tmp_path):
        canon, mirror = self._layout(tmp_path)
        shutil.rmtree(str(mirror / "tdd"))
        v = gate.skill_mirror_violations(str(canon), [str(mirror)])
        assert v and "R4" in v[0], "鏡像整個少了一個 skill 卻沒被判違規:%s" % v

    def test_an_extra_skill_in_the_mirror_is_a_violation(self, tmp_path):
        """反方向:鏡像有而正典沒有 —— 正典被刪、鏡像留著舊的,同樣是不一致。"""
        canon, mirror = self._layout(tmp_path)
        (mirror / "ghost").mkdir()
        (mirror / "ghost" / "SKILL.md").write_text("孤兒", encoding="utf-8")
        v = gate.skill_mirror_violations(str(canon), [str(mirror)])
        assert v and "R4" in v[0], "鏡像多出一個正典沒有的 skill 卻沒被判違規:%s" % v

    def test_a_mirror_that_does_not_exist_at_all_is_not_a_violation(self, tmp_path):
        """鏡像整個沒建起來不是 drift —— 那是還沒裝,由安裝流程負責,不是 R4。"""
        canon, _ = self._layout(tmp_path)
        assert gate.skill_mirror_violations(
            str(canon), [str(tmp_path / "never-created")]) == []


class TestAuthoritativeLayerDetection:
    """權威層沒裝時要有東西叫。

    `.git/hooks/` 依 git 設計不進版控,clone 出來的副本上權威層不存在,
    而且**完全靜默**:前哨照跑、測試照綠,gate.py 甚至還在訊息裡宣稱
    「繞過前哨仍會在 commit 被擋」—— 那句話當場是假的。
    F-009 的最終形式:規則存在,但整層沒被部署。

    只驗未安裝路徑:已安裝路徑就是本機現況,測它等於測環境(接縫 S3)。

    **偵測器自己適用維度 4**:它會不會被同一個「沒裝」略過?
    會 —— clone 下來直接手動 commit 的人,前哨與測試都碰不到他。
    這個缺口關不掉(git 刻意不讓 clone 自動執行任何東西),
    所以實作不得假裝關掉了:涵蓋範圍必須寫在訊息裡,票 05 的 ADR 才有東西可引。
    """

    @staticmethod
    def _repo(tmp_path, hook_body=None, hooks_dir=".git/hooks"):
        (tmp_path / ".git").mkdir(exist_ok=True)
        if hook_body is not None:
            d = tmp_path / hooks_dir.replace("/", os.sep if False else "/")
            d.mkdir(parents=True, exist_ok=True)
            (d / "pre-commit").write_text(hook_body, encoding="utf-8")
        return tmp_path

    def test_no_hook_at_all_is_not_installed(self, tmp_path):
        installed, detail = gate.authoritative_layer(str(self._repo(tmp_path)))
        assert installed is False
        assert "pre-commit" in detail

    def test_a_hook_that_does_not_call_the_gate_is_not_installed(self, tmp_path):
        """別人的 hook 佔著位子 —— 檔案在,但它不呼叫閘門。

        只驗「檔案存不存在」的話這種情況會判成已安裝,而那正是最容易發生的:
        專案本來就有自己的 pre-commit。
        """
        root = self._repo(tmp_path, "#!/bin/sh\nnpm run lint\n")
        installed, detail = gate.authoritative_layer(str(root))
        assert installed is False
        assert "gate.py" in detail

    def test_a_hook_that_calls_the_gate_is_installed(self, tmp_path):
        """正控。**兩段都接**才算裝好 —— 票 76(B5)把「已安裝」的語意從
        「六站段在」收緊為「hook 契約完整(leak_scan + gate.py --pre-commit)」,
        本 fixture 的 hook 因此與 install.py 的 HOOK 同形。
        只有 gate 段的 hook 現在判未安裝,由
        TestAuthorityLayerIsWired.test_a_hook_missing_the_leak_stage_is_not_installed 釘住。
        """
        root = self._repo(
            tmp_path,
            '#!/bin/sh\nroot="$(git rev-parse --show-toplevel)"\n'
            'python "$root/.claude/portable/leak_scan.py" --staged || exit 1\n'
            'exec python "$root/.claude/hooks/gate.py" --pre-commit\n')
        installed, _ = gate.authoritative_layer(str(root))
        assert installed is True

    def test_the_notice_names_the_gap_it_cannot_close(self, tmp_path):
        """偵測器涵蓋不到「clone 下來直接手動 commit 的人」。

        訊息不得只說「沒裝,請裝」—— 那讀起來像裝了就全部關上了。
        已知關不掉的部分要出現在訊息裡。
        """
        _, detail = gate.authoritative_layer(str(self._repo(tmp_path)))
        notice = gate.not_installed_notice(detail)
        assert "手動" in notice or "人工" in notice, notice
        assert "關不掉" in notice, "沒說那個缺口關不掉,讀起來像裝了就全部關上了"

    def test_the_sentinel_stops_claiming_commit_will_catch_it(self, tmp_path, monkeypatch):
        """前哨的擋下訊息原本無條件宣稱「繞過前哨仍會在 commit 被擋」。

        權威層不在時那是**假的**,而且是最糟的一種假:它讓人以為還有第二道。
        """
        monkeypatch.setattr(gate, "authoritative_layer", lambda root=None: (False, "沒裝"))
        msg = gate.sentinel_footer()
        assert "仍會在 commit 被擋" not in msg
        assert "沒裝" in msg or "未安裝" in msg

    def test_the_sentinel_still_says_so_when_it_is_true(self, monkeypatch):
        monkeypatch.setattr(gate, "authoritative_layer", lambda root=None: (True, "裝好了"))
        assert "commit" in gate.sentinel_footer()


# ─────────────────────────────────────────────────────────────────────────────
# R3 紅燈半的判定對象 —— 「檔案存不存在」 vs 「實作寫了沒」
#
# 由來(2026-08-12 實測):`redlight_missing("gate")` 對 gate.py 永遠不合格,
# 而 `redlight_missing("edit_result")` 在同一次執行、同一份紀錄檔下合格。
# 差別只在 find_implementation 找不找得到實作檔:
#
#   規則要問的是「**這個實作**寫之前,測試紅過嗎」
#   它量的是「**這個檔案**當時存不存在」
#
# 新檔案兩者重合;既有檔案永遠分岔 —— 於是每一支既有 .py 的紅燈先行
# **在機制上寫不出來**,而唯一出口是 legacy 豁免清單,也就是把 R3 從
# 最需要它的檔案上整條移開。這與 F-046 是同一個形狀(fail-closed 的方向對了,
# 判定的對象錯了),同一輪撞到第二次。
#
# 修法:紅燈紀錄宣告的 impl_hash 若等於**這支檔案在 HEAD 的內容**,
# 那就是「對著改動前的碼紅過」= 既有檔案的紅燈先行。
# 錨定 HEAD 而不是磁碟現況,是因為判準必須**時點不變**:
# 前哨評估時檔案還沒被寫,提交時已經被寫,而 HEAD 在這兩個時點都沒動。
# ─────────────────────────────────────────────────────────────────────────────

class TestRedlightJudgesTheImplementationNotTheFile:

    @pytest.fixture()
    def repo(self, tmp_path, monkeypatch):
        """真的 git repo —— HEAD 錨點只能對著真的物件庫驗。"""
        def git(*a):
            return subprocess.run(["git"] + list(a), cwd=str(tmp_path),
                                  capture_output=True)
        git("init", "-q")
        git("config", "user.email", "t@t")
        git("config", "user.name", "t")
        (tmp_path / "pkg").mkdir()
        io.open(tmp_path / "pkg" / "thing.py", "w", encoding="utf-8",
                newline="\n").write("def f():\n    return 1\n")
        (tmp_path / "tests").mkdir()
        io.open(tmp_path / "tests" / "test_thing.py", "w",
                encoding="utf-8").write("x\n")
        git("add", "-A")
        git("commit", "-qm", "go-live")
        monkeypatch.setattr(gate, "ROOT", str(tmp_path))
        monkeypatch.setattr(gate, "RUN_LOG", str(tmp_path / ".dev" / "test-runs.jsonl"))
        monkeypatch.chdir(tmp_path)
        return tmp_path

    def _log(self, repo, *recs):
        d = repo / ".dev"
        d.mkdir(exist_ok=True)
        with io.open(d / "test-runs.jsonl", "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    def _head_hash(self, repo):
        import hashlib
        blob = subprocess.run(["git", "cat-file", "blob", "HEAD:pkg/thing.py"],
                              cwd=str(repo), capture_output=True).stdout
        norm = blob.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        return hashlib.sha256(norm).hexdigest()

    def _red(self, **kw):
        rec = {"test_file": "tests/test_thing.py", "result": "red",
               "failed_tests": ["test_a"], "impl_file": "pkg/thing.py",
               "impl_exists": True, "impl_hash": None, "ticket_id": "07"}
        rec.update(kw)
        return rec

    # ── 正控 ──────────────────────────────────────────────────────────────

    def test_a_red_against_the_head_version_unlocks_an_existing_file(self, repo):
        """**本單元的主張**:既有檔案第一次做得到紅燈先行。

        當前票有一條紅燈,而且它是對著**改動前的碼**紅的 -> 放行。
        """
        self._log(repo, self._red(impl_hash=self._head_hash(repo)))
        assert gate.redlight_missing("thing", impl_rel="pkg/thing.py",
                                     ticket="07") is None

    def test_a_new_file_redlight_still_passes(self, repo):
        """舊行為不得回歸:實作不存在時紅過的紀錄照樣算數。"""
        self._log(repo, self._red(impl_file=None, impl_exists=False, impl_hash=None))
        assert gate.redlight_missing("thing", impl_rel="pkg/thing.py",
                                     ticket="07") is None

    # ── 負控 ──────────────────────────────────────────────────────────────

    def test_no_redlight_under_the_current_ticket_is_blocked(self, repo):
        self._log(repo)
        assert gate.redlight_missing("thing", impl_rel="pkg/thing.py",
                                     ticket="07") is not None

    def test_only_an_older_tickets_redlight_is_blocked(self, repo):
        """**時效**:一筆舊票的紅燈不得永久解鎖這支檔案。

        少了這條,「impl_hash 與 HEAD 相同」單獨用會把方向從「永遠不合格」
        翻成「永遠合格」—— 只要檔案自那次紅燈後沒被提交過就一直成立。
        每張票要有自己的紅燈。
        """
        self._log(repo, self._red(ticket_id="06", impl_hash=self._head_hash(repo)))
        assert gate.redlight_missing("thing", impl_rel="pkg/thing.py",
                                     ticket="07") is not None, \
            "舊票的紅燈解鎖了當前票的修改"

    def test_a_new_file_without_any_redlight_is_blocked(self, repo):
        self._log(repo, self._red(result="green", impl_exists=False, impl_hash=None))
        assert gate.redlight_missing("thing", impl_rel="pkg/thing.py",
                                     ticket="07") is not None

    def test_a_red_against_an_already_modified_implementation_is_blocked(self, repo):
        """紅燈發生在實作寫完之後 -> 不是紅燈先行。

        這是本修法唯一可能被拿來自我服務的路徑:先寫實作、再跑紅燈。
        hash 錨在 HEAD,所以那種紀錄的 impl_hash 對不上,擋。
        """
        self._log(repo, self._red(impl_hash="0" * 64))
        assert gate.redlight_missing("thing", impl_rel="pkg/thing.py",
                                     ticket="07") is not None

    def test_an_untracked_implementation_falls_back_to_existence(self, repo):
        """檔案不在 HEAD(新建、未提交)-> 只認 impl_exists=False 那條路。"""
        io.open(repo / "pkg" / "fresh.py", "w", encoding="utf-8").write("x = 1\n")
        self._log(repo, self._red(test_file="tests/test_fresh.py",
                                  impl_file="pkg/fresh.py", impl_hash="a" * 64))
        assert gate.redlight_missing("fresh", impl_rel="pkg/fresh.py",
                                     ticket="07") is not None

    # ── 接線 ──────────────────────────────────────────────────────────────

    def test_check_actually_passes_the_ticket_and_path_through(self):
        """漏傳參數會靜默走回寬鬆分支 —— 接線要測(F-044)。"""
        src = io.open(ROOT / ".claude" / "hooks" / "gate.py", encoding="utf-8").read()
        assert "impl_rel=" in src and "ticket=ticket" in src, \
            "check() 沒有把實作路徑與當前票傳進 redlight_missing"


# ─────────────────────────────────────────────────────────────────────────────
# 票 08 —— 豁免帳本記的是「評估事件」,不是「寫入」
#
# 實測:19 筆 gate-self-modification,而 gate.py 對 HEAD 位元組不變。
# 原因是 log_exemption() 在 check() 裡、在**判決之前**被呼叫:被擋下的嘗試
# 照樣記,而且 **check() 有副作用** —— 跑一次測試就多一筆(測試自己會呼叫它)。
#
# ADR 0004 的「某一輪十筆就是把後門當日常通道」假設一筆 = 一次修改。
# 一筆其實 = 一次評估,所以那個門檻的刻度是錯的。
# 先補欄位而不動記錄單位,只會讓刻度錯誤的訊號看起來更嚴謹(F-031)。
# ─────────────────────────────────────────────────────────────────────────────

class TestTheLedgerRecordsWritesNotEvaluations:

    @pytest.fixture()
    def led(self, tmp_path, monkeypatch):
        p = tmp_path / "gate-exemptions.jsonl"
        monkeypatch.setattr(gate, "EXEMPTION_LOG", str(p))
        return p

    def _rows(self, led):
        if not led.exists():
            return []
        return [json.loads(l) for l in io.open(str(led), encoding="utf-8")
                if l.strip()]

    def test_check_is_pure_and_writes_nothing(self, led, monkeypatch):
        """**判定函式不得有副作用。**

        那個副作用正是「跑一次測試就多一筆」的來源:測試呼叫 check() 是為了
        問它的判斷,不是因為有人要寫檔案。記錄屬於強制點,不屬於判定。
        """
        monkeypatch.setattr(gate, "load_stage", lambda: ("implement", "08"))
        gate.check(".claude/hooks/gate.py", "x = 1")
        gate.check(".claude/hooks/gate.py", "x = 2", at_commit=True)
        assert self._rows(led) == [], \
            "check() 仍在寫帳本 —— 每一次評估都被記成一次豁免"

    def test_a_granted_exemption_is_recorded_at_the_enforcement_point(
            self, led, monkeypatch):
        ex = []
        monkeypatch.setattr(gate, "load_stage", lambda: ("implement", "08"))
        gate.check(".claude/hooks/gate.py", "x = 1", exemptions=ex)
        assert ex, "check() 沒有把用到的豁免交出來"
        assert ex[0]["reason"] == "gate-self-modification"

    def test_a_blocked_attempt_is_not_counted_as_granted(self, led, monkeypatch):
        """豁免只有在寫入**真的成立**時才算被用掉。

        被 R3 擋下的嘗試不該與「後門真的被走了一次」記成同一件事 ——
        ADR 0004 的門檻只算 granted。
        """
        rec = gate.exemption_record(
            {"file": ".claude/hooks/gate.py", "module": "gate",
             "reason": "gate-self-modification", "declared_in": "x"},
            verdict="[R3/紅燈] 擋", at_commit=False, stage="implement",
            ticket="08", content=None)
        assert rec["outcome"] == "blocked"
        assert rec["blocked_by"] == "R3"

    def test_the_record_carries_the_new_fields(self, led, monkeypatch, tmp_path):
        rec = gate.exemption_record(
            {"file": ".claude/hooks/gate.py", "module": "gate",
             "reason": "gate-self-modification", "declared_in": "x"},
            verdict=None, at_commit=False, stage="implement", ticket="08",
            content=None)
        for f in ("ts", "stage", "ticket", "outcome", "content_hash",
                  "result_hash", "changes_bytes", "at_commit"):
            assert f in rec, "帳本缺欄位 %s:%r" % (f, rec)
        assert rec["outcome"] == "granted"
        assert rec["stage"] == "implement" and rec["ticket"] == "08"

    def test_a_write_that_changes_nothing_says_so(self, led, monkeypatch, tmp_path):
        """**這是本票的原始問題。** 19 筆豁免、零位元組變更,
        帳本必須自己講得出這件事,而不是靠事後推論。"""
        monkeypatch.setattr(gate, "ROOT", str(tmp_path))
        io.open(tmp_path / "same.py", "w", encoding="utf-8",
                newline="\n").write("x = 1\n")
        rec = gate.exemption_record(
            {"file": "same.py", "module": "same", "reason": "gate-self-modification",
             "declared_in": "x"},
            verdict=None, at_commit=False, stage="implement", ticket="08",
            content="x = 1\n")
        assert rec["changes_bytes"] is False, rec
        assert rec["content_hash"] == rec["result_hash"]

    def test_a_write_that_does_change_bytes_says_so(self, led, monkeypatch, tmp_path):
        """反控:真的改了東西要記成 True —— 少了它,「一律 False」也會讓上面那條過。"""
        monkeypatch.setattr(gate, "ROOT", str(tmp_path))
        io.open(tmp_path / "diff.py", "w", encoding="utf-8",
                newline="\n").write("x = 1\n")
        rec = gate.exemption_record(
            {"file": "diff.py", "module": "diff", "reason": "gate-self-modification",
             "declared_in": "x"},
            verdict=None, at_commit=False, stage="implement", ticket="08",
            content="x = 2\n")
        assert rec["changes_bytes"] is True, rec
        assert rec["content_hash"] != rec["result_hash"]

    def test_the_record_says_which_tool_it_came_from(self, led, monkeypatch,
                                                     tmp_path):
        """**gate.py 不看 tool_name** —— 擋住 Read 的只有 settings.json 的 matcher。

        判定保持 fail-closed(有東西進來就判)是對的,不改成白名單。
        但帳本必須說得出這一筆是什麼工具來的,否則「有幾筆」又變成一個
        解釋不了的數字 —— 那正是這張票要修的東西。
        """
        rec = gate.exemption_record(
            {"file": ".claude/hooks/gate.py", "module": "gate",
             "reason": "gate-self-modification", "declared_in": "x"},
            verdict=None, at_commit=False, stage="implement", ticket="08",
            content=None, tool="Read")
        assert rec["tool"] == "Read"

    def test_an_unknown_result_is_none_not_false(self, led, monkeypatch, tmp_path):
        """算不出結果(提交時、anchor 套不上)-> None,**不是 False**。

        None 是「不知道有沒有變」,False 是「確定沒變」。把前者寫成後者,
        對帳時會看到一串「都沒改」而其實是「都不知道」。
        """
        monkeypatch.setattr(gate, "ROOT", str(tmp_path))
        io.open(tmp_path / "u.py", "w", encoding="utf-8", newline="\n").write("x\n")
        rec = gate.exemption_record(
            {"file": "u.py", "module": "u", "reason": "gate-self-modification",
             "declared_in": "x"},
            verdict=None, at_commit=True, stage="review", ticket=None, content=None)
        assert rec["changes_bytes"] is None and rec["result_hash"] is None, rec


class TestTheSuiteItselfLeavesNoTrace:
    """整輪測試跑完,正式帳本不得增加任何一筆 —— 這是票 08 的驗收條件之一。

    這條測的是**本測試檔以外**的東西:任何一條測試若在正式帳本留下痕跡,
    帳本就再也回答不了「有幾次真的走了後門」。
    """

    def test_the_real_ledger_is_untouched_by_calling_check(self, monkeypatch):
        real = pathlib.Path(gate.EXEMPTION_LOG)
        before = len(io.open(str(real), encoding="utf-8").readlines()) \
            if real.exists() else 0
        monkeypatch.setattr(gate, "load_stage", lambda: ("implement", "08"))
        for _ in range(3):
            gate.check(".claude/hooks/gate.py", "x = 1")
        after = len(io.open(str(real), encoding="utf-8").readlines()) \
            if real.exists() else 0
        assert after == before, "呼叫 check() 污染了正式帳本(%d -> %d)" % (before, after)


# ─────────────────────────────────────────────────────────────────────────────
# R3 × provenance —— 同步來的成品,紅燈責任在上游
#
# 下游 repo 收到 sync 帶進來的實作時,R3 要求本地紅燈紀錄,而**紅綠燈迴圈在上游**:
# 下游拿到的是成品,它從來沒有機會讓那些測試在實作不存在時紅過。
# legacy 名單只減不增,正確地不是出路(那是給機制上線前的既有碼,不是給新收到的成品)。
#
# 判準:**與上游那個 commit 的物件逐位元組相同 ⇒ 紅燈責任在上游。**
#
# **provenance 是控制,不是證據,所以不得可自助。**
# 驗證一律對到上游的 git 物件(`git show <commit>:<path>` 取內容自己算 hash),
# **不採信 provenance 檔案裡宣稱的 hash** —— 那個欄位是給人看的,不是判定依據。
# 手寫一筆 provenance 造不出一個上游沒有的 blob,所以偽造需要改上游,不是改本地檔案。
# ─────────────────────────────────────────────────────────────────────────────

class TestR3AcceptsUpstreamProvenance:

    @pytest.fixture()
    def world(self, tmp_path, monkeypatch):
        """上游(框架)與下游(已裝 repo),兩個真的 git repo。

        上游必須是真的 git 物件庫 —— 判定要對到 `git show`,
        用假的字串替身會讓「偽造不了」這個性質整條測不到。
        """
        up, down = tmp_path / "up", tmp_path / "down"
        for r in (up, down):
            r.mkdir()
            for c in ("init -q", "config user.email t@t", "config user.name t"):
                subprocess.run(["git"] + c.split(), cwd=str(r), capture_output=True)

        (up / "pkg").mkdir()
        io.open(up / "pkg" / "thing.py", "w", encoding="utf-8",
                newline="\n").write("def f():\n    return 1\n")
        subprocess.run(["git", "add", "-A"], cwd=str(up), capture_output=True)
        subprocess.run(["git", "commit", "-qm", "up"], cwd=str(up),
                       capture_output=True)
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(up),
                             capture_output=True).stdout.decode().strip()

        (down / "pkg").mkdir()
        (down / "tests").mkdir()
        io.open(down / "tests" / "test_thing.py", "w",
                encoding="utf-8").write("x = 1\n")
        monkeypatch.setattr(gate, "ROOT", str(down))
        monkeypatch.setattr(gate, "RUN_LOG", str(down / ".dev" / "test-runs.jsonl"))
        monkeypatch.setattr(gate, "PROVENANCE", str(down / ".dev" / "provenance.jsonl"))
        pointer = tmp_path / "upstream-roots.txt"
        io.open(pointer, "w", encoding="utf-8", newline="\n").write(
            "UPSTREAM_ROOT=%s\n" % str(up).replace("\\", "/"))
        monkeypatch.setattr(gate, "UPSTREAM_ROOTS", str(pointer))
        monkeypatch.setattr(gate, "EXEMPTION_LOG",
                            str(down / ".dev" / "gate-exemptions.jsonl"))
        monkeypatch.setattr(gate, "load_stage", lambda: ("implement", "11"))
        monkeypatch.chdir(down)
        return up, down, sha

    def _sync_in(self, down, text="def f():\n    return 1\n"):
        io.open(down / "pkg" / "thing.py", "w", encoding="utf-8",
                newline="\n").write(text)

    def _prov(self, down, **kw):
        rec = {"path": "pkg/thing.py", "upstream_path": "pkg/thing.py"}
        rec.pop("upstream_root", None)
        rec.update(kw)
        d = down / ".dev"
        d.mkdir(exist_ok=True)
        with io.open(d / "provenance.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # ── 正控 ──────────────────────────────────────────────────────────────

    def test_a_file_matching_the_upstream_object_needs_no_local_redlight(self, world):
        """**本節的主張**:內容與上游該 commit 的物件相同 -> R3 紅燈半不適用。"""
        up, down, sha = world
        self._sync_in(down)
        self._prov(down, upstream_commit=sha)
        msg = gate.check("pkg/thing.py", "def f():\n    return 2\n")
        assert not (msg and "R3/紅燈" in msg), msg

    def test_the_exemption_is_collected_with_its_own_reason(self, world):
        """豁免要逐筆記帳,而且要與 gate-self 分得開 ——
        混在一起對帳時又會得到一個解釋不了的數字(票 08)。

        斷言的是 `check()` 收進 bucket,不是它寫檔:票 08 之後判定是純函式,
        寫帳本屬於強制點(只有那裡知道「真的有人要寫」)。
        """
        up, down, sha = world
        self._sync_in(down)
        self._prov(down, upstream_commit=sha)
        used = []
        gate.check("pkg/thing.py", "def f():\n    return 2\n", exemptions=used)
        assert any(e.get("reason") == "upstream-provenance" for e in used), used

    def test_the_judgement_stays_pure(self, world):
        """provenance 這條路徑不得把副作用帶回 `check()` —— 票 08 剛拆掉的東西。"""
        up, down, sha = world
        self._sync_in(down)
        self._prov(down, upstream_commit=sha)
        ledger = down / ".dev" / "gate-exemptions.jsonl"
        before = ledger.exists() and len(io.open(str(ledger), encoding="utf-8").readlines())
        gate.check("pkg/thing.py", "def f():\n    return 2\n")
        after = ledger.exists() and len(io.open(str(ledger), encoding="utf-8").readlines())
        assert after == before, "check() 又開始寫帳本了(票 08 的回歸)"

    # ── 負控:自助偽造的每一條路 ──────────────────────────────────────────

    def test_a_hand_written_provenance_for_a_local_file_is_refused(self, world):
        """**必備負控**:自己寫一筆 provenance 給一個上游沒有的新檔案 -> 擋。

        手寫 provenance 造不出一個上游沒有的 blob;`git show` 直接失敗。
        偽造要改上游,不是改本地檔案 —— 這就是「不得可自助」的意思。
        """
        up, down, sha = world
        io.open(down / "pkg" / "mine.py", "w", encoding="utf-8",
                newline="\n").write("def mine():\n    return 9\n")
        io.open(down / "tests" / "test_mine.py", "w",
                encoding="utf-8").write("x = 1\n")
        self._prov(down, path="pkg/mine.py", upstream_path="pkg/mine.py",
                   upstream_commit=sha)
        msg = gate.check("pkg/mine.py", "def mine():\n    return 8\n")
        assert msg and "R3" in msg, "手寫 provenance 就換到了 R3 豁免:%r" % msg

    def test_a_claimed_hash_is_not_trusted(self, world):
        """**判定不得只驗 provenance 裡宣稱的 hash。**

        這筆紀錄宣稱的 hash 與本地檔案完全相符,但上游那個物件的內容不同 ——
        採信宣稱值的實作會放行,對到 git 物件的實作會擋。
        兩種實作在別的測試上表現一樣,只有這條分得開它們。
        """
        up, down, sha = world
        self._sync_in(down, "def f():\n    return 999\n")     # 與上游不同
        local = hashlib.sha256(b"def f():\n    return 999\n").hexdigest()
        # 連 upstream_root 都一併塞進紀錄 —— 判定必須忽略它,改讀指標檔。
        self._prov(down, upstream_root=str(up), upstream_commit=sha,
                   content_hash=local)
        msg = gate.check("pkg/thing.py", "def f():\n    return 998\n")
        assert msg and "R3" in msg, "採信了 provenance 自己宣稱的 hash:%r" % msg

    def test_content_that_drifted_from_upstream_is_refused(self, world):
        """本地被改過 -> 不再是「上游的成品」-> 紅燈責任回到本地。"""
        up, down, sha = world
        self._sync_in(down, "def f():\n    return 1\n# 本地加的\n")
        self._prov(down, upstream_commit=sha)
        msg = gate.check("pkg/thing.py", "def f():\n    return 3\n")
        assert msg and "R3" in msg, msg

    def test_an_unreachable_upstream_is_refused(self, world):
        """上游問不到 -> **fail-closed**。問不到不等於相同。"""
        up, down, sha = world
        self._sync_in(down)
        io.open(down.parent / "upstream-roots.txt", "w", encoding="utf-8",
                newline="\n").write("UPSTREAM_ROOT=%s\n"
                                    % str(down / "no_such_repo").replace("\\", "/"))
        self._prov(down, upstream_commit=sha)
        msg = gate.check("pkg/thing.py", "def f():\n    return 2\n")
        assert msg and "R3" in msg, msg

    def test_no_provenance_at_all_is_refused(self, world):
        up, down, sha = world
        self._sync_in(down)
        msg = gate.check("pkg/thing.py", "def f():\n    return 2\n")
        assert msg and "R3" in msg, msg

    # ── 上游位置住在指標檔,不住在 jsonl ────────────────────────────────

    def test_a_missing_pointer_file_refuses(self, world, monkeypatch):
        """指標檔缺失 -> 沒有上游可查 -> **fail-closed**。

        位置屬於**本機設定**,不屬於版控:寫進 jsonl 會把使用者的目錄結構
        跟著 commit 送出去(去識別化),而且那個欄位一旦可寫,
        指向一個自己控制的 repo 就能造出任意「上游物件」—— 控制就不再是控制。
        """
        up, down, sha = world
        self._sync_in(down)
        self._prov(down, upstream_commit=sha)
        monkeypatch.setattr(gate, "UPSTREAM_ROOTS", str(down / "nope.txt"))
        msg = gate.check("pkg/thing.py", "def f():\n    return 2\n")
        assert msg and "R3" in msg, msg

    def test_a_malformed_pointer_file_refuses(self, world, monkeypatch):
        """認不得的行 -> 整份當壞掉 -> 不給豁免(shadow-clamp 同款紀律)。"""
        up, down, sha = world
        self._sync_in(down)
        self._prov(down, upstream_commit=sha)
        bad = down.parent / "bad-pointer.txt"
        io.open(bad, "w", encoding="utf-8", newline="\n").write("隨便寫的東西\n")
        monkeypatch.setattr(gate, "UPSTREAM_ROOTS", str(bad))
        msg = gate.check("pkg/thing.py", "def f():\n    return 2\n")
        assert msg and "R3" in msg, msg

    def test_a_pointer_to_the_wrong_repo_refuses(self, world, monkeypatch):
        """指標指向**別的 repo** -> 物件比對失敗 -> 擋。

        這條與「指標缺失」不同:指標在、格式對、repo 也是真的 git repo,
        只是不是那個上游。判定仍然要靠物件比對擋下來。
        """
        up, down, sha = world
        other = down.parent / "other_repo"
        other.mkdir()
        for c in ("init -q", "config user.email t@t", "config user.name t"):
            subprocess.run(["git"] + c.split(), cwd=str(other), capture_output=True)
        io.open(other / "readme.txt", "w", encoding="utf-8").write("x\n")
        subprocess.run(["git", "add", "-A"], cwd=str(other), capture_output=True)
        subprocess.run(["git", "commit", "-qm", "o"], cwd=str(other),
                       capture_output=True)
        ptr = down.parent / "wrong-pointer.txt"
        io.open(ptr, "w", encoding="utf-8", newline="\n").write(
            "UPSTREAM_ROOT=%s\n" % str(other).replace("\\", "/"))
        monkeypatch.setattr(gate, "UPSTREAM_ROOTS", str(ptr))
        self._sync_in(down)
        self._prov(down, upstream_commit=sha)
        msg = gate.check("pkg/thing.py", "def f():\n    return 2\n")
        assert msg and "R3" in msg, msg

    def test_the_record_no_longer_carries_the_root(self, world):
        """jsonl 裡不該有 upstream_root —— 而且判定也不該讀它。

        上一條的負控(宣稱 hash 不採信)是同一個原則:
        **紀錄裡的欄位是給人看的,判定一律走獨立來源。**
        """
        up, down, sha = world
        self._sync_in(down)
        self._prov(down, upstream_root=str(down / "no_such_repo"),
                   upstream_commit=sha)
        msg = gate.check("pkg/thing.py", "def f():\n    return 2\n")
        assert not (msg and "R3/紅燈" in msg), \
            "判定讀了紀錄裡的 upstream_root,而不是指標檔:%r" % msg

    # ── 豁免的是 R3 **兩半**,不只紅燈半(票 20)────────────────────────

    def test_a_certified_file_with_no_test_file_is_not_blocked(self, world):
        """**本節的主張**:上游自己不出貨測試的檔案,下游拿到後 R3 完全不擋。

        原本只豁免紅燈半,前半的正當性寫著「同步本來就會把測試一起帶過來」——
        而那個前提對 `g1_verify.py` / `shadow_review.py` / `verify_gates.py`
        為假:上游 `tests/` 根本沒有對應檔案,再同步幾次都一樣。

        下游也沒有合法解:legacy 只減不增、自己補測試與 F-0014 的責任歸屬相衝、
        手寫豁免是自助。所以責任整個歸上游 ——
        **下游不得對進口成品要求比上游對自己更多的紀律。**
        """
        up, down, sha = world
        io.open(up / "pkg" / "notested.py", "w", encoding="utf-8",
                newline="\n").write("def g():\n    return 1\n")
        subprocess.run(["git", "add", "-A"], cwd=str(up), capture_output=True)
        subprocess.run(["git", "commit", "-qm", "no test upstream"],
                       cwd=str(up), capture_output=True)
        sha2 = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(up),
                              capture_output=True).stdout.decode().strip()
        io.open(down / "pkg" / "notested.py", "w", encoding="utf-8",
                newline="\n").write("def g():\n    return 1\n")
        self._prov(down, path="pkg/notested.py", upstream_path="pkg/notested.py",
                   upstream_commit=sha2)
        assert not (down / "tests" / "test_notested.py").exists()
        msg = gate.check("pkg/notested.py", "def g():\n    return 2\n")
        assert msg is None or "R3" not in msg, \
            "有證但上游沒測試檔的成品仍被 R3 擋:%r" % msg

    def test_a_drifted_file_gets_both_halves_back(self, world):
        """**負控**:本地改一個位元組就不再是「上游的成品」,兩半都回來。"""
        up, down, sha = world
        io.open(down / "pkg" / "mine2.py", "w", encoding="utf-8",
                newline="\n").write("def h():\n    return 1\n")
        self._prov(down, path="pkg/mine2.py", upstream_path="pkg/mine2.py",
                   upstream_commit=sha)
        msg = gate.check("pkg/mine2.py", "def h():\n    return 2\n")
        assert msg and "R3" in msg, "漂移的檔案沒有被 R3 擋:%r" % msg

    def test_a_local_file_without_provenance_is_still_blocked(self, world):
        """**負控**:R3 對本地寫的碼完全不變。"""
        up, down, sha = world
        io.open(down / "pkg" / "fresh_local.py", "w", encoding="utf-8",
                newline="\n").write("def k():\n    return 1\n")
        msg = gate.check("pkg/fresh_local.py", "def k():\n    return 2\n")
        assert msg and "R3" in msg, msg

    # ── 票 13 C:五態各自的原因,以及**每一態仍然被擋** ──────────────────

    def test_the_five_failure_modes_each_report_their_own_reason(
            self, world, monkeypatch):
        """票 13 C —— `upstream_backed` 原本把**五種**失敗全收斂成 `False`,
        於是 R3 的訊息三種情況印同一句:「跑一次測試讓紀錄長出來」——
        而那對一個**同步進來的成品做不到**(那正是 F-0014 開這條路的理由)。

        票面原本寫「三態」,實際列舉是**五態**(多出:provenance 檔本身讀不動、
        紀錄缺 `upstream_commit` 欄位)。**分支 3 拆開** ——
        `not root`(指標檔不可用)與 `not commit`(紀錄缺欄位)是兩個不同的修法。
        """
        up, down, sha = world
        self._sync_in(down)

        # 態一:沒有 provenance 紀錄
        ok, why = gate.upstream_backed("pkg/thing.py")
        assert ok is False and "沒有" in why and "紀錄" in why, why

        # 態二:指標檔不可用(讀不到或格式不對)——**不追到那一層的原因**
        self._prov(down, upstream_commit=sha)
        monkeypatch.setattr(gate, "UPSTREAM_ROOTS",
                            str(down / "no-such-pointer.txt"))
        ok, why = gate.upstream_backed("pkg/thing.py")
        assert ok is False and "指標" in why, why

    def test_a_record_without_a_commit_field_says_so(self, world, monkeypatch):
        """態三:紀錄在、指標在,但紀錄**缺 `upstream_commit`**。

        與態二分開:那一態要去修指標檔,這一態要去修 sync 產出的紀錄。
        **修法不同就不能共用一句話。**
        """
        up, down, sha = world
        self._sync_in(down)
        self._prov(down)                       # 不給 upstream_commit
        ok, why = gate.upstream_backed("pkg/thing.py")
        assert ok is False and "upstream_commit" in why, why

    def test_an_object_missing_upstream_says_so(self, world):
        """態四:上游問不到那個物件(commit 或路徑錯)。"""
        up, down, sha = world
        self._sync_in(down)
        self._prov(down, upstream_commit="0" * 40)
        ok, why = gate.upstream_backed("pkg/thing.py")
        assert ok is False and ("上游" in why or "物件" in why), why

    def test_content_drift_says_so(self, world):
        """態五:上游有那個物件,但**內容漂移**了。"""
        up, down, sha = world
        self._sync_in(down, text="def f():\n    return 2\n")   # 改一個位元組
        self._prov(down, upstream_commit=sha)
        ok, why = gate.upstream_backed("pkg/thing.py")
        assert ok is False and ("漂移" in why or "不相同" in why
                                or "對不上" in why), why

    @pytest.mark.parametrize("mode", ["no-record", "no-pointer", "no-commit",
                                      "no-object", "drift"])
    def test_every_failure_mode_is_still_blocked(self, world, monkeypatch, mode):
        """**反控 —— 本輪最重要的一條。**

        `upstream_backed` 改回 tuple 之後,**`(False, reason)` 在 `if` 裡是真的**。
        呼叫端若忘了解包,fail-closed 會被簽名改動**整條翻成 fail-open** ——
        每一個同步進來的檔案都會拿到豁免,而測試全綠、訊息什麼都不說。

        所以五個 False 分支逐一驗證「**仍然被擋**」,而不是只驗 reason 對不對。
        原因對了而擋沒了,是這一輪最貴的失敗方式。
        """
        up, down, sha = world
        if mode == "drift":
            self._sync_in(down, text="def f():\n    return 2\n")
        else:
            self._sync_in(down)
        if mode == "no-pointer":
            self._prov(down, upstream_commit=sha)
            monkeypatch.setattr(gate, "UPSTREAM_ROOTS", str(down / "nope.txt"))
        elif mode == "no-commit":
            self._prov(down)
        elif mode == "no-object":
            self._prov(down, upstream_commit="0" * 40)
        elif mode == "drift":
            self._prov(down, upstream_commit=sha)
        # no-record:什麼都不寫

        msg = gate.check("pkg/thing.py", "def f():\n    return 2\n")
        assert msg and "R3" in msg, (
            "%s:provenance 失敗卻放行 —— tuple 恆為真把 fail-closed 翻成 fail-open"
            % mode)

    def test_provenance_does_not_exempt_r2(self, world, monkeypatch):
        """**只豁免 R3。** R2 的窗口問題是票 10 的事,兩者不得互相代勞 ——
        一個豁免同時鬆兩條規則,爆炸半徑就不再是它宣稱的那個。"""
        up, down, sha = world
        monkeypatch.setattr(gate, "load_stage", lambda: ("review", "11"))
        self._sync_in(down)
        self._prov(down, upstream_commit=sha)
        msg = gate.check("pkg/thing.py", "def f():\n    return 2\n")
        assert msg and "R2" in msg, "provenance 順手把 R2 也豁免了:%r" % msg


class TestUntestedByDecisionCannotBeSelfServed:
    """票 24 — R3 的「Untested by decision」豁免必須是**無法自我服務**的。

    那段程式碼自己寫下的理由是:

        豁免不是 gate.py 自己開的後門 —— 它去讀一個**前一站產物裡已經存在的決定**。
        要新增豁免必須回頭改票,**那是看得見、會被審查的動作**。

    而判定實際做的是 `os.path.exists()`,**完全不碰 git**。
    被 R3 擋住的當下,建一個檔、寫一行宣告,豁免就到手了 ——
    不會出現在任何 diff、任何 review、任何 clone 裡。理由與實作對不上。

    **同一份檔案裡已經有解對的先例**:`check_legacy_list` 把凍結清單綁到
    go-live 樹,並且把理由寫死了 ——

        被 R3 擋下的人只要在末尾加一行就豁免到手 —— 完全不必碰 git 歷史,
        而「無法自我服務」正是選這個設計的**唯一**理由。
        「有一條測試會抓到」不算守住:沒有機制強制那條測試被跑。

    選型判準因此不是「哪個好寫」,是:**被擋住的代理人,能不能靠自己
    造出一個滿足這個判定的東西?** 能,就還沒修完。
    位置搬到哪裡都不解決這件事 —— 未追蹤的新檔在哪個目錄都一樣好造。
    **要綁的是「已經 commit」,不是「在哪個資料夾」。**
    """

    def _repo(self, tmp_path, monkeypatch):
        repo = tmp_path
        for c in ("init -q", "config user.email t@t", "config user.name t"):
            subprocess.run(["git"] + c.split(), cwd=str(repo), capture_output=True)
        (repo / "pkg").mkdir()
        (repo / "pkg" / "thing.py").write_text("x = 1\n", encoding="utf-8")
        (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=str(repo), capture_output=True)
        subprocess.run(["git", "commit", "-qm", "seed"], cwd=str(repo),
                       capture_output=True)
        monkeypatch.setattr(gate, "ROOT", str(repo))
        return repo

    DECL = "**Untested by decision:** thing\n"

    def _write_decl(self, repo, rel, commit):
        p = repo / rel.replace("/", os.sep)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# 票\n\n" + self.DECL, encoding="utf-8")
        if commit:
            subprocess.run(["git", "add", "-A"], cwd=str(repo), capture_output=True)
            subprocess.run(["git", "commit", "-qm", "宣告"], cwd=str(repo),
                           capture_output=True)
        return p

    def test_an_uncommitted_declaration_does_not_grant_the_exemption(
            self, tmp_path, monkeypatch):
        """**核心紅燈。** 未追蹤的宣告 = 代理人在被擋當下自己造出來的東西。

        這正是那段 docstring 說「看得見、會被審查」時排除掉的情況,
        而現行實作(`os.path.exists`)會吃下去。
        """
        repo = self._repo(tmp_path, monkeypatch)
        self._write_decl(repo, ".scratch/f/issues/01-x.md", commit=False)
        mods, declared_in = gate.ticket_untested_modules("f", "01")
        assert "thing" not in mods, (
            "未 commit 的宣告被吃進去了 —— 被 R3 擋住的代理人可以自己造一個,"
            "而且不會留下任何版控痕跡:%s" % declared_in)

    def test_a_committed_declaration_still_grants_the_exemption(
            self, tmp_path, monkeypatch):
        """**反控。** 少了它,「一律不豁免」的實作也會讓上一條過 ——
        那是把功能拿掉,不是修好。"""
        repo = self._repo(tmp_path, monkeypatch)
        self._write_decl(repo, ".scratch/f/issues/01-x.md", commit=True)
        mods, declared_in = gate.ticket_untested_modules("f", "01")
        assert "thing" in mods, "已 commit 的合法宣告被拒:%s" % declared_in

    def test_a_committed_declaration_under_docs_tickets_is_found(
            self, tmp_path, monkeypatch):
        """宣告位置不能綁死 `.scratch/`。

        實測:agent-gates 的票住在**進版控**的 `docs/tickets/<feature>/`,
        而 `.scratch/` 被 gitignore(0 個追蹤檔);
        三個下游 repo 反而把 `.scratch/` 進版控(31 / 21 / 3 個追蹤檔)。
        **同一個豁免位置,上游不受審查、下游受審查** —— 方向剛好反了。

        所以要找的是「**已 commit 的票**」,兩個位置都算;
        真正做事的是 commit 這個條件,不是資料夾名字。
        """
        repo = self._repo(tmp_path, monkeypatch)
        self._write_decl(repo, "docs/tickets/f/01-x.md", commit=True)
        mods, declared_in = gate.ticket_untested_modules("f", "01")
        assert "thing" in mods, "進版控的票位置找不到宣告:%s" % declared_in

    def test_no_declaration_at_all_is_still_fail_closed(self, tmp_path, monkeypatch):
        """既有行為的釘子:沒有宣告 = 不豁免。修的時候不能把這個方向弄反。"""
        repo = self._repo(tmp_path, monkeypatch)
        mods, declared_in = gate.ticket_untested_modules("f", "01")
        assert mods == set() and declared_in is None

    def test_the_commit_time_check_does_not_accept_an_uncommitted_ticket(
            self, tmp_path, monkeypatch):
        """`logged_exemption_backed` 是提交時那一半,同一個洞。

        它**不採信紀錄本身**、會回頭打開紀錄指名的票 —— 判準是對的,
        但「打開」用的是 `os.path.exists()`,所以未追蹤的票一樣過關。
        兩半都要綁 commit,只修一半等於沒修(繞道走另一半)。
        """
        repo = self._repo(tmp_path, monkeypatch)
        self._write_decl(repo, ".scratch/f/issues/01-x.md", commit=False)
        (repo / ".dev").mkdir(exist_ok=True)
        (repo / ".dev" / "gate-exemptions.jsonl").write_text(
            json.dumps({"file": "pkg/thing.py", "module": "thing",
                        "declared_in": ".scratch/f/issues/01-x.md"},
                       ensure_ascii=False) + "\n", encoding="utf-8")
        assert gate.logged_exemption_backed("pkg/thing.py", "thing") is False, (
            "提交時採信了一張未 commit 的票 —— 紀錄可以偽造,票也可以現造")

    def test_the_commit_time_check_accepts_a_committed_ticket(
            self, tmp_path, monkeypatch):
        """**反控**,同上:合法的那條路要留著。"""
        repo = self._repo(tmp_path, monkeypatch)
        self._write_decl(repo, ".scratch/f/issues/01-x.md", commit=True)
        (repo / ".dev").mkdir(exist_ok=True)
        (repo / ".dev" / "gate-exemptions.jsonl").write_text(
            json.dumps({"file": "pkg/thing.py", "module": "thing",
                        "declared_in": ".scratch/f/issues/01-x.md"},
                       ensure_ascii=False) + "\n", encoding="utf-8")
        assert gate.logged_exemption_backed("pkg/thing.py", "thing") is True


class TestEnforcementDoesNotTeachItsOwnBypass:
    """票 13 B —— 擋下訊息末尾寫著「如確定要略過:`git commit --no-verify`」。

    兩個問題,第二個更嚴重:

      **一、enforcement 訊息不得提示自身的繞過方式。**
      訊息要說出**哪一個前提沒滿足**(讓人去修),不是提供一條
      **不必滿足前提的出口**(讓人去繞)。前者把人推向修好,後者推向略過 ——
      而被煩到的規則會被關掉,提示語等於幫它加速。

      **二、「會留下紀錄,請自行負責」是假陳述。**
      `--no-verify` 在 git 裡**不留任何紀錄**:commit 上沒有標記、reflog 也不記。
      **那句話宣稱了一個不存在的機制**,比不寫更糟 ——
      它讓人以為有事後對帳,於是更放心用。

    與票 26 的同族(「請改用 Write / Edit」指向不能刪檔的工具)、
    票 22 的同族(machine-init 承諾一個不存在的指令):
    **訊息描述了一個世界上不存在的東西,而人會照著它去做。**
    """

    def _blocked_stderr(self, monkeypatch, capsys):
        # 簽名跟著本體走(票 42 加了 `gitlinks` 收集串列)——
        # 替身漏一個參數,mode_pre_commit 會在**取清單**那一步就掛掉,
        # 而這條測試要驗的是它**擋下之後**說了什麼。
        monkeypatch.setattr(gate, "staged_paths", lambda cwd=None, gitlinks=None: [])
        monkeypatch.setattr(gate, "check_skill_copies", lambda: [])
        monkeypatch.setattr(gate, "check_third_axis_mount", lambda: [])
        monkeypatch.setattr(gate, "check_to_spec_override", lambda: [])
        monkeypatch.setattr(gate, "check_legacy_list",
                            lambda: ["[R6] 測試用的違規"])
        monkeypatch.setattr(gate, "shadow_active", lambda: False)
        rc = gate.mode_pre_commit()
        return rc, capsys.readouterr().err

    def test_the_block_message_does_not_name_the_bypass_flag(
            self, monkeypatch, capsys):
        """**核心紅燈。** 擋下訊息不得含任何繞過指令。"""
        rc, err = self._blocked_stderr(monkeypatch, capsys)
        assert rc == 1, "沒擋"
        assert "--no-verify" not in err, (
            "enforcement 訊息教人怎麼繞過自己:%r" % err)

    def test_the_block_message_does_not_claim_a_record_is_kept(
            self, monkeypatch, capsys):
        """**假陳述。** git 對 `--no-verify` 不留任何痕跡 ——
        宣稱「會留下紀錄」會讓人以為有事後對帳,於是更放心用。"""
        rc, err = self._blocked_stderr(monkeypatch, capsys)
        assert "會留下紀錄" not in err, "宣稱了一個不存在的留痕機制:%r" % err

    def test_the_block_message_still_says_what_was_violated(
            self, monkeypatch, capsys):
        """**反控。** 拿掉繞過提示之後,訊息仍要說出擋了什麼、幾項。"""
        rc, err = self._blocked_stderr(monkeypatch, capsys)
        assert "測試用的違規" in err, "違規內容不見了:%r" % err
        assert "1 項" in err or "1项" in err, "沒說出違規項數:%r" % err


class TestFailClosedMessagesNameTheAbsolutePath:
    """票 31 / #10 —— 目錄名打錯時,沒有任何管道會說「你建在隔壁」。

    `.dev` 打成 `.dve` 時:

      `git status` 看不見    整個目錄被 gitignore,新目錄同樣被 ignore
      訊息只說「讀不到流程狀態」,**不會說它去哪裡找的**

    於是使用者對著一個**存在的、名字差一個字母**的目錄,
    收到一個「檔案不見了」的訊息。與票 26 同型:
    **訊息說的是真話,但它指向的排查方向是錯的。**

    修法成本近乎零:印出它**實際查找的絕對路徑**。打錯字時那條路徑本身就是證據 ——
    人一眼看到 `…\\.dve\\pipeline.json` 就知道了。

    ## 絕對路徑不得出現在第一行(順序先於 1–2 的那條)

    絕對路徑含使用者名稱,而 `log_shadow` 會把**訊息的第一行**寫進
    `.dev/shadow-log.jsonl`(持久檔)。所以路徑放在**第二行之後** ——
    人看得到,證據檔存不到。

    (`gate-exemptions.jsonl` 現在進版控,但它存的是 `blocked_by` 規則碼、
    不是訊息全文,已查證。)
    """

    def test_the_message_names_the_absolute_path_it_looked_for(self, monkeypatch):
        monkeypatch.setattr(gate, "load_stage",
                            lambda: (gate.UNREADABLE_STAGE, None))
        msg = gate.check("pkg/thing.py", "x = 1")
        assert msg and "R2" in msg, msg
        assert gate.PIPELINE in msg, (
            "訊息沒印出實際查找的絕對路徑 —— 打錯目錄名時人不會知道找錯地方:%r"
            % msg)

    def test_the_absolute_path_is_not_on_the_first_line(self, monkeypatch):
        """**這條先於上一條成立才有意義。**

        `log_shadow` 只取 `msg.splitlines()[0]` 寫進持久的證據檔,
        而絕對路徑含使用者名稱。放第一行 = 每一次影子攔截都把使用者名稱寫進檔案。
        """
        monkeypatch.setattr(gate, "load_stage",
                            lambda: (gate.UNREADABLE_STAGE, None))
        msg = gate.check("pkg/thing.py", "x = 1")
        first = msg.splitlines()[0]
        assert gate.PIPELINE not in first, (
            "絕對路徑出現在第一行 —— 它會被 log_shadow 寫進 shadow-log.jsonl:%r"
            % first)

    def test_the_message_still_says_what_to_do(self, monkeypatch):
        """**反控。** 加了路徑之後,原本的判準與指示不得消失。"""
        monkeypatch.setattr(gate, "load_stage",
                            lambda: (gate.UNREADABLE_STAGE, None))
        msg = gate.check("pkg/thing.py", "x = 1")
        assert "idle" in msg, "「不知道停在哪一站不等於 idle」那句不見了"
        assert "pipeline.json" in msg


class TestAuthorityLayerIsWired:
    """票 27 — 權威層有沒有**真的接上 git**。

    **這個 class 只放既有涵蓋沒有的東西。** 偵測本身早就存在
    (`authoritative_layer()`,連同 `TestAuthoritativeLayerNotice` 那組測試):
    它已經處理 `core.hooksPath`、已經判內容而非只判檔案存在、
    已經被 `sentinel_footer()` 與 `mode_hook()` 呼叫。
    第一版的我沒查就另寫了一份實作,那是重複不是補強(F-080)。

    剩下三件事是真的缺的:

    1. **`--pre-commit` 也要出現。** 只檢查 `"gate.py" in body` 的話,
       一支「呼叫了 gate.py 但沒帶 `--pre-commit`」的 hook 會被判成已安裝 ——
       而那種 hook 什麼都不擋。
    2. **`core.hooksPath` 的優先順序有測試。** 既有測試造的是假 `.git` 目錄
       (不是真 repo),`git config` 問不到就退回預設路徑,所以那條分支沒被走過。
    3. **活體金絲雀** —— 見 `test_this_repo_itself_is_wired`。

    一句話教訓(票 27):**手動呼叫一支檢查,不等於那支檢查在通行路上。**
    修正版:**訊號太弱也不等於沒有訊號** —— `mode_hook()` 每 4 小時會印一次
    未安裝提醒,訊號存在,只是節流到實務上沒人看見。兩者的修法不同
    (一個是接線,一個是提高可見度),所以不能混為一談。
    """

    def _repo(self, tmp_path, name):
        repo = tmp_path / name
        repo.mkdir()
        for c in ("init -q", "config user.email t@t", "config user.name t"):
            subprocess.run(["git"] + c.split(), cwd=str(repo), capture_output=True)
        return repo

    def _hook(self, path, body):
        path.parent.mkdir(parents=True, exist_ok=True)
        io.open(path, "w", encoding="utf-8", newline="\n").write(body)

    LEAK_ONLY = ('#!/bin/sh\nexec python "$(git rev-parse --show-toplevel)'
                 '/.claude/portable/leak_scan.py" --staged\n')
    WIRED = ('#!/bin/sh\nroot="$(git rev-parse --show-toplevel)"\n'
             'python "$root/.claude/portable/leak_scan.py" --staged || exit 1\n'
             'exec python "$root/.claude/hooks/gate.py" --pre-commit\n')
    # 呼叫了 gate.py,但**沒帶 --pre-commit** —— 它會跑 gate.py 的預設模式,
    # 那不是權威判定。檔案在、名字對、內容含 "gate.py",而它什麼都不擋。
    NO_MODE_FLAG = ('#!/bin/sh\nexec python "$(git rev-parse --show-toplevel)'
                    '/.claude/hooks/gate.py"\n')

    def test_a_hook_that_calls_the_gate_without_the_mode_flag_is_not_installed(
            self, tmp_path):
        """**票 27 收尾的紅燈。** 只比對 `"gate.py" in body` 會放行這一支。

        這是「讀起來在守、實際只守一部分」的形狀(R4 那一族):
        判定用的證據比它宣稱保證的東西弱一階。
        """
        repo = self._repo(tmp_path, "nomodeflag")
        self._hook(repo / ".git" / "hooks" / "pre-commit", self.NO_MODE_FLAG)
        installed, detail = gate.authoritative_layer(str(repo))
        assert installed is False, (
            "hook 呼叫 gate.py 但沒帶 --pre-commit,卻被判成已安裝 —— "
            "那支 hook 什麼都不擋:%s" % detail)
        assert "--pre-commit" in detail, "訊息沒說出缺的是哪一個前提:%r" % detail

    def test_the_check_follows_core_hookspath(self, tmp_path):
        """**驗的是 git 實際會執行的那一支,不是某個路徑上的檔案。**

        構造:`.git/hooks/pre-commit` 接得好好的,但 `core.hooksPath` 指到
        另一個目錄,而那裡的 hook 只有 leak_scan。git 會執行後者。
        只看 `.git/hooks/` 的實作會在這裡給出綠燈 —— 而那個綠燈是假的。

        這不是假想:`bootstrap.sh` 宣稱用 `core.hooksPath` 指向版控裡的
        `.githooks/`,而實測那個 config 根本沒設定。兩條掛載路徑並存,
        所以「哪一支會跑」必須問 git,不能假設。

        既有測試造的是假 `.git` 目錄,`git config` 問不到 —— 這條走的是**真 repo**,
        那個分支才真的被執行到。
        """
        repo = self._repo(tmp_path, "hookspath")
        self._hook(repo / ".git" / "hooks" / "pre-commit", self.WIRED)
        self._hook(repo / ".githooks" / "pre-commit", self.LEAK_ONLY)
        subprocess.run(["git", "config", "core.hooksPath", ".githooks"],
                       cwd=str(repo), capture_output=True)
        installed, detail = gate.authoritative_layer(str(repo))
        assert installed is False, (
            "core.hooksPath 指到的那支沒接權威層,卻因為 .git/hooks/ 裡有一支"
            "接好的而判成已安裝 —— 綠燈的原因不對:%s" % detail)
        assert ".githooks" in detail, "訊息沒指名實際會跑的那一支:%r" % detail

    def test_a_wired_hook_under_hookspath_is_installed(self, tmp_path):
        """**反控。** 少了它,「真 repo 一律判未安裝」的實作也會讓上面兩條過。"""
        repo = self._repo(tmp_path, "hookspathok")
        self._hook(repo / ".githooks" / "pre-commit", self.WIRED)
        subprocess.run(["git", "config", "core.hooksPath", ".githooks"],
                       cwd=str(repo), capture_output=True)
        installed, detail = gate.authoritative_layer(str(repo))
        assert installed is True, detail

    # 呼叫了 gate.py --pre-commit,但**沒接 leak_scan** —— 六站那段在,
    # 洩漏偵測那段不在。hook 的契約是**兩段都接**(.githooks/pre-commit 票 27)。
    GATE_ONLY = ('#!/bin/sh\nexec python "$(git rev-parse --show-toplevel)'
                 '/.claude/hooks/gate.py" --pre-commit\n')

    def test_a_hook_missing_the_leak_stage_is_not_installed(self, tmp_path):
        """**票 76(B5)的紅燈。** 缺洩漏段的 hook 不得被判成「已安裝」。

        與票 27 那條(`NO_MODE_FLAG`)同族、方向相反:那次掉的是 gate 段,
        這次掉的是 leak_scan 段。`authoritative_layer()` 原本只找
        `"gate.py"` 與 `"--pre-commit"` 兩個字串 —— 判定用的證據比 hook
        契約(兩段都接)弱一階,於是裝好之後洩漏段被降級是**完全靜默**的:
        常駐提醒照說已安裝、活體金絲雀照綠,唯一驗它的時點是安裝當下
        (verify_gates 的 F-062 檢查),而那個時點只有一次。
        """
        repo = self._repo(tmp_path, "gateonly")
        self._hook(repo / ".git" / "hooks" / "pre-commit", self.GATE_ONLY)
        installed, detail = gate.authoritative_layer(str(repo))
        assert installed is False, (
            "hook 缺 leak_scan 段,卻被判成已安裝 —— 洩漏偵測層靜默消失:%s"
            % detail)
        assert "leak_scan" in detail, (
            "訊息沒說出缺的是哪一個前提(洩漏段):%r" % detail)

    def test_this_repo_itself_is_wired(self):
        """**活體金絲雀:現在、這台機器上、這個 repo,權威層真的接上了嗎。**

        既有那組測試明講「只驗未安裝路徑:已安裝路徑就是本機現況,
        測它等於測環境(接縫 S3)」—— 那條原則對**框架性質**成立,
        而這一條刻意違反它,因為它問的不是框架性質,是**部署事實**。
        票 27 的整件事就是:框架性質全部正確,而部署從來沒發生過,
        40 個 commit 沒有人發現。**只驗框架性質的測試集,永遠抓不到這個。**

        代價誠實寫出來:任何**新 clone** 在跑 `bootstrap.sh` 之前,這一條都會紅。
        那是刻意的(缺席必須出聲),但紅燈必須帶著修法 —— 否則就變成
        「這套測試本來就紅」,而那比沒有測試更糟(F-031)。修法只有一行,
        所以斷言訊息直接把它寫出來。
        """
        installed, detail = gate.authoritative_layer(str(ROOT))
        assert installed is True, (
            "%s\n"
            "     權威層沒接上 —— 六站閘門只剩前哨,commit 時不會判定。\n"
            "     修法:在 repo 根目錄跑 `sh bootstrap.sh`(一行 config,每個 clone 一次)。"
            % detail)


# ─────────────────────────────────────────────────────────────────────────────
# 票 41 —— R3 對 gitlink(submodule)路徑永遠給不出合格紅燈
#
# 下游(量化)實測:`data_collector` 是 submodule,parent 的樹在那一格存的是
# 一個 commit id(mode 160000),不是子樹。於是:
#
#   git cat-file blob HEAD:data_collector/<檔>   →  fatal
#   head_content_hash(...)                       →  None
#
# 而 redlight_missing 的兩個合格出口是「實作當時不存在」與「impl_hash == HEAD」——
# 既有檔案走不到前者,head is None 走不到後者。**兩個都走不到 = 永遠不合格。**
# 出口只剩 legacy 清單,而它只減不增且入場券綁 parent 的 go-live 樹,等於沒有出口。
#
# F-0013 把錨點放在 HEAD 是對的(時點不變),錯的是它假設
# `git show HEAD:<路徑>` 對任何受版控的路徑都讀得到。這個缺席**完全無聲**:
# 「gitlink 讀不到」與「新建未提交」在 head_blob 裡共用同一個回傳值 None。
#
# 本組測試的重心在**負控**:修法是「多一條讀取路徑」,而多一條路徑最便宜的寫法
# 就是失敗時放行。少了 3/4,本票會把「永遠擋」換成「永遠放行」,而測試全綠。
# ─────────────────────────────────────────────────────────────────────────────

class TestGitlinkPathsCanReachAQualifyingRedlight:

    @pytest.fixture()
    def repo(self, tmp_path, monkeypatch):
        """parent + 真的 submodule。**gitlink 只能對著真的物件庫驗。**

        用 `update-index --cacheinfo` 直接種一格 mode 160000,不走
        `git submodule add` —— 後者要 `protocol.file.allow`(git 2.38+ 預設擋
        file:// submodule),那條限制與本票無關,卻會讓 fixture 因為別的理由壞掉。
        判定看的是 **tree 的 mode**,而這條路徑產出的 mode 與 `submodule add` 相同。

        fixture 自己斷言那一格真的是 160000:**fixture 壞掉要當場出聲**,
        否則「測試綠了」可能只代表它測了一個沒有 gitlink 的 repo。
        """
        def git(*a, **kw):
            cwd = kw.pop("cwd", str(tmp_path))
            return subprocess.run(["git"] + list(a), cwd=cwd, capture_output=True)

        sub = tmp_path / "sub"
        sub.mkdir()
        io.open(sub / "thing.py", "w", encoding="utf-8",
                newline="\n").write("def f():\n    return 1\n")
        git("init", "-q", cwd=str(sub))
        git("config", "user.email", "t@t", cwd=str(sub))
        git("config", "user.name", "t", cwd=str(sub))
        git("add", "-A", cwd=str(sub))
        git("commit", "-qm", "sub", cwd=str(sub))
        sub_head = git("rev-parse", "HEAD", cwd=str(sub)).stdout.decode().strip()

        git("init", "-q")
        git("config", "user.email", "t@t")
        git("config", "user.name", "t")
        (tmp_path / "pkg").mkdir()
        io.open(tmp_path / "pkg" / "plain.py", "w", encoding="utf-8",
                newline="\n").write("x = 1\n")
        (tmp_path / "tests").mkdir()
        io.open(tmp_path / "tests" / "test_thing.py", "w", encoding="utf-8").write("x\n")
        io.open(tmp_path / "tests" / "test_plain.py", "w", encoding="utf-8").write("x\n")
        git("add", "pkg", "tests")
        git("update-index", "--add", "--cacheinfo", "160000,%s,sub" % sub_head)
        git("commit", "-qm", "parent")

        mode = git("ls-tree", "HEAD", "--", "sub").stdout.decode().split(" ")[0]
        assert mode == "160000", "fixture 沒種出 gitlink(mode=%r)" % mode

        monkeypatch.setattr(gate, "ROOT", str(tmp_path))
        monkeypatch.setattr(gate, "RUN_LOG", str(tmp_path / ".dev" / "test-runs.jsonl"))
        monkeypatch.chdir(tmp_path)
        return tmp_path

    def _log(self, repo, *recs):
        d = repo / ".dev"
        d.mkdir(exist_ok=True)
        with io.open(d / "test-runs.jsonl", "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    def _sub_head_hash(self, repo, rel="thing.py"):
        blob = subprocess.run(["git", "cat-file", "blob", "HEAD:" + rel],
                              cwd=str(repo / "sub"), capture_output=True).stdout
        norm = blob.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        return hashlib.sha256(norm).hexdigest()

    def _red(self, **kw):
        rec = {"test_file": "tests/test_thing.py", "result": "red",
               "failed_tests": ["test_a"], "impl_file": "sub/thing.py",
               "impl_exists": True, "impl_hash": None, "ticket_id": "41"}
        rec.update(kw)
        return rec

    # ── 正控 ──────────────────────────────────────────────────────────────

    def test_head_blob_delegates_into_the_submodule(self, repo):
        """紅燈 1:parent 問不到的東西,要去問那個 submodule 自己的 HEAD。"""
        raw = gate.head_blob("sub/thing.py")
        assert raw is not None, (
            "head_blob 對 gitlink 底下的檔案回 None —— parent 的 "
            "`HEAD:sub/thing.py` 本來就 fatal,要委派給 submodule")
        assert b"def f()" in raw

    def test_an_existing_file_in_a_submodule_can_reach_a_qualifying_redlight(self, repo):
        """**本單元的主張**:submodule 底下的既有檔案做得到紅燈先行。"""
        self._log(repo, self._red(impl_hash=self._sub_head_hash(repo)))
        assert gate.redlight_missing("thing", impl_rel="sub/thing.py",
                                     ticket="41") is None, \
            "submodule 底下的既有檔案仍然拿不到合格紅燈"

    # ── 負控 ──────────────────────────────────────────────────────────────

    def test_a_file_absent_from_the_submodule_head_is_still_blocked(self, repo):
        """紅燈 3:委派之後仍讀不到 ⇒ **維持 fail-closed**。

        「讀不到」不得變成放行 —— 那是把一個「永遠擋」的缺陷換成
        「永遠放行」的缺陷,而後者不會有人發現。
        """
        io.open(repo / "sub" / "fresh.py", "w", encoding="utf-8").write("y = 2\n")
        assert gate.head_blob("sub/fresh.py") is None, \
            "檔案不在 submodule 的 HEAD 裡,head_blob 卻回了內容"
        self._log(repo, self._red(test_file="tests/test_fresh.py",
                                  impl_file="sub/fresh.py", impl_hash="a" * 64))
        assert gate.redlight_missing("fresh", impl_rel="sub/fresh.py",
                                     ticket="41") is not None

    def test_a_broken_submodule_does_not_open_the_gate(self, repo):
        """紅燈 4:submodule 的 `.git` 不見 ⇒ 委派失敗 ⇒ 照擋。

        fail-closed 不能靠「委派剛好會成功」。這也是**未 init 的 submodule**
        在磁碟上的真實樣子:目錄在、工作樹在、`.git` 不在。

        用改名不用 `rmtree`:Windows 上 git 的物件檔是唯讀的,
        `shutil.rmtree` 直接 PermissionError —— 那會讓這條負控因為
        **與判定無關的理由**變紅,而紅得不對的測試等於沒有測試。
        """
        os.rename(str(repo / "sub" / ".git"), str(repo / "sub" / ".git-gone"))
        assert gate.head_blob("sub/thing.py") is None
        self._log(repo, self._red(impl_hash="b" * 64))
        assert gate.redlight_missing("thing", impl_rel="sub/thing.py",
                                     ticket="41") is not None

    def test_a_red_against_a_modified_submodule_implementation_is_blocked(self, repo):
        """紅燈 5:先寫實作再補跑紅燈,在 submodule 底下照樣不算。

        委派把出口打開了,這條確認打開的是**正確的那一個**出口。
        """
        self._log(repo, self._red(impl_hash="0" * 64))
        assert gate.redlight_missing("thing", impl_rel="sub/thing.py",
                                     ticket="41") is not None

    # ── 回歸 ──────────────────────────────────────────────────────────────

    def test_a_plain_directory_is_not_mistaken_for_a_submodule(self, repo):
        """紅燈 6:mode 只認 `160000`。

        檔案模式位元是**封閉集合**(`100644` / `100755` / `120000` /
        `040000` / `160000`),所以判定用枚舉、不用 pattern 比對(F-087)。
        一般目錄(`040000`)底下的路徑照舊由 parent 回答;不在 HEAD 就是 None,
        不得因為「委派一下說不定讀得到」而繞去別的物件庫。
        """
        assert gate.head_blob("pkg/plain.py") is not None, "一般路徑被弄壞了"
        assert gate.head_blob("pkg/nope.py") is None, \
            "一般目錄底下不存在的檔案卻讀到了內容"


# ─────────────────────────────────────────────────────────────────────────────
# 票 42 —— 權威層自己的 staged 清單也把 gitlink 當成原始碼
#
# `staged_paths` 在本框架有**兩份**:`.claude/portable/scanner.py`(下游回報的那份)
# 與本檔測的這份。下游沒撞到第二份,只是因為 hook 的順序是
# `leak_scan || exit 1` 在前 —— **還沒走到 gate**。
#
# 本機唯讀實測(開票時):
#   is_source_path('data_collector') = True     ← 無副檔名、top 不在非原始碼清單
#   check(…, at_commit=True):grill / spec / tickets → [R2/commit] 前置站卻要提交原始碼
#                             research            → [R2/範圍]
#                             implement / review  → None
#
# **implement / review 放行是巧合,不是判定認得 gitlink。** 那兩站只是 R2 在提交時
# 本來就不問的站別;判定從頭到尾都把那一格當成一支沒有副檔名的原始碼檔。
# 而 R2 的擋下訊息**完全不提 gitlink** —— 使用者會去查站別(票 13 的判準:
# 訊息要說出是哪一個前提沒滿足,不是把人指向錯的方向)。
#
# 修的範圍**只有**「gitlink 不是原始碼」這一句,不順手改 is_source_path 的其他語意。
# ─────────────────────────────────────────────────────────────────────────────

class TestTheAuthorityLayerDoesNotTreatAGitlinkAsSource:

    def _repo(self, tmp_path):
        """外層 repo:staged 一個一般檔 + 一格 gitlink。"""
        def git(*a, **kw):
            return subprocess.run(["git"] + list(a),
                                  cwd=kw.get("cwd", str(tmp_path)),
                                  capture_output=True)

        inner = tmp_path / "data_collector"
        inner.mkdir()
        io.open(inner / "collect.py", "w", encoding="utf-8",
                newline="\n").write("x = 1\n")
        for c in ("init -q", "config user.email t@t", "config user.name t",
                  "add -A", "commit -qm inner"):
            git(*c.split(), cwd=str(inner))
        sha = git("rev-parse", "HEAD", cwd=str(inner)).stdout.decode().strip()

        for c in ("init -q", "config user.email t@t", "config user.name t"):
            git(*c.split())
        io.open(tmp_path / "README.md", "w", encoding="utf-8").write("x\n")
        git("add", "README.md")
        git("commit", "-qm", "base")
        (tmp_path / "pkg").mkdir()
        io.open(tmp_path / "pkg" / "a.py", "w", encoding="utf-8",
                newline="\n").write("y = 1\n")
        git("add", "pkg/a.py")
        git("update-index", "--add", "--cacheinfo",
            "160000,%s,data_collector" % sha)
        mode = git("ls-files", "-s", "data_collector").stdout.decode().split(" ")[0]
        assert mode == "160000", "fixture 沒種出 gitlink(mode=%r)" % mode
        return tmp_path

    def test_the_gitlink_is_not_in_the_staged_listing(self, tmp_path):
        """**本組的主張**:那一格不進權威層的判定清單,所以 R2/R3 不會碰它。"""
        repo = self._repo(tmp_path)
        got = gate.staged_paths(str(repo))
        assert "data_collector" not in got, \
            "gitlink 仍被當成待判定的原始碼:%r" % got

    def test_ordinary_files_are_still_listed(self, tmp_path):
        """**負控**:判定面不得被這次過濾弄小。

        少了它,「staged_paths 一律回空」也會讓上面那條過 ——
        而那是把整個權威層靜默關掉,測試看起來還是綠的。
        """
        repo = self._repo(tmp_path)
        assert sorted(gate.staged_paths(str(repo))) == ["pkg/a.py"]

    def test_the_skip_is_visible_to_the_caller(self, tmp_path):
        """跳過要**看得見**,理由與 (a) 那半相同:靜默跳過不算修好。"""
        repo = self._repo(tmp_path)
        skipped = []
        gate.staged_paths(str(repo), gitlinks=skipped)
        assert skipped == ["data_collector"], \
            "被跳過的 gitlink 沒有交給呼叫端:%r" % skipped

    def test_the_verdict_comes_from_the_index_not_the_filesystem(self, tmp_path):
        """**負控**:判定依據不得跑到檔案系統去(同 scanner 那半)。

        把目錄搬走 —— `os.path.isdir()` 從此回 False,而 index 裡那一格還是
        160000。index 的 mode 才是權威。
        """
        repo = self._repo(tmp_path)
        os.rename(str(repo / "data_collector"), str(repo / "moved-away"))
        assert "data_collector" not in gate.staged_paths(str(repo))

    def test_the_pre_commit_report_names_the_skipped_gitlink(self, tmp_path):
        """**接線要測**(F-044):過濾寫好了但沒接上報告,等於靜默跳過。

        訊息要說出**由誰守** —— 外層對 gitlink 的正確語意是
        「這一格由內層 repo 自己守」,而不是「這一格沒事」。
        """
        note = gate.gitlink_note(["data_collector"])
        assert "data_collector" in note and "gitlink" in note and "內層" in note, note
        src = io.open(ROOT / ".claude" / "hooks" / "gate.py", encoding="utf-8").read()
        assert "gitlinks=" in src and "gitlink_note" in src, \
            "mode_pre_commit 沒有把跳過的 gitlink 接進報告"

    def _fresh_scanner(self):
        """另外載一份 scanner。**不共用模組物件** —— 下面那條要改它的常數,
        改在共用的那一份上會滲到別的測試(而那種污染是無聲的)。"""
        spec = importlib.util.spec_from_file_location(
            "scanner_for_parity", ROOT / ".claude" / "portable" / "scanner.py")
        sc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sc)
        return sc

    def _assert_parity(self, repo, sc):
        """兩份 `staged_paths` 對同一個 repo 的答案必須一致。

        **抽成一個函式,是為了讓下面那條突變測試打到同一段斷言** ——
        複製一份斷言來測「斷言會不會紅」,測到的是那份副本(ADR 0003 的形狀)。
        """
        g_skipped, s_skipped = [], []
        g = gate.staged_paths(str(repo), gitlinks=g_skipped)
        s = sc.staged_paths(cwd=str(repo), gitlinks=s_skipped)
        assert sorted(g) == sorted(s), "兩份 staged 清單對同一個 repo 給出不同答案"
        assert g_skipped == s_skipped == ["data_collector"], \
            "兩份對「哪一格是 gitlink」的答案不一致:%r / %r" % (g_skipped, s_skipped)

    def test_both_staged_listings_agree_on_a_gitlink(self, tmp_path):
        """**同缺陷的兩份實作必然漂開**(F-058 家族)—— 所以釘住兩者一致。

        `staged_paths` 有兩份(`.claude/hooks/gate.py` 與
        `.claude/portable/scanner.py`),它們**不共用程式碼**:前者是權威層 hook,
        隨 `.claude/hooks/` 安裝;後者是 portable 掃描器骨架。
        本票同時修兩份,而「同時修好」不會自己維持下去 ——
        下一次只有一邊被動到時,漂開是無聲的。這條測試就是那個機制。

        **兩份是刻意保留的,不是還沒清掉的重複**(票 42 裁決):
        權威層要依賴最少的東西 —— 讓它 import `portable/` 會多一個失效點,
        而**閘門起不來的樣子跟沒裝一模一樣**(全靜默)。
        看到這個重複想合併之前,先讀那則裁決。
        """
        self._assert_parity(self._repo(tmp_path), self._fresh_scanner())

    def test_the_parity_check_itself_goes_red_when_one_side_drifts(self, tmp_path):
        """**釘住上面那條會咬**:只改壞一份,一致性斷言必須紅。

        沒有這條的話,`_assert_parity` 只是一句「兩邊相等」的宣稱 ——
        它可能因為**任何**理由恆真(兩邊都回空、兩個清單都被跳過清單吃掉、
        斷言寫錯方向),而恆真的斷言與有效的斷言在測試輸出上長得一模一樣。

        F-090 才剛示範過這件事的代價:那一格的 fail-closed 分支從來沒有被走到過,
        測試卻一路綠 —— **綠的理由不是我以為的那個**,而它差一步就變成 fail-open。

        突變的打法:只動 scanner 那一份的 `GITLINK_MODE`(改成一個不存在的 mode,
        等於它不再認得 gitlink)。改常數不改檔案 —— 這一份是本測試自己載的,
        不會滲到別處;而它造成的**行為**就是「只有一邊被修好」。
        """
        repo = self._repo(tmp_path)         # **在 raises 之外建** —— 見下
        sc = self._fresh_scanner()
        sc.GITLINK_MODE = "160001"          # 只有 scanner 那一份漂開

        # fixture 自己也有一句 assert(mode 必須是 160000)。把它放進 raises 區塊裡,
        # 這條測試會在 fixture 壞掉時**照樣綠** —— 綠的理由變成「fixture 炸了」。
        # 這正是本條要防的東西的縮影,所以它不能自己犯一次。
        with pytest.raises(AssertionError) as caught:
            self._assert_parity(repo, sc)
        assert "gitlink" in str(caught.value) or "staged 清單" in str(caught.value), \
            "紅是紅了,但不是被一致性斷言擋下的:%s" % caught.value


class TestFrictionNumbersAreUnique:
    """票 83 —— friction 號的唯一性,權威層檢查。

    **它已經撞過一次**(2026-08-26):兩個視窗各發了一個 `F-122`,
    `721cb8f` 與 `0b17cae` **都經過 pre-commit,兩次都綠**。
    抓到它靠的是有人為了發下一個號去查最大號,順手看到 `uniq -d` 回了兩個 122 ——
    **下一次沒有人去查最大號時,它不會被發現。**

    ## 為什麼這一條適合進權威層(判準寫死,免得被拿去論證別的)

    **零誤報**(兩個一樣的號就是撞號,沒有灰色地帶)、
    **零判斷**(不必理解那兩則寫了什麼)、**極便宜**(一次掃描 + 一個 set)。

    對照:票 53 登記的 stale status 偵測器**不該**用同一個理由進權威層 ——
    它要判「票面說的與實際做的一不一致」,而「實際做了什麼」本身要推論,
    **推論會錯,而錯在權威層等於擋住做對事的人**,那種規則最後會被整條關掉。

    > **進權威層的門檻不是「重要」,是「零誤報 + 零判斷 + 便宜」。**

    ## 範圍:只查重複

    不查連號(改號會留下空洞,見發號規則第 4 節)、不查格式、不查跨 repo。
    **一條檢查一件事** —— 混進一個會誤報的子判定,整條的可信度就跟著它走。
    """

    def _log(self, tmp_path, body):
        p = tmp_path / "friction-log.md"
        p.write_text(body, encoding="utf-8")
        return str(p)

    def test_a_duplicate_number_is_a_violation(self, tmp_path, monkeypatch):
        """正向:同一個號出現兩次 → 違規。"""
        path = self._log(tmp_path,
                         "## F-001 甲\n\n內文\n\n## F-002 乙\n\n## F-001 丙\n")
        v = gate.check_friction_numbers(path)
        assert v, "撞號沒有被抓到"

    def test_the_message_names_which_number(self, tmp_path):
        """**訊息要說出是哪一個號** —— 一份 log 幾百則,
        「有撞號」而不說哪一個等於要人自己再掃一次(票 13 的判準)。"""
        path = self._log(tmp_path, "## F-007 甲\n\n## F-007 乙\n")
        v = gate.check_friction_numbers(path)
        assert v and "F-007" in v[0], v

    def test_a_clean_log_passes(self, tmp_path):
        """負控一:沒撞號就不得報。"""
        path = self._log(tmp_path, "## F-001 甲\n\n## F-002 乙\n\n## F-003 丙\n")
        assert gate.check_friction_numbers(path) == []

    def test_a_gap_in_numbering_is_not_a_violation(self, tmp_path):
        """**負控二:缺號合法。** 改號會留下空洞(發號規則第 4 節:
        原號不回收),把連號也查進來的話本條就不再是零誤報的。"""
        path = self._log(tmp_path, "## F-001 甲\n\n## F-003 丙\n\n## F-009 己\n")
        assert gate.check_friction_numbers(path) == []

    def test_a_companion_note_heading_is_not_a_collision(self, tmp_path):
        """**負控三:併記段不算撞號。**

        本庫實際有一段標題是 `## 併記於 F-118(…)` —— 它**刻意不**寫成
        `## F-118 …` 正是為了不被本檢查判成撞號。
        判定對象是**發號用的標題行**(`^## F-<數字>`),不是任何提到號碼的行。
        """
        path = self._log(tmp_path,
                         "## F-118 甲\n\n## 併記於 F-118(2026-08-26):乙\n")
        assert gate.check_friction_numbers(path) == []

    def test_an_inline_mention_is_not_a_collision(self, tmp_path):
        """負控四:內文引用重複是正常的,不得誤判。"""
        path = self._log(tmp_path,
                         "## F-005 甲\n\n見 F-005 與 F-005 的討論。\n\n## F-006 乙\n")
        assert gate.check_friction_numbers(path) == []

    def test_a_downstream_prefix_is_handled_by_its_own_namespace(self, tmp_path):
        """下游用自己的前綴,`TSI-001` 與 `F-001` **不衝突**。"""
        path = self._log(tmp_path, "## F-001 甲\n\n## TSI-001 乙\n")
        assert gate.check_friction_numbers(path) == []

    def test_a_duplicate_downstream_number_is_still_caught(self, tmp_path):
        """而同一個前綴內撞號照樣要抓 —— 否則判定就只服務上游。"""
        path = self._log(tmp_path, "## TSI-001 甲\n\n## TSI-001 乙\n")
        v = gate.check_friction_numbers(path)
        assert v and "TSI-001" in v[0], v

    def test_an_unreadable_log_is_a_violation_not_a_pass(self, tmp_path):
        """**fail-closed**:讀不到不得靜默通過(家規)。"""
        v = gate.check_friction_numbers(str(tmp_path / "does-not-exist.md"))
        assert v, "讀不到檔案竟然回報乾淨(fail-open)"

    def test_the_rule_is_actually_invoked_at_the_authoritative_layer(
            self, monkeypatch):
        """**最強的那一條**(照 R6 的先例):驗規則真的被 pre-commit 呼叫,
        不只是函式回對值。沒有這條的話,一個寫好卻沒接上的檢查會全綠。"""
        monkeypatch.setattr(gate, "check_friction_numbers",
                            lambda *a, **k: ["假違規"])
        assert gate.mode_pre_commit() == 1, "pre-commit 沒有呼叫 check_friction_numbers"

    def test_the_shipped_log_is_clean(self):
        """對**本庫現行的** friction-log 跑一次 —— 正對照,不是只測 tmp_path。"""
        assert gate.check_friction_numbers() == []

    # ── 票 103:訊息內容與多重撞號的正控 ──────────────────────────────────
    #
    # 上面那批問的是**會不會擋**。以下九條問的是另外兩件事:
    #   ① 擋下時**訊息說了什麼**(具體到行號,不只是號碼)
    #   ② 撞號**不只一次 / 不只一個號**時,分筆與排序對不對
    #
    # 口徑:每一條都斷言**訊息的具體內容**或**發現的筆數**,
    # 不得只斷言 truthy —— 那一層上面已經有了,再加一條是重複不是涵蓋。

    def test_the_message_names_both_line_numbers(self, tmp_path):
        """**票 83 驗收條件的另一半**,逐字:「訊息**點名是哪個號、哪兩行**」。

        「哪個號」上面兩條已經問過(`F-007` / `TSI-001`);
        **「哪兩行」到今天為止沒有任何斷言碰過** —— 而產生它的是三行程式碼
        (`enumerate(lines, 1)`、`dupes.setdefault(...)`、`"、".join(...)`)。

        `"F-007" in v[0]` 在行號整個算錯時**仍然會綠**(`F-105`:
        訊息類斷言有兩種,只有一種抓得到判定壞掉)。
        """
        path = self._log(tmp_path, "## F-007 甲\n\n內文\n\n## F-007 乙\n")
        v = gate.check_friction_numbers(path)
        assert v, "撞號沒有被抓到"
        assert "第 1 行" in v[0] and "第 5 行" in v[0], (
            "訊息沒有點名兩個行號 —— 只說『有撞號』等於要人自己再掃一次:%r" % v[0])

    def test_the_message_lists_every_line_when_a_number_repeats_three_times(
            self, tmp_path):
        """三次撞號時**三個行號都要在訊息裡**,不是只有頭尾。

        少一個行號的話,人會照著訊息去改那兩處,而第三處留在原地 ——
        **一份修好一半的 log,與一份沒撞號的 log,下一次掃描的結果相同。**
        """
        path = self._log(tmp_path,
                         "## F-007 甲\n\n## F-007 乙\n\n## F-007 丙\n")
        v = gate.check_friction_numbers(path)
        assert v, "三次撞號沒有被抓到"
        for expected in ("第 1 行", "第 3 行", "第 5 行"):
            assert expected in v[0], (
                "三次撞號的訊息漏了 %s:%r" % (expected, v[0]))

    def test_three_occurrences_are_one_finding_not_three(self, tmp_path):
        """**同一個號撞三次是【一筆】發現。**

        分成三筆的話,一份 log 裡一個號撞十次會印十則幾乎相同的訊息,
        而**吵到讀不下去的訊息,人會照著繞而不是照著修**(`F-031`)。
        判準是「哪個號撞了」,不是「撞了幾次」。
        """
        path = self._log(tmp_path,
                         "## F-007 甲\n\n## F-007 乙\n\n## F-007 丙\n")
        v = gate.check_friction_numbers(path)
        assert len(v) == 1, "同一個號撞三次應該是一筆發現,實際 %d 筆:%r" % (len(v), v)

    def test_two_distinct_collisions_produce_two_findings(self, tmp_path):
        """兩個**不同的號**各自撞 → **兩筆**發現。

        `for num in sorted(dupes)` 這個迴圈在現有測試裡**永遠只跑一圈** ——
        每一份 tmp log 都只有一個撞號。只跑一圈的迴圈與沒有迴圈,
        在測試輸出上長得一樣。
        """
        path = self._log(tmp_path,
                         "## F-001 甲\n\n## F-002 乙\n\n"
                         "## F-001 丙\n\n## F-002 丁\n")
        v = gate.check_friction_numbers(path)
        assert len(v) == 2, "兩個號各自撞應該是兩筆發現,實際 %d 筆:%r" % (len(v), v)
        assert "F-001" in v[0] + v[1] and "F-002" in v[0] + v[1], v

    def test_the_findings_are_ordered_by_number(self, tmp_path):
        """**輸出順序是決定性的**(`sorted(dupes)`),不是 dict 的插入順序。

        這裡刻意讓 `F-002` **先**撞完、`F-001` **後**撞完 ——
        照插入順序的話 `F-002` 會排在前面。
        順序不決定性的話,兩次跑同一份 log 可以給出兩種輸出,
        而**比對輸出的人會以為 log 變了**。
        """
        path = self._log(tmp_path,
                         "## F-002 甲\n\n## F-002 乙\n\n"
                         "## F-001 丙\n\n## F-001 丁\n")
        v = gate.check_friction_numbers(path)
        assert len(v) == 2, v
        assert "F-001" in v[0], "排序不是照號碼:第一筆應該是 F-001,實際 %r" % v[0]
        assert "F-002" in v[1], "排序不是照號碼:第二筆應該是 F-002,實際 %r" % v[1]

    # ── 判定矩陣:以下四條釘的是 `gate.py` 那一份正則自己 ──────────────
    #
    # **這四個條件今天只在 `.claude/portable/` 那一側有測試**
    # (`tests/test_friction_heading.py`),而兩份是各自獨立的字面,不是同一個物件。
    # `TestBothHeadingCriteriaAgree` 做的是對帳,而對帳綠有兩種來源:
    # 兩邊都對,以及**兩邊一起錯** —— 那個 class 自己的 docstring 就寫過這句。
    # 它「釘住」用的 5 筆語料裡**沒有** `###`、沒有無空白、沒有邊界案例。

    def test_a_third_level_heading_is_not_an_issuing_line(self, tmp_path):
        """`###` 不是發號位置 —— **三級標題是段落,不是條目**。

        本庫實際有一行 `### F-058 家族註記(票 42)`,而 `## F-058` 也在同一份
        log 裡。判準放寬到 `#+` 的話,那一對會變成撞號 ——
        **而它們本來就是同一則的標題與子節。**
        """
        path = self._log(tmp_path, "### F-001 甲\n\n### F-001 乙\n")
        assert gate.check_friction_numbers(path) == []

    def test_a_heading_without_a_letter_prefix_is_not_an_issuing_line(self, tmp_path):
        """**前綴必須是字母。** 純數字標題(`## 118 甲`)是散文,不是發號。

        少了這個條件,一份用數字當小節編號的文件會整份被判成撞號 ——
        而那種誤報會讓整條規則被關掉(`CLAUDE.md`:錯在權威層等於擋住做對事的人)。
        """
        path = self._log(tmp_path, "## 118 甲\n\n## 118 乙\n")
        assert gate.check_friction_numbers(path) == []

    def test_a_longer_token_is_not_swallowed(self, tmp_path):
        """**邊界**:`## F-118x` 不得被讀成 `F-118`。

        少了尾端邊界,一個打錯的號會靜靜地被算成另一個號 ——
        於是這裡會報一個**不存在的撞號**,而人會去改一則本來沒問題的紀錄。
        """
        path = self._log(tmp_path, "## F-118 甲\n\n## F-118x 乙\n")
        assert gate.check_friction_numbers(path) == []

    def test_a_hash_without_a_space_is_not_an_issuing_line(self, tmp_path):
        """`##F-001`(無空白)不是 markdown 標題,所以也不是發號行。

        判準是 `^##\\s+` —— `\\s+` 的 `+` 不是裝飾:
        少了它,任何以 `##` 開頭的字串都會被當成標題行掃描。
        """
        path = self._log(tmp_path, "##F-001 甲\n\n##F-001 乙\n")
        assert gate.check_friction_numbers(path) == []


class TestUpstreamMustNotBeInShadowMode:
    """票 89 第 1 條 —— **上游 repo 不得處於影子狀態**,而違反的當下要有東西叫。

    由來:`docs/audits/2026-08-28-f110-inventory.md` 第 1 條。
    `.dev/shadow.json` 存在 -> `shadow_active()` 為真 -> 整個上游閘門從「擋」
    退回「只記不擋」;而**那不是錯誤狀態,那是影子模式的正常狀態**,
    所以到今天為止沒有任何東西會說。票 49 的攔截帳本整個建立在
    「上游全程 enforce」這個前提上 —— 這一項被好心補上,那本帳從此
    一筆都不會再長,而它看起來仍然正常。

    ## 錨與威脅模型(票 89 一之三,寫進測試免得下一個人以為它更強)

    錨是 `read_upstream_root() == ROOT`。它**擋得住「好心補上」,
    擋不住「決定要關掉」** —— `~/.claude/upstream-roots.txt` 沒有 G1 保護,
    改一行就能讓本規則失效。那是宣告的守備範圍,不是缺陷;
    已知缺口的票號是票 89 自己,出口是第二階段(git 背書的錨,9/11)。

    ## 三條硬條件,每一條都有自己的測試

    1. **不得對下游生效** —— `shadow.json` 存在是影子模式的**合法**狀態。
       一條「一律擋」的實作會在三天後擋到每一個開了影子的下游,
       **而它會讓正控全綠**(票 22 Phase 2 第 7 條紅燈的同一句話)。
    2. **錨讀不到時不擋,但出聲** —— fail-closed 會擋到每一個沒有那個檔的下游;
       fail-open 是 `F-042` 家族(守衛的「不在」與「放行」長得一樣)。
       所以兩個斷言都要:**不擋** 且 **有那一行輸出**。
       只驗「不擋」的話,一個什麼都不做的實作也會綠。
    3. **影子分支不得吞掉這一條** —— 這是最容易寫錯的一格:
       `mode_pre_commit` 在有違規且 `shadow_active()` 為真時會寫 shadow-log 並回 0。
       本規則若走那條路,它**永遠不可能觸發** —— 它要偵測的正是影子開著這件事。
    """

    def _anchor(self, monkeypatch, value):
        monkeypatch.setattr(gate, "read_upstream_root", lambda: value)

    def _shadow_file(self, monkeypatch, tmp_path, exists):
        p = tmp_path / "shadow.json"
        if exists:
            io.open(p, "w", encoding="utf-8").write('{"until": "2099-01-01"}')
        monkeypatch.setattr(gate, "SHADOW_STATE", str(p))
        return p

    # ── 正控 ──────────────────────────────────────────────────────────
    def test_upstream_with_a_shadow_state_file_is_a_violation(
            self, monkeypatch, tmp_path):
        self._anchor(monkeypatch, gate.ROOT)
        self._shadow_file(monkeypatch, tmp_path, exists=True)
        v, note = gate.upstream_shadow_violation()
        assert v, "上游有 shadow.json 竟然沒有違規"
        assert "shadow.json" in v

    # ── 🔴 反控:不得對下游生效 ────────────────────────────────────────
    def test_a_downstream_repo_with_a_shadow_state_file_is_untouched(
            self, monkeypatch, tmp_path):
        """**少了這一條,一個「一律擋」的實作也會讓正控全綠。**"""
        self._anchor(monkeypatch, str(tmp_path / "some-other-upstream"))
        self._shadow_file(monkeypatch, tmp_path, exists=True)
        v, note = gate.upstream_shadow_violation()
        assert v is None, "下游開影子被擋了 —— 那是影子模式的合法狀態:%r" % (v,)

    def test_upstream_without_the_file_is_clean(self, monkeypatch, tmp_path):
        self._anchor(monkeypatch, gate.ROOT)
        self._shadow_file(monkeypatch, tmp_path, exists=False)
        assert gate.upstream_shadow_violation() == (None, None)

    def test_the_anchor_tolerates_a_different_separator(
            self, monkeypatch, tmp_path):
        """指標檔寫的是正斜線(`UPSTREAM_ROOT=C:/projects/...`,由人手維護),
        而 `ROOT` 在 Windows 上是反斜線。**不正規化就永遠比不中**,
        於是規則在它唯一該生效的 repo 上靜默失效。

        ⚠ **在 POSIX 上這一條是恆真的**(`os.sep` 就是 `/`,替換後沒變)——
        寫在這裡是因為它守的是 Windows 那一面,而上游就住在 Windows。
        **不要把它讀成「分隔符處理在所有平台都驗過了」。**
        """
        self._anchor(monkeypatch, gate.ROOT.replace(os.sep, "/"))
        self._shadow_file(monkeypatch, tmp_path, exists=True)
        v, _ = gate.upstream_shadow_violation()
        assert v, "只差分隔符寫法就比不中 —— 錨在它唯一該生效的地方失效了"

    def test_case_folding_follows_the_platform_not_a_guess(
            self, monkeypatch, tmp_path):
        """大小寫**跟著平台走**,不是無條件折疊。

        本條的第一版寫死了「大寫也要比中」,那是**把開發機的檔案系統
        當成世界的性質** —— 本機(Windows)全綠,CI(Linux)當場紅。
        `F-109` 家族的另一面:那不是一個會過期的數字,是一個**只在一種平台成立的斷言**。

        - **Windows**:檔案系統不分大小寫 -> 大寫寫法**必須**比中
        - **POSIX**:分大小寫 -> 大寫是**另一個路徑**,**必須不比中**

        後者不是將就,是正確性:無條件折疊會讓一個 Linux 下游
        (路徑只差大小寫)被誤判成上游,然後被擋。

        ⚠ **不用 `os.path.normcase` 去算期望值** —— 那是拿衍生欄位
        驗它的來源欄位,恆真(`F-114`)。這裡把兩個平台的**語意**分別寫死。
        """
        self._anchor(monkeypatch, gate.ROOT.replace(os.sep, "/").upper())
        self._shadow_file(monkeypatch, tmp_path, exists=True)
        v, _ = gate.upstream_shadow_violation()
        if os.name == "nt":
            assert v, "Windows 檔案系統不分大小寫,大寫寫法竟然比不中"
        else:
            assert v is None, (
                "POSIX 分大小寫,大寫是另一個路徑,不得比中 —— "
                "無條件折疊會把 Linux 下游誤判成上游")

    def test_a_genuinely_different_path_never_matches(
            self, monkeypatch, tmp_path):
        """**平台無關的那一條**:真的不同的路徑,任何平台都不得比中。

        上面兩條各自只在一種平台上有內容;少了這一條,
        一個「永遠回 True」的 `_same_path` 在**兩邊都會綠**。
        """
        self._anchor(monkeypatch, str(tmp_path / "definitely-not-the-upstream"))
        self._shadow_file(monkeypatch, tmp_path, exists=True)
        v, note = gate.upstream_shadow_violation()
        assert v is None and note is None

    # ── 🔴 錨讀不到:不擋,但出聲 ──────────────────────────────────────
    def test_an_unreadable_anchor_does_not_block(self, monkeypatch, tmp_path):
        """fail-closed 會擋到每一個沒有 `upstream-roots.txt` 的下游 = 災難。"""
        self._anchor(monkeypatch, None)
        self._shadow_file(monkeypatch, tmp_path, exists=True)
        v, _ = gate.upstream_shadow_violation()
        assert v is None, "錨讀不到就擋,會擋掉每一個下游"

    def test_an_unreadable_anchor_still_says_so(self, monkeypatch, tmp_path):
        """**而它不得靜默** —— 靜默失效是 `F-042` 家族。"""
        self._anchor(monkeypatch, None)
        self._shadow_file(monkeypatch, tmp_path, exists=True)
        _, note = gate.upstream_shadow_violation()
        assert note, "錨讀不到卻什麼都沒說 —— 規則靜默失效"
        assert "未生效" in note

    def test_the_note_is_silent_when_there_is_nothing_to_say(
            self, monkeypatch, tmp_path):
        """錨讀不到**而且**沒有 shadow.json 時不必吵 ——
        一個每次都印的提醒會訓練人忽略它(F-031)。"""
        self._anchor(monkeypatch, None)
        self._shadow_file(monkeypatch, tmp_path, exists=False)
        assert gate.upstream_shadow_violation() == (None, None)

    # ── 接線:規則真的在通行路上 ──────────────────────────────────────
    def test_the_rule_is_actually_invoked_at_the_authoritative_layer(
            self, monkeypatch):
        """**最強的那一條**(照 R6 / R9 的先例):驗規則真的被 pre-commit 呼叫,
        不只是函式回對值。沒有這條的話,一個寫好卻沒接上的檢查會全綠 ——
        票 27 逐字:手動呼叫一支檢查,不等於那支檢查在通行路上。"""
        monkeypatch.setattr(gate, "upstream_shadow_violation",
                            lambda: ("假違規:上游處於影子狀態", None))
        assert gate.mode_pre_commit() == 1, \
            "pre-commit 沒有呼叫 upstream_shadow_violation"

    def test_the_rule_is_actually_invoked_at_the_sentinel(
            self, monkeypatch):
        """前哨也要接 —— **權威層才擋就已經太晚**:
        影子開著的那段期間,agent 的每一次寫入都已經不受 enforce 保護了。"""
        monkeypatch.setattr(gate, "upstream_shadow_violation",
                            lambda: ("假違規:上游處於影子狀態", None))

        class _Stdin:
            buffer = io.BytesIO(json.dumps(
                {"tool_name": "Write",
                 "tool_input": {"file_path": "README.md", "content": "x"}}
            ).encode("utf-8"))

        monkeypatch.setattr(gate.sys, "stdin", _Stdin())
        assert gate.mode_hook() == 2, "前哨沒有呼叫 upstream_shadow_violation"

    # ── 🔴 影子分支不得吞掉它 ────────────────────────────────────────
    def test_shadow_mode_cannot_swallow_this_particular_violation(
            self, monkeypatch):
        """**它要偵測的正是影子開著這件事。**

        走一般 `violations` 那條路的話:影子開著 -> 寫 shadow-log -> 回 0,
        於是這條規則**永遠不可能觸發**,而測試若只驗函式回傳值會全綠。
        """
        monkeypatch.setattr(gate, "upstream_shadow_violation",
                            lambda: ("假違規:上游處於影子狀態", None))
        monkeypatch.setattr(gate, "shadow_active", lambda *a, **k: True)
        assert gate.mode_pre_commit() == 1, \
            "影子分支把「上游處於影子狀態」這條違規吞掉了"

    # ── 活體正對照 ────────────────────────────────────────────────────
    def test_the_live_repo_is_not_in_shadow_mode(self):
        """對**本庫現行狀態**跑一次 —— 正對照,不是只測 tmp_path。

        這一條同時是那份「刻意不存在」的機器化身:
        `docs/machine-init.md:170-186` 與交接檔 :110-130 說它必須不存在,
        而在本條之前**沒有任何東西在看**。

        ⚠ `SHADOW_STATE` 被 conftest 的 autouse fixture 指到 tmp,
        所以這裡讀**真實路徑**,不讀模組常數 —— 否則驗的是 fixture,不是 repo。
        """
        real = os.path.join(str(ROOT), ".dev", "shadow.json")
        assert not os.path.exists(real), (
            "上游出現了 .dev/shadow.json —— 整個閘門會從『擋』退回『只記不擋』,"
            "而票 49 的攔截帳本會靜默停止成長。見 docs/machine-init.md:170")


# ═══════════════════════════════════════════════════════════════════════════
# 票 99 裁 A —— 「當前 stage 允許寫 src 嗎」要有一支具名函式
#
# 現況:這個判準 inline 在 `check()` 裡(`:1870` 的 set comprehension、
# `:1891` 的 `first_writable`),**沒有名字**。
# 於是任何想問這個問題的 consumer(票 99 的 `status`)只有兩條路:
#   1. 拿候選路徑一條一條餵 `check()` —— 那是用「擋不擋」去反推「能不能寫」
#   2. 自己組一份判定 —— **那就長出第二份判準**,而兩份必然漂開(F-058 家族)
# 兩條都不行,所以抽一支具名函式出來,`check()` 改呼叫它。
#
# 🔴 本區塊寫下的當下,`gate.stage_allows_src_write` **不存在** —— 這是票 99 的
#    第二筆紅燈,形狀是 AttributeError。
# ═══════════════════════════════════════════════════════════════════════════

class TestStageAllowsSrcWrite:
    """裁 A:把 `check()` 裡的 inline 判準抽成 `gate.stage_allows_src_write(stage_id)`。

    **這一組不驗新行為。** R2 的行為由既有那些測試守著,抽函式不得改變它們 ——
    本組驗的是「那個判準有沒有名字、拿不拿得到、壞掉時往哪一邊倒」。
    """

    def _stages_yaml(self, tmp_path, text):
        p = tmp_path / "pipeline-stages.yaml"
        with io.open(str(p), "w", encoding="utf-8") as f:
            f.write(text)
        return str(p)

    # ── 甲、宣告了就是 True,沒宣告就是 False ──────────────────────────
    def test_a_stage_that_declares_it_may_write_source(self, tmp_path, monkeypatch):
        """守的是判準 2(只呼叫不重述):consumer 要問這件事得有一支函式可呼叫。"""
        monkeypatch.setattr(gate, "STAGES_DEF", self._stages_yaml(tmp_path, u"""
stages:
  - id: X
    skill: implement
    allows_src_write: true
  - id: Y
    skill: grill
"""))
        assert gate.stage_allows_src_write("X") is True

    def test_a_stage_without_the_field_may_not(self, tmp_path, monkeypatch):
        """守的是判準 2:欄位缺席不等於允許 —— 那是 R2 的整個重點。"""
        monkeypatch.setattr(gate, "STAGES_DEF", self._stages_yaml(tmp_path, u"""
stages:
  - id: X
    skill: implement
    allows_src_write: true
  - id: Y
    skill: grill
"""))
        assert gate.stage_allows_src_write("Y") is False

    # ── 乙、不認得的站名 -> False ─────────────────────────────────────
    def test_an_unknown_stage_is_refused(self, tmp_path, monkeypatch):
        """守的是判準 4(算不出來不得寫成通過)—— 這一層的 fail-closed 面。

        `pipeline.json` 是可被手改的執行期狀態,打錯一個字就會出現一個
        定義檔裡沒有的站名。**那時的正確答案是「不准寫」,不是「查無此站所以隨便」。**
        """
        monkeypatch.setattr(gate, "STAGES_DEF", self._stages_yaml(tmp_path, u"""
stages:
  - id: X
    skill: implement
    allows_src_write: true
"""))
        assert gate.stage_allows_src_write("no_such_stage") is False
        assert gate.stage_allows_src_write(gate.UNREADABLE_STAGE) is False

    # ── 丙、定義檔讀不到 -> False ─────────────────────────────────────
    def test_an_unreadable_definition_refuses(self, tmp_path, monkeypatch):
        """守的是判準 4:`load_stage_defs()` 回 err 時一律 False。

        `load_stage_defs` 自己已經 fail-closed(回 `stages=[]` + err),
        而**「呼叫端有沒有照著倒」是另一件事** —— 一個把空清單讀成
        「沒有任何限制」的呼叫端會把 fail-closed 翻成 fail-open,而且完全無聲。
        """
        monkeypatch.setattr(gate, "STAGES_DEF", str(tmp_path / "no-such-file.yaml"))
        stages, _flow, err = gate.load_stage_defs()
        assert err, "前提不成立:這個路徑應該讀不到"
        assert stages == []
        assert gate.stage_allows_src_write("X") is False

    # ── 丁、結構紅:`check()` 不得再留第二份判準 ───────────────────────
    def test_check_no_longer_carries_an_inline_copy(self):
        """**守的是「不長第二份判準」,不是行為。**

        抽函式最常見的失敗不是抽錯,是**抽了但沒接** —— 新函式在旁邊,
        `check()` 照舊用它自己那份 inline 的。那時甲乙丙三條全綠
        (新函式自己是對的),而生產路徑一個字都沒變。
        **行為測試看不見這種失敗,因為行為確實沒變。**

        ⚠ 這條驗的是原始碼字面,所以它會被無害的改寫弄紅(例如換個變數名)。
        那是刻意的代價:字面比對誤報的方向是「叫一次去看一眼」,
        而漏報的方向是「第二份判準活著而沒有人知道」。
        """
        import inspect
        src = inspect.getsource(gate.check)
        assert 'allows_src_write")}' not in src, (
            "`check()` 裡還留著 inline 的 set comprehension —— "
            "抽出來的函式沒有被接上,生產路徑仍然走第二份判準")


# ── 票 102:R1 主路徑的正對照 ────────────────────────────────────────────
#
# 清冊(`docs/audits/2026-08-16-rule-inventory.md:415`)逐字:
#   「**(b) 成立** —— ⚠ 但**只涵蓋 fail-closed 分支**;
#     **主路徑(規格書含程式碼 → 擋)沒有正控**。
#     `CORPUS` 裡有那個輸入,但只餵給結構不變式與 trace 測試」
#
# **語料在、規則在、測試在,而「這條規則會擋」從來沒有被任何一條斷言問過。**
# 本檔第 44 / 46 行那兩條夾程式碼的規格書語料,只流向
# `test_coverage_no_rule_is_skipped_at_the_authoritative_layer`(比 trace 集合差)、
# `test_every_divergence_is_declared_by_its_rule`(只在兩層分歧時才斷言)——
# 兩條都不看 `msg` 裡有沒有 `R1`。
#
# **口徑(票 102 裁三,逐字)**:
#   正控 18 條 = 16(8 樣式 × 2 路徑,content 直給)
#   + 2(每條路徑各一條 content=None 真寫檔到 tmp_path 再讀)。


@pytest.fixture
def spec_root(tmp_path, monkeypatch):
    """把 ROOT 指到 tmp_path,路徑一律給絕對的。

    理由與 `test_gate_boundaries.py:46-48` 那格相同:`rel()` 走 `abspath`,
    相對路徑會以 cwd 為基準而不是 ROOT,收斂之後變成 `../..` 開頭,
    被「repo 外不管」那條(`gate.py:1839`)提早放行 —— **測試會綠,而它沒測到東西**。
    """
    monkeypatch.setattr(gate, "ROOT", str(tmp_path))
    return tmp_path


# `CODE_IN_SPEC_RE`(`gate.py:186`)的八個分支,一個樣式一列。
# 第一支是圍籬(不受 `^` 約束,任何位置都算),其餘七支要 `^\s*<關鍵字>\s`。
# **樣本刻意各自只命中自己那一支**:`from os import path` 的 `import`
# 不在行首,所以它是 `from` 的樣本,不是 `import` 的 —— 突變時才歸得了因。
R1_CODE_SHAPES = [
    ("fence", "## 問題\n```python\nprint(1)\n```\n"),
    ("def", "## 問題\ndef f():\n    pass\n"),
    ("class", "## 問題\nclass A:\n    pass\n"),
    ("import", "## 問題\nimport os\n"),
    ("from", "## 問題\nfrom os import path\n"),
    ("function", "## 問題\nfunction f() { return 1 }\n"),
    ("const", "## 問題\nconst x = 1\n"),
    ("let", "## 問題\nlet x = 1\n"),
]

# `gate.py:1845` 的兩條路徑判定,一條一列。
# A 是**前綴**(底下任意深度);B 是**完整比對**(`[^/]+` 只吃一層、檔名必須是 spec.md)。
R1_SPEC_PATHS = ["docs/specs/x.md", ".scratch/f/spec.md"]

R1_FENCE = "## 問題\n```python\nprint(1)\n```\n"


class TestASpecCarryingCodeIsBlocked:
    """**正控 16 條:8 樣式 × 2 路徑,content 直給。**

    這一批走的是**前哨**那條路:呼叫端把內容交出來,gate 不必碰磁碟。
    """

    @pytest.mark.parametrize("rel_path", R1_SPEC_PATHS)
    @pytest.mark.parametrize("shape,body", R1_CODE_SHAPES,
                             ids=[s for s, _ in R1_CODE_SHAPES])
    def test_every_code_shape_is_blocked_on_every_spec_path(
            self, spec_root, shape, body, rel_path):
        msg = gate.check(str(spec_root / rel_path), body)
        assert msg and "R1" in msg, (
            "規格書夾了 `%s` 卻沒有被 R1 擋:path=%s msg=%r —— "
            "**這正是清冊 :415 說的那一格**:語料在 CORPUS 裡,而沒有斷言問過它"
            % (shape, rel_path, msg))


class TestASpecReadFromDiskIsBlockedToo:
    """**正控 2 條:每條路徑各一,`content=None` 真寫檔再讀。**

    `content is None` 是 **commit 那一側**的形態:內容不由呼叫端給,
    由 gate 自己 `io.open(os.path.join(ROOT, r))` 讀(`gate.py:1848-1857`)。

    **它與既有那條 fail-closed 正控是相反的一半**:
    `test_gate_boundaries.py:39-50` 驗的是「讀**不到**時擋」,
    本批驗的是「讀**得到**而且裡面有碼時擋」——
    而後者在票 102 之前沒有任何斷言。
    """

    @pytest.mark.parametrize("rel_path", R1_SPEC_PATHS)
    def test_a_spec_on_disk_with_code_is_blocked(self, spec_root, rel_path):
        p = spec_root / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(R1_FENCE, encoding="utf-8")
        msg = gate.check(str(p), None)
        assert msg and "R1" in msg, (
            "從磁碟讀到的規格書夾了程式碼卻放行:path=%s msg=%r" % (rel_path, msg))
        assert "fail-closed" not in msg, (
            "擋是擋了,**但走的是 fail-closed 那一支** —— 那條已經有正控了,"
            "而本條要驗的是「讀得到且有碼」那一格:msg=%r" % msg)


class TestR1DoesNotBlockWhatItShouldNotSee:
    """**反控 4 條。** 每一條都是一個「把判定弄寬」會紅的方向。

    正控只證明規則會動,不證明它動得**不多**:一支「凡是 `docs/specs/`
    一律擋」的實作會讓上面 18 條全綠,而那是把功能弄壞,不是修好。
    """

    def test_a_spec_with_only_prose_is_not_blocked(self, spec_root):
        """反控 1:純散文的規格書不得被擋(語料同 CORPUS 第 43 / 45 行)。"""
        for rel_path in R1_SPEC_PATHS:
            msg = gate.check(str(spec_root / rel_path), "## 問題\n只有散文。")
            assert msg is None, (
                "純散文的規格書被擋了:path=%s msg=%r —— "
                "少了這條,一支「凡是規格書路徑一律擋」的實作也會讓正控全綠"
                % (rel_path, msg))

    def test_a_document_that_is_not_a_spec_never_enters_the_rule(self, spec_root):
        """反控 2:非規格書路徑不進判定。

        `friction-log.md` 那一格是實害不是假想:它**正是寫閘門行為的文件**,
        而 `import` 這個字會出現在裡面。同一個形狀已經咬過一次 ——
        `_quote_spans()` 的 docstring 逐字:「G1 擋住了『描述 G1 擋了什麼』」。
        """
        cases = [("docs/agents/friction-log.md", "import 這個字不是程式"),
                 (".scratch/f/issues/01-x.md", R1_FENCE)]
        for rel_path, body in cases:
            msg = gate.check(str(spec_root / rel_path), body)
            assert "R1" not in (msg or ""), (
                "非規格書的文件進了 R1 的判定:path=%s msg=%r" % (rel_path, msg))

    def test_a_neighbouring_directory_name_is_not_the_spec_dir(self, spec_root):
        """反控 3:**前綴要帶邊界**。

        現行 `startswith("docs/specs/")` 帶尾斜線,所以 `docs/specsx/` 不命中。
        本條釘住它:改成 `startswith("docs/specs")` 的那一天它會紅。
        同族:`is_source_path` 的 `docsx/thing.py`(本檔 :262)、
        `g1_guard` 的「前綴要帶邊界」、`CLAUDE.md` 的常駐檢查項。
        """
        msg = gate.check(str(spec_root / "docs/specsx/x.md"), R1_FENCE)
        assert "R1" not in (msg or ""), (
            "`docs/specsx/` 被當成規格書目錄 —— 前綴少了邊界:msg=%r" % msg)

    def test_the_scratch_form_matches_exactly_one_level(self, spec_root):
        """反控 4:`.scratch` 那條只吃一層(`[^/]+`),`.scratch/a/b/spec.md` 不進判定。

        ⚠ **它釘的是現行行為,不是理想行為;要不要支援多層是另一件事,本票不裁。**

        寫這一句的理由:一條釘住現行行為的測試,與一條釘住正確行為的測試
        **長得一模一樣**。不標明的話,下一個想放寬 `.scratch` 判定的人
        會看到它紅,然後以為自己違反了一條設計決定 —— 而它只是現況的快照。
        """
        msg = gate.check(str(spec_root / ".scratch/a/b/spec.md"), R1_FENCE)
        assert "R1" not in (msg or ""), (
            "`.scratch/a/b/spec.md` 進了 R1 的判定,而現行正則只吃一層:msg=%r" % msg)


# ─────────────────────────────────────────────────────────────────────────────
# 票 10 —— R2 的內容豁免(權威層):與上游 provenance 釘住的物件逐位元組相同的
# staged 檔案放行。**綁內容,不綁站別 —— 沒有窗口,就沒有忘記關窗這個失效模式。**
# ─────────────────────────────────────────────────────────────────────────────

UP_SRC = "def f():\n    return 1\n"

# 在 fixture 換掉 `gate.load_stage` 之前先抓住真的那一支 —— ⑥ 要它去真的讀
# pipeline.json,否則「不寫」那條斷言測的是一個根本沒被開啟過的檔案。
_REAL_LOAD_STAGE = gate.load_stage


class TestR2AcceptsAnUpstreamIdenticalStagedFile:
    """票 10:**豁免綁內容,不綁站別。**

    要解的事:同步要寫 `.claude/portable/*.py`、`.claude/hooks/*.py`,而那些在
    目標 repo 是原始碼;下游停在前置站時 R2 擋 commit。紙上流程是「人手動把
    `current_stage` 改成 implement,做完再改回去」—— 實測窗口 57 分 38 秒、
    逾 1 小時 08 分各一次,而**窗口期間 R2 對整個 repo 都是開的**,不只對同步的那些檔案。

    內容豁免沒有窗口:只放行「與上游那個 commit 的物件逐位元組相同」的檔案,
    差一個位元組就回到 R2 正常判定。**無法自我服務** —— 偽造要先改上游。

    **判定對象是 staged 的位元組**(`git show :<path>`),不是工作樹:
    commit 要判的是**要進 commit 的那一份**(F-046 那條判準換一個時點)。

    ## 站別為什麼用 `spec` 而不是票面寫的 `review`

    票面 §設計 (g) 的 ① 寫「停在 review」,那是**前哨**的擋法。
    本刀只做權威層,而 `at_commit` 的 R2 只擋**前置站**
    (`grill` / `spec` / `tickets`;`review` / `arch` / `idle` 在提交時本來就放行,
    ADR 0005)—— 拿 `review` 當正控的話,那條測試從第一天就是綠的,
    **證明不了任何東西**。改用 `spec`,紅燈才對著本票要加的分支。
    """

    @pytest.fixture()
    def world(self, tmp_path, monkeypatch):
        """上游與下游兩個**真的** git repo(判定要對到真的 git 物件)。

        `core.autocrlf false`:行尾那一格(③)要真的測到正規化 ——
        讓 git 在 `add` 時自己把 CRLF 轉掉的話,兩邊在**進 index 之前**就一樣了,
        於是把正規化整段拿掉那條測試照樣綠。
        """
        up, down = tmp_path / "up", tmp_path / "down"
        for r in (up, down):
            r.mkdir()
            for c in ("init -q", "config user.email t@t", "config user.name t",
                      "config core.autocrlf false"):
                subprocess.run(["git"] + c.split(), cwd=str(r), capture_output=True)

        (up / "pkg").mkdir()
        io.open(up / "pkg" / "thing.py", "w", encoding="utf-8",
                newline="\n").write(UP_SRC)
        subprocess.run(["git", "add", "-A"], cwd=str(up), capture_output=True)
        subprocess.run(["git", "commit", "-qm", "up"], cwd=str(up),
                       capture_output=True)
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(up),
                             capture_output=True).stdout.decode().strip()

        (down / "pkg").mkdir()
        (down / "tests").mkdir()
        io.open(down / "tests" / "test_thing.py", "w",
                encoding="utf-8").write("x = 1\n")
        (down / ".dev").mkdir()

        monkeypatch.setattr(gate, "ROOT", str(down))
        monkeypatch.setattr(gate, "PROVENANCE", str(down / ".dev" / "provenance.jsonl"))
        monkeypatch.setattr(gate, "RUN_LOG", str(down / ".dev" / "test-runs.jsonl"))
        monkeypatch.setattr(gate, "EXEMPTION_LOG",
                            str(down / ".dev" / "gate-exemptions.jsonl"))
        monkeypatch.setattr(gate, "PIPELINE", str(down / ".dev" / "pipeline.json"))
        pointer = tmp_path / "upstream-roots.txt"
        io.open(pointer, "w", encoding="utf-8", newline="\n").write(
            "UPSTREAM_ROOT=%s\n" % str(up).replace("\\", "/"))
        monkeypatch.setattr(gate, "UPSTREAM_ROOTS", str(pointer))
        monkeypatch.setattr(gate, "load_stage", lambda: ("spec", "10"))
        monkeypatch.chdir(down)
        return up, down, sha

    def _stage(self, down, text, worktree=None):
        """把 `text` 放進 index。`worktree` 給值時,`add` 之後再把工作樹改成別的內容。

        `newline=""`:寫進去的就是傳進來的那些位元組,Python 不做行尾翻譯 ——
        ③ 那一格的整個判準就是行尾。
        """
        p = down / "pkg" / "thing.py"
        io.open(p, "w", encoding="utf-8", newline="").write(text)
        subprocess.run(["git", "add", "pkg/thing.py"], cwd=str(down),
                       capture_output=True)
        if worktree is not None:
            io.open(p, "w", encoding="utf-8", newline="").write(worktree)

    def _prov(self, down, **kw):
        rec = {"path": "pkg/thing.py", "upstream_path": "pkg/thing.py"}
        rec.update(kw)
        with io.open(down / ".dev" / "provenance.jsonl", "a",
                     encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # ── ① 正控 ────────────────────────────────────────────────────────────

    def test_a_staged_file_identical_to_the_upstream_object_passes_r2(self, world):
        """**本節的主張**:staged 內容 = 上游那個 commit 的同路徑物件 -> R2 不擋,
        而且**不必動 `pipeline.json`**。"""
        up, down, sha = world
        self._stage(down, UP_SRC)
        self._prov(down, upstream_commit=sha)
        msg = gate.check("pkg/thing.py", None, at_commit=True)
        assert not (msg and "[R2" in msg), msg

    # ── ② 反控:差一個位元組就回到 R2 正常判定 ─────────────────────────────

    def test_one_byte_of_drift_falls_back_to_normal_r2(self, world):
        """**反控,現行就綠** —— 它擋的是實作把「相同」寫鬆(例如比對工作樹、
        比對 provenance 自己宣稱的 hash、或前綴比對)之後正控仍然全綠。"""
        up, down, sha = world
        self._stage(down, UP_SRC + " ")
        self._prov(down, upstream_commit=sha)
        msg = gate.check("pkg/thing.py", None, at_commit=True)
        assert msg and "[R2" in msg, (
            "staged 與上游差一個位元組,R2 仍必須擋:msg=%r" % msg)

    # ── ③ 正控:只差行尾 ──────────────────────────────────────────────────

    def test_only_the_line_endings_differ(self, world):
        """`git show` 給的是物件裡的位元組(LF),autocrlf 的機器上工作樹是 CRLF ——
        不正規化的話這條規則在那些機器上**永遠不成立**(ADR F-0013 踩過)。

        失敗方向是「擋住做對事的人」,而那種規則最後會被整條關掉。
        """
        up, down, sha = world
        self._stage(down, UP_SRC.replace("\n", "\r\n"))
        self._prov(down, upstream_commit=sha)
        msg = gate.check("pkg/thing.py", None, at_commit=True)
        assert not (msg and "[R2" in msg), msg

    # ── ④ 正控:缺件一律不豁免,而且訊息點名缺的是哪一個 ───────────────────

    def test_a_missing_upstream_pointer_is_named(self, world, monkeypatch):
        up, down, sha = world
        self._stage(down, UP_SRC)
        self._prov(down, upstream_commit=sha)
        # 指標檔**不存在**,但名字是真的那一個 —— 訊息要印得出人該去建哪個檔。
        monkeypatch.setattr(gate, "UPSTREAM_ROOTS",
                            str(down / "gone" / "upstream-roots.txt"))
        msg = gate.check("pkg/thing.py", None, at_commit=True)
        assert msg and "[R2" in msg, msg
        assert "指標檔" in msg and "upstream-roots.txt" in msg, (
            "訊息沒說出缺的是指標檔 —— 人會去查站別,查不出所以然(票 13):msg=%r" % msg)

    def test_a_file_without_provenance_is_named(self, world):
        up, down, sha = world
        self._stage(down, UP_SRC)          # 不發 provenance
        msg = gate.check("pkg/thing.py", None, at_commit=True)
        assert msg and "[R2" in msg, msg
        assert "provenance" in msg, (
            "訊息沒說出這個檔案沒有同步紀錄:msg=%r" % msg)

    def test_an_unreachable_upstream_repo_is_named(self, world, monkeypatch):
        up, down, sha = world
        self._stage(down, UP_SRC)
        self._prov(down, upstream_commit=sha)
        pointer = down / "moved-pointer.txt"
        io.open(pointer, "w", encoding="utf-8", newline="\n").write(
            "UPSTREAM_ROOT=%s\n" % str(down / "no_such_repo").replace("\\", "/"))
        monkeypatch.setattr(gate, "UPSTREAM_ROOTS", str(pointer))
        msg = gate.check("pkg/thing.py", None, at_commit=True)
        assert msg and "[R2" in msg, msg
        assert "問不到" in msg, (
            "訊息沒說出上游那個物件問不到:msg=%r" % msg)

    # ── ⑤ 正控:帳本 ──────────────────────────────────────────────────────

    def test_the_exemption_is_recorded_with_its_own_reason(self, world):
        """豁免要逐筆記帳,而且要與 `gate-self-modification` 分得開 ——
        混在一起對帳又會得到一個解釋不了的數字(票 08)。

        `reason` 是**第四個**值,不是第二個:程式裡已經有 `ticket-declared`、
        `gate-self-modification`、`upstream-provenance`。

        斷言 `check()` 收進 bucket、不斷言它寫檔:票 08 之後判定是純函式,
        寫帳本屬於強制點(只有那裡知道「真的有人要寫」)。
        """
        up, down, sha = world
        self._stage(down, UP_SRC)
        self._prov(down, upstream_commit=sha)
        used = []
        gate.check("pkg/thing.py", None, at_commit=True, exemptions=used)
        reasons = [e.get("reason") for e in used]
        assert "upstream-identical" in reasons, used
        assert "gate-self-modification" not in reasons, used

        # 票 49 的讀法(逐筆對「哪一條規則、outcome 是什麼」)不得改變:
        # 欄位集合與 outcome 語意照舊,只是多一個 reason 值。
        ex = [e for e in used if e["reason"] == "upstream-identical"][0]
        rec = gate.exemption_record(ex, None, True, "spec", "10", None,
                                    tool="pre-commit")
        assert set(rec) == {
            "ts", "file", "module", "ticket", "stage", "declared_in", "reason",
            "tool", "outcome", "blocked_by", "at_commit", "content_hash",
            "result_hash", "changes_bytes"}, sorted(rec)
        assert rec["reason"] == "upstream-identical"
        assert rec["outcome"] == "granted" and rec["blocked_by"] is None, rec

    # ── ⑥ 反控:不必開窗 ──────────────────────────────────────────────────

    def test_the_exemption_never_writes_pipeline_json(self, world, monkeypatch):
        """**反控。** 票面要的是「不必改 `pipeline.json`」,那有兩半:

        **不寫** —— 位元組與 mtime 都不動;
        **判定不隨站別改變** —— 三個前置站都豁免,所以沒有窗口要開。

        「**不讀**」測不了,而且不該測:`load_stage()` 每一次判定都要讀它才知道
        停在哪一站,那是構造。硬要斷言「沒讀」等於要求閘門不知道自己在哪一站。
        """
        up, down, sha = world
        monkeypatch.setattr(gate, "load_stage", _REAL_LOAD_STAGE)
        self._stage(down, UP_SRC)
        self._prov(down, upstream_commit=sha)
        p = down / ".dev" / "pipeline.json"
        for stage in ("grill", "spec", "tickets"):
            io.open(p, "w", encoding="utf-8", newline="\n").write(
                json.dumps({"current_stage": stage, "ticket_id": "10"}))
            before = p.read_bytes()
            mtime = os.stat(str(p)).st_mtime_ns
            msg = gate.check("pkg/thing.py", None, at_commit=True)
            assert not (msg and "[R2" in msg), (stage, msg)
            assert p.read_bytes() == before, stage
            assert os.stat(str(p)).st_mtime_ns == mtime, stage

    # ── ⑦ 反控:判的是 staged,不是工作樹 ─────────────────────────────────

    def test_the_judgement_is_on_the_staged_bytes_not_the_worktree(self, world):
        """**兩個方向都要**:一個方向只證明「有時候對」。

        方向二(工作樹乾淨、staged 漂移)是關鍵的那一格 —— 照抄 R3 現有的
        `upstream_backed`(它讀工作樹,`gate.py:1735`)的話,方向一會綠、
        方向二會漏,而**正控全綠**。
        """
        up, down, sha = world
        self._prov(down, upstream_commit=sha)

        # 方向一:staged = 上游,工作樹漂移 -> 豁免(R3 可能另外擋,不是 R2 的事)
        self._stage(down, UP_SRC, worktree=UP_SRC + "# drift\n")
        msg = gate.check("pkg/thing.py", None, at_commit=True)
        assert not (msg and "[R2" in msg), ("方向一", msg)

        # 方向二:工作樹 = 上游,staged 漂移 -> 擋(讀工作樹的話這裡會綠)
        self._stage(down, UP_SRC + "# drift\n", worktree=UP_SRC)
        msg = gate.check("pkg/thing.py", None, at_commit=True)
        assert msg and "[R2" in msg, ("方向二", msg)


class TestTicketNumberMatchingCarriesABoundary:
    """票 77(由票 111 落地)—— 票號比對不帶邊界:別張票的宣告豁免得了當前票。

    ```
    gate.py  if not name.startswith(str(ticket_id)):
    ```

    `ticket_id="1"` 命中 `10-*.md`;`"0"` 命中 `01-*.md`。命中之後
    `committed_declaration()` 讀的是**那張票**的 `**Untested by decision:**`,
    於是**別張票裁過的模組**豁免掉當前票的 R3。

    **同一件事有三個實作,而修好的是另外兩個**:`status.py` 與 `mcp_server.py`
    都已改成 `str(票號) + "-"`,`status.py` 的 docstring 還逐字寫著
    「`gate.py` 有語意相同的一份,**本票不修它**」—— F-085 的知情版
    (修好一個命中之後沒找同類),而沒修的那一份在**權威層**。

    ⚠ **補零不在這一層**(照 `status.py` 的同一條判準):`"1"` 回 `None` 是
    **正確行為**,不是要靠補零去救 —— 下游 repo 不見得補零到兩位,
    把命名慣例埋進判定會在別的 repo 出錯。
    """

    @pytest.fixture()
    def repo(self, tmp_path, monkeypatch):
        """一個真的 git repo,票**已 commit**(判定綁 HEAD,票 24)。"""
        d = tmp_path / "docs" / "tickets" / "f"
        d.mkdir(parents=True)
        for name, mod in (("01-a.md", "mod01"), ("10-b.md", "mod10"),
                          ("11-c.md", "mod11"), ("111-d.md", "mod111")):
            io.open(d / name, "w", encoding="utf-8", newline="\n").write(
                "# t\n\n**Untested by decision:** %s\n" % mod)
        for c in ("init -q", "config user.email t@t", "config user.name t"):
            subprocess.run(["git"] + c.split(), cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "commit", "-qm", "t"], cwd=str(tmp_path),
                       capture_output=True)
        monkeypatch.setattr(gate, "ROOT", str(tmp_path))
        monkeypatch.chdir(tmp_path)
        return tmp_path

    # ── 正控(兩條,現行皆紅)────────────────────────────────────────────

    @pytest.mark.parametrize("ticket_id,wrong", [
        ("1", "10-b.md"),     # 「1」不得命中 10 / 11 / 111
        ("0", "01-a.md"),     # 「0」不得命中 01
    ])
    def test_a_number_never_matches_a_longer_one(self, repo, ticket_id, wrong):
        """**沒有 `<號>-` 開頭的票 = 沒有那張票**,不是「拿最像的那一張」。

        回錯一份票比回不出來糟得多:回不出來的人會再查,
        拿到一份看起來對的票的人不會(`status.py` 的同一句話)。
        """
        mods, rel = gate.ticket_untested_modules("f", ticket_id)
        assert rel is None, "票號 %r 命中了 %s(應為 None)" % (ticket_id, rel)
        assert mods == set(), mods

    # ── 反控(現行即綠,修完必須仍綠)──────────────────────────────────

    @pytest.mark.parametrize("ticket_id,expect_file,expect_mod", [
        ("11", "11-c.md", "mod11"),
        ("111", "111-d.md", "mod111"),
        ("01", "01-a.md", "mod01"),
    ])
    def test_an_exact_number_still_finds_its_own_ticket(self, repo, ticket_id,
                                                        expect_file, expect_mod):
        """**反控**:收窄的失敗方向是「誰也找不到自己的票」,而那會讓
        每一個合法的 `Untested by decision` 宣告失效 —— 擋住做對事的人。"""
        mods, rel = gate.ticket_untested_modules("f", ticket_id)
        assert rel and rel.endswith(expect_file), (ticket_id, rel)
        assert mods == {expect_mod}, (ticket_id, mods)


class TestInlineInterpretersAreUndecidable:
    """票 112 —— 前哨對**內嵌直譯器**一律擋並出聲。

    ## 要解的事

    R7 的**偵測**這一側是白名單:`WRITE_CONSTRUCT` 列舉動詞、`>`、`<<`。
    `python -c "open('pkg/evil.py','w').write('x')"` 三樣都不沾,
    於是**第一關就 return None**,連目標抽取那一層都走不到(2026-09-07 實測放行)。

    ## 判準:不可判定 ⇒ 擋,而且說「我判不出來」

    **不解析引號裡的程式。** 一個字串參數裡的 Python / JS 是**資料不是 shell 語法**;
    要判斷它會不會寫檔就得寫一個直譯器語意的分析器,而
    **「半套的解析器比零涵蓋更危險」是 R7 自己的原則**。
    所以本規則只問一件**字串答得出來**的事:
    **這一段的指令位置是不是直譯器,而且它帶了「後面是程式碼」的旗標。**

    ## 為什麼掛在 R7 底下(`[R7/內嵌直譯器]`)而不是新開一個 R 編號

    `rule_codes()` 的 docstring 自己寫了判準:
    「`[R2/commit]` 這種帶子類的歸到 R2 —— **子類是同一條規則的不同時點,不是新規則**」。
    本條與 R7 是**同一個對象**(工具呼叫)、**同一個出口**(改用檔案工具 / 腳本檔)、
    **同一層**(sentinel-only,ADR 0008)——
    差別只在「R7 判『寫到哪』,本條判『判不判得出來』」,那是同一條規則的兩個問法。

    另一半理由是機器面的:新開 `[R10]` 會讓 `rule_codes()` 多一條,而
    `verify_gates.py` 要求**每一條規則都有一個淨室情境**;
    R7 在那裡本來就是特例(前哨規則,commit 擋不到它)。
    硬造一個新編號等於在淨室裡多一個必須特判的規則,
    **而它與 R7 的特判理由一字不差** —— 那是同一件事的第二份定義(票 29 的形狀)。

    ## 位置

    依指令釘在 `tests/test_gate.py`。
    (R7 的**行為層**正負控慣例在 `tests/test_bash_write.py`;本 class 判的是
    `bash_write_violation` 的回傳,兩邊都跑得動,不搬既有那些。)
    """

    # ── ①② 正控:寫或讀都擋 —— 判準是「判不出來」,不是「有沒有在寫」──────

    @pytest.mark.parametrize("cmd,flag", [
        ('python -c "open(\'x\',\'w\').write(\'a\')"', "-c"),      # ① 會寫
        ('python -c "print(1)"', "-c"),                            # ② 純讀,一樣擋
        ('python3 -c "print(1)"', "-c"),
        ('py -c "print(1)"', "-c"),
        ('node -e "require(\'fs\').writeFileSync(\'x.py\',\'\')"', "-e"),
        ('node --eval "1+1"', "--eval"),
        ('perl -e "print 1"', "-e"),
        ('ruby -e "puts 1"', "-e"),
        ('powershell -Command "Get-Date"', "-Command"),
        ('powershell -c "Get-Date"', "-c"),
        ('pwsh -Command "Get-Date"', "-Command"),
        ('pwsh -NoProfile -Command "Get-Date"', "-Command"),
    ])
    def test_an_inline_interpreter_is_blocked(self, cmd, flag):
        """**每一個直譯器 + 程式碼旗標都要擋**,而且訊息要點名是哪一個旗標。

        列舉來源是**各語言自己的旗標表**,不是「我想得到的」(F-083)——
        想不到不等於不存在。
        """
        msg = gate.bash_write_violation(cmd)
        assert msg and "R7" in msg, "內嵌直譯器沒被擋:%r -> %r" % (cmd, msg)
        assert ".scratch" in msg, "訊息沒給出口(寫成 .scratch/ 腳本檔):%r" % msg
        assert flag in msg, "訊息沒點名旗標 %r:%r" % (flag, msg)

    def test_the_message_says_it_cannot_decide_not_that_you_wrote(self):
        """訊息**不得**說「你寫了檔」—— 那是具體而錯誤的訊息,而人會相信它,
        然後去找一個不存在的寫入(票 21 付過這個代價)。"""
        msg = gate.bash_write_violation('python -c "print(1)"')
        assert "判不出" in msg or "不可判定" in msg, msg

    def test_an_env_assignment_prefix_does_not_launder_it(self):
        """`PYTHONIOENCODING=utf-8 python -c …` —— 指令位置在環境變數指派之後。

        少了這一格,**本規則自己有一條一行的繞道**,而那條繞道是這個 repo
        日常在用的寫法(報告裡到處都是 `PYTHONIOENCODING=utf-8 python …`)。
        """
        msg = gate.bash_write_violation('PYTHONIOENCODING=utf-8 python -c "print(1)"')
        assert msg and "R7" in msg, msg

    def test_a_wrapper_does_not_launder_it(self):
        """`sudo` / `env` / `xargs` 這些包裝器後面才是真正的指令 ——
        `WRAPPERS` 已經為了同一個理由存在(`sudo rm -rf x` 的 rm 不在指令位置)。"""
        msg = gate.bash_write_violation('sudo python -c "print(1)"')
        assert msg and "R7" in msg, msg

    def test_a_later_segment_is_checked_too(self):
        """`&&` / `;` 之後那一段一樣要判 —— 逐段是 R7 既有的紀律。"""
        msg = gate.bash_write_violation('git status && python -c "print(1)"')
        assert msg and "R7" in msg, msg

    # ── ③④⑤ 反控 ────────────────────────────────────────────────────────

    @pytest.mark.parametrize("cmd", [
        "python .scratch/probe.py",                 # ③ 出口要通
        "python .scratch/f/prototype/x.py",
        "python -m pytest -q",                      # ④ -m 不是內嵌碼
        "python -m pip install -e .",
        "python .claude/hooks/gate.py --pre-commit",
        "python .claude/portable/verify_gates.py /tmp/x",
        "git status",                               # ⑤ 一般指令不受影響
        "ls -la",
    ])
    def test_the_exits_and_ordinary_commands_stay_open(self, cmd):
        """**反控**:出口不通的話,這條規則就是一堵沒有門的牆 ——
        而沒有門的規則會被整條關掉(F-031)。

        `python -m pytest` 那一格特別要緊:**CI 與本機的每一次測試都走它**。
        """
        assert gate.bash_write_violation(cmd) is None, "誤擋:%r" % cmd

    def test_the_existing_verb_rule_is_untouched(self):
        """⑤ **反控**:R7 既有的動詞判定不受影響 —— 本票只加一條前置判定。"""
        msg = gate.bash_write_violation("tee pkg/evil.py")
        assert msg and "R7" in msg, msg
        assert "內嵌直譯器" not in msg, "既有動詞路徑被新規則接管了:%r" % msg

    def test_a_quoted_mention_in_another_command_is_not_a_hit(self):
        """**反控**:比對錨在**指令位置**,不是「字串裡有沒有出現 python -c」。

        少了這一格,`git commit -m "改了 python -c 那條規則"` 會被擋 ——
        而那是本 repo 每天都在做的事(這張票的 commit 訊息自己就有那串字)。
        """
        cmd = 'git commit -m "fix: 前哨擋 python -c 內嵌直譯器"'
        assert gate.bash_write_violation(cmd) is None, "誤擋:%r" % cmd

    def test_the_rule_stays_inside_r7(self):
        """規則代號不新增 —— `rule_codes()` 仍然只有既有那幾條。

        新開一個編號會讓 `verify_gates` 要求一個新的淨室情境,
        而那個情境的特判理由與 R7 一字不差(見本 class 的 docstring)。
        """
        codes = gate.rule_codes()
        assert "R7" in codes
        assert "R10" not in codes, "多了一個規則代號,淨室會要求它的情境:%s" % sorted(codes)


# ─────────────────────────────────────────────────────────────────────────────
# 票 133 批一 ① —— R9 的權威輸入是 **index**,不是工作樹
#
# ## 這一格的問題與答案(票面同文)
#
# 問:**R9 在 commit 的時點,權威輸入該是哪一個版本?**
# 答:**index**。R9 的命題是「同一份 friction log 裡不得有兩個相同的號」,
#     而「那一份」指的是**要進歷史的那一份** —— 進歷史的是 index。
#     舊版讀工作樹 ⇒ `git add <撞號版>` 之後把工作樹改乾淨,R9 綠、撞號進歷史。
#
# **答案不是「因為別格也是 index」推出來的**:R9 判的對象就是那個檔案本身,
# 而那個檔案會被這次 commit 帶走,所以 index 是它唯一正確的對象。
# (對照:`content_after_edit` 那條路的正確對象**不是** index —— 見票 133 三分類。)
#
# ## 為什麼 `path` 參數保留讀工作樹
#
# `path` 是**明確指定一個檔**的診斷/測試入口(既有 20+ 條測試都靠它)。
# 「讀這個檔」與「讀這個 repo 要提交的那一份」是兩個問題 ——
# 照票 133 的硬限制:**共用一個讀取函式不等於共用一個正確對象**,
# 所以來源綁**執行上下文**(有沒有給 path),不綁函式。
#
# ## 2×2 真值表 + 一格 fail-closed
#
#            | 工作樹乾淨              | 工作樹撞號
#   ---------+------------------------+---------------------------
#   index    | **① 本格本體**(要擋)  | ④ 反控:偵測面不得變小(要擋)
#   撞號     |                        |
#   ---------+------------------------+---------------------------
#   index    | ③ 反控:不得變成永遠紅  | **② 鑑別格**(要放行)
#   乾淨     | (要放行)              |
#
# ② 是鑑別格:「兩邊都讀」的偷懶修法會讓 ① 變綠,而 ② 會抓到它 ——
# 那一次 commit 進歷史的 log 是乾淨的,擋下來就是誤擋,而誤擋會讓規則被關掉。
# ⑤ 另加一格:**檔案不在 index 裡 → fail-closed,且訊息要說出怎麼修。**
#
# 語料取本檔既有 R9 測試在用的那一組(`## F-001 甲` / `## F-002 乙` / `## F-001 丙`,
# 見 `TestFrictionNumbersAreUnique::test_a_duplicate_number_is_a_violation`),
# **不憑空發明新字串**。
# ─────────────────────────────────────────────────────────────────────────────

_R9_REL = "docs/agents/friction-log.md"
_R9_DUP = u"## F-001 甲\n\n內文\n\n## F-002 乙\n\n## F-001 丙\n"
_R9_CLEAN = u"## F-001 甲\n\n內文\n\n## F-002 乙\n\n## F-003 丙\n"


def _git133(args, cwd):
    subprocess.run(["git"] + list(args), cwd=str(cwd), capture_output=True,
                   check=False)


class TestR9JudgesTheStagedFrictionLog:

    def _repo(self, tmp_path, staged, worktree, add=True):
        """真 git repo:`staged` 進 index,`worktree` 留工作樹。

        `add=False` 用於 ⑤ —— 檔案在磁碟上但**不在 index 裡**。
        """
        _git133(["init", "-q"], tmp_path)
        _git133(["config", "user.email", "t@local"], tmp_path)
        _git133(["config", "user.name", "t"], tmp_path)
        p = tmp_path / "docs" / "agents" / "friction-log.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        io.open(str(p), "w", encoding="utf-8", newline="\n").write(staged)
        if add:
            _git133(["add", "--", _R9_REL], tmp_path)
        io.open(str(p), "w", encoding="utf-8", newline="\n").write(worktree)
        return tmp_path

    def test_a_duplicate_in_the_index_is_caught(self, tmp_path):
        """① **本格本體**:撞號版在 index、乾淨版在工作樹 → 必須擋。

        舊版讀工作樹 ⇒ 回 `[]` ⇒ 撞號靜默進歷史,而 R9 是
        **唯一進了權威層的散文規則**(門檻是零誤報 + 零判斷 + 便宜)。
        """
        repo = self._repo(tmp_path, staged=_R9_DUP, worktree=_R9_CLEAN)
        v = gate.check_friction_numbers(cwd=str(repo))
        assert v, ("index 裡有撞號、工作樹乾淨,R9 卻回報乾淨 —— "
                   "判的是工作樹,而進歷史的是 index 那一份")
        assert "F-001" in v[0], u"擋下了但沒說出是哪一個號:%r" % v

    def test_a_duplicate_only_in_the_worktree_is_not_caught(self, tmp_path):
        """② **鑑別格**:乾淨版在 index、撞號版在工作樹 → 必須放行。

        那一次 commit 進歷史的 log 是乾淨的 ⇒ **擋下來就是誤擋**。
        這一格抓的是「兩邊都讀」那個偷懶修法 —— 它讓 ① 變綠,
        代價是每一個「工作樹還在草稿中」的狀態都擋死 commit。
        """
        repo = self._repo(tmp_path, staged=_R9_CLEAN, worktree=_R9_DUP)
        v = gate.check_friction_numbers(cwd=str(repo))
        assert v == [], u"index 是乾淨的卻被擋 —— 判定對象跑到工作樹去了:%r" % v

    def test_an_agreeing_clean_log_passes(self, tmp_path):
        """③ **反控**:兩邊一致且乾淨 → 放行。

        少了它,「一律回違規」也能讓 ① 過,而那是把權威層變成永遠紅。
        """
        repo = self._repo(tmp_path, staged=_R9_CLEAN, worktree=_R9_CLEAN)
        assert gate.check_friction_numbers(cwd=str(repo)) == []

    def test_an_agreeing_duplicate_is_still_caught(self, tmp_path):
        """④ **反控**:兩邊一致且撞號 → 仍要擋。

        這是最日常的那一格(`git add` 之後沒再改)。少了它,
        「index 讀不到就跳過」也能讓 ① ② ③ 全過 —— 而那是把 R9 整條關掉,
        **測試看起來還是綠的**。
        """
        repo = self._repo(tmp_path, staged=_R9_DUP, worktree=_R9_DUP)
        v = gate.check_friction_numbers(cwd=str(repo))
        assert v and "F-001" in v[0], u"偵測面被弄小了:%r" % v

    def test_a_log_missing_from_the_index_fails_closed_with_a_fix(self, tmp_path):
        """⑤ **fail-closed,而且訊息要說出怎麼修。**

        檔案在磁碟上、**不在 index 裡**(新裝的 repo 還沒 `git add` 就是這個狀態)。
        **不得退回工作樹** —— `gate.py:1966` 逐字:「退回去就是判錯對象,
        而且是往 fail-open 的方向錯」。

        但**方向對不代表訊息對**:一個只說「讀不到」的訊息會讓人去找一個
        不存在的損壞檔案。訊息要點出那個沒被滿足的前提(票 13)——
        這裡的前提是「它要在 index 裡」,修法是 `git add`。
        """
        repo = self._repo(tmp_path, staged=_R9_CLEAN, worktree=_R9_CLEAN,
                          add=False)
        v = gate.check_friction_numbers(cwd=str(repo))
        assert v, u"不在 index 裡卻回報乾淨 —— fail-open"
        assert "index" in v[0] and "git add" in v[0], (
            u"訊息沒說出前提與修法,人會去找一個不存在的損壞檔案:%r" % v)

    def test_the_explicit_path_argument_still_reads_the_worktree(self, tmp_path):
        """**反控(硬限制那一條)**:給了 `path` 就還是讀工作樹。

        少了它,把整支函式改成讀 index 也會讓 ① 過 ——
        而那會打壞既有 20+ 條以 `path` 餵語料的測試,
        以及「明確指定一個檔」這個診斷入口本身。
        **共用一個讀取函式不等於共用一個正確對象。**
        """
        repo = self._repo(tmp_path, staged=_R9_CLEAN, worktree=_R9_DUP)
        p = str(repo / "docs" / "agents" / "friction-log.md")
        v = gate.check_friction_numbers(p)
        assert v and "F-001" in v[0], (
            u"`path` 那條路不再讀工作樹 —— 診斷入口與既有語料一起被換掉了:%r" % v)


# ─────────────────────────────────────────────────────────────────────────────
# 票 133 批一 ② —— R1 在 commit 時點的權威輸入是 **index**,不是工作樹
#
# ## 這一格的問題與答案
#
# 問:**R1 在 commit 的時點,權威輸入該是哪一個版本?**
# 答:**index**。R1 的命題是「規格書裡不得夾程式碼」,而「那份規格書」指的是
#     **要進歷史的那一份** —— 進歷史的是 index。
#
# 現行 R1 **完全不看 `at_commit`**:R1 分支的三個 return 全部早於
# `check()` 裡第一個消費 `at_commit` 的分支,所以 `content is None` 時
# 兩個時點都讀工作樹 ⇒ `git add <夾了碼的版本>` 之後把工作樹改乾淨,
# R1 綠、程式碼靜默進歷史。**失敗方式是靜默的** —— 兩份多數時候一樣,
# 所以日常與既有測試都照不到它。
#
# **答案不是從「R9 也是 index」推出來的**:R1 判的對象就是那個規格檔本身,
# 而那個檔會被這次 commit 帶走 ⇒ index 是它唯一正確的對象。
# (對照:前哨那條路的正確對象**不是** index —— 呼叫端把 `content` 交出來,
#  那是「這次編輯之後會變成什麼」,它還沒進 index,也不該進。
#  票 133 的硬限制:**共用一個讀取函式不等於共用一個正確對象**。)
#
# ## 2×2 真值表 + 硬限制 + 邊界
#
#            | 工作樹乾淨              | 工作樹夾碼
#   ---------+------------------------+----------------------------
#   index    | **① 本格本體**(要擋)  | ④ 反控:偵測面不得變小(要擋)
#   夾碼     |                        |
#   ---------+------------------------+----------------------------
#   index    | ③ 反控:不得變成永遠紅  | **② 鑑別格**(要放行)
#   乾淨     | (要放行)              |
#
# ② 是鑑別格,抓的是「乾脆兩邊都讀」那個偷懶修法:它會讓 ① 變綠,
# 代價是每一個「工作樹還在草稿中」的狀態都擋死 commit。那一次 commit
# 進歷史的規格書是乾淨的,擋下來就是誤擋 —— 而 CLAUDE.md 逐字:
# 「錯在權威層等於擋住做對事的人,那種規則最後會被整條關掉」。
#
# ③ 少了它,「一律回違規」也能讓 ① 過,而那是把 R1 變成永遠紅。
# ④ 少了它,「index 讀不到就跳過」也能讓 ① ② ③ 全過 —— 那是把 R1 整條關掉,
#    **而測試看起來還是綠的**。
#
# ⑤ **硬限制**:`at_commit=False`,或 `content` 有給值 → 行為一個位元組都不准動。
#    前哨 / PreToolUse 那條路不在本票範圍內,而「順手一起改」是看不見的擴大。
# ⑥ **邊界**:規格檔不在 index 裡(`git show :<path>` 問不到)→ fail-closed,
#    訊息要點名檔案與原因。**不得退回工作樹** —— 那是另一份東西。
#
# 假樣本一律取本檔既有的 `R1_CODE_SHAPES`(八個樣式,一個樣式命中一支分支),
# 乾淨樣本取既有反控 1 在用的純散文形狀 —— **不憑空發明新字串**。
# ─────────────────────────────────────────────────────────────────────────────

# 反控 1(`test_a_spec_with_only_prose_is_not_blocked`)逐字在用的那一份。
_R1_IDX_CLEAN = u"## 問題\n只有散文。"

# 每支測試要一條**自己的**規格路徑,才能共用同一個 git repo(省掉上百次 init)。
# 用 list 長度當序號:不引進新的 import,而且同一個 process 內單調遞增。
_R1_IDX_SEQ = []


def _r1_uniq():
    _R1_IDX_SEQ.append(1)
    return u"n%d" % len(_R1_IDX_SEQ)


# R1 的兩條路徑判定,一條一列(與 `R1_SPEC_PATHS` 同一組分支):
# `docs` 是**前綴**(底下任意深度);`scratch` 是**完整比對**(`[^/]+` 只吃一層)。
_R1_IDX_LAYOUTS = ["docs", "scratch"]


def _r1_layout_path(layout, uniq):
    if layout == "docs":
        return u"docs/specs/%s.md" % uniq
    return u".scratch/%s/spec.md" % uniq


@pytest.fixture(scope="session")
def _r1_index_repo(tmp_path_factory):
    """整個 session **一個** git repo。

    每支測試各用一條獨佔的規格路徑,所以共用 index 不會互相汙染 ——
    而 `git init` 在 Windows 上不便宜,一百多次會讓這批測試變成沒人想跑的那種。
    """
    repo = tmp_path_factory.mktemp("r1_index_repo")
    _git133(["init", "-q"], repo)
    _git133(["config", "user.email", "t@local"], repo)
    _git133(["config", "user.name", "t"], repo)
    return repo


@pytest.fixture
def r1_spec(_r1_index_repo, monkeypatch):
    """回一個建構子:`(layout, staged, worktree, add=True) -> 絕對路徑`。

    `ROOT` 指到那個 repo —— 理由同 `spec_root`:`rel()` 走 `abspath`,
    ROOT 沒指過去的話路徑會收斂成 `../..` 開頭,被「repo 外不管」那條提早放行,
    **測試會綠,而它沒測到東西**。

    順帶:`staged_blob` 的 `cwd` 預設就是 `ROOT`,所以 `check()` 不必為了
    測試多長一個 `cwd` 參數 —— monkeypatch ROOT 這一步同時餵了兩條路。

    `add=False` 用於 ⑥ —— 檔案在磁碟上但**不在 index 裡**。
    """
    monkeypatch.setattr(gate, "ROOT", str(_r1_index_repo))

    def build(layout, staged, worktree, add=True):
        rel_path = _r1_layout_path(layout, _r1_uniq())
        p = _r1_index_repo / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        io.open(str(p), "w", encoding="utf-8", newline="\n").write(staged)
        if add:
            # `-f`:`.scratch/` 在真 repo 裡是 gitignore 的,而本批的判定對象
            # 是「index 裡有沒有這一份」,不是「它該不該被 ignore」。
            _git133(["add", "-f", "--", rel_path], _r1_index_repo)
        io.open(str(p), "w", encoding="utf-8", newline="\n").write(worktree)
        return str(p)

    return build


@pytest.mark.parametrize("layout", _R1_IDX_LAYOUTS)
@pytest.mark.parametrize("shape,body", R1_CODE_SHAPES,
                         ids=[s for s, _ in R1_CODE_SHAPES])
class TestR1JudgesTheStagedSpec:
    """2×2 真值表的四格,八個樣式 × 兩條路徑各跑一輪。"""

    def test_code_in_the_index_is_caught(self, r1_spec, shape, body, layout):
        """① **本格本體**:夾碼版在 index、乾淨版在工作樹 → 必須擋。

        現行讀工作樹 ⇒ 回 None ⇒ 程式碼靜默進歷史。
        """
        p = r1_spec(layout, staged=body, worktree=_R1_IDX_CLEAN)
        msg = gate.check(p, None, at_commit=True)
        assert msg and "R1" in msg, (
            u"index 裡夾了 `%s`、工作樹乾淨,R1 卻放行 —— "
            u"判的是工作樹,而進歷史的是 index 那一份:path=%s msg=%r"
            % (shape, p, msg))

    def test_code_only_in_the_worktree_is_not_caught(self, r1_spec, shape,
                                                     body, layout):
        """② **鑑別格**:乾淨版在 index、夾碼版在工作樹 → 必須放行。

        這一格抓「兩邊都讀」那個偷懶修法 —— 它讓 ① 變綠,
        代價是這一格被錯殺,而權威層的誤擋最後會讓整條規則被關掉。
        """
        p = r1_spec(layout, staged=_R1_IDX_CLEAN, worktree=body)
        msg = gate.check(p, None, at_commit=True)
        assert msg is None, (
            u"index 是乾淨的卻被擋 —— 判定對象跑到工作樹去了:"
            u"shape=%s path=%s msg=%r" % (shape, p, msg))

    def test_an_agreeing_dirty_spec_is_still_caught(self, r1_spec, shape,
                                                    body, layout):
        """④ **反控**:兩邊一致且夾碼 → 仍要擋(最日常的那一格)。"""
        p = r1_spec(layout, staged=body, worktree=body)
        msg = gate.check(p, None, at_commit=True)
        assert msg and "R1" in msg, (
            u"偵測面被弄小了 —— 兩邊都夾了 `%s` 還放行:path=%s msg=%r"
            % (shape, p, msg))


@pytest.mark.parametrize("layout", _R1_IDX_LAYOUTS)
def test_an_agreeing_clean_spec_passes_at_commit(r1_spec, layout):
    """③ **反控**:兩邊一致且乾淨 → 放行。

    少了它,「一律回違規」也能讓 ① 過,而那是把權威層變成永遠紅。
    """
    p = r1_spec(layout, staged=_R1_IDX_CLEAN, worktree=_R1_IDX_CLEAN)
    msg = gate.check(p, None, at_commit=True)
    assert msg is None, u"兩邊都乾淨卻被擋:path=%s msg=%r" % (p, msg)


@pytest.mark.parametrize("layout", _R1_IDX_LAYOUTS)
@pytest.mark.parametrize("shape,body", R1_CODE_SHAPES,
                         ids=[s for s, _ in R1_CODE_SHAPES])
class TestR1SentryPathIsUntouched:
    """⑤ **硬限制反控**:`at_commit=False` 或 `content` 有給值 → 行為不變。

    本票只動「commit 時點且 content 為 None」那一格。少了這一批,
    把 R1 整條改成讀 index 也會讓 ① ② ③ ④ 全過 —— 而那會把前哨
    (PreToolUse:內容還沒進 index,也不該進)一起換掉,
    **共用一個讀取函式不等於共用一個正確對象**。
    """

    def test_at_write_time_a_dirty_worktree_is_still_caught(self, r1_spec, shape,
                                                            body, layout):
        """⑤a:`at_commit=False` + content=None → 仍讀工作樹(夾碼 → 擋)。"""
        p = r1_spec(layout, staged=_R1_IDX_CLEAN, worktree=body)
        msg = gate.check(p, None, at_commit=False)
        assert msg and "R1" in msg, (
            u"寫入時點不再讀工作樹 —— 前哨被一起換掉了:"
            u"shape=%s path=%s msg=%r" % (shape, p, msg))

    def test_at_write_time_a_clean_worktree_still_passes(self, r1_spec, shape,
                                                         body, layout):
        """⑤b:`at_commit=False` + content=None → 仍讀工作樹(乾淨 → 放行)。

        與 ⑤a 相反的一半:少了它,「寫入時點一律擋」也能讓 ⑤a 綠。
        """
        p = r1_spec(layout, staged=body, worktree=_R1_IDX_CLEAN)
        msg = gate.check(p, None, at_commit=False)
        assert msg is None, (
            u"寫入時點跑去讀 index 了 —— 前哨的正確對象不是 index:"
            u"shape=%s path=%s msg=%r" % (shape, p, msg))

    def test_given_content_wins_over_both_sources(self, r1_spec, shape, body,
                                                  layout):
        """⑤c:`content` 有給值 → 用它,即使兩邊都乾淨、即使 at_commit=True。

        這是前哨真正在走的形態:`content_after_edit` —— 「這次編輯之後會變成
        什麼」,它還沒有進 index。
        """
        p = r1_spec(layout, staged=_R1_IDX_CLEAN, worktree=_R1_IDX_CLEAN)
        msg = gate.check(p, body, at_commit=True)
        assert msg and "R1" in msg, (
            u"呼叫端交出來的內容夾了 `%s` 卻沒被判 —— "
            u"content 那條路被 index 蓋掉了:path=%s msg=%r" % (shape, p, msg))

    def test_given_clean_content_is_not_overridden_by_the_index(
            self, r1_spec, shape, body, layout):
        """⑤d:`content` 給的是乾淨的 → 放行,即使 index 與工作樹都夾碼。

        與 ⑤c 相反的一半:少了它,「content 有給值時順便也讀 index」
        會讓 ⑤c 綠,而那條修法會在前哨誤擋每一次「正在把碼刪掉」的編輯。
        """
        p = r1_spec(layout, staged=body, worktree=body)
        msg = gate.check(p, _R1_IDX_CLEAN, at_commit=True)
        assert msg is None, (
            u"content 給的是乾淨的卻被擋 —— 判定對象跑去 index 了:"
            u"shape=%s path=%s msg=%r" % (shape, p, msg))


@pytest.mark.parametrize("layout", _R1_IDX_LAYOUTS)
def test_a_spec_missing_from_the_index_fails_closed_with_a_reason(r1_spec, layout):
    """⑥ **邊界:不在 index 裡 → fail-closed,而且訊息要說出是哪個檔、為什麼。**

    檔案在磁碟上、**不在 index 裡**(規格書剛寫好還沒 `git add` 就是這個狀態)。
    工作樹刻意放**乾淨**的那一份:退回工作樹的修法會在這裡拿到一個假綠燈。

    **不得退回工作樹** —— `staged_blob` 的 docstring 逐字:「退回去就是判錯對象,
    而且是往 fail-open 的方向錯」。

    但**方向對不代表訊息對**(票 13):只說「讀不到」會讓人去找一個不存在的
    損壞檔案,而這裡沒被滿足的前提是「它要在 index 裡」——
    訊息要指向那個前提,並寫出修法。
    """
    p = r1_spec(layout, staged=_R1_IDX_CLEAN, worktree=_R1_IDX_CLEAN, add=False)
    msg = gate.check(p, None, at_commit=True)
    assert msg, u"不在 index 裡卻回報乾淨 —— fail-open:path=%s" % p
    assert "R1" in msg and "fail-closed" in msg, (
        u"擋是擋了,但沒標明是 R1 的 fail-closed 那一支:msg=%r" % msg)
    assert os.path.basename(p) in msg, (
        u"訊息沒點名是哪個檔 —— 人不知道要去 add 什麼:msg=%r" % msg)
    assert "index" in msg and "git add" in msg, (
        u"訊息沒說出前提與修法,人會去找一個不存在的損壞檔案:msg=%r" % msg)


# ─────────────────────────────────────────────────────────────────────────────
# 票 133 批一 ③ —— R8 在 commit 時點的權威輸入是 **index**,不是工作樹
#
# ## 這一格的問題與答案
#
# 問:**R8 在 commit 的時點,權威輸入該是哪一個版本?**
# 答:**index**。R8 的命題是「生產程式碼不得 import research/」,而「那份程式碼」
#     指的是**要進歷史的那一份** —— 進歷史的是 index。
#
# 現行 R8 在 `content is None` 時走 `read_text_or_none(ROOT/r)`,**兩個時點都讀工作樹**
# ⇒ `git add <import 了 research 的版本>` 之後把工作樹改乾淨,R8 綠、
# 對 research/ 的依賴靜默進歷史。**失敗方式是靜默的。**
#
# **答案不是從「R1 / R9 也是 index」推出來的**:R8 判的對象就是那個 .py 檔本身,
# 而那個檔會被這次 commit 帶走 ⇒ index 是它唯一正確的對象。
# (對照:`content` 有給值那條路的正確對象**不是** index —— 那是前哨,
#  問的是「這次編輯之後會變成什麼」(票 07 / F-046 的判定對象裁決),
#  它還沒進 index,也不該進。票 133 的硬限制:
#  **共用一個讀取函式不等於共用一個正確對象。**)
#
# ## ⚠ 與 R1 的三個差異(照抄 R1 的改法會出事)
#
# 1. **R8 之後還有東西** —— legacy 清單豁免、R3 的兩半都排在它後面,
#    而 R1 那一支是 `return None` 結束整個分支。
# 2. **R8 有三段出口**(讀不到 / 不是合法 Python / 真的 import 了),R1 只有兩段。
# 3. **R8 前面還有 R2** —— 站別不對的話根本走不到 R8,所以本批一律 monkeypatch
#    `load_stage` 成 implement(既有 R8 測試就是這個做法)。
#
# ⇒ **因此本批的斷言一律只問「訊息裡有沒有 R8」,不問「有沒有被擋」。**
#    乾淨那幾格會走到 R3,而 R3 在臨時 repo 裡本來就會說話(沒有紅燈紀錄)——
#    那與本票無關。既有 R8 測試(`test_edit_result.py`)用的就是這個寫法:
#    `assert not (msg and "R8" in msg)`。
#
# ## 2×2 真值表 + 硬限制 + 邊界
#
#            | 工作樹乾淨              | 工作樹 import 了 research
#   ---------+------------------------+----------------------------
#   index    | **① 本格本體**(要擋)  | ④ 反控:偵測面不得變小(要擋)
#   違規     |                        |
#   ---------+------------------------+----------------------------
#   index    | ③ 反控:不得變成永遠紅  | **② 鑑別格**(要放行)
#   乾淨     | (要放行)              |
#
# ⑤ **硬限制**:`at_commit=False`,或 `content` 有給值 → 行為一個位元組都不准動。
# ⑥ **邊界**:檔案不在 index 裡 → fail-closed,訊息要點名檔案與原因。
#
# ## 語料出處(**逐字複製,未發明新樣本**)
#
# 違規 9 個:`tests/test_research_stage.py` 的
#   `TestR8ProductionMustNotImportResearch::test_production_importing_research_is_blocked`(4 個)
#   + `TestTheSyntaxAxisIsEnumeratedNotSampled`(票 104)判為 True 的 5 個。
# 乾淨 1 個:同檔 `test_a_boundary_neighbour_is_not_a_research_import` 的第一個
#   (`import research_utils` —— F-051 那個邊界)。
#
# ⚠ **複製就是第二份來源,而註解不是機制** ⇒ 底下有一組**漂移守衛**,
# 拿 `imports_research()` 對每一個樣本問一次分類。上游那批改了行為的話,
# 守衛會先紅,而不是讓 2×2 靜靜地測不到東西。
#
# 📌 **候選(未開票,票 133 批一 ③ 裁決:登記不做)——「複製 vs 引用」**
#     更好的做法是把那 10 個字串抽成 `tests/test_research_stage.py` 的**具名常數**
#     再 import 進來,**一份來源**就不需要漂移守衛。
#     沒有在本票做的理由:那要動到另一個測試檔,而本票的範圍是判定對象。
#     **記在這裡是因為下一個動這組語料的人會先看到這裡** ——
#     動工的觸發條件:任何人要在這組語料裡增刪樣本時。
#     ⚠ 這一句是**紀錄不是機制**:沒有東西會在它被忽略時出聲(CLAUDE.md 的祈使句那條)。
# ─────────────────────────────────────────────────────────────────────────────

# 違規樣本:`imports_research()` 判 True。每一個都是**合法 Python**
# (不合法會走 `parses_as_python` 那一段,那是另一個出口,不是本批要驗的)。
_R8_BAD = [
    ("plain", u"import research\n"),
    ("dotted", u"import research.explore\n"),
    ("from", u"from research import explore\n"),
    ("from_dotted", u"from research.explore import thing\n"),
    ("aliased", u"import research as r\n"),
    ("aliased_dotted", u"import research.explore as e\n"),
    ("multi_name", u"import os, research\n"),
    ("star", u"from research import *\n"),
    # ⚠ 票 104 逐字標注「**現行行為,未裁是否正確**」。本批沿用它,
    # 因為本批驗的是**判定對象**,不是判定內容 —— 那一軸改判的那天,
    # 上面的漂移守衛會先紅,而不是這一批。
    ("relative_module", u"from .research import x\n"),
]

# 乾淨樣本:F-051 的邊界鄰居。**不是新字串**。
_R8_CLEAN = u"import research_utils\n"

# 每支測試要一條**自己的**生產檔路徑,才能共用同一個 git repo。
_R8_SEQ = []


def _r8_uniq():
    _R8_SEQ.append(1)
    return u"m%d" % len(_R8_SEQ)


@pytest.fixture(scope="session")
def _r8_index_repo(tmp_path_factory):
    """整個 session **一個** git repo(理由同 `_r1_index_repo`)。"""
    repo = tmp_path_factory.mktemp("r8_index_repo")
    _git133(["init", "-q"], repo)
    _git133(["config", "user.email", "t@local"], repo)
    _git133(["config", "user.name", "t"], repo)
    return repo


@pytest.fixture
def r8_src(_r8_index_repo, monkeypatch):
    """回一個建構子:`(staged, worktree, add=True) -> 絕對路徑`。

    兩個 monkeypatch,缺一不可:

    - `ROOT` 指到臨時 repo —— 同 `spec_root` 的理由,而且 `staged_blob` 的
      `cwd` 預設就是 `ROOT`,一步餵了 `rel()` 與 git 兩條路。
    - `load_stage` 成 implement —— **R2 排在 R8 前面**,站別不對的話
      根本走不到 R8(既有 R8 測試就是這個做法)。
      `STAGES_DEF` 是 import 時凍結的絕對路徑,指著**真** repo 的定義檔,
      所以 `load_stage_defs()` 仍然讀得到,R2-fc 不會觸發。

    `add=False` 用於 ⑥ —— 檔案在磁碟上但**不在 index 裡**。
    """
    monkeypatch.setattr(gate, "ROOT", str(_r8_index_repo))
    monkeypatch.setattr(gate, "load_stage", lambda: ("implement", "133"))

    def build(staged, worktree, add=True):
        rel_path = u"macro_audit/%s.py" % _r8_uniq()
        p = _r8_index_repo / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        io.open(str(p), "w", encoding="utf-8", newline="\n").write(staged)
        if add:
            _git133(["add", "-f", "--", rel_path], _r8_index_repo)
        io.open(str(p), "w", encoding="utf-8", newline="\n").write(worktree)
        return str(p)

    return build


def _r8_said(msg):
    """訊息裡有沒有 R8。

    **只問這個,不問「有沒有被擋」** —— 乾淨那幾格會往下走到 R3,
    而 R3 在臨時 repo 裡本來就會說話(沒有紅燈紀錄),那與本票無關。
    寫法同既有的 `test_edit_result.py`。
    """
    return "R8" in (msg or "")


class TestTheR8CorpusStillClassifiesAsItsSourceSays:
    """**漂移守衛**:本批的語料是從別的檔**複製**來的,而複製會漂。

    2×2 的每一格都假設「這 9 個是違規、那 1 個是乾淨」。
    假設若靜靜變假,2×2 會**全綠而什麼都沒測到**。
    這一組把假設本身變成斷言 —— **註解不是機制,斷言才是。**
    """

    @pytest.mark.parametrize("shape,body", _R8_BAD,
                             ids=[s for s, _ in _R8_BAD])
    def test_every_bad_sample_is_still_a_research_import(self, shape, body):
        assert gate.imports_research(body) is True, (
            u"語料漂了:`%s` 不再被判為 import research ⇒ "
            u"用它當違規樣本的每一格都會變成「測不到東西的綠」:%r" % (shape, body))

    def test_the_clean_sample_is_still_not_a_research_import(self):
        assert gate.imports_research(_R8_CLEAN) is False, (
            u"乾淨樣本漂了:`%r` 現在被判為 import research ⇒ "
            u"所有「乾淨」那一側的格子都在測錯東西" % _R8_CLEAN)


@pytest.mark.parametrize("shape,body", _R8_BAD, ids=[s for s, _ in _R8_BAD])
class TestR8JudgesTheStagedSource:
    """2×2 真值表裡有違規樣本的三格,九個 import 形式各跑一輪。"""

    def test_a_research_import_in_the_index_is_caught(self, r8_src, shape, body):
        """① **本格本體**:違規版在 index、乾淨版在工作樹 → R8 必須說話。

        現行讀工作樹 ⇒ R8 沉默 ⇒ 對 research/ 的依賴靜默進歷史。
        """
        p = r8_src(staged=body, worktree=_R8_CLEAN)
        msg = gate.check(p, None, at_commit=True)
        assert _r8_said(msg), (
            u"index 裡有 `%s`、工作樹乾淨,R8 卻沒說話 —— "
            u"判的是工作樹,而進歷史的是 index 那一份:path=%s msg=%r"
            % (shape, p, msg))

    def test_a_research_import_only_in_the_worktree_is_not_caught(
            self, r8_src, shape, body):
        """② **鑑別格**:乾淨版在 index、違規版在工作樹 → R8 不可說話。

        抓「乾脆兩邊都讀」那個偷懶修法 —— 它讓 ① 變綠,
        代價是每一個「工作樹還在草稿中」的狀態都擋死 commit。
        """
        p = r8_src(staged=_R8_CLEAN, worktree=body)
        msg = gate.check(p, None, at_commit=True)
        assert not _r8_said(msg), (
            u"index 是乾淨的,R8 卻說話了 —— 判定對象跑到工作樹去了:"
            u"shape=%s path=%s msg=%r" % (shape, p, msg))

    def test_an_agreeing_research_import_is_still_caught(self, r8_src, shape, body):
        """④ **反控**:兩邊一致且違規 → 仍要說話(最日常的那一格)。

        少了它,「index 讀不到就跳過」也能讓 ① ② ③ 全過 —— 那是把 R8 整條關掉,
        **而測試看起來還是綠的**。
        """
        p = r8_src(staged=body, worktree=body)
        msg = gate.check(p, None, at_commit=True)
        assert _r8_said(msg), (
            u"偵測面被弄小了 —— 兩邊都有 `%s` 還沉默:path=%s msg=%r"
            % (shape, p, msg))


def test_an_agreeing_clean_source_passes_r8_at_commit(r8_src):
    """③ **反控**:兩邊一致且乾淨 → R8 不得說話。

    少了它,「一律回違規」也能讓 ① 過,而那是把 R8 變成永遠紅。
    """
    p = r8_src(staged=_R8_CLEAN, worktree=_R8_CLEAN)
    msg = gate.check(p, None, at_commit=True)
    assert not _r8_said(msg), u"兩邊都乾淨 R8 卻說話:path=%s msg=%r" % (p, msg)


@pytest.mark.parametrize("shape,body", _R8_BAD, ids=[s for s, _ in _R8_BAD])
class TestR8SentryPathIsUntouched:
    """⑤ **硬限制反控**:`at_commit=False` 或 `content` 有給值 → 行為不變。

    本票只動「commit 時點且 content 為 None」那一格。少了這一批,
    把 R8 整條改成讀 index 也會讓 ① ② ③ ④ 全過 —— 而那會把前哨
    (票 07 / F-046 的「判定對象是套用編輯後的整檔結果」)一起換掉。
    """

    def test_at_write_time_a_dirty_worktree_is_still_caught(self, r8_src, shape, body):
        """⑤a:`at_commit=False` + content=None → 仍讀工作樹(違規 → 說話)。"""
        p = r8_src(staged=_R8_CLEAN, worktree=body)
        msg = gate.check(p, None, at_commit=False)
        assert _r8_said(msg), (
            u"寫入時點不再讀工作樹 —— 前哨被一起換掉了:"
            u"shape=%s path=%s msg=%r" % (shape, p, msg))

    def test_at_write_time_a_clean_worktree_still_passes(self, r8_src, shape, body):
        """⑤b:`at_commit=False` + content=None → 仍讀工作樹(乾淨 → 沉默)。

        與 ⑤a 相反的一半:少了它,「寫入時點一律擋」也能讓 ⑤a 綠。
        """
        p = r8_src(staged=body, worktree=_R8_CLEAN)
        msg = gate.check(p, None, at_commit=False)
        assert not _r8_said(msg), (
            u"寫入時點跑去讀 index 了 —— 前哨的正確對象不是 index:"
            u"shape=%s path=%s msg=%r" % (shape, p, msg))

    def test_given_content_wins_over_both_sources(self, r8_src, shape, body):
        """⑤c:`content` 有給值 → 用它,即使兩邊都乾淨、即使 at_commit=True。

        這是前哨真正在走的形態:`content_after_edit` —— 「這次編輯之後會變成
        什麼」,它還沒有進 index(票 07 / F-046)。
        """
        p = r8_src(staged=_R8_CLEAN, worktree=_R8_CLEAN)
        msg = gate.check(p, body, at_commit=True)
        assert _r8_said(msg), (
            u"呼叫端交出來的內容有 `%s` 卻沒被判 —— "
            u"content 那條路被 index 蓋掉了:path=%s msg=%r" % (shape, p, msg))

    def test_given_clean_content_is_not_overridden_by_the_index(
            self, r8_src, shape, body):
        """⑤d:`content` 給的是乾淨的 → R8 沉默,即使 index 與工作樹都違規。

        與 ⑤c 相反的一半:少了它,「content 有給值時順便也讀 index」
        會讓 ⑤c 綠,而那條修法會在前哨誤擋每一次「正在把 import 刪掉」的編輯
        —— 那正是 `test_edit_result.py::test_an_edit_that_removes_the_import_is_allowed`
        守著的方向。
        """
        p = r8_src(staged=body, worktree=body)
        msg = gate.check(p, _R8_CLEAN, at_commit=True)
        assert not _r8_said(msg), (
            u"content 給的是乾淨的 R8 卻說話 —— 判定對象跑去 index 了:"
            u"shape=%s path=%s msg=%r" % (shape, p, msg))


def test_a_source_missing_from_the_index_fails_closed_with_a_reason(r8_src):
    """⑥ **邊界:不在 index 裡 → fail-closed,而且訊息要說出是哪個檔、為什麼。**

    檔案在磁碟上、**不在 index 裡**。工作樹刻意放**乾淨**的那一份:
    退回工作樹的修法會在這裡拿到一個假綠燈。

    **不得退回工作樹** —— `staged_blob` 的 docstring 逐字:「退回去就是判錯對象,
    而且是往 fail-open 的方向錯」。

    但**方向對不代表訊息對**(票 13):只說「讀不到」會讓人去找一個不存在的
    損壞檔案,而這裡沒被滿足的前提是「它要在 index 裡」。
    R8 既有的三段出口本來就分得開「讀不到」與「你 import 了 research」
    (票 07 的代價逐字:誤導的訊息比沒有訊息貴)—— 新增這一段不得把它們混回去。
    """
    p = r8_src(staged=_R8_CLEAN, worktree=_R8_CLEAN, add=False)
    msg = gate.check(p, None, at_commit=True)
    assert msg, u"不在 index 裡卻放行 —— fail-open:path=%s" % p
    assert _r8_said(msg) and "fail-closed" in msg, (
        u"沒標明是 R8 的 fail-closed 那一支:msg=%r" % msg)
    assert os.path.basename(p) in msg, (
        u"訊息沒點名是哪個檔 —— 人不知道要去 add 什麼:msg=%r" % msg)
    assert "index" in msg and "git add" in msg, (
        u"訊息沒說出前提與修法,人會去找一個不存在的損壞檔案:msg=%r" % msg)
    assert "不得 import research/" not in msg, (
        u"把「讀不到」說成「你 import 了 research」—— 票 07 的那個代價回來了:%r" % msg)
