import logging
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from .utils import createUser, validateFieldsPassed, skip_firebase_auth
from .responses import create_response
from .SMSUtils import SMSUtils
from .EmailUtils import EmailUtils
import json
from .models import Role, CustomUser, Organisation, dynamic_filter, RbacTasks, ProductCategories, Products, Orders, Comms
from firebase_admin import auth
from django.forms.models import model_to_dict
from .serializer import CustomUserSerializer, OrganisationsSerializer, RoleSerializer, RbacTasksSerilizer, ProductCategoriesSerializer, ProductSerializer, OrdersSerializer

from rest_framework.parsers import JSONParser
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from json import JSONDecodeError
import os

import random
import string


logger = logging.getLogger(__name__)

# Create your views here.
@skip_firebase_auth
@api_view(['POST'])
def test_view(request):
    return create_response(200, "Success", {})

@api_view(['POST'])
def my_view(request):
    user = getattr(request, 'firebase_user', None)
    return create_response(404, "Success", {'message': f'Hello {user.username}'})

@skip_firebase_auth
@api_view(['POST'])
def createNewUser(request):
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header.startswith("Bearer "):
        return create_response(401, "unauthorized", "Missing or invalid auth token")

    id_token = auth_header.split("Bearer ")[-1]
    try:
        data = request.data
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token["uid"]

        result = validateFieldsPassed(data, "username", "firstName", "lastName", "phoneNumber", "email")
        if result is not None:
            return create_response(400, "bad request", f"Missing field(s): {result}")

        client_role = Role.objects.get(name="client")
        user = CustomUser(
            username=data.get("username"),
            firebase_uid=uid,
            first_name=data.get("firstName"),
            last_name=data.get("lastName"),
            phoneNumber=data.get("phoneNumber"),
            email=data.get("email")
        )
        user.save()
        user.roles.set([client_role])
        user.save()

        serializer = CustomUserSerializer(instance=user)
        return create_response(201, "User created successfully", serializer.data)

    except Exception as e:
        logger.exception("Something went wrong: %s", e)
        return create_response(500, "internal server error", str(e))


@api_view(['POST'])
def createOrganisation(request):
    try:
        # Decode and parse JSON body
        data = request.data

        # Validate required fields
        result = validateFieldsPassed(data, "name", "primaryPhoneNumber")
        if result is not None:
            return create_response(502, "bad request", f"Expected fields {result}")

        user = request.firebase_user

        # Create organisation
        organisation = Organisation(
            name=data.get("name"),
            primaryPhoneNumber=data.get("primaryPhoneNumber"),
            admin=user
        )
        organisation.save()

        # Try to assign 'admin' role to user
        try:
            admin_role = Role.objects.get(name="admin")
        except Role.DoesNotExist:
            logger.warning("Role 'admin' not found. Creating it.")
            admin_role = Role(name="admin", description="Administrator Role")
            admin_role.save()

        # Set role and link organisation
        user.roles.set([admin_role])
        user.organisation = organisation
        user.save()

        # Serialize and return organisation
        res = OrganisationsSerializer(instance=organisation)
        return create_response(200, "success", res.data)

    except JSONDecodeError as e:
        logger.exception("JSON decode error")
        return create_response(400, "invalid JSON", str(e))

    except ObjectDoesNotExist as e:
        logger.exception("Related object not found")
        return create_response(404, "not found", str(e))

    except ValidationError as e:
        logger.exception("Validation error")
        return create_response(422, "validation error", str(e))

    except Exception as e:
        logger.exception("Unexpected error occurred")
        return create_response(500, "internal server error", str(e))

@api_view(['POST'])
def getUserDetails(request):
    res = CustomUserSerializer(instance=request.firebase_user)
    return create_response(200, "success", res.data)

@api_view(['POST'])
def getOrganisationDetails(request):
    res = OrganisationsSerializer(instance=request.firebase_user.organisation)
    return create_response(200, "success", res.data)

