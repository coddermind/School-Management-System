from django.db import models
from django.conf import settings
from administration.models import Grade, Section

class Announcement(models.Model):
    """Model for Announcements"""
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='announcements')
    is_active = models.BooleanField(default=True)
    
    # Target audience
    for_students = models.BooleanField(default=True)
    for_teachers = models.BooleanField(default=True)
    for_admins = models.BooleanField(default=True)
    
    # Optional: Specific grade/section targeting
    specific_grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='announcements', 
                                      null=True, blank=True)
    specific_section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='announcements', 
                                        null=True, blank=True)
    
    # Optional: File attachment
    attachment = models.FileField(upload_to='announcements/', null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class Message(models.Model):
    """Model for private messages between users"""
    
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=200, null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    attachment = models.FileField(upload_to='messages/', null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Message from {self.sender.get_full_name()} to {self.receiver.get_full_name()}"

class Notification(models.Model):
    """Model for system notifications"""
    
    NOTIFICATION_TYPES = [
        ('INFO', 'Information'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('SUCCESS', 'Success'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=100)
    message = models.TextField()
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES, default='INFO')
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    link = models.URLField(null=True, blank=True)  # Optional link to redirect to
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.get_full_name()}"

class Event(models.Model):
    """Model for school events"""
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=200, null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_events')
    is_active = models.BooleanField(default=True)
    
    # Target audience
    for_students = models.BooleanField(default=True)
    for_teachers = models.BooleanField(default=True)
    for_parents = models.BooleanField(default=True)
    
    # Optional: Specific grade/section targeting
    specific_grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='events', 
                                      null=True, blank=True)
    specific_section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='events', 
                                        null=True, blank=True)
    
    # Optional: Image
    image = models.ImageField(upload_to='events/', null=True, blank=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return self.title
