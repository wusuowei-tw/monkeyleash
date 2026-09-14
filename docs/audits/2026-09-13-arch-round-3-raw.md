# 第六站(arch)第三次診斷 —— 原文收錄(2026-09-13 輪)

> **⚠ 本檔的原文段【一個字未改】。** 所有標註、更正與現版核對**都在原文之外**。

## 收錄標註

| 項目 | 內容 |
|---|---|
| **來源** | **Jeff 提供的 GPT 對話內容**(第六站 9/13 輪)。**該對話從未進過版控。** |
| **原報告日期** | **2026-09-13** |
| **原報告宣告的基準** | **`59d9e2c`** + 當時的工作樹 |
| **本次收錄日期** | **2026-09-14** |
| **收錄時的 repo HEAD** | `18b0b55a8b98ce3a8815df7e20a95fb4016eba58` |
| **原文結論的狀態** | **尚待現版核對** —— 核對結果寫在**票 140**,不寫進本檔 |

## ⚠ 這份檔案為什麼存在

**原報告只存在於一個 GPT 對話裡,沒有任何版控落點。**

同一個形狀在本 repo 發生過:`docs/audits/2026-09-07-arch-round-2.md` 的開頭逐字記著 ——

> **上一輪(2026-08-24)的 19 條清單已經佚失。**
> 它住在報告與 `.scratch/` 裡,兩者都被清掉了,而三張票(76 / 77 / 78)引用它為來源。

⚠ **「8/24 清單佚失」是該份 9/07 審計文件的既有記載,本輪未重新調查。**

## ⚠ 原文裡兩句已過時的敘述(**不在原文內改寫,在此另列**)

原文以 `59d9e2c` 為基準,而**現行遠端是 `18b0b55`**。下列兩句因此已過時:

| 原文 | 現況 |
|---|---|
| 「**R5 兩格修復尚未提交,因此必須分開計數**」 | R5 兩格已於 `ef89a53` 提交(2026-09-13),`57abc81` 補票面、`3b73bcb` 補帳本 |
| 「**票 133:只算 HEAD —— 4 格已改、10 格未改、1 格待驗證**」 | 已不成立。批一七格全部收完:**六格修復 + 一格(⑦ R4)經量測後保留原設計** |

⚠ **原文其餘敘述同樣是 `59d9e2c` 時點的判讀,不得直接當成現版事實** ——
逐項現版核對見**票 140**。

## 原文(以下逐字收錄,未改動)

---

有改善，但還不能算架構漏洞已收乾淨。 本輪新增辨識 7 項 fail-open、2 項次要缺陷，另外發現 1 個票 133 分批修復造成的交互缺口；它仍歸原票，不重複加算。
全程唯讀：沒有修改檔案、執行探針、跑測試或呼叫會記帳的 gate 入口。以下新問題是靜態呼叫鏈判讀，不是實測繞過成功。
審查基準是 HEAD 59d9e2c 加目前工作樹。R5 兩格修復尚未提交，因此必須分開計數。
之前的問題改善多少
9/7 基準的 13 項 A／B：9 項已有改善、1 項重定義並留下另票、2 項未修、1 項維持不修裁決。改善不表示整個家族已封閉。
舊項目	本輪結果	現碼證據
A-1：repo 內 tmp／scratchpad 被放行	原案例已補 repo 內外判定；票 97 的路徑正規化缺口仍在	[gate.py (line 708)](/C:/projects/agent-gates/.claude/hooks/gate.py:708)、[gate.py (line 716)](/C:/projects/agent-gates/.claude/hooks/gate.py:716)
A-2：內嵌直譯器漏擋	標準寫法已擋；修復仍有新缺口，見下方 A-4	[gate.py (line 1074)](/C:/projects/agent-gates/.claude/hooks/gate.py:1074)
A-3：票號前綴	已補 <票號>- 邊界及 .md 限制	[gate.py (line 1570)](/C:/projects/agent-gates/.claude/hooks/gate.py:1570)
A-4：安裝偵測不驗執行位元	未修；仍只靠內容字串判「已接兩段」	[gate.py (line 325)](/C:/projects/agent-gates/.claude/hooks/gate.py:325)、[gate.py (line 350)](/C:/projects/agent-gates/.claude/hooks/gate.py:350)
B-1：缺全庫邊界檢查機制	未修，票 113 仍 candidate	[票113:3 (line 3)](/C:/projects/agent-gates/docs/tickets/framework-updates/113-boundary-family-needs-a-machine.md:3)
B-2／B-3／B-4：重複實作與漂移	已依語意採共用或對帳；不是全部機械合併	[票114:24 (line 24)](/C:/projects/agent-gates/docs/tickets/framework-updates/114-three-things-with-two-sources.md:24)、[差集測試:203 (line 203)](/C:/projects/agent-gates/tests/test_non_source_list_parity.py:203)、[行尾對帳:205 (line 205)](/C:/projects/agent-gates/tests/test_line_ending_parity.py:205)
B-5：install 裸 print	已改 UTF-8 輸出	[install.py (line 58)](/C:/projects/agent-gates/.claude/portable/install.py:58)
B-6／B-8：帳本分類、ADR 引用	已分桶、ADR 改記身分編號	[ledger_verify.py (line 170)](/C:/projects/agent-gates/.claude/portable/ledger_verify.py:170)、[gate.py (line 2421)](/C:/projects/agent-gates/.claude/hooks/gate.py:2421)
B-7：帳本讀取側	status 分桶已修；原 code-review 散文問題分流票 122，未消失	[status.py (line 170)](/C:/projects/agent-gates/.claude/portable/status.py:170)、[票116:51 (line 51)](/C:/projects/agent-gates/docs/tickets/framework-updates/116-the-ledger-and-its-readers-disagree.md:51)
B-9：註解可能被認成規則碼	維持既有不修裁決	[gate.py (line 1269)](/C:/projects/agent-gates/.claude/hooks/gate.py:1269)


