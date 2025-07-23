#!/usr/bin/python
"""
This script collects audio fingerprints from .mp3 files in a specified
directory and stores them in a database. It includes functionality to detect
and skip duplicate songs based on file hash, metadata, or audio signature
to maintain a clean song library.
"""
import os
import argparse
import logging

from termcolor import colored

from libs.reader_file import FileReader
from libs.db_sqlite import SqliteDatabase
from libs.config import get_config
from libs.utils import grouper
import libs.fingerprint as fingerprint

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Collect fingerprints of songs.")
    parser.add_argument(
        "--signature-check",
        default="No",
        choices=["Yes", "No"],
        help="Enable signature check to find acoustically similar songs (default: No)",
    )
    return parser.parse_args()


def find_matches(samples, fs, database, channel_hashes=None):
    """Finds matches of the provided samples against the database."""
    # Use channel_hashes if provided, otherwise calculate them
    hashes_to_match = (
        channel_hashes
        if channel_hashes is not None
        else list(fingerprint.fingerprint(samples, fs=fs))
    )
    return return_matches(hashes_to_match, database)


def return_matches(hashes, database):
    """Returns matches for the provided hashes."""
    mapper = {str(hash_val).upper(): offset for hash_val, offset in hashes}
    values = mapper.keys()

    for value_chunk in grouper(values, 1000):
        # Convert the filter object from grouper into a list
        split_values = list(value_chunk)

        # Skip empty chunks
        if not split_values:
            continue

        query = """
            SELECT upper(hash), song_fk, offset
            FROM fingerprints
            WHERE upper(hash) IN (%s)
        """
        query %= ", ".join("?" * len(split_values))

        db_results = database.execute_all(query, split_values)
        for hash_val, sid, db_offset in db_results:
            offset_diff = (
                int.from_bytes(db_offset, byteorder="little")
                if isinstance(db_offset, bytes)
                else int(db_offset)
            )
            yield (sid, offset_diff - mapper[str(hash_val)])


def align_matches(matches, database):
    """
    Aligns matches and determines if a high-confidence match exists.
    Returns the matched song and the confidence score.
    """
    diff_counter = {}
    largest_count = 0
    song_id = -1

    for sid, diff in matches:
        diff_counter.setdefault(diff, {})
        diff_counter[diff].setdefault(sid, 0)
        diff_counter[diff][sid] += 1

        if diff_counter[diff][sid] > largest_count:
            largest_count = diff_counter[diff][sid]
            song_id = sid

    if largest_count >= 1000:
        song = database.get_song_by_id(song_id)
        return song, largest_count

    return None, 0


def fingerprint_song(audio, database, check_signature):
    """Fingerprints a single song and stores it in the database."""
    # Check if song is already in the database by hash or metadata
    if song_by_hash := database.get_song_by_filehash(audio["file_hash"]):
        logging.warning(
            "Skipping '%s' (already in DB with hash for song: %s)",
            audio["songname"],
            song_by_hash[1],
        )
        return

    tag = audio["metadata"]
    if tag.get("title"):
        if song_by_tags := database.get_song_by_tags(
            tag["title"],
            tag.get("artist"),
            tag.get("album"),
            tag.get("genre"),
            tag.get("duration"),
            tag.get("track"),
        ):
            logging.warning(
                "Skipping '%s' (metadata matches existing song: '%s')",
                audio["songname"],
                song_by_tags[1],
            )
            return

    # Generate audio fingerprints
    all_channel_hashes = set()
    found_matches = []

    for channel in audio["channels"]:
        channel_hashes = list(fingerprint.fingerprint(channel, fs=audio["Fs"]))
        all_channel_hashes.update(channel_hashes)

        # If signature check is enabled, find matches for the current channel
        if check_signature == "Yes":
            found_matches.extend(
                find_matches(channel, audio["Fs"], database, channel_hashes)
            )

    # If checking signatures, align matches to see if the song is a duplicate
    if check_signature == "Yes":
        matched_song, confidence = align_matches(found_matches, database)
        if matched_song:
            logging.warning(
                "Skipping '%s', determined to be a duplicate of '%s' (confidence: %d)",
                audio["songname"],
                matched_song[1],
                confidence,
            )
            return

    # Add new song and its fingerprints to the database
    song_id = database.add_song(audio["songname"], audio["file_hash"], tag)
    logging.info(
        "id=%s: %s",
        song_id,
        colored(audio["songname"], "white", attrs=["bold"]),
    )

    fingerprint_values = [(song_id, h, o) for h, o in all_channel_hashes]
    logging.info(
        "Storing %d hashes for '%s'",
        len(fingerprint_values),
        audio["songname"],
    )
    database.store_fingerprints(fingerprint_values)


def main():
    """Main function to run the fingerprinting process."""
    arguments = parse_arguments()
    config = get_config()
    mp3_directory = config.get("mp3_dir", "mp3/")

    with SqliteDatabase() as database:
        for filename in os.listdir(mp3_directory):
            if filename.endswith(".mp3"):
                try:
                    file_path = os.path.join(mp3_directory, filename)
                    reader = FileReader(file_path)
                    if audio_data := reader.parse_audio():
                        fingerprint_song(
                            audio_data, database, arguments.signature_check
                        )
                except (IOError, ValueError) as e:
                    logging.error("Error processing %s: %s", filename, e)

    logging.info("--- End of fingerprinting process ---")


if __name__ == "__main__":
    main()
