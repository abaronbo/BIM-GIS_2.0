# Generated by Django 5.0.6 on 2024-11-14 17:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ifcupload', '0004_flooddefensemechanism_class_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='flooddefensemechanism',
            name='fragment_id_map',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
