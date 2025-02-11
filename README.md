# Quantum Cloud Simulation Environment

This repository implements a **Quantum Cloud Simulation Environment** for managing and simulating quantum computing workflows. The system is designed to handle job submissions, allocate quantum devices, and process quantum jobs efficiently. It supports dynamic job generation, resource allocation across multiple quantum devices.

## Features

- **Event-Driven Architecture**: Powered by an `EventBus` for efficient communication.
- **Dynamic Job Generation**: Support for both random and pre-defined job inputs.
- **Quantum Device Management**: Simulation of diverse quantum devices with maintenance and resource allocation.
- **Parallel and Serial Job Execution**: Brokers for assigning jobs to devices in parallel or sequentially.

---

## Installation

### Prerequisites

Ensure you have Python installed (version 3.8+ recommended). The following Python libraries are required:
- `simpy`
- `networkx`
- `matplotlib`

Install the dependencies using pip:
```bash
pip install simpy networkx matplotlib
```

### Clone the Repository

Clone this repository to your local machine:
```bash
git clone https://github.com/your-repo-name.git
cd your-repo-name
```

---

## How to Run

### Example Simulation

1. **Setup Quantum Devices**: Create a list of `QuantumDevice` instances to simulate various quantum processors.

2. **Initialize the Environment**:
   - Use the `QCloudSimEnv` class to initialize the simulation environment with your chosen devices and brokers.
Example:
```python
from QCloud import *

ibm_kawasaki = IBM_Kawasaki(env=None, name="ibm_kawasaki", printlog = True)
qcloudsimenv = QCloudSimEnv(devices=[ibm_kawasaki], broker_class=ParallelBroker,
                    job_feed_method="generator", job_generation_model=lambda: random.expovariate(lambd=0.1))
qcloudsimenv.run(until=100)
```

3. **Run the Simulation**:
   - Customize the simulation duration by modifying the `run(until=...)` parameter.

### Using Job Generator
To dispatch jobs:
- **Dynamic Job Generation**:
  Specify `job_feed_method='generator'` and optionally provide a custom job arrival model.
- **Predefined Jobs**:
  Provide a path to a `.csv` file containing job definitions and set `job_feed_method='dispatcher'`.

Example CSV format:
```csv
job_id,num_of_shots,arrival_time,circuit_depth,required_qubits
1,500,1.0,15,20
2,300,2.0,10,15
```

---

## Repository Structure

- `broker.py`: Implements parallel and serial brokers for job-device management.
- `dependencies.py`: Shared utilities and imports.
- `event_bus.py`: Event-driven communication via a lightweight `EventBus`.
- `job_generator.py`: Dynamic or pre-defined job dispatching.
- `job_records_manager.py`: Tracks and logs job lifecycle events.
- `qcloud.py`: Core cloud management and inter-device communication.
- `qcloudsimenvironment.py`: Simulation environment setup and management.
- `qdevices.py`: Quantum device simulations, including topology and maintenance.
- `qjob.py`: Represents individual quantum jobs.

---
