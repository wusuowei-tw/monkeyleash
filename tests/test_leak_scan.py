# -*- coding: utf-8 -*-
"""洩漏偵測規則自己的測試。

**規則要有機器驗證,不能只靠人工斷言。** template 含實際路徑那條紅線
(明文寫在指令裡、但沒有機器在流量路徑上驗它)就是這樣死的 —— 這裡不重演。

**這個測試檔自己也被 shipped-tree-is-clean 掃描**,所以它不含任何實際敏感字面:
所有偵測樣本都是組裝的,或用注入的 pattern。
"""

import importlib.util
import io
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "leak_scan", ROOT / ".claude" / "portable" / "leak_scan.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ls = _load()


def _write(tmp_path, text):
    p = tmp_path / "candidate.txt"
    io.open(p, "w", encoding="utf-8", newline="\n").write(text)
    return str(p)


def test_a_credential_shape_is_caught(tmp_path):
    # 組裝而不寫死:測試檔自己也被掃,寫死會擋住自己
    assert ls.scan([_write(tmp_path, "keyfile = client." + "pfx")]) == 1
    assert ls.scan([_write(tmp_path, "cert = server." + "pem")]) == 1


def test_a_private_key_header_is_caught(tmp_path):
    header = "-----BEGIN RSA " + "PRIVATE KEY-----"
    assert ls.scan([_write(tmp_path, header)]) == 1


def test_a_github_token_shape_is_caught(tmp_path):
    tok = "ghp" + "_" + ("A" * 24)
    assert ls.scan([_write(tmp_path, "token=" + tok)]) == 1


def test_personal_patterns_are_unioned_in(tmp_path, monkeypatch):
    """個人 token 走**注入的** local pattern 檔,不綁本機實際清單 ——
    測的是聯集機制,而不是「這台機器剛好有那份清單」。"""
    local = tmp_path / "local.txt"
    io.open(local, "w", encoding="utf-8", newline="\n").write("PROJECT_CODENAME_XYZ\n")
    monkeypatch.setattr(ls, "LOCAL_PATTERNS_FILE", str(local))
    assert ls.scan([_write(tmp_path, "cd PROJECT_CODENAME_XYZ")]) == 1


def test_a_missing_local_file_is_not_an_error(tmp_path, monkeypatch):
    """個人清單缺席不是錯(別台機器就沒有)—— 只用通用形狀,乾淨檔仍放行。"""
    monkeypatch.setattr(ls, "LOCAL_PATTERNS_FILE", str(tmp_path / "nope.local.txt"))
    assert ls.scan([_write(tmp_path, "# clean\nhello world")]) == 0


def test_a_missing_local_file_warns_visibly(tmp_path, monkeypatch, capsys):
    """缺個人清單不 fail-closed,但**不能無痕** —— 要有顯式警告到 stderr。

    無痕的話,某人 clone 後沒建個人清單,掃描靜默只剩通用形狀,
    他會以為個人 token 也在守,而其實沒有。"""
    monkeypatch.setattr(ls, "LOCAL_PATTERNS_FILE", str(tmp_path / "nope.local.txt"))
    ls.load_patterns()
    err = capsys.readouterr().err
    assert "找不到個人 pattern" in err and "警告" in err


def test_the_committed_pattern_file_has_no_personal_tokens():
    """**發布的 pattern 檔本身不得含個人 token。**

    這正是差點被推上去的洩漏:pattern 檔進版控,而它列的就是那些敏感字樣 ——
    掃描器跳過自己(SELF)所以抓不到,要一條明確的測試守。
    個人 token 屬於 ~/.claude/leak-patterns.local.txt(不進版控)。
    """
    text = io.open(ls.PATTERNS_FILE, encoding="utf-8").read()
    # token 全組裝 —— 這個測試檔自己也被掃,寫死個人字面會擋住自己
    personal = ["Sino" + "pac", "相" + "簿", "AI" + "工作台", "台股" + "交易",
                "local" + "_db", "Users" + chr(92) + "user", "Users/" + "user"]
    found = [t for t in personal if t in text]
    assert not found, "通用 pattern 檔含個人 token(該搬去 local):%s" % found


def test_a_clean_file_passes(tmp_path):
    clean = ("# 一般文件,含佔位符路徑\n"
             r"C:\Users\<你>\.claude\g1-protected.txt" + "\n"
             r"D:\<備份目錄>" + "\n"
             "/tmp/x  /home/someone/data\n")
    assert ls.scan([_write(tmp_path, clean)]) == 0


def test_missing_pattern_file_fails_closed(tmp_path, monkeypatch):
    """通用 pattern 讀不到 → 退出碼 2(機制錯誤),不是 0(放行)。

    讀不到就放行的話,刪掉 pattern 檔就等於關掉洩漏偵測。
    """
    monkeypatch.setattr(ls, "PATTERNS_FILE", str(tmp_path / "gone.txt"))
    monkeypatch.setattr(ls, "LOCAL_PATTERNS_FILE", str(tmp_path / "gone.local.txt"))
    assert ls.scan([_write(tmp_path, "anything")]) == 2


