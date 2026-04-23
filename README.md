# Stopwatch Tutorial

[![codecov](https://codecov.io/github/oddrationale/stopwatch-tutorial/branch/main/graph/badge.svg)](https://app.codecov.io/github/oddrationale/stopwatch-tutorial)

A small [Textual](https://textual.textualize.io/) stopwatch app with multiple timers and keyboard-first navigation.

## Requirements

- Python `3.13+`
- `uv`

## Setup

```bash
uv sync
```

To install the local Git hooks:

```bash
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
```

## Run

```bash
uv run stopwatch-tutorial
```

For Textual's live dev mode:

```bash
uv run textual run --dev stopwatch_tutorial.ui.app:StopwatchApp
```

You can also run the packaged module directly:

```bash
uv run python -m stopwatch_tutorial
```

## Install With `uv tool`

If you want the command installed on your `PATH`, use `uv tool install`:

```bash
uv tool install git+https://github.com/oddrationale/stopwatch-tutorial
stopwatch-tutorial
```

## Run With `uvx`

If you want to run it without installing anything, use `uvx`:

```bash
uvx --from git+https://github.com/oddrationale/stopwatch-tutorial stopwatch-tutorial
```

## Features

- Multiple independent stopwatches
- Add and remove timers from the app
- Keyboard and mouse friendly controls

## Controls

- `Tab`: move between visible stopwatch buttons
- `Shift+Tab`: move backwards through visible stopwatch buttons
- `Enter` or `Space`: press the focused button
- `Up` / `Down`: move between stopwatches
- `Left` / `Right`: move between visible buttons in the selected stopwatch
- `a`: add a stopwatch
- `r`: remove the selected stopwatch
- `d`: toggle light/dark theme

## Validation

Run the project checks with:

```bash
uv run ruff check .
uv run ty check
uv run pytest
```

The pytest configuration enforces `100%` coverage for `stopwatch_tutorial`.

GitHub Actions also uploads the generated `coverage.xml` report to Codecov.

## Git Hooks

This project uses `pre-commit`:

- `pre-commit`: `ruff format`, `ruff check`
- `pre-push`: `ty check`, `pytest`

Run all hooks manually with:

```bash
uv run pre-commit run --all-files
uv run pre-commit run --hook-stage pre-push --all-files
```
