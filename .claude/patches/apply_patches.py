# -*- coding: utf-8 -*-
"""重套本地 patch —— 冪等,可在每次 npx skills update 後無腦執行。

為什麼不用「存一份改好的檔案蓋回去」:那會把上游的更新一併蓋掉,
等於永遠停在 patch 當下的版本。這裡改成「找錨點、插入區塊」,
上游怎麼更新都能重套;錨點不見了就 exit 2 讓人來看,不猜。

兩個 patch:
  P1 code-review — Data Integrity 第三軸掛載點(brief 留空)
  P2 to-spec     — 覆寫上游的 inline snippet 例外(與 gate R1 正面衝突)
"""

import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TARGET = os.path.join(ROOT, ".agents", "skills", "code-review", "SKILL.md")
TARGET_TO_SPEC = os.path.join(ROOT, ".agents", "skills", "to-spec", "SKILL.md")

UPSTREAM_EXCEPTION = ("Exception: if a prototype produced a snippet that encodes a decision "
                      "more precisely than prose can (state machine, reducer, schema, type shape), "
                      "inline it within the relevant decision and note briefly that it came from a "
                      "prototype. Trim to the decision-rich parts — not a working demo, just the "
                      "important bits.")

LOCAL_OVERRIDE = """<!-- LOCAL OVERRIDE (prototype snippets) — re-applied by .claude/patches/apply_patches.py.
     上游允許把 prototype 的 snippet inline 進 spec;本 repo 不允許,見 docs/adr/0002。 -->

**本 repo 覆寫上游此處的例外:規格書一律不得 inline 任何程式碼片段(gate R1 會擋)。**
prototype 的產出是丟棄式的、過期最快,正是 R1 要防的東西。改用:

- spec 要帶 prototype 成果 → 用連結指向 `.scratch/<feature>/prototype/`,不 inline
- API 形狀該進 spec 的部分 → 用散文描述(欄位、型別、狀態轉移各是什麼),不用 code 圍籬"""

ANCHOR_SPAWN = "### 4. Spawn both sub-agents in parallel"
ANCHOR_SPEC_TAIL = "If the spec is missing, skip the Spec sub-agent and note this in the final report."
ANCHOR_AGG = "### 5. Aggregate"

BLOCK_3B = """### 3b. Identify the data-integrity sources

<!-- LOCAL PATCH (third axis) — re-applied by .claude/patches/apply_patches.py.
     Do NOT hand-edit .agents/skills/code-review/SKILL.md; edit the patch script. -->

**TODO(user): brief 待填(框架層 vs 專案層分開,本分支不填)。**

Source: `.claude/review/data-integrity.md`. **If that file does not exist, this axis does not exist** — see step 4.

### 4. Spawn the sub-agents in parallel"""

BLOCK_4 = """**Data Integrity sub-agent prompt** — spawn **only if `.claude/review/data-integrity.md` exists**:

- The diff command and commit list.
- The contents of `.claude/review/data-integrity.md`, pasted in full.
- The brief: **TODO(user) — 待使用者提供。**

**Clean degradation is mandatory.** When that file is absent the axis is simply not part of this review: do not spawn the sub-agent, do not invent criteria, and in step 5 **omit the heading entirely** — no "not configured" note, no empty section, no mention anywhere in the report. The output must be byte-indistinguishable from the upstream two-axis review.

### 5. Aggregate"""

AGG_OLD = ("Present the two reports under `## Standards` and `## Spec` headings, verbatim or lightly cleaned. "
           "Do **not** merge or rerank findings — the two axes are deliberately separate (see _Why two axes_).")
AGG_NEW = ("Present a `## <axis>` heading for **each axis that actually ran** — `## Standards`, `## Spec`, "
           "and `## Data Integrity` — verbatim or lightly cleaned. An axis that did not run has no heading at all. "
           "Do **not** merge or rerank findings — the axes are deliberately separate (see _Why separate axes_).")

WHY_OLD = "- Code that does exactly what the issue asked but breaks the project's conventions → **Spec pass, Standards fail.**"
WHY_NEW = (WHY_OLD +
           "\n- Code that is clean and matches the spec but mis-handles data → "
           "**Standards pass, Spec pass, Data Integrity fail.**")


def fail(msg):
    sys.stderr.write("[apply_patches] %s\n" % msg)
    sys.exit(2)


ANCHOR_STD_BRIEF = ("- The brief: \"Report — per file/hunk where relevant — (a) every place the diff "
                    "violates a documented standard")

BLOCK_EXEMPTION_RECON = """- **Exemption reconciliation (local addition).** Read `.dev/gate-exemptions.jsonl` if it exists.
  Every line records a case where gate R3 waived the "must have a test file" rule because a ticket
  declared that module untested. For each line, open the ticket named in `declared_in` and confirm
  the module really is listed under `**Untested by decision:**`. Report any line whose ticket does
  not back it — that is a test-skip that was granted without a prior decision, which is the exact
  backdoor the exemption mechanism exists to prevent. Also report tickets whose declared-untested
  list has grown since the ticket was written, if the git history shows it.
"""


