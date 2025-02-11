# Implementation of Fidelity_Estimator class

import pandas as pd

class Fidelity_Estimator:
    def __init__(self, calibration_file_path):
        """
        Initialize the Fidelity Estimator by loading calibration data.

        Parameters:
        - calibration_file_path: Path to the CSV file containing calibration data.
        """
        self.calibration_data = pd.read_csv(calibration_file_path)
        self.readout_errors, self.single_qubit_gate_errors, self.two_qubit_gate_errors = self.extract_errors_from_csv()

    def extract_errors_from_csv(self):
        """
        Extract readout errors, single-qubit gate errors, and two-qubit gate errors from calibration data.

        Returns:
        - readout_errors: List of readout assignment errors for each qubit.
        - single_qubit_gate_errors: Dictionary with average single-qubit gate error rates.
        - two_qubit_gate_errors: Dictionary with error rates for two-qubit gates.
        """
        # Remove trailing spaces from column names
        self.calibration_data.columns = self.calibration_data.columns.str.strip()

        # Extract readout errors: list of readout assignment errors for each qubit
        readout_errors = self.calibration_data["Readout assignment error"].tolist()

        # Extract single-qubit gate errors (using 'RX error' and 'Pauli-X error' as an example)
        single_qubit_gate_errors = {
            "rx": self.calibration_data["RX error"].mean(),  # Average RX error
            "x": self.calibration_data["Pauli-X error"].mean()  # Average Pauli-X error
        }

        # Extract two-qubit gate errors from the 'CZ error' column
        two_qubit_gate_errors = {}
        for cz_errors in self.calibration_data["CZ error"]:
            pairs = cz_errors.split(";")
            for pair in pairs:
                gate, error = pair.split(":")
                two_qubit_gate_errors[gate] = float(error)

        return readout_errors, single_qubit_gate_errors, two_qubit_gate_errors

    def estimate_fidelity(self, job):
        """
        Estimate fidelity of a quantum job using pre-computed gate and readout errors.

        Parameters:
        - job: Dictionary containing job details (num_qubits, depth, gates).

        Returns:
        - estimated_fidelity: Estimated fidelity for the job.
        """
        num_qubits = job['num_qubits']
        depth = job['depth']

        # Estimate single-qubit gate fidelity
        avg_single_qubit_error = self.single_qubit_gate_errors["rx"]  # Assuming RX as representative
        single_qubit_fidelity = (1 - avg_single_qubit_error) ** depth

        # Estimate two-qubit gate fidelity
        two_qubit_fidelity = 1.0

        # Estimate readout fidelity (average over the qubits used in the job)
        avg_readout_error = sum(self.readout_errors[:num_qubits]) / num_qubits
        readout_fidelity = (1 - avg_readout_error) ** num_qubits

        # Combined fidelity
        estimated_fidelity = single_qubit_fidelity * two_qubit_fidelity * readout_fidelity
        return estimated_fidelity