# ERP Experiment 3 — Independent Audit, 17 October 2026

## Evidence examined
Archive: `ERP_Experiment3_Evidence_20261017T160748779808Z.zip`. The archive contains 34 files including its manifest. Every one of the 33 non-manifest files matches the SHA-256 listed in `manifest.json`. All 45 best-per-trial decoded schedules were independently checked for operation duration, completeness, precedence, machine exclusivity, F-machine outage [3,5), integer timing, exact fixed-horizon upper bound, tardiness, tariff calculations, and objective. All 45 passed. Nine exported QUBO coefficient sets were checked against their metadata counts. No independent execution of Qiskit Aer, CP-SAT, or simulated annealing was conducted during this audit; solver run statuses derive from archived Colab output.

## Classical QUBO scaling, synthetic industrial extension

| Jobs | CP-SAT certified minimum makespan | QUBO variables | Quadratic interactions | CP-SAT exact minimum-H optimum | CP-SAT unrestricted weighted optimum | Best QUBO objective at minimum H |
|---:|---:|---:|---:|---:|---:|---:|
| 3 | 9 h | 40 | 180 | 11.4456 | 11.4456 | 11.4456 |
| 4 | 11 h | 76 | 536 | 15.5360 | 14.5808 (12 h) | 15.5360 |
| 5 | 12 h | 113 | 1,010 | 16.6684 | 15.7132 (13 h) | 16.6684 |

QUBO best results match the certified **minimum-makespan-horizon** CP-SAT optimum. In the 4/5 job instances, restricting makespan to its minimum leaves an unrestricted weighted-objective gap of 0.9552 units (~6.55% and ~6.08%, respectively). This is an objective tradeoff and cannot be described as a QUBO solver failure.

## Penalty sensitivity (five seeds per cell)

| Jobs | P=5 feasible samples / optimum matches | P=25 feasible samples / optimum matches | P=100 feasible samples / optimum matches |
|---:|---|---|---|
| 3 | 65.17%; 5/5 | 82.83%; 5/5 | 73.83%; 5/5 |
| 4 | 16.40%; 5/5 | 39.07%; 5/5 | 60.53%; 5/5 |
| 5 | 5.06%; 2/5 | 29.18%; 5/5 | 49.29%; 3/5 |

“Optimum matches” refers to best feasible schedule among the reads for a run, not all samples; “feasible percentage” refers to actual recorded simulated annealing reads. `neal` is a classical simulated annealing solver. No physical QPU and no VeloxQ was used.

## Qiskit Aer QAOA depth experiment (8 qubits, 2,048 measured shots per seed)

| Depth | Seed 23 optimal samples | Seed 67 optimal samples | COBYLA convergence flags |
|---|---:|---:|---|
| p=1 | 8 (0.391%) | 74 (3.613%) | True; True |
| p=2 | 12 (0.586%) | 64 (3.125%) | True; False |
| p=3 | 129 (6.299%) | 173 (8.447%) | False; False |

All six runs contain 2,048 count observations each. QAOA was sampled on Qiskit Aer and parameterized circuits were optimized using Qiskit Statevector expectation and SciPy COBYLA. The two best p=3 fractions do not establish an optimizer convergence claim, general depth law, physical hardware performance or quantum advantage.

## Recommended targeted follow-up

Test **adaptive exact-horizon QUBO** on 4 and 5 jobs at their certified minimum makespan and one hour beyond. The existing model fixed H at the minimum makespan, which can block a better weighted-objective schedule. An exact-H one-hot completion anchor ensures the QUBO objective differs from F only by the constant H. Compare across horizons, with independent CP-SAT certification. Existing certified reference objectives are 14.5808 at 4 jobs / H=12, and 15.7132 at 5 jobs / H=13; these numbers are *targets for the new test*, not outcomes of new annealer executions.

This project solves a small, synthetic industrial extension; the official 2x2/3x3 baseline is supported by the separate Option A v2 evidence. Keep the public repository, MIT license, submission JSON files, verified README, development log, project design, 5-minute demo video, and 3-minute live talk separate from scientific claims about the solver.
