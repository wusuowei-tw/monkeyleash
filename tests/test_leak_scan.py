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


def test_the_shipped_tree_is_clean():
    """**發布來源自己必須乾淨** —— 持續的機器保證,不是一次性人工斷言。

    掃描用兩份 pattern 的聯集(含本機個人清單),所以它也會抓到
    「不小心把個人資料寫進版控檔」。"""
    import os
    files = []
    for dp, dns, fns in os.walk(str(ROOT)):
        rel = os.path.relpath(dp, str(ROOT)).replace("\\", "/")
        if any(x in ("/" + rel + "/") for x in
               ("/.git/", "/skills/", "/__pycache__/", "/.pytest_cache/",
                "/.dev/", "/.cache/", "/.scratch/")) or rel.startswith(".claude/skills"):
            dns[:] = []
            continue
        for fn in fns:
            files.append(os.path.join(dp, fn))
    assert ls.scan(files) == 0, "發布來源含洩漏 —— 見上方輸出"


def test_gitignore_content_is_not_scanned(tmp_path):
    """.gitignore 的工作是列出秘密檔形狀 —— 內容掃它必然假陽性(F-062 實測:
    安裝器產的秘密檔區塊被掃描器擋下)。與 pattern 檔跳過自己同一個理由。
    副檔名組裝而不寫死,同本檔其他測試。"""
    g = tmp_path / ".gitignore"
    g.write_text("*." + "pfx" + "\n*." + "pem" + "\n", encoding="utf-8")
    assert ls.scan([str(g)]) == 0
