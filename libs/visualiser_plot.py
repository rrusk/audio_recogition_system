"""
Provides a plot-based audio visualizer using Matplotlib.
"""

from matplotlib import pyplot


class VisualiserPlot:
    """
    A class to generate a simple waveform plot for audio data.
    """

    @staticmethod
    def show(data):
        """
        Displays a waveform plot of the given audio data.

        Args:
            data (np.array): A numpy array of audio samples.
        """
        pyplot.plot(data)
        pyplot.show()