@api_view(['POST'])
def createRoles(request):
    data = request.data

    # Validate required fields
    result = validateFieldsPassed(data, "name", "description")
    if result is not None:
        return create_response(502, "bad request", f"Expected fields {result}")


    role = Role(name=data.get("name"), description=data.get("description"), organisation=request.firebase_user.organisation)
    role.save()
    serializedRoles = RoleSerializer(instance=role)
    return create_response(200, "success", serializedRoles.data)

@api_view(['POST'])
def adminCreateNewUser(request):
    try:
        data = request.data
        result = validateFieldsPassed(data, "username", "firstName", "lastName", "phoneNumber", "email", "authPassword", "role")
        if result is not None:
            return create_response(400, "bad request", f"Missing field(s): {result}")

        email=data.get("email")
        username=data.get("username")
        authPassword=data.get("authPassword")

        filters = {
            "username__icontains":username,
            "email__icontains": email
        }

        existingUser = dynamic_filter(
            CustomUser, filter_type="or", filter_dict=filters)
        if existingUser.exists():
            return create_response(409, "Conflict", "User already exists")
        else:
            user = auth.create_user(
                email=email,
                password=authPassword,
                display_name=username,
            )

            role = Role.objects.get(name=data.get("role"))
            dbuser = CustomUser(
                username=data.get("username"),
                firebase_uid=user.uid,
                first_name=data.get("firstName"),
                last_name=data.get("lastName"),
                phoneNumber=data.get("phoneNumber"),
                email=email,
                organisation=request.firebase_user.organisation
            )
            dbuser.save()
            dbuser.roles.set([role])
            dbuser.save()

            serializer = CustomUserSerializer(instance=dbuser)
            return create_response(201, "User created successfully", serializer.data)

    except Exception as e:
        logger.exception("Something went wrong: %s", e)
        return create_response(500, "internal server error", str(e))


@api_view(['POST'])
def getRoles(request):
    filters = {
        "organisation__isnull": True,
        "organisation": request.firebase_user.organisation
    }

    existingRole = dynamic_filter(
        Role, filter_type="or", filter_dict=filters)

    res = RoleSerializer(instance=existingRole, many=True)
    return create_response(200, "success", res.data)


@api_view(['POST'])
def listRbacTasks(request):
    filters = {
        "organisation__isnull": True,
        "organisation": request.firebase_user.organisation
    }

    rbacTasks = dynamic_filter(
        RbacTasks, filter_type="or", filter_dict=filters)

    res = RoleSerializer(instance=rbacTasks, many=True)
    return create_response(200, "success", res.data)


@api_view(['POST'])
def adminAdRbacTasks(request):
    try:

        data = request.data
        result = validateFieldsPassed(data, "urlPath", "task", "roles")
        if result is not None:
            return create_response(400, "bad request", f"Missing field(s): {result}")

        roles = data.get("roles")
        task = RbacTasks(
            organisation = request.firebase_user.organisation,
            urlPath = data.get("urlPath"),
            task = data.get("task"),
        )
        task.saveTask(request.firebase_user)
        task.roles.set(createRolesTask(data.get("roles", [])))
        task.saveTask(request.firebase_user)
        res = RbacTasksSerilizer(instance=task)
        return create_response(200, "success", res.data)
    except Exception as e:
        logger.exception("Something went wrong: %s", e)
        return create_response(500, "internal server error", str(e))


def createRolesTask(roles: list) -> list:
    result = []
    for role in roles:
        try:
            role = Role.objects.get(name=role)
            result.append(role)
        except Role.DoesNotExist:
            role = Role(
                name=role
            )
            role.save()
            result.append(role)
    return result

