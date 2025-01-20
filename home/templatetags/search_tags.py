from django import template
from ..forms import SearchBarForm

register = template.Library()


@register.inclusion_tag('components/search_bar.html', takes_context=True)
def search_bar(context, placeholder="Search...", search_url=None):
    request = context['request']
    form = SearchBarForm(request.GET or None)
    form.fields['q'].widget.attrs['placeholder'] = placeholder

    return {
        'search_form': form,
        'current_search': request.GET.get('q', ''),
        'search_url': search_url or request.path,
        'current_params': request.GET.copy()
    }