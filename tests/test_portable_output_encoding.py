# -*- coding: utf-8 -*-
"""票 62 —— 三支可攜工具的輸出在 cp950 主控台上不得炸掉。

## 這個檔案守的是什麼

`verify_gates.py` / `g1_verify.py` / `shadow_review.py` 都是**「證明別的東西
是對的」那一類工具**:淨室驗證、G1 的全套驗收(`ADR 0009` 唯一合法途徑的
其中一步)、影子模式的晉升判定。它們壞掉時,壞的不是功能,
**是證據的產生能力** —— 而那種壞法不會讓任何別的測試變紅。

現象是 `UnicodeEncodeError` **未捕捉 → 行程死掉**,不是輸出變亂碼。

## 為什麼這裡的測試在 CI 上不是空的(票 58 判準)

Linux 的主控台是 UTF-8,所以一條「跑得完」的測試在 CI 上**恆綠** ——
那正是「一個從來不會紅的綠燈是空的」。

所以本檔**不依賴執行環境的主控台**:每一條都自己造出 cp950 的輸出情境
(`io.TextIOWrapper(..., encoding="cp950", errors="strict")`),
在 Linux 上一樣造得出來、一樣會紅。

**而「這個情境真的會拒絕」本身也要被證明** —— 見
`TestTheHarnessItselfRejectsTheMark`:少了它,一個什麼都接受的假 harness
會讓底下三條**因為錯的理由**而綠(`F-103`)。

## errors="strict" 是判準,不是預設值

`errors="replace"` 會把 `✓` 換成 `?` 而**不丟例外** —— 那正是修法 (c)
(「把符號換成 ASCII」)的機器版,而 (c) 已被裁決排除:
它治的是症狀,下一個人寫一個非 ASCII 訊息就再犯。
所以本檔同時斷言**寫出去的位元組解回來仍然帶著原本那個符號**,
不只斷言「沒有丟例外」。
"""
import contextlib
import importlib.util
import io
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PORTABLE = ROOT / ".claude" / "portable"

# 票面量到的是「3 檔 7 行」,而那次掃描的判準是**行首是 `print(` 的那一行**。
# 用 ast 重掃**整個 print 呼叫**之後是 **3 檔 9 個呼叫** —— 多出來的兩個是
# 跨行的 print,它們的壞字落在第二行,而第二行不以 `print(` 開頭。
# 兩個數字都對,量的不是同一個單位(`F-109`:數字要帶單位與基準)。
CP950_UNSAFE = ("✓", "✗", "≥", "⚠")   # ✓ ✗ ≥ ⚠


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, PORTABLE / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@contextlib.contextmanager
def cp950_console():
    """把 `sys.stdout` 換成一個**真的** cp950、**真的**會拒絕的主控台。

    `write_through=True`:不加的話 TextIOWrapper 可能把文字留在自己的緩衝裡,
    等到 flush 才編碼 —— 那會讓例外在被測函式**回來之後**才丟,
    而測試看到的就變成「呼叫成功了」。**編碼的時點要在呼叫之內。**
    """
    raw = io.BytesIO()
    wrapper = io.TextIOWrapper(raw, encoding="cp950", errors="strict",
                               newline="", write_through=True)
    old = sys.stdout
    sys.stdout = wrapper
    try:
        yield raw
    finally:
        sys.stdout = old
        # **`detach()` 不是整潔,是必要的。** 換回去之後 wrapper 沒有人引用,
        # 被回收時會**連底下那個 BytesIO 一起關掉** —— 於是離開這個區塊之後
        # 讀 `raw.getvalue()` 會丟 `ValueError: I/O operation on closed file`。
        # 實際踩過一次:斷言「寫出去的位元組裡有那個符號」時才炸出來。
        # 那一次順帶證明了那些位元組斷言不是裝飾 —— 它們真的會讀。
        wrapper.flush()
        wrapper.detach()


def _carries(raw, mark):
    """那個符號有沒有以 **utf-8 位元組**的形態出現在輸出裡。

    ## 為什麼是「找位元組」而不是「整串解碼」

    修法 (a) 只把**會炸的那幾個** `print` 改走 buffer,其餘 cp950 編得動的
    `print` **刻意留著**(那是範圍,不是遺漏)。於是在這個 harness 底下,
    同一個 BytesIO 會同時收到**兩種編碼**:留下來的 `print` 寫 cp950 位元組,
    `_out` 寫 utf-8 位元組。

    > **拿 `.decode("utf-8")` 去讀整串會丟 `UnicodeDecodeError`,
    > 而那是 harness 的問題,不是被測程式的問題。**

    ⚠ **這件事在真實環境的意思要說清楚,不要讓讀的人自己猜**:

    | 輸出去哪 | 結果 |
    |---|---|
    | Windows **主控台** | `sys.stdout.buffer` 是 `_WindowsConsoleIO`,它把寫進去的位元組**當 utf-8** 轉 UTF-16 再送給主控台 API ⇒ **顯示正確** |
    | **管線 / 重導向** | 是普通檔案,`print` 走 locale(cp950)、`_out` 走 utf-8 ⇒ **同一份輸出裡兩種編碼** |

    後者是 (a) 這個修法**已知而且刻意接受**的代價:本票要換掉的是
    「行程死掉」,不是「排版好看」。要讓整份輸出同編碼,得把這三支的
    **所以** `print` 都改走 `_out` —— 那是另一個範圍,不在本票。

    (實測基礎:不帶 `-X utf8` 把 `verify_gates.py` 導進管線,今天在
    `verify_gates.py:241` 丟 `UnicodeEncodeError` —— 所以「重導向會過而
    主控台會炸」那個假設是**反的**,票 62 偵察題 ① 的第二半由此得證。)
    """
    return mark.encode("utf-8") in raw.getvalue()


