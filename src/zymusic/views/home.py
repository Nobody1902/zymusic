from dataclasses import InitVar

import flet as ft

from zymusic.album_card import AlbumCard
from zymusic.async_update import async_update
from zymusic.backend.media_player import MediaPlayer
from zymusic.backend.song import Song
from zymusic.playlist_card import PlaylistCard
from zymusic.song_tile import SongTile


def _content_type(item: dict) -> str:
    if "videoId" in item:
        return "song"
    if "browseId" in item:
        bid = item["browseId"]
        if bid.startswith("MPRE"):
            return "album"
        if bid.startswith("UC"):
            return "artist"

        return "browse"
    if "playlistId" in item:
        return "playlist"
    if "podcastId" in item:
        return "podcast"
    if "index" in item:
        return "episode"
    return "unknown"


@async_update
@ft.control(post_init_args=2)
class HomeView(ft.Column):
    player: InitVar[MediaPlayer | None] = None

    def __post_init__(self, ref, player):
        self._player = player
        super().__post_init__(ref)

    def _make_song_tile(self, item: dict) -> SongTile:
        song = Song.from_home_item(item)
        return SongTile(song=song, on_click=lambda _: self._player.play_song(song))

    def _make_fallback_card(self, item: dict) -> ft.Container:
        thumbnails = item.get("thumbnails") or []
        thumb_url = thumbnails[-1]["url"] if thumbnails else None
        title = item.get("title", "")

        return ft.Container(
            width=160,
            height=180,
            border_radius=10,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=ft.Column(
                spacing=4,
                controls=[
                    ft.Container(
                        width=160,
                        height=160,
                        border_radius=10,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        content=(
                            ft.Image(src=thumb_url, fit=ft.BoxFit.COVER)
                            if thumb_url
                            else ft.Container(
                                bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
                                alignment=ft.Alignment.CENTER,
                                content=ft.Icon(
                                    ft.Icons.MUSIC_NOTE,
                                    size=48,
                                    color=ft.Colors.GREY_600,
                                ),
                            )
                        ),
                    ),
                    ft.Text(
                        title,
                        size=12,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
            ),
        )

    def init(self):
        super().init()

        self.home = self._player.get_home()

        sections: list[ft.Control] = []
        for section in self.home:
            title = section.get("title")
            contents = section.get("contents") or []
            if not contents:
                continue

            items: list[ft.Control] = []
            for c in contents:
                ctype = _content_type(c)
                if ctype == "song":
                    items.append(self._make_song_tile(c))
                elif ctype == "album":
                    items.append(
                        AlbumCard(
                            album=c,
                            expand=False,
                            on_click=lambda e: self._player.play_album(
                                e.control.data.get("browseId")
                            ),
                        )
                    )
                elif ctype == "playlist":
                    items.append(
                        PlaylistCard(
                            playlist=c,
                            expand=False,
                            on_click=lambda e: self._player.play_playlist(
                                e.control.data.get("playlistId")
                            ),
                        )
                    )
                else:
                    items.append(self._make_fallback_card(c))

            sections.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=100),
                    content=ft.Column(
                        spacing=8,
                        controls=[
                            ft.Container(
                                padding=ft.padding.only(left=16, top=16),
                                alignment=ft.Alignment.CENTER,
                                content=ft.Text(
                                    title or "",
                                    size=32,
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ),
                            ft.Row(
                                controls=[
                                    ft.ListView(
                                        horizontal=True,
                                        expand=True,
                                        height=210,
                                        scroll=ft.ScrollMode.AUTO,
                                        spacing=8,
                                        controls=items,
                                    ),
                                ]
                            ),
                        ],
                    ),
                )
            )

        self.controls = [
            ft.ListView(expand=True, controls=sections),
        ]
