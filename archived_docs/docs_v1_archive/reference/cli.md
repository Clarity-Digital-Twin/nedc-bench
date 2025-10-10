# CLI Reference

Status: The standalone CLI is not implemented yet. The `nedc-bench` console entry in `pyproject.toml` is intentionally disabled. Use the API or provided scripts instead.

## Alternatives

- Shell wrapper (Alpha): `./run_nedc.sh ref.list hyp.list`
- Beta scripts: `python scripts/run_beta_batch.py`
- Parity check: `python scripts/compare_parity.py`
- API server: `uv run uvicorn nedc_bench.api.main:app --reload`

## Examples

- Run Alpha tool over lists:

  ```bash
  ./run_nedc.sh data/csv_bi_parity/csv_bi_export_clean/lists/ref.list \
                 data/csv_bi_parity/csv_bi_export_clean/lists/hyp.list
  ```

- Run all Beta algorithms and save SSOT:

  ```bash
  uv run python scripts/run_beta_batch.py
  ```

- Compare Alpha vs Beta parity:

  ```bash
  uv run python scripts/compare_parity.py
  ```

- Start API locally and use REST/WebSocket:

  ```bash
  uv run uvicorn nedc_bench.api.main:app --reload
  # Open http://localhost:8000/docs
  ```

## Roadmap

If a CLI is needed later, it will be added under `nedc_bench/cli.py` and re-enabled via `[project.scripts]`.
