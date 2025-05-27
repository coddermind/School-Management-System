from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, StudentProfile, TeacherProfile

class UserAdmin(BaseUserAdmin):
    """Custom User Admin"""
    
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('user_type', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'user_type', 'profile_pic', 'phone_number', 'address', 'date_of_birth')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'user_type'),
        }),
    )

class StudentProfileAdmin(admin.ModelAdmin):
    """Student Profile Admin"""
    
    list_display = ('user', 'admission_number', 'parent_name', 'parent_phone')
    search_fields = ('admission_number', 'user__email', 'user__first_name', 'user__last_name', 'parent_name')
    
class TeacherProfileAdmin(admin.ModelAdmin):
    """Teacher Profile Admin"""
    
    list_display = ('user', 'employee_id', 'qualification', 'experience', 'joining_date')
    search_fields = ('employee_id', 'user__email', 'user__first_name', 'user__last_name', 'qualification')
    list_filter = ('joining_date',)

# Register the models
admin.site.register(User, UserAdmin)
admin.site.register(StudentProfile, StudentProfileAdmin)
admin.site.register(TeacherProfile, TeacherProfileAdmin)
