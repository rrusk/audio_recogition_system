"""
Audio recognition script for matching audio samples to songs using fingerprints.

This module provides functions to group iterables, fingerprint audio samples,
find matches in a database, and align matches to identify the best matching song.
It can be run as a standalone script to recognize songs from an audio file.
"""

#!/usr/bin/python
import sys
import argparse
from argparse import RawTextHelpFormatter
from itertools import zip_longest

from termcolor import colored

from libs.config import get_config
from libs.db_sqlite import SqliteDatabase
from libs.reader_file import FileReader
import libs.fingerprint as fingerprint


def grouper(iterable, n, fillvalue=None):
    """Groups elements from iterable in chunks of size n."""
    iterators = [iter(iterable)] * n
    return (
        filter(None, values) for values in zip_longest(fillvalue=fillvalue, *iterators)
    )


def find_matches(samples, fs, db):
    """
    Finds fingerprint matches for the given audio samples.

    Args:
        samples (array-like): Audio samples to fingerprint.
        fs (int): Sample rate of the audio.
        db (SqliteDatabase): Database instance.

    Returns:
        generator: Yields tuples of (song_id, offset difference) for matches found in the database.
    """
    hashes = fingerprint.fingerprint(samples, fs=fs)
    return return_matches(hashes, db)


def return_matches(hashes, db):
    """
    Returns matches from the database for the given hashes.

    Args:
        hashes (list): List of (hash, offset) tuples.
        db (SqliteDatabase): Database instance.

    Yields:
        tuple: (song_id, offset difference)
    """
    mapper = {str(hash_val).upper(): int(offset) for hash_val, offset in hashes}
    values = mapper.keys()

    for split_values in grouper(values, 1000):
        split_values = list(split_values)  # Convert filter object to list
        query = (
            "SELECT upper(hash), song_fk, offset "
            "FROM fingerprints "
            "WHERE upper(hash) IN (%s)"
        )
        query %= ", ".join("?" * len(split_values))

        x = db.execute_all(query, split_values)
        matches_found = len(x)

        if matches_found > 0:
            local_msg = "   ** found %d hash matches (step %d/%d)"
            print(
                colored(local_msg, "green")
                % (matches_found, len(split_values), len(values))
            )
        else:
            local_msg = "   ** no matches found (step %d/%d)"
            print(colored(local_msg, "red") % (len(split_values), len(values)))

        for hash_val, sid, db_offset in x:
            # Decode db_offset if it's a byte string, then convert to int
            if isinstance(db_offset, bytes):
                db_offset = int.from_bytes(db_offset, byteorder="little")
            else:
                db_offset = int(db_offset)

            yield (sid, db_offset - mapper[str(hash_val)])


def align_matches(match_tuples, db):
    """
    Aligns matches to find the best matching song and offset.

    Args:
        match_tuples (iterable): Iterable of (song_id, offset difference) tuples.
        db (SqliteDatabase): Database instance.

    Returns:
        dict: Information about the best matching song.
    """
    diff_counter = {}
    largest = 0
    largest_count = 0
    song_id = -1

    for tup in match_tuples:
        sid, diff = tup

        if diff not in diff_counter:
            diff_counter[diff] = {}

        if sid not in diff_counter[diff]:
            diff_counter[diff][sid] = 0

        diff_counter[diff][sid] += 1

        if diff_counter[diff][sid] > largest_count:
            largest = diff
            largest_count = diff_counter[diff][sid]
            song_id = sid

    song_m = db.get_song_by_id(song_id)

    n_seconds = round(
        float(largest)
        / fingerprint.DEFAULT_FS
        * fingerprint.DEFAULT_WINDOW_SIZE
        * fingerprint.DEFAULT_OVERLAP_RATIO,
        5,
    )

    return {
        "SONG_ID": song_id,
        "SONG_NAME": song_m[1],
        "CONFIDENCE": largest_count,
        "OFFSET": int(largest),
        "OFFSET_SECS": n_seconds,
    }


if __name__ == "__main__":
    CONFIG = get_config()

    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
    parser.add_argument("-f", "--file", required=True, help="Path to the audio file")
    args = parser.parse_args()

    if not args.file:
        parser.print_help()
        sys.exit(0)

    FILE_PATH = args.file

    # Use a 'with' statement to manage the entire database session
    with SqliteDatabase() as DB:
        # All database-dependent code must be indented inside this block
        reader = FileReader(FILE_PATH)
        audio_data = reader.parse_audio()

        CHANNELS = audio_data["channels"]
        FS = audio_data["Fs"]
        MSG = f" * loaded {len(CHANNELS[0])} samples from file '{FILE_PATH}'"
        print(colored(MSG, attrs=["dark"]))

        # This loop must be inside the 'with' block to use the open connection
        matches = []
        for channeln, channel in enumerate(CHANNELS):
            MSG = "   fingerprinting channel %d/%d"
            print(colored(MSG, attrs=["dark"]) % (channeln + 1, len(CHANNELS)))

            matches.extend(find_matches(channel, FS, DB))

            MSG = "   finished channel %d/%d, got %d hashes"
            print(
                colored(MSG, attrs=["dark"])
                % (channeln + 1, len(CHANNELS), len(matches))
            )

        # Align matches and print the final result
        TOTAL_MATCHES_FOUND = len(matches)
        if TOTAL_MATCHES_FOUND > 0:
            MSG = " ** totally found %d hash matches"
            print(colored(MSG, "green") % TOTAL_MATCHES_FOUND)

            if song := align_matches(matches, DB):
                MSG = (
                    " => song: %s (id=%d)\n    offset: %d (%d secs)\n    confidence: %d"
                )
                print(
                    colored(MSG, "green")
                    % (
                        song["SONG_NAME"],
                        song["SONG_ID"],
                        song["OFFSET"],
                        song["OFFSET_SECS"],
                        song["CONFIDENCE"],
                    )
                )
            else:
                MSG = " ** no matches found in alignment"
                print(colored(MSG, "red"))
        else:
            MSG = " ** no matches found at all"
            print(colored(MSG, "red"))
