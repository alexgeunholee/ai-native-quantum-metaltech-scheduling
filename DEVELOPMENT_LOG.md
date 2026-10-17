# Development Log — AI-Native Quantum

**QPoland Quantum Hackathon 2026 | MetalTech Manufacturing Production Scheduling**  
**Team:** AI-Native Quantum · **Discord:** `@alexglee`  
**Repository:** https://github.com/alexgeunholee/ai-native-quantum-metaltech-scheduling  
**Research period documented:** 17 October 2026 (UTC)  
**Status:** Experimental work completed; submission video, form, and live jury presentation are separate human deliverables.

## Purpose, authorship, and evidence policy

This is a dated engineering and research diary, not a reconstructed claim of a single uninterrupted run. It explains **what was attempted, what worked, what failed or exposed a limitation, why the method changed, and what evidence supports each result**. Times refer to captured export or execution timestamps when available. Multiple runs of similar models are deliberately kept separate. The Human Expert / Project Manager (PM) set objectives, approved the testing direction, ran the Colab workflows, evaluated actual outputs, and handled team registration and publication. ChatGPT acted as an **Agentic AI Project Coordinator (PC)** for mathematical formulation, experimental planning, code generation and debugging, analysis, and documentation. Google Colab and the indicated software backends performed actual calculations. Use of AI is also disclosed in [`AI_USAGE.md`](AI_USAGE.md).

The official challenge provides **two scheduling instances**. Additional machine outages, customer due dates, electricity prices, and the fourth and fifth jobs in our research were **designed synthetic test scenarios**, not supplied factory observations. The official schedule deliverables remain [`schedule_2x2.json`](schedule_2x2.json) and [`schedule_3x3.json`](schedule_3x3.json).

## Research development at a glance

| Stage | Question and main development decision | Recorded outcome |
|---|---|---|
| I. Original problem | How can the official job-shop instances be expressed and evaluated correctly? | Defined compulsory operations, precedence, machine capacities, and makespan reference |
| II. QUBO formulation | How can hard manufacturing requirements become an energy function? | One-hot, machine-conflict, precedence, and time-window model; 3×3 reduced from 72 to 39 start bits |
| III. Baseline | Can a genuine simulator-executed QAOA circuit and a classical QUBO solver reach official optima? | 4 h and 8 h, independently referenced by CP-SAT |
| IV. Industrial extension | What changes when downtime, due dates, priorities, and electricity cost matter? | Feasible 9-hour scenario; energy price $23.56 to $22.28 in a controlled synthetic comparison |
| V. Robustness and backends | How do penalties, size, depth, and backend affect feasibility and solution quality? | 45 historical `neal` trials; QAOA depth tests; two real VeloxQ GPU quantum-inspired campaigns |
| VI. Adaptive horizon | Does minimizing makespan always minimize the business objective? | No: composite-score reductions 6.15% (4 jobs) and 5.73% (5 jobs) |
| VII. Qualification and handoff | Can reported results be independently checked and presented without rerunning? | Saved model/evidence manifests, decoded schedules, audits, public MIT repository, live and presenter notebooks |

---

## 17 October 2026 — Stages I–III: Problem selection, modeling, and official baselines

### Decision 1 — Keep the mandatory challenge instances distinct from the extension

We interpreted the official MetalTech task as a **nonpreemptive job-shop scheduling problem**. Each operation has a fixed processing duration and an assigned machine. A job cannot start its next operation until its previous operation finishes; a machine cannot process two jobs simultaneously. The mandatory objective is to minimize the **makespan**, the latest operation completion time. The small two-job/two-machine instance follows T (lathe) → F (milling), and the three-job/three-machine instance follows T → F → S (welding).

**Why this mattered:** Our later energy-aware and customer-priority experiments add conditions not present in the original task. We chose to preserve the official answers separately so that extensions could not inadvertently change the required output format or obscure which results the organizers provided.

### Decision 2 — Build a time-indexed QUBO, then preserve a classical exact reference

