# -*- coding: utf-8 -*-
"""票 114 刀一 B-4 —— 行尾正規化的**三端對帳**。

## 為什麼是三端,不是兩端

「內容比對前把行尾正規化」這條判準,本 repo 的生產碼有**三處**各自的字面
(票 114 步驟 0 的全庫掃描,2026-09-08,以 `7e46b85` 的樹為底):

  ① `.claude/hooks/redlight.py:56`   `content_hash`   —— R3 判紅燈對著哪份碼發生
  ② `.claude/portable/sync.py:100`   `_norm`          —— sync 的 copy 桶分流與寫後重驗
  ③ `.claude/portable/sync.py:377`   `_read`          —— canon_drift 的正典段漂移判定

**同缺陷的三份實作必然漂開**(`F-058` 家族),而漂開的那天不會有東西說話:
③ 守的是下游 `CLAUDE.md` 正典段的**拒絕條件**,它判錯的樣子是一次看起來成功的同步。

**兩份實作一個字都不改**(票 114 裁決甲 = B2)。這條測試綁的是**行為一致**,
不是字面相同 —— 與 `tests/test_gate.py::TestBothHeadingCriteriaAgree` 同型。

## ⚠ 三端不同質:哪一端釘使用端、哪一端只能釘定義端

**判準要釘在使用端,不是釘在定義端**(票 42 原句)。所以:

  `sync.file_hash`    ← ② 的**使用端**。sync/status/user_layer 實際呼叫的就是它
  `gate._hash_bytes`  ← ① 的**使用端**。gate 實際呼叫的就是它

**而 ③ 只能釘定義端,這是刻意的**:`_read` 的使用端是 `canon_drift`,
而 `canon_drift` 在 `_read` 之後**還做正典段抽取**(`HYBRID` 表的 `extract`),
把它拉進來的話,這條測試就變成在測界線標記的解析,不是在測行尾正規化 ——
**一條檢查一件事**,混進第二個子判定,整條的可信度就跟著它走。
代價說清楚:`_read` 哪天不再被 `canon_drift` 呼叫,本檔照樣綠。
那個風險由 `_read` 只有一個呼叫端(`sync.py:411`)壓著,不是由本檔壓著。

## ⚠ 邊界:③ 在字元層正規化,①② 在位元組層

`_read` 先 `f.read().decode("utf-8")` **再** replace —— 字元層;
①② 直接對 `bytes` replace —— 位元組層。

**UTF-8 底下兩者等價**:`\r`(U+000D)與 `\n`(U+000A)在 UTF-8 是單位元組
`0x0D` / `0x0A`,且不會出現在任何多位元組序列的後續位元組裡(那些一律 ≥ 0x80)。
所以「先 decode 再換」與「直接換位元組」在可 UTF-8 解碼的輸入上結果相同。

**非 UTF-8 輸入不等價**:`_read` 會丟 `Refused`(它把解碼失敗當成「判不了就停」),
而 ①② 照樣回一個雜湊。**所以本檔的語料限定為可 UTF-8 解碼的位元組。**
**這是妥協聲明,不是遺漏** —— 三端在非 UTF-8 輸入上本來就不同意,
而那個差異是 `_read` 刻意的 fail-closed,不是漂移。

## 同判準的其他副本(本票不動,但要可搜尋)

`tests/` 底下另有兩處**逐字正確**的同判準副本,票 114 裁決乙1 判定本票不動它們:

  `tests/test_gate.py:1525`  `_head_hash`      —— 替 R3 測試自己算 HEAD blob 雜湊
  `tests/test_gate.py:2588`  `_sub_head_hash`  —— 同上,submodule 那一組

第三處 `tests/test_sync.py:71` 的 `_h` **當時已經漂開**(只做 `\r\n`→`\n`,
漏掉 `\r`→`\n`),而它是 `test_sync.py` 十餘條斷言的判準來源;
票 114 步驟 3 已把它改成呼叫 `sync.file_hash`。
"""

