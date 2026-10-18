# Project Design — AI-Native Hybrid Quantum-Classical Manufacturing Scheduling

**QPoland Quantum Hackathon 2026 | MetalTech challenge**  
**Team:** AI-Native Quantum · **Discord:** `@alexglee`  
**GitHub:** https://github.com/alexgeunholee/ai-native-quantum-metaltech-scheduling  
**Methods:** QUBO / QAOA on Qiskit Aer / classical `neal` simulated annealing / OR-Tools CP-SAT / remote VeloxQ GPU quantum-inspired optimization  
**Status:** Completed, experimentally supported research design; physical quantum hardware and quantum speedup are **not** claimed.

## Executive design summary

This project solves the compulsory MetalTech factory scheduling instances and investigates an extension that is closer to operational planning. The central engineering problem is to schedule ordered job operations on exclusive machines while controlling not only the **makespan** but also **customer lateness, a planned machine outage, and time-of-use energy cost**. Our contribution is an auditable integration of established QUBO and quantum/classical solver tools, time-window reduction, controlled robustness testing, and an **adaptive exact-horizon search**. We do **not** claim to have invented QUBO, QAOA, simulated annealing, or quantum-inspired GPU solvers.

The seven research stages are: **I — original problem; II — QUBO design; III — official quantum/classical baselines; IV — industrial scheduling extension; V — solver robustness and VeloxQ; VI — adaptive-horizon correction; VII — independent qualification and presentation**. All required official answers are kept in [`schedule_2x2.json`](schedule_2x2.json) and [`schedule_3x3.json`](schedule_3x3.json); extended cases use synthetic, openly documented inputs.

---

## Stage I — Official production scheduling problem

### 1.1 Resources, jobs, and operation order

MetalTech requires nonpreemptive jobs to traverse machines in a fixed order. `T` denotes lathe/turning, `F` milling, and `S` welding. A job's next operation cannot start before the previous operation completes; each machine can run at most one operation at a time. The official job processing times (hours) are:

**Official 2×2 instance, T → F**

| Job | Turning T | Milling F | Sequence |
|---|---:|---:|---|
| Z1 | 2 | 1 | T → F |
| Z2 | 1 | 2 | T → F |

**Official 3×3 instance, T → F → S**

| Job | Turning T | Milling F | Welding S | Sequence |
|---|---:|---:|---:|---|
| Z1 | 2 | 1 | 2 | T → F → S |
| Z2 | 1 | 2 | 1 | T → F → S |
| Z3 | 2 | 2 | 1 | T → F → S |

The official objective is **minimum makespan** `C_max`: the time at which the last required operation finishes. Independent CP-SAT references reported optimal makespans **4 hours (2×2)** and **8 hours (3×3)**. Our archived official schedules attain these references.

### 1.2 Why the two official instances use different solvers

The smaller 2×2 problem is the **quantum-algorithm baseline**: its eight-bit QUBO is implemented as a QAOA circuit and genuinely sampled on the **Qiskit Aer quantum simulator**. The larger 3×3 problem is the **QUBO optimization baseline**: its 39-bit model is solved with a **classical** simulated-annealing BQM optimizer (`neal`). We distinguish an actual quantum-circuit simulation from classical or quantum-inspired QUBO software, rather than labelling all methods “quantum execution.”

## Stage II — Mathematical formulation and binary energy model

### 2.1 Sets, variables, and feasible start windows

Let `J` denote jobs and `O_j` the ordered operations for job `j`. Each operation `o=(j,m)` has required machine `m`, processing duration `d_o`, and a finite set of legal integer start times `A_o(H)` within candidate horizon `H`. A **binary start-time decision** is:

```text
x[o,t] = 1  if operation o starts at integer time t;
         0  otherwise, for t in A_o(H).
```

Hours are discrete. The completion time of an operation selected at time `t` is `t + d_o`; the job completion is that of its last operation. To reduce QUBO size, the earliest possible start of an operation is bounded below by the sum of durations of its **predecessors in the same job**. Its latest candidate start is bounded above by `H − (its duration + all subsequent durations in the job)`. These are safe *within the chosen horizon* and do not exclude a feasible schedule completing by `H`.

In the official 3×3 case, naïvely enumerating starts before these bounds gives **72** candidates; admissible pruning leaves **39 bits**, a **45.83%** reduction, and 181 actual quadratic interactions at H=8. The official 2×2 H=4 model has 8 bits and 12 interactions. The model coefficients, mappings and tests are preserved in `evidence/original_baselines/`.

