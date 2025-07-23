"""
This module provides a MongoDB implementation of the Database base class.
It handles all direct interactions with a MongoDB server.
"""

from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from .config import get_config
from .db import Database


class MongoDatabase(Database):
    """
    MongoDB database adapter for storing and retrieving song and fingerprint data.
    """

    def __init__(self):
        """
        Initializes the MongoDatabase object and establishes a connection.
        """
        super().__init__()
        self.client = None
        self.db = None
        self.songs = None
        self.fingerprints = None
        self.connect()

    def connect(self):
        """
        Connects to the MongoDB server using credentials from the config file.
        """
        config = get_config()
        try:
            self._establish_connection(config)
        except ConnectionFailure as e:
            print(f"Could not connect to MongoDB: {e}")
            self.client = None
            self.db = None

    def _establish_connection(self, config):
        self.client = MongoClient(config["db.dsn"], serverSelectionTimeoutMS=5000)
        self.client.admin.command("ping")
        self.db = self.client[config["db.database"]]
        self.songs = self.db.songs
        self.fingerprints = self.db.fingerprints
        print("MongoDB connection successful.")

    def get_song_by_filehash(self, filehash):
        """Retrieves a song by its file hash."""
        return self.songs.find_one({"filehash": filehash})

    def get_song_by_id(self, song_id):
        """Retrieves a song by its unique ID."""
        return self.songs.find_one({"_id": ObjectId(song_id)})

    def get_song_by_tags(self, title, artist, album, genre, duration, track):
        """Retrieves a song by its metadata tags."""
        criteria = {}
        if title:
            criteria["title"] = title
        if artist:
            criteria["artist"] = artist
        return self.songs.find_one(criteria)

    def add_song(self, filename, filehash, metadata):
        """Adds a new song to the database if it doesn't already exist."""
        if song := self.get_song_by_filehash(filehash):
            return song["_id"]

        if song := self.get_song_by_tags(
            metadata.get("title"),
            metadata.get("artist"),
            metadata.get("album"),
            metadata.get("genre"),
            metadata.get("duration"),
            metadata.get("track"),
        ):
            return song["_id"]

        document = {
            "name": filename,
            "filehash": filehash,
            "title": metadata.get("title"),
            "artist": metadata.get("artist"),
            "album": metadata.get("album"),
            "genre": metadata.get("genre"),
            "track": metadata.get("track"),
            "duration": metadata.get("duration"),
        }
        return self.songs.insert_one(document).inserted_id

    def get_song_hashes_count(self, song_id):
        """Gets the total number of fingerprints for a given song."""
        return self.fingerprints.count_documents({"song_fk": ObjectId(song_id)})

    def store_fingerprints(self, values):
        """Inserts multiple fingerprint records into the database."""
        if documents := [
            {"song_fk": song_id, "hash": h, "offset": o} for song_id, h, o in values
        ]:
            self.fingerprints.insert_many(documents)
