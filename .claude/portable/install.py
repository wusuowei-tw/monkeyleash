# -*- coding: utf-8 -*-
"""把六站閘門裝進另一個 repo。

用法:python .claude/portable/install.py <目標目錄>
      python .claude/portable/install.py <目標目錄> --approve-inventory <64 碼 hex>
      python .claude/portable/install.py --rehook <已安裝的目標目錄>

**兩次執行,中間由人核准(票 169)。** 第一次只產名冊候選、印出候選 hash,以結束碼 3 結束,
目標零寫入;由人檢視候選並親自核准那一個 hash,第二次帶 `--approve-inventory <hash>` 重跑,
依現況重算一致才寫入。hash 只能逐字來自人的明示核准,agent 不得自行推導或代填。
已安裝的目標只走 `--rehook`,不得重跑完整安裝(票 156 D12)。

**單一路徑,零分支。** 全新專案不是另一種情境,它只是「既有原始碼數為零」的特例:
同一條路徑跑完會產出一份空的豁免清單。為空 repo 開第二條分支的話,
較少被走到的那條就是下一個 F-009(規則存在但沒被走過)。

核准之後,安裝**一律建立 commit**:go-live sha 必須指向一個真的存在的 commit,
而安裝框架本來就是一次變更 —— 既有專案也該有那個 commit,空 repo 只是它的第一個。

裝 skill 是**安裝的一部分**,不是前置條件。當前置條件的話,漏做時 R4/R5
靜默不可驗 —— 跟權威層那個缺口同型。

本檔在票 01 宣告為 Untested by decision(接縫 S5):
它由空 repo 的端到端實測完整涵蓋,不另寫單元測試。
"""

import io
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import claude_md  # noqa: E402
import manifest  # noqa: E402  (同目錄,安裝器與標記表是一組的)


def _out(text):
    """輸出走 **utf-8 位元組**,不走 `print`(票 62 家族第四支,票 115)。

    `print` 用主控台的編碼,而 Windows 的 cp950 編不出很多東西 —— 那不是亂碼,
    是 `UnicodeEncodeError` 未捕捉、**行程當場死掉**。

    **這一支特別要緊**:安裝完成報告是**下游第一次見到這個框架的畫面**。
    它在 cp950 主控台上死掉的樣子,是一個看起來像「裝壞了」的 traceback ——
    而實際上 repo 已經裝好了,死的只是最後那段報告。
    **看不懂的第一印象比看不懂的擋下訊息更貴**:後者至少還有 pre-commit 擋著。

    **寫法與 `verify_gates.py` / `g1_verify.py` / `shadow_review.py` 一致**,
    不是新發明的。`flush` 的理由:本檔的輸出全部走這裡,而
    `sys.stdout.buffer` 是二進位層 —— 不先 flush 文字層的話,
    萬一將來有人加回一個 `print`,兩層的輸出會交錯。

    ## ⚠ 刻意**不做** `try/except` 退回 `stream.write`

    `user_layer._write` 是那樣寫的,而**那條退路在 cp950 上照樣會炸** ——
    它沒有救到任何東西,只是把「為什麼炸」藏起來。
    **票 62 要消掉的正是「炸掉時看不出來」,而 fail-soft 就是那個東西本身。**
    (票 115 裁一,2026-09-09。)
    """
    sys.stdout.flush()
    sys.stdout.buffer.write((text + "\n").encode("utf-8"))
    sys.stdout.buffer.flush()


HOOK = ("#!/bin/sh\n"
        "# 六站閘門 — 洩漏偵測 + 權威判定。邏輯不在這裡,只呼叫共用腳本。\n"
        "# 洩漏偵測在前:秘密一旦進了歷史,擋下 commit 是唯一便宜的時點。\n"
        "# 之前只接 gate.py —— 裝出來的 repo 對真 key 的 commit 完全放行(負控實測),\n"
        "# 而 F-055 說的就是洩漏 hook 不會自己跟過去。接線是安裝器的責任。\n"
        "# 直譯器只經 .claude/bin/gatepy 取 .venv-gates(票 156);不退回 .venv 或 PATH 上的 python。\n"
        'root="$(git rev-parse --show-toplevel)"\n'
        'sh "$root/.claude/bin/gatepy" "$root/.claude/portable/leak_scan.py" --staged || exit 1\n'
        'exec sh "$root/.claude/bin/gatepy" "$root/.claude/hooks/gate.py" --pre-commit\n')

# 已知的 agent-gates HOOK 範本(票 156 第三節第 7 條第 6 點):版本 ID → sha256(LF 標準形,UTF-8)。
# `--rehook` 只認這張表裡的內容(比對前唯一允許的正規化是 CRLF→LF,G2)。
# fixture 在 tests/fixtures/hooks/;表與範本不漂移由 tests/test_install.py 守。
KNOWN_HOOKS = {
    "hook-v1-bare-python": "eb6ee62cfb31803c26c3547822ba76b8104d111f759a960774d425a6b1f1c807",
    "hook-v2-gatepy": "091c0290f0e9c43441678f3c33391a31d8260c84764c9c86270e688fa1ccd83d",
}
VENV_GATES = ".venv-gates"

# 票 169:新下游安裝的 extension 名冊前置核准(D1～D4)。
# 候選檔根目錄是**模組屬性、呼叫時才讀**(測試換成 tmp);拋棄式 repo 用它自己的候選根目錄(D4 例外 / E3)。
CANDIDATES_DIR = os.path.join(SRC_ROOT, ".dev", "install-candidates")
_REAL_CANDIDATES_DIR = CANDIDATES_DIR      # E3 的比對基準:不隨測試替換而移動
CANDIDATE_SCHEMA = "monkeyleash.install-candidate"
CANDIDATE_VERSION = 1
CANDIDATE_NOTE = u"install-candidate(票 169)"
# 票 171:承接上游 HEAD 名冊的 contract 項目時一律用這個 note(不抄上游 note)。
CARRIED_CONTRACT_NOTE = u"install-candidate(票 171 承接上游已提交名冊的 contract 項目)"
UPSTREAM_INVENTORY_REL = ".agents/extension-inventory.json"
UNBORN = "UNBORN"                          # UNBORN 裁決:尚無 commit 的 target_head(全大寫、逐字)
EXIT_INVENTORY_PENDING = 3                 # 候選已產生、尚未核准(下游零寫入)
EXIT_INVENTORY_MISMATCH = 4                # 核准 hash 與現況不一致(D3;下游零寫入)
EXIT_CANDIDATE_CORRUPT = 5                 # 既有候選檔內容 hash 與檔名不符(D1;下游零寫入、原檔不覆寫)
EXIT_REVERIFY_ROLLED_BACK = 6              # 第一個 commit 前重驗不一致、已自動復原並驗證(新裁決 3／4)
EXIT_ROLLBACK_FAILED = 7                   # 自動復原失敗或復原後驗證不一致(R6:hard fail,未恢復)
_HEX64 = re.compile(r"\A[0-9a-f]{64}\Z")
_HEX40 = re.compile(r"\A[0-9a-f]{40}\Z")

# 安裝出的 repo 的 .gitignore 必帶兩組:框架垃圾 + 秘密檔。
# 秘密那組是預設值問題:框架裝好的新專案,第一個放進去的秘密(.env)
# 原本不被任何規則守著 —— 不是使用者疏忽,是安裝器沒給預設。
# `.venv-gates/`(票 156 G4):閘門專用 venv,新下游由 setup_gates_env 先登記在 .git/info/exclude,
# 正式安裝時由這裡永久寫進 .gitignore。
GITIGNORE_FRAMEWORK = ("__pycache__/", ".cache/", "/.claude/skills/", "/skills/", ".venv-gates/")
# 憑證副檔名用組裝而不寫死 —— 寫死的話 leak_scan 的通用 pattern 會擋住
# 本檔自己的 commit(防禦清單長得像洩漏)。與 tests/test_leak_scan.py 同一手法。
GITIGNORE_SECRETS = ((".env", ".env.*", "!.env.example", "credentials.json",
                      "service-account*.json")
                     + tuple("*." + ext for ext in ("pem", "pfx", "p12", "key")))


def run(args, cwd, check=True):
    p = subprocess.run(args, cwd=cwd, capture_output=True)
    out = (p.stdout + p.stderr).decode("utf-8", "replace")
    if check and p.returncode != 0:
        raise SystemExit("指令失敗(%s):%s\n%s" % (p.returncode, " ".join(args), out))
    return p.returncode, out


def git_paths(args, cwd, check=True):
    """凡是**拿 git 輸出當路徑**的地方都走這裡。`-z`(NUL 分隔),不是 splitlines。

    git 對非 ASCII 檔名預設回傳 C-quoted 路徑(`"\\345\\217\\260….py"`)。
    在這支的後果是**靜默漏帶**:中文檔名的檔案列不出來 → 不被複製到目標 repo,
    而少帶正是 F-030/F-031 那一族最難發現的失效。ls-tree 那邊還會把壞路徑寫進
    legacy 清單,R6 事後拿它去 `git cat-file` 查證必然失敗。

    不用 `core.quotePath=false`:它只解引號,檔名含換行或引號仍有歧義。
    另外走 stdout,不併 stderr —— 併起來的話警告訊息會被當成路徑。
    """
    p = subprocess.run(["git"] + args + ["-z"], cwd=cwd, capture_output=True)
    if check and p.returncode != 0:
        raise SystemExit("指令失敗(%s):git %s\n%s"
                         % (p.returncode, " ".join(args),
                            (p.stdout + p.stderr).decode("utf-8", "replace")))
    return [x for x in p.stdout.decode("utf-8", "replace").split("\0") if x.strip()]


def source_files():
    """來源檔案集合 —— **含未追蹤但沒被 ignore 的檔案**。

    只取 `git ls-files` 的話,還沒 commit 的框架檔會**靜默漏帶**:
    安裝照樣成功、閘門照樣擋、輸出全綠,而裝出來的框架少了安裝器本身。
    實際發生過(第一次端到端就中):manifest.py / install.py / test_manifest.py
    三個都還沒進版控,於是新 repo 拿到一套裝不動下一個專案的框架。

    往「帶」的方向倒:多帶進來的暫存檔是吵鬧的(看得見、刪得掉),
    漏帶是靜默的。未追蹤的會在安裝輸出裡單獨列出來。

    **`--exclude-standard` 把 ignored 也排除了 —— 那是同一個病的另一半。**
    上面那段描述了「還沒 commit 的框架檔會靜默漏帶」,修好 untracked 那半就停了。
    量化實測:`.claude/` 被 gitignore → 框架檔完全不進列舉 →
    裝出**沒有閘門的 repo** → `verify_gates` 崩潰,而安裝本身成功且安靜(票 18)。
    """
    t = git_paths(["ls-files"], SRC_ROOT)
    u = git_paths(["ls-files", "--others", "--exclude-standard"], SRC_ROOT)
    return t + u + ignored_framework_files(), u


