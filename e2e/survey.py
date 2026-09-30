"""
Helpers for filling in the survey response form.
"""

from e2e.base import Locator, Page, expect

# The score chosen for every likert statement
LIKERT_SCORE = "3"
COMMENT = "Automated end-to-end test comment"
INVALID_MESSAGE = "Values are incorrect or missing"


def get_fields(page: Page) -> Locator:
    """
    The input fields on the current survey page, in the same order as the section configuration.
    """
    return page.locator(".sort-survey-response .card-body > .mb-3")


def fill_field(field: Locator, config: dict):
    """
    Answer one survey question, based on its configuration.
    """
    field_type = config["type"]
    if field_type == "likert":
        rows = field.locator("tbody tr")
        expect(rows).to_have_count(len(config["sublabels"]))
        for row in rows.all():
            row.get_by_label(f"Score {LIKERT_SCORE}", exact=True).check()
    elif field_type == "text":
        value = "30" if config.get("textType") == "INTEGER_TEXT" else "Tester"
        field.get_by_label(config["label"]).fill(value)
    elif field_type == "textarea":
        field.get_by_label(config["label"]).fill(COMMENT)
    elif field_type in ("radio", "checkbox"):
        field.get_by_label(config["options"][0], exact=True).check()
    elif field_type == "select":
        field.get_by_label(config["label"]).select_option(config["options"][0])
    else:
        raise ValueError(f"Unknown field type: {field_type}")


def fill_section(page: Page, section: dict):
    """
    Answer every question on the current survey page.
    """
    expect(page.get_by_role("heading", name=section["title"], exact=True)).to_be_visible()
    fields = get_fields(page)
    expect(fields).to_have_count(len(section["fields"]))
    for field, config in zip(fields.all(), section["fields"]):
        fill_field(field, config)


def fill_pages(page: Page, sections: list[dict]):
    """
    Answer the questions on each of these pages, moving on to the next page after each one.
    """
    for section in sections:
        fill_section(page, section)
        page.get_by_role("button", name="Next >").click()