We defined a binary variable for each allowed operation start time and applied quadratic penalties to forbid missing or multiple starts, overlapping machine occupancy, and incorrect job sequence. Earliest- and latest-start bounds removed start times that could never lead to a feasible fixed-horizon schedule. For the official 3×3 instance at an 8-hour horizon, the candidate count decreased from **72 naïve start variables to 39 allowed variables** (45.83% reduction), with **181 quadratic interactions**. The 2×2, four-hour formulation contained **8 variables and 12 interactions**.

**Why this mattered:** Time-window pruning changes the computational representation without relaxing the actual scheduling constraints. We kept original coefficient models so the method could be inspected independently rather than relying on screenshots of a solver answer.

### 15:26 UTC evidence export — First complete baseline experiment

The initial integrated Colab execution exported `evidence/original_baselines/FINAL_RESULTS_FOR_CHATGPT.txt` (generated **15:26:30 UTC**), 43 supporting evidence artifacts, and their manifest. We ran an **actual eight-qubit QAOA circuit on Qiskit Aer**, not on physical quantum hardware. From 4,096 measurement shots, **142 samples** represented an optimal four-hour schedule (3.47%). The selected depth-three COBYLA parameter-search run hit its iteration limit; sampling an optimal bitstring **does not establish convergence of that variational optimization**.

For the official 3×3 case, a **classical `neal` simulated-annealing solver** processed the 39-bit QUBO with no warm start, reported best penalty energy **0**, and decoded to a valid **8-hour makespan** schedule. Separate OR-Tools CP-SAT executions reported `OPTIMAL` at **4 hours** and **8 hours**, respectively. The CP-SAT results provide reference optima for these particular models, not an assertion of quantum advantage.

**Evidence:** `evidence/original_baselines/quantum/`, `evidence/original_baselines/qubos/`, `evidence/original_baselines/verification/`, `evidence/original_baselines/FINAL_RESULTS_FOR_CHATGPT.txt`, and the two root schedule files.

## 17 October 2026 — Stage IV: Synthetic manufacturing conditions and business objectives

### Problem extension and assumptions

After the mandatory baselines, we introduced a **synthetic milling maintenance outage `[3,5)`**, due dates **Z1=7, Z2=5, Z3=10**, and customer-priority weights **1, 3, 1**. These choices test whether a schedule that is shortest is also useful from a business perspective. Tardiness incurs a cost only when a job finishes after its specified deadline. The multiobjective measure adds makespan and twice the weighted tardiness.

Next, we assigned illustrative machine power consumption **T=8 kW, F=12 kW, S=6 kW** and a time-of-use tariff of **$0.27/kWh during hours 2–5** and **$0.11/kWh otherwise**. The complete numerical score is `F = makespan + 2 × weighted tardiness + 0.02 × electricity cost in USD`. The coefficients are project-designed weights, not a conversion to actual factory profit.

### Modeling decision — Electricity cost as a linear QUBO term

For a known machine duration, power draw, and hourly tariff, choosing a start time already determines its electricity charge. We therefore added that charge as a coefficient of the corresponding **existing start-time bit**, rather than introducing a new binary variable for each billing hour. The three-job, exact-nine-hour model remained **40 bits and 180 interactions**.

The initial feasible synthetic schedule had a weighted tardiness of 1 and a nine-hour makespan. The energy-aware schedule retained the same makespan and weighted tardiness but reduced computed electricity spending from **$23.56 to $22.28**, a **$1.28 / 5.43%** difference between these **two synthetic schedules**. Its full score was **11.4456**, matching the recorded CP-SAT `OPTIMAL` result. We do **not** describe this as real plant-dollar savings or a quantum improvement.

**Evidence:** `evidence/original_baselines/extension/`, `evidence/original_baselines/reports/`, `evidence/original_baselines/verification/`.

## 17 October 2026, 16:08 UTC — Stage V: Penalty sensitivity, robustness, and scaling

