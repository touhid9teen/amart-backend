# Generated manually - adds admin fields with data migration for slug population

import uuid
from django.db import migrations, models
import django.db.models.deletion
from django.utils.text import slugify


def populate_product_slugs(apps, schema_editor):
    """Generate slugs for existing products that don't have one."""
    Product = apps.get_model('store', 'Product')
    slug_map = {}
    products = list(Product.objects.all().only('id', 'name', 'slug'))

    for product in products:
        if not product.slug:
            base_slug = slugify(product.name) or 'product'
            product.slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"

        # Fix duplicates
        while product.slug in slug_map:
            product.slug = f"{product.slug}-{uuid.uuid4().hex[:8]}"

        slug_map[product.slug] = product.id
        Product.objects.filter(id=product.id).update(slug=product.slug)


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0002_alter_product_image'),
    ]

    operations = [
        # ── Category changes ──────────────────────────────
        migrations.AddField(
            model_name='category',
            name='description',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='category',
            name='parent',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='children',
                to='store.category',
            ),
        ),

        # ── Product changes (slug WITHOUT unique first) ───
        migrations.AddField(
            model_name='product',
            name='slug',
            field=models.SlugField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='short_description',
            field=models.CharField(blank=True, default='', max_length=500),
        ),
        migrations.AddField(
            model_name='product',
            name='discount_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='sku',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='product',
            name='stock',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='product',
            name='brand',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='products',
                to='admin_dashboard.brand',
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='tags',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='product',
            name='status',
            field=models.CharField(
                choices=[('active', 'Active'), ('draft', 'Draft'), ('archived', 'Archived')],
                default='active',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='product',
            name='description',
            field=models.TextField(blank=True, default=''),
        ),

        # ── Data migration: populate slugs ────────────────
        migrations.RunPython(
            populate_product_slugs,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
