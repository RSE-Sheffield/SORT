# Plan: Add name-typing confirmation to admin console delete pages

## Context

Issue #571 requests that all delete operations in the admin console require users to type the entity's name (user/project/organisation) before confirming the deletion. This prevents accidental deletions by adding a deliberate friction step — similar to GitHub's "type the repo name to delete" pattern.

Currently the only implemented delete action in the admin console is **ConsoleRemoveMemberView** (`/console/organisations/<org_pk>/members/<membership_pk>/remove/`). It already has a two-step GET/POST confirmation page (`remove_member_confirm.html`), but the confirmation is just a single button click — no name-typing required.

The other "Delete" buttons visible in the console UI (organisation detail, project detail) are currently disabled with no backing view, so they are out of scope.

## Changes required

### 1. Update `remove_member_confirm.html`

**File**: `home/templates/console/remove_member_confirm.html`

Replace the simple "Are you sure?" card body with:

- Instruction: "To confirm, type `{{ membership.user.email }}` below"
- A text `<input>` (not part of the POST form — used only for client-side gating)
- The submit button starts **disabled** and is enabled only when the input exactly matches the user's email
- Small inline `<script>` to wire up the enable/disable logic

Using email rather than display name because it's unambiguous and can't contain tricky Unicode lookalikes.

### 2. No view changes needed

`ConsoleRemoveMemberView` already handles GET (show form) and POST (execute delete) correctly. The typing requirement is purely a client-side UX guard — the POST itself remains protected by CSRF and `StaffRequiredMixin`.

## Critical files

- `home/templates/console/remove_member_confirm.html` — only file to edit

## Implementation detail

```html
{# Inside card-body #}
<p>Are you sure you want to remove <strong>{{ membership.user }}</strong> from <strong>{{ organisation.name }}</strong>?</p>
<p class="text-muted small">This will revoke their access to all projects in this organisation.</p>
<div class="mt-3">
    <label for="confirm-input" class="form-label small">
        To confirm, type <strong>{{ membership.user.email }}</strong> below:
    </label>
    <input type="text" id="confirm-input" class="form-control form-control-sm" autocomplete="off">
</div>

{# Submit button starts disabled #}
<button type="submit" id="confirm-submit" class="btn btn-danger" disabled>Remove member</button>

<script>
document.getElementById('confirm-input').addEventListener('input', function () {
    document.getElementById('confirm-submit').disabled =
        this.value !== '{{ membership.user.email }}';
});
</script>
```

## Verification

1. Navigate to any organisation in the admin console (`/console/organisations/<pk>/`)
2. Click the remove (×) icon next to a member
3. Confirm: submit button is disabled on page load
4. Type wrong text → button stays disabled
5. Type the member's exact email → button becomes enabled
6. Submit → member removed, success message shown, redirect to org detail
