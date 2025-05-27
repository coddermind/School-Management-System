from django.db import models
from django.conf import settings
from administration.models import AcademicSession, Grade, Section, Subject, ClassSubject

class Student(models.Model):
    """Model to associate a student with a class and section"""
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                                related_name='student_record', limit_choices_to={'user_type': 'STUDENT'})
    academic_session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name='students')
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='students')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='students')
    roll_number = models.PositiveIntegerField()
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=5000.00)
    
    class Meta:
        unique_together = ['academic_session', 'grade', 'section', 'roll_number']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.grade.display_name} {self.section.name}"

class TimeSlot(models.Model):
    """Model for Time Slots in Timetable"""
    
    name = models.CharField(max_length=50)  # e.g., "Period 1", "Break", "Lunch"
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"

class Weekday(models.Model):
    """Model for Weekdays"""
    
    WEEKDAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    day = models.PositiveSmallIntegerField(choices=WEEKDAY_CHOICES, unique=True)
    
    def __str__(self):
        return self.get_day_display()

class Timetable(models.Model):
    """Model for Timetable"""
    
    academic_session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name='timetables')
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='timetables')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='timetables')
    day = models.ForeignKey(Weekday, on_delete=models.CASCADE, related_name='timetables')
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name='timetables')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='timetables')
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                                related_name='timetables', limit_choices_to={'user_type': 'TEACHER'})
    
    class Meta:
        unique_together = ['academic_session', 'grade', 'section', 'day', 'time_slot']
    
    def __str__(self):
        return f"{self.grade.display_name} {self.section.name} - {self.day} - {self.time_slot.name} - {self.subject.name}"

class Attendance(models.Model):
    """Model for Student Attendance"""
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='attendances')
    is_present = models.BooleanField(default=True)
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                                 related_name='marked_attendances', limit_choices_to={'user_type': 'TEACHER'})
    remarks = models.CharField(max_length=200, null=True, blank=True)
    
    class Meta:
        unique_together = ['student', 'date', 'subject']
    
    def __str__(self):
        status = "Present" if self.is_present else "Absent"
        return f"{self.student.user.get_full_name()} - {self.date} - {self.subject.name} - {status}"

class ExamType(models.Model):
    """Model for Exam Types (e.g., Mid-term, Final, Quiz)"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return self.name

class Exam(models.Model):
    """Model for Exams"""
    
    name = models.CharField(max_length=200)
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE, related_name='exams')
    academic_session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name='exams')
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='exams')
    start_date = models.DateField()
    end_date = models.DateField()
    
    def __str__(self):
        return f"{self.name} - {self.academic_session} - {self.grade.display_name}"

class ExamSchedule(models.Model):
    """Model for Exam Schedules"""
    
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='schedules')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='exam_schedules')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    class Meta:
        unique_together = ['exam', 'subject', 'date']
    
    def __str__(self):
        return f"{self.exam.name} - {self.subject.name} - {self.date}"

class Mark(models.Model):
    """Model for Student Marks"""
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='marks')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='marks')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='marks')
    marks_obtained = models.DecimalField(max_digits=6, decimal_places=2)
    maximum_marks = models.DecimalField(max_digits=6, decimal_places=2)
    remarks = models.CharField(max_length=200, null=True, blank=True)
    
    class Meta:
        unique_together = ['student', 'exam', 'subject']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.exam.name} - {self.subject.name} - {self.marks_obtained}/{self.maximum_marks}"
    
    @property
    def percentage(self):
        if self.maximum_marks > 0:
            return (self.marks_obtained / self.maximum_marks) * 100
        return 0

class Assignment(models.Model):
    """Model for Assignments"""
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructions = models.TextField(null=True, blank=True)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='assignments')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='assignments', null=True, blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='assignments')
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                               related_name='assignments', limit_choices_to={'user_type': 'TEACHER'})
    assigned_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    file = models.FileField(upload_to='assignments/', null=True, blank=True)
    max_score = models.DecimalField(max_digits=6, decimal_places=2, default=100.00)
    grading_criteria = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.title} - {self.subject.name} - {self.grade.display_name}"

class AssignmentSubmission(models.Model):
    """Model for Assignment Submissions"""
    
    STATUS_CHOICES = (
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
    )
    
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='submissions')
    submission_date = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(auto_now_add=True)  # Another field for submission time
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    file = models.FileField(upload_to='assignment_submissions/', null=True, blank=True)
    submission_text = models.TextField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    marks = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    grade = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['assignment', 'student']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.assignment.title}"
    
    @property
    def is_late(self):
        return self.submission_date.date() > self.assignment.due_date
