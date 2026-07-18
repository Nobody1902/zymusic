from dataclasses import InitVar

import flet as ft

from zymusic.async_update import async_update
from zymusic.backend.media_player import MediaPlayer


@async_update
@ft.control(post_init_args=2)
class LibraryView(ft.Column):
    player: InitVar[MediaPlayer | None] = None

    def __post_init__(self, ref, player):
        self._player = player
        super().__post_init__(ref)

    def init(self):
        super().init()

        self.controls = [ft.Text("Library")]
