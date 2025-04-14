from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from survey.models import SurveyFile, SurveyEvidenceFile


class Command(BaseCommand):
    help = "Clear orphaned uploaded files uploaded by the user"


    def handle(self, *args, **options):

        upload_root = Path(settings.MEDIA_ROOT)

        # Gets all file in the uploads folder, delete any that's not in use
        for (dirpath, dir_names, file_names) in upload_root.walk():
            for file_name in file_names:
                file_path = dirpath/file_name
                relative_path = file_path.relative_to(upload_root)
                if (SurveyEvidenceFile.objects.filter(file=str(relative_path)).count() < 1
                        and SurveyFile.objects.filter(file=str(relative_path)).count() < 1):
                    print(f"Deleting {file_path}")
                    file_path.unlink(missing_ok=True)

        self.clear_empty_directories(settings.MEDIA_ROOT)


    def clear_empty_directories(self, root_dir: str):
        for item in Path(root_dir).iterdir():
            if item.is_dir():
                if not any(item.iterdir()):
                    print(f"Deleting empty directory {item}")
                    item.rmdir()
                else:
                    self.clear_empty_directories(item)
