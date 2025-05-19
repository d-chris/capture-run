from __future__ import annotations

import os
import subprocess
import sys

import pytest

from capture import run


def coverage() -> bool:
    """Check if the code is running under coverage."""
    return os.environ.get("COVERAGE_PROCESS_START") or os.environ.get("COV_CORE_SOURCE")


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
        "timeout": 3,
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
        {
            "universal_newlines": True,
            "text": False,
        },
        {
            "bufsize": -1,
        },
    ],
    ids=[
        "input+stdin",
        "capture_output+stdout",
        "capture_output+stderr",
        "universal_newlines+text",
        "bufsize",
    ],
)
def test_run_valueerror(kwargs) -> None:

    with pytest.raises(ValueError):
        _ = run(["echo", "ok"], **kwargs)


def test_run_python(capfd, tmp_path) -> None:

    script = tmp_path / "echo.py"
    script.write_text("print('😊')\n", encoding="utf-8")

    kwargs = {
        "args": ["python", script],
        # "encoding": "cp850",
        "executable": sys.executable,
        "capture_output": True,
    }

    a = subprocess.run(**kwargs)  # type: subprocess.CompletedProcess
    asys = capfd.readouterr()

    b = run(**kwargs)  # type: subprocess.CompletedProcess
    bsys = capfd.readouterr()

    assert asys.out == bsys.out
    assert a.stdout == b.stdout
    assert a.returncode == b.returncode
