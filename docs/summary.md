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

{% for entry in site.data.components_with_duplicate_prefixes %}
    <p><ul>
    {% for x in entry %}
        <li>
        {{ x.name }}
        ({% if (x.identifier | lowercase) contains x.prefix %}
        <a href="https://identifiers.org/{{x.identifier}}">{{x.identifier}}]</a>
        {% else %}
        <a href="https://identifiers.org/{{x.prefix}}:{{x.identifier}}">{{x.prefix}}:{{x.identifier}}</a>
        {% endif %})
        </li>
    {% endfor %}
    </ul></p>
{% endfor %}
