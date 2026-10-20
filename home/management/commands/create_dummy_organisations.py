from django.core.management.base import BaseCommand

from home.models import Organisation

ORGANISATIONS = [
    (
        "Sheffield Teaching Hospitals NHS Foundation Trust",
        "One of the largest NHS teaching hospital trusts in the UK, providing acute, "
        "specialist and community care across five hospitals.",
    ),
    (
        "Leeds Teaching Hospitals NHS Trust",
        "A major teaching trust delivering local, regional and national specialist "
        "services across seven hospital sites.",
    ),
    (
        "Manchester University NHS Foundation Trust",
        "The largest NHS trust in England, providing hospital and community "
        "healthcare services across Greater Manchester.",
    ),
    (
        "Oxford University Hospitals NHS Foundation Trust",
        "A group of four hospitals providing acute and specialist clinical services "
        "and a base for medical research and education.",
    ),
    (
        "Cambridge University Hospitals NHS Foundation Trust",
        "Operator of Addenbrooke's and the Rosie Hospital, combining patient care "
        "with clinical research and teaching.",
    ),
    (
        "Newcastle upon Tyne Hospitals NHS Foundation Trust",
        "Provider of acute and specialist hospital services across the North East "
        "of England.",
    ),
    (
        "Nottingham University Hospitals NHS Trust",
        "One of the largest acute trusts in the country, delivering general and "
        "specialist care across two campuses.",
    ),
    (
        "Birmingham Women's and Children's NHS Foundation Trust",
        "A specialist trust dedicated to the health of women, babies, children "
        "and young people.",
    ),
    (
        "South London and Maudsley NHS Foundation Trust",
        "A specialist mental health trust providing care for children, adults "
        "and older people.",
    ),
    (
        "Yorkshire Ambulance Service NHS Trust",
        "Provider of emergency, urgent and patient transport services across "
        "Yorkshire and the Humber.",
    ),
]


class Command(BaseCommand):
    help = "Create some dummy NHS organisations for demos and screenshots."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing organisations with these names before creating them.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            names = [name for name, _ in ORGANISATIONS]
            deleted, _ = Organisation.objects.filter(name__in=names).delete()
            self.stdout.write(f"Deleted {deleted} existing organisation(s).")

        for name, description in ORGANISATIONS:
            organisation, created = Organisation.objects.get_or_create(
                name=name, defaults={"description": description}
            )
            status = "Created" if created else "Already exists"
            self.stdout.write(f"{status}: {organisation.name}")
