"""Tests for the command-line interface of mtrip."""

import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import patch
from io import StringIO

from mtrip.cli.mtrip_cmd import main as mtrip_main


class TestCLI(unittest.TestCase):
    """Test cases for the mtrip command-line interface."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a test input file
        self.input_file = os.path.join(self.temp_dir, "input.nwk")
        with open(self.input_file, "w") as f:
            f.write("((A,B),(C,D));\n")
            f.write("(A,(B,(C,D)));\n")
            f.write("((A,C),(B,D));\n")
        
        # Define an output file path
        self.output_file = os.path.join(self.temp_dir, "output.nwk")
        
        # Define a pickle file path
        self.pickle_file = os.path.join(self.temp_dir, "weights.p")

    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directory and its contents
        shutil.rmtree(self.temp_dir)

    def test_basic_run(self):
        """Test basic execution of mtrip CLI."""
        # Mock command line arguments
        testargs = ["mtrip", self.input_file, self.output_file]
        
        # Capture stdout to avoid cluttering the test output
        with patch.object(sys, "argv", testargs):
            with patch("sys.stdout", new=StringIO()) as fake_out:
                # Run the CLI
                exit_code = mtrip_main()
        
        # Check that the command executed successfully
        self.assertEqual(exit_code, 0)
        
        # Verify output file was created
        self.assertTrue(os.path.exists(self.output_file))
        
        # Verify the output file contains valid Newick trees
        with open(self.output_file, "r") as f:
            trees = f.readlines()
        
        self.assertGreater(len(trees), 0)
        for tree in trees:
            self.assertTrue(tree.strip().endswith(";"))

    def test_print_option(self):
        """Test the --print option prints to stdout."""
        # Mock command line arguments
        testargs = ["mtrip", self.input_file, self.output_file, "--print"]
        
        # Capture stdout
        with patch.object(sys, "argv", testargs):
            with patch("sys.stdout", new=StringIO()) as fake_out:
                # Run the CLI
                exit_code = mtrip_main()
                output = fake_out.getvalue()
        
        # Check that the command executed successfully
        self.assertEqual(exit_code, 0)
        
        # Verify that the output contains trees (newlines ending with semicolons)
        self.assertTrue(any(line.strip().endswith(";") for line in output.splitlines()))

    def test_nosave_option(self):
        """Test the --nosave option prevents file creation."""
        # Mock command line arguments
        testargs = ["mtrip", self.input_file, self.output_file, "--nosave", "--print"]
        
        # Capture stdout
        with patch.object(sys, "argv", testargs):
            with patch("sys.stdout", new=StringIO()) as fake_out:
                # Run the CLI
                exit_code = mtrip_main()
        
        # Check that the command executed successfully
        self.assertEqual(exit_code, 0)
        
        # Verify output file was NOT created
        self.assertFalse(os.path.exists(self.output_file))

    def test_binary_option(self):
        """Test the --binary option creates a pickle file."""
        # Mock command line arguments
        testargs = ["mtrip", self.input_file, self.output_file, "--binary", self.pickle_file]
        
        # Capture stdout
        with patch.object(sys, "argv", testargs):
            with patch("sys.stdout", new=StringIO()) as fake_out:
                # Run the CLI
                exit_code = mtrip_main()
        
        # Check that the command executed successfully
        self.assertEqual(exit_code, 0)
        
        # Verify pickle file was created
        self.assertTrue(os.path.exists(self.pickle_file))
        
        # Verify the pickle file is non-empty (we don't try to load it as that would
        # require importing pickle and handling version compatibility issues)
        self.assertGreater(os.path.getsize(self.pickle_file), 0)


if __name__ == "__main__":
    unittest.main()