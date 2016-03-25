# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('obiwankenoweb', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('lat', models.FloatField()),
                ('lng', models.FloatField()),
                ('alt', models.FloatField()),
                ('tz', models.FloatField()),
                ('city', models.CharField(max_length=64)),
            ],
        ),
    ]
