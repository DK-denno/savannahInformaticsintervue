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
        # If it's a queryset, we'll serialize it to a list of dictionaries.
        # This can be expanded to handle specific fields, annotations, or related objects.
        return list(queryset.values())

    elif isinstance(queryset, list):
        # If it's already a list, no need to change it, but ensure it's serializable.
        return [item if isinstance(item, dict) else item.__dict__ for item in queryset]

    elif isinstance(queryset, dict):
        # If it's already a dict, return it as-is.
        return queryset

    else:
        # Handle any other custom cases (like individual model instances, etc.)
        try:
            # If the object is a single model instance, convert it to a dict.
            return queryset.__dict__
        except AttributeError:
            # If it's an unrecognized type, simply return it as-is.
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