@api_view(['POST'])
def adminAddProductCategories(request):
    try:

        data = request.data
        result = validateFieldsPassed(data, "name", "description")
        if result is not None:
            return create_response(400, "bad request", f"Missing field(s): {result}")

        filters = {
            "name": data.get("name")
        }

        existingCategory = dynamic_filter(
            ProductCategories, filter_type="or", filter_dict=filters)

        if existingCategory.exists():
            return create_response(409, "Conflict", "Category already exists")
        else:
            category = ProductCategories(
                name = data.get("name"),
                description = data.get("description"),
            )
            category.save()
            res = ProductCategoriesSerializer(instance=category)
            return create_response(200, "success", res.data)
    except Exception as e:
        logger.exception("Something went wrong: %s", e)
        return create_response(500, "internal server error", str(e))


@api_view(['POST'])
def adminListProductCategories(request):
    try:
        filters = {}

        for key, value in request.data.items():
            if key and value is not None and str(value).strip() != "":
                filters[f"{key}__icontains"] = value

        if filters:
            existingCategory = dynamic_filter(
                ProductCategories, filter_type="or", filter_dict=filters)
        else:
            existingCategory = ProductCategories.objects.all()

        res = ProductCategoriesSerializer(instance=existingCategory, many=True)
        return create_response(200, "success", res.data)

    except Exception as e:
        logger.exception("Something went wrong: %s", e)
        return create_response(500, "internal server error", str(e))

@api_view(['POST'])
def adminAddProducts(request):
    try:

        data = request.data
        result = validateFieldsPassed(data, "category", "name", "price", "isActive")
        if result is not None:
            return create_response(400, "bad request", f"Missing field(s): {result}")

        filters = {
            "name": data.get("name"),
            "organisation": request.firebase_user.organisation
        }

        existingProduct = dynamic_filter(
            Products, filter_type="and", filter_dict=filters)

        if existingProduct.exists():
            return create_response(504, "Product Already exists", ProductSerializer(instance=existingProduct, many=True).data)
        else:
            category = ProductCategories.objects.get(pk=data.get("category"))
            product = Products(
                organisation = request.firebase_user.organisation,
                name = data.get("name"),
                price = data.get("price"),
                isActive = data.get("isActive"),
                category=category
            )
            product.saveProduct(request.firebase_user)
            res = ProductSerializer(instance=product)
            return create_response(200, "success", res.data)
    except Exception as e:
        logger.exception("Something went wrong: %s", e)
        return create_response(500, "internal server error", str(e))


@api_view(['POST'])
def adminListProducts(request):
    try:
        filters = {}
        for key, value in request.data.items():
            if key and value is not None and str(value).strip() != "":
                filters[f"{key}__icontains"] = value

        if filters:
            existingProduct = dynamic_filter(
                Products, filter_type="or", filter_dict=filters)
        else:
            existingProduct = Products.objects.all()

        res = ProductSerializer(instance=existingProduct, many=True)
        return create_response(200, "success", res.data)
    except Exception as e:
        logger.exception("Something went wrong: %s", e)
        return create_response(500, "internal server error", str(e))


@api_view(['POST'])
def creatOrder(request):
    try:
        data = request.data
        result = validateFieldsPassed(data, "productId")
        if result is not None:
            return create_response(400, "bad request", f"Missing field(s): {result}")

        product = Products.objects.get(pk=data.get("productId"))
        order = createOrder(request.firebase_user, product, data)
        sendSmSMessage(order)
        sendEmailMessage(order)
        # res = ProductSerializer(instance=existingProduct, many=True)
        return create_response(200, "success", {})
    except Exception as e:
        logger.exception("Something went wrong: %s", e)
        return create_response(500, "internal server error", str(e))


def generate_random_alphanumeric(length=8):
    characters = string.ascii_letters + string.digits  # a-zA-Z0-9
    return ''.join(random.choices(characters, k=length))

def createOrder(user, product, data) -> Orders:
    order = Orders (
        user = user,
        product = product,
        amountPaid = 0.0,
        primaryPhoneNumber = data.get("phoneNumber", user.phoneNumber),
        orderNumber=generate_random_alphanumeric(6)
    )
    order.save()
    return order

