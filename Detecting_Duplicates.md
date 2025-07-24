# Project Goal

The primary goal of this project is to create an audio fingerprinting system to identify and recognize songs. A key feature is its ability to detect and prevent the addition of duplicate songs into its database, even if the files have been modified (e.g., volume normalization), which would change their file hash.

## How It Works

1. **Database Setup**: The `reset-database.py` script, runnable via `make reset`, sets up a SQLite database with two main tables: `songs` and `fingerprints`.
2. **Fingerprinting Process**: The core logic resides in `collect-fingerprints-of-songs.py`. When run with the `--signature-check Yes` flag (as the `make fingerprint-songs-filter-duplicates` command does), it performs the following steps for each `.mp3` file in the `mp3/` directory:
    * It first checks if a song with the exact same file hash already exists in the database.
    * It then checks if a song with matching metadata (title, artist, album, etc.) already exists.
    * Crucially, it generates audio fingerprints of the current song and searches the database for similar fingerprints from other songs.
    * The `align_matches` function analyzes these matches to see if there's a high-confidence match with an existing song.
    * If a similar song is found through any of these checks, the current file is skipped, and not added to the database, preventing duplicates.
    * If the song is unique, its metadata and fingerprints are added to the database.
3. **Core Technology**:
    * **Audio Reading**: `reader_file.py` uses the `pydub` library to read audio data from files and `tinytag` to extract metadata like title, artist, and album.
    * **Fingerprinting**: `fingerprint.py` implements the audio fingerprinting algorithm. It uses a spectrogram to identify peaks in the audio's frequency and time, and then creates hashes based on pairs of these peaks. This method is robust against changes like volume normalization.
    * **Recognition**: The `recognize_from_file.py` script can take an audio file and use the fingerprinting database to identify the song.

In short, this is a comprehensive audio recognition system, similar in concept to Shazam, with a specific feature to ensure that the song library remains free of duplicates by checking not only file hashes but also audio metadata and the acoustic fingerprints themselves.
