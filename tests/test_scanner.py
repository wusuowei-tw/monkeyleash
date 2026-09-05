# -*- coding: utf-8 -*-
"""掃描器共骨架 —— 兩支掃描器(leak_scan / cookie_ban)合一後的共同判定邏輯。

合一的**核心約束**:豁免綁在**規則組**上,不是綁在掃描器上。

  `.md` 裡的 cookie 選項名 -> 放行(規則的說明本身必須寫得出來)
  `.md` 裡的金鑰           -> 擋  (散文裡的金鑰就是外洩的金鑰)

同一個副檔名,兩個相反的正確答案。一套豁免套用全部 pattern 的話,合一本身
就會把這個差異壓平 —— **而壓平的方向是 fail-open**(取寬的那一邊)。
所以骨架的資料結構必須容得下逐組的適用範圍,這不是設計品味,是合一的前提。

失效方向:掃描器的失效方向是**靜默放行**。所以本檔的每一條「讀不動」
「取不到清單」「解不開編碼」都往「計為違規」倒,而且都有反控 ——
少了反控,「全部當成違規」也會讓正控過(那是另一種壞掉,只是吵)。

**這個測試檔自己也被 shipped-tree-is-clean 掃描**,所以偵測樣本一律組裝,
不寫死任何敏感字面。
"""

import importlib.util  # noqa: F401  (下方 _load 用)
import io
import os
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "scanner_under_test", ROOT / ".claude" / "portable" / "scanner.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sc = _load()

# ─────────────────────────────────────────────────────────────────────────────
# 樣本字串一律**執行時拼裝**,不得靜置成文。
#
# 理由不是這個 repo 的潔癖:框架的出貨檔案會落進每一個安裝的 repo,而那些 repo
# 各自有自己的內容守衛(影音 repo 的 D21 cookie 護欄就擋下過本檔)。
# **框架的測試檔在下游是被掃描的資料,不是可信的自己人**,而框架不知道下游
# 裝了哪些守衛,也不該知道。所以出貨檔案必須對任意內容守衛惰性。
#
# 拼接點的選法:切完之後**每一段靜置文字**都不得比中下游的 pattern。
# 本檔原本的寫法把切點放在選項名的**尾段**之前,於是前半仍是一個完整的選項名,
# 而下游的短 pattern 在連字號處就成立詞邊界 —— 照樣比中。
# **切點必須落在第一個詞的中間**,讓每一段都不是任何 pattern 的完整前綴。
#
# 連這段註解都不能舉字面反例:寫下「錯的寫法長什麼樣」會把它重新種回檔案裡。
# 防禦的說明長得像它要擋的東西,是掃描器這一類工具的通病(F-062)。
#
# 測試效力不變:掃描器收到的仍是拼好的完整字串。
# ─────────────────────────────────────────────────────────────────────────────
SECRET = "ghp" + "_" + ("A" * 24)
COOKIE_OPT = "--cook" + "ies-from-browser"
COOKIE_RE = "--cook" + "ies-from-browser"


def _groups():
    """兩組規則,適用範圍相反 —— 合一的核心約束就靠這個結構表達。"""
    return [
        sc.RuleGroup("leak", [r"\bghp_[A-Za-z0-9]{20,}"]),               # 散文照掃
        # pattern 也是拼裝的:regex 字面量本身就是完整字串,靜置一樣會被下游比中。
        sc.RuleGroup("cookie", [COOKIE_RE],
                     skip_suffix=(".md", ".rst", ".adoc")),              # 散文豁免
    ]


def _w(tmp_path, name, text, mode="w"):
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    if mode == "wb":
        io.open(p, "wb").write(text)
    else:
        io.open(p, "w", encoding="utf-8", newline="\n").write(text)
    return str(p)


# ─────────────────────────────────────────────────────────────────────────────
# 一、逐組豁免範圍 —— 合一不得把兩邊的差異壓平
# ─────────────────────────────────────────────────────────────────────────────

class TestExemptionScopeIsPerRuleGroup:

    def test_a_secret_in_prose_is_still_caught(self, tmp_path):
        """`.md` 裡的金鑰 -> 擋。散文豁免對金鑰完全不成立。"""
        hits = sc.scan_paths([_w(tmp_path, "docs/note.md", "token=" + SECRET)],
                             _groups(), root=str(tmp_path))
        assert [h.group for h in hits] == ["leak"], hits

    def test_a_cookie_option_in_prose_is_allowed(self, tmp_path):
        """`.md` 裡的 cookie 選項名 -> 放行。

        規則的說明本身必須寫得出來:ADR 要解釋擋的是哪個選項、friction 要記錄
        踩過的坑。掃散文的話每一份解釋這條規則的文件都得規避字面,
        而那種稅最後會讓人去放寬 pattern。
        """
        hits = sc.scan_paths([_w(tmp_path, "docs/adr.md", "禁止 " + COOKIE_OPT)],
                             _groups(), root=str(tmp_path))
        assert hits == [], hits

    def test_both_hold_in_the_same_file(self, tmp_path):
        """**同一個檔案、同一次掃描**,兩個相反的答案要同時成立。

        分開兩個檔案測的話,「兩組共用同一份豁免」這個缺陷測不出來 ——
        它只有在同一次判定裡兩組拿到不同範圍時才會現形。
        """
        p = _w(tmp_path, "docs/both.md",
               "說明:禁止 " + COOKIE_OPT + "\ntoken=" + SECRET + "\n")
        hits = sc.scan_paths([p], _groups(), root=str(tmp_path))
        assert [h.group for h in hits] == ["leak"], \
            "散文豁免被套到金鑰那組(壓平,方向 fail-open):%r" % hits

    def test_a_cookie_option_in_code_is_caught(self, tmp_path):
        """反控:同一組 pattern 在非散文檔案照樣命中 —— 豁免的只有散文格式。"""
        hits = sc.scan_paths([_w(tmp_path, "dl.py", "cmd = '" + COOKIE_OPT + "'")],
                             _groups(), root=str(tmp_path))
        assert [h.group for h in hits] == ["cookie"], hits


