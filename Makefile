.PHONY: tests

install:
	@echo soon

clean:
	@find . -name \*.pyc -delete

reset:
	@python reset_database.py

tests:
	@python tests/*.py

stat:
	@python get_database_stat.py

fingerprint-songs: clean
	@python collect_fingerprints_of_songs.py

fingerprint-songs-filter-duplicates: clean
	@python collect_fingerprints_of_songs.py  --signature-check Yes

recognize-listen: clean
	@python recognize_from_microphone.py -s $(seconds)

recognize-file: clean
	@python recognize_from_file.py
