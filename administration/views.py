from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.mixins import admin_required
from .models import SchoolSettings, Grade, Section, Subject, ClassSubject, AcademicSession, ClassRoom
from .forms import SchoolSettingsForm, GradeForm, SectionForm, SubjectForm, AcademicSessionForm, ClassRoomForm, ClassSubjectForm
from django import forms
from django.conf import settings
from accounts.models import User
from django.http import JsonResponse

# Create your views here.

# School Settings
@login_required
@admin_required
def school_settings(request):
    """View to manage school settings"""
    try:
        settings = SchoolSettings.objects.get()
    except SchoolSettings.DoesNotExist:
        settings = None
    
    if request.method == 'POST':
        if settings:
            form = SchoolSettingsForm(request.POST, request.FILES, instance=settings)
        else:
            form = SchoolSettingsForm(request.POST, request.FILES)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'School settings updated successfully!')
            return redirect('administration:school_settings')
    else:
        if settings:
            form = SchoolSettingsForm(instance=settings)
        else:
            form = SchoolSettingsForm()
    
    context = {
        'form': form,
        'settings': settings
    }
    return render(request, 'administration/school_settings.html', context)

# Classes (Grades)
@login_required
@admin_required
def class_list(request):
    """View to list all classes/grades"""
    classes = Grade.objects.all().prefetch_related('students', 'sections')
    
    # Get student count for each class
    for grade in classes:
        grade.student_count = grade.students.count()
    
    context = {
        'classes': classes
    }
    return render(request, 'administration/class_list.html', context)

@login_required
@admin_required
def add_class(request):
    """View to add a new class/grade"""
    if request.method == 'POST':
        form = GradeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Class added successfully!')
            return redirect('administration:class_list')
    else:
        form = GradeForm()
    
    context = {
        'form': form
    }
    return render(request, 'administration/class_form.html', context)

@login_required
@admin_required
def edit_class(request, pk):
    """View to edit a class/grade"""
    grade = get_object_or_404(Grade, pk=pk)
    
    if request.method == 'POST':
        form = GradeForm(request.POST, instance=grade)
        if form.is_valid():
            form.save()
            messages.success(request, 'Class updated successfully!')
            return redirect('administration:class_list')
    else:
        form = GradeForm(instance=grade)
    
    context = {
        'form': form,
        'grade': grade
    }
    return render(request, 'administration/class_form.html', context)

@login_required
@admin_required
def delete_class(request, pk):
    """View to delete a class/grade"""
    grade = get_object_or_404(Grade, pk=pk)
    
    if request.method == 'POST':
        grade.delete()
        messages.success(request, 'Class deleted successfully!')
        return redirect('administration:class_list')
    
    context = {
        'grade': grade
    }
    return render(request, 'administration/class_confirm_delete.html', context)

# Sections
@login_required
@admin_required
def section_list(request):
    """View to list all sections"""
    sections = Section.objects.all()
    context = {
        'sections': sections
    }
    return render(request, 'administration/section_list.html', context)

@login_required
@admin_required
def add_section(request):
    """View to add a new section"""
    if request.method == 'POST':
        form = SectionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Section added successfully!')
            return redirect('administration:section_list')
    else:
        form = SectionForm()
    
    context = {
        'form': form
    }
    return render(request, 'administration/section_form.html', context)

@login_required
@admin_required
def edit_section(request, pk):
    """View to edit a section"""
    section = get_object_or_404(Section, pk=pk)
    
    if request.method == 'POST':
        form = SectionForm(request.POST, instance=section)
        if form.is_valid():
            form.save()
            messages.success(request, 'Section updated successfully!')
            return redirect('administration:section_list')
    else:
        form = SectionForm(instance=section)
    
    context = {
        'form': form,
        'section': section
    }
    return render(request, 'administration/section_form.html', context)

@login_required
@admin_required
def delete_section(request, pk):
    """View to delete a section"""
    section = get_object_or_404(Section, pk=pk)
    
    if request.method == 'POST':
        grade = section.grade
        section.delete()
        messages.success(request, 'Section deleted successfully.')
        return redirect('administration:section_list')
    
    context = {
        'section': section
    }
    return render(request, 'administration/section_confirm_delete.html', context)

