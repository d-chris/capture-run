import os
import shutil
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


@p.mark.parametrize("text", [True, False], ids=lambda x: f"txt={x}")
@p.mark.parametrize(
    "args",
    [
        "ping localhost -n 1" if os.name == "nt" else "ping -c 1 localhost",
        "python --version",
        "git --version",
    ],
    ids=lambda x: x.split()[0],
)
def test_run_tools(runner: t.Callable, args: str, text: bool) -> None:

    executable = shutil.which(args.split()[0])

    if executable is None:
        p.skip(f"tool not found: {args}")

    kwargs = {
        "args": args,
        "shell": True,
        "text": text,
        "lazy": True,
    }

    runner(**kwargs)
