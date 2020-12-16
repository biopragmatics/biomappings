# -*- coding: utf-8 -*-

"""Utilities."""

import os
from subprocess import CalledProcessError, check_output  # noqa: S404
from typing import Any, Mapping, Optional, Tuple


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


def get_script_url(fname: str) -> str:
    """Get the source path for this script.

    :param fname: Pass ``__file__`` as the argument to this function.
    :return: The script's URL to GitHub
    """
    commit_hash = get_git_hash()
    script_name = os.path.basename(fname)
    return f'https://github.com/biomappings/biomappings/blob/{commit_hash}/scripts/{script_name}'


def get_canonical_tuple(mapping: Mapping[str, Any]) -> Tuple[str, str, str, str]:
    """Get the canonical tuple from a mapping entry."""
    source = mapping['source prefix'], mapping['source identifier']
    target = mapping['target prefix'], mapping['target identifier']
    if source > target:
        source, target = target, source
    return (*source, *target)
