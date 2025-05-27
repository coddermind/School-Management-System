from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class SchoolSettings(models.Model):
    """Model for storing school settings like name, logo, address, etc."""
    
    school_name = models.CharField(max_length=200)
    school_logo = models.ImageField(upload_to='school/logo/', null=True, blank=True)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(null=True, blank=True)
    school_description = models.TextField(null=True, blank=True)
    established_year = models.PositiveIntegerField(null=True, blank=True)
    principal_name = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        verbose_name = 'School Settings'
        verbose_name_plural = 'School Settings'
    
    def __str__(self):
        return self.school_name
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if SchoolSettings.objects.exists() and not self.pk:
            raise ValueError('Only one School Settings instance can exist')
        return super().save(*args, **kwargs)

class AcademicSession(models.Model):
    """Model for Academic Sessions (e.g., 2023-2024)"""
    
    name = models.CharField(max_length=200, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # If this is set to active, deactivate all others
        if self.is_active:
            AcademicSession.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)

class Grade(models.Model):
    """Model for Grades/Classes (e.g., 1st Grade, 2nd Grade)"""
    
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.display_name

class Section(models.Model):
    """Model for Sections within a Grade (e.g., A, B, C)"""
    
    name = models.CharField(max_length=50)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='sections')
    
    class Meta:
        unique_together = ['name', 'grade']
    
    def __str__(self):
        return f"{self.grade.display_name} - Section {self.name}"

class Subject(models.Model):
    """Model for Subjects"""
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class ClassSubject(models.Model):
    """Model for mapping Subjects to Grades"""
    
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='class_subjects')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='class_subjects', null=True, blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='class_subjects')
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name='teaching_subjects', limit_choices_to={'user_type': 'TEACHER'})
    
    class Meta:
        unique_together = ['grade', 'section', 'subject']
    
    def __str__(self):
        section_name = f" - Section {self.section.name}" if self.section else ""
        return f"{self.grade.display_name}{section_name} - {self.subject.name}"

class ClassRoom(models.Model):
    """Model for Physical Classrooms"""
    
    name = models.CharField(max_length=50, unique=True)
    capacity = models.PositiveIntegerField()
    description = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return self.name
