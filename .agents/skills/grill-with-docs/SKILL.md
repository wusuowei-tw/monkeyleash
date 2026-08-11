---
name: grill-with-docs
description: A relentless interview to sharpen a plan or design, which also creates docs (ADR's and glossary) as we go.
disable-model-invocation: true
---

Run a `/grilling` session, using the `/domain-modeling` skill.

<!-- LOCAL OVERRIDE (question triage) -->

## 問人之前先問自己:這題是不是三個指令就能查

**「先查清 X」不是問題,是待辦。** 把它寫成 Q 丟給使用者,等於把調查外包。

實際發生過:問「鏡像是 symlink 靜默回退還是腳本本來就複製」——三個指令就查清了,
而且**列出的兩個選項都不對**(答案是檔案層硬連結)。憑空推測出來的選項會把對方的
判斷錨定在錯的集合裡,比不問更糟。

判準:一個問題如果能由**讀碼、跑指令、看檔案**得到答案,它就不該出現在提問清單上。
提問保留給**判斷**:取捨、風險接受、優先序 —— 那些查不出來的東西。
