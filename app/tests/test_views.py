from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock
from app.models import CustomUser, Role, Organisation
from rest_framework import status
import requests
import time


class ViewsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.role_client, _ = Role.objects.get_or_create(name="client")
        self.role_admin, _ = Role.objects.get_or_create(name="admin")
        self.valid_token = ""
        self.firebase_login("dk@dk.dk1", "dk@dk.dk1")
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="dk@dk.dk",
            phoneNumber="123456789",
            firebase_uid=self.valid_token,
            first_name="John",
            last_name="Doe",
        )

        self.user.roles.add(self.role_client)
        self.client.force_authenticate(user=self.user)

    # -------- /test --------
    def test_test_view(self):
        response = self.client.post("/api/test_view/")
        self.assertEqual(response.status_code, 200)

    # # -------- /createNewUser --------
    @patch("firebase_admin.auth.verify_id_token")
    def test_create_new_user_missing_fields(self, mock_verify_token):
        mock_verify_token.return_value = {"uid": "abc123"}
        data = {}
        response = self.client.post("/api/createNewUser/", HTTP_AUTHORIZATION="Bearer " + self.valid_token, data=data, format="json")
        self.assertEqual(response.status_code, 400)

    # -------- /createOrganisation --------
    def test_create_organisation_success(self):
        data = {
            "name": "MyOrg",
            "primaryPhoneNumber": "5555555"
        }
        response = self.client.post("/api/createOrganisation/", HTTP_AUTHORIZATION="Bearer " + self.valid_token, data=data, format="json")
        self.assertEqual(response.status_code, 200)

    def test_create_organisation_missing_fields(self):
        response = self.client.post("/api/createOrganisation/", HTTP_AUTHORIZATION="Bearer " + self.valid_token, data={}, format="json")
        self.assertEqual(response.status_code, 502)

    # # -------- /adminCreateNewUser --------
    @patch("firebase_admin.auth.create_user")
    def test_admin_create_new_user_success(self, mock_create_user):
        self.user.roles.add(self.role_admin)
        mock_create_user.return_value = MagicMock(uid="firebase456")
        data = {
            "username": "adminuser",
            "firstName": "Admin",
            "lastName": "User",
            "phoneNumber": "7777777",
            "email": "admin@example.com",
            "authPassword": "password123",
            "role": "admin"
        }
        response = self.client.post("/api/adminCreateNewUser/", HTTP_AUTHORIZATION="Bearer " + self.valid_token, data=data, format="json")
        self.assertEqual(response.status_code, 201)

    def test_admin_create_user_conflict(self):
        CustomUser.objects.create(
            username="existinguser",
            email="existing@example.com",
            phoneNumber="7777777"
        )
        self.user.roles.add(self.role_admin)
        data = {
            "username": "existinguser",
            "firstName": "Test",
            "lastName": "Test",
            "phoneNumber": "7777777",
            "email": "existing@example.com",
            "authPassword": "pass123",
            "role": "admin"
        }
        response = self.client.post("/api/adminCreateNewUser/", HTTP_AUTHORIZATION="Bearer " + self.valid_token, data=data, format="json")
        self.assertEqual(response.status_code, 409)

    # # -------- /getUserDetails --------
    def test_get_user_details_success(self):
        response = self.client.post("/api/getUserDetails/", HTTP_AUTHORIZATION="Bearer " + self.valid_token, data={}, format="json")
        self.assertEqual(response.status_code, 200)

    # # -------- /createRoles --------
    def test_create_roles_success(self):
        data = {
            "name": "Manager",
            "description": "Manager role"
        }
        response = self.client.post("/api/createRoles/", HTTP_AUTHORIZATION="Bearer " + self.valid_token, data=data, format="json")
        self.assertEqual(response.status_code, 200)

    def test_create_roles_invalid(self):
        response = self.client.post("/api/createRoles/", HTTP_AUTHORIZATION="Bearer " + self.valid_token, data={}, format="json")
        self.assertEqual(response.status_code, 502)

    # # -------- /createCategory --------
    def test_create_category_success(self):
        data = {"name": "Electronics", "description": "def jaaam"}
        response = self.client.post("/api/adminAddProductCategories/", HTTP_AUTHORIZATION="Bearer " + self.valid_token, data=data, format="json")
        self.assertEqual(response.status_code, 200)

    def test_create_category_duplicate(self):
        data = {"name": "Electronics", "description": "def jaaam"}
        response = self.client.post("/api/adminAddProductCategories/", HTTP_AUTHORIZATION="Bearer " + self.valid_token, data=data, format="json")
        response2 = self.client.post("/api/adminAddProductCategories/", HTTP_AUTHORIZATION="Bearer " + self.valid_token, data=data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response2.status_code, 409)

    # # -------- /createProduct --------
    def test_create_product(self):
        #create category
        data = {"name": "Electronics", "description": "def jaaam"}
        response = self.client.post("/api/adminAddProductCategories/", HTTP_AUTHORIZATION="Bearer " + self.valid_token, data=data, format="json")

        #Create Org
        data = {
            "name": "MyOrg",
            "primaryPhoneNumber": "5555555"
        }
        response = self.client.post("/api/createOrganisation/", HTTP_AUTHORIZATION="Bearer " + self.valid_token, data=data, format="json")

        data2 = {
            "category":1,
            "name":"test prodct",
            "price":200.0,
            "isActive":True
        }
        response2 = self.client.post("/api/adminAddProducts/", HTTP_AUTHORIZATION="Bearer " + self.valid_token, data=data2, format="json")
        self.assertEqual(response2.status_code, 200)

    def test_create_product_missing_fields(self):
        response = self.client.post("/api/adminAddProducts/", HTTP_AUTHORIZATION="Bearer " + self.valid_token, data={}, format="json")
        self.assertEqual(response.status_code, 400)


    def createTestCaseUser(self, uid):
        user = CustomUser(
            username="testUserName",
            first_name="testUserfName",
            last_name="testUserLname",
            phoneNumber="987654321",
            email="alice@example.com",
            firebase_uid=uid
        )
        user.save()
        time.sleep(3)

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
        self.createTestCaseUser(self.valid_uid)