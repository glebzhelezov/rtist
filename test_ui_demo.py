#!/usr/bin/env python
"""
Demo script for testing the RTIST UI with mock functionality.
"""
import sys
import os
import time
import random
from typing import List

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Mock the median_triplet_trees function for testing
def mock_median_triplet_trees(nwks: List[str], n_threads=None, return_extra=False):
    """Mock implementation for testing UI."""
    # Simulate some processing time
    time.sleep(2)
    
    # Generate some mock results based on input
    results = []
    taxa = set()
    
    # Extract taxa from input trees
    for nwk in nwks:
        chars = [c for c in nwk if c.isalpha()]
        taxa.update(chars)
    
    taxa = sorted(taxa)
    
    # Generate some mock median trees
    if len(taxa) >= 3:
        results.append(f"(({taxa[0]},{taxa[1]}),{taxa[2]});")
        if len(taxa) >= 4:
            results.append(f"({taxa[0]},({taxa[1]},({taxa[2]},{taxa[3]})));")
        if len(taxa) >= 5:
            results.append(f"(({taxa[0]},{taxa[1]}),(({taxa[2]},{taxa[3]}),{taxa[4]}));")
    
    if return_extra:
        # Mock additional return values
        reverse_dict = list(taxa)
        weights = [random.randint(1, 10) for _ in range(len(taxa))]
        stack = [random.randint(1, 5) for _ in range(len(taxa))]
        best_biparts = [(i, i+1) for i in range(len(taxa)-1)]
        return results, reverse_dict, weights, stack, best_biparts
    
    return results

# Monkey patch the function for testing
import mtrip.cli.mtrip_ui as ui_module
ui_module.median_triplet_trees = mock_median_triplet_trees

# Also patch the import check
ui_module.__version__ = "0.3.0"

if __name__ == "__main__":
    from mtrip.cli.mtrip_ui import main
    main()