#!/usr/bin/env python3
"""
Provides a command-line utility to display statistics about the audio database,
including song counts, fingerprint counts, duplicates, and hash collisions.
"""

from termcolor import colored
from libs.db_sqlite import SqliteDatabase


def print_summary(db_conn):
    """
    Prints a summary of the total number of songs and fingerprints.

    Args:
        db_conn (SqliteDatabase): An active database connection object.

    Returns:
        int: The total count of songs in the database.
    """
    query = """
        SELECT
            (SELECT COUNT(*) FROM songs),
            (SELECT COUNT(*) FROM fingerprints)
    """
    songs_count, fingerprints_count = db_conn.execute_one(query)

    songs_colored = colored(f"{songs_count} song(s)", "yellow")
    fingerprints_colored = colored(f"{fingerprints_count} fingerprint(s)", "yellow")
    total_colored = colored("total", "yellow")

    print(f" * {total_colored}: {songs_colored} ({fingerprints_colored})")

    return songs_count


def print_songs(db_conn):
    """
    Prints a list of all songs, ordered by the number of fingerprints they have.

    Args:
        db_conn (SqliteDatabase): An active database connection object.
    """
    query = """
        SELECT
            s.id,
            s.name,
            (SELECT count(f.id) FROM fingerprints AS f WHERE f.song_fk = s.id) AS fingerprints_count
        FROM songs AS s
        ORDER BY fingerprints_count DESC
    """
    rows = db_conn.execute_all(query)

    for song_id, name, hashes_count in rows:
        id_colored = colored(f"id={song_id}", "white", attrs=["dark"])
        name_colored = colored(name, "white", attrs=["bold"])
        hashes_colored = colored(f"{hashes_count} hashes", "green")
        print(f"   ** {id_colored} {name_colored}: {hashes_colored}")


def print_duplicates(db_conn):
    """
    Finds and prints songs that have duplicate fingerprints.

    Args:
        db_conn (SqliteDatabase): An active database connection object.
    """
    query = """
        SELECT a.song_fk, s.name, SUM(a.cnt)
        FROM (
            SELECT song_fk, COUNT(*) cnt
            FROM fingerprints
            GROUP BY hash, song_fk, offset
            HAVING cnt > 1
            ORDER BY cnt ASC
        ) a
        JOIN songs s ON s.id = a.song_fk
        GROUP BY a.song_fk
    """
    rows = db_conn.execute_all(query)

    duplications_colored = colored(f"{len(rows)} song(s)", "yellow")
    print(f" * duplications: {duplications_colored}")

    for song_id, name, duplicate_count in rows:
        id_colored = colored(f"id={song_id}", "white", attrs=["dark"])
        name_colored = colored(name, "white", attrs=["bold"])
        duplicates_colored = colored(f"{duplicate_count} duplicate(s)", "red")
        print(f"   ** {id_colored} {name_colored}: {duplicates_colored}")


def print_collisions(db_conn):
    """
    Finds and prints the total number of hash collisions.

    Args:
        db_conn (SqliteDatabase): An active database connection object.
    """
    query = """
        SELECT sum(a.n) FROM (
            SELECT
                hash,
                count(distinct song_fk) AS n
            FROM fingerprints
            GROUP BY `hash`
            HAVING n > 1
            ORDER BY n DESC
        ) a
    """
    rows = db_conn.execute_all(query)

    # Use a more direct way to get the collision value or default to 0
    val = rows[0][0] if rows and rows[0] and rows[0][0] is not None else 0

    collisions_colored = colored(f"{val} hash(es)", "red")
    print(f" * collisions: {collisions_colored}")


if __name__ == "__main__":
    with SqliteDatabase() as db:
        print("")

        song_count = print_summary(db)
        print_songs(db)
        if song_count:
            print("")

        print_duplicates(db)
        if song_count:
            print("")

        print_collisions(db)

        print("\ndone")
