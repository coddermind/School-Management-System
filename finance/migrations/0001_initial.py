# Generated by Django 5.2 on 2025-04-10 05:19

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('academics', '0001_initial'),
        ('administration', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FeeCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'Fee Categories',
            },
        ),
        migrations.CreateModel(
            name='FeeStructure',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('frequency', models.CharField(choices=[('ANNUAL', 'Annual'), ('SEMI_ANNUAL', 'Semi-Annual'), ('QUARTERLY', 'Quarterly'), ('MONTHLY', 'Monthly'), ('ONE_TIME', 'One Time')], max_length=20)),
                ('due_date', models.DateField(blank=True, null=True)),
                ('academic_session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fee_structures', to='administration.academicsession')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fee_structures', to='finance.feecategory')),
                ('grade', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fee_structures', to='administration.grade')),
            ],
            options={
                'unique_together': {('academic_session', 'grade', 'category')},
            },
        ),
        migrations.CreateModel(
            name='FeePayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount_paid', models.DecimalField(decimal_places=2, max_digits=10)),
                ('payment_date', models.DateField(auto_now_add=True)),
                ('payment_method', models.CharField(choices=[('CASH', 'Cash'), ('BANK_TRANSFER', 'Bank Transfer'), ('CREDIT_CARD', 'Credit Card'), ('CHEQUE', 'Cheque'), ('OTHER', 'Other')], max_length=20)),
                ('transaction_id', models.CharField(blank=True, max_length=100, null=True)),
                ('receipt_number', models.CharField(max_length=50, unique=True)),
                ('remarks', models.TextField(blank=True, null=True)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fee_payments', to='academics.student')),
                ('fee_structure', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='finance.feestructure')),
            ],
        ),
        migrations.CreateModel(
            name='SalaryStructure',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('basic_salary', models.DecimalField(decimal_places=2, max_digits=10)),
                ('allowances', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('deductions', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('effective_date', models.DateField()),
                ('teacher', models.OneToOneField(limit_choices_to={'user_type': 'TEACHER'}, on_delete=django.db.models.deletion.CASCADE, related_name='salary_structure', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SalaryPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('month', models.PositiveSmallIntegerField()),
                ('year', models.PositiveIntegerField()),
                ('payment_date', models.DateField()),
                ('payment_method', models.CharField(choices=[('BANK_TRANSFER', 'Bank Transfer'), ('CHEQUE', 'Cheque'), ('CASH', 'Cash'), ('OTHER', 'Other')], max_length=20)),
                ('transaction_id', models.CharField(blank=True, max_length=100, null=True)),
                ('remarks', models.TextField(blank=True, null=True)),
                ('is_paid', models.BooleanField(default=False)),
                ('teacher', models.ForeignKey(limit_choices_to={'user_type': 'TEACHER'}, on_delete=django.db.models.deletion.CASCADE, related_name='salary_payments', to=settings.AUTH_USER_MODEL)),
                ('salary_structure', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='finance.salarystructure')),
            ],
            options={
                'unique_together': {('teacher', 'month', 'year')},
            },
        ),
    ]
