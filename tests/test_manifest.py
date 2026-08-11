# -*- coding: utf-8 -*-
"""票 01 — 標記表的讀取(接縫 S1:逐檔的事實)。

只測讀取與「未標記 → copy」這條預設,不測安裝行為(S5 裁決:安裝由票 02 的
空 repo 實測完整涵蓋)。

貫穿全部斷言的一句話:**代價不對稱。**
多帶一個檔案是**吵鬧的** —— 到了新專案馬上發現不對;
少帶一個是**靜默的** —— 沒人知道少了一條規則。
所以每一個不確定的方向都往「帶」倒,而且要**出聲**。
"""

import importlib.util
import io
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "manifest_under_test", ROOT / ".claude" / "portable" / "manifest.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


manifest = _load()


@pytest.fixture
def table(tmp_path, monkeypatch):
    p = tmp_path / "portable-manifest.txt"
    monkeypatch.setattr(manifest, "MANIFEST", str(p))
    return p


def _write(p, text):
    io.open(p, "w", encoding="utf-8", newline="\n").write(text)


def test_an_explicit_mark_is_read(table):
    _write(table, "# 註解\n.agents/pipeline-stages.yaml  copy\n"
                  ".agents/legacy-no-redlight.txt  generate\nCLAUDE.md  ask\n")
    assert manifest.mark_for(".agents/pipeline-stages.yaml") == "copy"
    assert manifest.mark_for(".agents/legacy-no-redlight.txt") == "generate"
    assert manifest.mark_for("CLAUDE.md") == "ask"


def test_an_unmarked_path_defaults_to_copy(table):
    """沒標記不等於不帶 —— 那又是白名單。預設偏向多帶。"""
    _write(table, ".agents/pipeline-stages.yaml  copy\n")
    assert manifest.mark_for(".claude/hooks/gate.py") == "copy"


def test_unmarked_paths_are_reported_not_silently_defaulted(table):
    """套了預設就要出聲,讓人確認。靜默套用等於沒有標記表。"""
    _write(table, ".agents/pipeline-stages.yaml  copy\n")
    seen = manifest.unmarked([".agents/pipeline-stages.yaml",
                             ".claude/hooks/gate.py", "CLAUDE.md"])
    assert set(seen) == {".claude/hooks/gate.py", "CLAUDE.md"}


def test_a_missing_manifest_marks_everything_copy_and_reports_all(tmp_path, monkeypatch):
    """標記表不見了 —— 往吵鬧的方向倒:全部照帶,而且全部列出來。

    這裡的 fail-closed 不是「什麼都不帶」:少帶是靜默的,那才是危險的方向。
    """
    monkeypatch.setattr(manifest, "MANIFEST", str(tmp_path / "nope.txt"))
    assert manifest.mark_for("anything.py") == "copy"
    assert manifest.unmarked(["a.py", "b.py"]) == ["a.py", "b.py"]


def test_an_unknown_mark_is_an_error_not_a_silent_default(table):
    """標記打錯字不得退化成 copy。

    把一個該 generate 的檔案(例如豁免清單)照抄進新專案,看起來一切正常,
    實際上 R6 會拿別的 repo 的路徑去驗 —— 正是那種靜默壞掉。
    """
    _write(table, ".agents/legacy-no-redlight.txt  genrate\n")
    with pytest.raises(ValueError) as e:
        manifest.mark_for(".agents/legacy-no-redlight.txt")
    assert "genrate" in str(e.value)


def test_a_duplicate_entry_is_an_error(table):
    """同一路徑標兩次,行為就取決於讀取順序 —— 那是隱形的。"""
    _write(table, "CLAUDE.md  copy\nCLAUDE.md  ask\n")
    with pytest.raises(ValueError) as e:
        manifest.mark_for("CLAUDE.md")
    assert "CLAUDE.md" in str(e.value)


def test_skip_is_a_valid_mark_with_a_reason(table):
    """第四種標記:專案自己的檔案剛好住在框架目錄底下(例如 tests/ 裡的專案測試)。

    這不在原本的三種標記裡 —— 是把框架範圍寫成「根目錄 + 例外」之後才出現的:
    範圍用根目錄圈,範圍內預設 copy,**要留下不帶的必須明講**,而且要有理由。
    用 ask 表達會讓每次安裝都問一堆確定不是框架的東西。
    """
    _write(table, "tests/test_dataflows_config.py  skip\n")
    assert manifest.mark_for("tests/test_dataflows_config.py") == "skip"
    assert manifest.MARKS["skip"].strip(), "skip 沒有理由欄"


