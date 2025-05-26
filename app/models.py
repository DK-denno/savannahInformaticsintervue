from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q

class Role(models.Model):
    name = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=80, blank=True, null=True)
    organisation = models.ForeignKey('Organisation', on_delete=models.SET_NULL, related_name='role_organisation', null=True, blank=True)

    def __str__(self):
        return self.name

class Organisation(models.Model):
    name = models.CharField(max_length=128, unique=True)
    primaryPhoneNumber = models.CharField(max_length=128, unique=True)
    admin = models.OneToOneField('CustomUser', on_delete=models.SET_NULL, related_name='admin_organisation', null=True)

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    organisation = models.ForeignKey(Organisation, on_delete=models.SET_NULL, related_name="user_organisation", null=True, blank=True)
    firebase_uid = models.CharField(max_length=128, unique=True)
    phoneNumber = models.CharField(max_length=15)
    roles = models.ManyToManyField(Role, related_name='roles_users')

    def __str__(self):
        return self.username

    def get_roles_array(self):
        return [{role.name: True} for role in self.roles.all()]

    def has_superadmin_role(self):
        return any(r.get("superadmin") or r.get("super_admin") for r in self.get_roles_array()) or self.is_superuser

    def belongs_to_an_organisation(self):
        return self.organisation is not None

    def saveUser(self, user, *args, **kwargs):
        self.organisation = user.organisation
        super().save(*args, **kwargs)

    @staticmethod
    def filter_by_user_role(queryset, user):
        if user.has_superadmin_role():
            return queryset
        return queryset.filter(organisation=user.organisation)

class RbacTasks(models.Model):
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name="rbac_organisation", null=True, blank=True)
    urlPath = models.CharField(max_length=128, null=True, blank=True)
    task = models.CharField(max_length=128, unique=True, null=True, blank=True)
    roles = models.ManyToManyField(Role, related_name='rbac_users', blank=True)

    def __str__(self):
        return self.task + " for path - " + self.urlPath

    def validateOrganisation(self, user):
        # Ensure the admin user belongs to this organisation
        if user.organisation is not self.organisation and not user.has_superadmin_role():
            raise ValidationError("Admin user must belong to this organisation.")

    def saveTask(self, user, *args, **kwargs):
        self.validateOrganisation(user)
        self.organisation = user.organisation
        super().save(*args, **kwargs)

    @staticmethod
    def filter_by_user_role(queryset, user):
        if user.has_superadmin_role():
            return queryset
        return queryset.filter(organisation=user.organisation)

    def get_roles_array(self):
        return [{role.name: True} for role in self.roles.all()]


class ProductCategories(models.Model):
    name = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=100, unique=True, blank=True, null=True)

    def __str__(self):
        return self.name

class Products(models.Model):
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name="product_organisations")
    category = models.ForeignKey(ProductCategories, on_delete=models.CASCADE, related_name="product_categories")
    name = models.CharField(max_length=100, unique=True)
    price = models.FloatField()
    isActive = models.BooleanField(default=True)

    def __str__(self):
        return self.name + " @ " + str(self.price) +"/= " + self.organisation.name

    def validateOrganisation(self, user):
        # Ensure the admin user belongs to this organisation
        if user.organisation is not self.organisation and not user.has_superadmin_role():
            raise ValidationError("Admin user must belong to this organisation.")

    def saveProduct(self, user, *args, **kwargs):
        self.validateOrganisation(user)
        self.organisation = user.organisation
        super().save(*args, **kwargs)


    @staticmethod
    def filter_by_user_role(queryset, user):
        if user.has_superadmin_role():
            return queryset
        return queryset.filter(organisation=user.organisation)


class Orders(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="order_users")
    orderNumber = models.CharField(max_length=100, unique=True)
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name="product_orders")
    amountPaid = models.FloatField(default=0.0)
    primaryPhoneNumber = models.CharField(max_length=100)
    isFulFilled = models.BooleanField(default=False)

    def __str__(self):
        return self.product.name + " @ KES " + str(product.price)

    @staticmethod
    def filter_by_user_role(queryset, user):
        if user.has_superadmin_role():
            return queryset
        return queryset.filter(organisation=user.organisation)

class Comms(models.Model):
    receipientPhoneNumber = models.CharField(max_length=100)
    recipientEmail = models.CharField(max_length=100)
    communicationType = models.CharField(max_length=10)
    status = models.CharField(max_length=50)
    reason = models.CharField(max_length=300)

    def __str__(self):
        return "Phone: " + self.receipientPhoneNumber + " Email: " + self.recipientEmail +  " Type" + self.communicationType + " Status: " + self.status



def dynamic_filter(model_class, filter_type="and", filter_dict=None):
    """
    Dynamically filter a Django model using AND/OR conditions with a dictionary.

    Args:
        model_class: The Django model class (e.g., MyModel)
        filter_type: 'and' or 'or'
        filter_dict: Dictionary of field-value pairs (e.g., {"name": "Alice", "age__gte": 25})

    Returns:
        QuerySet
    """
    if not filter_dict:
        return model_class.objects.none()

    q_objects = [Q(**{key: value}) for key, value in filter_dict.items()]

    if filter_type.lower() == "or":
        query = Q()
        for q in q_objects:
            query |= q
    else:  # default to AND
        query = Q()
        for q in q_objects:
            query &= q

    return model_class.objects.filter(query)