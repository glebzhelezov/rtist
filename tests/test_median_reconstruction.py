"""Integration tests for median tree reconstruction in mtrip."""

import unittest
import os
import array
from mtrip.median_tree_reconstruction import median_triplet_trees


class TestMedianReconstruction(unittest.TestCase):
    """Integration test cases for median tree reconstruction."""

    def setUp(self):
        """Set up test data."""
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.test_data_dir = os.path.join(self.test_dir, "test_data")
        
        # Simple test case with Newick strings (without semicolons for the function)
        self.nwks = [
            "((A,B),(C,D))",
            "(A,(B,(C,D)))",
            "((A,C),(B,D))"
        ]

    def test_median_triplet_trees_basic(self):
        """Test median_triplet_trees returns valid trees for a simple case."""
        # Run with default settings
        trees = median_triplet_trees(self.nwks)
        
        self.assertIsInstance(trees, list)
        self.assertGreater(len(trees), 0)
        
        # Check that each tree has a semicolon at the end
        for tree in trees:
            self.assertTrue(tree.endswith(";"))
        
        # Verify the trees contain all the expected taxa
        for tree in trees:
            self.assertIn("A", tree)
            self.assertIn("B", tree)
            self.assertIn("C", tree)
            self.assertIn("D", tree)
            
        # Check that at least one of our input trees is in the output
        # (When all trees have equal weight, at least one should be in the median set)
        input_with_semicolons = [nwk + ";" for nwk in self.nwks]
        self.assertTrue(any(tree in input_with_semicolons for tree in trees))

    def test_median_triplet_trees_with_file(self):
        """Test median_triplet_trees using a file of Newick strings."""
        # Path to the test file
        file_path = os.path.join(self.test_data_dir, "small_test.nwk")
        
        # Read Newick strings from file (removing semicolons as required by the function)
        with open(file_path, "r") as f:
            nwks = [line.strip()[:-1] for line in f]  # Remove semicolon at end
        
        # Run with parallel processing (2 threads)
        trees = median_triplet_trees(nwks, n_threads=2)
        
        self.assertIsInstance(trees, list)
        self.assertGreater(len(trees), 0)
        
        # Basic validation of the output trees
        for tree in trees:
            self.assertTrue(tree.endswith(";"))
            for taxon in ["A", "B", "C", "D"]:
                self.assertIn(taxon, tree)

    def test_return_extra(self):
        """Test median_triplet_trees with return_extra=True returns additional data."""
        trees, reverse_dict, weights, stack, best_biparts = median_triplet_trees(
            self.nwks, return_extra=True
        )
        
        # Check that all expected return values are present
        self.assertIsInstance(trees, list)
        self.assertIsInstance(reverse_dict, list)
        # weights is actually an array.array, not a list
        self.assertIsInstance(weights, array.array)
        # stack is actually an array.array, not a list
        self.assertIsInstance(stack, array.array)
        self.assertIsInstance(best_biparts, list)
        
        # Verify trees were returned
        self.assertGreater(len(trees), 0)
        
        # Verify reverse dictionary contains all taxa
        self.assertEqual(sorted(reverse_dict), ["A", "B", "C", "D"])
        
        # Verify weights array has expected structure
        self.assertGreater(len(weights), 0)
        
        # Verify stack has expected structure
        self.assertEqual(len(stack), 2**len(reverse_dict))
        
        # Verify best_biparts has expected structure
        self.assertEqual(len(best_biparts), 2**len(reverse_dict))


if __name__ == "__main__":
    unittest.main()