# School Management System

A comprehensive School Management System built with Django, providing separate portals for Admin, Teachers, and Students.

## Features

- **Authentication & User Roles**: Separate login for Admin, Teachers, and Students with role-based access
- **Admin Panel**: Manage school info, classrooms, subjects, academic sessions, timetables, etc.
- **Teacher Portal**: Manage attendance, assignments, marks, and communication with students
- **Student Portal**: View timetable, assignments, attendance, fees, and communication
- **Comprehensive Management**: Timetable, attendance, assignments, exams, fees, salaries, and reporting

## Installation

1. Clone the repository
```
git clone <repository-url>
cd school_management_system
```

2. Create a virtual environment and activate it
```
python -m venv venv
# On Windows
venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate
```

3. Install dependencies
```
pip install -r requirements.txt
```

4. Configure environment variables
   - Create a `.env` file in the project root and define the following variables:
     ```
     SECRET_KEY=your_secret_key
     DEBUG=True
     ```

5. Run migrations
```
python manage.py makemigrations
python manage.py migrate
```

6. Create a superuser
```
python manage.py createsuperuser
```

7. Run the development server
```
python manage.py runserver
```

8. Access the application at http://127.0.0.1:8000/

## Usage

- **Admin Access**: Navigate to `/admin/` to access the Django admin interface
- **User Portals**:
  - Admin Portal: `/administration/`
  - Teacher Portal: `/teacher/`
  - Student Portal: `/student/`

## License

This project is licensed under the MIT License - see the LICENSE file for details. 