# ─────────────────────────────────────────────────────────────────────────────
# 二、讀不動一律 fail-closed(leak_scan 那邊原本是 except: continue)
# ─────────────────────────────────────────────────────────────────────────────

class TestUnreadableIsAViolation:

    def test_a_cp950_file_with_a_secret_is_caught(self, tmp_path):
        """正控:cp950 存的檔案裡的金鑰要抓得到。

        zh-TW Windows 上 cp950 是預設編碼。原本只用 utf-8 開檔,
        UnicodeDecodeError 被 `except: continue` 吞掉 -> **整個檔案靜默跳過**。
        """
        raw = (u"# 註解:設定\ntoken=" + SECRET + u"\n").encode("cp950")
        hits = sc.scan_paths([_w(tmp_path, "conf.ps1", raw, mode="wb")],
                             _groups(), root=str(tmp_path))
        assert [h.group for h in hits] == ["leak"], hits

    def test_a_clean_cp950_file_passes(self, tmp_path):
        """**反控**:cp950 的乾淨檔案要放行。

        少了這條,「讀不動一律當違規」的實作也會讓上面那條正控過 ——
        正控單獨看分不出「抓到了」與「全部都擋」。
        """
        raw = u"# 註解:這裡沒有秘密\nvalue = 1\n".encode("cp950")
        hits = sc.scan_paths([_w(tmp_path, "clean.ps1", raw, mode="wb")],
                             _groups(), root=str(tmp_path))
        assert hits == [], hits

    def test_a_file_whose_bytes_cannot_be_read_is_a_violation(self, tmp_path):
        """連位元組都拿不到 -> 計為違規,不是跳過。

        已知的二進位副檔名在 skip 就濾掉了;走到這裡還讀不動的是意料外的東西,
        而意料外的東西在掃描器裡一律擋。
        """
        hits = sc.scan_paths([str(tmp_path / "does_not_exist.py")],
                             _groups(), root=str(tmp_path))
        assert len(hits) == 1 and hits[0].group == "<讀不到內容>", hits

    def test_the_reason_is_carried_not_swallowed(self, tmp_path):
        hits = sc.scan_paths([str(tmp_path / "nope.py")], _groups(),
                             root=str(tmp_path))
        assert hits[0].context, "讀不到的理由沒有被帶出來,只留下一個空的違規"


# ─────────────────────────────────────────────────────────────────────────────
# 三、self-skip 綁 repo 相對路徑,不綁檔名
# ─────────────────────────────────────────────────────────────────────────────

class TestSelfSkipIsPathBound:

    def test_the_declared_self_path_is_skipped(self, tmp_path):
        p = _w(tmp_path, "tools/scan.py", "token=" + SECRET)
        hits = sc.scan_paths([p], _groups(), root=str(tmp_path),
                             self_paths=("tools/scan.py",))
        assert hits == []

    def test_the_same_basename_elsewhere_is_not_skipped(self, tmp_path):
        """**綁檔名的話,豁免的鑰匙就握在要規避的人手上** ——
        任何目錄放一個同名檔就免掃,而那個檔名誰都造得出來。"""
        p = _w(tmp_path, "anywhere/scan.py", "token=" + SECRET)
        hits = sc.scan_paths([p], _groups(), root=str(tmp_path),
                             self_paths=("tools/scan.py",))
        assert [h.group for h in hits] == ["leak"], \
            "同名檔在別的目錄也被當成掃描器自己(檔名式豁免):%r" % hits


# ─────────────────────────────────────────────────────────────────────────────
# 四、staged 清單取不到 -> 機制錯誤,不是「沒有檔案要掃」
# ─────────────────────────────────────────────────────────────────────────────

class TestStagedListingFailureIsNotAnEmptyList:

    def test_a_failed_git_call_raises(self, monkeypatch):
        """git 因任何理由失敗 -> stdout 空 -> 清單空 -> 掃描器回 0 -> 放行。
        權威層沒有 fail-open 的餘地,所以退出碼要看。"""
        class _R:
            returncode = 128
            stdout = b""
            stderr = b"fatal: not a git repository"
        monkeypatch.setattr(sc.subprocess, "run", lambda *a, **k: _R())
        with pytest.raises(sc.StagedListingFailed):
            sc.staged_paths()

    def test_a_successful_call_splits_on_nul(self, monkeypatch):
        """非 ASCII 檔名要走 -z:C-quoted 路徑開不了檔 -> 被當成讀不動 -> 靜默不掃。"""
        class _R:
            returncode = 0
            stdout = u"docs/台股.md\0pkg/a.py\0".encode("utf-8")
            stderr = b""
        monkeypatch.setattr(sc.subprocess, "run", lambda *a, **k: _R())
        assert sc.staged_paths() == [u"docs/台股.md", "pkg/a.py"]


