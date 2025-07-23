#!/usr/bin/python
"""
This module provides a file reader for audio files, capable of parsing audio
data, metadata tags, and generating a unique file hash.
"""
import os
from hashlib import sha1

import numpy as np
from pydub import AudioSegment
from pydub.utils import audioop
from tinytag import TinyTag

from .reader import BaseReader


class FileReader(BaseReader):
    """
    Reads audio files using pydub, extracting channel data, metadata, and a file hash.
    """

    def __init__(self, filename):
        """
        Initializes the FileReader.

        Args:
            filename (str): The path to the audio file.
        """
        super().__init__()
        self.filename = filename

    def recognize(self):
        """
        This method is implemented to satisfy the BaseReader contract.
        File recognition logic is handled by other parts of the application.
        """

    def parse_audio(self, limit=None):
        """
        Reads any file supported by pydub (ffmpeg) and returns the data contained
        within.

        Can be optionally limited to a certain number of seconds from the start
        of the file by specifying the `limit` parameter.

        Args:
            limit (int, optional): The amount of seconds to read from the start of the file.
                                   Defaults to None, which reads the entire file.

        Returns:
            dict: A dictionary containing song properties and audio data, or an
                  empty dictionary if the file is unreadable.
        """
        songname, extension = os.path.splitext(os.path.basename(self.filename))

        try:
            audiofile = AudioSegment.from_file(self.filename)

            if limit:
                audiofile = audiofile[: limit * 1000]

            # Use the public API to get audio data as a numpy array
            data = np.array(audiofile.get_array_of_samples(), dtype=np.int16)

            # Use a list comprehension to extract channels
            channels = [
                data[chn :: audiofile.channels] for chn in range(audiofile.channels)
            ]

        except audioop.error:
            # pydub does not support 24-bit wav files, which can cause this error.
            print(
                f"pydub failed to read {self.filename}, likely a 24-bit WAV. Skipping."
            )
            return {}

        return {
            "songname": songname,
            "extension": extension,
            "channels": channels,
            "Fs": audiofile.frame_rate,
            "file_hash": self.parse_file_hash(),
            "metadata": self.get_song_tags(),
        }

    def parse_file_hash(self, blocksize=2**20):
        """
        Small function to generate a hash to uniquely identify a file.
        Inspired by MD5 version here:
        http://stackoverflow.com/a/1131255/712997

        Works with large files.

        Args:
            blocksize (int): The size of each chunk to read from the file.

        Returns:
            str: The uppercase hexadecimal hash of the file.
        """
        s = sha1()
        with open(self.filename, "rb") as f:
            while True:
                if buf := f.read(blocksize):
                    s.update(buf)
                else:
                    break
        return s.hexdigest().upper()

    def get_song_tags(self):
        """
        Extracts metadata tags from the audio file using TinyTag.

        Returns:
            dict: A dictionary of common metadata tags.
        """
        tag = TinyTag.get(self.filename)
        return {
            "title": tag.title,
            "artist": tag.artist,
            "album": tag.album,
            "genre": tag.genre,
            "duration": tag.duration,
            "track": tag.track,
        }
