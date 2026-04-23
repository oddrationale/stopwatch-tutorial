from dataclasses import dataclass
from enum import Enum
from math import isfinite


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
        case _:
            msg = f"Unsupported timer state: {timer_state!r}"
            raise TypeError(msg)


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


class StopwatchButton(str, Enum):
    START = "start"
    STOP = "stop"
    RESET = "reset"


def visible_buttons(timer_state: TimerState) -> tuple[StopwatchButton, ...]:
    """Return the buttons that should be focusable for the timer state."""
    if is_running(timer_state):
        return (StopwatchButton.STOP,)
    return (StopwatchButton.START, StopwatchButton.RESET)


def default_button(timer_state: TimerState) -> StopwatchButton:
    """Return the default button for the timer state."""
    return visible_buttons(timer_state)[0]