# ─────────────────────────────────────────────────────────────────────────────
# 票 42(a) —— staged 清單裡的 gitlink 不是檔案
#
# `git diff --cached --name-only` 對 submodule 條目回傳**目錄路徑**,而 index 裡
# 它的 mode 是 160000(gitlink),值是一個 commit sha:**沒有 blob 內容可掃**。
# 掃描器拿它去 open() → Windows 得 PermissionError(POSIX 是 IsADirectoryError)
# → 落進「讀不到內容」的 fail-closed 分支 → 擋下 commit。
#
# 「讀不到不等於乾淨」對**應該是檔案**的東西成立。gitlink 不是讀不到,是
# **根本沒有內容這回事** —— 把「沒有內容」判成「內容讀不到」,產生一個
# **永遠無法滿足的條件**:使用者沒有任何合法動作能讓它變乾淨,因為沒有東西可以洗。
#
# 判定依據是 **index 的 mode**,不是檔案系統。用 `os.path.isdir()` 的話,
# 判定會跑到磁碟上去問一個 git 才有權威回答的問題(見下方那條負控)。
# ─────────────────────────────────────────────────────────────────────────────

def _repo_with_staged_gitlink(tmp_path):
    """外層 repo:staged 一個一般檔 + 一格 gitlink。回傳外層根目錄。

    不用 `git submodule add`(git 2.38+ 預設擋 file:// submodule,
    那條限制與本票無關卻會讓 fixture 因為別的理由壞掉);
    改用 `update-index --cacheinfo` 直接種一格,產出的 mode 相同。
    """
    import subprocess

    def git(*a, **kw):
        return subprocess.run(["git"] + list(a),
                              cwd=kw.get("cwd", str(tmp_path)),
                              capture_output=True)

    inner = tmp_path / "sub"
    inner.mkdir()
    io.open(inner / "collect.py", "w", encoding="utf-8", newline="\n").write("x = 1\n")
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
    git("update-index", "--add", "--cacheinfo", "160000,%s,sub" % sha)

    mode = git("ls-files", "-s", "sub").stdout.decode().split(" ")[0]
    assert mode == "160000", "fixture 沒種出 gitlink(mode=%r)" % mode
    return tmp_path


class TestAStagedGitlinkIsNotAFile:

    def test_the_gitlink_is_not_in_the_listing(self, tmp_path):
        """**本組的主張**:那一格不進 staged 清單,所以沒有東西會去 open() 它。"""
        root = _repo_with_staged_gitlink(tmp_path)
        got = sc.staged_paths(cwd=str(root))
        assert "sub" not in got, "gitlink 仍被當成檔案列進 staged 清單:%r" % got

    def test_ordinary_files_are_still_listed(self, tmp_path):
        """**負控**:掃描面不得被這次過濾弄小。

        少了它,「staged_paths 一律回空」也會讓上面那條過 ——
        而那是把偵測整條關掉,測試看起來還是綠的。
        """
        root = _repo_with_staged_gitlink(tmp_path)
        assert sc.staged_paths(cwd=str(root)) == ["pkg/a.py"]

    def test_the_skip_is_visible_to_the_caller(self, tmp_path):
        """跳過要**看得見**:呼叫端拿得到被跳過的那幾格,才印得出報告。

        靜默跳過與修好之間差的就是這個 —— 票 39 的
        「未內容掃描清單一律進報告」是同一條規矩。
        """
        root = _repo_with_staged_gitlink(tmp_path)
        skipped = []
        sc.staged_paths(cwd=str(root), gitlinks=skipped)
        assert skipped == ["sub"], "被跳過的 gitlink 沒有交給呼叫端:%r" % skipped

    def test_the_return_type_is_still_a_flat_list(self, tmp_path):
        """**簽名不變**:回傳仍是路徑串列,不是 (paths, skipped) 這種 tuple。

        票 13 C 的教訓:`upstream_backed` 改成回 `(bool, reason)` 時,
        忘了解包的呼叫端**每一個都拿到豁免** —— `(False, "…")` 在 `if` 裡是真的,
        fail-closed 整條翻成 fail-open,而測試全綠、訊息什麼都不說。
        簽名不變就沒有那個失敗模式,所以「跳過清單」走**呼叫端傳入的收集串列**。
        """
        root = _repo_with_staged_gitlink(tmp_path)
        got = sc.staged_paths(cwd=str(root))
        assert isinstance(got, list) and all(isinstance(p, str) for p in got), got

    def test_the_verdict_comes_from_the_index_not_the_filesystem(self, tmp_path):
        """**負控:判定依據不得跑到檔案系統去。**

        把工作樹裡的那個目錄搬走 —— `os.path.isdir()` 從此回 False,
        而 index 裡那一格**還是 160000**。用檔案系統判的實作會在這裡
        把 gitlink 重新當成檔案(而且是一個不存在的檔案)。

        index 的 mode 才是權威:它是 git 對「這一格是什麼」的答案,
        而磁碟上的樣子隨時可以被別的東西改動。
        """
        root = _repo_with_staged_gitlink(tmp_path)
        os.rename(str(root / "sub"), str(root / "sub-moved-away"))
        got = sc.staged_paths(cwd=str(root))
        assert "sub" not in got, \
            "工作樹目錄一搬走,gitlink 就被當成檔案了 —— 判定掛在檔案系統上:%r" % got

    def test_an_unreadable_index_is_a_mechanism_error(self, tmp_path, monkeypatch):
        """**fail-closed**:問不到 index 的 mode = 這個問題沒有答案,不是「都不是 gitlink」。

        往「不知道」倒成「一律當檔案」的話,gitlink 又回到 open() 那條路;
        倒成「一律跳過」更糟 —— 那會把整份 staged 清單靜默清空。
        兩種都不對,所以這裡丟例外,由呼叫端變成機制錯誤(退出碼 2)。
        """
        root = _repo_with_staged_gitlink(tmp_path)
        real = sc.subprocess.run

        def fake(cmd, *a, **k):
            if "ls-files" in cmd:
                class _R:
                    returncode = 128
                    stdout = b""
                    stderr = b"fatal: boom"
                return _R()
            return real(cmd, *a, **k)

        monkeypatch.setattr(sc.subprocess, "run", fake)
        with pytest.raises(sc.StagedListingFailed):
            sc.staged_paths(cwd=str(root))


