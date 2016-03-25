# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('obiwankenoweb', '0002_location'),
    ]

    operations = [
        migrations.DeleteModel(
            name='TelegramUpdate',
        ),
    ]
