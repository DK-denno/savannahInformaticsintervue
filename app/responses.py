from django.http import JsonResponse

def format_queryset_for_response(queryset):
    """
    Dynamically format a queryset to a format acceptable for a response payload.

    Args:
        queryset (QuerySet): The queryset to be formatted.

    Returns:
        list: A list of dictionaries or a single dictionary.
    """
    if isinstance(queryset, QuerySet):
        return list(queryset.values())

    elif isinstance(queryset, list):
        return [item if isinstance(item, dict) else item.__dict__ for item in queryset]

    elif isinstance(queryset, dict):
        return queryset

    else:
        try:
            return queryset.__dict__
        except AttributeError:
            return queryset

def create_response(status, message, payload=None):
    """
    Unified JSON response generator for Django views and middleware.
    """
    if payload is None:
        payload = []

    if not isinstance(payload, (dict, list, str)):
        payload = []

    return JsonResponse({
        'Status': status,
        'Message': message,
        'Payload': payload
    }, status=status)