### 2.2 Hard scheduling constraints

The model must enforce all of the following:

**Exactly one start per operation.** Every operation is scheduled once and not split into several segments:

```text
sum_{t in A_o(H)} x[o,t] = 1       for every operation o.
```

**Machine exclusivity.** For any pair of candidate operation starts `(o,t)` and `(p,u)` using the same machine, where their occupied time intervals overlap (`[t,t+d_o)` intersects `[u,u+d_p)`), both bits cannot equal one:

```text
x[o,t] + x[p,u] <= 1.
```

**Job precedence.** For consecutive operations `o` then `p` of one job, any proposed pair with `u < t+d_o` is forbidden. This encodes T→F (and F→S in the 3×3 and extensions). End times are non-inclusive, so back-to-back machine use is permitted.

**Fixed-horizon bound.** Only candidate starts whose operations can finish within `H` enter the QUBO. Thus every feasible decoded assignment has `C_max <= H` before exact-finish anchoring.

**Planned maintenance (synthetic extension only).** Milling (F) is unavailable over `[3,5)`. Candidate milling starts whose processing intervals overlap downtime are removed. This is a **hard outage**, not a monetary penalty for using the machine.

### 2.2A Feasibility conditions and verification

A manufacturing schedule is **feasible** if each required operation selects exactly one integer start time from its admissible time window; every job completes operations in its prescribed technological order; no two operations using the same machine overlap; and every operation finishes by the selected horizon `H`. The schedule is nonpreemptive: an operation runs continuously for its assigned duration once started. For the synthetic industrial extension, no milling operation may overlap the planned maintenance interval `[3,5)`.

For the **adaptive exact-horizon** models, feasibility additionally requires the actual makespan to equal `H`, rather than merely satisfy `C_max <= H`. This is enforced by the documented terminal-finish anchor together with the usual scheduling constraints.

After a solver returns binary assignments, we reconstruct operation start and finish times and check the original scheduling requirements independently of the solver's reported energy. A zero or low QUBO energy by itself is not sufficient proof of feasibility if a model or penalty scale is incorrect. The official benchmark optima of **4 hours (2×2)** and **8 hours (3×3)**, and the reported finite synthetic benchmark objectives, are supported by **previously recorded OR-Tools CP-SAT `OPTIMAL` results**; the live demo compares new candidate schedules against these historical references and does not rerun CP-SAT.

### 2.3 Convert hard constraints into a QUBO/BQM

A Quadratic Unconstrained Binary Optimization energy assigns penalties to infeasible bit configurations. Define:

- `C_machine`: all pairs of candidate starts that overlap on the same machine.
- `C_order`: all pairs that violate within-job precedence.
- `P1,P2,P3 > 0`: one-hot, machine and precedence penalty scales.
- `c[o,t]`: optional cost of selecting start `t` for operation `o`.

A representative model is:

```text
E(x) = P1 * sum_o (1 - sum_{t in A_o} x[o,t])^2
     + P2 * sum_{(a,b) in C_machine} x[a] * x[b]
     + P3 * sum_{(a,b) in C_order}   x[a] * x[b]
     +       sum_{o,t in A_o} c[o,t] * x[o,t].
```

Because bits satisfy `x^2=x`, the squared one-hot terms expand into ordinary **linear and quadratic** coefficients plus a constant offset. The expression is a QUBO even though the engineering requirements began as constraints. The offset is preserved so recomputed sample energies can be reconciled with solver energies. For instance, the frozen official 3-job BQM has **39 bits / 181 interactions / offset 45**; an energy of **zero** on the pure-penalty H=8 model indicates zero encoded violations, *not* a proof that no shorter `H` works. The separate CP-SAT reference certified that the actual optimum is eight hours.

Our experimental penalty scales are model dependent. The official small cases use their stored settings, while the synthetic robustness campaign deliberately compares `P=5,25,100`. The numerical meaning of a penalty must always be considered relative to the objective-coefficient range. We **decode and inspect each schedule**, because low sampled energy alone is not a sufficient feasibility certificate if weights are poorly calibrated.

### 2.4 Mapping QUBO to a quantum QAOA cost Hamiltonian

