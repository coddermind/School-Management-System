from django.urls import path
from . import views

app_name = 'administration'

urlpatterns = [
    # School Settings
    path('school-settings/', views.school_settings, name='school_settings'),
    
    # Classes & Sections
    path('classes/', views.class_list, name='class_list'),
    path('classes/add/', views.add_class, name='add_class'),
    path('classes/edit/<int:pk>/', views.edit_class, name='edit_class'),
    path('classes/delete/<int:pk>/', views.delete_class, name='delete_class'),
    path('classes/<int:grade_id>/sections/', views.grade_sections, name='grade_sections'),
    path('classes/<int:grade_id>/sections/<int:section_id>/delete/', views.delete_grade_section, name='delete_grade_section'),
    
    # AJAX routes
    path('get-sections-for-grade/', views.get_sections_for_grade, name='get_sections_for_grade'),
    
    # Class Subjects (Link Classes with Subjects)
    path('class-subjects/', views.class_subject_list, name='class_subject_list'),
    path('class-subjects/add/', views.add_class_subject, name='add_class_subject'),
    path('class-subjects/edit/<int:pk>/', views.edit_class_subject, name='edit_class_subject'),
    path('class-subjects/delete/<int:pk>/', views.delete_class_subject, name='delete_class_subject'),
    path('classes/<int:grade_id>/subjects/', views.grade_subjects, name='grade_subjects'),
    path('classes/<int:grade_id>/subjects/<int:class_subject_id>/delete/', views.delete_grade_subject, name='delete_grade_subject'),
    
    path('sections/', views.section_list, name='section_list'),
    path('sections/add/', views.add_section, name='add_section'),
    path('sections/edit/<int:pk>/', views.edit_section, name='edit_section'),
    path('sections/delete/<int:pk>/', views.delete_section, name='delete_section'),
    path('sections/<int:pk>/detail/', views.section_detail, name='section_detail'),
    
    # Subjects
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/add/', views.add_subject, name='add_subject'),
    path('subjects/edit/<int:pk>/', views.edit_subject, name='edit_subject'),
    path('subjects/delete/<int:pk>/', views.delete_subject, name='delete_subject'),
    
    # Academic Sessions
    path('academic-sessions/', views.academic_session_list, name='academic_session_list'),
    path('academic-sessions/add/', views.add_academic_session, name='add_academic_session'),
    path('academic-sessions/edit/<int:pk>/', views.edit_academic_session, name='edit_academic_session'),
    path('academic-sessions/delete/<int:pk>/', views.delete_academic_session, name='delete_academic_session'),
    
    # Class Rooms
    path('classrooms/', views.classroom_list, name='classroom_list'),
    path('classrooms/add/', views.add_classroom, name='add_classroom'),
    path('classrooms/edit/<int:pk>/', views.edit_classroom, name='edit_classroom'),
    path('classrooms/delete/<int:pk>/', views.delete_classroom, name='delete_classroom'),
]
