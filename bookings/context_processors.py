from .utils import get_footer_sections, get_navigation_items, get_site_configuration


def global_settings(request):
    language = request.session.get("language", "en")
    return {
        "current_language": language,
        "site_settings": get_site_configuration(),
        "navigation_items": get_navigation_items(language),
        "footer_sections": get_footer_sections(language),
    }