For quantum-circuit simulation, a binary bit `x_i` can be expressed using Pauli Z as `x_i=(I−Z_i)/2`. Substituting this into the QUBO creates a diagonal cost Hamiltonian made of I, Z and ZZ terms. In standard QAOA, an alternating ansatz uses phase separation based on this cost Hamiltonian and a transverse-X mixing operator. A classical COBYLA loop estimates circuit parameters; the selected circuit is measured in the computational basis to obtain sampled bitstrings, which are mapped back to operation start times.

The **eight-qubit 2×2** simulator circuits are small enough for actual Qiskit Aer sampling. The original recorded test used QAOA **depth p=3** and **4,096 shots**, observing an optimal schedule **142 times** (3.47%). The later fresh demonstration sampled **141/4,096** (3.44%) using previously fitted parameters. The original selected p=3 parameter optimizer reached its iteration limit; therefore we disclose that a valid best sampled solution was observed but **variational parameter convergence was not proved**. There was no physical QPU run.

### 2.5 Independent classical reference model

We also expressed each scheduling instance in **OR-Tools CP-SAT** with interval/scheduling constraints, start/finish domains, resource non-overlap, and precedence. CP-SAT solved the official makespan problem and, in later stages, the synthetic business objective. Captured `OPTIMAL` statuses are our **historical exact reference evidence for the corresponding finite discrete models**. The public lightweight offline verifier reads saved reports and rechecks feasibility; it is **not itself another CP-SAT run or an independent mathematical proof of a broader scheduling class**.

## Stage III — Executed official baselines

| Experiment | Model size | Actual method | Best observed result | Reference / qualification |
|---|---|---|---|---|
| Official 2 jobs × 2 machines, H4 | 8 bits / 12 interactions | Qiskit Aer QAOA circuit, 4,096 shots | Feasible 4-hour schedule; 142 historical optimal shots | CP-SAT `OPTIMAL`, four hours; COBYLA p3 not converged |
| Live repetition, same official model | 8 bits | New Aer circuit measurement using archived fitted angles | 4 hours; 141/4,096 optimal shots | Genuine new sampling, not a new variational fit |
| Official 3 jobs × 3 machines, H8 | 39 bits / 181 interactions | Classical `neal` QUBO sampling | Eight-hour schedule, zero penalty energy | CP-SAT `OPTIMAL`, eight hours; no QPU claim |

An eight-hour baseline example is available in `schedule_3x3.json`: T runs Z1 `[0,2)`, Z2 `[2,3)`, Z3 `[3,5)`; F runs Z1 `[2,3)`, Z2 `[3,5)`, Z3 `[5,7)`; S runs Z1 `[3,5)`, Z2 `[6,7)`, Z3 `[7,8)`. All durations, job dependencies and resource capacities are satisfied.

## Stage IV — Synthetic industry-oriented scheduling extension

### 4.1 Additional constraints and assumptions

The extended three-job model retains the official T→F→S durations and adds the following **synthetic** inputs:

| Attribute | Synthetic value | Operational meaning |
|---|---|---|
| Milling unavailability | `[3,5)` hours | Planned downtime during which no milling task may run |
| Customer due dates | Z1=7; Z2=5; Z3=10 hours | Target completion time for each job |
| Priority weights | Z1=1; Z2=3; Z3=1 | Z2 lateness receives triple weight |
| Power consumption | T=8; F=12; S=6 kW | Constant illustrative consumption when operating |
| Peak tariff | $0.27/kWh during hours `h mod 8` in {2,3,4,5} | Illustrative time-of-use price |
| Other-hour tariff | $0.11/kWh | Illustrative off-peak price |

The outage is applied as a hard constraint. By contrast, deadline tardiness and electricity cost are **soft business terms**, so the optimizer can rationally trade them against makespan when the score weights permit.

### 4.2 Full composite objective and units

For job `j`, define `completion_j` as its final operation finish and `due_j` as its synthetic due time. Its tardiness is:

```text
T_j = max(0, completion_j - due_j)
W   = sum_j weight_j * T_j
```

Let `C_e` represent scheduled electricity charges in USD. The synthetic project-defined composite objective is:

```text
F = C_max + 2 * W + 0.02 * C_e

C_max : hours
W     : weighted hours of job lateness
C_e   : USD of electricity charge
```

