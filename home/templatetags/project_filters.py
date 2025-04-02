from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    if dictionary is None:
        return False
    return dictionary.get(key, False)
