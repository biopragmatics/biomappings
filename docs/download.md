---
layout: page
title: Download
permalink: /download/
---
The biomappings database can be downloaded directly
from [GitHub](https://github.com/biopragmatics/biomappings/tree/master/src/biomappings/resources).

## License

The manually curated portions of these data are available under the
[CC0 1.0 Universal License](https://github.com/biopragmatics/biomappings/blob/master/LICENSE).

## Programmatic Access


There are three main functions exposed from `biomappings`. Each loads a list of dictionaries with the mappings in each.

```python
import biomappings

true_mappings = biomappings.load_mappings()

false_mappings = biomappings.load_false_mappings()

predictions = biomappings.load_predictions()
```

Alternatively, you can use the above links to the TSVs on GitHub in with the library or programming language of your
choice.

The data can also be loaded as [networkx](https://networkx.org/) graphs with the following functions:

```python
import biomappings

true_graph = biomappings.get_true_graph()

false_graph = biomappings.get_false_graph()

predictions_graph = biomappings.get_predictions_graph()
```

The source code can be found at
[https://github.com/biopragmatics/biomappings](https://github.com/biopragmatics/biomappings).
It is licensed under the MIT License.
