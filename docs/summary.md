---
layout: page
title: Summary
permalink: /summary/
---

## Component Summaries

An undirected graph can be generated from equivalences in which all entities in a component can be considered equivalent
due to the transitivity of the relationship.

This chart shows various aspects of the positive mappings graph. Larger components means that more extensive curation
has been done. Higher density components means that they have been checked multiple times.

<img src="https://raw.githubusercontent.com/biomappings/biomappings/master/docs/img/components.png" alt="Comparison"/>

## Curation Warnings

### Duplicate Prefixes

<div>
{% for nodes in site.data.components_with_duplicate_prefixes %}
<ul>
{% for node in nodes %}
<li>
{{ node.name }}
({% if (node.identifier | downcase) contains node.prefix %}
<a href="https://identifiers.org/{{node.identifier}}">{{node.identifier}}</a>
{% else %}
<a href="https://identifiers.org/{{node.prefix}}:{{node.identifier}}">{{node.prefix}}:{{node.identifier}}</a>
{% endif %})
</li>
{% endfor %}
</ul>
{% endfor %}
</div>
