from django.contrib import admin
from users.models import CaptainUser
from django.contrib.auth.admin import UserAdmin
from django.forms import TextInput, Textarea, CharField
from django import forms
from django.db import models


class UserAdminConfig(UserAdmin):
    model = CaptainUser
    search_fields = ('email', 'display_name',)
    list_filter = ('email', 'display_name', 'is_active', 'is_staff')
    ordering = ('-start_date',)
    list_display = ('email', 'display_name', 'id',
                    'is_active', 'is_staff')
    fieldsets = (
        (None, {'fields': ('email', 'display_name')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups')}),
        ('Personal', {'fields': ('about',)}),
    )
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 20, 'cols': 60})},
    }
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'display_name', 'password1', 'password2', 'is_active', 'is_staff')}
         ),
    )


admin.site.register(CaptainUser, UserAdminConfig)
