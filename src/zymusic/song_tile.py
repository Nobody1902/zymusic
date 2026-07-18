from dataclasses import InitVar

import flet as ft

from zymusic.backend.song import Song


@ft.control(post_init_args=2)
class SongTile(ft.Container):
    song: InitVar[Song | None] = None

    def __post_init__(self, ref, song):
        self._song = song
        super().__post_init__(ref)

    def _on_hover(self, e):
        self.play_overlay.visible = e.data
        self.update()

    def _handle_click(self, e) -> None:
        if self.on_click:
            self.on_click(e)  # pyright: ignore[reportCallIssue]

    def init(self):
        super().init()

        self.play_overlay = ft.Container(
            bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLACK),
            alignment=ft.Alignment.CENTER,
            content=ft.Icon(
                ft.Icons.PLAY_ARROW,
                color=ft.Colors.WHITE,
                size=32,
            ),
            visible=False,
        )
        cover = (
            ft.Image(src=self._song.thumbnail, fit=ft.BoxFit.COVER)
            if self._song.thumbnail
            else ft.Icon(ft.Icons.MUSIC_NOTE, size=48)
        )

        self.tile = ft.ListTile(
            title=self._song.title,
            subtitle=self._song.artist,
            shape=ft.RoundedRectangleBorder(radius=ft.BorderRadius.all(10)),
            leading=ft.Container(
                width=48,
                height=48,
                content=ft.Stack(
                    controls=[
                        cover,
                        self.play_overlay,
                    ]
                ),
            ),
            on_click=lambda e: self._handle_click(e),
            data=self._song,
        )

        self.content = self.tile

        self.on_hover = self._on_hover
