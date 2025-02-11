#qdevices.py

from utility_functions.graph_manipulation import *
import networkx as nx
import simpy
import json
import os
import random
import pandas as pd
import math
from abc import ABC, abstractmethod

class BaseQDevice(ABC):
    """
    Abstract base class for quantum devices.
    """
    def __init__(self, name, env, event_bus):
        """
        Initialize a base device.

        Parameters:
        - name (str): Name of the quantum device.
        - env (simpy.Environment): The simulation environment.
        - event_bus (EventBus): EventBus instance for event-driven communication.
        """
        self.name = name
        self.env = env
        self.event_bus = event_bus

    @abstractmethod
    def process_job(self, job_id, qubits_required):
        """
        Abstract method for processing a job on the device.
        """
        pass

    @abstractmethod
    def maintenance(self):
        """
        Abstract method for performing maintenance on the device.
        """
        pass

    @abstractmethod
    def calculate_process_time(self, qubits_required):
        """
        Abstract method to calculate the processing time for a job.
        """
        pass
    

class QuantumDevice(BaseQDevice):
    """
    QuantumDevice is a class representing a quantum computing device with a specific topology.

    Attributes:
    -----------
    name : str
        The name of the quantum device.
    nodes_file_name : str
            File name that contains a list of nodes representing the connections between qubits in JSON format.
        pos_file_name : str
            File name that contains a dictionary representing the positions of the qubits for visualization purposes in JSON format.
    color_map : list
        A list of color representing the color of nodes. 
    number_of_qubits: int
        An integer representing the number of physical qubits available.
    env : simpy.Environment
        The simulation environment.
    container : simpy.Container
        A container in simpy to manage resources.
    resource : simpy.Resource
        A resource manager in simpy for handling shared resources.
    """

    def __init__(self, name, nodes_file_name, pos_file_name, env, maintenance_interval, maintenance_duration, maintenance_switch, event_bus=None, job_records_manager=None, printlog=True):
        """
        Initializes the QuantumDevice with a name, nodes, and positions.

        Parameters:
        -----------
        name : str
            The name of the quantum device.
        nodes_file_name : str
            File name that contains a list of nodes representing the connections between qubits in JSON format.
        pos_file_name : str
            File name that contains a dictionary representing the positions of the qubits for visualization purposes in JSON format.
        color_map : list
            A list of color representing the color of nodes. 
        number_of_qubits: int
            An integer representing the number of physical qubits available.
        env : simpy.Environment
            The simulation environment.
        """
        self.name = name
        self.env = None     # simpy simulation environment
        self.maintenance_interval = maintenance_interval
        self.maintenance_duration = maintenance_duration
        self.maintenance_switch = maintenance_switch
        self.job_records_manager = job_records_manager
        self.event_bus = event_bus
        self.printlog = printlog

        # Load nodes and positions from files
        self.nodes, self.pos = self.load_topology(nodes_file_name, pos_file_name)
        
        # number of qubits calculated from position dictionary
        self.number_of_qubits = len(self.pos)
        
        # generate the color_map as 'skyblue' for each qubit
        self.color_map = ['skyblue' for _ in range(self.number_of_qubits)]
        
        # Initialize the graph with nodes
        self.graph = nx.Graph()
        self.graph.add_edges_from(self.nodes)
        
        # Initialize the simpy container and resource
        self.container = simpy.Container(env=self.env, capacity=len(self.pos), init=len(self.pos))
        self.resource = simpy.PriorityResource(env=env, capacity=1)
        self.maint_lock = False
        
    def assign_env(self, env):
        """
        Assigns a SimPy environment and initializes SimPy-dependent attributes.
        """
        self.env = env
        self.container = simpy.Container(env=env, capacity=len(self.pos), init=len(self.pos))
        self.resource = simpy.PriorityResource(env=env, capacity=1)

        # Start maintenance process if required
        if self.maintenance_switch:
            self.env.process(self.maintenance())
            
    def load_topology(self, nodes_file_name, pos_file_name):
        
        """Loads the nodes and positions from the specified JSON files."""
        
        # Get the directory of the current file
        current_dir = os.path.dirname(os.path.abspath(__file__))  
        topology_dir = os.path.join(current_dir, 'topology')
        nodes_file = os.path.join(topology_dir, nodes_file_name)
        pos_file = os.path.join(topology_dir, pos_file_name)
        
        with open(nodes_file, 'r') as f:
            nodes = json.load(f)['nodes']
     
        with open(pos_file, 'r') as f:
            pos = {int(k): tuple(v) for k, v in json.load(f)['pos'].items()}
        
        return nodes, pos
    
    def maintenance(self, maintenance_switch):
        """
        Maintenance process that will run at regular intervals.
        The interval and duration of maintenance are set by the child class.
        """
        yield self.env.timeout(random.randint(60, 120))
        
        if self.maintenance_switch: 
            while True:
                # Wait for the maintenance interval
                yield self.env.timeout(self.maintenance_interval)
                             
                # New job won't be able to process on the machine
                self.maint_lock = True
                
                # Block the resource during maintenance with highest priority (priority=1)
                with self.resource.request(priority=1) as req:

                    remaining_qubits = self.container.level                                                   
                    yield self.env.timeout(self.maintenance_duration)

                    # Job will be able to assign the machine again
                    self.maint_lock = False
            
    def calculate_process_time(self, job):
        """Simple way to calculate the processing time based on the number of qubits required.
            Child class will override this"""
        if self.printlog:
            print(f"{self.env.now:.2f}: Calculating process time for {job.num_qubits} qubits on {self.name}.")
        return job.num_qubits * 100

    def process_job(self, job, wait_time_start):
        
        job_id = job.job_id
        qubits_required = job.num_qubits
        """Process a job on this quantum device."""
        if self.printlog:
            print(f"{self.env.now:.2f}: {self.name} received job #{job_id} requiring {qubits_required} qubits.")
        
        # Log job start processing
        self.job_records_manager.log_job_event(job_id, 'devc_name', self.name)
        self.job_records_manager.log_job_event(job_id, 'devc_start', round(self.env.now,4))
        
        # Publish a 'device_start' event
        self.event_bus.publish("device_start", {
            "device": self.name,
            "job_id": job_id,
            "timestamp": round(self.env.now, 2),
        })
        
        selected_vertices = select_vertices_fast(self, qubits_required, job_id)

        while selected_vertices is None or self.maint_lock:
            if self.printlog:
                print(f"{self.env.now:.2f}: Job #{job_id} is waiting for {self.name}.")
            yield self.env.timeout(1)  # Wait before retrying
            selected_vertices = select_vertices_fast(self, qubits_required, job_id)

        remove_connectivity(self, selected_vertices, 'red')

        
        process_time = self.calculate_process_time(job)
        if self.printlog:
            print(f"{self.env.now:.2f}: Job #{job_id} will take {process_time:.4f} sim-mins on {self.name}.")
        
        yield self.env.timeout(process_time)
        

        # Log job finish processing
        self.job_records_manager.log_job_event(job_id, 'devc_finish', round(self.env.now,4))
        
        
        # Publish a 'device_finish' event
        self.event_bus.publish("device_finish", {
            "device": self.name,
            "job_id": job_id,
            "timestamp": round(self.env.now, 2),
        })
        
        yield self.container.put(qubits_required)
        reconnect_nodes(self, selected_vertices)
        if self.printlog:
            print(f"{self.env.now:.2f}: Job #{job_id} completed on {self.name}.")
    
    def estimate_fidelity(self, job):
        pass
            
