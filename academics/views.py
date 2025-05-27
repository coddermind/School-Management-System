from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.mixins import admin_required, teacher_required
from accounts.models import User
from administration.models import Grade, Section, Subject, AcademicSession, ClassSubject
from .models import Student, Attendance, Timetable, Assignment, AssignmentSubmission, ExamType, Exam, ExamSchedule, Mark, TimeSlot, Weekday
from .forms import StudentForm, AttendanceForm, TimetableForm, AssignmentForm, ExamForm, ExamScheduleForm, MarkForm
from django.http import JsonResponse
from django.utils import timezone
from django.db import models
from datetime import datetime
import logging

# Create your views here.

# Student Management
@login_required
@admin_required
def student_list(request):
    """View to list all students"""
    # Check if this is an AJAX request for sections
    if request.GET.get('ajax') == 'true' and request.GET.get('grade'):
        grade_id = request.GET.get('grade')
        sections = Section.objects.filter(grade_id=grade_id).values('id', 'name')
        return JsonResponse({'sections': list(sections)})
    
    students = Student.objects.all().select_related('user', 'grade', 'section', 'academic_session')
    
    # Get filter parameters
    grade_id = request.GET.get('grade', '')
    section_id = request.GET.get('section', '')
    session_id = request.GET.get('session', '')
    search_query = request.GET.get('search', '')
    
    # Apply filters
    if grade_id:
        students = students.filter(grade_id=grade_id)
    
    if section_id:
        students = students.filter(section_id=section_id)
    
    if session_id:
        students = students.filter(academic_session_id=session_id)
    
    if search_query:
        from django.db.models import Q
        students = students.filter(
            Q(user__first_name__icontains=search_query) | 
            Q(user__last_name__icontains=search_query) |
            Q(roll_number__icontains=search_query)
        )
    
    # Get data for dropdowns
    grades = Grade.objects.all()
    sections = Section.objects.all()
    academic_sessions = AcademicSession.objects.all()
    
    # If a grade is selected, filter sections to show only those for the selected grade
    if grade_id:
        sections = sections.filter(grade_id=grade_id)
    
    context = {
        'students': students,
        'grades': grades,
        'sections': sections,
        'academic_sessions': academic_sessions,
        'selected_grade': grade_id,
        'selected_section': section_id,
        'selected_session': session_id,
        'search_query': search_query
    }
    return render(request, 'academics/student_list.html', context)

@login_required
@admin_required
def add_student(request):
    """View to add a new student"""
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save()
            
            # Create fee entries for the student based on their grade's fee structures
            try:
                from finance.models import FeeCategory, FeeStructure, FeePayment
                from django.utils import timezone
                from datetime import datetime
                import calendar
                
                # Get the current month and year
                now = timezone.now()
                current_month = now.month
                current_year = now.year
                
                # Format month name
                month_name = calendar.month_name[current_month]
                
                # Check if a Monthly Fee category exists, create if not
                fee_category, created = FeeCategory.objects.get_or_create(
                    name='Monthly Fee',
                    defaults={'description': 'Regular monthly fee for students'}
                )
                
                # Check if fee structure for this grade and monthly fee exists, create if not
                fee_structure, created = FeeStructure.objects.get_or_create(
                    name=f'Monthly Fee - {student.grade.display_name}',
                    category=fee_category,
                    grade=student.grade,
                    academic_session=student.academic_session,
                    defaults={
                        'amount': student.monthly_fee,
                        'is_mandatory': True,
                        'frequency': 'MONTHLY',
                        'applicable_from': now.date(),
                        'description': f'Monthly Fee for {student.grade.display_name}'
                    }
                )
                
                # If fee structure already existed but with different amount, update it to match student's fee
                if not created and fee_structure.amount != student.monthly_fee:
                    fee_structure.amount = student.monthly_fee
                    fee_structure.save()
                
                # Generate receipt number
                receipt_prefix = "RCPT"
                receipt_number = f"{receipt_prefix}-{now.strftime('%Y%m%d')}-{FeePayment.objects.count() + 1}"
                
                # Create the payment record with zero amount paid (pending payment)
                fee_payment = FeePayment.objects.create(
                    student=student,
                    fee_structure=fee_structure,
                    amount_paid=0,  # Zero initially as pending
                    payment_date=now.date(),
                    payment_method='PENDING',
                    receipt_number=receipt_number,
                    remarks=f'Monthly Fee for {month_name} {current_year} (New Student)'
                )
                
                messages.success(request, f'Student added successfully! Monthly fee for {month_name} {current_year} has been generated as pending.')
            except Exception as e:
                messages.warning(request, f'Student added but there was an issue creating fee entries: {str(e)}')
            
            return redirect('academics:student_list')
    else:
        form = StudentForm()
    
    context = {
        'form': form
    }
    return render(request, 'academics/student_form.html', context)

@login_required
@admin_required
def edit_student(request, pk):
    """View to edit a student"""
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student updated successfully!')
            return redirect('academics:student_list')
    else:
        form = StudentForm(instance=student)
    
    context = {
        'form': form,
        'student': student
    }
    return render(request, 'academics/student_form.html', context)

@login_required
@admin_required
def delete_student(request, pk):
    """View to delete a student"""
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        student.delete()
        messages.success(request, 'Student deleted successfully!')
        return redirect('academics:student_list')
    
    context = {
        'student': student
    }
    return render(request, 'academics/student_confirm_delete.html', context)

@login_required
def student_detail(request, pk):
    """View to see student details"""
    student = get_object_or_404(Student, pk=pk)
    
    # Get attendance summary
    attendance_summary = {}
    attendances = Attendance.objects.filter(student=student)
    for subject in Subject.objects.all():
        subject_attendances = attendances.filter(subject=subject)
        total = subject_attendances.count()
        present = subject_attendances.filter(is_present=True).count()
        absent = total - present
        percentage = round((present / total) * 100) if total > 0 else 0
        
        attendance_summary[subject.name] = {
            'total': total,
            'present': present,
            'absent': absent,
            'percentage': percentage
        }
    
    # Get student's fee payments
    from finance.models import FeePayment
    fee_payments = FeePayment.objects.filter(student=student).select_related('fee_structure')
    
    # Calculate total pending fees
    total_fees = sum(payment.fee_structure.amount for payment in fee_payments)
    total_paid = sum(payment.amount_paid for payment in fee_payments)
    pending_fees = total_fees - total_paid
    
    # Create a custom template filter for subtraction
    from django.template.defaulttags import register
    @register.filter
    def subtract(value, arg):
        return value - arg
    
    @register.filter
    def sum_attr(collection, attr_name):
        """Sum values of a specific attribute in a collection of objects"""
        try:
            return sum(getattr(item, attr_name) for item in collection)
        except (TypeError, AttributeError):
            return 0
    
    context = {
        'student': student,
        'attendance_summary': attendance_summary,
        'fee_payments': fee_payments,
        'pending_fees': pending_fees,
        # Add these fields to match user detail view for student
        'parent_name': student.user.student_profile.parent_name if hasattr(student.user, 'student_profile') and student.user.student_profile else None,
        'parent_phone': student.user.student_profile.parent_phone if hasattr(student.user, 'student_profile') and student.user.student_profile else None,
        'parent_email': student.user.student_profile.parent_email if hasattr(student.user, 'student_profile') and student.user.student_profile else None,
        'admission_number': student.user.student_profile.admission_number if hasattr(student.user, 'student_profile') and student.user.student_profile else None,
        'blood_group': student.user.student_profile.blood_group if hasattr(student.user, 'student_profile') and student.user.student_profile else None
    }
    return render(request, 'academics/student_detail.html', context)

# Teacher Management
@login_required
@admin_required
def teacher_list(request):
    """View to list all teachers"""
    teachers = User.objects.filter(user_type='TEACHER')
    context = {
        'teachers': teachers
    }
    return render(request, 'academics/teacher_list.html', context)

@login_required
@admin_required
def add_teacher(request):
    """Redirect to the accounts app add_teacher view"""
    return redirect('accounts:add_teacher')

