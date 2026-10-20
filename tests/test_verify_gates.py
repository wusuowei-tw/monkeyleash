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
        "home-nonempty", "home-is-file", "claude-is-file", "marker-preexists", "home-is-symlink"])
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
            _t146_link_dir(real, home)
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
        "v-env-moved", "vi-home-symlink"])
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
                    _t146_link_dir(moved, iso.home)
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
            os.makedirs(os.path.join(target, ".git", "hooks"), exist_ok=True)  # 票 156 D-11:target 先由 prepare_target_env 備好(git init),不再假定為空
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
        # 3h 准改:trigger 改為情境專用常數(N-4;與正控 trigger 不同)。
        assert (target / getattr(vg, "SCENARIO_TRIGGER_R10")).is_file()
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
            if list(args[1:4]) == ["diff", "--cached", "--name-only"]:
                return 0, "docs/adr/verify-trigger-r10.md\n"  # 3h 准改:staged 查詢回非空(N-4)
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


# ─────────────────────────────────────────────────────────────────────────────
# 票 146 第三站 3h 紅燈(S3h-146-1)—— N-3 隔離清理拒絕 reparse point、N-4 情境 staged 非空
#
# 契約在票 146〈3h 契約與紅燈(N-1～N-4)〉。Windows 用 junction(`_winapi.CreateJunction`,不需額外權限),
# POSIX 用 symlink。哨兵目錄放 tmp_path 下、workdir 之外;新名稱以 getattr 取得,缺 ⇒ 該 node 紅。
# ─────────────────────────────────────────────────────────────────────────────

def _t146_link_dir(src, dst):
    """dst 成為指向 src 的目錄連結:Windows 用 junction,POSIX 用 symlink(3h;T146-50b / 51b 准改亦用此)。"""
    if os.name == "nt":
        import _winapi
        _winapi.CreateJunction(str(src), str(dst))
    else:
        os.symlink(str(src), str(dst))


def _t146_outside(tmp_path, deep=False):
    """workdir 之外的哨兵目錄:sentinel.txt(deep=True 再加 deep/inner.txt)。"""
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "sentinel.txt").write_bytes(b"sentinel\n")
    if deep:
        (outside / "deep").mkdir()
        (outside / "deep" / "inner.txt").write_bytes(b"inner\n")
    return outside


def _t146_rel_files(root):
    out = []
    for dirpath, _d, filenames in os.walk(str(root)):
        for f in filenames:
            out.append(os.path.relpath(os.path.join(dirpath, f), str(root)).replace(os.sep, "/"))
    return sorted(out)


def _t146_under(p, base):
    """realpath(p) 是否為 realpath(base) 本身或其後代(路徑邊界比較;不同磁碟 ⇒ False)。"""
    rp, rb = os.path.normcase(os.path.realpath(str(p))), os.path.normcase(os.path.realpath(str(base)))
    try:
        return os.path.commonpath([rp, rb]) == rb
    except ValueError:
        return False