### Question — Do stronger constraint penalties always produce better answers?

We expanded the synthetic scheduling workload to **3, 4, and 5 jobs**, at the certified minimum-makespan horizons **9, 11, and 12 hours**. The corresponding fixed-horizon QUBOs had **40 / 76 / 113 binary variables** and **180 / 536 / 1,010 interactions**. We tested three penalty strengths **5, 25, 100**, with **five independent seed configurations per size and penalty**, for **45 classical simulated-annealing trials**.

All 45 selected trial-best schedules were feasible under the checked constraints; however, feasibility among the underlying samples varied appreciably. The historical mean feasible-sample rates for penalties (5, 25, 100) were **65.17%, 82.83%, 73.83%** at 3 jobs; **16.40%, 39.07%, 60.53%** at 4 jobs; and **5.06%, 29.18%, 49.29%** at 5 jobs. At five jobs, the fixed-horizon optimum was reached in **2/5, 5/5, 3/5 seeds** for the respective penalties. A larger penalty may increase the proportion of valid samples but does not necessarily improve the chance of the best business solution.

Separate genuine Aer QAOA depth tests used **p=1, 2, 3**, with two seeds each and **2,048 shots per run**. The historical best depth-three optimal-bitstring frequency was approximately **8.45%**, but both depth-three COBYLA runs reported unsuccessful parameter convergence. Therefore we report **observed sampling frequency**, not a validated monotonic advantage from increasing QAOA depth.

### Discovery — Fixed shortest makespan obscured better overall objectives

CP-SAT revealed that the 4-job, minimum-horizon **H=11** model's best business score was **15.5360**, whereas the unrestricted synthetic-business reference was **14.5808**. For five jobs, **H=12** yielded **16.6684**, above the unrestricted reference **15.7132**. These were **not solver errors**: the feasible sets had been restricted to the shortest permitted makespans, which can increase deadline penalties. We identified this as a **model-scope limitation** requiring a horizon-search correction, not as a basis for claiming the solver failed to optimize its stated model.

**Evidence:** `evidence/robustness_scaling/FINAL_RESULTS_FOR_CHATGPT.txt`, `evidence/robustness_scaling/full_results.json`, `audits/experiment3_independent_audit.md`.

## 17 October 2026, 16:20 UTC — Stage VI: Adaptive exact-horizon correction

### Corrective design — Test multiple completion horizons

To permit comparison of schedules that finish at different times, we introduced an **exact-makespan finishing anchor** into the existing QUBO. Its penalty is zero only when at least one last operation finishes at the trial horizon `H`, while all the usual one-hot, precedence, and capacity requirements remain active. We evaluated five exact-horizon settings: 3 jobs at H=9, 4 jobs at H=11 and 12, and 5 jobs at H=12 and 13.

**Why this mattered:** The feasible energy of a fixed-`H` QUBO represents the **variable business terms**, not necessarily the complete `F` score. We added the horizon back when comparing separate models, rather than directly comparing raw QUBO energies from different horizons and penalties.

### Actual results and independent checks

We performed **50 classical `neal` trials** across the five horizon cases. In **44/50 trials**, the best sample achieved the corresponding exact-horizon CP-SAT optimum. All 50 decoded best schedules passed the recorded feasibility checks. The result table captures both successes and incomplete optimization runs:

| Jobs | Exact horizon H | Bits / interactions | Reference score | `neal` best score | Exact-H optimum hits |
|---|---:|---:|---:|---:|---:|
| 3 | 9 | 40 / 180 | 11.4456 | 11.4456 | 10 / 10 |
| 4 | 11 | 76 / 536 | 15.5360 | 15.5360 | 10 / 10 |
| 4 | 12 | 88 / 698 | 14.5808 | 14.5808 | 10 / 10 |
| 5 | 12 | 113 / 1,010 | 16.6684 | 16.6684 | 9 / 10 |
| 5 | 13 | 128 / 1,256 | 15.7132 | 15.7132 | 5 / 10 |

