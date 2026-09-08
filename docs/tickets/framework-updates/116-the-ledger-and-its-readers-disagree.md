# 116 — 帳本與讀它的三個東西各自假設了不同的格式(B-6 + B-7 + B-8)

**狀態**:**candidate**(立案,不動工)
**立案**:2026-09-07,第六站(arch)第二次診斷 → **B 桶 B-6 + B-7 + B-8**
**來源**:`docs/audits/2026-09-07-arch-round-2.md` 的 **B-6 / B-7 / B-8**
**站別**:立案時 `idle`;動工前由裁決者改 `current_stage` 與 `ticket_id`
**估工**:**小** · **裝新下游前**:**B-8 要;B-6 / B-7 不必**(只影響上游自己的對帳)

> 三件併一張,因為它們**同一個對象**(`.dev/gate-exemptions.jsonl`)、
> 而且**其中兩件會互相掩蓋**:格式有兩種(B-7)讓「斷點」的計數說不清楚(B-6),
> 於是先修任何一件,另一件的數字都會動。

> **⚠ 更正(2026-09-08 裁決,`F-036` 加註 —— 上面原句保留,不刪):**
>
> **(一)那個相依消失了,順序改成 `B-8 → B-6 → B-7`。**
> B-7 重定義成 `status.py:613`(見該節更正)之後,它不再碰 `chain_breaks` ——
> **兩刀改的是不同檔案、不同函式,誰先做都不會動到對方的數字。**
>
> **(二)新順序的判準換了一個**:原本排 B-7 先是因為那個相依;相依沒了之後,
> 剩下的判準是「**哪一件不能落**」——
> **B-8 是唯一「裝新下游前必做」的**(見票頭估工欄),
> 而它的票面自己就標了最容易做壞(`declared_in` 改記什麼,三個呼叫點要一致)。
>
> **(三)D-4 那個 fail-open 併進 B-6,不開新票** ——
> 同函式(`chain_breaks`)、同一次分桶動作,分兩刀會改到同一段碼。
> B-6 因此從兩桶擴成**四桶**,見該節。

---

## B-6 —— `ledger_verify` 的「驗整份」在活帳本上報 29 個斷點,而結構性的那些是設計

**受害符號**:`ledger_verify.chain_breaks`(判準是 `ended != started` 即斷)
vs `gate.exemption_record`(明寫 pre-commit 的 `result_hash` 是 `None`:**「None 不是 False」**)。

**實測(2026-09-07)**,單位:筆 / 個:

```
帳本               206 筆
result_hash 為 null  65 筆(其中 40 筆連鍵都沒有 = 票 08 之前的舊格式)
at_commit            25 筆
chain_breaks 會報    29 個斷點
```

**兩邊各自都對**:`gate` 那一側「提交時算不出結果內容,所以記 `None`(= 不知道),
不得寫成 `False`(= 確定沒變)」是刻意的;
`ledger_verify` 那一側「逐段驗接續,不是只比端點」也是刻意的(v1 只比兩端,漏了中間斷過又走回來)。
**壞的是它們對同一份資料的假設不同,而沒有東西在報告那個差。**

**後果是噪音**:文件寫的用法(`python .claude/portable/ledger_verify.py` = 驗整份)
在活帳本上必然報一串斷點,而**其中大部分是設計** ——
`F-031`:壞掉的訊號訓練人忽略訊號。

**修法方向**:`chain_breaks` 認得「`result_hash is None` 是**設計上的斷**」,
與「真的斷了」分成兩個桶回報。**不是把它們濾掉** ——
濾掉之後「有幾筆是不知道的」就沒有人看得到了(票 67 那 72 筆的同一句話:
**留白要有自己的桶,不能併進蓋章**)。

**紅燈形狀(一句)**:餵一份含 pre-commit 筆(`result_hash=None`)的帳本,
`chain_breaks` 要把它歸進「設計上的斷」而不是「斷點」,而**真的改壞一筆雜湊仍然要進斷點桶**。