# ─────────────────────────────────────────────────────────────────────────────
# 五、命中內容遮罩(兩邊都已有,合一不得掉)
# ─────────────────────────────────────────────────────────────────────────────

class TestHitsAreRedacted:

    def test_the_matched_value_is_not_in_the_context(self, tmp_path):
        """**掃描器的輸出本身是外流面**:擋下的那一刻,秘密會被印進終端機、
        CI log、agent 對話紀錄 —— 剛好是最多眼睛在看的時候(F-067)。"""
        hits = sc.scan_paths([_w(tmp_path, "a.py", "token=" + SECRET)],
                             _groups(), root=str(tmp_path))
        assert SECRET not in hits[0].context, hits[0].context
        assert "遮罩" in hits[0].context


class TestThisFileIsInertUnderDownstreamGuards:
    """**本檔自己必須惰性。**

    這條不是重複上面的註解,它是那條紀律的機器保證:下一個人把樣本字串
    inline 回去時要有東西變紅。註解只會被讀一次,測試每次都跑。

    斷言的是「檔案裡不含拼好的字串」—— 用**執行期組出來的值**去比對靜置原始碼,
    所以它不需要知道下游有哪些 pattern,只需要知道「凡是我拿來當樣本的東西,
    都不該以字面形式留在檔案裡」。這比列舉下游 pattern 更強,也不會過時。
    """

    def _source(self):
        return io.open(__file__, encoding="utf-8").read()

    @pytest.mark.parametrize("name", ["SECRET", "COOKIE_OPT", "COOKIE_RE"])
    def test_no_sample_string_appears_literally(self, name):
        src = self._source()
        value = globals()[name]
        assert value not in src, (
            "%s 的值以字面形式出現在本檔裡 —— 下游守衛會比中它,"
            "而框架的出貨檔案在下游是被掃描的資料。請改成執行時拼裝。" % name)

    def _shipping_set(self):
        """**出貨集合 = manifest 的 copy 桶**,不是 `git ls-files` 的全部。

        判定的對象是「會被搬到下游的檔案」。用 ls-files 等於問
        「這個 repo 裡有什麼」—— 那是另一個問題,而且答案包含
        **本 repo 自己的東西**(票、專案測試、將來還有守衛的 pattern 定義檔)。
        下游守衛的 pattern 檔本來就寫著要偵測的字樣;把它算進出貨集合,
        規則會要求一個**永遠不可能滿足**的條件,而那種規則最後會被整條關掉。

        這是「規則判錯對象」的第四例(F-046 R8 判片段、
        ADR F-0013 R3 判檔案存在、F-074 R3 在下游要上游的證據,以及這裡)。
        """
        import subprocess
        spec = importlib.util.spec_from_file_location(
            "manifest_for_inert_test", ROOT / ".claude" / "portable" / "manifest.py")
        mf = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mf)
        table = mf.load_table(str(ROOT / ".agents" / "portable-manifest.txt"))
        out = subprocess.run(["git", "ls-files", "-z"], cwd=str(ROOT),
                             capture_output=True)
        rels = [p for p in out.stdout.decode("utf-8", "replace").split("\0")
                if p.strip()]
        return [p for p in rels if mf.mark_in(p, table) == "copy"]

    def test_the_shipping_set_is_inert(self):
        """**出貨集合**(非散文)對已知下游守衛的 pattern 零命中。

        上面那條自我檢查是通則(不知道下游有什麼,只知道自己的樣本不該靜置);
        這一條是對一個**已知**守衛的具體保證 —— 影音 repo 的 D21。
        兩者都要:通則抓得到新樣本被 inline,具體這條抓得到「某個出貨檔案
        剛好寫了那串字」,而那不一定是樣本。

        pattern 也拼裝,否則本檔會被自己這條測試比中。

        **散文排除在外,那是決定不是疏漏**:改寫散文以規避字面,正是下游
        `DOC_SUFFIX` 豁免存在要避免的稅(規則的說明本身必須寫得出來)。
        代價寫在 F-073:框架散文的惰性依賴下游豁免散文這個決定。
        """
        pats = [r"--cook" + r"ies\b",
                r"--cook" + r"ies-from-browser\b",
                r"\bcook" + r"ies-from-browser\b"]
        rels = [p for p in self._shipping_set()
                if not p.lower().endswith((".md", ".rst", ".adoc"))]
        assert rels, "出貨集合是空的 —— 掃不到東西的綠燈不算綠燈"
        bad = []
        for rel in rels:
            try:
                text = io.open(ROOT / rel, encoding="utf-8").read()
            except Exception:
                continue
            for p in pats:
                for m in re.finditer(p, text):
                    bad.append("%s:%d" % (rel, text[:m.start()].count("\n") + 1))
        assert not bad, "出貨檔案含下游守衛會擋的字面:%s" % bad

    def test_the_shipping_set_excludes_this_repos_own_files(self):
        """判對象要驗得出來:本 repo 自己的東西不得落進出貨集合。

        沒有這條的話,`_shipping_set()` 退化成「全部」也一樣綠 ——
        而那正是這次要修的判錯對象。
        """
        ship = set(self._shipping_set())
        assert not [p for p in ship if p.startswith("docs/tickets/")], \
            "本 repo 的工作票被算進出貨集合"
        assert ".claude/hooks/gate.py" in ship, "出貨集合連框架自己都沒涵蓋"

    def test_the_assembled_value_is_still_the_real_thing(self):
        """**效力不得下降**:拼裝只改字面配置,不改掃描器收到的東西。

        少了這條,把樣本改成一個不會命中的無害字串也能讓上面那條過 ——
        那是用「測試不再測到東西」換「檔案惰性」。
        """
        assert COOKIE_OPT.startswith("--") and COOKIE_OPT.endswith("browser")
        # 長度也不能寫成 len("完整字串") —— 那又是一次靜置。本輪已經在註解、
        # pattern 清單、長度斷言三個地方各種回去一次,所以這件事靠的是上面
        # 那條機器檢查,不是「記得不要寫」。
        assert len(COOKIE_OPT) == len("--cook") + len("ies-from-browser")
        assert COOKIE_RE == COOKIE_OPT
        assert SECRET.startswith("ghp") and len(SECRET) == 28


