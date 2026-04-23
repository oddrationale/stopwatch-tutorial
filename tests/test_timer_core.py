from __future__ import annotations

import math
from typing import cast

import pytest

from main import (
    RunningTimer,
    StopwatchButton,
    StoppedTimer,
    TimerState,
    default_button,
    elapsed_time,
    format_time,
    is_running,
    require_elapsed_seconds,
    require_timestamp,
    reset_timer,
    start_timer,
    stop_timer,
    visible_buttons,
)


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (0.0, "00:00:00.00"),
        (3661.23, "01:01:01.23"),
        (360_000.0, "100:00:00.00"),
    ],
)
def test_format_time(seconds: float, expected: str) -> None:
    assert format_time(seconds) == expected


def test_require_elapsed_seconds_accepts_non_negative_finite_values() -> None:
    assert require_elapsed_seconds(12.5) == 12.5


@pytest.mark.parametrize("value", [-0.01, math.inf, math.nan])
def test_require_elapsed_seconds_rejects_invalid_values(value: float) -> None:
    with pytest.raises(ValueError, match="Elapsed time"):
        require_elapsed_seconds(value)


def test_require_timestamp_accepts_finite_values() -> None:
    assert require_timestamp(123.456) == 123.456


@pytest.mark.parametrize("value", [math.inf, math.nan])
def test_require_timestamp_rejects_invalid_values(value: float) -> None:
    with pytest.raises(ValueError, match="Timestamp"):
        require_timestamp(value)


def test_timer_dataclasses_validate_state() -> None:
    with pytest.raises(ValueError, match="Elapsed time"):
        StoppedTimer(total=-1.0)

    with pytest.raises(ValueError, match="Elapsed time"):
        RunningTimer(accumulated=-1.0, started_at=10.0)

    with pytest.raises(ValueError, match="Timestamp"):
        RunningTimer(accumulated=1.0, started_at=math.nan)


def test_elapsed_time_for_stopped_timer_returns_total() -> None:
    assert elapsed_time(StoppedTimer(total=7.25), now=100.0) == 7.25


def test_elapsed_time_for_running_timer_includes_accumulated_time() -> None:
    timer_state = RunningTimer(accumulated=2.5, started_at=10.0)

    assert elapsed_time(timer_state, now=13.75) == pytest.approx(6.25)


def test_elapsed_time_rejects_invalid_now_values() -> None:
    timer_state = RunningTimer(accumulated=1.0, started_at=10.0)

    with pytest.raises(ValueError, match="Timestamp"):
        elapsed_time(timer_state, now=math.nan)

    with pytest.raises(ValueError, match="must not be earlier"):
        elapsed_time(timer_state, now=9.0)


def test_elapsed_time_rejects_unknown_timer_state() -> None:
    with pytest.raises(TypeError, match="Unsupported timer state"):
        elapsed_time(cast(TimerState, "not-a-timer"), now=1.0)


def test_timer_transitions_and_button_helpers() -> None:
    stopped = StoppedTimer(total=3.5)

    running = start_timer(stopped, now=10.0)
    assert running == RunningTimer(accumulated=3.5, started_at=10.0)
    assert is_running(stopped) is False
    assert is_running(running) is True
    assert visible_buttons(stopped) == (
        StopwatchButton.START,
        StopwatchButton.RESET,
    )
    assert visible_buttons(running) == (StopwatchButton.STOP,)
    assert default_button(stopped) is StopwatchButton.START
    assert default_button(running) is StopwatchButton.STOP

    stopped_again = stop_timer(running, now=12.25)
    assert stopped_again == StoppedTimer(total=5.75)

    assert reset_timer(stopped_again) == StoppedTimer()
