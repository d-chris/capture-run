from __future__ import annotations

import io
import subprocess
import sys
import threading
from contextlib import ExitStack
from typing import Any


class StreamIO:
    def __new__(
        cls,
        initial_value: bytes | str | None = None,
        /,
        newline: str | None = None,
        *,
        encoding: str | None = None,
        text: bool = False,
    ):
        if encoding is None and text is False:
            return io.BytesIO(initial_value)
        else:
            return io.StringIO(initial_value, newline)


def run(
    *popenargs: subprocess._CMD,
    input: str | None = None,
    capture_output: bool = False,
    timeout: float = None,
    check: bool = False,
    **kwargs: Any,
) -> subprocess.CompletedProcess:

    if input is not None:
        if kwargs.get("stdin") is not None:
            raise ValueError("stdin and input arguments may not both be used.")
        kwargs["stdin"] = subprocess.PIPE

    if capture_output and ("stdout" in kwargs or "stderr" in kwargs):
        raise ValueError(
            "stdout and stderr arguments may not be used with capture_output."
        )

    is_text = kwargs.get("text", False) or bool(kwargs.get("encoding", None))
    encoding = kwargs.get("encoding", sys.getdefaultencoding())
    kwargs["stdout"] = subprocess.PIPE
    kwargs["stderr"] = subprocess.PIPE

    if is_text:
        kwargs["bufsize"] = 1

    stdout_buffer = StreamIO(text=is_text)
    stderr_buffer = StreamIO(text=is_text)

    def stream_reader(
        stream: io.BufferedReader,
        buffer: io.BytesIO | io.StringIO,
        file: io.TextIOWrapper,
    ) -> None:
        sentinel = "" if is_text else b""
        writer = file.write if is_text else file.buffer.write

        try:
            for line in iter(stream.readline, sentinel):
                buffer.write(line)
                if not capture_output:
                    writer(line)
                    file.flush()
        finally:
            stream.close()

    with subprocess.Popen(*popenargs, **kwargs) as process:
        try:
            with ExitStack() as stack:
                threads = [
                    stack.enter_context(
                        threading.Thread(
                            target=stream_reader,
                            args=(process.stdout, stdout_buffer, sys.stdout),
                        )
                    ),
                    stack.enter_context(
                        threading.Thread(
                            target=stream_reader,
                            args=(process.stderr, stderr_buffer, sys.stderr),
                        )
                    ),
                ]

                for t in threads:
                    t.start()

                if input is not None:
                    if isinstance(input, str) and is_text:
                        input = input.encode(encoding)
                    process.stdin.write(input)
                    process.stdin.close()

                process.wait(timeout)

        except subprocess.TimeoutExpired as exc:
            process.kill()
            exc.stdout, exc.stderr = process.communicate()
            raise
        except BaseException:
            process.kill()
            raise
        finally:
            for t in threads:
                t.join()

        retcode = process.poll()
        stdout = stdout_buffer.getvalue()
        stderr = stderr_buffer.getvalue()

        if check and retcode:
            raise subprocess.CalledProcessError(
                retcode,
                process.args,
                output=stdout,
                stderr=stderr,
            )

    return subprocess.CompletedProcess(process.args, retcode, stdout, stderr)
