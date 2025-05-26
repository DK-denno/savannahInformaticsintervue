from django.urls import path
from app import views

urlpatterns = [
    path("test_view/", views.test_view, name="test_view"),
    path("my_view/", views.my_view, name="my_view"),
    path("createNewUser/", views.createNewUser, name="createNewUser"),
    path("createOrganisation/", views.createOrganisation, name="createOrganisation"),
    path("getUserDetails/", views.getUserDetails, name="getUserDetails"),
    path("getOrganisationDetails/", views.getOrganisationDetails, name="getOrganisationDetails"),
    path("adminCreateNewUser/", views.adminCreateNewUser, name="adminCreateNewUser"),
    path("createRoles/", views.createRoles, name="createRoles"),
    path("getRoles/", views.getRoles, name="getRoles"),
    path("adminAdRbacTasks/", views.adminAdRbacTasks, name="adminAdRbacTasks"),
    path("adminAddProductCategories/", views.adminAddProductCategories, name="adminAddProductCategories"),
    path("adminListProductCategories/", views.adminListProductCategories, name="adminListProductCategories"),
    path("adminAddProducts/", views.adminAddProducts, name="adminAddProducts"),
    path("adminListProducts/", views.adminListProducts, name="adminListProducts"),
    path("creatOrder/", views.creatOrder, name="creatOrder"),
    path("adminListOrders/", views.adminListOrders, name="adminListOrders"),
    path("clientListOrders/", views.clientListOrders, name="clientListOrders")
]