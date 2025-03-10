# mtrip Test Suite

This directory contains unit and integration tests for the mtrip package.

## Running Tests

You can run the tests in several ways:

1. Using the test runner script:
   ```
   python tests/run_tests.py
   ```

2. Using Python's unittest module directly:
   ```
   python -m unittest discover -v tests
   ```

3. Running specific test files:
   ```
   python -m unittest tests/test_newick_parsing.py
   ```

4. Running a specific test case:
   ```
   python -m unittest tests.test_newick_parsing.TestNewickParsing.test_simplify_nwk
   ```

## Test Structure

The test suite includes the following test files:

- `test_newick_parsing.py`: Tests for Newick string parsing functions
- `test_bipartitions.py`: Tests for bipartition extraction and processing
- `test_triplet_omp.py`: Tests for the C code wrappers in triplet_omp
- `test_median_reconstruction.py`: Integration tests for the median tree reconstruction algorithm
- `test_cli.py`: Tests for the command-line interface

## Test Data

Example Newick files for testing are located in the `test_data/` directory.