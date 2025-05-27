from django import forms
from .models import SchoolSettings, Grade, Section, Subject, AcademicSession, ClassRoom, ClassSubject

class SchoolSettingsForm(forms.ModelForm):
    """Form for managing school settings"""
    
    class Meta:
        model = SchoolSettings
        fields = ('school_name', 'school_logo', 'address', 'phone', 'email', 
                 'website', 'school_description', 'established_year', 'principal_name')
        widgets = {
            'school_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'school_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'established_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'principal_name': forms.TextInput(attrs={'class': 'form-control'}),
            'school_logo': forms.FileInput(attrs={'class': 'form-control'})
        }

class GradeForm(forms.ModelForm):
    """Form for managing grades/classes"""
    
    class Meta:
        model = Grade
        fields = ('name', 'display_name')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'display_name': forms.TextInput(attrs={'class': 'form-control'})
        }

class SectionForm(forms.ModelForm):
    """Form for managing sections"""
    
    class Meta:
        model = Section
        fields = ('name', 'grade')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'grade': forms.Select(attrs={'class': 'form-control'})
        }

class SubjectForm(forms.ModelForm):
    """Form for managing subjects"""
    
    class Meta:
        model = Subject
        fields = ('name', 'code', 'description')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }

class ClassSubjectForm(forms.ModelForm):
    """Form for linking subjects to classes"""
    
    class Meta:
        model = ClassSubject
        fields = ('grade', 'section', 'subject', 'teacher')
        widgets = {
            'grade': forms.Select(attrs={'class': 'form-control'}),
            'section': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'teacher': forms.Select(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set section queryset to empty initially
        self.fields['section'].queryset = Section.objects.none()
        
        # If form is bound and grade is selected, or if instance has grade
        if self.data.get('grade') or (self.instance and self.instance.pk and self.instance.grade):
            grade_id = self.data.get('grade') or self.instance.grade.id
            self.fields['section'].queryset = Section.objects.filter(grade_id=grade_id)

class AcademicSessionForm(forms.ModelForm):
    """Form for managing academic sessions"""
    
    class Meta:
        model = AcademicSession
        fields = ('name', 'start_date', 'end_date', 'is_active')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

class ClassRoomForm(forms.ModelForm):
    """Form for managing classrooms"""
    
    class Meta:
        model = ClassRoom
        fields = ('name', 'capacity', 'description')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        } 