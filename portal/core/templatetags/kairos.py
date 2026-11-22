from django import template

from core.units import format_distance, format_duration

register = template.Library()


@register.filter
def distance(metres, units="mi"):
    return format_distance(metres, units)


@register.filter
def duration(seconds):
    return format_duration(seconds)