@login_required
@admin_required
def edit_teacher(request, pk):
    """Redirect to the accounts app edit_teacher view"""
    return redirect('accounts:edit_teacher', pk=pk)

@login_required
@admin_required
def delete_teacher(request, pk):
    """This view would be implemented in accounts app as it involves user deletion"""
    return redirect('academics:teacher_list')

@login_required
def teacher_detail(request, pk):
    """View to see teacher details"""
    teacher = get_object_or_404(User, pk=pk, user_type='TEACHER')
    
    # Get teaching subjects
    subjects = []
    class_subjects = teacher.teaching_subjects.all().select_related('grade', 'section', 'subject')
    for cs in class_subjects:
        section_info = f" - Section {cs.section.name}" if cs.section else ""
        subjects.append({
            'name': cs.subject.name,
            'grade': cs.grade,
            'grade_display': f"{cs.grade.display_name}{section_info}",
            'subject': cs.subject
        })
        
    context = {
        'teacher': teacher,
        'subjects': subjects,
    }
    return render(request, 'academics/teacher_detail.html', context)

# Grade/Class Management
@login_required
@admin_required
def grade_list(request):
    """View to list all grades/classes. Redirects to administration app's class_list view."""
    return redirect('administration:class_list')

@login_required
@admin_required
def add_grade(request):
    """View to add a new grade/class. Redirects to administration app's add_class view."""
    return redirect('administration:add_class')

@login_required
@admin_required
def edit_grade(request, pk):
    """View to edit a grade/class. Redirects to administration app's edit_class view."""
    return redirect('administration:edit_class', pk=pk)

@login_required
@admin_required
def delete_grade(request, pk):
    """View to delete a grade/class. Redirects to administration app's delete_class view."""
    return redirect('administration:delete_class', pk=pk)

# Subject Management
@login_required
@admin_required
def subject_list(request):
    """View to list all subjects. Redirects to administration app's subject_list view."""
    return redirect('administration:subject_list')

@login_required
@admin_required
def add_subject(request):
    """View to add a new subject. Redirects to administration app's add_subject view."""
    return redirect('administration:add_subject')

@login_required
@admin_required
def edit_subject(request, pk):
    """View to edit a subject. Redirects to administration app's edit_subject view."""
    return redirect('administration:edit_subject', pk=pk)

@login_required
@admin_required
def delete_subject(request, pk):
    """View to delete a subject. Redirects to administration app's delete_subject view."""
    return redirect('administration:delete_subject', pk=pk)

# Attendance Management
@login_required
def attendance_list(request):
    """View to list attendance records"""
    if request.user.is_teacher:
        # Get subjects taught by the teacher
        subjects = Subject.objects.filter(
            class_subjects__teacher=request.user
        ).distinct()
        attendance_records = Attendance.objects.filter(
            subject__in=subjects
        ).order_by('-date')
    elif request.user.is_student:
        student = get_object_or_404(Student, user=request.user)
        # Get subjects for the student's grade and section
        subjects = Subject.objects.filter(
            class_subjects__grade=student.grade,
            class_subjects__section=student.section
        ).distinct()
        attendance_records = Attendance.objects.filter(
            student=student,
            subject__in=subjects
        ).order_by('-date')
    else:
        attendance_records = Attendance.objects.all().order_by('-date')

    # Get filter parameters
    selected_grade = request.GET.get('grade')
    selected_subject = request.GET.get('subject')
    selected_date = request.GET.get('date')

    # Apply filters
    if selected_grade:
        attendance_records = attendance_records.filter(student__grade_id=selected_grade)
    if selected_subject:
        attendance_records = attendance_records.filter(subject_id=selected_subject)
    if selected_date:
        attendance_records = attendance_records.filter(date=selected_date)

    # Get available filters
    if request.user.is_teacher:
        grades = Grade.objects.filter(class_subjects__teacher=request.user).distinct()
    else:
        grades = Grade.objects.none()
    
    if request.user.is_student:
        student = get_object_or_404(Student, user=request.user)
        subjects = Subject.objects.filter(
            class_subjects__grade=student.grade,
            class_subjects__section=student.section
        ).distinct()
    else:
        subjects = Subject.objects.filter(class_subjects__grade__in=attendance_records.values('student__grade')).distinct()

    context = {
        'attendance_records': attendance_records,
        'grades': grades,
        'subjects': subjects,
        'selected_grade': selected_grade,
        'selected_subject': selected_subject,
        'selected_date': selected_date,
    }
    return render(request, 'academics/attendance_list.html', context)

@login_required
@teacher_required
def teacher_timetable(request):
    """View to show teacher's timetable for attendance marking"""
    # Get teacher's timetable
    timetable_entries = Timetable.objects.filter(
        teacher=request.user
    ).select_related('grade', 'section', 'day', 'time_slot', 'subject')
    
    # Apply filters from request
    day_id = request.GET.get('day')
    grade_id = request.GET.get('grade')
    section_id = request.GET.get('section')
    subject_id = request.GET.get('subject')
    
    if day_id:
        timetable_entries = timetable_entries.filter(day_id=day_id)
    
    if grade_id:
        timetable_entries = timetable_entries.filter(grade_id=grade_id)
    
    if section_id:
        timetable_entries = timetable_entries.filter(section_id=section_id)
    
    if subject_id:
        timetable_entries = timetable_entries.filter(subject_id=subject_id)
    
    # Order by day and time slot
    timetable_entries = timetable_entries.order_by('day__day', 'time_slot__start_time')
    
    # Get data for filter dropdowns
    days = Weekday.objects.all().order_by('day')
    subjects = Subject.objects.filter(
        id__in=timetable_entries.values_list('subject_id', flat=True)
    ).distinct()
    grades = Grade.objects.filter(
        id__in=timetable_entries.values_list('grade_id', flat=True)
    ).distinct()
    sections = Section.objects.filter(
        id__in=timetable_entries.values_list('section_id', flat=True)
    ).distinct()
    
    context = {
        'timetable_entries': timetable_entries,
        'days': days,
        'subjects': subjects,
        'grades': grades,
        'sections': sections,
        'selected_day': day_id,
        'selected_grade': grade_id,
        'selected_section': section_id,
        'selected_subject': subject_id
    }
    return render(request, 'academics/teacher_timetable.html', context)

@login_required
@teacher_required
def mark_attendance(request, timetable_id):
    """View to mark attendance for a specific class/section and subject"""
    timetable = get_object_or_404(Timetable, pk=timetable_id, teacher=request.user)
    
    # Get all students in this grade and section
    students = Student.objects.filter(
        grade=timetable.grade,
        section=timetable.section
    ).select_related('user').order_by('roll_number')
    
    # Get the date for attendance
    attendance_date = request.GET.get('date', timezone.now().date())
    
    # If this is a string, convert to a date
    if isinstance(attendance_date, str):
        try:
            attendance_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
        except ValueError:
            attendance_date = timezone.now().date()
    
    # Check if attendance already exists for this class/subject/date
    existing_attendance = Attendance.objects.filter(
        student__in=students,
        subject=timetable.subject,
        date=attendance_date
    )
    
    # Create a dict to look up existing attendance records
    attendance_dict = {attendance.student_id: attendance for attendance in existing_attendance}
    
    # Track attendance statuses and remarks
    student_attendance = []
    
    # If this is a POST request, save the attendance data
    if request.method == 'POST':
        # Get attendance data from form
        attendance_data = {}
        remarks_data = {}
        
        for key, value in request.POST.items():
            if key.startswith('attendance_'):
                student_id = key.replace('attendance_', '')
                attendance_data[student_id] = value == 'present'
            elif key.startswith('remarks_'):
                student_id = key.replace('remarks_', '')
                remarks_data[student_id] = value
        
        # Save attendance for each student
        for student in students:
            attendance_status = attendance_data.get(str(student.id), False)
            remarks = remarks_data.get(str(student.id), '')
            
            # Check if attendance already exists
            if student.id in attendance_dict:
                # Update existing attendance
                attendance = attendance_dict[student.id]
                attendance.is_present = attendance_status
                attendance.remarks = remarks
                attendance.marked_by = request.user
                attendance.save()
            else:
                # Create new attendance record
                Attendance.objects.create(
                    student=student,
                    subject=timetable.subject,
                    date=attendance_date,
                    is_present=attendance_status,
                    remarks=remarks,
                    marked_by=request.user
                )
        
        messages.success(request, f'Attendance marked successfully for {timetable.grade.display_name} {timetable.section.name} - {timetable.subject.name}')
        return redirect('academics:teacher_timetable')
    
    # For each student, prepare attendance data
    for student in students:
        attendance = attendance_dict.get(student.id)
        
        # Get student's attendance statistics
        total_classes = Attendance.objects.filter(
            student=student,
            subject=timetable.subject
        ).count()
        
        present_classes = Attendance.objects.filter(
            student=student,
            subject=timetable.subject,
            is_present=True
        ).count()
        
        attendance_percentage = round((present_classes / total_classes) * 100) if total_classes > 0 else 0
        
        student_attendance.append({
            'student': student,
            'attendance': attendance,
            'attendance_percentage': attendance_percentage
        })
    
    context = {
        'timetable': timetable,
        'students': student_attendance,
        'attendance_date': attendance_date,
        'page_title': f'Mark Attendance - {timetable.grade.display_name} {timetable.section.name} - {timetable.subject.name}'
    }
    return render(request, 'academics/mark_attendance.html', context)

