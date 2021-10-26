---
layout: page
title: Duplicate Prefixes
permalink: /duplicates/
---
If two concepts with the same prefix appear in the same equivalence component,
there is typically an error in curation. One prominent place where this happens
is WikiPathways, where multiple curators may have their own entry for the same
pathway. Even further, WikiPathways imports equivalent pathways to their own
curated ones from sources like NetPath.

<ol>
{% for nodes in site.data.components_with_duplicate_prefixes %}
<li><ul>
{% for node in nodes %}
<li>
{{ node[1].name }} (<a href="{{ node[1].link }}">{{ node[0] }}</a>)
</li>
{% endfor %}
</ul></li>
{% endfor %}
</ol>