class IBM_QuantumDevice(QuantumDevice):
    """
    A base class for IBM quantum devices that defines common attributes.
    """

    def __init__(self, name, nodes_file_name, pos_file_name, env, maintenance_interval, maintenance_duration, maintenance_switch, clops, qvol, median_T1, median_T2, processor_type, cali_filepath=None, printlog=True):
        super().__init__(name, nodes_file_name, pos_file_name, env, maintenance_interval, maintenance_duration, maintenance_switch, printlog)
        
        # IBM-specific attributes
        self.clops = clops  # Circuit Layer Operations Per Second
        self.qvol = qvol # Quantum Volume
        self.median_T1 = median_T1  # Median T1 time in microseconds
        self.median_T2 = median_T2  # Median T2 time in microseconds
        self.processor_type = processor_type  # Type of quantum processor
        self.cali_filepath = cali_filepath # Calibration file path
        self.printlog = printlog
        self.readout_errors, self.single_qubit_gate_errors, self.two_qubit_gate_errors = self.extract_errors_from_csv()

    def calculate_process_time(self, job):
        """
        Calculate processing time considering IBM-specific metrics.
        """
        M = 100
        K = 10
        S = job.num_shots
        D = math.log2(self.qvol)

        return  M * K * S * D / self.clops / 60
    
    def extract_errors_from_csv(self):
        """
        Extract errors specific to IBM devices from calibration data.
        """
        # file_path = 'QCloud/calibration/ibm_fez_calibrations_2025-01-13T16_54_24Z.csv'
        if self.cali_filepath is None: 
            self.cali_filepath = 'QCloud/calibration/ibm_fez_calibrations_2025-01-13T16_54_24Z.csv'
            
        file_path = self.cali_filepath
        calibration_data = pd.read_csv(file_path)
        calibration_data.columns = calibration_data.columns.str.strip()

        readout_errors = calibration_data["Readout assignment error"].tolist()
        single_qubit_gate_errors = {
            "rx": calibration_data["RX error"].mean(),
            "x": calibration_data["Pauli-X error"].mean(),
        }
        two_qubit_gate_errors = {}
        for cz_errors in calibration_data["CZ error"]:
            pairs = cz_errors.split(";")
            for pair in pairs:
                gate, error = pair.split(":")
                two_qubit_gate_errors[gate] = float(error)

        return readout_errors, single_qubit_gate_errors, two_qubit_gate_errors

    def estimate_fidelity(self, job):
        """
        Estimate fidelity for a quantum job using IBM calibration data.
        """
        num_qubits = job.num_qubits
        depth = job.depth

        # Estimate single-qubit gate fidelity
        avg_single_qubit_error = self.single_qubit_gate_errors["rx"]
        single_qubit_fidelity = (1 - avg_single_qubit_error) ** depth

        # Estimate readout fidelity
        avg_readout_error = sum(self.readout_errors) / len(self.readout_errors)
        readout_fidelity = (1 - avg_readout_error) ** num_qubits

        # Combined fidelity
        estimated_fidelity = single_qubit_fidelity * readout_fidelity
        self.job_records_manager.log_job_event(job.job_id, 'fidelity', round(estimated_fidelity,4))   
        return estimated_fidelity
    
