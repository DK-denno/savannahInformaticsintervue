from django.test import TestCase
from django.contrib.auth import get_user_model
from app.utils import (
    roles_match,
    arrayToString,
    validateFieldsPassed,
    skip_firebase_auth,
)
from rest_framework.test import APIRequestFactory
from rest_framework.decorators import api_view

User = get_user_model()

class UtilityFunctionTests(TestCase):

    def test_roles_match_with_overlap(self):
        user_roles = [{"admin": True}, {"editor": False}]
        task_roles = [{"admin": True}]
        self.assertTrue(roles_match(user_roles, task_roles))

    def test_roles_match_without_overlap(self):
        user_roles = [{"admin": True}]
        task_roles = [{"editor": True}]
        self.assertFalse(roles_match(user_roles, task_roles))

    def test_arrayToString(self):
        values = [1, 2, 3]
        result = arrayToString(values)
        self.assertEqual(result, "1,2,3")

    def test_arrayToString_empty(self):
        result = arrayToString([])
        self.assertEqual(result, "")

    def test_validateFieldsPassed_all_present(self):
        data = {"username": "john", "email": "john@example.com"}
        result = validateFieldsPassed(data, "username", "email")
        self.assertIsNone(result)

    def test_validateFieldsPassed_missing_fields(self):
        data = {"username": "john"}
        result = validateFieldsPassed(data, "username", "email")
        self.assertEqual(result, ["email"])

    def test_validateFieldsPassed_empty_string(self):
        data = {"username": "   "}
        result = validateFieldsPassed(data, "username")
        self.assertEqual(result, ["username"])

    def test_skip_firebase_auth_decorator(self):
        @skip_firebase_auth
        @api_view(['GET'])
        def dummy_view(request):
            return "ok"

        self.assertTrue(hasattr(dummy_view, 'skip_firebase_auth'))
        self.assertTrue(dummy_view.skip_firebase_auth)