最近的 index 家族則是：
範圍	目前結果
票 132：秘密掃描的被掃內容	已改讀 index，取不到不退回工作樹。[scanner.py (line 409)](/C:/projects/agent-gates/.claude/portable/scanner.py:409)
票 133：目前工作樹	6 格已改、8 格未改、1 格待驗證
票 133：只算 HEAD	4 格已改、10 格未改、1 格待驗證；差別是尚未提交的兩格 R5


六格修復的實際讀取點：R1 [2377 (line 2377)](/C:/projects/agent-gates/.claude/hooks/gate.py:2377)、R8 [2548 (line 2548)](/C:/projects/agent-gates/.claude/hooks/gate.py:2548)、R9 [1694 (line 1694)](/C:/projects/agent-gates/.claude/hooks/gate.py:1694)、R6 [110 (line 110)](/C:/projects/agent-gates/.claude/hooks/gate.py:110)、R5 [3476 (line 3476)](/C:/projects/agent-gates/.claude/hooks/gate.py:3476)／[3533 (line 3533)](/C:/projects/agent-gates/.claude/hooks/gate.py:3533)。
仍留下的八格：
既有格	工作樹讀取／消費點
R4 正典與鏡像	[gate.py (line 3347)](/C:/projects/agent-gates/.claude/hooks/gate.py:3347)
R2 站別定義、R3 research 豁免：兩格	[gate.py (line 1310)](/C:/projects/agent-gates/.claude/hooks/gate.py:1310)、[2609 (line 2609)](/C:/projects/agent-gates/.claude/hooks/gate.py:2609)
R3 legacy 成員豁免	[gate.py (line 2601)](/C:/projects/agent-gates/.claude/hooks/gate.py:2601)
R3 純套件標記豁免	[gate.py (line 2220)](/C:/projects/agent-gates/.claude/hooks/gate.py:2220)
R3 帳本回查	[gate.py (line 1594)](/C:/projects/agent-gates/.claude/hooks/gate.py:1594)
R3 上游成品豁免	[gate.py (line 2128)](/C:/projects/agent-gates/.claude/hooks/gate.py:2128)、[2655 (line 2655)](/C:/projects/agent-gates/.claude/hooks/gate.py:2655)
R2 上游豁免的 provenance 控制輸入	[gate.py (line 2083)](/C:/projects/agent-gates/.claude/hooks/gate.py:2083)、[2207 (line 2207)](/C:/projects/agent-gates/.claude/hooks/gate.py:2207)


