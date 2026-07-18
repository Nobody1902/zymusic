from typing import Any


class Song:
    title: str
    artist: str
    video_id: str
    album: str | None
    duration: int | None
    thumbnail: str | None
    artist_id: str | None
    album_id: str | None
    is_explicit: bool
    feedback_tokens: dict[str, Any]

    def __init__(
        self,
        title: str,
        artist: str,
        video_id: str,
        album: str | None = None,
        duration: int | None = None,
        thumbnail: str | None = None,
        artist_id: str | None = None,
        album_id: str | None = None,
        is_explicit: bool = False,
        feedback_tokens: dict[str, Any] | None = None,
    ):
        self.title = title
        self.artist = artist
        self.video_id = video_id
        self.album = album
        self.duration = duration
        self.thumbnail = thumbnail
        self.artist_id = artist_id
        self.album_id = album_id
        self.is_explicit = is_explicit
        self.feedback_tokens = feedback_tokens or {}

    def __repr__(self) -> str:
        return f"Song(title={self.title!r}, artist={self.artist!r}, video_id={self.video_id!r})"

    @classmethod
    def from_search_result(cls, result: dict) -> "Song":
        artists = result.get("artists") or []
        thumbnails = result.get("thumbnails") or []
        return cls(
            title=result.get("title", ""),
            artist=artists[0].get("name", "Unknown") if artists else "Unknown",
            video_id=result.get("videoId", ""),
            album=result.get("album"),
            duration=result.get("duration"),
            thumbnail=thumbnails[-1].get("url") if thumbnails else None,
            artist_id=artists[0].get("id") if artists else None,
            is_explicit=result.get("isExplicit", False),
            feedback_tokens=result.get("feedbackTokens", {}),
        )

    @classmethod
    def from_video_details(cls, details: dict) -> "Song":
        thumbnails = details.get("thumbnail", {}).get("thumbnails", [])
        return cls(
            title=details.get("title", ""),
            artist=details.get("author", "Unknown"),
            video_id=details.get("videoId", ""),
            duration=int(details.get("lengthSeconds", 0)),
            thumbnail=thumbnails[-1].get("url") if thumbnails else None,
        )

    @classmethod
    def from_watch_track(cls, track: dict) -> "Song":
        artists = track.get("artists") or []
        thumbnails = track.get("thumbnail") or []
        return cls(
            title=track.get("title", ""),
            artist=artists[0].get("name", "Unknown") if artists else "Unknown",
            video_id=track.get("videoId", ""),
            duration=track.get("length"),
            thumbnail=thumbnails[-1].get("url") if thumbnails else None,
            artist_id=artists[0].get("id") if artists else None,
        )
