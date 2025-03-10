"""Tests for Newick string parsing in mtrip."""

import unittest
import os
from mtrip.median_tree_reconstruction import (
    simplify_nwk,
    get_names,
    get_line_names,
    splitter,
)


class TestNewickParsing(unittest.TestCase):
    """Test cases for Newick string parsing functions."""

    def setUp(self):
        """Set up test data."""
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.newick1 = "((A,B),(C,D));"
        self.newick2 = "(A,(B,(C,D)));"
        self.newick3 = "((A:0.1,B:0.2):0.3,(C:0.4,D:0.5):0.6);"
        self.newick4 = "((A name,B name),(C name,D name));"
        
        # List of test Newicks
        self.nwk_list = [self.newick1, self.newick2, self.newick3]

    def test_simplify_nwk(self):
        """Test simplify_nwk removes branch lengths and extra spaces."""
        simplified = simplify_nwk(self.newick3)
        self.assertEqual(simplified, "((A,B),(C,D))")
        
        # Test with spaces
        with_spaces = " ((A, B), (C, D)); "
        simplified = simplify_nwk(with_spaces)
        self.assertEqual(simplified, "((A,B),(C,D))")

    def test_get_line_names(self):
        """Test get_line_names extracts leaf names correctly."""
        names = get_line_names(0, self.newick1)
        self.assertEqual(sorted(names), ["A", "B", "C", "D"])
        
        # Test with branch lengths
        names = get_line_names(0, self.newick3)
        self.assertEqual(sorted(names), ["A", "B", "C", "D"])
        
        # Test with invalid newick (unlabeled tip)
        invalid_newick = "((A,),(C,D));"
        with self.assertRaises(SyntaxError):
            get_line_names(0, invalid_newick)

    def test_get_names(self):
        """Test get_names extracts and sorts all unique names from multiple Newick strings."""
        names, dictionary, reverse_dictionary = get_names(self.nwk_list)
        
        self.assertEqual(names, {"A", "B", "C", "D"})
        self.assertEqual(len(dictionary), 4)
        self.assertEqual(sorted(dictionary.keys()), ["A", "B", "C", "D"])
        self.assertEqual(sorted(reverse_dictionary), ["A", "B", "C", "D"])
        
        # Check dictionary maps names to indices
        for i, name in enumerate(sorted(["A", "B", "C", "D"])):
            self.assertEqual(dictionary[name], i)
            self.assertEqual(reverse_dictionary[i], name)

    def test_splitter(self):
        """Test splitter correctly splits Newick strings into left and right subtrees."""
        # Remove trailing semicolon for splitter
        newick = self.newick1[:-1]
        left, right = splitter(newick)
        
        self.assertEqual(left, "(A,B)")
        self.assertEqual(right, "(C,D)")
        
        # Test a more complex case
        newick = self.newick2[:-1]
        left, right = splitter(newick)
        
        self.assertEqual(left, "A")
        self.assertEqual(right, "(B,(C,D))")
        
        # Test a leaf node
        result = splitter("A")
        self.assertEqual(result, ("A",))


if __name__ == "__main__":
    unittest.main()