from __future__ import annotations

import asyncio
import ctypes
import functools
import io
import locale
import os
import subprocess
import sys
from typing import Any


def default_encoding(
    executable: str | os.PathLike | None = None,
    **_,
) -> str:
    """
    Return cmd.exe encoding for windows when no executable is specified otherwise locale
    encoding for the platforms is returned.
    """

    if os.name == "nt" and executable is None:
        return f"cp{ctypes.windll.kernel32.GetConsoleOutputCP()}"
    else:
        return locale.getencoding()


def default_shell(
    executable: str | os.PathLike | None = None,
    **_,
) -> str | os.PathLike:
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
        object: Any,
        start: int,
        end: int,
        reason: str,
        buffer: io.StringIO | io.BytesIO,
    ) -> None:
        super().__init__(encoding, object, start, end, reason)

        self.buffer = buffer


async def asyncio_run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    # spawn the subprocess with separate pipes

    text = kwargs.pop("text", False)
    encoding = kwargs.pop("encoding", None)

    is_text = text or encoding is not None
    encoding = encoding or default_encoding()

    shell = kwargs.pop("shell", False)
    _ = kwargs.pop("bufsize", -1)

    timeout = kwargs.pop("timeout", None)
    capture_output = kwargs.pop("capture_output", False)
    check = kwargs.pop("check", False)

    if capture_output:
        stdout = stderr = devnull = open(os.devnull, "w")
    else:
        stdout = kwargs.pop("stdout", sys.stdout)
        stderr = kwargs.pop("stderr", sys.stderr)

    async def reader(
        stream: asyncio.StreamReader,
        buf: io.StringIO | io.BytesIO,
        output: io.TextIOBase,
    ) -> None:
        error: UnicodeDecodeError | None = None

        while True:
            chunk = await stream.readline()
            if not chunk:
                break

            try:
                s = chunk.decode(encoding, errors="strict" if text else "ignore")
            except UnicodeDecodeError as e:
                s = chunk.decode(default_encoding(), errors="replace")
                if error is None:
                    error = e

            if is_text:
                buf.write(s)
            else:
                buf.write(chunk)

            output.write(s)
            output.flush()

        if error is not None:
            raise DecodeError(
                encoding=error.encoding,
                object=error.object,
                start=error.start,
                end=error.end,
                reason=error.reason,
                buffer=buf,
            )

    stdout_buf = io.StringIO(newline=None) if is_text else io.BytesIO()
    stderr_buf = io.StringIO(newline=None) if is_text else io.BytesIO()

    if shell:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            **kwargs,
        )
    else:
        if isinstance(cmd, str):
            cmd = cmd.split(" ", maxsplit=1)

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            **kwargs,
        )

    tasks = [
        asyncio.create_task(reader(proc.stdout, stdout_buf, stdout)),
        asyncio.create_task(reader(proc.stderr, stderr_buf, stderr)),
    ]

    try:
        await asyncio.wait_for(proc.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        results = await asyncio.gather(proc.wait(), *tasks, return_exceptions=True)
    else:
        timeout = None
        results = await asyncio.gather(*tasks, return_exceptions=True)

    finally:
        if capture_output:
            devnull.close()

        for result in results:
            if isinstance(result, DecodeError):
                result.buffer.close()

        try:
            stdout = stdout_buf.getvalue()
            stderr = stderr_buf.getvalue()
        except ValueError:
            stdout = None
            stderr = None

    if timeout:
        raise subprocess.TimeoutExpired(
            cmd,
            float(timeout),
            output=stdout,
            stderr=stderr,
        )

    if check and proc.returncode != 0:
        raise subprocess.CalledProcessError(
            returncode=proc.returncode,
            cmd=cmd,
            output=stdout,
            stderr=stderr,
        )

    return subprocess.CompletedProcess(
        args=cmd,
        returncode=proc.returncode,
        stdout=stdout,
        stderr=stderr,
    )


@functools.wraps(subprocess.run)
def run(args, **kwargs) -> subprocess.CompletedProcess:

    if kwargs.get("input") is not None:
        if kwargs.get("stdin") is not None:
            raise ValueError("stdin and input arguments may not both be used.")
        kwargs["stdin"] = subprocess.PIPE

    if kwargs.get("capture_output") and ("stdout" in kwargs or "stderr" in kwargs):
        raise ValueError(
            "stdout and stderr arguments may not be used with capture_output."
        )

    return asyncio.run(asyncio_run(args, **kwargs))
