from django.db import models
from django.conf import settings
from academics.models import Student
from administration.models import AcademicSession, Grade

class FeeCategory(models.Model):
    """Model for Fee Categories (e.g., Tuition Fee, Library Fee, etc.)"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    
    class Meta:
        verbose_name_plural = 'Fee Categories'
    
    def __str__(self):
        return self.name

class FeeStructure(models.Model):
    """Model for Fee Structure"""
    
    FREQUENCY_CHOICES = [
        ('ANNUAL', 'Annual'),
        ('SEMI_ANNUAL', 'Semi-Annual'),
        ('QUARTERLY', 'Quarterly'),
        ('MONTHLY', 'Monthly'),
        ('ONE_TIME', 'One Time'),
    ]
    
    name = models.CharField(max_length=100)
    academic_session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name='fee_structures')
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='fee_structures')
    category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE, related_name='fee_structures')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='ANNUAL')
    due_date = models.DateField(null=True, blank=True)  # For one-time fees
    is_mandatory = models.BooleanField(default=True)
    description = models.TextField(null=True, blank=True)
    applicable_from = models.DateField(auto_now_add=True)
    
    class Meta:
        unique_together = ['academic_session', 'grade', 'category']
    
    def __str__(self):
        return f"{self.name} - {self.category.name} - {self.grade.display_name}"

class FeePayment(models.Model):
    """Model for Fee Payments"""
    
    PAYMENT_METHOD_CHOICES = [
        ('PENDING', 'Pending Payment'),
        ('CASH', 'Cash'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CREDIT_CARD', 'Credit Card'),
        ('CHEQUE', 'Cheque'),
        ('OTHER', 'Other'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_payments')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name='payments')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    receipt_number = models.CharField(max_length=50, unique=True)
    remarks = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"Receipt #{self.receipt_number} - {self.student.user.get_full_name()} - {self.fee_structure.category.name}"

class SalaryStructure(models.Model):
    """Model for Salary Structure of Teachers"""
    
    teacher = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                                   related_name='salary_structure', limit_choices_to={'user_type': 'TEACHER'})
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    effective_date = models.DateField()
    
    def __str__(self):
        return f"Salary Structure: {self.teacher.get_full_name()}"
    
    @property
    def net_salary(self):
        return self.basic_salary + self.allowances - self.deductions

class SalaryPayment(models.Model):
    """Model for Salary Payments"""
    
    PAYMENT_METHOD_CHOICES = [
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CHEQUE', 'Cheque'),
        ('CASH', 'Cash'),
        ('OTHER', 'Other'),
    ]
    
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                               related_name='salary_payments', limit_choices_to={'user_type': 'TEACHER'})
    salary_structure = models.ForeignKey(SalaryStructure, on_delete=models.CASCADE, related_name='payments')
    month = models.PositiveSmallIntegerField()  # 1-12 for January-December
    year = models.PositiveIntegerField()
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['teacher', 'month', 'year']
    
    def __str__(self):
        month_name = {
            1: 'January', 2: 'February', 3: 'March', 4: 'April',
            5: 'May', 6: 'June', 7: 'July', 8: 'August',
            9: 'September', 10: 'October', 11: 'November', 12: 'December'
        }
        return f"Salary: {self.teacher.get_full_name()} - {month_name[self.month]} {self.year}"
