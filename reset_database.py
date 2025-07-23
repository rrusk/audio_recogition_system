#!/usr/bin/python
"""
This script resets the SQLite database by dropping and recreating the
'songs' and 'fingerprints' tables.
"""
from libs.db_sqlite import SqliteDatabase

if __name__ == "__main__":
    with SqliteDatabase() as db:
        print("Dropping existing tables...")
        db.query("DROP TABLE IF EXISTS songs;")
        db.query("DROP TABLE IF EXISTS fingerprints;")

        print("Creating new 'songs' table...")
        db.query("""
            CREATE TABLE songs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT,
              filehash TEXT,
              title TEXT,
              artist TEXT,
              album TEXT,
              genre TEXT,
              track INT,
              duration INT
            );
        """)

        print("Creating new 'fingerprints' table...")
        db.query("""
            CREATE TABLE fingerprints (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              song_fk INTEGER,
              hash TEXT,
              offset INTEGER
            );
        """)

        print("Database has been reset successfully.")