class TestMultiHitLinesCannotBeReassembled:
    """票 32 —— 一行命中多條 pattern 時,**分段遮罩可以拼回完整祕密**。

    ## 共同形狀:**防護的單位小於攻擊者能取得的單位**

    F-067 立的規矩是「掃描器的輸出本身是外流面」,而它解的是**一次命中**。
    現行的遮罩是**逐命中**做的:`scan_paths` 對每個 (行, 規則組, pattern)
    各產生一個 `Hit`,每個 `Hit` 的 `context` 只遮**自己那一段**。

    於是同一行的兩份報告,**各自洩漏對方遮掉的那一半**:

        行 N  pattern A   ***已遮罩***  yyyy
        行 N  pattern B   aaaa  ***已遮罩***

    **每一行單獨看都合格。** 而讀報告的人拿到的是全部。

    與票 21 是結構上的親戚:那邊是逐 token 抽取對上整段語意,
    這邊是逐命中遮罩對上整行洩漏 —— **單位對不上**。

    同族:分頁 API 每頁各自過濾敏感欄位而併頁可還原;
    日誌逐條脫敏而多條的交集反推出身分。
    """

    def _group(self, patterns):
        return sc.RuleGroup("測試", patterns)

    def test_two_patterns_on_one_line_cannot_be_reassembled(self, tmp_path):
        """**核心紅燈。** 兩份報告行**併讀**不得還原原始行。

        斷言必須跨行做 —— 單行斷言會給假綠,而假綠正是本票要修的東西。
        """
        left, right = "AAAA" + "1111", "BBBB" + "2222"
        line = "k = %s and %s" % (left, right)
        p = tmp_path / "sample.txt"
        io.open(p, "w", encoding="utf-8", newline="\n").write(line + "\n")

        hits = sc.scan_paths([str(p)], [self._group([left, right])],
                             root=str(tmp_path))
        assert len(hits) >= 1, "沒有命中,測試前提不成立"
        joined = " ".join(h.context for h in hits)
        for secret in (left, right):
            assert secret not in joined, (
                "併讀兩份報告還原出了 %s —— 遮罩的單位小於洩漏的單位" % secret)

    def test_three_patterns_on_one_line_are_also_safe(self, tmp_path):
        """兩條特例不算解決 —— 三條以上同樣不得拼回。"""
        parts = ["AAAA" + "1111", "BBBB" + "2222", "CCCC" + "3333"]
        line = "a=%s b=%s c=%s" % tuple(parts)
        p = tmp_path / "s3.txt"
        io.open(p, "w", encoding="utf-8", newline="\n").write(line + "\n")

        hits = sc.scan_paths([str(p)], [self._group(parts)], root=str(tmp_path))
        joined = " ".join(h.context for h in hits)
        for secret in parts:
            assert secret not in joined, "三條命中仍可拼回 %s" % secret

    def test_a_single_hit_keeps_f067_behaviour(self, tmp_path):
        """**反控 —— F-067 不得被推翻。**

        單一命中的遮罩行為與訊息品質**不變**:遮掉命中那一段、
        **前後文要留得住**(F-067 的原話:「遮罩過頭 —— 前後文要留得住,
        否則定位不了」)。

        少了這條,「一律整行遮」也會讓上面兩條全綠,而那等於把 F-067 拆掉。
        """
        secret = "AAAA" + "1111"
        line = "token = %s  # 註解" % secret
        p = tmp_path / "one.txt"
        io.open(p, "w", encoding="utf-8", newline="\n").write(line + "\n")

        hits = sc.scan_paths([str(p)], [self._group([secret])], root=str(tmp_path))
        assert len(hits) == 1, hits
        ctx = hits[0].context
        assert secret not in ctx, "單一命中沒遮到"
        assert "已遮罩" in ctx, "遮罩標記不見了"
        assert "token" in ctx, "前後文被遮掉了 —— F-067 說定位得留得住"

    def test_the_line_number_still_locates_the_hit(self, tmp_path):
        """整行遮蔽之後,**行號仍然是定位手段** —— 那是最後一道可讀性。"""
        parts = ["AAAA" + "1111", "BBBB" + "2222"]
        p = tmp_path / "loc.txt"
        io.open(p, "w", encoding="utf-8", newline="\n").write(
            "first\n" + "x=%s y=%s\n" % tuple(parts))
        hits = sc.scan_paths([str(p)], [self._group(parts)], root=str(tmp_path))
        assert hits and all(h.line == 2 for h in hits), [h.line for h in hits]


