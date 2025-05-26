import logging
import json

from django.urls import resolve
from django.contrib.auth import get_user_model
from firebase_admin import auth

from ..responses import create_response
from ..models import RbacTasks, CustomUser
from ..utils import roles_match, createUser


User = get_user_model()
logger = logging.getLogger(__name__)


class FirebaseAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        url_path = request.path
        resolver_match = resolve(request.path)
        view_func = resolver_match.func

        # Skip Firebase auth if view is marked
        if getattr(view_func, "skip_firebase_auth", False):
            return self.get_response(request)

        if url_path.startswith("/api/"):
            auth_header = request.META.get("HTTP_AUTHORIZATION", "")
            if not auth_header.startswith("Bearer "):
                response = create_response(401, "unauthorised", "Bad Request")
                return response

            id_token = auth_header.split("Bearer ")[-1]
            try:
                decoded_token = auth.verify_id_token(id_token)
                uid = decoded_token["uid"]
                request.firebase_uid = uid
                print("uid : " + uid)

                try:
                    user = User.objects.get(firebase_uid=uid)
                    request.firebase_user = user

                    rbac_response = self.checkRbacTasks(request, url_path, user)
                    if rbac_response:
                        return rbac_response

                except User.DoesNotExist:
                    response = create_response(404, "NOT FOUND", "User Not Found")
                    return response

            except Exception as e:
                logger.exception(str(e))
                response = create_response(401, "INVALID", str(e))
                return response

        return self.get_response(request)

    def checkRbacTasks(self, request, url_path: str, user: CustomUser):
        try:
            if not user.has_superadmin_role:
                print(url_path)
                task = RbacTasks.objects.get(urlPath=url_path)
                if task:
                    task_roles = task.get_roles_array()
                    user_roles = user.get_roles_array()

                    if not user.has_superadmin_role:
                        if not user.belongs_to_an_organisation():
                            response = create_response(
                                403, "UNAUTHORISED", "User does not belong to an organisation"
                            )
                            return response

                        if not roles_match(user_roles, task_roles):
                            response = create_response(
                                413,
                                "UNAUTHORISED",
                                f"User is not authorised to access task {{ {task.task} }}",
                            )
                            return response

        except RbacTasks.DoesNotExist as e:
            logger.exception("RBAC Task does not exist")
            response = create_response(502, "Task Not Found", str(e))
            return response