class IBM_guadalupe(IBM_QuantumDevice):
    """
    IBM Guadalupe is one of IBM's quantum processors based on superconducting qubits.
    Source: https://quantum-computing.ibm.com/
    """
    def __init__(self, env, name=None, printlog=True):

        super().__init__(name = name if name else __class__.__name__ , 
                         nodes_file_name = 'IBM_guadalupe_nodes.json', 
                         pos_file_name = 'IBM_guadalupe_pos.json', 
                         env = env, 
                         maintenance_interval = 100, 
                         maintenance_duration = 15, 
                         maintenance_switch = False, 
                         clops=1400,  # Example value, need to update real data
                         qvol = 32,
                         median_T1=80,  # Example value in microseconds, need to update real data
                         median_T2=120,  # Example value in microseconds, need to update real data
                         processor_type="superconducting",
                         printlog=printlog)       
        
        
               
class IBM_tokyo(IBM_QuantumDevice):
    """
    IBM Tokyo is part of IBM's fleet of quantum processors. 
    It has been used for collaborative research with academic and industrial partners.
    Source: https://quantum-computing.ibm.com/
    """
    def __init__(self, env, name=None, printlog=True):   
        
        super().__init__(name = name if name else __class__.__name__ , 
                         nodes_file_name = 'IBM_tokyo_nodes.json', 
                         pos_file_name = 'IBM_tokyo_pos.json', 
                         env = env, 
                         maintenance_interval = 120, 
                         maintenance_duration = 15, 
                         maintenance_switch = False,
                         clops=1400,  # Example value, need to update real data
                         qvol = 32,
                         median_T1=80,  # Example value in microseconds, need to update real data
                         median_T2=120,  # Example value in microseconds, need to update real data
                         processor_type="superconducting",
                         printlog=printlog)       

                      
        
                
