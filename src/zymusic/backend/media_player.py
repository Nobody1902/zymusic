import subprocess

from ytmusicapi import YTMusic
from ytmusicapi.models.content.enums import LikeStatus, PlaylistSortOrder

from zymusic.backend.constants import YT_MUSIC_URL
from zymusic.backend.song import Song
from zymusic.backend.playlist import Playlist
from zymusic.backend.playqueue import Queue
from zymusic.backend.mpv_backend import MpvBackend


class MediaPlayer:
    def __init__(self, headers_file=None):
        self._yt = YTMusic(headers_file)
        self._queue = Queue()
        self._volume = 1.0
        self._repeat = "none"
        self._shuffle = False
        self._audio_device = None

        self._mpv = MpvBackend(
            on_track_end=self._on_mpv_track_end,
            on_state_change=self._on_mpv_state,
            on_position=self._on_mpv_position,
            on_error=self._on_mpv_error,
        )

        self._on_track_change = []
        self._on_playback_state = []
        self._on_queue_change = []
        self._on_position_change = []
        self._on_shuffle_change = []
        self._on_repeat_change = []
        self._on_volume_change = []
        self._on_mute_change = []
        self._on_speed_change = []
        self._on_error = []

    @property
    def ytmusic(self):
        return self._yt

    @property
    def queue(self):
        return self._queue

    @property
    def is_playing(self):
        return self._mpv.state in ("playing", "loading")

    @property
    def current_song(self):
        return self._queue.current

    @property
    def position(self):
        return self._mpv.position

    @property
    def duration(self):
        return self._mpv.duration

    @property
    def progress(self):
        return self._mpv.progress

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        self._volume = max(0.0, min(1.0, float(value)))
        if self._mpv.is_alive:
            self._mpv.set_volume(self._volume * 100)

    @property
    def muted(self):
        return self._mpv.is_muted

    @property
    def speed(self):
        return self._mpv.speed

    @speed.setter
    def speed(self, value):
        self._mpv.set_speed(value)

    @property
    def repeat(self):
        return self._repeat

    @repeat.setter
    def repeat(self, mode):
        if mode in ("none", "one", "all"):
            self._repeat = mode
            for cb in self._on_repeat_change:
                cb(mode)

    @property
    def shuffle(self):
        return self._shuffle

    @shuffle.setter
    def shuffle(self, enabled):
        self._shuffle = bool(enabled)
        if self._shuffle:
            self._queue.shuffle()
        for cb in self._on_shuffle_change:
            cb(self._shuffle)

    @property
    def audio_device(self):
        return self._audio_device

    @audio_device.setter
    def audio_device(self, device):
        self._audio_device = device
        if self._mpv.is_alive:
            self._mpv.set_audio_device(device)

    # ── Seek ──────────────────────────────────────────────────

    def seek(self, seconds):
        if self._mpv.is_alive:
            self._mpv.seek_absolute(seconds)

    def seek_relative(self, seconds):
        if self._mpv.is_alive:
            self._mpv.seek_relative(seconds)

    def seek_percent(self, percent):
        if self._mpv.is_alive:
            self._mpv.seek_percent(percent)

    # ── Playback control ──────────────────────────────────────

    def _load_current_into_mpv(self):
        song = self._queue.current
        if not song:
            return
        try:
            self._mpv.start()
        except (FileNotFoundError, RuntimeError):
            print("mpv unavailable, cannot play audio")
            return
        url = YT_MUSIC_URL.format(video_id=song.video_id)
        self._mpv.load(url)

    def play(self):
        song = self._queue.current
        if song is None and not self._queue.is_empty:
            song = self._queue.go_to(0)
        if song:
            self._load_current_into_mpv()
            self._mpv.play()
            self._emit_track_change(song)
        return song

    def pause(self):
        if self._mpv.is_alive:
            self._mpv.pause()

    def toggle_play(self):
        if self._mpv.state in ("playing", "loading"):
            self._mpv.pause()
        elif self._mpv.state == "paused":
            self._mpv.play()
        else:
            self.play()

    def stop(self):
        if self._mpv.is_alive:
            self._mpv.stop()

    def next(self):
        if self._repeat == "one":
            song = self._queue.current
            if song and self._mpv.is_alive:
                self._load_current_into_mpv()
                self._mpv.play()
                self._emit_track_change(song)
            return song

        if self._repeat == "all" and self._queue.current_index == len(self._queue) - 1:
            song = self._queue.go_to(0)
        else:
            song = self._queue.next()

        if song:
            self._load_current_into_mpv()
            self._mpv.play()
            self._emit_track_change(song)
        return song

    def prev(self):
        song = self._queue.prev()
        if song:
            self._load_current_into_mpv()
            self._mpv.play()
            self._emit_track_change(song)
        return song

    def play_index(self, index):
        song = self._queue.go_to(index)
        if song:
            self._load_current_into_mpv()
            self._mpv.play()
            self._emit_track_change(song)
        return song

    def play_song(self, song):
        self._queue.append(song)
        self.play_index(len(self._queue) - 1)

    def play_search_result(self, results, index=0):
        if not results or index >= len(results):
            return None
        self._queue.clear()
        self._queue.extend(results)
        return self.play_index(index)

    def play_album(self, browse_id, start_index=0):
        pl = Playlist.from_album(self._yt.get_album(browse_id))
        self._queue.clear()
        self._queue.extend(pl.tracks)
        return self.play_index(start_index)

    def play_playlist(self, playlist_id, limit=100, start_index=0):
        pl = Playlist.from_playlist(self._yt.get_playlist(playlist_id, limit))
        self._queue.clear()
        self._queue.extend(pl.tracks)
        return self.play_index(start_index)

    # ── Mute ──────────────────────────────────────────────────

    def mute(self):
        if self._mpv.is_alive:
            self._mpv.set_mute(True)

    def unmute(self):
        if self._mpv.is_alive:
            self._mpv.set_mute(False)

    def toggle_mute(self):
        if self._mpv.is_alive:
            self._mpv.toggle_mute()

    # ── Queue management ──────────────────────────────────────

    def add_to_queue(self, song):
        self._queue.append(song)
        self._emit_queue_change()

    def add_next(self, song):
        self._queue.insert_next(song)
        self._emit_queue_change()

    def remove_from_queue(self, index):
        removed = self._queue.remove(index)
        self._emit_queue_change()
        return removed

    def move_in_queue(self, from_index, to_index):
        self._queue.move(from_index, to_index)
        self._emit_queue_change()

    def clear_queue(self):
        self._queue.clear()
        self.stop()
        self._emit_queue_change()

    # ── Search & browse ───────────────────────────────────────

    def search(self, query, limit=20):
        results = self._yt.search(query, filter="songs", limit=limit)
        return [Song.from_search_result(r) for r in results]

    def search_suggestions(self, query):
        return self._yt.get_search_suggestions(query)

    def search_artists(self, query, limit=10):
        return self._yt.search(query, filter="artists", limit=limit)

    def search_albums(self, query, limit=10):
        return self._yt.search(query, filter="albums", limit=limit)

    def search_playlists(self, query, limit=10):
        return self._yt.search(query, filter="playlists", limit=limit)

    def get_album(self, browse_id):
        return Playlist.from_album(self._yt.get_album(browse_id))

    def get_artist(self, browse_id):
        return self._yt.get_artist(browse_id)

    def get_playlist(self, playlist_id, limit=100):
        return Playlist.from_playlist(self._yt.get_playlist(playlist_id, limit))

    def get_watch_playlist(self, video_id=None, playlist_id=None, limit=25):
        return Playlist.from_watch_playlist(
            self._yt.get_watch_playlist(video_id, playlist_id, limit=limit)
        )

    def get_home(self, limit=20):
        return self._yt.get_home(limit)

    def get_charts(self, country=None):
        return self._yt.get_charts(country or "ZZ")

    def get_mood_categories(self):
        return self._yt.get_mood_categories()

    def get_mood_playlists(self, mood):
        return self._yt.get_mood_playlists(mood)

    def get_explore(self):
        return self._yt.get_explore()

    # ── Song info ─────────────────────────────────────────────

    def get_song_info(self, video_id):
        data = self._yt.get_song(video_id)
        details = data.get("videoDetails", {})
        return Song.from_video_details(details)

    def get_song_details(self, video_id):
        return self._yt.get_song(video_id)

    def get_song_credits(self, browse_id):
        return self._yt.get_song_credits(browse_id)

    def get_lyrics(self, browse_id):
        result = self._yt.get_lyrics(browse_id)
        if result:
            return result.get("lyrics")
        return None

    # ── Library ───────────────────────────────────────────────

    def get_liked_songs(self, limit=100):
        data = self._yt.get_liked_songs(limit)
        return [
            Song.from_search_result(r)
            for r in data.get("tracks", [])
            if isinstance(r, dict)
        ]

    def get_history(self):
        data = self._yt.get_history()
        return [Song.from_search_result(r) for r in data if isinstance(r, dict)]

    def get_library_songs(self, limit=100):
        return self._yt.get_library_songs(limit)

    def get_library_albums(self, limit=25):
        return self._yt.get_library_albums(limit)

    def get_library_artists(self, limit=25):
        return self._yt.get_library_artists(limit)

    def get_library_playlists(self, limit=25):
        return self._yt.get_library_playlists(limit)

    def get_library_upload_songs(self, limit=100):
        return self._yt.get_library_upload_songs(limit)

    # ── Rating ────────────────────────────────────────────────

    def rate_song(self, video_id, rating):
        if isinstance(rating, str):
            try:
                rating = LikeStatus(rating)
            except ValueError:
                valid = [e.value for e in LikeStatus]
                print(f"rating must be one of {valid}")
                return
        return self._yt.rate_song(video_id, rating)

    def like_song(self, video_id):
        return self._yt.rate_song(video_id, LikeStatus.LIKE)

    def dislike_song(self, video_id):
        return self._yt.rate_song(video_id, LikeStatus.DISLIKE)

    def remove_rating(self, video_id):
        return self._yt.rate_song(video_id, LikeStatus.INDIFFERENT)

    # ── Library management ────────────────────────────────────

    def add_library_song(self, feedback_token):
        return self._yt.edit_song_library_status([feedback_token])

    def remove_library_song(self, feedback_token):
        return self._yt.edit_song_library_status([feedback_token])

    # ── Playlist management ───────────────────────────────────

    def create_playlist(self, title, description="", privacy="PUBLIC"):
        return self._yt.create_playlist(title, description, privacy)

    def edit_playlist(
        self,
        playlist_id,
        title=None,
        description=None,
        privacy=None,
        collaboration=None,
        move_item=None,
        add_playlist_id=None,
        sort_order=None,
        add_to_top=None,
    ):
        if isinstance(sort_order, str):
            sort_order = PlaylistSortOrder(sort_order)
        return self._yt.edit_playlist(
            playlist_id,
            title=title,
            description=description,
            privacyStatus=privacy,
            collaboration=collaboration,
            moveItem=move_item,
            addPlaylistId=add_playlist_id,
            sortOrder=sort_order,
            addToTop=add_to_top,
        )

    def delete_playlist(self, playlist_id):
        return self._yt.delete_playlist(playlist_id)

    def add_playlist_items(self, playlist_id, video_ids):
        return self._yt.add_playlist_items(playlist_id, video_ids)

    def remove_playlist_items(self, playlist_id, videos):
        return self._yt.remove_playlist_items(playlist_id, videos)

    # ── Account & subscriptions ───────────────────────────────

    def get_account_info(self):
        return self._yt.get_account_info()

    def subscribe_artists(self, channel_ids):
        return self._yt.subscribe_artists(channel_ids)

    def unsubscribe_artists(self, channel_ids):
        return self._yt.unsubscribe_artists(channel_ids)

    def get_library_subscriptions(self, limit=25):
        return self._yt.get_library_subscriptions(limit=limit)

    # ── Utility ───────────────────────────────────────────────

    def resolve_stream_url(self, video_id, quality="bestaudio"):
        url = f"https://music.youtube.com/watch?v={video_id}"
        try:
            result = subprocess.run(
                ["yt-dlp", "-g", "-f", quality, url],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except FileNotFoundError:
            print("yt-dlp not found")
        except subprocess.TimeoutExpired:
            print(f"yt-dlp timed out resolving {video_id}")
        return None

    def get_streaming_data(self, video_id):
        data = self._yt.get_song(video_id)
        return data.get("streamingData", {})

    # ── Mpv callbacks ─────────────────────────────────────────

    def _on_mpv_track_end(self):
        if self._mpv.state == "idle":
            self.next()

    def _on_mpv_state(self, state):
        is_playing = state in ("playing", "loading")
        for cb in self._on_playback_state:
            cb(is_playing)

    def _on_mpv_position(self, pos, duration):
        for cb in self._on_position_change:
            cb(pos, duration)

    def _on_mpv_error(self, file_name):
        for cb in self._on_error:
            cb(file_name)

    # ── Event registration ────────────────────────────────────

    def on_track_change(self, callback):
        self._on_track_change.append(callback)

    def on_playback_state_change(self, callback):
        self._on_playback_state.append(callback)

    def on_queue_change(self, callback):
        self._on_queue_change.append(callback)

    def on_position_change(self, callback):
        self._on_position_change.append(callback)

    def on_shuffle_change(self, callback):
        self._on_shuffle_change.append(callback)

    def on_repeat_change(self, callback):
        self._on_repeat_change.append(callback)

    def on_volume_change(self, callback):
        self._on_volume_change.append(callback)

    def on_mute_change(self, callback):
        self._on_mute_change.append(callback)

    def on_speed_change(self, callback):
        self._on_speed_change.append(callback)

    def on_error(self, callback):
        self._on_error.append(callback)

    # ── Event emitters ────────────────────────────────────────

    def _emit_track_change(self, song):
        for cb in self._on_track_change:
            cb(song)

    def _emit_queue_change(self):
        for cb in self._on_queue_change:
            cb()

    def _emit_playback_state(self, state):
        for cb in self._on_playback_state:
            cb(state)

    # ── Lifecycle ─────────────────────────────────────────────

    def shutdown(self):
        self._mpv.shutdown()
