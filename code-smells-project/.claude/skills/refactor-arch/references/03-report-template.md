# 03 — Audit Report Template

Print the Phase 2 report **exactly** in this structure. The same text is later saved to `reports/audit-<project-folder>.md`.

## Rules

- Header fields come from Phase 1 (`Files` = number of source files analyzed, `lines of code` = measured total).
- `## Summary` counts must equal the number of findings of each severity; `Total` must equal the sum.
- Findings are ordered **CRITICAL → HIGH → MEDIUM → LOW**; inside a severity, order by impact.
- Every finding has the five fields below, in this order. `File:` is the path relative to the project root plus line(s): `path:12`, `path:12-30`, or several locations separated by `, ` (`a.py:10, a.py:44-47, b.py:8`). Lines must be the real ones from the current files.
- Title = catalog name (e.g. `SQL Injection`, `God Class / God File`, `N+1 Queries`, `Deprecated API: datetime.utcnow()`), so each finding maps to a catalog entry.
- Description says concretely what is in the code (quote the offending identifier/literal when short). Impact says what can go wrong. Recommendation names the fix and the playbook entry (`PB-xx`).
- No findings without evidence. Do not include positive remarks in the findings list.

## Template

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <project folder name>
Stack:   <Language> + <Framework> <version>
Files:   <N> analyzed | ~<LOC> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [CRITICAL] <Title>
File: <path>:<lines>[, <path>:<lines> ...]
Description: <what is wrong, concretely>
Impact: <consequence>
Recommendation: <fix> (PB-xx)

### [HIGH] <Title>
File: ...
Description: ...
Impact: ...
Recommendation: ...

### [MEDIUM] <Title>
...

### [LOW] <Title>
...

================================
Total: <N> findings
================================
```

## Example finding (format reference only)

```
### [CRITICAL] SQL Injection
File: data/accounts.py:28, data/accounts.py:47-50
Description: Queries are built by concatenating request values, e.g. "WHERE login = '" + login + "'".
Impact: An attacker can bypass authentication or read/modify any table.
Recommendation: Use parameterized queries inside the model layer (PB-02).
```
