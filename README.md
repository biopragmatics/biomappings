# biomappings

<a href="https://pypi.org/project/biomappings">
    <img alt="PyPI" src="https://img.shields.io/pypi/v/biomappings" />
</a>
<a href="https://pypi.org/project/biomappings">
    <img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/biomappings" />
</a>
<a href="https://github.com/biomappings/biomappings/blob/main/LICENSE">
    <img alt="PyPI - License" src="https://img.shields.io/pypi/l/biomappings" />
</a>
<a href="https://zenodo.org/badge/latestdoi/285352907">
    <img src="https://zenodo.org/badge/285352907.svg" alt="DOI">
</a>

Community curated and predicted equivalences and related mappings between named biological entities
that are not available from primary sources.

Human-curated mappings are in `src/biomappings/resources/mappings.tsv`, and
automatically predicated mappings are in `src/biomappings/resources/predictions.tsv`

Equivalences and related mappings that are available from the OBO Foundry and other
primary sources can be accessed through [Inspector Javert's Xref Database](https://zenodo.org/record/3757266)
on Zenodo which was described in [this blog post](https://cthoyt.com/2020/04/19/inspector-javerts-xref-database.html).

## ⬇️ Installation

The most recent release can be installed from
[PyPI](https://pypi.org/project/biomappings/) with:

```bash
$ pip install biomappings
```

The most recent code and data can be installed directly from
GitHub with:

```bash
$ pip install git+https://github.com/biomappings/biomappings.git
```

To install in development mode, use the following:

```bash
$ git clone git+https://github.com/biomappings/biomappings.git
$ cd biomappings
$ pip install -e .
```

## License

Code is licensed under the MIT License. Data is licensed under the CC0 1.0 Universal License.