> **⚠ 擴充(2026-09-08 裁決,`F-036` 加註 —— 上面原句保留,不刪):兩桶擴成四桶。**
>
> ### 為什麼是四桶 —— 本輪實測的完整分解(2026-09-08,帳本 219 筆)
>
> ```
> 總筆數 = 219 筆;chain_breaks 目前報 = 33 個
>
> 斷點依「前一筆的 result_hash」分:
>     ended 是 None                        = 29 個
>         └ 14 鍵 pre-commit(at_commit=true,設計上 None)  28 個
>         └ 5 鍵舊格式(無 result_hash 鍵)                   1 個
>     ended 是真雜湊(真的對不上)          =  4 個
>     合計 29 + 4 = 33 ✓
> ```
>
> | # | 桶 | 目前 | 說明 |
> |---|---|---|---|
> | 1 | **設計上的斷**(pre-commit,`result_hash=None`) | **28 個** | `gate.exemption_record` 明寫「**None 不是 False**」——提交時算不出結果內容 |
> | 2 | **格式交界** | **1 個** | 索引 39 → 40,**5 鍵 → 13 鍵**(不是 5 → 14,見 B-7 更正 (五)) |
> | 3 | **真的對不上** | **4 個** | 逐筆列在下面。**這四個才是要查的東西** |
> | 4 | **無從驗證**(沒有雜湊欄位) | **39 對** | ⚠ **目前一個都沒被報出來** —— 見下 |
>
> ### 桶 3 —— 四個「真的對不上」,逐筆(1-based 序號)
>
> ```
> (57, 58)   ended=bdfff0b8199799a6c53472f4a03d3307cb22e2a04b425151c27a8d19319ffa19
>            started=36c3a116e593b9c5f1f6cd7a981aec957d772006dd3588d5dda786af18d2ac30
> (73, 74)   ended=ce5d1aefb21788171b37279e967c8a3b38e667594bac20b435bfaf8f8fad6ab5
>            started=64cd7af39fcdeafd1becdc16ed9249e795923b68daaf439bf43f523211ed61f1
> (143, 144) ended=795dff638f7593b67fe18eaf58572760eba0489f0069d2732b070905519a00a2
>            started=54dabea0ff1e2a2cd6e8cbab7cfc5ae8a83608a76f3ee77ce9cd63908991adcd
> (156, 157) ended=2293423e82b4bfbcfef96142e43b058c695eba63207dba1517747c8592dd4b9b
>            started=95f001e5e43d24a3cbd86e2f1de79413326e4e0982dfc5b8bebd0320064ea2b8
> ```
>
> **本刀只分桶,不追根因。** 這四筆為什麼對不上是另一個問題 ——
> **是否追,另開票,由裁決者定。** 分桶先做的理由:現在它們埋在 33 個裡面,
> **沒有人看得出哪四個值得查**。
>
> ### 桶 4 —— ⚠ **這一格是併進來的,而且是 fail-open**
>
> `chain_breaks` 兩邊都用 `.get()`:
>
> ```python
>         ended = records[i].get("result_hash")
>         started = records[i + 1].get("content_hash")
>         if ended != started:
> ```
>
> 5 鍵紀錄**兩個鍵都沒有** ⇒ 兩邊都是 `None` ⇒ `None != None` **為假** ⇒ **不算斷**。
>
> 實測:
>
> ```
> 5 鍵那批的 0-based 索引範圍 = 0..39(共 40 筆,連續 = True)
>   5 鍵批**內部**的相鄰對被判成斷 = 0 個(該批內部共 39 對)
> ```
>
> **⇒ 那 40 筆「完全沒有雜湊、無從驗證」的紀錄,在 `chain_breaks` 的輸出上
> 與「驗過而且接得上」的紀錄長得一模一樣。**
>
> **(2) `parse_records` 的 docstring 已經寫過這一條的另一半,而它沒管到這一格。** 逐字:
>
> > **壞行丟 `ValueError`,不跳過。** 跳過等於「那一段改動不存在」,
> > 而鏈會因此**看起來是連續的** —— 一個因為漏看而變乾淨的結論,比看得見的斷點危險。
>
> 那句話管的是**壞行**(解析不了的),**沒有管到「解析得了但沒有雜湊欄位的行」**——
> 而**後果與壞行完全相同**:鏈看起來是連續的。**本刀補的就是那一半。**
>
> ### (1) ⚠ 預測:修完之後回報的項目數會**變大**,那是正確的不是退步
>
> ```
> 修之前:33 個(單一桶,而且桶 4 完全不在裡面)
> 修之後:28 + 1 + 4 + 39 = 72 個(四桶,單位:相鄰對)
> ```
>
> **票面先寫下這個預測,動工後實測對照。**
>
> 一個「修完之後數字變大」的改動很容易被讀成退步,而它不是:
> **72 裡面有 39 個是本來就存在、只是沒有人看得到的東西**。
> (基準:以 `c4a418b` 當時的帳本 219 筆為底。**帳本每一次 gate 自我修改都會增長**,
> 所以動工當天要**先重量一次再比**,不要拿這裡的 72 直接對 —— `F-109` 的同一條。)
>
> ### 本刀與 B-7 的相依已經消失
>
> 原票面說「其中兩件會互相掩蓋…先修任何一件,另一件的數字都會動」。
> B-7 重定義成 `status.py:613` 之後,**它不再碰 `chain_breaks`** ——
> 兩刀改的是不同的檔案、不同的函式。**相依沒了,順序因此改成 B-8 → B-6 → B-7。**

