from biomappings.resources import (
    TRUE_MAPPINGS_PATH, FALSE_MAPPINGS_PATH, PREDICTIONS_PATH, UNSURE_PATH,
    MAPPINGS_HEADER,
)
import csv


def main():
    for path in [TRUE_MAPPINGS_PATH, FALSE_MAPPINGS_PATH, UNSURE_PATH]:
        rows = []
        with open(path, "r") as fh:
            reader = csv.reader(fh, delimiter="\t")
            header = next(reader)
            if header == MAPPINGS_HEADER:
                print(f"no need to re-write {path}")
                continue
            rows.append(MAPPINGS_HEADER)
            for *row, reviewer in reader:
                rows.append((*row, "", "", reviewer))

        with open(path, "w") as fh:
            for line in rows:
                print(*line, sep="\t", file=fh)

    with open(PREDICTIONS_PATH, "r") as fh:
        prediction_reader = csv.reader(fh, delimiter="\t")
        _header = next(prediction_reader)
        prediction_rows = [MAPPINGS_HEADER]
        for prediction_row in prediction_reader:
            prediction_rows.append((*prediction_row, ""))
    with open(PREDICTIONS_PATH, "w") as fh:
        for line in prediction_rows:
            print(*line, sep="\t", file=fh)


if __name__ == '__main__':
    main()
