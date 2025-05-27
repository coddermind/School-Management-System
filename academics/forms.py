from django import forms
from .models import Student, Attendance, Timetable, Assignment, AssignmentSubmission, ExamType, Exam, ExamSchedule, Mark, TimeSlot, Weekday
from accounts.models import User
from django.db.models import Q
from administration.models import ClassSubject, Subject, Grade, Section, AcademicSession

class StudentForm(forms.ModelForm):
    """Form for managing students"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If editing an existing student, don't filter out the current user
        if self.instance and self.instance.pk:
            # Get all student users except those that already have a Student record (excluding the current one)
            existing_student_users = Student.objects.exclude(pk=self.instance.pk).values_list('user_id', flat=True)
            self.fields['user'].queryset = User.objects.filter(user_type='STUDENT').exclude(id__in=existing_student_users)
        else:
            # Get all student users except those that already have a Student record
            existing_student_users = Student.objects.values_list('user_id', flat=True)
            self.fields['user'].queryset = User.objects.filter(user_type='STUDENT').exclude(id__in=existing_student_users)
        
        # When a grade is selected, filter sections to show only those for the selected grade
        if 'grade' in self.data:
            try:
                grade_id = int(self.data.get('grade'))
                self.fields['section'].queryset = self.fields['section'].queryset.filter(grade_id=grade_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.grade:
            self.fields['section'].queryset = self.fields['section'].queryset.filter(grade=self.instance.grade)
    
    class Meta:
        model = Student
        fields = ('user', 'academic_session', 'grade', 'section', 'roll_number', 'monthly_fee')
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'academic_session': forms.Select(attrs={'class': 'form-control'}),
            'grade': forms.Select(attrs={'class': 'form-control'}),
            'section': forms.Select(attrs={'class': 'form-control'}),
            'roll_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'monthly_fee': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'})
        }

class AttendanceForm(forms.ModelForm):
    """Form for managing attendance"""
    
    class Meta:
        model = Attendance
        fields = ('student', 'date', 'subject', 'is_present', 'remarks')
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'is_present': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'remarks': forms.TextInput(attrs={'class': 'form-control'})
        }

class TimetableForm(forms.ModelForm):
    """Form for managing timetable entries"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Hide the teacher field since it will be auto-selected
        self.fields['teacher'].widget = forms.HiddenInput()
        self.fields['teacher'].required = False  # Make teacher not required in form validation
        
        # When a grade is selected, filter sections to show only those for the selected grade
        if 'grade' in self.data:
            try:
                grade_id = int(self.data.get('grade'))
                self.fields['section'].queryset = self.fields['section'].queryset.filter(grade_id=grade_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.grade:
            self.fields['section'].queryset = self.fields['section'].queryset.filter(grade=self.instance.grade)
            
        # When grade and subject are both selected, filter subject options based on what's available for that grade
        if 'grade' in self.data and self.data.get('grade'):
            grade_id = int(self.data.get('grade'))
            # Get all subjects assigned to this grade through ClassSubject
            class_subjects = ClassSubject.objects.filter(grade_id=grade_id)
            self.fields['subject'].queryset = Subject.objects.filter(id__in=class_subjects.values_list('subject_id', flat=True))
            
            # Add class subjects to the help text for the subject field
            subject_teachers = {}
            for cs in class_subjects:
                subject_teachers[cs.subject_id] = cs.teacher.get_full_name() if cs.teacher else "No teacher assigned"
            
            self.subject_teachers = subject_teachers
    
    class Meta:
        model = Timetable
        fields = ('academic_session', 'grade', 'section', 'day', 'time_slot', 'subject', 'teacher')
        widgets = {
            'academic_session': forms.Select(attrs={'class': 'form-control'}),
            'grade': forms.Select(attrs={'class': 'form-control'}),
            'section': forms.Select(attrs={'class': 'form-control'}),
            'day': forms.Select(attrs={'class': 'form-control'}),
            'time_slot': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'teacher': forms.Select(attrs={'class': 'form-control'})
        }
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Check if all required fields are provided (except teacher which will be auto-set)
        required_fields = ['academic_session', 'grade', 'section', 'day', 'time_slot', 'subject']
        for field in required_fields:
            if field not in cleaned_data or not cleaned_data.get(field):
                self.add_error(field, f'This field is required.')
                
        grade = cleaned_data.get('grade')
        subject = cleaned_data.get('subject')
        
        # If both grade and subject are provided, auto-select the teacher
        if grade and subject:
            try:
                # Find the class subject that links this grade and subject
                class_subject = ClassSubject.objects.get(grade=grade, subject=subject)
                if class_subject.teacher:
                    # Always set the teacher based on the subject and grade
                    cleaned_data['teacher'] = class_subject.teacher
                    print(f"DEBUG - Auto-assigning teacher: {class_subject.teacher.id} - {class_subject.teacher.get_full_name()}")
                else:
                    self.add_error('subject', 'No teacher is assigned to this subject for this grade.')
                    return cleaned_data
            except ClassSubject.DoesNotExist:
                self.add_error('subject', 'This subject is not assigned to this grade.')
                return cleaned_data
            except Exception as e:
                self.add_error('subject', f'Error finding teacher: {str(e)}')
                return cleaned_data
        
        # Check for scheduling conflicts
        teacher = cleaned_data.get('teacher')
        day = cleaned_data.get('day')
        time_slot = cleaned_data.get('time_slot')
        
        if teacher and day and time_slot:
            # Check if this teacher is already scheduled during this time slot on this day
            existing_entry = Timetable.objects.filter(
                teacher=teacher,
                day=day,
                time_slot=time_slot
            )
            
            # Exclude the current instance if editing
            if self.instance.pk:
                existing_entry = existing_entry.exclude(pk=self.instance.pk)
            
            if existing_entry.exists():
                conflict = existing_entry.first()
                self.add_error('time_slot', f'This teacher already has a class scheduled during this time slot: {conflict.grade.display_name} {conflict.section.name} - {conflict.subject.name}')
        
        # Check if this time slot is already scheduled for this class/section on this day
        section = cleaned_data.get('section')
        academic_session = cleaned_data.get('academic_session')
        
        if grade and section and day and time_slot and academic_session:
            existing_entry = Timetable.objects.filter(
                academic_session=academic_session,
                grade=grade,
                section=section,
                day=day,
                time_slot=time_slot
            )
            
            # Exclude the current instance if editing
            if self.instance.pk:
                existing_entry = existing_entry.exclude(pk=self.instance.pk)
            
            if existing_entry.exists():
                conflict = existing_entry.first()
                self.add_error('time_slot', f'This class already has a subject scheduled during this time slot: {conflict.subject.name} with {conflict.teacher.get_full_name()}')
        
        return cleaned_data

class TimeSlotForm(forms.ModelForm):
    """Form for managing time slots"""
    
    class Meta:
        model = TimeSlot
        fields = ('name', 'start_time', 'end_time')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
        }