class IBM_montreal(IBM_QuantumDevice): 
    """
    IBM Montreal is a superconducting qubit-based quantum processor.
    Source: https://quantum-computing.ibm.com/
    """
    def __init__(self, env, name=None, printlog=True):    
                
        super().__init__(name = name if name else __class__.__name__ , 
                         nodes_file_name = 'IBM_montreal_nodes.json', 
                         pos_file_name = 'IBM_montreal_pos.json', 
                         env = env, 
                         maintenance_interval = 140, 
                         maintenance_duration = 25, 
                         maintenance_switch = False,
                         clops=1400,  # Example value, need to update real data
                         qvol = 32,
                         median_T1=80,  # Example value in microseconds, need to update real data
                         median_T2=120,  # Example value in microseconds, need to update real data
                         processor_type="superconducting",
                         printlog=printlog)       
        
   
           
class IBM_rochester(IBM_QuantumDevice):
    """
    IBM Rochester is one of the early quantum processors from IBM, 
    named after the city of Rochester, New York, where IBM has a 
    significant presence. It is primarily used for foundational 
    research in quantum computing and testing new quantum algorithms.
    Source: https://quantum-computing.ibm.com/
    """
    def __init__(self, env, name=None, printlog=True):    
        
        super().__init__(name = name if name else __class__.__name__ , 
                         nodes_file_name = 'IBM_rochester_nodes.json', 
                         pos_file_name = 'IBM_rochester_pos.json', 
                         env = env, 
                         maintenance_interval = 140, 
                         maintenance_duration = 25, 
                         maintenance_switch = False,
                         clops=1400,  # Example value, need to update real data
                         qvol = 32,
                         median_T1=80,  # Example value in microseconds, need to update real data
                         median_T2=120,  # Example value in microseconds, need to update real data
                         processor_type="superconducting",
                         printlog=printlog)       
  
        
        
class IBM_hummingbird(IBM_QuantumDevice):
    """
    IBM Hummingbird is a more advanced quantum processor, part of IBM's effort to scale up quantum computing capabilities significantly. It is designed for more complex quantum computations, exploring error correction techniques, and scaling towards practical quantum advantage.
    Source: https://quantum-computing.ibm.com/
    """
    def __init__(self, env, name=None, printlog=True):

        super().__init__(name = name if name else __class__.__name__ , 
                         nodes_file_name = 'IBM_hummingbird_nodes.json', 
                         pos_file_name = 'IBM_hummingbird_pos.json', 
                         env = env, 
                         maintenance_interval = 140, 
                         maintenance_duration = 25, 
                         maintenance_switch = False,
                         clops=1400,  # Example value, need to update real data
                         qvol = 128, # https://docs.quantum.ibm.com/guides/processor-types
                         median_T1=80,  # Example value in microseconds, need to update real data
                         median_T2=120,  # Example value in microseconds, need to update real data
                         processor_type="superconducting",
                         printlog=printlog)                   

### IBM machines that are online as of 01-26-2025        
        
class IBM_Marrakesh(IBM_QuantumDevice):
    """
    Source: https://quantum.ibm.com/services/resources
    """
    def __init__(self, env, name=None, printlog=True):     
                
        super().__init__(name = name if name else __class__.__name__ , 
                         nodes_file_name = 'IBM_heron_r2_nodes.json', 
                         pos_file_name = 'IBM_heron_r2_pos.json', 
                         env = env, 
                         maintenance_interval = 180, # randomly assigned minutes 
                         maintenance_duration = 40, # randomly assigned minutes 
                         maintenance_switch = False,
                         clops=195000,  # updated real data on 01-26-2025
                         qvol = 128, # https://docs.quantum.ibm.com/guides/processor-types
                         median_T1=163.59,  # in microseconds, updated real data on 12-8-2024
                         median_T2=108.55,  # in microseconds, updated real data on 12-8-2024
                         processor_type="Heron r2",
                         printlog=printlog)      

        
        
class IBM_Fez(IBM_QuantumDevice):
    """
    Source: https://quantum.ibm.com/services/resources
    """
    def __init__(self, env, name=None, printlog=True):     
                
        super().__init__(name = name if name else __class__.__name__ , 
                         nodes_file_name = 'IBM_heron_r2_nodes.json', 
                         pos_file_name = 'IBM_heron_r2_pos.json', 
                         env = env, 
                         maintenance_interval = 120, # randomly assigned minutes 
                         maintenance_duration = 60, # randomly assigned minutes 
                         maintenance_switch = False,
                         clops=195000,  # updated real data on 01-26-2025
                         qvol = 128, # https://docs.quantum.ibm.com/guides/processor-types
                         median_T1=110.89,  # in microseconds, updated real data on 12-8-2024
                         median_T2=91.27,  # in microseconds, updated real data on 12-8-2024
                         processor_type="Heron r2",
                         printlog=printlog)              

        

