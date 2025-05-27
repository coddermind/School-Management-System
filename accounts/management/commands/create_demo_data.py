import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from accounts.models import User, StudentProfile, TeacherProfile
from administration.models import SchoolSettings, AcademicSession, Grade, Section, Subject, ClassSubject, ClassRoom
from academics.models import Student, TimeSlot, Weekday, Timetable, ExamType

class Command(BaseCommand):
    help = 'Creates demo data for the School Management System'
    
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Creating demo data...'))
        
        # Create admin user
        admin_user, created = User.objects.get_or_create(
            email='admin@school.com',
            defaults={
                'first_name': 'Admin',
                'last_name': 'User',
                'user_type': 'ADMIN',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Admin user created'))
        
        # Create school settings
        school_settings, created = SchoolSettings.objects.get_or_create(
            school_name='Demo School',
            defaults={
                'address': '123 School Street, City, State, 12345',
                'phone': '+1234567890',
                'email': 'contact@school.com',
                'website': 'https://school.com',
                'school_description': 'A demo school for the School Management System',
                'established_year': 2000,
                'principal_name': 'John Doe',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('School settings created'))
        
        # Create academic session
        current_year = date.today().year
        academic_session, created = AcademicSession.objects.get_or_create(
            name=f'{current_year}-{current_year+1}',
            defaults={
                'start_date': date(current_year, 7, 1),
                'end_date': date(current_year+1, 6, 30),
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Academic session created'))
        
        # Create grades
        grades = []
        for i in range(1, 13):
            grade, created = Grade.objects.get_or_create(
                name=f'Grade {i}',
                display_name=f'Grade {i}'
            )
            grades.append(grade)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Grade {i} created'))
        
        # Create sections
        sections = []
        section_names = ['A', 'B', 'C']
        for grade in grades:
            for section_name in section_names:
                section, created = Section.objects.get_or_create(
                    name=section_name,
                    grade=grade
                )
                sections.append(section)
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Section {section.name} created for {grade.name}'))
        
        # Create subjects
        subjects = []
        subject_data = [
            ('MATH', 'Mathematics'),
            ('ENG', 'English'),
            ('SCI', 'Science'),
            ('HIS', 'History'),
            ('GEO', 'Geography'),
            ('PHY', 'Physics'),
            ('CHEM', 'Chemistry'),
            ('BIO', 'Biology'),
            ('CS', 'Computer Science'),
            ('ART', 'Arts'),
            ('MUS', 'Music'),
            ('PE', 'Physical Education'),
        ]
        for code, name in subject_data:
            subject, created = Subject.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'description': f'This is the {name} subject',
                }
            )
            subjects.append(subject)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Subject {name} created'))
        
        # Create classrooms
        classrooms = []
        for i in range(1, 21):
            classroom, created = ClassRoom.objects.get_or_create(
                name=f'Room {i}',
                defaults={
                    'capacity': random.randint(30, 50),
                    'description': f'Classroom {i}',
                }
            )
            classrooms.append(classroom)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Classroom {classroom.name} created'))
        
        # Create teacher users
        teachers = []
        for i in range(1, 11):
            teacher, created = User.objects.get_or_create(
                email=f'teacher{i}@school.com',
                defaults={
                    'first_name': f'Teacher{i}',
                    'last_name': 'Surname',
                    'user_type': 'TEACHER',
                }
            )
            if created:
                teacher.set_password('teacher123')
                teacher.save()
                self.stdout.write(self.style.SUCCESS(f'Teacher {teacher.email} created'))
            
            teacher_profile, created = TeacherProfile.objects.get_or_create(
                user=teacher,
                defaults={
                    'employee_id': f'EMP{i:03d}',
                    'qualification': random.choice(['B.Ed.', 'M.Ed.', 'Ph.D.']),
                    'experience': random.randint(1, 15),
                    'joining_date': date.today() - timedelta(days=random.randint(30, 1000)),
                }
            )
            teachers.append(teacher)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Teacher profile for {teacher.email} created'))
        
        # Create class-subject-teacher assignments
        for grade in grades:
            for subject in random.sample(subjects, min(6, len(subjects))):
                class_subject, created = ClassSubject.objects.get_or_create(
                    grade=grade,
                    subject=subject,
                    defaults={
                        'teacher': random.choice(teachers),
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Class subject {grade.name} - {subject.name} created'))
        
        # Create student users
        students = []
        for i in range(1, 51):
            student, created = User.objects.get_or_create(
                email=f'student{i}@school.com',
                defaults={
                    'first_name': f'Student{i}',
                    'last_name': 'Surname',
                    'user_type': 'STUDENT',
                }
            )
            if created:
                student.set_password('student123')
                student.save()
                self.stdout.write(self.style.SUCCESS(f'Student {student.email} created'))
            
            student_profile, created = StudentProfile.objects.get_or_create(
                user=student,
                defaults={
                    'admission_number': f'ADM{i:03d}',
                    'parent_name': 'Parent Name',
                    'parent_phone': f'+123456789{i%10}',
                    'parent_email': f'parent{i}@example.com',
                    'blood_group': random.choice(['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']),
                    'emergency_contact': f'+987654321{i%10}',
                }
            )
            
            # Assign student to a class
            section = random.choice(sections)
            student_record, created = Student.objects.get_or_create(
                user=student,
                defaults={
                    'academic_session': academic_session,
                    'grade': section.grade,
                    'section': section,
                    'roll_number': i,
                }
            )
            students.append(student)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Student {student.email} assigned to {section.grade.name} {section.name}'))
        
        # Create time slots
        time_slots = []
        time_slot_data = [
            ('Period 1', '08:00', '08:45'),
            ('Period 2', '08:45', '09:30'),
            ('Period 3', '09:30', '10:15'),
            ('Break', '10:15', '10:30'),
            ('Period 4', '10:30', '11:15'),
            ('Period 5', '11:15', '12:00'),
            ('Lunch', '12:00', '12:45'),
            ('Period 6', '12:45', '13:30'),
            ('Period 7', '13:30', '14:15'),
            ('Period 8', '14:15', '15:00'),
        ]
        for name, start_time, end_time in time_slot_data:
            time_slot, created = TimeSlot.objects.get_or_create(
                name=name,
                defaults={
                    'start_time': start_time,
                    'end_time': end_time,
                }
            )
            time_slots.append(time_slot)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Time slot {name} created'))
        
        # Create weekdays
        weekdays = []
        for i in range(7):
            weekday, created = Weekday.objects.get_or_create(day=i)
            weekdays.append(weekday)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Weekday {weekday.get_day_display()} created'))
        
        # Create exam types
        exam_types = []
        exam_type_data = [
            ('Mid-Term', 'Mid-term examination'),
            ('Final', 'Final examination'),
            ('Quiz', 'Regular class quiz'),
            ('Assignment', 'Take-home assignment'),
        ]
        for name, description in exam_type_data:
            exam_type, created = ExamType.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
                }
            )
            exam_types.append(exam_type)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Exam type {name} created'))
        
        self.stdout.write(self.style.SUCCESS('Demo data creation completed!')) 