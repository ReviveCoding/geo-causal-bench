"""Qualify batched seasonal/compliance DGP kernels on the single JAX GPU."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import jax
import jax.numpy as jnp

from geocausal.artifacts import atomic_write_json

ROOT = Path(__file__).resolve().parents[1]


@jax.jit
def seasonal_batch(keys: jax.Array) -> jax.Array:
    def world(key: jax.Array) -> jax.Array:
        noise = jax.random.normal(key, (40, 393))
        time_axis = jnp.arange(393)
        seasonal = 1 + 0.12 * jnp.sin(2 * jnp.pi * time_axis / 7)
        return jnp.mean(jnp.exp(6 + 0.12 * noise) * seasonal)

    return jax.vmap(world)(keys)


@jax.jit
def compliance_batch(keys: jax.Array) -> jax.Array:
    def world(key: jax.Array) -> jax.Array:
        assignment = jax.random.bernoulli(key, 0.5, (40,))
        dose = jax.random.bernoulli(jax.random.fold_in(key, 1), 0.5, (40, 28))
        baseline = jax.random.lognormal(jax.random.fold_in(key, 2), shape=(40, 28))
        return jnp.sum(baseline * dose * assignment[:, None] * 0.08)

    return jax.vmap(world)(keys)


def measure(function: object, keys: jax.Array) -> dict[str, float]:
    started = time.perf_counter()
    result = function(keys)  # type: ignore[operator]
    result.block_until_ready()
    first = time.perf_counter() - started
    started = time.perf_counter()
    result = function(keys)  # type: ignore[operator]
    result.block_until_ready()
    steady = time.perf_counter() - started
    return {
        "first_sec": first,
        "steady_sec": steady,
        "worlds_per_sec": len(keys) / steady,
        "checksum": float(jnp.sum(result)),
    }


def main() -> None:
    keys = jax.random.split(jax.random.PRNGKey(20260915), 1024)
    payload = {
        "extension_id": "OPERATIONS-STUDY-001/COMPLIANCE-SEMANTICS-001",
        "evidence_class": "MEASURED",
        "backend": jax.default_backend(),
        "devices": [str(device) for device in jax.devices()],
        "batch_worlds": len(keys),
        "seasonal_kernel": measure(seasonal_batch, keys),
        "compliance_kernel": measure(compliance_batch, keys),
        "nvidia_smi": subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.used,driver_version",
                "--format=csv,noheader",
            ],
            text=True,
        ).strip(),
        "claim_boundary": "GPU_KERNEL_QUALIFICATION_NOT_WHOLE_PIPELINE_SPEEDUP",
    }
    atomic_write_json(ROOT / "evidence/operations/gpu_execution.json", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
