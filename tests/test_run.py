import subprocess

import pytest

from subprocess_run.run import run


@pytest.fixture(
    params=[
        ["echo", "ok"],
        ["echo", "nok", "&", "exit", "1"],
        ["echo", "✔ succeeded", "&", "exit", "0"],
        ["echo", "\u2718 failed", "&", "exit", "1"],  # "✘"
    ],
    ids=lambda x: " ".join(x),
)
def commands(request):
    return request.param


@pytest.mark.parametrize("text", [True, False])
@pytest.mark.parametrize("encoding", [None, "utf-8"])
@pytest.mark.parametrize("capture_output", [True, False])
def test_run_shell(capfd, commands, text, encoding, capture_output):

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


@pytest.mark.parametrize("text", [True, False])
@pytest.mark.parametrize("encoding", [None, "utf-8"])
@pytest.mark.parametrize("capture_output", [True, False])
def test_run(capfd, commands, text, encoding, capture_output):

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


def test_run_check():
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

    e = excinfo.value

    assert e.stderr == "nok\n"


def test_run_timeout():
    kwargs = {
        "args": [
            "python",
            "-c",
            "import time; print('timeout'); time.sleep(1)",
        ],
        "timeout": 0.1,
        "text": True,
    }

    with pytest.raises(subprocess.TimeoutExpired) as excinfo:
        _ = run(**kwargs)

    e = excinfo.value
    assert e.output == "timeout\n"


def test_run_input():
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