A 桶：立即該修的 fail-open
下列「新增」指本輪新辨識，不表示都是最近才引入。
#	問題與可達的漏擋方向	證據
A-1	兩段權威層都漏 rename。 staged 清單只收 ACM，Git 判為 R 的目的路徑不進判定。把研究碼改名移進生產目錄，或把原本豁免的檔案改名到受管位置，可跳過目的地應有的檢查。內容來源即使修成 index，也救不了根本沒列入的檔案。	[gate.py (line 3650)](/C:/projects/agent-gates/.claude/hooks/gate.py:3650)、[scanner.py (line 499)](/C:/projects/agent-gates/.claude/portable/scanner.py:499)
A-2	R7 沒有換行邊界。 git status 後接真正換行，再接 tee pkg/x.py，會被視為同一段；整段以許可的 git 開頭，提前放行。	[gate.py (line 554)](/C:/projects/agent-gates/.claude/hooks/gate.py:554)、[569 (line 569)](/C:/projects/agent-gates/.claude/hooks/gate.py:569)、[1083 (line 1083)](/C:/projects/agent-gates/.claude/hooks/gate.py:1083)
A-3	某段抽到許可目標，替另一段抽取失敗背書。 echo x > .cache/probe; sed -i s/a/b/ pkg/x.py：第一段把全域 saw_target 設成 True；第二段的 sed 寫入被偵測，但沒有抽取分支，最後不再補「解析不出」的拒絕。	[gate.py (line 751)](/C:/projects/agent-gates/.claude/hooks/gate.py:751)、[800 (line 800)](/C:/projects/agent-gates/.claude/hooks/gate.py:800)、[865 (line 865)](/C:/projects/agent-gates/.claude/hooks/gate.py:865)
A-4	票 112 的內嵌直譯器守衛仍只認部分 token 寫法。 env -i python -c … 會把 -i 當成指令名；python "-c" … 則不認被引號包住的旗標。兩者仍是同一個「傳入程式碼」概念，卻可漏過新增守衛。	[gate.py (line 1024)](/C:/projects/agent-gates/.claude/hooks/gate.py:1024)、[1034 (line 1034)](/C:/projects/agent-gates/.claude/hooks/gate.py:1034)、[1037 (line 1037)](/C:/projects/agent-gates/.claude/hooks/gate.py:1037)、[1089 (line 1089)](/C:/projects/agent-gates/.claude/hooks/gate.py:1089)
A-5	「純套件標記」判準不等於沒有可測行為。 __init__.py 裡的 async def、頂層呼叫等都可能沒有符合正則的 def/class 行，卻含真正邏輯，仍直接豁免 R3。即使工作樹與 index 完全相同也成立，所以不是票 133 第 11 格的來源問題。	[gate.py (line 2211)](/C:/projects/agent-gates/.claude/hooks/gate.py:2211)、[2223 (line 2223)](/C:/projects/agent-gates/.claude/hooks/gate.py:2223)、[2615 (line 2615)](/C:/projects/agent-gates/.claude/hooks/gate.py:2615)
A-6	R3 的測試存在判定仍看磁碟。 有合格紅燈紀錄及本機測試檔，就可能提交實作而不提交測試；把測試 staged 刪除但保留磁碟副本，同樣能滿足存在判定。這格不吃檔案內容，故不在票 133 的內容家族計數內。	[gate.py (line 2627)](/C:/projects/agent-gates/.claude/hooks/gate.py:2627)、[2663 (line 2663)](/C:/projects/agent-gates/.claude/hooks/gate.py:2663)、[2675 (line 2675)](/C:/projects/agent-gates/.claude/hooks/gate.py:2675)
A-7	使用者層匯入把「有分類」當成「准許自動覆寫」。 import_() 只拒絕未分類，後續對所有 incoming 項寫入；human 沒有被排除。因此匯入包若帶 g1-protected.txt 或 shadow-clamp.txt，腳本仍會覆寫本應人工處理的守衛控制檔。	[user_layer.py (line 316)](/C:/projects/agent-gates/.claude/portable/user_layer.py:316)、[347 (line 347)](/C:/projects/agent-gates/.claude/portable/user_layer.py:347)、[358 (line 358)](/C:/projects/agent-gates/.claude/portable/user_layer.py:358)；分類：[manifest:61 (line 61)](/C:/projects/agent-gates/.agents/user-layer-manifest.txt:61)