class IBM_Torino(IBM_QuantumDevice):
    """
    Source: https://quantum.ibm.com/services/resources
    """
    def __init__(self, env, name=None, printlog=True):     
                
        super().__init__(name = name if name else __class__.__name__ , 
                         nodes_file_name = 'IBM_heron_r1_nodes.json', 
                         pos_file_name = 'IBM_heron_r1_pos.json', 
                         env = env, 
                         maintenance_interval = 150, # randomly assigned minutes
                         maintenance_duration = 45, # randomly assigned minutes
                         maintenance_switch = False,
                         clops=210000,  # updated real data on 01-26-2025
                         qvol = 128, # https://docs.quantum.ibm.com/guides/processor-types
                         median_T1=170.21,  # in microseconds, updated real data on 12-8-2024
                         median_T2=134.5,  # in microseconds, updated real data on 12-8-2024
                         processor_type="Heron r1",
                         printlog=printlog)                

        
        
class IBM_Quebec(IBM_QuantumDevice):
    """
    Source: https://quantum.ibm.com/services/resources
    """
    def __init__(self, env, name=None, printlog=True):     
                
        super().__init__(name = name if name else __class__.__name__ , 
                         nodes_file_name = 'IBM_eagle_r3_nodes.json', 
                         pos_file_name = 'IBM_eagle_r3_pos.json', 
                         env = env, 
                         maintenance_interval = 150, # randomly assigned minutes
                         maintenance_duration = 45, # randomly assigned minutes
                         maintenance_switch = False,
                         clops=32000,  # updated real data on 01-26-2025
                         qvol = 128, # https://docs.quantum.ibm.com/guides/processor-types
                         median_T1=299.8,  # in microseconds, updated real data on 12-8-2024
                         median_T2=209.3,  # in microseconds, updated real data on 12-8-2024
                         processor_type="Eagle r3",
                         printlog=printlog)     

        
        

class IBM_Kyiv(IBM_QuantumDevice):
    """
    Source: https://quantum.ibm.com/services/resources
    """
    def __init__(self, env, name=None, printlog=True):     
                
        super().__init__(name = name if name else __class__.__name__ , 
                         nodes_file_name = 'IBM_eagle_r3_nodes.json', 
                         pos_file_name = 'IBM_eagle_r3_pos.json', 
                         env = env, 
                         maintenance_interval = 160, # randomly assigned minutes
                         maintenance_duration = 40, # randomly assigned minutes
                         maintenance_switch = False,
                         clops=30000,  # updated real data on 01-26-2025
                         qvol = 128, # https://docs.quantum.ibm.com/guides/processor-types
                         median_T1=185.7,  # in microseconds, updated real data on 12-8-2024
                         median_T2=146.38,  # in microseconds, updated real data on 12-8-2024
                         processor_type="Eagle r3",
                         printlog=printlog)    
        
        
        
class IBM_Brisbane(IBM_QuantumDevice):
    """
    Source: https://quantum.ibm.com/services/resources
    """
    def __init__(self, env, name=None, printlog=True):     
                
        super().__init__(name = name if name else __class__.__name__ , 
                         nodes_file_name = 'IBM_eagle_r3_nodes.json', 
                         pos_file_name = 'IBM_eagle_r3_pos.json', 
                         env = env, 
                         maintenance_interval = 180, # randomly assigned minutes
                         maintenance_duration = 60, # randomly assigned minutes
                         maintenance_switch = False,
                         clops=180000,  # updated real data on 01-26-2025
                         qvol = 128, # https://docs.quantum.ibm.com/guides/processor-types
                         median_T1=212.07,  # in microseconds, updated real data on 12-8-2024
                         median_T2=124.65,  # in microseconds, updated real data on 12-8-2024
                         processor_type="Eagle r3",
                         printlog=printlog)    

        
        
        