The multipliers **2** and **0.02** convert differently dimensioned engineering terms into a **user-selected numerical ranking score**. Its numerical value is *not itself dollars*. Comparing two objective values is meaningful only under the **same synthetic data, tariffs, weights and horizon treatment**.

### 4.3 Electricity cost without additional decision bits

For an operation starting at `t`, let `p_m` be the machine's kW demand and `r(h)` the tariff during hour `h`. Its deterministic charge is:

```text
energy_cost[o,t] = p_m * sum_{h=t}^{t+d_o-1} r(h)  [USD].
```

Because the charge is fully determined once start bit `x[o,t]` is chosen, we can include `0.02*energy_cost[o,t]` **linearly** in the QUBO. Similarly, for the final operation of job `j`, its weighted tardiness can be included linearly as `2*weight_j*max(0,t+d_o-due_j)*x[o,t]`. Thus **no new binary variables** or extra quadratic couplers are required for these costs in this implementation. The three-job H9 formulation remains **40 bits and 180 couplings**, with an offset of 250 in the stored frozen P25 BQM.

### 4.3A Quantifying the cost of industrial realism

The Stage 2 industrial extension was designed to incorporate additional manufacturing requirements while controlling QUBO model size. For the official three-job instance at an eight-hour horizon, the naïve time-indexed formulation contained **72 binary start-time candidates**. Applying feasible earliest- and latest-start bounds reduced this to **39 variables**, a **45.83% reduction**.

For the synthetic three-job industrial extension at a nine-hour horizon, the corresponding naïve formulation contained **81 candidates**. Precedence-aware and horizon-based pruning reduced the count to **48**. The planned milling-machine outage during hours three through five (`[3,5)`) eliminated **eight additional candidates**, producing the final model of **40 binary variables and 180 quadratic interactions**.

| Model and pruning step | Binary start-time candidates | Quadratic interactions in final QUBO |
|---|---:|---:|
| Official 3 jobs, H=8: naïve enumeration | 72 | — |
| Official 3 jobs, H=8: feasible start-window pruning | **39** | **181** |
| Industrial 3 jobs, H=9: naïve enumeration | 81 | — |
| Industrial 3 jobs, H=9: precedence and horizon pruning | 48 | — |
| Industrial 3 jobs, H=9: additionally exclude milling outage | **40** | **180** |

Customer due dates, priority-weighted tardiness, and predetermined electricity tariffs were incorporated through **linear coefficients** associated with the existing operation start-time variables. Consequently, these objective terms required **no additional binary variables or quadratic interactions** in the selected formulation. This result assumes that each operation has a fixed duration and machine power demand and that the time-dependent tariffs and due dates are known before optimization.

The final industrial model was evaluated using **classical simulated annealing** and **VeloxQ GPU-based quantum-inspired optimization**, with previously certified **OR-Tools CP-SAT** solutions used as references. The resulting best feasible schedule matched the certified composite objective of **11.4456**, demonstrating that additional operating considerations could be integrated without a proportional increase in QUBO model size.

These variable reductions are specific to the documented fixed-horizon models. They represent **mathematical model compression**, not physical qubit savings demonstrated on quantum hardware. The number of physical qubits or quantum gates needed by a future QAOA implementation would also depend on hardware constraints, gate compilation, and circuit design; **no 40-qubit industrial QAOA circuit was executed** in this project.

### 4.4 Observed Stage IV outcomes

A synthetic baseline containing outage and weighted deadlines had `C_max=9`, `W=1` and modeled electricity spending **$23.56**. Adding the tariff term and reoptimizing yielded a schedule with `C_max=9`, `W=1`, electricity charge **$22.28**, and total `F=9+2+0.02(22.28)=11.4456`. The difference of **$1.28**, or **5.43%** of the first synthetic electricity charge, is an observed comparison **between these schedules**. The energy-aware result matched the archived unrestricted CP-SAT optimum for the three-job synthetic instance. Neither scenario describes measured MetalTech energy savings.

## Stage V — Robustness, scalability and independent quantum-inspired solver

### 5.1 Penalty sensitivity: 45 historical classical annealing trials

The robustness investigation considered 3, 4, and 5 jobs (the additional jobs synthetic) at certified shortest feasible horizons H9, H11, and H12. For each size, we tested **5, 25, 100** as penalties across **five seeds**, yielding **45** historical `neal` trials. Their fixed minimum-horizon QUBO sizes were 40/180, 76/536 and 113/1010 variables/interactions, respectively.