def test_the_scanner_skips_itself(tmp_path):
    """pattern 檔與 scanner 本身含要偵測的字樣,不能自己擋自己。"""
    assert ls.should_skip(".claude/portable/leak-patterns.txt")
    assert ls.should_skip(".claude/portable/leak_scan.py")


def _write_named(tmp_path, name, text, mode="w"):
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    if mode == "wb":
        io.open(p, "wb").write(text)
    else:
        io.open(p, "w", encoding="utf-8", newline="\n").write(text)
    return str(p)


_TOK = "ghp" + "_" + ("A" * 24)          # 組裝:本檔自己也被掃


class TestUnreadableIsNotAPass:
    """讀不動的檔案原本是 `except: continue` —— **靜默跳過**。

    下游的 cookie_ban 早就修成 fail-closed,上游沒修,於是同一件事兩個方向。
    合一時若以 leak_scan 為基準,會把這個洞一起合進去。
    """

    def test_a_cp950_file_with_a_secret_is_caught(self, tmp_path):
        """正控:cp950 的 .ps1 裡寫著金鑰要抓得到。

        zh-TW Windows 上 cp950 是預設編碼,這不是假想情況。
        """
        raw = (u"# 設定檔\ntoken=" + _TOK + u"\n").encode("cp950")
        assert ls.scan([_write_named(tmp_path, "conf.ps1", raw, "wb")]) == 1

    def test_a_clean_cp950_file_passes(self, tmp_path):
        """**反控**:cp950 的乾淨檔案要放行。

        少了這條,「讀不動一律當違規」的實作也會讓正控過 ——
        正控單獨看分不出「抓到了」與「全部都擋」。
        """
        raw = u"# 註解:這裡沒有秘密\nvalue = 1\n".encode("cp950")
        assert ls.scan([_write_named(tmp_path, "clean.ps1", raw, "wb")]) == 0

    def test_a_file_whose_bytes_cannot_be_read_is_a_violation(self, tmp_path):
        """連位元組都拿不到 -> 計為違規。已知的二進位在 SKIP_SUFFIX 就濾掉了,
        走到這裡還讀不動的是意料外的東西。"""
        assert ls.scan([str(tmp_path / "does_not_exist.py")]) == 1


class TestSelfSkipIsPathBoundNotNameBound:
    """**基本檔名版本的豁免鑰匙握在要規避的人手上。**"""

    def test_the_real_scanner_is_still_skipped(self, tmp_path):
        assert ls.scan([str(ROOT / ".claude" / "portable" / "leak_scan.py")]) == 0
        assert ls.scan([str(ROOT / ".claude" / "portable" / "leak-patterns.txt")]) == 0

    def test_a_same_named_file_elsewhere_is_scanned(self, tmp_path):
        """任何目錄放一個叫 leak_scan.py 的檔就免掃 —— 那個檔名誰都造得出來。"""
        p = _write_named(tmp_path, "elsewhere/leak_scan.py", "token=" + _TOK)
        assert ls.scan([p]) == 1, "同名檔在別的目錄被當成掃描器自己"


class TestProseIsNotExemptForSecrets:
    """**這條釘的是合一時不得引入的東西。**

    下游 cookie_ban 有 DOC_SUFFIX(.md/.rst/.adoc 不掃),理由是
    「規則的說明本身必須寫得出來」—— 那對**選項名**成立,對**金鑰**完全不成立:
    .md 裡的金鑰就是外洩的金鑰。合一若把散文豁免套到全部 pattern,
    就是把差異壓平,而壓平的方向是 fail-open。
    """

    def test_a_secret_in_markdown_is_caught(self, tmp_path):
        assert ls.scan([_write_named(tmp_path, "notes.md", "token=" + _TOK)]) == 1

    def test_a_secret_in_rst_is_caught(self, tmp_path):
        assert ls.scan([_write_named(tmp_path, "notes.rst", "token=" + _TOK)]) == 1


class TestStagedListingFailureIsNotAnEmptyList:

    def test_a_failed_git_call_returns_mechanism_error(self, monkeypatch):
        """git 壞掉 -> stdout 空 -> 清單空 -> main 回 0 -> pre-commit 放行。
        「沒有檔案要掃」與「問不到有哪些檔案」是兩件事。"""
        class _R:
            returncode = 128
            stdout = b""
            stderr = b"fatal: not a git repository"
        monkeypatch.setattr(ls.subprocess, "run", lambda *a, **k: _R())
        assert ls.main(["--staged"]) == 2


# ─────────────────────────────────────────────────────────────────────────────
# 票 42(a) —— staged 的 gitlink 沒有內容可掃,而「沒有內容」不是「讀不到內容」
#
# 下游(台股資訊收集)實測:bump 一格 gitlink 時 pre-commit 擋下,訊息是
# 「讀不到檔案:[Errno 13] Permission denied: '…/data_collector'」。
# 那一格是 mode 160000,值是一個 commit sha —— **沒有 blob 可掃**。
#
# 「讀不到不等於乾淨」這條規則的正當性,對**應該是檔案**的東西成立;
# 對 gitlink 它產生一個**永遠無法滿足的條件**:使用者沒有任何合法動作
# 能讓它變乾淨,因為沒有東西可以洗。而下游因此連框架都同步不了(票 42 (b))。
# ─────────────────────────────────────────────────────────────────────────────

