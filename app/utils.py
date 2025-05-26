import json
from django.contrib.auth import get_user_model
import logging
from .serializer import CustomUserSerializer
from .responses import create_response
from functools import wraps



User = get_user_model()
logger = logging.getLogger(__name__)

def roles_match(user_roles, task_roles):
    def extract_active_roles(roles):
        return {role for r in roles for role, is_active in r.items() if is_active}

    user_active_roles = extract_active_roles(user_roles)
    task_active_roles = extract_active_roles(task_roles)

    return not user_active_roles.isdisjoint(task_active_roles)

def createUser(data: json, uid:str):
    try:
        print("Got here :> ")
        data.firebase_uid = uid
        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.saveUser()
            user = User.objects.get(username=request.data['username'])
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return e

def arrayToString(values: list) -> str:
    return ",".join(map(str, values))

def skip_firebase_auth(view_func):
    view_func.skip_firebase_auth = True
    return view_func

def validateFieldsPassed(data, *fields):
    missing = [f for f in fields if f not in data or not str(data[f]).strip()]
    return missing if missing else None