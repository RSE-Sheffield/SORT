"""Column sorting for the staff console list views."""

ASC = "asc"
DESC = "desc"


class SortableMixin:
    """
    Sort a queryset from ``?sort=<key>&dir=asc|desc``.

    ``sort_fields`` maps each public sort key to an ORM field name (or a tuple
    of them); keys outside this whitelist are ignored. ``default_sort`` names the
    key used when the request has no valid ``sort``.
    """

    sort_fields: dict = {}
    default_sort: str = ""
    default_dir: str = ASC

    def get_sort(self):
        key = self.request.GET.get("sort")
        if key not in self.sort_fields:
            return self.default_sort, self.default_dir
        direction = DESC if self.request.GET.get("dir") == DESC else ASC
        return key, direction

    def apply_sort(self, queryset, context):
        key, direction = self.get_sort()
        fields = self.sort_fields[key]
        if isinstance(fields, str):
            fields = (fields,)
        prefix = "-" if direction == DESC else ""
        # pk tiebreaker keeps ordering stable, which pagination requires.
        queryset = queryset.order_by(*[f"{prefix}{f}" for f in fields], "pk")
        context["sort"] = key
        context["dir"] = direction
        return queryset
