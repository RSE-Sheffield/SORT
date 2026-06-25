"""
Generate JSON Schema from survey configuration for validating response answers.
"""


def field_schema(field_config: dict) -> dict:
    """Return a JSON Schema for one field's answer value."""
    field_type = field_config["type"]

    if field_type == "likert":
        return _likert_schema(field_config)
    elif field_type in ("radio", "select"):
        return _radio_schema(field_config)
    elif field_type == "checkbox":
        return _checkbox_schema(field_config)
    elif field_type in ("text", "textarea"):
        return _text_schema(field_config)
    else:
        # Empty schema: any value is valid (no constraints imposed)
        return {}


def _likert_schema(field_config: dict) -> dict:
    """Likert answer: array of strings from options, one per sublabel."""
    num_sublabels = len(field_config.get("sublabels", []))
    options = field_config.get("options", [])
    schema = {
        "type": "array",
        "items": {"type": "string", "enum": options},
        "minItems": num_sublabels,
        "maxItems": num_sublabels,
    }
    return schema


def _radio_schema(field_config: dict) -> dict:
    """Radio/select answer: single string from options."""
    options = field_config.get("options", [])
    schema = {"type": "string"}
    if options:
        schema["enum"] = options
    if field_config.get("required"):
        schema["minLength"] = 1
    return schema


def _checkbox_schema(field_config: dict) -> dict:
    """Checkbox answer: array of strings from options."""
    options = field_config.get("options", [])
    schema = {"type": "array", "items": {"type": "string"}}
    if options:
        schema["items"]["enum"] = options
    if field_config.get("required"):
        schema["minItems"] = 1
    return schema


def _text_schema(field_config: dict) -> dict:
    """Text/textarea answer: string."""
    schema = {"type": "string"}
    if field_config.get("required"):
        schema["minLength"] = 1
    return schema