class TestTheHarnessItselfRejectsTheMark:
    """**反控:先證明這個情境真的會拒絕。**

    這一條在修好之前與之後都該綠。它紅的話,底下三條的綠**沒有資訊量**
    —— 那是「綠的原因不是你以為的」(`F-032`)。
    """

    @pytest.mark.parametrize("mark", CP950_UNSAFE)
    def test_a_bare_print_of_the_mark_still_raises(self, mark):
        with cp950_console():
            with pytest.raises(UnicodeEncodeError):
                print(mark)

    def test_plain_chinese_is_not_the_problem(self):
        """**歸因要對**:cp950 編得動中文,炸的是那幾個符號。

        少了這一條,讀的人會以為「中文訊息不可攜」,
        然後去做一件不必要而且很大的事(把訊息改成英文)。
        """
        with cp950_console():
            print("這一行全是中文,cp950 編得動")


class TestVerifyGatesReportsSurviveACp950Console:
    """`verify_gates.py`:淨室驗證 —— **本機唯一涵蓋「安裝後形態」的東西**。

    這三個回報函式只把**已經算好的**布林值排版印出來,不做任何判定 ——
    判定留在 `main()` 裡,本票不動它。
    """

    def test_installer_defaults_line(self):
        vg = _load("vg_enc", "verify_gates.py")
        with cp950_console() as raw:
            vg._report_installer_defaults()
        assert _carries(raw, "✓")

    def test_per_rule_result_line(self):
        vg = _load("vg_enc", "verify_gates.py")
        with cp950_console() as raw:
            vg._report_rule_result("R7", True)
            vg._report_rule_result("R9", False)
        # 兩個分支都驗:只驗擋下那一支的話,「沒擋到 ✗」那條路徑
        # 仍然帶著一個會炸的符號,而它正是驗收失敗時才會走到的那條。
        assert _carries(raw, "✓") and _carries(raw, "✗")

    def test_authority_layer_probe_lines(self):
        vg = _load("vg_enc", "verify_gates.py")
        with cp950_console() as raw:
            vg._report_authority_probe(False, "detail", False, "squat", True)
        assert _carries(raw, "✓")

    def test_the_failing_branch_of_the_probe_is_also_safe(self):
        """**負控方向的對稱**:三個布林全部反過來,走的是 `✗` 那半邊。

        驗收工具最需要能印出來的時刻,正是它要說「沒偵測到 ✗」的時刻。
        """
        vg = _load("vg_enc", "verify_gates.py")
        with cp950_console() as raw:
            vg._report_authority_probe(True, "detail", True, "squat", False)
        assert _carries(raw, "✗")


class TestG1VerifyMainSurvivesACp950Console:
    """`g1_verify.py`:**改 G1 的唯一合法途徑要跑它**(`ADR 0009`)。

    它在本機跑不完的話,那條途徑在 Windows 主控台上**走不通**。

    ⚠ **一個位元組都不碰 `~/.claude/`**(界線 A,票 88 §八之一):
    `PROTECTED_LIST` 換成 tmp_path 底下的假清單,`run()` 換成不起行程的替身。
    真實的保護清單、真實的 `g1_guard.py`,本檔從頭到尾沒有讀過。
    """

    def test_main_runs_to_the_end(self, tmp_path, monkeypatch):
        gv = _load("gv_enc", "g1_verify.py")

        fake_list = tmp_path / "g1-protected.txt"
        fake_list.write_text(
            "# 假清單,只為了讓 main() 有三條可跑\n"
            + "\n".join(str(tmp_path / ("entry%d" % i)) for i in range(1, 4)) + "\n",
            encoding="utf-8")
        monkeypatch.setattr(gv, "PROTECTED_LIST", str(fake_list))

        def fake_run(guard, payload):
            """替身:一律回「第一級擋下,且訊息點名這條路徑」。

            不起子行程,也就不會碰到真的 `g1_guard.py` —— 本測試要驗的是
            **這支工具印不印得出來**,不是 G1 擋不擋得住。
            """
            blob = json.dumps(payload, ensure_ascii=False)
            if "_g1_neighbour" in blob or "touch /tmp/x" in blob:
                return (0, "")
            return (2, "[G1/保護清單] %s" % blob.replace("/", "\\"))

        monkeypatch.setattr(gv, "run", fake_run)

        with cp950_console() as raw:
            gv.main("stub-guard-not-executed")
        assert _carries(raw, "✓")


# `shadow_review.py` 那一條**不在這個檔裡**,在 `tests/test_shadow_review.py`。
#
# **不是編排偏好,是 R3 要求的**:`shadow_review.py` 不在
# `.agents/legacy-no-redlight.txt` 上,所以動它需要一筆**屬於當前票**、
# 而且記在**它自己那個配對測試檔**(`tests/test_shadow_review.py`)上的紅燈。
# 紅燈記在本檔的話,R3 在前哨就會擋下對 `shadow_review.py` 的修改 ——
# 而它確實擋了一次(票 62 落地紀錄)。
#
# `verify_gates.py` 與 `g1_verify.py` **在**那份清單上(第 26 / 22 行),
# 所以它們兩支的測試留在本檔。
# ⇒ **三支的測試分兩處,而分界線是那份清單,不是我的判斷。**
