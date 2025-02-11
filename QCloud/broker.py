# broker.py

from QCloud.dependencies import *
from abc import ABC, abstractmethod

class BaseBroker(ABC):
    def __init__(self, env, job, devices, job_records_manager):
        """
        Base class for all brokers.
        """
        self.env = env
        self.job = job
        self.devices = devices
        self.job_records_manager = job_records_manager

    @abstractmethod
    def assign_device(self):
        """
        Assign a job to an appropriate quantum device.
        """
        pass

    @abstractmethod
    def run(self):
        """
        Run the broker's main functionality for job processing.
        """
        pass
    
    
class SerialBroker(BaseBroker):
    def __init__(self, env, job, devices, log_event_callback, qcloud):
        """
        Initialize the ParallelBroker.

        Parameters:
        - env: SimPy environment.
        - job_id: ID of the job being handled.
        - job: The QJob object representing the job.
        - devices: List of quantum devices.
        - log_event_callback: Callback function for logging job events.
        - qcloud: Reference to the QCloud instance for job allocation.
        """
        super().__init__(env, job, devices, log_event_callback)
        self.qcloud = qcloud
        
    def assign_device(self):
        """
        Assign a job to a random available device.
        """
        device = random.choice(self.devices)
        while device.maint_lock:
            print(f'{self.env.now:.2f}: Job #{self.job.job_id} waiting. {device.name} under maintenance...')
            yield self.env.timeout(1)
        return device

    def run(self):
        """
        Assign a device and process the job.
        """
        device = yield from self.assign_device()

        # Process the job
        with device.resource.request(priority=2) as req:
            yield req
            yield from device.process_job(self.job, self.env.now)

            
# broker.py

class ParallelBroker(BaseBroker):
    def __init__(self, env, job, devices, log_event_callback, qcloud):
        """
        Initialize the ParallelBroker.

        Parameters:
        - env: SimPy environment.
        - job_id: ID of the job being handled.
        - job: The QJob object representing the job.
        - devices: List of quantum devices.
        - log_event_callback: Callback function for logging job events.
        - qcloud: Reference to the QCloud instance for job allocation.
        """
        super().__init__(env, job, devices, log_event_callback)
        self.qcloud = qcloud
    
    def assign_device(self):
        pass
    
    def run(self):
        """
        Process jobs with device allocation.
        """
        # Regular allocation to a single device
        device = random.choice(self.devices)
        while device.maint_lock:
            print(f'{self.env.now:.2f}: Job #{self.job.job_id} waiting. {device.name} under maintenance...')
            yield self.env.timeout(1)
        yield device.container.get(self.job.num_qubits)
        with device.resource.request(priority=2) as req:

            yield from device.process_job(self.job, self.env.now)
            fidelity = device.estimate_fidelity(self.job)
            # print(f"Estimated fidelity for Job #{self.job.job_id} on {device.name}: {fidelity}")
