# capture-run

A drop-in replacement for `subprocess.run` that captures stdout and stderr while also displaying output live in the console.

## Installation

```cmd
pip install capture-run
```

## Usage

```doctest
>>> from capture_run import run

>>> run("echo $ bytes")
$ bytes
CompletedProcess(args='echo $ bytes', returncode=0, stdout=b'$ bytes\r\n', stderr=b'')

>>> run("echo $ text", text=True)
$ text
CompletedProcess(args='echo $ text', returncode=0, stdout='$ text\n', stderr='')

>>> run("echo $ captured", capture_output=True, encoding="utf-8")
CompletedProcess(args='echo $ captured', returncode=0, stdout='$ captured\n', stderr='')
```