| Jobs | H | Mean feasible samples at P5 | P25 | P100 | Best-score optimum hits P5 / P25 / P100 |
|---|---:|---:|---:|---:|---|
| 3 | 9 | 65.17% | 82.83% | 73.83% | 5/5 · 5/5 · 5/5 |
| 4 | 11 | 16.40% | 39.07% | 60.53% | 5/5 · 5/5 · 5/5 |
| 5 | 12 | 5.06% | 29.18% | 49.29% | 2/5 · 5/5 · 3/5 |

These percentages describe **sample feasibility**, not the probability of guaranteed global optimization. Increasing penalty can discourage infeasible states while changing the balance of energy scales, and at five jobs P100 produced more feasible samples than P25 but **fewer trial-best optimum matches** in this small test. All reported best-per-trial schedules remained feasible, and numerical conclusions should not be generalized to factory-scale instances.

### 5.2 QAOA depth sensitivity

A separate simulator-only comparison explored **p=1,2,3**, with two fitted starts each and 2,048 shots per run. Individual optimal-shot fractions and optimizer-success flags are retained in `evidence/robustness_scaling/FINAL_RESULTS_FOR_CHATGPT.txt` and the quantum evidence folder. The best observed historical p3 frequency was about **8.45%**; both p3 COBYLA success flags were false. Greater ansatz depth is **not** established here to produce a consistently higher hit rate or more efficient computation.

### 5.3 VeloxQ — Remote GPU-based quantum-inspired benchmark

We reused **the same frozen BQM/QUBO coefficients** rather than refitting a special solver-specific energy function, and ran two separate actual remote VeloxQ campaigns. VeloxQ accepts `dimod.BinaryQuadraticModel` with binary variables, linear/quadratic terms and offset. The experiment configured **`num_rep=256` and `num_steps=1500`** for each job. A **private API credential** was entered interactively or via environment; it is not in public code. The SDK and its documented parameters are at https://github.com/quantumz-io/veloxq_sdk.

| Frozen model | Bits | Interactions | BQM offset | CP-SAT reference | First VeloxQ best | Second/live VeloxQ best | Live feasible reads |
|---|---:|---:|---:|---:|---:|---:|---:|
| Official 3 jobs H8 | 39 | 181 | 45 | 8 h | 8 h | 8 h | 229/256 |
| Energy-aware 3 jobs H9 P25 | 40 | 180 | 250 | 11.4456 | 11.4456 | 11.4456 | 211/256 |
| Adaptive 4 jobs H12 P25 | 88 | 698 | 325 | 14.5808 | 14.5808 | 14.5808 | 94/256 |
| Adaptive 5 jobs H13 P25 | 128 | 1,256 | 400 | 15.7132 | 15.7388 | 15.7132 | 57/256 |

The first campaign matched **three of four** certified best objectives; its five-job result was a valid schedule with a **0.163% score gap**. A later fresh live campaign matched **all four**, including the 128-bit instance. Both outcomes are reported to preserve **stochastic variation**; a single successful repeat cannot prove guaranteed optimum recovery. The live sample counts correspond to feasible reads at **89.45%, 82.42%, 36.72%, 22.27%** for the four models, respectively. Although feasibility becomes less common across these different test cases, changes in constraints and horizon prevent interpreting this as a controlled asymptotic scaling law.

**Interpretation:** VeloxQ provided genuinely executed **GPU quantum-inspired** QUBO optimization, but it was **not physical quantum annealing or a gate-model QPU**. Its observed wall-clock measurements include service and API overhead and are not a hardware-normalized test of advantage over CP-SAT, `neal`, or QAOA Aer. Validity is established by **decoding and checking the schedules**, not just choosing the minimum-energy solver sample.

## Stage VI — Correcting the fixed-minimum-horizon limitation

### 6.1 Why the baseline modeling strategy needed refinement

Minimizing makespan first and restricting all other optimization to that horizon may create a **suboptimal full business score**. A slightly later completion can make an important order less tardy or shift machine operation into a lower-price period. Experiment 3 exposed this on two synthetic larger workloads: at the *shortest feasible horizon*, four jobs achieved `F=15.5360` and five jobs `F=16.6684`, even though independent **unrestricted** CP-SAT optimization found `14.5808` and `15.7132` on the same underlying multiobjective problems. This gap was a **restriction of the candidate horizon**, not a defect in simulated annealing itself.

