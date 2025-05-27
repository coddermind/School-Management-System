from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseRedirect
from django import forms
from django.contrib.auth.decorators import login_required as django_login_required
from django.utils import timezone
from django.db.models import Q
from django.db.models import Count

from .forms import (
    CustomAuthenticationForm, UserRegistrationForm, UserUpdateForm, 
    StudentProfileForm, TeacherProfileForm, CustomPasswordChangeForm,
    CustomPasswordResetForm, CustomSetPasswordForm, AdminUserForm
)
from .models import User, StudentProfile, TeacherProfile
from academics.models import Student, Timetable, Assignment, AssignmentSubmission, Attendance, Exam
from administration.models import Subject
from communication.models import Message
from .mixins import admin_required, teacher_required, student_required

# Create a custom login_required decorator with the correct login URL
login_required = lambda view_func: django_login_required(login_url=reverse_lazy('accounts:login'))(view_func)

def login_view(request):
    """View for user login"""
    if request.user.is_authenticated:
        if request.user.is_admin:
            return redirect('accounts:admin_dashboard')
        elif request.user.is_teacher:
            return redirect('accounts:teacher_dashboard')
        else:
            return redirect('accounts:student_dashboard')
            
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.get_full_name() or user.email}!")
                next_url = request.GET.get('next', None)
                if next_url:
                    return redirect(next_url)
                if user.is_admin:
                    return redirect('accounts:admin_dashboard')
                elif user.is_teacher:
                    return redirect('accounts:teacher_dashboard')
                else:
                    return redirect('accounts:student_dashboard')
    else:
        form = CustomAuthenticationForm()
        
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    """View for user logout"""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('/accounts/login/?next=/')

@method_decorator(login_required, name='dispatch')
class ProfileView(TemplateView):
    """View for user profile"""
    template_name = 'accounts/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user_form'] = UserUpdateForm(instance=user)
        
        if user.is_student:
            try:
                student_profile = user.student_profile
                context['profile_form'] = StudentProfileForm(instance=student_profile)
            except StudentProfile.DoesNotExist:
                context['profile_form'] = StudentProfileForm()
        
        elif user.is_teacher:
            try:
                teacher_profile = user.teacher_profile
                context['profile_form'] = TeacherProfileForm(instance=teacher_profile)
            except TeacherProfile.DoesNotExist:
                context['profile_form'] = TeacherProfileForm()
                
        return context
    
    def post(self, request, *args, **kwargs):
        user = request.user
        user_form = UserUpdateForm(request.POST, request.FILES, instance=user)
        
        if user.is_student:
            try:
                student_profile = user.student_profile
                profile_form = StudentProfileForm(request.POST, instance=student_profile)
            except StudentProfile.DoesNotExist:
                profile_form = StudentProfileForm(request.POST)
        
        elif user.is_teacher:
            try:
                teacher_profile = user.teacher_profile
                profile_form = TeacherProfileForm(request.POST, instance=teacher_profile)
            except TeacherProfile.DoesNotExist:
                profile_form = TeacherProfileForm(request.POST)
        else:
            profile_form = None
            
        if user_form.is_valid() and (profile_form is None or profile_form.is_valid()):
            user_form.save()
            
            if profile_form:
                profile = profile_form.save(commit=False)
                profile.user = user
                profile.save()
                
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('accounts:profile')
        
        context = self.get_context_data(**kwargs)
        context['user_form'] = user_form
        if profile_form:
            context['profile_form'] = profile_form
        return render(request, self.template_name, context)

