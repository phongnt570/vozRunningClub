# Generated by Django 4.1 on 2023-05-31 11:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SettingDefaultDonation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('default_donation', models.IntegerField()),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SettingRegisteredMileage',
            fields=[
                ('distance', models.IntegerField(primary_key=True, serialize=False)),
                ('donation_per_km', models.IntegerField()),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='SettingStravaClub',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('club_url', models.CharField(max_length=1024)),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StravaRunner',
            fields=[
                ('strava_id', models.IntegerField(primary_key=True, serialize=False)),
                ('strava_name', models.CharField(max_length=64)),
                ('voz_name', models.CharField(max_length=64)),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='WeeklyProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField()),
                ('week_num', models.IntegerField()),
                ('distance', models.FloatField(default=0.0)),
                ('runs', models.IntegerField(default=0)),
                ('longest_run', models.FloatField(default=0.0)),
                ('average_pace', models.FloatField(default=0.0)),
                ('elevation_gain', models.FloatField(default=0.0)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('registered_mileage', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='weeklyTracking.settingregisteredmileage')),
                ('runner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='weeklyTracking.stravarunner')),
            ],
        ),
    ]