### 6.2 Exact-horizon anchor and objective consistency

To test a range of completion horizons, let `last(j)` be the last operation for job `j`. Add a quadratic **terminal-finish anchor**:

```text
E_anchor(H) = P_H * (1 - sum_j x[last(j), H - d_last(j)])^2.
```

A valid assignment has exactly one last operation ending at `H` (machine exclusivity forbids two simultaneous final operations on the shared last machine). Together with all scheduling constraints and the `C_max <= H` bounds, this sets **`C_max = H` exactly**. For each candidate horizon, the unconstrained binary energy includes one-hot, machine, precedence and anchor penalties plus `2W+0.02C_e`. When **all hard penalties vanish**, the full business score equals:

```text
F = H + E_feasible_variable_terms
  = H + 2*W + 0.02*C_e.
```

This is a crucial comparison rule: **do not compare raw QUBO energies across different H as if the horizon constant were included**. Penalty offsets and the absolute numerical scale must be handled consistently. The archived independent audit checked stored binary assignments, schedule costs and energy reconstruction.

### 6.3 Five exact-horizon models and 50 recorded annealing trials

| Jobs | Exact horizon | Bits | Couplings | Exact-H CP-SAT best F | Historical `neal` best F | Trial-best hits |
|---|---:|---:|---:|---:|---:|---:|
| 3 | 9 | 40 | 180 | 11.4456 | 11.4456 | 10 / 10 |
| 4 | 11 | 76 | 536 | 15.5360 | 15.5360 | 10 / 10 |
| 4 | 12 | 88 | 698 | 14.5808 | 14.5808 | 10 / 10 |
| 5 | 12 | 113 | 1,010 | 16.6684 | 16.6684 | 9 / 10 |
| 5 | 13 | 128 | 1,256 | 15.7132 | 15.7132 | 5 / 10 |

We ran **10 independent `neal` trials for each exact-horizon model**, or **50** trials in total. **44/50 trial-best schedules** matched their corresponding exact-H CP-SAT optimum, while all 50 decoded best schedules satisfied the recorded machine, precedence, outage and horizon requirements. Each historical trial comprised 240 annealing reads (12,000 combined sample reads); those reads are **not 12,000 independent experimental trials**. The hardest five-job H13 setting attained the best reference in only five of ten trials; we do not conceal that stochastic limitation.

### 6.4 The principal validated research finding

| Synthetic jobs | Shortest feasible H | Best F at shortest H | Better H | Best F at better H | Relative reduction |
|---|---:|---:|---:|---:|---:|
| 3 | 9 | 11.4456 | 9 | 11.4456 | 0.00% |
| 4 | 11 | 15.5360 | 12 | 14.5808 | **6.15%** |
| 5 | 12 | 16.6684 | 13 | 15.7132 | **5.73%** |

The 4- and 5-job schedules accept an **extra one hour of makespan** to reduce the weighted tardiness contribution sufficiently to lower the complete score. The better H12/H13 results match **unrestricted** historical CP-SAT `OPTIMAL` objectives for these *finite synthetic instances*. The improvements are **composite-score reductions**, not a reduction in completion time, measured energy-dollar savings, or quantum computational speedup. The intended contribution is a clearly verified **formulation and workflow improvement** in the treatment of business objectives.

## Stage VII — Scientific certification, reproducibility and presentation

### 7.1 What we check for each reported schedule

A returned binary sample is mapped back through the stored index/variable dictionary. The audit checks exactly one selected start per operation; matching durations and integer windows; strict T→F→S precedence; resource occupancy with no overlapping intervals on one machine; permitted milling intervals outside the synthetic `[3,5)` outage; and, for exact-horizon models, **actual** makespan equal to H. It recomputes weighted tardiness, hourly electricity cost and the composite objective, and reconciles that result to the archived binary energy after accounting for the objective constant and BQM offset.

The original baseline exported **43 hash-manifested evidence artifacts**; the adaptive-horizon independent review checked **29** artifact hashes and all **50** best-per-trial decoded schedules. The new live VeloxQ Gantt charts were checked against their actual exported schedules, and evidence archives retain separate timestamps. Cryptographic hashes support unchanged files; **hash integrity does not on its own prove the solver found a global optimum**.

### 7.2 Project materials and execution routes

