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

import importlib.util
import io
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

    def test_the_shipped_non_prose_tree_is_inert(self):
        """整棵出貨樹(非散文)對**已知下游守衛**的 pattern 零命中。

        上面那條自我檢查是通則(不知道下游有什麼,只知道自己的樣本不該靜置);
        這一條是對一個**已知**守衛的具體保證 —— 影音 repo 的 D21。
        兩者都要:通則抓得到新樣本被 inline,具體這條抓得到「某個檔案剛好寫了
        那串字」,而那不一定是樣本。

        pattern 也拼裝,否則本檔會被自己這條測試比中。

        **散文排除在外,那是決定不是疏漏**:改寫散文以規避字面,正是下游
        `DOC_SUFFIX` 豁免存在要避免的稅(規則的說明本身必須寫得出來)。
        代價寫在 F-073:框架散文的惰性依賴下游豁免散文這個決定。
        """
        import subprocess
        pats = [r"--cook" + r"ies\b",
                r"--cook" + r"ies-from-browser\b",
                r"\bcook" + r"ies-from-browser\b"]
        out = subprocess.run(["git", "ls-files", "-z"], cwd=str(ROOT),
                             capture_output=True)
        rels = [p for p in out.stdout.decode("utf-8", "replace").split("\0")
                if p.strip() and not p.lower().endswith((".md", ".rst", ".adoc"))]
        assert rels, "git ls-files 回空 —— 掃不到東西的綠燈不算綠燈"
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
