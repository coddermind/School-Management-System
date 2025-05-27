from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    """Custom User model with email as username and additional fields."""
    
    USER_TYPE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('TEACHER', 'Teacher'),
        ('STUDENT', 'Student'),
    )
    
    username = None
    email = models.EmailField(_('email address'), unique=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='STUDENT')
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_type_display()})"
    
    @property
    def is_admin(self):
        return self.user_type == 'ADMIN'
    
    @property
    def is_teacher(self):
        return self.user_type == 'TEACHER'
    
    @property
    def is_student(self):
        return self.user_type == 'STUDENT'

class StudentProfile(models.Model):
    """Additional details for Student users."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    admission_number = models.CharField(max_length=20, unique=True)
    parent_name = models.CharField(max_length=100)
    parent_phone = models.CharField(max_length=15)
    parent_email = models.EmailField()
    blood_group = models.CharField(max_length=5, null=True, blank=True)
    emergency_contact = models.CharField(max_length=15, null=True, blank=True)
    
    def __str__(self):
        return f"Student Profile: {self.user.get_full_name()}"

class TeacherProfile(models.Model):
    """Additional details for Teacher users."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    employee_id = models.CharField(max_length=20, unique=True)
    qualification = models.CharField(max_length=100)
    experience = models.IntegerField(default=0)  # Experience in years
    joining_date = models.DateField()
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Basic salary amount
    
    def __str__(self):
        return f"Teacher Profile: {self.user.get_full_name()}"
