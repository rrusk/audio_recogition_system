"""
This module provides a class for reading audio from a microphone using PyAudio.
"""

import wave
import pyaudio
import numpy

from .reader import BaseReader


class MicrophoneReader(BaseReader):
    """
    A class for capturing and handling audio from a microphone input stream.
    """

    default_chunksize = 8192
    default_format = pyaudio.paInt16
    default_channels = 2
    default_rate = 44100

    def __init__(self):
        """Initializes the MicrophoneReader and PyAudio instance."""
        super().__init__()
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.data = []
        self.channels = self.default_channels
        self.chunksize = self.default_chunksize
        self.rate = self.default_rate
        self.recorded = False

    def recognize(self):
        """
        This method is implemented to satisfy the BaseReader contract.
        Microphone recognition logic is handled by other scripts.
        """

    def start_recording(
        self,
        channels=default_channels,
        rate=default_rate,
        chunksize=default_chunksize,
    ):
        """
        Starts the audio recording stream.

        Args:
            channels (int): The number of audio channels.
            rate (int): The sample rate in Hz.
            chunksize (int): The number of frames per buffer.
        """
        self.chunksize = chunksize
        self.channels = channels
        self.recorded = False
        self.rate = rate

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        self.stream = self.audio.open(
            format=self.default_format,
            channels=channels,
            rate=rate,
            input=True,
            frames_per_buffer=chunksize,
        )

        self.data = [[] for _ in range(channels)]

    def process_recording(self):
        """
        Reads a chunk of data from the stream and processes it.

        Returns:
            numpy.array: The raw audio data chunk as a numpy array.
        """
        data = self.stream.read(self.chunksize)

        # http://docs.scipy.org/doc/numpy/reference/generated/numpy.fromstring.html
        # A new 1-D array initialized from raw binary or text data in a string.
        # Note: numpy.fromstring is deprecated, using numpy.frombuffer instead.
        nums = numpy.frombuffer(data, numpy.int16)

        for c in range(self.channels):
            self.data[c].extend(nums[c :: self.channels])

        return nums

    def stop_recording(self):
        """Stops and closes the audio recording stream."""
        if not self.stream:
            return

        self.stream.stop_stream()
        self.stream.close()
        self.stream = None
        self.recorded = True

    def get_recorded_data(self):
        """
        Returns the recorded audio data.

        Returns:
            list: A list of lists, where each sublist contains the sample
                  data for a single channel.
        """
        return self.data

    def save_recorded(self, output_filename):
        """
        Saves the recorded audio data to a WAV file.

        Args:
            output_filename (str): The path to the output WAV file.
        """
        wf = wave.open(output_filename, "wb")
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.audio.get_sample_size(self.default_format))
        wf.setframerate(self.rate)

        # Interleave channel data before writing
        # Stack channels vertically (e.g., [[c1, c1], [c2, c2]])
        # then transpose to interleave them ([[c1, c2], [c1, c2]])
        interleaved_data = numpy.vstack(self.data).T

        wf.writeframes(interleaved_data.tobytes())
        wf.close()

    def play(self):
        """Placeholder for a playback function. Not yet implemented."""

    def get_recorded_time(self):
        """
        Calculates the total recorded time in seconds.

        Returns:
            float: The length of the recording in seconds.
        """
        return len(self.data[0]) / self.rate
