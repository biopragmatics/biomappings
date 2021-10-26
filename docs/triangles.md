---
layout: page
title: Incomplete Triangles
permalink: /triangles/
---
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
