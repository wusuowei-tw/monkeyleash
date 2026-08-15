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
