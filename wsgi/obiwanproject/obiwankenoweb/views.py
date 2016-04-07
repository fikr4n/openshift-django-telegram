from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseForbidden
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.template.defaultfilters import date as format_date, slugify
import json
import re
import logging
import random
from datetime import datetime, timedelta
from .models import Misc, Subscriber, Location, Reminder
from iclib import salat, qibla

tgramupd_logger = logging.getLogger(__name__ + '.tgramupd')


def index(request):
    return HttpResponse('<h2>Welcome to the landing page!</h2>')


@csrf_exempt
def update(request):
    access_token = request.GET.get('auth', '')
    if request.method == 'POST' and access_token == Misc.objects.get(
            key='webservice_token').value:  # authorized
        request_body = request.body.decode()
        response = TelegramHandler(request_body).handle()
        if response:
            response_body = json.dumps(response)
            return HttpResponse(response_body, content_type='application/json')
        else:
            return HttpResponse('OK\n')
    else:
        return HttpResponseForbidden('Forbidden\n')


class TelegramHandler(object):
    _command_pattern = re.compile(r'^/([a-zA-Z0-9]+)(\w+)?(@\S*)?(.*)$', re.S)

    def __init__(self, request_body):
        self.req_str = request_body
        self.req_obj = json.loads(request_body)

    def handle(self):
        tgramupd_logger.info(self.req_str)

        message = self.req_obj.get('message')
        if message:
            chat_id = int(message['chat']['id'])
            text = message.get('text')
            if text:  # text message
                return self._handle_command(chat_id, text) or None

            new_participant = message.get('new_chat_participant')
            left_participant = message.get('left_chat_participant')
            user = left_participant or new_participant
            if user and str(user['id']) == Misc.objects.get(key='bot_user_id').value:
                # bot added or removed
                if left_participant:  # removed from group
                    Subscriber.objects.filter(pk=chat_id).update(
                        active=False)
                else:  # added to group
                    Subscriber.objects.update_or_create(pk=chat_id, defaults={'active': True, 'info': self.req_str})
        return None

    def _handle_command(self, chat_id, text):
        m = self._command_pattern.match(text)
        if m:
            reply = None
            command = m.group(1)
            arg = (m.group(2) or '').replace('_', ' ')
            recipient = m.group(3)
            arg += m.group(4)
            try:
                reply = getattr(self, '_command_' + command)(command=command,
                    recipient=recipient, arg=arg, chat_id=chat_id)
            except AttributeError:
                if recipient:  # unknown command, explicit recipient
                    reply = random.choice([
                        'Afwan, tentang perintah /%s ini, yang ditanya tidak '
                        'lebih tahu daripada yang bertanya 😕.',
                        'Mungkin yang di bawah ane lebih tahu tentang /%s gan. 👇',
                        'Afwan, ane tidak mengerti perintah /%s.',
                        ]) % command
            if reply:
                return {'method': 'sendMessage', 'chat_id': chat_id, 'text': reply}

    @staticmethod
    def _command_start(**kwargs):
        return 'بسم الله الرحمن الرحيم\nSelamat datang, ketik /help untuk bantuan.'

    @staticmethod
    def _command_help(**kwargs):
        return '''Berikan saya perintah dengan mengetik garis miring.

/jadwalshalat <LOK> - jadwal shalat hari ini untuk lokasi <LOK>
/qiblat <LOK> - arah qiblat untuk lokasi <LOK>
/agenda - tampilkan daftar agenda
/buatagenda - buat agenda baru (tampilkan cara membuat agenda)
/hapusagenda - pilih agenda untuk dihapus
/help - tampilkan teks ini'''

    @staticmethod
    def _command_qiblat(arg, **kwargs):
        location_name = arg.strip() or 'Jakarta'
        try:
            l = Location.objects.get(city__iexact=location_name)
        except (Location.DoesNotExist, Location.MultipleObjectsReturned):
            return 'Afwan, ane belum tahu lokasi "%s" ada dimana.' % location_name

        direction = qibla.direction(l.lat, l.lng)
        return '🕌 Arah qiblat untuk {} (koordinat {:n}, {:n}) adalah {:n}° dari utara (searah jarum jam).'.format(
            l.city, l.lat, l.lng, direction)

    @staticmethod
    def _command_jadwalshalat(arg, **kwargs):
        location_name = arg.strip() or 'Jakarta'
        try:
            l = Location.objects.get(city__iexact=location_name)
        except (Location.DoesNotExist, Location.MultipleObjectsReturned):
            return 'Afwan, ane belum tahu lokasi "%s" ada dimana.' % location_name

        date = timezone.now().astimezone(timezone.FixedOffset(l.tz * 60))
        t = salat.TimeCalculator().date(date). \
            location(l.lat, l.lng, l.alt, l.tz). \
            method('muhammadiyah').calculate()
        return '''🕌 Jadwal shalat {} untuk {}
(koordinat {:n}, {:n}; ketinggian {:n} mdpl; zona waktu UTC{:+n}):

Shubuh - {}
Syuruq - {}
Zhuhur - {}
Ashar - {}
Maghrib - {}
Isya - {}'''.format(date.strftime('%d-%b-%Y'), l.city, l.lat, l.lng, l.alt, l.tz,
                    *[t.get_time(i).strftime('%H:%M') for i in range(salat.N)])

    @staticmethod
    def _command_agenda(chat_id, **kwargs):
        reply = []
        for event in Reminder.objects.filter(subscriber_id=chat_id, type=Reminder.EVENT).\
                order_by('year', 'month', 'mday'):
            reply.append(event.message)
        return '\n\n'.join(reply) or 'Tidak ada agenda.'

    @staticmethod
    def _command_buatagenda(chat_id, arg, **kwargs):
        args = arg.split(maxsplit=2)
        if len(args) != 3:
            return '''\
/buatagenda <THN>-<BLN>-<TGL> <JAM>:<MNT>[<ZONA>] <JUDUL AGENDA>
<DESKRIPSI AGENDA>

Contoh zona waktu adalah +0700 untuk WIB. Jika zona waktu tidak ditentukan, dianggap +0700.
Contoh:

/buatagenda 2016-12-31 16:00 Rapat Akhir Tahun

atau:

/buatagenda 2016-12-31 16:00+0900 Rapat Akhir Tahun
Catatan: Bawa konsumsi masing-masing'''
        arg_time = args[0] + ' ' + args[1]
        try:
            t = datetime.strptime(arg_time, '%Y-%m-%d %H:%M%z')
        except ValueError:
            try:
                t = datetime.strptime(arg_time + '+0700', '%Y-%m-%d %H:%M%z')
            except ValueError:
                return 'Maaf, format waktunya salah, ane nggak ngerti.'
        reminder_t = (t.replace(hour=21, minute=0, second=0) - timedelta(days=1)).astimezone(timezone.UTC())
        message = '📅 %s\n✒ %s' % (t.strftime('%d-%b-%Y %H:%M'), args[2])
        try:
            Reminder.objects.create(year=reminder_t.year, month=reminder_t.month, mday=reminder_t.day,
                                    hour=reminder_t.hour, message=message, subscriber_id=chat_id, type='EV')
            return 'Agenda ditambahkan.'
        except IntegrityError:
            return 'Afwan, saat ini agenda cuma dapat digunakan di dalam grup.'

    @staticmethod
    def _command_hapusagenda(chat_id, arg, **kwargs):
        def from_id(x):
            return ('1' if x < 0 else '2') + str(abs(x) + 6123)

        def to_id(x):
            return (int(x[1:]) - 6123) * (-1 if x.startswith('1') else 1)

        arg = arg.strip()
        if not arg:
            reply = []
            for event in Reminder.objects.filter(subscriber_id=chat_id, type='EV').order_by('year', 'month', 'mday'):
                reply.append('/hapusagenda_%s %s' % (from_id(event.pk), slugify(event.message[:40])))
            return '\n'.join(reply) or 'Tidak ada agenda.'
        try:
            Reminder.objects.get(pk=to_id(arg), subscriber_id=chat_id).delete()
            return 'Agenda dihapus.'
        except (ValueError, Reminder.DoesNotExist):
            return 'Agenda tersebut tidak ada, ente jangan mengada-ngada.'
