# monkeyleash

**No monkeypatch, no fake greens.**

Machine-enforced gates for a six-stage, test-first development pipeline —
plus a user-level guard against destructive filesystem commands, for coding
agents. Formerly `agent-gates`.

Core premise: **prompts are suggestions; files and hooks are law.**

[![tests](https://github.com/wusuowei-tw/monkeyleash/actions/workflows/tests.yml/badge.svg)](https://github.com/wusuowei-tw/monkeyleash/actions/workflows/tests.yml)

[繁體中文](README.zh-TW.md)

## What this is

A set of git hooks and Claude Code hooks that refuse to let a coding agent
(or a human) skip steps: no source writes outside the implementation stage,
no `x.py` without `tests/test_x.py`, no secrets in commits, no spec files
that contain code. The rules are enforced twice — early by an agent-side
hook, and authoritatively by `pre-commit` — and every rule fails *closed*:
when the gate itself breaks, it blocks rather than passes.

It also ships **G1**, a user-level guard that blocks destructive filesystem
commands (`rm -rf`, `Remove-Item -Recurse`, …) against a protected list that
the agent cannot edit. This is a denylist hook, not a sandbox — real isolation
needs containers or OS-level permissions.

The six-stage pipeline builds on Matt Pocock's open-source skills
(grill-with-docs → to-spec → to-tickets → implement → code-review →
improve-codebase-architecture); the enforcement layer — the gates
themselves, the ledger, and the friction log — is original to this repo.

## Prerequisites

- Python ≥ 3.10, git
- Claude Code (the `PreToolUse` hook layer targets it; the `pre-commit`
  layer works with any git client)
- **On Windows, run the `bootstrap.sh` line in Git Bash** (bundled with Git for
  Windows) — PowerShell has no `sh`. Everything else runs in any shell.

## Quickstart

    git clone https://github.com/wusuowei-tw/monkeyleash
    cd monkeyleash
    sh bootstrap.sh          # wires .githooks/ via core.hooksPath (once per clone)
    python -m pytest -q      # run the framework's own tests

The last command ends with `1 failed` (`TestLegacyNoRedlightList`) — that is a
known gap, not a broken install. CI skips this one; see ticket 54 for why.

Install into another repository:

    python .claude/portable/install.py <path-to-target-repo>

Install always creates a commit and ends with a full verification —
*installed* means *verified*, not *copied*. Verify later with:

    python .claude/portable/verify_gates.py <scratch-dir>   # every rule, clean-room
    python .claude/portable/g1_verify.py                    # G1 protected list

## No coding background? Let your AI install it

Paste the following into your coding agent (Claude Code or similar) from
inside the project you want to protect:

```
Install monkeyleash (https://github.com/wusuowei-tw/monkeyleash) into this
project by following the "Quickstart" section of its README.

Rules for this task:
1. Before running each command, explain in plain language what it does and
   why — then run it.
2. When the install finishes, run the verification commands from the README
   and paste their complete output back to me.
3. If anything fails or gets blocked, report the original error message
   verbatim. Do not work around it, do not change paths, do not edit the
   gate's state files — stop and ask me.
```

## Two enforcement layers

| Layer | Mount | Reach |
|---|---|---|
| Outpost | `.claude/settings.json` → `PreToolUse` | Travels with the repo; covers only the agent path |
| Authority | `.git/hooks/pre-commit` (via `.githooks/`) | Binds everyone — **but must be wired once per clone** (`docs/adr/0007`) |

What that adds up to:

- The outpost hooks into **Claude Code's tool layer**. Drive the repo with a
  different agent and this layer is simply not there.
- The authority layer is a git `pre-commit` hook, so it does not care which
  agent (or human) is committing — but it lives in `.git/hooks/`, which a
  clone never carries. It exists only after `bootstrap.sh` has been run once.
- So: someone who never runs `bootstrap.sh` gets **no** enforcement, and an
  agent that is not Claude Code gets **the authority layer only**. That is the
  boundary of the design, not a defect.

## Rules

The authoritative list is `rule_codes()` in `.claude/hooks/gate.py` — it is
derived from the rules' own block messages, so this table claims only that
each row is correct, not that it is complete.

| | Blocks when |
|---|---|
| R1 | a spec under `docs/specs/` contains code |
| R2 | source is written outside a stage that allows it (`docs/adr/0005`) |
| R3 | `x.py` is written without `tests/test_x.py`, or without a failing test written first |
| R4 | a skill mirror drifts from the canonical `.agents/skills/` |
| R5 | the canonical `code-review` skill lost its third-axis mount point |
| R6 | the red-light exemption list gains an entry not in the go-live tree |
| R7 | Bash writes into the repo — use Write/Edit instead (outpost only, `docs/adr/0008`) |
| R8 | production code imports from `research/` |
| G1 | a path on the protected list is touched (user level, independent of the pipeline) |

There is no per-repo switch: once installed, every rule is active (`docs/adr/0010`).

## Known limitations

- The authority layer lives in `.git/hooks/`, which git never versions.
  A fresh clone is **silent** about it until `bootstrap.sh` runs.
- Personal leak patterns (`~/.claude/leak-patterns.local.txt`) stay on the
  author's machine by design; CI scans with the generic patterns only.
  The two sides therefore scan with different pattern sets — when they
  disagree, find out which set was used, then fix whichever side is wrong.
- Gate messages are currently in Traditional Chinese.
- Skill mirrors under `.claude/skills/` are hard links or symlinks depending
  on the platform; R4 cannot assume either.

## Where to read next

- `docs/agents/friction-log.md` — the numbered `F-` entries: every one is a
  bug that actually happened, not a principle imagined at design time.
  This is the most portable asset in the repo.
- `docs/adr/` — decisions and their reasons.
- `docs/tickets/` — the work log, one file per ticket.
- `docs/audits/` — point-in-time audits (rule inventory, going-public surface).
- `CLAUDE.md` — the standing checks the agent is held to.

## License

MIT — see `LICENSE`. The skills under `.agents/skills/` are derived from
[mattpocock/skills](https://github.com/mattpocock/skills) (MIT) and modified
by `.claude/patches/`; see `THIRD_PARTY_NOTICES.md`.
