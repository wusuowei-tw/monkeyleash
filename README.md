# monkeyleash

**No monkeypatch, no fake greens.**

**A governance workflow for AI coding agents — for people who cannot inspect
the agent's work line by line.** Formerly `agent-gates`.

Core premise: **prompts are suggestions; files and hooks are law.**

*Current evidence base: 1 user · 1 agent (Claude Code) · 1 OS (Windows) ·
first external project pending.*

[![tests](https://github.com/wusuowei-tw/monkeyleash/actions/workflows/tests.yml/badge.svg)](https://github.com/wusuowei-tw/monkeyleash/actions/workflows/tests.yml)

[繁體中文](README.zh-TW.md)

---

You ask the AI "did you run the checks?" It says yes. How would you know?

monkeyleash is what I built after finding out that the six gates I had put on
my own project had been silently skipped in forty-odd changes. Not because the
AI lied — it didn't. Nothing was actually checking. This repo is the machinery
that now checks, plus the record of every way it has failed so far.

> Written for one person (me, a quant trader who does not read Python) and one
> agent (Claude Code) on one OS (Windows). Everything below is measured on that
> setup. Where it hasn't been proven elsewhere, the README says so instead of
> assuming.

## What it does, in one picture

```
 you (decide, approve)                  ← the only writer of intent
        │  paste the instruction
        ▼
 executor (Claude Code)                 ← writes code, never decides scope
        │
   ┌────┴────────────────────┐
   ▼                         ▼
 outpost hook              authority hook
 (every tool call,         (every commit,
  can be bypassed)          structural)
   └────┬────────────────────┘
        ▼
 evidence on disk: ledgers, intercepts, test runs, reports
        ▼
 status projection  →  read-only MCP  →  commander (Claude Desktop)
                                              │ reads, rules, writes next instruction
                                              ▼
                                             you
```

Two things are deliberate here:

- **The outbound path is authority; the return path is evidence.** The commander
  AI never touches the repo. The executor AI never decides what to do next. The
  human sits on the one line between them.
- **The scorer is not the student.** Every claim of "it passed" comes from a file
  the agent cannot edit, produced by a mechanism the agent cannot silently
  disable on the normal commit path.

## What's in the box

| Piece | What it is |
|---|---|
| **9 rules (R1–R9)** | Machine-enforced constraints on what the agent may write, where, and when: no code in specs, no writing outside the current stage's scope, no production file without a test, no `import research/` from production code, mirrors must match, no duplicate friction numbers, and so on. The authoritative list is `rule_codes()` in `.claude/hooks/gate.py`, derived from the rules' own block messages. |
| **G1** | A *user-level* guard, independent of the pipeline, that blocks destructive filesystem commands (`rm -rf`, `Remove-Item -Recurse`, …) against a protected list the agent cannot edit. **This is a denylist hook, not a sandbox** — real isolation needs containers or OS-level permissions. |
| **Two repository enforcement layers** | An *outpost* (`PreToolUse` hook, judges every Bash/Edit/Write before it runs) and an *authority* (`pre-commit`, `core.hooksPath`, the structural layer — not bypassable on the normal commit path). Rules declare which layer they live on. |
| **Six-station main-line pipeline** | `grill-with-docs → to-spec → to-tickets → implement → code-review → improve-codebase-architecture`. Two further stages exist off the main line: `idle` (standby) and `research` (an exploration area that may not write production code). The stage is a file the human edits; the agent can read it but not change it. Source writes are allowed only in stages that allow them. |
| **Ledgers** | Every exemption, every intercepted call, every test run, appended to `.dev/*.jsonl` with hashes chained. A restore that goes through `git checkout` leaves a visible gap in the chain rather than a clean lie. |
| **`status`** | One command that prints the repo's real state — HEAD, stage, ticket, which hooks are provably installed, which are only *claimed* — with every line carrying a `(source: …)` column. Lines it can't prove print `未證明` (unproven), not a green tick. |
| **Read-only MCP server** | Four tools for Claude Desktop: `status_all`, `ticket(n)`, `friction(code)`, `latest_report` (the latest executor report). Zero write paths, verified by an AST test that fails if a write call ever appears. |
| **Friction log** | 148 entries (numbered up to `F-159`; gaps are legal by design). Each one is a way the system or its author got fooled, written next to the line of code that now guards against it. Every entry is a failure mode met in practice, not a hypothetical threat list. This is the repo's most important asset. |
| **Positive controls** | Tests that are only trusted after a bounded mutation has made them fail on purpose. 4 of 9 rules have been through this so far. The other 5 are listed as *not yet proven*, not as passing. |

## What it does *not* claim

- It does not make the agent write correct code. It makes "the checks ran" a
  verifiable statement.
- It has not been run by anyone but the author. The first external project is
  scheduled; until then, "works for other people" is unproven.
- Rule R4 (mirror consistency) cannot currently be mutation-tested on Windows —
  symlink tests skip there. This is recorded, not hidden.
- The outpost layer can be turned off by the agent's host. Only the authority
  layer is structural. Bypassing the outpost is logged; bypassing `pre-commit`
  is not possible without `--no-verify`, which the ledger would show as a gap.
- `status` can tell you a hook is *configured*. It cannot tell you it *ran* on
  the last commit. That line prints "unproven" on purpose.
- Personal leak patterns (`~/.claude/leak-patterns.local.txt`) stay on the
  author's machine by design; CI scans with the generic patterns only. The two
  sides therefore scan with different pattern sets — when they disagree, find
  out which set was used, then fix whichever side is wrong.
- Gate messages are currently in Traditional Chinese.

## Quick start (10 minutes)

Requires Python `>= 3.10` and git.

```bash
git clone https://github.com/wusuowei-tw/monkeyleash.git
cd monkeyleash
pip install -e ".[dev]"
python -m pytest -q      # on a fresh clone: 2 failed
sh bootstrap.sh          # wires .githooks/ via core.hooksPath (once per clone)
python -m pytest -q      # now: 1 failed
```

**On Windows, run the `bootstrap.sh` line in Git Bash** (bundled with Git for
Windows) — PowerShell has no `sh`. Everything else runs in any shell.

**The `pip install -e ".[dev]"` line is not optional on a clean machine.**
Measured 2026-09-04 on a fresh laptop: skipping it makes `pytest` abort during
*collection* — the whole suite, not one test — with
`ModuleNotFoundError: No module named 'mcp'` and `1 error during collection`.
An aborted collection reports **zero tests run**, which does not look like a
missing dependency; it looks like nothing happened.

**The two failures on the first run are the point**, and they are not the same
kind of failure (measured on a clean clone, 2026-09-04):

| Test | After `bootstrap.sh` | Why |
|---|---|---|
| `TestAuthorityLayerIsWired::test_this_repo_itself_is_wired` | **goes green** | It is the test that says *"the authority layer is not installed"*. It should be red until it is. |
| `TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce` | **stays red** | It needs the drainage evidence in `.dev/test-runs.jsonl`, which is gitignored and therefore never present in a clone. A known gap, not a broken install; CI deselects it. See ticket 54. |

Then look at the state of the repo:

```bash
python .claude/portable/status.py
```

Every line has a source. Lines that say `未證明` are things the tool refuses to
guess.

Install into another repository:

```bash
python .claude/portable/install.py <path-to-target-repo>
```

Install always creates a commit and ends with a full verification —
*installed* means *verified*, not *copied*. Verify later with:

```bash
python .claude/portable/verify_gates.py <scratch-dir>   # every rule, clean-room
python .claude/portable/g1_verify.py                    # G1 protected list
```

## No coding background? Let your AI install it

Paste the following into your coding agent (tested with Claude Code) from
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

## Two repository enforcement layers

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

There is no per-repo switch: once installed, every rule is active
(`docs/adr/0010`).

## How it differs from other agent-governance tools

Several projects enforce policy on AI coding agents (hooks, sandboxes,
policy-as-code compiled into git hooks and CI). monkeyleash overlaps with them
on enforcement and is behind some of them on multi-agent support and
portability. It is not trying to replace them. What it adds is the operating
model around the enforcement — and that model would still apply if the
enforcement underneath were swapped out:

- a human on the authority line who does not need to read the code,
- evidence that lives in the repo and is produced by something the agent can't
  edit,
- a status view that distinguishes *configured* from *proven*,
- and a friction log that treats every fooled check as a first-class artifact.

If your team reads code and runs five agents, one of the other tools is
probably a better fit. If you are one person supervising one agent on work you
can't inspect line by line, this is the setup I use.

## Where it comes from

The six-station workflow and the skills under `.agents/skills/` are adapted
from [mattpocock/skills](https://github.com/mattpocock/skills) (MIT). The exact
upstream commit is **not recorded** — this repository has no
`skills-lock.json` (tracked as ticket 74). The file list, the three files
modified after fetching, and the upstream license text are in
`THIRD_PARTY_NOTICES.md`. I translated the skills to Traditional Chinese and
kept the originals byte-identical where the provenance rules require it.

What is original to this repo is the layer the upstream did not have: the
enforcement (gates, the two hook layers, the pipeline file the agent may not
edit), the evidence (ledgers, intercepts, test-run records, reports), the
`status` projection, the read-only MCP server, and the friction log.

## Read more

- The story of the forty-odd silent skips (Chinese):
  https://vocus.cc/article/6a950f34fd8978000170e285
- `docs/agents/friction-log.md` — the numbered `F-` entries: every one is a bug
  that actually happened, not a principle imagined at design time. This is the
  most portable asset in the repo.
- `docs/adr/` — architecture decisions, including why enforcement is
  deny-by-default and why the agent may not edit its own stage.
- `docs/tickets/` — the work log, one file per ticket.
- `docs/audits/` — point-in-time audits (rule inventory, going-public surface).
- `docs/machine-init.md` — setting up a second machine from zero, with the
  places the docs and reality disagreed.
- `CLAUDE.md` — the standing checks the agent is held to.

## Status

Actively developed, one maintainer. Numbers below are from 2026-09-04:

| | |
|---|---|
| Tests, local | **1313** passed (3 skipped, 3 xfailed) |
| Tests, CI | **1303** passed (the difference is itemised in ticket 106) |
| Rules | **9** (R1–R9), plus G1 at the user level |
| Friction log | **148** entries, numbered up to `F-159` |
| Tickets | **105 files**, numbered up to 106 |

> Counts and highest numbers are different things here: friction numbers and
> ticket numbers may have gaps (a renumbered entry leaves a hole, and R9
> deliberately does not check for consecutive numbering). Both are given above.

## License

MIT — see `LICENSE`. The skills under `.agents/skills/` are derived from
[mattpocock/skills](https://github.com/mattpocock/skills) (MIT) and modified
by `.claude/patches/`; see `THIRD_PARTY_NOTICES.md`.