@login_required
@admin_required
def section_detail(request, pk):
    """View for displaying details of a section."""
    section = get_object_or_404(Section, pk=pk)
    
    # Get students in this section
    try:
        from academics.models import Student
        students = Student.objects.filter(current_section=section)
    except ImportError:
        students = []
    
    # Get schedules for this section
    try:
        from academics.models import Schedule
        schedules = Schedule.objects.filter(section=section)
    except ImportError:
        schedules = []
    
    context = {
        'section': section,
        'students': students,
        'schedules': schedules,
        'title': f'Section Detail - {section.name}'
    }
    
    return render(request, 'administration/section_detail.html', context)

# Subjects
@login_required
@admin_required
def subject_list(request):
    """View to list all subjects"""
    subjects = Subject.objects.all()
    context = {
        'subjects': subjects
    }
    return render(request, 'administration/subject_list.html', context)

@login_required
@admin_required
def add_subject(request):
    """View to add a new subject"""
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject added successfully!')
            return redirect('administration:subject_list')
    else:
        form = SubjectForm()
    
    context = {
        'form': form
    }
    return render(request, 'administration/subject_form.html', context)

@login_required
@admin_required
def edit_subject(request, pk):
    """View to edit a subject"""
    subject = get_object_or_404(Subject, pk=pk)
    
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject updated successfully!')
            return redirect('administration:subject_list')
    else:
        form = SubjectForm(instance=subject)
    
    context = {
        'form': form,
        'subject': subject
    }
    return render(request, 'administration/subject_form.html', context)

@login_required
@admin_required
def delete_subject(request, pk):
    """View to delete a subject"""
    subject = get_object_or_404(Subject, pk=pk)
    
    if request.method == 'POST':
        subject.delete()
        messages.success(request, 'Subject deleted successfully!')
        return redirect('administration:subject_list')
    
    context = {
        'subject': subject
    }
    return render(request, 'administration/subject_confirm_delete.html', context)

# Academic Sessions
@login_required
@admin_required
def academic_session_list(request):
    """View to list all academic sessions"""
    sessions = AcademicSession.objects.all()
    context = {
        'sessions': sessions
    }
    return render(request, 'administration/academic_session_list.html', context)

@login_required
@admin_required
def add_academic_session(request):
    """View to add a new academic session"""
    if request.method == 'POST':
        form = AcademicSessionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Academic session added successfully!')
            return redirect('administration:academic_session_list')
    else:
        form = AcademicSessionForm()
    
    context = {
        'form': form
    }
    return render(request, 'administration/academic_session_form.html', context)

@login_required
@admin_required
def edit_academic_session(request, pk):
    """View to edit an academic session"""
    session = get_object_or_404(AcademicSession, pk=pk)
    
    if request.method == 'POST':
        form = AcademicSessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            messages.success(request, 'Academic session updated successfully!')
            return redirect('administration:academic_session_list')
    else:
        form = AcademicSessionForm(instance=session)
    
    context = {
        'form': form,
        'session': session
    }
    return render(request, 'administration/academic_session_form.html', context)

@login_required
@admin_required
def delete_academic_session(request, pk):
    """View to delete an academic session"""
    session = get_object_or_404(AcademicSession, pk=pk)
    
    if request.method == 'POST':
        session.delete()
        messages.success(request, 'Academic session deleted successfully!')
        return redirect('administration:academic_session_list')
    
    context = {
        'session': session
    }
    return render(request, 'administration/academic_session_confirm_delete.html', context)

# Classrooms
@login_required
@admin_required
def classroom_list(request):
    """View to list all classrooms"""
    classrooms = ClassRoom.objects.all()
    context = {
        'classrooms': classrooms
    }
    return render(request, 'administration/classroom_list.html', context)

