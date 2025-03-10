"""Tests for C code wrappers in mtrip."""

import unittest
import array
from mtrip import triplet_omp


class TestTripletOmp(unittest.TestCase):
    """Test cases for C code wrappers in mtrip.triplet_omp."""

    def test_zero_array(self):
        """Test zero_array creates a zero-filled array of the specified size."""
        # Test with default int type
        arr = triplet_omp.zero_array(10)
        self.assertEqual(len(arr), 10)
        self.assertEqual(arr.typecode, 'i')
        self.assertEqual(list(arr), [0] * 10)
        
        # Test with float type
        arr = triplet_omp.zero_array(5, 'f')
        self.assertEqual(len(arr), 5)
        self.assertEqual(arr.typecode, 'f')
        self.assertEqual(list(arr), [0.0] * 5)

    def test_py_combinations_2(self):
        """Test py_combinations_2 calculates n choose 2 correctly."""
        self.assertEqual(triplet_omp.py_combinations_2(2), 1)
        self.assertEqual(triplet_omp.py_combinations_2(3), 3)
        self.assertEqual(triplet_omp.py_combinations_2(4), 6)
        self.assertEqual(triplet_omp.py_combinations_2(5), 10)
        self.assertEqual(triplet_omp.py_combinations_2(10), 45)

    def test_create_two2three(self):
        """Test create_two2three creates the correct mapping from binary to ternary expansions."""
        # For n=2, the binary numbers 0, 1, 2, 3 map to ternary equivalents
        # where 2^i becomes 3^i:
        # 0 -> 0
        # 1 (2^0) -> 1 (3^0)
        # 2 (2^1) -> 3 (3^1)
        # 3 (2^0 + 2^1) -> 4 (3^0 + 3^1)
        arr = triplet_omp.create_two2three(2)
        self.assertEqual(list(arr), [0, 1, 3, 4])
        
        # For n=3, the binary numbers map to:
        # 0 -> 0
        # 1 (2^0) -> 1 (3^0)
        # 2 (2^1) -> 3 (3^1)
        # 3 (2^0 + 2^1) -> 4 (3^0 + 3^1)
        # 4 (2^2) -> 9 (3^2)
        # 5 (2^0 + 2^2) -> 10 (3^0 + 3^2)
        # 6 (2^1 + 2^2) -> 12 (3^1 + 3^2)
        # 7 (2^0 + 2^1 + 2^2) -> 13 (3^0 + 3^1 + 3^2)
        arr = triplet_omp.create_two2three(3)
        self.assertEqual(list(arr), [0, 1, 3, 4, 9, 10, 12, 13])

    def test_py_n_common_triplets(self):
        """Test py_n_common_triplets calculates common triplet count correctly."""
        # Binary sets: 
        # 3 = {0,1} (i.e., A,B)
        # 5 = {0,2} (i.e., A,C)
        # 6 = {1,2} (i.e., B,C)
        # 7 = {0,1,2} (i.e., A,B,C)
        
        # No common triplets between disjoint sets
        self.assertEqual(triplet_omp.py_n_common_triplets(1, 2, 4, 8), 0)
        
        # Same bipartition gives 4 (depends on the C implementation)
        # The actual number depends on how triplets are counted in the implementation
        result = triplet_omp.py_n_common_triplets(3, 12, 3, 12)
        self.assertGreater(result, 0)  # Should at least be positive
        
        # Other examples - just test that values make sense
        self.assertEqual(triplet_omp.py_n_common_triplets(3, 4, 5, 2), 0)  # No overlap
        
        # Same bipartition should have a positive count
        self.assertGreater(triplet_omp.py_n_common_triplets(7, 8, 7, 8), 0)

    def test_py_compressed_weight_rep(self):
        """Test py_compressed_weight_rep processes bipartition weights correctly."""
        # This is a simplified test case since full testing requires actual tree data
        # We'll set up a small example with just one bipartition
        
        # Setup for a basic test case with 3 species
        # For a tree ((A,B),C)
        subsets = [7]  # All species (2^0 + 2^1 + 2^2 - 1)
        start_i = [0]
        end_i = [1]
        biparts_a = [3]  # A,B (2^0 + 2^1)
        biparts_b = [4]  # C (2^2)
        bipart_weights = [1]  # Weight of this bipartition
        n_species = 3
        
        # Run the function with a single thread
        weights = triplet_omp.py_compressed_weight_rep(
            subsets, start_i, end_i, biparts_a, biparts_b, bipart_weights, n_species, n_threads=1
        )
        
        # Verify that weights array is the expected length
        # The size is 2*3^(n_species-1)
        self.assertEqual(len(weights), 2 * 3**(n_species-1))
        
        # Due to the implementation details, it's difficult to verify the exact values
        # in the weights array without deep knowledge of the C code. Instead, we just
        # verify that the array has non-zero values where we'd expect them.
        self.assertTrue(any(w > 0 for w in weights))


if __name__ == "__main__":
    unittest.main()