# -*- coding: utf-8 -*-
"""測試不得寫進宿主的真實證據檔(票 18)。

由來(量化實測):框架測試把合成的 fixture 條目寫進宿主真實的 `shadow-log`,
4 筆變 13 筆。**證據檔是閘門的判定依據** —— shadow-log 決定影子模式要不要晉升,
`test-runs.jsonl` 決定 R3 的紅燈半。往裡面寫測試造的假紀錄,
等於讓測試去改變閘門**之後**的判斷。

而且它會讓一個已經記錄在案的量測再偏一次:F-072 說影子期的樣本因上游缺陷而偏,
「晉升門檻的樣本在同步完成前不算數」。合成條目往同一個方向再推 ——
fixture 造的多半是乾淨的假陽性,所以誤擋率會看起來比實際好。

`test-runs.jsonl` 不在本檔範圍:紅燈紀錄是紀錄器在每次**真實執行**後追加的,
那是機制的正常產出。分辨兩者的判準是
**「這筆紀錄描述的事情有沒有真的發生」**,不是「誰寫的」。
"""

import glob
import hashlib
import importlib.util
import io
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

# 紅燈紀錄由紀錄器在真實執行後追加,是機制的正常產出,不是污染。
EXPECTED_TO_GROW = {"test-runs.jsonl"}

EVIDENCE_FIELDS = ("SHADOW_LOG", "SHADOW_STATE", "EXEMPTION_LOG", "PROVENANCE")


def _load():
    """**模組層載入**,不是在測試裡載。

    conftest 的隔離 fixture 在每條測試 setup 時走訪 `sys.modules`,
    所以只蓋得到那時候已經載入的。在測試函式裡才載的那份不會被蓋 ——
    而那正是這個檔案要驗的東西,拿一份蓋不到的來驗等於什麼都沒驗。
    """
    spec = importlib.util.spec_from_file_location(
        "gate_for_evidence_test", ROOT / ".claude" / "hooks" / "gate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gate = _load()


def _digest(path):
    return hashlib.sha256(io.open(path, "rb").read()).hexdigest()


def _evidence_files():
    return sorted(p for p in glob.glob(str(ROOT / ".dev" / "*.jsonl"))
                  if os.path.basename(p) not in EXPECTED_TO_GROW)


def test_the_isolation_fixture_redirected_this_module():
    """autouse fixture 有沒有真的接上 —— 接線要測(F-044)。"""
    for name in EVIDENCE_FIELDS:
        value = getattr(gate, name).replace("\\", "/")
        assert "/.dev/" not in value, "%s 仍指向 repo 的 .dev/:%s" % (name, value)


def test_every_loaded_gate_is_redirected():
    """各測試檔各載一份 gate,只改一個沒有用 —— 每一份都要被蓋到。

    **第一版的 fixture 走訪 `sys.modules`,而那是空轉的**:
    `module_from_spec` + `exec_module` 不會把模組註冊進 `sys.modules`。
    是這條測試把它抓出來的 —— 一條「接線有沒有接上」的測試,
    抓到的正是「接線根本沒接上」。
    """
    import sys
    sys.path.insert(0, str(ROOT / "tests"))
    from conftest import _loaded_gate_modules          # noqa: E402
    loaded = _loaded_gate_modules()
    assert loaded, "一份 gate 都沒載入 —— 這條測試沒有在測任何東西"
    for mod in loaded:
        for name in EVIDENCE_FIELDS:
            if hasattr(mod, name):
                value = getattr(mod, name).replace("\\", "/")
                assert "/.dev/" not in value, (
                    "%s.%s 仍指向 repo 的 .dev/" % (mod.__name__, name))


def test_shadow_is_deterministically_off_during_tests():
    """影子在測試中恆為關 —— 結果不得取決於宿主 repo 碰巧開沒開。

    量化那邊兩條測試因為宿主開著影子而永久紅,而永久紅是萬能鑰匙(F-071)。
    影子開的那個方向由 tests/test_shadow.py 自己開,成對驗。
    """
    assert gate.shadow_active() is False


def test_a_blocked_judgement_does_not_touch_host_evidence():
    """**負控**:走一次會落到證據路徑的判定,宿主檔案逐位元組不變。

    這條在測試集合裡有先天限制:它只看得到自己這一輪。
    真正的守法是外部比對(跑全套件前後各算一次 hash),寫在票 18 的驗收裡。
    這裡釘的是它能釘的那半。
    """
    before = {p: _digest(p) for p in _evidence_files()}
    assert before, ".dev/ 底下沒有證據檔可驗 —— 空的綠燈不算綠燈"
    gate.check(".claude/hooks/gate.py", "x = 1")          # 走 GATE_SELF 豁免路徑
    gate.log_shadow("[R3] probe.py:測試用", at_commit=False)
    for path, digest in before.items():
        assert _digest(path) == digest, "%s 被測試改到了" % path
