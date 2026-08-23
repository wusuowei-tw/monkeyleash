# Third-party notices

This repository redistributes material from the following projects. Each is
listed with its license, the files it covers, and what we changed.

## mattpocock/skills

- Source: <https://github.com/mattpocock/skills>
- License: MIT (the upstream repository ships its own `LICENSE` file)
- Copyright (c) Matt Pocock

### Files

The 39 files under `.agents/skills/` (13 skill directories) were fetched
from the upstream repository with the `skills` CLI
(`npx skills update`, wrapped by `scripts/skills-update.sh`):

```
.agents/skills/code-review/
.agents/skills/codebase-design/
.agents/skills/diagnosing-bugs/
.agents/skills/domain-modeling/
.agents/skills/grill-with-docs/
.agents/skills/grilling/
.agents/skills/handoff/
.agents/skills/implement/
.agents/skills/improve-codebase-architecture/
.agents/skills/setup-matt-pocock-skills/
.agents/skills/tdd/
.agents/skills/to-spec/
.agents/skills/to-tickets/
```

`.claude/skills/` and `skills/` are machine-generated mirrors of the same
files and are not committed.

### Modifications

Three of these files are **modified after fetching** and redistributed in
modified form. The modifications are applied by
`.claude/patches/apply_patches.py` (idempotent; re-applied on every update)
and are not part of the upstream project:

- `.agents/skills/code-review/SKILL.md` — adds a third review axis
  (exemption reconnaissance) as a mount point that gate rule R5 checks for
- `.agents/skills/to-spec/SKILL.md` — overrides the upstream "inline
  snippet" exception (specs under `docs/specs/` must not contain code; gate
  rule R1 enforces it)
- `.agents/skills/grill-with-docs/SKILL.md` — adds a question-triage step
  ("is this a question, or a to-do?")

### Provenance caveat

This repository has **no `skills-lock.json`**, so the exact upstream
commit or version the files were taken from is not recorded. Tracked as
ticket `docs/tickets/framework-updates/74`.

### License text (MIT)

```
MIT License

Copyright (c) Matt Pocock

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## GitHub Actions used in CI

`.github/workflows/tests.yml` pins `actions/checkout` and
`actions/setup-python` by commit SHA. Both are MIT-licensed by GitHub and are
fetched at CI time, not redistributed here.
