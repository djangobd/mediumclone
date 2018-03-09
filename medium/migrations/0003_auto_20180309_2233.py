# Generated by Django 2.0.2 on 2018-03-09 15:33

from django.db import migrations
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0002_auto_20150616_2121'),
        ('medium', '0002_auto_20180309_2223'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='followed_topics',
        ),
        migrations.AddField(
            model_name='userprofile',
            name='followed_topics',
            field=taggit.managers.TaggableManager(blank=True, help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags'),
        ),
    ]