class TestAStagedGitlinkDoesNotBlockTheCommit:

    def _repo(self, tmp_path, monkeypatch, dirty=False):
        import subprocess

        def git(*a, **kw):
            return subprocess.run(["git"] + list(a),
                                  cwd=kw.get("cwd", str(tmp_path)),
                                  capture_output=True)

        inner = tmp_path / "sub"
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

        io.open(tmp_path / "note.md", "w", encoding="utf-8", newline="\n").write(
            ("token=" + _TOK + "\n") if dirty else "沒有秘密\n")
        git("add", "note.md")
        git("update-index", "--add", "--cacheinfo", "160000,%s,sub" % sha)

        monkeypatch.setattr(ls, "ROOT", str(tmp_path))
        monkeypatch.setattr(ls, "LOCAL_PATTERNS_FILE", str(tmp_path / "none.local.txt"))
        return tmp_path

    def test_a_staged_gitlink_alone_passes(self, tmp_path, monkeypatch):
        """**本組的主張**:bump 一格 gitlink 過得了 pre-commit。"""
        self._repo(tmp_path, monkeypatch)
        assert ls.main(["--staged"]) == 0, \
            "gitlink 仍被當成讀不到內容的檔案而擋下 commit"

    def test_the_skipped_gitlink_is_in_the_report(self, tmp_path, monkeypatch, capsys):
        """跳過要**看得見**,而且要說出**由誰守**。

        外層對 gitlink 的正確語意是「這一格由內層 repo 自己守」
        (內層有自己的 pre-commit 跑 leak_scan)。靜默跳過的話,
        讀報告的人分不出「掃過沒事」與「根本沒掃」—— 票 39 的同一條規矩。
        """
        self._repo(tmp_path, monkeypatch)
        ls.main(["--staged"])
        err = capsys.readouterr().err
        assert "sub" in err, "被跳過的 gitlink 沒有進報告:%s" % err
        assert "gitlink" in err and "內層" in err, \
            "報告沒說出這一格由誰守:%s" % err

    def test_an_ordinary_staged_file_is_still_scanned(self, tmp_path, monkeypatch):
        """**負控**:掃描面不得被這次過濾弄小。

        少了它,「staged 一律回空」也會讓上面兩條過 ——
        而那是把 pre-commit 的偵測整條關掉,測試看起來還是綠的。
        """
        self._repo(tmp_path, monkeypatch, dirty=True)
        assert ls.main(["--staged"]) == 1, \
            "同一批 staged 裡的一般檔案沒有被掃到"


class TestPatternFileEncoding:

    def test_a_bom_does_not_corrupt_the_first_pattern(self, tmp_path, monkeypatch):
        """PowerShell 的 `Set-Content -Encoding utf8` 寫的是**帶 BOM** 的 UTF-8。

        用 `utf-8` 讀的話 BOM 會變成第一條 pattern 的一部分,那條 pattern
        從此永遠不命中 —— 少了一條規則,而且完全無聲。
        """
        pf = tmp_path / "pat.txt"
        io.open(pf, "wb").write(u"﻿\\bghp_[A-Za-z0-9]{20,}\n".encode("utf-8"))
        monkeypatch.setattr(ls, "PATTERNS_FILE", str(pf))
        monkeypatch.setattr(ls, "LOCAL_PATTERNS_FILE", str(tmp_path / "none.txt"))
        assert ls.scan([_write_named(tmp_path, "a.py", "token=" + _TOK)]) == 1


def test_the_shipped_tree_is_clean():
    """**發布來源自己必須乾淨** —— 持續的機器保證,不是一次性人工斷言。

    掃描用兩份 pattern 的聯集(含本機個人清單),所以它也會抓到
    「不小心把個人資料寫進版控檔」。

    **掃的是 git 認得的檔案,不是檔案系統走訪。** 這條原本用 os.walk,於是
    把 `.env` 也掃了進來 —— 而 `.env` 是**刻意**不進版控的,裡面本來就該有金鑰。
    諷刺的是這個坑是框架自己挖的:安裝器會把 `.env` 寫進目標 repo 的 .gitignore,
    所以每個裝了框架的專案遲早都會踩到這條紅測試,而且**它會把真金鑰印進測試輸出**
    (log、CI 畫面、對話紀錄都算外流面)。
    「發布來源乾淨」問的是**會被推出去的東西**乾不乾淨,那個集合的定義是 git 的,
    不是檔案系統的。用 ls-files 就同時解決假陽性與印金鑰兩件事。
    """
    import os
    import subprocess
    out = subprocess.run(["git", "ls-files", "-z"], cwd=str(ROOT), capture_output=True)
    rels = [p for p in out.stdout.decode("utf-8", "replace").split("\0") if p.strip()]
    files = [os.path.join(str(ROOT), p.replace("/", os.sep)) for p in rels]
    files = [f for f in files if os.path.isfile(f)]
    assert files, "git ls-files 回空 —— 掃不到東西的綠燈不算綠燈"
    assert ls.scan(files) == 0, "發布來源含洩漏 —— 見上方輸出"