class IBM_Sherbrooke(IBM_QuantumDevice):
    """
    Source: https://quantum.ibm.com/services/resources
    """
    def __init__(self, env, name=None, printlog=True):     
                
        super().__init__(name = name if name else __class__.__name__ , 
                         nodes_file_name = 'IBM_eagle_r3_nodes.json', 
                         pos_file_name = 'IBM_eagle_r3_pos.json', 
                         env = env, 
                         maintenance_interval = 120, # randomly assigned minutes
                         maintenance_duration = 40, # randomly assigned minutes
                         maintenance_switch = False,
                         clops=30000,  # updated real data on 01-26-2025
                         qvol = 128, # https://docs.quantum.ibm.com/guides/processor-types
                         median_T1=269.72,  # in microseconds, updated real data on 12-8-2024
                         median_T2=159.98,  # in microseconds, updated real data on 12-8-2024
                         processor_type="Eagle r3",
                         printlog=printlog)    
        
        
        
        
class IBM_Kawasaki(IBM_QuantumDevice):
    """
    Source: https://quantum.ibm.com/services/resources
    """
    def __init__(self, env, name=None, printlog=True):     
                
        super().__init__(name = name if name else __class__.__name__ , 
                         nodes_file_name = 'IBM_eagle_r3_nodes.json', 
                         pos_file_name = 'IBM_eagle_r3_pos.json', 
                         env = env, 
                         maintenance_interval = 140, # randomly assigned minutes
                         maintenance_duration = 40, # randomly assigned minutes
                         maintenance_switch = False,
                         clops=29000,  # updated real data on 01-26-2025
                         qvol = 128, # https://docs.quantum.ibm.com/guides/processor-types
                         median_T1=185.7,  # in microseconds, updated real data on 12-8-2024
                         median_T2=146.38,  # in microseconds, updated real data on 12-8-2024
                         processor_type="Eagle r3",
                         printlog=printlog)    
        
         
        
class IBM_Rensselaer(IBM_QuantumDevice):
    """
    Source: https://quantum.ibm.com/services/resources
    """
    def __init__(self, env, name=None, printlog=True):     
                
        super().__init__(name = name if name else __class__.__name__ , 
                         nodes_file_name = 'IBM_eagle_r3_nodes.json', 
                         pos_file_name = 'IBM_eagle_r3_pos.json', 
                         env = env, 
                         maintenance_interval = 120, # randomly assigned minutes
                         maintenance_duration = 30, # randomly assigned minutes
                         maintenance_switch = False,
                         clops=32000,  # updated real data on 01-26-2025
                         qvol = 128, # https://docs.quantum.ibm.com/guides/processor-types
                         median_T1=232.22,  # in microseconds, updated real data on 12-8-2024
                         median_T2=158.19,  # in microseconds, updated real data on 12-8-2024
                         processor_type="Eagle r3",
                         printlog=printlog)    
        
        

class IBM_Brussels(IBM_QuantumDevice):
    """
    Source: https://quantum.ibm.com/services/resources
    """
    def __init__(self, env, name=None, printlog=True):     
                
        super().__init__(name = name if name else __class__.__name__ , 
                         nodes_file_name = 'IBM_eagle_r3_nodes.json', 
                         pos_file_name = 'IBM_eagle_r3_pos.json', 
                         env = env, 
                         maintenance_interval = 160, # randomly assigned minutes
                         maintenance_duration = 40, # randomly assigned minutes
                         maintenance_switch = False,
                         clops=220000,  # updated real data on 01-26-2025
                         qvol = 128, # https://docs.quantum.ibm.com/guides/processor-types
                         median_T1=308.18,  # in microseconds, updated real data on 12-8-2024
                         median_T2=177.36,  # in microseconds, updated real data on 12-8-2024
                         processor_type="Eagle r3",
                         printlog=printlog)    
        
        
        
class IBM_Strasbourg(IBM_QuantumDevice):
    """
    Source: https://quantum.ibm.com/services/resources
    """
    def __init__(self, env, name=None, printlog=True):     
                
        super().__init__(name = name if name else __class__.__name__ , 
                         nodes_file_name = 'IBM_eagle_r3_nodes.json', 
                         pos_file_name = 'IBM_eagle_r3_pos.json', 
                         env = env, 
                         maintenance_interval = 180, # randomly assigned minutes
                         maintenance_duration = 60, # randomly assigned minutes
                         maintenance_switch = False,
                         clops=220000,  # updated real data on 01-26-2025
                         qvol = 128, # https://docs.quantum.ibm.com/guides/processor-types
                         median_T1=280.84,  # in microseconds, updated real data on 12-8-2024
                         median_T2=143.8,  # in microseconds, updated real data on 12-8-2024
                         processor_type="Eagle r3",
                         printlog=printlog)    
        
        
        
