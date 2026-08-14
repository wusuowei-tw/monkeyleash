# -*- coding: utf-8 -*-
"""票 11 — R7:Bash 寫入 repo 一律擋,請改用 Write/Edit。

**這是收口,不是擴涵蓋。**

不採用「加 Bash 進 matcher + 解析寫入目標」:從指令字串解析「寫到哪」解不完
(heredoc 內文的路徑、sed -i、> 重導、tee、自己算路徑的腳本),
而 **60% 有效的解析器比零涵蓋更危險** —— 零涵蓋你知道它是零,
60% 你會以為 Bash 被守住了。那是 R4 的形狀。

改為:述詞只回答「**有沒有在寫**」,不回答「寫到哪」。
判斷不出來就當作在寫(fail-closed),所有寫入被逼回檔案工具 ——
而那條路 R1–R6 已經守得住,且在兩個環境各驗過一次。

**殘留缺口(明寫,不假裝擋得住)**:`python foo.py` 這種「指令本身看不出在寫」的
仍然穿得過去。不假裝 —— 那正是本票拒絕解析器的同一個理由。
"""

import importlib.util
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load_gate():
    spec = importlib.util.spec_from_file_location(
        "gate_for_bash", ROOT / ".claude" / "hooks" / "gate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gate = _load_gate()


@pytest.mark.parametrize("cmd", [
    "echo x > notes.txt",
    "printf 'a' >> docs/agents/friction-log.md",
    "sed -i 's/a/b/' macro_audit/classify.py",
    "cat x | tee out.txt",
    "cp a.py b.py",
    "mv a.py b.py",
    "touch newfile.py",
    "mkdir -p newdir",
    "python - <<'PY'\nimport io\nio.open('x.py','w').write('x')\nPY",
])
def test_writing_commands_are_blocked(cmd):
    """每一種都是「明顯在寫」。heredoc 那條順帶結構性消滅 F-028。"""
    msg = gate.bash_write_violation(cmd)
    assert msg and "R7" in msg, "沒擋到:%r -> %r" % (cmd, msg)
    assert "Write" in msg or "Edit" in msg, "訊息沒告訴人改用什麼:%r" % msg


@pytest.mark.parametrize("cmd", [
    "cat macro_audit/classify.py",
    "python -m pytest tests/ -q",
    "grep -rn foo tests/",
    "ls -la",
    "python .claude/hooks/gate.py --pre-commit",
    "git commit -m 'x'",
    "git add -A",
    "bash scripts/skills-update.sh",
])
def test_non_writing_or_sanctioned_commands_pass(cmd):
    """誤擋的代價不是不方便,是規則會被關掉 —— 而關掉的涵蓋率是零。"""
    assert gate.bash_write_violation(cmd) is None, "誤擋:%r" % cmd


@pytest.mark.parametrize("cmd", [
    "ls > /dev/null",
    "python x.py 2>&1",
    "echo probe > /tmp/probe.txt",
])
def test_targets_that_are_certainly_outside_the_repo_pass(cmd):
    """「確定在 repo 外」與「不知道寫到哪」是兩件事。

    前者可以放行:R7 管的是 repo 內,repo 外是 G1 的事。
    後者必須擋:不知道就當作在寫。
    """
    assert gate.bash_write_violation(cmd) is None, "誤擋:%r" % cmd


def test_every_exception_carries_a_reason():
    """理由欄是讓判準漂移看得見的東西 —— 與三份非原始碼清單同一個規矩。"""
    for name in ("BASH_ALLOWED_CMDS", "BASH_ALLOWED_TARGETS"):
        table = getattr(gate, name)
        assert isinstance(table, dict), "%s 必須是 {項目: 理由}" % name
        for k, why in table.items():
            assert isinstance(why, str) and why.strip(), "%s 的 %r 沒有理由" % (name, k)


def test_the_rule_is_enumerated_like_every_other_rule():
    """R7 要進 rule_codes,否則 verify_gates 不會替它準備情境 —— 規則存在卻沒被證明擋得住。"""
    assert "R7" in gate.rule_codes()


class TestEveryWriteTargetMustBeAllowed:
    """**「提到一個許可目標」不等於「每個寫入目標都被許可」。**

    原本的檢查是 `if target in cmd: return None` —— 只要指令**字串裡出現**
    任何一個許可目標,整條就免檢。於是在任何指令後面加 `2>/dev/null`
    就整條免檢,而抑制 stderr 是每個人本來就有的習慣:
    **這不是要刻意繞才踩得到的洞,是日常寫法會誤觸的洞**,
    只是誤觸的方向是「被放行」,所以沒有人會發現。

    判錯對象第七例(票 19)。
    """

    @pytest.mark.parametrize("cmd,named", [
        ("python x.py > out.txt 2>/dev/null", "out.txt"),
        ("python x.py >out.txt 2>/dev/null", "out.txt"),
        ("cat a > b.txt 2>/dev/null", "b.txt"),
    ])
    def test_a_suppressed_stderr_does_not_whitelist_a_real_write(self, cmd, named):
        msg = gate.bash_write_violation(cmd)
        assert msg, "加了 2>/dev/null 就免檢:%r" % cmd
        assert named in msg, "沒有點名真正的寫入目標(%s):%s" % (named, msg)

    @pytest.mark.parametrize("cmd", [
        "rm -rf important_dir >/dev/null",
        "cp secret.env backup.env 2>/dev/null",
        "mv a.txt b.txt >/dev/null",
        "tee gate.py < evil 2>/dev/null",
    ])
    def test_a_write_command_is_not_rescued_by_dev_null(self, cmd):
        assert gate.bash_write_violation(cmd), "寫入指令被 /dev/null 救了:%r" % cmd

    # ── 正控:不得回歸 ────────────────────────────────────────────────
    @pytest.mark.parametrize("cmd", [
        "ls >/dev/null",
        "ls > /dev/null",
        "ls >/dev/null 2>&1",
        "python -m pytest -q > /dev/null 2>&1",
        "grep -c foo bar >/dev/null",
    ])
    def test_writing_only_to_dev_null_is_still_allowed(self, cmd):
        assert gate.bash_write_violation(cmd) is None, cmd

    @pytest.mark.parametrize("cmd", [
        "python x.py > /tmp/out.txt",
        "rm -rf /tmp/scratch",
        "python x.py > C:/x/scratchpad/out.txt",
    ])
    def test_allowed_targets_still_pass(self, cmd):
        assert gate.bash_write_violation(cmd) is None, cmd

    def test_an_unparseable_write_is_blocked(self):
        """解析不出目標 → 擋。**半套的解析器比零涵蓋更危險**,
        所以不確定時往嚴的倒(ADR 0008 的同一句話)。"""
        assert gate.bash_write_violation("Set-Content -Path (Join-Path $a $b) -Value x")


class TestRedirectsInsideQuotesAreNotTargets:
    """票 21 標本 3(最後一塊)—— `REDIRECT_RE` 命中**引號內**的 `>`。

    `sed 's/[A-Za-z]:/<路徑>/g' file.txt` 的引號**成對且乾淨**,
    所以 E/F 的訊號打不到它;垃圾目標 `/g` 來自 `REDIRECT_RE`
    把引號裡的 `>` 當成 shell 重導向。這是 F-078 的核心。

    ## 選型論證:**上層收口讓下層原本危險的做法變成良定義**

    原本拒絕「先剝掉引號內容」的理由是:
    shell 引號規則有轉義、巢狀、`$(...)`,**半套的解析器比零涵蓋更危險**。

    **E/F 落地之後那個前提變了**:引號一旦不成對、或有跳脫空白,
    **整段已經先被 refuse 掉**。走到這一步的段落,引號**必然成對且無跳脫** ——
    在那個前提下遮蔽成對引號是**良定義的,不是猜**。

    這是本票最可攜的結構性收穫:
    **一個上層的收口,可以把下層原本危險的做法變成安全的。**
    順序不能反 —— 先做遮蔽、後做 refuse,遮蔽仍然是猜。

    ## 遮蔽只用於「找目標」,不用於「判斷有沒有在寫」

    `WRITE_CONSTRUCT` 仍然跑在**原字串**上。理由:引號裡的東西**可能被執行**
    (`sh -c "rm -rf x"`、`powershell -Command "Remove-Item x"`),
    而那件事從字串本身判斷不出來。**偵測要過度涵蓋,抽取才要誠實** ——
    把遮蔽用在偵測上,就是把誤擋換成漏擋,而那個方向更糟。
    """

    def test_a_redirect_inside_quotes_is_not_reported_as_a_target(self):
        """**核心紅燈。** 引號內的 `>` 不得變成寫入目標。"""
        msg = gate.bash_write_violation(
            "sed 's/[A-Za-z]:/<x>/g' file.txt")
        assert msg, "仍應擋(偵測跑在原字串上,保守)"
        assert "/g" not in msg, "引號內的 > 生出了垃圾目標 /g:%r" % msg
        assert "解析不出寫入目標" in msg, "沒退回誠實訊息:%r" % msg

    @pytest.mark.parametrize("cmd,target", [
        ("python x.py > out.txt", "out.txt"),
        ("python x.py >> docs/log.txt", "docs/log.txt"),
        ('echo "a -> b" > out.txt', "out.txt"),
    ])
    def test_real_redirects_outside_quotes_are_still_caught(self, cmd, target):
        """**驗收 3a,反控 —— 本票最危險的一條。**

        遮蔽**不得**把真的重導向一起遮掉。第三個案例是關鍵:
        同一條指令裡**同時有**引號內的 `->` 與引號外的真重導向,
        遮蔽必須只吃掉前者。

        誤擋變漏擋,方向比誤擋更糟 —— 誤擋會被抱怨,漏擋不會有人發現。
        """
        msg = gate.bash_write_violation(cmd)
        assert msg, "%s 的真重導向沒擋到 —— 遮蔽把它一起遮掉了" % cmd
        assert target in msg, "重導向目標沒被點名:%r" % msg

    def test_a_quoted_redirect_target_is_still_named(self):
        """重導向目標本身被引號包住時,仍要點名它的**原文**。

        遮蔽保長度,所以偏移量對得回原字串 —— 這條釘住那個對應關係。
        """
        msg = gate.bash_write_violation('python x.py > "out file.txt"')
        assert msg, "沒擋"
        assert "out file.txt" in msg, "引號內的重導向目標沒被還原:%r" % msg


class TestAmbiguousQuotingRefusesInsteadOfInventing:
    """票 21 E/F —— 引號碎裂與跳脫空格:**切不乾淨就 refuse,絕不捏造路徑**。

    本票的標題病:`rm pkg/my\\ file.py` 現行會生出**兩個**目標,
    其中 `file.py` 是**憑空捏造的路徑** —— 指令裡根本沒有那個檔案。
    「具體而錯誤」比「含糊而誠實」傷害更大,因為人會相信它然後去找一個不存在的檔案。

    ## 為什麼不造 tokenizer(量測結果,不是偏好)

    `shlex` 兩個模式都不能用:

        posix=True   E/F 切得完美,但 `rm C:\\Users\\fake\\thing.py`
                     -> `C:Usersfakething.py`  **反斜線被當跳脫,Windows 路徑毀了**
        posix=False  Windows 路徑正確,但 E 裂成 `"pkg"` + `/"thing.py"`(比現行更糟),
                     F 的反斜線接空格照樣裂

    **`posix=True` 那條是「半套解析比零解析危險」的直接證據**:
    它產生一個**看起來像路徑、實際不存在**的字串,然後那個字串會被拿去比對許可清單。
    零解析至少知道自己是零。

    所以改成:**偵測「切不乾淨」的字元層級訊號,命中就 refuse** ——
    不需要任何解析器,只需要兩個可列舉的訊號。
    """

    @pytest.mark.parametrize("cmd", [
        'rm "pkg"/"thing.py"',                 # E:引號碎裂
        "rm 'pkg'/thing.py",                   # E:單引號碎裂
        'Remove-Item "pkg"/thing.py',          # E:PowerShell 版
        "rm pkg/my\\ file.py",                 # F:跳脫空格
        'rm "my file.py"',                     # F:引號內空白(現行裂成兩個)
        'Remove-Item "my file.py"',            # F:PowerShell 版
    ])
    def test_ambiguous_quoting_is_refused_without_naming_a_path(self, cmd):
        """**核心紅燈。** 擋下,而且**不報任何路徑**。"""
        msg = gate.bash_write_violation(cmd)
        assert msg, "%s 沒擋" % cmd
        assert "無法可靠切分" in msg, "沒說出是切不乾淨:%r" % msg
        assert "file.py" not in msg.replace("無法可靠切分", ""), (
            "訊息裡出現了路徑碎片 —— 本票的標題病就是捏造路徑:%r" % msg)

    @pytest.mark.parametrize("cmd", [
        'rm "unbalanced.py',
        "rm 'unbalanced.py",
        'Set-Content "unbalanced.py -Value x',
    ])
    def test_unclosed_quotes_take_the_same_refuse_path(self, cmd):
        """**驗收 2a。** 引號未閉合(shlex 會 ValueError 那類)走同一條路 ——
        擋下、同樣不報路徑。

        不同的失敗形狀走不同的訊息,人得學兩套;而它們的處置完全一樣。
        """
        msg = gate.bash_write_violation(cmd)
        assert msg, "%s 沒擋" % cmd
        assert "無法可靠切分" in msg, "沒走同一條 refuse 路徑:%r" % msg

    @pytest.mark.parametrize("cmd,target", [
        ('rm "pkg/thing.py"', "pkg/thing.py"),
        ("rm 'pkg/thing.py'", "pkg/thing.py"),
        ('Remove-Item "pkg/thing.py"', "pkg/thing.py"),
        ('Set-Content "pkg/thing.py" -Value x', "pkg/thing.py"),
    ])
    def test_simple_quoting_still_gets_a_clean_message(self, cmd, target):
        """**驗收 2b,反控。** 單純的頭尾引號**不得**被新訊號誤傷 ——
        訊息要照樣點名正確目標。

        新訊號只認「剝掉成對外層引號之後**還有**引號」,
        `"pkg/thing.py"` 剝完是乾淨的,所以不命中。
        """
        msg = gate.bash_write_violation(cmd)
        assert msg, cmd
        assert target in msg, "單純引號被誤傷,訊息不再點名目標:%r" % msg
        assert "無法可靠切分" not in msg, "單純引號被當成切不乾淨:%r" % msg

    @pytest.mark.parametrize("cmd,target", [
        (r"rm C:\Users\fake\thing.py", r"C:\Users\fake\thing.py"),
        (r"Remove-Item C:\Users\fake\thing.py", r"C:\Users\fake\thing.py"),
    ])
    def test_windows_paths_keep_working(self, cmd, target):
        """**驗收 2c,反控。** Windows 路徑滿是反斜線,不得被 F 的訊號誤傷。

        F 認的是**反斜線接空白**,而 `C:\\Users\\fake` 的反斜線後面是字母。
        這條同時釘住「不要改用 shlex posix=True」—— 那個模式會把這條路徑
        吃成 `C:Usersfakething.py`。
        """
        msg = gate.bash_write_violation(cmd)
        assert msg, cmd
        assert target in msg, "Windows 路徑被吃掉或誤判:%r" % msg
        assert "無法可靠切分" not in msg, "Windows 路徑被當成切不乾淨:%r" % msg


class TestExtractionFailureMustRefuse:
    """票 36 —— 動詞認得、目標抽不到,現行是 **fail-open**。

    `unallowed_write_targets` 只在 `not saw_construct` 時補佔位項。
    動詞認得時 `saw_construct=True`,運算元全被跳過 → `bad` 為空 → 回 `[]` →
    `bash_write_violation` 的 `if not bad: return None` → **放行**。

    **這是票 29 的回歸。** 票 29 為避免票 21 的垃圾目標(`-Value hello`
    被當成寫入目標),把 PowerShell 的抽取收窄成「只認可列舉的位置」。
    收窄是對的,錯在**沒有配 fail-closed 的底** ——
    收窄之後「抽不到」變成常態,而底層仍是「抽不到就放行」。

    **具名教訓:收窄抽取必須同時鋪底,否則「不亂猜」退化成「不擋」。**
    收窄的動機永遠是訊息品質(別報垃圾),代價落在涵蓋率 ——
    兩者不在同一個人的注意力裡:改的時候在看訊息,而破的是攔截。

    ## 三態,不是兩態

        抽到目標,有不許可的   -> 擋,點名
        抽到目標,全部許可     -> **放行**
        一個目標都沒抽到       -> **擋(解析失敗)**   ← 現在是放行

    所以要追蹤的是「有沒有抽到任何目標」,不是「`bad` 空不空」——
    `saw_construct`(有沒有寫入構造)與 `saw_target`(有沒有抽到目標)
    是兩件事,而現行把它們混成一個變數。**那個混同就是這個洞的根。**
    """

    @pytest.mark.parametrize("cmd", [
        "rm -- -weird.py",
        "rm -rf --preserve-root -- -x.py",
        "Copy-Item .cache/x.json pkg/thing.py",
        "Move-Item .cache/x.json pkg/thing.py",
    ])
    def test_an_extraction_failure_is_blocked(self, cmd):
        """**核心紅燈。** 這四條現在全部放行,而它們都會動到 `pkg/` 底下的檔案。"""
        assert gate.bash_write_violation(cmd), (
            "%s 抽不到目標卻放行 —— 解析失敗的預設姿態必須是 refuse" % cmd)

    def test_the_message_says_it_could_not_parse_rather_than_inventing_a_path(self):
        """訊息要說**解析失敗**,不是捏造一個看起來像路徑的東西。

        票 21 的標題病就是憑空生出路徑(`rm pkg/my\\ file.py` 生出一個
        不存在的 `file.py`)。**擋得住而說不出來,好過擋得住而說錯。**
        """
        msg = gate.bash_write_violation("rm -- -weird.py")
        assert msg, "沒擋"
        assert "解析" in msg, "沒說出這是解析失敗:%r" % msg

    @pytest.mark.parametrize("cmd", [
        "rm -rf /tmp/scratch",
        "python x.py > /dev/null",
        "python x.py > C:/x/scratchpad/out.txt",
        "Remove-Item .cache/x.json",
    ])
    def test_allowed_targets_still_pass(self, cmd):
        """**反控,本票最容易做錯的地方。**

        這四條是「抽到目標、而目標被許可」—— `bad` 同樣是空的。
        若修法寫成「`bad` 空就擋」,它們會全部變成違規,
        於是 R7 每天擋掉大量正當指令,然後整條規則被關掉(F-031)。
        **把 fail-open 修成 fail-everything,不算修好。**
        """
        assert gate.bash_write_violation(cmd) is None, cmd


class TestPowerShellVerbFamiliesAreCovered:
    """票 29 —— R7 漏掉 PowerShell 的刪改動詞家族,而 G1 只管專案外。

    `WRITE_CONSTRUCT` 收了寫入動詞(`Set-Content` / `Add-Content` / `Out-File` /
    `New-Item` / `Clear-Content`),**漏掉 `Remove-Item` / `Move-Item` /
    `Copy-Item` / `Rename-Item` 整個刪改家族**。
    而 G1 第二級**刻意只管專案外**(專案內刪除放行是寫在 `g1_guard.py` 註解裡的設計)。
    **兩層的空隙疊在一起:專案內 `Remove-Item` 同時穿過 R7 與 G1。**

    漏掉的是**刪除**,方向特別差:寫入被漏還留著檔案可以事後看,
    刪除被漏之後**沒有東西可以看** —— 與 G1 保護清單把備份排第一的不對稱同一條。

    ## 實測發現的第二個缺口(票面只寫了第一個)

    `WRITE_COMMANDS` 的註解寫著「**與 WRITE_CONSTRUCT 的第一段同一份名單**」,
    而實測兩者的 PowerShell 交集是**空集合** —— 那五個動詞一個都不在 `WRITE_COMMANDS` 裡。

    後果:`Set-Content foo.py` 偵測得到(擋下)、但**抽不出目標**,
    訊息因此退化成「(解析不出寫入目標)」。**那正是卡點 #6b 那個沒用的訊息的來源。**

    所以本票要修的是**兩份名單的一致性**,不是往其中一份加幾個字 ——
    這是 F-083「收了一個入口就回頭問同類入口」在同一支檔案內的形式。
    """

    DELETE_FAMILY = ["Remove-Item", "Move-Item", "Copy-Item", "Rename-Item"]
    WRITE_FAMILY = ["Set-Content", "Add-Content", "Out-File",
                    "New-Item", "Clear-Content"]

    @pytest.mark.parametrize("verb", DELETE_FAMILY)
    def test_the_deletion_family_is_blocked(self, verb):
        """**核心紅燈。** 現行 `WRITE_CONSTRUCT` 認不得這四個動詞,整條放行。"""
        msg = gate.bash_write_violation("%s pkg/thing.py" % verb)
        assert msg, "%s 在專案內動檔案卻整條放行 —— 它同時穿過 R7 與 G1" % verb
        assert "R7" in msg, msg

    @pytest.mark.parametrize("verb", DELETE_FAMILY + WRITE_FAMILY)
    def test_the_message_names_the_target(self, verb):
        """訊息要點名**目標**,不是退化成「解析不出寫入目標」。

        票 13 的判準:訊息要說出是哪一個前提沒滿足。
        而「(解析不出寫入目標)」連錯誤的具體都沒有 —— 人拿它做不了任何事。
        """
        msg = gate.bash_write_violation("%s pkg/thing.py" % verb)
        assert msg, verb
        assert "thing.py" in msg, (
            "%s:訊息沒點名目標,退化成含糊句了:%r" % (verb, msg))

    def test_the_two_lists_agree_on_powershell_verbs(self):
        """**結構測試:兩份名單必須一致。**

        `WRITE_COMMANDS` 的註解宣稱它與 `WRITE_CONSTRUCT` 的第一段是同一份名單,
        而實測交集為空。**註解描述了一個不存在的同步** ——
        與 machine-init 曾經承諾一個不存在的指令同一族。

        這條測試存在的理由不是「現在對不對」,是**往後任何一邊加動詞時,
        另一邊沒加會當場紅**。名單一致靠機制,不靠記性。
        """
        import re as _re
        # 名詞可能是多個字(`New-FileCatalog`、`Update-ScriptFileInfo`)——
        # 第一版寫成 `[A-Z][a-z]+-[A-Z][a-z]+`,把它們截成 `New-File`、
        # `Update-Script`,於是**測試自己造出三個不存在的缺口**。
        # 截斷型的比對錯誤與票 04 那條「邊界放在擷取處會砍長度」同族。
        in_construct = {m.lower() for m in _re.findall(
            r"[A-Z][a-z]+-[A-Za-z]+", gate.WRITE_CONSTRUCT.pattern)}
        in_commands = {w.lower() for w in gate.WRITE_COMMANDS}
        missing = sorted(in_construct - in_commands)
        assert not missing, (
            "這些動詞偵測得到卻抽不出目標(訊息會退化成含糊句):%s" % missing)

    @pytest.mark.parametrize("cmd", [
        "Get-ChildItem .",
        "Test-Path pkg/thing.py",
        "Get-Content pkg/thing.py",
        "Select-String -Pattern x -Path pkg/thing.py",
    ])
    def test_read_only_powershell_still_passes(self, cmd):
        """**反控。** 少了它,「一律擋含連字號動詞的指令」也會讓上面全綠 ——
        而那會讓 R7 每天擋掉大量唯讀診斷,然後整條規則被關掉(F-031)。"""
        assert gate.bash_write_violation(cmd) is None, cmd

    @pytest.mark.parametrize("cmd", [
        "rm pkg/thing.py",
        "cp a.py b.py",
        "echo x > notes.txt",
    ])
    def test_existing_posix_behaviour_is_unchanged(self, cmd):
        """**反控。** 既有 POSIX 那半的行為零變化 —— 回歸網,不是宣稱。"""
        msg = gate.bash_write_violation(cmd)
        assert msg and "R7" in msg, cmd

    def test_allowed_targets_still_win_for_the_new_verbs(self):
        """新動詞也要吃許可清單 —— 否則 `.dev/` 之類的正當寫入會被誤擋。"""
        assert gate.bash_write_violation("Remove-Item .cache/x.json") is None

    THIRD_FAMILY = [
        # *-Item 家族沒收完 —— 第一輪只收了五個
        ("Set-Item pkg/thing.py -Value x", "thing.py"),
        ("Clear-Item pkg/thing.py", "thing.py"),
        # Export-*:直接把資料寫成檔
        ("Export-Csv -Path pkg/out.csv -InputObject $x", "out.csv"),
        ("Export-Clixml -Path pkg/out.xml -InputObject $x", "out.xml"),
        ("Export-Alias pkg/aliases.txt", "aliases.txt"),
        # 壓縮/解壓:解壓也是寫
        ("Compress-Archive -Path pkg -DestinationPath pkg/out.zip", "out.zip"),
        ("Expand-Archive -Path a.zip -DestinationPath pkg/x", "pkg/x"),
        # 其餘寫檔者
        ("New-FileCatalog -Path pkg -CatalogFilePath pkg/cat.cat", "cat.cat"),
        ("Update-ScriptFileInfo pkg/x.ps1", "x.ps1"),
        ("Tee-Object -FilePath pkg/thing.py", "thing.py"),
        ("Start-Transcript -Path pkg/log.txt", "log.txt"),
    ]

    @pytest.mark.parametrize("cmd,target", THIRD_FAMILY)
    def test_the_third_family_is_blocked_and_named(self, cmd, target):
        """票 29 收尾 —— **第三類調查的紅燈**。

        調查方法照 F-083:**列舉來源,不是「我想得到的」**。
        跑了兩個軸,而**兩個軸互相看不見對方**:

          動詞軸   `Get-Command | Where Verb -in (Set/New/Remove/Export/…)`
          參數軸   `Where Parameters 含 OutFile / FilePath / DestinationPath`

        動詞軸漏掉 `Invoke-WebRequest -OutFile`(動詞是 Invoke,完全看不出在寫);
        參數軸漏掉 `Set-Item`(參數是位置運算元,沒有具名輸出參數)。
        **一個軸的「查完了」是另一個軸的盲區** —— 這句話比這張表本身值錢。
        """
        msg = gate.bash_write_violation(cmd)
        assert msg, "%s 會寫檔卻整條放行" % cmd
        assert target in msg, "訊息沒點名目標 %s:%r" % (target, msg)

    @pytest.mark.parametrize("cmd", [
        "Start-Job -FilePath pkg/x.ps1",
        "Invoke-Command -FilePath pkg/x.ps1",
    ])
    def test_filepath_as_an_input_is_not_a_write(self, cmd):
        """**反控,而且是這一輪最重要的一條。**

        `-FilePath` 在 `Tee-Object` 是**輸出**,在 `Start-Job` 是**輸入腳本** ——
        同一個參數名,相反方向。純參數比對會把後者誤判成寫入。

        擋住這個誤判的是**動詞閘**:抽取只在「動詞已經是已知寫入者」時才跑,
        所以參數名的歧義**被動詞這一層中和掉了**。
        這條測試釘的就是那個中和 —— 少了它,往後有人把參數比對抽出來獨立用,
        誤擋會悄悄回來。
        """
        assert gate.bash_write_violation(cmd) is None, cmd

    def test_named_parameter_values_do_not_become_targets(self):
        """**防止本票引進票 21 的病。**

        PowerShell 用具名參數:`Set-Content foo.py -Value x -Encoding utf8`。
        既有的運算元迴圈跳過 `-Xxx`,**但不跳過它後面那個值** ——
        照搬到 PowerShell 會讓 `x`、`utf8` 全變成「寫入目標」。

        那正是票 21 記的形狀:**具體而錯誤的訊息比含糊而誠實傷害更大**,
        因為人會相信它,然後去找一個不存在的路徑。

        所以本票的抽取只認**可列舉的位置**:動詞後面第一個運算元,
        以及 `-Path` / `-LiteralPath` / `-Destination` / `-NewName` 後面那一個。
        其餘一律不當目標 —— 抽不到就退回佔位項(擋),不亂猜。
        """
        msg = gate.bash_write_violation(
            "Set-Content pkg/thing.py -Value hello -Encoding utf8")
        assert msg and "thing.py" in msg, msg
        for noise in ("hello", "utf8"):
            assert noise not in msg, (
                "具名參數的值被當成寫入目標了(%r)—— 那是票 21 的病:%r"
                % (noise, msg))
