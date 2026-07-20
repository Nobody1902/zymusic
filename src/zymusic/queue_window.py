from dataclasses import InitVar

import flet as ft

from zymusic.async_update import async_update
from zymusic.backend.media_player import MediaPlayer
from zymusic.backend.song import Song
from zymusic.song_tile import SongTile


@async_update
@ft.control(post_init_args=2)
class Queue(ft.Column):
    player: InitVar[MediaPlayer | None] = None

    def __post_init__(self, ref, player):
        self._player = player
        super().__post_init__(ref)

    def update_queue(self):
        self.queue_list.controls = []

        for el in self._player.queue.items:
            self.queue_list.controls.append(
                SongTile(
                    song=el, on_click=lambda e: self._player.play_song(e.control.data)
                )
            )

        self.update()

    def update_current(self, song: Song):
        for c in self.queue_list.controls:
            if c._song == song:
                c.bgcolor = ft.Colors.PRIMARY_CONTAINER
            else:
                c.bgcolor = None

        self.update()

    def init(self):
        super().init()

        self._player.on_track_change(self.update_current)
        self._player.queue.on_change(self.update_queue)

        self.queue_list = ft.ListView(spacing=10, expand=True)

        self.controls = [
            ft.Column(
                align=ft.Alignment.CENTER,
                controls=[
                    ft.Text("Queue"),
                ],
            ),
            self.queue_list,
        ]
