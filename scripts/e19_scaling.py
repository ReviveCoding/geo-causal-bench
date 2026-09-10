"""Measure JAX batch scaling and bounded CPU worker scaling."""

from __future__ import annotations

import concurrent.futures
import json
import time
from functools import partial
from pathlib import Path

import numpy as np


def cpu_world(index: int) -> float:
    from geocausal.dgp import generate_world
    from geocausal.estimators import estimate_all

    world, _ = generate_world(
        seed=20260909 + index,
        world_id=f"SCALE-{index:04d}",
        scenario_id=f"S{index % 14:02d}",
    )
    return sum(item.estimate for item in estimate_all(world).values())


def main() -> None:
    import jax
    import jax.numpy as jnp

    root = Path(__file__).resolve().parents[1]

    @partial(jax.jit, static_argnums=1)
    def gpu_batch(key: jax.Array, batch: int) -> jax.Array:
        innovations = jax.random.normal(key, (batch, 40, 203), dtype=jnp.float32)
        return jnp.exp(jnp.clip(6.1 + 0.55 * innovations, 0.5, 7.5)).mean()

    gpu_rows = []
    for batch in (16, 64, 256):
        key = jax.random.fold_in(jax.random.key(20260909), batch)
        started = time.perf_counter()
        compiled = gpu_batch.lower(key, batch).compile()
        compile_sec = time.perf_counter() - started
        started = time.perf_counter()
        result = compiled(key)
        result.block_until_ready()
        steady_sec = time.perf_counter() - started
        started = time.perf_counter()
        rng = np.random.default_rng(20260909 + batch)
        cpu = np.exp(
            np.clip(6.1 + 0.55 * rng.normal(size=(batch, 40, 203)), 0.5, 7.5)
        ).mean()
        cpu_sec = time.perf_counter() - started
        gpu_rows.append(
            {
                "batch": batch,
                "compile_sec": compile_sec,
                "gpu_steady_sec": steady_sec,
                "cpu_numpy_sec": cpu_sec,
                "gpu_worlds_per_sec": batch / steady_sec,
                "cpu_worlds_per_sec": batch / cpu_sec,
                "steady_gpu_speedup": cpu_sec / steady_sec,
                "gpu_result": float(result),
                "cpu_result": float(cpu),
            }
        )

    cpu_rows = []
    tasks = list(range(80))
    for workers in (1, 2, 4):
        started = time.perf_counter()
        if workers == 1:
            values = [cpu_world(index) for index in tasks]
        else:
            with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
                values = list(pool.map(cpu_world, tasks))
        runtime = time.perf_counter() - started
        cpu_rows.append(
            {
                "workers": workers,
                "worlds": len(tasks),
                "runtime_sec": runtime,
                "worlds_per_sec": len(tasks) / runtime,
                "checksum": float(sum(values)),
            }
        )
    payload = {
        "jax_backend": jax.default_backend(),
        "jax_devices": [str(device) for device in jax.devices()],
        "gpu_batch_scaling": gpu_rows,
        "cpu_worker_scaling": cpu_rows,
        "bounded_worker_max": 4,
    }
    output = root / "evidence" / "runtime" / "e19_scaling.json"
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
