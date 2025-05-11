from __future__ import annotations

import os
import subprocess
import sys

import pytest

from capture import run


def coverage() -> bool:
    """Check if the code is running under coverage."""
    return os.environ.get("COVERAGE_PROCESS_START") or os.environ.get("COV_CORE_SOURCE")


@pytest.fixture(
    params=[
        ["echo", "ok"],
        ["echo", "nok", ";", "exit", "1"],
        pytest.param(
            ["echo", "☺ bright", ";", "exit", "0"],
            marks=pytest.mark.xfail(
                sys.platform == "win32", reason="cp850 not guaranteed supported on Win"
            ),
        ),
        pytest.param(
            ["echo", "\u263b dark", ";", "exit", "1"],  # "☻"
            marks=pytest.mark.xfail(
                sys.platform == "win32", reason="cp850 not guaranteed supported on Win"
            ),
        ),
    ],
    ids=repr,
)
def commands(request: pytest.FixtureRequest) -> list[str]:
    if sys.platform == "win32":
        return ["&" if x == ";" else x for x in request.param]
    else:
        return request.param


@pytest.mark.parametrize("text", [True, False], ids=lambda x: f"txt={x}")
@pytest.mark.parametrize("encoding", [None, "utf-8"], ids=lambda x: f"enc={x}")
@pytest.mark.parametrize("capture_output", [True, False], ids=lambda x: f"cap={x}")
def test_run_shell(
    capfd: pytest.CaptureFixture,
    commands: list[str],
    text: bool,
    encoding: str | None,
    capture_output: bool,
) -> None:

    kwargs = {
        "args": " ".join(commands),
        "shell": True,
        "text": text,
        "capture_output": capture_output,
        "encoding": encoding,
    }

    a = subprocess.run(**kwargs)  # type: subprocess.CompletedProcess
    asys = capfd.readouterr()

    b = run(**kwargs)  # type: subprocess.CompletedProcess
    bsys = capfd.readouterr()

    assert asys == bsys

    assert (a.returncode == b.returncode) and (a.args == b.args)

    if capture_output:
        assert (a.stdout == b.stdout) and (a.stderr == b.stderr)
    else:
        assert (a.stdout is None) and (a.stderr is None)
        assert (b.stdout is not None) and (b.stderr is not None)


@pytest.mark.parametrize("text", [True, False], ids=lambda x: f"txt={x}")
@pytest.mark.parametrize("encoding", [None, "utf-8"], ids=lambda x: f"enc={x}")
@pytest.mark.parametrize("capture_output", [True, False], ids=lambda x: f"cap={x}")
def test_run(
    capfd: pytest.CaptureFixture,
    commands: list[str],
    text: bool,
    encoding: str | None,
    capture_output: bool,
) -> None:

    kwargs = {
        "args": commands,
        "shell": False,
        "text": text,
        "capture_output": capture_output,
        "encoding": encoding,
    }

    a = subprocess.run(**kwargs)  # type: subprocess.CompletedProcess
    asys = capfd.readouterr()

    b = run(**kwargs)  # type: subprocess.CompletedProcess
    bsys = capfd.readouterr()

    assert asys == bsys

    assert (a.returncode == b.returncode) and (a.args == b.args)

    if capture_output:
        assert (a.stdout == b.stdout) and (a.stderr == b.stderr)
    else:
        assert (a.stdout is None) and (a.stderr is None)
        assert (b.stdout is not None) and (b.stderr is not None)


def test_run_check() -> None:
    kwargs = {
        "args": [
            "python",
            "-c",
            "import sys; print('nok', file=sys.stderr); sys.exit(1)",
        ],
        "check": True,
        "text": True,
    }

    with pytest.raises(subprocess.CalledProcessError) as excinfo:
        _ = run(**kwargs)

    e = excinfo.value  # type: subprocess.CalledProcessError

    assert e.stderr == "nok\n"


def test_run_timeout() -> None:
    kwargs = {
        "args": [
            "python",
            "-c",
            "import time; print('timeout', flush=True); time.sleep(1)",
        ],
        "timeout": 0.1,
        "text": True,
    }

    with pytest.raises(subprocess.TimeoutExpired) as excinfo:
        _ = run(**kwargs)

    if not coverage():
        e = excinfo.value  # type: subprocess.TimeoutExpired
        assert e.output == "timeout\n"


def test_run_input() -> None:
    kwargs = {
        "args": [
            "python",
            "-c",
            "print(input())",
        ],
        "input": "ok",
        "text": True,
        "capture_output": True,
    }

    a = subprocess.run(**kwargs)  # type: subprocess.CompletedProcess
    b = run(**kwargs)  # type: subprocess.CompletedProcess

    assert a.stdout == b.stdout == "ok\n"


@pytest.mark.parametrize(
    "kwargs",
    [
        {
            "input": "ok",
            "stdin": sys.stdin,
        },
        {
            "capture_output": True,
            "stdout": sys.stdout,
        },
        {
            "capture_output": True,
            "stderr": sys.stderr,
        },
    ],
    ids=[
        "input+stdin",
        "capture_output+stdout",
        "capture_output+stderr",
    ],
)
def test_run_valueerror(kwargs) -> None:

    with pytest.raises(ValueError):
        _ = run(["echo", "ok"], **kwargs)