A-1 另有唯讀佐證：既有 commit 8dbd594 有兩筆 R100；對同一份歷史 diff 加 --diff-filter=ACM，兩筆都消失。這證明清單排除行為，沒有實測違規 commit。
修復交互缺口，歸票 133，不另加一項：
R6 現在驗 index 清單，R3 卻仍讀工作樹清單發豁免。於是：
index 保持合法清單；只在工作樹加上新模組 → R3 放行該模組，R6 驗另一份乾淨清單而通過。

原本兩者同讀工作樹時，R6 尚能擋住「新檔不在 go-live 樹」；分批換來源後，這個補擋消失。證據：[gate.py (line 110)](/C:/projects/agent-gates/.claude/hooks/gate.py:110)、[1821 (line 1821)](/C:/projects/agent-gates/.claude/hooks/gate.py:1821)、[2601 (line 2601)](/C:/projects/agent-gates/.claude/hooks/gate.py:2601)。這是本輪最需要優先收掉的修復交互作用。
B 桶：次要缺陷
#	發現	證據
B-1	秘密遮罩先截斷、後替換。 命中跨過第 100 字時，完整命中字串不在 snippet 裡，replace 換不到，可能把秘密前段印進錯誤報告。commit 仍被擋，因此不是放行漏洞。	[scanner.py (line 636)](/C:/projects/agent-gates/.claude/portable/scanner.py:636)、[649 (line 649)](/C:/projects/agent-gates/.claude/portable/scanner.py:649)、[536 (line 536)](/C:/projects/agent-gates/.claude/portable/scanner.py:536)
B-2	帳本輪替可以在摘要不完整時刪原檔。 壞 JSON 行被跳過；讀取失敗回空清單，呼叫端仍往 os.remove 走。這不是既有的「摘要刻意不留全文」，而是連摘要計數也可能遺失。	[gate.py (line 3078)](/C:/projects/agent-gates/.claude/hooks/gate.py:3078)、[3088 (line 3088)](/C:/projects/agent-gates/.claude/hooks/gate.py:3088)、[3120 (line 3120)](/C:/projects/agent-gates/.claude/hooks/gate.py:3120)


既有票 117–122 的未完成事項仍保留，不冒充本輪新發現。
C 桶：查過後不需另修
項目	理由與證據
R5 前哨仍讀工作樹	本次分流接對了：前哨明傳 path，commit 裸呼叫取 index；不能全域替換。[gate.py (line 3379)](/C:/projects/agent-gates/.claude/hooks/gate.py:3379)、[3697 (line 3697)](/C:/projects/agent-gates/.claude/hooks/gate.py:3697)
影子套用卡使用 startswith	比的是紀錄 ID 縮寫，而且零命中、多命中都拒絕；已限制到唯一紀錄。[shadow_review.py (line 306)](/C:/projects/agent-gates/.claude/portable/shadow_review.py:306)
R7 沒有 commit 第二道	ADR 0008 的既定角色；但不能拿它替上列 R7 漏擋開脫。[gate.py (line 177)](/C:/projects/agent-gates/.claude/hooks/gate.py:177)


D 桶：仍需查證
項目	本輪能說到哪裡
票 133 第 15 格：秘密規則清單	仍讀工作樹。另須更正票面的一個前提：票說 .claude/portable/leak-patterns.txt 受 R2/R3 管，但 .txt 已被列為非原始碼，會提前返回。攻擊實驗本輪未做，仍列待驗證。[leak_scan.py (line 137)](/C:/projects/agent-gates/.claude/portable/leak_scan.py:137)、[gate.py (line 228)](/C:/projects/agent-gates/.claude/hooks/gate.py:228)、[2406 (line 2406)](/C:/projects/agent-gates/.claude/hooks/gate.py:2406)
R4 的實際部署效果	本機 .claude/skills 與 skills 兩個鏡像目錄都不存在；程式會跳過不存在的鏡像。這是既有票 133 的已知情形，不能將它回零當作一致性已被驗證。下游未查。[gate.py (line 3312)](/C:/projects/agent-gates/.claude/hooks/gate.py:3312)


本輪數字：新增 7 項 A、2 項 B；另揭露 1 個既有票內的修復交互缺口。票 133 在目前工作樹仍有 8 格未改、1 格待驗證。 這些是本輪確認到的範圍，不是宣稱剩餘漏洞已被全部窮盡。