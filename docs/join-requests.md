# Organisation Join Requests

Self-service route for a user to gain access to an organisation that already
exists in SORT, as an alternative to an administrator inviting or adding them
(see [invitations.md](invitations.md)).

Before this existed, a new user whose Trust was already registered had no way to
associate themselves with it: every route out of the no-organisation state led to
"create your first organisation", which produced duplicate organisations and
manual admin work.

## The flow

0. A user with no organisation lands on the get-started chooser at
   `/organisations/get-started/` (`organisation_get_started`), which offers both
   routes — join an existing organisation, or create one — and reports any
   request already waiting for a decision. `OrganisationRequiredMixin` redirects
   here rather than to `organisation_create`, so a user whose request is pending
   is not pushed towards making a duplicate organisation. The requester-facing
   views below deliberately do not use that mixin, since its target is what
   sends users to them. Members are redirected on to `myorganisation`, so the
   page cannot become a second dashboard.
1. A user browses or searches all registered organisations at
   `/organisations/` (`organisation_browse`).
2. They submit a request with an optional message
   (`/organisations/<pk>/join/`, `organisation_join_request`).
3. Every active ADMIN of that organisation is emailed, and a badge appears in
   their navigation bar.
4. An ADMIN reviews the queue at `/myorganisation/join-requests/`
   (`join_requests`) and either approves — choosing the role to grant, Project
   Manager by default — or rejects with an optional reason.
5. The requester is emailed the outcome and can see it at `/myjoinrequests/`
   (`join_requests_mine`), where they can also withdraw a request that is still
   pending.

## Model

`home.models.OrganisationJoinRequest`. See
[data-model.md](data-model.md#organisationjoinrequest) for the fields.

The important constraint is a **partial** unique index on
`(user, organisation) WHERE status = 'PENDING'`: a user may have only one
outstanding request per organisation, but a rejected or withdrawn request can be
submitted again. `unique_together` cannot express a conditional uniqueness,
which is why this model uses `Meta.constraints` where `OrganisationMembership`
uses `unique_together`.

There is no expiry and no cap on how many organisations a user may request to
join.

## Service API

`home.services.organisation_join_request_service`
(`OrganisationJoinRequestService`). It is a separate service from
`OrganisationService` because `requires_permission` resolves
`can_<type>(user, obj)` on the service instance, and `OrganisationService.can_edit`
already means "may edit this *Organisation*"; these methods need
`can_edit(user, join_request)`. Permission logic is not duplicated — the
predicates delegate to `organisation_service.can_manage_members`, so "who may
decide a join request" stays defined in one place.

| Method | Permission | Notes |
|---|---|---|
| `create_join_request(user, organisation, message="")` | any authenticated user | raises `AlreadyMemberError` or `DuplicateJoinRequestError` |
| `approve(user, join_request, role=ROLE_PROJECT_MANAGER)` | `can_manage_members` | returns the `OrganisationMembership` |
| `reject(user, join_request, note="")` | `can_manage_members` | |
| `withdraw(user, join_request)` | the requester | |
| `get_requests(user, organisation, status=PENDING)` | `can_manage_members` | pass `status=None` for the full history |
| `get_user_requests(user)` | — | the caller's own requests |
| `get_pending_organisation_ids(user)` | — | for the browse page's per-row state |
| `get_pending_count(user, organisation)` | — | returns 0 for non-administrators; backs the nav badge |

All four write methods re-read the request under `select_for_update()` and check
that it is still pending, raising `JoinRequestAlreadyDecidedError` otherwise.
That serialises two administrators clicking Approve at the same moment. Approval
also tolerates the requester having been added manually in the meantime: it
reuses the existing membership rather than tripping
`OrganisationMembership`'s `unique_together`.

`can_create` deliberately does **not** check for existing membership. Already
being a member is validation, not a permission problem, and folding it in would
make `requires_permission` raise an opaque `PermissionDenied` before
`create_join_request` could raise the specific `AlreadyMemberError` that views
report to the user.

### No DataProtectionEvent

Deciding a request does not write to the
[data protection audit log](data-protection.md). `EventType` is scoped to actions
taken on a subject's personal data (erasure, export, restriction, consent
withdrawal, membership removal). Granting access is already audited in-domain:
the request stores `decided_by`, `decided_at` and `granted_role`, and the
resulting membership stores `added_by`.

## Email notifications

`home.notifications` — a plain module, not a service, since there is nothing to
permission-gate.

- One message **per recipient**, so administrators' email addresses are not
  disclosed to each other.
- Suspended (`is_active=False`) and GDPR-erased (`@deleted.invalid`) admin
  accounts are excluded; an organisation with no active administrators logs a
  warning and sends nothing, leaving the request visible in SORT.
- `send_mail()` does not apply `EMAIL_SUBJECT_PREFIX`, so `render_email()`
  applies it explicitly.
- `django.contrib.sites` is not installed, so absolute links come from
  `request.build_absolute_uri`. The request is threaded down from the view.

**Failure policy — deliberately different from the invite flow.** The member
invite view deletes its `Invitation` if the email fails, because an invitation
*is* its email: the tokenised link is the only way to use it. A join request is
durable application state instead, so the notification helpers are called from
the view *after* the service has committed, never inside its transaction, and a
send failure is logged and surfaced as a warning message — never rolled back.

## Known limitations

- The nav badge counts pending requests for the **active** organisation only, so
  an administrator of several organisations must switch to see each one's queue.
- The browse page exposes every organisation's name and description to any
  authenticated user. This is intentional (NHS organisation names are public),
  but do not extend it with member counts or administrator identities.
