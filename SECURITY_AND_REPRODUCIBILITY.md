# Security and reproducing experiments

No API key or password should be committed. The actual VeloxQ token is **not included**. If you rerun a live benchmark, enter a replacement credential through the notebook's masked prompt or a private `VELOX_TOKEN` environment variable. Avoid exporting the notebook after printing credentials; avoid pasting keys into a public GitHub issue or notebook cell. Keep `.env`, `config.py`, and Secrets outside the repository.

To inspect all results with **no computation or credentials**, open `notebooks/02_PRESENT_Seven_Stage_Recorded_Results.ipynb` in Colab. The archived outputs travel with the notebook. To perform **fresh local computation**, use `notebooks/01_LIVE_Seven_Stage_Demo.ipynb` or the historical study notebooks; some stochastic result counts can vary and external packages/solver APIs may change. VeloxQ's remote backend requires access from its provider.

Run the independent lightweight verifier: `python scripts/verify_submission.py`. This uses only Python standard-library and saved JSON/manifest files; it validates structure, file hashes, original schedule feasibility and reported observations without launching any solvers. It cannot substitute for an exact mathematical proof of global optimality, which relies on the historical CP-SAT `OPTIMAL` records.