class TestTicket146IsolationReparse:
    """票 146 3h:N-3(清理前驗 claude_root 解析位置、全樹預檢拒絕 reparse point)與 N-4(情境 trigger 與正控不同、
    staged 非空;gate 回 0 ⇒ 演習失敗)。"""

    def test_t146_82_restore_refuses_claude_root_link(self, tmp_path):
        """T146-82(behavior-red):iso.claude_root 本身換成指向 outside 的連結 ⇒ restore_user_layer SystemExit;sentinel 仍在。
        BASELINE 紅因(Windows):junction 被 `_lkind` 判為 dir,清理照做、刪到 outside。"""
        restore_user_layer = getattr(vg, "restore_user_layer")
        outside = _t146_outside(tmp_path)
        (tmp_path / "wd").mkdir()
        with getattr(vg, "isolated_home")(str(tmp_path / "wd")) as iso:
            os.rmdir(iso.claude_root)
            _t146_link_dir(outside, iso.claude_root)
            with pytest.raises(SystemExit):
                restore_user_layer(iso)
        assert (outside / "sentinel.txt").is_file()

    def test_t146_82b_restore_refuses_direct_child_link(self, tmp_path):
        """T146-82b(behavior-red):iso.claude_root/skills 是指向 outside 的連結、另有 plain.txt ⇒ SystemExit;
        sentinel 與 plain.txt 都仍在(預檢失敗時什麼都不刪)。"""
        restore_user_layer = getattr(vg, "restore_user_layer")
        outside = _t146_outside(tmp_path)
        (tmp_path / "wd").mkdir()
        with getattr(vg, "isolated_home")(str(tmp_path / "wd")) as iso:
            _t146_link_dir(outside, os.path.join(iso.claude_root, "skills"))
            plain = os.path.join(iso.claude_root, "plain.txt")
            with open(plain, "wb") as f:
                f.write(b"plain\n")
            with pytest.raises(SystemExit):
                restore_user_layer(iso)
            assert os.path.isfile(plain)
        assert (outside / "sentinel.txt").is_file()

    def test_t146_82c_restore_refuses_nested_link_without_enumerating_outside(self, tmp_path, monkeypatch):
        """T146-82c(behavior-red):巢狀 skills/synced/<D>/sub 是連結(同層有 SKILL.md、根有 plain.txt)⇒ SystemExit;
        restore_user_layer 執行期間不得列舉 outside 本身或其後代(spy 只在呼叫期間記錄);之後四個檔都仍在。"""
        restore_user_layer = getattr(vg, "restore_user_layer")
        outside = _t146_outside(tmp_path, deep=True)
        (tmp_path / "wd").mkdir()
        seen = []
        state = {"on": False}
        real_listdir, real_scandir = os.listdir, os.scandir

        def spy_listdir(path=".", *a, **k):
            if state["on"]:
                seen.append(os.fspath(path) if not isinstance(path, int) else path)
            return real_listdir(path, *a, **k)

        def spy_scandir(path=".", *a, **k):
            if state["on"]:
                seen.append(os.fspath(path) if not isinstance(path, int) else path)
            return real_scandir(path, *a, **k)
        with getattr(vg, "isolated_home")(str(tmp_path / "wd")) as iso:
            d = os.path.join(iso.claude_root, "skills", "synced", "b1")
            os.makedirs(d)
            skill = os.path.join(d, "SKILL.md")
            with open(skill, "wb") as f:
                f.write(b"# s\n")
            plain = os.path.join(iso.claude_root, "plain.txt")
            with open(plain, "wb") as f:
                f.write(b"plain\n")
            _t146_link_dir(outside, os.path.join(d, "sub"))
            monkeypatch.setattr(os, "listdir", spy_listdir)
            monkeypatch.setattr(os, "scandir", spy_scandir)
            raised = False
            state["on"] = True
            try:
                restore_user_layer(iso)
            except SystemExit:
                raised = True
            finally:
                state["on"] = False
                monkeypatch.setattr(os, "listdir", real_listdir)
                monkeypatch.setattr(os, "scandir", real_scandir)
            assert raised, "restore_user_layer 沒有拒絕巢狀連結"
            leaked = [p for p in seen if not isinstance(p, int) and _t146_under(p, outside)]
            assert leaked == [], leaked
            assert os.path.isfile(skill) and os.path.isfile(plain)
        assert (outside / "sentinel.txt").is_file() and (outside / "deep" / "inner.txt").is_file()

    def test_t146_82d_scenario_r10_refuses_claude_root_link(self, tmp_path):
        """T146-82d(behavior-red):同 T146-82 佈置 ⇒ scenario_r10(target) SystemExit;outside 遞迴列舉只有 sentinel.txt。"""
        scenario_r10 = getattr(vg, "scenario_r10")
        outside = _t146_outside(tmp_path)
        target = tmp_path / "target"
        (target / ".dev").mkdir(parents=True)
        (tmp_path / "wd").mkdir()
        with getattr(vg, "isolated_home")(str(tmp_path / "wd")) as iso:
            os.rmdir(iso.claude_root)
            _t146_link_dir(outside, iso.claude_root)
            with pytest.raises(SystemExit):
                scenario_r10(str(target))
        assert _t146_rel_files(outside) == ["sentinel.txt"], _t146_rel_files(outside)

    def test_t146_82e_require_isolation_checks_claude_root_realpath(self, tmp_path):
        """T146-82e(behavior-red):iso.claude_root 改指 workdir 內另一個真目錄(非連結)⇒ _require_isolation SystemExit。
        BASELINE 紅因:只驗 realpath(home),不驗 claude_root 的解析位置。"""
        require = getattr(vg, "_require_isolation")
        (tmp_path / "wd").mkdir()
        with getattr(vg, "isolated_home")(str(tmp_path / "wd")) as iso:
            other = os.path.join(str(tmp_path / "wd"), "other-claude")
            os.mkdir(other)
            iso.claude_root = other
            with pytest.raises(SystemExit):
                require(iso)

    def test_t146_83_scenario_trigger_differs_and_stages_nonempty(self, target, tmp_path):
        """T146-83(behavior-red):正控提交後,情境 trigger 與正控不同 ⇒ git add -A 後 staged 非空且含 SCENARIO_TRIGGER_R10。
        BASELINE 紅因:`SCENARIO_TRIGGER_R10` 不存在;情境寫同一個 trigger、staged 為空。"""
        trig = getattr(vg, "SCENARIO_TRIGGER_R10")
        assert trig != "docs/adr/verify-trigger.md", trig
        getattr(vg, "precontrol_r10")(target)
        _git(["add", "-A"], target)
        _git(["commit", "-qm", "precontrol (t146-83)"], target)
        vg.restore(target)
        (tmp_path / "wd").mkdir()
        with getattr(vg, "isolated_home")(str(tmp_path / "wd")):
            getattr(vg, "scenario_r10")(target)
        _git(["add", "-A"], target)
        staged = [n for n in _git(["diff", "--cached", "--name-only"], target).stdout.decode("utf-8").splitlines() if n]
        assert staged and trig in staged, staged

    @staticmethod
    def _wire_run(monkeypatch, commits, staged_after_precontrol, code="R10"):
        """假 sh:commit 依序回 commits;`git diff --cached --name-only` 在正控 commit 之前回非空,
        之後回 staged_after_precontrol。回 (calls, ran)。"""
        calls = {"commit": 0}
        ran = []

        def fake_sh(args, cwd, check=True):
            if len(args) > 1 and args[1] == "commit":
                calls["commit"] += 1
                return commits.pop(0)
            if list(args[1:4]) == ["diff", "--cached", "--name-only"]:
                if code in vg.PRECONTROL and calls["commit"] == 0:
                    return 0, "docs/adr/verify-trigger.md\n"
                return 0, staged_after_precontrol
            return 0, ""
        monkeypatch.setattr(vg, "sh", fake_sh)
        monkeypatch.setattr(vg, "restore", lambda t: None)
        monkeypatch.setattr(vg, "restore_user_layer", lambda iso: None)
        monkeypatch.setitem(vg.PRECONTROL, "R10", lambda t: None)
        monkeypatch.setitem(vg.SCENARIOS, code, lambda t: ran.append(t))
        return calls, ran

    def test_t146_83b_run_scenario_fails_when_staged_empty(self, tmp_path, monkeypatch):
        """T146-83b(behavior-red):正控 commit rc 0、情境 staged 查詢回空 ⇒ (False, 含「情境 staged 為空」);
        commit 恰好 1 次(正控),情境 commit 0 次。BASELINE 紅因:沒有 staged 檢查,情境照樣 commit。"""
        import types
        calls, _ran = self._wire_run(monkeypatch, [(0, ""), (1, _T146_R10_OUT)], "")
        blocked, out = vg.run_scenario(str(tmp_path), "R10", iso=types.SimpleNamespace(tag="t146-83b"))
        assert blocked is False and u"情境 staged 為空" in out, (blocked, out)
        assert calls["commit"] == 1, calls

    def test_t146_83c_run_scenario_fails_when_gate_returns_zero(self, tmp_path, monkeypatch):
        """T146-83c:正控 commit (0, "");情境 staged 非空;情境 commit 回 (0, 正確 marker + reason)⇒ False;commit 2 次。
        (印出正確訊息但 gate 回 0 ⇒ 演習判失敗;排除 nothing-to-commit 白送非零退出碼。)"""
        import types
        calls, _ran = self._wire_run(monkeypatch, [(0, ""), (0, _T146_R10_OUT)], "docs/adr/verify-trigger-r10.md\n")
        blocked, out = vg.run_scenario(str(tmp_path), "R10", iso=types.SimpleNamespace(tag="t146-83c"))
        assert blocked is False, (blocked, out)
        assert calls["commit"] == 2, calls

    def test_t146_83d_r4_generic_with_staged_check(self, tmp_path, monkeypatch):
        """T146-83d(behavior-red):R4 —— staged 非空、commit (1, "[R4] …") ⇒ True;staged 回空 ⇒ (False, 含「情境 staged 為空」)。
        BASELINE 紅因:沒有 staged 檢查,空 staged 也照樣 commit 並判擋下。"""
        calls, _ran = self._wire_run(monkeypatch, [(1, u"[R4] 鏡像缺少 x")], "docs/adr/verify-trigger.md\n", code="R4")
        blocked, out = vg.run_scenario(str(tmp_path), "R4")
        assert blocked is True, out
        calls, _ran = self._wire_run(monkeypatch, [(1, u"[R4] 鏡像缺少 x")], "", code="R4")
        blocked, out = vg.run_scenario(str(tmp_path), "R4")
        assert blocked is False and u"情境 staged 為空" in out, (blocked, out)


