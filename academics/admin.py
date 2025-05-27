from django.contrib import admin
from .models import (
    Student, TimeSlot, Weekday, Timetable, Attendance, 
    ExamType, Exam, ExamSchedule, Mark, Assignment, AssignmentSubmission
)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'academic_session', 'grade', 'section', 'roll_number')
    list_filter = ('academic_session', 'grade', 'section')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'roll_number')

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_time', 'end_time')

@admin.register(Weekday)
class WeekdayAdmin(admin.ModelAdmin):
    list_display = ('day',)

@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('academic_session', 'grade', 'section', 'day', 'time_slot', 'subject', 'teacher')
    list_filter = ('academic_session', 'grade', 'section', 'day')
    search_fields = ('subject__name', 'teacher__email')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'subject', 'is_present', 'marked_by')
    list_filter = ('date', 'subject', 'is_present')
    search_fields = ('student__user__email', 'student__user__first_name', 'student__user__last_name')
    date_hierarchy = 'date'

@admin.register(ExamType)
class ExamTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'exam_type', 'academic_session', 'grade', 'start_date', 'end_date')
    list_filter = ('exam_type', 'academic_session', 'grade')
    search_fields = ('name',)
    date_hierarchy = 'start_date'

@admin.register(ExamSchedule)
class ExamScheduleAdmin(admin.ModelAdmin):
    list_display = ('exam', 'subject', 'date', 'start_time', 'end_time')
    list_filter = ('exam', 'subject', 'date')
    date_hierarchy = 'date'

@admin.register(Mark)
class MarkAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'subject', 'marks_obtained', 'maximum_marks', 'percentage')
    list_filter = ('exam', 'subject')
    search_fields = ('student__user__email', 'student__user__first_name', 'student__user__last_name')

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'grade', 'section', 'subject', 'teacher', 'assigned_date', 'due_date')
    list_filter = ('grade', 'section', 'subject', 'assigned_date', 'due_date')
    search_fields = ('title', 'description')
    date_hierarchy = 'assigned_date'

@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student', 'submission_date', 'marks', 'is_late')
    list_filter = ('assignment', 'submission_date')
    search_fields = ('student__user__email', 'student__user__first_name', 'student__user__last_name')
    date_hierarchy = 'submission_date'
