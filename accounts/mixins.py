from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse_lazy
from django.shortcuts import redirect

def admin_required(view_func):
    """
    Decorator for views that checks that the user is an admin.
    """
    def check_admin(user):
        return user.is_authenticated and user.is_admin
    
    decorated_view = user_passes_test(check_admin, login_url=reverse_lazy('accounts:login'))(view_func)
    return decorated_view

def teacher_required(view_func):
    """
    Decorator for views that checks that the user is a teacher.
    """
    def check_teacher(user):
        return user.is_authenticated and user.is_teacher
    
    decorated_view = user_passes_test(check_teacher, login_url=reverse_lazy('accounts:login'))(view_func)
    return decorated_view

def student_required(view_func):
    """
    Decorator for views that checks that the user is a student.
    """
    def check_student(user):
        return user.is_authenticated and user.is_student
    
    decorated_view = user_passes_test(check_student, login_url=reverse_lazy('accounts:login'))(view_func)
    return decorated_view

class AdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin for class-based views that checks that the user is an admin.
    """
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin
    
    def handle_no_permission(self):
        return redirect('accounts:login')

class TeacherRequiredMixin(UserPassesTestMixin):
    """
    Mixin for class-based views that checks that the user is a teacher.
    """
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_teacher
    
    def handle_no_permission(self):
        return redirect('accounts:login')

class StudentRequiredMixin(UserPassesTestMixin):
    """
    Mixin for class-based views that checks that the user is a student.
    """
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_student
    
    def handle_no_permission(self):
        return redirect('accounts:login')