The adaptive approach improved the **composite synthetic-business score** by **6.15%** (4 jobs, H11→H12) and **5.73%** (5 jobs, H12→H13), while each schedule's makespan increased by one hour. The best improved scores matched the archived **unrestricted** CP-SAT `OPTIMAL` references for these instances. These percentages **do not mean makespan improved or that comparable dollar savings were realized**.

The audit recomputed feasibility, timing, cost, weighted tardiness, QUBO energies, optimum-hit totals, and checked **29 evidence hashes**. This later evidence audit is separate from the original solver execution.

**Evidence:** `evidence/adaptive_horizon/FINAL_RESULTS_FOR_CHATGPT.txt`, `evidence/adaptive_horizon/models/`, `evidence/adaptive_horizon/runs/`, `audits/experiment4_independent_audit.md`.

## 17 October 2026, approximately 18:24–18:26 UTC — VeloxQ onboarding and debugging

### New experimental opportunity

After completing the core work, we explored **VeloxQ**, a remotely hosted **GPU-based quantum-inspired solver**, as a fourth computational method. It is **not** a physical quantum-processing unit. The team obtained VeloxQ API access and planned to reuse four **frozen binary QUBOs**: official 39-bit, synthetic energy-aware 40-bit, adaptive four-job 88-bit, and adaptive five-job 128-bit. This avoided claiming a comparison based on differently reformulated optimization problems.

### Errors encountered and repairs

The first Colab model-loader used a model-order-dependent assertion. Although the correct sizes appeared in the console, the assertion compared them to a fixed list in the wrong dictionary order and failed. We replaced it with **per-model-ID checks** covering variable count, quadratic interactions, and offset while preserving the model fingerprint. A second problem was that the results ZIP was created but not automatically downloaded when `RUN_REMOTE=False`; we corrected the export cell so the Colab download occurs in both preflight and remote modes.

A preflight ZIP with `RUN_REMOTE=False` demonstrated successful export but **contained no VeloxQ execution**. We explicitly distinguished that preflight from later actual solver campaigns. We also adopted masked API-key input or Colab Secrets; the API credential is never embedded in notebooks or the public repository. Because an earlier key was disclosed in a conversation, rotating it was recommended.

**Engineering lesson:** Correct QUBO data, robust notebook control flow, solver access, credential handling, and trustworthy evidence export are all essential to a reproducible optimization demonstration.

## 17 October 2026, approximately 18:41 UTC — First real VeloxQ campaign

Four remotely submitted VeloxQ jobs completed using **256 repetitions and 1,500 steps per model**. Three best feasible schedules matched their archived CP-SAT references; the 128-bit five-job case produced a feasible H=13 schedule with score **15.7388**, compared with optimal reference **15.7132**, a gap of about **0.163%**. The first campaign proved the integration was operational while also showing that the strongest solver sample need not always attain the optimum.

We retained the actual QUBO sizes, result mappings, decoded schedules, feasibility counts, timings, Gantt charts, and checksum manifest. We did not substitute archived or fabricated answers for remote results.

**Evidence:** `evidence/veloxq_initial_campaign/` and `RESULTS_AND_VERIFICATION.md`.

## 17 October 2026, 20:23 UTC — Fresh seven-stage live Colab demonstration

### Research demonstration choice

The Human PM requested a notebook where each experimental step could be run in front of an audience, independently of the **read-only, slide-style Colab presentation**. We retained original executable cells in the live version and embedded previously observed outcomes in the presentation version, keeping fresh calculations distinct from historical evidence. Live QAOA sampled with previously fitted angles; it did **not** repeat the full parameter optimization.

### Actual new outputs

The new 2×2 Qiskit Aer sample contained **141 optimal schedules in 4,096 shots** (3.44%), versus **142/4,096** in the original baseline. The official classical QUBO again returned an 8-hour schedule, and the live synthetic energy/penalty and adaptive-horizon measurements agreed with their archived reference outcomes under the tested cases.

