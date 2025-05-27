from django.contrib import admin
from .models import SchoolSettings, AcademicSession, Grade, Section, Subject, ClassSubject, ClassRoom

@admin.register(SchoolSettings)
class SchoolSettingsAdmin(admin.ModelAdmin):
    list_display = ('school_name', 'email', 'phone', 'principal_name')
    
@admin.register(AcademicSession)
class AcademicSessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    
@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name')
    search_fields = ('name', 'display_name')
    
@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'grade')
    list_filter = ('grade',)
    search_fields = ('name', 'grade__name')
    
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')
    
@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = ('grade', 'section', 'subject', 'teacher')
    list_filter = ('grade', 'section', 'subject')
    search_fields = ('grade__name', 'section__name', 'subject__name', 'teacher__email')
    
@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity')
    search_fields = ('name',)
