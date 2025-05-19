import os
import typing as t

import pytest as p


@p.mark.parametrize("text", [True, False], ids=lambda x: f"txt={x}")
def test_run_exec(
    runner: t.Callable,
    commands: list[str],
    encoding: t.Optional[str],
    text: bool,
) -> None:

    kwargs = {
        "args": commands,
        "text": text,
        "encoding": encoding,
    }

    runner(**kwargs)


@p.mark.parametrize("text", [True, False], ids=lambda x: f"txt={x}")
@p.mark.parametrize("shell", [True, False], ids=lambda x: f"sh={x}")
def test_run_shell(
    runner: t.Callable,
    commands: list[str],
    encoding: t.Optional[str],
    text: bool,
    shell: bool,
) -> None:

    kwargs = {
        "args": " ".join(commands),
        "shell": shell,
        "text": text,
        "encoding": encoding,
    }

    runner(**kwargs)


def test_run_ping(runner: t.Callable) -> None:

    kwargs = {
        "args": "ping localhost -n 1" if os.name == "nt" else "ping -c 1 localhost",
        "shell": True,
    }

    runner(**kwargs)