def export_attendance_csv(request):
    """Export attendance records as CSV"""
    import csv
    from django.http import HttpResponse
    from datetime import datetime
    
    # Apply the same filters as in attendance_list
    queryset = Attendance.objects.all().select_related(
        'student', 'student__user', 'student__grade', 'subject'
    )
    
    # Apply user-specific filtering
    if request.user.is_admin:
        pass
    elif request.user.is_teacher:
        queryset = queryset.filter(marked_by=request.user)
    else:
        try:
            student = Student.objects.get(user=request.user)
            queryset = queryset.filter(student=student)
        except Student.DoesNotExist:
            queryset = Attendance.objects.none()
    
    # Apply request filters
    grade_id = request.GET.get('grade')
    subject_id = request.GET.get('subject')
    date = request.GET.get('date')
    status = request.GET.get('status')
    search = request.GET.get('search')
    
    if grade_id:
        queryset = queryset.filter(student__grade_id=grade_id)
    
    if subject_id:
        queryset = queryset.filter(subject_id=subject_id)
    
    if date:
        queryset = queryset.filter(date=date)
    
    if status:
        if status == 'present':
            queryset = queryset.filter(is_present=True)
        elif status == 'absent':
            queryset = queryset.filter(is_present=False)
    
    if search:
        from django.db.models import Q
        queryset = queryset.filter(
            Q(student__user__first_name__icontains=search) |
            Q(student__user__last_name__icontains=search)
        )
    
    # Order by date (newest first) and then by student name
    queryset = queryset.order_by('-date', 'student__user__first_name')
    
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    response['Content-Disposition'] = f'attachment; filename="attendance_export_{timestamp}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Student Name', 'Class', 'Subject', 'Date', 'Status', 'Remarks', 'Marked By'])
    
    for attendance in queryset:
        writer.writerow([
            attendance.id,
            attendance.student.user.get_full_name(),
            attendance.student.grade.name,
            attendance.subject.name,
            attendance.date,
            'Present' if attendance.is_present else 'Absent',
            attendance.remarks or '',
            attendance.marked_by.get_full_name() if attendance.marked_by else ''
        ])
    
    return response

def export_attendance_pdf(request):
    """Export attendance records as PDF"""
    from django.http import HttpResponse
    from django.template.loader import get_template
    from xhtml2pdf import pisa
    from io import BytesIO
    from datetime import datetime
    
    # Apply the same filters as in attendance_list
    queryset = Attendance.objects.all().select_related(
        'student', 'student__user', 'student__grade', 'subject'
    )
    
    # Apply user-specific filtering
    if request.user.is_admin:
        pass
    elif request.user.is_teacher:
        queryset = queryset.filter(marked_by=request.user)
    else:
        try:
            student = Student.objects.get(user=request.user)
            queryset = queryset.filter(student=student)
        except Student.DoesNotExist:
            queryset = Attendance.objects.none()
    
    # Apply request filters
    grade_id = request.GET.get('grade')
    subject_id = request.GET.get('subject')
    date = request.GET.get('date')
    status = request.GET.get('status')
    search = request.GET.get('search')
    
    if grade_id:
        queryset = queryset.filter(student__grade_id=grade_id)
    
    if subject_id:
        queryset = queryset.filter(subject_id=subject_id)
    
    if date:
        queryset = queryset.filter(date=date)
    
    if status:
        if status == 'present':
            queryset = queryset.filter(is_present=True)
        elif status == 'absent':
            queryset = queryset.filter(is_present=False)
    
    if search:
        from django.db.models import Q
        queryset = queryset.filter(
            Q(student__user__first_name__icontains=search) |
            Q(student__user__last_name__icontains=search)
        )
    
    # Order by date (newest first) and then by student name
    queryset = queryset.order_by('-date', 'student__user__first_name')
    
    # Prepare context for template
    context = {
        'attendance_list': queryset,
        'title': 'Attendance Report',
        'date_generated': datetime.now(),
        'user': request.user
    }
    
    # Render template to HTML
    template = get_template('academics/attendance_pdf.html')
    html = template.render(context)
    
    # Create PDF
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="attendance_report_{timestamp}.pdf"'
        return response
    
    return HttpResponse("Error generating PDF", status=400)

@login_required
def attendance_detail(request, pk):
    """View for detailed information about an attendance record"""
    attendance = get_object_or_404(Attendance, pk=pk)
    
    # Check if the user has permission to view this attendance record
    if not request.user.is_admin:
        if request.user.is_teacher and attendance.marked_by != request.user:
            messages.error(request, "You don't have permission to view this attendance record.")
            return redirect('academics:attendance_list')
        elif request.user.is_student:
            try:
                student = Student.objects.get(user=request.user)
                if attendance.student != student:
                    messages.error(request, "You don't have permission to view this attendance record.")
                    return redirect('academics:attendance_list')
            except Student.DoesNotExist:
                messages.error(request, "You don't have permission to view this attendance record.")
                return redirect('academics:attendance_list')
    
    # Get attendance statistics for this student
    student_attendance = Attendance.objects.filter(student=attendance.student)
    
    # Overall attendance stats
    total_count = student_attendance.count()
    present_count = student_attendance.filter(is_present=True).count()
    absent_count = total_count - present_count
    
    # Calculate attendance percentage
    attendance_percentage = round((present_count / total_count) * 100) if total_count > 0 else 0
    
    # Get attendance stats for this subject
    subject_attendance = student_attendance.filter(subject=attendance.subject)
    subject_total = subject_attendance.count()
    subject_present = subject_attendance.filter(is_present=True).count()
    subject_absent = subject_total - subject_present
    subject_percentage = round((subject_present / subject_total * 100) if subject_total > 0 else 0)
    
    attendance_stats = {
        'total_count': total_count,
        'present_count': present_count,
        'absent_count': absent_count,
        'attendance_percentage': attendance_percentage,
        'subject_total': subject_total,
        'subject_present': subject_present,
        'subject_absent': subject_absent,
        'subject_percentage': subject_percentage
    }
    
    context = {
        'attendance': attendance,
        'attendance_stats': attendance_stats
    }
    return render(request, 'academics/attendance_detail.html', context)

@login_required
@teacher_required
def add_attendance(request):
    """View to add attendance records"""
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            attendance = form.save(commit=False)
            attendance.marked_by = request.user
            attendance.save()
            messages.success(request, 'Attendance recorded successfully!')
            return redirect('academics:attendance_list')
    else:
        form = AttendanceForm()
    
    context = {
        'form': form
    }
    return render(request, 'academics/attendance_form.html', context)

