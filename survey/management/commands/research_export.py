from django.core.management import BaseCommand

from home.services.research_export import ResearchExport


class Command(BaseCommand):
    """
    Export all consented research data (shared surveys, participants who gave
    research consent) across every organisation to one Excel workbook.
    """

    help = "Export all consented research data to an Excel (.xlsx) file."

    def add_arguments(self, parser):
        parser.add_argument("-o", "--output", required=True, help="Output .xlsx file path")

    def handle(self, *args, output, **options):
        row_count = ResearchExport().write_xlsx(output)
        self.stdout.write(f"Wrote {row_count} responses to {output}")
