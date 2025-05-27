from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    # Fee Categories
    path('fee-categories/', views.fee_category_list, name='fee_category_list'),
    path('fee-categories/add/', views.add_fee_category, name='add_fee_category'),
    path('fee-categories/edit/<int:pk>/', views.edit_fee_category, name='edit_fee_category'),
    path('fee-categories/delete/<int:pk>/', views.delete_fee_category, name='delete_fee_category'),
    
    # Fee Structure
    path('fee-structures/', views.fee_structure_list, name='fee_structure_list'),
    path('fee-structures/add/', views.add_fee_structure, name='add_fee_structure'),
    path('fee-structures/edit/<int:pk>/', views.edit_fee_structure, name='edit_fee_structure'),
    path('fee-structures/delete/<int:pk>/', views.delete_fee_structure, name='delete_fee_structure'),
    
    # Fee Payments
    path('fee-payments/', views.fee_payment_list, name='fee_payment_list'),
    path('fee-payments/add/', views.add_fee_payment, name='add_fee_payment'),
    path('fee-payments/edit/<int:pk>/', views.edit_fee_payment, name='edit_fee_payment'),
    path('fee-payments/delete/<int:pk>/', views.delete_fee_payment, name='delete_fee_payment'),
    path('fee-payments/<int:pk>/receipt/', views.fee_payment_receipt, name='fee_payment_receipt'),
    path('fee-payments/export/', views.export_fee_payments, name='export_fee_payments'),
    path('student/<int:student_id>/payments/', views.student_fee_payments, name='student_fee_payments'),
    
    # Student Fee Management
    path('student-fees/', views.student_fee_management, name='student_fee_management'),
    path('generate-monthly-fees/', views.generate_monthly_fees, name='generate_monthly_fees'),
    
    # Salary Structure
    path('salary-structures/', views.salary_structure_list, name='salary_structure_list'),
    path('salary-structures/add/', views.add_salary_structure, name='add_salary_structure'),
    path('salary-structures/edit/<int:pk>/', views.edit_salary_structure, name='edit_salary_structure'),
    path('salary-structures/delete/<int:pk>/', views.delete_salary_structure, name='delete_salary_structure'),
    
    # Salary Payments
    path('salary-payments/', views.salary_payment_list, name='salary_payment_list'),
    path('salary-payments/add/', views.add_salary_payment, name='add_salary_payment'),
    path('salary-payments/edit/<int:pk>/', views.edit_salary_payment, name='edit_salary_payment'),
    path('salary-payments/delete/<int:pk>/', views.delete_salary_payment, name='delete_salary_payment'),
    path('teacher/<int:teacher_id>/salary-payments/', views.teacher_salary_payments, name='teacher_salary_payments'),
] 