class Amazon_dwave(QuantumDevice):
    """
    The D-Wave QPU is a lattice of interconnected qubits. While some qubits connect to others via couplers, the D-Wave QPU is not fully connected. Instead, the qubits of D-Wave annealing quantum computers interconnect in one of the following topologies:

    Pegasus: 14-1026 Next-Generation Topology of D-Wave Quantum Processors
    https://www.dwavesys.com/media/jwwj5z3z/14-1026a-c_next-generation-topology-of-dw-quantum-processors.pdf?_gl=1*sl9028*_gcl_au*NDI1MTIwMzY4LjE3MjI1NDgzNTk.*_ga*OTk3MzI5MzA0LjE3MjI1NDgzNTk.*_ga_DXNKH9HE3W*MTcyMjU3MDMwOC4yLjEuMTcyMjU3MDM3Ni42MC4wLjA.

    Zephyr: 14-1056 Zephyr Topology of D-Wave Quantum Processors
    https://www.dwavesys.com/media/2uznec4s/14-1056a-a_zephyr_topology_of_d-wave_quantum_processors.pdf?_gl=1*sl9028*_gcl_au*NDI1MTIwMzY4LjE3MjI1NDgzNTk.*_ga*OTk3MzI5MzA0LjE3MjI1NDgzNTk.*_ga_DXNKH9HE3W*MTcyMjU3MDMwOC4yLjEuMTcyMjU3MDM3Ni42MC4wLjA.

    Source: https://docs.dwavesys.com/docs/latest/c_gs_4.html
    """
    def __init__(self, env, name=None, printlog=True):     
        
        super().__init__(name = name if name else __class__.__name__ , 
                         nodes_file_name = 'Amazon_dwave_nodes.json', 
                         pos_file_name = 'Amazon_dwave_pos.json', 
                         env = env, 
                         maintenance_interval = 140, 
                         maintenance_duration = 25, 
                         maintenance_switch = False,
                         printlog=printlog)     
        
        
        
        
class Chimera_dwave_72(QuantumDevice):
    """
    The Chimera topology is a specific layout of qubits used in D-Wave quantum annealers. It is designed to optimize the interconnectivity between qubits while maintaining a scalable and manufacturable architecture [1]. 

    Reference: [1] Ayanzadeh, Ramin & Mousavi, Ahmad & Halem, Milton & Finin, Tim. (2018). Quantum Annealing Based Binary Compressive Sensing with Matrix Uncertainty. 

    Source: https://www.researchgate.net/figure/Chimera-Topology-in-D-Wave-Quantum-Annealers_fig1_330102244
    
    """
    
    def __init__(self, env, name=None, printlog=True):

        super().__init__(name = name if name else __class__.__name__ , 
                         nodes_file_name = 'Chimera_dwave_72_nodes.json', 
                         pos_file_name = 'Chimera_dwave_72_pos.json', 
                         env = env, 
                         maintenance_interval = 200, 
                         maintenance_duration = 25, 
                         maintenance_switch = False,
                         printlog=printlog)     
   
  

class Chimera_dwave_128(QuantumDevice):
    """

    The Chimera topology is a specific layout of qubits used in D-Wave quantum annealers. It is designed to optimize the interconnectivity between qubits while maintaining a scalable and manufacturable architecture [1]. 

    Reference: [1] Ayanzadeh, Ramin & Mousavi, Ahmad & Halem, Milton & Finin, Tim. (2018). Quantum Annealing Based Binary Compressive Sensing with Matrix Uncertainty. 

    Source: https://www.researchgate.net/figure/Chimera-Topology-in-D-Wave-Quantum-Annealers_fig1_330102244
    
    """
    
    def __init__(self, env, name=None, printlog=True):

        super().__init__(name = name if name else __class__.__name__ , 
                         nodes_file_name = 'Chimera_dwave_128_nodes.json', 
                         pos_file_name = 'Chimera_dwave_128_pos.json', 
                         env = env, 
                         maintenance_interval = 250, 
                         maintenance_duration = 40, 
                         maintenance_switch = False,
                         printlog=printlog)     
        
        
               