| Goal | Repository asset |
|---|---|
| Official machine-readable submissions | `schedule_2x2.json`, `schedule_3x3.json` |
| Run original official and energy benchmarks | `notebooks/03_Original_Baselines_Energy_Reference.ipynb` |
| Inspect robustness and scaling experiments | `notebooks/04_Stage_V_Robustness_Scaling.ipynb` |
| Inspect adaptive exact-horizon construction | `notebooks/05_Stage_VI_Adaptive_Horizon.ipynb` |
| Live code-by-code demonstration with optional private VeloxQ credential | `notebooks/01_LIVE_Seven_Stage_Demo.ipynb` |
| Presentation with unchanged live code and archived outcomes, **without running cells** | `notebooks/02_PRESENT_Seven_Stage_Recorded_Results.ipynb` |
| Standalone secure VeloxQ integration | `notebooks/06_Standalone_VeloxQ_Secure_Benchmark.ipynb` |
| Source evidence and original coefficients | `evidence/` and `src/` |
| Historical and post-run audit records | `audits/` and `RESULTS_AND_VERIFICATION.md` |
| Non-executing offline checks | `python scripts/verify_submission.py` |
| AI assistance and authorship disclosure | `AI_USAGE.md` |

The **live** notebook may produce new, stochastic outcomes and needs the indicated Python dependencies and optional external credentials. The **presenter** notebook contains pre-recorded outcomes beside original code cells, and **must not be described as a fresh execution**. Its saved visuals are meant to make the hackathon live talk fast, legible and transparent about evidence provenance.

### 7.3 Threats to validity and scope limitations

1. **Problem scale:** at most 128 binary variables in the VeloxQ benchmark and five synthetic jobs; not a measured enterprise-scale deployment.
2. **Discretization and assumptions:** hour-sized slots, fixed machine paths, nonpreemptive durations, and an illustrative periodic price schedule. Real factories have setup times, uncertain arrivals, staffing, and dynamic constraints.
3. **Synthetic economics:** additional outage, due dates, power use, costs and job definitions are not provided real industrial observations. The objective's weights are chosen for the study, so its percentage improvements do not convert into factory revenue or operating-profit claims.
4. **Quantum terminology:** Qiskit Aer performed *simulated* gate-model circuit measurements; `neal` performed *classical* QUBO annealing; VeloxQ performed GPU-based *quantum-inspired* optimization. **No physical QPU executed this project.**
5. **Optimizer variability:** the original selected depth-three QAOA parameter search hit its iteration limit; stochastic annealing/VeloxQ optimum-hit rates vary with runs and penalty scales.
6. **Performance comparisons:** no strictly matched hardware resources, cost accounting, or normalized benchmark campaign exists to support claims of quantum advantage, quantum speedup, or superior solver scalability.
7. **Reference certification:** exact optimality is supported by archived CP-SAT `OPTIMAL` outcomes on precisely specified models; a no-solver hash checker verifies consistency but does **not** create a fresh proof.

### 7.4 Scope of originality and responsible attribution

The novel value of this submission is **application-level systems integration**: transforming actual job-shop rules into a QUBO, preserving official outputs, appending time-of-use pricing without new decision bits, measuring stochastic feasibility, diagnosing the fixed-minimum-horizon limitation, recovering certified better business scores with adaptive horizons, and benchmarking the same frozen QUBOs against an independent GPU-based quantum-inspired backend. These are **project contributions within established algorithm families**, not claims that the underlying solvers were invented by this team. Computational stages were planned and interpreted through the **Human Expert/PM → Agentic AI PC (ChatGPT) → execution tools** process, with human responsibility for the final submission.

**Final scientific message:** *The shortest feasible manufacturing schedule is not necessarily the best schedule under weighted customer deadlines and time-dependent energy costs. A carefully constrained, adaptively selected QUBO horizon can improve the complete business score, and independent classical reference solutions allow that claim to be verified on the tested instances.*

---

**For reproducibility and submission:** Begin with [`README.md`](README.md), read the dated [`DEVELOPMENT_LOG.md`](DEVELOPMENT_LOG.md), inspect original evidence under [`evidence/`](evidence/), run the source notebooks if new execution is desired, and see [`AI_USAGE.md`](AI_USAGE.md) for AI-assisted development disclosure. The official form submission and genuine demonstration-video link are separate required human actions.
