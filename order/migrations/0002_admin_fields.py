# Generated manually - adds updated_at and fixes order statuses

from django.db import migrations, models


def fix_order_statuses(apps, schema_editor):
    """Map old status values to new ones."""
    Order = apps.get_model('order', 'Order')
    Order.objects.filter(status='approved').update(status='processing')
    Order.objects.filter(status='cancel').update(status='cancelled')


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('processing', 'Processing'),
                    ('shipped', 'Shipped'),
                    ('delivered', 'Delivered'),
                    ('cancelled', 'Cancelled'),
                    ('refunded', 'Refunded'),
                ],
                default='pending',
                max_length=32,
            ),
        ),
        migrations.RunPython(
            fix_order_statuses,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