@login_required
@admin_required
def add_classroom(request):
    """View to add a new classroom"""
    if request.method == 'POST':
        form = ClassRoomForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Classroom added successfully!')
            return redirect('administration:classroom_list')
    else:
        form = ClassRoomForm()
    
    context = {
        'form': form
    }
    return render(request, 'administration/classroom_form.html', context)

@login_required
@admin_required
def edit_classroom(request, pk):
    """View to edit a classroom"""
    classroom = get_object_or_404(ClassRoom, pk=pk)
    
    if request.method == 'POST':
        form = ClassRoomForm(request.POST, instance=classroom)
        if form.is_valid():
            form.save()
            messages.success(request, 'Classroom updated successfully!')
            return redirect('administration:classroom_list')
    else:
        form = ClassRoomForm(instance=classroom)
    
    context = {
        'form': form,
        'classroom': classroom
    }
    return render(request, 'administration/classroom_form.html', context)

@login_required
@admin_required
def delete_classroom(request, pk):
    """View to delete a classroom"""
    classroom = get_object_or_404(ClassRoom, pk=pk)
    
    if request.method == 'POST':
        classroom.delete()
        messages.success(request, 'Classroom deleted successfully!')
        return redirect('administration:classroom_list')
    
    context = {
        'classroom': classroom
    }
    return render(request, 'administration/classroom_confirm_delete.html', context)

@login_required
@admin_required
def grade_sections(request, grade_id):
    """View to list and manage sections for a specific grade"""
    grade = get_object_or_404(Grade, pk=grade_id)
    sections = Section.objects.filter(grade=grade)
    
    if request.method == 'POST':
        form = SectionForm(request.POST)
        if form.is_valid():
            # Set the grade automatically
            section = form.save(commit=False)
            section.grade = grade
            section.save()
            messages.success(request, f'Section added successfully to {grade.display_name}!')
            return redirect('administration:grade_sections', grade_id=grade.id)
    else:
        # Pre-fill the grade field and hide it
        form = SectionForm(initial={'grade': grade})
        form.fields['grade'].widget = forms.HiddenInput()
    
    context = {
        'grade': grade,
        'sections': sections,
        'form': form
    }
    return render(request, 'administration/grade_sections.html', context)

@login_required
@admin_required
def delete_grade_section(request, grade_id, section_id):
    """View to delete a section from a grade"""
    grade = get_object_or_404(Grade, pk=grade_id)
    section = get_object_or_404(Section, pk=section_id, grade=grade)
    
    if request.method == 'POST':
        section_name = section.name
        section.delete()
        messages.success(request, f'Section {section_name} has been deleted from {grade.display_name}!')
        return redirect('administration:grade_sections', grade_id=grade.id)
    
    context = {
        'grade': grade,
        'section': section
    }
    return render(request, 'administration/grade_section_confirm_delete.html', context)

# Class Subjects Management (Link Classes with Subjects)
@login_required
@admin_required
def class_subject_list(request):
    """View to list all class-subject mappings"""
    class_subjects = ClassSubject.objects.all().select_related('grade', 'section', 'subject', 'teacher')
    
    # Filter options
    grade_id = request.GET.get('grade', '')
    section_id = request.GET.get('section', '')
    subject_id = request.GET.get('subject', '')
    teacher_id = request.GET.get('teacher', '')
    
    # Apply filters
    if grade_id:
        class_subjects = class_subjects.filter(grade_id=grade_id)
        # If grade is filtered, only show sections for that grade
        sections = Section.objects.filter(grade_id=grade_id)
    else:
        sections = Section.objects.all()
    
    if section_id:
        class_subjects = class_subjects.filter(section_id=section_id)
    
    if subject_id:
        class_subjects = class_subjects.filter(subject_id=subject_id)
    
    if teacher_id:
        class_subjects = class_subjects.filter(teacher_id=teacher_id)
    
    # Get lists for dropdowns
    grades = Grade.objects.all()
    subjects = Subject.objects.all()
    teachers = User.objects.filter(user_type='TEACHER')
    
    # Get student counts for each class-subject
    from academics.models import Student
    for cs in class_subjects:
        if cs.section:
            cs.student_count = Student.objects.filter(grade=cs.grade, section=cs.section).count()
        else:
            cs.student_count = Student.objects.filter(grade=cs.grade).count()
    
    context = {
        'class_subjects': class_subjects,
        'grades': grades,
        'sections': sections,
        'subjects': subjects,
        'teachers': teachers,
        'selected_grade': grade_id,
        'selected_section': section_id,
        'selected_subject': subject_id,
        'selected_teacher': teacher_id
    }
    return render(request, 'administration/class_subject_list.html', context)

