import flet as ft

from zymusic.bottombar import BottomBar
from zymusic.backend.media_player import MediaPlayer

from zymusic.queue_window import Queue
from zymusic.sidebar import Sidebar
from zymusic.views.home import HomeView
from zymusic.views.library import LibraryView
from zymusic.views.search import SearchView
from zymusic.views.settings import SettingsView


def main(page: ft.Page):

    mp = MediaPlayer()
    page.on_close = lambda _: mp.shutdown()

    page.title = "zymusic"

    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.DEEP_PURPLE)
    page.dark_theme = ft.Theme(color_scheme_seed=ft.Colors.DEEP_PURPLE)

    home_view = HomeView(player=mp, expand=True)
    search_view = SearchView(player=mp, expand=True)
    library_view = LibraryView(player=mp, expand=True)
    settings_view = SettingsView(player=mp, expand=True)
    views = [home_view, search_view, library_view, settings_view]

    content_column = ft.Column(expand=5, controls=[home_view])
    queue = Queue(player=mp, expand=3)

    def switch_view(index):
        content_column.controls = [views[index]]
        page.update()

    page.add(
        ft.Row(
            expand=True,
            controls=[
                Sidebar(on_change=lambda e: switch_view(e.control.selected_index)),
                ft.VerticalDivider(width=1),
                content_column,
                ft.VerticalDivider(width=1),
                queue,
            ],
        )
    )

    page.bottom_appbar = BottomBar(player=mp)


if __name__ == "__main__":
    ft.run(main)