def test_gitignore_content_is_not_scanned(tmp_path):
    """.gitignore 的工作是列出秘密檔形狀 —— 內容掃它必然假陽性(F-062 實測:
    安裝器產的秘密檔區塊被掃描器擋下)。與 pattern 檔跳過自己同一個理由。
    副檔名組裝而不寫死,同本檔其他測試。"""
    g = tmp_path / ".gitignore"
    g.write_text("*." + "pfx" + "\n*." + "pem" + "\n", encoding="utf-8")
    assert ls.scan([str(g)]) == 0


def test_a_binary_cert_is_caught_by_extension(tmp_path):
    """二進位憑證檔掃內容永遠漏(utf-8 解不開被跳過)——依副檔名擋。
    副檔名組裝而不寫死:本測試檔會被 shipped-tree 掃描(F-062)。"""
    import os
    for ext in ("pfx", "p12", "jks", "keystore"):
        f = tmp_path / ("cert." + ext)
        f.write_bytes(b"\x30\x82\x04\x00" + os.urandom(128))  # 二進位,非 utf-8
        assert ls.scan([str(f)]) == 1, "%s 副檔名沒被擋" % ext


def test_a_text_pem_key_is_caught_by_extension(tmp_path):
    """文字型憑證副檔名即使內容看似無害,副檔名本身就該擋(字面副檔名避寫,見上)。"""
    for ext in ("pem", "key"):
        f = tmp_path / ("server." + ext)
        f.write_text("not actually a key but named like one\n", encoding="utf-8")
        assert ls.scan([str(f)]) == 1, "%s 副檔名沒被擋" % ext


def test_a_non_cert_extension_still_passes(tmp_path):
    """正控:名字相近但非憑證副檔名的乾淨檔案照常放行。"""
    f = tmp_path / "notes.keys.md"  # 含 'key' 但副檔名是 .md
    f.write_text("my thoughts on keys\n", encoding="utf-8")
    assert ls.scan([str(f)]) == 0


_P8 = "p" + "8"          # PKCS#8 私鑰;副檔名組裝,同本檔其他測試
_P7B = "p" + "7b"        # PKCS#7 簽章包


class TestCertExtCoversPkcs8AndPkcs7:
    """票 23:`CERT_EXT` 漏掉 PKCS#8 與 PKCS#7 兩種副檔名。

    **每一條都斷言「命中理由是憑證副檔名」,不只斷言退出碼。**
    只看退出碼會綠得莫名其妙:這兩種副檔名不在 `SKIP_SUFFIX` 裡,
    所以二進位的那份會走到內容比對、解不開、被 `TestUnreadableIsNotAPass`
    那條規則計為違規 —— 退出碼 1,理由卻是「讀不到內容」。
    **擋對了但理由是別的**,而那個理由不穩:任何一次把這兩種副檔名加進
    `SKIP_SUFFIX` 的「整理」,都會讓它從擋變放行,且沒有訊號。
    """

    def test_an_ascii_decodable_pkcs8_is_caught_by_extension(self, tmp_path, capsys):
        """**核心紅燈。** 內容可解碼、不含任何秘密形狀 —— 內容比對必然放行。

        判定不能取決於「手上這份剛好是二進位」。同一種副檔名可以是 DER 也可以是
        PEM,也可以是被工具轉過一手的純文字;副檔名判定的價值就在於不必知道
        內容長什麼樣(F-062)。
        """
        f = tmp_path / ("client." + _P8)
        f.write_text("AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8=\n", encoding="utf-8")
        assert ls.scan([str(f)]) == 1, "可解碼的 PKCS#8 沒被擋 —— 這是 fail-open"
        assert "憑證副檔名" in capsys.readouterr().err

    def test_a_der_pkcs8_is_caught_as_a_cert_not_as_unreadable(self, tmp_path, capsys):
        """二進位那份今天也會回 1,但**理由是「讀不到內容」**。理由要對。"""
        import os
        f = tmp_path / ("client." + _P8)
        f.write_bytes(b"\x30\x82\x04\xbe\x02\x01\x00" + os.urandom(128))
        assert ls.scan([str(f)]) == 1
        assert "憑證副檔名" in capsys.readouterr().err

    def test_a_der_pkcs7_bundle_is_caught_as_a_cert(self, tmp_path, capsys):
        import os
        f = tmp_path / ("bundle." + _P7B)
        f.write_bytes(b"\x30\x82\x03\x0a\x06\x09" + os.urandom(128))
        assert ls.scan([str(f)]) == 1
        assert "憑證副檔名" in capsys.readouterr().err

    def test_a_pem_pkcs8_is_caught_by_extension_not_by_the_key_header(
            self, tmp_path, capsys):
        """PEM 形狀但**不含**私鑰標頭 —— 只有副檔名判定抓得到它。

        用 CERTIFICATE 標頭而不是 PRIVATE KEY:後者會命中通用內容 pattern,
        那樣測到的是內容比對,不是這次的修改。
        """
        f = tmp_path / ("client." + _P8)
        f.write_text("-----BEGIN CERTIFICATE-----\nQUJD\n-----END CERTIFICATE-----\n",
                     encoding="utf-8")
        assert ls.scan([str(f)]) == 1
        assert "憑證副檔名" in capsys.readouterr().err

    def test_an_uppercase_extension_is_caught(self, tmp_path, capsys):
        """現行用 `.lower()` 後 `endswith`,這條應該一開始就對 ——
        留著是為了守住往後別把 `lower()` 拿掉。"""
        f = tmp_path / ("client." + _P8.upper())
        f.write_text("harmless\n", encoding="utf-8")
        assert ls.scan([str(f)]) == 1
        assert "憑證副檔名" in capsys.readouterr().err

    def test_a_lookalike_extension_still_passes(self, tmp_path):
        """**誤擋的代價在這裡不是不方便,是這條規則會被關掉。**

        含但不以該副檔名結尾的,一律放行。
        """
        for name in ("x." + _P8 + "x", "notes-about-" + _P8 + ".md",
                     "bundle." + _P7B + ".md"):
            f = tmp_path / name
            f.write_text("just prose about key formats\n", encoding="utf-8")
            assert ls.scan([str(f)]) == 0, "%s 被誤擋" % name


