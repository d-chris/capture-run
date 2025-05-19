import pytest as p
import subprocess
from capture import run


@p.mark.parametrize("text", [True, False], ids=lambda x: f"txt={x}")
@p.mark.parametrize("shell", [True, False], ids=lambda x: f"sh={x}")
def test_run_shell(
    capfdbinary: p.CaptureFixture,
    commands: list[str],
    encoding: str | None,
    text: bool,
    shell: bool,
) -> None:

    kwargs = {
        "args": " ".join(commands),
        "shell": shell,
        "text": text,
        "encoding": encoding,
    }

    a = subprocess.run(
        capture_output=True, **kwargs
    )  # type: subprocess.CompletedProcess
    asys = capfdbinary.readouterr()

    c = subprocess.run(
        capture_output=False, **kwargs
    )  # type: subprocess.CompletedProcess
    csys = capfdbinary.readouterr()

    b = run(capture_output=False, **kwargs)  # type: subprocess.CompletedProcess
    bsys = capfdbinary.readouterr()

    d = run(capture_output=True, **kwargs)  # type: subprocess.CompletedProcess
    dsys = capfdbinary.readouterr()

    assert a.args == b.args == c.args == d.args, "missmatch in arguments"
    assert (
        a.returncode == b.returncode == c.returncode == d.returncode
    ), "missmatch in returncode"

    assert asys.out == asys.err == b"", "subprocess.run() should be capture output"

    assert a.stdout == b.stdout == d.stdout, f"missmatch in captured stdout {encoding=}"
    assert a.stderr == b.stderr == d.stderr, f"missmatch in captured stderr {encoding=}"

    assert csys.out == bsys.out, f"missmatch in console output {encoding=}"
    assert csys.err == bsys.err, f"missmatch in console error {encoding=}"

    assert asys.out == dsys.out, f"missmatch in captured console output {encoding=}"
    assert asys.err == dsys.err, f"missmatch in captured console error {encoding=}"
