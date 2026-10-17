# Development Log — QPoland 2026, Team AI-Native Quantum

This record is based on dated exported execution evidence and the documented project decisions. It is prepared for the Human Project Manager's factual review before final public submission. Unperformed activities (recording video, submitting a form) are not presented as completed.

## 2026-10-17 — Project selection and first method decisions
- Reviewed the official MetalTech job-shop scheduling challenge and its two compulsory baseline instances. Established a Human Expert / PM → ChatGPT Agentic AI PC → Google Colab tools working structure, with the PM approving scope and results.
- Adopted time-indexed start bits and penalties for one-hot selection, machine exclusivity and process-order precedence. Chose Qiskit Aer QAOA for the 2×2 quantum-algorithm requirement, classical `neal` BQM for the 3×3 QUBO requirement and OR-Tools CP-SAT for independent optimum references.
- Rejected any unsupported physical-QPU or quantum-advantage representation. Decided to record model coefficients, seed, code and source-specific execution evidence.

## 2026-10-17, 15:24–15:27 UTC — Original baseline and synthetic industrial extension
- Ran the first Google Colab integrated notebook, generating 43 evidence files and a SHA-256 manifest. Baseline A produced a valid 4-hour schedule sampled 142/4096 times on Qiskit Aer; the selected depth-three COBYLA trial reached its iteration cap, so convergence was not claimed. Baseline B produced a valid 8-hour, zero-penalty QUBO solution on `neal` with no solver warm-start.
- Introduced synthetic milling downtime `[3,5)`, three customer due dates and priority weights, then tariff-aware electricity charge. Using deterministic time-of-use charges as **linear QUBO coefficients** retained 40 binary variables and 180 couplings. For the observed comparable schedules, electricity cost changed from $23.56 to $22.28 without worsening makespan/tardiness.
- Independent post-execution checks recomputed feasibility, cost, penalties and the 43 hash entries. These checks did not rerun CP-SAT.

## 2026-10-17, 16:07 UTC — Robustness and scaling study
- Conducted 45 `neal` sensitivity trials across penalties 5, 25, 100; five seeds per penalty/job-size configuration across three synthetic job sizes (3–5), plus QAOA depth benchmarks.
- Found that fixed *minimum makespan* horizons can be suboptimal for the whole multiobjective business score. For four jobs H=11 gave 15.5360 and for five jobs H=12 gave 16.6684, above unrestricted CP-SAT reference scores.

## 2026-10-17, 16:19–16:20 UTC — Adaptive-horizon correction
- Added exact terminal-operation finishing-time anchoring to the QUBO and compared multiple horizon values. Executed 50 historical simulated-annealing trials; 44 trial best-schedules attained the exact-H CP-SAT objective and all selected schedules met the checked hard constraints.
- Recovered global synthetic-business-objective references: 14.5808 for 4 jobs at H=12 and 15.7132 for 5 jobs at H=13. Recorded **6.15%** and **5.73%** score improvements relative to their respective shorter fixed-horizon cases.

## 2026-10-17, 18:24–18:26 UTC — VeloxQ integration debugging
- Team AI-Native Quantum obtained VeloxQ SDK access and designed a supplementary quantum-inspired solver benchmark on four frozen QUBOs. The first export was a *no-remote-run* preflight. Corrected a model-order-dependent assertion and an export/download condition that skipped ZIP downloads when remote execution was disabled.
- Adopted hidden API credential input and never included an API key in the versioned notebooks. An earlier credential had been accidentally shared in chat; replacement/rotation was recommended. **No credential is committed to this repository.**

## 2026-10-17, 18:41 UTC — First actual VeloxQ GPU remote campaign
- Four remote jobs succeeded at 256 repetitions and 1500 steps; the 39-, 40- and 88-bit models matched exact references. The 128-bit model returned a feasible 13-hour schedule with composite objective 15.7388, **0.163% above** the CP-SAT reference 15.7132.
- Archived raw model/coefficient mapping, returned schedule/energy summaries, feasible-sample counts, four Gantt charts and SHA-256 manifest.

## 2026-10-17, 20:23 UTC — Fresh seven-stage live Colab demonstration
- Conducted a cell-by-cell Colab live demonstration. Fresh Qiskit Aer sampling returned **141/4096** optimal 2×2 shots with historically fitted p=3 parameters, distinct from the original 142/4096. Classical `neal` baselines, penalty sensitivity and adaptive horizons were also run fresh.
- Four **new** VeloxQ GPU remote jobs returned feasible best solutions matching all four prior CP-SAT objectives, including the 128-bit, 1256-coupling five-job case (15.7132). Feasible-sample proportions: 229/256, 211/256, 94/256, 57/256. The first 3/4-match and second 4/4-match campaigns are both preserved to disclose stochastic variability.
- The live archive was independently reviewed for recorded schedule feasibility, machine overlaps, maintenance and precedence. The review was a post-run consistency audit, not another remote execution.

## 2026-10-17 — Consolidation and packaging
- Consolidated the scientific narrative into seven stages, with a live executable Colab notebook and a slide-style notebook retaining original code cells and recorded outputs. Prepared the required official root schedule files, MIT license, README with AI-use disclosure, Project Design, Development Log, machine-readable archives and submission checklist.
- The Human PM still must verify authorship and dates, publish the repository, provide a **real** ≤5-minute program-run video URL, submit the organizer Google Form and attend the scheduled live presentation. No video or GitHub publication is assumed by this record.
