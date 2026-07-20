from dataclasses import InitVar

import flet as ft


def _make_thumb(url: str | None) -> ft.Control:
    if url:
        return ft.Image(src=url, fit=ft.BoxFit.COVER)
    return ft.Container(
        bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
        alignment=ft.Alignment.CENTER,
        content=ft.Icon(ft.Icons.ALBUM, size=48, color=ft.Colors.GREY_600),
    )


@ft.control(post_init_args=2)
class AlbumCard(ft.Container):
    album: InitVar[dict | None] = None

    def __post_init__(self, ref, album):
        self._album = album or {}
        super().__post_init__(ref)

    def _handle_click(self, e) -> None:
        if self.on_click:
            self.on_click(e)  # pyright: ignore[reportCallIssue]

    def init(self):
        super().init()

        data = self._album
        thumbnails = data.get("thumbnails") or []
        thumb_url = thumbnails[-1]["url"] if thumbnails else None

        artists = data.get("artists") or []
        artist_name = artists[0].get("name", "") if artists else ""
        year = data.get("year") or ""
        album_type = data.get("type") or ""

        parts = [p for p in (artist_name, year or album_type) if p]
        subtitle = " · ".join(parts)

        self.content = ft.Card(
            variant=ft.CardVariant.FILLED,
            shape=ft.RoundedRectangleBorder(radius=12),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            data=data,
            content=ft.Container(
                width=160,
                on_click=lambda e: self._handle_click(e),
                data=self._album,
                content=ft.Column(
                    spacing=4,
                    controls=[
                        ft.Container(
                            width=160,
                            height=160,
                            clip_behavior=ft.ClipBehavior.HARD_EDGE,
                            content=_make_thumb(thumb_url),
                        ),
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=8),
                            content=ft.Column(
                                spacing=0,
                                controls=[
                                    ft.Text(
                                        data.get("title", ""),
                                        size=12,
                                        weight=ft.FontWeight.BOLD,
                                        max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    ft.Text(
                                        subtitle,
                                        size=11,
                                        color=ft.Colors.GREY_500,
                                        max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
            ),
        )
