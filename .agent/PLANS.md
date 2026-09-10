# ExecPlan Convention

An ExecPlan is a self-contained, continuously updated implementation and
research narrative. It is not a checklist written once at project start. The
plan must explain the current state to a new contributor who has no access to
prior chat context.

## Required qualities

1. Be self-contained. Define project-specific names, paths, commands,
   scientific boundaries, and acceptance criteria in the document.
2. Be outcome-oriented. Describe observable behavior and durable evidence,
   not only edits or intentions.
3. Be living. Update Progress, Surprises & Discoveries, Decision Log, and
   Outcomes & Retrospective whenever reality changes.
4. Be restartable. State exact commands, prerequisites, receipts, hashes, and
   recovery rules. Completed immutable stages should be verified and reused.
5. Be scientifically honest. Record failures and null or unfavorable results;
   do not rewrite gates after protected evidence is opened.
6. Be explicit about evidence boundaries. Separate development, qualification,
   frozen confirmatory, external, simulated, and projected evidence.

## Required sections

Every project ExecPlan contains: Purpose / Big Picture; Progress; Surprises &
Discoveries; Decision Log; Outcomes & Retrospective; Context and Orientation;
Plan of Work; Concrete Steps; Validation and Acceptance; Idempotence and
Recovery; Artifacts and Notes; Interfaces and Dependencies.

Progress entries are timestamped in UTC and use `[x]`, `[ ]`, or `[~]`.
Decisions record date, choice, rationale, and consequences. Discoveries cite
the command or artifact that established them. At each stopping point the plan
must name the next legal action.
