from django.contrib import admin
from .models import Announcement, Message, Notification, Event

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at', 'is_active', 'for_students', 'for_teachers', 'for_admins')
    list_filter = ('is_active', 'for_students', 'for_teachers', 'for_admins', 'created_at')
    search_fields = ('title', 'content', 'author__email')
    date_hierarchy = 'created_at'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'subject', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('sender__email', 'receiver__email', 'subject', 'content')
    date_hierarchy = 'created_at'

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'created_at', 'is_read')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__email', 'title', 'message')
    date_hierarchy = 'created_at'

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'location', 'created_by', 'is_active')
    list_filter = ('is_active', 'for_students', 'for_teachers', 'for_parents', 'start_date')
    search_fields = ('title', 'description', 'location')
    date_hierarchy = 'start_date'