# ─────────────────────────────────────────────────────────────────────────────
# 票 156 S3b 紅燈 —— D-11 離線核心(Jeff 2026-10-19 約 20:01)
#
# **一般 verify_gates 必須能離線綠燈**:網路 / PyPI 是否可用,不得是它能不能綠的必要條件。
# 真的照鎖定檔建 `.venv-gates` 的是整合層(CI 明確標示的步驟,見 tests/test_ci_workflow.py)。
#
# 介面(S3b 定;實作站照此實作):
#   vg.prepare_target_env(target)  在 install 之前對暫存 target 執行 setup(核心模式:安裝步驟是假步驟)
#   vg.setup_gates_env             verify_gates 使用的 setup 模組(`_install_lock` 是真的安裝步驟)
#   vg._ev_matching_policy(target) 正二政策 = upstream profile 的有效集合 ∩ 能力邊界(不再讀全域環境)
# ─────────────────────────────────────────────────────────────────────────────

class _T156Stop(Exception):
    pass


class TestT156D11OfflineCore:

    def test_d11_a_setup_runs_before_install(self, tmp_path, monkeypatch):
        """(a):verify_gates 呼叫 install 之前,先對暫存 target 執行 setup。"""
        wd = tmp_path / "wd"
        wd.mkdir()
        order = []
        monkeypatch.setattr(vg, "prepare_target_env", lambda target: order.append(("setup", target)))

        def fake_install_main(target):
            order.append(("install", target))
            raise _T156Stop()
        monkeypatch.setattr(vg.install, "main", fake_install_main)
        with pytest.raises(_T156Stop):
            vg.main(str(wd))
        assert [o[0] for o in order] == ["setup", "install"], order
        assert order[0][1] == order[1][1], "setup 與 install 對的不是同一個 target:%r" % order

    def test_d11_b_the_core_mode_never_runs_the_real_install_or_touches_the_network(self, tmp_path,
                                                                                  monkeypatch):
        """(b):核心模式下 setup 的安裝步驟是假步驟 —— 真正的 `_install_lock` 一次都沒被呼叫;
        行程內任何 socket 連線都會撞上哨兵。"""
        import socket
        prepare = getattr(vg, "prepare_target_env", None)
        setup_mod = getattr(vg, "setup_gates_env", None)
        assert prepare is not None and setup_mod is not None, \
            "verify_gates 沒有 prepare_target_env / setup_gates_env(票 156 實作站產生)"
        real_install = []

        def sentinel_install(*a, **k):
            real_install.append(a)
            raise AssertionError("核心模式呼叫了真正的 _install_lock(會連網)")
        monkeypatch.setattr(setup_mod, "_install_lock", sentinel_install)

        def no_network(*a, **k):
            raise AssertionError("核心模式發出了網路連線:%r" % (a,))
        monkeypatch.setattr(socket.socket, "connect", no_network)
        t = tmp_path / "target"
        t.mkdir()
        for args in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
            subprocess.run(["git"] + args, cwd=str(t), capture_output=True, check=True)
        prepare(str(t))
        assert real_install == []
        assert (t / ".venv-gates").is_dir()

    def test_d11_c_the_pos2_policy_uses_the_upstream_profile_set(self, tmp_path, monkeypatch):
        """(c):正二政策的 dists = upstream profile 的有效集合 ∩ `KNOWN_DISTS`,**不讀全域環境**。
        環境裡裝的是 anyio 4.15.1(也在能力邊界內),鎖定檔是 4.15.0 ⇒ 政策必須是 4.15.0。"""
        import importlib.metadata as md
        import shutil
        t = tmp_path / "target"
        (t / ".claude" / "hooks").mkdir(parents=True)
        shutil.copy2(os.path.join(HERE, "..", ".claude", "hooks", "redlight.py"),
                     str(t / ".claude" / "hooks" / "redlight.py"))
        real_version = md.version

        def fake_version(name):
            return {"anyio": "4.15.1", "pytest": "9.1.1"}.get(name) or real_version(name)
        monkeypatch.setattr(md, "version", fake_version)
        pol = vg._ev_matching_policy(str(t))
        assert pol["dists"] == [["anyio", "4.15.0"]], pol["dists"]
        assert pol["pytest_versions"] == ["9.1.1"], pol["pytest_versions"]