---

## B-7 —— 帳本兩種格式並存,而票 49 的對帳讀法沒有分支

**受害符號**:`.dev/gate-exemptions.jsonl` 的**首行 5 鍵**(票 08 之前)
vs `gate.exemption_record` 產的 **14 鍵**。

**實測**:5 鍵 **40 筆** / 14 鍵 **166 筆**(合計 206 筆)。

**問題不在舊資料存在** —— 舊資料**本來就該留著**(`F-036`:歷史紀錄記的是當時的事實,
改它會讓事後修飾混進審計軌跡)。
問題在**讀的那一側沒有承認有兩種**:票 49 的對帳表逐筆問「哪一條規則有帳、`outcome` 是什麼」,
而 40 筆**根本沒有 `outcome` 這個鍵** —— 它們會被讀成「沒有 outcome」還是「不知道」?
**兩者在表上長得一樣。**

**修法方向**:讀取側加分支,並在對帳輸出裡**明確分桶**:
`舊格式(欄位不存在)` / `新格式`。**不補值、不推論** ——
給舊筆一個假的 `outcome` 就是拿一個沒發生的機制去解釋一個發生過的事。

**紅燈形狀(一句)**:餵一份混合格式的帳本,對帳輸出要分成兩桶且兩桶筆數相加等於總筆數;
**任何一筆被靜默丟掉就紅**。

