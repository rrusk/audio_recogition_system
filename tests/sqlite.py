"""Tests for the SQLite database functionality."""

import sys
import os
import unittest
from libs.db_sqlite import SqliteDatabase

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


class TestSqliteDatabase(unittest.TestCase):
    """Test suite for the SqliteDatabase class."""

    TEST_DB_PATH = ":memory:"

    def create_schema(self, db):
        """Helper function to create the necessary tables."""
        db.query(
            """
            CREATE TABLE songs (
              id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, filehash TEXT,
              title TEXT, artist TEXT, album TEXT, genre TEXT, track INT,
              duration INT
            );
        """
        )
        db.query(
            """
            CREATE TABLE fingerprints (
              id INTEGER PRIMARY KEY AUTOINCREMENT, song_fk INTEGER,
              hash TEXT, offset INTEGER
            );
        """
        )

    def test_add_and_get_song(self):
        """Test that a song can be added and retrieved correctly."""
        with SqliteDatabase(db_path=self.TEST_DB_PATH) as db:
            self.create_schema(db)

            filename = "test_song.mp3"
            filehash = "test_hash_123"
            metadata = {"title": "Test Title", "artist": "Test Artist"}

            song_id = db.add_song(filename, filehash, metadata)
            self.assertEqual(song_id, 1)

            retrieved_song = db.get_song_by_id(song_id)
            self.assertIsNotNone(retrieved_song)
            self.assertEqual(retrieved_song[1], filename)

    def test_get_non_existent_song(self):
        """Test that querying for a non-existent song returns None."""
        with SqliteDatabase(db_path=self.TEST_DB_PATH) as db:
            self.create_schema(db)
            retrieved_song = db.get_song_by_id(999)
            self.assertIsNone(retrieved_song)

    def test_store_and_count_fingerprints(self):
        """Test that fingerprints can be stored and counted for a song."""
        with SqliteDatabase(db_path=self.TEST_DB_PATH) as db:
            self.create_schema(db)
            song_id = db.add_song("test.mp3", "hash1", {})
            self.assertEqual(song_id, 1)

            fingerprints = [
                (song_id, "fp_hash_1", 12),
                (song_id, "fp_hash_2", 15),
            ]
            db.store_fingerprints(fingerprints)

            count = db.get_song_hashes_count(song_id)
            self.assertEqual(count, 2)


if __name__ == "__main__":
    unittest.main()
