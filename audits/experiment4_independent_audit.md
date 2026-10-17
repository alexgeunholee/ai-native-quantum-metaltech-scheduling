# Experiment 4 — Independent Scientific Audit and Submission Addendum

**Execution date:** 2026-10-17. **Actual solver:** classical `dwave-neal` simulated annealing operating on QUBO binary quadratic models; **reference:** independent OR-Tools CP-SAT. **Hardware:** no QPU, no VeloxQ, no new Qiskit Aer execution in this experiment.

## The problem

The official MetalTech problem schedules operations in strict T (lathe) → F (milling) → S (welding) order under non-overlap constraints. The mandatory baseline minimizes makespan and was solved in Option A: 4 h (2×2 via real Qiskit Aer QAOA circuit sampling) and 8 h (3×3 via classical QUBO simulated annealing). The synthetic Stage 2 extension introduces milling outage `[3,5)`, job deadlines and priority weights, and illustrative time-of-use electricity costs; Z4 and Z5 are additional **synthetic** jobs.

The economic objective is `F = makespan_hours + 2 × weighted_tardiness_hours + 0.02 × electricity_cost_usd`. Previous Experiment 3 restricted the QUBO to the *shortest feasible makespan*. Experiment 4 addresses the observed problem that shortening makespan may prevent meeting more important weighted deadlines, increasing the full business objective.

## Technical solution and distinguishing contribution

Each binary decision `x[j,m,t]` states whether job `j` starts machine operation `m` at discrete hour `t`. One-hot, machine-capacity, and precedence penalties enforce scheduling requirements; infeasible milling-operation starts are discarded. Candidate windows are reduced with earliest/latest start bounds, and per-operation electricity charges and tardiness costs enter as linear terms. The new exact-finish anchor at trial horizon `H` is `P*(1 - sum_j x[j,S,H-p[j,S]])^2`, where a feasible machine-exclusive schedule permits exactly one finishing job at `H`. Thus **for feasible exact-H solutions**, the QUBO energy equals `F − H`, permitting objective comparisons across separately sampled horizons after adding back `H`.

The workflow first solves a minimum-makespan CP-SAT model, then compares QUBO annealing across multiple exact horizons and independently certifies each with a corresponding exact-horizon CP-SAT run. It also solves the **unrestricted** weighted objective in CP-SAT and verifies the best adaptive QUBO result against this certified reference. The distinctive project contribution is this transparent integration and validation—not a claim to have invented QAOA, quantum advantage, or globally novel QUBO encoding.

## Experiment 4 verified results

| Jobs | Horizon (h) | Variables | Quadratic terms | Exact-H CP-SAT optimum | Classical QUBO best | Exact-H optimum trials |
|---|---:|---:|---:|---:|---:|---:|
| 3 | 9 | 40 | 180 | 11.4456 | 11.4456 | 10 / 10 |
| 4 | 11 | 76 | 536 | 15.5360 | 15.5360 | 10 / 10 |
| 4 | 12 | 88 | 698 | 14.5808 | 14.5808 | 10 / 10 |
| 5 | 12 | 113 | 1,010 | 16.6684 | 16.6684 | 9 / 10 |
| 5 | 13 | 128 | 1,256 | 15.7132 | 15.7132 | 5 / 10 |

**Total: 50 independent annealing trials, of which 44 matched the exact-horizon optimum.** Each trial comprised 240 annealing reads, i.e. 12,000 samples over all trials. They are not 12,000 statistically independent optimization *trials*; the reproducibility unit is the independent configured run/seed.

| Jobs | Minimum-makespan fixed-horizon best | Adaptive QUBO best and makespan | Reduction in business objective | Matches unrestricted CP-SAT? |
|---|---:|---:|---:|---|
| 3 | 11.4456 (9 h) | 11.4456 (9 h) | 0% | Yes, CP-SAT OPTIMAL |
| 4 | 15.5360 (11 h) | 14.5808 (12 h) | 6.15% | Yes, CP-SAT OPTIMAL |
| 5 | 16.6684 (12 h) | 15.7132 (13 h) | 5.73% | Yes, CP-SAT OPTIMAL |

The improved 4- and 5-job schedules trade one additional hour of makespan for a reduction in weighted customer tardiness from 2 to 1, enough to improve the total modeled objective. **These percentages are reductions in an arbitrary weighted score, not dollar savings or quantum speedups.**

### Repeatability and sensitivity

For the hardest configuration, five jobs and H=13, penalty `P=25` reached the exact-H optimum in 4/5 seeds, versus 1/5 for `P=100`. The observed best annealer schedules matched the unrestricted optimum in 5/10 runs overall at this H. This emphasizes that higher feasibility rates with larger penalties do not guarantee more optimum hits. The sample is limited; do not extrapolate to industrial scale.

## Independent audit performed after receipt

1. Verified all **29** file SHA-256 entries against contents of `ERP_Experiment4_Adaptive_Horizon_Evidence_20261017T161924873224Z.zip` (30 archive entries including manifest).
2. Reconstructed and checked all **50** best-per-trial schedules: exactly one T/F/S operation per job, exact durations, machine non-overlap, T→F→S precedence, milling outage avoidance, and required exact makespan.
3. Independently recomputed all **50** trial schedule objectives, tariff electricity costs, and weighted tardiness. Values matched the records.
4. Recomputed the total QUBO energy from the exported JSON coefficients and each chosen bit assignment; it matched the stored sample energy and `F-H` (within floating point tolerance).
5. Confirmed five per-horizon and three unrestricted CP-SAT reports had `status=OPTIMAL` and `certified=true` and that their schedules agreed with the same independent verifier.
6. Verified exported model sizes and exact-horizon optimum-hit counts against each trial record.

### Scientific qualifications

- `neal` is a **classical** simulated-annealing QUBO solver, not physical quantum annealing. Experiment 4 made **no new Qiskit Aer circuit runs**; the Qiskit quantum requirement is satisfied by the original 2×2 baseline experiment.
- CP-SAT certification applies to the **specified discrete synthetic instances and objective**, not all possible factory environments.
- Runtime and feasibility metrics are Colab-software-specific; they do not demonstrate quantum computational advantage.
- Z4–Z5 data, all production disruptions, priorities, and electricity tariffs are project-designed synthetic values, not organizers' data or measured factory values.
- The earlier 3-job QAOA COBYLA fit did **not** certify optimizer convergence, although optimal schedules were observed in actual Aer shots.
- The mandatory files `schedule_2x2.json` and `schedule_3x3.json` remain the official-output artifacts. The Experiment 4 extended schedules are **supplementary**.

## Submission checklist — still pending human actions

Confirm team lock-in; publish a **public MIT-licensed** Git repository containing the baseline source and required JSON schedules; verify README, AI-use disclosure, project design and dated development log reflect the additional experiments; **record and link the actual ≤5-minute video**; submit the organizer's real Google Form by **2026-10-18 15:00 UTC+2 / 09:00 EDT**; and prepare the actual three-minute live presentation and approximately two-minute Q&A. The present ZIP is **not** itself an organizer submission.
