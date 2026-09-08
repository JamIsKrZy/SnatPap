from django.db import migrations, models


def copy_legacy_location(apps, schema_editor):
    UserProfile = apps.get_model('user_auth', 'UserProfile')
    UserProfile.objects.exclude(location='').update(street_address=models.F('location'))


class Migration(migrations.Migration):
    dependencies = [
        ('user_auth', '0001_userprofile'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userprofile',
            old_name='number',
            new_name='phone_number',
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='phone_number',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='country_code',
            field=models.CharField(default='+63', max_length=6),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='barangay',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='city_municipality',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='postal_code',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='province',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='street_address',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.RunPython(copy_legacy_location, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='userprofile',
            name='location',
        ),
    ]
