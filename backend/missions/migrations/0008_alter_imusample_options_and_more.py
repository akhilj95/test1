# Generated by Django 5.2.4 on 2025-07-13 21:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('missions', '0007_imusample_magnetometersample_pressuresample'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='imusample',
            options={'ordering': ['timestamp']},
        ),
        migrations.AlterModelOptions(
            name='magnetometersample',
            options={'ordering': ['timestamp']},
        ),
        migrations.AlterModelOptions(
            name='pressuresample',
            options={'ordering': ['timestamp']},
        ),
        migrations.RemoveIndex(
            model_name='imusample',
            name='missions_im_log_fil_7eaf5f_idx',
        ),
        migrations.RemoveIndex(
            model_name='magnetometersample',
            name='missions_ma_log_fil_67cc77_idx',
        ),
        migrations.RemoveIndex(
            model_name='pressuresample',
            name='missions_pr_log_fil_f48288_idx',
        ),
        migrations.AlterField(
            model_name='imusample',
            name='deployment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s', to='missions.sensordeployment'),
        ),
        migrations.AlterField(
            model_name='imusample',
            name='log_file',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s', to='missions.logfile'),
        ),
        migrations.AlterField(
            model_name='magnetometersample',
            name='deployment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s', to='missions.sensordeployment'),
        ),
        migrations.AlterField(
            model_name='magnetometersample',
            name='log_file',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s', to='missions.logfile'),
        ),
        migrations.AlterField(
            model_name='pressuresample',
            name='deployment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s', to='missions.sensordeployment'),
        ),
        migrations.AlterField(
            model_name='pressuresample',
            name='log_file',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s', to='missions.logfile'),
        ),
    ]
