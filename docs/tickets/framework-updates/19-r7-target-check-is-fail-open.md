# 19 — R7 的目標檢查是 fail-open;provenance 只記寫入不記一致

## 一、R7:提到一個許可目標,整條指令就免檢(**fail-open**)

```python
for target, _why in BASH_ALLOWED_TARGETS.items():
    if target in cmd:
        return None
```

問的是「指令有沒有**提到**許可目標」,該問的是「**每一個**寫入目標都被許可嗎」。
判錯對象第七例。

實測(2026-08-13):

```
python x.py > out.txt 2>/dev/null      放行   ← 真的寫了 out.txt
rm -rf important_dir >/dev/null        放行
cp secret.env backup.env 2>/dev/null   放行
tee gate.py < evil 2>/dev/null         放行   ← 覆蓋閘門自己
```

**在任何指令後面加 `2>/dev/null` 就整條免檢。** 而抑制 stderr 是
每個人本來就有的習慣 —— 這不是要刻意繞才踩得到的洞,是日常寫法會誤觸的洞,
只是誤觸的方向是「被放行」,所以沒有人會發現。

### 下游回報的症狀在上游不成立

量化回報「`>/dev/null` 仍被判寫入」。上游實測**全部放行**
(`ls >/dev/null`、`> /dev/null`、`>/dev/null 2>&1`、`cd X && ls >/dev/null`)。
量化的 gate.py 落後(F-072 已記:它連 `-z` 都還沒有),那個症狀應該隨同步消失。
**真正要修的是反方向。**

### 修法

抽出**每一個**寫入目標,逐個檢查:

- 重導向:`>` / `>>` 後面那個 token 是目標
- 寫入指令(`rm` / `cp` / `mv` / `tee` / `touch` / `mkdir` / …):
  它的每一個路徑運算元都是目標
- **任何一個目標不在許可清單 → 擋**,並點名是哪一個(票 13 判準)
- 解析不出來 → **擋**(半套的解析器比零涵蓋更危險,所以不確定時往嚴的倒)

## 二、provenance 只記「這次寫了什麼」,不記「什麼與上游一致」

```python
write_provenance(src, target, plan.changed + plan.added, commit)
```

於是**從未需要更新的檔案拿不到證**:量化的 `g1_verify.py`、`shadow_review.py`
一直與上游相同,所以每一輪同步都不在 `changed + added` 裡,
從來沒有 provenance —— R3 一醒就紅,而且永遠不會自己好。

`verify_gates.py` 這輪是綠的,那是**巧合**:它剛好這輪有變。
一個靠「剛好有改」才成立的保證,不是保證。

### 修法

`copy` 桶的檔案,凡驗證與上游**逐位元組相同**一律發證,不論這輪有沒有寫過。
判準從「我寫了它」改成「它與上游一致」—— 後者才是 R3 要問的
(F-0014:與上游那個 commit 的物件逐位元組相同 ⇒ 紅燈責任在上游)。

負控:本地漂移的 copy 檔**不發證**。

### 補證模式(髒樹可跑)

量化需要在「把東西納入管理」之前先補證,而發證目前要求淨樹 ——
**發證與淨樹互為前提,死循環。**

補證模式只寫 `.dev/provenance.jsonl`,**不寫任何 repo 內容**,
所以 `refuse_if_dirty` 對它不適用:那道檢查的理由是
「在未提交的變更上覆寫,出事時分不出是誰改的」,而補證什麼都不覆寫。
判準仍是「與上游逐位元組相同」,漂移的檔案照樣不發證 —— 髒樹不會換來假證。

## 怎樣算做完

- `> out.txt 2>/dev/null` → 擋,且訊息點名 `out.txt`
- `>/dev/null` 單獨 → 放行(正控不得回歸)
- `rm -rf x >/dev/null` → 擋
- 未變更但與上游相同的 copy 檔 → 有 provenance
- 本地漂移的 copy 檔 → 沒有 provenance
- 補證模式在髒樹上跑得動,且不寫任何 repo 內容(逐位元組驗)