def patch_exemption_recon():
    """P3:code-review Standards 軸加「豁免逐筆對帳」。冪等。"""
    if not os.path.exists(TARGET):
        fail("找不到 %s" % TARGET)
    s = io.open(TARGET, encoding="utf-8").read()
    if "Exemption reconciliation (local addition)" in s:
        print("[apply_patches] code-review 豁免對帳已存在,無需重套")
        return
    if ANCHOR_STD_BRIEF not in s:
        fail("錨點消失:Standards sub-agent brief。上游改了措辭,請人工檢查後更新本腳本。")
    i = s.index(ANCHOR_STD_BRIEF)
    j = s.index("\n\n", i)
    s = s[:j + 1] + "\n" + BLOCK_EXEMPTION_RECON + s[j + 1:]
    io.open(TARGET, "w", encoding="utf-8", newline="").write(s)
    print("[apply_patches] 已重套 code-review 豁免對帳")


def patch_to_spec():
    """P2:覆寫 to-spec 的 inline snippet 例外。冪等。"""
    if not os.path.exists(TARGET_TO_SPEC):
        fail("找不到 %s" % TARGET_TO_SPEC)
    s = io.open(TARGET_TO_SPEC, encoding="utf-8").read()
    if "LOCAL OVERRIDE (prototype snippets)" in s:
        print("[apply_patches] to-spec 覆寫已存在,無需重套")
        return
    if UPSTREAM_EXCEPTION not in s:
        fail("錨點消失:to-spec 的 inline snippet 例外原文。上游改了措辭,請人工檢查後更新本腳本。")
    s = s.replace(UPSTREAM_EXCEPTION, LOCAL_OVERRIDE, 1)
    io.open(TARGET_TO_SPEC, "w", encoding="utf-8", newline="").write(s)
    print("[apply_patches] 已重套 to-spec 的 inline snippet 覆寫")


TARGET_GRILL = os.path.join(ROOT, ".agents", "skills", "grill-with-docs", "SKILL.md")

BLOCK_QUESTION_TRIAGE = """
<!-- LOCAL OVERRIDE (question triage) -->

## 問人之前先問自己:這題是不是三個指令就能查

**「先查清 X」不是問題,是待辦。** 把它寫成 Q 丟給使用者,等於把調查外包。

實際發生過:問「鏡像是 symlink 靜默回退還是腳本本來就複製」——三個指令就查清了,
而且**列出的兩個選項都不對**(答案是檔案層硬連結)。憑空推測出來的選項會把對方的
判斷錨定在錯的集合裡,比不問更糟。

判準:一個問題如果能由**讀碼、跑指令、看檔案**得到答案,它就不該出現在提問清單上。
提問保留給**判斷**:取捨、風險接受、優先序 —— 那些查不出來的東西。
"""


def patch_grill_question_triage():
    """P4:grill 站加「先查清 X 不是問題,是待辦」。冪等。

    2026-08-09 這段先被手寫進正典就沒登記 —— 下一次 `npx skills update`
    會靜默把它蓋掉,而那正是 wrapper 與 R5 存在的理由(F-002)。
    手寫進正典而不登記,等於把持久性交給記性。
    """
    if not os.path.exists(TARGET_GRILL):
        fail("找不到 %s" % TARGET_GRILL)
    s = io.open(TARGET_GRILL, encoding="utf-8").read()
    if "LOCAL OVERRIDE (question triage)" in s:
        print("[apply_patches] grill 提問判準已存在,無需重套")
        return
    # 這個 skill 短到沒有結構性錨點可用 —— 附加到尾端,語意上也對:
    # 它是本地補充,不是插進上游流程的中間。
    io.open(TARGET_GRILL, "w", encoding="utf-8", newline="").write(
        s.rstrip("\n") + "\n" + BLOCK_QUESTION_TRIAGE)
    print("[apply_patches] 已重套 grill 提問判準")


def main():
    patch_to_spec()
    patch_exemption_recon()
    patch_grill_question_triage()

    if not os.path.exists(TARGET):
        fail("找不到 %s" % TARGET)
    s = io.open(TARGET, encoding="utf-8").read()

    if "### 3b. Identify the data-integrity sources" in s:
        print("[apply_patches] code-review 第三軸掛載點已存在,無需重套")
        return 0

    if ANCHOR_SPAWN not in s:
        fail("錨點消失:'%s'。上游改了結構,請人工檢查後更新本腳本。" % ANCHOR_SPAWN)
    if ANCHOR_SPEC_TAIL not in s or ANCHOR_AGG not in s:
        fail("錨點消失(spec tail / aggregate)。上游改了結構,請人工檢查。")

    s = s.replace(ANCHOR_SPAWN, BLOCK_3B, 1)
    s = s.replace(ANCHOR_AGG, BLOCK_4, 1)
    if AGG_OLD in s:
        s = s.replace(AGG_OLD, AGG_NEW, 1)
    s = s.replace("## Why two axes", "## Why separate axes")
    if WHY_OLD in s and "Data Integrity fail" not in s:
        s = s.replace(WHY_OLD, WHY_NEW, 1)

    io.open(TARGET, "w", encoding="utf-8", newline="").write(s)
    print("[apply_patches] 已重套 code-review 第三軸掛載點")
    return 0


if __name__ == "__main__":
    sys.exit(main())
