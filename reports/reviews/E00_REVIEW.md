# E00 Phase Review

Status: **COMPLETE**. Evidence class: **MEASURED**.

Ubuntu 22.04.5 under WSL2, Python 3.11.16, R 4.5.3, Git 2.34.1, uv 0.12.12,
32 logical CPUs, 15.5 GiB WSL RAM, and disk/GPU facts are recorded in
`evidence/e00_environment_probe.txt`. The host OS API query was denied; the
nonprivileged runtime reports Windows build 10.0.26200 and the preflight context
is retained.

JAX and jaxlib 0.10.2 selected exactly `cuda:0`, an NVIDIA GeForce RTX 4090
Laptop GPU (driver 610.62, 16,376 MiB). A synchronized 6144x6144 float32
JIT matmul/tanh used about 3,515 MiB, took 0.206 seconds including first compile
and 0.0298 seconds steady-state. XGBoost 3.2.0 completed eight CUDA histogram
rounds in 0.255 seconds. This proves execution, not merely imports. A first
JAX-array-to-XGBoost attempt failed without CuPy; host NumPy ingestion with
`device=cuda` succeeded. No drivers, system CUDA, BIOS, or security settings
were changed. Exactly one GPU was claimed and used.

Review result: environment identity and GPU backend are qualified. The
project-local environment and dependency locks isolate package changes.