def test_the_matched_secret_is_not_printed(tmp_path, capsys):
    """掃描器的輸出本身是外流面:擋下的那一刻,秘密會被印進終端機、CI log、
    對話紀錄 —— 剛好是最多眼睛在看的時候。命中的那一段必須遮掉(F-066)。"""
    secret = "AIza" + "Z" * 35
    f = _write(tmp_path, "k = " + secret)
    assert ls.scan([f]) == 1
    err = capsys.readouterr().err
    assert secret not in err, "命中的秘密被原樣印出來了"
    assert "已遮罩" in err
    assert "k = " in err, "遮罩過頭 —— 前後文要留得住,否則定位不了"


def test_personal_pattern_text_is_not_printed(tmp_path, capsys, monkeypatch):
    """個人 pattern 本身往往就是秘密(使用者名稱、往來對象、金鑰字面),
    印出 pattern 等於在報告裡再洩一次。"""
    personal = tmp_path / "local.txt"
    tok = "MySecret" + "Employer"
    personal.write_text(tok + "\n", encoding="utf-8")
    monkeypatch.setattr(ls, "LOCAL_PATTERNS_FILE", str(personal))
    f = _write(tmp_path, "company = " + tok)
    assert ls.scan([f]) == 1
    err = capsys.readouterr().err
    assert tok not in err, "個人 pattern 的內容被印出來了"
    assert "個人 pattern #" in err


# ─────────────────────────────────────────────────────────────────────────────
# 審查模式:副檔名改**白名單**(deny-by-default)—— 票 39 / P2,裁決 4
#
# pre-commit 那個情境用黑名單是對的:跳過二進位省時間、也省雜訊。
# **公開審查的問題不一樣** —— 那裡「沒掃」與「掃過沒事」不能混為一談,
# 而黑名單的性質就是「沒列到的一律進來掃」…… 反過來說,
# 被列到的一律**靜默消失**。審查要的是相反的預設:
#
#   **只掃得懂的才掃,掃不懂的一律浮上來要人看。**
#
# 注意方向:這裡的「白名單」等於 deny-by-default,**與 ADR 0003 同方向**。
# 0003 講的黑名單列的是「不管的東西」,而這裡的清單列的是「要跳過的東西」——
# 同一個東西列在相反的欄位裡,所以要換一邊才維持同一個方向。
# ─────────────────────────────────────────────────────────────────────────────

