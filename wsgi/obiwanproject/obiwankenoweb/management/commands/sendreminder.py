import os
from datetime import datetime, timedelta
from urllib import request, parse
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from obiwankenoweb.models import Reminder, Subscriber, Misc


class Command(BaseCommand):
    help = 'Send reminders which match current time'
    
    def add_argument(self, parser):
        pass
    
    def handle(self, *args, **options):
        time_format = '%Y-%m-%d %H'
        AN_HOUR = timedelta(hours=1)
        
        now_t = datetime.utcnow()
        if now_t.minute > 50:  # translate forward if it's nearly next hour
            now_t += AN_HOUR
        now_t = now_t.replace(minute=0, second=0, microsecond=0)
        try:
            last_t = datetime.strptime(Misc.objects.get(key='last_reminder_time').value, time_format)
            next_t = max(now_t - 3 * AN_HOUR, last_t + AN_HOUR)
        except (ValueError, Misc.DoesNotExist):
            next_t = now_t
        
        while next_t <= now_t:
            self._send_reminder(next_t)
            next_t += AN_HOUR
        Misc.objects.update_or_create(key='last_reminder_time', defaults={
            'value': now_t.strftime(time_format)})
    
    def _send_reminder(self, t):
        reminders = Reminder.objects.filter(
            Q(year=t.year) | Q(year__isnull=True),
            Q(month=t.month) | Q(month__isnull=True),
            Q(mday=t.day) | Q(mday__isnull=True),
            Q(wday=t.isoweekday() % 7) | Q(wday__isnull=True),
            hour=t.hour,
            subscriber__active=True)
        try:
            for i in reminders:
                msg = i.message
                if i.type == Reminder.EVENT:
                    msg = '⏰ Agenda besok!!!\n\n' + msg
                self._send_message(i.subscriber.chat_id, msg)
        except Exception as e:
            raise CommandError('fail to send message: ' + repr(e))
    
    def _send_message(self, chat_id, message):
        token = os.environ['OBIWAN_TELEGRAM_TOKEN']
        body = parse.urlencode({'chat_id': chat_id, 'text': message}, encoding='utf-8')
        response = request.urlopen('https://api.telegram.org/bot%s/sendMessage' % token, data=body.encode())
        self.stdout.write('%s: %s...' % (chat_id, response.read()[:16].decode()))

