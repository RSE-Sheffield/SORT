# Data Protection Audit Log

SORT keeps an **append-only audit log of actions taken on users' personal data** —
erasures, subject-access exports, account restrictions, consent withdrawals and
removals from organisations. The log exists so the service can demonstrate UK GDPR
**Article 5(2) accountability**: a tamper-resistant record of *what* was done to
*whose* data, *by whom*, and *when*.

The subsystem has three parts:

- **`DataProtectionEvent`** — the append-only model (`home/models.py`).
- **`data_protection_service`** — the service that records and queries events
  (`home/services/data_protection.py`).
- **`ConsoleDataProtectionLogView`** — the staff-only console view that displays the
  log (`home/views/console.py`).

## The audit log model (`DataProtectionEvent`)

Each event is one immutable row. Subject identity is **never** stored as a foreign key
to `User` — entries must survive erasure of the subject — so identity is captured as
the original user id plus a one-way pseudonym instead (see
[Pseudonymisation](#pseudonymisation)).

| Field | Type | Meaning |
|-------|------|---------|
| `event_type` | `CharField` (choices) | What happened — one of the [event types](#event-types) below. |
| `subject_user_id` | `IntegerField`, nullable | The subject's original `User` PK. Kept as a plain integer so it survives the user being deleted. |
| `subject_identifier` | `CharField` | Stable pseudonym for the subject (e.g. `sha256:…`), or `deleted-user-<pk>` if the subject had no email. Never plaintext. |
| `actioned_by` | FK → `User`, `SET_NULL` | Staff member who performed the action. Nulled (not deleted) if that staff account is later removed. |
| `requested_by` | FK → `User`, `SET_NULL` | User who requested the action, where applicable (e.g. a subject-access request). |
| `requested_at` | `DateTimeField`, nullable | When the action was requested. |
| `actioned_at` | `DateTimeField`, `auto_now_add` | When the action was recorded. Set once, immutable. |
| `notes` | `TextField` | Free-text context or reason for the action. |

Events are ordered newest-first (`-actioned_at`). Two indexes support the console
filters: `(event_type, -actioned_at)` and `(subject_user_id)`.

See [data-model.md](data-model.md) for how this model sits alongside the rest of the
schema.

### Event types

`DataProtectionEvent.EventType` defines the full taxonomy. Note that the model defines
all six, but only some are emitted by application flows **today** — the rest are
reserved for their corresponding flows as they are built.

| Value | Label | Emitted today? |
|-------|-------|----------------|
| `membership_removed` | Removed from organisation | ✅ Yes — by `ConsoleRemoveMemberView`. |
| `erasure` | Erasure request actioned | Reserved — call `record_event` from the erasure flow. |
| `export` | Subject access export generated | Reserved — call `record_event` from the export flow. |
| `restriction` | Account restricted / suspended | Reserved. |
| `unrestriction` | Account restriction lifted | Reserved. |
| `consent_withdrawal` | Consent withdrawn | Reserved. |

To start logging a reserved type, call `record_event` from the relevant flow — no
model or migration change is needed. See
[Recording events from new flows](#recording-events-from-new-flows).

## Immutability guarantees

The log is **append-only**. The model enforces this at three points so an event cannot
be altered or removed once written:

- `save()` raises `ValueError` if the instance already has a `pk` — existing rows
  cannot be updated.
- `delete()` raises `ValueError` — instances cannot delete themselves.
- A `pre_delete` signal handler (`_prevent_dp_event_delete`) raises `ValueError` —
  this also blocks queryset-level deletes (`QuerySet.delete()`) and cascades that would
  otherwise bypass the model's `delete()`.

In practice: there is no supported path to edit or delete an event through the ORM,
the Django admin, or the console. Corrections are made by recording a *new* event, not
by changing an old one.

## Pseudonymisation

The log must satisfy two competing requirements: it must **not retain plaintext
personal data** (an erased subject's email cannot live on forever in an immutable
log), yet it must still **correlate multiple events for the same person**. A salted,
one-way hash satisfies both.

`pseudonymise_identifier(value)` (in `home/services/data_protection.py`) produces the
stored identifier:

```python
digest = hashlib.sha256(
    f"sort-dp:{settings.SECRET_KEY}:{value.strip().lower()}".encode()
).hexdigest()
return f"sha256:{digest[:32]}"
```

- **One-way** — the original email cannot be recovered from the stored value.
- **Stable within a deployment** — the same email always hashes to the same
  identifier, so all events for one person share a `subject_identifier` and can be
  grouped.
- **Salted with `SECRET_KEY`** — the mapping is namespaced to the deployment. Rotating
  `SECRET_KEY` simply re-namespaces *future* hashes; historical identifiers are
  unaffected (and remain comparable among themselves).
- **Deleted-user fallback** — if the subject has no email available,
  `record_event` stores `deleted-user-<pk>` instead.

## Service API

All access goes through the `data_protection_service` singleton:

```python
from home.services import data_protection_service
```

### `record_event` — write

```python
data_protection_service.record_event(
    *,
    event_type: str,                       # a DataProtectionEvent.EventType value
    subject_user: User,                    # the person whose data was acted on
    actioned_by: Optional[User],           # staff/system actor (None if unattributable)
    requested_by: Optional[User] = None,
    requested_at: Optional[datetime] = None,
    notes: str = "",
) -> DataProtectionEvent
```

`record_event` is **deliberately not permission-gated**. The calling flow has already
performed its own permission checks, and the audit record must always be written —
including when the caller is a system task with no `request.user`. Pseudonymisation of
the subject is handled internally; callers pass the real `User`.

> **Caller responsibility:** because the write path performs no permission check, the
> calling code is responsible for authorising the underlying action before recording
> it.

### `list_events` — read

```python
data_protection_service.list_events(
    user: User,                            # must be active staff
    *,
    event_type: Optional[str] = None,
    subject_user_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> QuerySet[DataProtectionEvent]
```

The read path **is** gated: it raises `PermissionDenied` unless `user` is
authenticated, active, and staff. All filters are optional and combine with AND. The
queryset uses `select_related("actioned_by", "requested_by")` to avoid N+1 queries
when rendering actor columns.

## Recording events from new flows

To log a data protection action from anywhere in the codebase:

1. Perform and authorise the action as usual.
2. After it succeeds, record the event:

```python
from home.models import DataProtectionEvent
from home.services import data_protection_service

# ... member removal already authorised and performed ...
data_protection_service.record_event(
    event_type=DataProtectionEvent.EventType.MEMBERSHIP_REMOVED,
    subject_user=removed_user,
    actioned_by=request.user,
    notes=f"Removed from organisation '{org_name}'",
)
```

This mirrors the one wired-up call site today, `ConsoleRemoveMemberView`
(`home/views/console.py`). Pick the `EventType` that matches the action; pass
`requested_by` / `requested_at` when the action originated from a user request.

## Viewing the log (console)

The log is exposed through `ConsoleDataProtectionLogView`, a **staff-only** console
page (`StaffRequiredMixin`):

- **URL:** `/console/data-protection/` — reverse name `admin_data_protection_log`.
- **Template:** `console/data_protection_log.html`, linked from the console nav
  (`base_console.html`).
- **Filters (GET params):** `event_type` and `subject_user` (subject user id).
- **Pagination:** 25 events per page (`page` param); active filters are preserved
  across pages.

The view delegates to `list_events`, so the same staff gate applies — a non-staff user
who reaches the view is denied.

## Design notes

- **Append-only by design.** Audit integrity depends on events being immutable; the
  three-layer enforcement (`save`, `delete`, `pre_delete` signal) makes accidental or
  programmatic mutation fail loudly rather than silently corrupting the record.
- **Service layer.** Recording and reading both go through the service singleton,
  consistent with SORT's [service layer pattern](architecture.md#permission-architecture)
  — though note the asymmetric gating (open write, staff-gated read) described above.
- **Retention.** Entries are intended to be retained for the accountability period and
  are not pruned automatically. Because they hold no plaintext personal data, retaining
  them does not itself keep an erased subject's identity on file.
