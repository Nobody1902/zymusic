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
            self.cover_image.src = song.thumbnail
            self.cover_image.visible = True
            self.cover_placeholder.visible = False

        self.title_text.value = song.title
        self.artist_text.value = song.artist
        self.empty_text.visible = False
        self.track_info.visible = True
        self.pause_button.disabled = False
        self.previous_button.disabled = False
        self.next_button.disabled = False
        self.shuffle_button.disabled = False
        self.repeat_button.disabled = False
        self.progress_slider.disabled = False
        self.update()

    def _format_time(self, seconds):
        minutes = int(seconds) // 60
        secs = int(seconds) % 60
        return f"{minutes}:{secs:02d}"

    def _on_position_change(self, pos, duration):
        self.progress_slider.max = duration
        self.progress_slider.value = pos
        self.current_time.content.value = self._format_time(pos)
        self.duration_time.content.value = self._format_time(duration)
        self.update()

    def _on_playback_state_change(self, playing):
        self.pause_button.icon = ft.Icons.PAUSE if playing else ft.Icons.PLAY_ARROW
        self.update()

    def _on_shuffle_change(self, enabled):
        self.shuffle_button.icon_color = (
            ft.Colors.PRIMARY if enabled else ft.Colors.GREY_500
        )

        self.shuffle_button.bgcolor = ft.Colors.PRIMARY_CONTAINER if enabled else None
        self.update()

    def _on_repeat_change(self, mode):
        if mode == "none":
            self.repeat_button.icon = ft.Icons.REPEAT
            self.repeat_button.icon_color = ft.Colors.GREY_500
            self.repeat_button.bgcolor = None
        elif mode == "all":
            self.repeat_button.icon = ft.Icons.REPEAT
            self.repeat_button.icon_color = ft.Colors.PRIMARY
        elif mode == "one":
            self.repeat_button.icon = ft.Icons.REPEAT_ONE
            self.repeat_button.icon_color = ft.Colors.PRIMARY
        self.update()

    def _toggle_shuffle(self):
        self._player.shuffle = not self._player.shuffle

    def _cycle_repeat(self):
        modes = ("none", "all", "one")
        current = (
            modes.index(self._player.repeat) if self._player.repeat in modes else 0
        )
        self._player.repeat = modes[(current + 1) % len(modes)]

    def init(self):
        super().init()

        self._player.on_track_change(self._on_track_change)
        self._player.on_position_change(self._on_position_change)
        self._player.on_playback_state_change(self._on_playback_state_change)
        self._player.on_shuffle_change(self._on_shuffle_change)
        self._player.on_repeat_change(self._on_repeat_change)

        self.cover_image = ft.Image(
            src="",
            fit=ft.BoxFit.FILL,
            visible=False,
        )
        self.cover_placeholder = ft.Icon(
            ft.Icons.MUSIC_NOTE, size=40, color=ft.Colors.GREY_600
        )
        self.cover = ft.Stack(
            width=50,
            height=50,
            controls=[
                self.cover_placeholder,
                self.cover_image,
            ],
        )

        self.title_text = ft.Text(
            "",
            weight=ft.FontWeight.BOLD,
            overflow=ft.TextOverflow.ELLIPSIS,
            max_lines=1,
            no_wrap=True,
        )
        self.artist_text = ft.Text(
            "",
            color=ft.Colors.GREY_500,
            overflow=ft.TextOverflow.ELLIPSIS,
            max_lines=1,
            no_wrap=True,
        )
        self.track_info = ft.Column(
            visible=False,
            spacing=0,
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                self.title_text,
                self.artist_text,
            ],
        )

        self.empty_text = ft.Text(
            "Not playing",
            size=14,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.GREY_500,
        )

        self.current_time = ft.Container(
            content=ft.Text(
                self._format_time(0),
                size=11,
                color=ft.Colors.GREY_500,
            ),
            padding=ft.padding.only(right=8),
        )
        self.duration_time = ft.Container(
            content=ft.Text(
                self._format_time(0),
                size=11,
                color=ft.Colors.GREY_500,
            ),
            padding=ft.padding.only(left=8),
        )

        self.progress_slider = ft.Slider(
            min=0,
            max=1,
            height=20,
            padding=0,
            expand=True,
            disabled=True,
            on_change=lambda e: self._player.seek(e.control.value),
        )

        self.pause_button = ft.IconButton(
            ft.Icons.PAUSE,
            on_click=lambda _: self._player.toggle_play(),
            disabled=True,
        )

        self.previous_button = ft.IconButton(
            ft.Icons.SKIP_PREVIOUS,
            on_click=lambda _: self._player.prev(),
            disabled=True,
        )
        self.next_button = ft.IconButton(
            ft.Icons.SKIP_NEXT,
            on_click=lambda _: self._player.next(),
            disabled=True,
        )

        self.shuffle_button = ft.IconButton(
            ft.Icons.SHUFFLE,
            on_click=lambda _: self._toggle_shuffle(),
            disabled=True,
        )
        self.repeat_button = ft.IconButton(
            ft.Icons.REPEAT,
            on_click=lambda _: self._cycle_repeat(),
            disabled=True,
        )

        self.padding = ft.Padding.only(left=20, right=20, bottom=10)

        self.content = ft.Column(
            height=150,
            margin=0,
            spacing=5,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    margin=ft.margin.only(top=4),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            self.current_time,
                            self.progress_slider,
                            self.duration_time,
                        ],
                    ),
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    height=45,
                    controls=[
                        ft.Row(
                            expand=True,
                            alignment=ft.MainAxisAlignment.START,
                            controls=[
                                self.cover,
                                self.empty_text,
                                self.track_info,
                            ],
                        ),
                        ft.Row(
                            expand=True,
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                self.shuffle_button,
                                self.previous_button,
                                self.pause_button,
                                self.next_button,
                                self.repeat_button,
                            ]
                        ),
                        ft.Row(
                            expand=True,
                            alignment=ft.MainAxisAlignment.END,
                            controls=[
                                ft.IconButton(ft.Icons.MORE_HORIZ),
                            ],
                        ),
                    ],
                ),
            ],
        )