class TestReviewModeUsesAnExtensionAllowlist:

    def test_an_unknown_extension_is_reported_not_skipped(self, tmp_path,
                                                          capsys):
        """`.env.backup` 這種**沒人列過**的副檔名,審查模式要讓它浮上來。

        它是本輪最想接住的形狀:名字看起來就有問題,而**黑名單裡沒有它**
        (`.backup` 不在 SKIP_SUFFIX、也不在 CERT_EXT),
        於是黑名單其實會照掃 —— 但**掃得懂與否是另一回事**,
        而審查模式不接受「掃過了、沒命中」當成乾淨的證明。
        """
        f = _write_named(tmp_path, "prod.env.backup", "nothing suspicious here")
        rc = ls.scan([f], review=True)
        err = capsys.readouterr().err
        assert rc != 0, "非白名單副檔名在審查模式下被放行了"
        assert "prod.env.backup" in err, err

    def test_an_allowlisted_extension_is_scanned_normally(self, tmp_path):
        """`.md` / `.py` 這些**掃得懂**的,審查模式照原本的內容比對走。"""
        clean = _write_named(tmp_path, "notes.md", "這一行沒有秘密")
        assert ls.scan([clean], review=True) == 0

        dirty = _write_named(tmp_path, "notes2.md",
                             "token = " + "ghp" + "_" + ("A" * 24))
        assert ls.scan([dirty], review=True) == 1

    def test_the_skipped_list_is_part_of_the_report(self, tmp_path, capsys):
        """Q5:**被跳過的清單是報告的必要部分,不是選項。**

        差別在誰負舉證責任:清單在,人看到「跳過了 N 個」會去想那些是什麼;
        清單不在,「跳過」這件事根本不存在於報告上,於是等同沒發生。
        """
        img = _write_named(tmp_path, "logo.png", b"\x89PNG\r\n", mode="wb")
        ls.scan([img], review=True)
        err = capsys.readouterr().err
        assert "logo.png" in err, "被跳過的檔案沒有出現在報告裡:%s" % err

    def test_an_empty_skipped_list_is_still_printed(self, tmp_path, capsys):
        """**空清單也要印。**「印出來是空的」與「沒印」是兩件事 ——
        後者讓人無從分辨這一輪到底有沒有跳過東西。"""
        clean = _write_named(tmp_path, "notes.md", "乾淨")
        ls.scan([clean], review=True)
        err = capsys.readouterr().err
        assert "未內容掃描" in err, "空的跳過清單沒有印出來:%s" % err

    def test_default_mode_is_unchanged(self, tmp_path, capsys):
        """**反控:審查模式不得滲進預設模式。**

        `.env.backup` 在 pre-commit 情境下沒有內容問題就是通過 ——
        把審查模式的嚴格度倒灌回預設,會讓每天的 commit 開始被陌生副檔名擋,
        而**被煩到的規則會被關掉**。
        """
        f = _write_named(tmp_path, "prod.env.backup", "nothing suspicious here")
        assert ls.scan([f]) == 0
        assert "未內容掃描" not in capsys.readouterr().err


# ─────────────────────────────────────────────────────────────────────────────
# 票 106 —— `main()` 的 argv 處理:一個檔都沒掃也回 0
#
# `leak_scan.py:278` 的 `return scan(paths, review=review) if paths else 0`
# 把三條路徑收斂成同一個靜默出口:
#
#   A 不認得的旗標(`--help` / `--foo` / **`--stage` 打錯**)-> 回 0,零輸出
#   B 零路徑                                                -> 回 0,零輸出
#   C `--staged` 但清單為空                                  -> 回 0
#
# **A 與 B 是缺陷,C 不是。** C 碰得到(`--allow-empty`、純刪除 `D`、mode-only),
# 而把它判成 2 會造出一個**永遠無法滿足的條件** —— `scanner.py:219-222` 對
# gitlink 逐字記過同一個教訓:使用者沒有任何合法動作能讓它變乾淨。
#
# **A 比 B 更壞**:B 需要有人手動不給參數,A 只需要打錯一個字元 ——
# `--stage` 少一個 `d`,`|| exit 1` 不觸發,commit 照常成功,
# 而洩漏偵測整層從此不在,沒有任何東西會說。
# ─────────────────────────────────────────────────────────────────────────────

