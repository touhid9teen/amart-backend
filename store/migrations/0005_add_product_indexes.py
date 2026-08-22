# Generated manually for performance optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0004_make_slug_unique'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['is_active', '-createdAt'], name='product_active_created_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['is_active', 'is_featured'], name='product_active_featured_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['name'], name='product_name_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['slug'], name='product_slug_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['sellingPice'], name='product_price_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['stock'], name='product_stock_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['status'], name='product_status_idx'),
        ),
    ]
