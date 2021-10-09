---
layout: page
title: Summary
permalink: /summary/
---

## Full Summary

This chart shows the summary of positive mappings, as a shortened version of the home page.

<img src="https://raw.githubusercontent.com/biopragmatics/biomappings/master/docs/img/summary.png" alt="Summary"/>

## Component Summaries

An undirected graph can be generated from equivalences in which all entities in a component can be considered equivalent
due to the transitivity of the relationship.

This chart shows various aspects of the positive mappings graph. Larger components means that more extensive curation
has been done. Higher density components means that they have been checked multiple times.

<img src="https://raw.githubusercontent.com/biopragmatics/biomappings/master/docs/img/components.png" alt="Component Summary"/>

## Curation Warnings

### Duplicate Prefixes

If two concepts with the same prefix appear in the same equivalence component, there is typically an error in curation.

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

### Incomplete Triangles

Incomplete triangles are components within the graph such that `A skos:exactMatch B`, `B skos:exactMatch C`, but it is
not explicitly curated that `A skos:exactMatch C`. Curating the relationship between `A` and `C` relation is an
opportunity to make the other relations much higher confidence.

<ol>
{% for entry in site.data.incomplete_components %}
<li>
<p>Nodes</p>
<ul>
{% for node in entry['nodes'] %}
<li>
{{ node[1].name }} (<a href="{{ node[1].link }}">{{ node[0] }}</a>)
</li>
{% endfor %}
</ul>
<p>Missing Edges</p>
<ul>
{% for edge in entry['edges'] %}
<li>
<code>
<a href="{{ edge.source.link }}">{{ edge.source.curie }}</a> {{ edge.source.name }} skos:exactMatch
<a href="{{ edge.target.link }}">{{ edge.target.curie }}</a> {{ edge.target.name }}
</code>
</li>
{% endfor %}
</ul>
</li>
{% endfor %}
</ol>
