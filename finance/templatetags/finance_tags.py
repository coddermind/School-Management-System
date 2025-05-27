from django import template

register = template.Library()

@register.filter
def count_by_status(student_data, status):
    """Count student records by status"""
    count = 0
    for data in student_data:
        if data['status'] == status:
            count += 1
    return count

@register.filter
def sum_pending_fees(student_data):
    """Sum all pending fees"""
    total = 0
    for data in student_data:
        total += data['pending_fee']
    return total 