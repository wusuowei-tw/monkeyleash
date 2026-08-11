# -*- coding: utf-8 -*-
"""紅燈紀錄 —— 讓「這個測試曾經紅過」不再只是宣稱。

R3 的原始規格是「對應測試檔存在 **且** 有紅燈紀錄」,實作只做了前半,
而且沒有任何東西發現它掉了(F-012)。只驗檔案存在的話,一個永遠跑不起來的
測試檔也能過關 —— 上一輪就是這樣:repo 有十七個測試檔而測試執行器根本沒安裝。

**時序判準不用任何時間戳。** 要問的不是「檔案何時出現」,而是
「紅燈發生時,這個實作存不存在」—— 那件事在紅燈那一刻可以直接觀測,不必事後推斷。
檔案系統時間會被複製與觸碰打亂、會被時鐘回撥影響,版控時間對未提交的新檔根本不存在;
兩者都在回答錯的問題。所以紀錄自己宣告當時實作存不存在,並記下雜湊。

紀錄是**證據**(消失即失去判定依據),放 .dev/ 並進版控;append-only,不覆寫 ——
覆寫會讓歷史消失,而斷言需要歷史。
"""

import hashlib
import io
import json
import os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUN_LOG = os.path.join(ROOT, ".dev", "test-runs.jsonl")

# 測試檔名對應到實作檔名的搜尋範圍。與 R3 反向:R3 由實作找測試,這裡由測試找實作。
#
# 跳過清單是**明列**的,不是「所有點開頭的目錄」—— 後者會跳過 .claude/hooks/,
# 而閘門自己就住在那裡:實作明明存在,紀錄卻宣告 impl_exists=False,
# R3 拿這種紀錄去判定會無條件放行。又是一次「以錯的來源決定可見範圍」(F-019)。
_SEARCH_SKIP = {".git", ".venv", "node_modules", "__pycache__", ".cache",
                ".scratch", ".dev", "tests", "docs", ".agents", "skills",
                "build", "logs", "assets", "tradingagents.egg-info"}


def find_implementation(test_file):
    """tests/test_foo.py -> 專案裡的 foo.py。找不到回 None。

    找不到不是錯誤:測試檔可以不對應單一實作(例如整合測試)。
    R3 只在「由實作反查」時才需要這個對應,方向相反時允許落空。
    """
    base = os.path.basename(test_file)
    if not base.startswith("test_") or not base.endswith(".py"):
        return None
    target = base[len("test_"):]
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in _SEARCH_SKIP]
        if target in filenames:
            return os.path.relpath(os.path.join(dirpath, target), ROOT).replace("\\", "/")
    return None


def record_run(test_file, passed, failed_tests):
    """追加一筆紀錄。回傳寫入的內容(方便呼叫端斷言)。"""
    impl = find_implementation(test_file)
    impl_path = os.path.join(ROOT, impl.replace("/", os.sep)) if impl else None
    exists = bool(impl_path and os.path.exists(impl_path))

    digest = None
    if exists:
        try:
            digest = hashlib.sha256(io.open(impl_path, "rb").read()).hexdigest()
        except Exception:
            digest = None

    rec = {
        "test_file": test_file.replace("\\", "/"),
        "time": datetime.now(timezone.utc).isoformat(),
        "result": "green" if passed else "red",
        "failed_tests": list(failed_tests or []),
        # 在事件當下留下的事實,不是事後從時間戳推斷出來的
        "impl_file": impl,
        "impl_exists": exists,
        "impl_hash": digest,
    }
    try:
        os.makedirs(os.path.dirname(RUN_LOG), exist_ok=True)
        with io.open(RUN_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return rec
