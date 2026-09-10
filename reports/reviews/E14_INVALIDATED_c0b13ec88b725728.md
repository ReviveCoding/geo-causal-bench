# E14 Immediate Adversarial Review — Invalidated Protocol

Protocol: `AWARE-GEO-c0b13ec88b725728`. Status: **PROTOCOL_INVALIDATION**.

The first canonical score appeared to pass H1, H2, and numeric guardrails, but
fresh code-path review found that `score_committed_once` set decision
materiality to half the hidden true effect. Because that same materiality was
used to decide LAUNCH/HOLD/STOP, hidden truth affected the evaluated business
action. This violates the AWARE information boundary and invalidates H2,
decision-regret, false-launch, and false-stop results. The invalidated outputs
remain archived and may not support claims.

Correction: materiality is now computed from the observed pre-treatment total
inside the truth-blind estimator process and committed with the selection.
Scoring reads that committed value only. The evaluator also no longer reads the
protected seed file, and truth-ledger hashes now use the frozen public world
identity hash. These are scientific-semantic changes, so a new protocol identity
and entirely new final world set are mandatory.
