import math
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseForbidden
from django.utils import timezone
from django.utils.formats import date_format, time_format, number_format, get_format_lazy
from django.views.decorators.csrf import csrf_exempt
from django.template.defaultfilters import slugify
import json
import re
import logging
import random
from datetime import datetime, timedelta
from .models import Misc, Subscriber, Location, Reminder
from iclib import salat, qibla

tgramupd_logger = logging.getLogger(__name__ + '.tgramupd')


def timezone_format(x):
    f, i = math.modf(x)
    return 'UTC%+03.0f%02.0f' % (i, abs(f * 60))


def parse_date_time(x):
    try:
        tzinfo = datetime.strptime(x[-5:], '%z').tzinfo
        x = x[:-5].rstrip()
    except ValueError:
        tzinfo = timezone.get_default_timezone()

    for i in get_format_lazy('DATETIME_INPUT_FORMATS'):
        try:
            return datetime.strptime(x, i).replace(tzinfo=tzinfo)
        except ValueError:
            pass


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
                reply = getattr(self, '_command_' + command)(command=command, recipient=recipient, arg=arg,
                                                             chat_id=chat_id)
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
        return '🕌 Arah qiblat untuk {} (koordinat {}, {}) adalah {}° dari utara (searah jarum jam).'.format(
            l.city, number_format(l.lat), number_format(l.lng), number_format(direction, 2))

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
(koordinat {}, {}; ketinggian {} mdpl; zona waktu {}):

Shubuh - {}
Syuruq - {}
Zhuhur - {}
Ashar - {}
Maghrib - {}
Isya - {}'''.format(date_format(date), l.city, number_format(l.lat), number_format(l.lng), number_format(l.alt, -2),
                    timezone_format(l.tz),
                    *[time_format(t.get_time(i)) for i in range(salat.N)])

    @staticmethod
    def _command_agenda(chat_id, **kwargs):
        reply = []
        for event in Reminder.objects.filter(subscriber_id=chat_id, type=Reminder.EVENT).\
                order_by('year', 'month', 'mday'):
            reply.append(event.message)
        return '\n\n'.join(reply) or 'Tidak ada agenda.'

    @staticmethod
    def _command_buatagenda(chat_id, arg, **kwargs):
        args = arg.split('\n', maxsplit=1)
        if len(args) != 2:
            return '''\
/buatagenda <WAKTU>[<ZONA_WAKTU>]
<JUDUL AGENDA>
[<DESKRIPSI AGENDA>]

Jika zona waktu tidak ditentukan, dianggap +0700, wakni WIB.
Contoh:

/buatagenda 31-12-2016 16.00
Rapat Akhir Tahun (format Indonesia)

/buatagenda 2016-12-31 16:00
Rapat Akhir Tahun (format waktu ISO)

/buatagenda 31-12-2016 16.00+0900
Rapat Akhir Tahun (zona WIT)
Catatan tambahan: Bawa konsumsi masing-masing'''

        arg_time, arg_text = args
        t = parse_date_time(arg_time.strip())
        if not t:
            return 'Maaf, format waktunya salah, ane nggak ngerti.'
        reminder_t = (t.replace(hour=21, minute=0, second=0) - timedelta(days=1)).astimezone(timezone.UTC())
        message = '📅 %s %s\n✒ %s' % (date_format(t), time_format(t), arg_text)
        try:
            Reminder.objects.create(year=reminder_t.year, month=reminder_t.month, mday=reminder_t.day,
                                    hour=reminder_t.hour, message=message, subscriber_id=chat_id, type=Reminder.EVENT)
            return 'Agenda ditambahkan.'
        except IntegrityError:
            return 'Afwan, saat ini agenda cuma dapat digunakan di dalam grup.'

    @staticmethod
    def _command_hapusagenda(chat_id, arg, **kwargs):
        magic_nonnegative = '2'
        magic_negative = '1'
        magic_init = 6123

        def from_id(x):
            return (magic_negative if x < 0 else magic_nonnegative) + str(abs(x) + magic_init)

        def to_id(x):
            return (int(x[1:]) - magic_init) * (-1 if x.startswith(magic_negative) else 1)

        arg = arg.strip()
        if not arg:
            reply = []
            for event in Reminder.objects.filter(subscriber_id=chat_id, type=Reminder.EVENT).\
                    order_by('year', 'month', 'mday'):
                reply.append('/hapusagenda_%s %s' % (from_id(event.pk), slugify(event.message[:40])))
            return '\n'.join(reply) or 'Tidak ada agenda.'
        try:
            Reminder.objects.get(pk=to_id(arg), subscriber_id=chat_id).delete()
            return 'Agenda dihapus.'
        except (ValueError, Reminder.DoesNotExist):
            return 'Agenda tersebut tidak ada, ente jangan mengada-ngada.'
