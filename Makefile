.PHONY: tests

install:
	@echo Not Implemented

clean:
	@find . -name \*.pyc -delete

reset:
	@python reset_database.py

tests:
	@python -m unittest discover tests/

stat:
	@python get_database_stat.py

fingerprint-songs: clean
	@python collect_fingerprints_of_songs.py

fingerprint-songs-filter-duplicates: clean
	@python collect_fingerprints_of_songs.py  --signature-check Yes

recognize-listen: clean
	@python recognize_from_microphone.py -s $(seconds)

# make recognize-file file="mp3/your_song.mp3"
recognize-file: clean
	@python recognize_from_file.py -f $(file)
