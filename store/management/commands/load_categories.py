from django.core.management.base import BaseCommand
from django.utils.text import slugify
from store.models import Category

class Command(BaseCommand):
    help = 'Load categories with Bangla names (no image for now)'

    def handle(self, *args, **kwargs):
        category_data = [
            {
                "documentId": "cat001",
                "name": "Vegetable",
                "colore": "#8BC34A",
                "image_alt": "তাজা শাকসবজি",
            },
            {
                "documentId": "cat002",
                "name": "Fruits",
                "colore": "#FF9800",
                "image_alt": "টাটকা ফলমূল",
            },
            {
                "documentId": "cat003",
                "name": "Paan Corner",
                "colore": "#4CAF50",
                "image_alt": "পান, সুপারি, জর্দা",
            },
            {
                "documentId": "cat004",
                "name": "Dairy, Bread & Eggs",
                "colore": "#FFEB3B",
                "image_alt": "ডেইরি, পাউরুটি ও ডিম",
            },
            {
                "documentId": "cat005",
                "name": "Cold Drinks & Juices",
                "colore": "#03A9F4",
                "image_alt": "ঠান্ডা পানীয় ও জুস",
            },
            {
                "documentId": "cat006",
                "name": "Snacks & Munchies",
                "colore": "#FFC107",
                "image_alt": "স্ন্যাকস ও মুখরোচক খাবার",
            },
            {
                "documentId": "cat007",
                "name": "Breakfast & Instant Food",
                "colore": "#CDDC39",
                "image_alt": "ব্রেকফাস্ট ও ইনস্ট্যান্ট খাবার",
            },
            {
                "documentId": "cat008",
                "name": "Sweet Tooth",
                "colore": "#E91E63",
                "image_alt": "মিষ্টি ও ডেজার্ট",
            },
            {
                "documentId": "cat009",
                "name": "Bakery & Biscuits",
                "colore": "#795548",
                "image_alt": "বেকারি ও বিস্কুট",
            },
            {
                "documentId": "cat010",
                "name": "Tea, Coffee & Health Drink",
                "colore": "#607D8B",
                "image_alt": "চা, কফি ও স্বাস্থ্যকর পানীয়",
            },
            {
                "documentId": "cat011",
                "name": "Atta, Rice & Dal",
                "colore": "#FF5722",
                "image_alt": "আটা, চাল ও ডাল",
            },
            {
                "documentId": "cat012",
                "name": "Masala, Oil & More",
                "colore": "#9C27B0",
                "image_alt": "মসলা, তেল ইত্যাদি",
            },
            {
                "documentId": "cat013",
                "name": "Sauces & Spreads",
                "colore": "#3F51B5",
                "image_alt": "সস ও স্প্রেড",
            },
            {
                "documentId": "cat014",
                "name": "Chicken, Meat & Fish",
                "colore": "#F44336",
                "image_alt": "মুরগি, মাংস ও মাছ",
            },
            {
                "documentId": "cat015",
                "name": "Organic & Healthy Living",
                "colore": "#009688",
                "image_alt": "অর্গানিক ও স্বাস্থ্যকর জীবনধারা",
            },
            {
                "documentId": "cat016",
                "name": "Baby Care",
                "colore": "#E91E63",
                "image_alt": "শিশুর যত্ন",
            },
            {
                "documentId": "cat017",
                "name": "Pharma & Wellness",
                "colore": "#673AB7",
                "image_alt": "ঔষধ ও সুস্থতা পণ্য",
            },
            {
                "documentId": "cat018",
                "name": "Cleaning Essentials",
                "colore": "#9E9E9E",
                "image_alt": "পরিষ্কার-পরিচ্ছন্নতার পণ্য",
            },
            {
                "documentId": "cat019",
                "name": "Home & Office",
                "colore": "#607D8B",
                "image_alt": "বাড়ি ও অফিস সামগ্রী",
            },
            {
                "documentId": "cat020",
                "name": "Personal Care",
                "colore": "#009688",
                "image_alt": "ব্যক্তিগত পরিচর্যার পণ্য",
            },
            {
                "documentId": "cat021",
                "name": "Pet Care",
                "colore": "#FF9800",
                "image_alt": "পোষা প্রাণীর যত্ন",
            },
        ]

        # Change this block in your handle() method:
        for data in category_data:
            slug = slugify(data["name"])
            category, created = Category.objects.get_or_create(
                slug=slug,
                defaults={
                    **data,
                    "slug": slug,
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Created category: {data['name']}"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ Category already exists: {data['name']}"))