from __future__ import annotations

import runpy


def test_running_main_module_starts_the_app(monkeypatch) -> None:
    run_calls: list[str] = []

    def fake_run(self) -> None:
        run_calls.append(self.__class__.__name__)

    monkeypatch.setattr("textual.app.App.run", fake_run)

    runpy.run_module("main", run_name="__main__")

    assert run_calls == ["StopwatchApp"]
