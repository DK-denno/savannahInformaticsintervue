from rest_framework import serializers
from .models import CustomUser, RbacTasks, Organisation, Role, ProductCategories,Products, Orders

class CustomUserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'roles', 'first_name', 'last_name']

    def get_roles(self, obj):
        return obj.get_roles_array()

class RbacTasksSerilizer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = RbacTasks
        fields = ['task', 'roles', 'id']

    def get_roles(self, obj):
        return obj.get_roles_array()


class OrganisationsSerializer(serializers.ModelSerializer):
    admin = CustomUserSerializer(read_only=True)
    class Meta:
        model = Organisation
        fields = ['id', 'name', 'primaryPhoneNumber', 'admin']


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['name', 'description']


class ProductCategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategories
        fields = ['id', 'name', 'description']


class ProductSerializer(serializers.ModelSerializer):
    category = ProductCategoriesSerializer(read_only=True)
    class Meta:
        model = Products
        fields = ['id', 'category', 'name', 'price', 'isActive']


class OrdersSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Orders
        fields = ['id', 'orderNumber', 'amountPaid', 'primaryPhoneNumber', 'isFulFilled', 'user', 'product']
