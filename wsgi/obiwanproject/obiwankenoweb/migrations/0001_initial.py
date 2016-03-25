# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Misc',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('key', models.CharField(unique=True, max_length=32)),
                ('value', models.CharField(blank=True, max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='Reminder',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('year', models.SmallIntegerField(null=True, blank=True)),
                ('month', models.SmallIntegerField(null=True, blank=True)),
                ('mday', models.SmallIntegerField(null=True, blank=True)),
                ('wday', models.SmallIntegerField(null=True, blank=True)),
                ('hour', models.SmallIntegerField(default=0)),
                ('message', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Subscriber',
            fields=[
                ('id', models.BigIntegerField(serialize=False, primary_key=True)),
                ('info', models.TextField()),
                ('active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='TelegramUpdate',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('update_id', models.BigIntegerField()),
                ('time_received', models.DateTimeField()),
                ('content', models.TextField()),
            ],
        ),
        migrations.AddField(
            model_name='reminder',
            name='subscriber',
            field=models.ForeignKey(to='obiwankenoweb.Subscriber'),
        ),
    ]
