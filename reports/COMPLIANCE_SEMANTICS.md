# Compliance Semantics

Extension `COMPLIANCE-SEMANTICS-001` uses `DGP_A_v2_COMPLIANCE`, paired potential outcomes, shared shocks, separately stored assignment and dose, and truth-isolated observed payloads. Assignment ITT, per-dose response, and CACE are distinct by definition—not by requiring unequal numbers. CACE is reported only under recorded random-assignment, exclusion, monotonicity, and no-interference assumptions.

| nominal_compliance | estimand | bias | rmse | coverage |
| --- | --- | --- | --- | --- |
| 0 | assignment_itt | 86.9477 | 1193.37 | 0.96 |
| 0 | cace | nan | nan | nan |
| 0 | dose_response | nan | nan | nan |
| 0.25 | assignment_itt | 104.859 | 1226.65 | 0.94 |
| 0.25 | cace | 39.5297 | 417.5 | 0.94 |
| 0.25 | dose_response | 1.46605 | 15.0155 | 0.93 |
| 0.5 | assignment_itt | 95.9313 | 1114.91 | 0.96 |
| 0.5 | cace | 10.5341 | 130.534 | 0.96 |
| 0.5 | dose_response | 0.598729 | 5.12003 | 0.92 |
| 0.75 | assignment_itt | 169.674 | 1107.38 | 0.95 |
| 0.75 | cace | 11.2612 | 78.4852 | 0.95 |
| 0.75 | dose_response | 0.470525 | 3.38901 | 0.91 |
| 1 | assignment_itt | 13.5644 | 1181.96 | 0.96 |
| 1 | cace | 0.678222 | 59.0981 | 0.96 |
| 1 | dose_response | 0.0242222 | 2.11065 | 0.96 |
