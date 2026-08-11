# ADR 0002:規格書一律不 inline 程式碼片段(覆寫上游 to-spec 的例外)

- 狀態:已採納
- 日期:2026-08-09
- 發現於:Step 5 試跑第二站,`/to-spec` 動手前

## 背景

本 repo 的 gate R1 規定:規格書不得含程式碼(code 圍籬、`def`/`import`/`function` 等)。
理由是規格書夾程式碼的話,程式一改規格書就過期,而過期的規格書比沒有規格書更糟——
它讀起來像權威,卻在描述一個已經不存在的實作。

上游 `to-spec` skill 的模板在 Implementation Decisions 節留了一個例外:

> Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can
> (state machine, reducer, schema, type shape), inline it within the relevant decision...

這與 R1 正面衝突。本次沒有跑 `/prototype` 因此沒撞上,但只要哪天先 prototype 再 to-spec,
skill 會要求 AI 做一件 gate 一定會擋的事。

## 決定

**保留 R1,覆寫上游的例外。** 規格書一律不得 inline 任何程式碼片段。改用:

- spec 要帶 prototype 成果 → 用連結指向 `.scratch/<feature>/prototype/`,不 inline
- API 形狀該進 spec 的部分 → 用散文描述(有哪些欄位、型別是什麼、狀態怎麼轉移),不用 code 圍籬

## 理由

R1 存在的理由是防止規格書夾帶會過期的程式碼。而 prototype 的產出**依定義是丟棄式的**,
是所有程式碼裡過期最快的一種。上游那個例外剛好打在 R1 要防的靶心上。

「用散文描述比較不精確」是真的,但那個不精確有個好處:它逼人寫下決定本身
(為什麼是這個形狀),而不是貼上一段當時湊出來能跑的東西。
真的需要精確形狀時,連結指向 prototype 目錄,讀者看得到完整脈絡,也看得到它是丟棄式的。

## 後果

- 本地 `to-spec` skill 的該段被覆寫,納入 patch 管理(`.claude/patches/apply_patches.py` 的 P2)
- `gate.py` R5 增加 P2 的存在與位置判定:覆寫被 `npx skills update` 蓋掉即擋 commit
- 這是**第二次覆寫上游決定**(第一次見 ADR 0001)。兩次都源於同一件事:
  採用外部框架時,它的假設與本地強制層的假設不一定相容,而衝突只會在真的跑到那一站時才現形
- 升級上游時若該段措辭改變,`apply_patches.py` 會因錨點消失而 exit 2,要人來看,不會靜默略過
