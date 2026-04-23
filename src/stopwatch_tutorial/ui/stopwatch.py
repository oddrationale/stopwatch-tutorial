from time import monotonic
from typing import Literal

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import HorizontalGroup, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Button, Digits

from stopwatch_tutorial.core import (
    RunningTimer,
    StopwatchButton,
    StoppedTimer,
    TimerState,
    default_button,
    elapsed_time,
    format_time,
    is_running,
    reset_timer,
    start_timer,
    stop_timer,
    visible_buttons,
)


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
            case _:
                msg = (
                    "Button press does not match the current timer state, "
                    f"got button={button.value!r}, timer_state={self.timer_state!r}"
                )
                raise RuntimeError(msg)

    def compose(self) -> ComposeResult:
        """Create child widgets of a stopwatch."""
        yield StopwatchControl(
            "Start", id=StopwatchButton.START.value, variant="success"
        )
        yield StopwatchControl("Stop", id=StopwatchButton.STOP.value, variant="error")
        yield StopwatchControl("Reset", id=StopwatchButton.RESET.value)
        yield TimeDisplay()
