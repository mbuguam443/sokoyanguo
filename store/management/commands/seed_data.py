from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from django.contrib.auth.models import User
from store.models import Category, Product, Courier
from pathlib import Path
import random

class Command(BaseCommand):
    help = 'Seed database with sample categories and products'

    def handle(self, *args, **options):
        static_img = Path(settings.BASE_DIR) / 'static' / 'img'

        cat_data = [
            ("Men's Clothing", 'mens-clothing', 'cat-1.jpg'),
            ("Women's Clothing", 'womens-clothing', 'cat-2.jpg'),
            ("Baby & Kids", 'baby-kids', 'cat-3.jpg'),
            ('Accessories', 'accessories', 'cat-4.jpg'),
            ('Bags', 'bags', 'cat-5.jpg'),
            ('Shoes', 'shoes', 'cat-6.jpg'),
        ]

        for name, slug, img_file in cat_data:
            cat, created = Category.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'is_active': True}
            )
            if created:
                src = static_img / img_file
                if src.exists():
                    with open(src, 'rb') as f:
                        cat.image.save(img_file, File(f))
                self.stdout.write(f'  Created category: {name}')

        product_data = [
            ('Classic Fit Formal Shirt', 'classic-fit-formal-shirt', "Men's Clothing", 1, 49.99, 'product-1.jpg'),
            ('Slim Fit Casual Shirt', 'slim-fit-casual-shirt', "Men's Clothing", 29.99, 44.99, 'product-2.jpg'),
            ('Summer Floral Dress', 'summer-floral-dress', "Women's Clothing", 49.99, 69.99, 'product-3.jpg'),
            ('Elegant Evening Gown', 'elegant-evening-gown', "Women's Clothing", 89.99, 129.99, 'product-4.jpg'),
            ('Kids Cotton Polo Shirt', 'kids-cotton-polo-shirt', 'Baby & Kids', 19.99, 29.99, 'product-5.jpg'),
            ('Leather Crossbody Bag', 'leather-crossbody-bag', 'Accessories', 39.99, 59.99, 'product-6.jpg'),
            ('Canvas Tote Bag', 'canvas-tote-bag', 'Bags', 24.99, 39.99, 'product-7.jpg'),
            ('Running Sneakers', 'running-sneakers', 'Shoes', 1, 89.99, 'product-8.jpg'),
        ]

        for name, slug, cat_name, price, compare_price, img_file in product_data:
            cat = Category.objects.get(name=cat_name)
            prod, created = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'category': cat,
                    'description': f'High quality {name.lower()} — perfect for any occasion. Premium material with excellent craftsmanship.',
                    'price': price,
                    'compare_price': compare_price,
                    'stock': random.randint(20, 100),
                    'is_featured': random.choice([True, False]),
                    'is_new': random.choice([True, False, False, False]),
                    'is_active': True,
                }
            )
            if created:
                src = static_img / img_file
                if src.exists():
                    with open(src, 'rb') as f:
                        prod.image.save(img_file, File(f))
                self.stdout.write(f'  Created product: {name}')

        couriers = ['Boda Boda Rider', 'Wells Fargo', 'G4S', 'Aramex', 'FedEx', 'DHL', 'Kenyaco', 'Pickup Station', 'Other']
        for name in couriers:
            Courier.objects.get_or_create(name=name)
        self.stdout.write(f'  Created {len(couriers)} couriers')

        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser('admin', 'admin@sokoyanguo.co.ke', 'admin123')
            self.stdout.write('  Created superuser: admin / admin123')

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
