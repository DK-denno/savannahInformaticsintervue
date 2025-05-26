from django.contrib import admin

from app.models import *

# Register your models here.
admin.site.register(Role)
admin.site.register(Organisation)


class CustomUserAdmin(admin.ModelAdmin):
    filter_horizontal = ('roles',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return CustomUser.filter_by_user_role(qs, request.user)

class RbacTasksAdmin(admin.ModelAdmin):
    filter_horizontal = ('roles',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return RbacTasks.filter_by_user_role(qs, request.user)

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(RbacTasks, RbacTasksAdmin)
admin.site.register(ProductCategories)
admin.site.register(Products)