# ─────────────────────────────────────────────────────────────────────────────
# 票 156 S4f-1 紅燈 —— 裁決 S4f-甲:核心模式的假安裝步驟改成「離線複製」
# (Jeff 2026-10-20 約 13:53)
#
# 核心模式從**上游已安裝**的 `<SRC_ROOT>/.venv-gates` 複製 downstream 有效集合
# (payload + `*.dist-info`)進暫存 target 的 `.venv-gates`,讓 install 的事前檢查
# 與其後的端到端情境在**不連網**時也走得通。
#
# **這裡證明的是自洽**:上游 venv 的子集能通過 downstream 身分檢查。
# 鎖定檔「真的裝得起來」由 CI 整合步驟(`id: gates-bootstrap-integration`)證明。
#
# 接縫:`_core_install_offline` 是既有的(D-11)。來源路徑的接縫 `_core_source_venv`
# 是本站**假設**的名字 —— 紅燈要的是「來源缺失 / 不合法時 fail-closed」,不是這個名字;
# S4f-2 選的接縫若不同,改 patch 目標不算改規格,斷言不得放寬。
#
# **只在上游跑**:本檔標 copy,會跟著裝進下游、也會在 verify_gates 的淨室 target 裡再跑一次;
# 那裡的 `SRC_ROOT` 是 target 自己,沒有「上游已安裝的 .venv-gates」可言。
# 判別用上游測試鎖定檔是否存在(manifest 標 skip,不出貨)—— 與 `bootstrap.sh` 選 profile 同一個慣例。
# ─────────────────────────────────────────────────────────────────────────────

