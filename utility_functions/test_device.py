import sys
import os

# Add the path to your_module to sys.path
module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(module_path)

import unittest
import simpy
from devices import QuantumDevice, IBM_guadalupe, IBM_tokyo  # Import your quantum device classes

# The function to be tested
def has_reversed_pair(data):
    pairs_set = set()
    
    for pair in data:
        p = tuple(pair)
        if (p[1], p[0]) in pairs_set:
            return True  # Reversed pair found
        pairs_set.add(p)
    
    return False  # No reversed pair found


class TestHasReversedPairDynamic(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Set up the quantum device dynamically."""
        env = simpy.Environment()  # Create the simpy environment
        cls.device_class = cls.device_class(env)  # Instantiate the device dynamically


    def test_reversed_pair_exists(self):
        """Test case where a reversed pair exists in the quantum device's nodes."""
        print(f"testing {self.device_class.name}")
        data = self.device_class.nodes
        self.assertFalse(has_reversed_pair(data), "Should return True when reversed pair exists")

    def test_no_reversed_pair(self):
        """Test case where no reversed pair exists in the quantum device's nodes."""
        data = self.device_class.nodes
        self.assertFalse(has_reversed_pair(data), "Should return False when no reversed pair exists")

    def test_empty_data(self):
        """Test case where the data is empty."""
        data = self.device_class.nodes
        self.assertFalse(has_reversed_pair(data), "Should return False for empty data")

    def test_single_pair(self):
        """Test case where only one pair is present."""
        data = self.device_class.nodes
        self.assertFalse(has_reversed_pair(data), "Should return False for single pair")

    def test_multiple_reversed_pairs(self):
        """Test case where there are multiple reversed pairs in the data."""
        data = self.device_class.nodes
        self.assertFalse(has_reversed_pair(data), "Should return True when multiple reversed pairs exist")


def run_tests_with_device_class(device_class):
    """Helper function to run the tests with a given device class."""
    # Attach the device class to the test class dynamically
    TestHasReversedPairDynamic.device_class = device_class
    
    # Create a test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHasReversedPairDynamic)
    
    # Run the test suite
    result = unittest.TextTestRunner().run(suite)
    
    return result


if __name__ == '__main__':
    # Run tests for multiple device classes
    print("Running tests for IBM_guadalupe")
    result_guadalupe = run_tests_with_device_class(IBM_guadalupe)

    print("\nRunning tests for IBM_tokyo")
    result_tokyo = run_tests_with_device_class(IBM_tokyo)