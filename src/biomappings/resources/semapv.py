"""Tools for semapv."""

from functools import lru_cache

import pystow

__all__ = [
    "get_semapv",
]

url = "https://raw.githubusercontent.com/mapping-commons/semantic-mapping-vocabulary/main/semapv-terms.tsv"


@lru_cache(1)
def get_semapv():
    df = pystow.ensure_csv(
        "bio",
        "semapv",
        url=url,
        read_csv_kwargs=dict(
            usecols=[0, 1],
            skiprows=1,
        ),
    )
    df["ID"] = df["ID"].map(lambda s: s.removeprefix("semapv:"))
    return dict(df.values)
