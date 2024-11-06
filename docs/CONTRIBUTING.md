---
layout: page
title: Contributing
permalink: /contributing/
---
Contributions to Biomappings are welcomed and encouraged. Thanks for
considering to participate.

All contributors, maintainers, and participants of the Biomappings project
are expected to follow our [Code of Conduct](CODE_OF_CONDUCT.md).
This document is organized as follows:

1. [Content Contribution](#content-contribution)
2. [Code Contribution](#code-contribution)

## Content Contribution

There are several ways to add new content to Biomappings:

1. Write a script that automatically generates new mappings
2. Curate mappings using the local web application
3. Suggest curations in the issue tracker

### Who Can Add New Mappings

New mappings can be added by anyone, even if they are for a resource they
do not themselves maintain. A main goal of Biomappings is to fill in the
gaps left by primary curation projects, so expertise is welcome from
anywhere.

### Requirements for New Mappings

1. Mappings must use canonical Bioregistry prefixes and local unique identifier
   standards
2. Mappings should not duplicate previously curated work (e.g., from primary resources or other Biomappings curations)
3. Mappings should be one-to-one between vocabularies when possible
4. Mappings should be properly attributed with ORCID for manual curation or provenance to a script if automatically
   generated.

### Editing Mappings

Sometimes, it becomes clear that a mapping was not correct. If this is the case,
then anyone is free to turn a manually curated mapping into an incorrect
mapping.
However, the original contributor should be contacted (which should be possible
via the `git blame` feature on GitHub as well as the ORCID identifier
annotation).

Currently, Biomappings uses a simple format and does not track full change
history for each mapping. Therefore, the ORCID identifier should be overwritten
by the last person to make a manual curation to the mapping.

### Review of Additions and Edits

Review of edits to existing records is handled by the Biomappings Review Team,
whose membership and conduct is described in the Biomappings's
[Project Governance](GOVERNANCE.md).

## Code Contribution

See the CONTRIBUTING.md file in the GitHub Repository.