@login_required
@teacher_required
def edit_attendance(request, pk):
    """View to edit attendance records"""
    attendance = get_object_or_404(Attendance, pk=pk)
    
    if request.method == 'POST':
        form = AttendanceForm(request.POST, instance=attendance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Attendance updated successfully!')
            return redirect('academics:attendance_list')
    else:
        form = AttendanceForm(instance=attendance)
    
    context = {
        'form': form,
        'attendance': attendance
    }
    return render(request, 'academics/attendance_form.html', context)

@login_required
@teacher_required
def delete_attendance(request, pk):
    """View to delete attendance records"""
    attendance = get_object_or_404(Attendance, pk=pk)
    
    if request.method == 'POST':
        attendance.delete()
        messages.success(request, 'Attendance record deleted successfully!')
        return redirect('academics:attendance_list')
    
    context = {
        'attendance': attendance
    }
    return render(request, 'academics/attendance_confirm_delete.html', context)

# Timetable Management
@login_required
def timetable_list(request):
    """View to list timetable entries"""
    # Get filter parameters
    grade_id = request.GET.get('grade', '')
    section_id = request.GET.get('section', '')
    day_id = request.GET.get('day', '')
    teacher_id = request.GET.get('teacher', '')
    subject_id = request.GET.get('subject', '')
    
    if request.user.is_admin:
        # Admin can see all timetable entries
        timetable_entries = Timetable.objects.all().select_related('grade', 'section', 'subject', 'teacher', 'day', 'time_slot')
        
        # Apply filters for admin
        if grade_id:
            timetable_entries = timetable_entries.filter(grade_id=grade_id)
        
        if section_id:
            timetable_entries = timetable_entries.filter(section_id=section_id)
        
        if day_id:
            timetable_entries = timetable_entries.filter(day_id=day_id)
        
        if teacher_id:
            timetable_entries = timetable_entries.filter(teacher_id=teacher_id)
        
        if subject_id:
            timetable_entries = timetable_entries.filter(subject_id=subject_id)
            
    elif request.user.is_teacher:
        # Teachers can see timetable entries where they teach
        timetable_entries = Timetable.objects.filter(teacher=request.user).select_related('grade', 'section', 'subject', 'day', 'time_slot')
        
        # Apply filters for teacher
        if grade_id:
            timetable_entries = timetable_entries.filter(grade_id=grade_id)
        
        if section_id:
            timetable_entries = timetable_entries.filter(section_id=section_id)
        
        if day_id:
            timetable_entries = timetable_entries.filter(day_id=day_id)
        
        if subject_id:
            timetable_entries = timetable_entries.filter(subject_id=subject_id)
            
    else:
        # Students can see timetable entries for their grade and section
        try:
            student = Student.objects.get(user=request.user)
            timetable_entries = Timetable.objects.filter(
                grade=student.grade, 
                section=student.section, 
                academic_session=student.academic_session
            ).select_related('subject', 'teacher', 'day', 'time_slot')
            
            # Only apply day and subject filters for students
            if day_id:
                timetable_entries = timetable_entries.filter(day_id=day_id)
            
            if subject_id:
                timetable_entries = timetable_entries.filter(subject_id=subject_id)
                
        except Student.DoesNotExist:
            timetable_entries = Timetable.objects.none()
    
    # Get data for dropdowns
    grades = Grade.objects.all()
    sections = Section.objects.all()
    days = Weekday.objects.all().order_by('day')
    teachers = User.objects.filter(user_type='TEACHER')
    subjects = Subject.objects.all()
    
    # If a grade is selected, filter sections to show only those for the selected grade
    if grade_id:
        sections = sections.filter(grade_id=grade_id)
    
    context = {
        'timetable_entries': timetable_entries,
        'grades': grades,
        'sections': sections,
        'days': days,
        'teachers': teachers,
        'subjects': subjects,
        'selected_grade': grade_id,
        'selected_section': section_id,
        'selected_day': day_id,
        'selected_teacher': teacher_id,
        'selected_subject': subject_id
    }
    return render(request, 'academics/timetable_list.html', context)

@login_required
@admin_required
def add_timetable(request):
    """View to add timetable entries"""
    if request.method == 'POST':
        print("DEBUG - POST data:", request.POST)
        form = TimetableForm(request.POST)
        
        # Log form errors if present
        if not form.is_valid():
            print("DEBUG - Form errors:", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            if form.non_field_errors():
                for error in form.non_field_errors():
                    messages.error(request, error)
        else:
            try:
                # Log what we're about to save
                cleaned_data = form.cleaned_data
                grade = cleaned_data.get('grade')
                subject = cleaned_data.get('subject')
                teacher = cleaned_data.get('teacher')
                
                # If teacher is not set but we have grade and subject, try to set it automatically
                if not teacher and grade and subject:
                    try:
                        class_subject = ClassSubject.objects.get(grade=grade, subject=subject)
                        if class_subject.teacher:
                            timetable = form.save(commit=False)
                            timetable.teacher = class_subject.teacher
                            timetable.save()
                            print(f"DEBUG - Auto-assigned teacher in view: {class_subject.teacher.get_full_name()}")
                            messages.success(request, 'Timetable entry added successfully!')
                            return redirect('academics:timetable_list')
                        else:
                            messages.error(request, 'No teacher is assigned to this subject for this grade.')
                    except ClassSubject.DoesNotExist:
                        messages.error(request, 'This subject is not assigned to this grade.')
                    except Exception as e:
                        print(f"DEBUG - Error finding teacher: {str(e)}")
                        messages.error(request, f'Error finding teacher: {str(e)}')
                else:
                    # Normal flow if teacher is already set
                    timetable = form.save()
                    print(f"DEBUG - Saved timetable with ID: {timetable.id}, Teacher: {timetable.teacher.get_full_name()}")
                    messages.success(request, 'Timetable entry added successfully!')
                    return redirect('academics:timetable_list')
            except Exception as e:
                import traceback
                error_detail = traceback.format_exc()
                print(f"DEBUG - Error saving timetable: {str(e)}\n{error_detail}")
                messages.error(request, f'Error saving timetable entry: {str(e)}')
    else:
        form = TimetableForm()
    
    context = {
        'form': form
    }
    return render(request, 'academics/timetable_form.html', context)

@login_required
@admin_required
def edit_timetable(request, pk):
    """View to edit timetable entries"""
    timetable = get_object_or_404(Timetable, pk=pk)
    
    if request.method == 'POST':
        print(f"DEBUG - Editing timetable {pk} - POST data:", request.POST)
        form = TimetableForm(request.POST, instance=timetable)
        
        # Log form errors if present
        if not form.is_valid():
            print("DEBUG - Form errors:", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            if form.non_field_errors():
                for error in form.non_field_errors():
                    messages.error(request, error)
        else:
            try:
                # Log what we're about to save
                cleaned_data = form.cleaned_data
                teacher = cleaned_data.get('teacher')
                print(f"DEBUG - About to update timetable with teacher: {teacher.id if teacher else 'None'} - {teacher.get_full_name() if teacher else 'None'}")
                
                timetable = form.save()
                print(f"DEBUG - Updated timetable with ID: {timetable.id}")
                messages.success(request, 'Timetable entry updated successfully!')
                return redirect('academics:timetable_list')
            except Exception as e:
                import traceback
                error_detail = traceback.format_exc()
                print(f"DEBUG - Error updating timetable: {str(e)}\n{error_detail}")
                messages.error(request, f'Error updating timetable entry: {str(e)}')
    else:
        form = TimetableForm(instance=timetable)
        # Log the current teacher for debugging
        if timetable.teacher:
            print(f"DEBUG - Initial teacher for timetable {pk}: {timetable.teacher.id} - {timetable.teacher.get_full_name()}")
    
    context = {
        'form': form,
        'timetable': timetable
    }
    return render(request, 'academics/timetable_form.html', context)

@login_required
@admin_required
def delete_timetable(request, pk):
    """View to delete timetable entries"""
    timetable = get_object_or_404(Timetable, pk=pk)
    
    if request.method == 'POST':
        timetable.delete()
        messages.success(request, 'Timetable entry deleted successfully!')
        return redirect('academics:timetable_list')
    
    context = {
        'timetable': timetable
    }
    return render(request, 'academics/timetable_confirm_delete.html', context)

# Assignment Management
@login_required
def assignment_list(request):
    """View to list assignments"""
    if request.user.is_teacher:
        assignments = Assignment.objects.filter(teacher=request.user)
    elif request.user.is_student:
        student = get_object_or_404(Student, user=request.user)
        assignments = Assignment.objects.filter(
            grade=student.grade,
            subject__in=Subject.objects.filter(
                class_subjects__grade=student.grade,
                class_subjects__section=student.section
            )
        )
    else:
        assignments = Assignment.objects.all()

    # Get filter parameters
    selected_grade = request.GET.get('grade')
    selected_subject = request.GET.get('subject')
    selected_status = request.GET.get('status')

    # Apply filters
    if selected_grade:
        assignments = assignments.filter(grade_id=selected_grade)
    if selected_subject:
        assignments = assignments.filter(subject_id=selected_subject)
    if selected_status:
        if selected_status == 'pending':
            assignments = assignments.exclude(submissions__student__user=request.user)
        elif selected_status == 'submitted':
            assignments = assignments.filter(submissions__student__user=request.user, submissions__status='submitted')
        elif selected_status == 'graded':
            assignments = assignments.filter(submissions__student__user=request.user, submissions__status='graded')

    # Get available filters
    if request.user.is_teacher:
        grades = Grade.objects.filter(class_subjects__teacher=request.user).distinct()
    else:
        grades = Grade.objects.none()
    
    if request.user.is_student:
        student = get_object_or_404(Student, user=request.user)
        subjects = Subject.objects.filter(
            class_subjects__grade=student.grade,
            class_subjects__section=student.section
        ).distinct()
    else:
        subjects = Subject.objects.filter(class_subjects__grade__in=assignments.values('grade')).distinct()

    context = {
        'assignments': assignments,
        'grades': grades,
        'subjects': subjects,
        'selected_grade': selected_grade,
        'selected_subject': selected_subject,
        'selected_status': selected_status,
    }
    return render(request, 'academics/assignment_list.html', context)

@login_required
@teacher_required
def add_assignment(request):
    """View to add assignments"""
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.teacher = request.user
            assignment.save()
            messages.success(request, 'Assignment added successfully!')
            return redirect('academics:assignment_list')
    else:
        form = AssignmentForm(user=request.user)
    
    context = {
        'form': form
    }
    return render(request, 'academics/assignment_form.html', context)

@login_required
@teacher_required
def edit_assignment(request, pk):
    """View to edit assignments"""
    assignment = get_object_or_404(Assignment, pk=pk, teacher=request.user)
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES, instance=assignment, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Assignment updated successfully!')
            return redirect('academics:assignment_list')
    else:
        form = AssignmentForm(instance=assignment, user=request.user)
    
    context = {
        'form': form,
        'assignment': assignment
    }
    return render(request, 'academics/assignment_form.html', context)

@login_required
@teacher_required
def delete_assignment(request, pk):
    """View to delete assignments"""
    assignment = get_object_or_404(Assignment, pk=pk, teacher=request.user)
    
    if request.method == 'POST':
        assignment.delete()
        messages.success(request, 'Assignment deleted successfully!')
        return redirect('academics:assignment_list')
    
    context = {
        'assignment': assignment
    }
    return render(request, 'academics/assignment_confirm_delete.html', context)

@login_required
@teacher_required
def assignment_submissions(request, pk):
    """View to list submissions for an assignment"""
    assignment = get_object_or_404(Assignment, pk=pk, teacher=request.user)
    submissions = AssignmentSubmission.objects.filter(assignment=assignment).select_related('student', 'student__user')
    
    context = {
        'assignment': assignment,
        'submissions': submissions
    }
    return render(request, 'academics/assignment_submissions.html', context)

@login_required
def assignment_detail(request, pk):
    """View to display assignment details"""
    from django.utils import timezone
    
    assignment = get_object_or_404(Assignment, pk=pk)
    
    # Check permissions
    if not request.user.is_admin:
        if request.user.is_teacher and assignment.teacher != request.user:
            messages.error(request, "You don't have permission to view this assignment.")
            return redirect('academics:assignment_list')
        elif request.user.is_student:
            # Check if student is in the assigned grade and section
            try:
                student = Student.objects.get(user=request.user)
                if (assignment.grade != student.grade) or (assignment.section and assignment.section != student.section):
                    messages.error(request, "This assignment is not for your class.")
                    return redirect('academics:assignment_list')
            except Student.DoesNotExist:
                messages.error(request, "You don't have permission to view this assignment.")
                return redirect('academics:assignment_list')
    
    # Get submission for this student if applicable
    student_submission = None
    if request.user.is_student:
        try:
            student = Student.objects.get(user=request.user)
            student_submission = AssignmentSubmission.objects.filter(
                assignment=assignment,
                student=student
            ).first()
        except Student.DoesNotExist:
            pass
    
    # Get all submissions if teacher or admin
    submissions = None
    submissions_graded_count = 0
    submissions_pending_count = 0
    
    if request.user.is_admin or (request.user.is_teacher and assignment.teacher == request.user):
        submissions = AssignmentSubmission.objects.filter(
            assignment=assignment
        ).select_related('student', 'student__user', 'student__grade', 'student__section')
        
        # Count graded and pending submissions
        submissions_graded_count = submissions.filter(status='graded').count()
        submissions_pending_count = submissions.filter(status='submitted').count()
    
    context = {
        'assignment': assignment,
        'student_submission': student_submission,
        'submissions': submissions,
        'submissions_graded_count': submissions_graded_count,
        'submissions_pending_count': submissions_pending_count,
        'now': timezone.now()
    }
    return render(request, 'academics/assignment_detail.html', context)

@login_required
def submit_assignment(request, pk):
    """View for students to submit assignments"""
    assignment = get_object_or_404(Assignment, pk=pk)
    
    # Check if student is in the assigned grade and section
    try:
        student = Student.objects.get(user=request.user)
        if (assignment.grade != student.grade) or (assignment.section and assignment.section != student.section):
            messages.error(request, "This assignment is not for your class.")
            return redirect('academics:assignment_list')
    except Student.DoesNotExist:
        messages.error(request, "You must be a student to submit assignments.")
        return redirect('academics:assignment_list')
    
    # Check if student has already submitted
    existing_submission = AssignmentSubmission.objects.filter(
        assignment=assignment,
        student=student
    ).first()
    
    if request.method == 'POST':
        # Handle file upload
        submitted_file = request.FILES.get('submission_file')
        submission_text = request.POST.get('submission_text', '')
        
        if not submitted_file and not submission_text:
            messages.error(request, "You must submit either a file or text content.")
        else:
            if existing_submission:
                # Update existing submission
                if submitted_file:
                    existing_submission.file = submitted_file
                existing_submission.submission_text = submission_text
                existing_submission.submitted_at = timezone.now()
                existing_submission.status = 'submitted'
                existing_submission.save()
                messages.success(request, "Your assignment has been resubmitted successfully.")
            else:
                # Create new submission
                submission = AssignmentSubmission(
                    assignment=assignment,
                    student=student,
                    file=submitted_file,
                    submission_text=submission_text,
                    status='submitted'
                )
                submission.save()
                messages.success(request, "Your assignment has been submitted successfully.")
            
            return redirect('academics:assignment_detail', pk=assignment.pk)
    
    context = {
        'assignment': assignment,
        'existing_submission': existing_submission
    }
    return render(request, 'academics/submit_assignment.html', context)

@login_required
@teacher_required
def grade_submission(request, pk):
    """View for teachers to grade assignment submissions"""
    submission = get_object_or_404(AssignmentSubmission, pk=pk)
    
    # Check if the teacher is authorized to grade this submission
    if submission.assignment.teacher != request.user:
        messages.error(request, "You don't have permission to grade this submission.")
        return redirect('academics:assignment_list')
    
    if request.method == 'POST':
        grade = request.POST.get('grade')
        feedback = request.POST.get('feedback', '')
        
        try:
            grade_value = float(grade)
            if grade_value < 0 or grade_value > submission.assignment.max_score:
                messages.error(request, f"Grade must be between 0 and {submission.assignment.max_score}.")
            else:
                submission.grade = grade_value
                submission.feedback = feedback
                submission.graded_at = timezone.now()
                submission.status = 'graded'
                submission.save()
                messages.success(request, "Submission graded successfully.")
                return redirect('academics:assignment_detail', pk=submission.assignment.pk)
        except ValueError:
            messages.error(request, "Please enter a valid numeric grade.")
    
    context = {
        'submission': submission,
        'assignment': submission.assignment
    }
    return render(request, 'academics/grade_submission.html', context)

# Exam Management
@login_required
@admin_required
def exam_list(request):
    """View to list exams"""
    exams = Exam.objects.all().select_related('exam_type', 'academic_session', 'grade')
    
    # Get filter parameters
    grade_id = request.GET.get('grade', '')
    exam_type_id = request.GET.get('exam_type', '')
    session_id = request.GET.get('session', '')
    status = request.GET.get('status', '')
    
    # Apply filters
    if grade_id:
        exams = exams.filter(grade_id=grade_id)
    
    if exam_type_id:
        exams = exams.filter(exam_type_id=exam_type_id)
    
    if session_id:
        exams = exams.filter(academic_session_id=session_id)
    
    if status:
        from django.utils import timezone
        today = timezone.now().date()
        
        if status == 'upcoming':
            exams = exams.filter(start_date__gt=today)
        elif status == 'ongoing':
            exams = exams.filter(start_date__lte=today, end_date__gte=today)
        elif status == 'completed':
            exams = exams.filter(end_date__lt=today)
    
    # Get data for dropdowns
    grades = Grade.objects.all()
    exam_types = ExamType.objects.all()
    academic_sessions = AcademicSession.objects.all()
    
    context = {
        'exams': exams,
        'grades': grades,
        'exam_types': exam_types,
        'academic_sessions': academic_sessions
    }
    return render(request, 'academics/exam_list.html', context)

@login_required
@admin_required
def add_exam(request):
    """View to add exams"""
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exam added successfully!')
            return redirect('academics:exam_list')
    else:
        form = ExamForm()
    
    context = {
        'form': form
    }
    return render(request, 'academics/exam_form.html', context)

@login_required
@admin_required
def edit_exam(request, pk):
    """View to edit exams"""
    exam = get_object_or_404(Exam, pk=pk)
    
    if request.method == 'POST':
        form = ExamForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exam updated successfully!')
            return redirect('academics:exam_list')
    else:
        form = ExamForm(instance=exam)
    
    context = {
        'form': form,
        'exam': exam
    }
    return render(request, 'academics/exam_form.html', context)

@login_required
@admin_required
def delete_exam(request, pk):
    """View to delete exams"""
    exam = get_object_or_404(Exam, pk=pk)
    
    if request.method == 'POST':
        exam.delete()
        messages.success(request, 'Exam deleted successfully!')
        return redirect('academics:exam_list')
    
    context = {
        'exam': exam
    }
    return render(request, 'academics/exam_confirm_delete.html', context)

@login_required
def exam_detail(request, pk):
    """View for detailed information about an exam"""
    exam = get_object_or_404(Exam, pk=pk)
    
    # Get exam schedules
    schedules = ExamSchedule.objects.filter(exam=exam).select_related('subject')
    
    # Get student marks if student
    student_marks = None
    if request.user.is_student:
        try:
            student = Student.objects.get(user=request.user)
            student_marks = Mark.objects.filter(
                exam=exam,
                student=student
            ).select_related('subject')
        except Student.DoesNotExist:
            pass
    
    # Get all marks if admin or teacher
    all_marks = None
    if request.user.is_admin or request.user.is_teacher:
        all_marks = Mark.objects.filter(exam=exam).select_related('student', 'student__user', 'subject')
    
    context = {
        'exam': exam,
        'schedules': schedules,
        'student_marks': student_marks,
        'all_marks': all_marks
    }
    return render(request, 'academics/exam_detail.html', context)

@login_required
@admin_required
def exam_schedule(request, pk):
    """View to manage exam schedule"""
    exam = get_object_or_404(Exam, pk=pk)
    schedules = ExamSchedule.objects.filter(exam=exam).select_related('subject')
    
    context = {
        'exam': exam,
        'schedules': schedules
    }
    return render(request, 'academics/exam_schedule.html', context)

@login_required
@admin_required
def exam_marks(request, pk):
    """View to view/manage exam marks"""
    exam = get_object_or_404(Exam, pk=pk)
    marks = Mark.objects.filter(exam=exam).select_related('student', 'student__user', 'subject')
    
    context = {
        'exam': exam,
        'marks': marks
    }
    return render(request, 'academics/exam_marks.html', context)

@login_required
@admin_required
def add_exam_grade(request, pk):
    """View to add exam grades/marks for students"""
    exam = get_object_or_404(Exam, pk=pk)
    
    if request.method == 'POST':
        student_id = request.POST.get('student')
        subject_id = request.POST.get('subject')
        marks_obtained = request.POST.get('marks_obtained')
        remarks = request.POST.get('remarks', '')
        
        try:
            student = Student.objects.get(pk=student_id)
            subject = Subject.objects.get(pk=subject_id)
            marks_value = float(marks_obtained)
            
            # Check if mark already exists
            existing_mark = Mark.objects.filter(
                exam=exam,
                student=student,
                subject=subject
            ).first()
            
            if existing_mark:
                existing_mark.marks_obtained = marks_value
                existing_mark.remarks = remarks
                existing_mark.save()
                messages.success(request, f"Marks for {student.user.get_full_name()} updated successfully.")
            else:
                mark = Mark(
                    exam=exam,
                    student=student,
                    subject=subject,
                    marks_obtained=marks_value,
                    remarks=remarks
                )
                mark.save()
                messages.success(request, f"Marks for {student.user.get_full_name()} added successfully.")
                
            return redirect('academics:exam_marks', pk=exam.pk)
            
        except (Student.DoesNotExist, Subject.DoesNotExist):
            messages.error(request, "Invalid student or subject selected.")
        except ValueError:
            messages.error(request, "Please enter valid numeric marks.")
    
    # Get students and subjects for the form
    students = Student.objects.filter(grade=exam.grade).select_related('user')
    subjects = Subject.objects.filter(class_subjects__grade=exam.grade).distinct()
    
    context = {
        'exam': exam,
        'students': students,
        'subjects': subjects
    }
    return render(request, 'academics/add_exam_grade.html', context)

@login_required
@admin_required
def edit_exam_grade(request, pk):
    """View to edit exam grades/marks"""
    mark = get_object_or_404(Mark, pk=pk)
    exam = mark.exam
    
    if request.method == 'POST':
        marks_obtained = request.POST.get('marks_obtained')
        remarks = request.POST.get('remarks', '')
        
        try:
            marks_value = float(marks_obtained)
            mark.marks_obtained = marks_value
            mark.remarks = remarks
            mark.save()
            messages.success(request, "Marks updated successfully.")
            return redirect('academics:exam_marks', pk=exam.pk)
        except ValueError:
            messages.error(request, "Please enter valid numeric marks.")
    
    context = {
        'mark': mark,
        'exam': exam
    }
    return render(request, 'academics/edit_exam_grade.html', context)

@login_required
@admin_required
def delete_exam_grade(request, pk):
    """View to delete exam grades/marks"""
    mark = get_object_or_404(Mark, pk=pk)
    exam = mark.exam
    
    if request.method == 'POST':
        student_name = mark.student.user.get_full_name()
        mark.delete()
        messages.success(request, f"Marks for {student_name} deleted successfully.")
        return redirect('academics:exam_marks', pk=exam.pk)
    
    context = {
        'mark': mark,
        'exam': exam
    }
    return render(request, 'academics/delete_exam_grade.html', context)

@login_required
def grade_sections_api(request, grade_id):
    """API endpoint to get sections for a grade"""
    from django.http import JsonResponse
    
    try:
        grade = Grade.objects.get(id=grade_id)
        sections_queryset = Section.objects.filter(grade=grade)
        
        # If teacher_only parameter is provided and user is a teacher
        teacher_only = request.GET.get('teacher_only') == 'true'
        if teacher_only and request.user.is_teacher:
            # Get all class subjects for this teacher and grade
            class_subjects = ClassSubject.objects.filter(
                grade=grade,
                teacher=request.user
            )
            
            # Check if teacher has any sections that are specifically assigned
            has_specific_sections = class_subjects.exclude(section=None).exists()
            
            # Check if teacher has any subjects without specific section (teaches all sections)
            teaches_all_sections = class_subjects.filter(section=None).exists()
            
            if has_specific_sections and not teaches_all_sections:
                # Only show specific sections if teacher doesn't teach "all sections"
                teacher_sections = class_subjects.exclude(section=None).values_list('section', flat=True).distinct()
                sections_queryset = sections_queryset.filter(id__in=teacher_sections)
            elif not has_specific_sections and not teaches_all_sections:
                # If teacher has no assignments at all for this grade, return empty
                sections_queryset = Section.objects.none()
            # If teaches_all_sections is True, keep all sections (default behavior)
        
        sections = sections_queryset.values('id', 'name')
        return JsonResponse({
            'status': 'success',
            'sections': list(sections)
        })
    except Grade.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Grade not found',
            'sections': []
        })
    except Exception as e:
        print(f"Error in grade_sections_api: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'sections': []
        })

