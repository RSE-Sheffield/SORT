from django import template
from django.utils.html import format_html

from home.views.sorting import ASC, DESC

register = template.Library()


@register.simple_tag(takes_context=True)
def sort_header(context, key, label):
    """Render a sortable ``<th>`` whose link toggles the sort on ``key``."""
    request = context["request"]
    current_key = context.get("sort")
    current_dir = context.get("dir", ASC)
    active = key == current_key

    params = request.GET.copy()
    params.pop("page", None)
    params["sort"] = key
    params["dir"] = DESC if active and current_dir == ASC else ASC

    if active:
        aria_sort = "ascending" if current_dir == ASC else "descending"
        icon = "bx-sort-up" if current_dir == ASC else "bx-sort-down"
    else:
        aria_sort = "none"
        icon = "bx-sort-alt-2 text-muted"

    return format_html(
        '<th scope="col" aria-sort="{}"><a href="?{}" class="text-reset text-decoration-none">'
        '{} <i class="bx {}" aria-hidden="true"></i></a></th>',
        aria_sort,
        params.urlencode(),
        label,
        icon,
    )
