from __future__ import annotations

import subprocess
import sys
import typing as t

import pytest as p

import capture


@p.fixture(
    params=[None, "utf-8", "ansi", "cp850", "cp1252"],
    ids=lambda x: f"enc={x}",
)
def encoding(request: p.FixtureRequest) -> str | None:
    """Fixture to provide encoding parameter."""
    return request.param


@p.fixture(
    params=[
        ["echo", "ok"],
        ["echo", "nok", ";", "exit", "1"],
        ["echo", "☺ bright", ";", "exit", "0"],
        ["echo", "\u263b dark", ";", "exit", "1"],  # "☻"
        ["echo", "\U0001f680", ";", "echo", "rocket"],  # 🚀
    ],
    ids=[
        "echo=ok",
        "echo=nok",
        "echo=bright",
        "echo=dark",
        "echo=rocket",
    ],
)
def commands(request: p.FixtureRequest) -> list[str]:
    if sys.platform == "win32":
        return ["&" if x == ";" else x for x in request.param]
    else:
        return request.param


@p.fixture()
def runner(capfdbinary: p.CaptureFixture) -> t.Callable:
    """
    Returns a function which compares subprocess.run() and capture.run() output and
    return values.
    """

    def run(**kwargs):
        encoding = kwargs.get("encoding", None)
        _ = kwargs.pop("capture_output", None)
        lazy = kwargs.pop("lazy", False)

        sc = subprocess.run(
            capture_output=True, **kwargs
        )  # type: subprocess.CompletedProcess
        scap = capfdbinary.readouterr()

        s = subprocess.run(
            capture_output=False, **kwargs
        )  # type: subprocess.CompletedProcess
        ssys = capfdbinary.readouterr()

        c = capture.run(
            capture_output=False, lazy=lazy, **kwargs
        )  # type: subprocess.CompletedProcess
        csys = capfdbinary.readouterr()

        cc = capture.run(
            capture_output=True, lazy=lazy, **kwargs
        )  # type: subprocess.CompletedProcess
        ccap = capfdbinary.readouterr()

        assert sc.args == c.args == s.args == cc.args, "missmatch in arguments"
        assert (
            sc.returncode == c.returncode == s.returncode == cc.returncode
        ), "missmatch in returncode"

        assert scap.out == scap.err == b"", "subprocess.run() should be capture output"

        assert (
            sc.stdout == c.stdout == cc.stdout
        ), f"missmatch in cap stdout {encoding=}"
        assert (
            sc.stderr == c.stderr == cc.stderr
        ), f"missmatch in cap stderr {encoding=}"

        assert ssys.out == csys.out, f"missmatch in console output {encoding=}"
        assert ssys.err == csys.err, f"missmatch in console error {encoding=}"

        assert scap.out == ccap.out, f"missmatch in captured console output {encoding=}"
        assert scap.err == ccap.err, f"missmatch in captured console error {encoding=}"

    return run