# ─────────────────────────────────────────────────────────────────────────────
# 七、比對軸:同一個秘密換一種**寫法**就穿過去(票 39 / P2)
#
# 來源是委託書「軸二」指定的編碼與轉換分類表,不是憑印象列的。
# 本輪只收三種 —— 裁決 3 指定的 NFKC、零寬字元、大小寫。
# **其餘(Base64 / URL 編碼 / 跳脫 / 字串分段)歸妥協聲明,不在這裡假裝有守。**
#
# 方向是 fail-closed 的加法:正規化後的比對是**額外**一輪,
# 不取代原本那輪。原因見 test_normalisation_never_removes_an_existing_hit ——
# 正規化會折掉大小寫與相容字,而**折掉的東西有可能正是某條 pattern 要的**。
# ─────────────────────────────────────────────────────────────────────────────

class TestObfuscationByFormIsNormalisedBeforeMatching:

    # 樣本一律執行時拼裝(同本檔開頭那段的理由)
    TOKEN = "ghp" + "_" + ("A" * 24)
    RULE = r"\bghp_[A-Za-z0-9]{20,}"
    ZWSP = "​"

    def _group(self):
        return [sc.RuleGroup("leak", [self.RULE])]

    def _scan(self, tmp_path, line, name="s.txt"):
        p = tmp_path / name
        io.open(p, "w", encoding="utf-8", newline="\n").write(line + "\n")
        return sc.scan_paths([str(p)], self._group(), root=str(tmp_path))

    def test_a_fullwidth_form_is_caught(self, tmp_path):
        """全形拉丁字母 —— NFKC 折得動的那一類。"""
        wide = "".join(chr(ord(c) + 0xFEE0) if "!" <= c <= "~" else c
                       for c in self.TOKEN)
        assert wide != self.TOKEN
        assert self._scan(tmp_path, "token = " + wide), "全形形式沒被抓到"

    def test_a_zero_width_char_inside_the_secret_is_caught(self, tmp_path):
        """零寬字元插在秘密中間 —— **肉眼完全看不出來**,而比對整條失效。

        這一種最惡劣的地方不是它難擋,是**貼上去的人自己也看不見** ——
        從剪貼簿帶進來的零寬字元不需要任何惡意就能讓一條規則消失。
        """
        broken = self.TOKEN[:6] + self.ZWSP + self.TOKEN[6:]
        assert self._scan(tmp_path, "token = " + broken), "零寬形式沒被抓到"

    def test_an_upper_case_form_is_caught(self, tmp_path):
        """大小寫 —— 委託書列了、回件漏答,自行補上的那一件。"""
        assert self._scan(tmp_path, "token = " + self.TOKEN.upper()), \
            "大寫形式沒被抓到"

    def test_normalisation_never_removes_an_existing_hit(self, tmp_path):
        """**反控:加了正規化之後,原本抓得到的仍然要抓得到。**

        這條防的是把新一輪比對寫成「取代」而不是「加上」——
        正規化會折掉大小寫與相容字,而折掉的東西有可能正是某條 pattern
        要的(例:只認大寫的 token 格式)。取代的話涵蓋會**變小**,
        而變小的方向沒有任何測試會抱怨。
        """
        upper_only = sc.RuleGroup("upper", [r"\bAKIA[A-Z0-9]{16}\b"])
        secret = "AKIA" + ("Z" * 16)
        p = tmp_path / "u.txt"
        io.open(p, "w", encoding="utf-8", newline="\n").write("k=" + secret + "\n")
        assert sc.scan_paths([str(p)], [upper_only], root=str(tmp_path)), \
            "原本抓得到的樣本在加了正規化之後漏掉了"

    def test_a_hit_only_visible_after_normalisation_masks_the_whole_line(
            self, tmp_path):
        """**遮罩安全性**:命中對不回原文時,一律整行遮。

        正規化後比對到的那一段,在**原文裡不存在**(中間夾著零寬字元)。
        照舊路徑走的話 `text.replace(matched, ...)` 會**什麼都換不到**,
        於是原始那一行**原樣印出來** —— 擋下的那一刻把秘密印進終端機。

        這與票 32 是同一個判準:**對不回去就不要猜,整行遮。**
        """
        broken = self.TOKEN[:6] + self.ZWSP + self.TOKEN[6:]
        hits = self._scan(tmp_path, "token = " + broken)
        assert hits, "前提就沒成立:零寬形式要先抓得到"
        ctx = hits[0].context
        assert self.TOKEN[:6] not in ctx and self.TOKEN[6:] not in ctx, \
            "原文片段漏出來了:%r" % ctx
        assert "遮罩" in ctx, "沒有遮罩標記:%r" % ctx

    def test_a_plain_hit_still_keeps_its_context(self, tmp_path):
        """**反控:一般命中不得被整行遮蓋掉。**

        少了這條,「一律整行遮」會讓上面那條全綠,而 F-067 的
        「前後文要留得住」就被悄悄拆掉了。
        """
        hits = self._scan(tmp_path, "token = " + self.TOKEN + "  # note")
        assert len(hits) == 1, hits
        assert "token" in hits[0].context, "前後文被遮掉了"

    def test_homoglyphs_are_explicitly_out_of_scope(self, tmp_path):
        """**同形字不在本輪範圍** —— 這條釘住的是妥協聲明,不是功能。

        回件第 3 節把「同形字 / 零寬」列在同一列、處置寫「NFKC + 濾 ZWJ」。
        **NFKC 折的是相容性差異(全形、連字),不是視覺相似。**
        西里爾 `С`(U+0421)在 NFKC / 濾零寬 / casefold 之後都還原不成拉丁 `C`。

        所以本條**斷言它抓不到** —— 把它放進「已修好」那一格就是製造一格
        假涵蓋,而假涵蓋正是整份 ADR F-0015 在打的東西。

        將來若引入 TR39 confusables 表,這條會紅 —— **那時是刻意改它**,
        不是它壞了。
        """
        cyrillic_a = "А"          # 西里爾大寫 А,視覺同拉丁 A
        spoofed = "ghp" + "_" + cyrillic_a + ("A" * 23)
        assert spoofed != self.TOKEN
        assert not self._scan(tmp_path, "token = " + spoofed), \
            "同形字被抓到了 —— 若是刻意引入 confusables 表,請一併更新妥協聲明"


