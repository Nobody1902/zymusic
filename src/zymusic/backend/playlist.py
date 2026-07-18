from zymusic.backend.song import Song


class Playlist:
    def __init__(self, title=None, description=None, browse_id=None, tracks=None,
                 thumbnails=None, owner=None, artist=None, year=None, track_count=None):
        self.title = title
        self.description = description
        self.browse_id = browse_id
        self.tracks = tracks or []
        self.thumbnails = thumbnails or []
        self.owner = owner
        self.artist = artist
        self.year = year
        self.track_count = track_count

    def __repr__(self):
        return f"Playlist(title={self.title!r}, tracks={len(self.tracks)})"

    def play(self, player, start_index=0):
        if not self.tracks or start_index >= len(self.tracks):
            return None
        player.clear_queue()
        for song in self.tracks:
            player.add_to_queue(song)
        return player.play_index(start_index)

    @classmethod
    def from_album(cls, data):
        thumbnails = data.get("thumbnails") or []
        artists = data.get("artists") or []
        tracks_data = data.get("tracks") or []
        return cls(
            title=data.get("title"),
            description=data.get("description"),
            browse_id=data.get("browseId"),
            tracks=[Song.from_watch_track(t) for t in tracks_data if isinstance(t, dict)],
            thumbnails=thumbnails[-1] if thumbnails else None,
            artist=artists[0].get("name") if artists else None,
            year=data.get("year"),
            track_count=data.get("trackCount"),
        )

    @classmethod
    def from_playlist(cls, data):
        thumbnails = data.get("thumbnails") or []
        tracks_data = data.get("tracks") or []
        return cls(
            title=data.get("title"),
            description=data.get("description"),
            browse_id=data.get("id") or data.get("browseId"),
            tracks=[Song.from_watch_track(t) for t in tracks_data if isinstance(t, dict)],
            thumbnails=thumbnails[-1] if thumbnails else None,
            owner=data.get("owner"),
            track_count=data.get("trackCount"),
        )

    @classmethod
    def from_watch_playlist(cls, data):
        tracks_data = data.get("tracks") or []
        return cls(
            tracks=[Song.from_watch_track(t) for t in tracks_data if isinstance(t, dict)],
        )

    @classmethod
    def from_search_tracks(cls, title, tracks_data):
        if all(isinstance(t, dict) for t in tracks_data):
            songs = [Song.from_search_result(t) for t in tracks_data]
        else:
            songs = [t for t in tracks_data if isinstance(t, Song)]
        return cls(title=title, tracks=songs)

    @property
    def duration(self):
        total = 0
        for s in self.tracks:
            if s.duration:
                total += s.duration if isinstance(s.duration, int) else 0
        return total