@login_required
def grade_subjects_api(request, grade_id):
    """API endpoint to get subjects for a grade"""
    from django.http import JsonResponse
    
    try:
        grade = Grade.objects.get(id=grade_id)
        class_subjects = ClassSubject.objects.filter(grade=grade).select_related('subject', 'teacher')
        
        subjects = []
        for cs in class_subjects:
            subject_data = {
                'id': cs.subject.id,
                'name': cs.subject.name
            }
            
            if cs.teacher:
                subject_data['teacher_name'] = cs.teacher.get_full_name()
                subject_data['teacher_id'] = cs.teacher.id
            
            subjects.append(subject_data)
        
        return JsonResponse({
            'status': 'success',
            'subjects': subjects
        })
    except Grade.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Grade not found',
            'subjects': []
        })

@login_required
def available_subjects_api(request):
    """API view to get available (unscheduled) subjects for a grade at a specific day and time slot"""
    grade_id = request.GET.get('grade_id')
    section_id = request.GET.get('section_id')
    day_id = request.GET.get('day_id')
    time_slot_id = request.GET.get('time_slot_id')
    academic_session_id = request.GET.get('academic_session_id')
    
    if not all([grade_id, day_id, time_slot_id]):
        return JsonResponse({'error': 'Missing required parameters'}, status=400)
    
    try:
        # Get all subjects for this grade from ClassSubject
        class_subjects = ClassSubject.objects.filter(grade_id=grade_id).select_related('subject', 'teacher')
        
        # Find subjects that are already scheduled for this grade, section, day and time slot
        scheduled_subjects = []
        if section_id:
            filters = {
                'grade_id': grade_id,
                'section_id': section_id,
                'day_id': day_id,
                'time_slot_id': time_slot_id
            }
            
            # Add academic session filter if provided
            if academic_session_id:
                filters['academic_session_id'] = academic_session_id
                
            already_scheduled = Timetable.objects.filter(**filters).values_list('subject_id', flat=True)
            scheduled_subjects.extend(already_scheduled)
        
        # Also find subjects whose teachers are already booked at this time slot on this day
        teachers_busy = {}
        for cs in class_subjects:
            if cs.teacher:
                filters = {
                    'teacher': cs.teacher,
                    'day_id': day_id,
                    'time_slot_id': time_slot_id
                }
                
                # Add academic session filter if provided
                if academic_session_id:
                    filters['academic_session_id'] = academic_session_id
                    
                teacher_busy_elsewhere = Timetable.objects.filter(**filters).exists()
                
                if teacher_busy_elsewhere:
                    teachers_busy[cs.subject.id] = cs.teacher.get_full_name()
        
        subjects_data = []
        for cs in class_subjects:
            # Check if this subject is already scheduled or its teacher is busy
            is_available = cs.subject.id not in scheduled_subjects
            teacher_conflict = teachers_busy.get(cs.subject.id)
            
            subject_data = {
                'id': cs.subject.id,
                'name': f"{cs.subject.name} ({cs.subject.code})",
                'teacher_name': cs.teacher.get_full_name() if cs.teacher else "No teacher assigned",
                'teacher_id': cs.teacher.id if cs.teacher else None,
                'is_available': is_available,
                'conflict_reason': f"Teacher {teacher_conflict} is already teaching during this time slot" if teacher_conflict else None
            }
            subjects_data.append(subject_data)
        
        return JsonResponse({
            'subjects': subjects_data, 
            'scheduled_subjects': list(scheduled_subjects),
            'teachers_busy': teachers_busy
        })
    except Exception as e:
        import traceback
        error_msg = f"Error in available_subjects_api: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)  # For server logs
        return JsonResponse({'error': str(e), 'message': 'An error occurred while fetching subjects'}, status=500)

