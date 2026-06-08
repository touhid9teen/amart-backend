# Generated manually - adds role field to User model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_remove_user_country_code_remove_user_phone_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[('user', 'User'), ('admin', 'Admin'), ('superadmin', 'Super Admin')],
                default='user',
                max_length=20,
            ),
        ),
    ]
