# Project Design — Seven-stage QUBO / QAOA / Quantum-Inspired Manufacturing Scheduling

## I. Original optimization problem

Official MetalTech scheduling: jobs have fixed operations on T (lathe), F (milling), and S (welding). A 2×2 instance has Z1 T2,F1 and Z2 T1,F2. The 3×3 instance has Z1 T2,F1,S2; Z2 T1,F2,S1; Z3 T2,F2,S1. Every operation executes exactly once and nonpreemptively, operations in a job preserve machine order, and machines handle no more than one operation at a time. Baseline objective is minimum `C_max` (the finishing time of the last operation). The official data are in `evidence/original_baselines/inputs/`.

## II. Time-indexed binary/QUBO model

Let `x_{jmt}∈{0,1}` denote operation `(j,m)` starting at integer hour `t` within planning horizon `H`. The earliest candidate start is the sum of that job's preceding durations; its latest candidate start is `H - remaining_job_duration`. This pruning is admissible for the fixed-horizon feasibility case. Official 3×3 at H=8 shrinks 72 naïve candidates to **39** start variables, with **181** pair interactions; official 2×2 at H=4 uses **8** variables and **12** interactions.

Define the binary-quadratic penalty model

```
E(x) = P1 Σ_o (1 − Σ_{t∈allowed(o)} x_{ot})²
     + P2 Σ_{(a,b) with overlapping same-machine time slots} x_a x_b
     + P3 Σ_{(a,b) with violated job precedence} x_a x_b
     + Σ_{o,t} cost_{ot} x_{ot}.
```

For baseline feasibility, all `cost_{ot}=0`, with positive penalties. The first term imposes exactly one start per operation; the second excludes simultaneous machine tasks; the third forbids starts that break job precedence. Penalty expansion creates the linear and quadratic coefficients included in the archived models. Zero energy certifies feasibility *at the fixed horizon*, not globally minimal makespan; **an independent CP-SAT search** is needed to certify minimum H. Typical recorded penalties: official A `P=1`, official B `P=5`; synthetic extensions explore `P=5,25,100` with appropriate objective scaling. Overly small `P` can allow constraint violations; overly large `P` can distort effective search priorities and feasibility/quality behavior.

## III. Baseline quantum and classical solvers

The 8-bit A QUBO is mapped to a QAOA cost operator with X-mixer. Historical statevector-assisted fitting tested depths p=1,2,3 using SciPy COBYLA multi-start search. A selected p=3 circuit then received 4,096 actual **Qiskit Aer simulator** measurement shots, yielding **142** sampled optimal bitstrings (3.47%). A separate live-demo Aer run using previously fitted angles observed **141/4096** optimal shots (3.44%); the demo is genuine fresh sampling but *not a fresh full variational-parameter optimization*. The historical p=3 COBYLA trial hit its iteration cap (`optimizer_success=false`). There was **no physical QPU**.

The 39-bit B QUBO is sampled classically with D-Wave Ocean's `neal` simulated annealing; decoded, zero-energy, 8-hour schedules were produced. Independent OR-Tools CP-SAT runs reported `OPTIMAL` 4h (A) and 8h (B) and supplied exact reference horizons.

## IV. Synthetic industrial extension

For the 3×3 job timings, impose milling downtime `[3,5)` by removing any F-start whose run would overlap it. Set due times Z1=7, Z2=5, Z3=10 and tardiness weights Z1=1, Z2=3, Z3=1. Job weighted tardiness is `W = Σ_j w_j max(0, completion_j - due_j)`. Add optional synthetic electricity consumption T 8kW, F 12kW, S 6kW with peak rate `$0.27/kWh` during hours `[2,6)` and `$0.11/kWh` outside this window. Let `C_e` be the deterministic USD electricity charge from operation start times. The full evaluated business objective is:

```
F = C_max + 2 W + 0.02 C_e.
```

At exact H=9, the corresponding QUBO minimizes the variable part `2 W + 0.02 C_e` plus constraint penalties; Cmax=H is constant on feasible anchored schedules. Tariff energy is a known charge for each potential start, so it is a **linear coefficient** (`Σ cost_{ot} x_{ot}`), increasing neither binary variable count nor quadratic interaction count for this stage: **40 bits / 180 couplings**. The archived `neal` example had `C_max=9`, `W=1`, electricity `$22.28`, `F=11.4456`. An earlier outage/tardiness schedule cost `$23.56` under the same synthetic tariff, meaning a **5.43% reduction in observed electricity cost between these particular schedules**, not a universal cost saving or quantum advantage.

## V. Robustness, scaling, and VeloxQ

A controlled synthetic sensitivity study considered penalties `P∈{5,25,100}`, independent seeds, and 3/4/5 job cases. For fixed *minimum makespan* horizons, variable counts were 40/76/113 and pair interactions 180/536/1010. Constraint feasibility frequency changes with both model size and penalty selection. The historical experiments compare Qiskit Aer depth p=1,2,3 and classical QUBO optimization, with original runs and selected fresh live-demo repetitions preserved separately.

The separate **VeloxQ GPU-based quantum-inspired** API uses the same frozen binary QUBO models through `dimod.BinaryQuadraticModel` and `VeloxQSolver.sample(bqm)`, at `num_rep=256`, `num_steps=1500`. The first real remote campaign returned 3/4 best-objective matches and one feasible five-job result 0.163% above the reference. The later live campaign returned 4/4 matches: 39bits (8h,229/256 feasible), 40bits (11.4456,211/256), 88bits (14.5808,94/256), 128bits (15.7132,57/256). Feasibility requires independent decoding and machine/precedence/outage checks: raw lowest QUBO energy alone is not a feasible-schedule certificate. The API token is supplied privately when rerunning and is never committed.

## VI. Adaptive exact-horizon search

The minimum makespan can conflict with tardiness and tariff expenditure. To compare feasible schedules at multiple exact horizon values, use a terminal anchoring term (with compatible coefficient scales)

```
P (1 − Σ_j x_{j,last_operation,H − duration(j,last_operation)})².
```

It requires at least one final operation to finish at exactly H; each other operation still satisfies feasibility and the upper horizon bound. Across 4 jobs, fixed minimum H=11 gave F=15.5360, while H=12 gave F=14.5808 (**6.15% lower**). Across 5 jobs, H=12 gave F=16.6684 while H=13 gave F=15.7132 (**5.73% lower**). These latter results match previously recorded *unrestricted* CP-SAT optimal objectives on the same synthetic instances; 50 recorded simulated-annealing trials yielded 44 best-per-trial exact-H optimum matches, with stochastic variation. The improvement is **in the full composite objective**, not simply makespan or a measured manufacturing-dollar saving.

## VII. Reproducibility, simplifications, qualification

Original input and schedule JSONs are at the repository root / `evidence/original_baselines/`; full coefficient models and metadata are archived, with 43 checksum-manifested original baseline evidence artifacts and separate sensitivity, adaptive, and VeloxQ campaigns. `scripts/verify_submission.py` checks file hashes, official schedule feasibility, original zero-penalty QUBO energies and recorded live statuses without running solvers. Historical CP-SAT claims rely on captured `OPTIMAL` result reports; this lightweight verifier is not itself a new solver proof.

Limitations: synthetic power, deadlines and larger job sets; fixed machine order and hour granularity; no stochastic machine-breakdown/large-enterprise dataset; no physical QPU; limited scaling to 128 binary variables for VeloxQ; no proven quantum/classical speed advantage. Work consists of integrating and validating established formulations and solver backends, not inventing QUBO or QAOA.
