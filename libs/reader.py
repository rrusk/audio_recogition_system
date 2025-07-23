"""
This module provides an abstract base class for reader objects.
All specific reader implementations (e.g., for files or microphones)
should inherit from this class.
"""

from abc import ABC, abstractmethod


class BaseReader(ABC):
    """
    Abstract base class for an audio reader.

    Defines the common interface that all reader subclasses must implement.
    """

    def __init__(self):
        """Initializes the base reader."""

    @abstractmethod
    def recognize(self):
        """
        Abtract method for recognition logic.

        Subclasses must implement this method to perform their specific
        form of audio recognition.
        """
