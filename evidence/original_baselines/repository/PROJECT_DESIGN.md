# Project Design — ERP Quantum Production Scheduling (2026)

## Decision problem
Machine order T→F→S, known integer processing times, one operation start per job-machine, no machine overlaps, minimize makespan. Official Instances A (2×2) and B (3×3) are supplied in inputs/.

## Time-indexed QUBO
Binary x[j,m,t] selects operation start t. Fixed-horizon energy: P * sum_(j,m) (1-sum_t x[j,m,t])^2 + P * sum_(conflicting machine starts) x_a*x_b + P * sum_(invalid job-order starts) x_a*x_b. Horizons H=4 (A) and H=8 (B). Candidate time windows calculated by prefix/suffix job durations. In Stage 2, add exact outage start pruning and linear weighted tardiness on final-operation x variables. In the synthetic energy extension, per-operation electricity cost is another linear one-hot start coefficient; no additional start binary variables or quadratic interactions are needed at fixed H=9.

Penalty A=1, B=5, Stage2=100. Number of variables/unique quadratic interactions: A 8/12; B 39/181; extension 40/180; energy extension 40/180.

Baseline QUBOs search for feasibility at chosen horizons. A global makespan optimum is proven independently with OR-Tools CP-SAT, not by a failed or successful heuristic sample alone.

## Solvers actually used
Stage A: QAOA state-vector expected-energy optimization (Qiskit Statevector + SciPy COBYLA); final circuit **executed on Qiskit Aer** with actual measurement shots. Stage B and both extensions: neal **classical simulated annealing** on a binary quadratic model. Classical exact reference: OR-Tools CP-SAT. No physical QPU or VeloxQ executed.

## Proposed Stage 2
Outage on milling interval [3,5); deadlines Z1=7,Z2=5,Z3=10; priority weights Z1=1,Z2=3,Z3=1; F=makespan+2*weighted tardiness. This is investigator-designed, not official input. Fixed-horizon H=9 QUBO optimizes weighted tardiness while the *complete* F objective is separately optimized and certified using CP-SAT. Synthetic energy extension: power T/F/S=8/12/6kW, peak hours [2,6), off-peak/peak 11/27 cents per kWh; weighted energy coefficient 0.02 USD. Each selected start variable carries exact tariff charge as a linear coefficient, preserving 40 variables. CP-SAT independently optimizes full F including makespan, weighted tardiness and electricity cost.

## Results and limitations
A: Aer QAOA status PASS; exact reference 4h; optimal shot frequency 0.034668.
B: QUBO status PASS; exact reference 8h; warm-start used=False.
Stage2: QUBO status PASS; CP-SAT exact F=11; warm-start used=False.
Energy Stage2: classical QUBO status PASS; CP-SAT exact full F=11.445600; QUBO matched exact=True; warm-start=False.
A simulator is not quantum-hardware execution, and a classical BQM optimizer is not quantum advantage. Solver evidence is in outputs, including any recorded failure.