_S4F_UPSTREAM_VENV = os.path.join(vg.SRC_ROOT, ".venv-gates")
_S4F_RI = os.path.join(vg.SRC_ROOT, ".claude", "portable", "runtime_identity.py")
_S4F_MARK = "[verify_gates/核心]"


def _s4f_is_upstream():
    return os.path.isfile(os.path.join(vg.SRC_ROOT, *vg.runtime_identity.LOCK_UPSTREAM_TESTS_REL.split("/")))


def _s4f_python(venv_dir):
    if os.name == "nt":
        return os.path.join(venv_dir, "Scripts", "python.exe")
    return os.path.join(venv_dir, "bin", "python")


def _s4f_site(venv_dir):
    import glob
    if os.name == "nt":
        cands = [os.path.join(venv_dir, "Lib", "site-packages")]
    else:
        cands = sorted(glob.glob(os.path.join(venv_dir, "lib", "python3.*", "site-packages")))
    cands = [c for c in cands if os.path.isdir(c)]
    assert len(cands) == 1, "找不到唯一的 site-packages:%s → %r" % (venv_dir, cands)
    return cands[0]


def _s4f_downstream_set():
    """downstream 有效集合 `{正規化名稱: 版本}`(核心鎖定檔、目前平台的 marker)。"""
    ri = vg.runtime_identity
    return ri.expected_set([ri.load_locks()["core"]], ri._marker_env())


