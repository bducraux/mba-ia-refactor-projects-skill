---
name: refactor-arch
description: Audits and refactors a backend codebase into an MVC architecture in three gated phases — (1) detect stack and map the current architecture, (2) audit against an anti-pattern catalog and produce a severity-ranked report, then STOP for human confirmation, (3) refactor to MVC and validate that the app boots and every original endpoint still responds. Stack-agnostic (Python/Flask, Node/Express and similar). Use when the user runs /refactor-arch or asks to audit or refactor a project's architecture.
disable-model-invocation: true
---

# refactor-arch

You are a senior software architect. Your job is to analyze, audit and refactor **the project in the current working directory** into a clean MVC architecture **without breaking its public behavior**.

The knowledge you need is in `references/` (next to this file). Read each reference **when its phase starts** — do not rely on memory:

| Phase | Read first |
| --- | --- |
| 1 — Analysis | `references/01-project-analysis.md` |
| 2 — Audit | `references/02-anti-patterns-catalog.md`, `references/03-report-template.md` |
| 3 — Refactoring | `references/04-mvc-guidelines.md`, `references/05-refactoring-playbook.md` |

## Ground rules (apply to every phase)

1. **Stack-agnostic.** Decide everything from evidence in the files (manifests, imports, entry points), using the heuristics in `01-project-analysis.md`. Never assume a stack from the folder or project name.
2. **No invented findings.** Every finding must point to code you actually read. Get line numbers from the tool output (read files with line numbers, or `grep -n`); never estimate them. If you are unsure a line range is right, re-read the file.
3. **Scope.** Analyze only the project's own source code. Ignore dependency and generated folders: `node_modules/`, `.venv/`, `venv/`, `__pycache__/`, `dist/`, `build/`, `.git/`, `.claude/`, lock files, `*.db`.
4. **Read-only until confirmed.** Phases 1 and 2 must not create, edit, move or delete any file — not even the report. Running read-only commands (`ls`, `find`, `grep`, `wc`, `cat`, `git status`) is fine.
5. **Language of output.** The phase banners and report headings are in English exactly as in the templates; descriptions may follow the language of the codebase.

---

## Phase 1 — Project Analysis

Follow `references/01-project-analysis.md` to determine:

- **Language** and **framework with version** (read it from `requirements.txt` / `pyproject.toml` / `package.json` / lock files — do not guess).
- **Dependencies** (runtime only, excluding the framework).
- **Domain** of the application, inferred from routes, table/model names and seed data (e.g. "Library API (livros, empréstimos, membros)").
- **Architecture** currently in place (monolithic / partially layered / layered) and why.
- **Source files** count and approximate **lines of code** (count with a command; exclude the ignored folders above).
- **Database** engine and **tables/models**.
- **Entry point and start command** (e.g. `python app.py`, `npm start`) and **port**.
- **Endpoint inventory**: every route as `METHOD /path` (from route declarations; include example request files such as `*.http` if present). Keep this list — Phase 3 must validate every one of these endpoints.