def createUserMessageFromOrder(order) -> str:
    try:
        data = {
            "username":order.user.username,
            "amount":str(order.product.price),
            "organisationName":order.product.organisation.name,
            "orderNumber": order.orderNumber
        }
        message = (
            "Dear {username}, we have received your order of "
            "KES {amount}/=. Your order number is {orderNumber}. "
            "This has been logged and received by {organisationName}. "
            "We will send you updates on your package throughout the "
            "shipping process. Thank you for shopping with us."
        )

        return message.format(**data)
    except Exception as e:
        logger.exception("Something went wrong: %s", e)
        return create_response(500, "internal server error", str(e))

def sendSmSMessage(order):
    try:
        sms = SMSUtils(order.primaryPhoneNumber, createUserMessageFromOrder(order))
        api_key = os.environ.get("AT_API_KEY")
        username = os.environ.get("AT_USERNAME")
        response = sms.send_via_africastalking(
            api_key=api_key,
            username=username
        )

        print("Status:", sms.status)
        print("API Response:", response)
        comms = Comms(
            receipientPhoneNumber = order.primaryPhoneNumber,
            recipientEmail = "",
            communicationType = "SMS",
            status = sms.status,
            reason = response
        )
        comms.save()
    except Exception as e:
        logger.exception("Something went wrong: %s", e)
        return create_response(500, "internal server error", str(e))

@api_view(['POST'])
def adminListOrders(request):
    try:
        filters = {}
        for key, value in request.data.items():
            if key and value is not None and str(value).strip() != "":
                filters[f"{key}__icontains"] = value

        if filters:
            existingOrders = dynamic_filter(
                Products, filter_type="or", filter_dict=filters)
        else:
            existingOrders = Orders.objects.all()

        res = OrdersSerializer(instance=existingOrders, many=True)
        return create_response(200, "success", res.data)
    except Exception as e:
        logger.exception("Something went wrong: %s", e)
        return create_response(500, "internal server error", str(e))

@api_view(['POST'])
def clientListOrders(request):
    try:
        filters = {}
        for key, value in request.data.items():
            if key and value is not None and str(value).strip() != "":
                filters[f"{key}__icontains"] = value

        if filters:
            filters["userId"] = request.firebase_user.id
            existingOrders = dynamic_filter(
                Products, filter_type="or", filter_dict=filters)
        else:
            existingOrders = Orders.objects.filter(user=request.firebase_user)

        res = OrdersSerializer(instance=existingOrders, many=True)
        return create_response(200, "success", res.data)
    except Exception as e:
        logger.exception("Something went wrong: %s", e)
        return create_response(500, "internal server error", str(e))

def createAdminEmailMessageFromOrder(order) -> str:
    try:
        data = {
            "username":order.user.username,
            "productName":order.product.name,
            "price":str(order.product.price),
            "organisationName":order.product.organisation.name,
            "userPhoneNumber":order.user.phoneNumber
        }
        message = (
            "Dear {organisationName} admin, We have a logged a new order"
            " with the following details :- \n"
            " Product Name: {productName} \n"
            " Product Price: {price}\n"
            " Customer name: {username}\n"
            " Customer Phone Number: {userPhoneNumber}\n"
        )

        return message.format(**data)
    except Exception as e:
        logger.exception("Something went wrong: %s", e)
        return create_response(500, "internal server error", str(e))

def sendEmailMessage(order):
    try:
        email_util = EmailUtils(
            to_email=order.product.organisation.admin.email,
            subject="You have a new pending Order #{}".format(order.orderNumber),
            message=createAdminEmailMessageFromOrder(order)
        )
        email_util.send_email()

        print("Status:", email_util.status)
        print("API Response:", email_util.response)
        comms = Comms(
            receipientPhoneNumber = "",
            recipientEmail = order.product.organisation.admin.email,
            communicationType = "EMAIL",
            status = email_util.status,
            reason = email_util.response
        )
        comms.save()
    except Exception as e:
        logger.exception("Something went wrong: %s", e)
        return create_response(500, "internal server error", str(e))