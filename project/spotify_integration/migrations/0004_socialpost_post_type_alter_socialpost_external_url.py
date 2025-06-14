# Generated by Django 5.2.1 on 2025-06-01 15:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('spotify_integration', '0003_socialpost'),
    ]

    operations = [
        migrations.AddField(
            model_name='socialpost',
            name='post_type',
            field=models.CharField(choices=[('track', 'Track'), ('album', 'Album'), ('artist', 'Artist'), ('follow', 'Follow')], db_index=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='socialpost',
            name='external_url',
            field=models.URLField(max_length=250, unique=True, verbose_name='Link to entity (song, artist, etc...) on Spotify'),
        ),
    ]
