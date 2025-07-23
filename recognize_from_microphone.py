#!/usr/bin/env python3
"""
This script captures audio from a microphone for a specified duration,
generates audio fingerprints, and attempts to recognize the song by
matching the fingerprints against a database.
"""
import argparse
from argparse import RawTextHelpFormatter

from termcolor import colored

from libs.config import get_config
from libs.db_sqlite import SqliteDatabase
import libs.fingerprint as fingerprint
from libs.reader_microphone import MicrophoneReader
from libs.utils import grouper
from libs.visualiser_console import VisualiserConsole as visual_peak
from libs.visualiser_plot import VisualiserPlot as visual_plot


def find_matches(db_conn, samples, fs=fingerprint.DEFAULT_FS):
    """
    Generates fingerprints for audio samples and queries the database for matches.

    Args:
        db_conn (SqliteDatabase): An active database connection.
        samples (np.array): A numpy array of audio samples.
        fs (int): The sample rate of the audio.

    Yields:
        tuple: A tuple of (song_id, offset_difference) for each match found.
    """
    hashes = fingerprint.fingerprint(samples, fs=fs)
    return return_matches(db_conn, hashes)


def return_matches(db_conn, hashes):
    """
    Looks up a list of hashes in the database.

    Args:
        db_conn (SqliteDatabase): An active database connection.
        hashes (list): A list of (hash, offset) tuples.

    Yields:
        tuple: A tuple of (song_id, offset_difference) for each match found.
    """
    # Create a mapping of hash -> offset
    mapper = {fp_hash.upper(): offset for fp_hash, offset in hashes}
    values = list(mapper.keys())

    for split_values in grouper(values, 1000):
        query = """
            SELECT upper(hash), song_fk, offset
            FROM fingerprints
            WHERE upper(hash) IN (%s)
        """
        # Create a string of '?' placeholders for the query
        placeholders = ", ".join("?" * len(split_values))
        query %= placeholders

        db_matches = db_conn.execute_all(query, split_values)
        matches_found = len(db_matches)

        if matches_found > 0:
            msg = f"   ** found {matches_found} hash matches"
            print(colored(f"{msg} (step {len(split_values)}/{len(values)})", "green"))
        else:
            msg = f"   ** no matches found (step {len(split_values)}/{len(values)})"
            print(colored(msg, "red"))

        for fp_hash, sid, offset in db_matches:
            # Return (song_id, database_offset - microphone_sample_offset)
            yield (sid, offset - mapper[fp_hash])


def align_matches(db_conn, matches):
    """
    Calculates the most likely song match from a list of hash matches.

    Args:
        db_conn (SqliteDatabase): An active database connection.
        matches (list): A list of (song_id, offset_difference) tuples.

    Returns:
        dict: A dictionary containing the recognized song's information.
    """
    diff_counter = {}
    largest_count = 0
    song_id = -1
    largest_offset = 0  # Initialize to handle case with no matches

    for sid, diff in matches:
        if diff not in diff_counter:
            diff_counter[diff] = {}
        if sid not in diff_counter[diff]:
            diff_counter[diff][sid] = 0
        diff_counter[diff][sid] += 1

        if diff_counter[diff][sid] > largest_count:
            largest_offset = diff
            largest_count = diff_counter[diff][sid]
            song_id = sid

    song_match_data = db_conn.get_song_by_id(song_id)

    nseconds = round(
        float(largest_offset)
        / fingerprint.DEFAULT_FS
        * fingerprint.DEFAULT_WINDOW_SIZE
        * fingerprint.DEFAULT_OVERLAP_RATIO,
        5,
    )

    return {
        "SONG_ID": song_id,
        "SONG_NAME": song_match_data[1] if song_match_data else "Unknown",
        "CONFIDENCE": largest_count,
        "OFFSET": int(largest_offset),
        "OFFSET_SECS": nseconds,
    }


def main():
    """The main function to run the recognition process."""
    config = get_config()
    db_conn = SqliteDatabase()

    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
    parser.add_argument(
        "-s", "--seconds", nargs="?", default=10, help="Number of seconds to record."
    )
    args = parser.parse_args()
    seconds_to_record = int(args.seconds)

    # Configure audio recording settings
    CHUNK_SIZE = 2**12  # 4096 # pylint: disable=invalid-name
    CHANNELS = 2  # pylint: disable=invalid-name
    RECORD_FOREVER = False  # pylint: disable=invalid-name
    VISUALISE_CONSOLE = bool(config["mic.visualise_console"])  # pylint: disable=invalid-name
    VISUALISE_PLOT = bool(config["mic.visualise_plot"])  # pylint: disable=invalid-name

    reader = MicrophoneReader(None)
    reader.start_recording(
        seconds=seconds_to_record, chunksize=CHUNK_SIZE, channels=CHANNELS
    )

    print(colored(" * started recording..", attrs=["dark"]))

    # This loop is designed for continuous recording, but we break after one pass.
    while True:
        buffer_size = int(reader.rate / reader.chunksize * seconds_to_record)
        for i in range(buffer_size):
            nums = reader.process_recording()
            if VISUALISE_CONSOLE:
                msg = colored(f"   {i:05d}", attrs=["dark"]) + colored(
                    f" {visual_peak.calc(nums)}", "green"
                )
                print(msg)
            else:
                msg = f"   processing {i+1} of {buffer_size}.."
                print(colored(msg, attrs=["dark"]))

        if not RECORD_FOREVER:
            break

    reader.stop_recording()
    print(colored(" * recording has been stopped", attrs=["dark"]))

    if VISUALISE_PLOT:
        data = reader.get_recorded_data()[0]
        visual_plot.show(data)

    data = reader.get_recorded_data()
    print(colored(f" * recorded {len(data[0])} samples", attrs=["dark"]))

    matches = []
    channel_amount = len(data)

    for channel_num, channel_samples in enumerate(data):
        msg = f"   fingerprinting channel {channel_num + 1}/{channel_amount}"
        print(colored(msg, attrs=["dark"]))

        matches.extend(find_matches(db_conn, channel_samples))

        msg = f"   finished channel {channel_num + 1}/{channel_amount}, "
        msg += f"got {len(matches)} total matches"
        print(colored(msg, attrs=["dark"]))

    total_matches_found = len(matches)
    print("")

    if total_matches_found > 0:
        msg = f" ** totally found {total_matches_found} hash matches"
        print(colored(msg, "green"))

        song = align_matches(db_conn, matches)

        msg = (
            f" => song: {song['SONG_NAME']} (id={song['SONG_ID']})\n"
            f"    offset: {song['OFFSET']} ({song['OFFSET_SECS']} secs)\n"
            f"    confidence: {song['CONFIDENCE']}"
        )
        print(colored(msg, "green"))
    else:
        print(colored(" ** no matches found at all", "red"))


if __name__ == "__main__":
    main()
