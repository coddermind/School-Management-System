from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import api
from .forms import CustomPasswordResetForm, CustomSetPasswordForm

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('admin/dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('teacher/dashboard/', views.TeacherDashboardView.as_view(), name='teacher_dashboard'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('home/', views.home, name='home'),
    
    # Teacher management
    path('admin/teachers/add/', views.add_teacher, name='add_teacher'),
    path('admin/teachers/<int:pk>/edit/', views.edit_teacher, name='edit_teacher'),
    
    # User management
    path('admin/users/', views.user_list, name='user_list'),
    path('admin/users/add/', views.add_user, name='add_user'),
    path('admin/users/<int:pk>/edit/', views.edit_user, name='edit_user'),
    path('admin/users/<int:pk>/delete/', views.delete_user, name='delete_user'),
    path('admin/users/<int:pk>/', views.user_detail, name='user_detail'),
    
    # Password reset
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             form_class=CustomPasswordResetForm
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             form_class=CustomSetPasswordForm
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ),
         name='password_reset_complete'),
    
    # API endpoints
    path('api/login/', api.LoginAPIView.as_view(), name='api_login'),
    path('api/logout/', api.LogoutAPIView.as_view(), name='api_logout'),
    path('api/user/', api.UserAPIView.as_view(), name='api_user'),
    path('api/change-password/', api.ChangePasswordAPIView.as_view(), name='api_change_password'),
    path('api/student-profile/', api.StudentProfileAPIView.as_view(), name='api_student_profile'),
    path('api/teacher-profile/', api.TeacherProfileAPIView.as_view(), name='api_teacher_profile'),
]
