# myapp/middleware/custom_firebase_auth.py
from .firebase_auth_middleware import FirebaseAuthMiddleware
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomFirebaseAuthMiddleware(FirebaseAuthMiddleware):
    def get_user_from_firebase_uid(self, uid):
        # Example: match users by email if firebase_uid is not present
        try:
            return User.objects.get(firebase_uid=uid)
        except User.DoesNotExist:
            return None

    def on_auth_success(self, request, uid, user):
        # You can attach roles, logging, etc.
        request.user_role = user.role  # assuming `role` field exists
