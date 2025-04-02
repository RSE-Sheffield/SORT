import json
import logging
from os import path
from django import template
from urllib.parse import urljoin
from django.conf import settings
from django.utils.safestring import mark_safe
from django.contrib.staticfiles import finders
from django.templatetags.static import static

logger = logging.getLogger(__name__)

register = template.Library()


@register.simple_tag
def vite_client():
    """
    Include vite's hot reloading code when in debug mode only.
    """
    if settings.DEBUG:
        vite_client_path = urljoin(settings.VITE_BASE_URL, "/@vite/client")
        return mark_safe(f"<script type = 'module' src = '{vite_client_path}'> </script>")

    return ""


@register.simple_tag
def vite_asset(asset_path):
    """
    Link directly to asset on vite dev server in debug mode and to static assets folder in production.
    """

    if settings.DEBUG:
        vite_asset_path = urljoin(settings.VITE_BASE_URL, asset_path)
        return mark_safe(f"<script type = 'module' src = '{vite_asset_path}' > </script>")
    else:
        vite_manifest_path = finders.find(settings.VITE_MANIFEST_FILE_PATH)
        if vite_manifest_path:
            with open(vite_manifest_path, "r") as f:
                vite_manifest = json.load(f)
                if asset_path in vite_manifest:
                    asset_static_path = path.join(settings.VITE_STATIC_DIR, vite_manifest[asset_path]["file"])
                    asset_static_path_found = finders.find(asset_static_path)
                    if asset_static_path_found:
                        return mark_safe(f"<script type = 'module' src = '{static(asset_static_path)}' > </script>")
                    else:
                        raise FileNotFoundError(f"Specified vite asset file {asset_static_path} cannot found.")
        else:
            raise FileNotFoundError(f"Vite manifest file ({settings.VITE_MANIFEST_FILE_PATH}) cannot be found.")

    return ""
