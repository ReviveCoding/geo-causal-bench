"""Empirically qualify JAX CUDA and XGBoost CUDA in the WSL runtime."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from importlib import metadata
from pathlib import Path


def gpu_snapshot() -> str:
    command = [
        "nvidia-smi",
        "--query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    return subprocess.check_output(command, text=True).strip()


def main() -> None:
    import jax
    import jax.numpy as jnp
    import numpy as np
    import xgboost as xgb

    devices = jax.devices()
    gpu_devices = jax.devices("gpu")
    if len(gpu_devices) != 1:
        raise RuntimeError(f"Expected exactly one visible GPU, found {gpu_devices!r}")

    gpu = gpu_devices[0]
    key = jax.random.key(20260909)
    size = 6144
    with jax.default_device(gpu):
        left = jax.random.normal(key, (size, size), dtype=jnp.float32)
        right = jax.random.normal(
            jax.random.fold_in(key, 1), (size, size), dtype=jnp.float32
        )

        @jax.jit
        def workload(a: jax.Array, b: jax.Array) -> jax.Array:
            return jnp.tanh(a @ b).mean()

        compile_start = time.perf_counter()
        compiled_result = workload(left, right)
        compiled_result.block_until_ready()
        compile_and_first_sec = time.perf_counter() - compile_start

        run_start = time.perf_counter()
        repeated_result = workload(left, right)
        repeated_result.block_until_ready()
        steady_state_sec = time.perf_counter() - run_start

    # Host arrays intentionally avoid making CuPy an implicit interoperability
    # dependency. XGBoost must still execute histogram training on ``cuda``.
    x_train = np.arange(4096, dtype=np.float32).reshape(1024, 4)
    y_train = (np.arange(1024) % 2).astype(np.float32)
    dtrain = xgb.QuantileDMatrix(x_train, y_train)
    xgb_start = time.perf_counter()
    booster = xgb.train(
        {"device": "cuda", "tree_method": "hist", "max_depth": 3, "seed": 20260909},
        dtrain,
        num_boost_round=8,
    )
    xgb_sec = time.perf_counter() - xgb_start

    payload = {
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "jax_version": metadata.version("jax"),
        "jaxlib_version": metadata.version("jaxlib"),
        "xgboost_version": metadata.version("xgboost"),
        "backend": jax.default_backend(),
        "devices": [str(device) for device in devices],
        "gpu_device": str(gpu),
        "matrix_size": size,
        "compile_and_first_sec": compile_and_first_sec,
        "steady_state_sec": steady_state_sec,
        "result": float(repeated_result),
        "nvidia_smi_after": gpu_snapshot(),
        "xgboost_cuda_train_sec": xgb_sec,
        "xgboost_boosted_rounds": booster.num_boosted_rounds(),
    }
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    if len(sys.argv) > 1:
        output = Path(sys.argv[1])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
