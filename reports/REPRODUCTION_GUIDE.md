# Reproduction Guide

From WSL Ubuntu 22.04:

```bash
cd /mnt/c/Users/bjw-0/Downloads/geo-causal-bench
source .codex-wsl-env.sh
python -m geocausal.cli pipeline --resume
ruff format --check src tests scripts
ruff check src tests scripts
mypy src
pytest -q
python -m build
python scripts/verify_evidence.py
```

`E14` refuses to run when canonical final evidence exists. To reproduce final
numbers without violating one-way access, verify the committed Parquet hashes
and use `artifacts/results.duckdb`; do not delete final receipts or rerun the
protected command under the same protocol. Raw public acquisition is reproduced
with `python scripts/acquire_public.py` in the isolated environment. R known
answers use `Rscript r/qualify_methods.R`.