def ignored_framework_files():
    """被 `.gitignore` 蓋住、但**落在框架範圍內**的檔案。

    契約是「**本來會帶、卻被 gitignore 藏起來的**」,所以兩道過濾都要:

      `in_scope()` 為假   -> 不是框架的東西(鏡像 `.claude/skills/`、`skills/`)
      標記是 `skip`       -> 框架範圍內但本來就不帶(`__pycache__`)

    只過 `in_scope` 不夠:`__pycache__` 在 `.claude/hooks/` 底下,`in_scope` 為真,
    最後會被標記表擋在複製之外 —— 但它會混進**廣播清單**裡。
    每次安裝都報一串位元碼檔案,那是噪音,而噪音會訓練人忽略那句提醒(F-031)。
    出聲的東西必須全部值得看。

    「被 gitignore 蓋住的框架檔」本身是個怪狀態,所以**不只帶,還要出聲**
    (呼叫端會列出來)—— 少了那句,下一個人不會知道他的 `.gitignore`
    正在對抗安裝器。
    """
    ig = git_paths(["ls-files", "--others", "--ignored", "--exclude-standard"],
                   SRC_ROOT)
    return [p for p in ig
            if not is_bytecode(p) and manifest.in_scope(p) and manifest.mark_for(p) != "skip"]


_BYTECODE_DIR = "__pycache__"
_BYTECODE_EXTS = (".pyc", ".pyo")


def is_bytecode(rel_path):
    """票 172 D1:位元碼的唯一判定 —— 任一段恰為 `__pycache__`,或副檔名為 `.pyc`／`.pyo`(不分大小寫)。

    不靠 manifest 標記:標記表只能逐目錄寫 skip,而 copy 目錄與巢狀深度是開放集合,
    位元碼的標誌(目錄名與兩個副檔名)才是封閉的那一邊。
    """
    parts = rel_path.split("/")
    if _BYTECODE_DIR in parts:
        return True
    return os.path.splitext(parts[-1])[1].lower() in _BYTECODE_EXTS


def classify(paths):
    """逐檔分類。回傳 (要複製的, 各標記的清單, 靠預設過關的)。

    票 172 D2:位元碼先排除,不進任何桶(因此不進 copy 桶、journal、copy_into)。
    """
    paths = [p for p in paths if not is_bytecode(p)]
    buckets = {m: [] for m in manifest.MARKS}
    for p in paths:
        if manifest.in_scope(p):
            buckets[manifest.mark_for(p)].append(p)
    # 「在範圍內但沒標記」在前綴範圍下由構造為空 —— 真正會漏帶的是鄰居那一群
    return buckets, manifest.uncovered_neighbours(paths)


def copy_into(target, paths):
    for p in paths:
        dst = os.path.join(target, p.replace("/", os.sep))
        os.makedirs(os.path.dirname(dst) or target, exist_ok=True)
        shutil.copy2(os.path.join(SRC_ROOT, p.replace("/", os.sep)), dst)


def build_mirrors(target):
    """鏡像目錄。形態由環境決定(symlink / 硬連結 / 實體複製都出現過),
    這裡用實體複製 —— 它在任何檔案系統上都成立,而 R4 的實體目錄分支吃得下。"""
    canon = os.path.join(target, ".agents", "skills")
    if not os.path.isdir(canon):
        return []
    made = []
    for m in (os.path.join(target, ".claude", "skills"), os.path.join(target, "skills")):
        if os.path.exists(m):
            shutil.rmtree(m)
        shutil.copytree(canon, m)
        made.append(os.path.relpath(m, target).replace("\\", "/"))
    return made


def generate_state(target):
    """.dev/ 是這個 repo 的狀態與證據,不照抄。空證據是誠實的起點。"""
    dev = os.path.join(target, ".dev")
    os.makedirs(dev, exist_ok=True)
    io.open(os.path.join(dev, "pipeline.json"), "w", encoding="utf-8", newline="\n").write(
        json.dumps({"current_stage": "idle", "feature": None,
                    "ticket_id": None, "updated": ""}, ensure_ascii=False, indent=2) + "\n")
    for name in ("test-runs.jsonl", "gate-exemptions.jsonl"):
        io.open(os.path.join(dev, name), "w", encoding="utf-8", newline="\n").write("")

    # 框架自己會產生的垃圾。不寫這個的話,安裝當下跑驗證產生的 __pycache__
    # 會被第一個 commit 收進去 —— 不是複製過去的,是裝好之後自己長出來的。
    # 用附加不覆寫:目標可能已經有自己的 .gitignore。
    # CLAUDE.md 只帶框架段。專案段留在原地 —— 把某個專案的規矩裝進另一個專案,
    # agent 會照錯的規矩工作,而**那不會報錯**。汙染方向比乾淨要緊。
    src = os.path.join(SRC_ROOT, "CLAUDE.md")
    if os.path.exists(src):
        io.open(os.path.join(target, "CLAUDE.md"), "w",
                encoding="utf-8", newline="\n").write(
            claude_md.render_for_new_repo(io.open(src, encoding="utf-8").read()))

    ignore = os.path.join(target, ".gitignore")
    have = io.open(ignore, encoding="utf-8").read() if os.path.exists(ignore) else ""
    # **查重比對的是【行】,不是子字串**(票 78)。
    #
    # 舊寫法是 `p not in have`,而 `have` 是整檔內容 —— 於是檔裡任何位置出現
    # 那串字元(例如一行註解「keep .env.example」)就當成「已經有了」,
    # **真的防護行不補,而且完全靜默**。裝出來的 repo 第一個放進去的秘密沒人守,
    # 正是 F-062 要防的方向。
    #
    # **要問的是「這個 pattern 行存不存在」,子字串答的是「這串字元出現過沒有」
    # —— 問錯對象。**
    #
    # 失效方向只有一邊:子字串**只會過度抑制**(該補的不補),
    # 不會過度追加 —— 所以改成行精確之後,「不重複追加」那個本意不受影響,
    # 而那件事有自己的反控釘著(`tests/test_install.py` 的 ② )。
    have_lines = set(l.strip() for l in have.splitlines())
    # **前導斜線是必要的,不是風格。** 寫成 `skills/` 的話 gitignore 會在
    # **任何深度**比對同名目錄 —— 於是 `.agents/skills/`(正典)也被排除,
    # 而 git 對 ignored 檔案依定義是靜默的。後果不是少幾個檔案:
    # 正典沒進版控 → 下一次從這個 repo 安裝時帶不走 skills → R5 在目標 repo 失敗。
    # 淨室測試抓到的,而且要「安裝出來的 repo 再安裝一次」才會現形。
    add = [p for p in GITIGNORE_FRAMEWORK if p not in have_lines]
    if add:
        with io.open(ignore, "a", encoding="utf-8", newline="\n") as f:
            f.write(("\n" if have and not have.endswith("\n") else "")
                    + "# 六站閘門會產生的東西(鏡像目錄由 skills 工具重建)\n"
                    + "\n".join(add) + "\n")
        have = io.open(ignore, encoding="utf-8").read()
        have_lines = set(l.strip() for l in have.splitlines())
    secrets = [p for p in GITIGNORE_SECRETS if p not in have_lines]
    if secrets:
        with io.open(ignore, "a", encoding="utf-8", newline="\n") as f:
            f.write(("\n" if have and not have.endswith("\n") else "")
                    + "# 秘密與憑證 —— 永不進版控(安裝器預設,見 F-062)\n"
                    + "\n".join(secrets) + "\n")


def install_hook(target):
    """**不進版控**的那一半:`.git/hooks/pre-commit`。

    仍然要寫,而且是甲的裁決 C 的一半(票 58):
    `authoritative_layer()` 沒設 `core.hooksPath` 時查的就是這裡,
    停寫它而又不設 config 的話,`main()` 的強制驗證會**假失敗**。
    """
    hooks = os.path.join(target, ".git", "hooks")
    os.makedirs(hooks, exist_ok=True)
    path = os.path.join(hooks, "pre-commit")
    io.open(path, "w", encoding="utf-8", newline="\n").write(HOOK)
    try:
        os.chmod(path, 0o755)
    except Exception:
        pass
    return path


PORTABLE_HOOK_DIR = ".githooks"
PORTABLE_HOOK_REL = PORTABLE_HOOK_DIR + "/pre-commit"


def install_portable_layer(target):
    """**進版控**的那一半:`.githooks/pre-commit` + `bootstrap.sh`(票 58 / F-065:1115)。

    在此之前裝出來的 repo **沒有 `.githooks/`**,於是 `bootstrap.sh` 宣稱的那條路
    (「hook 進版控,靠一行 config 指過去」)在目標 repo 上不存在 ——
    那一步實際是「**先手工造一個 hook**,再跑一行 config」,
    而 `F-065:1118` 逐字寫著「現在是人工補的,**下一個安裝的人不會知道要補**」。

    **⚠ 本函式不關掉 ADR 0007 那個缺口。** `ADR 0007:19-22` 已經寫著
    `core.hooksPath` 只是把「複製一個檔案」換成「跑一行 config」,**沒有消除那一步**;
    `:33` 寫著三個偵測點都碰不到「clone 下來直接手動 commit 的人」——
    **本函式對他零影響**。受益的是**會跑 `bootstrap.sh` 的人**:
    在他身上,`ADR 0007:20` 那句第一次成為真的。

    **`bootstrap.sh` 從來源檔讀,不在本檔再寫一份常數。** 兩份就是同一個事實
    有兩個可寫的位置(`legacy-no-redlight.txt:12` 的同一條規矩),
    而下一次改 bootstrap 會漏掉其中一份 —— 漏掉的正是出貨給下游的那一份。
    形式抄 `generate_manifest()`:它同樣讀來源的檔,理由同樣是單一來源。

    **讀不到來源就丟例外,不寫半個。** 產一個沒有 `bootstrap.sh` 的
    `.githooks/` 等於把「指過去的目錄是空的」那個狀態裝進新 repo,
    而那正是 bootstrap 第一道 fail-closed 在防的東西。
    """
    d = os.path.join(target, PORTABLE_HOOK_DIR)
    os.makedirs(d, exist_ok=True)
    hook = os.path.join(d, "pre-commit")
    io.open(hook, "w", encoding="utf-8", newline="\n").write(HOOK)

    src = os.path.join(SRC_ROOT, "bootstrap.sh")
    if not os.path.exists(src):
        raise SystemExit(
            "[安裝/fail-closed] 來源沒有 bootstrap.sh(%s)—— 拒絕只產一半。\n"
            "     只產 .githooks/ 而不產 bootstrap.sh,等於把「指過去的目錄\n"
            "     不知道怎麼啟用」裝進新 repo,而那是靜默的。" % src)
    dst = os.path.join(target, "bootstrap.sh")
    io.open(dst, "w", encoding="utf-8", newline="\n").write(
        io.open(src, encoding="utf-8").read())
    return hook, dst


