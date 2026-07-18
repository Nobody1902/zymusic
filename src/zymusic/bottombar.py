from dataclasses import InitVar

import flet as ft

from zymusic.async_update import async_update
from zymusic.backend.media_player import MediaPlayer


@async_update
@ft.control(post_init_args=2)
class BottomBar(ft.BottomAppBar):
    player: InitVar[MediaPlayer | None] = None

    def __post_init__(self, ref, player):
        self._player = player
        super().__post_init__(ref)

    def _on_track_change(self, song):
        if song.thumbnail:
            self.cover.src = song.thumbnail

        self.title_text.value = song.title
        self.artist_text.value = song.artist
        self.update()

    def _on_position_change(self, pos, duration):
        self.progress_slider.max = duration
        self.progress_slider.value = pos
        self.update()

    def _on_playback_state_change(self, playing):
        self.pause_button.icon = ft.Icons.PAUSE if playing else ft.Icons.PLAY_ARROW
        self.update()

    def init(self):
        super().init()

        self._player.on_track_change(self._on_track_change)
        self._player.on_position_change(self._on_position_change)
        self._player.on_playback_state_change(self._on_playback_state_change)

        self.cover = ft.Image(
            src="https://yt3.googleusercontent.com/j75nRhWXJf_EUFoIz6KZ4KzBBGvSv6lAHVSjoofP7ndFBwOlvYGDeZ-c0uN2hEyDUPfk5u6AlriKNI4=w544-h544-l90-rj",
            fit=ft.BoxFit.FILL,
        )
        self.title_text = ft.Text("", weight=ft.FontWeight.BOLD)
        self.artist_text = ft.Text("", color=ft.Colors.GREY_500)

        self.progress_slider = ft.Slider(
            min=0,
            max=1,
            height=20,
            padding=0,
            on_change=lambda e: self._player.seek(e.control.value),
        )

        self.pause_button = ft.IconButton(
            ft.Icons.PAUSE, on_click=lambda _: self._player.toggle_play()
        )

        self.previous_button = ft.IconButton(
            ft.Icons.SKIP_PREVIOUS, on_click=lambda _: self._player.prev()
        )
        self.next_button = ft.IconButton(
            ft.Icons.SKIP_NEXT, on_click=lambda _: self._player.next()
        )

        self.padding = ft.Padding.only(left=20, right=20, bottom=10)

        self.content = ft.Column(
            height=150,
            margin=0,
            spacing=5,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                self.progress_slider,
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    height=45,
                    controls=[
                        ft.Row(
                            controls=[
                                self.cover,
                                ft.Column(
                                    spacing=0,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    controls=[
                                        self.title_text,
                                        self.artist_text,
                                    ],
                                ),
                            ]
                        ),
                        ft.Row(
                            controls=[
                                ft.IconButton(ft.Icons.SHUFFLE),
                                self.previous_button,
                                self.pause_button,
                                self.next_button,
                                ft.IconButton(ft.Icons.REPEAT),
                            ]
                        ),
                        ft.Row(
                            controls=[
                                ft.IconButton(ft.Icons.MORE_HORIZ),
                            ],
                        ),
                    ],
                ),
            ],
        )
