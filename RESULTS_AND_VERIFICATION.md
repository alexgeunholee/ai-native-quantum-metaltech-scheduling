# Completed Results — What Was Actually Executed

## Official instances

| Instance | Actual method | Observed schedule | Source reference |
|---|---|---:|---|
| 2×2, 8-bit QUBO | Qiskit Aer QAOA simulator, 4,096 original shots | 4 h; 142 optimal shots (3.47%) | `evidence/original_baselines/quantum/A_QAOA_Aer_counts.json` |
| 2×2, fresh demo | Qiskit Aer QAOA, saved p=3 angles, 4,096 new shots | 4 h; 141 optimal shots (3.44%) | `evidence/live_demo/LIVE_DEMO_RESULTS.json` |
| 3×3, 39-bit QUBO | `neal` classical simulated annealing | 8 h; QUBO energy 0 | `schedule_3x3.json`; `evidence/original_baselines/reports/B_solver_report.json` |

QAOA's original COBYLA p=3 parameter optimization hit the iteration cap, even though the circuit sampled optimal solutions. An independent historical CP-SAT optimization reported `OPTIMAL` for 4 h and 8 h. The live demo uses archived fitted angles rather than reoptimizing them from scratch.

## Synthetic multiobjective manufacturing results

Formula: `F = makespan + 2 × weighted tardiness + 0.02 × electricity USD`; power assumptions and extended job instances are artificial scenario data. For comparable observed 3-job schedules, electricity cost was $23.56 without tariff as a priority and $22.28 with tariff terms (−$1.28, −5.43%), while makespan remained 9 h and weighted tardiness remained 1. The extension uses 40 bits and 180 couplings. This is not a measured real-factory saving or a comparison claiming classical superiority.

| Jobs | Shortest considered exact H | F there | Improved H | Improved F | Relative composite-score reduction |
|---|---:|---:|---:|---:|---:|
| 4 | 11 | 15.5360 | 12 | 14.5808 | 6.15% |
| 5 | 12 | 16.6684 | 13 | 15.7132 | 5.73% |

Historical Experiment 3: 45 sensitivity trials across 3 job counts × 3 penalty strengths × 5 seeds, plus six Aer QAOA depth runs. Historical Experiment 4: 50 annealer trials, 44 exact-H trial-best objective matches to stored CP-SAT references. Fresh live-demo results are separately stored in `evidence/live_demo/`.

## Two actual VeloxQ GPU quantum-inspired campaigns

**Configuration per job:** `num_rep=256`, `num_steps=1500`. Both sets of four jobs returned successful remote executions. The first run (18:41 UTC) matched three of four historical best references; the live run (20:23 UTC) matched four of four.

| Model | Bits | Interactions | CP-SAT objective | First VeloxQ best | Live VeloxQ best | Live feasible reads |
|---|---:|---:|---:|---:|---:|---:|
| Official H8, 3 jobs | 39 | 181 | 8 h | 8 h | 8 h | 229/256 |
| Energy H9, 3 jobs | 40 | 180 | 11.4456 | 11.4456 | 11.4456 | 211/256 |
| Adaptive H12, 4 jobs | 88 | 698 | 14.5808 | 14.5808 | 14.5808 | 94/256 |
| Adaptive H13, 5 jobs | 128 | 1256 | 15.7132 | 15.7388 (0.163% high) | 15.7132 | 57/256 |

The four benchmarks have differing constraints, so feasible fraction alone is not a controlled measurement of a scaling law. Remote wall time includes API overhead; no apples-to-apples throughput comparison or quantum speedup is established. `VeloxQ` operates GPU-based quantum-inspired software, **not a physical QPU**.

## Evidence organization and verification

Original baseline: 43 SHA-256-manifested files at `evidence/original_baselines/`; robustness and adaptive campaigns likewise include manifests and recorded CP-SAT output. Initial VeloxQ has `evidence/veloxq_initial_campaign/SHA256_MANIFEST.json`. Fresh live demo contains raw `LIVE_DEMO_RESULTS.json`, actual Gantt PNGs and CSV measurements. Read `audits/` for independent consistency reviews.

Run `python scripts/verify_submission.py` from the repository root to check model hashes where supplied, mandatory JSON scheduling feasibility and live-run consistency. This only rechecks saved evidence; it **does not rerun any CP-SAT solver, QAOA circuit, `neal` or VeloxQ job**, and recorded `OPTIMAL` statuses are used as certified references in the original runs.
