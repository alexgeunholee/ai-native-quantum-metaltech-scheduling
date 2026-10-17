# AI-Native Quantum — Independent Review of Live-Demo Evidence

**Source:** `AI_Native_Quantum_Live_Demo_20261017T202305Z.zip`
**Source SHA-256:** `9d8ea6b6ce4147eea3344bc8ec89b9e3112c502d4adea005b1d70be24158a222`
**Live archive timestamp:** 2026-10-17 20:23:05 UTC

## Scope and verification performed

The ZIP is readable (CRC check passed). The main structured evidence is `LIVE_DEMO_RESULTS.json`, accompanied by 10 Gantt images, saved plots, and three CSV reports. The documented token was not found in the files. The submitted ZIP does **not** include the raw solver API transcript or a new independent CP-SAT solve; the reported comparisons depend on earlier certified references. The audit independently checked best-schedule operation counts, no machine overlaps, T→F→S precedence, and the [3,5) F-machine outage for synthetic cases. These checks passed on all four live VeloxQ best schedules. The full QUBO formulation can be independently reproduced from the separate live notebook and original research archives.

## Fresh VeloxQ remote results

| Benchmark | Earlier best objective | Fresh best objective | Fresh feasible samples | Remote wall time (s) | Exact reference matched |
|---|---:|---:|---:|---:|:---:|
| `official_3jobs_H8` | 8.0000 | 8.0000 | 229/256 (89.45%) | 3.625 | Yes |
| `energy_3jobs_H9_P25` | 11.4456 | 11.4456 | 211/256 (82.42%) | 2.196 | Yes |
| `energy_4jobs_H12_P25` | 14.5808 | 14.5808 | 94/256 (36.72%) | 2.289 | Yes |
| `energy_5jobs_H13_P25` | 15.7388 | 15.7132 | 57/256 (22.27%) | 3.167 | Yes |

**Interpretation:** The first campaign matched 3/4 reference objectives; the live repeat matched 4/4. The five-job gap reduced from 0.0256 (0.163%) to 0 on this repeat. Neither result should be erased: each reflects an actual independent run. All fresh runs reported 256 repetitions and the same fixed frozen QUBOs. QUBO energies for the last three cases differ from the composite business objective because the energy function encodes a fixed horizon, linearized terms, penalty structure, and offset.

## Other freshly executed stages

* **QAOA Aer:** 141/4096 optimal measurements (3.44%) at the four-hour reference optimum; archived parameter angles, so this is fresh sampling, **not** a new fit.
* **Official 3×3 classical QUBO:** 8-hour optimal makespan, 1138/1200 feasible samples.
* **Synthetic energy-aware three-job QUBO:** composite optimum 11.4456, 9-hour makespan, modeled electricity $22.28, 938/1200 feasible samples.
* **New penalty-sensitivity trials:** nine fresh single-seed experiments across 3–5 jobs and penalties 5/25/100. This is not the same as the historical multi-seed robustness census.
* **Fresh QAOA depth samples:** p=1: 34/1024 (3.32%), p=2: 8/1024 (0.78%), p=3: 95/1024 (9.28%). Previously fitted parameters were reused; no optimizer convergence claim.
* **Fresh adaptive-horizon tests:** 4 jobs/H11: 15.5360, 4 jobs/H12: 14.5808, 5 jobs/H12: 16.6684, 5 jobs/H13: 15.7132. All four matched their archived CP-SAT references.

## Scientific conclusions and limitations

1. The demo demonstrates fresh executions across all seven stages and retains a clear distinction between new and historic solver results.
2. Four live VeloxQ runs return feasible, exact-reference best schedules, including the largest 128-variable, 1,256-interaction model. The earlier VeloxQ session contains a nonzero 128-variable gap, indicating observed variability between runs.
3. The live Aer QAOA shots are simulator samples, while VeloxQ is a GPU-based quantum-inspired optimizer. **No physical QPU experiment or quantum speedup is demonstrated.**
4. Several larger instances, maintenance windows, due dates and electricity tariffs are **synthetic**. The adaptive-horizon improvement concerns the specified composite objective, not general monetary savings.
5. The archive confirms claimed sampled outcomes, but further scientific reproducibility relies on sharing the complete executable Colab notebook and unmodified input coefficients in the public repository. The live export ZIP alone is insufficient to rebuild all QUBOs from scratch.

## Submission recommendation

**Approve the live-demo results for inclusion in the presentation and submission repository.** Update Stage V Step 5.5 to show first-campaign 3/4 and live repeat 4/4; keep both source ZIP files. The demonstration video still needs to be recorded/uploaded, and GitHub/team/form submission must be completed separately; no ZIP upload implies these steps have been done.