import hashlib
import importlib.util
import io
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load(name, *parts):
    """兩側都用路徑載入。寫法抄 `tests/test_gate.py:336-343`。

    `import sync` / `import redlight` 在這裡會 ImportError —— 那兩個目錄
    不在 `sys.path` 上。而那種失敗會讓本檔**整個收不到**,
    收不到的樣子跟「沒有這條對帳」一模一樣。
    """
    spec = importlib.util.spec_from_file_location(name, ROOT.joinpath(*parts))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sync = _load("sync_for_parity", ".claude", "portable", "sync.py")
gate = _load("gate_for_parity", ".claude", "hooks", "gate.py")


# 六種行尾輸入。**全部可 UTF-8 解碼**(見上方邊界聲明)。
CORPUS = [
    ("CRLF",        b"a\r\nb\r\nc\r\n"),
    ("LF",          b"a\nb\nc\n"),
    ("CR",          b"a\rb\rc\r"),
    ("mixed",       b"a\r\nb\nc\rd\n\r\ne"),
    ("no-trail-nl", b"a\r\nb"),
    ("empty",       b""),
]


def _spill(tmp_path, raw):
    """把語料寫成一個真的檔案。**`newline` 不介入 —— 走二進位。**

    用文字模式寫的話,Python 會替我們翻譯行尾,語料裡的 `\\r` 就到不了被測的碼,
    而測試會**因為錯的理由**而綠(`F-032`)。
    """
    tmp_path.mkdir(parents=True, exist_ok=True)
    p = tmp_path / "probe.txt"
    with io.open(str(p), "wb") as f:
        f.write(raw)
    return p


def _end_file_hash(tmp_path, raw):
    """② 的使用端:`sync.file_hash`(內部走 `_norm`)。"""
    return sync.file_hash(str(_spill(tmp_path, raw)))


def _end_hash_bytes(tmp_path, raw):
    """① 的使用端:`gate._hash_bytes`(內部走 `_redlight().content_hash`)。"""
    return gate._hash_bytes(raw)


def _end_read(tmp_path, raw):
    """③ 的定義端:`sync._read`。它回的是正規化後的**全文**,不是雜湊。

    所以這裡自己補 sha256,好讓三端的回傳值可比。
    `.encode("utf-8")` 是把它換回位元組 —— 不是第四份正規化,
    這一步不碰任何 `\\r` / `\\n`。
    """
    text = sync._read(str(_spill(tmp_path, raw)), u"來源", u"probe.txt")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


ENDS = [
    ("sync.file_hash", _end_file_hash),
    ("gate._hash_bytes", _end_hash_bytes),
    ("sync._read+sha256", _end_read),
]


def _disagreements(ends, tmp_path):
    """三端對同一筆語料給出不同答案的那些。回 [(語料名, {端名: 值}), ...]。

    **回清單不回布林**:擋下訊息要說得出**是哪一筆語料、哪一端**不同,
    否則紅燈只說「不一致」,而人要自己重跑一遍才知道往哪裡看。
    """
    out = []
    for name, raw in CORPUS:
        got = {}
        for end_name, fn in ends:
            got[end_name] = fn(tmp_path / name.replace("/", "_"), raw)
        if len(set(got.values())) > 1:
            out.append((name, got))
    return out


class TestTheParityCheckItselfCatchesADriftedEnd:
    """**反控甲:先證明這個對帳真的會咬。**

    形狀抄 `tests/test_portable_output_encoding.py::TestTheHarnessItselfRejectsTheMark`
    那一層(引 `F-103`)。少了它,底下的對帳只是一句「三邊相等」的宣稱 ——
    它可能因為**任何**理由恆真(語料分辨不出行尾、三端其實是同一個物件、
    斷言寫錯方向),而**恆真的斷言與有效的斷言在測試輸出上長得一模一樣**。

    做法:拿一份**刻意不做行尾正規化**的假實作當第三端,斷言對帳**必須**抓到它。
    """

    @staticmethod
    def _drifted(tmp_path, raw):
        """假的一端:直接 sha256,不正規化行尾。"""
        return hashlib.sha256(raw).hexdigest()

    def test_a_non_normalising_end_is_caught(self, tmp_path):
        ends = [ENDS[0], ENDS[1], ("drifted(不正規化)", self._drifted)]
        bad = _disagreements(ends, tmp_path)
        assert bad, (
            "拿一份公認不正規化的實作當第三端,對帳竟然一個差異都沒抓到 —— "
            "那代表這組語料分辨不出行尾,對帳斷言是恆真的")

    def test_the_corpus_actually_separates_line_endings(self, tmp_path):
        """**歸因要對**:上一條抓到的必須是**行尾**,不是別的東西。

        少了這一條,一組全是 `LF` 的語料也會讓上一條綠 —— 因為
        `drifted` 對**任何**輸入都可能碰巧不同。這裡直接證明語料裡有
        CRLF/CR,而它們在正規化之後應當收斂成同一個值。
        """
        crlf = dict(CORPUS)["CRLF"]
        lf = dict(CORPUS)["LF"]
        cr = dict(CORPUS)["CR"]
        assert crlf != lf and cr != lf, "語料的三種行尾在位元組層必須不同"
        naive = {self._drifted(tmp_path, r) for r in (crlf, lf, cr)}
        assert len(naive) == 3, (
            "不正規化的實作對這三筆給出相同的雜湊 —— 那代表語料選錯了,"
            "上一條抓到的不會是行尾")


