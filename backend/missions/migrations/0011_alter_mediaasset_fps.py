# Generated by Django 5.2.4 on 2025-07-14 00:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('missions', '0010_alter_mission_location'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mediaasset',
            name='fps',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
    ]