class TestMainNeverReturnsZeroWithoutScanning:
    """票 106 —— 「掃過了乾淨」與「一個檔都沒掃」不得回同一個退出碼。

    `F-155` 的形狀落在洩漏偵測本身:兩者今天在退出碼**與輸出**上都逐字相同。
    """

    def test_an_unknown_flag_is_a_mechanism_error(self, capsys):
        """① **不認得的旗標 -> exit 2,而且訊息要點名它。**

        判準寫「**未知**旗標」而不是「所有旗標」——
        `--staged` / `--review` / `--help` 都是認得的,不走這條。
        點名的理由:一個只說「用法不對」的訊息,對
        `--stage`(少一個 `d`)這種錯**幫不上忙** ——
        人會盯著那一行看半天,而差別只有一個字元。
        """
        rc = ls.main(["--foo"])
        err = capsys.readouterr().err
        assert rc == 2, u"不認得的旗標回了 %r,而不是 2(機制錯誤)" % rc
        assert "--foo" in err, u"訊息沒有點名那個旗標:%r" % err

    def test_a_mistyped_staged_flag_is_caught(self, capsys):
        """① 的實際形狀:`--stage` 少一個 `d`。

        **這一條才是本票真正要防的那個** —— 它不需要任何人做錯事,
        只需要打錯一個字元,而現況是**完全靜默地什麼都不掃**。
        """
        rc = ls.main(["--stage"])
        err = capsys.readouterr().err
        assert rc == 2, u"`--stage`(打錯的 `--staged`)回了 %r,靜默放行" % rc
        assert "--stage" in err, err

    def test_no_paths_at_all_is_a_mechanism_error(self, capsys):
        """② **零路徑 -> exit 2**,訊息要說「沒有給任何路徑」。

        與 ① 分開測:兩者今天走同一行(`:278`),而**修法可以只修一半** ——
        一個只擋未知旗標的實作會讓這一條仍然靜默回 0。
        """
        rc = ls.main([])
        err = capsys.readouterr().err
        assert rc == 2, u"零路徑回了 %r,而不是 2" % rc
        assert "沒有給任何路徑" in err, u"訊息沒說出是什麼問題:%r" % err

    def test_help_prints_usage_and_exits_zero(self, capsys):
        """③ **`--help` -> 印用法,exit 0**(裁四:甲案)。

        ⚠ **這一條的紅在「沒有輸出」那一半,不是退出碼那一半** ——
        `--help` 今天**本來就回 0**。
        **寫成只斷言退出碼的話,它從第一天就是綠的,而且永遠不會紅**(`F-158`)。

        本票的病是**靜默**,不是 exit 0 本身:`--help` 印了用法就不靜默了,
        而「查用法回機制錯誤」會讓人以為裝壞了。
        """
        rc = ls.main(["--help"])
        cap = capsys.readouterr()
        out = cap.out + cap.err
        assert rc == 0, u"`--help` 回了 %r" % rc
        assert "用法" in out and "--staged" in out, (
            u"`--help` 沒有印出用法(檔頭 :7-9 那三行):%r" % out[:200])

    def test_an_empty_staged_list_still_returns_zero(self, monkeypatch, capsys):
        """④ **負控:`--staged` 但清單為空,仍要回 0。**

        🔴 **這一條寫完就是綠的,而它是本組最要緊的一條。**

        C 碰得到:`git commit --allow-empty`、**純刪除**(`staged_paths` 用
        `--diff-filter=ACM`,`D` 不在裡面)、mode-only 改動。
        把它判成 2,就是把「**沒有東西要掃這回事**」判成「掃描機制壞了」,
        造出一個**永遠無法滿足的條件** —— 使用者沒有任何合法動作
        能讓一個 `--allow-empty` 的 commit 變得「有檔案可掃」。
        `scanner.py:219-222` 對 gitlink 逐字記過同一個教訓。

        **「問不到」早就回 2 了**(`scanner.staged_paths` 對非零退出碼 raise),
        所以這裡回 0 是對的,不是漏網。

        ⚠ **沒有這一條,下一個人會順手把三條都改成 2** ——
        而那個改動**讀起來會像「把 fail-closed 做得更徹底」**。
        """
        class _R:
            returncode = 0
            stdout = b""
            stderr = b""
        monkeypatch.setattr(ls.subprocess, "run", lambda *a, **k: _R())
        rc = ls.main(["--staged"])
        err = capsys.readouterr().err
        assert rc == 0, u"沒有 staged 檔卻回了 %r —— 那會擋死 --allow-empty" % rc
        assert "機制" not in err and "沒有給任何路徑" not in err, (
            u"沒有 staged 檔被說成機制錯誤:%r" % err)


# ─────────────────────────────────────────────────────────────────────────────
# 票 108:通用組**逐條**正對照 —— 表驅動
#
# 在這之前,往 `leak-patterns.txt` 加一行**不會有任何東西要求它配一條斷言**:
# 加完測試全綠,而那條規則從沒被驗證過會命中。與票 102 記過的形狀同一族 ——
# **輸入存在不等於斷言存在。**
#
# 表以 **pattern 原字串**為 key。改了一條 pattern,key 就對不上 → 紅 →
# 有人得回來看。**這是本票唯一那個「規則變動會叫」的機制。**
#
# **key 也要組裝,不只樣本。** 憑證副檔名那三條的 pattern 字串
# **自己就打得到自己**(字串裡含 `.` 接副檔名再接非字元 ⇒ `\b` 成立),
# 寫成字面的話**這個測試檔**會被 shipped-tree 掃描擋下 ——
# 與檔頭那條紀律同一個理由,只是這次中槍的是 key 不是樣本。
#
# **這不是推論,是實測**(票 108 刀一):本段原本把那三條的 pattern
# 寫成字面當例子,`test_the_shipped_tree_is_clean` 當場紅,
# 擋下訊息點名的就是**這幾行註解**。⇒ **連解釋這條陷阱的句子都會踩到它。**
#
# ⚠ **本表目前只驗一個方向:「pattern 都有樣本嗎」。**
# 反方向(「樣本都還對應得到 pattern 嗎」——刪掉一條 pattern 之後表裡會留下
# 孤兒)**沒有機器在管**。CLAUDE.md 那條「驗兩個方向」的判準適用於此,
# 而本票的裁決範圍只含前者,所以它是一個**寫下來的缺口**,不是留白。
# ─────────────────────────────────────────────────────────────────────────────

_PFX = "pfx"                             # 組裝:字面的 `.` + 這三個字會打到自己
_P12 = "p" + "12"
_PEM = "pem"

_NO_LOCAL = str(ROOT / "tests" / "no-such-leak-patterns.local.txt")

