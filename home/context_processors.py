from .services import organisation_service


def organisation_context(request):
    """
    Make the user's active organisation and the organisations they can
    switch between available on every page, for the nav bar's org switcher.
    """
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {}

    return {
        "active_organisation": organisation_service.get_active_organisation(request),
        "switchable_organisations": organisation_service.get_user_organisations(
            request.user
        ),
    }