Then print exactly this block (fill every field; keep the labels):

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <language>
Framework:     <framework> <version>
Dependencies:  <comma-separated runtime deps>
Domain:        <one-line domain description>
Architecture:  <current architecture + one-line justification>
Source files:  <N> files analyzed | ~<LOC> lines of code
DB tables:     <comma-separated tables/models>
Entry point:   <file> (<start command>, port <port>)
Endpoints:     <N> routes
================================
```

After the block, list the endpoint inventory (`METHOD /path`, one per line). Then continue directly to Phase 2.

---

## Phase 2 — Architecture Audit

1. Read `references/02-anti-patterns-catalog.md` and `references/03-report-template.md`.
2. Go through **every** source file found in Phase 1 and check it against **every** catalog entry, using the detection signals listed for each anti-pattern (including the **Deprecated APIs** section). Use `grep -n` for the signal patterns and read the surrounding code to confirm before reporting.
3. For each confirmed problem create a finding with:
   - severity from the catalog (CRITICAL, HIGH, MEDIUM, LOW — use the catalog's definitions, adjust only with a written reason);
   - **exact location** `File: <relative/path>:<line>` or `<start>-<end>`; when the same problem repeats in several places, list all locations (comma-separated) in the same finding;
   - Description (what is in the code, concretely), Impact, Recommendation (pointing to the playbook transformation).
4. Group repetitions of the same anti-pattern into one finding; do not pad the report with trivial items, and do not omit real CRITICAL/HIGH issues.
5. Sort findings **CRITICAL → HIGH → MEDIUM → LOW**, compute the summary counts and the total, and print the report **exactly** in the format of `03-report-template.md`.
6. If the project already has some layering, still audit it: report what is wrong inside the existing layers (security, duplication, N+1, fat routes, unused abstractions, deprecated APIs) and what layers are missing.

Then print exactly this line and **STOP**. End your turn and wait for the user's answer:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

**Hard rule:** do not create, edit or delete any file before the user answers. Do not start Phase 3 on your own, do not "prepare" files, do not save the report yet.

### After the answer

- Whatever the answer, first **save the report** (the exact text printed in Phase 2, from the opening `====` line to the closing `Total:` block) to `<repository root>/reports/audit-<project-folder-name>.md`. Find the repository root with `git rev-parse --show-toplevel` (if not a git repo, use the parent of the project folder). Create `reports/` if needed. This is the only file written outside the project folder.
- If the answer is **n** (or anything other than yes): print `Refactoring skipped. Report saved to <path>.` and stop. Do not touch the project.
- If the answer is **y**: go to Phase 3.

---

## Phase 3 — Refactoring

Read `references/04-mvc-guidelines.md` and `references/05-refactoring-playbook.md` before changing anything.

### 3.0 Capture a behavioral baseline (before editing)

1. Install dependencies if needed (`pip install -r requirements.txt` inside an existing virtualenv such as `.venv/` if there is one, or `npm install`).
2. Prepare the data the app needs to run (e.g. seed script if the README says so).
3. Boot the **original** app in the background with its original start command and call **every endpoint from the Phase 1 inventory** (use `curl`), with valid sample inputs taken from the code, seeds or example request files. Record method, path, status code and the top-level JSON keys of each response in a temporary file **outside the project** (e.g. under the system temp dir).
4. Stop the app and restore the data to the same initial state (delete the generated database file only if it is created automatically by the app or a seed script).

### 3.1 Refactor

Apply the target structure from `04-mvc-guidelines.md` for the detected stack, using the transformations from `05-refactoring-playbook.md`, so that **every finding from the report is addressed**. Mandatory outcomes:

- **Config** module reading environment variables with safe development defaults; no secrets in code. Create/update `.env.example` listing every variable (never write real secrets; never create or commit `.env`).
- **Models** encapsulate all data access (parameterized queries / ORM, no SQL elsewhere).
- **Controllers** own the request flow (parse → validate → call service/model → build response); business rules in a service layer when they are more than trivial.
- **Routes/Views** only map `METHOD /path` → controller.
- **Centralized error handling** (one error handler/middleware; controllers raise/throw domain errors instead of formatting 500s themselves).
- **Clear entry point / composition root** that builds config → db → models/services → controllers → routes → app.
- **Authentication covers the whole auth finding.** If the report has an authentication/authorization finding (AP-09), take the list of routes it cites and wrap **each one** with the auth decorator/middleware at route level (PB-12b) — every sensitive write route (create/update/delete account, password, email, role, active flag) and every cited read of another user's private data. Authorization inside the service is unconditional (caller is the owner or an admin; role changes and deletions admin-only), never a check that runs only when a certain field is in the payload. "Contract preservation" is not a reason to leave a cited route open.

**Contract preservation (non-negotiable):**

- Keep **every original route** with the same path and HTTP method, the same success and error **status codes**, and the same **response body shape** (same keys, same envelope, same content type).
- Keep the **original start command and port** working (e.g. `python app.py`, `npm start`): if you move code, leave the original entry file as a thin bootstrap or update the start script accordingly.
- Keep seed/sample data behavior so the app starts with the same data.
- **Intentional contract changes are allowed only to remove a security vulnerability** — e.g. stop returning passwords/hashes/secrets in a response, require an admin credential (from config) for an endpoint that executes arbitrary SQL/code or destroys data, or require authentication (401/403) on the routes cited in an authentication finding. Never silently delete a route. Every intentional change must be listed in the final output under "Intentional contract changes".
- If the project is already partially layered, **evolve** the existing structure (add the missing layers, move logic out of routes, fix issues in place). Do not rewrite what is already correct.

Do not add new third-party dependencies unless a finding cannot be fixed without one (e.g. a password-hashing library); prefer the standard library or what the framework already provides (e.g. `werkzeug.security` in Flask, `crypto.scrypt` in Node).

### 3.2 Validate

1. Install dependencies again if you changed manifests.
2. Boot the refactored app with the **original start command**; confirm it starts without errors (check the process output).
3. Call every endpoint from the Phase 1 inventory again with the same inputs used in 3.0 and compare with the baseline: same status code and same top-level keys, except for the listed intentional contract changes.
4. Re-run the detection signals from the catalog (`grep -n`) over the new code to confirm that the reported anti-patterns are gone.
5. **Auth negative tests** (when the report has an AP-09 finding): for every route cited in it call (a) with no credential → expect 401/403, (b) with a valid token of a different non-admin user → expect 403, (c) as the owner or admin → expect the original status and shape. Then try the takeover explicitly: change another account's password (e.g. the seeded admin's) without a token, then log in with the new password — both must fail and the original password must still work. Any route that accepts the anonymous write is a failure: fix it and validate again.
6. If anything fails, fix it and validate again. Stop the app and leave the working tree with no stray processes, temp files or generated databases.

Then print exactly this block:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<tree of the new source layout, one file per line, with a short comment for key files>

## Intentional contract changes
<"None" or one line per change: METHOD /path — what changed — which finding it fixes>

## Validation
  ✓ Application boots without errors (<start command>)
  ✓ All endpoints respond correctly (<N>/<N> match the baseline)
  ✓ Zero anti-patterns remaining (<how this was checked>)
  ✓ Auth enforced on <N>/<N> routes from the auth finding (anonymous → 401, other user → 403; takeover attempt rejected) — or "No auth finding"
================================
```

Use `✗` instead of `✓` for anything that did not pass, with the reason — never report a check you did not run.
