from .services import organisation_join_request_service, organisation_service


def organisation_context(request):
    """
    Make the user's active organisation and the organisations they can
    switch between available on every page, for the nav bar's org switcher.

    Also supplies the count of join requests awaiting the user's decision, for
    the nav bar's badge. That count is scoped to the active organisation, both
    to keep it consistent with the review page it links to and to keep the cost
    to a single indexed COUNT(*) — and only for administrators, since
    ``get_pending_count`` returns 0 for everyone else without querying.

    All three values are derived from a single membership fetch, rather than
    each independently re-querying membership/role data for the same user.
    """
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {}

    memberships = organisation_service.get_user_memberships(request.user)
    active_organisation = organisation_service.get_active_organisation(
        request, memberships=memberships
    )
    active_role = next(
        (
            membership.role
            for membership in memberships
            if membership.organisation_id
            == getattr(active_organisation, "id", None)
        ),
        None,
    )

    return {
        "active_organisation": active_organisation,
        "switchable_organisations": organisation_service.get_user_organisations(
            request.user, memberships=memberships
        ),
        "pending_join_request_count": (
            organisation_join_request_service.get_pending_count(
                request.user, active_organisation, role=active_role
            )
        ),
    }
