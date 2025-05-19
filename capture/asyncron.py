from __future__ import annotations

import asyncio
import contextlib
import functools
import io
import locale
import os
import subprocess
import sys
import typing as t

if t.TYPE_CHECKING:
    from collections.abc import Generator
    from collections.abc import Sequence


@contextlib.contextmanager
def arguments(args) -> Generator[Sequence[str]]:

    if isinstance(args, str):
        yield args.split(" ", maxsplit=1)
    else:
        yield args


def default_encoding(
    executable: str | os.PathLike | None = None,
    **_,
) -> str:
    """
    Return cmd.exe encoding for windows when no executable is specified otherwise locale
    encoding for the platforms is returned.
    """

    return locale.getpreferredencoding(False)


def default_shell(
    executable: str | os.PathLike | None = None,
    **_,
) -> str | os.PathLike:
    """
    Return the default shell for the platform. If an executable is specified, it is
    returned.
    """

    if executable is not None:
        return executable

    if os.name == "nt":
        return os.environ.get("COMSPEC", "cmd.exe")
    else:
        return "/bin/sh"


class DecodeError(UnicodeDecodeError):
    def __init__(
        self,
        /,
        encoding: str,
        object: t.Any,
        start: int,
        end: int,
        reason: str,
        buffer: io.StringIO | io.BytesIO,
    ) -> None:
        super().__init__(encoding, object, start, end, reason)

        self._buffer = buffer

    @property
    def buffer(self) -> io.StringIO | io.BytesIO:
        return self._buffer


async def asyncio_run(
    args: subprocess._CMD,
    /,
    input: str | None = None,
    capture_output: bool = False,
    timeout: float | None = None,
    check: bool = False,
    *,
    shell: bool = False,
    text: bool = False,
    encoding: str | None = None,
    **kwargs,
) -> subprocess.CompletedProcess:
    # spawn the subprocess with separate pipes

    is_text = text or encoding is not None
    encoding = encoding or default_encoding()

    if capture_output:
        stdout = stderr = devnull = open(os.devnull, "w", encoding=encoding)
    else:
        stdout = sys.stdout
        stderr = sys.stderr

    async def reader(
        stream: asyncio.StreamReader,
        buf: io.StringIO | io.BytesIO,
        output: io.TextIOBase,
    ) -> None:

        while True:
            chunk = await stream.readline()
            if not chunk:
                break

            if is_text:
                buf.write(chunk.decode(encoding, errors="replace"))
            else:
                buf.write(chunk)

            output.write(chunk.decode("utf-8", errors="replace"))
            output.flush()

    async def writer(
        stream: asyncio.StreamWriter,
        input: str | bytes | None,
        encoding: str | None,
    ) -> None:

        if input is not None:
            if isinstance(input, str):
                input = input.encode(encoding)
            stream.write(input)
            await stream.drain()

        stream.close()
        await stream.wait_closed()

    stdout_buf = io.StringIO(newline=None) if is_text else io.BytesIO()
    stderr_buf = io.StringIO(newline=None) if is_text else io.BytesIO()

    if shell:
        proc = await asyncio.create_subprocess_shell(
            args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            **kwargs,
        )
    else:
        with arguments(args) as a:
            proc = await asyncio.create_subprocess_exec(
                *a,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                **kwargs,
            )

    tasks = [
        asyncio.create_task(reader(proc.stdout, stdout_buf, stdout)),
        asyncio.create_task(reader(proc.stderr, stderr_buf, stderr)),
        asyncio.create_task(writer(proc.stdin, input, encoding)),
    ]

    try:
        await asyncio.wait_for(proc.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await asyncio.gather(proc.wait(), *tasks, return_exceptions=True)
    else:
        timeout = None
        await asyncio.gather(*tasks, return_exceptions=True)

    finally:
        if capture_output:
            devnull.close()

        stdout = stdout_buf.getvalue()
        stderr = stderr_buf.getvalue()

    if timeout:
        raise subprocess.TimeoutExpired(
            args,
            float(timeout),
            output=stdout,
            stderr=stderr,
        )

    if check and proc.returncode != 0:
        raise subprocess.CalledProcessError(
            returncode=proc.returncode,
            cmd=args,
            output=stdout,
            stderr=stderr,
        )

    return subprocess.CompletedProcess(
        args=args,
        returncode=proc.returncode,
        stdout=stdout,
        stderr=stderr,
    )


@functools.wraps(subprocess.run)
def run(
    args: subprocess._CMD,
    *,
    input: str | None = None,
    capture_output: bool = False,
    timeout: float | None = None,
    check: bool = False,
    stdin: t.Literal[None] = None,
    stdout: t.Literal[None] = None,
    stderr: t.Literal[None] = None,
    bufsize: t.Literal[0] = 0,
    universal_newlines: t.Literal[False] = False,
    **kwargs,
) -> subprocess.CompletedProcess:
    """
    Run a command with the given arguments and return a CompletedProcess instance.
    This function is a wrapper around asyncio.create_subprocess_exec and
    asyncio.create_subprocess_shell.
    """

    if stdin is not None:
        raise ValueError("'stdin' is not supported, use 'input' argument.")

    if stdout is not None or stderr is not None:
        raise ValueError(
            "'stdout' and 'stderr' are not supported, use 'capture_output' argument."
        )

    if universal_newlines is not False:
        raise ValueError("'universal_newlines' is not supported, use 'text' instead.")

    if bufsize != 0:
        raise ValueError("'bufsize' is not supported.")

    return asyncio.run(
        asyncio_run(
            args,
            input=input,
            capture_output=capture_output,
            timeout=timeout,
            check=check,
            **kwargs,
        )
    )