# ─────────────────────────────────────────────────────────────────────────────
# 八、跳過清單的比對必須帶邊界(票 39 / P2 第五件)
#
# 現象:`SKIP_PARTS` 有一條裸的 `skills/`,為了跳過**鏡像**
# (`.claude/skills/`、`skills/`,兩者都 gitignore)而放;
# 但比對是**子字串**,而正典 `.agents/skills/` 的路徑裡剛好含有 `skills/`
# —— 於是 39 個進版控的正典檔**在兩種模式下都從來沒有被內容掃描過**。
#
# **正典被當成鏡像跳過了**,而它是會跟著公開走的那一份。
#
# 這一族在本 repo 已經被命名過:`g1_guard.py` 的 docstring 寫著
# 「前綴要帶邊界…… 與 `.gitignore` 的 `skills/` 缺前導斜線同一族」——
# **教訓學在一個地方,而隔壁的資料從來沒有回頭重掃**(F-082 的形狀)。
#
# 正確形狀 repo 裡也已經有了:`gate.py:is_source_path` 用
# `r.split("/")[0]` 取頂層段,那是**根錨定 + 分段**,不是子字串。
# ─────────────────────────────────────────────────────────────────────────────

class TestSkipListMatchingIsBounded:

    def _skipped(self, rel):
        return sc._globally_skipped(rel, (), sc.SKIP_SUFFIX, sc.SKIP_PARTS)

    # ── 反控:鏡像仍然要被跳過 ──────────────────────────────────
    def test_the_mirrors_are_still_skipped(self):
        """**先守住原本對的那一半。**

        少了這條,「把 skills/ 整條拿掉」也會讓下面那條全綠 ——
        而那是把鏡像放進掃描,每次都會撈到一堆與正典重複的命中。
        """
        for rel in ("skills/tdd/SKILL.md", ".claude/skills/tdd/SKILL.md"):
            assert self._skipped(rel), "鏡像沒有被跳過:%s" % rel

    # ── 正控:正典要進掃描 ──────────────────────────────────────
    def test_the_canonical_skills_tree_is_scanned(self):
        """`.agents/skills/` 是**正典**、進版控、會跟著公開走。"""
        assert not self._skipped(".agents/skills/tdd/SKILL.md"), \
            "正典被當成鏡像跳過了"

    # ── 同族:子字串比對會誤吞的其他形狀 ────────────────────────
    def test_a_directory_merely_ending_in_the_marker_is_not_skipped(self):
        """`myskills/` 含有 `skills/` 這個子字串 —— 但它不是鏡像。

        這一條與上面那條是**同一個 bug 的不同受害者**:
        修好正典卻沒問「還有誰會被誤吞」,就只修了自己看得見的那一個。
        """
        assert not self._skipped("src/myskills/thing.py")
        assert not self._skipped("docs/skills-guide.md")

    def test_a_directory_merely_ending_in_dot_git_is_not_skipped(self):
        """`foo.git/` 含有 `.git` —— 但 `.git/` 要的是那個**目錄段**。"""
        assert not self._skipped("vendor/foo.git/README.md")

    def test_a_real_nested_git_dir_is_still_skipped(self):
        """反控:真的 `.git/` 段,**在任何深度**都要跳過。"""
        assert self._skipped("vendor/thing/.git/config")

    def test_cache_markers_still_match_at_any_depth(self):
        """反控:快取類的標記本來就該在任何深度命中,不得被根錨定綁住。"""
        for rel in ("a/b/__pycache__/x.pyc", "a/.pytest_cache/x",
                    "deep/nest/.cache/x"):
            assert self._skipped(rel), rel

    def test_a_name_merely_ending_in_cache_is_not_skipped(self):
        """`my.cache/` 不是 `.cache/`。"""
        assert not self._skipped("a/my.cache/x.txt")


