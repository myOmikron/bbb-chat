# Generated by Django 3.1.7 on 2021-03-17 12:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_chat_internal_meeting_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='chat',
            old_name='meeting_id',
            new_name='external_meeting_id',
        ),
    ]
