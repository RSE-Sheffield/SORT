from collections import Counter

from django.db import migrations


def lowercase_emails(apps, schema_editor):
    """
    Normalize existing user emails to lowercase (see issue #667: mixed-case
    emails could never log in again once the case-insensitive lookup was
    added, since exact-match DB queries are case-sensitive on Postgres).
    """
    User = apps.get_model("home", "User")

    users = list(User.objects.all())
    collisions = [
        email
        for email, count in Counter(u.email.lower() for u in users).items()
        if count > 1
    ]
    if collisions:
        raise ValueError(
            "Cannot lowercase emails: the following addresses collide once "
            f"lowercased and need manual resolution first: {collisions}"
        )

    for user in users:
        lowered = user.email.lower()
        if lowered != user.email:
            user.email = lowered
            user.save(update_fields=["email"])


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0013_dataprotectionevent"),
    ]

    operations = [
        migrations.RunPython(lowercase_emails, migrations.RunPython.noop),
    ]
