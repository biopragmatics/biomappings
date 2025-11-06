"""The biomappings CLI."""

from __future__ import annotations

from .resources import get_curator_names, get_current_curator
from .utils import DATA_DIRECTORY, DEFAULT_REPO, IMG_DIRECTORY
from .version import get_git_hash

main = DEFAULT_REPO.get_cli(
    enable_web=get_git_hash() is not None,
    get_user=get_current_curator,
    output_directory=DATA_DIRECTORY,
    sssom_directory=DATA_DIRECTORY.joinpath("sssom"),
    image_directory=IMG_DIRECTORY,
    get_orcid_to_name=get_curator_names,
)

if __name__ == "__main__":
    main()