class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to check if user is admin"""
    def test_func(self):
        return self.request.user.is_admin

class TeacherRequiredMixin(UserPassesTestMixin):
    """Mixin to check if user is teacher"""
    def test_func(self):
        return self.request.user.is_teacher

class StudentRequiredMixin(UserPassesTestMixin):
    """Mixin to check if user is student"""
    def test_func(self):
        return self.request.user.is_student

@method_decorator(login_required, name='dispatch')
class AdminDashboardView(AdminRequiredMixin, TemplateView):
    """View for admin dashboard"""
    template_name = 'accounts/admin_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Import models
        from academics.models import Student
        from administration.models import Grade, Subject
        
        # Count data for dashboard
        context['total_students'] = Student.objects.count()
        context['total_teachers'] = User.objects.filter(user_type='TEACHER').count()
        context['total_classes'] = Grade.objects.count()
        context['total_subjects'] = Subject.objects.count()
        
        # Get recent models if they exist
        try:
            from communication.models import Announcement, Event
            from finance.models import FeePayment, SalaryPayment
            
            # Recent announcements
            context['recent_announcements'] = Announcement.objects.order_by('-created_at')[:5]
            
            # Recent fee payments
            context['recent_fee_payments'] = FeePayment.objects.order_by('-payment_date')[:5]
            
            # Upcoming events
            context['upcoming_events'] = Event.objects.filter(
                end_date__gte=timezone.now()
            ).order_by('start_date')[:5]
            
            # Recent salary payments
            context['recent_salary_payments'] = SalaryPayment.objects.order_by('-payment_date')[:5]
        except (ImportError, NameError):
            # Handle case where models don't exist yet
            pass
            
        return context

@method_decorator(login_required, name='dispatch')
class TeacherDashboardView(TeacherRequiredMixin, TemplateView):
    """View for teacher dashboard"""
    template_name = 'accounts/teacher_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the teacher's assigned class subjects
        class_subjects = self.request.user.teaching_subjects.all().select_related('grade', 'subject', 'section')
        
        # Count metrics for dashboard
        context['total_classes'] = class_subjects.count()
        context['total_subjects'] = class_subjects.values('subject').distinct().count()
        
        # Try to get assignments if the module exists
        try:
            from academics.models import Assignment
            context['total_assignments'] = Assignment.objects.filter(teacher=self.request.user).count()
        except (ImportError, NameError):
            context['total_assignments'] = 0
        
        # Try to get messages if the module exists  
        try:
            from communication.models import Message
            context['total_messages'] = Message.objects.filter(receiver=self.request.user, is_read=False).count()
        except (ImportError, NameError):
            context['total_messages'] = 0
        
        # Get class subject details for display
        subjects_data = []
        for cs in class_subjects:
            section_name = f"Section {cs.section.name}" if cs.section else "All Sections"
            subjects_data.append({
                'id': cs.id,
                'grade': cs.grade.display_name,
                'section': section_name,
                'subject': cs.subject.name,
                'subject_code': cs.subject.code
            })
        
        context['subjects_data'] = subjects_data
        
        return context

@login_required
@student_required
def student_dashboard(request):
    """Student dashboard view"""
    try:
        student = Student.objects.get(user=request.user)
        
        # Get all subjects for the student's grade
        subjects = Subject.objects.filter(
            class_subjects__grade=student.grade
        ).distinct()
        
        # Get today's classes
        today = timezone.now().date()
        today_classes = Timetable.objects.filter(
            grade=student.grade,
            section=student.section,
            day__day=today.weekday() + 1  # Monday is 1, Sunday is 7
        ).order_by('time_slot__start_time')
        
        # Get pending assignments
        pending_assignments = Assignment.objects.filter(
            grade=student.grade,
            subject__in=subjects,
            due_date__gte=today
        ).exclude(
            submissions__student=student
        ).order_by('due_date')
        
        # Get upcoming exams through ExamSchedule
        upcoming_exams = Exam.objects.filter(
            grade=student.grade,
            schedules__subject__in=subjects,
            start_date__gte=today
        ).distinct().order_by('start_date')
        
        # Get attendance records
        attendance_records = Attendance.objects.filter(
            student=student,
            subject__in=subjects
        )
        
        # Calculate attendance percentage
        total_classes = attendance_records.count()
        if total_classes > 0:
            present_classes = attendance_records.filter(is_present=True).count()
            attendance_percentage = (present_classes / total_classes) * 100
        else:
            attendance_percentage = 0
            
        # Get unread messages
        unread_messages = Message.objects.filter(
            receiver=request.user,
            is_read=False
        ).count()
        
        context = {
            'student': student,
            'subjects': subjects,
            'today_classes': today_classes,
            'pending_assignments': pending_assignments,
            'upcoming_exams': upcoming_exams,
            'attendance_percentage': attendance_percentage,
            'unread_messages': unread_messages,
        }
        return render(request, 'accounts/student_dashboard.html', context)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('accounts:profile')

@login_required
def change_password(request):
    """View for changing password"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your password has been changed successfully!")
            return redirect('accounts:profile')
    else:
        form = CustomPasswordChangeForm(user=request.user)
        
    return render(request, 'accounts/change_password.html', {'form': form})

@login_required
def home(request):
    """Redirect to the appropriate dashboard based on user type"""
    if request.user.is_admin:
        return redirect('accounts:admin_dashboard')
    elif request.user.is_teacher:
        return redirect('accounts:teacher_dashboard')
    else:
        return redirect('accounts:student_dashboard')

