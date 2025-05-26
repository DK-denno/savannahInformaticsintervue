from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class WhatsappSessionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """Handles incoming requests and processes JSON body if applicable."""
        pass

    def process_response(self, request, response):
        """Logs response status for debugging."""
        print(f"Response: {response.status_code} for {request.path}")
        return response


    