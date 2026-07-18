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

    async def _on_suggestion_click(self, e):
        suggestion = e.control.data
        self.search_box.value = suggestion
        await self.search_box.close_view()
        self._search()

    async def _fetch_suggestions(self, query: str):
        suggestions = self._player.search_suggestions(query)
        if suggestions:
            self.search_box.controls = [
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.SEARCH),
                    title=ft.Text(s),
                    data=s,
                    on_click=self._on_suggestion_click,
                )
                for s in suggestions
            ]
        else:
            await self.search_box.close_view()

    async def _on_change(self, e):
        query = e.control.value.strip()
        if not query:
            self.search_box.controls = []
            return

        await self._fetch_suggestions(query)

    async def _on_submit(self, _):
        await self.search_box.close_view()
        self._search()

    async def _on_tap(self, _):
        await self.search_box.open_view()

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

        self.search_box = ft.SearchBar(
            bar_hint_text="Search...",
            view_hint_text="Search songs...",
            bar_leading=ft.Icon(ft.Icons.SEARCH),
            keyboard_type=ft.KeyboardType.WEB_SEARCH,
            autofocus=True,
            shrink_wrap=True,
            divider_color=ft.Colors.PRIMARY,
            on_change=self._on_change,
            on_submit=self._on_submit,
            on_tap=self._on_tap,
            expand=True,
        )

        self.search_results = ft.ListView(expand=True, spacing=10)

        self.controls = [
            ft.Row(
                height=70,
                controls=[
                    self.search_box,
                ],
            ),
            self.search_results,
        ]
