import json
import logging
import os
from enum import Enum
from os import path
from typing import LiteralString

from django import template
from urllib.parse import urljoin
from django.conf import settings
from django.utils.safestring import mark_safe
from django.contrib.staticfiles import finders
from django.templatetags.static import static

logger = logging.getLogger(__name__)

register = template.Library()

VITE_MANIFEST = None


@register.simple_tag
def vite_client():
    """
    Include vite's hot reloading code when in debug mode only.
    """
    if settings.DEBUG:
        vite_client_path = urljoin(settings.VITE_BASE_URL, "/@vite/client")
        return mark_safe(f"<script type = 'module' src = '{vite_client_path}'> </script>")

    return ""


class AssetType(Enum):
    SCRIPT = 0
    CSS = 1


@register.simple_tag
def vite_asset(asset_path: str) -> str:
    """
    Link directly to asset on vite dev server in debug mode and to static assets folder in production.
    """

    if settings.DEBUG:
        vite_asset_path = urljoin(settings.VITE_BASE_URL, asset_path)
        return mark_safe(f"<script type = 'module' src = '{vite_asset_path}' > </script>")
    else:
        global VITE_MANIFEST
        if VITE_MANIFEST is None:
            vite_manifest_path = finders.find(settings.VITE_MANIFEST_FILE_PATH)
            if vite_manifest_path:
                with open(vite_manifest_path, "r") as f:
                    VITE_MANIFEST = json.load(f)
            else:
                raise FileNotFoundError(f"Vite manifest file ({settings.VITE_MANIFEST_FILE_PATH}) cannot be found.")

        if asset_path in VITE_MANIFEST:
            manifest_asset = VITE_MANIFEST[asset_path]
            import_tags = []
            if "css" in manifest_asset:
                for css_path in manifest_asset["css"]:
                    import_tags.append(get_asset_import_tag(path.join(settings.VITE_STATIC_DIR, css_path),
                                                            AssetType.CSS))

            if "file" in manifest_asset:
                import_tags.append(get_asset_import_tag(path.join(settings.VITE_STATIC_DIR, manifest_asset["file"]),
                                                        AssetType.SCRIPT))

            return mark_safe("".join(import_tags))

    return ""


def get_asset_import_tag(asset_static_path: str | LiteralString | bytes, type: AssetType):
    asset_static_path_found = finders.find(asset_static_path)
    if asset_static_path_found:
        if type == AssetType.SCRIPT:
            return f"<script type = 'module' src = '{static(asset_static_path)}' ></script>\n"
        elif type == AssetType.CSS:
            return f"<link rel='stylesheet' href='{static(asset_static_path)}'>\n"
        else:
            return ""
    else:
        raise FileNotFoundError(f"Specified vite asset file {asset_static_path} cannot found.")
