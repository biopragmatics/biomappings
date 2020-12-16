# -*- coding: utf-8 -*-

"""Utilities."""

import os
from subprocess import CalledProcessError, check_output  # noqa: S404
from typing import Optional


def get_git_hash() -> Optional[str]:
    """Get the git hash.

    :return:
        The git hash, equals 'UNHASHED' if encountered CalledProcessError, signifying that the
        code is not installed in development mode.
    """
    rv = _git('rev-parse', 'HEAD')
    if rv:
        return rv[:6]


def commit(message: str) -> Optional[str]:
    """Make a commit with the following message."""
    return _git('commit', '-m', message, '-a')


def _git(*args: str) -> Optional[str]:
    with open(os.devnull, 'w') as devnull:
        try:
            ret = check_output(  # noqa: S603,S607
                ['git', *args],
                cwd=os.path.dirname(__file__),
                stderr=devnull,
            )
        except CalledProcessError:
            return
        else:
            return ret.strip().decode('utf-8')
