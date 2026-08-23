# -*- coding: utf-8 -*-
"""票 53 偵測器 I 的**上游專用**那一半 —— 兩條樹相依的判定。

**本檔標 `skip`,不出貨。** 兩條各有各的理由,合檔所以取最嚴的那條:

  I-3   正典段的 ADR 引用要 resolve        `docs/adr/` 目前標 `ask`(票 66 止血),
                                            下游那份可能落後
  I-5   正典段的路徑 token 全部要被分類     分類表是**上游這棵樹**的事實

與本檔配對的另一半在 `tests/test_claude_md.py`(標 `copy`,跟著出貨):
I-1a / I-1b / I-2 / I-4 / 枚舉沒壞。切法的判準是**下游那一側的事實**,
不是上游的進度 —— 照 `tests/test_bootstrap.py` 那一則的教訓。

## 釘子已拔:I-1b 於 2026-08-21 搬去 `tests/test_claude_md.py`

原本扣在本檔,理由是**出口未備**:`CLAUDE.md` 標 `generate`(sync 從不更新
下游的正典段),而 `.claude/hooks/gate.py` 標 `copy`(每次 sync 都更新)——
上游加一條規則之後,下游的下一次 sync 就讓
「它的 gate.py 有 R9」與「它的正典段沒提過 R9」同時成立,I-1b 當場紅,
**而下游沒有做錯任何事,也沒有任何指令可以修好它**。

到期條件寫的是「**那個指令存在且驗收過**」,不是「B5 那一刀 commit 了」——
兩者現在都成立(`sync.py --regenerate-canon`,六條驗收)。
搬過去安全的理由:**斷言與它的出口同在 `copy` 桶**,下游同一批拿到,
不存在「先收到紅、後收到出口」的窗口。

另外三條當時為什麼沒有同一個問題(逐條問過,不是推的):

  I-1a  下游的舊正典段提到的代號是**現有代號的子集** -> 不會紅
  I-2   舊正典段引用的是**更舊的** F 號,而 friction-log 只增不刪 -> resolve 得到
  I-4   舊正典段的行號引用命中數是 0(實測基準 `7253d46` 與 `d9aefd4` 都是 0)
"""

import importlib.util
import io
import os
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load(name, relpath):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


claude_md = _load("claude_md_for_canon", pathlib.PurePath(
    ".claude", "portable", "claude_md.py"))


def canon_text():
    return claude_md.framework_section(
        io.open(ROOT / "CLAUDE.md", encoding="utf-8").read())


# ─────────────────────────────────────────────────────────────────────────────
# I-3 —— 正典段的 ADR 引用要 resolve
# ─────────────────────────────────────────────────────────────────────────────
#
# 前綴比對,不比全名:ADR 檔名是 `NNNN-slug.md`,而正典段引用的是編號。
# 上游 0012 之後改用 `F-00NN` 前綴,所以兩種前綴都試(票 66 順帶登記過
# 那是慣例不是機制)。

ADR_REF = re.compile(r"docs/adr/(F-\d+|\d+)")


def adr_refs_in(text):
    out = []
    for r in ADR_REF.findall(text):
        if r not in out:
            out.append(r)
    return out


def _adr_filenames():
    return sorted(os.listdir(ROOT / "docs" / "adr"))


def test_every_adr_reference_in_the_canon_resolves():
    names = _adr_filenames()
    assert names, "`docs/adr/` 一個檔都沒枚舉到 —— 枚舉本身壞了,不是通過"
    refs = adr_refs_in(canon_text())
    assert refs, "正典段一個 ADR 引用都沒有 —— 枚舉本身壞了,不是通過"
    bad = [r for r in refs
           if not any(n.startswith(r) or n.startswith("F-" + r) for n in names)]
    assert not bad, (
        "正典段引用了不存在的 ADR:%s\n"
        "ADR 被改名或刪除時,正典段沒有跟著改。" % ", ".join(bad))


def test_i3_catches_an_adr_reference_that_does_not_resolve():
    """I-3 的正對照。"""
    assert adr_refs_in("見 `docs/adr/0003` 與 `docs/adr/9999`") == ["0003", "9999"]


# ─────────────────────────────────────────────────────────────────────────────
# I-5 —— 正典段的路徑 token 全部要被分類,未分類即紅
# ─────────────────────────────────────────────────────────────────────────────
#
# **為什麼是分類、不是「所有路徑都必須存在 + 例外清單」**:例外會有 10 項,
# 而 10 項的理由各不相同(使用者層 / gitignored / 上下文相對名 / 設計上可缺)。
# **10 項例外的黑名單不是黑名單,是一份寫反了的白名單。**
#
# 分類式仍然 fail-closed:**未分類即紅**,同標記表那條
# 「沒被提到不是合法狀態」。明天有人在正典段加一個新的路徑引用,
# 沒進下表就是紅,而紅的訊息會告訴他要判什麼。
#
# **誠實話:下表是人寫的,所以「未分類 = 0」今天為真是因為表照今天的內容寫。**
# 真正的斷言是那個條件本身,它對**明天新增的** token 才有效力。

