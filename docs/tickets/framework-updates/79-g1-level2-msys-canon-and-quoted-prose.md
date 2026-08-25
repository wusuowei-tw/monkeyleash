# 79 — G1 第二級:MSYS 形態比不上包含性判定 + 引號散文裡的動詞被配對

**狀態**:進行中
**立案**:2026-08-25,G1 修法輪(量化 8/25 實證兩個假陽性,框架件回上游修)
**來源**:量化實證 + 本輪唯讀偵察(探針 14 案,A1/A4/A5/B1/C1/C2 六筆誤擋實證)
**裁決**(2026-08-25,全文在派工訊息):①必修 canon() 兩側共用;②修,走 A 引號法,
附三條件(a 不平衡退回現行為並釘測試、b 引號內路徑照算、c heredoc 殘留寫進守備宣告);
③正負對照兩方向分開;④照 ADR 0009 四步 + sync 兩下游 + 演練筆電 machine-init 登記;
⑤量化原始擋下訊息對帳前,不宣稱兩缺陷已窮盡。

---

## 缺陷(實證)

| | 位置 | 機制 |
|---|---|---|
| ① | `level2_hit`(比對段) | `ABS_PATH` 認得 `/c/…`(MSYS)與 `/mnt/c/…`(WSL,`mnt` 在 POSIX 白名單),但比對只正規化反斜線與大小寫,不轉磁碟形式 → 擷取得到、比不上 → 判專案外。而 `variants()` 早就會做形態互轉,只給第一級用 —— TSI-035 形狀:一組本該一起的知識只在一邊 |
| ② | `DESTRUCTIVE.search` 全文搜尋 | 動詞與路徑各自全文搜尋、無引號約束 → `git commit -m "上次 rm -rf /home/x 被擋"` 的散文配對成擋。G1 擋住「描述 G1 擋了什麼」,而 friction log 正是寫閘門行為的文件 |

實證表(修前,部署版探針):A1 MSYS 專案內 rm、A4 `cd /c/<proj> && rm -rf build/`、
A5 大寫 `/C/`、B1 WSL `/mnt/c/<proj>`、C1 散文引專案內路徑、C2 散文引外部路徑 —— 六筆 exit=2 誤擋;
A2(同路徑 Windows 形態)exit=0 對照;D1/D2 真外部仍擋。

## 修法

- ① `_canon()`:斜線/小寫正規化 + `/x/…`、`/mnt/x/…` → `x:/…`;**proj 與擷取路徑兩側同一個函式**。
- ② `_quote_spans()`:掃單/雙引號區間(雙引號內認 `\` 跳脫);**動詞**落在區間內不算;
  **路徑照算**(`rm -rf "/home/x"` 仍擋);掃描失敗(未閉合)→ 回 None 區間 = 退回現行為(往擋倒)。

## 登記(不修)

- cygdrive(`/cygdrive/c/…`)與 UNC(`\\server\…`):**擷取不到 = 漏,不是誤擋**;
  補擷取是擴權面,照 F-050 等實際誤擋實例。
- heredoc 內文的動詞 + 路徑仍會誤擋:已知殘留,寫進 guard docstring 守備宣告。
- POSIX 白名單外的根(`/srv` 等):既有 xfail(framework-updates/04),本輪不動。

## 驗收(兩方向分開,參照物不同)

- **方向 A(新放的都放了)**:負對照六筆(A1/A4/A5/B1/C1/C2,全部來自本輪實證誤擋,F-050 合規)→ 修後放行。
- **方向 B(原擋的都還擋)**:LEVEL2_REGRESSION 既有各條逐條;加 WSL 真外部 `/mnt/d/x`、
  引號路徑 `rm -rf "/home/x"`(裁決條件 b 的關鍵反控)、不平衡引號退回擋(條件 a,測試釘住)。
- 第一級全套、子目錄、鄰居、Write、fail-closed、磁碟根:不受本修影響,g1_verify 全套照跑。

## 散布與覆蓋(ADR 0009)

1. 草稿 = 本 repo 正典 `.claude/portable/g1_guard.py`(agent 寫)
2. `g1_verify.py` 全套對草稿全綠(條數不寫死),交 **diff**
3. **人**:備份 `~/.claude/hooks/g1_guard.py` 為 `.working`,`cp`(不是 `mv`)覆蓋,`git status` 查正本
4. agent live 探針真觸發一次;沒擋 → 立刻請人還原
5. sync 下發量化 / 影音(`g1_guard.py`、`tests/test_g1_guard.py` 同批,copy 桶)
6. **演練筆電另走一次 3–4(machine-init)—— 登記在此,別漏**

## 執行紀錄(2026-08-25)

- **R2 一次正確擋下**(收線後 `current_stage='idle'`),未自行改 pipeline,Jeff 開站後續行 —— 追認:正確運作非誤擋。
- **紅燈分佈(票 79 名下的紀錄)**:`7 failed, 7 passed, 53 deselected` ——
  failed 全是**方向 A 負對照**(修後該放行),passed 全是**方向 B 對照**(現版本來就擋 / 本來就放)。
  **這個分佈本身就是「兩方向參照物不同」的證明:同一批新測試,一半以現況為紅、一半以現況為綠。**
- 修後:`tests/test_g1_guard.py` 全檔 `64 passed, 3 xfailed`(xfail = framework-updates/04,不動)。
- `g1_verify` 全套對草稿 exit=0:34 條各命中自己那條、子目錄、3 鄰居、10 條第二級回歸、fail-closed。
- 修後探針 16 案(A1–C3 放行 10、D1–D6 仍擋 6)全符,含三條新方向 B:
  引號路徑 `rm -rf "/home/x"` 擋、不平衡引號退回擋、`/mnt/d/x` 擋。
- **verify 側加案例緩議**:`g1_verify.py` 無配對測試檔,改它會被 R3 擋;
  兩方向的持久防護改由 `tests/test_g1_guard.py`(copy 桶,隨每個 repo 跑)承擔,
  verify 側案例登記為候選(先開 `tests/test_g1_verify.py` 紅燈再動)。

## 對帳待辦(裁 ⑤)

- [ ] 量化該次原始擋下訊息到手後對帳;對上之前**不宣稱兩缺陷已窮盡**
  (他們用 `-F`,訊息理論上不在指令字串裡 —— 可能有第三個觸發面)。
