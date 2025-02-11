# qcloudsimenvironment.py

from QCloud import *
from QCloud.job_generator import JobGenerator

class QCloudSimEnv(simpy.Environment):
    def __init__(self, devices, broker_class=ParallelBroker, job_feed_method='generator', job_generation_model=None, file_path=None):
        """
        Initialize the simulation environment.

        Parameters:
        - devices: List of quantum devices.
        - broker_class: Class of the broker to use for job handling.
        - job_feed_method: 'generator' for random job generation or 'dispatcher' for jobs from a CSV file.
        - job_generation_model: Callable for job inter-arrival times (used if method='generator').
        - file_path: Path to the .csv file containing predefined jobs (used if method='dispatcher').
        """
        super().__init__()  # Create the SimPy environment
        self.devices = devices
        self.broker_class = broker_class
        self.job_feed_method = job_feed_method
        self.job_generation_model = job_generation_model
        self.file_path = file_path
        self.event_bus = EventBus()  # Shared EventBus
        self.job_records_manager = JobRecordsManager(self.event_bus)  # Shared JobRecordsManager
        self.qcloud = QCloud(self, self.devices, self.job_records_manager)
        self.job_generator = None
        self._initialize_devices()
        self._initialize_job_generator()

    def _initialize_devices(self):
        """Assign the environment and initialize each device."""
        for device in self.devices:
            device.assign_env(self)
            device.job_records_manager = self.job_records_manager
            device.event_bus = self.event_bus
            self.process(device.maintenance(False))

    def _initialize_job_generator(self):
        """Initialize the job generator based on the feed method."""
        self.job_generator = JobGenerator(
            env=self,
            broker_class=self.broker_class,
            devices=self.devices,
            job_records_manager=self.job_records_manager,
            event_bus=self.event_bus,
            qcloud=self.qcloud,
            method=self.job_feed_method,
            job_generation_model=self.job_generation_model,
            file_path=self.file_path
        )

    def run(self, until=None):
        """
        Run the simulation including job generation and device communication.

        Parameters:
        - until: Time to run the simulation.
        """
        # Start job generation
        self.process(self.job_generator.run())

        # Run the simulation
        if until is not None:
            super().run(until=until)
        else:
            super().run()
