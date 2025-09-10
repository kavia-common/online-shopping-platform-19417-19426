# DRF configuration extracted to its own module to keep settings tidy.

# PUBLIC_INTERFACE
def get_rest_framework_settings():
    """Return REST_FRAMEWORK settings dict used by Django settings."""
    return {
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "rest_framework.authentication.SessionAuthentication",
            "rest_framework.authentication.BasicAuthentication",
        ],
        "DEFAULT_PERMISSION_CLASSES": [
            "rest_framework.permissions.AllowAny",
        ],
        "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
        "PAGE_SIZE": 20,
    }
