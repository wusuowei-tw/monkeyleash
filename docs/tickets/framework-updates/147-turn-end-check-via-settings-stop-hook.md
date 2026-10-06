# 票 147 —— 收工檢查改用 settings Stop hook

**狀態**:**待辦。只登記,不排程。**
**優先度**:**未定。**
**發現於**:2026-10-04,monkeyleash-mod V0 唯讀偵察(裁決:V0 = NO-GO)。
**報告**:`.dev/reports/2026-10-04T110800Z-mods-v0-recon.md`(⚠ 只在本機)。

---

## 命題

「Claude 準備結束回合 / 宣稱完成」這個時間點**今天就攔得到**,不需要 mod:
settings 的 **Stop hook** 可以擋下收工、讓 Claude 繼續做。

hooks.md〈Stop decision control〉原文:
> Exit 2 or `decision: "block"` with a `reason` prevents Claude from stopping and forces the conversation to continue. The reason is shown to Claude as a system reminder so it can act on your feedback and try a different approach.

對照 mod 這一側(偵察結論):`turn.complete` 是**事後**才觸發,
只能觀察或在回答底下加一行字(`{ text }`),**擋不了**。
mod 經由 `classic.Stop` 回 `{ block }` 會不會生效:**UNKNOWN**(沒有實跑)。

## 為什麼獨立成一張票

**Stop 和 PreToolUse、Gate/CI 屬於不同的生命週期:**

| 層 | 時間點 | 擋的是 |
|---|---|---|
| PreToolUse(gate.py 前哨) | 每一次工具呼叫之前 | 一個**動作** |
| pre-commit / CI | commit / push 時 | 一份**結果** |
| **Stop** | 回合結束之前 | 一句**宣稱** |

前兩層管的都是「做了什麼」;Stop 管的是「**說了什麼**」。
混進票 146 的話,會被當成擴充完整性的一部分,而它其實是另一件事。

## 現況

`.claude/settings.json` 目前只登記了 `PreToolUse`(matcher
`Write|Edit|MultiEdit|NotebookEdit|Bash|PowerShell`),**沒有 Stop**。

## 開工前要先裁的事(**現在不裁**)

1. **判準是什麼。** 「宣稱完成卻沒有附證據」是一個**需要推論**的檢查 ——
   依 CLAUDE.md〈R9 為什麼在權威層〉的門檻(零誤報 + 零判斷 + 便宜),
   **它不夠格進權威層**。所以 Stop hook 的定位必須先講清楚:前哨?lint?提醒?
2. **block 還是 additionalContext。** hooks.md 兩種都有:
   `decision: "block"` 會強制繼續;`hookSpecificOutput.additionalContext`
   "appears as a system reminder but doesn't prevent the stop"。
   會推論錯的檢查用 block,等於擋住做對事的人。
3. **迴圈上限。** hook 一直 block 的話,回合會一直接下去。
   有沒有現成的防迴圈欄位:**未查證** —— 10/4 取得的 hooks.md Stop 輸入範例只有
   `session_id`、`prompt_id`、`transcript_path`、`cwd`、`permission_mode`、
   `hook_event_name`、`last_assistant_message`、`stop_reason`,不要憑記憶補欄位。
4. **與票 146 的交集**:Stop hook 本身也是 hooks 清單上的一員,
   一樣受 `disableAllHooks` / `--safe-mode` / `--bare` 影響。
