# Getting Started with the School Management System

This guide will help you set up and run the School Management System project.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## Installation

1. Clone the repository (if you haven't already):
   ```
   git clone <repository-url>
   cd school_management_system
   ```

2. Create a virtual environment and activate it:
   ```
   # On Windows
   python -m venv venv
   venv\Scripts\activate

   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Apply migrations to set up the database:
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```

5. Create a superuser for admin access:
   ```
   python manage.py createsuperuser
   ```

## Populating Demo Data

To quickly set up the system with demo data, run:

```
python manage.py create_demo_data
```

This will create:
- Admin user (email: admin@school.com, password: admin123)
- Teachers (email: teacher1@school.com through teacher10@school.com, password: teacher123)
- Students (email: student1@school.com through student50@school.com, password: student123)
- School settings
- Academic sessions
- Grades and sections
- Subjects
- Classrooms
- Time slots and weekdays
- Exam types

## Running the Server

Start the development server:

```
python manage.py runserver
```

The application will be available at http://127.0.0.1:8000/

## Accessing the System

- Admin Panel: http://127.0.0.1:8000/admin/
- School Management System:
  - Login: http://127.0.0.1:8000/accounts/login/
  - Admin Dashboard: http://127.0.0.1:8000/accounts/admin/dashboard/
  - Teacher Dashboard: http://127.0.0.1:8000/accounts/teacher/dashboard/
  - Student Dashboard: http://127.0.0.1:8000/accounts/student/dashboard/

## API Endpoints

The system provides RESTful API endpoints:

- Login: POST http://127.0.0.1:8000/accounts/api/login/
- Logout: POST http://127.0.0.1:8000/accounts/api/logout/
- User Profile: GET/PUT http://127.0.0.1:8000/accounts/api/user/
- Change Password: POST http://127.0.0.1:8000/accounts/api/change-password/
- Student Profile: GET/PUT http://127.0.0.1:8000/accounts/api/student-profile/
- Teacher Profile: GET/PUT http://127.0.0.1:8000/accounts/api/teacher-profile/

## Next Steps

After setting up the system, you can:

1. Customize school settings through the admin panel
2. Add more users, classes, subjects, etc.
3. Create timetables, assignments, exams
4. Record attendance, marks, fees, etc.

## Troubleshooting

If you encounter any issues:

1. Ensure all migrations are applied: `python manage.py migrate`
2. Check for any error messages in the console
3. Verify database settings in `settings.py`
4. Ensure all dependencies are installed correctly

## Customization

To customize the system:

1. Modify templates in the `templates` directory
2. Edit static files in the `static` directory
3. Add or modify models, views, and URLs as needed