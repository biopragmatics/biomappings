---
layout: page title: Summary permalink: /summary/
---

## Component Summaries

An undirected graph can be generated from equivalences in which all entities in a component can be considered equivalent
due to the transitivity of the relationship.

This chart shows various aspects of the positive mappings graph. Larger components means that more extensive curation
has been done. Higher density components means that they have been checked multiple times.

<img src="https://raw.githubusercontent.com/biomappings/biomappings/master/docs/img/components.png" alt="Comparison"/>

## Curation Warnings

### Duplicate Prefixes

<ul>
{% for entry in site.data.components_with_duplicate_prefixes %}
    <li><ul>
    {% for x in entry %}
        <li>
            {{ entry.name }} ({{entry.identifier}})
        </li>
    {% endfor %}
    </ul></li>
{% endfor %}
</ul>
