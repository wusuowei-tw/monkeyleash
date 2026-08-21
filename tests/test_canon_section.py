# -*- coding: utf-8 -*-
"""票 53 偵測器 I 的**上游專用**那一半 —— 三條樹相依 / 出口未備的判定。

**本檔標 `skip`,不出貨。** 三條各有各的理由,合檔所以取最嚴的那條:

  I-1b  每條存在的規則都要在正典段出現過   **出口未備**,見下
  I-3   正典段的 ADR 引用要 resolve        `docs/adr/` 目前標 `ask`(票 66 止血),
                                            下游那份可能落後
  I-5   正典段的路徑 token 全部要被分類     分類表是**上游這棵樹**的事實

與本檔配對的另一半在 `tests/test_claude_md.py`(標 `copy`,跟著出貨):
I-1a / I-2 / I-4 / 枚舉沒壞。切法的判準是**下游那一側的事實**,
不是上游的進度 —— 照 `tests/test_bootstrap.py` 那一則的教訓。

## ⚠ 釘子 —— I-1b 為什麼還不能出貨,以及它什麼時候可以

`CLAUDE.md` 標 `generate`:**sync 從不更新下游的正典段**。
而 `.claude/hooks/gate.py` 標 `copy`:**每次 sync 都更新**。

所以上游加一條規則之後,下游的下一次 sync 會讓
「它的 gate.py 有 R9」與「它的正典段沒提過 R9」同時成立 —— **I-1b 當場紅**,
而下游沒有做錯任何事,也沒有任何指令可以修好它。

**一道 fail-closed 守衛在出口存在之前不得出貨**(票 66 逐字:
「一道沒有出口的 fail-closed 守衛,第一次擋住的時候就會被繞過或拿掉」)。

出口是 B5 的 `--regenerate-canon`。**B5 落地之後,I-1b 搬進
`tests/test_claude_md.py`,本檔剩兩條。** 到期條件是「那個指令存在且驗收過」,
不是「B5 那一刀 commit 了」。

另外三條為什麼沒有同一個問題(逐條問過,不是推的):

  I-1a  下游的舊正典段提到的代號是**現有代號的子集** -> 不會紅
  I-2   舊正典段引用的是**更舊的** F 號,而 friction-log 只增不刪 -> resolve 得到
  I-4   舊正典段的行號引用命中數是 0(實測基準 `7253d46` 與 `d9aefd4` 都是 0)
"""

import importlib.util
import io
import os
import pathlib
import re

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
# I-1b —— 每條存在的規則都要在正典段出現過至少一次
# ─────────────────────────────────────────────────────────────────────────────
#
# **與 I-1a 是兩個問題,不是同一個檢查跑兩遍。**
# I-1a 的參照物是**現實**(規則還在不在),I-1b 的參照物是**正典段的過去**
# (它涵蓋了多少)。參照物不同,盲區就不同。
#
# 標本:2026-08-21 實測,`rule_codes()` 是 R1..R8 而正典段從頭到尾沒提過 R6 ——
# 票 51 ① 只記了「R8 不在規則表」,而 R6 連散文裡都沒有。
# 每一個下游拿到的規則清單因此少一條,**而沒有任何東西說話**。
#
# 規則表自己寫著「只求『列出的每一條都對』,不宣稱『列完了』」——
# 那句話管的是**表**,本條管的是**整段**。兩件事。

def rules_named_in(text):
    return set(re.findall(r"\bR\d+\b", text))


def test_every_rule_that_exists_is_named_somewhere_in_the_canon():
    gate = _load("gate_for_canon_section",
                 pathlib.PurePath(".claude", "hooks", "gate.py"))
    authoritative = gate.rule_codes()
    assert authoritative, "`rule_codes()` 回空 —— 權威來源讀不到,不是通過"
    missing = sorted(authoritative - rules_named_in(canon_text()))
    assert not missing, (
        "下列規則存在,而正典段從頭到尾沒有提過:%s\n"
        "正典段跟著每一次 install 出貨,所以每個下游拿到的規則清單都少這幾條。\n"
        "改法:規則表加一列(表只求「列出的每一條都對」,加一列正確的不違反它)。"
        % ", ".join(missing))


def test_i1b_catches_a_rule_that_the_canon_never_mentions():
    """I-1b 的正對照。"""
    assert sorted({"R1", "R2", "R6"} - rules_named_in("表裡有 R1 與 R2。")) == ["R6"]


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

# 不必存在於這棵樹上的 token,逐一給理由。**理由欄不是註解,是判準本身** ——
# 清單一長判準就會漂移,理由欄是讓漂移看得見的東西(照 manifest.py 的同一條)。
NOT_EXPECTED_ON_DISK = {
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


def test_every_path_token_in_the_canon_is_classified():
    tokens = path_tokens_in(canon_text())
    assert tokens, "正典段一個路徑 token 都沒枚舉到 —— 枚舉本身壞了,不是通過"
    unclassified = []
    for t in tokens:
        if t in NOT_EXPECTED_ON_DISK:
            continue
        if not (ROOT / pathlib.PurePath(t)).exists():
            unclassified.append(t)
    assert not unclassified, (
        "正典段的下列路徑 token 在這棵樹上不存在,而且沒有被分類:\n  %s\n"
        "判一次它屬於哪一種:\n"
        "  在這棵樹上 -> 把引用寫成完整路徑(裸檔名不算)\n"
        "  使用者層 / gitignored / 上下文相對名 / 設計上可缺\n"
        "     -> 加進本檔的 NOT_EXPECTED_ON_DISK,**連理由一起寫**\n"
        % "\n  ".join(unclassified))


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
    assert "g1_verify.py" not in NOT_EXPECTED_ON_DISK, \
        "裸檔名不該靠豁免表放行 —— 出口是把它寫成完整路徑"
    assert not (ROOT / "g1_verify.py").exists(), "這個標本要成立,樹根不能真的有這個檔"
