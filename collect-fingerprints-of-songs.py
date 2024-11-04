#!/usr/bin/python
import os
import sys
import argparse
from termcolor import colored
from libs.reader_file import FileReader
from libs.db_sqlite import SqliteDatabase
from libs.config import get_config
from itertools import zip_longest
from tinytag import TinyTag
import libs.fingerprint as fingerprint


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Collect fingerprints of songs.")
    parser.add_argument("--signature-check", default="No", choices=["Yes", "No"],
                        help="Enable signature check (default: No)")
    return parser.parse_args()


def find_matches(samples, Fs, db, precomputed_hashes=None):
    """Finds matches of the provided samples against the database."""
    # Use precomputed hashes if provided, otherwise calculate them
    hashes = precomputed_hashes if precomputed_hashes !=[] else fingerprint.fingerprint(samples, Fs=Fs)
    return return_matches(hashes, db)


def return_matches(hashes, db):
    """Returns matches for the provided hashes."""
    mapper = {}
    for hash_val, offset in hashes:
        mapper[str(hash_val).upper()] = offset
    values = mapper.keys()

    for split_values in grouper(values, 1000):
        split_values = list(split_values)
        query = """
            SELECT upper(hash), song_fk, offset
            FROM fingerprints
            WHERE upper(hash) IN (%s)
        """
        query = query % ', '.join('?' * len(split_values))

        x = db.executeAll(query, split_values)
        for hash_val, sid, db_offset in x:
            if isinstance(db_offset, bytes):
                db_offset = int.from_bytes(db_offset, byteorder='little')
            else:
                db_offset = int(db_offset)
            yield (sid, db_offset - mapper[str(hash_val)])

def align_matches(matches, db):
    """Aligns matches and determines if a high-confidence match exists."""
    diff_counter = {}
    largest_count = 0
    song_id = -1

    for sid, diff in matches:
        if diff not in diff_counter:
            diff_counter[diff] = {}

        if sid not in diff_counter[diff]:
            diff_counter[diff][sid] = 0

        diff_counter[diff][sid] += 1

        if diff_counter[diff][sid] > largest_count:
            largest_count = diff_counter[diff][sid]
            song_id = sid

    if largest_count >= 1000:  # Confidence threshold to avoid adding duplicates
        return song_id
    return None

def grouper(iterable, n, fillvalue=None):
    """Groups elements from iterable in chunks of size n."""
    args = [iter(iterable)] * n
    return (filter(None, values) for values in zip_longest(fillvalue=fillvalue, *args))

if __name__ == '__main__':
    args = parse_arguments()
    config = get_config()
    db = SqliteDatabase()
    path = "mp3/"

    # Fingerprint all files in the directory
    for filename in os.listdir(path):
        if filename.endswith(".mp3"):
            reader = FileReader(path + filename)
            audio = reader.parse_audio()

            song = db.get_song_by_filehash(audio['file_hash'])
            if song:
                print(colored(f" * Skipping '{filename}' (already in DB)", 'red'))
                continue
            
            # to avoid doing a match on re-normalized files,
            # see if the files metadata matches a song in the database
            tag = audio['metadata']
            title = tag["title"]
            if title:
                song = db.get_song_by_tags(title, tag["artist"], tag["album"], tag["genre"], tag["duration"], tag["track"])
                if song:
                    print(colored(f" * Skipping '{filename}' (with metadata matching '{song[1]}')", 'red'))
                    continue

            # If signature check is enabled, compute fingerprints once per channel
            hashes = set()
            if args.signature_check == "Yes":
                matches = []
                for channeln, channel in enumerate(audio['channels']):
                    channel_hashes = fingerprint.fingerprint(channel, Fs=audio['Fs'], plots=config['fingerprint.show_plots'])
                    hashes |= set(channel_hashes)
                for channel in audio['channels']:
                    matches.extend(find_matches(channel, audio['Fs'], db, precomputed_hashes=channel_hashes))

                # If a match with high confidence is found, skip adding this song
                matched_song_id = align_matches(matches, db)
                if matched_song_id:
                    matched_song = db.get_song_by_id(matched_song_id)
                    print(colored(f" * Skipping '{filename}', similar to '{matched_song[1]}'", 'red'))
                    continue

            # Add new song to the database
            song_id = db.add_song(filename, audio['file_hash'], audio['metadata'])
            msg = f" * {colored('id=%s', 'white', attrs=['dark'])}: {colored('%s', 'white', attrs=['bold'])}" % (song_id, filename)
            print(msg)

            # If not previously computed, compute fingerprints for storage
            if not hashes:
                for channeln, channel in enumerate(audio['channels']):
                    channel_hashes = fingerprint.fingerprint(channel, Fs=audio['Fs'], plots=config['fingerprint.show_plots'])
                    hashes |= set(channel_hashes)
            
            # Store unique hashes in the database
            values = [(song_id, hash, offset) for hash, offset in hashes]
            print(colored(f"   Storing {len(values)} hashes for '{filename}'", 'green'))
            db.store_fingerprints(values)

    print('End of fingerprinting process')
