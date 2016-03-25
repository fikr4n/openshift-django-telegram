from django.db import models
from django.template.defaultfilters import truncatechars, default_if_none as defnone
import json


class Subscriber(models.Model):
    id = models.BigIntegerField(primary_key=True)
    info = models.TextField()
    active = models.BooleanField(default=True)

    def chat_title(self):
        try:
            req_obj = json.loads(self.info)
            return req_obj['message']['chat']['title']
        except Exception:
            return None

    def __str__(self):
        return '%s (%s)' % (self.chat_id, self.chat_title() or '<untitled>')

    @property
    def chat_id(self):
        return self.id


class Reminder(models.Model):
    DEFAULT = 'DF'
    EVENT = 'EV'
    TYPE_CHOICES = (
        (DEFAULT, 'Default'),
        (EVENT, 'Event'),
    )
    year = models.SmallIntegerField(null=True, blank=True)
    month = models.SmallIntegerField(null=True, blank=True)
    mday = models.SmallIntegerField(null=True, blank=True)
    wday = models.SmallIntegerField(null=True, blank=True)
    hour = models.SmallIntegerField(default=0)
    message = models.TextField()
    subscriber = models.ForeignKey(Subscriber, on_delete=models.CASCADE)
    type = models.CharField(max_length=2, choices=TYPE_CHOICES, default=DEFAULT)

    def message_preview(self):
        return truncatechars(self.message, 80)

    def __str__(self):
        return '%s-%s-%s d%s %02d:00 %s' % (defnone(self.year, '*'),
            defnone(self.month, '*'), defnone(self.mday, '*'),
            defnone(self.wday, '*'), int(self.hour), truncatechars(self.message, 16))


class Misc(models.Model):
    key = models.CharField(max_length=32, unique=True)
    value = models.CharField(max_length=256, blank=True)

    def __str__(self):
        return self.key


class Location(models.Model):
    lat = models.FloatField()
    lng = models.FloatField()
    alt = models.FloatField()
    tz = models.FloatField()
    city = models.CharField(max_length=64)

