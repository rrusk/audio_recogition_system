#!/usr/bin/python
import os
import sys
import libs
import libs.fingerprint as fingerprint
import argparse

from argparse import RawTextHelpFormatter
from itertools import zip_longest
from termcolor import colored
from libs.config import get_config
from libs.db_sqlite import SqliteDatabase
from libs.reader_file import FileReader  # Updated import for FileReader

def grouper(iterable, n, fillvalue=None):
    """Groups elements from iterable in chunks of size n."""
    args = [iter(iterable)] * n
    return (filter(None, values) for values in zip_longest(fillvalue=fillvalue, *args))

if __name__ == '__main__':
    config = get_config()
    db = SqliteDatabase()

    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
    parser.add_argument('-f', '--file', required=True, help="Path to the audio file")
    args = parser.parse_args()

    if not args.file:
        parser.print_help()
        sys.exit(0)

    file_path = args.file
    reader = FileReader(file_path)
    audio_data = reader.parse_audio()

    songname = audio_data['songname']
    channels = audio_data['channels']
    Fs = audio_data['Fs']

    msg = f" * loaded {len(channels[0])} samples from file '{file_path}'"
    print(colored(msg, attrs=['dark']))

    # Process fingerprint matching
    channel_amount = len(channels)
    matches = []

    def find_matches(samples, Fs):
        hashes = fingerprint.fingerprint(samples, Fs=Fs)
        return return_matches(hashes)

    def return_matches(hashes):
        mapper = {}
        for hash_val, offset in hashes:
            # Ensure hash_val is stored as a string and offset as an integer
            mapper[str(hash_val).upper()] = int(offset)
        values = mapper.keys()

        for split_values in grouper(values, 1000):
            split_values = list(split_values)  # Convert filter object to list
            query = """
                SELECT upper(hash), song_fk, offset
                FROM fingerprints
                WHERE upper(hash) IN (%s)
            """
            query = query % ', '.join('?' * len(split_values))

            x = db.executeAll(query, split_values)
            matches_found = len(x)

            if matches_found > 0:
                msg = '   ** found %d hash matches (step %d/%d)'
                print(colored(msg, 'green') % (
                    matches_found,
                    len(split_values),
                    len(values)
                ))
            else:
                msg = '   ** no matches found (step %d/%d)'
                print(colored(msg, 'red') % (
                    len(split_values),
                    len(values)
                ))

            for hash_val, sid, db_offset in x:
                # Decode db_offset if it's a byte string, then convert to int
                if isinstance(db_offset, bytes):
                    db_offset = int.from_bytes(db_offset, byteorder='little')
                else:
                    db_offset = int(db_offset)
                
                yield (sid, db_offset - mapper[str(hash_val)])

    for channeln, channel in enumerate(channels):
        msg = '   fingerprinting channel %d/%d'
        print(colored(msg, attrs=['dark']) % (channeln + 1, channel_amount))

        matches.extend(find_matches(channel, Fs))

        msg = '   finished channel %d/%d, got %d hashes'
        print(colored(msg, attrs=['dark']) % (
            channeln + 1, channel_amount, len(matches)
        ))

    def align_matches(matches):
        diff_counter = {}
        largest = 0
        largest_count = 0
        song_id = -1

        for tup in matches:
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

        songM = db.get_song_by_id(song_id)

        nseconds = round(float(largest) / fingerprint.DEFAULT_FS *
                         fingerprint.DEFAULT_WINDOW_SIZE *
                         fingerprint.DEFAULT_OVERLAP_RATIO, 5)

        return {
            "SONG_ID": song_id,
            "SONG_NAME": songM[1],
            "CONFIDENCE": largest_count,
            "OFFSET": int(largest),
            "OFFSET_SECS": nseconds
        }

    total_matches_found = len(matches)

    if total_matches_found > 0:
        msg = ' ** totally found %d hash matches'
        print(colored(msg, 'green') % total_matches_found)

        song = align_matches(matches)

        msg = ' => song: %s (id=%d)\n'
        msg += '    offset: %d (%d secs)\n'
        msg += '    confidence: %d'

        print(colored(msg, 'green') % (
            song['SONG_NAME'], song['SONG_ID'],
            song['OFFSET'], song['OFFSET_SECS'],
            song['CONFIDENCE']
        ))
    else:
        msg = ' ** no matches found at all'
        print(colored(msg, 'red'))
