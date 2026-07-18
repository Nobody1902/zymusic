import flet as ft
from zymusic.async_update import async_update


@async_update
@ft.control
class Sidebar(ft.NavigationRail):
    def init(self):
        super().init()

        self.min_width = 72
        self.min_extended_width = 200
        self.label_type = ft.NavigationRailLabelType.SELECTED
        self.group_alignment = 0.0
        self.selected_index = 1
        self.leading = ft.IconButton(ft.Icons.ACCOUNT_CIRCLE)
        self.destinations = [
            ft.NavigationRailDestination(
                icon=ft.Icons.HOME_OUTLINED,
                selected_icon=ft.Icons.HOME,
                label="Home",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SEARCH_OUTLINED,
                selected_icon=ft.Icons.SEARCH,
                label="Search",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.LIBRARY_MUSIC_OUTLINED,
                selected_icon=ft.Icons.LIBRARY_MUSIC,
                label="Library",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SETTINGS_OUTLINED,
                selected_icon=ft.Icons.SETTINGS,
                label="Settings",
            ),
        ]