# **「存在」的判準是 git 追蹤集合,不是磁碟。**(2026-08-21,CI run #34 的教訓)
#
# 第一版用 `os.path.exists()`,本機全綠而 CI 紅:`.dev/pipeline.json` 在**開發機**
# 的磁碟上,而它被 `.gitignore` 排除,乾淨 checkout 沒有它 —— 於是它在本機被歸進
# 「存在」桶,在 CI 變成未分類。
#
# **根因不是漏了一個檔,是判準問錯了問題。** I-5 要問的是
# 「這個引用指向的東西**會不會跟著出貨**」,而那是**出貨樹**的性質;
# 磁碟只是「這台機器現在長什麼樣」,兩者在開發機上碰巧重合。
#
# 換判準之後,兩個 token 的分類改變(逐一對照過 22 個):
#   `.dev/pipeline.json`  磁碟在 / git 未追蹤  <- CI 抓到的那個
#   `.git/hooks/`         磁碟在 / git 未追蹤  <- **CI 也抓不到的那個**
# 後者要緊:git 自己會在每個 clone 建出 `.git/hooks/`,所以它在**兩邊**的磁碟上
# 都存在 —— 舊判準下它永遠綠,而它從來就不是出貨樹的一部分。
# **同一族的兩個成員,一個被 CI 抓到、一個連 CI 都跳過**,而分辨它們的是判準本身。

# 不會跟著出貨的 token,逐一給理由。**理由欄不是註解,是判準本身** ——
# 清單一長判準就會漂移,理由欄是讓漂移看得見的東西(照 manifest.py 的同一條)。
NOT_IN_THE_SHIPPED_TREE = {
    ".dev/pipeline.json":            "執行期狀態,`.gitignore` 排除 —— "
                                     "每個 repo 自己產生,不隨出貨走(票 31 的 .dev 分軌)",
    ".git/hooks/":                   "git 自己的目錄,依定義不進版控 —— "
                                     "而它在每個 clone 的磁碟上都存在,所以磁碟判準看不見它",
    "~/.claude/settings.json":       "使用者層 —— 不在任何 repo 裡,CI 上也沒有",
    "~/.claude/hooks/g1_guard.py":   "使用者層 —— G1 的本體依設計住家目錄(ADR 0009)",
    "~/.claude/g1-protected.txt":    "使用者層 —— 保護清單不進版控(它自己在保護清單裡)",
    ".claude/skills/":               "gitignored 鏡像 —— 由上游工具產生,不進版控",
    "skills/":                       "gitignored 鏡像 —— 同上",
    ".scratch/portability/grill.md": "gitignored 工作階段暫存 —— 本機才有",
    "CONTEXT.md":                    "設計上可缺 —— domain.md 逐字:"
                                     "「If any of these files don't exist, proceed silently」",
    "gate.py":                       "上下文相對名,不是路徑 —— 全名在同段別處出現過",
    "scanner.py":                    "上下文相對名 —— 同上",
    "pipeline-stages.yaml":          "上下文相對名 —— 同上",
}

PATH_TOKEN = (
    re.compile(r"`([A-Za-z0-9_.~/-]+\.(?:py|md|json|yaml|yml|txt|sh))`"),
    re.compile(r"`([A-Za-z0-9_.~/-]+/)`"),
)


def path_tokens_in(text):
    out = []
    for pat in PATH_TOKEN:
        for t in pat.findall(text):
            if t not in out:
                out.append(t)
    return out


def tracked_paths():
    """出貨樹 = git 追蹤集合。**不是磁碟** —— 見上面那段的由來。"""
    out = subprocess.run(["git", "ls-files", "-z"],
                         cwd=str(ROOT), capture_output=True)
    assert out.returncode == 0, out.stderr
    return set(p for p in out.stdout.decode("utf-8").split("\0") if p)


def in_shipped_tree(token, tracked):
    """目錄 token 用前綴比對,檔案 token 用完全比對。"""
    if token.endswith("/"):
        return any(p.startswith(token) for p in tracked)
    return token in tracked


def test_every_path_token_in_the_canon_is_classified():
    tokens = path_tokens_in(canon_text())
    assert tokens, "正典段一個路徑 token 都沒枚舉到 —— 枚舉本身壞了,不是通過"
    tracked = tracked_paths()
    assert tracked, "`git ls-files` 回空 —— 枚舉本身壞了,不是通過"
    unclassified = [t for t in tokens
                    if t not in NOT_IN_THE_SHIPPED_TREE
                    and not in_shipped_tree(t, tracked)]
    assert not unclassified, (
        "正典段的下列路徑 token **不在出貨樹裡**(git 追蹤集合),而且沒有被分類:\n  %s\n"
        "判一次它屬於哪一種:\n"
        "  會跟著出貨 -> 把引用寫成完整路徑(裸檔名不算),並確認它真的進版控\n"
        "  使用者層 / gitignored / git 自己的目錄 / 上下文相對名 / 設計上可缺\n"
        "     -> 加進本檔的 NOT_IN_THE_SHIPPED_TREE,**連理由一起寫**\n"
        "判準是 git 不是磁碟:磁碟只說「這台機器現在長什麼樣」。\n"
        % "\n  ".join(unclassified))


