# 76 — R7 三處許可比對不帶邊界 + 權威層偵測不驗洩漏段

**狀態**:**done**(2026-08-24 收刀:CI run #44 綠;commit `d57e74a` 立案 / `bd19d2d` 修復)
**立案**:2026-08-24,第六站診斷半(唯讀)→ 唯讀探針實測定案
**來源**:第六站 improve-codebase-architecture 診斷清單甲組(A1/A2/A3)+ 乙組 B5
**摩擦記錄**:F-117(F-086 又一實例 —— 判準寫下了、同 repo 同形狀沒被重掃)

---

## 定性(票面明寫)

**R7 為 sentinel-only(ADR 0008,無第二道)。本票修的是內部韁繩,不是對外攻擊面。**
但依 ADR 0003 分流:R7 破,Bash 路徑上的寫入不再被逼回 Write/Edit,
R2/R3 對那條路徑整段落空 —— 「不改會讓別的規則失效」,不屬可擱置類。

## 現象(2026-08-24 唯讀探針實測,8/8 成立、對照組 4/4 符合設計)

三處同族(比對不帶邊界,F-051 家族),一處異族但同「宣稱比實際強」形:

| 項 | 位置 | 洞 | 實測放行的探針 |
|---|---|---|---|
| A1 | `gate.py` `bash_write_violation` 的 `seg.startswith(p)`(約 :778) | 許可前綴無邊界 | `gitfoo > x.py`、`github-cli > x.py`、`pipx > x.py` |
| A2 | 許可切段 `re.split(r"&&\|\\\|\\\|\|;", cmd)`(約 :777)vs 目標切段(約 :515,多含單一管線) | 同一條規則兩份切段定義;管線接在許可前綴後整段免檢 | `git log \| tee pkg/evil.py`、`pip list \| tee x.py` |
| A3 | `_target_allowed` 的 `any(t in tok …)`(約 :491-493) | 許可目標用子字串比對 | `tee mybuild/x.py`、`tee x.dev/y.py`、`tee myscratchpad_notes.py` |
| B5 | `authoritative_layer()`(約 :247-259) | 只驗 `"gate.py"` 與 `"--pre-commit"`,不驗 leak_scan 段 —— hook 降級成只剩 gate 段時照報「已安裝」 | (讀碼 + 測試盤點定案:`TestAuthorityLayerIsWired` 四條無一構造「有 gate 段、缺洩漏段」) |

對照組(修完**必須維持放行/維持擋**,誤擋方向一併釘住):
`git status` 放行、`tee build/out.tmp` 放行、`tee .dev/notes.jsonl` 放行、
`cat x | tee out.txt` 維持擋。

## 範圍(四項,裁決逐字)

1. **A1 許可前綴補邊界** —— 前綴後須為空白或字串尾。
2. **A2 兩份切段定義收成單一來源** —— 照 `gate.py` `POSIX_WRITE_COMMANDS`
   自己記載的教訓(票 29:兩份各自維護的名單必分岔,單一來源後
   「兩邊要一致」是構造不是註解)。
3. **A3 目標比對改邊界式** —— 照 `scanner.py` `SKIP_ROOTS`/`SKIP_PARTS`
   的正典形狀(根錨定 vs 任意深度帶 `/` 邊界,兩種錨定不合成一種)。
4. **B5 `authoritative_layer` 補驗 leak_scan 字串** + 一條「缺洩漏段要叫」負控
   (既有測試只驗「缺 gate 段要叫」;缺口與票 27 同族、方向相反)。

## 紀律(裁決逐字,執行順序)

- **紅燈先行**:8 條探針全數轉為常駐回歸測試(它們就是現成的紅燈),
  4 條對照組同時入測 —— 誤擋方向也要釘住:`git status`、`build/`、`.dev/`
  必須維持放行。
- **修完走三半徑(F-082/F-085)**:
  1. 同檔目視同族(gate.py 內每一處 `startswith`/`in` 式的放行比對);
  2. 全庫重掃同形狀比對(受害字串搜法,不搜概念);
  3. **R7 影子帳本回掃** —— 歷史上有沒有指令走過這三個洞
     (`.dev/shadow-log.jsonl` 的 cmd_verb/cmd_len/cmd_sha256 指紋所及範圍內查;
     票 68 之前的紀錄無指令,判不出的照 F-116/票 67 紀律留白)。
     **有 = 分開登記,不改歷史。**
- **F-117 入 friction log**(已於立案同批寫入,見該檔)。
- **收刀**:CI 綠即收;收刀單獨回報,**含測試數預測**
  (預測帶基準:`外層 N(以 <commit> 的 collected M 為底)`,照 F-109)。

## 驗收要有的反控

- A1:`gitfoo > x.py` 擋、`git status` 放行(邊界收窄不得誤傷真 git)。
- A2:`git log | tee pkg/evil.py` 擋、`git commit -m 'x'` 放行;
  切段定義單一來源後,加一條守住「往後有人再拆開它」(形狀照
  `test_the_two_lists_agree_on_powershell_verbs`)。
- A3:`tee mybuild/x.py` 擋、`tee build/out.tmp` 放行、`tee .dev/notes.jsonl` 放行、
  `echo x > /dev/null` 放行(`/dev/null` 是完整 token,不受邊界化誤傷)。
- B5:hook 只剩 gate 段 → `authoritative_layer` 回 False 且訊息點名缺的是洩漏段;
  兩段齊全 → True(既有反控 `test_a_wired_hook_under_hookspath_is_installed` 不得紅)。

## 探針原始紀錄(定案證據,2026-08-24)

腳本:草稿區 `r7_probe.py`(repo 外),`importlib` 載入 gate.py 直呼
`bash_write_violation()`,無寫入副作用。逐條結果:

```
[A1] 'gitfoo > x.py'          -> None(放行)
[A1] 'github-cli > x.py'      -> None(放行)
[A1] 'pipx > x.py'            -> None(放行)
[A1] 'git status'             -> None(放行)(對照,正確)
[A2] 'git log | tee pkg/evil.py' -> None(放行)
[A2] 'pip list | tee x.py'       -> None(放行)
[A2] 'cat x | tee out.txt'       -> 擋下:[R7] 這個 Bash 指令會寫到沒有被許可的位置(out.txt)。(對照,正確)
[A3] 'tee mybuild/x.py'          -> None(放行)
[A3] 'tee x.dev/y.py'            -> None(放行)
[A3] 'tee myscratchpad_notes.py' -> None(放行)
[A3] 'tee build/out.tmp'         -> None(放行)(對照,設計許可)
[A3] 'tee .dev/notes.jsonl'      -> None(放行)(對照,設計許可)
```

B6 附帶查證(與本票相關的邊界條件):`rule_codes()` 生產呼叫端只有
`verify_gates.py`(走預設、只掃 gate.py 自己)—— 本票**不搬任何規則出檔**,
全部修在 gate.py 原位,rule_codes 涵蓋不變。

## 收尾登記(2026-08-24 裁決)

- **下游待辦(獨立,不在本票)**:量化 repo 那份 202 筆 R7 影子帳本的回掃
  = **下游量化視窗的獨立待辦** —— 本票已修的三個洞(A1/A2/A3)在該帳本裡
  有沒有歷史放行,屆時查。本 repo 側無帳本、構造上放行不留痕,已照票 67 留白。
- 三半徑命中兩處已各開候選票:**77**(票號前綴邊界)、**78**(gitignore 行精確查重)。
