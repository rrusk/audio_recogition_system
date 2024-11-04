import sys

class Database(object):
  TABLE_SONGS = None
  TABLE_FINGERPRINTS = None

  def __init__(self, a):
    self.a = a

  def connect(self): pass
  def insert(self, table, params): pass

  def get_song_by_filehash(self, filehash):
    return self.findOne(self.TABLE_SONGS, {
      "filehash": filehash
    })

  def get_song_by_id(self, id):
    return self.findOne(self.TABLE_SONGS, {
      "id": id
    })
    

  def get_song_by_tags(self, title, artist, album, genre, duration, track):
    # Start with an empty dictionary for search criteria
    criteria = {}

    # Add only non-None values to criteria
    if title is not None:
        criteria['title'] = title
    if artist is not None:
        criteria['artist'] = artist
    if album is not None:
        criteria['album'] = album
    if genre is not None:
        criteria['genre'] = genre
    if duration is not None:
        criteria['duration'] = duration
    if track is not None:
        criteria['track'] = track

    # Use the populated criteria dictionary in the search
    return self.findOne(self.TABLE_SONGS, criteria)


  def add_song(self, filename, filehash, metadata):
    song = self.get_song_by_filehash(filehash)
    if not song:
      self.get_song_by_tags(metadata['title'], metadata['artist'], metadata['album'], metadata['genre'], metadata['duration'], metadata['track'])
    if not song:
      song_id = self.insert(self.TABLE_SONGS, {
        "name": filename,
        "filehash": filehash,
        "title": metadata['title'],
        "artist": metadata['artist'],
        "album": metadata['album'],
        "genre": metadata['genre'],
        "track": metadata['track'],
        "duration": round(metadata['duration'],1)
      })
    else:
      song_id = song[0]

    return song_id

  def get_song_hashes_count(self, song_id):
    pass

  def store_fingerprints(self, values):
    self.insertMany(self.TABLE_FINGERPRINTS,
      ['song_fk', 'hash', 'offset'], values
    )
