# 74 — `.agents/skills/` 沒有 lock 檔,上游版本不可考

**狀態**:**candidate**(立案,不動工)
**立案**:2026-08-23,票 72 ② 的誠實一行
**來源**:票 72(THIRD_PARTY_NOTICES 要寫「取自哪一版」而寫不出來)

---

## 現象

`scripts/skills-update.sh` 走 `npx skills@latest update -y -p`,但 repo 裡**沒有** `skills-lock.json`
(根目錄、`.agents/`、`~/.agents` 都找過)。39 檔的來源 repo 確定(`mattpocock/skills`,MIT),
**來源 commit / 版本不確定**。`git log` 只能給「本 repo 何時收進來」,給不了「上游那時是哪一版」。

## 為什麼要緊

1. 第三方聲明寫不出版本,只能寫「不可考」—— 誠實,但對讀的人沒用。
2. R4/R5 守的是「鏡像與正典一致」「patch 還在」,**守不住「正典是從哪來的」**;
   `skills update` 靜默升級後,與上游的 diff 沒有基準可比。
3. 與 CI 「action 釘 40 位 sha,不釘標籤」同一原理:記確切位元組,不記會漂的名字。

## 候選處置(不裁)

- 查 `skills` CLI 是否支援 lock(`skills-lock.json` 是它的既有概念);支援就讓 wrapper 產生並進版控
- 不支援則在 `.agents/skills/UPSTREAM` 之類的一行檔手寫上游 commit,由 `skills-update.sh` 更新時要求填
- 回填:用現有 39 檔對上游歷史做內容比對,找出最接近的上游 commit,填入第一版
