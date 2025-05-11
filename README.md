# capture-run

[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/capture-run)](https://pypi.org/project/capture-run/)
[![PyPI - Version](https://img.shields.io/pypi/v/capture-run)](https://pypi.org/project/capture-run/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/capture-run)](https://pypi.org/project/capture-run/)
[![PyPI - License](https://img.shields.io/pypi/l/capture-run)](https://raw.githubusercontent.com/d-chris/capture-run/main/LICENSE)
[![GitHub - Pytest](https://img.shields.io/github/actions/workflow/status/d-chris/capture-run/pytest.yml?logo=github&label=pytest)](https://github.com/d-chris/capture-run/actions/workflows/pytest.yml)
[![GitHub - Release](https://img.shields.io/github/v/tag/d-chris/capture-run?logo=github&label=github)](https://github.com/d-chris/capture-run)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://raw.githubusercontent.com/d-chris/capture-run/main/.pre-commit-config.yaml)

<!-- [![GitHub - Page](https://img.shields.io/website?url=https%3A%2F%2Fd-chris.github.io%2Fcapture-run&up_message=pdoc&logo=github&label=documentation)](https://d-chris.github.io/capture-run) -->
<!-- [![codecov](https://codecov.io/gh/d-chris/capture-run/graph/badge.svg?token=WY062DFVTR)](https://codecov.io/gh/d-chris/capture-run) -->
---

A drop-in replacement for `subprocess.run` that captures stdout and stderr while also displaying output live in the console.

## Installation

```cmd
pip install capture-run
```

## Usage

```doctest
>>> from capture import run

>>> run("echo $ bytes")
$ bytes
CompletedProcess(args='echo $ bytes', returncode=0, stdout=b'$ bytes\r\n', stderr=b'')

>>> run("echo $ text", text=True)
$ text
CompletedProcess(args='echo $ text', returncode=0, stdout='$ text\n', stderr='')

>>> run("echo $ captured", capture_output=True, encoding="utf-8")
CompletedProcess(args='echo $ captured', returncode=0, stdout='$ captured\n', stderr='')
```
