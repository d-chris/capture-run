from __future__ import annotations

import io
import subprocess
import sys
import threading
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from typing import Protocol

    class WritableStream(Protocol):
        def write(self, data: str | bytes) -> int: ...

        def getvalue(self) -> str | bytes: ...


class StreamIO:
    def __new__(
        cls,
        initial_value: bytes | str | None = None,
        /,
        newline: str | None = None,
        *,
        encoding: str | None = None,
        text: bool = False,
    ) -> WritableStream:
        if encoding is None and text is False:
            return io.BytesIO(initial_value)
        else:
            return io.StringIO(initial_value, newline)


def run(
    *args: subprocess._CMD,
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
        _file = file.write if is_text else file.buffer.write

        try:
            for line in iter(stream.read, sentinel):
                buffer.write(line)
                if not capture_output:
                    _file(line)
                    file.flush()
        finally:
            stream.close()

    process = subprocess.Popen(*args, **kwargs)

    threads = [
        threading.Thread(
            target=stream_reader,
            args=(process.stdout, stdout_buffer, sys.stdout),
        ),
        threading.Thread(
            target=stream_reader,
            args=(process.stderr, stderr_buffer, sys.stderr),
        ),
    ]

    for t in threads:
        t.start()

    if input is not None:
        if isinstance(input, str) and is_text:
            input = input.encode(encoding)
        process.stdin.write(input)
        process.stdin.close()

    try:
        process.wait(timeout)
    except subprocess.TimeoutExpired as e:
        process.kill()
        raise e
    finally:
        for t in threads:
            t.join()

    stdout_data = stdout_buffer.getvalue()
    stderr_data = stderr_buffer.getvalue()

    if check and process.returncode != 0:
        raise subprocess.CalledProcessError(
            process.returncode,
            process.args,
            output=stdout_data,
            stderr=stderr_data,
        )

    return subprocess.CompletedProcess(
        args=process.args,
        returncode=process.returncode,
        stdout=stdout_data,
        stderr=stderr_data,
    )
