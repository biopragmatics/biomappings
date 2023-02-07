---
layout: home
---
<p align="center">
  <img src="https://raw.githubusercontent.com/biopragmatics/biomappings/master/docs/source/logo.png" height="150">
</p>

This site summarizes the `biomappings` resources. They can be downloaded under the CC0-1.0 License from the open-source
repository on [GitHub](https://github.com/biopragmatics/biomappings).

| Type      |                                             Count | 
|-----------|--------------------------------------------------:|
| Positive  |    {{ site.data.summary.positive_mapping_count }} |
| Negative  |    {{ site.data.summary.negative_mapping_count }} |
| Unsure    |      {{ site.data.summary.unsure_mapping_count }} |
| Predicted | {{ site.data.summary.predictions_mapping_count }} |

## Positive Mappings ({{ site.data.summary.positive_mapping_count }})

<table>
<thead>
<tr>
    <th>Source Prefix</th>
    <th>Target Prefix</th>
    <th align="right">Count</th>
</tr>
</thead>
<tbody>
{% for entry in site.data.summary.positive %}
    <tr>
        <td><a href="https://bioregistry.io/{{ entry.source }}">{{ entry.source }}</a></td>
        <td><a href="https://bioregistry.io/{{ entry.target }}">{{ entry.target }}</a></td>
        <td align="right">{{ entry.count }}</td>
    </tr>
{% endfor %}
</tbody>
</table>

## Negative Mappings ({{ site.data.summary.negative_mapping_count }})

<table>
<thead>
<tr>
    <th>Source Prefix</th>
    <th>Target Prefix</th>
    <th align="right">Count</th>
</tr>
</thead>
<tbody>
{% for entry in site.data.summary.negative %}
    <tr>
        <td><a href="https://bioregistry.io/{{ entry.source }}">{{ entry.source }}</a></td>
        <td><a href="https://bioregistry.io/{{ entry.target }}">{{ entry.target }}</a></td>
        <td align="right">{{ entry.count }}</td>
    </tr>
{% endfor %}
</tbody>
</table>

## Unsure Mappings ({{ site.data.summary.unsure_mapping_count }})

<table>
<thead>
<tr>
    <th>Source Prefix</th>
    <th>Target Prefix</th>
    <th align="right">Count</th>
</tr>
</thead>
<tbody>
{% for entry in site.data.summary.unsure %}
    <tr>
        <td><a href="https://bioregistry.io/{{ entry.source }}">{{ entry.source }}</a></td>
        <td><a href="https://bioregistry.io/{{ entry.target }}">{{ entry.target }}</a></td>
        <td align="right">{{ entry.count }}</td>
    </tr>
{% endfor %}
</tbody>
</table>

## Predictions ({{ site.data.summary.predictions_mapping_count }})

<table>
<thead>
<tr>
    <th>Source Prefix</th>
    <th>Target Prefix</th>
    <th align="right">Count</th>
</tr>
</thead>
<tbody>
{% for entry in site.data.summary.predictions %}
    <tr>
        <td><a href="https://bioregistry.io/{{ entry.source }}">{{ entry.source }}</a></td>
        <td><a href="https://bioregistry.io/{{ entry.target }}">{{ entry.target }}</a></td>
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
    <th>ORCID</th>
    <th align="right">Curation Count</th>
</tr>
</thead>
<tbody>
{% for entry in site.data.summary.contributors %}
    <tr>
        <td>{{ entry.name }}</td>
        <td>{% if entry.orcid %}<a href="https://orcid.org/{{ entry.orcid }}">{{ entry.orcid }}</a>{% else %}Unknown{% endif %}</td>
        <td align="right">{{ entry.count }}</td>
    </tr>
{% endfor %}
</tbody>
</table>

<!--
<apicuron-widget database="biomappings"></apicuron-widget>
<script type="text/javascript" src="https://apicuron.org/assets/apicuron-widget.js"></script>
-->
