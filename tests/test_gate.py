# -*- coding: utf-8 -*-
"""票 01 — 兩層不變式,以及閘門自我修改的豁免。

不變式是單向的:**任何時點下,權威層的嚴格程度不得低於前哨。**
前哨擋而權威放行 = 缺陷;權威擋而前哨放行 = 合規(R4/R5 只在提交時評估就是這種)。

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

    R4/R5 只在提交時評估就是這種情況;為了讓兩層對稱而把成本推進前哨是錯的方向。
    這裡以「存在一個權威嚴於前哨的案例、而測試不因此失敗」來表達單向性。
    """
    monkeypatch.setattr(gate, "load_stage", lambda: ("implement", "01"))
    # R4/R5 只在 pre_commit 模式被呼叫,check() 本身不含它們 —— 單向性由此成立:
    # 權威層額外跑的檢查不需要在前哨有對應。
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
        root = self._repo(tmp_path, '#!/bin/sh\nexec python "$(git rev-parse '
                                    '--show-toplevel)/.claude/hooks/gate.py" --pre-commit\n')
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

    def test_provenance_does_not_exempt_r2(self, world, monkeypatch):
        """**只豁免 R3。** R2 的窗口問題是票 10 的事,兩者不得互相代勞 ——
        一個豁免同時鬆兩條規則,爆炸半徑就不再是它宣稱的那個。"""
        up, down, sha = world
        monkeypatch.setattr(gate, "load_stage", lambda: ("review", "11"))
        self._sync_in(down)
        self._prov(down, upstream_commit=sha)
        msg = gate.check("pkg/thing.py", "def f():\n    return 2\n")
        assert msg and "R2" in msg, "provenance 順手把 R2 也豁免了:%r" % msg


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
