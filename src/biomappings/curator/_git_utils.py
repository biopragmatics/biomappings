"""Reusable git code."""

from __future__ import annotations


def _git(*args: str) -> str | None:
    import os
    from subprocess import CalledProcessError, check_output

    with open(os.devnull, "w") as devnull:
        try:
            ret = check_output(  # noqa: S603
                ["git", *args],  # noqa:S607
                cwd=os.path.dirname(__file__),
                stderr=devnull,
            )
        except CalledProcessError as e:
            print(e)  # noqa:T201
            return None
        else:
            return ret.strip().decode("utf-8")
