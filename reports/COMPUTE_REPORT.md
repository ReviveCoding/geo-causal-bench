# Compute Report

**MEASURED:** E00 JAX 0.10.2 selected one `cuda:0` RTX 4090 Laptop GPU. A
6144-square synchronized JIT workload took 0.206 s first/compile and 0.0298 s
steady, using about 3.5 GiB. XGBoost CUDA qualification took 0.255 s; the E15
64-tree GPU model took 0.976 s.

JAX batch world-equivalent throughput was 6,144/s (batch 16), 10,558/s (64),
and 96,172/s (256), versus NumPy 2,288/s, 3,076/s, and 3,872/s: steady-state
GPU speedups 2.69x, 3.43x, and 24.84x. Compilation cost was 0.37--0.40 s, so CPU
can be preferable for one tiny batch. No multi-GPU claim is made.

Bounded CPU scaling over 80 worlds measured 64.5/s at one worker, 275/s at two,
and 471/s at four. A JAX/fork compatibility warning was emitted; results and
checksums matched. Official GeoX retained-design analysis took 20.6 s and design
comparison 22.7 s. The compute budget and raw evidence contain exact timings.
