from dataclasses import InitVar

import flet as ft

from zymusic.backend.song import Song


@ft.control(post_init_args=2)
class SongTile(ft.ListTile):
    song: InitVar[Song | None] = None

    def __post_init__(self, ref, song):
        self._song = song
        self.data = song
        super().__post_init__(ref)

    def init(self):
        super().init()

        cover = (
            ft.Image(
                src=self._song.thumbnail,
                fit=ft.BoxFit.COVER,
                width=48,
                height=48,
                border_radius=ft.BorderRadius.all(10),
            )
            if self._song.thumbnail
            else ft.Icon(ft.Icons.MUSIC_NOTE, size=48)
        )

        self.title = self._song.title
        self.subtitle = self._song.artist
        self.shape = ft.RoundedRectangleBorder(radius=ft.BorderRadius.all(10))
        self.leading = cover
