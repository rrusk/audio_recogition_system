# Updates

- modifications for Python3 compatibility
- updates to add song metadata so song isn't added to the database again after mp3 normalization which will change the file hash
- updates to detect duplicated songs for the use case where one wants only distinct songs in a playlist

## Distinct song use case

1. Run `$make fingerprint_songs_filter_duplicates` to generate a database with distinct songs

## Original Readme from [audio_recognition_system](https://github.com/baliksjosay/audio_recogition_system)

### Fingerprint audio files & identify what's playing

- conference [PaceMaker: BackEnd-2016 conference](http://www.pacemaker.in.ua/BackEnd-2016/about)
- slides are on [slideshare.net/rodomansky/ok-shazam-la-lalalaa](http://www.slideshare.net/rodomansky/ok-shazam-la-lalalaa)

#### How to set up

1. Run `$ make clean reset` to clean & init database struct
1. Run `$ make tests` to make sure that everything is properly configurated
1. Copy some `.mp3` audio files into `mp3/` directory
1. Run `$ make fingerprint-songs` to analyze audio files & fill your db with hashes
1. Start play any of audio file (from any source) from `mp3/` directory, and run (parallely) `$ make recognize-listen seconds=5`

#### How to

- To remove a specific song & related hash from db

  ```bash
  $python sql-execute.py -q "DELETE FROM songs WHERE id = 6;"
  $python sql-execute.py -q "DELETE FROM fingerprints WHERE song_fk = 6;"
  ```

#### Thanks to

- [How does Shazam work](http://coding-geek.com/how-shazam-works/)
- [Audio fingerprinting and recognition in Python](https://github.com/worldveil/dejavu) - thanks for fingerprinting login via pynum
- [Audio Fingerprinting with Python and Numpy](http://willdrevo.com/fingerprinting-and-audio-recognition-with-python/)
- [Shazam It! Music Recognition Algorithms, Fingerprinting, and Processing](https://www.toptal.com/algorithms/shazam-it-music-processing-fingerprinting-and-recognition)
- [Creating Shazam in Java](http://royvanrijn.com/blog/2010/06/creating-shazam-in-java/)
