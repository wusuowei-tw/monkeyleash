# -*- coding: utf-8 -*-
"""CI 設定檔的安全驗收 —— 票 54 的四條件裡的 1 / 2 / 4。

**紅燈先行。** 本檔在 `.github/workflows/*.yml` 存在之前就寫,第一次跑必紅
(找不到 workflow)。那個紅是要它紅:**「還沒有 CI」與「CI 沒被驗」
在綠燈上長得一樣**,而只有前者是暫時的。

為什麼寫成測試而不是寫成規矩:**註解不是機制**(F-086)。
「設定檔不得出現密鑰」寫在票面上,下一個改 workflow 的人不會讀票面 ——
他會讀 CI 紅不紅。

四條件裡的第 3 條(不得為了讓測試變綠而把 `~/.claude/` 的檔案上傳或重建到 CI)
沒有自己的測試:它由 `test_nothing_reaches_for_the_user_layer` 涵蓋 ——
**要用那些檔案,就得先寫出它們的位置**,而那條路被封住了。
"""
import glob
import importlib.util
import io
import os
import pathlib
import re

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / ".github" / "workflows"


def _load_leak_scan():
    spec = importlib.util.spec_from_file_location(
        "leak_scan_for_ci_test", ROOT / ".claude" / "portable" / "leak_scan.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def workflow_files():
    return sorted(glob.glob(str(WORKFLOW_DIR / "*.yml"))
                  + glob.glob(str(WORKFLOW_DIR / "*.yaml")))


def _text(path):
    return io.open(path, encoding="utf-8").read()


def _walk_uses(node):
    """遞迴取出所有 `uses:` 的值 —— 不假設 step 的巢狀深度。

    寫死 `jobs -> steps` 的話,composite action、reusable workflow
    (`jobs.<id>.uses`)這些位置的 `uses` 會漏掉,而**漏掉的那個不會出聲**。
    """
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "uses" and isinstance(v, str):
                yield v
            else:
                for u in _walk_uses(v):
                    yield u
    elif isinstance(node, list):
        for item in node:
            for u in _walk_uses(item):
                yield u


# ── 使用者層的「位置」——封閉集合,枚舉不比對(F-087)────────────────
#
# 只封位置,不封 `~/.claude/` 底下每一個檔名:`settings.json`、`cache/`、
# `hooks/` 這些名字在 CI 設定裡有正當用途(`actions/cache` 就是一個),
# 全列進去會製造假警報,而**假警報會訓練人去忽略這條測試**。
#
# 位置這一組才是真正的封閉集合:**要讀那些檔案,就得先寫出它們住在哪**。
USER_LAYER_LOCATIONS = (
    "~/.claude",
    "$HOME/.claude",
    "${HOME}/.claude",
    "%USERPROFILE%",
    "$USERPROFILE",
    "${USERPROFILE}",
    "$env:USERPROFILE",
)

# 名字本身就不可能為了別的理由出現在 CI 設定裡的那幾個。
# 位置那一組是主防線,這一組是它的反控 —— 有人用別的寫法組出路徑時仍會命中。
USER_LAYER_DISTINCTIVE_NAMES = (
    "leak-patterns.local.txt",
    "g1-protected.txt",
    "shadow-clamp.txt",
    "upstream-roots.txt",
    "age-recipient.txt",
    ".credentials.json",
    "g1-trace.log",
)


def test_there_is_at_least_one_workflow():
    """**紅燈錨點。** 沒有 workflow 時整組驗收會空轉全綠 ——
    而那正是「沒有 CI」被讀成「CI 是安全的」的那一步。
    """
    assert workflow_files(), (
        "%s 底下沒有任何 workflow —— 這一組驗收目前什麼都沒驗。\n"
        "     這是票 54 的第一個紅燈,寫 YAML 之後它才該變綠。" % WORKFLOW_DIR)


@pytest.mark.parametrize("path", workflow_files() or [None])
def test_no_secrets_are_referenced(path):
    """條件 1:設定檔不得出現任何密鑰或權杖。

    本 repo 的 CI 只跑測試,不發布、不部署、不對外呼叫 —— **它不需要任何密鑰**。
    所以判準不是「密鑰有沒有寫對」,是 `secrets.` 這個詞根本不該出現:
    **需求為零時,任何一次出現都是需求變了**,而那要有人看見。
    """
    if path is None:
        pytest.skip("沒有 workflow — 由 test_there_is_at_least_one_workflow 負責紅")
    body = _text(path)
    hits = [(i, l.strip()) for i, l in enumerate(body.splitlines(), 1)
            if "secrets." in l or "${{ secrets" in l]
    assert not hits, (
        "%s 引用了 secrets(本 repo 的 CI 不需要任何密鑰):\n  %s"
        % (os.path.basename(path),
           "\n  ".join("第 %d 行:%s" % (i, l) for i, l in hits)))


@pytest.mark.parametrize("path", workflow_files() or [None])
def test_nothing_reaches_for_the_user_layer(path):
    """條件 1 + 條件 3:不得碰 `~/.claude/` 底下任何東西。

    條件 3(「不得為了讓測試變綠而把那些檔案上傳或重建到 CI」)由這條涵蓋:
    **要用它們,就得先寫出它們的位置。**

    個人 pattern 那 12 條測試在 CI 上是**放棄涵蓋**,不是想辦法補齊 ——
    補齊的唯一辦法是把 `leak-patterns.local.txt` 送上 CI,而那個檔的內容
    本身就是要防的東西(使用者名稱、資料夾名、往來對象)。
    **為了讓測試變綠而洩漏它要保護的東西,是把手段換成了反面。**
    """
    if path is None:
        pytest.skip("沒有 workflow — 由 test_there_is_at_least_one_workflow 負責紅")
    body = _text(path)
    found = [t for t in USER_LAYER_LOCATIONS + USER_LAYER_DISTINCTIVE_NAMES
             if t in body]
    assert not found, (
        "%s 指向使用者層:%s\n"
        "     那些檔案不進版控、不上 CI。缺了它們的涵蓋是已知代價(票 54 落差表),"
        "不是待補的洞。" % (os.path.basename(path), found))


@pytest.mark.parametrize("path", workflow_files() or [None])
def test_leak_scan_is_clean_on_the_workflow(path):
    """條件 1:用 repo 自己的洩漏偵測掃 workflow 檔本身。

    上面兩條是**列舉已知形狀**,這條是**通用形狀**(金鑰、權杖、憑證)。
    兩者不重疊:列舉抓得到我想得到的,通用抓得到我沒想到的。
    """
    if path is None:
        pytest.skip("沒有 workflow — 由 test_there_is_at_least_one_workflow 負責紅")
    leak_scan = _load_leak_scan()
    rc = leak_scan.scan([path])
    assert rc == 0, "leak_scan 對 %s 回 %d(0=乾淨 / 1=有命中 / 2=機制錯誤)" % (
        os.path.basename(path), rc)


@pytest.mark.parametrize("path", workflow_files() or [None])
def test_permissions_are_least_privilege(path):
    """條件 2:明寫 `permissions: contents: read`,而且只有這一項。

    **沒寫 `permissions` 不等於安全** —— 沒寫的時候用的是 repo 的預設,
    而預設可能是讀寫,且**那個預設不在這個檔案裡,改了不會有 diff**。
    所以判準是「有沒有明寫」,不是「有沒有寫錯」。

    多一項就紅:`contents: read` 之外的每一項都要有人說出理由,
    而說理由的地方是裁決,不是這個檔。
    """
    if path is None:
        pytest.skip("沒有 workflow — 由 test_there_is_at_least_one_workflow 負責紅")
    doc = yaml.safe_load(_text(path))
    perms = doc.get("permissions")
    assert perms is not None, (
        "%s 沒有頂層 permissions —— 那表示用 repo 預設,"
        "而預設不在這個檔案裡、改了不會有 diff。" % os.path.basename(path))
    assert perms == {"contents": "read"}, (
        "%s 的 permissions 是 %r,要求恰好是 {'contents': 'read'}"
        % (os.path.basename(path), perms))


@pytest.mark.parametrize("path", workflow_files() or [None])
def test_checkout_fetches_the_whole_history(path):
    """R6 要 `git cat-file -e <go-live>:<path>`,而 go-live 是一個**舊** commit。

    `actions/checkout` 預設 `fetch-depth: 1`(只抓最新一筆)——
    那棵樹在 CI 的 repo 裡根本不存在,於是**九個條目全部判違規**,
    而 R6 的訊息會說它們「是新檔案、後來手加的」。

    **fail-closed 的方向是對的,診斷是錯的**:R6 分不出
    「路徑不在那棵樹裡」與「那棵樹不在這個 repo 裡」。
    在任何淺層 clone 上,R6 會擋下每一次 commit 並給出錯誤的理由。

    這條測試守的是**環境前提**,不是 R6 的邏輯 —— 邏輯那半另有登記。
    本機永遠測不出這個(本機的 clone 一直是完整的),所以它只能寫成
    對設定檔的斷言。
    """
    if path is None:
        pytest.skip("沒有 workflow — 由 test_there_is_at_least_one_workflow 負責紅")
    doc = yaml.safe_load(_text(path))
    depths = []
    for job in (doc.get("jobs") or {}).values():
        for step in (job.get("steps") or []):
            uses = step.get("uses", "")
            if "actions/checkout@" in uses:
                depths.append((step.get("with") or {}).get("fetch-depth"))
    assert depths, "%s 沒有 actions/checkout 步驟 —— 這條測試沒有在測任何東西" % (
        os.path.basename(path))
    bad = [d for d in depths if d != 0]
    assert not bad, (
        "%s 的 checkout 沒有 fetch-depth: 0(取到 %r)。\n"
        "     預設是淺層(只抓最新一筆),而 R6 要查 go-live 那棵舊樹。"
        % (os.path.basename(path), bad))


SHA40 = re.compile(r"^[0-9a-f]{40}$")


@pytest.mark.parametrize("path", workflow_files() or [None])
def test_every_third_party_action_is_pinned_to_a_sha(path):
    """條件 4:第三方 action 一律釘 40 位 commit sha,不釘標籤。

    `actions/checkout@v4` 這種標籤**可以被移動** —— 同一個名字今天與下個月
    可能是不同的程式碼,而且不會有通知。與 provenance 同一原理:
    **記住那一組確切的位元組,不是記住一個會漂移的名字。**

    `./` 開頭(repo 內的 action)豁免:它的內容就在這個 repo 裡,
    隨 commit 一起被固定,沒有第二份可以漂。
    """
    if path is None:
        pytest.skip("沒有 workflow — 由 test_there_is_at_least_one_workflow 負責紅")
    doc = yaml.safe_load(_text(path))
    unpinned = []
    for u in _walk_uses(doc):
        if u.startswith("./"):
            continue
        ref = u.rsplit("@", 1)[-1] if "@" in u else ""
        if not SHA40.match(ref):
            unpinned.append(u)
    assert not unpinned, (
        "%s 有沒釘 sha 的 action:%s\n"
        "     標籤會被移動,而移動不會通知任何人。" % (os.path.basename(path), unpinned))
