from pathlib import Path
import itertools as itt
from typing import Callable
from more_itertools import chunked
CLASSES_LINE = "#   Classes"


def _split(line: str) -> bool:
    return line.startswith(CLASSES_LINE)


def _sw(k: str) -> Callable[[str], bool]:
    return lambda line: line.startswith(k)


def main():
    path = Path("/Users/cthoyt/dev/human-phenotype-ontology/src/ontology/hp-edit.owl")
    raw_lines = path.read_text().splitlines()
    idx = next(
        i
        for i, line in enumerate(raw_lines)
        if line.startswith(CLASSES_LINE)
    )
    preamble_lines = raw_lines[:idx + 3]
    lines = raw_lines[idx + 3:]

    itttt = itt.groupby(lines[:10], key=_sw("# Class:"))
    for _, l in itttt:


    i = 0
    for (a, k), (b, v) in chunked(itttt, 2):
        print(a, list(k), b, list(v))
        i += 1
        if i > 10:
            break


if __name__ == '__main__':
    main()