Most importantly, **all four new VeloxQ remote jobs matched the archived CP-SAT best objectives**, including the previously near-optimal five-job benchmark. With the same reported **256 repetitions / 1,500 steps** per benchmark, the live feasible-sample counts were:

| Frozen QUBO | Bits / couplings | CP-SAT reference | New VeloxQ best | Feasible samples |
|---|---:|---:|---:|---:|
| Official 3 jobs, H=8 | 39 / 181 | 8 h | 8 h | 229 / 256 |
| Energy-aware 3 jobs, H=9 | 40 / 180 | 11.4456 | 11.4456 | 211 / 256 |
| Adaptive 4 jobs, H=12 | 88 / 698 | 14.5808 | 14.5808 | 94 / 256 |
| Adaptive 5 jobs, H=13 | 128 / 1,256 | 15.7132 | 15.7132 | 57 / 256 |

The 3/4 match in the first campaign and 4/4 match in the second are **both disclosed**, reflecting stochastic variability instead of a guarantee of repeated optimality. Feasible fractions cannot be interpreted as a controlled scaling law because the instances and constraints also change. The review of submitted outputs recomputed timing, precedence, machine conflicts, and maintenance conditions; it was a post-run **consistency check**, not another VeloxQ or CP-SAT solver run.

**Evidence:** `evidence/live_demo/LIVE_DEMO_RESULTS.json`, `evidence/live_demo/fresh_penalty_sweep.csv`, `evidence/live_demo/fresh_adaptive_horizons.csv`, archived `gantt_*.png`, and `audits/live_demo_independent_review.md`.

## 17 October 2026, 22:00 UTC — Stage VII: Integrated documentation and public repository

We consolidated the scientific workflow into **seven research stages**, maintained both an **executable live notebook** and a **non-executing presenter notebook with original code and archived outputs**, added explicit AI-use disclosure and license files, and prepared machine-readable schedules and evidence for external review.

A public GitHub repository was published under the team account at the URL above. The first published commit is **`6ab9c92`**, message **“Initial QPoland Hackathon submission”**. At publication the root README, MIT LICENSE, Development Log, Project Design, schedule JSON files, notebooks, evidence and auditor notes were accessible. Publishing the repository does **not** constitute submitting the organizer's Google Form.

### Scientific claims we deliberately do not make

- **No physical QPU was used.** Qiskit Aer is a quantum-circuit simulator; `neal` is classical simulated annealing; VeloxQ is GPU-based quantum-inspired optimization.
- **No quantum advantage, industrial-scale speedup, or guaranteed stochastic convergence is established.** Solver and API timings are not normalized hardware benchmarks.
- **No real manufacturer cost savings are proven.** Extra deadlines, outages, energy tariff, electricity consumption and 4–5-job workloads were synthetic.
- **QAOA parameter convergence was not proved** for the original selected p=3 run even though optimal configurations were sampled.
- **A stored CP-SAT `OPTIMAL` report** is evidence of an earlier reference solve; the lightweight offline manifest verifier does not itself rerun CP-SAT.

### Remaining human-controlled submission actions

The team must verify this diary's chronology and authorship, confirm Discord team lock-in, record and upload an **actual video of no more than five minutes showing software running**, add the real video URL to `README.md`, submit the official form before the organizer deadline, and be prepared for the **three-minute live presentation and approximately two-minute jury questions**. None of these future actions is marked complete merely because this log has been published.

### Traceability / starting points

See [`PROJECT_DESIGN.md`](PROJECT_DESIGN.md) for the mathematical model, [`RESULTS_AND_VERIFICATION.md`](RESULTS_AND_VERIFICATION.md) for numeric results, [`AI_USAGE.md`](AI_USAGE.md) for human/AI roles, the source notebooks in [`notebooks/`](notebooks/), and the archived execution outputs under [`evidence/`](evidence/). `scripts/verify_submission.py` rechecks saved schedules and evidence but **does not reproduce the optimizer runs**.