# ─────────────────────────────────────────────────────────────────────────────
# 票 109:`read_text` 的解碼階梯 —— UTF-16 與可讀性
#
# 這一組測的是**骨架自己**(`scanner.read_text`),不是某一支掃描器的組態。
# `tests/test_leak_scan.py` 那一組測的是**同一件事的對外行為**(scan 的退出碼);
# 兩邊都要,因為它們證的是不同的命題:這裡證「解碼決策對不對」,
# 那裡證「決策接到偵測上之後,金鑰真的被擋下」。
#
# 失效方向照本檔檔頭:**靜默放行**。所以每一條都往「不可讀 -> 計為違規」倒,
# 而且配反控 —— 少了反控,「全部當成違規」也會讓正控過。
# ─────────────────────────────────────────────────────────────────────────────

_AWS = "AKIA" + ("Z" * 16)                  # 組裝:本檔自己也被掃
_ASCII_LINE = u"aws_access_key_id = " + _AWS + u"\n"
_CJK_LINE = u"# 票 109 探針 —— 尾巴全是 Z。\n金鑰 = " + _AWS + u"\n"


def _wb(tmp_path, name, data):
    p = tmp_path / name
    io.open(str(p), "wb").write(data)
    return str(p)


class TestReadTextUnderstandsUtf16:
    """**六格 = 三態 × 兩種內容。**

    三態:LE+BOM / BE+BOM / 無 BOM。兩種內容:純 ASCII 與含 CJK。
    **兩種內容不是湊數** —— 它們在舊碼裡走的是**不同的解碼分支**
    (純 ASCII 在 `utf-8-sig` 第一格就「成功」,含 CJK 掉到 `latin-1`),
    只測一種等於只驗一條路,而修法很容易只接住其中一條。
    """

    @pytest.mark.parametrize("content", [_ASCII_LINE, _CJK_LINE],
                             ids=["ascii", "cjk"])
    @pytest.mark.parametrize("bom,endian", [
        (b"\xff\xfe", "le"), (b"\xfe\xff", "be"), (b"", "le"),
    ], ids=["le-bom", "be-bom", "no-bom"])
    def test_the_secret_survives_decoding(self, tmp_path, content, bom, endian):
        raw = bom + content.encode("utf-16-" + endian)
        text, why = sc.read_text(_wb(tmp_path, "probe.env", raw))
        assert why is None, u"解不開:%s" % why
        assert _AWS in text, (
            u"解出來的文字裡找不到樣本 —— 這個檔不是「掃過乾淨」,"
            u"是「解成亂碼之後沒命中」。解出來的前 40 字:%r" % text[:40])


class TestLatin1IsNoLongerAGuaranteedPass:
    """**`latin-1` 對全部 256 個位元組值都成功**,所以舊版的 fail-closed 出口
    是死碼。這一組把它叫醒。"""

    def test_latin1_still_decodes_every_byte_value(self):
        """先釘住前提本身 —— 這是上面那句話的來源,不是我推的。"""
        assert bytes(bytearray(range(256))).decode("latin-1")

    def test_random_bytes_are_reported_not_decoded_into_noise(self, tmp_path):
        raw = bytes(bytearray((i * 7 + 3) % 256 for i in range(512)))
        text, why = sc.read_text(_wb(tmp_path, "noise.bin", raw))
        assert text is None and why, (
            u"解不出可讀文字的位元組流被當成文字回傳了 —— "
            u"fail-closed 出口仍是死碼。解出來的前 40 字:%r"
            % (text[:40] if text else None))


class TestDecodingDoesNotOverreach:
    """**反控:涵蓋不得變小。** 往「更會判成 UTF-16」走一步的代價在這裡。"""

    def test_a_plain_utf8_file_is_unchanged(self, tmp_path):
        text, why = sc.read_text(_wb(tmp_path, "a.txt",
                                     _CJK_LINE.encode("utf-8")))
        assert why is None and _AWS in text

    def test_a_cp950_file_is_unchanged(self, tmp_path):
        text, why = sc.read_text(_wb(tmp_path, "b.txt",
                                     _CJK_LINE.encode("cp950")))
        assert why is None and _AWS in text

    def test_a_utf8_file_with_a_few_nuls_is_not_read_as_utf16(self, tmp_path):
        """NUL 是合法的 UTF-8 位元組,這種檔真的存在。

        誤判成 UTF-16 的話它會被解成亂碼,**裡面的金鑰就消失了** ——
        一個為了多抓而做的改動,反而讓這一類檔完全失去偵測。
        """
        content = (u"# note\x00\x00\n" + _ASCII_LINE
                   + u"padding padding padding padding padding\n" * 4)
        text, why = sc.read_text(_wb(tmp_path, "c.txt",
                                     content.encode("utf-8")))
        assert why is None, u"含少量 NUL 的 UTF-8 檔被判成不可讀:%s" % why
        assert _AWS in text, u"含少量 NUL 的 UTF-8 檔被誤判成 UTF-16,樣本消失"

    def test_an_empty_file_is_readable_not_broken(self, tmp_path):
        """空檔案是合法的文字檔,不是壞檔案 —— 可讀性檢查不得把它擋掉。"""
        text, why = sc.read_text(_wb(tmp_path, "empty.txt", b""))
        assert why is None and text == u""
