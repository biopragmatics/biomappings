"""Tools for semapv."""

import json
from functools import lru_cache
from pathlib import Path

__all__ = [
    "get_semapv",
]

url = "https://raw.githubusercontent.com/mapping-commons/semantic-mapping-vocabulary/main/semapv-terms.tsv"
HERE = Path(__file__).parent.resolve()
PATH = HERE.joinpath("semapv.json")


@lru_cache(1)
def get_semapv():
    """Get a dictionary of semapv local unique identifier to labels."""
    if PATH.is_file():
        return json.loads(PATH.read_text())

    import pystow

    df = pystow.ensure_csv(
        "bio",
        "semapv",
        url=url,
        read_csv_kwargs={
            "usecols": [0, 1],
            "skiprows": 1,
        },
    )
    df["ID"] = df["ID"].map(lambda s: s.removeprefix("semapv:"))
    rv = dict(df.values)
    PATH.write_text(json.dumps(rv, indent=True, sort_keys=True))
    return rv


if __name__ == "__main__":
    get_semapv()
