---
layout: page
title: Governance
permalink: /governance/
---

The goal of the Biomappings project is to enable community-driven curation and maintenance of semantic mappings between
ontology and database terms, either to fill in the gaps in existing direct first-party mappings (e.g., DOID to MeSH) or
where no direct first-party mappings exist (e.g., MeSH to ChEBI).

## Manually Updating Biomappings

- Manual updates to the contents of the Biomappings project (e.g., adding new predictions, curating predictions, adding
  novel mappings) must be done either in the form of an issue or a pull request.
- Manual updates can be accepted if all continuous integration tests pass and a member of the Biomappings Review Team
  approves. It's best practice that a member of the Biomappings Review Team does not approve their own updates, but this
  is optional.
- Mappings should conform to the Bioregistry standard and the [contribution guidelines](CONTRIBUTING.md)

## Review Team

The *Review Team* is responsible for reviewing requests for new mappings (both predictions and manual
curations).

### Membership

- Membership to the Review Team is requested on the issue tracker.
- Membership to the Review Team is granted at the discretion of the existing Review Team using Disapproval Voting.
- Members must join and participate the OBO Foundry Slack.
- Members must be listed alphabetically by family name below

### Member Onboarding

- Add to the GitHub review team (note that GitHub hasn't yet enabled teams to be publicly viewed, and this link
  currently results in a 404 error)
- Add to membership list below in alphabetical order by last name in along with their GitHub handle, ORCID identifier,
  and date of joining.

### Removing Members

- Members who unresponsive for 3 or more months can be removed by another member of the Review Team
- Members who do not conduct themselves according to the [Code of Conduct](CODE_OF_CONDUCT.md) can be suggested to be
  removed by a member of the Review Team.

### Member Offboarding

- Remove from the the GitHub review team (note that GitHub hasn't yet enabled teams to be publicly viewed, and this link currently results in a 404 error)
- Add the date of exit and move their name and information ot the previous members list.

### Members

- Benjamin M. Gyori (@bgyori; https://orcid.org/0000-0001-9439-5346; joined 2020-08-05)
- Charles Tapley Hoyt (@cthoyt; https://orcid.org/0000-0003-4423-4370; joined 2020-08-05)

### Previous Members

We're a new team and don't have any yet!

## Development Team

The *Development Team* is responsible for maintaining the codebase associated with the project, which includes the Python package, the web curation application, and related GitHub repositories. It is implemented as a GitHub team that has "maintain" permissions (e.g., able to write to the repo as well as maintain issues and pull requests).

Contributions to the project code must be submitted as pull requests to https://github.com/biopragmatics/biomappings. They must conform to the [contribution guidelines](CONTRIBUTING.md). Code contributions must be approved by a member of the Development Team as well as pass continuous integration tests before merging.

## Membership

Membership admission, onboarding, removal, and offboarding work the same as for the Review Team, except it is required that a potential member of the Development Team has previously made a contribution as an external contributor (to which there are no requirements).

### Members

- Benjamin M. Gyori (@bgyori; https://orcid.org/0000-0001-9439-5346; joined 2020-08-05)
- Charles Tapley Hoyt (@cthoyt; https://orcid.org/0000-0003-4423-4370; joined 2020-08-05)

### Previous Members

We're a new team and don't have any yet!

## Publications and Attribution

All members of the core development and review teams are automatically authors on Biomappings papers and can propose
other co-authors.

All (direct) contributions to the data underlying Biomappings, regardless of curation size, should be considered for
authorship on Biomappings papers. These contributions are automatically summarized
on [https://biopragmatics.github.io/biomappings](https://biopragmatics.github.io/biomappings).

Attribution information must be collected for all changes to the data underlying Biomappings:

- Manual updates (i.e., changes to the positive, negative, or unsure mappings file) must include the
  curator's [ORCiD identifier](https://orcid.org/).
- Automatic updates (i.e., additions to predictions via lexical mapping, inference, etc.) must include a permalink to
  the script that generated them (e.g., to a git hash or a Zenodo archive). This script should ideally be added into
  the `scripts/` folder of the Biomappings GitHub repository for maximum transparency along with an explanation on how
  to re-run it.

Larger external institutional contributors should be acknowledged in the following places, where appropriate:

- On the support and funding sections of the repository's
  main [README.md](https://github.com/biopragmatics/biomappings/blob/master/README.md)
- On the acknowledgements section
  of [https://biopragmatics.github.io/biomappings](https://biopragmatics.github.io/biomappings)

## Updating governance

This governance must updated through the following steps:

- Create an issue on the [Biomappings issue tracker](https://github.com/biopragmatics/biomappings) describing the
  desired change and reasoning.
- Engage potential stakeholders in discussion.
- Solicit the Biomappings Review Team for a review.
- The Biomappings Review Team will accept changes at their discretion.

This procedure doesn't apply to cosmetic or ergonomics changes, which are allowed to be done in a more *ad-hoc* manner.
The Biomappings Review Team may later make explicit criteria for accepting changes to this governance.

## Inspiration and Credit

The Biomappings governance document was heavily influenced by
the [Bioregistry project's governance](https://github.com/biopragmatics/bioregistry/blob/main/docs/GOVERNANCE.md).
