#job_generator.py
            
import json
import random
import csv
from .qjob import QJob

class JobGenerator:
    """
    Generates jobs dynamically or dispatches predefined jobs from a .csv file.
    """
    def __init__(self, env, broker_class, devices, job_records_manager, event_bus, qcloud, method='generator', job_generation_model=None, file_path=None):
        """
        Initialize the JobGenerator.

        Parameters:
        - env: SimPy environment.
        - broker_class: Class of the Broker to use for job handling.
        - devices: List of quantum devices.
        - job_records_manager: Instance of JobRecordsManager.
        - event_bus: Instance of EventBus.
        - method: 'generator' for dynamic job generation or 'dispatcher' for predefined jobs.
        - job_generation_model: Callable for job inter-arrival times (used if method='generator').
        - csv_file_path: Path to the .csv file containing predefined jobs (used if method='dispatcher').
        """
        self.env = env
        self.broker_class = broker_class
        self.devices = devices
        self.job_records_manager = job_records_manager
        self.event_bus = event_bus
        self.qcloud = qcloud
        self.method = method
        self.job_generation_model = job_generation_model or (lambda: random.expovariate(3))
        self.file_path = file_path
        # self.jobs = self._load_jobs_from_csv() if method == 'dispatcher' and csv_file_path else None
        self.job_id = 1

        if method == 'dispatcher' and file_path:
            if file_path.endswith('.csv'):
                self.jobs = self._load_jobs_from_csv()
            elif file_path.endswith('.json'):
                self.jobs = self._load_jobs_from_json()
            else:
                raise ValueError("Unsupported file format. Please use a .csv or .json file.")
    
        # Validate the method and parameters
        if method not in ['generator', 'dispatcher']:
            raise ValueError("Invalid method. Choose 'generator' or 'dispatcher'.")
        if method == 'dispatcher' and not file_path:
            raise ValueError("csv_file_path must be provided when method is 'dispatcher'.")

    def _load_jobs_from_csv(self):
        """
        Load jobs from the specified .csv file.
        """
        jobs = []
        with open(self.file_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                
                arrival_time = self.env.now if row["arrival_time"].strip() == '' else float(row["arrival_time"])
                
                jobs.append({
                    "job_id": int(row["job_id"]),
                    "num_qubits": int(row["num_qubits"]),
                    "depth": int(row["depth"]),
                    "num_shots": int(row["num_shots"]),
                    "priority": int(row["priority"]),
                    "arrival_time": arrival_time                    
                })
        return jobs

    def _load_jobs_from_json(self):
        """
        Load jobs from the specified .json file.
        """
        with open(self.file_path, 'r') as jsonfile:
            data = json.load(jsonfile)
            jobs = data.get("jobs", [])
        return jobs

    def run(self):
        """
        Run the job generator or dispatcher based on the selected method.
        """
        if self.method == 'dispatcher':  # Dispatch predefined jobs from .csv
            for job_props in self.jobs:
                # Wait until the job's arrival time

                delay = job_props["arrival_time"] - (self.env.now if self.env.now > 0 else 0)
                yield self.env.timeout(max(delay, 0.01))

                # Create the job
                job = QJob(
                    job_id=job_props["job_id"],
                    num_qubits=job_props["num_qubits"],
                    depth=job_props["depth"],
                    num_shots=job_props["num_shots"],
                    priority=job_props["priority"],
                    arrival_time=job_props["arrival_time"]
                )

                # Log job arrival
                self.job_records_manager.log_job_event(job_props["job_id"], 'arrival', round(self.env.now, 2))

                # Pass the job to the broker
                broker = self.broker_class(self.env, job, self.devices, self.job_records_manager, self.qcloud)
                self.env.process(broker.run())

        elif self.method == 'generator':  # Generate jobs dynamically
            while True:
                # Generate inter-arrival time and wait
                inter_arrival_time = self.job_generation_model()
                yield self.env.timeout(inter_arrival_time)

                # Generate a new job
                num_shots = random.randint(10000, 100000)
                arrival_time = self.env.now
                depth = random.randint(5, 20)
                num_qubits = random.randint(5, 20)
                priority = random.randint(1, 2)
                
                # For job generator, self.job_id is assigned to QJob
                job = QJob(self.job_id, num_qubits, depth, num_shots, priority, arrival_time) 
                
                # Log job arrival
                self.job_records_manager.log_job_event(self.job_id, 'arrival', round(self.env.now, 2))

                # Pass the job to the broker
                broker = self.broker_class(self.env, job, self.devices, self.job_records_manager, self.qcloud)
                self.env.process(broker.run())

                self.job_id += 1

