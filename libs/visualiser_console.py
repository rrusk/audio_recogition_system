"""
Provides a console-based audio visualizer.
"""

import numpy as np


class VisualiserConsole:
    """
    A class to generate a simple text-based progress bar for audio amplitude.
    """

    @staticmethod
    def calc(data):
        """
        Calculates the peak audio level and generates a corresponding text bar.

        Args:
            data (np.array): A numpy array of audio samples.

        Returns:
            tuple: A tuple containing the calculated peak value (float) and
                   the visual bar (string).
        """
        peak = np.average(np.abs(data)) * 2
        bars = "#" * int(200 * peak / 2**16)
        return (peak, bars)
