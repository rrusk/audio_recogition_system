"""
Initializes the libs package and configures the matplotlib backend.

This file sets the backend for matplotlib to 'TkAgg' to ensure compatibility
across different environments.
"""

import matplotlib

# Set the backend for matplotlib
matplotlib.use("TkAgg")


def x():
    """A sample function for testing."""
    print("XXX")
