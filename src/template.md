---
description: "{{ description }}"
tools:
  [
{% for tool in tools %}
    "{{ tool }}",
{% endfor %}
  ]
user-invocable: false
argument-hint: "{{ argument_hint }}"
---

{{ disclaimer | trim }}

{{ file_communication | trim }}

## あなたの役割

{{ role | trim }}

## 手順 (#tool:todo)

{{ steps | trim }}
{% for section in sections | default([]) %}
## {{ section.title }}

{{ section.content | trim }}
{% endfor %}
## 1行サマリの内容

{{ summary_hint | trim }}
