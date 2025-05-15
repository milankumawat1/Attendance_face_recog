from django import template
from django.template.defaultfilters import stringfilter
from datetime import datetime

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter to get an item from a dictionary using a key.
    Returns None if the key doesn't exist.
    """
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def format_time(value):
    """
    Template filter to format time values.
    Returns a formatted time string or 'Not checked out' if None.
    """
    if value is None:
        return 'Not checked out'
    
    # If it's already a string, return it
    if isinstance(value, str):
        return value
    
    # If it's a datetime object, format it
    try:
        return value.strftime('%I:%M %p')
    except (AttributeError, TypeError):
        return str(value) 