from __future__ import annotations

import sys

import pytest as p


@p.fixture(
    params=[None, "utf-8", "ansi", "cp850", "cp1252"],
    ids=lambda x: f"enc={x}",
)
def encoding(request: p.FixtureRequest) -> str | None:
    """Fixture to provide encoding parameter."""
    return request.param


@p.fixture(
    params=[
        ["echo", "ok"],
        ["echo", "nok", ";", "exit", "1"],
        ["echo", "☺ bright", ";", "exit", "0"],
        ["echo", "\u263b dark", ";", "exit", "1"],  # "☻"
        ["echo", "\U0001f680", ";", "echo", "rocket"],  # 🚀
    ],
    ids=[
        "echo=ok",
        "echo=nok",
        "echo=bright",
        "echo=dark",
        "echo=rocket",
    ],
)
def commands(request: p.FixtureRequest) -> list[str]:
    if sys.platform == "win32":
        return ["&" if x == ";" else x for x in request.param]
    else:
        return request.param