# pattern 原字串 -> 該條規則的**組裝**正樣本(一整行內容)。
#
# **憑證那三條的樣本放在【內容】裡,不放檔名。** `leak_scan.scan()` 會先用
# `CERT_EXT` 對**路徑**短路(不讀內容);把樣本放成檔名的話走的是副檔名那條路,
# **regex 一個字都沒被驗到**,而測試照樣綠。
SAMPLES = {
    "\\." + _PFX + "\\b": "keyfile = client." + _PFX,
    "\\." + _P12 + "\\b": "bundle = server." + _P12,
    "\\." + _PEM + "\\b": "cert = server." + _PEM,
    "-----BEGIN " + "[A-Z ]*" + "PRIVATE KEY-----":
        "-----BEGIN RSA " + "PRIVATE KEY-----",
    "\\bsk-[A-Za-z0-9]{16,}": "OPENAI_API_KEY=" + "sk" + "-" + ("A" * 20),
    "\\bghp_[A-Za-z0-9]{20,}": "token=" + _TOK,
    "\\bgithub_pat_[A-Za-z0-9_]{20,}":
        "token=" + "github" + "_pat_" + ("A" * 24),
    "\\bAKIA[0-9A-Z]{16}\\b": "aws_access_key_id = " + "AKIA" + ("Z" * 16),
    "\\bxox[baprs]-[A-Za-z0-9-]{10,}": "slack = " + "xox" + "b-" + ("A" * 12),
    "\\bAIza[A-Za-z0-9_\\-]{30,}": "key = " + "AIza" + ("Z" * 35),
    # 票 108 的本體:Google 2026-06 起的 Gemini 新格式 Auth key。
    "\\bAQ\\.[A-Za-z0-9_\\-]{40,}": "GOOGLE_API_KEY=" + "AQ" + "." + ("A" * 50),
}


def _generic_pattern_strings():
    """`load_patterns()` 的**通用組**原字串。

    `LOCAL_PATTERNS_FILE` 暫時指到不存在的路徑 —— **只驗出貨檔**。
    這台機器上個人清單是存在的;不隔開的話這張表會被一份**不進版控、
    每台機器不同**的清單汙染,而**下游根本收不到那份清單** ——
    於是本地全綠、下游沒有規則,兩件事看起來一樣。
    """
    saved = ls.LOCAL_PATTERNS_FILE
    ls.LOCAL_PATTERNS_FILE = _NO_LOCAL
    try:
        generic = [g for g in ls.load_patterns() if g.name == u"通用"]
    finally:
        ls.LOCAL_PATTERNS_FILE = saved
    assert len(generic) == 1, u"找不到通用組(load_patterns 的分組變了?)"
    return [raw for raw, _rx in generic[0].patterns]


GENERIC_PATTERNS = _generic_pattern_strings()


@pytest.mark.parametrize("pattern", GENERIC_PATTERNS)
def test_every_generic_pattern_has_a_positive_control(pattern, tmp_path,
                                                     monkeypatch):
    """出貨檔裡的**每一條**通用 pattern 都要有一個組裝正樣本,而且真的命中。

    **缺樣本一律紅,不 skip。** skip 的話這條元測試就退化成
    「有樣本的都過」—— 而那正是它要修的病:**沒被驗的那些會安靜地不存在。**
    """
    monkeypatch.setattr(ls, "LOCAL_PATTERNS_FILE", _NO_LOCAL)
    assert pattern in SAMPLES, (
        u"通用 pattern %r 沒有正樣本 —— 在 SAMPLES 裡補一條組裝樣本。\n"
        u"    (不得寫死敏感字面:本檔自己也被 shipped-tree 掃描)" % pattern)
    rc = ls.scan([_write(tmp_path, SAMPLES[pattern])])
    assert rc == 1, (
        u"通用 pattern %r 有樣本卻沒命中(scan 回 %r)—— "
        u"樣本與 pattern 對不上,規則等於不存在" % (pattern, rc))


def test_the_new_google_key_shape_is_caught(tmp_path, monkeypatch):
    """票 108 正控:`AQ.` + 50 字的新格式 Auth key 要被擋。

    **組裝**,不寫死。桌機 2026-09-05 實測:含新鑰的 `.env` 餵給 `leak_scan`
    回 exit 0(沒擋)—— 舊的 `\\bAIza…` 那條打不到新格式。
    """
    monkeypatch.setattr(ls, "LOCAL_PATTERNS_FILE", _NO_LOCAL)
    sample = "GOOGLE_API_KEY=" + "AQ" + "." + ("A" * 50)
    assert ls.scan([_write(tmp_path, sample)]) == 1, \
        u"新格式金鑰沒被擋 —— 通用組缺 AQ. 那條"


def test_a_short_aq_string_is_not_caught(tmp_path, monkeypatch):
    """反控:`AQ.` + **39** 字不命中 —— 釘住下限真的在 40。

    少了它,把 `{40,}` 誤打成 `{4,}` 之類的**放寬**方向不會有任何測試抱怨,
    而放寬的失效是靜默的(誤擋才吵)。
    """
    monkeypatch.setattr(ls, "LOCAL_PATTERNS_FILE", _NO_LOCAL)
    short = "GOOGLE_API_KEY=" + "AQ" + "." + ("A" * 39)
    assert ls.scan([_write(tmp_path, short)]) == 0, \
        u"低於下限的字串被擋了 —— 下限不在 40"
