from dataclasses import InitVar

import flet as ft

from zymusic.async_update import async_update
from zymusic.backend.media_player import MediaPlayer
from zymusic.song_tile import SongTile


@async_update
@ft.control(post_init_args=2)
class SearchView(ft.Column):
    player: InitVar[MediaPlayer | None] = None

    def __post_init__(self, ref, player):
        self._player = player
        super().__post_init__(ref)

    def _search(self):
        query = self.search_box.value.strip()
        if not query:
            return

        self.song_results = self._player.search(query)
        self.search_results.controls = []
        for s in self.song_results:
            self.search_results.controls.append(
                SongTile(
                    song=s,
                    on_click=lambda e: self._player.play_search_result(
                        self.song_results, index=self.song_results.index(e.control.data)
                    ),
                )
            )

        self.update()

    def init(self):
        super().init()

        self.search_box = ft.TextField(
            hint_text="Search...",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=12,
            expand=True,
            autofocus=True,
            height=50,
            keyboard_type=ft.KeyboardType.WEB_SEARCH,
            on_submit=self._search,
        )

        self.search_results = ft.ListView(expand=True, spacing=10)

        self.controls = [
            ft.Row(
                height=50,
                controls=[
                    self.search_box,
                ],
            ),
            self.search_results,
        ]