# Reports
@login_required
@admin_required
def academic_report(request):
    """View to generate and display academic reports"""
    # Get filter parameters
    grade_id = request.GET.get('grade', '')
    section_id = request.GET.get('section', '')
    session_id = request.GET.get('session', '')
    student_id = request.GET.get('student', '')
    
    # Base queryset for students
    students = Student.objects.all().select_related('user', 'grade', 'section', 'academic_session')
    
    # Apply filters
    if grade_id:
        students = students.filter(grade_id=grade_id)
    
    if section_id:
        students = students.filter(section_id=section_id)
    
    if session_id:
        students = students.filter(academic_session_id=session_id)
    
    if student_id:
        students = students.filter(id=student_id)
    
    # Get data for dropdowns
    grades = Grade.objects.all()
    sections = Section.objects.all()
    if grade_id:
        sections = sections.filter(grade_id=grade_id)
    
    academic_sessions = AcademicSession.objects.all()
    
    # Get exam results for selected students
    results = []
    
    for student in students:
        # Get all exams for this student's grade
        exams = Exam.objects.filter(grade=student.grade, academic_session=student.academic_session)
        
        student_results = {
            'student': student,
            'exams': []
        }
        
        for exam in exams:
            # Get marks for this student in this exam
            marks = Mark.objects.filter(
                student=student,
                exam=exam
            ).select_related('subject')
            
            if marks.exists():
                total_marks = marks.aggregate(total=models.Sum('marks_obtained'))['total'] or 0
                max_possible = sum(mark.subject.max_marks for mark in marks)
                percentage = (total_marks / max_possible * 100) if max_possible > 0 else 0
                
                exam_result = {
                    'exam': exam,
                    'marks': marks,
                    'total_marks': total_marks,
                    'max_possible': max_possible,
                    'percentage': round(percentage, 2)
                }
                
                student_results['exams'].append(exam_result)
        
        if student_results['exams']:
            results.append(student_results)
    
    context = {
        'students': students,
        'grades': grades,
        'sections': sections,
        'academic_sessions': academic_sessions,
        'selected_grade': grade_id,
        'selected_section': section_id,
        'selected_session': session_id,
        'selected_student': student_id,
        'results': results
    }
    return render(request, 'academics/academic_report.html', context)

