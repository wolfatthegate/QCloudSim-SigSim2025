
# Quantum Cloud Simulation Environment [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.15272987.svg)](https://doi.org/10.5281/zenodo.15272987)


This repository contains the SigSim2025 artifact: a digital‑twin simulation of a quantum cloud environment, including event‑driven job brokering, dynamic/predefined job feeds, and device maintenance cycles. It supports both serial and parallel scheduling policies across multiple quantum devices.

## Prerequisites

- Git  
- Docker (recommended) or Python 3.8+

## Cloning the repository
To clone the repository, run the following command. 
```bash
git clone https://github.com/quantumcloudsim/SigSim2025.git
```

## Python Environment (if not using Docker)

1. **Create & activate a virtual environment**  
   For macOS/Linux, run the following commands: 
   ```bash
   cd SigSim2025
   python3 -m venv .venv
   source .venv/bin/activate       # macOS/Linux
   ```
   For Windows PowerShell, run the following: 
   ```bash
   cd SigSim2025
   python3 -m venv .venv
   .venv\Scripts\Activate.ps1      # Windows PowerShell
   ```
3.	**Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3.	**Run Use‑Case scripts**
   ```bash
   python3 Section-6-Use-case-1.py
   python3 Section-6-Use-case-2.py
   ```
## Containerized Artifact (using Docker)
We also generated an image for this work and made it public. You can fetch the container and reproduce the experiments via Docker.

1. **Clone the repository**
   ```bash 
   git clone https://github.com/quantumcloudsim/SigSim2025.git
   cd SigSim2025
   ```
2. **Pull the container image**

   ```bash
   docker pull ghcr.io/quantumcloudsim/sigsim2025:latest
   ```
3. **Run Use-Case 1**

    ```bash
    docker run --rm ghcr.io/quantumcloudsim/sigsim2025:latest \
    python Section-6-Use-case-1.py
    ```
3. **Run Use-Case 2**

    ```bash
    docker run --rm ghcr.io/quantumcloudsim/sigsim2025:latest \
    python Section-6-Use-case-2.py
    ```
## Repository Structure

   ```bash
      SigSim2025/
      ├── Dockerfile
      ├── README.md
      ├── requirements.txt
      ├── qcloud.py
      ├── Section-6-Use-case-1.py
      ├── Section-6-Use-case-2.py
      ├── QCloud/                  # Core simulation code
      ├── configs/                 # Configuration files
      ├── results/                 # Experiment outputs
      ├── synth_job_batches/       # Job definitions
      └── utility_functions/       # Helper scripts
   ```

## Example Code

This example demonstrates how to set up and run a simulation using the QCloud framework. The code initializes a device (using the IBM_Kawasaki class) and runs a simulation environment (QCloudSimEnv) with a custom job generation model. The simulation runs until a specified time limit.

1.	**Prepare the Environment:**
Make sure you have created a virtual environment and installed all required packages.

2.	**Run the Simulation:**
Save the following sample code in a Python file (e.g., simulate.py):

   ```python
   from QCloud import *

   ibm_kawasaki = IBM_Kawasaki(env=None, name="ibm_kawasaki", printlog=True)
   qcloudsimenv = QCloudSimEnv(
      devices=[ibm_kawasaki],
      broker_class=ParallelBroker,
      job_feed_method="generator",
      job_generation_model=lambda: random.expovariate(lambd=0.1)
   )
   qcloudsimenv.run(until=100)
   ```
3.	**Observe the Output:**
The simulation will execute, logging events to your console (as specified by printlog=True). You can review the simulation steps and results, which might include job scheduling, device processing, and more depending on how the QCloud framework is designed. If you choose to print the log, the output looks somewhat a like: 

```
0.87: ibm_kawasaki received job #1 requiring 10 qubits.
0.87: Job #1 will take 199.5885 sim-mins on ibm_kawasaki.
20.03: ibm_kawasaki received job #2 requiring 10 qubits.
20.03: Job #2 will take 205.3736 sim-mins on ibm_kawasaki.
37.74: ibm_kawasaki received job #3 requiring 17 qubits.
37.74: Job #3 will take 165.9724 sim-mins on ibm_kawasaki.
43.35: ibm_kawasaki received job #4 requiring 6 qubits.
43.35: Job #4 will take 69.5052 sim-mins on ibm_kawasaki.
50.16: ibm_kawasaki received job #5 requiring 15 qubits.
50.16: Job #5 is waiting for ibm_kawasaki.
60.16: Job #5 is waiting for ibm_kawasaki.
...
...
```
**Code Explanation**

-	IBM_Kawasaki Initialization:
   -	env=None: No specific environment passed during initialization.
   -	name="ibm_kawasaki": Assigns a name to the device instance.
   -	printlog=True: Enables logging to standard output.
-	QCloudSimEnv Setup:
   -	devices=[ibm_kawasaki]: Registers the device to be used in the simulation.
   -	broker_class=ParallelBroker: Uses the ParallelBroker class to manage job distribution.
   -	job_feed_method="generator": Configures the environment to generate jobs using a generator.
   -	job_generation_model=lambda: random.expovariate(lambd=0.1): Defines a job generation model where jobs arrive following an exponential distribution.
-	qcloudsimenv.run(until=100): Runs the simulation for 100 time units. You can modify this value to run the simulation for a different period.


## Citation 
If you use this artifact in your work, please cite:
  
   ```
     @misc{SigSim2025,
       author       = {A Digital Twin of Scalable Quantum Clouds},
       title        = {{Submission to SigSim2025}},
       year         = {2025},
       doi          = {10.5281/zenodo.15099199},
       howpublished = {\url{https://github.com/quantumcloudsim/SigSim2025.git}}
     }
   ```
