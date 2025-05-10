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


def stream_reader_text(
    stream: io.BufferedReader,
    buffer: io.StringIO,
    file: io.TextIOWrapper,
    /,
    *,
    capture_output: bool,
    encoding: str,
) -> None:
    try:
        for line in iter(stream.read, b""):
            decoded_line = line.decode(encoding)
            buffer.write(decoded_line)
            if not capture_output:
                file.write(decoded_line)
                file.flush()
    finally:
        stream.close()


def stream_reader_binary(
    stream: io.BufferedReader,
    buffer: io.BytesIO,
    file: io.TextIOWrapper,
    /,
    *,
    capture_output: bool,
    **_: Any,
) -> None:
    try:
        for line in iter(stream.read, b""):
            buffer.write(line)
            if not capture_output:
                file.buffer.write(line)
                file.flush()
    finally:
        stream.close()


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

    # Always use binary mode for Popen
    kwargs["text"] = False
    kwargs["encoding"] = None
    kwargs["stdout"] = subprocess.PIPE
    kwargs["stderr"] = subprocess.PIPE

    stdout_buffer = StreamIO(text=is_text)
    stderr_buffer = StreamIO(text=is_text)

    thread_reader = stream_reader_text if is_text else stream_reader_binary
    thread_kwargs = {
        "capture_output": capture_output,
        "encoding": encoding,
    }

    process = subprocess.Popen(*args, **kwargs)

    threads = [
        threading.Thread(
            target=thread_reader,
            args=(process.stdout, stdout_buffer, sys.stdout),
            kwargs=thread_kwargs,
        ),
        threading.Thread(
            target=thread_reader,
            args=(process.stderr, stderr_buffer, sys.stderr),
            kwargs=thread_kwargs,
        ),
    ]

    for t in threads:
        t.start()

    if input is not None:
        if isinstance(input, str):
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
