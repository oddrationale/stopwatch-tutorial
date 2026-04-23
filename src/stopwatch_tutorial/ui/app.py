from typing import Literal

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header

from stopwatch_tutorial.ui.stopwatch import Stopwatch, StopwatchList


class StopwatchApp(App):
    """A Textual app to manage stopwatches."""

    CSS_PATH = "stopwatch.tcss"

    BINDINGS = [
        Binding(
            "up",
            "select_previous_stopwatch",
            "Previous",
            priority=True,
            show=False,
        ),
        Binding(
            "down",
            "select_next_stopwatch",
            "Next",
            priority=True,
            show=False,
        ),
        Binding(
            "left",
            "focus_previous_button",
            "Previous button",
            priority=True,
            show=False,
        ),
        Binding(
            "right",
            "focus_next_button",
            "Next button",
            priority=True,
            show=False,
        ),
        ("d", "toggle_dark", "Toggle dark mode"),
        ("a", "add_stopwatch", "Add"),
        ("r", "remove_stopwatch", "Remove"),
    ]

    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        yield Header()
        yield Footer()
        yield StopwatchList(Stopwatch(), Stopwatch(), Stopwatch(), id="timers")

    def on_mount(self) -> None:
        """Focus the first stopwatch so there is always a current selection."""
        self.query_one(Stopwatch).focus_default()

    def action_add_stopwatch(self) -> None:
        """An action to add a timer."""
        new_stopwatch = Stopwatch()
        self.query_one("#timers").mount(new_stopwatch)
        self.call_after_refresh(new_stopwatch.scroll_visible)
        self.call_after_refresh(new_stopwatch.focus_default)

    def get_selected_stopwatch(self) -> Stopwatch | None:
        """Get the currently selected stopwatch from the focused widget."""
        focused = self.focused
        if focused is None:
            return None

        return next(
            (
                widget
                for widget in focused.ancestors_with_self
                if isinstance(widget, Stopwatch)
            ),
            None,
        )

    def move_stopwatch_selection(self, direction: Literal[-1, 1]) -> None:
        """Move the selected stopwatch up or down."""
        selected_stopwatch = self.get_selected_stopwatch()
        if selected_stopwatch is None:
            return

        stopwatches = list(self.query(Stopwatch))
        selected_index = stopwatches.index(selected_stopwatch)
        next_index = selected_index + direction
        if 0 <= next_index < len(stopwatches):
            next_stopwatch = stopwatches[next_index]
            next_stopwatch.scroll_visible()
            next_stopwatch.focus_default()

    def action_select_previous_stopwatch(self) -> None:
        """Select the stopwatch above the current selection."""
        self.move_stopwatch_selection(-1)

    def action_select_next_stopwatch(self) -> None:
        """Select the stopwatch below the current selection."""
        self.move_stopwatch_selection(1)

    def action_focus_previous_button(self) -> None:
        """Focus the previous visible button in the selected stopwatch."""
        selected_stopwatch = self.get_selected_stopwatch()
        if selected_stopwatch is None:
            return
        selected_stopwatch.focus_button(-1)

    def action_focus_next_button(self) -> None:
        """Focus the next visible button in the selected stopwatch."""
        selected_stopwatch = self.get_selected_stopwatch()
        if selected_stopwatch is None:
            return
        selected_stopwatch.focus_button(1)

    def action_remove_stopwatch(self) -> None:
        """Called to remove a timer."""
        selected_stopwatch = self.get_selected_stopwatch()
        if selected_stopwatch is None:
            return

        stopwatches = list(self.query(Stopwatch))
        selected_index = stopwatches.index(selected_stopwatch)

        next_stopwatch = None
        if selected_index < len(stopwatches) - 1:
            next_stopwatch = stopwatches[selected_index + 1]
        elif selected_index > 0:
            next_stopwatch = stopwatches[selected_index - 1]

        selected_stopwatch.remove()
        if next_stopwatch is not None:
            self.call_after_refresh(next_stopwatch.focus_default)

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )
