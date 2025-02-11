#qjob.py

class QJob:
    
    def __init__(self, job_id,                 
                 num_qubits, 
                 depth,
                 num_shots,
                 priority, 
                 arrival_time,
                 circuit_name=None, 
                 gates=None, 
                 expected_exec_time=None, 
                 noise_model=None):
        
        """
        Initializes a QJob instance.

        Parameters:
        - num_of_shots (int): The number of shots for the quantum job.
        - arrival_time (float): The time when the job arrives in the system.
        - circuit_depth (int): The depth of the quantum circuit.
        - required_qubits (int): The number of qubits required.
        - qcloud (QCloud): Reference to the QCloud object for logging.
        """

        self.job_id = job_id
        self.circuit_name = circuit_name
        self.num_qubits = num_qubits
        self.depth = depth
        self.num_shots = num_shots
        self.gates = gates
        self.expected_exec_time = expected_exec_time
        self.priority = priority
        self.noise_model = noise_model
        self.arrival_time = arrival_time
        

    def __repr__(self):
        """
        Provides a string representation of the QJob object.
        """
        return (f"QJob(job_id={self.job_id}, "
                f"circuit_name={self.circuit_name}, "
                f"num_qubits={self.num_qubits}, "
                f"depth={self.depth}, "
                f"gates={self.gates}, "
                f"expected_exec_time={self.expected_exec_time}, "
                f"priority={self.priority}, "
                f"noise_model={self.noise_model}, "
                f"arrival_time={self.arrival_time:.2f}, "
                f"num_shots={self.num_shots})")