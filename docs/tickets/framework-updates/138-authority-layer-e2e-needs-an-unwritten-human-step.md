# 票 138 —— 權威層端對端驗證需要人工步驟,而該步驟沒有被寫下來

**狀態**:**candidate。只登記,本輪不查、不修。**
**優先度**:**未定** —— 見〈時鐘〉欄。
**發現於**:2026-09-12,做票 133 批一 ② R1 與 ③ R8 的權威層探測時。
**來源**:票 133 批一 ② / ③。**該票只登記本票,不處理。**

---

## ⚠ 本票的證據邊界

**本票只記錄「發生了什麼」,沒有做任何診斷、沒有提修法。**
下面沒有寫的東西就是沒查。

---

## 三件事實

### 一、兩格的端對端證據都無法用 agent 工具取得

票 133 批一 **② R1** 與 **③ R8** 兩格,要驗「權威層在真的 commit 路徑上會擋」,
需要造出一個違規樣本進 index。兩條造法各自撞上一道前哨:

**(a) 造違規樣本 → 被同一條規則的前哨擋。**

R1(2026-09-12,`.scratch/r1probe/spec.md`,語料 `R1_CODE_SHAPES` 的 `def` 樣式):

```
PreToolUse:Write hook error: [python "$CLAUDE_PROJECT_DIR/.claude/hooks/gate.py"]:
[六站閘門/前哨] [R1][enforce] .scratch/r1probe/spec.md:規格書禁止含程式碼。spec 站只描述『要解決什麼問題』與『怎樣算做完』,請移除 code 圍籬 / def / import / function。
(權威判定在 pre-commit,繞過前哨仍會在 commit 被擋)
```

R8(2026-09-12,`.scratch/r8probe/mod.py`,語料 `import research`):

```
PreToolUse:Write hook error: [python "$CLAUDE_PROJECT_DIR/.claude/hooks/gate.py"]:
[六站閘門/前哨] [R8][enforce] .scratch/r8probe/mod.py:生產程式碼不得 import research/。
     research/ 是探索區,可以被丟棄;生產碼依賴它,研究一被殺掉生產就壞。
     反方向可以:research/ 底下的碼 import 生產資料層是允許的。
     要用到某段研究成果,把它移出 research/ 走六站,不是 import 它。
(權威判定在 pre-commit,繞過前哨仍會在 commit 被擋)
```

**(b) 刪工作樹那份 → 被 R7 擋。**

R1 那次的替代造法是「乾淨版進 index、刪掉工作樹那份」(乾淨內容前哨不擋)。
刪檔被 R7 擋:

```
PreToolUse:Bash hook error: [python "$CLAUDE_PROJECT_DIR/.claude/hooks/gate.py"]:
[六站閘門/前哨] [R7][enforce] 這個 Bash 指令會寫到沒有被許可的位置(.scratch/r1probe/spec.md、(引號或跳脫使目標無法可靠切分))。
     …
     **Write / Edit 不能刪除或改名** —— 這條的出口是 `git rm`(`git` 在許可清單裡)。
```

**R7 指定的出口 `git rm` 會同時從 index 與工作樹移除**,而本實驗需要 index 保留那一份
⇒ **用它就毀掉實驗本身。**

### 二、兩次都靠 Jeff 本人手動操作才取到

- **② R1**:Jeff 手動執行 `del .scratch\r1probe\spec.md`(工作樹),
  之後 agent 接手 `--pre-commit` 取 rc。結果:`AD` 狀態下 **rc=0**,
  證明權威層讀的是 index(舊碼讀工作樹會 `FileNotFoundError` → fail-closed → rc=1)。
  紀錄:`.dev/reports/2026-09-12T022816Z-r1-authority-layer-reads-index-verified.md`
- **③ R8**:**待做。** 2026-09-12 的探測在第 1 步被前哨 R8 擋下,
  第 2–6 步未執行。紀錄:
  `.dev/reports/2026-09-12T062635Z-r8-probe-blocked-by-sentry-same-shape-as-r1.md`

### 三、這一步目前沒有任何文件寫下來

「權威層端對端驗證需要人工做哪一個動作」這件事,**不在** `CLAUDE.md`、
**不在** `docs/adr/`、**不在** 票 133 的票面流程裡、**不在**任何 skill 裡。

⇒ **下一個做 ④–⑦ 的人會重新撞一次。**

---

## 時鐘

**有觸發條件,沒有日期。**

> **下一次有人動票 133 的 ④–⑦ 任何一格時。**

照 `docs/agents/issue-tracker.md` 的時鐘欄規矩,沒有日期 ⇒ 停在 `candidate`,
不排進任何順序。

---

## 相關

- 票 133(批一 ② / ③)—— 本票的來源。
- `docs/adr/0009` —— `g1_verify.py` 的覆蓋那一步同樣「只有人能做」,**而那件事有明文流程**。
  (**本行只記兩者都存在一個人工步驟,不主張它們同類、也不主張該照搬。**)