class Amazon_rigetti(QuantumDevice):
    """
    The Rigetti quantum computer is one of the quantum processing units (QPUs) available through Amazon Braket, AWS's quantum computing service. The Rigetti QPUs use superconducting qubits, which are a popular choice for building quantum computers due to their scalability and relatively high coherence times. 

    References: 
    Amazon Braket - Quantum Computers https://aws.amazon.com/braket/
    Rigetti Computing - Quantum Cloud Services https://docs.rigetti.com/qcs
    Amazon Braket – Go Hands-On with Quantum Computing https://aws.amazon.com/blogs/aws/amazon-braket-go-hands-on-with-quantum-computing/

    """
    def __init__(self, env, name=None, printlog=True):

        super().__init__(name = name if name else __class__.__name__ , 
                         nodes_file_name = 'Amazon_rigetti_nodes.json', 
                         pos_file_name = 'Amazon_rigetti_pos.json', 
                         env = env, 
                         maintenance_interval = 250, 
                         maintenance_duration = 40, 
                         maintenance_switch = False,
                         printlog=printlog)     
        
        
               
class Google_sycamore(QuantumDevice):
    """
    The Sycamore quantum computer is a quantum processor developed by Google AI Quantum. The Sycamore processor uses superconducting qubits arranged in a two-dimensional grid. Each qubit is connected to four nearest neighbors, which allows for high connectivity and complex interactions needed for quantum computations.

    The processor utilizes a combination of single-qubit and two-qubit gates to perform quantum operations. The fidelity (accuracy) of these gates is crucial for the performance of the quantum computer, with single-qubit gate fidelities exceeding 99.9% and two-qubit gate fidelities around 99.4% [1].

    The Sycamore quantum computer leverages transmon qubits, which can be considered as nonlinear superconducting resonators functioning at 5 to 7 GHz. The quantum bits are encoded as the resonant circuit’s two lowest quantum eigenstates. 

    Reference: [1] AbuGhanem, M., Eleuch, H. Full quantum tomography study of Google’s Sycamore gate on IBM’s quantum computers. EPJ Quantum Technol. 11, 36 (2024). https://doi.org/10.1140/epjqt/s40507-024-00248-8

    Source: https://epjquantumtechnology.springeropen.com/articles/10.1140/epjqt/s40507-024-00248-8
    """
    
    def __init__(self, env, name=None, printlog=True):

        super().__init__(name = name if name else __class__.__name__ , 
                         nodes_file_name = 'Google_sycamore_nodes.json', 
                         pos_file_name = 'Google_sycamore_pos.json', 
                         env = env, 
                         maintenance_interval = 150, 
                         maintenance_duration = 20, 
                         maintenance_switch = False,
                         printlog=printlog)    


class Google_sycamore_53(QuantumDevice):
    """
    The Sycamore 
    quantum computer is a quantum processor developed by Google AI Quantum. The Sycamore processor uses superconducting qubits arranged in a two-dimensional grid. Each qubit is connected to four nearest neighbors, which allows for high connectivity and complex interactions needed for quantum computations.

    The processor utilizes a combination of single-qubit and two-qubit gates to perform quantum operations. The fidelity (accuracy) of these gates is crucial for the performance of the quantum computer, with single-qubit gate fidelities exceeding 99.9% and two-qubit gate fidelities around 99.4% [1].

    The Sycamore quantum computer leverages transmon qubits, which can be considered as nonlinear superconducting resonators functioning at 5 to 7 GHz. The quantum bits are encoded as the resonant circuit’s two lowest quantum eigenstates. 

    Reference: [1] AbuGhanem, M., Eleuch, H. Full quantum tomography study of Google’s Sycamore gate on IBM’s quantum computers. EPJ Quantum Technol. 11, 36 (2024). https://doi.org/10.1140/epjqt/s40507-024-00248-8

    Source: https://epjquantumtechnology.springeropen.com/articles/10.1140/epjqt/s40507-024-00248-8
    """
    
    def __init__(self, env, name=None, printlog=True):

        super().__init__(name = name if name else __class__.__name__ , 
                         nodes_file_name = 'Google_sycamore_53_nodes.json', 
                         pos_file_name = 'Google_sycamore_53_pos.json', 
                         env = env, 
                         maintenance_interval = 140, 
                         maintenance_duration = 25, 
                         maintenance_switch = False,
                         printlog=printlog)    
        