def _s4f_dists(site):
    """site-packages 內的 dist:`{正規化名稱: Distribution}`。"""
    import importlib.metadata as md
    out = {}
    for d in md.distributions(path=[site]):
        name = d.metadata.get("Name") if d.metadata else None
        if name:
            out[vg.runtime_identity.normalize(name)] = d
    return out


def _s4f_payload(site, dist):
    """dist 在 `site` 之內、實際存在的檔案(相對 site 的路徑;不含 __pycache__)。site 之外的(Scripts/bin 進入點)不算。"""
    assert dist.files is not None, "%s 沒有 RECORD,判不出 payload" % dist.metadata.get("Name")
    site_abs = os.path.normcase(os.path.realpath(site))
    out = []
    for f in dist.files:
        p = os.path.realpath(str(dist.locate_file(f)))
        if not os.path.normcase(p).startswith(site_abs + os.sep) or not os.path.isfile(p):
            continue
        rel = os.path.relpath(p, os.path.realpath(site))
        if "__pycache__" in rel.split(os.sep):
            continue
        out.append(rel)
    return out


def _s4f_identity(target):
    """D-10 / 規格 4:target 的直譯器跑**上游**的 runtime_identity,`--repo` 指向 target。"""
    argv = [_s4f_python(os.path.join(str(target), ".venv-gates")), _S4F_RI,
            "--whoami", "--repo", str(target), "--profile", "downstream"]
    p = subprocess.run(argv, capture_output=True)
    out = (p.stdout + p.stderr).decode("utf-8", "replace")
    lines = [l for l in out.splitlines() if l.strip()]
    return p.returncode, (lines[-1] if lines else ""), out


def _s4f_sysexit_text(excinfo):
    return str(excinfo.value.code)


