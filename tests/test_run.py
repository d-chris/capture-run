import subprocess

import pytest

from subprocess_run.run import run


@pytest.mark.parametrize(
    "kwargs",
    [
        {
            "args": "echo ok",
            "shell": True,
            "capture_output": True,
        },
        {
            "args": "echo nok & exit 1",
            "shell": True,
            "capture_output": True,
        },
        {
            "args": ["echo", "ok"],
            "capture_output": True,
        },
    ],
    ids=lambda x: repr(x),
)
@pytest.mark.parametrize("text", [True, False])
def test_run_capture_output(capfd, kwargs, text):

    a = subprocess.run(text=text, **kwargs)  # type: subprocess.CompletedProcess
    asys = capfd.readouterr()

    b = run(text=text, **kwargs)  # type: subprocess.CompletedProcess
    bsys = capfd.readouterr()

    assert asys == bsys
    assert (
        (a.returncode == b.returncode)
        and (a.args == b.args)
        and (a.stdout == b.stdout)
        and (a.stderr == b.stderr)
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {
            "args": "echo ok",
            "shell": True,
        },
        {
            "args": "echo nok & exit 1",
            "shell": True,
        },
        {
            "args": ["echo", "ok"],
        },
    ],
    ids=lambda x: repr(x),
)
@pytest.mark.parametrize("text", [True, False])
def test_run(capfd, kwargs, text):
    a = subprocess.run(text=text, **kwargs)  # type: subprocess.CompletedProcess
    asys = capfd.readouterr()

    b = run(text=text, **kwargs)  # type: subprocess.CompletedProcess
    bsys = capfd.readouterr()

    assert (a.returncode == b.returncode) and (a.args == b.args)
    assert (a.stdout is None) and (a.stderr is None)
    assert asys == bsys


@pytest.mark.parametrize(
    "kwargs",
    [
        {
            "args": "echo ok",
            "shell": True,
        },
        {
            "args": "echo nok & exit 1",
            "shell": True,
        },
        {
            "args": ["echo", "ok"],
        },
    ],
    ids=lambda x: repr(x),
)
def test_run_encoding(capfd, kwargs):
    a = subprocess.run(encoding="utf-8", **kwargs)  # type: subprocess.CompletedProcess
    asys = capfd.readouterr()

    b = run(encoding="utf-8", **kwargs)  # type: subprocess.CompletedProcess
    bsys = capfd.readouterr()

    assert (a.returncode == b.returncode) and (a.args == b.args)
    assert (a.stdout is None) and (a.stderr is None)
    assert asys == bsys