def stage_hook_executable(target):
    """把 `.githooks/pre-commit` 的 **index mode** 設成 `100755`。

    **`os.chmod` 不夠,兩層都失效:**

      檔案系統   Windows 沒有 POSIX 執行位元,`os.chmod(0o755)` 實質是 no-op
      git index  `filemode=false` 時 git 一律把新檔記成 `100644`,**不看檔案系統**

    而 **Linux 上 git 不執行沒有執行位元的 hook,並且不出聲** ——
    所以這一步漏掉的話,裝出來的 repo 在 CI(Linux)上是
    **靜默沒有權威層**的,而 `authoritative_layer()` 只讀內容不看 mode,
    它會回報「已安裝」(票 58 D0:上游自己就量到 `100644`)。

    **必須在 `git add` 之後呼叫** —— `update-index --chmod` 改的是既有的
    index 條目,檔案還沒進 index 時它沒有對象可改。
    """
    run(["git", "update-index", "--chmod=+x", "--", PORTABLE_HOOK_REL], target)


def generate_manifest(target):
    """把標記表產進目標 repo。

    **它自己標 `ask`,所以不在 copy 桶裡** —— 沒有這一步,裝出來的 repo
    一張標記表都沒有:`_table()` 回空 → 每個檔案退化成預設 `copy`、
    `in_scope` 跟著失真。而那個狀態是**靜默**的:安裝成功、hook 裝好、
    大部分測試照樣綠,只有兩條會紅,而且紅得像是那兩條測試自己的問題
    (淨室安裝實測,2026-08-13)。

    產出的內容就是來源那一份:表裡的框架列是**框架的事實**,跟著走才對。
    來源 host repo 自己的 `skip` 列一起帶過去是**刻意**的 ——
    它們指向新 repo 不存在的檔案,永遠不會命中,而代價不對稱:
    多帶一列是吵鬧的(看得到、可以刪),漏帶一列是靜默的。

    新 repo 自己的檔案由人補:`tests/` 底下每個檔案都要有標記,缺一個就紅。
    那條紅燈是**要**它紅 —— 分類是決定,不是安裝器推導得出來的事實。
    """
    src = os.path.join(SRC_ROOT, ".agents", "portable-manifest.txt")
    dst = os.path.join(target, ".agents", "portable-manifest.txt")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    body = io.open(src, encoding="utf-8-sig").read()
    with io.open(dst, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)
        if not body.endswith("\n"):
            f.write("\n")
        f.write(
            "\n# ── 本 repo 自己的檔案 ────────────────────────────────────\n"
            "# 安裝器產到框架列為止,底下由人補。\n"
            "# tests/ 底下每個檔案都要有標記,缺一個就紅 —— 那條紅燈是要它紅:\n"
            "# 「這個測試屬於框架還是專案」沒有任何機器答得出來。\n")
    return dst


def generate_legacy_list(target, go_live):
    """既有 .py 的紅燈豁免清單 —— 在目標 repo 重新產生,絕不照抄。

    照抄的話清單裡是**來源 repo 的路徑**,拿目標 repo 的 sha 去驗每一筆都不在樹裡,
    R6 全數判違規 —— 而且是在安裝之後才炸,看起來像框架壞了。
    """
    sys.path.insert(0, os.path.join(target, ".claude", "hooks"))
    for mod in ("gate",):
        sys.modules.pop(mod, None)
    spec_path = os.path.join(target, ".claude", "hooks", "gate.py")
    import importlib.util
    spec = importlib.util.spec_from_file_location("target_gate", spec_path)
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)

    files = sorted(p for p in git_paths(["ls-tree", "-r", "--name-only", go_live], target)
                   if p.endswith(".py") and g.is_source_path(p))
    dst = os.path.join(target, ".agents", "legacy-no-redlight.txt")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with io.open(dst, "w", encoding="utf-8", newline="\n") as f:
        f.write("# go-live: %s\n" % go_live)
        f.write("# 機制上線前就存在的 .py —— 豁免 R3 **整條**(兩半:紅燈紀錄 + 測試檔存在)。\n")
        f.write("# 生成的,不是手寫的。只減不增(R6 驗每一筆都在上面那個 commit 的樹裡)。\n")
        for p in files:
            f.write(p + "\n")
    return files


POLICY_TEMPLATE = ".agents/evidence-policy.template.json"