def test_a_directory_entry_covers_everything_under_it(table):
    """框架範圍用根目錄圈,不逐檔列 —— 逐檔列的話新增一個框架檔就會漏,
    而漏掉是靜默的。"""
    # 刻意不用 copy:預設就是 copy,拿它當斷言的話,前綴比對根本不存在也會綠 ——
    # 那是「綠燈掩蓋未實作」。
    _write(table, ".agents/skills/  ask\n")
    assert manifest.mark_for(".agents/skills/tdd/SKILL.md") == "ask"


def test_the_most_specific_entry_wins(table):
    """目錄標 copy、裡面某個檔標 skip —— 較長的前綴優先,不是讀取順序決定。

    順序決定的話,同一份標記表換個排法就換個行為,那是隱形的。
    """
    _write(table, "tests/  ask\ntests/test_dataflows_config.py  skip\n")
    assert manifest.mark_for("tests/test_gate.py") == "ask"          # 較短前綴
    assert manifest.mark_for("tests/test_dataflows_config.py") == "skip"  # 較長者勝


def test_a_path_outside_every_root_is_not_in_scope(table):
    """範圍之外的檔案不是「未標記所以 copy」,是**根本不是框架的東西**。

    未標記→copy 這條預設只在框架範圍**之內**成立;
    套到範圍外的話,安裝會把整個專案的原始碼一起搬過去。
    """
    _write(table, ".agents/  copy\n")
    assert manifest.in_scope(".agents/pipeline-stages.yaml") is True
    assert manifest.in_scope("tradingagents/graph/setup.py") is False


def test_every_file_under_tests_is_marked_or_explicitly_excluded():
    """`tests/` 底下每個檔案都要有標記,缺一個就紅。

    由來:三個框架測試(test_bash_write / test_gate_boundaries / test_g1_guard_draft)
    沒進標記表,**是靠鄰居清單抓到的**。而鄰居清單是啟發式的 ——
    它只列「跟框架檔同目錄」的東西,範圍定義一變就抓不到,
    而且抓不到時**不會出聲**。

    這條測試把它變成機器保證:`tests/` 是框架與專案測試混居的地方,
    每一個檔案都必須被明確歸類 —— `copy`(框架的)或 `skip`(專案的)。
    「沒被提到」不再是一個合法狀態。
    """
    tests_dir = ROOT / "tests"
    unclassified = []
    for p in sorted(tests_dir.rglob("*")):
        if p.is_dir() or "__pycache__" in p.parts:
            continue
        rel = p.relative_to(ROOT).as_posix()
        if not manifest.in_scope(rel):
            unclassified.append(rel)
    assert not unclassified, (
        "這些 tests/ 底下的檔案沒有標記,打包時會靜默漏帶或誤帶:\n  %s\n"
        "框架的標 copy,專案自己的標 skip —— 「沒被提到」不是合法狀態。"
        % "\n  ".join(unclassified))


def test_uncovered_neighbours_are_reported(table):
    """加上前綴範圍之後,「未標記但在範圍內」由構造為空 —— 那條確認清單成了廢話。

    真正會漏帶的是另一群:**跟框架檔住在同一個目錄、卻沒被任何根目錄涵蓋**的檔案。
    tests/ 底下同時住著框架的閘門測試與專案自己的測試,漏一個框架測試
    不會有任何人發現(少帶是靜默的)。所以那群要出聲。

    跟框架完全無關的目錄(整個目錄都不在範圍內)不列 —— 那會把整個專案印出來,
    吵到沒有人會讀,等於沒印。
    """
    _write(table, "tests/test_gate.py  copy\n.claude/hooks/  copy\n")
    out = manifest.uncovered_neighbours([
        "tests/test_gate.py",            # 涵蓋
        "tests/test_rank.py",            # 鄰居,未涵蓋 -> 要列
        ".claude/hooks/gate.py",         # 涵蓋
        "tradingagents/graph/setup.py",  # 完全無關的目錄 -> 不列
    ])
    assert out == ["tests/test_rank.py"], out