@login_required
@admin_required
def add_class_subject(request):
    """View to add a new class-subject mapping"""
    if request.method == 'POST':
        form = ClassSubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject assigned to class successfully!')
            return redirect('administration:class_subject_list')
    else:
        form = ClassSubjectForm()
    
    context = {
        'form': form
    }
    return render(request, 'administration/class_subject_form.html', context)

@login_required
@admin_required
def edit_class_subject(request, pk):
    """View to edit a class-subject mapping"""
    class_subject = get_object_or_404(ClassSubject, pk=pk)
    
    if request.method == 'POST':
        form = ClassSubjectForm(request.POST, instance=class_subject)
        if form.is_valid():
            form.save()
            messages.success(request, 'Class-subject assignment updated successfully!')
            return redirect('administration:class_subject_list')
    else:
        form = ClassSubjectForm(instance=class_subject)
    
    context = {
        'form': form,
        'class_subject': class_subject
    }
    return render(request, 'administration/class_subject_form.html', context)

@login_required
@admin_required
def delete_class_subject(request, pk):
    """View to delete a class-subject mapping"""
    class_subject = get_object_or_404(ClassSubject, pk=pk)
    
    if request.method == 'POST':
        class_subject.delete()
        messages.success(request, 'Class-subject assignment deleted successfully!')
        return redirect('administration:class_subject_list')
    
    context = {
        'class_subject': class_subject
    }
    return render(request, 'administration/class_subject_confirm_delete.html', context)

@login_required
@admin_required
def grade_subjects(request, grade_id):
    """View to manage subjects for a specific grade"""
    grade = get_object_or_404(Grade, pk=grade_id)
    class_subjects = ClassSubject.objects.filter(grade=grade).select_related('subject', 'teacher')
    
    if request.method == 'POST':
        form = ClassSubjectForm(request.POST)
        if form.is_valid():
            # Set the grade automatically
            class_subject = form.save(commit=False)
            class_subject.grade = grade
            try:
                class_subject.save()
                messages.success(request, f'Subject added successfully to {grade.display_name}!')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
            return redirect('administration:grade_subjects', grade_id=grade.id)
    else:
        # Pre-fill the grade field and hide it
        form = ClassSubjectForm(initial={'grade': grade})
        form.fields['grade'].widget = forms.HiddenInput()
    
    context = {
        'grade': grade,
        'class_subjects': class_subjects,
        'form': form
    }
    return render(request, 'administration/grade_subjects.html', context)

@login_required
@admin_required
def delete_grade_subject(request, grade_id, class_subject_id):
    """View to delete a subject from a grade"""
    grade = get_object_or_404(Grade, pk=grade_id)
    class_subject = get_object_or_404(ClassSubject, pk=class_subject_id, grade=grade)
    
    if request.method == 'POST':
        subject_name = class_subject.subject.name
        class_subject.delete()
        messages.success(request, f'Subject {subject_name} has been removed from {grade.display_name}!')
        return redirect('administration:grade_subjects', grade_id=grade.id)
    
    context = {
        'grade': grade,
        'class_subject': class_subject
    }
    return render(request, 'administration/grade_subject_confirm_delete.html', context)

@login_required
@admin_required
def get_sections_for_grade(request):
    """AJAX view to get sections for a given grade"""
    grade_id = request.GET.get('grade_id')
    sections = {}
    
    if grade_id:
        for section in Section.objects.filter(grade_id=grade_id):
            sections[section.id] = f"Section {section.name}"
    
    return JsonResponse({'sections': sections})