def _target_redlight(target):
    """目標 repo 的 `.claude/hooks/redlight.py`(剛複製過去的那一份)。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "target_redlight", os.path.join(target, ".claude", "hooks", "redlight.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_policy_template(target):
    """evidence policy 範本 —— 寫到**非 canonical** 路徑(票 145〈四十八〉48.1 第 6 點 A)。

    內容取自目標 repo 的 redlight `policy_template()`:框架能力邊界常數的完整列舉,**不是本機觀察值**
    (不自動信任首次觀察值)。範本會隨安裝 commit 一起提交,但它不在 canonical path
    (`redlight.POLICY_FILE`),**永遠不會被當成 authority**;canonical 那一份只有人放上去並 commit 才存在。
    不另放範本來源檔:常數只有 redlight 那一份,範本由它產生,兩者不會漂移。
    """
    rl = _target_redlight(target)
    dst = os.path.join(target, *POLICY_TEMPLATE.split("/"))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with io.open(dst, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rl.policy_template(), ensure_ascii=False, indent=2) + "\n")
    return dst, rl.POLICY_FILE


def _settings_hook_commands(target):
    """目標 `.claude/settings.json` 的 hooks 內全部 command 字串(出現順序、去重)。讀不到 / 不是 JSON ⇒ SystemExit。"""
    path = os.path.join(target, ".claude", "settings.json")
    try:
        with io.open(path, encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, ValueError) as e:
        raise SystemExit("讀不到目標的 .claude/settings.json,產生不了 extension allowlist:%s" % type(e).__name__)
    out = []

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "command" and isinstance(v, str):
                    if v not in out:
                        out.append(v)
                else:
                    walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(doc.get("hooks") if isinstance(doc, dict) else None)
    return out


def write_extension_policy(target, approved=None):
    """票 146 G-2:安裝器的最小 extension policy —— 空 inventory + 只授權安裝器寫入的 hook command。

    **這是安裝預設,不是核准過的觀測快照**:不登記任何使用者擴充(dev-mods / skills / commands / synced / .mcp.json)。
    兩份都不存在 ⇒ 產生,回 `created=True`;兩份都存在且合法 ⇒ 保留不覆寫,`created=False`;
    只有一份、任一不合法或 JSON 解析失敗 ⇒ SystemExit,**之前不寫任何檔**。
    常數與驗證函式取自目標 repo 的 redlight —— 與判定器是同一份,不在這裡另寫一份。

    `approved`(票 169):安裝前置核准過的 `(allowlist, inventory)`。給了 ⇒ 目標不得已有任何一份 policy,
    寫入的就是核准的內容(取代空名冊預設);hook command 必須與複製過去的 settings.json 一致,否則停止。
    """
    rl = _target_redlight(target)
    allow_path = os.path.join(target, *rl.EXT_ALLOWLIST_FILE.split("/"))
    inv_path = os.path.join(target, *rl.EXT_INVENTORY_FILE.split("/"))
    present = [os.path.lexists(p) for p in (allow_path, inv_path)]
    if approved is not None and any(present):
        raise SystemExit("核准的 extension policy 不覆蓋目標既有的 policy 檔 —— 安裝停止。")
    if all(present):
        docs = []
        for rel, p in ((rl.EXT_ALLOWLIST_FILE, allow_path), (rl.EXT_INVENTORY_FILE, inv_path)):
            try:
                with io.open(p, encoding="utf-8") as f:
                    docs.append(json.load(f))
            except (OSError, ValueError) as e:
                raise SystemExit("既有的 %s 讀不到或不是 JSON(%s)—— 不覆寫,安裝停止。" % (rel, type(e).__name__))
        bad = [rel for rel, ok in ((rl.EXT_ALLOWLIST_FILE, rl._extension_allowlist_ok(docs[0])),
                                   (rl.EXT_INVENTORY_FILE, rl._extension_inventory_ok(docs[1]))) if not ok]
        if bad:
            raise SystemExit("既有的 extension policy 不合法:%s —— 不覆寫,安裝停止。" % "、".join(bad))
        return allow_path, inv_path, False
    if any(present):
        have = rl.EXT_ALLOWLIST_FILE if present[0] else rl.EXT_INVENTORY_FILE
        raise SystemExit("extension policy 只有一份(%s)—— 不補另一份、不覆寫,安裝停止。" % have)
    hooks = _settings_hook_commands(target)
    if approved is not None:
        allow, inv = json.loads(json.dumps(approved[0])), json.loads(json.dumps(approved[1]))
        if allow.get("project_settings_hook_commands") != hooks:
            raise SystemExit("核准的 hook command 與目標 .claude/settings.json 不一致 —— 安裝停止。")
    else:
        allow = {}
        for k in rl.EXT_ALLOWLIST_FIELDS:
            allow[k] = []
        allow["schema"] = rl.EXT_ALLOWLIST_SCHEMA
        allow["version"] = rl.EXT_ALLOWLIST_VERSION
        allow["project_settings_hook_commands"] = hooks
        inv = {"schema": rl.EXT_INVENTORY_SCHEMA, "version": rl.EXT_INVENTORY_VERSION, "entries": []}
    for k in rl.EXT_INVENTORY_FIELDS:
        if k not in inv:
            raise SystemExit("目標 redlight 的 EXT_INVENTORY_FIELDS 多出未知欄位 %r —— 產生不了合法 inventory" % k)
    if not (rl._extension_allowlist_ok(allow) and rl._extension_inventory_ok(inv)):
        raise SystemExit("產生的最小 extension policy 沒有通過目標 redlight 的驗證 —— 安裝停止。")
    for p, doc in ((allow_path, allow), (inv_path, inv)):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with io.open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
    return allow_path, inv_path, True


def write_decisions_pending(target, buckets, carried_untracked, unmarked, policy_file=None,
                           extension_policy=None, extension_note=None):
    """把需要人決定的項目**寫成檔案**,不只印終端機。

    印出來沒人看等於沒列(F-036 的同一個病:訊號不落地就等於沒有訊號)。
    寫成 docs/decisions-pending.md —— 人回頭找得到,也進得了版控、能被 review。
    沒有任何待決項目時回 None(不留空檔案佔位)。

    `policy_file`(canonical evidence policy 路徑)給了 ⇒ 一律加一項「evidence policy 未初始化」
    (票 145〈四十八〉48.1 第 6 點 A):安裝後 canonical policy 必然不存在,在人建立之前任何 run 都退不了紅。
    """
    sections = []
    if policy_file:
        sections.append(("evidence policy 未初始化 —— 在建立之前,任何測試執行都不會讓紅燈退休",
                         [policy_file],
                         "審閱 `%s`(框架能力邊界的完整列舉)→ 依本 repo 需要收窄;"
                         "`committed_overrides` 必須等於本 repo 已提交設定檔 addopts 帶來的 override"
                         "(例:`--strict-markers` ⇒ `strict_markers=true`)→ 存成 `%s` → commit。"
                         "**這一步只有人做**;status 的 `evidence policy:` 行會顯示目前狀態。"
                         % (POLICY_TEMPLATE, policy_file)))
    if extension_policy:
        # 票 146 G-2:安裝來源記在這裡與安裝 commit 訊息,不在 policy 檔加頂層 note(五處閉合裁決)。
        sections.append(("extension policy 是安裝器產生的最小版 —— 不是核准過的觀測快照",
                         list(extension_policy),
                         extension_note or
                         "由安裝器產生：空 inventory + 安裝器寫入的 hook command；未登記任何使用者擴充；"
                         "這不是核准過的觀測快照。R10 在 pre-commit 以這兩份的 HEAD 版本判定;"
                         "使用者層(`~/.claude`)有任何未登記的入口,commit 就會被擋。"
                         "要登記實際擴充,由人審閱後只 stage 這兩份 policy 提交(policy-only 通道)。"))
    if buckets.get("ask"):
        sections.append(("需要你決定帶不帶(標記為 ask,安裝時沒有帶過去)",
                         buckets["ask"],
                         "這些檔案混著框架與專案兩種東西。看過內容後,"
                         "要嘛手動複製過來、要嘛確認不需要。"))
    if carried_untracked:
        sections.append(("帶過去了但來源 repo 還沒進版控 —— 確認不是暫存檔",
                         carried_untracked,
                         "來源是未追蹤檔,可能是還沒 commit 的框架檔,也可能是暫存物。"))
    if unmarked:
        sections.append(("跟框架檔住在同一個目錄、卻沒被帶過去 —— 確認不是漏的",
                         unmarked,
                         "少帶是靜默的(F-030/F-031)。逐一確認這些是專案自己的、不是漏掉的框架檔。"))
    if not sections:
        return None

    path = os.path.join(target, "docs", "decisions-pending.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lines = ["# 安裝待決定項目\n",
             "由 install.py 產生。**這是這些決定的落地處,不是終端機。**",
             "處理完一項就把它從這裡刪掉;清空了就代表安裝的人工部分做完了。\n"]
    for title, items, note in sections:
        lines.append("## %s\n" % title)
        lines.append("%s\n" % note)
        for it in sorted(items):
            lines.append("- [ ] `%s`" % it)
        lines.append("")
    io.open(path, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    return path


def target_venv_python(target):
    """`<target>/.venv-gates` 的直譯器(Windows 版面優先,其次 POSIX)。沒有回 None —— **不找別的**。"""
    for rel in (("Scripts", "python.exe"), ("bin", "python")):
        p = os.path.join(target, VENV_GATES, *rel)
        if os.path.isfile(p):
            return p
    return None


def _run_target_identity(target):
    """事前檢查唯一的子行程入口(票 156 D-10 / F0c (b))。回 `(ok, 輸出)`。

    用 **target 自己的** `.venv-gates` 直譯器,執行**上游**(本檔所在 repo)的 `runtime_identity.py`,
    明確帶 `--repo <target> --profile downstream`。不用本行程的 `sys.executable`,
    不另寫第二套環境驗證邏輯 —— 身分判定只有 runtime_identity 那一份。
    """
    py = target_venv_python(target)
    if py is None:
        return False, "沒有 %s 的直譯器" % os.path.join(target, VENV_GATES)
    argv = [py, os.path.join(SRC_ROOT, ".claude", "portable", "runtime_identity.py"),
            "--repo", target, "--profile", "downstream"]
    p = subprocess.run(argv, capture_output=True)
    out = ((p.stdout or b"") + (p.stderr or b"")).decode("utf-8", "replace")
    return p.returncode == 0, out


def precheck(target):
    """`main()` 在**任何寫入之前**的檢查(G4)。不合法就結束,target 一個位元組都不動。

    target 必須已存在(`os.makedirs(target)` 本身就是寫入,所以排在它之前)、
    `.venv-gates` 的直譯器存在、身分檢查與 downstream(core)profile 都合法。
    新下游的順序是:從上游執行 `setup_gates_env.py <target>` → 驗身分 → 才執行本檔。
    """
    if not os.path.isdir(target):
        raise SystemExit("[安裝/事前檢查] %s 不存在 —— 不替你建立。新下游請先從上游執行 "
                         "setup_gates_env.py <target>(它要求 target 已 git init)。" % target)
    if target_venv_python(target) is None:
        raise SystemExit("[安裝/事前檢查] %s 沒有 .venv-gates 的直譯器 —— 拒絕安裝,target 未被寫入。\n"
                         "     先從上游執行:python .claude/portable/setup_gates_env.py %s" % (target, target))
    ok, out = _run_target_identity(target)
    if not ok:
        raise SystemExit("[安裝/事前檢查] %s/.venv-gates 的身分檢查不合法 —— 拒絕安裝,target 未被寫入:\n%s"
                         % (target, out))


# ── `--rehook`(票 156 D11)──────────────────────────────────────────────────────
#
# 只寫 `.git/hooks/pre-commit` 與 `.githooks/pre-commit`,其他檔一律不碰;不自動提交。
# 兩支**分別**判定所有權:存在就必須(CRLF→LF 之後)逐位元組等於 KNOWN_HOOKS 的某一版。
# 任何一支不認得、缺一支 ⇒ 整次 fail-closed,兩支都不寫。
# 更新是**全有或全無**:先保存兩支原始內容與 metadata,替換失敗就把已換掉的復原。
# 這是以保存與復原達成的全有或全無,**不是**檔案系統層的跨檔原子交易。

_REHOOK_PATHS = ((".git", "hooks", "pre-commit"), (".githooks", "pre-commit"))


def _lf(data):
    """唯一允許的正規化(G2):CRLF → LF。不刪空白、不動 BOM、不改編碼。"""
    return data.replace(b"\r\n", b"\n")


def _known_hook_id(data):
    import hashlib
    digest = hashlib.sha256(_lf(data)).hexdigest()
    for vid, sha in KNOWN_HOOKS.items():
        if sha == digest:
            return vid
    return None


def _replace_hook(path, data):
    """替換單一 hook 檔(同目錄暫存檔 + `os.replace`),保留原本的 mode。RT8(i) 的注入點。"""
    mode = os.stat(path).st_mode
    tmp = path + ".rehook-tmp"
    try:
        with io.open(tmp, "wb") as f:
            f.write(data)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def _restore_hook(path, saved):
    data, mode, atime_ns, mtime_ns = saved
    with io.open(path, "wb") as f:
        f.write(data)
    os.chmod(path, mode)
    os.utime(path, ns=(atime_ns, mtime_ns))


def rehook(target):
    """已安裝的下游**只刷新 pre-commit**。回 `"updated"` 或 `"no-op"`;拒絕 ⇒ SystemExit。"""
    target = os.path.abspath(target)
    for rel in ((".claude", "hooks", "gate.py"), (".agents", "extension-allowlist.json")):
        if not os.path.isfile(os.path.join(target, *rel)):
            raise SystemExit("[rehook] %s 沒有裝過 agent-gates(缺 %s)—— 拒絕。"
                             % (target, "/".join(rel)))
    if target_venv_python(target) is None:
        raise SystemExit("[rehook] %s 沒有 .venv-gates 的直譯器 —— 拒絕(新 hook 經 gatepy 只認 .venv-gates)。"
                         % target)
    paths = [os.path.join(target, *rel) for rel in _REHOOK_PATHS]
    missing = [p for p in paths if not os.path.isfile(p)]
    if missing:
        raise SystemExit("[rehook] 缺 %s —— 現行安裝契約一定同時寫這兩支,缺一支不是它會產生的狀態;"
                         "fail-closed,兩支都不寫。" % "、".join(missing))
    bodies = []
    for p in paths:
        with io.open(p, "rb") as f:
            bodies.append(f.read())
    unknown = [p for p, b in zip(paths, bodies) if _known_hook_id(b) is None]
    if unknown:
        raise SystemExit("[rehook] 這些 hook 的內容不是已登記的 agent-gates 範本(手工改過或自訂):%s"
                         " —— fail-closed,兩支都不寫。" % "、".join(unknown))
    desired = HOOK.encode("utf-8")
    if all(_lf(b) == desired for b in bodies):
        return "no-op"
    saved = {}
    for p, b in zip(paths, bodies):
        st = os.stat(p)
        saved[p] = (b, st.st_mode, st.st_atime_ns, st.st_mtime_ns)
    done = []
    try:
        for p, b in zip(paths, bodies):
            if _lf(b) == desired:
                continue
            _replace_hook(p, desired)
            done.append(p)
    except BaseException:
        for p in done:
            _restore_hook(p, saved[p])
        raise
    return "updated"


def verify(target):
    """安裝時**強制**跑一次。不通過就不算安裝完成。

    票 01 只驗 R2(最薄的端到端);全規則機器列舉的版本是票 02。
    刪規則輪起 R2 只提示不擋,端到端探針改用保留硬擋的 R4(`_probe_r4`)。

    **直譯器(票 156 D-10)**:明確取 `<target>/.venv-gates` 的那一支執行 gate ——
    不經 sh 或 gatepy(從 PowerShell 跑安裝時 PATH 上通常沒有 sh)、
    不用裸 `python`、不用本行程的 `sys.executable`、不退回 PATH。
    """
    py = target_venv_python(target)
    if py is None:
        raise SystemExit("安裝後驗證找不到 %s 的直譯器 —— 拒絕(不退回其他 Python)。"
                         % os.path.join(target, VENV_GATES))
    rc, out = run([py, os.path.join(".claude", "hooks", "gate.py"), "--pre-commit"],
                  target, check=False)
    if rc != 0:
        hint = ""
        if "[R10/fail-closed] claude_root_invalid" in out:
            # 票 146 G-4(選 A):root 不存在即 invalid;安裝器只說明前提,不替人建立。
            hint = "\n需要使用者層根目錄 ~/.claude 存在且可列舉；安裝器不會替你建立。"
        raise SystemExit("安裝後的權威判定不乾淨,安裝不算完成:\n%s%s" % (out, hint))

    # 權威層裝了沒 —— 這一層不進版控,漏裝是完全靜默的。安裝時是唯一被機器強制的時點。
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "installed_gate", os.path.join(target, ".claude", "hooks", "gate.py"))
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    ok, detail = g.authoritative_layer(target)
    if not ok:
        raise SystemExit("權威層沒裝起來,安裝不算完成:%s" % detail)
    return _probe_r4(target, g)


PROBE_MIRROR_DIR = ".claude/skills"


def _probe_fingerprint(path):
    import hashlib
    try:
        return hashlib.sha256(io.open(path, "rb").read()).hexdigest()
    except (IOError, OSError):
        return None


def _probe_snapshot(target, watched):
    _, head = run(["git", "rev-parse", "HEAD"], target)
    _, index = run(["git", "ls-files", "-s"], target)
    _, status = run(["git", "status", "--porcelain=v1", "--untracked-files=all"], target)
    return {"HEAD": head.strip(), "index": index, "status": status,
            "fingerprint": dict((rel, _probe_fingerprint(os.path.join(target, *rel.split("/"))))
                                for rel in watched)}


_PROBE_BLOCK_HEAD = "[六站閘門/pre-commit] commit 已擋下"
_PROBE_ENTRY = re.compile(r"^  (\[R\d+[^\]]*\](?:\[enforce\])?) ?(.*)$")


def _probe_block_problems(out, rel, rc):
    """探針的擋下只認 gate 的**擋下段**(`commit 已擋下` 之後、兩格縮排的那幾項),提示段不算。

    允許的硬擋只有兩種:(i) R4,且指向本次刪除的鏡像檔;
    (ii) R10,且內容就是**同一則** R4 違規(同檔、同原因)—— R10 的鏡像比對會把同一個缺檔再報一次。
    其餘任何一項(別條規則、R4 指向別的檔、R10 只同檔名)都算其他硬擋。
    """
    lines = out.splitlines()
    starts = [i for i, l in enumerate(lines) if l.startswith(_PROBE_BLOCK_HEAD)]
    if not starts:
        return ["提交被擋了(rc=%d),但輸出裡沒有閘門的擋下段 —— 環境錯誤或別的 hook 先擋,"
                "不算閘門擋下。" % rc]
    entries = []
    for l in lines[starts[-1] + 1:]:
        if l.startswith("[六站閘門"):
            break
        m = _PROBE_ENTRY.match(l)
        if m:
            entries.append((m.group(1), m.group(2)))
    hit = re.compile(r"(?<![\w./-])%s(?![\w./-])" % re.escape(rel))
    r4 = [body for tag, body in entries if tag.startswith("[R4") and hit.search(body)]
    if not r4:
        return ["提交被擋了(rc=%d),但擋下段裡沒有 R4 指向 %s 的那一則。" % (rc, rel)]
    others = [tag + " " + body for tag, body in entries
              if not (tag.startswith("[R4") and body in r4)
              and not (tag.startswith("[R10") and any(("[R4] " + b) in body for b in r4))]
    if others:
        return ["擋下段裡有 R4 以外的硬擋 —— 探針問不準「閘門是不是因為 R4 而擋」:\n    %s"
                % "\n    ".join(others)]
    return []


def _probe_r4(target, g):
    """安裝後用**保留硬擋的 R4** 證明閘門還會擋(刪規則輪;探針位置裁決整理 v2)。

    R1/R2/R3/R8 降為提示之後,舊探針(前置站提交原始碼、要 R2 擋)必然失敗。
    在**被安裝的 repo 內**刪一個鏡像 SKILL.md,`git commit --allow-empty` ——
    不 add 任何檔、不改站牌 —— 要求 R4 擋下且指向那個檔,之後以 `build_mirrors` 重建。
    git 真的選中的那個 hook 跑起來才會有這個結果,所以它證明的是接線,不只是判定。

    前提不成立就**不跑探針**,失敗也**不自動回退** —— 任何變動都印出來交給人。
    """
    staged = run(["git", "diff", "--cached", "--name-only"], target)[1].strip()
    if staged:
        raise SystemExit("安裝後自我檢查沒有執行:index 與 HEAD 不一致(有暫存內容)。\n"
                         "探針要一個空的待提交區才問得準;不會替你退出暫存或搬動工作:\n%s"
                         % staged)

    canon = os.path.join(target, ".agents", "skills")
    names = sorted(n for n in (os.listdir(canon) if os.path.isdir(canon) else [])
                   if os.path.isfile(os.path.join(canon, n, "SKILL.md"))
                   and os.path.isfile(os.path.join(target, *(PROBE_MIRROR_DIR.split("/") + [n, "SKILL.md"]))))
    if not names:
        raise SystemExit("安裝後自我檢查沒有執行:找不到可用來探針的鏡像 SKILL.md(%s/<skill>/SKILL.md)。"
                         % PROBE_MIRROR_DIR)
    rel = "%s/%s/SKILL.md" % (PROBE_MIRROR_DIR, names[0])
    canon_rel = ".agents/skills/%s/SKILL.md" % names[0]
    mirror = os.path.join(target, *rel.split("/"))
    if _probe_fingerprint(mirror) != _probe_fingerprint(os.path.join(target, *canon_rel.split("/"))):
        raise SystemExit("安裝後自我檢查沒有執行:鏡像 %s 與正典 %s 不一致(既存修改)。\n"
                         "探針要刪再重建它,重建會蓋掉那份內容 —— 停下,沒有刪檔。" % (rel, canon_rel))
    baseline = g.check_skill_copies()
    if baseline:
        raise SystemExit("安裝後自我檢查沒有執行:R4 在不刪檔時就已經不通過 ——\n"
                         "那樣的擋下證明不了探針問的事。停下,沒有刪檔:\n%s" % "\n".join(baseline))

    watched = (rel, canon_rel, ".dev/pipeline.json")
    before = _probe_snapshot(target, watched)
    os.remove(mirror)
    rc, out = run(["git", "commit", "--allow-empty", "-q", "-m", "install self-check probe"],
                  target, check=False)
    rebuilt = None
    try:
        build_mirrors(target)
    except Exception as e:  # noqa: BLE001 —— 重建失敗要原樣說出來
        rebuilt = "%s: %s" % (type(e).__name__, e)
    after = _probe_snapshot(target, watched)

    problems = []
    if rebuilt is not None:
        problems.append("鏡像重建失敗(%s 可能沒有回來):%s" % (rel, rebuilt))
    if rc == 0:
        problems.append("空提交被放行了(rc=0)—— 閘門沒在守。")
    else:
        problems += _probe_block_problems(out, rel, rc)
    for key in ("HEAD", "index", "status", "fingerprint"):
        if before[key] != after[key]:
            problems.append("探針前後 %s 不一致。" % key)
    if problems:
        raise SystemExit(
            "安裝後自我檢查失敗,安裝不算完成:\n  %s\n"
            "位置:%s\n探針前 HEAD:%s\n探針後 HEAD:%s\n"
            "沒有做任何自動回退(不 reset、不改你的歷史)。提交輸出:\n%s"
            % ("\n  ".join(problems), target, before["HEAD"], after["HEAD"], out))
    return out


def refuse_if_dirty(target):
    """既有 repo 的 working tree 不乾淨 → 拒絕安裝並列出變更。

    **「安裝器假設 repo 乾淨」是個沒寫出來的前置條件。**
    install 隨後會 `git add -A && git commit` 生成 go-live —— 在乾淨 repo 無害,
    在髒 repo 會把使用者未提交的工作**全部掃進**框架安裝 commit(難以復原,
    而且 submodule / WIP 都會被吞)。同一行程式碼的破壞性取決於落地環境(friction)。
    把這個前置條件從假設變成機器檢查:髒就停,讓機器擋而不是靠人擋。
    """
    if not os.path.isdir(os.path.join(target, ".git")):
        return  # 全新 / 非 git 目錄:沒有既有工作可吞
    # --ignore-submodules=dirty:submodule 的**內部**未提交變更(status 的 ` m`)
    # 住在 submodule 自己的 index,父 repo 的 `git add -A` 碰不到、吞不走 ——
    # 它不是這道檢查要防的危險。**指標移動**(` M`)才會被 add -A 提交進安裝 commit,
    # 那個仍會被抓到。把「髒」定義成「add -A 吞得走的東西」,而不是 status 的預設髒。
    # 這裡的路徑是**要給人看的**(「你的工作區有這些未提交變更」)——
    # C-quoted 的話使用者認不出自己的檔案,所以同樣走 -z。
    changes = git_paths(["status", "--porcelain", "--ignore-submodules=dirty"],
                        target, check=False)
    if changes:
        listed = "\n".join("    " + c for c in changes[:20])
        more = ("\n    …(還有 %d 個)" % (len(changes) - 20)) if len(changes) > 20 else ""
        raise SystemExit(
            "拒絕安裝:目標 repo 的 working tree 不乾淨(%d 個未提交變更)。\n"
            "install 會 git add -A && commit 生成 go-live —— 那會把下面這些\n"
            "未提交的工作全部掃進框架安裝 commit,難以復原。\n"
            "先 commit 或 stash 這些變更,再重跑安裝:\n%s%s"
            % (len(changes), listed, more))


# ── 票 169:安裝前置核准(preflight)與 D4 沙盒例外 ─────────────────────────────────
#
# 順序(全部在第一個寫入目標之前):precheck → require_git_repo → refuse_if_dirty →
# 既有 policy 檢查 → 產生候選(D2)→ 依 D1 落地 → 判核准(D3)。任何一步不過 ⇒ 下游零寫入。

def _canon(path):
    return os.path.normcase(os.path.realpath(os.fspath(path)))


def _inside(child, parent):
    c, p = _canon(child), _canon(parent)
    return c == p or c.startswith(p.rstrip(os.sep) + os.sep)


def _git_out(args, cwd):
    p = subprocess.run(["git"] + list(args), cwd=cwd, capture_output=True)
    return p.returncode, p.stdout.decode("utf-8", "replace").strip()


def require_git_repo(target):
    """非 git 目錄裁決(票 169):target 必須是 git repo 的最上層;不是 ⇒ 零寫入拒絕。

    安裝器**不再**替人 `git init` 或建立目錄 —— 那是一次未受治理的寫入。
    """
    hint = ("[安裝/事前檢查] %s 不是 git repo 的最上層 —— 請先 git init"
            "(安裝器不會替你 git init 或建立目錄;下游未寫入)。" % target)
    if not os.path.lexists(os.path.join(target, ".git")):
        raise SystemExit(hint)
    rc, top = _git_out(["rev-parse", "--show-toplevel"], target)
    if rc != 0 or not top or _canon(top) != _canon(target):
        raise SystemExit(hint)


def target_head(target):
    """UNBORN 裁決:有 commit ⇒ 完整 40 碼 SHA;unborn branch ⇒ `UNBORN`;其他狀態 ⇒ 停止。"""
    rc, out = _git_out(["rev-parse", "--verify", "-q", "HEAD^{commit}"], target)
    if rc == 0 and _HEX40.match(out):
        return out
    rc2, _ref = _git_out(["symbolic-ref", "-q", "HEAD"], target)
    if rc != 0 and rc2 == 0:
        return UNBORN
    raise SystemExit("[安裝/名冊候選] 讀不出 target 的 HEAD(不是 40 碼 commit,也不是 unborn branch)"
                     " —— 下游未寫入。")


def _upstream_head():
    rc, out = _git_out(["rev-parse", "HEAD"], SRC_ROOT)
    if rc != 0 or not _HEX40.match(out):
        raise SystemExit("[安裝/名冊候選] 讀不到 agent-gates 的 HEAD(完整 40 碼)—— 下游未寫入。")
    return out


def _source_redlight():
    """上游(本檔所在 repo)的 `.claude/hooks/redlight.py` —— 會被複製到目標的同一份。

    preflight 在任何寫入之前跑,目標此時還沒有 redlight,所以不能用 `_target_redlight`。
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "source_redlight", os.path.join(SRC_ROOT, ".claude", "hooks", "redlight.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def upstream_inventory_head(root=None):
    """票 171 D1:上游 **HEAD 已提交** 的 `.agents/extension-inventory.json`(不讀工作樹)。`root` 為 None ⇒ 上游 repo。

    讀不到 / 解析失敗 ⇒ SystemExit,下游未寫入。合格與否由呼叫端以 redlight 的 `_extension_inventory_ok` 判定。
    """
    root = SRC_ROOT if root is None else os.fspath(root)
    p = subprocess.run(["git", "cat-file", "blob", "HEAD:" + UPSTREAM_INVENTORY_REL], cwd=root, capture_output=True)
    if p.returncode != 0:
        raise SystemExit("[安裝/名冊候選] 讀不到上游 HEAD 已提交的 %s —— 下游未寫入。" % UPSTREAM_INVENTORY_REL)
    try:
        return json.loads(p.stdout.decode("utf-8"))
    except Exception:
        raise SystemExit("[安裝/名冊候選] 上游 HEAD 的 %s 解析失敗 —— 下游未寫入。" % UPSTREAM_INVENTORY_REL)


def _carry_contracts(rl, upstream_inventory, synced_pairs, claude_root):
    """票 171 D2 / D3:回 `{邏輯路徑: contract 項目}`(只含本次觀測到、且通過契約驗證的)。

    只承接 contract.name 在 `EXT_CONTRACT_PATHS` 且 path 等於該名稱寫死路徑的項目;path / contract 逐字照抄、
    note 用 `CARRIED_CONTRACT_NOTE`。本機不在 synced_files ⇒ 不承接;驗證失敗或實際路徑解析不了 ⇒ SystemExit
    (只印類別/欄位代碼)。
    """
    if not rl._extension_inventory_ok(upstream_inventory):
        raise SystemExit("[安裝/名冊候選] 上游 HEAD 名冊沒有通過 redlight 的 policy 驗證 —— 下游未寫入。")
    have = set(rel for rel, _sha in synced_pairs)
    carried = {}
    for item in upstream_inventory.get("entries") or []:
        contract = item.get("contract") if isinstance(item, dict) else None
        if not isinstance(contract, dict):
            continue
        name, path = contract.get("name"), item.get("path")
        if name not in rl.EXT_CONTRACT_PATHS or path != rl.EXT_CONTRACT_PATHS[name]:
            continue
        if path not in have:
            continue
        real = rl._synced_contract_real_path(claude_root, path)
        if real is None:
            raise SystemExit("[安裝/名冊候選] contract %s 的實際路徑無法解析 —— 下游未寫入。" % name)
        res = rl.synced_contract_check(name, real, contract.get("pins"))
        if res is not None:
            raise SystemExit("[安裝/名冊候選] contract %s 驗證失敗:%s/%s —— 下游未寫入。"
                             % (name, res.get("category"), res.get("field")))
        carried[path] = {"path": path, "contract": {"name": name, "pins": dict(contract["pins"])},
                         "note": CARRIED_CONTRACT_NOTE}
    return carried


def _carried_contract_names(inv):
    """D6:候選 inventory 裡承接的 contract 名稱(依路徑排序)。"""
    return [e["contract"]["name"] for e in inv.get("entries") or [] if "contract" in e]


def _canonical_bytes(doc):
    return json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256(data):
    import hashlib
    return hashlib.sha256(data).hexdigest()


def target_id(canonical_path):
    """D1 的 `<target-id>`:target canonical 路徑的 SHA-256 前 16 碼(只當資料夾名,不參與核准判定)。"""
    return _sha256(canonical_path.encode("utf-8"))[:16]


def inventory_candidate(target, claude_root=None, upstream_head=None, upstream_inventory=None):
    """D2:依現況產生候選 ⇒ `(canonical_bytes, candidate_hash)`。純讀,不寫任何檔。

    現況一律取自上游 redlight 的 `extension_report`(R10 自己的觀測,不另寫一套算法);
    `claude_root` 為 None ⇒ 同 R10 取使用者層 `~/.claude`。`upstream_head` 為 None ⇒ 讀 agent-gates 的 HEAD。
    任何一項無法登記(觀測失敗、symlink / 讀不到、`.mcp.json` 讀不到)⇒ SystemExit,下游未寫入。
    票 171:`upstream_inventory` 為 None ⇒ 讀上游 HEAD 已提交的名冊(`upstream_inventory_head`);其中本機觀測到
    且通過契約驗證的 contract 項目取代同路徑的 sha256 項目,承接 ≥1 條 ⇒ version 2;0 條 ⇒ 與票 171 前逐位元相同。
    """
    rl = _source_redlight()
    report = rl.extension_report(target, claude_root)
    if report.get("observation") != "ok":
        raise SystemExit("[安裝/名冊候選] 使用者層觀測失敗:%s —— 下游未寫入。" % report.get("reason"))
    surfaces = report.get("surfaces") or {}
    errors = surfaces.get("errors") or []
    if errors:
        raise SystemExit("[安裝/名冊候選] 觀測失敗:%s: %s(共 %d 筆)—— 下游未寫入。"
                         % (errors[0][0], errors[0][-1], len(errors)))

    def entries(pairs, label):
        out = []
        for rel, sha in sorted(pairs, key=lambda item: item[0]):
            if sha is None:
                raise SystemExit("[安裝/名冊候選] %s 有無法登記的項目(symlink 或讀不到):%s —— 下游未寫入。"
                                 % (label, rel))
            out.append({"path": rel, "sha256": sha, "note": CANDIDATE_NOTE})
        return out

    mcp = list(surfaces.get("mcp_json_servers") or [])
    if any(isinstance(m, str) and m.endswith(": unreadable") for m in mcp):
        raise SystemExit("[安裝/名冊候選] 目標的 .mcp.json 讀不到或格式不明 —— 下游未寫入。")
    allow = {}
    for k in rl.EXT_ALLOWLIST_FIELDS:
        allow[k] = []
    allow["schema"] = rl.EXT_ALLOWLIST_SCHEMA
    allow["version"] = rl.EXT_ALLOWLIST_VERSION
    allow["dev_mod_files"] = entries(surfaces.get("dev_mod_files") or [], "dev-mods")
    allow["user_skill_plugins"] = entries(surfaces.get("user_skill_plugins") or [], "user-skills")
    allow["user_commands"] = entries(surfaces.get("user_commands") or [], "user-commands")
    allow["project_settings_hook_commands"] = _settings_hook_commands(SRC_ROOT)
    allow["mcp_json_servers"] = mcp
    synced_pairs = surfaces.get("synced_files") or []
    up_inv = upstream_inventory if upstream_inventory is not None else upstream_inventory_head()
    carried = _carry_contracts(rl, up_inv, synced_pairs, report.get("claude_root"))
    synced_entries = [carried.get(e["path"], e) for e in entries(synced_pairs, "synced")]
    inv = {"schema": rl.EXT_INVENTORY_SCHEMA,
           "version": rl.EXT_INVENTORY_VERSION_CONTRACT if carried else rl.EXT_INVENTORY_VERSION,
           "entries": synced_entries}
    if not (rl._extension_allowlist_ok(allow) and rl._extension_inventory_ok(inv)):
        raise SystemExit("[安裝/名冊候選] 產生的候選沒有通過 redlight 的 policy 驗證 —— 下游未寫入。")
    doc = {"schema": CANDIDATE_SCHEMA, "version": CANDIDATE_VERSION,
           "agent_gates_head": upstream_head if upstream_head is not None else _upstream_head(),
           "target": {"path": _canon(target).replace("\\", "/"), "head": target_head(target)},
           "inventory": inv, "allowlist": allow}
    data = _canonical_bytes(doc)
    return data, _sha256(data)


def _shown_candidate(cands_dir, tid, digest):
    """候選檔的**相對**位置(不印本機絕對路徑)。"""
    tail = "%s/%s.json" % (tid, digest)
    try:
        rel = os.path.relpath(cands_dir, SRC_ROOT)
    except ValueError:
        rel = None
    if rel and not rel.startswith(".."):
        return rel.replace("\\", "/") + "/" + tail
    return "<候選根目錄>/" + tail


def _store_candidate(cands_dir, data, digest):
    """D1:候選落地。已存在 ⇒ 只驗它自己的 bytes(不符 ⇒ 候選證據毀損、停止、不覆寫);不存在 ⇒ 新建。回相對位置。"""
    doc = json.loads(data.decode("utf-8"))
    tid = target_id(doc["target"]["path"])
    folder = os.path.join(cands_dir, tid)
    path = os.path.join(folder, digest + ".json")
    shown = _shown_candidate(cands_dir, tid, digest)
    if os.path.lexists(path):
        try:
            with io.open(path, "rb") as f:
                existing = f.read()
        except OSError:
            existing = None
        if existing is None or _sha256(existing) != digest:
            _out("[安裝/名冊候選] 候選證據毀損(candidate evidence corruption):%s 的內容 hash 與檔名不符。" % shown)
            _out("    依現況重算的 hash:%s" % digest)
            _out("    原檔未覆寫、下游未寫入、安裝停止。請人工檢視該檔再決定怎麼處置。")
            raise SystemExit(EXIT_CANDIDATE_CORRUPT)
    else:
        os.makedirs(folder, exist_ok=True)
        with io.open(path, "xb") as f:
            f.write(data)
    return shown


def inventory_preflight(target, approve, cands_dir, claude_root=None, upstream_head=None):
    """D1 / D3:產生候選並依 D1 落地,再判核准。回 `("pending", hash, 位置)` 或 `("approved", 候選文件, hash)`。

    核准判定**只**比對「依現況重算的 hash」與 `approve` —— 既有候選檔只驗它自己的 bytes,
    從不拿來當判定來源。其餘情形一律 SystemExit,下游零寫入。
    """
    data, digest = inventory_candidate(target, claude_root=claude_root, upstream_head=upstream_head)
    doc = json.loads(data.decode("utf-8"))
    shown = _store_candidate(cands_dir, data, digest)
    if approve is None:
        return "pending", digest, shown, doc
    if approve != digest:
        _out("[安裝/名冊候選] 核准的 hash 與依現況重算的 hash 不一致 —— 下游未寫入、安裝停止。")
        _out("    核准值:%s" % approve)
        _out("    現況:  %s" % digest)
        _out("    新候選:%s(需要重新審閱並由 Jeff 明示核准)" % shown)
        raise SystemExit(EXIT_INVENTORY_MISMATCH)
    return "approved", doc, digest


class DisposableRepo(str):
    """D4 例外(E1):`create_disposable_repo` 親手建立的拋棄式 repo。

    做成 str 子類別只為了能直接當路徑用;**判定一律看 `_registered_sandbox` 的記憶體登記**,
    不看這個型別、它的值或任何屬性 —— 自己建構一個同型別的物件不會被登記。
    """
    __slots__ = ()


_DISPOSABLE = {}


def create_disposable_repo(path, candidates_dir):
    """E1 / E3:親手 `mkdir` 一個拋棄式 repo 目錄並登記在本程序記憶體;回傳的物件是 self-approve 的唯一依據。

    目錄已存在 ⇒ `FileExistsError` 外傳(不是親手建立的就不登記)。候選根目錄不得落在上游真正的
    `.dev/install-candidates/` 之下,也不得在拋棄式 repo 裡面。只有內部呼叫;沒有 CLI、環境變數或設定檔入口。
    """
    path = os.path.abspath(os.fspath(path))
    cands = os.path.abspath(os.fspath(candidates_dir))
    if _inside(cands, _REAL_CANDIDATES_DIR):
        raise SystemExit("[安裝/拋棄式] 候選根目錄不得在上游的 .dev/install-candidates/ 之下 —— 拒絕。")
    if _inside(cands, path):
        raise SystemExit("[安裝/拋棄式] 候選根目錄不得在拋棄式 repo 裡面 —— 拒絕。")
    os.mkdir(path)
    real = os.path.realpath(path)
    obj = DisposableRepo(real)
    _DISPOSABLE[id(obj)] = (obj, os.path.normcase(real), cands)
    return obj


def _registered_sandbox(obj):
    """E1:`obj` 必須**正是** `create_disposable_repo` 回傳的那個物件。回登記項或 None。

    只查本程序的記憶體登記(以物件身分比對);不讀磁碟、不讀環境變數、不看路徑樣式或字串值。
    """
    entry = _DISPOSABLE.get(id(obj))
    if entry is None or entry[0] is not obj:
        return None
    return entry


def install_disposable(sandbox):
    """D4 例外的入口(內部函式):只接受 `create_disposable_repo` 回傳的物件本身;其他一律拒絕、零寫入(E1 / E5)。"""
    if _registered_sandbox(sandbox) is None:
        raise SystemExit("[安裝/拋棄式] 拒絕 self-approve:目標不是本程序以 create_disposable_repo 親手建立的"
                         "拋棄式 repo —— 未寫入任何東西。")
    return main(sandbox)


def _approve_inventory(target, approve, cands_dir, self_approve):
    """`approve` 為 None 且不是拋棄式 repo ⇒ 印 hash 與候選位置後停止(EXIT_INVENTORY_PENDING)。

    拋棄式 repo(D4 例外):把剛算出的 hash 交回**同一條**比對路徑 —— 依現況重算、逐字比對(E4)。
    """
    state = inventory_preflight(target, approve, cands_dir)
    if state[0] == "pending" and self_approve:
        state = inventory_preflight(target, state[1], cands_dir)
    if state[0] == "pending":
        _out("[安裝/名冊核准] 下游尚未寫入任何東西。extension 名冊候選已產生:")
        _out("    候選 hash:%s" % state[1])
        _out("    候選檔:  %s" % state[2])
        names = _carried_contract_names(state[3]["inventory"])
        if names:
            _out(u"    承接上游 contract %d 筆（名稱：%s）" % (len(names), u"、".join(names)))
        _out("    審閱候選內容後由 Jeff 明示核准,再以 --approve-inventory <hash> 重跑安裝。")
        _out("    (產生候選 ≠ 核准候選;agent 不得自行推導、複製或代填這個 hash。)")
        raise SystemExit(EXIT_INVENTORY_PENDING)
    return state[1], state[2]


# ── 票 169 輪四:第一個 commit 前重驗與自動復原(新裁決 3／4,R1～R7)────────────────
#
# 範圍(R7):只涵蓋「第一個寫入」到「第一個 commit 成功」之間;commit 一成功就離開,之後的失敗不復原。
# journal(R2 的寫入紀錄)= 這一段**每一步會寫的路徑**,在寫入前一次登記:框架檔、鏡像兩棵樹、
# 產生的狀態檔、hooks、兩份 policy、目標 redlight 載入時留下的 `__pycache__`,以及 `git add` /
# `git commit` 會寫的 `.git/index`、`.git/objects/`、`.git/COMMIT_EDITMSG`、`.git/index.lock`。

_JOURNAL_FILES = (".dev/pipeline.json", ".dev/test-runs.jsonl", ".dev/gate-exemptions.jsonl", "CLAUDE.md",
                  ".gitignore", PORTABLE_HOOK_REL, "bootstrap.sh", ".agents/portable-manifest.txt",
                  POLICY_TEMPLATE, ".git/hooks/pre-commit", ".git/index", ".git/index.lock",
                  ".git/COMMIT_EDITMSG")
_JOURNAL_TREES = (".claude/skills", "skills", ".claude/hooks/__pycache__", ".git/objects")
_NO_BYTES_TREES = (".git/objects",)        # 既有物件不會被改寫;只記存在,不讀內容


class _ReverifyMismatch(Exception):
    """第一個 commit 前重算的候選 hash 與核准值不一致。帶著新候選的 bytes 與 hash。"""

    def __init__(self, data, digest):
        Exception.__init__(self, digest)
        self.data = data
        self.digest = digest


def _under(rel, root):
    return rel == root or rel.startswith(root + "/")


def _fs_snapshot(target):
    """R1:target 底下**全部**路徑(含 `.git/`、ignored、目錄本身)→ 種類 dir / file / link。不跟隨連結。"""
    import stat as _stat
    out = {}
    for dp, dns, fns in os.walk(target, followlinks=False):
        for name in list(dns) + list(fns):
            p = os.path.join(dp, name)
            rel = os.path.relpath(p, target).replace("\\", "/")
            mode = os.lstat(p).st_mode
            out[rel] = "link" if _stat.S_ISLNK(mode) else ("dir" if _stat.S_ISDIR(mode) else "file")
    return out


def _git_state(target):
    """R1:HEAD、index、tracked / untracked / ignored、repo-local config、core.hooksPath(git 看得到的那一半)。"""
    def g(*args):
        p = subprocess.run(["git"] + list(args), cwd=target, capture_output=True)
        return p.returncode, p.stdout
    return {"head": g("rev-parse", "--verify", "-q", "HEAD"),
            "symref": g("symbolic-ref", "-q", "HEAD"),
            "index": g("ls-files", "-s", "-z"),
            "status": g("status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignored"),
            "config": g("config", "--local", "--list", "-z"),
            "hooksPath": g("config", "--get", "core.hooksPath")}


class _Journal(object):
    """R1 的開始前快照 + R2 的寫入紀錄。只在記憶體裡,不落地。"""

    def __init__(self, target, files, trees):
        self.target = target
        self.files = frozenset(files)
        self.trees = tuple(trees)
        anc = set()
        for rel in list(self.files) + list(self.trees):
            parts = rel.split("/")
            for i in range(1, len(parts)):
                anc.add("/".join(parts[:i]))
        self.ancestors = frozenset(anc)
        self.git = None
        self.fs = None
        self.data = {}

    def journaled(self, rel):
        return rel in self.files or rel in self.ancestors or any(_under(rel, t) for t in self.trees)


def _begin_journal(target, copy_paths, rl):
    """R1:任何寫入之前的快照。寫入點開始前就是連結或型別不符 ⇒ 不動手(下游零寫入)。"""
    import stat as _stat
    files = set(copy_paths) | set(_JOURNAL_FILES) | {rl.EXT_ALLOWLIST_FILE, rl.EXT_INVENTORY_FILE}
    j = _Journal(target, files, _JOURNAL_TREES)
    j.git = _git_state(target)
    j.fs = _fs_snapshot(target)
    for rel, kind in sorted(j.fs.items()):
        if not j.journaled(rel):
            continue
        want = "file" if rel in j.files else "dir"
        if kind == "link" or (rel in j.files or rel in j.ancestors) and kind != want:
            raise SystemExit("[安裝/事前檢查] %s 開始前就存在,且是 %s(安裝器要寫的是 %s)—— 下游未寫入。"
                             % (rel, kind, want))
    keep = [rel for rel, kind in j.fs.items() if kind == "file"
            and (rel == ".git/config" or _under(rel, ".git/hooks")
                 or (j.journaled(rel) and not any(_under(rel, t) for t in _NO_BYTES_TREES)))]
    for rel in keep:
        full = os.path.join(target, *rel.split("/"))
        with io.open(full, "rb") as f:
            j.data[rel] = (f.read(), _stat.S_IMODE(os.lstat(full).st_mode))
    return j


def _rb_remove(path):
    """復原:刪除一個本次新建的路徑(R2)。目錄只用 rmdir —— 裡面有不在紀錄內的東西就失敗,不連帶刪。"""
    import stat as _stat
    if _stat.S_ISDIR(os.lstat(path).st_mode):
        os.rmdir(path)
        return
    try:
        os.chmod(path, _stat.S_IWRITE | _stat.S_IREAD)     # git 物件是唯讀檔(Windows 上 remove 會被拒)
    except OSError:
        pass
    os.remove(path)


def _rb_restore_dir(path):
    """復原:重建一個開始前就存在的目錄(R3)。"""
    os.mkdir(path)


def _rb_restore(path, data, mode):
    """復原:把開始前就存在的檔寫回開始前的 bytes(R3)。"""
    with io.open(path, "wb") as f:
        f.write(data)
    os.chmod(path, mode)


def _rollback_failed(reason):
    """R6:hard fail。不再嘗試任何其他修復,也不宣稱恢復了原狀。"""
    _out("[安裝/復原失敗] %s。" % reason)
    _out("    下游 repo **未恢復**到安裝前的狀態 —— 安裝器不再嘗試其他修復;請人工檢查目標 repo。")
    raise SystemExit(EXIT_ROLLBACK_FAILED)


def _rollback_diffs(journal):
    """R5:與開始前逐項比對。回不一致項目的名稱(不含任何檔案內容)。"""
    target = journal.target
    diffs = []
    if _git_state(target) != journal.git:
        diffs.append("git 狀態(HEAD / index / status / config / core.hooksPath)")
    if _fs_snapshot(target) != journal.fs:
        diffs.append("檔案系統路徑集合")
    for rel, (data, _mode) in sorted(journal.data.items()):
        full = os.path.join(target, *rel.split("/"))
        try:
            with io.open(full, "rb") as f:
                same = f.read() == data
        except OSError:
            same = False
        if not same:
            diffs.append(rel)
    return diffs


def _rollback(journal):
    """第一個 commit 前失敗的自動復原(R2 / R3 / R5 / R6;只在 main 的復原範圍內被呼叫,R7)。

    順序:刪除「開始前不存在 且 在寫入紀錄裡」的路徑(由深到淺)→ 重建開始前存在、現在不見的目錄
    → 把開始前存在、現在不同的檔寫回原 bytes → 逐項驗證。任何一步失敗或驗證不一致 ⇒ hard fail。
    開始前就存在的路徑(含 ignored)從不刪除。
    """
    target = journal.target
    try:
        now = _fs_snapshot(target)
        new = [rel for rel in now if rel not in journal.fs and journal.journaled(rel)]
        for rel in sorted(new, key=lambda r: (-r.count("/"), r)):
            _rb_remove(os.path.join(target, *rel.split("/")))
        for rel in sorted(r for r, k in journal.fs.items() if k == "dir"):
            full = os.path.join(target, *rel.split("/"))
            if not os.path.isdir(full):
                _rb_restore_dir(full)
        for rel, (data, mode) in sorted(journal.data.items()):
            full = os.path.join(target, *rel.split("/"))
            try:
                with io.open(full, "rb") as f:
                    same = f.read() == data
            except OSError:
                same = False
            if not same:
                _rb_restore(full, data, mode)
    except Exception as e:
        _rollback_failed(u"復原中途失敗(%s)" % type(e).__name__)
    diffs = _rollback_diffs(journal)
    if diffs:
        _rollback_failed(u"復原後與開始前不一致:%s" % u"、".join(diffs[:5]))


def _reverify_before_commit(target, approved_hash):
    """新裁決 3:第一個 git add 之前,依現況重新產生候選並重算 hash;不一致 ⇒ _ReverifyMismatch。"""
    data, digest = inventory_candidate(target)
    if digest != approved_hash:
        raise _ReverifyMismatch(data, digest)


def main(target, approve_inventory=None):
    sandbox = _registered_sandbox(target)
    if approve_inventory is not None and not (isinstance(approve_inventory, str)
                                              and _HEX64.match(approve_inventory)):
        raise SystemExit("--approve-inventory 必須是 64 碼小寫 hex(逐字來自 Jeff 的明示核准)。")
    target = os.path.abspath(target)
    if sandbox is not None and os.path.normcase(os.path.realpath(target)) != sandbox[1]:
        raise SystemExit("[安裝/拋棄式] 拋棄式 repo 的實際位置與建立時不同 —— 拒絕。")
    precheck(target)              # 票 156 G4:任何寫入之前
    require_git_repo(target)      # 票 169 非 git 目錄裁決:不再 makedirs / git init
    refuse_if_dirty(target)
    rl = _source_redlight()
    for rel in (rl.EXT_ALLOWLIST_FILE, rl.EXT_INVENTORY_FILE):
        if os.path.lexists(os.path.join(target, *rel.split("/"))):
            raise SystemExit("[安裝/事前檢查] 目標已有 %s —— 新下游安裝不接手既有的 extension policy;"
                             "下游未寫入。" % rel)
    cands = sandbox[2] if sandbox is not None else CANDIDATES_DIR
    approved, approved_hash = _approve_inventory(target, approve_inventory, cands, sandbox is not None)

    all_files, untracked = source_files()
    buckets, unmarked = classify(all_files)
    carried_untracked = [p for p in untracked if manifest.in_scope(p)]
    journal = _begin_journal(target, buckets["copy"], rl)     # 輪四 R1:任何寫入之前
    try:
        copy_into(target, buckets["copy"])
        mirrors = build_mirrors(target)
        generate_manifest(target)     # 它標 ask,copy 桶帶不過去 —— 得自己產
        generate_state(target)
        hook = install_hook(target)
        portable_hook, boot = install_portable_layer(target)
        _template, policy_file = write_policy_template(target)
        # 票 146 G-2:在第一個 `git add -A` 之前 —— 隨既有的安裝 commit 進 HEAD,不另開 commit、不新增豁免。
        ext_allow, ext_inv, _created = write_extension_policy(
            target, approved=(approved["allowlist"], approved["inventory"]))
        n_inv = len(approved["inventory"]["entries"])
        n_files = sum(len(approved["allowlist"][k]) for k in ("dev_mod_files", "user_skill_plugins", "user_commands"))
        n_mcp = len(approved["allowlist"]["mcp_json_servers"])
        ext_note = None
        if n_inv or n_files or n_mcp:
            ext_note = ("由安裝前置核准(票 169)登記:候選 hash %s;inventory %d 筆、allowlist 檔案型 %d 筆、"
                        ".mcp.json server %d 筆,另加安裝器寫入的 hook command。R10 在 pre-commit 以這兩份的 HEAD 版本判定;"
                        "使用者層(`~/.claude`)之後有任何未登記的變動,commit 就會被擋。"
                        % (approved_hash, n_inv, n_files, n_mcp))

        # 新裁決 3:第一個 git add / commit 之前重驗。
        _reverify_before_commit(target, approved_hash)
        run(["git", "add", "-A"], target)
        # **在 add 之後、commit 之前。** `update-index --chmod` 改的是既有 index 條目,
        # 放在 add 之前沒有對象可改;放在 commit 之後那個 mode 進不了這一筆。
        stage_hook_executable(target)
        run(["git", "commit", "-q", "--no-verify", "-m", "裝上六站閘門(框架安裝)"], target)
    except BaseException as e:
        # R7:只有第一個 commit 成功之前的失敗會走到這裡。
        _rollback(journal)
        if isinstance(e, _ReverifyMismatch):
            shown = _store_candidate(cands, e.data, e.digest)
            _out("[安裝/名冊重驗] 第一個 commit 前依現況重算的 hash 與核准值不一致 —— 安裝停止;"
                 "下游已復原到安裝前狀態並逐項驗證過。")
            _out("    核准值:%s(已失效)" % approved_hash)
            _out("    現況:  %s" % e.digest)
            _out("    新候選:%s(需要重新審閱並由 Jeff 明示核准)" % shown)
            raise SystemExit(EXIT_REVERIFY_ROLLED_BACK)
        _out("[安裝/復原] 第一個 commit 前失敗 —— 下游已復原到安裝前狀態並逐項驗證過;原始錯誤如下。")
        raise
    _, go_live = run(["git", "rev-parse", "HEAD"], target)
    go_live = go_live.strip()

    legacy = generate_legacy_list(target, go_live)
    run(["git", "add", "-A"], target)
    run(["git", "commit", "-q", "--no-verify", "-m",
         "凍結既有 .py 的紅燈豁免清單(go-live %s)" % go_live[:7]], target)

    blocked = verify(target)
    pending = write_decisions_pending(
        target, buckets, carried_untracked, unmarked, policy_file=policy_file,
        extension_policy=[os.path.relpath(p, target).replace("\\", "/") for p in (ext_allow, ext_inv)],
        extension_note=ext_note)

    _out("裝好了:%s" % target)
    _out("  複製      %d 個檔案" % len(buckets["copy"]))
    _out("  產生      .dev/(狀態與空證據)、.agents/legacy-no-redlight.txt(%d 筆)" % len(legacy))
    _out("  鏡像      %s" % (", ".join(mirrors) or "(無 skills 可鏡像)"))
    _out("  權威層    %s(這台機器,不進版控)"
         % os.path.relpath(hook, target).replace("\\", "/"))
    _out("  可攜層    %s + bootstrap.sh(進版控,mode 100755)"
         % os.path.relpath(portable_hook, target).replace("\\", "/"))
    # **C 的代價要說出來(票 58 甲)。** 裝出來的 repo 上,`.githooks/` 在
    # `bootstrap.sh` 跑之前是**死的** —— 只看目錄結構的人會以為權威層走那裡,
    # 而實際走 `.git/hooks/`。不說的話,這就是本票自己製造的下一則 F-099。
    _out("\n**`.githooks/` 現在是死的,要跑一次 `sh bootstrap.sh` 才會生效。**")
    _out("    現在生效的是 .git/hooks/pre-commit(這台機器,clone 帶不走)。")
    _out("    `.githooks/` 進了版控,所以**下一個 clone 只要跑那一行**就接上 ——")
    _out("    在此之前,那一步是「先手工造一個 hook,再跑一行 config」。")
    _out("    這一步關不掉:git 刻意不讓 clone 自動執行任何東西(ADR 0007)。")
    _out("  go-live   %s" % go_live)
    if carried_untracked:
        _out("\n帶過去了但來源 repo 還沒把它們進版控 —— 確認不是暫存檔:")
        for p in carried_untracked:
            _out("    %s" % p)
    # 被 .gitignore 蓋住的框架檔:帶了,但要說。
    # 不說的話,下一個人不會知道他的 .gitignore 正在對抗安裝器 ——
    # 而那個狀態的後果是「裝出沒有閘門的 repo」,且安裝過程安靜又成功(票 18)。
    # 票 172 D3:只列「ignored 框架檔 ∩ 本次實際交給 copy_into 的 copy 桶」—— 宣稱「已強制帶過去」才為真。
    copied = set(buckets["copy"])
    hidden = [p for p in ignored_framework_files() if p in copied]
    if hidden:
        _out("\n**來源的 .gitignore 蓋住了這些框架檔**,已強制帶過去 ——"
             "請確認那是刻意的:")
        for p in hidden:
            _out("    %s" % p)
    # ask / 未涵蓋鄰居 / 未進版控 —— **落地成檔案**,不只印終端機。
    # 印出來沒人看等於沒列;寫成 decisions-pending.md,人回頭找得到,也進得了版控。
    if pending:
        _out("\n要人決定的項目已寫進:%s" % os.path.relpath(pending, target).replace("\\", "/"))
        _out("    (別只看終端機 —— 那份檔案是這些決定的落地處)")
    else:
        _out("\n沒有待決定項目。")
    _out("\n閘門實測（R4 空提交探針）:")
    for line in blocked.strip().splitlines():
        _out("    %s" % line)


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == "--rehook":
        _out("[rehook] %s" % rehook(args[1]))
        sys.exit(0)
    if len(args) == 1 and not args[0].startswith("--"):
        main(args[0])
    elif (len(args) == 3 and not args[0].startswith("--") and args[1] == "--approve-inventory"
          and _HEX64.match(args[2])):
        main(args[0], approve_inventory=args[2])
    else:
        raise SystemExit("用法:python .claude/portable/install.py <目標目錄>\n"
                         "      python .claude/portable/install.py <目標目錄> --approve-inventory <64 碼 hex>"
                         "(值必須逐字來自 Jeff 的明示核准)\n"
                         "      python .claude/portable/install.py --rehook <已安裝的目標目錄>")
