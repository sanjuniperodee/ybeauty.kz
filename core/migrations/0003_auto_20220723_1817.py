# Generated by Django 2.2 on 2022-07-23 12:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_item_firm'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='description1',
            field=models.TextField(default='NONE'),
        ),
        migrations.AddField(
            model_name='item',
            name='description2',
            field=models.TextField(default='NONE'),
        ),
        migrations.AlterField(
            model_name='item',
            name='description',
            field=models.TextField(default='NONE'),
        ),
    ]
