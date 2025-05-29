from django.test import TestCase, RequestFactory
from django.http import JsonResponse
from unittest.mock import patch, MagicMock
from django.urls import reverse
from app.middleware.firebase_auth_middleware import FirebaseAuthMiddleware
from app.models import CustomUser, RbacTasks
from app.views import createRolesTask

import requests

class FirebaseAuthMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.api_url = reverse('my_view')
        self.valid_uid = "firebase-uid-123"
        self.valid_token = "valid-firebase-token"
        self.firebase_login("dk@dk.dk1", "dk@dk.dk1")
        self.mock_rbac_task()

        def dummy_view(request):
            return JsonResponse({"message": "ok"})

        self.get_response = dummy_view
        self.middleware = FirebaseAuthMiddleware(get_response=self.get_response)

    def test_public_routes_skip_auth(self):
        public_routes = ['/api/test_view/']
        for route in public_routes:
            request = self.factory.get(route)
            response = self.middleware(request)
            self.assertEqual(response.status_code, 200)

    def test_missing_authorization_header(self):
        request = self.factory.get("/api/test_view/")
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    @patch('firebase_admin.auth.verify_id_token')
    def test_expired_token(self, mock_verify):
        mock_verify.side_effect = ValueError('Token expired')
        request = self.factory.get(self.api_url)
        request.META['HTTP_AUTHORIZATION'] = f"Bearer {self.valid_token}"
        response = self.middleware(request)
        self.assertEqual(response.status_code, 401)

    @patch('firebase_admin.auth.verify_id_token')
    @patch('app.models.CustomUser.objects.get')
    def test_superadmin_bypasses_rbac(self, mock_get_user, mock_verify):
        user = MagicMock()
        user.has_superadmin_role = True
        mock_verify.return_value = {'uid': self.valid_uid}
        mock_get_user.return_value = user

        request = self.factory.get(self.api_url)
        request.META['HTTP_AUTHORIZATION'] = f"Bearer {self.valid_token}"
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    @patch('firebase_admin.auth.verify_id_token')
    @patch('app.models.CustomUser.objects.get')
    def test_organization_requirement(self, mock_get_user, mock_verify):
        user = MagicMock()
        user.has_superadmin_role = False
        user.belongs_to_an_organisation.return_value = False
        mock_verify.return_value = {'uid': self.valid_uid}
        mock_get_user.return_value = user

        request = self.factory.get(self.api_url)
        request.META['HTTP_AUTHORIZATION'] = f"Bearer {self.valid_token}"
        response = self.middleware(request)
        self.assertEqual(response.status_code, 403)

    def test_skip_firebase_auth_decorator(self):
        request = self.factory.get("/api/test_view/")
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    @patch('firebase_admin.auth.verify_id_token')
    @patch('app.models.CustomUser.objects.get')
    def test_all_protected_endpoints(self, mock_get_user, mock_verify):
        user = MagicMock()
        user.has_superadmin_role = True
        mock_verify.return_value = {'uid': self.valid_uid}
        mock_get_user.return_value = user

        protected_endpoints = [
            reverse('createNewUser'),
            reverse('createOrganisation'),
            reverse('getUserDetails'),
            reverse('adminCreateNewUser'),
            reverse('creatOrder'),
        ]

        for endpoint in protected_endpoints:
            request = self.factory.get(endpoint)
            request.META['HTTP_AUTHORIZATION'] = f"Bearer {self.valid_token}"
            response = self.middleware(request)
            self.assertEqual(response.status_code, 200, f"Failed for endpoint: {endpoint}")

    def test_malformed_authorization_header(self):
        malformed_headers = [
            "Bearer",
            "Bearer ",
            "Basic abc123",
            "Token abc123",
            "InvalidFormat"
        ]

        for header in malformed_headers:
            request = self.factory.get(self.api_url)
            request.META['HTTP_AUTHORIZATION'] = header
            response = self.middleware(request)
            self.assertEqual(response.status_code, 401, f"Failed for header: {header}")

    @patch('firebase_admin.auth.verify_id_token')
    @patch('app.models.CustomUser.objects.get')
    def test_user_does_not_exist(self, mock_get_user, mock_verify):
        mock_verify.return_value = {'uid': 'nonexistent'}
        mock_get_user.side_effect = CustomUser.DoesNotExist('User not found')

        request = self.factory.get(self.api_url)
        request.META['HTTP_AUTHORIZATION'] = "Bearer validtoken"
        response = self.middleware(request)
        self.assertEqual(response.status_code, 404)

    @patch('firebase_admin.auth.verify_id_token')
    @patch('app.models.CustomUser.objects.get')
    def test_valid_user_with_invalid_rbac_role(self, mock_get_user, mock_verify):
        user = MagicMock()
        user.has_superadmin_role = False
        user.get_roles_array.return_value = [{"client":True}]
        user.belongs_to_an_organisation.return_value = True
        mock_verify.return_value = {'uid': self.valid_uid}
        mock_get_user.return_value = user

        mock_task = MagicMock()
        mock_task.get_roles_array.return_value = [{"admin":True}]

        request = self.factory.get("/api/my_view/")
        request.META['HTTP_AUTHORIZATION'] = "Bearer validtoken"

        with patch('app.middleware.firebase_auth_middleware.RbacTasks.objects.get', return_value=mock_task):
            response = self.middleware(request)
            self.assertEqual(response.status_code, 413)

    @patch('firebase_admin.auth.verify_id_token')
    @patch('app.models.CustomUser.objects.get')
    def test_valid_user_passes_rbac_check(self, mock_get_user, mock_verify):
        user = MagicMock()
        user.has_superadmin_role = False
        user.get_roles_array.return_value = [{"admin":True}]
        user.belongs_to_an_organisation.return_value = True
        mock_verify.return_value = {'uid': self.valid_uid}
        mock_get_user.return_value = user

        mock_task = MagicMock()
        mock_task.get_roles_array.return_value = [{"admin":True}]

        request = self.factory.get("/api/my_view/")
        request.META['HTTP_AUTHORIZATION'] = "Bearer validtoken"

        with patch('app.middleware.firebase_auth_middleware.RbacTasks.objects.get', return_value=mock_task):
            response = self.middleware(request)
            self.assertEqual(response.status_code, 200)

    def firebase_login(self, email, password):
        url = 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyBxhdAXMPmqdiFnSy77RJuJM2VfsC0OQuQ'
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        res = response.json()
        self.valid_token = res["idToken"]
        self.valid_uid = res["localId"]

    def mock_rbac_task(self):
        mock_rbac_task = RbacTasks (
            urlPath = "/api/my_view/",
            task = "mock-my-view"
        )
        mock_rbac_task.save()
        mock_rbac_task.roles.set(createRolesTask(["admin"]))
        mock_rbac_task.save()