def git_ignores(rel):
    """`git check-ignore` 命中嗎。

    **這是版控裡的事實,不是這台機器的事實** —— 規則寫在 `.gitignore`,
    每個 clone 都一樣。用它來表達「工作機會長出這個檔,而它永不進出貨樹」,
    比斷言「磁碟上有沒有」強一階:後者在乾淨 checkout 上是假的。
    """
    out = subprocess.run(["git", "check-ignore", "-q", rel],
                         cwd=str(ROOT), capture_output=True)
    return out.returncode == 0


def test_the_shipped_tree_criterion_is_not_the_disk_criterion():
    """判準換掉的那一格,留一條測試釘住它不會被換回去。

    標本兩個,**而它們被發現的方式不同**:

      `.dev/pipeline.json`  兩邊磁碟不同 -> CI run #34 紅,所以被發現
      `.git/hooks/`         **兩邊磁碟都有** -> CI 不會紅,舊判準下它永遠綠

    後者是這一格存在的理由:**一個判準的錯,只有一部分會被環境差異照出來。**

    ## 本條自己犯過同一個錯(CI run #36)

    第一版對兩個 token 都斷言「磁碟上存在」—— 而 `.dev/pipeline.json`
    在乾淨 checkout 上不存在,於是**這條釘住判準的測試,自己用了它要釘掉的判準**。

    那是同一族在 24 小時內的第三次:
      作者(B0 寫裸檔名)-> 環境(I-5 用磁碟判準)-> **釘子本身(本條)**
    每一次都比前一次高一層,而**高一層的那次更難看見,因為它看起來像在防守**。

    改法:斷言只用**環境無關的事實**。
      兩個 token   不在 git 追蹤集合 + 已分類且附理由   (處處為真)
      `.git/hooks/` 磁碟上存在                          (git 依定義在每個 clone 都建它)
      `.dev/pipeline.json` 被 `.gitignore` 命中          (規則在版控裡)

    CI run #34 的紅**留在這段文字裡當歷史證據**,不再當成可斷言的事實。
    """
    tracked = tracked_paths()

    # (a) 兩個都硬斷言:不在出貨樹、已分類、理由非空。
    for token in (".dev/pipeline.json", ".git/hooks/"):
        assert not in_shipped_tree(token, tracked), \
            "%s 進了出貨樹 —— 標本失效,回頭重判它的分類" % token
        assert token in NOT_IN_THE_SHIPPED_TREE, "%s 沒有被分類" % token
        assert NOT_IN_THE_SHIPPED_TREE[token].strip(), \
            "%s 分類了但沒寫理由 —— 理由欄是讓判準漂移看得見的東西" % token

    # (b) 磁碟那半只對 `.git/hooks/` 硬斷言 —— git 依定義在每個 clone 都建它,
    #     所以「磁碟有、出貨樹沒有」這個組合處處成立。它是較強的那個標本。
    assert (ROOT / ".git" / "hooks").exists(), \
        "`.git/hooks/` 不在磁碟上 —— 那不是 git repo,本條的前提不成立"

    # (c) `.dev/pipeline.json` 改用 ignore 規則表達,不用磁碟。
    #     語意:工作機會長出它,而它永不進出貨樹。
    assert git_ignores(".dev/pipeline.json"), \
        "`.dev/pipeline.json` 不再被 .gitignore 命中 —— 分類的前提變了,回頭重判"


def test_i5_catches_an_unclassified_path_token():
    """I-5 的正對照 —— 標本是**寫這條判準的人自己**。

    B0(`ef995c1`)第一版把新指標寫成裸檔名 `g1_verify.py`,唯讀探測當場報
    「未分類 1 -> 紅」。它與 `gate.py` / `scanner.py` 同類(上下文相對名),
    而處置不是把它加進豁免表,是**改寫成完整路徑** ——
    完整路徑指得到東西,裸檔名要讀者自己猜。

    **判準還沒落地,而它在寫下來的當天就抓到一次真的,對象是寫它的人。**
    """
    found = path_tokens_in("跑完 `g1_verify.py` 的全套驗收,見 `docs/adr/`")
    assert found == ["g1_verify.py", "docs/adr/"]
    assert "g1_verify.py" not in NOT_IN_THE_SHIPPED_TREE, \
        "裸檔名不該靠豁免表放行 —— 出口是把它寫成完整路徑"
    assert not (ROOT / "g1_verify.py").exists(), "這個標本要成立,樹根不能真的有這個檔"
