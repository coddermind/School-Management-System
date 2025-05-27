from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from administration.models import Grade, Section, Subject, ClassSubject
from academics.models import Timetable
from django.db.models import Q

@login_required
@require_GET
def available_subjects_api(request):
    """API endpoint to get subjects available for scheduling in a timetable"""
    grade_id = request.GET.get('grade_id')
    section_id = request.GET.get('section_id')
    day_id = request.GET.get('day_id')
    time_slot_id = request.GET.get('time_slot_id')
    academic_session_id = request.GET.get('academic_session_id')
    
    # Validate required parameters
    if not all([grade_id, day_id, time_slot_id, academic_session_id]):
        return JsonResponse({
            'status': 'error',
            'message': 'Missing required parameters',
            'subjects': []
        })
    
    try:
        # Get all subjects for this grade
        grade = Grade.objects.get(id=grade_id)
        class_subjects = ClassSubject.objects.filter(grade=grade).select_related('subject', 'teacher')
        
        # Find existing timetable entries for this grade, section, day and time slot
        existing_entries = Timetable.objects.filter(
            grade_id=grade_id,
            day_id=day_id,
            time_slot_id=time_slot_id,
            academic_session_id=academic_session_id
        )
        
        if section_id:
            existing_entries = existing_entries.filter(section_id=section_id)
        
        # Get scheduled subjects for this slot
        scheduled_subjects = list(existing_entries.values_list('subject_id', flat=True))
        
        # Find teachers who are already teaching during this time slot
        busy_teachers = Timetable.objects.filter(
            day_id=day_id,
            time_slot_id=time_slot_id,
            academic_session_id=academic_session_id
        ).exclude(
            Q(grade_id=grade_id) & Q(section_id=section_id) if section_id else Q(grade_id=grade_id)
        ).values_list('teacher_id', 'grade__display_name', 'section__name')
        
        # Create a dictionary of busy teachers with their schedule info
        teachers_busy = {}
        for teacher_id, grade_name, section_name in busy_teachers:
            if teacher_id in teachers_busy:
                teachers_busy[teacher_id].append(f"{grade_name} {section_name}")
            else:
                teachers_busy[teacher_id] = [f"{grade_name} {section_name}"]
        
        # Prepare subject list with availability info
        subjects = []
        for cs in class_subjects:
            subject_data = {
                'id': cs.subject.id,
                'name': cs.subject.name,
                'is_available': True,
                'conflict_reason': None
            }
            
            # Add teacher info if available
            if cs.teacher:
                subject_data['teacher_name'] = cs.teacher.get_full_name()
                subject_data['teacher_id'] = cs.teacher.id
                
                # Check if teacher is busy
                if cs.teacher.id in teachers_busy:
                    subject_data['is_available'] = False
                    subject_data['conflict_reason'] = f"Teacher already teaching {', '.join(teachers_busy[cs.teacher.id])}"
            
            # Check if subject is already scheduled
            if cs.subject.id in scheduled_subjects:
                subject_data['is_available'] = False
                subject_data['conflict_reason'] = "Already scheduled for this time slot"
            
            subjects.append(subject_data)
        
        return JsonResponse({
            'status': 'success',
            'subjects': subjects,
            'scheduled_subjects': scheduled_subjects,
            'teachers_busy': teachers_busy
        })
        
    except (Grade.DoesNotExist, ValueError) as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'subjects': []
        }) 