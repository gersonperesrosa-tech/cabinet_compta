from django import template

register = template.Library()

@register.filter
def to(start, end):
    return range(start, end + 1)

@register.filter
def dict_get(d, key):
    return d.get(key)