@login_required
@admin_required
def add_teacher(request):
    """View to add a new teacher"""
    if request.method == 'POST':
        # Use UserUpdateForm instead of UserRegistrationForm to avoid password fields
        user_form = UserUpdateForm(request.POST, request.FILES)
        profile_form = TeacherProfileForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            # Create user with default password
            user = user_form.save(commit=False)
            user.user_type = 'TEACHER'
            user.set_password('teacher123')  # Set default password
            user.save()
            
            # Create the teacher profile
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            
            # Create salary structure if basic_salary is provided
            if profile.basic_salary > 0:
                from finance.models import SalaryStructure
                from django.utils import timezone
                
                # Check if salary structure doesn't already exist
                if not hasattr(user, 'salary_structure'):
                    SalaryStructure.objects.create(
                        teacher=user,
                        basic_salary=profile.basic_salary,
                        effective_date=profile.joining_date or timezone.now().date()
                    )
            
            messages.success(request, f'Teacher {user.get_full_name()} added successfully with default password: teacher123')
            return redirect('academics:teacher_list')
    else:
        user_form = UserUpdateForm()
        profile_form = TeacherProfileForm()
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    return render(request, 'accounts/teacher_form.html', context)

@login_required
@admin_required
def edit_teacher(request, pk):
    """View to edit a teacher"""
    user = get_object_or_404(User, pk=pk, user_type='TEACHER')
    
    try:
        profile = user.teacher_profile
    except TeacherProfile.DoesNotExist:
        # Create an empty profile if it doesn't exist
        profile = TeacherProfile(user=user)
        profile.save()
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, request.FILES, instance=user)
        profile_form = TeacherProfileForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Teacher updated successfully!')
            return redirect('academics:teacher_list')
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = TeacherProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'teacher': user
    }
    return render(request, 'accounts/teacher_form.html', context)

@login_required
@admin_required
def user_list(request):
    """View to list all users"""
    users = User.objects.all().order_by('user_type')
    
    # Filter options
    user_type = request.GET.get('user_type', '')
    search_query = request.GET.get('search', '')
    
    # Apply filters
    if user_type:
        users = users.filter(user_type=user_type)
    
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    context = {
        'users': users,
        'user_type': user_type,
        'search_query': search_query
    }
    return render(request, 'accounts/user_list.html', context)

@login_required
@admin_required
def add_user(request):
    """View to add a new user"""
    if request.method == 'POST':
        form = AdminUserForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            
            # Determine which default password was used
            user_type = form.cleaned_data.get('user_type')
            if user_type == 'ADMIN':
                default_password = 'admin123'
            elif user_type == 'TEACHER':
                default_password = 'teacher123'
            elif user_type == 'STUDENT':
                default_password = 'student123'
            else:
                default_password = 'changeme123'
                
            messages.success(
                request, 
                f'User {user.get_full_name()} has been added successfully with default password: {default_password}'
            )
            return redirect('accounts:user_list')
    else:
        form = AdminUserForm()
    
    context = {
        'form': form,
        'title': 'Add User'
    }
    return render(request, 'accounts/user_form.html', context)

@login_required
@admin_required
def edit_user(request, pk):
    """View to edit an existing user"""
    try:
        user_obj = User.objects.get(pk=pk)
    except User.DoesNotExist:
        messages.error(request, 'User does not exist.')
        return redirect('accounts:user_list')
    
    if request.method == 'POST':
        form = AdminUserForm(request.POST, request.FILES, instance=user_obj)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.get_full_name()} has been updated successfully.')
            return redirect('accounts:user_list')
    else:
        form = AdminUserForm(instance=user_obj)
    
    context = {
        'form': form,
        'user_obj': user_obj,
        'title': f'Edit User: {user_obj.get_full_name()}'
    }
    return render(request, 'accounts/user_form.html', context)

@login_required
@admin_required
def delete_user(request, pk):
    """View to delete a user"""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        email = user.email
        user.delete()
        messages.success(request, f'User {email} deleted successfully!')
        return redirect('accounts:user_list')
    
    context = {
        'user_obj': user  # renamed to avoid conflict with request.user
    }
    return render(request, 'accounts/user_confirm_delete.html', context)

@login_required
@admin_required
def user_detail(request, pk):
    """View to display user details"""
    try:
        user = User.objects.get(pk=pk)
        
        context = {
            'user_obj': user,
            'title': f'User Details: {user.get_full_name()}',
        }
        
        # Add teacher-specific data if user is a teacher
        if user.user_type == 'TEACHER':
            try:
                teacher_profile = user.teacher_profile
                context['teacher_profile'] = teacher_profile
            except:
                pass
        
        # Add student-specific data if user is a student
        elif user.user_type == 'STUDENT':
            try:
                student_profile = user.student_profile
                context['student_profile'] = student_profile
            except:
                pass
                
        return render(request, 'accounts/user_detail.html', context)
    except User.DoesNotExist:
        messages.error(request, 'User does not exist.')
        return redirect('accounts:user_list')
