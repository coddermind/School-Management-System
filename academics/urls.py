from django.urls import path
from . import views
from . import api

app_name = 'academics'

urlpatterns = [
    # Students
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.add_student, name='add_student'),
    path('students/edit/<int:pk>/', views.edit_student, name='edit_student'),
    path('students/delete/<int:pk>/', views.delete_student, name='delete_student'),
    path('students/<int:pk>/detail/', views.student_detail, name='student_detail'),
    
    # Teachers
    path('teachers/', views.teacher_list, name='teacher_list'),
    path('teachers/add/', views.add_teacher, name='add_teacher'),
    path('teachers/edit/<int:pk>/', views.edit_teacher, name='edit_teacher'),
    path('teachers/delete/<int:pk>/', views.delete_teacher, name='delete_teacher'),
    path('teachers/<int:pk>/detail/', views.teacher_detail, name='teacher_detail'),
    
    # Classes/Grades
    path('classes/', views.grade_list, name='grade_list'),
    path('classes/add/', views.add_grade, name='add_grade'),
    path('classes/edit/<int:pk>/', views.edit_grade, name='edit_grade'),
    path('classes/delete/<int:pk>/', views.delete_grade, name='delete_grade'),
    
    # Subjects
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/add/', views.add_subject, name='add_subject'),
    path('subjects/edit/<int:pk>/', views.edit_subject, name='edit_subject'),
    path('subjects/delete/<int:pk>/', views.delete_subject, name='delete_subject'),
    
    # Attendance
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance/teacher/', views.teacher_timetable, name='teacher_timetable'),
    path('attendance/mark/<int:timetable_id>/', views.mark_attendance, name='mark_attendance'),
    path('attendance/add/', views.add_attendance, name='add_attendance'),
    path('attendance/<int:pk>/', views.attendance_detail, name='attendance_detail'),
    path('attendance/<int:pk>/edit/', views.edit_attendance, name='edit_attendance'),
    path('attendance/<int:pk>/delete/', views.delete_attendance, name='delete_attendance'),
    path('attendance/export/csv/', views.export_attendance_csv, name='export_attendance_csv'),
    path('attendance/export/pdf/', views.export_attendance_pdf, name='export_attendance_pdf'),
    
    # Timetable
    path('timetable/', views.timetable_list, name='timetable_list'),
    path('timetable/add/', views.add_timetable, name='add_timetable'),
    path('timetable/edit/<int:pk>/', views.edit_timetable, name='edit_timetable'),
    path('timetable/delete/<int:pk>/', views.delete_timetable, name='delete_timetable'),
    
    # Assignments
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/add/', views.add_assignment, name='add_assignment'),
    path('assignments/edit/<int:pk>/', views.edit_assignment, name='edit_assignment'),
    path('assignments/delete/<int:pk>/', views.delete_assignment, name='delete_assignment'),
    path('assignments/<int:pk>/detail/', views.assignment_detail, name='assignment_detail'),
    path('assignments/<int:pk>/submit/', views.submit_assignment, name='submit_assignment'),
    path('assignments/submissions/<int:pk>/grade/', views.grade_submission, name='grade_submission'),
    
    # Exams
    path('exams/', views.exam_list, name='exam_list'),
    path('exams/add/', views.add_exam, name='add_exam'),
    path('exams/edit/<int:pk>/', views.edit_exam, name='edit_exam'),
    path('exams/delete/<int:pk>/', views.delete_exam, name='delete_exam'),
    path('exams/<int:pk>/detail/', views.exam_detail, name='exam_detail'),
    path('exams/<int:pk>/grades/add/', views.add_exam_grade, name='add_exam_grade'),
    path('exam-grades/edit/<int:pk>/', views.edit_exam_grade, name='edit_exam_grade'),
    path('exam-grades/delete/<int:pk>/', views.delete_exam_grade, name='delete_exam_grade'),
    
    # Reports
    path('reports/academic/', views.academic_report, name='academic_report'),
    path('reports/attendance/', views.attendance_report, name='attendance_report'),
    path('students/<int:student_id>/report-card/', views.student_report_card, name='student_report_card'),
    
    # API endpoints
    path('api/grade/<int:grade_id>/sections/', views.grade_sections_api, name='grade_sections_api'),
    path('api/grade/<int:grade_id>/subjects/', views.grade_subjects_api, name='grade_subjects_api'),
    path('api/available-subjects/', api.available_subjects_api, name='available_subjects_api'),
]
