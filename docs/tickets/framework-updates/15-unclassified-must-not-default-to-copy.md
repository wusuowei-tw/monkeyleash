# 15 — 更新路徑不得把「未分類」當成「照抄」

## 下游攔到的(影音第三輪 dry-run,2026-08-13)

sync 將覆蓋目標 repo 的六個根目錄檔:

```
README.md  pyproject.toml  .gitignore  .gitattributes
bootstrap.sh  .githooks/pre-commit
```

其中 `.githooks/pre-commit` 會從**三層掛載降成只剩 leak_scan** ——
**權威層靜默消失**。沒有任何訊息會說這件事:hook 還在、還會跑、還會擋洩漏,
只是不再呼叫 `gate.py --pre-commit`。這正是 ADR 0007 說的那個缺口的最壞版本:
不是沒裝,是**裝過又被拆掉**,而拆掉的動作看起來像一次成功的更新。

## 根因:批次二把兩份實作合一時,順手換掉了預設值

`79bfe22` 為了消滅 F-058(同一件事兩份實作),讓 `sync.mark_for` 改呼叫
`manifest.mark_in`。兩者對**沒有命中任何前綴**的檔案處置不同:

| | 未命中任何前綴時 |
|---|---|
| 舊 `sync.mark_for` | 回 `None`,而 `None != "copy"` → **跳過** |
| `manifest.mark_in` | 回 `DEFAULT_MARK`,也就是 **`"copy"`** → **覆蓋** |

實測 `.agents/portable-manifest.txt` 目前有 **8 筆**未分類檔案
(上列六筆,加上 `docs/agents/adr-numbering.md`、`docs/machine-init.md`)。

**「未標記 → copy」這個預設在安裝器是對的,在更新路徑是災難。**
安裝器有兩道護欄讓那個預設安全:

1. `classify()` 先過 `in_scope()`,範圍外的檔案根本不進任何桶
2. 未涵蓋的鄰居會被列出來讓人確認(`uncovered_neighbours`)

**我把分類器搬過去,沒把讓它安全的那兩道搬過去。** 更新路徑既沒有範圍過濾,
也沒有人確認的環節,而它的寫入對象是**別人 repo 裡已經存在的檔案**。
同一個預設,兩邊的風險方向相反:
安裝器裡「多帶」是吵鬧的(空 repo,看得到);更新路徑裡「多帶」是**覆蓋**,
而覆蓋是靜默的。

## 範圍

1. 八筆未分類檔案在 manifest 明列。六個根目錄檔標 `skip`
   (各 repo 自己的檔案,上游同名檔只屬於上游自己);
   `adr-numbering.md` 與 `machine-init.md` 標 `copy`(框架知識,會旅行)。
2. **sync 遇到未分類檔案一律 fail-closed 拒絕**,並點名是哪個檔、
   缺的是哪個前提(票 13 的判準)。不再有「預設」這回事 ——
   `manifest` 提供一個不帶預設的查詢,預設由各呼叫端**明確**選擇。
3. 以測試釘死:未標記檔 → 拒絕;負控:明列 `skip` 後 → 不碰、逐位元組不變。

## 怎樣算做完

- 上游 `git ls-files` 的每一筆都有明確標記,一筆未分類都沒有
- 塞一個沒標記的檔案進來源 → sync 拒絕,訊息點名該檔
- 那個檔案標 `skip` 之後 → sync 通過,且目標的同名檔逐位元組不變
- 安裝器的「未標記 → copy」語意不變(它有 `in_scope` 與人確認兩道護欄)
