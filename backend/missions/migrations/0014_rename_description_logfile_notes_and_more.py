# Generated by Django 5.2.4 on 2025-07-14 14:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('missions', '0013_rename_description_mission_notes_mission_cloud_cover_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='logfile',
            old_name='description',
            new_name='notes',
        ),
        migrations.AddField(
            model_name='logfile',
            name='already_parsed',
            field=models.BooleanField(default=False),
        ),
    ]