@login_required
@admin_required
def attendance_report(request):
    """View to generate and display attendance reports"""
    # Get filter parameters
    grade_id = request.GET.get('grade', '')
    section_id = request.GET.get('section', '')
    subject_id = request.GET.get('subject', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    # Base queryset for attendance
    attendance_records = Attendance.objects.all().select_related(
        'student', 'student__user', 'student__grade', 'student__section', 'subject'
    )
    
    # Apply filters
    if grade_id:
        attendance_records = attendance_records.filter(student__grade_id=grade_id)
    
    if section_id:
        attendance_records = attendance_records.filter(student__section_id=section_id)
    
    if subject_id:
        attendance_records = attendance_records.filter(subject_id=subject_id)
    
    if start_date:
        attendance_records = attendance_records.filter(date__gte=start_date)
    
    if end_date:
        attendance_records = attendance_records.filter(date__lte=end_date)
    
    # Aggregate attendance data by student
    student_attendance = {}
    
    for record in attendance_records:
        student_id = record.student.id
        
        if student_id not in student_attendance:
            student_attendance[student_id] = {
                'student': record.student,
                'total': 0,
                'present': 0,
                'absent': 0,
                'by_subject': {}
            }
        
        # Update overall attendance
        student_attendance[student_id]['total'] += 1
        if record.is_present:
            student_attendance[student_id]['present'] += 1
        else:
            student_attendance[student_id]['absent'] += 1
        
        # Update subject-wise attendance
        subject_id = record.subject.id
        if subject_id not in student_attendance[student_id]['by_subject']:
            student_attendance[student_id]['by_subject'][subject_id] = {
                'subject': record.subject,
                'total': 0,
                'present': 0,
                'absent': 0
            }
        
        student_attendance[student_id]['by_subject'][subject_id]['total'] += 1
        if record.is_present:
            student_attendance[student_id]['by_subject'][subject_id]['present'] += 1
        else:
            student_attendance[student_id]['by_subject'][subject_id]['absent'] += 1
    
    # Calculate percentages and convert to list
    attendance_data = []
    
    for student_id, data in student_attendance.items():
        # Calculate overall percentage
        overall_percentage = round((data['present'] / data['total'] * 100) if data['total'] > 0 else 0, 2)
        data['percentage'] = overall_percentage
        
        # Calculate subject percentages
        for subject_id, subject_data in data['by_subject'].items():
            subject_percentage = round((subject_data['present'] / subject_data['total'] * 100) if subject_data['total'] > 0 else 0, 2)
            subject_data['percentage'] = subject_percentage
        
        attendance_data.append(data)
    
    # Sort by student name
    attendance_data.sort(key=lambda x: x['student'].user.get_full_name())
    
    # Get data for dropdowns
    grades = Grade.objects.all()
    sections = Section.objects.all()
    if grade_id:
        sections = sections.filter(grade_id=grade_id)
    
    subjects = Subject.objects.all()
    
    context = {
        'grades': grades,
        'sections': sections,
        'subjects': subjects,
        'selected_grade': grade_id,
        'selected_section': section_id,
        'selected_subject': subject_id,
        'start_date': start_date,
        'end_date': end_date,
        'attendance_data': attendance_data
    }
    return render(request, 'academics/attendance_report.html', context)

@login_required
def student_report_card(request, student_id):
    """Generate a comprehensive report card for a specific student"""
    try:
        # Get the student
        student = Student.objects.select_related('user', 'grade', 'section', 'academic_session').get(id=student_id)
        
        # Check permissions - only admin, the student themselves, or a teacher can view
        if not (request.user.is_admin or 
                (request.user.is_student and request.user.student_record == student) or 
                request.user.is_teacher):
            messages.error(request, "You don't have permission to view this report card.")
            return redirect('academics:student_list')
        
        # Get all exams for this student's grade and academic session
        exams = Exam.objects.filter(
            grade=student.grade, 
            academic_session=student.academic_session
        ).order_by('start_date')
        
        # Get all subjects for this student's grade
        subjects = Subject.objects.filter(grade=student.grade)
        
        # Prepare data structure for the report card
        report_data = {
            'student': student,
            'exams': [],
            'final_result': {
                'total_marks': 0,
                'max_possible': 0,
                'percentage': 0,
                'grade': '',
                'remarks': ''
            },
            'attendance': {
                'total_days': 0,
                'present_days': 0,
                'absent_days': 0,
                'percentage': 0,
                'by_subject': {}
            }
        }
        
        # Get marks for each exam
        cumulative_marks_obtained = 0
        cumulative_max_marks = 0
        
        for exam in exams:
            # Get all marks for this student in this exam
            marks = Mark.objects.filter(
                student=student,
                exam=exam
            ).select_related('subject')
            
            if marks.exists():
                total_marks = marks.aggregate(total=models.Sum('marks_obtained'))['total'] or 0
                max_possible = marks.aggregate(total=models.Sum('maximum_marks'))['total'] or 0
                percentage = (total_marks / max_possible * 100) if max_possible > 0 else 0
                
                # Calculate grade based on percentage
                grade = 'F'
                if percentage >= 90:
                    grade = 'A+'
                elif percentage >= 80:
                    grade = 'A'
                elif percentage >= 70:
                    grade = 'B+'
                elif percentage >= 60:
                    grade = 'B'
                elif percentage >= 50:
                    grade = 'C'
                elif percentage >= 40:
                    grade = 'D'
                
                exam_result = {
                    'exam': exam,
                    'marks': marks,
                    'total_marks': total_marks,
                    'max_possible': max_possible,
                    'percentage': round(percentage, 2),
                    'grade': grade
                }
                
                report_data['exams'].append(exam_result)
                
                # Add to cumulative totals for final result
                cumulative_marks_obtained += total_marks
                cumulative_max_marks += max_possible
        
        # Calculate final result
        if cumulative_max_marks > 0:
            final_percentage = (cumulative_marks_obtained / cumulative_max_marks * 100)
            final_grade = 'F'
            remarks = 'Needs significant improvement.'
            
            if final_percentage >= 90:
                final_grade = 'A+'
                remarks = 'Outstanding performance! Excellent work throughout the year.'
            elif final_percentage >= 80:
                final_grade = 'A'
                remarks = 'Excellent performance. Keep up the good work!'
            elif final_percentage >= 70:
                final_grade = 'B+'
                remarks = 'Very good performance. Consistent effort shown.'
            elif final_percentage >= 60:
                final_grade = 'B'
                remarks = 'Good performance. Continue working hard.'
            elif final_percentage >= 50:
                final_grade = 'C'
                remarks = 'Satisfactory performance. More effort needed in some areas.'
            elif final_percentage >= 40:
                final_grade = 'D'
                remarks = 'Pass. Needs to work harder to improve performance.'
            
            report_data['final_result']['total_marks'] = cumulative_marks_obtained
            report_data['final_result']['max_possible'] = cumulative_max_marks
            report_data['final_result']['percentage'] = round(final_percentage, 2)
            report_data['final_result']['grade'] = final_grade
            report_data['final_result']['remarks'] = remarks
        
        # Get attendance data
        attendance_records = Attendance.objects.filter(
            student=student,
            date__gte=student.academic_session.start_date,
            date__lte=student.academic_session.end_date
        ).select_related('subject')
        
        # Calculate overall attendance
        total_days = attendance_records.count()
        present_days = attendance_records.filter(is_present=True).count()
        absent_days = total_days - present_days
        attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
        
        report_data['attendance']['total_days'] = total_days
        report_data['attendance']['present_days'] = present_days
        report_data['attendance']['absent_days'] = absent_days
        report_data['attendance']['percentage'] = round(attendance_percentage, 2)
        
        # Calculate subject-wise attendance
        for subject in subjects:
            subject_records = attendance_records.filter(subject=subject)
            subject_total = subject_records.count()
            subject_present = subject_records.filter(is_present=True).count()
            subject_absent = subject_total - subject_present
            subject_percentage = (subject_present / subject_total * 100) if subject_total > 0 else 0
            
            report_data['attendance']['by_subject'][subject.id] = {
                'subject': subject,
                'total': subject_total,
                'present': subject_present,
                'absent': subject_absent,
                'percentage': round(subject_percentage, 2)
            }
        
        # Teachers' comments and remarks (could be expanded in a real system)
        report_data['teacher_remarks'] = []
        
        context = {
            'report_data': report_data,
            'title': f"{student.user.get_full_name()} - Report Card",
            'academic_year': student.academic_session,
            'today': timezone.now().date()
        }
        
        return render(request, 'academics/student_report_card.html', context)
    
    except Student.DoesNotExist:
        messages.error(request, "Student not found.")
        return redirect('academics:student_list')
