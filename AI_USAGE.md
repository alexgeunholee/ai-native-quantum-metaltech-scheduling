# AI Usage Disclosure — Explicitly required by the hackathon rules

The team used OpenAI ChatGPT as an **Agentic AI Project Coordinator (PC)** to interpret the hackathon requirements, draft and revise QUBO/QAOA mathematical formulations, generate Python/Colab code, troubleshoot integration failures, draft experimental protocols and documentation, and assess exported numerical evidence. This use of AI was disclosed; AI did not physically execute quantum hardware or independently certify industrial claims.

The **Human Expert / Project Manager (PM)** reviewed materials, decided the experiment stages and solver choices, requested reruns and corrections, supplied actual Colab outcome ZIPs, and is responsible for explaining the full solution, checking correctness, and publishing the final submission. All decisions and actual outcomes remain subject to the human team's acceptance.

**Execution tools are separate from the three human/AI coordination roles:** Google Colab ran Qiskit Aer quantum *simulations*, classical `neal` simulated annealing and OR-Tools CP-SAT; externally hosted VeloxQ ran two actual GPU-based **quantum-inspired** sampler campaigns via its SDK. Neither the AI coordinator nor the VeloxQ API use establishes a physical QPU or a quantum speed advantage.

Stage 2 downtime, deadlines, electricity tariffs and 4–5-job cases are synthetic test conditions, not provided industrial-factory observations. Human review and disclosure of AI assistance are required when the repository, video and project are submitted.
