# Compute Budget

Evidence class: **PROJECTED**, based on the 16-world smoke/pilot in
`evidence/runtime/pilot_runtime.json` and measured official-package runtimes.

The frozen candidate budget is 200 development worlds, 300 qualification
worlds, 1,000 null worlds, 500 final worlds, and 250 post-final ablation worlds.
That is 2,250 Track A worlds and 9,000 independent estimator invocations. The
pilot mean was 0.00984 seconds per world (p95 0.01282), projecting 22 seconds of
single-process core simulation. I/O, bootstrap scoring, reports, and validation
are budgeted at ten times that estimate: under 5 CPU minutes and 0.2 GB.

Track B uses 300 worlds and 1,800 estimator invocations, budgeted under 10 CPU
minutes and 0.1 GB. The maintained R known-answer suite measured about 47
seconds after installation; it is not multiplied across all Monte Carlo worlds.
The official GeoX retained-design analysis measured 20.6 seconds and its
random/stratified comparison 22.7 seconds. A repeat allowance of 5 minutes is
reserved for GeoX, on the one GPU queue.

The JAX scaling study will use batches 16/64/256 with tensors shaped
`[batch, 40, 203]`; peak raw tensor storage is below 10 MB, with a 1 GB VRAM
allowance for compilation/runtime. The synchronized E00 matrix qualification
used 3.5 GB of 16.4 GB VRAM. Only one GPU process runs at once. CPU/R work is
bounded at four workers because WSL has 15.5 GiB RAM despite 32 logical CPUs.

Expected total wall time after implementation is below one hour; GPU time below
15 minutes; CPU time below one core-hour; canonical evidence below 1 GB. For a
binomial rate near 5%, 1,000 null worlds give an approximate 95% Monte Carlo
half-width of 1.35 percentage points. The 500-world final mixture gives about
1.9 points overall near 5%, with wider scenario-specific uncertainty explicitly
reported. No full Cartesian sensitivity grid is authorized.

If actual runtime exceeds budget, optional E21, redundant sensitivity cells,
and exploratory nonlinear variants are reduced in that order. Frozen primary
world counts are not reduced after E13.
