---
layout: home
---
This site summarizes the `biomappings` resources.

## Positive Mappings

<table>
<thead>
<tr>
    <th>Source Prefix</th>
    <th>Target Prefix</th>
    <th>Count</th>
</tr>
</thead>
<tbody>
{% for entry in site.data.summary['positive'] %}
    <tr>
        <td>{{ entry.source }}</td>
        <td>{{ entry.target }}</td>
        <td align="right">{{ entry.count }}</td>
    </tr>
{% endfor %}
</tbody>
</table>

## Negative Mappings

<table>
<thead>
<tr>
    <th>Source Prefix</th>
    <th>Target Prefix</th>
    <th>Count</th>
</tr>
</thead>
<tbody>
{% for entry in site.data.summary['negative'] %}
    <tr>
        <td>{{ entry.source }}</td>
        <td>{{ entry.target }}</td>
        <td align="right">{{ entry.count }}</td>
    </tr>
{% endfor %}
</tbody>
</table>

## Predictions

<table>
<thead>
<tr>
    <th>Source Prefix</th>
    <th>Target Prefix</th>
    <th>Count</th>
</tr>
</thead>
<tbody>
{% for entry in site.data.summary['predictions'] %}
    <tr>
        <td>{{ entry.source }}</td>
        <td>{{ entry.target }}</td>
        <td align="right">{{ entry.count }}</td>
    </tr>
{% endfor %}
</tbody>
</table>

## Contributors

<table>
<thead>
<tr>
    <th>Contributor</th>
    <th>Curation count</th>
</tr>
</thead>
<tbody>
{% for entry in site.data.summary['contributors'] %}
    <tr>
        <td>{% if entry.orcid %}<a href="https://orcid.org/{{ entry.orcid }}">{{ entry.orcid }}</a>{% else %}Unknown{% endif %}</td>
        <td align="right">{{ entry.count }}</td>
    </tr>
{% endfor %}
</tbody>
</table>
