from django.contrib import admin
from .models import *


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ['id', 'subscriber', 'type', 'year', 'month', 'mday', 'wday', 'hour', 'message_preview']


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ['chat_id', 'active', 'chat_title']


@admin.register(Misc)
class MiscAdmin(admin.ModelAdmin):
    list_display = ['key', 'value']


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['city', 'lat', 'lng', 'alt', 'tz']

