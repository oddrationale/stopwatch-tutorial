from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pytest
from textual import events
from textual.widgets import Button

from main import (
    RunningTimer,
    Stopwatch,
    StopwatchApp,
    StopwatchButton,
    StopwatchControl,
    StoppedTimer,
    TimeDisplay,
    format_time,
    start_timer,
    stop_timer,
)


def get_stopwatches(app: StopwatchApp) -> list[Stopwatch]:
    return list(app.query(Stopwatch))


def get_button(
    stopwatch: Stopwatch, button: StopwatchButton
) -> StopwatchControl:
    return stopwatch.query_one(f"#{button.value}", StopwatchControl)


async def click_widget_center(pilot, widget) -> None:
    region = widget.region
    await pilot.click(offset=(region.x + max(1, region.width // 2), region.y))


def test_app_actions_are_noops_without_a_selected_stopwatch(
    monkeypatch,
) -> None:
    app = StopwatchApp()
    monkeypatch.setattr(app, "get_selected_stopwatch", lambda: None)

    app.move_stopwatch_selection(-1)
    app.move_stopwatch_selection(1)
    app.action_focus_previous_button()
    app.action_focus_next_button()
    app.action_remove_stopwatch()


def test_toggle_dark_switches_between_themes() -> None:
    app = StopwatchApp()
    app.theme = "textual-dark"

    app.action_toggle_dark()
    assert app.theme == "textual-light"

    app.action_toggle_dark()
    assert app.theme == "textual-dark"


def test_stopwatch_on_click_ignores_button_clicks(monkeypatch) -> None:
    stopwatch = Stopwatch()
    focus_calls: list[str] = []

    def fake_focus_default() -> None:
        focus_calls.append("focused")

    monkeypatch.setattr(stopwatch, "focus_default", fake_focus_default)
    stopwatch.on_click(
        cast(
            events.Click,
            SimpleNamespace(
                widget=StopwatchControl("Start", id=StopwatchButton.START.value)
            ),
        )
    )

    assert focus_calls == []


def test_stopwatch_focus_event_helpers_delegate_correctly(monkeypatch) -> None:
    stopwatch = Stopwatch()
    selection_updates: list[str] = []
    deferred_callbacks: list[object] = []

    def fake_update_selection_state() -> None:
        selection_updates.append("updated")

    def fake_call_after_refresh(callback) -> bool:
        deferred_callbacks.append(callback)
        return True

    monkeypatch.setattr(
        stopwatch, "update_selection_state", fake_update_selection_state
    )
    monkeypatch.setattr(stopwatch, "call_after_refresh", fake_call_after_refresh)

    stopwatch.on_focus()
    stopwatch.on_descendant_focus()
    stopwatch.on_blur()
    stopwatch.on_descendant_blur()

    assert selection_updates == ["updated", "updated"]
    assert deferred_callbacks == [
        stopwatch.update_selection_state,
        stopwatch.update_selection_state,
    ]


def test_stopwatch_rejects_illegal_button_state_combinations() -> None:
    stopwatch = Stopwatch()

    with pytest.raises(RuntimeError, match="Button press does not match"):
        stopwatch.on_button_pressed(
            cast(
                Button.Pressed,
                SimpleNamespace(button=SimpleNamespace(id=StopwatchButton.STOP.value)),
            )
        )


@pytest.mark.asyncio
async def test_initial_tab_order_cycles_only_visible_buttons() -> None:
    app = StopwatchApp()

    async with app.run_test(size=(100, 40)) as pilot:
        stopwatches = get_stopwatches(app)
        expected_focus = [
            (0, StopwatchButton.START),
            (0, StopwatchButton.RESET),
            (1, StopwatchButton.START),
            (1, StopwatchButton.RESET),
            (2, StopwatchButton.START),
            (2, StopwatchButton.RESET),
            (0, StopwatchButton.START),
        ]

        for index, button in expected_focus:
            assert app.focused is get_button(stopwatches[index], button)
            await pilot.press("tab")


@pytest.mark.asyncio
async def test_keyboard_controls_start_stop_reset_and_focus_buttons() -> None:
    app = StopwatchApp()

    async with app.run_test(size=(100, 40)) as pilot:
        stopwatch = get_stopwatches(app)[0]

        await pilot.press("right")
        assert app.focused is get_button(stopwatch, StopwatchButton.RESET)

        await pilot.press("left")
        assert app.focused is get_button(stopwatch, StopwatchButton.START)

        await pilot.press("space")
        await pilot.pause()
        assert isinstance(stopwatch.timer_state, RunningTimer)
        assert app.focused is get_button(stopwatch, StopwatchButton.STOP)

        await pilot.press("left", "right")
        assert app.focused is get_button(stopwatch, StopwatchButton.STOP)

        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(stopwatch.timer_state, StoppedTimer)
        assert app.focused is get_button(stopwatch, StopwatchButton.START)

        await pilot.press("right", "space")
        await pilot.pause()
        assert stopwatch.timer_state == StoppedTimer()
        assert app.focused is get_button(stopwatch, StopwatchButton.START)
        assert stopwatch.query_one(TimeDisplay).value == format_time(
            stopwatch.timer_state.total
        )


@pytest.mark.asyncio
async def test_arrow_navigation_and_add_remove_actions_work_end_to_end() -> None:
    app = StopwatchApp()

    async with app.run_test(size=(100, 40)) as pilot:
        stopwatches = get_stopwatches(app)
        assert app.focused is get_button(stopwatches[0], StopwatchButton.START)

        await pilot.press("up")
        assert app.focused is get_button(stopwatches[0], StopwatchButton.START)

        await pilot.press("down")
        assert app.focused is get_button(stopwatches[1], StopwatchButton.START)

        await pilot.press("down")
        assert app.focused is get_button(stopwatches[2], StopwatchButton.START)

        await pilot.press("down")
        assert app.focused is get_button(stopwatches[2], StopwatchButton.START)

        await pilot.press("a")
        await pilot.pause()
        stopwatches = get_stopwatches(app)
        assert len(stopwatches) == 4
        assert app.focused is get_button(stopwatches[3], StopwatchButton.START)

        await pilot.press("r")
        await pilot.pause()
        stopwatches = get_stopwatches(app)
        assert len(stopwatches) == 3
        assert app.focused is get_button(stopwatches[2], StopwatchButton.START)


@pytest.mark.asyncio
async def test_mouse_selection_and_running_non_selected_timer_behave_correctly() -> None:
    app = StopwatchApp()

    async with app.run_test(size=(100, 40)) as pilot:
        first, second, _third = get_stopwatches(app)

        await click_widget_center(pilot, second.query_one(TimeDisplay))
        await pilot.pause()
        assert app.focused is get_button(second, StopwatchButton.START)
        assert app.get_selected_stopwatch() is second

        await click_widget_center(pilot, get_button(second, StopwatchButton.START))
        await pilot.pause()
        assert isinstance(second.timer_state, RunningTimer)
        assert app.focused is get_button(second, StopwatchButton.STOP)

        first.timer_state = start_timer(cast(StoppedTimer, first.timer_state), now=1.0)
        await pilot.pause()
        assert isinstance(first.timer_state, RunningTimer)
        assert app.focused is get_button(second, StopwatchButton.STOP)

        first.timer_state = stop_timer(first.timer_state, now=2.0)
        await pilot.pause()
        assert first.timer_state == StoppedTimer(total=1.0)


@pytest.mark.asyncio
async def test_get_selected_stopwatch_returns_none_when_focus_is_cleared() -> None:
    app = StopwatchApp()

    async with app.run_test(size=(100, 40)) as pilot:
        app.screen.set_focus(None)
        await pilot.pause()

        assert app.get_selected_stopwatch() is None


@pytest.mark.asyncio
async def test_focus_button_defaults_when_focus_is_outside_the_stopwatch() -> None:
    app = StopwatchApp()

    async with app.run_test(size=(100, 40)) as pilot:
        stopwatch = get_stopwatches(app)[0]
        app.screen.set_focus(None)
        await pilot.pause()

        stopwatch.focus_button(1)
        await pilot.pause()
        assert app.focused is get_button(stopwatch, StopwatchButton.START)


@pytest.mark.asyncio
async def test_removing_the_last_stopwatch_clears_selection() -> None:
    app = StopwatchApp()

    async with app.run_test(size=(100, 40)) as pilot:
        for remaining in (2, 1, 0):
            await pilot.press("r")
            await pilot.pause()
            assert len(get_stopwatches(app)) == remaining

        assert app.focused is None
        assert app.get_selected_stopwatch() is None
