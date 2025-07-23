"""
This module provides a concrete SQLite implementation of the Database base class.
It handles all direct interactions with the SQLite database file.
"""

import logging
import sqlite3

from .config import get_config
from .db import Database
from .utils import grouper

log = logging.getLogger(__name__)


class SqliteDatabase(Database):
    """
    SQLite database adapter for storing and retrieving song and fingerprint data.

    This class provides a context manager for handling database connections
    and implements the methods defined in the Database base class.
    """

    TABLE_SONGS = "songs"
    TABLE_FINGERPRINTS = "fingerprints"

    def __init__(self, db_path=None):
        """
        Initializes the database object.
        Uses a provided path for testing or gets it from config for production.
        """
        super().__init__()
        if db_path:
            self.db_path = db_path  # Use provided path for tests
        else:
            config = get_config()
            self.db_path = config["db.file"]  # Use config path for normal operation

        self.conn = None
        self.cur = None

    def __enter__(self):
        """Opens the database connection when entering a 'with' block."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.text_factory = str
        self.cur = self.conn.cursor()
        log.info("sqlite - connection opened")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Commits changes and closes the connection when exiting a 'with' block."""
        if self.conn:
            self.conn.commit()
            self.conn.close()
            log.info("sqlite - connection has been closed")

    # ----------------------------------------------------------------
    # Low-level cursor execution methods
    # ----------------------------------------------------------------

    def query(self, query_string, values=None):
        """Executes a query that doesn't return a value (e.g., DROP, CREATE)."""
        if values is None:
            values = []
        self.cur.execute(query_string, values)
        self.conn.commit()

    def execute_one(self, query, values=None):
        """Executes a query and returns the first result."""
        if values is None:
            values = []
        self.cur.execute(query, values)
        return self.cur.fetchone()

    def execute_all(self, query, values=None):
        """Executes a query and returns all results."""
        if values is None:
            values = []
        self.cur.execute(query, values)
        return self.cur.fetchall()

    def insert(self, table, params):
        """Inserts a single record into a table."""
        keys = ", ".join(params.keys())
        values = list(params.values())
        placeholders = ", ".join(["?"] * len(values))
        query = f"INSERT INTO {table} ({keys}) VALUES ({placeholders})"
        self.cur.execute(query, values)
        self.conn.commit()
        return self.cur.lastrowid

    # ----------------------------------------------------------------
    # High-level implementation of abstract methods
    # ----------------------------------------------------------------

    def get_song_by_filehash(self, filehash):
        """Retrieves a song by its file hash."""
        return self.execute_one(
            f"SELECT * FROM {self.TABLE_SONGS} WHERE filehash = ?", [filehash]
        )

    def get_song_by_id(self, song_id):
        """Retrieves a song by its unique ID."""
        return self.execute_one(
            f"SELECT * FROM {self.TABLE_SONGS} WHERE id = ?", [song_id]
        )

    def get_song_by_tags(self, title, artist, album, genre, duration, track):
        """Retrieves a song by its metadata tags."""
        criteria = {}
        if title:
            criteria["title"] = title
        if artist:
            criteria["artist"] = artist
        if album:
            criteria["album"] = album
        if genre:
            criteria["genre"] = genre
        if duration:
            criteria["duration"] = round(duration, 1)
        if track:
            criteria["track"] = track

        if not criteria:
            return None

        conditions = " AND ".join(f"{key} = ?" for key in criteria)
        values = list(criteria.values())
        query = f"SELECT * FROM {self.TABLE_SONGS} WHERE {conditions}"

        return self.execute_one(query, values)

    def add_song(self, filename, filehash, metadata):
        """Adds a new song to the database if it doesn't already exist."""
        # First, try to find the song by its unique hash
        song = self.get_song_by_filehash(filehash)
        if song:
            return song[0]  # Return existing song ID

        # If not found by hash, try to find it by metadata tags.
        song = self.get_song_by_tags(
            metadata.get("title"),
            metadata.get("artist"),
            metadata.get("album"),
            metadata.get("genre"),
            metadata.get("duration"),
            metadata.get("track"),
        )
        if song:
            return song[0]  # Return existing song ID

        # If it's truly a new song, insert it
        return self.insert(
            self.TABLE_SONGS,
            {
                "name": filename,
                "filehash": filehash,
                "title": metadata.get("title"),
                "artist": metadata.get("artist"),
                "album": metadata.get("album"),
                "genre": metadata.get("genre"),
                "track": metadata.get("track"),
                "duration": round(metadata.get("duration", 0), 1),
            },
        )

    def get_song_hashes_count(self, song_id):
        """Gets the total number of fingerprints for a given song."""
        query = f"SELECT count(*) FROM {self.TABLE_FINGERPRINTS} WHERE song_fk = ?"
        rows = self.execute_one(query, [song_id])
        return int(rows[0]) if rows else 0

    def store_fingerprints(self, values):
        """Inserts multiple fingerprint records into the database."""
        for split_values in grouper(values, 1000):
            filtered_values = list(split_values)
            if not filtered_values:
                continue

            query = (
                f"INSERT OR IGNORE INTO {self.TABLE_FINGERPRINTS} "
                "(song_fk, hash, offset) VALUES (?, ?, ?)"
            )
            self.cur.executemany(query, filtered_values)
        self.conn.commit()
