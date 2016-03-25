# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('obiwankenoweb', '0003_delete_telegramupdate'),
    ]

    operations = [
        migrations.AddField(
            model_name='reminder',
            name='type',
            field=models.CharField(max_length=2, choices=[('DF', 'Default'), ('EV', 'Event')], default='DF'),
        ),
    ]
