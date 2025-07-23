"""
This module provides a base class for database operations.
Subclasses should implement the methods defined here to provide
concrete functionality for a specific database system.
"""


class Database:
    """
    Base class for a database interface.
    It defines the common methods that any database adapter should implement.
    """

    TABLE_SONGS = None
    TABLE_FINGERPRINTS = None

    def __init__(self):
        """Initializes the base database class."""

    def get_song_by_filehash(self, filehash):
        """
        Retrieves a song by its file hash.

        Args:
            filehash (str): The hash of the file to find.
        """
        raise NotImplementedError

    def get_song_by_id(self, song_id):
        """
        Retrieves a song by its unique ID.

        Args:
            song_id (int): The ID of the song to retrieve.
        """
        raise NotImplementedError

    def get_song_by_tags(self, title, artist, album, genre, duration, track):
        """
        Retrieves a song by its metadata tags.

        Args:
            title (str): The title of the song.
            artist (str): The artist of the song.
            album (str): The album of the song.
            genre (str): The genre of the song.
            duration (float): The duration of the song in seconds.
            track (int): The track number of the song.
        """
        raise NotImplementedError

    def add_song(self, filename, filehash, metadata):
        """
        Adds a new song to the database if it doesn't already exist.

        Args:
            filename (str): The name of the song file.
            filehash (str): The hash of the file.
            metadata (dict): A dictionary of song metadata.

        Returns:
            int: The ID of the song (either new or existing).
        """
        raise NotImplementedError

    def get_song_hashes_count(self, song_id):
        """
        Gets the total number of fingerprints for a given song.

        Args:
            song_id (int): The ID of the song.
        """
        raise NotImplementedError

    def store_fingerprints(self, values):
        """
        Inserts multiple fingerprint records into the database.

        Args:
            values (list): A list of tuples with fingerprint data to insert.
        """
        raise NotImplementedError
