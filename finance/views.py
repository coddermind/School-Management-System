from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.mixins import admin_required
from academics.models import Student
from accounts.models import User
from .models import FeeCategory, FeeStructure, FeePayment, SalaryStructure, SalaryPayment
from django.db.models import Sum, Avg, Q
from django.utils import timezone
from datetime import datetime
from django.core.paginator import Paginator
from academics.models import Grade
import calendar

# Create placeholder views for the finance app
@login_required
@admin_required
def fee_category_list(request):
    """View to list all fee categories"""
    context = {
        'categories': FeeCategory.objects.all()
    }
    return render(request, 'finance/fee_category_list.html', context)

@login_required
@admin_required
def add_fee_category(request):
    """View to add a new fee category"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        
        if name:
            try:
                # Check if a category with this name already exists
                if FeeCategory.objects.filter(name=name).exists():
                    messages.error(request, f"Fee category '{name}' already exists.")
                else:
                    # Create the new category
                    FeeCategory.objects.create(
                        name=name,
                        description=description
                    )
                    messages.success(request, f"Fee category '{name}' added successfully.")
                    return redirect('finance:fee_category_list')
            except Exception as e:
                messages.error(request, f"Error adding fee category: {str(e)}")
        else:
            messages.error(request, "Category name is required.")
    
    context = {
        'title': 'Add Fee Category'
    }
    return render(request, 'finance/fee_category_form.html', context)

@login_required
@admin_required
def edit_fee_category(request, pk):
    """View to edit a fee category"""
    return redirect('finance:fee_category_list')

@login_required
@admin_required
def delete_fee_category(request, pk):
    """View to delete a fee category"""
    return redirect('finance:fee_category_list')

# Fee Structure
@login_required
@admin_required
def fee_structure_list(request):
    """View to list all fee structures"""
    context = {
        'fee_structures': FeeStructure.objects.all()
    }
    return render(request, 'finance/fee_structure_list.html', context)

@login_required
@admin_required
def add_fee_structure(request):
    """View to add a new fee structure"""
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        grade_id = request.POST.get('grade')
        amount = request.POST.get('amount')
        description = request.POST.get('description', '')
        is_mandatory = request.POST.get('is_mandatory') == 'on'
        applicable_from = request.POST.get('applicable_from')
        
        if name and category_id and grade_id and amount:
            try:
                category = FeeCategory.objects.get(id=category_id)
                grade = Grade.objects.get(id=grade_id)
                
                # Create the fee structure
                FeeStructure.objects.create(
                    name=name,
                    category=category,
                    grade=grade,
                    amount=amount,
                    description=description,
                    is_mandatory=is_mandatory,
                    applicable_from=applicable_from or timezone.now().date()
                )
                
                messages.success(request, f"Fee structure '{name}' created successfully.")
                return redirect('finance:fee_structure_list')
                
            except FeeCategory.DoesNotExist:
                messages.error(request, "Selected fee category does not exist.")
            except Grade.DoesNotExist:
                messages.error(request, "Selected grade/class does not exist.")
            except Exception as e:
                messages.error(request, f"Error creating fee structure: {str(e)}")
        else:
            messages.error(request, "All required fields must be filled.")
    
    # GET request
    categories = FeeCategory.objects.all()
    grades = Grade.objects.all()
    
    context = {
        'categories': categories,
        'grades': grades,
        'title': 'Add Fee Structure'
    }
    return render(request, 'finance/fee_structure_form.html', context)

@login_required
@admin_required
def edit_fee_structure(request, pk):
    """View to edit a fee structure"""
    return redirect('finance:fee_structure_list')

@login_required
@admin_required
def delete_fee_structure(request, pk):
    """View to delete a fee structure"""
    return redirect('finance:fee_structure_list')

# Fee Payments
@login_required
@admin_required
def fee_payment_list(request):
    """View to list all fee payments"""
    # Get all students and fee categories for the filter
    all_students = Student.objects.all().select_related('user')
    
    # Base queryset
    payments_queryset = FeePayment.objects.all().select_related(
        'student__user', 'student__grade', 'student__section',
        'fee_structure__category'
    ).order_by('-payment_date')
    
    # Apply filters
    if request.GET.get('search'):
        search_query = request.GET.get('search').strip()
        payments_queryset = payments_queryset.filter(
            Q(student__user__first_name__icontains=search_query) | 
            Q(student__user__last_name__icontains=search_query) | 
            Q(student__roll_number__icontains=search_query)
        )
    
    if request.GET.get('payment_status'):
        payment_status = request.GET.get('payment_status')
        if payment_status == 'PENDING':
            payments_queryset = payments_queryset.filter(payment_method='PENDING')
        else:
            payments_queryset = payments_queryset.filter(payment_method=payment_status)
    
    if request.GET.get('from_date'):
        try:
            from_date = datetime.strptime(request.GET.get('from_date'), '%Y-%m-%d').date()
            payments_queryset = payments_queryset.filter(payment_date__gte=from_date)
        except ValueError:
            pass
    
    if request.GET.get('to_date'):
        try:
            to_date = datetime.strptime(request.GET.get('to_date'), '%Y-%m-%d').date()
            payments_queryset = payments_queryset.filter(payment_date__lte=to_date)
        except ValueError:
            pass
    
    # Calculate aggregate values
    filtered_total = payments_queryset.aggregate(total=Sum('amount_paid'))['total'] or 0
    
    # Get current month payments
    current_month = timezone.now().month
    current_year = timezone.now().year
    monthly_payments = FeePayment.objects.filter(
        payment_date__month=current_month, 
        payment_date__year=current_year
    )
    monthly_total = monthly_payments.aggregate(total=Sum('amount_paid'))['total'] or 0
    
    # Calculate average payment
    average_payment = payments_queryset.aggregate(avg=Avg('amount_paid'))['avg'] or 0
    
    # Pagination
    paginator = Paginator(payments_queryset, 10)
    page_number = request.GET.get('page', 1)
    payments = paginator.get_page(page_number)
    
    context = {
        'payments': payments,
        'all_students': all_students,
        'payment_methods': FeePayment.PAYMENT_METHOD_CHOICES,
        'filtered_total': filtered_total,
        'monthly_total': monthly_total,
        'average_payment': average_payment,
    }
    return render(request, 'finance/fee_payment_list.html', context)

@login_required
@admin_required
def add_fee_payment(request):
    """View to add a new fee payment"""
    # Initialize selected student if provided in URL
    selected_student_id = request.GET.get('student')
    selected_student = None
    
    if request.method == 'POST':
        student_id = request.POST.get('student')
        fee_structure_id = request.POST.get('fee_structure')
        amount_paid = request.POST.get('amount_paid')
        payment_date = request.POST.get('payment_date')
        payment_method = request.POST.get('payment_method')
        term = request.POST.get('term')
        remark = request.POST.get('remark', '')
        
        try:
            student = Student.objects.get(id=student_id)
            fee_structure = FeeStructure.objects.get(id=fee_structure_id)
            
            # Generate receipt number (you can customize this as needed)
            receipt_prefix = "RCPT"
            receipt_number = f"{receipt_prefix}-{timezone.now().strftime('%Y%m%d')}-{FeePayment.objects.count() + 1}"
            
            # Create payment record
            payment = FeePayment.objects.create(
                student=student,
                fee_structure=fee_structure,
                amount_paid=amount_paid,
                payment_date=payment_date or timezone.now().date(),
                payment_method=payment_method,
                receipt_number=receipt_number,
                term=term,
                remarks=remark
            )
            
            messages.success(request, f"Payment recorded successfully. Receipt Number: {receipt_number}")
            
            # Redirect to receipt view
            return redirect('finance:fee_payment_receipt', pk=payment.id)
            
        except Student.DoesNotExist:
            messages.error(request, "Student not found.")
        except FeeStructure.DoesNotExist:
            messages.error(request, "Fee structure not found.")
        except Exception as e:
            messages.error(request, f"Error recording payment: {str(e)}")
        
        return redirect('finance:add_fee_payment')
    
    # GET request - show the form
    students = Student.objects.all().select_related('user', 'grade', 'section')
    fee_structures = FeeStructure.objects.all().select_related('category', 'grade')
    
    # If student ID is provided, get the student object and filter fee structures
    if selected_student_id:
        try:
            selected_student = Student.objects.get(id=selected_student_id)
            fee_structures = fee_structures.filter(grade=selected_student.grade)
        except Student.DoesNotExist:
            pass
    
    context = {
        'students': students,
        'fee_structures': fee_structures,
        'payment_methods': FeePayment.PAYMENT_METHOD_CHOICES,
        'current_date': timezone.now().date().strftime('%Y-%m-%d'),
        'title': 'Record New Fee Payment',
        'selected_student': selected_student
    }
    return render(request, 'finance/fee_payment_form.html', context)

@login_required
@admin_required
def edit_fee_payment(request, pk):
    """View to edit a fee payment"""
    payment = get_object_or_404(FeePayment, pk=pk)
    
    if request.method == 'POST':
        amount_paid = request.POST.get('amount_paid')
        payment_method = request.POST.get('payment_method')
        payment_date = request.POST.get('payment_date')
        remark = request.POST.get('remark', '')
        
        if amount_paid and payment_method != 'PENDING':
            try:
                # Update the payment record
                payment.amount_paid = amount_paid
                payment.payment_method = payment_method
                if payment_date:
                    payment.payment_date = payment_date
                payment.remarks = remark
                payment.save()
                
                messages.success(request, f"Payment updated successfully. Receipt Number: {payment.receipt_number}")
                
                # Redirect to receipt view
                return redirect('finance:fee_payment_receipt', pk=payment.id)
            except Exception as e:
                messages.error(request, f"Error updating payment: {str(e)}")
        else:
            messages.error(request, "Amount paid and payment method are required.")
    
    # Get request - show the form
    context = {
        'payment': payment,
        'payment_methods': [pm for pm in FeePayment.PAYMENT_METHOD_CHOICES if pm[0] != 'PENDING'],
        'title': f'Update Payment for {payment.student.user.get_full_name()}',
        'fee_name': payment.fee_structure.name,
        'fee_amount': payment.fee_structure.amount,
        'current_date': timezone.now().date().strftime('%Y-%m-%d'),
    }
    return render(request, 'finance/edit_fee_payment.html', context)

@login_required
@admin_required
def delete_fee_payment(request, pk):
    """View to delete a fee payment"""
    return redirect('finance:fee_payment_list')

@login_required
def fee_payment_receipt(request, pk):
    """View to display fee payment receipt"""
    payment = get_object_or_404(FeePayment, pk=pk)
    
    # Calculate balance (if any)
    if hasattr(payment, 'fee_structure') and hasattr(payment.fee_structure, 'amount'):
        balance = payment.fee_structure.amount - payment.amount_paid
    else:
        balance = 0
    
    # Get term/academic period information
    if hasattr(payment.student, 'academic_session'):
        term = payment.student.academic_session.name
    else:
        term = "Current Term"
    
    context = {
        'payment': payment,
        'balance': balance,
        'school_name': 'School Management System',  # Replace with dynamic school info if available
        'school_logo': None,  # Replace with actual logo if available
        'school_address': '123 School Street, Education City',  # Replace with actual address
    }
    return render(request, 'finance/fee_payment_receipt.html', context)

@login_required
def student_fee_payments(request, student_id):
    """View to list fee payments for a specific student"""
    student = get_object_or_404(Student, pk=student_id)
    payments = FeePayment.objects.filter(student=student).select_related(
        'fee_structure__category'
    ).order_by('-payment_date')
    
    # Calculate total payments for this student
    total_paid = payments.aggregate(total=Sum('amount_paid'))['total'] or 0
    
    context = {
        'student': student,
        'payments': payments,
        'total_paid': total_paid
    }
    return render(request, 'finance/student_fee_payments.html', context)

@login_required
@admin_required
def export_fee_payments(request):
    """View to export fee payments as CSV"""
    import csv
    from django.http import HttpResponse
    
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="fee_payments_export.csv"'
    
    # Apply the same filters as in the fee_payment_list view
    payments_queryset = FeePayment.objects.all().select_related(
        'student__user', 'student__grade', 'student__section',
        'fee_structure__category'
    ).order_by('-payment_date')
    
    if request.GET.get('search'):
        search_query = request.GET.get('search').strip()
        payments_queryset = payments_queryset.filter(
            Q(student__user__first_name__icontains=search_query) | 
            Q(student__user__last_name__icontains=search_query) | 
            Q(student__roll_number__icontains=search_query)
        )
    
    if request.GET.get('payment_status'):
        payment_status = request.GET.get('payment_status')
        if payment_status == 'PENDING':
            payments_queryset = payments_queryset.filter(payment_method='PENDING')
        else:
            payments_queryset = payments_queryset.filter(payment_method=payment_status)
    
    if request.GET.get('from_date'):
        try:
            from_date = datetime.strptime(request.GET.get('from_date'), '%Y-%m-%d').date()
            payments_queryset = payments_queryset.filter(payment_date__gte=from_date)
        except ValueError:
            pass
    
    if request.GET.get('to_date'):
        try:
            to_date = datetime.strptime(request.GET.get('to_date'), '%Y-%m-%d').date()
            payments_queryset = payments_queryset.filter(payment_date__lte=to_date)
        except ValueError:
            pass
    
    # Create CSV writer
    writer = csv.writer(response)
    writer.writerow(['Student', 'Roll Number', 'Grade & Section', 'Amount', 'Date', 'Payment Method'])
    
    # Add data rows
    for payment in payments_queryset:
        writer.writerow([
            payment.student.user.get_full_name(),
            payment.student.roll_number,
            f"{payment.student.grade.display_name} {payment.student.section.name}",
            payment.amount_paid,
            payment.payment_date,
            payment.get_payment_method_display()
        ])
    
    return response

# Salary Structure
@login_required
@admin_required
def salary_structure_list(request):
    """View to list all salary structures"""
    salary_structures = SalaryStructure.objects.all().select_related('teacher')
    
    # Apply search filter if provided
    search_query = request.GET.get('search', '')
    if search_query:
        salary_structures = salary_structures.filter(
            Q(teacher__first_name__icontains=search_query) |
            Q(teacher__last_name__icontains=search_query) |
            Q(teacher__email__icontains=search_query)
        )
    
    context = {
        'salary_structures': salary_structures,
        'search_query': search_query
    }
    return render(request, 'finance/salary_structure_list.html', context)

@login_required
@admin_required
def add_salary_structure(request):
    """View to add a new salary structure"""
    if request.method == 'POST':
        teacher_id = request.POST.get('teacher')
        basic_salary = request.POST.get('basic_salary')
        allowances = request.POST.get('allowances', 0)
        deductions = request.POST.get('deductions', 0)
        effective_date = request.POST.get('effective_date')
        
        if teacher_id and basic_salary and effective_date:
            try:
                teacher = User.objects.get(id=teacher_id, user_type='TEACHER')
                
                # Check if this teacher already has a salary structure
                existing_structure = SalaryStructure.objects.filter(teacher=teacher).first()
                if existing_structure:
                    messages.error(request, f"Salary structure already exists for {teacher.get_full_name()}. Please edit the existing one.")
                    return redirect('finance:edit_salary_structure', pk=existing_structure.id)
                
                # Create the salary structure
                SalaryStructure.objects.create(
                    teacher=teacher,
                    basic_salary=basic_salary,
                    allowances=allowances or 0,
                    deductions=deductions or 0,
                    effective_date=effective_date or timezone.now().date()
                )
                
                messages.success(request, f"Salary structure for {teacher.get_full_name()} created successfully.")
                return redirect('finance:salary_structure_list')
                
            except User.DoesNotExist:
                messages.error(request, "Selected teacher does not exist.")
            except Exception as e:
                messages.error(request, f"Error creating salary structure: {str(e)}")
        else:
            messages.error(request, "All required fields must be filled.")
    
    # GET request
    teachers = User.objects.filter(user_type='TEACHER')
    
    # Exclude teachers who already have salary structures
    teachers_with_structures = SalaryStructure.objects.values_list('teacher_id', flat=True)
    available_teachers = teachers.exclude(id__in=teachers_with_structures)
    
    context = {
        'teachers': available_teachers,
        'title': 'Define New Salary Structure'
    }
    return render(request, 'finance/salary_structure_form.html', context)

@login_required
@admin_required
def edit_salary_structure(request, pk):
    """View to edit a salary structure"""
    salary_structure = get_object_or_404(SalaryStructure, pk=pk)
    
    if request.method == 'POST':
        basic_salary = request.POST.get('basic_salary')
        allowances = request.POST.get('allowances', 0)
        deductions = request.POST.get('deductions', 0)
        effective_date = request.POST.get('effective_date')
        
        if basic_salary and effective_date:
            try:
                # Update the salary structure
                salary_structure.basic_salary = basic_salary
                salary_structure.allowances = allowances or 0
                salary_structure.deductions = deductions or 0
                if effective_date:
                    salary_structure.effective_date = effective_date
                salary_structure.save()
                
                messages.success(request, f"Salary structure for {salary_structure.teacher.get_full_name()} updated successfully.")
                return redirect('finance:salary_structure_list')
            except Exception as e:
                messages.error(request, f"Error updating salary structure: {str(e)}")
        else:
            messages.error(request, "Basic salary and effective date are required.")
    
    context = {
        'salary_structure': salary_structure,
        'title': f'Edit Salary Structure - {salary_structure.teacher.get_full_name()}'
    }
    return render(request, 'finance/salary_structure_form.html', context)

@login_required
@admin_required
def delete_salary_structure(request, pk):
    """View to delete a salary structure"""
    salary_structure = get_object_or_404(SalaryStructure, pk=pk)
    
    if request.method == 'POST':
        teacher_name = salary_structure.teacher.get_full_name()
        
        # Check if there are any salary payments linked to this structure
        if salary_structure.payments.exists():
            messages.error(request, f"Cannot delete: There are salary payments associated with this structure.")
            return redirect('finance:salary_structure_list')
        
        # Delete the structure
        try:
            salary_structure.delete()
            messages.success(request, f"Salary structure for {teacher_name} deleted successfully.")
        except Exception as e:
            messages.error(request, f"Error deleting salary structure: {str(e)}")
    
    return redirect('finance:salary_structure_list')

# Salary Payments
@login_required
@admin_required
def salary_payment_list(request):
    """View to list all salary payments"""
    # Base queryset
    payments_queryset = SalaryPayment.objects.all().select_related(
        'teacher', 'salary_structure'
    ).order_by('-payment_date')
    
    # Apply filters
    if request.GET.get('search'):
        search_query = request.GET.get('search').strip()
        payments_queryset = payments_queryset.filter(
            Q(teacher__first_name__icontains=search_query) | 
            Q(teacher__last_name__icontains=search_query) | 
            Q(teacher__email__icontains=search_query)
        )
    
    if request.GET.get('payment_method'):
        payment_method = request.GET.get('payment_method')
        payments_queryset = payments_queryset.filter(payment_method=payment_method)
    
    if request.GET.get('payment_status'):
        is_paid = request.GET.get('payment_status') == 'paid'
        payments_queryset = payments_queryset.filter(is_paid=is_paid)
    
    if request.GET.get('from_date'):
        try:
            from_date = datetime.strptime(request.GET.get('from_date'), '%Y-%m-%d').date()
            payments_queryset = payments_queryset.filter(payment_date__gte=from_date)
        except ValueError:
            pass
    
    if request.GET.get('to_date'):
        try:
            to_date = datetime.strptime(request.GET.get('to_date'), '%Y-%m-%d').date()
            payments_queryset = payments_queryset.filter(payment_date__lte=to_date)
        except ValueError:
            pass
    
    if request.GET.get('month'):
        month = int(request.GET.get('month'))
        payments_queryset = payments_queryset.filter(month=month)
    
    if request.GET.get('year'):
        year = int(request.GET.get('year'))
        payments_queryset = payments_queryset.filter(year=year)
    
    # Calculate aggregate values
    filtered_total = sum(payment.salary_structure.net_salary for payment in payments_queryset if payment.is_paid)
    
    # Get current month payments
    current_month = timezone.now().month
    current_year = timezone.now().year
    monthly_payments = SalaryPayment.objects.filter(
        month=current_month, 
        year=current_year,
        is_paid=True
    )
    monthly_total = sum(payment.salary_structure.net_salary for payment in monthly_payments)
    
    # Pagination
    paginator = Paginator(payments_queryset, 10)
    page_number = request.GET.get('page', 1)
    payments = paginator.get_page(page_number)
    
    context = {
        'payments': payments,
        'payment_methods': SalaryPayment.PAYMENT_METHOD_CHOICES,
        'filtered_total': filtered_total,
        'monthly_total': monthly_total,
        'months': [(i, calendar.month_name[i]) for i in range(1, 13)],
        'years': range(timezone.now().year - 2, timezone.now().year + 2),
        'current_month': current_month,
        'current_year': current_year,
    }
    return render(request, 'finance/salary_payment_list.html', context)

@login_required
@admin_required
def add_salary_payment(request):
    """View to add a new salary payment"""
    # Initialize selected teacher if provided in URL
    selected_teacher_id = request.GET.get('teacher')
    selected_teacher = None
    selected_structure = None
    
    if request.method == 'POST':
        teacher_id = request.POST.get('teacher')
        month = request.POST.get('month')
        year = request.POST.get('year')
        payment_date = request.POST.get('payment_date') or timezone.now().date()
        payment_method = request.POST.get('payment_method')
        transaction_id = request.POST.get('transaction_id', '')
        remarks = request.POST.get('remarks', '')
        is_paid = request.POST.get('is_paid') == 'on'
        
        if teacher_id and month and year:
            try:
                teacher = User.objects.get(id=teacher_id, user_type='TEACHER')
                
                # Get the salary structure for this teacher
                try:
                    salary_structure = SalaryStructure.objects.get(teacher=teacher)
                except SalaryStructure.DoesNotExist:
                    messages.error(request, f"No salary structure defined for {teacher.get_full_name()}. Please define a salary structure first.")
                    return redirect('finance:add_salary_structure')
                
                # Check if a payment for this month/year already exists
                existing_payment = SalaryPayment.objects.filter(
                    teacher=teacher,
                    month=month,
                    year=year
                ).first()
                
                if existing_payment:
                    messages.error(request, f"A salary payment for {teacher.get_full_name()} for {calendar.month_name[int(month)]} {year} already exists.")
                    return redirect('finance:edit_salary_payment', pk=existing_payment.id)
                
                # Create the salary payment
                payment = SalaryPayment.objects.create(
                    teacher=teacher,
                    salary_structure=salary_structure,
                    month=month,
                    year=year,
                    payment_date=payment_date,
                    payment_method=payment_method,
                    transaction_id=transaction_id,
                    remarks=remarks,
                    is_paid=is_paid
                )
                
                messages.success(request, f"Salary payment for {teacher.get_full_name()} for {calendar.month_name[int(month)]} {year} recorded successfully.")
                return redirect('finance:salary_payment_list')
                
            except User.DoesNotExist:
                messages.error(request, "Selected teacher does not exist.")
            except Exception as e:
                messages.error(request, f"Error recording salary payment: {str(e)}")
        else:
            messages.error(request, "Teacher, month, and year are required fields.")
    
    # GET request
    teachers = User.objects.filter(user_type='TEACHER')
    
    # If teacher ID is provided, get the teacher and their salary structure
    if selected_teacher_id:
        try:
            selected_teacher = User.objects.get(id=selected_teacher_id, user_type='TEACHER')
            selected_structure = SalaryStructure.objects.filter(teacher=selected_teacher).first()
        except User.DoesNotExist:
            pass
    
    context = {
        'teachers': teachers,
        'payment_methods': SalaryPayment.PAYMENT_METHOD_CHOICES,
        'months': [(i, calendar.month_name[i]) for i in range(1, 13)],
        'years': range(timezone.now().year - 2, timezone.now().year + 3),
        'current_month': timezone.now().month,
        'current_year': timezone.now().year,
        'current_date': timezone.now().date().strftime('%Y-%m-%d'),
        'title': 'Record New Salary Payment',
        'selected_teacher': selected_teacher,
        'selected_structure': selected_structure
    }
    return render(request, 'finance/salary_payment_form.html', context)

@login_required
@admin_required
def edit_salary_payment(request, pk):
    """View to edit a salary payment"""
    payment = get_object_or_404(SalaryPayment, pk=pk)
    
    if request.method == 'POST':
        payment_date = request.POST.get('payment_date')
        payment_method = request.POST.get('payment_method')
        transaction_id = request.POST.get('transaction_id', '')
        remarks = request.POST.get('remarks', '')
        is_paid = request.POST.get('is_paid') == 'on'
        
        try:
            # Update the payment record
            if payment_date:
                payment.payment_date = payment_date
            payment.payment_method = payment_method
            payment.transaction_id = transaction_id
            payment.remarks = remarks
            payment.is_paid = is_paid
            payment.save()
            
            messages.success(request, f"Salary payment for {payment.teacher.get_full_name()} for {calendar.month_name[payment.month]} {payment.year} updated successfully.")
            return redirect('finance:salary_payment_list')
        except Exception as e:
            messages.error(request, f"Error updating salary payment: {str(e)}")
    
    context = {
        'payment': payment,
        'payment_methods': SalaryPayment.PAYMENT_METHOD_CHOICES,
        'title': f'Update Salary Payment - {payment.teacher.get_full_name()}',
        'current_date': timezone.now().date().strftime('%Y-%m-%d'),
    }
    return render(request, 'finance/edit_salary_payment.html', context)

@login_required
@admin_required
def delete_salary_payment(request, pk):
    """View to delete a salary payment"""
    payment = get_object_or_404(SalaryPayment, pk=pk)
    
    if request.method == 'POST':
        teacher_name = payment.teacher.get_full_name()
        month_year = f"{calendar.month_name[payment.month]} {payment.year}"
        
        try:
            payment.delete()
            messages.success(request, f"Salary payment for {teacher_name} for {month_year} deleted successfully.")
        except Exception as e:
            messages.error(request, f"Error deleting salary payment: {str(e)}")
    
    return redirect('finance:salary_payment_list')

@login_required
def teacher_salary_payments(request, teacher_id):
    """View to list salary payments for a specific teacher"""
    teacher = get_object_or_404(User, pk=teacher_id, user_type='TEACHER')
    payments = SalaryPayment.objects.filter(teacher=teacher).order_by('-year', '-month')
    
    # Try to get the teacher's salary structure
    salary_structure = SalaryStructure.objects.filter(teacher=teacher).first()
    
    context = {
        'teacher': teacher,
        'payments': payments,
        'salary_structure': salary_structure
    }
    return render(request, 'finance/teacher_salary_payments.html', context)

@login_required
@admin_required
def student_fee_management(request):
    """View to manage student fees with filtering options"""
    from django.db.models import Q, Sum, F, FloatField, ExpressionWrapper
    
    # Check if we need to automatically generate fees for new students
    auto_generate = request.GET.get('auto_generate') == 'true'
    
    # Get query parameters for filtering
    grade_id = request.GET.get('grade')
    section_id = request.GET.get('section')
    fee_status = request.GET.get('status')
    search_query = request.GET.get('search')
    
    # Base query - Get all students with their fee information
    students = Student.objects.all().select_related('user', 'grade', 'section')
    
    # Apply grade filter
    if grade_id:
        students = students.filter(grade_id=grade_id)
    
    # Apply section filter
    if section_id:
        students = students.filter(section_id=section_id)
    
    # Apply search filter
    if search_query:
        students = students.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(roll_number__icontains=search_query)
        )
    
    # Get all grades and sections for the filter dropdowns
    grades = Grade.objects.all()
    sections = Section.objects.all()
    
    # Prepare the student data with fee information
    student_data = []
    current_month = timezone.now().month
    current_year = timezone.now().year
    
    # Students whose fees need to be generated
    students_needing_generation = []
    
    for student in students:
        # Get all fee payments for the student
        fee_payments = FeePayment.objects.filter(student=student).select_related('fee_structure')
        
        # Calculate total fee amount and amount paid
        total_fee = sum(payment.fee_structure.amount for payment in fee_payments)
        total_paid = sum(payment.amount_paid for payment in fee_payments)
        pending_fee = total_fee - total_paid
        
        # Get current month fee status
        current_month_payments = fee_payments.filter(
            fee_structure__category__name='Monthly Fee',
            payment_date__month=current_month,
            payment_date__year=current_year
        )
        
        if current_month_payments.exists():
            current_month_fee = current_month_payments.first().fee_structure.amount
            current_month_paid = current_month_payments.aggregate(
                paid=Sum('amount_paid')
            )['paid'] or 0
            
            if current_month_paid >= current_month_fee:
                status = "Paid"
                status_class = "success"
            elif current_month_paid > 0:
                status = "Partially Paid"
                status_class = "warning"
            else:
                status = "Pending"
                status_class = "danger"
            
            needs_generation = False
        else:
            # For students with no fee records for current month,
            # automatically consider them as pending if they have been added in the current month
            current_month_fee = student.monthly_fee
            current_month_paid = 0
            
            # Check if the student was added in the current month
            student_created_date = student.user.date_joined
            if student_created_date.month == current_month and student_created_date.year == current_year:
                status = "Pending"
                status_class = "danger"
                
                # Create a note that this student's fee needs to be generated
                needs_generation = True
                students_needing_generation.append(student)
            else:
                status = "Not Generated"
                status_class = "secondary"
                needs_generation = False
        
        # Skip filtering if no status is selected or status matches
        if fee_status and status.lower() != fee_status.lower():
            continue
        
        # Add student to the data list
        student_data.append({
            'student': student,
            'total_fee': total_fee,
            'total_paid': total_paid,
            'pending_fee': pending_fee,
            'monthly_fee': student.monthly_fee,
            'current_month_paid': current_month_paid,
            'current_month_fee': current_month_fee,
            'status': status,
            'status_class': status_class,
            'needs_generation': needs_generation if 'needs_generation' in locals() else False
        })
    
    # Check if there are any students whose fees need to be generated
    needs_generation_count = len(students_needing_generation)
    
    # Auto-generate fee entries for new students if requested
    if auto_generate and needs_generation_count > 0:
        try:
            from finance.models import FeeCategory, FeeStructure, FeePayment
            import calendar
            
            # Get the current month name
            month_name = calendar.month_name[current_month]
            now = timezone.now()
            
            # Get or create the Monthly Fee category
            fee_category, _ = FeeCategory.objects.get_or_create(
                name='Monthly Fee',
                defaults={'description': 'Regular monthly fee for students'}
            )
            
            # Counter for generated entries
            generated_count = 0
            
            for student in students_needing_generation:
                # Check if a fee structure exists for this grade and create if necessary
                fee_structure, _ = FeeStructure.objects.get_or_create(
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
                
                # Double-check that we don't already have a fee entry for this month
                existing_payment = FeePayment.objects.filter(
                    student=student,
                    fee_structure__category=fee_category,
                    payment_date__month=current_month,
                    payment_date__year=current_year
                ).first()
                
                if not existing_payment:
                    # Generate receipt number
                    receipt_prefix = "RCPT"
                    receipt_number = f"{receipt_prefix}-{now.strftime('%Y%m%d')}-{FeePayment.objects.count() + 1}"
                    
                    # Create fee payment entry
                    FeePayment.objects.create(
                        student=student,
                        fee_structure=fee_structure,
                        amount_paid=0,  # Initially zero as pending
                        payment_date=now.date(),
                        payment_method='PENDING',
                        receipt_number=receipt_number,
                        remarks=f'Monthly Fee for {month_name} {current_year} (New Student - Auto-generated)'
                    )
                    generated_count += 1
            
            if generated_count > 0:
                messages.success(
                    request, 
                    f"Successfully auto-generated {generated_count} fee entries for new students."
                )
                # Redirect to refresh the page without the auto_generate parameter
                return redirect('finance:student_fee_management')
        except Exception as e:
            messages.error(request, f"Error auto-generating fees: {str(e)}")
    
    context = {
        'student_data': student_data,
        'grades': grades,
        'sections': sections,
        'selected_grade': grade_id,
        'selected_section': section_id,
        'selected_status': fee_status,
        'search_query': search_query,
        'current_month': timezone.now().strftime('%B %Y'),
        'needs_generation_count': needs_generation_count
    }
    return render(request, 'finance/student_fee_management.html', context)

@login_required
@admin_required
def generate_monthly_fees(request):
    """Generate monthly fee entries for all students"""
    if request.method == 'POST':
        try:
            from academics.models import Student
            from finance.models import FeeCategory, FeeStructure, FeePayment
            import calendar
            from datetime import date, datetime, timedelta
            
            # Get the current date
            now = timezone.now()
            current_month = now.month
            current_year = now.year
            current_month_name = calendar.month_name[current_month]
            
            # Check if we're generating for the next month (force next month generation)
            force_next_month = request.POST.get('force_next_month') == 'true'
            
            if force_next_month:
                # Calculate next month and year
                if current_month == 12:
                    target_month = 1
                    target_year = current_year + 1
                else:
                    target_month = current_month + 1
                    target_year = current_year
                target_month_name = calendar.month_name[target_month]
            else:
                # Use current month
                target_month = current_month
                target_year = current_year
                target_month_name = current_month_name
                
            # Get the 1st day of the target month for payment date
            if force_next_month:
                # Set payment date to 1st of next month
                if current_month == 12:
                    payment_date = date(current_year + 1, 1, 1)
                else:
                    payment_date = date(current_year, current_month + 1, 1)
            else:
                # Use current date for current month generation
                payment_date = now.date()
            
            # Get or create the Monthly Fee category
            fee_category, _ = FeeCategory.objects.get_or_create(
                name='Monthly Fee',
                defaults={'description': 'Regular monthly fee for students'}
            )
            
            # Get all students
            students = Student.objects.all()
            
            # Counter for new fee entries
            new_entries = 0
            updated_entries = 0
            
            for student in students:
                # Check if a fee structure exists for this grade
                fee_structure, created = FeeStructure.objects.get_or_create(
                    name=f'Monthly Fee - {student.grade.display_name}',
                    category=fee_category,
                    grade=student.grade,
                    academic_session=student.academic_session,
                    defaults={
                        'amount': student.monthly_fee,
                        'is_mandatory': True,
                        'frequency': 'MONTHLY',
                        'applicable_from': date.today()
                    }
                )
                
                # If fee structure already exists but amount is different, update it
                if not created and fee_structure.amount != student.monthly_fee:
                    fee_structure.amount = student.monthly_fee
                    fee_structure.save()
                    updated_entries += 1
                
                # Check if a fee payment for the target month already exists
                existing_payment = FeePayment.objects.filter(
                    student=student,
                    fee_structure__category=fee_category,
                    payment_date__month=target_month,
                    payment_date__year=target_year
                ).first()
                
                if not existing_payment:
                    # Get previous unpaid fees
                    previous_unpaid = FeePayment.objects.filter(
                        student=student,
                        fee_structure__category=fee_category,
                        payment_method='PENDING'
                    ).exclude(
                        payment_date__month=target_month,
                        payment_date__year=target_year
                    )
                    
                    # Calculate total pending amount
                    previous_amount = sum(
                        payment.fee_structure.amount - payment.amount_paid 
                        for payment in previous_unpaid
                    )
                    
                    # Total fee amount including previous unpaid fees
                    total_fee = student.monthly_fee + previous_amount
                    
                    # Generate receipt number
                    receipt_prefix = "RCPT"
                    receipt_number = f"{receipt_prefix}-{now.strftime('%Y%m%d')}-{FeePayment.objects.count() + 1}"
                    
                    # Create new fee payment entry
                    FeePayment.objects.create(
                        student=student,
                        fee_structure=fee_structure,
                        amount_paid=0,  # Initially zero as it's pending
                        payment_date=payment_date,
                        payment_method='PENDING',
                        receipt_number=receipt_number,
                        remarks=f'Monthly Fee for {target_month_name} {target_year}' + 
                                (f' (Includes Rs.{previous_amount} from previous months)' if previous_amount > 0 else '')
                    )
                    new_entries += 1
            
            if force_next_month:
                messages.success(
                    request, 
                    f"Successfully generated {new_entries} new fee entries for NEXT MONTH ({target_month_name} {target_year}). "
                    f"Updated {updated_entries} existing fee structures."
                )
            else:
                messages.success(
                    request, 
                    f"Successfully generated {new_entries} new fee entries for {target_month_name} {target_year}. "
                    f"Updated {updated_entries} existing fee structures."
                )
            
        except Exception as e:
            messages.error(request, f"Error generating monthly fees: {str(e)}")
        
        return redirect('finance:student_fee_management')
    
    # If not POST request, redirect to the fee management page
    return redirect('finance:student_fee_management') 