class AssignmentForm(forms.ModelForm):
    """Form for managing assignments"""
    instructions = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}), required=False)
    max_score = forms.DecimalField(widget=forms.NumberInput(attrs={'class': 'form-control'}), required=True)
    grading_criteria = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=False)
    attachment = forms.FileField(widget=forms.FileInput(attrs={'class': 'form-control'}), required=False)
    
    class Meta:
        model = Assignment
        fields = ('title', 'description', 'grade', 'section', 'subject', 'due_date', 'file')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'grade': forms.Select(attrs={'class': 'form-control'}),
            'section': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'file': forms.FileInput(attrs={'class': 'form-control'})
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # If this is an edit form, populate the custom fields from the instance
        if self.instance and self.instance.pk:
            self.fields['instructions'].initial = self.instance.instructions
            self.fields['max_score'].initial = self.instance.max_score
            self.fields['grading_criteria'].initial = self.instance.grading_criteria
        
        if self.user and self.user.is_teacher:
            # Get all class subjects assigned to this teacher
            teacher_class_subjects = ClassSubject.objects.filter(teacher=self.user)
            
            # Restrict grade choices to only those assigned to the teacher
            assigned_grades = teacher_class_subjects.values_list('grade', flat=True).distinct()
            self.fields['grade'].queryset = Grade.objects.filter(id__in=assigned_grades)
            
            # Restrict subject choices to only those assigned to the teacher
            assigned_subjects = teacher_class_subjects.values_list('subject', flat=True).distinct()
            self.fields['subject'].queryset = Subject.objects.filter(id__in=assigned_subjects)
            
            # Get all sections assigned to this teacher from class subjects
            # Get all section IDs excluding None values
            assigned_sections = teacher_class_subjects.exclude(section=None).values_list('section', flat=True).distinct()
            
            # Set section queryset to show only those assigned to the teacher
            if assigned_sections:
                self.fields['section'].queryset = Section.objects.filter(id__in=assigned_sections)
            else:
                # If teacher has no specific section assignments
                self.fields['section'].queryset = Section.objects.none()
                
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Save additional fields to the model
        instance.instructions = self.cleaned_data.get('instructions')
        instance.max_score = self.cleaned_data.get('max_score')
        instance.grading_criteria = self.cleaned_data.get('grading_criteria')
        
        # Handle file upload if attachment is provided
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            instance.file = attachment
            
        if commit:
            instance.save()
            
        return instance

class AssignmentSubmissionForm(forms.ModelForm):
    """Form for managing assignment submissions"""
    
    class Meta:
        model = AssignmentSubmission
        fields = ('assignment', 'student', 'file', 'remarks')
        widgets = {
            'assignment': forms.Select(attrs={'class': 'form-control'}),
            'student': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }

class MarkAssignmentSubmissionForm(forms.ModelForm):
    """Form for marking assignment submissions"""
    
    class Meta:
        model = AssignmentSubmission
        fields = ('marks', 'remarks')
        widgets = {
            'marks': forms.NumberInput(attrs={'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }

class ExamTypeForm(forms.ModelForm):
    """Form for managing exam types"""
    
    class Meta:
        model = ExamType
        fields = ('name', 'description')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }

class ExamForm(forms.ModelForm):
    """Form for managing exams"""
    
    class Meta:
        model = Exam
        fields = ('name', 'exam_type', 'academic_session', 'grade', 'start_date', 'end_date')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'exam_type': forms.Select(attrs={'class': 'form-control'}),
            'academic_session': forms.Select(attrs={'class': 'form-control'}),
            'grade': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
        }

class ExamScheduleForm(forms.ModelForm):
    """Form for managing exam schedules"""
    
    class Meta:
        model = ExamSchedule
        fields = ('exam', 'subject', 'date', 'start_time', 'end_time')
        widgets = {
            'exam': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
        }

class MarkForm(forms.ModelForm):
    """Form for managing marks"""
    
    class Meta:
        model = Mark
        fields = ('student', 'exam', 'subject', 'marks_obtained', 'maximum_marks', 'remarks')
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'exam': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'marks_obtained': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'maximum_marks': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'remarks': forms.TextInput(attrs={'class': 'form-control'})
        } 