class TestS4fCoreCopiesFromUpstreamVenv:

    @pytest.fixture(autouse=True)
    def _upstream_only(self):
        if not _s4f_is_upstream():
            pytest.skip("上游專屬:沒有上游測試鎖定檔(下游或淨室 target)")
        assert os.path.isfile(_s4f_python(_S4F_UPSTREAM_VENV)), \
            "上游 .venv-gates 不存在 —— 這組測試只依賴上游已存在且合法的 .venv-gates,不自己建"

    def test_s4f_d_copied_target_is_complete_usable_and_passes_downstream_identity(self, tmp_path):
        """規格 2 + 4:真建環境。(i) target 直譯器 `-I` 匯入 yaml / pytest,且模組在 target 的 venv 之內;
        (ii) 每個 downstream 套件在來源 site-packages 內的檔案,target 都有同一相對路徑;不得多複製;
        (4) 上游 runtime_identity 對 target 的 downstream 身分為 ok。"""
        target = tmp_path / "target"
        vg.prepare_target_env(str(target))
        venv = os.path.join(str(target), ".venv-gates")
        py = _s4f_python(venv)

        # (i) 可用性
        p = subprocess.run([py, "-I", "-c", "import yaml, pytest; print(yaml.__file__); print(pytest.__file__)"],
                           capture_output=True)
        out = (p.stdout + p.stderr).decode("utf-8", "replace")
        assert p.returncode == 0, out
        venv_abs = os.path.normcase(os.path.realpath(venv))
        for line in [l for l in out.splitlines() if l.strip()][-2:]:
            assert os.path.normcase(os.path.realpath(line.strip())).startswith(venv_abs + os.sep), (line, venv)

        # (ii) 完整性:逐套件、逐檔
        src_site, dst_site = _s4f_site(_S4F_UPSTREAM_VENV), _s4f_site(venv)
        src = _s4f_dists(src_site)
        expected = _s4f_downstream_set()
        missing = []
        for name in sorted(expected):
            assert name in src, "上游 .venv-gates 沒有 %s —— 上游環境本身不合法" % name
            for rel in _s4f_payload(src_site, src[name]):
                if not os.path.isfile(os.path.join(dst_site, rel)):
                    missing.append((name, rel))
        assert not missing, "target 缺 %d 個檔(前 10 個):%r" % (len(missing), missing[:10])

        # 不得多複製:target 的 dist = downstream 有效集合 ∪ runtime-bootstrap 例外
        allowed = set(expected) | set(vg.runtime_identity.normalize(n)
                                      for n, _v in vg.runtime_identity.BOOTSTRAP_EXCEPTIONS)
        got = set(_s4f_dists(dst_site))
        assert got <= allowed, "多複製了:%s" % sorted(got - allowed)

        # (4) 結果可驗
        rc, last, full = _s4f_identity(target)
        assert rc == 0 and last == "identity: ok", full

    def test_s4f_d_source_is_the_upstream_repo_venv_checked_first(self, tmp_path, monkeypatch):
        """規格 1:來源是 `<SRC_ROOT>/.venv-gates`,不是 `sys.prefix`;複製**之前**先以來源直譯器跑
        上游 runtime_identity `--profile upstream`(`--repo` = 上游根)。"""
        import sys
        target = tmp_path / "target"
        bogus = tmp_path / "bogus-prefix"
        bogus.mkdir()
        monkeypatch.setattr(sys, "prefix", str(bogus))
        real_run = subprocess.run
        seen = []

        def recording_run(args, *a, **k):
            argv = [str(x) for x in args] if isinstance(args, (list, tuple)) else [str(args)]
            dst = os.path.join(str(target), ".venv-gates")
            yaml_there = os.path.isdir(dst) and any(
                os.path.isdir(os.path.join(s, "yaml")) for s in
                [os.path.join(dst, "Lib", "site-packages")] + [os.path.join(dst, "lib", v, "site-packages")
                                                             for v in ("python3.11",)])
            seen.append((argv, yaml_there))
            return real_run(args, *a, **k)
        monkeypatch.setattr(subprocess, "run", recording_run)
        vg.prepare_target_env(str(target))
        monkeypatch.undo()

        up_abs = os.path.normcase(os.path.realpath(_S4F_UPSTREAM_VENV))
        root_abs = os.path.normcase(os.path.realpath(vg.SRC_ROOT))
        checks = [(argv, yaml_there) for argv, yaml_there in seen
                  if any(os.path.basename(x) == "runtime_identity.py" for x in argv)
                  and "--profile" in argv and argv[argv.index("--profile") + 1:argv.index("--profile") + 2] == ["upstream"]]
        assert checks, "沒有看到以 upstream profile 檢查來源的呼叫:%r" % [a for a, _ in seen]
        argv, yaml_there = checks[0]
        assert os.path.normcase(os.path.realpath(argv[0])).startswith(up_abs + os.sep), argv
        assert "--repo" in argv and \
            os.path.normcase(os.path.realpath(argv[argv.index("--repo") + 1])) == root_abs, argv
        assert not yaml_there, "來源檢查發生在複製之後"

        # 複製出來的位元組來自上游 venv(不是 sys.prefix,也不是別的環境)
        src_site, dst_site = _s4f_site(_S4F_UPSTREAM_VENV), _s4f_site(os.path.join(str(target), ".venv-gates"))
        rel = os.path.join("yaml", "__init__.py")
        assert os.path.isfile(os.path.join(dst_site, rel)), "target 沒有 %s" % rel
        with open(os.path.join(src_site, rel), "rb") as a, open(os.path.join(dst_site, rel), "rb") as b:
            assert a.read() == b.read()

    def test_s4f_d_no_network_no_pip_install_and_still_identity_ok(self, tmp_path, monkeypatch):
        """規格 3:prepare 期間真的 `_install_lock` 一次都不呼叫、不起任何 `pip install` 子行程 ——
        **而且**結果仍然合法(只監測不連網的話,現行什麼都不裝的假步驟會恆綠)。"""
        def no_install_lock(*a, **k):
            raise AssertionError("核心模式呼叫了真正的 _install_lock(會連網)")
        monkeypatch.setattr(vg.setup_gates_env, "_install_lock", no_install_lock)

        def is_pip_install(args):
            argv = [str(x) for x in args] if isinstance(args, (list, tuple)) else str(args).split()
            return "pip" in argv and "install" in argv

        real_run, real_popen = subprocess.run, subprocess.Popen

        def guarded_run(args, *a, **k):
            if is_pip_install(args):
                raise AssertionError("核心模式啟動了 pip install:%r" % (args,))
            return real_run(args, *a, **k)

        def guarded_popen(args, *a, **k):
            if is_pip_install(args):
                raise AssertionError("核心模式啟動了 pip install:%r" % (args,))
            return real_popen(args, *a, **k)
        monkeypatch.setattr(subprocess, "run", guarded_run)
        monkeypatch.setattr(subprocess, "Popen", guarded_popen)

        target = tmp_path / "target"
        vg.prepare_target_env(str(target))
        monkeypatch.undo()
        rc, last, full = _s4f_identity(target)
        assert rc == 0 and last == "identity: ok", full

    def test_s4f_d_missing_source_venv_is_fail_closed(self, tmp_path, monkeypatch):
        """規格 5(一):上游沒有 `.venv-gates` ⇒ 明確 SystemExit(含 `[verify_gates/核心]`),target 不得有任何套件。"""
        nowhere = tmp_path / "no-upstream" / ".venv-gates"
        monkeypatch.setattr(vg, "_core_source_venv", lambda *a, **k: str(nowhere), raising=False)
        target = tmp_path / "target"
        with pytest.raises(SystemExit) as e:
            vg.prepare_target_env(str(target))
        assert _S4F_MARK in _s4f_sysexit_text(e), _s4f_sysexit_text(e)
        dst = os.path.join(str(target), ".venv-gates")
        if os.path.isdir(dst):
            assert not set(_s4f_dists(_s4f_site(dst))) & set(_s4f_downstream_set()), "來源缺失卻寫入了套件"

    def test_s4f_d_invalid_source_identity_is_fail_closed(self, tmp_path, monkeypatch):
        """規格 1 + 5(二):來源存在但過不了 upstream 身分(這裡用一個空 venv 當壞來源 ——
        它**不是**上游環境,只是一個離線建的反例)⇒ SystemExit(含 `[verify_gates/核心]`),target 不寫入套件。"""
        import venv
        bad = tmp_path / "bad-upstream" / ".venv-gates"
        venv.EnvBuilder(with_pip=False).create(str(bad))
        monkeypatch.setattr(vg, "_core_source_venv", lambda *a, **k: str(bad), raising=False)
        target = tmp_path / "target"
        with pytest.raises(SystemExit) as e:
            vg.prepare_target_env(str(target))
        assert _S4F_MARK in _s4f_sysexit_text(e), _s4f_sysexit_text(e)
        dst = os.path.join(str(target), ".venv-gates")
        if os.path.isdir(dst):
            assert not set(_s4f_dists(_s4f_site(dst))) & set(_s4f_downstream_set()), "來源不合法卻寫入了套件"

    def test_s4f_d_negative_control_metadata_only_copy_is_rejected(self, tmp_path, monkeypatch):
        """規格 2 負控:壞的複製(除 `packaging` 外**只**複製 `*.dist-info`、不複製 payload)
        ⇒ 正式程式碼必須在宣告成功**之前**拒絕它(SystemExit)。正常回傳 = 本測試 FAIL。

        `packaging` 例外照完整複製:runtime_identity 自己要 import 它。不留它的話,壞實作會先在
        身分檢查就倒下,而本條要逼出的是「身分 ok 之外的 payload 驗證」—— metadata 全在時
        `identity: ok` 仍可能成立,光靠它不夠。"""
        import shutil
        src_site = _s4f_site(_S4F_UPSTREAM_VENV)
        src = _s4f_dists(src_site)
        expected = _s4f_downstream_set()

        def metadata_only_copy(python, locks):
            dst_site = _s4f_site(os.path.dirname(os.path.dirname(python)))
            for name in sorted(expected):
                for rel in _s4f_payload(src_site, src[name]):
                    top = rel.split(os.sep)[0]
                    if name != "packaging" and not top.endswith(".dist-info"):
                        continue
                    os.makedirs(os.path.dirname(os.path.join(dst_site, rel)), exist_ok=True)
                    shutil.copy2(os.path.join(src_site, rel), os.path.join(dst_site, rel))
        monkeypatch.setattr(vg, "_core_install_offline", metadata_only_copy)

        target = tmp_path / "target"
        with pytest.raises(SystemExit):
            vg.prepare_target_env(str(target))
