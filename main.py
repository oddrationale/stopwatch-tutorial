from dataclasses import dataclass
from enum import Enum
from math import isfinite
from time import monotonic
from typing import Literal

from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import HorizontalGroup, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Button, Digits, Footer, Header

# --- Functional core: pure functions and immutable state ---


def format_time(time: float) -> str:
    """Format a time value in seconds to HH:MM:SS.cc display string."""
    minutes, seconds = divmod(time, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02,.0f}:{minutes:02.0f}:{seconds:05.2f}"


def require_elapsed_seconds(value: float) -> float:
    """Validate an elapsed duration."""
    if not isfinite(value) or value < 0:
        msg = f"Elapsed time must be a finite, non-negative float, got {value!r}"
        raise ValueError(msg)
    return value


def require_timestamp(value: float) -> float:
    """Validate a monotonic timestamp."""
    if not isfinite(value):
        msg = f"Timestamp must be a finite float, got {value!r}"
        raise ValueError(msg)
    return value


@dataclass(frozen=True)
class StoppedTimer:
    """A timer that is not currently running."""

    total: float = 0.0

    def __post_init__(self) -> None:
        require_elapsed_seconds(self.total)


@dataclass(frozen=True)
class RunningTimer:
    """A timer that is currently running."""

    accumulated: float
    started_at: float

    def __post_init__(self) -> None:
        require_elapsed_seconds(self.accumulated)
        require_timestamp(self.started_at)


type TimerState = StoppedTimer | RunningTimer


def elapsed_time(timer_state: TimerState, now: float) -> float:
    """Return the elapsed time for a timer state."""
    now = require_timestamp(now)
    match timer_state:
        case StoppedTimer(total=total):
            return total
        case RunningTimer(accumulated=accumulated, started_at=started_at):
            if now < started_at:
                msg = (
                    "Current time must not be earlier than the timer start time, "
                    f"got now={now!r}, started_at={started_at!r}"
                )
                raise ValueError(msg)
            return accumulated + (now - started_at)


def start_timer(timer_state: StoppedTimer, now: float) -> RunningTimer:
    """Start a stopped timer."""
    return RunningTimer(
        accumulated=timer_state.total,
        started_at=require_timestamp(now),
    )


def stop_timer(timer_state: RunningTimer, now: float) -> StoppedTimer:
    """Stop a running timer."""
    return StoppedTimer(total=elapsed_time(timer_state, now))


def reset_timer(_: StoppedTimer) -> StoppedTimer:
    """Reset a stopped timer back to zero."""
    return StoppedTimer()


def is_running(timer_state: TimerState) -> bool:
    """Return whether the timer is currently running."""
    return isinstance(timer_state, RunningTimer)


def visible_buttons(timer_state: TimerState) -> tuple["StopwatchButton", ...]:
    """Return the buttons that should be focusable for the timer state."""
    if is_running(timer_state):
        return (StopwatchButton.STOP,)
    return (StopwatchButton.START, StopwatchButton.RESET)


def default_button(timer_state: TimerState) -> "StopwatchButton":
    """Return the default button for the timer state."""
    return visible_buttons(timer_state)[0]


class StopwatchButton(str, Enum):
    START = "start"
    STOP = "stop"
    RESET = "reset"


# --- Imperative shell: thin widget wrappers ---


class TimeDisplay(Digits):
    """A widget to display elapsed time."""


class StopwatchControl(Button):
    """A stopwatch button that supports both Enter and Space."""

    BINDINGS = [
        Binding(
            "enter,space",
            "press",
            "Press button",
            show=False,
        )
    ]


class StopwatchList(VerticalScroll, can_focus=False):
    """A non-focusable container for stopwatches."""


class Stopwatch(HorizontalGroup):
    """A stopwatch widget."""

    can_focus = False
    timer_state: reactive[TimerState] = reactive(StoppedTimer(), init=False)

    def on_mount(self) -> None:
        """Set up the display refresh loop."""
        self.update_timer = self.set_interval(1 / 60, self.refresh_time, pause=True)
        self.refresh_time()

    def watch_timer_state(self, _old: TimerState, new: TimerState) -> None:
        """Render timer state and align the shell with it."""
        if is_running(new):
            self.update_timer.resume()
            self.add_class("started")
        else:
            self.update_timer.pause()
            self.remove_class("started")
        self.refresh_time()
        if self.has_focus_within:
            self.call_after_refresh(self.focus_default)

    def refresh_time(self) -> None:
        """Refresh the rendered elapsed time."""
        self.query_one(TimeDisplay).update(
            format_time(elapsed_time(self.timer_state, monotonic()))
        )

    def update_selection_state(self) -> None:
        """Keep the selected class aligned with focus within the stopwatch."""
        self.set_class(self.has_focus or self.has_focus_within, "selected")

    def focus_default(self) -> None:
        """Focus the primary visible control for this stopwatch."""
        button_id = default_button(self.timer_state)
        self.query_one(f"#{button_id.value}", StopwatchControl).focus()

    def focus_button(self, direction: Literal[-1, 1]) -> None:
        """Move focus between the visible buttons for this stopwatch."""
        buttons = visible_buttons(self.timer_state)
        focused = self.screen.focused
        if not isinstance(focused, StopwatchControl) or self not in focused.ancestors:
            self.focus_default()
            return

        current_button = StopwatchButton(focused.id)
        current_index = buttons.index(current_button)
        next_index = max(0, min(current_index + direction, len(buttons) - 1))
        self.query_one(f"#{buttons[next_index].value}", StopwatchControl).focus()

    def on_click(self, event: events.Click) -> None:
        """Select this stopwatch when it is clicked."""
        if not isinstance(event.widget, StopwatchControl):
            self.focus_default()

    def on_focus(self) -> None:
        """Refresh selection styling when the stopwatch gains focus."""
        self.update_selection_state()

    def on_blur(self) -> None:
        """Refresh selection styling when the stopwatch loses focus."""
        self.call_after_refresh(self.update_selection_state)

    def on_descendant_focus(self) -> None:
        """Refresh selection styling when a child widget gains focus."""
        self.update_selection_state()

    def on_descendant_blur(self) -> None:
        """Refresh selection styling when a child widget loses focus."""
        self.call_after_refresh(self.update_selection_state)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        button = StopwatchButton(event.button.id)
        now = monotonic()
        match button, self.timer_state:
            case StopwatchButton.START, StoppedTimer() as timer_state:
                self.timer_state = start_timer(timer_state, now)
            case StopwatchButton.STOP, RunningTimer() as timer_state:
                self.timer_state = stop_timer(timer_state, now)
            case StopwatchButton.RESET, StoppedTimer() as timer_state:
                self.timer_state = reset_timer(timer_state)

    def compose(self) -> ComposeResult:
        """Create child widgets of a stopwatch."""
        yield StopwatchControl(
            "Start", id=StopwatchButton.START.value, variant="success"
        )
        yield StopwatchControl("Stop", id=StopwatchButton.STOP.value, variant="error")
        yield StopwatchControl("Reset", id=StopwatchButton.RESET.value)
        yield TimeDisplay()


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


if __name__ == "__main__":
    app = StopwatchApp()
    app.run()
