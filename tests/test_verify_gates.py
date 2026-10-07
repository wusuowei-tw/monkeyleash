# -*- coding: utf-8 -*-
"""verify_gates 的情境隔離 —— `restore()` 要真的把 target 還原成乾淨。

票 56。由來(2026-08-17 唯讀實測):全新安裝、單次執行,跑到 R5 那一步時
commit 的輸出裡帶著一筆 **R4** 違規:

    [R4][enforce] 鏡像缺少 .claude/skills/tdd/SKILL.md —— 正典有而鏡像沒有。

來源只可能是同一次執行裡前一步的 `scenario_r4`。`restore()` 用
`git reset --hard` + `git clean -fd`,而鏡像目錄被 `.gitignore` 忽略 ——
兩個指令都碰不到它,那個刪除因此永久留著。

**為什麼這一條非有不可**:`run_scenario` 的判定是連言

    blocked = rc != 0 and ("[%s]" % code in out or "[%s/" % code in out)

殘留讓 `rc != 0` 對後續每一條走 commit 的情境(R5 / R6 / R8)**恆真** ——
真正在做事的只剩第二個連言項。今天還不產生錯判,但「讀起來在驗兩件事、
實際只驗一件」正是本專案付過三次錢的那個形狀。

**測的是 `restore()` 的後置條件,不是它的實作。** 不斷言它有沒有呼叫
`build_mirrors`,只斷言「跑完之後鏡像回得來」—— 斷言實作的話,
換一種同樣正確的修法會讓這條測試假紅。
"""
import importlib.util
import io
import os
import subprocess

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PORTABLE = os.path.join(HERE, "..", ".claude", "portable")

MIRROR_REL = ".claude/skills/tdd/SKILL.md"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(PORTABLE, filename))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


vg = _load("verify_gates_under_test", "verify_gates.py")
_install = _load("install_for_verify_gates_test", "install.py")


class TestGitignoreAssertionEnumeratesBothLists:
    """票 78 裁決 B —— 淨室的 `.gitignore` 斷言從 `.env` **一項**擴到兩組清單全部。

    ## 為什麼是枚舉不是抽查

    `GITIGNORE_FRAMEWORK` 與 `GITIGNORE_SECRETS` 是**封閉且可窮舉**的集合。
    `CLAUDE.md` 常駐檢查項逐字:**封閉且可窮舉時,枚舉勝過比對 ——
    比對的漏是未知的,枚舉的漏是不存在的。**

    舊斷言只問 `.env` 一項:其餘十幾條(框架四條、秘密清單其餘各條)
    **零護欄**,而且只在安裝當下跑一次。

    ## 這條斷言驗的是【產物 vs 規格】,不是恆真檢查

    `gitignore_gaps()` 拿**安裝出來的檔案**去比**安裝器自己的常數**。
    那不是 `F-114` 說的「用衍生欄位驗來源欄位」——
    常數是**規格**,檔案是**產物**,而本票的缺陷正是「產物沒跟上規格」。

    > **但它確實驗不到「規格本身縮水了」** —— 那一面由
    > `tests/test_install.py` 的 `test_gitignore_secrets_cover_common_shapes`
    > 與 `test_framework_ignores_unchanged` 釘著。**兩面分工,寫在這裡免得
    > 下一個人以為這條涵蓋了全部。**
    """

    def _full_body(self):
        return "\n".join(list(_install.GITIGNORE_FRAMEWORK)
                         + list(_install.GITIGNORE_SECRETS)) + "\n"

    def test_a_complete_gitignore_reports_no_gap(self):
        assert vg.gitignore_gaps(self._full_body()) == []

    def test_removing_any_single_entry_is_reported(self):
        """**有界突變:逐條拿掉,每一條都要被指名。**

        這是本條的非空性證明 —— 一個永遠回 `[]` 的實作會讓上一條綠,
        而只有這一條會紅。**逐條**而不是抽一條:清單是封閉的,枚舉得完。
        """
        entries = list(_install.GITIGNORE_FRAMEWORK) + list(_install.GITIGNORE_SECRETS)
        assert len(entries) >= 8, "清單短得可疑,枚舉沒有意義了:%r" % entries
        for dropped in entries:
            body = "\n".join(e for e in entries if e != dropped) + "\n"
            gaps = vg.gitignore_gaps(body)
            assert gaps == [dropped], (
                "拿掉 %r 之後,斷言回報的缺項是 %r —— 應該剛好是被拿掉的那一條"
                % (dropped, gaps))

    def test_a_comment_mentioning_an_entry_is_not_counted_as_present(self):
        """**行精確的另一半:註解不算數。**

        淨室這一側若用子字串,它會對一個「只有註解、沒有防護」的
        `.gitignore` 報全過 —— 那正是本票要修的安裝器缺陷的**驗收側版本**,
        而兩邊同時瞎掉的話,缺陷不會有任何訊號。
        """
        entries = list(_install.GITIGNORE_FRAMEWORK) + list(_install.GITIGNORE_SECRETS)
        body = "\n".join("# 提到 %s 但沒有真的守它" % e for e in entries) + "\n"
        assert vg.gitignore_gaps(body) == entries, (
            "全是註解的 .gitignore 被判成有守 —— 驗收側也是子字串")


