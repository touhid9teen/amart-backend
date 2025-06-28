from django.core.management.base import BaseCommand
from django.db import transaction
from store.models import Product, Category

class Command(BaseCommand):
    help = 'Load product data into existing categories: Vegetable, Fruits, Fresh Meat with Bangla names'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        category_map = {
            "Vegetable": Category.objects.get(name__iexact="Vegetable"),
            "Fruits": Category.objects.get(name__iexact="Fruits"),
            "Fresh Meat": Category.objects.get(name__iexact="Fresh Meat"),
        }

        product_data = [
           {
    "name": "বেগুন (Eggplant)",
    "description": "তাজা ও নরম বেগুন রান্নার জন্য উপযুক্ত।",
    "mrp": 2.20,
    "sellingPice": 1.70,
    "ItemQuantityType": "কেজি",
    "image_alt": "বেগুনের ছবি",
    "categories": ["Vegetable"],
},
{
    "name": "পটল (Pointed Gourd)",
    "description": "তরকারিতে ব্যবহারযোগ্য তাজা পটল।",
    "mrp": 2.00,
    "sellingPice": 1.60,
    "ItemQuantityType": "কেজি",
    "image_alt": "পটলের ছবি",
    "categories": ["Vegetable"],
},
{
    "name": "শসা (Cucumber)",
    "description": "ঠান্ডা ও রিফ্রেশিং শসা।",
    "mrp": 1.80,
    "sellingPice": 1.40,
    "ItemQuantityType": "কেজি",
    "image_alt": "শসার ছবি",
    "categories": ["Vegetable"],
},
{
    "name": "আম (Mango)",
    "description": "মিষ্টি ও রসালো দেশি আম।",
    "mrp": 4.50,
    "sellingPice": 3.90,
    "ItemQuantityType": "কেজি",
    "image_alt": "আমের ছবি",
    "categories": ["Fruits"],
},
{
    "name": "কমলা (Orange)",
    "description": "ভিটামিন সি সমৃদ্ধ কমলা।",
    "mrp": 3.20,
    "sellingPice": 2.70,
    "ItemQuantityType": "কেজি",
    "image_alt": "কমলার ছবি",
    "categories": ["Fruits"],
},
{
    "name": "আঙ্গুর (Grapes)",
    "description": "বীজবিহীন মিষ্টি আঙ্গুর।",
    "mrp": 4.80,
    "sellingPice": 4.00,
    "ItemQuantityType": "কেজি",
    "image_alt": "আঙ্গুরের ছবি",
    "categories": ["Fruits"],
},
{
    "name": "মাটন (Mutton)",
    "description": "দেশি খাসির মাংস।",
    "mrp": 14.00,
    "sellingPice": 12.50,
    "ItemQuantityType": "কেজি",
    "image_alt": "মাটনের ছবি",
    "categories": ["Fresh Meat"],
},
{
    "name": "দেশি মুরগি (Deshi Chicken)",
    "description": "স্বাস্থ্যকর দেশি মুরগির মাংস।",
    "mrp": 7.50,
    "sellingPice": 6.80,
    "ItemQuantityType": "কেজি",
    "image_alt": "দেশি মুরগির ছবি",
    "categories": ["Fresh Meat"],
},
{
    "name": "হাঁসের মাংস (Duck Meat)",
    "description": "নরম ও মজাদার হাঁসের মাংস।",
    "mrp": 8.50,
    "sellingPice": 7.70,
    "ItemQuantityType": "কেজি",
    "image_alt": "হাঁসের মাংসের ছবি",
    "categories": ["Fresh Meat"],
}

        ]

        for data in product_data:
            category_names = data.pop("categories")
            product = Product.objects.create(**data)
            product.categories.set([category_map[name] for name in category_names])

        self.stdout.write(self.style.SUCCESS("✅ বাংলা নামসহ প্রোডাক্টগুলো যুক্ত হয়েছে।"))
