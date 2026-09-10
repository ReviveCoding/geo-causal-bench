# Data Cards

| ID | Source and role | Authority / pinned identity | License / redistribution | Truth boundary |
|---|---|---|---|---|
| D1 | GeoLift PreTest and Test; public anchor and external package case | official Meta GeoLift repo commit `db34ea4299ff0e28515ebac502b78c076c93c905` | MIT repository; verify per-manifest before row commit | external observations; no known counterfactual truth |
| D2 | California Proposition 99 panel; SDID qualification and external case | official synthdid repo commit `70c1ce3eac58e28c30b67435ca377bb48baa9b8a` | repository license recorded in manifest; source traces to ADH (2010) | observed case; no known counterfactual truth |
| D3 | `mpdta`; did qualification and external case | official did repo commit `74b88eb07f1faa644df1271055a0f77848f6550c` | repository/package license recorded in manifest | observed/simulated package example; not Track A truth |
| D4 | GeoX single/multi-cell official example CSVs | official GeoX commit `0a1dd0f730ab8170e4e46646f3bf69400d57d021` | Apache-2.0 repository; verify files/manifests | official behavior example; no accuracy ranking |

Each acquired byte stream receives a JSON manifest with source ID/name,
authoritative URL, commit/package/version, UTC timestamp, license, SHA-256,
bytes, row count, schema, schema hash, redistribution status, and scientific
role. Raw row-level data is ignored by Git by default. Curated/anchor summaries
may be committed only when license and scientific need permit.

Data flow is RAW → STAGED → CURATED → ANALYTICAL MARTS. Validation covers
schema, duplicate rows and geo/date keys, missing/non-monotone dates, negative
response/spend, treatment metadata/contamination, spikes/outliers, missingness,
concentration, and response/spend consistency. External outcomes cannot be
treated as known truth.
