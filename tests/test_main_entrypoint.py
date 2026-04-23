from __future__ import annotations

import stopwatch_tutorial
import runpy


def test_package_root_exports_primary_entrypoints() -> None:
    assert stopwatch_tutorial.main.__module__ == "stopwatch_tutorial.cli"
    assert stopwatch_tutorial.StopwatchApp.__module__ == "stopwatch_tutorial.ui.app"


def test_running_package_dunder_main_starts_the_app(monkeypatch) -> None:
    run_calls: list[str] = []

    def fake_run(self) -> None:
        run_calls.append(self.__class__.__name__)

    monkeypatch.setattr("textual.app.App.run", fake_run)

    runpy.run_module("stopwatch_tutorial.__main__", run_name="__main__")

    assert run_calls == ["StopwatchApp"]