def _git(args, cwd):
    p = subprocess.run(["git"] + args, cwd=cwd, capture_output=True)
    assert p.returncode == 0, (
        "測試自己的 git 前置失敗:%s\n%s"
        % (" ".join(args), (p.stdout + p.stderr).decode("utf-8", "replace")))
    return p


def _write(root, rel, text):
    dst = os.path.join(root, rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    io.open(dst, "w", encoding="utf-8", newline="\n").write(text)


@pytest.fixture()
def target(tmp_path):
    """最小的「安裝後」形狀:正典 + 兩個**被 gitignore 的**鏡像。

    鏡像被忽略是重現缺陷的必要條件,不是佈景 —— 鏡像若進版控,
    `git reset --hard` 自己就會把它還原,這條測試會綠得毫無理由。
    """
    root = str(tmp_path / "target")
    os.makedirs(root)
    _write(root, ".agents/skills/tdd/SKILL.md", "# tdd 正典\n")
    _write(root, ".claude/skills/tdd/SKILL.md", "# tdd 正典\n")
    _write(root, "skills/tdd/SKILL.md", "# tdd 正典\n")
    _write(root, ".gitignore", "/.dev/\n.claude/skills/\n/skills/\n")
    _write(root, "docs/adr/keep.md", "讓 docs/adr 在版控裡\n")
    os.makedirs(os.path.join(root, ".dev"))

    _git(["init", "-q"], root)
    _git(["config", "user.email", "t@example.invalid"], root)
    _git(["config", "user.name", "test"], root)
    _git(["add", "-A"], root)
    _git(["commit", "-qm", "base"], root)

    # 前置條件:鏡像確實不在版控裡,否則本測試量到的是 git 而不是 restore
    tracked = subprocess.run(["git", "ls-files", MIRROR_REL],
                             cwd=root, capture_output=True).stdout
    assert not tracked.strip(), (
        "%s 竟然進了版控 —— 缺陷的前提不成立,這條測試會綠在錯的理由上" % MIRROR_REL)
    return root


class TestItDoesNotCarryItsOwnCopyOfTheHeadingCriterion:
    """framework-updates/98:**`verify_gates.py` 不得再自帶發號標題的正則字面。**

    在本票之前,`scenario_r9` 裡有一行與 `.claude/hooks/gate.py:1283` **逐字相同**
    的正則 —— portable 這一側因此有**兩份**字面(另一份在 `sync.py`,而且是鬆的)。
    現在兩處都改用 `.claude/portable/friction_heading.py` 的那一份,全庫 3 份 -> 2 份。

    ## 這條測試的三句限制,寫出來免得它被讀成別的東西

    1. **本條是「關於沒有什麼」的斷言,對修法中立。**
       它不說要用哪個模組、不說要怎麼取得判準 —— 只說「這裡不再有一份自己的字面」。
       任何正確的修法都讓它保持綠;只有「又長出一份」才讓它紅。
    2. **它守的是「不要再長出第五份字面」,不是行為。**
       行為那一半由 `tests/test_gate.py::TestBothHeadingCriteriaAgree` 釘住
       (兩份判準對同一組標題行給出相同判定)。
       本條刻意不碰行為 —— 舊字面與新常數對任何輸入答案都一樣,**行為上取不到紅**。
    3. **共用常數若搬家,本條不受影響。**
       哪天那份判準從 `friction_heading.py` 併去別的模組,本條照樣綠 ——
       這正是本檔檔頭那句「斷言實作的話,換一種同樣正確的修法會讓這條測試假紅」
       要避開的東西。所以本條只斷言**缺席**,不斷言**出處**。

    ## 斷言對象是**程式碼**,不是註解或 docstring

    本票在 `verify_gates.py` 留下的註解**沒有帶那個字面**,而且應該保持那樣。
    但若將來有人在註解或 docstring 裡引用它(例如解釋修法的由來),
    **本條不該因此變紅** —— 註解裡的一份字面不會被執行,它不是第五份實作。
    所以判定走 `ast`:只看程式碼裡的字串常數,docstring 與註解都排除。
    """

    SRC = os.path.join(PORTABLE, "verify_gates.py")
    NEEDLE = "^##"

    def _code_string_literals(self):
        """回傳這支檔案裡**程式碼**用到的字串常數(排除 docstring;註解本來就不是常數)。"""
        import ast as _ast
        tree = _ast.parse(io.open(self.SRC, encoding="utf-8").read(),
                          filename=self.SRC)
        docstrings = set()
        for node in _ast.walk(tree):
            if isinstance(node, (_ast.Module, _ast.ClassDef,
                                 _ast.FunctionDef, _ast.AsyncFunctionDef)):
                body = getattr(node, "body", None) or []
                if (body and isinstance(body[0], _ast.Expr)
                        and isinstance(body[0].value, _ast.Constant)
                        and isinstance(body[0].value.value, str)):
                    docstrings.add(id(body[0].value))
        out = []
        for node in _ast.walk(tree):
            if (isinstance(node, _ast.Constant) and isinstance(node.value, str)
                    and id(node) not in docstrings):
                out.append(node.value)
        return out

    def test_no_heading_regex_literal_remains_in_the_code(self):
        offenders = [lit for lit in self._code_string_literals()
                     if self.NEEDLE in lit]
        assert not offenders, (
            "verify_gates.py 的程式碼裡還有發號標題的正則字面:%r —— "
            "portable 這一側只該有一份(framework-updates/98)。"
            "同缺陷的兩份實作必然漂開(F-058 家族)。" % (offenders,))

    def test_the_check_ignores_docstrings_and_comments(self):
        """**釘住上面那條看的是程式碼,不是散文。**

        沒有這條的話,`test_no_heading_regex_literal_remains_in_the_code` 可能
        其實是在對整個檔案做字串搜尋 —— 那樣的話,任何一句**解釋**這個修法的
        註解都會把它變紅,而那是假紅。

        用**合成樣本**驗機制,不依賴 `verify_gates.py` 當下的內容:
        一份把那個字面只放在 docstring 與註解裡的原始碼,萃取器必須回空;
        而把它放進程式碼時,萃取器必須抓到。**兩個方向都驗,否則恆真。**
        """
        import ast as _ast

        def extract(src):
            tree = _ast.parse(src)
            docs = set()
            for node in _ast.walk(tree):
                if isinstance(node, (_ast.Module, _ast.ClassDef,
                                     _ast.FunctionDef, _ast.AsyncFunctionDef)):
                    body = getattr(node, "body", None) or []
                    if (body and isinstance(body[0], _ast.Expr)
                            and isinstance(body[0].value, _ast.Constant)
                            and isinstance(body[0].value.value, str)):
                        docs.add(id(body[0].value))
            return [n.value for n in _ast.walk(tree)
                    if isinstance(n, _ast.Constant) and isinstance(n.value, str)
                    and id(n) not in docs]

        prose_only = u"\n".join([
            u'"""說明:舊版用的是 ^## 開頭的正則。"""',
            u'# 註解也提到 ^## 這個字面',
            u'x = 1',
        ])
        assert not [l for l in extract(prose_only) if self.NEEDLE in l], (
            "萃取器吃到了 docstring 或註解 —— 那會讓解釋修法的散文變成假紅")

        in_code = u"\n".join([u'import re', u'P = re.compile(r"^##x")'])
        assert [l for l in extract(in_code) if self.NEEDLE in l], (
            "萃取器連程式碼裡的字面都抓不到 —— 上一條會恆綠")

class TestScenarioR4LeavesTheTargetClean:
    """`scenario_r4` 跑完再 `restore()`,target 必須回到乾淨。"""

    def test_the_scenario_really_deletes_the_mirror_file(self, target):
        """**前置控制**:情境真的做了它宣稱的事。

        少了這一條,主紅燈可能綠在「情境根本沒刪東西」上 ——
        而那種綠與修好了長得一模一樣。
        """
        vg.scenario_r4(target)
        assert not os.path.exists(os.path.join(target, MIRROR_REL.replace("/", os.sep))), \
            "scenario_r4 沒有刪掉鏡像檔,這條測試底下的主張全部落空"

    def test_restore_brings_the_deleted_mirror_file_back(self, target):
        """**主紅燈**:被忽略的鏡像檔,`restore()` 之後要回得來。

        紅的時候代表:R4 之後的每一條情境都在一個帶著 R4 違規的 repo 上跑。
        """
        vg.scenario_r4(target)
        vg.restore(target)
        assert os.path.exists(os.path.join(target, MIRROR_REL.replace("/", os.sep))), \
            ("restore() 之後 %s 仍然不見 —— 下一條規則會在一個帶著 R4 違規的 "
             "repo 上跑,而它的 `rc != 0` 那一半因此是白送的。" % MIRROR_REL)

    def test_restore_still_cleans_the_tracked_side(self, target):
        """**反控**:追蹤側本來就還原得了。

        沒有這一條的話,主紅燈可能被讀成「restore 整個壞掉」——
        實際上它對追蹤側是好的,壞的只有被忽略的那一半。
        """
        vg.scenario_r4(target)
        vg.restore(target)
        dirty = subprocess.run(["git", "status", "--porcelain"],
                               cwd=target, capture_output=True).stdout
        assert not dirty.strip(), \
            "追蹤側沒有被還原乾淨:%r" % dirty.decode("utf-8", "replace")
        assert not os.path.exists(os.path.join(target, "docs", "adr", "verify-trigger.md")), \
            "情境寫的未追蹤檔沒有被清掉"


# 票 145 Station 3g 紅燈 #33(〈四十六〉46.4 第 4、5 點;規劃檔 docs/audits/2026-10-03-m1a-station3g-redlight-plan.md P5)。
# 淨室的兩正三負由 `verify_gates.EVIDENCE_SCENARIOS` 列舉,比照 `SCENARIOS` 的「規則 ↔ 情境」對照。
# **這一條只證明情境有接線,不證明情境結果** —— 結果由 4g 本機實跑 verify_gates 照錄(〈四十八〉48.1 第 7 點)。
_EVIDENCE_SCENARIO_KEYS = {
    "pos1-uninitialized",       # 正一:未初始化 ⇒ 框架測試全綠、authority 為 unknown
    "pos2-initialized",         # 正二:已提交且相符的 policy ⇒ 紅 → 固定全套 → true → 合法退休
    "neg1-mismatch",            # 負一:policy / environment 不符 ⇒ unknown
    "neg2-worktree-differs",    # 負二:HEAD 有 policy、worktree 不同 ⇒ unknown
    "neg3-worktree-only",       # 負三:worktree 有 policy、HEAD 沒有 ⇒ unknown
}


def test_every_evidence_policy_scenario_is_wired():
    """#33。分類:behavior-red。

    `verify_gates.EVIDENCE_SCENARIOS` 必須是 dict,鍵恰為兩正三負五個情境,值皆可呼叫。
    BASELINE(560f618)上失敗的原因:`.claude/portable/verify_gates.py` 沒有 `EVIDENCE_SCENARIOS`(只有 `SCENARIOS`,`:225-235`)。
    """
    table = getattr(vg, "EVIDENCE_SCENARIOS", None)
    assert isinstance(table, dict), "verify_gates 沒有 EVIDENCE_SCENARIOS:淨室的兩正三負沒有接線"
    assert set(table) == _EVIDENCE_SCENARIO_KEYS, sorted(table)
    assert all(callable(f) for f in table.values()), table


# ─────────────────────────────────────────────────────────────────────────────
# 票 146 第三站 3g 紅燈(S3g-146-1)—— 淨室家目錄隔離(G-1)、R10 情境與原因斷言(G-3)
#
# 契約在票 146〈3g 契約與紅燈〉。新名稱一律在測試內 getattr 取得;缺 ⇒ 該 node 以 AttributeError 紅,
# 不讓收集失敗。真實 ~/.claude 一律不碰:需要家目錄的佈置先把 USERPROFILE 與 HOME 都指到 tmp。
# Windows 上 symlink 案 skip。marker 的位置以 `<home>/<ISOLATION_MARKER>` 佈置(契約:建 home、home/.claude、marker)。
# ─────────────────────────────────────────────────────────────────────────────

_T146_SKIP_SYMLINK = pytest.mark.skipif("os.name == 'nt'", reason="Windows 建 symlink 需要額外權限;POSIX 才產得出來")
_T146_R10_OUT = u"[R10/fail-closed] 未受管入口：synced（額外 2 / 缺少 0 / 內容不符 0）"


class _T146Stop(Exception):
    pass


def _t146_norm(p):
    return os.path.normcase(os.path.abspath(str(p)))


def _t146_tree(root):
    """root 底下所有項目的 (相對路徑, 型別, 位元組或 None)。"""
    out = []
    for dirpath, dirnames, filenames in os.walk(str(root)):
        for d in sorted(dirnames):
            out.append((os.path.relpath(os.path.join(dirpath, d), str(root)), "dir", None))
        for f in sorted(filenames):
            full = os.path.join(dirpath, f)
            with open(full, "rb") as fh:
                out.append((os.path.relpath(full, str(root)), "file", fh.read()))
    return sorted(out)


class TestTicket146Cleanroom:
    """票 146 3g:verify_gates 的隔離家目錄 context、R10 情境、正控與原因斷言。全部在 S3g-146-1 預期失敗(Windows symlink 案 skip)。"""

    @pytest.mark.parametrize("pre", ["both-set", "both-absent"])
    def test_t146_50_isolated_home_sets_both_vars_and_restores(self, tmp_path, monkeypatch, pre):
        """T146-50(behavior-red):with 內 expanduser("~") == iso.home == <wd>/home、兩變數 == iso.home、
        claude_root 為空目錄、marker 內容 == token、current_isolation() is iso;離開後 environ 與進入前完全相同、current 為 None。
        BASELINE 紅因:`vg.isolated_home` 不存在。"""
        isolated_home = getattr(vg, "isolated_home")
        current = getattr(vg, "current_isolation")
        if pre == "both-set":
            monkeypatch.setenv("USERPROFILE", str(tmp_path / "pre-up"))
            monkeypatch.setenv("HOME", str(tmp_path / "pre-home"))
        else:
            monkeypatch.delenv("USERPROFILE", raising=False)
            monkeypatch.delenv("HOME", raising=False)
        wd = tmp_path / "wd"
        wd.mkdir()
        before = dict(os.environ)
        with isolated_home(str(wd)) as iso:
            want = _t146_norm(wd / getattr(vg, "ISOLATED_HOME_DIRNAME"))
            assert _t146_norm(iso.home) == want, iso.home
            assert _t146_norm(os.path.expanduser("~")) == want
            assert _t146_norm(os.environ["USERPROFILE"]) == want and _t146_norm(os.environ["HOME"]) == want
            assert os.path.isdir(iso.claude_root) and os.listdir(iso.claude_root) == []
            assert os.path.isfile(iso.marker) and not os.path.islink(iso.marker)
            with open(iso.marker, encoding="utf-8") as f:
                assert f.read() == iso.token
            assert current() is iso
        assert dict(os.environ) == before
        assert current() is None

    @pytest.mark.parametrize("case", [
        "home-nonempty", "home-is-file", "claude-is-file", "marker-preexists",
        pytest.param("home-is-symlink", marks=_T146_SKIP_SYMLINK)])
    def test_t146_50b_isolated_home_refuses_bad_preexisting(self, tmp_path, case):
        """T146-50b(behavior-red):home 非空 / home 是檔 / .claude 是檔 / marker 已存在 / home 是 symlink ⇒ 進入即 SystemExit;
        預置物位元組不變、environ 不變、current_isolation() 為 None。BASELINE 紅因:`vg.isolated_home` 不存在。"""
        isolated_home = getattr(vg, "isolated_home")
        current = getattr(vg, "current_isolation")
        wd = tmp_path / "wd"
        wd.mkdir()
        home = wd / getattr(vg, "ISOLATED_HOME_DIRNAME")
        marker_name = getattr(vg, "ISOLATION_MARKER")
        if case == "home-nonempty":
            home.mkdir()
            (home / "keep.txt").write_bytes(b"keep\n")
        elif case == "home-is-file":
            home.write_bytes(b"not a dir\n")
        elif case == "claude-is-file":
            home.mkdir()
            (home / ".claude").write_bytes(b"not a dir\n")
        elif case == "marker-preexists":
            home.mkdir()
            (home / marker_name).write_bytes(b"stale-token")
        else:
            real = tmp_path / "elsewhere"
            real.mkdir()
            os.symlink(str(real), str(home))
        snap = _t146_tree(wd)
        env = dict(os.environ)
        with pytest.raises(SystemExit):
            with isolated_home(str(wd)):
                pass
        assert _t146_tree(wd) == snap, case
        assert dict(os.environ) == env
        assert current() is None

    def test_t146_50c_isolated_home_restores_on_exception(self, tmp_path):
        """T146-50c(behavior-red):with 內 raise RuntimeError ⇒ 外傳;environ 還原;current_isolation() 為 None。
        BASELINE 紅因:`vg.isolated_home` 不存在。"""
        isolated_home = getattr(vg, "isolated_home")
        current = getattr(vg, "current_isolation")
        wd = tmp_path / "wd"
        wd.mkdir()
        env = dict(os.environ)
        with pytest.raises(RuntimeError):
            with isolated_home(str(wd)):
                raise RuntimeError("t146-50c")
        assert dict(os.environ) == env
        assert current() is None

    def test_t146_50d_isolated_home_refuses_nesting(self, tmp_path):
        """T146-50d(behavior-red):巢狀進入 ⇒ SystemExit;外層 iso 仍是 current。BASELINE 紅因:`vg.isolated_home` 不存在。"""
        isolated_home = getattr(vg, "isolated_home")
        current = getattr(vg, "current_isolation")
        (tmp_path / "wd1").mkdir()
        (tmp_path / "wd2").mkdir()
        with isolated_home(str(tmp_path / "wd1")) as outer:
            with pytest.raises(SystemExit):
                with isolated_home(str(tmp_path / "wd2")):
                    pass
            assert current() is outer
        assert current() is None

    def test_t146_51_restore_user_layer_clears_only_isolated_root(self, tmp_path):
        """T146-51(behavior-red):restore_user_layer(iso) 清空 claude_root(保留空目錄),home 下的 marker 仍在。
        BASELINE 紅因:`vg.restore_user_layer` 不存在。"""
        isolated_home = getattr(vg, "isolated_home")
        restore_user_layer = getattr(vg, "restore_user_layer")
        (tmp_path / "wd").mkdir()
        with isolated_home(str(tmp_path / "wd")) as iso:
            p = os.path.join(iso.claude_root, "skills", "synced", "x", "y.md")
            os.makedirs(os.path.dirname(p))
            with open(p, "wb") as f:
                f.write(b"y\n")
            restore_user_layer(iso)
            assert os.path.isdir(iso.claude_root) and os.listdir(iso.claude_root) == []
            assert os.path.isfile(iso.marker)

    @pytest.mark.parametrize("case", [
        "i-marker-deleted", "ii-marker-changed", "iii-forged-namespace", "iv-after-exit",
        "v-env-moved", pytest.param("vi-home-symlink", marks=_T146_SKIP_SYMLINK)])
    def test_t146_51b_restore_user_layer_refuses(self, tmp_path, monkeypatch, case):
        """T146-51b(behavior-red):marker 刪除 / 內容改變 / 偽造 iso / context 已結束 / expanduser 不是 iso.home /
        iso.home 換成 symlink ⇒ 各 SystemExit,事前放的檔仍在。BASELINE 紅因:`vg.isolated_home` 不存在。"""
        import shutil
        import types
        isolated_home = getattr(vg, "isolated_home")
        restore_user_layer = getattr(vg, "restore_user_layer")
        (tmp_path / "wd").mkdir()
        with isolated_home(str(tmp_path / "wd")) as iso:
            planted = os.path.join(iso.claude_root, "keep.md")
            with open(planted, "wb") as f:
                f.write(b"keep\n")
            if case == "iv-after-exit":
                pass
            else:
                target = iso
                if case == "i-marker-deleted":
                    os.remove(iso.marker)
                elif case == "ii-marker-changed":
                    with open(iso.marker, "w", encoding="utf-8") as f:
                        f.write("not-the-token")
                elif case == "iii-forged-namespace":
                    target = types.SimpleNamespace(workdir=iso.workdir, home=iso.home, claude_root=iso.claude_root,
                                                   marker=iso.marker, token=iso.token)
                elif case == "v-env-moved":
                    other = tmp_path / "other-home"
                    other.mkdir()
                    monkeypatch.setenv("USERPROFILE", str(other))
                    monkeypatch.setenv("HOME", str(other))
                else:
                    moved = str(iso.home) + "-moved"
                    shutil.move(str(iso.home), moved)
                    os.symlink(moved, str(iso.home))
                    planted = os.path.join(moved, os.path.basename(str(iso.claude_root)), "keep.md")
                with pytest.raises(SystemExit):
                    restore_user_layer(target)
                assert os.path.isfile(planted), case
        if case == "iv-after-exit":
            with pytest.raises(SystemExit):
                restore_user_layer(iso)
            assert os.path.isfile(planted), case

    def test_t146_52_main_enters_isolation_before_install(self, tmp_path, monkeypatch):
        """T146-52(behavior-red):main 在呼叫 install.main 之前已進入隔離 —— 假 install.main 記到的 expanduser / 兩變數 ==
        <wd>/home、current_isolation() 非 None;_Stop 外傳後 environ 還原、current 為 None。
        BASELINE 紅因:main 沒有隔離,記到的是真實家目錄。"""
        wd = tmp_path / "wd"
        wd.mkdir()
        seen = {}

        def fake_main(target):
            seen["home"] = os.path.expanduser("~")
            seen["USERPROFILE"] = os.environ.get("USERPROFILE")
            seen["HOME"] = os.environ.get("HOME")
            cur = getattr(vg, "current_isolation", None)
            seen["active"] = bool(cur and cur() is not None)
            raise _T146Stop()
        monkeypatch.setattr(vg.install, "main", fake_main)
        env = dict(os.environ)
        with pytest.raises(_T146Stop):
            vg.main(str(wd))
        want = _t146_norm(wd / "home")
        assert _t146_norm(seen["home"]) == want, seen
        assert _t146_norm(seen["USERPROFILE"]) == want and _t146_norm(seen["HOME"]) == want, seen
        assert seen["active"] is True, seen
        assert dict(os.environ) == env
        assert getattr(vg, "current_isolation")() is None

    def test_t146_52b_main_loads_target_gate_inside_isolation(self, tmp_path, monkeypatch):
        """T146-52b(behavior-red):load_target_gate 在隔離內被呼叫(expanduser == <wd>/home)。
        BASELINE 紅因:main 沒有隔離。"""
        wd = tmp_path / "wd"
        wd.mkdir()
        seen = {}

        def fake_main(target):
            os.makedirs(os.path.join(target, ".git", "hooks"))
            with open(os.path.join(target, ".git", "hooks", "pre-commit"), "w", encoding="utf-8") as f:
                f.write("#!/bin/sh\npython .claude/portable/leak_scan.py --staged\n")
            with open(os.path.join(target, ".gitignore"), "w", encoding="utf-8") as f:
                f.write("\n".join(list(_install.GITIGNORE_FRAMEWORK) + list(_install.GITIGNORE_SECRETS)) + "\n")

        def fake_load(target):
            seen["home"] = os.path.expanduser("~")
            raise _T146Stop()
        monkeypatch.setattr(vg.install, "main", fake_main)
        monkeypatch.setattr(vg, "load_target_gate", fake_load)
        with pytest.raises(_T146Stop):
            vg.main(str(wd))
        assert _t146_norm(seen["home"]) == _t146_norm(wd / "home"), seen

    @pytest.mark.parametrize("case", ["no-marker", "marker-without-context"])
    def test_t146_53_scenario_r10_refuses_without_active_context(self, tmp_path, monkeypatch, case):
        """T146-53(behavior-red):沒有有效 context(即使 marker 檔存在)⇒ scenario_r10 SystemExit,假家目錄只有預置物。
        BASELINE 紅因:`vg.scenario_r10` 不存在。"""
        scenario_r10 = getattr(vg, "scenario_r10")
        fake = tmp_path / "fakehome"
        (fake / ".claude").mkdir(parents=True)
        if case == "marker-without-context":
            (fake / getattr(vg, "ISOLATION_MARKER")).write_bytes(b"forged-token")
        monkeypatch.setenv("USERPROFILE", str(fake))
        monkeypatch.setenv("HOME", str(fake))
        target = tmp_path / "target"
        (target / ".dev").mkdir(parents=True)
        snap = _t146_tree(fake)
        with pytest.raises(SystemExit):
            scenario_r10(str(target))
        assert _t146_tree(fake) == snap, case

    def test_t146_53b_scenario_r10_plants_exactly_two_entries(self, tmp_path):
        """T146-53b(behavior-red):隔離 context 內 scenario_r10 回 None;claude_root 下恰好兩個 regular file(內容如契約);
        trigger 檔存在;stage 為 implement。BASELINE 紅因:`vg.scenario_r10` 不存在。"""
        import json
        scenario_r10 = getattr(vg, "scenario_r10")
        isolated_home = getattr(vg, "isolated_home")
        target = tmp_path / "target"
        (target / ".dev").mkdir(parents=True)
        (tmp_path / "wd").mkdir()
        with isolated_home(str(tmp_path / "wd")) as iso:
            assert scenario_r10(str(target)) is None
            files = []
            for dirpath, _d, filenames in os.walk(iso.claude_root):
                for f in filenames:
                    files.append(os.path.relpath(os.path.join(dirpath, f), iso.claude_root).replace(os.sep, "/"))
            assert sorted(files) == ["skills/synced/.bucket-vgbucket", "skills/synced/vgbucket/SKILL.md"], files
            with open(os.path.join(iso.claude_root, "skills", "synced", "vgbucket", "SKILL.md"), encoding="utf-8") as f:
                assert f.read() == "# verify_gates r10\n"
            with open(os.path.join(iso.claude_root, "skills", "synced", ".bucket-vgbucket"), encoding="utf-8") as f:
                assert f.read() == "vgbucket\n"
        assert (target / "docs" / "adr" / "verify-trigger.md").is_file()
        stage = json.loads((target / ".dev" / "pipeline.json").read_text(encoding="utf-8"))["current_stage"]
        assert stage == "implement", stage

    def test_t146_54_r10_wiring_tables(self):
        """T146-54(behavior-red):SCENARIOS / EXPECTED_REASON / EXPECTED_MARKER / PRECONTROL 的 R10 接線;R1–R9 不在 EXPECTED_MARKER。
        BASELINE 紅因:`vg.scenario_r10` 等名稱不存在。"""
        scenario_r10 = getattr(vg, "scenario_r10")
        precontrol_r10 = getattr(vg, "precontrol_r10")
        assert vg.SCENARIOS["R10"] is scenario_r10
        assert getattr(vg, "EXPECTED_REASON")["R10"] == u"未受管入口：synced（額外 2"
        marker = getattr(vg, "EXPECTED_MARKER")
        assert marker["R10"] == "[R10/fail-closed]"
        assert not [c for c in ("R%d" % i for i in range(1, 10)) if c in marker], sorted(marker)
        assert getattr(vg, "PRECONTROL")["R10"] is precontrol_r10

    @pytest.mark.parametrize("case", ["a-precontrol-blocked", "b-r10-blocked-right-reason", "c-r10-wrong-reason",
                                      "d-r4-generic", "e-r10-bare-code", "f-r10-other-subtag"])
    def test_t146_55_run_scenario_requires_code_reason_and_precontrol(self, tmp_path, monkeypatch, case):
        """T146-55(behavior-red):正控未放行 ⇒ (False, 「正控未放行」) 且情境不跑;R10 必須同時含 "[R10/fail-closed]"
        與指定原因(只有 "[R10]" 或其他 "[R10/…]" ⇒ False);R1–R9 保留原代號判定;R10 成立時以傳入 iso 清理恰好一次。
        BASELINE 紅因:`run_scenario` 沒有 iso 參數、沒有 PRECONTROL / restore_user_layer。"""
        import types
        target = tmp_path / "target"
        (target / ".dev").mkdir(parents=True)
        code = "R4" if case == "d-r4-generic" else "R10"
        commits = {
            "a-precontrol-blocked": [(1, "pre-control blocked")],
            "b-r10-blocked-right-reason": [(0, ""), (1, _T146_R10_OUT)],
            "c-r10-wrong-reason": [(0, ""), (1, u"[R10/fail-closed] claude_root 無法確定")],
            "d-r4-generic": [(1, u"[R4] 鏡像缺少 x")],
            "e-r10-bare-code": [(0, ""), (1, u"[R10] 未受管入口：synced（額外 2 / 缺少 0 / 內容不符 0）")],
            "f-r10-other-subtag": [(0, ""), (1, u"[R10/shadow] 未受管入口：synced（額外 2 / 缺少 0 / 內容不符 0）")],
        }[case]
        cleaned, ran = [], []

        def fake_sh(args, cwd, check=True):
            if len(args) > 1 and args[1] == "commit":
                return commits.pop(0)
            return 0, ""
        monkeypatch.setattr(vg, "sh", fake_sh)
        monkeypatch.setattr(vg, "restore", lambda t: None)
        monkeypatch.setattr(vg, "restore_user_layer", lambda iso: cleaned.append(iso))
        monkeypatch.setitem(vg.PRECONTROL, "R10", lambda t: None)
        monkeypatch.setitem(vg.SCENARIOS, code, lambda t: ran.append(t))
        iso = types.SimpleNamespace(tag="t146-55") if code == "R10" else None
        blocked, out = vg.run_scenario(str(target), code, iso=iso)
        if case == "a-precontrol-blocked":
            assert blocked is False and u"正控未放行" in out, out
            assert ran == [], ran
        elif case == "b-r10-blocked-right-reason":
            assert blocked is True and _T146_R10_OUT in out, out
            assert cleaned == [iso], cleaned
        elif case == "d-r4-generic":
            assert blocked is True, out
        else:
            assert blocked is False, (case, out)
