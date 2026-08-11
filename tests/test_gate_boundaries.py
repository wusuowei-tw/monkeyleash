# -*- coding: utf-8 -*-
"""閘門的邊界:例外處置、跨行程編碼、進入點解析。

三件事的共同根源是 F-042:`except Exception: return 0` 把
「我不懂發生什麼事」翻譯成「沒事」,而前哨層因此整輪靜默失效。

**閘門裡的例外只有兩種正確處置:擋下、或明確記錄後擋下。沒有一種是放行。**

`mode_hook()` 的 payload 解析在這裡補測 —— 它先前被歸類為「進入點分派,不測」,
兩次都以「只是接線」為由跳過,而那條接線裡藏著整個系統最要命的一行。
**判準修正:進入點若包含解碼、解析、格式轉換,它就不是接線。**
接線是把 A 傳給 B;一旦中間有轉換,它就是有行為的程式碼,要測。
"""

import importlib.util
import io
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load_gate():
    spec = importlib.util.spec_from_file_location(
        "gate_boundaries", ROOT / ".claude" / "hooks" / "gate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gate = _load_gate()


class TestExceptionsNeverAllow:
    """三個實際存在過的 fail-open 位置。"""

    def test_a_spec_that_cannot_be_read_is_blocked_not_allowed(
            self, tmp_path, monkeypatch):
        """R1 讀不到規格書內容時原本 `return None`(放行)。

        commit 時 content 是 None、由 gate 自己從磁碟讀 —— 讀失敗就等於
        「規格書裡有沒有程式碼」這個問題沒被回答,而沒被回答不等於答案是「沒有」。
        """
        # 路徑要給絕對的:`rel()` 走 abspath,相對路徑會以 cwd 為基準而不是 ROOT,
        # 結果變成 `../..` 開頭而被「repo 外不管」那條提早放行(F-043 的修正)。
        monkeypatch.setattr(gate, "ROOT", str(tmp_path))   # 檔案不存在於此
        msg = gate.check(str(tmp_path / ".scratch" / "f" / "spec.md"), None)
        assert msg and "R1" in msg, "規格書讀不到卻放行(fail-open):%r" % msg

    def test_an_unreadable_pipeline_blocks_at_commit_too(self, tmp_path, monkeypatch):
        """`load_stage()` 讀不到時原本回 `("idle", None)`。

        寫入時 idle 不可寫 → 擋下(看起來沒問題);
        **但提交時 idle 是刻意放行的**(ADR 0005),於是 pipeline.json 壞掉或被刪,
        R2 在提交時就無條件通過。「不知道停在哪一站」被翻譯成「停在 idle」。
        """
        monkeypatch.setattr(gate, "PIPELINE", str(tmp_path / "gone.json"))
        stage, _ = gate.load_stage()
        assert stage != "idle", "讀不到流程狀態卻回報 idle —— 那是猜,不是讀"
        msg = gate.check("macro_audit/thing.py", "x = 1", at_commit=True)
        assert msg and "R2" in msg, "流程狀態讀不到卻放行提交(fail-open):%r" % msg

    def test_a_failed_exemption_record_blocks_the_exemption(self, tmp_path, monkeypatch):
        """豁免記帳寫不進去時原本 `pass` —— 豁免照給,紀錄沒了。

        豁免的正當性建立在「它被記錄下來、可被逐筆對帳」上面(ADR 0004/0006)。
        記錄失敗還照給,等於給了一個**沒有人看得到**的豁免。
        """
        monkeypatch.setattr(gate, "EXEMPTION_LOG", str(tmp_path / "nodir" / "x.jsonl"))
        monkeypatch.setattr(gate, "_append_jsonl",
                            lambda *a, **k: (_ for _ in ()).throw(IOError("磁碟滿了")))
        with pytest.raises(SystemExit):
            gate.log_exemption("macro_audit/x.py", "x", "01", "票 01")


class TestCrossProcessEncodingIsExplicit:
    """跨行程邊界不得依賴平台預設編碼(F-042)。

    這條測的是**原始碼裡的寫法**,不是行為 —— 因為行為只有在
    cp950 主控台 + 非 ASCII payload 同時出現時才會壞,而 CI 或別台機器上測不出來。
    測寫法可以在任何機器上成立。
    """

    SOURCES = {
        "gate.py": ROOT / ".claude" / "hooks" / "gate.py",
        "redlight.py": ROOT / ".claude" / "hooks" / "redlight.py",
    }

    @staticmethod
    def _calls(path):
        """用 AST 列出呼叫,**不用正則掃文字**。

        第一版用文字比對,結果打到註解裡引用的那段字串 —— 測試自己在說謊。
        要檢查程式的性質就得看程式的結構,不是看它的字面。
        """
        import ast
        tree = ast.parse(io.open(path, encoding="utf-8").read())
        out = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                out.append((node, ast.unparse(node.func),
                            {k.arg for k in node.keywords}, node.args))
        return out

    @pytest.mark.parametrize("name", sorted(SOURCES))
    def test_stdin_is_read_as_bytes_and_decoded_explicitly(self, name):
        import ast
        bad = []
        for node, func, _kw, args in self._calls(self.SOURCES[name]):
            if func == "json.load" and args and "stdin" in ast.unparse(args[0]):
                bad.append(node.lineno)
        assert not bad, (
            "%s 第 %s 行用 json.load(sys.stdin):Windows 上會用主控台編碼解 "
            "UTF-8 payload,中文路徑當場壞掉(F-042)" % (name, bad))

    @pytest.mark.parametrize("name", sorted(SOURCES))
    def test_every_file_open_names_its_encoding(self, name):
        import ast
        bad = []
        for node, func, kw, args in self._calls(self.SOURCES[name]):
            if func not in ("io.open", "open"):
                continue
            mode = args[1].value if len(args) > 1 and isinstance(args[1], ast.Constant) else "r"
            if "b" not in str(mode) and "encoding" not in kw:
                bad.append(node.lineno)
        assert not bad, "%s 第 %s 行的 open 沒寫 encoding" % (name, bad)

    @pytest.mark.parametrize("name", sorted(SOURCES))
    def test_subprocess_output_is_decoded_explicitly(self, name):
        src = io.open(self.SOURCES[name], encoding="utf-8").read()
        assert "universal_newlines=True" not in src, (
            "%s 用 universal_newlines:那會用平台預設編碼解 subprocess 輸出" % name)
        assert ", text=True" not in src, (
            "%s 用 text=True:同樣依賴平台預設編碼" % name)


class TestEntryPointParsing:
    """進入點若包含解碼 / 解析 / 格式轉換,它就不是接線(S6 判準修正)。

    語料含**中文路徑與非 ASCII**,因為壞掉的正是那個情況 ——
    只用 ASCII 語料測,這個缺陷永遠不會現身。
    """

    @staticmethod
    def _payload(command):
        return {
            "session_id": "x", "hook_event_name": "PreToolUse",
            # 合成路徑,含 CJK 是刻意的 —— 這裡驗的就是 utf-8 payload 解碼(F-042)。
            "cwd": "C:\\Users\\someone\\專案\\目標倉庫",
            "tool_name": "Bash",
            "tool_input": {"command": command, "description": "測試"},
        }

    def test_a_utf8_payload_with_chinese_paths_parses(self, monkeypatch):
        """實際壞掉的那一個形狀:合法 UTF-8、含中文路徑、含 Windows 反斜線。"""
        raw = json.dumps(self._payload("echo x > 筆記.txt"),
                         ensure_ascii=False).encode("utf-8")
        got = gate.parse_hook_payload(raw)
        assert got["tool_name"] == "Bash"
        assert "筆記" in got["tool_input"]["command"]

    def test_an_ascii_only_payload_still_parses(self):
        raw = json.dumps(self._payload("echo x > notes.txt")).encode("utf-8")
        assert gate.parse_hook_payload(raw)["tool_input"]["command"].endswith("notes.txt")

    def test_broken_input_raises_instead_of_returning_empty(self):
        """壞掉的輸入必須讓呼叫端擋下,不能回一個空的 payload 讓它「沒事發生」。"""
        with pytest.raises(Exception):
            gate.parse_hook_payload(b"{not json")

    def test_the_payload_shape_is_the_one_actually_observed(self):
        """對照基準:2026-08-10 從真實 PreToolUse 抓到的頂層鍵。

        形狀變了要有人知道 —— 而不是靠 payload_text 回空字串然後靜默放行。
        """
        raw = json.dumps(self._payload("ls")).encode("utf-8")
        got = gate.parse_hook_payload(raw)
        for key in ("tool_name", "tool_input", "cwd", "hook_event_name"):
            assert key in got, "缺少實際觀測到的鍵:%s" % key
