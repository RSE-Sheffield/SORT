import secrets

from django.db import migrations, models

# Frozen copy of survey.models.SHORT_CODE_ALPHABET / SHORT_CODE_LENGTH
SHORT_CODE_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
SHORT_CODE_LENGTH = 8


def populate_short_codes(apps, schema_editor):
    """
    Give every existing invitation a short code so that existing surveys also
    get a shortened link. Existing tokens (and therefore long links) are unchanged.
    """
    Invitation = apps.get_model("survey", "Invitation")
    used_codes = set(
        Invitation.objects.exclude(short_code=None).values_list("short_code", flat=True)
    )
    for invitation in Invitation.objects.filter(short_code=None).iterator():
        code = None
        while code is None or code in used_codes:
            code = "".join(
                secrets.choice(SHORT_CODE_ALPHABET) for _ in range(SHORT_CODE_LENGTH)
            )
        used_codes.add(code)
        invitation.short_code = code
        invitation.save(update_fields=["short_code"])


class Migration(migrations.Migration):

    dependencies = [
        ("survey", "0030_merge_20260217_1045"),
    ]

    operations = [
        migrations.AddField(
            model_name="invitation",
            name="short_code",
            field=models.CharField(
                blank=True,
                editable=False,
                help_text="Short code used in shortened invitation links",
                max_length=8,
                null=True,
                unique=True,
            ),
        ),
        migrations.RunPython(populate_short_codes, migrations.RunPython.noop),
    ]
