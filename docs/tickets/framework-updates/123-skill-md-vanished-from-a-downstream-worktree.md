# 票 123 —— 影音下游的 `.agents/skills/code-review/SKILL.md` 從工作區消失

**狀態**:立案。**本票今日只立案,未動工。**
**發現於**:2026-09-09,筆電(hostname `14X`),上游 HEAD `63cd0fa`。
**受影響 repo**:`analyst-tracker`(影音下游),工作區位於 OneDrive 底下,HEAD `562e4ef`。

## 現象

該下游的工作區裡 `.agents/skills/code-review/SKILL.md` **不存在**,
而它**在 HEAD 裡**。`git status` 因此報一筆 ` D`(已刪除、未提交)。

同一個目錄底下的 `agents/openai.yaml` **還在**。
所以形狀是:**目錄還在、目錄裡的附屬檔還在,只有 `SKILL.md` 這一支不見了。**

## 證據(今日原始輸出)

工作區狀態(這一條要帶 `--untracked-files=no`,理由見票 125):

```
$ git -C "<影音>" status --porcelain --untracked-files=no
 D .agents/skills/code-review/SKILL.md
 M .dev/intercepts-2026-09.jsonl
 M .dev/pipeline.json
```

版控史 —— **只有安裝那一顆碰過它**:

```
$ git -C "<影音>" log --oneline -3 -- .agents/skills/code-review/SKILL.md
5e930af 裝上六站閘門(框架安裝)
```

檔案確實在 HEAD 裡:

```
$ git -C "<影音>" cat-file -e HEAD:.agents/skills/code-review/SKILL.md && echo "HEAD 裡有這個檔"
HEAD 裡有這個檔
```

目錄現況:

```
$ ls -lR --numeric-uid-gid "<影音>/.agents/skills/code-review/"
<影音>/.agents/skills/code-review/:
total 0
drwxr-xr-x 1 197609 197609 0 Aug 11 19:44 agents

<影音>/.agents/skills/code-review/agents:
total 4
-rw-r--r-- 1 197609 197609 103 Aug 11 19:18 openai.yaml
```

本段為 `Wed Sep  9 09:02:49     2026` 重跑;上方其餘量測為本日稍早,兩次時點不同,期間未對該目錄做任何寫入。

> **這一段哪裡是逐字、哪裡不是**(`F-151`:先問這一行是【資料】還是【關於資料的說明】):
> **資料列逐字**(mode / uid / gid / size / mtime / 名稱皆為重跑原文,未手改任何欄位);
> **兩行路徑標頭的前綴被縮寫成 `<影音>`** —— 原文是絕對路徑,而它含使用者名,
> 那是受守的個人識別。縮的是**路徑前綴**,不是列的內容。
>
> 第一次量測用的是 `ls -lR`(不帶旗標),輸出的擁有者欄帶使用者名,
> 因此**被權威層的洩漏偵測擋在 commit 之前**;本段是換旗標重跑的結果,
> **不是把欄位手改掉的** —— 手改會讓一段「關於資料的說明」長得像資料。

## 為什麼要緊

`code-review` **是 R5 直接點名的那一支**(「正典 `code-review` 缺第三軸掛載點
(patch 未重套)→ 擋」),同時也在 R4 的守備範圍(`.claude/skills/` 或 `skills/`
的 SKILL.md 與正典 `.agents/skills/` 不一致 → 擋)。

而現在的形狀是 **「目錄還在,守的東西不見了」** ——
這正是本 repo 反覆記錄的那一族:一個看起來完整的結構,
而它宣稱要守的東西已經不在裡面,**沒有東西會說話**。

`agents/openai.yaml` 還在這件事讓它更難被看見:目錄非空,
任何「檢查目錄在不在」層級的判定都會過。

## 未證明(今日一件都沒查)

- **它是怎麼消失的。** 四個候選 —— 手動刪、工具刪、OneDrive 同步事故、
  `skills update` 覆蓋 —— **一個都沒查**,四個都只是候選,不是假說排序。
- **它消失多久了。** 目錄 mtime `Aug 11 19:44` 是**目錄**的時間,不是刪除事件的時間;
  `agents/openai.yaml` 的 `Aug 11 19:18` 同理。**沒有比對過任何其他時間來源。**
- **有沒有東西因此紅過。** R4 / R5 理應對這件事有反應,
  但**今天沒有在那個 repo 上跑過任何閘門或測試**。
  「沒有東西說話」目前是**觀察不到,不是已證明不存在**。
- **其他下游有沒有同樣情形。** 只看了影音這一個。量化下游(`TradingAgents-main`)
  今天被別的守衛擋在更前面,沒走到這一格。

## 不寫進本票的東西

**不建議復原方式。** `git checkout` 會讓工作區看起來正常,
而**成因未知時復原等於把唯一的證據抹掉** —— 若是 OneDrive 事故或工具覆蓋,
那條路徑會再走一次,而下一次連「曾經不見過」都看不到了。
**復原方式等查清成因再定。**

今日**未**對該檔做任何 `checkout` / `add` / `commit`,影音 repo 一個檔都沒碰。