class TestAllThreeNormalisersAgree:
    """**三端對同一組輸入必須給出相同答案。** 綁行為,不綁字面。

    不一致代表有一端在做另外兩端以為它沒做的事 —— 而那件事的後果各不相同:
    ① 漂掉 ⇒ R3 對既有檔案誤判;② 漂掉 ⇒ sync 誤搬或誤判「沒動到」;
    ③ 漂掉 ⇒ `canon_drift` 對下游 `CLAUDE.md` 的正典段判錯,
    而它判錯的樣子是**一次看起來成功的同步**。
    """

    def test_the_three_ends_agree_on_every_corpus_entry(self, tmp_path):
        bad = _disagreements(ENDS, tmp_path)
        assert not bad, (
            "三份行尾正規化對同一筆輸入給出不同答案(%d 筆語料不一致):\n  %s\n"
            "同缺陷的三份實作必然漂開(F-058 家族)。三處分別是:\n"
            "  ① .claude/hooks/redlight.py content_hash\n"
            "  ② .claude/portable/sync.py  _norm(經 file_hash)\n"
            "  ③ .claude/portable/sync.py  _read(經 canon_drift)"
            % (len(bad),
               "\n  ".join("%s -> %s" % (name, got) for name, got in bad)))

    @pytest.mark.parametrize("name,raw", CORPUS)
    def test_each_entry_separately_so_the_red_names_the_input(
            self, tmp_path, name, raw):
        """逐筆再跑一次 —— **紅燈要指出是哪一種行尾**。

        上一條回報全部,這一條讓 pytest 的測試名字本身就是答案:
        `[CR]` 紅而別的綠,不必讀訊息就知道漏的是 `\\r` 那一步。
        """
        got = {n: fn(tmp_path, raw) for n, fn in ENDS}
        assert len(set(got.values())) == 1, "%s:%s" % (name, got)

    def test_the_three_ends_are_not_the_same_object(self):
        """**反控:三端必須真的是三個不同的可呼叫物。**

        少了這一條,有人把 `ENDS` 寫成同一個函式三次,上面兩條會恆真 ——
        而那正是「綠的原因不是你以為的」(`F-032`)。
        """
        fns = [fn for _, fn in ENDS]
        assert len({id(f) for f in fns}) == 3, "三端指到同一個物件"
        assert sync.file_hash is not gate._hash_bytes

    def test_equivalent_line_endings_actually_collapse(self, tmp_path):
        """**歸因要對**:三端相等要是因為**都正規化了**,不是因為都沒動。

        CRLF / LF / CR 三筆語料在位元組層不同,正規化之後應當收斂成同一個值。
        少了這一條,三端全部改成「原樣 sha256」也會讓上面全綠。
        """
        for end_name, fn in ENDS:
            vals = {fn(tmp_path / end_name.replace(".", "_"), raw)
                    for raw in (dict(CORPUS)["CRLF"],
                                dict(CORPUS)["LF"],
                                dict(CORPUS)["CR"])}
            assert len(vals) == 1, (
                "%s 沒有把 CRLF / LF / CR 收斂成同一個值:%s" % (end_name, vals))