> **⚠ 更正(2026-09-08 裁決,`F-036` 加註 —— 上面全部原句保留,不刪):**
>
> ### (一)「票 49 的對帳表」三處皆誤
>
> **① 它不是程式,是散文。** 那段東西是
> `.claude/patches/apply_patches.py:81` 的 `BLOCK_EXEMPTION_RECON` ——
> 一段被 `patch_exemption_recon()` **注入 `code-review` skill 的 Standards 軸**的英文,
> **由 agent 讀了去做**,沒有任何程式在執行它。逐字:
>
> ```
> - **Exemption reconciliation (local addition).** Read `.dev/gate-exemptions.jsonl` if it exists.
>   Every line records a case where gate R3 waived the "must have a test file" rule because a ticket
>   declared that module untested. For each line, open the ticket named in `declared_in` and confirm
>   the module really is listed under `**Untested by decision:**`. Report any line whose ticket does
>   not back it — that is a test-skip that was granted without a prior decision, which is the exact
>   backdoor the exemption mechanism exists to prevent. Also report tickets whose declared-untested
>   list has grown since the ticket was written, if the git history shows it.
> ```
>
> **② 它不是票 49 的,而且早於票 49。**
>
> ```
> $ git log -S "BLOCK_EXEMPTION_RECON" --format="%h %ad %s" --date=short -- .claude/patches/apply_patches.py
> 91335c8 2026-08-11 agent-gates:六站流程閘門與 agent 檔案系統災難防護
> ```
>
> 它在 **go-live commit `91335c8`(2026-08-11)** 就存在。
> 票 49(`49-a-record-when-something-is-blocked.md`)講的是**攔截帳本**
> `.dev/intercepts.jsonl`,**不是豁免帳本**;它裡面的「對帳」指的是
> 「影子側與 enforce 側**用同一組欄位對帳**」(`:304`),與這一段無關。
>
> **③ 它根本不讀 `outcome`。** 它讀的是 `declared_in` 與模組名 ——
> **而那兩個欄位 5 鍵舊格式都有**:
>
> ```
>  5 鍵:['declared_in', 'file', 'module', 'reason', 'ticket']
>                 ↑                ↑
> ```
>
> **⇒ 那 40 筆對這段對帳完全可讀,「沒有分支」在這裡不構成問題。**
> 上面那段「它們會被讀成『沒有 outcome』還是『不知道』?」問的是一個不存在的讀者。
>
> ### (二)實際裁決:B-7 重定義為 `status.py:613`
>
> **全庫唯一讀 `outcome` 的程式**(`gate.py` 是寫的那一側):
>
> ```
> $ grep -rn "outcome" .claude/portable/*.py .claude/hooks/*.py | grep -v "gate.py"
> .claude/portable/status.py:613:        blocked = len([r for r in ex if r.get("outcome") == "blocked"])
> .claude/portable/status.py:615:        exval = u"總 %d 筆;outcome=blocked %d 筆;最後一筆 %s" % (
> ```
>
> `.get()` 讓「**沒有這個鍵**」與「**值不是 blocked**」在輸出上長得一樣。
> 實測(2026-09-08):`blocked = 1 筆`,而**沒有 `outcome` 這個鍵的有 40 筆** ——
> 它們**既不在 blocked 也不在 granted,報表上沒有它們的位置**。
> `status.py:615` 印的是「總 219 筆;outcome=blocked 1 筆」。
>
> **與票 67 那 72 筆是同一句話**:留白要有自己的桶,不能併進蓋章。
>
> 上面「修法方向」與「紅燈形狀」兩段的**內容仍然適用**,只是對象換成
> `status.py` 的那一行 —— 分桶、不補值、兩桶(或三桶)相加等於總筆數。
>
> ### (三)數字全面更新(舊那組已過期)
>
> 上面「實測:5 鍵 40 筆 / 14 鍵 166 筆(合計 206 筆)」是 **2026-09-07** 量的,
> **中間隔了票 114 的四刀**(每刀改 `gate.py` 都會寫一筆自我修改豁免)。
> **2026-09-08 重量**:
>
> | 項目 | 值 | 單位 |
> |---|---|---|
> | 總筆數 | **219** | 筆 |
> | `result_hash` 為 null(含缺鍵) | **69** | 筆 |
> | └ 其中連 `result_hash` 這個鍵都沒有 | **40** | 筆 |
> | └ 有鍵但值為 null | **29** | 筆 |
> | 14 鍵新格式 | **176** | 筆 |
> | `chain_breaks` 報的斷點 | **33** | 個(相鄰對) |
>
> 相加:`219 = 150(有鍵且有值) + 29 + 40`;`69 = 29 + 40`。
>
> ### (四)⚠ 票面的模型漏了第三種形狀:**13 鍵,3 筆**
>
> 上面只寫了「5 鍵 vs 14 鍵」,而實際有三種:
>
> ```
>      5 鍵    40 筆
>     13 鍵     3 筆      ← 票面沒有
>     14 鍵   176 筆
>     40 + 3 + 176 = 219 ✓
> ```
>
> **13 鍵是票 08 的第一批**(0-based 索引 40/41/42,即 5 鍵那批之後緊接的三筆,
> `ts` 都是 `2026-08-12T23:2x`,`ticket=08`,`file=.claude/hooks/gate.py`)。
> **與 14 鍵只差一個鍵:少了 `tool`**(那一欄是後來才加的)。
>
> **對 B-7 沒有影響**:它們**有** `outcome`(值 `granted`)——
> 這也解釋了為什麼「`outcome` 為 None 的正好是 40 筆」= 5 鍵那批,不多不少。
>
> **對 B-6 有影響,見該節的四桶分解。**
>
> ### (五)⚠ 併記一處我自己的更正
>
> 本輪第一份報告把那個交界斷點寫成「**5 鍵 / 14 鍵**交界」,**那是錯的** ——
> 逐筆量過之後是 **5 鍵 → 13 鍵**(索引 39 → 40)。
> 當時只看了「5 鍵批的邊界在索引 39」就推斷下一筆是 14 鍵,**沒有去看那一筆**。
> (`CLAUDE.md`:推論鏈的品質保證不了前提。)

