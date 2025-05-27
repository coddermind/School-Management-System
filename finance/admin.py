from django.contrib import admin
from .models import FeeCategory, FeeStructure, FeePayment, SalaryStructure, SalaryPayment

@admin.register(FeeCategory)
class FeeCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('academic_session', 'grade', 'category', 'amount', 'frequency', 'due_date')
    list_filter = ('academic_session', 'grade', 'category', 'frequency')
    search_fields = ('category__name', 'grade__name')

@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'fee_structure', 'amount_paid', 'payment_date', 'payment_method', 'receipt_number')
    list_filter = ('payment_date', 'payment_method', 'fee_structure__category')
    search_fields = ('student__user__email', 'student__user__first_name', 'student__user__last_name', 'receipt_number')
    date_hierarchy = 'payment_date'

@admin.register(SalaryStructure)
class SalaryStructureAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'basic_salary', 'allowances', 'deductions', 'net_salary', 'effective_date')
    search_fields = ('teacher__email', 'teacher__first_name', 'teacher__last_name')
    list_filter = ('effective_date',)

@admin.register(SalaryPayment)
class SalaryPaymentAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'month', 'year', 'payment_date', 'payment_method', 'is_paid')
    list_filter = ('month', 'year', 'payment_date', 'payment_method', 'is_paid')
    search_fields = ('teacher__email', 'teacher__first_name', 'teacher__last_name')
    date_hierarchy = 'payment_date'
