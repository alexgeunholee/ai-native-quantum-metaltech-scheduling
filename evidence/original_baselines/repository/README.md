# QPoland 2026 — ERP Scheduling, AI + Quantum

Open `ERP_Quantum_Hackathon_Option_A_Upgraded_Energy_Colab.ipynb` in Google Colab and select **Runtime → Run all** (CPU runtime). The notebook installs all dependencies, includes official problem inputs, performs the QAOA/Aer simulator run, runs binary QUBO optimization using neal, certifies exact references via OR-Tools CP-SAT, executes both a proposed downtime/deadline Stage2 and an additional synthetic time-of-use energy Stage2, and downloads `ERP_Quantum_Hackathon_Evidence.zip`.

## Required exported files
`schedules/schedule_2x2.json` and `schedules/schedule_3x3.json` exist only when actual sampler-generated schedules pass validation. Copy them to repository root as `schedule_2x2.json` and `schedule_3x3.json` for official submission. The notebook archive includes `inputs/`, `qubos/`, `quantum/`, `verification/`, `figures/`, `reports/`, and Stage2 outputs. `FINAL_RESULTS_FOR_CHATGPT.txt` contains compact numbers for writing final materials.

## Three-party co-pilot / AI usage
Human Expert/Project Manager sets research objectives, approves experiments, reviews and accepts results, controls public submissions; ChatGPT acting as Agentic AI Project Coordinator assisted with data interpretation, mathematical formulation, QUBO design, Python/Qiskit code generation, automated checks, scientific reporting, and presentation drafts; Google Colab with Qiskit Aer and classical solvers performs actual computations. The team independently examines evidence and assumes responsibility for claims. Do not claim physical QPU/VeloxQ usage unless independently executed later and supported by logs.

## Methods and limitations
A is real Qiskit Aer QAOA circuit measurement, parameter-fitted using noiseless state-vector + SciPy. B and extension use neal, a **classical** QUBO sampler, potentially with an explicitly marked CP-SAT warm-start. CP-SAT is used for exact verification, not disguised as a quantum optimizer. Stage2 outage/deadline and electricity parameters are separately labeled synthetic research extensions; there is NO implemented peak-energy hard cap, machine-flexibility model, operator pool, or sequence-dependent setup constraint in this notebook.

## Needed before final submission
(1) Add actual notebook file and verified JSON files to the public MIT-licensed repo; (2) audit all actual results; (3) upload and link recorded demonstration video; (4) submit the organizer's Google Form; (5) prepare for 3-minute live presentation and Q&A. The notebook cannot execute these Human PM actions.