---

## B-8 —— `declared_in` 記的是一條下游多半不存在的路徑

**受害符號**:`gate.note_exemption(..., declared_in="docs/adr/…")`
(三個呼叫點:ADR 0004 / F-0014 / F-0016)vs `portable-manifest.txt` 的 `docs/adr/ ask`。

**manifest 自己逐字寫著**:「`ask` 桶**安裝時不帶過去**,所以下游多半沒有 `docs/adr/`」。

於是下游帳本的每一筆豁免都引用一個**在那個 repo 裡不存在的檔案** ——
`F-122` 的形狀(點名一個下游不會有的檔案)。

**修法方向(裁決給的)**:`declared_in` 改記
**ADR 編號 + 上游 URL**,不記路徑;
並給既有帳本一個**讀取層對應**(舊筆的路徑 → 編號),
**不改寫歷史帳本**(`F-036` + ADR 0006 的同一條:agent 改不了已經落地的紀錄,那是它可信的理由)。

**兩個必須先答的問題**:

1. **`logged_exemption_backed` 會回頭打開 `declared_in` 指名的東西驗票**
   (`committed_declaration`)。那一條路徑上的 `declared_in` 是**票**不是 ADR
   (`reason=ticket-declared`),所以改動要**只動 ADR 那幾個呼叫點**,
   不得讓票那條路徑跟著變 —— 否則 R3 的票宣告豁免會整條失效。
   **這一格是本票最容易做壞的地方。**
2. **上游 URL 寫死在 `gate.py` 裡,是不是一個新的漂移點?**
   repo 搬家 / 改名之後那個 URL 會過期,而**過期時沒有東西會說話**
   (本 repo 剛從 `agent-gates` 改名為 `monkeyleash`,那次改名的餘波還在票 90)。
   候選:只記編號(`F-0016`),URL 放**一個地方**(README 或 `CONTEXT.md`)由人維護。

**紅燈形狀(一句)**:新產生的豁免紀錄,`declared_in` 是 ADR 編號而不是路徑;
而 `reason=ticket-declared` 那條路徑的 `declared_in` **仍然是票的路徑**、
`logged_exemption_backed` 仍然驗得到票。

---

## 裝新下游前要不要

| | | 理由 |
|---|---|---|
| B-6 | **不必** | 只影響上游自己跑 `ledger_verify` 時的噪音 |
| B-7 | **不必** | 40 筆舊格式是**上游自己的歷史**;新裝的下游帳本從第一筆就是 14 鍵 |
| B-8 | **要** | 這一格**只在下游成立** —— 上游有 `docs/adr/`,所以在上游看永遠正常 |

> B-8 那一列就是「**在開發機上看永遠正常**」的另一個形狀(`F-142` 的親戚):
> 差別是那一族是平台,這一格是**安裝形態**。
