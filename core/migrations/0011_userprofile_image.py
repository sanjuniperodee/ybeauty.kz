# Generated by Django 2.2 on 2022-10-09 17:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_auto_20221009_2309'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='image',
            field=models.ImageField(default=None, upload_to=''),
        ),
    ]
